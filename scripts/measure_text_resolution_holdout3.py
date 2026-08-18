#!/usr/bin/env python3
"""Score v0.13 holdout 3 exactly once.

Predictions C3-1--C3-4 and the complete row set are frozen in
docs/DESIGN-coverage-holdout3.md before this program is run. The output keeps
every row, including misses and wrong binds. The candidate-commit version of
this file emitted every blind candidate and its recovered immutable output is
`text_resolution_holdout3_result.raw.json`. This post-adjudication version
emits the separate compact view: exact count plus the first 25 ids.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import records  # noqa: E402
from resolver import ASK, BIND, default_index, resolve  # noqa: E402

SPEC = REPO / "experiments" / "text_resolution_holdout3.json"
DEFAULT_OUT = REPO / "experiments" / "text_resolution_holdout3_result.json"
_WORD = re.compile(r"[a-z0-9_]+")
_STOP = frozenset("a an the is are of in on at to for from by with and or".split())


def _tokens(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


def _blind_candidates(text: str, corpus: dict) -> tuple[str, ...]:
    """Capability-blind title overlap: no graph, lexicon, or morphology."""
    asked = _tokens(text)
    scores = {
        sid: len(asked & _tokens(str(node.get("title", ""))))
        for sid, (node, _corpus_id) in corpus.items()
    }
    best = max(scores.values(), default=0)
    if best == 0:
        return ()
    return tuple(sorted(sid for sid, score in scores.items() if score == best))


def run(out_path: Path = DEFAULT_OUT) -> dict:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    index = default_index()
    corpus = records()
    rows: list[dict] = []
    groups: dict[str, list[dict]] = defaultdict(list)

    for query in spec["queries"]:
        text, target, group = query["text"], query["target"], query["group"]
        if target not in corpus:
            raise ValueError(f"registered target is not committed: {target}")
        outcome = resolve(text, index)
        blind = _blind_candidates(text, corpus)
        row = {
            "text": text,
            "target": target,
            "group": group,
            "kind": outcome.kind,
            "resolver": outcome.resolver,
            "reached": outcome.kind in {BIND, ASK},
            "target_recalled": target in outcome.candidates,
            "wrong_bind": outcome.kind == BIND and outcome.bound != target,
            "bound": outcome.bound,
            "candidates": list(outcome.candidates),
            "blind_target_recalled": target in blind,
            "detail": outcome.detail,
            "blind_candidate_count": len(blind),
            "blind_candidates_preview": list(blind[:25]),
        }
        rows.append(row)
        groups[group].append(row)

    total = len(rows)
    reached = sum(row["reached"] for row in rows)
    recalled = sum(row["target_recalled"] for row in rows)
    wrong = sum(row["wrong_bind"] for row in rows)
    blind_recalled = sum(row["blind_target_recalled"] for row in rows)
    coverage = reached / total
    target_recall = recalled / total
    blind_recall = blind_recalled / total

    result = {
        "schema": "text_resolution_holdout3.v1",
        "design": "docs/DESIGN-coverage-holdout3.md",
        "spec": "experiments/text_resolution_holdout3.json",
        "graph_nodes": index.size,
        "adjudication": {
            "C3-1": {"fired": coverage >= 0.875, "coverage": round(coverage, 4),
                     "reached": reached, "of": total, "threshold": 0.875},
            "C3-2": {"fired": target_recall >= 0.833,
                     "target_recall": round(target_recall, 4),
                     "recalled": recalled, "of": total, "threshold": 0.833},
            "C3-3": {"fired": wrong == 0, "wrong_binds": wrong},
            "C3-4": {"fired": blind_recall < 1.0 and blind_recall < target_recall,
                     "blind_target_recall": round(blind_recall, 4),
                     "resolver_target_recall": round(target_recall, 4)},
        },
        "groups": {
            name: {
                "reached": sum(row["reached"] for row in members),
                "target_recalled": sum(row["target_recalled"] for row in members),
                "of": len(members),
            }
            for name, members in sorted(groups.items())
        },
        "rows": rows,
    }
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = run()
    print(json.dumps(result["adjudication"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
