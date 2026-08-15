"""Pinned volume tests for factorial_recursive.

Executed ONLY by scripts/_verifier_sandbox.py under the python-tests
backend (the repo suite discovers tests/ alone). The range(20) loop is
the TheAlgorithms doctest, kept as a real loop (P-W11).
"""

from __future__ import annotations

import math
import unittest

from factorial_recursive import factorial_recursive


class FactorialRecursive(unittest.TestCase):
    def test_agrees_with_math_factorial_through_19(self) -> None:
        for i in range(20):
            self.assertEqual(factorial_recursive(i), math.factorial(i), i)

    def test_source_doctest_points(self) -> None:
        self.assertEqual(factorial_recursive(0), 1)
        self.assertEqual(factorial_recursive(1), 1)


if __name__ == "__main__":
    unittest.main()
