#!/usr/bin/env python3
"""Per-test wall-clock, because every explanation of the slow gate was wrong.

Three times during v0.12 a reason was given for the ~10-hour suite and three
times it was folklore:

1. "several tests each reload the 12k graph" — only FOUR modules rebuild it,
   and they cache in `setUpClass`.
2. "the cost is the eight torch modules" — the modules actually observed
   crawling (`test_controller`, `test_ask`, `test_corpus_analogy_split`)
   contain no torch, no epochs, no training.
3. "I don't know" — correct, and the reason it stayed unknown is that
   `unittest -v` prints test NAMES and not DURATIONS, so every estimate came
   from a proxy: CPU counters, progress marks, module counts.

This prints the durations. It is deliberately tiny and has no dependencies
beyond the standard library, so it can be pointed at one suspicious module
during a release without competing for much.

    python scripts/time_tests.py tests.test_ask
    python scripts/time_tests.py --top 25 tests.test_controller tests.test_ask
    python scripts/time_tests.py --json timings.json tests.test_probes

The output is a ranked table, because the question is never "how long did
the suite take" — it is "which handful of tests are the suite".
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

# `python -m unittest` puts the repo root on sys.path; running this as a file
# does not, so `tests.test_x` would not import. Both the root (for `tests`)
# and `scripts/` (for what the tests import) are needed.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

PINNED_LEAN_TOOLCHAIN = "leanprover/lean4:v4.32.2"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def runtime_identity() -> dict:
    return {
        "python_executable": sys.executable,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_build": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor()
        or os.environ.get("PROCESSOR_IDENTIFIER", ""),
        "logical_cpus": os.cpu_count(),
    }


def sanitized_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if source is None else source)
    for name in ("PYTHONPATH", "PYTHONHOME", "CORO_SESSION_KEYFILE", "HF_TOKEN"):
        env.pop(name, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    return env


def _file_identity(path: Path) -> dict:
    resolved = path.resolve()
    if not resolved.is_file():
        return {"present": False, "path": str(resolved)}
    return {
        "present": True,
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": _sha256_file(resolved),
    }


def _archive_identity(root: Path) -> dict:
    archive_root = root / "data_sources" / "archives"
    if not archive_root.is_dir():
        return {"present": False, "files": [], "manifest_sha256": None}
    files = []
    for path in sorted(p for p in archive_root.rglob("*") if p.is_file()):
        files.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
        })
    encoded = "".join(
        f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n" for row in files
    ).encode("utf-8")
    return {
        "present": True,
        "files": files,
        "manifest_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _lean_identity() -> dict:
    mangled = PINNED_LEAN_TOOLCHAIN.replace("/", "--").replace(":", "---")
    binary = (
        Path.home() / ".elan" / "toolchains" / mangled / "bin"
        / ("lean.exe" if os.name == "nt" else "lean")
    )
    identity = _file_identity(binary)
    identity["toolchain"] = PINNED_LEAN_TOOLCHAIN
    return identity


def environment_identity(
    env: Mapping[str, str] | None = None, root: Path = REPO,
) -> dict:
    values = os.environ if env is None else env
    distributions = sorted(
        f"{dist.metadata.get('Name', '<unnamed>')}=={dist.version}"
        for dist in importlib.metadata.distributions()
    )
    distribution_bytes = "".join(f"{row}\n" for row in distributions).encode(
        "utf-8"
    )
    wordnet_value = values.get("COROLLARY_WORDNET")
    return {
        "distributions": {
            "count": len(distributions),
            "sha256": hashlib.sha256(distribution_bytes).hexdigest(),
        },
        "PATH_sha256": hashlib.sha256(values.get("PATH", "").encode("utf-8")).hexdigest(),
        "PYTHONIOENCODING": values.get("PYTHONIOENCODING", ""),
        "PYTHONDONTWRITEBYTECODE": values.get("PYTHONDONTWRITEBYTECODE", ""),
        "PYTHONNOUSERSITE": values.get("PYTHONNOUSERSITE", ""),
        "COROLLARY_WORDNET": (
            {"present": False, "path": None}
            if wordnet_value is None else _file_identity(Path(wordnet_value))
        ),
        "worktree_archives": _archive_identity(root),
        "session22080_ast": _file_identity(
            root / "prover" / "lean" / "session" / ".lake" / "build"
            / "ir" / "Session22080.ast.json"
        ),
        "lean": _lean_identity(),
        "removed_from_child": [
            "PYTHONPATH", "PYTHONHOME", "CORO_SESSION_KEYFILE", "HF_TOKEN"
        ],
    }


def assert_clean_source(root: Path = REPO) -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root, check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    if status:
        raise RuntimeError("timing JSON requires a clean tracked/untracked worktree")
    ignored = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "-z",
         "--", "*.py", "*.pyc", "*.pyd", "*.so", "*.dll"],
        cwd=root, check=True, capture_output=True,
    ).stdout.split(b"\0")
    unsafe = []
    for raw in ignored:
        if not raw:
            continue
        name = raw.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        if not name.startswith(".venv/"):
            unsafe.append(name)
    if unsafe:
        raise RuntimeError(
            "ignored executable Python files outside .venv: " + ", ".join(unsafe)
        )


class TimingResult(unittest.TextTestResult):
    """Records elapsed per test, from `startTest` to `stopTest`.

    **Fixture time is NOT captured, and the gap is the point.** `unittest`
    runs `setUpClass` and `setUpModule` before any `startTest`, so their cost
    lands in no test's row. An earlier version of this docstring claimed the
    cost was attributed to the first test of the class; that was wrong, and
    the first real run proved it: `test_corpus_analogy_split` summed to
    6,064.8s across its tests while the module took 10,765.0s. The missing
    ~4,700s is class fixtures.

    So read the output as two numbers, not one. `total` is what the module
    costs a gate. The sum of the rows is what the *tests* cost. When they
    diverge, the difference is fixture work, and no amount of speeding up
    individual tests will touch it.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings: list[tuple[str, float, str]] = []
        self._started: float | None = None

    def startTest(self, test) -> None:
        self._started = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test) -> None:
        elapsed = time.perf_counter() - (self._started or time.perf_counter())
        self.timings.append((test.id(), elapsed, test.__class__.__module__))
        super().stopTest(test)


class TimingRunner(unittest.TextTestRunner):
    resultclass = TimingResult


def _git_head() -> str:
    """Return the exact source revision measured by this process."""
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="+", help="module or test ids")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args(argv)

    if args.json:
        assert_clean_source()
    started_utc = _utc_now()

    suite = unittest.defaultTestLoader.loadTestsFromNames(args.targets)
    runner = TimingRunner(verbosity=0)
    started = time.perf_counter()
    result = runner.run(suite)
    total = time.perf_counter() - started
    finished_utc = _utc_now()

    rows = sorted(result.timings, key=lambda r: -r[1])
    print(f"\n{len(rows)} tests in {total:.1f}s "
          f"({'OK' if result.wasSuccessful() else 'FAILED'})")

    by_module: dict[str, float] = {}
    for _tid, elapsed, module in rows:
        by_module[module] = by_module.get(module, 0.0) + elapsed
    timed_seconds = sum(elapsed for _tid, elapsed, _module in rows)
    fixture_and_overhead = max(0.0, total - timed_seconds)
    print(f"\ntimed tests: {timed_seconds:.1f}s; "
          f"fixtures/runner overhead: {fixture_and_overhead:.1f}s")
    print("\ntimed test bodies by module (fixtures excluded):")
    for module, elapsed in sorted(by_module.items(), key=lambda kv: -kv[1]):
        share = 100 * elapsed / total if total else 0
        print(f"  {elapsed:8.1f}s  {share:5.1f}%  {module}")

    print(f"\nslowest {min(args.top, len(rows))} tests:")
    for tid, elapsed, _m in rows[:args.top]:
        print(f"  {elapsed:8.2f}s  {tid}")

    if args.json:
        assert_clean_source()
        with args.json.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(
                {
                    "schema_version": 2,
                    "head": _git_head(),
                    "runtime": runtime_identity(),
                    "environment": environment_identity(),
                    "started_utc": started_utc,
                    "finished_utc": finished_utc,
                    "targets": args.targets,
                    "successful": result.wasSuccessful(),
                    "total_seconds": round(total, 2),
                    "timed_test_seconds": round(timed_seconds, 2),
                    "fixture_and_overhead_seconds": round(
                        fixture_and_overhead, 2
                    ),
                    "tests": len(rows),
                    "failures": len(result.failures),
                    "errors": len(result.errors),
                    "skipped": len(result.skipped),
                    "timed_tests_by_module": {
                        k: round(v, 2) for k, v in by_module.items()
                    },
                    "slowest": [
                        {"test": t, "seconds": round(e, 3)} for t, e, _ in rows
                    ],
                },
                indent=2,
            ) + "\n")
        print(f"\nwrote {args.json}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
