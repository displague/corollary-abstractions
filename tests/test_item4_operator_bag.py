"""P3 of docs/DESIGN-item4-authoring.md: operator-bag vs typed matcher.

Registered before the 251-node ingest ran. The bag pairs by the surface
glyph set {+,-,*,/,^,=}; the matcher pairs by typed skeleton. The bag
must form strictly more pairs; matcher precision against the bag must
stay 1.0 (same skeleton implies same glyphs); bag precision is the
number of record.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from measure_operator_bag import measure  # noqa: E402


class OperatorBagBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = measure(REPO_ROOT / "data")

    def test_zero_parse_problems(self) -> None:
        self.assertEqual(self.report["parse_problems"], 0)

    def test_bag_forms_strictly_more_pairs(self) -> None:
        all_ = self.report["all"]
        self.assertGreater(all_["operator_bag"]["pairs"], all_["matcher"]["pairs"])

    def test_matcher_precision_against_the_bag_is_one(self) -> None:
        self.assertEqual(self.report["all"]["only_matcher"], 0)
        self.assertEqual(self.report["all"]["matcher"]["precision"], 1.0)

    def test_ingesting_ground_identities_worsens_bag_precision(self) -> None:
        """The roadmap question, on this wave: the baseline still 'wins'
        on pair count and loses harder on precision than it did on 257.
        """
        prior = self.report["prior"]["operator_bag"]["precision"]
        ingested = self.report["ingested"]["operator_bag"]["precision"]
        combined = self.report["all"]["operator_bag"]["precision"]
        self.assertLess(ingested, prior)
        self.assertLess(combined, prior)
        self.assertLess(combined, 0.03)


if __name__ == "__main__":
    unittest.main()
