#!/usr/bin/env python3
"""H-P1's tests: the runner's refusals, and a tamper for every check.

Two programs are under test here and they are tested from opposite ends.

`scripts/run_house_rules_gates.py` is tested through its REFUSALS first. A
registered run that scores whatever tree it is handed is not registered, so
the four things it must refuse — an existing output path, a dirty tree, a
moved seal, a wrong tip — each get a test, and `--allow-dirty` gets one that
holds it to its bargain: it may print a table and it may license nothing.
Only then is the green arm read, and it is read once, from a single scored
run shared by the whole module — `setUpClass` fires per subclass, so hanging
it there would score the corpus once for every class in the file.

`scripts/check_house_rules_receipts.py` is tested through TAMPERS. A checker
that has never been shown going red is a checker nobody has tested, so every
check it performs over the two artifacts has a test that breaks exactly that
check's subject and asserts the named failure comes back. The tampers are
applied to in-memory copies and to files in a temporary directory; nothing
here writes into the repository, which is the same rule the run itself is
scored against.

Three named failures are deliberately not tamper-tested, and the reason is
that they are not properties of the artifacts at all: `replay-refused` (the
runner declined to run), `replay-head` and `replay-digest` (the replay's own
view of the tree disagrees with this checker's). They are conditions of the
machine the replay ran on, reachable only by lying to git or to the
filesystem, and the replay arm exercises the path they live on. The
`receipts-*` half of every dual-labelled check (`{label}-date`,
`{label}-writer-digest`, …) is the same code with the other label, driven by
the `verdicts-*` tests.

Two rules this file follows deliberately:

* **no test asserts a containment by reading a name.** DESIGN §7's B3 forbids
  "test assertions reading the mutant's name", so the B3 arm here drives the
  DETECTOR — a detector that does not fire must produce a survivor — and
  never inspects an output for a string;
* **no admitted symbol name is written into this file.** It sits inside the
  tree B5's disclosure sweep counts, so where a test needs one it derives it
  from the sealed corpus at runtime.
"""

from __future__ import annotations

import contextlib
import copy
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

import check_house_rules_receipts as checker  # noqa: E402
import run_house_rules_gates as gates  # noqa: E402
import symbol_ledger as SL  # noqa: E402

FIXTURES = REPO / gates.FIXTURES
PREREG = REPO / gates.PREREG


@contextlib.contextmanager
def quiet():
    """The checker narrates to stdout; the tests do not need the narration."""

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        yield buffer


def names_of(failures) -> list[str]:
    return [name for name, _ in failures]


def fresh() -> checker.Failures:
    return checker.Failures()


# --------------------------------------------------------------------------
# the refusals, first
# --------------------------------------------------------------------------


class RefusalTests(unittest.TestCase):
    """Four refusals, all of them before any gate is scored."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="house-rules-refusal-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.prereg = json.loads(PREREG.read_text(encoding="utf-8"))

    @contextlib.contextmanager
    def _git_says(
        self,
        *,
        status: str = "",
        head: str = "e" * 40,
        ancestor: bool = True,
        first_commit: str | None = "c" * 40,
    ):
        """Drive `scoring_tree`'s view of git without touching the real tree.

        The pins are NOT faked: `scoring_tree` re-digests every `frozen` row
        against the real files, so the moved-seal arm below is a real digest
        comparison and not a mocked one.
        """

        def fake_git(*args: str) -> str:
            if args and args[0] == "status":
                return status
            if args[:2] == ("rev-parse", "HEAD"):
                return head
            return ""

        with mock.patch.object(gates, "_git", side_effect=fake_git), mock.patch.object(
            gates, "_is_ancestor", return_value=ancestor
        ), mock.patch.object(gates, "_first_commit", return_value=first_commit):
            yield

    def _scoring_tree(self, prereg, allow_dirty=False, **kwargs):
        with self._git_says(**kwargs):
            return gates.scoring_tree(prereg, allow_dirty)

    def test_an_existing_output_path_refuses(self) -> None:
        path = self.tmp / "verdicts.json"
        path.write_text("{}", encoding="utf-8")
        with self.assertRaises(gates.RunRefusal) as caught:
            gates.refuse_existing(path, "verdicts")
        self.assertIn("already exists", str(caught.exception))

    def test_write_once_never_replaces_an_artifact(self) -> None:
        """The structural half of the same refusal: `open(..., 'x')`."""

        path = self.tmp / "receipts.json"
        gates.write_once(path, {"schema": "probe"})
        with self.assertRaises(gates.RunRefusal):
            gates.write_once(path, {"schema": "probe"})
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema"], "probe")

    def test_a_dirty_tree_refuses(self) -> None:
        with self.assertRaises(gates.RunRefusal) as caught:
            self._scoring_tree(self.prereg, status=" M scripts/symbol_ledger.py\n")
        self.assertIn("clean tree", str(caught.exception))

    def test_a_wrong_tip_refuses(self) -> None:
        with self.assertRaises(gates.RunRefusal) as caught:
            self._scoring_tree(self.prereg, ancestor=False)
        self.assertIn("not a strict ancestor", str(caught.exception))

    def test_an_uncommitted_registration_input_refuses(self) -> None:
        with self.assertRaises(gates.RunRefusal) as caught:
            self._scoring_tree(self.prereg, first_commit=None)
        self.assertIn("not committed", str(caught.exception))

    def test_a_moved_seal_refuses(self) -> None:
        moved = copy.deepcopy(self.prereg)
        moved["frozen"][0]["sha256_lf"] = "0" * 64
        with self.assertRaises(gates.RunRefusal) as caught:
            self._scoring_tree(moved)
        self.assertIn("seal moved", str(caught.exception))
        self.assertIn(moved["frozen"][0]["path"], str(caught.exception))

    def test_a_clean_tree_at_the_right_tip_is_registered(self) -> None:
        tree = self._scoring_tree(self.prereg)
        self.assertTrue(tree["registered_before_the_run"])
        self.assertFalse(tree["dirty"])
        self.assertFalse(tree["wrong_tip"])
        self.assertEqual(tree["frozen_pins_that_moved"], [])

    def test_allow_dirty_licenses_nothing_even_on_a_clean_tree(self) -> None:
        """The hatch's whole bargain, asserted rather than trusted."""

        tree = self._scoring_tree(self.prereg, allow_dirty=True)
        self.assertFalse(tree["dirty"])
        self.assertFalse(tree["wrong_tip"])
        self.assertFalse(tree["registered_before_the_run"])
        self.assertEqual(gates.score_b10(self.prereg, tree)["verdict"], "RED")

    def test_the_receipt_checker_is_a_registration_input(self) -> None:
        """The second program is committed before the run, like the first."""

        recorded = self._scoring_tree(self.prereg)["first_commit_of"]
        self.assertIn(gates.RECEIPT_CHECKER, recorded)
        self.assertIn(gates.THIS, recorded)


# --------------------------------------------------------------------------
# one scored run, read by everything below
# --------------------------------------------------------------------------


#: ONE scored run for the whole module. `setUpClass` fires once per SUBCLASS,
#: so hanging the run off it would score the corpus five times over — and each
#: run boots a dozen sessions and shells out to the census checker. The run is
#: read-only to every test below, so one is enough.
_RUN: dict = {}


def scored_run() -> dict:
    if not _RUN:
        tmp = Path(tempfile.mkdtemp(prefix="house-rules-run-"))
        verdicts_path = tmp / "house_rules_verdicts.json"
        receipts_path = tmp / "house_rules_receipts.json"
        verdicts, receipts = gates.run(
            out_path=verdicts_path,
            receipts_path=receipts_path,
            allow_dirty=True,
        )
        gates.write_once(receipts_path, receipts)
        gates.write_once(verdicts_path, verdicts)
        _RUN.update(
            tmp=tmp,
            verdicts_path=verdicts_path,
            receipts_path=receipts_path,
            verdicts=verdicts,
            receipts=receipts,
            prereg=json.loads(PREREG.read_text(encoding="utf-8")),
            fixtures=json.loads(FIXTURES.read_text(encoding="utf-8")),
        )
    return _RUN


def tearDownModule() -> None:
    if _RUN:
        shutil.rmtree(_RUN["tmp"], ignore_errors=True)


class ScoredRunTestCase(unittest.TestCase):
    """One `--allow-dirty` run into a temporary directory, scored once."""

    @classmethod
    def setUpClass(cls) -> None:
        run = scored_run()
        cls.tmp = run["tmp"]
        cls.verdicts_path = run["verdicts_path"]
        cls.receipts_path = run["receipts_path"]
        cls.verdicts = run["verdicts"]
        cls.receipts = run["receipts"]
        cls.prereg = run["prereg"]
        cls.fixtures = run["fixtures"]

    def table(self) -> dict:
        return self.verdicts["construction_gate"]


class GreenArmTests(ScoredRunTestCase):
    """What the rehearsal scores, and what the hatch withholds from it."""

    def test_every_gate_but_b10_is_green_on_the_rehearsal(self) -> None:
        for name in gates.SCORED_GATES:
            row = self.table()[name]
            if name == "B10":
                continue
            self.assertEqual(row["verdict"], "GREEN", f"{name}: {row['misses']}")

    def test_b10_is_red_because_the_hatch_was_used(self) -> None:
        row = self.table()["B10"]
        self.assertEqual(row["verdict"], "RED")
        self.assertIn("registered_before_the_run is false", row["misses"])
        self.assertFalse(self.verdicts["registered_before_the_run"])

    def test_no_sentence_is_licensed_by_a_rehearsal(self) -> None:
        r_h1 = self.verdicts["result_gates"]["R-H1"]
        self.assertFalse(r_h1["green"])
        self.assertIsNone(r_h1["licensed_sentence"])

    def test_b1_scores_against_the_sealed_clause_order(self) -> None:
        """Not against the module's own map, which would compare a value to itself."""

        b1 = self.table()["B1"]
        sealed = sorted(self.fixtures["clause_order"], key=lambda row: row["rank"])
        self.assertEqual(
            tuple((row["clause"], row["refusal_code"]) for row in sealed),
            SL.CLAUSE_ORDER,
        )
        self.assertTrue(b1["shipped_clause_order_equals_the_sealed_order"])
        self.assertEqual(b1["fall_throughs"], 0)
        self.assertEqual(b1["deciding_clauses_outside_the_committed_order"], 0)
        self.assertEqual(
            b1["inputs_scored_total"],
            b1["sweep_inputs_scored"] + b1["fixture_declarations_scored"],
        )

    def test_b1_checks_the_fixtures_where_more_than_one_clause_holds(self) -> None:
        """Those rows are the only ones an order can be wrong about."""

        b1 = self.table()["B1"]
        expected = sorted(
            row["fixture_id"]
            for row in self.fixtures["fixtures"]
            if row.get("also_grounds_for")
        )
        self.assertEqual(b1["multi_ground_fixtures"], expected)
        self.assertEqual(b1["multi_ground_fixtures_off_the_seal"], [])
        self.assertGreater(len(expected), 0)

    def test_the_sweep_mutates_the_command_word_too(self) -> None:
        """The clause says every fixture LINE, not every declaration argument."""

        sweep = self.table()["B1"]["sweep"]
        self.assertTrue(sweep["mutation_covers_the_command_word"])
        alphabet = {
            token
            for row in self.fixtures["fixtures"]
            for token in row["line"].split()
        }
        self.assertEqual(sweep["alphabet_size"], len(alphabet))
        self.assertIn("declare", alphabet)

    def test_b7_meets_its_floor_without_an_authored_input(self) -> None:
        b7 = self.table()["B7"]
        floor = self.prereg["frozen_numbers"]["b7_codes_floor"]
        hit = int(b7["codes_hit_on_the_sweep"].split("/")[0])
        self.assertGreaterEqual(hit, floor)
        self.assertFalse(b7["all_admitted"])
        self.assertFalse(b7["all_unparsed"])
        self.assertEqual(
            sorted(list(b7["per_code_counts"]) + list(b7["hand_only_codes"])),
            sorted(SL.REFUSAL_CODES),
        )

    def test_b3_maps_every_sealed_mutant_and_no_other(self) -> None:
        b3 = self.table()["B3"]
        self.assertTrue(b3["detector_map_covers_the_seal_exactly"])
        self.assertEqual(b3["survivors"], [])
        self.assertGreaterEqual(
            len(b3["rows"]), self.prereg["frozen_numbers"]["b3_mutant_floor"]
        )

    def test_b9_compares_strictly_and_reports_the_equality_case(self) -> None:
        b9 = self.table()["B9"]
        self.assertEqual(
            b9["fired"], b9["out_of_half_agreement"] > b9["void_threshold"]
        )
        self.assertEqual(
            b9["agreement_equals_the_threshold"],
            b9["out_of_half_agreement"] == b9["void_threshold"],
        )
        self.assertTrue(b9["equality_is_not_a_firing"])
        for forbidden in self.prereg["b9_control"]["admitter_inputs_forbidden"]:
            self.assertIn(forbidden, b9["inputs_refused"])

    def test_b5_sweeps_the_output_tree_with_no_carve_out(self) -> None:
        b5 = self.table()["B5"]
        self.assertEqual(b5["documents_containing_an_admitted_name"], 0)
        self.assertEqual(b5["session_documents_or_journals_written"], [])
        # Only the two rows this sweep produces are held out of the document
        # it sweeps; nothing else in the verdicts artifact is exempt.
        self.assertEqual(
            b5["held_out_of_the_swept_document"],
            ["construction_gate.B4", "construction_gate.B5"],
        )
        disclosure = b5["whole_repository_sweep_disclosure"]
        self.assertFalse(disclosure["is_the_gate"])
        self.assertTrue(disclosure["all_hits_existed_before_the_run"])
        self.assertEqual(disclosure["hits"], len(disclosure["paths"]))
        self.assertEqual(disclosure["files_that_could_not_be_read"], [])

    def test_b5_sweeps_the_parts_of_the_document_a_fragment_would_miss(self) -> None:
        """R-H2 quotes hypothesis text verbatim; it must be inside the sweep."""

        names = checker.admitted_names_from_the_seal(self.fixtures)
        text = self.verdicts_path.read_text(encoding="utf-8").casefold()
        self.assertEqual([n for n in names if n.casefold() in text], [])
        for key in ("counts", "result_gates", "non_claims", "provenance"):
            self.assertIn(key, self.verdicts)

    def test_the_receipts_carry_fixture_ids_and_no_symbol_name(self) -> None:
        """The construction rule the prereg registered, checked on the bytes."""

        names = checker.admitted_names_from_the_seal(self.fixtures)
        text = self.receipts_path.read_text(encoding="utf-8").casefold()
        self.assertTrue(self.receipts["carries_no_admitted_symbol_name"])
        self.assertEqual([n for n in names if n.casefold() in text], [])

    def test_r_h2_is_a_reported_arm_with_no_threshold(self) -> None:
        r_h2 = self.verdicts["result_gates"]["R-H2"]
        self.assertIsNone(r_h2["threshold"])
        self.assertTrue(r_h2["gates_nothing"])
        self.assertEqual(r_h2["population_size"], r_h2["population_size_sealed"])
        self.assertIsInstance(r_h2["parse_as_declarations"], int)
        self.assertLessEqual(r_h2["parse_as_declarations"], r_h2["population_size"])


class GatesCanGoRedTests(ScoredRunTestCase):
    """A gate that has never been seen red is a gate nobody has tested."""

    def test_b3_reports_a_survivor_when_a_detector_does_not_fire(self) -> None:
        detectors = copy.deepcopy(self.table()["B3"]["detectors_exercised"])
        target = sorted(detectors)[0]
        detectors[target]["fires"] = False
        row = gates.score_b3(self.prereg, self.fixtures, detectors)
        self.assertEqual(row["verdict"], "RED")
        self.assertTrue(row["survivors"])
        self.assertNotEqual(row["mutants"].split("/")[0], row["mutants"].split("/")[1])

    def test_b8_goes_red_when_the_named_target_is_not_the_whole_set(self) -> None:
        prereg = copy.deepcopy(self.prereg)
        prereg["b8_named_targets"]["schema_category_target_fixtures"] = [
            prereg["b8_named_targets"]["schema_category_target_fixtures"][0]
        ]
        inputs = SL.load_inputs(REPO)
        replay = gates.Replay(self.fixtures, inputs)
        row = gates.score_b8(prereg, self.fixtures, inputs, replay)
        self.assertEqual(row["verdict"], "RED")

    def test_b10_goes_red_on_a_seal_that_moved(self) -> None:
        tree = copy.deepcopy(self.verdicts["scoring_tree"])
        tree["frozen_pins_that_moved"] = ["experiments/house_rules_fixtures.json"]
        self.assertEqual(gates.score_b10(self.prereg, tree)["verdict"], "RED")


# --------------------------------------------------------------------------
# the checker, one tamper per check
# --------------------------------------------------------------------------


class CheckerCleanArmTests(ScoredRunTestCase):
    def test_the_checker_passes_the_untampered_run(self) -> None:
        failures = fresh()
        with quiet():
            checker.check_shape(self.verdicts, self.receipts, self.prereg, failures)
            checker.check_no_clock(self.verdicts, "verdicts", failures)
            checker.check_no_clock(self.receipts, "receipts", failures)
            checker.check_prereg_binding(
                self.verdicts, self.receipts, self.prereg, PREREG, failures
            )
            checker.check_frozen_pins(self.prereg, failures)
            checker.check_provenance(self.verdicts, "verdicts", failures)
            checker.check_ancestry(self.verdicts, self.prereg, failures)
            checker.check_verdict_table(self.verdicts, self.prereg, failures)
            checker.check_result_gates(self.verdicts, self.prereg, failures)
            checker.check_b9(
                self.verdicts, self.receipts, self.prereg, self.fixtures, failures
            )
            checker.check_receipts(
                self.verdicts, self.receipts, self.fixtures, failures
            )
            checker.check_b5_resweep(
                self.verdicts,
                self.receipts,
                self.fixtures,
                self.verdicts_path,
                self.receipts_path,
                failures,
                whole_repository=False,
            )
        self.assertEqual(names_of(failures), [])

    def test_the_whole_repository_disclosure_recomputes(self) -> None:
        """The slow leg: the disclosed count is verified, not asserted."""

        failures = fresh()
        with quiet():
            checker.check_b5_resweep(
                self.verdicts,
                self.receipts,
                self.fixtures,
                self.verdicts_path,
                self.receipts_path,
                failures,
                whole_repository=True,
            )
        self.assertEqual(names_of(failures), [])

    def test_the_checker_reports_a_green_run_as_green(self) -> None:
        """The rehearsal is red at B10; the green path needs its own arm."""

        verdicts = copy.deepcopy(self.verdicts)
        verdicts["registered_before_the_run"] = True
        verdicts["construction_gate"]["B10"]["verdict"] = "GREEN"
        verdicts["construction_gate"]["B10"]["misses"] = []
        verdicts["gate_greens"]["B10"] = True
        verdicts["gate_reds"] = []
        verdicts["result_gates"]["R-H1"]["green"] = True
        verdicts["result_gates"]["R-H1"]["licensed_sentence"] = self.prereg[
            "r_h1_sentence"
        ]
        verdicts["result_gates"]["R-H3"]["licensed"] = False
        verdicts["result_gates"]["R-H3"]["reds_in_scope"] = []
        verdicts["result_gates"]["R-H3"]["reds"] = []
        failures = fresh()
        with quiet():
            checker.check_verdict_table(verdicts, self.prereg, failures)
            checker.check_result_gates(verdicts, self.prereg, failures)
        self.assertEqual(names_of(failures), [])


class CheckerTamperTests(ScoredRunTestCase):
    """Every check, broken on purpose, once."""

    def tamper(self, function, *args, **kwargs) -> list[str]:
        failures = fresh()
        with quiet():
            function(*args, failures, **kwargs)
        return names_of(failures)

    # -- shape, clocks, binding ------------------------------------------

    def test_a_moved_date_is_a_wall_clock_read(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["date"] = "2026-09-30"
        self.assertIn(
            "verdicts-date",
            self.tamper(checker.check_shape, verdicts, self.receipts, self.prereg),
        )

    def test_a_wrong_schema_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        receipts["schema"] = "corollary.something-else/1"
        self.assertIn(
            "receipts-schema",
            self.tamper(checker.check_shape, self.verdicts, receipts, self.prereg),
        )

    def test_a_foreign_preregistration_id_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["preregistration_id"] = "house-rules.h-p1.registered-run.v2"
        self.assertIn(
            "verdicts-prereg-id",
            self.tamper(checker.check_shape, verdicts, self.receipts, self.prereg),
        )

    def test_a_clock_field_at_any_depth_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B4"]["generated_at"] = "2026-09-02T10:00:00Z"
        self.assertIn(
            "record-clock",
            self.tamper(checker.check_no_clock, verdicts, "verdicts"),
        )

    def test_a_forged_prereg_digest_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["preregistration_sha256_lf"] = "0" * 64
        self.assertIn(
            "verdicts-prereg-digest",
            self.tamper(
                checker.check_prereg_binding,
                verdicts,
                self.receipts,
                self.prereg,
                PREREG,
            ),
        )

    def test_a_registration_claim_without_a_commit_fails(self) -> None:
        """`registered_before_the_run` with nothing behind it is the lie."""

        verdicts = copy.deepcopy(self.verdicts)
        verdicts["registered_before_the_run"] = True
        verdicts["registration_commit"] = None
        self.assertIn(
            "verdicts-registration-commit",
            self.tamper(
                checker.check_prereg_binding,
                verdicts,
                self.receipts,
                self.prereg,
                PREREG,
            ),
        )

    def test_an_artifact_with_no_head_commit_fails(self) -> None:
        """Two absences agreeing is not a proof of ancestry."""

        verdicts = copy.deepcopy(self.verdicts)
        verdicts["scoring_tree"]["head_commit"] = None
        verdicts["scoring_tree"]["sealed_commit_is_strict_ancestor_of_head"] = False
        self.assertIn(
            "ancestry-head",
            self.tamper(checker.check_ancestry, verdicts, self.prereg),
        )

    def test_an_artifact_with_no_provenance_inputs_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["provenance"]["inputs"] = []
        self.assertIn(
            "verdicts-provenance",
            self.tamper(checker.check_provenance, verdicts, "verdicts"),
        )

    def test_an_underreported_b5_hit_fails(self) -> None:
        name = checker.admitted_names_from_the_seal(self.fixtures)[0]
        leaked = copy.deepcopy(self.verdicts)
        leaked["construction_gate"]["B5"]["leaked_for_the_test"] = name
        path = self.tmp / "underreported_verdicts.json"
        path.write_text(json.dumps(leaked, indent=2), encoding="utf-8")
        found = self.tamper(
            checker.check_b5_resweep,
            self.verdicts,
            self.receipts,
            self.fixtures,
            path,
            self.receipts_path,
            whole_repository=False,
        )
        self.assertIn("b5-underreported", found)

    def test_a_moved_pin_fails(self) -> None:
        prereg = copy.deepcopy(self.prereg)
        prereg["frozen"][0]["sha256_lf"] = "0" * 64
        self.assertIn("frozen-pin", self.tamper(checker.check_frozen_pins, prereg))

    def test_a_forged_input_digest_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["provenance"]["inputs"][0]["sha256_lf"] = "0" * 64
        self.assertIn(
            "verdicts-input-digest",
            self.tamper(checker.check_provenance, verdicts, "verdicts"),
        )

    def test_a_swapped_second_program_fails(self) -> None:
        """The checker refuses to verify a run pinned to other bytes of it."""

        verdicts = copy.deepcopy(self.verdicts)
        verdicts["provenance"]["second_program"]["sha256_lf"] = "0" * 64
        self.assertIn(
            "verdicts-second-program-digest",
            self.tamper(checker.check_provenance, verdicts, "verdicts"),
        )

    def test_a_forged_writer_digest_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["provenance"]["writer_sha256_lf"] = "0" * 64
        self.assertIn(
            "verdicts-writer-digest",
            self.tamper(checker.check_provenance, verdicts, "verdicts"),
        )

    # -- ancestry ---------------------------------------------------------

    def test_a_substituted_sealed_commit_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["sealed_commit"] = "0" * 40
        self.assertIn(
            "sealed-commit",
            self.tamper(checker.check_ancestry, verdicts, self.prereg),
        )

    def test_an_asserted_ancestry_that_git_denies_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["scoring_tree"]["head_commit"] = verdicts["sealed_commit"]
        self.assertIn(
            "ancestry",
            self.tamper(checker.check_ancestry, verdicts, self.prereg),
        )

    def test_a_rewritten_ancestry_proof_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B10"]["ancestry_proof"] = "trust me -> true"
        self.assertIn(
            "ancestry-proof",
            self.tamper(checker.check_ancestry, verdicts, self.prereg),
        )

    # -- the verdict table ------------------------------------------------

    def test_a_green_verdict_over_a_nonempty_misses_list_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B10"]["verdict"] = "GREEN"
        self.assertIn(
            "gate-verdict",
            self.tamper(checker.check_verdict_table, verdicts, self.prereg),
        )

    def test_a_roll_up_that_disagrees_with_the_table_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["gate_greens"]["B10"] = True
        self.assertIn(
            "gate-greens",
            self.tamper(checker.check_verdict_table, verdicts, self.prereg),
        )

    def test_a_red_dropped_from_gate_reds_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["gate_reds"] = []
        self.assertIn(
            "gate-reds",
            self.tamper(checker.check_verdict_table, verdicts, self.prereg),
        )

    def test_a_clause_softened_after_the_score_fails(self) -> None:
        """The failure mode this check exists for."""

        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B1"]["clause"] = (
            "most inputs receive a verdict"
        )
        self.assertIn(
            "gate-clause",
            self.tamper(checker.check_verdict_table, verdicts, self.prereg),
        )

    # -- the result gates -------------------------------------------------

    def test_a_licensed_r_h1_over_a_red_gate_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H1"]["green"] = True
        self.assertIn(
            "r-h1-green",
            self.tamper(checker.check_result_gates, verdicts, self.prereg),
        )

    def test_a_sentence_licensed_without_a_green_r_h1_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H1"]["licensed_sentence"] = self.prereg[
            "r_h1_sentence"
        ]
        self.assertIn(
            "r-h1-sentence",
            self.tamper(checker.check_result_gates, verdicts, self.prereg),
        )

    def test_a_narrowed_requirement_list_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H1"]["requires"] = ["B1", "B2"]
        self.assertIn(
            "r-h1-requires",
            self.tamper(checker.check_result_gates, verdicts, self.prereg),
        )

    def test_a_withheld_r_h3_licence_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H3"]["licensed"] = False
        self.assertIn(
            "r-h3", self.tamper(checker.check_result_gates, verdicts, self.prereg)
        )

    def test_a_threshold_added_to_the_reported_arm_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H2"]["threshold"] = 0
        self.assertIn(
            "r-h2-threshold",
            self.tamper(checker.check_result_gates, verdicts, self.prereg),
        )

    # -- B9 ---------------------------------------------------------------

    def test_a_restated_agreement_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B9"]["out_of_half_agreement"] = 0.5
        self.assertIn(
            "b9-agreement",
            self.tamper(
                checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
            ),
        )

    def test_a_misreported_firing_fails(self) -> None:
        """The flag and the arithmetic must agree, in either direction."""

        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B9"]["fired"] = True
        self.assertIn(
            "b9-fired",
            self.tamper(
                checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
            ),
        )

    def test_a_loosened_threshold_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B9"]["void_threshold"] = 0.99
        self.assertIn(
            "b9-reported-threshold",
            self.tamper(
                checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
            ),
        )

    def test_a_split_that_is_not_the_registered_rule_fails(self) -> None:
        prereg = copy.deepcopy(self.prereg)
        prereg["b9_control"]["scored_half_fixture_ids"] = list(
            reversed(prereg["b9_control"]["scored_half_fixture_ids"])
        )
        self.assertIn(
            "b9-split",
            self.tamper(
                checker.check_b9, self.verdicts, self.receipts, prereg, self.fixtures
            ),
        )

    def test_a_rewritten_voiding_sentence_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["voiding_sentence"]["text"] = "the capability is fine, actually"
        self.assertIn(
            "b9-voiding-text",
            self.tamper(
                checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
            ),
        )

    # -- the receipt set --------------------------------------------------

    def test_a_dropped_receipt_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        receipts["receipts"] = receipts["receipts"][1:]
        receipts["receipt_count"] = len(receipts["receipts"])
        self.assertIn(
            "missing-receipt",
            self.tamper(checker.check_receipts, self.verdicts, receipts, self.fixtures),
        )

    def test_an_invented_receipt_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        row = copy.deepcopy(receipts["receipts"][0])
        row["fixture_id"] = "hr-fx-s9-t99"
        receipts["receipts"].append(row)
        receipts["receipt_count"] = len(receipts["receipts"])
        self.assertIn(
            "extra-receipt",
            self.tamper(checker.check_receipts, self.verdicts, receipts, self.fixtures),
        )

    def test_a_receipt_off_the_seal_flagged_as_on_it_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        receipts["receipts"][0]["refusal_code"] = "UNPARSED"
        receipts["receipts"][0]["matches_sealed_expectation"] = True
        self.assertIn(
            "receipt-expectation",
            self.tamper(checker.check_receipts, self.verdicts, receipts, self.fixtures),
        )

    def test_a_restated_corpus_count_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["counts"]["admitted"] = 99
        self.assertIn(
            "counts",
            self.tamper(checker.check_receipts, verdicts, self.receipts, self.fixtures),
        )

    # -- B5, on the bytes -------------------------------------------------

    def test_an_admitted_name_in_a_committed_output_fails(self) -> None:
        """The one check the runner cannot perform on itself."""

        name = checker.admitted_names_from_the_seal(self.fixtures)[0]
        leaked = copy.deepcopy(self.verdicts)
        leaked["construction_gate"]["B5"]["leaked_for_the_test"] = name
        path = self.tmp / "leaked_verdicts.json"
        path.write_text(json.dumps(leaked, indent=2), encoding="utf-8")
        self.assertIn(
            "b5-leak",
            self.tamper(
                checker.check_b5_resweep,
                self.verdicts,
                self.receipts,
                self.fixtures,
                path,
                self.receipts_path,
                whole_repository=False,
            ),
        )

    def test_a_restated_disclosure_count_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        disclosure = verdicts["construction_gate"]["B5"][
            "whole_repository_sweep_disclosure"
        ]
        disclosure["hits"] = disclosure["hits"] + 5
        self.assertIn(
            "b5-disclosure-count",
            self.tamper(
                checker.check_b5_resweep,
                verdicts,
                self.receipts,
                self.fixtures,
                self.verdicts_path,
                self.receipts_path,
                whole_repository=True,
            ),
        )

    def test_a_restated_name_count_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B5"]["admitted_symbol_names_swept_for"] = 1
        self.assertIn(
            "b5-name-count",
            self.tamper(
                checker.check_b5_resweep,
                verdicts,
                self.receipts,
                self.fixtures,
                self.verdicts_path,
                self.receipts_path,
                whole_repository=False,
            ),
        )


class CheckerTamperTestsPartTwo(ScoredRunTestCase):
    """The rest of the checker's named failures, one tamper each."""

    tamper = CheckerTamperTests.tamper

    # -- shape ------------------------------------------------------------

    def test_a_wrong_verdicts_schema_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["schema"] = "corollary.not-this/1"
        self.assertIn(
            "verdicts-schema",
            self.tamper(checker.check_shape, verdicts, self.receipts, self.prereg),
        )

    def test_a_wrong_stage_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        receipts["stage"] = "H-P0"
        self.assertIn(
            "receipts-stage",
            self.tamper(checker.check_shape, self.verdicts, receipts, self.prereg),
        )

    def test_a_provenance_input_that_does_not_exist_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["provenance"]["inputs"].append(
            {"path": "experiments/not_a_file.json", "sha256_lf": "0" * 64}
        )
        self.assertIn(
            "verdicts-input-missing",
            self.tamper(checker.check_provenance, verdicts, "verdicts"),
        )

    # -- the table --------------------------------------------------------

    def test_a_missing_gate_row_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        del verdicts["construction_gate"]["B11"]
        found = self.tamper(checker.check_verdict_table, verdicts, self.prereg)
        self.assertIn("gate-missing", found)

    def test_a_gate_row_with_no_misses_list_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B11"]["misses"] = "none"
        self.assertIn(
            "gate-misses",
            self.tamper(checker.check_verdict_table, verdicts, self.prereg),
        )

    def test_a_gate_row_that_is_not_an_object_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B11"] = "GREEN"
        self.assertIn(
            "gate-shape",
            self.tamper(checker.check_verdict_table, verdicts, self.prereg),
        )

    # -- the result gates -------------------------------------------------

    def test_a_widened_r_h3_scope_fails(self) -> None:
        """A red B12 alone does not license the bounded negative."""

        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H3"]["gates_in_scope"] = list(gates.SCORED_GATES)
        self.assertIn(
            "r-h3-scope",
            self.tamper(checker.check_result_gates, verdicts, self.prereg),
        )

    def test_a_restated_in_scope_red_list_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H3"]["reds_in_scope"] = []
        self.assertIn(
            "r-h3-scope",
            self.tamper(checker.check_result_gates, verdicts, self.prereg),
        )

    def test_a_restated_r_h2_population_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H2"]["population_size"] = 3
        self.assertIn(
            "r-h2-population",
            self.tamper(checker.check_result_gates, verdicts, self.prereg),
        )

    def test_an_impossible_r_h2_count_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["result_gates"]["R-H2"]["parse_as_declarations"] = -1
        self.assertIn(
            "r-h2-count",
            self.tamper(checker.check_result_gates, verdicts, self.prereg),
        )

    # -- B9 ---------------------------------------------------------------

    def test_a_moved_anchor_fails(self) -> None:
        prereg = copy.deepcopy(self.prereg)
        prereg["frozen_numbers"]["b9_scored_half_majority_class_rate"] = 0.5
        found = self.tamper(
            checker.check_b9, self.verdicts, self.receipts, prereg, self.fixtures
        )
        self.assertIn("b9-anchor", found)

    def test_a_threshold_that_is_not_anchor_plus_margin_fails(self) -> None:
        prereg = copy.deepcopy(self.prereg)
        prereg["frozen_numbers"]["b9_void_threshold"] = 0.9
        self.assertIn(
            "b9-threshold",
            self.tamper(
                checker.check_b9, self.verdicts, self.receipts, prereg, self.fixtures
            ),
        )

    def test_a_foreign_writer_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["provenance"]["writer"] = "scripts/something_else.py"
        self.assertIn(
            "verdicts-writer",
            self.tamper(checker.check_provenance, verdicts, "verdicts"),
        )

    def test_a_foreign_second_program_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["provenance"]["second_program"]["path"] = "scripts/other_checker.py"
        self.assertIn(
            "verdicts-second-program",
            self.tamper(checker.check_provenance, verdicts, "verdicts"),
        )

    def test_a_restated_fit_accuracy_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B9"]["fit_half_accuracy"] = 0.99
        self.assertIn(
            "b9-fit-accuracy",
            self.tamper(
                checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
            ),
        )

    def test_a_misreported_equality_case_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        b9 = verdicts["construction_gate"]["B9"]
        b9["agreement_equals_the_threshold"] = not b9["agreement_equals_the_threshold"]
        self.assertIn(
            "b9-equality",
            self.tamper(
                checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
            ),
        )

    def test_a_voiding_block_that_disagrees_with_b9_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["voiding_sentence"]["agreement"] = 0.1
        self.assertIn(
            "b9-voiding-block",
            self.tamper(
                checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
            ),
        )

    def test_an_unreadable_fitted_rule_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B9"]["fitted_rule"] = "whatever"
        self.assertIn(
            "b9-rule",
            self.tamper(
                checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
            ),
        )

    def test_receipts_that_do_not_cover_both_halves_fail(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        scored = self.prereg["b9_control"]["scored_half_fixture_ids"][0]
        receipts["receipts"] = [
            row for row in receipts["receipts"] if row["fixture_id"] != scored
        ]
        self.assertIn(
            "b9-truth",
            self.tamper(
                checker.check_b9, self.verdicts, receipts, self.prereg, self.fixtures
            ),
        )

    def test_a_constant_rule_is_re_evaluable(self) -> None:
        """The hypothesis space includes two constants; the checker reads them."""

        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B9"]["fitted_rule"] = "const:REFUSED"
        found = self.tamper(
            checker.check_b9, verdicts, self.receipts, self.prereg, self.fixtures
        )
        self.assertNotIn("b9-rule", found)
        self.assertIn("b9-fit-accuracy", found)

    # -- receipts and the clause order ------------------------------------

    def test_a_duplicated_receipt_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        receipts["receipts"].append(copy.deepcopy(receipts["receipts"][0]))
        receipts["receipt_count"] = len(receipts["receipts"])
        self.assertIn(
            "duplicate-receipt",
            self.tamper(checker.check_receipts, self.verdicts, receipts, self.fixtures),
        )

    def test_a_restated_receipt_count_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        receipts["receipt_count"] = 1
        self.assertIn(
            "receipt-count",
            self.tamper(checker.check_receipts, self.verdicts, receipts, self.fixtures),
        )

    def test_a_verdicts_artifact_citing_the_wrong_receipt_count_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["receipts_artifact"]["receipt_count"] = 1
        self.assertIn(
            "receipt-count-cited",
            self.tamper(checker.check_receipts, verdicts, self.receipts, self.fixtures),
        )

    def test_a_receipt_deciding_off_the_sealed_clause_order_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        row = next(r for r in receipts["receipts"] if r["refusal_code"] != "NONE")
        others = [c for c in SL.CLAUSE_IDS if c != row["deciding_clause"]]
        row["deciding_clause"] = others[0]
        self.assertIn(
            "clause-exclusivity",
            self.tamper(
                checker.check_clause_order, self.verdicts, receipts, self.fixtures
            ),
        )

    def test_a_reordered_seal_fails(self) -> None:
        fixtures = copy.deepcopy(self.fixtures)
        fixtures["clause_order"][0]["rank"] = 99
        self.assertIn(
            "clause-order",
            self.tamper(
                checker.check_clause_order, self.verdicts, self.receipts, fixtures
            ),
        )

    def test_a_dropped_also_holding_ground_fails(self) -> None:
        receipts = copy.deepcopy(self.receipts)
        row = next(r for r in receipts["receipts"] if r["also_grounds_for"])
        row["also_grounds_for"] = []
        self.assertIn(
            "clause-multi-ground",
            self.tamper(
                checker.check_clause_order, self.verdicts, receipts, self.fixtures
            ),
        )

    def test_a_restated_multi_ground_list_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B1"]["multi_ground_fixtures"] = []
        self.assertIn(
            "clause-multi-ground",
            self.tamper(
                checker.check_clause_order, verdicts, self.receipts, self.fixtures
            ),
        )

    # -- B5's disclosure --------------------------------------------------

    def test_a_restated_disclosure_path_list_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        disclosure = verdicts["construction_gate"]["B5"][
            "whole_repository_sweep_disclosure"
        ]
        disclosure["paths"] = disclosure["paths"][:-1] + ["docs/not-a-file.md"]
        self.assertIn(
            "b5-disclosure-paths",
            self.tamper(
                checker.check_b5_resweep,
                verdicts,
                self.receipts,
                self.fixtures,
                self.verdicts_path,
                self.receipts_path,
                whole_repository=True,
            ),
        )

    def test_a_hit_that_did_not_pre_exist_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        disclosure = verdicts["construction_gate"]["B5"][
            "whole_repository_sweep_disclosure"
        ]
        disclosure["all_hits_existed_before_the_run"] = False
        disclosure["hits_that_did_not_exist_before_the_run"] = ["reports/new.json"]
        self.assertIn(
            "b5-disclosure-pre-existing",
            self.tamper(
                checker.check_b5_resweep,
                verdicts,
                self.receipts,
                self.fixtures,
                self.verdicts_path,
                self.receipts_path,
                whole_repository=True,
            ),
        )

    def test_a_restated_unreadable_list_fails(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B5"]["whole_repository_sweep_disclosure"][
            "files_that_could_not_be_read"
        ] = ["scripts/locked.py"]
        self.assertIn(
            "b5-unreadable",
            self.tamper(
                checker.check_b5_resweep,
                verdicts,
                self.receipts,
                self.fixtures,
                self.verdicts_path,
                self.receipts_path,
                whole_repository=True,
            ),
        )


class ReplayTests(ScoredRunTestCase):
    """The byte-identity arm, and the mask that may not swallow a difference."""

    def test_json_diff_finds_every_leaf_that_moved(self) -> None:
        left = {"a": {"b": 1, "c": 2}, "d": [1, 2]}
        right = {"a": {"b": 9, "c": 2}, "d": [1, 3]}
        diffs = checker.json_diff(left, right)
        self.assertEqual(sorted(diffs), [("a", "b"), ("d", 1)])
        self.assertEqual(checker.json_diff(left, copy.deepcopy(left)), [])

    def test_the_real_mask_names_only_tree_facts_and_no_gate_row(self) -> None:
        """A mask wide enough to swallow a gate would make the replay empty."""

        for path in checker.TIP_DEPENDENT:
            self.assertGreaterEqual(len(path), 2, path)
            # Nothing in the mask may cover a whole gate row or the table.
            self.assertNotEqual(path, ("construction_gate",))
            if path[0] == "construction_gate":
                self.assertGreaterEqual(len(path), 3, path)
        masked_gates = {
            path[1] for path in checker.TIP_DEPENDENT if path[0] == "construction_gate"
        }
        # Only B10 (which is the tree) and B4's two digest strings may move.
        self.assertEqual(masked_gates, {"B10", "B4"})
        for name in gates.SCORED_GATES:
            covered = any(
                path[:2] == ("construction_gate", name) and len(path) == 2
                for path in checker.TIP_DEPENDENT
            )
            self.assertFalse(covered, name)

    def test_the_rehearsal_mask_is_the_only_wider_one_and_says_so(self) -> None:
        self.assertIn(("construction_gate", "B10"), checker.DIRTY_DEPENDENT)
        self.assertNotIn(("construction_gate", "B10"), checker.TIP_DEPENDENT)
        for path in checker.DIRTY_DEPENDENT:
            self.assertNotEqual(path[:1], ("counts",))

    def test_a_replay_reproduces_the_run(self) -> None:
        failures = fresh()
        with quiet():
            checker.check_replay(
                self.verdicts, self.receipts, failures, allow_dirty=True
            )
        self.assertEqual(names_of(failures), [])

    def test_a_replay_catches_a_field_outside_the_mask(self) -> None:
        verdicts = copy.deepcopy(self.verdicts)
        verdicts["construction_gate"]["B7"]["per_code_counts"]["UNPARSED"] = 1
        receipts = copy.deepcopy(self.receipts)
        receipts["receipts"][0]["grounds_count"] = 99
        failures = fresh()
        with quiet():
            checker.check_replay(verdicts, receipts, failures, allow_dirty=True)
        found = names_of(failures)
        self.assertIn("replay-bytes", found)
        self.assertIn("replay-receipts", found)


if __name__ == "__main__":
    unittest.main()
