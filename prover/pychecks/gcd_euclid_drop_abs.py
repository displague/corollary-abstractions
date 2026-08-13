"""Declared debug mutation of the recursive Euclid candidate.

Same body as gcd_euclid_recursive.py with `abs` deleted. Compiles and
type-checks; the pinned tests that include negatives FAIL. The FAIL
verdict is committed and cited by no node
(docs/DESIGN-programming-discipline.md §5.3, P6).
"""

from __future__ import annotations


def greatest_common_divisor(a: int, b: int) -> int:
    """Broken Euclid: drops abs, so a negative base-case remainder leaks."""
    return b if a == 0 else greatest_common_divisor(b % a, a)
