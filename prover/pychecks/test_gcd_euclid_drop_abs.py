"""Pinned tests for the drop-abs mutation.

Same cases as the recursive Euclid tests: the negatives are what FAIL.
"""

from __future__ import annotations

import unittest

from gcd_euclid_drop_abs import greatest_common_divisor


class EuclidDropAbs(unittest.TestCase):
    def test_known_pair(self) -> None:
        self.assertEqual(greatest_common_divisor(24, 40), 8)

    def test_negatives(self) -> None:
        self.assertEqual(greatest_common_divisor(-3, 9), 3)
        self.assertEqual(greatest_common_divisor(-3, -9), 3)


if __name__ == "__main__":
    unittest.main()
