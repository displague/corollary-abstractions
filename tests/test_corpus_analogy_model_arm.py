"""Regression pins for the corpus-analogy MODEL ARM reporting harness.

The model number is stochastic (seed/GPU variance) and is deliberately NOT
pinned. What IS pinned: the frozen blind ceilings the arm reports against, that
the harness reads them from the committed table and agrees with them, the
model-vs-ceiling comparison logic (strict `>`, signed margin), the mean/sd
summary, and the artifact's structure -- including which holdout is the strict
release-gate target and which is near-vacuous. If the frozen split moves a
ceiling, `load_frozen_ceilings` breaks here rather than silently re-baselining.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "scripts"))

import corpus_analogy_split as cas  # noqa: E402
import train_corpus_analogy as tca  # noqa: E402


class CeilingPins(unittest.TestCase):
    """The four frozen blind ceilings, pinned to the byte-exact values."""

    def test_expected_ceilings_are_the_disclosed_values(self) -> None:
        self.assertEqual(tca.EXPECTED_BLIND_CEILINGS["family"], 0.4)
        self.assertEqual(tca.EXPECTED_BLIND_CEILINGS["discipline"],
                         0.9318181818181818)
        self.assertEqual(tca.EXPECTED_BLIND_CEILINGS["vocabulary"],
                         0.39759036144578314)
        # the strict release-gate ceiling
        self.assertEqual(tca.EXPECTED_BLIND_CEILINGS["shape"],
                         0.10687022900763359)

    def test_axes_are_exactly_the_frozen_split_names(self) -> None:
        self.assertEqual(set(tca.EXPECTED_BLIND_CEILINGS),
                         set(cas.SPLIT_NAMES))

    def test_strict_and_near_vacuous_labels(self) -> None:
        # shape is the strict ~0.10-0.14 target; discipline is near-vacuous
        self.assertEqual(tca.STRICT_HOLDOUT, "shape")
        self.assertEqual(tca.NEAR_VACUOUS_HOLDOUT, "discipline")

    def test_harness_reads_ceilings_from_committed_table_and_agrees(self) -> None:
        ceilings = tca.load_frozen_ceilings()
        for name, expected in tca.EXPECTED_BLIND_CEILINGS.items():
            self.assertAlmostEqual(ceilings[name], expected, places=12)

    def test_moved_ceiling_is_rejected(self) -> None:
        import json
        import tempfile
        table = json.loads(tca.CEILINGS_PATH.read_text(encoding="utf-8"))
        table["ceilings"]["shape"]["blind_ceiling"] = 0.5  # a laundered ceiling
        with tempfile.TemporaryDirectory() as d:
            bogus = Path(d) / "moved.json"
            bogus.write_text(json.dumps(table), encoding="utf-8")
            with self.assertRaises(ValueError):
                tca.load_frozen_ceilings(bogus)


class ComparisonLogic(unittest.TestCase):
    """Model-vs-ceiling: strict `>`, signed margin -- matching is NOT beating."""

    def test_strictly_above_beats(self) -> None:
        v = tca.compare_to_ceiling(0.1145, 0.1069)
        self.assertTrue(v["beats_ceiling"])
        self.assertAlmostEqual(v["margin"], 0.1145 - 0.1069, places=9)

    def test_below_does_not_beat(self) -> None:
        v = tca.compare_to_ceiling(0.187, 0.400)
        self.assertFalse(v["beats_ceiling"])
        self.assertLess(v["margin"], 0)

    def test_exact_match_is_not_beating(self) -> None:
        v = tca.compare_to_ceiling(0.1069, 0.1069)
        self.assertFalse(v["beats_ceiling"])
        self.assertEqual(v["margin"], 0.0)


class Summary(unittest.TestCase):
    def test_mean_and_sample_sd(self) -> None:
        s = tca.summarize_scores([0.10, 0.12, 0.14])
        self.assertAlmostEqual(s["mean"], 0.12, places=9)
        self.assertAlmostEqual(s["sd"], 0.02, places=9)
        self.assertEqual(s["n_seeds"], 3)
        self.assertEqual(s["per_seed"], [0.10, 0.12, 0.14])

    def test_single_seed_sd_is_zero(self) -> None:
        s = tca.summarize_scores([0.11])
        self.assertEqual(s["sd"], 0.0)
        self.assertEqual(s["mean"], 0.11)

    def test_empty_refuses(self) -> None:
        with self.assertRaises(ValueError):
            tca.summarize_scores([])


class ReportStructure(unittest.TestCase):
    def test_holdout_report_shape(self) -> None:
        entry = tca.build_holdout_report("shape", [0.11, 0.12, 0.10], 0.1069)
        for key in ("model_exact", "ceiling", "model_mean", "margin",
                    "beats_ceiling", "is_strict_ceiling", "is_near_vacuous"):
            self.assertIn(key, entry)
        self.assertTrue(entry["is_strict_ceiling"])
        self.assertFalse(entry["is_near_vacuous"])
        self.assertEqual(entry["ceiling"], 0.1069)

    def test_discipline_flagged_near_vacuous(self) -> None:
        entry = tca.build_holdout_report("discipline", [0.6, 0.6, 0.6],
                                         0.9318181818181818)
        self.assertTrue(entry["is_near_vacuous"])
        self.assertFalse(entry["is_strict_ceiling"])


if __name__ == "__main__":
    unittest.main()
