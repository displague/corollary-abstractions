"""Fast checks that resolver context is hard intersection, never ranking."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import harness  # noqa: E402
from resolver import GraphIndex  # noqa: E402


class HardConstraintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = GraphIndex(
            statement_ids=("alpha.one", "beta.two", "gamma.three"),
            corpus_of={
                "alpha.one": "corpus.a",
                "beta.two": "corpus.b",
                "gamma.three": "corpus.b",
            },
            by_prose={
                "shared": ("alpha.one", "beta.two"),
                "unique": ("gamma.three",),
            },
        )
        self.candidates = self.index.statement_ids

    def test_complete_word_constraint_keeps_every_match_and_never_ranks(self) -> None:
        self.assertEqual(
            harness._narrow_candidates(
                self.index, self.candidates, "word", "shared"
            ),
            ("alpha.one", "beta.two"),
        )

    def test_zero_match_is_empty_for_the_runtime_to_preserve(self) -> None:
        self.assertEqual(
            harness._narrow_candidates(
                self.index, self.candidates, "word", "absent"
            ),
            (),
        )

    def test_corpus_constraint_is_exact_not_a_score(self) -> None:
        self.assertEqual(
            harness._narrow_candidates(
                self.index, self.candidates, "corpus", "corpus.b"
            ),
            ("beta.two", "gamma.three"),
        )


if __name__ == "__main__":
    unittest.main()
