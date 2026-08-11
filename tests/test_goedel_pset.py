"""Goedel-Pset-v1 scale coverage: manifest pin, the self-checking audit fields,
internal consistency of the aggregate measurement, and regression tests for the
no-head operator/constructor glyphs the 1.73M-scale run surfaced.

Unlike the miniF2F / Lean-workbook slices there is no committed per-statement
extract (it would be ~300 MB), so the coverage.json cannot be regenerated in CI
from committed data. Instead the artifact is SELF-CHECKING: it carries the
false-positive audit counts, which must be 0, and its totals/dup fields must be
internally consistent. Reproduction from the pinned parquets is a manual step.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import grammar_coverage as gc  # noqa: E402

MANIFEST = json.loads(
    (REPO_ROOT / "data_sources" / "manifest.json").read_text(encoding="utf-8")
)
COVERAGE = json.loads(
    (REPO_ROOT / "experiments" / "goedel_pset_coverage.json").read_text(encoding="utf-8")
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _source() -> dict:
    return next(s for s in MANIFEST["sources"] if s["id"] == "hf-goedel-pset-v1")


class ManifestPin(unittest.TestCase):
    def test_revision_and_four_parquets_pinned(self) -> None:
        src = _source()
        self.assertRegex(src["hf_revision"], r"^[0-9a-f]{40}$")
        self.assertIn("MIT", src["license"])
        self.assertEqual(len(src["files"]), 4)
        total = 0
        for f in src["files"]:
            self.assertTrue(_HEX64.match(f["sha256"]))
            self.assertIsInstance(f["row_count"], int)
            total += f["row_count"]
        self.assertEqual(total, 1732594)


class SelfCheckingAudit(unittest.TestCase):
    def test_audit_counts_are_zero(self) -> None:
        a = COVERAGE["audit"]
        self.assertEqual(a["covered_foreign_glyph_count"], 0,
                         "a covered statement carries a non-whitelisted glyph — regression")
        self.assertEqual(a["covered_carrier_residual_count"], 0,
                         "a covered statement still uses integer division/monus — regression")

    def test_totals_are_internally_consistent(self) -> None:
        t = COVERAGE["totals"]
        self.assertEqual(t["rows"], t["parsed"] + t["unparsed"])
        full_untl = sum(COVERAGE["full_statement_untranslatable_reasons"].values())
        self.assertEqual(full_untl + t["full_statement"]["covered"], t["parsed"])
        self.assertGreaterEqual(t["goal_only"]["covered"], t["full_statement"]["covered"])
        # the pinned 1.73M source
        self.assertEqual(t["rows"], 1732594)

    def test_duplicate_stats_consistent(self) -> None:
        d = COVERAGE["duplicate_analysis"]
        self.assertEqual(
            d["unique_goals"] + d["duplicate_statements"], d["total_parsed"]
        )
        self.assertGreater(d["duplicate_statements"], 0)
        self.assertLessEqual(d["unique_covered_goals"], d["unique_goals"])


class NoHeadGlyphs(unittest.TestCase):
    """Regression for the false positives the 1.73M scale surfaced: operators and
    constructors with no corpus head that an ASCII-blind classifier accepted."""

    def _reason(self, goal, **flags):
        stmt = {
            "name": "t", "goal": goal, "value_vars": [], "hyps": [],
            "fn_unknown": False, "domain_vars": {}, **flags,
        }
        return gc.classify(stmt)["goal_reason"]

    def test_product_cross_and_smul_blocked(self) -> None:
        self.assertEqual(self._reason("A × B = C"), "vector_or_module_op")
        self.assertEqual(self._reason("(a - b) • (a + b) = 0"), "vector_or_module_op")

    def test_lattice_min_max_blocked(self) -> None:
        self.assertEqual(self._reason("(3 ⊓ 4 ⊓ 5) = 2"), "min_max")

    def test_imaginary_units_are_complex(self) -> None:
        for g in ("(3 - ℐ) * (2 - ℐ) = 5", "𝕀 * 𝕀 = -1"):
            self.assertEqual(self._reason(g), "complex_number")

    def test_aleph_cardinal_blocked(self) -> None:
        self.assertEqual(self._reason("ℵ₀ = ℵ₀"), "set_or_finset")

    def test_anonymous_constructor_blocked(self) -> None:
        self.assertEqual(self._reason("⟨a⟩ = b"), "tuple_or_structure")

    def test_cyrillic_and_script_l_are_variable_names(self) -> None:
        # visible identifiers now, so a real-carrier statement over them is covered
        self.assertTrue(
            gc.classify({
                "name": "t", "goal": "М + О = ℓ", "value_vars": ["М", "О", "ℓ"],
                "hyps": [], "fn_unknown": False, "domain_vars": {},
                "has_field_carrier": True,
            })["full_ok"]
        )

    def test_two_arg_log_blocked_one_arg_supported(self) -> None:
        # regression: arity-blindness accepted base-b `log b x` (Nat.log/Real.logb)
        for g in ("log 8 64 = 4", "log 2 (2^n) = n", "log 27 3 = 1/3"):
            self.assertEqual(self._reason(g), "two_arg_log_no_head", g)
        # one-argument log is still the supported Real.log head
        self.assertIsNone(self._reason("Real.log x > 0", value_vars=["x"], has_field_carrier=True))
        self.assertIsNone(self._reason("log x = 5", value_vars=["x"], has_field_carrier=True))

    def test_ordinary_inequality_still_covered(self) -> None:
        self.assertIsNone(
            gc.classify({
                "name": "t", "goal": "a^2 + b^2 ≥ 2 * a * b", "value_vars": ["a", "b"],
                "hyps": [], "fn_unknown": False, "domain_vars": {},
                "has_field_carrier": True,
            })["goal_reason"]
        )


class LetBindingGoals(unittest.TestCase):
    """v0.10 item 1 (cont.): `let x := e` goal bindings are definitional
    equalities, not a truncation point. 87% of the old no_relation_in_goal
    bucket (226,631 of 258,495 statements) was the parser stopping at the
    binding's `:=` and classifying the two-token stub `let x`."""

    def test_let_goal_parses_past_the_binding(self) -> None:
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n  let x : ℝ := 4\n  let y : ℝ := 3\n"
            "  x + y = 7 := by sorry",
        )
        self.assertEqual(st["goal"], "x + y = 7")
        self.assertEqual(st["goal_lets"], ["x = (4 : ℝ)", "y = (3 : ℝ)"])
        # a field-typed LET does not set the statement-wide field carrier
        # (segment-local signal only — the review-caught shielding fix)
        self.assertFalse(st["has_field_carrier"])
        self.assertTrue(gc.classify(st)["full_ok"])

    def test_let_with_tuple_rhs_is_blocked_not_covered(self) -> None:
        # the binding is part of the goal: an uncarried constructor in the RHS
        # blocks the whole statement with the constructor's own label
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n  let v : ℝ × ℝ := (1, 2)\n  v.1 = 1 := by sorry",
        )
        r = gc.classify(st)
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "tuple_or_structure")

    def test_untyped_numeral_let_keeps_the_nat_carrier(self) -> None:
        # `let n := 10` elaborates at ℕ, so `/` over it is still Nat.div: the
        # carrier gap must survive the desugaring (carrier-honesty at let scope)
        st = gc.parse_lean4_theorem(
            "t", "theorem t :\n  let n := 10\n  n / 4 = 2 := by sorry"
        )
        self.assertTrue(st["has_nat_carrier"])
        r = gc.classify(st)
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_let_body_keeps_its_own_blocker_label(self) -> None:
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n  let p := 4\n  ∀ k : ℝ, k * p = 4 * k := by sorry",
        )
        r = gc.classify(st)
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "universal_quantifier")

    def test_proof_terminator_not_confused_by_proof_side_let(self) -> None:
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t (x : ℝ) (h : x = 1) : x + 1 = 2 := by\n"
            "  let y := 3\n  linarith",
        )
        self.assertEqual(st["goal"], "x + 1 = 2")
        self.assertNotIn("goal_lets", st)


class PredicateHeads(unittest.TestCase):
    """v0.10 item 1 (cont.): the relational/predicate heads, chosen by measured
    frequency inside the no_relation_in_goal bucket. A supported predicate over
    an unsupported inner term is NOT covered; arity is enforced; predicates the
    corpus does not carry keep precise gap labels."""

    def _mk(self, goal, vars=(), hyps=(), fn=False, **flags):
        return {
            "name": "t", "goal": goal, "value_vars": list(vars),
            "hyps": list(hyps), "fn_unknown": fn, "domain_vars": {}, **flags,
        }

    def test_bare_parity_and_primality_goals_covered(self) -> None:
        for goal in ("Even (n ^ 2 + n)", "Odd (2*n + 1)", "Nat.Prime 17"):
            r = gc.classify(self._mk(goal, vars=("n",), has_nat_carrier=True))
            self.assertTrue(r["full_ok"], goal)

    def test_negated_predicate_goal_covered(self) -> None:
        # NEG is a corpus head (logic); data/number_theory defines ODD through it
        r = gc.classify(self._mk("¬ Nat.Prime 100"))
        self.assertTrue(r["full_ok"])

    def test_irrational_over_supported_inner_covered(self) -> None:
        r = gc.classify(self._mk("Irrational (Real.sqrt 3)"))
        self.assertTrue(r["full_ok"])

    def test_predicate_composition_covered(self) -> None:
        # MEET/JOIN/IMPLIES are corpus heads, so compositions of predicate atoms
        # are proposition-shaped
        r = gc.classify(self._mk("Even n → Odd (n + 1)", vars=("n",), has_nat_carrier=True))
        self.assertTrue(r["full_ok"])

    def test_false_goal_is_the_contradiction_node(self) -> None:
        # FALSITY is carried by data/logic; the hypotheses must still reduce
        r = gc.classify(self._mk("False", vars=("n",), hyps=("n = 1", "n = 2"),
                                 has_nat_carrier=True))
        self.assertTrue(r["full_ok"])
        r2 = gc.classify(self._mk("False", vars=("n",), hyps=("abs n = 1",),
                                  has_nat_carrier=True))
        self.assertFalse(r2["full_ok"])

    def test_predicate_over_unsupported_inner_not_covered(self) -> None:
        r = gc.classify(self._mk("Even (Finset.card S)"))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "set_or_finset")

    def test_predicate_arity_enforced(self) -> None:
        r = gc.classify(self._mk("Even n m", vars=("n", "m"), has_nat_carrier=True))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "predicate_extra_arg")

    def test_unapplied_predicate_is_not_a_proposition(self) -> None:
        r = gc.classify(self._mk("Even"))
        self.assertFalse(r["goal_ok"])

    def test_coprime_keeps_a_precise_gap_label(self) -> None:
        # coprimality (2-ary) has no corpus head; it must not vanish into
        # no_relation_in_goal now that primality is supported
        r = gc.classify(self._mk("Nat.Coprime 4 9"))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "coprime_no_head")

    def test_uncarried_predicates_stay_gaps(self) -> None:
        r = gc.classify(self._mk("Function.Injective f", fn=True))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "no_relation_in_goal")
        r2 = gc.classify(self._mk("IsEven 4"))
        self.assertFalse(r2["goal_ok"])

    def test_integer_predicate_over_field_carrier_blocked(self) -> None:
        # over ℝ mathlib's `Even x` is trivially true for every real — that is
        # not the integer parity head the corpus carries
        r = gc.classify(self._mk("Even x", vars=("x",), has_field_carrier=True))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "integer_predicate_field_carrier")

    def test_integer_predicate_over_coerced_or_ascribed_arg_blocked(self) -> None:
        # the argument-level hole (review follow-up): a coercion/ascription in
        # the ARGUMENT is the field reading even with no field binder in sight
        for goal in ("Even ↑n", "Odd (x : ℝ)"):
            r = gc.classify(self._mk(goal, vars=("n", "x"), has_nat_carrier=True))
            self.assertFalse(r["goal_ok"], goal)
            self.assertEqual(r["goal_reason"], "integer_predicate_field_carrier", goal)
        # the plain integer application stays covered
        r2 = gc.classify(self._mk("Even (n + 1)", vars=("n",), has_nat_carrier=True))
        self.assertTrue(r2["full_ok"])


class CarrierSignalLocality(unittest.TestCase):
    """Review-caught over-count (v0.10 item 1 cont. adversarial review): the
    field signal computed over the WHOLE statement let a `: ℚ` ascription in
    one segment legitimize ℕ floor-division/monus in a sibling segment. 6,066
    covered Goedel-Pset rows fell to this under the uniform segment-local fix
    (1,146 already inside the old baseline via goal↔hyp shielding; the
    review's own laxer segment notion had estimated 3,644). The signal is now
    segment-local; these two tests are distilled from the review's evidence
    rows."""

    def test_monus_in_nat_let_not_shielded_by_rat_cast_in_body(self) -> None:
        # Goedel-Pset-413727: the goal body carries `(w : ℚ)`, but the monus
        # `a + b - 1` lives inside an ℕ-typed binding with no local signal.
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n"
            "  let a : ℕ := 5\n"
            "  let b : ℕ := 3\n"
            "  let w : ℕ := a * (a + b - 1)\n"
            "  (w : ℚ) / a = 3/7 := by sorry",
        )
        r = gc.classify(st)
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "nat_monus_no_head")

    def test_nat_div_in_nat_let_not_shielded_by_rat_typed_sibling(self) -> None:
        # Goedel-Pset-1082706: `s / n` over ℕ is 0 (the stated claim is
        # arithmetically false in Lean); the ℚ-typed sibling binding must not
        # shield it.
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t (n g s : ℕ) (h1 : n = 125) (h2 : g = 50) (h3 : s = 25) :\n"
            "  let r : ℚ := s / n\n"
            "  let b : ℕ := (n - g) * (s / n)\n"
            "  b = 15 ∧ r = 1/5 := by sorry",
        )
        r = gc.classify(st)
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_local_signal_still_legitimizes_its_own_segment(self) -> None:
        # the control: division-free ℕ bindings plus a ℚ-cast body divide fine
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n"
            "  let a : ℕ := 5\n"
            "  let w : ℕ := a + 2\n"
            "  (w : ℚ) / a = 7/5 := by sorry",
        )
        r = gc.classify(st)
        self.assertTrue(r["full_ok"], r)

    def test_hyp_signal_does_not_shield_goal_monus(self) -> None:
        # the pre-existing (pre-slice) exposure: goal↔hyp shielding
        r = gc.classify({
            "name": "t", "goal": "a - b = 2", "value_vars": ["a", "b", "x"],
            "hyps": ["x = (3 : ℚ) / 4"], "fn_unknown": False, "domain_vars": {},
            "has_nat_carrier": True,
        })
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "nat_monus_no_head")

    def test_carrier_residual_audit_sees_cross_segment_shielding(self) -> None:
        # The audit itself was blind by construction (it regexed the same
        # concatenated text), so it could never flag the class it guards.
        # Per-segment, the 1082706 shape IS a residual if it were ever covered.
        import ingest_goedel_pset as igp
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t (n g s : ℕ) :\n"
            "  let r : ℚ := s / n\n"
            "  let b : ℕ := (n - g) * (s / n)\n"
            "  b = 15 := by sorry",
        )
        self.assertTrue(igp._carrier_residual(st))
        # ... and the ℚ-local division alone is NOT a residual
        st2 = gc.parse_lean4_theorem(
            "t",
            "theorem t (n s : ℕ) :\n"
            "  let r : ℚ := s / n\n"
            "  n + s = 150 := by sorry",
        )
        self.assertFalse(igp._carrier_residual(st2))


if __name__ == "__main__":
    unittest.main()
