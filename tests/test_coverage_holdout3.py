#!/usr/bin/env python3
"""Integrity checks for the spent v0.13 item-1 ledgers.

These tests do not rescore either holdout. They guard the exact one-shot rows,
archive identity, and fired/missed adjudications that the docs publish.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = json.loads(
    (ROOT / "experiments" / "text_resolution_holdout3.json").read_text(
        encoding="utf-8"
    )
)
HOLDOUT = json.loads(
    (ROOT / "experiments" / "text_resolution_holdout3_result.json").read_text(
        encoding="utf-8"
    )
)
F4 = json.loads(
    (ROOT / "experiments" / "false_positive_rate_f4.json").read_text(
        encoding="utf-8"
    )
)
MANIFEST = json.loads(
    (ROOT / "data_sources" / "manifest.json").read_text(encoding="utf-8")
)


class HoldoutThreeLedger(unittest.TestCase):
    def test_result_rows_are_exactly_the_registered_rows(self) -> None:
        registered = [
            (row["text"], row["target"], row["group"]) for row in SPEC["queries"]
        ]
        scored = [
            (row["text"], row["target"], row["group"])
            for row in HOLDOUT["rows"]
        ]
        self.assertEqual(scored, registered)
        self.assertEqual(len(scored), 24)
        self.assertEqual(len(set(scored)), 24)

    def test_fired_and_missed_predictions_stay_honest(self) -> None:
        adj = HOLDOUT["adjudication"]
        self.assertEqual(
            (adj["C3-1"]["reached"], adj["C3-1"]["of"]), (24, 24)
        )
        self.assertEqual(
            (adj["C3-2"]["recalled"], adj["C3-2"]["of"]), (23, 24)
        )
        self.assertTrue(adj["C3-1"]["fired"])
        self.assertTrue(adj["C3-2"]["fired"])
        self.assertFalse(adj["C3-3"]["fired"])
        self.assertEqual(adj["C3-3"]["wrong_binds"], 1)
        self.assertTrue(adj["C3-4"]["fired"])
        self.assertEqual(
            max(row["blind_candidate_count"] for row in HOLDOUT["rows"]), 14571
        )

    def test_wrong_bind_is_named_not_rounded_away(self) -> None:
        wrong = [row for row in HOLDOUT["rows"] if row["wrong_bind"]]
        self.assertEqual(len(wrong), 1)
        self.assertEqual(
            wrong[0]["text"], "interest accumulated without compounding"
        )
        self.assertEqual(
            wrong[0]["bound"], "economics.finance.continuous_compounding"
        )


class FreshFalsePositiveLedger(unittest.TestCase):
    def test_archive_digest_is_the_manifest_pin(self) -> None:
        pin = next(
            source["sha256"] for source in MANIFEST["sources"]
            if source["id"] == "wordnet-2025-json"
        )
        self.assertEqual(F4["archive_sha256"], pin)

    def test_f4_miss_and_all_claims_are_retained(self) -> None:
        self.assertEqual(F4["seed"], 20260818)
        self.assertEqual(F4["sampled"], 1000)
        self.assertEqual(F4["claimed"], 34)
        self.assertEqual(len(F4["claimed_samples"]), 34)
        self.assertEqual(F4["false_positive_rate"], 0.034)
        self.assertFalse(F4["adjudication"]["F4"]["fired"])
        self.assertEqual(F4["adjudication"]["F4"]["threshold"], 0.03)


if __name__ == "__main__":
    unittest.main()
