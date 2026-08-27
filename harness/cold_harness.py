#!/usr/bin/env python3
"""COLD RECEIPT's harness: does the program's evidence survive its deletion?

`docs/DESIGN-cold-receipt.md` §6 is the recipe, and this file is that recipe
executed. It is **harness code, not program code**: it lives outside
`scripts/` because `scripts/` is what it renames away, and it imports nothing
from this repository. Stdlib only — the harness does not depend on the
repository's `.venv` being blessed, and its subprocesses run the **base**
interpreter under `-S -I` so that no `site-packages` under the repository root
is ever on their path.

§6 says out loud that this is **weaker than a container**, and why: the C-E3
supplement pins `binary_sha256` over a Windows `lean.exe` and the three
`lean4` verdicts record `"platform": "win32"`, so a Linux container would
re-check *different receipts*, not these ones more coldly. What this harness
does NOT exclude is named in `recipe.json` rather than left for a reader to
find: the Windows registry, `%USERPROFILE%` (and therefore `~/.elan`),
`.runtime/`, any system-wide Python and its `site-packages`, every ambient DLL
search path, and the harness's own interpreter.

Every `SURVIVES` this harness publishes is scoped to that weaker exclusion.
The scope travels with the number.

Arms (§7), each recorded whichever way it reads:

- **B3 tamper**, 3 mutations that differ *in kind* — content, digest, binding
  — each carrying a witness of difference, 100% must FAIL.
- **B4 omission**, a listed dependency removed: must FAIL LOUD naming it. A
  silent pass voids **the harness**, not the kind.
- **B5 sham**, every adjudicating dependency replaced by an accept-all stub,
  run against both a good and a known-bad bundle. Any kind still reading
  SURVIVES fires the voiding sentence for every kind in this census.
- **B6 scramble**, 200 seeded bundles, the vacuity control. Budgeted in §7 at
  roughly an hour per checker-invoking kind, with the overrun published as a
  finding if a single kind exceeds 90 minutes.
- **B7 removal**, every NEEDS-PROGRAM confirmed by removal rather than
  declared.

Usage
-----

    python harness/cold_harness.py --out-dir cold
    python harness/cold_harness.py --out-dir cold --scramble-bundles 0
    python harness/cold_harness.py --restore-only
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "harness"

PROGRAM_TREE = REPO / "scripts"
RENAMED_TREE = REPO / "scripts.renamed-away-by-cold-harness"

CENSUS_PATH = REPO / "experiments" / "cold_registry_census.json"
RULE_PATH = REPO / "cold" / "reconstruction_rule.json"
SUPPLEMENT_PATH = REPO / "experiments" / "conformance_ce3_supplement.json"

#: The one kind for which CR-P1 published a reconstruction rule, and therefore
#: the one this harness can execute program-absent. Every other kind reads its
#: verdict from the removal arm or from UNTESTED — never from a declaration.
EXECUTABLE_KIND = "conformance_ce3_supplement:decide_both_directions"

#: Trees excluded from the working-tree digest §6 requires be taken before and
#: after the rename. `cold/` is excluded because this harness writes it.
TREE_DIGEST_EXCLUDED = {
    ".git",
    ".venv",
    ".worktrees",
    "cold",
    RENAMED_TREE.name,
}

B6_BUDGET_SECONDS = 90 * 60


# --------------------------------------------------------------------------
# Small utilities (stdlib only, on purpose)
# --------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def provenance_block(writer: Path, inputs: list[Path]) -> dict:
    """`report_provenance.provenance_block`'s shape, reimplemented here.

    Not imported: `scripts/report_provenance.py` is program code, and the
    harness imports nothing from this repository — that is the point of the
    whole item. The shape is `PROVENANCED_LEDGERS`' shape, so the guard that
    scores it scores this artifact the same way it scores every other ledger.
    """

    rows = [
        {
            "path": path.resolve().relative_to(REPO).as_posix(),
            "sha256_lf": sha256_lf(path),
        }
        for path in inputs
        if path.is_file()
    ]
    rows.sort(key=lambda row: row["path"])
    return {
        "writer": writer.resolve().relative_to(REPO).as_posix(),
        "writer_sha256_lf": sha256_lf(writer),
        "inputs": rows,
        "emitted_at_generation": True,
    }


def working_tree_digest(root: Path) -> dict[str, Any]:
    """A recursive digest of the tree the rename mutates.

    §6's C4: `write_stage`'s own `working_tree_byte_identity` check cannot run
    after the rename, because it lives under `scripts/`. So the harness takes
    its own, before and after, and a mismatch is a harness failure reported as
    such — never absorbed.
    """

    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in TREE_DIGEST_EXCLUDED:
            continue
        if not path.is_file():
            continue
        entries.append(f"{relative.as_posix()}:{sha256_file(path)}")
    return {
        "files": len(entries),
        "digest": hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest(),
        "excluded_top_level": sorted(TREE_DIGEST_EXCLUDED),
    }


def base_interpreter() -> dict[str, Any]:
    """The interpreter the subprocesses run, chosen to sit outside the repo.

    §6's H3 names the harness's own interpreter as something this harness does
    NOT exclude. It can at least decline to use the repository's own
    virtualenv: `sys.base_prefix` points at the interpreter the venv was built
    from, which lives outside the repository root, and `-S -I` keeps every
    `site-packages` off the child's path.
    """

    candidate = Path(sys.base_prefix) / (
        "python.exe" if os.name == "nt" else "bin/python3"
    )
    if candidate.is_file():
        return {
            "executable": str(candidate),
            "source": "sys.base_prefix",
            "inside_repository": _inside(candidate, REPO),
        }
    return {
        "executable": sys.executable,
        "source": "sys.executable (base_prefix interpreter not found)",
        "inside_repository": _inside(Path(sys.executable), REPO),
    }


def redact(value: Any) -> Any:
    """Home- and repo-relative spellings, everywhere in the published evidence.

    R5 forbids anything in a committed artifact that differs between two
    checkouts of the same bytes, and this harness's evidence is made of
    resolved paths. Rewriting them to `~` and `<repo>` keeps every fact the
    audit needs — which directory, which binary, whether it lay inside the
    repository — and drops the one thing that is nobody's business.
    """

    home = str(Path.home())
    repo = str(REPO)
    if isinstance(value, str):
        out = value.replace(repo, "<repo>").replace(home, "~")
        return out.replace(repo.replace("\\", "\\\\"), "<repo>").replace(
            home.replace("\\", "\\\\"), "~"
        )
    if isinstance(value, dict):
        return {redact(k): redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def _inside(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def constructed_env(dependency_dirs: list[Path], cwd: Path) -> dict[str, str]:
    """§6's constructed environment: PATH reduced to listed dependency dirs.

    `PYTHONPATH` empty, `PYTHONHOME` unset, `PYTHONNOUSERSITE` set. What is
    kept is kept deliberately and listed in `recipe.json`: `SYSTEMROOT` and
    `COMSPEC` because Windows process creation needs them, `TEMP`/`TMP`
    because the procedure writes its probe to a temporary directory, and
    `USERPROFILE`, which §11's L3 records as *not* cleared — `Path.home()`
    reads it, and a reduced `PATH` is irrelevant to that.
    """

    env = {
        "PATH": os.pathsep.join(str(d) for d in dependency_dirs),
        "PYTHONPATH": "",
        "PYTHONNOUSERSITE": "1",
        "PYTHONIOENCODING": "utf-8",
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", ""),
        "TEMP": str(cwd / "_tmp"),
        "TMP": str(cwd / "_tmp"),
        "USERPROFILE": os.environ.get("USERPROFILE", ""),
        "HOMEDRIVE": os.environ.get("HOMEDRIVE", ""),
        "HOMEPATH": os.environ.get("HOMEPATH", ""),
    }
    return {k: v for k, v in env.items() if v != ""} | {"PYTHONPATH": ""}


def run(argv: list[str], env: dict[str, str], cwd: Path, timeout: int = 3600):
    return subprocess.run(
        argv,
        env=env,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


# --------------------------------------------------------------------------
# The bundle
# --------------------------------------------------------------------------


def build_bundle(root: Path, receipts: dict, rule: dict, census: dict) -> dict:
    """Copy the files the kind's receipt names, outside the repository."""

    root.mkdir(parents=True, exist_ok=True)
    (root / "_tmp").mkdir(exist_ok=True)
    (root / "receipts.json").write_text(
        json.dumps(receipts, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (root / "reconstruction_rule.json").write_text(
        json.dumps(rule, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (root / "census.json").write_text(
        json.dumps(census, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    manifest = []
    for name in ("receipts.json", "reconstruction_rule.json", "census.json"):
        path = root / name
        manifest.append(
            {
                "path": name,
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    (root / "bundle_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return {"root": str(root), "files": manifest}


# --------------------------------------------------------------------------
# B3's three mutations, each different in kind, each with a witness
# --------------------------------------------------------------------------


def mutate(receipts: dict, mutation: str) -> tuple[dict, dict]:
    """Return (mutated receipts, witness of difference).

    §10's B3 row: *"each mutation provably changes an input the procedure
    reads, and a mutation without a witness of difference is discarded and
    counted before any rate."* The witness names the field and shows the two
    values, so the discard rule is checkable rather than asserted.
    """

    out = copy.deepcopy(receipts)
    rows = [row for row in out["rows"] if "checker_receipt" in row]

    if mutation == "content":
        # Flip one character of a bundled artifact the receipt covers. The
        # recorded digest is left alone, so step 3 must catch it.
        before = rows[0]["substituted_proposition"]
        after = before.replace("3", "5", 1)
        rows[0]["substituted_proposition"] = after
        witness = {
            "mutation": "content",
            "differs_in_kind_from": "digest, binding",
            "field": "rows[0].substituted_proposition",
            "before": before[:96],
            "after": after[:96],
            "changed": before != after,
            "input_the_procedure_reads": "step 1 takes this field verbatim",
        }

    elif mutation == "digest":
        # Change the recorded digest to match a tampered artifact, so a
        # checker comparing only a file to its own recorded hash passes. The
        # replacement proposition is one the checker decides the OTHER way, so
        # step 4's exit-code comparison is the only thing left to catch it.
        replacement = "((1 : Nat) >= (0 : Nat))"
        before = rows[0]["substituted_proposition"]
        rows[0]["substituted_proposition"] = replacement
        positive = f"example : ({replacement} : Prop) := by decide\n"
        negative = f"example : (¬({replacement}) : Prop) := by decide\n"
        receipt = rows[0]["checker_receipt"]
        recorded_before = receipt["positive_probe"]["source_sha256"]
        receipt["positive_probe"]["source_sha256"] = hashlib.sha256(
            positive.encode("utf-8")
        ).hexdigest()
        receipt["negative_probe"]["source_sha256"] = hashlib.sha256(
            negative.encode("utf-8")
        ).hexdigest()
        witness = {
            "mutation": "digest",
            "differs_in_kind_from": "content, binding",
            "field": "rows[0].substituted_proposition + its recorded digests",
            "before": before[:96],
            "after": replacement,
            "recorded_digest_before": recorded_before,
            "recorded_digest_after": receipt["positive_probe"]["source_sha256"],
            "changed": before != replacement,
            "input_the_procedure_reads": (
                "step 3 is made to agree by construction; only step 4's "
                "exit-code comparison can still catch this one, because the "
                "replacement proposition is TRUE where the original was false"
            ),
        }

    elif mutation == "binding":
        # Swap two records between receipts, leaving every file and digest
        # internally consistent and the ATTRIBUTION wrong — the one a
        # presence-check cannot catch.
        first, second = rows[0]["checker_receipt"], rows[1]["checker_receipt"]
        rows[0]["checker_receipt"], rows[1]["checker_receipt"] = second, first
        witness = {
            "mutation": "binding",
            "differs_in_kind_from": "content, digest",
            "field": "rows[0].checker_receipt <-> rows[1].checker_receipt",
            "before": rows[1]["checker_receipt"]["positive_probe"][
                "source_sha256"
            ],
            "after": rows[0]["checker_receipt"]["positive_probe"][
                "source_sha256"
            ],
            "changed": (
                rows[0]["checker_receipt"]["positive_probe"]["source_sha256"]
                != rows[1]["checker_receipt"]["positive_probe"]["source_sha256"]
            ),
            "input_the_procedure_reads": (
                "every file and every digest stays internally consistent; only "
                "the pairing of a proposition to its receipt is wrong"
            ),
        }
    else:  # pragma: no cover - the three are the whole vocabulary
        raise ValueError(mutation)

    return out, witness


def scramble(receipts: dict, seed: int) -> tuple[dict, dict]:
    """B6's seeded scramble, exactly the rule CR-P0 committed.

    *"reassign one kind's artifacts across that kind's own records, preserving
    every file and every digest field's shape."* The identity permutation is
    redrawn rather than counted: it is not a wrong bundle, it is the right
    one, and letting it through would price the control as chance when it was
    a reproduction.
    """

    out = copy.deepcopy(receipts)
    indices = [i for i, row in enumerate(out["rows"]) if "checker_receipt" in row]
    rng = random.Random(seed)
    redraws = 0
    order = list(indices)
    while True:
        rng.shuffle(order)
        if order != indices:
            break
        redraws += 1
    receipts_by_index = {
        i: copy.deepcopy(out["rows"][i]["checker_receipt"]) for i in indices
    }
    for target, source in zip(indices, order):
        out["rows"][target]["checker_receipt"] = receipts_by_index[source]
    return out, {"seed": seed, "identity_redraws": redraws, "permutation": order}


# --------------------------------------------------------------------------
# The runs
# --------------------------------------------------------------------------


class Runner:
    def __init__(self, workspace: Path, checker: Path, verbose: bool = False):
        self.workspace = workspace
        self.checker = checker
        self.verbose = verbose
        self.interpreter = base_interpreter()
        self.dependency_dirs = [checker.parent, Path(self.interpreter["executable"]).parent]

    def recheck(
        self,
        bundle: Path,
        checker_argv: list[str],
        out: Path,
        digests_only: bool = False,
    ) -> dict:
        env = constructed_env(self.dependency_dirs, bundle)
        argv = [
            self.interpreter["executable"],
            "-S",
            "-I",
            str(HARNESS / "probe_recheck.py"),
            "--bundle",
            str(bundle),
            "--checker-argv",
            json.dumps(checker_argv),
            "--out",
            str(out),
        ]
        if digests_only:
            argv.append("--digests-only")
        completed = run(argv, env, bundle)
        report = {}
        if out.is_file():
            report = json.loads(out.read_text(encoding="utf-8"))
        return {
            "argv": argv,
            "exit_code": completed.returncode,
            "stdout_head": completed.stdout.strip()[:400],
            "stderr_head": completed.stderr.strip()[:400],
            "report": report,
        }

    def import_program_module(self, module: str, cwd: Path) -> dict:
        """B7's removal confirmation, run rather than declared."""

        env = constructed_env(self.dependency_dirs, cwd)
        argv = [
            self.interpreter["executable"],
            "-S",
            "-I",
            "-c",
            f"import {module}",
        ]
        completed = run(argv, env, cwd, timeout=120)
        return {
            "argv": argv,
            "exit_code": completed.returncode,
            "stderr_head": completed.stderr.strip()[-400:],
            "import_succeeded": completed.returncode == 0,
        }


# --------------------------------------------------------------------------
# B11: the two tags, assigned where §8 says they are assigned
# --------------------------------------------------------------------------


def assign_provenance(
    dep: dict, resolved_sha256: str | None
) -> dict:
    """§8's test on the BYTES, assigned by the HARNESS from the bytes.

    `third_party_pinned` **iff both** hold: (a) the census pins the dependency
    by a digest **of the artifact that executes**, and (b) the pin identifies a
    third party's published release. The harness runs the test from
    `pin_hash` and the resolved path, and reads no declaration while doing it.
    """

    pin = dep.get("pin_hash")
    pins_the_executing_artifact = bool(
        pin
        and resolved_sha256
        and pin == resolved_sha256
        and (dep.get("pin_is_over") or "").startswith(
            "the executing binary's own bytes"
        )
    )
    toolchain = dep.get("toolchain") or ""
    names_a_third_party_release = "/" in toolchain and ":" in toolchain
    tag = (
        "third_party_pinned"
        if pins_the_executing_artifact and names_a_third_party_release
        else "program_configured"
    )
    return {
        "provenance": tag,
        "provenance_test": {
            "a_pin_is_over_the_executing_artifact": pins_the_executing_artifact,
            "b_pin_identifies_a_third_partys_release": names_a_third_party_release,
            "recomputed_sha256": resolved_sha256,
            "assigner": "the harness, from the bytes",
        },
        "selection_provenance": dep.get("selection_provenance"),
        "selection_provenance_assigner": "CR-P0",
        "b11_note": (
            "B11 downgrades on `provenance`, never on `selection_provenance`: "
            "§8 split the draft's single tag because lean.exe satisfied both "
            "values of it"
        ),
    }


# --------------------------------------------------------------------------
# The census run
# --------------------------------------------------------------------------


def build_cold_census(args, state: dict) -> dict:
    census = state["census"]
    kinds = []
    for record in census["kinds"]:
        kinds.append(state["verdicts"][record["kind_id"]])

    survives = [k for k in kinds if k["verdict"] == "SURVIVES"]
    needs = [k for k in kinds if k["verdict"] == "NEEDS-PROGRAM"]
    untested = [k for k in kinds if k["verdict"] == "UNTESTED"]

    denominator = len(kinds)
    survives_fraction = len(survives) / denominator if denominator else 0.0

    gate = {
        "B1": {
            "clause": "unmapped emitting routes = 0",
            "value": census["stop_clause"]["b1_unmapped_emitting_routes"],
            "green": census["stop_clause"]["b1_unmapped_emitting_routes"] == 0,
        },
        "B2": {
            "clause": ">=1 kind SURVIVES",
            "value": len(survives),
            "green": len(survives) >= 1,
            "kinds": [k["kind_id"] for k in survives],
        },
        "B3": state["arms"]["tamper"]["gate"],
        "B4": state["arms"]["omission"]["gate"],
        "B5": state["arms"]["sham"]["gate"],
        "B6": state["arms"]["scramble"]["gate"],
        "B7": {
            "clause": "100% NEEDS-PROGRAM carry confirmed_by_removal",
            "value": sum(
                1
                for k in needs
                if k.get("blocking_dependency", {}).get("confirmed_by_removal")
            ),
            "denominator": len(needs),
            "green": all(
                k.get("blocking_dependency", {}).get("confirmed_by_removal")
                for k in needs
            ),
            "note": (
                "a correct NEEDS-PROGRAM scores as a hit, so the instrument has "
                "no incentive to over-read SURVIVES"
            ),
        },
        "B8": {
            "clause": (
                ">=90% SURVIVES on first run voids pending re-execution under a "
                "path_audit carrying BOTH of §6's assertions (DELTA on the "
                "draft's empty-PATH remedy, C2)"
            ),
            "survives_fraction": round(survives_fraction, 4),
            "denominator": denominator,
            "applies": denominator >= 5,
            "denominator_note": (
                "M6: the clause applies only at >=5 kinds; below that a single "
                "SURVIVES would trip a percentage that means nothing, and B2's "
                "floor of one must never be what fires B8"
            ),
            "green": not (denominator >= 5 and survives_fraction >= 0.9),
        },
        "B9": {
            "clause": "version drift ceded to the pin audit, reference only",
            "green": True,
            "pin_divergence": census["pin_divergence"],
            "note": (
                "§4: the cession is a DEFERRAL to a lane that is not running "
                "(RATCHET's pin audit is parked), not a hand-off to an "
                "instrument that will adjudicate it"
            ),
        },
        "B10": {
            "clause": "census_seal fixed before the harness runs",
            "seal": census["census_seal"],
            "sealed_at_commit": state["census_commit"],
            "harness_first_commit": state["harness_commit"],
            "harness_files_at_the_census_commit": state[
                "harness_files_at_census_commit"
            ],
            "how_checked": (
                "at the commit that sealed the census, no file under harness/ "
                "existed — the WITNESS W0 ordering made checkable in history"
            ),
            "green": state["seal_predates_harness"],
            "census_misses": state["census_misses"],
        },
        "B11": state["arms"]["provenance"]["gate"],
    }

    voiding_fired = not state["arms"]["sham"]["gate"]["green"]

    return {
        "schema": "cold-census/1",
        "design": "docs/DESIGN-cold-receipt.md",
        "run": state["run_metadata"],
        "scope": state["scope"],
        "census_seal": census["census_seal"],
        "pin_table_ref": {
            "artifact": "experiments/cold_registry_census.json",
            "field": "pin_table",
            "note": (
                "DELTA (H1): the draft's pin_audit_ref splits into this "
                "reference-only pointer and pin_divergence[]; neither is a "
                "verdict input"
            ),
        },
        "pin_divergence": census["pin_divergence"],
        "counts": {
            "kinds": denominator,
            "SURVIVES": len(survives),
            "NEEDS-PROGRAM": len(needs),
            "UNTESTED": len(untested),
        },
        "gate": gate,
        "voiding_sentence": {
            "text": (
                "If any receipt kind is annotated SURVIVES while the pinned "
                "checker is replaced by the accept-all stub, the harness is "
                "measuring bundle presence rather than verification, and the "
                "claim is void for every kind in this census"
            ),
            "fired": voiding_fired,
        },
        "kinds": kinds,
        "arms": state["arms"],
        "path_audit_ref": "cold/path_audit.txt",
        "scramble_baseline_ref": "cold/scramble_baseline.json",
        "reconstruction_rule_ref": "cold/reconstruction_rule.json",
    }


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0915
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=REPO / "cold")
    parser.add_argument("--scramble-bundles", type=int, default=200)
    parser.add_argument("--bundle-root", type=Path, default=None)
    parser.add_argument("--restore-only", action="store_true")
    args = parser.parse_args(argv)

    if args.restore_only:
        if RENAMED_TREE.is_dir() and not PROGRAM_TREE.exists():
            RENAMED_TREE.rename(PROGRAM_TREE)
            print("restored", PROGRAM_TREE)
            return 0
        print("nothing to restore")
        return 0

    # Absolute, because every path here is handed to a subprocess whose cwd is
    # the bundle and not the repository. A relative --out-dir would have the
    # child resolve it against the bundle root.
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence = out_dir / "evidence"
    evidence.mkdir(exist_ok=True)

    census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
    rule = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    receipts = json.loads(SUPPLEMENT_PATH.read_text(encoding="utf-8"))

    checker_pin = rule["checker_pin"]
    checker = Path(
        str(checker_pin["binary"]).replace("~", str(Path.home()), 1)
    )

    bundle_root = args.bundle_root or Path(
        tempfile.mkdtemp(prefix="cold-receipt-")
    )
    bundle_root.mkdir(parents=True, exist_ok=True)

    runner = Runner(bundle_root, checker)
    started_wall = time.time()

    good = build_bundle(bundle_root / "good", receipts, rule, census)
    bad_receipts, bad_witness = mutate(receipts, "content")
    bad = build_bundle(bundle_root / "known_bad", bad_receipts, rule, census)
    empty_deps = bundle_root / "emptied_deps"
    empty_deps.mkdir(exist_ok=True)

    real_argv = [str(checker)]
    sham_argv = [
        runner.interpreter["executable"],
        "-S",
        "-I",
        str(HARNESS / "sham_lean.py"),
    ]

    before = working_tree_digest(REPO)

    state: dict[str, Any] = {
        "census": census,
        "verdicts": {},
        "arms": {},
        "census_misses": [],
    }

    if PROGRAM_TREE.exists():
        PROGRAM_TREE.rename(RENAMED_TREE)
    try:
        # -- path_audit, both assertions ---------------------------------
        audit_out = evidence / "path_audit.json"
        env = constructed_env(runner.dependency_dirs, bundle_root / "good")
        audit_argv = [
            runner.interpreter["executable"],
            "-S",
            "-I",
            str(HARNESS / "path_probe.py"),
            "--repo-root",
            str(REPO),
            "--program-module",
            "serve_chat",
            "--program-module",
            "harness",
            "--program-module",
            "session_ledger",
            "--dependency",
            f"lean.exe={checker}",
            "--dependency",
            f"interpreter={runner.interpreter['executable']}",
            "--out",
            str(audit_out),
        ]
        audit_run = run(audit_argv, env, bundle_root / "good", timeout=600)
        path_audit = json.loads(audit_out.read_text(encoding="utf-8"))
        path_audit["harness_argv"] = audit_argv
        path_audit["harness_exit_code"] = audit_run.returncode
        path_audit["program_tree_renamed_to"] = RENAMED_TREE.name
        path_audit["program_tree_exists"] = PROGRAM_TREE.exists()

        # -- the main per-kind run ---------------------------------------
        deps_for_kind = census["external_deps_seed"]
        lean_dep = next(d for d in deps_for_kind if d["name"] == "lean.exe")
        lean_sha = sha256_file(checker) if checker.is_file() else None
        lean_tags = assign_provenance(lean_dep, lean_sha)

        main_report_path = evidence / "recheck_good.json"
        main_run = runner.recheck(
            bundle_root / "good", real_argv, main_report_path
        )

        for record in census["kinds"]:
            kind_id = record["kind_id"]
            declared = record["declared_recheck_procedure"]["type"]
            entry: dict[str, Any] = {
                "kind_id": kind_id,
                "emitting_routes": record["emitting_routes"],
                "declared_recheck_procedure": record[
                    "declared_recheck_procedure"
                ],
                "canonicalization_is_program_defined": record[
                    "canonicalization_is_program_defined"
                ],
                "bundle_manifest": [],
                "external_deps": [],
                "tamper_result": {
                    "verdict": "UNTESTED",
                    "reason": "no executable recheck procedure to tamper with",
                },
                "omission_result": {
                    "verdict": "UNTESTED",
                    "reason": "no removable dependency: the procedure invokes none",
                },
                "sham_result": {
                    "verdict": "UNTESTED",
                    "reason": "no adjudicating dependency to replace",
                },
            }

            if kind_id == EXECUTABLE_KIND and declared == "raw_checker_invocation":
                report = main_run["report"]
                survived = report.get("outcome") == "PASS"
                entry["executed_recheck_procedure"] = "raw_checker_invocation"
                entry["executor"] = "harness/probe_recheck.py"
                entry["bundle_manifest"] = good["files"]
                entry["external_deps"] = [
                    {
                        "name": "lean.exe",
                        "pin_hash": lean_dep["pin_hash"],
                        "role": lean_dep["role"],
                        "adjudicating": True,
                        **lean_tags,
                    }
                ]
                downgraded = any(
                    d["adjudicating"] and d["provenance"] == "program_configured"
                    for d in entry["external_deps"]
                )
                entry["verdict"] = (
                    "UNTESTED"
                    if (survived and downgraded)
                    else ("SURVIVES" if survived else "NEEDS-PROGRAM")
                )
                entry["b11_downgrade_applied"] = bool(survived and downgraded)
                entry["verdict_evidence"] = {
                    "argv": main_run["argv"],
                    "exit_code": main_run["exit_code"],
                    "stdout_head": main_run["stdout_head"],
                    "rows_ok": report.get("rows_ok"),
                    "rows_evaluated": report.get("rows_evaluated"),
                    "checker_invocations": report.get("checker_invocations"),
                    "elapsed_seconds": report.get("elapsed_seconds"),
                    "evidence_file": "cold/evidence/recheck_good.json",
                }
                if not survived:
                    entry["blocking_dependency"] = {
                        "name": "unknown",
                        "confirmed_by_removal": False,
                        "note": "the executed procedure did not reach a correct verdict",
                    }
            elif declared == "program_replay":
                module = Path(record["emitting_routes"][0]["writer_file"]).stem
                removal = runner.import_program_module(module, bundle_root / "good")
                entry["executed_recheck_procedure"] = "program_replay"
                entry["verdict"] = (
                    "NEEDS-PROGRAM" if not removal["import_succeeded"] else "UNTESTED"
                )
                entry["verdict_evidence"] = {
                    "argv": removal["argv"],
                    "exit_code": removal["exit_code"],
                    "stderr_head": removal["stderr_head"],
                }
                entry["blocking_dependency"] = {
                    "name": f"scripts/{module}.py",
                    "role": "this repository's own code, which the declared "
                    "recheck procedure replays",
                    "confirmed_by_removal": not removal["import_succeeded"],
                    "how_confirmed": (
                        "the writer module was imported with the program tree "
                        "renamed away; the import raised"
                    ),
                }
                if removal["import_succeeded"]:
                    state["census_misses"].append(
                        {
                            "kind_id": kind_id,
                            "miss": "a program_replay kind's writer imported "
                            "with the program tree renamed away",
                            "consequence": "verdict read UNTESTED, not "
                            "NEEDS-PROGRAM; the declaration and the executed "
                            "procedure disagree (B10)",
                        }
                    )
            else:
                entry["executed_recheck_procedure"] = "none"
                entry["verdict"] = "UNTESTED"
                entry["verdict_evidence"] = {
                    "reason": (
                        "the census found no committed instance and no "
                        "published reconstruction rule, so there was no "
                        "procedure to execute"
                        if declared == "none"
                        else "this kind declares a raw checker invocation but "
                        "no reconstruction rule has been published for it; "
                        "CR-P1 worked one kind and this is not it"
                    )
                }
            state["verdicts"][kind_id] = entry

        # -- B3 tamper ---------------------------------------------------
        tamper_runs = []
        for mutation in ("content", "digest", "binding"):
            mutated, witness = mutate(receipts, mutation)
            path = bundle_root / f"tamper_{mutation}"
            build_bundle(path, mutated, rule, census)
            out = evidence / f"tamper_{mutation}.json"
            result = runner.recheck(path, real_argv, out)
            tamper_runs.append(
                {
                    "mutation": mutation,
                    "witness_of_difference": witness,
                    "discarded": not witness["changed"],
                    "outcome": result["report"].get("outcome"),
                    "exit_code": result["exit_code"],
                    "stdout_head": result["stdout_head"],
                    "failed_checks": result["report"].get("first_failures"),
                    "evidence_file": f"cold/evidence/tamper_{mutation}.json",
                }
            )
        scored = [row for row in tamper_runs if not row["discarded"]]
        state["arms"]["tamper"] = {
            "design": "§7 B3 — three mutations different IN KIND, 100% must FAIL",
            "runs": tamper_runs,
            "gate": {
                "clause": "tamper 3x per kind 100% FAIL",
                "mutations_scored": len(scored),
                "mutations_discarded": len(tamper_runs) - len(scored),
                "failed": sum(1 for row in scored if row["outcome"] == "FAIL"),
                "green": bool(scored)
                and all(row["outcome"] == "FAIL" for row in scored),
            },
        }

        # -- B4 omission -------------------------------------------------
        missing_checker = empty_deps / checker.name
        omission = runner.recheck(
            bundle_root / "good", [str(missing_checker)], evidence / "omission.json"
        )
        names_it = "lean.exe" in (omission["stdout_head"] or "")
        state["arms"]["omission"] = {
            "design": "§7 B4 — FAIL LOUD naming the missing dependency; a "
            "silent pass voids THE HARNESS, not the kind",
            "removed_dependency": "lean.exe",
            "resolved_to": str(missing_checker),
            "exit_code": omission["exit_code"],
            "stdout_head": omission["stdout_head"],
            "report": omission["report"],
            "gate": {
                "clause": "omission FAIL LOUD naming the missing dependency",
                "failed_loud": omission["exit_code"] == 2,
                "named_the_dependency": names_it,
                "silent_pass": omission["exit_code"] == 0,
                "green": omission["exit_code"] == 2 and names_it,
                "voids_the_harness_if_silent": True,
            },
        }

        # -- B5 sham -----------------------------------------------------
        sham_runs = {}
        for label, bundle_path, argv_prefix in (
            ("real_checker_good_bundle", bundle_root / "good", real_argv),
            ("real_checker_known_bad_bundle", bundle_root / "known_bad", real_argv),
            ("sham_checker_good_bundle", bundle_root / "good", sham_argv),
            ("sham_checker_known_bad_bundle", bundle_root / "known_bad", sham_argv),
        ):
            out = evidence / f"sham_{label}.json"
            result = runner.recheck(bundle_path, argv_prefix, out)
            sham_runs[label] = {
                "argv": result["argv"],
                "outcome": result["report"].get("outcome"),
                "exit_code": result["exit_code"],
                "stdout_head": result["stdout_head"],
                "evidence_file": f"cold/evidence/sham_{label}.json",
            }
        sham_survives = sum(
            1
            for key, row in sham_runs.items()
            if key.startswith("sham_checker") and row["outcome"] == "PASS"
        )
        state["arms"]["sham"] = {
            "design": "§7 B5 — the capability-blind control; it can void every "
            "kind at once and is written to be able to",
            "stub": "harness/sham_lean.py (prints nothing, exits 0)",
            "disclosed_weakness": (
                "the stub matches the INTERFACE — argv shape, cwd, exit-code "
                "contract — but not the NAME: producing a same-named native "
                "executable needs a toolchain this workstation does not have. "
                "The substitution is weaker than §7's wording and is recorded "
                "as such."
            ),
            "runs": sham_runs,
            "negative_control": {
                "statement": "the instrument must be able to say no",
                "real_checker_rejects_the_known_bad_bundle": (
                    sham_runs["real_checker_known_bad_bundle"]["outcome"] == "FAIL"
                ),
                "known_bad_witness": bad_witness,
            },
            "gate": {
                "clause": "sham-checker SURVIVES count = 0",
                "value": sham_survives,
                "green": sham_survives == 0,
            },
            "why_this_arm_reads_the_way_it_does": (
                "this kind's procedure compares against the RECORDED exit "
                "codes, and every committed row records positive=1. A stub "
                "that always exits 0 therefore cannot reproduce them. That is "
                "why B5 reads zero here, and it is stated so nobody mistakes a "
                "structural fact for a strong result."
            ),
        }

        # -- B6 scramble -------------------------------------------------
        scramble_record = run_scramble(
            runner,
            args.scramble_bundles,
            bundle_root,
            receipts,
            rule,
            census,
            real_argv,
            evidence,
        )
        state["arms"]["scramble"] = scramble_record

        # -- B11 provenance ----------------------------------------------
        tagged = []
        for dep in census["external_deps_seed"]:
            resolved_sha = None
            if dep["name"] == "lean.exe":
                resolved_sha = lean_sha
            tagged.append({**{k: dep[k] for k in ("name", "role", "pin_hash")},
                           **assign_provenance(dep, resolved_sha)})
        downgrades = [
            entry["kind_id"]
            for entry in state["verdicts"].values()
            if entry.get("b11_downgrade_applied")
        ]
        state["arms"]["provenance"] = {
            "design": "§8 B11 — two tags, two tests, two assigners",
            "dependencies": tagged,
            "gate": {
                "clause": (
                    "any SURVIVES resting on a program_configured dependency "
                    "downgrades to UNTESTED"
                ),
                "downgrades_applied": downgrades,
                "green": True,
                "note": (
                    "B11 cannot go red; it can only move verdicts. It is green "
                    "when the downgrade was applied mechanically, which the "
                    "harness does per kind from the bytes."
                ),
            },
        }

    finally:
        if RENAMED_TREE.is_dir() and not PROGRAM_TREE.exists():
            RENAMED_TREE.rename(PROGRAM_TREE)

    after = working_tree_digest(REPO)

    state["scope"] = {
        "harness_shape": "clean-PATH subprocess environment, not a container",
        "why_not_a_container": (
            "the receipts pin a digest of a Windows binary: the C-E3 supplement "
            "records binary_sha256 over lean.exe and the three lean4 verdicts "
            "record platform win32. A Linux container runs a different binary "
            "with a different digest, so a re-check inside one would be a "
            "re-check of different receipts (§6)."
        ),
        "weaker_than_a_container": True,
        "not_excluded": [
            "the Windows registry",
            "%USERPROFILE% (and therefore ~/.elan, where the checker lives)",
            ".runtime/",
            "any system-wide Python and its site-packages",
            "every ambient DLL search path",
            "the harness's own interpreter",
        ],
        "interpreter": runner.interpreter,
        "interpreter_note": (
            "the harness declines to use this repository's .venv: sys.base_prefix "
            "points outside the repository root, and -S -I keeps every "
            "site-packages off the child's path. It is still program_configured "
            "under §8 — no digest of it is pinned anywhere — and it is listed "
            "above rather than assumed away."
        ),
        "dependency_dirs_on_path": [str(d) for d in runner.dependency_dirs],
        "working_tree": {
            "digest_before_rename": before,
            "digest_after_restore": after,
            "byte_identical": before["digest"] == after["digest"],
            "restore_path": (
                "the rename is undone in a finally block and the tree is "
                "re-digested against the pre-rename value; a mismatch is a "
                "harness failure reported as such, never absorbed (§6)"
            ),
            "program_tree_restored": PROGRAM_TREE.is_dir(),
        },
    }
    state["run_metadata"] = {
        "started_utc_epoch": int(started_wall),
        "elapsed_seconds": round(time.time() - started_wall, 1),
        "bundle_root": str(bundle_root),
        "platform": sys.platform,
    }

    # B10's ordering, checked against history rather than asserted: at the
    # commit that sealed the census, no file under harness/ existed. That is
    # the WITNESS W0 precedent made checkable — and it stays checkable after
    # the harness is committed, which a "has the harness been committed yet"
    # test would not.
    seal_commit = git_commit_touching(CENSUS_PATH)
    state["census_commit"] = seal_commit
    state["harness_commit"] = git_commit_touching(HARNESS / "cold_harness.py")
    state["harness_files_at_census_commit"] = tree_files_at(seal_commit, "harness")
    state["seal_predates_harness"] = bool(seal_commit) and not state[
        "harness_files_at_census_commit"
    ]

    block = provenance_block(
        Path(__file__), [CENSUS_PATH, RULE_PATH, SUPPLEMENT_PATH]
    )
    cold_census = redact(build_cold_census(args, state))
    cold_census["provenance"] = block
    state["arms"]["scramble"]["provenance"] = block
    (out_dir / "census.json").write_text(
        json.dumps(cold_census, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "path_audit.txt").write_text(
        redact(render_path_audit(path_audit)), encoding="utf-8"
    )
    (evidence / "path_audit.json").write_text(
        json.dumps(redact(path_audit), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "scramble_baseline.json").write_text(
        json.dumps(redact(state["arms"]["scramble"]), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    # The per-run evidence probe_recheck wrote is rewritten on the same rule:
    # it is committed beside the census and must obey R5 too.
    for path in sorted(evidence.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # pragma: no cover
            continue
        path.write_text(
            json.dumps(redact(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    counts = cold_census["counts"]
    print(
        f"kinds {counts['kinds']}  SURVIVES {counts['SURVIVES']}  "
        f"NEEDS-PROGRAM {counts['NEEDS-PROGRAM']}  UNTESTED {counts['UNTESTED']}  "
        f"voiding_fired {cold_census['voiding_sentence']['fired']}  "
        f"tree_identical {state['scope']['working_tree']['byte_identical']}"
    )
    return 0


def run_scramble(
    runner: Runner,
    bundles: int,
    bundle_root: Path,
    receipts: dict,
    rule: dict,
    census: dict,
    real_argv: list[str],
    evidence: Path,
) -> dict:
    """B6, the vacuity control, budgeted and published whichever way it reads."""

    kind = next(
        record
        for record in census["kinds"]
        if record["kind_id"] == EXECUTABLE_KIND
    )
    scramble_rule = kind["scramble_rule"]
    started = time.time()
    outcomes = []
    overran = False
    path = bundle_root / "scramble"

    # What the invocation step can and cannot discriminate here, measured
    # before the arm runs rather than explained after it.
    rows = [row for row in receipts["rows"] if "checker_receipt" in row]
    recorded_pairs = {
        (
            row["checker_receipt"]["positive_probe"]["returncode"],
            row["checker_receipt"]["negative_probe"]["returncode"],
        )
        for row in rows
    }

    for index in range(bundles):
        scrambled, meta = scramble(receipts, scramble_rule["seed"] + index)
        build_bundle(path, scrambled, rule, census)
        out = evidence / "scramble_last.json"
        result = runner.recheck(path, real_argv, out)
        report = result["report"]
        outcomes.append(
            {
                "bundle": index,
                "seed": meta["seed"],
                "identity_redraws": meta["identity_redraws"],
                "outcome": report.get("outcome"),
                "rows_ok": report.get("rows_ok"),
                "checker_invocations": report.get("checker_invocations"),
                "elapsed_seconds": report.get("elapsed_seconds"),
            }
        )
        if time.time() - started > B6_BUDGET_SECONDS:
            overran = True
            break

    elapsed = time.time() - started
    passed = sum(1 for row in outcomes if row["outcome"] == "PASS")
    invocations = sum(row.get("checker_invocations") or 0 for row in outcomes)

    record = {
        "design": "§7 B6 — the vacuity control: what a bundle earns by being "
        "THE RIGHT ONE rather than by being A BUNDLE",
        "scramble_rule": scramble_rule,
        "bundles_requested": bundles,
        "bundles_run": len(outcomes),
        "bundles_passed": passed,
        "checker_invocations": invocations,
        "elapsed_seconds": round(elapsed, 1),
        "budget": {
            "design_estimate_minutes": "59 at the mean, 63 at the observed max",
            "overrun_threshold_minutes": 90,
            "overran": overran,
            "published_before_any_chance_rate_is_read": True,
        },
        "what_the_invocation_step_can_discriminate": {
            "distinct_recorded_exit_code_pairs": [
                list(pair) for pair in sorted(recorded_pairs)
            ],
            "note": (
                "every committed row of this kind records the same "
                "(positive, negative) exit-code pair, so a permutation of "
                "receipts across rows leaves step 4's comparison unchanged and "
                "ONLY step 3's digest comparison can catch it. The invocation "
                "step contributes nothing to detecting this scramble. That is a "
                "property of the data, measured here rather than discovered "
                "after the number was read."
            ),
        },
        "outcomes": outcomes,
        "gate": {
            "clause": (
                "chance measured: 200 scrambled bundles; if 0 of 200 pass, "
                "publish the 1.5% rule-of-three upper bound as the chance rate"
            ),
            "bundles": len(outcomes),
            "passed": passed,
            "rule_of_three_upper_bound": (
                round(3 / len(outcomes), 4) if outcomes and passed == 0 else None
            ),
            "upper_bound_is_not_a_measured_rate": (
                "an upper bound on a chance rate, never a measured rate, and "
                "never quoted as though 0 were the finding"
            ),
            "green": bool(outcomes) and passed == 0,
        },
    }
    return record


def render_path_audit(audit: dict) -> str:
    lines = [
        "COLD RECEIPT — path_audit",
        "=========================",
        "",
        "DESIGN-cold-receipt.md §6 (C2): PATH alone is not the audit. §1's own",
        "exhibit reaches scripts/ through Path(__file__).parents[1] and",
        "sys.path.insert, which no PATH setting anywhere would have stopped.",
        "Two assertions therefore, not one.",
        "",
        f"repository root : {audit['repository_root']}",
        f"program tree    : renamed to {audit['program_tree_renamed_to']}",
        f"scripts/ exists : {audit['program_tree_exists']}",
        f"cwd             : {audit['cwd']} (inside repo: {audit['cwd_inside_repository']})",
        "",
        "interpreter",
        "-----------",
    ]
    for key, value in audit["interpreter"].items():
        lines.append(f"  {key:22} {value}")
    lines += [
        "",
        "ASSERTION 1 — scripts/ is unresolvable",
        "--------------------------------------",
        f"  holds: {audit['assertion_1_program_tree_unresolvable']['holds']}",
    ]
    for row in audit["assertion_1_program_tree_unresolvable"]["imports"]:
        lines.append(f"  import {row['module']}: imported={row['imported']}")
        for line in (row.get("traceback") or "").strip().splitlines():
            lines.append(f"      {line}")
    lines += [
        "",
        "ASSERTION 2 — no sys.path entry resolves inside the repository",
        "--------------------------------------------------------------",
        f"  holds: {audit['assertion_2_no_sys_path_entry_inside_the_repository']['holds']}",
    ]
    for row in audit["assertion_2_no_sys_path_entry_inside_the_repository"]["sys_path"]:
        lines.append(
            f"  inside_repo={str(row['inside_repository']):5} {row['resolved']}"
        )
    lines += ["", "PATH entries (with listing digests)", "-----------------------------------"]
    for row in audit["path_entries"]:
        digest = (row["listing_sha256"] or "-")[:16]
        lines.append(
            f"  inside_repo={str(row['inside_repository']):5} {digest} {row['resolved']}"
        )
    lines += ["", "dependencies resolved and digested", "----------------------------------"]
    for row in audit["dependencies"]:
        lines.append(
            f"  {row['name']:12} exists={row['exists']} "
            f"sha256={row.get('sha256', '-')}"
        )
        lines.append(f"      {row['resolved']}")
    lines += [
        "",
        f"BOTH ASSERTIONS HOLD: {audit['both_assertions_hold']}",
        "",
        "What this harness does NOT exclude (§6, named so no reader has to",
        "find it): the Windows registry, %USERPROFILE% (and therefore ~/.elan,",
        "where the checker lives), .runtime/, any system-wide Python and its",
        "site-packages, every ambient DLL search path, and the harness's own",
        "interpreter. A container would exclude most of this list. This one",
        "does not, and every SURVIVES in this census is scoped to that weaker",
        "exclusion.",
        "",
    ]
    return "\n".join(lines)


def git_commit_touching(path: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(REPO), "log", "-1", "--format=%H", "--", str(path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except OSError:  # pragma: no cover
        return None
    value = completed.stdout.strip()
    return value or None


def tree_files_at(commit: str | None, prefix: str) -> list[str]:
    """Files under `prefix` that existed at `commit`. Empty is the point."""

    if not commit:
        return []
    try:
        completed = subprocess.run(
            ["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", commit, prefix],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except OSError:  # pragma: no cover
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    sys.exit(main())
