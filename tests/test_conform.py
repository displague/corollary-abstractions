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

    def test_the_artifact_scale_arm_of_e5_is_recorded_as_unrun(self) -> None:
        """The test above is ONE STATEMENT; E5 registered two full runs.

        Pinned so the smaller claim can never be mistaken for the larger
        one. `experiments/conformance_run.json` has no byte-reproduction
        proof, and the artifact must keep saying so.
        """

        block = _corrections()["e5_and_c_e1_second_arm_were_never_executed"]
        self.assertIn("UNRUN", block["status"])
        self.assertIn("NO byte-reproduction proof", block["e5"])
        self.assertIn("second", block["c_e1_second_arm"])


def _run_artifact() -> dict:
    return json.loads(
        (ROOT / "experiments" / "conformance_run.json").read_text(
            encoding="utf-8"))


def _corrections() -> dict:
    return _run_artifact()["post_run_corrections"]


class NihilRefusesEveryWayOfBeingOutOfTheClass(unittest.TestCase):
    """§3.4: `OUT_OF_CLASS` is a RETURN, and it has to be reachable.

    The existing injection test probes `[5]`, `[]`, `[0]` and `[7]` — four
    degenerate constants that all fail the same length check. None of them can
    exercise the class boundary that actually matters, which is the
    *coefficients*: the declared class is integer-coefficient univariate
    polynomials, and before 2026-08-25 the procedure coerced with `int(c)`
    rather than testing membership. So `[Fraction(1, 2), 1]` was truncated to
    `[0, 1]` and answered EXISTS with the witness "0" — a confident wrong
    answer about a different polynomial — and `['x', 1]` raised `ValueError`
    out of a procedure whose contract is that it returns rather than fails.

    These are the injection probes aimed where it CAN fail.
    """

    def test_a_non_integer_coefficient_is_out_of_class_not_truncated(self):
        record = conform.rational_root_test([Fraction(1, 2), 1])
        self.assertEqual(record["verdict"], conform.OUT_OF_CLASS)
        self.assertNotIn("witness", record)
        self.assertIn("not an integer", record["reason"])

    def test_a_float_coefficient_with_a_fractional_part_is_out_of_class(self):
        self.assertEqual(
            conform.rational_root_test([2.5, 1])["verdict"],
            conform.OUT_OF_CLASS,
        )

    def test_a_non_numeric_coefficient_returns_rather_than_raising(self) -> None:
        for probe in (["x", 1], [None, 1], [[], 1]):
            with self.subTest(probe=probe):
                record = conform.rational_root_test(probe)
                self.assertEqual(record["verdict"], conform.OUT_OF_CLASS)
                self.assertIn("not a number", record["reason"])

    def test_an_out_of_class_answer_carries_the_refusal_sentence(self) -> None:
        record = conform.rational_root_test([Fraction(1, 3), 2])
        self.assertEqual(record["certifies"],
                         conform.NIHIL_CERTIFIES[conform.OUT_OF_CLASS])

    def test_integer_valued_coefficients_stay_in_class(self) -> None:
        """The fix must not narrow the class it is protecting."""
        for probe in ([-1, 2], [Fraction(-1), 2], [-1.0, 2.0], ["-1", "2"]):
            with self.subTest(probe=probe):
                record = conform.rational_root_test(probe)
                self.assertEqual(record["verdict"], conform.EXISTS)
                self.assertEqual(record["witness"], "1/2")


class TheE4ClassIsUnchangedByTheRefusalFix(unittest.TestCase):
    """E4's 110 stand as measured: the fix moved nothing inside the class.

    `scripts/conform.py` is NOT among E7's frozen artifacts — E7 freezes the
    parser, the evaluator, the domain schema and the sampler — so the refusal
    path was repairable. What is not permitted is a repair that quietly
    re-scores a registered gate, so every committed instance is re-checked
    against the fixed procedure here and pinned to the artifact's own row.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.klass = json.loads(
            (ROOT / "data" / "domains" / "nihil_class.json").read_text(
                encoding="utf-8"))
        cls.e4 = _run_artifact()["e4"]

    def test_all_110_committed_instances_still_decide_as_registered(self) -> None:
        instances = self.klass["instances"]
        self.assertEqual(len(instances), 110)
        wrong = []
        for instance in instances:
            record = conform.rational_root_test(instance["coefficients"])
            if record["verdict"] != instance["expected"]:
                wrong.append(instance["coefficients"])
        self.assertEqual(wrong, [], "the fix moved an in-class verdict")
        self.assertEqual(self.e4["instances"], 110)
        self.assertEqual(self.e4["correct"], 110)
        self.assertEqual(self.e4["incorrect"], [])

    def test_the_enumeration_counts_are_identical_to_the_registered_run(self):
        """Not just the verdicts — the printed enumeration behind each one."""
        registered = {tuple(row["coefficients"]): row["candidates_enumerated"]
                      for row in self.e4["per_instance"]}
        self.assertEqual(len(registered), 110)
        for instance in self.klass["instances"]:
            coefficients = tuple(instance["coefficients"])
            with self.subTest(coefficients=coefficients):
                record = conform.rational_root_test(list(coefficients))
                self.assertEqual(record.get("candidates_enumerated"),
                                 registered[coefficients])

    def test_the_registered_injection_probes_still_return_out_of_class(self):
        for probe in ([5], [], [0], [7]):
            with self.subTest(probe=probe):
                self.assertEqual(
                    conform.rational_root_test(probe)["verdict"],
                    conform.OUT_OF_CLASS,
                )


class TheE4InstanceSetDigestIsRecomputable(unittest.TestCase):
    """H5: the freeze key was copied, never checked.

    `measure_conformance.py:686` lifts `instance_set_digest` out of the
    committed class file verbatim, so nothing in the tree could have noticed
    an instance list edited after its freeze — the word "frozen" was doing
    work no code backed. The recipe is recovered and pinned here instead.
    """

    def test_the_digest_is_sha256_over_the_committed_coefficient_lists(self):
        import hashlib

        klass = json.loads(
            (ROOT / "data" / "domains" / "nihil_class.json").read_text(
                encoding="utf-8"))
        payload = json.dumps([i["coefficients"] for i in klass["instances"]])
        self.assertEqual(
            hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            klass["instance_set_digest"],
        )

    def test_the_registered_run_quotes_the_same_digest(self) -> None:
        klass = json.loads(
            (ROOT / "data" / "domains" / "nihil_class.json").read_text(
                encoding="utf-8"))
        self.assertEqual(_run_artifact()["e4"]["instance_set_digest"],
                         klass["instance_set_digest"])


class TheNatClampFigureIsRecomputable(unittest.TestCase):
    """M6: the backlog's `69 of 297` had lived only in commit prose.

    The pre-fix figure — 76 ground statements deciding at `0 = 0` under a
    CLAMPING reading — is not recomputable and never will be: the clamping
    code was replaced before it was committed, and it survives only in the
    comment at `scripts/conform.py:202-207` and in commit `a58d642`'s
    message. That is recorded where the 76 is quoted. The POST-fix figure is
    recomputable, and a reader who wants to check the backlog's claim about
    the blanket `Nat` row should not have to take it on trust.
    """

    def test_69_of_the_297_ground_statements_decide_at_zero_equals_zero(self):
        schema = conform_domain.load()
        relations = census.evaluator_relations()
        ground, at_zero = 0, 0
        for path in census.corpora():
            document = json.loads(path.read_text(encoding="utf-8"))
            corpus = document.get("corpus_id", path.parent.name)
            for node in document.get("statement_nodes", []):
                row = census.classify(node, corpus, relations,
                                      schema.output_roles)
                try:
                    program = conform.compile_statement(node, row, schema)
                except conform.Refusal:
                    continue
                if program.variables:
                    continue
                record = conform.run(program, schema.digest, budget=0)
                ground += 1
                if record.get("left") == "0" and record.get("right") == "0":
                    at_zero += 1
        self.assertEqual(ground, 297)
        self.assertEqual(at_zero, 69)
        self.assertEqual(_run_artifact()["e1"]["ground_statements"], 297)


class TheTruncatingInverseHasADeclaredReading(unittest.TestCase):
    """L2: `inv` under truncating division was applying an undeclared rule.

    The schema is E7-frozen, so the declaration lives in the branch's own
    comment. What is pinned here is that the reading the comment declares is
    the reading the code applies, and that the reading is the same operator
    the `*` node uses rather than a second, quieter one.
    """

    def test_a_bare_inverse_floors_like_the_carriers_own_division(self) -> None:
        tree = census.parse("1 / 4")
        self.assertEqual(
            conform.eval_under_domain(
                tree, {}, "Nat", "truncating", "truncated-at-zero"),
            Fraction(0),
        )
        self.assertEqual(
            conform.eval_under_domain(tree, {}, "Rat", "exact", "signed"),
            Fraction(1, 4),
        )

    def test_the_declaration_is_written_where_the_rule_is_applied(self) -> None:
        source = (ROOT / "scripts" / "conform.py").read_text(encoding="utf-8")
        branch = source.split('if op == "inv":', 1)[1].split('if op == "^"')[0]
        self.assertIn("DECLARED READING", branch)
        self.assertIn("WHERE THE DECLARATION STOPS", branch)
        returns = [line.strip() for line in branch.splitlines()
                   if line.strip().startswith("return")]
        self.assertEqual(returns,
                         ["return Fraction(1 // inner)",
                          "return Fraction(1) / inner"],
                         "the dead zero arm should be gone with the fix")


class ThePostRunCorrectionsAreCheckableAgainstTheRowsTheyCorrect(
        unittest.TestCase):
    """The dated block in `conformance_run.json`, recomputed rather than read.

    A correction that only asserts something is worth no more than the claim
    it replaced. Every arithmetic sentence in `post_run_corrections` that can
    be recomputed from the artifact's own scored rows is recomputed here, so
    a reader who doubts the block can run this file instead of trusting it.

    The scored rows are NEVER edited by that block or by this test; the
    review rule for this branch is that the void stands and only the record
    around it moves.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = _run_artifact()
        cls.block = cls.artifact["post_run_corrections"]

    def test_the_block_is_dated_and_says_it_re_ran_nothing(self) -> None:
        self.assertEqual(self.block["dated"], "2026-08-25")
        self.assertIn("re-scored", self.block["nothing_below_re_runs_anything"])

    def test_c_e3_attempted_25_sampled_counterexamples_and_not_27(self) -> None:
        """M5: the 27 counted two ground `DECIDED_FALSE` ids as sampled."""
        adjudicated = self.artifact["c_e3"]["adjudicated"]
        ground = {row["statement_id"]
                  for row in self.artifact["e1"]["decided_false_exhaustively"]}
        self.assertEqual(len(ground), 15)
        sampled = [row for row in adjudicated
                   if row["statement_id"] not in ground]
        self.assertEqual(len(sampled), 25)
        # And every one of them is the instrument gap, not an adjudication.
        self.assertEqual(
            {row["reason"] for row in sampled},
            {"decide did not reduce in either direction"},
        )
        # Two of the fifteen ground ids carry a `skel.` prefix, which is what
        # a prefix-based count sorted onto the sampled side.
        self.assertEqual(
            sum(1 for sid in ground if ".ground." not in sid), 2)

    def test_twelve_of_fifteen_ground_verdicts_were_confirmed(self) -> None:
        adjudicated = self.artifact["c_e3"]["adjudicated"]
        confirmed = [row for row in adjudicated if row.get("available")]
        self.assertEqual(len(confirmed), 12)
        self.assertTrue(all(row["agrees"] for row in confirmed))
        self.assertEqual(self.artifact["e1"]["decided_false"], 15)

    def test_no_scored_counterexample_row_carries_the_provisional_label(self):
        """H2: the label is real at runtime and absent from the artifact."""
        rows = self.artifact["e2"]["counterexamples_exhaustively"]
        self.assertEqual(len(rows), 775)
        self.assertEqual(
            [row for row in rows if "correlated_interpretation" in row], [])
        # Not one appears anywhere under the scored gates either — the only
        # occurrences in the file are inside `post_run_corrections`, where
        # this correction names the field it is about.
        scored = {key: value for key, value in self.artifact.items()
                  if key != "post_run_corrections"}
        self.assertNotIn("correlated_interpretation", json.dumps(scored))
        # ...and it IS emitted where the design says it must be. The
        # existing runtime assertion is
        # `TheRecordCountsAreNeverConflated.test_a_nonconformant_verdict
        # _carries_the_provisional_label`; this half only fixes which of the
        # two objects carries it, so a reader is not left believing both do.
        self.assertIn(
            "WRITER DEFECT",
            self.block["the_exhaustive_counterexample_rows_carry_no"
                       "_correlated_interpretation_label"]["what_went_wrong"],
        )

    def test_the_two_zero_side_figures_are_different_statistics(self) -> None:
        """M5: 33.2% is `left == "0"`; the falsifying side is 35.9%."""
        rows = self.artifact["e2"]["counterexamples_exhaustively"]
        left_zero = sum(1 for r in rows if r["counterexample"]["left"] == "0")
        self.assertEqual(left_zero, 257)
        self.assertEqual(round(left_zero / len(rows) * 100, 1), 33.2)

        def falsifying(row):
            cx = row["counterexample"]
            if cx["relation"] in {">=", ">"}:
                return cx["left"]
            if cx["relation"] in {"<=", "<"}:
                return cx["right"]
            return None

        side_zero = sum(1 for r in rows if falsifying(r) == "0")
        self.assertEqual(side_zero, 278)
        self.assertEqual(round(side_zero / len(rows) * 100, 1), 35.9)

    def test_the_admitted_count_is_a_break_on_first_count(self) -> None:
        """H3: `admitted == 1` is the sampler's best case, not its worst."""
        rows = self.artifact["e2"]["counterexamples_exhaustively"]
        first_point = sum(1 for r in rows if r["admitted"] == 1)
        self.assertEqual(first_point, 358)
        self.assertEqual(round(first_point / len(rows) * 100, 1), 46.2)
        source = (ROOT / "scripts" / "conform.py").read_text(encoding="utf-8")
        # The `break` that gives the field this meaning, quoted from source.
        counterexample_arm = source.split("counterexample = {", 1)[1]
        self.assertIn("break", counterexample_arm.split("record.update", 1)[0])
        self.assertIn("BREAKS out of the point loop",
                      self.block["the_admitted_count_inference_was_inverted"]
                      ["the_semantics"])

    def test_the_perturbation_table_has_four_rows_of_a_five_class_generator(
            self) -> None:
        """M2: `reassociate_an_operator` never fired, and that explains the 0."""
        per_class = self.artifact["c_e1"]["per_class"]
        self.assertEqual(len(per_class), 4)
        self.assertNotIn("reassociate_an_operator", per_class)
        published = self.block[
            "c_e1_per_class_is_a_four_row_table_of_a_five_class_generator"][
                "the_five_class_table_as_published_plus_the_zero_row"]
        self.assertEqual(len(published), 5)
        for name, row in per_class.items():
            for field in ("discarded", "flipped", "generated", "surviving"):
                self.assertEqual(published[name][field], row[field],
                                 f"{name}.{field} was republished wrong")
        self.assertEqual(published["reassociate_an_operator"]["generated"], 0)
        self.assertEqual(self.artifact["c_e1"]["discarded_as_non_mutations"], 0)

    def test_the_samplable_refused_split_is_derivable_from_the_rows(self) -> None:
        """M9: 214 = 173 `guard_measure_zero` + 41 all-points-errored."""
        e2, e3 = self.artifact["e2"], self.artifact["e3"]
        admitted_nothing = (e2["denominator"]
                            - e2["statements_admitting_at_least_one_point"])
        self.assertEqual(admitted_nothing, 173)
        self.assertEqual(e3["buckets"]["samplable_refused"], 214)
        self.assertEqual(214 - admitted_nothing, 41)
        derived = self.block[
            "samplable_refused_214_has_no_per_statement_breakdown_but_the"
            "_split_is_derivable"]["derivable_from_this_artifact_alone"]
        self.assertIn("173", derived)
        self.assertIn("41", derived)

    def test_the_block_is_the_only_thing_that_moved(self) -> None:
        """The artifact still round-trips through its own writer, unchanged.

        `scripts/measure_conformance.py` writes with `indent=2`,
        `ensure_ascii=False` and `sort_keys=True`. If the correction block
        had been pasted in at the end of the file, or with a different
        indent, this would fail — which is the point: an append that breaks
        the writer's conventions is an edit to the artifact's format, and
        this branch is not permitted one.
        """

        raw = (ROOT / "experiments" / "conformance_run.json").read_text(
            encoding="utf-8")
        rendered = json.dumps(json.loads(raw), indent=2, ensure_ascii=False,
                              sort_keys=True) + "\n"
        self.assertEqual(rendered, raw)


if __name__ == "__main__":
    unittest.main()
