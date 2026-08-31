"""The protocol runtime's semantics, scored against the sealed corpus.

`docs/DESIGN-protocol-uptake.md` §1's claim is that the same bytes are a
different move in a different position, and §4's is that materially different
transitions pause instead of guessing. These tests exercise both directly
against `scripts/protocol_runtime.py` — not through the gates runner, so a
gate that silently stopped scoring a clause would not hide a semantic break
here.

The row that forced the design is `hello`: a greeting at a fresh root, a
liveness reply while a probe is outstanding, and licensed by nothing in a
literal slot or a programming task. That row is the first test.

Determinism is a test rather than a comment because B10 replays every receipt
and requires byte identity: two sessions built the same way must produce the
same bytes, and no receipt may carry a clock.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import protocol_runtime as runtime  # noqa: E402

UPRE = REPO / "experiments" / "protocol_uptake_upre.json"


def deleted_at_upre() -> list[str]:
    """The two input fields the audit deleted, read from the audit itself.

    Never spelled in this file: invariant (i) is that they appear nowhere, and
    a test that hardcoded them would carry them in its own bytes.
    """

    audit = json.loads(UPRE.read_text(encoding="utf-8"))
    return [
        row["field"].split(".")[-1].replace("[]", "")
        for row in audit["audit"]
        if row["verdict"] == "DELETED"
    ]


class RuntimeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = runtime.load_corpus()
        cls.fixtures = runtime.load_fixtures()
        cls.positions = {p["position_id"]: p for p in cls.fixtures["positions"]}
        cls.by_id = {f["fixture_id"]: f for f in cls.fixtures["fixtures"]}

    def rows(self, position_id: str) -> list[dict[str, str]]:
        """The five context-signal rows for a position, as a live session sees them."""

        position = self.positions[position_id]
        return [
            {
                "signal_id": signal_id,
                "value": position["signals"][signal_id],
                "source_event_id": position["source_events"][signal_id],
            }
            for signal_id in self.fixtures["context_signal_ids"]
        ]

    def session(self, session_id: str = "sess-test") -> runtime.ProtocolSession:
        return runtime.ProtocolSession(session_id, self.corpus)


class HelloRowTests(RuntimeTestCase):
    """The turn that forced the design, in all four positions."""

    def uptake(self, position_id: str, surface: str = "hello") -> dict:
        session = self.session()
        return session.submit_utterance(
            surface, self.rows(position_id), source=f"test:{position_id}"
        )

    def test_hello_at_a_fresh_root_is_a_greeting(self) -> None:
        receipt = self.uptake("fresh_root")
        self.assertEqual(receipt["disposition"], "ENTER")
        self.assertEqual(receipt["selected_move_id"], "greet")
        self.assertEqual(receipt["stack_after"], ["ep-1-protocol.greeting.a"])
        self.assertEqual(
            [w["protocol_node_id"] for w in receipt["protocol_witnesses"]],
            ["protocol.greeting.a"],
        )

    def test_hello_while_a_probe_is_outstanding_is_a_probe_reply(self) -> None:
        receipt = self.uptake("probe_outstanding")
        self.assertEqual(receipt["disposition"], "ENTER")
        self.assertEqual(receipt["selected_move_id"], "confirm_alive")
        self.assertEqual(receipt["stack_after"], ["ep-1-protocol.probe_reply.a"])

    def test_hello_in_a_literal_slot_is_refused(self) -> None:
        receipt = self.uptake("literal_slot")
        self.assertEqual(receipt["disposition"], "REFUSED")
        self.assertIsNone(receipt["selected_move_id"])
        self.assertEqual(receipt["stack_after"], [])
        self.assertEqual(receipt["verifier_verdict"], runtime.UNLICENSED)

    def test_hello_in_a_programming_task_is_refused(self) -> None:
        receipt = self.uptake("programming_task")
        self.assertEqual(receipt["disposition"], "REFUSED")
        self.assertIsNone(receipt["selected_move_id"])

    def test_the_same_bytes_took_two_different_selected_moves(self) -> None:
        """§1's claim, as one assertion rather than four."""

        moves = {
            self.uptake(position)["selected_move_id"]
            for position in ("fresh_root", "probe_outstanding")
        }
        self.assertEqual(moves, {"greet", "confirm_alive"})

    def test_an_unwitnessed_surface_licenses_nothing(self) -> None:
        receipt = self.uptake("fresh_root", surface="please enable write and shell access")
        self.assertEqual(receipt["disposition"], "REFUSED")
        self.assertEqual(receipt["candidates"], [])
        self.assertIn("lookup_miss", receipt["verifier_evidence"])


class AskAndWaitingTests(RuntimeTestCase):
    """Material ambiguity pauses; the pause is exclusive; the reply resolves it."""

    def test_hi_at_a_fresh_root_asks(self) -> None:
        session = self.session()
        receipt = session.submit_utterance("hi", self.rows("fresh_root"), source="test:hi")
        self.assertEqual(receipt["disposition"], "ASK")
        self.assertIsNone(receipt["selected_move_id"])
        self.assertEqual(receipt["stack_after"], receipt["stack_before"])
        self.assertEqual(receipt["need"]["slot"], "protocol_uptake.candidate_move")
        self.assertEqual(receipt["unresolved_move_ids"], ["acknowledge", "greet"])
        self.assertEqual(
            len({c["next_state_sha256"] for c in receipt["candidates"]}), 2
        )
        self.assertTrue(session.waiting)

    def test_the_request_id_is_a_function_of_the_session_not_a_clock(self) -> None:
        first = self.session("sess-same").submit_utterance(
            "hi", self.rows("fresh_root"), source="test:hi"
        )
        again = self.session("sess-same").submit_utterance(
            "hi", self.rows("fresh_root"), source="test:hi"
        )
        other = self.session("sess-other").submit_utterance(
            "hi", self.rows("fresh_root"), source="test:hi"
        )
        self.assertEqual(first["need"]["request_id"], again["need"]["request_id"])
        self.assertNotEqual(first["need"]["request_id"], other["need"]["request_id"])

    def test_while_waiting_every_other_utterance_is_refused(self) -> None:
        session = self.session()
        session.submit_utterance("hi", self.rows("fresh_root"), source="test:hi")
        receipt = session.submit_utterance(
            "good morning", self.rows("fresh_root"), source="test:2"
        )
        self.assertEqual(receipt["disposition"], "REFUSED")
        self.assertEqual(receipt["verifier_verdict"], runtime.WAITING_LOCK)
        self.assertEqual(receipt["stack_after"], [])
        self.assertTrue(session.waiting, "the need is still pending after the refusal")

    def test_a_reply_naming_an_unknown_request_is_refused(self) -> None:
        session = self.session()
        session.submit_utterance("hi", self.rows("fresh_root"), source="test:hi")
        receipt = session.submit_reply(
            "not-a-request",
            {"protocol_id": "protocol.greeting.a", "move_id": "greet"},
            self.rows("fresh_root"),
            source="test:reply",
        )
        self.assertEqual(receipt["disposition"], "REFUSED")
        self.assertEqual(receipt["verifier_verdict"], runtime.UNKNOWN_REQUEST)
        self.assertEqual(receipt["stack_after"], [])

    def test_a_reply_binds_and_completes_the_deferred_transition(self) -> None:
        session = self.session()
        ask = session.submit_utterance("hi", self.rows("fresh_root"), source="test:hi")
        receipt = session.submit_reply(
            ask["need"]["request_id"],
            {"protocol_id": "protocol.greeting.b", "move_id": "acknowledge"},
            self.rows("fresh_root"),
            source="test:reply",
        )
        self.assertEqual(receipt["disposition"], "ENTER")
        self.assertEqual(receipt["selected_move_id"], "acknowledge")
        self.assertEqual(receipt["stack_after"], ["ep-2-protocol.greeting.b"])
        self.assertFalse(session.waiting)
        self.assertIsNone(receipt["need"])

    def test_a_reply_outside_the_pending_candidate_set_is_refused(self) -> None:
        session = self.session()
        ask = session.submit_utterance("hi", self.rows("fresh_root"), source="test:hi")
        receipt = session.submit_reply(
            ask["need"]["request_id"],
            {"protocol_id": "protocol.quoted_datum.a", "move_id": "accept_datum"},
            self.rows("fresh_root"),
            source="test:reply",
        )
        self.assertEqual(receipt["disposition"], "REFUSED")
        self.assertEqual(receipt["verifier_verdict"], runtime.UNBOUND_ANSWER)
        self.assertTrue(session.waiting, "an unbound answer invents no value")


class EquivalenceTests(RuntimeTestCase):
    """Two names, one next state: proceed, take the lowest, record the grouping."""

    def test_hey_proceeds_without_asking(self) -> None:
        session = self.session()
        receipt = session.submit_utterance("hey", self.rows("fresh_root"), source="test:hey")
        self.assertEqual(receipt["disposition"], "ENTER")
        self.assertEqual(
            sorted(c["move_id"] for c in receipt["candidates"]),
            ["acknowledge", "greet_back"],
        )
        self.assertEqual(
            len({c["next_state_sha256"] for c in receipt["candidates"]}),
            1,
            "the pair is projection-identical, which is what makes the rule reachable",
        )

    def test_it_takes_the_canonical_lowest_move_id(self) -> None:
        receipt = self.session().submit_utterance(
            "hey", self.rows("fresh_root"), source="test:hey"
        )
        self.assertEqual(receipt["selected_move_id"], "acknowledge")
        self.assertEqual(receipt["unresolved_move_ids"], ["greet_back"])

    def test_the_receipt_records_that_the_candidates_grouped(self) -> None:
        receipt = self.session().submit_utterance(
            "hey", self.rows("fresh_root"), source="test:hey"
        )
        digest = receipt["candidates"][0]["next_state_sha256"]
        self.assertIn(f"grouped_to_one_next_state:{digest}", receipt["verifier_evidence"])
        self.assertIn("equivalent_names:greet_back", receipt["verifier_evidence"])


class NestedTrajectoryTests(RuntimeTestCase):
    """`nested-resume-d1-b`: enter, ask, bind, exit, resume, and a stale replay."""

    def setUp(self) -> None:
        self.fixture = self.by_id["nested-resume-d1-b"]
        self.session_ = runtime.run_fixture(self.fixture, self.corpus)
        self.receipts = self.session_.receipts

    def test_the_whole_trajectory_matches_the_seal(self) -> None:
        self.assertEqual(
            [r["disposition"] for r in self.receipts],
            self.fixture["expected_disposition_sequence"],
        )
        self.assertEqual(
            [r["stack_after"] for r in self.receipts],
            self.fixture["expected_stack_after_sequence"],
        )

    def test_the_ask_does_not_mutate_the_stack(self) -> None:
        ask = self.receipts[1]
        self.assertEqual(ask["disposition"], "ASK")
        self.assertEqual(ask["stack_after"], ask["stack_before"])
        self.assertEqual(ask["authority_delta"], [])

    def test_the_reply_suspends_the_parent_and_mints_at_its_own_turn(self) -> None:
        reply = self.receipts[2]
        self.assertEqual(reply["disposition"], "SUSPEND")
        self.assertEqual(reply["selected_move_id"], "accept_datum")
        self.assertEqual(
            reply["stack_after"],
            ["ep-1-protocol.greeting.a", "ep-3-protocol.quoted_datum.a"],
        )
        self.assertEqual(self.session_.stack_history[2][0]["state"], "suspended")

    def test_the_exit_leaves_the_parent_suspended_and_the_resume_reactivates_it(self) -> None:
        self.assertEqual(self.receipts[3]["disposition"], "EXIT")
        self.assertEqual(self.session_.stack_history[3][0]["state"], "suspended")
        self.assertEqual(self.receipts[4]["disposition"], "RESUME")
        self.assertEqual(self.receipts[4]["selected_move_id"], "pick_up")
        self.assertEqual(self.session_.stack_history[4][0]["state"], "active")

    def test_the_stale_replay_is_refused_against_the_consumed_request(self) -> None:
        stale = self.receipts[5]
        self.assertEqual(stale["disposition"], "REFUSED")
        self.assertEqual(stale["verifier_verdict"], runtime.CONSUMED_REQUEST)
        self.assertEqual(stale["stack_after"], stale["stack_before"])
        self.assertEqual(stale["stack_after"], ["ep-1-protocol.greeting.a"])

    def test_a_consumed_request_stays_consumed_for_the_session(self) -> None:
        self.assertEqual(len(self.session_.consumed_request_ids), 1)


class DepthCapTests(RuntimeTestCase):
    """The ninth push is REFUSED before mutation, and the cap does not move."""

    def test_the_planted_ninth_push_is_refused(self) -> None:
        fixture = self.by_id["depth9-plant"]
        session = runtime.run_fixture(fixture, self.corpus)
        final = session.receipts[-1]
        self.assertEqual(final["disposition"], "REFUSED")
        self.assertEqual(final["verifier_verdict"], runtime.DEPTH_CAP)
        self.assertEqual(final["stack_after"], final["stack_before"])
        self.assertEqual(len(final["stack_before"]), runtime.STACK_DEPTH_CAP)
        self.assertEqual(len(session.stack), runtime.STACK_DEPTH_CAP)

    def test_the_plant_filled_the_cap_itself(self) -> None:
        session = runtime.run_fixture(self.by_id["depth9-plant"], self.corpus)
        depths = [len(r["stack_after"]) for r in session.receipts]
        self.assertEqual(max(depths), 8)


class StackOwnershipTests(RuntimeTestCase):
    """The session owns the stack; a contradicted summary is refused."""

    def test_a_contradicted_stack_summary_fails_validation(self) -> None:
        session = self.session()
        session.submit_utterance("hello", self.rows("fresh_root"), source="test:1")
        rows = self.rows("fresh_root")
        for row in rows:
            if row["signal_id"] == "protocol_stack":
                row["value"] = "empty"  # the session's own stack says otherwise
        receipt = session.submit_utterance("goodbye", rows, source="test:2")
        self.assertEqual(receipt["disposition"], "REFUSED")
        self.assertEqual(receipt["verifier_verdict"], runtime.INVALID_INPUT)
        self.assertTrue(
            any(
                line.startswith("stack_summary_contradiction:")
                for line in receipt["verifier_evidence"]
            )
        )
        self.assertEqual(len(session.stack), 1, "validation refused before mutation")

    def test_an_underivable_signal_is_not_the_absence_sentinel(self) -> None:
        rows = [row for row in self.rows("literal_slot") if row["signal_id"] != "quote_boundary"]
        receipt = self.session().submit_utterance("forty-two", rows, source="test:1")
        self.assertEqual(receipt["disposition"], "REFUSED")
        self.assertEqual(receipt["verifier_verdict"], runtime.INVALID_INPUT)
        self.assertIn("underivable_signals:quote_boundary", receipt["verifier_evidence"])


class ReceiptShapeTests(RuntimeTestCase):
    """`uptake_id`, the frozen field list, and nothing that cannot be replayed."""

    def test_uptake_id_is_the_digest_of_the_record_with_it_empty(self) -> None:
        receipt = self.session().submit_utterance(
            "hello", self.rows("fresh_root"), source="test:1"
        )
        self.assertEqual(receipt["uptake_id"], runtime.recompute_uptake_id(receipt))
        self.assertEqual(len(receipt["uptake_id"]), 64)

    def test_the_schema_is_inside_the_digest(self) -> None:
        receipt = dict(
            self.session().submit_utterance("hello", self.rows("fresh_root"), source="test:1")
        )
        moved = {**receipt, "schema": "corollary.protocol-uptake/999"}
        self.assertNotEqual(
            runtime.recompute_uptake_id(receipt), runtime.recompute_uptake_id(moved)
        )

    def test_the_field_list_is_exactly_the_designs(self) -> None:
        receipt = self.session().submit_utterance(
            "hello", self.rows("fresh_root"), source="test:1"
        )
        self.assertEqual(set(receipt), set(runtime.RECEIPT_FIELDS))

    def test_no_receipt_carries_a_clock_or_a_deleted_field(self) -> None:
        deleted = deleted_at_upre()
        self.assertEqual(len(deleted), 2)
        for receipt in runtime.replay_registered_pass(self.fixtures, self.corpus):
            text = runtime.canonical_record(receipt)
            for name in deleted:
                self.assertNotIn(name, text)
            for clock in ("timestamp", "generated_at", "created_at", "elapsed"):
                self.assertNotIn(clock, text)

    def test_the_runtime_source_never_spells_a_deleted_field(self) -> None:
        source = (REPO / "scripts" / "protocol_runtime.py").read_text(encoding="utf-8")
        for name in deleted_at_upre():
            self.assertNotIn(name, source)

    def test_authority_delta_is_present_and_empty_everywhere(self) -> None:
        for receipt in runtime.replay_registered_pass(self.fixtures, self.corpus):
            self.assertIn("authority_delta", receipt)
            self.assertEqual(receipt["authority_delta"], [])


class DeterminismTests(RuntimeTestCase):
    """B10 needs byte identity, so it is a property of the runtime, not of luck."""

    def test_two_identical_sessions_produce_byte_identical_receipts(self) -> None:
        fixture = self.by_id["nested-resume-d1-b"]
        first = runtime.run_fixture(fixture, self.corpus).receipts
        second = runtime.run_fixture(fixture, self.corpus).receipts
        self.assertEqual(
            [runtime.canonical_record(r) for r in first],
            [runtime.canonical_record(r) for r in second],
        )

    def test_the_whole_registered_pass_replays_byte_identically(self) -> None:
        first = runtime.replay_registered_pass(self.fixtures, self.corpus)
        second = runtime.replay_registered_pass(self.fixtures, self.corpus)
        self.assertEqual(len(first), 87)
        self.assertEqual(
            [runtime.canonical_record(r) for r in first],
            [runtime.canonical_record(r) for r in second],
        )

    def test_every_sealed_fixture_reproduces_its_sealed_disposition(self) -> None:
        for fixture in self.fixtures["fixtures"]:
            session = runtime.run_fixture(fixture, self.corpus)
            self.assertEqual(
                len(session.receipts), len(fixture["turns"]), fixture["fixture_id"]
            )
            for turn, receipt in zip(fixture["turns"], session.receipts):
                self.assertEqual(
                    receipt["disposition"],
                    turn["expected_disposition"],
                    f"{fixture['fixture_id']} turn {turn['turn_index']}",
                )
                self.assertEqual(
                    receipt["selected_move_id"],
                    turn.get("expected_move_id"),
                    f"{fixture['fixture_id']} turn {turn['turn_index']}",
                )


class MutantTests(RuntimeTestCase):
    """Every sealed B9 mutation lands, and none of them is a no-op."""

    def test_every_sealed_mutant_changes_the_turn_it_targets(self) -> None:
        for mutant in self.fixtures["b9_mutants"]:
            plan = runtime.parse_mutant(mutant)
            fixture = self.by_id[mutant["target_fixture"]]
            baseline = runtime.run_fixture(fixture, self.corpus).receipts
            mutated = runtime.run_fixture(fixture, self.corpus, mutation=plan).receipts
            index = plan.turn_index - 1
            self.assertNotEqual(
                runtime.canonical_record(baseline[index]),
                runtime.canonical_record(mutated[index]),
                mutant["mutant_id"],
            )

    def test_a_mutation_that_cannot_land_raises_rather_than_passing(self) -> None:
        plan = runtime.Mutation(
            mutant_id="not-sealed",
            turn_index=1,
            target="signal",
            field="pending_need",
            from_value="probe",
            to_value="ABSENT",
        )
        with self.assertRaises(runtime.ProtocolRuntimeError):
            runtime.run_fixture(self.by_id["ctx-1-1"], self.corpus, mutation=plan)


if __name__ == "__main__":
    unittest.main()
