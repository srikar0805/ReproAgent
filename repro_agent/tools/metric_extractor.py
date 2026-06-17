"""Heuristics for finding reported metrics in paper text."""

from __future__ import annotations

import re

from repro_agent.schemas.paper import ReportedMetric


METRIC_NAMES = (
    "accuracy",
    "precision",
    "recall",
    "f1",
    "f1-score",
    "loss",
    "mae",
    "mape",
    "rmse",
    "r2",
)


def extract_metrics(text: str) -> list[ReportedMetric]:
    metrics: list[ReportedMetric] = []
    compact = " ".join(text.split())
    for name in METRIC_NAMES:
        metric_then_value = re.compile(
            rf"(?P<context>[^.\n]{{0,100}}\b{name}\b[^.\n]{{0,80}}?)"
            r"(?P<value>\d+(?:\.\d+)?)\s*(?:mm)?\s*(?P<percent>%?)",
            re.IGNORECASE,
        )
        value_then_metric_percent = re.compile(
            r"(?P<value>\d+(?:\.\d+)?)\s*(?P<percent>%)"
            rf"(?P<context>[^.\n]{{0,80}}\b{name}\b[^.\n]{{0,80}})",
            re.IGNORECASE,
        )
        value_then_metric = re.compile(
            r"(?P<value>\d+(?:\.\d+)?)\s*(?:mm\s*)?(?P<percent>)"
            rf"(?P<context>[^.\n]{{0,80}}\b{name}\b[^.\n]{{0,80}})",
            re.IGNORECASE,
        )
        patterns = [metric_then_value, value_then_metric_percent]
        if name.lower() in {"mae", "mape", "rmse", "r2", "loss"}:
            patterns.append(value_then_metric)
        for pattern in patterns:
            for match in pattern.finditer(compact):
                raw_value = float(match.group("value"))
                value = _normalize_value(name, raw_value, bool(match.group("percent")))
                metrics.append(
                    ReportedMetric(
                        name=name.lower(),
                        value=value,
                        context=match.group("context").strip(),
                    )
            )
    return _dedupe(metrics)


def _normalize_value(name: str, value: float, is_percent: bool) -> float:
    if is_percent:
        return value / 100
    if name.lower() not in {"loss", "mae", "mape", "rmse"} and 1 < value <= 100:
        return value / 100
    return value


def _dedupe(metrics: list[ReportedMetric]) -> list[ReportedMetric]:
    seen: set[tuple[str, float | None, str | None]] = set()
    unique: list[ReportedMetric] = []
    for metric in metrics:
        key = (metric.name, metric.value, metric.context)
        if key in seen:
            continue
        seen.add(key)
        unique.append(metric)
    return unique[:20]
