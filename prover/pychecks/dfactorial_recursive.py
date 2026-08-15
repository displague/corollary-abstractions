"""Pinned candidate for programming.dfactorial.recursive.

The body is the TheAlgorithms/Python function `double_factorial_recursive`
(commit f5988cc, MIT; extract in data_sources/derived/algorithms/).
A python-tests PASS over this file certifies compile + mypy --strict +
the pinned tests, not correctness in general.
"""

from __future__ import annotations


def double_factorial_recursive(n: int) -> int:
    """n!!, recursive, step n - 2. The factorial-named non-twin."""
    return 1 if n <= 1 else n * double_factorial_recursive(n - 2)
