"""Pinned candidate for programming.dfactorial.iterative.

The body is the TheAlgorithms/Python function `double_factorial_iterative`
(commit f5988cc, MIT; extract in data_sources/derived/algorithms/).
A python-tests PASS over this file certifies compile + mypy --strict +
the pinned tests, not correctness in general.
"""

from __future__ import annotations


def double_factorial_iterative(num: int) -> int:
    """n!!, iterative product num, num-2, .... Same recurrence as recursive."""
    value = 1
    for i in range(num, 0, -2):
        value *= i
    return value
