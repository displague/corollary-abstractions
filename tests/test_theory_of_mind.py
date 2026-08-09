"""P-CF1 controls: owned frames derive false belief from event visibility."""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import Verdict  # noqa: E402
from frames import FrameEvent, FrameExecutor, FrameSpec, Literal  # noqa: E402


BASKET = Literal("marble", "located_in", "basket")
NOT_BASKET = BASKET.negated
BOX = Literal("marble", "located_in", "box")
PLACE = FrameEvent(
    "place", (BASKET,), ("sally", "anne", "world"), ("located_in",)
)
MOVE = FrameEvent(
    "move", (NOT_BASKET, BOX), ("anne", "world"), ("located_in",)
)


def belief(owner: str):
    executor = FrameExecutor()
    state = executor.open_frame(
        FrameSpec(frame=f"runtime.frames.belief_{owner}", owner=owner)
    )
    return executor, state


class TheoryOfMindTests(unittest.TestCase):
    def test_sally_false_belief_is_derived_from_missing_the_move(self) -> None:
        executor, sally = belief("sally")
        _, world = belief("world")

        sally = executor.observe_event(sally, PLACE).next_state
        world = executor.observe_event(world, PLACE).next_state
        sally_after_move = executor.observe_event(sally, MOVE).next_state
        world_after_move = executor.observe_event(world, MOVE).next_state

        self.assertEqual(executor.belief_value(sally_after_move, "marble", "located_in"), "basket")
        self.assertEqual(executor.belief_value(world_after_move, "marble", "located_in"), "box")
        self.assertIs(executor.check(sally_after_move, BASKET).verdict, Verdict.VERIFIED)
        self.assertIs(executor.check(world_after_move, BASKET).verdict, Verdict.REFUTED)
        self.assertEqual(sally_after_move.observed_events, (PLACE,))
        self.assertEqual(world_after_move.observed_events, (PLACE, MOVE))

    def test_anne_witnesses_the_move_and_updates(self) -> None:
        executor, anne = belief("anne")
        anne = executor.observe_event(anne, PLACE).next_state
        anne = executor.observe_event(anne, MOVE).next_state
        self.assertEqual(executor.belief_value(anne, "marble", "located_in"), "box")

    def test_unwitnessed_event_cannot_be_replayed_with_forged_visibility(self) -> None:
        executor, sally = belief("sally")
        sally = executor.observe_event(sally, PLACE).next_state
        missed = executor.observe_event(sally, MOVE)
        forged = replace(MOVE, witnessed_by=("sally", "anne", "world"))
        replay = executor.observe_event(missed.next_state, forged)
        self.assertIs(replay.verdict, Verdict.REFUSED)
        self.assertIs(replay.next_state, None)
        self.assertEqual(executor.belief_value(missed.next_state, "marble", "located_in"), "basket")

    def test_observed_event_retry_is_idempotent_but_collision_refuses(self) -> None:
        executor, sally = belief("sally")
        first = executor.observe_event(sally, PLACE)
        retry = executor.observe_event(first.next_state, PLACE)
        collision = executor.observe_event(
            first.next_state,
            replace(PLACE, effects=(BOX,)),
        )
        self.assertIs(retry.verdict, Verdict.VERIFIED)
        self.assertEqual(retry.next_state, first.next_state)
        self.assertIs(collision.verdict, Verdict.REFUSED)

    def test_witnessed_move_supersedes_declaration_backed_belief(self) -> None:
        executor = FrameExecutor()
        state = executor.open_frame(
            FrameSpec(
                frame="runtime.frames.declared_belief",
                owner="sally",
                declarations=(("initial", BASKET),),
            )
        )
        visible_move = replace(MOVE, witnessed_by=("sally", "anne", "world"))
        moved = executor.observe_event(state, visible_move).next_state
        self.assertEqual(executor.belief_value(moved, "marble", "located_in"), "box")
        self.assertIs(executor.check(moved, BASKET).verdict, Verdict.REFUTED)
        self.assertIn("initial", moved.superseded_declarations)

    def test_nonfunctional_positive_values_accumulate(self) -> None:
        executor, sally = belief("sally")
        red = FrameEvent(
            "red", (Literal("marble", "has_trait", "red"),), ("sally",)
        )
        round_ = FrameEvent(
            "round", (Literal("marble", "has_trait", "round"),), ("sally",)
        )
        sally = executor.observe_event(sally, red).next_state
        sally = executor.observe_event(sally, round_).next_state
        self.assertIs(
            executor.check(sally, Literal("marble", "has_trait", "red")).verdict,
            Verdict.VERIFIED,
        )
        self.assertIs(
            executor.check(sally, Literal("marble", "has_trait", "round")).verdict,
            Verdict.VERIFIED,
        )

    def test_unowned_frame_cannot_consume_attributed_events(self) -> None:
        executor = FrameExecutor()
        state = executor.open_frame(FrameSpec(frame="runtime.frames.unowned"))
        result = executor.observe_event(state, PLACE)
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIs(result.next_state, None)

    def test_owned_frame_persists_instead_of_demoting_on_close(self) -> None:
        executor, sally = belief("sally")
        sally = executor.observe_event(sally, PLACE).next_state
        result = executor.close_frame(sally)
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertEqual(result.state, sally)
        self.assertEqual(result.demoted, ())

    def test_runtime_and_corpus_frame_namespaces_are_explicit(self) -> None:
        with self.assertRaisesRegex(ValueError, "reserved runtime.frames"):
            FrameSpec(frame="narrative.frames.synthetic")
        with self.assertRaisesRegex(ValueError, "corpus-backed"):
            FrameSpec(frame="runtime.frames.synthetic", corpus_backed=True)
        corpus = FrameSpec(
            frame="narrative.frames.cartoon_gravity", corpus_backed=True
        )
        self.assertTrue(corpus.corpus_backed)

    def test_owner_and_event_metadata_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "owner must be non-empty"):
            FrameSpec(frame="runtime.frames.blank_owner", owner=" ")
        with self.assertRaisesRegex(ValueError, "event_id"):
            FrameEvent(" ", (BOX,), ("sally",))
        with self.assertRaisesRegex(ValueError, "at least one effect"):
            FrameEvent("empty", (), ("sally",))
        with self.assertRaisesRegex(ValueError, "must be unique"):
            FrameEvent("duplicate", (BOX,), ("sally", "sally"))
        with self.assertRaisesRegex(ValueError, "must name an event effect"):
            FrameEvent("wrong_function", (BOX,), ("sally",), ("has_trait",))
        with self.assertRaisesRegex(ValueError, "contradictory effects"):
            FrameEvent("incoherent", (BOX, BOX.negated), ("sally",))
        cupboard = Literal("marble", "located_in", "cupboard")
        with self.assertRaisesRegex(ValueError, "competing positive values"):
            FrameEvent(
                "ambiguous_location",
                (BOX, cupboard),
                ("sally",),
                ("located_in",),
            )


if __name__ == "__main__":
    unittest.main()
