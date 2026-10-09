# 0002. Describe the infrastructure in YAML validated by a JSON Schema

- **Status:** Accepted
- **Date:** 2026-10-08

## Context

Users describe Azure infrastructure, Entra ID objects and external systems by
hand, and want a diagram out of it. The input has to be easy to write and
review, and mistakes (a missing name, a typo in a key, a dangling reference)
should be caught with a clear message rather than producing a wrong diagram.

## Decision

The input is a YAML document whose structure mirrors the Azure hierarchy
(tenant → management group → subscription → resource group → resource).

- Its shape is defined by [`schema/azure-diagram.schema.json`](../../schema/azure-diagram.schema.json),
  written in JSON Schema 2020-12 and shipped inside the package.
- The loader reads it with `yaml.safe_load` and validates it with `jsonschema`,
  reporting **every** error with its YAML path
  (`entra.groups[0].members[2]: 'name' is a required property`), then exits 1.
- Rules the schema can't express (unique ids, references that resolve to the
  right kind of object) are checked while building the node tree, with equally
  specific messages.
- Example files start with a `yaml-language-server` schema comment so editors
  give autocomplete and inline validation.

## Alternatives considered

- **JSON input.** Easier to parse, but noisier to write by hand and has no comments.
- **A Python DSL or Bicep/Terraform as input.** More powerful, but ties the tool to
  a language or toolchain. Importing from those is left as later work.
- **Validation in code only.** Gives no editor support and is easy to let drift
  from the documented format.

## Consequences

- The schema is the single source of truth for the format; adding a resource type
  starts with a schema `$def`.
- Editors give authors immediate feedback.
- Runtime dependencies: `PyYAML` and `jsonschema`.
