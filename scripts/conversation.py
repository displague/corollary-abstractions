#!/usr/bin/env python3
"""Maintained user-frame demonstration over repeated ASK turns.

Registered predictions (P-CR, before executing the expanded demo):

P-CR1. Two owners starting from one identical public golden-chicken state can
    answer the same private slot differently; each renderer uses only its own
    signed binding and neither session mutates the shared story or the other.
P-CR2. A later reply for the same owner and slot explicitly supersedes the
    earlier request id, preserves both bindings as provenance, and renders only
    the new value. Session identity and accepted story beats remain stable.
P-CR3. Across all turns, user testimony clears the pending UNKNOWN but never
    enters ``frame.asserted`` or corpus state. Dropping the verifier still drops
    the signing authority; this is maintained in-process state, not a durable
    authenticated restart format.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from controller import Controller, RunResult, SequencePolicy, StopReason
from frames import FrameExecutor, Literal
from oracle_controller_demo import StoryState, story_oracle_run
from retrieval import RetrievalState, RetrievalVerifier, ask_action


class EmptyStore:
    """ASK must not consult a durable store for a user-private slot."""

    def query(self, key: str, limit: int = 24):
        raise AssertionError(f"ASK unexpectedly queried durable store for {key!r}")

    def binding_match_mode(self, item, key: str):
        del item, key
        return None

    def contains_item(self, item) -> bool:
        del item
        return False


@dataclass
class ConversationSession:
    """Persist accepted symbolic state and per-turn traces across user input."""

    state: RetrievalState
    verifier: RetrievalVerifier
    story_state: StoryState
    controller: Controller[RetrievalState] = field(
        default_factory=lambda: Controller(max_steps=8)
    )
    turns: list[RunResult[RetrievalState]] = field(default_factory=list)
    active_slot: str = "egg_color"

    def run_turn(self, actions) -> RunResult[RetrievalState]:
        result = self.controller.run(
            self.state,
            SequencePolicy(tuple(actions)),
            self.verifier,
            is_complete=lambda state: (
                state.pending is None
                and self.verifier.binding_value(state, self.active_slot)
                is not None
            ),
            is_waiting=lambda state: state.awaiting is not None,
        )
        self.state = result.final_state
        self.turns.append(result)
        return result

    def request_private_slot(self, slot: str) -> None:
        """Open a new goal while retaining this owner's session memory."""
        if self.state.pending is not None or self.state.awaiting is not None:
            raise ValueError("cannot open a new goal while another is unresolved")
        fresh = RetrievalState.from_unknown(
            self.verifier.frame_executor,
            self.state.frame,
            slot,
            slot,
            Literal("the golden chicken's eggs", "color", slot),
            resolution_channel="user",
            user_owner=self.state.user_frame.owner,
        )
        self.state = replace(
            fresh,
            session_id=self.state.session_id,
            user_frame=self.state.user_frame,
        )
        self.active_slot = slot

    def ask_and_reply(self, slot: str, value: str) -> None:
        if self.state.pending is None:
            self.request_private_slot(slot)
        asked = self.run_turn((ask_action(slot),))
        if asked.stop_reason is not StopReason.WAITING:
            raise AssertionError("ASK did not pause for user input")
        reply = self.verifier.reply_action(self.state, value)
        answered = self.run_turn((reply,))
        if not answered.solved:
            raise AssertionError("authenticated reply did not resume the goal")


def golden_chicken_revision_session(
    owner: str = "interlocutor",
) -> ConversationSession:
    executor = FrameExecutor()
    accepted_story = story_oracle_run().final_state
    frame = accepted_story.frame_state
    state = RetrievalState.from_unknown(
        executor,
        frame,
        "egg_color",
        "egg_color",
        Literal("the golden chicken's eggs", "color", "egg_color"),
        resolution_channel="user",
        user_owner=owner,
    )
    return ConversationSession(
        state=state,
        verifier=RetrievalVerifier(EmptyStore(), executor),
        story_state=accepted_story,
    )


def render_revision(session: ConversationSession) -> str:
    color = session.verifier.binding_value(session.state, "egg_color")
    if color is None:
        raise ValueError("egg_color has no authenticated user binding")
    accepted_story = " ".join(
        beat.text if beat.text.endswith((".", "!", "?")) else f"{beat.text}."
        for beat in session.story_state.beats
    )
    return f"{accepted_story} Now the golden chicken laid {color} eggs."


def main() -> int:
    alice = golden_chicken_revision_session("alice")
    bob = golden_chicken_revision_session("bob")
    assert alice.story_state == bob.story_state

    alice.ask_and_reply("egg_color", "silver")
    bob.ask_and_reply("egg_color", "blue")
    print("ALICE: Now make the golden chicken lay silver eggs.")
    print(f"SYSTEM/ALICE: {render_revision(alice)}")
    print("BOB: In my version, make the eggs blue.")
    print(f"SYSTEM/BOB: {render_revision(bob)}")

    first_request = alice.state.user_frame.bindings[-1].request_id
    alice.request_private_slot("egg_color")
    alice.ask_and_reply("egg_color", "copper")
    assert first_request in alice.state.user_frame.superseded_request_ids
    print("ALICE: Change mine: make the eggs copper instead.")
    print(f"SYSTEM/ALICE: {render_revision(alice)}")
    print(
        "STATUS: owner-isolated session bindings; the silver request is "
        "explicitly superseded, and no user reply enters world truth"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
