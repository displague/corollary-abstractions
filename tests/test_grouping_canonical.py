#!/usr/bin/env python3
"""G-P and G0: the parser, the canonical emitter, and the census they produced.

DESIGN-voice-completion §6 asks G-P for exactly two properties, and this file
asserts both **over all 2,313 covered statements** rather than over examples:

  (i)  every covered statement round-trips `parse → emit → parse` to the same
       tree, compared by a signature that erases grouping brackets — because a
       bracket is how the source *wrote* the shape, not part of the shape, and
       comparing raw nodes would compare the thing canonicalization is allowed
       to change;
  (ii) emission is idempotent, `canon(canon(x)) == canon(x)`.

Plus the claim the whole design rests on and the one that nearly slipped:

  **it can only remove.** A parsing source already follows precedence, so the
  canonical form can only drop brackets. The census's no-negative-bucket check
  caught a real defect during construction — the first transcription of the
  tail-position clause made the emitter ADD a bracket on exactly one statement
  of 2,313 — and that is why the assertion is over the corpus and not over a
  handful of cases.

The oracle-backed gates G1 and G1b live in `tests/test_grouping_agreement.py`
beside their artifact; nothing here calls the pinned binary.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import grouping_canonical_probe as gp  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402

DATA = ROOT / "data" / "foreign_voice"
CENSUS_PATH = ROOT / "experiments" / "grouping_census.json"
RULE = gp.Rule.load()


def _covered() -> list[dict]:
    preview = json.loads((DATA / "eligibility_preview.json").read_text(encoding="utf-8"))
    register = json.loads((DATA / "register.json").read_text(encoding="utf-8"))
    return mfv.covered_rows(preview, register)


COVERED = _covered()
SEALED = json.loads((DATA / "b0d_sealed_renderings.json").read_text(encoding="utf-8"))


class TheRuleIsAnArtifact(unittest.TestCase):
    """§3.1: trusted and reviewed, like rule R — not renderer logic."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = json.loads((DATA / "grouping.json").read_text(encoding="utf-8"))

    def test_the_loader_reads_every_level_from_the_file(self) -> None:
        self.assertEqual(len(RULE.infix), len(self.raw["levels"]))
        self.assertEqual(len(RULE.prefix), len(self.raw["prefix"]))

    def test_the_measured_levels_are_the_ones_the_probe_found(self) -> None:
        """Spot-checks of the table read off the pinned binary."""
        self.assertEqual(RULE.infix["^"], (75, "right"))
        self.assertEqual(RULE.infix["*"], (70, "left"))
        self.assertEqual(RULE.infix["+"], (65, "left"))
        self.assertEqual(RULE.infix["="], (50, "none"))
        self.assertEqual(RULE.infix["∧"], (35, "right"))
        self.assertEqual(RULE.infix["∨"], (30, "right"))
        self.assertEqual(RULE.infix["→"], (25, "right"))
        self.assertEqual(RULE.infix["↔"], (20, "none"))
        self.assertEqual(RULE.prefix["¬"], 40)
        self.assertEqual(RULE.prefix["-"], 75)

    def test_the_ascii_orderings_sit_at_the_relation_level(self) -> None:
        """The digraph rows v0.19 added by dated correction, carried here."""
        self.assertEqual(RULE.infix[">="], RULE.infix["≥"])
        self.assertEqual(RULE.infix["<="], RULE.infix["≤"])

    def test_a_bad_associativity_refuses_at_load(self) -> None:
        raw = json.loads(json.dumps(self.raw))
        raw["levels"][0]["associativity"] = "sideways"
        import tempfile
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "grouping.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(gp.GroupingError):
                gp.Rule.load(path)

    def test_the_two_supplied_clauses_are_written_down(self) -> None:
        """Correction 3: a reader must not reverse-engineer them from a program."""
        self.assertTrue(self.raw["binder_group_rule"]["strip"])
        self.assertTrue(self.raw["ascription_rule"]["never_a_grouping_pair"])
        self.assertIn("tail_propagates_through", self.raw["binder_tail_rule"])
        self.assertIn("a_bracket_restores_tail", self.raw["binder_tail_rule"])


class GPRoundTrips(unittest.TestCase):
    """G-P(i) and G-P(ii), over the whole covered set."""

    def test_every_covered_statement_parses(self) -> None:
        failures = []
        for row in COVERED:
            try:
                gp.parse(row["interpreted"], RULE)
            except gp.GroupingError as exc:
                failures.append((row["statement_id"], str(exc)))
        self.assertEqual(failures, [])

    def test_parse_emit_parse_yields_the_same_tree(self) -> None:
        """G-P(i). Compared by a signature that erases grouping brackets."""
        mismatches = []
        for row in COVERED:
            before = gp.parse(row["interpreted"], RULE)
            after = gp.parse(gp.canon(row["interpreted"], RULE), RULE)
            if gp.signature(before) != gp.signature(after):
                mismatches.append(row["statement_id"])
        self.assertEqual(mismatches, [])

    def test_emission_is_idempotent(self) -> None:
        """G-P(ii). `canon(canon(x)) == canon(x)`, all 2,313."""
        mismatches = []
        for row in COVERED:
            once = gp.canon(row["interpreted"], RULE)
            if gp.canon(once, RULE) != once:
                mismatches.append(row["statement_id"])
        self.assertEqual(mismatches, [])

    def test_it_never_adds_a_bracket(self) -> None:
        """The claim §3.1 makes and the census checks. One counterexample refutes it."""
        gained = []
        for row in COVERED:
            node = gp.parse(row["interpreted"], RULE)
            emission = gp.emit(node, RULE)
            before = gp.source_pairs(node).count("grouping")
            after = emission.pair_kinds.count("grouping")
            if after > before:
                gained.append((row["statement_id"], before, after))
        self.assertEqual(gained, [])

    def test_the_statement_that_caught_the_tail_bug_stays_fixed(self) -> None:
        """A regression pin on the one statement in 2,313 that found it.

        `(B → ∀ x y z : Rat, body)` must not come back as
        `(B → (∀ x y z : Rat, body))`. Before the fix it did, and nothing else
        in the corpus noticed.
        """
        row = next(r for r in COVERED
                   if r["statement_id"].endswith("lean_workbook_plus_82031"))
        node = gp.parse(row["interpreted"], RULE)
        emission = gp.emit(node, RULE)
        self.assertEqual(emission.pair_kinds.count("grouping"),
                         gp.source_pairs(node).count("grouping"))


class TheThreeKindsOfParenthesis(unittest.TestCase):
    """Correction 2: only one of the three is a grouping bracket."""

    def test_an_ascription_is_never_a_grouping_pair(self) -> None:
        node = gp.parse("∀ x : Rat, (36 : Rat) / x = 1", RULE)
        self.assertEqual(gp.source_pairs(node), ["ascription"])
        emission = gp.emit(node, RULE)
        self.assertEqual(emission.pair_kinds, ["ascription"])
        self.assertIn("( 36 : Rat )", " ".join(emission.tokens))

    def test_an_ascription_survives_canonicalization_untouched(self) -> None:
        """Its brackets ARE the ascription. Removing them changes the term."""
        text = "∀ x : Rat, (36 : Rat) ≤ x"
        self.assertIn("( 36 : Rat )", gp.canon(text, RULE))

    def test_a_binder_group_is_stripped(self) -> None:
        node = gp.parse("∃ (x y : Rat), x = y", RULE)
        self.assertEqual(gp.source_pairs(node), ["binder_group"])
        self.assertEqual(gp.canon("∃ (x y : Rat), x = y", RULE),
                         "∃ x y : Rat , x = y")

    def test_a_grouping_pair_is_removed_only_when_redundant(self) -> None:
        self.assertEqual(gp.canon("∀ a b : Rat, (a + b) = a + b", RULE),
                         "∀ a b : Rat , a + b = a + b")
        self.assertEqual(gp.canon("∀ a b : Rat, (a + b) * a = a", RULE),
                         "∀ a b : Rat , ( a + b ) * a = a")

    def test_the_census_records_the_kind_per_statement(self) -> None:
        census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(census["statements"]), len(COVERED))
        for row in census["statements"][:50]:
            for kind in row["pair_kinds_source"]:
                self.assertIn(kind, ("grouping", "ascription", "binder_group"))


class TailPositionAndPrecedence(unittest.TestCase):
    """The two supplied clauses, and the measured levels, as behaviour."""

    def test_a_binder_in_tail_position_needs_no_bracket(self) -> None:
        self.assertEqual(gp.canon("¬ ∃ x : Rat, x = x", RULE),
                         "¬ ∃ x : Rat , x = x")

    def test_a_binder_out_of_tail_position_keeps_its_bracket(self) -> None:
        text = "∀ z : Rat, (∀ x : Rat, x = x) ∧ z = z"
        self.assertIn("( ∀ x : Rat , x = x ) ∧", gp.canon(text, RULE))

    def test_a_bracket_restores_tail_position(self) -> None:
        """The clause whose first transcription was backwards."""
        text = "∀ V a b : Rat, (a = 1 → V = 2) ∧ (b = 1 → ∀ x : Rat, x = V)"
        out = gp.canon(text, RULE)
        self.assertIn("→ ∀ x : Rat , x = V )", out)
        self.assertNotIn("→ ( ∀", out)

    def test_precedence_removes_only_what_precedence_implies(self) -> None:
        self.assertEqual(gp.canon("∀ a b c : Rat, a + (b * c) = a", RULE),
                         "∀ a b c : Rat , a + b * c = a")
        self.assertEqual(gp.canon("∀ a b c : Rat, (a + b) * c = a", RULE),
                         "∀ a b c : Rat , ( a + b ) * c = a")

    def test_associativity_is_respected_in_both_directions(self) -> None:
        self.assertEqual(gp.canon("∀ a b c : Rat, (a - b) - c = a", RULE),
                         "∀ a b c : Rat , a - b - c = a")
        self.assertIn("a - ( b - c )",
                      gp.canon("∀ a b c : Rat, a - (b - c) = a", RULE))
        self.assertEqual(gp.canon("∀ a b c : Nat, a ^ (b ^ c) = a", RULE),
                         "∀ a b c : Nat , a ^ b ^ c = a")
        self.assertIn("( a ^ b )",
                      gp.canon("∀ a b c : Nat, (a ^ b) ^ c = a", RULE))

    def test_a_non_associative_chain_is_refused_rather_than_invented(self) -> None:
        """`a = b = c` is not a term in this toolchain, so it is not one here.

        This test failed on its first run and found a real gap: the parser had
        happily read it as `(∀ a b c : Rat, a = b) = c`, re-associating an input
        the pinned binary REJECTS. An unbracketed binder can never be the left
        operand of an infix operator — its body would have swallowed it — and
        the parser now says so.
        """
        with self.assertRaises(gp.GroupingError):
            gp.parse("∀ a b c : Rat, a = b = c", RULE)
        with self.assertRaises(gp.GroupingError):
            gp.parse("∀ a b c : Rat, a = b ∧ b = c ∧ c = a → a = b = c", RULE)

    def test_an_unbracketed_binder_cannot_be_a_left_operand(self) -> None:
        """There is no input that expresses it, which is the point.

        `∀ x : Rat, x = x ∧ q` reads the `∧` into the BODY — the binder
        swallowed it — so an unbracketed binder can never be a left operand.
        Getting the operator outside requires the bracket, and the bracket is
        then not redundant and stays.
        """
        node = gp.parse("∀ q : Rat, ∀ x : Rat, x = x ∧ q = q", RULE)
        self.assertEqual(gp.signature(node)[0], "binder")
        self.assertIn("( ∀ x : Rat , x = x ) ∧",
                      gp.canon("∀ z : Rat, (∀ x : Rat, x = x) ∧ z = z", RULE))

    def test_the_unary_minus_binds_looser_than_a_power(self) -> None:
        self.assertEqual(gp.canon("∀ a : Rat, -(a ^ 2) = a", RULE),
                         "∀ a : Rat , - a ^ 2 = a")


class TheCensusIsG0(unittest.TestCase):
    """The §3 probe: published before the rule is proposed, and with no floor."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))

    def test_it_reproduces_from_the_committed_tree(self) -> None:
        again = gp.census(COVERED, SEALED["renderings"], RULE)
        self.assertEqual(again["pairs"], self.census["pairs"])
        self.assertEqual(again["covered"], self.census["covered"])
        self.assertEqual(again["sealed_hundred"], self.census["sealed_hundred"])

    def test_it_has_no_floor_and_says_why(self) -> None:
        self.assertIn("no_floor", self.census)
        self.assertIn("ORDERING", self.census["no_floor"])

    def test_the_exposure_counts_are_labelled_exposure(self) -> None:
        """They say how much surface moved, not whether it helped a reader."""
        label = self.census["exposure"]["label"]
        self.assertIn("EXPOSURE, NOT READABILITY", label)
        self.assertIn("C-V3", label)
        self.assertIn("ABSENT", label)

    def test_the_delta_distribution_has_no_negative_bucket(self) -> None:
        for key in self.census["it_can_only_remove"]["delta_distribution"]:
            self.assertGreaterEqual(int(key), 0)
        self.assertEqual(self.census["it_can_only_remove"]["gained_a_bracket"], 0)

    def test_the_sealed_split_is_fifteen_and_eighty_five(self) -> None:
        sealed = self.census["sealed_hundred"]
        self.assertEqual(sealed["statements"], 100)
        self.assertEqual(sealed["parse_failures"], 0)
        self.assertEqual(sealed["changed"], 15)
        self.assertEqual(sealed["byte_identical"], 85)
        self.assertEqual(sealed["gained_a_bracket"], 0)
        self.assertEqual(len(sealed["changed_ids"]), 15)

    def test_the_pool_arithmetic_is_published_for_g5b(self) -> None:
        pool = self.census["drop_group_pool"]
        self.assertEqual(pool["v019_admitting"], 1549)
        self.assertEqual(
            pool["admitting_through_a_real_grouping_pair"]
            + pool["admitting_only_through_ascription_or_binder_group"],
            pool["v019_admitting"])
        self.assertLess(pool["canonical_admitting"], pool["v019_admitting"])

    def test_the_v019_pool_reproduces_the_shipped_artifact(self) -> None:
        """1,549 is the number v0.19's own run recorded. If it moved, so did the tree."""
        rate = json.loads(
            (ROOT / "experiments" / "foreign_voice_rate.json").read_text(encoding="utf-8"))
        self.assertEqual(self.census["drop_group_pool"]["v019_admitting"],
                         rate["c_v4"]["per_class"]["drop_group"]["admitting"])


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
