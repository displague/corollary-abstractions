"""P-LS1 / P-LS1b: langgen.xlang.v1 surface round-trip with LOST dual.

Registration (DESIGN-language-as-structure §7):
  fragment_id: langgen.xlang.v1
  suite: N=500, seed=20260812, depth≤2, both langs A and B
  floor: ≥0.98 exact leaf-aware canonical equality after P(R_det(t))
  LOST: dual-pass over pinned suite file; LOST must be 0
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "scripts"))

from langgen import (  # noqa: E402
    FRAGMENT_ID,
    make_roundtrip_suite,
    parse,
    render,
    roundtrip_ok,
)
from match_signatures import canonicalize  # noqa: E402

SUITE_PATH = ROOT / "tests" / "fixtures" / "langgen_roundtrip_suite_v1.json"
SUITE_SEED = 20260812
SUITE_N = 500
SUITE_DEPTH = 2
FLOOR = 0.98


def _load_suite() -> list[tuple]:
    payload = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    assert payload["fragment_id"] == FRAGMENT_ID
    assert payload["seed"] == SUITE_SEED
    assert payload["n"] == SUITE_N

    def thaw(node):
        if isinstance(node, list):
            return tuple(thaw(x) for x in node)
        return node

    return [thaw(t) for t in payload["trees"]]


class RoundTripRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not SUITE_PATH.is_file():
            raise unittest.SkipTest(f"missing pinned suite {SUITE_PATH}")
        cls.suite = _load_suite()
        if len(cls.suite) != SUITE_N:
            raise AssertionError(f"suite size {len(cls.suite)} != {SUITE_N}")

    def test_suite_is_machine_generated_not_hand_picked(self) -> None:
        regenerated = make_roundtrip_suite(SUITE_N, SUITE_SEED, SUITE_DEPTH)
        self.assertEqual(
            [canonicalize(t) for t in regenerated],
            [canonicalize(t) for t in self.suite],
        )

    def test_p_ls1_floor_both_languages(self) -> None:
        for lang in ("A", "B"):
            hits = sum(1 for t in self.suite if roundtrip_ok(t, lang))
            rate = hits / len(self.suite)
            self.assertGreaterEqual(
                rate,
                FLOOR,
                f"{lang}: {hits}/{len(self.suite)}={rate:.4f} < floor {FLOOR}",
            )
            # Registered suite currently achieves 1.0 under deterministic R.
            self.assertEqual(hits, len(self.suite), f"{lang} incomplete suite")

    def test_p_ls1b_lost_dual_zero(self) -> None:
        """Every pinned tree still round-trips (LOST=0)."""
        lost: list[str] = []
        for i, t in enumerate(self.suite):
            for lang in ("A", "B"):
                if not roundtrip_ok(t, lang):
                    surface = render(t, lang, deterministic=True)
                    lost.append(f"{i}:{lang}:{surface}")
        self.assertEqual(lost, [], f"LOST={len(lost)} e.g. {lost[:3]}")

    def test_deterministic_render_is_stable(self) -> None:
        t = self.suite[0]
        a = render(t, "A", deterministic=True)
        b = render(t, "A", deterministic=True)
        self.assertEqual(a, b)
        self.assertEqual(parse(a, "A")[1], t[1])


if __name__ == "__main__":
    unittest.main()
