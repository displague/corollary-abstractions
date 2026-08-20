#!/usr/bin/env python3
"""DESIGN-compile-before-query §3 and §7 made executable: the query side.

One sealed closure, one exact canonical target, one answer. The answer is
either a **shortest replayable action sequence** or a **bounded negative that
cannot be quoted without its bound** — and there is deliberately no third
vocabulary item for an unrestricted "no".

Four commitments this module keeps, each of which is the reason a line of it
exists rather than a decoration on one:

* **The closure answers only if it is still the closure it says it is.**
  Before a single byte of the target is examined, the stored
  ``closure_digest`` is recomputed from the file's own contents, the frozen
  sources named in its ``source_manifest`` are re-hashed, and the adapter
  code is re-digested. A corrupt or drifted closure answers nothing: it
  raises. A receipt quotes a digest as the name of what was consulted, and a
  name that does not match the thing is worse than no answer at all.

* **Presence requires bytes AND digest together.** A state record whose
  digest equals the target's but whose canonical bytes differ is §3's named
  corruption case, returned as ``CORRUPT_TARGET`` with no route. The query
  layer cannot rebuild the world — that is :mod:`closure_check`'s job — so
  the one internal inconsistency it *can* see, it refuses rather than
  answers.

* **A returned route is replayed before it is claimed.** The route is
  derived from the closure's own accepted edges, but the closure is
  untrusted (§5), so the route is then walked through the world's OWN
  verifier via the registered adapter, from the regenerated initial state,
  and the final canonical bytes must equal the target's. A mismatch raises;
  it never becomes a receipt that says ``REACHABLE``. Emitting an
  unreplayable route would make the receipt a claim about a file instead of
  a claim about a world.

* **The negative keeps its bound attached.** ``NOT_REACHABLE_WITHIN_HORIZON``
  is the only negative available, and the display prints the horizon, the
  visited-state count, the closure digest, the snapshot files, and the
  native verifier's adapter id in the same breath. Nothing here can be
  truthfully quoted as an unqualified impossibility claim, because nothing
  here says one.

This module is part of the generic layer: it contains no world-name
conditional and reaches an adapter only through the registration's declared
``adapter_id`` via :func:`closure_worlds.load_world`, which is §5's one
sanctioned selection mechanism.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "experiments"))

import closure_check  # noqa: E402
import closure_worlds  # noqa: E402
from closure_worlds import Refusal, sha256_hex, sha256_lf_file  # noqa: E402

RECEIPT_SCHEMA_TAG = "closure-receipt/1"

REACHABLE = "REACHABLE"
NOT_REACHABLE = "NOT_REACHABLE_WITHIN_HORIZON"
CORRUPT_TARGET = "CORRUPT_TARGET"


class QueryRefused(RuntimeError):
    """The query was not answered, and no receipt was written.

    Distinct from ``CORRUPT_TARGET``, which IS an answer: that outcome says
    the closure holds an internally inconsistent record for these exact
    bytes. The exceptions below say the closure or its context is not in a
    condition to be asked anything at all, so returning any receipt — even a
    negative one — would attach a digest to a claim it does not cover.
    """


class CorruptClosure(QueryRefused):
    """The stored ``closure_digest`` is not the digest of these contents."""


class StaleSnapshot(QueryRefused):
    """A frozen source, or the adapter code, has drifted since the seal.

    Replay runs against the CURRENT registration and the CURRENT adapter. If
    either has moved, a ``REACHABLE`` receipt naming the sealed closure would
    be reporting a walk through a different world than the one the closure
    was compiled from.
    """


class WrongWorld(QueryRefused):
    """The supplied registration is not the one this closure was built from."""


class ReplayDisagreement(QueryRefused):
    """The world's own verifier did not reproduce the route's endpoint.

    Raised instead of emitting a ``REACHABLE`` receipt: an unreplayable
    route is the one failure mode a query can detect on its own, and a
    receipt is worth exactly as much as its worst undetected claim.
    """


# ---------------------------------------------------------------------------
# Refusals that precede any answer
# ---------------------------------------------------------------------------


def _refuse_unless_sealed(closure: dict, repo_root: Path) -> None:
    """Recompute everything the receipt is about to quote as a name.

    A receipt names four things it did not itself derive: the closure
    digest, the snapshot files, the adapter, and the horizon. Three of them
    are checkable here in microseconds against the very bytes on disk, and a
    name that goes unchecked is a citation, not evidence.
    """

    recomputed = closure_check.closure_digest(closure)
    stored = closure.get(closure_check.DIGEST_KEY)
    if stored != recomputed:
        raise CorruptClosure(
            f"closure_digest: expected {recomputed}, found {stored} — a "
            f"closure that is not the closure it names answers nothing"
        )
    for entry in closure.get("source_manifest", []):
        path = repo_root / entry["path"]
        if not path.is_file():
            raise StaleSnapshot(
                f"source_manifest: expected a readable frozen source at "
                f"{entry['path']}, found no such file"
            )
        found = sha256_lf_file(path)
        if found != entry["sha256_lf"]:
            raise StaleSnapshot(
                f"source_manifest[{entry['path']}].sha256_lf: expected "
                f"{entry['sha256_lf']}, found {found}"
            )
    expected_adapter = closure_worlds.adapter_digest()
    if closure.get("adapter_digest") != expected_adapter:
        raise StaleSnapshot(
            f"adapter_digest: expected {expected_adapter}, found "
            f"{closure.get('adapter_digest')} — replay would run through "
            f"different code than the closure was compiled from"
        )


def _refuse_unless_same_world(closure: dict, registration: dict) -> None:
    if closure.get("world_id") != registration.get("world_id"):
        raise WrongWorld(
            f"world_id: the closure declares "
            f"{closure.get('world_id')!r} and the registration declares "
            f"{registration.get('world_id')!r}"
        )
    if closure.get("adapter_id") != registration.get("adapter_id"):
        raise WrongWorld(
            f"adapter_id: the closure declares "
            f"{closure.get('adapter_id')!r} and the registration declares "
            f"{registration.get('adapter_id')!r}"
        )


# ---------------------------------------------------------------------------
# The canonical shortest route
# ---------------------------------------------------------------------------


def accepted_edges(closure: dict) -> dict[str, list[tuple[str, str]]]:
    """Accepted edges per state, in canonical ``canonical_action`` order.

    Refusal rows are edges of the closure but not of the graph: nothing
    arrives anywhere by being declined, so a refusal can never appear in a
    route.
    """

    edges: dict[str, list[tuple[str, str]]] = {}
    for record in closure.get("states", []):
        rows = sorted(
            (row["canonical_action"], row["successor_digest"])
            for row in record.get("outgoing", [])
            if row.get("disposition") == "successor"
        )
        edges[record["state_digest"]] = rows
    return edges


def canonical_routes(closure: dict) -> dict[str, list[str]]:
    """Breadth-first shortest routes from the initial state, one per state.

    The tie-break is total and stated rather than incidental: within a
    level-synchronous sweep, states are expanded in ascending
    ``state_digest`` order and their accepted rows in ascending
    ``canonical_action`` order, so the first discovery of a state fixes its
    route. Two runs, two machines, and two readers therefore get the same
    route for the same closure — a "shortest" route chosen by dictionary
    iteration order would be shortest but not canonical, and a receipt
    quoting it could not be reproduced from the file.

    This is the same rule the checker uses to spell a convergence cell's
    primary route (lexicographically first establishing edge), reached by
    breadth-first sweep rather than by importing it: the query side must not
    inherit the derivation whose output it is reporting.
    """

    initial = closure["initial_state_digest"]
    edges = accepted_edges(closure)
    routes: dict[str, list[str]] = {initial: []}
    level = [initial]
    while level:
        discovered: list[str] = []
        for digest in sorted(level):
            for action_text, successor in edges.get(digest, ()):
                if successor in routes:
                    continue
                routes[successor] = routes[digest] + [action_text]
                discovered.append(successor)
        level = discovered
    return routes


def replay(registration: dict, route: list[str], target_bytes: bytes) -> None:
    """Walk the route through the world's own verifier, or raise.

    The closure is untrusted. This function asks the registered adapter —
    the same code path the builder and the checker used — to regenerate the
    initial state and apply each canonical action in order, and demands that
    the final canonicalization equal the supplied target byte for byte. It
    returns nothing on success because it asserts nothing beyond that.
    """

    adapter = closure_worlds.load_world(registration)
    state = adapter.initial_state()
    for index, action_text in enumerate(route):
        action = json.loads(action_text)
        outcome = adapter.validate_and_apply(
            state, action["name"], action["params"]
        )
        if isinstance(outcome, Refusal):
            raise ReplayDisagreement(
                f"shortest_route[{index}] {action_text}: the closure records "
                f"this action as accepted, the world's own verifier refused "
                f"it with {outcome.code!r}"
            )
        state = outcome
    found = adapter.canonicalize(state)
    if found != target_bytes:
        raise ReplayDisagreement(
            f"shortest_route: replaying {len(route)} action(s) through the "
            f"world's own verifier produced "
            f"{sha256_hex(found)}, not the target {sha256_hex(target_bytes)}"
        )


# ---------------------------------------------------------------------------
# The query
# ---------------------------------------------------------------------------


def query(
    closure: dict,
    registration: dict,
    target_bytes: bytes,
    repo_root: Path,
) -> dict:
    """Ask one sealed closure about one exact canonical target state.

    ``target_bytes`` are the target's canonical bytes exactly as the world's
    canonicalizer would spell them — not a description, not a pattern, not a
    partial state. §3 gives the query no vocabulary for approximate targets
    on purpose: an approximate match would need a similarity judgement, and
    every such judgement in this repository is exactly the untrusted kind of
    claim the closure exists to avoid.

    Returns a receipt conforming to ``schema/closure-receipt.schema.json``.
    Raises :class:`QueryRefused` — never returns a receipt — when the
    closure is not intact, the registration is the wrong world, or a route
    the closure asserts fails to replay through the world's own verifier.
    """

    _refuse_unless_sealed(closure, repo_root)
    _refuse_unless_same_world(closure, registration)

    target_digest = sha256_hex(target_bytes)
    receipt = {
        "schema": RECEIPT_SCHEMA_TAG,
        "world_id": closure["world_id"],
        "closure_digest": closure[closure_check.DIGEST_KEY],
        "horizon": closure["horizon"],
        "visited_states": len(closure["states"]),
        "adapter_id": closure["adapter_id"],
        "target_digest": target_digest,
        "outcome": NOT_REACHABLE,
    }

    record = None
    for candidate in closure["states"]:
        if candidate["state_digest"] == target_digest:
            record = candidate
            break

    if record is None:
        # The bound travels with this answer everywhere it is displayed or
        # serialized; there is no outcome value here that omits it.
        return receipt

    if record["canonical_state"].encode("utf-8") != target_bytes:
        # §3: "A digest match with unequal canonical bytes is refused as
        # corruption." Not answered as present, not answered as absent.
        receipt["outcome"] = CORRUPT_TARGET
        return receipt

    routes = canonical_routes(closure)
    if target_digest not in routes:
        # A recorded state that no accepted edge reaches from the initial
        # state. The checker rejects such a closure outright; here it means
        # the query cannot offer a replayable route, and an unreplayable
        # "present" would be worth nothing.
        raise ReplayDisagreement(
            f"states[{target_digest}]: the closure records this state but no "
            f"accepted edge path reaches it from the initial state"
        )

    route = routes[target_digest]
    replay(registration, route, target_bytes)
    receipt["outcome"] = REACHABLE
    receipt["shortest_route"] = route
    return receipt


# ---------------------------------------------------------------------------
# The §7 display
# ---------------------------------------------------------------------------


def display_lines(
    receipt: dict, closure: dict, closure_path: Path | None = None
) -> list[str]:
    """§7's display: the answer, never separable from what bounded it.

    Snapshot files, horizon, visited-state count, closure digest, and the
    native verifier's adapter id are printed for every outcome, including
    the positive one. The negative is spelled "not reachable within horizon
    N" and the word for an unrestricted negative does not appear in this
    module's vocabulary at all — not as a fallback, not as a comment on the
    outcome, not as prose a reader could lift out of the block and quote.
    """

    lines: list[str] = []
    if closure_path is not None:
        lines.append(f"closure: {closure_path.as_posix()}")
    lines.append(f"world_id: {receipt['world_id']}")
    lines.append("snapshot:")
    for entry in closure.get("source_manifest", []):
        lines.append(f"  {entry['path']}  sha256_lf={entry['sha256_lf']}")
    lines.append(f"horizon: {receipt['horizon']}")
    lines.append(f"visited_states: {receipt['visited_states']}")
    lines.append(f"closure_digest: {receipt['closure_digest']}")
    lines.append(f"adapter_id: {receipt['adapter_id']}")
    lines.append(f"target_digest: {receipt['target_digest']}")
    lines.append(f"outcome: {receipt['outcome']}")

    if receipt["outcome"] == REACHABLE:
        route = receipt.get("shortest_route", [])
        lines.append(f"shortest_route: {len(route)} action(s), replayed "
                     f"through the world's own verifier")
        for step, action_text in enumerate(route, start=1):
            lines.append(f"  {step}. {action_text}")
        if not route:
            lines.append("  (the target IS the initial state)")
    elif receipt["outcome"] == NOT_REACHABLE:
        lines.append(
            f"these canonical bytes are not reachable within horizon "
            f"{receipt['horizon']} of the closure named above, which visited "
            f"{receipt['visited_states']} states"
        )
        lines.append(
            "that is the whole claim: it is bounded by this snapshot, this "
            "adapter, and this horizon, and says nothing about longer routes"
        )
    else:
        lines.append(
            "a state record carries this digest but different canonical "
            "bytes; a digest match with unequal canonical bytes is refused "
            "as corruption, not answered"
        )
    return lines


def serialize_receipt(receipt: dict) -> str:
    return json.dumps(receipt, indent=2, sort_keys=True,
                      ensure_ascii=False) + "\n"


def find_registration(world_id: str) -> dict:
    """The committed registration declaring this ``world_id``.

    Located through :func:`closure_worlds.registration_paths` — the
    manifest-pinned set — rather than by guessing a filename, so a query can
    only ever be answered against a registration the manifest covers.
    """

    for path in closure_worlds.registration_paths():
        registration = closure_worlds.load_registration(path)
        if registration["world_id"] == world_id:
            return registration
    raise WrongWorld(
        f"no committed registration declares world_id {world_id!r}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Ask one sealed bounded closure about one exact canonical "
            "target state, and print the answer with its bound attached."
        )
    )
    parser.add_argument("closure", type=Path)
    parser.add_argument(
        "target", type=Path,
        help="a file holding the target's exact canonical bytes",
    )
    parser.add_argument(
        "receipt", type=Path, nargs="?",
        help="optional path to write the receipt JSON to",
    )
    arguments = parser.parse_args(argv)

    closure = closure_check.load_closure(arguments.closure)
    registration = find_registration(closure["world_id"])
    target_bytes = arguments.target.read_bytes()

    receipt = query(closure, registration, target_bytes, REPO)

    path = arguments.closure.resolve()
    try:
        shown = path.relative_to(REPO)
    except ValueError:
        shown = path
    for line in display_lines(receipt, closure, shown):
        print(line)

    if arguments.receipt is not None:
        arguments.receipt.write_text(
            serialize_receipt(receipt), encoding="utf-8"
        )
        print(f"wrote {arguments.receipt.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
