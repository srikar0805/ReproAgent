"""Required and available artifact discovery."""

from __future__ import annotations

from pathlib import Path
import re

from repro_agent.schemas.audit import (
    ArtifactCategory,
    ArtifactImpact,
    Evidence,
    MissingArtifact,
    RequiredArtifact,
)
from repro_agent.tools.command_validator import PATH_ARGUMENTS


BLOCKING_CATEGORIES = {
    ArtifactCategory.DATASET,
    ArtifactCategory.LABELS,
    ArtifactCategory.DATASET_SPLIT,
    ArtifactCategory.MODEL_CHECKPOINT,
    ArtifactCategory.CONFIGURATION,
}


def inventory_files(repo_path: Path) -> list[str]:
    files: list[str] = []
    for path in repo_path.rglob("*"):
        if not path.is_file() or _ignored(path):
            continue
        files.append(path.relative_to(repo_path).as_posix())
    return sorted(files)


def extract_external_links(repo_path: Path) -> list[str]:
    links: list[str] = []
    for path in repo_path.rglob("*"):
        if not path.is_file() or _ignored(path):
            continue
        if path.suffix.lower() not in {".md", ".rst", ".txt", ".toml", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        links.extend(re.findall(r"https?://[^\s>)]+", text))
    return sorted(set(links))


def required_artifacts_from_command(
    command: list[str], repo_path: Path | None = None
) -> list[RequiredArtifact]:
    artifacts: list[RequiredArtifact] = []
    command_script = _script_from_command(command)
    for index, part in enumerate(command):
        if part not in PATH_ARGUMENTS:
            continue
        for value in _values_for_arg(command, index):
            category = categorize_artifact(value, argument=part)
            evidence = [
                Evidence(
                    source="README.md",
                    kind="command_argument",
                    detail=f"{part} {value}",
                    operation="documented command",
                )
            ]
            if repo_path is not None:
                evidence.extend(
                    _python_file_access_evidence(
                        repo_path,
                        value,
                        part,
                        preferred_script=command_script,
                    )
                )
            artifacts.append(
                RequiredArtifact(
                    name=Path(value).name,
                    path=value,
                    category=category,
                    severity="blocker" if category in BLOCKING_CATEGORIES else "required",
                    evidence=evidence,
                    required_for=_required_for(category),
                    searched_locations=_searched_locations(category),
                    impact=_impact_for(category),
                )
            )
    return _dedupe_required(artifacts)


def missing_artifacts(repo_path: Path, required: list[RequiredArtifact]) -> list[MissingArtifact]:
    missing: list[MissingArtifact] = []
    for artifact in required:
        if artifact.category == ArtifactCategory.METRICS_OUTPUT:
            continue
        if (repo_path / artifact.path).exists():
            continue
        missing.append(
            MissingArtifact(
                name=artifact.name,
                path=artifact.path,
                category=artifact.category,
                severity=artifact.severity,
                evidence=artifact.evidence,
                required_for=artifact.required_for,
                searched_locations=artifact.searched_locations,
                impact=artifact.impact,
            )
        )
    return missing


def categorize_artifact(path: str, argument: str | None = None) -> ArtifactCategory:
    lower = path.lower()
    if argument in {"--checkpoint", "--checkpoints", "--ckpt", "--weights"}:
        return ArtifactCategory.MODEL_CHECKPOINT
    if argument in {"--labels", "--label"} or "label" in lower:
        return ArtifactCategory.LABELS
    if argument in {"--split", "--split_json"} or "split" in lower:
        return ArtifactCategory.DATASET_SPLIT
    if argument in {"--config"} or lower.endswith((".yaml", ".yml", ".toml")):
        return ArtifactCategory.CONFIGURATION
    if argument == "--output":
        return ArtifactCategory.METRICS_OUTPUT
    if lower.endswith((".h5", ".hdf5", ".csv", ".json", ".npz", ".npy", ".parquet")):
        return ArtifactCategory.DATASET
    if lower.endswith((".pt", ".pth", ".ckpt", ".pkl", ".safetensors")):
        return ArtifactCategory.MODEL_CHECKPOINT
    return ArtifactCategory.UNKNOWN


def _values_for_arg(command: list[str], index: int) -> list[str]:
    values: list[str] = []
    for value in command[index + 1 :]:
        if value.startswith("--"):
            break
        values.append(value)
    return values


def _required_for(category: ArtifactCategory) -> str:
    if category == ArtifactCategory.MODEL_CHECKPOINT:
        return "reported_evaluation"
    if category == ArtifactCategory.DATASET_SPLIT:
        return "reported_train_test_split"
    if category in {ArtifactCategory.DATASET, ArtifactCategory.LABELS}:
        return "training_and_evaluation"
    if category == ArtifactCategory.METRICS_OUTPUT:
        return "metrics_recording"
    return "experiment"


def _searched_locations(category: ArtifactCategory) -> list[str]:
    locations = ["repository", "git_lfs", "github_releases", "linked_downloads"]
    if category == ArtifactCategory.METRICS_OUTPUT:
        return ["repository_output_path"]
    return locations


def _impact_for(category: ArtifactCategory) -> ArtifactImpact:
    if category in BLOCKING_CATEGORIES:
        return ArtifactImpact(
            blocks_execution=True,
            blocks_result_verification=True,
            notes=[f"Missing {category.value} prevents legitimate reproduction."],
        )
    return ArtifactImpact(
        blocks_execution=False,
        blocks_result_verification=False,
        notes=["Output path can be created during execution."],
    )


def _python_file_access_evidence(
    repo_path: Path,
    artifact_path: str,
    argument: str | None,
    preferred_script: str | None = None,
) -> list[Evidence]:
    evidence: list[Evidence] = []
    artifact_name = Path(artifact_path).name
    argument_name = _argument_stem(artifact_path, argument)
    access_patterns = ("h5py.File", "open(", "torch.load", "np.load", "json.loads")
    for path in repo_path.rglob("*.py"):
        if _ignored(path):
            continue
        rel_path = path.relative_to(repo_path).as_posix()
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line_number, line in enumerate(lines, start=1):
            compact = line.strip()
            if artifact_name not in compact and f"args.{argument_name}" not in compact:
                continue
            if not any(pattern in compact for pattern in access_patterns):
                continue
            evidence.append(
                Evidence(
                    source=rel_path,
                    kind="file_access",
                    detail=compact,
                    line=line_number,
                    operation=_operation_from_line(compact),
                )
            )
    return sorted(
        evidence,
        key=lambda entry: (
            entry.source != preferred_script,
            entry.source,
            entry.line or 0,
        ),
    )[:10]


def _script_from_command(command: list[str]) -> str | None:
    return next((part for part in command if part.endswith(".py")), None)


def _argument_stem(path: str, argument: str | None) -> str:
    if argument:
        return argument.removeprefix("--").replace("-", "_")
    stem = Path(path).stem
    aliases = {"dataset": "dataset", "label": "labels", "split": "split_json"}
    return aliases.get(stem, stem)


def _operation_from_line(line: str) -> str:
    for operation in ("h5py.File", "torch.load", "np.load", "open", "json.loads"):
        if operation in line:
            return operation
    return "file access"


def _dedupe_required(artifacts: list[RequiredArtifact]) -> list[RequiredArtifact]:
    seen: set[str] = set()
    unique: list[RequiredArtifact] = []
    for artifact in artifacts:
        if artifact.path in seen:
            continue
        seen.add(artifact.path)
        unique.append(artifact)
    return unique


def _ignored(path: Path) -> bool:
    ignored_parts = {".git", ".venv", "venv", "__pycache__", "site-packages"}
    return any(part in ignored_parts for part in path.parts)
