# 0007. Emit uncompressed draw.io XML that references draw.io's built-in Azure stencils

- **Status:** Accepted
- **Date:** 2026-10-08

## Context

The output must open directly in draw.io, diagrams.net and the VS Code draw.io
extension, be reviewable in pull requests, and keep the extra information from
the YAML (descriptions, tags).

## Decision

- Write an `mxfile` with a single uncompressed `mxGraphModel`, built with the
  standard library's `xml.etree.ElementTree`. No draw.io install is needed.
- Icons reference draw.io's built-in Azure stencils (`img/lib/azure2/...`) by
  path; nothing is embedded. Every path in the icon table is checked to exist in
  the `jgraph/drawio` repository. A per-object `icon:` overrides the table.
- Each node is an `<object>` (UserObject) wrapping its `mxCell`, so `description`
  and `tags` appear in draw.io's *Edit Data* dialog. Descriptions are always kept
  as the tooltip, even when `--no-descriptions` hides them from labels.
- A box's icon is a locked child cell so it moves with the box.
- Cell ids are node ids (ADR 0003) and all text is HTML-escaped.

## Alternatives considered

- **Compressed (deflate + base64) diagrams.** draw.io's default, but opaque in diffs.
- **Embedding icon images as data URIs.** Self-contained, but bloats the file and
  duplicates what draw.io already ships.
- **Generating SVG or PNG directly.** Not editable afterwards, which defeats the
  point of targeting draw.io.

## Consequences

- Output is diff-friendly and editable, and small.
- Icons depend on draw.io keeping its stencil paths; the icon table is the one
  place to fix if they move.
