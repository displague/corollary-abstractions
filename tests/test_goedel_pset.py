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


if __name__ == "__main__":
    unittest.main()
