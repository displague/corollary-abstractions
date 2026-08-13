#!/usr/bin/env python3
"""Seed data/lean_workbook/nodes.json — first wave of covered ingest.

docs/DESIGN-item4-authoring.md (committed first). Unique-covered Lean-workbook
goals that are ground arithmetic after stripping Lean type ascriptions.
Formal without verified_by (item 2 decision (b), recorded at node level).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import grammar_coverage as gc  # noqa: E402
from match_signatures import Parser, TemplateParseError, canonicalize, tokenize  # noqa: E402

EXTRACT = REPO / "data_sources" / "derived" / "lean_workbook" / "statements.json"

# Already authored elsewhere (item 2 / item 5).
SKIP_NAMES = frozenset(
    {
        "lean_workbook_1041",
        "lean_workbook_10202",
        "lean_workbook_10411",
        "lean_workbook_22080",
        "lean_workbook_26313",
    }
)

ASCRIPTION = re.compile(r"\(\s*(\d+)\s*:\s*[^)]+\)")
GROUND = re.compile(r"^[0-9+\-*/^%=<>≤≥∣\s√()]+$")
SQRT_BARE = re.compile(r"√\s*(\d+)")
ATTRIBUTION = (
    "Lean-workbook-proofs (c) Goedel-LM, MIT License. Proofs by "
    "Goedel-Prover (Lin et al., 2025, arXiv:2502.07640); problems from "
    "Lean Workbook. Statement signatures extracted; proofs omitted."
)

PROVENANCE = [
    {
        "citation_key": "leanworkbook_goedel2025",
        "bibliographic_entry": ATTRIBUTION,
        "url": "https://huggingface.co/datasets/Goedel-LM/Lean-workbook-proofs",
    }
]


def strip_goal(goal: str) -> str:
    text = ASCRIPTION.sub(r"\1", goal)
    text = text.replace("ℝ", "").replace("ℕ", "").replace("ℤ", "").replace("ℚ", "")
    return " ".join(text.split())


def to_template(surface: str) -> str:
    text = SQRT_BARE.sub(r"SQRT(\1)", surface)
    text = text.replace("∣", " | ")
    text = text.replace("≥", ">=").replace("≤", "<=")
    return " ".join(text.split())


def template_parses(template: str) -> bool:
    try:
        canonicalize(Parser(tokenize(template)).parse())
    except TemplateParseError:
        return False
    return True


def is_ground_arith(stmt: dict) -> bool:
    surface = strip_goal(stmt["goal"])
    return bool(GROUND.match(surface.replace("SQRT", "")))


def select_statements() -> list[dict]:
    extract = json.loads(EXTRACT.read_text(encoding="utf-8"))
    seen: set[str] = set()
    chosen: list[dict] = []
    for stmt in extract["statements"]:
        if stmt["name"] in SKIP_NAMES:
            continue
        key = " ".join(stmt["goal"].split())
        if key in seen:
            continue
        seen.add(key)
        if not is_ground_arith(stmt):
            continue
        if not gc.classify(stmt)["full_ok"]:
            continue
        if not template_parses(to_template(strip_goal(stmt["goal"]))):
            continue
        chosen.append(stmt)
    return chosen


def node_from(stmt: dict) -> dict:
    surface = strip_goal(stmt["goal"])
    template = to_template(surface)
    name = stmt["name"]
    sid = "leanworkbook.ground." + name
    return {
        "statement_id": sid,
        "title": f"{name} (Ingested, Formal Without Bridge)",
        "statement_class": "proposition",
        "epistemic_status": "formal",
        "theory_context": {
            "disciplines": ["number_theory"],
            "subfield": "ground_arithmetic",
            "topic": "ingested_lean_workbook",
        },
        "formal_statement": {
            "canonical_ascii": surface,
            "canonical_latex": surface.replace("%", "\\bmod "),
            "equivalent_forms": [
                {
                    "form_id": "ascii_ground",
                    "notation_system": "ascii",
                    "expression": surface,
                    "scope_note": "Restated from the pinned Lean-workbook extract.",
                }
            ],
        },
        "structural_signature": {
            "archetype_id": "ingested_ground_arithmetic",
            "anonymized_template": template,
            "slot_schema": [
                {
                    "slot_id": "GROUND",
                    "syntactic_category": "constant",
                    "semantic_role": "documentation of a fully ground template",
                }
            ],
            "invariants": [
                "Fully ground: no matcher slots.",
                "NODE-LEVEL RECORD, decision (b) of ROADMAP-v0.10 item 2: "
                "formal without a verified_by bridge. The Lean-workbook proof "
                "is not re-checked under this repo's hermetic core-Lean "
                "budget. epistemic_status formal records provenance, not a "
                "certificate.",
            ],
        },
        "symbol_lexicon": {
            "symbols": [
                {
                    "symbol": "1",
                    "syntactic_category": "constant",
                    "semantic_role": "ground_numeral",
                    "mathematical_order": 0,
                    "description": "A ground numeral standing in the template.",
                }
            ],
            "operators": [
                {
                    "symbol": "=",
                    "name": "equality",
                    "arity": 2,
                    "operator_family": "relational",
                }
            ],
            "functionals": [],
            "index_sets": [],
            "constants": [
                {
                    "symbol": "1",
                    "description": "ground numeral",
                    "value": 1,
                }
            ],
        },
        "semantic_interpretation": {
            "statement_meaning": (
                f"The ground arithmetic claim stated by Lean-workbook "
                f"problem {name}, restated from the pinned extract."
            ),
            "statistical_significance": (
                "First-wave ingest of the unique-covered ground-arithmetic "
                "subset (docs/DESIGN-item4-authoring.md). formal-without-bridge."
            ),
            "regularity_conditions": [
                "Ground numerals; operators read as the corpus heads."
            ],
        },
        "inferential_links": {
            "entailed_by": [],
            "entails": [],
            "equivalent_to": [],
            "special_case_of": [],
            "generalizes": [],
            "composed_with": [],
        },
        "provenance": PROVENANCE,
        "keywords": ["ingested", "lean workbook", "ground arithmetic",
                     "formal without bridge"],
    }


def main() -> None:
    statements = select_statements()
    nodes = [node_from(stmt) for stmt in statements]
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "lean_workbook.ground.v1",
        "discipline": "lean_workbook",
        "version": "1.0.0-alpha",
        "statement_nodes": nodes,
    }
    out = Path("data") / "lean_workbook" / "nodes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out} ({len(nodes)} nodes)")


if __name__ == "__main__":
    main()
