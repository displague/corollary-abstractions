#!/usr/bin/env python3
"""B-P: the identity witness exists, is stable, and refuses rather than guesses.

DESIGN-foreign-voice §6 B-P asks for exactly two properties and one refusal:

  (i)  binder-name independence **on the registered pairs** — the two pairs the
       grounding prototype retained, which the design quotes by digest;
  (ii) byte-identical output across two runs;
  and B5's hermetic clause: *"An absent pinned toolchain **refuses and never
  downloads**, asserted on every machine — the existing test is
  `tests/test_external_verifier.py:215`
  (`test_missing_toolchain_refuses_and_never_downloads`), deliberately not
  skipped, and this cycle's harness gains its sibling."*

The refusal tests are **not** skipped when the toolchain is absent — that is
the whole point of them.  The serialization tests are, because a machine
without the pinned binary cannot run the oracle at all and a green suite there
would be a green suite that measured nothing.
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
sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice_oracle as fvo  # noqa: E402
import foreign_voice_rule_r as fvr  # noqa: E402
from git_ordering import assert_added_before  # noqa: E402

PREREG_PATH = ROOT / "experiments" / "foreign_voice_prereg.json"
PROTOTYPE = ROOT / "prover" / "lean" / "normalizer" / "Serialize.prototype.lean"

#: The digests DESIGN-foreign-voice §3.2 quotes for the retained pairs. They
#: are prefixes in the design; the full values are pinned here, measured.
PAIR_ONE = "25ec23fb13b3312063d7b9754afbb2f3694775f83c5d7726d4925c7486dce3c3"
PAIR_TWO = "f89095af7546ebd1b61e2374119fa2e041d8c89af2ece93c6f11016c893bae7f"
PAIR_ONE_LENGTH = 475
PAIR_TWO_LENGTH = 2627


def _strip_lean_comments(text: str) -> str:
    """Drop `/- … -/` blocks (nested), `--` line comments, and string literals.

    `Serialize.lean` discusses `sorry` at length in order to say it is absent,
    and its FVERR messages name `sorryAx` in order to report refusing one. A
    substring check over the raw file is therefore a check that the file does
    not TALK about the thing it forbids, which is the opposite of what is
    wanted. Comments and string literals come out; what is left is the terms
    the program actually elaborates.
    """
    out: list[str] = []
    depth = 0
    i = 0
    while i < len(text):
        if text.startswith("/-", i):
            depth += 1
            i += 2
            continue
        if text.startswith("-/", i) and depth:
            depth -= 1
            i += 2
            continue
        if depth:
            i += 1
            continue
        if text.startswith("--", i):
            newline = text.find("\n", i)
            i = len(text) if newline == -1 else newline
            continue
        if text[i] == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
            i += 1
            out.append('""')
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _have_toolchain() -> bool:
    try:
        fvo.load()
    except fvo.OracleRefusal:
        return False
    return True


HAVE_LEAN = _have_toolchain()


class HermeticRefusal(unittest.TestCase):
    """Deliberately not skipped. An absent toolchain must never be a download."""

    def test_missing_toolchain_refuses_and_never_downloads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pin = root / "lean-toolchain"
            pin.write_bytes(b"leanprover/lean4:v0.0.0-nonexistent\n")
            with self.assertRaises(fvo.OracleRefusal) as caught:
                fvo.load(serializer=ROOT / "prover" / "lean" / "normalizer" /
                         "Serialize.lean", toolchain_file=pin)
        self.assertIn("refusing to download", str(caught.exception))

    def test_a_missing_toolchain_file_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(fvo.OracleRefusal):
                fvo.load(toolchain_file=Path(temporary) / "absent")

    def test_a_missing_serializer_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(fvo.OracleRefusal):
                fvo.load(serializer=Path(temporary) / "absent.lean")

    def test_the_committed_pin_names_the_toolchain_the_prereg_froze(self) -> None:
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        row = {r["path"]: r for r in prereg["frozen"]}[
            "prover/lean/normalizer/lean-toolchain"]
        self.assertEqual(
            fvo.DEFAULT_TOOLCHAIN_FILE.read_text(encoding="utf-8").strip(),
            row["toolchain"])


class TagDiscipline(unittest.TestCase):
    """Tags are the identity, so a bad one refuses before the binary is touched."""

    @classmethod
    def setUpClass(cls) -> None:
        if not HAVE_LEAN:
            raise unittest.SkipTest("pinned Lean toolchain not installed")
        cls.oracle = fvo.load()

    def test_a_tag_with_a_quote_refuses(self) -> None:
        with self.assertRaises(fvo.OracleRefusal):
            self.oracle.serialize([('a"b', "1 = 1")])

    def test_a_repeated_tag_refuses(self) -> None:
        with self.assertRaises(fvo.OracleRefusal):
            self.oracle.serialize([("a", "1 = 1"), ("a", "2 = 2")])

    def test_a_multiline_term_refuses(self) -> None:
        with self.assertRaises(fvo.OracleRefusal):
            self.oracle.serialize([("a", "1 =\n1")])


@unittest.skipUnless(HAVE_LEAN, "pinned Lean toolchain not installed")
class BinderNameIndependence(unittest.TestCase):
    """B-P(i) — the prototype's two retained pairs, as the first two cases."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = fvo.load()
        cls.answers = cls.oracle.serialize([
            ("pair1a", "∀ p q : Nat, p + q = q + p"),
            ("pair1b", "∀ zzz www : Nat, zzz + www = www + zzz"),
            ("pair2a", "∀ a b c : Rat, 9 * (a ^ 3 + b ^ 3 + c ^ 3) ≥ (a + b + c) ^ 3"),
            ("pair2b", "∀ x y z : Rat, 9*(x^3+y^3+z^3) ≥ (x+y+z)^3"),
        ])

    def test_every_registered_pair_elaborated(self) -> None:
        for tag, row in self.answers.items():
            with self.subTest(tag=tag):
                self.assertTrue(row.ok, row.error)

    def test_the_first_pair_is_byte_identical(self) -> None:
        """`∀ p q` and `∀ zzz www`: the names are gone from the string itself."""
        self.assertEqual(self.answers["pair1a"].serialization,
                         self.answers["pair1b"].serialization)
        self.assertEqual(len(self.answers["pair1a"].serialization),
                         PAIR_ONE_LENGTH)
        self.assertEqual(self.answers["pair1a"].digest, PAIR_ONE)

    def test_the_second_pair_is_byte_identical(self) -> None:
        """In-territory: a Rat-interpreted residue statement of the kind B1 scores.

        The pair also differs in whitespace, so it witnesses that the digest is
        of the ELABORATED TERM and not of any normalization of the text.
        """
        self.assertEqual(self.answers["pair2a"].serialization,
                         self.answers["pair2b"].serialization)
        self.assertEqual(len(self.answers["pair2a"].serialization),
                         PAIR_TWO_LENGTH)
        self.assertEqual(self.answers["pair2a"].digest, PAIR_TWO)

    def test_the_design_quotes_these_digests(self) -> None:
        """The design records 16-hex prefixes; this pins the full values to them."""
        design = (ROOT / "docs" / "DESIGN-foreign-voice.md").read_text(
            encoding="utf-8")
        self.assertIn(PAIR_ONE[:16], design)
        self.assertIn(PAIR_TWO[:16], design)

    def test_the_slot_renaming_the_lexicon_performs_is_invisible(self) -> None:
        """The property the loanword lexicon's slot marker actually depends on.

        The renderer erases `a`, `b` to `variable zero`, `variable one` and the
        inverse writes them back as `v0`, `v1`. If that renaming moved the
        digest, every round trip would fail for a reason that has nothing to do
        with the words — which is exactly why the design made binder-name
        independence a property of the serializer's type.
        """
        answers = self.oracle.serialize([
            ("named", "∀ a b : Rat, a + b = b + a"),
            ("slots", "∀ v0 v1 : Rat , v0 + v1 = v1 + v0"),
        ])
        self.assertTrue(answers["named"].ok, answers["named"].error)
        self.assertTrue(answers["slots"].ok, answers["slots"].error)
        self.assertEqual(answers["named"].digest, answers["slots"].digest)


@unittest.skipUnless(HAVE_LEAN, "pinned Lean toolchain not installed")
class RunStability(unittest.TestCase):
    """B-P(ii) and B5 — two runs, byte-identical, or the oracle is not a function."""

    TERMS = [
        ("s0", "∀ a b c : Rat, a^2 + b^2 + c^2 ≥ a*b + b*c + c*a"),
        ("s1", "∀ x : Rat, x ≠ 1 → (x^2 + x + 1) / (x - 1) ^ 2 ≥ 1 / 4"),
        ("s2", "¬ ∃ x : Rat, x^4 + x^3 - x + 1 = 0"),
        ("s3", "∀ n : Nat, 2 ≤ n → 5 ^ n + 9 < 6 ^ n"),
        ("s4", "∀ k : Int, (k - 1) * k * (k + 1) * (k + 2) = (k ^ 3 - k) * (k + 2)"),
    ]

    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = fvo.load()
        cls.first = cls.oracle.serialize(cls.TERMS)
        cls.second = cls.oracle.serialize(cls.TERMS)

    def test_two_runs_agree_byte_for_byte(self) -> None:
        for tag, _term in self.TERMS:
            with self.subTest(tag=tag):
                self.assertTrue(self.first[tag].ok, self.first[tag].error)
                self.assertEqual(self.first[tag].serialization,
                                 self.second[tag].serialization)

    def test_batching_does_not_change_an_answer(self) -> None:
        """A digest that depended on its neighbours would not be a function."""
        alone = self.oracle.serialize([self.TERMS[2]], batch_size=1)
        self.assertEqual(alone["s2"].digest, self.first["s2"].digest)

    def test_the_settings_the_run_carries_are_the_committed_ones(self) -> None:
        """B5: asserted as committed settings, not left to a flag."""
        preamble = self.oracle.preamble()
        self.assertIn("set_option autoImplicit false", preamble)
        self.assertIn("set_option relaxedAutoImplicit false", preamble)
        self.assertIn(f"set_option maxHeartbeats {self.oracle.rule.max_heartbeats}",
                      preamble)


@unittest.skipUnless(HAVE_LEAN, "pinned Lean toolchain not installed")
class FailureIsNamedNotSilent(unittest.TestCase):
    """B2 — the outcomes are distinguished and none is a silent drop."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = fvo.load()

    def test_a_mathlib_head_is_reported_as_an_unknown_identifier(self) -> None:
        """The register's largest entry, arriving with its reason attached."""
        row = self.oracle.digest_of("Real.sqrt x ≥ 0")
        self.assertFalse(row.ok)
        self.assertIn("Real.sqrt", row.error)
        self.assertEqual(row.digest, "")

    def test_auto_implicit_is_really_off(self) -> None:
        """Correction 3's measurement, as a one-line assertion.

        At Lean's defaults an unknown identifier is auto-bound and this
        elaborates. With the committed settings it must not.
        """
        row = self.oracle.digest_of("∀ x : Rat, x + unbound_name = 0")
        self.assertFalse(row.ok)
        self.assertIn("unbound_name", row.error)

    def test_a_batch_where_every_tag_fails_to_parse_is_not_a_refusal(self) -> None:
        """The bug C-V1 found before it ever ran.

        An earlier guard read "every tag in this batch is missing" as a
        file-level failure and refused. But C-V1 is the one control built to
        feed the oracle deliberate nonsense — text inverted through a SCRAMBLED
        table — and a batch of that can legitimately have every tag fail to
        parse. The guard turned the control into a run abort.

        The sentinels are the authority on file-level failure instead, and are
        strictly better at it: they sit after every statement, so a preamble
        that did not compile leaves them unanswered. If they answered, the file
        was fine and the missing tags are genuine parse errors, however many.
        """
        answers = self.oracle.serialize([
            ("a", "∀ a b : Rat, ((a + b"),
            ("b", "∀ x y : Rat, ((x * y"),
            ("c", "∀ p q : Rat, ((p - q"),
        ])
        self.assertEqual(set(answers), {"a", "b", "c"})
        for tag in ("a", "b", "c"):
            with self.subTest(tag=tag):
                self.assertFalse(answers[tag].ok)
                self.assertIn("parse_error", answers[tag].error)

    def test_a_bystander_of_a_parse_error_still_gets_its_answer(self) -> None:
        """A swallowed command is re-probed alone before it is called a failure."""
        answers = self.oracle.serialize([
            ("broken", "∀ a b : Rat, ((a + b"),
            ("fine", "∀ a b : Rat, a + b = b + a"),
        ])
        self.assertFalse(answers["broken"].ok)
        self.assertIn("parse_error", answers["broken"].error)
        self.assertTrue(answers["fine"].ok, answers["fine"].error)

    def test_nothing_in_the_serializer_path_proves_anything(self) -> None:
        """No `sorry`, no axiom audit, no verdict. §4's boundary, in the bytes."""
        text = (ROOT / "prover" / "lean" / "normalizer" /
                "Serialize.lean").read_text(encoding="utf-8")
        code = _strip_lean_comments(text)
        # `hasSorry` survives the strip and must: it is the guard, not a use.
        code = code.replace("hasSorry", "")
        for forbidden in ("#print axioms", "sorry", ":= by", "theorem ",
                          "example ", "axiom "):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, code)

    def test_the_guards_h2_added_are_in_the_code_and_not_only_the_comment(
            self) -> None:
        """A guard described in a docstring and absent from the code is prose."""
        code = _strip_lean_comments(
            (ROOT / "prover" / "lean" / "normalizer" /
             "Serialize.lean").read_text(encoding="utf-8"))
        self.assertIn("hasExprMVar", code)
        self.assertIn("hasSorry", code)
        self.assertIn("withoutErrToSorry", code)


class PreregOrdering(unittest.TestCase):
    """C-R3's discipline, imported: the serializer's digest lands with it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))

    def test_the_serializer_and_driver_are_frozen_now(self) -> None:
        frozen = {row["path"]: row for row in self.prereg["frozen"]}
        for path in ("prover/lean/normalizer/Serialize.lean",
                     "scripts/foreign_voice_oracle.py"):
            with self.subTest(path=path):
                self.assertIn(path, frozen)
                digest = hashlib.sha256(
                    (ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                self.assertEqual(digest, frozen[path]["sha256_lf"])

    def test_the_prototype_is_still_in_the_tree_unmoved(self) -> None:
        """H4 kept it so the design's digests are reproducible, not remembered."""
        frozen = {row["path"]: row for row in self.prereg["frozen"]}
        digest = hashlib.sha256(
            PROTOTYPE.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        self.assertEqual(
            digest, frozen["prover/lean/normalizer/Serialize.prototype.lean"]["sha256_lf"])

    def test_b_p_precedes_the_frozen_register_in_the_git_history(self) -> None:
        """§10's order: B-P, then B4.

        Two earlier versions of this asserted, in turn, that the register was
        the only `pending` row and that its prereg row said "promoted". The
        first was true of one commit; the second was a string. The history is
        neither.
        """
        assert_added_before(
            self, "prover/lean/normalizer/Serialize.lean",
            "data/foreign_voice/register.json",
            "§10 discharges B-P before the register is frozen, so the identity "
            "witness exists before the inventory of what it cannot witness")


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
