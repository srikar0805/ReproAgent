from pathlib import Path

from repro_agent.orchestrator import Orchestrator
from repro_agent.schemas.common import to_plain_data
from repro_agent.schemas.environment import EnvironmentPlanStatus, SmokeStage
from repro_agent.schemas.validator import validate_output


def test_environment_plan_enforces_sandbox_defaults(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    plan = Orchestrator().plan_environment(
        repo="tests/fixtures/sample_repo",
        artifact_dir=artifact_dir,
        dockerfile_path=tmp_path / "Dockerfile.reproagent",
    )

    assert plan.status == EnvironmentPlanStatus.PLANNED
    assert "USER repro" in plan.dockerfile
    assert "--network" in plan.run_prefix
    assert "none" in plan.run_prefix
    assert "--read-only" in plan.run_prefix
    assert "--cap-drop" in plan.run_prefix
    assert "/var/run/docker.sock" in plan.resource_policy.forbidden_mounts
    assert plan.build_command[-3:] == [
        "-f",
        str((tmp_path / "Dockerfile.reproagent").resolve()),
        str(Path("tests/fixtures/sample_repo").resolve()),
    ]
    assert [step.stage for step in plan.smoke_tests[:2]] == [
        SmokeStage.IMPORTS,
        SmokeStage.CLI_HELP,
    ]
    assert plan.smoke_tests[-1].requires_approval is True
    validate_output("environment-plan", to_plain_data(plan))
