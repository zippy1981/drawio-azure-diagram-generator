# 0013. Give model deployments no id and reference them by name

- **Status:** Proposed
- **Date:** 2026-10-09

## Context

[ADR 0003](0003-uuid-ids-and-named-external-systems.md) gives every object except
external systems a UUID id, and agents pointed at their model deployment by that id.
A model deployment has no GUID of its own in Azure: it is identified by its name
within the Foundry resource, and that name is what an agent's definition uses.
Making authors invent or copy a UUID for it adds noise and hides which model an
agent uses.

## Decision

- Model deployments may not have an `id`, like external systems. Their cell id is
  still a UUIDv5 derived from the name path, so it stays stable.
- An agent's `model` is the **name** of a model deployment in the same foundry.
- Deployment names must be unique within a foundry; a duplicate, or a `model` that
  names no deployment in the agent's foundry, is an error.
- This amends ADR 0003 for model deployments only.

## Alternatives considered

- **Keep UUID references.** Consistent with the rest of the document, but the UUID
  doesn't correspond to anything real and makes agents harder to read.
- **Allow either a UUID or a name.** More flexible, but two ways to say the same
  thing, and the UUID form has no real use.
- **Names unique across the whole document.** Simpler lookup, but two foundries can
  legitimately have deployments with the same name (e.g. `gpt-4.1` in each).

## Consequences

- Agents read naturally (`model: gpt-chat`).
- `connections` can no longer point at a model deployment, since it has no id
  to refer to. Agents are the only thing that uses them today.
- Renaming a deployment means updating the agents that use it.
