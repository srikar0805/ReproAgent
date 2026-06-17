"""Execution-stage schemas."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExecutionPlan:
    command: list[str]
    timeout_minutes: int
    retries: int
    requires_network: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int
    stdout_path: str | None
    stderr_path: str | None
    metrics_path: str | None
    classified_error: str | None = None
