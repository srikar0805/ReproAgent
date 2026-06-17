"""Paper analysis agent."""

from __future__ import annotations

from pathlib import Path
import re

from repro_agent.schemas.paper import (
    ExperimentTarget,
    PaperAnalysis,
    PaperConfiguration,
    ReportedMetric,
)
from repro_agent.tools.metric_extractor import extract_metrics
from repro_agent.tools.pdf_parser import extract_text


DATASET_HINTS = ("CIFAR-10", "CIFAR10", "MNIST", "ImageNet", "SVHN", "Fashion-MNIST")
OPTIMIZER_HINTS = ("AdamW", "Adam", "SGD", "RMSprop", "Adagrad")


class PaperAnalyzer:
    """Extract a first-pass reproduction target from a paper."""

    def analyze(self, paper_path: Path, target_description: str | None = None) -> PaperAnalysis:
        text = extract_text(paper_path)
        metrics = extract_metrics(text)
        target_metric = self._select_metric(metrics, target_description)
        description = target_description or self._default_target_description(target_metric)

        target = ExperimentTarget(
            description=description,
            table=self._extract_table(description),
            dataset=self._select_dataset(text, description),
            model=self._select_model(description),
            metric=target_metric,
        )

        uncertainties = self._uncertainties(target, text)
        return PaperAnalysis(
            source=str(paper_path),
            title=self._extract_title(text),
            abstract=self._extract_abstract(text),
            target=target,
            configuration=self._extract_configuration(text),
            datasets=self._extract_datasets(text),
            models=self._extract_models(text, description),
            metrics=metrics,
            uncertainties=uncertainties,
        )

    def _select_metric(
        self, metrics: list[ReportedMetric], target_description: str | None
    ) -> ReportedMetric | None:
        if not metrics:
            return None
        if target_description:
            lower_target = target_description.lower()
            for metric in metrics:
                if metric.value is None:
                    continue
                value_text = f"{metric.value:g}"
                if value_text in lower_target and metric.name.lower() in lower_target:
                    return metric
            for metric in metrics:
                if (
                    metric.name.lower() in lower_target
                    and metric.context
                    and all(word in metric.context.lower() for word in lower_target.split() if len(word) > 5)
                ):
                    return metric
            for metric in metrics:
                if metric.name.lower() in lower_target:
                    return metric
        return metrics[0]

    def _extract_title(self, text: str) -> str | None:
        for line in text.splitlines():
            stripped = line.strip()
            if len(stripped) >= 8 and not stripped.lower().startswith(("abstract", "arxiv")):
                return stripped[:200]
        return None

    def _extract_abstract(self, text: str) -> str | None:
        match = re.search(
            r"\babstract\b\s*(?P<abstract>.+?)(?:\n\s*(?:1\s+)?introduction\b|\n\s*keywords\b)",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None
        return " ".join(match.group("abstract").split())[:1500]

    def _extract_configuration(self, text: str) -> PaperConfiguration:
        compact = " ".join(text.split())
        return PaperConfiguration(
            epochs=self._extract_int(compact, r"(\d+)\s+epochs?"),
            batch_size=self._extract_int(compact, r"batch\s+size\s+(?:of\s+)?(\d+)"),
            optimizer=self._extract_optimizer(compact),
            learning_rate=self._extract_float(
                compact,
                r"(?:learning\s+rate|lr)\s*(?:=|:|of)?\s*([0-9]+(?:\.[0-9]+)?(?:e-\d+)?)",
            ),
            seed=self._extract_int(compact, r"seed\s*(?:=|:)?\s*(\d+)"),
        )

    def _extract_int(self, text: str, pattern: str) -> int | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return int(match.group(1)) if match else None

    def _extract_float(self, text: str, pattern: str) -> float | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    def _extract_optimizer(self, text: str) -> str | None:
        for optimizer in OPTIMIZER_HINTS:
            if re.search(rf"\b{re.escape(optimizer)}\b", text, re.IGNORECASE):
                return optimizer
        return None

    def _extract_datasets(self, text: str) -> list[str]:
        found = []
        if re.search(r"\b(swine|sow|gilt|pig)\b", text, re.IGNORECASE) and re.search(
            r"\bRGB-D|depth frames?|body-condition\b", text, re.IGNORECASE
        ):
            found.append("Swine RGB-D body-condition dataset")
        for dataset in DATASET_HINTS:
            if re.search(rf"\b{re.escape(dataset)}\b", text, re.IGNORECASE):
                found.append("CIFAR-10" if dataset == "CIFAR10" else dataset)
        unique = []
        for dataset in found:
            if dataset not in unique:
                unique.append(dataset)
        return unique

    def _select_dataset(self, text: str, description: str | None) -> str | None:
        datasets = self._extract_datasets(" ".join([description or "", text[:5000]]))
        return datasets[0] if datasets else None

    def _extract_models(self, text: str, description: str | None) -> list[str]:
        candidates = []
        for source in (description or "", text[:8000]):
            candidates.extend(re.findall(r"\b(?:Model|Method|Network)\s+[A-Z][A-Za-z0-9_-]*", source))
        return sorted(set(candidates))[:20]

    def _select_model(self, description: str | None) -> str | None:
        if not description:
            return None
        match = re.search(r"\bModel\s+[A-Za-z0-9_-]+", description)
        return match.group(0) if match else None

    def _extract_table(self, description: str | None) -> str | None:
        if not description:
            return None
        match = re.search(r"\bTable\s+\d+\b", description, re.IGNORECASE)
        return match.group(0) if match else None

    def _default_target_description(self, metric: ReportedMetric | None) -> str:
        if metric and metric.context:
            return metric.context
        return "Unspecified reproduction target"

    def _uncertainties(self, target: ExperimentTarget, text: str) -> list[str]:
        uncertainties = []
        if target.metric is None or target.metric.value is None:
            uncertainties.append("Reported metric value was not detected")
        if target.dataset is None:
            uncertainties.append("Dataset was not detected")
        if not re.search(r"\bseed\b", text, re.IGNORECASE):
            uncertainties.append("Random seed is not reported")
        return uncertainties
