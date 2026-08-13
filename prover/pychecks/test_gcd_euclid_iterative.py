"""Pinned tests for gcd_euclid_iterative."""

from __future__ import annotations

import unittest

from gcd_euclid_iterative import gcd_by_iterative


class EuclidIterative(unittest.TestCase):
    def test_known_pair(self) -> None:
        self.assertEqual(gcd_by_iterative(24, 40), 8)

    def test_ones(self) -> None:
        self.assertEqual(gcd_by_iterative(1, 1), 1)
        self.assertEqual(gcd_by_iterative(1, -800), 1)
        self.assertEqual(gcd_by_iterative(11, 37), 1)

    def test_negatives(self) -> None:
        self.assertEqual(gcd_by_iterative(-3, -9), 3)
        self.assertEqual(gcd_by_iterative(3, -9), 3)

    def test_zero_zero(self) -> None:
        self.assertEqual(gcd_by_iterative(0, 0), 0)


if __name__ == "__main__":
    unittest.main()
