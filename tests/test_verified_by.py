"""Regression controls for merged-graph ``verified_by`` integrity."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_nodes import verified_by_errors  # noqa: E402


def node(statement_id: str, artifact: str, reference: str | None) -> dict:
    link = {"system": "lean4", "artifact": artifact}
    if reference is not None:
        link["reference"] = reference
    return {"statement_id": statement_id, "verified_by": [link]}


class VerifiedByIntegrityTests(unittest.TestCase):
    def write_artifact(self, root: Path, theorems: list[str]) -> str:
        path = root / "proof.json"
        path.write_text(
            json.dumps(
                [
                    {
                        "theorem": theorem,
                        "tactic": "exact proof",
                        "stateBefore": "goal",
                        "stateAfter": "no goals",
                    }
                    for theorem in theorems
                ]
            ),
            encoding="utf-8",
        )
        return path.name

    def test_live_merged_corpus_has_exclusive_resolving_links(self) -> None:
        nodes = []
        for path in sorted((REPO_ROOT / "data").glob("*/nodes.json")):
            nodes.extend(
                json.loads(path.read_text(encoding="utf-8"))["statement_nodes"]
            )
        self.assertEqual(verified_by_errors(nodes, REPO_ROOT), [])
        links = [link for n in nodes for link in n.get("verified_by", [])]
        self.assertEqual(len(links), 16)
        self.assertEqual(len({link["reference"] for link in links}), 16)

    def test_missing_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            errors = verified_by_errors(
                [node("logic.example.missing", "absent.json", "T")],
                Path(temporary),
            )
        self.assertTrue(any("does not exist" in error for error in errors))

    def test_malformed_artifact_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "proof.json").write_text("{}", encoding="utf-8")
            errors = verified_by_errors(
                [node("logic.example.malformed", "proof.json", "T")], root
            )
        self.assertTrue(any("no complete theorem" in error for error in errors))

    def test_artifact_row_without_theorem_identity_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "proof.json").write_text(
                json.dumps([{"theorem": ""}]), encoding="utf-8"
            )
            errors = verified_by_errors(
                [node("logic.example.malformed_row", "proof.json", "T")], root
            )
        self.assertTrue(any("no complete theorem" in e for e in errors))

    def test_label_only_row_is_not_a_proof_transition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "proof.json").write_text(
                json.dumps([{"theorem": "Fake.theorem"}]), encoding="utf-8"
            )
            errors = verified_by_errors(
                [node("logic.example.label_only", "proof.json", "Fake.theorem")],
                root,
            )
        self.assertTrue(any("no complete theorem" in e for e in errors))

    def test_every_transition_field_must_be_nonblank(self) -> None:
        complete = {
            "theorem": "BooleanLaws.actual",
            "tactic": "exact proof",
            "stateBefore": "goal",
            "stateAfter": "no goals",
        }
        for field in ("theorem", "tactic", "stateBefore", "stateAfter"):
            with (
                self.subTest(field=field),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                row = dict(complete)
                row[field] = "  "
                (root / "proof.json").write_text(
                    json.dumps([row]), encoding="utf-8"
                )
                errors = verified_by_errors(
                    [
                        node(
                            "logic.example.blank_transition",
                            "proof.json",
                            "BooleanLaws.actual",
                        )
                    ],
                    root,
                )
                self.assertTrue(any("no complete theorem" in e for e in errors))

    def test_absent_reference_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = self.write_artifact(root, ["BooleanLaws.actual"])
            errors = verified_by_errors(
                [node("logic.example.dangling", artifact, "BooleanLaws.absent")],
                root,
            )
        self.assertTrue(any("is absent" in error for error in errors))

    def test_empty_reference_cannot_bypass_theorem_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = self.write_artifact(root, ["BooleanLaws.actual"])
            errors = verified_by_errors(
                [node("logic.example.empty", artifact, "")], root
            )
        self.assertTrue(any("non-empty theorem identity" in e for e in errors))

    def test_reference_free_link_requires_one_theorem(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = self.write_artifact(root, ["A", "B"])
            errors = verified_by_errors(
                [node("logic.example.ambiguous", artifact, None)], root
            )
        self.assertTrue(any("ambiguous across theorems" in e for e in errors))

    def test_theorem_has_only_one_statement_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact = self.write_artifact(root, ["BooleanLaws.shared"])
            errors = verified_by_errors(
                [
                    node("logic.example.first", artifact, "BooleanLaws.shared"),
                    node("logic.example.second", artifact, "BooleanLaws.shared"),
                ],
                root,
            )
        self.assertTrue(any("claimed by multiple statements" in e for e in errors))
        self.assertTrue(any("logic.example.first" in e for e in errors))
        self.assertTrue(any("logic.example.second" in e for e in errors))

    def test_artifact_must_stay_inside_repository_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            errors = verified_by_errors(
                [node("logic.example.escape", "../proof.json", "T")], root
            )
        self.assertTrue(any("escapes repository root" in error for error in errors))

    def test_backslash_artifact_separators_are_refused(self) -> None:
        """Review F3: a backslash path names a different file on POSIX."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.write_artifact(root, ["BooleanLaws.t"])
            errors = verified_by_errors(
                [node("logic.example.slash", "prover\proof.json", "T")], root
            )
        self.assertTrue(any("forward slashes" in e for e in errors))

    def test_each_citer_of_a_broken_artifact_gets_its_own_error(self) -> None:
        """Review F2: the failure cache must re-attribute, not absorb."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "proof.json").write_text("[]", encoding="utf-8")
            errors = verified_by_errors(
                [
                    node("logic.example.first", "proof.json", "T"),
                    node("logic.example.second", "proof.json", "T"),
                ],
                root,
            )
        self.assertTrue(any("logic.example.first" in e for e in errors))
        self.assertTrue(any("logic.example.second" in e for e in errors))

    def test_malformed_link_shapes_fail_without_jsonschema(self) -> None:
        cases = (
            ({"statement_id": "logic.example.list", "verified_by": "bad"}, "list"),
            ({"statement_id": "logic.example.entry", "verified_by": ["bad"]}, "object"),
            (
                {
                    "statement_id": "logic.example.system",
                    "verified_by": [{"system": "", "artifact": "proof.json"}],
                },
                "system",
            ),
            (
                {
                    "statement_id": "logic.example.artifact",
                    "verified_by": [{"system": "lean4", "artifact": ""}],
                },
                "artifact",
            ),
        )
        for malformed, expected in cases:
            with self.subTest(expected=expected):
                errors = verified_by_errors([malformed], REPO_ROOT)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_unsupported_proof_system_fails_before_ownership(self) -> None:
        malformed = {
            "statement_id": "logic.example.wrong_system",
            "verified_by": [
                {
                    "system": "LEAN4",
                    "artifact": "prover/sample_triples.json",
                    "reference": "BooleanLaws.modus_ponens",
                }
            ],
        }
        errors = verified_by_errors([malformed], REPO_ROOT)
        self.assertTrue(any("supports only `lean4`" in e for e in errors), errors)

    def test_default_cli_paths_work_from_foreign_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "validate_nodes.py")],
                cwd=temporary,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("209 statement nodes", result.stdout)

    def test_wrong_statement_valid_theorem_is_capability_blind_control(self) -> None:
        """Cheap lint cannot prove theorem/statement semantic correspondence."""
        unrelated = node(
            "physics.example.unrelated_gravity_claim",
            "prover/sample_triples.json",
            "BooleanLaws.modus_ponens",
        )
        self.assertEqual(verified_by_errors([unrelated], REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
