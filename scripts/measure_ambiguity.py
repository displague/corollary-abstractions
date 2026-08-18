#!/usr/bin/env python3
"""A1 — is ambiguity common enough to be worth resolving?

`docs/DESIGN-ambiguity-and-context.md` orders this FIRST, ahead of any of
the machinery in its §3, and says why: if in-corpus queries almost always
BIND, then the ASK substrate is an artifact of a small curated layer, it
will thin out as the corpus grows, and context-accumulation is machinery
for a problem that solves itself. §6 names A1 as the falsifier for the
whole frame.

- **A1.** On the development and holdout query sets, at least **25%** of
  in-corpus queries end in ASK rather than BIND.

Registered in that design before this script existed. Measured over every
committed query set at once — the development set and both text holdouts —
because the prediction was written about all of them and picking the
friendliest one afterwards is how a threshold becomes a formality.

Also reported, unregistered and clearly labelled: the SIZE of the candidate
sets. A1 only asks whether ambiguity happens. Whether it is *tractable* —
two candidates a person can choose between, versus ninety they cannot — is
what A2 will have to move, and knowing the starting distribution costs
nothing here.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from resolver import ASK, BIND, default_index, resolve  # noqa: E402

DEFAULT_OUT = REPO / "experiments" / "ambiguity_rate.json"
THRESHOLD = 0.25

QUERY_SETS = (
    ("development", "text_resolution_queries.json"),
    ("holdout_1", "text_resolution_holdout.json"),
    ("holdout_2", "text_resolution_holdout2.json"),
)


def run(out_path: Path) -> dict:
    index = default_index()
    per_set: dict[str, dict] = {}
    all_sizes: list[int] = []
    total_bind = total_ask = 0

    for name, filename in QUERY_SETS:
        path = REPO / "experiments" / filename
        if not path.is_file():
            continue
        spec = json.loads(path.read_text(encoding="utf-8"))
        binds = asks = 0
        sizes: list[int] = []
        ask_examples: list[dict] = []
        for query in spec["queries"]:
            # Only in-corpus queries. A refusal that ends in PASS says
            # nothing about ambiguity, and counting it would dilute the
            # rate with questions the corpus was never going to answer.
            if query.get("expect") != "resolve":
                continue
            outcome = resolve(query["text"], index)
            if outcome.kind == BIND:
                binds += 1
            elif outcome.kind == ASK:
                asks += 1
                sizes.append(len(outcome.candidates))
                if len(ask_examples) < 8:
                    ask_examples.append({
                        "text": query["text"],
                        "candidates": len(outcome.candidates),
                        "resolver": outcome.resolver,
                    })
        decided = binds + asks
        per_set[name] = {
            "resolve_queries": decided,
            "bind": binds,
            "ask": asks,
            "ask_rate": round(asks / decided, 4) if decided else None,
            "ask_candidates_median": (
                statistics.median(sizes) if sizes else None
            ),
            "ask_candidates_max": max(sizes) if sizes else None,
            "ask_examples": ask_examples,
        }
        all_sizes.extend(sizes)
        total_bind += binds
        total_ask += asks

    decided = total_bind + total_ask
    rate = (total_ask / decided) if decided else 0.0
    result = {
        "schema": "ambiguity_rate.v1",
        "design": "docs/DESIGN-ambiguity-and-context.md",
        "measures": "how often an in-corpus query ends in ASK rather than BIND",
        "graph_nodes": index.size,
        "pooled": {
            "resolve_queries": decided,
            "bind": total_bind,
            "ask": total_ask,
            "ask_rate": round(rate, 4),
        },
        "unregistered_probe": {
            "note": "A1 asks IF ambiguity happens; tractability is A2's",
            "ask_candidates_median": (
                statistics.median(all_sizes) if all_sizes else None
            ),
            "ask_candidates_max": max(all_sizes) if all_sizes else None,
            "ask_sets_of_two_or_three": sum(1 for s in all_sizes if s <= 3),
            "ask_sets_over_ten": sum(1 for s in all_sizes if s > 10),
        },
        "per_set": per_set,
        "adjudication": {
            "A1": {
                "fired": rate >= THRESHOLD,
                "ask_rate": round(rate, 4),
                "threshold": THRESHOLD,
                "ask": total_ask,
                "of": decided,
            }
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    result = run(args.out)
    print(json.dumps({
        "A1": result["adjudication"]["A1"],
        "pooled": result["pooled"],
        "candidate_sizes": result["unregistered_probe"],
        "per_set": {
            k: {"ask": v["ask"], "bind": v["bind"], "rate": v["ask_rate"]}
            for k, v in result["per_set"].items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
