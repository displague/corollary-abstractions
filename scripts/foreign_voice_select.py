#!/usr/bin/env python3
"""B0d's id-selection rule: 100 statements, drawn by a committed rule.

DESIGN-foreign-voice §6 B0d: *"Over 100 statements drawn from the
oracle-eligible set by a **committed deterministic rule seeded from the lexicon
digest** (no hand-picking, and the rule is in the prereg commit)"*, and the
three-line separation its adversarial review required:

  1. the lexicon digest is frozen **before the hand-renderings exist**;
  2. the 100 ids **follow from that digest** by this rule;
  3. the 100 hand-renderings are committed verbatim as a **sealed prediction**
     that the implementation must later reproduce **byte-identically**, with
     every divergence reported in the run artifact.

*"A hand probe whose outputs are never compared against the implementation is a
rehearsal, not a gate."*

## Why the seed is the lexicon's own digest

v0.18's C-R1 idiom, imported: *"a seed someone chose would be a knob; the table
under test is not"* (`tests/test_measure_realization.py:163–167`).  The draw is
a function of the artifact being probed, so nobody can shop for an easy
hundred by re-rolling.  `scripts/measure_realization.py:387` seeds from
`int(seed_hex[:16], 16)`; this module does the same, from
`data/foreign_voice/lexicon.json`'s LF sha256.

## The portability caveat, stated rather than discovered

`random.Random.shuffle` is deterministic for a given seed **on a given CPython
implementation**, not by language guarantee — the same caveat v0.18's
derangement already lives under.  So the drawn ids are also **committed as a
file**, and `tests/test_foreign_voice_b0d.py` re-derives them and compares.  If
a future interpreter changes the shuffle, that test goes red and the change is
a visible event with a dated amendment, rather than a sealed prediction
quietly pointing at a different hundred statements.

## No hand-picking, and what that costs

The pool is **every oracle-eligible statement**, in sorted id order, with
nothing removed — including the six the lexicon will refuse (four carrying a
coercion arrow, one carrying a 433-digit literal, one carrying a non-canonical
decimal).  Excluding them would be selecting for renderability, which is
exactly the hand-picking the clause forbids; if the draw lands on one, the
sealed prediction for it is a **refusal with its reason**, and the
implementation must reproduce that refusal too.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = REPO_ROOT / "data" / "foreign_voice" / "lexicon.json"
PREVIEW_PATH = REPO_ROOT / "data" / "foreign_voice" / "eligibility_preview.json"
DEFAULT_OUT = REPO_ROOT / "data" / "foreign_voice" / "b0d_ids.json"

SAMPLE_SIZE = 100


def sha256_lf(path: Path) -> str:
    """Canonical-LF sha256 — the same digest the prereg records."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def eligible_ids(preview: dict) -> list[str]:
    """Every oracle-eligible id, sorted. Nothing removed — see the docstring."""
    return sorted(row["statement_id"] for row in preview["statements"]
                  if row["accepted"])


def select(pool: list[str], seed_hex: str, size: int = SAMPLE_SIZE) -> list[str]:
    """The rule. Sorted pool, seeded shuffle, first `size`, returned sorted.

    Sorting the pool first is load-bearing: the preview's statement order is a
    corpus-iteration artifact, and a rule that depended on it would not be a
    function of the digest.
    """
    if len(pool) < size:
        raise ValueError(f"pool of {len(pool)} cannot yield {size} ids")
    shuffled = list(pool)
    random.Random(int(seed_hex[:16], 16)).shuffle(shuffled)
    return sorted(shuffled[:size])


def build(lexicon_path: Path = LEXICON_PATH,
          preview_path: Path = PREVIEW_PATH,
          size: int = SAMPLE_SIZE) -> dict:
    seed_hex = sha256_lf(lexicon_path)
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    pool = eligible_ids(preview)
    ids = select(pool, seed_hex, size)
    by_id = {row["statement_id"]: row for row in preview["statements"]}
    return {
        "selection_id": "foreign_voice.b0d_ids.v1",
        "registered": "2026-08-24",
        "design": "docs/DESIGN-foreign-voice.md",
        "gate": "B0d — the inverse direction, unpreviewed and the real probe",
        "rule": [
            "pool = every oracle-eligible statement id in "
            "data/foreign_voice/eligibility_preview.json, sorted ascending;",
            "seed = int(sha256_lf(data/foreign_voice/lexicon.json)[:16], 16);",
            "random.Random(seed).shuffle(pool); take the first 100; return them sorted.",
        ],
        "seed_source": "data/foreign_voice/lexicon.json",
        "seed_source_digest": seed_hex,
        "seed_why": (
            "v0.18's C-R1 idiom: a seed someone chose would be a knob; the "
            "table under test is not. The draw is a function of the artifact "
            "being probed, so nobody can shop for an easy hundred."
        ),
        "pool_size": len(pool),
        "sample_size": len(ids),
        "no_hand_picking": (
            "The pool is every oracle-eligible statement with nothing removed, "
            "including the six the lexicon refuses. Excluding them would be "
            "selecting for renderability."
        ),
        "statement_ids": ids,
        "drawn": [
            {
                "statement_id": sid,
                "corpus": by_id[sid]["corpus"],
                "source": by_id[sid]["source"],
                "interpreted": by_id[sid]["interpreted"],
            }
            for sid in ids
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--size", type=int, default=SAMPLE_SIZE)
    args = parser.parse_args(argv)
    report = build(size=args.size)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"seed {report['seed_source_digest'][:16]}  pool {report['pool_size']}  "
          f"drawn {report['sample_size']}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
