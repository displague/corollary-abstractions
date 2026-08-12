#!/usr/bin/env python3
"""Packed ambiguity: filter before prefer (P-LS8).

Fragment: ``ambiguity.forest.v1``

A surface string may yield multiple candidate terms (attachment / scope).
Hard filters (world/frame/index constraints) run first. Preference is never
invoked on the unfiltered forest. Outcomes:

- 0 remain → UNKNOWN / ASK
- 1 remains → UNIQUE
- >1 remain → MULTI (report all) or ASK — never a silent unique parse

Suite registration: M ≥ 15 controlled items with ≥ 2 candidates each.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Sequence


FRAGMENT_ID = "ambiguity.forest.v1"


class AmbiguityOutcome(str, Enum):
    UNIQUE = "unique"
    MULTI = "multi"
    ASK = "ask"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ForestCandidate:
    """One parse/term reading of a surface string."""

    candidate_id: str
    reading: str  # structural label e.g. attach_high / attach_low / scope_wide
    term_key: str  # denotation key for equality of meaning

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must be non-empty")


@dataclass(frozen=True)
class HardConstraint:
    """Named hard filter; returns True if the candidate is legal."""

    name: str
    accepts: Callable[[ForestCandidate], bool]


@dataclass(frozen=True)
class AmbiguityItem:
    """One registered ambiguity case for the suite."""

    item_id: str
    surface: str
    candidates: tuple[ForestCandidate, ...]
    constraints: tuple[HardConstraint, ...] = ()

    def __post_init__(self) -> None:
        if len(self.candidates) < 2:
            raise ValueError(
                f"item {self.item_id!r} must ship ≥2 candidates for P-LS8"
            )


@dataclass(frozen=True)
class AmbiguityResult:
    outcome: AmbiguityOutcome
    survivors: tuple[ForestCandidate, ...]
    eliminated: tuple[tuple[ForestCandidate, str], ...]  # cand, constraint name
    preferred_invoked: bool
    fragment_id: str = FRAGMENT_ID


def hard_filter(
    candidates: Sequence[ForestCandidate],
    constraints: Sequence[HardConstraint],
) -> tuple[tuple[ForestCandidate, ...], tuple[tuple[ForestCandidate, str], ...]]:
    """Apply all hard constraints; never rank."""
    survivors: list[ForestCandidate] = []
    eliminated: list[tuple[ForestCandidate, str]] = []
    for cand in candidates:
        blocked_by: str | None = None
        for cons in constraints:
            if not cons.accepts(cand):
                blocked_by = cons.name
                break
        if blocked_by is None:
            survivors.append(cand)
        else:
            eliminated.append((cand, blocked_by))
    return tuple(survivors), tuple(eliminated)


def resolve_forest(
    item: AmbiguityItem,
    *,
    prefer_when_multi: bool = False,
    prefer: Callable[[Sequence[ForestCandidate]], ForestCandidate] | None = None,
) -> AmbiguityResult:
    """Filter then decide UNIQUE / MULTI / ASK / UNKNOWN.

    Preference is only legal when ``prefer_when_multi`` is True *and* a
    ``prefer`` function is supplied *and* survivors > 1. Even then, the
    result records that preference ran; default for the fragment is
    MULTI without preference (silent unique is forbidden).
    """
    survivors, eliminated = hard_filter(item.candidates, item.constraints)
    if len(survivors) == 0:
        return AmbiguityResult(
            AmbiguityOutcome.UNKNOWN, (), eliminated, preferred_invoked=False
        )
    if len(survivors) == 1:
        return AmbiguityResult(
            AmbiguityOutcome.UNIQUE, survivors, eliminated, preferred_invoked=False
        )
    # >1 survivors
    if prefer_when_multi and prefer is not None:
        chosen = prefer(survivors)
        if chosen not in survivors:
            raise ValueError("prefer() emitted OOV candidate")
        return AmbiguityResult(
            AmbiguityOutcome.UNIQUE,
            (chosen,),
            eliminated,
            preferred_invoked=True,
        )
    # Default: multi or ask — never silent unique without recording alts
    return AmbiguityResult(
        AmbiguityOutcome.MULTI, survivors, eliminated, preferred_invoked=False
    )


def make_attachment_suite() -> tuple[AmbiguityItem, ...]:
    """M≥15 controlled attachment/scope items with ≥2 candidates each."""
    items: list[AmbiguityItem] = []
    # Attachment: "saw NP with telescope" — high vs low attach
    for i in range(8):
        world_blocks_low = i % 2 == 0
        high = ForestCandidate(f"att{i}_high", "attach_high", f"see_man_i{i}")
        low = ForestCandidate(f"att{i}_low", "attach_low", f"see_man_with_scope_i{i}")
        cons: list[HardConstraint] = []
        if world_blocks_low:
            cons.append(
                HardConstraint(
                    "world_no_instrument",
                    lambda c, low_id=low.candidate_id: c.candidate_id != low_id,
                )
            )
        items.append(
            AmbiguityItem(
                item_id=f"attach_{i}",
                surface=f"saw the man with the telescope #{i}",
                candidates=(high, low),
                constraints=tuple(cons),
            )
        )
    # Scope: every/some relative order
    for i in range(7):
        wide = ForestCandidate(f"scp{i}_wide", "scope_wide", f"forall_exists_i{i}")
        narrow = ForestCandidate(f"scp{i}_narrow", "scope_narrow", f"exists_forall_i{i}")
        # Frame blocks wide for odd i
        cons2: list[HardConstraint] = []
        if i % 2 == 1:
            cons2.append(
                HardConstraint(
                    "frame_blocks_wide",
                    lambda c, wid=wide.candidate_id: c.candidate_id != wid,
                )
            )
        items.append(
            AmbiguityItem(
                item_id=f"scope_{i}",
                surface=f"every student read some book #{i}",
                candidates=(wide, narrow),
                constraints=tuple(cons2),
            )
        )
    if len(items) < 15:
        raise RuntimeError("suite must be M>=15")
    return tuple(items)
