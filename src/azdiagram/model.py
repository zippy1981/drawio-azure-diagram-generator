from __future__ import annotations

from dataclasses import dataclass, field


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
        return bool(self.children)

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass
class Edge:
    id: str
    source: str
    target: str
    label: str = ""
    description: str = ""
    line: str = "solid"  # solid | dashed | dotted
    bidirectional: bool = False
    implicit: bool = False  # derived from identity/imageRef/model/target rather than `connections`


@dataclass
class Diagram:
    id: str
    title: str
    page_name: str
    show_descriptions: bool
    direction: str
    max_row_width: int
    sections: list[Node]
    edges: list[Edge]
