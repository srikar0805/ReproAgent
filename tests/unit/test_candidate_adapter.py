from pathlib import Path

from repro_agent.orchestrator import Orchestrator
from repro_agent.schemas.adapter import AdapterStatus
from repro_agent.schemas.common import to_plain_data
from repro_agent.schemas.validator import validate_output


def test_candidate_adapter_detects_evaluation_contract() -> None:
    plan = Orchestrator().plan_candidate_adapter(
        "tests/fixtures/sample_candidate_repo"
    )

    assert plan.status == AdapterStatus.PLANNED
    assert plan.evaluation_entrypoint == "evaluate.py"
    assert plan.input_arguments["dataset_argument"] == "--dataset"
    assert plan.output_contract["output_argument"] == "--output"
    validate_output("candidate-adapter", to_plain_data(plan))


def test_candidate_adapter_is_incomplete_without_evaluator(tmp_path: Path) -> None:
    repo = tmp_path / "candidate"
    repo.mkdir()
    (repo / "requirements.txt").write_text("torch>=2.1\n", encoding="utf-8")
    (repo / "train.py").write_text(
        'if __name__ == "__main__":\n    pass\n',
        encoding="utf-8",
    )

    plan = Orchestrator().plan_candidate_adapter(str(repo))

    assert plan.status == AdapterStatus.INCOMPLETE
    assert "evaluation_entrypoint" in plan.missing_fields
