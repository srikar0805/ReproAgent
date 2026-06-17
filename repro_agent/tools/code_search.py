"""Code search helpers for likely experiment entry points."""

from __future__ import annotations

from pathlib import Path
import re


TRAIN_HINTS = ("train", "fit", "main")
EVAL_HINTS = ("eval", "evaluate", "test", "validate")
CONFIG_SUFFIXES = (".yaml", ".yml", ".json", ".toml")


def find_entrypoints(repo_path: Path) -> tuple[str | None, str | None, list[str]]:
    candidates = [
        path
        for path in repo_path.rglob("*.py")
        if not _skip_path(path) and _looks_executable(path)
    ]
    rel_candidates = [path.relative_to(repo_path).as_posix() for path in candidates]

    train = _best_match(rel_candidates, TRAIN_HINTS)
    evaluate = _best_match(rel_candidates, EVAL_HINTS)
    return train, evaluate, rel_candidates[:25]


def find_configs(repo_path: Path) -> list[str]:
    configs: list[str] = []
    for path in repo_path.rglob("*"):
        if _skip_path(path) or not path.is_file():
            continue
        if path.suffix.lower() in CONFIG_SUFFIXES and _configish(path):
            configs.append(path.relative_to(repo_path).as_posix())
    return sorted(configs)[:50]


def extract_readme_commands(repo_path: Path) -> list[list[str]]:
    readme = _readme(repo_path)
    if readme is None:
        return []

    commands: list[list[str]] = []
    pending = ""
    for raw_line in readme.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("```", "#")):
            continue
        if pending:
            pending = f"{pending} {line}"
        else:
            pending = line
        if pending.endswith("\\"):
            pending = pending[:-1].strip()
            continue
        line = pending
        pending = ""
        line = line.strip().removeprefix("$").strip()
        if _is_setup_command(line):
            continue
        if not line.startswith(("python ", "python3 ", "torchrun ")):
            continue
        commands.append(_split_shell_words(line))
    return commands[:10]


def _is_setup_command(line: str) -> bool:
    setup_markers = (
        "python -m venv",
        "pip install",
        "conda ",
        "source ",
        "activate",
        "&&",
    )
    lower = line.lower()
    return any(marker in lower for marker in setup_markers)


def _split_shell_words(line: str) -> list[str]:
    import shlex

    return shlex.split(line)


def summarize_readme(repo_path: Path) -> str | None:
    readme = _readme(repo_path)
    if readme is None:
        return None
    lines = [line.strip() for line in readme.splitlines() if line.strip()]
    return " ".join(lines[:6])[:800]


def _readme(repo_path: Path) -> str | None:
    for name in ("README.md", "README.rst", "README.txt", "readme.md"):
        path = repo_path / name
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
    return None


def _best_match(paths: list[str], hints: tuple[str, ...]) -> str | None:
    scored: list[tuple[int, str]] = []
    for path in paths:
        lower = path.lower()
        score = 0
        for hint in hints:
            if re.search(rf"(^|[/_\-]){re.escape(hint)}([/_\-.]|$)", lower):
                score += 3
            elif hint in lower:
                score += 1
        if score:
            scored.append((score, path))
    if not scored:
        return None
    return sorted(scored, key=lambda item: (-item[0], len(item[1]), item[1]))[0][1]


def _looks_executable(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "if __name__" in text or "argparse" in text or "click.command" in text


def _configish(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return "config" in path.stem.lower() or "configs" in parts or "config" in parts


def _skip_path(path: Path) -> bool:
    ignored_parts = {".git", ".venv", "venv", "__pycache__", "site-packages"}
    return any(part in ignored_parts for part in path.parts)
