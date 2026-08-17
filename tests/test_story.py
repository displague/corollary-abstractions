#!/usr/bin/env python3
"""The story is held and checked, not invented.

The claim being defended is narrow: beats come from committed frame data,
the rendering is the committed v0.8 program, and the constraints are corpus
statements quoted verbatim. Nothing in `story.py` writes a sentence of
fiction, and these tests are what keep that true.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from story import (  # noqa: E402
    CONSTRAINT_IDS,
    constraint_prose,
    is_story_request,
    render,
    tell,
)


class TheStoryVerifies(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.told = tell()

    def test_it_reaches_a_complete_three_beat_story(self) -> None:
        roles = [role for role, _text in self.told.beats]
        self.assertEqual(roles, ["setup", "complication", "resolution"])

    def test_the_verifier_accepted_every_beat(self) -> None:
        self.assertTrue(self.told.solved)
        self.assertEqual(self.told.rejected, 0)

    def test_chekhov_is_actually_satisfied_not_merely_cited(self) -> None:
        """The planted element must reappear in the resolution.

        Without this the test would pass on a story that plants a feather
        and never uses it, while still printing the Chekhov rule.
        """
        beats = dict((role, text) for role, text in self.told.beats)
        self.assertIn("feather", beats["setup"])
        self.assertIn("feather", beats["resolution"])

    def test_the_desire_opened_is_the_desire_closed(self) -> None:
        self.assertTrue(self.told.desire)
        beats = dict((role, text) for role, text in self.told.beats)
        self.assertIn("sing", beats["setup"])
        self.assertIn("sang", beats["resolution"])


class TheRulesAreQuoted(unittest.TestCase):
    def test_every_constraint_resolves_to_a_committed_statement(self) -> None:
        prose = constraint_prose()
        self.assertEqual(set(prose), set(CONSTRAINT_IDS))

    def test_constraint_text_is_verbatim_from_the_corpus(self) -> None:
        corpus_blob = (
            REPO / "data" / "narrative" / "nodes.json"
        ).read_text(encoding="utf-8")
        parsed = json.loads(corpus_blob)
        by_id = {n["statement_id"]: n for n in parsed["statement_nodes"]}
        for sid, (title, meaning) in constraint_prose().items():
            self.assertEqual(title, by_id[sid]["title"])
            self.assertEqual(
                meaning,
                by_id[sid]["semantic_interpretation"]["statement_meaning"],
            )

    def test_the_answer_says_it_invents_nothing(self) -> None:
        rendered = "\n".join(render(tell(), constraint_prose()))
        self.assertIn("not written for this answer", rendered)
        self.assertIn("no other story is invented", rendered)


class RequestDetection(unittest.TestCase):
    def test_story_requests_are_recognised(self) -> None:
        for line in (
            "tell me a story about a chicken",
            "tell me a story",
            "write me a story about the sea",
            "story",
        ):
            with self.subTest(line=line):
                self.assertTrue(is_story_request(line))

    def test_other_text_is_not_a_story_request(self) -> None:
        for line in (
            "what is the cosine of a double angle",
            "the history of a story is long",
            "suppose x=5, what is x ^ 2",
            "where does dotty think bob is?",
        ):
            with self.subTest(line=line):
                self.assertFalse(is_story_request(line))


if __name__ == "__main__":
    unittest.main()
