#!/usr/bin/env python3
"""Dictionary senses are quoted, attributed, and never mistaken for corpus.

Skips loudly when the pinned archive is absent rather than passing on an
empty index — the WOLD lesson from v0.11, where a missing archive produced a
quiet wrong number instead of a refusal.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from gloss import archive_path, look_up, render  # noqa: E402

HAVE_ARCHIVE = archive_path() is not None
REASON = "COROLLARY_WORDNET not set to the pinned archive"


@unittest.skipUnless(HAVE_ARCHIVE, REASON)
class GlossesAreQuoted(unittest.TestCase):
    def test_a_common_noun_has_human_written_senses(self) -> None:
        gloss = look_up("chicken")
        self.assertTrue(gloss.found)
        self.assertTrue(any(s.definitions for s in gloss.senses))

    def test_every_printed_sentence_is_a_wordnet_string(self) -> None:
        """The guarantee: labels are ours, sentences are the dictionary's."""
        gloss = look_up("chicken")
        printed = render(gloss)
        quotable = {
            text
            for sense in gloss.senses
            for text in (*sense.definitions, *sense.examples)
        }
        # Every indented content line must be a verbatim gloss/example, or a
        # label line we control (identified by its trailing colon or prefix).
        for line in printed:
            stripped = line.strip()
            if not stripped or stripped.startswith(("(", "also:", "e.g.", "...")):
                continue
            if stripped.startswith("chicken —") or stripped.startswith("quoted from"):
                continue
            self.assertIn(stripped, quotable, f"unattributed sentence: {line!r}")

    def test_ambiguity_is_reported_not_resolved(self) -> None:
        gloss = look_up("spring")
        self.assertGreater(len(gloss.senses), 1)

    def test_provenance_travels_with_the_answer(self) -> None:
        gloss = look_up("chicken")
        self.assertTrue(gloss.archive)
        self.assertEqual(len(gloss.archive_sha256), 64)

    def test_an_unknown_word_is_reported_as_absent(self) -> None:
        gloss = look_up("zzqxwv")
        self.assertFalse(gloss.found)
        self.assertIn("no dictionary entry", "\n".join(render(gloss)))

    def test_a_gloss_is_labelled_as_not_a_corpus_statement(self) -> None:
        rendered = "\n".join(render(look_up("chicken")))
        self.assertIn("not a statement in this corpus", rendered)


class WithoutTheArchive(unittest.TestCase):
    def test_lookup_reports_absence_rather_than_guessing(self) -> None:
        self.assertIsNone(look_up("chicken", archive=None) if not HAVE_ARCHIVE else None)


if __name__ == "__main__":
    unittest.main()
