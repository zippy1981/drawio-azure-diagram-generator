# 0008. Ship a small Python package with an argparse CLI and minimal dependencies

- **Status:** Accepted
- **Date:** 2026-10-08

## Context

The tool runs locally and in pipelines, should be quick to install, and has a
small command-line surface.

## Decision

- Python (3.10 and newer), packaged with `pyproject.toml` and Hatchling in a
  `src/azdiagram/` layout, split by pipeline stage: `loader`, `build`, `model`,
  `icons`, `layout`, `drawio`, `cli`.
- Runtime dependencies are only `PyYAML` and `jsonschema`; XML uses the standard library.
- The CLI is a single `azdiagram` command built on `argparse`:
  `azdiagram INPUT.yaml [-o OUTPUT.drawio] [--no-descriptions] [--direction horizontal|vertical] [--validate-only]`.
  Output defaults to `INPUT.drawio`. Exit codes: 0 ok, 1 validation error, 2 usage error.

## Alternatives considered

- **Click, Typer or Cyclopts.** Nicer for many subcommands, but one command with
  five options doesn't need another dependency.
- **A Node.js tool.** draw.io itself is JavaScript, but Python is a better fit for
  the YAML/JSON Schema tooling and for the intended users.

## Consequences

- Installs with a plain `pip install`.
- Each stage can be tested on its own.
- If the tool grows subcommands (e.g. importing from Azure), the CLI choice
  should be revisited in a new ADR.
