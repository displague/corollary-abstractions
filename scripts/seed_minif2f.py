#!/usr/bin/env python3
"""Seed data/minif2f/nodes.json — held-out A of docs/DESIGN-heldout-recovery.md.

miniF2F competition statements, admitted by the SAME coverage instrument
(`grammar_coverage.classify` -> `full_ok`) and authored by the SAME emitter
(`emit_skeleton.emit_or_reason`) that produced the 12,514 Lean-workbook
templates in v0.11. Formal without a verified_by bridge.

**The emitter is not widened for this source** (design §3). A statement the
emitter refuses is an exclusion, counted in
`experiments/minif2f_emit.json` — never a reason to add a tokenizer rule.
That discipline is the whole point of calling this a holdout: an emitter
tuned on miniF2F would make the recovery curve a fact about the tuning.

Why this is a holdout and Lean-workbook is not (design §3): a random slice
of Lean-workbook is a split, not a source holdout. miniF2F is competition
problems (AIME/AMC/IMO and MATH-derived), not olympiad inequality drills,
and the emitter was fitted to neither its distribution nor its surface.

## Registered predictions (written before this seed was first run)

- **E1 (coverage).** Unique full-statement-covered statements = 163 +/- 5.
  Design quotes 163/488 (33.4%); dedup on the normalized goal can only
  lower it.  ADJUDICATED: **160** — fired.
- **E2 (emit rate).** >= 90% of considered emit a parse-clean template
  through the unwidened emitter (Lean-workbook got 99.03%).
  ADJUDICATED: **98.12%** (157/160) — fired.
- **E3 (exclusion shape).** Exclusions dominated by `emit:` refusals
  rather than `parse_fail`.  ADJUDICATED: 2 `emit:untokenizable` vs 1
  `parse_fail` — fired, but n=3 is barely a test and is reported as such.
- **E4 (regime).** Authored count lands in [128, 512], the band where
  v0.11's own curve was below its null at N=8/32 and had flipped by 128.
  ADJUDICATED: **157** — fired. Held-out A can therefore probe H2's flip
  point, but only just: N=all is 157, so the curve runs 8 / 32 / 157.

The three refusals, recorded because they are the emitter's honest edge:
`mathd_algebra_129` and `mathd_algebra_245` use the superscript inverse
`x⁻¹`, which the tokenizer has no rule for; `aime_1983_p9` emits a string
the matcher then declines to re-parse. Note `mathd_algebra_129`'s *goal*
is the trivial `a = -2` — the refusal is in a hypothesis, because
`emit_statement` folds hypotheses into `IMPLIES(MEET(...), goal)`.

## Why this writes data_holdout/, not data/

A holdout committed into `data/` is not held out: it joins the merged
graph every ledger and pinned guard is computed over. Measured, both
discipline labels distort the published v0.11 channel split, and the
constituent total moves on either:

| variant | constituents | external (conservative) | prior_corpus |
|---|---|---|---|
| v0.11 tagged / pinned | 181,909 | 0.391 | 286 |
| `data/`, discipline `minif2f` | 183,305 | **0.581** | **10** |
| `data/`, discipline `number_theory` | 183,305 | 0.389 | **26,014** |

A novel discipline makes the holdout a universal `external` donor —
`owner_channel`'s docstring argues against exactly that shape, since an
umbrella label is "shared ground that must not be counted as external
evidence." `number_theory` fixes the external share but makes the holdout
a 26k-strong `prior_corpus` donor to the Lean-workbook layer. There is no
free label: the holdout would be paying grounding credit to the very
corpus it is supposed to be independent of.

So `data_holdout/` is a **quarantine tier** — a corpus that keeps every
benefit of being committed (git-versioned, browsable, schema-validated,
byte-reproducible from this seed) while being invisible to the default
merged graph. `decompose.load_trees` already takes its data directory as
a parameter, so the measurement loads
`load_trees(data_holdout)` and merges it in memory as the ingested
overlay — which is precisely what `analyze_loaded`'s docstring describes:
"the curve's many points share one `load_trees` of the curated layer;
only the ingested overlay changes."

Gates that still cover it:
  python scripts/check_regeneration.py                      # both roots
  python scripts/validate_nodes.py --nodes data_holdout/minif2f/nodes.json

## Ingested, not curated

These nodes are **ingested** in the sense `decompose._ingested_sid` means:
authored in one mechanical act from a pinned external extract, not written
by hand. `minif2f` is registered there and in
`measure_operator_bag.INGESTED_DISCIPLINES` alongside `lean_workbook`.
Those registrations are inert while the holdout is unloaded — no node
carries the corpus id — and become load-bearing the moment the
measurement merges the overlay: without them P-E5 would promote these 157
forms to patterns and move the grounding of every node in the merged run.

Discipline is `mathematics`, the honest umbrella for competition problems
spanning algebra, number theory and geometry. `owner_channel` treats a
shared umbrella as non-external on purpose, which is the correct reading
here: miniF2F is not an independent field from the rest of the corpus.

Held-out-ness is a fact about the MEASUREMENT's id set (design §4:
Lean-workbook is curated-relative to this holdout), not about this flag.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import grammar_coverage as gc  # noqa: E402
import emit_skeleton as emit  # noqa: E402

EXTRACT = REPO / "data_sources" / "derived" / "minif2f" / "statements.json"

ATTRIBUTION = (
    "miniF2F (c) 2021 OpenAI, released under Apache License 2.0. Authors: "
    "Kunhao Zheng, Kudzo Ahegbebu, Stanislas Polu, David Renshaw, OpenAI "
    "GPT-f. Statement signatures extracted; proofs omitted. Pinned at "
    "commit 4e433ff5cadff23f9911a2bb5bbab2d351ce5554 "
    "(data_sources/derived/minif2f/NOTICE.md)."
)

PROVENANCE = [
    {
        "citation_key": "minif2f_openai2021",
        "bibliographic_entry": ATTRIBUTION,
        "url": "https://github.com/openai/miniF2F",
    }
]


def select_emitted() -> tuple[list[tuple[dict, str]], dict]:
    """Unique-covered miniF2F statements whose emitted template parses.

    Admission order mirrors `seed_lean_workbook.select_emitted` exactly so
    the two censuses are comparable: dedup on normalized goal, then
    `full_ok`, then emit.
    """
    extract = json.loads(EXTRACT.read_text(encoding="utf-8"))
    seen: set[str] = set()
    chosen: list[tuple[dict, str]] = []
    excluded: dict[str, int] = {}
    samples: dict[str, list[str]] = {}
    duplicates = 0
    considered = 0
    for stmt in extract["statements"]:
        key = " ".join(stmt["goal"].split())
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
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
    by_split: dict[str, int] = {}
    for stmt, _ in chosen:
        split = stmt.get("split", "unknown")
        by_split[split] = by_split.get(split, 0) + 1
    census = {
        "generated_by": "scripts/seed_minif2f.py emit census",
        "design": "docs/DESIGN-heldout-recovery.md",
        "role": "held-out A (small-N) — the emitter was not fitted to this source",
        "statements_in_extract": len(extract["statements"]),
        "duplicate_goals_dropped": duplicates,
        "unique_goals": len(seen),
        "unique_covered_considered": considered,
        "emitted": len(chosen),
        "excluded": sum(excluded.values()),
        "emitted_by_split": dict(sorted(by_split.items())),
        "excluded_by_reason": dict(
            sorted(excluded.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        "excluded_samples": samples,
        "emitter_widened": False,
    }
    return chosen, census


def node_from_emitted(stmt: dict, template: str) -> dict:
    name = stmt["name"]
    sid = "minif2f.skel." + name
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
        "title": f"{name} (miniF2F, Emitted Skeleton, Formal Without Bridge)",
        "statement_class": "proposition",
        "epistemic_status": "formal",
        "theory_context": {
            "disciplines": ["mathematics"],
            "subfield": "competition_problem",
            "topic": "ingested_minif2f",
        },
        "formal_statement": {
            "canonical_ascii": surface,
            "canonical_latex": surface,
            "equivalent_forms": [
                {
                    "form_id": "emitted_skeleton",
                    "notation_system": "ascii",
                    "expression": template,
                    "scope_note": "Matcher template emitted from the pinned miniF2F extract.",
                }
            ],
        },
        "structural_signature": {
            "archetype_id": "ingested_emitted_skeleton",
            "anonymized_template": template,
            "slot_schema": slots,
            "invariants": [
                "Emitted from Lean surface by scripts/emit_skeleton.py, unwidened.",
                "NODE-LEVEL RECORD: formal without a verified_by bridge. The "
                "miniF2F reference proof is not re-checked under this repo's "
                "hermetic core-Lean budget. epistemic_status formal records "
                "provenance, not a certificate.",
                "HELD-OUT A of docs/DESIGN-heldout-recovery.md. The emitter "
                "was fitted to Lean-workbook, not to this source.",
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
                f"The covered miniF2F competition claim stated by problem "
                f"{name}, emitted as a matcher template "
                f"(docs/DESIGN-skeleton-emitter.md)."
            ),
            "statistical_significance": (
                "Held-out A of the structure-recovery design: unique-covered "
                "miniF2F statements whose Lean surface emits a parse-clean "
                "matcher template through the unwidened emitter. "
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
        "keywords": ["ingested", "minif2f", "competition", "emitted skeleton",
                     "formal without bridge", "held-out"],
    }


def main() -> None:
    emitted, census = select_emitted()
    nodes = [node_from_emitted(stmt, tmpl) for stmt, tmpl in emitted]
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "minif2f.skel.v1",
        "discipline": "minif2f",
        "version": "1.0.0-alpha",
        "statement_nodes": nodes,
    }
    out = Path("data_holdout") / "minif2f" / "nodes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(
        (json.dumps(corpus, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    )
    census_path = Path("experiments") / "minif2f_emit.json"
    gc.write_json(census_path, census)
    print(
        f"wrote {out} ({len(nodes)} emitted nodes); census {census_path} "
        f"(considered {census['unique_covered_considered']}, "
        f"excluded {census['excluded']})"
    )


if __name__ == "__main__":
    main()
