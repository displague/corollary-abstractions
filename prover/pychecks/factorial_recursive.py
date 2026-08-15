"""Pinned candidate for programming.factorial.recursive.

The body is the TheAlgorithms/Python function `factorial_recursive`
(commit f5988cc, MIT; extract in data_sources/derived/algorithms/).
A python-tests PASS over this file certifies compile + mypy --strict +
the pinned tests, not correctness in general.
"""

from __future__ import annotations


def factorial_recursive(n: int) -> int:
    """n!, recursive, base n in {0, 1}."""
    return 1 if n in {0, 1} else n * factorial_recursive(n - 1)
