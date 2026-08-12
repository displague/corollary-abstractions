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

    def test_let_body_with_quantifier_prefix_now_covers(self) -> None:
        # Pre-quantifier-slice this was the `universal_quantifier` gap; the
        # let binding still desugars to its definitional equation and the
        # ∀-prefixed body now reduces under the FORALL head.
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n  let p := 4\n  ∀ k : ℝ, k * p = 4 * k := by sorry",
        )
        r = gc.classify(st)
        self.assertTrue(r["goal_ok"], r["goal_reason"])
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_quantified_let_rhs_stays_a_gap(self) -> None:
        # A quantifier inside a let-binding EQUATION is a Prop-valued binding,
        # not a prefix on the goal proposition: precisely labeled, not covered.
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n  let P := ∀ k : ℕ, k ≥ 0\n  1 = 1 := by sorry",
        )
        r = gc.classify(st)
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "quantifier_embedded")

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


class QuantifierHeads(unittest.TestCase):
    """v0.10: the FORALL/EXISTS binder heads. A quantifier PREFIX over a
    numeric domain is extracted before every other check; everything else
    keeps a precise label. Carrier honesty is segment-local in BOTH
    directions, untyped binders take Lean's ℕ default, shadowing is refused,
    and the two audit rows the 1.73M run surfaced are pinned here."""

    def _mk(self, goal, vars=(), hyps=(), fn=False, **flags):
        return {
            "name": "t", "goal": goal, "value_vars": list(vars),
            "hyps": list(hyps), "fn_unknown": fn, "domain_vars": {}, **flags,
        }

    # ---- supported prefix shapes ------------------------------------------
    def test_typed_prefix_chains_cover(self) -> None:
        for goal in (
            "∀ x : ℝ, x^2 ≥ 0",
            "∃ x : ℝ, x^2 = 2 ∧ x > 0",
            "∀ x y : ℝ, x * y = y * x",
            "∀ x : ℝ, ∀ y : ℝ, x + y = y + x",
            "∀ (x : ℝ) (hx : x > 0), x^2 > 0",
            "∀ ⦃a b : ℕ⦄, a + b = b + a",
            "∀ x : ℕ, Even (2 * x)",
        ):
            r = gc.classify(self._mk(goal))
            self.assertTrue(r["full_ok"], (goal, r["full_reason"]))

    def test_bounded_binder_desugars_like_lean(self) -> None:
        # ∀ x > 0, P  ==  ∀ x, x > 0 → P; the bound is a checked conjunct
        r = gc.classify(self._mk("∀ ε > 0, ∃ δ > 0, δ < ε"))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_untyped_binder_defaults_to_nat_carrier(self) -> None:
        # Lean's elaboration defaults the binder to ℕ absent a field signal:
        # `1/x` IS Nat.div as formalized, and the claim stays a carrier gap.
        r = gc.classify(self._mk("∀ x > 0, x + 1/x ≥ 2"))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")
        # a segment-local field signal lifts the default
        r = gc.classify(self._mk("∀ x > (0 : ℝ), x / 2 < x"))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_negation_wrapped_chain_is_neg_composition(self) -> None:
        # NEG∘EXISTS is exactly what the quantifier De Morgan nodes state.
        r = gc.classify(self._mk("¬ (∃ k : ℕ, n = 2 * k)", vars=("n",),
                                 has_nat_carrier=True))
        self.assertTrue(r["full_ok"], r["full_reason"])
        # ... and the honest refusal inside: monus over ℕ stays a gap
        r = gc.classify(self._mk("¬∃ x y : ℕ, 7^x - 3^y = 4"))
        self.assertEqual(r["goal_reason"], "nat_monus_no_head")

    def test_exists_unique_rides_the_expansion(self) -> None:
        # ∃! desugars to its ExistsUnique expansion (carried heads only),
        # grounded by logic.quantification.unique_existence_expansion.
        r = gc.classify(self._mk("∃! x : ℝ, 2*x = 6"))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_quantified_hypothesis_unblocks_full_statement(self) -> None:
        r = gc.classify(self._mk("x = 3", vars=("x", "n"),
                                 hyps=["∃ k : ℕ, n = 2 * k"],
                                 has_nat_carrier=True))
        self.assertTrue(r["full_ok"], r["full_reason"])

    # ---- carrier honesty, segment-local in BOTH directions ----------------
    def test_goal_field_binder_does_not_shield_hyp_nat_division(self) -> None:
        r = gc.classify(self._mk("a / 2 = 3", vars=("a",),
                                 hyps=["∃ x : ℝ, x = 1"],
                                 has_nat_carrier=True))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_hyp_nat_binder_does_not_gap_the_goal(self) -> None:
        r = gc.classify(self._mk("a = 3", vars=("a",),
                                 hyps=["∀ n : ℕ, n ≥ 0"]))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_quantifier_nat_binder_gaps_its_own_segment(self) -> None:
        r = gc.classify(self._mk("∀ n : ℕ, n - 1 ≤ n"))
        self.assertEqual(r["goal_reason"], "nat_monus_no_head")
        r = gc.classify(self._mk("∀ n : ℤ, n - 1 ≤ n"))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_shadowed_binder_refused_precisely(self) -> None:
        # per-statement carrier flags cannot express two carriers for one
        # name, so re-binding an outer variable is refused, not guessed at.
        r = gc.classify(self._mk("∀ y : ℝ, y ≥ 0", vars=("y",)))
        self.assertEqual(r["goal_reason"], "quantifier_shadowed_binder")

    # ---- precise labels for what stays out of reach -----------------------
    def test_unreachable_shapes_keep_precise_labels(self) -> None:
        # (the two connective-position rows that sat here before the
        # embedded-quantifier slice now cover via the atom-tree walk and are
        # asserted positive in GoedelPsetEmbeddedQuantifierWalk; TERM-position
        # quantifiers are what genuinely stays out)
        for goal, label in (
            ("(∃ x : ℝ, x = 1) = False", "quantifier_embedded"),
            ("IsLeast {n : ℕ | ∀ w : ℝ, w ≥ 0} 4", "quantifier_embedded"),
            ("∀ f : ℝ → ℝ, f 0 = 0", "quantifier_function_binder"),
            ("∃ q : ℕ → (ℝ × ℝ), q = q", "quantifier_function_binder"),
            ("∀ S : Finset ℕ, S.card ≥ 0", "set_or_finset"),
            ("∀ x ∈ Finset.range 5, x < 5", "set_or_finset"),
            ("∀ x ∈ Set.Icc (-3 : ℝ) (-1), x ≤ 0", "set_or_finset"),
            ("∃ B ⊆ A, B = B", "set_or_finset"),
            ("∀ z : ℂ, z = z", "complex_number"),
            ("∀ p : Prop, p ∨ ¬p", "quantifier_over_sort"),
            ("∃ p : ℕ × ℕ, p = p", "vector_or_module_op"),
            ("∃ x : ℝ,", "quantifier_malformed"),
        ):
            r = gc.classify(self._mk(goal, vars=("A",)))
            self.assertEqual(r["goal_reason"], label, goal)

    def test_quantified_let_rhs_is_embedded(self) -> None:
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n  let P := ∀ k : ℕ, k ≥ 0\n  1 = 1 := by sorry",
        )
        self.assertEqual(gc.classify(st)["goal_reason"], "quantifier_embedded")

    # ---- the two audit rows the 1.73M run surfaced ------------------------
    def test_star_operator_is_uninterpreted_notation(self) -> None:
        # Goedel-Pset-91093: `2 ★ (2 ★ x)` — the ★ glyph is invisible to the
        # identifier scan, the same class as `⋆` and the section dot.
        r = gc.classify(self._mk("∃! x : ℚ, (2 ★ (2 ★ x)) = (1 ★ x) ∧ x = 21/20"))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "uninterpreted_notation")

    def test_carrier_audit_sees_quantifier_field_binder(self) -> None:
        # Goedel-Pset-1326754-class, distilled to the PURE-field chain: the
        # segment's own binder declares the field carrier, so the audit must
        # not flag the cover ...
        import ingest_goedel_pset as igp
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t : ∃ (last : Rat), last = 1 /. 2 := by sorry",
        )
        r = gc.classify(st)
        self.assertTrue(r["full_ok"], r["full_reason"])
        self.assertFalse(igp._carrier_residual(st))
        # ... while a ℕ-quantified division would still be one if it were
        # ever covered (the audit stays able to see the class it guards).
        st2 = gc.parse_lean4_theorem(
            "t",
            "theorem t (n : ℕ) :\n  ∃ k : ℕ, k = n / 2 := by sorry",
        )
        self.assertTrue(igp._carrier_residual(st2))

    # ---- the mixed-carrier chain shield (adversarial-review catch) --------
    def test_mixed_carrier_chain_does_not_shield(self) -> None:
        """Review-caught over-count: the chain-level field flag is one
        boolean, so `∀ (d : ℚ) (n : ℕ), …` shielded a sibling ℕ binder's
        Nat.div/monus in conjuncts that never touch d. Under carrier mixing
        the field flag is demoted and the integer reading's gap wins —
        distilled from the review's evidence rows."""
        # 216780-class: `(n - 2) * 180` is ℕ monus regardless of the ℚ sibling
        r = gc.classify(self._mk("∀ (d : ℚ) (n : ℕ), (n - 2) * 180 = 360 ∧ d = 1"))
        self.assertEqual(r["goal_reason"], "nat_monus_no_head")
        # 846154-class: `4 / m` with m : ℕ is Nat.div — value-breaking cover
        r = gc.classify(self._mk("∃ (a : ℚ) (m : ℕ), 4 / m = 2 ∧ a = 1"))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")
        # 1684555-class: a vacuous quantifier-ℝ binder over statement-ℤ division
        r = gc.classify(self._mk("∀ a : ℝ, k / 2 = 1", vars=("k",),
                                 has_int_carrier=True))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")
        # 968965-class: quantifier-ℝ binder must not shield statement-ℕ 1/n
        r = gc.classify(self._mk("∀ x : ℝ, 1 / n ≤ x ∨ x < 0", vars=("n",),
                                 has_nat_carrier=True))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")
        # ... and the same rule holds in hypothesis position
        r = gc.classify(self._mk("a = 1", vars=("a",),
                                 hyps=["∀ (d : ℚ) (n : ℕ), n / 2 = 1 ∧ d = 2"]))
        self.assertEqual(r["full_reason"], "hyp:integer_division_no_head")

    def test_mixed_carrier_controls(self) -> None:
        # pure-field chains keep dividing
        r = gc.classify(self._mk("∀ (x y : ℝ), x / 2 + y / 2 = 1"))
        self.assertTrue(r["full_ok"], r["full_reason"])
        # an in-segment textual signal (coercion arrow) still legitimizes,
        # exactly as everywhere else
        r = gc.classify(self._mk("∀ (d : ℚ) (n : ℕ), ↑n / 2 = d"))
        self.assertTrue(r["full_ok"], r["full_reason"])
        # the ∀ (n : ℕ)-only variant refused correctly BEFORE the fix: control
        r = gc.classify(self._mk("∀ (n : ℕ), n / 2 = 1"))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")
        # int+field mix with `-` only: subtraction is a real head over ℤ
        r = gc.classify(self._mk("∀ (d : ℚ) (k : ℤ), k - 1 ≤ k ∧ d = 2"))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_carrier_audit_sees_mixed_chain_shield(self) -> None:
        # The audit's `continue` used to fire on the same one-boolean signal
        # as the classifier's shield — structurally blind to this class. Now
        # a mixed chain gets no excuse and the shape reads as a residual.
        import ingest_goedel_pset as igp
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t : ∀ (d : ℚ) (n : ℕ), n / 2 = 1 ∧ d = 2 := by sorry",
        )
        self.assertTrue(igp._carrier_residual(st))
        # control: the pure-field chain stays excused
        st2 = gc.parse_lean4_theorem(
            "t",
            "theorem t : ∀ (d : ℚ), d / 2 = 1 := by sorry",
        )
        self.assertFalse(igp._carrier_residual(st2))

    def test_audit_normalizer_keeps_factorial_and_set_braces_foreign(self) -> None:
        import ingest_goedel_pset as igp
        # ∃! and binder braces normalize; a bare factorial `!` and set-builder
        # braces (with `|`) must still read as foreign glyphs.
        self.assertFalse(set(igp._audit_normalize("∃! x : ℚ, x = 1")) - igp._ALLOWED)
        self.assertFalse(set(igp._audit_normalize("∀ ⦃a b : ℕ⦄, a = b")) - igp._ALLOWED)
        self.assertFalse(set(igp._audit_normalize("∀ {a : ℕ}, a = a")) - igp._ALLOWED)
        self.assertTrue(set(igp._audit_normalize("n ! = 6")) - igp._ALLOWED)
        self.assertTrue(
            set(igp._audit_normalize("∀ x ∈ {y : ℕ | y > 0}, x > 0")) - igp._ALLOWED)

    def test_audit_normalizer_reaches_every_binder_group(self) -> None:
        import ingest_goedel_pset as igp
        # Goedel-Pset-251446 (embedded-quantifier slice audit catch): the
        # SECOND consecutive implicit-binder group must normalize too...
        self.assertFalse(
            set(igp._audit_normalize(
                "(¬(∀ {α : ℝ} {n : ℕ} (h : 0 < α ∧ 0 < n), ∃ x, x = α * n))"
                " ∧ (∀ {α : ℝ} {n : ℕ} (h : 0 < α ∧ 0 < n), ∃ x, x = α * n)"
            )) - igp._ALLOWED)
        # ...but a brace past the binder section's comma is NOT binder
        # position and stays foreign, as does a set-builder in the section.
        self.assertTrue(
            set(igp._audit_normalize("∀ x : ℕ, x ∈ ({1} : Set ℕ)")) - igp._ALLOWED)
        self.assertTrue(
            set(igp._audit_normalize("∀ {x : ℕ} (h : x ∈ {y | y > 0}), x > 0"))
            - igp._ALLOWED)
        # reviewer's control: the widened pattern must not cross a membership
        # glyph into set-literal braces (their inner comma would even pass
        # the inner class — the ∈ exclusion is what stops it).
        self.assertTrue(
            set(igp._audit_normalize("∀ x ∈ ({1, 2} : Set ℕ), x > 0"))
            - igp._ALLOWED)


class GoedelPsetEmbeddedQuantifierWalk(unittest.TestCase):
    """v0.10 embedded quantifiers: the atom-tree walk. A goal-body or
    hypothesis segment whose flat verdict would be `quantifier_embedded` is
    re-judged as a connective tree; every leaf faces the existing machinery.
    Scope hygiene per the registered design: binders per subformula, shadow
    refusal on scope overlap, sibling scopes alpha-independent, carriers
    leaf-local, term/let positions and past-cap nests refused precisely."""

    def _mk(self, goal, vars=(), hyps=(), fn=False, **flags):
        return {
            "name": "t", "goal": goal, "value_vars": list(vars),
            "hyps": list(hyps), "fn_unknown": fn, "domain_vars": {}, **flags,
        }

    # ---- shapes the walk reaches ------------------------------------------
    def test_embedded_shapes_cover(self) -> None:
        for goal in (
            # the two rows test_unreachable_shapes asserted embedded pre-slice:
            "(∀ x : ℝ, x = x) ∧ (∃ y : ℝ, y = 2)",
            "∀ x : ℝ, (∃ y : ℝ, y > x) → x < x + 1",
            # iff-of-existence (the top Goedel ↔ shape)
            "(∃ x : ℝ, x^2 + 2 * x + 1 = 0) ↔ 1 ≤ 1",
            # claim ∧ witness (the top Goedel ∧ shape)
            "1 + 1 = 2 ∧ ∃ y : ℝ, y^2 = 4",
            # disjunction of existentials, SIBLING scopes reusing a name —
            # alpha-independent, each occurrence inside exactly one binder
            "(∃ k : ℤ, 6 = 2 * k) ∨ (∃ k : ℤ, 6 = 2 * k + 1)",
            # NEG over IFF over two existentials (miniF2F
            # numbertheory_notequiv2i2jasqbsqdiv8's shape)
            "¬((∃ i : ℤ, 4 = 2 * i) ↔ (∃ k : ℤ, 16 = 8 * k))",
            # ∃! in connective position rides its expansion
            "(∃! x : ℝ, x = 1) ∨ 1 = 2",
            # quantifier under quantifier under connective
            "∃ m : ℕ, (m > 3 ∧ ∃ p : ℕ, m * p ≤ m + p)",
            # ¬-wrapped universal against its existential dual (De Morgan)
            "¬(∀ x : ℝ, x^2 + 1 > 0) ↔ ∃ x : ℝ, x^2 + 1 ≤ 0",
        ):
            r = gc.classify(self._mk(goal))
            self.assertTrue(r["full_ok"], (goal, r["full_reason"]))

    def test_embedded_hypothesis_unblocks_full_statement(self) -> None:
        r = gc.classify(self._mk(
            "c = 4", vars=("c",), has_field_carrier=True,
            hyps=("c > 0", "∃ x : ℝ, x = c ∧ ∀ y : ℝ, y^2 ≥ 0"),
        ))
        self.assertTrue(r["full_ok"], r["full_reason"])

    # ---- scope hygiene: shadowing refused on OVERLAP only ------------------
    def test_enclosing_binder_shadow_refused(self) -> None:
        r = gc.classify(self._mk("∀ x : ℝ, (∃ x : ℝ, x = 1) ∧ x > 0"))
        self.assertEqual(r["goal_reason"], "quantifier_shadowed_binder")

    def test_statement_binder_shadow_refused(self) -> None:
        r = gc.classify(self._mk(
            "(∃ n : ℕ, n = 1) ∧ n = 2", vars=("n",), has_nat_carrier=True))
        self.assertEqual(r["goal_reason"], "quantifier_shadowed_binder")

    # ---- carrier honesty, leaf-local ---------------------------------------
    def test_field_binder_leaf_does_not_shield_sibling_nat_division(self) -> None:
        # the mixed-carrier chain shield, one level down: a ℚ-quantified leaf
        # must not legitimize Nat.div in its SIBLING conjunct
        r = gc.classify(self._mk(
            "(∀ d : ℚ, d = d) ∧ n / 3 = 4", vars=("n",), has_nat_carrier=True))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_field_binder_leaf_does_not_shield_sibling_monus(self) -> None:
        r = gc.classify(self._mk(
            "(∀ x : ℝ, x^2 ≥ 0) ∧ n - 2 = 1", vars=("n",), has_nat_carrier=True))
        self.assertEqual(r["goal_reason"], "nat_monus_no_head")

    def test_untyped_embedded_binder_keeps_nat_default(self) -> None:
        # untyped ∃ in connective position defaults to ℕ exactly like a
        # prefix binder: its body's `/` stays Nat.div
        r = gc.classify(self._mk("(∃ x, x / 2 = 3) ∧ 1 = 1"))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_pure_field_embedded_leaf_still_divides(self) -> None:
        r = gc.classify(self._mk("(∃ x : ℝ, x / 2 = 3) ∧ 1 = 1"))
        self.assertTrue(r["full_ok"], r["full_reason"])

    # ---- precise refusals through the tree ---------------------------------
    def test_inner_leaf_defects_get_their_own_labels(self) -> None:
        for goal, label in (
            ("(∀ f : ℝ → ℝ, f 0 = 0) ∧ 1 = 1", "quantifier_function_binder"),
            ("(∀ p : Prop, p ∨ ¬p) ∧ 1 = 1", "quantifier_over_sort"),
            ("(∃ x : ℕ, f x = 1) ∧ 1 = 1", "unsupported_symbol:f"),
            ("(∃ x : ℝ, |x| = 1) ∧ 1 = 1", "absolute_value"),
        ):
            r = gc.classify(self._mk(goal))
            self.assertEqual(r["goal_reason"], label, goal)

    def test_term_position_quantifier_stays_embedded(self) -> None:
        for goal in (
            "(∃ x : ℝ, x = 1) = False",       # Prop-valued equality operand
            "IsLeast {n : ℕ | ∀ w : ℝ, w ≥ 0} 4",  # set-builder body
        ):
            r = gc.classify(self._mk(goal))
            self.assertEqual(r["goal_reason"], "quantifier_embedded", goal)

    def test_depth_cap_refuses_conservatively(self) -> None:
        goal = "(" * 45 + "∃ x : ℕ, x = 1" + ")" * 45 + " ∧ 1 = 1"
        r = gc.classify(self._mk(goal))
        self.assertEqual(r["goal_reason"], "quantifier_embedded")

    # ---- the nested-shield review fix (fifth cycle): atom contact ----------
    def test_nested_and_single_chain_agree(self) -> None:
        # The review's probe pair: an inherited field flag must not survive
        # into a descendant ℕ leaf — the nested spelling and the single
        # mixed chain must give the SAME verdict.
        nested = gc.classify(self._mk("∀ x : ℝ, x = x ∧ ∀ n : ℕ, n / 2 * 2 = n"))
        single = gc.classify(self._mk("∀ (x : ℝ) (n : ℕ), x = x ∧ n / 2 * 2 = n"))
        self.assertEqual(nested["goal_reason"], "integer_division_no_head")
        self.assertEqual(nested["goal_reason"], single["goal_reason"])

    def test_field_prefix_does_not_shield_nested_nat_division(self) -> None:
        # Goedel-Pset-704685's shape: `∃ l : ℝ, … ∧ ∀ a > 0, a + 4/a ≥ 4` —
        # the inner a is ℕ by the untyped-binder rule and l never touches
        # its atom, so 4/a is Nat.div and the row must refuse.
        r = gc.classify(self._mk("∃ l : ℝ, l = 4 ∧ ∀ a > 0, a + 4 / a ≥ 4"))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_unused_field_binder_does_not_shield(self) -> None:
        # Goedel-Pset-1586260's shape: a vacuous `m : ℝ` binder must not
        # shield a ℕ-defaulted ∃-leaf's division anywhere in its body.
        r = gc.classify(self._mk("∃ m : ℝ, m = m ∧ ∃ x, 4 / x = 2"))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_field_contact_in_the_atom_still_covers(self) -> None:
        # Positive control (the reviewer's adjudicated-honest class): the
        # field var SHARES the atom, so Lean elaborates the division in ℝ.
        r = gc.classify(self._mk("∃ l : ℝ, 1 = 1 ∧ ∀ a : ℕ, l ≥ 4 / a"))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_unused_statement_field_binder_does_not_shield(self) -> None:
        # Goedel-Pset-1586260 verbatim shape: the unused STATEMENT binder
        # `(m : ℝ)` must not shield the ℕ-defaulted ∃-leaves' `4 / x`. The
        # statement is pure-field, so its value vars shield by NAME — and m
        # touches no atom.
        r = gc.classify(self._mk(
            "(∃ x y, (y = 4 / x ∧ x = 2 ∧ y = 2)) ∧ (∃ x y, (y = 4 / x ∧ x = 2 ∧ y = 0))",
            vars=("m",), hyps=("m ≠ 0",), has_field_carrier=True))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_statement_field_contact_still_covers(self) -> None:
        # ...while the same pure-field statement DOES shield an atom its
        # field var actually touches (x : ℝ forces the ℝ reading of q / 3).
        r = gc.classify(self._mk(
            "x > 0 ∧ ∃ q : ℤ, x = q / 3", vars=("x",), has_field_carrier=True))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_mixed_statement_keeps_the_disclosed_blanket(self) -> None:
        # A MIXED statement (ℝ and ℤ binders) has no per-name types in the
        # extracts; the walk keeps the flat path's disclosed blanket
        # (Goedel-Pset-359's adjudicated-honest shape).
        r = gc.classify(self._mk(
            "a = a ↔ ∃ f g : ℤ, x = f / g", vars=("x", "a"),
            has_field_carrier=True, has_int_carrier=True))
        self.assertTrue(r["full_ok"], r["full_reason"])

    def test_quantified_let_rhs_still_refused(self) -> None:
        # the walk is gated to goal bodies and hypotheses; a quantified
        # let-RHS is a Prop-valued binding and keeps the embedded label
        st = gc.parse_lean4_theorem(
            "t",
            "theorem t :\n  let P := (∀ k : ℕ, k ≥ 0) ∧ 1 = 1\n  2 = 2 := by sorry",
        )
        self.assertEqual(gc.classify(st)["goal_reason"], "quantifier_embedded")


if __name__ == "__main__":
    unittest.main()
