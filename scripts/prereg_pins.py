#!/usr/bin/env python3
"""Resolve a preregistered pin through the retirements declared against it.

A preregistration freezes a digest so a later run can prove it was measured
under the artifact it claims. When a defect forces one of those artifacts to
change, the repository's standing mechanic (v0.19's transliteration lane, and
ROADMAP-v0.20 §4b after it) is **retirement in writing, never edit in place**:

* the frozen row keeps its original digest, because artifacts that quoted a
  number measured under it must stay checkable against it;
* a dated `amendments` entry names the row it retires and the **successor
  prereg** that carries the digest future comparisons read against;
* the frozen row grows a `retired_for_future_comparisons` marker pointing at
  that amendment by id.

Two consumers were each re-implementing half of that walk — a test that
followed one hop and a run-writer that followed none, so a declared
retirement read to the writer as undeclared drift. This module is the one
implementation both use, which is what makes "the chain is followed, never
skipped" a property of the code rather than of two comments.

**The chain is followed to its end, and every hop must be declared.** A
successor row may itself have been retired by a later amendment; that is what
happens when two cycles touch one file. What is never permitted is a hop that
does not exist: a marker naming an amendment its own prereg does not record
raises, rather than silently dropping the check. A pin deleted and a pin
retired in writing are different things, and only the second one is allowed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class PinChainError(RuntimeError):
    """A retirement marker that does not resolve. Never a silently dropped check."""


def sha256_lf(path: Path) -> str:
    """The digest every prereg in this repository records."""

    return hashlib.sha256(
        Path(path).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()


def resolve_pin(
    prereg: dict,
    row: dict,
    *,
    prereg_path: str = "<prereg>",
    repo_root: Path | None = None,
    _seen: tuple[str, ...] = (),
) -> dict:
    """The digest `row` should be checked against today, and how it was reached.

    Returns ``{"sha256_lf", "source", "hops"}`` — the live pin, the prereg
    file that carries it, and the amendment ids walked to get there. A row
    with no retirement marker resolves to itself in zero hops, so the common
    case costs nothing and reads the same way.
    """

    root = repo_root or REPO_ROOT
    marker = row.get("retired_for_future_comparisons")
    if marker is None:
        return {"sha256_lf": row["sha256_lf"], "source": prereg_path, "hops": list(_seen)}

    amendment_id = marker.get("amendment")
    named = [
        entry
        for entry in prereg.get("amendments", ())
        if entry.get("amendment_id", "").endswith(str(amendment_id))
    ]
    if len(named) != 1:
        raise PinChainError(
            f"{row['path']} claims retirement by amendment {amendment_id!r}, "
            f"which {prereg_path} does not record exactly once "
            f"({len(named)} matches). A pin retired in writing names an "
            f"amendment that exists; anything else is a pin deleted."
        )
    successor_path = named[0]["successor_prereg"]["path"]
    if successor_path in _seen:
        raise PinChainError(
            f"retirement chain for {row['path']} revisits {successor_path}; "
            f"a cycle is not a retirement"
        )
    successor = json.loads((root / successor_path).read_text(encoding="utf-8"))
    live_rows = {entry["role"]: entry for entry in successor["frozen"]}
    if row["role"] not in live_rows:
        raise PinChainError(
            f"{successor_path} carries no {row['role']!r} row, so the "
            f"retirement of {row['path']} declared in {prereg_path} does not "
            f"land anywhere"
        )
    live = live_rows[row["role"]]
    if live["path"] != row["path"]:
        raise PinChainError(
            f"{successor_path} pins {live['path']} for role {row['role']!r}, "
            f"but {prereg_path} retired {row['path']}"
        )
    # Follow the whole chain: two cycles touching one file is exactly the case
    # a single hop gets wrong.
    return resolve_pin(
        successor,
        live,
        prereg_path=successor_path,
        repo_root=root,
        _seen=(*_seen, successor_path),
    )


def check_frozen(prereg: dict, *, prereg_path: str, repo_root: Path | None = None):
    """Every frozen row against its live pin. Yields one record per row."""

    root = repo_root or REPO_ROOT
    for row in prereg["frozen"]:
        path = root / row["path"]
        resolved = resolve_pin(
            prereg, row, prereg_path=prereg_path, repo_root=root
        )
        observed = sha256_lf(path) if path.exists() else None
        yield {
            "path": row["path"],
            "role": row["role"],
            "recorded_sha256_lf": row["sha256_lf"],
            "live_sha256_lf": resolved["sha256_lf"],
            "live_pin_source": resolved["source"],
            "retirement_hops": resolved["hops"],
            "observed_sha256_lf": observed,
            "agrees": observed == resolved["sha256_lf"],
        }
