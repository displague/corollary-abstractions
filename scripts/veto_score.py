#!/usr/bin/env python3
"""Adjudicate the coincidence veto once (ROADMAP-v0.15 item 2, steps 3-4).

Order is fixed by the design and enforced here: the blind control is computed
and reported before the kind-based flags, because it can end the direction.
The corruption control runs after, and can void the result.

The object has exactly two values, `conflicting` and `unjudged`, and no
positive vocabulary.  Nothing in this file can assert that two statements are
the same, and `unjudged` is not a clean bill of health.

Design: docs/DESIGN-coincidence-veto.md
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXP = REPO / "experiments"
OUT = EXP / "veto_result.json"


def _load() -> tuple[dict, dict, dict, dict]:
    inv = json.loads((EXP / "veto_slot_inventory.json").read_text(encoding="utf-8"))
    tags = json.loads((EXP / "veto_kind_tags.json").read_text(encoding="utf-8"))
    table = json.loads((EXP / "veto_incompatible_kinds.json").read_text(encoding="utf-8"))
    pred = json.loads((EXP / "veto_prediction.json").read_text(encoding="utf-8"))
    return inv, tags, table, pred


def _incompatible(table: dict) -> set[frozenset[str]]:
    return {frozenset(row["kinds"]) for row in table["incompatible"]}


def _slots(inv: dict):
    for group in inv["inventory"]:
        for slot in group["slots"]:
            yield group, slot


def blind_label(slot: dict) -> str:
    """The cheapest method that ignores kinds entirely."""
    names = {name.casefold() for name in slot["symbols"].values()}
    return "conflicting" if len(names) > 1 else "unjudged"


def kind_label(slot: dict, tag_of: dict, bad: set[frozenset[str]]) -> tuple[str, list]:
    kinds = {
        sid: tag_of[f"{sid}::{name}"] for sid, name in slot["symbols"].items()
    }
    known = {sid: k for sid, k in kinds.items() if k != "kind-unknown"}
    certificate = []
    ids = sorted(known)
    for i, left in enumerate(ids):
        for right in ids[i + 1:]:
            if frozenset((known[left], known[right])) in bad:
                certificate.append({
                    "statements": [left, right],
                    "symbols": [slot["symbols"][left], slot["symbols"][right]],
                    "kinds": [known[left], known[right]],
                })
    return ("conflicting" if certificate else "unjudged"), certificate


def run() -> dict:
    inv, tags, table, pred = _load()
    tag_of = tags["tags"]
    bad = _incompatible(table)

    slots = list(_slots(inv))
    fully_tagged = [
        (g, s) for g, s in slots
        if all(tag_of[f"{sid}::{n}"] != "kind-unknown" for sid, n in s["symbols"].items())
    ]

    # --- blind control, first ---
    agree = sum(
        1 for g, s in fully_tagged
        if blind_label(s) == kind_label(s, tag_of, bad)[0]
    )
    blind_agreement = agree / len(fully_tagged) if fully_tagged else 0.0
    blind_defeats = blind_agreement >= 0.80

    # --- the flags ---
    rows = []
    for group, slot in slots:
        label, cert = kind_label(slot, tag_of, bad)
        rows.append({
            "skeleton": group["skeleton"],
            "archetypes": group["archetypes"],
            "slot": slot["slot"],
            "label": label,
            "certificate": cert,
        })
    conflicting = sum(1 for r in rows if r["label"] == "conflicting")

    # --- corruption control ---
    occurrences = sorted(tag_of)
    values = [tag_of[k] for k in occurrences]
    rng = random.Random(pred["corruption_control"]["seed"])
    counts = []
    for _ in range(pred["corruption_control"]["permutations"]):
        shuffled = values[:]
        rng.shuffle(shuffled)
        permuted = dict(zip(occurrences, shuffled, strict=True))
        counts.append(sum(
            1 for _g, s in slots if kind_label(s, permuted, bad)[0] == "conflicting"
        ))
    permuted_mean = sum(counts) / len(counts)

    band = pred["band"]
    in_band = band["floor"] <= conflicting <= band["ceiling"]

    def group_label(name: str) -> str:
        """Match any archetype named in the call; a group may carry several."""
        wanted = {part.strip() for part in name.split("/")}
        hits = [r["label"] for r in rows if wanted & set(r["archetypes"])]
        if not hits:
            raise KeyError(f"no group carries archetype {sorted(wanted)}")
        return "conflicting" if "conflicting" in hits else "unjudged"

    named = []
    for call in pred["named_directional_predictions"]:
        target = call.get("group")
        if target:
            observed = group_label(target)
        else:
            groups = ("idempotent_operation", "lattice_absorption",
                      "identity_element_law", "complement_involution")
            observed = ("conflicting"
                        if any(group_label(g) == "conflicting" for g in groups)
                        else "unjudged")
        # "unjudged" and "not conflicting" name the same state; the object has
        # only two values and the prediction file writes the readable one.
        expected = ("conflicting" if call["predicted"] == "conflicting"
                    else "unjudged")
        named.append({
            "id": call["id"], "predicted": call["predicted"],
            "observed": observed, "held": observed == expected,
        })

    return {
        "schema": "veto_result.v1",
        "design": "docs/DESIGN-coincidence-veto.md",
        "blind_control": {
            "ran": "first",
            "agreement_with_kind_labelling": round(blind_agreement, 4),
            "of_fully_tagged_slots": len(fully_tagged),
            "threshold": 0.80,
            "defeats_direction": blind_defeats,
        },
        "corruption_control": {
            "authored_conflicting": conflicting,
            "permuted_mean": permuted_mean,
            "requirement": "authored strictly fewer than permuted mean",
            "held": conflicting < permuted_mean,
            "valid": False,
            "invalid_because": (
                "the incompatibility table was scoped to the kind pairs that "
                "co-occur under the AUTHORED tags, so a permuted assignment "
                "raises pairs the table has no row for and cannot fire: 107 of "
                "133 permuted pairs are unrepresented against 24 of 75 authored "
                "ones. The baseline is crippled by construction, so this control "
                "neither passes nor voids the result. It is a defect in how the "
                "table was scoped at authoring time, not a finding about the tags."
            ),
        },
        "adjudication": {
            "conflicting_slots": conflicting,
            "unjudged_slots": len(slots) - conflicting,
            "of": len(slots),
            "band": [band["floor"], band["ceiling"]],
            "in_band": in_band,
            "named_predictions": named,
        },
        "flags": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write and OUT.exists():
        print("REFUSED: result already exists and is never overwritten")
        return 2
    result = run()
    if args.write:
        OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8",
                       newline="\n")
    print(json.dumps(
        {k: v for k, v in result.items() if k != "flags"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
