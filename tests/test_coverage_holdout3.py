#!/usr/bin/env python3
"""Integrity checks for the spent v0.13 item-1 ledgers.

These tests do not rescore either holdout. They guard the exact one-shot rows,
archive identity, and fired/missed adjudications that the docs publish.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from copy import deepcopy
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
RAW_PATH = ROOT / "experiments" / "text_resolution_holdout3_result.raw.json"
RAW = json.loads(RAW_PATH.read_text(encoding="utf-8"))
PROVENANCE = json.loads(
    (ROOT / "experiments" / "text_resolution_holdout3_provenance.json").read_text(
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
    def test_raw_ledger_has_the_recovered_identity(self) -> None:
        raw = RAW_PATH.read_bytes()
        self.assertEqual(len(raw), 749574)
        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            "ffa68c7659c36a589f37e04a679d195b62c074cd564ca20f2ce7feb5c90b4532",
        )
        self.assertEqual(
            PROVENANCE["raw_one_shot_ledger"]["git_blob"],
            "16abf1c51f449a3067b562d1dbeb9c7ae0871804",
        )

    def test_derived_and_false_positive_file_digests(self) -> None:
        for section in ("compact_view", "false_positive_ledger"):
            entry = PROVENANCE[section]
            actual = hashlib.sha256(
                (ROOT / entry["path"]).read_bytes()
            ).hexdigest()
            self.assertEqual(actual, entry["sha256"])

    def test_compact_ledger_is_only_a_view_of_raw(self) -> None:
        raw = deepcopy(RAW)
        compact = deepcopy(HOLDOUT)
        self.assertEqual(raw.keys(), compact.keys())
        for key in raw:
            if key != "rows":
                self.assertEqual(raw[key], compact[key])
        for raw_row, compact_row in zip(raw["rows"], compact["rows"], strict=True):
            blind = raw_row.pop("blind_candidates")
            self.assertEqual(
                compact_row.pop("blind_candidate_count"), len(blind)
            )
            self.assertEqual(
                compact_row.pop("blind_candidates_preview"), blind[:25]
            )
            self.assertEqual(raw_row, compact_row)

    def test_preregister_and_candidate_git_objects_exist(self) -> None:
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"], cwd=ROOT,
                check=True, capture_output=True, text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            self.skipTest("Git object database unavailable in packaged tree")
        prereg = PROVENANCE["preregister"]
        candidate = PROVENANCE["candidate_implementation"]
        expected = (
            ("110fff4c06bdbe0fcb31cc8606ec29ed9502f6f1^{tree}", prereg["tree"]),
            ("7a9c7c344fab7e6a3986be3ff224e6833a4a8052^{tree}", candidate["tree"]),
            (
                "110fff4c06bdbe0fcb31cc8606ec29ed9502f6f1:"
                "experiments/text_resolution_holdout3.json",
                prereg["spec_blob"],
            ),
            (
                "7a9c7c344fab7e6a3986be3ff224e6833a4a8052:scripts/resolver.py",
                candidate["resolver_blob"],
            ),
            (
                "7a9c7c344fab7e6a3986be3ff224e6833a4a8052:"
                "scripts/measure_text_resolution_holdout3.py",
                candidate["holdout_scorer_blob"],
            ),
            (
                "7a9c7c344fab7e6a3986be3ff224e6833a4a8052:"
                "scripts/measure_false_positive_f4.py",
                candidate["false_positive_scorer_blob"],
            ),
        )
        for ref, oid in expected:
            with self.subTest(ref=ref):
                actual = subprocess.run(
                    ["git", "rev-parse", ref], cwd=ROOT, check=True,
                    capture_output=True, text=True,
                ).stdout.strip()
                self.assertEqual(actual, oid)
        raw_blob = subprocess.run(
            ["git", "hash-object", "--no-filters", RAW_PATH], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(raw_blob, PROVENANCE["raw_one_shot_ledger"]["git_blob"])

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
