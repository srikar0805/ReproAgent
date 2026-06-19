"""Generate sandboxed execution commands without executing them."""

from __future__ import annotations

from pathlib import Path

from repro_agent.schemas.environment import ResourcePolicy, SmokeStage, SmokeTestStep
from repro_agent.schemas.experiment import RepositoryInspection


class SandboxExecutor:
    def __init__(self, policy: ResourcePolicy) -> None:
        self.policy = policy

    def run_prefix(self, image_name: str, artifact_dir: Path) -> list[str]:
        prefix = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cpus",
            str(self.policy.cpus),
            "--memory",
            self.policy.memory,
            "--pids-limit",
            str(self.policy.pids_limit),
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=512m",
            "--mount",
            f"type=bind,src={artifact_dir.resolve()},dst=/artifacts",
            image_name,
        ]
        return prefix

    def progressive_smoke_tests(
        self, inspection: RepositoryInspection
    ) -> list[SmokeTestStep]:
        imports = ["python", "-c", self._import_script(inspection.framework)]
        steps = [
            SmokeTestStep(
                stage=SmokeStage.IMPORTS,
                command=imports,
                timeout_seconds=60,
            )
        ]
        entrypoint = inspection.entrypoints.evaluate or inspection.entrypoints.train
        if entrypoint:
            steps.append(
                SmokeTestStep(
                    stage=SmokeStage.CLI_HELP,
                    command=["python", entrypoint, "--help"],
                    timeout_seconds=60,
                )
            )
        steps.extend(
            [
                SmokeTestStep(
                    stage=SmokeStage.CONFIGURATION,
                    command=["repro-agent-internal", "validate-config"],
                    timeout_seconds=60,
                    notes=["Static configuration/path validation; no repository code execution."],
                ),
                SmokeTestStep(
                    stage=SmokeStage.DATASET_LOADER,
                    command=["repro-agent-internal", "dataset-loader-smoke-test"],
                    timeout_seconds=120,
                    requires_dataset=True,
                    requires_approval=True,
                ),
                SmokeTestStep(
                    stage=SmokeStage.CHECKPOINT_LOADING,
                    command=["repro-agent-internal", "checkpoint-load-smoke-test"],
                    timeout_seconds=120,
                    requires_checkpoint=True,
                    requires_approval=True,
                ),
                SmokeTestStep(
                    stage=SmokeStage.ONE_BATCH_INFERENCE,
                    command=["repro-agent-internal", "one-batch-inference"],
                    timeout_seconds=300,
                    requires_dataset=True,
                    requires_checkpoint=True,
                    requires_approval=True,
                ),
                SmokeTestStep(
                    stage=SmokeStage.SHORT_EXPERIMENT,
                    command=["repro-agent-internal", "short-experiment"],
                    timeout_seconds=900,
                    requires_dataset=True,
                    requires_approval=True,
                ),
                SmokeTestStep(
                    stage=SmokeStage.FULL_EXPERIMENT,
                    command=inspection.candidate_command,
                    timeout_seconds=0,
                    requires_dataset=True,
                    requires_approval=True,
                    notes=["Not eligible until all earlier stages pass."],
                ),
            ]
        )
        return steps

    def _import_script(self, framework: str | None) -> str:
        module = {
            "pytorch": "torch",
            "tensorflow": "tensorflow",
            "jax": "jax",
            "scikit-learn": "sklearn",
        }.get(framework)
        if module:
            return f"import {module}; print({module}.__version__)"
        return "print('No framework-specific import detected')"
