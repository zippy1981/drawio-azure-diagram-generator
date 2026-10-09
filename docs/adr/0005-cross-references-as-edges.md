# 0005. Draw cross references as edges, but show group membership as copies

- **Status:** Accepted
- **Date:** 2026-10-08

## Context

Besides containment, the input expresses relationships: generic connections,
a container app's managed identity, a container's image, an agent's model, a
connector's target, and Entra group owners and members. Group membership is
typically dense, and arrows from many groups to many principals would make the
Entra section unreadable.

## Decision

- `connections[]` become solid edges with an optional label, style and
  `bidirectional` flag.
- Implicit references become dashed, labelled edges: `identity` ("runs as"),
  `imageRef` ("pulls"), `model` ("uses") and `connector.target` ("connects to").
- Edges use draw.io's orthogonal router and are parented to the root layer so
  they can cross box boundaries.
- A `ref` in a group's `owners`/`members` renders a **copy** of the referenced
  principal's icon inside the Owners/Members box, with no arrow.

## Alternatives considered

- **Arrows for group membership too.** Accurate, but the Entra box would turn into
  a web of crossing lines.
- **Leaving implicit references undrawn.** Hides the most useful information in an
  architecture diagram (who runs as what, what talks to what).

## Consequences

- Most relationships are visible at a glance.
- The same principal can appear more than once in the Entra section.
- In busy diagrams the orthogonal router crosses labels. Better routing (e.g. ELK)
  is future work; draw.io's Arrange → Layout helps in the meantime.
