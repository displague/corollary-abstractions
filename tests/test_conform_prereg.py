#!/usr/bin/env python3
"""The preregistration step: the schema's gate, the sampler, and the census.

`docs/DESIGN-statements-that-run.md` §5 asks for the domain schema committed
with its digest **before the compiler exists**, with *"the refusal path
exercised by injection rather than accident"* — so every load-gate clause
below is tested by handing the loader a table that violates it, not by
hoping the committed one never does.

E5 (determinism) and E7 (the freeze) are the other two subjects. E6's closed
seat is asserted structurally: the sampler imports nothing learned and its
point set is a function of committed digests.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import conform_census as census  # noqa: E402
import conform_domain  # noqa: E402
import conform_sampler as sampler  # noqa: E402

PREREG = ROOT / "experiments" / "conformance_prereg.json"


def _valid_table() -> dict:
    return json.loads(
        (ROOT / "data" / "domains" / "domain_schema.json").read_text(
            encoding="utf-8")
    )


class TheSchemaLoadsUnderItsOwnGate(unittest.TestCase):
    """v0.19's lexicon rule: a table that fails its gate RAISES."""

    def test_the_committed_table_loads(self) -> None:
        schema = conform_domain.load()
        self.assertEqual(schema.schema_id, "conformance.domain_schema.v1")
        self.assertIn("Nat", schema.carriers)
        self.assertTrue(schema.class_rows)
        self.assertTrue(schema.output_roles)

    def test_the_lean_workbook_class_row_declares_truncating_division(self):
        """Correction 4's whole point, read off the committed table."""
        schema = conform_domain.load()
        row = schema.carrier_for(
            "leanworkbook.ground.lean_workbook_plus_26988",
            "lean_workbook.ground.v1",
        )
        self.assertIsNotNone(row)
        self.assertEqual(row["carrier"], "Nat")
        self.assertEqual(row["division"], "truncating")

    def test_an_authored_statement_has_no_row_and_that_is_a_refusal(self):
        """§3.3: domain absence is a refusal, never a default."""
        schema = conform_domain.load()
        self.assertIsNone(
            schema.carrier_for(
                "geometry.area_formulas.circle_area_formula",
                "geometry.foundations.v1",
            ),
            "an authored statement must not inherit a carrier by default",
        )


class TheGateRefusesByInjection(unittest.TestCase):
    """Each clause exercised by a table that violates it (§5)."""

    def _refuses(self, mutate) -> str:
        table = _valid_table()
        mutate(table)
        with self.assertRaises(conform_domain.DomainSchemaError) as caught:
            conform_domain.build(table, "<injected>")
        return str(caught.exception)

    def test_a_missing_schema_id_refuses(self) -> None:
        self.assertIn("schema_id", self._refuses(lambda t: t.pop("schema_id")))

    def test_an_empty_carrier_list_refuses(self) -> None:
        self.assertIn("carriers", self._refuses(
            lambda t: t.__setitem__("carriers", [])))

    def test_a_class_row_with_an_unknown_carrier_refuses(self) -> None:
        message = self._refuses(
            lambda t: t["class_rows"][0].__setitem__("carrier", "Complex"))
        self.assertIn("Complex", message)

    def test_a_class_row_missing_a_reading_refuses(self) -> None:
        message = self._refuses(lambda t: t["class_rows"][0].pop("division"))
        self.assertIn("division", message)

    def test_a_class_row_indexed_by_an_unsupported_field_refuses(self) -> None:
        message = self._refuses(
            lambda t: t["class_rows"][0].__setitem__("applies_to", "vibes"))
        self.assertIn("corpus_id", message)

    def test_two_rows_for_one_statement_refuses(self) -> None:
        """A statement with two declared domains has none."""
        row = {"statement_id": "x.y.z", "carrier": "Nat"}
        message = self._refuses(
            lambda t: t.__setitem__("statement_rows", [row, dict(row)]))
        self.assertIn("more than one row", message)

    def test_an_output_role_without_a_witness_refuses(self) -> None:
        """A reviewed artifact nobody can check is not reviewed."""
        message = self._refuses(
            lambda t: t["reviewed_output_roles"]["roles"].append(
                {"role": "invented_role"}))
        self.assertIn("witness", message)

    def test_a_branch_cut_without_an_id_refuses(self) -> None:
        message = self._refuses(
            lambda t: t["branch_cuts"].append({"rule": "refuse"}))
        self.assertIn("cut_id", message)

    def test_a_table_that_is_not_an_object_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "schema.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(conform_domain.DomainSchemaError):
                conform_domain.load(path)


class TheSamplerIsAFunctionOfCommittedArtifacts(unittest.TestCase):
    """E5: same schema, same seed, same points. A seed chosen would be a knob."""

    def test_the_seed_derives_from_the_schema_digest(self) -> None:
        first = sampler.derive_seed("digest-a", "stmt.one")
        self.assertEqual(first, sampler.derive_seed("digest-a", "stmt.one"))
        self.assertNotEqual(first, sampler.derive_seed("digest-b", "stmt.one"))
        self.assertNotEqual(first, sampler.derive_seed("digest-a", "stmt.two"))

    def test_two_samplings_are_byte_identical(self) -> None:
        first = sampler.sample_points(("a", "b"), "d", "s", budget=64)
        second = sampler.sample_points(("a", "b"), "d", "s", budget=64)
        self.assertEqual([p.printable() for p in first],
                         [p.printable() for p in second])

    def test_points_are_exact_rationals(self) -> None:
        for point in sampler.sample_points(("a",), "d", "s", budget=32):
            for _name, value in point.bindings:
                self.assertIsInstance(value, Fraction)

    def test_the_pool_reaches_sign_zero_and_non_integers(self) -> None:
        """A pool of positive integers would not test a statement's edges."""
        values = {
            value
            for point in sampler.sample_points(("a",), "d", "s", budget=400)
            for _name, value in point.bindings
        }
        self.assertTrue(any(v < 0 for v in values), "no negative point")
        self.assertIn(Fraction(0), values)
        self.assertTrue(any(v.denominator != 1 for v in values),
                        "no non-integer point")

    def test_no_variables_means_no_points(self) -> None:
        self.assertEqual(sampler.sample_points((), "d", "s"), [])

    def test_nothing_learned_sits_in_the_sampler(self) -> None:
        """E6 / §9: the one seat a ranker could take, closed in writing."""
        source = (ROOT / "scripts" / "conform_sampler.py").read_text(
            encoding="utf-8")
        for forbidden in ("torch", "sklearn", "numpy.random", "import random"):
            self.assertNotIn(forbidden, source)


class TheCensusReproducesTheDesignsWalk(unittest.TestCase):
    """§3.1's shape walk, whose numbers the design published before this lane."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = conform_domain.load()
        cls.rows = list(census.walk(output_roles=cls.schema.output_roles))

    def test_the_shape_walk_matches_the_designs_census_exactly(self) -> None:
        parses = sum(1 for r in self.rows if r.parses)
        shaped = sum(1 for r in self.rows if r.evaluable_shaped)
        ground = sum(1 for r in self.rows if r.ground)
        self.assertEqual(len(self.rows), 12777)
        self.assertEqual(parses, 8586)
        self.assertEqual(shaped, 8476)
        self.assertEqual(ground, 297)
        self.assertEqual(shaped - ground, 8179)

    def test_the_shape_exclusions_match_the_design(self) -> None:
        counts: dict[str, int] = {}
        for row in self.rows:
            if row.shape_exclusion:
                counts[row.shape_exclusion] = counts.get(row.shape_exclusion, 0) + 1
        self.assertEqual(counts["does_not_parse"], 4191)
        self.assertEqual(counts["not_a_top_level_relation"], 10)
        self.assertEqual(counts["nested_relation"], 1)
        self.assertEqual(counts["head_outside_evaluator"], 98)
        self.assertEqual(counts["relation_undecidable"], 1)

    def test_every_statement_lands_in_exactly_one_bucket(self) -> None:
        """E3's partition property, asserted on the classification itself."""
        self.assertTrue(all(r.bucket for r in self.rows))
        self.assertEqual(len(self.rows), 12777)

    def test_the_guard_is_read_from_the_template_not_the_ascii(self) -> None:
        """Correction 3: the ascii field is the conclusion, hypotheses deleted."""
        row = next(
            r for r in self.rows
            if r.statement_id == "leanworkbook.skel.lean_workbook_10009"
        )
        self.assertTrue(row.guard.present)
        self.assertEqual(
            row.guard.source_field,
            "structural_signature.anonymized_template",
        )
        self.assertGreaterEqual(len(row.guard.conjuncts), 4)
        self.assertTrue(row.guard.has_equality, "a + b + c = 1 is the fourth")

    def test_a_constant_slot_refuses_rather_than_being_sampled(self) -> None:
        """§3.2.1: pi's declared value is a twelve-digit decimal, not pi."""
        row = next(
            r for r in self.rows
            if r.statement_id == "geometry.area_formulas.circle_area_formula"
        )
        self.assertEqual(row.bucket, "refused_typed_slot")
        self.assertIn(row.typed_refusal, {"named_constant", "defined_output"})

    def test_a_definitional_equality_refuses(self) -> None:
        """The pilot that falsified `A = s^2` is what this rule prevents."""
        row = next(
            r for r in self.rows
            if r.statement_id == "chemistry.solutions.molarity_definition"
        )
        self.assertEqual(row.typed_refusal, "defined_output")

    def test_the_single_authored_inequality_survives(self) -> None:
        """The design predicts exactly one authored candidate; check it is here."""
        row = next(
            r for r in self.rows
            if r.statement_id == "difftop.morse.weak_morse_inequality"
        )
        self.assertNotEqual(row.bucket, "refused_typed_slot")
        self.assertTrue(row.evaluable_shaped)

    def test_an_undeclared_slot_is_refused_not_sampled(self) -> None:
        """Fail closed: 'sample only kind = variable' admits one category."""
        refusals = {
            r.typed_refusal for r in self.rows if r.typed_refusal
        }
        self.assertIn("slot_alignment_failed", refusals)


class TheFreezeIsRecordedBeforeTheCompiler(unittest.TestCase):
    """E7, and the ordering that makes it a freeze rather than a note."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(PREREG.read_text(encoding="utf-8"))

    def test_every_frozen_digest_matches_the_tree(self) -> None:
        """E7's sweep, re-aimed 2026-08-26 for the first retired row.

        The v0.21 session-ledger lane moved scripts/evaluate.py after this
        freeze, and the v0.21 gate's first run went red here -- the freeze
        doing its job. The row is retired by dated amendment with its
        successor pin, so the sweep now uses the shared transitive walk
        (scripts/prereg_pins.py, built for exactly this at the v0.20
        integration): an unretired row must match the tree; a retired row
        must match the pin at the END of its declared chain. Any change
        past the last amendment is still red.
        """
        from prereg_pins import check_frozen
        for record in check_frozen(
                self.doc,
                prereg_path="experiments/conformance_prereg.json",
                repo_root=ROOT):
            with self.subTest(role=record["role"]):
                self.assertIsNotNone(
                    record["observed_sha256_lf"],
                    f"{record['path']} is not in the tree")
                self.assertTrue(
                    record["agrees"],
                    f"E7 VOID: {record['path']} matches neither its recorded "
                    f"pin nor the pin at the end of its retirement chain "
                    f"(live pin from {record['live_pin_source']}, walked via "
                    f"{record['retirement_hops'] or 'no amendments'}). A "
                    f"change past the last amendment needs its own review "
                    f"naming the reason.")

    def test_the_four_the_design_names_are_all_frozen(self) -> None:
        roles = {row["role"] for row in self.doc["frozen"]}
        self.assertLessEqual(
            {"parser", "evaluator", "domain_schema", "sampler"}, roles)

    def test_the_e0_series_is_adjudicated_in_writing(self) -> None:
        adjudication = self.doc["e0_series_adjudication"]
        self.assertEqual(adjudication["E0"]["status"], "DISCHARGED")
        self.assertEqual(adjudication["E0e"]["status"], "DISCHARGED")
        self.assertIn("§4b", adjudication["E0"]["owner"])
        self.assertIn("§4c", adjudication["E0e"]["owner"])
        self.assertTrue(adjudication["E0"]["evidence"])

    def test_e0b_clears_its_floor(self) -> None:
        table = self.doc["census"]["e0b_guard_recovery_table"]
        self.assertGreaterEqual(table["total_compiling"], table["floor"])
        self.assertTrue(table["floor_met"])

    def test_the_census_reconciles_with_the_designs_preview(self) -> None:
        """Where this lane's numbers differ, the difference is explained."""
        reconciliation = self.doc["census"]["reconciliation_with_the_designs_preview"]
        self.assertIn("Correction 2", reconciliation["why_the_numbers_differ"])
        self.assertIn("design_preview", reconciliation)

    def test_the_writer_refuses_once_the_compiler_exists(self) -> None:
        """A freeze recorded after the thing it constrains is not a freeze."""
        import write_conformance_prereg as writer

        self.assertEqual(writer.COMPILER, "scripts/conform.py")
        if (ROOT / writer.COMPILER).exists():
            self.assertEqual(writer.main([]), 2)


if __name__ == "__main__":
    unittest.main()
