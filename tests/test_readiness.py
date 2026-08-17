#!/usr/bin/env python3
"""The v0.13 readiness floor, asserted on the code that actually ships.

## These are NOT predictions, and the difference matters

T1–T4 and S1–S5 were registered before their runs and are the predictions of
record, misses included: **T2 0.9167**, **S2 0.9385**, **S5 0.8127** all fell
short of their thresholds on the runs that scored them. Those numbers do not
move, and nothing here backdates them.

What this file is instead is a **regression floor**. The thresholds below are
set FROM measured values on the shipping code, which makes them worthless as
predictions and useful as a gate: they exist so that a later change cannot
quietly undo what was fixed. Calling them predictions would be exactly the
after-the-fact goalpost-moving this project spends its commit messages
refusing.

Each floor names the failure it was earned by, so a future reader can tell a
threshold that means something from a number someone liked.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import records  # noqa: E402
from resolver import ASK, BIND, default_index, resolve  # noqa: E402

try:
    from decompose import INGESTED_CORPUS_PREFIXES
except ImportError:  # pragma: no cover
    INGESTED_CORPUS_PREFIXES = ("lean_workbook", "ingested_arithmetic")

QUERIES = REPO / "experiments" / "text_resolution_queries.json"


class ReadinessFloor(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = default_index()
        cls.corpus = records()
        cls.spec = json.loads(QUERIES.read_text(encoding="utf-8"))

    def test_arbitrary_text_coverage_holds(self) -> None:
        """Floor 1.000. Earned by the lexicon layer: `greatest common
        divisor` missed until the corpus's own glossary was indexed."""
        rows = [q for q in self.spec["queries"] if q["expect"] == "resolve"]
        reached = sum(
            1 for q in rows if resolve(q["text"], self.index).kind in {BIND, ASK}
        )
        self.assertEqual(reached, len(rows), "a covered query stopped resolving")

    def test_refusal_of_out_of_corpus_text_holds(self) -> None:
        """Floor 1.000. Earned twice: a Monty Python joke binding on
        `velocity`, and `translate this sentence into portuguese` binding to
        a logic node on ['into','sentence']."""
        rows = [q for q in self.spec["queries"] if q["expect"] == "refuse"]
        passed = sum(
            1 for q in rows
            if resolve(q["text"], self.index).kind not in {BIND, ASK}
        )
        self.assertEqual(passed, len(rows), "out-of-corpus text was claimed")

    def test_every_ingested_node_stays_reachable(self) -> None:
        """Floor 1.000, sampled. Earned by S5's miss: whole statements were
        refused because `resolve_expression` rejected relation roots, so
        2,728 ground arithmetic nodes were unreachable by the one query that
        fits them."""
        ingested = [
            (sid, node)
            for sid, (node, cid) in self.corpus.items()
            if cid.startswith(tuple(INGESTED_CORPUS_PREFIXES))
        ]
        self.assertGreater(len(ingested), 1000, "vacuous: no ingested nodes")
        sample = ingested[::200]
        missed = []
        for sid, node in sample:
            template = (node.get("structural_signature") or {}).get(
                "anonymized_template"
            )
            if not isinstance(template, str) or not template:
                continue
            if sid not in resolve(template, self.index).candidates:
                missed.append(sid)
        self.assertEqual(missed, [], f"unreachable ingested nodes: {missed[:5]}")

    def test_curated_statements_stay_discriminable(self) -> None:
        """Floor 0.90 self-bind. Earned by the pooling fix: first-resolver-
        wins bound `Pythagorean Theorem` to the wrong node twelve times."""
        curated = [
            (sid, node)
            for sid, (node, cid) in self.corpus.items()
            if not cid.startswith(tuple(INGESTED_CORPUS_PREFIXES))
        ]
        self.assertGreater(len(curated), 100, "vacuous: no curated nodes")
        bound_self = 0
        bound_other = 0
        for sid, node in curated:
            title = str(node.get("title", "")).strip()
            if not title:
                continue
            outcome = resolve(title, self.index)
            if outcome.kind == BIND:
                if outcome.bound == sid:
                    bound_self += 1
                else:
                    bound_other += 1
        rate = bound_self / len(curated)
        precision = bound_self / max(1, bound_self + bound_other)
        self.assertGreaterEqual(rate, 0.90, f"self-bind fell to {rate:.4f}")
        self.assertGreaterEqual(
            precision, 0.97, f"bind precision fell to {precision:.4f}"
        )

    def test_resolution_stays_fast_enough_for_small_hardware(self) -> None:
        """Floor: 2,000 resolutions in under 5s, single core, no GPU.
        Earned by the claim that this runs on a Pi, which should be checked
        rather than repeated."""
        import time  # noqa: PLC0415

        started = time.perf_counter()
        for _ in range(2000):
            resolve("trigonometry.identities.double_angle_cosine", self.index)
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, 5.0, f"2k resolutions took {elapsed:.2f}s")


if __name__ == "__main__":
    unittest.main()
