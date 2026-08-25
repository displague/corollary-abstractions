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
sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice_lexicon as fvl  # noqa: E402
import foreign_voice_select as fvs  # noqa: E402
import numeral_words as nw  # noqa: E402
from git_ordering import (  # noqa: E402
    assert_absent_or_added_after,
    assert_added_before,
    first_added,
    is_ancestor,
)

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

    def test_the_seed_is_the_lexicons_digest_at_the_amendment_parent(self) -> None:
        """v0.18's C-R1 idiom, now a CONSEQUENCE rather than a constant (F6/G3).

        The seed was the committed lexicon's digest until v0.20's canonical
        grouping amendment moved that file. B0d's pool is the ELIGIBLE set,
        which does not depend on the grammar, so the draw is grammar-independent
        and the seed still identifies it — but the value now has to be DERIVED
        from the amendment commit's parent rather than read off the tree.

        The derivation lives in the sealed file's own header so it can be
        recomputed rather than trusted, and this asserts against it. The
        canonical form of this assertion — re-extracting the blob with
        `git show {parent}:…` and refusing on mismatch, the
        `transliteration_served_diff.py:357-360` precedent — is ROADMAP-v0.20
        §4d's scope and lands in the batch lane.
        """
        self.assertEqual(self.ids["seed_source"], "data/foreign_voice/lexicon.json")
        sealed = json.loads(SEALED_PATH.read_text(encoding="utf-8"))
        derivation = sealed["id_selection_seed_derivation"]

        # RECOMPUTED, not compared literal-to-literal. The first version of
        # this assertion checked the artifact's `derived_value` against the id
        # file's `seed_source_digest` — two strings written by the same script
        # in the same breath, so it could not have caught a wrong derivation.
        # Reviewer finding M9. This runs the derivation the header describes:
        # find the commit that re-sealed the file, take its PARENT's lexicon
        # blob, and hash it.
        import subprocess

        reseal = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--diff-filter=M", "--format=%H",
             "-1", "--", "data/foreign_voice/b0d_sealed_renderings.json"],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(reseal.returncode, 0, reseal.stderr)
        commit = reseal.stdout.strip().split("\n")[0]
        self.assertTrue(commit, "no re-seal commit found")

        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show",
             f"{commit}~1:data/foreign_voice/lexicon.json"],
            capture_output=True)
        self.assertEqual(
            blob.returncode, 0,
            f"cannot read the parent's lexicon blob at {commit[:8]}~1 — the "
            f"seed derivation is unverifiable here, and that is a FAILURE")
        recomputed = hashlib.sha256(
            blob.stdout.replace(b"\r\n", b"\n")).hexdigest()

        self.assertEqual(recomputed, derivation["derived_value"],
                         "the header's derived_value is not what the "
                         "derivation it describes actually produces")
        self.assertEqual(recomputed, self.ids["seed_source_digest"],
                         "the drawn ids were not seeded from the parent "
                         "commit's lexicon")
        self.assertTrue(derivation["agrees_with_the_recorded_seed"])
        self.assertNotEqual(
            recomputed, _sha256_lf(LEXICON_PATH),
            "the lexicon has not moved, so this test is asserting nothing that "
            "the simpler v0.19 form did not already assert")

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

    def test_the_lexicon_digest_the_seal_names_is_the_retired_one(self) -> None:
        """The table DID move after the draw, and the prereg records both values.

        Written for v0.19, where the seal's seed and the frozen lexicon digest
        were the same number. v0.20's amendment separated them, and the honest
        restatement is that the seal names the value the prereg RETIRED, not
        the value it currently pins.
        """
        sealed = json.loads(SEALED_PATH.read_text(encoding="utf-8"))
        retirements = [entry for entry in self.prereg["corrections"]
                       if "digests_retired" in entry]
        if not retirements:
            frozen = {row["path"]: row for row in self.prereg["frozen"]}
            self.assertEqual(sealed["id_selection_seed"],
                             frozen["data/foreign_voice/lexicon.json"]["sha256_lf"])
            return
        retired = {row["path"]: row for entry in retirements
                   for row in entry["digests_retired"]}
        self.assertEqual(sealed["id_selection_seed"],
                         retired["data/foreign_voice/lexicon.json"]["v019_sha256_lf"])

    def test_the_seal_predates_the_serializer_in_the_git_history(self) -> None:
        """§10's order, checked against the history rather than against prose.

        Two earlier versions of this test asserted, in turn, that
        `Serialize.lean` did not exist and that its prereg row said
        "promoted" — the first a fact about one tree, the second a string
        somebody could type. The ordering the design registers is a fact about
        WHEN things were written, so this asks git.
        """
        assert_added_before(
            self, "data/foreign_voice/b0d_sealed_renderings.json",
            "prover/lean/normalizer/Serialize.lean",
            "§10 orders the seal before B-P, so the hundred are a prediction "
            "and not a transcript of something that already ran")

    def test_the_ids_predate_the_renderings_in_the_git_history(self) -> None:
        """The review's three-line separation, in the order it requires."""
        ids = first_added("data/foreign_voice/b0d_ids.json")
        renderings = first_added("data/foreign_voice/b0d_sealed_renderings.json")
        self.assertTrue(
            is_ancestor(ids, renderings) or ids == renderings,
            "the drawn ids must not postdate the renderings authored for them; "
            "same commit is permitted here because the review's separation puts "
            "the DIGEST before both, not the ids before the sentences")

    def test_the_lexicon_predates_the_draw_in_the_git_history(self) -> None:
        """The first line of the separation: the seed is frozen before the draw."""
        assert_added_before(
            self, "data/foreign_voice/lexicon.json",
            "data/foreign_voice/b0d_ids.json",
            "the lexicon whose digest seeds the draw must be frozen before the "
            "draw, or the seed is a choice rather than a consequence")

    def test_the_renderer_did_not_exist_when_the_seal_was_written(self) -> None:
        """The seal is only a prediction if nothing could have produced it.

        Written in the B0d commit as "the renderer does not exist", which was
        true of that tree and stopped being true the moment phase 2 landed.
        The durable claim is about the ORDER, so it is read from the history.
        """
        assert_absent_or_added_after(
            self, "data/foreign_voice/b0d_sealed_renderings.json",
            "scripts/foreign_voice.py",
            "a hundred sentences authored after the renderer existed would be "
            "a transcript, not a prediction")


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
