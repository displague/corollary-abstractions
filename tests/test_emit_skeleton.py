"""Skeleton emitter (docs/DESIGN-skeleton-emitter.md), registered before the seed.

P-E1: TOKEN_RE accepts standalone < > and still prefers <= >=.
P-E2 samples: each census bucket's first examples emit and parse.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from emit_skeleton import (  # noqa: E402
    emit_expr,
    emit_or_reason,
    emit_statement,
    template_parses,
)
from match_signatures import Parser, tokenize  # noqa: E402


class TokenReStandaloneInequalities(unittest.TestCase):
    def test_lt_gt_tokenize(self) -> None:
        self.assertEqual(tokenize("a < b"), ["a", "<", "b"])
        self.assertEqual(tokenize("a > b"), ["a", ">", "b"])

    def test_le_ge_still_win(self) -> None:
        self.assertEqual(tokenize("a <= b"), ["a", "<=", "b"])
        self.assertEqual(tokenize("a >= b"), ["a", ">=", "b"])

    def test_lt_eq_does_not_steal_le(self) -> None:
        tree = Parser(tokenize("a <= b")).parse()
        self.assertEqual(tree[0], "rel")
        self.assertEqual(tree[1], "<=")


class EmitSamples(unittest.TestCase):
    def _ok(self, text: str, contains: str | None = None) -> str:
        tmpl = emit_expr(text)
        self.assertTrue(template_parses(tmpl), tmpl)
        if contains:
            self.assertIn(contains, tmpl)
        return tmpl

    def test_field_inequality(self) -> None:
        t = self._ok("x ^ 2 + x + y ^ 2 + y + 1 ≥ x * y", ">=")
        self.assertIn("x ^ 2", t)

    def test_hyps_become_implies_meet(self) -> None:
        tmpl = emit_statement({
            "goal": "a * b <= 1 / 4",
            "hyps": ["0 < a ∧ 0 < b"],
        })
        self.assertTrue(template_parses(tmpl), tmpl)
        self.assertTrue(tmpl.startswith("IMPLIES("), tmpl)
        self.assertIn("MEET(", tmpl)
        self.assertIn("<", tmpl)

    def test_sqrt_juxtaposition(self) -> None:
        t = self._ok("Real.sqrt a + Real.sqrt b ≥ a * b", "SQRT(")
        self.assertIn("SQRT(a)", t)
        self.assertIn("SQRT(b)", t)

    def test_trig_juxtaposition_and_parens(self) -> None:
        t = self._ok("cos (x - y) = cos x * cos y + sin x * sin y", "COS(")
        self.assertIn("SIN(x)", t)
        self.assertIn("COS(y)", t)

    def test_quantifier_prefix(self) -> None:
        t = self._ok("∀ x y : ℝ, x + y ≥ y + x", "FORALL(")
        self.assertIn("FORALL(x,", t)
        self.assertIn("FORALL(y,", t)

    def test_exists_negated(self) -> None:
        t = self._ok("¬ ∃ x : ℝ, x^4 + x^3 - x + 1 = 0", "NEG(")
        self.assertIn("EXISTS(x,", t)

    def test_predicate(self) -> None:
        t = self._ok("Even (a + c)", "EVEN(")
        self.assertIn("EVEN(a + c)", t)

    def test_greek_romanized(self) -> None:
        t = self._ok("(2 * α ^ 2 + 2 * α * β + β ^ 2) * x ≥ 0")
        self.assertIn("alpha", t)
        self.assertIn("beta", t)
        self.assertNotRegex(t, r"[αβ]")

    def test_ne_is_neg_of_eq(self) -> None:
        t = self._ok("a ≠ 0", "NEG(")
        self.assertIn("a = 0", t)

    def test_iff_is_meet_of_implies(self) -> None:
        t = self._ok("a = b ↔ b = a", "MEET(")
        self.assertIn("IMPLIES(", t)

    def test_sqrt_paren_expr(self) -> None:
        self._ok("√(a + b) ≥ 0", "SQRT(")


class EmitCensus(unittest.TestCase):
    def test_committed_census_matches_the_probed_cut(self) -> None:
        import json
        census = json.loads(
            (REPO / "experiments" / "lean_workbook_emit.json").read_text(
                encoding="utf-8")
        )
        self.assertEqual(census["emitted"], 12212)
        self.assertEqual(census["excluded"], 123)
        self.assertEqual(census["unique_covered_considered"], 12335)


class EmitOrReason(unittest.TestCase):
    def test_covered_inequality_emits(self) -> None:
        tmpl, reason = emit_or_reason({
            "name": "t",
            "goal": "a + b >= 2",
            "hyps": ["a ≥ 0", "b ≥ 0"],
            "value_vars": ["a", "b"],
        })
        self.assertIsNone(reason)
        self.assertIsNotNone(tmpl)
        self.assertTrue(template_parses(tmpl))


if __name__ == "__main__":
    unittest.main()
