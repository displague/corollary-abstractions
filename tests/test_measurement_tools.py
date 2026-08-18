"""Fast regression coverage for the v0.13 measurement utilities."""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import measure_ambiguity as ambiguity_measure  # noqa: E402
import time_tests  # noqa: E402
import plan_test_shards as shard_plan  # noqa: E402
from resolver import ASK, BIND, PASS, GraphIndex, Resolution  # noqa: E402


def _queries(*expectations: str) -> list[dict]:
    return [
        {"text": f"query {position}", "expect": expectation}
        for position, expectation in enumerate(expectations)
    ]


class AmbiguityMeasurementTests(unittest.TestCase):
    def test_pass_stays_in_registered_denominator(self) -> None:
        outcomes = iter((
            Resolution(BIND, "fake", ("one",)),
            Resolution(ASK, "fake", ("one", "two")),
            Resolution(PASS, "fake"),
        ))
        result = ambiguity_measure.measure(
            GraphIndex(statement_ids=("one", "two")),
            {"registered": _queries("resolve", "resolve", "resolve", "refuse")},
            resolver=lambda _text, _index: next(outcomes),
        )

        self.assertEqual(result["schema"], "ambiguity_rate.v2")
        self.assertEqual(result["pooled"], {
            "registered_resolve_queries": 3,
            "bind": 1,
            "ask": 1,
            "pass": 1,
            "ask_rate": 0.3333,
        })
        self.assertEqual(result["adjudication"]["A1"]["of"], 3)

    def test_unexpected_outcome_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unexpected resolver outcome"):
            ambiguity_measure.measure(
                GraphIndex(),
                {"registered": _queries("resolve")},
                resolver=lambda _text, _index: Resolution("guessed", "fake"),
            )

    def test_missing_and_malformed_query_sets_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(FileNotFoundError, "missing"):
                ambiguity_measure._load_query_sets(root, (("set", "missing.json"),))

            bad_cases = {
                "invalid-json.json": "{",
                "no-list.json": '{"queries": {}}',
                "bad-row.json": '{"queries": [3]}',
                "bad-text.json": '{"queries": [{"text": "", "expect": "resolve"}]}',
                "bad-expect.json": (
                    '{"queries": [{"text": "question", "expect": "maybe"}]}'
                ),
            }
            for filename, content in bad_cases.items():
                with self.subTest(filename=filename):
                    (root / filename).write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        ambiguity_measure._load_query_sets(
                            root, (("set", filename),)
                        )

    def test_manifest_digest_is_order_stable_and_drift_sensitive(self) -> None:
        original = ambiguity_measure._manifest_digest({"b": "2", "a": "1"})
        reordered = ambiguity_measure._manifest_digest({"a": "1", "b": "2"})
        drifted = ambiguity_measure._manifest_digest({"a": "1", "b": "3"})
        self.assertEqual(original, reordered)
        self.assertNotEqual(original, drifted)

    def test_text_digest_is_newline_stable_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.json"
            path.write_bytes(b'{\r\n  "value": 1\r\n}\r\n')
            windows = ambiguity_measure._sha256_text(path)
            path.write_bytes(b'{\n  "value": 1\n}\n')
            unix = ambiguity_measure._sha256_text(path)
            path.write_bytes(b'{\n  "value": 2\n}\n')
            drifted = ambiguity_measure._sha256_text(path)
        self.assertEqual(windows, unix)
        self.assertNotEqual(unix, drifted)

    def test_committed_artifact_regenerates_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            generated = Path(tmp) / "ambiguity_rate.json"
            result = ambiguity_measure.run(generated)
            committed = ROOT / "experiments" / "ambiguity_rate.json"
            self.assertEqual(generated.read_bytes(), committed.read_bytes())
        self.assertEqual(result["adjudication"]["A1"], {
            "fired": True,
            "ask_rate": 0.2581,
            "threshold": 0.25,
            "ask": 16,
            "of": 62,
        })
        provenance = result["provenance"]
        self.assertEqual(provenance["algorithm"], "sha256")
        self.assertEqual(len(provenance["query_files"]), 3)
        self.assertEqual(
            set(provenance["resolver_sources"]),
            set(ambiguity_measure.RESOLVER_SOURCES),
        )
        self.assertGreater(provenance["corpus_nodes"]["files"], 0)
        self.assertEqual(len(provenance["measurement_inputs_sha256"]), 64)


class _PassingCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        time.sleep(0.03)

    def check_success(self) -> None:
        time.sleep(0.002)


class _FailingCase(unittest.TestCase):
    def check_failure(self) -> None:
        self.fail("intentional timer failure")


class TimingToolTests(unittest.TestCase):
    def test_success_json_and_fixture_gap_are_explicit(self) -> None:
        target = f"{__name__}._PassingCase.check_success"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "timings.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with (
                patch.object(time_tests, "assert_clean_source"),
                patch.object(
                    time_tests, "environment_identity", return_value={"test": True}
                ),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
            ):
                status = time_tests.main(["--json", str(output), target])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(status, 0)
        self.assertIn("OK", stdout.getvalue())
        self.assertEqual(payload["tests"], 1)
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["targets"], [target])
        self.assertTrue(payload["successful"])
        self.assertEqual(payload["failures"], 0)
        self.assertEqual(payload["errors"], 0)
        self.assertGreater(payload["total_seconds"], payload["timed_test_seconds"])
        self.assertGreaterEqual(payload["fixture_and_overhead_seconds"], 0.02)
        self.assertIn(__name__, payload["timed_tests_by_module"])
        self.assertEqual(len(payload["slowest"]), 1)

    def test_failure_returns_nonzero_and_still_writes_json(self) -> None:
        target = f"{__name__}._FailingCase.check_failure"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "timings.json"
            with (
                patch.object(time_tests, "assert_clean_source"),
                patch.object(
                    time_tests, "environment_identity", return_value={"test": True}
                ),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                status = time_tests.main(["--json", str(output), target])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(status, 1)
        self.assertFalse(payload["successful"])
        self.assertEqual(payload["failures"], 1)
        self.assertEqual(payload["tests"], 1)
        self.assertEqual(len(payload["slowest"]), 1)


class ShardPlanningTests(unittest.TestCase):
    @staticmethod
    def _environment() -> dict:
        return {
            "distributions": {"count": 0, "sha256": "0" * 64},
            "PATH_sha256": "0" * 64,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "COROLLARY_WORDNET": {"present": False, "path": None},
            "worktree_archives": {
                "present": False,
                "files": [],
                "manifest_sha256": None,
            },
            "session22080_ast": {"present": False, "path": "missing-ast"},
            "lean": {
                "present": False,
                "path": "missing-lean",
                "toolchain": time_tests.PINNED_LEAN_TOOLCHAIN,
            },
            "removed_from_child": [
                "PYTHONPATH", "PYTHONHOME", "CORO_SESSION_KEYFILE", "HF_TOKEN"
            ],
        }

    @staticmethod
    def _manifest(rows: list[tuple[str, float]]) -> dict:
        modules = sorted(module for module, _seconds in rows)
        return {
            "schema_version": 1,
            "kind": "whole_suite_module_timings",
            "head": "a" * 40,
            "runtime": {
                "python_executable": "python",
                "python_implementation": "CPython",
                "python_version": "3.test",
                "python_build": "3.test (test)",
                "platform": "test-platform",
                "machine": "test-machine",
                "processor": "test-processor",
                "logical_cpus": 4,
            },
            "environment": ShardPlanningTests._environment(),
            "started_utc": "2026-08-18T00:00:00+00:00",
            "finished_utc": "2026-08-18T01:00:00+00:00",
            "inventory_sha256": shard_plan.inventory_digest(modules),
            "inventory": modules,
            "status": "complete",
            "completed": [
                {
                    "module": module,
                    "receipt": f"modules/{module}.json",
                    "receipt_sha256": "0" * 64,
                    "log": f"modules/{module}.log",
                    "log_sha256": "0" * 64,
                    "started_utc": "2026-08-18T00:00:00+00:00",
                    "finished_utc": "2026-08-18T00:00:00+00:00",
                    "seconds": seconds,
                    "tests": 1,
                    "skipped": 0,
                }
                for module, seconds in sorted(rows)
            ],
        }

    def test_lpt_assignment_is_balanced_and_order_independent(self) -> None:
        rows = [
            ("tests.test_slow", 8.0),
            ("tests.test_mid", 5.0),
            ("tests.test_small", 3.0),
            ("tests.test_tiny", 2.0),
        ]
        forward = shard_plan.balanced_plan(self._manifest(rows), 2)
        reverse = shard_plan.balanced_plan(self._manifest(list(reversed(rows))), 2)
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [shard["predicted_seconds"] for shard in forward["shards"]],
            [10.0, 8.0],
        )
        self.assertEqual(forward["predicted_parallel_wall_seconds"], 10.0)
        self.assertEqual(forward["measured_serial_seconds"], 18.0)
        self.assertEqual(
            forward["measurement_manifest_sha256"],
            shard_plan.hashlib.sha256(
                shard_plan._canonical_json_bytes(self._manifest(rows))
            ).hexdigest(),
        )
        self.assertIn("host-specific", forward["scope"])

    def test_ties_have_explicit_module_and_shard_order(self) -> None:
        manifest = self._manifest([
            ("tests.test_b", 1.0),
            ("tests.test_a", 1.0),
            ("tests.test_c", 1.0),
        ])
        plan = shard_plan.balanced_plan(manifest, 2)
        self.assertEqual(plan["shards"][0]["modules"], ["tests.test_a", "tests.test_c"])
        self.assertEqual(plan["shards"][1]["modules"], ["tests.test_b"])

    def test_more_shards_than_modules_refuses(self) -> None:
        with self.assertRaisesRegex(shard_plan.MeasurementError, "exceeds"):
            shard_plan.balanced_plan(
                self._manifest([("tests.test_a", 1.0)]), 2
            )

    def test_incomplete_duplicate_and_nonfinite_evidence_refuses(self) -> None:
        manifest = self._manifest([
            ("tests.test_a", 1.0),
            ("tests.test_b", 2.0),
        ])
        cases = []
        incomplete = json.loads(json.dumps(manifest))
        incomplete["status"] = "running"
        cases.append(incomplete)
        duplicate = json.loads(json.dumps(manifest))
        duplicate["completed"][1]["module"] = "tests.test_a"
        cases.append(duplicate)
        nonfinite = json.loads(json.dumps(manifest))
        nonfinite["completed"][0]["seconds"] = float("nan")
        cases.append(nonfinite)
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(shard_plan.MeasurementError):
                    shard_plan.balanced_plan(payload, 2)

    def test_plan_loader_binds_raw_receipt_and_log_bytes(self) -> None:
        manifest = self._manifest([("tests.test_a", 1.0)])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            modules = root / "modules"
            modules.mkdir()
            (modules / "tests.test_a.log").write_text("OK\n", encoding="utf-8")
            receipt = {
                "schema_version": 2,
                "head": "a" * 40,
                "runtime": manifest["runtime"],
                "environment": manifest["environment"],
                "started_utc": "2026-08-18T00:00:00+00:00",
                "finished_utc": "2026-08-18T00:00:00+00:00",
                "targets": ["tests.test_a"],
                "successful": True,
                "total_seconds": 1.0,
                "tests": 1,
                "skipped": 0,
                "failures": 0,
                "errors": 0,
            }
            receipt_path = modules / "tests.test_a.json"
            log_path = modules / "tests.test_a.log"
            shard_plan._atomic_json(receipt_path, receipt)
            row = manifest["completed"][0]
            row["receipt_sha256"] = shard_plan._sha256_file(receipt_path)
            row["log_sha256"] = shard_plan._sha256_file(log_path)
            path = root / "manifest.json"
            shard_plan._atomic_json(path, manifest)
            self.assertEqual(shard_plan.load_measurement(path, root=None), manifest)

            receipt_path.write_text(
                json.dumps(receipt) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(
                shard_plan.MeasurementError, "raw receipt hash mismatch"
            ):
                shard_plan.load_measurement(path, root=None)

            shard_plan._atomic_json(receipt_path, receipt)
            row["receipt_sha256"] = shard_plan._sha256_file(receipt_path)
            shard_plan._atomic_json(path, manifest)
            log_path.write_text("changed\n", encoding="utf-8")
            with self.assertRaisesRegex(
                shard_plan.MeasurementError, "raw log hash mismatch"
            ):
                shard_plan.load_measurement(path, root=None)

    def test_new_manifest_satisfies_its_own_schema(self) -> None:
        manifest = shard_plan._new_manifest(
            "a" * 40, ["tests.test_a"], self._environment()
        )
        self.assertIs(shard_plan._validate_manifest(manifest), manifest)

    def test_environment_schema_and_nested_digests_fail_closed(self) -> None:
        manifest = self._manifest([("tests.test_a", 1.0)])
        bad_path = json.loads(json.dumps(manifest))
        bad_path["environment"]["PATH_sha256"] = "not-a-digest"
        bad_archive = json.loads(json.dumps(manifest))
        bad_archive["environment"]["worktree_archives"] = {
            "present": True,
            "files": [{"path": "x", "bytes": 1, "sha256": "0" * 64}],
            "manifest_sha256": "0" * 64,
        }
        bad_lean = json.loads(json.dumps(manifest))
        bad_lean["environment"]["lean"]["toolchain"] = "unpinned"
        for payload in (bad_path, bad_archive, bad_lean):
            with self.subTest(payload=payload):
                with self.assertRaises(shard_plan.MeasurementError):
                    shard_plan._validate_manifest(payload)

    def test_child_environment_removes_import_and_secret_overrides(self) -> None:
        poisoned = {
            "PATH": "safe",
            "PYTHONPATH": "injected",
            "PYTHONHOME": "injected-home",
            "CORO_SESSION_KEYFILE": "attacker-key",
            "HF_TOKEN": "secret",
        }
        clean = time_tests.sanitized_environment(poisoned)
        for name in (
            "PYTHONPATH", "PYTHONHOME", "CORO_SESSION_KEYFILE", "HF_TOKEN"
        ):
            self.assertNotIn(name, clean)
        self.assertEqual(clean["PYTHONNOUSERSITE"], "1")

    def test_discovery_is_sorted_and_ignores_non_test_modules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            for name in ("test_z.py", "helper.py", "test_a.py"):
                (tests / name).write_text("", encoding="utf-8")
            modules = shard_plan.discover_modules(root)
        self.assertEqual(modules, ["tests.test_a", "tests.test_z"])

    def test_nested_test_module_refuses_instead_of_disappearing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "tests" / "nested"
            nested.mkdir(parents=True)
            (nested / "test_hidden.py").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(shard_plan.MeasurementError, "nested"):
                shard_plan.discover_modules(root)

    def test_git_inventory_excludes_an_untracked_test(self) -> None:
        listing = "tests/test_z.py\ntests/helper.py\ntests/test_a.py\n"
        with patch.object(
            shard_plan.subprocess,
            "run",
            return_value=shard_plan.subprocess.CompletedProcess(
                args=[], returncode=0, stdout=listing
            ),
        ):
            modules = shard_plan.modules_at_head("a" * 40, ROOT)
        self.assertEqual(modules, ["tests.test_a", "tests.test_z"])

    def test_committed_nested_test_refuses(self) -> None:
        listing = "tests/test_a.py\ntests/nested/test_hidden.py\n"
        with patch.object(
            shard_plan.subprocess,
            "run",
            return_value=shard_plan.subprocess.CompletedProcess(
                args=[], returncode=0, stdout=listing
            ),
        ):
            with self.assertRaisesRegex(shard_plan.MeasurementError, "nested"):
                shard_plan.modules_at_head("a" * 40, ROOT)

    def test_plan_git_provenance_requires_commit_and_exact_inventory(self) -> None:
        manifest = self._manifest([("tests.test_a", 1.0)])
        missing = shard_plan.subprocess.CompletedProcess(args=[], returncode=1)
        with patch.object(shard_plan.subprocess, "run", return_value=missing):
            with self.assertRaisesRegex(shard_plan.MeasurementError, "available commit"):
                shard_plan._verify_git_provenance(manifest, ROOT)
        exists = shard_plan.subprocess.CompletedProcess(args=[], returncode=0)
        with (
            patch.object(shard_plan.subprocess, "run", return_value=exists),
            patch.object(
                shard_plan, "modules_at_head", return_value=["tests.test_other"]
            ),
        ):
            with self.assertRaisesRegex(shard_plan.MeasurementError, "inventory"):
                shard_plan._verify_git_provenance(manifest, ROOT)

    def test_cleanliness_check_includes_untracked_files(self) -> None:
        status = "?? tests/test_injected.py\n"
        with patch.object(
            shard_plan.subprocess,
            "run",
            return_value=shard_plan.subprocess.CompletedProcess(
                args=[], returncode=0, stdout=status
            ),
        ):
            self.assertEqual(
                shard_plan._working_changes(ROOT),
                ["?? tests/test_injected.py"],
            )

    def test_clean_source_refuses_ignored_importable_code(self) -> None:
        for suffix in ("pyc", "pyd", "so", "dll"):
            with self.subTest(suffix=suffix):
                clean = shard_plan.subprocess.CompletedProcess(
                    args=[], returncode=0, stdout=""
                )
                ignored = shard_plan.subprocess.CompletedProcess(
                    args=[], returncode=0,
                    stdout=f"scripts/__pycache__/shadow.{suffix}\0".encode(),
                )
                with patch.object(
                    time_tests.subprocess, "run", side_effect=[clean, ignored]
                ):
                    with self.assertRaisesRegex(RuntimeError, "ignored executable"):
                        time_tests.assert_clean_source(ROOT)


class HistoricalGateReceiptTests(unittest.TestCase):
    def test_retained_v013_receipts_match_the_released_ledger(self) -> None:
        ledger = json.loads(
            (ROOT / "reports" / "test_gate_v013.json").read_text(encoding="utf-8")
        )
        retained = ROOT / "reports" / "test_gate_v013"
        all_modules: list[str] = []
        for shard in ledger["shards"]:
            number = shard["shard"]
            receipt = json.loads(
                (retained / "receipts" / f"shard-{number}.json").read_text(
                    encoding="utf-8"
                )
            )
            modules = (
                retained / "modules" / f"shard-{number}.txt"
            ).read_text(encoding="utf-8").splitlines()
            log = (retained / "logs" / f"shard-{number}.log").read_text(
                encoding="utf-8"
            )
            self.assertEqual(receipt["shard"], number)
            self.assertEqual(receipt["head"], ledger["head"])
            self.assertEqual(receipt["modules"], len(modules))
            self.assertEqual(receipt["started"], shard["started"])
            self.assertEqual(receipt["elapsed_seconds"], shard["elapsed_seconds"])
            self.assertEqual(receipt["exit_code"], shard["exit_code"])
            self.assertEqual(modules, shard["modules"])
            match = re.search(r"Ran (\d+) tests in ([0-9.]+)s", log)
            self.assertIsNotNone(match)
            self.assertEqual(int(match.group(1)), shard["tests"])
            self.assertEqual(float(match.group(2)), shard["unittest_seconds"])
            skipped = re.search(r"skipped=(\d+)", log)
            self.assertEqual(int(skipped.group(1)) if skipped else 0, shard["skipped"])
            self.assertRegex(log, r"(?m)^OK(?: \(skipped=\d+\))?$")
            all_modules.extend(modules)
        self.assertEqual(len(all_modules), ledger["summary"]["modules"])
        self.assertEqual(len(all_modules), len(set(all_modules)))


if __name__ == "__main__":
    unittest.main()
