#!/usr/bin/env python3
"""Index-relative language outcomes for belief and fiction (P-LS10, P-LS12).

Fragment: ``index.language.v1``

- Attitude reports are legal at the belief index even when world-false.
- Fiction-frame asserts are index-legal; on exit they do not promote to
  world VERIFIED (demotion / non-leak).

Does not re-implement FrameExecutor; uses lightweight IndexState mirrors of
the same epistemic discipline for a registered test suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum


FRAGMENT_ID = "index.language.v1"


class IndexId(str, Enum):
    WORLD = "world"
    BELIEF = "belief"  # e.g. Sally
    FICTION = "fiction"  # e.g. golden_chicken frame


class IndexStatus(str, Enum):
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    UNKNOWN = "UNKNOWN"
    REFUSED = "REFUSED"


@dataclass(frozen=True)
class Proposition:
    key: str  # e.g. marble_location=basket
    surface: str  # realized English


@dataclass(frozen=True)
class IndexState:
    """Facts held at one index; immutable updates."""

    index_id: IndexId
    facts: frozenset[str] = frozenset()
    open: bool = True  # fiction frame open?

    def assert_fact(self, fact: str) -> tuple["IndexState", IndexStatus]:
        if self.index_id is IndexId.FICTION and not self.open:
            return self, IndexStatus.REFUSED
        # Contradiction within index
        neg = _negate(fact)
        if neg in self.facts:
            return self, IndexStatus.REFUTED
        return (
            replace(self, facts=self.facts | {fact}),
            IndexStatus.VERIFIED,
        )


def _negate(fact: str) -> str:
    if fact.startswith("not:"):
        return fact[4:]
    return f"not:{fact}"


@dataclass
class MultiIndexWorld:
    """World + belief + fiction indices; tracks world-leak attempts."""

    world: IndexState = field(
        default_factory=lambda: IndexState(
            IndexId.WORLD, frozenset({"marble_location=box"})
        )
    )
    belief: IndexState = field(
        default_factory=lambda: IndexState(
            IndexId.BELIEF, frozenset({"marble_location=basket"})
        )
    )
    fiction: IndexState = field(
        default_factory=lambda: IndexState(
            IndexId.FICTION,
            frozenset({"agent=golden_chicken", "trait=golden"}),
            open=True,
        )
    )
    world_verified_leaks: int = 0

    def utter_attitude(
        self, surface: str, content_fact: str
    ) -> tuple[IndexStatus, IndexStatus]:
        """Report attitude: legal at belief even if world disagrees.

        Returns (belief_status, world_status_of_same_content).
        """
        # Belief may already hold content; asserting report is VERIFIED at belief
        belief_status = (
            IndexStatus.VERIFIED
            if content_fact in self.belief.facts
            else IndexStatus.UNKNOWN
        )
        # Re-check / affirm at belief index
        new_belief, belief_status = self.belief.assert_fact(content_fact)
        self.belief = new_belief
        # World evaluation of the same content (unguarded)
        if content_fact in self.world.facts:
            world_status = IndexStatus.VERIFIED
        elif _negate(content_fact) in self.world.facts or any(
            f.startswith("marble_location=") and f != content_fact
            for f in self.world.facts
        ):
            # Distinct location facts conflict for this fragment
            world_status = IndexStatus.REFUTED
        else:
            world_status = IndexStatus.UNKNOWN
        return belief_status, world_status

    def utter_fiction_assert(self, fact: str) -> IndexStatus:
        new_f, status = self.fiction.assert_fact(fact)
        self.fiction = new_f
        return status

    def close_fiction(self) -> None:
        """Exit fiction: demote — do not copy facts into world VERIFIED."""
        self.fiction = replace(self.fiction, open=False)
        # Explicit non-leak: world unchanged; count if caller wrongly promotes
        # (promotion must go through promote_fiction_to_world)

    def promote_fiction_to_world(self, fact: str) -> IndexStatus:
        """Illegal laundering path — records leak attempts for tests."""
        if fact in self.fiction.facts and not self.fiction.open:
            self.world_verified_leaks += 1
            # Still do not actually verify in world for closed fiction
            return IndexStatus.REFUSED
        if fact in self.fiction.facts and self.fiction.open:
            # Open frame: still not auto world-verified without explicit world assert
            return IndexStatus.REFUSED
        return IndexStatus.UNKNOWN

    def world_has(self, fact: str) -> bool:
        return fact in self.world.facts


def attitude_report_surface(agent: str, content: str) -> str:
    return f"{agent} believes {content}"


def fiction_premise_surface(premise: str) -> str:
    return f"suppose {premise}"
