#!/usr/bin/env python3
"""Seed data_holdout/goedel_pset/nodes.json — held-out B of
docs/DESIGN-heldout-recovery.md.

The scale test. Held-out A (miniF2F, 157 nodes) sits at exactly the size
where v0.11's own curve was still *below* its null, so A can probe the sign
flip and cannot test compounding. B is drawn large enough to sit above the
N=128 point where Lean-workbook's curve changed sign.

Reads the committed seeded sample at
`data_sources/derived/goedel_pset/sample.json` and authors it through the
SAME unwidened emitter that produced Lean-workbook's 12,514 templates and
miniF2F's 157. **The emitter is not widened for this source.** Refusals are
counted in `experiments/goedel_pset_emit.json`.

## Quarantined, like every holdout

Writes to `data_holdout/`, not `data/`, per
[docs/DESIGN-holdout-quarantine.md](../docs/DESIGN-holdout-quarantine.md).
A holdout committed into the merged graph is not held out: authoring
miniF2F into `data/` moved the published v0.11 channel split under every
discipline label available. B needs the rule more than A did — 2,048
ingested nodes would move the external share further than 157 could.

## No archive required

The 789 MB of pinned parquets are gitignored and are read only by
`scripts/sample_goedel_pset.py`, which runs once and commits the sample.
This seed needs nothing but that committed file, so
`check_regeneration.py` — which runs every `seed_*.py` — works in a clone
that has never fetched the source. See sample_goedel_pset.py's docstring
for why that split exists (short version: v0.11's WOLD reach ledger).

## Registered predictions (written before the sample was drawn)

Priors, same emitter: Lean-workbook 12,514/12,637 = **99.03%**; miniF2F
157/160 = **98.12%**. Goedel-Pset is machine-formalized from NuminaMath by
a prover rather than written by hand, and its proofs are `sorry`, so it is
a genuinely different surface.

- **B1 (emit rate).** >= 90% of the sampled unique-covered statements emit
  a parse-clean template through the unwidened emitter.
  **FIRED — 92.58%** (1,896 of 2,048). It fired, and the trend inside it
  is the interesting part: 99.03% (Lean-workbook, fitted) -> 98.12%
  (miniF2F) -> 92.58% (Goedel-Pset). The emitter is measurably worse the
  further it gets from the source it was built on, which is what a
  held-out is for.
- **B2 (draw efficiency).** Reaching the 2,048 target needs fewer than
  2,500 candidates. **ILL-POSED — not tested.** The design forbids
  topping the draw up ("counted, not padded"), so exactly 2,048 candidates
  were drawn and 1,896 authored; nobody ever went looking for a 2,048th
  authored node. The implied figure is 2,048 / 0.9258 = ~2,212 candidates,
  which would have satisfied the prediction, but that is arithmetic, not a
  measurement. The prediction contradicted the design it was written under
  and should not have been registered in this form.
- **B3 (exclusion shape).** Exclusions are dominated by `emit:` refusals
  rather than `parse_fail`, as in both priors (Lean-workbook 69 vs 54,
  miniF2F 2 vs 1). **MISSED, and decisively: parse_fail 114 vs emit: 38**,
  a 3:1 inversion. B is the first sample large enough to test this and it
  broke the pattern immediately. See `parse_fail_attribution` in the
  census: 101 of the 114 (88.6%) carry one unrewritten name, `Real.pi`,
  into the emitted template, which the matcher then declines to re-parse.
  So the miss has a single named cause rather than being diffuse.
- **B4 (regime).** The authored count is >= 512, so B sits above the
  N=128 sign-flip point and can test H1 (scale), not merely H2 (the flip).
  **FIRED — 1,896**, comfortably above.

Not padded. Design §3: "target 2,048, or whatever the emitter actually
emits — counted, not padded."

## The finding this authoring produced, and what is NOT done about it

66% of all exclusions (101 of 152) come from a single unmapped nullary
constant. The coverage instrument admits these statements — `π` is in its
allowed glyph set — while the emitter cannot round-trip them, so
**coverage overstates what is authorable on this source**. That gap did
not show on Lean-workbook or miniF2F at a size where it was visible.

Mapping `Real.pi` is deliberately NOT done here. Design §3: "The emitter
is not widened for these sources; exclusions are counted." Widening the
emitter while authoring a holdout is how the holdout stops being one. The
lever is now named and sized for whoever decides it later: ~101 nodes,
92.58% -> ~97.5%, and the decision owes its own prediction.

## Not a verified corpus

Goedel-Pset proofs are `sorry`. These nodes are formal-without-bridge, and
`verified_by` is absent by construction — a Goedel-Pset node that cited
`verified_by` without a PASS is exactly the case v0.12 item 4's rule exists
to refuse.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import grammar_coverage as gc  # noqa: E402
import emit_skeleton as emit  # noqa: E402

SAMPLE = REPO / "data_sources" / "derived" / "goedel_pset" / "sample.json"

# A dotted Lean name (`Real.pi`) that survived head rewriting into the emitted
# template. The matcher's tokenizer has no rule for it, so the template does
# not round-trip and the statement is excluded as `parse_fail`. Attributing
# those exclusions to the specific surviving name is the difference between
# "114 refusals" and "one unmapped constant costs us 101 nodes".
_DOTTED_NAME = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_.]*")


def _provenance(src: dict) -> list[dict]:
    return [
        {
            "citation_key": "goedel_pset_v1",
            "bibliographic_entry": src["attribution"],
            "url": src["url"],
        }
    ]


def select_emitted() -> tuple[list[tuple[dict, str]], dict, dict]:
    """Author every sampled statement the unwidened emitter accepts."""
    doc = json.loads(SAMPLE.read_text(encoding="utf-8"))
    chosen: list[tuple[dict, str]] = []
    excluded: dict[str, int] = {}
    samples: dict[str, list[str]] = {}
    survivors: Counter = Counter()
    parse_fail_unexplained: list[str] = []
    n_explained = 0
    n_unexplained = 0
    for stmt in doc["statements"]:
        template, reason = emit.emit_or_reason(stmt)
        if template is None:
            why = reason or "unknown"
            excluded[why] = excluded.get(why, 0) + 1
            bucket = samples.setdefault(why, [])
            if len(bucket) < 5:
                bucket.append(f"{stmt['name']}: {stmt['goal'][:160]}")
            if why == "parse_fail":
                try:
                    rendered = emit.emit_statement(stmt)
                except emit.EmitError:
                    rendered = ""
                hits = set(_DOTTED_NAME.findall(rendered))
                for h in hits:
                    survivors[h] += 1
                if hits:
                    n_explained += 1
                else:
                    n_unexplained += 1
                    if len(parse_fail_unexplained) < 10:
                        parse_fail_unexplained.append(
                            f"{stmt['name']}: {rendered[:140]}"
                        )
            continue
        chosen.append((stmt, template))
    considered = len(doc["statements"])
    n_parse_fail = excluded.get("parse_fail", 0)
    census = {
        "generated_by": "scripts/seed_goedel_pset.py emit census",
        "design": "docs/DESIGN-heldout-recovery.md",
        "role": "held-out B (scale) — the emitter was not fitted to this source",
        "sample": {
            "path": "data_sources/derived/goedel_pset/sample.json",
            "seed": doc["selection"]["seed"],
            "target": doc["selection"]["target"],
            "unique_covered_available": doc["selection"]["unique_covered_available"],
            "rows_scanned": doc["selection"]["rows_scanned"],
        },
        "considered": considered,
        "emitted": len(chosen),
        "excluded": sum(excluded.values()),
        "emit_rate_pct": round(100.0 * len(chosen) / considered, 2) if considered else 0.0,
        "excluded_by_reason": dict(
            sorted(excluded.items(), key=lambda kv: (-kv[1], kv[0]))
        ),
        "excluded_samples": samples,
        "parse_fail_attribution": {
            "note": "A `parse_fail` means the emitter produced a string the "
                    "matcher then refused to re-parse. Where an unrewritten "
                    "dotted Lean name survived into that string, it is named "
                    "here. This is diagnosis, NOT a licence to widen: design "
                    "§3 forbids widening the emitter for a held-out source.",
            "parse_fail_total": n_parse_fail,
            "explained_by_surviving_dotted_name": n_explained,
            "unexplained": n_unexplained,
            "surviving_names": dict(
                sorted(survivors.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
            "unexplained_samples": parse_fail_unexplained,
        },
        "emitter_widened": False,
    }
    return chosen, census, doc["source"]


def _sid_slug(name: str) -> str:
    """`Goedel-Pset-999539` -> `goedel_pset_999539`.

    The schema pins statement ids to `^[a-z0-9]+(\\.[a-z0-9_]+)+$`; upstream
    ids carry capitals and hyphens. miniF2F needed no slug because its names
    were already lowercase-with-underscores. The upstream name is preserved
    verbatim in the title and in `semantic_interpretation`, so the mapping
    back to the source row stays readable; only the id is normalized, and
    the numeric suffix keeps it injective.
    """
    return re.sub(r"[^a-z0-9_]", "_", name.lower())


def node_from_emitted(stmt: dict, template: str, provenance: list[dict]) -> dict:
    name = stmt["name"]
    sid = "goedelpset.skel." + _sid_slug(name)
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
        "title": f"{name} (Goedel-Pset, Emitted Skeleton, Formal Without Bridge)",
        "statement_class": "proposition",
        "epistemic_status": "formal",
        "theory_context": {
            "disciplines": ["mathematics"],
            "subfield": "formalized_word_problem",
            "topic": "ingested_goedel_pset",
        },
        "formal_statement": {
            "canonical_ascii": surface,
            "canonical_latex": surface,
            "equivalent_forms": [
                {
                    "form_id": "emitted_skeleton",
                    "notation_system": "ascii",
                    "expression": template,
                    "scope_note": "Matcher template emitted from the pinned Goedel-Pset sample.",
                }
            ],
        },
        "structural_signature": {
            "archetype_id": "ingested_emitted_skeleton",
            "anonymized_template": template,
            "slot_schema": slots,
            "invariants": [
                "Emitted from Lean surface by scripts/emit_skeleton.py, unwidened.",
                "NODE-LEVEL RECORD: formal without a verified_by bridge. "
                "Goedel-Pset proofs are `sorry` — there is no proof to bridge "
                "to, so epistemic_status formal records provenance only.",
                "HELD-OUT B of docs/DESIGN-heldout-recovery.md. The emitter "
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
                f"The covered Goedel-Pset claim stated by problem {name}, "
                f"emitted as a matcher template "
                f"(docs/DESIGN-skeleton-emitter.md)."
            ),
            "statistical_significance": (
                "Held-out B of the structure-recovery design: a seeded sample "
                "of unique-covered Goedel-Pset statements whose Lean surface "
                "emits a parse-clean matcher template through the unwidened "
                "emitter. formal-without-bridge."
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
        "provenance": provenance,
        "keywords": ["ingested", "goedel pset", "formalized word problem",
                     "emitted skeleton", "formal without bridge", "held-out"],
    }


def main() -> None:
    if not SAMPLE.exists():
        print(
            f"MISSING sample: {gc.rel(SAMPLE)}. Draw it first (needs the "
            "pinned parquets, once):\n"
            "  python scripts/fetch_sources.py --fetch hf-goedel-pset-v1\n"
            "  python scripts/sample_goedel_pset.py",
            file=sys.stderr,
        )
        raise SystemExit(2)
    emitted, census, src = select_emitted()
    provenance = _provenance(src)
    nodes = [node_from_emitted(s, t, provenance) for s, t in emitted]
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "goedel_pset.skel.v1",
        "discipline": "goedel_pset",
        "version": "1.0.0-alpha",
        "statement_nodes": nodes,
    }
    out = Path("data_holdout") / "goedel_pset" / "nodes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(
        (json.dumps(corpus, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    )
    census_path = Path("experiments") / "goedel_pset_emit.json"
    gc.write_json(census_path, census)
    print(
        f"wrote {out} ({len(nodes)} emitted nodes); census {census_path} "
        f"(considered {census['considered']}, excluded {census['excluded']}, "
        f"emit rate {census['emit_rate_pct']}%)"
    )


if __name__ == "__main__":
    main()
