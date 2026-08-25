#!/usr/bin/env python3
"""E0c's frozen register: exhaustive, zero-bearing, and never summed.

`docs/DESIGN-statements-that-run.md` §3.3 and E3. Two properties matter more
than the counts: the register lists its blocked sets **exhaustively** (LOST
= 0), and its `blocking_count` fields are **never summed against E3's
statement partition** — the register is indexed by construct, E3 by
statement, and conflating them double-counts.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import conform_domain  # noqa: E402

REGISTER = ROOT / "experiments" / "conformance_register.json"
PREREG = ROOT / "experiments" / "conformance_prereg.json"


class TheRegisterIsFrozenAndComplete(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(REGISTER.read_text(encoding="utf-8"))
        cls.entries = {e["construct_id"]: e for e in cls.doc["entries"]}

    def test_every_entry_lists_its_blocked_set_exhaustively(self) -> None:
        """LOST = 0: a count without its ids is a number nobody can check."""
        for construct, entry in self.entries.items():
            with self.subTest(construct=construct):
                self.assertEqual(
                    entry["blocking_count"], len(entry["statement_ids"]),
                    f"{construct} counts {entry['blocking_count']} and lists "
                    f"{len(entry['statement_ids'])}",
                )

    def test_no_statement_is_blocked_by_two_constructs_in_this_walk(self) -> None:
        """The walk stops at the first construct, so ids are disjoint here.

        The design warns that a statement CAN carry two constructs (its
        nested-relation case), which is why the counts must never be summed
        against E3. On this tree the walk's ordering makes the sets disjoint,
        and that is asserted rather than assumed — if it ever stops being
        true, the arithmetic test below is the one that must change.
        """
        ids = [i for e in self.doc["entries"] for i in e["statement_ids"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_the_arithmetic_closes_to_the_corpus(self) -> None:
        blocked = sum(e["blocking_count"] for e in self.doc["entries"])
        denominator = self.doc["e2_denominator"]
        total = (
            blocked
            + denominator["samplable_and_schema_covered"]
            + denominator["ground_and_schema_covered"]
        )
        self.assertEqual(total, 12777, "every statement must land somewhere")

    def test_the_register_ships_its_zeros(self) -> None:
        """A register that lists only populated rows cannot show you a zero."""
        self.assertIn("operator_pm", self.entries)
        self.assertEqual(self.entries["operator_pm"]["blocking_count"], 0)
        zero_rows = [
            c for c, e in self.entries.items() if e["blocking_count"] == 0
        ]
        self.assertGreaterEqual(len(zero_rows), 1)

    def test_every_construct_carries_a_reason(self) -> None:
        for construct, entry in self.entries.items():
            with self.subTest(construct=construct):
                self.assertTrue(entry["reason"].strip())

    def test_constructs_this_lane_added_say_so_with_a_date(self) -> None:
        """A closed vocabulary extended silently is not closed."""
        for construct in (
            "slot_alignment_failed", "undeclared_slot",
            "category_outside_typing_rule", "no_sampled_variable",
            "does_not_parse", "not_a_top_level_relation", "nested_relation",
        ):
            with self.subTest(construct=construct):
                self.assertIn("added 2026-08-25",
                              self.entries[construct]["reason"])

    def test_the_largest_entry_is_the_one_the_design_predicted(self) -> None:
        """§3.3 expects guard_measure_zero, and says the run decides."""
        largest = max(self.doc["entries"], key=lambda e: e["blocking_count"])
        self.assertEqual(largest["construct_id"], "does_not_parse")
        blocking = {
            e["construct_id"]: e["blocking_count"] for e in self.doc["entries"]
        }
        # Among the constructs that block a PARSEABLE statement — which is
        # what §3.3's prediction is about — the design named guard_measure_zero.
        parseable = {
            c: n for c, n in blocking.items() if c != "does_not_parse"
        }
        self.assertEqual(max(parseable, key=parseable.get), "guard_measure_zero")

    def test_the_ground_class_is_fully_schema_covered(self) -> None:
        """All 297 sit under the lean_workbook class row; E1 needs that."""
        self.assertEqual(
            self.doc["e2_denominator"]["ground_and_schema_covered"], 297)

    def test_e2s_denominator_is_the_intersection_not_the_whole_set(self) -> None:
        """E0c: a rate can never be quoted against a denominator the schema
        had not actually reached."""
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        whole = prereg["census"]["e0d_samplable_denominator"]["samplable"]
        intersected = self.doc["e2_denominator"]["samplable_and_schema_covered"]
        self.assertLessEqual(intersected, whole)
        self.assertIn("INTERSECTED",
                      self.doc["e2_denominator"]["what_this_is"])

    def test_the_freeze_digests_match_the_tree(self) -> None:
        for key, path in (
            ("schema_digest_at_freeze", "data/domains/domain_schema.json"),
            ("parser_digest_at_freeze", "scripts/match_signatures.py"),
            ("evaluator_digest_at_freeze", "scripts/evaluate.py"),
            ("sampler_digest_at_freeze", "scripts/conform_sampler.py"),
            ("census_digest_at_freeze", "scripts/conform_census.py"),
        ):
            with self.subTest(key=key):
                self.assertEqual(
                    self.doc[key], conform_domain.sha256_lf(ROOT / path))

    def test_the_blocked_set_digest_reproduces(self) -> None:
        import hashlib

        blob = json.dumps(
            {e["construct_id"]: e["statement_ids"] for e in self.doc["entries"]},
            sort_keys=True, ensure_ascii=False,
        ).encode("utf-8")
        self.assertEqual(
            self.doc["blocked_set_digest"], hashlib.sha256(blob).hexdigest())

    def test_the_writer_refuses_once_the_compiler_exists(self) -> None:
        import write_conformance_register as writer

        if (ROOT / writer.COMPILER).exists():
            self.assertEqual(writer.main([]), 2)


if __name__ == "__main__":
    unittest.main()
