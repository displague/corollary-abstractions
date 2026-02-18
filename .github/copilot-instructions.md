# Copilot Instructions for corollary-abstractions

Use academically rigorous language and ontology-first structure.

## Core Working Model

- Treat each entry in `data/statistics/nodes.json` as a `Mathematical Statement Node`.
- Preserve the schema contract in `schema/equation-node.schema.json`.
- Maintain graph integrity through `inferential_links`.
- Apply project skills from `.github/skills/` when relevant.

## Authoring Principles

- Prefer formal naming over colloquial naming.
  - Good: `Lindeberg-Levy Central Limit Theorem`
  - Avoid: `CLT thing`
- Keep canonical expressions concise and standard.
- Distinguish:
  - `statement_class`: theorem/corollary/definition/transformation/model specification
  - `epistemic_status`: formal/derived/assumed/asymptotic/empirical
- Add provenance for new statements whenever a stable textbook source is known.

## Inferential Discipline

- For derived results, use `statement_class: corollary` and set `entailed_by`.
- Keep reciprocity consistent:
  - If A `entails` B, B should include A in `entailed_by`.
  - If A `generalizes` B, B should include A in `special_case_of`.
  - `equivalent_to` should be symmetric.

## Validation Requirement

After schema or corpus edits, run:

```bash
python scripts/validate_nodes.py
```

Do not finalize changes with failing validation.
