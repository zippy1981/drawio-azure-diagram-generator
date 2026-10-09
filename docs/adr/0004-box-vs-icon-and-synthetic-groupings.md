# 0004. Render nodes as boxes or icons by whether they have children, with synthetic grouping boxes

- **Status:** Accepted
- **Date:** 2026-10-08

## Context

The diagram nests deeply (subscription → resource group → AI Foundry → agent →
connector). Fixed "this kind is always a box" rules waste space on empty
containers and lose information when a resource has children. Some children
(blob containers, model deployments, agents, connectors, group owners and
members) are clearer when gathered under a labelled heading.

## Decision

- Input is turned into a uniform `Node` tree before layout.
- **Box vs icon:** a node with at least one child renders as a box with its icon
  in the upper-left corner; a node with no children renders as just its icon with
  the label underneath.
- **Synthetic groupings** (`Owners`, `Members`, `Blob containers`, `Models`,
  `Agents`, `Connectors`) are inserted as dashed boxes with no fill, and only when
  their list is non-empty.
- Top-level sections are, in order: **External**, the **Entra tenant**, each
  top-level management group, then each top-level subscription. Empty sections
  are dropped.
- Boxes are coloured by tier (External grey, Entra purple, management
  group/subscription yellow, resource group blue, resources white) so nesting is
  readable.

## Alternatives considered

- **Fixed box/icon per kind.** Simpler, but an empty resource group would be a big
  empty box and a storage account with containers would have nowhere to put them.
- **No synthetic groupings.** Children of different kinds would be mixed together
  inside a parent, which is hard to scan.

## Consequences

- Diagrams stay compact and the same kind can look different depending on content.
- Tests must cover both forms and the "only when non-empty" rule.
