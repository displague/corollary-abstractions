#!/usr/bin/env python3
"""The protocol corpus and its fixture seal, generated from one committed seed.

Design pointer: ``docs/DESIGN-protocol-uptake.md`` — §3 (the corpus is a
*generated* artifact whose source is this script, and whose output is
``protocol/protocols.json``, deliberately **outside** ``data/``: a node file
under ``data/*/nodes.json`` would silently join the boot corpus count, the
merged resolver graph, and every census over that graph), §6 step 2 (U-P0
seals the builder, its corpus, the regeneration checker, and the fixtures),
§7 B1/B2/B4. Stage: **U-P0**. Roadmap: ``docs/ROADMAP-v0.24.md#1``.
Surviving schema fields: ``experiments/protocol_uptake_upre.json``.

Nothing here is a runtime. ``scripts/protocol_runtime.py`` — the module that
will own the protocol stack — does not exist yet and U-P0 registers that it
must not. This script authors seed definitions and *derives* everything a
later runtime will be scored against.

The generation rule for the sealed 8×4 table — the **honest table**, never a
hand-written label::

    cell(surface, position) = the unique move family F such that the sealed
    corpus witnesses the normalized surface under F via an ENTRY move AND the
    position satisfies F's entry predicate, including its required absences.
    Zero matches is REFUSED.

Two matches is impossible because entry predicates are pairwise exclusive
across families on the four positions — and this script *asserts* that
exclusivity on the 32 rather than assuming it. Refusal fixtures, ASK
fixtures, equivalence fixtures, and every product cell's expectation are
computed from that same rule applied to the seed; the nested trajectories
author their dispositions and this script derives their episode ids, stack
snapshots, and next-state digests, then checks each authored move is the
*unique* corpus move whose predicate holds at that turn.

Predicate language: exact value equality on signal values, with the named
absence sentinel ``ABSENT``. ``protocol_stack``'s predicate value is the
top-summary token (``empty`` / ``top:<protocol_id>:active`` /
``top:<protocol_id>:suspended``); the full stack is receipt state, not a
predicate value.

Usage
-----

    python scripts/build_protocol_corpus.py
    python scripts/build_protocol_corpus.py --out protocol/protocols.json
    python scripts/build_protocol_corpus.py --fixtures experiments/protocol_uptake_fixtures.json
    python scripts/build_protocol_corpus.py --table
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO = Path(__file__).resolve().parents[1]

CORPUS_SCHEMA = "corollary.protocol-corpus/1"
FIXTURES_SCHEMA = "corollary.protocol-uptake-fixtures/1"
DESIGN = "docs/DESIGN-protocol-uptake.md"
ROADMAP = "docs/ROADMAP-v0.24.md#1"
UPRE = "experiments/protocol_uptake_upre.json"
GENERATOR = "scripts/build_protocol_corpus.py"
RUNTIME_MODULE = "scripts/protocol_runtime.py"

DEFAULT_CORPUS_OUT = "protocol/protocols.json"
DEFAULT_FIXTURES_OUT = "experiments/protocol_uptake_fixtures.json"

# --------------------------------------------------------------------------
# Vocabulary. Absence is a value, not a missing key (DESIGN §3).
# --------------------------------------------------------------------------

ABSENT = "ABSENT"
SET = "SET"
PROBE = "probe"
REFUSED = "REFUSED"

STACK_EMPTY = "empty"
STACK_DEPTH_CAP = 8

NORMALIZATION = "NFC + casefold + strip; every lookup key stored here is already normalized"
PREDICATE_LANGUAGE = (
    "exact value equality on signal values, with named absence sentinel ABSENT; "
    "protocol_stack's predicate value is the top-summary token"
)

# The five context signals and two witness fields that survived U-PRE. The two
# candidate fields that audit DELETED are named there and nowhere else — not
# even in a comment here, because "they appear nowhere" is checked by reading
# these files' bytes.
SIGNAL_IDS = (
    "pending_need",
    "quote_boundary",
    "expected_output_slot",
    "active_task",
    "protocol_stack",
)
NON_STACK_SIGNALS = SIGNAL_IDS[:4]
WITNESS_FIELDS = ("protocol_node_id", "relation")

MOVE_KINDS = ("entry", "continuation", "resume", "exit")
FAMILIES = ("greeting", "probe_reply", "quoted_datum", "expected_output")

NEXT_STATE_PROJECTION = ("protocol_id", "stack_after", "pending_request_id", "authority_delta")

SESSION_ROOT_EVENT = "evt-session-root"


class ConstructionRefusal(RuntimeError):
    """A seal that cannot be built honestly — DESIGN §10 BLOCKED CONSTRUCTION."""


# --------------------------------------------------------------------------
# Seed: the four context positions. The stack is empty in all four; a
# multi-turn fixture reuses a position's four non-stack values while the
# protocol_stack signal is derived from the trajectory.
# --------------------------------------------------------------------------

POSITION_SEED: tuple[dict[str, Any], ...] = (
    {
        "position_id": "fresh_root",
        "gloss": "no pending need, no quote boundary, no expected-output slot, empty protocol stack",
        "signals": {
            "pending_need": ABSENT,
            "quote_boundary": ABSENT,
            "expected_output_slot": ABSENT,
            "active_task": ABSENT,
        },
        "source_events": {
            "pending_need": SESSION_ROOT_EVENT,
            "quote_boundary": SESSION_ROOT_EVENT,
            "expected_output_slot": SESSION_ROOT_EVENT,
            "active_task": SESSION_ROOT_EVENT,
        },
        # The event `remove_context_event` deletes for this position.
        "position_event": SESSION_ROOT_EVENT,
    },
    {
        "position_id": "probe_outstanding",
        "gloss": "a live probe need",
        "signals": {
            "pending_need": PROBE,
            "quote_boundary": ABSENT,
            "expected_output_slot": ABSENT,
            "active_task": ABSENT,
        },
        "source_events": {
            "pending_need": "evt-probe-open",
            "quote_boundary": SESSION_ROOT_EVENT,
            "expected_output_slot": SESSION_ROOT_EVENT,
            "active_task": SESSION_ROOT_EVENT,
        },
        "position_event": "evt-probe-open",
    },
    {
        "position_id": "literal_slot",
        "gloss": "quote boundary set",
        "signals": {
            "pending_need": ABSENT,
            "quote_boundary": SET,
            "expected_output_slot": ABSENT,
            "active_task": ABSENT,
        },
        "source_events": {
            "pending_need": SESSION_ROOT_EVENT,
            "quote_boundary": "evt-quote-open",
            "expected_output_slot": SESSION_ROOT_EVENT,
            "active_task": SESSION_ROOT_EVENT,
        },
        "position_event": "evt-quote-open",
    },
    {
        "position_id": "programming_task",
        "gloss": "expected-output slot and active task set",
        "signals": {
            "pending_need": ABSENT,
            "quote_boundary": ABSENT,
            "expected_output_slot": SET,
            "active_task": SET,
        },
        "source_events": {
            "pending_need": SESSION_ROOT_EVENT,
            "quote_boundary": SESSION_ROOT_EVENT,
            "expected_output_slot": "evt-task-open",
            "active_task": "evt-task-open",
        },
        "position_event": "evt-task-open",
    },
)

POSITION_IDS = tuple(p["position_id"] for p in POSITION_SEED)


def _pred(*pairs: tuple[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(pairs)


# Entry predicates read only the four non-stack signals; continuation,
# resume, and exit predicates read only protocol_stack's top summary.
GREETING_ENTRY = _pred(
    ("pending_need", ABSENT), ("quote_boundary", ABSENT), ("expected_output_slot", ABSENT)
)
PROBE_ENTRY = _pred(("pending_need", PROBE))
QUOTED_ENTRY = _pred(("quote_boundary", SET))
OUTPUT_ENTRY = _pred(("expected_output_slot", SET), ("active_task", SET))


def _top(protocol_id: str, state: str) -> tuple[tuple[str, str], ...]:
    return _pred(("protocol_stack", f"top:{protocol_id}:{state}"))


# --------------------------------------------------------------------------
# Seed: seven protocol nodes, four move families, typed moves.
# --------------------------------------------------------------------------

NODE_SEED: tuple[dict[str, Any], ...] = (
    {
        "protocol_id": "protocol.greeting.a",
        "family": "greeting",
        "moves": (
            {
                "move_id": "greet",
                "kind": "entry",
                "keys": ("hello", "good morning", "hi", "greetings"),
                "predicate": GREETING_ENTRY,
            },
            {
                "move_id": "smalltalk",
                "kind": "continuation",
                "keys": ("how are you",),
                "predicate": _top("protocol.greeting.a", "active"),
            },
            {
                "move_id": "pick_up",
                "kind": "resume",
                "keys": ("how are you",),
                "predicate": _top("protocol.greeting.a", "suspended"),
            },
            {
                "move_id": "farewell",
                "kind": "exit",
                "keys": ("goodbye",),
                "predicate": _top("protocol.greeting.a", "active"),
            },
        ),
    },
    {
        "protocol_id": "protocol.greeting.b",
        "family": "greeting",
        "moves": (
            {
                "move_id": "acknowledge",
                "kind": "entry",
                "keys": ("hi", "greetings", "hey", "welcome"),
                "predicate": GREETING_ENTRY,
            },
            # Deliberately projection-identical to `acknowledge`: same node, so
            # same protocol_id, same push, same empty authority. This is the
            # equivalence pair section 4's proceed-without-asking rule needs.
            {
                "move_id": "greet_back",
                "kind": "entry",
                "keys": ("hey", "welcome"),
                "predicate": GREETING_ENTRY,
            },
        ),
    },
    {
        "protocol_id": "protocol.probe_reply.a",
        "family": "probe_reply",
        "moves": (
            {
                "move_id": "confirm_alive",
                "kind": "entry",
                "keys": ("hello", "still here", "ready", "yes"),
                "predicate": PROBE_ENTRY,
            },
        ),
    },
    {
        "protocol_id": "protocol.probe_reply.b",
        "family": "probe_reply",
        "moves": (
            {
                "move_id": "confirm_alive_alt",
                "kind": "entry",
                "keys": ("yes",),
                "predicate": PROBE_ENTRY,
            },
        ),
    },
    {
        "protocol_id": "protocol.quoted_datum.a",
        "family": "quoted_datum",
        "moves": (
            {
                "move_id": "accept_datum",
                "kind": "entry",
                "keys": ("hello world", "forty-two", "null"),
                "predicate": QUOTED_ENTRY,
            },
            {
                "move_id": "close_quote",
                "kind": "exit",
                "keys": ("end quote",),
                "predicate": _top("protocol.quoted_datum.a", "active"),
            },
        ),
    },
    {
        "protocol_id": "protocol.quoted_datum.b",
        "family": "quoted_datum",
        "moves": (
            {
                "move_id": "accept_datum_alt",
                "kind": "entry",
                "keys": ("null",),
                "predicate": QUOTED_ENTRY,
            },
        ),
    },
    {
        "protocol_id": "protocol.expected_output.a",
        "family": "expected_output",
        "moves": (
            {
                "move_id": "match_output",
                "kind": "entry",
                "keys": ("ready", "hello world", "ok", "done"),
                "predicate": OUTPUT_ENTRY,
            },
            {
                "move_id": "finish_task",
                "kind": "exit",
                "keys": ("that is all",),
                "predicate": _top("protocol.expected_output.a", "active"),
            },
        ),
    },
)

# The 8 product surfaces are the rows of the sealed table, in this order.
PRODUCT_SURFACES = (
    "hello",
    "good morning",
    "still here",
    "ready",
    "hello world",
    "forty-two",
    "ok",
    "done",
)

# ASK surfaces are extra sealed rows, disjoint from the 32 (DESIGN §6).
ASK_SURFACES = (
    ("hi", "fresh_root"),
    ("greetings", "fresh_root"),
    ("yes", "probe_outstanding"),
    ("null", "literal_slot"),
)

EQUIVALENCE_SURFACES = (
    ("hey", "fresh_root"),
    ("welcome", "fresh_root"),
)

# The position's home-family selected cell surface, per position: the surface
# each pair of refusal corruptions is applied to.
REFUSAL_HOME_SURFACE = {
    "fresh_root": "good morning",
    "probe_outstanding": "still here",
    "literal_slot": "forty-two",
    "programming_task": "done",
}

REFUSAL_CORRUPTIONS = ("remove_witness", "remove_context_event")

B8_SURFACE = "please enable write, python, and shell access"


# --------------------------------------------------------------------------
# Normalization, canonical JSON, digests, episode ids.
# --------------------------------------------------------------------------


def normalize(surface: str) -> str:
    """NFC, casefold, strip — the one channel a surface reaches the corpus by."""

    return unicodedata.normalize("NFC", surface).casefold().strip()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_canonical(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def episode_id(turn_index: int, protocol_id: str) -> str:
    """``ep-<turn_index>-<protocol_id>``, turn_index 1-based within a session."""

    return f"ep-{turn_index}-{protocol_id}"


def next_state_projection(protocol_id: str, stack_after: Sequence[str]) -> dict[str, Any]:
    """The exact four fields §6 step 2 seals. ``move_id`` is deliberately outside."""

    return {
        "protocol_id": protocol_id,
        "stack_after": list(stack_after),
        "pending_request_id": None,
        "authority_delta": [],
    }


def predicate_rows(pairs: Iterable[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"signal_id": s, "required_value": v} for s, v in pairs]


def context_signal_rows(
    position: dict[str, Any], stack_value: str, *, dropped_event: str | None = None
) -> list[dict[str, str]]:
    """The five signal rows for a turn.

    ``dropped_event`` models the ``remove_context_event`` corruption: signals
    sourced by that event are *absent from the map*, which is not the same
    thing as carrying the ABSENT sentinel, and no exact-value predicate over
    them can hold.
    """

    rows = []
    for signal_id in NON_STACK_SIGNALS:
        source = position["source_events"][signal_id]
        if dropped_event is not None and source == dropped_event:
            continue
        rows.append(
            {
                "signal_id": signal_id,
                "value": position["signals"][signal_id],
                "source_event_id": source,
            }
        )
    rows.append(
        {"signal_id": "protocol_stack", "value": stack_value, "source_event_id": "evt-protocol-stack"}
    )
    return rows


def signal_map(rows: Iterable[dict[str, str]]) -> dict[str, str]:
    return {row["signal_id"]: row["value"] for row in rows}


def predicate_holds(predicate: Iterable[dict[str, str]], signals: dict[str, str]) -> bool:
    """Exact value equality. A signal missing from the map cannot satisfy anything."""

    return all(
        row["signal_id"] in signals and signals[row["signal_id"]] == row["required_value"]
        for row in predicate
    )


# --------------------------------------------------------------------------
# The corpus.
# --------------------------------------------------------------------------


def build_corpus() -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    for seed in NODE_SEED:
        moves = []
        for move in seed["moves"]:
            keys = [normalize(k) for k in move["keys"]]
            if sorted(keys) != sorted(set(keys)):
                raise ConstructionRefusal(
                    f"{seed['protocol_id']}/{move['move_id']} repeats a lookup key"
                )
            if move["kind"] not in MOVE_KINDS:
                raise ConstructionRefusal(f"unknown move kind {move['kind']!r}")
            moves.append(
                {
                    "move_id": move["move_id"],
                    "kind": move["kind"],
                    "keys": keys,
                    "required_signal_predicates": predicate_rows(move["predicate"]),
                }
            )
        nodes.append(
            {"protocol_id": seed["protocol_id"], "family": seed["family"], "moves": moves}
        )

    # The witness channel: normalized surface -> witnesses. The witness pair
    # proper is (protocol_node_id, relation) — the two U-PRE survivors; the
    # move it names is carried beside it so the admission predicate never has
    # to touch the surface bytes again.
    lookup: dict[str, list[dict[str, str]]] = {}
    for node in nodes:
        for move in node["moves"]:
            for key in move["keys"]:
                lookup.setdefault(key, []).append(
                    {
                        "protocol_node_id": node["protocol_id"],
                        "relation": node["family"],
                        "move_id": move["move_id"],
                        "move_kind": move["kind"],
                    }
                )
    lookup = {
        key: sorted(entries, key=lambda e: (e["protocol_node_id"], e["move_id"]))
        for key, entries in sorted(lookup.items())
    }

    corpus = {
        "schema": CORPUS_SCHEMA,
        "design": DESIGN,
        "roadmap": ROADMAP,
        "stage": "U-P0",
        "generator": GENERATOR,
        "generated_note": (
            "Generated artifact. The seed in the generator is source truth; a direct "
            "edit of this file is a DESIGN §10 stop condition. Deliberately outside "
            "data/ so it joins no boot corpus count and no merged resolver graph."
        ),
        "runtime_module": RUNTIME_MODULE,
        "normalization": NORMALIZATION,
        "predicate_language": PREDICATE_LANGUAGE,
        "absence_sentinel": ABSENT,
        "context_signal_ids": list(SIGNAL_IDS),
        "protocol_witness_fields": list(WITNESS_FIELDS),
        "upre_note": (
            "the context signal ids and witness fields above are exactly U-PRE's "
            "survivors; the two fields U-PRE deleted are named there and appear "
            "nowhere here, not even as a list of what was removed"
        ),
        "move_kinds": list(MOVE_KINDS),
        "families": list(FAMILIES),
        "stack_depth_cap": STACK_DEPTH_CAP,
        "stack_top_summary_forms": [
            STACK_EMPTY,
            "top:<protocol_id>:active",
            "top:<protocol_id>:suspended",
        ],
        "nodes": nodes,
        "lookup": lookup,
    }
    _check_corpus_invariants(corpus)
    return corpus


def nodes_by_id(corpus: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {node["protocol_id"]: node for node in corpus["nodes"]}


def family_entry_predicate(corpus: dict[str, Any], family: str) -> list[dict[str, str]]:
    """One entry predicate per family, asserted well-defined across its nodes."""

    seen: list[list[dict[str, str]]] = []
    for node in corpus["nodes"]:
        if node["family"] != family:
            continue
        for move in node["moves"]:
            if move["kind"] == "entry":
                seen.append(move["required_signal_predicates"])
    if not seen:
        raise ConstructionRefusal(f"family {family!r} has no entry move")
    first = canonical_json(seen[0])
    for other in seen[1:]:
        if canonical_json(other) != first:
            raise ConstructionRefusal(
                f"family {family!r} has two different entry predicates; the honest "
                f"table's rule is a predicate per family"
            )
    return seen[0]


def witnessed_moves(corpus: dict[str, Any], surface: str) -> list[dict[str, str]]:
    return list(corpus["lookup"].get(normalize(surface), ()))


def entry_candidates(
    corpus: dict[str, Any],
    surface: str,
    signals: dict[str, str],
    *,
    drop_witness_nodes: frozenset[str] = frozenset(),
) -> list[dict[str, Any]]:
    """Every corpus-witnessed ENTRY move whose required predicates all hold."""

    index = nodes_by_id(corpus)
    out = []
    for witness in witnessed_moves(corpus, surface):
        if witness["move_kind"] != "entry":
            continue
        if witness["protocol_node_id"] in drop_witness_nodes:
            continue
        node = index[witness["protocol_node_id"]]
        move = next(m for m in node["moves"] if m["move_id"] == witness["move_id"])
        if predicate_holds(move["required_signal_predicates"], signals):
            out.append({"node": node, "move": move, "witness": witness})
    return sorted(out, key=lambda c: (c["node"]["protocol_id"], c["move"]["move_id"]))


def all_candidates(
    corpus: dict[str, Any], surface: str, signals: dict[str, str]
) -> list[dict[str, Any]]:
    """Every corpus-witnessed move of any kind whose predicates hold."""

    index = nodes_by_id(corpus)
    out = []
    for witness in witnessed_moves(corpus, surface):
        node = index[witness["protocol_node_id"]]
        move = next(m for m in node["moves"] if m["move_id"] == witness["move_id"])
        if predicate_holds(move["required_signal_predicates"], signals):
            out.append({"node": node, "move": move, "witness": witness})
    return sorted(out, key=lambda c: (c["node"]["protocol_id"], c["move"]["move_id"]))


def check_survivor_schema(document: Any, *, where: str) -> None:
    """Every schema field is a U-PRE survivor — checked positively.

    The audit deleted two input fields. This check is written as *membership in
    the survivor lists* rather than as a search for the deleted names, so no
    file in this slice ever has to spell a name that is supposed to appear
    nowhere; ``experiments/protocol_uptake_upre.json`` remains the one place
    they are written down.
    """

    if isinstance(document, dict):
        if "signal_id" in document and document["signal_id"] not in SIGNAL_IDS:
            raise ConstructionRefusal(
                f"{where}: signal id {document['signal_id']!r} is not one of U-PRE's "
                f"surviving context signals"
            )
        if "protocol_node_id" in document:
            extra = set(document) - set(WITNESS_FIELDS) - {"move_id", "move_kind"}
            if extra:
                raise ConstructionRefusal(
                    f"{where}: witness carries {sorted(extra)}, which U-PRE's surviving "
                    f"witness fields do not include"
                )
        for value in document.values():
            check_survivor_schema(value, where=where)
    elif isinstance(document, list):
        for value in document:
            check_survivor_schema(value, where=where)


def _check_corpus_invariants(corpus: dict[str, Any]) -> None:
    check_survivor_schema(corpus, where="corpus")

    # (a) each PRODUCT surface matches at most one node per family.
    for surface in PRODUCT_SURFACES:
        seen: dict[str, set[str]] = {}
        for witness in witnessed_moves(corpus, surface):
            if witness["move_kind"] != "entry":
                continue
            seen.setdefault(witness["relation"], set()).add(witness["protocol_node_id"])
        for family, node_ids in seen.items():
            if len(node_ids) > 1:
                raise ConstructionRefusal(
                    f"product surface {surface!r} matches {len(node_ids)} nodes in "
                    f"family {family!r}; a 32 cell could then become a two-next_state "
                    f"ASK the family-level rule would miss"
                )

    # (b) ASK and equivalence keys are disjoint from the 8 product surfaces.
    products = {normalize(s) for s in PRODUCT_SURFACES}
    extras = {normalize(s) for s, _ in ASK_SURFACES} | {
        normalize(s) for s, _ in EQUIVALENCE_SURFACES
    }
    overlap = products & extras
    if overlap:
        raise ConstructionRefusal(
            f"ASK/equivalence surfaces overlap the product surfaces: {sorted(overlap)}"
        )

    # (c) entry predicates are pairwise exclusive across families on the four
    #     positions. This is what makes "two matches" impossible on the 32.
    preds = {f: family_entry_predicate(corpus, f) for f in FAMILIES}
    for position in POSITION_SEED:
        signals = dict(position["signals"])
        signals["protocol_stack"] = STACK_EMPTY
        holding = [f for f in FAMILIES if predicate_holds(preds[f], signals)]
        if len(holding) > 1:
            raise ConstructionRefusal(
                f"entry predicates of {holding} both hold at "
                f"{position['position_id']!r}; the honest table's uniqueness fails"
            )


# --------------------------------------------------------------------------
# The sealed 8×4 table and its two view-ceilings.
# --------------------------------------------------------------------------


def build_table(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    positions = {p["position_id"]: p for p in POSITION_SEED}
    rows = []
    for row_index, surface in enumerate(PRODUCT_SURFACES, start=1):
        cells = []
        for col_index, position_id in enumerate(POSITION_IDS, start=1):
            position = positions[position_id]
            signals = dict(position["signals"])
            signals["protocol_stack"] = STACK_EMPTY
            matched = entry_candidates(corpus, surface, signals)
            families = sorted({c["node"]["family"] for c in matched})
            if len(families) > 1:
                raise ConstructionRefusal(
                    f"cell ({surface!r}, {position_id!r}) matches families {families}; "
                    f"pairwise exclusivity was supposed to make that impossible"
                )
            if not matched:
                cells.append(
                    {
                        "col": col_index,
                        "position_id": position_id,
                        "label": REFUSED,
                        "protocol_id": None,
                        "move_id": None,
                    }
                )
                continue
            if len(matched) != 1:
                raise ConstructionRefusal(
                    f"cell ({surface!r}, {position_id!r}) has {len(matched)} candidates; "
                    f"a 32 cell may not be materially ambiguous"
                )
            chosen = matched[0]
            cells.append(
                {
                    "col": col_index,
                    "position_id": position_id,
                    "label": chosen["node"]["family"],
                    "protocol_id": chosen["node"]["protocol_id"],
                    "move_id": chosen["move"]["move_id"],
                }
            )
        rows.append({"row": row_index, "surface": normalize(surface), "cells": cells})
    return rows


def table_labels(rows: list[dict[str, Any]]) -> list[list[str]]:
    return [[cell["label"] for cell in row["cells"]] for row in rows]


def c_surface(rows: list[dict[str, Any]]) -> int:
    """Cells the best function of surface alone matches: per row, the max multiplicity."""

    return sum(max(Counter(labels).values()) for labels in table_labels(rows))


def c_position(rows: list[dict[str, Any]]) -> int:
    """Cells the best function of position alone matches: per column, the max multiplicity."""

    grid = table_labels(rows)
    return sum(max(Counter(col).values()) for col in zip(*grid))


def position_switch_agreement(rows: list[dict[str, Any]]) -> int:
    """Agreement of the control ``fresh_root -> greeting, else REFUSED`` with the table."""

    agree = 0
    for row in rows:
        for cell in row["cells"]:
            predicted = "greeting" if cell["position_id"] == "fresh_root" else REFUSED
            if predicted == cell["label"]:
                agree += 1
    return agree


def table_summary(corpus: dict[str, Any] | None = None) -> dict[str, Any]:
    corpus = corpus or build_corpus()
    rows = build_table(corpus)
    return {
        "generation_rule": (
            "cell(surface, position) = the unique family F such that the corpus "
            "witnesses the normalized surface under F via an ENTRY move and the "
            "position satisfies F's entry predicate; zero matches = REFUSED"
        ),
        "positions": list(POSITION_IDS),
        "table": rows,
        "c_surface": c_surface(rows),
        "c_position": c_position(rows),
        "position_switch_agreement": position_switch_agreement(rows),
    }


# --------------------------------------------------------------------------
# Stack arithmetic for the nested trajectories. This is fixture arithmetic
# over authored dispositions, not an admission engine: nothing here ranks or
# selects a candidate. The runtime that will own the stack is
# scripts/protocol_runtime.py, and U-P0 registers that it does not exist yet.
# --------------------------------------------------------------------------


def stack_top_summary(stack: list[dict[str, str]]) -> str:
    if not stack:
        return STACK_EMPTY
    top = stack[-1]
    return f"top:{top['protocol_id']}:{top['state']}"


def stack_ids(stack: list[dict[str, str]]) -> list[str]:
    return [episode["episode_id"] for episode in stack]


def apply_disposition(
    stack: list[dict[str, str]], disposition: str, protocol_id: str | None, turn_index: int
) -> list[dict[str, str]]:
    after = [dict(e) for e in stack]
    if disposition == "ENTER":
        if after:
            raise ConstructionRefusal("ENTER on a non-empty stack is a SUSPEND")
        after.append(
            {
                "episode_id": episode_id(turn_index, protocol_id),
                "protocol_id": protocol_id,
                "state": "active",
            }
        )
    elif disposition == "SUSPEND":
        if not after:
            raise ConstructionRefusal("SUSPEND on an empty stack has no parent")
        if len(after) >= STACK_DEPTH_CAP:
            raise ConstructionRefusal("a ninth push is REFUSED before mutation")
        after[-1]["state"] = "suspended"
        after.append(
            {
                "episode_id": episode_id(turn_index, protocol_id),
                "protocol_id": protocol_id,
                "state": "active",
            }
        )
    elif disposition == "RESUME":
        if not after or after[-1]["state"] != "suspended":
            raise ConstructionRefusal("RESUME needs a suspended top episode")
        after[-1]["state"] = "active"
    elif disposition == "EXIT":
        if not after or after[-1]["state"] != "active":
            raise ConstructionRefusal("EXIT needs an active top episode")
        after.pop()
    elif disposition in ("CONTINUE", "ASK", REFUSED):
        pass
    else:
        raise ConstructionRefusal(f"unknown disposition {disposition!r}")
    return after


# --------------------------------------------------------------------------
# Seed: the eight nested/interruption trajectories, the depth-nine plant.
# Each turn authors its disposition and (for selected turns) the move; this
# script derives the stack snapshots, the protocol_stack signal value, the
# episode ids, and the next-state digests, and then checks the authored move
# is the unique corpus move whose predicates hold at that turn.
# --------------------------------------------------------------------------

FRESH = "fresh_root"
PROBE_POS = "probe_outstanding"
LITERAL = "literal_slot"
TASK = "programming_task"


def _u(surface: str, position_id: str, disposition: str, protocol_id=None, move_id=None, **extra):
    turn = {
        "turn_kind": "utterance",
        "surface": surface,
        "position_id": position_id,
        "expected_disposition": disposition,
        "expected_protocol_id": protocol_id,
        "expected_move_id": move_id,
    }
    turn.update(extra)
    return turn


def _reply(position_id: str, disposition: str, binds_turn: int, protocol_id=None, move_id=None, **extra):
    turn = {
        "turn_kind": "reply",
        "surface": None,
        "position_id": position_id,
        "binds_request_minted_at_turn": binds_turn,
        "expected_disposition": disposition,
        "expected_protocol_id": protocol_id,
        "expected_move_id": move_id,
    }
    turn.update(extra)
    return turn


NESTED_SEED: tuple[dict[str, Any], ...] = (
    {
        "fixture_id": "nested-enter-d1-a",
        "gloss": "a greeting entered at a fresh root; depth one",
        "turns": (_u("hello", FRESH, "ENTER", "protocol.greeting.a", "greet"),),
    },
    {
        "fixture_id": "nested-enter-d1-b",
        "gloss": "a probe reply entered while a probe is outstanding; depth one",
        "turns": (_u("still here", PROBE_POS, "ENTER", "protocol.probe_reply.a", "confirm_alive"),),
    },
    {
        "fixture_id": "nested-suspend-d2-a",
        "gloss": "a quoted datum interrupts an active greeting; depth two",
        "turns": (
            _u("hello", FRESH, "ENTER", "protocol.greeting.a", "greet"),
            _u("forty-two", LITERAL, "SUSPEND", "protocol.quoted_datum.a", "accept_datum"),
        ),
    },
    {
        "fixture_id": "nested-suspend-d2-b",
        "gloss": "expected program output interrupts an active probe reply; depth two",
        "turns": (
            _u("still here", PROBE_POS, "ENTER", "protocol.probe_reply.a", "confirm_alive"),
            _u("hello world", TASK, "SUSPEND", "protocol.expected_output.a", "match_output"),
        ),
    },
    {
        "fixture_id": "nested-resume-d1-a",
        "gloss": "the child exits and the exact parent episode resumes",
        "turns": (
            _u("hello", FRESH, "ENTER", "protocol.greeting.a", "greet"),
            _u("forty-two", LITERAL, "SUSPEND", "protocol.quoted_datum.a", "accept_datum"),
            _u("end quote", FRESH, "EXIT", "protocol.quoted_datum.a", "close_quote"),
            _u("how are you", FRESH, "RESUME", "protocol.greeting.a", "pick_up"),
        ),
    },
    {
        "fixture_id": "nested-resume-d1-b",
        "gloss": (
            "material ambiguity inside an active protocol: the ASK does not mutate the "
            "stack, the reply completes the deferred transition, and a stale replay of "
            "the same reply is REFUSED against the consumed request"
        ),
        "turns": (
            _u("hello", FRESH, "ENTER", "protocol.greeting.a", "greet"),
            _u("null", LITERAL, "ASK"),
            _reply(
                LITERAL,
                "SUSPEND",
                2,
                "protocol.quoted_datum.a",
                "accept_datum",
                reply_selects={
                    "protocol_id": "protocol.quoted_datum.a",
                    "move_id": "accept_datum",
                },
            ),
            _u("end quote", FRESH, "EXIT", "protocol.quoted_datum.a", "close_quote"),
            _u("how are you", FRESH, "RESUME", "protocol.greeting.a", "pick_up"),
            _reply(
                FRESH,
                REFUSED,
                2,
                refusal_reason="consumed_request",
                stale_replay_of_turn=3,
                reply_selects={
                    "protocol_id": "protocol.quoted_datum.a",
                    "move_id": "accept_datum",
                },
            ),
        ),
    },
    {
        "fixture_id": "nested-exit-d1",
        "gloss": "a depth-one greeting exits and the stack empties",
        "turns": (
            _u("hello", FRESH, "ENTER", "protocol.greeting.a", "greet"),
            _u("goodbye", FRESH, "EXIT", "protocol.greeting.a", "farewell"),
        ),
    },
    {
        "fixture_id": "nested-exit-d2",
        "gloss": "a depth-two child exits; the parent stays suspended",
        "turns": (
            _u("hello", FRESH, "ENTER", "protocol.greeting.a", "greet"),
            _u("forty-two", LITERAL, "SUSPEND", "protocol.quoted_datum.a", "accept_datum"),
            _u("end quote", FRESH, "EXIT", "protocol.quoted_datum.a", "close_quote"),
        ),
    },
)

DEPTH9_SEED: dict[str, Any] = {
    "fixture_id": "depth9-plant",
    "gloss": (
        "the plant fills the stack to the declared cap of eight itself, then asks for a "
        "ninth push. The ninth is REFUSED before mutation. Not one of the eight nested "
        "fixtures, and it does not raise the cap."
    ),
    "turns": (
        _u("hello", FRESH, "ENTER", "protocol.greeting.a", "greet"),
        _u("forty-two", LITERAL, "SUSPEND", "protocol.quoted_datum.a", "accept_datum"),
        _u("ok", TASK, "SUSPEND", "protocol.expected_output.a", "match_output"),
        _u("still here", PROBE_POS, "SUSPEND", "protocol.probe_reply.a", "confirm_alive"),
        _u("hello", FRESH, "SUSPEND", "protocol.greeting.a", "greet"),
        _u("forty-two", LITERAL, "SUSPEND", "protocol.quoted_datum.a", "accept_datum"),
        _u("ok", TASK, "SUSPEND", "protocol.expected_output.a", "match_output"),
        _u("still here", PROBE_POS, "SUSPEND", "protocol.probe_reply.a", "confirm_alive"),
        _u("hello", FRESH, REFUSED, refusal_reason="stack_depth_cap"),
    ),
}


# --------------------------------------------------------------------------
# The fixtures.
# --------------------------------------------------------------------------


def _candidate_row(candidate: dict[str, Any], stack_after: Sequence[str]) -> dict[str, Any]:
    projection = next_state_projection(candidate["node"]["protocol_id"], stack_after)
    return {
        "protocol_id": candidate["node"]["protocol_id"],
        "move_id": candidate["move"]["move_id"],
        "relation": candidate["node"]["family"],
        "required_signal_predicates": candidate["move"]["required_signal_predicates"],
        "next_state": projection,
        "next_state_sha256": sha256_canonical(projection),
    }


def _candidate_stack_after(
    kind: str, stack: list[dict[str, str]], turn_index: int, protocol_id: str
) -> list[str]:
    """The ``stack_after`` a candidate of this kind would produce.

    Episode ids only — that is what the four-field projection digests. A
    resume changes an episode's state but not the list of ids, which is a
    property of the projection the design sealed, not a shortcut here.
    """

    ids = stack_ids(stack)
    if kind == "entry":
        return ids + [episode_id(turn_index, protocol_id)]
    if kind == "exit":
        return ids[:-1]
    return ids


def _witness_rows(candidates: Sequence[dict[str, Any]]) -> list[dict[str, str]]:
    seen = {}
    for candidate in candidates:
        seen[candidate["node"]["protocol_id"]] = {
            "protocol_node_id": candidate["node"]["protocol_id"],
            "relation": candidate["node"]["family"],
        }
    return [seen[key] for key in sorted(seen)]


def build_product_fixtures(corpus: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positions = {p["position_id"]: p for p in POSITION_SEED}
    fixtures = []
    for row in rows:
        for cell in row["cells"]:
            position = positions[cell["position_id"]]
            signal_rows = context_signal_rows(position, STACK_EMPTY)
            signals = signal_map(signal_rows)
            candidates = entry_candidates(corpus, row["surface"], signals)
            if cell["label"] == REFUSED:
                if candidates:
                    raise ConstructionRefusal(
                        f"ctx-{row['row']}-{cell['col']} is REFUSED in the table but has candidates"
                    )
                expected = {
                    "expected_disposition": REFUSED,
                    "expected_family": None,
                    "expected_protocol_id": None,
                    "expected_move_id": None,
                    "expected_next_state_sha256": None,
                }
            else:
                if len(candidates) != 1:
                    raise ConstructionRefusal(
                        f"ctx-{row['row']}-{cell['col']} has {len(candidates)} candidates"
                    )
                candidate = candidates[0]
                stack_after = [episode_id(1, candidate["node"]["protocol_id"])]
                expected = {
                    "expected_disposition": "ENTER",
                    "expected_family": candidate["node"]["family"],
                    "expected_protocol_id": candidate["node"]["protocol_id"],
                    "expected_move_id": candidate["move"]["move_id"],
                    "expected_next_state_sha256": sha256_canonical(
                        next_state_projection(candidate["node"]["protocol_id"], stack_after)
                    ),
                }
            fixture = {
                "fixture_id": f"ctx-{row['row']}-{cell['col']}",
                "kind": "product",
                "row": row["row"],
                "col": cell["col"],
                "surface": row["surface"],
                "position_id": cell["position_id"],
                "family": cell["label"] if cell["label"] != REFUSED else None,
                "corruption": None,
                "turns": [
                    {
                        "turn_index": 1,
                        "turn_kind": "utterance",
                        "surface": row["surface"],
                        "position_id": cell["position_id"],
                        "context_signals": signal_rows,
                        "protocol_witnesses": _witness_rows(candidates),
                        "stack_before": [],
                        "expected_stack_after": (
                            [] if cell["label"] == REFUSED
                            else [episode_id(1, cell["protocol_id"])]
                        ),
                        "candidates": [
                            _candidate_row(c, [episode_id(1, c["node"]["protocol_id"])])
                            for c in candidates
                        ],
                        **expected,
                    }
                ],
                **expected,
                "expected_authority_delta": [],
            }
            fixtures.append(fixture)
    return fixtures


def build_refusal_fixtures(corpus: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positions = {p["position_id"]: p for p in POSITION_SEED}
    by_surface = {row["surface"]: row for row in rows}
    fixtures = []
    for position_id in POSITION_IDS:
        position = positions[position_id]
        surface = normalize(REFUSAL_HOME_SURFACE[position_id])
        cell = next(
            c for c in by_surface[surface]["cells"] if c["position_id"] == position_id
        )
        if cell["label"] == REFUSED:
            raise ConstructionRefusal(
                f"refusal fixtures corrupt a *selected* home cell; "
                f"({surface!r}, {position_id!r}) is already REFUSED"
            )
        for corruption in REFUSAL_CORRUPTIONS:
            if corruption == "remove_witness":
                signal_rows = context_signal_rows(position, STACK_EMPTY)
                dropped_nodes = frozenset({cell["protocol_id"]})
                dropped_event = None
            else:
                dropped_event = position["position_event"]
                signal_rows = context_signal_rows(
                    position, STACK_EMPTY, dropped_event=dropped_event
                )
                dropped_nodes = frozenset()
            signals = signal_map(signal_rows)
            candidates = entry_candidates(
                corpus, surface, signals, drop_witness_nodes=dropped_nodes
            )
            if candidates:
                raise ConstructionRefusal(
                    f"corruption {corruption!r} on ({surface!r}, {position_id!r}) still "
                    f"leaves {len(candidates)} candidate(s); the refusal fixture would "
                    f"not be a refusal"
                )
            fixtures.append(
                {
                    "fixture_id": f"refusal-{position_id}-{corruption}",
                    "kind": "refusal",
                    "surface": surface,
                    "position_id": position_id,
                    "family": None,
                    "corruption": corruption,
                    "corruption_detail": (
                        {
                            "removed_witness_protocol_node_id": cell["protocol_id"],
                            "removed_witness_relation": cell["label"],
                        }
                        if corruption == "remove_witness"
                        else {
                            "removed_source_event_id": dropped_event,
                            "removed_signal_ids": [
                                s
                                for s in NON_STACK_SIGNALS
                                if position["source_events"][s] == dropped_event
                            ],
                        }
                    ),
                    "uncorrupted_cell": {
                        "protocol_id": cell["protocol_id"],
                        "move_id": cell["move_id"],
                        "label": cell["label"],
                    },
                    "turns": [
                        {
                            "turn_index": 1,
                            "turn_kind": "utterance",
                            "surface": surface,
                            "position_id": position_id,
                            "context_signals": signal_rows,
                            "protocol_witnesses": [],
                            "stack_before": [],
                            "expected_stack_after": [],
                            "candidates": [],
                            "expected_disposition": REFUSED,
                            "expected_protocol_id": None,
                            "expected_move_id": None,
                        }
                    ],
                    "expected_disposition": REFUSED,
                    "expected_family": None,
                    "expected_protocol_id": None,
                    "expected_move_id": None,
                    "expected_stack_mutation": False,
                    "expected_authority_delta": [],
                }
            )
    return fixtures


def build_ask_fixtures(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    positions = {p["position_id"]: p for p in POSITION_SEED}
    fixtures = []
    for surface, position_id in ASK_SURFACES:
        surface = normalize(surface)
        position = positions[position_id]
        signal_rows = context_signal_rows(position, STACK_EMPTY)
        candidates = entry_candidates(corpus, surface, signal_map(signal_rows))
        rows = [
            _candidate_row(c, [episode_id(1, c["node"]["protocol_id"])]) for c in candidates
        ]
        digests = {row["next_state_sha256"] for row in rows}
        if len(rows) < 2 or len(digests) < 2:
            raise ConstructionRefusal(
                f"ASK fixture on ({surface!r}, {position_id!r}) has {len(rows)} candidates "
                f"and {len(digests)} distinct next_state_sha256; material ambiguity needs two"
            )
        fixtures.append(
            {
                "fixture_id": f"ask-{surface.replace(' ', '_')}-{position_id}",
                "kind": "ask",
                "surface": surface,
                "position_id": position_id,
                "family": None,
                "corruption": None,
                "turns": [
                    {
                        "turn_index": 1,
                        "turn_kind": "utterance",
                        "surface": surface,
                        "position_id": position_id,
                        "context_signals": signal_rows,
                        "protocol_witnesses": _witness_rows(candidates),
                        "stack_before": [],
                        "expected_stack_after": [],
                        "candidates": rows,
                        "expected_disposition": "ASK",
                        "expected_protocol_id": None,
                        "expected_move_id": None,
                    }
                ],
                "expected_disposition": "ASK",
                "expected_state": "WAITING",
                "expected_family": None,
                "expected_protocol_id": None,
                "expected_move_id": None,
                "expected_selected_move_id": None,
                "expected_unresolved_move_ids": sorted(row["move_id"] for row in rows),
                "expected_distinct_next_state_sha256": sorted(digests),
                "expected_need": {
                    "minted": True,
                    "slot": "protocol_uptake.candidate_move",
                    "request_id": None,
                    "request_id_note": (
                        "verifier-minted at run time; not frozen at U-P0, only its "
                        "existence and its slot are"
                    ),
                },
                "expected_stack_mutation": False,
                "expected_authority_delta": [],
            }
        )
    return fixtures


def build_equivalence_fixtures(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    positions = {p["position_id"]: p for p in POSITION_SEED}
    fixtures = []
    for surface, position_id in EQUIVALENCE_SURFACES:
        surface = normalize(surface)
        position = positions[position_id]
        signal_rows = context_signal_rows(position, STACK_EMPTY)
        candidates = entry_candidates(corpus, surface, signal_map(signal_rows))
        rows = [
            _candidate_row(c, [episode_id(1, c["node"]["protocol_id"])]) for c in candidates
        ]
        digests = {row["next_state_sha256"] for row in rows}
        if len(rows) != 2 or len(digests) != 1:
            raise ConstructionRefusal(
                f"equivalence fixture on ({surface!r}, {position_id!r}) has {len(rows)} "
                f"candidates grouping to {len(digests)} digest(s); it must be two names, "
                f"one next state"
            )
        canonical = min(row["move_id"] for row in rows)
        protocol_id = rows[0]["protocol_id"]
        fixtures.append(
            {
                "fixture_id": f"equivalence-{surface}-{position_id}",
                "kind": "equivalence",
                "surface": surface,
                "position_id": position_id,
                "family": "greeting",
                "corruption": None,
                "turns": [
                    {
                        "turn_index": 1,
                        "turn_kind": "utterance",
                        "surface": surface,
                        "position_id": position_id,
                        "context_signals": signal_rows,
                        "protocol_witnesses": _witness_rows(candidates),
                        "stack_before": [],
                        "expected_stack_after": [episode_id(1, protocol_id)],
                        "candidates": rows,
                        "expected_disposition": "ENTER",
                        "expected_protocol_id": protocol_id,
                        "expected_move_id": canonical,
                    }
                ],
                "expected_disposition": "ENTER",
                "expected_family": "greeting",
                "expected_protocol_id": protocol_id,
                "expected_move_id": canonical,
                "expected_proceeds_without_asking": True,
                "expected_equivalence_recorded": True,
                "expected_equivalence_partition": [sorted(row["move_id"] for row in rows)],
                "expected_shared_next_state_sha256": sorted(digests)[0],
                "expected_stack_after": [episode_id(1, protocol_id)],
                "expected_authority_delta": [],
            }
        )
    return fixtures


def _trajectory_turns(corpus: dict[str, Any], seed: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    positions = {p["position_id"]: p for p in POSITION_SEED}
    stack: list[dict[str, str]] = []
    deepest = 0
    turns = []
    consumed_requests: set[int] = set()
    for turn_index, authored in enumerate(seed["turns"], start=1):
        position = positions[authored["position_id"]]
        top_summary = stack_top_summary(stack)
        signal_rows = context_signal_rows(position, top_summary)
        signals = signal_map(signal_rows)
        disposition = authored["expected_disposition"]
        protocol_id = authored.get("expected_protocol_id")
        move_id = authored.get("expected_move_id")

        candidates = (
            all_candidates(corpus, authored["surface"], signals)
            if authored["turn_kind"] == "utterance"
            else []
        )

        if authored["turn_kind"] == "utterance" and disposition not in ("ASK", REFUSED):
            if len(candidates) != 1:
                raise ConstructionRefusal(
                    f"{seed['fixture_id']} turn {turn_index}: {len(candidates)} corpus "
                    f"moves hold, so the authored selection is not derivable"
                )
            only = candidates[0]
            if (only["node"]["protocol_id"], only["move"]["move_id"]) != (protocol_id, move_id):
                raise ConstructionRefusal(
                    f"{seed['fixture_id']} turn {turn_index}: corpus selects "
                    f"{only['node']['protocol_id']}/{only['move']['move_id']}, "
                    f"fixture authored {protocol_id}/{move_id}"
                )
        if authored["turn_kind"] == "utterance" and disposition == "ASK":
            rows = [
                _candidate_row(
                    c,
                    _candidate_stack_after(
                        c["move"]["kind"], stack, turn_index, c["node"]["protocol_id"]
                    ),
                )
                for c in candidates
            ]
            if len(rows) < 2 or len({r["next_state_sha256"] for r in rows}) < 2:
                raise ConstructionRefusal(
                    f"{seed['fixture_id']} turn {turn_index} is authored ASK without two "
                    f"materially different candidates"
                )
        if authored["turn_kind"] == "reply":
            binds = authored["binds_request_minted_at_turn"]
            if disposition == REFUSED:
                if binds not in consumed_requests:
                    raise ConstructionRefusal(
                        f"{seed['fixture_id']} turn {turn_index}: a stale replay must "
                        f"name an already-consumed request"
                    )
            else:
                if binds in consumed_requests:
                    raise ConstructionRefusal(
                        f"{seed['fixture_id']} turn {turn_index}: request already consumed"
                    )
                consumed_requests.add(binds)
                node = nodes_by_id(corpus)[protocol_id]
                move = next(m for m in node["moves"] if m["move_id"] == move_id)
                if not predicate_holds(move["required_signal_predicates"], signals):
                    raise ConstructionRefusal(
                        f"{seed['fixture_id']} turn {turn_index}: the deferred move's "
                        f"predicates do not hold at binding time"
                    )
        if disposition == REFUSED and authored.get("refusal_reason") == "stack_depth_cap":
            if len(stack) != STACK_DEPTH_CAP:
                raise ConstructionRefusal(
                    f"{seed['fixture_id']} turn {turn_index}: the cap refusal needs a "
                    f"stack already at {STACK_DEPTH_CAP}, found {len(stack)}"
                )

        stack_before = [dict(e) for e in stack]
        after = apply_disposition(stack, disposition, protocol_id, turn_index)
        deepest = max(deepest, len(after))

        candidate_rows = [
            _candidate_row(
                c,
                _candidate_stack_after(
                    c["move"]["kind"], stack_before, turn_index, c["node"]["protocol_id"]
                ),
            )
            for c in candidates
        ]

        turn = {
            "turn_index": turn_index,
            "turn_kind": authored["turn_kind"],
            "surface": authored["surface"],
            "position_id": authored["position_id"],
            "position_note": (
                "position_id names only the four non-stack signal values; protocol_stack "
                "is derived from this trajectory"
            ),
            "context_signals": signal_rows,
            "protocol_witnesses": _witness_rows(candidates),
            "stack_before": [dict(e) for e in stack_before],
            "stack_before_ids": stack_ids(stack_before),
            "expected_disposition": disposition,
            "expected_protocol_id": protocol_id,
            "expected_move_id": move_id,
            "expected_stack_after": [dict(e) for e in after],
            "expected_stack_after_ids": stack_ids(after),
            "expected_depth_after": len(after),
            "candidates": candidate_rows,
            "expected_authority_delta": [],
        }
        for extra in ("binds_request_minted_at_turn", "reply_selects", "refusal_reason",
                      "stale_replay_of_turn"):
            if extra in authored:
                turn[extra] = authored[extra]
        if disposition in ("ASK", REFUSED):
            turn["expected_stack_mutation"] = False
        if disposition not in ("ASK", REFUSED) and protocol_id is not None:
            turn["expected_next_state_sha256"] = sha256_canonical(
                next_state_projection(protocol_id, stack_ids(after))
            )
        turns.append(turn)
        stack = after
    return turns, deepest


def build_nested_fixtures(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    fixtures = []
    for seed in NESTED_SEED:
        turns, deepest = _trajectory_turns(corpus, seed)
        fixtures.append(
            {
                "fixture_id": seed["fixture_id"],
                "kind": "nested",
                "gloss": seed["gloss"],
                "family": None,
                "surface": None,
                "surfaces": [t["surface"] for t in turns],
                "corruption": None,
                "turns": turns,
                "expected_stack_after_sequence": [t["expected_stack_after_ids"] for t in turns],
                "expected_disposition_sequence": [t["expected_disposition"] for t in turns],
                "deepest_depth": deepest,
                "arrival_order_replays_required": 3,
                "expected_authority_delta": [],
            }
        )
    return fixtures


def build_depth9_fixture(corpus: dict[str, Any]) -> dict[str, Any]:
    turns, deepest = _trajectory_turns(corpus, DEPTH9_SEED)
    final = turns[-1]
    if final["expected_disposition"] != REFUSED:
        raise ConstructionRefusal("the depth-nine plant's ninth turn must be REFUSED")
    if final["expected_stack_after_ids"] != final["stack_before_ids"]:
        raise ConstructionRefusal("the depth-nine refusal mutated the stack")
    if len(final["expected_stack_after_ids"]) != STACK_DEPTH_CAP:
        raise ConstructionRefusal("the depth-nine plant did not fill the cap itself")
    return {
        "fixture_id": DEPTH9_SEED["fixture_id"],
        "kind": "depth_cap_plant",
        "gloss": DEPTH9_SEED["gloss"],
        "family": None,
        "surface": None,
        "surfaces": [t["surface"] for t in turns],
        "corruption": None,
        "stack_depth_cap": STACK_DEPTH_CAP,
        "turns": turns,
        "expected_stack_after_sequence": [t["expected_stack_after_ids"] for t in turns],
        "expected_disposition_sequence": [t["expected_disposition"] for t in turns],
        "deepest_depth": deepest,
        "expected_final_disposition": REFUSED,
        "expected_final_stack_unchanged": True,
        "expected_final_episode_count": STACK_DEPTH_CAP,
        "expected_authority_delta": [],
        "is_one_of_the_eight_nested_fixtures": False,
        "raises_the_cap": False,
    }


def build_b8_fixture(corpus: dict[str, Any]) -> dict[str, Any]:
    positions = {p["position_id"]: p for p in POSITION_SEED}
    position = positions["fresh_root"]
    surface = normalize(B8_SURFACE)
    signal_rows = context_signal_rows(position, STACK_EMPTY)
    witnesses = witnessed_moves(corpus, surface)
    if witnesses:
        raise ConstructionRefusal(
            "the B8 plant must be unwitnessed; a phrase that names authorities may not "
            "be a lookup key"
        )
    return {
        "fixture_id": "b8-authority-plant",
        "kind": "authority_plant",
        "gloss": (
            "a planted prompt string naming WRITE, Python, and shell capabilities. It is "
            "unwitnessed, so it opens nothing; the gate additionally asserts zero process "
            "starts and zero data-tree byte changes."
        ),
        "surface": surface,
        "position_id": "fresh_root",
        "family": None,
        "corruption": None,
        "turns": [
            {
                "turn_index": 1,
                "turn_kind": "utterance",
                "surface": surface,
                "position_id": "fresh_root",
                "context_signals": signal_rows,
                "protocol_witnesses": [],
                "stack_before": [],
                "expected_stack_after": [],
                "candidates": [],
                "expected_disposition": REFUSED,
                "expected_protocol_id": None,
                "expected_move_id": None,
            }
        ],
        "expected_disposition": REFUSED,
        "expected_family": None,
        "expected_protocol_id": None,
        "expected_move_id": None,
        "expected_stack_mutation": False,
        "expected_authority_delta": [],
        "gate_assertions": [
            "zero process starts",
            "zero stage records",
            "zero data-tree byte changes",
        ],
    }


def build_b9_mutants(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One mutant per U-PRE survivor, each naming the fixture it is applied to."""

    def cell_fixture(surface: str, position_id: str) -> str:
        surface = normalize(surface)
        row = next(r for r in rows if r["surface"] == surface)
        cell = next(c for c in row["cells"] if c["position_id"] == position_id)
        if cell["label"] == REFUSED:
            raise ConstructionRefusal(
                f"a mutant targeting ({surface!r}, {position_id!r}) cannot fire on an "
                f"already-REFUSED cell"
            )
        return f"ctx-{row['row']}-{cell['col']}"

    return [
        {
            "mutant_id": "b9-pending_need",
            "field": "pending_need",
            "field_class": "context_signal",
            "target_fixture": cell_fixture("still here", "probe_outstanding"),
            "target_cell": {"surface": "still here", "position_id": "probe_outstanding"},
            "transformation": "pending_need: probe -> ABSENT",
            "expected_effect": REFUSED,
        },
        {
            "mutant_id": "b9-quote_boundary",
            "field": "quote_boundary",
            "field_class": "context_signal",
            "target_fixture": cell_fixture("forty-two", "literal_slot"),
            "target_cell": {"surface": "forty-two", "position_id": "literal_slot"},
            "transformation": "quote_boundary: SET -> ABSENT",
            "expected_effect": REFUSED,
        },
        {
            "mutant_id": "b9-expected_output_slot",
            "field": "expected_output_slot",
            "field_class": "context_signal",
            "target_fixture": cell_fixture("done", "programming_task"),
            "target_cell": {"surface": "done", "position_id": "programming_task"},
            "transformation": "expected_output_slot: SET -> ABSENT",
            "expected_effect": REFUSED,
        },
        {
            "mutant_id": "b9-active_task",
            "field": "active_task",
            "field_class": "context_signal",
            "target_fixture": cell_fixture("done", "programming_task"),
            "target_cell": {"surface": "done", "position_id": "programming_task"},
            "transformation": (
                "active_task: SET -> ABSENT with expected_output_slot kept SET — the "
                "stale-slot case the conjunction exists for"
            ),
            "expected_effect": REFUSED,
        },
        {
            "mutant_id": "b9-protocol_stack",
            "field": "protocol_stack",
            "field_class": "context_signal",
            "target_fixture": "nested-resume-d1-a",
            "target_turn_index": 4,
            "transformation": (
                "top summary top:protocol.greeting.a:suspended -> "
                "top:protocol.greeting.a:active"
            ),
            "expected_effect": (
                "selected-move change: pick_up -> smalltalk, RESUME -> CONTINUE; or "
                "validation failure"
            ),
        },
        {
            "mutant_id": "b9-protocol_node_id",
            "field": "protocol_witnesses[].protocol_node_id",
            "field_class": "protocol_witness",
            "target_fixture": cell_fixture("hello", "fresh_root"),
            "target_cell": {"surface": "hello", "position_id": "fresh_root"},
            "transformation": (
                "witness protocol_node_id protocol.greeting.a -> dangling "
                "protocol.greeting.zz"
            ),
            "expected_effect": "validation failure",
        },
        {
            "mutant_id": "b9-relation",
            "field": "protocol_witnesses[].relation",
            "field_class": "protocol_witness",
            "target_fixture": cell_fixture("hello", "fresh_root"),
            "target_cell": {"surface": "hello", "position_id": "fresh_root"},
            "transformation": "witness relation greeting -> probe_reply",
            "expected_effect": "REFUSED or validation failure",
        },
    ]


def build_fixtures(corpus: dict[str, Any] | None = None) -> dict[str, Any]:
    corpus = corpus or build_corpus()
    rows = build_table(corpus)

    surface_ceiling = c_surface(rows)
    position_ceiling = c_position(rows)
    switch_agreement = position_switch_agreement(rows)
    for name, value in (("c_surface", surface_ceiling), ("c_position", position_ceiling)):
        if value >= 32:
            raise ConstructionRefusal(
                f"{name} = {value}/32: that view is a sufficient statistic and the "
                f"joint-uptake claim is vacuous — BLOCKED CONSTRUCTION"
            )
        if value >= 24:
            raise ConstructionRefusal(
                f"{name} = {value}/32 >= 24: the table is at least as separable as the "
                f"exclusive-home shape and no joint claim was constructed — "
                f"BLOCKED CONSTRUCTION"
            )

    product = build_product_fixtures(corpus, rows)
    refusal = build_refusal_fixtures(corpus, rows)
    ask = build_ask_fixtures(corpus)
    equivalence = build_equivalence_fixtures(corpus)
    nested = build_nested_fixtures(corpus)
    depth9 = build_depth9_fixture(corpus)
    b8 = build_b8_fixture(corpus)
    fixtures = product + refusal + ask + equivalence + nested + [depth9, b8]

    deepest_nested = max(f["deepest_depth"] for f in nested)
    if deepest_nested != 2:
        raise ConstructionRefusal(
            f"the eight nested fixtures reach depth {deepest_nested}; the declared "
            f"resource bound of {STACK_DEPTH_CAP} is four times a deepest of two"
        )

    switching = [
        row["surface"]
        for row in rows
        if len({c["label"] for c in row["cells"] if c["label"] != REFUSED}) >= 2
    ]
    if len(switching) < 2:
        raise ConstructionRefusal(
            "fewer than two surfaces take two different selected moves across "
            "positions; 'same utterance, different moves' was not constructed"
        )

    document = {
        "schema": FIXTURES_SCHEMA,
        "design": DESIGN,
        "roadmap": ROADMAP,
        "stage": "U-P0",
        "generator": GENERATOR,
        "upre": UPRE,
        "generated_note": (
            "Generated artifact. Every expectation below is derived from the seed in "
            "the generator by the sealed rule; no cell is hand-labelled. A direct edit "
            "of this file is a DESIGN §10 stop condition."
        ),
        "construction_note": (
            "Construction fixtures authored by this repository. They license no "
            "population claim about human conventions."
        ),
        "normalization": NORMALIZATION,
        "predicate_language": PREDICATE_LANGUAGE,
        "absence_sentinel": ABSENT,
        "episode_id_rule": "ep-<turn_index>-<protocol_id>, turn_index 1-based within a session",
        "next_state_projection": list(NEXT_STATE_PROJECTION),
        "next_state_sha256_rule": (
            "sha256 of the canonical JSON (sorted keys, comma/colon separators, UTF-8) "
            "of the four-field projection; move_id is deliberately outside it"
        ),
        "context_signal_ids": list(SIGNAL_IDS),
        "protocol_witness_fields": list(WITNESS_FIELDS),
        "stack_depth_cap": STACK_DEPTH_CAP,
        "positions": [
            {
                "position_id": p["position_id"],
                "gloss": p["gloss"],
                "signals": {**p["signals"], "protocol_stack": STACK_EMPTY},
                "source_events": {**p["source_events"], "protocol_stack": "evt-protocol-stack"},
                "context_event_removed_by_remove_context_event": p["position_event"],
            }
            for p in POSITION_SEED
        ],
        "product_surfaces": [normalize(s) for s in PRODUCT_SURFACES],
        "ask_surfaces": [
            {"surface": normalize(s), "position_id": p} for s, p in ASK_SURFACES
        ],
        "equivalence_surfaces": [
            {"surface": normalize(s), "position_id": p} for s, p in EQUIVALENCE_SURFACES
        ],
        "table_generation_rule": table_summary(corpus)["generation_rule"],
        "sealed_table": rows,
        "ceilings": {"c_surface": surface_ceiling, "c_position": position_ceiling},
        "position_switch_control": {
            "rule": "fresh_root -> greeting, else REFUSED",
            "frozen_table_agreement": switch_agreement,
            "cells": 32,
        },
        "surfaces_taking_two_different_selected_moves": switching,
        "deepest_nested_depth": deepest_nested,
        "counts": {
            "product": len(product),
            "refusal": len(refusal),
            "ask": len(ask),
            "equivalence": len(equivalence),
            "nested": len(nested),
            "depth_cap_plant": 1,
            "authority_plant": 1,
            "b9_mutants": 7,
            "total_fixtures": len(fixtures),
        },
        "fixtures": fixtures,
        "b9_mutants": build_b9_mutants(rows),
    }

    check_survivor_schema(document, where="fixtures")
    return document


# --------------------------------------------------------------------------
# Writing. Byte-deterministic, LF, trailing newline.
# --------------------------------------------------------------------------


def render(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render(document))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out",
        default=DEFAULT_CORPUS_OUT,
        help=f"where to write the generated protocol corpus (default {DEFAULT_CORPUS_OUT})",
    )
    parser.add_argument(
        "--fixtures",
        default=None,
        help=f"write the generated fixture file here instead (e.g. {DEFAULT_FIXTURES_OUT})",
    )
    parser.add_argument(
        "--table",
        action="store_true",
        help="print the sealed 8x4 table, c_surface, c_position, and the "
        "position-switch agreement as JSON",
    )
    args = parser.parse_args(argv)

    try:
        corpus = build_corpus()
        if args.table:
            print(json.dumps(table_summary(corpus), indent=2, ensure_ascii=False))
            return 0
        if args.fixtures:
            path = Path(args.fixtures)
            write_json(path if path.is_absolute() else REPO / path, build_fixtures(corpus))
            print(f"wrote {args.fixtures}")
            return 0
        path = Path(args.out)
        write_json(path if path.is_absolute() else REPO / path, corpus)
        print(f"wrote {args.out}")
        return 0
    except ConstructionRefusal as exc:
        print(f"BLOCKED CONSTRUCTION: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
