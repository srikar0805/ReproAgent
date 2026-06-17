"""Environment planning agent for the Docker milestone."""

from __future__ import annotations

from repro_agent.schemas.experiment import RepositoryInspection
from repro_agent.tools.docker_tools import build_command, planned_image_name


class EnvironmentBuilder:
    def plan(self, inspection: RepositoryInspection) -> dict:
        image_name = planned_image_name(inspection.commit)
        return {
            "docker_image": image_name,
            "build_command": build_command(image_name),
            "dependency_sources": inspection.dependency_sources,
            "notes": [
                "Docker execution is planned but not implemented in milestone 1.",
                "Network access must be explicitly approved before dependency installation.",
            ],
        }
