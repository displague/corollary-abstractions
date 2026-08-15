"""Pinned candidate for programming.binexp.iterative.

The body is the TheAlgorithms/Python function `binary_exp_iterative`
(commit f5988cc, MIT; extract in data_sources/derived/algorithms/).
A python-tests PASS over this file certifies compile + mypy --strict +
the pinned tests, not correctness in general.
"""

from __future__ import annotations


def binary_exp_iterative(base: float, exponent: int) -> float:
    """a^b by squaring, iterative bit-shift. Same recurrence as recursive."""
    result: float = 1.0
    while exponent > 0:
        if exponent & 1:
            result *= base
        base *= base
        exponent >>= 1
    return result
