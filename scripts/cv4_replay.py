#!/usr/bin/env python3
"""G3: re-derive v0.19's drawn C-V4 id lists, and pin them.

DESIGN-voice-completion §3.4 and Correction 6.  **The ids are not in the run
artifact.**  A sweep of `experiments/foreign_voice_rate.json` finds no
sample-id field anywhere: `c_v4.per_class` carries counts only, and the 2,313
B1 receipts carry no mutation record.  What *is* committed is the selection
program, so the ids are **re-derived** rather than transcribed — and the
derivation is checkable rather than asserted.

## Why the seed can no longer carry them

Correction 4.  The canonicalization contradicts the lexicon's committed
`reading_rules`, so that file must be amended and its digest moves.  Worse
than the seed moving: `drop_group` and `shift_group` admit on *"the quantity"
appearing in the surface*, and canonical rendering takes that pool from
**1,549 to 1,399** — so even an unchanged seed would draw a different 50.
Seed-pinning cannot preserve those draws.  **The id list is the pin.**

Seed-pinning survives for B0d alone, whose pool is the eligible set and is
grammar-independent (§3.2).  Everywhere else, this file.

## The pre-amendment lexicon comes from git, not from memory

The replay must run against the lexicon **as it was when v0.19 drew**.  This
module extracts that blob with `git show {parent}:…` and **refuses to write
anything** unless its LF sha256 equals the retired pin the prereg records.
The precedent is exact and its reasoning is quoted where it is used:

> *"An in-memory revert re-types the old regex, and the digest check would then
> be checking the copy against itself. The blob from git IS the pre-amendment
> file."* (`scripts/transliteration_served_diff.py:357–360`)

## What it verifies before it will write

Every one of the five `admitting` counts must reproduce the shipped artifact's
own numbers.  If a single pool differs, the replay is not replaying v0.19's
draw and the ids it produces are some other sample.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice_lexicon as fvl  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "data" / "foreign_voice" / "cv4_replay_ids.json"
LEXICON = "data/foreign_voice/lexicon.json"


class ReplayRefusal(RuntimeError):
    """The pre-amendment inputs could not be established. Never a guessed id list."""


def retired_lexicon_digest() -> str:
    """The value the prereg recorded when the amendment retired it."""
    prereg = json.loads(
        (REPO_ROOT / "experiments" / "foreign_voice_prereg.json").read_text(
            encoding="utf-8"))
    for entry in prereg.get("corrections", []):
        for row in entry.get("digests_retired", []):
            if row["path"] == LEXICON:
                return row["v019_sha256_lf"]
    raise ReplayRefusal(
        "the prereg records no retirement for the lexicon; there is nothing to "
        "replay against")


def pre_amendment_lexicon(parent: str) -> fvl.ForeignLexicon:
    """The blob from git, digest-checked. REFUSES rather than reconstructing."""
    blob = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{parent}:{LEXICON}"],
        capture_output=True)
    if blob.returncode != 0:
        raise ReplayRefusal(
            f"cannot read {LEXICON} at {parent}: "
            f"{blob.stderr.decode('utf-8', 'replace')[:160]}")
    raw = blob.stdout.replace(b"\r\n", b"\n")
    digest = hashlib.sha256(raw).hexdigest()
    expected = retired_lexicon_digest()
    if digest != expected:
        raise ReplayRefusal(
            f"the blob at {parent} is {digest[:16]}… and the prereg retired "
            f"{expected[:16]}…. An in-memory revert would re-type the old file "
            f"and the digest check would be checking the copy against itself; "
            f"the blob from git IS the pre-amendment file, and this one is not it."
        )
    return fvl.build(json.loads(raw.decode("utf-8"), object_pairs_hook=fvl._load_pairs),
                     "<pre-amendment>"), digest


def replay(parent: str) -> dict:
    lexicon, digest = pre_amendment_lexicon(parent)
    data = REPO_ROOT / "data" / "foreign_voice"
    preview = json.loads((data / "eligibility_preview.json").read_text(encoding="utf-8"))
    register = json.loads((data / "register.json").read_text(encoding="utf-8"))
    rows = mfv.covered_rows(preview, register)

    prereg = json.loads(
        (REPO_ROOT / "experiments" / "foreign_voice_prereg.json").read_text(
            encoding="utf-8"))
    block = prereg["c_v4"]
    plan = mfv._plan(digest, rows, lexicon, block["sample_size"],
                     block["mutations"])

    shipped = json.loads(
        (REPO_ROOT / "experiments" / "foreign_voice_rate.json").read_text(
            encoding="utf-8"))["c_v4"]["per_class"]

    classes: dict[str, dict] = {}
    mismatches: list[str] = []
    for name, sample in sorted(plan.items()):
        admitting = sample[0]["admitting"] if sample else 0
        if admitting != shipped[name]["admitting"]:
            mismatches.append(
                f"{name}: replay {admitting}, artifact {shipped[name]['admitting']}")
        classes[name] = {
            "statement_ids": [entry["statement_id"] for entry in sample],
            "admitting": admitting,
            "admitting_in_the_shipped_artifact": shipped[name]["admitting"],
            "reproduces": admitting == shipped[name]["admitting"],
            "sample_size": len(sample),
        }
    if mismatches:
        raise ReplayRefusal(
            "the replay does not reproduce the shipped pools, so it is not "
            "replaying v0.19's draw: " + "; ".join(mismatches))

    return {
        "replay_id": "foreign_voice.cv4_replay_ids.v1",
        "registered": "2026-08-25",
        "gate": "G3 — the drawn id lists are pinned, and the pin is reproducible",
        "design": "docs/DESIGN-voice-completion.md",
        "why_the_id_list_and_not_the_seed": [
            "The canonicalization amends the lexicon, so its digest — the seed "
            "for every draw in the cycle — moves.",
            "Worse than the seed moving: drop_group and shift_group admit on a "
            "grouping word appearing in the surface, and canonical rendering "
            "takes that pool from 1,549 to 1,399. Even an unchanged seed would "
            "draw a different 50.",
            "So the ids themselves are the pin. Seed-pinning survives for B0d "
            "alone, whose pool is the eligible set and is grammar-independent.",
        ],
        "derivation": {
            "program": "scripts/measure_foreign_voice.py::_plan, unmodified",
            "inputs": [
                "the covered rows of data/foreign_voice/eligibility_preview.json",
                "the PRE-AMENDMENT data/foreign_voice/lexicon.json, taken as a "
                "blob from git and digest-checked",
                "experiments/foreign_voice_prereg.json's c_v4 sample_rule and "
                "mutation list",
            ],
            "parent_commit": parent,
            "pre_amendment_lexicon_sha256_lf": digest,
            "why_the_blob_and_not_an_in_memory_revert": (
                "an in-memory revert re-types the old file and the digest check "
                "would then be checking the copy against itself; the blob from "
                "git IS the pre-amendment file"
            ),
            "verified_against": (
                "all five `admitting` counts reproduce the shipped "
                "experiments/foreign_voice_rate.json exactly; the module refuses "
                "to write if any one of them differs"
            ),
        },
        "classes": classes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parent", default="HEAD~1",
                        help="the commit whose lexicon blob predates the amendment")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        report = replay(args.parent)
    except ReplayRefusal as exc:
        print(f"replay refused: {exc}", file=sys.stderr)
        return 2
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    for name, row in sorted(report["classes"].items()):
        print(f"  {name:16} {row['sample_size']} ids, admitting {row['admitting']} "
              f"(artifact {row['admitting_in_the_shipped_artifact']}) "
              f"reproduces={row['reproduces']}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
