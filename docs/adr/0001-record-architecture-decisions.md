# 0001. Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

The generator was designed up front in [`PLAN.md`](../../PLAN.md). That plan mixes
the decisions with the details of how to carry them out, and it will keep changing
as the code does. Future contributors, human or AI, need to know *why* things are
the way they are before changing them.

## Decision

We will record every architecturally significant decision as an Architecture
Decision Record (ADR), following Michael Nygard's format
([original post](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)),
with an added "Alternatives considered" section.

- ADRs live in `docs/adr/` as Markdown, numbered sequentially (`NNNN-title.md`).
- [`template.md`](template.md) is the starting point, and [`README.md`](README.md) is the index.
- Accepted ADRs are immutable. A change of direction is a new ADR that supersedes the old one.
- A pull request that makes a significant decision includes its ADR.
- ADRs 0002–0010 were written after the fact from `PLAN.md` and the first
  implementation.

## Alternatives considered

- **Keep everything in `PLAN.md`.** The plan describes *what* to build; the reasons
  and the options that were turned down get lost when it's edited.
- **Commit messages only.** The reasoning gets scattered and is hard to find.

## Consequences

- Decisions are reviewable in pull requests, versioned with the code, and searchable.
- There is a small overhead to writing an ADR for each significant change.
