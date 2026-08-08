"""Adversarial controls for the authenticated conversational ASK channel."""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    Controller,
    SequencePolicy,
    StopReason,
    Verdict,
)
from conversation import (  # noqa: E402
    golden_chicken_revision_session,
    render_revision,
)
from frames import FrameExecutor, FrameSpec, Literal  # noqa: E402
from retrieval import (  # noqa: E402
    RetrievalState,
    RetrievalNeed,
    RetrievalVerifier,
    UserBinding,
    ask_action,
    retrieval_action,
)


class CountingStore:
    def __init__(self) -> None:
        self.queries = 0

    def query(self, key: str, limit: int = 24):
        del key, limit
        self.queries += 1
        raise AssertionError("user-private ASK/RETRIEVE guard touched the store")

    def binding_match_mode(self, item, key: str):
        del item, key
        return None

    def contains_item(self, item) -> bool:
        del item
        return False


class AskReturnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.executor = FrameExecutor()
        self.frame = self.executor.open_frame(
            FrameSpec(frame="conversation.frames.test")
        )
        self.store = CountingStore()
        self.verifier = RetrievalVerifier(self.store, self.executor)
        self.state = self.make_state()

    def make_state(
        self,
        *,
        channel: str = "user",
        frame=None,
        owner: str = "interlocutor",
    ) -> RetrievalState:
        return RetrievalState.from_unknown(
            self.executor,
            frame or self.frame,
            "tone",
            "tone",
            Literal("story revision", "requested tone", "tone"),
            resolution_channel=channel,
            user_owner=owner,
        )

    def ask(self, state: RetrievalState | None = None):
        return self.verifier.evaluate(state or self.state, ask_action("tone"))

    def asked_state(self) -> RetrievalState:
        outcome = self.ask()
        self.assertIs(outcome.verdict, Verdict.VERIFIED)
        assert outcome.next_state is not None
        return outcome.next_state

    def test_controller_stops_waiting_after_verified_question(self) -> None:
        result = Controller(max_steps=4).run(
            self.state,
            SequencePolicy((ask_action("tone"),)),
            self.verifier,
            is_complete=lambda state: state.pending is None,
            is_waiting=lambda state: state.awaiting is not None,
        )
        self.assertIs(result.stop_reason, StopReason.WAITING)
        self.assertFalse(result.solved)
        self.assertEqual(result.accepted_steps, 1)
        self.assertIsNotNone(result.final_state.awaiting)

    def test_signed_reply_resumes_same_session_and_binds_user_frame(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        result = Controller(max_steps=4).run(
            asked,
            SequencePolicy((reply,)),
            self.verifier,
            is_complete=lambda state: (
                self.verifier.binding_value(state, "tone") is not None
            ),
        )
        self.assertTrue(result.solved)
        self.assertEqual(result.final_state.session_id, self.state.session_id)
        self.assertIsNone(result.final_state.pending)
        self.assertIsNone(result.final_state.awaiting)
        self.assertEqual(
            self.verifier.binding_value(result.final_state, "tone"),
            "whimsical",
        )
        self.assertEqual(result.final_state.frame.asserted, ())

    def test_user_private_retrieve_refuses_before_store_access(self) -> None:
        outcome = self.verifier.evaluate(self.state, retrieval_action("tone"))
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("user-private", outcome.reason)
        self.assertEqual(self.store.queries, 0)

    def test_store_assigned_unknown_cannot_ask_in_open_frame(self) -> None:
        state = self.make_state(channel="store")
        outcome = self.verifier.evaluate(state, ask_action("tone"))
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("durable store", outcome.reason)
        self.assertIsNone(outcome.next_state)

    def test_frame_local_scope_explicitly_routes_store_need_to_user(self) -> None:
        frame = self.executor.open_frame(
            FrameSpec(frame="conversation.frames.private", retrieval="frame_local")
        )
        state = self.make_state(channel="store", frame=frame)
        outcome = self.verifier.evaluate(state, ask_action("tone"))
        self.assertIs(outcome.verdict, Verdict.VERIFIED)
        self.assertEqual(self.store.queries, 0)

    def test_policy_cannot_guess_user_reply_signature(self) -> None:
        asked = self.asked_state()
        assert asked.awaiting is not None
        guessed = Action.build(
            ActionKind.ASK,
            "reply",
            {
                "request_id": asked.awaiting.request_id,
                "value": "whimsical",
                "signature": "guessed",
            },
        )
        outcome = self.verifier.evaluate(asked, guessed)
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("policy output is not user input", outcome.reason)
        self.assertIsNone(outcome.next_state)

    def test_second_verifier_cannot_accept_first_verifiers_question(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        other = RetrievalVerifier(self.store, self.executor)
        outcome = other.evaluate(asked, reply)
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("provenance is invalid", outcome.reason)

    def test_post_signature_answer_mutation_is_refused(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        arguments = dict(reply.arguments)
        arguments["value"] = "formal"
        outcome = self.verifier.evaluate(
            asked, Action.build(ActionKind.ASK, "reply", arguments)
        )
        self.assertIs(outcome.verdict, Verdict.REFUSED)

    def test_reply_cannot_cross_session(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        replay = replace(asked, session_id="different-session")
        outcome = self.verifier.evaluate(replay, reply)
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("provenance is invalid", outcome.reason)

    def test_reply_cannot_cross_frame(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        other_spec = replace(asked.frame.spec, frame="conversation.frames.other")
        replay = replace(asked, frame=replace(asked.frame, spec=other_spec))
        outcome = self.verifier.evaluate(replay, reply)
        self.assertIs(outcome.verdict, Verdict.REFUSED)

    def test_reply_cannot_cross_user_owner(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        replay = replace(
            asked,
            user_frame=replace(asked.user_frame, owner="different-user"),
        )
        outcome = self.verifier.evaluate(replay, reply)
        self.assertIs(outcome.verdict, Verdict.REFUSED)

    def test_reply_cannot_cross_question(self) -> None:
        first = self.asked_state()
        first_reply = self.verifier.reply_action(first, "whimsical")
        second_initial = self.make_state()
        second_outcome = self.verifier.evaluate(
            second_initial, ask_action("tone")
        )
        assert second_outcome.next_state is not None
        outcome = self.verifier.evaluate(second_outcome.next_state, first_reply)
        self.assertIs(outcome.verdict, Verdict.REFUSED)

    def test_reply_cannot_clear_a_substituted_pending_need(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        assert asked.pending is not None
        substituted = replace(
            asked,
            pending=RetrievalNeed(
                "audience",
                "audience",
                Literal("story revision", "requested audience", "audience"),
                asked.pending.unknown_evidence,
                "user",
            ),
        )
        outcome = self.verifier.evaluate(substituted, reply)
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("differs from", outcome.reason)

    def test_reply_rechecks_that_pending_literal_is_still_unknown(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        assert asked.pending is not None
        resolved_frame = replace(
            asked.frame,
            asserted=(("external_resolution", asked.pending.unresolved_literal),),
        )
        outcome = self.verifier.evaluate(replace(asked, frame=resolved_frame), reply)
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("no longer UNKNOWN", outcome.reason)

    def test_waiting_branch_refuses_every_non_reply_action(self) -> None:
        asked = self.asked_state()
        actions = (
            ask_action("tone"),
            retrieval_action("tone"),
            Action.build(
                ActionKind.GEN,
                "assert_fact",
                {
                    "claim_id": "smuggle",
                    "subject": "x",
                    "predicate": "p",
                    "value": "v",
                },
            ),
        )
        for action in actions:
            with self.subTest(action=action):
                outcome = self.verifier.evaluate(asked, action)
                self.assertIs(outcome.verdict, Verdict.REFUSED)
                self.assertIn("waiting", outcome.reason)
                self.assertIsNone(outcome.next_state)
        self.assertEqual(self.store.queries, 0)

    def test_forged_blank_owner_and_invalid_channel_cannot_open_question(self) -> None:
        assert self.state.pending is not None
        blank_owner = replace(
            self.state,
            user_frame=replace(self.state.user_frame, owner=" "),
        )
        invalid_channel = replace(
            self.state,
            frame=replace(
                self.state.frame,
                spec=replace(self.state.frame.spec, retrieval="frame_local"),
            ),
            pending=replace(self.state.pending, resolution_channel="invalid"),
        )
        for forged in (blank_owner, invalid_channel):
            with self.subTest(forged=forged):
                outcome = self.verifier.evaluate(forged, ask_action("tone"))
                self.assertIs(outcome.verdict, Verdict.REFUSED)

    def test_forged_public_question_cannot_receive_signed_reply(self) -> None:
        asked = self.asked_state()
        assert asked.awaiting is not None
        forged = replace(
            asked,
            awaiting=replace(asked.awaiting, signature="forged"),
        )
        with self.assertRaisesRegex(ValueError, "verifier-minted"):
            self.verifier.reply_action(forged, "whimsical")

    def test_forged_public_binding_is_not_authoritative(self) -> None:
        forged = replace(
            self.state,
            pending=None,
            user_frame=replace(
                self.state.user_frame,
                bindings=(UserBinding("fake", "tone", "whimsical", "guess"),),
            ),
        )
        self.assertIsNone(self.verifier.binding_value(forged, "tone"))

    def test_closed_frame_refuses_question_and_reply(self) -> None:
        closed = replace(self.state, frame=replace(self.state.frame, closed=True))
        self.assertIs(
            self.verifier.evaluate(closed, ask_action("tone")).verdict,
            Verdict.REFUSED,
        )
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        closed_asked = replace(asked, frame=replace(asked.frame, closed=True))
        self.assertIs(
            self.verifier.evaluate(closed_asked, reply).verdict,
            Verdict.REFUSED,
        )

    def test_wrong_ask_shapes_and_missing_state_are_refused(self) -> None:
        no_pending = RetrievalState(frame=self.frame)
        cases = (
            (no_pending, ask_action("tone")),
            (self.state, Action.build(ActionKind.ASK, "unknown")),
            (
                self.state,
                Action.build(
                    ActionKind.ASK,
                    "clarify",
                    {"slot": "tone", "extra": "smuggled"},
                ),
            ),
            (self.state, ask_action("wrong-slot")),
            (
                self.state,
                Action.build(
                    ActionKind.ASK,
                    "reply",
                    {"request_id": "x", "signature": "x", "value": "x"},
                ),
            ),
        )
        for state, action in cases:
            with self.subTest(action=action):
                outcome = self.verifier.evaluate(state, action)
                self.assertIs(outcome.verdict, Verdict.REFUSED)
                self.assertIsNone(outcome.next_state)

    def test_rejected_reply_does_not_mutate_controller_state(self) -> None:
        asked = self.asked_state()
        assert asked.awaiting is not None
        guessed = Action.build(
            ActionKind.ASK,
            "reply",
            {
                "request_id": asked.awaiting.request_id,
                "signature": "guess",
                "value": "whimsical",
            },
        )
        result = Controller(max_steps=2).run(
            asked,
            SequencePolicy((guessed,)),
            self.verifier,
            is_complete=lambda state: state.pending is None,
        )
        self.assertEqual(result.final_state, asked)
        self.assertEqual(result.accepted_steps, 0)

    def test_consumed_reply_cannot_satisfy_reinstated_identical_need(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        answered = Controller(max_steps=2).run(
            asked,
            SequencePolicy((reply,)),
            self.verifier,
            is_complete=lambda state: state.pending is None,
        )
        reinstated = replace(
            answered.final_state,
            pending=asked.pending,
            awaiting=asked.awaiting,
            user_frame=replace(
                answered.final_state.user_frame,
                consumed_request_ids=(),
            ),
        )
        replay = self.verifier.evaluate(reinstated, reply)
        self.assertIs(replay.verdict, Verdict.REFUSED)
        self.assertIn("already consumed", replay.reason)

    def test_goal_exception_does_not_consume_uncommitted_reply(self) -> None:
        asked = self.asked_state()
        reply = self.verifier.reply_action(asked, "whimsical")
        calls = 0

        def failing_goal(state):
            nonlocal calls
            del state
            calls += 1
            if calls == 1:
                return False
            raise RuntimeError("goal failed after speculative verification")

        with self.assertRaisesRegex(RuntimeError, "speculative"):
            Controller(max_steps=2).run(
                asked,
                SequencePolicy((reply,)),
                self.verifier,
                is_complete=failing_goal,
            )
        retry = Controller(max_steps=2).run(
            asked,
            SequencePolicy((reply,)),
            self.verifier,
            is_complete=lambda state: state.pending is None,
        )
        self.assertTrue(retry.solved)

    def test_ask_transitions_refuse_dependency_smuggling(self) -> None:
        clarify = replace(
            ask_action("tone"), dependencies=("forged-prerequisite",)
        )
        self.assertIs(
            self.verifier.evaluate(self.state, clarify).verdict,
            Verdict.REFUSED,
        )
        asked = self.asked_state()
        reply = replace(
            self.verifier.reply_action(asked, "whimsical"),
            dependencies=("forged-prerequisite",),
        )
        self.assertIs(
            self.verifier.evaluate(asked, reply).verdict,
            Verdict.REFUSED,
        )

    def test_golden_chicken_revision_pauses_resumes_and_renders(self) -> None:
        session = golden_chicken_revision_session()
        session_id = session.state.session_id
        original_beats = session.story_state.beats
        original_obligations = session.story_state.frame_state.obligations
        self.assertEqual(len(original_beats), 3)
        self.assertEqual(len(original_obligations), 1)
        self.assertEqual(session.state.frame, session.story_state.frame_state)
        first = session.run_turn((ask_action("egg_color"),))
        self.assertIs(first.stop_reason, StopReason.WAITING)
        assert session.state.awaiting is not None
        self.assertIn("egg_color", session.state.awaiting.prompt)

        reply = session.verifier.reply_action(session.state, "silver")
        second = session.run_turn((reply,))
        self.assertTrue(second.solved)
        self.assertEqual(session.state.session_id, session_id)
        self.assertEqual(len(session.turns), 2)
        self.assertEqual(session.story_state.beats, original_beats)
        self.assertEqual(
            session.story_state.frame_state.obligations, original_obligations
        )
        rendered = render_revision(session)
        for beat in original_beats:
            self.assertIn(beat.text, rendered)
        self.assertTrue(rendered.endswith("Now the golden chicken laid silver eggs."))
        self.assertEqual(session.state.frame.asserted, ())


if __name__ == "__main__":
    unittest.main()
