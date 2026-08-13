#!/usr/bin/env python3
"""Capability-blind operator-bag baseline vs typed-skeleton matcher.

docs/DESIGN-item4-authoring.md §3–§4 (P3). Two statements are a bag-pair
iff they use the same set of surface glyphs {+,-,*,/,^,=}. The matcher
pairs by typed skeleton. Precision and recall are reported both ways.
"""

from __future__ import annotations

import json
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


def score(pred: set, ref: set) -> dict[str, float | int]:
    tp = pred & ref
    return {
        "pairs": len(pred),
        "precision": (len(tp) / len(pred)) if pred else float("nan"),
        "recall": (len(tp) / len(ref)) if ref else float("nan"),
    }


def measure(data_dir: Path) -> dict:
    nodes, problems = load_nodes(data_dir)
    report = build_report(nodes, problems)
    ingested = {n.statement_id for n in nodes if n.discipline == "lean_workbook"}
    prior = {n.statement_id for n in nodes} - ingested
    typed = report["typed_twin_groups"]

    def block(allowed: set[str] | None) -> dict:
        matcher = pairs_from_groups(typed, allowed)
        bag = bag_pairs(nodes, allowed)
        return {
            "nodes": len(allowed) if allowed is not None else len(nodes),
            "matcher": score(matcher, bag),
            "operator_bag": score(bag, matcher),
            "intersection": len(matcher & bag),
            "only_matcher": len(matcher - bag),
            "only_bag": len(bag - matcher),
        }

    return {
        "schema": "item4_operator_bag.v1",
        "glyphs": ["+", "-", "*", "/", "^", "="],
        "parse_problems": len(problems),
        "all": block(None),
        "prior": block(prior),
        "ingested": block(ingested),
        "group_counts": report["group_counts"],
        "nodes_analyzed": report["nodes_analyzed"],
    }


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    result = measure(REPO / "data")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
