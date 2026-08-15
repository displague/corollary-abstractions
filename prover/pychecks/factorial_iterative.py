"""Pinned candidate for programming.factorial.iterative.

The body is the TheAlgorithms/Python function `factorial`
(commit f5988cc, MIT; extract in data_sources/derived/algorithms/).
A python-tests PASS over this file certifies compile + mypy --strict +
the pinned tests, not correctness in general.
"""

from __future__ import annotations


def factorial(number: int) -> int:
    """n!, iterative product 1..n. Same recurrence as the recursive form."""
    value = 1
    for i in range(1, number + 1):
        value *= i
    return value
