"""Controls for the external verifier (v0.10 item 2).

Four families, mirroring docs/DESIGN-external-verifier.md Sec. 7:

* verdict-object honesty — a verdict is never a bare boolean, a PASS without
  pinned inputs is refused, and the committed verdicts re-hash green;
* hermetic refusal — a missing toolchain REFUSES (never downloads), an
  escaping path REFUSES, moved bytes refuse a recheck;
* negative controls — a false statement FAILS (P3), a `sorry` proof of a
  true statement FAILS on the axiom audit (P4), a failing/networking/
  out-of-tree-writing python check FAILS with the refusal named (P5);
* the attach rule — a PASS verdict on the WRONG statement must not attach
  (P7), symmetric to test_verified_by's capability-blind control.

The lean-backed tests run the real pinned toolchain and are skipped only
where it is absent; on the development machine they run.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from external_verifier import (  # noqa: E402
    FAIL,
    PASS,
    REFUSED,
    Verdict,
    check_lean4,
    check_python_tests,
    load_verdict,
    recheck,
    toolchain_binary,
    verdict_ledger_errors,
)

PINNED_TOOLCHAIN = "leanprover/lean4:v4.32.2"
HAVE_LEAN = toolchain_binary(PINNED_TOOLCHAIN) is not None

LEAN_VERDICT = "prover/verifier-verdicts/lean_workbook_1041.lean4.json"
PY_VERDICT = "prover/verifier-verdicts/lean_workbook_1041.python-tests.json"
FAIL_VERDICT = "prover/verifier-verdicts/lean_workbook_10411.lean4.json"


def lean_repo(root: Path, theorem: str) -> None:
    """A minimal fake repo whose lean project pins the REAL toolchain."""
    project = root / "prover" / "lean" / "t"
    project.mkdir(parents=True)
    (project / "lean-toolchain").write_bytes(
        (PINNED_TOOLCHAIN + "\n").encode()
    )
    (project / "T.lean").write_bytes(theorem.encode("utf-8"))


class VerdictObjectHonesty(unittest.TestCase):
    def test_verdict_is_a_record_not_a_boolean(self) -> None:
        verdict = Verdict(
            backend="lean4", claim={"statement_id": "x"}, checks=["c"],
            inputs={"a": "0" * 64}, environment={"platform": "test"},
            verdict=PASS,
        )
        payload = json.loads(verdict.to_bytes().decode("utf-8"))
        for fields in ("backend", "claim", "checks", "inputs",
                       "environment", "verdict", "evidence"):
            self.assertIn(fields, payload)

    def test_verdict_bytes_are_deterministic(self) -> None:
        verdict = Verdict(
            backend="lean4", claim={"statement_id": "x"}, checks=[],
            inputs={"a": "0" * 64}, environment={}, verdict=FAIL,
        )
        self.assertEqual(verdict.to_bytes(), verdict.to_bytes())
        self.assertNotIn(b"\r\n", verdict.to_bytes())

    def test_pass_without_pinned_inputs_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "prover" / "verifier-verdicts"
            target.mkdir(parents=True)
            (target / "empty.json").write_bytes(
                Verdict(
                    backend="lean4", claim={"statement_id": "x"},
                    checks=[], inputs={}, environment={}, verdict=PASS,
                ).to_bytes()
            )
            with self.assertRaisesRegex(ValueError, "certifies nothing"):
                load_verdict(root, "prover/verifier-verdicts/empty.json")

    def test_committed_verdicts_and_ledger_are_green(self) -> None:
        self.assertEqual(verdict_ledger_errors(REPO_ROOT), [])
        for name in (LEAN_VERDICT, PY_VERDICT):
            verdict = load_verdict(REPO_ROOT, name)
            self.assertEqual(verdict["verdict"], PASS)
            self.assertEqual(
                verdict["claim"]["statement_id"],
                "numbertheory.ingested.lean_workbook_1041",
            )


class CommittedNegativeRecord(unittest.TestCase):
    """P8(a): the check the verifier does NOT pass, committed as a FAIL.

    `lean_workbook_10411` is TRUE and ground, and the shipped toolchain
    still cannot prove it: `decide` on `2014^2015` exceeds the default
    `exponentiation.threshold`, so the declaration closes with `sorryAx`.
    The design promised this would be recorded as a FAIL rather than
    silently dropped or rescued by raising the option inside the verifier.
    A ledger that only ever contains passes is not a ledger.
    """

    def test_the_negative_is_committed_and_names_its_axiom(self) -> None:
        verdict = load_verdict(REPO_ROOT, FAIL_VERDICT)
        self.assertEqual(verdict["verdict"], FAIL)
        self.assertEqual(verdict["evidence"]["axioms"], ["sorryAx"])
        self.assertIn("axiom audit failed", verdict["evidence"]["reason"])

    def test_the_verifier_never_raised_the_option_to_pass_it(self) -> None:
        """The probe source carries no `set_option` escape hatch."""
        source = (
            REPO_ROOT / "prover" / "lean" / "ingested" / "Lw10411Probe.lean"
        ).read_text(encoding="utf-8")
        self.assertNotIn("set_option", source.split("-/", 1)[1])

    def test_the_mathlib_node_stays_unbridged_and_says_why(self) -> None:
        """P2: decision (b) at node level, and nothing upgrades it.

        `lean_workbook_10202` (`2^21 ≡ 1 [ZMOD 7]`) is Mathlib notation core
        Lean cannot parse. It is in the corpus as `formal` PROVENANCE with no
        bridge, and the reason is written into the node itself rather than
        left to this design note — every future unbridged ingest owes the
        same record.
        """
        corpus = json.loads(
            (REPO_ROOT / "data" / "number_theory" / "nodes.json").read_text(
                encoding="utf-8"
            )
        )
        node = next(
            n
            for n in corpus["statement_nodes"]
            if n["statement_id"].endswith("lean_workbook_10202")
        )
        self.assertEqual(node.get("verified_by", []), [])
        self.assertEqual(node["epistemic_status"], "formal")
        written = json.dumps(node["semantic_interpretation"])
        self.assertIn("Mathlib", written)

    def test_a_non_pass_verdict_is_referenced_by_no_artifact(self) -> None:
        """It sits in the ledger and backs nothing — the vocabulary working."""
        manifest = json.loads(
            (REPO_ROOT / "prover" / "proof-artifact-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        referenced = {
            name
            for entry in manifest["artifacts"].values()
            for name in entry.get("verdicts", [])
        }
        self.assertNotIn(FAIL_VERDICT, referenced)
        self.assertEqual(verdict_ledger_errors(REPO_ROOT), [])


class LedgerBytesArePortable(unittest.TestCase):
    """A committed ledger may not carry one machine's checkout paths.

    Lean prints the absolute source path in every diagnostic, so the first
    FAIL verdict written here embedded this developer's home directory —
    unreproducible on any other checkout, and its `output_sha256` would have
    differed per clone even when the outcome was identical. The verifier now
    folds pinned inputs' own paths back to their repository-relative names
    (and the python sandbox's scratch directory to a fixed token); these are
    the regressions.
    """

    def test_no_committed_verdict_contains_an_absolute_path(self) -> None:
        directory = REPO_ROOT / "prover" / "verifier-verdicts"
        for path in sorted(directory.glob("*.json")):
            text = path.read_text(encoding="utf-8")
            for needle in (":\\\\", ":/Users", "/home/", "\\\\Users\\\\"):
                self.assertNotIn(needle, text, f"{path.name}: {needle}")
            self.assertNotIn(str(REPO_ROOT), text, path.name)

    def test_the_diagnostic_still_names_the_file_relatively(self) -> None:
        """Folding paths must not cost the reader the location."""
        verdict = load_verdict(REPO_ROOT, FAIL_VERDICT)
        self.assertTrue(
            any(
                line.startswith("prover/lean/ingested/Lw10411Probe.lean:")
                for line in verdict["evidence"]["output_tail"]
            ),
            verdict["evidence"]["output_tail"],
        )

    @unittest.skipUnless(HAVE_LEAN, "pinned Lean toolchain not installed")
    def test_a_fresh_failing_run_is_path_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lean_repo(root, "theorem t : 1 = 2 := by decide\n")
            verdict = check_lean4(
                root, "prover/lean/t/T.lean", "s", "1 = 2", "t"
            )
        self.assertEqual(verdict.verdict, FAIL)
        self.assertNotIn(str(root), json.dumps(verdict.evidence))


class HermeticRefusal(unittest.TestCase):
    def test_missing_toolchain_refuses_and_never_downloads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "prover" / "lean" / "t"
            project.mkdir(parents=True)
            (project / "lean-toolchain").write_bytes(
                b"leanprover/lean4:v0.0.0-nonexistent\n"
            )
            (project / "T.lean").write_bytes(b"theorem t : True := trivial\n")
            verdict = check_lean4(
                root, "prover/lean/t/T.lean", "s", "True", "t"
            )
        self.assertEqual(verdict.verdict, REFUSED)
        self.assertIn("refusing to download", verdict.evidence["reason"])

    def test_escaping_source_path_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            verdict = check_lean4(
                Path(temporary), "../outside.lean", "s", "True", "t"
            )
        self.assertEqual(verdict.verdict, REFUSED)

    def test_recheck_refuses_moved_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "cand.py"
            tests = root / "test_cand.py"
            candidate.write_bytes(b"X: int = 1\n")
            tests.write_bytes(
                b"import unittest\nfrom cand import X\n\n\n"
                b"class T(unittest.TestCase):\n"
                b"    def test_x(self) -> None:\n"
                b"        self.assertEqual(X, 1)\n"
            )
            verdict = check_python_tests(
                root, "cand.py", "test_cand.py", "s", "X == 1"
            )
            target = root / "prover" / "verifier-verdicts"
            target.mkdir(parents=True)
            (target / "v.json").write_bytes(verdict.to_bytes())
            candidate.write_bytes(b"X: int = 2\n")  # move the pinned bytes
            ok, detail = recheck(root, "prover/verifier-verdicts/v.json")
        self.assertFalse(ok)
        self.assertIn("refusing to re-adjudicate moved bytes", detail)


@unittest.skipUnless(HAVE_LEAN, "pinned Lean toolchain not installed")
class LeanNegativeControls(unittest.TestCase):
    def test_false_statement_fails(self) -> None:
        """P3: `decide` on 14 | 2^30 + 3^60 (false) is FAIL, never PASS."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lean_repo(
                root,
                "theorem t : 14 ∣ 2^30 + 3^60 := by decide\n"
                "#print axioms t\n",
            )
            verdict = check_lean4(
                root, "prover/lean/t/T.lean", "s", "14 ∣ 2^30 + 3^60", "t"
            )
        self.assertEqual(verdict.verdict, FAIL)
        self.assertNotEqual(verdict.evidence["exit_code"], 0)

    def test_sorry_fails_on_the_axiom_audit(self) -> None:
        """P4: exit code 0 + sorry must fail — the axiom audit catches it."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lean_repo(
                root,
                "theorem t : 13 ∣ 2^30 + 3^60 := by sorry\n"
                "#print axioms t\n",
            )
            verdict = check_lean4(
                root, "prover/lean/t/T.lean", "s", "13 ∣ 2^30 + 3^60", "t"
            )
        self.assertEqual(verdict.verdict, FAIL)
        self.assertIn("sorryAx", json.dumps(verdict.evidence))

    def test_wrong_surface_fails_containment(self) -> None:
        """A verdict cannot claim a statement the source does not declare."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lean_repo(
                root,
                "theorem t : 13 ∣ 2^30 + 3^60 := by decide\n"
                "#print axioms t\n",
            )
            verdict = check_lean4(
                root, "prover/lean/t/T.lean", "s", "7 ∣ 2^30 + 3^60", "t"
            )
        self.assertEqual(verdict.verdict, FAIL)
        self.assertIn("surface containment", verdict.evidence["reason"])

    def test_committed_lean_verdict_rechecks(self) -> None:
        ok, detail = recheck(REPO_ROOT, LEAN_VERDICT)
        self.assertTrue(ok, detail)


class PythonNegativeControls(unittest.TestCase):
    def write_pair(self, root: Path, candidate: bytes, tests: bytes) -> None:
        (root / "cand.py").write_bytes(candidate)
        (root / "test_cand.py").write_bytes(tests)

    def test_failing_test_fails(self) -> None:
        """P5: the mutated claim (14 | ...) FAILS; no silent pass."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_pair(
                root,
                b"def residue() -> int:\n"
                b"    return (2**30 + 3**60) % 14\n",
                b"import unittest\nfrom cand import residue\n\n\n"
                b"class T(unittest.TestCase):\n"
                b"    def test_zero(self) -> None:\n"
                b"        self.assertEqual(residue(), 0)\n",
            )
            verdict = check_python_tests(
                root, "cand.py", "test_cand.py", "s", "14 | 2^30 + 3^60"
            )
        self.assertEqual(verdict.verdict, FAIL)
        self.assertIn("sandboxed tests failed", verdict.evidence["reason"])

    def test_network_attempt_is_refused_by_the_sandbox(self) -> None:
        """P5: socket.getaddrinfo trips the audit hook, named in evidence."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_pair(
                root,
                b"import socket\n\n\n"
                b"def resolve() -> int:\n"
                b"    socket.getaddrinfo('example.com', 80)\n"
                b"    return 0\n",
                b"import unittest\nfrom cand import resolve\n\n\n"
                b"class T(unittest.TestCase):\n"
                b"    def test_resolve(self) -> None:\n"
                b"        self.assertEqual(resolve(), 0)\n",
            )
            verdict = check_python_tests(
                root, "cand.py", "test_cand.py", "s", "network control"
            )
        self.assertEqual(verdict.verdict, FAIL)
        self.assertIn("sandbox refused audit event", json.dumps(verdict.evidence))

    def test_out_of_sandbox_write_is_refused(self) -> None:
        """P5: writing outside the sandbox directory trips the hook."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            escape = (root / "escape.txt").as_posix()
            self.write_pair(
                root,
                (
                    "def touch() -> int:\n"
                    f"    open({escape!r}, 'w').close()\n"
                    "    return 0\n"
                ).encode(),
                b"import unittest\nfrom cand import touch\n\n\n"
                b"class T(unittest.TestCase):\n"
                b"    def test_touch(self) -> None:\n"
                b"        self.assertEqual(touch(), 0)\n",
            )
            verdict = check_python_tests(
                root, "cand.py", "test_cand.py", "s", "write control"
            )
        self.assertEqual(verdict.verdict, FAIL)
        self.assertIn(
            "sandbox refused write outside sandbox",
            json.dumps(verdict.evidence),
        )

    def test_a_low_level_write_outside_the_sandbox_is_refused(self) -> None:
        """The hole the review found: `os.open` carries mode None.

        The hook originally read only the `open` event's MODE, which every
        low-level open leaves as None — so `os.open`, `_io.FileIO`, and
        CPython's own bytecode-cache writer all sailed past a rule whose
        verdict text claimed to refuse writes outside the sandbox. It was
        not hypothetical: a check run with a cold cache wrote `__pycache__`
        into the repository while reporting PASS. The flags are read now,
        and the runner is invoked with -B so nothing legitimate needs that
        write.
        """
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            escape = (root / "escape-low-level.txt").as_posix()
            self.write_pair(
                root,
                (
                    "import os\n\n\n"
                    "def touch() -> int:\n"
                    f"    fd = os.open({escape!r}, os.O_WRONLY | os.O_CREAT)\n"
                    "    os.close(fd)\n"
                    "    return 0\n"
                ).encode(),
                b"import unittest\nfrom cand import touch\n\n\n"
                b"class T(unittest.TestCase):\n"
                b"    def test_touch(self) -> None:\n"
                b"        self.assertEqual(touch(), 0)\n",
            )
            verdict = check_python_tests(
                root, "cand.py", "test_cand.py", "s", "low-level write control"
            )
            self.assertFalse((root / "escape-low-level.txt").exists())
        self.assertEqual(verdict.verdict, FAIL)
        self.assertIn(
            "sandbox refused write outside sandbox",
            json.dumps(verdict.evidence),
        )

    def test_a_check_writes_no_bytecode_into_the_repository(self) -> None:
        """The cold-cache run must be the same run as the warm one."""
        cache = REPO_ROOT / "prover" / "pychecks" / "__pycache__"
        if cache.exists():
            shutil.rmtree(cache)
        verdict = check_python_tests(
            REPO_ROOT,
            "prover/pychecks/lean_workbook_1041_check.py",
            "prover/pychecks/test_lean_workbook_1041.py",
            "numbertheory.ingested.lean_workbook_1041",
            "13 | 2^30 + 3^60",
        )
        self.assertEqual(verdict.verdict, PASS, verdict.evidence)
        self.assertFalse(cache.exists())

    def test_committed_python_verdict_rechecks(self) -> None:
        ok, detail = recheck(REPO_ROOT, PY_VERDICT)
        self.assertTrue(ok, detail)


class AttachRule(unittest.TestCase):
    """P7: the ledger rung fails closed; wrong statements cannot attach."""

    def build_repo(
        self,
        root: Path,
        verdict_statement: str = "node.a",
        verdict_outcome: str = PASS,
        tamper: bool = False,
        drop_verdict: bool = False,
    ) -> list[dict]:
        artifact = root / "prover" / "triples.json"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"[]\n")
        source = root / "prover" / "src.txt"
        source.write_bytes(b"pinned input\n")
        import hashlib

        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        verdict = Verdict(
            backend="lean4",
            claim={"statement_id": verdict_statement, "surface": "s",
                   "reference": "t"},
            checks=["c"],
            inputs={"prover/src.txt": digest},
            environment={"platform": "test"},
            verdict=verdict_outcome,
        )
        verdict_dir = root / "prover" / "verifier-verdicts"
        verdict_dir.mkdir()
        if not drop_verdict:
            (verdict_dir / "v.json").write_bytes(verdict.to_bytes())
        manifest = {
            "schema_version": 1,
            "artifacts": {
                "prover/triples.json": {
                    "sha256": hashlib.sha256(b"[]\n").hexdigest(),
                    "verdicts": ["prover/verifier-verdicts/v.json"],
                }
            },
        }
        (root / "prover" / "proof-artifact-manifest.json").write_bytes(
            json.dumps(manifest).encode()
        )
        if tamper:
            source.write_bytes(b"moved bytes\n")
        return [
            {
                "statement_id": "node.a",
                "verified_by": [
                    {
                        "system": "lean4",
                        "artifact": "prover/triples.json",
                        "reference": "t",
                    }
                ],
            }
        ]

    def test_matching_chain_is_green(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nodes = self.build_repo(root)
            self.assertEqual(verdict_ledger_errors(root, nodes), [])

    def test_pass_on_the_wrong_statement_does_not_attach(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nodes = self.build_repo(root, verdict_statement="node.OTHER")
            errors = verdict_ledger_errors(root, nodes)
        self.assertTrue(
            any("must not attach" in error for error in errors), errors
        )

    def test_non_pass_verdict_cannot_back_an_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nodes = self.build_repo(root, verdict_outcome=FAIL)
            errors = verdict_ledger_errors(root, nodes)
        self.assertTrue(
            any("only a PASS may back" in error for error in errors), errors
        )

    def test_tampered_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nodes = self.build_repo(root, tamper=True)
            errors = verdict_ledger_errors(root, nodes)
        self.assertTrue(
            any("the pinned bytes moved" in error for error in errors), errors
        )

    def test_missing_verdict_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            nodes = self.build_repo(root, drop_verdict=True)
            errors = verdict_ledger_errors(root, nodes)
        self.assertTrue(
            any("absent or already invalid" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
