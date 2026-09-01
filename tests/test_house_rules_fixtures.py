"""HOUSE RULES — guards for H-PRE's fixture seal.

``docs/DESIGN-house-rules.md`` §6 step 1 makes this artifact the construction
prerequisite of the whole slice: the fixtures, their expected verdicts, B3's
mutant set, B12's prefix-adjacent mutants, and B9's class balance are all
sealed *before* a checker exists to be scored on them. B10 then freezes them.

A seal is only a seal if the numbers it publishes can be recomputed from its
own bytes by a program that did not write them. So these tests deliberately do
not read the artifact's summary fields and believe them — every floor, every
count, every class balance is **recounted from the fixture rows** and compared
against what the artifact claims. Where the two disagree the artifact is wrong,
which is the only way "sealed" means anything.

What is scored here:

* the committed JSON is the committed builder's output, byte for byte;
* the §6.1 floors — ≥8 admitted across ≥3 arities and ≥4 categories, ≥30 B3
  mutants, B12 mutants present — hold on a recount;
* all eight refusal codes are fired by a fixture or deleted with a recorded
  reason, and the two codes deleted at design time are not resurrected;
* the committed clause order actually decides every order-sensitive line;
* the session arithmetic is consistent: no session admits more than four, and
  the SYMBOL_BUDGET fixture really is a fifth declaration in a full session;
* B9's split rule is deterministic, partitions the declaration corpus, and its
  sealed class balance matches a recount;
* the checks can go red, exercised on perturbed copies.

Nothing here parses a declaration line. ``scripts/symbol_ledger.py`` is
registered as not existing yet, and this module asserts that.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import build_house_rules_fixtures as builder  # noqa: E402

BUILDER = REPO / "scripts" / "build_house_rules_fixtures.py"
FIXTURES = REPO / "experiments" / "house_rules_fixtures.json"
SCHEMA = REPO / "schema" / "equation-node.schema.json"
MATCH_SIGNATURES = REPO / "scripts" / "match_signatures.py"

ADMITTED = "ADMITTED_DECLARED_SYMBOL"
REFUSED = "REFUSED"

EIGHT_CODES = (
    "UNPARSED",
    "ARITY_CATEGORY_MISMATCH",
    "CATEGORY_NOT_IN_SCHEMA",
    "RESERVED_PREFIX",
    "COLLIDES_WITH_LIBRARY_SYMBOL",
    "REDEFINITION_ATTEMPT",
    "COLLIDES_WITH_SESSION_NAME",
    "SYMBOL_BUDGET",
)

DELETED_AT_DESIGN_TIME = ("UNBOUND_VARIABLE", "REQUIRES_CONSERVATIVITY_VERDICT")


def _load() -> dict:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def _declarations(document: dict) -> list[dict]:
    return [f for f in document["fixtures"] if f["kind"] == "declaration"]


def _admitted(document: dict) -> list[dict]:
    return [f for f in _declarations(document) if f["expected_verdict"] == ADMITTED]


class TheArtifactIsItsGeneratorsOutput(unittest.TestCase):
    """(a) The committed file is what the builder emits, byte for byte."""

    def test_regeneration_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "regenerated.json"
            run = subprocess.run(
                [sys.executable, str(BUILDER), "--out", str(out)],
                cwd=REPO,
                capture_output=True,
                text=True,
                env=dict(os.environ, PYTHONIOENCODING="utf-8"),
            )
            self.assertEqual(run.returncode, 0, (run.stderr or run.stdout)[-800:])
            self.assertEqual(FIXTURES.read_bytes(), out.read_bytes())

    def test_regeneration_is_stable_across_runs(self) -> None:
        """Determinism, not just agreement with one committed blob."""

        first = builder.render(builder.build_fixtures(REPO))
        second = builder.render(builder.build_fixtures(REPO))
        self.assertEqual(first, second)
        self.assertEqual(first, FIXTURES.read_bytes())

    def test_the_builders_own_check_mode_passes(self) -> None:
        run = subprocess.run(
            [sys.executable, str(BUILDER), "--check"],
            cwd=REPO,
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        )
        self.assertEqual(run.returncode, 0, (run.stderr or run.stdout)[-800:])

    def test_the_artifact_names_its_generator_and_its_source_commit(self) -> None:
        document = _load()
        self.assertEqual(document["generator"], "scripts/build_house_rules_fixtures.py")
        self.assertEqual(BUILDER, REPO / document["generator"])
        self.assertTrue(document["generator_placement_note"].strip())
        self.assertEqual(document["schema"], "corollary.house-rules-fixtures/1")
        self.assertEqual(document["stage"], "H-PRE")
        self.assertRegex(document["source_commit"], r"^[0-9a-f]{40}$")

    def test_no_wall_clock_or_randomness_reaches_the_bytes(self) -> None:
        source = BUILDER.read_text(encoding="utf-8")
        for forbidden in ("import random", "datetime.now", "time.time", "os.environ", "uuid"):
            self.assertNotIn(forbidden, source, f"{forbidden} would break determinism")
        self.assertIsNone(_load()["generation"]["seed"])


class TheCheckerDoesNotExistYet(unittest.TestCase):
    """H-PRE seals before H-P0 builds. A seal written after its checker is fitted."""

    def test_symbol_ledger_is_registered_as_not_existing(self) -> None:
        """The seal RECORDS that it predates its checker.

        Deliberately not `assertFalse(path.exists())`: H-P0 lands
        `scripts/symbol_ledger.py` as its very next step, and a test that goes
        permanently red then — repairable only by editing the module B10 froze —
        would be a self-destruct, not a guard. What H-PRE can honestly assert is
        that the artifact names the module and the commit it was sealed at; the
        ORDER is enforced by B10's freeze and by git, not by a filesystem probe
        that expires.
        """

        document = _load()
        self.assertEqual(
            document["checker_module_registered_as_not_existing"], "scripts/symbol_ledger.py"
        )
        self.assertRegex(document["source_commit"], r"^[0-9a-f]{40}$")

    def test_the_builder_contains_no_parser(self) -> None:
        """The seal fixes bytes and expectations; parsing them is H-P0's job."""

        source = BUILDER.read_text(encoding="utf-8")
        # The builder may NAME the parser in its provenance prose — that is the
        # point of the citations. What it may not do is import one or run one.
        for forbidden in (
            "import re",
            "import match_signatures",
            "from match_signatures",
            "def parse",
            "tokenize(",
        ):
            self.assertNotIn(forbidden, source, forbidden)

    def test_the_grounds_derivation_never_reads_the_surface_line(self) -> None:
        """`derive_grounds` is a consistency check, not a smuggled parser."""

        source = BUILDER.read_text(encoding="utf-8")
        function = source.split("def derive_grounds(")[1].split("\ndef ")[0]
        # Drop the docstring: it NAMES `turn["line"]` in order to say the code
        # never reads it, and scanning prose for a forbidden token is how the
        # earlier no-parser assertion got this wrong twice.
        body = function.split('"""')[2] if function.count('"""') >= 2 else function
        self.assertNotIn('["line"]', body)
        self.assertNotIn("['line']", body)


class TheDeclaredFloorsHoldOnARecount(unittest.TestCase):
    """(b) DESIGN §6.1 — declared construction bounds, recounted from the rows."""

    def setUp(self) -> None:
        self.document = _load()
        self.declarations = _declarations(self.document)
        self.admitted = _admitted(self.document)

    def test_at_least_eight_admitted(self) -> None:
        self.assertGreaterEqual(len(self.admitted), 8)
        self.assertEqual(len(self.admitted), self.document["coverage"]["admitted_count"])
        self.assertEqual(len(self.admitted), self.document["counts"]["admitted"])

    def test_at_least_three_distinct_arities(self) -> None:
        arities = sorted({f["read_arity"] for f in self.admitted})
        self.assertGreaterEqual(len(arities), 3)
        self.assertEqual(arities, self.document["coverage"]["arities_exercised"])
        self.assertTrue(all(isinstance(a, int) and a >= 1 for a in arities))

    def test_at_least_four_distinct_categories(self) -> None:
        used = sorted({c for f in self.admitted for c in f["read_argument_categories"]})
        self.assertGreaterEqual(len(used), 4)
        self.assertEqual(used, self.document["coverage"]["categories_exercised"])

    def test_every_admitted_category_is_a_member_of_the_committed_schema_enum(self) -> None:
        enum = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]["symbolToken"][
            "properties"
        ]["syntactic_category"]["enum"]
        self.assertEqual(len(enum), 9)
        self.assertEqual(list(enum), self.document["schema_source"]["categories"])
        for fixture in self.admitted:
            for category in fixture["read_argument_categories"]:
                self.assertIn(category, enum, fixture["fixture_id"])

    def test_the_sealed_schema_digest_matches_the_committed_schema(self) -> None:
        self.assertEqual(
            self.document["schema_source"]["sha256_lf"], builder.sha256_lf(SCHEMA)
        )

    def test_arity_and_category_count_agree_on_every_admitted_line(self) -> None:
        """The property ARITY_CATEGORY_MISMATCH exists to refuse, held on admissions."""

        for fixture in self.admitted:
            self.assertEqual(
                fixture["read_arity"],
                len(fixture["read_argument_categories"]),
                fixture["fixture_id"],
            )

    def test_every_declaration_line_uses_the_registered_surface_form(self) -> None:
        for fixture in self.declarations:
            self.assertTrue(
                fixture["line"] == "declare" or fixture["line"].startswith("declare "),
                fixture["fixture_id"],
            )
        for fixture in self.document["fixtures"]:
            if fixture["kind"] == "use":
                self.assertTrue(fixture["line"].startswith("suppose "), fixture["fixture_id"])


class EveryRefusalCodeFiresOrIsDeletedWithAReason(unittest.TestCase):
    """(b) §6.1's coverage requirement and the U-PRE deletion mechanic."""

    def setUp(self) -> None:
        self.document = _load()
        self.fired = Counter(
            f["expected_refusal_code"]
            for f in _declarations(self.document)
            if f["expected_refusal_code"] != "NONE"
        )
        self.fired.update(
            m["expected_refusal_code"]
            for m in self.document["b12_round_trip"]["mutants"]
            if m["expected_refusal_code"] != "NONE"
        )

    def test_all_eight_codes_are_covered_or_deleted(self) -> None:
        deleted_here = {row["code"] for row in self.document["deleted_codes"]["at_h_pre"]}
        for code in EIGHT_CODES:
            with self.subTest(code=code):
                if code in deleted_here:
                    row = next(
                        r
                        for r in self.document["deleted_codes"]["at_h_pre"]
                        if r["code"] == code
                    )
                    self.assertTrue(row["reason"].strip(), "a deletion owes a reason")
                else:
                    self.assertGreaterEqual(self.fired[code], 1, f"{code} fires nowhere")

    def test_the_clause_order_is_the_designs_committed_order(self) -> None:
        order = [row["refusal_code"] for row in self.document["clause_order"]]
        self.assertEqual(order, list(EIGHT_CODES))
        ranks = [row["rank"] for row in self.document["clause_order"]]
        self.assertEqual(ranks, list(range(1, 9)))

    def test_the_two_design_time_deletions_are_recorded_and_not_resurrected(self) -> None:
        recorded = {row["code"] for row in self.document["deleted_codes"]["at_design_time"]}
        self.assertEqual(recorded, set(DELETED_AT_DESIGN_TIME))
        for row in self.document["deleted_codes"]["at_design_time"]:
            self.assertTrue(row["reason"].strip())
            self.assertTrue(row["ground_fixture"].strip())
        for code in DELETED_AT_DESIGN_TIME:
            self.assertNotIn(code, self.fired)
            self.assertNotIn(code, [r["refusal_code"] for r in self.document["clause_order"]])

    def test_exactly_one_deciding_clause_per_declaration(self) -> None:
        clause_by_code = {
            row["refusal_code"]: row["clause"] for row in self.document["clause_order"]
        }
        for fixture in _declarations(self.document):
            code = fixture["expected_refusal_code"]
            with self.subTest(fixture=fixture["fixture_id"]):
                if code == "NONE":
                    self.assertEqual(fixture["expected_verdict"], ADMITTED)
                    self.assertEqual(fixture["expected_deciding_clause"], "c9_admit")
                else:
                    self.assertEqual(fixture["expected_verdict"], REFUSED)
                    self.assertEqual(fixture["expected_deciding_clause"], clause_by_code[code])

    def test_the_committed_order_decides_every_order_sensitive_line(self) -> None:
        rank = {row["refusal_code"]: row["rank"] for row in self.document["clause_order"]}
        sensitive = [f for f in _declarations(self.document) if f["order_sensitive"]]
        self.assertGreaterEqual(len(sensitive), 2, "order-sensitivity must be exercised")
        for fixture in sensitive:
            code = fixture["expected_refusal_code"]
            for other in fixture["also_grounds_for"]:
                self.assertLess(
                    rank[code], rank[other], f"{fixture['fixture_id']}: {other} runs earlier"
                )

    def test_the_reserved_prefix_before_library_collision_case_is_present(self) -> None:
        """The task the clause order exists for, on a verified real census member."""

        sensitive = [
            f
            for f in _declarations(self.document)
            if f["expected_refusal_code"] == "RESERVED_PREFIX"
            and "COLLIDES_WITH_LIBRARY_SYMBOL" in f["also_grounds_for"]
        ]
        self.assertTrue(sensitive)
        targets = {row["name"] for row in self.document["library_collision_targets"]}
        for fixture in sensitive:
            self.assertIn(fixture["read_symbol_name"], targets)

    def test_the_sum_total_fixture_refuses_reserved_prefix(self) -> None:
        """B2 mandates this by name."""

        rows = [
            f
            for f in _declarations(self.document)
            if f["read_symbol_name"] == "sum_total"
            and f["expected_refusal_code"] == "RESERVED_PREFIX"
        ]
        self.assertTrue(rows, "DESIGN B2: the sum_total fixture must refuse RESERVED_PREFIX")

    def test_every_library_collision_target_carries_its_provenance(self) -> None:
        targets = self.document["library_collision_targets"]
        self.assertTrue(targets)
        for row in targets:
            self.assertTrue(row["provenance"].strip())
            self.assertTrue(row["reached_by"].strip())
            self.assertTrue(row["why_the_census_must_contain_it"].strip())

    def test_all_three_session_name_sub_cases_are_exercised(self) -> None:
        """DESIGN §4's union has three members; two can decide, and the third is named."""

        subcases = {
            f["session_name_subcase"]
            for f in _declarations(self.document)
            if f["session_name_subcase"]
        }
        self.assertEqual(
            subcases,
            {
                "already_admitted_symbol",
                "supposition_binding_subject",
                "live_non_binding_supposition_head",
            },
        )
        # The first sub-case is reached by an EARLIER clause, which is the whole
        # point of sealing the union membership separately from the verdict.
        by_subcase = {
            f["session_name_subcase"]: f
            for f in _declarations(self.document)
            if f["session_name_subcase"]
        }
        self.assertEqual(
            by_subcase["already_admitted_symbol"]["expected_refusal_code"],
            "REDEFINITION_ATTEMPT",
        )
        self.assertIn(
            "COLLIDES_WITH_SESSION_NAME",
            by_subcase["already_admitted_symbol"]["also_grounds_for"],
        )
        for key in ("supposition_binding_subject", "live_non_binding_supposition_head"):
            self.assertEqual(
                by_subcase[key]["expected_refusal_code"], "COLLIDES_WITH_SESSION_NAME"
            )

    def test_each_session_name_subcase_has_the_turn_that_creates_it(self) -> None:
        """The union member must be created by an earlier turn, not asserted."""

        fixtures = self.document["fixtures"]
        binding = [f for f in fixtures if f["kind"] == "use" and f.get("binds_subject")]
        self.assertTrue(binding)
        opaque_heads = {
            f["read_applied_head"]
            for f in fixtures
            if f["kind"] == "use" and f["expected_disposition"] == "OPAQUE_ATOM"
        }
        by_subcase = {
            f["session_name_subcase"]: f
            for f in _declarations(self.document)
            if f["session_name_subcase"]
        }
        subject_fixture = by_subcase["supposition_binding_subject"]
        creator = next(
            f
            for f in binding
            if f["binds_subject"] == subject_fixture["read_symbol_name"]
            and f["session_id"] == subject_fixture["session_id"]
            and f["turn_index"] < subject_fixture["turn_index"]
        )
        self.assertEqual(creator["expected_disposition"], "BINDING_SUPPOSITION_UNCHANGED")
        head_fixture = by_subcase["live_non_binding_supposition_head"]
        self.assertIn(head_fixture["read_symbol_name"], opaque_heads)


class TheGroundsAreDerivedNotAsserted(unittest.TestCase):
    """`also_grounds_for` is computed by the generator and re-derived here.

    The review's sharpest finding: a fixture that omits an EARLIER ground is
    structurally invisible to a check that only verifies the expected code is
    earliest among the DECLARED ones. So the builder now derives all six
    decidable clauses from the sealed reading, and this test re-derives them a
    second time, independently, walking the session state itself.
    """

    def setUp(self) -> None:
        self.document = _load()

    def test_every_parsed_declaration_carries_generator_derived_grounds(self) -> None:
        for fixture in _declarations(self.document):
            if fixture["read_symbol_name"] is not None:
                self.assertTrue(
                    fixture["grounds_derived_by_generator"], fixture["fixture_id"]
                )

    def test_unparsed_lines_ground_no_later_clause(self) -> None:
        for fixture in _declarations(self.document):
            if fixture["expected_refusal_code"] == "UNPARSED":
                self.assertFalse(fixture["grounds_derived_by_generator"])
                self.assertEqual(fixture["also_grounds_for"], [])

    def test_the_grounds_recompute_from_a_walk_of_the_session(self) -> None:
        enum = set(self.document["schema_source"]["categories"])
        prefixes = tuple(self.document["b12_round_trip"]["reserved_prefixes"])
        library = {row["name"] for row in self.document["library_collision_targets"]}
        rank = {row["refusal_code"]: row["rank"] for row in self.document["clause_order"]}

        state: dict[str, dict] = {}
        for fixture in self.document["fixtures"]:
            session = state.setdefault(
                fixture["session_id"], {"admitted": set(), "names": set(), "running": 0}
            )
            if fixture["kind"] == "use":
                if fixture.get("binds_subject"):
                    session["names"].add(fixture["binds_subject"])
                if fixture["expected_disposition"] == "OPAQUE_ATOM" and fixture[
                    "read_applied_head"
                ]:
                    session["names"].add(fixture["read_applied_head"])
                continue

            name = fixture["read_symbol_name"]
            if name is None:
                continue
            cats = fixture["read_argument_categories"]
            grounds = set()
            if len(cats) != fixture["read_arity"]:
                grounds.add("ARITY_CATEGORY_MISMATCH")
            if any(c not in enum for c in cats):
                grounds.add("CATEGORY_NOT_IN_SCHEMA")
            if name.startswith(prefixes):
                grounds.add("RESERVED_PREFIX")
            if name in library:
                grounds.add("COLLIDES_WITH_LIBRARY_SYMBOL")
            if name in session["admitted"]:
                grounds.add("REDEFINITION_ATTEMPT")
            if name in session["names"]:
                grounds.add("COLLIDES_WITH_SESSION_NAME")
            if session["running"] >= 4:
                grounds.add("SYMBOL_BUDGET")

            code = fixture["expected_refusal_code"]
            expected = min(grounds, key=lambda c: rank[c]) if grounds else "NONE"
            with self.subTest(fixture=fixture["fixture_id"]):
                self.assertEqual(expected, code)
                self.assertEqual(sorted(grounds - {code}), fixture["also_grounds_for"])

            if code == "NONE":
                session["admitted"].add(name)
                session["names"].add(name)
                session["running"] += 1


class TheNormalizationOrderIsSealed(unittest.TestCase):
    """NFC, then casefold, then match — an order, not three facts."""

    def setUp(self) -> None:
        self.document = _load()

    def test_the_generator_runs_the_rule_rather_than_describing_it(self) -> None:
        self.assertEqual(builder.normalize_name("SUM_TOTAL"), "sum_total")
        self.assertEqual(builder.normalize_name("ﬁrst_of"), "first_of")
        self.assertEqual(builder.normalize_name("straße_of"), "strasse_of")
        self.assertEqual(builder.normalize_name("café_of"), "café_of")

    def test_every_raw_name_normalizes_to_its_sealed_read_name(self) -> None:
        seen = 0
        for fixture in _declarations(self.document):
            raw = fixture.get("raw_symbol_name")
            if raw and fixture["read_symbol_name"]:
                seen += 1
                self.assertEqual(
                    builder.normalize_name(raw), fixture["read_symbol_name"], raw
                )
        self.assertGreaterEqual(seen, 2, "normalization must be exercised by fixtures")

    def test_a_casefold_expansion_carries_a_surface_into_the_production(self) -> None:
        """The case `.lower()` fails and match-before-normalize fails."""

        expanding = [
            f
            for f in _admitted(self.document)
            if f.get("raw_symbol_name")
            and f["raw_symbol_name"].lower() != f["read_symbol_name"]
        ]
        self.assertTrue(expanding, "no fixture separates casefold from lower()")
        for fixture in expanding:
            raw = fixture["raw_symbol_name"]
            self.assertNotEqual(raw.lower(), fixture["read_symbol_name"])
            self.assertEqual(builder.normalize_name(raw), fixture["read_symbol_name"])

    def test_normalization_is_not_a_repair_mechanism(self) -> None:
        """An NFC fixture that still refuses, so the rule cannot be read as coercion."""

        refused = [
            f
            for f in _declarations(self.document)
            if f.get("raw_symbol_name") and f["expected_refusal_code"] == "UNPARSED"
        ]
        self.assertTrue(refused)
        for fixture in refused:
            normalized = builder.normalize_name(fixture["raw_symbol_name"])
            self.assertFalse(
                all(c.isascii() for c in normalized),
                "the refusing normalization fixture should stay outside the production",
            )


class TheSessionArithmeticIsConsistent(unittest.TestCase):
    """(f) The budget is 4, the floor is 8, so the corpus spans sessions."""

    def setUp(self) -> None:
        self.document = _load()

    def test_no_session_admits_more_than_four(self) -> None:
        counted = Counter(
            f["session_id"] for f in _admitted(self.document)
        )
        for session in self.document["sessions"]:
            with self.subTest(session=session["session_id"]):
                self.assertLessEqual(session["admitted_count"], 4)
                self.assertEqual(
                    session["admitted_count"], counted.get(session["session_id"], 0)
                )

    def test_the_corpus_spans_at_least_three_sessions(self) -> None:
        sessions = {f["session_id"] for f in _declarations(self.document)}
        self.assertGreaterEqual(len(sessions), 3)

    def test_the_budget_fixture_is_a_fifth_declaration_in_a_full_session(self) -> None:
        rows = [
            f
            for f in _declarations(self.document)
            if f["expected_refusal_code"] == "SYMBOL_BUDGET"
        ]
        self.assertTrue(rows)
        for fixture in rows:
            self.assertEqual(fixture["admitted_in_session_before_this_turn"], 4)

    def test_the_running_admitted_count_recomputes_from_turn_order(self) -> None:
        running: Counter = Counter()
        for fixture in _declarations(self.document):
            self.assertEqual(
                fixture["admitted_in_session_before_this_turn"],
                running[fixture["session_id"]],
                fixture["fixture_id"],
            )
            if fixture["expected_verdict"] == ADMITTED:
                running[fixture["session_id"]] += 1

    def test_turn_indices_are_dense_and_one_based_within_each_session(self) -> None:
        by_session: dict[str, list[int]] = {}
        for fixture in self.document["fixtures"]:
            by_session.setdefault(fixture["session_id"], []).append(fixture["turn_index"])
        for session_id, turns in by_session.items():
            self.assertEqual(turns, list(range(1, len(turns) + 1)), session_id)

    def test_a_fresh_session_sees_an_admitted_symbol_as_an_opaque_atom(self) -> None:
        """B5's third leg, as a fixture: same bytes, no declaration, opaque."""

        admitted_names = {f["read_symbol_name"] for f in _admitted(self.document)}
        fresh = [
            f
            for f in self.document["fixtures"]
            if f["kind"] == "use"
            and f["expected_disposition"] == "OPAQUE_ATOM"
            and f["read_applied_head"] in admitted_names
        ]
        self.assertTrue(fresh, "no fixture checks that a declaration dies with its session")
        for fixture in fresh:
            session = next(
                s for s in self.document["sessions"] if s["session_id"] == fixture["session_id"]
            )
            self.assertEqual(session["admitted_count"], 0)


class TheUseSideFixturesFenceTheRegression(unittest.TestCase):
    """(B6) Correct arity passes, wrong arity refuses by name, undeclared is opaque."""

    def setUp(self) -> None:
        self.document = _load()
        self.uses = [f for f in self.document["fixtures"] if f["kind"] == "use"]

    def test_all_three_dispositions_are_exercised(self) -> None:
        dispositions = Counter(f["expected_disposition"] for f in self.uses)
        for disposition in ("CHECKED_SUPPOSITION", "USE_ARITY_MISMATCH", "OPAQUE_ATOM"):
            self.assertGreaterEqual(dispositions[disposition], 1, disposition)

    def test_use_arity_mismatch_is_not_an_admissibility_code(self) -> None:
        """DESIGN §3: it is a supposition-ledger refusal name, not a verdict code."""

        self.assertNotIn(
            "USE_ARITY_MISMATCH", [row["refusal_code"] for row in self.document["clause_order"]]
        )
        self.assertIn("USE_ARITY_MISMATCH", self.document["use_side_note"])

    def test_every_checked_use_cites_a_declaration_and_matches_its_arity(self) -> None:
        """No carve-out: a binding supposition is no longer labelled CHECKED.

        The earlier form skipped rows whose cited declaration was None, which
        silently exempted `suppose headcount = 12` — a turn this slice does not
        touch — from a check that claimed to cover every checked use. It now
        carries BINDING_SUPPOSITION_UNCHANGED and the exemption is gone.
        """

        arity_by_name = {
            f["read_symbol_name"]: f["read_arity"] for f in _admitted(self.document)
        }
        checked = [f for f in self.uses if f["expected_disposition"] == "CHECKED_SUPPOSITION"]
        self.assertTrue(checked)
        for fixture in checked:
            name = fixture["cites_declaration_symbol"]
            self.assertIsNotNone(name, fixture["fixture_id"])
            self.assertIn(name, arity_by_name, fixture["fixture_id"])
            self.assertEqual(
                fixture["read_argument_count"], arity_by_name[name], fixture["fixture_id"]
            )

    def test_a_binding_supposition_is_not_given_the_slices_verdict(self) -> None:
        binding = [
            f for f in self.uses if f["expected_disposition"] == "BINDING_SUPPOSITION_UNCHANGED"
        ]
        self.assertTrue(binding, "the binding-supposition turn must carry its own disposition")
        for fixture in binding:
            self.assertIsNone(fixture["read_applied_head"])
            self.assertIsNone(fixture["cites_declaration_symbol"])
            self.assertIsNone(fixture["round_trip_for"])
            self.assertTrue(fixture["binds_subject"])
        # and it is outside B6's counts
        self.assertEqual(
            self.document["counts"]["use_checked"],
            sum(1 for f in self.uses if f["expected_disposition"] == "CHECKED_SUPPOSITION"),
        )

    def test_every_mismatched_use_really_mismatches_its_declaration(self) -> None:
        arity_by_name = {
            f["read_symbol_name"]: f["read_arity"] for f in _admitted(self.document)
        }
        rows = [f for f in self.uses if f["expected_disposition"] == "USE_ARITY_MISMATCH"]
        self.assertTrue(rows)
        for fixture in rows:
            name = fixture["cites_declaration_symbol"]
            self.assertIn(name, arity_by_name, fixture["fixture_id"])
            self.assertNotEqual(
                fixture["read_argument_count"], arity_by_name[name], fixture["fixture_id"]
            )
            self.assertEqual(fixture["expected_refusal_name"], "USE_ARITY_MISMATCH")

    def test_undeclared_applied_atoms_cite_no_declaration(self) -> None:
        for fixture in self.uses:
            if fixture["expected_disposition"] == "OPAQUE_ATOM":
                self.assertIsNone(fixture["cites_declaration_symbol"], fixture["fixture_id"])


class TheContainmentMutantsAreSealed(unittest.TestCase):
    """(c) B3 — ≥30 seeded mutants, each naming its vector and target."""

    def setUp(self) -> None:
        self.b3 = _load()["b3_containment"]

    def test_at_least_thirty_mutants(self) -> None:
        self.assertGreaterEqual(len(self.b3["mutants"]), 30)
        self.assertEqual(len(self.b3["mutants"]), self.b3["mutant_count"])

    def test_all_four_vectors_are_covered(self) -> None:
        vectors = Counter(m["vector"] for m in self.b3["mutants"])
        self.assertEqual(set(vectors), set(self.b3["vectors"]))
        self.assertEqual(
            set(self.b3["vectors"]),
            {"answer_evidence", "session_document", "journal", "library_path"},
        )
        for vector in self.b3["vectors"]:
            self.assertGreaterEqual(vectors[vector], 1, vector)

    def test_every_mutant_names_a_target_an_attempt_and_a_stopper(self) -> None:
        ids = set()
        for mutant in self.b3["mutants"]:
            self.assertTrue(mutant["target"].strip())
            self.assertTrue(mutant["attempt"].strip())
            self.assertTrue(mutant["stopper_mechanism"].strip())
            self.assertEqual(mutant["expected_outcome"], "STOPPED")
            self.assertNotIn(mutant["mutant_id"], ids)
            ids.add(mutant["mutant_id"])

    def test_every_stopper_is_machinery_or_the_checker(self) -> None:
        """B3: "stopped by the shipped machinery or the checker".

        A row whose stopper is a design argument ("the slice sheds frames",
        "this slice mints no questions") is a row H-P1 could only score by
        agreeing with the author, and six such rows would have taken the set
        below the declared floor of 30. The vocabulary is closed.
        """

        for mutant in self.b3["mutants"]:
            self.assertIn(
                mutant["stopper_kind"],
                ("shipped_machinery", "checker"),
                mutant["mutant_id"],
            )

    def test_every_stopper_mechanism_names_something_checkable(self) -> None:
        """Each mechanism must point at a module, a digest, a sweep or a gate."""

        anchors = (
            ".py", "digest", "sweep", "B4", "B5", "B2", "encode", "_TYPES",
            "resolve_pin", "census", "regeneration", "checker", "barrier",
            "node id", "graph", "ledger", "provenance",
        )
        for mutant in self.b3["mutants"]:
            with self.subTest(mutant=mutant["mutant_id"]):
                self.assertTrue(
                    any(a in mutant["stopper_mechanism"] for a in anchors),
                    mutant["stopper_mechanism"],
                )


class TheRoundTripMutantsSitAtTheReservedPrefixes(unittest.TestCase):
    """(d) B12 — seeded at reserved-prefix-adjacent names."""

    def setUp(self) -> None:
        self.b12 = _load()["b12_round_trip"]
        self.prefixes = tuple(self.b12["reserved_prefixes"])

    def test_the_prefixes_are_the_parsers_own(self) -> None:
        """Read out of scripts/match_signatures.py, not restated from memory.

        A hardcoded literal here would agree with the artifact forever and
        detect nothing if the shipped parser's prefixes moved — which is the
        one event this gate exists to survive. The constant is read TEXTUALLY
        so the no-import rule stands.
        """

        source = MATCH_SIGNATURES.read_text(encoding="utf-8")
        line = next(
            l for l in source.splitlines() if l.startswith("BIG_OP_PREFIXES")
        )
        shipped = tuple(
            part.strip().strip('"').strip("'")
            for part in line.split("(", 1)[1].rsplit(")", 1)[0].split(",")
            if part.strip()
        )
        self.assertEqual(self.prefixes, shipped)

    def test_mutants_are_present_and_span_the_adjacency_kinds(self) -> None:
        self.assertGreaterEqual(len(self.b12["mutants"]), 10)
        adjacencies = {m["adjacency"] for m in self.b12["mutants"]}
        for required in (
            "starts_with_prefix",
            "one_character_from_prefix",
            "contains_prefix_not_leading",
            "prefix_minus_underscore_exactly",
            "prefix_without_underscore",
        ):
            self.assertIn(required, adjacencies, required)

    def test_every_reserved_prefix_is_exercised_by_a_leading_mutant(self) -> None:
        leading = [
            m["read_symbol_name"]
            for m in self.b12["mutants"]
            if m["expected_refusal_code"] == "RESERVED_PREFIX"
        ]
        for prefix in self.prefixes:
            self.assertTrue(
                any(name.startswith(prefix) for name in leading), f"{prefix} unexercised"
            )

    def test_the_refusal_expectation_tracks_the_prefix_and_nothing_else(self) -> None:
        for mutant in self.b12["mutants"]:
            name = mutant["read_symbol_name"]
            leading = name.startswith(self.prefixes)
            with self.subTest(mutant=mutant["mutant_id"]):
                if mutant["expected_refusal_code"] == "RESERVED_PREFIX":
                    self.assertTrue(leading, f"{name} starts with no reserved prefix")
                if mutant["expected_verdict"] == ADMITTED:
                    self.assertFalse(leading, f"{name} starts with a reserved prefix")

    def test_admitted_mutants_owe_a_byte_identical_round_trip(self) -> None:
        """Scored on the sealed USE LINE, not on a sentence the generator wrote.

        The previous form asserted that a name appeared in a string the builder
        had interpolated that same name into — it could not fail. B12 is a round
        trip, so the mutant owes a `suppose` line and the key it must resolve to.
        """

        admitted = [m for m in self.b12["mutants"] if m["expected_verdict"] == ADMITTED]
        self.assertTrue(admitted, "a round-trip gate with no admitted name tests nothing")
        for mutant in admitted:
            with self.subTest(mutant=mutant["mutant_id"]):
                self.assertTrue(mutant["use_line"].startswith("suppose "))
                self.assertEqual(
                    mutant["expected_resolved_key"], mutant["read_symbol_name"]
                )
                # The resolved key is the NORMALIZED name, which need not be a
                # substring of the line the person typed.
                self.assertEqual(
                    mutant["expected_resolved_key"],
                    builder.normalize_name(mutant["raw_symbol_name"]),
                )

    def test_refused_mutants_owe_no_round_trip(self) -> None:
        for mutant in self.b12["mutants"]:
            if mutant["expected_verdict"] != ADMITTED:
                self.assertIsNone(mutant["use_line"], mutant["mutant_id"])
                self.assertIsNone(mutant["expected_resolved_key"], mutant["mutant_id"])

    def test_every_admitted_fixture_symbol_has_a_declare_then_use_pair(self) -> None:
        """B12 says EVERY admitted fixture symbol, so the seal leaves no choice."""

        document = _load()
        admitted = {f["read_symbol_name"] for f in _admitted(document)}
        round_trips = {
            f["round_trip_for"] for f in document["fixtures"] if f.get("round_trip_for")
        }
        self.assertEqual(admitted - round_trips, set())
        self.assertEqual(round_trips - admitted, set())
        for fixture in document["fixtures"]:
            if fixture.get("round_trip_for"):
                self.assertEqual(
                    fixture["read_applied_head"], fixture["round_trip_for"]
                )
                self.assertEqual(fixture["expected_disposition"], "CHECKED_SUPPOSITION")

    def test_names_are_normalized_before_comparison(self) -> None:
        """Casefold runs before the prefix check, so an uppercased hazard still refuses."""

        uppercased = [m for m in self.b12["mutants"] if "uppercased" in m["adjacency"]]
        self.assertTrue(uppercased)
        for mutant in uppercased:
            self.assertEqual(mutant["read_symbol_name"], mutant["read_symbol_name"].casefold())
            self.assertEqual(mutant["expected_refusal_code"], "RESERVED_PREFIX")

    def test_the_replay_policy_keeps_mutants_out_of_the_session_budgets(self) -> None:
        self.assertIn("fresh single-declaration session", self.b12["replay_policy"])


class TheClassBalanceIsSealedBeforeAnyAdmitterExists(unittest.TestCase):
    """(e) B9 — the majority-class anchor must not be tunable after the fact."""

    def setUp(self) -> None:
        self.document = _load()
        self.b9 = self.document["b9_class_balance"]
        self.declarations = _declarations(self.document)

    def test_the_split_is_a_partition_of_the_declaration_corpus(self) -> None:
        halves = self.b9["fit_half_fixture_ids"] + self.b9["scored_half_fixture_ids"]
        self.assertEqual(
            sorted(halves), sorted(f["fixture_id"] for f in self.declarations)
        )
        self.assertEqual(len(halves), len(set(halves)), "a fixture cannot be in both halves")

    def test_the_split_rule_is_deterministic_and_recomputable_from_these_bytes(self) -> None:
        """The rule, applied by this test rather than trusted from the artifact."""

        fit = [f["fixture_id"] for i, f in enumerate(self.declarations) if i % 2 == 0]
        scored = [f["fixture_id"] for i, f in enumerate(self.declarations) if i % 2 == 1]
        self.assertEqual(fit, self.b9["fit_half_fixture_ids"])
        self.assertEqual(scored, self.b9["scored_half_fixture_ids"])
        self.assertIn("Even index", self.b9["split_rule"])

    def test_every_sealed_balance_matches_a_recount(self) -> None:
        verdict = {f["fixture_id"]: f["expected_verdict"] for f in self.declarations}
        cases = (
            ("corpus_balance", [f["fixture_id"] for f in self.declarations]),
            ("fit_half_balance", self.b9["fit_half_fixture_ids"]),
            ("scored_half_balance", self.b9["scored_half_fixture_ids"]),
        )
        for key, ids in cases:
            with self.subTest(half=key):
                admitted = sum(1 for i in ids if verdict[i] == ADMITTED)
                refused = len(ids) - admitted
                sealed = self.b9[key]
                self.assertEqual(sealed["n"], len(ids))
                self.assertEqual(sealed["admitted"], admitted)
                self.assertEqual(sealed["refused"], refused)
                self.assertEqual(
                    sealed["majority_class"], ADMITTED if admitted > refused else REFUSED
                )
                self.assertAlmostEqual(
                    sealed["majority_class_rate"], max(admitted, refused) / len(ids), places=5
                )

    def test_the_anchor_and_threshold_follow_the_scored_half(self) -> None:
        scored = self.b9["scored_half_balance"]
        self.assertEqual(self.b9["majority_class_anchor"], scored["majority_class_rate"])
        self.assertEqual(self.b9["declared_margin_points"], 10)
        self.assertAlmostEqual(
            self.b9["void_threshold"], scored["majority_class_rate"] + 0.10, places=5
        )

    def test_the_voiding_sentence_is_the_frozen_one(self) -> None:
        for phrase in (
            "exceeds the scored half's majority-class rate by more than ten points",
            "the capability is void",
            "honest negative",
        ):
            self.assertIn(phrase, self.b9["voiding_sentence"])

    def test_the_blind_controls_inputs_are_surface_only(self) -> None:
        self.assertEqual(
            self.b9["admitter_inputs_forbidden"], ["the census", "the schema enum", "the ledger"]
        )
        self.assertTrue(self.b9["admitter_inputs_allowed"])


class TheFloorsAreNamedAsBoundsNotMeasurements(unittest.TestCase):
    """The standing honesty rule the roadmap requires the notes to carry."""

    def test_the_construction_note_says_so(self) -> None:
        note = _load()["construction_note"]
        self.assertIn("DECLARED CONSTRUCTION BOUNDS, NOT MEASUREMENTS", note)
        self.assertIn("license no population claim", note)

    def test_the_honesty_note_carries_the_ledger_groundedness_sentence(self) -> None:
        note = _load()["honesty_note"]
        self.assertIn("ledger-groundedness, never correspondence", note)


class TheConstructionChecksCanGoRed(unittest.TestCase):
    """A check that survives a corrupted seal is freezing nothing.

    Note which mechanism each case names. Most of these corruptions are now
    caught by `derive_grounds` — the generator recomputing the clause the
    committed order would reach and finding it disagrees with the author —
    rather than by a later standalone check. That is the point of the
    derivation, and it is why two checks that used to catch these were deleted
    as unreachable rather than kept as decoration.
    """

    def _refuses(self, mutate, pattern: str) -> None:
        """Refuses, AND for the stated reason.

        A bare assertRaises passes whenever anything at all objects, so a check
        could be deleted and its own negative test would stay green on a
        different check's complaint. Each case now matches the message.
        """

        original = builder.authored_sessions
        try:
            builder.authored_sessions = mutate(original)
            with self.assertRaisesRegex(builder.ConstructionRefusal, pattern):
                builder.build_fixtures(REPO)
        finally:
            builder.authored_sessions = original

    def test_dropping_the_admitted_floor_refuses(self) -> None:
        def mutate(original):
            def sessions():
                keep = original()[:1]
                return keep

            return sessions

        self._refuses(mutate, r"admitted fixtures; the floor is")

    def test_a_fifth_admission_in_one_session_refuses(self) -> None:
        def mutate(original):
            def sessions():
                out = list(original())
                first = dict(out[0])
                extra = builder._admit(
                    "declare one_too_many/1 (variable)", "one_too_many", 1, ("variable",), "x"
                )
                first["turns"] = tuple(first["turns"]) + (extra,)
                out[0] = first
                return tuple(out)

            return sessions

        self._refuses(
            mutate, r"decides SYMBOL_BUDGET from the derived grounds"
        )

    def test_an_expectation_that_ignores_the_clause_order_refuses(self) -> None:
        def mutate(original):
            def sessions():
                out = list(original())
                third = dict(out[2])
                bad = builder._decl(
                    "declare sum_i/1 (index)",
                    name="sum_i",
                    arity=1,
                    categories=("index",),
                    code="COLLIDES_WITH_LIBRARY_SYMBOL",
                    also=("RESERVED_PREFIX",),
                    why="deliberately inverted",
                )
                third["turns"] = tuple(third["turns"]) + (bad,)
                out[2] = third
                return tuple(out)

            return sessions

        self._refuses(mutate, r"but .* runs earlier in the committed order|derived grounds")

    def test_an_invented_library_collision_target_refuses(self) -> None:
        def mutate(original):
            def sessions():
                out = list(original())
                third = dict(out[2])
                bad = builder._decl(
                    "declare not_in_any_corpus/1 (variable)",
                    name="not_in_any_corpus",
                    arity=1,
                    categories=("variable",),
                    code="COLLIDES_WITH_LIBRARY_SYMBOL",
                    why="names a head no census can contain",
                )
                third["turns"] = tuple(third["turns"]) + (bad,)
                out[2] = third
                return tuple(out)

            return sessions

        self._refuses(
            mutate, r"COLLIDES_WITH_LIBRARY_SYMBOL, but the committed order decides NONE"
        )

    def test_a_category_outside_the_schema_enum_on_an_admission_refuses(self) -> None:
        def mutate(original):
            def sessions():
                out = list(original())
                third = dict(out[2])
                bad = builder._admit(
                    "declare hedgehog_of/1 (hedgehog)", "hedgehog_of", 1, ("hedgehog",), "x"
                )
                third["turns"] = tuple(third["turns"]) + (bad,)
                out[2] = third
                return tuple(out)

            return sessions

        self._refuses(
            mutate, r"decides CATEGORY_NOT_IN_SCHEMA from the derived grounds"
        )

    def test_a_resurrected_design_time_deletion_refuses(self) -> None:
        def mutate(original):
            def sessions():
                out = list(original())
                third = dict(out[2])
                bad = builder._decl(
                    "declare ghost/1 (variable)",
                    name="ghost",
                    arity=1,
                    categories=("variable",),
                    code="UNBOUND_VARIABLE",
                    why="a code deleted at design time",
                )
                third["turns"] = tuple(third["turns"]) + (bad,)
                out[2] = third
                return tuple(out)

            return sessions

        self._refuses(mutate, r"not one of the eight committed refusal codes")


if __name__ == "__main__":
    unittest.main()
