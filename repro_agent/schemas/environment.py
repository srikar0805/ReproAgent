"""Environment reconstruction and progressive smoke-test schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EnvironmentPlanStatus(str, Enum):
    PLANNED = "planned"
    UNSUPPORTED = "unsupported"


class SmokeStage(str, Enum):
    IMPORTS = "imports"
    CLI_HELP = "cli_help"
    CONFIGURATION = "configuration"
    DATASET_LOADER = "dataset_loader"
    CHECKPOINT_LOADING = "checkpoint_loading"
    ONE_BATCH_INFERENCE = "one_batch_inference"
    SHORT_EXPERIMENT = "short_experiment"
    FULL_EXPERIMENT = "full_experiment"


@dataclass(frozen=True)
class ResourcePolicy:
    cpus: int
    memory: str
    pids_limit: int
    timeout_seconds: int
    network_enabled: bool
    read_only_root: bool
    cap_drop: list[str]
    forbidden_mounts: list[str]


@dataclass(frozen=True)
class SmokeTestStep:
    stage: SmokeStage
    command: list[str]
    timeout_seconds: int
    requires_dataset: bool = False
    requires_checkpoint: bool = False
    requires_approval: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EnvironmentBuildPlan:
    schema_version: str
    tool_version: str
    status: EnvironmentPlanStatus
    repository: str
    repository_commit: str | None
    python_version: str
    framework: str | None
    dependency_sources: list[str]
    image_name: str
    dockerfile_name: str
    dockerfile: str
    build_command: list[str]
    run_prefix: list[str]
    resource_policy: ResourcePolicy
    smoke_tests: list[SmokeTestStep]
    notes: list[str] = field(default_factory=list)
