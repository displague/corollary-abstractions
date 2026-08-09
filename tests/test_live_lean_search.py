from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "prover"))
sys.path.insert(0, str(ROOT / "scripts"))

from controller import Action, ActionKind, Verdict  # noqa: E402
from live_search import (  # noqa: E402
    ABLATION_TACTICS,
    BLIND_TACTICS,
    LiveLeanVerifier,
    TacticRejected,
    blind_search,
)


class FakeLeanBackend:
    name = "fake-lean-kernel"

    def __init__(self):
        self.calls = 0
        self.transitions = {
            ("root", "intro P Q h"): "with-h",
            ("root", "intro"): "with-P",
            ("with-P", "intro"): "with-PQ",
            ("with-PQ", "intro"): "with-h",
            ("with-h", "clear h"): "dead-no-h",
            ("with-h", "constructor"): "need-Q",
            ("need-Q", "exact h.right"): "need-P",
            ("need-P", "exact h.left"): "no goals",
        }

    def start(self, proposition: str) -> object:
        self.calls += 1
        if not proposition:
            raise AssertionError("test proposition missing")
        return "root"

    def apply(self, goal: object, tactic: str) -> object:
        self.calls += 1
        try:
            return self.transitions[(goal, tactic)]
        except KeyError as exc:
            raise TacticRejected(f"{tactic} does not apply to {goal}") from exc

    def render(self, goal: object) -> str:
        return str(goal)

    def solved(self, goal: object) -> bool:
        return goal == "no goals"


class LiveLeanSearchTests(unittest.TestCase):
    def test_blind_palette_solves_and_abandons_clear_branch(self) -> None:
        result = blind_search(LiveLeanVerifier(FakeLeanBackend()), BLIND_TACTICS)
        self.assertTrue(result.solved)
        solution = [entry.action.argument("tactic")
                    for entry in result.solution_trace]
        self.assertEqual(
            solution,
            ["intro P Q h", "constructor",
             "exact h.right", "exact h.left"],
        )
        accepted_clear = [entry for entry in result.trace
                          if entry.action.argument("tactic") == "clear h"
                          and entry.accepted]
        self.assertEqual(len(accepted_clear), 1)
        self.assertNotIn(accepted_clear[0].index,
                         [entry.index for entry in result.solution_trace])

    def test_projection_ablation_is_load_bearing(self) -> None:
        result = blind_search(
            LiveLeanVerifier(FakeLeanBackend()), ABLATION_TACTICS
        )
        self.assertFalse(result.solved)
        self.assertEqual(result.stop_reason.value, "exhausted")

    def test_public_state_forgery_is_refused_before_backend_call(self) -> None:
        backend = FakeLeanBackend()
        verifier = LiveLeanVerifier(backend)
        state = verifier.start("t", "P")
        action = Action.build(
            ActionKind.GEN, "lean_tactic", {"tactic": "intro"}
        )
        calls = backend.calls
        for forged in (
            replace(state, handle="guessed"),
            replace(state, goal_text="different"),
            replace(state, theorem="other"),
            replace(state, tactics=("invented",)),
        ):
            result = verifier.evaluate(forged, action)
            self.assertEqual(result.verdict, Verdict.REFUSED)
            self.assertIsNone(result.next_state)
        self.assertEqual(backend.calls, calls)

    def test_tactic_failure_has_no_next_state(self) -> None:
        backend = FakeLeanBackend()
        verifier = LiveLeanVerifier(backend)
        state = verifier.start("t", "P")
        result = verifier.evaluate(
            state,
            Action.build(ActionKind.GEN, "lean_tactic", {"tactic": "fail"}),
        )
        self.assertEqual(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)

    def test_action_shape_and_dependencies_are_fail_closed(self) -> None:
        backend = FakeLeanBackend()
        verifier = LiveLeanVerifier(backend)
        state = verifier.start("t", "P")
        actions = (
            Action.build(ActionKind.POINT, "lean_tactic", {"tactic": "intro"}),
            Action.build(ActionKind.GEN, "other", {"tactic": "intro"}),
            Action.build(ActionKind.GEN, "lean_tactic", {"tactic": ""}),
            Action.build(
                ActionKind.GEN, "lean_tactic",
                {"tactic": "intro", "ignored": "pruning-bypass"},
            ),
            Action(
                ActionKind.GEN, "lean_tactic",
                (("tactic", "intro"), ("tactic", "intro")),
            ),
            Action.build(ActionKind.GEN, "lean_tactic", {"tactic": "intro"},
                         dependencies=("forged",)),
        )
        calls = backend.calls
        for action in actions:
            self.assertEqual(
                verifier.evaluate(state, action).verdict, Verdict.REFUSED
            )
        self.assertEqual(backend.calls, calls)

    def test_state_key_preserves_policy_relevant_tactic_history(self) -> None:
        verifier = LiveLeanVerifier(FakeLeanBackend())
        state = verifier.start("t", "P")
        left = replace(state, tactics=("left-path",))
        right = replace(state, tactics=("right-path",))
        self.assertEqual(left.goal_text, right.goal_text)
        self.assertNotEqual(verifier.state_key(left), verifier.state_key(right))


if __name__ == "__main__":
    unittest.main()
