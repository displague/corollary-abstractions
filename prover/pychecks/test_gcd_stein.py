"""Pinned tests for gcd_stein."""

from __future__ import annotations

import unittest

from gcd_stein import gcd_stein


class SteinBinary(unittest.TestCase):
    def test_known_pair(self) -> None:
        self.assertEqual(gcd_stein(24, 40), 8)

    def test_ones(self) -> None:
        self.assertEqual(gcd_stein(1, 1), 1)
        self.assertEqual(gcd_stein(11, 37), 1)

    def test_negatives(self) -> None:
        self.assertEqual(gcd_stein(-3, 9), 3)
        self.assertEqual(gcd_stein(-3, -9), 3)

    def test_zero_zero(self) -> None:
        self.assertEqual(gcd_stein(0, 0), 0)

    def test_powers_of_two(self) -> None:
        self.assertEqual(gcd_stein(16, 48), 16)


if __name__ == "__main__":
    unittest.main()
