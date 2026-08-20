#!/usr/bin/env python3
"""DESIGN-compile-before-query §5 made executable: the independent checker.

The builder is untrusted. The closure file is untrusted. Every controller,
policy, search routine, and future model in this repository is untrusted.
This module therefore does not audit a closure for internal consistency —
that would only re-hash the builder's own claims, which §9 names vacuous. It
**rebuilds the reachable graph from the frozen sources** and then demands
exact bidirectional equality with the file: same state digests, same
canonical bytes, same minimum depths, the same canonically ordered
action/refusal/successor row for every interior state, the same predecessor
witnesses, the same convergence cells, and the same closure digest. A
missing edge, an extra state, a relabelled key, or a route that the graph
does not support all land as one *named first disagreement*.

What this module is allowed to touch, and what it is not:

* It MAY call a world's own verifier and canonicalizer, through the adapter
  contract in :mod:`closure_worlds`, selected only by the registration's
  declared ``adapter_id``. Duplicating a world's semantics here would create
  a second, unblessed definition of legality and would defeat the point.
* It MUST NOT import the builder, a controller, a search policy, or any
  adapter method that filters legal actions. It enumerates the schema
  product itself (:func:`enumerate_actions`) precisely so that a builder
  which quietly conceals an inconvenient move is caught by arithmetic rather
  than by trust.
* It contains no world-name conditional. That prohibition is mechanical:
  ``tests/test_bounded_closure.py`` scans this file's source text for world
  names and fails if one appears.

:func:`enumerate_actions` and :func:`canonical_closure_bytes` are public and
are imported *by the builder* rather than reimplemented there. Two spellings
of the action product, or two spellings of the canonical form, would be two
places for the gate to disagree with itself; there is exactly one of each,
and it lives on the checking side of the trust boundary.
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "experiments"))

import closure_worlds  # noqa: E402
from closure_worlds import (  # noqa: E402
    Refusal,
    canonical_action,
    canonical_json,
    sha256_hex,
    sha256_lf_file,
)

DIGEST_KEY = "closure_digest"


@dataclass(frozen=True)
class CheckReport:
    """The whole verdict: one boolean and one sentence naming the break.

    ``first_disagreement`` is deliberately a single sentence rather than a
    list. §5 asks for *the* named first disagreement, and a checker that
    returned every downstream consequence of one corruption would let a
    reader mistake noise for severity.
    """

    ok: bool
    first_disagreement: str | None
    derived_states: int
    derived_cells: int


def enumerate_actions(
    action_schema: list[dict],
) -> tuple[tuple[str, dict[str, str]], ...]:
    """The complete syntactic action product, in registration order.

    Families in declared list order; within a family the parameters vary
    rightmost-fastest over their declared value lists. This is a pure data
    transform with no filtering whatsoever: an action the world will always
    refuse still appears here, because the closure records refusals as
    edges and a missing row is exactly the corruption class 2 forgery.
    """

    actions: list[tuple[str, dict[str, str]]] = []
    for family in action_schema:
        parameters = family["parameters"]
        names = [parameter["name"] for parameter in parameters]
        domains = [parameter["values"] for parameter in parameters]
        for combination in itertools.product(*domains):
            actions.append((family["name"], dict(zip(names, combination))))
    return tuple(actions)


def canonical_closure_bytes(closure: dict) -> bytes:
    """The one serialization a closure is digested through.

    Tables are sorted so that a semantics-preserving reorder (corruption
    class 12) normalizes to identical bytes, while genuinely ordered data —
    convergence routes and the source manifest — is left exactly as
    written. Sorting a route would erase the difference between two ways of
    reaching a state, which is the one thing §6 exists to record.
    """

    normalized = copy.deepcopy(closure)
    normalized.pop(DIGEST_KEY, None)
    states = sorted(
        normalized.get("states", []),
        key=lambda state: state["state_digest"],
    )
    for state in states:
        state["outgoing"] = sorted(
            state.get("outgoing", []),
            key=lambda row: row["canonical_action"],
        )
    normalized["states"] = states
    normalized["convergence_cells"] = sorted(
        normalized.get("convergence_cells", []),
        key=lambda cell: cell["end_state_digest"],
    )
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def closure_digest(closure: dict) -> str:
    return sha256_hex(canonical_closure_bytes(closure))


def load_closure(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _row_identity(row: dict) -> tuple[str, str, str]:
    """An outgoing row reduced to what it actually asserts.

    Disposition and payload travel together: turning a refusal into a
    successor (class 4) must not be able to hide behind a leftover field.
    """

    action = str(row.get("canonical_action"))
    disposition = str(row.get("disposition"))
    if disposition == "successor":
        return (action, disposition, str(row.get("successor_digest")))
    return (action, disposition, str(row.get("refusal_code")))


def _rows_in_canonical_order(rows: list[dict]) -> list[tuple[str, str, str]]:
    return sorted(_row_identity(row) for row in rows)


def _fail(message: str, states: int = 0, cells: int = 0) -> CheckReport:
    return CheckReport(False, message, states, cells)


def _check_frozen_context(
    closure: dict, registration: dict, repo_root: Path
) -> str | None:
    """§5 step 1: nothing else is worth checking until the sources match."""

    for entry in closure.get("source_manifest", []):
        path = repo_root / entry["path"]
        if not path.is_file():
            return (
                f"source_manifest: expected a readable frozen source at "
                f"{entry['path']}, found no such file"
            )
        found = sha256_lf_file(path)
        if found != entry["sha256_lf"]:
            return (
                f"source_manifest[{entry['path']}].sha256_lf: expected "
                f"{entry['sha256_lf']}, found {found}"
            )
    expected_adapter = closure_worlds.adapter_digest()
    if closure.get("adapter_digest") != expected_adapter:
        return (
            f"adapter_digest: expected {expected_adapter}, found "
            f"{closure.get('adapter_digest')}"
        )
    if closure.get("adapter_id") != registration["adapter_id"]:
        return (
            f"adapter_id: expected {registration['adapter_id']!r}, found "
            f"{closure.get('adapter_id')!r}"
        )
    if closure.get("horizon") != registration["horizon"]:
        return (
            f"horizon: expected {registration['horizon']}, found "
            f"{closure.get('horizon')}"
        )
    expected_schema = sha256_hex(
        canonical_json(registration["action_schema"]).encode("utf-8")
    )
    if closure.get("action_schema_digest") != expected_schema:
        return (
            f"action_schema_digest: expected {expected_schema}, found "
            f"{closure.get('action_schema_digest')}"
        )
    return None


def _traverse(adapter, actions, horizon: int, max_states: int):
    """§5 steps 4-6: the checker's own canonical breadth-first traversal.

    States are processed in ascending ``(depth, state_digest)`` order and
    actions in enumerated order, which together make the derived graph a
    function of the frozen sources alone — no builder ordering, no dict
    iteration accident, nothing the untrusted side can influence.

    Returns ``(derived, initial_digest, ceiling_message)``.
    """

    initial_native = adapter.initial_state()
    initial_bytes = adapter.canonicalize(initial_native)
    initial_digest = sha256_hex(initial_bytes)

    derived: dict[str, dict] = {
        initial_digest: {
            "canonical_state": initial_bytes.decode("utf-8"),
            "minimum_depth": 0,
            "outgoing": [],
        }
    }
    native = {initial_digest: initial_native}
    frontier = [initial_digest]

    while frontier:
        successors: list[str] = []
        for digest in sorted(frontier):
            depth = derived[digest]["minimum_depth"]
            if depth >= horizon:
                continue
            rows: list[dict] = []
            for name, params in actions:
                action_text = canonical_action(name, params)
                outcome = adapter.validate_and_apply(
                    native[digest], name, params
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
                if successor_digest not in derived:
                    derived[successor_digest] = {
                        "canonical_state": successor_bytes.decode("utf-8"),
                        "minimum_depth": depth + 1,
                        "outgoing": [],
                    }
                    native[successor_digest] = outcome
                    successors.append(successor_digest)
                    if len(derived) > max_states:
                        return (
                            derived,
                            initial_digest,
                            f"ceilings.max_states: the reachable graph "
                            f"exceeds the registered ceiling of "
                            f"{max_states} distinct states",
                        )
                rows.append({
                    "canonical_action": action_text,
                    "disposition": "successor",
                    "successor_digest": successor_digest,
                })
            derived[digest]["outgoing"] = rows
        frontier = successors

    return derived, initial_digest, None


def _incoming_edges(derived: dict[str, dict]) -> dict[str, list[tuple]]:
    """Accepted edges, indexed by the state they land on."""

    incoming: dict[str, list[tuple[str, str]]] = {
        digest: [] for digest in derived
    }
    for source, record in derived.items():
        for row in record["outgoing"]:
            if row["disposition"] != "successor":
                continue
            incoming[row["successor_digest"]].append(
                (source, row["canonical_action"])
            )
    for digest in incoming:
        incoming[digest].sort()
    return incoming


def _derive_cells(
    derived: dict[str, dict],
    incoming: dict[str, list[tuple[str, str]]],
    initial_digest: str,
    horizon: int,
) -> list[dict]:
    """§6: at most one bounded, deterministic alternate route per state.

    The closure never enumerates all paths — it retains the canonical
    shortest route and the first differing alternate, both derived here so
    that the builder cannot omit, inject, or cherry-pick a cell. Two routes
    ending in equal bytes demonstrate only that the registered operations
    commute on that case; nothing here claims they mean the same thing.
    """

    routes: dict[str, list[str]] = {initial_digest: []}
    ordered = sorted(
        derived,
        key=lambda digest: (derived[digest]["minimum_depth"], digest),
    )
    primary_edge: dict[str, tuple[str, str]] = {}
    for digest in ordered:
        if digest == initial_digest:
            continue
        depth = derived[digest]["minimum_depth"]
        parents = [
            edge for edge in incoming[digest]
            if derived[edge[0]]["minimum_depth"] + 1 == depth
        ]
        if not parents:
            continue
        source, action_text = parents[0]
        primary_edge[digest] = (source, action_text)
        routes[digest] = routes.get(source, []) + [action_text]

    cells: list[dict] = []
    for digest in sorted(derived):
        if digest == initial_digest or digest not in routes:
            continue
        primary_route = routes[digest]
        for source, action_text in incoming[digest]:
            if (source, action_text) == primary_edge.get(digest):
                continue
            if derived[source]["minimum_depth"] + 1 > horizon:
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


def check_closure(
    closure: dict, registration: dict, repo_root: Path
) -> CheckReport:
    """Rebuild the world's bounded closure and demand it match, exactly.

    The nine steps run in §5's order and return at the FIRST disagreement,
    so the reported sentence names the cause rather than a consequence of
    it. A ``CheckReport`` with ``ok`` true asserts one narrow thing: the
    committed file is exactly what this versioned adapter, verifier, and
    frozen source snapshot produce within the registered horizon. It
    asserts nothing about mathematical truth, physical realism, or the
    completeness of the authored rules.
    """

    context_failure = _check_frozen_context(closure, registration, repo_root)
    if context_failure is not None:
        return _fail(context_failure)

    adapter = closure_worlds.load_world(registration)
    horizon = registration["horizon"]
    ceilings = registration["ceilings"]

    initial_bytes = adapter.canonicalize(adapter.initial_state())
    initial_digest = sha256_hex(initial_bytes)
    if closure.get("initial_state_digest") != initial_digest:
        return _fail(
            f"initial_state_digest: expected {initial_digest}, found "
            f"{closure.get('initial_state_digest')}"
        )
    by_digest: dict[str, dict] = {}
    for record in closure.get("states", []):
        digest = record["state_digest"]
        if digest in by_digest:
            return _fail(
                f"states[{digest}]: expected one record per state digest, "
                f"found a duplicate record"
            )
        by_digest[digest] = record
    initial_record = by_digest.get(initial_digest)
    if initial_record is None:
        return _fail(
            f"states[{initial_digest}]: expected a record for the "
            f"regenerated initial state, found none"
        )
    if initial_record["minimum_depth"] != 0:
        return _fail(
            f"states[{initial_digest}].minimum_depth: expected 0, found "
            f"{initial_record['minimum_depth']}"
        )
    if initial_record["canonical_state"].encode("utf-8") != initial_bytes:
        return _fail(
            f"states[{initial_digest}].canonical_state: expected the "
            f"regenerated initial state's canonical bytes, found different "
            f"bytes under the same digest"
        )

    actions = enumerate_actions(registration["action_schema"])
    if len(actions) > ceilings["max_actions_per_state"]:
        return _fail(
            f"ceilings.max_actions_per_state: expected at most "
            f"{ceilings['max_actions_per_state']} syntactic actions per "
            f"interior state, found {len(actions)}"
        )

    derived, initial_digest, ceiling_failure = _traverse(
        adapter, actions, horizon, ceilings["max_states"]
    )
    if ceiling_failure is not None:
        return _fail(ceiling_failure, len(derived))
    derived_count = len(derived)

    missing = sorted(set(derived) - set(by_digest))
    if missing:
        return _fail(
            f"states: expected a record for reachable state {missing[0]}, "
            f"found none",
            derived_count,
        )
    extra = sorted(set(by_digest) - set(derived))
    if extra:
        return _fail(
            f"states[{extra[0]}]: expected no such state, found a record "
            f"for a state the frozen sources do not reach",
            derived_count,
        )

    for digest in sorted(derived):
        record = by_digest[digest]
        expected = derived[digest]
        if record["canonical_state"] != expected["canonical_state"]:
            return _fail(
                f"states[{digest}].canonical_state: expected the bytes the "
                f"world's canonicalizer produced, found different bytes "
                f"under the same digest",
                derived_count,
            )
        if record["minimum_depth"] != expected["minimum_depth"]:
            return _fail(
                f"states[{digest}].minimum_depth: expected "
                f"{expected['minimum_depth']}, found "
                f"{record['minimum_depth']}",
                derived_count,
            )
        found_rows = _rows_in_canonical_order(record.get("outgoing", []))
        expected_rows = _rows_in_canonical_order(expected["outgoing"])
        if found_rows != expected_rows:
            if expected["minimum_depth"] >= horizon and found_rows:
                return _fail(
                    f"states[{digest}].outgoing: expected an empty row set "
                    f"for a boundary state at depth {horizon}, found "
                    f"{len(found_rows)} rows",
                    derived_count,
                )
            return _fail(
                _name_row_disagreement(digest, expected_rows, found_rows),
                derived_count,
            )

    incoming = _incoming_edges(derived)
    for digest in sorted(derived):
        if digest == initial_digest:
            continue
        depth = derived[digest]["minimum_depth"]
        witnesses = [
            edge for edge in incoming[digest]
            if derived[edge[0]]["minimum_depth"] + 1 == depth
        ]
        if not witnesses:
            return _fail(
                f"states[{digest}]: expected a predecessor edge at depth "
                f"{depth - 1} witnessing its minimum depth, found none",
                derived_count,
            )

    expected_cells = _derive_cells(
        derived, incoming, initial_digest, horizon
    )
    found_cells = closure.get("convergence_cells", [])
    cell_failure = _name_cell_disagreement(expected_cells, found_cells)
    if cell_failure is not None:
        return _fail(cell_failure, derived_count, len(expected_cells))

    expected_digest = closure_digest(closure)
    if closure.get(DIGEST_KEY) != expected_digest:
        return _fail(
            f"closure_digest: expected {expected_digest}, found "
            f"{closure.get(DIGEST_KEY)}",
            derived_count,
            len(expected_cells),
        )

    return CheckReport(True, None, derived_count, len(expected_cells))


def _name_row_disagreement(
    digest: str,
    expected_rows: list[tuple[str, str, str]],
    found_rows: list[tuple[str, str, str]],
) -> str:
    """Turn a row-set difference into one sentence about one row."""

    expected_by_action = {row[0]: row for row in expected_rows}
    found_by_action = {row[0]: row for row in found_rows}
    for action_text in sorted(expected_by_action):
        if action_text not in found_by_action:
            return (
                f"states[{digest}].outgoing[{action_text}]: expected a row "
                f"for this enumerated action, found none"
            )
    for action_text in sorted(found_by_action):
        if action_text not in expected_by_action:
            return (
                f"states[{digest}].outgoing[{action_text}]: expected no "
                f"such row, found one for an action outside the enumerated "
                f"product"
            )
    for action_text in sorted(expected_by_action):
        expected_row = expected_by_action[action_text]
        found_row = found_by_action[action_text]
        if expected_row != found_row:
            return (
                f"states[{digest}].outgoing[{action_text}]: expected "
                f"({expected_row[1]}, {expected_row[2]}), found "
                f"({found_row[1]}, {found_row[2]})"
            )
    return (
        f"states[{digest}].outgoing: expected {len(expected_rows)} rows, "
        f"found {len(found_rows)}"
    )


def _name_cell_disagreement(
    expected_cells: list[dict], found_cells: list[dict]
) -> str | None:
    """Turn a cell-set difference into one sentence about one cell."""

    expected_by_end = {
        cell["end_state_digest"]: cell for cell in expected_cells
    }
    found_by_end: dict[str, dict] = {}
    for cell in found_cells:
        end = cell.get("end_state_digest")
        if end in found_by_end:
            return (
                f"convergence_cells[{end}]: expected at most one cell per "
                f"end state, found a duplicate"
            )
        found_by_end[end] = cell
    for end in sorted(expected_by_end):
        if end not in found_by_end:
            return (
                f"convergence_cells[{end}]: expected a cell for this "
                f"convergence, found none"
            )
    for end in sorted(found_by_end):
        if end not in expected_by_end:
            return (
                f"convergence_cells[{end}]: expected no cell for this end "
                f"state, found one"
            )
    for end in sorted(expected_by_end):
        expected_cell = expected_by_end[end]
        found_cell = found_by_end[end]
        for field in (
            "start_state_digest", "primary_route", "alternate_route",
        ):
            if expected_cell[field] != found_cell.get(field):
                return (
                    f"convergence_cells[{end}].{field}: expected "
                    f"{canonical_json(expected_cell[field])}, found "
                    f"{canonical_json(found_cell.get(field))}"
                )
    if len(found_cells) != len(expected_cells):
        return (
            f"convergence_cells: expected {len(expected_cells)} cells, "
            f"found {len(found_cells)}"
        )
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild a bounded closure from its frozen sources and report "
            "the first disagreement with the committed file."
        )
    )
    parser.add_argument("closure", type=Path)
    parser.add_argument("registration", type=Path)
    arguments = parser.parse_args(argv)

    closure = load_closure(arguments.closure)
    registration = closure_worlds.load_registration(arguments.registration)
    report = check_closure(closure, registration, REPO)
    print(f"ok: {report.ok}")
    print(f"derived_states: {report.derived_states}")
    print(f"derived_cells: {report.derived_cells}")
    if report.first_disagreement is not None:
        print(f"first_disagreement: {report.first_disagreement}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
