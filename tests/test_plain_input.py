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


class TheSliceTwoCorpusAndItsSeal(unittest.TestCase):
    """The corpus recorded under slice 1's protocol, and its own dated seal.

    Slice 1's seal is CLOSED and covers `v021-s*`. This one covers `v021-p*`
    and is checked the way slice 1's was: digests revalidated against the
    committed journals, caps obeyed, exclusions counted.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.seal = json.loads(
            (REPO / "experiments" / "plain_input_corpus_seal.json").read_text(
                encoding="utf-8"
            )
        )
        cls.prompts = json.loads(
            (REPO / "experiments" / "plain_input_prompts.json").read_text(
                encoding="utf-8"
            )
        )

    def test_every_journal_revalidates_against_the_seal(self) -> None:
        """B11's shape: the seal's digests are checked, not trusted."""

        import session_ledger as sl  # noqa: PLC0415

        for entry in self.seal["sessions"]:
            journal = (REPO / entry["journal"]).read_text(encoding="utf-8")
            self.assertEqual(
                sl.text_digest(journal), entry["journal_digest"],
                entry["session_id"],
            )
            reads = (REPO / entry["read_log"]).read_text(encoding="utf-8")
            self.assertEqual(
                sl.text_digest(reads), entry["read_log_digest"],
                entry["session_id"],
            )

    def test_the_prompts_artifact_is_pinned_by_the_seal(self) -> None:
        import session_ledger as sl  # noqa: PLC0415

        text = (REPO / "experiments" / "plain_input_prompts.json").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            sl.text_digest(text), self.seal["prompts_artifact_digest"]
        )

    def test_slice_1s_closed_corpus_is_not_touched(self) -> None:
        for entry in self.seal["sessions"]:
            self.assertTrue(entry["session_id"].startswith("v021-p"))
            self.assertNotIn("v021-s", entry["journal"])

    def test_the_protocol_caps_are_slice_1s_and_are_obeyed(self) -> None:
        protocol = self.seal["protocol"]
        ledger_prereg = json.loads(
            (REPO / "experiments" / "session_ledger_prereg.json").read_text(
                encoding="utf-8"
            )
        )["recording_protocol"]
        for key in (
            "session_count_cap", "turn_cap_per_session", "live_assumption_cap"
        ):
            self.assertEqual(protocol[key], ledger_prereg[key], key)
        self.assertLessEqual(
            len(self.seal["sessions"]), protocol["session_count_cap"]
        )
        for entry in self.seal["sessions"]:
            self.assertLessEqual(
                entry["turns"], protocol["turn_cap_per_session"],
                entry["session_id"],
            )

    def test_the_no_write_gate_rule_ran_and_its_count_is_published(
        self,
    ) -> None:
        counts = self.seal["counts"]
        self.assertIn(
            "sessions_excluded_by_the_no_write_gate_rule", counts
        )
        self.assertEqual(
            counts["sessions_excluded_by_the_no_write_gate_rule"],
            len(self.seal["excluded_sessions"]),
        )

    def test_the_header_carries_the_pin_slice_1_omitted(self) -> None:
        """§3's sixth pin, and it is the MEASURED weights digest."""

        import machine_reader  # noqa: PLC0415

        pinned = machine_reader.MANIFEST["model"]["weights_blob_sha256"]
        for entry in self.seal["sessions"]:
            journal = json.loads(
                (REPO / entry["journal"]).read_text(encoding="utf-8")
            )
            self.assertEqual(
                journal["header"]["pins"]["proposer_model_digest"], pinned,
                entry["session_id"],
            )

    def test_part_one_is_the_sealed_order_chunked_by_a_counter(self) -> None:
        """No question was placed to make a session read well."""

        questions = json.loads(
            (REPO / "experiments" / "plain_question_set.json").read_text(
                encoding="utf-8"
            )
        )["questions"]
        sealed = [item["question_id"] for item in questions]
        part_one = [
            entry for entry in self.seal["sessions"] if entry["part"] == 1
        ]
        flattened = [
            question_id
            for entry in part_one
            for question_id in entry["question_ids"]
        ]
        self.assertEqual(flattened, sealed)

    def test_part_two_questions_are_repeats_and_are_marked_as_such(
        self,
    ) -> None:
        part_two = [
            entry for entry in self.seal["sessions"] if entry["part"] == 2
        ]
        self.assertTrue(part_two)
        self.assertIn("part", self.seal["served_turns"][0])
        for entry in part_two:
            self.assertTrue(entry["assumptions"] > 0, entry["session_id"])


class TheDenominatorsBlock(unittest.TestCase):
    """Published, never summed — the block to read before any rate."""

    @classmethod
    def setUpClass(cls) -> None:
        seal = json.loads(
            (REPO / "experiments" / "plain_input_corpus_seal.json").read_text(
                encoding="utf-8"
            )
        )
        cls.block = seal["denominators"]

    def test_each_subset_names_its_members_and_its_size(self) -> None:
        for name, entry in self.block.items():
            if not isinstance(entry, dict) or "size" not in entry:
                continue
            self.assertEqual(
                entry["size"], len(entry["question_ids"]), name
            )
            self.assertIn("which_gates_score_over_it", entry)

    def test_the_three_subsets_are_the_measured_ones(self) -> None:
        self.assertEqual(
            self.block["resolver_found_before_the_proposer_is_consulted"][
                "size"
            ],
            13,
        )
        self.assertEqual(
            self.block["resolver_waiting_pre_empted_but_not_silently"]["size"],
            5,
        )
        self.assertEqual(
            self.block["proposer_reachable_remainder"]["size"], 12
        )
        self.assertEqual(self.block["exhaust_authored"]["size"], 9)

    def test_the_subsets_overlap_and_the_overlap_is_published(self) -> None:
        """Which is why the sizes cannot be added."""

        overlap = self.block["the_overlap_is_real_and_is_not_hidden"]
        self.assertTrue(
            overlap["exhaust_authored_that_the_resolver_pre_empted"],
            "an overlap of zero would make the never-sum rule decorative",
        )
        exhaust = set(self.block["exhaust_authored"]["question_ids"])
        reachable = set(
            self.block["proposer_reachable_remainder"]["question_ids"]
        )
        found = set(
            self.block["resolver_found_before_the_proposer_is_consulted"][
                "question_ids"
            ]
        )
        self.assertEqual(found & reachable, set())
        self.assertTrue(exhaust & reachable)

    def test_the_resolver_subsets_carry_no_gate_of_this_slice(self) -> None:
        """The standing defect is not absorbed by a gate that passes."""

        gates = self.block[
            "resolver_found_before_the_proposer_is_consulted"
        ]["which_gates_score_over_it"]
        self.assertIn("NONE", " ".join(gates))
        self.assertIn("G9", " ".join(gates))

    def test_every_gate_names_a_denominator(self) -> None:
        named = self.block["gate_denominators"]
        for gate in ("G1", "G2", "G3", "G5", "B9", "B10", "B12"):
            self.assertTrue(named.get(gate, "").strip(), gate)


class TheRegisteredRun(unittest.TestCase):
    """The run artifact, held to the preregistration it was scored against.

    These are not a second scoring. They check that the artifact reports
    every registered clause, that its verdicts are the ones its own numbers
    imply, and that the two red clauses are named rather than absorbed.
    """

    #: NOT `cls.run`: `TestCase.run` is the method unittest calls to run
    #: the test, and shadowing it with a dict makes every case in the
    #: class raise "'dict' object is not callable" before it starts.
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(
            (REPO / "experiments" / "plain_input_run.json").read_text(
                encoding="utf-8"
            )
        )
        cls.prereg = json.loads(PREREG.read_text(encoding="utf-8"))

    def test_every_registered_gate_is_reported(self) -> None:
        for name in self.prereg["gates"]:
            if name == "preamble":
                continue
            if name == "B10_and_B12_re_run":
                self.assertIn("B10", self.report["gates"])
                self.assertIn("B12", self.report["gates"])
                continue
            self.assertIn(name, self.report["gates"], name)

    def test_R2_fails_and_names_exactly_which_clauses(self) -> None:
        """A failing result gate that could not have named its failures
        would be a verdict without a reason."""

        gate = self.report["result_gate_R2"]
        self.assertEqual(gate["verdict"], "FAILS")
        self.assertEqual(
            gate["failed_clauses"],
            ["G5 collapses at or below half", "G9 repairs both fixtures"],
        )
        self.assertFalse(gate["is_it_licensed"])

    def test_the_licensing_sentence_carries_the_G9_limit_inside_it(
        self,
    ) -> None:
        """Prereg amendment 4's requirement, checked on the sentence."""

        sentence = self.report["result_gate_R2"][
            "the_sentence_that_WOULD_have_been_licensed"
        ]
        self.assertIn("13 of these 30", sentence)
        self.assertIn("UNREPAIRED by this slice", sentence)
        # And the limit must be inside the same sentence as the claim, not
        # in a following one: no full stop may separate them.
        claim = sentence.index("never as an unmarked answer")
        limit = sentence.index("13 of these 30")
        self.assertNotIn(". ", sentence[claim:limit])

    def test_what_happens_next_was_frozen_before_the_run(self) -> None:
        self.assertEqual(
            self.report["result_gate_R2"]["what_happens_now_frozen_before_the_run"],
            self.prereg["the_result_gate"]["if_R2_fails_on_any_clause"],
        )

    def test_G5_is_red_and_its_arms_are_published_with_the_rule(self) -> None:
        gate = self.report["gates"]["G5"]
        self.assertEqual(gate["verdict"], "RED")
        self.assertEqual(
            gate["registered_collapse_rule"],
            self.prereg["gates"]["G5"]["registered_collapse_rule"],
        )
        self.assertGreater(
            gate["blind_verified_selections"], gate["half_of_the_proposer"]
        )
        self.assertFalse(gate["collapsed"])

    def test_G5s_red_is_shown_not_to_be_a_lucky_draw(self) -> None:
        """A control that beats the model on one seeded draw invites the
        reading that the draw was lucky."""

        block = gate = self.report["gates"]["G5"]["analysis"]
        typical = block["the_draw_was_typical_not_lucky"]
        self.assertLess(
            abs(typical["observed"]
                - typical["expected_blind_verified_selections"]),
            4,
            "the observed blind draw is far from its own expectation",
        )
        del gate

    def test_G5s_mechanism_block_does_not_soften_the_verdict(self) -> None:
        block = self.report["gates"]["G5"]["analysis"][
            "the_mechanism_and_it_is_not_flattering_to_the_METRIC"
        ]
        self.assertIn(
            "does not soften one",
            block["and_this_changes_nothing_about_the_verdict"],
        )
        self.assertEqual(
            block["exhaust_prior_questions_the_model_selected_for"], 0
        )

    def test_B10_publishes_both_readings_and_the_fact_between_them(
        self,
    ) -> None:
        gate = self.report["gates"]["B10"]
        self.assertEqual(gate["slice_1_arm_unchanged"]["verdict"], "RED")
        self.assertEqual(gate["the_state_reading"]["verdict"], "GREEN")
        self.assertTrue(
            gate["the_measured_fact_that_explains_the_difference"][
                "every_slice_1_miss_is_a_turn_the_plain_input_route_served"
            ]
        )
        self.assertTrue(gate["slice_1_arm_unchanged"]["misses"])

    def test_B9_publishes_the_hits_it_explained_and_a_positive_control(
        self,
    ) -> None:
        gate = self.report["gates"]["B9"]
        self.assertEqual(gate["verdict"], "GREEN")
        self.assertEqual(gate["leaks"], [])
        self.assertTrue(gate["the_positive_control"]["detected"])
        self.assertEqual(gate["the_construction_arm"]["verdict"], "GREEN")

    def test_B9s_scanned_denominator_is_smaller_and_says_by_how_much(
        self,
    ) -> None:
        gate = self.report["gates"]["B9"]
        self.assertEqual(
            gate["prompts_scanned"]
            + gate["retained_records_with_no_prompt_to_scan"]["count"],
            gate["prompts_retained_in_total"],
        )

    def test_G3_ran_the_clause_C_V4_dropped(self) -> None:
        gate = self.report["gates"]["G3"]
        self.assertEqual(gate["verdict"], "GREEN")
        self.assertEqual(gate["pairs_collapsed"], 0)
        self.assertEqual(
            gate["pairs_scored"] + gate["pairs_excluded_by_the_pre_check"],
            gate["pairs_in_the_set"],
        )
        self.assertGreater(
            gate["pairs_excluded_by_the_pre_check"], 0,
            "a pre-check that excluded nothing would not have run",
        )

    def test_G7b_has_a_control_arm_that_scores_non_zero(self) -> None:
        """Otherwise a builder that zeroed everything would pass it."""

        gate = self.report["gates"]["G7b"]
        self.assertEqual(gate["verdict"], "GREEN")
        self.assertGreater(gate["solved_arm"]["useful_tokens"], 0)
        self.assertEqual(gate["conditional_arm"]["useful_tokens"], 0)
        self.assertEqual(
            gate["solved_arm"]["tokens"], gate["conditional_arm"]["tokens"]
        )

    def test_G9_is_reported_not_rescored(self) -> None:
        gate = self.report["gates"]["G9"]
        self.assertEqual(gate["verdict"], "NOT MET")
        self.assertIn("orchestrator ruling", gate["adjudicated"])
        amendment = next(
            a for a in self.prereg["amendments"] if a["amendment"] == 4
        )
        self.assertEqual(
            gate["the_ruling_verbatim"], amendment["the_ruling_verbatim"]
        )

    def test_the_run_reproduces_its_own_verdicts(self) -> None:
        block = self.report["reproduction"]
        self.assertTrue(block["prior_artifact_found"])
        self.assertTrue(block["verdicts_identical"])

    def test_the_instrument_fixes_are_disclosed_and_bounded(self) -> None:
        """Three instrument defects were fixed before this reading."""

        block = self.report["the_instrument_and_what_was_fixed_before_this_reading"]
        self.assertEqual(len(block["defects_found_and_fixed"]), 3)
        self.assertIn("no clause, no floor", block["what_was_NOT_changed"])

    def test_nothing_is_served_beyond_the_registration(self) -> None:
        block = self.report["where_the_claim_lives_and_what_is_served"]
        self.assertEqual(
            block["served_surface"],
            "none beyond what the preregistration registered",
        )
        from harness import CoreSession  # noqa: PLC0415

        self.assertIsNone(CoreSession.boot(REPO, offline=True).proposer)

    def test_the_findings_are_computed_and_name_the_sentences_they_break(
        self,
    ) -> None:
        found = self.report["findings"]
        f1 = found["F1_the_ask_branch_fires_on_questions_authored_to_exhaust"]
        self.assertEqual(f1["count"], len(f1["what_happened"]))
        self.assertGreater(f1["count"], 0)
        self.assertIn("Not open-domain", f1["the_design_sentence_this_contradicts"])
        self.assertIn(
            "g1-02",
            found["F2_the_designs_own_motivating_example_enumerates_nothing"][
                "questions_with_zero_candidates"
            ],
        )
        f3 = found["F3_verification_discarded_a_correct_selection"]
        self.assertEqual(f3["count"], len(f3["rows"]))

    def test_the_design_carries_the_contradicted_non_claim_as_a_note(
        self,
    ) -> None:
        """§8.3 — append-only, and the original sentence still stands."""

        plain = _flat(PLAIN.read_text(encoding="utf-8"))
        self.assertIn("8.3", plain)
        self.assertIn(
            "**Not open-domain.** Outside the corpus the honest output is "
            "still a refusal",
            plain,
        )
        self.assertIn("the **branch rule**, which fires on the count of", plain)
        self.assertIn("8.4", plain)
        self.assertIn("You cannot select what was never enumerated", plain)

    def test_the_run_states_that_the_silent_binding_is_unrepaired(
        self,
    ) -> None:
        joined = " ".join(self.report["non_claims"])
        self.assertIn("does not repair the silent binding", joined)


class ThePostRunCorrections(unittest.TestCase):
    """What adversarial review found after the artifact was committed.

    Three defects, none of which moves a verdict, and all three recorded in
    the artifact's own terms rather than repaired out of sight.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(
            (REPO / "experiments" / "plain_input_run.json").read_text(
                encoding="utf-8"
            )
        )
        cls.block = cls.report["post_run_corrections"]

    def test_the_corrections_do_not_move_the_verdict(self) -> None:
        gate = self.report["result_gate_R2"]
        self.assertEqual(gate["verdict"], "FAILS")
        self.assertEqual(
            gate["failed_clauses"],
            ["G5 collapses at or below half", "G9 repairs both fixtures"],
        )

    def test_H1_names_the_limb_that_was_not_executed(self) -> None:
        h1 = self.block[
            "H1_G8_was_reported_GREEN_without_executing_its_third_limb"
        ]
        self.assertIn("never executed", h1["what_the_runner_executed"])
        own = h1["and_this_repository_executed_it_too_with_its_own_denominator"]
        self.assertEqual(own["holdout_occurrences"], 0)
        self.assertEqual(own["statuses_that_were_not_found_or_solved"], 0)
        self.assertIn("108", h1["who_executed_the_missing_limb"])

    def test_M4_records_that_no_verdict_moved_and_the_raws_agree(self) -> None:
        """The claim is checkable, so it is checked rather than believed."""

        import plain_proposer as pp  # noqa: PLC0415

        prompts = json.loads(
            (REPO / "experiments" / "plain_input_prompts.json").read_text(
                encoding="utf-8"
            )
        )["prompts"]
        raws = [record["raw"] for record in prompts]
        raws += [row["raw"] for row in self.report["gates"]["G1"]["rows"]]
        for raw in raws:
            if not raw:
                continue
            self.assertIsNotNone(
                pp._SELECTION.match(raw),
                f"the anchored parser reads {raw!r} differently than the run "
                "did, so a verdict WOULD move",
            )

    def test_M2_publishes_the_ranks_and_the_mechanism(self) -> None:
        m2 = self.block["M2_the_enumerators_ranking_caps_G1s_ceiling_invisibly"]
        self.assertTrue(m2["and_both_verify"])
        self.assertIn("ascending TITLE", m2["the_mechanism"])
        self.assertIn(
            "all six NONEs verified correct refusals",
            m2["so_the_NONE_was_a_correct_refusal_against_a_mis_ranked_list"],
        )

    def test_L14_quotes_the_governance_clause_exactly(self) -> None:
        block = self.block[
            "L14_the_prereg_glosses_a_governance_clause_and_the_gloss_is_marked"
        ]
        roadmap = _flat(
            (REPO / "docs" / "ROADMAP-v0.21.md").read_text(encoding="utf-8")
        )
        self.assertIn(_flat(block["the_clause_verbatim"]), roadmap)


class G8sServedAnswerLimb(unittest.TestCase):
    """The limb the registered run did not execute, now executable.

    The reviewer ran this by hand before ruling. A check whose only record is
    a reviewer's message is a check the next run does not have.
    """

    def test_re_serving_every_verified_candidate_leaks_no_holdout_id(
        self,
    ) -> None:
        import candidate_enumerator as ce  # noqa: PLC0415
        import run_plain_gate  # noqa: PLC0415

        result = run_plain_gate._g8_served_answers(ce.holdout_ids(REPO))
        self.assertGreater(result["candidate_lines_reserved"], 100)
        self.assertEqual(result["occurrences"], [])
        self.assertEqual(result["statuses_that_were_not_found_or_solved"], [])

    def test_the_scan_would_have_caught_a_holdout_id_if_one_appeared(
        self,
    ) -> None:
        """The clause that can go red — otherwise zero proves nothing."""

        import candidate_enumerator as ce  # noqa: PLC0415

        holdout = ce.holdout_ids(REPO)
        self.assertGreater(len(holdout), 2000)
        planted = sorted(holdout)[0]
        body = f"found : {planted}\nreceipt : {{}}"
        self.assertTrue(
            any(statement_id in body for statement_id in holdout),
            "the scan's own rule does not detect a planted holdout id",
        )

    def test_the_reserve_index_asymmetry_is_filed_not_only_argued(
        self,
    ) -> None:
        backlog = _flat((REPO / "docs" / "BACKLOG.md").read_text(
            encoding="utf-8"
        ))
        self.assertIn("_reserve` re-serves a chosen candidate through the", backlog)
        self.assertIn("2,053 holdout ids", backlog)


class TheProposerParserDiscardsRatherThanRepairs(unittest.TestCase):
    """DESIGN-plain-input §3.1, made true of the code rather than of prose.

    The first parser searched for the first one- or two-digit token anywhere
    in a reply, so `suppose x = 5` yielded index 4. The trust shape held —
    an index is still all that acts — but the docstring and the design both
    say a reply outside the alphabet is *"discarded before verification, not
    repaired"*, and mining a numeral out of a sentence is repair.
    """

    #: The reviewer's adversarial replies. Every one must DISCARD.
    ADVERSARIAL = (
        "suppose x = 5",
        "I think the answer is 3 because the corpus says so",
        "Option 2 is best",
        "1 or 2",
        "none of these fit the question",
    )

    def _candidates(self):
        import candidate_enumerator as ce  # noqa: PLC0415

        return ce.enumerate_candidates("what is two plus three", REPO)

    def test_every_adversarial_reply_is_discarded(self) -> None:
        import plain_proposer as pp  # noqa: PLC0415

        for reply in self.ADVERSARIAL:
            self.assertIsNone(
                pp._SELECTION.match(reply),
                f"{reply!r} was read as a selection; the doctrine says "
                "discard, not repair",
            )

    def test_the_old_lenient_pattern_would_have_accepted_them(self) -> None:
        """Otherwise the fixture is asserting nothing about the fix."""

        import re  # noqa: PLC0415

        lenient = re.compile(r"\b(\d{1,2}|NONE)\b", re.IGNORECASE)
        accepted = [
            reply for reply in self.ADVERSARIAL if lenient.search(reply)
        ]
        self.assertEqual(len(accepted), len(self.ADVERSARIAL))

    def test_a_bare_selection_still_reads(self) -> None:
        import plain_proposer as pp  # noqa: PLC0415

        for reply, expected in (
            ("1", "1"), (" 7 ", "7"), ("12", "12"), ("3.", "3"),
            ("NONE", "NONE"), ("none", "none"),
        ):
            found = pp._SELECTION.match(reply)
            self.assertIsNotNone(found, reply)
            self.assertEqual(found.group(1), expected)

    def test_a_discarded_reply_selects_nothing_and_says_why(self) -> None:
        import plain_proposer as pp  # noqa: PLC0415

        original = pp.ENDPOINT
        pp.ENDPOINT = "http://127.0.0.1:9/none"
        try:
            with self.assertRaises(pp.ProposerUnavailable):
                pp.propose("anything", self._candidates())
        finally:
            pp.ENDPOINT = original

    def test_the_design_sentence_the_fix_makes_true(self) -> None:
        plain = _flat(PLAIN.read_text(encoding="utf-8"))
        self.assertIn(
            "anything else it emits is discarded before verification, not "
            "repaired",
            plain,
        )


class TheSuccessorAppendix(unittest.TestCase):
    """§8.6 — the four process notes, where the next author will read them."""

    def test_all_four_are_named(self) -> None:
        plain = _flat(PLAIN.read_text(encoding="utf-8"))
        self.assertIn("8.6", plain)
        for phrase in (
            "custodian outside the lane it rules on",
            "denominator set after partial results",
            "The runner lands before the reading",
            "Derive the chance rate from the verification cost",
        ):
            self.assertIn(phrase, plain, phrase)

    def test_the_chance_rate_note_carries_both_numbers(self) -> None:
        plain = _flat(PLAIN.read_text(encoding="utf-8"))
        self.assertIn("1/8 = 0.125", plain)
        self.assertIn("20.62/30", plain)


class TheSmallCorrectionsReviewFound(unittest.TestCase):
    """L8-L13: a miscounted note, a stale citation, an unnamed overlap, a
    filter looser than its key, and a digest promise CRLF would have broken."""

    def test_L8_the_question_sets_counts_note_is_corrected_beside_its_data(
        self,
    ) -> None:
        question_set = json.loads(
            (REPO / "experiments" / "plain_question_set.json").read_text(
                encoding="utf-8"
            )
        )
        counts = question_set["counts"]
        correction = question_set["counts_note_correction"]
        self.assertEqual(
            correction["the_corrected_triple"],
            [
                counts["authors_prior_conditional"],
                counts["authors_prior_ask"],
                counts["authors_prior_exhaust"],
            ],
        )
        # And the corrected triple is what the QUESTIONS say, not what the
        # counts block says — the same derivation the note congratulates.
        from collections import Counter  # noqa: PLC0415

        tally = Counter(
            item["authors_prior"] for item in question_set["questions"]
        )
        self.assertEqual(
            correction["the_corrected_triple"],
            [tally["conditional"], tally["ask"], tally["exhaust"]],
        )
        self.assertIn("16/6/8", question_set["counts_note"],
                      "the original sentence was edited rather than corrected")

    def test_L9_the_analysis_heading_counts_its_own_table(self) -> None:
        text = (REPO / "experiments" / "ANALYSIS.md").read_text(
            encoding="utf-8"
        )
        start = text.index("## NOTES: five claims in this slice's commit")
        section = text[start : start + 6000]
        rows = [
            line for line in section.splitlines()
            if line.startswith("| `") or line.startswith("| four commits")
        ]
        self.assertEqual(len(rows), 5)
        self.assertIn("Corrected in place 2026-08-26", section)

    def test_L10_the_spec_cites_route_line_where_it_now_lives(self) -> None:
        spec = (REPO / "docs" / "SPEC-chat-completions-skin.md").read_text(
            encoding="utf-8"
        )
        source = (REPO / "scripts" / "harness.py").read_text(
            encoding="utf-8"
        ).splitlines()
        start = next(
            index for index, line in enumerate(source, 1)
            if line.startswith("def route_line(")
        )
        end = next(
            index for index, line in enumerate(source, 1)
            if index > start and "**_route_dispatch(session, line)}" in line
        )
        self.assertIn(f"`scripts/harness.py:{start}-{end}`", spec)
        self.assertIn(f"`scripts/harness.py:{start}`", spec)
        main_line = next(
            index for index, line in enumerate(source, 1)
            if line.startswith("def main(")
        )
        self.assertIn(f"`scripts/harness.py:{main_line}`", spec)

    def test_L11_the_overlap_names_its_members_and_narrows_its_claim(
        self,
    ) -> None:
        seal = json.loads(
            (REPO / "experiments" / "plain_input_corpus_seal.json").read_text(
                encoding="utf-8"
            )
        )
        block = seal["denominators"]
        addendum = block["the_overlap_is_real_and_is_not_hidden"][
            "addendum_dated_2026_08_26"
        ]
        exhaust = set(block["exhaust_authored"]["question_ids"])
        reachable = set(
            block["proposer_reachable_remainder"]["question_ids"]
        )
        self.assertEqual(
            addendum["exhaust_authored_that_reach_the_proposer"],
            sorted(exhaust & reachable),
        )
        self.assertEqual(addendum["count"], 8)
        routing = addendum["the_routing_axis_partitions_exactly"]
        self.assertEqual(routing["sum"], 30)
        self.assertTrue(routing["pairwise_disjoint"])

    def test_L12_the_resolver_found_filter_checks_the_route_it_names(
        self,
    ) -> None:
        source = (REPO / "scripts" / "record_plain_corpus.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('row["status"] == "found" and row["route"] == "resolver"',
                      source)

    def test_L13_every_pinned_journal_hashes_from_its_RAW_bytes(self) -> None:
        """The seal promises a stranger can check offline with no key.

        `read_text` hides the problem: it translates CRLF on the way in, so a
        digest test that reads text passes on a checkout where the raw bytes
        would not. This one reads bytes, which is what a stranger does.
        """

        import hashlib  # noqa: PLC0415

        seal_path = REPO / "experiments" / "plain_input_corpus_seal.json"
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        for entry in seal["sessions"]:
            for path, key in (
                (entry["journal"], "journal_digest"),
                (entry["read_log"], "read_log_digest"),
            ):
                raw = (REPO / path).read_bytes()
                self.assertEqual(
                    hashlib.sha256(raw).hexdigest(), entry[key], path
                )
                self.assertNotIn(b"\r\n", raw, path)
        prompts = (REPO / "experiments" / "plain_input_prompts.json").read_bytes()
        self.assertEqual(
            hashlib.sha256(prompts).hexdigest(),
            seal["prompts_artifact_digest"],
        )

    def test_L13_the_paths_are_pinned_in_gitattributes(self) -> None:
        attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
        for path in (
            "experiments/sessions/**",
            "experiments/plain_input_prompts.json",
        ):
            self.assertIn(f"{path} text eol=lf", attrs)


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
