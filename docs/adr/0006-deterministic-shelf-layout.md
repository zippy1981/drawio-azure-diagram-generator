# 0006. Lay out the diagram with a deterministic shelf packer, not an external layout engine

- **Status:** Accepted
- **Date:** 2026-10-08

## Context

Nodes need sizes and positions. Generic graph layout engines (Graphviz, ELK) are
good at edges but treat deep nesting awkwardly, add runtime dependencies, and
can produce different output for small input changes.

## Decision

`layout.py` is a pure, deterministic, bottom-up "shelf" packer:

1. **Measure (post-order).** Leaves have a fixed size (48×48 icon in a 120-wide
   slot plus label lines). A box lays its children out left to right, wrapping
   when a row would exceed `diagram.maxRowWidth`, and adds padding and a header.
   Leaves are placed before boxes in each row.
2. **Place (pre-order).** Child positions are relative to the parent, matching
   how draw.io stores geometry of child cells.
3. **Top level.** Sections go side by side (`direction: horizontal`) or stacked
   (`vertical`), aligned at the top.

## Alternatives considered

- **Graphviz / ELK (elkjs).** Better edge routing, but extra dependencies (ELK
  needs Node) and less predictable output. Kept as a possible later option.
- **Let draw.io lay it out.** draw.io has no headless layout we can call, and the
  user would have to arrange every diagram by hand.

## Consequences

- No layout dependency; the same input always gives the same geometry.
- Layout is easy to unit-test (children never overlap and stay inside their parent).
- Edge routing is left to draw.io and can be messy in busy diagrams (see ADR 0005).
