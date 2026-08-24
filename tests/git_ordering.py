#!/usr/bin/env python3
"""Read the preregistration ORDER out of the git history, not out of prose.

DESIGN-foreign-voice §10 registers an order — the design, then rule R and the
lexicon and the frozen parser digest, then B0d's ids and its sealed hundred,
then B-P, then the frozen register, then the renderer, then the run — and §6
B7 says the digests are recorded *before* the artifacts they gate exist.

Three earlier versions of these assertions checked, in turn: that a file did
not exist, that a `pending` list still held a row, and that a prereg row said
"promoted".  Each was true of exactly one commit and then had to be restated,
and the last of them was a string somebody could type.  The order the design
registers is a fact about **when things were written**, so this module asks
the thing that knows.

Outside a git checkout — a tarball, an exported tree, a sdist — the ordering
is genuinely unreadable and every caller **skips** rather than passing.  A
green assertion that could not have been red is the failure mode this whole
file exists to replace.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _git(*args: str) -> str:
    """Run git in the repository, or SKIP. Never fails the suite on a tarball."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError as exc:  # pragma: no cover - no git binary on this machine
        raise unittest.SkipTest(f"git is not available: {exc}") from None
    if completed.returncode != 0:
        raise unittest.SkipTest(
            f"git {' '.join(args)} failed ({completed.stderr.strip()[:120]}); "
            f"this is not a git checkout, so the ordering cannot be read here")
    return completed.stdout.strip()


def first_added(path: str) -> str:
    """The commit that first ADDED `path`, as a full sha. Skips if unreadable."""
    out = _git("log", "--diff-filter=A", "--format=%H", "--", path)
    if not out:
        raise unittest.SkipTest(
            f"no add-commit recorded for {path}; the history is shallow or the "
            f"file arrived outside this branch")
    # `git log` lists newest first; a path added, deleted and re-added has more
    # than one. The one that matters is the FIRST time it existed.
    return out.split("\n")[-1].strip()


def is_ancestor(earlier: str, later: str) -> bool:
    """True when `earlier` is a STRICT ancestor of `later`.

    Strict on purpose: two artifacts added in the same commit are not ordered
    by the history, and an ordering claim that same-commit satisfies is an
    ordering claim that a single squashed commit would satisfy too.
    """
    if earlier == later:
        return False
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "merge-base", "--is-ancestor",
         earlier, later],
        capture_output=True, text=True,
    )
    return completed.returncode == 0


def assert_added_before(case: unittest.TestCase, earlier_path: str,
                        later_path: str, because: str) -> None:
    """`earlier_path` must have entered the tree in an earlier commit."""
    earlier = first_added(earlier_path)
    later = first_added(later_path)
    case.assertTrue(
        is_ancestor(earlier, later),
        f"{earlier_path} ({earlier[:8]}) must be added in a commit strictly "
        f"before {later_path} ({later[:8]}): {because}")


def assert_absent_or_added_after(case: unittest.TestCase, gate_path: str,
                                 gated_path: str, because: str) -> None:
    """`gated_path` may not exist yet; if it does, `gate_path` came first."""
    if not (REPO_ROOT / gated_path).exists():
        return
    assert_added_before(case, gate_path, gated_path, because)


__all__ = ["REPO_ROOT", "assert_absent_or_added_after", "assert_added_before",
           "first_added", "is_ancestor"]
