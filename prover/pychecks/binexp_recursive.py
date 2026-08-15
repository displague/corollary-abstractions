"""Pinned candidate for programming.binexp.recursive.

The body is the TheAlgorithms/Python function `binary_exp_recursive`
(commit f5988cc, MIT; extract in data_sources/derived/algorithms/).
A python-tests PASS over this file certifies compile + mypy --strict +
the pinned tests, not correctness in general.
"""

from __future__ import annotations


def binary_exp_recursive(base: float, exponent: int) -> float:
    """a^b by squaring, recursive. Odd-first in the source; even-first on the node."""
    if exponent == 0:
        return 1
    if exponent % 2 == 1:
        return binary_exp_recursive(base, exponent - 1) * base
    half = binary_exp_recursive(base, exponent // 2)
    return half * half
