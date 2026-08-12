#!/usr/bin/env python3
"""The external verifier: a transition authority over pinned inputs.

Design: docs/DESIGN-external-verifier.md (committed before this file).

THE HONESTY BOUNDARY, verbatim from ROADMAP-v0.10 item 2: **a passing check
certifies what it checks, not correctness in general.** Every verdict this
module emits names the checks it ran; nothing downstream may read a PASS as
more than those checks passing over those exact bytes in that recorded
environment.

Two backends stand behind one interface:

* ``lean4`` — invokes the pinned toolchain's ``lean`` binary DIRECTLY BY PATH
  (never through the elan proxy), so an absent toolchain is a REFUSAL and can
  never become a network download. A PASS requires: exit 0, no warnings, and
  the ``#print axioms`` footprint of the claimed theorem contained in
  ``ALLOWED_AXIOMS`` — which is what catches a ``sorry`` (sorryAx) that the
  compiler alone would wave through with exit 0 plus a warning.
* ``python-tests`` — ``py_compile`` both pinned modules, ``mypy --strict``
  over them (offline, version recorded), then the pinned unit tests in a
  subprocess whose first act is installing a CPython audit hook that refuses
  sockets, subprocesses, and writes outside its sandbox directory
  (scripts/_verifier_sandbox.py). The hook is a DISCIPLINE boundary, not a
  security boundary — ctypes or a hostile C extension could evade it — and
  the verdict's checks list says exactly that.

A verdict is never a bare boolean: it is a committed JSON object recording
the claim, the checks run, every input's sha256, the environment, and the
outcome (``pass`` / ``fail`` / ``refused``). REFUSED means the check could
not run (missing toolchain, escaping path, unreadable input); FAIL means it
ran and did not pass. Verdict bytes are deterministic (LF, sorted keys, no
timestamps) so they can be committed and re-checked like every other ledger.

A verdict alone never mints a ``verified_by`` link. The corpus link
vocabulary is unchanged (``system: lean4`` with a traced transition-row
artifact, digest-pinned in prover/proof-artifact-manifest.json);
``verdict_ledger_errors`` is the fail-closed rung that re-checks the whole
chain — verdict shape, input digests, manifest pins, and that a PASS verdict
attaches to the statement it names and no other.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from proof_artifacts import (  # noqa: E402
    read_regular_file_once,
    resolve_contained_artifact,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_VERSION = 1
PASS = "pass"
FAIL = "fail"
REFUSED = "refused"
VERDICTS = (PASS, FAIL, REFUSED)

VERDICT_DIR = "prover/verifier-verdicts"
PROOF_MANIFEST = "prover/proof-artifact-manifest.json"

# The axiom footprint a lean4 PASS may carry. `decide` proofs land on
# {propext} or nothing; classical corpus proofs may add Classical.choice and
# Quot.sound. sorryAx is the load-bearing exclusion: a `sorry` elaborates
# with exit 0 and only a warning, so the compiler alone cannot be the
# authority — the axiom audit is.
ALLOWED_AXIOMS = frozenset({"propext", "Classical.choice", "Quot.sound"})

_AXIOM_LINE = re.compile(
    r"'(?P<name>[^']+)' (?:depends on axioms: \[(?P<axioms>[^\]]*)\]"
    r"|does not depend on any axioms)"
)


# --------------------------------------------------------------------------
# Verdict object
# --------------------------------------------------------------------------


@dataclass
class Verdict:
    backend: str
    claim: dict
    checks: list[str]
    inputs: dict[str, str]
    environment: dict[str, str]
    verdict: str
    evidence: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "backend": self.backend,
            "claim": self.claim,
            "checks": self.checks,
            "inputs": self.inputs,
            "environment": self.environment,
            "verdict": self.verdict,
            "evidence": self.evidence,
        }

    def to_bytes(self) -> bytes:
        """Deterministic bytes: LF, sorted keys, no timestamps."""
        return (
            json.dumps(
                self.as_dict(), ensure_ascii=False, indent=1, sort_keys=True
            )
            + "\n"
        ).encode("utf-8")


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _pin_inputs(repo_root: Path, names: list[str]) -> dict[str, str]:
    """sha256 every input by repository-relative name; ValueError refuses."""
    pins: dict[str, str] = {}
    for name in names:
        path = resolve_contained_artifact(repo_root, name)
        pins[name] = _digest(read_regular_file_once(path))
    return pins


def _refusal(backend: str, claim: dict, reason: str) -> Verdict:
    return Verdict(
        backend=backend,
        claim=claim,
        checks=[],
        inputs={},
        environment={"platform": sys.platform},
        verdict=REFUSED,
        evidence={"reason": reason},
    )


# --------------------------------------------------------------------------
# lean4 backend
# --------------------------------------------------------------------------


def toolchain_binary(toolchain: str) -> Path | None:
    """The installed toolchain's lean binary, or None. NEVER downloads."""
    mangled = toolchain.strip().replace("/", "--").replace(":", "---")
    binary = (
        Path.home()
        / ".elan"
        / "toolchains"
        / mangled
        / "bin"
        / ("lean.exe" if os.name == "nt" else "lean")
    )
    return binary if binary.is_file() else None


def check_lean4(
    repo_root: Path,
    source: str,
    statement_id: str,
    surface: str,
    reference: str,
) -> Verdict:
    """Adjudicate: does the pinned Lean source prove the claimed theorem?

    PASS certifies exactly: the pinned bytes elaborate under the pinned
    toolchain with exit 0 and no warnings; the claimed surface appears
    verbatim in the source as `reference`'s statement; and the audited axiom
    footprint of `reference` is inside ALLOWED_AXIOMS. Nothing more.
    """

    claim = {
        "statement_id": statement_id,
        "surface": surface,
        "reference": reference,
    }
    toolchain_name = str(Path(source).parent / "lean-toolchain").replace(
        "\\", "/"
    )
    try:
        inputs = _pin_inputs(repo_root, [source, toolchain_name])
    except ValueError as exc:
        return _refusal("lean4", claim, str(exc))

    source_path = resolve_contained_artifact(repo_root, source)
    source_text = read_regular_file_once(source_path).decode("utf-8")
    toolchain = (
        read_regular_file_once(
            resolve_contained_artifact(repo_root, toolchain_name)
        )
        .decode("utf-8")
        .strip()
    )
    binary = toolchain_binary(toolchain)
    if binary is None:
        return _refusal(
            "lean4",
            claim,
            f"toolchain {toolchain!r} is not installed; "
            "refusing to download (hermetic rule)",
        )

    checks = [
        "elaborates: pinned toolchain lean binary invoked directly by path "
        "(no elan proxy, no network), exit 0 required, warnings fail",
        "axiom audit: `#print axioms` footprint of the claimed reference "
        f"must be contained in {sorted(ALLOWED_AXIOMS)} (a `sorry` surfaces "
        "here as sorryAx even though the compiler exits 0)",
        "surface containment: the claimed statement appears verbatim in the "
        "pinned source as the claimed reference's declaration",
    ]

    declaration = f"theorem {reference} : {surface}"
    if declaration not in source_text:
        return Verdict(
            backend="lean4",
            claim=claim,
            checks=checks,
            inputs=inputs,
            environment={"toolchain": toolchain, "platform": sys.platform},
            verdict=FAIL,
            evidence={
                "reason": (
                    "surface containment failed: the pinned source does not "
                    f"declare {declaration!r}"
                )
            },
        )

    with tempfile.TemporaryDirectory() as scratch:
        completed = subprocess.run(
            [str(binary), str(source_path)],
            cwd=scratch,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        version = subprocess.run(
            [str(binary), "--version"],
            cwd=scratch,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).stdout.strip()

    output = (completed.stdout or "") + (completed.stderr or "")
    output = output.replace("\r\n", "\n")
    environment = {
        "toolchain": toolchain,
        "lean_version": version,
        "platform": sys.platform,
    }
    evidence: dict = {
        "exit_code": completed.returncode,
        "output_sha256": _digest(output.encode("utf-8")),
    }

    failures: list[str] = []
    if completed.returncode != 0:
        failures.append(f"lean exited {completed.returncode}")
    warned = [
        line for line in output.splitlines() if "warning:" in line.casefold()
    ]
    if warned:
        failures.append(f"lean warned: {warned[0].strip()}")

    audited: set[str] | None = None
    for match in _AXIOM_LINE.finditer(output):
        if match.group("name") == reference:
            raw = match.group("axioms")
            audited = (
                {a.strip() for a in raw.split(",") if a.strip()}
                if raw
                else set()
            )
    if audited is None:
        failures.append(
            f"axiom audit missing: no `#print axioms` output for {reference!r}"
        )
    else:
        evidence["axioms"] = sorted(audited)
        illegal = audited - ALLOWED_AXIOMS
        if illegal:
            failures.append(
                f"axiom audit failed: {sorted(illegal)} outside the allowed set"
            )

    if failures:
        evidence["reason"] = "; ".join(failures)
        if completed.returncode != 0:
            evidence["output_tail"] = output.strip().splitlines()[-8:]
    return Verdict(
        backend="lean4",
        claim=claim,
        checks=checks,
        inputs=inputs,
        environment=environment,
        verdict=FAIL if failures else PASS,
        evidence=evidence,
    )


# --------------------------------------------------------------------------
# python-tests backend
# --------------------------------------------------------------------------


def check_python_tests(
    repo_root: Path,
    candidate: str,
    tests: str,
    statement_id: str,
    surface: str,
) -> Verdict:
    """Adjudicate: does the pinned candidate pass its pinned typed tests?

    PASS certifies exactly: both pinned modules compile; both pass
    ``mypy --strict``; and the pinned tests pass under the sandboxed runner.
    The sandbox (scripts/_verifier_sandbox.py) refuses sockets, subprocesses
    and out-of-tree writes at the CPython audit-hook layer — a DISCIPLINE
    boundary, not a security boundary, and the checks list says so.
    """

    claim = {"statement_id": statement_id, "surface": surface}
    try:
        inputs = _pin_inputs(repo_root, [candidate, tests])
    except ValueError as exc:
        return _refusal("python-tests", claim, str(exc))

    candidate_path = resolve_contained_artifact(repo_root, candidate)
    tests_path = resolve_contained_artifact(repo_root, tests)
    sandbox_runner = Path(__file__).resolve().parent / "_verifier_sandbox.py"

    checks = [
        "compile: both pinned modules byte-compile",
        "types: mypy --strict over both pinned modules (offline)",
        "tests: pinned unittest module executed in a subprocess whose first "
        "act installs a CPython audit hook refusing sockets, subprocesses, "
        "and writes outside the sandbox directory (a discipline boundary, "
        "not a security boundary)",
    ]

    try:
        import mypy.version  # noqa: PLC0415

        mypy_version = mypy.version.__version__
    except Exception:
        return _refusal(
            "python-tests",
            claim,
            "mypy is not importable in this environment; the type-check "
            "stage cannot run and a partial authority must refuse, not "
            "silently narrow its claim",
        )

    environment = {
        "python": platform.python_version(),
        "mypy": mypy_version,
        "platform": sys.platform,
    }
    evidence: dict = {}
    failures: list[str] = []

    for name, path in ((candidate, candidate_path), (tests, tests_path)):
        try:
            compile(
                read_regular_file_once(path).decode("utf-8"), name, "exec"
            )
        except SyntaxError as exc:
            failures.append(f"compile failed for {name}: {exc}")

    stage_results: dict[str, int] = {}
    if not failures:
        with tempfile.TemporaryDirectory() as scratch:
            mypy_run = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "mypy",
                    "--strict",
                    "--no-error-summary",
                    "--cache-dir",
                    str(Path(scratch) / "mypy-cache"),
                    str(candidate_path),
                    str(tests_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stage_results["mypy"] = mypy_run.returncode
            if mypy_run.returncode != 0:
                failures.append(
                    "mypy --strict failed: "
                    + (mypy_run.stdout or mypy_run.stderr).strip()[:400]
                )
            test_run = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    str(sandbox_runner),
                    scratch,
                    str(candidate_path),
                    str(tests_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stage_results["tests"] = test_run.returncode
            test_output = (
                (test_run.stdout or "") + (test_run.stderr or "")
            ).replace("\r\n", "\n")
            evidence["tests_output_sha256"] = _digest(
                test_output.encode("utf-8")
            )
            if test_run.returncode != 0:
                failures.append(
                    "sandboxed tests failed: " + test_output.strip()[:400]
                )

    evidence["stages"] = stage_results
    if failures:
        evidence["reason"] = "; ".join(failures)
    return Verdict(
        backend="python-tests",
        claim=claim,
        checks=checks,
        inputs=inputs,
        environment=environment,
        verdict=FAIL if failures else PASS,
        evidence=evidence,
    )


# --------------------------------------------------------------------------
# The ledger rung: fail-closed re-check of every committed verdict
# --------------------------------------------------------------------------

_REQUIRED_VERDICT_FIELDS = (
    "schema_version",
    "backend",
    "claim",
    "checks",
    "inputs",
    "environment",
    "verdict",
    "evidence",
)


def load_verdict(repo_root: Path, name: str) -> dict:
    """Load and shape-check one committed verdict; ValueError fails closed."""
    path = resolve_contained_artifact(repo_root, name)
    try:
        verdict = json.loads(read_regular_file_once(path).decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"verdict {name} is not valid JSON: {exc}") from exc
    if not isinstance(verdict, dict):
        raise ValueError(f"verdict {name} must be a JSON object")
    missing = [f for f in _REQUIRED_VERDICT_FIELDS if f not in verdict]
    if missing:
        raise ValueError(f"verdict {name} is missing fields: {missing}")
    if verdict["verdict"] not in VERDICTS:
        raise ValueError(
            f"verdict {name} has unknown verdict {verdict['verdict']!r}"
        )
    if not isinstance(verdict["inputs"], dict) or not verdict["inputs"]:
        if verdict["verdict"] == PASS:
            raise ValueError(
                f"verdict {name}: a PASS with no pinned inputs certifies "
                "nothing and is refused"
            )
    if not isinstance(verdict["claim"], dict) or not verdict["claim"].get(
        "statement_id"
    ):
        raise ValueError(f"verdict {name} names no claim.statement_id")
    return verdict


def verdict_ledger_errors(
    repo_root: Path, nodes: list[dict] | None = None
) -> list[str]:
    """Every committed verdict and manifest chain re-checked, fail closed.

    Checks: (1) every verdict in prover/verifier-verdicts/ parses, is
    shape-complete, and every pinned input re-hashes to its recorded sha256;
    (2) every manifest artifact entry's sha256 matches the committed bytes;
    (3) every manifest `verdicts` reference names an existing PASS verdict;
    (4) a PASS verdict attaches only to the statement it names: if a node
    cites an artifact whose manifest entry carries verdicts, the verdict's
    claim.statement_id must equal that node's statement_id (the
    wrong-statement control — a passing check on the WRONG statement must
    not attach).
    """

    errors: list[str] = []
    verdicts: dict[str, dict] = {}
    verdict_dir = repo_root / VERDICT_DIR
    if verdict_dir.is_dir():
        for path in sorted(verdict_dir.glob("*.json")):
            name = f"{VERDICT_DIR}/{path.name}"
            try:
                verdict = load_verdict(repo_root, name)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            verdicts[name] = verdict
            for input_name, recorded in sorted(verdict["inputs"].items()):
                try:
                    resolved = resolve_contained_artifact(
                        repo_root, input_name
                    )
                    actual = _digest(read_regular_file_once(resolved))
                except ValueError as exc:
                    errors.append(f"{name}: input {input_name}: {exc}")
                    continue
                if actual != recorded:
                    errors.append(
                        f"{name}: input {input_name} re-hashes to {actual}, "
                        f"verdict pinned {recorded} — the pinned bytes moved"
                    )

    manifest_path = repo_root / PROOF_MANIFEST
    if not manifest_path.is_file():
        return errors
    try:
        manifest = json.loads(
            read_regular_file_once(manifest_path).decode("utf-8")
        )
        entries = manifest["artifacts"]
        if not isinstance(entries, dict):
            raise ValueError("artifacts must be an object")
    except (ValueError, KeyError) as exc:
        errors.append(f"{PROOF_MANIFEST} is unreadable: {exc}")
        return errors

    if nodes is None:
        nodes = []
        for path in sorted((repo_root / "data").glob("*/nodes.json")):
            corpus = json.loads(path.read_text(encoding="utf-8"))
            nodes.extend(corpus.get("statement_nodes", []))
    citers: dict[str, set[str]] = {}
    for node in nodes:
        for link in node.get("verified_by", []) or []:
            if isinstance(link, dict) and isinstance(
                link.get("artifact"), str
            ):
                citers.setdefault(link["artifact"], set()).add(
                    node.get("statement_id", "<unknown>")
                )

    for artifact, entry in sorted(entries.items()):
        if not isinstance(entry, dict):
            errors.append(f"{PROOF_MANIFEST}: entry {artifact} must be an object")
            continue
        try:
            resolved = resolve_contained_artifact(repo_root, artifact)
            actual = _digest(read_regular_file_once(resolved))
        except ValueError as exc:
            errors.append(f"{PROOF_MANIFEST}: {artifact}: {exc}")
            continue
        if actual != entry.get("sha256"):
            errors.append(
                f"{PROOF_MANIFEST}: {artifact} re-hashes to {actual}, "
                f"manifest pins {entry.get('sha256')}"
            )
        for verdict_name in entry.get("verdicts", []) or []:
            verdict = verdicts.get(verdict_name)
            if verdict is None:
                errors.append(
                    f"{PROOF_MANIFEST}: {artifact} cites verdict "
                    f"{verdict_name} which is absent or already invalid"
                )
                continue
            if verdict["verdict"] != PASS:
                errors.append(
                    f"{PROOF_MANIFEST}: {artifact} cites verdict "
                    f"{verdict_name} whose verdict is "
                    f"{verdict['verdict']!r}; only a PASS may back an "
                    "artifact"
                )
            claimed = verdict["claim"]["statement_id"]
            for citer in sorted(citers.get(artifact, set())):
                if citer != claimed:
                    errors.append(
                        f"{PROOF_MANIFEST}: {artifact} is cited by "
                        f"{citer} but its verdict {verdict_name} claims "
                        f"{claimed} — a passing check on the wrong "
                        "statement must not attach"
                    )
    return errors


# --------------------------------------------------------------------------
# recheck: re-run a committed verdict from its own record
# --------------------------------------------------------------------------


def recheck(repo_root: Path, verdict_name: str) -> tuple[bool, str]:
    """Re-run a committed verdict's check from its pinned record.

    Success requires: every pinned input re-hashes identically, AND a fresh
    run of the same backend over the same inputs lands on the same verdict.
    Environment differences are reported, not failed — a verdict is a record
    of ONE run; a re-run on another machine that flips the outcome is a
    divergence worth failing on, a different lean point-release that reaches
    the same outcome is not.
    """

    recorded = load_verdict(repo_root, verdict_name)
    for input_name, pinned in sorted(recorded["inputs"].items()):
        actual = _digest(
            read_regular_file_once(
                resolve_contained_artifact(repo_root, input_name)
            )
        )
        if actual != pinned:
            return False, (
                f"input {input_name} re-hashes to {actual}, verdict pinned "
                f"{pinned} — refusing to re-adjudicate moved bytes"
            )

    claim = recorded["claim"]
    if recorded["backend"] == "lean4":
        sources = [n for n in recorded["inputs"] if n.endswith(".lean")]
        if len(sources) != 1:
            return False, "lean4 verdict must pin exactly one .lean input"
        fresh = check_lean4(
            repo_root,
            sources[0],
            claim["statement_id"],
            claim["surface"],
            claim["reference"],
        )
    elif recorded["backend"] == "python-tests":
        pinned_inputs = sorted(recorded["inputs"])
        tests = [n for n in pinned_inputs if Path(n).name.startswith("test")]
        others = [n for n in pinned_inputs if n not in tests]
        if len(tests) != 1 or len(others) != 1:
            return False, (
                "python-tests verdict must pin exactly one candidate and "
                "one test module"
            )
        fresh = check_python_tests(
            repo_root, others[0], tests[0], claim["statement_id"],
            claim["surface"],
        )
    else:
        return False, f"unknown backend {recorded['backend']!r}"

    if fresh.verdict != recorded["verdict"]:
        return False, (
            f"re-run verdict {fresh.verdict!r} diverges from recorded "
            f"{recorded['verdict']!r}: "
            f"{fresh.evidence.get('reason', '<no reason>')}"
        )
    notes = []
    if fresh.environment != recorded["environment"]:
        notes.append(
            f"environment differs (recorded {recorded['environment']}, "
            f"re-run {fresh.environment}) — outcome identical"
        )
    return True, "; ".join(notes) or "re-run reproduced the recorded verdict"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def _write_verdict(verdict: Verdict, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(verdict.to_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    lean = sub.add_parser("check-lean4")
    lean.add_argument("--source", required=True)
    lean.add_argument("--statement-id", required=True)
    lean.add_argument("--surface", required=True)
    lean.add_argument("--reference", required=True)
    lean.add_argument("--write", type=Path)

    pytests = sub.add_parser("check-python")
    pytests.add_argument("--candidate", required=True)
    pytests.add_argument("--tests", required=True)
    pytests.add_argument("--statement-id", required=True)
    pytests.add_argument("--surface", required=True)
    pytests.add_argument("--write", type=Path)

    re_parser = sub.add_parser("recheck")
    re_parser.add_argument("verdict")

    sub.add_parser("ledger")

    args = parser.parse_args(argv)
    root = args.repo_root.resolve()

    if args.command == "check-lean4":
        verdict = check_lean4(
            root, args.source, args.statement_id, args.surface, args.reference
        )
    elif args.command == "check-python":
        verdict = check_python_tests(
            root, args.candidate, args.tests, args.statement_id, args.surface
        )
    elif args.command == "recheck":
        ok, detail = recheck(root, args.verdict)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        return 0 if ok else 1
    else:  # ledger
        errors = verdict_ledger_errors(root)
        for error in errors:
            print(f"ERROR: {error}")
        print(
            f"verdict ledger: {'FAIL' if errors else 'OK'} "
            f"({len(errors)} error(s))"
        )
        return 1 if errors else 0

    print(json.dumps(verdict.as_dict(), ensure_ascii=False, indent=1))
    if args.write:
        _write_verdict(verdict, args.write)
        print(f"verdict written to {args.write}")
    return 0 if verdict.verdict == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
