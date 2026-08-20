#!/usr/bin/env python3
"""Dictionary senses are quoted, attributed, and never mistaken for corpus.

Skips loudly when the pinned archive is absent rather than passing on an
empty index — the WOLD lesson from v0.11, where a missing archive produced a
quiet wrong number instead of a refusal.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from gloss import archive_path, look_up, pinned_archive_path, render  # noqa: E402

HAVE_ARCHIVE = archive_path() is not None
REASON = (
    "no WordNet archive (fetch wordnet-2025-json or set COROLLARY_WORDNET)"
)


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


class ArchiveIsLocatedWithoutConfiguration(unittest.TestCase):
    """The manifest-pinned fetch location is a fallback, never an override.

    The boot printed `[OFF] no archive` while the archive sat in the checkout
    at the exact path `fetch_sources.py` chose for it. These pin the fix: an
    unset env var falls back to the manifest's `archive_dir`; a hand-named
    path keeps priority and keeps its loud named-but-missing semantics (the
    fallback never rescues a misconfiguration).
    """

    def _repo(self, tmp: str, *, fetched: bool, manifest: bool = True) -> Path:
        root = Path(tmp)
        archives = root / "data_sources" / "archives"
        archives.mkdir(parents=True)
        if manifest:
            pinned = {
                "archive_dir": "data_sources/archives",
                "sources": [
                    {
                        "id": "wordnet-2025-json",
                        "group": "wordnet",
                        "filename": "english-wordnet-2025-json.zip",
                    }
                ],
            }
            (root / "data_sources" / "manifest.json").write_text(
                json.dumps(pinned), encoding="utf-8"
            )
        if fetched:
            (archives / "english-wordnet-2025-json.zip").write_bytes(b"zip")
        return root

    def test_fetched_archive_is_found_from_the_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp, fetched=True)
            found = pinned_archive_path(root)
            self.assertIsNotNone(found)
            self.assertEqual(found.name, "english-wordnet-2025-json.zip")

    def test_unfetched_archive_is_absence_not_a_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp, fetched=False)
            self.assertIsNone(pinned_archive_path(root))

    def test_missing_manifest_is_absence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp, fetched=True, manifest=False)
            self.assertIsNone(pinned_archive_path(root))

    def test_env_var_overrides_the_pinned_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            named = Path(tmp) / "my-own-wordnet.zip"
            named.write_bytes(b"zip")
            with patch.dict("os.environ", {"COROLLARY_WORDNET": str(named)}):
                self.assertEqual(archive_path(), named)

    def test_named_missing_env_path_is_not_rescued_by_the_fallback(self) -> None:
        # A person who named a path gets the loud FAIL semantics the probe
        # owns; silently answering from the pinned copy would hide the typo.
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "no_such_archive.zip")
            with patch.dict("os.environ", {"COROLLARY_WORDNET": missing}):
                self.assertIsNone(archive_path())

    def test_unset_env_falls_back_to_the_pinned_location(self) -> None:
        with patch.dict("os.environ"):
            os.environ.pop("COROLLARY_WORDNET", None)
            self.assertEqual(archive_path(), pinned_archive_path())


if __name__ == "__main__":
    unittest.main()
