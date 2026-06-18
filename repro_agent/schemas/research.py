"""Schemas for baseline preparation and fair-comparison planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from repro_agent.schemas.audit import ReportMetadata


class ResearchMode(str, Enum):
    EXACT_REPRODUCTION = "exact_reproduction"
    INDEPENDENT_REPLICATION = "independent_replication"
    FAIR_BENCHMARK = "fair_benchmark"


class PreparationStatus(str, Enum):
    READY_FOR_ENVIRONMENT = "ready_for_environment"
    BLOCKED = "blocked"
    ASSUMPTIONS_REQUIRED = "assumptions_required"
    PROTOCOL_DEFINITION_REQUIRED = "protocol_definition_required"


@dataclass(frozen=True)
class ResolutionOption:
    option_id: str
    title: str
    description: str
    preserves_exact_reproduction: bool
    scientific_impact: str
    recommended: bool = False


@dataclass(frozen=True)
class BaselinePlan:
    metadata: ReportMetadata
    mode: ResearchMode
    status: PreparationStatus
    target: dict
    repository: dict
    audit_id: str
    command: list[str]
    supplied_dataset: str | None
    blockers: list[dict]
    options: list[ResolutionOption]
    assumptions: list[dict] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComparisonPlan:
    metadata: ReportMetadata
    mode: ResearchMode
    status: PreparationStatus
    target: dict
    baseline: dict
    candidate: dict
    shared_protocol: dict
    blockers: list[dict]
    options: list[ResolutionOption]
    fairness_requirements: list[str]
    next_steps: list[str] = field(default_factory=list)
