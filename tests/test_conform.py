#!/usr/bin/env python3
"""The compiler: what a verdict is, and what its sentence is allowed to say.

`docs/DESIGN-statements-that-run.md` §3.2/§3.4. The properties under test are
the honesty ones rather than the arithmetic: that `certifies` comes from a
closed table keyed on the verdict and cannot drift from it, that an errored
point is neither a counterexample nor agreement, that a statement whose guard
admits nothing is REFUSED rather than reported as not-falsified, and that the
domain readings the schema declares are the ones actually applied.
"""

from __future__ import annotations

import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import conform  # noqa: E402
import conform_census as census  # noqa: E402
import conform_domain  # noqa: E402


def _node(corpus: str, statement_id: str):
    document = json.loads(
        (ROOT / "data" / corpus / "nodes.json").read_text(encoding="utf-8"))
    for node in document["statement_nodes"]:
        if node["statement_id"] == statement_id:
            return node, document.get("corpus_id", corpus)
    raise AssertionError(f"{statement_id} is not in data/{corpus}")


class TheCertifiesTableIsClosedAndKeyed(unittest.TestCase):
    """§3.4: every verdict has a row, including the two that computed nothing."""

    def test_every_verdict_has_a_certifies_sentence(self) -> None:
        for verdict in (
            conform.DECIDED_TRUE, conform.DECIDED_FALSE, conform.NONCONFORMANT,
            conform.NO_COUNTEREXAMPLE_FOUND, conform.UNDECLARED_DOMAIN,
            conform.REFUSED,
        ):
            with self.subTest(verdict=verdict):
                self.assertTrue(conform.CERTIFIES[verdict].strip())

    def test_the_not_falsified_row_refuses_to_certify_universally(self) -> None:
        """The design's central honesty boundary, asserted on the sentence."""
        sentence = conform.CERTIFIES[conform.NO_COUNTEREXAMPLE_FOUND]
        self.assertIn("certifies nothing universally", sentence)
        self.assertIn("not evidence the statement is true", sentence)

    def test_no_verdict_name_contains_the_word_conforms(self) -> None:
        """It is `NO_COUNTEREXAMPLE_FOUND` rather than anything with `conforms`."""
        for verdict in conform.CERTIFIES:
            self.assertNotIn("CONFORM", verdict.replace("NONCONFORMANT", ""))

    def test_a_refusal_says_it_is_not_a_negative_result(self) -> None:
        self.assertIn("not a negative result",
                      conform.CERTIFIES[conform.REFUSED])

    def test_the_nihil_table_is_closed_the_same_way(self) -> None:
        for verdict in (conform.NO_SUCH_OBJECT, conform.EXISTS,
                        conform.OUT_OF_CLASS):
            self.assertTrue(conform.NIHIL_CERTIFIES[verdict].strip())
        self.assertIn("not a failure to find",
                      conform.NIHIL_CERTIFIES[conform.NO_SUCH_OBJECT])


class TheDeclaredDomainIsTheOneApplied(unittest.TestCase):
    """Correction 4: the difference between Nat and Rat is one operator."""

    def test_truncating_division_is_the_declared_reading(self) -> None:
        tree = census.parse("2017 - (2017 / 3)")
        truncating = conform.eval_under_domain(
            tree, {}, "Nat", "truncating", "truncated-at-zero")
        exact = conform.eval_under_domain(tree, {}, "Rat", "exact", "signed")
        self.assertEqual(truncating, Fraction(1345))
        self.assertNotEqual(exact, Fraction(1345))

    def test_the_exact_reading_delegates_to_the_committed_evaluator(self) -> None:
        """The common path is `evaluate._eval_tree` and nothing else."""
        import evaluate as ev

        tree = census.parse("2 + 3 * 4")
        self.assertEqual(
            conform.eval_under_domain(tree, {}, "Rat", "exact", "signed"),
            ev._eval_tree(tree, {}, set()),
        )

    def test_nat_has_no_negation_and_refuses_rather_than_clamping(self) -> None:
        """Found in implementation: clamping invented a reading Nat lacks.

        Before this, 76 of the 297 ground statements decided with both sides
        at zero — a quarter of the class returning DECIDED_TRUE for a reason
        that was not the statement's.
        """
        tree = census.parse("0 - 5")   # parses as neg(5) at the top
        with self.assertRaises(conform.Refusal) as caught:
            conform.eval_under_domain(
                census.parse("-5"), {}, "Nat", "truncating",
                "truncated-at-zero")
        self.assertEqual(caught.exception.construct, "negation_outside_carrier")
        # Binary subtraction is a different case and DOES truncate.
        self.assertEqual(
            conform.eval_under_domain(
                tree, {}, "Nat", "truncating", "truncated-at-zero"),
            Fraction(0),
        )

    def test_carrier_membership_is_checked_before_the_guard(self) -> None:
        self.assertTrue(conform.in_carrier(Fraction(3), "Nat"))
        self.assertFalse(conform.in_carrier(Fraction(-3), "Nat"))
        self.assertFalse(conform.in_carrier(Fraction(1, 2), "Nat"))
        self.assertTrue(conform.in_carrier(Fraction(-3), "Int"))
        self.assertTrue(conform.in_carrier(Fraction(1, 2), "Rat"))

    def test_division_by_zero_errors_rather_than_deciding(self) -> None:
        import evaluate as ev

        with self.assertRaises(ev.EvalError):
            conform.eval_under_domain(
                census.parse("1 / 0"), {}, "Rat", "exact", "signed")


class TheGroundClassIsDecided(unittest.TestCase):
    """E1, on the statements the design named before any run."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = conform_domain.load()
        cls.relations = census.evaluator_relations()

    def _run(self, corpus: str, statement_id: str) -> dict:
        node, corpus_id = _node(corpus, statement_id)
        row = census.classify(
            node, corpus_id, self.relations, self.schema.output_roles)
        program = conform.compile_statement(node, row, self.schema)
        return conform.run(program, self.schema.digest)

    def test_correction_fours_witness_decides_true_under_nat(self) -> None:
        record = self._run(
            "lean_workbook", "leanworkbook.ground.lean_workbook_plus_26988")
        self.assertEqual(record["verdict"], conform.DECIDED_TRUE)
        self.assertEqual(record["domain"]["carrier"], "Nat")
        self.assertEqual(record["domain"]["division"], "truncating")

    def test_the_two_named_before_the_run_still_fail(self) -> None:
        """Named in §3.5 so finding them again cannot be called a discovery."""
        for statement_id in (
            "leanworkbook.ground.lean_workbook_plus_16115",
            "leanworkbook.ground.lean_workbook_plus_46623",
        ):
            with self.subTest(statement_id=statement_id):
                record = self._run("lean_workbook", statement_id)
                self.assertEqual(record["verdict"], conform.DECIDED_FALSE)

    def test_a_decided_record_carries_both_exact_values(self) -> None:
        record = self._run(
            "lean_workbook", "leanworkbook.ground.lean_workbook_plus_16115")
        self.assertIn("left", record)
        self.assertIn("right", record)
        self.assertEqual(record["points_sampled"], 0,
                         "a decided statement is not sampled")

    def test_the_rendering_bound_refuses_by_name(self) -> None:
        """E0e's vocabulary: `evaluation_budget_exceeded`, never a truncation."""
        record = self._run(
            "lean_workbook", "leanworkbook.ground.lean_workbook_5646")
        self.assertEqual(record["verdict"], conform.REFUSED)
        self.assertEqual(record["refusal_reason"], "evaluation_budget_exceeded")


class RefusalsAreRefusalsNotResults(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = conform_domain.load()
        cls.relations = census.evaluator_relations()

    def test_an_authored_statement_refuses_for_an_absent_domain(self) -> None:
        node, corpus_id = _node(
            "geometry", "geometry.area_formulas.circle_area_formula")
        row = census.classify(
            node, corpus_id, self.relations, self.schema.output_roles)
        with self.assertRaises(conform.Refusal) as caught:
            conform.compile_statement(node, row, self.schema)
        self.assertIn(
            caught.exception.construct,
            {"named_constant", "defined_output", "domain_absent"},
        )

    def test_a_typed_slot_refusal_never_reaches_the_sampler(self) -> None:
        node, corpus_id = _node(
            "chemistry", "chemistry.solutions.molarity_definition")
        row = census.classify(
            node, corpus_id, self.relations, self.schema.output_roles)
        with self.assertRaises(conform.Refusal) as caught:
            conform.compile_statement(node, row, self.schema)
        self.assertEqual(caught.exception.construct, "defined_output")


class NihilDecidesRatherThanFailingToFind(unittest.TestCase):
    """§3.4 type two, and E4's shape."""

    def test_the_sqrt_two_exemplar_has_no_rational_root(self) -> None:
        record = conform.rational_root_test([-2, 0, 1])
        self.assertEqual(record["verdict"], conform.NO_SUCH_OBJECT)
        self.assertEqual(record["candidates_enumerated"], 4)
        self.assertEqual(len(record["enumeration"]), 4)

    def test_a_polynomial_with_a_root_returns_the_witness(self) -> None:
        record = conform.rational_root_test([-4, 0, 1])
        self.assertEqual(record["verdict"], conform.EXISTS)
        self.assertEqual(Fraction(record["witness"]) ** 2, 4)

    def test_out_of_class_is_returned_not_guessed(self) -> None:
        for instance in ([5], [], [0]):
            with self.subTest(instance=instance):
                self.assertEqual(
                    conform.rational_root_test(instance)["verdict"],
                    conform.OUT_OF_CLASS,
                )

    def test_the_enumeration_is_printed_exhaustively(self) -> None:
        record = conform.rational_root_test([-6, 1, 1])
        if record["verdict"] == conform.NO_SUCH_OBJECT:
            self.assertEqual(
                record["candidates_refuted"], record["candidates_enumerated"])

    def test_a_rational_root_is_found_where_one_exists(self) -> None:
        # 2x - 1 = 0 has root 1/2, which an integer-only search would miss.
        record = conform.rational_root_test([-1, 2])
        self.assertEqual(record["verdict"], conform.EXISTS)
        self.assertEqual(Fraction(record["witness"]), Fraction(1, 2))


class TheRecordCountsAreNeverConflated(unittest.TestCase):
    """§3.2: admitted, rejected and errored are three counts, never summed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = conform_domain.load()
        cls.relations = census.evaluator_relations()
        # An INEQUALITY-only guard: `10009` carries `a + b + c = 1`, which
        # the compiler now refuses as `guard_measure_zero` to match the
        # denominator E0c published.
        node, corpus_id = _node(
            "lean_workbook", "leanworkbook.skel.lean_workbook_10012")
        row = census.classify(
            node, corpus_id, cls.relations, cls.schema.output_roles)
        cls.record = conform.run(
            conform.compile_statement(node, row, cls.schema),
            cls.schema.digest, budget=200)

    def test_the_three_point_counts_are_separate_fields(self) -> None:
        for field in ("points_admitted", "points_rejected", "points_errored",
                      "points_domain_rejected", "points_sampled"):
            self.assertIn(field, self.record)

    def test_the_record_says_they_are_never_summed(self) -> None:
        self.assertIn("never summed", self.record["counts_are_never_summed"])

    def test_a_guard_that_admits_nothing_refuses(self) -> None:
        """E2a: never `NO_COUNTEREXAMPLE_FOUND` over zero admitted points."""
        if self.record["points_admitted"] == 0:
            self.assertEqual(self.record["verdict"], conform.REFUSED)
            self.assertEqual(
                self.record["refusal_reason"], "guard_measure_zero")

    def test_the_sentence_carries_the_admitted_denominator(self) -> None:
        if self.record["verdict"] == conform.NO_COUNTEREXAMPLE_FOUND:
            self.assertIn("admitted points", self.record["certifies"])
            self.assertNotIn("N admitted", self.record["certifies"])

    def test_a_nonconformant_verdict_carries_the_provisional_label(self) -> None:
        """§3.5 clause 1: EVERY one carries it, not only suspect ones."""
        if self.record["verdict"] == conform.NONCONFORMANT:
            self.assertIn("PROVISIONAL", self.record["correlated_interpretation"])
            self.assertIn("counterexample", self.record)


class AnEqualityGuardRefusesRatherThanBeingSampled(unittest.TestCase):
    """E0d/E2a: an equality conjunct is measure-zero under sampling.

    The register FROZE these as `guard_measure_zero` before the run, so the
    compiler refuses them and E2's denominator stays the one E0c published.
    A rate quoted against a denominator the register did not name is exactly
    what E0c exists to prevent.
    """

    def test_an_equality_guarded_statement_refuses_at_compile(self) -> None:
        schema = conform_domain.load()
        relations = census.evaluator_relations()
        node, corpus_id = _node(
            "lean_workbook", "leanworkbook.skel.lean_workbook_10009")
        row = census.classify(node, corpus_id, relations, schema.output_roles)
        self.assertTrue(row.guard.has_equality, "the fixture must carry one")
        with self.assertRaises(conform.Refusal) as caught:
            conform.compile_statement(node, row, schema)
        self.assertEqual(caught.exception.construct, "guard_measure_zero")


class TheRunIsDeterministic(unittest.TestCase):
    """E5: same statement, same schema, same seed -> byte-identical record."""

    def test_two_runs_of_one_statement_are_byte_identical(self) -> None:
        schema = conform_domain.load()
        relations = census.evaluator_relations()
        node, corpus_id = _node(
            "lean_workbook", "leanworkbook.skel.lean_workbook_10012")
        row = census.classify(node, corpus_id, relations, schema.output_roles)
        program = conform.compile_statement(node, row, schema)
        first = conform.run(program, schema.digest, budget=128)
        second = conform.run(program, schema.digest, budget=128)
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
