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
import re
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

#: The program tree, as the child sees it. Both limbs of the removal arm put
#: this exact string on `PYTHONPATH`; in the with-program limb the directory
#: is there and in the program-absent limb it is not. That single difference
#: is the whole experiment, and amendment 2 exists because the first run did
#: not have it (see `REMOVAL_ARM_AMENDMENT`).
PROGRAM_TREE_ON_PATH = str(PROGRAM_TREE)

REMOVAL_ARM_AMENDMENT = {
    "amendment": 2,
    "dated": "2026-08-27",
    "authority": (
        "ROADMAP-v0.21 §4.0(1) — an arm that never executed as designed is a "
        "bug, not a reading"
    ),
    "defect": (
        "run 1's removal arm ran `python -S -I -c \"import <module>\"`. Since "
        "3.11 `-I` implies `-E` and `-P`, so PYTHONPATH was ignored and the "
        "program tree was never on the child's path at all. The import failed "
        "identically with scripts/ PRESENT and ABSENT: the arm could not go "
        "red for the reason it claimed, and all nine confirmed_by_removal "
        "verdicts rested on it."
    ),
    "repair": (
        "two limbs per kind with identical argv and environment, differing "
        "only in whether the program tree exists: a with-program POSITIVE "
        "CONTROL run before the rename, and the program-absent limb run "
        "during it. NEEDS-PROGRAM now requires positive-limb SUCCESS and "
        "absent-limb FAILURE. A kind that fails both ways reads UNTESTED with "
        "its true blocking dependency named."
    ),
    "flags_dropped": ["-I"],
    "why": "-I implies -E, which is what silently discarded PYTHONPATH",
}

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

#: The commit that first sealed this registry, and the seal it carried. Both
#: are history, quoted so B10's W0 fact stays checkable after the registry is
#: amended — an amendment must not be able to erase the ordering it inherited.
FIRST_SEAL_COMMIT = "d930150"
RUN_ONE_SEAL = "6c575c70dbbdd7f79245a90902b84b0d1dd74e13176e2f878ece4f1b91b00ded"


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
        # Gitignored build output, not the repository. Excluded by name so the
        # exclusion is a rule rather than a convenience applied after a
        # surprise.
        if "__pycache__" in relative.parts:
            continue
        if not path.is_file():
            continue
        entries.append(f"{relative.as_posix()}:{sha256_file(path)}")
    return {
        "files": len(entries),
        "digest": hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest(),
        "excluded_top_level": sorted(TREE_DIGEST_EXCLUDED),
        "excluded_by_name": ["__pycache__"],
        "manifest": entries,
        "manifest_note": (
            "M5: the file:digest list the summary digest is computed FROM, so "
            "a test can re-derive it instead of believing this report"
        ),
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


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def removal_targets(record: dict, repo: Path) -> dict:
    """Which module the removal arm must actually remove (H4/H5).

    Two rules, in order, and the artifact records which one fired:

    - **descriptor**: if the kind's committed instances carry a
      `recheck_command`, the thing to remove is what that command RUNS, not
      the module that WROTE the receipt. The radius certificates name
      `scripts/radius_recheck.py`; removing `retraction_radius` would have
      tested the writer and called it the rechecker.
    - **all routes**: otherwise every distinct `writer_file` across ALL of the
      kind's `emitting_routes`. Run 1 took `emitting_routes[0]` and therefore
      tested one route of a multi-route kind — `closure-receipt/1` is emitted
      from `build_throughput_tasks` and `closure_query`, and the design's §5
      names the latter.
    """

    commands: list[str] = []
    for rel in record["committed_instances"].get("sample_paths", []):
        path = repo / rel
        if not path.is_file() or path.suffix not in (".json", ".jsonl"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        for mapping in _iter_mappings_any(data):
            value = mapping.get("recheck_command")
            if isinstance(value, str):
                commands.append(value)

    modules: list[str] = []
    for command in commands:
        for token in re.findall(r"scripts[/\\]([A-Za-z_][A-Za-z0-9_]*)\.py", command):
            modules.append(token)
    if modules:
        return {
            "modules": sorted(set(modules)),
            "selected_by": "recheck_descriptor",
            "descriptor_commands": sorted(set(commands))[:4],
            "note": (
                "the descriptor names what the recheck RUNS; removing the "
                "writer instead would have tested the wrong program"
            ),
        }

    writers = sorted(
        {Path(row["writer_file"]).stem for row in record["emitting_routes"]}
    )
    return {
        "modules": writers,
        "selected_by": "all_emitting_routes",
        "routes_covered": len(record["emitting_routes"]),
        "note": (
            "every distinct writer across ALL emitting routes, not "
            "emitting_routes[0]"
        ),
    }


def _iter_mappings_any(value: Any):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _iter_mappings_any(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_mappings_any(item)


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
        """One limb of B7's removal arm, run rather than declared.

        `-I` is deliberately ABSENT: it implies `-E`, which discards
        `PYTHONPATH`, which is exactly the bug amendment 2 repairs. `-S` stays,
        so no `site-packages` is on the path and a third-party import failure
        is visible as itself rather than hidden by the repository's `.venv`.

        The caller runs this twice with the same argv and environment — once
        with the program tree present, once with it renamed away — so the only
        difference between the two results is the removal.
        """

        env = constructed_env(self.dependency_dirs, cwd)
        env["PYTHONPATH"] = PROGRAM_TREE_ON_PATH
        # `-B` because the with-program limb imports real modules, and a
        # successful import writes __pycache__ INTO the tree this harness is
        # simultaneously proving it did not disturb. The first run of the
        # amended arm caught exactly that: 1251 files in, 1265 out.
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        argv = [
            self.interpreter["executable"],
            "-S",
            "-B",
            "-c",
            f"import {module}",
        ]
        try:
            completed = run(argv, env, cwd, timeout=180)
        except subprocess.TimeoutExpired:  # pragma: no cover
            return {
                "argv": argv,
                "pythonpath": PROGRAM_TREE_ON_PATH,
                "exit_code": None,
                "stderr_head": "TimeoutExpired",
                "import_succeeded": False,
                "missing_module": None,
            }
        stderr = completed.stderr.strip()
        missing = None
        marker = "ModuleNotFoundError: No module named "
        if marker in stderr:
            missing = stderr.split(marker)[-1].split("\n")[0].strip().strip("'\"")
        return {
            "argv": argv,
            "pythonpath": PROGRAM_TREE_ON_PATH,
            "program_tree_present": PROGRAM_TREE.is_dir(),
            "exit_code": completed.returncode,
            "stderr_head": stderr[-500:],
            "import_succeeded": completed.returncode == 0,
            "missing_module": missing,
        }

    def removal_limbs(self, modules: list[str], cwd: Path) -> dict:
        """Run one limb of the arm over every target module of one kind."""

        return {module: self.import_program_module(module, cwd) for module in modules}


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
            "registry_uncommitted_at_run": state["registry_uncommitted_at_run"],
            "how_checked": (
                "the seal the harness read is the committed one, and the "
                "registry had no uncommitted modification when the run began"
            ),
            "w0_ordering_at_first_seal": state["w0_ordering_at_first_seal"],
            "green": state["seal_predates_harness"],
            "census_misses": state["census_misses"],
            "census_miss_count": len(state["census_misses"]),
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
        "path_audit_ref": state.get("path_audit_ref", "cold/path_audit.txt"),
        "scramble_baseline_ref": state.get("scramble_ref", "cold/scramble_baseline.json"),
        "reconstruction_rule_ref": "cold/reconstruction_rule.json",
    }


def main(argv: list[str] | None = None) -> int:  # noqa: PLR0915
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=REPO / "cold")
    parser.add_argument("--scramble-bundles", type=int, default=200)
    parser.add_argument("--bundle-root", type=Path, default=None)
    parser.add_argument("--restore-only", action="store_true")
    parser.add_argument(
        "--run-label",
        default="",
        help="suffix for this run's artifacts, so an earlier run is retained "
        "unedited rather than overwritten",
    )
    parser.add_argument(
        "--reuse-scramble",
        type=Path,
        default=None,
        help="carry a previous B6 result forward with its digest and the "
        "reason it was not re-run",
    )
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
    suffix = f"_{args.run_label}" if args.run_label else ""
    evidence = out_dir / f"evidence{suffix}"
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
    # M5: the manifest the byte-identity claim is recomputed FROM lands in
    # evidence, so a test re-derives the digest instead of believing this
    # harness's own report of it. The census keeps the summary only.
    (evidence / "tree_manifest_before.json").write_text(
        json.dumps(before, indent=2), encoding="utf-8"
    )
    before = {k: v for k, v in before.items() if k != "manifest"}
    before["manifest_file"] = f"cold/evidence{suffix}/tree_manifest_before.json"

    state: dict[str, Any] = {
        "census": census,
        "verdicts": {},
        "arms": {},
        "census_misses": [],
    }

    # -- C1's POSITIVE CONTROL, run while the program is still present -------
    # Identical argv and environment to the program-absent limb; the only
    # difference is that scripts/ exists. A kind whose import fails HERE is
    # blocked by something other than the removal, and the arm says which.
    targets = {
        record["kind_id"]: removal_targets(record, REPO)
        for record in census["kinds"]
    }
    with_program: dict[str, dict] = {}
    for record in census["kinds"]:
        kind_id = record["kind_id"]
        if record["declared_recheck_procedure"]["type"] != "program_replay":
            continue
        with_program[kind_id] = runner.removal_limbs(
            targets[kind_id]["modules"], bundle_root / "good"
        )

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

        # M4: discovered, not a literal. The executable kind is the one whose
        # DECLARED procedure is a raw checker invocation and for which CR-P1
        # published a reconstruction rule naming it.
        executable_kind = next(
            (
                record["kind_id"]
                for record in census["kinds"]
                if record["declared_recheck_procedure"]["type"]
                == "raw_checker_invocation"
                and record["kind_id"] == rule.get("kind_id")
            ),
            None,
        )
        state["executable_kind"] = {
            "kind_id": executable_kind,
            "discovered_by": (
                "declared_recheck_procedure.type == 'raw_checker_invocation' "
                "AND cold/reconstruction_rule.json names this kind_id"
            ),
            "candidates_declaring_raw_checker_invocation": [
                record["kind_id"]
                for record in census["kinds"]
                if record["declared_recheck_procedure"]["type"]
                == "raw_checker_invocation"
            ],
        }

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
                # H1: these are the defaults for kinds NO arm ran on, and they
                # say why rather than asserting a verdict the arm never
                # produced. The kind the arms DID run on gets its real results
                # written in below.
                "tamper_result": {
                    "verdict": "UNTESTED",
                    "reason": (
                        "no procedure executed program-absent for this kind, "
                        "so no input a procedure reads could be mutated "
                        "(§10's B3 row: a kind whose procedure cannot be shown "
                        "to read the mutated input yields no tamper arm and is "
                        "UNTESTED, never a silent pass)"
                    ),
                },
                "omission_result": {
                    "verdict": "UNTESTED",
                    "reason": (
                        "§7's M5 escape: no procedure ran, so no listed "
                        "dependency could be removed from one"
                    ),
                },
                "sham_result": {
                    "verdict": "UNTESTED",
                    "reason": (
                        "no adjudicating dependency was invoked for this kind, "
                        "so there was nothing for the accept-all stub to "
                        "replace"
                    ),
                },
            }

            if kind_id == executable_kind and declared == "raw_checker_invocation":
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
                target = targets[kind_id]
                present = with_program[kind_id]
                absent = runner.removal_limbs(
                    target["modules"], bundle_root / "good"
                )
                entry["executed_recheck_procedure"] = "program_replay"
                entry["removal_arm"] = {
                    "targets": target,
                    "with_program_limb": present,
                    "program_absent_limb": absent,
                    "single_variable": (
                        "identical argv and environment in both limbs; the only "
                        "difference is whether scripts/ exists"
                    ),
                    "amendment": REMOVAL_ARM_AMENDMENT["amendment"],
                }

                positive_ok = bool(present) and all(
                    row["import_succeeded"] for row in present.values()
                )
                absent_failed = bool(absent) and all(
                    not row["import_succeeded"] for row in absent.values()
                )
                imported_while_absent = [
                    module
                    for module, row in absent.items()
                    if row["import_succeeded"]
                ]

                if positive_ok and absent_failed:
                    entry["verdict"] = "NEEDS-PROGRAM"
                    entry["blocking_dependency"] = {
                        "name": [f"scripts/{m}.py" for m in target["modules"]],
                        "role": (
                            "this repository's own code, which the declared "
                            "recheck procedure replays"
                        ),
                        "confirmed_by_removal": True,
                        "how_confirmed": (
                            "the same import, with the same argv and the same "
                            "PYTHONPATH, SUCCEEDED with scripts/ present and "
                            "FAILED with it renamed away; the difference "
                            "between the two limbs is the removal and nothing "
                            "else"
                        ),
                    }
                elif not positive_ok:
                    # The kind is blocked by something that is not the program.
                    # Naming it is the whole value of the positive control.
                    blockers = sorted(
                        {
                            row["missing_module"]
                            for row in present.values()
                            if not row["import_succeeded"] and row["missing_module"]
                        }
                    )
                    entry["verdict"] = "UNTESTED"
                    entry["blocking_dependency"] = {
                        "name": blockers or ["unknown"],
                        "role": (
                            "a dependency that is NOT this repository's code: "
                            "the recheck could not run even with the program "
                            "fully present"
                        ),
                        "confirmed_by_removal": False,
                        "how_confirmed": (
                            "the with-program positive control FAILED, so the "
                            "program-absent failure cannot be attributed to "
                            "the removal. The true blocking dependency is "
                            "named here instead."
                        ),
                        "is_program_configured": True,
                    }
                    state["census_misses"].append(
                        {
                            "kind_id": kind_id,
                            "miss": (
                                "declared program_replay, but the procedure "
                                "cannot run even with the program present"
                            ),
                            "true_blocking_dependency": blockers,
                            "consequence": (
                                "verdict reads UNTESTED, not NEEDS-PROGRAM "
                                "(B10: the declared and executed procedures "
                                "disagree)"
                            ),
                        }
                    )
                else:
                    entry["verdict"] = "UNTESTED"
                    entry["blocking_dependency"] = {
                        "name": imported_while_absent,
                        "role": "resolved from outside the renamed program tree",
                        "confirmed_by_removal": False,
                        "how_confirmed": (
                            "a target imported with the program tree renamed "
                            "away, so the removal did not remove it"
                        ),
                    }
                    state["census_misses"].append(
                        {
                            "kind_id": kind_id,
                            "miss": (
                                "a program_replay target imported with the "
                                "program tree renamed away"
                            ),
                            "modules": imported_while_absent,
                            "consequence": "verdict read UNTESTED, not NEEDS-PROGRAM",
                        }
                    )

                sample = next(iter(absent.values()), {})
                entry["verdict_evidence"] = {
                    "argv": sample.get("argv"),
                    "pythonpath": sample.get("pythonpath"),
                    "exit_code": sample.get("exit_code"),
                    "stderr_head": sample.get("stderr_head"),
                    "with_program_limb_succeeded": positive_ok,
                    "program_absent_limb_failed": absent_failed,
                    "note": (
                        "the verdict comes from the EXECUTED pair of limbs, "
                        "never from the declaration (§4)"
                    ),
                }
            else:
                entry["executed_recheck_procedure"] = "none"
                entry["verdict"] = "UNTESTED"
                entry["verdict_evidence"] = {
                    "reason": (
                        "the census found no committed instance of this kind "
                        "under either the exact or the superset rule, so there "
                        "was no receipt to re-check"
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
            "ran_on_kind": executable_kind,
            "runs": tamper_runs,
            "gate": {
                "clause": "tamper 3x per kind 100% FAIL",
                # M2: the denominator is ONE kind. B3 is green over the kind
                # whose procedure executed, and silent about the other 18.
                "kinds_in_denominator": 1,
                "kind_in_denominator": executable_kind,
                "kinds_with_no_tamper_arm": len(census["kinds"]) - 1,
                "scope_note": (
                    "this row scores the one kind whose procedure executed "
                    "program-absent. It says nothing about the other 18, which "
                    "read UNTESTED for tamper because no procedure ran on them."
                ),
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
            "ran_on_kind": executable_kind,
            "gate": {
                "clause": "omission FAIL LOUD naming the missing dependency",
                "kinds_in_denominator": 1,
                "kind_in_denominator": executable_kind,
                "scope_note": (
                    "one kind invoked a removable dependency; every other kind "
                    "reads §7's M5 UNTESTED escape because no procedure ran"
                ),
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
            "ran_on_kind": executable_kind,
            "gate": {
                "clause": "sham-checker SURVIVES count = 0",
                "kinds_in_denominator": 1,
                "kind_in_denominator": executable_kind,
                "scope_note": (
                    "one kind invoked an adjudicating dependency for the stub "
                    "to replace; the arm is silent about the other 18"
                ),
                "value": sham_survives,
                "green": sham_survives == 0,
            },
            # M3: the arm's ACTUAL mechanism, recorded beside the interface
            # weakness, because they are two different limitations.
            "mechanism": {
                "what_the_stub_does": "prints nothing, exits 0, for every probe",
                "what_the_procedure_compares": (
                    "the RECORDED exit codes, and every committed row of this "
                    "kind records positive=1 / negative=0"
                ),
                "therefore": (
                    "a constant-zero stub fails the good bundle AND the "
                    "known-bad bundle. It cannot read SURVIVES for this kind "
                    "under ANY bundle, so B5's zero here is STRUCTURAL: the "
                    "arm could not have fired for this kind however the "
                    "receipts read."
                ),
                "what_that_costs": (
                    "B5 is a real control against a harness that checked only "
                    "bundle PRESENCE — that harness would have passed the "
                    "sham. It is NOT evidence that this kind's procedure would "
                    "detect a subtler stub, e.g. one replaying the recorded "
                    "exit codes. That stronger arm is not run here and is not "
                    "claimed."
                ),
            },
        }

        # -- B6 scramble -------------------------------------------------
        if args.reuse_scramble is not None:
            carried = json.loads(
                args.reuse_scramble.read_text(encoding="utf-8")
            )
            carried["carried_forward"] = {
                "from_artifact": args.reuse_scramble.resolve()
                .relative_to(REPO)
                .as_posix(),
                "artifact_sha256": sha256_file(args.reuse_scramble),
                "why_not_re_run": (
                    "amendment 2 repairs the REMOVAL arm. B6 scrambles the "
                    "C-E3 bundle and invokes the pinned checker; nothing the "
                    "amendment changes touches it, its rule is seeded from the "
                    "kind_id, and the run is deterministic. Re-running 10,000 "
                    "invocations to reproduce a number the fix cannot move "
                    "would be an hour spent proving determinism."
                ),
                "what_would_invalidate_this": (
                    "any change to the scramble rule, the bundle contents, the "
                    "reconstruction rule, or the checker pin"
                ),
            }
            carried.pop("provenance", None)
            state["arms"]["scramble"] = carried
        else:
            state["arms"]["scramble"] = run_scramble(
                runner,
                args.scramble_bundles,
                bundle_root,
                receipts,
                rule,
                census,
                real_argv,
                evidence,
            )

        # -- H1: the arms' results, written INTO the kind they ran on ----
        # Run 1 left this record saying UNTESTED on all three arms while the
        # arms block above it showed them running on exactly this kind. A
        # record that contradicts its own evidence is worse than a silent one.
        if executable_kind and executable_kind in state["verdicts"]:
            target = state["verdicts"][executable_kind]
            tamper_gate = state["arms"]["tamper"]["gate"]
            target["tamper_result"] = {
                "verdict": "FAIL_ON_ALL_MUTATIONS"
                if tamper_gate["green"]
                else "NOT_ALL_MUTATIONS_FAILED",
                "mutations_scored": tamper_gate["mutations_scored"],
                "mutations_discarded": tamper_gate["mutations_discarded"],
                "mutations_failed": tamper_gate["failed"],
                "per_mutation": {
                    row["mutation"]: {
                        "outcome": row["outcome"],
                        "failed_checks": sorted(
                            {
                                check
                                for failure in (row["failed_checks"] or [])
                                for check in failure["failed_checks"]
                            }
                        ),
                    }
                    for row in state["arms"]["tamper"]["runs"]
                },
            }
            omission_gate = state["arms"]["omission"]["gate"]
            target["omission_result"] = {
                "verdict": "FAIL_LOUD"
                if omission_gate["green"]
                else ("SILENT_PASS" if omission_gate["silent_pass"] else "FAILED_QUIETLY"),
                "removed_dependency": state["arms"]["omission"]["removed_dependency"],
                "exit_code": state["arms"]["omission"]["exit_code"],
                "named_the_dependency": omission_gate["named_the_dependency"],
            }
            sham_gate = state["arms"]["sham"]["gate"]
            target["sham_result"] = {
                "verdict": "NO_SURVIVOR" if sham_gate["green"] else "SURVIVED_THE_STUB",
                "survives_count": sham_gate["value"],
                "runs": {
                    label: row["outcome"]
                    for label, row in state["arms"]["sham"]["runs"].items()
                },
                "mechanism_ref": "arms.sham.mechanism",
            }

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
    (evidence / "tree_manifest_after.json").write_text(
        json.dumps(after, indent=2), encoding="utf-8"
    )
    after = {k: v for k, v in after.items() if k != "manifest"}
    after["manifest_file"] = f"cold/evidence{suffix}/tree_manifest_after.json"

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
    state["scramble_ref"] = (
        args.reuse_scramble.resolve().relative_to(REPO).as_posix()
        if args.reuse_scramble is not None
        else f"cold/scramble_baseline{suffix}.json"
    )
    state["path_audit_ref"] = f"cold/path_audit{suffix}.txt"
    state["run_metadata"] = {
        "executable_kind": state.get("executable_kind"),
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
    # B10, generalised for a second run. Run 1 could ask "did any harness file
    # exist at the sealing commit?"; run 2 cannot, because the harness exists.
    # What must hold for EVERY run is that the seal the harness read is the
    # committed one and was committed before the run started.
    state["registry_uncommitted_at_run"] = not git_clean(CENSUS_PATH)
    state["seal_predates_harness"] = (
        bool(seal_commit) and not state["registry_uncommitted_at_run"]
    )
    state["w0_ordering_at_first_seal"] = {
        "statement": (
            "at the commit that first sealed this registry, no file under "
            "harness/ existed — the WITNESS W0 ordering"
        ),
        "first_seal_commit": FIRST_SEAL_COMMIT,
        "harness_files_at_that_commit": tree_files_at(FIRST_SEAL_COMMIT, "harness"),
    }

    # H2: the two instance-side misses, published as B10 misses because they
    # were found AFTER run 1's seal. The amended registry repairs the rule; the
    # miss is recorded against the seal that did not have it.
    for row in census.get("instance_recall_probe", {}).get(
        "kinds_the_exact_rule_alone_would_have_read_as_none", []
    ):
        state["census_misses"].append(
            {
                "kind_id": row["kind_id"],
                "miss": (
                    "run 1's exact key-set instance rule read 0 committed "
                    f"instances; a proper-superset match finds "
                    f"{row['superset_only_count']}"
                ),
                "found_after_seal": RUN_ONE_SEAL,
                "repaired_in": "registry amendment 2 (I2b)",
                "consequence": (
                    "the kind's declared recheck procedure moved from `none` "
                    "to `program_replay`, and it is adjudicated by the removal "
                    "arm in this run rather than skipped"
                ),
            }
        )

    block = provenance_block(
        Path(__file__), [CENSUS_PATH, RULE_PATH, SUPPLEMENT_PATH]
    )
    cold_census = redact(build_cold_census(args, state))
    cold_census["amendment"] = REMOVAL_ARM_AMENDMENT | {
        "run_one_artifacts_retained_unedited": [
            "cold/census.json",
            "cold/path_audit.txt",
            "cold/scramble_baseline.json",
            "cold/evidence/",
            "cold/result_gate.json",
        ],
        "registry_amendment": census.get("amendment", {}).get("amendment"),
        "registry_seal_run_one": RUN_ONE_SEAL,
        "registry_seal_this_run": census["census_seal"],
    }
    cold_census["provenance"] = block
    (out_dir / f"census{suffix}.json").write_text(
        json.dumps(cold_census, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / f"path_audit{suffix}.txt").write_text(
        redact(render_path_audit(path_audit)), encoding="utf-8"
    )
    (evidence / "path_audit.json").write_text(
        json.dumps(redact(path_audit), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if args.reuse_scramble is None:
        state["arms"]["scramble"]["provenance"] = block
        (out_dir / f"scramble_baseline{suffix}.json").write_text(
            json.dumps(
                redact(state["arms"]["scramble"]), indent=2, ensure_ascii=False
            )
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


def git_clean(path: Path) -> bool:
    """True when `path` has no uncommitted modification."""

    try:
        completed = subprocess.run(
            ["git", "-C", str(REPO), "diff", "--quiet", "HEAD", "--", str(path)],
            capture_output=True,
            timeout=60,
        )
    except OSError:  # pragma: no cover
        return False
    return completed.returncode == 0


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
