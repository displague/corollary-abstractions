"""Tests for the exploratory grounded-admission measurement."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from measure_grounded_admission import (  # noqa: E402
    EXECUTABLE_LEDGER_COMMIT,
    PROSE_DESIGN_COMMIT,
    PAIRS_PER_SOURCE,
    SEEDS,
    SOURCES,
    DATA,
    HOLDOUT,
    _sha256,
    _tree_digest,
    adjudicate,
    changed_head_positions,
    construction_checks,
    fixed_owned_score,
    head_blind,
    leaves,
    replace_head,
)


class TreeFoilTests(unittest.TestCase):
    def setUp(self):
        self.tree = (
            "rel",
            "=",
            (
                ("call", "F", (("slot", "x"),)),
                ("op", "+", (("slot", "x"), ("num", 1.0))),
            ),
        )

    def test_one_head_swap_preserves_blind_tree_and_leaves(self):
        foil = replace_head(self.tree, (1,), "*")
        self.assertEqual(head_blind(self.tree), head_blind(foil))
        self.assertEqual(leaves(self.tree), leaves(foil))
        self.assertEqual(changed_head_positions(self.tree, foil), [(1,)])

    def test_replacing_a_leaf_is_refused(self):
        with self.assertRaisesRegex(ValueError, "applied node"):
            replace_head(self.tree, (0, 0), "G")


class FixedOwnerScoreTests(unittest.TestCase):
    def test_candidate_only_owners_do_not_mint_grounding(self):
        entry = {
            "considered": 3,
            "constituents": [
                {"grounded_via": "exact", "owners": ["fixed.a", "candidate.x"]},
                {"grounded_via": "exact", "owners": ["candidate.y"]},
                {"grounded_via": "pattern", "owners": ["fixed.b"]},
            ],
        }
        score = fixed_owned_score(entry, {"fixed.a", "fixed.b"})
        self.assertEqual(score["fixed_owned_exact"], 1)
        self.assertEqual(score["nonfixed_only_exact"], 1)
        self.assertEqual(score["grounded_at_all"], 1 / 3)
        self.assertFalse(score["admitted"])

    def test_zero_denominator_refuses(self):
        score = fixed_owned_score({"considered": 0, "constituents": []}, set())
        self.assertEqual(score["grounded_at_all"], 0.0)
        self.assertFalse(score["admitted"])


def _source_row(
    *,
    valid: bool = True,
    authentic: float = 0.8,
    foil_rejection: float = 0.8,
    paired: float = 0.8,
    margin: float = 0.1,
) -> dict:
    return {
        "construction": {"valid": valid, "blind_paired_accuracy": 0.5},
        "metrics": {
            "authentic_acceptance": authentic,
            "foil_rejection": foil_rejection,
            "balanced_accuracy": (authentic + foil_rejection) / 2,
            "paired_accuracy": paired,
            "mean_margin": margin,
        },
    }


class AdjudicationTests(unittest.TestCase):
    def test_all_prose_stated_bars_fire_from_three_seed_means(self):
        runs = [
            {"seed": seed, "sources": {source: _source_row() for source in SOURCES}}
            for seed in SEEDS
        ]
        result = adjudicate(runs)
        self.assertEqual(
            [result[key]["status"] for key in ("G1", "G2", "G3", "G4")],
            ["FIRED", "FIRED", "FIRED", "FIRED"],
        )

    def test_construction_miss_refuses_measurement_predictions(self):
        runs = [
            {
                "seed": seed,
                "sources": {
                    source: _source_row(valid=not (seed == SEEDS[0] and source == SOURCES[0]))
                    for source in SOURCES
                },
            }
            for seed in SEEDS
        ]
        result = adjudicate(runs)
        self.assertEqual(result["G3"]["status"], "MISSED")
        self.assertEqual(result["G1"]["status"], "REFUSED")
        self.assertEqual(result["G2"]["status"], "REFUSED")
        self.assertEqual(result["G4"]["status"], "REFUSED")


class ConstructionCheckTests(unittest.TestCase):
    def test_swapped_batch_preserves_head_multiset(self):
        a = ("call", "F", (("slot", "x"),))
        b = ("call", "G", (("slot", "y"),))
        pairs = []
        for i in range(PAIRS_PER_SOURCE // 2):
            pairs.extend(
                (
                    {
                        "authentic_tree": a,
                        "foil_tree": replace_head(a, (), "G"),
                        "path": [],
                    },
                    {
                        "authentic_tree": b,
                        "foil_tree": replace_head(b, (), "F"),
                        "path": [],
                    },
                )
            )
        checks = construction_checks(pairs)
        self.assertTrue(checks["valid"])
        self.assertEqual(checks["blind_paired_accuracy"], 0.5)


class CommittedLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "experiments" / "grounded_admission.json"
        if not path.exists():
            raise unittest.SkipTest("committed exploratory ledger is absent")
        cls.ledger = json.loads(path.read_text(encoding="utf-8"))

    def test_ledger_links_prose_design_without_overstating_provenance(self):
        self.assertEqual(self.ledger["design_commit"], PROSE_DESIGN_COMMIT)
        self.assertNotEqual(PROSE_DESIGN_COMMIT, EXECUTABLE_LEDGER_COMMIT)
        self.assertEqual(
            EXECUTABLE_LEDGER_COMMIT,
            "943c87cd9ddc7f381c8b20c316c4871c2e89707d",
        )
        self.assertEqual(self.ledger["seeds"], list(SEEDS))
        self.assertEqual(self.ledger["pairs_per_source_per_seed"], PAIRS_PER_SOURCE)
        self.assertFalse(self.ledger["pattern_membership"])

    def test_source_digests_cover_fixed_graph_and_both_holdouts(self):
        digests = self.ledger["source_digests"]
        self.assertEqual(digests["fixed_data"], _tree_digest(DATA))
        for source in SOURCES:
            self.assertEqual(digests[source]["sha256"], _sha256(HOLDOUT / source / "nodes.json"))

    def test_every_measurement_cell_is_present_and_nonvacuous(self):
        self.assertEqual(len(self.ledger["runs"]), len(SEEDS))
        for run, seed in zip(self.ledger["runs"], SEEDS):
            self.assertEqual(run["seed"], seed)
            for source in SOURCES:
                cell = run["sources"][source]
                self.assertEqual(len(cell["rows"]), PAIRS_PER_SOURCE)
                self.assertTrue(cell["construction"]["valid"])
                self.assertEqual(cell["construction"]["blind_paired_accuracy"], 0.5)

    def test_closed_form_adjudication_and_negative_outcome_are_pinned(self):
        self.assertEqual(self.ledger["adjudication"], adjudicate(self.ledger["runs"]))
        self.assertEqual(
            {key: self.ledger["adjudication"][key]["status"] for key in ("G1", "G2", "G3", "G4")},
            {"G1": "MISSED", "G2": "MISSED", "G3": "FIRED", "G4": "FIRED"},
        )


if __name__ == "__main__":
    unittest.main()
