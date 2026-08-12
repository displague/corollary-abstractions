"""Pinned computational candidate for lean_workbook_1041 (13 | 2^30 + 3^60).

This module is an INPUT to scripts/external_verifier.py's python-tests
backend: its sha256 is recorded in the committed verdict
prover/verifier-verdicts/lean_workbook_1041.python-tests.json and re-checked
by `external_verifier.py ledger`/`recheck`. It is an independent, second
transition authority over the same ingested statement the lean4 backend
verifies — exact integer arithmetic here, kernel-checked `decide` there.

What a PASS over this file certifies, exactly: this candidate compiles,
passes mypy --strict, and its pinned test asserting `claim_residue() == 0`
passes under the sandboxed runner. Nothing more.
"""

from __future__ import annotations

DIVISOR: int = 13


def claim_dividend() -> int:
    """The dividend of the ingested claim, computed in exact arithmetic."""
    return 2**30 + 3**60


def claim_residue() -> int:
    """The residue of the ingested claim: 0 exactly when 13 | 2^30 + 3^60."""
    return claim_dividend() % DIVISOR
