#!/usr/bin/env python3
"""The C-E3 supplementary adjudicator: substitution, refusal, and the artifact.

`docs/ROADMAP-v0.21.md` §2's named early rider. The registered run's C-E3
handed the checker an OPEN term and recorded the elaboration failure as
`decide did not reduce in either direction`. The repair is a substitution
step, and the substitution step is the whole thing worth testing: a wrong
substitution produces a checker verdict about a statement nobody measured,
and it would read exactly like a real result.

**The capture fixture is the one that matters.** `x1 + x >= x1 * x` under
`{"x": "2", "x1": "3"}` is not an exotic shape — this corpus is full of
`x`, `x1`, `x2` — and a textual rewrite of `x` to `2` turns `x1` into `21`.
That is not a substitution failure a reader would notice in the artifact: the
proposition would still be closed, still decide, and still be wrong.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import conform  # noqa: E402
import conform_census as census  # noqa: E402
import conformance_ce3_supplement as sup  # noqa: E402

ARTIFACT = ROOT / sup.ARTIFACT

#: The domain every row of the registered run's sampled counterexample class
#: declares, and the only one this writer presents.
NAT = ("Nat", "truncating", "truncated-at-zero")


def _closed(text: str, bindings: dict[str, str]):
    return sup.substitute(census.parse(text), bindings)


def _value(tree, side: int):
    return conform.eval_under_domain(tree[2][side], {}, *NAT)


class SubstitutionIsStructuralNotTextual(unittest.TestCase):
    """Three hand-built fixtures, and the third is the one with teeth."""

    def test_a_plain_binding_lands_at_the_slot(self) -> None:
        """Fixture 1: truncated subtraction, where the carrier does the work."""
        closed = _closed("a - b >= 0", {"a": "1", "b": "4"})
        self.assertEqual(sup.free_slots(closed), set())
        # `1 - 4` is 0 over Nat, not -3, and the substituted tree must be read
        # under the DECLARED subtraction rather than under the reader's.
        self.assertEqual(_value(closed, 0), 0)
        self.assertEqual(
            sup.render_proposition(closed, *NAT),
            "((((1) - (4)) : Nat) >= (0 : Nat))",
        )

    def test_a_binding_under_a_truncating_division(self) -> None:
        """Fixture 2: `1/x` at x=3 is 0, and the rendering says so."""
        closed = _closed("1/x >= 2", {"x": "3"})
        self.assertEqual(_value(closed, 0), 0)
        self.assertEqual(
            sup.render_proposition(closed, *NAT),
            "((((1) / (3)) : Nat) >= (2 : Nat))",
        )

    def test_a_prefix_named_variable_is_not_captured(self) -> None:
        """Fixture 3: NAIVE STRING SUBSTITUTION WOULD CAPTURE `x1`.

        This is the fixture the whole rider turns on. The record's binding map
        is applied against the statement's `slot` nodes — the names
        `conform.py` binds — so `x1` keeps its own binding and `x` keeps its
        own. A textual rewrite would produce `21 + 2 >= 21 * 2`, a closed
        proposition that decides cleanly and answers a question nobody asked.
        """

        text = "x1 + x >= x1 * x"
        bindings = {"x": "2", "x1": "3"}
        closed = _closed(text, bindings)
        self.assertEqual(sup.free_slots(closed), set())
        self.assertEqual(_value(closed, 0), 5)
        self.assertEqual(_value(closed, 1), 6)
        self.assertEqual(
            sup.render_proposition(closed, *NAT),
            "(((3 + 2) : Nat) >= ((3 * 2) : Nat))",
        )

        naive = text
        for name, value in bindings.items():
            naive = naive.replace(name, value)
        self.assertEqual(naive, "21 + 2 >= 21 * 2")
        self.assertNotIn("21", sup.render_proposition(closed, *NAT))


class AMissingBindingIsARefusalNotAGuess(unittest.TestCase):
    """A slot the record never bound is a point the run never drew."""

    def test_substitute_refuses_and_names_the_variable(self) -> None:
        with self.assertRaises(sup.Unpresentable) as caught:
            _closed("x + y >= 0", {"x": "2"})
        self.assertIn("'y'", str(caught.exception))
        self.assertIn("not be closed", str(caught.exception))

    def test_an_empty_binding_map_refuses_rather_than_defaulting(self) -> None:
        with self.assertRaises(sup.Unpresentable):
            _closed("x >= 0", {})

    def test_a_row_with_a_missing_binding_is_not_presented(self) -> None:
        """The refusal reaches the artifact as a row, not as a crash."""
        entry = {
            "adjudicated_index": 0,
            "c_e3_row": {"statement_id": "fixture", "reason": "fixture"},
            "e2_row": {
                "statement_id": "fixture",
                "domain": {"carrier": "Nat", "division": "truncating",
                           "subtraction": "truncated-at-zero"},
                "counterexample": {"bindings": {"x": "2"}, "left": "0",
                                   "right": "0", "relation": ">="},
            },
        }
        node = {"formal_statement": {"canonical_ascii": "x + y >= 0"}}
        row = sup.adjudicate(entry, node, Path("nonexistent-lean"), 5)
        self.assertEqual(row["decide_verdict"], sup.NOT_PRESENTED)
        self.assertIn("'y'", row["not_presented_because"])
        self.assertNotIn("checker_receipt", row)


class TheRenderingRefusesWhereTheReadingsDiverge(unittest.TestCase):
    """Correction 7's honest half, stated per domain rather than per row."""

    def test_rat_is_outside_decides_reach(self) -> None:
        closed = _closed("x >= 0", {"x": "2"})
        with self.assertRaises(sup.Unpresentable) as caught:
            sup.render_proposition(closed, "Rat", "exact", "signed")
        self.assertIn("Correction 7", str(caught.exception))

    def test_int_under_a_truncating_division_refuses(self) -> None:
        """Python floors and Lean's Int.div truncates toward zero."""
        closed = _closed("x >= 0", {"x": "2"})
        with self.assertRaises(sup.Unpresentable) as caught:
            sup.render_proposition(closed, "Int", "truncating", "signed")
        self.assertIn("toward", str(caught.exception))

    def test_nat_under_a_signed_subtraction_refuses(self) -> None:
        closed = _closed("x >= 0", {"x": "2"})
        with self.assertRaises(sup.Unpresentable):
            sup.render_proposition(closed, "Nat", "truncating", "signed")

    def test_a_unary_negation_over_nat_refuses_the_way_the_evaluator_does(
            self) -> None:
        closed = _closed("-3 * x >= 1", {"x": "2"})
        with self.assertRaises(sup.Unpresentable) as caught:
            sup.render_proposition(closed, *NAT)
        self.assertIn("negation", str(caught.exception))


def _binary():
    try:
        return sup.pinned_binary()
    except (sup.Unpresentable, OSError):
        return None


@unittest.skipIf(_binary() is None, "the pinned toolchain is not installed")
class TheRenderingMeansToLeanWhatItMeansToTheEvaluator(unittest.TestCase):
    """The renderer's claim, checked against the checker rather than argued.

    `render` mirrors `conform.eval_under_domain` branch for branch, and the
    supplement's whole value depends on that mirror holding: a rendering bug
    would surface as a `refuted_counterexample`, which is the one verdict this
    project would act on. So the mirror is tested on the truncation-sensitive
    shapes rather than asserted in a comment.
    """

    CASES = [
        ("a - b >= 0", {"a": "1", "b": "4"}, True),        # Nat clamps to 0
        ("a - b >= 1", {"a": "1", "b": "4"}, False),       # and 0 >= 1 is false
        ("1/x >= 1", {"x": "3"}, False),                   # floor(1/3) = 0
        ("1/x >= 0", {"x": "3"}, True),
        ("x1 + x >= x1 * x", {"x": "2", "x1": "3"}, False),
        ("x1 + x >= x1 + x", {"x": "2", "x1": "3"}, True),
        ("(a + b) / c = 2", {"a": "5", "b": "3", "c": "3"}, True),
    ]

    def test_each_case_decides_the_way_the_evaluator_does(self) -> None:
        binary = _binary()
        for text, bindings, expected in self.CASES:
            with self.subTest(text=text, bindings=bindings):
                closed = _closed(text, bindings)
                left, right = _value(closed, 0), _value(closed, 1)
                holds = conform.decide_relation(closed[1], left, right)
                self.assertEqual(holds, expected, "the fixture's own reading")
                proposition = sup.render_proposition(closed, *NAT)
                verdict, receipt = sup.decide_both_directions(
                    proposition, binary, timeout=60)
                self.assertEqual(
                    verdict,
                    sup.REFUTED if holds else sup.CONFIRMED,
                    f"Lean and the evaluator disagree on {proposition!r}: "
                    f"{receipt}",
                )


@unittest.skipUnless(ARTIFACT.exists(), "the supplement has not been run")
class TheArtifactSaysWhatItIsAndWhatItCannotDo(unittest.TestCase):
    """The schema, and the sentences the rider is not allowed to drop."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_the_header_names_its_authority_and_its_ordering(self) -> None:
        self.assertEqual(self.doc["supplement_id"],
                         "conformance.ce3.supplement.v1")
        self.assertEqual(self.doc["ordering"], "RETROSPECTIVE")
        self.assertIn("4.0(1)", self.doc["authority"])
        self.assertIn("found by REVIEW AFTER", self.doc["ordering_disclosed"])
        # NOT `assertIn(needle, haystack + needle)`, which is what this line
        # used to be: an assertion that appends its own needle to the
        # haystack cannot go red, and §4's standing review question is
        # exactly that. This reads the field.
        self.assertIn("is NOT edited by this rider",
                      self.doc["measure_conformance_is_byte_frozen"])
        self.assertIn(":434-438",
                      self.doc["measure_conformance_is_byte_frozen"])

    def test_the_original_run_is_read_only_and_digested(self) -> None:
        source = self.doc["source"]
        self.assertEqual(source["run_artifact"], sup.RUN)
        self.assertTrue(source["run_artifact_is_read_only_here"])
        self.assertEqual(
            source["run_artifact_sha256_lf"],
            sup._sha256_lf(ROOT / sup.RUN),
            "the supplement's digest of the registered run no longer matches "
            "the tree: the original was edited, which this rider forbids",
        )

    def test_the_checker_is_the_pinned_one_invoked_by_path(self) -> None:
        checker = self.doc["checker"]
        toolchain = (ROOT / sup.TOOLCHAIN_PIN).read_text(
            encoding="utf-8").strip()
        self.assertEqual(checker["toolchain"], toolchain)
        self.assertIn("no network", checker["invocation"])
        self.assertIn("both directions", checker["decision_procedure"])

    def test_every_row_carries_its_bindings_and_a_verdict(self) -> None:
        self.assertTrue(self.doc["rows"])
        allowed = {sup.CONFIRMED, sup.REFUTED, sup.DID_NOT_REDUCE,
                   sup.NOT_PRESENTED}
        for row in self.doc["rows"]:
            with self.subTest(statement=row["statement_id"]):
                self.assertIn(row["decide_verdict"], allowed)
                self.assertEqual(row["means"], sup.MEANS[row["decide_verdict"]])
                # Correction 7 requires the honest non-claim PER
                # COUNTEREXAMPLE, not once per artifact.
                self.assertEqual(row["honest_non_claim"],
                                 sup.HONEST_NON_CLAIM[row["decide_verdict"]])
                self.assertTrue(row["bindings"])
                self.assertIn("adjudicated_index", row)
                if row["decide_verdict"] == sup.NOT_PRESENTED:
                    self.assertTrue(row["not_presented_because"])
                    continue
                self.assertTrue(row["substituted_proposition"])
                receipt = row["checker_receipt"]
                self.assertIn("positive_probe", receipt)
                self.assertIn("negative_probe", receipt)
                for probe in ("positive_probe", "negative_probe"):
                    self.assertIn("source_sha256", receipt[probe])
                    self.assertIn("returncode", receipt[probe])

    def test_the_proposition_is_closed_and_carries_no_variable_name(
            self) -> None:
        """The gap being repaired, checked on the artifact itself."""
        for row in self.doc["rows"]:
            proposition = row.get("substituted_proposition")
            if proposition is None:
                continue
            with self.subTest(statement=row["statement_id"]):
                for name in row["bindings"]:
                    # A TOKEN test, not a substring test. The rendering
                    # carries the carrier's own name — `Nat` — and a variable
                    # called `a` or `n` is a substring of it. A substring
                    # assertion here would be red on a correct artifact,
                    # which is the mirror image of the failure mode §4 names.
                    self.assertIsNone(
                        re.search(
                            rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])",
                            proposition),
                        f"variable {name} survived into the proposition; this "
                        f"is the v0.20 gap, not its repair")

    def test_every_substitution_reproduces_the_runs_own_numbers(self) -> None:
        """The cross-check that says the point is the run's point."""
        self.assertEqual(
            self.doc["aggregate"]["rows_whose_substitution_did_not_reproduce_"
                                  "the_run"],
            [],
        )
        for row in self.doc["rows"]:
            if row["decide_verdict"] == sup.NOT_PRESENTED:
                continue
            with self.subTest(statement=row["statement_id"]):
                recomputation = row["evaluator_recomputation"]
                self.assertTrue(recomputation["reproduces_the_runs_numbers"])
                self.assertEqual(recomputation["left"], row["run_recorded"]["left"])
                self.assertEqual(recomputation["right"],
                                 row["run_recorded"]["right"])

    def test_the_exact_rational_reading_is_recomputed_not_trusted(self) -> None:
        """H1: the number that says which risk the agreement priced.

        Recomputed here from the corpus and the record's own bindings, so the
        artifact's aggregate is checked against the tree rather than read back
        out of itself.
        """
        run = json.loads((ROOT / sup.RUN).read_text(encoding="utf-8"))
        entries = sup.sampled_rows(run)
        nodes = sup.corpus_nodes({e["e2_row"]["statement_id"] for e in entries})
        # THE ARTIFACT'S DENOMINATOR IS `confirmed_rows`, not every sampled
        # row, and this test used to walk all of them. The two coincide only
        # because every row confirmed; a test whose denominator agrees with
        # the artifact's by luck is a test that stops agreeing the first time
        # a row reads differently.
        confirmed = {
            row["statement_id"] for row in self.doc["rows"]
            if row["decide_verdict"] == sup.CONFIRMED
        }
        self.assertEqual(len(confirmed),
                         self.doc["aggregate"]["of_confirmed_rows"])
        holds = 0
        for entry in entries:
            e2_row = entry["e2_row"]
            if e2_row["statement_id"] not in confirmed:
                continue
            node = nodes[e2_row["statement_id"]]
            closed = sup.substitute(
                census.parse(
                    (node.get("formal_statement") or {}).get(
                        "canonical_ascii", "")),
                e2_row["counterexample"]["bindings"])
            left = conform.eval_under_domain(
                closed[2][0], {}, "Rat", "exact", "signed")
            right = conform.eval_under_domain(
                closed[2][1], {}, "Rat", "exact", "signed")
            holds += conform.decide_relation(closed[1], left, right)
        self.assertEqual(
            self.doc["aggregate"]["rows_that_hold_over_exact_rationals"],
            holds)

    def test_the_agreement_is_not_sold_as_a_corpus_finding(self) -> None:
        prices = self.doc["aggregate"]["what_the_agreement_therefore_PRICES"]
        self.assertIn("DOMAIN risk", prices)
        self.assertIn("is therefore ARITHMETIC-IMPLEMENTATION risk", prices)
        self.assertIn("untouched", prices)

    def test_the_aggregate_tallies_the_rows_it_published(self) -> None:
        tally = self.doc["aggregate"]["by_verdict"]
        self.assertEqual(sum(tally.values()), len(self.doc["rows"]))
        self.assertEqual(self.doc["aggregate"]["adjudicated"],
                         len(self.doc["rows"]))
        refuted = self.doc["aggregate"]["refuted_counterexamples"]
        self.assertEqual(
            len(refuted), tally.get(sup.REFUTED, 0),
            "a refuted counterexample must appear in the named list, not only "
            "in the count")

    def test_the_non_claims_keep_the_void_where_it_is(self) -> None:
        joined = " ".join(self.doc["non_claims"])
        self.assertIn("does not un-void", joined)
        self.assertIn("no conformance rate", joined)
        self.assertIn("prover/verifier-verdicts/", joined)
        self.assertIn("agreement", self.doc["what_this_answers"])
        self.assertIn("disagreement", self.doc["what_this_answers"])
        self.assertIn("FILED", self.doc["what_this_answers"]["disagreement"])

    def test_it_adjudicates_the_sampled_class_the_run_left_open(self) -> None:
        run = json.loads((ROOT / sup.RUN).read_text(encoding="utf-8"))
        expected = sup.sampled_rows(run)
        self.assertEqual(len(self.doc["rows"]), len(expected))
        self.assertEqual(
            [r["statement_id"] for r in self.doc["rows"]],
            [e["e2_row"]["statement_id"] for e in expected],
        )
        for row in self.doc["rows"]:
            with self.subTest(statement=row["statement_id"]):
                self.assertEqual(
                    row["run_recorded"]["c_e3_said"],
                    "decide did not reduce in either direction",
                    "this row was not one of the 25 the gap withheld")


PREREG = ROOT / sup.PREREG

#: main's tip when this branch was cut. A FIXED commit rather than the moving
#: `main`, so the reversibility check below asks the same question forever.
BASE_COMMIT = "a98fa3cc17813e879cad6e8df095ab3f3863e0ab"


class TheAmendmentIsDatedRetrospectiveAndAppendOnly(unittest.TestCase):
    """The prereg amendment carries its own authority, or it is decoration."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(PREREG.read_text(encoding="utf-8"))
        cls.entry = next(
            a for a in cls.doc["amendments"]
            if a["amendment_id"] == "conformance.prereg.amendment.ce3-supplement"
        )

    def test_it_is_dated_and_says_on_what_basis(self) -> None:
        self.assertEqual(self.entry["dated"], "2026-08-26")
        self.assertIn("UTC", self.entry["dated_basis"])
        self.assertIn("2026-08-25", self.entry["dated_basis"],
                      "the local clock read a different day; say so")

    def test_the_ordering_is_labelled_retrospective_in_the_field_itself(
            self) -> None:
        self.assertTrue(self.entry["ordering"].startswith("RETROSPECTIVE"),
                        self.entry["ordering"])
        self.assertIn("found by REVIEW AFTER", self.entry["ordering_disclosed"])
        self.assertIn("weaker than a floor frozen before",
                      self.entry["ordering_disclosed"])

    def test_it_names_the_relaxation_that_permits_it(self) -> None:
        self.assertIn("§4.0(1)", self.entry["authority"])
        self.assertIn("bug-not-result", self.entry["authority"])
        self.assertIn("foreign_voice_rate",
                      self.entry["precedent_for_the_shape"])

    def test_it_lists_what_it_cannot_do_and_the_list_is_not_a_gesture(
            self) -> None:
        cannot = self.entry["what_it_cannot_do"]
        self.assertGreaterEqual(len(cannot), 6)
        joined = " ".join(cannot)
        self.assertIn("NEVER un-voids", joined)
        self.assertIn("read-only", joined)
        self.assertIn("verified_by", joined)

    def test_deleting_the_amendment_restores_the_sealed_file_byte_for_byte(
            self) -> None:
        """APPEND-ONLY, checked mechanically rather than promised.

        The house rule for an in-place edit to a canonical artifact is that a
        reader can undo it and get the original back. Here that is literally
        true: the amendment is one contiguous block, and removing it restores
        the blob sealed at `BASE_COMMIT`.
        """
        try:
            original = subprocess.run(
                ["git", "show", f"{BASE_COMMIT}:{sup.PREREG}"],
                cwd=ROOT, capture_output=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            self.skipTest(f"git could not read the sealed blob: {exc}")

        current = PREREG.read_bytes().replace(b"\r\n", b"\n")
        start = current.index(b'  "amendments": [')
        end = current.index(b'  "census": {')
        reconstructed = current[:start] + current[end:]
        self.assertEqual(
            reconstructed, original.replace(b"\r\n", b"\n"),
            "the amendment is not append-only: removing the block does not "
            "restore the preregistration as it was sealed")


@unittest.skipUnless((ROOT / "experiments" / "conformance_e5_late.json").exists(),
                     "the late determinism artifact has not been written")
class TheLateDeterminismCheckDisclosesItsLateness(unittest.TestCase):
    """§4.0(2): a byte-identity check cannot be gamed by when it runs — but
    the lateness is still disclosed rather than left for a reader to infer."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(
            (ROOT / "experiments" / "conformance_e5_late.json").read_text(
                encoding="utf-8"))

    def test_it_says_it_is_late_and_names_the_authority(self) -> None:
        self.assertIn("4.0(2)", self.doc["authority"])
        disclosure = self.doc["lateness_disclosure"]
        self.assertIn("WAS NOT RUN", disclosure)
        self.assertIn("2026-08-25", disclosure,
                      "the disclosure must name the run it is late for")
        self.assertIn("stop condition", disclosure)

    def test_the_two_fresh_runs_are_compared_by_digest(self) -> None:
        e5 = self.doc["e5"]
        self.assertIn("run_1_sha256", e5)
        self.assertIn("run_2_sha256", e5)
        self.assertEqual(e5["byte_identical"],
                         e5["run_1_sha256"] == e5["run_2_sha256"])
        self.assertEqual(e5["verdict"],
                         "HOLDS" if e5["byte_identical"] else "DIVERGED")

    def test_the_stability_arm_says_which_evidence_it_rides(self) -> None:
        self.assertIn("rides_the_same_evidence", self.doc["c_e1_stability_arm"])

    def test_the_original_artifact_was_not_written_over(self) -> None:
        self.assertTrue(self.doc["the_original_was_not_written_over"])


if __name__ == "__main__":
    unittest.main()
