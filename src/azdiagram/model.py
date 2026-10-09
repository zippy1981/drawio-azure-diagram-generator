"""Data model shared by the build, layout and draw.io stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Iterator

YamlObject: TypeAlias = dict[str, Any]
"""One mapping from the parsed YAML document (already validated against the schema)."""

LineStyle: TypeAlias = Literal["solid", "dashed", "dotted"]
Direction: TypeAlias = Literal["horizontal", "vertical"]


@dataclass
class Node:
    """One object in the diagram. A node with children renders as a box, otherwise as an icon."""

    kind: str
    id: str
    name: str
    description: str = ""
    icon: str = ""
    style: str = ""
    props: dict[str, str] = field(default_factory=dict)
    children: list[Node] = field(default_factory=list)

    # Filled in by layout(); x/y are relative to the parent box (or the page for sections).
    x: float = 0
    y: float = 0
    width: float = 0
    height: float = 0

    @property
    def is_box(self) -> bool:
        """Whether the node renders as a box (it has children) rather than a bare icon."""
        return bool(self.children)

    def walk(self) -> Iterator[Node]:
        """Yield this node and all of its descendants, depth first."""
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass
class Edge:
    """An arrow between two nodes, referenced by their cell ids."""

    id: str
    source: str
    target: str
    label: str = ""
    description: str = ""
    line: LineStyle = "solid"
    bidirectional: bool = False
    implicit: bool = False  # derived from identity/imageRef/model/target rather than `connections`


@dataclass
class Diagram:
    """Everything needed to lay out and write one draw.io page."""

    id: str
    title: str
    page_name: str
    show_descriptions: bool
    direction: Direction
    max_row_width: int
    sections: list[Node]
    edges: list[Edge]
