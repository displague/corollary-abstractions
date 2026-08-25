#!/usr/bin/env python3
"""G3, ENFORCED: re-derive the pinned C-V4 id lists, don't just read them.

Reviewer finding H3.  `data/foreign_voice/cv4_replay_ids.json` is the pin that
replaced the seed — three of C-V4's five pools move with the grammar, so a
seed cannot identify them — and its own header says the derivation is
*"checkable rather than asserted"*.  It was not being checked.
`scripts/cv4_replay.py` refuses on the branch tip (the pre-amendment lexicon
is no longer at `HEAD~1`), and no collected test ever performed the
derivation, so the strongest claim in the file rested on a program nobody ran.

This module performs it, the way the reviewer did:

* the **pre-canonical renderer** is reconstructed from git at `4d09d95` — the
  G-P commit, before `foreign_voice.py` began emitting canonical grouping;
* the **pre-amendment lexicon** is taken as a blob from git and digest-checked
  against the retirement the prereg records;
* `measure_foreign_voice._plan` is re-executed against them, unmodified;
* the five id lists and the five `admitting` counts must match the pin, and
  the counts must match the numbers v0.19's own run artifact recorded.

**It never skips.**  A tree where the derivation cannot run cannot check G3,
and an unrunnable check reported as a pass is precisely what the pin exists to
prevent.  Refusal is red.

The reconstruction is from **blobs**, not from an in-memory revert, for the
reason `transliteration_served_diff.py:357-360` already states: *"An in-memory
revert re-types the old regex, and the digest check would then be checking the
copy against itself. The blob from git IS the pre-amendment file."*
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import foreign_voice_lexicon as fvl  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402

DATA = ROOT / "data" / "foreign_voice"
#: The G-P commit: the parser and rule landed, the renderer had NOT yet been
#: made canonical. That is the renderer v0.19's draw ran under.
PRE_CANONICAL_RENDERER_COMMIT = "4d09d95"
LEXICON = "data/foreign_voice/lexicon.json"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args],
                          capture_output=True)


class G3TheIdPinsAreReDerivable(unittest.TestCase):
    """The derivation the pin's own header promises, actually run."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pin = json.loads((DATA / "cv4_replay_ids.json").read_text(encoding="utf-8"))
        cls.prereg = json.loads(
            (ROOT / "experiments" / "foreign_voice_prereg.json").read_text(
                encoding="utf-8"))
        cls.rate = json.loads(
            (ROOT / "experiments" / "foreign_voice_rate.json").read_text(
                encoding="utf-8"))

    def _retired_lexicon_digest(self) -> str:
        for entry in self.prereg.get("corrections", []):
            for row in entry.get("digests_retired", []):
                if row["path"] == LEXICON:
                    return row["v019_sha256_lf"]
        self.fail("the prereg records no lexicon retirement to replay against")

    def _pre_amendment_lexicon(self):
        expected = self._retired_lexicon_digest()
        found = None
        # Walk the file's history for the blob whose digest IS the retired pin.
        log = _git("log", "--format=%H", "--", LEXICON)
        self.assertEqual(log.returncode, 0, "cannot read the lexicon's history")
        for commit in log.stdout.decode().split():
            blob = _git("show", f"{commit}:{LEXICON}")
            if blob.returncode != 0:
                continue
            raw = blob.stdout.replace(b"\r\n", b"\n")
            if hashlib.sha256(raw).hexdigest() == expected:
                found = raw
                break
        self.assertIsNotNone(
            found,
            f"no commit in this history carries a {LEXICON} blob digesting to "
            f"the retired pin {expected[:16]}…; G3 cannot be checked here and "
            f"that is a FAILURE, not a skip")
        return fvl.build(
            json.loads(found.decode("utf-8"), object_pairs_hook=fvl._load_pairs),
            "<pre-amendment>")

    def _pre_canonical_renderer(self):
        blob = _git("show", f"{PRE_CANONICAL_RENDERER_COMMIT}:scripts/foreign_voice.py")
        self.assertEqual(
            blob.returncode, 0,
            f"cannot read the pre-canonical renderer at "
            f"{PRE_CANONICAL_RENDERER_COMMIT}; G3 cannot be checked here and "
            f"that is a FAILURE, not a skip")
        source = blob.stdout.decode("utf-8")
        self.assertNotIn(
            "grouping_canonical_probe", source,
            "the blob taken as the PRE-canonical renderer already imports the "
            "grouping rule, so it is not the pre-canonical renderer and this "
            "test would be replaying the wrong grammar")
        scratch = tempfile.mkdtemp()
        path = Path(scratch) / "foreign_voice_pre.py"
        path.write_text(source, encoding="utf-8", newline="\n")
        spec = importlib.util.spec_from_file_location("foreign_voice_pre", path)
        module = importlib.util.module_from_spec(spec)
        # Registered BEFORE execution: the module defines frozen dataclasses,
        # and `dataclasses` resolves `cls.__module__` through `sys.modules`
        # while the class body is being processed.
        sys.modules["foreign_voice_pre"] = module
        self.addCleanup(sys.modules.pop, "foreign_voice_pre", None)
        spec.loader.exec_module(module)
        return module

    def test_the_five_id_lists_and_pools_re_derive(self) -> None:
        lexicon = self._pre_amendment_lexicon()
        renderer = self._pre_canonical_renderer()
        seed = self._retired_lexicon_digest()

        preview = json.loads((DATA / "eligibility_preview.json").read_text(encoding="utf-8"))
        register = json.loads((DATA / "register.json").read_text(encoding="utf-8"))
        rows = mfv.covered_rows(preview, register)
        block = json.loads(
            (ROOT / "experiments" / "foreign_voice_prereg.json").read_text(
                encoding="utf-8"))["c_v4"]

        # `_plan` reaches the renderer through the module-global `fv`; swap in
        # the reconstructed one for the duration, then put it back.
        original = mfv.fv
        mfv.fv = renderer
        try:
            plan = mfv._plan(seed, rows, lexicon, block["sample_size"],
                             block["mutations"])
        finally:
            mfv.fv = original

        shipped = self.rate["c_v4"]["per_class"]
        for name, expected in sorted(self.pin["classes"].items()):
            with self.subTest(mutation=name):
                sample = plan[name]
                derived_ids = [row["statement_id"] for row in sample]
                derived_pool = sample[0]["admitting"] if sample else 0
                self.assertEqual(derived_ids, expected["statement_ids"],
                                 f"{name}: the re-derived draw is not the pinned one")
                self.assertEqual(derived_pool, expected["admitting"],
                                 f"{name}: the re-derived pool is not the pinned one")
                self.assertEqual(derived_pool, shipped[name]["admitting"],
                                 f"{name}: the re-derived pool does not match "
                                 f"what v0.19's own run recorded")

    def test_the_pools_are_the_numbers_the_design_names(self) -> None:
        """2,285 / 2,162 / 1,549 / 1,549 / 1,764 — Correction 6's own list."""
        self.assertEqual(
            {name: row["admitting"] for name, row in self.pin["classes"].items()},
            {"drop_ascription": 2285, "drop_binder": 2162, "drop_group": 1549,
             "shift_group": 1549, "swap_binder": 1764})

    def test_the_ten_named_cases_are_drawn_from_the_pinned_fifty(self) -> None:
        """C-G1's named set must be a subset of the set it is named against."""
        drawn = set(self.pin["classes"]["drop_group"]["statement_ids"])
        named = set(self.pin["c_g1"]["the_ten_named_blind_cases"])
        self.assertEqual(len(named), 10)
        self.assertTrue(named <= drawn,
                        "a named blind case that is not in drop_group's drawn "
                        "fifty could never be scored, and C-G1's per-id floor "
                        "would be unfalsifiable for it")


if __name__ == "__main__":  # pragma: no cover - CLI
    unittest.main()
