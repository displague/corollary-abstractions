#!/usr/bin/env python3
"""Gates on B0d's sealed prediction: the rule, the draw, and the hundred.

DESIGN-foreign-voice §6 B0d and the three-line separation its adversarial
review required.  Nothing here imports a renderer — `scripts/foreign_voice.py`
does not exist at this commit, and that is the whole point of a seal.

What each block is for:

- **The rule** — re-derived from the committed lexicon digest and compared
  against the committed id list.  `random.Random.shuffle` is deterministic for
  a seed on a given CPython, not by language guarantee (the same caveat
  v0.18's C-R1 derangement lives under), so the draw is *both* computed and
  committed, and this test is what turns red if the interpreter's shuffle ever
  moves.
- **No hand-picking** — the pool is asserted to be every oracle-eligible id
  with nothing removed, and the seed is asserted to be the lexicon's own
  digest rather than a number somebody chose.
- **The seal** — one surface per drawn id, in the drawn order, verbatim, with
  every word traceable to a lexicon row or the registered numeral pair.  That
  last sweep is v0.18's R2, imported: it is the check that a sealed sentence
  cannot smuggle in surface from outside the two permitted sources.
- **What is NOT checked, and why** — the token sequence.  Checking it means
  writing the literal inverse, and the literal inverse is the implementation.
  Asserting it here would make the seal a rehearsal of a program that already
  agreed with itself.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import foreign_voice_lexicon as fvl  # noqa: E402
import foreign_voice_select as fvs  # noqa: E402
import numeral_words as nw  # noqa: E402

LEXICON_PATH = ROOT / "data" / "foreign_voice" / "lexicon.json"
PREVIEW_PATH = ROOT / "data" / "foreign_voice" / "eligibility_preview.json"
IDS_PATH = ROOT / "data" / "foreign_voice" / "b0d_ids.json"
SEALED_PATH = ROOT / "data" / "foreign_voice" / "b0d_sealed_renderings.json"
PREREG_PATH = ROOT / "experiments" / "foreign_voice_prereg.json"


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class SelectionRuleTests(unittest.TestCase):
    """The committed deterministic rule, re-derived rather than trusted."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
        cls.preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))

    def test_the_seed_is_the_lexicons_own_digest(self) -> None:
        """v0.18's C-R1 idiom: a seed someone chose would be a knob."""
        self.assertEqual(self.ids["seed_source"], "data/foreign_voice/lexicon.json")
        self.assertEqual(self.ids["seed_source_digest"], _sha256_lf(LEXICON_PATH))

    def test_the_draw_re_derives_from_the_committed_rule(self) -> None:
        """Also the portability tripwire: red if the shuffle ever moves."""
        pool = fvs.eligible_ids(self.preview)
        redrawn = fvs.select(pool, self.ids["seed_source_digest"], fvs.SAMPLE_SIZE)
        self.assertEqual(redrawn, self.ids["statement_ids"])

    def test_the_pool_is_every_eligible_id_with_nothing_removed(self) -> None:
        """Excluding the unrenderable six would be selecting for renderability."""
        accepted = [row["statement_id"] for row in self.preview["statements"]
                    if row["accepted"]]
        self.assertEqual(self.ids["pool_size"], len(accepted))
        self.assertEqual(self.ids["pool_size"], 2319)

    def test_the_draw_is_a_hundred_distinct_eligible_ids(self) -> None:
        drawn = self.ids["statement_ids"]
        self.assertEqual(len(drawn), 100)
        self.assertEqual(len(set(drawn)), 100)
        eligible = {row["statement_id"] for row in self.preview["statements"]
                    if row["accepted"]}
        self.assertTrue(set(drawn) <= eligible)

    def test_the_draw_is_sorted(self) -> None:
        """The rule returns sorted ids, so the file is diffable."""
        self.assertEqual(self.ids["statement_ids"],
                         sorted(self.ids["statement_ids"]))


class SealedRenderingTests(unittest.TestCase):
    """The hundred, as a prediction the implementation must reproduce."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sealed = json.loads(SEALED_PATH.read_text(encoding="utf-8"))
        cls.ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
        cls.lex = fvl.load(LEXICON_PATH)
        cls.vocabulary = {word for phrase in cls.lex.phrase_to_token
                          for word in phrase}

    def test_one_rendering_per_drawn_id_in_the_drawn_order(self) -> None:
        rendered = [row["statement_id"] for row in self.sealed["renderings"]]
        self.assertEqual(rendered, self.ids["statement_ids"])

    def test_every_word_traces_to_a_row_or_to_the_numeral_pair(self) -> None:
        """R2, imported from v0.18. The seal cannot smuggle in outside surface."""
        offenders: dict[str, list[str]] = {}
        for row in self.sealed["renderings"]:
            outside = [word for word in row["surface"].split()
                       if word not in self.vocabulary
                       and not nw.is_numeral_word(word)]
            if outside:
                offenders[row["statement_id"]] = outside
        self.assertEqual(offenders, {})

    def test_no_surface_is_empty_or_carries_stray_whitespace(self) -> None:
        """Byte-identical reproduction is the bar, so the bytes are gated."""
        for row in self.sealed["renderings"]:
            with self.subTest(statement_id=row["statement_id"]):
                surface = row["surface"]
                self.assertTrue(surface)
                self.assertEqual(surface, surface.strip())
                self.assertNotIn("  ", surface)
                self.assertNotIn("\n", surface)
                self.assertNotIn("\t", surface)

    def test_every_rendering_carries_the_interpretation_it_was_authored_against(
            self) -> None:
        """Authored against R(s), not against the corpus source (Correction 3)."""
        by_id = {row["statement_id"]: row for row in self.ids["drawn"]}
        for row in self.sealed["renderings"]:
            with self.subTest(statement_id=row["statement_id"]):
                self.assertEqual(row["interpreted"],
                                 by_id[row["statement_id"]]["interpreted"])
                self.assertEqual(row["source"], by_id[row["statement_id"]]["source"])

    def test_the_prediction_for_every_row_is_recorded(self) -> None:
        """A seal with no prediction is a note. Refusals would be sealed too."""
        for row in self.sealed["renderings"]:
            self.assertIn(row["predicted"], {"rendered", "refused"})

    def test_a_slot_word_is_always_followed_by_a_numeral_run(self) -> None:
        """The slot marker's grammar, checked over the whole seal.

        This is not the inverse — it never asks what token a phrase emits. It
        asks only that the one generated row in the table is used the way the
        table says it is used.
        """
        marker = self.lex.slot_word
        for row in self.sealed["renderings"]:
            words = row["surface"].split()
            for index, word in enumerate(words):
                if word != marker:
                    continue
                with self.subTest(statement_id=row["statement_id"], at=index):
                    self.assertLess(index + 1, len(words),
                                    "a slot word ends the sentence")
                    self.assertTrue(nw.is_numeral_word(words[index + 1]),
                                    f"{words[index + 1]!r} follows {marker!r} "
                                    f"and is not a numeral word")


class SealOrderingTests(unittest.TestCase):
    """B7's ordering, extended by B0d: digests before renderings, always."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))

    def test_the_sealed_file_is_frozen_in_the_prereg(self) -> None:
        frozen = {row["path"]: row for row in self.prereg["frozen"]}
        for path in ("data/foreign_voice/b0d_ids.json",
                     "data/foreign_voice/b0d_sealed_renderings.json",
                     "scripts/foreign_voice_select.py"):
            with self.subTest(path=path):
                self.assertIn(path, frozen)
                self.assertEqual(_sha256_lf(ROOT / path), frozen[path]["sha256_lf"])

    def test_the_lexicon_digest_the_seal_names_is_the_frozen_one(self) -> None:
        """If the table moved after the draw, the draw is of a different hundred."""
        frozen = {row["path"]: row for row in self.prereg["frozen"]}
        sealed = json.loads(SEALED_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            sealed["id_selection_seed"],
            frozen["data/foreign_voice/lexicon.json"]["sha256_lf"])

    def test_the_serializer_has_still_not_landed(self) -> None:
        """B0d precedes B-P in the design's §10 order, and the file says so."""
        pending = {row["role"]: row for row in self.prereg["pending"]}
        self.assertEqual(pending["serializer"]["sha256_lf"], "pending")
        self.assertFalse((ROOT / "prover" / "lean" / "normalizer" /
                          "Serialize.lean").exists())

    def test_no_renderer_exists_yet(self) -> None:
        """The seal is only a prediction if nothing has run against it."""
        self.assertFalse((ROOT / "scripts" / "foreign_voice.py").exists())


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
