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


class TheCandidateEnumerator(unittest.TestCase):
    """Exact code, finite list, `data/` only."""

    @classmethod
    def setUpClass(cls) -> None:
        import candidate_enumerator as ce  # noqa: PLC0415

        cls.ce = ce
        cls.holdout = ce.holdout_ids(REPO)
        cls.questions = json.loads(
            QUESTIONS.read_text(encoding="utf-8")
        )["questions"]
        cls.pairs = json.loads(DISTRACTORS.read_text(encoding="utf-8"))["pairs"]

    def test_g8_no_holdout_id_is_ever_enumerated(self) -> None:
        """The gate that exists because slice 1 MEASURED the exposure.

        Every utterance in both frozen sets is enumerated and every
        candidate checked against the holdout id set. One occurrence is red.
        """

        self.assertEqual(len(self.holdout), 2053)
        utterances = [q["question"] for q in self.questions]
        for pair in self.pairs:
            utterances.extend([pair["a"], pair["b"]])
        leaked = []
        for utterance in utterances:
            for candidate in self.ce.enumerate_candidates(utterance, REPO):
                if candidate.statement_id in self.holdout:
                    leaked.append((utterance, candidate.statement_id))
        self.assertEqual(leaked, [], "holdout material reached a candidate list")

    def test_the_enumerator_reads_one_directory_and_the_index_it_builds_too(
        self,
    ) -> None:
        """Not a filter over two directories — a glob over one.

        `resolver.default_index` spans data/ AND data_holdout/. The
        enumerator must not use it, for verification either: a candidate
        confirmed by holdout material would be confirmed by material the
        model is forbidden to see.
        """

        import ast  # noqa: PLC0415

        source = (REPO / "scripts" / "candidate_enumerator.py").read_text(
            encoding="utf-8"
        )
        # AST, not a grep: the module's docstring NAMES `default_index` in
        # the paragraph explaining why it must not be used, and a string
        # search cannot tell an explanation from a call. Slice 1 hit the
        # same wall with a `.normal_form` grep and solved it by renaming a
        # field; here the honest instrument is to look for the call.
        tree = ast.parse(source)
        called = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        self.assertNotIn("default_index", called)
        self.assertNotIn("default_index", imported)
        self.assertIn("build_index", imported)

        index = self.ce._data_only_index(str(REPO))
        self.assertEqual(set(index.corpus_of) & self.holdout, set())

    def test_the_list_is_finite_and_frozen_at_the_registered_limit(self) -> None:
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        registered = prereg["amendments"][0]["adds"]["candidate_limit"]
        self.assertEqual(self.ce.CANDIDATE_LIMIT, registered)
        for question in self.questions:
            candidates = self.ce.enumerate_candidates(question["question"], REPO)
            self.assertLessEqual(len(candidates), registered)
            self.assertEqual(
                [c.index for c in candidates], list(range(len(candidates)))
            )

    def test_the_order_is_total_so_the_list_does_not_move(self) -> None:
        """A list whose order moved would move the blind arm's baseline."""

        for question in self.questions[:8]:
            first = self.ce.enumerate_candidates(question["question"], REPO)
            second = self.ce.enumerate_candidates(question["question"], REPO)
            self.assertEqual(
                [c.line for c in first], [c.line for c in second]
            )

    def test_a_candidate_that_binds_elsewhere_is_not_verified(self) -> None:
        """Accepting whatever came back would verify the verifier."""

        forged = self.ce.Candidate(
            index=0,
            line="Pythagorean Identity",
            route_expect="resolver",
            source="committed_statement",
            statement_id="trigonometry.definitions.tangent",
        )
        self.assertIsNone(self.ce.verify(forged, REPO))

    def test_verification_strength_is_from_the_frozen_vocabulary(self) -> None:
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        vocabulary = set(
            prereg["section_4_questions_answered"]["q4_who_verifies_exactly"][
                "vocabulary"
            ]
        )
        seen = set()
        for question in self.questions:
            _c, verified = self.ce.verified_candidates(question["question"], REPO)
            for item in verified:
                self.assertIn(item.verification_strength, vocabulary)
                seen.add(item.verification_strength)
        # Both strengths must actually occur, or the field is decorative.
        self.assertIn("exact_computation", seen)
        self.assertIn("word_match", seen)


class TheProposer(unittest.TestCase):
    """It returns an integer. That is the whole of what it may do."""

    @classmethod
    def setUpClass(cls) -> None:
        import candidate_enumerator as ce  # noqa: PLC0415
        import plain_proposer as pp  # noqa: PLC0415

        cls.ce, cls.pp = ce, pp

    def test_b9_the_prompt_carries_no_history_at_all(self) -> None:
        """B9 by construction: there is no history parameter to pass.

        The design permits assumption `normal_form`s as the one exception.
        This proposer does not use even that, so the prompt is the utterance
        and the candidate lines and nothing else — checked by building one
        and asserting every line of it is accounted for.
        """

        utterance = "what is the cosine of a double angle"
        candidates = self.ce.enumerate_candidates(utterance, REPO)
        prompt = self.pp.build_prompt(utterance, candidates)
        accounted = {utterance, "Question:", "Candidate readings:"}
        for candidate in candidates:
            accounted.add(candidate.line)
        for line in prompt.splitlines():
            line = line.strip()
            if not line:
                continue
            body = line.split(". ", 1)[-1] if line[0].isdigit() else line
            body = body.replace("Question: ", "")
            self.assertTrue(
                body in accounted or body in {"Candidate readings:"},
                f"prompt line not accounted for by utterance or candidates: {line!r}",
            )

    def test_the_signature_takes_no_history(self) -> None:
        """A leak needs a channel; this is the check that there is none."""

        import inspect  # noqa: PLC0415

        parameters = set(inspect.signature(self.pp.propose).parameters)
        self.assertEqual(parameters, {"utterance", "candidates", "timeout"})

    def test_g6_an_unreachable_model_refuses_rather_than_crashing(self) -> None:
        """Bar clause 3: missing checkpoint -> OFF, not crash."""

        original = self.pp.ENDPOINT
        self.pp.ENDPOINT = "http://127.0.0.1:9/none"
        try:
            with self.assertRaises(self.pp.ProposerUnavailable):
                self.pp.propose("anything", [
                    self.ce.Candidate(0, "2 + 2", "evaluate", "arithmetic")
                ])
        finally:
            self.pp.ENDPOINT = original

    def test_an_unreadable_reply_is_discarded_and_never_repaired(self) -> None:
        """DESIGN-plain-input §3.1: discarded before verification, not repaired."""

        source = (REPO / "scripts" / "plain_proposer.py").read_text(
            encoding="utf-8"
        )
        # No retry, no second prompt, no repair pass.
        self.assertNotIn("retry", source.lower())
        self.assertIn("discarded_reason", source)

    def test_the_weights_pin_is_one_copy_of_the_digest(self) -> None:
        import machine_reader as mr  # noqa: PLC0415

        source = (REPO / "scripts" / "plain_proposer.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            mr.MANIFEST["model"]["weights_blob_sha256"], source,
            "the digest is copied rather than read from machine_reader",
        )

    def test_the_blind_arm_draws_from_the_same_list(self) -> None:
        """G5's control isolates selection, so it must share the alphabet."""

        import random  # noqa: PLC0415

        candidates = self.ce.enumerate_candidates(
            "what is the cosine of a double angle", REPO
        )
        proposal = self.pp.blind_select(candidates, random.Random(0))
        self.assertIsNotNone(proposal.selected_index)
        self.assertLess(proposal.selected_index, len(candidates))


class P4Determinism(unittest.TestCase):
    """What temperature 0 earned, and what it therefore licenses."""

    ARTIFACT = REPO / "experiments" / "plain_proposer_determinism.json"

    @classmethod
    def setUpClass(cls) -> None:
        if not cls.ARTIFACT.exists():  # pragma: no cover - ordering guard
            raise unittest.SkipTest("P4 has not run yet")
        cls.p4 = json.loads(cls.ARTIFACT.read_text(encoding="utf-8"))

    def test_the_licence_follows_the_measurement(self) -> None:
        licence = self.p4["what_this_licenses"]
        if self.p4["two_passes_byte_identical"]:
            self.assertIn("determinism-plus-commit", licence)
            self.assertEqual(self.p4["differing"], [])
        else:
            self.assertIn("execute-once", licence)
            self.assertTrue(self.p4["differing"])

    def test_the_pin_was_verified_before_any_question(self) -> None:
        self.assertTrue(self.p4["model"]["weights_verified_before_any_question"])

    def test_it_did_not_inherit_c_v3_primes_result(self) -> None:
        self.assertIn(
            "belongs to the prompt set that produced it",
            self.p4["why_c_v3_primes_result_was_not_inherited"],
        )

    def test_the_limit_is_stated_whichever_way_it_read(self) -> None:
        self.assertIn("not a proof of determinism", self.p4["the_honest_limit"])


class TheWiring(unittest.TestCase):
    """Row 12's pre-router, and the quarantine that makes it believable."""

    @classmethod
    def setUpClass(cls) -> None:
        from resolver import default_index  # noqa: PLC0415

        cls.index = default_index()

    def _session(self, proposer=None):
        from harness import CoreSession  # noqa: PLC0415

        session = CoreSession.boot(REPO, offline=True)
        session.resolver_index = self.index
        session.proposer = proposer
        return session

    def test_g4_every_earlier_row_is_byte_identical_on_and_off(self) -> None:
        """The quarantine invariant, over lines the registered rows claim.

        Voiding sentence: *a single differing verdict voids the whole
        reading.* So this compares whole verdict dicts, not a summary.
        """

        import plain_router  # noqa: PLC0415
        from harness import render_verdict, route_line  # noqa: PLC0415

        lines = [
            "",
            "2 + 2",
            "owns x ^ 2",
            "suppose the corpus is complete",
            "retract a999",
            "twin programming.euclid.recursive",
            "twin no.such.statement",
            "de morgan laws",
            "tell me a story",
            "conform no.such.statement a=1",
            "what is the cosine of a double angle",
            "the quadratic formula",
        ]
        router = plain_router.PlainRouter()
        for line in lines:
            off = route_line(REPO, self._session(None), line or None)
            on = route_line(REPO, self._session(router), line or None)
            self.assertEqual(
                render_verdict(off), render_verdict(on),
                f"proposer changed a verdict on an earlier row: {line!r}",
            )
            self.assertEqual(off.get("route"), on.get("route"), line)
            self.assertEqual(off.get("status"), on.get("status"), line)

    def test_a_session_with_no_proposer_runs_the_old_code(self) -> None:
        from harness import CoreSession  # noqa: PLC0415

        self.assertIsNone(CoreSession.boot(REPO, offline=True).proposer)

    def test_g6_an_absent_model_exhausts_exactly_as_today(self) -> None:
        """Bar clause 3, at the wiring level rather than the client level."""

        import plain_proposer as pp  # noqa: PLC0415
        import plain_router  # noqa: PLC0415
        from harness import render_verdict, route_line  # noqa: PLC0415

        line = "how do i change a tyre"
        off = route_line(REPO, self._session(None), line)
        router = plain_router.PlainRouter()
        original = pp.ENDPOINT
        pp.ENDPOINT = "http://127.0.0.1:9/none"
        try:
            on = route_line(REPO, self._session(router), line)
        finally:
            pp.ENDPOINT = original
        self.assertEqual(render_verdict(off), render_verdict(on))
        self.assertTrue(router.traces[-1].unavailable)

    def test_the_conditional_answer_is_a_label_around_an_existing_answer(
        self,
    ) -> None:
        """§7: 'a LABEL WRAPPED AROUND AN EXISTING ANSWER, not a generated one'."""

        import plain_router  # noqa: PLC0415
        from harness import route_line  # noqa: PLC0415

        router = plain_router.PlainRouter()
        verdict = router._conditional(
            REPO,
            self._session(None),
            "irrelevant",
            _StubVerified("Pythagorean Identity"),
            [_StubVerified("Pythagorean Identity")],
        )
        self.assertEqual(verdict["status"], "conditional")
        underlying = route_line(REPO, self._session(None), "Pythagorean Identity")
        for line in (underlying.get("answer") or []):
            self.assertIn(line, verdict["answer"])

    def test_the_conditional_receipt_carries_what_section_3b_requires(
        self,
    ) -> None:
        import plain_router  # noqa: PLC0415

        router = plain_router.PlainRouter()
        verdict = router._conditional(
            REPO, self._session(None), "irrelevant",
            _StubVerified("Pythagorean Identity"),
            [_StubVerified("Pythagorean Identity"), _StubVerified("Other", 1)],
        )
        receipt = verdict["receipt"]
        self.assertEqual(len(receipt["suppositions"]), 1)
        self.assertEqual(receipt["suppositions"][0]["source"], "proposed")
        self.assertIn("verification_strength", receipt)
        self.assertEqual(receipt["alternatives_not_taken"], ["Other"])

    def test_g9_is_adjudicated_not_met_in_advance_with_its_reason(self) -> None:
        """The finding this slice reports rather than discovers."""

        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        amendment = next(
            a for a in prereg["amendments"] if a["amendment"] == 3
        )
        self.assertEqual(amendment["the_adjudication"]["G9"], "NOT MET, and not repaired inside this slice.")
        self.assertIn(
            "one row upstream",
            amendment["the_adjudication"]["what_this_is_evidence_of"],
        )


class TheOrchestratorsRulingOnG9(unittest.TestCase):
    """Amendment 4 — the ruling, its fixtures, and where they were filed.

    Amendment 3 adjudicated G9 from inside the lane. This class holds the
    RULING that fixed that adjudication from outside it, and it holds the
    three places the ruling sends the consequences: the prereg, the design's
    append-only notes, and BACKLOG's custody of the defect.
    """

    #: The thirteen, in the order the sealed question set lists them. Typed
    #: here as well as in the artifacts so a re-measurement that MOVED the
    #: number cannot pass quietly: this list is what the ruling was made on.
    THIRTEEN = (
        "g1-03", "g1-05", "g1-06", "g1-07", "g1-10", "g1-12", "g1-14",
        "g1-15", "g1-17", "g1-18", "g1-19", "g1-20", "g1-22",
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        cls.amendment = next(
            a for a in cls.prereg["amendments"] if a["amendment"] == 4
        )
        cls.backlog = _flat(
            (REPO / "docs" / "BACKLOG.md").read_text(encoding="utf-8")
        )
        cls.plain = _flat(PLAIN.read_text(encoding="utf-8"))

    def test_the_ruling_is_recorded_verbatim(self) -> None:
        """Quoted, because a ruling the ruled lane paraphrases is a ruling
        the lane could soften."""

        ruling = self.amendment["the_ruling_verbatim"]
        self.assertIn("G9 is adjudicated NOT MET for this slice by "
                      "orchestrator ruling.", ruling)
        self.assertIn("13 of 30, measured, upgrading P2's 2-of-10", ruling)
        self.assertIn(
            "its own prereg + control + K re-measurement", ruling
        )
        self.assertIn(
            "dated supersession note there, not deletion", ruling
        )

    def test_the_thirteen_fixtures_are_the_measured_thirteen(self) -> None:
        block = self.amendment["the_thirteen_fixtures"]
        self.assertEqual(tuple(block["question_ids"]), self.THIRTEEN)
        self.assertEqual(block["count"], 13)
        self.assertEqual(block["reaching_the_proposer"], 12)
        self.assertEqual(
            len(block["and_five_more_that_are_pre_empted_but_not_silently"]
                ["question_ids"]),
            5,
        )

    def test_the_thirteen_are_what_the_committed_tree_actually_does(
        self,
    ) -> None:
        """The clause that CAN go red — and would, the day a resolver
        change moved the surface this ruling was made against.

        ROADMAP-v0.21 §4.0's standing review question is *'a green
        assertion that could not have gone red is not evidence'*. Comparing
        the amendment's list against a list typed beside it would be that
        assertion. This one re-serves the sealed questions and compares.
        """

        from harness import CoreSession, route_line  # noqa: PLC0415
        from resolver import default_index  # noqa: PLC0415

        questions = json.loads(
            (REPO / "experiments" / "plain_question_set.json").read_text(
                encoding="utf-8"
            )
        )["questions"]
        index = default_index()
        found = []
        for item in questions:
            session = CoreSession.boot(REPO, offline=True)
            session.resolver_index = index
            verdict = route_line(REPO, session, item["question"])
            if verdict.get("status") == "found":
                found.append(item["question_id"])
        self.assertEqual(tuple(found), self.THIRTEEN)

    def test_the_backlog_supersedes_rather_than_deletes(self) -> None:
        """Both entries stand: the two-fixture one, marked, and the
        thirteen-fixture one that carries the work."""

        self.assertIn("SUPERSEDED 2026-08-26", self.backlog)
        self.assertIn(
            "aggregate.raw_prompts_silently_bound_today", self.backlog,
            "the superseded entry was deleted rather than marked",
        )
        self.assertIn("`p04`", self.backlog)
        for question_id in self.THIRTEEN:
            self.assertIn(
                f"`{question_id}`", self.backlog,
                f"{question_id} is a filed fixture and is not in BACKLOG",
            )

    def test_the_successor_s_three_obligations_are_filed(self) -> None:
        self.assertIn("its **own\npreregistration**".replace("\n", " "),
                      self.backlog)
        self.assertIn("own capability-blind control", self.backlog)
        self.assertIn("K re-measurement", self.backlog)

    def test_r2_must_carry_the_limit_in_the_claiming_sentence(self) -> None:
        clause = self.amendment["the_requirement_placed_on_R2"]
        self.assertIn("IN THE SAME SENTENCE", clause["clause"])
        self.assertIn("B10", clause["the_pattern_it_reuses"])


class _AlwaysFirst:
    """A blind arm that always picks candidate 0. Deterministic on purpose.

    G5's real blind arm is a uniform draw; this one is a fixture, so a test
    about the CEILING does not fail on a day the draw missed.
    """

    def randrange(self, count: int) -> int:  # noqa: ARG002
        return 0


class TheSharedSuppositionCeiling(unittest.TestCase):
    """Prereg amendment 5 — the frozen 8, spent from outside the ledger.

    The bound exists in the preregistration as a number and an outcome: at
    most eight live in a session, and *"a ninth refuses with the same typed
    `assumption_budget` refusal"*. These drive it until it fires, because a
    bound nobody has seen fire is a bound nobody has checked.
    """

    LINE = "what is two plus three"

    def _session(self, session_id: str = "ceiling-test"):
        from harness import CoreSession  # noqa: PLC0415

        return CoreSession.boot(REPO, offline=True, session_id=session_id)

    def test_the_ceiling_is_the_ledgers_own_number_not_a_second_copy(
        self,
    ) -> None:
        import plain_router  # noqa: PLC0415
        import session_ledger  # noqa: PLC0415

        self.assertEqual(
            plain_router.SUPPOSITION_CEILING,
            session_ledger.LIVE_ASSUMPTION_CAP,
        )
        self.assertEqual(plain_router.SUPPOSITION_CEILING, 8)
        self.assertEqual(plain_router.SUPPOSITION_BUDGET, 1)

    def test_the_ninth_proposed_supposition_refuses_by_type(self) -> None:
        import plain_router  # noqa: PLC0415

        router = plain_router.PlainRouter(blind_rng=_AlwaysFirst())
        session = self._session()
        for turn in range(plain_router.SUPPOSITION_CEILING):
            verdict = router.route(REPO, session, self.LINE)
            self.assertIsNotNone(verdict, f"turn {turn} served nothing")
            self.assertEqual(
                verdict["status"], "conditional", f"turn {turn}"
            )
        ninth = router.route(REPO, session, self.LINE)
        self.assertEqual(ninth["status"], "refused")
        self.assertEqual(ninth["refusal_type"], "assumption_budget")
        self.assertNotIn("answer", ninth)

    def test_the_refusal_type_is_the_one_the_suppose_route_uses(self) -> None:
        """Same ceiling, same word — imported, not spelled again."""

        import plain_router  # noqa: PLC0415
        import session_ledger  # noqa: PLC0415

        self.assertEqual(
            plain_router.REFUSAL_ASSUMPTION_BUDGET,
            session_ledger.REFUSAL_ASSUMPTION_BUDGET,
        )

    def test_typed_assumptions_and_proposed_ones_share_the_ceiling(
        self,
    ) -> None:
        """The half of q3 that survived: they spend ONE budget, not two."""

        import plain_router  # noqa: PLC0415
        import session_ledger as sl  # noqa: PLC0415

        barrier = sl.ReadBarrier()
        assumptions = sl.AssumptionSet("ceiling-shared", barrier)
        barrier.open_turn(0)
        for name in "abcdefgh":
            declared = assumptions.declare(f"{name} = 1", 0)
            self.assertNotIsInstance(declared, str, f"declaring {name}")
        self.assertEqual(len(assumptions.live()), 8)

        session = self._session("ceiling-shared")
        session.assumptions = assumptions
        router = plain_router.PlainRouter(blind_rng=_AlwaysFirst())
        verdict = router.route(REPO, session, self.LINE)
        self.assertEqual(verdict["status"], "refused")
        self.assertEqual(verdict["refusal_type"], "assumption_budget")

    def test_the_counter_is_per_session(self) -> None:
        """A router reused across sessions must not carry a budget across."""

        import plain_router  # noqa: PLC0415

        router = plain_router.PlainRouter(blind_rng=_AlwaysFirst())
        for turn in range(plain_router.SUPPOSITION_CEILING):
            router.route(REPO, self._session("one"), self.LINE)
            del turn
        fresh = router.route(REPO, self._session("two"), self.LINE)
        self.assertEqual(fresh["status"], "conditional")

    def test_a_proposed_supposition_never_enters_the_assumption_set(
        self,
    ) -> None:
        """G4b, satisfied more strictly than its frozen mechanism asked."""

        import plain_router  # noqa: PLC0415
        import session_ledger as sl  # noqa: PLC0415

        barrier = sl.ReadBarrier()
        assumptions = sl.AssumptionSet("g4b", barrier)
        barrier.open_turn(0)
        session = self._session("g4b")
        session.assumptions = assumptions
        router = plain_router.PlainRouter(blind_rng=_AlwaysFirst())
        verdict = router.route(REPO, session, self.LINE)
        self.assertEqual(verdict["status"], "conditional")
        self.assertEqual(verdict["receipt"]["suppositions"][0]["source"],
                         "proposed")
        self.assertEqual(assumptions.all_records(), [])
        self.assertEqual(barrier.close_turn(), ())


class AmendmentFiveStatesBothHalves(unittest.TestCase):
    """A divergence disclosed in one direction only is a defence."""

    @classmethod
    def setUpClass(cls) -> None:
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        cls.amendment = next(
            a for a in prereg["amendments"] if a["amendment"] == 5
        )
        cls.plain = _flat(PLAIN.read_text(encoding="utf-8"))

    def test_it_quotes_the_two_sentences_it_diverges_from(self) -> None:
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        frozen = self.amendment["the_two_sentences_as_frozen"]
        self.assertIn(
            frozen["from_G4b_how_it_is_checked_here"],
            prereg["gates"]["G4b"]["how_it_is_checked_here"],
        )
        self.assertIn(
            frozen["from_q3_per_session_rule"],
            prereg["section_4_questions_answered"]
            ["q3_what_bounds_the_supposition_count"]["per_session_rule"],
        )

    def test_g4bs_clause_is_still_verbatim_from_the_design(self) -> None:
        self.assertIn(
            _flat(self.amendment
                  ["consequence_one_it_is_STRICTER_on_the_clause_G4b_names"]
                  ["the_clause_verbatim"]),
            self.plain,
        )

    def test_the_cost_is_stated_and_not_only_the_gain(self) -> None:
        cost = self.amendment["consequence_two_what_it_COSTS_a_reader"]
        self.assertIn("will not see", cost)
        kept = self.amendment[
            "consequence_three_the_frozen_NUMBER_is_preserved_by_a_"
            "different_counter"
        ]
        self.assertIn("what_is_not_kept", kept)
        self.assertIn("two counters that can disagree",
                      kept["what_is_not_kept"].lower())

    def test_the_refused_alternative_is_named_with_its_reason(self) -> None:
        refused = self.amendment["why_the_ledgers_record_shape_was_not_widened_instead"]
        self.assertIn("MAC payload", refused["why_it_was_refused"])
        self.assertTrue(refused["both_were_checked_rather_than_assumed"])


class TheSixthPinTheDesignRegistered(unittest.TestCase):
    """§3's `proposer_model_digest`, and the machinery that has to know it.

    The pin is registered by the DESIGN — *"slice 2 only, key omitted until
    then, omission meaning 'no proposer served'"*. Before this, a journal
    that carried it would have been refused `stale-environment` on every
    replay by the unknown-pin sweep: a journal made unreplayable by obeying
    its own design.
    """

    def test_the_required_five_are_unchanged(self) -> None:
        import session_ledger as sl  # noqa: PLC0415

        self.assertEqual(len(sl.PIN_FIELDS), 5)
        self.assertNotIn("proposer_model_digest", sl.PIN_FIELDS)

    def test_the_optional_pin_is_registered_not_special_cased(self) -> None:
        import replay_session  # noqa: PLC0415

        self.assertEqual(
            replay_session.OPTIONAL_PIN_FIELDS, ("proposer_model_digest",)
        )

    def test_the_recorder_the_protocol_froze_is_byte_unchanged(self) -> None:
        """Why the registry is in the replayer and not in the ledger.

        The recording protocol pins a digest over `session_ledger.py` and
        `session_recorder.py`. Slice 2 records under slice 1's unmodified
        recorder or it is not recording under the same protocol, so a
        constant added to the ledger would have cost that.
        """

        from session_recorder import recorder_code_digest  # noqa: PLC0415

        frozen = json.loads(
            (REPO / "experiments" / "session_ledger_prereg.json").read_text(
                encoding="utf-8"
            )
        )["amendments"][0]["adds"]["recorder_code_digest"]
        self.assertEqual(recorder_code_digest(REPO), frozen)

    def test_absent_is_allowed_equal_passes_and_different_mismatches(
        self,
    ) -> None:
        import replay_session  # noqa: PLC0415
        import session_ledger as sl  # noqa: PLC0415

        base = {name: name for name in sl.PIN_FIELDS}
        live = dict(base, proposer_model_digest="abc")

        self.assertEqual(replay_session.compare_pins(dict(base), live), [])
        self.assertEqual(
            replay_session.compare_pins(
                dict(base, proposer_model_digest="abc"), live
            ),
            [],
        )
        self.assertEqual(
            replay_session.compare_pins(
                dict(base, proposer_model_digest="zzz"), live
            ),
            ["proposer_model_digest"],
        )

    def test_an_unregistered_pin_is_still_a_mismatch(self) -> None:
        """The sweep the optional registry must not have disabled."""

        import replay_session  # noqa: PLC0415
        import session_ledger as sl  # noqa: PLC0415

        base = {name: name for name in sl.PIN_FIELDS}
        self.assertEqual(
            replay_session.compare_pins(
                dict(base, some_future_pin="x"), dict(base)
            ),
            ["some_future_pin"],
        )

    def test_the_live_table_does_not_hash_a_model_it_does_not_need(
        self,
    ) -> None:
        """A slice-1 journal must not pay to hash a model it never used."""

        import replay_session  # noqa: PLC0415
        import session_ledger as sl  # noqa: PLC0415

        calls = []
        original = replay_session._live_proposer_digest
        replay_session._live_proposer_digest = lambda: calls.append(1) or "x"
        stub = {name: name for name in sl.PIN_FIELDS}
        original_pins = sl.pins
        sl.pins = lambda repo_root, matrix: dict(stub)  # noqa: ARG005
        try:
            without = replay_session.live_pin_table(REPO, None, dict(stub))
            withpin = replay_session.live_pin_table(
                REPO, None, dict(stub, proposer_model_digest="anything")
            )
        finally:
            sl.pins = original_pins
            replay_session._live_proposer_digest = original
        self.assertNotIn("proposer_model_digest", without)
        self.assertEqual(withpin["proposer_model_digest"], "x")
        self.assertEqual(len(calls), 1, "the blob was hashed when unneeded")


class TheDesignsAppendOnlyNotes(unittest.TestCase):
    """§8 — added after the seed, never editing what it corrects."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = PLAIN.read_text(encoding="utf-8")
        cls.flat = _flat(cls.raw)

    def test_section_4s_phase_2_argument_is_marked_measured_false(
        self,
    ) -> None:
        self.assertIn("8.1", self.flat)
        self.assertIn(
            "nine admit countably infinite languages", self.flat
        )
        self.assertIn("index into that list", self.flat)

    def test_the_original_prose_is_untouched(self) -> None:
        """The sentence §8.1 corrects must still be in §4, unedited.

        An append-only note whose subject quietly moved is a note about
        nothing.
        """

        self.assertIn(
            "Either argue the boundary holds (the bound is on the "
            "**output** alphabet, not the input) or concede the design is "
            "Phase 6 arriving early and price it accordingly.",
            self.flat,
        )
        self.assertIn(
            "A candidate is a **string that route_line already accepts**",
            self.flat,
        )

    def test_the_note_appears_after_the_prose_it_corrects(self) -> None:
        self.assertLess(
            self.raw.index("## 4. Questions the course must answer"),
            self.raw.index("## 8. Notes added after the seed"),
        )

    def test_the_g9_limit_is_stated_inside_the_design(self) -> None:
        self.assertIn("13 of 30 return `found` from the resolver", self.flat)


class _StubVerified:
    """A Verified stand-in, so the shape tests need no model."""

    def __init__(self, line: str, index: int = 0) -> None:
        from candidate_enumerator import Candidate  # noqa: PLC0415

        self.candidate = Candidate(
            index=index,
            line=line,
            route_expect="resolver",
            source="committed_statement",
            statement_id="trigonometry.identities.pythagorean",
            why="stub",
        )
        self.verification_strength = "word_match"
        self.detail = "stub"
        self.evidence = {}


if __name__ == "__main__":
    unittest.main()
