#!/usr/bin/env python3
"""Seed data/lean_workbook/nodes.json — covered ingest + skeleton emitter.

First wave (docs/DESIGN-item4-authoring.md): unique-covered ground arithmetic.
Second wave (docs/DESIGN-skeleton-emitter.md): every remaining unique-covered
statement whose emitted matcher template parses. Formal without verified_by.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import grammar_coverage as gc  # noqa: E402
import emit_skeleton as emit  # noqa: E402
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
    text = text.replace("√", "SQRT")
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


def select_ground() -> list[dict]:
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


def select_emitted(skip_names: set[str]) -> tuple[list[tuple[dict, str]], dict]:
    """Remaining unique-covered statements whose emitted template parses.

    Returns ([(stmt, template), ...], census).
    """
    extract = json.loads(EXTRACT.read_text(encoding="utf-8"))
    seen: set[str] = set()
    chosen: list[tuple[dict, str]] = []
    excluded: dict[str, int] = {}
    samples: dict[str, list[str]] = {}
    considered = 0
    for stmt in extract["statements"]:
        if stmt["name"] in SKIP_NAMES or stmt["name"] in skip_names:
            continue
        key = " ".join(stmt["goal"].split())
        if key in seen:
            continue
        seen.add(key)
        if is_ground_arith(stmt) and template_parses(
            to_template(strip_goal(stmt["goal"]))
        ):
            continue  # first wave owns these
        if not gc.classify(stmt)["full_ok"]:
            continue
        considered += 1
        template, reason = emit.emit_or_reason(stmt)
        if template is None:
            why = reason or "unknown"
            excluded[why] = excluded.get(why, 0) + 1
            bucket = samples.setdefault(why, [])
            if len(bucket) < 5:
                bucket.append(f"{stmt['name']}: {stmt['goal'][:160]}")
            continue
        chosen.append((stmt, template))
    census = {
        "generated_by": "scripts/seed_lean_workbook.py emit census",
        "design": "docs/DESIGN-skeleton-emitter.md",
        "unique_covered_considered": considered,
        "emitted": len(chosen),
        "excluded": sum(excluded.values()),
        "excluded_by_reason": dict(sorted(excluded.items(),
                                          key=lambda kv: (-kv[1], kv[0]))),
        "excluded_samples": samples,
    }
    return chosen, census


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


def node_from_emitted(stmt: dict, template: str) -> dict:
    name = stmt["name"]
    sid = "leanworkbook.skel." + name
    slots = [
        {
            "slot_id": s,
            "syntactic_category": "variable",
            "semantic_role": "value in an ingested covered statement",
        }
        for s in emit.slots_in(template)
    ]
    if not slots:
        slots = [{
            "slot_id": "GROUND",
            "syntactic_category": "constant",
            "semantic_role": "documentation of a fully ground template",
        }]
    surface = stmt["goal"]
    return {
        "statement_id": sid,
        "title": f"{name} (Ingested, Emitted Skeleton, Formal Without Bridge)",
        "statement_class": "proposition",
        "epistemic_status": "formal",
        "theory_context": {
            "disciplines": ["number_theory"],
            "subfield": "covered_ingest",
            "topic": "ingested_lean_workbook",
        },
        "formal_statement": {
            "canonical_ascii": surface,
            "canonical_latex": surface,
            "equivalent_forms": [
                {
                    "form_id": "emitted_skeleton",
                    "notation_system": "ascii",
                    "expression": template,
                    "scope_note": "Matcher template emitted from the pinned extract.",
                }
            ],
        },
        "structural_signature": {
            "archetype_id": "ingested_emitted_skeleton",
            "anonymized_template": template,
            "slot_schema": slots,
            "invariants": [
                "Emitted from Lean surface by scripts/emit_skeleton.py.",
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
                    "symbol": slots[0]["slot_id"],
                    "syntactic_category": "variable",
                    "semantic_role": "ingested_slot",
                    "mathematical_order": 0,
                    "description": "A slot standing in an emitted template.",
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
            "constants": [],
        },
        "semantic_interpretation": {
            "statement_meaning": (
                f"The covered Lean-workbook claim stated by problem {name}, "
                f"emitted as a matcher template (docs/DESIGN-skeleton-emitter.md)."
            ),
            "statistical_significance": (
                "Second-wave ingest of unique-covered statements whose Lean "
                "surface emits a parse-clean matcher template. "
                "formal-without-bridge."
            ),
            "regularity_conditions": [
                "Heads are the corpus heads the coverage instrument already carries.",
                "Hypotheses, if any, wrap the goal as IMPLIES(MEET(...), goal).",
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
        "keywords": ["ingested", "lean workbook", "emitted skeleton",
                     "formal without bridge"],
    }


def main() -> None:
    ground = select_ground()
    skip = {s["name"] for s in ground}
    emitted, census = select_emitted(skip)
    nodes = [node_from(stmt) for stmt in ground]
    nodes.extend(node_from_emitted(stmt, tmpl) for stmt, tmpl in emitted)
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "lean_workbook.ground.v1",
        "discipline": "lean_workbook",
        "version": "1.0.0-alpha",
        "statement_nodes": nodes,
    }
    out = Path("data") / "lean_workbook" / "nodes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(
        (json.dumps(corpus, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    )
    census_path = Path("experiments") / "lean_workbook_emit.json"
    gc.write_json(census_path, census)
    print(
        f"wrote {out} ({len(ground)} ground + {len(emitted)} emitted = "
        f"{len(nodes)} nodes); census {census_path} "
        f"(excluded {census['excluded']})"
    )


if __name__ == "__main__":
    main()
