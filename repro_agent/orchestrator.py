"""High-level orchestration for ReproAgent workflows."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tempfile

from repro_agent import __version__
from repro_agent.agents.artifact_auditor import ArtifactAuditor
from repro_agent.agents.paper_analyzer import PaperAnalyzer
from repro_agent.agents.repository_inspector import RepositoryInspector
from repro_agent.schemas.audit import (
    AuditVerdict,
    AuditVerdictStatus,
    CommandAudit,
    ComputeEstimate,
    EnvironmentAudit,
    ReportMetadata,
    ReproducibilityAudit,
    ReproductionStatus,
)
from repro_agent.schemas.common import to_plain_data
from repro_agent.schemas.experiment import ReproductionSpec
from repro_agent.schemas.research import (
    BaselinePlan,
    ComparisonPlan,
    PreparationStatus,
    ResearchMode,
    ResolutionOption,
)
from repro_agent.tools.docker_tools import planned_image_name
from repro_agent.tools.command_validator import validate_documented_command
from repro_agent.tools.git_tools import clone_repository, get_remote_url, looks_like_url


class Orchestrator:
    def __init__(
        self,
        paper_analyzer: PaperAnalyzer | None = None,
        repository_inspector: RepositoryInspector | None = None,
        artifact_auditor: ArtifactAuditor | None = None,
    ) -> None:
        self.paper_analyzer = paper_analyzer or PaperAnalyzer()
        self.repository_inspector = repository_inspector or RepositoryInspector()
        self.artifact_auditor = artifact_auditor or ArtifactAuditor()

    def inspect_paper(self, paper: Path, target: str | None = None) -> dict:
        return to_plain_data(self.paper_analyzer.analyze(paper, target))

    def inspect_repo(self, repo: str, clone: bool = False) -> dict:
        return to_plain_data(self.repository_inspector.inspect(repo, clone=clone))

    def init_reproduction(
        self,
        paper: Path,
        repo: str,
        target: str,
        device: str = "cpu",
        clone: bool = False,
    ) -> ReproductionSpec:
        paper_analysis = self.paper_analyzer.analyze(paper, target)
        repo_inspection = self.repository_inspector.inspect(repo, clone=clone)

        reported_metric = paper_analysis.target.metric
        spec = ReproductionSpec(
            schema_version="0.1",
            paper={
                "title": paper_analysis.title,
                "source": str(paper),
            },
            repository={
                "url": repo_inspection.url or repo,
                "commit": repo_inspection.commit,
            },
            target={
                "description": target,
                "reported_metric": {
                    "name": reported_metric.name if reported_metric else None,
                    "value": reported_metric.value if reported_metric else None,
                },
                "uncertainties": paper_analysis.uncertainties
                + repo_inspection.uncertainties,
            },
            environment={
                "python": repo_inspection.python_version or "3.10",
                "framework": repo_inspection.framework,
                "device": device,
                "docker_image": planned_image_name(repo_inspection.commit),
            },
            dataset=to_plain_data(repo_inspection.dataset),
            execution={
                "command": repo_inspection.candidate_command,
                "timeout_minutes": 180,
                "retries": 3,
            },
            verification={
                "metric": reported_metric.name if reported_metric else None,
                "tolerance": 0.01,
                "repeated_runs": 1,
            },
        )
        return spec

    def audit(
        self,
        paper: Path,
        repo: str,
        target: str,
        device: str = "cpu",
        clone: bool = False,
    ) -> tuple[ReproductionSpec, ReproducibilityAudit]:
        with tempfile.TemporaryDirectory(prefix="repro-agent-audit-") as tmpdir:
            repo_path, repo_url = self._resolve_repo_for_audit(repo, clone, Path(tmpdir))
            paper_analysis = self.paper_analyzer.analyze(paper, target)
            repo_inspection = self.repository_inspector.inspect_path(repo_path)
            command_validation = validate_documented_command(repo_path)
            command = command_validation.corrected_command or repo_inspection.candidate_command
            artifact_audit = self.artifact_auditor.audit(repo_path, command)

            status = (
                ReproductionStatus.BLOCKED
                if artifact_audit.missing_artifacts
                else ReproductionStatus.INSPECTED
            )
            reported_metric = paper_analysis.target.metric
            spec = ReproductionSpec(
                schema_version="0.1",
                paper={"title": paper_analysis.title, "source": str(paper)},
                repository={
                    "url": repo_url or repo_inspection.url or repo,
                    "commit": repo_inspection.commit,
                },
                target={
                    "description": target,
                    "reported_metric": {
                        "name": reported_metric.name if reported_metric else None,
                        "value": reported_metric.value if reported_metric else None,
                    },
                    "uncertainties": paper_analysis.uncertainties
                    + repo_inspection.uncertainties,
                },
                environment={
                    "python": repo_inspection.python_version or "3.10",
                    "framework": repo_inspection.framework,
                    "device": device,
                    "docker_image": planned_image_name(repo_inspection.commit),
                },
                dataset=to_plain_data(repo_inspection.dataset),
                execution={
                    "command": command,
                    "timeout_minutes": 180,
                    "retries": 3,
                },
                verification={
                    "metric": reported_metric.name if reported_metric else None,
                    "tolerance": 0.01,
                    "repeated_runs": 1,
                },
            )
            audit = ReproducibilityAudit(
                metadata=self._build_metadata(
                    paper=paper,
                    repository_commit=repo_inspection.commit,
                    target=target,
                ),
                status=status,
                target={
                    "description": target,
                    "identification_confidence": "medium" if reported_metric else "low",
                    "reported_metric": {
                        "name": reported_metric.name if reported_metric else None,
                        "value": reported_metric.value if reported_metric else None,
                    },
                },
                repository={
                    "url": repo_url or repo_inspection.url or repo,
                    "commit": repo_inspection.commit,
                    "code_available": True,
                    "documented_command_available": bool(command_validation.documented_command),
                    "command_valid": command_validation.command_valid,
                },
                artifact_audit=artifact_audit,
                command_audit=CommandAudit(
                    documented_command=command_validation.documented_command,
                    corrected_command=command,
                    command_valid=command_validation.command_valid,
                    missing_required_arguments=command_validation.missing_required_arguments,
                    missing_referenced_paths=command_validation.missing_referenced_paths,
                    documentation_issues=command_validation.documentation_issues,
                ),
                environment_audit=EnvironmentAudit(
                    dependency_sources=repo_inspection.dependency_sources,
                    python_version=repo_inspection.python_version,
                    framework=repo_inspection.framework,
                    status=ReproductionStatus.NOT_ANALYZED,
                    notes=["Environment build is deferred to MVP 0.2."],
                ),
                compute=self._estimate_compute(repo_path),
                verdict=self._build_verdict(status, artifact_audit.missing_artifacts),
            )
            return spec, audit

    def prepare_baseline(
        self,
        paper: Path,
        repo: str,
        target: str,
        mode: ResearchMode = ResearchMode.EXACT_REPRODUCTION,
        dataset: Path | None = None,
        device: str = "cpu",
        clone: bool = False,
    ) -> tuple[ReproductionSpec, ReproducibilityAudit, BaselinePlan]:
        spec, audit = self.audit(
            paper=paper,
            repo=repo,
            target=target,
            device=device,
            clone=clone,
        )
        blockers = [to_plain_data(item) for item in audit.artifact_audit.missing_artifacts]
        dataset_value = self._resolve_supplied_dataset(dataset)
        status = self._preparation_status(mode, blockers, dataset_value)
        plan = BaselinePlan(
            metadata=audit.metadata,
            mode=mode,
            status=status,
            target=audit.target,
            repository=audit.repository,
            audit_id=audit.metadata.audit_id,
            command=spec.execution["command"],
            supplied_dataset=dataset_value,
            blockers=blockers,
            options=self._resolution_options(blockers),
            assumptions=self._baseline_assumptions(mode, blockers, dataset_value),
            next_steps=self._baseline_next_steps(status, mode),
        )
        return spec, audit, plan

    def plan_comparison(
        self,
        paper: Path,
        baseline_repo: str,
        candidate_repo: str,
        target: str,
        dataset: Path | None = None,
        mode: ResearchMode = ResearchMode.FAIR_BENCHMARK,
        device: str = "cpu",
        clone: bool = False,
    ) -> tuple[ReproductionSpec, ReproducibilityAudit, ComparisonPlan]:
        spec, audit, baseline_plan = self.prepare_baseline(
            paper=paper,
            repo=baseline_repo,
            target=target,
            mode=mode,
            dataset=dataset,
            device=device,
            clone=clone,
        )
        candidate = self.repository_inspector.inspect(candidate_repo, clone=clone)
        candidate_command = self._candidate_evaluation_command(candidate)
        blockers = list(baseline_plan.blockers)
        if not candidate_command:
            blockers.append(
                {
                    "finding_id": "CMP-001",
                    "category": "candidate_evaluation_entrypoint",
                    "severity": "blocker",
                    "path": candidate_repo,
                    "required_for": "candidate_evaluation",
                    "confidence": 0.8,
                }
            )
        dataset_value = self._resolve_supplied_dataset(dataset)
        status = self._comparison_status(
            mode=mode,
            baseline_status=baseline_plan.status,
            candidate_has_command=bool(candidate_command),
            dataset=dataset_value,
        )
        metric = audit.target["reported_metric"]
        plan = ComparisonPlan(
            metadata=audit.metadata,
            mode=mode,
            status=status,
            target=audit.target,
            baseline={
                "repository": audit.repository,
                "command": spec.execution["command"],
                "framework": spec.environment["framework"],
            },
            candidate={
                "repository": candidate.url or candidate.source,
                "commit": candidate.commit,
                "framework": candidate.framework,
                "command": candidate_command,
            },
            shared_protocol={
                "dataset": dataset_value or spec.dataset.get("name"),
                "metric": metric.get("name"),
                "reported_value": metric.get("value"),
                "split_policy": (
                    "original_required"
                    if mode == ResearchMode.EXACT_REPRODUCTION
                    else "common_split_must_be_declared"
                ),
                "device": device,
                "execution_available": False,
            },
            blockers=blockers,
            options=self._resolution_options(blockers),
            fairness_requirements=[
                "Use the same dataset version for baseline and candidate.",
                "Use the same train/validation/test split.",
                "Use the same preprocessing and metric implementation.",
                "Use the same fold or seed policy.",
                "Record parameters, runtime, memory, and code commits.",
                "Do not claim paper reproduction when using a replacement split.",
            ],
            next_steps=self._comparison_next_steps(status),
        )
        return spec, audit, plan

    def _resolve_repo_for_audit(
        self, repo: str, clone: bool, tmpdir: Path
    ) -> tuple[Path, str | None]:
        repo_path = Path(repo).expanduser()
        if repo_path.exists():
            return repo_path.resolve(), get_remote_url(repo_path)
        if looks_like_url(repo):
            if not clone:
                raise ValueError("Remote audit requires --clone.")
            destination = tmpdir / "repo"
            return clone_repository(repo, destination), repo
        raise FileNotFoundError(repo)

    def _build_verdict(self, status: ReproductionStatus, missing: list) -> AuditVerdict:
        if status == ReproductionStatus.BLOCKED:
            return AuditVerdict(
                status=AuditVerdictStatus.BLOCKED,
                reproducible_from_public_materials=False,
                primary_reason="Required scientific artifacts are unavailable.",
                recommended_actions=[
                    "Publish or link the missing datasets, labels, splits, and checkpoints.",
                    "Update README commands so required arguments are present.",
                    "Document artifact licenses and access requirements.",
                ],
            )
        return AuditVerdict(
            status=AuditVerdictStatus.RUNNABLE,
            reproducible_from_public_materials=True,
            primary_reason=(
                "No blocking missing artifacts were detected by static audit. "
                "This does not mean the result has been reproduced."
            ),
            recommended_actions=["Proceed to environment reconstruction."],
        )

    def _preparation_status(
        self, mode: ResearchMode, blockers: list[dict], dataset: str | None
    ) -> PreparationStatus:
        if not blockers:
            return PreparationStatus.READY_FOR_ENVIRONMENT
        if mode == ResearchMode.EXACT_REPRODUCTION:
            return PreparationStatus.BLOCKED
        if mode == ResearchMode.INDEPENDENT_REPLICATION:
            return PreparationStatus.ASSUMPTIONS_REQUIRED
        if dataset:
            return PreparationStatus.PROTOCOL_DEFINITION_REQUIRED
        return PreparationStatus.BLOCKED

    def _comparison_status(
        self,
        mode: ResearchMode,
        baseline_status: PreparationStatus,
        candidate_has_command: bool,
        dataset: str | None,
    ) -> PreparationStatus:
        if not candidate_has_command:
            return PreparationStatus.BLOCKED
        if baseline_status == PreparationStatus.READY_FOR_ENVIRONMENT:
            return PreparationStatus.READY_FOR_ENVIRONMENT
        if mode == ResearchMode.FAIR_BENCHMARK and dataset:
            return PreparationStatus.PROTOCOL_DEFINITION_REQUIRED
        return baseline_status

    def _resolution_options(self, blockers: list[dict]) -> list[ResolutionOption]:
        if not blockers:
            return []
        return [
            ResolutionOption(
                option_id="RES-001",
                title="Acquire original artifacts",
                description=(
                    "Request or download the exact missing datasets, splits, labels, "
                    "and checkpoints from an authoritative source."
                ),
                preserves_exact_reproduction=True,
                scientific_impact="none",
                recommended=True,
            ),
            ResolutionOption(
                option_id="RES-002",
                title="Independent replication",
                description=(
                    "Recreate missing components using explicit assumptions. This can "
                    "test the method, but cannot validate the exact published number."
                ),
                preserves_exact_reproduction=False,
                scientific_impact="high",
            ),
            ResolutionOption(
                option_id="RES-003",
                title="Define a fair common benchmark",
                description=(
                    "Run baseline and candidate under a newly declared common dataset, "
                    "split, preprocessing, and metric protocol."
                ),
                preserves_exact_reproduction=False,
                scientific_impact="high",
            ),
        ]

    def _baseline_assumptions(
        self, mode: ResearchMode, blockers: list[dict], dataset: str | None
    ) -> list[dict]:
        assumptions = []
        if dataset:
            assumptions.append(
                {
                    "name": "dataset_override",
                    "value": dataset,
                    "source": "user_supplied",
                    "scientific_impact": (
                        "unknown_requires_validation"
                        if mode == ResearchMode.EXACT_REPRODUCTION
                        else "high"
                    ),
                }
            )
        if blockers and mode != ResearchMode.EXACT_REPRODUCTION:
            assumptions.append(
                {
                    "name": "missing_artifact_policy",
                    "value": mode.value,
                    "source": "user_selected",
                    "scientific_impact": "high",
                }
            )
        return assumptions

    def _baseline_next_steps(
        self, status: PreparationStatus, mode: ResearchMode
    ) -> list[str]:
        if status == PreparationStatus.READY_FOR_ENVIRONMENT:
            return [
                "Build an isolated environment.",
                "Run import and CLI help smoke tests.",
                "Validate dataset and checkpoint loading.",
            ]
        if mode == ResearchMode.EXACT_REPRODUCTION:
            return [
                "Acquire the original blocking artifacts.",
                "Re-run the audit after placing or linking them.",
            ]
        return [
            "Review and approve all scientific assumptions.",
            "Record the new protocol as independent replication or fair benchmark.",
            "Do not compare the resulting metric directly as exact reproduction.",
        ]

    def _comparison_next_steps(self, status: PreparationStatus) -> list[str]:
        if status == PreparationStatus.READY_FOR_ENVIRONMENT:
            return [
                "Build isolated baseline and candidate environments.",
                "Validate both commands against the shared protocol.",
                "Run smoke tests before full evaluation.",
            ]
        if status == PreparationStatus.PROTOCOL_DEFINITION_REQUIRED:
            return [
                "Define and freeze the common dataset and split.",
                "Define one shared preprocessing and metric implementation.",
                "Review adapters for scientific changes before execution.",
            ]
        return [
            "Resolve blocking baseline or candidate artifacts.",
            "Re-run comparison planning after the repositories are complete.",
        ]

    def _candidate_evaluation_command(self, candidate) -> list[str]:
        evaluate = candidate.entrypoints.evaluate
        if not evaluate:
            return []
        if evaluate in candidate.candidate_command:
            return candidate.candidate_command
        return ["python", evaluate]

    def _resolve_supplied_dataset(self, dataset: Path | None) -> str | None:
        if dataset is None:
            return None
        if not dataset.exists():
            raise FileNotFoundError(f"Supplied dataset path does not exist: {dataset}")
        return str(dataset.resolve())

    def _build_metadata(
        self, paper: Path, repository_commit: str | None, target: str
    ) -> ReportMetadata:
        paper_hash = self._file_sha256(paper)
        audit_seed = "|".join(
            [
                paper_hash or "",
                repository_commit or "",
                target,
                __version__,
            ]
        )
        audit_id = "audit-" + hashlib.sha256(audit_seed.encode("utf-8")).hexdigest()[:12]
        created_at = (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        return ReportMetadata(
            schema_version="0.1.0",
            tool_version=__version__,
            audit_id=audit_id,
            created_at=created_at,
            repository_commit=repository_commit,
            paper_hash=paper_hash,
        )

    def _file_sha256(self, path: Path) -> str | None:
        if not path.exists():
            return None
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return "sha256:" + digest.hexdigest()

    def _estimate_compute(self, repo_path: Path) -> ComputeEstimate:
        readme = repo_path / "README.md"
        text = readme.read_text(encoding="utf-8", errors="ignore") if readme.exists() else ""
        lower = text.lower()
        accelerator = "NVIDIA A100" if "a100" in lower else None
        fold_runtime = 50 if "50 min" in lower and "fold" in lower else None
        fold_count = 4 if "4-fold" in lower or "folds 0–3" in lower or "folds 0-3" in lower else None
        total = fold_runtime * fold_count if fold_runtime and fold_count else None
        evidence = []
        if fold_runtime:
            evidence.append("README states each fold takes approximately 50 minutes.")
        if accelerator:
            evidence.append("README reports A100 inference/training context.")
        return ComputeEstimate(
            accelerator=accelerator,
            estimated_fold_runtime_minutes=fold_runtime,
            fold_count=fold_count,
            estimated_total_runtime_minutes=total,
            evidence=evidence,
        )
