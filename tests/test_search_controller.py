from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    SearchController,
    Verification,
    Verdict,
)


@dataclass(frozen=True)
class GraphState:
    node: str


class GraphVerifier:
    name = "test-graph"

    def __init__(self):
        self.edges = {
            ("root", "bad"): "dead",
            ("root", "good"): "middle",
            ("middle", "finish"): "solved",
            ("middle", "cycle"): "root",
        }

    def state_key(self, state: GraphState) -> str:
        return state.node

    def evaluate(self, state: GraphState, action: Action):
        target = self.edges.get((state.node, action.name))
        if target is None:
            return Verification(Verdict.REFUSED, "no edge")
        return Verification(
            Verdict.PROVEN if target == "solved" else Verdict.VERIFIED,
            "edge accepted",
            GraphState(target),
        )


class GraphPolicy:
    def propose_all(self, state, trace):
        del state, trace
        return tuple(
            Action.build(ActionKind.GEN, name)
            for name in ("bad", "good", "cycle", "finish")
        )


class SearchControllerTests(unittest.TestCase):
    def test_breadth_first_search_abandons_accepted_dead_branch(self) -> None:
        result = SearchController[GraphState](20, 100).run(
            GraphState("root"), GraphPolicy(), GraphVerifier(),
            lambda state: state.node == "solved",
        )
        self.assertTrue(result.solved)
        self.assertEqual(result.states_seen, 4)
        self.assertEqual(
            [entry.action.name for entry in result.solution_trace],
            ["good", "finish"],
        )
        dead = [entry for entry in result.trace
                if entry.action.name == "bad" and entry.accepted]
        self.assertEqual(len(dead), 1)
        self.assertNotIn(dead[0].index,
                         [entry.index for entry in result.solution_trace])

    def test_accepted_cycle_is_traced_but_not_requeued(self) -> None:
        result = SearchController[GraphState](20, 100).run(
            GraphState("root"), GraphPolicy(), GraphVerifier(),
            lambda state: state.node == "solved",
        )
        cycles = [entry for entry in result.trace
                  if entry.action.name == "cycle" and entry.accepted]
        self.assertEqual(len(cycles), 1)
        self.assertFalse(cycles[0].queued)

    def test_node_budget_is_distinct_from_proposal_budget(self) -> None:
        node_limited = SearchController[GraphState](1, 100).run(
            GraphState("root"), GraphPolicy(), GraphVerifier(),
            lambda state: state.node == "solved",
        )
        self.assertEqual(node_limited.stop_reason.value, "budget")
        self.assertEqual(node_limited.nodes_expanded, 1)

        proposal_limited = SearchController[GraphState](20, 1).run(
            GraphState("root"), GraphPolicy(), GraphVerifier(),
            lambda state: state.node == "solved",
        )
        self.assertEqual(proposal_limited.stop_reason.value, "budget")
        self.assertEqual(proposal_limited.proposals, 1)

    def test_proposal_budget_does_not_materialize_candidate_stream(self) -> None:
        yielded = []

        class StreamingPolicy:
            def propose_all(self, state, trace):
                del state, trace
                for index in range(100):
                    yielded.append(index)
                    yield Action.build(ActionKind.GEN, f"missing-{index}")

        result = SearchController[GraphState](20, 3).run(
            GraphState("root"), StreamingPolicy(), GraphVerifier(),
            lambda state: False,
        )
        self.assertEqual(result.stop_reason.value, "budget")
        self.assertEqual(result.proposals, 3)
        self.assertEqual(yielded, [0, 1, 2])

    def test_exhaustion_is_not_reported_as_budget(self) -> None:
        class EmptyPolicy:
            def propose_all(self, state, trace):
                del state, trace
                return ()

        result = SearchController[GraphState](20, 100).run(
            GraphState("root"), EmptyPolicy(), GraphVerifier(),
            lambda state: False,
        )
        self.assertEqual(result.stop_reason.value, "exhausted")

    def test_policy_and_verifier_cannot_mutate_other_branches(self) -> None:
        class MutatingPolicy:
            def propose_all(self, state, trace):
                state["path"].append("policy-corruption")
                if trace:
                    trace[0].state_after["path"].append("trace-corruption")
                return (Action.build(ActionKind.GEN, "advance"),)

        class MutatingVerifier:
            name = "mutating-verifier"

            def state_key(self, state):
                return "/".join(state["path"])

            def evaluate(self, state, action):
                del action
                state["path"].append("advance")
                return Verification(Verdict.PROVEN, "done", state)

        initial = {"path": []}
        result = SearchController[dict](2, 2).run(
            initial, MutatingPolicy(), MutatingVerifier(),
            lambda state: state["path"] == ["advance"],
        )
        self.assertTrue(result.solved)
        self.assertEqual(initial, {"path": []})
        self.assertEqual(result.initial_state, {"path": []})
        self.assertEqual(result.trace[0].state_before, {"path": []})
        self.assertEqual(result.final_state, {"path": ["advance"]})
        self.assertEqual(result.states_seen, 2)


if __name__ == "__main__":
    unittest.main()
