from pathlib import Path

from repro_agent.orchestrator import Orchestrator
from repro_agent.schemas.research import PreparationStatus, ResearchMode


def _write_baseline_repo(repo: Path) -> None:
    repo.mkdir()
    (repo / "README.md").write_text(
        """
```bash
python evaluate.py --dataset data/dataset.h5 --labels data/label.h5 --output metrics.json
```
""",
        encoding="utf-8",
    )
    (repo / "evaluate.py").write_text(
        """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", required=True)
parser.add_argument("--labels", required=True)
parser.add_argument("--output", required=True)
""",
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.10"\ndependencies = ["torch>=2.1"]\n',
        encoding="utf-8",
    )


def _write_candidate_repo(repo: Path) -> None:
    repo.mkdir()
    (repo / "README.md").write_text(
        """
```bash
python evaluate.py --dataset data/dataset.h5 --output candidate-metrics.json
```
""",
        encoding="utf-8",
    )
    (repo / "evaluate.py").write_text(
        """
import argparse
import torch
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", required=True)
parser.add_argument("--output", required=True)
""",
        encoding="utf-8",
    )
    (repo / "requirements.txt").write_text("torch>=2.1\n", encoding="utf-8")


def test_exact_baseline_remains_blocked_when_original_artifacts_are_missing(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "baseline"
    _write_baseline_repo(repo)

    _, _, plan = Orchestrator().prepare_baseline(
        paper=Path("tests/fixtures/paper.txt"),
        repo=str(repo),
        target="Table 2 accuracy",
        mode=ResearchMode.EXACT_REPRODUCTION,
    )

    assert plan.status == PreparationStatus.BLOCKED
    assert any(option.preserves_exact_reproduction for option in plan.options)
    assert any(not option.preserves_exact_reproduction for option in plan.options)


def test_fair_comparison_requires_protocol_definition_with_user_dataset(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    dataset = tmp_path / "shared-data"
    dataset.mkdir()
    _write_baseline_repo(baseline)
    _write_candidate_repo(candidate)

    _, _, plan = Orchestrator().plan_comparison(
        paper=Path("tests/fixtures/paper.txt"),
        baseline_repo=str(baseline),
        candidate_repo=str(candidate),
        target="Table 2 accuracy",
        dataset=dataset,
        mode=ResearchMode.FAIR_BENCHMARK,
    )

    assert plan.status == PreparationStatus.PROTOCOL_DEFINITION_REQUIRED
    assert plan.shared_protocol["dataset"] == str(dataset.resolve())
    assert plan.shared_protocol["execution_available"] is False
    assert "Use the same train/validation/test split." in plan.fairness_requirements


def test_missing_supplied_dataset_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "baseline"
    _write_baseline_repo(repo)

    try:
        Orchestrator().prepare_baseline(
            paper=Path("tests/fixtures/paper.txt"),
            repo=str(repo),
            target="Table 2 accuracy",
            dataset=tmp_path / "missing-data",
        )
    except FileNotFoundError as exc:
        assert "Supplied dataset path" in str(exc)
    else:
        raise AssertionError("Expected a missing supplied dataset to be rejected")
