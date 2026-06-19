"""Candidate-model adapter contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AdapterStatus(str, Enum):
    PLANNED = "planned"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class CandidateAdapterPlan:
    schema_version: str
    tool_version: str
    status: AdapterStatus
    repository: str
    repository_commit: str | None
    framework: str | None
    evaluation_entrypoint: str | None
    evaluation_command: list[str]
    input_arguments: dict[str, str | None]
    output_contract: dict[str, str | None]
    required_methods: list[str]
    scientific_constraints: list[str]
    missing_fields: list[str] = field(default_factory=list)
