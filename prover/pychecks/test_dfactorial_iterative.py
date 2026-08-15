"""Pinned volume tests for double_factorial_iterative.

Executed ONLY by scripts/_verifier_sandbox.py under the python-tests
backend. The range(20) loop is the TheAlgorithms doctest, kept as a
real loop (P-W11).
"""

from __future__ import annotations

import math
import unittest

from dfactorial_iterative import double_factorial_iterative


class DoubleFactorialIterative(unittest.TestCase):
    def test_agrees_with_prod_step_2_through_19(self) -> None:
        for i in range(20):
            self.assertEqual(
                double_factorial_iterative(i),
                math.prod(range(i, 0, -2)),
                i,
            )


if __name__ == "__main__":
    unittest.main()
