"""Repository dependency and framework detection."""

from __future__ import annotations

from pathlib import Path


DEPENDENCY_FILES = (
    "requirements.txt",
    "environment.yml",
    "environment.yaml",
    "conda.yml",
    "conda.yaml",
    "pyproject.toml",
    "setup.py",
)

FRAMEWORK_MARKERS = {
    "pytorch": ("torch", "torchvision", "pytorch-lightning", "lightning"),
    "tensorflow": ("tensorflow", "keras"),
    "jax": ("jax", "flax", "optax"),
    "scikit-learn": ("sklearn", "scikit-learn"),
}


def find_dependency_files(repo_path: Path) -> list[str]:
    found: list[str] = []
    for name in DEPENDENCY_FILES:
        for path in repo_path.rglob(name):
            if _skip_path(path):
                continue
            found.append(path.relative_to(repo_path).as_posix())
    return sorted(found)


def detect_framework(repo_path: Path, dependency_files: list[str]) -> str | None:
    haystack_parts: list[str] = []
    for rel_path in dependency_files[:10]:
        path = repo_path / rel_path
        if path.exists():
            haystack_parts.append(path.read_text(encoding="utf-8", errors="ignore"))

    for path in list(repo_path.rglob("*.py"))[:200]:
        if _skip_path(path):
            continue
        haystack_parts.append(path.read_text(encoding="utf-8", errors="ignore"))

    haystack = "\n".join(haystack_parts).lower()
    for framework, markers in FRAMEWORK_MARKERS.items():
        if any(marker in haystack for marker in markers):
            return framework
    return None


def detect_python_version(repo_path: Path) -> str | None:
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        for line in pyproject.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "requires-python" in line:
                return line.split("=", 1)[-1].strip().strip('"').strip("'")

    runtime = repo_path / "runtime.txt"
    if runtime.exists():
        text = runtime.read_text(encoding="utf-8", errors="ignore").strip()
        if text.startswith("python-"):
            return text.removeprefix("python-")
    return None


def _skip_path(path: Path) -> bool:
    ignored_parts = {".git", ".venv", "venv", "__pycache__", "site-packages"}
    return any(part in ignored_parts for part in path.parts)
