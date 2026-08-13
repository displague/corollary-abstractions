"""Pinned first-party candidate for programming.stein.binary.

Stein's binary GCD. First-party and disclosed as such
(docs/DESIGN-programming-discipline.md §3): it is the name-similar
non-twin for the Euclid pair, not an ingested source. A python-tests
PASS certifies compile + mypy --strict + the pinned tests, not
correctness in general.
"""

from __future__ import annotations


def gcd_stein(a: int, b: int) -> int:
    """Binary GCD (Stein). Different recurrence from Euclid."""
    a = abs(a)
    b = abs(b)
    if a == 0:
        return b
    if b == 0:
        return a
    shift = 0
    while ((a | b) & 1) == 0:
        a >>= 1
        b >>= 1
        shift += 1
    while (a & 1) == 0:
        a >>= 1
    while b != 0:
        while (b & 1) == 0:
            b >>= 1
        if a > b:
            a, b = b, a
        b -= a
    return a << shift
