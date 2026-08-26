#!/usr/bin/env python3
"""Slice 2 — plain input inside the session object.

`docs/DESIGN-plain-input.md` is the governing spec and
`docs/DESIGN-session-ledger.md` §5 completes it. These tests hold the
preregistration to the designs it quotes, and later hold the machinery to
the trust shape the preregistration froze.

The verbatim check is the same instrument slice 1 used, and it earned its
keep there twice — it caught a dropped `**` and a hyphenation artifact in
clauses that read correctly to a human eye.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

PLAIN = REPO / "docs" / "DESIGN-plain-input.md"
LEDGER = REPO / "docs" / "DESIGN-session-ledger.md"
PREREG = REPO / "experiments" / "plain_input_prereg.json"


def _flat(text: str) -> str:
    """Wrapping collapsed; a hyphen at a line break rejoins its word."""

    rejoined = re.sub(r"-\s*\n\s*", "-", text)
    return re.sub(r"\s+", " ", rejoined).strip()


class PreregIsVerbatim(unittest.TestCase):
    """Frozen clauses are quotations, not paraphrases."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        cls.plain = _flat(PLAIN.read_text(encoding="utf-8"))
        cls.ledger = _flat(LEDGER.read_text(encoding="utf-8"))

    def _quoted(self, label: str, clause: str, haystack: str) -> None:
        flat = _flat(clause)
        if flat in haystack:
            return
        self.fail(
            f"{label} is not verbatim in its design\n"
            f"  starts: {flat[:110]!r}\n"
            f"  ends:   {flat[-110:]!r}"
        )

    def test_every_gate_clause_is_verbatim(self) -> None:
        gates = self.prereg["gates"]
        for name in ("G1", "G2", "G3", "G4", "G4b", "G5", "G6", "G7"):
            self._quoted(name, gates[name]["clause_verbatim"], self.plain)

    def test_the_voiding_sentences_are_verbatim(self) -> None:
        gates = self.prereg["gates"]
        self._quoted("G3 voiding", gates["G3"]["voiding_sentence_verbatim"], self.plain)
        self._quoted("G4 voiding", gates["G4"]["voiding_sentence_verbatim"], self.plain)

    def test_b9_is_verbatim_from_the_ledger_design(self) -> None:
        self._quoted(
            "B9", self.prereg["gates"]["B9"]["clause_verbatim"], self.ledger
        )

    def test_the_section_4_questions_are_quoted_where_quoted(self) -> None:
        answers = self.prereg["section_4_questions_answered"]
        for key, block in answers.items():
            if key == "preamble" or "the_question_verbatim" not in block:
                continue
            self._quoted(key, block["the_question_verbatim"], self.plain)

    def test_a_quotation_is_a_quotation_and_not_a_span_of_the_document(
        self,
    ) -> None:
        """Containment alone cannot catch an OVER-broad quotation.

        Every contiguous span of the design is verbatim in the design, so a
        `_quoted` check passes just as happily on a whole section as on the
        sentence it was meant to be. This caught exactly that while the
        preregistration was being written: a `the_question_verbatim` field
        built by lifting between two markers ran from §1 to §4 and captured
        **26,657 characters**, and every verbatim test was green on it.

        A quoted clause is a clause: short enough to be one, and free of the
        section headings it would have to cross to be more.
        """

        def _clauses():
            gates = self.prereg["gates"]
            for name, gate in gates.items():
                for key in ("clause_verbatim", "voiding_sentence_verbatim"):
                    if key in gate:
                        yield f"{name}.{key}", gate[key]
            answers = self.prereg["section_4_questions_answered"]
            for name, block in answers.items():
                if isinstance(block, dict) and "the_question_verbatim" in block:
                    yield f"{name}.the_question_verbatim", block[
                        "the_question_verbatim"
                    ]

        for label, clause in _clauses():
            self.assertLess(
                len(clause), 1500,
                f"{label} is {len(clause)} characters — that is a span of the "
                "document, not a quotation of a clause",
            )
            self.assertNotIn(
                "## ", clause,
                f"{label} crosses a section heading, so it is quoting more "
                "than the clause it names",
            )

    def test_all_seven_questions_are_answered(self) -> None:
        """§4 lists seven; silence on any of them is not a disposition."""

        answers = self.prereg["section_4_questions_answered"]
        asked = [key for key in answers if key.startswith("q")]
        self.assertEqual(len(asked), 7, asked)
        for key in asked:
            self.assertTrue(answers[key].get("answer", "").strip(), key)

    def test_b9_is_now_scored(self) -> None:
        """Registered in slice 1 as NEVER; this slice is when it counts."""

        self.assertTrue(self.prereg["gates"]["B9"]["scored_in_this_commission"])

    def test_the_conditional_versus_clarify_question_is_adjudicated(self) -> None:
        """P2 did not settle it, so the prereg must — with P2 quoted."""

        block = self.prereg["the_conditional_versus_clarify_adjudication"]
        self._quoted(
            "P2's decision rule", block["p2_evidence_quoted"]["the_rule"], self.ledger
        )
        probe = json.loads(
            (REPO / "experiments" / "session_p2_separator_probe.json").read_text(
                encoding="utf-8"
            )
        )
        aggregate = probe["aggregate"]
        # The evidence quoted must be the evidence measured.
        self.assertIn(
            str(aggregate["prompts_with_a_separator"]),
            block["p2_evidence_quoted"]["what_p2_measured"],
        )
        self.assertIn(
            str(aggregate["prompts_with_a_separator_at_the_act_level"]),
            block["p2_evidence_quoted"]["what_p2_measured"],
        )
        self.assertTrue(block["the_rule_frozen_now"]["who_decides"].startswith(
            "exact code"
        ))

    def test_the_holdout_hazard_is_registered_with_its_measured_number(
        self,
    ) -> None:
        """G8 exists because slice 1 measured the exposure, not supposed it."""

        gate = self.prereg["gates"]["G8"]
        self.assertEqual(gate["standard"].split(".")[0], "ZERO occurrences")
        self.assertIn("2,053", gate["why_it_is_needed"])
        # And the number must still be true of the tree.
        from decompose import load_trees  # noqa: PLC0415
        from resolver import default_index  # noqa: PLC0415

        holdout = {node.statement_id for node in load_trees(REPO / "data_holdout")[0]}
        index = set(default_index().corpus_of)
        self.assertEqual(len(index & holdout), 2053)

    def test_the_model_pin_matches_the_committed_precedent(self) -> None:
        """One digest, read from where machine_reader already pins it."""

        import machine_reader  # noqa: PLC0415

        self.assertEqual(
            self.prereg["the_model_and_its_determinism"]["weights_blob_sha256"],
            machine_reader.MANIFEST["model"]["weights_blob_sha256"],
        )
        self.assertEqual(
            self.prereg["the_model_and_its_determinism"]["temperature"], 0
        )

    def test_the_supposition_bounds_reuse_the_ledgers_ceiling(self) -> None:
        import session_ledger  # noqa: PLC0415

        bounds = self.prereg["section_4_questions_answered"][
            "q3_what_bounds_the_supposition_count"
        ]
        self.assertEqual(bounds["per_answer"], 1)
        self.assertEqual(
            bounds["per_session"], session_ledger.LIVE_ASSUMPTION_CAP
        )

    def test_no_throughput_number_is_claimed(self) -> None:
        text = json.dumps(self.prereg)
        self.assertIn("must not appear in any sentence containing a K number", text)


if __name__ == "__main__":
    unittest.main()
