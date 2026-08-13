"""Controls for the recorded session (ROADMAP-v0.10 item 5).

The transcript is a committed claim about what ran, so the tests here are
the ones that could catch it being false: that the record still re-verifies
against live artifacts, that the legs say what the design registered they
would say, and — the one that matters most — that the refusal legs really
are refusals rather than steps the driver merely declined to take.

`scripts/trace_to_triples.py` gets its own controls because it is the code
that turns byte offsets into a `verified_by` artifact: an attribution bug
there would mis-assign a proof to a theorem, and every rung above would
inherit the error while still passing its own check.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from trace_to_triples import (  # noqa: E402
    declarations,
    owning_declaration,
    triples,
)

TRANSCRIPT = REPO_ROOT / "experiments" / "harness_session.json"


def transcript() -> dict:
    return json.loads(TRANSCRIPT.read_text(encoding="utf-8"))


def leg(name: str) -> dict:
    return next(entry for entry in transcript()["legs"] if entry["name"] == name)


class RecordedSession(unittest.TestCase):
    def test_the_record_still_verifies(self) -> None:
        """`--check` is the honest remainder of P5: re-verify, not re-run."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "session_run.py"),
             "--check"],
            capture_output=True, text=True, check=False,
            env={"PYTHONIOENCODING": "utf-8", **_min_env()},
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_transcript_carries_no_machine_paths_or_timestamps(self) -> None:
        raw = TRANSCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(str(REPO_ROOT), raw)
        for needle in (":\\\\", ":/Users", "/home/"):
            self.assertNotIn(needle, raw, needle)
        self.assertNotIn("timestamp", raw.lower())

    def test_the_authored_leg_was_applied_by_the_gate(self) -> None:
        write = leg("A")["write"]
        self.assertTrue(write["applied"])
        self.assertEqual(write["decision"], "STAGED_CANDIDATE")
        self.assertEqual(write["rung"], "PROVEN")
        self.assertEqual(
            write["node_id"], "numbertheory.ingested.lean_workbook_22080")
        # The gate's own verifications, not the driver's summary of them.
        self.assertIn("declared_node_present_and_only_it",
                      write["verifications"])
        self.assertIn("matcher_delta_applied", write["verifications"])

    def test_the_need_was_dead_before_the_write_and_met_after(self) -> None:
        """The session's whole shape in two records.

        Before: every registered path abstained. After — in the NEXT session,
        because the running one's store is a boot-time snapshot — the same
        need materializes.
        """
        self.assertEqual(leg("A")["need_before_write"]["stop_reason"],
                         "exhausted")
        after = leg("A'")["need_after_write"]
        self.assertEqual(after["stop_reason"], "solved")
        self.assertTrue(after["materialized"])

    def test_the_refused_leg_was_refused_by_the_gate_not_the_caller(
        self,
    ) -> None:
        """Leg B's point: the verifier failed it AND the gate refused it."""
        record = leg("B")
        self.assertEqual(record["verifier"]["verdict"], "fail")
        self.assertEqual(record["verifier"]["axioms"], ["sorryAx"])
        self.assertEqual(record["write"]["decision"], "REFUSED")
        self.assertFalse(record["write"]["applied"])
        self.assertTrue(record["write"]["tree_byte_identical"])

    def test_the_chicken_abstains_and_mints_nothing(self) -> None:
        record = leg("C")
        self.assertEqual(record["dispatch"]["stop_reason"], "exhausted")
        self.assertFalse(record["dispatch"]["materialized"])
        self.assertEqual(record["minted"], [])
        self.assertIn("did not register", record["dispatch"]["reason"])

    def test_the_matrix_is_recorded_as_liveness_only(self) -> None:
        boot = transcript()["boot"]
        self.assertTrue(boot["matrix"])
        self.assertIn("LIVENESS ONLY", transcript()["honesty_boundary"])


class TraceAttribution(unittest.TestCase):
    """The post-processor that turns byte offsets into a proof artifact."""

    SOURCE = (
        "theorem first : 1 = 1 := by rfl\n"
        "theorem second : 2 = 2 := by rfl\n"
    )

    def test_declarations_are_found_in_byte_order(self) -> None:
        found = declarations(self.SOURCE)
        self.assertEqual([name for _, name in found], ["first", "second"])
        self.assertLess(found[0][0], found[1][0])

    def test_a_tactic_is_attributed_to_the_declaration_above_it(self) -> None:
        decls = declarations(self.SOURCE)
        second_start = self.SOURCE.index("theorem second")
        self.assertEqual(owning_declaration(decls, second_start + 5), "second")
        self.assertEqual(owning_declaration(decls, 5), "first")

    def test_a_tactic_before_every_declaration_is_refused(self) -> None:
        decls = [(10, "later")]
        with self.assertRaises(ValueError):
            owning_declaration(decls, 0)

    def test_the_tactic_text_is_a_byte_slice_not_a_guess(self) -> None:
        """Unicode in the source must not shift the slice."""
        source = "theorem t : True := by trivial\n-- ⊢ ∀ ∃\n"
        raw = source.encode("utf-8")
        start = raw.index(b"trivial")
        ast = {
            "tactics": [
                {
                    "pos": {"byteIdx": start},
                    "endPos": {"byteIdx": start + len(b"trivial")},
                    "stateBefore": "⊢ True",
                    "stateAfter": "no goals",
                }
            ]
        }
        rows = triples(ast, raw, source)
        self.assertEqual(rows, [{
            "theorem": "t",
            "tactic": "trivial",
            "stateBefore": "⊢ True",
            "stateAfter": "no goals",
        }])

    def test_an_oversized_state_is_refused_not_truncated(self) -> None:
        source = "theorem t : True := by trivial\n"
        raw = source.encode("utf-8")
        ast = {
            "tactics": [
                {
                    "pos": {"byteIdx": 23},
                    "endPos": {"byteIdx": 30},
                    "stateBefore": "x" * 5000,
                    "stateAfter": "no goals",
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, "over the 4000 guard"):
            triples(ast, raw, source)

    def test_the_committed_artifact_matches_a_fresh_post_process(self) -> None:
        """The committed rows are what this code produces from the AST.

        Skipped when the tracer's build directory is absent — `.lake` is
        gitignored and does not survive a fresh clone. The artifact's digest
        pin is what protects it in that case; this is the stronger check
        when the inputs are present.
        """
        ast_path = (
            REPO_ROOT / "prover" / "lean" / "session" / ".lake" / "build"
            / "ir" / "Session22080.ast.json"
        )
        if not ast_path.is_file():
            self.skipTest("tracer build directory absent (gitignored)")
        source = REPO_ROOT / "prover" / "lean" / "session" / "Session22080.lean"
        raw = source.read_bytes()
        rows = triples(
            json.loads(ast_path.read_text(encoding="utf-8")), raw,
            raw.decode("utf-8"),
        )
        committed = json.loads(
            (REPO_ROOT / "prover" / "session_triples.json").read_text(
                encoding="utf-8")
        )
        self.assertEqual(rows, committed)


class EmptyExtractionIsRefused(unittest.TestCase):
    def test_no_tactics_writes_no_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ast = root / "empty.ast.json"
            ast.write_text(json.dumps({"tactics": []}), encoding="utf-8")
            source = root / "Empty.lean"
            source.write_text("theorem t : True := trivial\n", encoding="utf-8")
            out = root / "out.json"
            result = subprocess.run(
                [sys.executable,
                 str(REPO_ROOT / "scripts" / "trace_to_triples.py"),
                 "--ast", str(ast), "--source", str(source),
                 "--out", str(out)],
                capture_output=True, text=True, check=False,
                env={"PYTHONIOENCODING": "utf-8", **_min_env()},
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing to write an empty artifact", result.stderr)


def _min_env() -> dict:
    import os

    return {
        name: os.environ[name]
        # USERPROFILE/HOME are part of the minimum here: the verifier
        # resolves the pinned toolchain under the user's ~/.elan, and a
        # `--check` that cannot find it would REFUSE (correctly) and tell us
        # nothing about the record.
        for name in ("SystemRoot", "SYSTEMROOT", "COMSPEC", "PATH", "TEMP",
                     "TMP", "USERPROFILE", "HOME", "HOMEDRIVE", "HOMEPATH")
        if name in os.environ
    }


if __name__ == "__main__":
    unittest.main()
