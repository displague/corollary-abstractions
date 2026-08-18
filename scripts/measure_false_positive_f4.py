#!/usr/bin/env python3
"""Fresh v0.13 false-positive sample, registered before the only run.

F4: on 1,000 mechanically sampled, unscreened Open English WordNet 2025
examples/glosses at seed 20260818, at most 3.0% reach a corpus statement.
The threshold is v0.12's shipping F3 rate. The archive digest is pinned by
data_sources/manifest.json and checked before sampling.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from gloss import archive_path  # noqa: E402
from resolver import ASK, BIND, default_index, resolve  # noqa: E402
from wordnet_store import WordNetIndex  # noqa: E402

DEFAULT_OUT = REPO / "experiments" / "false_positive_rate_f4.json"
SAMPLE_SEED = 20260818
SAMPLE_SIZE = 1000
THRESHOLD = 0.030
ARCHIVE_SHA256 = "7d749f6e2c39e6970e4997839dcf6e42fd281f3c2fae0171d2192bae8cfa4b51"


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sentences(archive: Path) -> list[str]:
    index = WordNetIndex.load(archive)
    pool: list[str] = []
    for synset_id in sorted(index.synsets):
        synset = index.synsets[synset_id]
        for text in (*synset.examples, *synset.definitions):
            cleaned = " ".join(str(text).split())
            if 20 <= len(cleaned) <= 120:
                pool.append(cleaned)
                break
    random.Random(SAMPLE_SEED).shuffle(pool)
    return pool[:SAMPLE_SIZE]


def run(out_path: Path = DEFAULT_OUT) -> dict:
    archive = archive_path()
    if archive is None:
        raise RuntimeError("set COROLLARY_WORDNET to the pinned OEWN 2025 archive")
    digest = _digest(archive)
    if digest != ARCHIVE_SHA256:
        raise RuntimeError(f"WordNet digest mismatch: {digest}")
    texts = sentences(archive)
    if len(texts) != SAMPLE_SIZE:
        raise RuntimeError(f"expected {SAMPLE_SIZE} samples, got {len(texts)}")

    index = default_index()
    claimed: list[dict] = []
    for text in texts:
        outcome = resolve(text, index)
        if outcome.kind in {BIND, ASK}:
            claimed.append({
                "text": text,
                "kind": outcome.kind,
                "detail": outcome.detail,
                "bound": outcome.bound,
                "candidates": list(outcome.candidates),
            })
    rate = len(claimed) / len(texts)
    result = {
        "schema": "false_positive_rate.v2",
        "design": "docs/DESIGN-coverage-holdout3.md",
        "source": "Open English WordNet 2025 examples/glosses, unscreened",
        "archive_sha256": digest,
        "seed": SAMPLE_SEED,
        "sampled": len(texts),
        "claimed": len(claimed),
        "false_positive_rate": round(rate, 4),
        "adjudication": {
            "F4": {"fired": rate <= THRESHOLD, "rate": round(rate, 4),
                   "threshold": THRESHOLD}
        },
        "claimed_samples": claimed,
    }
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = run()
    print(json.dumps({k: v for k, v in result.items() if k != "claimed_samples"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
