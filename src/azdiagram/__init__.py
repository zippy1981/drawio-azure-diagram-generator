"""Render a YAML description of Azure infrastructure as a draw.io diagram."""

from __future__ import annotations

from typing import Any

from .build import DiagramError, build
from .drawio import to_drawio
from .layout import layout
from .loader import SchemaValidationError, load, validate
from .model import Diagram, Direction, Edge, Node

__all__ = [
    "Diagram",
    "DiagramError",
    "Direction",
    "Edge",
    "Node",
    "SchemaValidationError",
    "build",
    "layout",
    "load",
    "render",
    "to_drawio",
    "validate",
]


def render(
    doc: dict[str, Any],
    *,
    show_descriptions: bool | None = None,
    direction: Direction | None = None,
    max_row_width: int | None = None,
) -> str:
    """Build, lay out and serialize a document (no schema validation) to draw.io XML."""
    diagram = build(doc, show_descriptions=show_descriptions, direction=direction, max_row_width=max_row_width)
    layout(diagram)
    return to_drawio(diagram)
