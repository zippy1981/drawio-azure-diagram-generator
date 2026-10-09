# drawio-azure-diagram-generator

[![Lint Markdown](https://github.com/zippy1981/drawio-azure-diagram-generator/actions/workflows/markdown-lint.yml/badge.svg)](https://github.com/zippy1981/drawio-azure-diagram-generator/actions/workflows/markdown-lint.yml)

Turn a YAML description of Azure infrastructure (plus Entra ID and external
systems) into a [draw.io](https://www.drawio.com/) diagram.

![Sample diagram](examples/sample.svg)

## Usage

```sh
pip install -e .
azdiagram examples/sample.yaml                  # writes examples/sample.drawio
azdiagram infra.yaml -o infra.drawio --no-descriptions --direction vertical
azdiagram infra.yaml --validate-only
```

The YAML format is defined by [`schema/azure-diagram.schema.json`](schema/azure-diagram.schema.json);
see [`examples/sample.yaml`](examples/sample.yaml) and [PLAN.md](PLAN.md) for the details.
The reasoning behind the design is recorded in [`docs/adr/`](docs/adr/README.md).

## Rendering to SVG

`tools/render-svg.cjs` renders a `.drawio` file with draw.io's own renderer in
headless Chromium (needs Node and the `playwright` package). draw.io's viewer
script and the icons are fetched from the `jgraph/drawio` GitHub repo and cached
in `.cache/`, as are the Microsoft 365 icons from Microsoft's CDN; icons are
inlined so the SVG is self-contained.

```sh
node tools/render-svg.cjs examples/sample.drawio examples/sample.svg
```

## Tests

```sh
pip install -e '.[test]'
pytest
```
