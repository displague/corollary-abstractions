#!/usr/bin/env python3
"""B4 and B3: the inventory of silence, frozen, digested, and adding up.

DESIGN-foreign-voice §8: *"Coverage percent is not the headline. The register
is. No release sentence leads with a coverage number. If the register is thin
and the coverage is high, the cycle under-delivered on its actual product."*
So the register gets the tests a headline artifact gets, not the tests a
limitations paragraph would get:

- **B3's census closes exactly**, and the two `registered_blocked_*` buckets
  are asserted to be two numbers that are never summed into one.
- **Every entry carries the §3.3 shape** — a witness, a count, a digest over
  its own blocked set, a date, the frozen-before-render flag, and a revisit
  trigger — because an entry with a count and no reason is a code name.
- **No statement is registered twice**, and the blocked ids exactly account
  for the residue the oracle did not cover.
- **The classes were measured, not authored.** The Mathlib head list is
  re-derived from the committed eligibility preview's diagnostics and compared
  against the register's, so a hand-widened head list goes red.
- **B4's ordering** — the register is frozen and `scripts/foreign_voice.py`
  does not exist.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import foreign_voice_register as fvreg  # noqa: E402

REGISTER_PATH = ROOT / "data" / "foreign_voice" / "register.json"
PREVIEW_PATH = ROOT / "data" / "foreign_voice" / "eligibility_preview.json"
LEXICON_PATH = ROOT / "data" / "foreign_voice" / "lexicon.json"
RULE_PATH = ROOT / "data" / "foreign_voice" / "rule_r.json"
PREREG_PATH = ROOT / "experiments" / "foreign_voice_prereg.json"

_REQUIRED_FIELDS = (
    "register_id", "dialect_construct", "construct_class", "bucket", "reason",
    "blocking_count", "blocked_statement_set_digest", "surface_witness",
    "per_corpus", "decided_at", "frozen_before_render", "why",
    "revisit_trigger", "statement_ids",
)


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class RegisterSchema(unittest.TestCase):
    """§3.3's entry shape, over every entry, with nothing optional."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
        cls.entries = cls.register["entries"]

    def test_the_register_identifies_itself_and_its_freeze(self) -> None:
        self.assertEqual(self.register["register_id"], "foreign_voice.register.v1")
        self.assertEqual(self.register["frozen_at"], "2026-08-24")

    def test_it_was_frozen_against_the_digests_it_names(self) -> None:
        self.assertEqual(self.register["lexicon_digest_at_freeze"],
                         _sha256_lf(LEXICON_PATH))
        self.assertEqual(self.register["interpretation_digest_at_freeze"],
                         _sha256_lf(RULE_PATH))
        self.assertEqual(self.register["eligibility_preview_digest_at_freeze"],
                         _sha256_lf(PREVIEW_PATH))

    def test_every_entry_carries_the_whole_shape(self) -> None:
        for entry in self.entries:
            with self.subTest(register_id=entry.get("register_id")):
                for field in _REQUIRED_FIELDS:
                    self.assertIn(field, entry)
                self.assertTrue(entry["frozen_before_render"])
                self.assertTrue(entry["why"])
                self.assertTrue(entry["revisit_trigger"])
                self.assertTrue(entry["surface_witness"]["source"])
                self.assertTrue(entry["surface_witness"]["oracle_said"])

    def test_every_entrys_count_matches_its_own_id_list_and_digest(self) -> None:
        for entry in self.entries:
            with self.subTest(register_id=entry["register_id"]):
                ids = entry["statement_ids"]
                self.assertEqual(entry["blocking_count"], len(ids))
                self.assertEqual(len(set(ids)), len(ids))
                self.assertEqual(entry["blocked_statement_set_digest"],
                                 fvreg._digest_ids(ids))
                self.assertEqual(sum(entry["per_corpus"].values()), len(ids))

    def test_every_reason_is_from_the_lexicons_closed_vocabulary(self) -> None:
        lexicon = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        vocabulary = set(lexicon["refusal_reasons"])
        for entry in self.entries:
            with self.subTest(register_id=entry["register_id"]):
                self.assertIn(entry["reason"], vocabulary)

    def test_the_registers_own_digest_covers_every_blocked_statement(self) -> None:
        ids = [sid for entry in self.entries for sid in entry["statement_ids"]]
        self.assertEqual(len(ids), self.register["blocked_total"])
        self.assertEqual(len(set(ids)), len(ids),
                         "a statement registered under two classes")
        self.assertEqual(self.register["blocked_set_digest"], fvreg._digest_ids(ids))


class B3Arithmetic(unittest.TestCase):
    """The census closes exactly, and the two blocked buckets stay two."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
        cls.census = cls.register["b3_census"]
        cls.preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))

    def test_the_five_buckets_close_at_the_mute_set(self) -> None:
        total = (self.census["transliterable"] + self.census["covered"]
                 + self.census[fvreg.MATHLIB_BUCKET]
                 + self.census[fvreg.NO_ROW_BUCKET])
        self.assertEqual(total, self.preview["b0a"]["totals"]["mute"])
        self.assertEqual(total, 10605)
        self.assertEqual(total, self.census["total"])

    def test_the_two_blocked_buckets_are_two_numbers(self) -> None:
        """Never summed: a budget consequence and a design consequence."""
        self.assertIn(fvreg.MATHLIB_BUCKET, self.census)
        self.assertIn(fvreg.NO_ROW_BUCKET, self.census)
        self.assertNotIn("registered_blocked", self.census)
        self.assertGreater(self.census[fvreg.MATHLIB_BUCKET], 0)
        self.assertGreater(self.census[fvreg.NO_ROW_BUCKET], 0)

    def test_the_blocked_buckets_account_for_the_residue_the_oracle_lost(self) -> None:
        residue = self.preview["b0a"]["totals"]["residue"]
        blocked = (self.census[fvreg.MATHLIB_BUCKET]
                   + self.census[fvreg.NO_ROW_BUCKET])
        self.assertEqual(blocked, residue - self.census["covered"])
        self.assertEqual(blocked, self.register["blocked_total"])

    def test_the_covered_set_is_the_eligible_set_less_what_the_table_refuses(
            self) -> None:
        refused_though_eligible = sum(
            entry["blocking_count"] for entry in self.register["entries"]
            if entry["register_id"] in {"coercion", "unsupported_numeral",
                                        "noncanonical_numeral"})
        self.assertEqual(self.census["covered"],
                         self.preview["b0bc"]["accepted"] - refused_though_eligible)

    def test_the_prereg_quotes_the_registers_numbers(self) -> None:
        """The prereg's preview and the register cannot disagree in silence."""
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        b3 = prereg["b0_preview_2026_08_24"]["b3_preview"]
        for field in ("transliterable", "covered", fvreg.MATHLIB_BUCKET,
                      fvreg.NO_ROW_BUCKET, "total"):
            with self.subTest(field=field):
                self.assertEqual(b3[field], self.census[field])


class ClassesWereMeasuredNotAuthored(unittest.TestCase):
    """The discipline that retired the design's first-draft blocklist."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
        cls.preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
        cls.rejected = [row for row in cls.preview["statements"]
                        if not row["accepted"]]

    def test_the_head_list_is_the_one_the_oracle_itself_reported(self) -> None:
        """A hand-widened head list turns this red."""
        measured = fvreg.oracle_unknown_heads(self.rejected)
        self.assertEqual(self.register["oracle_unknown_heads"], measured)
        self.assertIn("Real.sqrt", measured)
        self.assertIn("Nat.Prime", measured,
                      "the measured list finds what an authored one missed")

    def test_the_whole_register_re_derives_from_the_committed_tree(self) -> None:
        rebuilt = fvreg.build()
        self.assertEqual(rebuilt["blocked_set_digest"],
                         self.register["blocked_set_digest"])
        self.assertEqual(rebuilt["b3_census"], self.register["b3_census"])
        self.assertEqual([e["register_id"] for e in rebuilt["entries"]],
                         [e["register_id"] for e in self.register["entries"]])

    def _build_from(self, preview: dict) -> dict:
        """Call the real `build()` against a mutated preview.

        The earlier version of these tests re-implemented the guard inside the
        test and asserted its own copy raised, which is a test of the test. The
        builder reads its preview from a path, so the mutation goes through a
        temporary file and `build()` runs unmodified — the guard that fires is
        the shipped one.
        """
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "preview.json"
            path.write_text(json.dumps(preview, ensure_ascii=False),
                            encoding="utf-8", newline="\n")
            return fvreg.build(preview_path=path)

    def test_the_real_builder_accepts_the_committed_preview(self) -> None:
        """The control for the two injections below: unmutated, it builds."""
        rebuilt = self._build_from(self.preview)
        self.assertEqual(rebuilt["blocked_set_digest"],
                         self.register["blocked_set_digest"])

    def test_a_class_with_no_committed_reason_refuses(self) -> None:
        """An entry with a count and no reason is a code name, not an inventory."""
        preview = json.loads(json.dumps(self.preview))
        original = fvreg._ENTRY_PROSE.pop("typeclass_instance_absent")
        try:
            with self.assertRaises(fvreg.RegisterError) as caught:
                self._build_from(preview)
        finally:
            fvreg._ENTRY_PROSE["typeclass_instance_absent"] = original
        self.assertIn("no committed entry prose", str(caught.exception))

    def test_a_census_that_does_not_close_refuses(self) -> None:
        """B3's arithmetic is a gate in the builder, not a claim in the file."""
        preview = json.loads(json.dumps(self.preview))
        preview["b0a"]["totals"]["transliterable"] += 1
        with self.assertRaises(fvreg.RegisterError) as caught:
            self._build_from(preview)
        self.assertIn("B3 does not close", str(caught.exception))

    def test_a_statement_registered_twice_refuses(self) -> None:
        """Two classes over one statement would double-count the silence.

        Injected by giving one already-blocked statement a duplicate row under
        a different corpus, so `classify` files the same id twice.
        """
        preview = json.loads(json.dumps(self.preview))
        rejected = next(row for row in preview["statements"]
                        if not row["accepted"])
        preview["statements"].append(dict(rejected))
        with self.assertRaises(fvreg.RegisterError):
            self._build_from(preview)

    def test_the_interpretation_absent_set_is_the_branch_clauses_own(self) -> None:
        """Branch (ii) was taken, so exactly those corpora carry that reason."""
        entry = {e["register_id"]: e for e in self.register["entries"]}[
            "prop_interpretation_absent"]
        self.assertEqual(set(entry["per_corpus"]), set(fvreg.PROP_CORPORA))
        self.assertEqual(entry["blocking_count"], 75)
        self.assertEqual(self.register["prop_branch"], "branch_ii")


class B4Ordering(unittest.TestCase):
    """Frozen first. The register precedes any render, and nothing renders yet."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))

    def test_the_register_is_frozen_in_the_prereg(self) -> None:
        frozen = {row["path"]: row for row in self.prereg["frozen"]}
        for path in ("data/foreign_voice/register.json",
                     "scripts/foreign_voice_register.py"):
            with self.subTest(path=path):
                self.assertIn(path, frozen)
                self.assertEqual(_sha256_lf(ROOT / path), frozen[path]["sha256_lf"])

    def test_nothing_is_pending_any_more(self) -> None:
        """Every artifact §10 orders before the renderer now exists and is pinned."""
        self.assertEqual(self.prereg["pending"], [])

    def test_no_renderer_exists_yet(self) -> None:
        """B4: freezing the register is a PRECONDITION of rendering anything."""
        self.assertFalse((ROOT / "scripts" / "foreign_voice.py").exists())
        self.assertFalse(
            (ROOT / "experiments" / "foreign_voice_rate.json").exists())


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
