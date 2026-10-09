"""Load YAML and validate it against the JSON Schema."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, cast

import jsonschema
import yaml

SCHEMA_NAME = "azure-diagram.schema.json"


class SchemaValidationError(Exception):
    """The document does not match the JSON Schema; `errors` holds one message per problem."""

    def __init__(self, errors: list[str]) -> None:
        """Store the individual error messages."""
        super().__init__("\n".join(errors))
        self.errors = errors


def load_schema() -> dict[str, Any]:
    """Return the JSON Schema, from the installed package or else the source checkout."""
    packaged = resources.files("azdiagram").joinpath(SCHEMA_NAME)
    text = packaged.read_text(encoding="utf-8") if packaged.is_file() else _repo_schema().read_text(encoding="utf-8")
    return cast("dict[str, Any]", json.loads(text))


def _repo_schema() -> Path:
    return Path(__file__).resolve().parents[2] / "schema" / SCHEMA_NAME


def _path(error: jsonschema.ValidationError) -> str:
    out = ""
    for part in error.absolute_path:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out or "(root)"


def validate(doc: object) -> None:
    """Raise SchemaValidationError listing every schema violation in `doc`."""
    validator = jsonschema.Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(doc), key=lambda e: [str(p) for p in e.absolute_path])
    if errors:
        raise SchemaValidationError([f"{_path(e)}: {e.message}" for e in errors])


def load(path: str | Path) -> dict[str, Any]:
    """Read and validate a YAML document."""
    with open(path, encoding="utf-8") as f:
        doc: object = yaml.safe_load(f)
    validate(doc)
    # The schema's root is an object, so a valid document is a mapping.
    return cast("dict[str, Any]", doc)
