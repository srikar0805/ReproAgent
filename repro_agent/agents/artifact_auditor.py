"""Artifact completeness auditor."""

from __future__ import annotations

from pathlib import Path

from repro_agent.schemas.audit import ArtifactAudit, ReproductionStatus
from repro_agent.tools.artifact_discovery import (
    extract_external_links,
    inventory_files,
    missing_artifacts,
    required_artifacts_from_command,
)


class ArtifactAuditor:
    def audit(self, repo_path: Path, command: list[str]) -> ArtifactAudit:
        required = required_artifacts_from_command(command, repo_path=repo_path)
        missing = missing_artifacts(repo_path, required)
        status = ReproductionStatus.BLOCKED if missing else ReproductionStatus.INSPECTED
        return ArtifactAudit(
            required_artifacts=required,
            available_artifacts=inventory_files(repo_path),
            missing_artifacts=missing,
            external_links=extract_external_links(repo_path),
            status=status,
        )
