#!/usr/bin/env python3
"""Two-turn ASK demonstration: a user-private UNKNOWN pauses and resumes."""

from __future__ import annotations

from dataclasses import dataclass, field

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

    def run_turn(self, actions) -> RunResult[RetrievalState]:
        result = self.controller.run(
            self.state,
            SequencePolicy(tuple(actions)),
            self.verifier,
            is_complete=lambda state: (
                state.pending is None
                and self.verifier.binding_value(state, "egg_color") is not None
            ),
            is_waiting=lambda state: state.awaiting is not None,
        )
        self.state = result.final_state
        self.turns.append(result)
        return result


def golden_chicken_revision_session() -> ConversationSession:
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
        user_owner="interlocutor",
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
    session = golden_chicken_revision_session()
    first = session.run_turn((ask_action("egg_color"),))
    assert first.stop_reason is StopReason.WAITING
    assert session.state.awaiting is not None
    print("USER: Now make the golden chicken lay eggs.")
    print(f"SYSTEM: {session.state.awaiting.prompt}")

    reply = session.verifier.reply_action(session.state, "silver")
    second = session.run_turn((reply,))
    assert second.solved
    print("USER: silver")
    print(f"SYSTEM: {render_revision(session)}")
    print("STATUS: user binding is frame-private VERIFIED provenance, not world truth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
