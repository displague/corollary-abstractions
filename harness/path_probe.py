#!/usr/bin/env python3
"""The subprocess that writes `path_audit`'s evidence.

`docs/DESIGN-cold-receipt.md` §6's C2 repair is the reason this exists as a
separate program: §1's own exhibit is `replay_session.py:69-71`, which reaches
`scripts/` through `Path(__file__).resolve().parents[1]` and
`sys.path.insert`. **No `PATH` setting anywhere would have stopped it.** So the
audit asserts two things, not one, and both are measured from inside the
subprocess that will run the recheck:

1. `scripts/` is unresolvable — an import of a known program module raises,
   with the traceback quoted;
2. no `sys.path` entry resolves inside the repository — the subprocess dumps
   its own resolved `sys.path` and every entry is shown to lie outside the
   repository root, alongside `PATH`'s entries with their listing digests, and
   every invoked dependency's resolved path and sha256.

Stdlib only, and it must run under `python -S -I`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path


def _listing_digest(directory: Path) -> str | None:
    """A digest of a directory's sorted entry names.

    Not of its contents: what the audit needs is a stable identity for *what
    was on PATH*, cheap enough to take for every entry.
    """

    try:
        names = sorted(p.name for p in directory.iterdir())
    except OSError:
        return None
    return hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()


def _inside(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(root)
        return True
    except (ValueError, OSError):
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--program-module",
        action="append",
        default=[],
        help="a module name that only exists inside the program tree",
    )
    parser.add_argument(
        "--dependency",
        action="append",
        default=[],
        help="a path whose resolution and sha256 the audit records",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.repo_root.resolve()

    sys_path = []
    for entry in sys.path:
        resolved = str(Path(entry).resolve()) if entry else "<empty string>"
        sys_path.append(
            {
                "raw": entry,
                "resolved": resolved,
                "inside_repository": bool(entry) and _inside(Path(entry), root),
                "exists": bool(entry) and Path(entry).exists(),
            }
        )

    path_entries = []
    for entry in (os.environ.get("PATH") or "").split(os.pathsep):
        if not entry:
            continue
        directory = Path(entry)
        path_entries.append(
            {
                "raw": entry,
                "resolved": str(directory.resolve()),
                "inside_repository": _inside(directory, root),
                "exists": directory.exists(),
                "listing_sha256": _listing_digest(directory),
            }
        )

    imports = []
    for name in args.program_module:
        record: dict = {"module": name}
        try:
            __import__(name)
            module = sys.modules[name]
            record["imported"] = True
            record["resolved_file"] = getattr(module, "__file__", None)
        except BaseException:  # noqa: BLE001 - the traceback IS the evidence
            record["imported"] = False
            record["traceback"] = traceback.format_exc()
        imports.append(record)

    dependencies = []
    for spec in args.dependency:
        name, _, raw = spec.partition("=")
        target = Path(raw or name)
        row: dict = {
            "name": name,
            "requested": str(target),
            "resolved": str(target.resolve()) if raw or name else None,
            "exists": target.is_file(),
        }
        if target.is_file():
            row["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            row["size_bytes"] = target.stat().st_size
        dependencies.append(row)

    audit = {
        "repository_root": str(root),
        "interpreter": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
            "flags_no_site": bool(getattr(sys.flags, "no_site", 0)),
            "flags_isolated": bool(getattr(sys.flags, "isolated", 0)),
            "inside_repository": _inside(Path(sys.executable), root),
        },
        "cwd": os.getcwd(),
        "cwd_inside_repository": _inside(Path.cwd(), root),
        "assertion_1_program_tree_unresolvable": {
            "statement": (
                "an import of a known program module raises, with the "
                "traceback quoted"
            ),
            "holds": bool(imports) and all(not r["imported"] for r in imports),
            "imports": imports,
        },
        "assertion_2_no_sys_path_entry_inside_the_repository": {
            "statement": (
                "every resolved sys.path entry lies outside the repository root"
            ),
            "holds": not any(entry["inside_repository"] for entry in sys_path),
            "sys_path": sys_path,
        },
        "path_entries": path_entries,
        "path_entries_inside_repository": [
            entry["raw"] for entry in path_entries if entry["inside_repository"]
        ],
        "dependencies": dependencies,
        "environment_keys_present": sorted(os.environ),
    }
    audit["both_assertions_hold"] = (
        audit["assertion_1_program_tree_unresolvable"]["holds"]
        and audit["assertion_2_no_sys_path_entry_inside_the_repository"]["holds"]
    )
    args.out.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("both_assertions_hold", audit["both_assertions_hold"])
    return 0 if audit["both_assertions_hold"] else 1


if __name__ == "__main__":
    sys.exit(main())
