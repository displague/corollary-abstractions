#!/usr/bin/env python3
"""P1 and P2 — the session ledger's construction prerequisites, checked.

`docs/DESIGN-session-ledger.md` §6 orders three prerequisites before any
slice exists. These tests keep the two measurement prerequisites honest:

* **P1** (`experiments/session_p1_command_bound.json`) — the bound on
  admitted commands per template class. The test recomputes it and demands
  byte identity, so the committed artifact is a *reproduction*, not a
  snapshot of a run nobody can repeat (ROADMAP-v0.21 §4.0(2)).
* **P2** (`experiments/session_p2_separator_probe.json`) — separator
  expressibility over ten hand-sealed ambiguous prompts. The test checks the
  seal came first: every prompt's candidate-reading set is inside the sealed
  half, and the probe's verdicts never add a reading the seal did not carry.

Both artifacts are hand-checkable and neither licenses a capability. What
these tests protect is the *order* — a probe whose question was written after
its answer is not a probe.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

P1_ARTIFACT = REPO / "experiments" / "session_p1_command_bound.json"
P1_BUILDER = REPO / "scripts" / "measure_command_bound.py"
P2_ARTIFACT = REPO / "experiments" / "session_p2_separator_probe.json"
P2_BUILDER = REPO / "scripts" / "probe_separator_expressibility.py"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class P1CommandBound(unittest.TestCase):
    """The artifact says what the code computes, and nothing else."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = _load(P1_ARTIFACT)

    def test_artifact_reproduces_byte_identically(self) -> None:
        """`--check` recomputes from committed bytes and compares."""

        result = subprocess.run(
            [sys.executable, str(P1_BUILDER), "--check"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_builder_digest_is_the_builders_bytes(self) -> None:
        self.assertEqual(
            self.artifact["builder_digest"],
            hashlib.sha256(P1_BUILDER.read_bytes()).hexdigest(),
        )

    def test_line_grammar_digest_matches_the_live_grammar(self) -> None:
        from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

        rendered = json.dumps(LINE_GRAMMAR, sort_keys=True, default=list)
        self.assertEqual(
            self.artifact["line_grammar_digest"],
            hashlib.sha256(rendered.encode("utf-8")).hexdigest(),
        )

    def test_one_class_per_grammar_row_in_order(self) -> None:
        from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

        classes = self.artifact["classes"]
        self.assertEqual(len(classes), len(LINE_GRAMMAR))
        for position, (row, entry) in enumerate(zip(LINE_GRAMMAR, classes)):
            self.assertEqual(entry["class_index"], position)
            self.assertEqual(entry["form"], row["form"])
            self.assertEqual(entry["route"], row["route"])

    def test_every_class_declares_a_bound_kind(self) -> None:
        for entry in self.artifact["classes"]:
            self.assertIn(
                entry["bound_kind"],
                {"closed", "open", "gated"},
                entry["form"],
            )

    def test_closed_classes_carry_a_count_and_open_ones_do_not(self) -> None:
        for entry in self.artifact["classes"]:
            if entry["bound_kind"] == "closed":
                self.assertIsNotNone(
                    entry["admitted_commands"], entry["form"]
                )
            if entry["bound_kind"] == "open":
                self.assertIsNone(entry["admitted_commands"], entry["form"])
                self.assertIn("unbounded_reason", entry)

    def test_the_total_is_the_sum_over_closed_classes_only(self) -> None:
        totals = self.artifact["totals"]
        closed = [
            entry
            for entry in self.artifact["classes"]
            if entry["bound_kind"] == "closed"
        ]
        self.assertEqual(totals["closed_classes"], len(closed))
        self.assertEqual(
            totals["closed_total"],
            sum(int(entry["admitted_commands"]) for entry in closed),
        )
        self.assertIsNone(totals["open_total"])

    def test_the_finding_carries_the_numbers_it_describes(self) -> None:
        """The sentence must be able to go red when the counts move.

        The cycle's standing review question is whether a green assertion
        could ever have gone red (ROADMAP-v0.21 §4). A hand-typed "eight of
        fourteen" beside a computed four is exactly the failure, so the
        finding is generated and this test pins it to the counts.
        """

        totals = self.artifact["totals"]
        finding = self.artifact["finding"]
        self.assertIn(str(totals["closed_total"]), finding)
        self.assertIn(str(totals["template_classes"]), finding)
        self.assertIn(str(totals["open_classes"]), finding)
        expected = (
            "The registered grammar is NOT finite."
            if totals["open_classes"]
            else "The registered grammar is finite."
        )
        self.assertTrue(finding.startswith(expected), finding[:80])

    def test_a_closed_class_whose_producer_went_silent_raises(self) -> None:
        """The kind/count agreement check is live, not decorative.

        Class 4 (`twin <statement-id>`) declares `bound_kind: closed`. If its
        producer stops reading — a moved ledger, an unreadable file — the
        builder must refuse rather than publish a class labelled closed with
        no count, which would look like an honest null and read as a bound.
        """

        import measure_command_bound as builder  # noqa: PLC0415

        original = builder._twin_vocabulary
        builder._twin_vocabulary = lambda _root: {
            "members": None,
            "reason": "simulated unreadable ledger",
        }
        try:
            with self.assertRaises(RuntimeError) as caught:
                builder._classes(REPO)
        finally:
            builder._twin_vocabulary = original
        self.assertIn("closed", str(caught.exception))

    def test_the_non_claims_are_carried_and_specific(self) -> None:
        claims = self.artifact["what_this_does_not_claim"]
        self.assertGreaterEqual(len(claims), 3)
        joined = " ".join(claims).lower()
        # The three the design names by hand: completeness over readings
        # (§11), the slice-2 proposer, and the environment-gated row.
        self.assertIn("completeness", joined)
        self.assertIn("proposer", joined)
        self.assertIn("gated", joined)


class P2SeparatorProbe(unittest.TestCase):
    """The seal came before the probe, and the probe stayed inside it."""

    @classmethod
    def setUpClass(cls) -> None:
        if not P2_ARTIFACT.exists():  # pragma: no cover - ordering guard
            raise unittest.SkipTest("P2 artifact is not committed yet")
        cls.artifact = _load(P2_ARTIFACT)

    def test_ten_prompts_sealed(self) -> None:
        self.assertEqual(len(self.artifact["seal"]["prompts"]), 10)

    def test_every_sealed_prompt_has_at_least_two_readings(self) -> None:
        for prompt in self.artifact["seal"]["prompts"]:
            self.assertGreaterEqual(
                len(prompt["candidate_readings"]), 2, prompt["prompt_id"]
            )

    def test_seal_digest_covers_the_sealed_half(self) -> None:
        import probe_separator_expressibility as probe  # noqa: PLC0415

        self.assertEqual(
            self.artifact["seal"]["seal_digest"],
            probe.seal_digest(self.artifact["seal"]["prompts"]),
        )

    def test_verdicts_name_only_sealed_readings(self) -> None:
        sealed = {
            prompt["prompt_id"]: {
                reading["reading_id"]
                for reading in prompt["candidate_readings"]
            }
            for prompt in self.artifact["seal"]["prompts"]
        }
        for verdict in self.artifact["verdicts"]:
            known = sealed[verdict["prompt_id"]]
            for reading_id in verdict["readings_probed"]:
                self.assertIn(reading_id, known, verdict["prompt_id"])

    def test_one_verdict_per_sealed_prompt(self) -> None:
        self.assertEqual(
            [prompt["prompt_id"] for prompt in self.artifact["seal"]["prompts"]],
            [verdict["prompt_id"] for verdict in self.artifact["verdicts"]],
        )

    def test_artifact_reproduces_byte_identically(self) -> None:
        result = subprocess.run(
            [sys.executable, str(P2_BUILDER), "--check"],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_aggregate_answer_is_computed_from_the_verdicts(self) -> None:
        separable = sum(
            1 for verdict in self.artifact["verdicts"] if verdict["separated"]
        )
        self.assertEqual(
            self.artifact["aggregate"]["prompts_with_a_separator"], separable
        )
        self.assertEqual(
            self.artifact["aggregate"]["prompts_total"],
            len(self.artifact["verdicts"]),
        )

    def test_this_is_a_measurement_and_not_a_gate(self) -> None:
        self.assertIn("not_a_gate", self.artifact)


if __name__ == "__main__":
    unittest.main()
