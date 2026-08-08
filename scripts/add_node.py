#!/usr/bin/env python3
"""Add Mathematical Statement Nodes from YAML/JSON template files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def load_json(path: Path) -> dict:
    """Load JSON from file."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    """Save JSON to file with proper formatting."""
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_template(path: Path) -> dict:
    """Load template from YAML or JSON file."""
    content = path.read_text(encoding="utf-8")
    
    if path.suffix in [".yaml", ".yml"]:
        if not YAML_AVAILABLE:
            print("Error: PyYAML is required for YAML files. Install with: pip install pyyaml")
            sys.exit(1)
        return yaml.safe_load(content)
    elif path.suffix == ".json":
        return json.loads(content)
    else:
        print(f"Error: Unsupported file format '{path.suffix}'. Use .yaml, .yml, or .json")
        sys.exit(1)


def create_template_file(output_path: Path, format: str = "yaml") -> None:
    """Create a template file with examples and documentation."""
    
    template = {
        "title": "Example Theorem Name",
        "statement_class": "theorem",
        "epistemic_status": "formal",
        "theory_context": {
            "disciplines": ["mathematics", "statistics"],
            "subfield": "probability_theory",
            "topic": "foundational_theorems"
        },
        "formal_statement": {
            "canonical_ascii": "E[X] = sum(x * P(X=x))",
            "canonical_latex": "E[X] = \\sum_{x} x \\cdot P(X=x)",
            "equivalent_forms": [
                {
                    "form_id": "expectation_discrete",
                    "notation_system": "ascii",
                    "expression": "E[X] = sum(x * p(x))",
                    "scope_note": "For discrete random variables"
                }
            ]
        },
        "structural_signature": {
            "archetype_id": "expectation_operator",
            "anonymized_template": "FUNCTIONAL[VAR] = SUM(VAR * PROB)",
            "slot_schema": [
                {
                    "slot_id": "VAR",
                    "syntactic_category": "random_variable",
                    "semantic_role": "target_variable"
                },
                {
                    "slot_id": "FUNCTIONAL",
                    "syntactic_category": "functional",
                    "semantic_role": "expectation_operator"
                },
                {
                    "slot_id": "PROB",
                    "syntactic_category": "distribution",
                    "semantic_role": "probability_mass"
                }
            ],
            "invariants": [
                "Linearity in VAR",
                "Weighted sum over support"
            ]
        },
        "symbol_lexicon": {
            "symbols": [
                {
                    "symbol": "X",
                    "syntactic_category": "random_variable",
                    "semantic_role": "random_variable",
                    "mathematical_order": 0,
                    "description": "Random variable"
                }
            ],
            "operators": [
                {
                    "symbol": "=",
                    "name": "equality",
                    "arity": 2,
                    "operator_family": "relational"
                }
            ],
            "functionals": [
                {
                    "notation": "E[·]",
                    "name": "expectation",
                    "input_arity": 1,
                    "codomain": "real",
                    "description": "Expected value operator"
                }
            ],
            "index_sets": [],
            "constants": []
        },
        "semantic_interpretation": {
            "statement_meaning": "The expected value is the probability-weighted average of all possible values",
            "statistical_significance": "Provides the center of mass of a probability distribution",
            "regularity_conditions": [
                "Random variable must have finite expectation",
                "Support must be countable (for discrete case)"
            ],
            "failure_modes": [
                "Does not exist for distributions with infinite expectation"
            ]
        },
        "inferential_links": {
            "entailed_by": [],
            "entails": [],
            "equivalent_to": [],
            "special_case_of": [],
            "generalizes": [],
            "composed_with": []
        },
        "provenance": [
            {
                "citation_key": "ross2014",
                "bibliographic_entry": "Ross, S. M. (2014). Introduction to Probability Models (11th ed.). Academic Press.",
                "url": "https://example.com/reference"
            }
        ],
        "keywords": ["expectation", "expected value", "probability"]
    }
    
    if format == "yaml" and YAML_AVAILABLE:
        # Add comments for YAML
        output_path.write_text(
            "# Mathematical Statement Node Template\n"
            "# Fill in the fields below to define a new node\n"
            "# \n"
            "# Required fields are marked with (REQUIRED)\n"
            "# Optional fields can be removed or left empty\n"
            "# \n"
            "# statement_class options: axiom, definition, lemma, proposition, theorem,\n"
            "#   corollary, identity, model_specification, estimator, transformation, approximation\n"
            "# \n"
            "# epistemic_status options: formal, derived, assumed, asymptotic, empirical\n"
            "# \n"
            "# notation_system options: ascii, latex, matrix_notation, event_probability,\n"
            "#   measure_theoretic, vector_notation\n"
            "# \n"
            "# syntactic_category options:\n"
            "#   - For symbols: variable, parameter, random_variable, statistic, set, index,\n"
            "#                  sequence, distribution, constant\n"
            "#   - For slots: variable, parameter, random_variable, statistic, functional,\n"
            "#                operator, set, index, sequence, distribution, constant\n"
            "# \n"
            "# operator_family options: arithmetic, relational, logical, set_theoretic,\n"
            "#   measure_theoretic, stochastic, limit\n"
            "\n"
            + yaml.dump(template, default_flow_style=False, sort_keys=False),
            encoding="utf-8"
        )
    else:
        # Save as JSON with comments in the structure
        save_json(output_path, template)
    
    print(f"✓ Template created: {output_path}")
    print(f"\nEdit this file and then run:")
    print(f"  python scripts/add_node.py --template {output_path} --discipline <discipline_name>")


def validate_node_structure(node: dict, schema: dict) -> list[str]:
    """Basic validation of node structure."""
    errors = []
    
    # Check required fields (except statement_id which can be auto-generated)
    required_fields = [f for f in schema.get("required", []) if f != "statement_id"]
    for field in required_fields:
        if field not in node:
            errors.append(f"Missing required field: {field}")
    
    # Check statement_class
    valid_classes = schema.get("properties", {}).get("statement_class", {}).get("enum", [])
    if node.get("statement_class") not in valid_classes:
        errors.append(f"Invalid statement_class: {node.get('statement_class')}")
    
    # Check epistemic_status
    valid_statuses = schema.get("properties", {}).get("epistemic_status", {}).get("enum", [])
    if node.get("epistemic_status") not in valid_statuses:
        errors.append(f"Invalid epistemic_status: {node.get('epistemic_status')}")
    
    return errors


def generate_statement_id(discipline: str, node: dict, existing_ids: set[str]) -> str:
    """Generate a unique statement ID if not provided."""
    if "statement_id" in node:
        return node["statement_id"]
    
    # Extract topic and title
    topic = node.get("theory_context", {}).get("topic", "general")
    title = node.get("title", "untitled")
    
    # Create a base ID
    base = f"{discipline}.{topic.replace(' ', '_').lower()}"
    
    # Create a suffix from the title
    words = title.lower().replace("-", " ").split()
    suffix = "_".join(w for w in words[:3] if w.isalnum())
    
    # Try the generated ID
    candidate = f"{base}.{suffix}"
    if candidate not in existing_ids:
        return candidate
    
    # If collision, add a number
    counter = 2
    while f"{candidate}_{counter}" in existing_ids:
        counter += 1
    return f"{candidate}_{counter}"


def main() -> int:
    """Main entry point."""
    import sys as _sys
    if "--legacy-direct-json" not in _sys.argv:
        print("DEPRECATED: add_node.py edits nodes.json directly, which now")
        print("violates the seed-as-source-of-truth invariant enforced by")
        print("scripts/check_regeneration.py (your edit would be flagged as")
        print("DRIFT and clobbered by the next regeneration).")
        print("Author via scripts/seed_<discipline>.py instead -- see")
        print("docs/ADDING_FORMULAE.md. To run anyway: --legacy-direct-json")
        return 1
    _sys.argv.remove("--legacy-direct-json")
    parser = argparse.ArgumentParser(
        description="Add Mathematical Statement Nodes from template files",
        epilog="Use --create-template to generate a template file to fill in."
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="Path to YAML or JSON template file containing node definition"
    )
    parser.add_argument(
        "--discipline",
        help="Discipline name (e.g., 'statistics', 'calculus'). Required when adding a node."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Base data directory (default: data)"
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schema/equation-node.schema.json"),
        help="Path to schema file (default: schema/equation-node.schema.json)"
    )
    parser.add_argument(
        "--create-template",
        type=Path,
        metavar="OUTPUT_FILE",
        help="Create a template file (YAML or JSON based on extension) and exit"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the template without adding to corpus"
    )
    args = parser.parse_args()
    
    # Handle template creation
    if args.create_template:
        format = "yaml" if args.create_template.suffix in [".yaml", ".yml"] else "json"
        create_template_file(args.create_template, format)
        return 0
    
    # Require template for adding nodes
    if not args.template:
        parser.error("--template is required (or use --create-template to generate one)")
    
    if not args.template.exists():
        print(f"Error: Template file not found: {args.template}")
        return 1
    
    # Load template
    print(f"Loading template: {args.template}")
    try:
        node = load_template(args.template)
    except Exception as e:
        print(f"Error loading template: {e}")
        return 1
    
    # Load schema for validation
    schema = {}
    if args.schema.exists():
        schema = load_json(args.schema)
    
    # Basic validation
    errors = validate_node_structure(node, schema)
    if errors:
        print("Template validation errors:")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    print("✓ Template structure validated")
    
    if args.validate_only:
        print("\n✓ Validation successful (--validate-only mode)")
        return 0
    
    # Require discipline for adding
    if not args.discipline:
        parser.error("--discipline is required when adding a node")
    
    discipline = args.discipline
    
    # Set up corpus path
    discipline_dir = args.data_dir / discipline
    corpus_path = discipline_dir / "nodes.json"
    
    # Create discipline directory if needed
    if not discipline_dir.exists():
        print(f"Creating new discipline directory: {discipline_dir}")
        discipline_dir.mkdir(parents=True)
    
    # Load or create corpus
    if corpus_path.exists():
        corpus = load_json(corpus_path)
        existing_count = len(corpus.get("statement_nodes", []))
        print(f"Loaded existing corpus with {existing_count} nodes")
    else:
        print(f"Creating new corpus: {corpus_path}")
        corpus = {
            "schema": "../../schema/equation-node.schema.json",
            "corpus_id": f"{discipline}.foundations.v1",
            "discipline": discipline,
            "version": "1.0.0-alpha",
            "statement_nodes": []
        }
        existing_count = 0
    
    # Get existing IDs
    existing_ids = {n["statement_id"] for n in corpus.get("statement_nodes", [])}
    
    # Generate ID if not provided
    if "statement_id" not in node:
        node["statement_id"] = generate_statement_id(discipline, node, existing_ids)
        print(f"Generated statement ID: {node['statement_id']}")
    
    # Check for duplicate ID
    if node["statement_id"] in existing_ids:
        print(f"Error: statement_id '{node['statement_id']}' already exists in corpus")
        return 1
    
    # Add node to corpus
    corpus["statement_nodes"].append(node)
    
    # Save corpus
    save_json(corpus_path, corpus)
    print(f"\n✓ Node added to {corpus_path}")
    print(f"  Corpus now has {len(corpus['statement_nodes'])} nodes (was {existing_count})")
    
    # Validate with full validator
    if args.schema.exists():
        print("\nRunning full validation...")
        import subprocess
        result = subprocess.run(
            ["python", "scripts/validate_nodes.py", "--nodes", str(corpus_path)],
            cwd=Path.cwd(),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Validation passed")
            print(result.stdout.strip())
        else:
            print("✗ Validation failed:")
            print(result.stdout)
            print(result.stderr)
            
            # Remove the added node since validation failed
            corpus["statement_nodes"] = corpus["statement_nodes"][:-1]
            save_json(corpus_path, corpus)
            print("\n⚠ Node removed from corpus due to validation failure")
            return 1
    
    print(f"\n✓ Successfully added node '{node['statement_id']}'!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
