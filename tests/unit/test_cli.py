import json
from pathlib import Path

from repro_agent.cli import main


def test_audit_cli_writes_validated_outputs(tmp_path: Path) -> None:
    output = tmp_path / "audit"
    result = main(
        [
            "audit",
            "--paper",
            "tests/fixtures/paper.txt",
            "--repo",
            "tests/fixtures/sample_repo",
            "--target",
            "Table 2 accuracy",
            "--output-dir",
            str(output),
        ]
    )

    assert result == 0
    audit = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    artifact = json.loads(
        (output / "artifact-audit.json").read_text(encoding="utf-8")
    )
    assert audit["metadata"]["schema_version"] == "0.2.0"
    assert artifact["metadata"] == audit["metadata"]


def test_environment_plan_cli_writes_dockerfile(tmp_path: Path) -> None:
    output = tmp_path / "environment"
    result = main(
        [
            "environment-plan",
            "--repo",
            "tests/fixtures/sample_repo",
            "--output-dir",
            str(output),
        ]
    )

    assert result == 0
    assert (output / "environment-plan.json").exists()
    assert (output / "Dockerfile.reproagent").exists()
