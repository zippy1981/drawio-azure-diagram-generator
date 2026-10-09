# 0010. Render SVG previews with draw.io's own renderer in headless Chromium

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The README needs a picture of the sample diagram, and changes to styling or
layout need a visual check. Only draw.io's renderer shows exactly what users
will see; a home-grown renderer would drift from it.

## Decision

[`tools/render-svg.cjs`](../../tools/render-svg.cjs) loads draw.io's
`viewer-static.min.js` in headless Chromium via Playwright and exports the
diagram as SVG.

- The viewer script and the referenced icons are fetched from the `jgraph/drawio`
  repository at a pinned tag (overridable with `DRAWIO_TAG`) and cached in `.cache/`.
- Icons are inlined as data URIs so the SVG is self-contained.
- [`examples/sample.svg`](../../examples/sample.svg) is committed and shown in the README.

## Alternatives considered

- **draw.io desktop CLI export.** Needs the Electron app and a display, which is
  heavy for CI and dev containers.
- **Writing our own SVG renderer.** Would not match draw.io.

## Consequences

- The preview matches what draw.io shows.
- This is a development tool only: it needs Node, the `playwright` package and
  network access on first run. The Python package does not depend on it.
