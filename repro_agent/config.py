"""Runtime configuration for ReproAgent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    artifact_dir: Path
    default_device: str
    allow_network: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            artifact_dir=Path(os.getenv("REPRO_AGENT_ARTIFACT_DIR", "artifacts")),
            default_device=os.getenv("REPRO_AGENT_DEFAULT_DEVICE", "cpu"),
            allow_network=os.getenv("REPRO_AGENT_ALLOW_NETWORK", "false").lower()
            in {"1", "true", "yes"},
        )
