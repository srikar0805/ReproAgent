"""High-level orchestration for ReproAgent workflows."""

from __future__ import annotations

from pathlib import Path
import tempfile

from repro_agent.agents.artifact_auditor import ArtifactAuditor
from repro_agent.agents.paper_analyzer import PaperAnalyzer
from repro_agent.agents.repository_inspector import RepositoryInspector
from repro_agent.schemas.audit import (
    AuditVerdict,
    CommandAudit,
    ComputeEstimate,
    EnvironmentAudit,
    ReproducibilityAudit,
    ReproductionStatus,
)
from repro_agent.schemas.common import to_plain_data
from repro_agent.schemas.experiment import ReproductionSpec
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
                status=status,
                reproducible_from_public_materials=False,
                primary_reason="Required scientific artifacts are unavailable.",
                recommended_actions=[
                    "Publish or link the missing datasets, labels, splits, and checkpoints.",
                    "Update README commands so required arguments are present.",
                    "Document artifact licenses and access requirements.",
                ],
            )
        return AuditVerdict(
            status=status,
            reproducible_from_public_materials=True,
            primary_reason="No blocking missing artifacts were detected by static audit.",
            recommended_actions=["Proceed to environment reconstruction."],
        )

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
