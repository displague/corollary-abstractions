#!/usr/bin/env python3
"""The transliteration lane: the two glyph equivalences and what they may move.

ROADMAP-v0.19 item 3a. Three separable claims are checked here, and they are
separable on purpose because each could be true while the others are false:

- **The equivalence is exact.** `≥` is not merely accepted; it produces the
  same token, the same tree and the same canonical skeleton as `>=`. A
  tokenizer that accepted the glyph and built a different relation would parse
  more of the corpus and mean something else by it.
- **The scope is two glyphs.** Every other unicode character the corpus carries
  is still refused. The lane's claim is about an alphabet, and a claim about an
  alphabet made by a change that quietly admitted a grammar would be false.
- **The change is additive at the surface.** `experiments/transliteration_
  served_diff.json` is the artifact rule 3 of the re-freeze discipline owes;
  these tests assert its central claim rather than trusting the file that
  asserts it about itself.

The successor-pin assertions live with the tests that used to read the retired
pin — `test_realization_lexicon`, `test_realize_term`, `test_measure_realization`
and `test_foreign_voice_lexicon` — because the point of re-aiming them was that
the digest keeps a witness in the place a reader already looks for one. What is
checked here is the successor prereg's own internal consistency.

The regeneration test is SLOW (four child interpreters, two of them sweeping
12,777 statements; ~100 s) and is skipped unless `COROLLARY_SLOW_TESTS=1`.
Skipped rather than deleted, and named in the skip message, because "the
artifact regenerates" is the only claim in this file that cannot be checked by
reading the artifact.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import match_signatures as ms  # noqa: E402

PREREG_PATH = ROOT / "experiments" / "transliteration_prereg.json"
RETIRED_PREREG = ROOT / "experiments" / "realization_prereg.json"
DIFF_PATH = ROOT / "experiments" / "transliteration_served_diff.json"
TASKS_PATH = ROOT / "experiments" / "throughput_tasks.json"

RETIRED_DIGEST = (
    "65fead2f47b6a2cea068cf2ee76db89e6e1bf0fcc7ab57220cdac328be05b599")


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _parse(text: str):
    return ms.canonicalize(ms.Parser(ms.tokenize(text)).parse())


class GlyphEquivalenceTests(unittest.TestCase):
    """`≥` IS `>=`, at the token and everywhere downstream of it."""

    def test_the_glyphs_tokenize_to_the_ascii_relations(self) -> None:
        self.assertEqual(ms.tokenize("a ≥ b"), ["a", ">=", "b"])
        self.assertEqual(ms.tokenize("a ≤ b"), ["a", "<=", "b"])

    def test_the_map_is_exactly_two_rows(self) -> None:
        """The scope limit, asserted rather than described.

        A later commit that adds a third row to `GLYPH_EQUIVALENTS` without a
        new preregistration entry breaks this, which is the intent: the lane's
        floors were frozen against a two-glyph change.
        """
        self.assertEqual(ms.GLYPH_EQUIVALENTS, {"≥": ">=", "≤": "<="})

    def test_the_two_spellings_canonicalize_identically(self) -> None:
        for glyph, ascii_form in ms.GLYPH_EQUIVALENTS.items():
            for template in ("a {} b", "x + 1 {} y * 2", "f(a, b) {} c^2"):
                with self.subTest(glyph=glyph, template=template):
                    self.assertEqual(_parse(template.format(glyph)),
                                     _parse(template.format(ascii_form)))

    def test_the_skeletons_agree_too(self) -> None:
        """Skeleton equality is what the round-trip gate actually compares."""
        self.assertEqual(ms.skeleton(_parse("a ≥ b + 1")),
                         ms.skeleton(_parse("a >= b + 1")))

    def test_the_relation_carried_in_the_tree_is_the_ascii_one(self) -> None:
        """Resolved at the token, so nothing downstream gains a vocabulary row.

        If the tree carried `≥` as its own relation, `RELATIONS`, the
        canonicalizer's symmetric-relation handling and the realization lexicon
        would each need a row, and each of those rows is a place two spellings
        of one relation could drift apart.
        """
        tree = _parse("a ≥ b")
        self.assertEqual(tree[0], "rel")
        self.assertEqual(tree[1], ">=")
        self.assertNotIn("≥", ms.RELATIONS)
        self.assertNotIn("≤", ms.RELATIONS)

    def test_no_other_unicode_is_admitted(self) -> None:
        """Two glyphs, and the ones deliberately left out stay left out."""
        for glyph in ("≠", "∈", "∀", "∃", "√", "∞", "×", "↑", "≡", "⊆"):
            with self.subTest(glyph=glyph):
                with self.assertRaises(ms.TemplateParseError):
                    ms.tokenize(f"a {glyph} b")

    def test_the_ascii_relations_are_untouched(self) -> None:
        """P-E1's ordering rule still holds: `<=` beats a standalone `<`."""
        self.assertEqual(ms.tokenize("a <= b"), ["a", "<=", "b"])
        self.assertEqual(ms.tokenize("a >= b"), ["a", ">=", "b"])
        self.assertEqual(ms.tokenize("a < b"), ["a", "<", "b"])
        self.assertEqual(ms.tokenize("a > b"), ["a", ">", "b"])


class LexiconNeedsNoRowsTests(unittest.TestCase):
    """The finding that made a second dated amendment unnecessary.

    The roadmap's step list anticipated adding `≥` / `≤` rows to
    `data/realization/lexicon.json` and recording another amendment for it.
    Measured instead: the rows are not needed, and — more than that — the
    committed loader REFUSES them. Both halves are asserted, because "not
    needed" and "not admissible" are different facts and only the second one
    closes the question.
    """

    @classmethod
    def setUpClass(cls) -> None:
        import realization_lexicon as rl

        cls.rl = rl
        cls.raw = json.loads(
            (ROOT / "data" / "realization" / "lexicon.json").read_text(
                encoding="utf-8"))

    def test_the_committed_table_has_no_glyph_rows(self) -> None:
        for section in ("relations", "operators", "call_heads", "structural"):
            for key in self.raw[section]:
                self.assertNotIn(key, ("≥", "≤"), section)

    def test_the_ascii_relations_already_carry_the_english(self) -> None:
        self.assertEqual(self.raw["relations"][">="], "is at least")
        self.assertEqual(self.raw["relations"]["<="], "is at most")

    def test_a_glyph_row_sharing_the_phrase_is_refused_forward(self) -> None:
        injured = json.loads(json.dumps(self.raw))
        injured["relations"]["≥"] = "is at least"
        with self.assertRaises(self.rl.LexiconError) as caught:
            self.rl.build(injured)
        self.assertIn("B2", str(caught.exception))

    def test_a_glyph_row_with_its_own_phrase_is_refused_in_reverse(self) -> None:
        """B7: the emitted token must tokenize to itself, and `≥` no longer does.

        This is the deeper reason the alternative is closed. Even a row that
        dodged B2 by inventing a different English phrase would emit the token
        `≥`, which the widened tokenizer now reads back as `>=` — a fluent
        sentence that re-parses to a tree the row did not describe. That is the
        `neg` bug of 2026-08-23 in a new spelling, and the gate added in
        response catches it here without being asked.
        """
        injured = json.loads(json.dumps(self.raw))
        injured["relations"]["≥"] = "is no smaller than"
        with self.assertRaises(self.rl.LexiconError):
            self.rl.build(injured)


class SuccessorPreregTests(unittest.TestCase):
    """The pin the amendment named, and its consistency with what it retired."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        cls.retired = json.loads(RETIRED_PREREG.read_text(encoding="utf-8"))

    def test_the_parser_row_matches_the_tree(self) -> None:
        """Re-aimed 2026-08-24 by `transliteration.prereg.v1.amendment.exact-literals-2026-08-24`.

        This file was the successor pin until ROADMAP-v0.20 §4b retired its
        parser row in turn — two cycles have now touched one file, which is
        exactly the case a single hop gets wrong. The row is checked against
        whatever the declared chain ends at, and the chain must be complete:
        `resolve_pin` raises on a marker naming an amendment this file does
        not record, so a retirement cannot become a way to stop checking.

        Re-aimed again 2026-09-01 by
        `exact_literals.prereg.v1.amendment.big-op-disclosure-2026-09-01`
        (ROADMAP-v0.25 §2, the `sum_total` silent-capture lane), which retired
        the exact-literals parser row into
        experiments/big_op_disclosure_prereg.json. THREE cycles have now
        touched this one file. Only the expected END of the chain moves here;
        the assertion above it — that the chain's terminal pin equals the tree
        — is untouched and is what actually does the checking. Re-aiming
        without an amendment to cite would be a test edited to make a change
        pass, so the amendment is named in this docstring and exists in that
        file's `amendments` array.
        """
        import prereg_pins

        row = {r["role"]: r for r in self.doc["frozen"]}["parser"]
        self.assertEqual(row["path"], "scripts/match_signatures.py")
        live = prereg_pins.resolve_pin(
            self.doc, row, prereg_path="experiments/transliteration_prereg.json"
        )
        self.assertEqual(_sha256_lf(ROOT / row["path"]), live["sha256_lf"])
        self.assertEqual(
            live["source"], "experiments/big_op_disclosure_prereg.json",
            "the parser chain must end at the pin the LAST amendment named — "
            "ROADMAP-v0.25 §2's big-op-disclosure-2026-09-01, which retired "
            "§4b's exact-literals pin in turn",
        )

    def test_it_names_the_digest_it_supersedes(self) -> None:
        row = {r["role"]: r for r in self.doc["frozen"]}["parser"]
        self.assertEqual(row["supersedes"]["sha256_lf"], RETIRED_DIGEST)
        self.assertNotEqual(row["sha256_lf"], RETIRED_DIGEST)

    def test_the_retired_prereg_points_here(self) -> None:
        """The chain has to close in both directions or it is not a chain."""
        amendment = self.retired["amendments"][0]
        self.assertEqual(amendment["successor_prereg"]["path"],
                         "experiments/transliteration_prereg.json")

    def test_the_lexicon_pin_agrees_with_the_one_it_re_records(self) -> None:
        here = {r["role"]: r for r in self.doc["frozen"]}["lexicon"]
        there = {r["role"]: r for r in self.retired["frozen"]}["lexicon"]
        self.assertEqual(here["sha256_lf"], there["sha256_lf"],
                         "two preregs pinning one table must pin one digest")

    def test_the_parse_gain_floor_is_frozen_and_has_no_round_trip_floor(
            self) -> None:
        floors = self.doc["frozen_floors"]
        self.assertEqual(floors["parse_gain"]["floor"], 6000)
        self.assertIsNone(floors["round_trip"]["floor"])
        self.assertTrue(floors["round_trip"]["no_floor_is_pre_committed"])

    def test_the_registered_run_row_is_pending_until_it_exists(self) -> None:
        pending = {row["path"]: row for row in self.doc["pending"]}
        script = "scripts/measure_transliteration.py"
        if (ROOT / script).exists():
            frozen = {row["path"]: row for row in self.doc["frozen"]}
            self.assertIn(script, frozen)
            self.assertIn("recorded", frozen[script])
            self.assertNotIn(script, pending)
        else:
            self.assertIn(script, pending)
            self.assertEqual(pending[script]["sha256_lf"], "pending")


class ServedDiffTests(unittest.TestCase):
    """Rule 3's artifact, and the additive-only claim it exists to support."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(DIFF_PATH.read_text(encoding="utf-8"))
        cls.tasks = json.loads(TASKS_PATH.read_text(encoding="utf-8"))

    def test_it_is_lf(self) -> None:
        self.assertNotIn(b"\r\n", DIFF_PATH.read_bytes())

    def test_nothing_previously_served_changed_or_was_lost(self) -> None:
        """The claim the lane stops on. Zero is the only passing value."""
        self.assertEqual(self.doc["claim"]["changed"], 0)
        self.assertEqual(self.doc["claim"]["lost"], 0)
        self.assertEqual(self.doc["corpus_wide_reading"]["changed"], 0)
        self.assertEqual(self.doc["corpus_wide_reading"]["lost"], 0)
        self.assertTrue(self.doc["claim"]["additive_only"])
        self.assertTrue(self.doc["corpus_wide_reading"]["additive_only"])

    def test_the_corpus_reading_gains_clear_the_frozen_floor(self) -> None:
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        floor = prereg["frozen_floors"]["parse_gain"]["floor"]
        self.assertGreaterEqual(self.doc["corpus_wide_reading"]["gained"], floor)

    def test_the_two_sides_were_two_different_parsers(self) -> None:
        """Without this, a diff of nothing and a change of nothing look alike.

        The generator's first draft ordered sys.path, which `answer.py:47`
        defeats, and produced a clean diff in which both sides were the NEW
        parser. Every child now reports the parser it loaded and the artifact
        carries all four readings, so the failure mode is visible in the file.
        """
        used = self.doc["mechanism"]["each_child_reports_the_parser_it_loaded"]
        after = self.doc["mechanism"]["after_parser_sha256_lf"]
        self.assertEqual(used["book_before"], RETIRED_DIGEST)
        self.assertEqual(used["corpus_before"], RETIRED_DIGEST)
        self.assertEqual(used["book_after"], after)
        self.assertEqual(used["corpus_after"], after)
        self.assertNotEqual(after, RETIRED_DIGEST)
        # Re-aimed 2026-08-24 by `…amendment.exact-literals-2026-08-24`: the
        # `after` side of THIS diff is the v0.19 transliteration parser, which
        # §4b has since superseded. The artifact records what it compared; the
        # tree has legitimately moved past both of its sides.
        self.assertNotEqual(
            after, _sha256_lf(ROOT / "scripts/match_signatures.py"),
            "this diff's `after` parser is itself retired now; agreeing with "
            "the tree would mean the record moved with it",
        )

    def test_the_witness_gap_is_real_and_the_eleven_are_unmoved(self) -> None:
        """Rule 3's premise, checked instead of quoted.

        `match_signatures.py` is not one of the witnessed modules — that is why
        this artifact is owed. And all eleven that ARE witnessed still match the
        tree, which is what makes the point: the seal is green and the rendered
        output moved anyway.
        """
        witnessed = self.tasks["rendering_module_digests"]
        self.assertNotIn("scripts/match_signatures.py", witnessed)
        self.assertFalse(
            self.doc["the_witness_gap_named_concretely"][
                "match_signatures_is_witnessed"])
        for path, digest in witnessed.items():
            with self.subTest(module=path):
                self.assertEqual(_sha256_lf(ROOT / path), digest)

    def test_the_book_reading_is_reported_even_though_it_is_empty(self) -> None:
        """Zero gains over the book is a result, and it has to be published.

        The book addresses no glyph-carrying statement, so its diff is thirty
        unchanged rows. That is exactly the reading a lane could be tempted to
        leave out; the artifact reports it and says what it does and does not
        establish.
        """
        self.assertEqual(self.doc["claim"]["gained"], 0)
        self.assertEqual(self.doc["claim"]["unchanged"], self.doc["scope"]["count"])
        self.assertTrue(any("ZERO GAINS" in line
                            for line in self.doc["the_book_reading"]))

    @unittest.skipUnless(os.environ.get("COROLLARY_SLOW_TESTS") == "1",
                         "~100 s: four child interpreters, two full corpus "
                         "sweeps. Run with COROLLARY_SLOW_TESTS=1, or directly: "
                         "python scripts/transliteration_served_diff.py --check")
    def test_it_regenerates_identically(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "transliteration_served_diff.py"),
             "--check"],
            cwd=str(ROOT), capture_output=True, text=True,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


def _synthetic_corpus(root: Path, rows: list[tuple[str, str]]) -> Path:
    """A tiny data dir of hand-written statements.

    The committed corpora cannot serve here: every glyph-carrying statement in
    the tree is in `lean_workbook` (12,514 nodes, ~76 s to walk), and no small
    corpus carries a glyph at all. So determinism and the refusal path are
    exercised over statements written for the purpose, which also lets a test
    ASK for a refusal instead of hoping the corpus supplies one.
    """
    target = root / "synthetic"
    target.mkdir(parents=True)
    (target / "nodes.json").write_text(json.dumps({
        "schema": "corollary.corpus.v1",
        "corpus_id": "synthetic",
        "discipline": "synthetic",
        "version": "1",
        "statement_nodes": [
            {"statement_id": sid, "formal_statement": {"canonical_ascii": src}}
            for sid, src in rows
        ],
    }, ensure_ascii=False), encoding="utf-8")
    return root


class RegisteredRunTests(unittest.TestCase):
    """The lane's artifact: its floors, its partition, and its witness."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.path = ROOT / "experiments" / "transliteration_rate.json"
        cls.doc = json.loads(cls.path.read_text(encoding="utf-8"))

    def test_it_is_lf(self) -> None:
        self.assertNotIn(b"\r\n", self.path.read_bytes())

    def test_it_carries_no_wall_clock(self) -> None:
        """A timestamp would make "the registered run" unreproducible."""
        def keys(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    yield key
                    yield from keys(value)
            elif isinstance(node, list):
                for item in node:
                    yield from keys(item)

        found = set(keys(self.doc))
        for forbidden in ("elapsed", "timestamp", "wall_clock", "started_at",
                          "generated_at", "run_at", "duration"):
            self.assertNotIn(forbidden, found)

    def test_it_is_the_run_over_the_committed_corpus(self) -> None:
        self.assertTrue(self.doc["over_the_committed_corpus"]["yes"])

    def test_the_parse_gain_floor_is_met(self) -> None:
        parse = self.doc["parse_rate"]
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        floor = prereg["frozen_floors"]["parse_gain"]["floor"]
        self.assertEqual(parse["floor"], floor)
        self.assertGreaterEqual(parse["newly_reached"], floor)
        self.assertTrue(parse["floor_met"])

    def test_the_parse_arithmetic_closes(self) -> None:
        parse = self.doc["parse_rate"]
        self.assertEqual(
            parse["under_the_retired_parser"]["parseable"] + parse["newly_reached"],
            parse["parseable"],
        )
        self.assertLessEqual(parse["parseable"], parse["nodes_total"])

    def test_the_retired_parser_count_reproduces_v018(self) -> None:
        """2,172 was v0.18's R0. Recomputed on the same walk, it must agree.

        This is what makes the two artifacts comparable statement for statement
        instead of approximately: if the walk had drifted, the denominators
        would differ and nobody quoting both rates would know.
        """
        historical = json.loads(
            (ROOT / "experiments" / "realization_rate.json").read_text(
                encoding="utf-8"))
        self.assertEqual(
            self.doc["parse_rate"]["under_the_retired_parser"]["parseable"],
            historical["r1"]["denominator"],
        )

    def test_the_round_trip_partition_balances(self) -> None:
        trip = self.doc["round_trip"]
        self.assertTrue(trip["partition_balances"])
        self.assertEqual(trip["served"] + trip["refused"] + trip["failed"],
                         trip["denominator"])
        self.assertEqual(trip["denominator"],
                         self.doc["parse_rate"]["newly_reached"])

    def test_no_round_trip_floor_was_pre_committed(self) -> None:
        """The probe's defining property, asserted in the artifact too."""
        self.assertTrue(self.doc["round_trip"]["no_floor_was_pre_committed"])
        self.assertNotIn("floor_met", self.doc["round_trip"])

    def test_refusals_are_reported_by_class(self) -> None:
        """Not aggregated, even when the count is zero.

        A zero here is a fact about which statements the two glyphs unlock, and
        it stays checkable only if the shape that would hold a non-zero is
        present rather than omitted.
        """
        trip = self.doc["round_trip"]
        self.assertIsInstance(trip["refusals_by_reason"], dict)
        self.assertEqual(sum(trip["refusals_by_reason"].values()),
                         trip["refused"])
        self.assertEqual(len(trip["failures"]), trip["failed"])

    def test_the_cross_check_agrees_with_its_independent_witness(self) -> None:
        cross = self.doc["parse_rate"]["cross_check"]
        self.assertTrue(cross["agrees"])
        self.assertEqual(
            cross["witness_gained"],
            self.doc["parse_rate"]["newly_reached"]
            - self.doc["round_trip"]["refused"]
            - self.doc["round_trip"]["failed"],
        )
        self.assertEqual(
            cross["witness_sha256_lf"],
            _sha256_lf(ROOT / "experiments" / "transliteration_served_diff.json"))

    def test_the_composition_travels_with_the_rate(self) -> None:
        """R1's rule imported: a rate never travels without its denominator."""
        comp = self.doc["newly_reached_composition"]
        self.assertEqual(comp["statements"],
                         self.doc["round_trip"]["denominator"])
        self.assertEqual(sum(row["newly_reached"] for row in comp["per_corpus"]),
                         comp["statements"])
        self.assertEqual(sum(comp["relations_present"].values()),
                         sum(comp["glyph_occurrences"].values()))
        self.assertTrue(comp["reading"])

    def test_it_says_what_the_rate_does_not_establish(self) -> None:
        """A 1.0 over a narrow set must not be readable as corpus coverage."""
        said = self.doc["round_trip"]["what_this_rate_does_and_does_not_establish"]
        self.assertTrue(any("DOES NOT ESTABLISH" in line for line in said))

    def test_it_does_not_blend_with_the_historical_artifact(self) -> None:
        self.assertIn("never blended",
                      self.doc["round_trip"]["not_averaged_with_v018"])

    def test_the_prereg_revalidation_holds_and_names_the_parser(self) -> None:
        """Re-aimed 2026-08-24 by `…amendment.exact-literals-2026-08-24`.

        This artifact is a RECORD OF A MEASUREMENT, not a live gate. It used
        to be checked against the tree, which was right while the tree still
        carried the parser it ran under. ROADMAP-v0.20 §4b moved that parser,
        so asking this artifact to match the tree would be asking a closed
        question — and worse, passing it would mean the record had been
        edited underneath the number it reports.

        What stays checkable is the identity the run declared: the digest it
        names is the one the amendment retired, and it is NOT the tree's.
        """
        gate = self.doc["prereg_revalidated"]
        self.assertEqual(gate["verdict"], "HOLDS")
        used = gate["the_parser_this_run_used"]
        self.assertEqual(used["supersedes"], RETIRED_DIGEST)
        live = _sha256_lf(ROOT / "scripts" / "match_signatures.py")
        self.assertNotEqual(
            used["sha256_lf"], live,
            "the tree has moved past this run's parser; if these agree the "
            "record was edited under the number it reports",
        )
        for row in gate["revalidated"]:
            self.assertTrue(row["agrees"], row["path"])


class RegisteredRunRefusalTests(unittest.TestCase):
    """The writer's own stop conditions, exercised rather than described."""

    @classmethod
    def setUpClass(cls) -> None:
        import measure_transliteration as mt

        cls.mt = mt

    def _refuses(self, prereg: dict) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            injured = Path(tmp) / "prereg.json"
            injured.write_text(json.dumps(prereg), encoding="utf-8")
            with self.assertRaises(self.mt.PreregMismatch) as caught:
                self.mt.revalidate_prereg(injured)
        return str(caught.exception)

    def test_a_drifted_pin_refuses_to_write(self) -> None:
        """Re-aimed 2026-08-24: corrupt a LIVE pin, not a retired one.

        This used to corrupt the `parser` row, which §4b has since retired —
        and a retired row's own digest is deliberately no longer what the
        tree is checked against, so corrupting it now proves nothing. The
        lexicon row carries a live pin and makes the same point.
        """
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        for row in prereg["frozen"]:
            if row["role"] == "lexicon":
                self.assertNotIn("retired_for_future_comparisons", row)
                row["sha256_lf"] = "0" * 64
        self.assertIn("lexicon.json", self._refuses(prereg))

    def test_retiring_a_pin_is_not_a_way_to_stop_checking_it(self) -> None:
        """The escape hatch this amendment must not have opened.

        A retired row is checked against the SUCCESSOR pin. So corrupting the
        successor must still refuse — otherwise "retired in writing" would be
        a way to launder a file out of every check it was under.

        Rebuilt 2026-09-01 for the third hop
        (`exact_literals.prereg.v1.amendment.big-op-disclosure-2026-09-01`).
        The chain is now transliteration -> exact_literals -> big_op_disclosure,
        and the pin that DECIDES is the one at the end, so that is the one this
        fixture corrupts. Corrupting the middle would prove nothing, which is
        the same reason the lexicon test above says its own row is the live
        one. Both hops are built inside the temp root, so the walk really
        walks two of them rather than being cut short.
        """
        import prereg_pins

        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        middle = json.loads(
            (ROOT / "experiments" / "exact_literals_prereg.json").read_text(
                encoding="utf-8"))
        end = json.loads(
            (ROOT / "experiments" / "big_op_disclosure_prereg.json").read_text(
                encoding="utf-8"))
        row = {r["role"]: r for r in prereg["frozen"]}["parser"]
        self.assertIn("retired_for_future_comparisons", row)
        self.assertIn(
            "retired_for_future_comparisons",
            {r["role"]: r for r in middle["frozen"]}["parser"],
            "the middle hop must itself be retired or this fixture is not "
            "exercising a two-hop walk",
        )

        # A chain whose TERMINAL parser pin is corrupt. Resolution must follow
        # the chain all the way TO it, so the tree is then compared against a
        # digest that cannot match — i.e. the retirement did not stop the check.
        for live in end["frozen"]:
            if live["role"] == "parser":
                live["sha256_lf"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "experiments").mkdir()
            prereg["amendments"][0]["successor_prereg"]["path"] = (
                "experiments/corrupt_middle.json")
            for entry in middle["amendments"]:
                entry["successor_prereg"]["path"] = "experiments/corrupt_end.json"
            (root / "experiments" / "corrupt_middle.json").write_text(
                json.dumps(middle), encoding="utf-8")
            (root / "experiments" / "corrupt_end.json").write_text(
                json.dumps(end), encoding="utf-8")
            resolved = prereg_pins.resolve_pin(
                prereg, row,
                prereg_path="experiments/transliteration_prereg.json",
                repo_root=root,
            )
        self.assertEqual(
            resolved["hops"],
            ["experiments/corrupt_middle.json", "experiments/corrupt_end.json"],
            "the walk must traverse both declared hops, not stop at the first",
        )
        self.assertEqual(
            resolved["sha256_lf"], "0" * 64,
            "resolution did not follow the retirement to the successor pin",
        )
        self.assertNotEqual(
            resolved["sha256_lf"], _sha256_lf(ROOT / row["path"]),
            "a corrupted successor pin must disagree with the tree; if it "
            "agreed, retiring a row would be a way to launder a file out of "
            "every check it was under",
        )

    def test_a_retirement_naming_an_unrecorded_amendment_fails_loudly(self):
        """A pin deleted and a pin retired in writing are different things."""
        import prereg_pins

        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        row = {r["role"]: r for r in prereg["frozen"]}["parser"]
        row["retired_for_future_comparisons"]["amendment"] = "no-such-amendment"
        with self.assertRaises(prereg_pins.PinChainError):
            prereg_pins.resolve_pin(prereg, row, prereg_path="<test>")

    def test_a_pending_row_whose_file_exists_refuses_to_write(self) -> None:
        """A freeze written after the thing it froze is not a freeze."""
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        prereg["pending"] = [{"path": "scripts/match_signatures.py",
                              "role": "invented", "sha256_lf": "pending"}]
        with tempfile.TemporaryDirectory() as tmp:
            injured = Path(tmp) / "prereg.json"
            injured.write_text(json.dumps(prereg), encoding="utf-8")
            with self.assertRaises(self.mt.PreregMismatch) as caught:
                self.mt.revalidate_prereg(injured)
        self.assertIn("still `pending`", str(caught.exception))

    def test_a_partial_corpus_says_its_cross_check_was_skipped(self) -> None:
        """Skipping is fine; skipping silently is not."""
        with tempfile.TemporaryDirectory() as tmp:
            data = _synthetic_corpus(Path(tmp) / "data",
                                     [("s.a", "a ≥ b"), ("s.b", "a >= b")])
            doc = self.mt.build_artifact(data)
        self.assertFalse(doc["over_the_committed_corpus"]["yes"])
        cross = doc["parse_rate"]["cross_check"]
        self.assertIsNone(cross["agrees"])
        self.assertIn("not_applicable", cross)

    def test_an_uncovered_head_is_reported_as_a_refusal_with_its_class(
            self) -> None:
        """The refusal path by injection rather than by accident.

        The committed corpus happens to hand this lane a set the lexicon covers
        completely. That is a fact about the corpus, not a property of the
        writer, and a refusal table that has never been non-empty is a table
        nobody has checked. So a statement with a head no lexicon row covers is
        written on purpose and its class asserted.
        """
        with tempfile.TemporaryDirectory() as tmp:
            data = _synthetic_corpus(Path(tmp) / "data", [
                ("s.covered", "a ≥ b"),
                ("s.uncovered", "NOSUCHHEAD(a) ≥ b"),
            ])
            doc = self.mt.build_artifact(data)
        trip = doc["round_trip"]
        self.assertEqual(trip["denominator"], 2)
        self.assertEqual(trip["served"], 1)
        self.assertEqual(trip["refused"], 1)
        self.assertEqual(trip["refusals_by_reason"], {"uncovered_head": 1})
        self.assertTrue(trip["partition_balances"])

    def test_two_runs_over_one_tree_are_byte_identical(self) -> None:
        """R5 at artifact scale, on a slice so it costs a second not a minute."""
        sources = ["a ≥ b", "a ≤ b", "1 + 2 ≥ 3",
                   "x*y ≤ z^2", "a >= b", "c = d"]
        rows = [("s.%d" % i, src) for i, src in enumerate(sources)]
        with tempfile.TemporaryDirectory() as tmp:
            data = _synthetic_corpus(Path(tmp) / "data", rows)
            first = self.mt.build_artifact(data)
            second = self.mt.build_artifact(data)

        def dump(doc: dict) -> str:
            return json.dumps(doc, indent=2, ensure_ascii=False)

        self.assertEqual(dump(first), dump(second))
        self.assertEqual(first["round_trip"]["denominator"], 4)

    @unittest.skipUnless(os.environ.get("COROLLARY_SLOW_TESTS") == "1",
                         "~76 s over the full corpus. Run with "
                         "COROLLARY_SLOW_TESTS=1, or directly: python "
                         "scripts/measure_transliteration.py --no-write")
    def test_the_committed_artifact_regenerates(self) -> None:
        committed = json.loads(
            (ROOT / "experiments" / "transliteration_rate.json").read_text(
                encoding="utf-8"))
        fresh = self.mt.build_artifact(ROOT / "data")
        self.assertEqual(json.dumps(fresh, indent=2, ensure_ascii=False),
                         json.dumps(committed, indent=2, ensure_ascii=False))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
