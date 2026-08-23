#!/usr/bin/env python3
"""Gates on the registered-run writer, and on the controls being aimed.

The artifact this writer produces is the cycle's headline, so the tests here
are about whether the *instrument* can be trusted, not about the numbers it
happened to report:

- **Byte-reproducibility.**  Two runs on one tree must produce identical
  bytes, or "the registered run" names a moving target.  Checked by
  regenerating into a temp path and comparing.
- **The C-R3 refusal path.**  A writer that revalidates digests and then
  writes anyway has revalidated nothing.  The mismatch is injected and the
  refusal asserted, including that no file is written.
- **C-R1's aim.**  The control is only informative because it is ONE-SIDED,
  and the way to prove a control is aimed is to show the un-aimed version
  behaves as predicted: a two-sided run of *the same derangement* must
  round-trip near-perfectly.  If it did not, the scramble would be breaking
  something other than word identity and the contrast would be measuring that
  instead.
- **C-R2's construction rule.**  Every mutation must be verified to change the
  canonical skeleton before it is realized, and the discarded ones must be
  counted rather than silently dropped.

The corpus-scale numbers themselves are asserted only where they are cheap and
load-bearing (the LOST=0 balance), because re-deriving them here would just be
running the instrument twice.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import measure_realization as mr  # noqa: E402
import realization_lexicon as rlex  # noqa: E402
import realize_term as rt  # noqa: E402
from match_signatures import (  # noqa: E402
    Parser,
    canonicalize,
    skeleton,
    tokenize,
)

LEXICON_PATH = ROOT / "data" / "realization" / "lexicon.json"
ARTIFACT_PATH = ROOT / "experiments" / "realization_rate.json"
LEX = rlex.load(LEXICON_PATH)


def _slice_corpora(root: Path, names: tuple[str, ...]) -> Path:
    """A small data dir carved out of the committed corpora."""
    for name in names:
        target = root / name
        target.mkdir(parents=True)
        (target / "nodes.json").write_bytes(
            (ROOT / "data" / name / "nodes.json").read_bytes()
        )
    return root


class PreregRevalidationTests(unittest.TestCase):
    """C-R3, and the refusal that gives it teeth."""

    def test_the_committed_tree_revalidates(self) -> None:
        block = mr.revalidate_prereg()
        self.assertEqual(block["verdict"], "HOLDS")
        roles = {row["role"] for row in block["revalidated"]}
        self.assertLessEqual(
            {"parser", "numeral_pair", "lexicon", "lexicon_loader", "inverter"},
            roles,
        )
        for row in block["revalidated"]:
            self.assertTrue(row["agrees"], row["path"])

    def test_a_drifted_digest_raises(self) -> None:
        prereg = json.loads(
            (ROOT / "experiments" / "realization_prereg.json").read_text(
                encoding="utf-8")
        )
        injured = copy.deepcopy(prereg)
        for row in injured["frozen"]:
            if row["role"] == "parser":
                row["sha256_lf"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prereg.json"
            path.write_text(json.dumps(injured), encoding="utf-8")
            with self.assertRaises(mr.PreregMismatch) as caught:
                mr.revalidate_prereg(path)
        self.assertIn("match_signatures.py", str(caught.exception))

    def test_the_writer_refuses_to_write_on_mismatch(self) -> None:
        """Revalidating and then writing anyway would revalidate nothing."""
        import contextlib
        import io

        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            prereg = json.loads(mr.PREREG_PATH.read_text(encoding="utf-8"))
            for row in prereg["frozen"]:
                if row["role"] == "inverter":
                    row["sha256_lf"] = "1" * 64
            injured = Path(tmp) / "prereg.json"
            injured.write_text(json.dumps(prereg), encoding="utf-8")
            out = Path(tmp) / "must-not-exist.json"
            data = _slice_corpora(Path(tmp) / "data", ("trigonometry",))
            with contextlib.redirect_stderr(stderr):
                code = mr.main(["--data-dir", str(data), "--out", str(out),
                                "--prereg", str(injured)])
            self.assertEqual(code, 3)
            self.assertFalse(out.exists(), "the artifact was written anyway")
        self.assertIn("REFUSING TO WRITE", stderr.getvalue())
        self.assertIn("realize_term.py", stderr.getvalue())


class ReproducibilityTests(unittest.TestCase):
    """R5 at artifact scale: two runs on one tree, identical bytes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        data = _slice_corpora(Path(cls._tmp.name) / "data",
                              ("trigonometry", "economics", "morphology"))
        cls.first = mr.build_artifact(data, LEXICON_PATH)
        cls.second = mr.build_artifact(data, LEXICON_PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _dump(self, artifact: dict) -> bytes:
        return (json.dumps(artifact, indent=2, ensure_ascii=False) + "\n").encode()

    def test_two_runs_are_byte_identical(self) -> None:
        self.assertEqual(self._dump(self.first), self._dump(self.second))

    def test_the_artifact_carries_no_wall_clock(self) -> None:
        """A timestamp would make 'the registered run' unreproducible.

        Checked over KEYS, not over the whole serialized text: the artifact's
        own prose explains that it records no elapsed time, and a substring
        scan flags that explanation as the thing it forbids.
        """
        def keys(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    yield key
                    yield from keys(value)
            elif isinstance(node, list):
                for item in node:
                    yield from keys(item)

        found = set(keys(self.first))
        for forbidden in ("elapsed", "timestamp", "wall_clock", "started_at",
                          "generated_at", "run_at", "duration"):
            self.assertNotIn(forbidden, found)

    def test_the_scramble_seed_is_the_lexicons_own_digest(self) -> None:
        """A seed someone chose would be a knob; the table under test is not."""
        from report_provenance import sha256_lf_file

        self.assertEqual(self.first["c_r1"]["scramble"]["seed_source_digest"],
                         sha256_lf_file(LEXICON_PATH))

    def test_lost_is_zero_balances_on_the_slice(self) -> None:
        lost = self.first["r1"]["lost_is_zero"]
        self.assertTrue(lost["balances"])
        self.assertEqual(lost["accounted"], lost["denominator"])


class ScrambleTests(unittest.TestCase):
    """C-R1's aim, proved by showing the un-aimed version behaves as predicted."""

    @classmethod
    def setUpClass(cls) -> None:
        from report_provenance import sha256_lf_file

        cls.raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        cls.digest = sha256_lf_file(LEXICON_PATH)
        cls.scrambled, cls.moved = mr.scrambled_lexicon(cls.raw, cls.digest)
        cls.probes = ["a + b = c", "a*b + c = d", "sin(x) = y", "a < b",
                      "a^2 + b^2 = c^2", "GCD(a, b) = c", "a/b = c"]

    def test_the_scrambled_table_passes_the_same_r2b_gate(self) -> None:
        """A wrong table, not a broken one: it loads through the real loader."""
        self.assertEqual(len(self.scrambled.phrase_to_token),
                         len(LEX.phrase_to_token))

    def test_the_derangement_has_no_fixed_point(self) -> None:
        for section in ("operators", "relations", "call_heads"):
            source = getattr(LEX, section)
            target = getattr(self.scrambled, section)
            for key in source:
                self.assertNotEqual(source[key], target[key],
                                    f"{section}:{key} kept its own phrase")

    def test_grouping_words_are_deliberately_untouched(self) -> None:
        """Breaking parenthesization would fail at the tokenizer, not the gate."""
        self.assertEqual(self.scrambled.structural, LEX.structural)
        self.assertEqual(self.scrambled.slot_marker, LEX.slot_marker)

    def test_one_sided_scramble_misses(self) -> None:
        """Emit deranged, read committed: the control's actual configuration."""
        passes = 0
        for source in self.probes:
            result = rt.realize(source, self.scrambled)
            self.assertIsInstance(result, rt.Realization)
            recovered, _ = rt.reparse(result.surface, LEX)
            if recovered == result.term_skeleton:
                passes += 1
        self.assertEqual(passes, 0, "a one-sided scramble must not pass")

    def test_two_sided_scramble_round_trips_near_perfectly(self) -> None:
        """THE aiming test: the same derangement, read through itself, passes.

        This is what proves the contrast is measuring word identity and not
        collateral damage. If a two-sided run of this derangement also failed,
        the scramble would be breaking the grammar rather than the words, and
        C-R1's contrast would be reporting that instead.
        """
        passes = 0
        for source in self.probes:
            result = rt.realize(source, self.scrambled)
            if result.round_trip == "EXACT":
                passes += 1
        self.assertEqual(passes, len(self.probes),
                         "a consistent relabelling is still a bijection")

    def test_the_digit_map_is_a_derangement(self) -> None:
        import random

        numerals = mr._ScrambledNumerals(random.Random(7))
        self.assertEqual(sorted(numerals.map), [str(d) for d in range(10)])
        self.assertEqual(sorted(numerals.map.values()), [str(d) for d in range(10)])
        for digit, mapped in numerals.map.items():
            self.assertNotEqual(digit, mapped)

    def test_the_digit_map_changes_the_numerals_it_touches(self) -> None:
        import random

        with mr._ScrambledNumerals(random.Random(7)):
            import numeral_words as nw
            self.assertNotEqual(nw.number_to_words(19), "nineteen")
            self.assertNotEqual(nw.number_to_words(2.5), "two point five")
        import numeral_words as nw
        self.assertEqual(nw.number_to_words(19), "nineteen")


class MutationTests(unittest.TestCase):
    """C-R2's construction rule, checked on the rules themselves."""

    def _tree(self, source: str) -> tuple:
        return canonicalize(Parser(tokenize(source)).parse())

    def test_each_rule_produces_a_skeleton_changing_mutation(self) -> None:
        cases = [
            (mr._rule_swap_noncommutative_args, "a < b + c"),
            (mr._rule_operator_word_swap, "a + b = c"),
            (mr._rule_alias_class_swap, "MOD(a, b) = c"),
            (mr._make_head_swap_rule(sorted(LEX.call_heads)), "sin(x) = y"),
        ]
        for rule, source in cases:
            with self.subTest(source=source):
                tree = self._tree(source)
                mutated = mr._replace_first(tree, rule)
                self.assertIsNotNone(mutated)
                self.assertNotEqual(skeleton(canonicalize(mutated)),
                                    skeleton(tree))

    def test_swapping_two_bare_slots_does_NOT_change_the_skeleton(self) -> None:
        """The reason the design insists on verifying before realizing.

        `a < b` and `b < a` are the SAME skeleton — `<` is not symmetric, but
        `render_skeleton` erases slot identity and renumbers by first
        occurrence, so two bare slots either side of any relation are
        indistinguishable. A near-miss set that assumed "non-symmetric
        relation => swapping changes the skeleton" would be feeding the gate
        mutations that are not mutations, and every one of them would
        "round-trip to the source" and void the control for behaving
        correctly. C-R2 discards these and counts the discards.
        """
        left, right = self._tree("a < b"), self._tree("b < a")
        self.assertEqual(skeleton(left), skeleton(right))
        mutated = mr._replace_first(left, mr._rule_swap_noncommutative_args)
        self.assertIsNotNone(mutated, "the rule does fire")
        self.assertEqual(skeleton(canonicalize(mutated)), skeleton(left),
                         "and its result is not a near-miss at all")

    def test_alias_siblings_are_the_declared_classes(self) -> None:
        """The design's correction, encoded: MOD/CONCAT are a real near-miss."""
        self.assertEqual(mr.ALIAS_SIBLING["MOD"], "CONCAT")
        self.assertEqual(mr.ALIAS_SIBLING["CONCAT"], "MOD")
        self.assertNotEqual(skeleton(self._tree("MOD(a, b) = c")),
                            skeleton(self._tree("CONCAT(a, b) = c")))

    def test_a_skeleton_preserving_swap_is_discarded_not_counted(self) -> None:
        """Discarded mutations must be COUNTED, not silently dropped."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _slice_corpora(Path(tmp) / "data", ("economics",))
            body = mr.measure(data, LEX)
            control = mr.control_c_r2(body["parseable_sources"], LEX)
        swaps = control["per_rule"]["swap_noncommutative_args"]
        self.assertGreater(
            swaps.get("discarded_skeleton_unchanged", 0), 0,
            "economics carries swaps that canonicalize away; they must appear "
            "as discards rather than vanishing from the accounting",
        )

    def test_the_control_counts_discards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = _slice_corpora(Path(tmp) / "data", ("trigonometry",))
            body = mr.measure(data, LEX)
            control = mr.control_c_r2(body["parseable_sources"], LEX)
        dispositions = ("not_applicable", "discarded_skeleton_unchanged",
                        "refused", "failed_to_parse", "round_tripped_to_source",
                        "reparsed_to_a_different_skeleton")
        outcomes = ("refused", "failed_to_parse", "round_tripped_to_source",
                    "reparsed_to_a_different_skeleton")
        for name, counts in control["per_rule"].items():
            with self.subTest(rule=name):
                self.assertEqual(
                    sum(counts.get(k, 0) for k in dispositions),
                    control["denominator_terms"],
                    f"{name} must give every term exactly one disposition",
                )
                self.assertEqual(
                    counts.get("generated", 0),
                    sum(counts.get(k, 0) for k in outcomes),
                    f"{name}'s generated count must equal its outcomes",
                )
                self.assertEqual(set(counts) - set(dispositions) - {"generated"},
                                 set(), f"{name} has an uncounted disposition")

    def test_tree_realization_uses_the_pinned_linearizer(self) -> None:
        """The glue is local; the linearizer is realize_term's own object."""
        tree = self._tree("a + b = c")
        self.assertEqual(mr._realize_tree(tree, LEX),
                         rt.realize("a + b = c", LEX).surface)


class ArtifactShapeTests(unittest.TestCase):
    """The committed registered run says what §10 requires it to say."""

    @classmethod
    def setUpClass(cls) -> None:
        if not ARTIFACT_PATH.exists():   # pragma: no cover - pre-run tree
            raise unittest.SkipTest("the registered run has not been executed yet")
        cls.doc = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))

    def test_it_is_lf(self) -> None:
        self.assertNotIn(b"\r\n", ARTIFACT_PATH.read_bytes())

    def test_it_carries_r0_r1_r2_r5_and_three_controls(self) -> None:
        for key in ("r0", "r1", "r2", "r5", "c_r1", "c_r2", "c_r3"):
            self.assertIn(key, self.doc)

    def test_r1_reports_its_denominator_in_the_same_sentence(self) -> None:
        """R0's rule: every sentence quoting R1 names the parseable count."""
        sentence = self.doc["r1"]["sentence"]
        self.assertIn(str(self.doc["r1"]["denominator"]), sentence)
        self.assertIn("parseable", sentence)

    def test_lost_is_zero(self) -> None:
        lost = self.doc["r1"]["lost_is_zero"]
        self.assertTrue(lost["balances"])
        self.assertEqual(
            lost["accounted"], lost["denominator"],
            "every parseable term is either served or listed by statement id",
        )

    def test_the_surface_digest_still_describes_the_tree(self) -> None:
        """R5/M2: a rendering change anywhere shows up as a digest mismatch."""
        import hashlib

        rows = []
        for path in sorted((ROOT / "data").glob("*/nodes.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            for node in doc.get("statement_nodes", []):
                sid = node.get("statement_id", "<missing-id>")
                source = ((node.get("formal_statement") or {})
                          .get("canonical_ascii") or "")
                result = rt.realize(source, LEX, statement_id=sid)
                if isinstance(result, rt.Realization) and result.served:
                    rows.append((sid, result.surface))
        rows.sort()
        joined = "\n".join(f"{sid}\t{surface}" for sid, surface in rows)
        self.assertEqual(len(rows), self.doc["r5"]["served_count"])
        self.assertEqual(hashlib.sha256(joined.encode("utf-8")).hexdigest(),
                         self.doc["r5"]["digest_over_all"])

    def test_no_control_voided(self) -> None:
        for key in ("c_r1", "c_r2"):
            with self.subTest(control=key):
                self.assertNotIn("VOID", self.doc[key]["verdict"])
        self.assertEqual(self.doc["c_r3"]["verdict"], "HOLDS")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
