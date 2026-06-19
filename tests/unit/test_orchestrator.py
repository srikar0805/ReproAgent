from pathlib import Path

from repro_agent.orchestrator import Orchestrator
from repro_agent.schemas.common import to_plain_data
from repro_agent.schemas.audit import ReproductionStatus
from repro_agent.tools.yaml_tools import dumps_yaml


def test_init_reproduction_generates_spec() -> None:
    spec = Orchestrator().init_reproduction(
        Path("tests/fixtures/paper.txt"),
        "tests/fixtures/sample_repo",
        "Table 2, Model A, CIFAR-10 accuracy",
    )
    data = to_plain_data(spec)

    assert data["schema_version"] == "0.1"
    assert data["target"]["reported_metric"]["name"] == "accuracy"
    assert data["environment"]["framework"] == "pytorch"
    assert data["execution"]["command"][0] == "python"
    assert "schema_version" in dumps_yaml(data)


def test_audit_blocks_when_command_artifacts_are_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
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
    (repo / "pyproject.toml").write_text("[project]\nrequires-python = \">=3.10\"\n", encoding="utf-8")

    _, audit = Orchestrator().audit(
        Path("tests/fixtures/paper.txt"),
        str(repo),
        "Table 2 accuracy",
    )

    assert audit.status == ReproductionStatus.BLOCKED
    assert audit.verdict.status == "blocked"
    assert audit.verdict.reproducible_from_public_materials is False
    assert audit.metadata.schema_version == "0.2.0"
    assert audit.metadata.paper_hash is not None
