# 0011. Lint Markdown with markdownlint on GitHub Actions

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The plan, README and ADRs are a large part of this repository and are read as
much as the code. Inconsistent Markdown renders badly and makes diffs noisy.
The `tax-data-collection` repository already has a Markdown lint pipeline.

## Decision

Copy that pipeline:

- [`.github/workflows/markdown-lint.yml`](../../.github/workflows/markdown-lint.yml)
  installs `markdownlint-cli` on Node 24 and runs `markdownlint '**/*.md'`.
- It runs on pushes and pull requests to `main` that change a `.md` file, the
  config, or the workflow itself.
- [`.markdownlint.json`](../../.markdownlint.json) uses the default rules with
  MD013 (line length) disabled.

## Alternatives considered

- **No linting.** Style drifts, especially with several authors and AI agents.
- **Prettier for Markdown.** Rewrites files rather than reporting problems, and
  differs from the sibling repository.

## Consequences

- Markdown is consistent across both repositories.
- Contributors can run `npx markdownlint-cli '**/*.md'` (or `--fix`) locally.
