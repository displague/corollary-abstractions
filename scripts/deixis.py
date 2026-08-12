#!/usr/bin/env python3
"""Deixis as composition of owner / here / now (P-LS6) — not WordNet person.

Fragment: ``deixis.compose.v1``

Resolves a closed set of deictic tokens against an explicit index of
speaker, addressee, place, and time. Lexical person features alone never
suffice: without the index fields, resolution fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


FRAGMENT_ID = "deixis.compose.v1"


class DeicticToken(str, Enum):
    I = "i"
    YOU = "you"
    HERE = "here"
    NOW = "now"


@dataclass(frozen=True)
class DeicticIndex:
    """Named indices — the composition substrate for deixis."""

    speaker_id: str
    addressee_id: str
    here_id: str
    now_id: str

    def __post_init__(self) -> None:
        for field_name in ("speaker_id", "addressee_id", "here_id", "now_id"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")


def resolve_deictic(
    token: DeicticToken | str,
    index: DeicticIndex | None,
) -> str | None:
    """Map deictic token to an index id, or None if index missing/unknown token.

    WordNet (or any lexicon) is intentionally not consulted.
    """
    if index is None:
        return None
    if isinstance(token, str):
        key = token.strip().casefold()
        try:
            token = DeicticToken(key)
        except ValueError:
            return None
    if token is DeicticToken.I:
        return index.speaker_id
    if token is DeicticToken.YOU:
        return index.addressee_id
    if token is DeicticToken.HERE:
        return index.here_id
    if token is DeicticToken.NOW:
        return index.now_id
    return None


def resolve_dialogue_turn(
    tokens: tuple[str, ...],
    index: DeicticIndex,
) -> dict[str, str | None]:
    """Resolve each token independently against the same index."""
    return {tok: resolve_deictic(tok, index) for tok in tokens}
