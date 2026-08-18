#!/usr/bin/env python3
"""Each ambiguity check must be trippable, or it is decoration.

Synthetic corpora throughout: these tests are about the checker, and using
the committed graph would make them slow and would quietly couple a
construction rule to whatever the corpus happens to contain today.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_ambiguity import TitleIndex, check_row, eligible  # noqa: E402
from resolver import GraphIndex  # noqa: E402


def node(title: str) -> dict:
    return {"title": title, "semantic_interpretation": {}, "keywords": [],
            "symbol_lexicon": {}}


#: `planar` and `complete` are both edge-bound statements about graphs, so a
#: query naming neither is genuinely undecided between them. `tangent` is the
#: control: nothing else in this corpus looks like it.
CORPUS = {
    "graph.planar_edge_bound": (node("upper edge bound for a planar graph"), "graph.v1"),
    "graph.complete_edge_count": (node("upper edge count for a complete graph"), "graph.v1"),
    "trig.tangent": (node("tangent as a trigonometric ratio"), "trig.v1"),
    "misc.filler": (node("unrelated statement about weather"), "misc.v1"),
}

INDEX = GraphIndex(
    statement_ids=tuple(CORPUS),
    corpus_of={sid: cid for sid, (_n, cid) in CORPUS.items()},
    by_prose={
        "planar": ("graph.planar_edge_bound",),
        "complete": ("graph.complete_edge_count",),
    },
    prose_df={"planar": 1, "complete": 1},
)


def ask_row(**overrides) -> dict:
    row = {
        "row_id": "T-01",
        "expected_route": "ASK",
        "query": "upper edge limit for a graph",
        "primary_id": "graph.planar_edge_bound",
        "retained_ids": ["graph.planar_edge_bound"],
        "competing_ids": ["graph.complete_edge_count"],
        "follow_up": {
            "line": "narrow word planar",
            "class": "word",
            "value": "planar",
        },
    }
    row.update(overrides)
    return row


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.titles = TitleIndex(CORPUS)

    def check(self, row: dict) -> list[str]:
        return check_row(row, CORPUS, self.titles, INDEX)


class AWellFormedRowPasses(Fixture):
    def test_a_genuinely_undecided_row_is_admitted(self) -> None:
        self.assertEqual(self.check(ask_row()), [])

    def test_non_ask_rows_are_not_this_checks_business(self) -> None:
        row = ask_row(expected_route="BIND", retained_ids=[], competing_ids=[])
        self.assertEqual(self.check(row), [])


class ItRefusesAmbiguityThatIsOnlyAsserted(Fixture):
    def test_a_row_naming_no_competitor_is_refused(self) -> None:
        problems = self.check(ask_row(competing_ids=[]))
        self.assertTrue(any("declares no competing_ids" in p for p in problems), problems)

    def test_a_query_the_corpus_already_settles_is_refused(self) -> None:
        """The v0.14 failure shape: the intended reading simply wins."""
        row = ask_row(
            query="tangent as a trigonometric ratio",
            primary_id="trig.tangent",
            retained_ids=["trig.tangent"],
            competing_ids=["graph.complete_edge_count"],
            follow_up={"line": "narrow corpus trig.v1", "class": "corpus",
                       "value": "trig.v1"},
        )
        problems = self.check(row)
        self.assertTrue(
            any("the corpus is not ambiguous here" in p for p in problems), problems
        )

    def test_a_declared_reading_outside_the_blind_horizon_is_refused(self) -> None:
        """A reading only the author can find is not one the corpus offers.

        Both readings tie at 0.625 here -- which is why the well-formed row
        passes check 2 -- so the id tie-break decides the order and a horizon
        of one keeps `complete` while losing `planar`.  Either way exactly one
        declared reading falls outside and the checker has to say so.
        """
        problems = check_row(ask_row(), CORPUS, self.titles, INDEX, blind_limit=1)
        self.assertTrue(any("blind top 1" in p for p in problems), problems)
        self.assertIn("graph.planar_edge_bound", " ".join(problems))
        # The tie is real, so ambiguity itself is not what was objected to.
        self.assertFalse(any("not ambiguous here" in p for p in problems), problems)


class ItRefusesAFollowUpThatDoesNotNarrow(Fixture):
    def test_a_follow_up_that_drops_an_intended_reading_is_refused(self) -> None:
        row = ask_row(
            retained_ids=["graph.planar_edge_bound", "graph.complete_edge_count"],
            competing_ids=["trig.tangent"],
            follow_up={"line": "narrow word planar", "class": "word",
                       "value": "planar"},
        )
        problems = self.check(row)
        self.assertTrue(
            any("drops intended readings" in p for p in problems), problems
        )

    def test_a_follow_up_that_eliminates_nothing_is_refused(self) -> None:
        """Keeping everything is not clarification, however well it scores."""
        row = ask_row(
            follow_up={"line": "narrow corpus graph.v1", "class": "corpus",
                       "value": "graph.v1"},
        )
        problems = self.check(row)
        self.assertTrue(
            any("eliminates no declared competitor" in p for p in problems), problems
        )


class ItRefusesIneligibleIds(Fixture):
    def test_absent_and_ingested_ids_are_named(self) -> None:
        self.assertEqual(eligible("graph.planar_edge_bound", CORPUS), None)
        self.assertEqual(eligible("nope.missing", CORPUS), "absent from data/")
        ingested = dict(CORPUS)
        ingested["x.y"] = (node("t"), "lean_workbook.batch.v1")
        self.assertIn("ingested corpus", eligible("x.y", ingested) or "")

    def test_a_row_pointing_at_a_missing_competitor_is_refused(self) -> None:
        problems = self.check(ask_row(competing_ids=["nope.missing"]))
        self.assertTrue(any("absent from data/" in p for p in problems), problems)

    def test_an_id_cannot_be_both_retained_and_competing(self) -> None:
        problems = self.check(
            ask_row(competing_ids=["graph.planar_edge_bound"])
        )
        self.assertTrue(
            any("both retained and competing" in p for p in problems), problems
        )


if __name__ == "__main__":
    unittest.main()
