#!/usr/bin/env python3
"""The runner's parts, exercised before the one run they get.

The registered run happens once.  Every piece of it that can be checked
without spending that run is checked here: the B7 revalidation gate, the C-V1
scramble, the five C-V4 mutations, the sample rule, and the fact that the
runner will not execute by accident.

The mutations get the most attention, because the first version of the aiming
test in `tests/test_foreign_voice.py` picked a statement with no parentheses
in it and its "mutation" was a **no-op** — the mutant and the original were
the same sentence, and the gate agreed they were the same term.  That is
exactly how a mutation control talks itself into a good number, and it is why
`mutate` is asserted here to CHANGE the surface, and why the runner counts
no-ops and drops them from the denominator instead of scoring them as
"not detected".
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
import foreign_voice_rule_r as fvr  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402
from git_ordering import assert_absent_or_added_after  # noqa: E402

LEX = fvl.load()
RULE = fvr.load()
LEXICON_PATH = ROOT / "data" / "foreign_voice" / "lexicon.json"
PREREG_PATH = ROOT / "experiments" / "foreign_voice_prereg.json"

#: A statement carrying every construct the five mutations need: a two-binder
#: preamble with an ascription, and grouping words.
SPECIMEN = "∀ a b : Rat, (a + b) * (a - b) = a^2 - b^2"


class RevalidationGate(unittest.TestCase):
    """B7 with teeth: no rate is published if a frozen artifact moved."""

    def test_the_run_is_closed_now_that_its_parser_pin_was_retired(self) -> None:
        """B7 refuses, and refusing is the CORRECT outcome. Renamed 2026-08-24.

        This test used to assert that the committed tree revalidates. It cannot
        any more, and the reason is not a regression: `foreign_voice.prereg.v1.
        amendment.transliteration-2026-08-24` (ROADMAP-v0.19 item 3a) retired
        the `parser` row, and `scripts/measure_foreign_voice.py` is byte-frozen
        by its own `registered_run` pin — so the writer cannot be taught to
        follow the retirement without retiring a second pin to do it.

        Leaving it refusing is the better outcome, not the cheaper one. The
        v0.19 registered run HAPPENED, under 65fead2f…, and its artifact
        `experiments/foreign_voice_rate.json` is the record. Re-executing it
        under a different parser would silently rewrite that artifact with
        B0a/C-V2 numbers computed on a moved denominator — which is exactly
        what B7 exists to prevent and exactly what the amendment declared it
        would not do. The run is CLOSED, and this assertion is what closes it.

        Note the deliberate difference from `test_foreign_voice_lexicon`'s
        digest sweep, which DOES follow the retirement and stays green. The two
        ask different questions: the sweep asks "does the tree still match a pin
        recorded somewhere" — bookkeeping, and it must keep working. This asks
        "may this run be executed and its artifact rewritten" — authority, and
        the answer is no.
        """
        with self.assertRaises(mfv.RunRefusal) as caught:
            mfv.revalidate()
        message = str(caught.exception)
        self.assertIn("B7 VOID", message)
        self.assertIn("match_signatures.py", message)
        self.assertIn("No rate is published", message)

    def test_the_retirement_that_closed_it_is_recorded_in_the_prereg(self) -> None:
        """A run closed by a refusal must be closed by a written reason.

        Without this, the refusal above is indistinguishable from someone
        having edited the parser without telling anyone — which is the failure
        B7 was built for. The amendment is what makes it the other thing.
        """
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        parser = {row["role"]: row for row in prereg["frozen"]}["parser"]
        marker = parser["retired_for_future_comparisons"]
        self.assertEqual(marker["amendment"], "transliteration-2026-08-24")
        amendment = [entry for entry in prereg["amendments"]
                     if entry["amendment_id"].endswith(marker["amendment"])]
        self.assertEqual(len(amendment), 1)
        self.assertEqual(amendment[0]["successor_prereg"]["path"],
                         "experiments/transliteration_prereg.json")
        historical = [row["path"] for row
                      in amendment[0]["declared_historical_artifacts"]]
        self.assertIn("experiments/foreign_voice_rate.json", historical)

    def test_a_moved_digest_refuses_and_names_the_file(self) -> None:
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        prereg["frozen"][0]["sha256_lf"] = "0" * 64
        with self.assertRaises(mfv.RunRefusal) as caught:
            self._revalidate_from(prereg)
        self.assertIn("B7 VOID", str(caught.exception))
        self.assertIn(prereg["frozen"][0]["path"], str(caught.exception))

    def test_an_absent_frozen_file_refuses(self) -> None:
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        prereg["frozen"][0]["path"] = "data/foreign_voice/not_a_file.json"
        with self.assertRaises(mfv.RunRefusal):
            self._revalidate_from(prereg)

    def test_a_pending_row_refuses(self) -> None:
        """The run may not precede the things it is gated on."""
        prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
        prereg["pending"] = [{"path": "x", "role": "y", "sha256_lf": "pending"}]
        with self.assertRaises(mfv.RunRefusal):
            self._revalidate_from(prereg)

    def _revalidate_from(self, prereg: dict) -> dict:
        import tempfile
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "prereg.json"
            path.write_text(json.dumps(prereg, ensure_ascii=False),
                            encoding="utf-8", newline="\n")
            return mfv.revalidate(path)


class ScrambleIsWrongNotBroken(unittest.TestCase):
    """C-V1's table must load through the same F1–F8 gate the real one does."""

    @classmethod
    def setUpClass(cls) -> None:
        raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        seed = mfv._sha256_lf(LEXICON_PATH)
        cls.scrambled, cls.moved = mfv.scrambled_lexicon(raw, seed)

    def test_it_loads_through_the_real_gate(self) -> None:
        self.assertTrue(self.scrambled.key_to_phrase)
        self.assertEqual(set(self.scrambled.key_to_phrase),
                         set(LEX.key_to_phrase))

    def test_every_scrambled_section_actually_moved(self) -> None:
        for section, moved in self.moved.items():
            with self.subTest(section=section):
                self.assertGreater(moved, 0)

    def test_the_derangement_has_no_fixed_point(self) -> None:
        for section in ("binders", "connectives", "relations", "operators",
                        "types"):
            for key in getattr(LEX, section):
                with self.subTest(key=key):
                    self.assertNotEqual(self.scrambled.key_to_phrase[key],
                                        LEX.key_to_phrase[key])

    def test_grouping_words_are_deliberately_untouched(self) -> None:
        """A scramble that broke bracketing would fail in the PARSER.

        It would prove nothing about whether the gate reads the words, which is
        the only thing C-V1 is for.
        """
        for key in LEX.structural:
            with self.subTest(key=key):
                self.assertEqual(self.scrambled.key_to_phrase[key],
                                 LEX.key_to_phrase[key])

    def test_a_scrambled_rendering_differs_from_the_committed_one(self) -> None:
        real = fv.render_interpreted(SPECIMEN, LEX)
        wrong = fv.render_interpreted(SPECIMEN, self.scrambled)
        self.assertNotEqual(real.surface, wrong.surface)

    def test_the_seed_is_the_lexicons_own_digest(self) -> None:
        """Same idiom as B0d's draw: the table under test is not a knob."""
        raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        again, _ = mfv.scrambled_lexicon(raw, mfv._sha256_lf(LEXICON_PATH))
        self.assertEqual(again.key_to_phrase, self.scrambled.key_to_phrase)


class Mutations(unittest.TestCase):
    """Five mechanical mutations, each asserted to actually mutate."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base = fv.render_interpreted(SPECIMEN, LEX).surface

    def test_the_specimen_admits_every_mutation(self) -> None:
        for name in ("drop_binder", "swap_binder", "drop_ascription",
                     "drop_group", "shift_group"):
            with self.subTest(mutation=name):
                self.assertTrue(mfv._admits(self.base, name, LEX))

    def test_every_mutation_changes_the_surface(self) -> None:
        """A no-op mutation scores as 'not detected' and flatters the control."""
        for name in ("drop_binder", "swap_binder", "drop_ascription",
                     "drop_group", "shift_group"):
            with self.subTest(mutation=name):
                mutated = mfv.mutate(self.base, name, LEX)
                self.assertNotEqual(mutated, self.base)

    def test_exactly_one_thing_changes(self) -> None:
        """C-V4 applies ONE mutation; two would measure their conjunction."""
        # `variable <n>` is two words; `of type <T>` is three; a grouping
        # pair is `the quantity` plus `end quantity`, so four.
        for name, delta in (("drop_binder", -2), ("swap_binder", 0),
                            ("drop_ascription", -3), ("drop_group", -4),
                            ("shift_group", 0)):
            with self.subTest(mutation=name):
                mutated = mfv.mutate(self.base, name, LEX)
                self.assertEqual(len(mutated.split()) - len(self.base.split()),
                                 delta)

    def test_swap_binder_touches_the_preamble_only(self) -> None:
        """§7's mutation is explicit: 'leaving the occurrences alone'."""
        mutated = mfv.mutate(self.base, "swap_binder", LEX)
        ascription = LEX.words_for(":").split()
        words = mutated.split()
        stop = next(i for i in range(len(words) - len(ascription) + 1)
                    if words[i:i + len(ascription)] == ascription)
        self.assertEqual(words[stop:], self.base.split()[stop:])
        self.assertNotEqual(words[:stop], self.base.split()[:stop])

    def test_every_mutant_still_inverts_or_refuses_loudly(self) -> None:
        """Either the inverse reads it, or it raises. Never silent nonsense."""
        for name in ("drop_binder", "swap_binder", "drop_ascription",
                     "drop_group", "shift_group"):
            with self.subTest(mutation=name):
                mutated = mfv.mutate(self.base, name, LEX)
                try:
                    text = fv.delexicalize(mutated, LEX)
                except fv.ForeignVoiceError:
                    continue
                self.assertIsInstance(text, str)

    def test_drop_binder_is_the_one_the_preamble_regenerates(self) -> None:
        """The blind-by-construction claim, at the text level.

        Dropping a binder from the preamble phrase leaves a term whose free
        identifier rule R binds straight back — so `R(inverse(mutant))` and
        `R(s)` differ only in binder ORDER or not at all. This is why it is
        excluded from the voiding pool.
        """
        mutated = mfv.mutate(self.base, "drop_binder", LEX)
        rebuilt = RULE.apply(fv.delexicalize(mutated, LEX)).text
        original = RULE.apply(fv.delexicalize(self.base, LEX)).text
        # The dropped binder comes straight back. The preambles are not
        # textually equal — the regenerated one is a SECOND binder group in
        # front, `∀ v0 : Rat, ∀ v1 : Rat, …` against `∀ v0 v1 : Rat, …` — but
        # the same names end up bound at the same type, which is why the
        # elaborated terms can agree and why B1 cannot see the deletion.
        self.assertEqual(RULE.bound_names(rebuilt), RULE.bound_names(original))
        self.assertEqual(rebuilt.count("Rat"), original.count("Rat") + 1)


class SamplePlan(unittest.TestCase):
    """C-V4's draw follows the preregistered rule, seeded from the table."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.block = json.loads(PREREG_PATH.read_text(encoding="utf-8"))["c_v4"]
        preview = json.loads(
            (ROOT / "data" / "foreign_voice" / "eligibility_preview.json")
            .read_text(encoding="utf-8"))
        register = json.loads(
            (ROOT / "data" / "foreign_voice" / "register.json")
            .read_text(encoding="utf-8"))
        cls.rows = mfv.covered_rows(preview, register)
        cls.plan = mfv._plan(mfv._sha256_lf(LEXICON_PATH), cls.rows, LEX,
                             cls.block["sample_size"], cls.block["mutations"])

    def test_every_mutation_class_drew_its_sample(self) -> None:
        for mutation in self.block["mutations"]:
            with self.subTest(mutation=mutation["name"]):
                sample = self.plan[mutation["name"]]
                self.assertEqual(len(sample), self.block["sample_size"])

    def test_the_draw_is_deterministic(self) -> None:
        again = mfv._plan(mfv._sha256_lf(LEXICON_PATH), self.rows, LEX,
                          self.block["sample_size"], self.block["mutations"])
        self.assertEqual(again, self.plan)

    def test_only_admitting_statements_are_drawn(self) -> None:
        by_id = {row["statement_id"]: row for row in self.rows}
        for mutation in self.block["mutations"]:
            name = mutation["name"]
            for entry in self.plan[name][:10]:
                with self.subTest(mutation=name, statement_id=entry["statement_id"]):
                    surface = fv.render_interpreted(
                        by_id[entry["statement_id"]]["interpreted"], LEX).surface
                    self.assertTrue(mfv._admits(surface, name, LEX))

    def test_four_classes_are_in_the_voiding_pool_and_one_is_not(self) -> None:
        pool = [m["name"] for m in self.block["mutations"] if m["in_voiding_pool"]]
        blind = [m["name"] for m in self.block["mutations"]
                 if not m["in_voiding_pool"]]
        self.assertEqual(len(pool), 4)
        self.assertEqual(blind, ["drop_binder"])
        for mutation in self.block["mutations"]:
            if mutation["in_voiding_pool"]:
                self.assertEqual(mutation["threshold"], 0.90)

    def test_the_pooled_95_floor_was_replaced_before_this_module_existed(
            self) -> None:
        from git_ordering import assert_added_before
        self.assertIn("per_class_thresholds_replace_the_pooled_95", self.block)
        assert_added_before(
            self, "experiments/foreign_voice_prereg.json",
            "scripts/measure_foreign_voice.py",
            "replacing a floor is a preregistration act and must predate the "
            "instrument that reads it")


class TheRunDoesNotHappenByAccident(unittest.TestCase):
    """A once-only act should not be reachable by typing a module name."""

    def test_the_bare_cli_refuses_and_writes_nothing(self) -> None:
        """Was "reports readiness"; the run is closed, so it reports refusal.

        Amended 2026-08-24 alongside `RevalidationGate` above: the parser pin
        was retired by `foreign_voice.prereg.v1.amendment.transliteration-
        2026-08-24`, B7 refuses, and `main` maps a RunRefusal to exit 2. The
        half of this test that mattered most is unchanged and still asserted:
        WRITES NOTHING. A closed run must not touch the artifact that records
        what it measured.
        """
        out = ROOT / "experiments" / "foreign_voice_rate.json"
        existed = out.exists()
        before = out.read_bytes() if existed else None
        code = mfv.main([])
        self.assertEqual(code, 2)
        self.assertEqual(out.exists(), existed)
        if existed:
            self.assertEqual(out.read_bytes(), before)

    def test_the_registered_run_needs_an_explicit_flag(self) -> None:
        self.assertIn("--perform-the-registered-run", _cli_help())

    def test_the_run_came_last_in_the_history(self) -> None:
        """§10 puts the run at the end, after everything that gates it.

        Written while the run had not happened, as "the artifact does not
        exist"; restated once it did, so the ordering stays checkable instead
        of expiring the moment it starts to matter.
        """
        for gate in ("experiments/foreign_voice_prereg.json",
                     "data/foreign_voice/lexicon.json",
                     "data/foreign_voice/rule_r.json",
                     "data/foreign_voice/b0d_sealed_renderings.json",
                     "prover/lean/normalizer/Serialize.lean",
                     "data/foreign_voice/register.json",
                     "scripts/foreign_voice.py",
                     "scripts/measure_foreign_voice.py"):
            with self.subTest(gate=gate):
                assert_absent_or_added_after(
                    self, gate, "experiments/foreign_voice_rate.json",
                    "the registered run is last in §10's order; a rate that "
                    "predated a thing it quotes would be quoting a file that "
                    "did not exist when it was measured")

    def test_c_v3_is_recorded_absent_with_the_claim_it_gates(self) -> None:
        block = mfv.c_v3_absent()
        self.assertEqual(block["status"], "absent")
        self.assertIn("NOT MADE", block["consequence"])
        self.assertIn("NON-MAINTAINER", block["reason"])
        self.assertIn("determinately", block["consequence"].lower())


def _cli_help() -> str:
    import contextlib
    import io
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.suppress(SystemExit):
        mfv.main(["--help"])
    return buffer.getvalue()


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
