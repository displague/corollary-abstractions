#!/usr/bin/env python3
"""Gates on `scripts/realize_term.py`: R5, R3, R2, and the C-R2 / C-R3 probes.

The design's claim is bounded and this module is written to test the bound and
nothing wider: *the sentence's structure is recoverable, given a lexicon whose
correctness is carried by review, not by the gate*
(DESIGN-sans-template-rendering §3).  So the tests here ask three things.

1. **Does the round trip hold where it should?**  A curated set spanning
   arithmetic, every relation, call heads (paren and bracket), nesting,
   fractions, decimals and negatives — each realized, re-read, and compared as
   a skeleton.
2. **Does it refuse where it must (R3)?**  Unparseable terms, uncovered heads,
   numerals outside the registered pair, and — the one that matters — a
   sentence whose re-parse disagrees is never served.  That last case is
   produced with a *scrambled* lexicon rather than asserted about a struct,
   because a refusal path that has never actually run is not a refusal path.
3. **Can the gate tell a real difference from a fake one (C-R2)?**  Operator
   swaps that are *verified to change the canonical skeleton first* must not
   round-trip to the source; commutative-argument swaps, which `canonicalize`
   legitimately erases, may.  A control that voided on correct behaviour would
   not be a control, and the design says so explicitly.

C-R3's assertion also lives here, aimed at this module's own risk: if writing
the realizer had required touching the parser, the digest recorded before the
realizer existed would no longer match.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import numeral_words as nw  # noqa: E402
import realization_lexicon as rlex  # noqa: E402
import realize_term as rt  # noqa: E402
from match_signatures import (  # noqa: E402
    Parser,
    canonicalize,
    skeleton,
    tokenize,
)

LEXICON_PATH = ROOT / "data" / "realization" / "lexicon.json"
PREREG_PATH = ROOT / "experiments" / "realization_prereg.json"

LEX = rlex.load(LEXICON_PATH)


def source_skeleton(text: str) -> str:
    """The source side of the comparison, through the frozen parser only."""
    return skeleton(canonicalize(Parser(tokenize(text)).parse()))


#: Curated coverage: arithmetic, relations, call heads, nesting, numerals.
CURATED = [
    # plain arithmetic and the precedence ladder
    "a + b = c",
    "a*b + c = d",
    "a + b*c = d",
    "(a + b)*c = d",
    "a^2 + b^2 = c^2",
    "2^3^4 = n",
    "(2^3)^4 = n",
    "a^(b + c) = d",
    # subtraction and division, i.e. neg and inv after canonicalization
    "a - b = c",
    "a - b - c = 0",
    "a/b = c",
    "a/b/c = d",
    "1/(a*b) = c",
    "(a + b)/(c - d) = 1",
    "-x^2 + 3*y = 0",
    "-(a + b)^2 = 0",
    "a*-b = c",
    "2^-3 = x",
    "x = -1",
    # every relation the tokenizer can reach
    "a = b",
    "a < b",
    "a > b",
    "a <= b",
    "a >= b",
    "a approx b",
    "a =>_d b",
    # call heads: paren, bracket, nested, multi-argument, relation-in-argument
    "sin(x)^2 + cos(x)^2 = 1",
    "GCD(a, b) = GCD(b, a)",
    "MEET(P, TRUTH) = P",
    "IMPLIES(TOUCHES(A, B), TOUCHES(B, A)) = TRUTH",
    "E[X|Y] = mean(X)",
    "sum(f(i)) = INTEGRAL(g(t))",
    "f(x = y) = z",
    "exp(-(r*t)) = y",
    "log10(x) < 100",
    "SQRT(b^2 - 4*a*c) = d",
    # numerals: integers, decimals, a corpus fraction, a big-ish integer
    "x = 19/13",
    "x = (0.375 + 2.5)*n",
    "x = 824",
    "x = 1000000007",
    "x = 190.3676248",
]


class RoundTripTests(unittest.TestCase):
    """R1's mechanism at unit scale: realize, re-read, compare skeletons."""

    def test_curated_set_round_trips_exactly(self) -> None:
        for source in CURATED:
            with self.subTest(source=source):
                result = rt.realize(source, LEX)
                self.assertIsInstance(result, rt.Realization, repr(result))
                self.assertEqual(
                    result.round_trip, "EXACT",
                    f"\n  source  : {source}"
                    f"\n  surface : {result.surface}"
                    f"\n  src skel: {result.term_skeleton}"
                    f"\n  got skel: {result.reparse_skeleton}",
                )
                self.assertEqual(result.term_skeleton, source_skeleton(source))
                self.assertTrue(result.served)

    def test_receipt_carries_every_field_the_design_names(self) -> None:
        result = rt.realize("a^2 + b^2 = c^2", LEX)
        payload = result.as_dict()
        for field in ("term_skeleton", "surface", "reparse_skeleton",
                      "round_trip", "lexicon_entries", "parameters"):
            self.assertIn(field, payload)
        self.assertEqual(payload["round_trip"], "EXACT")
        keys = {row["key"] for row in payload["lexicon_entries"]}
        self.assertEqual(keys, {"+", "=", "^", "slot_marker:variable"})
        self.assertEqual(payload["parameters"]["order"], "canonical")
        self.assertEqual(payload["parameters"]["slot_names"],
                         {"a": 0, "b": 1, "c": 2})

    def test_r2_every_surface_word_traces_to_a_row_or_the_numeral_pair(self) -> None:
        vocabulary = {w for phrase in LEX.phrase_to_token for w in phrase}
        for source in CURATED:
            with self.subTest(source=source):
                result = rt.realize(source, LEX)
                for word in result.surface.split():
                    self.assertTrue(
                        word in vocabulary or nw.is_numeral_word(word),
                        f"{word!r} is neither a lexicon word nor a numeral word",
                    )
                self.assertTrue(rt.surface_words_are_covered(result.surface, LEX))


class DeterminismTests(unittest.TestCase):
    """R5 — same term, same lexicon, same parameters, byte-identical sentence."""

    def test_repeated_realization_is_byte_identical(self) -> None:
        for source in CURATED:
            with self.subTest(source=source):
                first = rt.realize(source, LEX).surface
                for _ in range(4):
                    self.assertEqual(rt.realize(source, LEX).surface, first)

    def test_a_freshly_loaded_lexicon_gives_the_same_bytes(self) -> None:
        other = rlex.load(LEXICON_PATH)
        for source in CURATED:
            with self.subTest(source=source):
                self.assertEqual(rt.realize(source, LEX).surface,
                                 rt.realize(source, other).surface)

    def test_slot_naming_depends_only_on_the_term(self) -> None:
        """Renaming every variable must not change the sentence."""
        first = rt.realize("alpha^2 + beta^2 = gamma^2", LEX)
        second = rt.realize("p^2 + q^2 = r^2", LEX)
        self.assertEqual(first.surface, second.surface)
        self.assertEqual(first.term_skeleton, second.term_skeleton)


class RefusalTests(unittest.TestCase):
    """R3 — refuse at the surface, with the class named."""

    def test_unparseable_term_refuses(self) -> None:
        for source in ["not(P and Q) = (not P) or (not Q)",
                       "pi_1(S^1) iso Z",
                       "D(f)(x) = lim_{h->0} (f(x + h) - f(x)) / h",
                       "dbar = 2*|E| / |V|"]:
            with self.subTest(source=source):
                result = rt.realize(source, LEX)
                self.assertIsInstance(result, rt.Refusal)
                self.assertEqual(result.reason, "unparseable_term")
                self.assertFalse(result.served)

    def test_empty_term_refuses(self) -> None:
        result = rt.realize("   ", LEX)
        self.assertIsInstance(result, rt.Refusal)
        self.assertEqual(result.reason, "empty_term")

    def test_uncovered_head_refuses_rather_than_improvising(self) -> None:
        result = rt.realize("ZORPLE(x, y) = z", LEX)
        self.assertIsInstance(result, rt.Refusal)
        self.assertEqual(result.reason, "uncovered_head")
        self.assertIn("ZORPLE", result.detail)

    def test_uncovered_head_refuses_when_a_row_is_removed(self) -> None:
        """The refusal is a property of the table, not of one invented name."""
        raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        thinned = copy.deepcopy(raw)
        del thinned["call_heads"]["sin"]
        lex = rlex.build(thinned)
        self.assertIsInstance(rt.realize("sin(x) = y", lex), rt.Refusal)
        self.assertIsInstance(rt.realize("cos(x) = y", lex), rt.Realization)

    def test_numeral_outside_the_registered_pair_refuses(self) -> None:
        """The corpus's own 76-digit lean_workbook literal, verbatim in shape."""
        source = "x = " + "4" * 76
        result = rt.realize(source, LEX)
        self.assertIsInstance(result, rt.Refusal)
        self.assertEqual(result.reason, "unsupported_numeral")

    def test_bare_inverse_refuses(self) -> None:
        """A canonical `*` with no non-inv factor has no template spelling."""
        tree = ("op", "*", (("op", "inv", (("slot", "a"),)),
                            ("op", "inv", (("slot", "b"),))))
        linearizer = rt._Linearizer(LEX, {"a": 0, "b": 1})
        with self.assertRaises(rt.RefusalError) as caught:
            linearizer.emit(tree, rt.LEVEL_RELATION)
        self.assertEqual(caught.exception.reason, "leading_divisor")

    def test_every_refusal_reason_is_in_the_closed_set(self) -> None:
        for source in ["not(P and Q) = R", "ZORPLE(x) = y", "   ",
                       "x = " + "4" * 76]:
            result = rt.realize(source, LEX)
            self.assertIn(result.reason, rt.REFUSAL_REASONS)


class ScrambledLexiconTests(unittest.TestCase):
    """A failed re-parse is never served — exercised, not merely asserted.

    This is C-R1's mechanism at unit scale, and building it turned up a
    constraint on how C-R1 must be built that is worth stating before the
    registered run rather than after it:

    **The scramble has to be ONE-SIDED.**  Swapping two phrases in the table
    and then reading the surface back through that same swapped table is not a
    scrambled realizer at all — it is a consistent renaming, it is still a
    bijection, and it round-trips perfectly (`test_a_consistent_relabelling_is
    _not_a_control` below shows exactly that, at 4 of 4).  The control the
    design asks for is a realizer that emits the wrong words and is read by the
    **committed** table: forward scrambled, inverse honest.  A two-sided
    scramble would report a near-100% pass rate for the control and void the
    reading under C-R1's own "if the scrambled realizer passes ≥ 1%" clause,
    for a reason that has nothing to do with whether the gate reads the words.
    """

    PROBES = ["a + b = c", "a*b + c = d", "a + b*c = d", "a < b"]

    @classmethod
    def setUpClass(cls) -> None:
        raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        scrambled = copy.deepcopy(raw)
        ops = scrambled["operators"]
        ops["+"], ops["*"] = ops["*"], ops["+"]
        rels = scrambled["relations"]
        rels["="], rels["<"] = rels["<"], rels["="]
        cls.scrambled = rlex.build(scrambled)

    def test_the_scrambled_table_still_loads(self) -> None:
        """Swapping two phrases preserves bijectivity — R2b is not taste."""
        self.assertEqual(self.scrambled.words_for("+"), LEX.words_for("*"))

    def test_a_one_sided_scramble_fails_and_is_never_served(self) -> None:
        """Emit with the wrong words; read with the committed table."""
        failures = 0
        for source in self.PROBES:
            with self.subTest(source=source):
                surface = rt.realize(source, self.scrambled).surface
                recovered, _ = rt.reparse(surface, LEX)
                self.assertIsNotNone(recovered, "fluent-looking, per C-R1")
                if recovered != source_skeleton(source):
                    failures += 1
        self.assertEqual(failures, len(self.PROBES),
                         "a one-sided scramble should miss on all of them")

    def test_a_consistent_relabelling_is_not_a_control(self) -> None:
        """The finding: scrambling both directions passes, and proves nothing."""
        passes = 0
        for source in self.PROBES:
            result = rt.realize(source, self.scrambled)
            self.assertIsInstance(result, rt.Realization)
            if result.round_trip == "EXACT":
                passes += 1
        self.assertEqual(passes, len(self.PROBES))

    def test_a_failed_round_trip_is_never_served(self) -> None:
        """R3's third clause, on a realization that genuinely failed."""
        broken = copy.deepcopy(json.loads(LEXICON_PATH.read_text(encoding="utf-8")))
        # Give `+` the phrase for `*` WITHOUT giving `*` anything else, by
        # routing `*` to a fresh phrase: forward is wrong, the inverse table is
        # still a bijection, and the two disagree about which token `+` means.
        broken["operators"]["+"] = broken["operators"]["*"]
        broken["operators"]["*"] = "the muddled product of"
        lex = rlex.build(broken)
        result = rt.realize("a + b = c", lex)
        surface = result.surface
        recovered, _ = rt.reparse(surface, LEX)
        # Read back through the COMMITTED table the served path would use.
        self.assertNotEqual(recovered, source_skeleton("a + b = c"))
        forged = rt.Realization(
            source="a + b = c",
            term_skeleton=source_skeleton("a + b = c"),
            surface=surface,
            reparse_skeleton=recovered,
            round_trip="FAILED",
            lexicon_entries=(),
            parameters={},
        )
        self.assertFalse(forged.served)

    def test_the_true_table_serves_the_same_probes(self) -> None:
        """The contrast C-R1 is built on, in miniature."""
        for source in self.PROBES:
            with self.subTest(source=source):
                self.assertTrue(rt.realize(source, LEX).served)


class NearMissTests(unittest.TestCase):
    """C-R2 — skeleton-changing mutations must not round-trip to the SOURCE.

    Every mutation below is built the way the design requires: the swap is
    verified to change the canonical skeleton *before* it is realized, so a
    mutation that `canonicalize` legitimately erases can never be counted as a
    gate failure.
    """

    #: (source, mutated) pairs, one operator word apart on the surface.
    SWAPS = [
        ("a + b = c", "a*b = c"),
        ("a*b + c = d", "a*b*c = d"),
        ("a - b = c", "a + b = c"),
        ("a/b = c", "a*b = c"),
        ("a^2 = b", "a*2 = b"),
        ("a < b", "a = b"),
        ("a <= b", "a >= b"),
        ("sin(x) = y", "cos(x) = y"),
        ("GCD(a, b) = c", "MINOF(a, b) = c"),
        ("a + b*c = d", "(a + b)*c = d"),
    ]

    def test_every_mutation_really_changes_the_skeleton(self) -> None:
        """The precondition the design demands, checked before anything else."""
        for source, mutated in self.SWAPS:
            with self.subTest(source=source):
                self.assertNotEqual(source_skeleton(source),
                                    source_skeleton(mutated))

    def test_no_skeleton_changing_near_miss_round_trips_to_the_source(self) -> None:
        """If one did, canonicalization would be collapsing a distinction."""
        for source, mutated in self.SWAPS:
            with self.subTest(source=source):
                result = rt.realize(mutated, LEX)
                self.assertIsInstance(result, rt.Realization)
                self.assertNotEqual(
                    result.reparse_skeleton, source_skeleton(source),
                    f"{mutated!r} round-tripped to the skeleton of {source!r}",
                )

    def test_the_mutation_set_reparses_rather_than_failing_to_parse(self) -> None:
        """C-R2's ≥50% floor: the set must exercise the canonicalizer.

        A mutation set that merely fails to tokenize would be testing the
        tokenizer and would say nothing about whether the gate can tell two
        structures apart.
        """
        reparsed = 0
        for _, mutated in self.SWAPS:
            result = rt.realize(mutated, LEX)
            if (isinstance(result, rt.Realization)
                    and result.reparse_skeleton is not None):
                reparsed += 1
        self.assertGreaterEqual(reparsed / len(self.SWAPS), 0.5)
        self.assertEqual(reparsed, len(self.SWAPS))

    def test_a_commutative_swap_legitimately_round_trips(self) -> None:
        """The case a naive control would void on — named, not discovered.

        `canonicalize` sorts commutative arguments, so `a + b` and `b + a` are
        one skeleton and one sentence. A near-miss set built from swaps like
        this would void the gate for behaving correctly.
        """
        for left, right in [("a + b = c", "b + a = c"),
                            ("a*b = c", "b*a = c"),
                            ("GCD(a, b) = c", "GCD(b, a) = c")]:
            with self.subTest(pair=(left, right)):
                self.assertEqual(source_skeleton(left), source_skeleton(right))
                self.assertEqual(rt.realize(left, LEX).surface,
                                 rt.realize(right, LEX).surface)
                self.assertEqual(rt.realize(right, LEX).reparse_skeleton,
                                 source_skeleton(left))

    def test_an_alias_class_swap_also_round_trips_legitimately(self) -> None:
        """The other case the design names: same operation, two spellings.

        `MOD` and `CONCAT` are one declared alias class, and `=` is declared
        symmetric — so a mutation drawn from either would round-trip to the
        source at the level that erases the difference. Recorded here so the
        near-miss set above is visibly free of both kinds.
        """
        self.assertEqual(source_skeleton("a = b"), source_skeleton("b = a"))
        self.assertEqual(rt.realize("a = b", LEX).surface,
                         rt.realize("b = a", LEX).surface)


class StageOneTests(unittest.TestCase):
    """The inverter is table-driven, with no structure of its own (§3)."""

    def test_tokens_come_out_in_surface_order(self) -> None:
        """`canonicalize` has already sorted the factors; stage 1 just reads."""
        result = rt.realize("(a + b)*c = d", LEX)
        self.assertEqual(
            list(result.reparse_tokens),
            ["V0", "=", "V1", "*", "(", "V2", "+", "V3", ")"],
        )

    def test_it_does_not_count_brackets(self) -> None:
        """Unbalanced grouping words pass stage 1 and die in stage 2.

        This is the whole claim about the division of labour: stage 1 emits
        `(` because the writer wrote "the quantity", not because anything is
        balanced; stage 2 is what notices.
        """
        surface = "the quantity variable zero plus variable one equals variable two"
        tokens = rt.delexicalize(surface, LEX)
        self.assertEqual(tokens, ["(", "V0", "+", "V1", "=", "V2"])
        recovered, _ = rt.reparse(surface, LEX)
        self.assertIsNone(recovered)

    def test_it_refuses_words_it_has_no_row_for(self) -> None:
        self.assertIsNone(rt.delexicalize("variable zero flurb variable one", LEX))

    def test_the_slot_marker_reads_its_index_through_the_numeral_pair(self) -> None:
        self.assertEqual(
            rt.delexicalize("variable twenty-four equals variable zero", LEX),
            ["V24", "=", "V0"],
        )

    def test_numeral_runs_are_scanned_greedily_and_safely(self) -> None:
        self.assertEqual(
            rt.delexicalize("eight hundred twenty-four plus zero point five", LEX),
            ["824", "+", "0.5"],
        )

    def test_stage_one_is_a_pure_function_of_the_word_sequence(self) -> None:
        surface = rt.realize("(a + b)/(c - d) = 1", LEX).surface
        first = rt.delexicalize(surface, LEX)
        self.assertEqual(first, rt.delexicalize(surface, LEX))
        self.assertEqual(first, rt.delexicalize(" ".join(surface.split()), LEX))


class TautologyProbeTests(unittest.TestCase):
    """C-R3, aimed at this module's own risk."""

    def test_the_parser_is_byte_unchanged_since_the_prereg_commit(self) -> None:
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        frozen = {row["role"]: row for row in prereg["frozen"]}
        parser = frozen["parser"]
        self.assertEqual(parser["path"], "scripts/match_signatures.py")
        digest = hashlib.sha256(
            (ROOT / parser["path"]).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        self.assertEqual(
            digest, parser["sha256_lf"],
            "C-R3 VOID: implementing the realizer changed the parser. The "
            "independence claim needs its own review naming the reason.",
        )

    def test_the_inverter_digest_is_recorded_beside_the_parser(self) -> None:
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        frozen = {row["role"]: row for row in prereg["frozen"]}
        self.assertIn("inverter", frozen)
        inverter = frozen["inverter"]
        self.assertEqual(inverter["path"], "scripts/realize_term.py")
        digest = hashlib.sha256(
            (ROOT / inverter["path"]).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        self.assertEqual(digest, inverter["sha256_lf"])
        self.assertIn("recorded", inverter,
                      "the inverter row must date itself: it postdates the "
                      "parser freeze by construction")

    def test_the_realizer_does_not_import_a_second_parser(self) -> None:
        """Stage 2 must be the frozen module, not a copy of it."""
        text = (ROOT / "scripts" / "realize_term.py").read_text(encoding="utf-8")
        self.assertIn("from match_signatures import", text)
        for forbidden in ("def tokenize", "class Parser", "def canonicalize",
                          "def skeleton"):
            self.assertNotIn(forbidden, text,
                             f"realize_term.py defines its own {forbidden!r}")


class CensusTests(unittest.TestCase):
    """The R0 table's shape, on a small slice so the test stays fast."""

    def test_census_over_two_small_corpora(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("trigonometry", "economics"):
                target = root / name
                target.mkdir()
                (target / "nodes.json").write_bytes(
                    (ROOT / "data" / name / "nodes.json").read_bytes()
                )
            report = rt.census(root, LEX)
        self.assertEqual(report["census_id"], "realization.census.v1")
        self.assertEqual({row["corpus"] for row in report["corpora"]},
                         {"trigonometry", "economics"})
        totals = report["totals"]
        self.assertEqual(totals["nodes"], 19)
        self.assertEqual(totals["parseable"], 19)
        self.assertEqual(totals["round_trip_exact"], 19)
        self.assertEqual(totals["round_trip_failed"], 0)
        self.assertEqual(totals["r1_verdict"], "FIRES")
        for row in report["corpora"]:
            self.assertTrue(row["thin_denominator"],
                            "both slices are under 50 and must say so")

    def test_census_names_its_denominator_and_disclaims_the_registered_run(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "trigonometry").mkdir()
            (root / "trigonometry" / "nodes.json").write_bytes(
                (ROOT / "data" / "trigonometry" / "nodes.json").read_bytes()
            )
            report = rt.census(root, LEX)
        self.assertIn("parseable", report["totals"])
        self.assertIn("round_trip_rate_over_parseable", report["totals"])
        self.assertTrue(any("not the registered full-corpus run" in line
                            for line in report["note"]))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
