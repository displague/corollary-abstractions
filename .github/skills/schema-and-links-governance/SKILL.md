# Skill: schema-and-links-governance

Maintain schema coherence and inferential-link integrity.

- Schema: `schema/equation-node.schema.json`. Node-level
  `additionalProperties: false` everywhere — extending requires a schema
  edit first (recent precedent: `epistemic_status: conjectured`,
  `verified_by`).
- Links: all six lists required; `entails`/`entailed_by`,
  `equivalent_to`, `special_case_of`/`generalizes` are
  reciprocity-checked over the MERGED graph by
  `scripts/validate_nodes.py`. Cross-corpus reciprocal edges require
  editing both owning seeds; `composed_with` is the only safe one-sided
  cross-corpus edge.
- `verified_by` entries `{system, artifact, reference}` link statements
  to machine-checked proofs; `seed_logic.py`'s check fails regeneration
  if the table and `prover/sample_triples.json` drift either way.
- Known schema gaps and their evidence live in `docs/BACKLOG.md`
  (scope construct, past modality, symbolToken categories).
