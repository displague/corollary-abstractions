#!/usr/bin/env python3
"""Closed-form key canonicalisation, token matching, and relevance scoring.

Extracted from ``retrieval.py`` so that external source adapters can match on
exactly the same closed forms the five committed stores use, without importing
the retrieval verifier (and without a second, drifting copy of the rules).
``retrieval`` re-exports :func:`exact_key` and :func:`query_tokens` so existing
importers are unaffected.

Nothing here is learned. Every function is a pure function of its arguments,
which is what lets a relevance score be *announced* rather than trusted.
"""

from __future__ import annotations

import re


_TOKEN = re.compile(r"[a-z0-9]+")
_WHITESPACE = re.compile(r"\s+")

#: Shortest token that may participate in a prefix (rather than equality)
#: match. Below this the prefix relation is too weak to be evidence: a
#: one-letter query would otherwise "cover" every alias that starts with it.
MIN_PREFIX_LENGTH = 3


def exact_key(value: str) -> str:
    """Canonical equality key that preserves closed-form operators."""

    return _WHITESPACE.sub(" ", value.strip().casefold())


def query_tokens(value: str) -> tuple[str, ...]:
    """Canonical closed-form query tokens."""

    return tuple(_TOKEN.findall(value.casefold()))


def token_covers(query_token: str, candidate: str) -> bool:
    """Closed-form token relation used by neighborhood matching.

    ``query_token`` covers ``candidate`` when they are equal, or when either
    is a prefix of the other and the *shorter* side is at least
    :data:`MIN_PREFIX_LENGTH` characters. The length guard is the existing
    anti-reverse-match rule (``tests/test_retrieval.py::
    test_short_nonexact_key_cannot_prefix_match_a_long_alias``), kept here so
    every consumer inherits it instead of re-deriving it.
    """

    if query_token == candidate:
        return True
    if len(query_token) >= MIN_PREFIX_LENGTH and candidate.startswith(query_token):
        return True
    return len(candidate) >= MIN_PREFIX_LENGTH and query_token.startswith(candidate)


def alias_covered(tokens: tuple[str, ...], alias_tokens: tuple[str, ...]) -> bool:
    """True when every query token is covered by some alias token."""

    return all(
        any(token_covers(token, candidate) for candidate in alias_tokens)
        for token in tokens
    )


def overlap_score(key: str, alias: str) -> float:
    """Deterministic relevance of one alias to one key, in ``[0.0, 1.0]``.

    Closed form, stated so a caller can recompute it:

    ``score = (query_coverage + alias_coverage + exact_share) / 3`` where, over
    the de-duplicated token sequences ``Q`` (from ``key``) and ``A`` (from
    ``alias``) and the :func:`token_covers` relation,

    * ``query_coverage = |{t in Q : t covers some a in A}| / |Q|`` — how much of
      the question the alias answers;
    * ``alias_coverage = |{a in A : some t in Q covers a}| / |A|`` — how much of
      the alias the question actually used, which is what separates a tight
      match from a long title that happens to contain the query;
    * ``exact_share = |{t in Q : t in A}| / |Q|`` — the share matched by token
      equality rather than by the weaker prefix relation.

    Each component is a ratio of small integers, so the value is reproducible
    on any platform; it is rounded to six places for stable printing. The score
    is ``1.0`` exactly when ``Q`` and ``A`` are the same token set, and ``0.0``
    when either side has no tokens. It is a *relevance ordering*, not a
    probability, not a confidence, and never an epistemic status: ranking never
    moves a record's rung (see ``retrieval.RetrievalItem.epistemic_status``).
    """

    query = tuple(dict.fromkeys(query_tokens(key)))
    alias_side = tuple(dict.fromkeys(query_tokens(alias)))
    if not query or not alias_side:
        return 0.0
    matched_query = sum(
        1 for token in query if any(token_covers(token, a) for a in alias_side)
    )
    matched_alias = sum(
        1 for a in alias_side if any(token_covers(token, a) for token in query)
    )
    exact_hits = sum(1 for token in query if token in alias_side)
    total = (
        matched_query / len(query)
        + matched_alias / len(alias_side)
        + exact_hits / len(query)
    )
    return round(total / 3, 6)


SCORE_DEFINITION = (
    "mean(query_coverage, alias_coverage, exact_token_share) over the "
    "best-scoring alias; closed form, see scripts/text_keys.overlap_score"
)
