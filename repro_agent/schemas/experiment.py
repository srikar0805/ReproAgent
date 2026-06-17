"""Experiment and repository schemas."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entrypoints:
    train: str | None = None
    evaluate: str | None = None
    candidates: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DatasetInfo:
    name: str | None = None
    auto_download: bool | None = None
    paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepositoryInspection:
    source: str
    url: str | None
    commit: str | None
    language: str | None
    framework: str | None
    python_version: str | None
    dependency_sources: list[str]
    entrypoints: Entrypoints
    configs: list[str]
    dataset: DatasetInfo
    candidate_command: list[str]
    readme_summary: str | None
    uncertainties: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReproductionSpec:
    schema_version: str
    paper: dict
    repository: dict
    target: dict
    environment: dict
    dataset: dict
    execution: dict
    verification: dict
