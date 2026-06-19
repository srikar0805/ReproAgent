"""Generate isolated environment reconstruction plans."""

from __future__ import annotations

from pathlib import Path
import re

from repro_agent import __version__
from repro_agent.sandbox.executor import SandboxExecutor
from repro_agent.sandbox.policies import FORBIDDEN_MOUNTS
from repro_agent.sandbox.resource_limits import (
    DEFAULT_CPU_COUNT,
    DEFAULT_MEMORY,
    DEFAULT_PIDS_LIMIT,
)
from repro_agent.schemas.environment import (
    EnvironmentBuildPlan,
    EnvironmentPlanStatus,
    ResourcePolicy,
)
from repro_agent.schemas.experiment import RepositoryInspection
from repro_agent.tools.docker_tools import planned_image_name


class EnvironmentBuilder:
    def plan(
        self,
        repo_path: Path,
        inspection: RepositoryInspection,
        artifact_dir: Path,
        dockerfile_path: Path | None = None,
    ) -> EnvironmentBuildPlan:
        image_name = planned_image_name(inspection.commit)
        python_version = self._python_version(inspection.python_version)
        dockerfile_name = "Dockerfile.reproagent"
        resolved_dockerfile = (
            dockerfile_path.resolve()
            if dockerfile_path is not None
            else (repo_path / dockerfile_name).resolve()
        )
        install_lines, status, notes = self._install_lines(inspection.dependency_sources)
        dockerfile = self._dockerfile(python_version, install_lines)
        policy = ResourcePolicy(
            cpus=DEFAULT_CPU_COUNT,
            memory=DEFAULT_MEMORY,
            pids_limit=DEFAULT_PIDS_LIMIT,
            timeout_seconds=900,
            network_enabled=False,
            read_only_root=True,
            cap_drop=["ALL"],
            forbidden_mounts=list(FORBIDDEN_MOUNTS),
        )
        executor = SandboxExecutor(policy)
        run_prefix = executor.run_prefix(
            image_name=image_name,
            artifact_dir=artifact_dir,
        )
        return EnvironmentBuildPlan(
            schema_version="0.2.0",
            tool_version=__version__,
            status=status,
            repository=inspection.url or inspection.source,
            repository_commit=inspection.commit,
            python_version=python_version,
            framework=inspection.framework,
            dependency_sources=inspection.dependency_sources,
            image_name=image_name,
            dockerfile_name=dockerfile_name,
            dockerfile=dockerfile,
            build_command=[
                "docker",
                "build",
                "-t",
                image_name,
                "-f",
                str(resolved_dockerfile),
                str(repo_path.resolve()),
            ],
            run_prefix=run_prefix,
            resource_policy=policy,
            smoke_tests=executor.progressive_smoke_tests(inspection),
            notes=[
                *notes,
                "Docker is required to execute this plan.",
                "Dependency installation requires explicit network approval.",
                "Full experiments require a separate explicit approval.",
            ],
        )

    def _python_version(self, declared: str | None) -> str:
        if not declared:
            return "3.10"
        match = re.search(r"(\d+\.\d+)", declared)
        return match.group(1) if match else "3.10"

    def _install_lines(
        self, dependency_sources: list[str]
    ) -> tuple[list[str], EnvironmentPlanStatus, list[str]]:
        if "requirements.txt" in dependency_sources:
            return (
                ["RUN python -m pip install --no-cache-dir -r requirements.txt"],
                EnvironmentPlanStatus.PLANNED,
                [],
            )
        if "pyproject.toml" in dependency_sources:
            return (
                ["RUN python -m pip install --no-cache-dir ."],
                EnvironmentPlanStatus.PLANNED,
                [],
            )
        conda = next(
            (
                path
                for path in dependency_sources
                if Path(path).name
                in {"environment.yml", "environment.yaml", "conda.yml", "conda.yaml"}
            ),
            None,
        )
        if conda:
            return (
                [],
                EnvironmentPlanStatus.UNSUPPORTED,
                [f"Conda environment detected at {conda}; Docker generation is not implemented."],
            )
        return (
            [],
            EnvironmentPlanStatus.UNSUPPORTED,
            ["No supported dependency source was detected."],
        )

    def _dockerfile(self, python_version: str, install_lines: list[str]) -> str:
        lines = [
            f"FROM python:{python_version}-slim",
            "",
            "RUN useradd --create-home --uid 1000 repro",
            "WORKDIR /workspace",
            "",
            "COPY . /workspace",
            "RUN python -m pip install --no-cache-dir --upgrade pip",
            *install_lines,
            "",
            "RUN mkdir -p /artifacts && chown repro:repro /artifacts",
            "USER repro",
            "",
            'ENV PYTHONDONTWRITEBYTECODE="1"',
            'ENV PYTHONUNBUFFERED="1"',
        ]
        return "\n".join(lines) + "\n"
