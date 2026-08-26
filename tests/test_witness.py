#!/usr/bin/env python3
"""WITNESS: the fragment census, the obligation builder, and W1's pilot.

`docs/DESIGN-witnessed-conformance.md`. The slice stopped at W1 with 0 of 6
discharged, and a stop is only a result if the machinery that produced it can
be shown to work. So the tests that matter here are the ones that could have
gone the other way:

- the builder **can** produce a non-trivial obligation (a hand-built flat `+`
  node), so `rejected_trivial` on the corpus is a reading and not a builder
  that always says trivial;
- the checker **does** decide those obligations, in both directions;
- and the toolchain's absence is **loud**, because a gate artifact written
  without its checker would record absence as if it were a reading.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import conform  # noqa: E402
import conform_census as census  # noqa: E402
import external_verifier as verifier  # noqa: E402
import witness_fragment_census as wfc  # noqa: E402
import witness_obligation as wo  # noqa: E402
import witness_pilot as wp  # noqa: E402

CENSUS = ROOT / wfc.ARTIFACT
PILOT = ROOT / wp.ARTIFACT


def _program(text: str, variables, guard=(), carrier="Nat",
             division="truncating", subtraction="truncated-at-zero"):
    return conform.Program(
        statement_id="fixture", corpus="fixture",
        conclusion=census.parse(text), guard_conjuncts=tuple(guard),
        variables=tuple(variables), carrier=carrier, division=division,
        subtraction=subtraction)


class TheTwoReadingsAreTheSameOnBinaryNodes(unittest.TestCase):
    """W1's structural finding, pinned so a parser change surfaces here."""

    SHAPES = ["a - b + c >= 0", "a + b - c >= 0", "a / 2 * 3 >= 1",
              "a * 3 / 2 >= 1", "a - b - c >= 0", "1 - a + b >= 0"]

    def test_the_parser_emits_binary_nodes_so_regrouping_is_a_no_op(
            self) -> None:
        for text in self.SHAPES:
            with self.subTest(text=text):
                side = census.parse(text)[2][0]
                self.assertEqual(wo.eval_tree(side), wo.surface_tree(side))

    def test_a_flat_node_DOES_diverge_and_the_builder_notices(self) -> None:
        """THE TEST THAT LETS `rejected_trivial` MEAN SOMETHING.

        Hand-built: a three-operand `+` with the negative in the middle. The
        evaluator hoists `a` and `c` and subtracts `b`; read as written it is
        `(a - b) + c`. Over Nat those differ, and the builder must produce a
        NON-trivial obligation for it. Without this test, "every obligation
        is trivial" would be indistinguishable from a builder that says
        trivial unconditionally.
        """

        flat = ("op", "+", (("slot", "a"),
                            ("op", "neg", (("slot", "b"),)),
                            ("slot", "c")))
        self.assertEqual(wo.render(wo.eval_tree(flat)), "((a + c) - b)")
        self.assertEqual(wo.render(wo.surface_tree(flat)), "((a - b) + c)")
        self.assertNotEqual(wo.eval_tree(flat), wo.surface_tree(flat))

        program = _program("a >= 0", ["a", "b", "c"])
        program.conclusion = ("rel", ">=", (flat, ("num", 1)))
        obligation = wo.build(program)
        self.assertFalse(obligation["trivial_by_construction"])
        self.assertIn("↔", obligation["obligation"])
        self.assertNotEqual(obligation["evaluated_reading"],
                            obligation["as_written_reading"])

    def test_a_flat_product_diverges_too(self) -> None:
        flat = ("op", "*", (("slot", "a"),
                            ("op", "inv", (("num", 2),)),
                            ("num", 3)))
        self.assertEqual(wo.render(wo.eval_tree(flat)), "((a * 3) / 2)")
        self.assertEqual(wo.render(wo.surface_tree(flat)), "((a / 2) * 3)")


class TheBuilderRefusesWhatItCannotState(unittest.TestCase):

    def test_a_non_nat_literal_refuses(self) -> None:
        with self.assertRaises(wo.Unbuildable):
            wo.render(("lit", "5/2"))

    def test_a_unary_negation_refuses_outside_a_plus_node(self) -> None:
        with self.assertRaises(wo.Unbuildable):
            wo.eval_tree(("op", "*", (("op", "neg", (("num", 3),)),
                                      ("slot", "x"))))

    def test_an_unsupported_domain_refuses(self) -> None:
        program = _program("x >= 0", ["x"], carrier="Rat", division="exact",
                           subtraction="signed")
        with self.assertRaises(wo.Unbuildable):
            wo.build(program)

    def test_the_ground_class_is_not_this_slices(self) -> None:
        with self.assertRaises(wo.Unbuildable):
            wo.build(_program("1 >= 0", []))


class B4RejectsASelfComparisonByOrdinaryMeans(unittest.TestCase):
    """One discharge voids the instrument, so the trap must never build."""

    def test_self_comparison_is_trivial_even_on_a_divergent_term(self) -> None:
        flat = ("op", "+", (("slot", "a"),
                            ("op", "neg", (("slot", "b"),)),
                            ("slot", "c")))
        program = _program("a >= 0", ["a", "b", "c"])
        program.conclusion = ("rel", ">=", (flat, ("num", 1)))
        # The same term builds NON-trivially in the ordinary direction...
        self.assertFalse(wo.build(program)["trivial_by_construction"])
        # ...and trivially when compared to itself. The builder has no branch
        # that recognises the trap; the tree comparison does all the work.
        self.assertTrue(
            wo.build(program, self_comparison=True)["trivial_by_construction"])


class TheFragmentPredicateIsExecutable(unittest.TestCase):

    def _linear(self, text: str) -> bool:
        try:
            wfc.check_linear(census.parse(text)[2][0])
            return True
        except wfc.NotLinear:
            return False

    def test_linear_terms_are_admitted(self) -> None:
        for text in ["a + b >= 1", "3 * a - 2 * b >= 1", "a / 4 >= 1",
                     "a ^ 1 + 2 >= 1"]:
            with self.subTest(text=text):
                self.assertTrue(self._linear(text))

    def test_non_linear_terms_are_rejected_with_a_reason(self) -> None:
        cases = {
            "a * b >= 1": "two variables multiplied together",
            "a ^ 2 >= 1": "a variable raised to a power > 1",
            # `1 / a` parses as `*(1, inv(a))`, so it trips the `*` node's
            # denominator clause rather than the bare-`inv` clause. The bare
            # clause is exercised directly below, because a branch no input
            # reaches is a branch no test covers.
            "1 / a >= 1": "division BY a variable is not linear",
            "2 ^ a >= 1": "a variable in an exponent",
            "b / a >= 1": "division BY a variable is not linear",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                with self.assertRaises(wfc.NotLinear) as caught:
                    wfc.check_linear(census.parse(text)[2][0])
                self.assertIn(expected, caught.exception.reason)

    def test_the_bare_inv_clause_is_exercised_directly(self) -> None:
        """A standalone `inv` node, which the parser only ever nests."""
        with self.assertRaises(wfc.NotLinear) as caught:
            wfc.check_linear(("op", "inv", (("slot", "a"),)))
        self.assertIn("a variable under `inv`", caught.exception.reason)

    def test_a_non_nat_literal_leaves_the_fragment(self) -> None:
        with self.assertRaises(wfc.NotLinear) as caught:
            wfc.check_linear(census.parse("2.5 * a >= 1")[2][0])
        self.assertIn("outside the declared Nat carrier",
                      caught.exception.reason)

    def test_the_exponent_bucket_is_one_bucket(self) -> None:
        """`power=2` and `power=1006` are the same rejection."""
        reasons = set()
        for text in ["a ^ 2 >= 1", "a ^ 1006 >= 1"]:
            with self.assertRaises(wfc.NotLinear) as caught:
                wfc.check_linear(census.parse(text)[2][0])
            reasons.add(caught.exception.reason)
        self.assertEqual(len(reasons), 1)


class TheToolchainsAbsenceIsLoud(unittest.TestCase):
    """A gate artifact written without its checker records absence as data."""

    def test_pinned_binary_raises_rather_than_returning_none(self) -> None:
        original = verifier.toolchain_binary
        verifier.toolchain_binary = lambda _toolchain: None
        try:
            with self.assertRaises(wp.ToolchainAbsent) as caught:
                wp.pinned_binary()
        finally:
            verifier.toolchain_binary = original
        message = str(caught.exception)
        self.assertIn("NOT INSTALLED", message)
        self.assertIn("refuses to download", message)
        self.assertIn("refuses to skip quietly", message)

    def test_main_exits_nonzero_rather_than_writing_an_artifact(self) -> None:
        original = verifier.toolchain_binary
        verifier.toolchain_binary = lambda _toolchain: None
        try:
            self.assertEqual(wp.main(["--out", "unused.json"]), 2)
        finally:
            verifier.toolchain_binary = original


@unittest.skipUnless(CENSUS.exists(), "W0 has not been run")
class TheCensusArtifactSaysWhatItCounted(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(CENSUS.read_text(encoding="utf-8"))

    def test_the_predicate_digests_are_recomputed_not_trusted(self) -> None:
        """M6: where a digest can be recomputed by a test, recompute it."""
        self.assertEqual(
            self.doc["selection_predicate_hash"],
            wfc._sha256_lf(ROOT / "scripts" / "witness_fragment_census.py"),
            "the census predicate changed after the census was written")
        self.assertEqual(
            self.doc["obligation_builder_hash"],
            wfc._sha256_lf(ROOT / "scripts" / "witness_obligation.py"),
            "the obligation builder changed after the census was written; the "
            "predicate's last clause is a call into it, so this voids the "
            "population")

    def test_the_population_matches_the_candidate_list(self) -> None:
        self.assertEqual(self.doc["candidate_population"],
                         len(self.doc["candidates"]))
        self.assertEqual(len(set(self.doc["candidates"])),
                         len(self.doc["candidates"]))

    def test_every_candidate_really_builds_an_obligation(self) -> None:
        """The predicate's last clause, checked against the tree."""
        programs = wp.load_programs(set(self.doc["candidates"]))
        self.assertEqual(len(programs), self.doc["candidate_population"])
        for statement_id, (program, _text) in programs.items():
            with self.subTest(statement=statement_id):
                wo.build(program)

    def test_the_withdraw_rule_fired_and_says_so(self) -> None:
        rule = self.doc["the_withdraw_and_reset_rule"]
        self.assertEqual(rule["threshold"], wfc.WITHDRAW_BELOW)
        self.assertEqual(rule["population"], self.doc["candidate_population"])
        self.assertEqual(
            rule["fires"], rule["population"] < wfc.WITHDRAW_BELOW)
        self.assertTrue(rule["fires"], "the design's amendment assumes it did")

    def test_the_decoys_are_out_of_fragment_and_recomputable(self) -> None:
        decoys = self.doc["decoys_drawn"]
        self.assertEqual(len(decoys), wfc.DRAFT_DECOYS)
        self.assertFalse(set(decoys) & set(self.doc["candidates"]))
        self.assertEqual(decoys, sorted(decoys))


@unittest.skipUnless(PILOT.exists(), "W1 has not been run")
class ThePilotStoppedAndShowedTheStopWasAReading(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(PILOT.read_text(encoding="utf-8"))

    def test_it_reads_the_census_it_was_drawn_from(self) -> None:
        census_doc = json.loads(CENSUS.read_text(encoding="utf-8"))
        self.assertEqual(self.doc["census_predicate_hash"],
                         census_doc["selection_predicate_hash"])
        self.assertEqual(
            self.doc["obligation_builder_hash"],
            wfc._sha256_lf(ROOT / "scripts" / "witness_obligation.py"))

    def test_the_draw_is_recomputable_from_the_census_alone(self) -> None:
        census_doc = json.loads(CENSUS.read_text(encoding="utf-8"))
        programs = wp.load_programs(set(census_doc["candidates"]))
        self.assertEqual([r["statement_id"] for r in wp.draw(programs)],
                         self.doc["drawn"])

    def test_all_six_shape_classes_were_filled(self) -> None:
        self.assertEqual(len(self.doc["rows"]), wp.PILOT_SIZE)
        self.assertTrue(all(r["class_was_filled"] for r in self.doc["rows"]))
        kinds = {r["guard_kind"] for r in self.doc["rows"]}
        self.assertIn("box", kinds, "the design asked for a box guard")
        self.assertIn("coupling", kinds, "and for a coupling guard")

    def test_both_controls_read_as_specified(self) -> None:
        controls = self.doc["controls"]
        self.assertTrue(controls["positive_control"]["met"],
                        "a non-trivial TRUE obligation must discharge")
        self.assertTrue(controls["negative_control"]["met"],
                        "a non-trivial FALSE obligation must not")
        self.assertTrue(controls["pipeline_is_not_broken"])

    def test_b4s_trap_returned_rejected_trivial(self) -> None:
        trap = self.doc["b4_self_comparison_trap"]
        self.assertTrue(trap["met"])
        self.assertEqual(trap["verdict"], wo.REJECTED_TRIVIAL)

    def test_the_counterfactual_is_what_makes_the_stop_worth_reading(
            self) -> None:
        counterfactual = self.doc["the_counterfactual_that_makes_B4_concrete"]
        self.assertEqual(counterfactual["of"], wp.PILOT_SIZE)
        self.assertEqual(counterfactual["obligations_the_checker_accepted"],
                         wp.PILOT_SIZE,
                         "an instrument without B4 would have published every "
                         "one of these as a discharged lemma")

    def test_the_stop_fired_and_no_floor_was_frozen(self) -> None:
        self.assertEqual(self.doc["reading"]["discharged"], 0)
        self.assertTrue(self.doc["stop_condition"]["fired"])
        self.assertIn("STOPPED", self.doc["stop_condition"]["verdict"])
        self.assertIsNone(self.doc["reading"]["floor_frozen"])

    def test_no_manifest_was_sealed(self) -> None:
        self.assertFalse(
            (ROOT / "experiments" / "witness_target_manifest.json").exists(),
            "the slice stopped at W1; sealing a manifest afterwards would be "
            "the design's own ordering violated")

    def test_the_non_claims_keep_the_void_where_it_is(self) -> None:
        joined = " ".join(self.doc["non_claims"])
        self.assertIn("No capability is claimed", joined)
        self.assertIn("stays void", joined)


if __name__ == "__main__":
    unittest.main()
