"""The gates runner end to end, plus the two red arms that prove it can fail.

`docs/DESIGN-protocol-uptake.md` §7 lists ten construction gates and §9 makes
R-U1 conditional on nine of them. A runner that reports green on the sealed
fixtures says nothing until the same runner is shown reporting red when
something is actually wrong, so this module runs both:

* the **green arm** — the whole registered pass on the sealed fixtures, into a
  temporary directory, in `--allow-dirty` mode. Every scored gate must be
  GREEN and B7 must be `PENDING_AMD3`: not green, not red, not invented from
  the text WAITING fallback;
* two **red arms** — a tampered receipts artifact must make B10 fail (both a
  dropped record and an added one, because §7's B10 fails on missing *and*
  extra), and a runtime whose selected moves are the lexical trigger's must
  make B4 fire.

`--allow-dirty` is the pre-run testing hatch. It never changes a verdict; it
sets `registered_before_the_run: false`, which withholds every §9 sentence —
these tests assert that too, so the hatch cannot quietly license a claim.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import check_protocol_receipts as replay_checker  # noqa: E402
import protocol_controls as controls  # noqa: E402
import protocol_runtime as runtime  # noqa: E402
import run_protocol_gates as gates  # noqa: E402

FIXTURES = REPO / "experiments" / "protocol_uptake_fixtures.json"


class GateRunTestCase(unittest.TestCase):
    """One registered pass, scored once, read by every test below."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="protocol-gates-"))
        cls.run_path = cls.tmp / "protocol_uptake_run.json"
        cls.receipts_path = cls.tmp / "protocol_uptake_receipts.json"
        cls.payload = gates.run(
            out_path=cls.run_path,
            receipts_path=cls.receipts_path,
            fixtures_path=FIXTURES,
            allow_dirty=True,
        )
        gates.write_once(cls.run_path, cls.payload)
        cls.receipts = json.loads(cls.receipts_path.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)


class GreenArmTests(GateRunTestCase):
    def test_every_scored_gate_is_green(self) -> None:
        for name in gates.SCORED_GATES:
            row = self.payload["construction_gate"][name]
            self.assertEqual(row["verdict"], "GREEN", f"{name}: {row.get('misses')}")
        self.assertEqual(self.payload["gate_reds"], [])

    def test_b7_is_read_from_its_instrument_and_never_fabricated(self) -> None:
        """B7 is reported, not scored — and reported from what measured it.

        AMD-3 (2026-08-31) gave the field one source: the artifact
        `scripts/run_b7_roundtrip.py` writes after the orchestrator's live
        Codex round trip. Until that artifact exists the verdict stays
        `PENDING_AMD3` — not green, not red, and not invented from the text
        WAITING fallback. Once it exists the verdict is the recorded one, and
        this runner still computes nothing: that is what the two arms below
        assert, so the test cannot go red for the system working.
        """

        b7 = self.payload["construction_gate"]["B7"]
        recorded = REPO / gates.B7_ARTIFACT
        if recorded.exists():
            artifact = json.loads(recorded.read_text(encoding="utf-8"))
            self.assertEqual(b7["verdict"], artifact["verdict"])
            self.assertEqual(b7["green"], artifact["verdict"] == "GREEN")
            self.assertEqual(b7["recorded_in"], gates.B7_ARTIFACT)
            # Nothing licenses B7 green from the text fallback: a green
            # verdict must carry the live host's log.
            if b7["green"]:
                self.assertTrue(b7["live_codex_log"])
                self.assertTrue(b7["self_check_passed"])
        else:
            self.assertEqual(b7["verdict"], "PENDING_AMD3")
            self.assertFalse(b7["green"])
            self.assertFalse(self.payload["gate_greens"]["B7"])
        self.assertEqual(self.payload["gates_pending"], ["B7"])
        self.assertFalse(self.payload["result_gates"]["R-U2"]["green"])
        self.assertIsNone(self.payload["result_gates"]["R-U2"]["licensed_sentence"])

    def test_b1_recomputes_the_frozen_numbers(self) -> None:
        b1 = self.payload["construction_gate"]["B1"]
        self.assertEqual(b1["regeneration_checker_exit"], 0)
        self.assertEqual(
            b1["recomputed_from_the_sealed_table"],
            {"c_surface": 21, "c_position": 21, "position_switch_agreement": 17},
        )

    def test_b2_reproduces_all_thirty_two_cells(self) -> None:
        b2 = self.payload["construction_gate"]["B2"]
        self.assertEqual(b2["cells_matching_the_sealed_table"], 32)
        self.assertEqual(b2["of"], 32)
        self.assertGreaterEqual(len(b2["surfaces_taking_two_different_selected_moves"]), 2)

    def test_b3_scores_eight_refusals_and_four_asks(self) -> None:
        b3 = self.payload["construction_gate"]["B3"]
        self.assertEqual(b3["refusals"], "8/8")
        self.assertEqual(b3["asks"], "4/4")
        self.assertTrue(b3["authority_delta_is_a_plaintext_field"])

    def test_b4_matches_the_ceilings_with_equality_and_does_not_fire(self) -> None:
        arms = self.payload["construction_gate"]["B4"]["refit_on_the_runtimes_selected_moves"]
        self.assertFalse(arms["fired"])
        self.assertEqual(arms["arms"]["surface_only_refit"]["agreement"], 21)
        self.assertEqual(arms["arms"]["position_only_refit"]["agreement"], 21)
        self.assertEqual(arms["arms"]["position_switch"]["agreement"], 17)
        for arm in arms["arms"].values():
            self.assertTrue(arm["equality_is_not_a_firing"])

    def test_b5_replays_every_trajectory_three_times(self) -> None:
        b5 = self.payload["construction_gate"]["B5"]
        self.assertEqual(b5["trajectories"], "8/8")
        for row in b5["rows"]:
            self.assertEqual(row["arrival_order_replays"], 3)
            self.assertTrue(row["replays_byte_identical"])
            self.assertTrue(row["episode_marks_reproduced"])
        self.assertEqual(b5["stale_reply"]["disposition"], "REFUSED")
        self.assertTrue(b5["stale_reply"]["stack_unchanged"])
        self.assertEqual(b5["depth_nine_plant"]["episodes_at_refusal"], 8)
        self.assertTrue(b5["depth_nine_plant"]["stack_unchanged"])

    def test_b6_pauses_on_ambiguity_and_proceeds_on_equivalence(self) -> None:
        b6 = self.payload["construction_gate"]["B6"]
        self.assertEqual(b6["ask_fixtures_waiting"], 4)
        self.assertEqual(b6["of_ask_fixtures"], 4)
        self.assertEqual(len(b6["equivalence_rows"]), 2)
        for row in b6["equivalence_rows"]:
            self.assertEqual(row["disposition"], "ENTER")
            self.assertEqual(row["selected_move_id"], min(row["candidate_move_ids"]))
            self.assertTrue(row["grouping_recorded_in_the_receipt"])
            self.assertEqual(len(row["derived_equivalence_partition"]), 1)

    def test_b8_opens_nothing_and_starts_no_process(self) -> None:
        b8 = self.payload["construction_gate"]["B8"]
        self.assertEqual(b8["disposition"], "REFUSED")
        self.assertEqual(b8["authority_delta"], [])
        self.assertEqual(b8["process_starts"], 0)
        self.assertTrue(b8["zero_data_tree_byte_changes"])
        self.assertEqual(b8["stage_records"], 0)

    def test_b9_fires_all_seven_sealed_mutants(self) -> None:
        b9 = self.payload["construction_gate"]["B9"]
        self.assertEqual(b9["mutants"], "7/7 fired")
        for row in b9["rows"]:
            self.assertTrue(row["fired"], row["mutant_id"])
            self.assertTrue(row["fired_by"])

    def test_b10_replays_the_receipts_artifact(self) -> None:
        b10 = self.payload["construction_gate"]["B10"]
        self.assertEqual(b10["checker_exit"], 0)

    def test_the_voiding_sentence_did_not_fire(self) -> None:
        self.assertFalse(self.payload["voiding_sentence"]["fired"])
        self.assertIn("void", self.payload["voiding_sentence"]["text"])

    def test_allow_dirty_withholds_every_result_sentence(self) -> None:
        self.assertFalse(self.payload["registered_before_the_run"])
        self.assertTrue(self.payload["scoring_tree"]["allow_dirty"])
        self.assertFalse(self.payload["result_gates"]["R-U1"]["green"])
        self.assertIsNone(self.payload["result_gates"]["R-U1"]["licensed_sentence"])

    def test_the_non_claims_are_copied_from_the_prereg(self) -> None:
        prereg = json.loads(
            (REPO / gates.PREREG).read_text(encoding="utf-8")
        )
        self.assertEqual(self.payload["non_claims"], prereg["non_claims"])
        self.assertEqual(
            self.payload["preregistration_sha256"], gates.sha256_lf(REPO / gates.PREREG)
        )
        self.assertEqual(
            self.payload["registration_commit"],
            self.payload["scoring_tree"]["first_commit_of"][gates.PREREG],
        )


class ArtifactTests(GateRunTestCase):
    def test_raw_receipts_land_before_compact_metrics(self) -> None:
        """§12's ordering, as a fact about the writer rather than a promise."""

        self.assertTrue(self.receipts_path.exists())
        self.assertEqual(self.receipts["receipt_count"], len(self.receipts["receipts"]))
        self.assertEqual(
            self.receipts["receipt_count"],
            self.payload["receipts_artifact"]["receipt_count"],
        )
        self.assertEqual(
            self.receipts["receipt_count"],
            len(runtime.replay_registered_pass(json.loads(FIXTURES.read_text(encoding="utf-8")))),
        )

    def test_every_raw_receipt_carries_its_own_digest(self) -> None:
        for record in self.receipts["receipts"]:
            self.assertEqual(record["uptake_id"], runtime.recompute_uptake_id(record))

    def test_an_existing_output_path_is_refused(self) -> None:
        with self.assertRaises(gates.RunRefusal):
            gates.run(
                out_path=self.run_path,
                receipts_path=self.tmp / "other-receipts.json",
                fixtures_path=FIXTURES,
                allow_dirty=True,
            )
        with self.assertRaises(gates.RunRefusal):
            gates.run(
                out_path=self.tmp / "other-run.json",
                receipts_path=self.receipts_path,
                fixtures_path=FIXTURES,
                allow_dirty=True,
            )

    def test_a_dirty_tree_is_refused_without_the_hatch(self) -> None:
        with mock.patch.object(
            gates, "_git", side_effect=lambda *args: "?? scripts/scratch.py" if args[0] == "status" else "x" * 40
        ):
            with self.assertRaises(gates.RunRefusal):
                gates.scoring_tree(allow_dirty=False)
            tree = gates.scoring_tree(allow_dirty=True)
        self.assertTrue(tree["dirty"])
        self.assertFalse(tree["registered_before_the_run"])


class RedArmTests(GateRunTestCase):
    """The gates can fail. Both arms are run, not described."""

    def check(self, receipts_path: Path) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = replay_checker.main(
                ["--fixtures", str(FIXTURES), "--receipts", str(receipts_path)]
            )
        return code, buffer.getvalue()

    def test_the_untampered_artifact_passes_b10(self) -> None:
        code, output = self.check(self.receipts_path)
        self.assertEqual(code, 0, output)
        self.assertIn("set equality OK", output)

    def test_a_dropped_receipt_fails_b10(self) -> None:
        """DESIGN §10 stops the slice on a checker that cannot detect an omission."""

        tampered = dict(self.receipts)
        tampered["receipts"] = self.receipts["receipts"][:-1]
        path = self.tmp / "dropped.json"
        path.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
        code, output = self.check(path)
        self.assertEqual(code, 1)
        self.assertIn("missing-record", output)

    def test_an_added_receipt_fails_b10(self) -> None:
        tampered = dict(self.receipts)
        extra = json.loads(json.dumps(self.receipts["receipts"][0]))
        extra["session_id"] = "sess-not-in-the-pass"
        extra["uptake_id"] = runtime.recompute_uptake_id(extra)
        tampered["receipts"] = self.receipts["receipts"] + [extra]
        path = self.tmp / "added.json"
        path.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
        code, output = self.check(path)
        self.assertEqual(code, 1)
        self.assertIn("extra-record", output)

    def test_an_edited_receipt_fails_b10(self) -> None:
        tampered = json.loads(json.dumps(self.receipts))
        tampered["receipts"][0]["disposition"] = "CONTINUE"
        path = self.tmp / "edited.json"
        path.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
        code, output = self.check(path)
        self.assertEqual(code, 1)
        self.assertIn("uptake-id", output)

    def test_a_lexical_trigger_runtime_makes_b4_fire(self) -> None:
        """Patch the runtime's selected moves into the trigger and re-score B4."""

        fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
        prereg = json.loads((REPO / gates.PREREG).read_text(encoding="utf-8"))
        scored = gates.Pass(fixtures, runtime.load_corpus())
        honest = gates.score_b4(scored, prereg)
        self.assertEqual(honest["verdict"], "GREEN")

        with mock.patch.object(
            gates.Pass,
            "product_grid",
            lambda self: controls.lexical_trigger_runtime(
                controls.sealed_labels(self.fixtures)
            ),
        ):
            leaked = gates.score_b4(scored, prereg)
        self.assertEqual(leaked["verdict"], "RED")
        evaluation = leaked["refit_on_the_runtimes_selected_moves"]
        self.assertTrue(evaluation["fired"])
        self.assertIn("surface_only_refit", evaluation["fired_arms"])
        self.assertEqual(evaluation["arms"]["surface_only_refit"]["agreement"], 32)

    def test_a_position_switch_runtime_makes_b4_fire(self) -> None:
        fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
        prereg = json.loads((REPO / gates.PREREG).read_text(encoding="utf-8"))
        scored = gates.Pass(fixtures, runtime.load_corpus())
        with mock.patch.object(
            gates.Pass,
            "product_grid",
            lambda self: controls.position_switch_runtime(
                controls.sealed_labels(self.fixtures), controls.position_ids(self.fixtures)
            ),
        ):
            leaked = gates.score_b4(scored, prereg)
        self.assertEqual(leaked["verdict"], "RED")
        self.assertIn(
            "position_switch",
            leaked["refit_on_the_runtimes_selected_moves"]["fired_arms"],
        )


if __name__ == "__main__":
    unittest.main()
