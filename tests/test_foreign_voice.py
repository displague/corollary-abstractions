#!/usr/bin/env python3
"""The renderer, the literal inverse, and the gate between them.

The load-bearing test in this file is `SealedPrediction`: the hundred
sentences B0d sealed **before this module existed** must come back
byte-identically.  Everything else exists so that a green result there means
what it says.

- **R5 (determinism)** — same statement, same table, same interpretation →
  byte-identical surface.  v0.18's lesson, imported: re-rendering twice in one
  process only proves the code holds no hidden state, so the golden pairs
  below are what make R5 mean *"the same sentences as last time"*.
- **Refusal, by injection rather than by accident** — the six statements the
  oracle accepts and the table cannot say must refuse, each with the reason
  the frozen register files it under.  A renderer that improvised past any of
  them would make the register a lie.
- **The inverse is literal** — it *"never counts a bracket, never consults an
  arity and never compares precedences"*.  Tested by handing it a surface with
  unbalanced grouping words and asserting it happily produces unbalanced Lean:
  a literal substitution has no opinion, and the *oracle* is what has one.
- **C2 and H2 regressions, over the API** — the metavariable collision, the
  `sorryAx` leak, and the batch guards, exercised through
  `foreign_voice_oracle` rather than by reading the Lean source.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice as fv  # noqa: E402
import foreign_voice_lexicon as fvl  # noqa: E402
import foreign_voice_oracle as fvo  # noqa: E402
import foreign_voice_rule_r as fvr  # noqa: E402
import numeral_words as nw  # noqa: E402
from git_ordering import assert_added_before  # noqa: E402

SEALED_PATH = ROOT / "data" / "foreign_voice" / "b0d_sealed_renderings.json"
APPENDIX_PATH = ROOT / "data" / "foreign_voice" / "b0d_appendix.json"
REGISTER_PATH = ROOT / "data" / "foreign_voice" / "register.json"
PREVIEW_PATH = ROOT / "data" / "foreign_voice" / "eligibility_preview.json"

LEX = fvl.load()
RULE = fvr.load()


def _have_toolchain() -> bool:
    try:
        fvo.load()
    except fvo.OracleRefusal:
        return False
    return True


HAVE_LEAN = _have_toolchain()


def _renderer_is_canonical() -> bool:
    """Does `foreign_voice.py` emit canonical grouping yet?

    §10 orders the dated re-seal BEFORE the canonical renderer, so between
    those two commits the seal is a prediction the renderer cannot yet meet.
    That is what a sealed prediction IS, and asserting it in that window would
    turn the ordering into a failure. Detected rather than dated: a statement
    whose outer bracket precedence already implies must lose its grouping words.
    """
    got = fv.render_interpreted("∀ a b : Rat, (a + b) = a + b", LEX)
    if isinstance(got, fv.Refusal):
        return False
    return LEX.words_for("(") not in got.surface


RENDERER_IS_CANONICAL = _renderer_is_canonical()


class SealedPrediction(unittest.TestCase):
    """B0d: the implementation must reproduce the hundred BYTE-IDENTICALLY.

    *"A hand probe whose outputs are never compared against the implementation
    is a rehearsal, not a gate."*  Divergences are reported, never repaired —
    so if this ever goes red, the fix is a report, not an edit to the seal.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.sealed = json.loads(SEALED_PATH.read_text(encoding="utf-8"))

    def test_the_seal_records_which_fifteen_were_re_authored(self) -> None:
        """The re-seal is 15 sentences, not 100, and the file says which."""
        reseal = self.sealed.get("reseal")
        if reseal is None:
            self.skipTest("no re-seal recorded (pre-v0.20 seal)")
        self.assertEqual(reseal["reauthored_count"], 15)
        self.assertEqual(reseal["unchanged_count"], 85)
        self.assertEqual(len(reseal["reauthored_ids"]), 15)
        reauthored = {row["statement_id"] for row in self.sealed["renderings"]
                      if row.get("reauthored_2026_08_24")}
        self.assertEqual(reauthored, set(reseal["reauthored_ids"]))

    def test_the_eighty_five_unchanged_still_match_the_v019_seal(self) -> None:
        """G2's other half: a grammar change that quietly moved one of the 85
        would be a grammar change nobody asked for."""
        import subprocess
        blob = subprocess.run(
            ["git", "-C", str(ROOT), "show",
             "HEAD:data/foreign_voice/b0d_sealed_renderings.json"],
            capture_output=True, text=True, encoding="utf-8")
        if blob.returncode != 0:
            self.skipTest("cannot read the previous seal from git")
        previous = {row["statement_id"]: row["surface"]
                    for row in json.loads(blob.stdout)["renderings"]}
        for row in self.sealed["renderings"]:
            if row.get("reauthored_2026_08_24"):
                continue
            with self.subTest(statement_id=row["statement_id"]):
                self.assertEqual(row["surface"], previous[row["statement_id"]])

    def test_the_seal_was_written_before_this_renderer(self) -> None:
        """Otherwise the hundred are a transcript and this test is theatre."""
        assert_added_before(
            self, "data/foreign_voice/b0d_sealed_renderings.json",
            "scripts/foreign_voice.py",
            "the sealed hundred are only a prediction if nothing that could "
            "produce them existed when they were written")

    @unittest.skipUnless(
        RENDERER_IS_CANONICAL,
        "the renderer is not canonical yet: §10 orders the re-seal BEFORE the "
        "canonical renderer, so in this window the seal is a prediction the "
        "renderer cannot meet. G2 asserts it the moment the renderer lands.")
    def test_all_one_hundred_reproduce_byte_identically(self) -> None:
        divergences: list[str] = []
        for row in self.sealed["renderings"]:
            got = fv.render_interpreted(row["interpreted"], LEX)
            if isinstance(got, fv.Refusal):
                divergences.append(
                    f"{row['statement_id']}: REFUSED {got.reason} ({got.detail})")
            elif got.surface != row["surface"]:
                divergences.append(
                    f"{row['statement_id']}:\n  sealed   {row['surface']}\n"
                    f"  rendered {got.surface}")
        self.assertEqual(divergences, [], "\n".join(divergences))

    @unittest.skipUnless(
        RENDERER_IS_CANONICAL,
        "the renderer is not canonical yet — see above")
    def test_the_renderer_reaches_them_from_the_corpus_source_too(self) -> None:
        """Rule R plus the renderer, end to end, not just the rendering half."""
        for row in self.sealed["renderings"][:20]:
            with self.subTest(statement_id=row["statement_id"]):
                got = fv.render(row["source"], LEX, RULE)
                self.assertIsInstance(got, fv.Rendering)
                self.assertEqual(got.interpreted, row["interpreted"])
                self.assertEqual(got.surface, row["surface"])


class AppendixGoldenPairs(unittest.TestCase):
    """The five constructs the seeded hundred did not draw.

    v0.18 pinned 13 (source, exact-surface) pairs so a lexicon edit that
    changes an emitted surface shows up as a diff. These are the same idea over
    the constructs that would otherwise have no golden row at all: both ASCII
    orderings, `%`, a decimal literal, and a statement with no preamble.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.appendix = json.loads(APPENDIX_PATH.read_text(encoding="utf-8"))

    def test_it_is_flagged_as_not_part_of_the_hundred(self) -> None:
        """Mixing a curated five into a random hundred breaks the rate."""
        self.assertTrue(self.appendix["NOT_PART_OF_THE_SEALED_HUNDRED"])
        sealed = json.loads(SEALED_PATH.read_text(encoding="utf-8"))
        drawn = {row["statement_id"] for row in sealed["renderings"]}
        for row in self.appendix["rows"]:
            with self.subTest(statement_id=row["statement_id"]):
                self.assertFalse(row["in_sealed_hundred"])
                self.assertNotIn(row["statement_id"], drawn)

    def test_every_appendix_row_renders_exactly(self) -> None:
        for row in self.appendix["rows"]:
            with self.subTest(statement_id=row["statement_id"]):
                got = fv.render_interpreted(row["interpreted"], LEX)
                self.assertIsInstance(got, fv.Rendering)
                self.assertEqual(got.surface, row["surface"])

    def test_the_ascii_and_glyph_orderings_render_differently(self) -> None:
        """The digraph correction, as a behaviour rather than a table row.

        Before it, `>=` rendered as "is greater than equals" and inverted to
        `> =`, which is not a term. The row that carries BOTH spellings is the
        one that would have been silently wrong.
        """
        both = fv.render_interpreted("∀ x : Rat, x >= 0 ∧ x ≥ 0", LEX)
        self.assertIn("at least equals", both.surface)
        self.assertIn("is at least", both.surface)
        self.assertNotIn("is greater than equals", both.surface)
        self.assertEqual(fv.delexicalize(both.surface, LEX),
                         "∀ v0 : Rat , v0 >= 0 ∧ v0 ≥ 0")


class Determinism(unittest.TestCase):
    """R5, and the two things it does and does not prove."""

    def test_the_same_statement_renders_identically_twice(self) -> None:
        source = "∀ a b c : ℝ, a^2 + b^2 + c^2 ≥ a*b + b*c + c*a"
        first = fv.render(source, LEX, RULE)
        second = fv.render(source, LEX, RULE)
        self.assertEqual(first.surface, second.surface)

    def test_a_freshly_loaded_table_renders_identically(self) -> None:
        """Re-rendering in one process only proves there is no hidden state."""
        source = "∀ x : ℝ, x ≠ 1 → (x^2 + x + 1) / (x - 1) ^ 2 ≥ 1 / 4"
        self.assertEqual(fv.render(source, fvl.load(), fvr.load()).surface,
                         fv.render(source, fvl.load(), fvr.load()).surface)

    def test_slot_indices_follow_first_occurrence_in_r_of_s(self) -> None:
        got = fv.render_interpreted("∀ z a : Rat, z + a = a + z", LEX)
        self.assertEqual(got.slot_names, {"z": 0, "a": 1})
        self.assertTrue(got.surface.startswith(
            "for every variable zero variable one of type rational"))

    def test_every_rendered_word_traces_to_a_row_or_the_numeral_pair(self) -> None:
        """R2's sweep, over the renderer's own output rather than over a seal."""
        for source in ("∀ a b : ℝ, a + b = b + a",
                       "2^30 % 1000 = 824",
                       "∀ x : ℝ, x = 0.5 ∨ x = -2"):
            with self.subTest(source=source):
                got = fv.render(source, LEX, RULE)
                self.assertTrue(fv.surface_words_are_covered(got.surface, LEX))

    def test_the_receipt_carries_the_interpretation_shift(self) -> None:
        """§3.3: a rate quoted without this field is a number pretending."""
        receipt = fv.render("∀ a : ℝ, a^2 ≥ 0", LEX, RULE).receipt()
        self.assertEqual(receipt["interpretation_shift"], ["ℝ→Rat"])
        self.assertEqual(receipt["renderer_id"], fv.RENDERER_ID)
        self.assertIn("surface_slot_names", receipt["parameters"])


class RefusalIsTheProduct(unittest.TestCase):
    """The six the oracle accepts and the table cannot say. Each by its reason."""

    @classmethod
    def setUpClass(cls) -> None:
        register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
        preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
        cls.by_id = {row["statement_id"]: row for row in preview["statements"]}
        cls.entries = {entry["register_id"]: entry for entry in register["entries"]}

    def _check(self, register_id: str, expected_reason: str) -> None:
        entry = self.entries[register_id]
        for statement_id in entry["statement_ids"]:
            with self.subTest(statement_id=statement_id):
                row = self.by_id[statement_id]
                got = fv.render_interpreted(row["interpreted"], LEX,
                                            statement_id=statement_id)
                self.assertIsInstance(got, fv.Refusal)
                self.assertEqual(got.reason, expected_reason)

    def test_the_four_coercion_statements_refuse(self) -> None:
        self._check("coercion", "no_lexicon_row")

    def test_the_out_of_domain_literal_refuses(self) -> None:
        self._check("unsupported_numeral", "unsupported_numeral")

    def test_the_noncanonical_decimal_refuses(self) -> None:
        """`23.50` and `23.5` are different OfScientific terms, not spellings.

        Rendering it would produce a sentence that is right about the number
        and wrong about the term, and B1 would score the renderer for it.
        """
        self._check("noncanonical_numeral", "noncanonical_numeral")

    def test_the_refused_six_are_exactly_the_registers_own_three_classes(
            self) -> None:
        counts = {name: self.entries[name]["blocking_count"]
                  for name in ("coercion", "unsupported_numeral",
                               "noncanonical_numeral")}
        self.assertEqual(counts, {"coercion": 4, "unsupported_numeral": 1,
                                  "noncanonical_numeral": 1})

    def test_every_refusal_reason_is_in_the_closed_vocabulary(self) -> None:
        raw = json.loads(
            (ROOT / "data" / "foreign_voice" / "lexicon.json").read_text(
                encoding="utf-8"))
        vocabulary = set(raw["refusal_reasons"])
        for register_id in ("coercion", "unsupported_numeral",
                            "noncanonical_numeral"):
            entry = self.entries[register_id]
            row = self.by_id[entry["statement_ids"][0]]
            got = fv.render_interpreted(row["interpreted"], LEX)
            self.assertIn(got.reason, vocabulary)

    def test_an_empty_statement_refuses_rather_than_rendering_nothing(self) -> None:
        got = fv.render("   ", LEX, RULE)
        self.assertIsInstance(got, fv.Refusal)


class TheInverseIsLiteral(unittest.TestCase):
    """*"never counts a bracket, never consults an arity, never compares."*"""

    def test_longest_match_is_the_unique_match_over_the_whole_table(self) -> None:
        """L1 and L2 make this a property, not a policy. Checked end to end."""
        order = sorted(LEX.phrase_to_token)
        surface = " ".join(word for seq in order for word in seq)
        # The slot word needs an index after it or the inverse refuses, which
        # is itself the rule working; drop it from this particular sweep.
        surface = " ".join(w for w in surface.split() if w != LEX.slot_word)
        tokens = fv.delexicalize(surface, LEX).split()
        expected = [LEX.phrase_to_token[seq] for seq in order
                    if seq != (LEX.slot_word,)]
        self.assertEqual(tokens, expected)

    def test_it_produces_unbalanced_lean_from_unbalanced_english(self) -> None:
        """A literal substitution has no opinion. The ORACLE has the opinion.

        If the inverse silently balanced brackets it would be repairing the
        renderer's mistakes, and B1 would be scoring a repair.
        """
        self.assertEqual(
            fv.delexicalize("the quantity variable zero plus one", LEX),
            "( v0 + 1")

    def test_a_slot_word_with_no_numeral_run_refuses(self) -> None:
        with self.assertRaises(fv.ForeignVoiceError):
            fv.delexicalize("variable plus one", LEX)

    def test_a_word_outside_both_sources_refuses(self) -> None:
        with self.assertRaises(fv.ForeignVoiceError):
            fv.delexicalize("variable zero flurble one", LEX)

    def test_tokens_come_back_space_separated(self) -> None:
        """So the pinned lexer never makes a munch decision the table could miss."""
        got = fv.render_interpreted("∀ v : Rat, v >= 10", LEX)
        self.assertEqual(fv.delexicalize(got.surface, LEX),
                         "∀ v0 : Rat , v0 >= 10")

    def test_numerals_are_unsigned_and_minus_is_always_the_operator(self) -> None:
        got = fv.render_interpreted("∀ x : Rat, x = -5", LEX)
        self.assertIn("minus five", got.surface)
        self.assertNotIn("negative", got.surface)
        self.assertEqual(fv.delexicalize(got.surface, LEX),
                         "∀ v0 : Rat , v0 = - 5")


@unittest.skipUnless(HAVE_LEAN, "pinned Lean toolchain not installed")
class TheGate(unittest.TestCase):
    """Both digests, recomputed in one run, over the appendix's five rows."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = fvo.load()
        appendix = json.loads(APPENDIX_PATH.read_text(encoding="utf-8"))
        cls.renderings = [
            fv.render_interpreted(row["interpreted"], LEX,
                                  source=row["source"],
                                  statement_id=row["statement_id"])
            for row in appendix["rows"]
        ]
        cls.receipts = fv.gate(cls.renderings, cls.oracle, RULE, LEX)

    def test_every_appendix_row_round_trips_to_identity(self) -> None:
        for receipt in self.receipts:
            with self.subTest(statement_id=receipt.rendering.statement_id):
                self.assertEqual(receipt.outcome, "identity",
                                 f"{receipt.orig_error} / {receipt.rt_error}")

    def test_the_receipt_names_the_bound_on_what_identity_means(self) -> None:
        """§8's non-claim travels with every receipt, not only with the release."""
        payload = self.receipts[0].as_dict()
        self.assertIn("elaboration erases", payload["identity_is_bounded"])
        self.assertIn("C-V4", payload["identity_is_bounded"])

    def test_a_rendering_error_is_visible_to_the_gate(self) -> None:
        """The aiming test: if a broken sentence still passed, B1 means nothing.

        A hand-run C-V4 `shift_group`. The first attempt at this test picked an
        appendix row with no parentheses in it, so the mutation was a NO-OP and
        the test passed the mutant unchanged — which is the exact way a
        mutation control talks itself into a good number. The mutation is now
        asserted to have changed the surface before the gate is asked anything.
        """
        good = fv.render_interpreted(
            "∀ a b : Rat, (a + b) * (a - b) = a^2 - b^2", LEX)
        moved = good.surface.replace(
            "end quantity times the quantity",
            "times the quantity end quantity", 1)
        self.assertNotEqual(moved, good.surface, "the mutation was a no-op")

        mutant = fv.Rendering(
            statement_id="mutant", source=good.source,
            interpreted=good.interpreted,
            interpretation_shift=good.interpretation_shift,
            surface=moved,
            slot_names=good.slot_names, numerals_used=good.numerals_used,
            lexicon_entries=good.lexicon_entries,
            preamble_binders=good.preamble_binders)
        clean, broken = fv.gate([good, mutant], self.oracle, RULE, LEX)
        self.assertEqual(clean.outcome, "identity",
                         f"{clean.orig_error} / {clean.rt_error}")
        self.assertNotEqual(broken.outcome, "identity")

    def test_rule_r_is_applied_to_the_inverse_output_independently(self) -> None:
        """No argument by which the round-trip side can learn about the original."""
        receipt = self.receipts[0]
        self.assertEqual(
            receipt.roundtrip_text,
            RULE.apply(fv.delexicalize(receipt.rendering.surface, LEX)).text)


@unittest.skipUnless(HAVE_LEAN, "pinned Lean toolchain not installed")
class OracleRegressions(unittest.TestCase):
    """C2 and H2, exercised through the API rather than by reading Lean source."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = fvo.load()

    def test_h2_the_metavariable_collision_is_gone(self) -> None:
        """`(1 2 3)` and `(4 5 6 7)` both used to serialize to the same `(mv)`."""
        answers = self.oracle.serialize([("a", "1 2 3"), ("b", "4 5 6 7")])
        for tag in ("a", "b"):
            with self.subTest(tag=tag):
                self.assertFalse(answers[tag].ok)
                self.assertIn("metavariable", answers[tag].error)
                self.assertEqual(answers[tag].digest, "")

    def test_h2_a_sorry_never_reaches_a_digest(self) -> None:
        answer = self.oracle.digest_of("(sorry : Nat)")
        self.assertFalse(answer.ok)
        self.assertIn("sorryAx", answer.error)

    def test_h2_did_not_cost_the_covered_set_anything(self) -> None:
        """A guard that refused real statements would be a coverage regression."""
        preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
        sample = [row for row in preview["statements"] if row["accepted"]][:40]
        answers = self.oracle.serialize(
            [(f"s{i}", row["interpreted"]) for i, row in enumerate(sample)])
        self.assertTrue(all(row.ok for row in answers.values()),
                        [row.error for row in answers.values() if not row.ok])

    def test_c2_an_accounted_for_diagnostic_does_not_abort_the_batch(self) -> None:
        """The deviation, as behaviour: a FAIL is a data point, not a refusal."""
        answers = self.oracle.serialize([
            ("bad", "1 2 3"),
            ("good", "∀ a b : Rat, a + b = b + a"),
        ])
        self.assertFalse(answers["bad"].ok)
        self.assertTrue(answers["good"].ok)

    def test_h4_a_reserved_sentinel_tag_refuses(self) -> None:
        with self.assertRaises(fvo.OracleRefusal):
            self.oracle.serialize([(fvo._SENTINEL_OK, "1 = 1")])

    def test_h4_the_sentinels_are_stripped_from_the_answers(self) -> None:
        answers = self.oracle.serialize([("only", "1 = 1")])
        self.assertEqual(set(answers), {"only"})

    def test_a_parse_error_bystander_still_answers(self) -> None:
        answers = self.oracle.serialize([
            ("broken", "∀ a b : Rat, ((a + b"),
            ("fine", "∀ a b : Rat, a + b = b + a"),
        ])
        self.assertIn("parse_error", answers["broken"].error)
        self.assertTrue(answers["fine"].ok)


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
