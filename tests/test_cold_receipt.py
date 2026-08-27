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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
