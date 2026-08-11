"""Lean-workbook-proofs ingestion + the Lean-4 dialect handling of the shared
grammar classifier.

The 68% coverage number is a load-bearing v0.9 claim on a 29,750-row source, so
these tests guard the classifier's Lean-4 additions (Unicode identifiers,
capitalized/bare mathlib spellings) and the committed measurement's byte-for-byte
regeneration, and lock in the false-positive audit (zero foreign glyphs in the
covered set) the review demanded.
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
import ingest_lean_workbook as ing  # noqa: E402

MANIFEST = json.loads(
    (REPO_ROOT / "data_sources" / "manifest.json").read_text(encoding="utf-8")
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _source() -> dict:
    return next(
        s for s in MANIFEST["sources"] if s["id"] == "hf-goedel-lean-workbook-proofs"
    )


class ManifestPin(unittest.TestCase):
    def test_hf_revision_and_file_are_pinned(self) -> None:
        src = _source()
        self.assertRegex(src["hf_revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(src["access"], "hf-dataset")
        self.assertIn("MIT", src["license"])
        self.assertEqual(len(src["files"]), 1)
        f = src["files"][0]
        self.assertTrue(_HEX64.match(f["sha256"]))
        self.assertEqual(f["row_count"], 29750)
        self.assertTrue(f["filename"].endswith(".parquet"))


class Lean4Dialect(unittest.TestCase):
    """The shared classifier must handle Lean 4 spellings and Unicode names."""

    def _mk(self, goal, vars=(), hyps=(), fn=False, domain=None):
        return {
            "name": "t", "goal": goal, "value_vars": list(vars),
            "hyps": list(hyps), "fn_unknown": fn, "domain_vars": domain or {},
        }

    def test_greek_value_vars_are_covered(self) -> None:
        r = gc.classify(self._mk("α + β = 2", vars=("α", "β")))
        self.assertTrue(r["full_ok"])

    def test_greek_complex_var_is_rejected(self) -> None:
        # regression: an ASCII-only ident regex left ω (ℂ) invisible -> false pos.
        r = gc.classify(self._mk("ω^2 + ω + 1 = 0", domain={"ω": "complex_number"}))
        self.assertEqual(r["goal_reason"], "complex_number")

    def test_capitalized_and_bare_transcendentals_covered(self) -> None:
        self.assertTrue(gc.classify(self._mk("Real.sqrt a ≥ 0", vars=("a",)))["full_ok"])
        self.assertTrue(gc.classify(self._mk("sqrt a ≥ 0", vars=("a",)))["full_ok"])

    def test_forward_trig_supported_inverse_trig_still_gap(self) -> None:
        # v0.10 item 1: SIN/COS/TAN are now corpus heads (data/trigonometry), so
        # forward trig is covered; inverse/reciprocal trig remain gaps.
        self.assertTrue(
            gc.classify(self._mk("sin x ^ 2 + cos x ^ 2 = 1", vars=("x",)))["full_ok"]
        )
        self.assertEqual(
            gc.classify(self._mk("arctan x = 0", vars=("x",)))["goal_reason"], "trig"
        )
        self.assertEqual(
            gc.classify(self._mk("cot x = 1", vars=("x",)))["goal_reason"], "trig"
        )

    def test_zmod_congruence_is_modulo_gap(self) -> None:
        r = gc.classify(self._mk("2 ^ 21 ≡ 1 [ZMOD 7]"))
        self.assertEqual(r["goal_reason"], "modulo_no_head")

    def test_lean4_complex_and_zmod_binders(self) -> None:
        _, _, _, dom = gc.classify_binder("a b c d : ℂ")
        self.assertEqual({n for n, _ in dom}, {"a", "b", "c", "d"})
        _, _, is_fn, _ = gc.classify_binder("f : ℕ → NNReal")
        self.assertTrue(is_fn)

    def test_parse_full_proof_strips_preamble_and_comment(self) -> None:
        row = (
            "import Mathlib\n\nopen BigOperators Real Nat\n\n"
            "/- an informal statement with $\\LaTeX$ -/\n"
            "theorem lean_workbook_1 (a b : ℝ) (h : 0 < a ∧ 0 < b) : "
            "a + b > 0 := by\n  nlinarith"
        )
        p = ing.parse_full_proof("lean_workbook_1", row)
        self.assertEqual(p["name"], "lean_workbook_1")
        self.assertEqual(p["value_vars"], ["a", "b"])
        self.assertEqual(p["goal"], "a + b > 0")
        self.assertIn("0 < a ∧ 0 < b", p["hyps"])


class CarrierAwareness(unittest.TestCase):
    """Regression for the adversarial-review blocker: `/` and `-` over ℕ/ℤ are
    Nat.div/Int.div (floor) and monus, not the real operations."""

    def _mk(self, goal, nat=False, intz=False, field=False, vars=(), hyps=()):
        return {
            "name": "t", "goal": goal, "value_vars": list(vars), "hyps": list(hyps),
            "fn_unknown": False, "domain_vars": {},
            "has_nat_carrier": nat, "has_int_carrier": intz, "has_field_carrier": field,
        }

    def test_nat_division_is_a_gap(self) -> None:
        r = gc.classify(self._mk("(1 + 1 / n)^n < 3", nat=True, vars=("n",)))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_int_division_is_a_gap(self) -> None:
        r = gc.classify(self._mk("a / b = 1", intz=True, vars=("a", "b")))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")

    def test_nat_monus_is_a_gap(self) -> None:
        r = gc.classify(self._mk("a - b = 0", nat=True, vars=("a", "b")))
        self.assertEqual(r["goal_reason"], "nat_monus_no_head")

    def test_real_division_is_covered(self) -> None:
        r = gc.classify(self._mk("x / 2 > 0", field=True, vars=("x",)))
        self.assertTrue(r["goal_ok"])

    def test_int_subtraction_over_Z_is_fine(self) -> None:
        # ℤ is a ring; `-` is genuine subtraction, not monus.
        r = gc.classify(self._mk("a - b = c", intz=True, vars=("a", "b", "c")))
        self.assertTrue(r["goal_ok"])

    def test_fractional_exponent_is_a_gap_regardless_of_carrier(self) -> None:
        for kw in ({"field": True}, {"nat": True}):
            r = gc.classify(self._mk("x ^ (1 / 3) = 2", vars=("x",), **kw))
            self.assertEqual(r["goal_reason"], "fractional_exponent")

    def test_coercion_signal_keeps_division_real(self) -> None:
        # a coercion ↑ means the arithmetic is over a field even with a ℕ binder.
        r = gc.classify(self._mk("(↑n) / 2 > 0", nat=True, vars=("n",)))
        self.assertTrue(r["goal_ok"])

    def test_nat_inverse_is_a_gap(self) -> None:
        r = gc.classify(self._mk("x⁻¹ + y⁻¹ = 4", nat=True, vars=("x", "y")))
        self.assertEqual(r["goal_reason"], "integer_division_no_head")


class CommittedArtifacts(unittest.TestCase):
    def setUp(self) -> None:
        self.ext = json.loads(ing.EXTRACT_PATH.read_text(encoding="utf-8"))
        self.cov = json.loads(ing.COVERAGE_PATH.read_text(encoding="utf-8"))

    def test_extract_is_complete(self) -> None:
        self.assertEqual(self.ext["row_count"], 29750)
        self.assertEqual(
            self.ext["parsed_count"] + self.ext["unparsed_count"], 29750
        )
        self.assertEqual(len(self.ext["statements"]), self.ext["parsed_count"])
        self.assertEqual(self.ext["source"]["hf_revision"], _source()["hf_revision"])

    def test_coverage_regenerates_byte_for_byte(self) -> None:
        rebuilt = gc.serialize(ing.build_coverage(self.ext))
        self.assertEqual(
            rebuilt, ing.COVERAGE_PATH.read_bytes(),
            "committed lean_workbook_coverage.json is stale; re-run coverage",
        )

    def test_totals_partition_rows(self) -> None:
        t = self.cov["totals"]
        untl = sum(self.cov["full_statement_untranslatable_reasons"].values())
        self.assertEqual(untl + t["full_statement"]["covered"], t["rows"])
        self.assertGreaterEqual(
            t["goal_only"]["covered"], t["full_statement"]["covered"]
        )

    def test_duplicate_stats_are_consistent(self) -> None:
        d = self.cov["duplicate_analysis"]
        self.assertEqual(
            d["unique_goals"] + d["duplicate_statements"], d["total_statements"]
        )
        self.assertGreater(d["duplicate_statements"], 0, "Lean Workbook has restatements")
        self.assertLessEqual(d["unique_covered_goals"], d["covered_statements"])

    def test_covered_set_has_no_out_of_grammar_glyphs(self) -> None:
        """The false-positive guard: every covered goal/hyp contains only
        whitelisted characters — no stray operator glyph survives as COVERED."""
        byname = {s["name"]: s for s in self.ext["statements"]}
        allowed = set(
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "+-*/^=<>≤≥≠∧∨¬→↔() .:_'↑ℝℕℤℚπ√∀∃,"
        )  # v0.10: ∀ ∃ and the binder comma are grammar glyphs; `∃!` is
        # pre-stripped below so a bare factorial `!` still trips the audit.
        allowed |= {chr(c) for c in range(0x2080, 0x209D)}  # subscripts
        allowed |= {chr(c) for c in range(0x2070, 0x2080)}  # superscripts
        allowed |= set("¹²³⁄")
        allowed |= {chr(c) for c in range(0x0370, 0x0400)}  # Greek block
        offenders = []
        for name in self.cov["covered_full_statement_names"]:
            s = byname[name]
            for txt in [s["goal"]] + s["hyps"]:
                norm = re.sub(r"([∀∃]\s*)\{([^{}|]*)\}", r"\1(\2)",
                              txt.replace("∃!", "∃"))
                bad = set(norm) - allowed
                if bad:
                    offenders.append((name, "".join(sorted(bad))))
                    break
        self.assertEqual(offenders, [], f"covered with foreign glyphs: {offenders[:5]}")

    def test_no_covered_statement_uses_a_gap_head(self) -> None:
        byname = {s["name"]: s for s in self.ext["statements"]}
        for name in self.cov["covered_full_statement_names"]:
            s = byname[name]
            for txt in [s["goal"]] + s["hyps"]:
                self.assertNotIn("%", txt, name)
                self.assertNotIn("∣", txt, name)
                self.assertNotIn("∑", txt, name)


if __name__ == "__main__":
    unittest.main()
