"""Tests for the address-space probe (ROADMAP-v0.19 item 2).

Five things have to be true for the probe's verdict to mean anything, and
all five are checkable rather than assertable:

1. the preregistration entered the tree in a commit strictly BEFORE the
   script and before the result, read out of git rather than out of prose;
2. the script imports engine machinery only from the two lists the prereg
   declares, checked by parsing this file's AST rather than by reading it;
3. the run is deterministic and the committed artifact regenerates
   byte-identically;
4. the verdict rule can go RED -- a channel that refuses everything scores
   a perfect false-positive number and must still read NOT BEATEN, which is
   the exact laundering the prereg's both-legs rule exists to refuse;
5. nothing in the artifact is a wall-clock reading, an absolute path, or a
   rate without the population it was computed over.

The two subprocess runs cost about eighty seconds between them. They are
here rather than in a manual step because "the committed numbers are what
the script produces" is the only sentence the whole artifact rests on.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from git_ordering import assert_added_before  # noqa: E402

PREREG = ROOT / "experiments" / "address_space_probe_prereg.json"
REPORT = ROOT / "experiments" / "address_space_probe.json"
SCRIPT = ROOT / "scripts" / "probe_address_space.py"

PREREG_PATH = "experiments/address_space_probe_prereg.json"
REPORT_PATH = "experiments/address_space_probe.json"
SCRIPT_PATH = "scripts/probe_address_space.py"

#: Every module in scripts/ that the probe is allowed to import. The prereg
#: names two; anything else is an engine surface this instrument may not
#: reach into, and the AST test below is what makes that a fact.
ALLOWED_MODULES = {"measure_block_mdl", "resolver"}

_RUNS: list[bytes] = []


def two_runs() -> list[bytes]:
    """Run the probe twice into throwaway paths. Cached for the module."""
    if _RUNS:
        return _RUNS
    with tempfile.TemporaryDirectory() as td:
        for name in ("a.json", "b.json"):
            out = Path(td) / name
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--write-report", str(out)],
                cwd=str(ROOT), capture_output=True, text=True,
            )
            if proc.returncode != 0:
                raise AssertionError(proc.stderr[-3000:])
            _RUNS.append(out.read_bytes())
    return _RUNS


def report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


class OrderingTests(unittest.TestCase):
    """The prereg is only a prereg if git says it came first."""

    def test_prereg_was_added_before_the_measurement_script(self):
        assert_added_before(
            self, PREREG_PATH, SCRIPT_PATH,
            "a baseline registered after the instrument that scores it is a "
            "baseline chosen to be beatable",
        )

    def test_prereg_was_added_before_the_result(self):
        assert_added_before(
            self, PREREG_PATH, REPORT_PATH,
            "ROADMAP-v0.19 item 2 requires the baselines pre-registered "
            "before any measurement",
        )

    def test_the_report_pins_the_prereg_it_was_adjudicated_against(self):
        digest = hashlib.sha256(
            PREREG.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        self.assertEqual(
            report()["prereg"]["sha256_lf"], digest,
            "the artifact quotes a prereg digest that is not the committed "
            "prereg; either the prereg moved after the run or the run is stale",
        )


class ImportDisciplineTests(unittest.TestCase):
    """No engine imports outside the declared comparison arms."""

    def _imports(self) -> dict[str, set[str]]:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        found: dict[str, set[str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                module = (node.module or "").split(".")[0]
                if (ROOT / "scripts" / f"{module}.py").exists():
                    found.setdefault(module, set()).update(
                        a.name for a in node.names
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if (ROOT / "scripts" / f"{module}.py").exists():
                        found.setdefault(module, set()).add("*module*")
        return found

    def test_only_the_two_declared_modules_are_imported(self):
        modules = set(self._imports())
        self.assertEqual(
            modules, ALLOWED_MODULES,
            f"probe_address_space.py imports {sorted(modules)}; the prereg "
            f"declares {sorted(ALLOWED_MODULES)} and nothing else. An "
            "instrument that reaches into answer.py, harness.py, "
            "controller.py or dispatcher.py is no longer measuring the "
            "engine from outside it.",
        )

    def test_the_imported_names_are_the_names_the_prereg_declared(self):
        declared = json.loads(PREREG.read_text(encoding="utf-8"))[
            "the_one_consumer"]["declared_comparison_arm_imports"]
        found = self._imports()
        self.assertEqual(
            found.get("resolver", set()),
            set(declared["from_scripts_resolver"]),
            "the comparison arm imports names the prereg did not declare",
        )
        self.assertEqual(
            found.get("measure_block_mdl", set()),
            set(declared["from_scripts_measure_block_mdl"]),
            "the dictionary dependency imports names the prereg did not "
            "declare",
        )

    def test_no_learned_component_and_no_network(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for banned in ("torch", "sklearn", "numpy.random", "requests",
                       "urllib.request", "socket"):
            self.assertNotIn(
                f"import {banned}", text,
                f"{banned} has no business in a closed-form probe",
            )


class DeterminismTests(unittest.TestCase):
    def test_two_runs_are_byte_identical(self):
        first, second = two_runs()
        self.assertEqual(
            first, second,
            "two runs of the probe disagree; something in the report reads a "
            "clock, a set iteration order, or the filesystem's order",
        )

    def test_the_committed_report_regenerates_byte_identically(self):
        self.assertTrue(REPORT.exists(), f"missing {REPORT}")
        self.assertEqual(
            two_runs()[0], REPORT.read_bytes().replace(b"\r\n", b"\n"),
            "experiments/address_space_probe.json is stale; regenerate it "
            "with scripts/probe_address_space.py --write-report",
        )

    def test_the_dictionary_rebuild_is_the_object_block_mdl_measured(self):
        check = report()["arm_B_compression"]["rebuild_check"]
        self.assertTrue(
            check["identical"],
            "the probe rebuilt a dictionary that is not the one "
            "experiments/block_mdl.json measured; every number downstream "
            "would then be about a different object",
        )
        self.assertEqual(check["rebuilt_rules"], check["committed_rules"])
        self.assertEqual(
            check["rebuilt_total_bits"], check["committed_total_bits"]
        )


class VerdictTests(unittest.TestCase):
    def test_every_baseline_carries_one_of_exactly_two_words(self):
        verdict = report()["verdict"]
        for key in ("A_retrieval", "B_compression", "C_term_layer"):
            self.assertIn(
                verdict[key]["verdict"], {"BEATEN", "NOT BEATEN"},
                f"{key} has a third verdict word; the roadmap allows two",
            )
            self.assertIn("the_number", verdict[key])

    def test_a_channel_that_refuses_everything_is_not_a_win(self):
        """The both-legs rule, exercised rather than quoted.

        Zero coverage and a perfect false-positive number is what a dead
        channel scores, and it is the single easiest way to launder one into
        a headline. The verdict function must call it NOT BEATEN.
        """
        from probe_address_space import verdict as adjudicate

        doctored = copy.deepcopy(report())
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        for key, arm in doctored["arm_A_retrieval"].items():
            if not key.startswith("block_channel_"):
                continue
            arm["pooled_coverage"]["rate"] = 0.0
            arm["pooled_coverage"]["reached"] = 0
            arm["pooled_claim_on_refuse_rows"]["rate"] = 0.0
            arm["pooled_claim_on_refuse_rows"]["claimed"] = 0
        got = adjudicate(doctored, prereg)
        self.assertEqual(got["A_retrieval"]["verdict"], "NOT BEATEN")
        self.assertEqual(got["A_retrieval"]["fp_leg"], "MET")
        self.assertEqual(got["A_retrieval"]["coverage_leg"], "MISSED")

    def test_the_verdict_can_go_green_when_the_numbers_say_so(self):
        """A test that only ever goes one way is not a test.

        Hand the same function a channel that clears both floors and it must
        say BEATEN, or the NOT BEATEN above is unfalsifiable.
        """
        from probe_address_space import verdict as adjudicate

        doctored = copy.deepcopy(report())
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        for key, arm in doctored["arm_A_retrieval"].items():
            if not key.startswith("block_channel_"):
                continue
            arm["pooled_coverage"]["rate"] = 0.95
            arm["pooled_claim_on_refuse_rows"]["rate"] = 0.01
        got = adjudicate(doctored, prereg)
        self.assertEqual(got["A_retrieval"]["verdict"], "BEATEN")

    def test_the_no_ceiling_diagnostic_never_wins_an_arm(self):
        """The degenerate reading is published and is not adjudicated.

        Dropping the document-frequency ceiling lets `of a` -- a block on
        14,570 of 14,830 nodes -- reach every query, so coverage climbs and
        means nothing. It is in the artifact so a reader can see it; it may
        not be the arm a verdict is read off.
        """
        verdict = report()["verdict"]
        self.assertNotIn("no_ceiling", verdict["A_retrieval"]["best_block_arm"])
        arms = report()["arm_A_retrieval"]
        self.assertTrue(
            any(k.endswith("_no_ceiling") for k in arms),
            "the diagnostic is missing; it is what makes the ceiling's role "
            "visible",
        )

    def test_the_single_question_is_answered_against_the_tag_bit_arm(self):
        """Beating grep is not evidence for unification, and the artifact
        must not be readable as if it were."""
        question = report()["verdict"]["the_single_question"]
        self.assertIn("ratio_vs_two_indexes_with_a_tag_bit", question)
        self.assertGreater(question["ratio_vs_grep"], 100)
        answer = question["answer"]
        beats_tag = question["unified_beats_two_indexes_with_one_tag_bit"]
        self.assertEqual(
            answer.startswith("ONE OBJECT"), beats_tag == "YES",
            "the answer disagrees with the measurement it is supposed to be "
            "read off",
        )


class ArtifactHygieneTests(unittest.TestCase):
    def test_no_wall_clock_no_absolute_paths(self):
        text = REPORT.read_text(encoding="utf-8")
        for banned in ("C:\\", "/Users/", "seconds", "elapsed", "timestamp"):
            self.assertNotIn(banned, text)

    def test_every_pooled_rate_names_its_population(self):
        arms = report()["arm_A_retrieval"]
        for key, arm in arms.items():
            if not isinstance(arm, dict) or "pooled_coverage" not in arm:
                continue
            self.assertIn(
                "populations", arm["pooled_coverage"],
                f"{key} reports a pooled rate with no population; "
                "DESIGN-block-vocabulary 3d correction 3 forbids it",
            )
            self.assertIn("populations", arm["pooled_claim_on_refuse_rows"])

    def test_the_unreproducible_population_is_labelled_not_a_rate(self):
        state = report()["wordnet_archive"]
        self.assertFalse(state["reproducible"])
        arms = report()["arm_A_retrieval"]
        claimed = arms["keyword_channel_same_run"]["per_population"][
            "P-FP-CLAIMED"]["refuse"]
        self.assertIn("not_a_rate", claimed)

    def test_blocks_are_multi_word(self):
        for label, entry in report()["dictionaries"].items():
            self.assertEqual(
                entry["blocks_that_are_one_word"], 0,
                f"{label} minted a one-word block; a one-word key is the "
                "keyword channel wearing a different id",
            )

    def test_the_cliff_is_flagged_where_it_fired(self):
        """DESIGN 3d correction 1: where the fixed-width code chose the rule
        count, the artifact has to say so rather than report the number as
        the data's."""
        dictionaries = report()["dictionaries"]
        self.assertTrue(dictionaries["folded_model_a"]["at_power_of_two_cliff"])
        self.assertFalse(dictionaries["cased_model_a"]["at_power_of_two_cliff"])


class ExpectationTests(unittest.TestCase):
    def test_every_registered_expectation_is_adjudicated(self):
        got = report()["registered_expectations"]
        for name in ("E1", "E2", "E3", "E4"):
            self.assertIn(name, got)
            self.assertIn("fired", got[name])
            self.assertIn("measured", got[name])


if __name__ == "__main__":
    unittest.main()
