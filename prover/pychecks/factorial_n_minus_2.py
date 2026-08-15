"""Declared debug mutation of the recursive factorial candidate.

Same body as factorial_recursive.py with the step rewritten `n - 2`.
Compiles and type-checks; the volume tests against math.factorial FAIL
(already at n = 3: 3 vs 6). The FAIL verdict is committed and cited by
no node (docs/DESIGN-programming-second-wave.md §5.3, P-W6).
"""

from __future__ import annotations


def factorial_recursive(n: int) -> int:
    """Broken factorial: steps by 2, so it agrees on {0,1} and fails at 3."""
    return 1 if n in {0, 1} else n * factorial_recursive(n - 2)
