#!/usr/bin/env python3
"""Adjudicate ECHO's population and instrument construction before a draw."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import measure_realization as mr  # noqa: E402
import realization_lexicon as rlex  # noqa: E402
import foreign_voice_oracle as fvo  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PREREG = ROOT / "experiments" / "echo_prereg.json"
DEFAULT_OUT = ROOT / "experiments" / "echo_population_audit.json"


class AuditRefusal(RuntimeError):
    """The registered audit cannot run against this tree or output path."""


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AuditRefusal(f"{path}: expected a JSON object")
    return value


def group_manifest(patterns: list[str]) -> tuple[str, list[dict]]:
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(path for path in ROOT.glob(pattern) if path.is_file())
    if not paths:
        raise AuditRefusal(f"freeze group matched no files: {patterns!r}")
    rows = [
        {"path": path.relative_to(ROOT).as_posix(), "sha256_lf": sha256_lf(path)}
        for path in sorted(paths)
    ]
    payload = "\n".join(f"{row['path']}\0{row['sha256_lf']}" for row in rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), rows


def revalidate(prereg: dict) -> list[dict]:
    rows = []
    for name, spec in sorted(prereg["freeze_groups"].items()):
        observed, members = group_manifest(spec["patterns"])
        rows.append({"group": name, "expected": spec["expected_digest"],
                     "observed": observed, "agrees": observed == spec["expected_digest"],
                     "members": members})
    moved = [row["group"] for row in rows if not row["agrees"]]
    if moved:
        raise AuditRefusal("preregistration digest drift: " + ", ".join(moved))
    return rows


def import_closure(relative: str) -> list[str]:
    """Return repository-local Python imports reachable from ``relative``."""
    pending = [ROOT / relative]
    seen: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        if not path.is_file():
            raise AuditRefusal(f"instrument path does not exist: {path}")
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        candidates: set[Path] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_path = Path(*alias.name.split("."))
                    candidates.update((ROOT / f"{module_path}.py",
                                       ROOT / module_path / "__init__.py",
                                       ROOT / "scripts" / f"{module_path}.py"))
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if not node.module:
                        raise AuditRefusal(
                            f"unresolved relative import in {path.relative_to(ROOT)}"
                        )
                    base = path.parent
                    for _ in range(node.level - 1):
                        base = base.parent
                    candidates.add(base / (node.module.replace(".", "/") + ".py"))
                elif node.module:
                    module_path = Path(*node.module.split("."))
                    candidates.update((ROOT / f"{module_path}.py",
                                       ROOT / module_path / "__init__.py",
                                       ROOT / "scripts" / f"{module_path}.py"))
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else ""
                if name in {"__import__", "eval", "exec"}:
                    raise AuditRefusal(
                        f"dynamic import/code path {name} in {path.relative_to(ROOT)}"
                    )
                if (isinstance(node.func, ast.Attribute)
                        and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "importlib"
                        and node.func.attr == "import_module"):
                    raise AuditRefusal(
                        f"dynamic import path importlib.import_module in "
                        f"{path.relative_to(ROOT)}"
                    )
        for candidate in candidates:
            if candidate.is_file() and candidate not in seen:
                pending.append(candidate)
    return sorted(path.relative_to(ROOT).as_posix() for path in seen)


def checker_probe(relative: str, fixture_term: str | None) -> dict:
    """Classify whether a checker actually delegates to an external binary."""
    path = ROOT / relative
    if not path.is_file():
        raise AuditRefusal(f"checker path does not exist: {path}")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports_subprocess = any(
        isinstance(node, ast.Import)
        and any(alias.name == "subprocess" for alias in node.names)
        for node in ast.walk(tree)
    )
    calls_subprocess_run = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
        and node.func.attr == "run"
        for node in ast.walk(tree)
    )
    invokes_resolved_binary = any(
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
        and node.attr == "binary"
        for node in ast.walk(tree)
    )
    observed_external = all(
        (imports_subprocess, calls_subprocess_run, invokes_resolved_binary)
    )
    result = {
        "path": relative,
        "imports_subprocess": imports_subprocess,
        "calls_subprocess_run": calls_subprocess_run,
        "invokes_resolved_binary": invokes_resolved_binary,
        "observed_external": observed_external,
        "probe_attempted": False,
        "probe_success": False,
    }
    if observed_external:
        if not fixture_term:
            raise AuditRefusal(f"external checker {relative} has no frozen probe term")
        if relative != "scripts/foreign_voice_oracle.py":
            raise AuditRefusal(f"no registered construction probe for {relative}")
        oracle = fvo.load()
        answer = oracle.digest_of(fixture_term)
        result.update({
            "probe_attempted": True,
            "probe_success": bool(answer.ok and answer.digest),
            "probe_term": fixture_term,
            "probe_digest": answer.digest,
            "probe_error": answer.error,
            "binary": str(oracle.binary),
            "binary_sha256": hashlib.sha256(oracle.binary.read_bytes()).hexdigest(),
            "toolchain": oracle.toolchain,
            "serializer_sha256_lf": sha256_lf(oracle.serializer),
        })
    return result


def derive_gates(prereg: dict, observed: dict) -> tuple[list[dict], str]:
    predicted = prereg["predictions"]["population"]
    prediction_fired = all(observed[key] == predicted[key] for key in observed)
    instruments = prereg["instrument_map"]
    checks = []
    for name, row in sorted(instruments.items()):
        reader_closure = import_closure(row["reader_path"])
        renderer_closure = import_closure(row["renderer_path"])
        shared = sorted(set(reader_closure) & set(renderer_closure))
        checker = checker_probe(row["checker_path"], row["checker_probe_term"])
        checks.append({
            "stratum": name,
            "checker": checker,
            "checker_external_expected": bool(row["checker_external"]),
            "checker_expectation_agrees": (
                checker["observed_external"] == bool(row["checker_external"])
            ),
            "reader_closure": reader_closure,
            "reader_lexicon": row["reader_lexicon"],
            "renderer_closure": renderer_closure,
            "shared_reader_renderer_modules": shared,
        })

    b1 = "FIRES" if prediction_fired and not observed["resolver_keys_are_an_addend"] else "MISSES"
    b3 = "FIRES" if all(
        row["checker"]["observed_external"]
        and row["checker"]["probe_success"]
        and row["checker_expectation_agrees"] for row in checks
    ) else "MISSES"
    b4 = "FIRES" if all(not row["shared_reader_renderer_modules"] for row in checks) else "MISSES"
    findings = [
        {"gate": "B1", "verdict": b1,
         "evidence": {"observed": observed, "prediction_fired": prediction_fired,
                      "object_types": {"native": "statement_id",
                                       "second": "statement_id",
                                       "resolver_fixture": "question_id (reported separately)"}}},
        {"gate": "B3", "verdict": b3, "per_stratum": checks},
        {"gate": "B4", "verdict": b4, "per_stratum": checks},
    ]
    final = "PROCEED_TO_PILOT" if all(row["verdict"] == "FIRES" for row in findings) else "STOP_BEFORE_PILOT"
    if not prediction_fired:
        final = "PREREGISTRATION_DISCREPANCY"
    return findings, final


def registration_commit() -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout.strip()
    if status:
        raise AuditRefusal("the registered audit runs only from a clean tree")
    commits = []
    for relative in ("experiments/echo_prereg.json",
                     "scripts/echo_population_audit.py", "scripts/echo_reparse.py"):
        commit = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", relative], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout.strip()
        if not commit:
            raise AuditRefusal(f"registration input is not committed: {relative}")
        commits.append(commit)
    if len(set(commits)) != 1:
        raise AuditRefusal("preregistration and its instruments were not committed together")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", check=True,
    ).stdout.strip()
    if head != commits[0]:
        raise AuditRefusal("the audit must run at the clean registration commit")
    return head


def audit() -> dict:
    commit = registration_commit()
    prereg = _load_object(PREREG)
    pins = revalidate(prereg)
    native = mr.measure(ROOT / "data", rlex.load())
    native_ids = {row[0] for row in native["served"]}
    second = _load_object(ROOT / "experiments" / "foreign_voice_rate2.json")
    second_ids = {row["statement_id"] for row in second["b1"]["receipts"]}
    plain = _load_object(ROOT / "experiments" / "plain_input_corpus_seal.json")
    resolver = plain["denominators"]["resolver_found_before_the_proposer_is_consulted"]["question_ids"]
    questions = _load_object(ROOT / "experiments" / "plain_question_set.json")
    question_ids = {row["question_id"] for row in questions["questions"]}
    resolver_are_prompt_keys = set(resolver) <= question_ids
    resolver_overlap_statements = set(resolver) & (native_ids | second_ids)
    resolver_keys_are_unique = len(resolver) == len(set(resolver))
    observed = {
        "native_served": len(native_ids),
        "resolver_found_fixture_keys": len(set(resolver)),
        "resolver_keys_are_an_addend": bool(
            not resolver_are_prompt_keys
            or not resolver_keys_are_unique
            or resolver_overlap_statements
        ),
        "second_voice_served": len(second_ids),
        "statement_id_overlap": len(native_ids & second_ids),
        "statement_id_union": len(native_ids | second_ids),
    }
    findings, gate = derive_gates(prereg, observed)
    return {
        "audit_id": "echo.population-audit.v1",
        "construction_gate": gate,
        "design": "docs/DESIGN-echo.md",
        "findings": findings,
        "non_claim": "No ECHO recovery, collision, or injectivity result exists.",
        "observed": observed,
        "pins": pins,
        "pilot_registered": 50,
        "pilot_rendered": 0,
        "preregistration": "experiments/echo_prereg.json",
        "preregistration_sha256": sha256_lf(PREREG),
        "registered_run_registered": 500,
        "registered_run_rendered": 0,
        "registration_commit": commit,
        "next_move": prereg["predictions"]["construction_gate"]["legal_next_move"],
    }


def write_once(path: Path, value: dict) -> None:
    """Create ``path`` atomically; an existing artifact is never replaced."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temp.exists():
        raise AuditRefusal(f"temporary output already exists: {temp}")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=1, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp, path)
        except FileExistsError as exc:
            raise AuditRefusal(f"registered artifact already exists: {path}") from exc
    finally:
        temp.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write-registered-audit", action="store_true")
    args = parser.parse_args(argv)
    if not args.write_registered_audit:
        parser.error("the once-only audit requires --write-registered-audit")
    result = audit()
    write_once(DEFAULT_OUT, result)
    print(json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True))
    return 2 if result["construction_gate"] != "PROCEED_TO_PILOT" else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
