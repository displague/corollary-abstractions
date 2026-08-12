#!/usr/bin/env python3
"""Entailment / contradiction without world commit (P-LS9).

Fragment: ``entailment.query.v1``

Answers whether A entails B, contradicts B, or is independent, using a
closed rule table over proposition ids. Does **not** mutate any world or
frame state. Every answer carries ``fragment_id``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


FRAGMENT_ID = "entailment.query.v1"


class Relation(str, Enum):
    ENTAILS = "entails"
    CONTRADICTS = "contradicts"
    INDEPENDENT = "independent"
    UNKNOWN = "unknown"  # proposition not in fragment inventory


@dataclass(frozen=True)
class EntailmentAnswer:
    relation: Relation
    premise: str
    conclusion: str
    fragment_id: str = FRAGMENT_ID
    evidence: tuple[str, ...] = ()
    world_mutations: int = 0  # must remain 0 on this path


# Closed inventory: edges are (premise, conclusion) → ENTAILS or CONTRADICTS.
# Symmetric contradiction is stored once and checked both ways.
_ENTAILS: frozenset[tuple[str, str]] = frozenset(
    {
        ("all_birds_fly", "some_birds_fly"),
        ("marble_in_box", "marble_located"),
        ("chicken_golden", "chicken_has_trait"),
        ("setup_done", "story_started"),
        ("planted_feather", "chekhov_open"),
        ("discharged_feather", "chekhov_closed"),
        ("p_and_q", "p"),
        ("p_and_q", "q"),
        ("forall_x_px", "pa"),
        ("rain_wet", "ground_wet_if_rain"),  # toy chain node
        ("sally_believes_basket", "sally_has_belief"),
        ("world_box", "world_has_location"),
        ("fiction_open", "frame_active"),
        ("agent_declared", "story_has_agent"),
        ("resolution_done", "three_beats_possible"),
    }
)

# Genuine contradictions only. World-box vs Sally-belief is NOT a
# contradiction (index-relative — see index_language / P-LS10).
_CONTRADICTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("marble_in_box", "marble_in_basket"),
        ("chicken_golden", "chicken_silver"),
        ("p", "not_p"),
        ("chekhov_open", "chekhov_closed"),
        ("agent_golden", "agent_silver"),
        ("obligation_open", "obligation_discharged"),
        ("frame_closed", "frame_accepts_beats"),
        ("day", "night"),
        ("wet", "dry"),
        ("true", "false"),
    }
)

_INVENTORY: frozenset[str] = frozenset(
    {a for a, _ in _ENTAILS}
    | {b for _, b in _ENTAILS}
    | {a for a, _ in _CONTRADICTS}
    | {b for _, b in _CONTRADICTS}
)


@dataclass
class WorldProbe:
    """Optional probe object; query path must not call mutate."""

    mutations: int = 0
    facts: set[str] = field(default_factory=set)

    def mutate(self, fact: str) -> None:
        self.mutations += 1
        self.facts.add(fact)


def query(
    premise: str,
    conclusion: str,
    world: WorldProbe | None = None,
) -> EntailmentAnswer:
    """Report relation without committing facts to ``world``.

    If ``world`` is supplied it is never mutated on this path (P-LS9 floor).
    """
    mutations_before = world.mutations if world is not None else 0
    if premise not in _INVENTORY or conclusion not in _INVENTORY:
        ans = EntailmentAnswer(
            Relation.UNKNOWN,
            premise,
            conclusion,
            evidence=("not_in_fragment_inventory",),
        )
    elif (premise, conclusion) in _ENTAILS:
        ans = EntailmentAnswer(
            Relation.ENTAILS,
            premise,
            conclusion,
            evidence=("closed_entailment_table",),
        )
    elif (premise, conclusion) in _CONTRADICTS or (
        conclusion,
        premise,
    ) in _CONTRADICTS:
        ans = EntailmentAnswer(
            Relation.CONTRADICTS,
            premise,
            conclusion,
            evidence=("closed_contradiction_table",),
        )
    else:
        ans = EntailmentAnswer(
            Relation.INDEPENDENT,
            premise,
            conclusion,
            evidence=("no_edge",),
        )
    if world is not None and world.mutations != mutations_before:
        raise RuntimeError("entailment query mutated world — P-LS9 violation")
    # Re-pack with explicit world_mutations=0
    return EntailmentAnswer(
        ans.relation,
        ans.premise,
        ans.conclusion,
        fragment_id=FRAGMENT_ID,
        evidence=ans.evidence,
        world_mutations=0,
    )


def registered_pairs() -> tuple[tuple[str, str, Relation], ...]:
    """N≥15 registered pairs for the test suite."""
    pairs: list[tuple[str, str, Relation]] = []
    for a, b in sorted(_ENTAILS):
        pairs.append((a, b, Relation.ENTAILS))
    for a, b in sorted(_CONTRADICTS):
        pairs.append((a, b, Relation.CONTRADICTS))
    # independents
    pairs.append(("all_birds_fly", "marble_in_box", Relation.INDEPENDENT))
    pairs.append(("setup_done", "day", Relation.INDEPENDENT))
    pairs.append(("fiction_open", "wet", Relation.INDEPENDENT))
    if len(pairs) < 15:
        raise RuntimeError(f"need N>=15 pairs, got {len(pairs)}")
    return tuple(pairs)
