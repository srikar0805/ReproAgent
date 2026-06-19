"""Infer a reviewable candidate-model evaluation adapter."""

from __future__ import annotations

from repro_agent import __version__
from repro_agent.schemas.adapter import AdapterStatus, CandidateAdapterPlan
from repro_agent.schemas.experiment import RepositoryInspection


class CandidateAdapterBuilder:
    def plan(self, inspection: RepositoryInspection) -> CandidateAdapterPlan:
        entrypoint = inspection.entrypoints.evaluate
        command = self._evaluation_command(inspection, entrypoint)
        supplied = {part for part in command if part.startswith("--")}
        inputs = {
            "dataset_argument": self._first_present(
                supplied, "--dataset", "--data"
            ),
            "split_argument": self._first_present(
                supplied, "--split_json", "--split"
            ),
            "checkpoint_argument": self._first_present(
                supplied, "--checkpoint", "--checkpoints", "--weights"
            ),
        }
        output_argument = self._first_present(supplied, "--output")
        missing = []
        if not entrypoint:
            missing.append("evaluation_entrypoint")
        if inputs["dataset_argument"] is None:
            missing.append("dataset_argument")
        if output_argument is None:
            missing.append("output_argument")
        return CandidateAdapterPlan(
            schema_version="0.2.0",
            tool_version=__version__,
            status=AdapterStatus.INCOMPLETE if missing else AdapterStatus.PLANNED,
            repository=inspection.url or inspection.source,
            repository_commit=inspection.commit,
            framework=inspection.framework,
            evaluation_entrypoint=entrypoint,
            evaluation_command=command,
            input_arguments=inputs,
            output_contract={
                "output_argument": output_argument,
                "format": "json" if output_argument else None,
                "metric_key": None,
            },
            required_methods=[
                "build_model(config)",
                "load_checkpoint(checkpoint_path)",
                "preprocess(batch)",
                "predict(batch)",
                "format_predictions(output)",
            ],
            scientific_constraints=[
                "Use the shared dataset and split.",
                "Use the shared preprocessing unless an approved adapter is required.",
                "Use the shared metric implementation.",
                "Record every input/output transformation.",
            ],
            missing_fields=missing,
        )

    def _evaluation_command(
        self, inspection: RepositoryInspection, entrypoint: str | None
    ) -> list[str]:
        if not entrypoint:
            return []
        if entrypoint in inspection.candidate_command:
            return inspection.candidate_command
        return ["python", entrypoint]

    def _first_present(self, supplied: set[str], *options: str) -> str | None:
        return next((option for option in options if option in supplied), None)
