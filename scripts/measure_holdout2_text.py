#!/usr/bin/env python3
"""R1–R4: the held-out text set, scored exactly once.

## Why this exists

T1–T4 and S1–S5 were registered honestly, but every failure they found was
then fixed — which makes the first query set a DEVELOPMENT set. A threshold
that a fix was aimed at is not evidence about unseen input, and the standing
misses (T2 0.9167, S2 0.9385, S5 0.8127) cannot be repaired by re-running
the same queries against repaired code.

So this applies the discipline the project already uses on its corpus: a
holdout. `experiments/text_resolution_holdout2.json` was authored in one
pass, committed before being run, and is disjoint from the development set.
It routes through `harness.route_line` — the real prompt, every route — not
through the resolver alone.

## Registered predictions, frozen before the first run

- **R1 (coverage).** >= 85% of `resolve` queries reach a statement. Lower
  than the development set's observed 1.0 on purpose: these phrasings were
  never checked, and a holdout that matched a tuned set exactly would be
  evidence of leakage rather than of quality.
- **R2 (refusal).** >= 90% of `refuse` queries reach neither a statement nor
  a dictionary sense. This is the one that must hold: claiming something the
  corpus does not contain is the failure that makes a resolver worse than
  nothing.
- **R3 (computation).** 100% of `compute` queries are answered by exact
  arithmetic. Arithmetic has no coverage excuse — either the expression was
  found and evaluated, or the reader was told what was missing.
- **R4 (definition).** >= 75% of `define` queries reach a dictionary sense
  when the WordNet archive is present, and the arm is SKIPPED, not scored,
  when it is absent.

R2 and R3 are the load-bearing pair. R1 missing means coverage needs work;
R2 or R3 missing means the thing is unsafe, and no coverage number redeems
that.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from gloss import archive_path  # noqa: E402
from harness import CoreSession, route_line  # noqa: E402

QUERIES = REPO / "experiments" / "text_resolution_holdout2.json"
DEFAULT_OUT = REPO / "experiments" / "text_resolution_holdout2_result.json"

#: Routes that count as "reached a statement in this corpus".
CORPUS_ROUTES = {"resolver", "statement"}


def run(out_path: Path) -> dict:
    spec = json.loads(QUERIES.read_text(encoding="utf-8"))
    session = CoreSession.boot(REPO, offline=False)
    have_wordnet = archive_path() is not None

    rows: list[dict] = []
    started = time.perf_counter()
    for query in spec["queries"]:
        text, expect = query["text"], query["expect"]
        verdict = route_line(REPO, session, text)
        route, status = verdict["route"], verdict["status"]
        if expect == "resolve":
            ok = route in CORPUS_ROUTES
        elif expect == "refuse":
            ok = route not in CORPUS_ROUTES | {"gloss", "evaluate"}
        elif expect == "compute":
            ok = route == "evaluate"
        else:  # define
            ok = route == "gloss"
        rows.append({
            "text": text, "expect": expect, "route": route,
            "status": status, "ok": ok,
            "detail": verdict.get("detail", "")[:120],
        })
    elapsed = time.perf_counter() - started

    def arm(name: str) -> tuple[int, int]:
        subset = [r for r in rows if r["expect"] == name]
        return sum(1 for r in subset if r["ok"]), len(subset)

    res_ok, res_n = arm("resolve")
    ref_ok, ref_n = arm("refuse")
    cmp_ok, cmp_n = arm("compute")
    def_ok, def_n = arm("define")

    adjudication = {
        "R1": {
            "fired": (res_ok / res_n if res_n else 0) >= 0.85,
            "coverage": round(res_ok / res_n, 4) if res_n else None,
            "threshold": 0.85, "reached": res_ok, "of": res_n,
        },
        "R2": {
            "fired": (ref_ok / ref_n if ref_n else 0) >= 0.90,
            "refusal": round(ref_ok / ref_n, 4) if ref_n else None,
            "threshold": 0.90, "refused": ref_ok, "of": ref_n,
        },
        "R3": {
            "fired": cmp_ok == cmp_n,
            "computed": cmp_ok, "of": cmp_n, "threshold": 1.0,
        },
        "R4": (
            {
                "fired": (def_ok / def_n if def_n else 0) >= 0.75,
                "defined": def_ok, "of": def_n, "threshold": 0.75,
            }
            if have_wordnet
            else {"skipped": "no WordNet archive; arm not scored"}
        ),
    }
    result = {
        "schema": "text_resolution_holdout.v1",
        "design": "docs/DESIGN-text-resolution.md",
        "note": "held out; authored and committed before the first run",
        "wordnet_present": have_wordnet,
        "queries": len(rows),
        "seconds": round(elapsed, 2),
        "adjudication": adjudication,
        "rows": rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    result = run(args.out)
    print(json.dumps(result["adjudication"], indent=2))
    misses = [r for r in result["rows"] if not r["ok"]]
    if misses:
        print("\nmisses:")
        for row in misses:
            print(f"  [{row['expect']}] {row['text']}")
            print(f"      -> {row['route']}/{row['status']}: {row['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
