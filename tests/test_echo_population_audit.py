from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import echo_population_audit as epa  # noqa: E402
import echo_reparse as er  # noqa: E402


class Preregistration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(epa.PREREG.read_text(encoding="utf-8"))

    def test_the_audit_and_both_draws_are_ordered_after_registration(self) -> None:
        self.assertEqual(self.prereg["registered_before"][0],
                         "experiments/echo_population_audit.json")
        self.assertEqual(self.prereg["predictions"]["construction_gate"]["expected"],
                         "STOP_BEFORE_PILOT")

    def test_every_frozen_group_revalidates(self) -> None:
        rows = epa.revalidate(self.prereg)
        self.assertEqual({row["group"] for row in rows},
                         set(self.prereg["freeze_groups"]))
        # Re-aimed 2026-09-01 by amd-2026-09-01-native-population and
        # amd-2026-09-01-audit-instrument (ROADMAP-v0.25 §2), in the shape
        # tests.test_no_flip_census took on 2026-08-31 for the same mechanic.
        # A group either still agrees with its original digest or carries a
        # dated retirement naming a recorded amendment; anything else raised
        # inside revalidate. An un-retired group must still agree EXACTLY, so
        # this is a weaker assertion only for the two rows an amendment names.
        self.assertTrue(all(row["agrees"] or row.get("retired") for row in rows))
        for row in rows:
            if row.get("retired"):
                self.assertIn("retired_by", row)
        live = [row["group"] for row in rows if not row.get("retired")]
        self.assertEqual(sorted(live),
                         ["resolver_fixtures", "second_voice_population"])
        native = next(row for row in rows if row["group"] == "native_population")
        self.assertGreater(len(native["members"]), 20)

    def test_group_membership_changes_the_digest(self) -> None:
        digest, _ = epa.group_manifest(["data/*/nodes.json"])
        narrower, _ = epa.group_manifest(["data/logic/nodes.json"])
        self.assertNotEqual(digest, narrower)

    def test_digest_drift_refuses_before_measurement(self) -> None:
        """Re-aimed 2026-09-01 onto a group no amendment has retired.

        This forged `native_population` until that group was retired by
        amd-2026-09-01-native-population, at which point forging it proves
        nothing — a retired group is reported and not enforced, which is the
        whole content of the amendment. The check itself is unchanged and is
        made against a LIVE group, so drift still refuses before measurement.
        """
        forged = copy.deepcopy(self.prereg)
        group = forged["freeze_groups"]["second_voice_population"]
        self.assertNotIn("retired_for_future_comparisons", group)
        group["expected_digest"] = "0" * 64
        with self.assertRaises(epa.AuditRefusal):
            epa.revalidate(forged)

    def test_retiring_a_group_is_not_a_way_to_stop_checking_it(self) -> None:
        """The escape hatch the 2026-09-01 amendments must not have opened.

        A retirement is a pin RETIRED, never a pin deleted: the marker has to
        name an amendment this prereg actually records, or revalidate refuses
        rather than silently dropping the group. Without this, adding four
        words to a freeze group would launder any file out of every check it
        was under.
        """
        forged = copy.deepcopy(self.prereg)
        forged["freeze_groups"]["second_voice_population"]["expected_digest"] = "0" * 64
        forged["freeze_groups"]["second_voice_population"][
            "retired_for_future_comparisons"] = {"amendment": "amd-that-does-not-exist"}
        with self.assertRaisesRegex(epa.AuditRefusal, "does not record"):
            epa.revalidate(forged)

    def test_resolver_fixture_ids_belong_to_the_frozen_question_set(self) -> None:
        seal = json.loads(
            (ROOT / "experiments" / "plain_input_corpus_seal.json").read_text(
                encoding="utf-8")
        )
        question_set = json.loads(
            (ROOT / "experiments" / "plain_question_set.json").read_text(
                encoding="utf-8")
        )
        resolver = set(seal["denominators"][
            "resolver_found_before_the_proposer_is_consulted"
        ]["question_ids"])
        questions = {row["question_id"] for row in question_set["questions"]}
        self.assertEqual(len(resolver), 13)
        self.assertLessEqual(resolver, questions)


class Reparser(unittest.TestCase):
    def test_import_closure_contains_no_renderer_module(self) -> None:
        self.assertEqual(epa.import_closure("scripts/echo_reparse.py"),
                         ["scripts/echo_reparse.py"])

    def test_dynamic_import_is_refused(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "scripts") as scratch:
            path = Path(scratch) / "dynamic_probe.py"
            path.write_text("import importlib\nimportlib.import_module('foreign_voice')\n",
                            encoding="utf-8")
            relative = path.relative_to(ROOT).as_posix()
            with self.assertRaisesRegex(epa.AuditRefusal, "dynamic import"):
                epa.import_closure(relative)

    def test_all_committed_surfaces_recover_the_stored_token_sequence(self) -> None:
        run = json.loads(
            (ROOT / "experiments" / "foreign_voice_rate2.json").read_text(
                encoding="utf-8")
        )
        for row in run["b1"]["receipts"]:
            with self.subTest(statement_id=row["statement_id"]):
                self.assertEqual(er.reparse(row["surface"]), row["roundtrip_text"])

    def test_slots_decimals_and_longest_match_are_literal(self) -> None:
        self.assertEqual(
            er.reparse("variable zero equals twenty-three point five"),
            "v0 = 23.5",
        )

    def test_malformed_decimal_refuses(self) -> None:
        with self.assertRaises(er.ReparseError):
            er.reparse("point")

    def test_unknown_word_refuses(self) -> None:
        with self.assertRaises(er.ReparseError):
            er.reparse("thiswordhasnorow")


class ClosedFormGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(epa.PREREG.read_text(encoding="utf-8"))
        cls.observed = dict(cls.prereg["predictions"]["population"])

    def test_registered_map_derives_b1_fire_b3_b4_miss_and_stop(self) -> None:
        findings, final = epa.derive_gates(self.prereg, self.observed)
        self.assertEqual({row["gate"]: row["verdict"] for row in findings},
                         {"B1": "FIRES", "B3": "MISSES", "B4": "MISSES"})
        self.assertEqual(final, "STOP_BEFORE_PILOT")

    def test_all_green_inputs_derive_proceed(self) -> None:
        prereg = copy.deepcopy(self.prereg)
        for row in prereg["instrument_map"].values():
            row["checker_external"] = True
        prereg["instrument_map"]["native"]["reader_path"] = (
            "scripts/echo_reparse.py"
        )
        external = {"observed_external": True, "probe_success": True}
        with mock.patch.object(epa, "import_closure",
                               side_effect=lambda path: [path]), \
                mock.patch.object(epa, "checker_probe", return_value=external):
            findings, final = epa.derive_gates(prereg, self.observed)
        self.assertTrue(all(row["verdict"] == "FIRES" for row in findings))
        self.assertEqual(final, "PROCEED_TO_PILOT")

    def test_population_mismatch_is_a_preregistration_discrepancy(self) -> None:
        observed = dict(self.observed)
        observed["native_served"] += 1
        _findings, final = epa.derive_gates(self.prereg, observed)
        self.assertEqual(final, "PREREGISTRATION_DISCREPANCY")

    def test_checker_externality_is_observed_not_only_declared(self) -> None:
        native = epa.checker_probe("scripts/match_signatures.py", None)
        second = epa.checker_probe("scripts/foreign_voice_oracle.py", "1 = 1")
        self.assertFalse(native["observed_external"])
        self.assertTrue(second["observed_external"])
        self.assertTrue(second["probe_success"])


class OrderingAndWriter(unittest.TestCase):
    def test_stopped_audit_records_both_zero_denominators(self) -> None:
        with mock.patch.object(epa, "revalidate", return_value=[]), \
                mock.patch.object(epa, "registration_commit", return_value="a" * 40), \
                mock.patch.object(epa.mr, "measure",
                                  return_value={"served": []}), \
                mock.patch.object(
                    epa, "_load_object", side_effect=[
                        json.loads(epa.PREREG.read_text(encoding="utf-8")),
                        {"b1": {"receipts": []}},
                        {"denominators": {
                            "resolver_found_before_the_proposer_is_consulted": {
                                "question_ids": []
                            }
                        }},
                        {"questions": []},
                    ]), \
                mock.patch.object(epa, "derive_gates",
                                  return_value=([], "STOP_BEFORE_PILOT")):
            result = epa.audit()
        self.assertEqual(result["pilot_registered"], 50)
        self.assertEqual(result["pilot_rendered"], 0)
        self.assertEqual(result["registered_run_registered"], 500)
        self.assertEqual(result["registered_run_rendered"], 0)

    def test_dirty_tree_refuses_before_history_is_consulted(self) -> None:
        dirty = mock.Mock(stdout=" M scripts/echo_reparse.py\n")
        with mock.patch.object(epa.subprocess, "run", return_value=dirty):
            with self.assertRaisesRegex(epa.AuditRefusal, "clean tree"):
                epa.registration_commit()

    def test_registration_inputs_must_share_the_current_commit(self) -> None:
        replies = [
            mock.Mock(stdout=""),
            mock.Mock(stdout="a\n"), mock.Mock(stdout="a\n"),
            mock.Mock(stdout="b\n"),
        ]
        with mock.patch.object(epa.subprocess, "run", side_effect=replies):
            with self.assertRaisesRegex(epa.AuditRefusal, "committed together"):
                epa.registration_commit()

    def test_write_once_creates_but_never_replaces(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "audit.json"
            epa.write_once(target, {"gate": "STOP"})
            before = target.read_bytes()
            with self.assertRaisesRegex(epa.AuditRefusal, "already exists"):
                epa.write_once(target, {"gate": "PROCEED"})
            self.assertEqual(target.read_bytes(), before)

    def test_failed_link_leaves_no_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "audit.json"
            with mock.patch.object(epa.os, "link", side_effect=OSError("plant")):
                with self.assertRaises(OSError):
                    epa.write_once(target, {"gate": "STOP"})
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(scratch).iterdir()), [])

    def test_bare_cli_refuses_before_audit(self) -> None:
        with mock.patch.object(epa, "audit") as audit:
            with self.assertRaises(SystemExit):
                epa.main([])
            audit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
