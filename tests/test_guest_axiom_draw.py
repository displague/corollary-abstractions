#!/usr/bin/env python3
"""G-P0: the drawing rule is the source of truth; the draw obeys it.

The rule was committed first. These tests recompute the recast from the
sealed questions and the covered set, and they refuse an invented
correction pool.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "tests"))

from git_ordering import assert_added_before  # noqa: E402
from guest_axiom_draw import (  # noqa: E402
    CORRECTIONS_PATH,
    DEFAULT_OUT,
    QUESTIONS_PATH,
    RULE_PATH,
    build,
    covered_ids,
    named_covered_ids,
    recast_question,
)
from supposition import _atom  # noqa: E402

RULE = json.loads(RULE_PATH.read_text(encoding="utf-8"))
QUESTIONS = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))


class RuleShapeTests(unittest.TestCase):
    def test_rule_names_the_voice_covered_set_constructor(self) -> None:
        covered = RULE["covered_set"]
        self.assertEqual(
            covered["constructor"], "scripts/measure_foreign_voice.py:covered_rows"
        )

    def test_pilot_ids_are_the_first_ten_question_ids(self) -> None:
        reserved = RULE["recorded_question_recast"]["pilot_reservation"]["question_ids"]
        self.assertEqual(
            reserved, [f"g1-{i:02d}" for i in range(1, 11)]
        )

    def test_correction_source_is_the_crossing_log_and_nothing_else(self) -> None:
        source = RULE["maintainer_correction_draw"]["named_source"]["path"]
        self.assertEqual(source, "experiments/crossing_corrections.json")
        self.assertFalse(
            CORRECTIONS_PATH.is_file(),
            "authoring the named log in the draw commit would invent the pool",
        )


class RecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.covered = covered_ids()
        cls.pilot = set(
            RULE["recorded_question_recast"]["pilot_reservation"]["question_ids"]
        )

    def test_covered_set_is_2313(self) -> None:
        self.assertEqual(len(self.covered), 2313)

    def test_exhaust_questions_are_nameless_even_if_why_names_an_id(self) -> None:
        for question in QUESTIONS["questions"]:
            if question["authors_prior"] != "exhaust":
                continue
            recast = recast_question(question, self.covered, self.pilot)
            self.assertEqual(recast["source_stratum"], "nameless_probe")
            self.assertIsNone(recast["target_statement_id"])

    def test_unique_covered_id_in_why_is_the_target_otherwise_nameless(self) -> None:
        for question in QUESTIONS["questions"]:
            if question["authors_prior"] == "exhaust":
                continue
            named = named_covered_ids(question["why"], self.covered)
            recast = recast_question(question, self.covered, self.pilot)
            if len(named) == 1:
                self.assertEqual(recast["source_stratum"], "recorded_question")
                self.assertEqual(recast["target_statement_id"], named[0])
                self.assertIn(named[0], self.covered)
            else:
                self.assertEqual(recast["source_stratum"], "nameless_probe")
                self.assertIsNone(recast["target_statement_id"])

    def test_hypothesis_text_is_the_question_verbatim(self) -> None:
        for question in QUESTIONS["questions"]:
            recast = recast_question(question, self.covered, self.pilot)
            self.assertEqual(recast["hypothesis_text"], question["question"])
            self.assertEqual(recast["hypothesis_normal_form"], _atom(question["question"])[0])

    def test_substring_ids_do_not_count(self) -> None:
        fake = set(self.covered)
        if not fake:
            self.skipTest("empty covered set")
        long_id = next(iter(sorted(fake)))
        prefix = long_id.rsplit(".", 1)[0]
        if prefix in fake:
            why = f"see {long_id} only"
            named = named_covered_ids(why, fake)
            self.assertIn(long_id, named)
            self.assertNotIn(prefix, named)


class DrawArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = build()

    def test_correction_arm_is_blocked_no_log(self) -> None:
        self.assertEqual(self.artifact["correction_arm"], "BLOCKED_NO_LOG")
        self.assertEqual(self.artifact["correction_pool_size"], 0)
        self.assertEqual(
            self.artifact["counts"]["maintainer_correction"], 0
        )

    def test_counts_are_computed_from_the_records(self) -> None:
        counts = self.artifact["counts"]
        rows = self.artifact["hypotheses"]
        self.assertEqual(counts["total"], len(rows))
        self.assertEqual(
            counts["recorded_question"],
            sum(1 for h in rows if h["source_stratum"] == "recorded_question"),
        )
        self.assertEqual(
            counts["nameless_probe"],
            sum(1 for h in rows if h["source_stratum"] == "nameless_probe"),
        )
        self.assertEqual(counts["pilot"], 10)
        self.assertEqual(counts["total"], 30)
        self.assertEqual(
            counts["recorded_question"] + counts["nameless_probe"], 30
        )
        yield_ = counts["recast_yield"]
        self.assertEqual(
            yield_["non_exhaust_questions"],
            sum(1 for h in rows if h["authors_prior"] != "exhaust"),
        )
        self.assertEqual(
            yield_["landed_in_covered_set"],
            counts["recorded_question"],
        )
        self.assertEqual(
            yield_["nameless_because_no_unique_covered_id"]
            + yield_["nameless_because_exhaust"],
            counts["nameless_probe"],
        )

    def test_every_non_nameless_target_is_in_the_covered_set(self) -> None:
        covered = covered_ids()
        for row in self.artifact["hypotheses"]:
            if row["source_stratum"] == "nameless_probe":
                self.assertIsNone(row["target_statement_id"])
                continue
            self.assertIn(row["target_statement_id"], covered)

    def test_no_resolver_import_in_the_writer(self) -> None:
        source = (REPO / "scripts" / "guest_axiom_draw.py").read_text(encoding="utf-8")
        self.assertNotIn("import resolver", source)
        self.assertNotIn("from resolver", source)

    def test_committed_artifact_matches_a_fresh_build(self) -> None:
        if not DEFAULT_OUT.is_file():
            self.skipTest("guest_hypotheses.json not written yet")
        committed = json.loads(DEFAULT_OUT.read_text(encoding="utf-8"))
        fresh = build()
        self.assertEqual(committed, fresh)

    def test_drawing_rule_commit_is_a_strict_ancestor_of_the_draw(self) -> None:
        if not DEFAULT_OUT.is_file():
            self.skipTest("guest_hypotheses.json not written yet")
        assert_added_before(
            self,
            "experiments/guest_axiom_draw_rule.json",
            "experiments/guest_hypotheses.json",
            "G-P0's drawing rule must be committed before the draw",
        )


if __name__ == "__main__":
    unittest.main()
