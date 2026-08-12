#!/usr/bin/env python3
"""Minimal discourse / common-ground store (P-LS7 first cut).

Fragment: ``discourse.entities.v1``

Holds introduced entities with a simple salience stack and resolves a tiny
closed set of anaphors (``it``, ``that``, ``he``, ``she``, ``they``) to the
most salient compatible entity. No open NLU: unknown anaphors and empty
stores fail closed (None / REFUSED-style callers).

This is not a full QUD/grounding dialogue model. It is the smallest state
that makes multi-turn reference *load-bearing*: wipe the store and
resolution must fail.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


FRAGMENT_ID = "discourse.entities.v1"


class Anaphor(str, Enum):
    IT = "it"
    THAT = "that"
    HE = "he"
    SHE = "she"
    THEY = "they"


# Coarse gender/animacy features for the toy fragment (hard constraints).
class EntityKind(str, Enum):
    NEUTER = "neuter"  # it / that
    MASC = "masc"  # he
    FEM = "fem"  # she
    PLURAL = "plural"  # they


_ANAPHOR_KIND: dict[Anaphor, EntityKind] = {
    Anaphor.IT: EntityKind.NEUTER,
    Anaphor.THAT: EntityKind.NEUTER,
    Anaphor.HE: EntityKind.MASC,
    Anaphor.SHE: EntityKind.FEM,
    Anaphor.THEY: EntityKind.PLURAL,
}


@dataclass(frozen=True)
class DiscourseEntity:
    entity_id: str
    kind: EntityKind
    surfaces: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id must be non-empty")


@dataclass(frozen=True)
class DiscourseState:
    """Immutable discourse snapshot; updates return a new state."""

    entities: tuple[DiscourseEntity, ...] = ()
    # Most-salient last (stack): resolve walks reverse.
    salience: tuple[str, ...] = ()
    fragment_id: str = FRAGMENT_ID

    def introduce(self, entity: DiscourseEntity) -> "DiscourseState":
        """Register entity and make it most salient (re-intro moves to top)."""
        others = tuple(e for e in self.entities if e.entity_id != entity.entity_id)
        sal = tuple(i for i in self.salience if i != entity.entity_id) + (
            entity.entity_id,
        )
        return DiscourseState(entities=others + (entity,), salience=sal)

    def _by_id(self, entity_id: str) -> DiscourseEntity | None:
        for entity in self.entities:
            if entity.entity_id == entity_id:
                return entity
        return None

    def resolve(self, anaphor: Anaphor | str) -> DiscourseEntity | None:
        """Most salient entity compatible with the anaphor; None if none."""
        if isinstance(anaphor, str):
            key = anaphor.strip().casefold()
            try:
                anaphor = Anaphor(key)
            except ValueError:
                return None
        want = _ANAPHOR_KIND[anaphor]
        for entity_id in reversed(self.salience):
            entity = self._by_id(entity_id)
            if entity is not None and entity.kind is want:
                return entity
        return None

    def wipe(self) -> "DiscourseState":
        """Ablation: empty store (P-LS7 negative control)."""
        return DiscourseState()
