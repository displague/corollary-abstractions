#!/usr/bin/env python3
"""Seed the committed query targets for the `reachable` line route (W2).

``closure_query.query`` refuses approximate targets by design: it takes the
target's *exact canonical bytes* and nothing weaker. A typed line therefore
cannot carry a target — it can only name a file that already holds those
bytes. This script is the authored source of those files, and it obeys two
rules that keep them from being decoration:

* **The bytes come from the adapter, never from the closure file.** Every
  target is produced by replaying a route through the world's OWN registered
  adapter and calling that adapter's ``canonicalize``. Copying
  ``canonical_state`` out of the closure would make the query a comparison of
  a file with itself, and the ``CORRUPT_TARGET`` arm would become
  unreachable-by-construction rather than unreached-in-fact.

* **Every target is verified against the arm it is filed under, and a
  disagreement aborts the whole run.** A ``reachable`` file whose query says
  ``NOT_REACHABLE_WITHIN_HORIZON`` (or the reverse) is not written and not
  quietly refiled; the script exits 2 with the mismatch named. A target set
  that can silently relabel itself is a task book grading its own answers.

The NOT-reachable arm is generated rather than invented: from a frontier
state (one at ``minimum_depth == horizon``) the script asks the adapter for
one more accepted transition, which lands on a *valid* state of the world
that the closure — bounded at that horizon — does not contain. That is a
real negative about a real state, not a corrupted byte string, so the
``reachable`` route's ``exhausted`` arm cannot become self-fulfilling.

Byte-idempotent by house rule (``check_regeneration.py`` runs every
``scripts/seed_*.py`` and reports any resulting diff under ``data/`` as
DRIFT): every choice below is a total order over committed data, so two runs
on two hosts write the same bytes.

Known shortfall, recorded in the manifest rather than padded around: §9's
floors apply *per world where the adapter affords them*, and a world whose
closure holds a single state with no accepted transition (today
``visual.rt0000``: horizon 1, one state, all six mutations refused by
``visual.verify``) affords exactly ONE reachable target and NO unreachable
one. The script writes what the world genuinely affords and records the
count, because manufacturing a second visual state would mean inventing a
transition its own verifier rejects.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "experiments"))

import closure_check  # noqa: E402
import closure_query  # noqa: E402
import closure_worlds  # noqa: E402
from closure_worlds import Refusal  # noqa: E402

OUT_DIR = REPO / "data" / "closure_targets"
MANIFEST_PATH = OUT_DIR / "manifest.json"
CLOSURE_DIR = REPO / "reports" / "closures"

SCHEMA_TAG = "closure-target-manifest/1"
SEED_SCRIPT = "scripts/seed_closure_targets.py"

REACHABLE_ARM = "reachable"
UNREACHABLE_ARM = "unreachable"

#: Per-world ceilings. The floors live in the spec — §9 asks for ">= 3
#: reachable and >= 2 not-reachable targets per world WHERE THE ADAPTER
#: AFFORDS THEM", so a world whose verifier admits no such state records the
#: shortfall (:func:`build_world`) instead of having one manufactured for it,
#: and the NOT_REACHABLE arm is carried by the worlds that afford it.
REACHABLE_TARGETS = 5
UNREACHABLE_TARGETS = 2

#: The §9 floors themselves, as data, so the shortfall test is the spec's
#: numbers rather than two literals drifting inside a conditional.
REACHABLE_FLOOR = 3
UNREACHABLE_FLOOR = 2


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def closure_path(world_id: str) -> Path:
    return CLOSURE_DIR / f"{world_id}.closure.json"


def replay_to_state(adapter, route: list[str]):
    """Walk one canonical route through the adapter, returning its endpoint.

    Raises on a refusal: the route came from the closure's own accepted
    edges, so a refusal here means the closure and the adapter disagree, and
    a target derived from that disagreement would name neither.
    """

    state = adapter.initial_state()
    for index, action_text in enumerate(route):
        action = json.loads(action_text)
        outcome = adapter.validate_and_apply(
            state, action["name"], action["params"]
        )
        if isinstance(outcome, Refusal):
            raise RuntimeError(
                f"route[{index}] {action_text}: the closure records this "
                f"action as accepted, the adapter refused it with "
                f"{outcome.code!r}"
            )
        state = outcome
    return state


def reachable_digests(closure: dict) -> list[str]:
    """Recorded state digests to draw reachable targets from, round-robin
    over depth so a target set is not five spellings of the same depth.

    Total order: depths ascending, digests ascending within a depth, one per
    depth per pass. The initial state is therefore always target 0 and the
    routes lengthen from there.
    """

    by_depth: dict[int, list[str]] = {}
    for record in closure["states"]:
        by_depth.setdefault(record["minimum_depth"], []).append(
            record["state_digest"]
        )
    for digests in by_depth.values():
        digests.sort()
    chosen: list[str] = []
    position = 0
    while len(chosen) < REACHABLE_TARGETS:
        added = False
        for depth in sorted(by_depth):
            if position < len(by_depth[depth]):
                chosen.append(by_depth[depth][position])
                added = True
                if len(chosen) == REACHABLE_TARGETS:
                    break
        if not added:
            break
        position += 1
    return chosen


def beyond_horizon_states(
    closure: dict, registration: dict, adapter
) -> list[bytes]:
    """Canonical bytes of valid states the closure's horizon excludes.

    One accepted transition out of a frontier state. Frontier states are
    taken in ascending digest order and the world's action product in
    registration order, so the first `UNREACHABLE_TARGETS` distinct
    successors are a function of committed data alone.
    """

    horizon = closure["horizon"]
    recorded = {record["state_digest"] for record in closure["states"]}
    routes = closure_query.canonical_routes(closure)
    frontier = sorted(
        record["state_digest"]
        for record in closure["states"]
        if record["minimum_depth"] == horizon
    )
    actions = closure_check.enumerate_actions(registration["action_schema"])
    found: list[bytes] = []
    seen: set[str] = set()
    for digest in frontier:
        route = routes.get(digest)
        if route is None:
            continue
        state = replay_to_state(adapter, route)
        for name, params in actions:
            outcome = adapter.validate_and_apply(state, name, params)
            if isinstance(outcome, Refusal):
                continue
            candidate = adapter.canonicalize(outcome)
            candidate_digest = sha256_hex(candidate)
            if candidate_digest in recorded or candidate_digest in seen:
                continue
            seen.add(candidate_digest)
            found.append(candidate)
            if len(found) == UNREACHABLE_TARGETS:
                return found
    return found


def target_path(world_id: str, arm: str, index: int) -> Path:
    return OUT_DIR / f"{world_id}.{arm}.{index}.state.json"


def build_world(world_id: str, registration: dict) -> tuple[list[dict], dict]:
    """Every target for one world, each verified against its own arm."""

    path = closure_path(world_id)
    if not path.is_file():
        raise SystemExit(
            f"REFUSING: {world_id} is registered but no sealed closure "
            f"exists at {path.relative_to(REPO).as_posix()}"
        )
    closure = closure_check.load_closure(path)
    adapter = closure_worlds.load_world(registration)
    routes = closure_query.canonical_routes(closure)

    entries: list[dict] = []
    for index, digest in enumerate(reachable_digests(closure)):
        payload = adapter.canonicalize(replay_to_state(adapter, routes[digest]))
        entries.append(_verified(world_id, REACHABLE_ARM, index, payload,
                                 closure, registration))
    for index, payload in enumerate(
        beyond_horizon_states(closure, registration, adapter)
    ):
        entries.append(_verified(world_id, UNREACHABLE_ARM, index, payload,
                                 closure, registration))

    counts = {
        REACHABLE_ARM: sum(1 for e in entries if e["arm"] == REACHABLE_ARM),
        UNREACHABLE_ARM: sum(
            1 for e in entries if e["arm"] == UNREACHABLE_ARM
        ),
    }
    summary = {
        "world_id": world_id,
        "closure": path.relative_to(REPO).as_posix(),
        "horizon": closure["horizon"],
        "visited_states": len(closure["states"]),
        "reachable_targets": counts[REACHABLE_ARM],
        "unreachable_targets": counts[UNREACHABLE_ARM],
    }
    if (
        counts[REACHABLE_ARM] < REACHABLE_FLOOR
        or counts[UNREACHABLE_ARM] < UNREACHABLE_FLOOR
    ):
        summary["shortfall"] = (
            f"this world affords {counts[REACHABLE_ARM]} reachable and "
            f"{counts[UNREACHABLE_ARM]} unreachable target(s), short of the "
            f"spec §9 floors ({REACHABLE_FLOOR}/{UNREACHABLE_FLOOR}), which "
            f"apply per world where the adapter affords them; its closure "
            f"holds {len(closure['states'])} state(s) within horizon "
            f"{closure['horizon']} and no further state is accepted by its "
            f"own verifier"
        )
    return entries, summary


ARM_OUTCOME = {
    REACHABLE_ARM: closure_query.REACHABLE,
    UNREACHABLE_ARM: closure_query.NOT_REACHABLE,
}


def _verified(
    world_id: str,
    arm: str,
    index: int,
    payload: bytes,
    closure: dict,
    registration: dict,
) -> dict:
    """One target entry, or an abort. The query decides the arm, not the
    derivation that produced the bytes."""

    receipt = closure_query.query(closure, registration, payload, REPO)
    expected = ARM_OUTCOME[arm]
    if receipt["outcome"] != expected:
        print(
            f"REFUSING to write {target_path(world_id, arm, index).name}: "
            f"expected outcome {expected}, the query answered "
            f"{receipt['outcome']}"
        )
        raise SystemExit(2)
    path = target_path(world_id, arm, index)
    path.write_bytes(payload)
    entry = {
        "arm": arm,
        "index": index,
        "path": path.relative_to(REPO).as_posix(),
        "sha256": sha256_hex(payload),
        "seed_script": SEED_SCRIPT,
        "world_id": world_id,
    }
    if arm == REACHABLE_ARM:
        entry["route_length"] = len(receipt["shortest_route"])
    return entry


def render(obj: dict) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files: list[dict] = []
    worlds: list[dict] = []
    for path in closure_worlds.registration_paths():
        registration = closure_worlds.load_registration(path)
        entries, summary = build_world(registration["world_id"], registration)
        files.extend(entries)
        worlds.append(summary)

    keep = {entry["path"] for entry in files} | {
        MANIFEST_PATH.relative_to(REPO).as_posix()
    }
    for stale in sorted(OUT_DIR.iterdir()):
        if stale.relative_to(REPO).as_posix() in keep:
            continue
        if not stale.is_file():
            # This script owns files in its directory, not trees. Removing a
            # directory it did not create would be a deletion nobody asked
            # for, so it is named and left alone.
            print(f"NOT a generated target, left in place: {stale.name}")
            continue
        stale.unlink()

    manifest = {
        "files": sorted(files, key=lambda e: e["path"]),
        "generated_by": SEED_SCRIPT,
        "schema": SCHEMA_TAG,
        "worlds": worlds,
    }
    MANIFEST_PATH.write_bytes(render(manifest).encode("utf-8"))
    print(
        f"wrote {len(files)} target(s) for {len(worlds)} world(s) to "
        f"{OUT_DIR.relative_to(REPO).as_posix()}"
    )
    for summary in worlds:
        note = summary.get("shortfall")
        print(
            f"  {summary['world_id']}: "
            f"{summary['reachable_targets']} reachable, "
            f"{summary['unreachable_targets']} unreachable"
            + (f" — {note}" if note else "")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
