#!/usr/bin/env python3
"""DESIGN-compile-before-query §7 made executable: the untrusted builder.

This module compiles one registered world's complete bounded closure before
any goal exists. Nothing it emits is evidence. §5 names the builder, the
closure file, the controller, every policy, and every future model
untrusted; the only thing that can promote a file written here into a claim
is :func:`closure_check.check_closure` rebuilding the same graph from the
frozen sources and finding no disagreement. So this file's job is not to be
convincing. Its job is to be *checkable*, and then to submit itself.

## The independence constraint, and why it is load-bearing

The gate's whole content is the equality between what this module derives
and what the checker derives. That equality is evidence only while the two
derivations are genuinely separate. If the builder called the checker's
traversal, its minimum-depth bookkeeping, or its convergence-cell rule, then
"builder agrees with checker" would decay into "one function agrees with
itself" — a tautology dressed as a gate, and precisely the vacuous check §9
forbids.

So this module implements, from the design text rather than from the
checker's source:

* its own level-synchronous breadth-first traversal (:func:`_traverse`);
* its own minimum-depth bookkeeping (first discovery in a level-synchronous
  sweep is minimal, and every state is expanded exactly once);
* its own §6 convergence-cell derivation (:func:`_convergence_cells`).

From :mod:`closure_check` it imports exactly three names, and they are the
*definitional* pieces rather than the derivational ones:
:func:`~closure_check.enumerate_actions` (which actions exist),
:func:`~closure_check.canonical_closure_bytes` and
:func:`~closure_check.closure_digest` (how the bytes are spelled). Two
spellings of the action product would let the builder honestly enumerate a
different product than the one the gate scores; two spellings of the
canonical form would let the two sides disagree about corruption class 12.
Those are definitions, not derivations, and there is exactly one of each.
The traversal, the comparison, and the cell rule are *never* imported.

## What a written file therefore claims

That this versioned adapter, the world's own verifier, and one frozen source
snapshot produce this graph within the registered horizon — no more. Not
mathematical truth, not physical realism, not completeness of the authored
rules. The ceilings in the registration are refusals, not targets: a
traversal that would exceed ``max_states`` or ``max_actions_per_state``
raises rather than truncating, because a silently truncated closure is a
false claim of completeness and §10 says park instead.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "experiments"))

import closure_worlds  # noqa: E402
from closure_check import (  # noqa: E402
    canonical_closure_bytes,
    closure_digest,
    enumerate_actions,
)
from closure_worlds import (  # noqa: E402
    Refusal,
    canonical_action,
    canonical_json,
    sha256_hex,
    sha256_lf_file,
)

FORMAT_VERSION = "bounded-closure/1"
OUTPUT_DIR = REPO / "reports" / "closures"


class CeilingExceeded(RuntimeError):
    """A registered resource ceiling would have been crossed.

    Raised instead of returning a partial closure. §8's B2 is a clause the
    construction may honestly miss; it is not a bound to quietly resize, and
    a truncated graph that still called itself closed would convert a miss
    into a forgery.
    """


class StateCeilingExceeded(CeilingExceeded):
    """The reachable graph is larger than ``ceilings.max_states``."""


class ActionCeilingExceeded(CeilingExceeded):
    """The schema product is larger than ``ceilings.max_actions_per_state``."""


class ClosureSizeExceeded(CeilingExceeded):
    """The canonical serialization is larger than ``max_closure_bytes``."""


class BuildTooSlow(CeilingExceeded):
    """The build took longer than ``max_seconds_per_closure``."""


class UnregisteredWorld(ValueError):
    """No committed registration file declares this ``world_id``."""


# ---------------------------------------------------------------------------
# Frozen context
# ---------------------------------------------------------------------------


def _manifest_entry(path: Path, repo_root: Path) -> dict:
    """One canonical-LF digest of one frozen source, path relative to root."""

    return {
        "path": path.resolve().relative_to(repo_root.resolve()).as_posix(),
        "sha256_lf": sha256_lf_file(path),
    }


def _registration_path(registration: dict) -> Path:
    """Locate the committed file this registration was loaded from.

    Matched by declared ``world_id`` against the manifest-pinned set, never
    by guessing a filename: the manifest is the authority on which
    registrations exist, and a builder that invented a path could pin a file
    the manifest does not cover.
    """

    world_id = registration["world_id"]
    for path in closure_worlds.registration_paths():
        if closure_worlds.load_registration(path)["world_id"] == world_id:
            return path
    raise UnregisteredWorld(
        f"no committed registration declares world_id {world_id!r}"
    )


def _source_manifest(registration: dict, repo_root: Path) -> list[dict]:
    """§5 step 1's subject: every frozen source this closure came from.

    Two files, in the order they are consulted — the registration manifest
    that pins which worlds exist, then the registration this closure was
    built from. The checker reloads and digest-checks each entry before
    trusting anything else in the object, so an entry listed here is a
    promise the builder makes and the checker independently collects on.
    """

    registration_path = _registration_path(registration)
    manifest_path = registration_path.parent / "manifest.json"
    return [
        _manifest_entry(manifest_path, repo_root),
        _manifest_entry(registration_path, repo_root),
    ]


# ---------------------------------------------------------------------------
# The builder's own traversal
# ---------------------------------------------------------------------------


def _traverse(
    adapter,
    actions: tuple[tuple[str, dict[str, str]], ...],
    horizon: int,
    max_states: int,
) -> tuple[dict[str, dict], str]:
    """Level-synchronous breadth-first enumeration from the initial state.

    Written from §3 and §7 rather than from the checker's traversal, because
    the gate scores the agreement of two independent derivations.

    The bookkeeping argument, stated so it can be audited rather than
    trusted: the sweep advances one whole depth at a time, so a state first
    observed while expanding depth *d* cannot also be reachable in fewer
    than *d + 1* steps — every shorter route would have been walked in an
    earlier sweep. First observation is therefore minimum depth, and each
    state joins exactly one level's expansion set, so each is expanded once
    and carries exactly one row per enumerated action.

    States are expanded in ascending ``(depth, state_digest)`` order and
    actions in enumerated order, which makes the result a function of the
    frozen sources alone — no dictionary-iteration accident, and nothing an
    untrusted ordering could influence.

    Boundary states (``minimum_depth == horizon``) are never expanded. They
    keep an empty row set and make no claim about the next step; calling
    them exhausted is exactly the overreach §3 refuses.
    """

    initial_native = adapter.initial_state()
    initial_bytes = adapter.canonicalize(initial_native)
    initial_digest = sha256_hex(initial_bytes)

    records: dict[str, dict] = {
        initial_digest: {
            "canonical_state": initial_bytes.decode("utf-8"),
            "minimum_depth": 0,
            "outgoing": [],
        }
    }
    natives = {initial_digest: initial_native}

    depth = 0
    level = [initial_digest]
    while level and depth < horizon:
        discovered: list[str] = []
        for digest in sorted(level):
            rows: list[dict] = []
            for name, params in actions:
                action_text = canonical_action(name, params)
                outcome = adapter.validate_and_apply(
                    natives[digest], name, params
                )
                if isinstance(outcome, Refusal):
                    rows.append({
                        "canonical_action": action_text,
                        "disposition": "illegal",
                        "refusal_code": outcome.code,
                    })
                    continue
                successor_bytes = adapter.canonicalize(outcome)
                successor_digest = sha256_hex(successor_bytes)
                if successor_digest not in records:
                    if len(records) + 1 > max_states:
                        raise StateCeilingExceeded(
                            f"ceilings.max_states: the reachable graph "
                            f"exceeds the registered ceiling of "
                            f"{max_states} distinct states"
                        )
                    records[successor_digest] = {
                        "canonical_state": successor_bytes.decode("utf-8"),
                        "minimum_depth": depth + 1,
                        "outgoing": [],
                    }
                    natives[successor_digest] = outcome
                    discovered.append(successor_digest)
                rows.append({
                    "canonical_action": action_text,
                    "disposition": "successor",
                    "successor_digest": successor_digest,
                })
            records[digest]["outgoing"] = rows
        level = discovered
        depth += 1

    return records, initial_digest


def _accepted_incoming(records: dict[str, dict]) -> dict[str, list[tuple]]:
    """Accepted edges indexed by the state they land on, canonically ordered.

    Refusals are edges of the closure but not of the graph: they record what
    the world declined, and nothing arrives at a state by being refused.
    """

    incoming: dict[str, list[tuple[str, str]]] = {
        digest: [] for digest in records
    }
    for source, record in records.items():
        for row in record["outgoing"]:
            if row["disposition"] != "successor":
                continue
            incoming[row["successor_digest"]].append(
                (source, row["canonical_action"])
            )
    for digest in incoming:
        incoming[digest].sort()
    return incoming


def _convergence_cells(
    records: dict[str, dict],
    incoming: dict[str, list[tuple[str, str]]],
    initial_digest: str,
    horizon: int,
) -> list[dict]:
    """§6: one bounded, deterministic alternate route per converged state.

    Derived here independently, and derived again by the checker, which is
    the only reason a cell in a committed file means anything. The rule, read
    off the design text:

    1. A state's **primary predecessor** is the lexicographically first
       ``(predecessor_digest, canonical_action)`` among the accepted incoming
       edges that establish its minimum depth. Following primary predecessors
       from the initial state spells its canonical shortest route.
    2. Its **alternate** is the first other accepted incoming edge — same
       ordering — whose predecessor's minimum depth plus one is within the
       horizon and whose reconstructed route differs from the primary one.
    3. Exactly one cell per end state, or none when no alternate exists.

    Routes are built in ascending ``(depth, digest)`` order so a predecessor's
    route is always already spelled when its successor needs it.

    Two routes ending in equal bytes demonstrate only that the registered
    operations commute on that case. They do not establish that the routes
    have the same informal meaning, and §6 refuses to read one into them.
    """

    routes: dict[str, list[str]] = {initial_digest: []}
    primary_edge: dict[str, tuple[str, str]] = {}
    by_depth_then_digest = sorted(
        records,
        key=lambda digest: (records[digest]["minimum_depth"], digest),
    )
    for digest in by_depth_then_digest:
        if digest == initial_digest:
            continue
        depth = records[digest]["minimum_depth"]
        establishing = [
            edge for edge in incoming[digest]
            if records[edge[0]]["minimum_depth"] + 1 == depth
        ]
        if not establishing:
            # No witness at the previous depth. The builder does not repair
            # this; the checker rejects such a state outright, and hiding it
            # here would only move the failure somewhere less legible.
            continue
        source, action_text = establishing[0]
        primary_edge[digest] = (source, action_text)
        routes[digest] = routes[source] + [action_text]

    cells: list[dict] = []
    for digest in sorted(records):
        if digest == initial_digest or digest not in routes:
            continue
        primary_route = routes[digest]
        for source, action_text in incoming[digest]:
            if (source, action_text) == primary_edge.get(digest):
                continue
            if records[source]["minimum_depth"] + 1 > horizon:
                continue
            if source not in routes:
                continue
            alternate_route = routes[source] + [action_text]
            if alternate_route == primary_route:
                continue
            cells.append({
                "start_state_digest": initial_digest,
                "primary_route": primary_route,
                "alternate_route": alternate_route,
                "end_state_digest": digest,
            })
            break
    cells.sort(key=lambda cell: cell["end_state_digest"])
    return cells


# ---------------------------------------------------------------------------
# The registered entry point
# ---------------------------------------------------------------------------


def build_closure(registration: dict, repo_root: Path) -> dict:
    """Compile one world's complete bounded closure, goal-free.

    No desired endpoint, success predicate, reward, query text, or model
    score enters this function — there is nowhere for one to enter. The
    closure is sealed before anybody names a target, which is the ordering
    discipline §2 kept from the declined experiment: seal the possibility
    space before selecting a persuasive target.
    """

    adapter = closure_worlds.load_world(registration)
    horizon = registration["horizon"]
    ceilings = registration["ceilings"]

    actions = enumerate_actions(registration["action_schema"])
    if len(actions) > ceilings["max_actions_per_state"]:
        raise ActionCeilingExceeded(
            f"ceilings.max_actions_per_state: the registered schema "
            f"enumerates {len(actions)} syntactic actions per interior "
            f"state, above the ceiling of "
            f"{ceilings['max_actions_per_state']}"
        )

    records, initial_digest = _traverse(
        adapter, actions, horizon, ceilings["max_states"]
    )
    incoming = _accepted_incoming(records)
    cells = _convergence_cells(records, incoming, initial_digest, horizon)

    states = []
    for digest in sorted(records):
        record = records[digest]
        states.append({
            "state_digest": digest,
            "canonical_state": record["canonical_state"],
            "minimum_depth": record["minimum_depth"],
            "outgoing": sorted(
                record["outgoing"],
                key=lambda row: row["canonical_action"],
            ),
        })

    closure = {
        "format_version": FORMAT_VERSION,
        "world_id": registration["world_id"],
        "source_manifest": _source_manifest(registration, repo_root),
        "adapter_id": registration["adapter_id"],
        "adapter_digest": closure_worlds.adapter_digest(),
        "action_schema_digest": sha256_hex(
            canonical_json(registration["action_schema"]).encode("utf-8")
        ),
        "horizon": horizon,
        "initial_state_digest": initial_digest,
        "states": states,
        "convergence_cells": cells,
    }
    closure["closure_digest"] = closure_digest(closure)
    return closure


# ---------------------------------------------------------------------------
# CLI: build, refuse, then submit to the independent checker
# ---------------------------------------------------------------------------


def _serialize(closure: dict) -> str:
    """The committed file's spelling: readable, sorted, newline-terminated.

    Distinct from :func:`canonical_closure_bytes`, which is what the digest
    is taken over. The file is indented so a reader can audit it; the digest
    is taken over the compact canonical form so that a reorder of rows or
    object keys — §9's class 12 — normalizes to identical bytes.
    """

    return json.dumps(
        closure, indent=2, sort_keys=True, ensure_ascii=False
    ) + "\n"


def _build_one(registration: dict, repo_root: Path) -> tuple[dict, float, int]:
    started = time.monotonic()
    closure = build_closure(registration, repo_root)
    elapsed = time.monotonic() - started
    size = len(canonical_closure_bytes(closure))
    ceilings = registration["ceilings"]
    if size > ceilings["max_closure_bytes"]:
        raise ClosureSizeExceeded(
            f"ceilings.max_closure_bytes: the canonical closure is {size} "
            f"bytes, above the ceiling of {ceilings['max_closure_bytes']}"
        )
    if elapsed > ceilings["max_seconds_per_closure"]:
        raise BuildTooSlow(
            f"ceilings.max_seconds_per_closure: the build took "
            f"{elapsed:.3f}s, above the ceiling of "
            f"{ceilings['max_seconds_per_closure']}s"
        )
    return closure, elapsed, size


def main(argv: list[str] | None = None) -> int:
    """Build every committed registration, then hand each to the checker.

    The build is not the result. The last thing this command does is give
    its own output to the independent checker and print that verdict, and it
    exits nonzero when any world disagrees — a builder that reported success
    on its own authority would be asserting exactly the thing §5 refuses to
    let it assert.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Compile the bounded closure of every registered world, refuse "
            "any that crosses a frozen ceiling, and report the independent "
            "checker's verdict on each."
        )
    )
    parser.add_argument(
        "--out-dir", type=Path, default=OUTPUT_DIR,
        help="directory for <world_id>.closure.json (default: %(default)s)",
    )
    arguments = parser.parse_args(argv)

    # Imported here, in the command rather than in the builder: the CLI is
    # allowed to run the adjudication, while `build_closure` above must not
    # borrow the checker's traversal, comparison, or cell derivation.
    from closure_check import check_closure, load_closure  # noqa: PLC0415

    arguments.out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for path in closure_worlds.registration_paths():
        registration = closure_worlds.load_registration(path)
        world_id = registration["world_id"]
        try:
            closure, elapsed, size = _build_one(registration, REPO)
        except CeilingExceeded as refusal:
            failures += 1
            print(f"{world_id}: REFUSED {refusal}")
            continue

        destination = arguments.out_dir / f"{world_id}.closure.json"
        destination.write_text(_serialize(closure), encoding="utf-8")

        report = check_closure(
            load_closure(destination), registration, REPO
        )
        boundary = sum(
            1 for state in closure["states"]
            if state["minimum_depth"] >= registration["horizon"]
        )
        print(
            f"{world_id}: ok={report.ok} "
            f"states={len(closure['states'])} "
            f"(interior={len(closure['states']) - boundary}, "
            f"boundary={boundary}) "
            f"cells={len(closure['convergence_cells'])} "
            f"seconds={elapsed:.3f} "
            f"canonical_bytes={size} "
            f"closure_digest={closure['closure_digest']}"
        )
        print(f"  wrote {destination.relative_to(REPO).as_posix()}")
        if not report.ok:
            failures += 1
            print(f"  first_disagreement: {report.first_disagreement}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
