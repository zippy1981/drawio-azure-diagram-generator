# Architecture Decision Records

This directory records the significant decisions made for this project, using
the lightweight format described in [ADR 0001](0001-record-architecture-decisions.md).
ADRs 0002–0010 were inferred from [`PLAN.md`](../../PLAN.md) and the first implementation.

| ADR | Title | Status |
| --- | ----- | ------ |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-yaml-input-validated-by-json-schema.md) | Describe the infrastructure in YAML validated by a JSON Schema | Accepted |
| [0003](0003-uuid-ids-and-named-external-systems.md) | Use UUID ids, derived from the name path when omitted; reference external systems by name | Accepted (amended by 0013) |
| [0004](0004-box-vs-icon-and-synthetic-groupings.md) | Render nodes as boxes or icons by whether they have children, with synthetic grouping boxes | Accepted |
| [0005](0005-cross-references-as-edges.md) | Draw cross references as edges, but show group membership as copies | Accepted |
| [0006](0006-deterministic-shelf-layout.md) | Lay out the diagram with a deterministic shelf packer, not an external layout engine | Accepted |
| [0007](0007-uncompressed-drawio-xml-with-builtin-stencils.md) | Emit uncompressed draw.io XML that references draw.io's built-in Azure stencils | Accepted |
| [0008](0008-python-package-and-cli.md) | Ship a small Python package with an argparse CLI and minimal dependencies | Accepted |
| [0009](0009-testing-with-pytest-and-golden-file.md) | Test with pytest and use the sample diagram as a golden file | Accepted |
| [0010](0010-svg-preview-with-drawio-renderer.md) | Render SVG previews with draw.io's own renderer in headless Chromium | Accepted |
| [0011](0011-lint-markdown.md) | Lint Markdown with markdownlint on GitHub Actions | Accepted |
| [0012](0012-microsoft-365-icons-from-microsoft-cdn.md) | Use Microsoft's CDN-hosted product icons for Microsoft 365 | Proposed |
| [0013](0013-model-deployments-referenced-by-name.md) | Give model deployments no id and reference them by name | Proposed |

## Adding a new ADR

1. Copy [`template.md`](template.md) to `NNNN-short-title.md`, using the next free number.
2. Fill it in and set the status to **Proposed** in your pull request.
3. Change the status to **Accepted** when the PR merges, and add a row to the table above.
4. Never rewrite an accepted ADR's decision. To change course, write a new ADR and mark
   the old one **Superseded by NNNN**.
