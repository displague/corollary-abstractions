"""Pinned candidate for programming.euclid.recursive.

The body is the TheAlgorithms/Python function `greatest_common_divisor`
(commit f5988cc, MIT; extract in data_sources/derived/algorithms/).
A python-tests PASS over this file certifies compile + mypy --strict +
the pinned tests, not correctness in general.
"""

from __future__ import annotations


def greatest_common_divisor(a: int, b: int) -> int:
    """Euclidean GCD, recursive, first-arg-zero orientation."""
    return abs(b) if a == 0 else greatest_common_divisor(b % a, a)
