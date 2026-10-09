"""Write the laid-out Node tree as uncompressed draw.io (mxGraphModel) XML."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET

from .build import derive_id
from .layout import HEADER_ICON, HEADER_ICON_INSET, HEADER_TEXT_LEFT, ICON, LEAF_W, MARGIN, TITLE_H
from .model import Diagram, Edge, Node

# kind -> (fillColor, strokeColor, dashed)
BOX_COLORS = {
    "external_section": ("#f5f5f5", "#666666", False),
    "entra_tenant": ("#e1d5e7", "#9673a6", False),
    "group": ("#ffffff", "#9673a6", False),
    "owners": ("none", "#9673a6", True),
    "members": ("none", "#9673a6", True),
    "management_group": ("#fff2cc", "#d6b656", True),
    "subscription": ("#fff2cc", "#d6b656", False),
    "resource_group": ("#dae8fc", "#6c8ebf", False),
    "blob_containers": ("none", "#999999", True),
    "models": ("none", "#999999", True),
    "agents": ("none", "#999999", True),
    "connectors": ("none", "#999999", True),
}
RESOURCE_BOX = ("#ffffff", "#6c8ebf", False)

RESERVED_ATTRS = {"id", "label", "tooltip", "placeholders", "link", "objectType", "description"}
XML_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")


def _label(name: str, description: str, show_descriptions: bool) -> str:
    out = f"<b>{html.escape(name)}</b>"
    if show_descriptions and description:
        out += f'<br><i style="font-size:10px;color:#555555;">{html.escape(description)}</i>'
    return out


def _user_object(root: ET.Element, cell_id: str, label: str, attrs: dict[str, str]) -> ET.Element:
    """An <object> wrapper so description/props show up in draw.io's Edit Data dialog."""
    obj = ET.SubElement(root, "object", {"id": cell_id, "label": label})
    for key, value in attrs.items():
        if value != "" and XML_NAME.match(key):
            obj.set(key, value)
    return obj


def _geometry(cell: ET.Element, x: float, y: float, w: float, h: float) -> None:
    ET.SubElement(
        cell, "mxGeometry", {"x": _num(x), "y": _num(y), "width": _num(w), "height": _num(h), "as": "geometry"}
    )


def _num(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else f"{v:.1f}"


def _emit_node(root: ET.Element, node: Node, parent: str, diagram: Diagram) -> None:
    attrs = {"tooltip": node.description, "objectType": node.kind, "description": node.description}
    attrs.update({k: v for k, v in node.props.items() if k not in RESERVED_ATTRS})
    obj = _user_object(root, node.id, _label(node.name, node.description, diagram.show_descriptions), attrs)

    if node.is_box:
        fill, stroke, dashed = BOX_COLORS.get(node.kind, RESOURCE_BOX)
        style = (
            "rounded=1;arcSize=4;absoluteArcSize=1;whiteSpace=wrap;html=1;container=1;collapsible=0;"
            "recursiveResize=0;align=left;verticalAlign=top;"
            f"spacingLeft={HEADER_TEXT_LEFT - 2};spacingTop=4;spacingRight=8;fontSize=12;"
            f"fillColor={fill};strokeColor={stroke};" + ("dashed=1;" if dashed else "") + node.style
        )
        cell = ET.SubElement(obj, "mxCell", {"style": style, "vertex": "1", "parent": parent})
        _geometry(cell, node.x, node.y, node.width, node.height)

        icon = ET.SubElement(
            root,
            "mxCell",
            {
                "id": f"{node.id}-icon",
                "value": "",
                "style": f"image;aspect=fixed;html=1;image={node.icon};movable=0;resizable=0;"
                "rotatable=0;deletable=0;editable=0;connectable=0;",
                "vertex": "1",
                "parent": node.id,
            },
        )
        _geometry(icon, HEADER_ICON_INSET, HEADER_ICON_INSET, HEADER_ICON, HEADER_ICON)

        for child in node.children:
            _emit_node(root, child, node.id, diagram)
    else:
        style = (
            f"image;aspect=fixed;html=1;image={node.icon};verticalLabelPosition=bottom;verticalAlign=top;"
            f"align=center;whiteSpace=wrap;labelWidth={LEAF_W};labelBackgroundColor=none;fontSize=12;" + node.style
        )
        cell = ET.SubElement(obj, "mxCell", {"style": style, "vertex": "1", "parent": parent})
        _geometry(cell, node.x + (node.width - ICON) / 2, node.y, ICON, ICON)


def _emit_edge(root: ET.Element, edge: Edge) -> None:
    style = (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        "endArrow=block;endFill=1;fontSize=10;labelBackgroundColor=#ffffff;"
    )
    if edge.line == "dashed":
        style += "dashed=1;"
    elif edge.line == "dotted":
        style += "dashed=1;dashPattern=1 3;"
    if edge.bidirectional:
        style += "startArrow=block;startFill=1;"
    if edge.implicit:
        style += "strokeColor=#808080;fontColor=#666666;"
    attrs = {"tooltip": edge.description, "description": edge.description}
    obj = _user_object(root, edge.id, html.escape(edge.label), attrs)
    cell = ET.SubElement(
        obj, "mxCell", {"style": style, "edge": "1", "parent": "1", "source": edge.source, "target": edge.target}
    )
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})


def to_drawio(diagram: Diagram) -> str:
    mxfile = ET.Element("mxfile", {"host": "azdiagram"})
    page = ET.SubElement(mxfile, "diagram", {"id": diagram.id, "name": diagram.page_name})
    model = ET.SubElement(
        page,
        "mxGraphModel",
        {
            "grid": "1",
            "gridSize": "10",
            "guides": "1",
            "tooltips": "1",
            "connect": "1",
            "arrows": "1",
            "fold": "1",
            "page": "0",
            "pageScale": "1",
            "math": "0",
            "shadow": "0",
        },
    )
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    if diagram.title:
        title = ET.SubElement(
            root,
            "mxCell",
            {
                "id": derive_id("title"),
                "value": html.escape(diagram.title),
                "style": "text;html=1;fontSize=20;fontStyle=1;align=left;verticalAlign=middle;",
                "vertex": "1",
                "parent": "1",
            },
        )
        _geometry(title, MARGIN, MARGIN, 600, TITLE_H - 10)

    for section in diagram.sections:
        _emit_node(root, section, "1", diagram)
    for edge in diagram.edges:
        _emit_edge(root, edge)

    ET.indent(mxfile)
    return ET.tostring(mxfile, encoding="unicode") + "\n"
