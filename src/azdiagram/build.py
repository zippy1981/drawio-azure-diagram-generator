"""Turn the validated YAML dict into a tree of Nodes plus Edges, resolving every reference."""

from __future__ import annotations

import re
import uuid
from functools import partial
from typing import TYPE_CHECKING, Any, NamedTuple

from .icons import icon_for, normalize_icon
from .model import Diagram, Direction, Edge, Node, YamlObject

if TYPE_CHECKING:
    from collections.abc import Callable

NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/zippy1981/drawio-azure-diagram-generator")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

COMMON_FIELDS = frozenset({"id", "name", "description", "icon", "style", "tags"})


class ChildSpec(NamedTuple):
    """A YAML list of child objects, optionally wrapped in a synthetic grouping box."""

    key: str
    child_kind: str
    group_kind: str | None = None
    group_label: str = ""


class ReferenceSpec(NamedTuple):
    """A field holding a reference that is drawn as an edge."""

    field: str
    target_kinds: frozenset[str] | None  # None: any endpoint, including external system names
    label: str


CHILDREN: dict[str, list[ChildSpec]] = {
    "entra_tenant": [
        ChildSpec("servicePrincipals", "service_principal"),
        ChildSpec("users", "user"),
        ChildSpec("groups", "group"),
    ],
    "group": [
        ChildSpec("owners", "principal", "owners", "Owners"),
        ChildSpec("members", "principal", "members", "Members"),
    ],
    "management_group": [
        ChildSpec("managementGroups", "management_group"),
        ChildSpec("subscriptions", "subscription"),
    ],
    "subscription": [ChildSpec("resourceGroups", "resource_group")],
    "resource_group": [
        ChildSpec("keyVaults", "key_vault"),
        ChildSpec("containerRegistries", "container_registry"),
        ChildSpec("containerApps", "container_app"),
        ChildSpec("storageAccounts", "storage_account"),
        ChildSpec("foundries", "foundry"),
    ],
    "container_app": [ChildSpec("containers", "container")],
    "container_registry": [ChildSpec("repositories", "repository")],
    "storage_account": [ChildSpec("blobContainers", "blob_container", "blob_containers", "Blob containers")],
    "foundry": [
        ChildSpec("models", "model_deployment", "models", "Models"),
        ChildSpec("agents", "agent", "agents", "Agents"),
    ],
    "agent": [ChildSpec("connectors", "connector", "connectors", "Connectors")],
}

REFERENCES: dict[str, list[ReferenceSpec]] = {
    "container_app": [ReferenceSpec("identity", frozenset({"service_principal"}), "runs as")],
    "container": [ReferenceSpec("imageRef", frozenset({"repository"}), "pulls")],
    "agent": [ReferenceSpec("model", frozenset({"model_deployment"}), "uses")],
    "connector": [ReferenceSpec("target", None, "connects to")],
}

# kinds whose `kind` field picks an icon variant, with its default
VARIANT_DEFAULTS: dict[str, str] = {"external": "system", "service_principal": "application"}

PRINCIPAL_KINDS: dict[str, str] = {"user": "user", "group": "group", "servicePrincipal": "service_principal"}
PRINCIPAL_NODE_KINDS = frozenset(PRINCIPAL_KINDS.values())


class DiagramError(Exception):
    """The document is schema-valid but inconsistent: duplicate ids, unresolved or mistyped references."""


def derive_id(*parts: str) -> str:
    """Return a deterministic UUIDv5 for a path of names."""
    return str(uuid.uuid5(NAMESPACE, "/".join(parts)))


def _scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(_scalar(v) for v in value)
    return str(value)


class _Builder:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}  # referenceable objects by id
        self.where: dict[str, str] = {}  # every cell id -> YAML location, for duplicate detection
        self.externals: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self.deferred: list[Callable[[], None]] = []  # reference resolution, run once every node exists

    def _claim(self, node_id: str, loc: str) -> None:
        if node_id in self.where:
            raise DiagramError(
                f"{loc}: duplicate id {node_id} (also used at {self.where[node_id]}); give one of them an explicit id"
            )
        self.where[node_id] = loc

    def synthetic(self, kind: str, name: str, node_id: str, loc: str) -> Node:
        self._claim(node_id, loc)
        return Node(kind=kind, id=node_id, name=name, icon=icon_for(kind))

    def obj(self, kind: str, obj: YamlObject, loc: str, path: list[str]) -> Node:
        spec = CHILDREN.get(kind, [])
        child_keys = {s.key for s in spec}
        path = [*path, obj["name"]]
        node_id = str(obj.get("id") or derive_id(*path)).lower()
        self._claim(node_id, loc)

        variant = obj.get("kind", VARIANT_DEFAULTS[kind]) if kind in VARIANT_DEFAULTS else None
        props = {k: _scalar(v) for k, v in obj.items() if k not in COMMON_FIELDS and k not in child_keys}
        for k, v in (obj.get("tags") or {}).items():
            props.setdefault(k, _scalar(v))

        node = Node(
            kind=kind,
            id=node_id,
            name=obj["name"],
            description=obj.get("description", ""),
            icon=normalize_icon(obj.get("icon") or icon_for(kind, variant)),
            style=obj.get("style", ""),
            props=props,
        )
        self.nodes[node_id] = node

        for child in spec:
            items: list[YamlObject] = obj.get(child.key) or []
            if not items:
                continue
            parent = node
            if child.group_kind:
                parent = self.synthetic(
                    child.group_kind, child.group_label, derive_id(node_id, child.key), f"{loc}.{child.key}"
                )
                node.children.append(parent)
            for i, item in enumerate(items):
                item_loc = f"{loc}.{child.key}[{i}]"
                if child.child_kind == "principal":
                    parent.children.append(self.principal(item, item_loc, [*path, child.key], parent, i))
                else:
                    parent.children.append(self.obj(child.child_kind, item, item_loc, path))

        for ref in REFERENCES.get(kind, []):
            if ref.field in obj:
                ref_loc = f"{loc}.{ref.field}"
                self.deferred.append(
                    partial(self.reference_edge, node, obj[ref.field], ref.target_kinds, ref.label, ref_loc)
                )
        return node

    def principal(self, item: YamlObject, loc: str, path: list[str], box: Node, index: int) -> Node:
        if "ref" not in item:
            return self.obj(PRINCIPAL_KINDS[item["type"]], item, loc, path)
        # A copy of a principal defined elsewhere; filled in once everything is built.
        ref = str(item["ref"]).lower()
        copy = Node(kind="", id=derive_id(box.id, "ref", ref, str(index)), name="")
        self._claim(copy.id, loc)
        self.deferred.append(partial(self.fill_ref, copy, item, loc))
        return copy

    def fill_ref(self, copy: Node, item: YamlObject, loc: str) -> None:
        target = self.lookup(item["ref"], PRINCIPAL_NODE_KINDS, f"{loc}.ref")
        copy.kind = target.kind
        copy.name = target.name
        copy.description = item.get("description", target.description)
        copy.icon = target.icon
        copy.props = {"ref": target.id}

    def lookup(self, ref: str, kinds: frozenset[str] | None, loc: str) -> Node:
        node = self.nodes.get(ref.lower())
        if node is None:
            raise DiagramError(f"{loc}: unknown id {ref}")
        if kinds and node.kind not in kinds:
            raise DiagramError(f"{loc}: {ref} is a {node.kind}, expected {' or '.join(sorted(kinds))}")
        return node

    def endpoint(self, value: str, loc: str) -> str:
        if UUID_RE.match(value):
            return self.lookup(value, None, loc).id
        if value in self.externals:
            return self.externals[value].id
        raise DiagramError(f"{loc}: {value!r} is neither a UUID nor the name of an external system")

    def reference_edge(self, node: Node, ref: str, kinds: frozenset[str] | None, label: str, loc: str) -> None:
        target = self.endpoint(ref, loc) if kinds is None else self.lookup(ref, kinds, loc).id
        self.edges.append(
            Edge(
                id=derive_id("edge", node.id, label, target),
                source=node.id,
                target=target,
                label=label,
                line="dashed",
                implicit=True,
            )
        )


def build(
    doc: dict[str, Any],
    *,
    show_descriptions: bool | None = None,
    direction: Direction | None = None,
    max_row_width: int | None = None,
) -> Diagram:
    """Build the Node tree. Keyword arguments override the document's `diagram` settings."""
    b = _Builder()
    sections: list[Node] = []

    externals: list[YamlObject] = doc.get("external") or []
    if externals:
        section = b.synthetic("external_section", "External", derive_id("section", "external"), "external")
        for i, ext in enumerate(externals):
            loc = f"external[{i}]"
            if ext["name"] in b.externals:
                raise DiagramError(f"{loc}: duplicate external system name {ext['name']!r}")
            node = b.obj("external", ext, loc, ["external"])
            b.externals[ext["name"]] = node
            section.children.append(node)
        sections.append(section)

    if doc.get("entra"):
        sections.append(b.obj("entra_tenant", doc["entra"], "entra", ["entra"]))
    for i, mg in enumerate(doc.get("managementGroups") or []):
        sections.append(b.obj("management_group", mg, f"managementGroups[{i}]", []))
    for i, sub in enumerate(doc.get("subscriptions") or []):
        sections.append(b.obj("subscription", sub, f"subscriptions[{i}]", []))

    for resolve in b.deferred:
        resolve()

    for i, conn in enumerate(doc.get("connections") or []):
        loc = f"connections[{i}]"
        b.edges.append(
            Edge(
                id=derive_id("connection", str(i)),
                source=b.endpoint(conn["from"], f"{loc}.from"),
                target=b.endpoint(conn["to"], f"{loc}.to"),
                label=conn.get("label", ""),
                description=conn.get("description", ""),
                line=conn.get("style", "solid"),
                bidirectional=conn.get("bidirectional", False),
            )
        )

    settings: YamlObject = doc.get("diagram") or {}
    return Diagram(
        id=derive_id("diagram"),
        title=settings.get("title", ""),
        page_name=settings.get("pageName", "Azure"),
        show_descriptions=settings.get("showDescriptions", True) if show_descriptions is None else show_descriptions,
        direction=direction or settings.get("direction", "horizontal"),
        max_row_width=max_row_width or settings.get("maxRowWidth", 1200),
        sections=sections,
        edges=b.edges,
    )
