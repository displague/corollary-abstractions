"""PROTOCOL UPTAKE — guards for U-P0's source and fixture seal.

``docs/DESIGN-protocol-uptake.md`` §6 step 2 makes the builder, its generated
corpus, the dedicated regeneration checker, and the generated fixtures the
construction prerequisite of the whole slice, and §7's B1 makes them the
source-truth gate. These tests score the properties that make the seal a seal
rather than a pile of committed JSON:

* the two generated artifacts are what the builder emits, byte for byte;
* the two view-ceilings and the position-switch control's table-agreement
  **recompute** from the committed sealed table to the numbers the prereg
  freezes — B1: "a mismatch is a construction bug, not a leak";
* the check can go red, exercised on perturbed copies, because a check that
  survives a corrupted table is freezing nothing; and
* the nine structural invariants U-P0 seals, each recomputed here rather than
  trusted from the artifact that asserts it.

Nothing here executes a protocol runtime. ``scripts/protocol_runtime.py`` is
registered as not existing yet.
"""

from __future__ import annotations

import hashlib
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

import build_protocol_corpus as builder  # noqa: E402
import check_protocol_regeneration as checker  # noqa: E402
from prereg_pins import sha256_lf  # noqa: E402

BUILDER = REPO / "scripts" / "build_protocol_corpus.py"
CORPUS = REPO / "protocol" / "protocols.json"
FIXTURES = REPO / "experiments" / "protocol_uptake_fixtures.json"
PREREG = REPO / "experiments" / "protocol_uptake_prereg.json"
UPRE = REPO / "experiments" / "protocol_uptake_upre.json"

REFUSED = "REFUSED"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _copy(document: dict) -> dict:
    return json.loads(json.dumps(document))


def _regenerate(role: str, tmpdir: Path) -> bytes:
    """Run the committed builder into a tempdir. Never into the repository."""

    out = tmpdir / f"{role}.json"
    flag = "--out" if role == "corpus" else "--fixtures"
    run = subprocess.run(
        [sys.executable, str(BUILDER), flag, str(out)],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"),
    )
    if run.returncode != 0:
        raise AssertionError(f"builder failed: {(run.stderr or run.stdout)[-500:]}")
    return out.read_bytes()


class TheGeneratedArtifactsRegenerate(unittest.TestCase):
    """(a) The committed files are the builder's output, byte for byte."""

    def test_the_corpus_matches_a_fresh_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(CORPUS.read_bytes(), _regenerate("corpus", Path(tmp)))

    def test_the_fixtures_match_a_fresh_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(FIXTURES.read_bytes(), _regenerate("fixtures", Path(tmp)))

    def test_the_builder_is_byte_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = _regenerate("corpus", Path(tmp) / "a")
            second = _regenerate("corpus", Path(tmp) / "b")
        self.assertEqual(first, second)

    def test_the_generated_files_are_lf_with_a_trailing_newline(self) -> None:
        for path in (CORPUS, FIXTURES, PREREG):
            with self.subTest(path=path.name):
                raw = path.read_bytes()
                self.assertNotIn(b"\r\n", raw)
                self.assertTrue(raw.endswith(b"\n"))

    def test_the_corpus_is_outside_the_data_tree(self) -> None:
        # DESIGN §3: under data/*/nodes.json it would silently join the boot
        # corpus count, the merged resolver graph, and every census over it.
        self.assertEqual(CORPUS.relative_to(REPO).parts[0], "protocol")
        self.assertFalse((REPO / "data" / "protocols.json").exists())


class TheCeilingsRecompute(unittest.TestCase):
    """(b) The frozen numbers recompute from the committed sealed table."""

    def setUp(self) -> None:
        self.fixtures = _load(FIXTURES)
        self.prereg = _load(PREREG)

    def test_c_surface_recomputes_to_the_frozen_number(self) -> None:
        self.assertEqual(
            checker.recompute_c_surface(self.fixtures),
            self.prereg["frozen_numbers"]["c_surface"],
        )

    def test_c_position_recomputes_to_the_frozen_number(self) -> None:
        self.assertEqual(
            checker.recompute_c_position(self.fixtures),
            self.prereg["frozen_numbers"]["c_position"],
        )

    def test_the_position_switch_agreement_recomputes(self) -> None:
        self.assertEqual(
            checker.recompute_position_switch_agreement(self.fixtures),
            self.prereg["frozen_numbers"]["position_switch_agreement"],
        )

    def test_the_fixtures_own_numbers_agree_with_the_prereg(self) -> None:
        frozen = self.prereg["frozen_numbers"]
        self.assertEqual(self.fixtures["ceilings"]["c_surface"], frozen["c_surface"])
        self.assertEqual(self.fixtures["ceilings"]["c_position"], frozen["c_position"])
        self.assertEqual(
            self.fixtures["position_switch_control"]["frozen_table_agreement"],
            frozen["position_switch_agreement"],
        )

    def test_the_prereg_pins_the_committed_files(self) -> None:
        for row in self.prereg["frozen"]:
            with self.subTest(role=row["role"]):
                self.assertEqual(sha256_lf(REPO / row["path"]), row["sha256_lf"])


class TheCheckCanGoRed(unittest.TestCase):
    """(c) The mutation arm. A check that survives a corrupted seal freezes nothing."""

    def setUp(self) -> None:
        self.corpus = _load(CORPUS)
        self.fixtures = _load(FIXTURES)
        self.prereg = _load(PREREG)

    def test_a_byte_edit_of_a_generated_file_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fresh = _regenerate("corpus", Path(tmp))
        tampered = CORPUS.read_bytes().replace(b"protocol.greeting.a", b"protocol.greeting.z", 1)
        self.assertNotEqual(tampered, CORPUS.read_bytes())
        self.assertNotEqual(tampered, fresh)

    def test_a_flipped_table_cell_moves_the_ceilings(self) -> None:
        mutated = _copy(self.fixtures)
        # "good morning" at fresh_root is greeting; call it REFUSED instead.
        cell = mutated["sealed_table"][1]["cells"][0]
        self.assertEqual(cell["label"], "greeting")
        cell["label"] = REFUSED
        failures = checker.Failures()
        checker.check_numbers(self.prereg, mutated, failures)
        self.assertTrue(failures, "a flipped sealed-table cell must fail the recomputation")
        self.assertIn("number-c_surface", [name for name, _ in failures])

    def test_a_broken_equivalence_digest_fires_invariant_h(self) -> None:
        mutated = _copy(self.fixtures)
        fixture = next(f for f in mutated["fixtures"] if f["kind"] == "equivalence")
        fixture["turns"][0]["candidates"][1]["next_state_sha256"] = "0" * 64
        failures = checker.Failures()
        checker.check_invariants(self.corpus, mutated, failures)
        self.assertIn("invariant-h", [name for name, _ in failures])

    def test_a_loosened_entry_predicate_fires_invariant_c(self) -> None:
        mutated = _copy(self.corpus)
        node = next(n for n in mutated["nodes"] if n["protocol_id"] == "protocol.probe_reply.a")
        move = next(m for m in node["moves"] if m["move_id"] == "confirm_alive")
        # Drop the probe requirement: probe_reply's entry now also holds at fresh_root.
        move["required_signal_predicates"] = [
            {"signal_id": "pending_need", "required_value": "ABSENT"}
        ]
        failures = checker.Failures()
        checker.check_invariants(mutated, self.fixtures, failures)
        self.assertIn("invariant-c", [name for name, _ in failures])

    def test_a_second_node_per_family_fires_invariant_a(self) -> None:
        mutated = _copy(self.corpus)
        mutated["lookup"]["hello"].append(
            {
                "protocol_node_id": "protocol.greeting.b",
                "relation": "greeting",
                "move_id": "acknowledge",
                "move_kind": "entry",
            }
        )
        failures = checker.Failures()
        checker.check_invariants(mutated, self.fixtures, failures)
        self.assertIn("invariant-a", [name for name, _ in failures])

    def test_an_ask_fixture_that_does_not_wait_fires_invariant_f(self) -> None:
        mutated = _copy(self.fixtures)
        ask = next(f for f in mutated["fixtures"] if f["kind"] == "ask")
        ask["expected_state"] = "ANSWERED"
        failures = checker.Failures()
        checker.check_invariants(self.corpus, mutated, failures)
        self.assertIn("invariant-f-waiting", [name for name, _ in failures])

    def test_a_deeper_nested_fixture_fires_invariant_g(self) -> None:
        mutated = _copy(self.fixtures)
        nested = next(f for f in mutated["fixtures"] if f["kind"] == "nested")
        nested["turns"][0]["expected_depth_after"] = 3
        failures = checker.Failures()
        checker.check_invariants(self.corpus, mutated, failures)
        self.assertIn("invariant-g", [name for name, _ in failures])

    def test_a_ceiling_at_the_degeneracy_bound_is_a_construction_refusal(self) -> None:
        mutated = _copy(self.fixtures)
        mutated["ceilings"]["c_surface"] = 24
        failures = checker.Failures()
        checker.check_invariants(self.corpus, mutated, failures)
        self.assertIn("invariant-e", [name for name, _ in failures])

    def test_a_deleted_field_reappearing_fires_invariant_i(self) -> None:
        # The builder's own positive survivor check is the same guard from the
        # other side: a signal id outside U-PRE's survivors is refused.
        with self.assertRaises(builder.ConstructionRefusal):
            builder.check_survivor_schema(
                {"context_signals": [{"signal_id": "a_field_no_audit_kept", "value": "x"}]},
                where="test",
            )

    def test_the_committed_checker_exits_zero_today(self) -> None:
        run = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "check_protocol_regeneration.py")],
            cwd=REPO,
            capture_output=True,
            text=True,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"),
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


class TheStructuralInvariants(unittest.TestCase):
    """(d) Each invariant U-P0 seals, recomputed here rather than trusted."""

    def setUp(self) -> None:
        self.corpus = _load(CORPUS)
        self.fixtures = _load(FIXTURES)
        self.prereg = _load(PREREG)

    def _entry_witnesses(self, surface: str) -> list[dict]:
        return [w for w in self.corpus["lookup"].get(surface, ()) if w["move_kind"] == "entry"]

    def test_a_each_product_surface_matches_at_most_one_node_per_family(self) -> None:
        for surface in self.fixtures["product_surfaces"]:
            per_family: dict[str, set[str]] = {}
            for witness in self._entry_witnesses(surface):
                per_family.setdefault(witness["relation"], set()).add(
                    witness["protocol_node_id"]
                )
            for family, node_ids in per_family.items():
                with self.subTest(surface=surface, family=family):
                    self.assertEqual(len(node_ids), 1)

    def test_b_ask_and_equivalence_keys_are_disjoint_from_the_product(self) -> None:
        products = set(self.fixtures["product_surfaces"])
        extras = {row["surface"] for row in self.fixtures["ask_surfaces"]} | {
            row["surface"] for row in self.fixtures["equivalence_surfaces"]
        }
        self.assertEqual(products & extras, set())
        self.assertEqual(len(products), 8)
        self.assertEqual(len(extras), 6)

    def test_c_entry_predicates_are_pairwise_exclusive_on_the_four_positions(self) -> None:
        preds = {
            family: checker.family_entry_predicate(self.corpus, family)
            for family in self.corpus["families"]
        }
        for position in self.fixtures["positions"]:
            signals = dict(position["signals"])
            signals["protocol_stack"] = "empty"
            holding = [f for f, p in preds.items() if checker.predicate_holds(p, signals)]
            with self.subTest(position=position["position_id"]):
                self.assertLessEqual(len(holding), 1)

    def test_d_at_least_two_surfaces_take_two_different_selected_moves(self) -> None:
        switching = [
            row["surface"]
            for row in self.fixtures["sealed_table"]
            if len(
                {
                    (cell["protocol_id"], cell["move_id"])
                    for cell in row["cells"]
                    if cell["label"] != REFUSED
                }
            )
            >= 2
        ]
        self.assertGreaterEqual(len(switching), 2)
        self.assertEqual(
            switching, self.fixtures["surfaces_taking_two_different_selected_moves"]
        )

    def test_e_both_ceilings_are_below_the_two_degeneracy_bounds(self) -> None:
        for name, value in self.fixtures["ceilings"].items():
            with self.subTest(ceiling=name):
                self.assertLess(value, 32, "a 32/32 view is a sufficient statistic")
                self.assertLess(value, 24, "24/32 is the exclusive-home separability")

    def test_f_four_ask_fixtures_all_stop_waiting(self) -> None:
        asks = [f for f in self.fixtures["fixtures"] if f["kind"] == "ask"]
        self.assertGreaterEqual(len(asks), 2)
        self.assertEqual(len(asks), 4)
        for fixture in asks:
            with self.subTest(fixture=fixture["fixture_id"]):
                self.assertEqual(fixture["expected_disposition"], "ASK")
                self.assertEqual(fixture["expected_state"], "WAITING")
                self.assertGreaterEqual(len(fixture["expected_unresolved_move_ids"]), 2)
                self.assertGreaterEqual(
                    len(fixture["expected_distinct_next_state_sha256"]), 2
                )
                self.assertTrue(fixture["expected_need"]["minted"])
                self.assertEqual(fixture["expected_authority_delta"], [])
                self.assertFalse(fixture["expected_stack_mutation"])

    def test_g_the_deepest_nested_fixture_depth_is_two(self) -> None:
        nested = [f for f in self.fixtures["fixtures"] if f["kind"] == "nested"]
        self.assertEqual(len(nested), 8)
        depths = [max(t["expected_depth_after"] for t in f["turns"]) for f in nested]
        self.assertEqual(max(depths), 2)
        # The cap is four times that deepest, declared and not measured.
        self.assertEqual(self.corpus["stack_depth_cap"], 8)

    def test_h_the_equivalence_pair_projections_coincide(self) -> None:
        equivalences = [f for f in self.fixtures["fixtures"] if f["kind"] == "equivalence"]
        self.assertEqual(len(equivalences), 2)
        for fixture in equivalences:
            with self.subTest(fixture=fixture["fixture_id"]):
                candidates = fixture["turns"][0]["candidates"]
                self.assertEqual(len(candidates), 2)
                digests = set()
                for candidate in candidates:
                    projection = builder.next_state_projection(
                        candidate["protocol_id"], candidate["next_state"]["stack_after"]
                    )
                    self.assertEqual(
                        sorted(projection), sorted(self.prereg["next_state_projection"])
                    )
                    digests.add(builder.sha256_canonical(projection))
                    self.assertEqual(candidate["next_state_sha256"], builder.sha256_canonical(projection))
                self.assertEqual(len(digests), 1)
                self.assertEqual(fixture["expected_shared_next_state_sha256"], digests.pop())
                move_ids = sorted(c["move_id"] for c in candidates)
                self.assertEqual(fixture["expected_move_id"], min(move_ids))
                self.assertTrue(fixture["expected_proceeds_without_asking"])
                self.assertTrue(fixture["expected_equivalence_recorded"])

    def test_h_move_id_is_outside_the_projection(self) -> None:
        # If it were inside, two names could never certify as one transition and
        # DESIGN §4's equivalence rule would be dead code.
        self.assertNotIn("move_id", self.prereg["next_state_projection"])
        self.assertEqual(
            self.prereg["next_state_projection"],
            ["protocol_id", "stack_after", "pending_request_id", "authority_delta"],
        )

    def test_i_the_fields_the_audit_deleted_appear_nowhere(self) -> None:
        deleted = checker.deleted_at_upre()
        self.assertEqual(len(deleted), 2)
        for path in (CORPUS, FIXTURES, PREREG, BUILDER, REPO / "scripts" / "check_protocol_regeneration.py", Path(__file__)):
            text = path.read_text(encoding="utf-8")
            for name in deleted:
                with self.subTest(path=path.name, field=name):
                    self.assertNotIn(name, text)

    def test_i_the_survivor_lists_are_the_audits(self) -> None:
        survivors = checker.surviving_at_upre()
        self.assertEqual(
            self.prereg["surviving_context_signal_ids"], survivors["context_signals"]
        )
        self.assertEqual(
            self.prereg["surviving_protocol_witness_fields"],
            survivors["protocol_witness_fields"],
        )
        self.assertEqual(self.corpus["context_signal_ids"], survivors["context_signals"])


class TheSeal(unittest.TestCase):
    """What U-P0 is obliged to have sealed, counted rather than described."""

    def setUp(self) -> None:
        self.fixtures = _load(FIXTURES)
        self.prereg = _load(PREREG)

    def test_the_fixture_counts_are_the_designs(self) -> None:
        self.assertEqual(
            self.fixtures["counts"],
            {
                "product": 32,
                "refusal": 8,
                "ask": 4,
                "equivalence": 2,
                "nested": 8,
                "depth_cap_plant": 1,
                "authority_plant": 1,
                "b9_mutants": 7,
                "total_fixtures": 56,
            },
        )
        self.assertEqual(self.prereg["fixture_counts"], self.fixtures["counts"])

    def test_every_product_cell_has_a_fixture_and_matches_the_table(self) -> None:
        by_id = {f["fixture_id"]: f for f in self.fixtures["fixtures"]}
        for row in self.fixtures["sealed_table"]:
            for cell in row["cells"]:
                fixture_id = f"ctx-{row['row']}-{cell['col']}"
                with self.subTest(fixture=fixture_id):
                    fixture = by_id[fixture_id]
                    self.assertEqual(fixture["surface"], row["surface"])
                    self.assertEqual(fixture["position_id"], cell["position_id"])
                    if cell["label"] == REFUSED:
                        self.assertEqual(fixture["expected_disposition"], REFUSED)
                        self.assertIsNone(fixture["expected_protocol_id"])
                    else:
                        self.assertEqual(fixture["expected_disposition"], "ENTER")
                        self.assertEqual(fixture["expected_family"], cell["label"])
                        self.assertEqual(fixture["expected_protocol_id"], cell["protocol_id"])
                        self.assertEqual(fixture["expected_move_id"], cell["move_id"])

    def test_the_eight_refusal_fixtures_are_two_per_position(self) -> None:
        refusals = [f for f in self.fixtures["fixtures"] if f["kind"] == "refusal"]
        self.assertEqual(len(refusals), 8)
        seen = Counter((f["position_id"], f["corruption"]) for f in refusals)
        self.assertEqual(set(seen.values()), {1})
        self.assertEqual(len({p for p, _ in seen}), 4)
        for fixture in refusals:
            with self.subTest(fixture=fixture["fixture_id"]):
                self.assertEqual(fixture["expected_disposition"], REFUSED)
                self.assertFalse(fixture["expected_stack_mutation"])
                self.assertEqual(fixture["expected_authority_delta"], [])
                self.assertEqual(fixture["turns"][0]["candidates"], [])

    def test_the_depth_cap_plant_fills_the_cap_and_is_refused(self) -> None:
        plant = next(f for f in self.fixtures["fixtures"] if f["kind"] == "depth_cap_plant")
        self.assertEqual(plant["fixture_id"], "depth9-plant")
        self.assertEqual(len(plant["turns"]), 9)
        self.assertEqual(plant["turns"][-1]["expected_disposition"], REFUSED)
        self.assertEqual(
            plant["turns"][-1]["expected_stack_after_ids"],
            plant["turns"][-1]["stack_before_ids"],
        )
        self.assertEqual(len(plant["turns"][-1]["expected_stack_after_ids"]), 8)
        self.assertFalse(plant["is_one_of_the_eight_nested_fixtures"])
        self.assertFalse(plant["raises_the_cap"])

    def test_the_b8_plant_is_unwitnessed_and_opens_nothing(self) -> None:
        plant = next(f for f in self.fixtures["fixtures"] if f["kind"] == "authority_plant")
        self.assertEqual(plant["expected_disposition"], REFUSED)
        self.assertEqual(plant["expected_authority_delta"], [])
        self.assertEqual(plant["turns"][0]["protocol_witnesses"], [])
        corpus = _load(CORPUS)
        self.assertNotIn(plant["surface"], corpus["lookup"])

    def test_the_seven_b9_mutants_name_existing_fixtures(self) -> None:
        by_id = {f["fixture_id"]: f for f in self.fixtures["fixtures"]}
        survivors = checker.surviving_at_upre()
        mutants = self.fixtures["b9_mutants"]
        self.assertEqual(len(mutants), survivors["count"])
        self.assertEqual(mutants, self.prereg["b9_mutants"])
        fields = [m["field"].split(".")[-1].replace("[]", "") for m in mutants]
        self.assertEqual(
            sorted(fields),
            sorted(survivors["context_signals"] + survivors["protocol_witness_fields"]),
        )
        for mutant in mutants:
            with self.subTest(mutant=mutant["mutant_id"]):
                self.assertIn(mutant["target_fixture"], by_id)
                self.assertTrue(mutant["expected_effect"])

    def test_the_prereg_registers_the_runtime_module_that_does_not_exist_yet(self) -> None:
        self.assertEqual(self.prereg["runtime_module"], "scripts/protocol_runtime.py")
        self.assertTrue(
            any("protocol_runtime" in row for row in self.prereg["registered_before"])
        )

    def test_the_prereg_is_a_registered_u_p0_manifest(self) -> None:
        self.assertEqual(self.prereg["status"], "REGISTERED")
        self.assertEqual(self.prereg["schema"], "corollary.protocol-uptake-prereg/1")
        self.assertEqual(self.prereg["registered_date"], "2026-08-31")
        self.assertEqual(self.prereg["design"], "docs/DESIGN-protocol-uptake.md")
        self.assertEqual(self.prereg["roadmap"], "docs/ROADMAP-v0.24.md#1")
        self.assertEqual(sorted(self.prereg["gates"]), sorted(f"B{i}" for i in range(1, 11)))
        self.assertGreaterEqual(len(self.prereg["non_claims"]), 6)

    def test_the_episode_ids_follow_the_sealed_rule(self) -> None:
        for fixture in self.fixtures["fixtures"]:
            for turn in fixture["turns"]:
                for episode in turn.get("expected_stack_after", []):
                    if not isinstance(episode, dict):
                        continue
                    with self.subTest(fixture=fixture["fixture_id"], episode=episode["episode_id"]):
                        self.assertTrue(
                            episode["episode_id"].endswith(f"-{episode['protocol_id']}")
                        )
                        self.assertTrue(episode["episode_id"].startswith("ep-"))

    def test_every_next_state_digest_is_the_canonical_four_field_sha256(self) -> None:
        checked = 0
        for fixture in self.fixtures["fixtures"]:
            for turn in fixture["turns"]:
                for candidate in turn.get("candidates", []):
                    expected = hashlib.sha256(
                        json.dumps(
                            candidate["next_state"],
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                        ).encode("utf-8")
                    ).hexdigest()
                    self.assertEqual(candidate["next_state_sha256"], expected)
                    self.assertEqual(
                        sorted(candidate["next_state"]),
                        sorted(self.prereg["next_state_projection"]),
                    )
                    checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
