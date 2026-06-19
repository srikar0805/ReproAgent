from pathlib import Path

from jsonschema import ValidationError

from repro_agent.orchestrator import Orchestrator
from repro_agent.schemas.common import to_plain_data
from repro_agent.schemas.research import ResearchMode
from repro_agent.schemas.validator import validate_output


def test_audit_and_component_envelopes_validate(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text(
        """
```bash
python evaluate.py --dataset data/test.csv --output metrics.json
```
""",
        encoding="utf-8",
    )
    (repo / "evaluate.py").write_text(
        """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", required=True)
parser.add_argument("--output", required=True)
""",
        encoding="utf-8",
    )
    (repo / "requirements.txt").write_text("numpy>=1.24\n", encoding="utf-8")

    _, audit = Orchestrator().audit(
        Path("tests/fixtures/paper.txt"),
        str(repo),
        "Table 2 accuracy",
    )
    audit_data = to_plain_data(audit)
    validate_output("audit", audit_data)
    validate_output(
        "artifact-audit",
        {
            "metadata": audit_data["metadata"],
            "artifact_audit": audit_data["artifact_audit"],
        },
    )
    validate_output(
        "command-audit",
        {
            "metadata": audit_data["metadata"],
            "command_audit": audit_data["command_audit"],
        },
    )
    validate_output(
        "environment-audit",
        {
            "metadata": audit_data["metadata"],
            "environment_audit": audit_data["environment_audit"],
        },
    )


def test_invalid_schema_version_is_rejected() -> None:
    invalid = {
        "metadata": {
            "schema_version": "0.1.0",
            "tool_version": "0.2.0",
            "audit_id": "audit-0123456789ab",
            "created_at": "2026-06-18T00:00:00Z",
            "repository_commit": None,
            "paper_hash": None,
        },
        "artifact_audit": {
            "required_artifacts": [],
            "available_artifacts": [],
            "missing_artifacts": [],
            "external_links": [],
            "status": "inspected",
        },
    }

    try:
        validate_output("artifact-audit", invalid)
    except ValidationError:
        pass
    else:
        raise AssertionError("Expected invalid schema version to be rejected")


def test_baseline_and_comparison_plans_validate(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    dataset = tmp_path / "data"
    baseline.mkdir()
    candidate.mkdir()
    dataset.mkdir()
    for repo in (baseline, candidate):
        (repo / "README.md").write_text(
            """
```bash
python evaluate.py --dataset data/test.csv --output metrics.json
```
""",
            encoding="utf-8",
        )
        (repo / "evaluate.py").write_text(
            """
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", required=True)
parser.add_argument("--output", required=True)
""",
            encoding="utf-8",
        )
        (repo / "requirements.txt").write_text("numpy>=1.24\n", encoding="utf-8")

    orchestrator = Orchestrator()
    _, _, baseline_plan = orchestrator.prepare_baseline(
        paper=Path("tests/fixtures/paper.txt"),
        repo=str(baseline),
        target="Table 2 accuracy",
        mode=ResearchMode.FAIR_BENCHMARK,
        dataset=dataset,
    )
    _, _, comparison_plan = orchestrator.plan_comparison(
        paper=Path("tests/fixtures/paper.txt"),
        baseline_repo=str(baseline),
        candidate_repo=str(candidate),
        target="Table 2 accuracy",
        dataset=dataset,
        mode=ResearchMode.FAIR_BENCHMARK,
    )

    validate_output("baseline-plan", to_plain_data(baseline_plan))
    validate_output("comparison-plan", to_plain_data(comparison_plan))
