#!/usr/bin/env python3
"""L1–L4 legality strata tags (P-LS11) — separable failure reasons.

Fragment: ``legality.strata.v1``

Does not replace verifiers; it standardizes *labels* so traces do not collapse
parse failure, type failure, index REFUTED, and normative REFUSED into one
string (DESIGN-language-as-structure §5.3.1, R11).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


FRAGMENT_ID = "legality.strata.v1"


class LegalityStratum(str, Enum):
    """Four notions of legal — do not conflate."""

    L1_GRAMMATICAL = "L1_grammatical"
    L2_WELL_TYPED = "L2_well_typed"
    L3_INDEX = "L3_index_consistent"
    L4_NORMATIVE = "L4_normative"


@dataclass(frozen=True)
class StratumVerdict:
    stratum: LegalityStratum
    ok: bool
    reason: str
    evidence: tuple[str, ...] = ()

    def tag(self) -> str:
        status = "ok" if self.ok else "fail"
        return f"{self.stratum.value}:{status}"


def grammatical_fail(reason: str, *evidence: str) -> StratumVerdict:
    return StratumVerdict(LegalityStratum.L1_GRAMMATICAL, False, reason, evidence)


def typed_fail(reason: str, *evidence: str) -> StratumVerdict:
    return StratumVerdict(LegalityStratum.L2_WELL_TYPED, False, reason, evidence)


def index_fail(reason: str, *evidence: str) -> StratumVerdict:
    return StratumVerdict(LegalityStratum.L3_INDEX, False, reason, evidence)


def normative_fail(reason: str, *evidence: str) -> StratumVerdict:
    return StratumVerdict(LegalityStratum.L4_NORMATIVE, False, reason, evidence)


def first_failure(
    checks: tuple[StratumVerdict, ...],
) -> StratumVerdict | None:
    """Return the first failing stratum verdict, or None if all ok."""
    for item in checks:
        if not item.ok:
            return item
    return None


def classify_story_introduce_trait(
    *,
    trait: str,
    allowed: frozenset[str],
    denied: frozenset[str],
) -> StratumVerdict:
    """Toy classifier for introduce-trait checks used in tests.

    - denied trait → L3 index (frame REFUTED against premises)
    - undeclared trait → L2 well-typed/semantic (UNKNOWN in story adapter)
    - allowed → L3 ok
    """
    if trait in denied:
        return index_fail(
            f"trait {trait!r} denied by frame premises",
            "narrative.frame.frame_consistency",
        )
    if trait not in allowed:
        return typed_fail(
            f"trait {trait!r} neither declared nor denied",
            "story.trait_inventory",
        )
    return StratumVerdict(
        LegalityStratum.L3_INDEX,
        True,
        f"trait {trait!r} admitted at frame index",
        ("frame",),
    )
