#!/usr/bin/env python3
"""Candidate-side contract for the v0.14 exclusion seam.

These tests are about the ADMISSION RULE, not about any registered row.
Nothing here reads `experiments/when_to_ask_holdout.json`, resolves a
registered query, or asserts a Q1-Q6 outcome; the one-shot scorer owns all
of that.  What must hold before that run is narrower and checkable now: a
veto changes who may be selected, and changes nothing else.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from resolver import (  # noqa: E402
    ASK,
    BIND,
    PASS,
    GraphIndex,
    NegativeGrammarError,
    normalize_surface,
    requires_term,
    resolve,
    resolve_negative,
    resolve_words,
)

#: Enough ids that the document-frequency ceiling admits a word carried by
#: three nodes.  Only the first three carry postings; the rest exist so the
#: graph has a size, which is one of the things masking must not change.
FILLER = tuple(f"filler.node.{n:04d}" for n in range(1000))


def index_with(**overrides) -> GraphIndex:
    prose = {
        "area": ("geo.square", "geo.rectangle", "geo.triangle"),
        "polygon": ("geo.square", "geo.rectangle"),
        "quadrilateral": ("geo.square",),
    }
    base = dict(
        statement_ids=("geo.square", "geo.rectangle", "geo.triangle", *FILLER),
        corpus_of={
            "geo.square": "geometry.v1",
            "geo.rectangle": "geometry.v1",
            "geo.triangle": "geometry.v1",
            **{sid: "filler.v1" for sid in FILLER},
        },
        by_prose=prose,
        prose_df={word: len(ids) for word, ids in prose.items()},
        by_keyword={},
        keyword_df={},
        by_lexicon={},
        lexicon_df={},
        by_skeleton={},
        by_statement={},
        inventory={
            "geo.square": frozenset({"square", "area", "polygon", "quadrilateral"}),
            "geo.rectangle": frozenset({"rectangle", "area", "polygon"}),
            "geo.triangle": frozenset({"triangle", "area"}),
        },
    )
    base.update(overrides)
    return GraphIndex(**base)


class FrozenGrammar(unittest.TestCase):
    def test_one_marker_and_a_short_term_parse(self) -> None:
        plan = resolve_negative("polygon area without square", index_with())
        self.assertEqual(plan.positive, "polygon area")
        self.assertEqual(plan.term, "square")
        self.assertEqual(plan.required_tokens, ("square",))

    def test_surface_normalization_precedes_the_match(self) -> None:
        self.assertEqual(normalize_surface("  Polygon   AREA  "), "polygon area")
        plan = resolve_negative("Polygon  Area   WITHOUT   Square", index_with())
        self.assertEqual((plan.positive, plan.term), ("polygon area", "square"))

    def test_shapes_outside_the_rule_refuse_rather_than_normalize(self) -> None:
        for text in (
            "polygon area",                       # no marker
            "area without square without cube",   # two markers
            "area without, square",               # punctuation before TERM
            "area without square.",               # punctuation after TERM
            "area without one two three",         # TERM too long
            "without square",                     # no positive payload
            "the without and",                    # TERM reduces to nothing
        ):
            with self.subTest(text=text):
                with self.assertRaises(NegativeGrammarError):
                    resolve_negative(text, index_with())

    def test_a_second_marker_is_refused_even_beside_punctuation(self) -> None:
        with self.assertRaises(NegativeGrammarError):
            resolve_negative("area (without proof) without square", index_with())


class VetoInventory(unittest.TestCase):
    def test_a_node_is_vetoed_only_by_its_own_committed_words(self) -> None:
        index = index_with()
        plan = resolve_negative("polygon area without square", index)
        self.assertEqual(plan.veto_ids, ("geo.square",))
        self.assertTrue(requires_term(index, "geo.square", ("square",)))
        self.assertFalse(requires_term(index, "geo.rectangle", ("square",)))

    def test_both_tokens_of_a_two_word_term_must_be_present(self) -> None:
        index = index_with()
        self.assertEqual(
            resolve_negative("area without quadrilateral polygon", index).veto_ids,
            ("geo.square",),
        )
        self.assertEqual(
            resolve_negative("area without quadrilateral triangle", index).veto_ids,
            (),
        )

    def test_a_saturating_word_still_vetoes(self) -> None:
        """The df ceiling is a retrieval rule; an exclusion gets no exemption."""
        index = index_with()
        plan = resolve_negative("polygon quadrilateral without area", index)
        self.assertEqual(
            plan.veto_ids, ("geo.rectangle", "geo.square", "geo.triangle")
        )


class MaskedAdmission(unittest.TestCase):
    def test_a_lower_scored_survivor_wins_after_the_top_is_excluded(self) -> None:
        index = index_with()
        open_outcome = resolve("polygon quadrilateral area", index)
        self.assertEqual(open_outcome.kind, BIND)
        self.assertEqual(open_outcome.bound, "geo.square")
        # geo.square scores 3 and geo.rectangle 2; excluding the winner must
        # promote the survivor rather than delete the answer.
        plan = resolve_negative("polygon quadrilateral area without square", index)
        self.assertEqual(plan.outcome.kind, BIND)
        self.assertEqual(plan.outcome.bound, "geo.rectangle")

    def test_masking_the_last_owner_does_not_unknow_its_word(self) -> None:
        """`quadrilateral` is a word the corpus knows, admissible or not."""
        index = index_with()
        plan = resolve_negative(
            "polygon quadrilateral area without quadrilateral", index
        )
        self.assertEqual(plan.veto_ids, ("geo.square",))
        self.assertNotIn("appear nowhere in the corpus", plan.outcome.detail)
        self.assertEqual(plan.outcome.kind, BIND)
        self.assertEqual(plan.outcome.bound, "geo.rectangle")

    def test_unmasked_candidates_keep_their_scores_and_order(self) -> None:
        index = index_with()
        unmasked = resolve_words("polygon area", index)
        masked = resolve_words("polygon area", index, mask=frozenset({"geo.triangle"}))
        self.assertEqual(unmasked.kind, ASK)
        self.assertEqual(unmasked.candidates, ("geo.rectangle", "geo.square"))
        self.assertEqual(masked.candidates, ("geo.rectangle", "geo.square"))
        self.assertEqual(unmasked.detail, masked.detail)

    def test_graph_size_and_document_frequencies_are_untouched(self) -> None:
        index = index_with()
        before = (index.size, dict(index.prose_df), dict(index.by_prose))
        resolve_negative("polygon quadrilateral area without square", index)
        self.assertEqual((index.size, index.prose_df, index.by_prose), before)


class TerminalRefusal(unittest.TestCase):
    def test_an_exact_id_whose_only_reading_is_excluded_passes(self) -> None:
        index = index_with()
        outcome = resolve("geo.square", index, mask=frozenset({"geo.square"}))
        self.assertEqual(outcome.kind, PASS)
        self.assertTrue(outcome.terminal)
        self.assertEqual(outcome.candidates, ())

    def test_a_terminal_pass_never_falls_through_to_word_overlap(self) -> None:
        """The forbidden path: exact evidence excluded, then retried loosely."""
        index = index_with(
            by_prose={
                "area": ("geo.square", "geo.rectangle", "geo.triangle"),
                "polygon": ("geo.square", "geo.rectangle"),
                "quadrilateral": ("geo.square",),
                "geo": ("geo.rectangle",),
                "square": ("geo.rectangle",),
            },
            prose_df={
                "area": 3, "polygon": 2, "quadrilateral": 1, "geo": 1, "square": 1,
            },
        )
        # Unmasked, the literal id binds itself.
        self.assertEqual(resolve("geo.square", index).bound, "geo.square")
        # Masked, the word index would happily offer geo.rectangle instead.
        loose = resolve_words("geo.square", index, mask=frozenset({"geo.square"}))
        self.assertEqual(loose.kind, BIND)
        self.assertEqual(loose.bound, "geo.rectangle")
        # The chain must refuse rather than accept that consolation prize.
        outcome = resolve("geo.square", index, mask=frozenset({"geo.square"}))
        self.assertEqual(outcome.kind, PASS)
        self.assertEqual(outcome.resolver, "statement_id")

    def test_zero_survivors_pass_rather_than_manufacture_a_winner(self) -> None:
        index = index_with()
        plan = resolve_negative("polygon quadrilateral area without area", index)
        self.assertEqual(
            plan.veto_ids, ("geo.rectangle", "geo.square", "geo.triangle")
        )
        self.assertEqual(plan.outcome.kind, PASS)
        self.assertEqual(plan.outcome.candidates, ())


if __name__ == "__main__":
    unittest.main()
