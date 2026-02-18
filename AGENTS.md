# AGENTS.md

Project-level agent instructions and skill index for `corollary-abstractions`.

## Objective

Model mathematical statements as reusable, cross-disciplinary structures with explicit inferential lineage, starting with statistics.

## Available Skills

### Skill: `statistics-ontology-authoring`
- Purpose: Author and refine statement nodes in `data/statistics/nodes.json`.
- Skill file: `.github/skills/statistics-ontology-authoring/SKILL.md`
- Use when:
  - Adding theorem/corollary/definition/model nodes.
  - Revising symbolic forms, assumptions, or provenance.

### Skill: `schema-and-links-governance`
- Purpose: Maintain schema coherence and inferential link integrity.
- Skill file: `.github/skills/schema-and-links-governance/SKILL.md`
- Use when:
  - Changing ontology fields in `schema/equation-node.schema.json`.
  - Modifying `inferential_links` semantics or reciprocity rules.

## Agent Execution Rules

- Prefer academically precise naming (`statement_class`, `epistemic_status`, `theory_context`, `inferential_links`).
- Keep canonical expressions mathematically standard and discipline-accurate.
- Treat corollaries as derived statements with explicit `entailed_by` references.
- Require provenance for new nodes where possible.
- Run `python scripts/validate_nodes.py` after edits to corpus or schema.

## Copilot and VS Code Integration

- Repository-wide guidance: `.github/copilot-instructions.md`
- Agent skills:
  - `.github/skills/statistics-ontology-authoring/SKILL.md`
  - `.github/skills/schema-and-links-governance/SKILL.md`

These paths follow current Agent Skills conventions used by GitHub Copilot and VS Code Copilot.
