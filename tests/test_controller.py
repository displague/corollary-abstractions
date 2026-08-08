from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    Controller,
    SequencePolicy,
    StopReason,
    Verification,
    Verdict,
)
from oracle_controller_demo import (  # noqa: E402
    LeanReplayState,
    LeanReplayVerifier,
    StoryFrameVerifier,
    StoryState,
    lean_oracle_run,
    story_oracle_actions,
    story_oracle_run,
)


class PassiveVerifier:
    name = "passive-isolation-probe"

    @staticmethod
    def state_key(state: list[str]) -> str:
        return repr(state)

    @staticmethod
    def evaluate(
        state: list[str], action: Action
    ) -> Verification[list[str]]:
        del state, action
        raise AssertionError("policy should stop before verifier evaluation")


class ControllerContractTests(unittest.TestCase):
    def test_public_action_vocabulary_is_complete(self) -> None:
        self.assertEqual(
            {kind.value for kind in ActionKind},
            {"POINT", "GEN", "RETRIEVE", "ASK", "WRITE"},
        )

    def test_rejected_verification_cannot_supply_next_state(self) -> None:
        bad = Verification(Verdict.REFUTED, "bad", next_state="mutated")
        with self.assertRaisesRegex(ValueError, "may not mutate"):
            bad.validate()

    def test_mutating_rejected_verifier_cannot_change_accepted_state(self) -> None:
        class MutatingVerifier:
            name = "mutation-probe"

            @staticmethod
            def state_key(state: list[str]) -> str:
                return repr(state)

            @staticmethod
            def evaluate(
                state: list[str], action: Action
            ) -> Verification[list[str]]:
                del action
                state.append("leaked from dead branch")
                return Verification(Verdict.REFUTED, "deliberate mutation probe")

        caller_state: list[str] = []
        run = Controller[list[str]](max_steps=1).run(
            caller_state,
            SequencePolicy((Action.build(ActionKind.GEN, "mutate"),)),
            MutatingVerifier(),
            lambda state: bool(state),
        )
        self.assertEqual(caller_state, [])
        self.assertEqual(run.initial_state, [])
        self.assertEqual(run.final_state, [])
        self.assertEqual(run.trace[0].state_before, [])
        self.assertEqual(run.trace[0].state_after, [])

    def test_mutating_state_key_cannot_change_accepted_state(self) -> None:
        class MutatingKeyVerifier:
            name = "state-key-mutation-probe"

            @staticmethod
            def state_key(state: list[str]) -> str:
                state.append("leaked from state_key")
                return repr(state)

            @staticmethod
            def evaluate(
                state: list[str], action: Action
            ) -> Verification[list[str]]:
                del state, action
                return Verification(Verdict.REFUTED, "deliberate key mutation probe")

        caller_state: list[str] = []
        run = Controller[list[str]](max_steps=1).run(
            caller_state,
            SequencePolicy((Action.build(ActionKind.GEN, "mutate-key"),)),
            MutatingKeyVerifier(),
            lambda state: bool(state),
        )
        self.assertEqual(caller_state, [])
        self.assertEqual(run.initial_state, [])
        self.assertEqual(run.final_state, [])
        self.assertEqual(run.trace[0].state_before, [])
        self.assertEqual(run.trace[0].state_after, [])

    def test_mutating_goal_cannot_change_accepted_state(self) -> None:
        class NoActionPolicy:
            @staticmethod
            def propose(state: list[str], trace: tuple[object, ...]) -> None:
                del state, trace
                return None

        def mutating_goal(state: list[str]) -> bool:
            state.append("leaked from goal")
            return False

        caller_state: list[str] = []
        run = Controller[list[str]]().run(
            caller_state,
            NoActionPolicy(),
            PassiveVerifier(),
            mutating_goal,
        )
        self.assertEqual(caller_state, [])
        self.assertEqual(run.initial_state, [])
        self.assertEqual(run.final_state, [])

    def test_mutating_policy_cannot_change_accepted_state(self) -> None:
        class MutatingPolicy:
            @staticmethod
            def propose(state: list[str], trace: tuple[object, ...]) -> None:
                del trace
                state.append("leaked from policy")
                return None

        caller_state: list[str] = []
        run = Controller[list[str]]().run(
            caller_state,
            MutatingPolicy(),
            PassiveVerifier(),
            lambda state: bool(state),
        )
        self.assertEqual(caller_state, [])
        self.assertEqual(run.initial_state, [])
        self.assertEqual(run.final_state, [])

    def test_duplicate_rejected_action_is_pruned(self) -> None:
        initial = StoryFrameVerifier().initial_state()
        invalid = Action.build(
            ActionKind.GEN,
            "resolve",
            {"agent": "the golden chicken", "desire": "x", "outcome": "done"},
        )
        run = Controller[StoryState](max_steps=2).run(
            initial,
            SequencePolicy((invalid, invalid)),
            StoryFrameVerifier(),
            lambda state: bool(state.beats),
        )
        self.assertEqual(run.stop_reason, StopReason.BUDGET)
        self.assertEqual(run.rejected_steps, 2)
        self.assertEqual(run.trace[0].verification.verdict, Verdict.REFUTED)
        self.assertEqual(run.trace[1].verification.verdict, Verdict.REFUSED)
        self.assertIn("duplicate", run.trace[1].verification.reason)
        self.assertEqual(run.final_state, initial)


class LeanReplayTests(unittest.TestCase):
    def test_oracle_replays_three_contiguous_extracted_steps(self) -> None:
        run = lean_oracle_run()
        self.assertTrue(run.solved)
        self.assertEqual(run.accepted_steps, 3)
        self.assertEqual(run.final_state.proof_state, "no goals")
        self.assertEqual(
            run.final_state.tactics, ("intro hp", "left", "exact hp")
        )
        self.assertEqual(run.trace[-1].verification.verdict, Verdict.PROVEN)

    def test_unrecorded_tactic_does_not_pass_replay_verifier(self) -> None:
        verifier = LeanReplayVerifier()
        valid = lean_oracle_run().initial_state
        action = Action.build(
            ActionKind.GEN, "lean_tactic", {"tactic": "exact imaginary_proof"}
        )
        result = verifier.evaluate(valid, action)
        self.assertEqual(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)
        self.assertIn("cannot adjudicate", result.reason)

    def test_untrusted_extraction_cannot_assign_proven(self) -> None:
        records = [
            {
                "theorem": "BooleanLaws.absorption_or_and",
                "tactic": "intro hp",
                "stateBefore": "fake start",
                "stateAfter": "fake middle 1",
            },
            {
                "theorem": "BooleanLaws.absorption_or_and",
                "tactic": "left",
                "stateBefore": "fake middle 1",
                "stateAfter": "fake middle 2",
            },
            {
                "theorem": "BooleanLaws.absorption_or_and",
                "tactic": "exact hp",
                "stateBefore": "fake middle 2",
                "stateAfter": "no goals",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fabricated.json"
            path.write_text(json.dumps(records), encoding="utf-8")
            run = lean_oracle_run(path)
        self.assertTrue(run.solved)
        self.assertEqual(run.trace[-1].verification.verdict, Verdict.VERIFIED)
        self.assertIn("digest is untrusted", run.trace[-1].verification.reason)

    def test_replay_is_state_sensitive(self) -> None:
        verifier = LeanReplayVerifier()
        valid = lean_oracle_run().initial_state
        wrong_state = replace(valid, proof_state=valid.proof_state + "\n-- changed")
        action = Action.build(
            ActionKind.GEN, "lean_tactic", {"tactic": "intro hp"}
        )
        self.assertEqual(
            verifier.evaluate(wrong_state, action).verdict, Verdict.REFUSED
        )


class StoryFrameTests(unittest.TestCase):
    def test_oracle_executes_three_verified_beats(self) -> None:
        run = story_oracle_run()
        self.assertTrue(run.solved)
        self.assertEqual(run.accepted_steps, 3)
        self.assertEqual(
            tuple(beat.role for beat in run.final_state.beats),
            ("setup", "complication", "resolution"),
        )
        self.assertTrue(
            all(entry.verification.verdict is Verdict.VERIFIED for entry in run.trace)
        )

    def test_out_of_order_beat_is_refuted_without_state_change(self) -> None:
        initial = story_oracle_run().initial_state
        resolution = story_oracle_actions()[-1]
        result = StoryFrameVerifier().evaluate(initial, resolution)
        self.assertEqual(result.verdict, Verdict.REFUTED)
        self.assertIsNone(result.next_state)

    def test_trait_contradiction_is_refuted(self) -> None:
        initial = story_oracle_run().initial_state
        contradictory = Action.build(
            ActionKind.GEN,
            "introduce",
            {
                "agent": "the golden chicken",
                "trait": "silver",
                "desire": "to sing",
            },
        )
        result = StoryFrameVerifier().evaluate(initial, contradictory)
        self.assertEqual(result.verdict, Verdict.REFUTED)
        self.assertIn("explicitly denied", result.reason)

    def test_undeclared_compatible_trait_is_unknown_not_refuted(self) -> None:
        initial = story_oracle_run().initial_state
        undeclared = Action.build(
            ActionKind.GEN,
            "introduce",
            {
                "agent": "the golden chicken",
                "trait": "brave",
                "desire": "to sing",
            },
        )
        result = StoryFrameVerifier().evaluate(initial, undeclared)
        self.assertEqual(result.verdict, Verdict.UNKNOWN)
        self.assertIn("neither declared nor denied", result.reason)

    def test_rejected_branch_is_not_a_premise_for_recovery(self) -> None:
        initial = story_oracle_run().initial_state
        invalid = story_oracle_actions()[-1]
        actions = (invalid,) + story_oracle_actions()
        run = Controller[StoryState](max_steps=4).run(
            initial,
            SequencePolicy(actions),
            StoryFrameVerifier(),
            lambda state: len(state.beats) == 3,
        )
        self.assertTrue(run.solved)
        self.assertEqual(run.rejected_steps, 1)
        self.assertEqual(run.accepted_steps, 3)
        self.assertEqual(run.trace[0].state_after, initial)
        self.assertEqual(run.trace[1].state_before, initial)


if __name__ == "__main__":
    unittest.main()
