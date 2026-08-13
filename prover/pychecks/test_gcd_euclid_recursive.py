"""Pinned tests for gcd_euclid_recursive.

Executed ONLY by scripts/_verifier_sandbox.py under the python-tests
backend (the repo suite discovers tests/ alone). Includes the
TheAlgorithms doctest cases plus the negatives that make dropping abs
a FAIL.
"""

from __future__ import annotations

import unittest

from gcd_euclid_recursive import greatest_common_divisor


class EuclidRecursive(unittest.TestCase):
    def test_known_pair(self) -> None:
        self.assertEqual(greatest_common_divisor(24, 40), 8)

    def test_ones(self) -> None:
        self.assertEqual(greatest_common_divisor(1, 1), 1)
        self.assertEqual(greatest_common_divisor(1, 800), 1)
        self.assertEqual(greatest_common_divisor(11, 37), 1)
        self.assertEqual(greatest_common_divisor(3, 5), 1)

    def test_divides(self) -> None:
        self.assertEqual(greatest_common_divisor(16, 4), 4)

    def test_negatives(self) -> None:
        self.assertEqual(greatest_common_divisor(-3, 9), 3)
        self.assertEqual(greatest_common_divisor(9, -3), 3)
        self.assertEqual(greatest_common_divisor(3, -9), 3)
        self.assertEqual(greatest_common_divisor(-3, -9), 3)

    def test_zero_zero(self) -> None:
        self.assertEqual(greatest_common_divisor(0, 0), 0)


if __name__ == "__main__":
    unittest.main()
