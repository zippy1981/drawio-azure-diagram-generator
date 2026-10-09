# 0003. Use UUID ids, derived from the name path when omitted; reference external systems by name

- **Status:** Accepted
- **Date:** 2026-10-09

## Context

Objects refer to each other (connections, managed identities, image pulls,
model deployments, connector targets, group members), so they need ids. Azure
and Entra objects already have GUIDs, but writing one for every object in a
hand-written file is tedious. The same ids become draw.io cell ids, so they must
be stable for regenerated diagrams to diff cleanly. External systems have no
natural GUID at all.

## Decision

- Every `id` is a UUID, typically the Entra object id or Azure resource GUID.
- When `id` is omitted, it is derived as a UUIDv5 of the object's name path
  (`Contoso Prod/rg-chat-prod/kv-chat-prod`), so it is stable across runs.
- Ids must be unique across the whole document, explicit and derived alike.
- External systems may not have an `id`. They are referenced by `name` wherever
  an endpoint is expected (`connections[].from/to`, `connector.target`), so their
  names must be unique. Internally they get a UUIDv5 of `external/<name>`.
- References are typed: `identity` must point at a service principal, `imageRef`
  at a repository, `model` at a model deployment, and group `ref`s at a user,
  group or service principal.

## Alternatives considered

- **Free-form string ids.** Friendlier to type, but invites collisions and doesn't
  line up with the real Azure/Entra identifiers.
- **Random UUIDs for omitted ids.** Every regeneration would rewrite every cell id
  and make diffs useless.
- **Requiring UUIDs on external systems.** They have no real identity to use, and
  their names are already unique and readable.

## Consequences

- Diagrams regenerate with stable cell ids and minimal diffs.
- Renaming an object without an explicit id changes its derived id and the ids of
  everything beneath it.
- Typed references catch wiring mistakes before anything is drawn.
