#!/usr/bin/env python3
"""Draw the committed Goedel-Pset holdout sample (held-out B, v0.12 item 1).

`ingest_goedel_pset.py` is deliberately aggregate-only: 1.73M statements would
be a ~300 MB extract, so only `experiments/goedel_pset_coverage.json` is
committed. That is fine for measuring grammar reach and useless for authoring
a holdout, which needs the statements themselves.

This script is the missing middle. It reads the four pinned parquets, draws a
seeded sample of unique-covered statements, and commits ONLY those to
`data_sources/derived/goedel_pset/sample.json` — a few thousand rows, small
enough to live in git.

## Why a separate stage, and not a step inside the seed

`check_regeneration.py` runs every `scripts/seed_*.py` on every release and
after every corpus edit. A seed that needs 789 MB of gitignored parquets would
fail for anyone who has not fetched them, and — worse — would be *unrefreshable*
rather than merely stale.

That trap is not hypothetical. v0.11's WOLD reach ledger sat wrong for a whole
release because `ingest_wold.py reach` refuses (correctly) to compute without
its pinned archive, so nobody could refresh it and nothing noticed. The tip
suite caught it only at tag time. The split here is the lesson applied:

    sample_goedel_pset.py   needs the parquets, run once, output committed
    seed_goedel_pset.py     needs nothing but the committed sample

## Determinism

The house convention for a committed selection is `measure_self_grounding`'s:
sort, then shuffle with a fixed seed, then take a prefix. That is what happens
here, over the *sorted* problem ids of the unique-covered set, so the sample is
a pure function of (pinned parquet bytes, SAMPLE_SEED, SAMPLE_TARGET) and does
not depend on parquet row order, dict iteration, or filesystem order.

Deduplication keys on `_goal_key` — the same blake2b-128 of the normalized goal
the coverage ledger already uses for its 24.1% duplicate rate — so "unique"
means here exactly what it means there. First occurrence in (file, row) order
wins, which is deterministic given pinned bytes.

Two passes, on purpose. Pass 1 keeps only `goal_key -> problem_id`, which is a
few tens of MB; holding 563k parsed statement dicts to avoid a second pass would
cost hundreds. Pass 2 re-reads and serializes only the chosen ids.

## What is NOT filtered here

The sample is drawn from statements the coverage instrument admits
(`full_ok`), **not** from statements the emitter is known to accept. Filtering
on the emitter would make its success rate 100% by construction and destroy the
measurement. The emitter runs in the seed, and its refusals are counted there —
design §3: "target 2,048, or whatever the emitter actually emits — counted, not
padded."

Usage (repo root, PYTHONIOENCODING=utf-8 on Windows):

    python scripts/fetch_sources.py --fetch hf-goedel-pset-v1
    python scripts/sample_goedel_pset.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grammar_coverage as gc  # noqa: E402
from ingest_goedel_pset import (  # noqa: E402
    ARCHIVE_DIR,
    MANIFEST_SOURCE_ID,
    _goal_key,
    _load_manifest_source,
    _sha256_file,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "data_sources" / "derived" / "goedel_pset" / "sample.json"

# Frozen with the design. Changing either changes which statements are in the
# holdout, which changes the curve -- so they are constants, not flags.
SAMPLE_SEED = 20260816
SAMPLE_TARGET = 2048

ATTRIBUTION = (
    "Goedel-Pset-v1 (c) Goedel-LM, MIT License. Formalized by Goedel-Prover "
    "(Lin et al., 2025, arXiv:2502.07640); problems from NuminaMath. Proofs "
    "are `sorry` (unverified). A seeded 2,048-statement sample of the "
    "unique-covered subset; statement signatures only, proofs omitted."
)


def _verify_archives(files: list[dict]) -> int:
    for fmeta in files:
        path = ARCHIVE_DIR / fmeta["filename"]
        if not path.exists():
            print(
                f"MISSING: {path}. Fetch first:\n"
                f"  python scripts/fetch_sources.py --fetch {MANIFEST_SOURCE_ID}",
                file=sys.stderr,
            )
            return 2
        digest = _sha256_file(path)
        if digest != fmeta["sha256"]:
            print(
                f"SHA MISMATCH for {fmeta['filename']}: expected "
                f"{fmeta['sha256']}, got {digest}. Refusing.",
                file=sys.stderr,
            )
            return 3
    return 0


def run() -> int:
    src = _load_manifest_source()
    files = src["files"]
    rc = _verify_archives(files)
    if rc:
        return rc

    import pyarrow.parquet as pq  # extract-stage-only dependency

    # ---- pass 1: which unique-covered ids exist -------------------------
    seen_keys: set[bytes] = set()
    covered_ids: list[str] = []
    rows = 0
    for fmeta in files:
        pf = pq.ParquetFile(ARCHIVE_DIR / fmeta["filename"])
        for batch in pf.iter_batches(
            columns=["problem_id", "formal_statement"], batch_size=8192
        ):
            ids = batch.column("problem_id").to_pylist()
            stmts = batch.column("formal_statement").to_pylist()
            for pid, formal in zip(ids, stmts):
                rows += 1
                st = gc.parse_lean4_theorem(pid, formal or "")
                if st is None:
                    continue
                if not gc.classify(st)["full_ok"]:
                    continue
                key = _goal_key(st)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                covered_ids.append(pid)

    if len(covered_ids) < SAMPLE_TARGET:
        print(
            f"REFUSING: only {len(covered_ids)} unique-covered statements, "
            f"fewer than the {SAMPLE_TARGET} target. Padding a holdout would "
            "make its size a choice rather than a measurement.",
            file=sys.stderr,
        )
        return 5

    # House convention: sort, shuffle with a fixed seed, take the prefix.
    ordered = sorted(covered_ids)
    random.Random(SAMPLE_SEED).shuffle(ordered)
    chosen = set(ordered[:SAMPLE_TARGET])

    # ---- pass 2: serialize just the chosen ------------------------------
    picked: dict[str, dict] = {}
    for fmeta in files:
        pf = pq.ParquetFile(ARCHIVE_DIR / fmeta["filename"])
        for batch in pf.iter_batches(
            columns=["problem_id", "formal_statement"], batch_size=8192
        ):
            ids = batch.column("problem_id").to_pylist()
            stmts = batch.column("formal_statement").to_pylist()
            for pid, formal in zip(ids, stmts):
                if pid not in chosen or pid in picked:
                    continue
                st = gc.parse_lean4_theorem(pid, formal or "")
                if st is None:
                    continue
                picked[pid] = st

    missing = chosen - set(picked)
    if missing:
        print(
            f"REFUSING: {len(missing)} chosen ids did not re-parse on the "
            "second pass; the two passes disagree.",
            file=sys.stderr,
        )
        return 6

    statements = [picked[pid] for pid in sorted(picked)]
    doc = {
        "generated_by": "scripts/sample_goedel_pset.py",
        "design": "docs/DESIGN-heldout-recovery.md",
        "role": "held-out B (scale) — seeded sample, not the whole corpus",
        "source": {
            "id": src["id"],
            "url": src["url"],
            "hf_repo": src["hf_repo"],
            "hf_revision": src["hf_revision"],
            "license": src["license"],
            "attribution": ATTRIBUTION,
            "files": [
                {"filename": f["filename"], "sha256": f["sha256"]} for f in files
            ],
        },
        "selection": {
            "rows_scanned": rows,
            "unique_covered_available": len(covered_ids),
            "seed": SAMPLE_SEED,
            "target": SAMPLE_TARGET,
            "method": "sort problem_ids, shuffle with seed, take prefix",
            "dedup_key": "blake2b-128 of the whitespace-normalized goal "
            "(same key as experiments/goedel_pset_coverage.json)",
            "emitter_filtered": False,
        },
        "statement_count": len(statements),
        "statements": statements,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    gc.write_json(OUT_PATH, doc)
    print(
        f"sample OK -> {gc.rel(OUT_PATH)}\n"
        f"  scanned {rows} rows; {len(covered_ids)} unique-covered available; "
        f"drew {len(statements)} at seed {SAMPLE_SEED}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
