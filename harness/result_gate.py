#!/usr/bin/env python3
"""The result gate: which sentence the census the harness returned licenses.

`docs/DESIGN-cold-receipt.md` §13 fixes this **before the run**, on
`DESIGN-session-ledger` §9's R1 shape — *the capability claimed and the number
that licenses it, with nothing more attached*. This file is that table
executed, so the reading is computed from the census rather than written about
it, and the sentence a partition licenses cannot widen on the way to a
release note.

The partitions are §13's, in §13's order, and the strings below are its
strings. The gate is deliberately **not** a summariser: it emits exactly one
`licensed_sentence`, and everything the design attaches to that partition —
the named kinds, the consequence, the stop — travels with it.

Harness code, not program code: stdlib only, imports nothing from this
repository.

    python harness/result_gate.py --census cold/census.json --out cold/result_gate.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CR_P0_ARTIFACT = "experiments/cold_registry_census.json"
CR_P1_ARTIFACT = "cold/reconstruction_rule.json"


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def provenance_block(writer: Path, inputs: list[Path]) -> dict:
    rows = [
        {
            "path": path.resolve().relative_to(REPO).as_posix(),
            "sha256_lf": sha256_lf(path),
        }
        for path in inputs
        if path.is_file()
    ]
    rows.sort(key=lambda row: row["path"])
    return {
        "writer": writer.resolve().relative_to(REPO).as_posix(),
        "writer_sha256_lf": sha256_lf(writer),
        "inputs": rows,
        "emitted_at_generation": True,
    }


def _commit_of(path: str, first: bool = True) -> str | None:
    """The commit that INTRODUCED `path`, not the one that last touched it.

    R-C's third clause is that CR-P0 and CR-P1 were committed **in order**,
    which is a fact about when each prerequisite LANDED. Reading the latest
    commit instead would let a later amendment to CR-P0 — exactly what
    amendment 2 is — retroactively falsify an ordering that did hold. The
    latest commit is recorded too, so the amendment stays visible.
    """

    argv = ["git", "-C", str(REPO), "log", "--format=%H"]
    if first:
        argv += ["--diff-filter=A", "--reverse"]
    else:
        argv += ["-1"]
    argv += ["--", path]
    completed = subprocess.run(
        argv, capture_output=True, text=True, timeout=60
    )
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    return lines[0] if lines else None


def _is_ancestor(earlier: str, later: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(REPO), "merge-base", "--is-ancestor", earlier, later],
        capture_output=True,
        timeout=60,
    )
    return completed.returncode == 0


def committed_in_order() -> dict:
    """R-C's third clause: CR-P0 and CR-P1 committed **in order**."""

    p0 = _commit_of(CR_P0_ARTIFACT)
    p1 = _commit_of(CR_P1_ARTIFACT)
    ordered = bool(p0 and p1) and (p0 == p1 or _is_ancestor(p0, p1))
    return {
        "cr_p0_first_commit": p0,
        "cr_p1_first_commit": p1,
        "cr_p0_latest_commit": _commit_of(CR_P0_ARTIFACT, first=False),
        "cr_p1_latest_commit": _commit_of(CR_P1_ARTIFACT, first=False),
        "cr_p0_precedes_cr_p1": ordered,
        "how_checked": (
            "git merge-base --is-ancestor over the commits that INTRODUCED "
            "each artifact; the latest commits are recorded beside them so a "
            "later amendment stays visible without falsifying an ordering that "
            "did hold"
        ),
    }


def adjudicate(census: dict) -> dict:
    counts = census["counts"]
    gate = census["gate"]
    kinds = census["kinds"]

    survives = [k["kind_id"] for k in kinds if k["verdict"] == "SURVIVES"]
    needs = [k["kind_id"] for k in kinds if k["verdict"] == "NEEDS-PROGRAM"]
    untested = [k["kind_id"] for k in kinds if k["verdict"] == "UNTESTED"]
    downgraded = [
        k["kind_id"] for k in kinds if k.get("b11_downgrade_applied")
    ]

    order = committed_in_order()
    reds = sorted(name for name, row in gate.items() if not row.get("green"))
    voiding = census["voiding_sentence"]["fired"]
    b1_unmeetable = gate["B1"]["value"] != 0

    r_c_green = (
        not reds and not voiding and order["cr_p0_precedes_cr_p1"]
    )

    # §13's partitions, in §13's order. The voiding sentence outranks every
    # reading because it says no partition is published at all.
    if b1_unmeetable:
        partition = "B1 unmeetable (CR-P0's stop)"
        sentence = "This program cannot enumerate its own evidence."
        attached = {
            "harness_opens": False,
            "headline": "the census",
        }
    elif voiding:
        partition = "voiding sentence fires"
        sentence = (
            "Instrument failure, not a capability. No partition is published, "
            "and the sham-checker result is the artifact."
        )
        attached = {"sham_result": census["arms"]["sham"]["gate"]}
    elif not survives:
        partition = "0 kinds SURVIVE (B2 red)"
        sentence = (
            "No receipt kind this program emits can be re-checked without the "
            "program."
        )
        attached = {
            "consequence": (
                "Every offline-checkability sentence in the tree is withdrawn "
                "to a bytes-integrity sentence, and §14's suspended habit "
                "becomes permanent."
            ),
            "this_is_a_report_and_stop": True,
        }
    elif untested and not survives and not needs:
        partition = "all UNTESTED via B11"
        sentence = (
            "The program's evidence was re-checked in a world the program "
            "prepared, and nothing follows about its independence."
        )
        attached = {"tags": census["arms"]["provenance"]["dependencies"]}
    else:
        partition = ">=1 SURVIVES, some NEEDS-PROGRAM"
        # §13's string, transcribed exactly. "census.json" is the design's
        # spelling; substituting the artifact's path would be paraphrasing a
        # frozen sentence, which is the habit this gate exists to prevent.
        sentence = (
            "For the receipt kinds census.json names SURVIVES, the recorded "
            "verdict can be re-derived on this workstation with the program's "
            "script tree renamed away and no sys.path entry inside the "
            "repository, using only the bundle and dependencies tagged "
            "third_party_pinned."
        )
        attached = {
            "scoped_to_kinds": survives,
            "needs_program_kinds_published_by_name": needs,
            "b7_note": (
                "a correct NEEDS-PROGRAM scores as a hit, so this partition is "
                "a reading and not a shortfall"
            ),
            "nothing_more": "no rate, no other machine, no person",
        }

    return {
        "schema": "cold-result-gate/1",
        "design": "docs/DESIGN-cold-receipt.md §13",
        "registered_before_the_run": True,
        "counts": counts,
        "verdicts": {
            "SURVIVES": survives,
            "NEEDS-PROGRAM": needs,
            "UNTESTED": untested,
            "downgraded_by_B11": downgraded,
        },
        "gate_greens": {name: bool(row.get("green")) for name, row in gate.items()},
        "gate_reds": reds,
        "voiding_sentence_fired": voiding,
        "ordering": order,
        "R_C": {
            "clause": (
                "B1 through B11 green, the voiding sentence not fired, and "
                "CR-P0 and CR-P1 committed in order"
            ),
            "green": r_c_green,
            "note": (
                "R-C failing on any clause serves nothing and publishes the "
                "readout"
            ),
        },
        "partition": partition,
        "licensed_sentence": sentence,
        "attached_to_the_sentence": attached,
        "non_claims": [
            "No stranger-success claim. What the harness shows is "
            "program-absent-harness success: a procedure completed with this "
            "repository's script tree renamed away, on this Windows "
            "workstation, under §6's named weaker-than-a-container exclusions. "
            "No person outside this repository is in the instrument; STRANGER "
            "stays parked.",
            "No version-drift claim, deferred by B9 to a parked lane.",
            "No composition claim. Each kind is adjudicated alone; that kinds A "
            "and B each SURVIVE says nothing about a claim resting on both.",
            "No coverage claim over the repository. The census covers what "
            "CR-P0 enumerates; later finds publish as census misses (B10).",
            "No retroactive effect. A SURVIVES makes no past sentence true; a "
            "NEEDS-PROGRAM voids no run — it voids the offline-checkability "
            "sentence about that kind, and nothing else.",
            "No security claim.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", type=Path, default=REPO / "cold" / "census.json")
    parser.add_argument("--out", type=Path, default=REPO / "cold" / "result_gate.json")
    args = parser.parse_args(argv)

    census_path = args.census.resolve()
    census = json.loads(census_path.read_text(encoding="utf-8"))
    gate = adjudicate(census)
    gate["provenance"] = provenance_block(Path(__file__), [census_path])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(gate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"partition: {gate['partition']}")
    print(f"R-C green: {gate['R_C']['green']}  reds: {gate['gate_reds'] or 'none'}")
    print(f"licensed:  {gate['licensed_sentence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
