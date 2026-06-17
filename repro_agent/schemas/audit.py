"""Audit schemas for reproducibility verdicts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ReproductionStatus(str, Enum):
    NOT_ANALYZED = "not_analyzed"
    INSPECTED = "inspected"
    BLOCKED = "blocked"
    ENVIRONMENT_FAILED = "environment_failed"
    EXECUTION_FAILED = "execution_failed"
    PARTIALLY_REPRODUCED = "partially_reproduced"
    APPROXIMATELY_REPRODUCED = "approximately_reproduced"
    EXACTLY_REPRODUCED = "exactly_reproduced"


class ArtifactCategory(str, Enum):
    DATASET = "dataset"
    LABELS = "labels"
    DATASET_SPLIT = "dataset_split"
    MODEL_CHECKPOINT = "model_checkpoint"
    CONFIGURATION = "configuration"
    METRICS_OUTPUT = "metrics_output"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RequiredArtifact:
    name: str
    path: str
    category: ArtifactCategory
    severity: str
    evidence: list[str]
    required_for: str


@dataclass(frozen=True)
class MissingArtifact:
    name: str
    path: str
    category: ArtifactCategory
    severity: str
    evidence: list[str]
    required_for: str


@dataclass(frozen=True)
class ArtifactAudit:
    required_artifacts: list[RequiredArtifact]
    available_artifacts: list[str]
    missing_artifacts: list[MissingArtifact]
    external_links: list[str] = field(default_factory=list)
    status: ReproductionStatus = ReproductionStatus.INSPECTED


@dataclass(frozen=True)
class DocumentationIssue:
    type: str
    message: str
    command_argument: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class CommandAudit:
    documented_command: list[str]
    corrected_command: list[str]
    command_valid: bool
    missing_required_arguments: list[str]
    missing_referenced_paths: list[str]
    documentation_issues: list[DocumentationIssue]


@dataclass(frozen=True)
class EnvironmentAudit:
    dependency_sources: list[str]
    python_version: str | None
    framework: str | None
    status: ReproductionStatus
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComputeEstimate:
    accelerator: str | None
    estimated_fold_runtime_minutes: int | None
    fold_count: int | None
    estimated_total_runtime_minutes: int | None
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuditVerdict:
    status: ReproductionStatus
    reproducible_from_public_materials: bool
    primary_reason: str
    recommended_actions: list[str]


@dataclass(frozen=True)
class ReproducibilityAudit:
    status: ReproductionStatus
    target: dict
    repository: dict
    artifact_audit: ArtifactAudit
    command_audit: CommandAudit
    environment_audit: EnvironmentAudit
    compute: ComputeEstimate
    verdict: AuditVerdict
