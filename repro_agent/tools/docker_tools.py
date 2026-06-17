"""Docker command planning helpers."""

from __future__ import annotations


def planned_image_name(commit: str | None) -> str:
    suffix = commit[:7] if commit else "unknown"
    return f"repro-agent/run:{suffix}"


def build_command(image_name: str, context: str = ".") -> list[str]:
    return ["docker", "build", "-t", image_name, context]
