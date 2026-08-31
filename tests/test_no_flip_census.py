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

import no_flip_census as nfc  # noqa: E402


class RegisteredPopulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = nfc.load_object(nfc.PREREG)

    def test_frozen_population_recounts_exactly(self) -> None:
        paths = nfc.journal_paths()
        observed = nfc.population(paths)
        self.assertEqual(observed, self.prereg["population"])
        self.assertEqual(observed["answering_total"], 220)
        self.assertEqual(observed["excluded_total"], 190)

    def test_reads_sidecars_are_not_journals(self) -> None:
        self.assertEqual(len(nfc.journal_paths()), 60)
        self.assertFalse(any(path.name.endswith(".reads.json")
                             for path in nfc.journal_paths()))

    def test_every_frozen_group_revalidates(self) -> None:
        rows = nfc.revalidate(self.prereg)
        # A group either still agrees with its original digest or carries a
        # dated retirement naming a recorded amendment; anything else raised
        # inside revalidate. An un-retired group must still agree exactly.
        self.assertTrue(
            all(row["agrees"] or row.get("retired") for row in rows)
        )
        for row in rows:
            if row.get("retired"):
                self.assertIn("retired_by", row)
        journals = next(row for row in rows
                        if row["group"] == "journal_population")
        self.assertEqual(len(journals["members"]), 60)

    def test_population_drift_refuses(self) -> None:
        observed = copy.deepcopy(self.prereg["population"])
        observed["answering_total"] += 1
        with self.assertRaisesRegex(nfc.CensusRefusal,
                                    "PREREGISTRATION_DISCREPANCY"):
            nfc.require_population(self.prereg, observed)


class ComparatorAndControls(unittest.TestCase):
    def test_primary_comparator_is_only_digest_inequality(self) -> None:
        a = "a" * 64
        b = "b" * 64
        self.assertFalse(nfc.digest_changed(a, a))
        self.assertTrue(nfc.digest_changed(a, b))
        with self.assertRaises(nfc.CensusRefusal):
            nfc.digest_changed("not-a-digest", b)

    def test_mutations_preserve_rows_and_only_move_them(self) -> None:
        source = {
            "route": "twin",
            "status": "found",
            "detail": "same",
            "answer": (
                "member     : a",
                "member     : b",
                "ledger     : reports/signature_matches.json",
            ),
        }
        mutated = nfc.plant_verdicts(source)
        self.assertEqual(
            list(mutated["MEMBER_ORDER"]["answer"]),
            ["member     : b", "member     : a",
             "ledger     : reports/signature_matches.json"],
        )
        self.assertEqual(
            list(mutated["LEDGER_POSITION"]["answer"]),
            ["ledger     : reports/signature_matches.json",
             "member     : a", "member     : b"],
        )

    def test_extra_prefix_rows_are_preserved(self) -> None:
        """The live twin answer prefixes a `level` row; plants must not drop it."""
        source = {
            "route": "twin",
            "status": "found",
            "answer": (
                "level      : typed",
                "member     : a",
                "member     : b",
                "ledger     : reports/signature_matches.json",
            ),
        }
        mutated = nfc.plant_verdicts(source)
        self.assertEqual(
            list(mutated["MEMBER_ORDER"]["answer"]),
            ["level      : typed", "member     : b", "member     : a",
             "ledger     : reports/signature_matches.json"],
        )
        self.assertEqual(
            list(mutated["LEDGER_POSITION"]["answer"]),
            ["level      : typed", "ledger     : reports/signature_matches.json",
             "member     : a", "member     : b"],
        )

    def test_invalid_plant_shape_refuses(self) -> None:
        source = {
            "route": "twin", "status": "found",
            "answer": ("member     : a", "ledger     : x"),
        }
        with self.assertRaisesRegex(nfc.CensusRefusal, "INVALID_PLANT"):
            nfc.plant_verdicts(source)

    def test_live_controls_have_registered_behavior(self) -> None:
        observed = nfc.controls(ROOT, 220)
        self.assertEqual(observed["exact_detected"], 2)
        self.assertEqual(observed["shape_only_detected"], 0)
        self.assertEqual(observed["always_changed_detected"], 2)
        self.assertEqual(
            observed["always_changed_false_positives_on_identical_self_pairs"],
            220,
        )


class Accounting(unittest.TestCase):
    @staticmethod
    def row(classification: str) -> dict:
        return {
            "session_id": "s", "turn_index": 0, "input_bytes": "x",
            "recorded_kind": "solved", "recorded_digest": "a" * 64,
            "live_digest": "b" * 64, "live_route": "exact",
            "live_status": "solved", "classification": classification,
        }

    def test_three_classes_partition_the_denominator(self) -> None:
        rows = [self.row("DIGEST_MATCH"), self.row("DIGEST_MISMATCH"),
                self.row("ANSWER_LOST")]
        result = nfc.validate_accounting(rows, 3)
        self.assertEqual(result["regression_candidates"], 2)
        self.assertEqual(len(result["red_rows"]), 2)

    def test_missing_red_field_refuses(self) -> None:
        row = self.row("DIGEST_MISMATCH")
        del row["live_route"]
        with self.assertRaisesRegex(nfc.CensusRefusal, "INVALID_ACCOUNTING"):
            nfc.validate_accounting([row], 1)

    def test_missing_receipt_refuses(self) -> None:
        with self.assertRaisesRegex(nfc.CensusRefusal, "INVALID_ACCOUNTING"):
            nfc.validate_accounting([], 1)


class OrderingAndWriter(unittest.TestCase):
    def test_dirty_tree_refuses_before_history(self) -> None:
        dirty = mock.Mock(stdout=" M scripts/no_flip_census.py\n")
        with mock.patch.object(nfc.subprocess, "run", return_value=dirty):
            with self.assertRaisesRegex(nfc.CensusRefusal, "clean tree"):
                nfc.registration_commit()

    def test_registration_inputs_must_share_current_commit(self) -> None:
        replies = [mock.Mock(stdout="")]
        replies.extend(mock.Mock(stdout="a\n") for _ in nfc.REGISTRATION_PATHS)
        replies[-1] = mock.Mock(stdout="b\n")
        with mock.patch.object(nfc.subprocess, "run", side_effect=replies):
            with self.assertRaisesRegex(nfc.CensusRefusal, "committed together"):
                nfc.registration_commit()

    def test_write_once_never_replaces(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "result.json"
            nfc.write_once(target, {"outcome": 0})
            before = target.read_bytes()
            with self.assertRaisesRegex(nfc.CensusRefusal, "already exists"):
                nfc.write_once(target, {"outcome": 1})
            self.assertEqual(target.read_bytes(), before)

    def test_failed_link_leaves_no_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "result.json"
            with mock.patch.object(nfc.os, "link", side_effect=OSError("plant")):
                with self.assertRaises(OSError):
                    nfc.write_once(target, {"outcome": 0})
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(scratch).iterdir()), [])

    def test_bare_cli_refuses_before_census(self) -> None:
        with mock.patch.object(nfc, "census") as census:
            with self.assertRaises(SystemExit):
                nfc.main([])
            census.assert_not_called()


class ReplayServesExcludedTurns(unittest.TestCase):
    def test_waiting_turns_are_served_even_though_they_are_not_scored(self) -> None:
        journal = {
            "header": {"session_id": "s", "pins": {}},
            "assumptions": [],
            "turns": [
                {
                    "turn_index": 0,
                    "input_bytes": "suppose x",
                    "result": {
                        "kind": "waiting",
                        "answer_bytes_digest": "a" * 64,
                    },
                },
                {
                    "turn_index": 1,
                    "input_bytes": "2 + 3",
                    "result": {
                        "kind": "solved",
                        "answer_bytes_digest": "b" * 64,
                    },
                },
            ],
        }
        served: list[str] = []

        class DummySession:
            resolver_index = None
            assumptions = None

        class DummyAssumptions:
            def advance(self, _index):
                return None

        class DummyBarrier:
            def open_turn(self, _index):
                return None

            def close_turn(self):
                return None

        def fake_route(_root, _session, line):
            served.append(line)
            if line == "2 + 3":
                return {"status": "solved", "route": "evaluate", "answer": ("5",)}
            return {"status": "waiting", "route": "suppose", "answer": ()}

        prereg = nfc.load_object(nfc.PREREG)
        with mock.patch.object(nfc, "load_object", return_value=journal), \
             mock.patch.object(nfc.CoreSession, "boot", return_value=DummySession()), \
             mock.patch.object(nfc.ledger, "ReadBarrier", return_value=DummyBarrier()), \
             mock.patch.object(nfc.replay_session, "_rebuild_assumptions",
                               return_value=DummyAssumptions()), \
             mock.patch.object(nfc, "route_line", fake_route), \
             mock.patch.object(nfc.ledger, "answer_bytes_digest",
                               return_value="b" * 64), \
             mock.patch("resolver.build_index", return_value={}):
            rows = nfc.replay_answering(nfc.ROOT, [Path("fake.json")], prereg)
        self.assertEqual(served, ["suppose x", "2 + 3"])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["input_bytes"], "2 + 3")
        self.assertEqual(rows[0]["classification"], "DIGEST_MATCH")


if __name__ == "__main__":
    unittest.main()
