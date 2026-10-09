"""Deterministic bottom-up shelf layout. Positions are relative to the parent box, as draw.io stores them."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .model import Diagram, Node

ICON = 48  # leaf icon size
LEAF_W = 120  # leaf slot width; the label wraps to this
HEADER_ICON = 24  # icon in a box's upper-left corner
HEADER_ICON_INSET = 8
HEADER_TEXT_LEFT = HEADER_ICON_INSET + HEADER_ICON + 8  # spacingLeft of a box label
PAD = 16  # inside a box, around its children
GAP = 16  # between siblings
SECTION_GAP = 40  # between top-level sections
MIN_BOX_W = 160
MARGIN = 20  # page margin
TITLE_H = 40

NAME_FONT = 12
DESC_FONT = 10
NAME_LINE = 15
DESC_LINE = 13


def _lines(text: str, width: float, font_size: int) -> int:
    if not text:
        return 0
    chars = max(1, int(width / (font_size * 0.6)))
    return max(1, len(textwrap.wrap(text, chars)))


def label_height(node: Node, width: float, show_descriptions: bool) -> float:
    """Estimate the height of a node's label when wrapped to `width` pixels."""
    h: float = _lines(node.name, width, NAME_FONT) * NAME_LINE
    if show_descriptions:
        h += _lines(node.description, width, DESC_FONT) * DESC_LINE
    return h


def _pack(children: list[Node], max_width: float) -> list[list[Node]]:
    rows: list[list[Node]] = []
    row_w = 0.0
    for child in children:
        if rows and row_w + GAP + child.width <= max_width:
            rows[-1].append(child)
            row_w += GAP + child.width
        else:
            rows.append([child])
            row_w = child.width
    return rows


def _measure(node: Node, diagram: Diagram) -> None:
    show = diagram.show_descriptions
    if not node.is_box:
        node.width = LEAF_W
        node.height = ICON + 4 + label_height(node, LEAF_W, show)
        return

    for child in node.children:
        _measure(child, diagram)

    # Icons first, then boxes, each group starting on its own row.
    leaves = [c for c in node.children if not c.is_box]
    boxes = [c for c in node.children if c.is_box]
    rows = _pack(leaves, diagram.max_row_width) + _pack(boxes, diagram.max_row_width)

    content_w = max(sum(c.width for c in row) + GAP * (len(row) - 1) for row in rows)
    # Wide enough to fit the name on one line where possible.
    name_w = HEADER_TEXT_LEFT + len(node.name) * NAME_FONT * 0.6 + PAD
    node.width = max(content_w + 2 * PAD, MIN_BOX_W, name_w)

    header = max(HEADER_ICON + 2 * HEADER_ICON_INSET, 10 + label_height(node, node.width - HEADER_TEXT_LEFT - 8, show))
    y: float = header
    for row in rows:
        x: float = PAD
        for child in row:
            child.x, child.y = x, y
            x += child.width + GAP
        y += max(c.height for c in row) + GAP
    node.height = y - GAP + PAD


def layout(diagram: Diagram) -> None:
    """Size every node and position it relative to its parent; sections are placed on the page."""
    for section in diagram.sections:
        _measure(section, diagram)

    x: float = MARGIN
    y: float = MARGIN + (TITLE_H if diagram.title else 0)
    for section in diagram.sections:
        section.x, section.y = x, y
        if diagram.direction == "vertical":
            y += section.height + SECTION_GAP
        else:
            x += section.width + SECTION_GAP
