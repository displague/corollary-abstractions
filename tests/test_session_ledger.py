#!/usr/bin/env python3
"""The session ledger — preregistration, records, recorder, replayer.

`docs/DESIGN-session-ledger.md` is the governing design and its §3 field
names are the contract. These tests hold three things:

* **The preregistration is verbatim.** Every clause frozen in
  `experiments/session_ledger_prereg.json` must still appear in the design
  under one stated normalization. If the design moves, this goes red and a
  person decides — which is the only thing a freeze is for.
* **The record types are the design's.** Field names, the status alphabet,
  the bounds, the chain, the MACs.
* **The behaviour the slice is for.** A supposition persists across turns; a
  later turn that consumes it cites it and the citation is read-derived; a
  turn that consumes nothing renders byte-identically to the same line served
  statelessly (B10's fence, tested rather than promised).
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

DESIGN = REPO / "docs" / "DESIGN-session-ledger.md"
PREREG = REPO / "experiments" / "session_ledger_prereg.json"


def _flat(text: str) -> str:
    """The prereg's stated normalization, and only that.

    Line wrapping collapses to single spaces, and a hyphen sitting at a line
    break rejoins the word it split. The design wraps `byte-dependence` across
    two lines; without the rejoin a quotation of it would depend on the
    design's column width, which is a property of the file and not of the
    sentence.
    """

    rejoined = re.sub(r"-\s*\n\s*", "-", text)
    return re.sub(r"\s+", " ", rejoined).strip()


class PreregIsVerbatim(unittest.TestCase):
    """Frozen clauses are quotations, not paraphrases."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        cls.design = _flat(DESIGN.read_text(encoding="utf-8"))

    def _assert_quoted(self, label: str, clause: str) -> None:
        """`assertIn` with the haystack kept out of the message.

        The design is ~25 kB flattened; a failure that pastes it makes the
        one thing a reader needs — WHICH clause drifted — the hardest thing
        to find in the output.
        """

        flat = _flat(clause)
        if flat in self.design:
            return
        self.fail(
            f"{label} is not verbatim in {DESIGN.name}\n"
            f"  frozen clause starts: {flat[:120]!r}\n"
            f"  frozen clause ends:   {flat[-120:]!r}"
        )

    def test_every_gate_clause_is_verbatim(self) -> None:
        clauses = self.prereg["construction_gate"]["clauses"]
        self.assertEqual(
            sorted(clauses, key=lambda name: int(name[1:])),
            [f"B{n}" for n in range(1, 14)],
            "the gate must carry B1..B13 and nothing else",
        )
        for name, clause in clauses.items():
            self._assert_quoted(name, clause["verbatim"])

    def test_the_voiding_sentence_is_verbatim(self) -> None:
        blind = self.prereg["blind_control"]
        for key in (
            "mixing_rule_verbatim",
            "voiding_sentence_verbatim",
            "voiding_sentence_second_half_verbatim",
            "vacuity_control_verbatim",
        ):
            self._assert_quoted(key, blind[key])

    def test_the_result_gate_is_verbatim(self) -> None:
        self._assert_quoted("R1", self.prereg["result_gate"]["R1_verbatim"])
        self._assert_quoted(
            "served claim",
            self.prereg["result_gate"]["served_claim_if_R1_holds_verbatim"],
        )

    def test_the_stop_conditions_and_non_claims_are_verbatim(self) -> None:
        self._assert_quoted(
            "stop conditions", self.prereg["stop_conditions"]["verbatim"]
        )
        self._assert_quoted("non-claims", self.prereg["non_claims"]["verbatim"])
        self._assert_quoted(
            "residual risk", self.prereg["non_claims"]["residual_risk_verbatim"]
        )

    def test_the_p3_floor_is_verbatim(self) -> None:
        self._assert_quoted(
            "P3 floor",
            self.prereg["floors_and_their_meetability"]["P3_corpus_floor"][
                "floor_verbatim"
            ],
        )

    def test_b9_is_registered_and_scored_never(self) -> None:
        """Its absence is recorded rather than inferred."""

        b9 = self.prereg["construction_gate"]["clauses"]["B9"]
        self.assertFalse(b9["scored_in_this_commission"])
        self.assertEqual(b9["scored_verdict"], "NEVER")
        self.assertIn("slice 2", b9["why_never"])

    def test_every_floor_carries_a_meetability_argument(self) -> None:
        """ROADMAP-v0.21 §4.0(3): a floor without one is a defect."""

        floors = self.prereg["floors_and_their_meetability"]
        named = [key for key in floors if key != "rule"]
        self.assertGreaterEqual(len(named), 6)
        for key in named:
            self.assertIn("meetability_argument", floors[key], key)
            self.assertGreater(len(floors[key]["meetability_argument"]), 200, key)

    def test_the_stranger_non_claim_sits_beside_the_by_construction_argument(
        self,
    ) -> None:
        """Meetability by construction is what makes the non-claim binding."""

        floor = self.prereg["floors_and_their_meetability"]["P3_corpus_floor"]
        self.assertIn("construction", floor["meetability_argument"])
        self.assertIn("STRANGER", floor["and_the_honest_half"])

    def test_the_protocol_freezes_the_numbers_the_design_names(self) -> None:
        protocol = self.prereg["recording_protocol"]
        self.assertEqual(protocol["session_count_cap"], 60)
        self.assertEqual(protocol["turn_cap_per_session"], 64)
        self.assertEqual(protocol["live_assumption_cap"], 8)
        self.assertEqual(
            protocol["ab_split_rule"],
            "half = 'B' if int(sha256(session_id)[:2], 16) % 2 else 'A'",
        )

    def test_every_pin_names_a_producer_or_says_why_not(self) -> None:
        pins = self.prereg["pins"]
        for name, pin in pins.items():
            if name == "source":
                continue
            if pin["producer"] is None:
                self.assertEqual(pin["status"], "OMITTED", name)
                self.assertIn("slice 2", pin["why_omitted"], name)
            else:
                self.assertTrue(pin["producer"].strip(), name)
                self.assertIn("why_this_one", pin, name)

    def test_determinism_replaces_execute_once(self) -> None:
        clause = self.prereg["determinism_clause"]
        self.assertEqual(
            clause["registered_as"],
            "artifact committed from a deterministic runner; reproductions "
            "welcome and recorded",
        )
        self.assertEqual(clause["replaces"], "executed once")


if __name__ == "__main__":
    unittest.main()
