#!/usr/bin/env python3
"""H-P0's tests: the stop condition first, then the clauses it protects.

`docs/DESIGN-house-rules.md` §9's stop condition is adjudicated FIRST in this
file and deliberately so — *"Stop before implementation if the declaration
form cannot express the sealed fixtures inside the registered grammar without
parser exceptions."* Everything below it is only worth running if that
passes, so it is the first class and it says what it is.

The fixtures were sealed at H-PRE, before this checker existed, which is the
only thing that makes them evidence rather than a mirror. Nothing in this
file may edit `experiments/house_rules_fixtures.json`; every expectation is
READ from it and compared against what the shipped code does.

Gate coverage in this file: B1 (totality, one deciding clause, over a
machine-enumerated sweep), B2 (freshness against the committed census, and
the census checker as a second program), B5's codec leg (`encode` refuses
both records), B6 (the use-side check and its regression fence), B8 (both
corruption arms), B11 (the import closure), B12 (round-trip identity over the
sealed pairs). B3/B4/B5's sweep, B7, B9 and B10 belong to H-P1's registered
run and are not simulated here — a construction test that scored a run gate
would be scoring itself.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import harness  # noqa: E402
import session_ledger as ledger  # noqa: E402
import session_state  # noqa: E402
import symbol_ledger as SL  # noqa: E402
import build_symbol_census as builder  # noqa: E402
import check_symbol_census as checker  # noqa: E402

FIXTURES = REPO / "experiments" / "house_rules_fixtures.json"
CENSUS = REPO / "experiments" / "symbol_census.json"


def _fixtures() -> dict:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def _inputs() -> SL.CommittedInputs:
    return SL.load_inputs(REPO)


def _rest(line: str) -> str:
    """Everything after the command word — what the route hands the checker."""

    return line.partition(" ")[2]


def _sessions(document: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in document["fixtures"]:
        grouped.setdefault(row["session_id"], []).append(row)
    for rows in grouped.values():
        rows.sort(key=lambda r: r["turn_index"])
    return grouped


def _live_session(session_id: str, inputs: SL.CommittedInputs):
    """A session with both ledgers attached, as a recorder would build it."""

    session = harness.CoreSession.boot(REPO, offline=True, session_id=session_id)
    session.assumptions = ledger.AssumptionSet(
        session_id=session_id, barrier=ledger.ReadBarrier()
    )
    session.symbols = SL.SymbolLedger(
        session_id=session_id, inputs=inputs, assumptions=session.assumptions
    )
    return session


class StopConditionIsAdjudicatedFirst(unittest.TestCase):
    """DESIGN §9, and the reason this class is at the top of the file."""

    def test_every_sealed_line_is_expressible_without_a_parser_exception(self) -> None:
        """The stop condition itself, over all 59 sealed fixture lines.

        `route_line` is the registered grammar, so this routes the real thing
        rather than calling the checker directly: a line that raised inside
        the harness would be just as much a stop as one that raised inside
        `parse_declaration`.
        """

        document = _fixtures()
        inputs = _inputs()
        routed = 0
        for session_id, rows in _sessions(document).items():
            session = _live_session(session_id, inputs)
            for row in rows:
                session.assumptions.barrier.open_turn(row["turn_index"])
                try:
                    harness.route_line(REPO, session, row["line"])
                except Exception as exc:  # noqa: BLE001 - the stop condition
                    self.fail(
                        f"DESIGN §9 STOP: {row['fixture_id']} raised "
                        f"{type(exc).__name__}: {exc} on {row['line']!r}"
                    )
                session.assumptions.barrier.close_turn()
                routed += 1
        self.assertEqual(routed, document["counts"]["fixtures_total"])
        self.assertEqual(routed, 59)

    def test_the_unparsed_fixtures_arrive_as_verdicts_and_not_as_exceptions(
        self,
    ) -> None:
        """The half of §9 that a bare "did not raise" would miss.

        A checker that swallowed everything into one refusal would also not
        raise. So this asserts the UNPARSED fixtures reach an UNPARSED
        VERDICT with `c1_unparsed` deciding — a refusal that named itself.
        """

        document = _fixtures()
        inputs = _inputs()
        unparsed = [
            row
            for row in document["fixtures"]
            if row["kind"] == "declaration"
            and row["expected_refusal_code"] == "UNPARSED"
        ]
        self.assertEqual(len(unparsed), 9, "H-PRE sealed nine UNPARSED rows")
        for row in unparsed:
            decision = SL.decide(
                _rest(row["line"]),
                inputs,
                session_id="stop-condition",
                turn_index=row["turn_index"],
            )
            self.assertEqual(decision.verdict.verdict, SL.VERDICT_REFUSED, row["line"])
            self.assertEqual(decision.verdict.refusal_code, "UNPARSED", row["line"])
            self.assertEqual(
                decision.verdict.deciding_clause, "c1_unparsed", row["line"]
            )
            self.assertIsNone(decision.parsed, row["line"])

    def test_parse_declaration_is_total_over_every_sealed_surface(self) -> None:
        """It returns, for every sealed byte string, including the use lines."""

        for row in _fixtures()["fixtures"]:
            for candidate in (row["line"], _rest(row["line"]), ""):
                try:
                    SL.parse_declaration(candidate)
                except Exception as exc:  # noqa: BLE001
                    self.fail(f"parse_declaration raised on {candidate!r}: {exc}")


class TheSealedFixturesGetTheirSealedVerdicts(unittest.TestCase):
    """Every declaration fixture, replayed in its own session in turn order."""

    def test_every_declaration_fixture_matches_its_sealed_verdict(self) -> None:
        document = _fixtures()
        inputs = _inputs()
        checked = 0
        for session_id, rows in _sessions(document).items():
            admitted: list[str] = []
            binding: set[str] = set()
            heads: set[str] = set()
            for row in rows:
                if row["kind"] == "use":
                    if row.get("binds_subject"):
                        binding.add(SL.normalize(row["binds_subject"]))
                    elif row.get("read_applied_head"):
                        heads.add(SL.normalize(row["read_applied_head"]))
                    continue
                decision = SL.decide(
                    _rest(row["line"]),
                    inputs,
                    session_id=session_id,
                    turn_index=row["turn_index"],
                    admitted=tuple(admitted),
                    session_names=SL.SessionNames(
                        admitted_symbols=frozenset(admitted),
                        binding_subjects=frozenset(binding),
                        applied_heads=frozenset(heads),
                    ),
                )
                self.assertEqual(
                    decision.verdict.verdict,
                    row["expected_verdict"],
                    row["fixture_id"],
                )
                self.assertEqual(
                    decision.verdict.refusal_code,
                    row["expected_refusal_code"],
                    row["fixture_id"],
                )
                self.assertEqual(
                    decision.verdict.deciding_clause,
                    row["expected_deciding_clause"],
                    row["fixture_id"],
                )
                if decision.admitted:
                    admitted.append(decision.declaration.symbol_name)
                checked += 1
        self.assertEqual(checked, document["counts"]["declaration_fixtures"])
        self.assertEqual(checked, 38)

    def test_the_normalization_order_is_nfc_then_casefold(self) -> None:
        """Session s5's fixtures disagree under `.lower()` or match-first."""

        document = _fixtures()
        inputs = _inputs()
        s5 = [
            row
            for row in document["fixtures"]
            if row["session_id"] == "hr-fx-s5" and row["kind"] == "declaration"
        ]
        self.assertTrue(s5)
        for row in s5:
            parsed = SL.parse_declaration(_rest(row["line"]))
            if row["expected_verdict"] == SL.VERDICT_ADMITTED:
                self.assertIsNotNone(parsed, row["fixture_id"])
                self.assertEqual(
                    parsed.symbol_name, row["read_symbol_name"], row["fixture_id"]
                )
                # The whole point: the key is NOT the bytes that were typed.
                self.assertNotEqual(
                    parsed.symbol_name, row["raw_symbol_name"], row["fixture_id"]
                )
            else:
                # A combining accent still refuses, so the rule cannot be read
                # as "normalize until it fits".
                self.assertIsNone(parsed, row["fixture_id"])
        del inputs

    def test_lower_alone_would_fail_the_sealed_corpus(self) -> None:
        """The mutation that H-PRE's review said H-P0 could otherwise ship."""

        raw = "ﬁrst_of"
        self.assertNotEqual(raw.lower(), "first_of")
        self.assertEqual(SL.normalize(raw), "first_of")


class TheClauseOrderDecidesExactlyOnce(unittest.TestCase):
    """B1's exclusivity, and the order-sensitivity H-PRE sealed for it."""

    def test_the_committed_order_is_the_designs_order(self) -> None:
        document = _fixtures()
        self.assertEqual(
            [clause for clause, _ in SL.CLAUSE_ORDER],
            [row["clause"] for row in document["clause_order"]],
        )
        self.assertEqual(
            list(SL.REFUSAL_CODES),
            [row["refusal_code"] for row in document["clause_order"]],
        )
        self.assertEqual(SL.CLAUSE_ADMIT, "c9_admit")

    def test_symbol_budget_is_last_so_a_bad_fifth_line_is_refused_for_being_bad(
        self,
    ) -> None:
        self.assertEqual(SL.REFUSAL_CODES[-1], "SYMBOL_BUDGET")

    def test_every_order_sensitive_fixture_grounds_its_later_codes_too(self) -> None:
        """H-PRE's `also_grounds_for`, checked rather than trusted.

        This is the check the H-PRE review called highest-value: verifying
        only that the expected code is earliest among the DECLARED grounds
        cannot see a fixture that OMITTED an earlier ground. Comparing the
        full computed set against the sealed one can.
        """

        document = _fixtures()
        inputs = _inputs()
        seen = 0
        for session_id, rows in _sessions(document).items():
            admitted: list[str] = []
            binding: set[str] = set()
            heads: set[str] = set()
            for row in rows:
                if row["kind"] == "use":
                    if row.get("binds_subject"):
                        binding.add(SL.normalize(row["binds_subject"]))
                    elif row.get("read_applied_head"):
                        heads.add(SL.normalize(row["read_applied_head"]))
                    continue
                parsed = SL.parse_declaration(_rest(row["line"]))
                grounds = SL.grounds_for(
                    parsed,
                    inputs,
                    admitted=tuple(admitted),
                    session_names=SL.SessionNames(
                        admitted_symbols=frozenset(admitted),
                        binding_subjects=frozenset(binding),
                        applied_heads=frozenset(heads),
                    ),
                )
                sealed = set(row["also_grounds_for"])
                if row["expected_refusal_code"] != "NONE":
                    sealed.add(row["expected_refusal_code"])
                self.assertEqual(set(grounds), sealed, row["fixture_id"])
                if row["order_sensitive"]:
                    self.assertGreater(len(grounds), 1, row["fixture_id"])
                    self.assertEqual(
                        grounds[0], row["expected_refusal_code"], row["fixture_id"]
                    )
                    seen += 1
                if not grounds:
                    admitted.append(parsed.symbol_name)
        self.assertEqual(
            seen, len(document["coverage"]["order_sensitive_fixture_ids"])
        )

    def test_the_three_session_name_subcases_are_named_and_reached(self) -> None:
        document = _fixtures()
        inputs = _inputs()
        sealed = {
            row["fixture_id"]: row["session_name_subcase"]
            for row in document["fixtures"]
            if row["kind"] == "declaration" and row.get("session_name_subcase")
        }
        self.assertTrue(sealed)
        for subcase in sealed.values():
            self.assertIn(subcase, SL.SESSION_NAME_SUBCASES)

        names = SL.SessionNames(
            admitted_symbols=frozenset({"already"}),
            binding_subjects=frozenset({"bound"}),
            applied_heads=frozenset({"applied"}),
        )
        self.assertEqual(names.subcase("already"), "already_admitted_symbol")
        self.assertEqual(names.subcase("bound"), "supposition_binding_subject")
        self.assertEqual(
            names.subcase("applied"), "live_non_binding_supposition_head"
        )
        self.assertIsNone(names.subcase("fresh"))
        del inputs


class B1TotalityOverAMachineEnumeratedSweep(unittest.TestCase):
    """B1: not the authored corpus — inputs the author did not pick."""

    def _sweep(self) -> list[str]:
        """Single-token deletion and substitution over the fixture alphabet."""

        document = _fixtures()
        lines = [
            _rest(row["line"])
            for row in document["fixtures"]
            if row["kind"] == "declaration"
        ]
        alphabet = sorted(
            {token for line in lines for token in line.replace(",", " ").split()}
        )
        out: list[str] = []
        for line in lines:
            tokens = line.split()
            for index in range(len(tokens)):
                out.append(" ".join(tokens[:index] + tokens[index + 1 :]))
                for replacement in alphabet[:12]:
                    out.append(
                        " ".join(
                            tokens[:index] + [replacement] + tokens[index + 1 :]
                        )
                    )
        return out

    def test_every_swept_input_gets_exactly_one_verdict_and_one_clause(self) -> None:
        inputs = _inputs()
        sweep = self._sweep()
        self.assertGreater(len(sweep), 400, "the sweep must not be trivial")
        clauses = set(SL.CLAUSE_IDS) | {SL.CLAUSE_ADMIT}
        for line in sweep:
            decision = SL.decide(
                line, inputs, session_id="b1-sweep", turn_index=1
            )
            self.assertIn(
                decision.verdict.verdict,
                {SL.VERDICT_ADMITTED, SL.VERDICT_REFUSED},
                line,
            )
            self.assertIn(decision.verdict.deciding_clause, clauses, line)
            if decision.admitted:
                self.assertEqual(decision.verdict.refusal_code, SL.REFUSAL_NONE, line)
                self.assertEqual(decision.verdict.deciding_clause, SL.CLAUSE_ADMIT, line)
            else:
                self.assertIn(decision.verdict.refusal_code, SL.REFUSAL_CODES, line)
                self.assertEqual(
                    decision.verdict.deciding_clause,
                    SL._CLAUSE_BY_CODE[decision.verdict.refusal_code],
                    line,
                )

    def test_the_sweep_is_not_all_one_code(self) -> None:
        """A total function that answers UNPARSED to everything is useless.

        This is not B7 — B7's 6-of-8 floor is H-P1's to score on the
        registered sweep. This is the weaker construction-time check that the
        sweep reaches more than one clause at all, so a checker that had
        collapsed would be caught here rather than at H-P1.
        """

        inputs = _inputs()
        reached = {
            SL.decide(line, inputs, session_id="b1-sweep", turn_index=1)
            .verdict.refusal_code
            for line in self._sweep()
        }
        self.assertGreater(len(reached), 1, sorted(reached))


class B2FreshnessAgainstTheCommittedCensus(unittest.TestCase):
    """The artifact, and the second program that proves it reproduces."""

    def test_the_census_checker_agrees_with_the_committed_artifact(self) -> None:
        run = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "check_symbol_census.py")],
            capture_output=True,
            text=True,
            cwd=str(REPO),
            env=None,
        )
        self.assertEqual(run.returncode, 0, (run.stderr or run.stdout)[-1200:])
        self.assertIn("CENSUS OK", run.stdout)

    def test_the_builder_and_the_checker_are_two_programs(self) -> None:
        """B2's structure: a shared bug must not be able to hide here."""

        source = (REPO / "scripts" / "check_symbol_census.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("import build_symbol_census", source)
        self.assertNotIn("from build_symbol_census", source)

    def test_the_two_extractions_agree_member_for_member(self) -> None:
        fresh = checker.recompute(REPO)
        built = builder.build_census(REPO)
        self.assertEqual(built["equality_members"], fresh["equality_members"])
        self.assertEqual(built["members_by_source"], fresh["members_by_source"])

    def test_no_admitted_fixture_symbol_collides_with_the_census(self) -> None:
        document = _fixtures()
        inputs = _inputs()
        admitted = [
            row["read_symbol_name"]
            for row in document["fixtures"]
            if row["kind"] == "declaration"
            and row["expected_verdict"] == SL.VERDICT_ADMITTED
        ]
        self.assertEqual(len(admitted), 13)
        for name in admitted:
            self.assertNotIn(name, inputs.equality_members, name)
            self.assertFalse(name.startswith(tuple(inputs.reserved_prefixes)), name)

    def test_the_named_collision_targets_are_all_in_the_census(self) -> None:
        """H-PRE verified these against the graph; the census must hold them."""

        document = _fixtures()
        inputs = _inputs()
        for target in document["library_collision_targets"]:
            name = target["name"]
            if name.startswith(tuple(inputs.reserved_prefixes)):
                # `sum_i` is guarded by the prefix rule AND is a member; both.
                self.assertIn(name, inputs.equality_members, name)
            else:
                self.assertIn(name, inputs.equality_members, name)

    def test_the_prefix_guard_is_distinct_from_the_equality_members(self) -> None:
        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        guard = census["prefix_guard"]
        self.assertEqual(guard["prefixes_that_are_also_equality_members"], [])
        self.assertTrue(guard["distinct_from_equality_members"])
        for prefix in guard["prefixes"]:
            self.assertNotIn(prefix, census["equality_members"])

    def test_the_prefixes_are_the_shipped_parsers_own(self) -> None:
        """Read textually out of match_signatures, so a drift there goes red."""

        source = (REPO / "scripts" / "match_signatures.py").read_text(
            encoding="utf-8"
        )
        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        for prefix in census["prefix_guard"]["prefixes"]:
            self.assertIn(f'"{prefix}"', source, prefix)

    def test_the_census_records_provenance_per_source(self) -> None:
        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        self.assertEqual(len(census["sources"]), 10)
        for source in census["sources"]:
            self.assertIn("raw_member_count", source)
            self.assertIn("name_shaped_member_count", source)
            self.assertGreaterEqual(
                source["raw_member_count"], source["name_shaped_member_count"]
            )
        by_name = {row["source"]: row for row in census["sources"]}
        # The five lexicon categories, at the distinct counts DESIGN §4 quotes.
        for category, expected in (
            ("symbols", 221),
            ("operators", 40),
            ("functionals", 95),
            ("constants", 37),
            ("index_sets", 12),
        ):
            self.assertEqual(
                by_name[f"symbol_lexicon.{category}"]["raw_member_count"],
                expected,
                category,
            )

    def test_glyph_members_are_carried_without_pretending_to_guard(self) -> None:
        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        operators = census["raw_members_by_source"]["symbol_lexicon.operators"]
        shaped = census["members_by_source"]["symbol_lexicon.operators"]
        self.assertGreater(len(operators), len(shaped))
        self.assertIn("implies", shaped)
        # Compare NORMALIZED raw members against the shaped set: a raw `X`
        # normalizes onto the name-shaped `x`, so differencing raw strings
        # against normalized ones would call it a glyph when it is not.
        carried_only = {
            member
            for member in operators
            if not SL.is_name_shaped(SL.normalize(member))
        }
        self.assertTrue(carried_only)
        self.assertEqual(len(carried_only), len(operators) - len(shaped))
        for glyph in carried_only:
            self.assertNotIn(SL.normalize(glyph), census["equality_members"])


class B6TheUseSideCheckIsLiveAndFenced(unittest.TestCase):
    """The refusal, and the fence that says what did NOT change."""

    def test_every_wrong_arity_use_refuses_and_names_the_declaration(self) -> None:
        document = _fixtures()
        inputs = _inputs()
        fired = 0
        for session_id, rows in _sessions(document).items():
            session = _live_session(session_id, inputs)
            for row in rows:
                session.assumptions.barrier.open_turn(row["turn_index"])
                verdict = harness.route_line(REPO, session, row["line"])
                session.assumptions.barrier.close_turn()
                if row["kind"] != "use":
                    continue
                if row["expected_disposition"] == "USE_ARITY_MISMATCH":
                    self.assertEqual(verdict["route"], "supposition", row["fixture_id"])
                    self.assertEqual(verdict["status"], "refused", row["fixture_id"])
                    self.assertEqual(
                        verdict.get("refusal_type"),
                        SL.REFUSAL_USE_ARITY_MISMATCH,
                        row["fixture_id"],
                    )
                    self.assertIn(
                        row["cites_declaration_symbol"],
                        verdict["detail"],
                        row["fixture_id"],
                    )
                    fired += 1
        self.assertEqual(fired, document["counts"]["use_arity_mismatch"])
        self.assertEqual(fired, 3)

    def test_an_undeclared_applied_atom_is_byte_identical_to_the_pre_slice_path(
        self,
    ) -> None:
        """B6's fence, replayed against BOTH code paths as B6 specifies.

        The pre-slice path is reproduced exactly: a session with no symbol
        ledger attached is, by construction, the code that ran before this
        slice existed — `_route_suppose`'s new block is guarded on
        `session.symbols` being present. So the two arms below are the two
        code paths, and the assertion is that they render the same bytes.
        """

        document = _fixtures()
        inputs = _inputs()
        opaque = [
            row
            for row in document["fixtures"]
            if row["kind"] == "use"
            and row["expected_disposition"] in {"OPAQUE_ATOM", "BINDING_SUPPOSITION_UNCHANGED"}
        ]
        self.assertEqual(len(opaque), 5)
        for row in opaque:
            with_slice = _live_session("fence-with", inputs)
            without = harness.CoreSession.boot(
                REPO, offline=True, session_id="fence-without"
            )
            without.assumptions = ledger.AssumptionSet(
                session_id="fence-without", barrier=ledger.ReadBarrier()
            )
            self.assertIsNone(without.symbols)

            with_slice.assumptions.barrier.open_turn(1)
            without.assumptions.barrier.open_turn(1)
            left = harness.route_line(REPO, with_slice, row["line"])
            right = harness.route_line(REPO, without, row["line"])
            with_slice.assumptions.barrier.close_turn()
            without.assumptions.barrier.close_turn()
            self.assertEqual(left, right, row["fixture_id"])

    def test_a_use_of_a_declared_symbol_with_the_right_arity_is_still_a_supposition(
        self,
    ) -> None:
        """A checked use is well-formed, never true. It stays held."""

        inputs = _inputs()
        session = _live_session("checked-use", inputs)
        session.assumptions.barrier.open_turn(1)
        harness.route_line(REPO, session, "declare parent_of/2 (variable, variable)")
        session.assumptions.barrier.close_turn()
        session.assumptions.barrier.open_turn(2)
        verdict = harness.route_line(REPO, session, "suppose parent_of(alice, bob)")
        session.assumptions.barrier.close_turn()
        self.assertEqual(verdict["route"], "supposition")
        self.assertNotEqual(verdict["status"], "refused")

    def test_the_two_spellings_of_the_refusal_name_agree(self) -> None:
        self.assertEqual(
            harness.USE_ARITY_MISMATCH, SL.REFUSAL_USE_ARITY_MISMATCH
        )
        self.assertEqual(SL.REFUSAL_USE_ARITY_MISMATCH, "USE_ARITY_MISMATCH")

    def test_use_arity_mismatch_is_not_an_admissibility_code(self) -> None:
        """§3: not a third record, and deliberately absent from the order."""

        self.assertNotIn(SL.REFUSAL_USE_ARITY_MISMATCH, SL.REFUSAL_CODES)
        self.assertNotIn(
            SL.REFUSAL_USE_ARITY_MISMATCH, [c for c, _ in SL.CLAUSE_ORDER]
        )


class B12RoundTripIdentity(unittest.TestCase):
    """An admitted name survives parsing unchanged, back to the ledger key."""

    def test_every_sealed_round_trip_pair_resolves_to_the_ledger_key(self) -> None:
        document = _fixtures()
        inputs = _inputs()
        pairs = 0
        for session_id, rows in _sessions(document).items():
            keys: dict[str, str] = {}
            for row in rows:
                if row["kind"] == "declaration":
                    parsed = SL.parse_declaration(_rest(row["line"]))
                    if parsed is not None and row["expected_verdict"] == SL.VERDICT_ADMITTED:
                        keys[parsed.symbol_name] = parsed.symbol_name
                    continue
                target = row.get("round_trip_for")
                if not target:
                    continue
                head = SL.applied_head(_rest(row["line"]))
                self.assertIsNotNone(head, row["fixture_id"])
                self.assertEqual(head[0], target, row["fixture_id"])
                self.assertIn(head[0], keys, row["fixture_id"])
                self.assertEqual(head[0], keys[head[0]], row["fixture_id"])
                pairs += 1
        self.assertEqual(pairs, document["counts"]["round_trip_pairs"])
        self.assertEqual(pairs, 13)
        del inputs

    def test_every_b12_mutant_gets_its_sealed_verdict(self) -> None:
        document = _fixtures()
        inputs = _inputs()
        for mutant in document["b12_round_trip"]["mutants"]:
            decision = SL.decide(
                _rest(mutant["line"]),
                inputs,
                session_id="b12",
                turn_index=1,
            )
            self.assertEqual(
                decision.verdict.verdict,
                mutant["expected_verdict"],
                mutant["mutant_id"],
            )
            self.assertEqual(
                decision.verdict.refusal_code,
                mutant["expected_refusal_code"],
                mutant["mutant_id"],
            )
            self.assertEqual(
                decision.verdict.deciding_clause,
                mutant["expected_deciding_clause"],
                mutant["mutant_id"],
            )
            sealed = set(mutant["also_grounds_for"])
            if mutant["expected_refusal_code"] != "NONE":
                sealed.add(mutant["expected_refusal_code"])
            self.assertEqual(set(decision.grounds), sealed, mutant["mutant_id"])

    def test_every_admitted_mutant_round_trips_to_its_declared_key(self) -> None:
        document = _fixtures()
        for mutant in document["b12_round_trip"]["mutants"]:
            if not mutant["expected_resolved_key"]:
                continue
            head = SL.applied_head(_rest(mutant["use_line"]))
            self.assertIsNotNone(head, mutant["mutant_id"])
            self.assertEqual(
                head[0], mutant["expected_resolved_key"], mutant["mutant_id"]
            )

    def test_the_reserved_prefix_adjacent_names_are_the_parsers_own(self) -> None:
        from match_signatures import BIG_OP_PREFIXES  # noqa: PLC0415

        document = _fixtures()
        self.assertEqual(
            sorted(document["b12_round_trip"]["reserved_prefixes"]),
            sorted(BIG_OP_PREFIXES),
        )


class B8Corruption(unittest.TestCase):
    """Both arms, each mutating a COPY and naming its target fixture."""

    def test_removing_a_census_member_flips_the_admission_it_blocked(self) -> None:
        inputs = _inputs()
        target = "meet"
        line = "meet/2 (set, set)"
        self.assertEqual(
            SL.decide(line, inputs, session_id="b8", turn_index=1)
            .verdict.refusal_code,
            "COLLIDES_WITH_LIBRARY_SYMBOL",
        )
        corrupted = SL.CommittedInputs(
            census_path=inputs.census_path,
            census_sha256_lf=inputs.census_sha256_lf,
            equality_members=inputs.equality_members - {target},
            reserved_prefixes=inputs.reserved_prefixes,
            schema_path=inputs.schema_path,
            schema_sha256_lf=inputs.schema_sha256_lf,
            categories=inputs.categories,
        )
        flipped = SL.decide(line, corrupted, session_id="b8", turn_index=1)
        self.assertEqual(flipped.verdict.verdict, SL.VERDICT_ADMITTED)
        self.assertEqual(flipped.verdict.deciding_clause, SL.CLAUSE_ADMIT)

    def test_removing_a_schema_category_flips_every_fixture_citing_it(self) -> None:
        document = _fixtures()
        inputs = _inputs()
        target = "statistic"
        corrupted = SL.CommittedInputs(
            census_path=inputs.census_path,
            census_sha256_lf=inputs.census_sha256_lf,
            equality_members=inputs.equality_members,
            reserved_prefixes=inputs.reserved_prefixes,
            schema_path=inputs.schema_path,
            schema_sha256_lf=inputs.schema_sha256_lf,
            categories=inputs.categories - {target},
        )
        citing = [
            row
            for row in document["fixtures"]
            if row["kind"] == "declaration"
            and row["expected_verdict"] == SL.VERDICT_ADMITTED
            and target in (row["read_argument_categories"] or [])
        ]
        self.assertTrue(citing, "no admitted fixture cites the mutated category")
        for row in citing:
            flipped = SL.decide(
                _rest(row["line"]), corrupted, session_id="b8", turn_index=1
            )
            self.assertEqual(
                flipped.verdict.refusal_code,
                "CATEGORY_NOT_IN_SCHEMA",
                row["fixture_id"],
            )

    def test_a_corrupted_census_file_changes_the_digest_a_verdict_cites(self) -> None:
        """The census_ref is what makes a verdict reproducible; it must move."""

        import tempfile  # noqa: PLC0415

        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        census["equality_members"] = [
            name for name in census["equality_members"] if name != "meet"
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "experiments").mkdir()
            (root / "schema").mkdir()
            (root / "experiments" / "symbol_census.json").write_text(
                json.dumps(census), encoding="utf-8"
            )
            (root / "schema" / "equation-node.schema.json").write_bytes(
                (REPO / "schema" / "equation-node.schema.json").read_bytes()
            )
            corrupted = SL.load_inputs(root)
        self.assertNotEqual(corrupted.census_sha256_lf, _inputs().census_sha256_lf)
        self.assertEqual(corrupted.schema_sha256_lf, _inputs().schema_sha256_lf)


class TheBudgetIsFourAndIsRefusedBeforeAnyMutation(unittest.TestCase):
    def test_the_cap_is_four_and_the_fifth_refuses(self) -> None:
        inputs = _inputs()
        ledger_ = SL.SymbolLedger(session_id="budget", inputs=inputs)
        self.assertEqual(ledger_.cap, 4)
        self.assertEqual(SL.SYMBOL_CAP, 4)
        for index, name in enumerate(
            ["alpha_of", "beta_of", "gamma_of", "delta_of"], start=1
        ):
            decision = ledger_.declare(f"{name}/1 (variable)", index)
            self.assertTrue(decision.admitted, name)
            self.assertEqual(len(ledger_.admitted_names()), index)
        fifth = ledger_.declare("epsilon_of/1 (variable)", 5)
        self.assertEqual(fifth.verdict.refusal_code, "SYMBOL_BUDGET")
        self.assertEqual(len(ledger_.admitted_names()), 4, "the ledger MUTATED")
        self.assertNotIn("epsilon_of", ledger_.admitted_names())

    def test_the_cap_is_below_the_live_assumption_cap(self) -> None:
        self.assertLess(SL.SYMBOL_CAP, ledger.LIVE_ASSUMPTION_CAP)

    def test_a_redefinition_is_refused_and_does_not_supersede(self) -> None:
        """Unlike a supposition, a declaration is NOT superseded by a second."""

        inputs = _inputs()
        ledger_ = SL.SymbolLedger(session_id="redef", inputs=inputs)
        first = ledger_.declare("cohort_of/2 (set, index)", 1)
        self.assertTrue(first.admitted)
        second = ledger_.declare("cohort_of/3 (set, index, index)", 2)
        self.assertEqual(second.verdict.refusal_code, "REDEFINITION_ATTEMPT")
        self.assertEqual(ledger_.declaration_for("cohort_of").arity, 2)
        self.assertEqual(len(ledger_.admitted_names()), 1)

    def test_decide_mutates_nothing(self) -> None:
        inputs = _inputs()
        ledger_ = SL.SymbolLedger(session_id="pure", inputs=inputs)
        SL.decide("alpha_of/1 (variable)", inputs, session_id="pure", turn_index=1)
        self.assertEqual(ledger_.admitted_names(), ())


class TheRecordsAreSessionScopedAndUnserializable(unittest.TestCase):
    """B5's codec leg. Not the fence — the codec agreeing with the fence."""

    def _records(self):
        inputs = _inputs()
        decision = SL.decide(
            "parent_of/2 (variable, variable)",
            inputs,
            session_id="codec",
            turn_index=1,
        )
        return decision.declaration, decision.verdict

    def test_neither_record_type_is_registered(self) -> None:
        self.assertNotIn("PersonSymbolDeclaration", session_state._TYPES)
        self.assertNotIn("AdmissibilityVerdict", session_state._TYPES)

    def test_encode_refuses_both_records(self) -> None:
        declaration, verdict = self._records()
        for record in (declaration, verdict):
            with self.assertRaises(session_state.SessionFormatError) as caught:
                session_state.encode(record)
            self.assertIn("unregistered dataclass", str(caught.exception))

    def test_a_fresh_session_has_forgotten_an_admitted_symbol(self) -> None:
        """B5's third leg, and the sealed s4 fixtures are its witness."""

        inputs = _inputs()
        first = _live_session("gone-1", inputs)
        first.assumptions.barrier.open_turn(1)
        harness.route_line(REPO, first, "declare sun_total/1 (variable)")
        first.assumptions.barrier.close_turn()
        self.assertIn("sun_total", first.symbols.admitted_names())

        fresh = _live_session("gone-2", inputs)
        self.assertEqual(fresh.symbols.admitted_names(), ())
        fresh.assumptions.barrier.open_turn(1)
        verdict = harness.route_line(REPO, fresh, "suppose sun_total(9)")
        fresh.assumptions.barrier.close_turn()
        self.assertNotEqual(verdict["status"], "refused")
        self.assertIsNone(fresh.symbols.check_use("sun_total(9)"))

    def test_the_decl_id_is_the_digest_of_the_record_with_decl_id_empty(self) -> None:
        declaration, verdict = self._records()
        payload = declaration.payload()
        payload["decl_id"] = ""
        self.assertEqual(declaration.decl_id, SL.digest(payload))
        self.assertEqual(verdict.decl_id, declaration.decl_id)

    def test_the_verdict_cites_both_committed_inputs(self) -> None:
        inputs = _inputs()
        _, verdict = self._records()
        self.assertEqual(verdict.schema_digest, inputs.schema_sha256_lf)
        self.assertEqual(verdict.census_ref["path"], SL.CENSUS_PATH)
        self.assertEqual(verdict.census_ref["sha256_lf"], inputs.census_sha256_lf)
        self.assertEqual(
            verdict.schema_digest, SL.sha256_lf(REPO / SL.SCHEMA_PATH)
        )

    def test_the_schemas_are_the_designs_names(self) -> None:
        declaration, verdict = self._records()
        self.assertEqual(declaration.schema, "corollary.person-symbol-declaration/1")
        self.assertEqual(verdict.schema, "corollary.admissibility-verdict/1")


class B11NoLearnedPath(unittest.TestCase):
    """The import-closure assertion, in `echo_population_audit`'s pattern."""

    #: Anything on the admission path that could make a decision by fitting
    #: rather than by reading. Named rather than pattern-matched so a reader
    #: can see what is being excluded.
    FORBIDDEN = (
        "torch",
        "numpy",
        "sklearn",
        "transformers",
        "plain_router",
        "proposer",
        "wordnet",
        "retrieve",
    )

    def _closure(self, relative: str) -> list[str]:
        from echo_population_audit import import_closure  # noqa: PLC0415

        return import_closure(relative)

    def test_the_checker_and_the_ledger_close_over_exact_modules_only(self) -> None:
        for relative in (
            "scripts/symbol_ledger.py",
            "scripts/build_symbol_census.py",
            "scripts/check_symbol_census.py",
        ):
            closure = self._closure(relative)
            self.assertEqual(
                closure,
                sorted(
                    {
                        relative,
                        "scripts/match_signatures.py",
                        "scripts/report_provenance.py",
                    }
                ),
                relative,
            )

    def test_no_forbidden_module_is_reachable_from_the_admission_path(self) -> None:
        closure = self._closure("scripts/symbol_ledger.py")
        for module in closure:
            for forbidden in self.FORBIDDEN:
                self.assertNotIn(forbidden, module, (module, forbidden))

    def test_the_closure_walk_refuses_a_dynamic_import(self) -> None:
        """The assertion is only worth anything if its walk can go red."""

        from echo_population_audit import AuditRefusal  # noqa: PLC0415

        with self.assertRaises(AuditRefusal):
            # `serve_chat` calls importlib.import_module; the walk refuses it.
            self._closure("scripts/serve_chat.py")


class TheGrammarRowIsRegisteredAndItsPinsMoved(unittest.TestCase):
    """§6.2's row, and the disclosure it owes against prior art."""

    def _row(self) -> dict:
        from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

        rows = [row for row in LINE_GRAMMAR if row["route"] == "declaration"]
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_the_row_is_the_designs_form_route_and_statuses(self) -> None:
        row = self._row()
        self.assertEqual(row["form"], "declare <name>/<arity> (<category>, ...)")
        self.assertEqual(row["route"], "declaration")
        self.assertEqual(sorted(row["statuses"]), ["held", "refused"])
        self.assertEqual(row["requires"], ())

    def test_the_row_sits_immediately_after_retract(self) -> None:
        from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

        routes = [row["route"] for row in LINE_GRAMMAR]
        self.assertEqual(
            routes[routes.index("retraction") + 1],
            "declaration",
            "the grammar mirrors route_line's chain in order",
        )

    def test_the_row_publishes_its_dev1_note_like_retract_does(self) -> None:
        row = self._row()
        self.assertIn("¶DEV-1", row["note"])
        self.assertIn("fresh sessions", row["note"])

    def test_the_row_discloses_declare_against_define_and_suppose(self) -> None:
        """§6.2 requires the prior-art disclosure to be published, not implied."""

        note = self._row()["note"]
        self.assertIn("define X", note)
        self.assertIn("WordNet", note)
        self.assertIn("suppose", note)

    def test_every_status_is_in_the_frozen_alphabet(self) -> None:
        from serve_chat import (  # noqa: PLC0415
            ENGINE_STATUSES,
            SKIN_ASSIGNED_STATUSES,
            WRITE_GATE_STATUSES,
        )

        alphabet = set(ENGINE_STATUSES) | set(WRITE_GATE_STATUSES) | set(
            SKIN_ASSIGNED_STATUSES
        )
        for status in self._row()["statuses"]:
            self.assertIn(status, alphabet)

    def test_the_capability_sheet_publishes_the_row(self) -> None:
        import serve_chat  # noqa: PLC0415

        engine = serve_chat.ChatEngine(REPO)
        sheet = engine.capability_sheet()
        rows = [
            row for row in sheet["line_grammar"] if row["route"] == "declaration"
        ]
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["served"])
        self.assertIn("¶DEV-1", rows[0]["note"])

    def test_the_served_skin_attaches_no_symbol_ledger(self) -> None:
        """¶DEV-1: declared vocabulary cannot cross an HTTP turn."""

        session = harness.CoreSession.boot(REPO, offline=True)
        self.assertIsNone(session.symbols)
        verdict = harness.route_line(
            REPO, session, "declare parent_of/2 (variable, variable)"
        )
        self.assertEqual(verdict["route"], "declaration")
        self.assertEqual(verdict["status"], "refused")
        self.assertEqual(verdict["refusal_type"], harness.NO_SYMBOL_LEDGER)

    def test_no_symbol_ledger_is_not_an_admissibility_code(self) -> None:
        self.assertNotIn(harness.NO_SYMBOL_LEDGER, SL.REFUSAL_CODES)

    def test_the_command_bound_artifact_carries_the_declaration_class(self) -> None:
        artifact = json.loads(
            (REPO / "experiments" / "session_p1_command_bound.json").read_text(
                encoding="utf-8"
            )
        )
        rows = [
            row for row in artifact["classes"] if row["route"] == "declaration"
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["bound_kind"], "open")
        self.assertEqual(rows[0]["class_index"], 5)
        self.assertEqual(artifact["totals"]["template_classes"], 16)
        self.assertIn(5, artifact["totals"]["open_class_indices"])

    def test_the_closed_total_did_not_move(self) -> None:
        """An open class adds no counted commands; the bound is unchanged."""

        artifact = json.loads(
            (REPO / "experiments" / "session_p1_command_bound.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(artifact["totals"]["closed_total"], 34863)


class TheHonestyNotesTravelWithTheCapability(unittest.TestCase):
    def test_the_module_says_what_an_admission_does_not_certify(self) -> None:
        source = (REPO / "scripts" / "symbol_ledger.py").read_text(encoding="utf-8")
        self.assertIn("ledger-groundedness, never correspondence", source)
        self.assertIn("never true", source)

    def test_the_admitted_render_says_it_is_not_a_truth_claim(self) -> None:
        inputs = _inputs()
        session = _live_session("honesty", inputs)
        session.assumptions.barrier.open_turn(1)
        verdict = harness.route_line(
            REPO, session, "declare parent_of/2 (variable, variable)"
        )
        session.assumptions.barrier.close_turn()
        self.assertEqual(verdict["status"], "held")
        rendered = " ".join(verdict["answer"])
        self.assertIn("never that it is true", rendered)
        self.assertIn("session only", rendered)

    def test_the_census_carries_its_prose_deviations(self) -> None:
        """H-PRE found four; the builder is their named consumer."""

        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        self.assertEqual(len(census["design_prose_deviations"]), 4)
        for row in census["design_prose_deviations"]:
            self.assertTrue(row["finding"].strip())
            self.assertTrue(row["this_builder_does"].strip())

    def test_the_leading_identifier_rule_is_written_down(self) -> None:
        """H-PRE said H-P0 still owed this rule in writing."""

        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        rule = census["leading_identifier_rule"]
        self.assertIn("MAXIMAL", rule)
        self.assertIn("sum_i", rule)
        self.assertIn("sum_i", census["members_by_source"]["functional_leading_identifiers"])
        self.assertIn("sum", census["members_by_source"]["head_aliases_keys"])


class TheSupposedHeadsAreReadWithoutTouchingThePinnedRecorder(unittest.TestCase):
    """§4's third source, read from OUTSIDE the byte-frozen recorder."""

    def _live(self):
        live = ledger.AssumptionSet(session_id="heads", barrier=ledger.ReadBarrier())
        live.barrier.open_turn(1)
        live.declare("parent_link(alice, bob)", 1)
        live.declare("headcount = 12", 1)
        live.barrier.close_turn()
        return live

    def test_it_reports_non_binding_supposition_heads_only(self) -> None:
        live = self._live()
        self.assertEqual(
            SL.supposition_applied_heads(live), frozenset({"parent_link"})
        )
        self.assertEqual(live.bound_names(), frozenset({"headcount"}))

    def test_reading_the_heads_fires_no_read_event(self) -> None:
        """Barrier-free for `subject`'s own reason, and it must stay so."""

        live = self._live()
        before = len(live.barrier.events)
        SL.supposition_applied_heads(live)
        self.assertEqual(len(live.barrier.events), before)

    def test_it_never_reads_the_private_binding(self) -> None:
        """The bypass the read barrier exists to make visible."""

        # Attribute ACCESS, not the word: the module's own prose explains
        # which attributes it declines to touch, and a check that could not
        # tell an explanation from a bypass would be the weaker check.
        source = (REPO / "scripts" / "symbol_ledger.py").read_text(encoding="utf-8")
        for access in ("._binding", ".normal_form", ".binding_for(", ".polarity"):
            self.assertNotIn(access, source, access)


class ThePinnedRecorderWasNotEdited(unittest.TestCase):
    """The rule prereg amendment 6 states, enforced here as a test.

    DESIGN-house-rules §3 asks for `USE_ARITY_MISMATCH` inside
    `scripts/session_ledger.py`. That module is one of the two
    RECORDER_MODULES pinned by `recorder_code_digest`, whose value is frozen
    in `session_ledger_prereg.json`'s amendment 1 and copied into the sealed
    corpus; `record_session_corpus.py` refuses to record under a recorder
    whose bytes moved. So the design's prose is honored in intent and refused
    in placement, and this test is why that cannot quietly regress.
    """

    def test_the_recorder_digest_is_unmoved(self) -> None:
        from session_recorder import recorder_code_digest  # noqa: PLC0415

        prereg = json.loads(
            (REPO / "experiments" / "session_ledger_prereg.json").read_text(
                encoding="utf-8"
            )
        )
        frozen = prereg["amendments"][0]["adds"]["recorder_code_digest"]
        self.assertEqual(recorder_code_digest(REPO), frozen)

    def test_this_slice_added_nothing_to_the_recorder_modules(self) -> None:
        from session_recorder import RECORDER_MODULES  # noqa: PLC0415

        for relative in RECORDER_MODULES:
            source = (REPO / relative).read_text(encoding="utf-8")
            self.assertNotIn("USE_ARITY_MISMATCH", source, relative)
            self.assertNotIn("symbol_ledger", source, relative)
            self.assertNotIn("applied_heads", source, relative)


if __name__ == "__main__":
    unittest.main()
