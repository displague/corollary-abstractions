# Quick Start Guide: Adding Formulae

This guide shows you how to add mathematical formulae from any discipline to the corollary-abstractions repository.

## Prerequisites

- Python 3.7+
- Optional: `pyyaml` for YAML template support (`pip install pyyaml`)

## Step 1: Create a Template

Generate a template file to guide your entry:

```bash
# Create JSON template (no dependencies required)
python scripts/add_node.py --create-template my_formula.json

# Or create YAML template (requires pyyaml)
python scripts/add_node.py --create-template my_formula.yaml
```

The template includes:
- All required and optional fields
- Documentation comments
- Valid options for each field
- Example values

## Step 2: Fill in Your Formula

Open the template in any text editor and fill in the details:

### Required Fields

- **title**: Formal name (e.g., "Pythagorean Theorem")
- **statement_class**: One of: axiom, definition, lemma, proposition, theorem, corollary, identity, model_specification, estimator, transformation, approximation
- **epistemic_status**: One of: formal, derived, assumed, asymptotic, empirical
- **theory_context**: Disciplines, subfield, and topic
- **formal_statement**: Canonical expression and equivalent forms
- **structural_signature**: Anonymized template and slot schema
- **symbol_lexicon**: Symbols, operators, functionals used
- **semantic_interpretation**: Meaning and significance
- **inferential_links**: Relationships to other nodes (can be empty arrays)

### Optional Fields

- **statement_id**: Auto-generated if not provided
- **provenance**: Bibliographic references
- **keywords**: Search terms

### Example: Simple Identity

```json
{
  "title": "Additive Identity",
  "statement_class": "identity",
  "epistemic_status": "formal",
  "theory_context": {
    "disciplines": ["mathematics", "algebra"],
    "subfield": "elementary_algebra",
    "topic": "arithmetic_properties"
  },
  "formal_statement": {
    "canonical_ascii": "x + 0 = x",
    "equivalent_forms": [
      {
        "form_id": "standard",
        "notation_system": "ascii",
        "expression": "x + 0 = x"
      }
    ]
  },
  "structural_signature": {
    "archetype_id": "identity_element",
    "anonymized_template": "ELEMENT + IDENTITY = ELEMENT",
    "slot_schema": [
      {
        "slot_id": "ELEMENT",
        "syntactic_category": "variable",
        "semantic_role": "operand"
      },
      {
        "slot_id": "IDENTITY",
        "syntactic_category": "constant",
        "semantic_role": "identity_element"
      }
    ],
    "invariants": ["Identity element for addition"]
  },
  "symbol_lexicon": {
    "symbols": [
      {
        "symbol": "x",
        "syntactic_category": "variable",
        "semantic_role": "operand",
        "mathematical_order": 0,
        "description": "Any number"
      }
    ],
    "operators": [
      {
        "symbol": "+",
        "name": "addition",
        "arity": 2,
        "operator_family": "arithmetic"
      },
      {
        "symbol": "=",
        "name": "equality",
        "arity": 2,
        "operator_family": "relational"
      }
    ],
    "functionals": [],
    "index_sets": [],
    "constants": [
      {
        "symbol": "0",
        "description": "Additive identity",
        "value": 0
      }
    ]
  },
  "semantic_interpretation": {
    "statement_meaning": "Adding zero to any number yields the same number",
    "statistical_significance": "Fundamental property of addition",
    "regularity_conditions": []
  },
  "inferential_links": {
    "entailed_by": [],
    "entails": [],
    "equivalent_to": [],
    "special_case_of": [],
    "generalizes": [],
    "composed_with": []
  }
}
```

## Step 3: Validate Your Template

Before adding, check if your template is valid:

```bash
python scripts/add_node.py --template my_formula.json --validate-only
```

This checks:
- Required fields are present
- Field values are valid
- Structure matches schema

## Step 4: Add to Corpus

Add your formula to a discipline:

```bash
python scripts/add_node.py --template my_formula.json --discipline <discipline_name>
```

For example:
```bash
# Add to existing statistics corpus
python scripts/add_node.py --template my_formula.json --discipline statistics

# Create new calculus corpus
python scripts/add_node.py --template my_formula.json --discipline calculus

# Add to geometry
python scripts/add_node.py --template my_formula.json --discipline geometry
```

The tool will:
1. ✓ Validate the template structure
2. ✓ Create the discipline directory if needed
3. ✓ Generate a unique statement_id if not provided
4. ✓ Add the node to `data/<discipline>/nodes.json`
5. ✓ Run full validation
6. ✓ Report success or errors

## Tips

1. **Start from the template**: Always use `--create-template` to ensure you have all required fields.

2. **Use descriptive titles**: Follow formal naming conventions:
   - Good: "Lindeberg-Levy Central Limit Theorem"
   - Avoid: "CLT thing"

3. **Validate early**: Use `--validate-only` to catch errors before adding.

4. **Check existing nodes**: Look at `data/statistics/nodes.json` for examples.

5. **Inferential links**: Start with empty arrays (`[]`). Add links after related nodes exist.

6. **Provenance**: Include bibliographic references when available.

## Common Errors

### Missing required fields
```
Error: Missing required field: formal_statement
```
**Solution**: Fill in all required fields from the schema.

### Invalid enum value
```
Error: Invalid statement_class: 'my_custom_type'
```
**Solution**: Use only the predefined values listed in the template comments.

### Validation failure
```
✗ Validation failed:
- node_id: missing inferential link list `entails`
```
**Solution**: Ensure all inferential_links fields are present (even as empty arrays).

## Getting Help

- Check the [schema](../schema/equation-node.schema.json) for complete field definitions
- Look at [existing nodes](../data/statistics/nodes.json) for examples
- See [copilot instructions](../.github/copilot-instructions.md) for authoring principles
- Run validation frequently: `python scripts/validate_nodes.py`
