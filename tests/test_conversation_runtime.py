from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from conversation import (  # noqa: E402
    ask_action,
    golden_chicken_revision_session,
    render_revision,
)
from retrieval import UserBinding  # noqa: E402


class ConversationRuntimeTests(unittest.TestCase):
    def test_two_owner_frames_diverge_without_public_state_leakage(self) -> None:
        alice = golden_chicken_revision_session("alice")
        bob = golden_chicken_revision_session("bob")
        public_story = alice.story_state
        self.assertEqual(bob.story_state, public_story)

        alice.ask_and_reply("egg_color", "silver")
        bob.ask_and_reply("egg_color", "blue")

        self.assertIn("silver eggs", render_revision(alice))
        self.assertNotIn("blue eggs", render_revision(alice))
        self.assertIn("blue eggs", render_revision(bob))
        self.assertNotIn("silver eggs", render_revision(bob))
        self.assertEqual(alice.story_state, public_story)
        self.assertEqual(bob.story_state, public_story)
        self.assertEqual(alice.state.frame.asserted, ())
        self.assertEqual(bob.state.frame.asserted, ())

    def test_revision_supersedes_prior_binding_with_provenance(self) -> None:
        session = golden_chicken_revision_session("alice")
        session_id = session.state.session_id
        story = session.story_state
        session.ask_and_reply("egg_color", "silver")
        old_binding = session.state.user_frame.bindings[-1]

        session.request_private_slot("egg_color")
        session.ask_and_reply("egg_color", "copper")

        frame = session.state.user_frame
        self.assertEqual(session.state.session_id, session_id)
        self.assertEqual(session.story_state, story)
        self.assertEqual([binding.value for binding in frame.bindings],
                         ["silver", "copper"])
        self.assertIn(old_binding.request_id, frame.superseded_request_ids)
        self.assertTrue(render_revision(session).endswith("copper eggs."))
        self.assertEqual(session.state.frame.asserted, ())

    def test_public_state_surgery_cannot_resurrect_superseded_answer(self) -> None:
        session = golden_chicken_revision_session("alice")
        session.ask_and_reply("egg_color", "silver")
        old_binding = session.state.user_frame.bindings[-1]
        session.request_private_slot("egg_color")
        session.ask_and_reply("egg_color", "copper")

        forged = replace(
            session.state,
            user_frame=replace(
                session.state.user_frame,
                bindings=(old_binding,),
                superseded_request_ids=(),
            ),
        )
        self.assertIsNone(
            session.verifier.binding_value(forged, "egg_color")
        )

    def test_forged_cross_slot_metadata_cannot_revoke_real_binding(self) -> None:
        session = golden_chicken_revision_session("alice")
        session.ask_and_reply("egg_color", "silver")
        session.request_private_slot("tone")
        session.ask_and_reply("tone", "whimsical")
        tone = session.state.user_frame.bindings[-1]

        session.request_private_slot("egg_color")
        forged = UserBinding(
            tone.request_id, "egg_color", "forged", "guessed-signature"
        )
        session.state = replace(
            session.state,
            user_frame=replace(
                session.state.user_frame,
                bindings=session.state.user_frame.bindings + (forged,),
            ),
        )
        session.ask_and_reply("egg_color", "copper")

        self.assertEqual(
            session.verifier.binding_value(session.state, "tone"),
            "whimsical",
        )

    def test_forged_current_request_cannot_choose_slot_to_revoke(self) -> None:
        session = golden_chicken_revision_session("alice")
        session.ask_and_reply("egg_color", "silver")
        session.request_private_slot("tone")
        session.ask_and_reply("tone", "whimsical")

        session.request_private_slot("egg_color")
        session.run_turn((ask_action("egg_color"),))
        request_id = session.state.awaiting.request_id
        forged = UserBinding(
            request_id, "tone", "forged", "guessed-signature"
        )
        session.state = replace(
            session.state,
            user_frame=replace(
                session.state.user_frame,
                bindings=session.state.user_frame.bindings + (forged,),
            ),
        )
        reply = session.verifier.reply_action(session.state, "copper")
        result = session.run_turn((reply,))

        self.assertTrue(result.solved)
        self.assertEqual(
            session.verifier.binding_value(session.state, "tone"),
            "whimsical",
        )
        self.assertEqual(
            session.verifier.binding_value(session.state, "egg_color"),
            "copper",
        )


if __name__ == "__main__":
    unittest.main()
