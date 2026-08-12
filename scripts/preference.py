#!/usr/bin/env python3
"""Preference over index-admissible realizations (P-LS4).

Fragment: ``preference.shallow.v1``

Every ranking feature is a **deterministic pure function** registered here and
covered by unit tests. Features take a closed candidate set plus an optional
discourse snapshot and return per-candidate score keys. The ranker may only
**permute** candidate ids — it cannot invent text or change denotation keys.

Shallow features only (DESIGN-language-as-structure §5.3.5): length,
registered pattern id, frequency count, discourse topic-tag match. No free
"coherence understanding."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Protocol, Sequence


FRAGMENT_ID = "preference.shallow.v1"


@dataclass(frozen=True)
class RealizationCandidate:
    """One admissible realization; denotation_key is identity of meaning."""

    candidate_id: str
    text: str
    denotation_key: str
    pattern_id: str = ""

    def __post_init__(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must be non-empty")
        if not self.denotation_key.strip():
            raise ValueError("denotation_key must be non-empty")


@dataclass(frozen=True)
class DiscourseSnapshot:
    """Minimal discourse view for shallow features (not a second memory)."""

    topic_tag: str = ""
    salient_entity_id: str = ""


class PreferenceFeature(Protocol):
    name: str

    def scores(
        self,
        candidates: Sequence[RealizationCandidate],
        discourse: DiscourseSnapshot | None = None,
    ) -> Mapping[str, float]:
        """Higher is better. Keys must be exactly the candidate_ids."""


def _assert_closed(
    candidates: Sequence[RealizationCandidate],
    scores: Mapping[str, float],
    feature_name: str,
) -> None:
    ids = {c.candidate_id for c in candidates}
    keys = set(scores)
    if keys != ids:
        raise ValueError(
            f"feature {feature_name!r} must score exactly the candidate set; "
            f"missing={sorted(ids - keys)} extra={sorted(keys - ids)}"
        )


# ---------------------------------------------------------------------------
# Registered pure features (each must have a unit test)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FeatureLength:
    """Prefer shorter surface strings (negative length)."""

    name: str = "length"

    def scores(
        self,
        candidates: Sequence[RealizationCandidate],
        discourse: DiscourseSnapshot | None = None,
    ) -> Mapping[str, float]:
        del discourse
        out = {c.candidate_id: -float(len(c.text)) for c in candidates}
        _assert_closed(candidates, out, self.name)
        return out


@dataclass(frozen=True)
class FeatureFrequency:
    """Prefer patterns with higher count in a fixed table (training prior)."""

    counts: Mapping[str, int]
    name: str = "frequency"

    def scores(
        self,
        candidates: Sequence[RealizationCandidate],
        discourse: DiscourseSnapshot | None = None,
    ) -> Mapping[str, float]:
        del discourse
        out = {
            c.candidate_id: float(self.counts.get(c.pattern_id, 0))
            for c in candidates
        }
        _assert_closed(candidates, out, self.name)
        return out


@dataclass(frozen=True)
class FeatureTopicTagMatch:
    """+1 when pattern_id equals discourse.topic_tag (shallow tag match)."""

    name: str = "topic_tag_match"

    def scores(
        self,
        candidates: Sequence[RealizationCandidate],
        discourse: DiscourseSnapshot | None = None,
    ) -> Mapping[str, float]:
        tag = (discourse.topic_tag if discourse else "") or ""
        out = {
            c.candidate_id: 1.0 if tag and c.pattern_id == tag else 0.0
            for c in candidates
        }
        _assert_closed(candidates, out, self.name)
        return out


#: Closed registry — adding a feature without a test is a review miss.
REGISTERED_FEATURES: tuple[str, ...] = (
    "length",
    "frequency",
    "topic_tag_match",
)


def rank_candidates(
    candidates: Sequence[RealizationCandidate],
    features: Sequence[PreferenceFeature],
    discourse: DiscourseSnapshot | None = None,
    *,
    weights: Mapping[str, float] | None = None,
) -> tuple[str, ...]:
    """Return candidate_ids best-first. Never emits an id outside ``candidates``.

    Combined score is sum of weight[name] * feature.scores(...). Default weight 1.
    Ties broken by candidate_id for determinism.
    """
    if not candidates:
        return ()
    ids = [c.candidate_id for c in candidates]
    id_set = set(ids)
    # Denotation guard: all candidates in one rank call must share denotation
    # or be explicitly multi-denotation (caller responsibility). We only
    # refuse empty denotation (dataclass) and OOV emission.
    totals = {cid: 0.0 for cid in ids}
    for feat in features:
        if feat.name not in REGISTERED_FEATURES:
            raise ValueError(
                f"unregistered preference feature {feat.name!r}; "
                f"fragment {FRAGMENT_ID} admits {REGISTERED_FEATURES}"
            )
        part = feat.scores(candidates, discourse)
        _assert_closed(candidates, part, feat.name)
        w = 1.0 if weights is None else float(weights.get(feat.name, 1.0))
        for cid, value in part.items():
            totals[cid] += w * value
    ordered = sorted(ids, key=lambda cid: (-totals[cid], cid))
    if set(ordered) != id_set:
        raise RuntimeError("ranker produced OOV or dropped candidates")
    return tuple(ordered)


def frequency_baseline(
    candidates: Sequence[RealizationCandidate],
    counts: Mapping[str, int],
) -> tuple[str, ...]:
    """Capability-blind baseline: pattern frequency, then id."""
    return rank_candidates(candidates, (FeatureFrequency(counts),))
