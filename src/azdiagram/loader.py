"""Load YAML and validate it against the JSON Schema."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import jsonschema
import yaml

SCHEMA_NAME = "azure-diagram.schema.json"


class ValidationFailed(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def load_schema() -> dict:
    packaged = resources.files("azdiagram").joinpath(SCHEMA_NAME)
    if packaged.is_file():
        return json.loads(packaged.read_text(encoding="utf-8"))
    # Running from a source checkout.
    repo_copy = Path(__file__).resolve().parents[2] / "schema" / SCHEMA_NAME
    return json.loads(repo_copy.read_text(encoding="utf-8"))


def _path(error: jsonschema.ValidationError) -> str:
    out = ""
    for part in error.absolute_path:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out or "(root)"


def validate(doc) -> None:
    validator = jsonschema.Draft202012Validator(load_schema())
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))
    if errors:
        raise ValidationFailed([f"{_path(e)}: {e.message}" for e in errors])


def load(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    validate(doc)
    return doc
