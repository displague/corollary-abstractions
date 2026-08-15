"""Pinned volume tests for the n-minus-2 factorial mutation.

Executed ONLY by scripts/_verifier_sandbox.py. Expected to FAIL: the
mutation agrees on {0, 1} and disagrees at 3. That FAIL is the recorded
negative (P-W6 / P-W11).
"""

from __future__ import annotations

import math
import unittest

from factorial_n_minus_2 import factorial_recursive


class FactorialNMinus2(unittest.TestCase):
    def test_agrees_with_math_factorial_through_19(self) -> None:
        for i in range(20):
            self.assertEqual(factorial_recursive(i), math.factorial(i), i)


if __name__ == "__main__":
    unittest.main()
