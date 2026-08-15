#!/usr/bin/env python3
"""Capability-blind operator-bag baseline vs typed-skeleton matcher.

docs/DESIGN-item4-authoring.md §3–§4 (P3) and docs/DESIGN-fair-fight.md
(ROADMAP-v0.11 item 2). Two statements are a bag-pair iff they use the
same set of surface glyphs {+,-,*,/,^,=}. The matcher pairs by typed
skeleton.

Figure of merit (registered before the 12,771-node re-run): bag
precision against typed twins. Matcher recall-against-the-bag is the
companion number 1 − k/|matcher|, with every print-convention miss
named. Pair sets are counted, not materialised.

Registered predictions (docs/DESIGN-fair-fight.md §3):

FF1  Bag precision on the full graph is strictly below the 508-node
     combined figure (0.0126).
FF2  Matcher precision against the bag is 1 − k/|matcher| with k a
     named print-convention count, not a silent 1.0.
FF3  The pair sets still almost nest: bag recall against the matcher
     equals matcher precision against the bag.
FF4  A committed-seed size-matched bag draw at k = |matcher| lands
     within 3× Bernoulli SE of bag precision.
FF5  Ingested-only bag precision is lower than curated-only.

The bag is not retuned. Glyphs stay {+,-,*,/,^,=}.
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from match_signatures import build_report, load_nodes  # noqa: E402

GLYPH_RE = re.compile(r"[+\-*/^=]")
DEFAULT_OUT = REPO / "experiments" / "item4_operator_bag.json"
DRAW_SEED = 20260814
PRIOR_COMBINED_PRECISION = 0.0126
INGESTED_DISCIPLINES = {"lean_workbook", "ingested_arithmetic"}
SCHEMA = "item4_operator_bag.v2"
MISS_LIST_CAP = 100


def comb2(n: int) -> int:
    return n * (n - 1) // 2 if n >= 2 else 0


def pairs_from_groups(groups: list[dict], allowed: set[str] | None = None) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for group in groups:
        ids = [m["statement_id"] for m in group["members"]]
        if allowed is not None:
            ids = [i for i in ids if i in allowed]
        if len(ids) > 1:
            out.update(combinations(sorted(ids), 2))
    return out


def bag_pairs(nodes, allowed: set[str] | None = None) -> set[tuple[str, str]]:
    bags: dict[frozenset[str], list[str]] = defaultdict(list)
    for node in nodes:
        if allowed is not None and node.statement_id not in allowed:
            continue
        bags[frozenset(GLYPH_RE.findall(node.template))].append(node.statement_id)
    out: set[tuple[str, str]] = set()
    for ids in bags.values():
        if len(ids) > 1:
            out.update(combinations(sorted(ids), 2))
    return out


def score_counts(pred_n: int, ref_n: int, intersection: int) -> dict[str, float | int]:
    return {
        "pairs": pred_n,
        "precision": (intersection / pred_n) if pred_n else float("nan"),
        "recall": (intersection / ref_n) if ref_n else float("nan"),
    }


def _glyphs(template: str) -> frozenset[str]:
    return frozenset(GLYPH_RE.findall(template))


def _matched_draw(
    bags: dict[frozenset[str], list[str]],
    typed_of: dict[str, int],
    k: int,
    seed: int,
) -> dict:
    groups = [(glyph, ids) for glyph, ids in bags.items() if len(ids) >= 2]
    weights = [comb2(len(ids)) for _, ids in groups]
    total = sum(weights)
    if total == 0 or k == 0:
        return {
            "drawn": 0, "twins": 0, "precision": None,
            "exhaustive": True, "seed": seed,
        }
    if k >= total:
        twins = 0
        for _, ids in groups:
            by_typed: dict[int | None, int] = defaultdict(int)
            for sid in ids:
                by_typed[typed_of.get(sid)] += 1
            for key, count in by_typed.items():
                if key is not None:
                    twins += comb2(count)
        return {
            "drawn": total, "twins": twins,
            "precision": twins / total if total else None,
            "exhaustive": True, "seed": seed,
        }
    rng = random.Random(seed)
    twins = 0
    # rng.choices on 12k tiny groups is fine; weights are pair-counts.
    index = list(range(len(groups)))
    for _ in range(k):
        gi = rng.choices(index, weights=weights, k=1)[0]
        a, b = rng.sample(groups[gi][1], 2)
        ta, tb = typed_of.get(a), typed_of.get(b)
        if ta is not None and ta == tb:
            twins += 1
    return {
        "drawn": k, "twins": twins, "precision": twins / k,
        "exhaustive": False, "seed": seed,
    }


def measure(data_dir: Path) -> dict:
    nodes, problems = load_nodes(data_dir)
    report = build_report(nodes, problems)
    ingested = {n.statement_id for n in nodes
                if n.discipline in INGESTED_DISCIPLINES}
    prior = {n.statement_id for n in nodes} - ingested
    typed = report["typed_twin_groups"]
    template_of = {n.statement_id: n.template for n in nodes}

    def block(allowed: set[str] | None) -> dict:
        matcher_n = 0
        intersection = 0
        only_matcher: list[list[str]] = []
        typed_of: dict[str, int] = {}
        for gi, group in enumerate(typed):
            ids = [m["statement_id"] for m in group["members"]]
            if allowed is not None:
                ids = [i for i in ids if i in allowed]
            if len(ids) < 2:
                continue
            for sid in ids:
                typed_of[sid] = gi
            by_glyph: dict[frozenset[str], list[str]] = defaultdict(list)
            for sid in ids:
                by_glyph[_glyphs(template_of[sid])].append(sid)
            matcher_n += comb2(len(ids))
            intersection += sum(comb2(len(members)) for members in by_glyph.values())
            if len(by_glyph) > 1 and len(only_matcher) < MISS_LIST_CAP:
                for a, b in combinations(sorted(ids), 2):
                    if _glyphs(template_of[a]) != _glyphs(template_of[b]):
                        only_matcher.append([a, b])
                        if len(only_matcher) >= MISS_LIST_CAP:
                            break

        bags: dict[frozenset[str], list[str]] = defaultdict(list)
        pool = nodes if allowed is None else [n for n in nodes if n.statement_id in allowed]
        for node in pool:
            bags[_glyphs(node.template)].append(node.statement_id)
        bag_n = sum(comb2(len(ids)) for ids in bags.values())
        k_miss = matcher_n - intersection
        draw = _matched_draw(bags, typed_of, matcher_n, DRAW_SEED)
        bag_precision = (intersection / bag_n) if bag_n else float("nan")
        se = None
        within = None
        if draw["precision"] is not None and bag_n and matcher_n:
            p = bag_precision
            se = math.sqrt(p * (1.0 - p) / matcher_n) if 0 <= p <= 1 else None
            if se is not None:
                within = abs(draw["precision"] - p) <= 3 * se + 1e-15
        return {
            "nodes": len(allowed) if allowed is not None else len(nodes),
            "matcher": score_counts(matcher_n, bag_n, intersection),
            "operator_bag": score_counts(bag_n, matcher_n, intersection),
            "intersection": intersection,
            "only_matcher": k_miss,
            "only_matcher_pairs": only_matcher,
            "only_bag": bag_n - intersection,
            "figure_of_merit": bag_precision,
            "size_matched_draw": draw,
            "draw_se": se,
            "draw_within_3se": within,
        }

    all_block = block(None)
    prior_block = block(prior)
    ingested_block = block(ingested)
    adj = {
        "FF1": {
            "fired": all_block["figure_of_merit"] < PRIOR_COMBINED_PRECISION,
            "bag_precision": all_block["figure_of_merit"],
            "prior_combined": PRIOR_COMBINED_PRECISION,
        },
        "FF2": {
            "fired": all_block["only_matcher"] >= 1,
            "k": all_block["only_matcher"],
            "matcher_pairs": all_block["matcher"]["pairs"],
            "named_pairs": all_block["only_matcher_pairs"],
        },
        "FF3": {
            "fired": (
                all_block["operator_bag"]["recall"]
                == all_block["matcher"]["precision"]
            ),
            "bag_recall_vs_matcher": all_block["operator_bag"]["recall"],
            "matcher_precision_vs_bag": all_block["matcher"]["precision"],
        },
        "FF4": {
            "fired": bool(all_block["draw_within_3se"]),
            "draw": all_block["size_matched_draw"],
            "se": all_block["draw_se"],
        },
        "FF5": {
            "fired": (
                ingested_block["figure_of_merit"]
                < prior_block["figure_of_merit"]
            ),
            "ingested": ingested_block["figure_of_merit"],
            "curated": prior_block["figure_of_merit"],
        },
    }
    return {
        "schema": SCHEMA,
        "glyphs": ["+", "-", "*", "/", "^", "="],
        "figure_of_merit": "operator_bag.precision against typed twins",
        "design": "docs/DESIGN-fair-fight.md",
        "parse_problems": len(problems),
        "all": all_block,
        "prior": prior_block,
        "ingested": ingested_block,
        "group_counts": report["group_counts"],
        "nodes_analyzed": report["nodes_analyzed"],
        "adjudication": adj,
    }


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    result = measure(REPO / "data")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(out),
        "nodes_analyzed": result["nodes_analyzed"],
        "figure_of_merit": result["all"]["figure_of_merit"],
        "adjudication": {
            name: {"fired": block["fired"]}
            for name, block in result["adjudication"].items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
