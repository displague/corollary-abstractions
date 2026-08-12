"""P-LS11: L1–L4 failure tags are separable."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from legality_strata import (  # noqa: E402
    FRAGMENT_ID,
    LegalityStratum,
    StratumVerdict,
    classify_story_introduce_trait,
    first_failure,
    grammatical_fail,
    index_fail,
    normative_fail,
    typed_fail,
)


class StrataSeparabilityTests(unittest.TestCase):
    def test_four_injected_failures_have_distinct_tags(self) -> None:
        injected = (
            grammatical_fail("no parse", "parser"),
            typed_fail("bad arity", "type"),
            index_fail("world refuted", "world"),
            normative_fail("obligation open", "chekhov"),
        )
        tags = [v.tag() for v in injected]
        self.assertEqual(len(tags), 4)
        self.assertEqual(len(set(tags)), 4)
        strata = {v.stratum for v in injected}
        self.assertEqual(
            strata,
            {
                LegalityStratum.L1_GRAMMATICAL,
                LegalityStratum.L2_WELL_TYPED,
                LegalityStratum.L3_INDEX,
                LegalityStratum.L4_NORMATIVE,
            },
        )
        self.assertTrue(all(not v.ok for v in injected))
        self.assertEqual(FRAGMENT_ID, "legality.strata.v1")

    def test_first_failure_preserves_order(self) -> None:
        checks = (
            StratumVerdict(LegalityStratum.L1_GRAMMATICAL, True, "ok"),
            typed_fail("type"),
            index_fail("index"),
        )
        hit = first_failure(checks)
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.stratum, LegalityStratum.L2_WELL_TYPED)

    def test_classify_denied_trait_is_l3_not_l1(self) -> None:
        v = classify_story_introduce_trait(
            trait="silver",
            allowed=frozenset({"golden"}),
            denied=frozenset({"silver"}),
        )
        self.assertFalse(v.ok)
        self.assertEqual(v.stratum, LegalityStratum.L3_INDEX)
        self.assertNotEqual(v.stratum, LegalityStratum.L1_GRAMMATICAL)

    def test_classify_undeclared_trait_is_l2(self) -> None:
        v = classify_story_introduce_trait(
            trait="brave",
            allowed=frozenset({"golden"}),
            denied=frozenset({"silver"}),
        )
        self.assertFalse(v.ok)
        self.assertEqual(v.stratum, LegalityStratum.L2_WELL_TYPED)

    def test_classify_allowed_trait_ok_at_l3(self) -> None:
        v = classify_story_introduce_trait(
            trait="golden",
            allowed=frozenset({"golden"}),
            denied=frozenset({"silver"}),
        )
        self.assertTrue(v.ok)
        self.assertEqual(v.stratum, LegalityStratum.L3_INDEX)


if __name__ == "__main__":
    unittest.main()
