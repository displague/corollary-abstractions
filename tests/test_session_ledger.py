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

    def test_the_recorder_digest_amendment_matches_the_recorder(self) -> None:
        """The C3 fix: a digest in the protocol, of the recorder as it is."""

        from session_recorder import recorder_code_digest  # noqa: PLC0415

        amendment = self.prereg["amendments"][0]
        self.assertEqual(amendment["dated"], "2026-08-25")
        self.assertEqual(
            amendment["adds"]["recorder_code_digest"],
            recorder_code_digest(REPO),
            "the recorder moved after its digest was frozen",
        )

    def test_the_amendment_changed_no_number(self) -> None:
        """An amendment that moved a floor would be a re-registration."""

        amendment = self.prereg["amendments"][0]
        self.assertIn("changes no clause", amendment["what_this_amendment_does_not_do"])
        self.assertIsNone(self.prereg["recording_protocol"]["recorder_code_digest"])

    def test_the_floor_ruling_retracts_without_erasing(self) -> None:
        """H2: amendment 4 replaces a justification; it does not delete one.

        A wrong reason that is quietly removed teaches nothing, and a reader
        asking whether the reading was chosen well needs to see the bad
        reason it was first given. So the retracted sentence must still be
        where it was written, and the amendment must quote it.
        """

        amendment = next(
            item for item in self.prereg["amendments"] if item["amendment"] == 4
        )
        original = self.prereg["floors_and_their_meetability"][
            "P3_corpus_floor"
        ]["why_this_reading_and_the_discrepancy_it_resolves"]
        self.assertIn("coin flip", original, "the original was edited")
        self.assertIn(
            amendment["what_this_replaces"]["the_retracted_sentence"][:60],
            original,
            "the amendment quotes a sentence the original does not contain",
        )
        self.assertIn(
            "deterministic",
            amendment["what_this_replaces"]["why_it_was_wrong"].lower(),
        )

    def test_the_roadmap_carries_the_dated_floor_correction(self) -> None:
        roadmap = (REPO / "docs" / "ROADMAP-v0.21.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Corrected 2026-08-26 by the design author", roadmap)
        self.assertIn(
            "corpus-wide, and ≥36 binding-dependent turns in half B's share",
            _flat(roadmap),
        )

    def test_determinism_replaces_execute_once(self) -> None:
        clause = self.prereg["determinism_clause"]
        self.assertEqual(
            clause["registered_as"],
            "artifact committed from a deterministic runner; reproductions "
            "welcome and recorded",
        )
        self.assertEqual(clause["replaces"], "executed once")


class _Recorded(unittest.TestCase):
    """One recorded session, shared by the behavioural tests below."""

    LINES: tuple[str, ...] = ()

    @classmethod
    def setUpClass(cls) -> None:
        import session_ledger as ledger  # noqa: PLC0415
        from resolver import default_index  # noqa: PLC0415
        from session_keys import SessionKeyRing  # noqa: PLC0415
        from session_recorder import SessionRecorder  # noqa: PLC0415

        cls.ledger = ledger
        cls.index = default_index()
        cls.ring = SessionKeyRing.ephemeral()
        cls.recorder = SessionRecorder(
            REPO,
            "v021-suite",
            "2026-08-25T00:00:00Z",
            cls.ring,
            shared_index=cls.index,
        )
        for line in cls.LINES:
            cls.recorder.turn(line)
        cls.document = cls.recorder.document()
        cls.pins = cls.recorder.pin_table


class RecordTypes(_Recorded):
    """§3's field names are the contract, checked against §3."""

    LINES = (
        "2 + 2",
        "suppose x = 5",
        "x ^ 2",
        "suppose y = 3",
        "x + y",
        "suppose not z = 4",
        "z ^ 2",
        "retract a001",
        "x ^ 2",
        "twin no.such.statement",
        "suppose y = 11",
        "y ^ 2",
    )

    def test_header_carries_the_five_pins_and_omits_the_sixth(self) -> None:
        pins = self.document["header"]["pins"]
        self.assertEqual(sorted(pins), sorted(self.ledger.PIN_FIELDS))
        self.assertNotIn("proposer_model_digest", pins)

    def test_header_carries_session_id_and_created_utc(self) -> None:
        header = self.document["header"]
        self.assertEqual(header["session_id"], "v021-suite")
        self.assertEqual(header["created_utc"], "2026-08-25T00:00:00Z")

    def test_assumption_records_carry_exactly_the_design_fields(self) -> None:
        required = {
            "assumption_id",
            "declared_at_turn",
            "text_bytes",
            "normal_form",
            "status",
            "superseded_by",
        }
        for record in self.document["assumptions"]:
            self.assertTrue(required.issubset(record), record["assumption_id"])
            self.assertIn(record["status"], self.ledger.ASSUMPTION_STATUSES)

    def test_turn_records_carry_exactly_the_design_fields(self) -> None:
        required = {
            "turn_index",
            "input_bytes",
            "resolution",
            "assumptions_declared",
            "assumptions_cited",
            "live_set_digest",
            "result",
            "receipt_digest",
            "prev_turn_digest",
            "mac",
        }
        for record in self.document["turns"]:
            self.assertTrue(required.issubset(record), record["turn_index"])
            self.assertIn(
                record["resolution"]["kind"], self.ledger.RESOLUTION_KINDS
            )

    def test_normal_form_is_the_atoms_own_pair(self) -> None:
        """`supposition._atom`'s return value, not a rendering of it.

        B4 mutates `normal_form` and nothing else, and requires the polarity
        flip to be one of the mutations it can make. So polarity has to live
        INSIDE the field the gate names.
        """

        from supposition import _atom  # noqa: PLC0415

        for record in self.document["assumptions"]:
            atom, polarity = _atom(record["text_bytes"])
            self.assertEqual(record["normal_form"], [atom, polarity])

    def test_the_live_set_is_never_in_the_journal(self) -> None:
        """§3: the digest, not the set — the journal stays linear."""

        for record in self.document["turns"]:
            self.assertIsInstance(record["live_set_digest"], str)
            self.assertEqual(len(record["live_set_digest"]), 64)
            self.assertNotIn("live_set", record)

    def test_the_chain_covers_every_turn(self) -> None:
        expected = self.ledger.header_digest(self.document["header"])
        for record in self.document["turns"]:
            self.assertEqual(record["prev_turn_digest"], expected)
            expected = self.ledger.digest(record)

    def test_every_record_authenticates(self) -> None:
        for record in self.document["assumptions"]:
            self.assertTrue(
                self.ledger.verify_assumption_mac(
                    record, "v021-suite", self.ring
                ),
                record["assumption_id"],
            )
        for record in self.document["turns"]:
            self.assertTrue(
                self.ledger.verify_turn_mac(record, "v021-suite", self.ring),
                record["turn_index"],
            )

    def test_the_extension_is_inside_the_mac(self) -> None:
        """An extension a tamperer could edit freely is B8's hole."""

        record = dict(self.document["turns"][0])
        record["session_events"] = [{"subsystem_id": "forged"}]
        self.assertFalse(
            self.ledger.verify_turn_mac(record, "v021-suite", self.ring)
        )

    def test_declared_and_cited_are_disjoint_on_every_turn(self) -> None:
        for record in self.document["turns"]:
            self.assertFalse(
                set(record["assumptions_declared"])
                & set(record["assumptions_cited"]),
                record["turn_index"],
            )

    def test_supersession_and_retraction_both_happened(self) -> None:
        """The lifecycle is exercised, not merely representable."""

        statuses = {
            record["assumption_id"]: record["status"]
            for record in self.document["assumptions"]
        }
        self.assertIn("retracted", statuses.values())
        self.assertIn("superseded", statuses.values())
        superseded = [
            record
            for record in self.document["assumptions"]
            if record["status"] == "superseded"
        ]
        for record in superseded:
            self.assertIsNotNone(record["superseded_by"], record["assumption_id"])

    def test_refusal_turns_carry_a_receipt_and_an_explicit_citation_list(
        self,
    ) -> None:
        """B7's shape, on the same corpus B7 will score."""

        refusals = [
            record
            for record in self.document["turns"]
            if record["result"]["kind"] in self.ledger.REFUSAL_STATUSES
        ]
        self.assertTrue(refusals, "no refusal turn in the fixture")
        for record in refusals:
            self.assertTrue(record["receipt_digest"])
            self.assertIsNotNone(record["assumptions_cited"])
            self.assertIsNotNone(record["result"]["refusal_type"])


class TheBehaviourTheSliceIsFor(_Recorded):
    """A supposition that persists, and an answer that says it consumed one."""

    LINES = RecordTypes.LINES

    def test_a_later_turn_answers_under_an_earlier_supposition(self) -> None:
        turn = self.document["turns"][2]
        self.assertEqual(turn["input_bytes"], "x ^ 2")
        self.assertEqual(turn["assumptions_cited"], ["a001"])
        self.assertEqual(turn["result"]["kind"], "solved")
        self.assertIn("25", self.recorder.outcomes[2].rendered)

    def test_the_declaring_turn_cites_nothing(self) -> None:
        turn = self.document["turns"][1]
        self.assertEqual(turn["assumptions_declared"], ["a001"])
        self.assertEqual(turn["assumptions_cited"], [])

    def test_two_assumptions_are_both_cited_when_both_are_consumed(
        self,
    ) -> None:
        turn = self.document["turns"][4]
        self.assertEqual(turn["input_bytes"], "x + y")
        self.assertEqual(turn["assumptions_cited"], ["a001", "a002"])

    def test_a_negated_assumption_refuses_by_type_instead_of_computing(
        self,
    ) -> None:
        turn = self.document["turns"][6]
        self.assertEqual(turn["input_bytes"], "z ^ 2")
        self.assertEqual(turn["result"]["kind"], "refused")
        self.assertEqual(
            turn["result"]["refusal_type"],
            self.ledger.REFUSAL_ASSUMPTION_CONFLICT,
        )
        self.assertEqual(turn["assumptions_cited"], ["a003"])

    def test_a_retracted_assumption_stops_being_consulted(self) -> None:
        before, after = self.document["turns"][2], self.document["turns"][8]
        self.assertEqual(before["input_bytes"], after["input_bytes"])
        self.assertEqual(after["assumptions_cited"], [])
        self.assertNotEqual(
            before["result"]["answer_bytes_digest"],
            after["result"]["answer_bytes_digest"],
        )

    def test_a_retract_turn_is_a_lifecycle_turn_not_an_answer(self) -> None:
        turn = self.document["turns"][7]
        self.assertEqual(turn["resolution"]["kind"], "supposition")
        self.assertEqual(turn["assumptions_cited"], ["a001"])
        self.assertFalse(self.ledger.is_binding_dependent(turn))

    def test_b10_every_uncited_turn_renders_byte_identically_stateless(
        self,
    ) -> None:
        """The fence, tested rather than promised."""

        from harness import CoreSession, route_line  # noqa: PLC0415

        for outcome in self.recorder.outcomes:
            record = self.document["turns"][outcome.turn_index]
            if record["assumptions_cited"]:
                continue
            fresh = CoreSession.boot(
                REPO, offline=True, session_id="v021-suite"
            )
            fresh.resolver_index = self.index
            verdict = route_line(REPO, fresh, record["input_bytes"])
            self.assertEqual(
                self.ledger.answer_bytes(verdict),
                outcome.rendered,
                f"turn {outcome.turn_index} ({record['input_bytes']!r}) "
                "cites nothing and does not render statelessly",
            )

    def test_the_read_log_is_written_apart_and_agrees(self) -> None:
        """B12's shape: two writers, one comparison."""

        citations = self.recorder.barrier.citations_by_turn()
        for record in self.document["turns"]:
            self.assertEqual(
                tuple(record["assumptions_cited"]),
                citations.get(record["turn_index"], ()),
                record["turn_index"],
            )

    def test_the_serving_path_never_bypasses_the_barrier(self) -> None:
        """`_binding` is private by name, and nothing in harness reads it."""

        source = (REPO / "scripts" / "harness.py").read_text(encoding="utf-8")
        self.assertNotIn("._binding", source)
        self.assertNotIn(".normal_form", source)


class BoundsAndRefusals(unittest.TestCase):
    """The §3 bounds, exercised outside the sealed corpus.

    The recording protocol caps live assumptions at 8, so a RECORDED
    session never declares a ninth and B10's denominator never contains a
    budget refusal — which is how the tension between §3's typed
    `assumption_budget` refusal and §7 B10 is resolved. The refusal still
    has to work, so it is exercised here.
    """

    def setUp(self) -> None:
        import session_ledger as ledger  # noqa: PLC0415
        from session_keys import SessionKeyRing  # noqa: PLC0415
        from session_recorder import SessionRecorder  # noqa: PLC0415

        self.ledger = ledger
        self.recorder = SessionRecorder(
            REPO, "v021-bounds", "2026-08-25T00:00:00Z",
            SessionKeyRing.ephemeral(),
        )

    def test_a_ninth_live_assumption_refuses_by_type(self) -> None:
        for index in range(self.ledger.LIVE_ASSUMPTION_CAP):
            outcome = self.recorder.turn(f"suppose v{index} = {index}")
            self.assertEqual(outcome.verdict["status"], "waiting")
        outcome = self.recorder.turn("suppose v99 = 99")
        self.assertEqual(outcome.verdict["status"], "refused")
        self.assertEqual(
            outcome.verdict["refusal_type"],
            self.ledger.REFUSAL_ASSUMPTION_BUDGET,
        )

    def test_re_supposing_a_live_subject_is_not_a_ninth(self) -> None:
        """Supersession replaces; it does not spend budget."""

        for index in range(self.ledger.LIVE_ASSUMPTION_CAP):
            self.recorder.turn(f"suppose v{index} = {index}")
        outcome = self.recorder.turn("suppose v0 = 100")
        self.assertEqual(outcome.verdict["status"], "waiting")

    def test_retracting_an_unknown_id_refuses_by_type(self) -> None:
        outcome = self.recorder.turn("retract a999")
        self.assertEqual(outcome.verdict["status"], "refused")
        self.assertEqual(
            outcome.verdict["refusal_type"],
            self.ledger.REFUSAL_UNKNOWN_ASSUMPTION,
        )

    def test_the_turn_cap_stops_recording(self) -> None:
        self.recorder.turns = ["stub"] * self.ledger.TURN_CAP
        with self.assertRaises(RuntimeError):
            self.recorder.turn("2 + 2")


class TheB10Regression(unittest.TestCase):
    """The ten misses that stopped the slice, as fixtures.

    Run 1 and run 2 both found `retract a999` rendering one way with a
    ledger attached and another way without, on a turn that cites nothing —
    the ledger's EXISTENCE reaching an unconditional answer's bytes. Prereg
    amendment 3 adjudicated it a construction defect and chose fix (a): the
    unknown-id arm stops decorating itself with ledger state. These are the
    regression fixtures, written from the ten misses the gate published.
    """

    @classmethod
    def setUpClass(cls) -> None:
        import session_ledger as ledger  # noqa: PLC0415
        from resolver import default_index  # noqa: PLC0415

        cls.ledger = ledger
        cls.index = default_index()

    def _serve(self, line: str, *, with_ledger: bool) -> str:
        from harness import CoreSession, route_line  # noqa: PLC0415

        session = CoreSession.boot(REPO, offline=True, session_id="b10-fixture")
        session.resolver_index = self.index
        if with_ledger:
            barrier = self.ledger.ReadBarrier()
            session.assumptions = self.ledger.AssumptionSet(
                "b10-fixture", barrier
            )
            barrier.open_turn(0)
            session.assumptions.declare("x = 5", 0)
            session.assumptions.declare("y = 3", 0)
        return self.ledger.answer_bytes(route_line(REPO, session, line))

    def test_the_exact_line_that_stopped_the_slice(self) -> None:
        self.assertEqual(
            self._serve("retract a999", with_ledger=True),
            self._serve("retract a999", with_ledger=False),
        )

    def test_no_rendering_of_this_arm_names_the_ledger(self) -> None:
        """The specific decoration that leaked, gone by name."""

        rendered = self._serve("retract a999", with_ledger=True)
        self.assertNotIn("keeps no assumption ledger", rendered)
        self.assertIn("no live assumption 'a999' in this session", rendered)

    def test_the_arm_is_still_a_typed_receipted_refusal(self) -> None:
        """Fix (a) removes nothing B7 asks for."""

        from harness import CoreSession, route_line  # noqa: PLC0415

        session = CoreSession.boot(REPO, offline=True, session_id="b10-fixture")
        session.resolver_index = self.index
        verdict = route_line(REPO, session, "retract a999")
        self.assertEqual(verdict["status"], "refused")
        self.assertEqual(verdict["refusal_type"], "unknown_assumption")

    def test_an_id_the_ledger_does_hold_still_retracts_and_cites(self) -> None:
        """The repair narrows the refusal arm and touches nothing else."""

        from harness import CoreSession, route_line  # noqa: PLC0415

        session = CoreSession.boot(REPO, offline=True, session_id="b10-fixture")
        session.resolver_index = self.index
        barrier = self.ledger.ReadBarrier()
        session.assumptions = self.ledger.AssumptionSet("b10-fixture", barrier)
        barrier.open_turn(0)
        session.assumptions.declare("x = 5", 0)
        verdict = route_line(REPO, session, "retract a001")
        self.assertEqual(verdict["status"], "canceled")
        self.assertEqual(barrier.close_turn(), ("a001",))

    def test_the_empty_argument_arm_never_read_session_state(self) -> None:
        self.assertEqual(
            self._serve("retract", with_ledger=True),
            self._serve("retract", with_ledger=False),
        )

    def test_the_sweep_finds_no_other_ledger_reader_in_a_refusal(self) -> None:
        """Amendment 3's sweep, kept live rather than filed as prose.

        An AST walk for `_route_*` functions that read the session's
        assumption ledger. Two are expected and both are accounted for in
        the amendment: `_route_suppose` (the budget refusal, disarmed by the
        protocol's cap of 8) and `_route_retract` (repaired here). A third
        would be a new member of the same family and this test is what makes
        it announce itself.
        """

        import ast  # noqa: PLC0415

        source = (REPO / "scripts" / "harness.py").read_text(encoding="utf-8")
        readers = set()
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.FunctionDef):
                continue
            if not node.name.startswith("_route"):
                continue
            for sub in ast.walk(node):
                if (
                    isinstance(sub, ast.Call)
                    and isinstance(sub.func, ast.Name)
                    and sub.func.id == "getattr"
                    and len(sub.args) >= 2
                    and isinstance(sub.args[1], ast.Constant)
                    and sub.args[1].value == "assumptions"
                ):
                    readers.add(node.name)
        self.assertEqual(readers, {"_route_suppose", "_route_retract"})


class Replay(_Recorded):
    """Replay re-verifies the record, and refuses a moved world."""

    LINES = RecordTypes.LINES

    def test_unmutated_replay_reproduces_every_turn(self) -> None:
        from replay_session import replay  # noqa: PLC0415

        report = replay(
            REPO, self.document, shared_index=self.index, live_pins=self.pins
        )
        self.assertIsNone(report.refusal)
        self.assertEqual(report.turns_reproduced, report.turns_total)
        self.assertIsNone(report.first_divergence_turn)

    def test_every_pin_perturbed_individually_refuses(self) -> None:
        """B3's shape: every pin, no sampling."""

        from replay_session import STALE, replay  # noqa: PLC0415

        for name in self.ledger.PIN_FIELDS:
            perturbed = dict(self.pins)
            perturbed[name] = "perturbed"
            report = replay(
                REPO,
                self.document,
                shared_index=self.index,
                live_pins=perturbed,
            )
            self.assertEqual(report.refusal, STALE, name)
            self.assertEqual(report.pin_mismatch, [name])
            self.assertEqual(report.turns_reproduced, 0, name)

    def test_the_replay_report_carries_the_designs_field_names(self) -> None:
        from replay_session import replay  # noqa: PLC0415

        report = replay(
            REPO, self.document, shared_index=self.index, live_pins=self.pins
        ).as_dict()
        for name in (
            "turns_total",
            "turns_reproduced",
            "first_divergence_turn",
            "pin_mismatch",
        ):
            self.assertIn(name, report)

    def test_the_stateless_baseline_cannot_follow_a_citing_turn(self) -> None:
        """§8's vacuity control, by construction rather than by hope."""

        from replay_session import replay  # noqa: PLC0415

        report = replay(
            REPO,
            self.document,
            stateless=True,
            shared_index=self.index,
            live_pins=self.pins,
        )
        self.assertLess(report.turns_reproduced, report.turns_total)
        citing = [
            record["turn_index"]
            for record in self.document["turns"]
            if record["assumptions_cited"]
        ]
        self.assertEqual(report.first_divergence_turn, min(citing))

    def test_a_mutated_cited_assumption_moves_the_replayed_answer(self) -> None:
        """B4's mechanism, on a fixture that never becomes a journal."""

        import copy  # noqa: PLC0415
        from replay_session import replay  # noqa: PLC0415

        mutated = copy.deepcopy(self.document)
        for record in mutated["assumptions"]:
            if record["assumption_id"] == "a002":
                record["text_bytes"] = "y = 8"
                record["normal_form"] = ["y = 8", True]
        report = replay(
            REPO, mutated, shared_index=self.index, live_pins=self.pins
        )
        self.assertIsNotNone(report.first_divergence_turn)
        # The declaring turn's own bytes are untouched, so it still replays.
        declaring = next(
            record["turn_index"]
            for record in self.document["turns"]
            if "a002" in record["assumptions_declared"]
        )
        self.assertGreater(report.first_divergence_turn, declaring)

    def test_a_polarity_flip_turns_an_answer_into_a_typed_refusal(self) -> None:
        import copy  # noqa: PLC0415
        from replay_session import replay  # noqa: PLC0415

        mutated = copy.deepcopy(self.document)
        for record in mutated["assumptions"]:
            if record["assumption_id"] == "a002":
                record["text_bytes"] = "not y = 3"
                record["normal_form"] = ["y = 3", False]
        report = replay(
            REPO, mutated, shared_index=self.index, live_pins=self.pins
        )
        self.assertIsNotNone(report.first_divergence_turn)
        statuses = {
            item["turn_index"]: item["replayed_status"]
            for item in report.divergences
        }
        self.assertIn("refused", statuses.values())


SEAL = REPO / "experiments" / "session_corpus_seal.json"


class TheSealedCorpus(unittest.TestCase):
    """P3's seal, and the journals it covers.

    This is the committed pattern `check_regeneration.py:97-100` names for
    hand-authored artifacts: an artifact under `experiments/` with a digest
    pin and a test. The seal is the pin; this is the test.
    """

    @classmethod
    def setUpClass(cls) -> None:
        if not SEAL.exists():  # pragma: no cover - ordering guard
            raise unittest.SkipTest("the corpus is not sealed yet")
        cls.seal = json.loads(SEAL.read_text(encoding="utf-8"))

    def test_every_journal_matches_its_sealed_digest(self) -> None:
        import session_ledger as ledger  # noqa: PLC0415

        for entry in self.seal["sessions"]:
            journal = REPO / entry["journal"]
            reads = REPO / entry["read_log"]
            self.assertEqual(
                ledger.text_digest(journal.read_text(encoding="utf-8")),
                entry["journal_digest"],
                entry["session_id"],
            )
            self.assertEqual(
                ledger.text_digest(reads.read_text(encoding="utf-8")),
                entry["read_log_digest"],
                entry["session_id"],
            )

    def test_journals_live_under_experiments_and_never_under_data(self) -> None:
        """§3's placement rule: a journal has no seed."""

        for entry in self.seal["sessions"]:
            self.assertTrue(entry["journal"].startswith("experiments/sessions/"))
            self.assertNotIn("data/", entry["journal"])

    def test_the_split_is_the_committed_hash_rule(self) -> None:
        import session_ledger as ledger  # noqa: PLC0415

        for entry in self.seal["sessions"]:
            self.assertEqual(
                entry["half"], ledger.half_of(entry["session_id"])
            )

    def test_no_recorded_turn_reached_the_write_gate(self) -> None:
        """§6 P3's rule, and the count is published either way."""

        self.assertEqual(self.seal["excluded_sessions"], [])
        self.assertEqual(
            self.seal["counts"]["sessions_excluded_by_the_no_write_gate_rule"],
            0,
        )
        for entry in self.seal["sessions"]:
            journal = json.loads(
                (REPO / entry["journal"]).read_text(encoding="utf-8")
            )
            for turn in journal["turns"]:
                self.assertNotEqual(
                    turn["resolution"]["grammar_query"],
                    "<repo-relative path>",
                    entry["session_id"],
                )
                self.assertNotIn(
                    turn["result"]["kind"],
                    {"PROVEN", "VERIFIED", "REFUSED"},
                    entry["session_id"],
                )

    def test_the_caps_were_respected(self) -> None:
        import session_ledger as ledger  # noqa: PLC0415

        protocol = self.seal["protocol"]
        self.assertLessEqual(
            self.seal["counts"]["sessions_recorded"],
            protocol["session_count_cap"],
        )
        for entry in self.seal["sessions"]:
            self.assertLessEqual(
                entry["turns"], protocol["turn_cap_per_session"]
            )
            journal = json.loads(
                (REPO / entry["journal"]).read_text(encoding="utf-8")
            )
            live = sum(
                1
                for record in journal["assumptions"]
                if record["status"] == "live"
            )
            self.assertLessEqual(live, ledger.LIVE_ASSUMPTION_CAP)

    def test_the_recorder_that_recorded_is_the_recorder_the_protocol_pinned(
        self,
    ) -> None:
        from session_recorder import recorder_code_digest  # noqa: PLC0415

        self.assertEqual(
            self.seal["recorder_code_digest"], recorder_code_digest(REPO)
        )

    def test_the_floor_verdict_is_computed_from_the_counts(self) -> None:
        counts, floor = self.seal["counts"], self.seal["floor"]
        self.assertEqual(
            floor["sessions_met"], counts["sessions_admitted"] >= 30
        )
        self.assertEqual(floor["turns_met"], counts["turns_admitted"] >= 120)
        self.assertEqual(
            floor["binding_dependent_in_half_b_met"],
            counts["by_half"]["B"]["binding_dependent_turns"] >= 36,
        )

    def test_the_other_readings_number_is_published(self) -> None:
        """The prereg chose a reading; the seal shows what the other gave.

        Without this the choice is convenient. With it, a reader who prefers
        the roadmap's wording has the number they need to disagree on the
        evidence.
        """

        other = self.seal["floor"]["under_the_roadmaps_compressed_reading"]
        self.assertIn("sessions_in_half_b", other)
        self.assertIn("sessions_met", other)

    def test_the_corpus_has_all_six_authored_shapes(self) -> None:
        shapes = {entry["shape"] for entry in self.seal["sessions"]}
        self.assertEqual(shapes, set(range(6)))
        self.assertGreater(self.seal["counts"]["assumption_free_sessions"], 0)
        self.assertGreater(self.seal["counts"]["refusal_turns_admitted"], 0)


RUN = REPO / "experiments" / "session_ledger_run.json"
RUN2 = REPO / "experiments" / "session_ledger_run2.json"
RUN3 = REPO / "experiments" / "session_ledger_run3.json"


class TheRegisteredRun(unittest.TestCase):
    """The gate's own artifacts, held to the shapes the design registered."""

    @classmethod
    def setUpClass(cls) -> None:
        if not RUN.exists():  # pragma: no cover - ordering guard
            raise unittest.SkipTest("the gate has not run yet")
        cls.first = json.loads(RUN.read_text(encoding="utf-8"))
        cls.second = (
            json.loads(RUN2.read_text(encoding="utf-8"))
            if RUN2.exists()
            else None
        )

    def test_every_registered_clause_is_adjudicated(self) -> None:
        gate = self.first["construction_gate"]
        self.assertEqual(
            sorted(gate, key=lambda name: int(name[1:])),
            [f"B{n}" for n in range(1, 14)],
        )

    def test_b9_is_never_and_says_why(self) -> None:
        b9 = self.first["construction_gate"]["B9"]
        self.assertEqual(b9["verdict"], "NEVER")
        self.assertIn("slice 2", b9["why"])

    def test_r1_is_computed_from_its_clauses(self) -> None:
        gate = self.second or self.first
        result = gate["result_gate"]
        expected = "HOLDS" if all(result["clauses"].values()) else "FAILS"
        self.assertEqual(result["verdict"], expected)

    def test_b10s_verdict_matches_its_misses(self) -> None:
        for artifact in filter(None, (self.first, self.second)):
            b10 = artifact["construction_gate"]["B10"]
            self.assertEqual(
                b10["verdict"], "GREEN" if not b10["misses"] else "RED"
            )

    def test_the_b10_finding_is_the_retract_line_and_nothing_else(self) -> None:
        """The finding is specific, and a wider one would be a different one."""

        b10 = self.first["construction_gate"]["B10"]
        self.assertEqual(b10["verdict"], "RED")
        lines = {miss["input_bytes"] for miss in b10["misses"]}
        self.assertEqual(lines, {"retract a999"})

    def test_the_scored_rows_carry_no_arm_label(self) -> None:
        """§8's blindness, checked in the artifact rather than trusted.

        If an arm label had reached the scorer it would be visible in the
        rows the scorer produced, because the artifact carries them.
        """

        for artifact in filter(None, (self.first, self.second)):
            for name in ("B4", "B5", "B6"):
                clause = artifact["construction_gate"][name]
                rows = clause.get("misses_published_individually") or clause.get(
                    "flip_rows", []
                )
                for row in rows:
                    self.assertNotIn("arm", row)

    def test_zero_flip_clauses_watch_their_denominator(self) -> None:
        """A clause that cannot go red for having too few cases is not one."""

        if self.second is None:  # pragma: no cover - ordering guard
            self.skipTest("the supplementary run is not committed yet")
        for name, floor in (("B5", 60), ("B6", 30)):
            clause = self.second["construction_gate"][name]
            self.assertEqual(clause["registered_denominator"], floor)
            self.assertEqual(
                clause["denominator_met"], clause["cases"] >= floor
            )
            if clause["cases"] < floor:
                self.assertEqual(clause["verdict"], "SHORT OF DENOMINATOR")

    def test_the_supplementary_run_repairs_and_does_not_overturn(self) -> None:
        if self.second is None:  # pragma: no cover - ordering guard
            self.skipTest("the supplementary run is not committed yet")
        supplementary = self.second["supplementary"]
        self.assertTrue(supplementary["is_supplementary"])
        self.assertTrue(
            supplementary["the_original_is_never_edited_or_re_scored"]
        )
        # A reading that stands must read the same way twice.
        self.assertEqual(
            self.first["construction_gate"]["B10"]["verdict"],
            self.second["construction_gate"]["B10"]["verdict"],
        )
        self.assertEqual(self.second["result_gate"]["verdict"], "FAILS")

    def test_the_baseline_scores_zero_on_b4_after_the_repair(self) -> None:
        """§8: it cannot respond — by construction, not by hope."""

        if self.second is None:  # pragma: no cover - ordering guard
            self.skipTest("the supplementary run is not committed yet")
        baseline = self.second["capability_blind_baseline"]
        self.assertEqual(baseline["b4_score"], 0)
        self.assertGreater(baseline["b4_cases_checked"], 0)
        self.assertEqual(baseline["verdict"], "GREEN")

    def test_the_voiding_sentence_is_carried_verbatim_and_evaluated(
        self,
    ) -> None:
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        for artifact in filter(None, (self.first, self.second)):
            blind = artifact["blind_control"]
            self.assertEqual(
                blind["voiding_sentence"],
                prereg["blind_control"]["voiding_sentence_verbatim"],
            )
            flips = (
                artifact["construction_gate"]["B5"]["flips"]
                + artifact["construction_gate"]["B6"]["flips"]
            )
            self.assertEqual(blind["voided"], bool(flips))

    def test_b1s_ordering_clause_is_missed_and_published(self) -> None:
        """Not reinterpreted into green, and the git order is in the record."""

        b1 = self.first["construction_gate"]["B1"]
        self.assertEqual(b1["clause_1_seal_before_replayer"]["verdict"], "MISSED")
        self.assertEqual(
            b1["clause_2_no_sealed_file_was_edited"]["verdict"], "GREEN"
        )
        self.assertTrue(
            b1["clause_1_seal_before_replayer"]["replayer_first_committed"]
        )

    def test_b13s_table_carries_its_own_limitation(self) -> None:
        b13 = self.first["construction_gate"]["B13"]
        self.assertEqual(len(b13["table"]), 20)
        self.assertIn("weak evidence", b13["and_the_limitation_of_an_easy_audit"])
        self.assertIn("NOT independent", b13["auditor_independence"])

    def test_no_correctness_claim_appears_anywhere(self) -> None:
        for artifact in filter(None, (self.first, self.second)):
            self.assertIn("reproducible, not correct", artifact["negative_honesty"])


class TheRepairRun(unittest.TestCase):
    """Run 3 — the fresh run at the fixed tree, and what it licenses."""

    @classmethod
    def setUpClass(cls) -> None:
        if not RUN3.exists():  # pragma: no cover - ordering guard
            raise unittest.SkipTest("the repair run has not happened yet")
        cls.run3 = json.loads(RUN3.read_text(encoding="utf-8"))
        cls.seal = json.loads(SEAL.read_text(encoding="utf-8"))

    def test_the_prior_runs_are_retained_unedited(self) -> None:
        """A repair that erased what it superseded would be uncheckable."""

        self.assertTrue(RUN.exists())
        self.assertTrue(RUN2.exists())
        self.assertEqual(
            json.loads(RUN.read_text(encoding="utf-8"))["construction_gate"][
                "B10"
            ]["verdict"],
            "RED",
            "run 1 must still carry the red that stopped the slice",
        )

    def test_b10_is_green_and_its_denominator_did_not_shrink(self) -> None:
        """Green by repair, not by a smaller question."""

        before = json.loads(RUN.read_text(encoding="utf-8"))
        b10_then = before["construction_gate"]["B10"]
        b10_now = self.run3["construction_gate"]["B10"]
        self.assertEqual(b10_now["verdict"], "GREEN")
        self.assertEqual(b10_now["misses"], [])
        self.assertEqual(
            b10_now["uncited_turns"],
            b10_then["uncited_turns"],
            "the same 260 uncited turns were asked the same question",
        )

    def test_the_corpus_did_not_move(self) -> None:
        prior = json.loads(
            (REPO / "experiments" / "session_corpus_seal_pre_repair.json")
            .read_text(encoding="utf-8")
        )
        for key in (
            "sessions_admitted",
            "turns_admitted",
            "binding_dependent_turns_admitted",
            "refusal_turns_admitted",
            "by_half",
        ):
            self.assertEqual(
                self.seal["counts"][key], prior["counts"][key], key
            )
        self.assertEqual(
            [entry["session_id"] for entry in self.seal["sessions"]],
            [entry["session_id"] for entry in prior["sessions"]],
        )
        self.assertEqual(self.seal["floor"]["all_met"], True)

    def test_the_repair_delta_is_published_with_its_missed_expectation(
        self,
    ) -> None:
        """The registered expectation missed, and the seal says so."""

        delta = self.seal["repair_delta"]
        self.assertFalse(delta["expectation_met"])
        self.assertEqual(delta["turns_whose_answer_digest_changed"], 0)
        self.assertEqual(
            delta["header_pins_that_moved"], {"rendering_module_digests": 60}
        )
        self.assertTrue(delta["counts_unchanged"])
        self.assertIn("EXPECTATION MISSED", delta["finding"])

    def test_r1_holds_and_serves_exactly_the_designs_sentence(self) -> None:
        result = self.run3["result_gate"]
        self.assertEqual(result["verdict"], "HOLDS")
        self.assertTrue(result["served"])
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        self.assertEqual(
            result["served_claim_if_it_holds"],
            prereg["result_gate"]["served_claim_if_R1_holds_verbatim"],
        )

    def test_no_surface_was_invented(self) -> None:
        """The design names none, so the claim lives in artifact and tests.

        The capability sheet carries registered-run rows for realization,
        conformance and the foreign voice because those designs asked for
        them. DESIGN-session-ledger asked for none, and shipping a row it did
        not ask for would be serving more than the gate licensed.
        """

        from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

        sheet_source = (REPO / "scripts" / "serve_chat.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("session_ledger_run", sheet_source)
        self.assertIn(
            "no capability-sheet row",
            self.run3["result_gate"]["where_the_claim_lives"],
        )
        # The one surface that DID change is the grammar row the Assumption
        # status alphabet required, and on this skin it always refuses.
        row = next(r for r in LINE_GRAMMAR if r["route"] == "retraction")
        self.assertEqual(sorted(row["statuses"]), ["canceled", "refused"])

    def test_b1s_ordering_slip_is_still_published_as_missed(self) -> None:
        """Not reinterpreted by a green run."""

        b1 = self.run3["construction_gate"]["B1"]
        self.assertEqual(
            b1["clause_1_seal_before_replayer"]["verdict"], "MISSED"
        )

    def test_the_suspended_habit_ends_by_the_gates_own_verdict(self) -> None:
        """§12, and it names B10's scope rather than overclaiming it."""

        text = self.run3["result_gate"]["the_suspended_habit_ends_here"]
        self.assertIn("shipped property", text)
        self.assertIn("resolver ASK", text)


if __name__ == "__main__":
    unittest.main()
