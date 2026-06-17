"""Paper analysis schemas."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReportedMetric:
    name: str
    value: float | None
    context: str | None = None


@dataclass(frozen=True)
class ExperimentTarget:
    description: str
    table: str | None = None
    dataset: str | None = None
    model: str | None = None
    metric: ReportedMetric | None = None


@dataclass(frozen=True)
class PaperConfiguration:
    epochs: int | None = None
    batch_size: int | None = None
    optimizer: str | None = None
    learning_rate: float | None = None
    seed: int | None = None


@dataclass(frozen=True)
class PaperAnalysis:
    source: str
    title: str | None
    abstract: str | None
    target: ExperimentTarget
    configuration: PaperConfiguration
    datasets: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    metrics: list[ReportedMetric] = field(default_factory=list)
    uncertainties: list[str] = field(default_factory=list)
