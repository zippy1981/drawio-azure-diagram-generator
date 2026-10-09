from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
import yaml

from azdiagram import DiagramError, SchemaValidationError, build, layout, render, validate
from azdiagram.cli import main

if TYPE_CHECKING:
    from azdiagram import Diagram, Node

Doc = dict[str, Any]
Mutation = Callable[[Doc], object]

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample.yaml"
UUID_A = "00000000-0000-0000-0000-00000000000a"


@pytest.fixture
def doc() -> Doc:
    loaded: Doc = yaml.safe_load(SAMPLE.read_text())
    return loaded


def _rg(d: Doc) -> Doc:
    rg: Doc = d["managementGroups"][0]["subscriptions"][0]["resourceGroups"][0]
    return rg


def test_sample_is_valid(doc: Doc) -> None:
    validate(doc)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["external"][0].pop("name"),
        lambda d: d["external"][0].__setitem__("id", UUID_A),
        lambda d: d["entra"]["users"][0].__setitem__("id", "alice"),
        lambda d: d["entra"]["users"][0].__setitem__("bogus", 1),
        lambda d: d["entra"]["servicePrincipals"][0].__setitem__("kind", "robot"),
        lambda d: d["entra"]["groups"][0]["owners"][0].__setitem__("ref", "alice"),
    ],
    ids=["missing-name", "external-id", "non-uuid-id", "unknown-key", "bad-enum", "non-uuid-ref"],
)
def test_schema_rejects(doc: Doc, mutate: Mutation) -> None:
    mutate(doc)
    with pytest.raises(SchemaValidationError):
        validate(doc)


def _nodes(diagram: Diagram) -> dict[str, Node]:
    return {n.id: n for s in diagram.sections for n in s.walk()}


def _by_name(diagram: Diagram) -> dict[str, Node]:
    return {n.name: n for n in _nodes(diagram).values()}


def test_box_or_icon_rule(doc: Doc) -> None:
    nodes = _by_name(build(doc))
    assert nodes["rg-chat-prod"].is_box
    assert nodes["kv-chat-prod"].is_box is False
    assert [c.name for c in nodes["stchatprod"].children] == ["Blob containers"]
    assert [c.name for c in nodes["aif-chat-prod"].children] == ["Models", "Agents"]


def test_synthetic_groupings_only_when_non_empty(doc: Doc) -> None:
    _rg(doc)["storageAccounts"][0].pop("blobContainers")
    nodes = _by_name(build(doc))
    assert not nodes["stchatprod"].is_box
    assert "Blob containers" not in nodes


def test_derived_ids_are_stable_uuids(doc: Doc) -> None:
    first = {name: n.id for name, n in _by_name(build(doc)).items()}
    second = {name: n.id for name, n in _by_name(build(copy.deepcopy(doc))).items()}
    assert first == second
    assert len(first["Carol (contractor)"]) == 36  # inline member, no id in the YAML


def test_group_ref_copies_principal(doc: Doc) -> None:
    owners = _by_name(build(doc))["Owners"]
    assert [(c.kind, c.name) for c in owners.children] == [("user", "Alice Smith")]


def test_externals_referenced_by_name(doc: Doc) -> None:
    diagram = build(doc)
    github = next(n for n in diagram.sections[0].children if n.name == "GitHub")
    assert any(e.target == github.id and e.label == "connects to" for e in diagram.edges)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d["connections"][0].__setitem__("from", "Nobody"), "neither a UUID nor"),
        (lambda d: d["connections"][0].__setitem__("from", UUID_A), "unknown id"),
        (
            lambda d: _rg(d)["containerApps"][0].__setitem__("identity", d["entra"]["users"][0]["id"]),
            "expected service_principal",
        ),
        (lambda d: d["entra"]["users"][1].__setitem__("id", d["entra"]["users"][0]["id"]), "duplicate id"),
    ],
    ids=["unknown-external", "unknown-uuid", "wrong-kind", "duplicate-id"],
)
def test_reference_errors(doc: Doc, mutate: Mutation, message: str) -> None:
    mutate(doc)
    with pytest.raises(DiagramError, match=message):
        build(doc)


def test_layout_children_inside_parent_without_overlap(doc: Doc) -> None:
    diagram = build(doc, max_row_width=500)
    layout(diagram)
    for node in _nodes(diagram).values():
        kids = node.children
        for c in kids:
            assert c.x >= 0
            assert c.y >= 0
            assert c.x + c.width <= node.width
            assert c.y + c.height <= node.height
        for i, a in enumerate(kids):
            for b in kids[i + 1 :]:
                apart = a.x + a.width <= b.x or b.x + b.width <= a.x or a.y + a.height <= b.y or b.y + b.height <= a.y
                assert apart, (a.name, b.name)


def test_drawio_is_consistent(doc: Doc) -> None:
    root = ET.fromstring(render(doc)).find("./diagram/mxGraphModel/root")
    assert root is not None
    ids = {el.get("id") for el in root if el.get("id")}
    for el in root:
        cell = el if el.tag == "mxCell" else el.find("mxCell")
        assert cell is not None
        for attr in ("parent", "source", "target"):
            if cell.get(attr):
                assert cell.get(attr) in ids


def test_sample_drawio_is_up_to_date(doc: Doc) -> None:
    assert render(doc) == (ROOT / "examples" / "sample.drawio").read_text()


def test_cli(tmp_path: Path) -> None:
    out = tmp_path / "out.drawio"
    assert main([str(SAMPLE), "-o", str(out)]) == 0
    assert out.read_text().startswith("<mxfile")
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 1\nexternal:\n  - description: no name\n")
    assert main([str(bad), "--validate-only"]) == 1
