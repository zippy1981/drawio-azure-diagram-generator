import copy
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

from azdiagram import DiagramError, build, layout, render
from azdiagram.cli import main
from azdiagram.loader import ValidationFailed, validate

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "examples" / "sample.yaml"
UUID_A = "00000000-0000-0000-0000-00000000000a"


@pytest.fixture
def doc():
    return yaml.safe_load(SAMPLE.read_text())


def test_sample_is_valid(doc):
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
def test_schema_rejects(doc, mutate):
    mutate(doc)
    with pytest.raises(ValidationFailed):
        validate(doc)


def _nodes(diagram):
    return {n.id: n for s in diagram.sections for n in s.walk()}


def test_box_or_icon_rule(doc):
    nodes = {n.name: n for n in _nodes(build(doc)).values()}
    assert nodes["rg-chat-prod"].is_box
    assert nodes["kv-chat-prod"].is_box is False
    assert [c.name for c in nodes["stchatprod"].children] == ["Blob containers"]
    assert [c.name for c in nodes["aif-chat-prod"].children] == ["Models", "Agents"]


def test_synthetic_groupings_only_when_non_empty(doc):
    doc["managementGroups"][0]["subscriptions"][0]["resourceGroups"][0]["storageAccounts"][0].pop("blobContainers")
    nodes = {n.name: n for n in _nodes(build(doc)).values()}
    assert not nodes["stchatprod"].is_box
    assert "Blob containers" not in nodes


def test_derived_ids_are_stable_uuids(doc):
    first = {n.name: n.id for n in _nodes(build(doc)).values()}
    second = {n.name: n.id for n in _nodes(build(copy.deepcopy(doc))).values()}
    assert first == second
    assert len(first["Carol (contractor)"]) == 36  # inline member, no id in the YAML


def test_group_ref_copies_principal(doc):
    nodes = {n.name: n for n in _nodes(build(doc)).values()}
    owners = nodes["Owners"]
    assert [(c.kind, c.name) for c in owners.children] == [("user", "Alice Smith")]


def test_externals_referenced_by_name(doc):
    diagram = build(doc)
    github = next(n for n in diagram.sections[0].children if n.name == "GitHub")
    assert any(e.target == github.id and e.label == "connects to" for e in diagram.edges)


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda d: d["connections"][0].__setitem__("from", "Nobody"), "neither a UUID nor"),
        (lambda d: d["connections"][0].__setitem__("from", UUID_A), "unknown id"),
        (
            lambda d: d["managementGroups"][0]["subscriptions"][0]["resourceGroups"][0]["containerApps"][0].__setitem__(
                "identity", d["entra"]["users"][0]["id"]
            ),
            "expected service_principal",
        ),
        (lambda d: d["entra"]["users"][1].__setitem__("id", d["entra"]["users"][0]["id"]), "duplicate id"),
    ],
    ids=["unknown-external", "unknown-uuid", "wrong-kind", "duplicate-id"],
)
def test_reference_errors(doc, mutate, message):
    mutate(doc)
    with pytest.raises(DiagramError, match=message):
        build(doc)


def test_layout_children_inside_parent_without_overlap(doc):
    diagram = build(doc, max_row_width=500)
    layout(diagram)
    for node in _nodes(diagram).values():
        kids = node.children
        for c in kids:
            assert c.x >= 0 and c.y >= 0
            assert c.x + c.width <= node.width and c.y + c.height <= node.height
        for i, a in enumerate(kids):
            for b in kids[i + 1 :]:
                apart = (
                    a.x + a.width <= b.x or b.x + b.width <= a.x or a.y + a.height <= b.y or b.y + b.height <= a.y
                )
                assert apart, (a.name, b.name)


def test_drawio_is_consistent(doc):
    root = ET.fromstring(render(doc)).find("./diagram/mxGraphModel/root")
    ids = {el.get("id") for el in root if el.get("id")}
    for el in root:
        cell = el if el.tag == "mxCell" else el.find("mxCell")
        if cell.get("parent"):
            assert cell.get("parent") in ids
        for end in ("source", "target"):
            if cell.get(end):
                assert cell.get(end) in ids


def test_sample_drawio_is_up_to_date(doc):
    assert render(doc) == (ROOT / "examples" / "sample.drawio").read_text()


def test_cli(tmp_path):
    out = tmp_path / "out.drawio"
    assert main([str(SAMPLE), "-o", str(out)]) == 0
    assert out.read_text().startswith("<mxfile")
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 1\nexternal:\n  - description: no name\n")
    assert main([str(bad), "--validate-only"]) == 1


def test_postgres_kinds_pick_icons(doc):
    nodes = {n.name: n for n in _nodes(build(doc)).values()}
    assert nodes["psql-chat-prod"].icon.endswith("azure2/databases/Azure_Database_PostgreSQL_Server.svg")
    assert nodes["cosmos-pg-analytics"].icon.endswith("Azure_Database_PostgreSQL_Server_Group.svg")
    assert nodes["hdb-vectors"].icon.endswith("azure2/databases/Azure_Database_PostgreSQL_Server.svg")
    assert nodes["psql-legacy-billing"].icon == "img/lib/mscae/Azure_Database_for_PostgreSQL_servers.svg"
    assert nodes["psql-legacy-billing"].props["kind"] == "singleServer"
    assert [c.name for c in nodes["psql-chat-prod"].children] == ["chat"]


def test_graph_is_a_top_level_section(doc):
    diagram = build(doc)
    assert [s.kind for s in diagram.sections] == [
        "external_section",
        "entra_tenant",
        "graph",
        "m365",
        "management_group",
    ]
    graph = diagram.sections[2]
    assert any(e.target == graph.id and e.label == "connects to" for e in diagram.edges)


def test_schema_rejects_unknown_postgres_kind(doc):
    rg = doc["managementGroups"][0]["subscriptions"][0]["resourceGroups"][1]
    rg["postgresServers"][0]["kind"] = "mysql"
    with pytest.raises(ValidationFailed):
        validate(doc)


def test_m365_apps_pick_icons(doc):
    nodes = {n.name: n for n in _nodes(build(doc)).values()}
    assert [c.name for c in nodes["Contoso Microsoft 365"].children] == ["Exchange Online", "SharePoint", "Teams", "Excel"]
    assert nodes["Teams"].icon.endswith("/teams_48x1.svg")
    assert nodes["Exchange Online"].icon.endswith("/outlook_48x1.svg")
    doc["m365"]["apps"][0]["kind"] = "other"
    nodes = {n.name: n for n in _nodes(build(doc)).values()}
    assert nodes["Exchange Online"].icon.endswith("/office_48x1.svg")
