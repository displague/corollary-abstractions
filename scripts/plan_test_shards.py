#!/usr/bin/env python3
"""Measure test modules at one frozen Git tip and plan balanced gate shards.

The v0.13 gate proved that module count is a bad proxy for runtime: one module
cost more than two hours while ten others finished in four seconds.  This tool
uses the measurement that matters.  ``measure`` runs every discovered
``tests/test_*.py`` module, one at a time, and retains a raw timing receipt and
log for each module.  Its manifest is replaced atomically after every module,
so an interrupted multi-hour run can resume without inventing results.

``plan`` applies deterministic longest-processing-time-first assignment: sort
by decreasing measured module wall clock (module name breaks ties), then give
each module to the currently lightest shard (shard number breaks ties).  It
refuses incomplete, failed, duplicated, non-finite, or wrong-tip evidence.

Neither command changes which tests run.  In particular, the expensive blind
control remains whole and is measured exactly like every other module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import time_tests

REPO = Path(__file__).resolve().parents[1]
MODULE_PATTERN = re.compile(r"tests\.test_[a-zA-Z0-9_]+\Z")
GIT_OBJECT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
RUNTIME_KEYS = {
    "python_executable", "python_implementation", "python_version",
    "python_build", "platform", "machine", "processor", "logical_cpus",
}


class MeasurementError(ValueError):
    """Timing evidence is absent, inconsistent, or unsafe to consume."""


def discover_modules(root: Path = REPO) -> list[str]:
    """Return the exact unittest module inventory in stable lexical order."""
    paths = sorted(path for path in (root / "tests").rglob("test_*.py") if path.is_file())
    nested = [path for path in paths if path.parent != root / "tests"]
    if nested:
        raise MeasurementError(
            "nested test modules are unsupported: "
            + ", ".join(path.relative_to(root).as_posix() for path in nested)
        )
    return [f"tests.{path.stem}" for path in paths]


def inventory_digest(modules: list[str]) -> str:
    payload = "".join(f"{module}\n" for module in modules).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise MeasurementError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def _head(root: Path = REPO) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()


def modules_at_head(head: str, root: Path = REPO) -> list[str]:
    """Return only test modules committed in the frozen Git tree."""
    output = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", head, "--", "tests"],
        cwd=root, check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    modules = []
    nested = []
    for filename in output.splitlines():
        path = Path(filename)
        if path.name.startswith("test_") and path.suffix == ".py":
            if path.parent.as_posix() != "tests":
                nested.append(filename)
            else:
                modules.append(f"tests.{path.stem}")
    if nested:
        raise MeasurementError("nested committed test modules are unsupported: " + ", ".join(nested))
    return sorted(modules)


def _working_changes(root: Path = REPO) -> list[str]:
    """Return tracked and untracked changes; either can alter Python imports."""
    output = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root, check=True, capture_output=True, text=True, encoding="utf-8",
    ).stdout
    return [line for line in output.splitlines() if line]


def _assert_frozen(head: str, root: Path) -> None:
    current = _head(root)
    if current != head:
        raise MeasurementError(f"current head {current} != frozen {head}")
    try:
        time_tests.assert_clean_source(root)
    except RuntimeError as exc:
        raise MeasurementError(str(exc)) from exc


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(_canonical_json_bytes(payload).decode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _canonical_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _new_manifest(
    head: str, modules: list[str], environment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "whole_suite_module_timings",
        "head": head,
        "runtime": _runtime_identity(),
        "environment": environment,
        "started_utc": _utc_now(),
        "finished_utc": None,
        "inventory_sha256": inventory_digest(modules),
        "inventory": modules,
        "status": "running",
        "completed": [],
    }


def _runtime_identity() -> dict[str, Any]:
    return time_tests.runtime_identity()


def _child_environment_identity(root: Path, env: dict[str, str]) -> dict[str, Any]:
    code = (
        "import json,sys; "
        f"sys.path.insert(0, {str(root / 'scripts')!r}); "
        "import time_tests; "
        "print(json.dumps(time_tests.environment_identity()))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=root, env=env, check=True,
        capture_output=True, text=True, encoding="utf-8",
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise MeasurementError("child environment identity was not JSON") from exc
    if not isinstance(payload, dict):
        raise MeasurementError("child environment identity is malformed")
    return payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise MeasurementError(f"measurement {field} time is absent")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise MeasurementError(f"measurement {field} time is malformed") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise MeasurementError(f"measurement {field} time is not UTC")
    return parsed


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _validate_file_identity(value: Any, field: str) -> None:
    if not isinstance(value, dict) or not isinstance(value.get("present"), bool):
        raise MeasurementError(f"{field} file identity is malformed")
    expected = {"present", "path", "bytes", "sha256"} if value["present"] else {
        "present", "path"
    }
    if set(value) != expected or not isinstance(value.get("path"), (str, type(None))):
        raise MeasurementError(f"{field} file identity is malformed")
    if value["present"] and (
        not isinstance(value["bytes"], int) or isinstance(value["bytes"], bool)
        or value["bytes"] < 0 or not _is_sha256(value["sha256"])
        or not isinstance(value["path"], str)
    ):
        raise MeasurementError(f"{field} file identity is malformed")


def _validate_environment(environment: Any) -> None:
    keys = {
        "distributions", "PATH_sha256", "PYTHONIOENCODING",
        "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "COROLLARY_WORDNET",
        "worktree_archives", "session22080_ast", "lean", "removed_from_child",
    }
    if not isinstance(environment, dict) or set(environment) != keys:
        raise MeasurementError("measurement environment identity is malformed")
    distributions = environment["distributions"]
    if (
        not isinstance(distributions, dict)
        or set(distributions) != {"count", "sha256"}
        or not isinstance(distributions["count"], int)
        or isinstance(distributions["count"], bool)
        or distributions["count"] < 0
        or not _is_sha256(distributions["sha256"])
    ):
        raise MeasurementError("distribution identity is malformed")
    if not _is_sha256(environment["PATH_sha256"]):
        raise MeasurementError("PATH identity is malformed")
    for key, expected in (
        ("PYTHONIOENCODING", "utf-8"),
        ("PYTHONDONTWRITEBYTECODE", "1"),
        ("PYTHONNOUSERSITE", "1"),
    ):
        if environment[key] != expected:
            raise MeasurementError(f"{key} is not frozen")
    if environment["removed_from_child"] != [
        "PYTHONPATH", "PYTHONHOME", "CORO_SESSION_KEYFILE", "HF_TOKEN"
    ]:
        raise MeasurementError("child environment sanitization policy drifted")
    _validate_file_identity(environment["COROLLARY_WORDNET"], "COROLLARY_WORDNET")
    _validate_file_identity(environment["session22080_ast"], "session22080_ast")
    lean = environment["lean"]
    if not isinstance(lean, dict) or lean.get("toolchain") != time_tests.PINNED_LEAN_TOOLCHAIN:
        raise MeasurementError("Lean identity is malformed")
    lean_file = {key: value for key, value in lean.items() if key != "toolchain"}
    _validate_file_identity(lean_file, "Lean")
    archives = environment["worktree_archives"]
    if not isinstance(archives, dict) or set(archives) != {
        "present", "files", "manifest_sha256"
    } or not isinstance(archives["present"], bool) or not isinstance(
        archives["files"], list
    ):
        raise MeasurementError("worktree archive identity is malformed")
    if not archives["present"]:
        if archives["files"] or archives["manifest_sha256"] is not None:
            raise MeasurementError("absent worktree archive has content")
        return
    if not _is_sha256(archives["manifest_sha256"]):
        raise MeasurementError("worktree archive manifest digest is malformed")
    paths = []
    for row in archives["files"]:
        if (
            not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}
            or not isinstance(row["path"], str)
            or not isinstance(row["bytes"], int) or isinstance(row["bytes"], bool)
            or row["bytes"] < 0 or not _is_sha256(row["sha256"])
        ):
            raise MeasurementError("worktree archive row is malformed")
        paths.append(row["path"])
    if paths != sorted(set(paths)):
        raise MeasurementError("worktree archive paths are not unique and sorted")
    encoded = "".join(
        f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n"
        for row in archives["files"]
    ).encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != archives["manifest_sha256"]:
        raise MeasurementError("worktree archive manifest digest mismatch")


def _validate_manifest(
    payload: Any, *, expected_head: str | None = None,
    expected_modules: list[str] | None = None,
    expected_runtime: dict[str, Any] | None = None,
    expected_environment: dict[str, Any] | None = None,
    require_complete: bool = False,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise MeasurementError("unsupported measurement manifest")
    if payload.get("kind") != "whole_suite_module_timings":
        raise MeasurementError("not a module-timing manifest")
    head = payload.get("head")
    modules = payload.get("inventory")
    completed = payload.get("completed")
    runtime = payload.get("runtime")
    environment = payload.get("environment")
    status = payload.get("status")
    if not isinstance(head, str) or not GIT_OBJECT_PATTERN.fullmatch(head):
        raise MeasurementError("manifest head is not a full Git object id")
    if expected_head is not None and head != expected_head:
        raise MeasurementError(f"measurement head {head} != expected {expected_head}")
    if (
        not isinstance(runtime, dict) or set(runtime) != RUNTIME_KEYS
        or not isinstance(runtime.get("logical_cpus"), int)
        or isinstance(runtime.get("logical_cpus"), bool)
        or runtime["logical_cpus"] < 1
        or any(
            not isinstance(runtime.get(key), str)
            for key in RUNTIME_KEYS if key != "logical_cpus"
        )
    ):
        raise MeasurementError("measurement runtime identity is malformed")
    if expected_runtime is not None and runtime != expected_runtime:
        raise MeasurementError("measurement runtime differs from current runtime")
    _validate_environment(environment)
    if expected_environment is not None and environment != expected_environment:
        raise MeasurementError("measurement environment differs from current environment")
    if (
        not isinstance(modules, list) or not modules
        or any(not isinstance(m, str) or not MODULE_PATTERN.fullmatch(m) for m in modules)
        or len(modules) != len(set(modules))
        or modules != sorted(modules)
    ):
        raise MeasurementError("inventory must be unique, sorted test modules")
    if payload.get("inventory_sha256") != inventory_digest(modules):
        raise MeasurementError("inventory digest mismatch")
    if expected_modules is not None and modules != expected_modules:
        raise MeasurementError("measurement inventory differs from frozen inventory")
    if not isinstance(completed, list):
        raise MeasurementError("completed rows must be a list")
    if status not in {"running", "complete"}:
        raise MeasurementError("measurement status is invalid")
    started = _parse_utc(payload.get("started_utc"), "start")
    if status == "complete":
        finished = _parse_utc(payload.get("finished_utc"), "finish")
        if finished < started:
            raise MeasurementError("measurement finishes before it starts")
    elif payload.get("finished_utc") is not None:
        raise MeasurementError("running measurement already has a finish time")
    seen: set[str] = set()
    for row in completed:
        if not isinstance(row, dict) or set(row) != {
            "module", "receipt", "receipt_sha256", "log", "log_sha256",
            "started_utc", "finished_utc", "seconds", "tests", "skipped",
        }:
            raise MeasurementError("malformed completed row")
        module = row["module"]
        seconds = row["seconds"]
        for field in ("receipt", "log"):
            value = row[field]
            parts = Path(value).parts if isinstance(value, str) else ()
            if (
                not parts or Path(value).is_absolute() or ".." in parts
                or parts[0] != "modules"
            ):
                raise MeasurementError(f"unsafe {field} path for {module}")
        for field in ("receipt_sha256", "log_sha256"):
            value = row[field]
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                raise MeasurementError(f"invalid {field} for {module}")
        if module not in modules or module in seen:
            raise MeasurementError("completed modules are duplicated or outside inventory")
        if (
            not isinstance(seconds, (int, float)) or isinstance(seconds, bool)
            or not math.isfinite(seconds) or seconds < 0
        ):
            raise MeasurementError(f"invalid wall clock for {module}")
        row_started = _parse_utc(row["started_utc"], f"{module} start")
        row_finished = _parse_utc(row["finished_utc"], f"{module} finish")
        if row_started < started or row_finished < row_started:
            raise MeasurementError(f"invalid timing interval for {module}")
        if seen:
            prior = _parse_utc(
                completed[len(seen) - 1]["finished_utc"], "prior module finish"
            )
            if row_started < prior:
                raise MeasurementError("module timing intervals overlap or reverse")
        if (
            not isinstance(row["tests"], int) or isinstance(row["tests"], bool)
            or row["tests"] <= 0
        ):
            raise MeasurementError(f"invalid test count for {module}")
        if (
            not isinstance(row["skipped"], int) or isinstance(row["skipped"], bool)
            or row["skipped"] < 0
            or row["skipped"] > row["tests"]
        ):
            raise MeasurementError(f"invalid skip count for {module}")
        seen.add(module)
    completed_modules = [row["module"] for row in completed]
    expected_prefix = modules[:len(completed_modules)]
    if completed_modules != expected_prefix:
        raise MeasurementError("completed rows are not the deterministic inventory prefix")
    if status == "complete" and completed:
        last_finished = _parse_utc(
            completed[-1]["finished_utc"], "last module finish"
        )
        if last_finished > finished:
            raise MeasurementError("module timing exceeds manifest finish")
    if require_complete:
        if payload.get("status") != "complete" or seen != set(modules):
            raise MeasurementError("measurement is not complete")
    return payload


def _verify_completed_artifacts(
    manifest: dict[str, Any], path: Path,
) -> None:
    """Verify raw receipts and logs for every row, including partial runs."""
    base = path.parent.resolve()
    for row in manifest["completed"]:
        receipt_path = (base / row["receipt"]).resolve()
        log_path = (base / row["log"]).resolve()
        if base not in receipt_path.parents or base not in log_path.parents:
            raise MeasurementError(f"artifact escaped measurement directory: {row['module']}")
        if _sha256_file(receipt_path) != row["receipt_sha256"]:
            raise MeasurementError(f"raw receipt hash mismatch for {row['module']}")
        if _sha256_file(log_path) != row["log_sha256"]:
            raise MeasurementError(f"raw log hash mismatch for {row['module']}")
        receipt = _read_json(receipt_path)
        receipt_started = (
            _parse_utc(receipt.get("started_utc"), f"{row['module']} receipt start")
            if isinstance(receipt, dict) else None
        )
        receipt_finished = (
            _parse_utc(receipt.get("finished_utc"), f"{row['module']} receipt finish")
            if isinstance(receipt, dict) else None
        )
        row_started = _parse_utc(row["started_utc"], f"{row['module']} row start")
        row_finished = _parse_utc(row["finished_utc"], f"{row['module']} row finish")
        if (
            not isinstance(receipt, dict)
            or receipt.get("schema_version") != 2
            or receipt.get("head") != manifest["head"]
            or receipt.get("runtime") != manifest["runtime"]
            or receipt.get("environment") != manifest["environment"]
            or receipt.get("targets") != [row["module"]]
            or receipt.get("successful") is not True
            or receipt.get("failures") != 0
            or receipt.get("errors") != 0
            or receipt.get("total_seconds") != row["seconds"]
            or receipt.get("tests") != row["tests"]
            or receipt.get("skipped") != row["skipped"]
            or receipt_started < row_started
            or receipt_finished < receipt_started
            or receipt_finished > row_finished
        ):
            raise MeasurementError(f"raw receipt mismatch for {row['module']}")
        if not log_path.is_file():
            raise MeasurementError(f"missing raw log for {row['module']}")


def load_measurement(
    path: Path, *, root: Path | None = REPO,
) -> dict[str, Any]:
    """Load a complete manifest and verify every retained raw receipt."""
    manifest = _validate_manifest(_read_json(path), require_complete=True)
    if root is not None:
        _verify_git_provenance(manifest, root.resolve())
    _verify_completed_artifacts(manifest, path)
    return manifest


def _read_json(path: Path) -> Any:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MeasurementError(f"cannot read {path}: {exc}") from exc
    if raw != _canonical_json_bytes(payload):
        raise MeasurementError(f"JSON is not canonical LF/indent form: {path}")
    return payload


def _verify_git_provenance(manifest: dict[str, Any], root: Path) -> None:
    head = manifest["head"]
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{head}^{{commit}}"], cwd=root,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if exists.returncode != 0:
        raise MeasurementError("measurement head is not an available commit")
    if modules_at_head(head, root) != manifest["inventory"]:
        raise MeasurementError("measurement inventory differs from its Git commit")


def measure(out_dir: Path, expected_head: str, *, root: Path = REPO) -> dict[str, Any]:
    root = root.resolve()
    out_dir = out_dir.resolve()
    if out_dir == root or root in out_dir.parents:
        raise MeasurementError("measurement output must be outside the worktree")
    _assert_frozen(expected_head, root)

    modules = modules_at_head(expected_head, root)
    filesystem_modules = discover_modules(root)
    if filesystem_modules != modules:
        raise MeasurementError("filesystem test inventory differs from frozen Git tree")
    manifest_path = out_dir / "manifest.json"
    env = time_tests.sanitized_environment()
    expected_environment = _child_environment_identity(root, env)
    if manifest_path.exists():
        manifest = _validate_manifest(
            _read_json(manifest_path), expected_head=expected_head,
            expected_modules=modules, expected_runtime=_runtime_identity(),
            expected_environment=expected_environment,
        )
        _verify_completed_artifacts(manifest, manifest_path)
        if manifest["status"] == "complete":
            return manifest
        if manifest["status"] != "running":
            raise MeasurementError("only a running measurement may resume")
    else:
        manifest = _new_manifest(expected_head, modules, expected_environment)
        _atomic_json(manifest_path, manifest)

    completed = {row["module"] for row in manifest["completed"]}
    for module in modules:
        if module in completed:
            continue
        _assert_frozen(expected_head, root)
        stem = module.removeprefix("tests.")
        receipt_rel = f"modules/{stem}.json"
        log_rel = f"modules/{stem}.log"
        receipt_path = out_dir / receipt_rel
        log_path = out_dir / log_rel
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"measuring {module}", flush=True)
        module_started = _utc_now()
        with log_path.open("w", encoding="utf-8", newline="\n") as log:
            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "time_tests.py"),
                 "--json", str(receipt_path), module],
                cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT,
                check=False,
            )
        _assert_frozen(expected_head, root)
        module_finished = _utc_now()
        receipt = _read_json(receipt_path)
        if (
            result.returncode != 0 or not isinstance(receipt, dict)
            or receipt.get("schema_version") != 2
            or receipt.get("head") != expected_head
            or receipt.get("runtime") != _runtime_identity()
            or receipt.get("environment") != expected_environment
            or receipt.get("targets") != [module]
            or receipt.get("successful") is not True
            or receipt.get("failures") != 0 or receipt.get("errors") != 0
        ):
            raise MeasurementError(
                f"{module} failed or emitted an inconsistent receipt; see {log_path}"
            )
        row = {
            "module": module,
            "receipt": receipt_rel,
            "receipt_sha256": _sha256_file(receipt_path),
            "log": log_rel,
            "log_sha256": _sha256_file(log_path),
            "started_utc": module_started,
            "finished_utc": module_finished,
            "seconds": receipt["total_seconds"],
            "tests": receipt["tests"],
            "skipped": receipt["skipped"],
        }
        manifest["completed"].append(row)
        _validate_manifest(
            manifest, expected_head=expected_head, expected_modules=modules,
            expected_runtime=_runtime_identity(),
            expected_environment=expected_environment,
        )
        _atomic_json(manifest_path, manifest)

    manifest["status"] = "complete"
    manifest["finished_utc"] = _utc_now()
    _validate_manifest(
        manifest, expected_head=expected_head, expected_modules=modules,
        expected_runtime=_runtime_identity(),
        expected_environment=expected_environment, require_complete=True,
    )
    _atomic_json(manifest_path, manifest)
    return manifest


def balanced_plan(manifest: dict[str, Any], shard_count: int) -> dict[str, Any]:
    manifest = _validate_manifest(manifest, require_complete=True)
    if shard_count < 1:
        raise MeasurementError("shard count must be positive")
    if shard_count > len(manifest["inventory"]):
        raise MeasurementError("shard count exceeds measured module count")
    shards = [
        {"shard": number, "predicted_seconds": 0.0, "modules": []}
        for number in range(shard_count)
    ]
    for row in sorted(
        manifest["completed"], key=lambda item: (-item["seconds"], item["module"])
    ):
        shard = min(shards, key=lambda item: (item["predicted_seconds"], item["shard"]))
        shard["modules"].append(row["module"])
        shard["predicted_seconds"] = round(
            shard["predicted_seconds"] + row["seconds"], 2
        )
    return {
        "schema_version": 1,
        "kind": "longest_processing_time_shard_plan",
        "measurement_head": manifest["head"],
        "measurement_manifest_sha256": hashlib.sha256(
            _canonical_json_bytes(manifest)
        ).hexdigest(),
        "inventory_sha256": manifest["inventory_sha256"],
        "rule": (
            "descending module seconds, module-name tie; assign to lowest "
            "current seconds, shard-number tie"
        ),
        "scope": (
            "host-specific estimate for this exact measurement head and "
            "environment only; remeasure after test/source/environment changes"
        ),
        "shards": shards,
        "predicted_parallel_wall_seconds": max(
            shard["predicted_seconds"] for shard in shards
        ),
        "measured_serial_seconds": round(
            sum(row["seconds"] for row in manifest["completed"]), 2
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    measure_parser = commands.add_parser("measure")
    measure_parser.add_argument("--out-dir", type=Path, required=True)
    measure_parser.add_argument("--head", required=True)
    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("--measurement", type=Path, required=True)
    plan_parser.add_argument("--shards", type=int, required=True)
    plan_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        if args.command == "measure":
            manifest = measure(args.out_dir, args.head)
            print(
                f"measured {len(manifest['inventory'])} modules at {manifest['head']}"
            )
        else:
            manifest = load_measurement(args.measurement)
            plan = balanced_plan(manifest, args.shards)
            _atomic_json(args.out, plan)
            print(
                f"planned {sum(len(s['modules']) for s in plan['shards'])} modules "
                f"across {len(plan['shards'])} shards"
            )
    except MeasurementError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
