"""Pinned candidate for programming.euclid.iterative.

The body is the TheAlgorithms/Python function `gcd_by_iterative`
(commit f5988cc, MIT; extract in data_sources/derived/algorithms/).
A python-tests PASS over this file certifies compile + mypy --strict +
the pinned tests, not correctness in general.
"""

from __future__ import annotations


def gcd_by_iterative(x: int, y: int) -> int:
    """Euclidean GCD, while-loop evaluation of the same remainder recurrence."""
    while y:
        x, y = y, x % y
    return abs(x)
