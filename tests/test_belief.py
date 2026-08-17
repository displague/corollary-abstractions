#!/usr/bin/env python3
"""Belief is not the world, and the grammar admits how small it is.

The load-bearing test is the false-belief one. A system that reports where
something actually is, when asked where someone *thinks* it is, has not
modelled belief at all — it has modelled the narrator.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from belief import answer, read  # noqa: E402

DOTTY = (
    "dotty sees bob walk into the room. bob is in the kitchen. "
    "dotty knows the room is the kitchen. Where does dotty think bob is?"
)
FALSE_BELIEF = (
    "dotty sees bob walk into the room. bob moves to the garden. "
    "Where does dotty think bob is?"
)


class BeliefIsNotTheWorld(unittest.TestCase):
    def test_the_probe_resolves_through_a_known_equality(self) -> None:
        result = answer(DOTTY)
        self.assertEqual(result.place, "kitchen")
        self.assertEqual(result.agent, "dotty")
        self.assertEqual(result.subject, "bob")

    def test_false_belief_reports_the_belief_not_the_world(self) -> None:
        """Sally-Anne. The whole design is judged here."""
        result = answer(FALSE_BELIEF)
        self.assertEqual(result.place, "room")
        self.assertEqual(result.world_place, "garden")

    def test_the_disagreement_is_disclosed(self) -> None:
        from belief import render  # noqa: PLC0415

        rendered = "\n".join(render(answer(FALSE_BELIEF)))
        self.assertIn("garden", rendered)
        self.assertIn("divergence", rendered)
        # And the readout stays a readout: no authored prose about beliefs.
        self.assertIn("located_in(bob) = room", rendered)

    def test_world_facts_never_enter_an_agents_store(self) -> None:
        """The separation that makes the false-belief answer possible."""
        reading = read("bob is in the kitchen. dotty sees bob walk into the room")
        self.assertEqual(reading.world.located_in.get("bob"), "kitchen")
        self.assertEqual(reading.agents["dotty"].located_in.get("bob"), "room")

    def test_an_unobserved_subject_is_refused_not_guessed(self) -> None:
        result = answer(
            "bob is in the kitchen. Where does dotty think bob is?"
        )
        self.assertIsNone(result.place)
        self.assertTrue(
            any("no observation" in s or "no frame" in s for s in result.steps),
            result.steps,
        )

    def test_an_agent_who_saw_nothing_is_refused(self) -> None:
        result = answer("Where does nobody think bob is?")
        self.assertIsNone(result.place)


class TheGrammarAdmitsItsLimits(unittest.TestCase):
    def test_non_belief_text_returns_nothing(self) -> None:
        self.assertIsNone(answer("what is the cosine of a double angle"))
        self.assertIsNone(answer("suppose the earth is round"))

    def test_unreadable_sentences_are_reported(self) -> None:
        reading = read(
            "dotty sees bob walk into the room. "
            "the quick brown fox jumps over the lazy dog"
        )
        self.assertTrue(reading.unread)
        self.assertIn("fox", " ".join(reading.unread))

    def test_equality_chains_terminate(self) -> None:
        """A cycle in `same_as` must not hang the resolver."""
        result = answer(
            "dotty sees bob walk into the room. "
            "dotty knows the room is the hall. "
            "dotty knows the hall is the room. "
            "Where does dotty think bob is?"
        )
        self.assertIn(result.place, {"room", "hall"})


if __name__ == "__main__":
    unittest.main()
