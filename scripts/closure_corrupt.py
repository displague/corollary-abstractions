#!/usr/bin/env python3
"""DESIGN-compile-before-query §9 made executable: the corruption battery.

Twelve named mutation classes, frozen at preregistration so that no class
can later be tuned to whatever a future builder happens to emit. That
ordering is the entire point of committing this file before
``scripts/closure_build.py`` exists: a battery written after the artifact
tests the artifact's habits, while a battery written before it tests the
checker's completeness. Classes 1-11 must each be rejected with a named
first disagreement; class 12 must normalize to identical bytes and an
identical closure digest, because reordering rows or object keys changes
nothing a closure asserts.

Two disciplines make the battery reproducible rather than merely random:

* Site selection is a pure function of ``(kind, seed)`` over candidates
  collected in canonical order — states by digest, rows by canonical
  action — so the same closure and seed always corrupt the same row, on any
  platform, in any interpreter session.
* :func:`corrupt` never mutates its argument. It returns a deep copy, or
  ``None`` when the closure genuinely offers no site for a class (no
  convergence cells, no accepted edges). ``None`` is an honest "this class
  does not apply here", and the gate records it as such rather than
  counting an absent mutation as a catch.

Ordered semantic lists are never shuffled. Routes are sequences of actions;
the source manifest is the order the sources were frozen in. Class 12
touches neither, and no class rewrites a string except where its own
definition says so.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

CLASSES: tuple[str, ...] = (
    "delete_legal_action_row",
    "conceal_schema_action",
    "change_successor",
    "refusal_marked_legal",
    "remove_interior_state",
    "alter_manifest_field",
    "omit_interior_frontier",
    "change_lookup_key",
    "inject_unreachable_state",
    "corrupt_one_convergence_route",
    "replace_alternate_route",
    "semantic_preserving_reorder",
)

INJECTED_MARKER = "|injected-unreachable"
INJECTED_REFUSAL = "injected"


def _site(kind: str, seed: int, count: int) -> int:
    """Pick one candidate site deterministically.

    md5 for determinism only, never for integrity — the same reason this
    repository's dataset-split helper uses it: ``hash()`` is
    process-randomized and would make a registered seed meaningless.
    """

    if count <= 0:
        raise ValueError("no candidate sites")
    digest = hashlib.md5(f"{kind}:{seed}".encode()).hexdigest()
    return int(digest, 16) % count


def _states_in_order(closure: dict) -> list[dict]:
    return sorted(closure["states"], key=lambda s: s["state_digest"])


def _rows_in_order(state: dict) -> list[dict]:
    return sorted(state["outgoing"], key=lambda r: r["canonical_action"])


def _drop_row(state: dict, row: dict) -> None:
    state["outgoing"] = [r for r in state["outgoing"] if r is not row]


def _flip_hex(value: str, position: int = 0) -> str:
    """Change one hex character, keeping the field's shape valid.

    A malformed digest would be caught by schema validation alone; the
    battery is only interesting when the forgery is well-formed.
    """

    original = value[position]
    replacement = "1" if original == "0" else "0"
    return value[:position] + replacement + value[position + 1:]


def _all_digests(closure: dict) -> list[str]:
    return sorted(state["state_digest"] for state in closure["states"])


def _all_actions(closure: dict) -> list[str]:
    actions = {
        row["canonical_action"]
        for state in closure["states"]
        for row in state["outgoing"]
    }
    for cell in closure.get("convergence_cells", []):
        actions.update(cell.get("primary_route", []))
        actions.update(cell.get("alternate_route", []))
    return sorted(actions)


def _reverse_key_order(value):
    """Rebuild every mapping with reversed insertion order.

    Lists keep their order here: reversing a route or the source manifest
    would change meaning, and class 12 is defined as the mutation that
    changes none.
    """

    if isinstance(value, dict):
        return {
            key: _reverse_key_order(item)
            for key, item in reversed(list(value.items()))
        }
    if isinstance(value, list):
        return [_reverse_key_order(item) for item in value]
    return value


def _delete_legal_action_row(closure: dict, kind: str, seed: int):
    candidates = [
        (state, row)
        for state in _states_in_order(closure)
        for row in _rows_in_order(state)
        if row.get("disposition") == "successor"
    ]
    if not candidates:
        return None
    state, row = candidates[_site(kind, seed, len(candidates))]
    _drop_row(state, row)
    return closure


def _conceal_schema_action(closure: dict, kind: str, seed: int):
    candidates = [
        (state, row)
        for state in _states_in_order(closure)
        for row in _rows_in_order(state)
    ]
    if not candidates:
        return None
    state, row = candidates[_site(kind, seed, len(candidates))]
    _drop_row(state, row)
    return closure


def _change_successor(closure: dict, kind: str, seed: int):
    candidates = [
        row
        for state in _states_in_order(closure)
        for row in _rows_in_order(state)
        if row.get("disposition") == "successor"
    ]
    if not candidates:
        return None
    row = candidates[_site(kind, seed, len(candidates))]
    alternatives = [
        digest for digest in _all_digests(closure)
        if digest != row["successor_digest"]
    ]
    if alternatives:
        row["successor_digest"] = alternatives[0]
    else:
        row["successor_digest"] = hashlib.sha256(
            f"{kind}:{seed}:{row['successor_digest']}".encode()
        ).hexdigest()
    return closure


def _refusal_marked_legal(closure: dict, kind: str, seed: int):
    candidates = [
        row
        for state in _states_in_order(closure)
        for row in _rows_in_order(state)
        if row.get("disposition") == "illegal"
    ]
    if not candidates:
        return None
    digests = _all_digests(closure)
    if not digests:
        return None
    row = candidates[_site(kind, seed, len(candidates))]
    row.pop("refusal_code", None)
    row["disposition"] = "successor"
    row["successor_digest"] = digests[0]
    return closure


def _remove_interior_state(closure: dict, kind: str, seed: int):
    horizon = closure["horizon"]
    initial = closure["initial_state_digest"]
    candidates = [
        state for state in _states_in_order(closure)
        if state["minimum_depth"] < horizon
        and state["state_digest"] != initial
    ]
    if not candidates:
        # A world whose only interior state is the initial one still has a
        # removable interior record; the class is not vacuous there.
        candidates = [
            state for state in _states_in_order(closure)
            if state["minimum_depth"] < horizon
        ]
    if not candidates:
        return None
    victim = candidates[_site(kind, seed, len(candidates))]
    closure["states"] = [s for s in closure["states"] if s is not victim]
    return closure


def _alter_manifest_field(closure: dict, kind: str, seed: int):
    sites: list[tuple[str, int]] = [("horizon", 0), ("adapter_digest", 0)]
    sites.extend(
        ("source_manifest", index)
        for index in range(len(closure.get("source_manifest", [])))
    )
    field, index = sites[_site(kind, seed, len(sites))]
    if field == "horizon":
        closure["horizon"] = closure["horizon"] + 1
    elif field == "adapter_digest":
        closure["adapter_digest"] = _flip_hex(closure["adapter_digest"])
    else:
        entry = closure["source_manifest"][index]
        entry["sha256_lf"] = _flip_hex(entry["sha256_lf"])
    return closure


def _omit_interior_frontier(closure: dict, kind: str, seed: int):
    horizon = closure["horizon"]
    candidates = [
        state for state in _states_in_order(closure)
        if state["minimum_depth"] < horizon and state["outgoing"]
    ]
    if not candidates:
        return None
    state = candidates[_site(kind, seed, len(candidates))]
    state["outgoing"] = []
    return closure


def _change_lookup_key(closure: dict, kind: str, seed: int):
    candidates = _states_in_order(closure)
    if not candidates:
        return None
    taken = set(_all_digests(closure))
    state = candidates[_site(kind, seed, len(candidates))]
    for position in range(len(state["state_digest"])):
        relabelled = _flip_hex(state["state_digest"], position)
        if relabelled not in taken:
            state["state_digest"] = relabelled
            return closure
    return None


def _inject_unreachable_state(closure: dict, kind: str, seed: int):
    candidates = _states_in_order(closure)
    if not candidates:
        return None
    template = candidates[_site(kind, seed, len(candidates))]
    canonical_state = template["canonical_state"] + INJECTED_MARKER
    digest = hashlib.sha256(canonical_state.encode("utf-8")).hexdigest()
    if digest in set(_all_digests(closure)):
        return None
    depth = 1
    if depth >= closure["horizon"]:
        outgoing: list[dict] = []
    else:
        outgoing = [
            {
                "canonical_action": action,
                "disposition": "illegal",
                "refusal_code": INJECTED_REFUSAL,
            }
            for action in _all_actions(closure)
        ]
    closure["states"].append({
        "state_digest": digest,
        "canonical_state": canonical_state,
        "minimum_depth": depth,
        "outgoing": outgoing,
    })
    return closure


def _corrupt_one_convergence_route(closure: dict, kind: str, seed: int):
    candidates = [
        cell for cell in sorted(
            closure.get("convergence_cells", []),
            key=lambda c: c["end_state_digest"],
        )
        if cell.get("alternate_route")
    ]
    if not candidates:
        return None
    vocabulary = _all_actions(closure)
    cell = candidates[_site(kind, seed, len(candidates))]
    original = cell["alternate_route"][0]
    replacements = [a for a in vocabulary if a != original]
    if not replacements:
        return None
    cell["alternate_route"][0] = replacements[0]
    return closure


def _replace_alternate_route(closure: dict, kind: str, seed: int):
    cells = closure.get("convergence_cells", [])
    if not cells:
        return None
    ordered = sorted(cells, key=lambda c: c["end_state_digest"])
    victim = ordered[_site(kind, seed, len(ordered))]
    closure["convergence_cells"] = [c for c in cells if c is not victim]
    return closure


def _semantic_preserving_reorder(closure: dict, kind: str, seed: int):
    closure["states"] = list(reversed(closure["states"]))
    for state in closure["states"]:
        state["outgoing"] = list(reversed(state["outgoing"]))
    closure["convergence_cells"] = list(
        reversed(closure.get("convergence_cells", []))
    )
    return _reverse_key_order(closure)


_MUTATIONS = {
    "delete_legal_action_row": _delete_legal_action_row,
    "conceal_schema_action": _conceal_schema_action,
    "change_successor": _change_successor,
    "refusal_marked_legal": _refusal_marked_legal,
    "remove_interior_state": _remove_interior_state,
    "alter_manifest_field": _alter_manifest_field,
    "omit_interior_frontier": _omit_interior_frontier,
    "change_lookup_key": _change_lookup_key,
    "inject_unreachable_state": _inject_unreachable_state,
    "corrupt_one_convergence_route": _corrupt_one_convergence_route,
    "replace_alternate_route": _replace_alternate_route,
    "semantic_preserving_reorder": _semantic_preserving_reorder,
}


def corrupt(closure: dict, kind: str, seed: int) -> dict | None:
    """Return one deep-copied, singly-mutated closure, or ``None``.

    The input is never touched. ``None`` means the closure offers no site
    for this class, which the gate must record and skip rather than score:
    a battery that silently counted an inapplicable class as caught would
    inflate exactly the number §8's clause B4 is trying to keep honest.
    """

    if kind not in _MUTATIONS:
        raise ValueError(f"unregistered corruption class {kind!r}")
    return _MUTATIONS[kind](copy.deepcopy(closure), kind, seed)


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 4:
        print(
            "usage: closure_corrupt.py <closure.json> <kind> <seed> "
            "<out.json>",
            file=sys.stderr,
        )
        return 2
    source, kind, seed, destination = arguments
    closure = json.loads(Path(source).read_text(encoding="utf-8"))
    mutated = corrupt(closure, kind, int(seed))
    if mutated is None:
        print(f"no candidate site for {kind!r} in {source}")
        return 1
    Path(destination).write_text(
        json.dumps(mutated, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {destination} ({kind}, seed {seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
