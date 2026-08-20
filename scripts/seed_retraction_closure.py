#!/usr/bin/env python3
"""Seed the blind control's 100 shuffle seeds (DESIGN-retraction-closure §6).

The control is the clause that can kill the capability: 100 degree-preserving,
kind-preserving edge shuffles of the real graph, each run against both live
drift roots, and *if one or more of the 100 shuffled graphs satisfies R2 on
both roots, the real edges carry no consequence-relevant information and this
capability is void.* A control with that much authority cannot be seeded from
the clock, from ``random`` without a seed, or from anything chosen after a
shuffle was seen to behave — so the seeds are committed BEFORE the assembler,
the radius tool, or the shuffler exist, and they are derived rather than drawn:

    seed_i = int.from_bytes(
        sha256(b'retraction-closure-shuffle-' + str(i).encode()).digest()[:4],
        'big')                                                  for i in 0..99

The rule travels inside the emitted file as well as here, so a reader can
recompute all 100 values without this script and confirm nothing was swapped.
There is no randomness anywhere in this file, and that is the point: a
committed list of opaque integers is only as trustworthy as its derivation.

This script owns the seeds file and nothing else in its directory. The two
hand-audited R2 ground-truth lists that sit beside it are adjudicated INPUTS,
not generated output: a program that could regenerate the list of published
claims a stale ledger touched would be deciding, rather than recording, what
the project has claimed. ``tests/test_retraction_closure.py`` asserts that
separation rather than trusting this paragraph.

Byte-idempotent by house rule (`check_regeneration.py` runs every
``scripts/seed_*.py`` and reports any resulting diff as DRIFT), so this script
writes the same bytes on every run and on every host.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "retraction_closure"
OUT_PATH = OUT_DIR / "shuffle_seeds.json"

SCHEMA_TAG = "retraction-shuffle-seeds/1"

#: Design §6's control size. Frozen: a control resized after seeing its own
#: outcome is not a control.
SHUFFLE_COUNT = 100

#: The domain-separating prefix. Any other prefix yields a different list, so
#: it is data here rather than an inline literal at the one call site.
SEED_PREFIX = b"retraction-closure-shuffle-"

#: The derivation, stated in the emitted file verbatim so the committed
#: integers can be rechecked without running this script.
SEED_RULE = (
    "seed_i = int.from_bytes(sha256(b'retraction-closure-shuffle-' + "
    "str(i).encode()).digest()[:4], 'big') for i in 0..99"
)


def shuffle_seed(index: int) -> int:
    """The i-th control seed. A 32-bit value: the first four digest bytes,
    big-endian, which is what the rule string in the file says and what a
    reader will recompute."""
    digest = hashlib.sha256(SEED_PREFIX + str(index).encode("ascii")).digest()
    return int.from_bytes(digest[:4], "big")


def build() -> dict:
    """The committed object, in full."""
    return {
        "schema": SCHEMA_TAG,
        "rule": SEED_RULE,
        "seeds": [shuffle_seed(i) for i in range(SHUFFLE_COUNT)],
    }


def render(obj: dict) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(render(build()), encoding="utf-8")
    print(f"wrote {SHUFFLE_COUNT} shuffle seed(s) to {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
