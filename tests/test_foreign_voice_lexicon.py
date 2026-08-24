#!/usr/bin/env python3
"""Gates on the foreign-voice preregistration artifacts: F1–F8, rule R, B7.

These tests run against `data/foreign_voice/lexicon.json`,
`data/foreign_voice/rule_r.json`, `data/foreign_voice/eligibility_preview.json`
and `experiments/foreign_voice_prereg.json` — the artifacts
DESIGN-foreign-voice §10 registers *before* `Serialize.lean` is written and
*before* any hand-rendering exists.  Nothing here imports a renderer, because
there is not one yet and the preregistration order is the point.

What each block is for:

- **F1–F8 (the load gate)** — the design says a table that fails any of them
  raises at load and *"nothing downstream gets a chance to work around it"*.
  So these tests **inject** a hole and assert the refusal, rather than
  asserting a property of the committed table alone.  Six injections, one per
  hole the authoring actually opened or the precedent warns about.
- **Longest-match unambiguity** — checked *constructively over the whole
  table*: every ordered pair of phrases is compared for the prefix relation,
  and a surface built by concatenating **every** row's phrase in order decodes
  back to exactly that row sequence.
- **Rule R** — the settings B5 will assert are asserted here as *committed
  settings*; the substitution's declared order-independence is checked rather
  than trusted; and the preamble is checked to be a pure function of the text.
- **Constructive coverage** — every one of the 2,319 oracle-eligible
  statements is tokenized with exactly this table's tokens, rule R's
  identifier grammar and the registered numeral pair.  The assertion is that
  the ONLY leftover is the construct the lexicon carries a refusal row for.
  This is the whole-table check, done over the corpus rather than sampled.
- **B7** — the recorded digests are recomputed against the working tree.  This
  is the test that goes red if the parser, the interpretation or the table was
  edited to make the oracle agree.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice_lexicon as fvl  # noqa: E402
import foreign_voice_rule_r as fvr  # noqa: E402
import numeral_words as nw  # noqa: E402
from git_ordering import (  # noqa: E402
    assert_absent_or_added_after,
    assert_added_before,
)

LEXICON_PATH = ROOT / "data" / "foreign_voice" / "lexicon.json"
RULE_PATH = ROOT / "data" / "foreign_voice" / "rule_r.json"
PREVIEW_PATH = ROOT / "data" / "foreign_voice" / "eligibility_preview.json"
PREREG_PATH = ROOT / "experiments" / "foreign_voice_prereg.json"


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class LexiconLoadTests(unittest.TestCase):
    """F1–F8, enforced at load rather than asserted about a file."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        cls.lex = fvl.load(LEXICON_PATH)

    def _injected(self, mutate) -> None:
        doc = copy.deepcopy(self.raw)
        mutate(doc)
        with self.assertRaises(fvl.ForeignLexiconError):
            fvl.build(doc, "<injected>")

    def test_committed_lexicon_loads(self) -> None:
        self.assertEqual(self.lex.lexicon_id, "foreign_voice.lexicon.v1")

    def test_f2_a_shared_phrase_refuses(self) -> None:
        """Forward injective: two constructors cannot say the same words."""
        self._injected(lambda d: d["relations"].__setitem__(
            "≠", d["relations"]["="]))

    def test_f3_a_shared_token_refuses(self) -> None:
        """Reverse injective — and the ONE way this table can break it.

        Every written row here is keyed by the token it emits, so two written
        rows cannot collide the way v0.18's `neg`/`-` did: that collision is
        designed out rather than legislated around (numerals are unsigned, so
        there is exactly one `-` row). The remaining hole is the row that is
        *generated* rather than written down — the slot marker, whose token is
        the bare prefix — and it is the same shape as commit 8910138's bug: a
        value, not a key. So that is what this injects.
        """
        doc = copy.deepcopy(self.raw)
        doc["types"][doc["slot_marker"]["token_prefix"]] = "the vee type"
        with self.assertRaises(fvl.ForeignLexiconError):
            fvl.build(doc, "<injected>")

    def test_f4_and_l1_a_prefix_phrase_refuses(self) -> None:
        """`is at` is a proper word-prefix of `is at most`; longest match cannot."""
        self._injected(lambda d: d["relations"].__setitem__("≈", "is at"))

    def test_l2_a_numeral_word_refuses(self) -> None:
        """`over` and `negative` are both words the numeral pair emits.

        Both spellings were tried during authoring — `/` as "over" and unary
        minus as "negative" — and both were caught here. The gate working is
        why the committed table says "divided by" and "minus".
        """
        self._injected(lambda d: d["operators"].__setitem__("/", "over"))
        self._injected(lambda d: d["operators"].__setitem__("+", "negative"))

    def test_f5_a_non_ascii_phrase_refuses(self) -> None:
        self._injected(lambda d: d["relations"].__setitem__("=", "équivaut à"))

    def test_f7_a_row_spelling_a_slot_refuses(self) -> None:
        """8910138's lesson in this dialect: the collision lives in a token."""
        self._injected(lambda d: d["types"].__setitem__("v0", "the first slot"))

    def test_f7_a_row_emitting_whitespace_refuses(self) -> None:
        """The inverse writes tokens space-separated; a token with a space is two."""
        self._injected(lambda d: d["types"].__setitem__("Nat Nat", "double natural"))

    def test_f7_a_numeric_token_refuses(self) -> None:
        self._injected(lambda d: d["types"].__setitem__("12", "a dozen"))

    def test_f8_a_construct_with_both_a_row_and_a_refusal_refuses(self) -> None:
        """One artifact would render it and the other would call it unspoken."""
        def mutate(doc: dict) -> None:
            doc["refusals"]["∧"] = {"construct": "conjunction",
                                    "reason": "no_lexicon_row"}
        self._injected(mutate)

    def test_f8_an_unknown_refusal_reason_refuses(self) -> None:
        def mutate(doc: dict) -> None:
            doc["refusals"]["↑"] = {"construct": "coercion", "reason": "too_hard"}
        self._injected(mutate)

    def test_f1_a_duplicate_key_refuses(self) -> None:
        text = LEXICON_PATH.read_text(encoding="utf-8")
        broken = text.replace('"lexicon_id":', '"lexicon_id": "x", "lexicon_id":', 1)
        with self.assertRaises(fvl.ForeignLexiconError):
            json.loads(broken, object_pairs_hook=fvl._load_pairs)


class LongestMatchTests(unittest.TestCase):
    """L1 and L2 checked constructively over the whole table, never sampled."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.lex = fvl.load(LEXICON_PATH)

    def test_no_phrase_is_a_prefix_of_another(self) -> None:
        seqs = sorted(self.lex.phrase_to_token)
        for i, seq in enumerate(seqs):
            for other in seqs[i + 1:]:
                if len(other) > len(seq):
                    self.assertNotEqual(
                        other[: len(seq)], seq,
                        f"L1: {' '.join(seq)!r} is a prefix of {' '.join(other)!r}")

    def test_no_phrase_word_is_a_numeral_word(self) -> None:
        for seq in self.lex.phrase_to_token:
            for word in seq:
                self.assertFalse(nw.is_numeral_word(word),
                                 f"L2: {word!r} is a numeral word")

    def test_every_row_decodes_out_of_a_concatenation_of_every_row(self) -> None:
        """The whole table, end to end, read back by longest match alone.

        Not a sample: the surface is every phrase in the table concatenated in
        a fixed order, and the decode must return exactly that row sequence.
        A table that needed lookahead would lose a row here.
        """
        order = sorted(self.lex.phrase_to_token)
        words: list[str] = []
        for seq in order:
            words.extend(seq)
        decoded: list[tuple[str, ...]] = []
        i = 0
        longest = self.lex.max_phrase_words
        while i < len(words):
            for size in range(min(longest, len(words) - i), 0, -1):
                candidate = tuple(words[i:i + size])
                if candidate in self.lex.phrase_to_token:
                    decoded.append(candidate)
                    i += size
                    break
            else:  # pragma: no cover - a failure here IS the assertion below
                self.fail(f"no phrase matches at word {i}: {words[i:i + 4]}")
        self.assertEqual(decoded, order)

    def test_the_slot_marker_is_a_row_like_any_other(self) -> None:
        """It is generated rather than written down, which is why it is gated."""
        self.assertIn(("variable",), self.lex.phrase_to_token)
        self.assertEqual(self.lex.slot_token(0), "v0")
        self.assertEqual(self.lex.slot_token(12), "v12")


class RuleRTests(unittest.TestCase):
    """The declared interpretation, and the settings B5 will assert."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = json.loads(RULE_PATH.read_text(encoding="utf-8"))
        cls.rule = fvr.load(RULE_PATH)

    def _injected(self, mutate) -> None:
        doc = copy.deepcopy(self.raw)
        mutate(doc)
        with self.assertRaises(fvr.RuleError):
            fvr.build(doc, "<injected>")

    def test_committed_rule_loads(self) -> None:
        self.assertEqual(self.rule.rule_id, "foreign_voice.rule_r.v1")

    def test_auto_implicit_is_off_as_a_committed_setting(self) -> None:
        """B5, and Correction 3's 680-of-1,000 is why it is not a flag."""
        self.assertFalse(self.rule.auto_implicit)
        self.assertFalse(self.rule.relaxed_auto_implicit)
        lines = self.rule.set_option_lines()
        self.assertIn("set_option autoImplicit false", lines)
        self.assertIn("set_option relaxedAutoImplicit false", lines)

    def test_auto_implicit_true_refuses(self) -> None:
        self._injected(lambda d: d["elaboration_settings"].__setitem__(
            "autoImplicit", True))

    def test_max_errors_reaches_the_command_line_not_the_source(self) -> None:
        """`set_option maxErrors` in the file does not take effect; -D does.

        This is not a style point. The frontend stops reporting after 100
        errors, and a batch prober that reads acceptance from the absence of a
        diagnostic then counts every later statement as accepted — measured on
        this tree, 2,982 eligible where the truth is 2,319.
        """
        self.assertEqual(self.rule.command_line_options(),
                         (f"-DmaxErrors={self.rule.max_errors}",))
        for line in self.rule.set_option_lines():
            self.assertNotIn("maxErrors", line)

    def test_the_substitution_is_order_independent(self) -> None:
        """The file claims it; the loader checks it; this checks the claim holds."""
        source = "∀ a : ℝ, ∃ b : ℤ, ∀ c : ℕ, ∃ d : ℚ, a + b + c + d = 0"
        forward = self.rule.substitute(source)
        self.assertEqual(self.rule.substitute(forward), forward)
        self.assertNotIn("ℝ", forward)
        self.assertIn("Rat", forward)
        self.assertIn("Int", forward)
        self.assertIn("Nat", forward)

    def test_a_substitution_that_reintroduces_a_key_refuses(self) -> None:
        self._injected(lambda d: d["type_substitutions"].__setitem__("ℝ", "ℤReal"))

    def test_a_preamble_type_outside_the_interpretation_refuses(self) -> None:
        self._injected(lambda d: d["preamble_rule"].__setitem__(
            "preamble_type", "Complex"))

    def test_an_unsorted_frozen_constant_list_refuses(self) -> None:
        def mutate(doc: dict) -> None:
            doc["frozen_constants"]["names"] = list(
                reversed(doc["frozen_constants"]["names"]))
        self._injected(mutate)

    def test_an_absent_prop_branch_decision_refuses(self) -> None:
        """The clause the design says must be decided at B0 time and recorded."""
        self._injected(lambda d: d["prop_branch"].__setitem__("decision", None))

    def test_the_prop_branch_is_recorded(self) -> None:
        self.assertEqual(self.rule.prop_branch, "branch_ii")

    def test_the_preamble_binds_free_names_sorted(self) -> None:
        applied = self.rule.apply("z + a = q")
        self.assertEqual(applied.preamble_binders, ("a", "q", "z"))
        self.assertEqual(applied.text, "∀ a q z : Rat, z + a = q")

    def test_a_bound_name_is_not_rebound(self) -> None:
        applied = self.rule.apply("∀ a b : ℝ, a + b = b + a")
        self.assertEqual(applied.preamble_binders, ())
        self.assertEqual(applied.text, "∀ a b : Rat, a + b = b + a")
        self.assertEqual(applied.interpretation_shift, ("ℝ→Rat",))

    def test_a_qualified_name_is_never_bound(self) -> None:
        """The rule, not a list, is what keeps Mathlib heads out of the preamble."""
        applied = self.rule.apply("Real.sqrt x ≥ 0")
        self.assertEqual(applied.preamble_binders, ("x",))
        self.assertNotIn("Real.sqrt :", applied.text)

    def test_a_bare_analytic_head_is_never_bound(self) -> None:
        applied = self.rule.apply("sin x + cos x = 1")
        self.assertEqual(applied.preamble_binders, ("x",))

    def test_r_is_a_pure_function_of_the_text(self) -> None:
        source = "∀ a b c : ℝ, a^2 + b^2 + c^2 ≥ a*b + b*c + c*a"
        self.assertEqual(self.rule.apply(source).text, self.rule.apply(source).text)


class ConstructiveCoverageTests(unittest.TestCase):
    """The whole eligible set, tokenized with exactly the committed table.

    The lexicon's `coverage.constructive_check` block claims one leftover
    across 2,319 statements. This is that claim, recomputed.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.lex = fvl.load(LEXICON_PATH)
        cls.rule = fvr.load(RULE_PATH)
        cls.preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
        cls.eligible = [row for row in cls.preview["statements"] if row["accepted"]]

    _IDENT_CHARS = r"A-Za-z_α-ωΑ-Ω0-9'₀-₉ₐ-ₜ"
    _IDENT = re.compile(r"[A-Za-z_α-ωΑ-Ω][" + _IDENT_CHARS + r"]*")
    _NUMERAL = re.compile(r"\d+(?:\.\d+)?")
    _RUN = re.compile(r"[^" + _IDENT_CHARS + r"\s]+")

    def _leftovers(self, text: str) -> set[str]:
        """Longest-first munch. Leftovers are TOKENS, not characters.

        The character-level version of this check reported no leftover for
        `>=`, because `>` and `=` are both rows — while the renderer would
        emit `is greater than equals` and the inverse would hand the pinned
        binary `> =`, which is not a term. So the scan takes the longest table
        token at each position and a leftover is whatever no token matches.
        """
        tokens = self.lex.tokens
        out: set[str] = set()
        i = 0
        while i < len(text):
            if text[i].isspace():
                i += 1
                continue
            match = self._NUMERAL.match(text, i)
            if match:
                i = match.end()
                continue
            match = self._IDENT.match(text, i)
            if match:
                # A type name is a row; every other identifier is a slot.
                i = match.end()
                continue
            for token in tokens:
                if text.startswith(token, i):
                    i += len(token)
                    break
            else:
                out.add(text[i])
                i += 1
        return out

    def test_the_pinned_operator_runs_are_the_ones_in_the_tree(self) -> None:
        """The check the character-level sweep did not have.

        Every maximal run of non-identifier, non-digit, non-space characters in
        the eligible set, counted, pinned in the lexicon. A new run shape —
        a dialect construct nobody expected — turns this red instead of
        rendering to something the inverse cannot say.
        """
        raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        occurrences: dict[str, int] = {}
        statements: dict[str, int] = {}
        for row in self.eligible:
            seen = set()
            for match in self._RUN.finditer(row["interpreted"]):
                run = match.group(0)
                occurrences[run] = occurrences.get(run, 0) + 1
                seen.add(run)
            for run in seen:
                statements[run] = statements.get(run, 0) + 1
        measured = [[run, occurrences[run], statements[run]]
                    for run in sorted(occurrences)]
        self.assertEqual(measured, raw["coverage"]["operator_runs"])

    def test_every_operator_run_decomposes_into_rows_of_this_table(self) -> None:
        """`>=` is the case this exists for: two rows that are not the right row."""
        raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        refused = set(self.lex.refusals)
        for run, _occ, _stmts in raw["coverage"]["operator_runs"]:
            with self.subTest(run=run):
                rest = run
                while rest:
                    if rest[0] in refused or rest[0] == ".":
                        # The refusal row, and the numeral pair's decimal point.
                        rest = rest[1:]
                        continue
                    for token in self.lex.tokens:
                        if rest.startswith(token):
                            rest = rest[len(token):]
                            break
                    else:
                        self.fail(f"{run!r} leaves {rest!r}, which no row can say")

    def test_the_ascii_and_unicode_orderings_are_both_rows(self) -> None:
        """Both spellings are in the corpus, so both are rows — see corrections."""
        for glyph in ("≥", "≤", ">=", "<="):
            self.assertIn(glyph, self.lex.relations, f"{glyph} has no row")
        self.assertNotEqual(self.lex.relations["≥"], self.lex.relations[">="])

    def test_the_eligible_set_is_the_size_the_preview_records(self) -> None:
        self.assertEqual(len(self.eligible), 2319)
        self.assertEqual(self.preview["b0bc"]["accepted"], 2319)
        self.assertEqual(self.preview["b0a"]["totals"]["residue"], 4191)
        self.assertEqual(self.preview["b0a"]["totals"]["transliterable"], 6414)
        self.assertEqual(self.preview["b0a"]["totals"]["mute"], 10605)

    def test_the_only_uncovered_construct_is_the_one_with_a_refusal_row(self) -> None:
        leftovers: set[str] = set()
        for row in self.eligible:
            leftovers |= self._leftovers(row["interpreted"])
        self.assertEqual(leftovers, set(self.lex.refusals),
                         "the lexicon's refusal rows and the constructs it "
                         "actually fails to cover must be the same set")
        self.assertEqual(leftovers, {"↑"})

    def test_every_type_ascription_names_a_type_with_a_row(self) -> None:
        seen: set[str] = set()
        for row in self.eligible:
            seen |= set(re.findall(r":\s*([A-Za-z][A-Za-z0-9_']*)",
                                   row["interpreted"]))
        self.assertEqual(seen, set(self.lex.types))

    def test_the_b3_preview_arithmetic_closes(self) -> None:
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        b3 = prereg["b0_preview_2026_08_24"]["b3_preview"]
        total = (b3["transliterable"] + b3["covered"]
                 + b3["registered_blocked_mathlib_head"]
                 + b3["registered_blocked_no_row"])
        self.assertEqual(total, 10605)
        self.assertEqual(total, b3["total"])
        self.assertTrue(b3["closes_exactly"])
        self.assertNotEqual(b3["registered_blocked_mathlib_head"],
                            b3["registered_blocked_no_row"],
                            "the two blocked buckets are reported separately and "
                            "never summed; this asserts they are two numbers")


class PreregDigestTests(unittest.TestCase):
    """B7 — recomputed against the working tree.

    This is the test that goes red if the parser, the interpretation or the
    table was edited to make the oracle agree.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))

    def test_prereg_identifies_itself(self) -> None:
        self.assertEqual(self.prereg["prereg_id"], "foreign_voice.prereg.v1")

    def test_every_frozen_digest_matches_the_tree(self) -> None:
        """B7's sweep, re-aimed 2026-08-24 for the one retired row.

        The amendment is `foreign_voice.prereg.v1.amendment.transliteration-
        2026-08-24` (ROADMAP-v0.19 item 3a). B7 froze the parser in its own
        right — B0a's split and C-V2's contrast are computed with it — and that
        freeze did its job: experiments/foreign_voice_rate.json was measured
        under 65fead2f… and this amendment postdates the run. The parser did not
        move while the claim was being made, which is precisely what B7 asks.

        A retired row is checked against the successor pin the amendment names,
        so the sweep still fails on any undeclared change; it does not become a
        row nobody checks.
        """
        amendments = {entry["amendment_id"]: entry
                      for entry in self.prereg.get("amendments", ())}
        for row in self.prereg["frozen"]:
            with self.subTest(path=row["path"]):
                path = ROOT / row["path"]
                self.assertTrue(path.is_file(), f"{row['path']} is not in the tree")
                marker = row.get("retired_for_future_comparisons")
                if marker is None:
                    self.assertEqual(
                        _sha256_lf(path), row["sha256_lf"],
                        f"B7 VOID: {row['path']} changed after the "
                        f"preregistration commit recorded it. If the change was "
                        f"needed to make the oracle agree, the independence "
                        f"claim is void and the change needs its own review "
                        f"naming the reason.")
                    continue
                named = [entry for key, entry in amendments.items()
                         if key.endswith(marker["amendment"])]
                self.assertEqual(len(named), 1, marker["amendment"])
                successor = json.loads(
                    (ROOT / named[0]["successor_prereg"]["path"]).read_text(
                        encoding="utf-8"))
                live = {r["role"]: r for r in successor["frozen"]}[row["role"]]
                self.assertEqual(
                    _sha256_lf(path), live["sha256_lf"],
                    f"{row['path']} matches neither its retired pin nor the "
                    f"successor pin. A change past the amendment needs its own.")

    def test_the_frozen_parser_is_the_one_v018_froze(self) -> None:
        """The same digest experiments/realization_prereg.json pinned.

        Still 65fead2f… in BOTH files and still equal to each other, which is
        the invariant this test was written for: the run recorded in
        experiments/foreign_voice_rate.json read the corpus through the same
        parser experiments/realization_rate.json did, so B0a's split and
        C-V2's contrast sit on v0.18's denominator and not a moved one.

        Since 2026-08-24 that digest is a HISTORICAL one in both files — both
        rows carry `retired_for_future_comparisons` from the transliteration
        amendment, and the tree no longer matches it. That is asserted here too,
        so this test cannot be misread as saying the working parser is still
        65fead2f…; the sweep above is what checks the tree.
        """
        frozen = {row["role"]: row for row in self.prereg["frozen"]}
        v018 = json.loads(
            (ROOT / "experiments" / "realization_prereg.json").read_text(
                encoding="utf-8"))
        v018_parser = {row["role"]: row for row in v018["frozen"]}["parser"]
        self.assertEqual(frozen["parser"]["sha256_lf"], v018_parser["sha256_lf"])
        self.assertEqual(frozen["parser"]["sha256_lf"][:8], "65fead2f")
        for row in (frozen["parser"], v018_parser):
            self.assertIn(
                "retired_for_future_comparisons", row,
                "if one file retires the parser pin and the other does not, a "
                "reader is told two different things about the same digest")
            self.assertEqual(
                row["retired_for_future_comparisons"]["amendment"],
                "transliteration-2026-08-24")

    def test_b7s_four_named_artifacts_are_all_accounted_for(self) -> None:
        roles = {row["role"] for row in self.prereg["frozen"]}
        self.assertIn("parser", roles)
        self.assertIn("interpretation", roles)
        self.assertIn("lexicon_and_inverse_table", roles)
        self.assertTrue(self.prereg["there_is_no_separate_inverse_table"],
                        "B7 names an inverse-table digest; if there is no "
                        "separate file, the prereg has to say so in writing")

    def test_a_pending_row_is_pending_and_names_a_file_that_is_not_there(
            self) -> None:
        """A row leaves `pending` only when the file it names exists.

        Vacuous once `pending` empties, which is why the ordering it was
        standing in for is now checked against the git history below instead.
        Kept because the invariant is still the rule for anything added later.
        """
        for row in self.prereg["pending"]:
            with self.subTest(role=row["role"]):
                self.assertEqual(row["sha256_lf"], "pending")
                self.assertTrue(row.get("why"))
                self.assertFalse((ROOT / row["path"]).exists())

    def test_b7s_order_holds_in_the_git_history(self) -> None:
        """B7: the digests are recorded BEFORE the artifacts they gate exist.

        The prereg's `pending` list said this while it had rows in it and says
        nothing now that it is empty. The history still says it, and will keep
        saying it after every row has landed — which is the point at which a
        reader is most likely to want to check.
        """
        assert_added_before(
            self, "experiments/foreign_voice_prereg.json",
            "prover/lean/normalizer/Serialize.lean",
            "B7 records the freeze list before `Serialize.lean` is written")
        assert_added_before(
            self, "data/foreign_voice/rule_r.json",
            "data/foreign_voice/b0d_sealed_renderings.json",
            "§5: rule R is committed with its digest before the lexicon's hand "
            "renderings or the serializer exist")

    def test_nothing_that_renders_predates_the_things_that_gate_it(self) -> None:
        """B4 and B7 as one ordering claim, checked whenever the renderer exists.

        Silent while `scripts/foreign_voice.py` is absent — and it is absent at
        the commit that writes this — and load-bearing the moment it lands.
        """
        for gate in ("data/foreign_voice/lexicon.json",
                     "data/foreign_voice/rule_r.json",
                     "data/foreign_voice/register.json",
                     "data/foreign_voice/b0d_sealed_renderings.json",
                     "prover/lean/normalizer/Serialize.lean"):
            with self.subTest(gate=gate):
                assert_absent_or_added_after(
                    self, gate, "scripts/foreign_voice.py",
                    "B4 makes freezing the register a precondition of rendering, "
                    "and the sealed hundred are only a prediction if nothing "
                    "that could produce them existed first")

    def test_every_frozen_row_carries_the_date_it_was_recorded(self) -> None:
        """A digest with no date cannot be read against an ordering."""
        for row in self.prereg["frozen"]:
            with self.subTest(path=row["path"]):
                self.assertTrue(row.get("recorded"))

    def test_no_pending_row_names_a_file_that_already_exists(self) -> None:
        for row in self.prereg["pending"]:
            with self.subTest(path=row["path"]):
                self.assertFalse(
                    (ROOT / row["path"]).exists(),
                    f"{row['path']} exists but is still marked pending; a digest "
                    f"recorded after the artifact it pins is not a preregistration")


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
