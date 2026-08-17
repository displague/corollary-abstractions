#!/usr/bin/env python3
"""Resolution at corpus scale, with ground truth the corpus supplies.

The hand-authored query set is 40 items I wrote myself. A perfect score on
it is weak evidence: I chose the questions, and I knew what was in the
graph. This is the harder measurement, and it is automatic.

**The test.** For every node, use the node's own TITLE as the query and ask
whether the chain returns that node. Ground truth is the id it came from, so
there is nothing to hand-label and nothing to argue about.

**What it measures, stated honestly.** This is *discrimination*, not
generalization. A title is indexed, so retrieval is expected; the question is
whether the graph can tell its own statements APART when asked in their own
words. A corpus where every title resolves to a unique node is one a person
can navigate. A corpus where titles collapse into big candidate sets is one
where asking is the only honest answer, and the size of those sets is the
data a ranker would have to earn its place against.

It is **not** evidence that unseen phrasings work. Only the hand-authored set
speaks to that, and it speaks quietly, from 40 examples.

## Registered predictions (written before this script was first run)

- **S1 (discrimination).** At least **60%** of curated nodes BIND to
  themselves from their own title. Curated titles are written by a person to
  name one statement, so most should be unique; the ones that are not will
  be families like "Factorial, Recursive" vs "Factorial, Iterative", which
  *should* be ambiguous and where asking is correct.
- **S2 (no wrong binds).** Of nodes that BIND, at least **95%** bind to
  THEMSELVES rather than to some other node. A confident wrong answer is the
  failure that matters; a large ASK set is merely unhelpful.
- **S3 (ingested nodes are the hard case).** Ingested nodes BIND to
  themselves at a strictly LOWER rate than curated ones, because 12,514 of
  them share a formulaic title of the form "<name> (Ingested, Emitted
  Skeleton, Formal Without Bridge)". If this misses, the titles are more
  distinctive than expected and the ingested layer is more navigable than
  the design assumed.
- **S4 (speed at scale).** The whole sweep runs in under 120 seconds on one
  CPU core, index build included. The claim that this fits small hardware
  should be checked at 12,777 queries, not at 40.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import records  # noqa: E402
from resolver import ASK, BIND, PASS, default_index, resolve  # noqa: E402

DEFAULT_OUT = REPO / "experiments" / "resolution_scale.json"

try:
    from decompose import INGESTED_CORPUS_PREFIXES
except ImportError:  # pragma: no cover
    INGESTED_CORPUS_PREFIXES = ("lean_workbook", "ingested_arithmetic")


def run(out_path: Path, limit: int | None = None) -> dict:
    index = default_index()
    corpus = records()
    started = time.perf_counter()

    buckets: dict[str, Counter] = {
        "curated": Counter(), "ingested": Counter(),
    }
    ask_sizes: dict[str, list[int]] = {"curated": [], "ingested": []}
    wrong_binds: list[dict] = []
    items = list(corpus.items())
    if limit:
        items = items[:limit]

    for sid, (node, corpus_id) in items:
        title = str(node.get("title", "")).strip()
        if not title:
            continue
        kind = (
            "ingested"
            if corpus_id.startswith(tuple(INGESTED_CORPUS_PREFIXES))
            else "curated"
        )
        outcome = resolve(title, index)
        if outcome.kind == BIND:
            if outcome.bound == sid:
                buckets[kind]["bind_self"] += 1
            else:
                buckets[kind]["bind_other"] += 1
                if len(wrong_binds) < 25:
                    wrong_binds.append(
                        {"asked_for": sid, "got": outcome.bound,
                         "title": title, "resolver": outcome.resolver}
                    )
        elif outcome.kind == ASK:
            ask_sizes[kind].append(len(outcome.candidates))
            if sid in outcome.candidates:
                buckets[kind]["ask_contains_self"] += 1
            else:
                buckets[kind]["ask_missing_self"] += 1
        else:
            buckets[kind]["pass"] += 1
        buckets[kind]["total"] += 1

    elapsed = time.perf_counter() - started

    def rate(kind: str, key: str) -> float:
        total = buckets[kind]["total"]
        return (buckets[kind][key] / total) if total else 0.0

    def summarise(kind: str) -> dict:
        sizes = sorted(ask_sizes[kind])
        binds = buckets[kind]["bind_self"] + buckets[kind]["bind_other"]
        return {
            "total": buckets[kind]["total"],
            "bind_self": buckets[kind]["bind_self"],
            "bind_other": buckets[kind]["bind_other"],
            "ask_contains_self": buckets[kind]["ask_contains_self"],
            "ask_missing_self": buckets[kind]["ask_missing_self"],
            "pass": buckets[kind]["pass"],
            "bind_self_rate": round(rate(kind, "bind_self"), 4),
            "bind_precision": (
                round(buckets[kind]["bind_self"] / binds, 4) if binds else None
            ),
            "ask_median_candidates": (
                sizes[len(sizes) // 2] if sizes else None
            ),
            "ask_max_candidates": (sizes[-1] if sizes else None),
        }

    curated, ingested = summarise("curated"), summarise("ingested")
    result = {
        "schema": "resolution_scale.v1",
        "measures": "discrimination (title -> own node), not generalization",
        "graph_nodes": index.size,
        "queries": curated["total"] + ingested["total"],
        "seconds": round(elapsed, 2),
        "curated": curated,
        "ingested": ingested,
        "wrong_bind_samples": wrong_binds,
        "adjudication": {
            "S1": {
                "fired": curated["bind_self_rate"] >= 0.60,
                "curated_bind_self_rate": curated["bind_self_rate"],
                "threshold": 0.60,
            },
            "S2": {
                "fired": (curated["bind_precision"] or 0) >= 0.95,
                "curated_bind_precision": curated["bind_precision"],
                "threshold": 0.95,
            },
            "S3": {
                "fired": ingested["bind_self_rate"] < curated["bind_self_rate"],
                "ingested_bind_self_rate": ingested["bind_self_rate"],
                "curated_bind_self_rate": curated["bind_self_rate"],
            },
            "S4": {"fired": elapsed < 120.0, "seconds": round(elapsed, 2)},
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)
    result = run(args.out, args.limit)
    print(json.dumps({
        "wrote": str(args.out),
        "queries": result["queries"],
        "seconds": result["seconds"],
        "curated": result["curated"],
        "ingested": result["ingested"],
        "adjudication": result["adjudication"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
