#!/usr/bin/env python3
"""Held-out structure recovery — H1–H6 of docs/DESIGN-heldout-recovery.md.

The v0.11 curve asked whether an ingested layer's parts start having owners
inside that same layer, and found a shape nobody predicted: below a
distribution-matched null at N=8 and N=32, above it from N=128. That was
measured on Lean-workbook, the source the emitter was built for. This script
asks the same question of two sources the emitter was **not** fitted to.

This is the "thin sibling that pins the holdout id set" the design's §4
sanctions. It does not modify `measure_self_grounding.py`, whose output is a
committed v0.11 artifact; it imports that module's scoring so the two curves
are the same measurement, not two implementations of one description.

## What "held out" means operationally

Route 1, owner identity, exactly as v0.11:

- The **holdout layer** is one quarantined corpus from `data_holdout/`.
  `ISG` counts a constituent when its most-independent owner is another
  statement *from that same holdout*.
- Everything in `data/` — including the 12,514 Lean-workbook templates — is
  the **fixed, curated-relative layer** (design §4). A Lean-workbook owner
  is an XSG owner here. Letting the 12k layer count as ingested would let it
  gift the holdout a curve, which is the failure the design names first.
- The **other holdout is excluded entirely.** Whether A and B may be loaded
  together is explicitly unsettled (DESIGN-holdout-quarantine.md §5) and
  would need its own null and its own prediction. One holdout per run.

## The null

`observed_inventory` over the *holdout's own* trees, then structurally-random
statements drawn from that inventory and attached to the same fixed layer.
So the null is distribution-matched to the holdout, not to Lean-workbook.

`generate_synthetic` hardcodes a `lean_workbook.null.*` corpus label. That
label is relabelled here to the holdout's own corpus id before attachment,
so that `owner_channel` sees the same same-corpus/prior-corpus geometry for
the null layer as for the real one. Relabelling in this sibling rather than
parameterising the v0.11 generator keeps that committed artifact untouched.

## The capability-blind baseline (H3)

Two holdout statements "ground" one another iff they share the operator-bag
glyph set `{+,-,*,/,^,=}` — the same bag item 2 already used. Its rate is
co-occurrence over bags, never over attributed owners.

The baseline reads `anonymized_template` **straight from the corpus JSON**
and never touches an `analyze_loaded` result. That is deliberate: the design
forbids it from reading `owners`, `owner_channels`, or any decompose field,
and the cheapest way to guarantee a program cannot read a field is to never
hand it the object. Its null is the synthetic templates at the same sizes
and seeds.

## Predictions

H1–H6 are frozen in §5 of the design and are NOT edited to match the
outcome. `adjudicate_heldout` below is closed-form over the computed rows.
Fired and missed are both first-class results.

Usage (repo root, PYTHONIOENCODING=utf-8 on Windows):

    python scripts/measure_heldout_recovery.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from decompose import analyze_loaded, attach_extra, load_trees  # noqa: E402
from measure_self_grounding import (  # noqa: E402
    _spread,
    generate_synthetic,
    observed_inventory,
    score_entries,
    subsample,
)

DEFAULT_OUT = REPO / "experiments" / "heldout_recovery.json"
DATA = REPO / "data"
HOLDOUT_ROOT = REPO / "data_holdout"

SELECTION_SEED = 20260816
NULL_SEEDS = (0, 1, 2)
SCHEMA = "heldout_recovery.v1"

# Held-out A is the small-N test; its whole point is to sit where a real
# curve can look like chance, so it gets the two small sizes and `all`.
# Held-out B is the scale test and spans the v0.11 sign-flip point.
HOLDOUTS: dict[str, dict] = {
    "minif2f": {
        "corpus_prefix": "minif2f",
        "role": "held-out A (small-N)",
        "sizes": (8, 32),
    },
    "goedel_pset": {
        "corpus_prefix": "goedel_pset",
        "role": "held-out B (scale)",
        "sizes": (8, 32, 128, 512),
    },
}

GLYPH_RE = re.compile(r"[+\-*/^=]")


# --------------------------------------------------------------------------
# capability-blind bag baseline
# --------------------------------------------------------------------------


def bag_key(template: str) -> frozenset[str]:
    return frozenset(GLYPH_RE.findall(template or ""))


def bag_cooccurrence_rate(templates: list[str]) -> float | None:
    """Fraction of statements whose glyph set is shared by >= 1 other.

    This is the bag's analogue of ISG: "does this statement have a partner
    in the layer?" answered without any notion of which subterm, which
    owner, or which channel. A single statement cannot co-occur with
    itself, so a layer of one scores 0.
    """
    if not templates:
        return None
    counts = Counter(bag_key(t) for t in templates)
    shared = sum(1 for t in templates if counts[bag_key(t)] > 1)
    return shared / len(templates)


def _templates_from_corpus(path: Path) -> dict[str, str]:
    """statement_id -> anonymized_template, read from the corpus file only."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {
        n["statement_id"]: n["structural_signature"]["anonymized_template"]
        for n in doc["statement_nodes"]
    }


# --------------------------------------------------------------------------
# curve
# --------------------------------------------------------------------------


def measure_holdout(
    name: str,
    spec: dict,
    *,
    selection_seed: int = SELECTION_SEED,
    null_seeds: tuple[int, ...] = NULL_SEEDS,
    min_family: int = 2,
) -> dict:
    fixed_nodes, fixed_trees, fixed_classes, fixed_corpus, fixed_disc = load_trees(DATA)
    hold_path = HOLDOUT_ROOT / name / "nodes.json"
    h_nodes, h_trees, h_classes, h_corpus, h_disc = load_trees(HOLDOUT_ROOT)

    prefix = spec["corpus_prefix"]
    holdout_ids = [
        n.statement_id for n in h_nodes
        if h_corpus.get(n.statement_id, "").startswith(prefix)
    ]
    if not holdout_ids:
        raise SystemExit(f"no nodes for holdout {name!r} under {HOLDOUT_ROOT}")
    holdout_corpus_id = h_corpus[holdout_ids[0]]
    by_id = {n.statement_id: n for n in h_nodes}
    templates = _templates_from_corpus(hold_path)

    inventory = observed_inventory(holdout_ids, h_trees, h_disc, h_corpus)
    n_all = len(holdout_ids)
    ns = [n for n in spec["sizes"] if n < n_all] + [n_all]

    def analyze_with(extra_ids: list[str]) -> tuple[dict, dict, dict]:
        nodes = list(fixed_nodes) + [by_id[s] for s in extra_ids]
        keep = {n.statement_id for n in nodes}
        trees = {s: (fixed_trees[s] if s in fixed_trees else h_trees[s])
                 for s in keep if s in fixed_trees or s in h_trees}
        classes = {s: (fixed_classes[s] if s in fixed_classes else h_classes[s])
                   for s in keep if s in fixed_classes or s in h_classes}
        corpus_of = {s: (fixed_corpus[s] if s in fixed_corpus else h_corpus[s])
                     for s in keep}
        disc_of = {s: (fixed_disc[s] if s in fixed_disc else h_disc[s])
                   for s in keep}
        nodes = [n for n in nodes if n.statement_id in trees]
        result = analyze_loaded(
            nodes, trees, classes, corpus_of, disc_of,
            min_family=min_family, pattern_membership=False,
        )
        return result, corpus_of, disc_of

    def analyze_null(synths: list[dict]) -> tuple[dict, dict, dict]:
        nodes = list(fixed_nodes)
        trees = dict(fixed_trees)
        classes = {k: dict(v) for k, v in fixed_classes.items()}
        corpus_of = dict(fixed_corpus)
        disc_of = dict(fixed_disc)
        attach_extra(nodes, trees, classes, corpus_of, disc_of, synths)
        result = analyze_loaded(
            nodes, trees, classes, corpus_of, disc_of,
            min_family=min_family, pattern_membership=False,
        )
        return result, corpus_of, disc_of

    points = []
    for n in ns:
        chosen = subsample(holdout_ids, n, selection_seed)
        chosen_set = set(chosen)
        real_result, real_corpus, real_disc = analyze_with(chosen)
        real_score = score_entries(
            real_result["decompositions"], chosen_set, real_corpus, real_disc)
        top = real_score["most_common_subterm"]
        drop = top["skeleton"] if top else None
        bag_real = bag_cooccurrence_rate([templates[s] for s in chosen])

        null_rows, s4_null_rows, bag_null_rows = [], [], []
        for seed in null_seeds:
            synths = generate_synthetic(n, inventory, seed)
            # Relabel so the null layer has the holdout's corpus geometry.
            for s in synths:
                s["corpus_id"] = f"{holdout_corpus_id}.null"
                s["discipline"] = f"{name}_null"
            synth_ids = {s["statement_id"] for s in synths}
            null_result, null_corpus, null_disc = analyze_null(synths)
            null_rows.append({
                "seed": seed,
                **score_entries(null_result["decompositions"], synth_ids,
                                null_corpus, null_disc),
            })
            s4_null_rows.append({
                "seed": seed,
                **score_entries(null_result["decompositions"], synth_ids,
                                null_corpus, null_disc, drop_skeleton=drop),
            })
            bag_null_rows.append({
                "seed": seed,
                "bag_rate": bag_cooccurrence_rate([s["template"] for s in synths]),
            })

        s4_real = score_entries(
            real_result["decompositions"], chosen_set, real_corpus, real_disc,
            drop_skeleton=drop)

        points.append({
            "n": n,
            "selection_seed": selection_seed,
            "real": real_score,
            "null": null_rows,
            "s4": {"dropped_skeleton": drop, "real": s4_real, "null": s4_null_rows},
            "bag_baseline": {
                "real_rate": bag_real,
                "null": bag_null_rows,
                "reads": "anonymized_template only; never an analyze_loaded field",
            },
        })

    return {
        "holdout": name,
        "role": spec["role"],
        "corpus_id": holdout_corpus_id,
        "holdout_layer": n_all,
        "fixed_layer": len(fixed_nodes),
        "fixed_layer_note": (
            "everything in data/, including the 12,514 Lean-workbook "
            "templates, is curated-relative to this holdout (design §4)"
        ),
        "other_holdout_loaded": False,
        "selection_seed": selection_seed,
        "null_seeds": list(null_seeds),
        "min_family": min_family,
        "pattern_membership": False,
        "points": points,
    }


# --------------------------------------------------------------------------
# H1–H6, closed form over the rows
# --------------------------------------------------------------------------


def _null_rates(point: dict) -> list[float]:
    return [float(r["isg_rate"]) for r in point["null"]
            if r["isg_rate"] is not None]


def _gap(point: dict) -> float | None:
    if point["real"]["isg_rate"] is None:
        return None
    rates = _null_rates(point)
    if not rates:
        return None
    return float(point["real"]["isg_rate"]) - sum(rates) / len(rates)


def adjudicate_heldout(curves: dict[str, dict]) -> dict:
    """H1–H6 exactly as written in DESIGN-heldout-recovery.md §5."""
    out: dict = {}
    b = curves.get("goedel_pset")

    # H1 — scale, held-out B: same predicate as S1, new source.
    if b:
        big = b["points"][-1]
        rates = _null_rates(big)
        mean = sum(rates) / len(rates)
        spread = _spread(rates)
        real = float(big["real"]["isg_rate"])
        out["H1"] = {
            "fired": real > mean and (real - mean) > spread,
            "n": big["n"],
            "isg_real": real,
            "isg_null_mean": mean,
            "isg_null_spread": spread,
            "gap": real - mean,
            "predicate": "isg_real > null_mean and gap > null spread",
        }

    # H2 — sign flip: at N=8 and N=32, real <= null on AT LEAST ONE holdout.
    h2_rows = []
    for name, curve in curves.items():
        for point in curve["points"]:
            if point["n"] in (8, 32):
                g = _gap(point)
                h2_rows.append({"holdout": name, "n": point["n"], "gap": g,
                                "real_at_or_below_null": g is not None and g <= 0})
    out["H2"] = {
        "fired": any(r["real_at_or_below_null"] for r in h2_rows),
        "rows": h2_rows,
        "predicate": "on >=1 holdout, gap <= 0 at N=8 or N=32",
    }

    # H3 — the keyword bag cannot steal the gap, held-out B at largest N.
    if b and "H1" in out:
        big = b["points"][-1]
        bag_real = big["bag_baseline"]["real_rate"]
        bag_nulls = [r["bag_rate"] for r in big["bag_baseline"]["null"]
                     if r["bag_rate"] is not None]
        bag_mean = sum(bag_nulls) / len(bag_nulls) if bag_nulls else None
        bag_gap = None if (bag_real is None or bag_mean is None) else bag_real - bag_mean
        owner_gap = out["H1"]["gap"]
        owner_spread = out["H1"]["isg_null_spread"]
        fired = bag_gap is not None and (
            bag_gap <= 0 or (owner_gap - bag_gap) > owner_spread
        )
        out["H3"] = {
            "fired": fired,
            "n": big["n"],
            "bag_real": bag_real,
            "bag_null_mean": bag_mean,
            "bag_gap": bag_gap,
            "owner_gap": owner_gap,
            "owner_null_spread": owner_spread,
            "predicate": "bag_gap <= 0, or (owner_gap - bag_gap) > owner null spread",
        }

    # H4 — the proxy is not ISG, both holdouts at largest N.
    h4_rows = []
    for name, curve in curves.items():
        big = curve["points"][-1]
        delta = big["real"].get("proxy_minus_isg_of_grounded")
        h4_rows.append({"holdout": name, "n": big["n"],
                        "proxy_rate": big["real"].get("proxy_rate"),
                        "isg_of_grounded": big["real"].get("isg_of_grounded"),
                        "proxy_minus_isg_of_grounded": delta,
                        "above_0_2": delta is not None and delta > 0.2})
    out["H4"] = {
        "fired": bool(h4_rows) and all(r["above_0_2"] for r in h4_rows),
        "rows": h4_rows,
        "predicate": "proxy - isg_of_grounded > 0.2 on BOTH holdouts",
    }

    # H5 — S4-style, held-out B: does H1 survive dropping the top subterm?
    if b and "H1" in out:
        big = b["points"][-1]
        s4_real = big["s4"]["real"]["isg_rate"]
        s4_nulls = [float(r["isg_rate"]) for r in big["s4"]["null"]
                    if r["isg_rate"] is not None]
        s4_mean = sum(s4_nulls) / len(s4_nulls) if s4_nulls else None
        s4_spread = _spread(s4_nulls) if s4_nulls else None
        survives = (
            s4_real is not None and s4_mean is not None
            and s4_real > s4_mean and (s4_real - s4_mean) > s4_spread
        )
        out["H5"] = {
            "fired": bool(survives),
            "n": big["n"],
            "dropped_skeleton": big["s4"]["dropped_skeleton"],
            "isg_real_after_drop": s4_real,
            "isg_null_mean_after_drop": s4_mean,
            "gap_after_drop": (None if (s4_real is None or s4_mean is None)
                               else s4_real - s4_mean),
            "gap_before_drop": out["H1"]["gap"],
            "direction_not_predicted": True,
            "predicate": "H1's predicate still holds with the top subterm removed",
        }

    # H6 — XSG does not fall by as much as ISG rises, N=8 -> N_max, holdout B.
    if b and len(b["points"]) >= 2:
        first, last = b["points"][0], b["points"][-1]
        isg_rise = (float(last["real"]["isg_rate"]) - float(first["real"]["isg_rate"]))
        xsg_fall = (float(first["real"]["xsg_rate"]) - float(last["real"]["xsg_rate"]))
        out["H6"] = {
            "fired": xsg_fall < isg_rise,
            "n_from": first["n"], "n_to": last["n"],
            "isg_rise": isg_rise, "xsg_fall": xsg_fall,
            "predicate": "xsg_fall < isg_rise",
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--only", nargs="*", default=None,
                    help="restrict to named holdouts")
    args = ap.parse_args()

    names = args.only or list(HOLDOUTS)
    curves: dict[str, dict] = {}
    for name in names:
        print(f"[measure] {name} ...", flush=True)
        curves[name] = measure_holdout(name, HOLDOUTS[name])
        pts = [(p["n"], p["real"]["isg_rate"]) for p in curves[name]["points"]]
        print(f"[measure] {name} points: {pts}", flush=True)

    result = {
        "schema": SCHEMA,
        "design": "docs/DESIGN-heldout-recovery.md",
        "route": 1,
        "proxy_is": "control",
        "passes": ["decompose.analyze_loaded"],
        "not_run": ["specialize.py"],
        "curves": curves,
        "adjudication": adjudicate_heldout(curves),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(args.out),
        "adjudication": {
            k: {"fired": v["fired"]} for k, v in result["adjudication"].items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
