# 0012. Use Microsoft's CDN-hosted product icons for Microsoft 365

- **Status:** Proposed
- **Date:** 2026-10-09

## Context

Diagrams can now include a Microsoft 365 tenant and its apps (Exchange Online,
SharePoint, Teams, Word, Excel and so on). [ADR 0007](0007-uncompressed-drawio-xml-with-builtin-stencils.md)
says icons are draw.io's built-in stencils, but draw.io has no current Microsoft 365
icons: its Office stencils are monochrome, date from around 2014, and have nothing
for Teams, OneDrive, Word, Excel, PowerPoint, Loop or Copilot.

## Decision

For Microsoft 365 only, icons reference Microsoft's Fluent product icons by URL on
Microsoft's CDN, at a pinned build:
`https://res.cdn.office.net/files/fabric-cdn-prod_20241209.001/assets/brand-icons/product/svg/<app>_48x1.svg`.

- The base URL lives in one constant in `icons.py`; every app `kind` maps to a file.
- Exchange Online uses the Outlook icon, and `kind: other` uses the Office icon,
  because the CDN has no Exchange (or Planner) icon. `icon:` still overrides.
- `tools/render-svg.cjs` fetches these URLs, caches them in `.cache/remote/`, and
  inlines them like the draw.io icons, so the SVG preview stays self-contained.
- Everything else keeps using draw.io's built-in icons (ADR 0007 is otherwise unchanged).

## Alternatives considered

- **draw.io's built-in Office stencils.** Work offline, but look dated, need a
  different cell style (`shape=mxgraph.office...`), and leave most apps sharing
  generic icons.
- **Committing Microsoft's SVGs and embedding them as data URIs.** Self-contained,
  but bloats every diagram and puts Microsoft brand assets in this repository.

## Consequences

- Microsoft 365 apps get current, recognisable icons with no files added to the repo.
- A `.drawio` file shows those icons only when the viewer can reach
  `res.cdn.office.net`; offline, the cells show as broken images (labels still show).
- If Microsoft removes the pinned build, the base URL needs updating in one place.
- Rendering the SVG preview needs network access to that host on first run.
