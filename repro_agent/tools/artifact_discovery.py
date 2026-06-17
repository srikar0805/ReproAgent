"""Required and available artifact discovery."""

from __future__ import annotations

from pathlib import Path
import re

from repro_agent.schemas.audit import ArtifactCategory, MissingArtifact, RequiredArtifact
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


def required_artifacts_from_command(command: list[str]) -> list[RequiredArtifact]:
    artifacts: list[RequiredArtifact] = []
    for index, part in enumerate(command):
        if part not in PATH_ARGUMENTS:
            continue
        for value in _values_for_arg(command, index):
            category = categorize_artifact(value, argument=part)
            artifacts.append(
                RequiredArtifact(
                    name=Path(value).name,
                    path=value,
                    category=category,
                    severity="blocker" if category in BLOCKING_CATEGORIES else "required",
                    evidence=[f"command argument {part}"],
                    required_for=_required_for(category),
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
