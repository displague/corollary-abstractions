# corollary-abstractions

Cross-discipline ontology of mathematical statements, with a symbolic engine
that detects structurally isomorphic formulas ("twins") across disciplines.

## Research Intent

The project models equations, inequalities, definitions, theorems, and corollaries as typed statement nodes so that:

- structurally isomorphic forms can be detected across disciplines
- corollaries can be re-evaluated in alternate theoretical contexts
- symbolic form, semantic role, and inferential lineage are captured separately

Longer term, the discovered structures are candidate *concept tokens* for an
extremely small model whose lexicon lives outside its weights — see
`docs/DESIGN-concept-tokens.md` for the design and `prover/README.md` for the
verifier-coupled sub-project that will test it.

## Structural Twin Detection

`scripts/match_signatures.py` parses every node's
`structural_signature.anonymized_template` into an expression tree,
canonicalizes it, and groups nodes by structural skeleton:

```bash
python scripts/match_signatures.py --write-report reports/signature_matches.json
```

It reports typed twins (slot categories respected), shape twins (categories
ignored), archetype-label drift, and `slot_schema` gaps. Twin proposals stay
in `reports/` — structural isomorphism is analogy, not the logical
`equivalent_to` of `inferential_links`.

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
- Corpora: `data/<discipline>/nodes.json` (statistics, geometry, algebra)
- Validator: `scripts/validate_nodes.py`
- Twin detection: `scripts/match_signatures.py`
- Formula entry CLI: `scripts/add_node.py`
- Model design: `docs/DESIGN-concept-tokens.md`
- Prover sub-project: `prover/README.md`

## Statistics Seed Corpus

Current seed nodes cover:

- affine location-scale transformation archetype
- simple linear regression specification and conditional expectation corollary
- z-standardization and normal-standardization corollary
- law of total probability and Bayes rule
- variance definition and computational identity corollary
- IID CLT and large-sample normal approximation corollary

## Adding New Formulae

To add formulae from any discipline **without directly editing JSON files**, use the `add_node.py` tool.

**📖 See the [complete guide](docs/ADDING_FORMULAE.md) for detailed instructions.**

### Quick Start

1. **Create a template file:**
   ```bash
   python scripts/add_node.py --create-template my_formula.json
   ```
   
   This creates a template with all required fields and documentation. You can also create YAML templates:
   ```bash
   python scripts/add_node.py --create-template my_formula.yaml
   ```

2. **Edit the template file** with your formula's details using any text editor.

3. **Add the formula to the corpus:**
   ```bash
   python scripts/add_node.py --template my_formula.json --discipline <discipline_name>
   ```
   
   The tool will:
   - Automatically generate a unique `statement_id` if not provided
   - Create the discipline directory if it doesn't exist
   - Validate the node structure
   - Add it to the appropriate corpus
   - Run full validation before committing

### Example Workflow

```bash
# Create a template for a new calculus theorem
python scripts/add_node.py --create-template /tmp/fundamental_theorem.json

# Edit the template with your theorem details
# (use your favorite editor)

# Add to the calculus discipline
python scripts/add_node.py --template /tmp/fundamental_theorem.json --discipline calculus

# Output:
# ✓ Template structure validated
# ✓ Node added to data/calculus/nodes.json
# ✓ Validation passed
# ✓ Successfully added node 'calculus.integration.fundamental_theorem'!
```

### Validate Without Adding

To check if your template is valid before adding it:

```bash
python scripts/add_node.py --template my_formula.json --validate-only
```

## Validation

Validate all corpora as one merged cross-discipline graph (default):

```bash
python scripts/validate_nodes.py

# Or validate a specific corpus:
python scripts/validate_nodes.py --nodes data/geometry/nodes.json
```

Install `jsonschema` (`pip install jsonschema`) to enable full schema
validation; without it only the minimal structural checks run.
