"""Static validation for documented experiment commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from repro_agent.schemas.audit import DocumentationIssue
from repro_agent.tools.code_search import extract_readme_commands


PATH_ARGUMENTS = {
    "--checkpoint",
    "--checkpoints",
    "--ckpt",
    "--weights",
    "--dataset",
    "--data",
    "--labels",
    "--label",
    "--split",
    "--split_json",
    "--config",
    "--output",
}


@dataclass(frozen=True)
class StaticCommandValidation:
    documented_command: list[str]
    corrected_command: list[str]
    command_valid: bool
    missing_required_arguments: list[str]
    missing_referenced_paths: list[str]
    documentation_issues: list[DocumentationIssue]


def validate_documented_command(repo_path: Path) -> StaticCommandValidation:
    commands = extract_readme_commands(repo_path)
    documented = commands[0] if commands else []
    corrected = list(documented)
    issues: list[DocumentationIssue] = []

    script = _script_from_command(documented)
    required_args = _required_args(repo_path / script) if script else []
    supplied_args = {part for part in documented if part.startswith("--")}

    missing_required = [arg for arg in required_args if arg not in supplied_args]
    for arg in missing_required:
        issues.append(
            DocumentationIssue(
                type="missing_required_argument",
                message=f"README command omits required argument {arg}.",
                command_argument=arg,
                source="README example command",
            )
        )
        corrected.extend([arg, _default_value_for(arg)])

    missing_paths = _missing_referenced_paths(repo_path, corrected)
    command_valid = not missing_required and not missing_paths
    return StaticCommandValidation(
        documented_command=documented,
        corrected_command=corrected,
        command_valid=command_valid,
        missing_required_arguments=missing_required,
        missing_referenced_paths=missing_paths,
        documentation_issues=issues,
    )


def _script_from_command(command: list[str]) -> str | None:
    return next((part for part in command if part.endswith(".py")), None)


def _required_args(script_path: Path) -> list[str]:
    if not script_path.exists():
        return []
    text = script_path.read_text(encoding="utf-8", errors="ignore")
    required: list[str] = []
    pattern = re.compile(
        r"add_argument\(\s*['\"](?P<arg>--[A-Za-z0-9_-]+)['\"][^)]*required\s*=\s*True",
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        arg = match.group("arg")
        if arg not in required:
            required.append(arg)
    return required


def _missing_referenced_paths(repo_path: Path, command: list[str]) -> list[str]:
    paths = []
    for index, part in enumerate(command):
        if part not in PATH_ARGUMENTS:
            continue
        for value in _values_for_arg(command, index):
            if part == "--output":
                continue
            if not (repo_path / value).exists():
                paths.append(value)
    return paths


def _values_for_arg(command: list[str], index: int) -> list[str]:
    values: list[str] = []
    for value in command[index + 1 :]:
        if value.startswith("--"):
            break
        values.append(value)
    return values


def _default_value_for(argument: str) -> str:
    if argument == "--output":
        return "artifacts/metrics.json"
    return "TODO"
