"""Pinned tests for lean_workbook_1041_check (13 | 2^30 + 3^60).

Executed ONLY by scripts/_verifier_sandbox.py under the python-tests backend
(the repo suite discovers tests/ alone). The digest of this file is pinned in
the committed verdict; editing it invalidates the verdict, which is the point.
"""

from __future__ import annotations

import unittest

from lean_workbook_1041_check import DIVISOR, claim_dividend, claim_residue


class LeanWorkbook1041(unittest.TestCase):
    def test_residue_is_zero(self) -> None:
        """The ingested claim itself: 13 divides 2^30 + 3^60 exactly."""
        self.assertEqual(claim_residue(), 0)

    def test_dividend_is_the_claimed_term(self) -> None:
        """The dividend is the statement's term, not a stand-in."""
        self.assertEqual(claim_dividend(), 2**30 + 3**60)

    def test_divisor_is_thirteen(self) -> None:
        self.assertEqual(DIVISOR, 13)


if __name__ == "__main__":
    unittest.main()
