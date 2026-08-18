"""Fast regression coverage for the v0.13 measurement utilities."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import measure_ambiguity as ambiguity_measure  # noqa: E402
import time_tests  # noqa: E402
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
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = time_tests.main(["--json", str(output), target])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(status, 0)
        self.assertIn("OK", stdout.getvalue())
        self.assertEqual(payload["tests"], 1)
        self.assertGreater(payload["total_seconds"], payload["timed_test_seconds"])
        self.assertGreaterEqual(payload["fixture_and_overhead_seconds"], 0.02)
        self.assertIn(__name__, payload["timed_tests_by_module"])
        self.assertEqual(len(payload["slowest"]), 1)

    def test_failure_returns_nonzero_and_still_writes_json(self) -> None:
        target = f"{__name__}._FailingCase.check_failure"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "timings.json"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                status = time_tests.main(["--json", str(output), target])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(status, 1)
        self.assertEqual(payload["tests"], 1)
        self.assertEqual(len(payload["slowest"]), 1)


if __name__ == "__main__":
    unittest.main()
