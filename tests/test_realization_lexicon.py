#!/usr/bin/env python3
"""Gates on the prereg artifacts: R2b, the longest-match rule, C-R3.

These tests run against `data/realization/lexicon.json`,
`scripts/numeral_words.py` and `experiments/realization_prereg.json` — the
three things DESIGN-sans-template-rendering §10 registers *before*
`realize_term.py` exists.  Nothing here imports the realizer; if it did, the
preregistration order would be a formality.

What each block is for:

- **R2b (bijectivity)** — the design says a table that is not injective in
  either direction *refuses at load*.  So these tests inject a duplicate and
  assert the refusal, in both directions, rather than asserting a property of
  the committed table alone.
- **Longest-match unambiguity** — checked *constructively over the whole
  table*, not sampled: every ordered pair of phrases is compared for the
  prefix relation, and a single surface built by concatenating **every** row's
  phrase in order is decoded back to exactly that row sequence.
- **The numeral pair** — round trips in both directions, including negatives,
  decimals and fractions, plus the refusals that keep the accepted language
  equal to the emitted language.
- **C-R3 (the tautology probe)** — the recorded digests are re-computed
  against the working tree.  This is the test that goes red if the parser was
  edited to make the realizer work.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import numeral_words as nw  # noqa: E402
import realization_lexicon as rl  # noqa: E402

LEXICON_PATH = ROOT / "data" / "realization" / "lexicon.json"
PREREG_PATH = ROOT / "experiments" / "realization_prereg.json"


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class LexiconLoadTests(unittest.TestCase):
    """R2b — bijectivity, enforced at load rather than asserted about a file."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        cls.lex = rl.load(LEXICON_PATH)

    def test_committed_lexicon_loads(self) -> None:
        self.assertEqual(self.lex.lexicon_id, "realization.lexicon.v1")
        self.assertEqual(len(self.lex.phrase_to_token), len(self.lex.key_to_phrase))
        self.assertEqual(self.lex.slot_marker, "variable")

    def test_r2b_refuses_two_heads_sharing_one_phrase(self) -> None:
        """Forward injectivity: one word sequence may not read as two heads."""
        injured = copy.deepcopy(self.raw)
        injured["call_heads"]["SIN"] = injured["call_heads"]["sin"]
        with self.assertRaisesRegex(rl.LexiconError, "B2"):
            rl.build(injured)

    def test_r2b_refuses_two_keys_sharing_one_token(self) -> None:
        """Reverse injectivity: two rows may not emit the same token.

        `E[]` already emits the token `E`, so a head literally named `E` is a
        real collision and not a contrived one.
        """
        injured = copy.deepcopy(self.raw)
        injured["call_heads"]["E"] = "the plain expectation of"
        with self.assertRaisesRegex(rl.LexiconError, "B3"):
            rl.build(injured)

    def test_r2b_refuses_duplicate_json_keys(self) -> None:
        """A duplicate key must refuse, not silently last-wins."""
        import tempfile

        text = json.dumps(self.raw, indent=2, ensure_ascii=False)
        injected = text.replace(
            '"sin": "the sine of"',
            '"sin": "the sine of",\n    "sin": "the other sine of"',
            1,
        )
        self.assertNotEqual(
            injected, text, "fixture anchor not found in the committed lexicon"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lexicon.json"
            path.write_text(injected, encoding="utf-8")
            with self.assertRaisesRegex(rl.LexiconError, "B1"):
                rl.load(path)

    def test_r2b_both_compositions_are_the_identity(self) -> None:
        """§3: forward and reverse readings of every row compose to identity."""
        phrase_to_key = {v: k for k, v in self.lex.key_to_phrase.items()}
        self.assertEqual(len(phrase_to_key), len(self.lex.key_to_phrase))
        for key, phrase in self.lex.key_to_phrase.items():
            self.assertEqual(phrase_to_key[phrase], key)
            self.assertEqual(self.lex.key_to_phrase[phrase_to_key[phrase]], phrase)

    def test_r2b_refuses_a_numeral_word_in_a_phrase(self) -> None:
        injured = copy.deepcopy(self.raw)
        injured["operators"]["+"] = "plus one"
        with self.assertRaisesRegex(rl.LexiconError, "L2"):
            rl.build(injured)

    def test_r2b_refuses_a_big_operator_head_spelling(self) -> None:
        """B7: `min_x(..)` would re-parse as a big operator over the product."""
        injured = copy.deepcopy(self.raw)
        injured["call_heads"]["min_x"] = "the windowed minimum of"
        with self.assertRaisesRegex(rl.LexiconError, "B7"):
            rl.build(injured)

    def test_r2b_refuses_a_non_identifier_head_token(self) -> None:
        injured = copy.deepcopy(self.raw)
        injured["call_heads"]["9x"] = "the digit headed thing of"
        with self.assertRaisesRegex(rl.LexiconError, "B7"):
            rl.build(injured)

    def test_b7_refuses_an_operator_row_that_emits_an_identifier(self) -> None:
        """The hole a key-only B7 left open — 8910138's bug, respelled.

        `operator_tokens: {"neg": "negg"}` tokenizes cleanly and means a SLOT.
        The old check looked only at call-head keys, i.e. everywhere except
        the place the bug it was written for actually lived.
        """
        injured = copy.deepcopy(self.raw)
        injured["operator_tokens"]["neg"] = "negg"
        with self.assertRaisesRegex(rl.LexiconError, "B7"):
            rl.build(injured)

    def test_b7_refuses_a_token_the_frozen_tokenizer_splits(self) -> None:
        injured = copy.deepcopy(self.raw)
        injured["operator_tokens"]["inv"] = "//"
        with self.assertRaisesRegex(rl.LexiconError, "splits into"):
            rl.build(injured)

    def test_b7_refuses_a_head_spelled_like_a_slot_token(self) -> None:
        """A head named `V0` is indistinguishable from the first variable."""
        injured = copy.deepcopy(self.raw)
        injured["call_heads"]["V0"] = "the zeroth vee of"
        with self.assertRaisesRegex(rl.LexiconError, "B7"):
            rl.build(injured)

    def test_b7_refuses_a_slot_prefix_that_is_not_an_identifier(self) -> None:
        injured = copy.deepcopy(self.raw)
        injured["slot_marker"]["token_prefix"] = "9"
        with self.assertRaisesRegex(rl.LexiconError, "B7"):
            rl.build(injured)

    def test_b7_runs_over_every_emitted_token_not_only_keys(self) -> None:
        """The generalization itself: keys, values and the slot prefix alike."""
        for section, key, value in [
            ("operator_tokens", "neg", "negg"),
            ("operator_tokens", "inv", "wibble"),
        ]:
            with self.subTest(key=key):
                injured = copy.deepcopy(self.raw)
                injured[section][key] = value
                with self.assertRaisesRegex(rl.LexiconError, "B7"):
                    rl.build(injured)

    def test_the_committed_table_emits_the_glyphs_it_means(self) -> None:
        """The positive side of B7, so the gate is not vacuously satisfied."""
        self.assertEqual(self.lex.phrase_to_token[("the", "opposite", "of")], "-")
        self.assertEqual(self.lex.phrase_to_token[("divided", "by")], "/")
        self.assertEqual(self.lex.phrase_to_token[("plus",)], "+")
        self.assertEqual(self.lex.phrase_to_token[("give", "or", "take")], "±")


class LongestMatchTests(unittest.TestCase):
    """The reading rule the lexicon file documents, checked constructively."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        cls.lex = rl.load(LEXICON_PATH)

    def _decode(self, words: list[str]) -> list[tuple[str, ...]]:
        """The longest-match scan, written here independently of the inverter."""
        out: list[tuple[str, ...]] = []
        i = 0
        while i < len(words):
            widths = range(min(self.lex.max_phrase_words, len(words) - i), 0, -1)
            for width in widths:
                candidate = tuple(words[i:i + width])
                if candidate in self.lex.phrase_to_token:
                    out.append(candidate)
                    i += width
                    break
            else:
                raise AssertionError(f"no phrase matches at {words[i:]!r}")
        return out

    def test_l1_no_phrase_is_a_proper_prefix_of_another(self) -> None:
        """Every ordered pair, not a sample: 169 rows is 28,561 comparisons."""
        phrases = sorted(self.lex.phrase_to_token)
        for a in phrases:
            for b in phrases:
                if a == b:
                    continue
                self.assertNotEqual(
                    b[: len(a)], a,
                    f"{' '.join(a)!r} is a proper prefix of {' '.join(b)!r}",
                )

    def test_l2_no_phrase_word_is_a_numeral_word(self) -> None:
        for phrase in self.lex.phrase_to_token:
            for word in phrase:
                self.assertFalse(
                    nw.is_numeral_word(word),
                    f"{word!r} in {' '.join(phrase)!r} is numeral vocabulary",
                )

    def test_longest_match_decodes_the_whole_table_concatenated(self) -> None:
        """Constructive unambiguity: concatenate EVERY row, decode, get it back.

        Prefix-freeness makes this a proof rather than a sample — if the decode
        of the concatenation of all rows is the identity, no boundary anywhere
        in the table is ambiguous under longest match.
        """
        order = sorted(self.lex.phrase_to_token)
        words = [w for phrase in order for w in phrase]
        self.assertEqual(self._decode(words), order)

    def test_longest_match_prefers_the_longer_row(self) -> None:
        """A probe that the scan is longest-match and not first-match."""
        long_phrase = tuple("the capital sine of".split())
        self.assertIn(long_phrase, self.lex.phrase_to_token)
        self.assertEqual(self._decode(list(long_phrase)), [long_phrase])

    def test_every_claimed_head_has_a_row(self) -> None:
        """The coverage the file claims is the coverage it has."""
        claimed = self.raw["head_coverage"]
        self.assertEqual(claimed["canonical_ascii_parseable"]["uncovered"], 0)
        self.assertEqual(claimed["anonymized_template"]["uncovered"], 0)
        self.assertEqual(
            len(self.lex.call_heads),
            claimed["canonical_ascii_parseable"]["covered"]
            + claimed["anonymized_template"]["covered"] - 9,
            "the two head inventories overlap in exactly 9 spellings",
        )
        for head in claimed["anonymized_template"]["top_by_mass"]:
            self.assertTrue(self.lex.covers(head), head)

    def test_lexicon_file_is_lf_and_sorted(self) -> None:
        data = LEXICON_PATH.read_bytes()
        self.assertNotIn(b"\r\n", data, "lexicon.json must be committed with LF")
        doc = json.loads(data.decode("utf-8"))
        for section in ("structural", "operators", "relations", "call_heads"):
            keys = list(doc[section])
            self.assertEqual(keys, sorted(keys), f"{section} keys are not sorted")
        self.assertEqual(list(doc), sorted(doc), "top-level keys are not sorted")


class IntegerNumeralTests(unittest.TestCase):
    """The registered numeral pair, integer half."""

    CASES = [
        (0, "zero"),
        (7, "seven"),
        (13, "thirteen"),
        (20, "twenty"),
        (21, "twenty-one"),
        (100, "one hundred"),
        (824, "eight hundred twenty-four"),
        (1000, "one thousand"),
        (1101, "one thousand one hundred one"),
        (1_000_000, "one million"),
        (999_999_999, "nine hundred ninety-nine million nine hundred "
                      "ninety-nine thousand nine hundred ninety-nine"),
        (1_000_000_000, "one billion"),
        (-42, "negative forty-two"),
        (-1_000_000_007, "negative one billion seven"),
    ]

    def test_pinned_cases_both_directions(self) -> None:
        for value, words in self.CASES:
            with self.subTest(value=value):
                self.assertEqual(nw.int_to_words(value), words)
                self.assertEqual(nw.words_to_int(words), value)

    def test_round_trip_dense_sweep(self) -> None:
        for n in range(-1050, 1050):
            self.assertEqual(nw.words_to_int(nw.int_to_words(n)), n)

    def test_round_trip_sparse_sweep_to_the_domain_edge(self) -> None:
        n = 1
        while n < nw.MAX_INT:
            for probe in (n, n - 1, n + 1, -n):
                if abs(probe) < nw.MAX_INT:
                    self.assertEqual(nw.words_to_int(nw.int_to_words(probe)), probe)
            n *= 7
        self.assertEqual(
            nw.words_to_int(nw.int_to_words(nw.MAX_INT - 1)), nw.MAX_INT - 1
        )

    def test_refuses_outside_the_registered_domain(self) -> None:
        for bad in (nw.MAX_INT, -nw.MAX_INT, 10 ** 30):
            with self.subTest(bad=bad), self.assertRaises(nw.NumeralError):
                nw.int_to_words(bad)

    def test_reader_refuses_non_canonical_readings(self) -> None:
        """The reader must reject what the writer would never emit."""
        for bad in ("twenty ten", "one one", "hundred", "negative", "",
                    "one hundred hundred", "twenty-zero", "eleventy",
                    "zero one", "one thousand thousand"):
            with self.subTest(bad=bad), self.assertRaises(nw.NumeralError):
                nw.words_to_int(bad)


class DecimalNumeralTests(unittest.TestCase):
    """The registered numeral pair, decimal half."""

    CASES = [
        (0.5, "zero point five"),
        (0.375, "zero point three seven five"),
        (7.42, "seven point four two"),
        (26.125, "twenty-six point one two five"),
        (190.3676248,
         "one hundred ninety point three six seven six two four eight"),
        (-0.25, "negative zero point two five"),
    ]

    #: Every non-integer literal the parseable canonical_ascii corpus carries.
    CORPUS_DECIMALS = [0.2, 0.25, 0.28, 0.3, 0.375, 0.5, 0.6, 0.656, 0.75, 0.9,
                       1.2, 2.5, 5.75, 6.5, 7.42, 9.1, 21.16, 26.125, 33.5,
                       37.5, 190.3676248]

    def test_pinned_cases_both_directions(self) -> None:
        for value, words in self.CASES:
            with self.subTest(value=value):
                self.assertEqual(nw.number_to_words(value), words)
                self.assertEqual(nw.words_to_number(words), value)
                self.assertEqual(float(nw.words_to_numeral_token(words)), value)

    def test_round_trip_over_every_corpus_literal(self) -> None:
        for value in self.CORPUS_DECIMALS:
            with self.subTest(value=value):
                self.assertEqual(nw.words_to_number(nw.number_to_words(value)),
                                 value)

    def test_integral_floats_render_as_integers(self) -> None:
        self.assertEqual(nw.number_to_words(2.0), "two")
        self.assertEqual(nw.words_to_numeral_token("two"), "2")

    def test_refuses_scientific_notation(self) -> None:
        """The corpus's 76-digit lean_workbook literal has no sayable form."""
        for bad in (8.888888888888888e+75, 1e-30, float("inf")):
            with self.subTest(bad=bad), self.assertRaises(nw.NumeralError):
                nw.number_to_words(bad)

    def test_reader_refuses_non_canonical_decimals(self) -> None:
        for bad in ("zero point", "one point ten", "one point five zero"):
            with self.subTest(bad=bad), self.assertRaises(nw.NumeralError):
                nw.words_to_numeral_token(bad)


class FractionNumeralTests(unittest.TestCase):
    """The exact-value half: `scripts/evaluate.py` answers in Fractions."""

    CASES = [
        (Fraction(19, 13), "nineteen over thirteen"),
        (Fraction(1, 2), "one over two"),
        (Fraction(-19, 13), "negative nineteen over thirteen"),
        (Fraction(4, 1), "four"),
        (Fraction(-4, 1), "negative four"),
    ]

    def test_pinned_cases_both_directions(self) -> None:
        for value, words in self.CASES:
            with self.subTest(value=value):
                self.assertEqual(nw.fraction_to_words(value), words)
                self.assertEqual(nw.words_to_fraction(words), value)

    def test_round_trip_over_a_sweep(self) -> None:
        for numerator in range(-30, 31):
            for denominator in range(1, 18):
                value = Fraction(numerator, denominator)
                self.assertEqual(nw.words_to_fraction(nw.fraction_to_words(value)),
                                 value)

    def test_reader_refuses_non_canonical_input(self) -> None:
        for bad in ("two over four", "one over zero", "one over negative two"):
            with self.subTest(bad=bad), self.assertRaises(nw.NumeralError):
                nw.words_to_fraction(bad)

    def test_vocabulary_is_exactly_what_the_pair_emits(self) -> None:
        """L2 leans on this set being complete; check it against renderings."""
        emitted: set[str] = set()
        for n in list(range(-200, 201)) + [10 ** k for k in range(3, 15)]:
            emitted.update(nw.int_to_words(n).split())
        emitted.update(nw.number_to_words(0.375).split())
        emitted.update(nw.fraction_to_words(Fraction(19, 13)).split())
        for word in sorted(emitted):
            self.assertTrue(nw.is_numeral_word(word), word)


class TautologyProbeTests(unittest.TestCase):
    """C-R3 — the parser is byte-frozen before the realizer is written."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))

    def test_frozen_digests_match_the_tree(self) -> None:
        """If implementing the realizer forced a parser change, this goes red.

        Re-aimed 2026-08-24 by the dated amendment
        `realization.prereg.v1.amendment.transliteration-2026-08-24`
        (ROADMAP-v0.19 item 3a, the transliteration lane). A row the amendment
        retired for future comparisons is checked against the SUCCESSOR pin the
        amendment names, not against its own historical digest: the row records
        what experiments/realization_rate.json was measured under, the tree has
        legitimately moved past it, and asking the tree to match it would be
        asking a closed question.

        The retirement is followed, never skipped. A retired row still has to
        agree with a live pin somewhere, and a marker naming an amendment this
        file does not record fails loudly rather than dropping the check. That
        is the difference between a pin retired in writing and a pin deleted.
        """
        self.assertEqual(self.prereg["prereg_id"], "realization.prereg.v1")
        frozen = {row["role"]: row for row in self.prereg["frozen"]}
        self.assertLessEqual(
            {"parser", "numeral_pair", "lexicon", "lexicon_loader"},
            set(frozen),
            "the four artifacts frozen before the realizer must all be recorded",
        )
        amendments = {entry["amendment_id"]: entry
                      for entry in self.prereg.get("amendments", ())}
        for role, row in frozen.items():
            with self.subTest(role=role):
                path = ROOT / row["path"]
                self.assertTrue(path.exists(), f"{role}: {row['path']} is missing")
                marker = row.get("retired_for_future_comparisons")
                if marker is None:
                    self.assertEqual(
                        _sha256_lf(path), row["sha256_lf"],
                        f"C-R3 VOID: {row['path']} changed after the "
                        f"preregistration commit. The independence claim needs "
                        f"its own review naming the reason.",
                    )
                    continue
                named = [entry for key, entry in amendments.items()
                         if key.endswith(marker["amendment"])]
                self.assertEqual(
                    len(named), 1,
                    f"{row['path']} claims retirement by amendment "
                    f"{marker['amendment']!r}, which this file does not record",
                )
                successor = json.loads(
                    (ROOT / named[0]["successor_prereg"]["path"]).read_text(
                        encoding="utf-8"))
                live = {r["role"]: r for r in successor["frozen"]}[role]
                self.assertEqual(live["path"], row["path"])
                self.assertEqual(
                    _sha256_lf(path), live["sha256_lf"],
                    f"{row['path']} matches neither its retired pin nor the "
                    f"successor pin in {named[0]['successor_prereg']['path']}. "
                    f"A second undeclared change needs its own amendment.",
                )

    def test_records_the_parser_by_name(self) -> None:
        frozen = {row["role"]: row["path"] for row in self.prereg["frozen"]}
        self.assertEqual(frozen["parser"], "scripts/match_signatures.py")
        self.assertEqual(frozen["numeral_pair"], "scripts/numeral_words.py")
        self.assertEqual(frozen["lexicon"], "data/realization/lexicon.json")

    def test_the_inverter_row_dates_itself(self) -> None:
        """§7 records the inverter's digest *beside* the parser's.

        It cannot be in the commit that freezes the parser before the realizer
        exists, so when it appears it must carry the date that says so. While
        it is still absent, `pending` names it — either state is honest; a row
        that claims to predate the parser freeze would not be.
        """
        frozen = {row["role"]: row for row in self.prereg["frozen"]}
        pending = {row["path"]: row for row in self.prereg["pending"]}
        if "inverter" in frozen:
            self.assertEqual(frozen["inverter"]["path"], "scripts/realize_term.py")
            self.assertIn("recorded", frozen["inverter"])
            self.assertEqual(self.prereg["pending"], [])
        else:
            self.assertIn("scripts/realize_term.py", pending)
            self.assertEqual(pending["scripts/realize_term.py"]["role"], "inverter")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
