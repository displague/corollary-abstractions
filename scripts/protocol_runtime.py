#!/usr/bin/env python3
"""The protocol runtime: the module that owns the interaction-control stack.

``experiments/protocol_uptake_prereg.json`` names this file, at U-P0, as *the
module that will own the protocol stack; it does not exist at this commit*.
This is that module, implemented after the seal, after the B10 receipt-replay
checker, and after the deliberately broken controls — DESIGN §6 step 4's
construction order, which puts the instrument before the thing it measures.

What this module is
-------------------

A **deterministic oracle path** (DESIGN §6 step 5). There is no learned
component and no ranker: the candidate proposer is closed-form, and the
verifier admits a transition only when the corpus-witnessed moves whose
required signal-value predicates hold group to exactly one next state.

Nothing in a receipt reads a clock or a random source. B10 regenerates every
record from the sealed input and requires byte identity, so a timestamp, a
process id, or an iteration order that depends on a hash seed would each be a
defect rather than a detail.

The one channel a surface reaches the transition by
---------------------------------------------------

DESIGN §3: the utterance is normalized (NFC, casefold, strip) and used as the
**exact lookup key** into the sealed corpus. The returned witnesses — never
the surface bytes — enter the admission predicate together with the context
signals. A lookup miss licenses nothing. The surface is not consulted again;
:func:`_admit` never sees it.

Consistency with the seal
-------------------------

Canonical JSON, digests, episode ids, the four-field next-state projection,
the stack arithmetic, and the candidate ``stack_after`` rule are **imported**
from ``scripts/build_protocol_corpus.py`` rather than restated here. The
builder's ``expected_next_state_sha256`` values and this runtime's computed
digests are then the same function of the same inputs by construction, and
cannot drift.

State this module owns
----------------------

An episode stack (list, root first, capped at eight — DESIGN §3's declared
resource bound), one pending need or ``None``, the set of request ids ever
consumed in the session, a 1-based turn counter, and an append-only list of
``ProtocolUptake`` receipts. It lives beside session state; it is not a
belief frame and it is not ``FrameExecutor.open_nested``.

Usage
-----

    from protocol_runtime import ProtocolSession, load_corpus
    session = ProtocolSession("sess-demo", load_corpus())
    receipt = session.submit_utterance("hello", rows, source="tty:1")

    python scripts/protocol_runtime.py --fixture ctx-1-1
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

from build_protocol_corpus import (  # noqa: E402
    NON_STACK_SIGNALS,
    REFUSED,
    SIGNAL_IDS,
    STACK_DEPTH_CAP,
    STACK_EMPTY,
    ConstructionRefusal,
    apply_disposition,
    canonical_json,
    check_survivor_schema,
    episode_id,
    next_state_projection,
    normalize,
    predicate_holds,
    sha256_canonical,
    stack_ids,
    stack_top_summary,
)
from build_protocol_corpus import _candidate_stack_after as candidate_stack_after  # noqa: E402

CORPUS_PATH = REPO / "protocol" / "protocols.json"
FIXTURES_PATH = REPO / "experiments" / "protocol_uptake_fixtures.json"

RECEIPT_SCHEMA = "corollary.protocol-uptake/1"

# DESIGN §3's field list, in its order. The two fields U-PRE deleted are in no
# schema this module writes; `check_survivor_schema` proves that positively on
# every emitted record rather than by a search for names.
RECEIPT_FIELDS = (
    "schema",
    "uptake_id",
    "session_id",
    "turn_id",
    "utterance_sha256",
    "utterance_source",
    "context_before_sha256",
    "context_signals",
    "protocol_witnesses",
    "candidates",
    "disposition",
    "selected_move_id",
    "unresolved_move_ids",
    "stack_before",
    "stack_after",
    "authority_delta",
    "need",
    "verifier_verdict",
    "verifier_evidence",
)

ENTER, SUSPEND, CONTINUE, RESUME, EXIT, ASK = (
    "ENTER",
    "SUSPEND",
    "CONTINUE",
    "RESUME",
    "EXIT",
    "ASK",
)
DISPOSITIONS = (ENTER, CONTINUE, SUSPEND, RESUME, EXIT, ASK, REFUSED)

# Verifier verdicts. A refusal names *which* rule refused; "REFUSED" alone
# would make the receipt table unreadable and B9's mutants unadjudicable.
ADMITTED = "ADMITTED"
MATERIAL_AMBIGUITY = "MATERIAL_AMBIGUITY"
UNLICENSED = "UNLICENSED"
INVALID_INPUT = "INVALID_INPUT"
WAITING_LOCK = "WAITING_LOCK"
DEPTH_CAP = "STACK_DEPTH_CAP"
UNKNOWN_REQUEST = "UNKNOWN_REQUEST"
CONSUMED_REQUEST = "CONSUMED_REQUEST"
UNBOUND_ANSWER = "UNBOUND_ANSWER"

NEED_SLOT = "protocol_uptake.candidate_move"
# Question wording is outside the scored claim (DESIGN §4): a hardcoded string
# and a fluent generated one both score zero. It is a constant here precisely
# so that it carries no information and stays byte-reproducible.
NEED_PROMPT = (
    "More than one registered protocol transition remains admissible for this "
    "turn, and they lead to materially different next states. Name the "
    "candidate move to take; nothing proceeds until one is named."
)

ENTRY = "entry"
KIND_DISPOSITION = {"continuation": CONTINUE, "resume": RESUME, "exit": EXIT}


class ProtocolRuntimeError(RuntimeError):
    """A caller error — never a refusal. Refusals are receipts, not exceptions."""


# --------------------------------------------------------------------------
# Loading.
# --------------------------------------------------------------------------


def load_corpus(path: Path | str | None = None) -> dict[str, Any]:
    return json.loads(Path(path or CORPUS_PATH).read_text(encoding="utf-8"))


def load_fixtures(path: Path | str | None = None) -> dict[str, Any]:
    return json.loads(Path(path or FIXTURES_PATH).read_text(encoding="utf-8"))


def canonical_record(record: dict[str, Any]) -> str:
    """The one byte-comparison unit for a receipt (B10)."""

    return canonical_json(record)


def recompute_uptake_id(record: dict[str, Any]) -> str:
    """``uptake_id`` is the canonical digest of the record with it set empty."""

    return sha256_canonical({**record, "uptake_id": ""})


# --------------------------------------------------------------------------
# Corruption hooks. Fixtures drive these; the real path never constructs one.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Mutation:
    """One B9 mutation, applied to one turn before admission.

    ``target`` is ``signal``, ``witness_node_id``, or ``witness_relation``.
    The plan is *derived from the sealed mutant row*, never hand-copied: see
    :func:`parse_mutant`.
    """

    mutant_id: str
    turn_index: int
    target: str
    field: str
    from_value: str
    to_value: str


def parse_mutant(mutant: dict[str, Any]) -> Mutation:
    """Read one sealed ``b9_mutants`` row into an applicable transformation.

    The seal states each transformation as ``<what>: <from> -> <to>`` prose.
    Parsing it here — rather than restating the seven transformations in a
    table this file authors — is what keeps the runtime's mutation and the
    prereg's mutation the same object. The left side's last token is the
    value being replaced; the right side's first token is its replacement,
    with ``dangling`` (the seal's word for a reference that resolves to no
    node) skipped.
    """

    text = mutant["transformation"]
    if " -> " not in text:
        raise ProtocolRuntimeError(
            f"{mutant['mutant_id']}: sealed transformation {text!r} has no '->'"
        )
    left, right = text.split(" -> ", 1)
    from_value = left.split()[-1].rstrip(":")
    tokens = [token for token in right.split() if token != "dangling"]
    to_value = tokens[0]

    field = mutant["field"]
    if mutant["field_class"] == "context_signal":
        target, field_name = "signal", field
    elif field.endswith("protocol_node_id"):
        target, field_name = "witness_node_id", "protocol_node_id"
    elif field.endswith("relation"):
        target, field_name = "witness_relation", "relation"
    else:
        raise ProtocolRuntimeError(f"{mutant['mutant_id']}: unknown field {field!r}")

    return Mutation(
        mutant_id=mutant["mutant_id"],
        turn_index=int(mutant.get("target_turn_index", 1)),
        target=target,
        field=field_name,
        from_value=from_value,
        to_value=to_value,
    )


def apply_signal_mutation(rows: list[dict[str, str]], mutation: Mutation) -> list[dict[str, str]]:
    """Rewrite one supplied signal value. A mutant that cannot land raises."""

    out = [dict(row) for row in rows]
    for row in out:
        if row["signal_id"] == mutation.field:
            if row["value"] != mutation.from_value:
                raise ProtocolRuntimeError(
                    f"{mutation.mutant_id}: {mutation.field} is {row['value']!r}, the "
                    f"seal mutates from {mutation.from_value!r}"
                )
            row["value"] = mutation.to_value
            return out
    raise ProtocolRuntimeError(
        f"{mutation.mutant_id}: no {mutation.field!r} row on this turn to mutate"
    )


# --------------------------------------------------------------------------
# The session.
# --------------------------------------------------------------------------


class ProtocolSession:
    """One protocol session: a stack, a pending need, and append-only receipts."""

    def __init__(
        self,
        session_id: str,
        corpus: dict[str, Any],
        *,
        depth_cap: int = STACK_DEPTH_CAP,
    ) -> None:
        self.session_id = session_id
        self.corpus = corpus
        self.depth_cap = depth_cap
        self.stack: list[dict[str, str]] = []
        self.pending: dict[str, Any] | None = None
        self.consumed_request_ids: set[str] = set()
        self.turn_index = 0
        self.receipts: list[dict[str, Any]] = []
        # Session state, not receipt state: the full stack after each turn,
        # with each episode's active/suspended mark. The receipt carries
        # episode ids (DESIGN §3's `stack_before[] / stack_after[]`), and B5
        # reads the marks from here rather than from a field the schema does
        # not have. No schema field is added after U-P0.
        self.stack_history: list[list[dict[str, str]]] = []
        self._nodes = {node["protocol_id"]: node for node in corpus["nodes"]}

    # -- derived state ----------------------------------------------------

    @property
    def waiting(self) -> bool:
        return self.pending is not None

    def top_summary(self) -> str:
        """The only part of the stack any admission predicate may read."""

        return stack_top_summary(self.stack)

    def episode_ids(self) -> list[str]:
        return stack_ids(self.stack)

    def stack_snapshot(self) -> list[dict[str, str]]:
        return [dict(episode) for episode in self.stack]

    # -- the two admissible inputs ---------------------------------------

    def submit_utterance(
        self,
        surface: str,
        context_signals: Sequence[dict[str, str]],
        *,
        source: str,
        suppress_witness_nodes: Iterable[str] = (),
        witness_mutation: Mutation | None = None,
    ) -> dict[str, Any]:
        """Admit one utterance turn and emit exactly one receipt."""

        self.turn_index += 1
        turn_index = self.turn_index
        rows = self._context_rows(context_signals)
        context_before = self._context_before_sha256(rows)
        stack_before = self.episode_ids()

        def refuse(verdict: str, evidence: list[str], *, disposition: str = REFUSED) -> dict:
            return self._emit(
                turn_index=turn_index,
                utterance_sha256=sha256_canonical(normalize(surface)),
                utterance_source=source,
                context_rows=rows,
                context_before_sha256=context_before,
                witnesses=[],
                candidates=[],
                disposition=disposition,
                selected_move_id=None,
                unresolved=[],
                stack_before=stack_before,
                stack_after=self.episode_ids(),
                need=None,
                verdict=verdict,
                evidence=evidence,
            )

        # 1. WAITING is exclusive. While a need is pending the only admissible
        #    input is a reply binding that exact request id (DESIGN §4).
        if self.waiting:
            return refuse(
                WAITING_LOCK,
                [f"waiting_on_request:{self.pending['request_id']}", "no_stack_mutation"],
            )

        # 2. The context must be derivable and must not contradict the stack
        #    this session owns.
        problem = self._validate_context(rows)
        if problem:
            return refuse(INVALID_INPUT, problem)

        # 3. The witness channel. The surface reaches the corpus here and
        #    nowhere else; from this point the admission predicate sees
        #    witnesses and signals only.
        key = normalize(surface)
        entries = [dict(entry) for entry in self.corpus["lookup"].get(key, ())]
        entries = [
            entry
            for entry in entries
            if entry["protocol_node_id"] not in set(suppress_witness_nodes)
        ]
        if witness_mutation is not None:
            entries = self._mutate_witnesses(entries, witness_mutation)
        problem = self._validate_witnesses(entries)
        if problem:
            return refuse(INVALID_INPUT, problem)

        signals = self._effective_signals(rows)
        return self._admit(
            turn_index=turn_index,
            utterance_sha256=sha256_canonical(key),
            utterance_source=source,
            rows=rows,
            context_before=context_before,
            entries=entries,
            signals=signals,
            evidence=[f"witness_lookup:{len(entries)}"] + ([] if entries else ["lookup_miss"]),
        )

    def submit_reply(
        self,
        request_id: str,
        answer: dict[str, str],
        context_signals: Sequence[dict[str, str]],
        *,
        source: str,
    ) -> dict[str, Any]:
        """Bind a reply to a pending need and complete the deferred transition."""

        self.turn_index += 1
        turn_index = self.turn_index
        rows = self._context_rows(context_signals)
        context_before = self._context_before_sha256(rows)
        stack_before = self.episode_ids()
        payload = {"request_id": request_id, "answer": dict(answer)}

        def refuse(verdict: str, evidence: list[str], candidates=()) -> dict:
            return self._emit(
                turn_index=turn_index,
                utterance_sha256=sha256_canonical(payload),
                utterance_source=source,
                context_rows=rows,
                context_before_sha256=context_before,
                witnesses=[],
                candidates=list(candidates),
                disposition=REFUSED,
                selected_move_id=None,
                unresolved=[],
                stack_before=stack_before,
                stack_after=self.episode_ids(),
                need=None,
                verdict=verdict,
                evidence=evidence,
            )

        if not self.waiting:
            verdict = CONSUMED_REQUEST if request_id in self.consumed_request_ids else UNKNOWN_REQUEST
            reason = "consumed_request" if verdict == CONSUMED_REQUEST else "no_pending_need"
            return refuse(verdict, [f"{reason}:{request_id}", "no_stack_mutation"])
        pending = self.pending
        if request_id != pending["request_id"]:
            verdict = CONSUMED_REQUEST if request_id in self.consumed_request_ids else UNKNOWN_REQUEST
            return refuse(
                verdict,
                [
                    f"reply_names:{request_id}",
                    f"pending_is:{pending['request_id']}",
                    "no_stack_mutation",
                ],
            )

        problem = self._validate_context(rows)
        if problem:
            return refuse(INVALID_INPUT, problem)

        chosen = None
        for candidate in pending["candidates"]:
            if (
                candidate["protocol_id"] == answer.get("protocol_id")
                and candidate["move_id"] == answer.get("move_id")
            ):
                chosen = candidate
                break
        if chosen is None:
            return refuse(
                UNBOUND_ANSWER,
                [
                    f"answer_not_a_pending_candidate:"
                    f"{answer.get('protocol_id')}/{answer.get('move_id')}",
                    "no_stack_mutation",
                ],
            )

        # The deferred transition is re-checked at binding time. A reply may
        # not resurrect a move whose predicates stopped holding while the
        # session waited.
        signals = self._effective_signals(rows)
        move = self._move(chosen["protocol_id"], chosen["move_id"])
        if not predicate_holds(move["required_signal_predicates"], signals):
            return refuse(
                UNLICENSED,
                [
                    f"deferred_predicate_failed:{chosen['protocol_id']}/{chosen['move_id']}",
                    "no_stack_mutation",
                ],
            )

        # The candidate set is re-projected at *this* turn: an episode minted
        # by a deferred transition is minted at the turn that completed it.
        entries = [
            {
                "protocol_node_id": candidate["protocol_id"],
                "relation": self._nodes[candidate["protocol_id"]]["family"],
                "move_id": candidate["move_id"],
                "move_kind": self._move(candidate["protocol_id"], candidate["move_id"])["kind"],
            }
            for candidate in pending["candidates"]
        ]
        self.consumed_request_ids.add(request_id)
        self.pending = None
        return self._admit(
            turn_index=turn_index,
            utterance_sha256=sha256_canonical(payload),
            utterance_source=source,
            rows=rows,
            context_before=context_before,
            entries=entries,
            signals=signals,
            evidence=[f"bound_request:{request_id}"],
            forced=(chosen["protocol_id"], chosen["move_id"]),
        )

    # -- admission --------------------------------------------------------

    def _admit(
        self,
        *,
        turn_index: int,
        utterance_sha256: str,
        utterance_source: str,
        rows: list[dict[str, str]],
        context_before: str,
        entries: list[dict[str, str]],
        signals: dict[str, str],
        evidence: list[str],
        forced: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        """The admission predicate. It sees witnesses and signals, never bytes."""

        stack_before = self.episode_ids()
        evidence = list(evidence)
        matched: list[dict[str, Any]] = []
        for entry in entries:
            move = self._move(entry["protocol_node_id"], entry["move_id"])
            problem = self._reading_rule(entry, move)
            if problem:
                return self._emit(
                    turn_index=turn_index,
                    utterance_sha256=utterance_sha256,
                    utterance_source=utterance_source,
                    context_rows=rows,
                    context_before_sha256=context_before,
                    witnesses=[],
                    candidates=[],
                    disposition=REFUSED,
                    selected_move_id=None,
                    unresolved=[],
                    stack_before=stack_before,
                    stack_after=self.episode_ids(),
                    need=None,
                    verdict=INVALID_INPUT,
                    evidence=evidence + [problem],
                )
            if predicate_holds(move["required_signal_predicates"], signals):
                matched.append({"entry": entry, "move": move})
            else:
                evidence.append(self._why_not(entry, move, signals))
        matched.sort(key=lambda row: (row["entry"]["protocol_node_id"], row["move"]["move_id"]))

        candidates = [
            {
                "protocol_id": row["entry"]["protocol_node_id"],
                "move_id": row["move"]["move_id"],
                "required_signal_predicates": [
                    dict(pred) for pred in row["move"]["required_signal_predicates"]
                ],
                "next_state_sha256": sha256_canonical(
                    next_state_projection(
                        row["entry"]["protocol_node_id"],
                        candidate_stack_after(
                            row["move"]["kind"],
                            self.stack,
                            turn_index,
                            row["entry"]["protocol_node_id"],
                        ),
                    )
                ),
            }
            for row in matched
        ]
        witnesses = self._witness_rows(matched)

        def emit(**kwargs) -> dict[str, Any]:
            base = dict(
                turn_index=turn_index,
                utterance_sha256=utterance_sha256,
                utterance_source=utterance_source,
                context_rows=rows,
                context_before_sha256=context_before,
                witnesses=witnesses,
                candidates=candidates,
                stack_before=stack_before,
                need=None,
                unresolved=[],
                selected_move_id=None,
            )
            base.update(kwargs)
            base.setdefault("stack_after", self.episode_ids())
            return self._emit(**base)

        groups: dict[str, list[int]] = {}
        for index, candidate in enumerate(candidates):
            groups.setdefault(candidate["next_state_sha256"], []).append(index)

        # 0 groups: nothing was licensed. A lookup miss lands here too.
        if not groups:
            return emit(
                disposition=REFUSED,
                verdict=UNLICENSED,
                evidence=evidence + ["no_candidate_survived_the_predicate", "no_stack_mutation"],
            )

        # More than one group: materially different next states remain, so the
        # verifier opens one signed request and stops WAITING (DESIGN §4).
        if len(groups) > 1 and forced is None:
            digests = sorted(groups)
            need = self._mint_need(turn_index, candidates, digests)
            self.pending = {
                "request_id": need["request_id"],
                "turn_index": turn_index,
                "candidates": [
                    {"protocol_id": c["protocol_id"], "move_id": c["move_id"]}
                    for c in candidates
                ],
                "next_state_sha256": digests,
            }
            return emit(
                disposition=ASK,
                verdict=MATERIAL_AMBIGUITY,
                unresolved=sorted(c["move_id"] for c in candidates),
                need=need,
                evidence=evidence
                + [
                    f"materially_distinct_next_states:{len(digests)}",
                    "no_stack_mutation",
                ],
            )

        if forced is not None:
            index = next(
                i
                for i, candidate in enumerate(candidates)
                if (candidate["protocol_id"], candidate["move_id"]) == forced
            )
            digest = candidates[index]["next_state_sha256"]
            group = [index]
        else:
            digest, group = next(iter(groups.items()))
            # DESIGN §4: differently named candidates that produce the same
            # next state are one transition, and the canonical lowest
            # identifier is taken. Asking would collect information the
            # transition does not use.
            group = sorted(group, key=lambda i: candidates[i]["move_id"])
        chosen = candidates[group[0]]
        chosen_move = matched[group[0]]["move"]
        siblings = sorted(
            candidates[i]["move_id"] for i in groups[digest] if i != group[0]
        )
        evidence.append(f"grouped_to_one_next_state:{digest}")
        if siblings:
            evidence.append(f"equivalent_names:{','.join(siblings)}")

        kind = chosen_move["kind"]
        authority_delta = list(chosen_move.get("authority_delta", ()))
        if authority_delta:
            # DESIGN §5: no protocol move may authorize WRITE, process
            # creation, filesystem, shell, or network access. A corpus that
            # declared one is refused here rather than served.
            return emit(
                disposition=REFUSED,
                verdict=INVALID_INPUT,
                evidence=evidence + [f"move_declares_authority:{sorted(authority_delta)}"],
            )

        if kind == ENTRY:
            disposition = ENTER if not self.stack else SUSPEND
            if len(self.stack) >= self.depth_cap:
                # The ninth push is REFUSED *before* mutation.
                return emit(
                    disposition=REFUSED,
                    verdict=DEPTH_CAP,
                    evidence=evidence
                    + [f"stack_depth_cap:{self.depth_cap}", "no_stack_mutation"],
                )
        else:
            disposition = KIND_DISPOSITION[kind]

        try:
            after = apply_disposition(self.stack, disposition, chosen["protocol_id"], turn_index)
        except ConstructionRefusal as exc:
            return emit(
                disposition=REFUSED,
                verdict=UNLICENSED,
                evidence=evidence + [f"illegal_stack_transition:{exc}", "no_stack_mutation"],
            )
        self.stack = after
        evidence.append(f"selected:{chosen['protocol_id']}/{chosen['move_id']}:{kind}")
        return emit(
            disposition=disposition,
            verdict=ADMITTED,
            selected_move_id=chosen["move_id"],
            unresolved=siblings,
            stack_after=self.episode_ids(),
            evidence=evidence,
        )

    # -- need minting -----------------------------------------------------

    def _mint_need(
        self, turn_index: int, candidates: list[dict[str, Any]], digests: list[str]
    ) -> dict[str, Any]:
        """One signed request. Its id is a function of the session, not a clock.

        B10 replays every receipt and requires byte identity, so a random or
        time-derived ``request_id`` would make the ASK path unreplayable. The
        id digests exactly what makes this need this need: the session, the
        turn, the slot, and the materially different next states that forced
        it.
        """

        request_id = sha256_canonical(
            {
                "session_id": self.session_id,
                "turn_index": turn_index,
                "slot": NEED_SLOT,
                "candidate_next_state_sha256": sorted(digests),
            }
        )
        return {
            "request_id": request_id,
            "slot": NEED_SLOT,
            "prompt": NEED_PROMPT,
            "answer_schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["protocol_id", "move_id"],
                "properties": {
                    "protocol_id": {
                        "enum": sorted({c["protocol_id"] for c in candidates})
                    },
                    "move_id": {"enum": sorted(c["move_id"] for c in candidates)},
                },
            },
        }

    # -- validation -------------------------------------------------------

    def _context_rows(self, context_signals: Sequence[dict[str, str]]) -> list[dict[str, str]]:
        """The supplied rows, verbatim, plus the stack row if none was supplied.

        Supplied values are recorded as supplied. A contradicted stack summary
        is a validation refusal below, not a silent correction: a receipt that
        quietly rewrote its own inputs would hide exactly the corruption B9
        exists to catch.
        """

        rows = [
            {
                "signal_id": row["signal_id"],
                "value": row["value"],
                "source_event_id": row["source_event_id"],
            }
            for row in context_signals
        ]
        if not any(row["signal_id"] == "protocol_stack" for row in rows):
            rows.append(
                {
                    "signal_id": "protocol_stack",
                    "value": self.top_summary(),
                    "source_event_id": "evt-protocol-stack",
                }
            )
        return rows

    def _validate_context(self, rows: list[dict[str, str]]) -> list[str]:
        seen = [row["signal_id"] for row in rows]
        unknown = sorted(set(seen) - set(SIGNAL_IDS))
        if unknown:
            return [f"unknown_signal_ids:{','.join(unknown)}"]
        duplicated = sorted({name for name in seen if seen.count(name) > 1})
        if duplicated:
            return [f"duplicate_signal_ids:{','.join(duplicated)}"]
        missing = [name for name in NON_STACK_SIGNALS if name not in seen]
        if missing:
            # `remove_context_event` lands here: a signal whose parent event is
            # gone is *underivable*, which is not the same fact as carrying the
            # ABSENT sentinel, and no exact-value predicate over it can hold.
            return [f"underivable_signals:{','.join(missing)}", "no_stack_mutation"]
        supplied = next(row["value"] for row in rows if row["signal_id"] == "protocol_stack")
        derived = self.top_summary()
        if supplied != derived:
            # The session owns the stack. A supplied summary that contradicts
            # its own derivation is refused rather than believed.
            return [
                f"stack_summary_contradiction:supplied={supplied}:derived={derived}",
                "no_stack_mutation",
            ]
        return []

    def _validate_witnesses(self, entries: list[dict[str, str]]) -> list[str]:
        for entry in entries:
            node = self._nodes.get(entry["protocol_node_id"])
            if node is None:
                return [
                    f"dangling_protocol_node_id:{entry['protocol_node_id']}",
                    "no_stack_mutation",
                ]
            if entry["relation"] != node["family"]:
                return [
                    f"witness_relation_mismatch:{entry['protocol_node_id']}:"
                    f"{entry['relation']}!={node['family']}",
                    "no_stack_mutation",
                ]
            if not any(move["move_id"] == entry["move_id"] for move in node["moves"]):
                return [
                    f"dangling_move_id:{entry['protocol_node_id']}/{entry['move_id']}",
                    "no_stack_mutation",
                ]
        return []

    def _reading_rule(self, entry: dict[str, str], move: dict[str, Any]) -> str | None:
        """Entry moves read the four non-stack signals; the rest read the top summary."""

        named = {pred["signal_id"] for pred in move["required_signal_predicates"]}
        if move["kind"] == ENTRY and "protocol_stack" in named:
            return f"entry_move_reads_the_stack:{entry['protocol_node_id']}/{move['move_id']}"
        if move["kind"] != ENTRY and named != {"protocol_stack"}:
            return (
                f"non_entry_move_reads_more_than_the_top_summary:"
                f"{entry['protocol_node_id']}/{move['move_id']}"
            )
        return None

    def _effective_signals(self, rows: list[dict[str, str]]) -> dict[str, str]:
        """The signal map the predicate sees: supplied values, *derived* stack."""

        signals = {row["signal_id"]: row["value"] for row in rows}
        signals["protocol_stack"] = self.top_summary()
        return signals

    def _context_before_sha256(self, rows: list[dict[str, str]]) -> str:
        return sha256_canonical(
            {
                "signals": {row["signal_id"]: row["value"] for row in rows},
                "stack": self.stack_snapshot(),
            }
        )

    def _mutate_witnesses(
        self, entries: list[dict[str, str]], mutation: Mutation
    ) -> list[dict[str, str]]:
        out = []
        landed = False
        for entry in entries:
            entry = dict(entry)
            if mutation.target == "witness_node_id" and entry["protocol_node_id"] == mutation.from_value:
                entry["protocol_node_id"] = mutation.to_value
                landed = True
            elif mutation.target == "witness_relation" and entry["relation"] == mutation.from_value:
                entry["relation"] = mutation.to_value
                landed = True
            out.append(entry)
        if not landed:
            raise ProtocolRuntimeError(
                f"{mutation.mutant_id}: no witness with {mutation.field}="
                f"{mutation.from_value!r} on this turn to mutate"
            )
        return out

    def _why_not(self, entry: dict[str, str], move: dict[str, Any], signals: dict[str, str]) -> str:
        for pred in move["required_signal_predicates"]:
            observed = signals.get(pred["signal_id"], "<underivable>")
            if observed != pred["required_value"]:
                return (
                    f"predicate_failed:{entry['protocol_node_id']}/{move['move_id']}:"
                    f"{pred['signal_id']}={observed}!={pred['required_value']}"
                )
        return f"predicate_failed:{entry['protocol_node_id']}/{move['move_id']}"

    def _move(self, protocol_id: str, move_id: str) -> dict[str, Any]:
        node = self._nodes[protocol_id]
        return next(move for move in node["moves"] if move["move_id"] == move_id)

    @staticmethod
    def _witness_rows(matched: list[dict[str, Any]]) -> list[dict[str, str]]:
        """The witnesses the surviving candidates cite, deduplicated and sorted.

        This is the builder's ``_witness_rows`` rule: a receipt cites the
        witnesses that carried its candidates, so B2's "every selected move
        cites at least one protocol witness" is a property of the record and
        not of the lookup table.
        """

        seen = {
            row["entry"]["protocol_node_id"]: {
                "protocol_node_id": row["entry"]["protocol_node_id"],
                "relation": row["entry"]["relation"],
            }
            for row in matched
        }
        return [seen[key] for key in sorted(seen)]

    # -- emission ---------------------------------------------------------

    def _emit(
        self,
        *,
        turn_index: int,
        utterance_sha256: str,
        utterance_source: str,
        context_rows: list[dict[str, str]],
        context_before_sha256: str,
        witnesses: list[dict[str, str]],
        candidates: list[dict[str, Any]],
        disposition: str,
        selected_move_id: str | None,
        unresolved: list[str],
        stack_before: list[str],
        stack_after: list[str],
        need: dict[str, Any] | None,
        verdict: str,
        evidence: list[str],
    ) -> dict[str, Any]:
        if disposition not in DISPOSITIONS:
            raise ProtocolRuntimeError(f"unknown disposition {disposition!r}")
        if disposition in (ASK, REFUSED) and selected_move_id is not None:
            raise ProtocolRuntimeError("ASK and REFUSED carry no selected move")
        if disposition != ASK and need is not None:
            raise ProtocolRuntimeError("only ASK carries a need")
        record = {
            "schema": RECEIPT_SCHEMA,
            "uptake_id": "",
            "session_id": self.session_id,
            "turn_id": f"turn-{turn_index}",
            "utterance_sha256": utterance_sha256,
            "utterance_source": utterance_source,
            "context_before_sha256": context_before_sha256,
            "context_signals": context_rows,
            "protocol_witnesses": witnesses,
            "candidates": candidates,
            "disposition": disposition,
            "selected_move_id": selected_move_id,
            "unresolved_move_ids": list(unresolved),
            "stack_before": list(stack_before),
            "stack_after": list(stack_after),
            # DESIGN §3: a plaintext receipt field, not only a digest
            # ingredient — and empty in this slice, because no move in the
            # sealed corpus opens an authority.
            "authority_delta": [],
            "need": need,
            "verifier_verdict": verdict,
            "verifier_evidence": list(evidence),
        }
        if set(record) != set(RECEIPT_FIELDS):
            raise ProtocolRuntimeError(
                f"receipt fields drifted from DESIGN §3: "
                f"{sorted(set(record) ^ set(RECEIPT_FIELDS))}"
            )
        record["uptake_id"] = sha256_canonical(record)
        check_survivor_schema(record, where="uptake receipt")
        self.receipts.append(record)
        self.stack_history.append(self.stack_snapshot())
        return record


# --------------------------------------------------------------------------
# Fixture driving. One session per fixture, one receipt per turn.
# --------------------------------------------------------------------------


def fixture_session_id(fixture_id: str, mutant_id: str | None = None) -> str:
    return f"sess-{fixture_id}" if mutant_id is None else f"sess-{fixture_id}-{mutant_id}"


def run_fixture(
    fixture: dict[str, Any],
    corpus: dict[str, Any] | None = None,
    *,
    mutation: Mutation | None = None,
    session_id: str | None = None,
) -> ProtocolSession:
    """Drive one sealed fixture through a fresh session.

    Every turn's context signals are the fixture's, supplied per turn; the
    turn's provenance travels in ``utterance_source`` as
    ``fixture:<fixture_id>:<turn_index>``. The session derives
    ``protocol_stack`` itself and refuses a supplied summary that contradicts
    it.
    """

    corpus = corpus if corpus is not None else load_corpus()
    fixture_id = fixture["fixture_id"]
    session = ProtocolSession(
        session_id or fixture_session_id(fixture_id, mutation.mutant_id if mutation else None),
        corpus,
    )

    suppress: list[str] = []
    if fixture.get("corruption") == "remove_witness":
        suppress = [fixture["corruption_detail"]["removed_witness_protocol_node_id"]]

    minted: dict[int, str] = {}
    for turn in fixture["turns"]:
        index = turn["turn_index"]
        rows = [dict(row) for row in turn["context_signals"]]
        witness_mutation = None
        if mutation is not None and mutation.turn_index == index:
            if mutation.target == "signal":
                rows = apply_signal_mutation(rows, mutation)
            else:
                witness_mutation = mutation
        source = f"fixture:{fixture_id}:{index}"
        if turn["turn_kind"] == "utterance":
            receipt = session.submit_utterance(
                turn["surface"],
                rows,
                source=source,
                suppress_witness_nodes=suppress,
                witness_mutation=witness_mutation,
            )
        else:
            binds = turn["binds_request_minted_at_turn"]
            receipt = session.submit_reply(
                minted.get(binds, f"never-minted-at-turn-{binds}"),
                turn.get("reply_selects") or {},
                rows,
                source=source,
            )
        if receipt["need"] is not None:
            minted[index] = receipt["need"]["request_id"]
    return session


def replay_fixtures(
    fixtures: dict[str, Any], corpus: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Every sealed fixture, in file order, each in its own session."""

    corpus = corpus if corpus is not None else load_corpus()
    records: list[dict[str, Any]] = []
    for fixture in fixtures["fixtures"]:
        records.extend(run_fixture(fixture, corpus).receipts)
    return records


def replay_mutants(
    fixtures: dict[str, Any], corpus: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Every sealed B9 mutant, applied to the fixture the seal names."""

    corpus = corpus if corpus is not None else load_corpus()
    by_id = {fixture["fixture_id"]: fixture for fixture in fixtures["fixtures"]}
    records: list[dict[str, Any]] = []
    for mutant in fixtures["b9_mutants"]:
        fixture = by_id[mutant["target_fixture"]]
        records.extend(run_fixture(fixture, corpus, mutation=parse_mutant(mutant)).receipts)
    return records


def replay_registered_pass(
    fixtures: dict[str, Any], corpus: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """The exact receipt list a registered pass emits, in emission order.

    The gates runner writes this list as ``protocol_uptake_receipts.json`` and
    the B10 checker regenerates it here. Both call *this* function, so "the
    checker may not validate only records the runtime chose to emit" is a
    property of the code path rather than a promise: there is one definition
    of what the pass emits, and set equality is taken against it.

    B5's arrival-order replays are identity checks over these same sessions,
    not extra sessions; re-running a trajectory produces the receipts already
    in this list, so the artifact carries each record once.
    """

    corpus = corpus if corpus is not None else load_corpus()
    return replay_fixtures(fixtures, corpus) + replay_mutants(fixtures, corpus)


# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixture", help="run one sealed fixture and print its receipts")
    parser.add_argument("--all", action="store_true", help="print the whole registered pass")
    args = parser.parse_args(argv)

    fixtures = load_fixtures()
    corpus = load_corpus()
    if args.all:
        print(json.dumps(replay_registered_pass(fixtures, corpus), indent=2, ensure_ascii=False))
        return 0
    if not args.fixture:
        parser.error("name a --fixture or pass --all")
    by_id = {fixture["fixture_id"]: fixture for fixture in fixtures["fixtures"]}
    if args.fixture not in by_id:
        print(f"no such fixture: {args.fixture}", file=sys.stderr)
        return 1
    session = run_fixture(by_id[args.fixture], corpus)
    print(json.dumps(session.receipts, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
