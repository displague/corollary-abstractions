from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

from depth_interface import (ARMS, SEEDS, adjudicate,  # noqa: E402
                            control_accounting, unconditional_from_row)


def _row(arm: str, seed: int, ood_exact: float) -> dict:
    """A minimal control row: OOD has 10 generated, 8 kept, 2 excluded.

    depth 4 keeps all it generates; depth 5 owns both capacity exclusions, so
    the exclusions are entirely at the deepest depth -- the pinned accounting.
    """
    diagnostics = {
        "mode": "teacher-forced",
        "step_perfect_rate": ood_exact,
        "first_error_decile": {
            "0": {"examples": 3, "fraction_of_erroneous": 0.6},
            "1": {"examples": 1, "fraction_of_erroneous": 0.2},
            "9": {"examples": 1, "fraction_of_erroneous": 0.2},
        },
    }
    return {
        "consumer": arm, "seed": seed, "params": 100,
        "test_exact": 1.0, "ood_exact": ood_exact,
        "ood_diagnostics": diagnostics,
        "inclusion": {
            split: {
                "generated": 10, "kept": 8,
                "dropped_max_len": 0, "dropped_max_tgt": 2,
                "by_depth": {
                    "4": {"generated": 4, "kept": 4,
                          "dropped_max_len": 0, "dropped_max_tgt": 0},
                    "5": {"generated": 6, "kept": 4,
                          "dropped_max_len": 0, "dropped_max_tgt": 2},
                },
            }
            for split in ("train", "val", "test", "ood")
        },
    }


class DepthInterfaceAccountingTests(unittest.TestCase):
    def write_control(self, root: Path, scores: dict) -> None:
        for arm in ARMS:
            for seed, score in zip(SEEDS, scores[arm]):
                (root / f"depth_{arm}_s{seed}.json").write_text(
                    json.dumps(_row(arm, seed, score)), encoding="utf-8")

    def test_unconditional_is_retained_times_kept_over_generated(self) -> None:
        # ood_exact = 4/8 = 0.5 retained; unconditional counts the 2 excluded
        # rows as failures: 4/10 = 0.4 = 0.5 * 8/10.
        result = unconditional_from_row(_row("address", 0, 0.5), "ood")
        self.assertEqual(result["correct"], 4)
        self.assertEqual(result["kept"], 8)
        self.assertEqual(result["generated"], 10)
        self.assertEqual(result["excluded"], 2)
        self.assertAlmostEqual(result["retained_ood"], 0.5)
        self.assertAlmostEqual(result["unconditional_ood"], 0.4)
        self.assertAlmostEqual(result["unconditional_ood"],
                               0.5 * 8 / 10)

    def test_capacity_exclusions_are_kept_per_depth(self) -> None:
        result = unconditional_from_row(_row("address", 0, 0.5), "ood")
        depths = result["by_depth"]
        self.assertEqual(depths["4"]["excluded"], 0)
        self.assertEqual(depths["5"]["excluded"], 2)
        # generated == kept + excluded at every depth, and the depth totals
        # reconstruct the split totals.
        self.assertEqual(
            sum(d["generated"] for d in depths.values()), result["generated"])
        self.assertEqual(
            sum(d["excluded"] for d in depths.values()), result["excluded"])
        self.assertEqual(depths["5"]["retained_scored"], 4)
        self.assertEqual(depths["5"]["unconditional_scored"], 6)

    def test_non_integer_correct_count_refuses(self) -> None:
        # 0.3 * 8 = 2.4 is not an integer correct count -> the accounting must
        # refuse rather than invent a fractional row.
        with self.assertRaisesRegex(ValueError, "cannot recover an integer"):
            unconditional_from_row(_row("address", 0, 0.3), "ood")

    def test_incoherent_inclusion_refuses(self) -> None:
        row = _row("address", 0, 0.5)
        row["inclusion"]["ood"]["dropped_max_tgt"] = 5  # 8 + 0 + 5 != 10
        with self.assertRaisesRegex(ValueError, "incoherent ood inclusion"):
            unconditional_from_row(row, "ood")

    def test_verdict_preserved_and_pdi1_fires(self) -> None:
        # address best, both worst, on retained AND unconditional; exclusions
        # entirely depth 5 -> P-DI1 fires.
        scores = {
            "address": (0.50, 0.50, 0.50),
            "query": (0.375, 0.375, 0.375),
            "memory": (0.25, 0.25, 0.25),
            "both": (0.125, 0.125, 0.125),
            "mlp": (0.375, 0.375, 0.375),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_control(root, scores)
            arms = control_accounting(root)
            for arm in ARMS:
                self.assertLess(arms[arm]["unconditional_mean"],
                                arms[arm]["retained_mean"])
            result = adjudicate(root, root, score_subsets=False)
        pdi1 = result["adjudication"]["P-DI1"]
        self.assertEqual(pdi1["status"], "FIRED")
        self.assertEqual(pdi1["retained_ordering"][0], "address")
        self.assertEqual(pdi1["unconditional_ordering"][0], "address")
        self.assertEqual(pdi1["exclusions_depth_set"], ["5"])
        self.assertTrue(pdi1["ordering_preserved"])

    def test_pdi2_pending_without_treatment(self) -> None:
        scores = {arm: (0.5, 0.5, 0.5) for arm in ARMS}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_control(root, scores)
            result = adjudicate(root, root, score_subsets=False)
        self.assertEqual(result["adjudication"]["P-DI2"]["status"], "PENDING")


class DepthInterfacePredictionTests(unittest.TestCase):
    def test_predictions_registered_in_roadmap_interface_lane(self) -> None:
        # The interface lane the predictions answer is roadmap item 5.
        roadmap = (ROOT / "docs" / "ROADMAP-v0.8.md").read_text(encoding="utf-8")
        self.assertIn("interface-level result", roadmap)
        self.assertIn("untruncated OOD", roadmap)


if __name__ == "__main__":
    unittest.main()
