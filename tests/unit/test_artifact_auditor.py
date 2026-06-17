from pathlib import Path

from repro_agent.agents.artifact_auditor import ArtifactAuditor
from repro_agent.schemas.audit import ArtifactCategory, ReproductionStatus
from repro_agent.tools.command_validator import validate_documented_command


def test_artifact_auditor_blocks_missing_scientific_artifacts(tmp_path: Path) -> None:
    command = [
        "python",
        "evaluate_ensemble.py",
        "--checkpoints",
        "results/fold0/best.pt",
        "results/fold1/best.pt",
        "--dataset",
        "data/dataset.h5",
        "--labels",
        "data/label.h5",
        "--split_json",
        "data/split.json",
        "--output",
        "artifacts/metrics.json",
    ]

    audit = ArtifactAuditor().audit(tmp_path, command)

    assert audit.status == ReproductionStatus.BLOCKED
    missing_paths = {artifact.path for artifact in audit.missing_artifacts}
    assert "data/dataset.h5" in missing_paths
    assert "data/label.h5" in missing_paths
    assert "data/split.json" in missing_paths
    assert "results/fold0/best.pt" in missing_paths
    assert all(
        artifact.category != ArtifactCategory.METRICS_OUTPUT
        for artifact in audit.missing_artifacts
    )


def test_command_validator_detects_missing_required_output(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        """
```bash
python evaluate_ensemble.py \\
  --checkpoints results/fold0/best.pt results/fold1/best.pt \\
  --dataset data/dataset.h5 --labels data/label.h5 --split_json data/split.json
```
""",
        encoding="utf-8",
    )
    (tmp_path / "evaluate_ensemble.py").write_text(
        """
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--checkpoints", nargs="+", required=True)
parser.add_argument("--dataset", required=True)
parser.add_argument("--labels", required=True)
parser.add_argument("--split_json", required=True)
parser.add_argument("--output", required=True)
""",
        encoding="utf-8",
    )

    audit = validate_documented_command(tmp_path)

    assert "--output" in audit.missing_required_arguments
    assert audit.corrected_command[-2:] == ["--output", "artifacts/metrics.json"]
    assert any(issue.type == "missing_required_argument" for issue in audit.documentation_issues)
