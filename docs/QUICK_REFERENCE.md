# Formula Entry System - Quick Reference

## Basic Commands

### Create a template
```bash
python scripts/add_node.py --create-template formula.json
# or
python scripts/add_node.py --create-template formula.yaml
```

### Validate a template
```bash
python scripts/add_node.py --template formula.json --validate-only
```

### Add to corpus
```bash
python scripts/add_node.py --template formula.json --discipline <name>
```

### Validate corpus
```bash
python scripts/validate_nodes.py
# or specific:
python scripts/validate_nodes.py --nodes data/<discipline>/nodes.json
```

## Required Template Fields

| Field | Description | Example |
|-------|-------------|---------|
| `title` | Formal name | "Pythagorean Theorem" |
| `statement_class` | Type of statement | "theorem", "definition", "corollary" |
| `epistemic_status` | Status of knowledge | "formal", "derived", "assumed" |
| `theory_context` | Discipline & topic | `{"disciplines": ["math"], "subfield": "...", "topic": "..."}` |
| `formal_statement` | Mathematical expression | `{"canonical_ascii": "...", "equivalent_forms": [...]}` |
| `structural_signature` | Anonymized form | `{"archetype_id": "...", "anonymized_template": "...", "slot_schema": [...]}` |
| `symbol_lexicon` | Symbols used | `{"symbols": [...], "operators": [...], ...}` |
| `semantic_interpretation` | Meaning | `{"statement_meaning": "...", "statistical_significance": "..."}` |
| `inferential_links` | Relations | `{"entailed_by": [], "entails": [], ...}` |

## Optional Fields

- `statement_id` - Auto-generated if omitted
- `provenance` - Bibliographic references
- `keywords` - Search terms

## Example Disciplines

- `statistics` - Statistical theorems and models
- `geometry` - Geometric theorems
- `calculus` - Calculus theorems
- `algebra` - Algebraic identities
- `probability_theory` - Probability theorems

Create new disciplines by specifying a new name!

## Tips

1. **Always start from a template**: `--create-template`
2. **Validate before adding**: `--validate-only`
3. **Check examples**: Look at `data/statistics/nodes.json`
4. **Empty inferential_links are OK**: Use `[]` for each field
5. **Auto-generated IDs**: Leave out `statement_id` to generate automatically

## Full Documentation

See [docs/ADDING_FORMULAE.md](ADDING_FORMULAE.md) for complete instructions.
