#!/usr/bin/env python3
"""Slot inventory for the coincidence veto (ROADMAP-v0.15 item 2, step 1).

Pure computation.  This emits which symbols sit in aligned slots of the
qualifying cross-field twin groups, and nothing else: no kind, no judgement,
no flag.  Those come from separately authored files, and this file must be
committed before they are written, because the denominator it establishes is
what the registered prediction is stated against.

Alignment is read from the committed skeleton, never chosen: slots are
numbered by first occurrence in the same typed-resorted tree that
`match_signatures.render_skeleton` walks, so `?0` here is `?0` there.

Design: docs/DESIGN-coincidence-veto.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import records  # noqa: E402
from decompose import INGESTED_CORPUS_PREFIXES  # noqa: E402
from match_signatures import (  # noqa: E402
    Parser,
    canonicalize,
    skeleton,
    slot_classes,
    tokenize,
    typed_resort,
)

LEDGER = REPO / "reports" / "signature_matches.json"
OUT = REPO / "experiments" / "veto_slot_inventory.json"


def slot_order(node: tuple) -> list[str]:
    """Slot names in first-occurrence order.

    This mirrors `render_skeleton`'s `indices.setdefault(name, len(indices))`
    exactly.  If that numbering ever changes, this inventory stops agreeing
    with the committed skeleton and the construction gate must fail rather
    than quietly realign.
    """
    seen: list[str] = []

    def walk(n: tuple) -> None:
        kind = n[0]
        if kind == "num":
            return
        if kind == "slot":
            if n[1] not in seen:
                seen.append(n[1])
            return
        for arg in n[2]:
            walk(arg)

    walk(node)
    return seen


def _committed_nodes() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted((REPO / "data").glob("*/nodes.json")):
        for node in json.loads(path.read_text(encoding="utf-8")).get(
            "statement_nodes", []
        ):
            out[node["statement_id"]] = node
    return out


def qualifying_groups(ledger: dict, corpus: dict) -> list[dict]:
    """The population predicate, committed rather than curated.

    A typed twin group qualifies when its members span more than one
    top-level id namespace and no member comes from an ingested corpus.
    """
    ingested = tuple(INGESTED_CORPUS_PREFIXES)

    def hand_authored(sid: str) -> bool:
        found = corpus.get(sid)
        return found is not None and not found[1].startswith(ingested)

    out = []
    for group in ledger["typed_twin_groups"]:
        ids = [m["statement_id"] for m in group["members"]]
        if len({s.split(".", 1)[0] for s in ids}) > 1 and all(
            hand_authored(s) for s in ids
        ):
            out.append(group)
    return sorted(out, key=lambda g: g["skeleton"])


def build() -> dict:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    corpus = records([REPO / "data"])
    nodes = _committed_nodes()
    groups_out: list[dict] = []
    problems: list[str] = []

    for group in qualifying_groups(ledger, corpus):
        orders: dict[str, list[str]] = {}
        for member in group["members"]:
            sid = member["statement_id"]
            node = nodes[sid]
            tree = canonicalize(
                Parser(
                    tokenize(node["structural_signature"]["anonymized_template"])
                ).parse()
            )
            classes = slot_classes(node)
            if skeleton(tree, classes) != group["skeleton"]:
                problems.append(f"{sid}: recomputed skeleton disagrees with ledger")
                continue
            orders[sid] = slot_order(typed_resort(tree, classes, None))

        widths = {len(v) for v in orders.values()}
        if len(orders) != len(group["members"]) or len(widths) != 1:
            problems.append(
                f"{group['skeleton']}: members disagree on slot count {sorted(widths)}"
            )
            continue

        width = widths.pop()
        groups_out.append({
            "skeleton": group["skeleton"],
            "archetypes": sorted(group.get("archetypes", [])),
            "members": sorted(orders),
            "slots": [
                {
                    "slot": index,
                    "symbols": {sid: orders[sid][index] for sid in sorted(orders)},
                }
                for index in range(width)
            ],
        })

    return {
        "schema": "veto_slot_inventory.v1",
        "design": "docs/DESIGN-coincidence-veto.md",
        "population": (
            "typed twin groups spanning more than one top-level id namespace "
            "with no ingested member"
        ),
        "groups": len(groups_out),
        "aligned_slots": sum(len(g["slots"]) for g in groups_out),
        "distinct_symbol_occurrences": len(
            {
                (sid, name)
                for g in groups_out
                for s in g["slots"]
                for sid, name in s["symbols"].items()
            }
        ),
        "problems": problems,
        "inventory": groups_out,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build()
    if report["problems"]:
        print("REFUSED:", *report["problems"], sep="\n  ")
        return 2
    if args.write:
        OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8",
                       newline="\n")
        print(f"wrote {OUT.relative_to(REPO)}")
    print(
        f"{report['groups']} groups, {report['aligned_slots']} aligned slots, "
        f"{report['distinct_symbol_occurrences']} symbol occurrences"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
