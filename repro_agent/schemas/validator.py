"""Validation helpers for ReproAgent's JSON output contracts."""

from __future__ import annotations

from importlib.resources import files
import json
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


SCHEMA_PACKAGE = "repro_agent.schemas.json"


def validate_output(schema_name: str, data: dict[str, Any]) -> None:
    schema = _load_schema(schema_name)
    common = _load_schema("common")
    common_resource = Resource.from_contents(common)
    registry = (
        Registry()
        .with_resource(common["$id"], common_resource)
        .with_resource(
            "https://reproagent.dev/schemas/common.json",
            common_resource,
        )
    )
    validator = Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    validator.validate(data)


def _load_schema(schema_name: str) -> dict[str, Any]:
    path = files(SCHEMA_PACKAGE).joinpath(f"{schema_name}.json")
    return json.loads(path.read_text(encoding="utf-8"))
