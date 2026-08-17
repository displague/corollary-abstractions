#!/usr/bin/env python3
"""Every question the maintainer has typed at this prompt, as a regression.

These were found by a person sitting down and asking things, which is the
only way this surface gets exercised honestly. Several exposed real bugs —
a proof request answered with the quadratic formula, an expression that
parsed with `when` but not with `if`, resolution reporting `solved` for an
assertion it had merely matched words against.

Each is pinned here so a later change has to break a named case rather than
quietly regress behaviour nobody wrote down. When a new probe finds
something, it belongs in this file BEFORE the fix.

The assertions are deliberately about ROUTE and STATUS rather than exact
wording. Wording should be free to improve; where a question goes, and how
strong a claim the system makes about it, should not drift silently.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from harness import CoreSession, route_line  # noqa: E402


class Probes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.session = CoreSession.boot(REPO, offline=False)

    def verdict(self, line: str) -> dict:
        return route_line(REPO, self.session, line)

    # -- computation ----------------------------------------------------

    def test_square_under_a_supposed_binding(self) -> None:
        for line in (
            "suppose x=5, what is the square of x?",
            "when x=5, what is x ^ 2?",
            "what is x ^ 2 if x=5?",
        ):
            with self.subTest(line=line):
                verdict = self.verdict(line)
                self.assertEqual(verdict["route"], "evaluate")
                self.assertEqual(verdict["status"], "solved")
                self.assertIn("25", verdict["detail"])

    def test_a_typed_relation_is_decided(self) -> None:
        verdict = self.verdict("does 2+2=4?")
        self.assertEqual(verdict["route"], "evaluate")
        self.assertIn("yes", verdict["detail"])

    def test_a_false_relation_is_decided_false(self) -> None:
        verdict = self.verdict("does 2+2=5?")
        self.assertEqual(verdict["route"], "evaluate")
        self.assertIn("no", verdict["detail"])

    # -- corpus lookup ---------------------------------------------------

    def test_explain_and_tell_me_about_reach_the_corpus(self) -> None:
        for line in (
            "explain goedel's theorem",
            "what is the cosine of a double angle",
            "tell me about the chain rule",
        ):
            with self.subTest(line=line):
                verdict = self.verdict(line)
                self.assertEqual(verdict["route"], "resolver")
                self.assertIn(verdict["status"], {"found", "waiting"})
                self.assertTrue(verdict.get("answer"))

    def test_a_proof_request_is_not_answered_with_an_unrelated_formula(self) -> None:
        """Regression: this bound confidently to the quadratic formula.

        Since exact relations became decidable, `prove that 2 + 2 = 4` is
        answered by ARITHMETIC. That is honest and useful, and it is not a
        proof — the project's standing rule is that a passing check
        certifies what it checks. So the requirement is not "never answer",
        it is: never claim to have proven, and disclose that the answer came
        from arithmetic rather than from the corpus.
        """
        verdict = self.verdict("prove that 2 + 2 = 4")
        self.assertNotIn(verdict["status"], {"verified", "proven"})
        body = "\n".join(verdict.get("answer", []))
        if verdict["route"] == "evaluate":
            self.assertIn("arithmetic", body)
            self.assertNotIn("proof", body.lower())
        else:
            self.assertNotEqual(verdict["status"], "solved")

    def test_an_assertion_is_not_agreed_with(self) -> None:
        """`solved` would read as confirmation; resolution only locates."""
        verdict = self.verdict(
            "the corpus contains a proof of the Riemann hypothesis"
        )
        self.assertNotIn(verdict["status"], {"solved", "verified", "proven"})

    # -- belief ----------------------------------------------------------

    def test_the_dotty_probe(self) -> None:
        verdict = self.verdict(
            "dotty sees bob walk into the room. bob is in the kitchen. "
            "dotty knows the room is the kitchen. Where does dotty think bob is?"
        )
        self.assertEqual(verdict["route"], "belief")
        self.assertIn("kitchen", verdict["detail"])

    def test_false_belief_reports_the_belief(self) -> None:
        verdict = self.verdict(
            "dotty sees bob walk into the room. bob moves to the garden. "
            "Where does dotty think bob is?"
        )
        self.assertEqual(verdict["route"], "belief")
        self.assertIn("room", verdict["detail"])
        self.assertNotIn("garden", verdict["detail"])

    # -- conjecture and refusal ------------------------------------------

    def test_a_supposition_is_held_not_answered(self) -> None:
        verdict = self.verdict("suppose the earth is round. is the earth round?")
        self.assertEqual(verdict["route"], "supposition")
        self.assertNotIn(verdict["status"], {"solved", "verified", "proven"})

    def test_a_definitional_question_reaches_the_dictionary(self) -> None:
        """Only when a definition was asked for.

        An earlier version fired on any line containing a dictionary word,
        so "tell me a story about a chicken" was answered by DEFINING
        chicken — a non-sequitur dressed as an answer. Skipped when the
        pinned archive is absent rather than passing on an empty index.
        """
        from gloss import archive_path  # noqa: PLC0415

        if archive_path() is None:
            self.skipTest("COROLLARY_WORDNET not set")
        for line, word in (
            ("what is a chicken?", "chicken"),
            ("explain what an egg is from the perspective of a bird", "egg"),
        ):
            with self.subTest(line=line):
                verdict = self.verdict(line)
                self.assertEqual(verdict["route"], "gloss")
                self.assertIn(word, verdict["detail"])
                self.assertIn(
                    "not a statement in this corpus",
                    "\n".join(verdict["answer"]),
                )

    def test_a_story_request_is_answered_by_the_verified_story(self) -> None:
        """This abstained for all of v0.13 on a false premise.

        Telling a story was said to require authoring or generating. The
        repo has had a golden-chicken frame and a StoryFrameVerifier since
        v0.8; nothing had let a person reach them.
        """
        verdict = self.verdict("tell me a story about a chicken")
        self.assertEqual(verdict["route"], "story")
        body = "\n".join(verdict["answer"])
        self.assertIn("golden chicken", body)
        self.assertIn("Chekhov", body)
        self.assertNotIn(verdict["status"], {"solved", "verified", "proven"})

    def test_out_of_corpus_questions_abstain_and_offer_a_frame(self) -> None:
        for line in (
            "how many continents are on planet earth?",
            "book me a flight to lisbon next friday",
        ):
            with self.subTest(line=line):
                verdict = self.verdict(line)
                self.assertEqual(verdict["route"], "dispatcher")
                self.assertEqual(verdict["status"], "exhausted")
                self.assertIn(
                    "suppose", "\n".join(verdict.get("answer", []))
                )


class BootReportsWhatIsInstalled(unittest.TestCase):
    def test_detection_is_not_forced_offline(self) -> None:
        """The CLI reported three subsystems OFF on a machine that had them.

        `offline=True` is for reproducing an absent box, and it had leaked
        into the default boot.
        """
        detected = CoreSession.boot(REPO, offline=False)
        forced = CoreSession.boot(REPO, offline=True)
        self.assertGreaterEqual(
            len(detected.matrix.registered_ids()),
            len(forced.matrix.registered_ids()),
        )

    def test_forced_offline_still_available_for_reproduction(self) -> None:
        forced = CoreSession.boot(REPO, offline=True)
        for optional in ("retrieve.wordnet", "prover.lean_live", "tool.torch"):
            self.assertNotIn(optional, forced.matrix.registered_ids())


if __name__ == "__main__":
    unittest.main()
