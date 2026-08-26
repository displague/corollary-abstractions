#!/usr/bin/env python3
"""The recorder — one served session, written down as it happens.

`docs/DESIGN-session-ledger.md` §5 slice 1: *"Journal + recorder wired into
the existing typed-line session (`CoreSession` already threads `session_id`
and a typed `SessionEvent` trace; the recorder rides it)."* This is that
recorder, and it is deliberately thin: it serves lines through
`harness.route_line` and writes down what happened. It does not decide
anything the harness would not have decided without it.

## What riding the trace means, concretely

`CoreSession.events` is the typed `SessionEvent` list the kernel already
keeps — a boot record and one record per kernel turn
(`harness.py:669-680`, `:714-730`). The recorder takes a slice of that list
per turn and writes the records the turn produced into the Turn's
`session_events` extension. It never re-types a component's conclusion in
prose, which is `session_run.py`'s own rule: *"a transcript that paraphrases
its sources is a story about a session."*

Only the structured fields travel, plus a digest of `detail`. A journal is
linear in turns by design (§3 keeps the live SET out and carries only its
digest), and pasting every stop-reason string in full would have made the
one artifact whose size the design bounded the one artifact that grew.

## Determinism

`created_utc` is supplied by the caller from the frozen recording protocol,
never read off the clock: a journal whose header changes every time it is
written is a journal that cannot be reproduced, and reproduction is what
ROADMAP-v0.21 §4.0(2) put in place of execute-once ceremony. `session_id`
is likewise assigned by the protocol's counter rule.

## The no-write-gate rule, enforced here rather than remembered

A recorded session must contain no corpus-mutating line (§6 P3, and P5's
MISSED IN KIND is why). Detection is on the SERVED VERDICT — route
`write_gate`, or any of the gate's uppercase statuses — not on the typed
line, so a line that reaches the gate through `_looks_like_path` rather
than by naming an existing file is caught too. A session that acquires one
is marked excluded, whole, and the seal counts and publishes it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import session_ledger as ledger  # noqa: E402
from harness import CoreSession, route_line  # noqa: E402

#: The two paths recording flows through. The prereg pins a digest over
#: BOTH, because "the recorder" is not one file: the journal object and the
#: thing that drives it are one instrument, and pinning half of it would
#: leave the other half free to move under a frozen protocol.
RECORDER_MODULES = ("scripts/session_ledger.py", "scripts/session_recorder.py")

#: `write_stage`'s uppercase verdicts, transported by the skin as statuses.
WRITE_GATE_STATUSES = frozenset({"PROVEN", "VERIFIED", "REFUSED"})


def recorder_code_digest(repo_root: Path) -> str:
    """One digest over the recorder's own bytes, for the protocol's C3 fix.

    Built from `build_throughput_tasks.canonical_lf_sha256` per module, then
    folded over the ordered (path, digest) pairs — the same canonical-LF
    convention every other digest in this cycle uses, so a checkout that
    rewrites line endings does not look like a changed recorder.
    """

    import build_throughput_tasks as builder  # noqa: PLC0415

    return ledger.digest(
        [[rel, builder.canonical_lf_sha256(rel)] for rel in RECORDER_MODULES]
    )


@dataclass
class TurnOutcome:
    """What one recorded turn produced, for a caller that wants to look."""

    turn_index: int
    verdict: dict
    record: dict
    rendered: str


@dataclass
class SessionRecorder:
    """One session, served and written down.

    `matrix` and `shared_index` are optional cost handles, not semantics: the
    boot matrix and the resolver's graph index are immutable and
    `serve_chat.ChatEngine.prewarm` already argues the case for sharing the
    index — *"the index is immutable and `resolver.default_index()` is
    deterministic, so handing the same object to every later session is
    replay-equivalent by construction"*. Every piece of SESSION state is
    still fresh per recorder.
    """

    repo_root: Path
    session_id: str
    created_utc: str
    keyring: object
    shared_index: object | None = None
    pin_table: dict | None = None

    session: CoreSession = field(init=False)
    barrier: ledger.ReadBarrier = field(init=False)
    assumptions: ledger.AssumptionSet = field(init=False)
    turns: list[ledger.Turn] = field(init=False, default_factory=list)
    outcomes: list[TurnOutcome] = field(init=False, default_factory=list)
    excluded_reason: str | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.session = CoreSession.boot(
            self.repo_root, offline=True, session_id=self.session_id
        )
        if self.shared_index is not None:
            self.session.resolver_index = self.shared_index
        self.barrier = ledger.ReadBarrier()
        self.assumptions = ledger.AssumptionSet(self.session_id, self.barrier)
        self.session.assumptions = self.assumptions
        self._event_mark = len(self.session.events)
        if self.pin_table is None:
            self.pin_table = ledger.pins(self.repo_root, self.session.matrix)

    # -- the header -------------------------------------------------------

    def header(self) -> dict:
        """§3's SessionHeader. `proposer_model_digest` is absent, and means so."""

        return {
            "session_id": self.session_id,
            "created_utc": self.created_utc,
            "pins": dict(self.pin_table),
        }

    # -- one turn ---------------------------------------------------------

    def turn(self, line: str) -> TurnOutcome:
        if len(self.turns) >= ledger.TURN_CAP:
            raise RuntimeError(
                f"session {self.session_id} is at the frozen {ledger.TURN_CAP}"
                "-turn cap; the protocol caps recording and recording more "
                "until a counter is met is the move the cap forbids"
            )
        turn_index = len(self.turns)
        declared_before = {
            record["assumption_id"] for record in self.assumptions.all_records()
        }

        self.barrier.open_turn(turn_index)
        verdict = route_line(self.repo_root, self.session, line)
        cited = self.barrier.close_turn()

        declared_after = {
            record["assumption_id"] for record in self.assumptions.all_records()
        }
        declared = tuple(sorted(declared_after - declared_before))
        # §3: a declaring turn does not cite what it declares, and the two
        # lists are disjoint "by construction". The construction is that
        # `AssumptionSet.declare` never touches the barrier — this assertion
        # is the check that the construction still holds, not the mechanism.
        overlap = set(declared) & set(cited)
        if overlap:
            raise RuntimeError(
                f"turn {turn_index} both declared and cited {sorted(overlap)}; "
                "§3 makes those disjoint by construction and they are not"
            )

        lifecycle = bool(declared) or verdict.get("route") == "retraction"
        live_digest = self.assumptions.live_set_digest()
        record_turn = ledger.Turn(
            turn_index=turn_index,
            input_bytes=line,
            resolution={
                "kind": ledger.resolution_kind(verdict, bool(declared), lifecycle),
                "grammar_query": ledger.grammar_query(verdict),
                "assumption_id": (
                    declared[0]
                    if declared
                    else (cited[0] if lifecycle and cited else None)
                ),
            },
            assumptions_declared=declared,
            assumptions_cited=cited,
            live_set_digest=live_digest,
            result={
                "kind": verdict.get("status"),
                "refusal_type": ledger.refusal_type(verdict),
                "answer_bytes_digest": ledger.answer_bytes_digest(verdict),
            },
            receipt_digest=ledger.receipt_digest(verdict, cited, live_digest),
            prev_turn_digest=self._prev_digest(),
            session_events=self._fresh_events(),
        )
        record_turn = ledger.sign_turn(
            record_turn,
            self.session_id,
            self.keyring,
            self.keyring.signing_key_id(),
        )
        self.turns.append(record_turn)

        if (
            verdict.get("route") == "write_gate"
            or verdict.get("status") in WRITE_GATE_STATUSES
        ):
            self.excluded_reason = (
                f"turn {turn_index} reached the write gate "
                f"(route {verdict.get('route')!r}, status "
                f"{verdict.get('status')!r}); the no-write-gate-turn rule "
                "excludes the session whole"
            )

        outcome = TurnOutcome(
            turn_index=turn_index,
            verdict=verdict,
            record=record_turn.record(),
            rendered=ledger.answer_bytes(verdict),
        )
        self.outcomes.append(outcome)
        return outcome

    def _fresh_events(self) -> tuple:
        """The SessionEvent trace this turn produced, structurally.

        Only the typed fields travel, plus a digest of `detail`: a journal is
        linear in turns by design (§3 keeps the live SET out and carries only
        its digest), and pasting every stop-reason string in full would make
        the one artifact whose size the design bounded the one that grows.
        """

        fresh = self.session.events[self._event_mark:]
        self._event_mark = len(self.session.events)
        return tuple(
            {
                "subsystem_id": event.subsystem_id,
                "kind": event.kind,
                "verdict": event.verdict,
                "stop_reason": event.stop_reason,
                "detail_digest": ledger.text_digest(event.detail),
            }
            for event in fresh
        )

    def _prev_digest(self) -> str:
        if not self.turns:
            return ledger.header_digest(self.header())
        return ledger.digest(self.turns[-1].record())

    # -- closing ----------------------------------------------------------

    def document(self) -> dict:
        """The journal, with every Assumption signed at its final status.

        Assumptions are signed at CLOSE, not at declaration, because a MAC
        over a record that will later change its own `status` and
        `superseded_by` would authenticate a version of the record the
        journal never contains. Turns are signed as they happen, because a
        turn is final the moment it is served — which is also what lets each
        turn's `prev_turn_digest` cover a signed predecessor.
        """

        self.assumptions.sign_all(self.keyring, self.keyring.signing_key_id())
        return ledger.journal_document(
            self.header(),
            self.assumptions.all_records(),
            [turn.record() for turn in self.turns],
        )

    def write(self, repo_root: Path | None = None) -> tuple[str, str]:
        """Write journal and read log. Returns (journal_digest, read_digest)."""

        root = repo_root or self.repo_root
        journal = ledger.write_journal(
            ledger.journal_path(root, self.session_id), self.document()
        )
        reads = ledger.write_read_log(
            ledger.read_log_path(root, self.session_id),
            self.session_id,
            self.barrier,
        )
        return journal, reads
