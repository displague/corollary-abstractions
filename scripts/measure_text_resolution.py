#!/usr/bin/env python3
"""T1–T4 of docs/DESIGN-text-resolution.md, closed-form over the query set.

Runs every committed query through the same chain the prompt uses, then
adjudicates the four registered predictions. Fired and missed both land.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import compose, records  # noqa: E402
from answer import render as render_answer  # noqa: E402
from resolver import ASK, BIND, PASS, default_index, reduce_text, resolve  # noqa: E402

QUERIES = REPO / "experiments" / "text_resolution_queries.json"
DEFAULT_OUT = REPO / "experiments" / "text_resolution.json"
_WORD = re.compile(r"[a-z0-9_]+")


def _prose_of(node: dict) -> str:
    semantic = node.get("semantic_interpretation") or {}
    return " ".join(
        str(x) for x in (
            node.get("title", ""),
            semantic.get("statement_meaning", ""),
            " ".join(node.get("keywords") or []),
        )
    ).lower()


def run(out_path: Path) -> dict:
    spec = json.loads(QUERIES.read_text(encoding="utf-8"))
    index = default_index()
    corpus = records()

    rows: list[dict] = []
    t0 = time.perf_counter()
    for query in spec["queries"]:
        text, expect = query["text"], query["expect"]
        outcome = resolve(text, index)
        reached = outcome.kind in {BIND, ASK}
        row = {
            "text": text,
            "expect": expect,
            "kind": outcome.kind,
            "resolver": outcome.resolver,
            "reached": reached,
            "candidates": len(outcome.candidates),
            "bound": outcome.bound,
            "ok": (reached if expect == "resolve" else outcome.kind == PASS),
        }
        # T3: a BIND must be able to show its words in the bound node's prose.
        if outcome.kind == BIND and outcome.bound in corpus:
            node, _cid = corpus[outcome.bound]
            prose = set(_WORD.findall(_prose_of(node)))
            asked = set(reduce_text(text))
            shown = sorted(asked & prose)
            row["words_shown"] = shown
            row["words_asked"] = sorted(asked)
            row["shows_its_words"] = bool(shown)
        # T4: every rendered sentence must appear verbatim in the corpus.
        if outcome.kind == BIND:
            answer = compose(outcome.bound or "")
            if answer is not None:
                quoted = [answer.title, answer.meaning]
                node, _cid = corpus.get(outcome.bound, ({}, ""))
                blob = json.dumps(node, ensure_ascii=False)
                row["quotes_verbatim"] = all(
                    (not s) or (s in blob) for s in quoted
                )
                row["answer_lines"] = len(render_answer(answer))
        rows.append(row)
    elapsed = time.perf_counter() - t0

    res = [r for r in rows if r["expect"] == "resolve"]
    ref = [r for r in rows if r["expect"] == "refuse"]
    binds = [r for r in res if r["kind"] == BIND]
    coverage = sum(1 for r in res if r["reached"]) / len(res) if res else 0.0
    refusal = sum(1 for r in ref if r["kind"] == PASS) / len(ref) if ref else 0.0
    shows = [r for r in binds if "shows_its_words" in r]
    t3 = all(r["shows_its_words"] for r in shows) if shows else False
    quoting = [r for r in binds if "quotes_verbatim" in r]
    t4 = all(r["quotes_verbatim"] for r in quoting) if quoting else False

    result = {
        "schema": "text_resolution.v1",
        "design": "docs/DESIGN-text-resolution.md",
        "queries": len(rows),
        "resolve_queries": len(res),
        "refuse_queries": len(ref),
        "graph_nodes": index.size,
        "seconds_for_all_queries": round(elapsed, 4),
        "adjudication": {
            "T1": {
                "fired": coverage >= 0.70,
                "coverage": round(coverage, 4),
                "threshold": 0.70,
                "reached": sum(1 for r in res if r["reached"]),
                "of": len(res),
            },
            "T2": {
                "fired": refusal >= 0.90,
                "refusal": round(refusal, 4),
                "threshold": 0.90,
                "passed": sum(1 for r in ref if r["kind"] == PASS),
                "of": len(ref),
            },
            "T3": {
                "fired": t3,
                "binds_checked": len(shows),
                "binds_showing_words": sum(
                    1 for r in shows if r["shows_its_words"]
                ),
            },
            "T4": {
                "fired": t4,
                "binds_checked": len(quoting),
                "binds_quoting_verbatim": sum(
                    1 for r in quoting if r["quotes_verbatim"]
                ),
            },
        },
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
    adj = result["adjudication"]
    print(json.dumps({
        "wrote": str(args.out),
        "T1_coverage": adj["T1"],
        "T2_refusal": adj["T2"],
        "T3_shows_words": adj["T3"],
        "T4_verbatim": adj["T4"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
