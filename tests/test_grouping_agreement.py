#!/usr/bin/env python3
"""G1 and G1b, read from their artifact and spot-re-derived against the binary.

Two pre-run prerequisites with **no allowance between them**:

* **G1** — `R(s)` and `canon(R(s))` elaborate to byte-identical serializations,
  2,313 of 2,313.  One disagreement means `grouping.json` states a precedence
  the toolchain does not use, and one wrong level is wrong everywhere.
* **G1b** — every canonical grouping pair, deleted, changes the term or fails
  to elaborate.  The floor is the pair count itself.

The full measurement takes minutes of pinned-binary time, so it lives in
`experiments/grouping_agreement.json` and this module asserts its floors and
**re-derives a sample through the oracle** — enough that a fabricated or stale
artifact fails here rather than being taken on trust.  The sample is drawn by
a fixed rule, not by hand.

G1b is the gate that **demotes C-V4′'s `drop_group` to a confirmation**: a
50-statement sample cannot establish what a 5,228-pair census establishes, and
the design says in advance which governs if they disagree.
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

import grouping_canonical_probe as gp  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402

AGREEMENT_PATH = ROOT / "experiments" / "grouping_agreement.json"
DATA = ROOT / "data" / "foreign_voice"
RULE = gp.Rule.load()

#: How many statements and how many pair deletions to re-derive live. Small
#: enough to run in a suite, large enough that a fabricated artifact fails.
SAMPLE = 25


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _oracle():
    import foreign_voice_oracle as fvo
    try:
        return fvo.load()
    except fvo.OracleRefusal:
        return None


ORACLE = _oracle()


class G1TheCanonicalizerAgrees(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not AGREEMENT_PATH.exists():
            raise unittest.SkipTest("grouping_agreement.json has not been produced")
        cls.report = json.loads(AGREEMENT_PATH.read_text(encoding="utf-8"))

    def test_the_floor_is_every_statement_and_it_is_met(self) -> None:
        g1 = self.report["g1"]
        self.assertEqual(g1["floor"], g1["statements"])
        self.assertEqual(g1["agree"], g1["statements"])
        self.assertTrue(g1["floor_met"])
        self.assertEqual(g1["disagreements"], [])

    def test_it_covered_the_whole_covered_set(self) -> None:
        preview = json.loads((DATA / "eligibility_preview.json").read_text(encoding="utf-8"))
        register = json.loads((DATA / "register.json").read_text(encoding="utf-8"))
        self.assertEqual(self.report["g1"]["statements"],
                         len(mfv.covered_rows(preview, register)))

    def test_it_names_the_rule_it_was_measured_against(self) -> None:
        """A stale artifact is caught here rather than trusted."""
        self.assertEqual(self.report["inputs"]["grouping_rule_sha256_lf"],
                         _sha256_lf(DATA / "grouping.json"))
        self.assertEqual(self.report["inputs"]["probe_sha256_lf"],
                         _sha256_lf(ROOT / "scripts" / "grouping_canonical_probe.py"))

    @unittest.skipUnless(ORACLE, "pinned Lean toolchain not installed")
    def test_a_sample_re_derives_against_the_pinned_binary(self) -> None:
        preview = json.loads((DATA / "eligibility_preview.json").read_text(encoding="utf-8"))
        register = json.loads((DATA / "register.json").read_text(encoding="utf-8"))
        rows = mfv.covered_rows(preview, register)
        stride = max(1, len(rows) // SAMPLE)
        sample = rows[::stride][:SAMPLE]
        terms = []
        for index, row in enumerate(sample):
            terms.append((f"o{index}", row["interpreted"]))
            terms.append((f"c{index}", gp.canon(row["interpreted"], RULE)))
        answers = ORACLE.serialize(terms)
        for index, row in enumerate(sample):
            with self.subTest(statement_id=row["statement_id"]):
                original, canonical = answers[f"o{index}"], answers[f"c{index}"]
                self.assertTrue(original.ok, original.error)
                self.assertTrue(canonical.ok, canonical.error)
                self.assertEqual(original.digest, canonical.digest)


class G1bNoRedundantBracketSurvives(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not AGREEMENT_PATH.exists():
            raise unittest.SkipTest("grouping_agreement.json has not been produced")
        cls.report = json.loads(AGREEMENT_PATH.read_text(encoding="utf-8"))

    def test_the_floor_is_every_pair_and_it_is_met(self) -> None:
        g1b = self.report["g1b"]
        self.assertEqual(g1b["floor"], g1b["pairs_tested"])
        self.assertEqual(g1b["detected"], g1b["pairs_tested"])
        self.assertEqual(g1b["blind"], 0)
        self.assertTrue(g1b["floor_met"])
        self.assertEqual(g1b["blind_cases"], [])

    def test_the_pair_count_matches_the_census(self) -> None:
        census = json.loads(
            (ROOT / "experiments" / "grouping_census.json").read_text(encoding="utf-8"))
        self.assertEqual(self.report["g1b"]["pairs_tested"],
                         census["pairs"]["canonical_grouping_pairs"])

    def test_the_detection_split_is_published(self) -> None:
        """Two ways to detect, and a reader is owed which one did the work."""
        g1b = self.report["g1b"]
        self.assertEqual(
            g1b["detected_by_digest_change"] + g1b["detected_by_failing_to_elaborate"],
            g1b["detected"])

    def test_ascription_and_binder_group_pairs_are_excluded(self) -> None:
        excluded = self.report["g1b"]["excluded_by_pair_kind"]
        census = json.loads(
            (ROOT / "experiments" / "grouping_census.json").read_text(encoding="utf-8"))
        kinds = census["pairs"]["source_by_kind"]
        self.assertEqual(excluded["ascription"], kinds["ascription"])
        self.assertEqual(excluded["binder_group"], kinds["binder_group"])

    def test_it_says_it_governs_over_the_sample(self) -> None:
        self.assertIn("THE CENSUS GOVERNS", self.report["g1b"]["it_demotes_the_sample"])

    @unittest.skipUnless(ORACLE, "pinned Lean toolchain not installed")
    def test_a_sample_of_deletions_re_derives(self) -> None:
        """Delete a real pair from a real canonical surface; the term must move."""
        preview = json.loads((DATA / "eligibility_preview.json").read_text(encoding="utf-8"))
        register = json.loads((DATA / "register.json").read_text(encoding="utf-8"))
        rows = mfv.covered_rows(preview, register)
        cases = []
        for row in rows:
            emission = gp.emit(gp.parse(row["interpreted"], RULE), RULE)
            spans = gp.grouping_pair_spans(emission.tokens, emission.pair_kinds)
            if spans:
                cases.append((row["statement_id"], emission.tokens, spans[0]))
            if len(cases) >= SAMPLE:
                break
        self.assertEqual(len(cases), SAMPLE)
        terms = []
        for index, (_sid, tokens, span) in enumerate(cases):
            terms.append((f"c{index}", " ".join(tokens)))
            terms.append((f"m{index}", " ".join(gp.delete_pair(tokens, span))))
        answers = ORACLE.serialize(terms)
        for index, (sid, _t, _s) in enumerate(cases):
            with self.subTest(statement_id=sid):
                canonical, mutant = answers[f"c{index}"], answers[f"m{index}"]
                self.assertTrue(canonical.ok, canonical.error)
                detected = (not mutant.ok) or mutant.digest != canonical.digest
                self.assertTrue(detected,
                                "a canonical grouping pair was deleted and the "
                                "term did not move — G1b's whole claim")

    def test_the_deletion_is_by_matched_pair(self) -> None:
        """§3.3's defect in the inherited control, fixed rather than inherited.

        v0.19 deleted the first opening and the first closing independently.
        On a nesting statement those are not a pair at all.
        """
        tokens = gp.tokenize("( ( a + b ) * c ) + d", RULE)
        emission = gp.emit(gp.parse("((a + b) * c) + d", RULE), RULE)
        spans = gp.grouping_pair_spans(emission.tokens, emission.pair_kinds)
        self.assertTrue(spans)
        start, end = spans[0]
        self.assertEqual(emission.tokens[start], "(")
        self.assertEqual(emission.tokens[end], ")")
        del tokens
        # first-open + first-close would pair the OUTER open with the INNER
        # close; by index they are a real pair.
        opened = [i for i, t in enumerate(emission.tokens) if t == "("]
        closed = [i for i, t in enumerate(emission.tokens) if t == ")"]
        if len(opened) > 1:
            self.assertNotEqual((opened[0], closed[0]), spans[0])


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
