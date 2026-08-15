"""Pinned volume tests for binary_exp_iterative.

Executed ONLY by scripts/_verifier_sandbox.py under the python-tests
backend. Source doctests plus a volume expansion of the a^b claim
(docs/DESIGN-programming-second-wave.md §5.1).
"""

from __future__ import annotations

import unittest

from binexp_iterative import binary_exp_iterative


class BinaryExpIterative(unittest.TestCase):
    def test_source_doctests(self) -> None:
        self.assertEqual(binary_exp_iterative(3, 5), 243)
        self.assertEqual(binary_exp_iterative(11, 13), 34522712143931)
        self.assertEqual(binary_exp_iterative(-1, 3), -1)
        self.assertEqual(binary_exp_iterative(0, 5), 0)
        self.assertEqual(binary_exp_iterative(3, 1), 3)
        self.assertEqual(binary_exp_iterative(3, 0), 1)
        self.assertEqual(binary_exp_iterative(1.5, 4), 5.0625)

    def test_volume_against_pow_through_15(self) -> None:
        for exponent in range(16):
            for base in (-2, -1, 0, 1, 2, 3):
                self.assertEqual(
                    binary_exp_iterative(float(base), exponent),
                    float(base ** exponent),
                    (base, exponent),
                )


if __name__ == "__main__":
    unittest.main()
