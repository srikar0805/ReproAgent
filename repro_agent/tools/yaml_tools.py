"""Small YAML writer for ReproAgent's simple data files."""

from __future__ import annotations

import re
from typing import Any


def dumps_yaml(data: dict[str, Any]) -> str:
    return "\n".join(_render_mapping(data, 0)) + "\n"


def _render_mapping(data: dict[str, Any], indent: int) -> list[str]:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.extend(_render_mapping(value, indent + 2))
        elif isinstance(value, list):
            if value:
                lines.append(f"{prefix}{key}:")
                lines.extend(_render_list(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: []")
        else:
            lines.append(f"{prefix}{key}: {_format_scalar(value)}")
    return lines


def _render_list(values: list[Any], indent: int) -> list[str]:
    prefix = " " * indent
    lines: list[str] = []
    if not values:
        return [f"{prefix}[]"]
    for value in values:
        if isinstance(value, dict):
            lines.append(f"{prefix}-")
            lines.extend(_render_mapping(value, indent + 2))
        elif isinstance(value, list):
            lines.append(f"{prefix}-")
            lines.extend(_render_list(value, indent + 2))
        else:
            lines.append(f"{prefix}- {_format_scalar(value)}")
    return lines


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    if (
        text == ""
        or re.fullmatch(r"\d+\.\d+(?:\.\d+)?", text)
        or any(char in text for char in ":#[]{}&,*?|\n<>=%@`")
    ):
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text
