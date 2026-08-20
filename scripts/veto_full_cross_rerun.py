#!/usr/bin/env python3
"""The tag-permutation control, rerun against the blind full-cross table.

ROADMAP-v0.16 item 2, exploratory by its own terms and labelled so: the
population is a census with no fresh half. The readout criterion was
fixed BEFORE the table existed (experiments/veto_full_cross_protocol.md):
established only if the real-tags conflicting count sits strictly below
the 5th percentile of the permuted distribution; otherwise the
suspension expires by its own two-cycle clause.

Everything mechanical is reused from the frozen v0.15 instrument
(`veto_score.py`): the slot inventory, the tags, the permutation scheme,
and the committed seed and permutation count from
`experiments/veto_prediction.json`. The only substitution is the verdict
source: the 325-pair table authored blind in an isolated context, which
gives every permuted pair a row — the coverage the v0.15 scoped table
could not provide, which is what invalidated the original control.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import veto_score  # noqa: E402

EXP = REPO / "experiments"
OUT = EXP / "veto_full_cross_result.json"


def main() -> int:
    inv, tags, scoped_table, pred = veto_score._load()
    full = json.loads(
        (EXP / "veto_full_cross_table.json").read_text(encoding="utf-8")
    )
    tag_of = tags["tags"]
    bad_full = {frozenset(row["kinds"]) for row in full["incompatible"]}
    bad_scoped = veto_score._incompatible(scoped_table)

    slots = list(veto_score._slots(inv))

    # Real tags, both tables (the scoped count is context, not a score).
    real_full = sum(
        1 for _g, s in slots
        if veto_score.kind_label(s, tag_of, bad_full)[0] == "conflicting"
    )
    real_scoped = sum(
        1 for _g, s in slots
        if veto_score.kind_label(s, tag_of, bad_scoped)[0] == "conflicting"
    )

    # The permutation loop: same seed, same count, same scheme as v0.15.
    occurrences = sorted(tag_of)
    values = [tag_of[k] for k in occurrences]
    rng = random.Random(pred["corruption_control"]["seed"])
    counts = []
    for _ in range(pred["corruption_control"]["permutations"]):
        shuffled = values[:]
        rng.shuffle(shuffled)
        permuted = dict(zip(occurrences, shuffled, strict=True))
        counts.append(sum(
            1 for _g, s in slots
            if veto_score.kind_label(s, permuted, bad_full)[0] == "conflicting"
        ))
    ordered = sorted(counts)
    p5_index = max(0, int(0.05 * len(ordered)) - 1)
    fifth_percentile = ordered[p5_index]
    established = real_full < fifth_percentile

    # Agreement with the v0.15 scoped table on the pairs both cover:
    # disagreements listed, not reconciled (protocol).
    scoped_pairs = bad_scoped | {
        frozenset(row["kinds"]) for row in scoped_table["deliberately_compatible"]
    }
    disagreements = []
    for pair in sorted(scoped_pairs, key=sorted):
        scoped_verdict = "incompatible" if pair in bad_scoped else "compatible"
        full_verdict = "incompatible" if pair in bad_full else "compatible"
        if scoped_verdict != full_verdict:
            disagreements.append({
                "kinds": sorted(pair),
                "scoped_v015": scoped_verdict,
                "blind_full": full_verdict,
            })

    result = {
        "schema": "veto-full-cross-result/1",
        "protocol": "experiments/veto_full_cross_protocol.md",
        "exploratory": True,
        "real_tags_conflicting_full_table": real_full,
        "real_tags_conflicting_scoped_table_v015": real_scoped,
        "permutations": len(counts),
        "seed": pred["corruption_control"]["seed"],
        "permuted_min": ordered[0],
        "permuted_5th_percentile": fifth_percentile,
        "permuted_mean": sum(counts) / len(counts),
        "permuted_max": ordered[-1],
        "criterion": "established iff real < 5th percentile (fixed in the protocol before the table existed)",
        "established": established,
        "consequence_if_not": "the suspension expires at this release by its own two-cycle clause; the count returns as an unadjudicated observation carrying the one-row finding",
        "scoped_overlap_pairs": len(scoped_pairs),
        "disagreements_with_scoped": disagreements,
    }
    with OUT.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=1, ensure_ascii=False)
        handle.write("\n")
    print(f"real (full table): {real_full}  |  scoped v0.15: {real_scoped}")
    print(f"permuted: min {ordered[0]}  p5 {fifth_percentile}  "
          f"mean {result['permuted_mean']:.1f}  max {ordered[-1]}")
    print(f"established: {established}")
    print(f"disagreements with scoped table: {len(disagreements)} "
          f"of {len(scoped_pairs)} shared pairs")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
