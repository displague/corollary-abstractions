#!/usr/bin/env python3
"""The live input loop — P-LS1–P-LS6 as executable checks.

`docs/DESIGN-live-session.md` §7 froze five predictions before the loop
existed. These tests are what keeps them true; §8 records the adjudication.

The routing decision is tested through `route_line`, which returns the
verdict as data, rather than by scraping stdout. Both are exercised: the
process-level tests below pipe one or more lines into `scripts/harness.py`,
so the original one-line contract and v0.13's visible multi-turn termination
are checked against the real binary, not only a callable helper.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from harness import (  # noqa: E402
    CoreSession,
    UNREGISTERED_PATH,
    read_one_line,
    render_verdict,
    route_line,
)

PY = sys.executable
HARNESS = REPO / "scripts" / "harness.py"
SEED_REPLACEMENT = "tests/fixtures/live_session_seed_replacement.json"


def run_harness(line: str | None) -> subprocess.CompletedProcess:
    """Run the real binary with `line` on stdin (None = closed stdin)."""
    return subprocess.run(
        [PY, str(HARNESS)],
        input="" if line is None else line + "\n",
        capture_output=True,
        text=True,
        cwd=REPO,
        timeout=600,
    )


class BootedSession(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.session = CoreSession.boot(REPO, offline=True)


class InteractiveProcess(BootedSession):
    """P-LS1/P-LS6 — structured turns until input reaches EOF."""

    def test_process_exits_zero_after_a_single_line(self) -> None:
        proc = run_harness("what is the airspeed velocity of an unladen swallow")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--- one typed line ---", proc.stdout)
        self.assertIn("status  :", proc.stdout)

    def test_boot_list_still_printed_before_the_verdict(self) -> None:
        """The reclamation appends to the boot list; it does not replace it."""
        proc = run_harness("anything at all")
        self.assertIn("corollary kernel (", proc.stdout)
        self.assertIn(") session", proc.stdout)
        self.assertIn("corpus.nodes", proc.stdout)
        self.assertLess(
            proc.stdout.index("corpus.nodes"),
            proc.stdout.index("--- one typed line ---"),
        )

    def test_a_second_line_is_dispatched_in_the_same_session(self) -> None:
        """P-LS6: the process consumes turns until its input reaches EOF."""
        proc = subprocess.run(
            [PY, str(HARNESS)],
            input="what is 2 + 2\nwhat is 3 + 3\n",
            capture_output=True, text=True, cwd=REPO, timeout=600,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.count("--- one typed line ---"), 2)
        self.assertIn("what is 2 + 2", proc.stdout)
        self.assertIn("what is 3 + 3", proc.stdout)

    def test_closed_stdin_is_a_waiting_verdict_not_a_traceback(self) -> None:
        proc = run_harness(None)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("status  : waiting", proc.stdout)
        self.assertNotIn("Traceback", proc.stderr)

    def test_read_one_line_reports_end_of_stream_as_none(self) -> None:
        self.assertIsNone(read_one_line(io.StringIO("")))
        self.assertEqual(read_one_line(io.StringIO("hello\nworld\n")), "hello")


class MultiTurnResolverContext(unittest.TestCase):
    """P-LS6 runtime: ASK state survives, narrows, and never guesses."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.session = CoreSession.boot(REPO, offline=True)

    def setUp(self) -> None:
        self.session.pending_candidates = ()
        self.session.pending_query = None
        self.session.pending_resolver = None
        self.session.context_hops = 0
        self.session.context_seen.clear()

    def test_second_content_word_narrows_to_one_and_quotes_the_corpus(self) -> None:
        first = route_line(REPO, self.session, "double factorial")
        self.assertEqual(first["status"], "waiting")
        self.assertEqual(len(self.session.pending_candidates), 2)

        second = route_line(REPO, self.session, "narrow word recursive")
        self.assertEqual(second["status"], "found")
        self.assertIn("programming.dfactorial.recursive", second["detail"])
        self.assertFalse(self.session.pending_candidates)

        from answer import records

        node, _corpus = records()["programming.dfactorial.recursive"]
        allowed = {
            node["title"],
            node["semantic_interpretation"]["statement_meaning"],
        }
        self.assertTrue(second["reading"])
        self.assertTrue(set(second["reading"]) <= allowed)

    def test_discipline_followup_reduces_six_candidates_to_one(self) -> None:
        first = route_line(REPO, self.session, "entropy in thermodynamics")
        self.assertEqual(len(self.session.pending_candidates), 6)
        second = route_line(
            REPO, self.session, "narrow discipline machine_learning"
        )
        self.assertEqual(second["status"], "found")
        self.assertIn("ml.objective.token_cross_entropy_loss", second["detail"])

    def test_unhelpful_context_does_not_choose_a_candidate(self) -> None:
        route_line(REPO, self.session, "area of a circle")
        before = self.session.pending_candidates
        verdict = route_line(REPO, self.session, "narrow word unrelated")
        self.assertEqual(verdict["status"], "waiting")
        self.assertEqual(self.session.pending_candidates, before)

    def test_repeated_no_progress_names_a_cycle_and_terminates(self) -> None:
        route_line(REPO, self.session, "area of a circle")
        route_line(REPO, self.session, "narrow word unrelated")
        verdict = route_line(REPO, self.session, "narrow word unrelated")
        self.assertEqual(verdict["status"], "cycle")
        self.assertIn("no reading was chosen", verdict["detail"])
        self.assertFalse(self.session.pending_candidates)

    def test_four_distinct_no_progress_hops_name_the_ceiling(self) -> None:
        route_line(REPO, self.session, "area of a circle")
        verdict = None
        for word in ("unrelated", "unhelpful", "irrelevant", "unknown"):
            verdict = route_line(REPO, self.session, f"narrow word {word}")
        assert verdict is not None
        self.assertEqual(verdict["status"], "hop_ceiling")
        self.assertIn("visible hop ceiling 4", verdict["detail"])
        self.assertFalse(self.session.pending_candidates)

    def test_quote_less_singleton_cannot_bypass_the_ceiling(self) -> None:
        self.session.pending_candidates = ("synthetic.a", "synthetic.b")
        self.session.pending_query = "synthetic ambiguous query"
        self.session.pending_resolver = "synthetic"
        with (
            patch("harness._narrow_candidates", return_value=("synthetic.a",)),
            patch("harness._restatement", return_value=()),
        ):
            verdict = None
            for word in ("first", "second", "third", "fourth"):
                verdict = route_line(REPO, self.session, f"narrow word {word}")
        assert verdict is not None
        self.assertEqual(verdict["status"], "hop_ceiling")
        self.assertIn("unrenderable candidate", verdict["detail"])
        self.assertFalse(self.session.pending_candidates)

    def test_cancel_is_explicit_and_chooses_nothing(self) -> None:
        route_line(REPO, self.session, "area of a circle")
        verdict = route_line(REPO, self.session, "cancel")
        self.assertEqual(verdict["status"], "canceled")
        self.assertIn("no reading was chosen", verdict["detail"])
        self.assertFalse(self.session.pending_candidates)

    def test_registered_command_escapes_pending_context(self) -> None:
        route_line(REPO, self.session, "area of a circle")
        before = self.session.pending_candidates
        verdict = route_line(REPO, self.session, "suppose x=5, what is x^2")
        self.assertEqual(verdict["route"], "evaluate")
        self.assertEqual(verdict["status"], "solved")
        self.assertEqual(self.session.pending_candidates, before)

    def test_a_new_ask_replaces_the_pending_question(self) -> None:
        route_line(REPO, self.session, "area of a circle")
        verdict = route_line(REPO, self.session, "double factorial")
        self.assertEqual(verdict["status"], "waiting")
        self.assertEqual(
            set(self.session.pending_candidates),
            {
                "programming.dfactorial.iterative",
                "programming.dfactorial.recursive",
            },
        )

    def test_pending_ask_is_session_local(self) -> None:
        other = CoreSession.boot(REPO, offline=True)
        route_line(REPO, self.session, "area of a circle")
        self.assertTrue(self.session.pending_candidates)
        self.assertFalse(other.pending_candidates)

    def test_real_process_stops_after_named_cycle(self) -> None:
        proc = subprocess.run(
            [PY, str(HARNESS), "--offline"],
            input=(
                "area of a circle\n"
                "narrow word unrelated\n"
                "narrow word unrelated\n"
                "what is 2 + 2\n"
            ),
            capture_output=True,
            text=True,
            cwd=REPO,
            timeout=600,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.count("--- one typed line ---"), 3)
        self.assertIn("status  : cycle", proc.stdout)
        self.assertNotIn("what is 2 + 2", proc.stdout)


class UnregisteredTextNeverVerifies(BootedSession):
    """P-LS2 — a sentence no path claims asks or is exhausted."""

    def test_free_text_reaches_a_program_and_names_what_it_lacks(self) -> None:
        """Either a resolver claims it, or the dispatcher abstains by name.

        This asserted `dispatcher` until v0.13 gave free text a resolver to
        reach. The invariant that mattered was never "the dispatcher runs" —
        it was "unclaimed text is not answered from nowhere", and that is
        what is checked here.
        """
        verdict = route_line(REPO, self.session, "why does this corpus exist")
        self.assertIn(verdict["route"], {"dispatcher", "resolver"})
        if verdict["route"] == "dispatcher":
            self.assertEqual(verdict["missing_capability"], UNREGISTERED_PATH)
        else:
            self.assertTrue(verdict.get("answer"))

    def test_free_text_is_never_reported_as_verified_or_proven(self) -> None:
        """`solved` is now reachable, and only where something was settled.

        v0.13 gave the prompt exact arithmetic, so `prove that 2 + 2 = 4` is
        answered by computing it — honestly, and disclosed as arithmetic
        rather than as a proof. What must never appear is `verified` or
        `proven`, which would claim a certificate the system does not hold.
        Text that is merely matched against corpus words must not reach
        `solved` either; that is asserted separately below.
        """
        for line in (
            "prove that 2 + 2 = 4",
            "the corpus contains a proof of the Riemann hypothesis",
            "yes",
        ):
            with self.subTest(line=line):
                verdict = route_line(REPO, self.session, line)
                self.assertNotIn(
                    verdict["status"].lower(), {"verified", "proven"}
                )

    def test_word_matching_alone_never_reports_solved(self) -> None:
        """Resolution locates a statement; it does not settle anything."""
        for line in (
            "the corpus contains a proof of the Riemann hypothesis",
            "explain goedel's theorem",
        ):
            with self.subTest(line=line):
                verdict = route_line(REPO, self.session, line)
                if verdict["route"] == "resolver":
                    self.assertIn(verdict["status"], {"found", "waiting"})

    def test_the_refusal_text_comes_from_the_dispatcher(self) -> None:
        """Not a paraphrase written in harness.py."""
        verdict = route_line(REPO, self.session, "an unclaimed need")
        self.assertIn(UNREGISTERED_PATH, verdict["detail"])
        self.assertIn("register", verdict["detail"].lower())


class TypedPathReachesTheWriteGate(BootedSession):
    """P-LS3 — seed_ownership, and a byte-identical tree."""

    def test_seed_replacing_proposal_refuses_at_seed_ownership(self) -> None:
        verdict = route_line(REPO, self.session, SEED_REPLACEMENT)
        self.assertEqual(verdict["route"], "write_gate")
        self.assertEqual(verdict["status"], "REFUSED")
        # The gate's own check name, verbatim.
        self.assertEqual(verdict["detail"], "candidate refused at seed_ownership")

    def test_the_gate_reports_the_tree_byte_identical(self) -> None:
        verdict = route_line(REPO, self.session, SEED_REPLACEMENT)
        self.assertIn("working_tree_byte_identical=True", verdict["evidence"])

    def test_no_file_changes_and_no_staging_receipt_is_written(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=REPO,
        ).stdout
        route_line(REPO, self.session, SEED_REPLACEMENT)
        after = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=REPO,
        ).stdout
        self.assertEqual(before, after)

    def test_the_fixture_is_a_real_seed_replacement(self) -> None:
        """Vacuity guard: the refusal must be about ownership, not a typo.

        If the fixture stopped naming a committed seed that owns a corpus,
        the gate would refuse at some earlier check and this class would
        still be green while testing nothing.
        """
        payload = json.loads((REPO / SEED_REPLACEMENT).read_text(encoding="utf-8"))
        self.assertEqual(payload["corpus"], "number_theory")
        self.assertTrue((REPO / payload["seed_script"]).is_file())
        self.assertTrue((REPO / "data" / payload["corpus"] / "nodes.json").is_file())


class DoesNotReplayTheRecording(BootedSession):
    """P-LS4 — the loop is not a costume over harness_session.json."""

    def test_harness_never_reads_the_recorded_session(self) -> None:
        source = (REPO / "scripts" / "harness.py").read_text(encoding="utf-8")
        self.assertNotIn("harness_session", source)

    def test_a_line_in_no_recorded_leg_still_reaches_a_program(self) -> None:
        recording = json.loads(
            (REPO / "experiments" / "harness_session.json").read_text(encoding="utf-8")
        )
        blob = json.dumps(recording)
        line = "a sentence that appears in no recorded leg whatsoever"
        self.assertNotIn(line, blob)
        verdict = route_line(REPO, self.session, line)
        # The claim is that a NON-recorded line still reaches a real program,
        # not that it reaches one particular program.
        self.assertIn(verdict["route"], {"dispatcher", "resolver"})


class FillsNoSlotThePersonDidNotType(BootedSession):
    """P-LS5 — a pause binds nothing."""

    def test_waiting_verdict_binds_no_line_and_no_route(self) -> None:
        verdict = route_line(REPO, self.session, None)
        self.assertIsNone(verdict["line"])
        self.assertEqual(verdict["route"], "none")
        self.assertEqual(verdict["status"], "waiting")

    def test_empty_line_is_also_a_pause_not_a_default(self) -> None:
        verdict = route_line(REPO, self.session, "")
        self.assertIsNone(verdict["line"])
        self.assertEqual(verdict["route"], "none")

    def test_rendered_pause_names_no_value(self) -> None:
        rendered = "\n".join(render_verdict(route_line(REPO, self.session, None)))
        self.assertIn("(none typed)", rendered)
        self.assertNotIn(UNREGISTERED_PATH, rendered)


class OwnershipIsTheFirstSolve(BootedSession):
    """The exact lookup — the only route that may end `solved`."""

    def test_a_hosted_part_solves_with_counts(self) -> None:
        verdict = route_line(REPO, self.session, "owns x ^ 2")
        self.assertEqual(verdict["route"], "ownership")
        self.assertEqual(verdict["status"], "solved")
        self.assertIn("statements host", verdict["detail"])

    def test_the_answer_names_the_corpora(self) -> None:
        verdict = route_line(REPO, self.session, "owns SIN(x) ^ 2")
        joined = "\n".join(verdict["answer"])
        self.assertIn("skeleton", joined)
        self.assertIn("lean_workbook", joined)

    def test_an_unhosted_part_is_exhausted_not_solved(self) -> None:
        """A lookup that finds nothing must not dress up as an answer."""
        verdict = route_line(REPO, self.session, "owns ACKERMANN(x, y)")
        self.assertEqual(verdict["status"], "exhausted")

    def test_a_bare_variable_is_refused(self) -> None:
        """Every statement hosts `x`; answering 12,777 is not an answer."""
        verdict = route_line(REPO, self.session, "owns x")
        self.assertEqual(verdict["status"], "refused")

    def test_unparseable_query_is_refused_not_guessed(self) -> None:
        verdict = route_line(REPO, self.session, "owns ((((")
        self.assertEqual(verdict["status"], "refused")
        self.assertIn("template expression", verdict["detail"])

    def test_english_does_not_reach_the_lookup(self) -> None:
        """`owns` is a command word, not comprehension.

        This is the costume guard: if a phrasing that merely *contains*
        the word started solving, the route would be pretending to read
        English.
        """
        verdict = route_line(REPO, self.session, "who owns x^2?")
        self.assertEqual(verdict["route"], "dispatcher")
        self.assertEqual(verdict["status"], "exhausted")

    def test_the_lookup_agrees_with_the_committed_measurement(self) -> None:
        """Vacuity guard with an external oracle.

        `DESIGN-heldout-recovery.md` §1 records 6,870 Lean-workbook hosts
        for the most common subterm. The lookup is a different code path
        to the same fact; if it drifts, one of them is wrong.
        """
        from ownership import lookup  # noqa: PLC0415

        answer = lookup("x ^ 2", REPO / "data")
        by_corpus = dict(answer.by_corpus)
        self.assertEqual(by_corpus["lean_workbook.ground.v1"], 6870)

    def test_solved_requires_the_subsystem_to_have_registered(self) -> None:
        """The gate is the real boot matrix, not an assumption."""
        from ownership import REQUIRES_SUBSYSTEM  # noqa: PLC0415

        self.assertIn(REQUIRES_SUBSYSTEM, self.session.matrix.registered_ids())


class RoutingIsAClosedForm(BootedSession):
    """The path/text split is computed, never guessed."""

    def test_a_question_with_windows_illegal_characters_is_text(self) -> None:
        verdict = route_line(REPO, self.session, "why did the chicken cross the road?")
        self.assertEqual(verdict["route"], "dispatcher")

    def test_a_nonexistent_json_path_still_reaches_the_gate(self) -> None:
        """So the gate's named refusal prints, not one invented here."""
        verdict = route_line(REPO, self.session, "staging/no_such_proposal.json")
        self.assertEqual(verdict["route"], "write_gate")
        self.assertEqual(verdict["status"], "REFUSED")


if __name__ == "__main__":
    unittest.main()
