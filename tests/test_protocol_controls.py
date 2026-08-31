"""The blind controls fire on a broken runtime and stay silent on the table.

`docs/DESIGN-protocol-uptake.md` §8 states the voiding sentence and §7's B4
adds the clause that makes it usable: *"A table-faithful runtime matches the
frozen ceilings with equality; equality is not a firing."* A control that
cannot fire and a control that always fires are the same non-instrument, so
these tests score both directions:

* fitted to the **sealed table**, the two restricted views reproduce U-P0's
  frozen ceilings exactly, and the position-switch control reproduces its
  frozen table-agreement — and none of the three fires;
* fitted to a **deliberately broken runtime**, each control fires.

Written against `scripts/protocol_controls.py`, which DESIGN §6 step 4 places
before the runtime exists. These tests therefore pass at a commit where
`scripts/protocol_runtime.py` does not exist yet, except for the one test that
asserts the runtime never imports the controls, which skips in that case.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import protocol_controls as controls  # noqa: E402

PREREG = REPO / "experiments" / "protocol_uptake_prereg.json"
RUNTIME = REPO / "scripts" / "protocol_runtime.py"


class ControlFitTests(unittest.TestCase):
    """The fits reproduce the numbers U-P0 froze, from the committed table."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = controls.load_fixtures()
        cls.sealed = controls.sealed_labels(cls.fixtures)
        cls.columns = controls.position_ids(cls.fixtures)
        cls.prereg = json.loads(PREREG.read_text(encoding="utf-8"))

    def test_the_sealed_table_is_the_thirty_two(self) -> None:
        self.assertEqual(len(self.sealed), 8)
        self.assertEqual(sum(len(row) for row in self.sealed), 32)
        self.assertEqual(self.columns, self.prereg["expected_uptake"]["columns"])

    def test_surface_only_fit_reproduces_c_surface(self) -> None:
        self.assertEqual(controls.fit_surface_only(self.sealed), 21)
        self.assertEqual(
            controls.fit_surface_only(self.sealed),
            self.prereg["frozen_numbers"]["c_surface"],
        )

    def test_position_only_fit_reproduces_c_position(self) -> None:
        self.assertEqual(controls.fit_position_only(self.sealed), 21)
        self.assertEqual(
            controls.fit_position_only(self.sealed),
            self.prereg["frozen_numbers"]["c_position"],
        )

    def test_position_switch_reproduces_its_frozen_agreement(self) -> None:
        self.assertEqual(
            controls.position_switch_agreement(self.sealed, self.columns), 17
        )
        self.assertEqual(
            controls.position_switch_agreement(self.sealed, self.columns),
            self.prereg["frozen_numbers"]["position_switch_agreement"],
        )

    def test_a_ragged_labeling_is_refused_rather_than_scored(self) -> None:
        with self.assertRaises(controls.ControlError):
            controls.fit_surface_only([["greeting"] * 4] * 7)


class VoidingSentenceTests(unittest.TestCase):
    """Equality is not a firing; exceeding is."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fixtures = controls.load_fixtures()
        cls.sealed = controls.sealed_labels(cls.fixtures)
        cls.columns = controls.position_ids(cls.fixtures)

    def evaluate(self, labels):
        return controls.voiding_sentence_evaluation(
            labels,
            c_surface=self.fixtures["ceilings"]["c_surface"],
            c_position=self.fixtures["ceilings"]["c_position"],
            frozen_position_switch_agreement=self.fixtures["position_switch_control"][
                "frozen_table_agreement"
            ],
            positions=self.columns,
        )

    def test_the_sealed_table_does_not_fire(self) -> None:
        """A table-faithful runtime's labels ARE the table. Equality passes."""

        evaluation = self.evaluate(self.sealed)
        self.assertFalse(evaluation["fired"])
        self.assertEqual(evaluation["fired_arms"], [])
        for arm in evaluation["arms"].values():
            self.assertTrue(arm["equality_is_not_a_firing"])

    def test_lexical_trigger_runtime_fires_the_surface_arm(self) -> None:
        """Surface in, family out, position ignored: 32/32 on a 21 ceiling."""

        labels = controls.lexical_trigger_runtime(self.sealed)
        for row in labels:
            self.assertEqual(len(set(row)), 1, "a lexical trigger is constant per surface")
        self.assertEqual(controls.fit_surface_only(labels), 32)
        evaluation = self.evaluate(labels)
        self.assertTrue(evaluation["fired"])
        self.assertIn("surface_only_refit", evaluation["fired_arms"])
        self.assertGreater(
            evaluation["arms"]["surface_only_refit"]["agreement"],
            evaluation["arms"]["surface_only_refit"]["frozen_ceiling"],
        )

    def test_position_switch_runtime_fires_the_switch_arm(self) -> None:
        """The runtime *is* the control, so it agrees with it on all 32."""

        labels = controls.position_switch_runtime(self.sealed, self.columns)
        self.assertEqual(controls.position_switch_agreement(labels, self.columns), 32)
        evaluation = self.evaluate(labels)
        self.assertTrue(evaluation["fired"])
        self.assertIn("position_switch", evaluation["fired_arms"])
        self.assertGreater(
            evaluation["arms"]["position_switch"]["agreement"],
            evaluation["arms"]["position_switch"]["frozen_table_agreement"],
        )

    def test_the_two_broken_runtimes_are_not_the_same_failure(self) -> None:
        """Two controls, two distinct ways to be wrong — not one test twice."""

        lexical = controls.lexical_trigger_runtime(self.sealed)
        switch = controls.position_switch_runtime(self.sealed, self.columns)
        self.assertNotEqual(lexical, switch)
        self.assertEqual(self.evaluate(lexical)["fired_arms"], ["surface_only_refit"])
        self.assertIn("position_only_refit", self.evaluate(switch)["fired_arms"])


class ControlIsolationTests(unittest.TestCase):
    """The broken runtimes are never reachable from the real path."""

    def test_the_runtime_does_not_import_the_controls(self) -> None:
        if not RUNTIME.exists():
            self.skipTest(
                "the runtime does not exist yet; DESIGN §6 step 4 commits the "
                "controls first"
            )
        source = RUNTIME.read_text(encoding="utf-8")
        self.assertNotIn("protocol_controls", source)

    def test_the_broken_runtimes_are_named_as_controls(self) -> None:
        for function in (controls.lexical_trigger_runtime, controls.position_switch_runtime):
            self.assertIn("BROKEN CONTROL", function.__doc__ or "")


if __name__ == "__main__":
    unittest.main()
