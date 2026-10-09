"""Render a YAML description of Azure infrastructure as a draw.io diagram."""

from .build import DiagramError, build
from .drawio import to_drawio
from .layout import layout
from .loader import load

__all__ = ["DiagramError", "build", "layout", "load", "render", "to_drawio"]


def render(doc: dict, **overrides) -> str:
    """Validate-free pipeline: YAML dict -> draw.io XML string."""
    diagram = build(doc, **overrides)
    layout(diagram)
    return to_drawio(diagram)
