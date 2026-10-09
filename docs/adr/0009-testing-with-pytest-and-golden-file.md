# 0009. Test with pytest and use the sample diagram as a golden file

- **Status:** Accepted
- **Date:** 2026-10-08

## Context

Most bugs in a generator like this show up as subtly wrong output: a missing
cell, a dangling edge, overlapping boxes, or an unintended change to every
diagram.

## Decision

Tests use pytest in `tests/test_azdiagram.py` and cover each stage:

- **Schema:** the sample validates; each class of invalid document fails.
- **Build:** synthetic groupings, the box/icon rule, stable derived ids, group
  ref copies, external references and clear errors for bad references.
- **Layout:** children never overlap and stay inside their parent.
- **draw.io:** every `parent`, `source` and `target` exists, and
  [`examples/sample.drawio`](../../examples/sample.drawio) is exactly what
  [`examples/sample.yaml`](../../examples/sample.yaml) renders to.

The golden file is regenerated deliberately whenever output changes, so the
diff shows the change in review.

## Alternatives considered

- **Structural assertions only.** Miss unintended changes to styling and geometry.
- **Comparing rendered images.** Slow and brittle; used only as a manual check
  (ADR 0010).

## Consequences

- Any change to output fails the golden test until `sample.drawio` is regenerated
  and committed alongside the change.
