"""Git helpers."""

from __future__ import annotations

from pathlib import Path
import subprocess


def get_commit(repo_path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def get_remote_url(repo_path: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def clone_repository(url: str, destination: Path) -> Path:
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(destination)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"Failed to clone {url}")
    return destination


def looks_like_url(source: str) -> bool:
    return source.startswith(("https://", "http://", "git@"))
