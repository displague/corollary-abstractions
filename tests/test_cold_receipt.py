"""COLD RECEIPT — guards for CR-P0's registry census.

`docs/DESIGN-cold-receipt.md` §5 makes the registry a construction
prerequisite and §10's B1 row makes it the pilot: *"the one floor whose
meetability is a prerequisite rather than an argument."* These tests score the
two properties that make it a registry rather than a list — it recomputes, and
it contains no kind names — and they recompute rather than trust, on
`test_retraction_closure`'s R5 shape.

Later stages of the slice add their own classes here; this module grows with
the census it guards.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import cold_registry_census as census  # noqa: E402

ARTIFACT = REPO / "experiments" / "cold_registry_census.json"
WRITER = REPO / "scripts" / "cold_registry_census.py"
RULE = REPO / "cold" / "reconstruction_rule.json"
SUPPLEMENT = REPO / "experiments" / "conformance_ce3_supplement.json"


def _load() -> dict:
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def _sha256_lf(path: Path) -> str:
    """Canonical-LF digest, recomputed here rather than imported.

    A test hashing with the writer's own helper would agree with the writer
    even if the helper were wrong.
    """

    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class TheCensusIsARuleAndNotAList(unittest.TestCase):
    """§5's construction defect, scored: a hand-written kind list.

    *"A hand-written kind list presented as a registry is the construction
    defect ROADMAP-v0.21 §4.0(3) exists to catch."* The mechanical form of
    that sentence is this: no `kind_id` the census publishes may appear as a
    literal in the script that publishes it. If one did, the rule would be
    reading a name a maintainer wrote rather than reaching a site.
    """

    def test_no_published_kind_id_appears_in_the_writer(self) -> None:
        source = WRITER.read_text(encoding="utf-8")
        named = [
            record["kind_id"]
            for record in _load()["kinds"]
            if record["kind_id"] in source
        ]
        self.assertEqual(named, [], "the writer names a kind it publishes")

    def test_no_excluded_path_is_named_in_the_writer_beyond_two_declared(self) -> None:
        # Exactly two paths the writer is allowed to name, each for a reason
        # the rule states out loud:
        #   scripts/serve_chat.py  — `_route_vocabulary` reads LINE_GRAMMAR as
        #     a route vocabulary, which the rule text names as its source;
        #   scripts/dump_server.py — `seeded_exclusion_check` asks whether the
        #     rule reached §5's seeded exclusion unaided, which requires
        #     quoting the seed.
        # Every other excluded path must be one the rule found.
        source = WRITER.read_text(encoding="utf-8")
        declared = {"scripts/serve_chat.py", "scripts/dump_server.py"}
        named = sorted(
            {
                row["path"]
                for row in _load()["excluded"]
                if row["path"] not in declared and row["path"] in source
            }
        )
        self.assertEqual(named, [], "the writer names an excluded path")

    def test_the_seeded_exclusion_is_reproduced_by_the_rule(self) -> None:
        check = _load()["seeded_exclusion_check"]
        self.assertTrue(check["reproduced_by_the_rule"])
        # It must be a *rule* that reached it, and the rule's own line range is
        # published beside the seed's rather than adjusted to match it.
        self.assertTrue(check["rule_that_reached_it"])
        self.assertTrue(check["line_range_the_rule_computed"])

    def test_the_exclusion_reason_is_the_rules_and_not_a_judgement(self) -> None:
        rules = census.ENUMERATION_RULE["exclusion_rules"]
        templates = {row["reason_template"] for row in rules.values()}
        for row in _load()["excluded"]:
            with self.subTest(path=row["path"], line=row["line_range"][0]):
                self.assertIn(row["reason"], templates)


class TheCensusRecomputes(unittest.TestCase):
    """R5's arithmetic, applied to the seal B10 freezes."""

    def test_the_seal_and_counts_recompute_from_the_committed_tree(self) -> None:
        fresh = census.build_census(REPO)
        committed = _load()
        self.assertEqual(committed["census_seal"], fresh["census_seal"])
        self.assertEqual(committed["counts"], fresh["counts"])

    def test_the_seal_covers_the_rule_the_kinds_and_the_exclusions(self) -> None:
        committed = _load()
        recomputed = census.census_seal(
            committed["kinds"], committed["excluded"]
        )
        self.assertEqual(committed["census_seal"], recomputed)

    def test_a_changed_kind_moves_the_seal(self) -> None:
        # The seal must be able to go red. A census_seal that survived an
        # edited kind record would be freezing nothing.
        committed = _load()
        mutated = json.loads(json.dumps(committed["kinds"]))
        mutated[0]["kind_id"] = mutated[0]["kind_id"] + "-tampered"
        self.assertNotEqual(
            committed["census_seal"],
            census.census_seal(mutated, committed["excluded"]),
        )


class TheCensusCarriesItsProvenance(unittest.TestCase):
    """`test_retraction_closure.PROVENANCED_LEDGERS`' pattern.

    That guard exists because two v0.22 item-1 artifacts attested a writer
    digest no committed file had. This artifact joins the same shape and is
    checked the same way.
    """

    def test_the_writer_digest_matches_the_committed_writer(self) -> None:
        block = _load()["provenance"]
        self.assertEqual(block["writer"], "scripts/cold_registry_census.py")
        self.assertEqual(block["writer_sha256_lf"], _sha256_lf(WRITER))
        self.assertTrue(block["emitted_at_generation"])

    def test_the_inputs_are_sorted_repo_relative_and_real(self) -> None:
        rows = _load()["provenance"]["inputs"]
        self.assertTrue(rows)
        paths = [row["path"] for row in rows]
        self.assertEqual(paths, sorted(paths))
        for row in rows:
            self.assertNotIn("\\", row["path"])
            self.assertFalse(Path(row["path"]).is_absolute(), row)
            self.assertTrue((REPO / row["path"]).is_file(), row)

    def test_two_input_digests_match_the_committed_files(self) -> None:
        rows = _load()["provenance"]["inputs"]
        for row in (rows[0], rows[-1]):
            self.assertEqual(row["sha256_lf"], _sha256_lf(REPO / row["path"]), row)

    def test_no_absolute_path_leaks_into_the_artifact(self) -> None:
        # R5 forbids anything that differs between two checkouts of the same
        # bytes, and a resolved dependency path is where one would leak.
        text = ARTIFACT.read_text(encoding="utf-8")
        self.assertNotIn(str(Path.home()), text)
        self.assertNotIn(str(REPO), text)


class B1IsMeetableOrTheSlicePublishesTheStop(unittest.TestCase):
    """§5's stop clause, adjudicated by the artifact rather than by a reader."""

    def test_every_published_kind_carries_a_rule_resolved_route(self) -> None:
        for record in _load()["kinds"]:
            with self.subTest(kind=record["kind_id"]):
                self.assertTrue(record["emitting_routes"])
                for row in record["emitting_routes"]:
                    self.assertIn(
                        row["route_source"],
                        {"dominating_guard", "writer_is_the_route"},
                    )

    def test_the_stop_clause_is_adjudicated_and_its_test_is_recorded(self) -> None:
        stop = _load()["stop_clause"]
        self.assertIn("fired", stop)
        self.assertEqual(
            stop["b1_unmapped_emitting_routes"],
            len(stop["kinds_with_no_machine_resolved_route"]),
        )
        self.assertEqual(stop["fired"], bool(stop["kinds_with_no_machine_resolved_route"]))

    def test_the_recall_probe_prices_what_the_rule_does_not_reach(self) -> None:
        # The census claims no coverage over the wider net's uncovered sites;
        # the probe exists so that claim is a number rather than a silence.
        probe = _load()["recall_probe"]
        self.assertGreater(probe["wider_net_sites"], 0)
        self.assertEqual(
            probe["uncovered_site_count"], len(probe["uncovered_sites"])
        )


class ThePinTableWasCapturedBeforeAnyRename(unittest.TestCase):
    """§6's ordering repair (C4), scored where it bites.

    `session_ledger.pins()` lives under `scripts/` and imports `serve_chat`
    and `write_stage`; after the harness's rename it cannot run. If this table
    is not in CR-P0's artifact, it does not exist later.
    """

    def test_the_pins_were_captured_and_cover_PIN_FIELDS(self) -> None:
        import session_ledger  # noqa: PLC0415

        table = _load()["pin_table"]
        self.assertEqual(table["status"], "captured", table.get("error"))
        self.assertTrue(table["captured_before_rename"])
        self.assertEqual(table["pin_fields"], sorted(session_ledger.PIN_FIELDS))
        self.assertEqual(sorted(table["pins"]), sorted(session_ledger.PIN_FIELDS))

    def test_the_pin_divergence_is_recorded_and_not_adjudicated(self) -> None:
        # §11: three lean-toolchain files pin v4.32.2 and a fourth pins
        # v4.29.1. B9 cedes drift to a parked lane, so the census records the
        # divergence and refuses to decide it.
        for row in _load()["pin_divergence"]:
            self.assertFalse(row["adjudicated"])


class TheExternalDepsSeedRecordsChoiceAndDeclinesToTagBytes(unittest.TestCase):
    """§8's split, scored: CR-P0 assigns `selection_provenance`, not `provenance`.

    The first version of the design defined a single tag `lean.exe` satisfied
    both values of. The repair is two fields with two assigners, and a census
    that pre-assigned the harness's field would hand it a declaration to read
    instead of a fact to test.
    """

    def test_the_census_assigns_selection_provenance_only(self) -> None:
        for row in _load()["external_deps_seed"]:
            with self.subTest(dep=row["name"]):
                self.assertIn(
                    row["selection_provenance"],
                    {"repository_file", "machine_state", "harness_constant"},
                )
                self.assertNotIn("provenance", row)

    def test_the_lean_pin_is_over_the_executing_binarys_own_bytes(self) -> None:
        row = next(
            r for r in _load()["external_deps_seed"] if r["name"] == "lean.exe"
        )
        self.assertRegex(row["pin_hash"], r"^[0-9a-f]{64}$")
        if row["recomputed_digest_now"] is None:
            self.skipTest("the pinned checker is not installed on this machine")
        # Recomputed against the binary while the program is still present, so
        # a later mismatch is about the harness rather than about unnoticed
        # drift.
        self.assertTrue(row["recomputed_matches_pin"])

    def test_the_unpinned_dependencies_say_so(self) -> None:
        rows = {r["name"]: r for r in _load()["external_deps_seed"]}
        for name in ("mypy", "jsonschema"):
            row = next(r for k, r in rows.items() if k == name)
            self.assertIsNone(row["pin_hash"])
            self.assertEqual(row["selection_provenance"], "machine_state")


class CRP1PublishesARuleAndTheGapInIt(unittest.TestCase):
    """§12's CR-P1, scored by re-deriving it rather than by reading it.

    The templates below are written out again here, deliberately. A test that
    imported `cold_reconstruct_ce3.POSITIVE_TEMPLATE` would agree with the
    rule even if the rule were wrong; what has to hold is that *these* bytes
    reach *those* digests.
    """

    POSITIVE = "example : ({prop} : Prop) := by decide\n"
    NEGATIVE = "example : (¬({prop}) : Prop) := by decide\n"

    @classmethod
    def setUpClass(cls) -> None:
        cls.rule = json.loads(RULE.read_text(encoding="utf-8"))
        cls.supplement = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
        cls.rows = [r for r in cls.supplement["rows"] if "checker_receipt" in r]

    @staticmethod
    def _digest(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def test_every_committed_row_reconstructs_both_digests(self) -> None:
        misses = []
        for row in self.rows:
            receipt = row["checker_receipt"]
            prop = row["substituted_proposition"]
            if self._digest(self.POSITIVE.format(prop=prop)) != receipt[
                "positive_probe"
            ]["source_sha256"]:
                misses.append((row["statement_id"], "positive"))
            if self._digest(self.NEGATIVE.format(prop=prop)) != receipt[
                "negative_probe"
            ]["source_sha256"]:
                misses.append((row["statement_id"], "negative"))
        self.assertEqual(misses, [])
        self.assertEqual(
            self.rule["verification"]["rows_whose_both_digests_reconstruct"],
            len(self.rows),
        )

    def test_the_digest_is_sensitive_to_the_trailing_newline(self) -> None:
        # The vacuity check. If the digest did not move when the newline was
        # dropped, the reconstruction rule's step 3 would be claiming a
        # precision it does not have, and B2's floor would rest on a digest
        # that agreed with anything shaped roughly right.
        prop = self.rows[0]["substituted_proposition"]
        recorded = self.rows[0]["checker_receipt"]["positive_probe"][
            "source_sha256"
        ]
        without = self.POSITIVE.format(prop=prop).rstrip("\n")
        self.assertNotEqual(self._digest(without), recorded)
        crlf = self.POSITIVE.format(prop=prop).replace("\n", "\r\n")
        self.assertNotEqual(self._digest(crlf), recorded)

    def test_the_negation_glyph_is_absent_from_the_artifact(self) -> None:
        # §12's finding, recomputed: the artifact carries only the positive
        # template, so a reconstructor must supply half the rule from outside
        # the receipt. Publishing that gap is what strengthens B2.
        text = SUPPLEMENT.read_text(encoding="utf-8")
        self.assertEqual(text.count("¬"), 0)
        gap = self.rule["unrecorded_half_of_the_rule"]
        self.assertEqual(gap["occurrences_in_artifact_text"], 0)
        self.assertEqual(gap["occurrences_in_artifact_bytes"], 0)
        self.assertTrue(gap["unrecorded_half"])

    def test_the_recorded_pattern_is_only_the_positive_template(self) -> None:
        patterns = {
            row["checker_receipt"]["pattern"]
            for row in self.rows
            if "pattern" in row["checker_receipt"]
        }
        self.assertEqual(patterns, {self.POSITIVE.rstrip("\n").replace("{prop}", "<prop>")})

    def test_b2_meetability_is_adjudicated_by_the_reconstruction(self) -> None:
        meet = self.rule["b2_meetability"]
        verification = self.rule["verification"]
        self.assertEqual(
            meet["every_committed_row_reconstructs"],
            verification["rows_with_a_receipt"]
            == verification["rows_whose_both_digests_reconstruct"],
        )
        self.assertEqual(
            meet["b2_floor_meetable"],
            meet["rule_published_as_a_rule"]
            and meet["every_committed_row_reconstructs"],
        )

    def test_the_transcripts_carry_the_bytes_and_not_a_summary(self) -> None:
        for transcript in self.rule["transcripts"]:
            for side in ("positive", "negative"):
                probe = transcript[side]
                self.assertEqual(
                    self._digest(probe["source_text"]), probe["recorded_sha256"]
                )
                self.assertEqual(
                    probe["source_bytes_len"],
                    len(probe["source_text"].encode("utf-8")),
                )

    def test_the_rule_carries_its_provenance(self) -> None:
        block = self.rule["provenance"]
        self.assertEqual(block["writer"], "scripts/cold_reconstruct_ce3.py")
        self.assertEqual(
            block["writer_sha256_lf"], _sha256_lf(REPO / block["writer"])
        )
        for row in block["inputs"]:
            self.assertEqual(
                row["sha256_lf"], _sha256_lf(REPO / row["path"]), row
            )


#: Run 1's artifacts, retained UNEDITED as the record of what the defective
#: removal arm actually produced. They are not the census any sentence rests
#: on; amendment 2's run is.
RUN1_CENSUS = REPO / "cold" / "census.json"
RUN1_RESULT_GATE = REPO / "cold" / "result_gate.json"

#: Amendment 2's run — the corrected census, and the one the gate reads.
COLD_CENSUS = REPO / "cold" / "census_run2.json"
PATH_AUDIT = REPO / "cold" / "path_audit_run2.txt"
PATH_AUDIT_JSON = REPO / "cold" / "evidence_run2" / "path_audit.json"
TREE_MANIFEST = REPO / "cold" / "evidence_run2" / "tree_manifest_before.json"
SCRAMBLE = REPO / "cold" / "scramble_baseline.json"
RESULT_GATE = REPO / "cold" / "result_gate_run2.json"


def _cold() -> dict:
    return json.loads(COLD_CENSUS.read_text(encoding="utf-8"))


class ThePathAuditCarriesBothAssertions(unittest.TestCase):
    """§6's C2 repair, scored where it was written.

    *"§1's own exhibit is the counter-example: replay_session.py:69-71 reaches
    scripts/ through Path(__file__).resolve().parents[1] and sys.path.insert.
    No PATH setting anywhere would have stopped it."* So a harness that proved
    only the PATH claim would have proved the wrong thing, and these tests are
    the reason it cannot.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads(PATH_AUDIT_JSON.read_text(encoding="utf-8"))

    def test_assertion_one_the_program_tree_is_unresolvable(self) -> None:
        first = self.audit["assertion_1_program_tree_unresolvable"]
        self.assertTrue(first["holds"])
        self.assertTrue(first["imports"])
        for row in first["imports"]:
            self.assertFalse(row["imported"], row["module"])
            # The traceback IS the evidence; a bare False would be a claim.
            self.assertIn("ModuleNotFoundError", row["traceback"])

    def test_assertion_two_no_sys_path_entry_resolves_inside_the_repo(self) -> None:
        second = self.audit["assertion_2_no_sys_path_entry_inside_the_repository"]
        self.assertTrue(second["holds"])
        inside = [row for row in second["sys_path"] if row["inside_repository"]]
        self.assertEqual(inside, [])

    def test_no_PATH_entry_resolves_inside_the_repository(self) -> None:
        self.assertEqual(self.audit["path_entries_inside_repository"], [])
        for row in self.audit["path_entries"]:
            self.assertIsNotNone(row["listing_sha256"], row["resolved"])

    def test_the_interpreter_is_not_the_repositorys_own_virtualenv(self) -> None:
        # The harness cannot exclude its own interpreter (§6 names it in the
        # not-excluded list). It can decline to use the one the program
        # prepared, and this is that declining, checked.
        interpreter = self.audit["interpreter"]
        self.assertFalse(interpreter["inside_repository"])
        self.assertTrue(interpreter["flags_no_site"])
        self.assertTrue(interpreter["flags_isolated"])

    def test_the_rendered_audit_states_both_assertions_and_the_scope(self) -> None:
        text = PATH_AUDIT.read_text(encoding="utf-8")
        self.assertIn("ASSERTION 1", text)
        self.assertIn("ASSERTION 2", text)
        self.assertIn("BOTH ASSERTIONS HOLD: True", text)
        # The scope travels with the number; it is not a footnote.
        self.assertIn("does NOT exclude", text)
        self.assertIn("weaker", text)


class TheHarnessRestoredTheTreeItMeasured(unittest.TestCase):
    """§6's C4: the rename is a known, reversible side effect with a restore
    path, and a mismatch is a harness failure reported as such, never absorbed.
    """

    def test_the_working_tree_is_byte_identical_across_the_rename(self) -> None:
        tree = _cold()["scope"]["working_tree"]
        self.assertTrue(tree["program_tree_restored"])
        self.assertEqual(
            tree["digest_before_rename"]["digest"],
            tree["digest_after_restore"]["digest"],
        )
        self.assertTrue(tree["byte_identical"])

    def test_the_scope_names_what_the_harness_does_not_exclude(self) -> None:
        scope = _cold()["scope"]
        self.assertTrue(scope["weaker_than_a_container"])
        joined = " ".join(scope["not_excluded"]).lower()
        for item in ("registry", "userprofile", "site-packages", "interpreter"):
            self.assertIn(item, joined)


class EveryArmIsScoredAndCouldHaveGoneRed(unittest.TestCase):
    """§7's four arms and §10's meetability rows, checked as numbers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cold = _cold()
        cls.arms = cls.cold["arms"]
        cls.gate = cls.cold["gate"]

    def test_b3_runs_three_mutations_that_are_different_in_kind(self) -> None:
        runs = {row["mutation"]: row for row in self.arms["tamper"]["runs"]}
        self.assertEqual(set(runs), {"content", "digest", "binding"})
        signatures = {}
        for name, row in runs.items():
            self.assertFalse(row["discarded"], name)
            self.assertTrue(row["witness_of_difference"]["changed"], name)
            self.assertEqual(row["outcome"], "FAIL", name)
            checks = tuple(
                sorted(
                    {
                        check
                        for failure in (row["failed_checks"] or [])
                        for check in failure["failed_checks"]
                    }
                )
            )
            signatures[name] = checks
        # v0.21's B8 arms "were one tamper shape run twice". Three distinct
        # failure signatures is the machine form of "different in kind".
        self.assertEqual(len(set(signatures.values())), 3, signatures)
        # The digest mutation's whole point: it makes step 3 agree by
        # construction, so ONLY the invocation can catch it.
        self.assertNotIn("positive_digest", signatures["digest"])
        self.assertIn("positive_exit_code", signatures["digest"])
        # The binding mutation leaves every file and digest internally
        # consistent; only the attribution is wrong.
        self.assertIn("positive_digest", signatures["binding"])
        self.assertNotIn("positive_exit_code", signatures["binding"])
        self.assertTrue(self.gate["B3"]["green"])

    def test_b4_fails_loud_and_names_the_missing_dependency(self) -> None:
        arm = self.arms["omission"]
        self.assertFalse(arm["gate"]["silent_pass"])
        self.assertTrue(arm["gate"]["failed_loud"])
        self.assertTrue(arm["gate"]["named_the_dependency"])
        self.assertIn(arm["removed_dependency"], arm["stdout_head"])

    def test_b5_has_a_working_negative_control_and_no_sham_survivor(self) -> None:
        arm = self.arms["sham"]
        # The instrument must be able to say no.
        self.assertTrue(arm["negative_control"]["real_checker_rejects_the_known_bad_bundle"])
        self.assertEqual(arm["runs"]["real_checker_good_bundle"]["outcome"], "PASS")
        self.assertEqual(arm["runs"]["real_checker_known_bad_bundle"]["outcome"], "FAIL")
        self.assertEqual(arm["gate"]["value"], 0)
        self.assertFalse(self.cold["voiding_sentence"]["fired"])
        # The weakness in the substitution is disclosed rather than glossed.
        self.assertIn("weaker than", arm["disclosed_weakness"])

    def test_b6_ran_the_budgeted_arm_and_published_its_bound_honestly(self) -> None:
        arm = self.arms["scramble"]
        self.assertEqual(arm["bundles_requested"], 200)
        self.assertEqual(arm["bundles_run"], 200)
        self.assertEqual(arm["bundles_passed"], 0)
        self.assertAlmostEqual(arm["gate"]["rule_of_three_upper_bound"], 0.015)
        self.assertIn("never a measured rate", arm["gate"]["upper_bound_is_not_a_measured_rate"])
        self.assertEqual(arm["checker_invocations"], 200 * 50)

    def test_b6_prices_what_its_invocation_step_can_discriminate(self) -> None:
        # A vacuity check on the vacuity control. Every committed row of this
        # kind records the same exit-code pair, so a permutation leaves step 4
        # unchanged and only step 3 can catch it. Measured, not explained after.
        discrimination = self.arms["scramble"][
            "what_the_invocation_step_can_discriminate"
        ]
        self.assertEqual(len(discrimination["distinct_recorded_exit_code_pairs"]), 1)

    def test_b7_confirms_every_needs_program_by_removal(self) -> None:
        needs = [k for k in self.cold["kinds"] if k["verdict"] == "NEEDS-PROGRAM"]
        self.assertTrue(needs)
        for kind in needs:
            blocking = kind["blocking_dependency"]
            self.assertTrue(blocking["confirmed_by_removal"], kind["kind_id"])
            self.assertNotEqual(kind["verdict_evidence"]["exit_code"], 0)
            self.assertIn("ModuleNotFoundError", kind["verdict_evidence"]["stderr_head"])
        self.assertEqual(self.gate["B7"]["denominator"], len(needs))
        self.assertTrue(self.gate["B7"]["green"])

    def test_b8_applies_its_denominator_rule(self) -> None:
        b8 = self.gate["B8"]
        self.assertGreaterEqual(b8["denominator"], 5)
        self.assertTrue(b8["applies"])
        self.assertLess(b8["survives_fraction"], 0.9)

    def test_b11_assigns_provenance_from_the_bytes(self) -> None:
        deps = {d["name"]: d for d in self.arms["provenance"]["dependencies"]}
        lean = deps["lean.exe"]
        self.assertEqual(lean["provenance"], "third_party_pinned")
        test = lean["provenance_test"]
        self.assertTrue(test["a_pin_is_over_the_executing_artifact"])
        self.assertTrue(test["b_pin_identifies_a_third_partys_release"])
        self.assertEqual(test["recomputed_sha256"], lean["pin_hash"])
        self.assertEqual(test["assigner"], "the harness, from the bytes")
        for name, dep in deps.items():
            if name == "lean.exe":
                continue
            self.assertEqual(dep["provenance"], "program_configured", name)


class TheResultGateLicensesOneSentenceAndNothingWider(unittest.TestCase):
    """§13, executed. The reading is computed from the census, not written
    about it, so the sentence a partition licenses cannot widen on the way to
    a release note.
    """

    #: §13's table, transcribed here independently of the writer's copy. Two
    #: transcriptions of the same frozen strings: if either moves, this fails
    #: rather than the gate quietly moving.
    PARTITIONS = {
        "B1 unmeetable (CR-P0's stop)",
        "voiding sentence fires",
        "0 kinds SURVIVE (B2 red)",
        "all UNTESTED via B11",
        ">=1 SURVIVES, some NEEDS-PROGRAM",
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = json.loads(RESULT_GATE.read_text(encoding="utf-8"))
        cls.cold = _cold()

    def test_the_partition_is_the_one_the_counts_imply(self) -> None:
        counts = self.cold["counts"]
        self.assertIn(self.gate["partition"], self.PARTITIONS)
        if self.cold["voiding_sentence"]["fired"]:
            expected = "voiding sentence fires"
        elif self.cold["gate"]["B1"]["value"] != 0:
            expected = "B1 unmeetable (CR-P0's stop)"
        elif counts["SURVIVES"] == 0:
            expected = "0 kinds SURVIVE (B2 red)"
        elif counts["NEEDS-PROGRAM"] == 0 and counts["SURVIVES"] == 0:
            expected = "all UNTESTED via B11"
        else:
            expected = ">=1 SURVIVES, some NEEDS-PROGRAM"
        self.assertEqual(self.gate["partition"], expected)

    def test_R_C_is_green_only_on_all_three_clauses(self) -> None:
        r_c = self.gate["R_C"]
        self.assertEqual(
            r_c["green"],
            not self.gate["gate_reds"]
            and not self.gate["voiding_sentence_fired"]
            and self.gate["ordering"]["cr_p0_precedes_cr_p1"],
        )

    def test_the_prerequisites_were_committed_in_order(self) -> None:
        # The clause is about when each prerequisite LANDED. Amendment 2 gave
        # CR-P0 a later commit than CR-P1; reading the latest commit instead of
        # the first would let a repair retroactively falsify an ordering that
        # did hold, so the gate reads the introducing commit and records both.
        ordering = self.gate["ordering"]
        self.assertTrue(ordering["cr_p0_first_commit"])
        self.assertTrue(ordering["cr_p1_first_commit"])
        self.assertTrue(ordering["cr_p0_precedes_cr_p1"])
        self.assertNotEqual(
            ordering["cr_p0_latest_commit"], ordering["cr_p0_first_commit"]
        )

    def test_the_sentence_attaches_nothing_wider(self) -> None:
        # "Nothing more — no rate, no other machine, no person."
        sentence = self.gate["licensed_sentence"]
        self.assertNotIn("%", sentence)
        self.assertNotIn("stranger", sentence.lower())
        self.assertNotIn("anyone", sentence.lower())
        joined = " ".join(self.gate["non_claims"]).lower()
        self.assertIn("no stranger-success claim", joined)
        self.assertIn("no composition claim", joined)
        self.assertIn("no retroactive effect", joined)

    def test_the_named_kinds_are_the_verdicts_the_census_published(self) -> None:
        if self.gate["partition"] != ">=1 SURVIVES, some NEEDS-PROGRAM":
            self.skipTest("a different partition is licensed")
        attached = self.gate["attached_to_the_sentence"]
        survives = [k["kind_id"] for k in self.cold["kinds"] if k["verdict"] == "SURVIVES"]
        needs = [k["kind_id"] for k in self.cold["kinds"] if k["verdict"] == "NEEDS-PROGRAM"]
        self.assertEqual(attached["scoped_to_kinds"], survives)
        self.assertEqual(attached["needs_program_kinds_published_by_name"], needs)


class TheScramblePathDoesNotNameAMissingGlobal(unittest.TestCase):
    """Run 2 of the v0.23 suite-gate re-seal crashed here.

    `run_scramble` looked up `EXECUTABLE_KIND`, a name the harness has
    never bound. Live run 2 always passed `--reuse-scramble`, so the
    branch never executed until a registry re-seal tried to run B6.
    The kind is discovered in `main` and passed in; a global of that
    name must not return.
    """

    def test_the_harness_does_not_name_EXECUTABLE_KIND(self) -> None:
        source = (REPO / "harness" / "cold_harness.py").read_text(encoding="utf-8")
        self.assertNotIn("EXECUTABLE_KIND", source)


class TheColdArtifactsCarryTheirProvenance(unittest.TestCase):
    """PROVENANCED_LEDGERS' pattern for the harness's own three artifacts.

    The harness reimplements the block rather than importing
    `scripts/report_provenance.py`, because it imports nothing from this
    repository. The guard is the same either way.
    """

    def test_each_cold_artifact_names_its_writer_and_its_digest_matches(self) -> None:
        for artifact, writer in (
            (COLD_CENSUS, "harness/cold_harness.py"),
            (RESULT_GATE, "harness/result_gate.py"),
        ):
            with self.subTest(artifact=artifact.name):
                block = json.loads(artifact.read_text(encoding="utf-8"))["provenance"]
                self.assertEqual(block["writer"], writer)
                self.assertEqual(
                    block["writer_sha256_lf"], _sha256_lf(REPO / writer)
                )
                self.assertTrue(block["emitted_at_generation"])
                for row in block["inputs"]:
                    self.assertEqual(
                        row["sha256_lf"], _sha256_lf(REPO / row["path"]), row
                    )


class RunOneIsRetainedAndItsProvenanceIsHistorical(unittest.TestCase):
    """Amendment 2 kept run 1 unedited, so its blocks attest a PAST writer.

    `PROVENANCED_LEDGERS` asks whether an artifact's writer digest matches the
    writer as committed NOW. For a deliberately retained artifact that is the
    wrong question — the right one is whether it matches the writer as
    committed AT ITS RUN. These artifacts therefore come off the live list and
    are checked against history instead, which is a stronger claim than the
    live guard makes, not a weaker one.
    """

    #: The commits at which run 1's writers stood when run 1 executed.
    RUN1_HARNESS_COMMIT = "d4b4753"
    RUN1_GATE_COMMIT = "aca2f2a"

    @staticmethod
    def _blob_sha256_lf(commit: str, path: str) -> str:
        blob = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{commit}:{path}"],
            capture_output=True,
            check=True,
        ).stdout
        return hashlib.sha256(blob.replace(b"\r\n", b"\n")).hexdigest()

    def test_run_one_artifacts_are_still_present_and_unedited(self) -> None:
        for artifact in (RUN1_CENSUS, RUN1_RESULT_GATE, SCRAMBLE):
            self.assertTrue(artifact.is_file(), artifact)

    def test_run_one_blocks_match_the_writers_as_committed_at_run_one(self) -> None:
        for artifact, writer, commit in (
            (RUN1_CENSUS, "harness/cold_harness.py", self.RUN1_HARNESS_COMMIT),
            (SCRAMBLE, "harness/cold_harness.py", self.RUN1_HARNESS_COMMIT),
            (RUN1_RESULT_GATE, "harness/result_gate.py", self.RUN1_GATE_COMMIT),
        ):
            with self.subTest(artifact=artifact.name):
                block = json.loads(artifact.read_text(encoding="utf-8"))["provenance"]
                self.assertEqual(block["writer"], writer)
                self.assertEqual(
                    block["writer_sha256_lf"],
                    self._blob_sha256_lf(commit, writer),
                )

    def test_run_one_recorded_the_defective_arm_and_run_two_says_so(self) -> None:
        # Run 1's nine confirmed_by_removal verdicts are retained as the record
        # of what the defective arm produced. The corrected census must name
        # the defect rather than quietly superseding it.
        amendment = _cold()["amendment"]
        self.assertEqual(amendment["amendment"], 2)
        self.assertIn("-I", amendment["flags_dropped"])
        self.assertIn("PYTHONPATH was ignored", amendment["defect"])
        self.assertIn(
            "cold/census.json", amendment["run_one_artifacts_retained_unedited"]
        )


class TheRemovalArmDependsOnTheRemoval(unittest.TestCase):
    """C1, the defect amendment 2 repairs, scored so it cannot come back.

    Run 1 ran `python -S -I -c "import <module>"`. `-I` implies `-E`, so
    `PYTHONPATH` was discarded and the program tree was never on the child's
    path: the import failed identically whether `scripts/` was present or
    absent. Nine `confirmed_by_removal` verdicts rested on a check that could
    not go red for the reason it claimed.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.cold = _cold()
        cls.needs = [
            k for k in cls.cold["kinds"] if k["verdict"] == "NEEDS-PROGRAM"
        ]

    def test_the_isolated_flag_is_gone_from_every_removal_argv(self) -> None:
        for kind in self.cold["kinds"]:
            arm = kind.get("removal_arm")
            if not arm:
                continue
            for limb in ("with_program_limb", "program_absent_limb"):
                for module, row in arm[limb].items():
                    with self.subTest(
                        kind=kind["kind_id"], limb=limb, module=module
                    ):
                        self.assertNotIn("-I", row["argv"])
                        self.assertTrue(row["pythonpath"].endswith("scripts"))

    def test_both_limbs_run_identical_argv_and_differ_only_in_the_removal(
        self,
    ) -> None:
        for kind in self.cold["kinds"]:
            arm = kind.get("removal_arm")
            if not arm:
                continue
            for module in arm["with_program_limb"]:
                with self.subTest(kind=kind["kind_id"], module=module):
                    present = arm["with_program_limb"][module]
                    absent = arm["program_absent_limb"][module]
                    self.assertEqual(present["argv"], absent["argv"])
                    self.assertEqual(present["pythonpath"], absent["pythonpath"])
                    self.assertTrue(present["program_tree_present"])
                    self.assertFalse(absent["program_tree_present"])

    def test_every_needs_program_has_a_succeeding_positive_control(self) -> None:
        # This is the assertion run 1 could not have passed. Without it,
        # "confirmed by removal" is a sentence about a failure that had
        # nothing to do with the removal.
        self.assertTrue(self.needs)
        for kind in self.needs:
            with self.subTest(kind=kind["kind_id"]):
                arm = kind["removal_arm"]
                self.assertTrue(arm["with_program_limb"])
                for module, row in arm["with_program_limb"].items():
                    self.assertTrue(row["import_succeeded"], module)
                for module, row in arm["program_absent_limb"].items():
                    self.assertFalse(row["import_succeeded"], module)
                    self.assertEqual(row["missing_module"], module)
                self.assertTrue(kind["blocking_dependency"]["confirmed_by_removal"])

    def test_a_kind_blocked_by_something_else_reads_untested_and_names_it(
        self,
    ) -> None:
        # H4/H5: the radius certificates' recheck_command runs
        # scripts/radius_recheck.py, which cannot import jsonschema — a
        # dependency of the repository's .venv, not of the program. With the
        # program FULLY PRESENT the procedure still cannot run, so the kind
        # cannot be scored NEEDS-PROGRAM however plausible that reading was.
        kind = next(
            k
            for k in self.cold["kinds"]
            if k["kind_id"] == "retraction_radius:certify"
        )
        self.assertEqual(kind["verdict"], "UNTESTED")
        self.assertEqual(
            kind["removal_arm"]["targets"]["selected_by"], "recheck_descriptor"
        )
        self.assertEqual(
            kind["removal_arm"]["targets"]["modules"], ["radius_recheck"]
        )
        self.assertIn("jsonschema", kind["blocking_dependency"]["name"])
        self.assertFalse(kind["blocking_dependency"]["confirmed_by_removal"])

    def test_the_removal_target_comes_from_the_descriptor_where_one_exists(
        self,
    ) -> None:
        # Removing the WRITER when the receipt names a RECHECKER would test the
        # wrong program and call the result a removal.
        kind = next(
            k
            for k in self.cold["kinds"]
            if k["kind_id"] == "retraction_radius:certify"
        )
        commands = kind["removal_arm"]["targets"]["descriptor_commands"]
        self.assertTrue(commands)
        for command in commands:
            self.assertIn("radius_recheck.py", command)
        self.assertNotIn(
            "retraction_radius", kind["removal_arm"]["targets"]["modules"]
        )

    def test_a_multi_route_kind_is_adjudicated_over_all_its_routes(self) -> None:
        # §5 names closure_query as an emitter of closure-receipt/1;
        # emitting_routes[0] is build_throughput_tasks. Run 1 tested only the
        # first.
        kind = next(
            k for k in self.cold["kinds"] if k["kind_id"] == "closure-receipt/1"
        )
        modules = kind["removal_arm"]["targets"]["modules"]
        self.assertIn("closure_query", modules)
        self.assertIn("build_throughput_tasks", modules)
        self.assertGreaterEqual(len(kind["removal_arm"]["with_program_limb"]), 2)


class TheArmsAreRecordedOnTheKindTheyRanOn(unittest.TestCase):
    """H1: a kind's own record must not contradict the arms block above it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cold = _cold()
        cls.executable = cls.cold["run"]["executable_kind"]["kind_id"]

    def test_the_executable_kind_is_discovered_and_not_a_literal(self) -> None:
        # M4: the harness finds it from the declared procedure type plus the
        # published reconstruction rule, so a second raw-invocation kind would
        # be picked up rather than ignored.
        discovered = self.cold["run"]["executable_kind"]
        self.assertIn(
            "declared_recheck_procedure.type", discovered["discovered_by"]
        )
        self.assertIn(
            self.executable,
            discovered["candidates_declaring_raw_checker_invocation"],
        )

    def test_the_kind_the_arms_ran_on_carries_their_results(self) -> None:
        kind = next(
            k for k in self.cold["kinds"] if k["kind_id"] == self.executable
        )
        for field in ("tamper_result", "omission_result", "sham_result"):
            with self.subTest(field=field):
                self.assertNotEqual(kind[field]["verdict"], "UNTESTED")
        self.assertEqual(kind["tamper_result"]["mutations_failed"], 3)
        self.assertEqual(kind["omission_result"]["verdict"], "FAIL_LOUD")
        self.assertEqual(kind["sham_result"]["survives_count"], 0)

    def test_other_kinds_say_why_no_arm_ran_rather_than_asserting_one(self) -> None:
        for kind in self.cold["kinds"]:
            if kind["kind_id"] == self.executable:
                continue
            with self.subTest(kind=kind["kind_id"]):
                self.assertEqual(kind["tamper_result"]["verdict"], "UNTESTED")
                self.assertIn("no procedure", kind["tamper_result"]["reason"])
                self.assertIn("M5", kind["omission_result"]["reason"])

    def test_the_arm_gate_rows_carry_their_one_kind_denominator(self) -> None:
        # M2: B3/B4/B5 are green over ONE kind and silent about eighteen.
        for name in ("B3", "B4", "B5"):
            row = self.cold["gate"][name]
            with self.subTest(gate=name):
                self.assertEqual(row["kinds_in_denominator"], 1)
                self.assertEqual(row["kind_in_denominator"], self.executable)
                self.assertTrue(row["scope_note"])

    def test_the_sham_arm_records_that_it_could_not_have_fired(self) -> None:
        # M3: the structural point, beside the interface weakness.
        mechanism = self.cold["arms"]["sham"]["mechanism"]
        self.assertIn("cannot read SURVIVES", mechanism["therefore"])
        self.assertIn("STRUCTURAL", mechanism["therefore"])
        self.assertIn("not claimed", mechanism["what_that_costs"])


class TheTreeIdentityRecomputesFromItsManifest(unittest.TestCase):
    """M5: the byte-identity claim is re-derived, not believed."""

    def test_the_summary_digest_recomputes_from_the_committed_manifest(self) -> None:
        manifest = json.loads(TREE_MANIFEST.read_text(encoding="utf-8"))
        entries = manifest["manifest"]
        recomputed = hashlib.sha256(
            "\n".join(entries).encode("utf-8")
        ).hexdigest()
        self.assertEqual(recomputed, manifest["digest"])
        reported = _cold()["scope"]["working_tree"]["digest_before_rename"]
        self.assertEqual(reported["digest"], recomputed)
        self.assertEqual(reported["files"], len(entries))

    def test_a_sample_of_manifest_digests_matches_the_files_on_disk(self) -> None:
        entries = json.loads(TREE_MANIFEST.read_text(encoding="utf-8"))["manifest"]
        for entry in (entries[0], entries[len(entries) // 2], entries[-1]):
            relative, _, digest = entry.rpartition(":")
            path = REPO / relative
            if not path.is_file():
                continue
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(), digest, relative
            )

    def test_pycache_is_excluded_by_a_named_rule(self) -> None:
        # The amended arm imports real modules, and a successful import writes
        # __pycache__ into the tree the harness is proving it did not disturb.
        # Both guards are in place: -B on the argv, and this exclusion.
        manifest = json.loads(TREE_MANIFEST.read_text(encoding="utf-8"))
        self.assertIn("__pycache__", manifest["excluded_by_name"])
        self.assertFalse([e for e in manifest["manifest"] if "__pycache__" in e])


class TheProseNumbersMatchTheArtifacts(unittest.TestCase):
    """H3: ANALYSIS quoted a pre-CR-P1 recall run and nobody noticed.

    Prose is where a stale number survives longest, so the prose is pinned to
    the artifact rather than to a reviewer's memory.
    """

    @staticmethod
    def _head() -> str:
        # Whitespace-normalised: prose wraps, and a number that fell across a
        # line break should not be able to hide from its own guard.
        head = (
            (REPO / "experiments" / "ANALYSIS.md")
            .read_text(encoding="utf-8")
            .split("\n---\n", 1)[0]
        )
        return re.sub(r"\s+", " ", head)

    def test_analysis_recall_numbers_are_the_registrys(self) -> None:
        registry = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        probe = registry["recall_probe"]
        admitted = probe["wider_net_sites"] - probe["uncovered_site_count"]
        head = self._head()
        self.assertTrue(
            f"{probe['uncovered_site_count']} uncovered" in head,
            "ANALYSIS uncovered-site count is stale",
        )
        self.assertTrue(
            f"{probe['wider_net_sites']} receipt-vocabulary sites" in head,
            "ANALYSIS wider-net count is stale",
        )
        self.assertTrue(
            f"admits {admitted} of" in head, "ANALYSIS admitted count is stale"
        )

    def test_analysis_partition_counts_are_the_censuss(self) -> None:
        counts = _cold()["counts"]
        head = self._head()
        for key in ("SURVIVES", "NEEDS-PROGRAM", "UNTESTED"):
            self.assertTrue(
                f"**{counts[key]}**" in head, f"ANALYSIS {key} count is stale"
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
