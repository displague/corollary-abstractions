#!/usr/bin/env python3
"""Answers are quotations; suppositions are conjecture. Neither is invented.

Two guarantees are worth more than any coverage number here:

- an answer's sentences appear verbatim in the committed corpus, so the
  renderer cannot author a claim;
- a supposition is never reported as a fact, so fiction cannot leak into the
  factual channel.

Both are asserted directly rather than inferred from behaviour.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import compose, records  # noqa: E402
from answer import render as render_answer  # noqa: E402
from supposition import render as render_supposition  # noqa: E402
from supposition import suppose  # noqa: E402

CURATED = "trigonometry.identities.double_angle_cosine"
INGESTED = "leanworkbook.skel.lean_workbook_49137"


class AnswersAreQuotations(unittest.TestCase):
    def test_every_sentence_appears_in_the_corpus(self) -> None:
        """The guarantee that makes 'factual' structural, not aspirational."""
        corpus = records()
        checked = 0
        for sid in (CURATED, INGESTED):
            answer = compose(sid)
            self.assertIsNotNone(answer, sid)
            blob = json.dumps(corpus[sid][0], ensure_ascii=False)
            for sentence in (answer.title, answer.meaning, answer.formal):
                if sentence:
                    self.assertIn(sentence, blob, f"{sid}: not verbatim")
                    checked += 1
        self.assertGreater(checked, 0, "vacuous: nothing was checked")

    def test_the_answer_names_its_source(self) -> None:
        rendered = "\n".join(render_answer(compose(CURATED)))
        self.assertIn(CURATED, rendered)

    def test_relations_come_from_committed_links(self) -> None:
        answer = compose(CURATED)
        self.assertTrue(answer.links)
        corpus = records()
        for _kind, target in answer.links:
            self.assertIn(target, corpus, "a relation points outside the graph")

    def test_ingested_prose_is_labelled_as_provenance(self) -> None:
        """12.5k nodes have machine-authored meanings; say so."""
        answer = compose(INGESTED)
        self.assertFalse(answer.prose_is_authored)
        self.assertIn("ingestion record", "\n".join(render_answer(answer)))

    def test_curated_prose_is_not_labelled_that_way(self) -> None:
        answer = compose(CURATED)
        self.assertTrue(answer.prose_is_authored)
        self.assertNotIn("ingestion record", "\n".join(render_answer(answer)))

    def test_unknown_statement_composes_nothing(self) -> None:
        self.assertIsNone(compose("no.such.statement"))


class SuppositionsAreConjecture(unittest.TestCase):
    def test_a_supposition_is_held_as_conjectured(self) -> None:
        held = suppose("the chicken crossed the road because it wanted to")
        self.assertEqual(held.status, "conjectured")

    def test_it_runs_in_a_runtime_frame_owned_by_the_person(self) -> None:
        held = suppose("cartoon gravity applies until you look down")
        self.assertTrue(held.frame.startswith("runtime.frames."))

    def test_negation_is_carried(self) -> None:
        self.assertFalse(suppose("not every gun is fired").polarity)
        self.assertTrue(suppose("every gun is fired").polarity)

    def test_it_never_claims_to_be_a_fact(self) -> None:
        rendered = "\n".join(
            render_supposition(suppose("the sea is made of ink"))
        ).lower()
        self.assertIn("not a corpus fact", rendered)
        for word in ("verified", "proven", "solved"):
            self.assertNotIn(word, rendered)

    def test_fiction_does_not_reach_the_factual_channel(self) -> None:
        """A supposition must not become answerable as a statement."""
        held = suppose("the chicken is a philosopher")
        self.assertIsNone(compose(held.claim))


if __name__ == "__main__":
    unittest.main()
