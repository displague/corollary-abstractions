from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "prover"))

from live_search import LiveLeanState  # noqa: E402
from train_tactic_policy import (  # noqa: E402
    HELD_OUT_THEOREMS,
    LearnedTacticPolicy,
    SCHEMAS,
    action_schema,
    default_output,
    frequency_tactics,
    load_examples,
    tactic_schema,
)


class FixedScores(torch.nn.Module):
    def forward(self, data, lengths):
        del lengths
        scores = torch.zeros((len(data), len(SCHEMAS)), device=data.device)
        scores[:, SCHEMAS.index("constructor")] = 3
        scores[:, SCHEMAS.index("projection")] = 2
        scores[:, SCHEMAS.index("intro")] = 1
        return scores


class TacticPolicyTests(unittest.TestCase):
    def test_atomic_schema_mapping_is_fail_closed(self) -> None:
        self.assertEqual(tactic_schema("intro h"), "intro")
        self.assertEqual(tactic_schema("exact h.right"), "projection")
        self.assertIsNone(tactic_schema("intro h\nconstructor"))
        self.assertIsNone(tactic_schema("simp"))

    def test_theorem_split_has_no_identity_leak(self) -> None:
        examples = load_examples(ROOT / "prover" / "sample_triples.json")
        train = {item.theorem for item in examples
                 if item.theorem not in HELD_OUT_THEOREMS}
        test = {item.theorem for item in examples
                if item.theorem in HELD_OUT_THEOREMS}
        self.assertTrue(train)
        self.assertEqual(test, HELD_OUT_THEOREMS)
        self.assertTrue(train.isdisjoint(test))

    def test_learned_scores_only_reorder_registered_actions(self) -> None:
        state = LiveLeanState("t", "⊢ P", "handle")
        tactics = ("intro P Q h", "exact h.left", "constructor",
                   "exact h.right")
        actions = tuple(
            LearnedTacticPolicy(FixedScores(), "cpu", tactics)
            .propose_all(state, ())
        )
        ranked = [action.argument("tactic") for action in actions]
        self.assertEqual(
            ranked,
            ["constructor", "exact h.left", "exact h.right", "intro P Q h"],
        )
        self.assertEqual({action_schema(value) for value in ranked},
                         {"constructor", "projection", "intro"})

    def test_committed_result_contains_three_non_vacuous_seeds(self) -> None:
        result = json.loads(
            (ROOT / "experiments" / "results" / "tactic_policy.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(len(result["runs"]), 3)
        self.assertTrue(result["blind_live"]["solved"])
        self.assertEqual(result["blind_live"]["proposals"], 86)
        self.assertTrue(result["frequency_live"]["solved"])
        self.assertEqual(result["frequency_live"]["proposals"], 64)
        for run in result["runs"]:
            self.assertGreater(run["heldout_top1"],
                               result["frequency_top1"])
            self.assertGreater(run["heldout_top1"], run["shuffled_top1"])
            self.assertTrue(run["live"]["solved"])
            self.assertFalse(run["live"]["ablation_solved"])
            self.assertLess(run["live"]["proposals"],
                            result["blind_live"]["proposals"])
        learned_mean = sum(
            run["live"]["proposals"] for run in result["runs"]
        ) / len(result["runs"])
        self.assertGreaterEqual(
            learned_mean, result["frequency_live"]["proposals"]
        )

    def test_nonlive_default_cannot_overwrite_canonical_result(self) -> None:
        self.assertEqual(default_output(True).name, "tactic_policy.json")
        self.assertEqual(default_output(False).name,
                         "tactic_policy_nonlive.json")

    def test_frequency_palette_is_state_blind_and_complete(self) -> None:
        examples = load_examples(ROOT / "prover" / "sample_triples.json")
        train = [item for item in examples
                 if item.theorem not in HELD_OUT_THEOREMS]
        ranked = frequency_tactics(train)
        from live_search import BLIND_TACTICS
        self.assertEqual(set(ranked), set(BLIND_TACTICS))
        self.assertEqual(ranked[:3],
                         ("intro P Q h", "intro", "constructor"))


if __name__ == "__main__":
    unittest.main()
