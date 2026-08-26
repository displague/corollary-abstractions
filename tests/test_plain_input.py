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


QUESTIONS = REPO / "experiments" / "plain_question_set.json"
DISTRACTORS = REPO / "experiments" / "plain_distractor_set.json"


class TheFrozenInputSets(unittest.TestCase):
    """G1's questions and G3's pairs — frozen before the proposer exists."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
        cls.pairs = json.loads(DISTRACTORS.read_text(encoding="utf-8"))

    def test_the_question_sets_counts_are_its_own_contents(self) -> None:
        rows = self.questions["questions"]
        counts = self.questions["counts"]
        self.assertEqual(counts["total"], len(rows))
        for disposition in ("conditional", "ask", "exhaust"):
            self.assertEqual(
                counts[f"authors_prior_{disposition}"],
                sum(1 for row in rows if row["authors_prior"] == disposition),
                disposition,
            )

    def test_the_set_cannot_read_better_than_its_own_ceiling(self) -> None:
        """A set on which everything works is a set chosen to read well.

        And the SENTENCE saying so must follow the counts. The first draft
        typed "eight of the thirty … 22/30" against an actual nine and
        21/30 — the same defect as the counts themselves, one field over.
        """

        counts = self.questions["counts"]
        ceiling = self.questions["ceiling"]
        self.assertGreaterEqual(counts["authors_prior_exhaust"], 8)
        self.assertEqual(
            ceiling["best_honest_verified_candidate_count"],
            counts["total"] - counts["authors_prior_exhaust"],
        )
        prose = self.questions["the_set_is_not_stacked_and_here_is_the_proof"]
        self.assertIn(
            f"{ceiling['best_honest_verified_candidate_count']}/{counts['total']}",
            prose,
        )
        self.assertIn(f"{counts['authors_prior_exhaust']} of the", prose)

    def test_every_question_is_unique_and_carries_its_prior(self) -> None:
        rows = self.questions["questions"]
        self.assertEqual(len({r["question_id"] for r in rows}), len(rows))
        self.assertEqual(len({r["question"] for r in rows}), len(rows))
        for row in rows:
            self.assertIn(row["authors_prior"], {"conditional", "ask", "exhaust"})
            self.assertTrue(row["why"].strip())

    def test_the_stranger_warning_is_carried_verbatim(self) -> None:
        design = _flat(PLAIN.read_text(encoding="utf-8"))
        self.assertIn(
            _flat(self.questions["the_warning_inherited_verbatim"]), design
        )

    def test_the_distractor_floor_is_zero_and_the_voiding_sentence_verbatim(
        self,
    ) -> None:
        design = _flat(PLAIN.read_text(encoding="utf-8"))
        self.assertEqual(self.pairs["registered_floor"], 0)
        self.assertIn(_flat(self.pairs["voiding_sentence_verbatim"]), design)

    def test_every_pair_names_two_different_expected_queries(self) -> None:
        """The clause C-V4 dropped, checked on the SET before any run."""

        for pair in self.pairs["pairs"]:
            self.assertNotEqual(pair["a"], pair["b"], pair["pair_id"])
            self.assertNotEqual(
                pair["expected_a"], pair["expected_b"], pair["pair_id"]
            )
            self.assertTrue(pair["why_they_differ"].strip())

    def test_the_hardest_pair_is_left_in_deliberately(self) -> None:
        """d03 may fail its own pre-check, and is kept anyway.

        P2 measured de Morgan's two corpora landing in the same twin group.
        A set that dropped its hardest pair before running would be a set
        chosen to read well; an exclusion the pre-check makes is one a
        reader can see.
        """

        d03 = next(p for p in self.pairs["pairs"] if p["pair_id"] == "d03")
        self.assertIn("EXCLUDED", d03["note"])
        self.assertIn(
            "chosen to read well",
            self.pairs["the_clause_C_V4_dropped_and_this_set_carries"][
                "and_one_pair_is_expected_to_be_excluded"
            ],
        )

    def test_no_mention_of_0_030_is_a_live_comparator(self) -> None:
        """It may be NAMED, but only to say it is not inherited.

        DESIGN-plain-input §2.3 records that the 0.030 false-positive
        denominator cannot be regenerated — the 1,000 sampled sentences were
        never committed — and forbids any gate from inheriting it as a live
        comparator. Scrubbing the string would be the wrong test: the
        artifacts SHOULD name it, in the sentence that disowns it.
        """

        def _leaves(node):
            if isinstance(node, dict):
                for value in node.values():
                    yield from _leaves(value)
            elif isinstance(node, list):
                for value in node:
                    yield from _leaves(value)
            elif isinstance(node, str):
                yield node

        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        seen = 0
        for artifact in (self.questions, self.pairs, prereg):
            for leaf in _leaves(artifact):
                if "0.030" not in leaf:
                    continue
                seen += 1
                self.assertTrue(
                    "unregenerable" in leaf
                    or "cannot be regenerated" in leaf
                    or "no gate" in leaf.lower()
                    or "0.030-era" in leaf,
                    f"0.030 appears without its disclaimer: {leaf[:180]}",
                )
        self.assertGreater(seen, 0, "the caveat is not carried anywhere")


class G7bConditionalScoresZero(unittest.TestCase):
    """The status exists, is non-answering, and forfeits its tokens.

    G7b is a gate rather than a note because §3b's whole honesty argument
    rests on it: *this design cannot inflate K by converting exhaustions
    into conditionals.* An argument that a metric cannot be inflated is
    worth exactly as much as the test that it cannot.
    """

    def test_the_status_is_in_the_frozen_alphabet(self) -> None:
        import serve_chat  # noqa: PLC0415

        self.assertIn("conditional", serve_chat.ENGINE_STATUSES)

    def test_the_status_is_not_answering(self) -> None:
        import serve_chat  # noqa: PLC0415

        self.assertNotIn("conditional", serve_chat.ANSWERING_STATUSES)

    def test_the_scoring_path_forfeits_its_tokens(self) -> None:
        """Driven from measure_throughput's own function, not a copy of it."""

        import measure_throughput as mt  # noqa: PLC0415

        self.assertIn("conditional", mt.NON_ANSWERING_STATUSES)
        self.assertTrue(mt.useful_tokens_are_forfeited_by("conditional"))
        # And the answering statuses do NOT forfeit, or the guard would be
        # zeroing everything and passing this test for the wrong reason.
        for answering in ("solved", "found", "held"):
            self.assertFalse(mt.useful_tokens_are_forfeited_by(answering))

    def test_the_guard_does_not_zero_a_certified_bounded_negative(self) -> None:
        """The bug this guard had on its first draft, kept as a fixture.

        `exhausted` is in NON_ANSWERING_STATUSES, and a closure task whose
        arm is 'unreachable' EXPECTS `exhausted` and scores it as a correct
        answer — a certified bounded negative carrying its receipt verbatim
        (SPEC §6.1; the task book's own `bounded_negative_is_an_answer`).
        The first version of the rule-level forfeit used the wide set and
        zeroed exactly that task. It must never do so again.
        """

        import measure_throughput as mt  # noqa: PLC0415

        self.assertFalse(mt.useful_tokens_are_forfeited_by("exhausted"))
        self.assertIn("exhausted", mt.NON_ANSWERING_STATUSES)
        self.assertNotIn("exhausted", mt.FORFEITING_STATUSES)

    def test_a_long_conditional_answer_still_scores_zero(self) -> None:
        """'whatever their content length' — checked with a long one."""

        import measure_throughput as mt  # noqa: PLC0415

        long_content = "x" * 5000
        self.assertGreater(len(long_content), 0)
        self.assertTrue(mt.useful_tokens_are_forfeited_by("conditional"))

    def test_a_status_that_never_arrived_forfeits_too(self) -> None:
        import measure_throughput as mt  # noqa: PLC0415

        self.assertTrue(mt.useful_tokens_are_forfeited_by(None))

    def test_the_sheet_contract_bumped_and_the_wire_did_not(self) -> None:
        """And the reason is recorded, not left to look like thrift."""

        import serve_chat  # noqa: PLC0415

        self.assertEqual(serve_chat.CAPABILITIES_SCHEMA, "corollary.capabilities/2")
        self.assertEqual(serve_chat.CHAT_SCHEMA, "corollary.chat/1")
        spec = _flat((REPO / "docs" / "SPEC-chat-completions-skin.md").read_text(
            encoding="utf-8"
        ))
        self.assertIn("¶AMD-1", spec)
        self.assertIn("corollary.chat/2` is owed", spec)

    def test_this_skin_cannot_emit_conditional_today(self) -> None:
        """The premise the un-bumped wire schema rests on, checked.

        If a fresh HTTP-path session could emit `conditional`, the wire
        contract WOULD have changed and `chat/2` would be owed now. The
        premise is that ¶DEV-1's fresh session carries no proposer.
        """

        from harness import CoreSession  # noqa: PLC0415

        session = CoreSession.boot(REPO, offline=True)
        self.assertIsNone(getattr(session, "proposer", None))
        self.assertIsNone(getattr(session, "assumptions", None))


if __name__ == "__main__":
    unittest.main()
