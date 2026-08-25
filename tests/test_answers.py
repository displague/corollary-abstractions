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
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import _realization_lexicon as lexicon  # noqa: E402
from answer import compose, records  # noqa: E402
from answer import render as render_answer  # noqa: E402
from realization_lexicon import load as load_lexicon  # noqa: E402
from realize_term import realize, surface_words_are_covered  # noqa: E402
from supposition import render as render_supposition  # noqa: E402
from supposition import suppose  # noqa: E402

CURATED = "trigonometry.identities.double_angle_cosine"
INGESTED = "leanworkbook.skel.lean_workbook_49137"

#: A curated node whose `canonical_ascii` parses and round-trips, so the
#: `in words` line is served (DESIGN-sans-template-rendering §5).
REALIZED = "algtop.homology.betti_alternating_sum"

#: An INGESTED node that also round-trips — the case where the provenance
#: disclaimer and the realized sentence must coexist.
REALIZED_INGESTED = "leanworkbook.ground.lean_workbook_13563"

#: One of exactly two nodes in the committed corpus that parse and are then
#: refused (`experiments/realization_rate.json`, `r1.lost_is_zero`): its
#: literals are 76 digits long, past the registered numeral domain. Named
#: from the run's exhaustive refusal list rather than invented, so a term
#: that stopped refusing would surface here as a failure.
NUMERAL_REFUSAL = "leanworkbook.ground.lean_workbook_37421"


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


def in_words_line(statement_id: str) -> str | None:
    """The rendered `in words` line for one statement, or None if absent."""

    lines = [
        line
        for line in render_answer(compose(statement_id))
        if line.startswith("in words")
    ]
    return lines[0] if lines else None


class TheRealizedSentence(unittest.TestCase):
    """`in words`, and the gate that decides whether it exists at all.

    The line is the one thing a reference entry says that is not copied from
    the corpus, so it is the one thing here that needs its own guarantees:
    it appears only behind an EXACT round trip (R3), every word in it traces
    to the lexicon or the registered numeral pair (R2), and the same term
    renders the same bytes every time (R5).
    """

    def test_a_round_tripping_term_is_rendered_in_words(self) -> None:
        answer = compose(REALIZED)
        receipt = realize(answer.formal, lexicon(), REALIZED)
        # The receipt is what licenses the line; assert it passed, then that
        # the line is exactly its surface.
        self.assertEqual(receipt.round_trip, "EXACT")
        self.assertTrue(receipt.served)
        self.assertEqual(in_words_line(REALIZED), f"in words   : {receipt.surface}")

    def test_the_line_sits_under_the_term_it_realizes(self) -> None:
        rendered = render_answer(compose(REALIZED))
        formal = next(i for i, l in enumerate(rendered) if l.startswith("formally"))
        self.assertEqual(rendered[formal + 1][:8], "in words")

    def test_the_label_column_matches_the_files_convention(self) -> None:
        """Eleven characters, then the colon — like every other label here."""

        rendered = render_answer(compose(REALIZED))
        labelled = [
            line for line in rendered
            if len(line) > 11 and line[11] == ":" and not line.startswith(" ")
        ]
        self.assertIn(in_words_line(REALIZED), labelled)
        for line in labelled:
            self.assertEqual(line[10:13], " : ", line)

    def test_a_refused_term_is_rendered_without_the_line(self) -> None:
        """R3: refusal at the surface is ABSENCE — no error text, no hedge."""

        answer = compose(NUMERAL_REFUSAL)
        receipt = realize(answer.formal, lexicon(), NUMERAL_REFUSAL)
        self.assertFalse(receipt.served)
        self.assertEqual(receipt.round_trip, "REFUSED")
        self.assertEqual(receipt.reason, "unsupported_numeral")
        rendered = "\n".join(render_answer(answer))
        self.assertIsNone(in_words_line(NUMERAL_REFUSAL))
        # Absence, not an explanation of the absence.
        for leak in ("REFUSED", "unsupported_numeral", "refus", "cannot"):
            self.assertNotIn(leak, rendered)
        # And the rest of the entry is undisturbed.
        self.assertIn(f"formally   : {answer.formal}", rendered)

    def test_the_ingestion_disclaimer_coexists_with_the_realized_sentence(self):
        """Both are true of the same node, so both are said."""

        answer = compose(REALIZED_INGESTED)
        self.assertFalse(answer.prose_is_authored)
        rendered = "\n".join(render_answer(answer))
        self.assertIn("ingestion record", rendered)
        self.assertIsNotNone(in_words_line(REALIZED_INGESTED))

    def test_the_disclaimer_is_unchanged_where_no_sentence_is_served(self):
        answer = compose(NUMERAL_REFUSAL)
        self.assertFalse(answer.prose_is_authored)
        self.assertIn(
            "note       : this text is an ingestion record, not an "
            "explanation a person wrote",
            render_answer(answer),
        )

    def test_R2_every_word_traces_to_the_lexicon_or_the_numeral_pair(self):
        """The renderer still authors nothing: it translates under a table."""

        checked = 0
        for statement_id in (REALIZED, REALIZED_INGESTED):
            line = in_words_line(statement_id)
            self.assertIsNotNone(line, statement_id)
            surface = line.split(": ", 1)[1]
            self.assertTrue(
                surface_words_are_covered(surface, lexicon()),
                f"{statement_id}: a word outside the lexicon and the numerals",
            )
            checked += 1
        self.assertGreater(checked, 0, "vacuous: nothing was checked")

    def test_R5_the_same_term_renders_the_same_bytes(self) -> None:
        first = in_words_line(REALIZED)
        for _ in range(3):
            self.assertEqual(in_words_line(REALIZED), first)
        # And through a freshly loaded table, not just the cached one.
        answer = compose(REALIZED)
        reloaded = realize(answer.formal, load_lexicon(), REALIZED)
        self.assertEqual(f"in words   : {reloaded.surface}", first)

    def test_a_term_that_does_not_parse_is_simply_absent(self) -> None:
        """The 83% case: most canonical_ascii does not parse, and says nothing."""

        answer = compose("logic.boolean_laws.de_morgan_laws")
        receipt = realize(answer.formal, lexicon(), answer.statement_id)
        self.assertFalse(receipt.served)
        self.assertIsNone(in_words_line(answer.statement_id))


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


class TheForeignVoiceLineArmsFromEvidence(unittest.TestCase):
    """4d's ARMED branch, which had no test at all (adversarial review, M2).

    Nothing could reach it: `_foreign_voice_armed` read the real repository
    root, the arming artifact does not exist there, and so the branch that
    emits the line was unreachable from any test. A branch nothing can reach
    is a branch nobody has checked — which is exactly what the review found.
    `repo_root` is now a parameter (production still passes nothing and gets
    the cached default-root answer), so a fixture artifact can arm it.

    The statement below is chosen because v0.18's realizer REFUSES it and the
    foreign renderer serves it — the only shape where the foreign line is
    reachable at all, since `render` tries the foreign voice only where the
    committed realizer produced nothing.
    """

    #: v0.18 refuses this (its canonical_ascii does not parse under the
    #: template parser); the foreign register renders it.
    FOREIGN_ONLY = "leanworkbook.skel.lean_workbook_10049"

    CLEARED_RUN = {
        "verdicts": {"overall": "FIRES", "voided": ["C-V3′"],
                     "summary": "floors met; C-V3' voided without blocking"},
        "c_g1": {"voided": False, "named_floor_met": True},
        "c_v4_prime": {"voided": False, "voided_classes": []},
        "b1": {"floor_met": True},
        "b3": {"closes_exactly": True},
        "b5": {"byte_identical": True},
    }

    def setUp(self) -> None:
        import answer as answer_module

        self.answer_module = answer_module
        answer_module._foreign_voice_armed.cache_clear()

    def tearDown(self) -> None:
        self.answer_module._foreign_voice_armed.cache_clear()

    def _root_with(self, run: dict | None) -> str:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        (root / "experiments").mkdir()
        if run is not None:
            (root / "experiments" / "foreign_voice_rate2.json").write_text(
                json.dumps(run), encoding="utf-8")
        return root

    def test_the_statement_is_one_only_the_foreign_voice_can_speak(self):
        """Guards the fixture: if v0.18 ever speaks for it, this test is vacuous."""
        from realize_term import realize

        composed = compose(self.FOREIGN_ONLY)
        self.assertIsNotNone(composed, self.FOREIGN_ONLY)
        self.assertFalse(
            realize(composed.formal, lexicon(), self.FOREIGN_ONLY).served,
            "v0.18's realizer now serves this, so the foreign branch is "
            "unreachable through it and this fixture must be re-chosen",
        )

    def test_an_armed_run_emits_the_foreign_line(self) -> None:
        root = self._root_with(self.CLEARED_RUN)
        try:
            composed = compose(self.FOREIGN_ONLY)
            surface = self.answer_module._foreign_in_words(
                composed.formal, self.FOREIGN_ONLY, repo_root=root)
            self.assertIsNotNone(surface, "the armed branch emitted nothing")
            self.assertTrue(surface.strip())
            # It is the foreign renderer's own surface, not a paraphrase.
            import foreign_voice

            self.assertEqual(
                surface,
                foreign_voice.render(
                    composed.formal, statement_id=self.FOREIGN_ONLY).surface,
            )
        finally:
            self._tmp.cleanup()

    def test_a_blocking_void_leaves_the_line_absent(self) -> None:
        blocked = json.loads(json.dumps(self.CLEARED_RUN))
        blocked["c_v4_prime"] = {"voided": True, "voided_classes": ["drop_group"]}
        root = self._root_with(blocked)
        try:
            composed = compose(self.FOREIGN_ONLY)
            self.assertIsNone(
                self.answer_module._foreign_in_words(
                    composed.formal, self.FOREIGN_ONLY, repo_root=root),
                "a blocking void must leave the surface dark",
            )
        finally:
            self._tmp.cleanup()

    def test_an_absent_run_leaves_the_line_absent(self) -> None:
        root = self._root_with(None)
        try:
            composed = compose(self.FOREIGN_ONLY)
            self.assertIsNone(
                self.answer_module._foreign_in_words(
                    composed.formal, self.FOREIGN_ONLY, repo_root=root))
        finally:
            self._tmp.cleanup()

    def test_a_malformed_run_fails_closed_rather_than_raising(self) -> None:
        """M1 at the served caller: answer.render must never propagate this."""
        for shape in ("[]", '"x"', '{"verdicts":"FIRES"}', "123", "{not json"):
            with self.subTest(shape=shape):
                self._tmp = tempfile.TemporaryDirectory()
                root = Path(self._tmp.name)
                (root / "experiments").mkdir()
                (root / "experiments" / "foreign_voice_rate2.json").write_text(
                    shape, encoding="utf-8")
                try:
                    composed = compose(self.FOREIGN_ONLY)
                    self.assertIsNone(
                        self.answer_module._foreign_in_words(
                            composed.formal, self.FOREIGN_ONLY, repo_root=root))
                finally:
                    self._tmp.cleanup()

    def test_production_state_and_served_line_agree(self) -> None:
        """Production behaviour, asserted beside the fixture behaviour.

        Written 2026-08-24 as `test_the_repository_as_it_stands_is_dark`,
        when the arming artifact did not exist; re-aimed 2026-08-25 at the
        merge that landed experiments/foreign_voice_rate2.json, because a
        test that hard-codes either state is a test that goes red the day
        the repository honestly changes state. The fixture tests above pin
        both branches; this one pins CONSISTENCY: the served line appears
        exactly when the arming read says it should.
        """
        armed = self.answer_module._foreign_voice_armed()
        rendered = "\n".join(render_answer(compose(self.FOREIGN_ONLY)))
        if armed:
            self.assertIn("in words", rendered)
        else:
            self.assertNotIn("in words", rendered)


if __name__ == "__main__":
    unittest.main()
