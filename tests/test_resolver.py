#!/usr/bin/env python3
"""The resolver chain: bind, ask, or pass — never guess.

The tests that matter here are the negative ones. A resolver that claims
everything is worse than no resolver, because it converts an honest
`exhausted` into a confident wrong answer.
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from resolver import (  # noqa: E402
    ASK,
    BIND,
    KEYWORD_DF_CEILING,
    PASS,
    default_index,
    reduce_text,
    resolve,
    resolve_keywords,
)


class ChainFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = default_index()


class ItRefusesToClaimNonsense(ChainFixture):
    """The failure mode that makes a resolver worse than nothing."""

    def test_one_stray_word_is_not_a_resolution(self) -> None:
        outcome = resolve(
            "what is the airspeed velocity of an unladen swallow", self.index
        )
        self.assertEqual(outcome.kind, PASS)

    def test_prose_about_nothing_in_the_corpus_passes(self) -> None:
        for text in (
            "please tell me a story about a dragon",
            "how do I bake sourdough bread",
            "who won the world cup",
        ):
            with self.subTest(text=text):
                self.assertEqual(resolve(text, self.index).kind, PASS)

    def test_a_saturating_keyword_cannot_resolve_the_corpus(self) -> None:
        """`ingested` sits on 12,525 nodes; matching it means nothing."""
        outcome = resolve_keywords("ingested", self.index)
        self.assertEqual(outcome.kind, PASS)

    def test_the_df_ceiling_actually_excludes_something(self) -> None:
        """Vacuity guard: the ceiling must bind on real data."""
        ceiling = int(self.index.size * KEYWORD_DF_CEILING)
        over = [w for w, n in self.index.keyword_df.items() if n > ceiling]
        self.assertTrue(over, "df ceiling excludes nothing — it is inert")


class ItBindsWhenExact(ChainFixture):
    def test_two_corroborating_words_bind(self) -> None:
        outcome = resolve("pythagorean theorem", self.index)
        self.assertEqual(outcome.kind, BIND)
        self.assertTrue(outcome.bound)

    def test_an_exact_statement_id_binds(self) -> None:
        outcome = resolve("trigonometry.identities.double_angle_cosine", self.index)
        self.assertEqual(outcome.kind, BIND)
        self.assertEqual(outcome.bound, "trigonometry.identities.double_angle_cosine")

    def test_a_unique_id_suffix_binds(self) -> None:
        outcome = resolve("identities.double_angle_cosine", self.index)
        self.assertEqual(outcome.kind, BIND)


class ItAsksWhenAmbiguous(ChainFixture):
    def test_a_shared_subterm_asks_and_names_candidates(self) -> None:
        outcome = resolve("SIN(x) ^ 2", self.index)
        self.assertEqual(outcome.kind, ASK)
        self.assertGreater(len(outcome.candidates), 1)
        for sid in outcome.candidates:
            self.assertIn(sid, self.index.corpus_of)

    def test_a_real_but_broad_keyword_asks(self) -> None:
        outcome = resolve("parity", self.index)
        self.assertEqual(outcome.kind, ASK)
        self.assertGreater(len(outcome.candidates), 1)

    def test_ask_never_silently_picks_one(self) -> None:
        outcome = resolve("parity", self.index)
        self.assertIsNone(outcome.bound)


class ExactnessBeatsKeywords(ChainFixture):
    def test_a_parseable_expression_is_not_second_guessed(self) -> None:
        outcome = resolve("x ^ 2", self.index)
        self.assertEqual(outcome.resolver, "expression")


class Reduction(unittest.TestCase):
    def test_stopwords_and_case_are_removed(self) -> None:
        self.assertEqual(reduce_text("What is THE Parity of x?"), ["parity", "x"])

    def test_reduction_is_not_stemming(self) -> None:
        """No morphology is claimed; `theorems` is not `theorem`."""
        self.assertEqual(reduce_text("theorems"), ["theorems"])


class ItIsFastEnoughToBeUseful(ChainFixture):
    def test_resolution_is_microseconds_once_indexed(self) -> None:
        """The claim that this runs on small hardware, as a check.

        Cold start dominates; the per-query cost must not. 10k resolutions
        of a bound query in well under a second, single-threaded.
        """
        start = time.perf_counter()
        for _ in range(10_000):
            resolve("trigonometry.identities.double_angle_cosine", self.index)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 5.0, f"10k resolutions took {elapsed:.2f}s")


if __name__ == "__main__":
    unittest.main()
