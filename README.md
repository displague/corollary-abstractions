# corollary-abstractions

Statistics-first ontology for mathematical statements and their inferential descendants.

## Research Intent

The project models equations, inequalities, definitions, theorems, and corollaries as typed statement nodes so that:

- structurally isomorphic forms can be detected across disciplines
- corollaries can be re-evaluated in alternate theoretical contexts
- symbolic form, semantic role, and inferential lineage are captured separately

## Ontology Design

Each statement node is represented as a `Mathematical Statement Node` with the following sections:

- `statement_class`: definition/theorem/corollary/model specification/etc.
- `epistemic_status`: formal, derived, assumed, asymptotic, empirical
- `theory_context`: discipline and subfield placement
- `formal_statement`: canonical and equivalent symbolic representations
- `structural_signature`: anonymized template plus typed role slots
- `symbol_lexicon`: symbols, operators, functionals, constants, index sets
- `semantic_interpretation`: meaning, inferential role, regularity conditions
- `inferential_links`: entailment, equivalence, specialization, composition edges
- `provenance`: bibliographic source anchors

## Project Files

- Schema: `schema/equation-node.schema.json`
- Statistics corpus: `data/statistics/nodes.json`
- Validator: `scripts/validate_nodes.py`

## Statistics Seed Corpus

Current seed nodes cover:

- affine location-scale transformation archetype
- simple linear regression specification and conditional expectation corollary
- z-standardization and normal-standardization corollary
- law of total probability and Bayes rule
- variance definition and computational identity corollary
- IID CLT and large-sample normal approximation corollary

## Validation

```bash
python scripts/validate_nodes.py
```
