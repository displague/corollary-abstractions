"""P-LS4: preference features are pure, registered, unit-tested; no OOV."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from preference import (  # noqa: E402
    FRAGMENT_ID,
    REGISTERED_FEATURES,
    DiscourseSnapshot,
    FeatureFrequency,
    FeatureLength,
    FeatureTopicTagMatch,
    RealizationCandidate,
    frequency_baseline,
    rank_candidates,
)


def _cands() -> tuple[RealizationCandidate, ...]:
    # Same denotation_key — packaging variants only.
    return (
        RealizationCandidate("long", "the quite very long form of hello", "greet"),
        RealizationCandidate("mid", "hello there", "greet", pattern_id="mid_pat"),
        RealizationCandidate("short", "hi", "greet", pattern_id="short_pat"),
    )


class PreferenceRegistryTests(unittest.TestCase):
    def test_registered_feature_names_match_implementations(self) -> None:
        self.assertEqual(
            set(REGISTERED_FEATURES),
            {"length", "frequency", "topic_tag_match"},
        )
        self.assertEqual(FRAGMENT_ID, "preference.shallow.v1")

    def test_length_feature_is_deterministic(self) -> None:
        cands = _cands()
        feat = FeatureLength()
        a = feat.scores(cands)
        b = feat.scores(cands)
        self.assertEqual(dict(a), dict(b))
        ordered = rank_candidates(cands, (feat,))
        self.assertEqual(ordered[0], "short")
        self.assertEqual(set(ordered), {c.candidate_id for c in cands})

    def test_frequency_baseline_and_feature(self) -> None:
        cands = _cands()
        counts = {"short_pat": 10, "mid_pat": 3}
        ordered = frequency_baseline(cands, counts)
        self.assertEqual(ordered[0], "short")
        self.assertEqual(set(ordered), {c.candidate_id for c in cands})

    def test_topic_tag_match_uses_discourse_snapshot_only(self) -> None:
        cands = _cands()
        feat = FeatureTopicTagMatch()
        cold = feat.scores(cands, DiscourseSnapshot(topic_tag=""))
        self.assertTrue(all(v == 0.0 for v in cold.values()))
        hot = feat.scores(cands, DiscourseSnapshot(topic_tag="short_pat"))
        self.assertEqual(hot["short"], 1.0)
        self.assertEqual(hot["mid"], 0.0)

    def test_rank_refuses_unregistered_feature_name(self) -> None:
        class Bogus:
            name = "coherence_llm"

            def scores(self, candidates, discourse=None):
                return {c.candidate_id: 0.0 for c in candidates}

        with self.assertRaises(ValueError) as ctx:
            rank_candidates(_cands(), (Bogus(),))  # type: ignore[arg-type]
        self.assertIn("unregistered", str(ctx.exception))

    def test_feature_must_score_exact_candidate_set(self) -> None:
        class Leak:
            name = "length"

            def scores(self, candidates, discourse=None):
                return {"ghost": 1.0}

        with self.assertRaises(ValueError):
            rank_candidates(_cands(), (Leak(),))  # type: ignore[arg-type]

    def test_suite_n_ge_30_fixed_sets(self) -> None:
        """Registered suite: N≥30 items, K≥3 candidates, 0 OOV."""
        counts = {"p0": 5, "p1": 2, "p2": 1}
        for i in range(30):
            cands = tuple(
                RealizationCandidate(
                    f"c{j}",
                    text=("x" * (10 - j)) + f"-{i}",
                    denotation_key=f"den{i}",
                    pattern_id=f"p{j}",
                )
                for j in range(3)
            )
            ordered = rank_candidates(
                cands,
                (FeatureLength(), FeatureFrequency(counts)),
            )
            self.assertEqual(len(ordered), 3)
            self.assertEqual(set(ordered), {c.candidate_id for c in cands})


if __name__ == "__main__":
    unittest.main()
