#!/usr/bin/env python3
"""The provenance block a report writer emits about its own run.

DESIGN-retraction-closure §4 wants the graph's edges into `report_ledger`
nodes emitted by the writers themselves at generation time (`inferred:
false`), following the precedent `reports/proof_correspondence.json`
already sets with its `inputs` block. This module is that precedent
factored out so the four bare core ledgers can adopt it identically.

Two constraints the code cannot show:

- **The block is a pure function of committed bytes** (gate R5, byte
  reproducibility). No timestamp, no absolute path, no environment,
  no hostname, no git state — two clean builds on two machines must
  produce identical bytes, so nothing that varies between them may
  enter. `emitted_at_generation` is a constant flag naming *how* the
  block was produced, not *when*; it is the `inferred: false` marker in
  ledger form.
- **This layer knows no ledger names.** It takes a writer path and an
  input path list as arguments. A world/report name literal here would
  make the generic layer answerable to one caller, which the bounded-
  closure suite forbids in its own generic layer for the same reason.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path

#: The repo this module ships in. `scripts/` sits directly under the root,
#: so the writer's own location fixes the root without a git call — a git
#: call would make the block depend on checkout state rather than bytes.
REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_lf_file(path: Path) -> str:
    """Canonical-LF SHA-256 of a file.

    Copied deliberately from `scripts/closure_worlds.py::sha256_lf_file`
    (design §8 there): newline translation on a Windows checkout must not
    change a frozen file's identity, so CRLF is folded to LF before
    hashing. The two implementations must agree; this one is a copy rather
    than an import because `closure_worlds` is a bounded-worlds instrument
    and a provenance helper importing it would couple the core ledger
    chain to that instrument's lifetime.
    """

    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def repo_relative(path: Path, repo_root: Path | None = None) -> str:
    """Repo-relative POSIX spelling of `path`.

    Forward slashes always, so a ledger written on Windows and a ledger
    written on Linux name the same input with the same string. A path
    outside the repo has no repo-relative identity at all; it degrades to
    its last two components rather than leaking an absolute path, which
    R5 forbids outright.
    """

    root = (repo_root or REPO_ROOT).resolve()
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        return Path(*resolved.parts[-2:]).as_posix()


def provenance_block(
    writer: Path,
    inputs: Iterable[Path],
    repo_root: Path | None = None,
) -> dict:
    """Build the block a writer stores under its report's `provenance` key.

    `writer` is the script producing the report (normally its `__file__`);
    `inputs` is exactly the set of committed files the writer read to
    produce it — derived by the caller from what it actually loads, since
    only the caller knows that. Inputs are sorted by their repo-relative
    path so the block's byte order is a property of the input set, not of
    filesystem or glob order.
    """

    root = (repo_root or REPO_ROOT).resolve()
    rows = [
        {"path": repo_relative(path, root), "sha256_lf": sha256_lf_file(Path(path))}
        for path in inputs
    ]
    rows.sort(key=lambda row: row["path"])
    return {
        "writer": repo_relative(Path(writer), root),
        "writer_sha256_lf": sha256_lf_file(Path(writer)),
        "inputs": rows,
        # Not a timestamp: the flag records that a deterministic writer
        # emitted this at generation time, which is what §4 means by an
        # edge carrying `inferred: false`.
        "emitted_at_generation": True,
    }


def corpus_provenance(
    writer: Path,
    data_dir: Path,
    repo_root: Path | None = None,
) -> dict:
    """Provenance for a writer whose whole input is `<data_dir>/*/nodes.json`.

    The glob mirrors the writers' own loaders exactly; if a writer ever
    reads something else, it must pass that file through
    `provenance_block` itself rather than widen this convenience.
    """

    return provenance_block(
        writer, sorted(Path(data_dir).glob("*/nodes.json")), repo_root
    )
