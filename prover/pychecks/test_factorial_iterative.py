"""Pinned volume tests for factorial (iterative).

Executed ONLY by scripts/_verifier_sandbox.py under the python-tests
backend. The range(20) loop is the TheAlgorithms doctest, kept as a
real loop (P-W11).
"""

from __future__ import annotations

import math
import unittest

from factorial_iterative import factorial


class FactorialIterative(unittest.TestCase):
    def test_agrees_with_math_factorial_through_19(self) -> None:
        for i in range(20):
            self.assertEqual(factorial(i), math.factorial(i), i)

    def test_source_doctest_points(self) -> None:
        self.assertEqual(factorial(0), 1)
        self.assertEqual(factorial(1), 1)
        self.assertEqual(factorial(6), 720)


if __name__ == "__main__":
    unittest.main()
