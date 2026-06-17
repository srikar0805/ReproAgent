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
    assert audit.missing_artifacts[0].finding_id == "ART-001"
    assert audit.missing_artifacts[0].confidence >= 0.9
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


def test_artifact_audit_includes_structured_code_evidence(tmp_path: Path) -> None:
    (tmp_path / "evaluate_ensemble.py").write_text(
        """
import json
import h5py
import torch

def main(args):
    ckpts = [torch.load(path) for path in args.checkpoints]
    data = h5py.File(args.dataset)
    labels = h5py.File(args.labels)
    split = json.loads(open(args.split_json).read())
""",
        encoding="utf-8",
    )
    command = [
        "python",
        "evaluate_ensemble.py",
        "--checkpoints",
        "results/fold0/best.pt",
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
    by_path = {artifact.path: artifact for artifact in audit.missing_artifacts}

    assert any(
        evidence.source == "evaluate_ensemble.py"
        and evidence.operation == "h5py.File"
        and evidence.line is not None
        for evidence in by_path["data/dataset.h5"].evidence
    )
    assert by_path["data/dataset.h5"].searched_locations == [
        "repository",
        "git_lfs",
        "github_releases",
        "linked_downloads",
    ]
    assert by_path["data/dataset.h5"].impact is not None
    assert by_path["data/dataset.h5"].impact.blocks_execution is True
