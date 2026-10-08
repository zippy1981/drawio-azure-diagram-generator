# Plan: YAML → draw.io Azure diagram generator

A Python CLI that reads a YAML description of Azure infrastructure (plus Entra ID
and external systems) and writes a `.drawio` file that opens directly in
draw.io / diagrams.net / the VS Code draw.io extension.

```
azdiagram examples/sample.yaml -o sample.drawio
```

## 1. Input format

- Schema: [`schema/azure-diagram.schema.json`](schema/azure-diagram.schema.json)
  (JSON Schema 2020-12, so editors with `yaml-language-server` give
  autocomplete and validation from the comment on line 1 of the YAML).
- Example: [`examples/sample.yaml`](examples/sample.yaml).

### Hierarchy

```
(page)
├── External                       box   – external[]
│   └── external system            icon
├── Entra tenant                   box   – entra
│   ├── Service principal          icon  – entra.servicePrincipals[]
│   ├── User                       icon  – entra.users[]
│   └── Group                      box   – entra.groups[]
│       ├── Owners                 box   – owners[]  (ref or inline principal)
│       └── Members                box   – members[] (ref or inline principal)
└── Azure
    ├── Management group (opt.)    box   – managementGroups[] (nestable)
    └── Subscription               box   – subscriptions[] (top level or under an MG)
        └── Resource group         box   – resourceGroups[]
            ├── Key vault          icon  – keyVaults[]
            ├── Container app      box   – containerApps[]
            │   └── Container      icon  – containers[]
            ├── ACR                box   – containerRegistries[]
            │   └── Repository     icon  – repositories[]
            ├── Storage account    box   – storageAccounts[]
            │   └── Blob containers box  – (synthetic grouping)
            │       └── Container  icon  – blobContainers[]
            └── AI Foundry         box   – foundries[]
                ├── Models         box   – (synthetic grouping)
                │   └── Deployment icon  – models[]
                └── Agents         box   – (synthetic grouping)
                    └── Agent      box   – agents[]
                        └── Connectors box – (synthetic grouping)
                            └── Connector icon – connectors[]
```

"box"/"icon" above is the usual outcome; the real rule is dynamic (see 3.2).

### Common fields (every object)

| field         | required | purpose                                                    |
|---------------|----------|------------------------------------------------------------|
| `name`        | yes      | first line of the label                                    |
| `description` | no       | second line of the label + tooltip                         |
| `id`          | no       | target for `ref`, `connections`, `identity`, `target`, ... |
| `icon`        | no       | override the default icon                                  |
| `style`       | no       | raw draw.io style appended to the generated one            |
| `tags`        | no       | key/value metadata stored as custom cell properties        |

Ids that are omitted are derived from the name path
(`sub-prod/rg-chat-prod/kv-chat-prod` → slugified) so they're stable across runs.

### Cross references (drawn as arrows)

- `connections[]` – generic `from`/`to` by id, with `label`, `style`, `bidirectional`.
- `containerApp.identity` → service principal (dashed, "runs as").
- `container.imageRef` → repository (dashed, "pulls").
- `agent.model` → model deployment (dashed, "uses").
- `connector.target` → any object (dashed, "connects to").
- `group.owners/members[].ref` → render a copy of the referenced principal's icon
  inside the Owners/Members box (no arrow, to keep the Entra box readable).

## 2. Project layout

```
pyproject.toml                  # entry point: azdiagram = azdiagram.cli:main
schema/azure-diagram.schema.json
examples/sample.yaml
src/azdiagram/
    __init__.py
    cli.py          # argparse: input, -o/--output, --no-descriptions, --validate-only
    loader.py       # YAML load + JSON Schema validation + semantic checks
    model.py        # dataclasses: Node(kind, id, name, description, icon, children, props)
    build.py        # YAML dict -> Node tree (incl. synthetic grouping boxes)
    icons.py        # kind -> draw.io image path table
    layout.py       # sizes and positions (pure, no XML)
    drawio.py       # Node tree + edges -> mxGraphModel XML
tests/
    test_schema.py  test_build.py  test_layout.py  test_drawio.py
    golden/sample.drawio
```

Dependencies: `PyYAML`, `jsonschema`. XML via stdlib `xml.etree.ElementTree`.
No draw.io install needed at runtime.

## 3. Pipeline

### 3.1 Load and validate (`loader.py`)
1. `yaml.safe_load`.
2. Validate against the JSON Schema; print every error with its YAML path
   (`entra.groups[0].members[2]: 'name' is a required property`) and exit 1.
3. Semantic checks the schema can't express:
   - ids are unique across the whole document (explicit + derived);
   - every `ref`, `from`, `to`, `identity`, `imageRef`, `model`, `target`
     resolves; `identity` must point at a service principal, `imageRef` at a
     repository, `model` at a model deployment;
   - `ref` inside owners/members points at a user, group or service principal.

### 3.2 Build the node tree (`build.py`)
Turn the dict into a uniform `Node` tree. Root children are the three
sections: **External**, **Entra tenant**, **Azure** (Azure holds the
management groups and/or top-level subscriptions). Empty sections are dropped.

Synthetic grouping nodes are inserted where the hierarchy asks for them:
`Owners`, `Members`, `Blob containers`, `Models`, `Agents`, `Connectors`. They
are only created when their list is non-empty.

**Box vs icon rule:** a node with at least one child renders as a box with its
icon in the upper-left corner; a node with no children renders as just the
icon with its label underneath. So an empty resource group shows as a lone RG
icon, and a storage account without blob containers shows as a storage icon.

### 3.3 Icons (`icons.py`)
All are draw.io's built-in Azure stencils (`img/lib/azure2/...`), so the file
needs no embedded images. Every path below was checked to exist in the
`jgraph/drawio` repo.

| kind                     | icon path (under `img/lib/azure2/`)          |
|--------------------------|----------------------------------------------|
| External section / system| `general/Globe.svg`                          |
| external `kind: user`    | `identity/Users.svg`                         |
| Entra tenant             | `identity/Azure_Active_Directory.svg`        |
| Service principal (app)  | `identity/Enterprise_Applications.svg`       |
| Service principal (MI)   | `identity/Managed_Identities.svg`            |
| User                     | `identity/Users.svg`                         |
| Group / Owners / Members | `identity/Groups.svg`                        |
| Management group         | `general/Management_Groups.svg`              |
| Subscription             | `general/Subscriptions.svg`                  |
| Resource group           | `general/Resource_Groups.svg`                |
| Key vault                | `security/Key_Vaults.svg`                    |
| Container app            | `other/Worker_Container_App.svg`             |
| Container                | `containers/Container_Instances.svg`         |
| Container registry       | `containers/Container_Registries.svg`        |
| Repository               | `general/Image.svg`                          |
| Storage account          | `storage/Storage_Accounts.svg`               |
| Blob containers (group)  | `general/Blob_Block.svg`                     |
| Blob container           | `general/Storage_Container.svg`              |
| AI Foundry               | `ai_machine_learning/AI_Foundry.svg`         |
| Models (group)           | `general/Cubes.svg`                          |
| Model deployment         | `ai_machine_learning/Azure_OpenAI.svg`       |
| Agents (group) / Agent   | `ai_machine_learning/Bot_Services.svg`       |
| Connectors (group)       | `networking/Connections.svg`                 |
| Connector                | `integration/Logic_Apps_Custom_Connector.svg`|

A per-object `icon:` overrides the table.

### 3.4 Layout (`layout.py`)
Simple, deterministic, bottom-up "shelf" packing — no external layout engine.

Constants: icon 48×48; leaf cell width 120 (room for a wrapped label) and
height 48 + label height (≈ 16 px per line; 1 line for name, +1–2 for
description); box padding 16; box header 40 (24×24 icon at (8,8), title to
its right); gap 16 between siblings.

1. **Measure (post-order).** Leaf size is fixed as above. A box lays out its
   children left-to-right, wrapping to a new row when the row would exceed
   `diagram.maxRowWidth`; its size is the bounding box of the rows plus
   padding and header. Leaves are placed before boxes in each row so small
   icons don't get scattered between big boxes.
2. **Place (pre-order).** Child positions are relative to the parent box —
   draw.io stores child geometry relative to the parent cell, so no absolute
   math is needed.
3. **Top level.** The three sections go side by side (`direction: horizontal`)
   or stacked (`vertical`), aligned at the top.

### 3.5 draw.io output (`drawio.py`)
Uncompressed XML (diff-friendly, and draw.io reads it):

```xml
<mxfile host="azdiagram">
  <diagram id="..." name="Azure">
    <mxGraphModel grid="1" gridSize="10" page="1" ...>
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        ... cells ...
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Each node becomes an `<object>` (a.k.a. UserObject) so `description` and
`tags` show up in draw.io's *Edit Data* dialog, wrapping the `mxCell`:

- **Box node** – two cells:
  - container: `rounded=1;arcSize=4;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;align=left;verticalAlign=top;spacingLeft=40;spacingTop=6;fillColor=<per-kind>;strokeColor=<per-kind>;dashed=<0|1>;`
    label = `<b>name</b><br><i>description</i>`;
  - icon: child of the container at (8,8,24,24),
    `image;aspect=fixed;html=1;image=img/lib/azure2/...;movable=0;resizable=0;selectable=0;`
    so it moves with the box and can't be dragged out by accident.
- **Icon node** – one cell:
  `image;aspect=fixed;html=1;image=img/lib/azure2/...;verticalLabelPosition=bottom;verticalAlign=top;align=center;whiteSpace=wrap;`
  with geometry 48×48 centred in its 120-wide slot and the same HTML label.
- **Edges** – `edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;`
  (+ `dashed=1`, `dashPattern=1 3` for dotted, `startArrow=block` when
  bidirectional), `parent="1"` so they can cross box boundaries.

Box colours by tier so nesting is readable (light fills, darker stroke):
External grey, Entra purple, Management group/Subscription yellow (MG
dashed), Resource group blue, resources white, synthetic groupings dashed
with no fill.

All text is HTML-escaped; descriptions are omitted from labels with
`--no-descriptions` / `diagram.showDescriptions: false` but always kept as
the `tooltip` attribute. Cell ids are the node ids, so regenerating the
diagram produces a stable diff.

## 4. CLI

```
azdiagram INPUT.yaml [-o OUTPUT.drawio] [--no-descriptions]
                    [--direction horizontal|vertical] [--validate-only]
```
Default output is `INPUT.drawio` next to the input. Exit codes: 0 ok,
1 validation error, 2 usage error.

## 5. Testing

- `test_schema.py`: sample validates; table of invalid docs (missing name,
  unknown key, bad enum, bad id pattern) each fails.
- `test_build.py`: synthetic groupings appear only when non-empty; box/icon
  rule; derived ids are stable; unresolved/mistyped refs raise clear errors.
- `test_layout.py`: children never overlap and stay inside the parent;
  wrapping happens at `maxRowWidth`.
- `test_drawio.py`: output parses as XML; every `parent` exists; every edge's
  source/target exists; golden-file comparison against `tests/golden/sample.drawio`.
- Manual check: open the sample in diagrams.net (or export with the draw.io
  desktop CLI `drawio -x -f png`) and eyeball it.

## 6. Milestones

1. `pyproject.toml`, loader + schema validation + semantic checks, CLI `--validate-only`.
2. Node tree + icon table.
3. Layout + XML writer for boxes and icons (no edges) → first openable diagram.
4. Edges (connections and implicit references).
5. Styling polish, `--no-descriptions`, `direction`, golden tests, README.

## 7. Later / out of scope for v1

- More resource types (VNets/subnets, App Service, Cosmos DB, SQL) – each is a
  schema `$def`, a list on `resourceGroup`, and an icon row.
- Importing from Azure (`az graph query`) or Bicep/Terraform state to produce
  the YAML.
- Role assignments drawn as edges from principals to scopes.
- Smarter edge routing / an ELK-based layout option.
