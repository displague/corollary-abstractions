#!/usr/bin/env python3
"""C-V3′: the refusal Correction 9 says must be BUILT, and the sheet's shape.

> **Correction 9.** The quotable refusal policy — *"digest-pinned here; token
> counting REFUSES (exit 2) when the file is absent or its digest mismatches —
> cannot-verify, never skip"* — is the **tokenizer's**.  `weights_blob_sha256`
> appears exactly once in the whole tree and **nothing reads it at run time**.
> So C-V3′ must BUILD the model-side refusal, not inherit it, *"with the
> sibling test the tokenizer already has"*.

This file is that sibling.  The refusal tests are **deliberately not skipped**
when the model is absent — that is the whole point of them, and it is the
discipline `tests/test_external_verifier.py` already applies to the pinned
toolchain.  Only the tests that need a live endpoint skip.

The other half asserts what the sheet is: four candidates, the truth among
them, three distractors from the C-V4′ mutation classes, and **the term never
shown as the answer**.  A blind reader that could see which one was marked
correct would not be blind.
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

import foreign_voice_lexicon as fvl  # noqa: E402
import grouping_canonical_probe as gp  # noqa: E402
import machine_reader as mr  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402

DATA = ROOT / "data" / "foreign_voice"
PILOT_PATH = ROOT / "experiments" / "c_v3_prime_pilot.json"


class TheRefusalIsBuiltNotInherited(unittest.TestCase):
    """Deliberately not skipped. An unpinnable model must never be a number."""

    def test_absent_weights_refuse_and_never_download(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            with self.assertRaises(mr.ReaderRefusal) as caught:
                mr.verify_weights(Path(scratch))
        message = str(caught.exception)
        self.assertIn("not downloading", message)
        self.assertIn("cannot-verify, never skip", message)

    def test_mismatched_weights_refuse(self) -> None:
        """A blob under the right NAME with the wrong BYTES must not pass.

        ollama names a blob by its digest, so trusting the filename would be
        checking the copy against itself — the reasoning the git-blob precedent
        states. The bytes are hashed.
        """
        pinned = mr.MANIFEST["model"]["weights_blob_sha256"]
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / f"sha256-{pinned}"
            path.write_bytes(b"not the weights")
            with self.assertRaises(mr.ReaderRefusal) as caught:
                mr.verify_weights(Path(scratch))
        self.assertIn("REFUSING", str(caught.exception))
        self.assertIn(pinned[:16], str(caught.exception))

    def test_the_pinned_digest_is_the_one_the_v017_baseline_pins(self) -> None:
        baseline = json.loads(
            (ROOT / "experiments" / "throughput_baseline.json").read_text(
                encoding="utf-8"))
        self.assertEqual(mr.MANIFEST["model"]["weights_blob_sha256"],
                         baseline["model"]["weights_blob_sha256"])
        self.assertEqual(mr.MANIFEST["model"]["provider_tag"],
                         baseline["model"]["provider_tag"])

    def test_it_does_not_inherit_the_baselines_sampling(self) -> None:
        """The throughput baseline runs at 0.7. This control pins 0."""
        baseline = json.loads(
            (ROOT / "experiments" / "throughput_baseline.json").read_text(
                encoding="utf-8"))
        self.assertEqual(mr.MANIFEST["sampling"]["temperature"], 0)
        self.assertNotEqual(mr.MANIFEST["sampling"]["temperature"],
                            baseline["sampling"].get("temperature"))
        self.assertIn("NOT inherited", mr.MANIFEST["sampling"]["sampling_source"])

    def test_it_records_requested_sampling_not_effective_sampling(self) -> None:
        """ollama's /v1 layer ignores some fields; the wording says so."""
        self.assertIn("sampling_requested", mr.MANIFEST["sampling"])
        self.assertIn("never claims what took effect",
                      mr.MANIFEST["sampling"]["not_settings_that_took_effect"])

    def test_it_says_it_grades_only(self) -> None:
        self.assertIn("no output reaches a served answer",
                      mr.MANIFEST["it_grades_only"])
        self.assertEqual(mr.MANIFEST["labelled"], "MACHINE-reader, never human")


class TheSheetIsBlind(unittest.TestCase):
    """Four candidates, the truth among them, and no mark on it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.lexicon = fvl.load()
        cls.rule = gp.Rule.load()
        raw = json.loads((DATA / "lexicon.json").read_text(encoding="utf-8"))
        cls.seed = mr._sha256_lf(DATA / "lexicon.json")
        cls.scrambled, _ = mfv.scrambled_lexicon(raw, cls.seed)
        cls.rows = mr.load_rows()
        cls.items = mr.build_items(cls.rows, cls.lexicon, cls.scrambled,
                                   cls.rule, 8, 4, cls.seed)

    def test_every_item_has_four_candidates_and_one_truth(self) -> None:
        for item in self.items:
            with self.subTest(statement_id=item.statement_id):
                self.assertEqual(len(item.candidates), 4)
                self.assertEqual(len(set(item.candidates)), 4,
                                 "a duplicated candidate makes the item unanswerable")
                self.assertIn(item.correct, range(4))

    def test_the_truth_is_the_canonical_term(self) -> None:
        by_id = {row["statement_id"]: row for row in self.rows}
        for item in self.items:
            with self.subTest(statement_id=item.statement_id):
                canonical = gp.canon(by_id[item.statement_id]["interpreted"],
                                     self.rule)
                self.assertEqual(item.candidates[item.correct], canonical)

    def test_every_distractor_comes_from_a_mutation_class(self) -> None:
        classes = {"drop_group", "shift_group", "swap_binder"}
        for item in self.items:
            with self.subTest(statement_id=item.statement_id):
                self.assertEqual(len(item.distractor_classes), 3)
                self.assertTrue(set(item.distractor_classes) <= classes)

    def test_the_prompt_never_marks_the_answer(self) -> None:
        """Blind means blind: nothing in the prompt distinguishes the truth."""
        for item in self.items:
            prompt = item.prompt()
            with self.subTest(statement_id=item.statement_id):
                self.assertNotIn("correct", prompt.lower())
                self.assertNotIn(item.arm, prompt)
                for letter in "ABCD":
                    self.assertIn(f"{letter}) ", prompt)

    def test_the_skeleton_arm_is_interleaved_and_unlabelled(self) -> None:
        arms = [item.arm for item in self.items]
        self.assertIn("served", arms)
        self.assertIn("skeleton", arms)
        self.assertNotEqual(arms, sorted(arms),
                            "an ordered sheet is not interleaved")

    def test_a_skeleton_item_shows_a_scrambled_sentence(self) -> None:
        by_id = {row["statement_id"]: row for row in self.rows}
        for item in self.items:
            if item.arm != "skeleton":
                continue
            with self.subTest(statement_id=item.statement_id):
                true_surface = mr.fv.render_interpreted(
                    by_id[item.statement_id]["interpreted"], self.lexicon)
                self.assertNotEqual(item.sentence, true_surface.surface)

    def test_the_sheet_is_deterministic_given_the_seed(self) -> None:
        again = mr.build_items(self.rows, self.lexicon, self.scrambled,
                               self.rule, 8, 4, self.seed)
        self.assertEqual([(i.statement_id, i.arm, i.correct) for i in again],
                         [(i.statement_id, i.arm, i.correct) for i in self.items])


class GradingIsMechanical(unittest.TestCase):
    """A letter, compared. No judgement anywhere in the scoring path."""

    def _item(self, correct: int) -> mr.Item:
        return mr.Item(statement_id="s", arm="served", sentence="x",
                       candidates=["a", "b", "c", "d"], correct=correct)

    def test_a_correct_letter_scores(self) -> None:
        result = mr.grade([self._item(2)], ["C"])
        self.assertEqual(result["per_arm"]["served"]["correct"], 1)

    def test_a_wrong_letter_does_not(self) -> None:
        result = mr.grade([self._item(2)], ["A"])
        self.assertEqual(result["per_arm"]["served"]["correct"], 0)

    def test_an_unparseable_answer_is_counted_not_guessed(self) -> None:
        result = mr.grade([self._item(2)], ["I am not sure"])
        self.assertEqual(result["per_arm"]["served"]["unparsed"], 1)
        self.assertEqual(result["per_arm"]["served"]["correct"], 0)

    def test_chatter_around_a_letter_still_grades(self) -> None:
        result = mr.grade([self._item(0)], ["A)"])
        self.assertEqual(result["per_arm"]["served"]["correct"], 1)


class ThePilotComesBeforeTheFloor(unittest.TestCase):
    """A floor derived from the instrument is frozen only after it repeats."""

    @classmethod
    def setUpClass(cls) -> None:
        if not PILOT_PATH.exists():
            raise unittest.SkipTest("the pilot has not been run")
        cls.pilot = json.loads(PILOT_PATH.read_text(encoding="utf-8"))

    def test_it_says_it_is_a_pilot_and_not_the_arm(self) -> None:
        self.assertIn("PILOT", self.pilot["control"])
        self.assertIn("floor_is_not_frozen_here", self.pilot)

    def test_reproducibility_is_measured_not_assumed(self) -> None:
        repro = self.pilot["reproducibility"]
        self.assertIn("two_passes_byte_identical", repro)
        self.assertIn("never tested", repro["question"])
        self.assertIn("revert", repro["consequence_if_false"])

    def test_it_carries_the_inherited_voiding_sentence(self) -> None:
        self.assertIn("half the served", self.pilot["inherited_voiding_sentence"])

    def test_it_is_labelled_machine_reader_throughout(self) -> None:
        self.assertIn("MACHINE-reader", self.pilot["labelled"])
        self.assertIn("not about", self.pilot["c_v3_human_is_still_absent"])

    def test_the_weights_were_verified_before_any_question(self) -> None:
        self.assertTrue(self.pilot["weights"]["verified"])
        self.assertEqual(self.pilot["weights"]["sha256"],
                         mr.MANIFEST["model"]["weights_blob_sha256"])


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
