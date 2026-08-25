#!/usr/bin/env python3
"""The point sampler, committed before the compiler so E7 can freeze it.

`docs/DESIGN-statements-that-run.md` E7 records the digests of the parser,
the evaluator, the domain schema **and the sampler** in the preregistration
commit, *before* `conform.py` is written. So the sampler is its own module:
a digest cannot be frozen before the thing it names exists.

**E5 — determinism, and why the seed is not a knob.** The seed is derived
from the domain schema's digest by a committed rule, so the point set is a
function of committed artifacts rather than of a wall clock. Same statement,
same schema, same seed produces a byte-identical record; two full runs on
one tree produce byte-identical artifacts. A seed someone chose would be a
knob, and a knob is a place to tune a result.

**E6 / §9 — the seat that stays closed.** Nothing here is learned. The only
place a ranker could sit in this design is choosing which points to test,
and a learned sampler is precisely the component that could make
`NO_COUNTEREXAMPLE_FOUND` mean less than it says by learning to avoid the
region where a statement fails. §9 closes that seat in writing; this module
is where it would otherwise have opened.

**What the sampler does not do.** It does not solve. An equality conjunct is
measure-zero under sampling (E0d), and this sampler does not rearrange one
to reach it — a one-equation solve is a named successor with its own
registration, and pretending to sample a measure-zero set would be reporting
admission that never happened.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from fractions import Fraction

#: M, frozen by E2: sampled points per statement.
DEFAULT_BUDGET = 1000

#: The value pool, small and rational on purpose. Exact arithmetic means a
#: sampled point is a `Fraction`, and the pool spans sign, zero, unit,
#: small integers and a few non-integers so that a statement true only of
#: integers is reachable by a rational point.
_NUMERATORS = (-7, -3, -2, -1, 0, 1, 2, 3, 4, 5, 7, 11)
_DENOMINATORS = (1, 1, 1, 2, 3, 4)


def derive_seed(schema_digest: str, statement_id: str) -> int:
    """E5's committed rule: the seed is a function of committed artifacts.

    The schema digest ties the point set to the reviewed table, and the
    statement id makes two statements' point sets independent without
    introducing a counter that a re-run could advance.
    """

    material = f"{schema_digest}\n{statement_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


class _Stream:
    """A deterministic value stream. Not `random`, so no global state exists."""

    def __init__(self, seed: int) -> None:
        self._state = seed & ((1 << 64) - 1)

    def next_int(self) -> int:
        # SplitMix64: small, deterministic, and committed here rather than
        # imported, so the point set cannot move when a library does.
        self._state = (self._state + 0x9E3779B97F4A7C15) & ((1 << 64) - 1)
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & ((1 << 64) - 1)
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & ((1 << 64) - 1)
        return z ^ (z >> 31)

    def choice(self, pool):
        return pool[self.next_int() % len(pool)]


@dataclass(frozen=True)
class Point:
    """One candidate binding set, before any guard has looked at it."""

    bindings: tuple[tuple[str, Fraction], ...]

    def as_dict(self) -> dict[str, Fraction]:
        return dict(self.bindings)

    def printable(self) -> dict[str, str]:
        return {name: str(value) for name, value in self.bindings}


def sample_points(
    variables,
    schema_digest: str,
    statement_id: str,
    budget: int = DEFAULT_BUDGET,
):
    """`budget` candidate points over `variables`, deterministically.

    Candidates, not admitted points: the guard decides admission, and the
    two counts are reported separately and never summed (§3.2). A statement
    whose guard admits none of these has a record that says nothing at all,
    and E2a refuses it rather than calling that agreement.
    """

    names = tuple(sorted(variables))
    if not names:
        return []
    stream = _Stream(derive_seed(schema_digest, statement_id))
    points = []
    for _ in range(budget):
        bindings = []
        for name in names:
            numerator = stream.choice(_NUMERATORS)
            denominator = stream.choice(_DENOMINATORS)
            bindings.append((name, Fraction(numerator, denominator)))
        points.append(Point(tuple(bindings)))
    return points


def sampler_digest() -> str:
    """This file's own LF digest — what E7 freezes."""

    from pathlib import Path

    return hashlib.sha256(
        Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
