---
name: schema-and-links-governance
description: Govern schema evolution and inferential link integrity for the Mathematical Statement Node model. Use when modifying schema/equation-node.schema.json, scripts/validate_nodes.py, or inferential link semantics.
---

# Schema and Links Governance

Protect ontology consistency during schema and validator changes.

## Required Workflow

1. If changing schema fields, update all dependent files:
   - `schema/equation-node.schema.json`
   - `data/statistics/nodes.json`
   - `scripts/validate_nodes.py`
2. Keep `inferential_links` contract intact:
   - `entailed_by`
   - `entails`
   - `equivalent_to`
   - `special_case_of`
   - `generalizes`
   - `composed_with`
3. Enforce reciprocity:
   - `entails` <-> `entailed_by`
   - `generalizes` <-> `special_case_of`
   - `equivalent_to` symmetric
4. Run `python scripts/validate_nodes.py`.

## Change Discipline

- Prefer additive schema evolution where possible.
- Avoid implicit renames.
- Keep field names academically precise.
