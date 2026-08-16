#!/usr/bin/env python3
"""Phase-1 offline core session kernel for the interactive harness.

This is the FIRST slice of v0.8 item 1 (``docs/ROADMAP-v0.8.md``) and the
Phase-1 deliverable of ``docs/DESIGN-interactive-harness.md`` §9: a *session*
that boots a capability matrix, runs the existing propose -> verify -> trace
controller for one conversation, and surfaces a pause as
``StopReason.WAITING`` through a subsystem-agnostic need channel. It ships no
demo menu, no open-prose authoring, no Chat-Completions HTTP skin, and no
Phase-2 need dispatcher / session budget / loop detection. Those are later
slices, called out in the module TODO and in the roadmap.

What this module is careful *not* to invent:

* **No second authority.** A pause is the existing verifier-owned ASK
  (:class:`retrieval.ClarificationRequest`, minted and signed by
  :class:`retrieval.RetrievalVerifier`). The kernel only *renders* it. It never
  guesses a slot value; a need with no channel to answer it stays WAITING.
* **No second dispatch vocabulary.** The retrieve leg walks
  ``retrieval.run_miss_chain`` — ROADMAP-v0.7 item 6's ladder — rather than a
  parallel one, exactly as ``docs/DESIGN-interactive-harness.md`` §6.2 requires.
* **No verdict laundering by the boot probes.** The matrix is a *liveness*
  channel (:class:`Liveness`, OK/OFF/FAIL) kept deliberately disjoint from
  :class:`controller.Verdict`; per §3.2 a green matrix is not a soundness
  claim, so its glyphs never share the verdict palette.

The capability matrix records whether the three optional dependency families —
WordNet, Lean (PyPantograph), and Torch — are present or absent, and the whole
session runs with all three OFF. ``CoreSession.boot(..., offline=True)`` forces
that state regardless of what is installed, which is what makes the offline
prediction (P-IH1) deterministic on a box where Torch happens to be present.
"""

from __future__ import annotations

import importlib.util
import os
import secrets
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

from controller import (
    Controller,
    RunResult,
    SequencePolicy,
    StopReason,
    Verdict,
)
from frames import FrameEvent, FrameExecutor, FrameSpec, Literal
from oracle_controller_demo import StoryState, story_oracle_run
from retrieval import (
    RetrievalState,
    RetrievalVerifier,
    UnifiedKnowledgeStore,
    ask_action,
    run_miss_chain,
)


# --------------------------------------------------------------------------
# Boot capability matrix (docs/DESIGN-interactive-harness.md §5)
# --------------------------------------------------------------------------


class Liveness(str, Enum):
    """A boot probe's disposition — liveness only, never an epistemic rung.

    Kept a distinct type from :class:`controller.Verdict` on purpose
    (``docs/DESIGN-interactive-harness.md`` §3.2): ``OK`` means "the subsystem
    answered a smoke call", not "its verdicts are more trustworthy". A fully
    green matrix is not a certificate, so this enum's members never map to the
    verdict palette of §4.2.
    """

    OK = "OK"
    OFF = "OFF"
    FAIL = "FAIL"


#: The optional dependency families the matrix is required to report. These are
#: the three §5 names an offline boot forces to OFF, and the set P-IH1 asserts
#: contributes no registered subsystem when the session runs offline.
OPTIONAL_SUBSYSTEMS = ("retrieve.wordnet", "prover.lean_live", "tool.torch")


@dataclass(frozen=True)
class CapabilityRecord:
    """One row of the boot matrix."""

    subsystem_id: str
    liveness: Liveness
    detail: str
    optional: bool

    @property
    def registered(self) -> bool:
        """A subsystem may contribute transitions only when its probe passed.

        Registration is OK-only: OFF (absent optional dependency) and FAIL
        (broken subsystem) both withhold the subsystem's registered paths, per
        §3.2's registration rule.
        """

        return self.liveness is Liveness.OK


@dataclass(frozen=True)
class CapabilityMatrix:
    """The result of boot probes; a plain record the shell renders."""

    records: tuple[CapabilityRecord, ...]

    def get(self, subsystem_id: str) -> CapabilityRecord:
        for record in self.records:
            if record.subsystem_id == subsystem_id:
                return record
        raise KeyError(subsystem_id)

    def registered_ids(self) -> tuple[str, ...]:
        return tuple(r.subsystem_id for r in self.records if r.registered)

    def optional_off_ids(self) -> tuple[str, ...]:
        return tuple(
            r.subsystem_id
            for r in self.records
            if r.optional and not r.registered
        )

    def registered_optional_ids(self) -> tuple[str, ...]:
        return tuple(
            r.subsystem_id
            for r in self.records
            if r.optional and r.registered
        )

    @property
    def has_required_failure(self) -> bool:
        """A required subsystem that FAILed forbids entering interactive mode.

        §5: FAIL on a *required* subsystem means refuse the session (or enter a
        read-only diagnose mode). FAIL on an *optional* one (a named-but-missing
        WordNet archive, P-IH5) is honest reporting, not a boot blocker.
        """

        return any(
            r.liveness is Liveness.FAIL and not r.optional for r in self.records
        )

    def render(self) -> tuple[str, ...]:
        """Kernel-style boot lines (§5). Liveness chrome, never a verdict."""

        lines = []
        for record in self.records:
            lines.append(
                f"[{record.liveness.value:<4}] {record.subsystem_id:<20} "
                f"{record.detail}"
            )
        lines.append(
            f"registered paths: {len(self.registered_ids())}  "
            f"optional off: {len(self.optional_off_ids())}"
        )
        return tuple(lines)


def _module_present(name: str) -> bool:
    """True iff ``name`` can be imported without importing it.

    ``find_spec`` raises :class:`ModuleNotFoundError` when an intermediate
    parent package is missing (e.g. probing ``pantograph.server`` with no
    ``pantograph``); that is an ABSENT signal, not a crash, so it is caught.
    """

    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def probe_wordnet(*, offline: bool, env: str | None) -> CapabilityRecord:
    """OFF when unconfigured, OK when the named archive exists, FAIL otherwise.

    This is P-IH5's honesty rule made executable and it mirrors
    :meth:`retrieval.UnifiedKnowledgeStore.load`, which raises for a named but
    missing archive rather than silently degrading to five stores: an unset
    ``COROLLARY_WORDNET`` is a graceful absence (OFF), a *named* path that does
    not exist is a loud misconfiguration (FAIL), never quietly the same as
    absence.
    """

    if offline:
        return CapabilityRecord(
            "retrieve.wordnet", Liveness.OFF, "offline boot forced OFF", True
        )
    if not env:
        return CapabilityRecord(
            "retrieve.wordnet",
            Liveness.OFF,
            "no archive (set COROLLARY_WORDNET=...)",
            True,
        )
    path = Path(env)
    if path.is_file():
        return CapabilityRecord(
            "retrieve.wordnet", Liveness.OK, f"archive {path.name}", True
        )
    return CapabilityRecord(
        "retrieve.wordnet",
        Liveness.FAIL,
        f"named archive does not exist: {env}",
        True,
    )


def probe_lean(*, offline: bool) -> CapabilityRecord:
    """OK when PyPantograph imports, OFF otherwise. Never FAIL: a missing
    optional prover is an absent dependency, and proof goals degrade to
    replay-only or REFUSED (§7), they do not brick the session."""

    if offline:
        return CapabilityRecord(
            "prover.lean_live", Liveness.OFF, "offline boot forced OFF", True
        )
    if _module_present("pantograph.server"):
        return CapabilityRecord(
            "prover.lean_live", Liveness.OK, "PyPantograph importable", True
        )
    return CapabilityRecord(
        "prover.lean_live", Liveness.OFF, "pantograph unavailable", True
    )


def probe_torch(*, offline: bool) -> CapabilityRecord:
    """OK when Torch imports, OFF otherwise. Optional neural tools ride on this;
    with it OFF the pure-symbolic session stays first-class (§7)."""

    if offline:
        return CapabilityRecord(
            "tool.torch", Liveness.OFF, "offline boot forced OFF", True
        )
    if _module_present("torch"):
        return CapabilityRecord("tool.torch", Liveness.OK, "torch importable", True)
    return CapabilityRecord("tool.torch", Liveness.OFF, "no torch", True)


#: The committed ledgers ``UnifiedKnowledgeStore.load`` reads with NO existence
#: guard (unlike ``specializations.json``, which it treats as optional). They
#: are a hard dependency of the corpus subsystem, so the boot probe must own
#: them: a checkout with ``data/`` but no ``reports/`` would otherwise raise a
#: ``FileNotFoundError`` from inside ``boot`` — bypassing the contract that a
#: probe returns FAIL and ``boot`` refuses cleanly, never crashes.
REQUIRED_CORPUS_LEDGERS = ("signature_matches.json", "decompositions.json")


def probe_corpus(repo_root: Path) -> CapabilityRecord:
    """Required. Committed ``data/*`` AND the ledgers the store loads
    unconditionally must be present and non-empty, else FAIL (§7).

    The probe reports FAIL; it never lets ``boot`` crash. Because
    ``UnifiedKnowledgeStore.load`` reads ``REQUIRED_CORPUS_LEDGERS`` without an
    existence guard, a data-present/reports-absent checkout has to surface here
    as a clean ``corpus.nodes`` FAIL rather than an unhandled exception one
    call later.
    """

    data_dir = repo_root / "data"
    corpora = sorted(data_dir.glob("*/nodes.json")) if data_dir.is_dir() else []
    if not corpora:
        return CapabilityRecord(
            "corpus.nodes", Liveness.FAIL, "no committed data/*/nodes.json", False
        )
    reports_dir = repo_root / "reports"
    missing = [
        name for name in REQUIRED_CORPUS_LEDGERS if not (reports_dir / name).is_file()
    ]
    if missing:
        return CapabilityRecord(
            "corpus.nodes",
            Liveness.FAIL,
            "missing required ledger(s): " + ", ".join(missing),
            False,
        )
    return CapabilityRecord(
        "corpus.nodes",
        Liveness.OK,
        f"{len(corpora)} corpora",
        False,
    )


def probe_narrative() -> CapabilityRecord:
    """Required. StoryVerifier answers an ``open_frame`` smoke via the oracle."""

    try:
        story = story_oracle_run().final_state
        assert story.frame_state is not None
    except Exception as exc:  # pragma: no cover - required-subsystem breakage
        return CapabilityRecord(
            "narrative.story", Liveness.FAIL, f"story smoke failed: {exc}", False
        )
    return CapabilityRecord(
        "narrative.story", Liveness.OK, "StoryVerifier smoke", False
    )


def probe_belief() -> CapabilityRecord:
    """Required. FrameExecutor opens an owned belief frame smoke."""

    try:
        FrameExecutor().open_frame(
            FrameSpec(frame="runtime.frames.harness_belief_smoke", owner="world")
        )
    except Exception as exc:  # pragma: no cover - required-subsystem breakage
        return CapabilityRecord(
            "belief.ownership", Liveness.FAIL, f"belief smoke failed: {exc}", False
        )
    return CapabilityRecord(
        "belief.ownership", Liveness.OK, "FrameExecutor smoke", False
    )


# --------------------------------------------------------------------------
# Subsystem-agnostic WAITING need channel (docs §2.2, §4.2; P-IH2)
# --------------------------------------------------------------------------


@runtime_checkable
class Need(Protocol):
    """A human-presentable pause record, whatever subsystem raised it.

    P-IH2 (strengthened): *every* subsystem that can pause must supply a need
    record through this one typed channel, and the shell must render it with no
    subsystem-specific knowledge. The protocol carries no subsystem id, no
    verifier handle, nothing a renderer could branch on — a need is a slot and
    the question that fills it, and that is all :func:`render_need` is allowed
    to see. :class:`retrieval.ClarificationRequest` satisfies it structurally
    today; any future pausing subsystem must satisfy it too or it cannot pause.
    """

    slot: str
    prompt: str


class PausingState(Protocol):
    """A session state that may be holding an outstanding :class:`Need`.

    The kernel reads ``.awaiting`` directly (no ``getattr`` duck-typing — the
    same typed-protocol discipline ROADMAP-v0.7 item 6 established): a state
    that can pause exposes this attribute, and :func:`pending_need` returns
    whatever is there without knowing the concrete state type.
    """

    awaiting: Need | None


#: §4.2 status chrome. A single renderer over structured stops; ASCII markers
#: are the floor, color/pulse a progressive enhancement a later slice may add.
WAITING_GLYPH = "..."
STATUS_GLYPH = {
    StopReason.SOLVED: "[OK]",
    StopReason.WAITING: f"[{WAITING_GLYPH}]",
    StopReason.EXHAUSTED: "[--]",
    StopReason.BUDGET: "[t]",
}


def pending_need(state: PausingState) -> Need | None:
    """The outstanding need on any pausing state, or None."""

    return state.awaiting


def render_need(need: Need) -> str:
    """Render a pause as a system question — subsystem-agnostic by construction.

    Reads only ``need.prompt`` (and names the slot). It cannot branch on which
    subsystem raised the need because a :class:`Need` exposes nothing else,
    which is exactly the property P-IH2 asserts. The human never sees the word
    ASK (§2.2); they see a pulsing question.
    """

    return f"[{WAITING_GLYPH}] {need.prompt}"


def render_stop(result: RunResult) -> str:
    """One status line over a structured run result (§4.2).

    On WAITING the line carries the rendered need, so a caller with an input
    channel can present it; on a terminal stop it carries the glyph and the
    last verdict. No verdict exists only as a rendered character — this reads
    the structured trace.
    """

    glyph = STATUS_GLYPH.get(result.stop_reason, "[?]")
    if result.stop_reason is StopReason.WAITING:
        # `.awaiting` is consulted ONLY on the WAITING branch: a terminal stop
        # (SOLVED/EXHAUSTED/BUDGET) may carry a state that never opened a need
        # channel — a non-retrieval subsystem's plain state (docs §10) — and it
        # must render from the structured trace without touching an attribute
        # it was never required to expose.
        need = pending_need(result.final_state)
        if need is not None:
            return f"{glyph} {render_need(need)}"
    verdict = (
        result.trace[-1].verification.verdict.value if result.trace else "none"
    )
    return f"{glyph} {result.stop_reason.value} (last verdict {verdict})"


# --------------------------------------------------------------------------
# Structured session trace (docs §4.2: typed records, not strings)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SessionEvent:
    """One structured trace record; TTY chrome is a renderer over these."""

    subsystem_id: str
    kind: str
    verdict: str | None
    stop_reason: str | None
    detail: str
    need_prompt: str | None = None


# --------------------------------------------------------------------------
# The Phase-1 offline core session (docs §3.3, §9 Phase 1)
# --------------------------------------------------------------------------


@dataclass
class CoreSession:
    """One live session over the microkernel, sharing one verifier and frame.

    Narrative revision, a visibility-derived belief query, and corpus retrieval
    interleave here because they share the kernel contract (§3.3), not because
    one model holds all skills. The session threads a single ``session_id`` and
    a single :class:`frames.FrameExecutor` across every leg; the verifier is the
    retrieve subsystem's, reused for the frame-private ASK leg because a
    user-private ASK never touches the store.

    Scope of THIS slice: a durable-for-the-session structured trace and the
    WAITING channel. It is deliberately NOT the Phase-2 need dispatcher and
    holds no session budget or cross-hop loop detection; ``_pruning`` on the
    verifier is the substrate a later slice threads (P-IH7), untouched here.
    """

    matrix: CapabilityMatrix
    executor: FrameExecutor
    verifier: RetrievalVerifier
    story: StoryState
    controller: Controller = field(default_factory=lambda: Controller(max_steps=8))
    session_id: str = field(default_factory=lambda: secrets.token_hex(16))
    state: RetrievalState | None = None
    active_slot: str | None = None
    events: list[SessionEvent] = field(default_factory=list)

    # -- boot -------------------------------------------------------------

    @classmethod
    def boot(
        cls,
        repo_root: Path,
        *,
        offline: bool = False,
        wordnet_env: str | None = None,
        session_id: str | None = None,
    ) -> "CoreSession":
        """Detect capabilities like kernel init, then build the session.

        ``session_id`` is supplied only by callers that must be able to
        REPRODUCE a session — the recorded run of ROADMAP-v0.10 item 5 writes
        a committed transcript, and a random id would make that transcript
        differ from itself on every run. Default stays the random token: an
        interactive session's identity is not the caller's to choose.

        ``offline=True`` forces every optional subsystem OFF regardless of what
        is installed — the honest way to reproduce a WordNet/Lean/Torch-absent
        box on one that happens to have them, and what P-IH1 boots under.
        ``wordnet_env`` defaults to the ``COROLLARY_WORDNET`` environment
        variable so an online boot honors the same archive the store does.
        """

        if wordnet_env is None and not offline:
            wordnet_env = os.environ.get("COROLLARY_WORDNET")

        records = (
            probe_corpus(repo_root),
            probe_narrative(),
            probe_belief(),
            probe_wordnet(offline=offline, env=wordnet_env),
            probe_lean(offline=offline),
            probe_torch(offline=offline),
        )
        matrix = CapabilityMatrix(records)
        if matrix.has_required_failure:
            raise RuntimeError(
                "a required subsystem FAILed its boot probe; refusing to enter "
                "interactive mode: "
                + ", ".join(
                    r.subsystem_id
                    for r in records
                    if r.liveness is Liveness.FAIL and not r.optional
                )
            )

        executor = FrameExecutor()
        # The retrieve subsystem's store. WordNet is loaded ONLY when its probe
        # registered OK, so a five-store session never silently gains a sixth.
        wn = matrix.get("retrieve.wordnet")
        wordnet_path = (
            Path(wordnet_env) if (wn.registered and wordnet_env) else None
        )
        store = UnifiedKnowledgeStore.load(
            repo_root / "data", repo_root / "reports", wordnet_path
        )
        verifier = RetrievalVerifier(store, executor)
        story = story_oracle_run().final_state
        session = cls(
            matrix=matrix,
            executor=executor,
            verifier=verifier,
            story=story,
            **({"session_id": session_id} if session_id else {}),
        )
        session.events.append(
            SessionEvent(
                "kernel",
                "boot",
                None,
                None,
                "registered "
                + ",".join(matrix.registered_ids())
                + "; optional off "
                + ",".join(matrix.optional_off_ids()),
            )
        )
        return session

    # -- kernel loop ------------------------------------------------------

    def run_turn(self, actions) -> RunResult[RetrievalState]:
        """Run one bounded controller turn over the current state.

        The completion and waiting predicates are the existing ones: a turn is
        SOLVED when the active private slot has an authoritative binding or the
        pending need cleared, and WAITING when the verifier minted an
        outstanding question. WAITING is surfaced through the generic need
        channel; the kernel never inspects which subsystem paused.
        """

        if self.state is None:
            raise ValueError("no open goal; open a frame-private slot first")
        slot = self.active_slot
        result = self.controller.run(
            self.state,
            SequencePolicy(tuple(actions)),
            self.verifier,
            is_complete=lambda s: (
                s.pending is None
                and (
                    slot is None
                    or self.verifier.binding_value(s, slot) is not None
                )
            ),
            is_waiting=lambda s: s.awaiting is not None,
        )
        self.state = result.final_state
        self._record_turn("retrieval-harness", result)
        return result

    def _record_turn(self, subsystem_id: str, result: RunResult) -> None:
        verdict = (
            result.trace[-1].verification.verdict.value if result.trace else None
        )
        need = pending_need(result.final_state)
        self.events.append(
            SessionEvent(
                subsystem_id,
                "turn",
                verdict,
                result.stop_reason.value,
                render_stop(result),
                need.prompt if need is not None else None,
            )
        )

    # -- leg 1: open a fiction frame, bind a private slot via WAITING ------

    def open_fiction_slot(
        self,
        slot: str,
        literal: Literal,
        *,
        owner: str = "interlocutor",
    ) -> None:
        """Open (or reopen) a frame-private slot over the accepted fiction.

        The frame is the story oracle's accepted final frame — a live narrative
        subsystem, not a demo mode. The slot is user-owned (``channel='user'``),
        so RETRIEVE cannot impersonate the interlocutor and the only way to fill
        it is a signed reply. The new state is threaded onto this session's id.
        """

        if self.state is not None and (
            self.state.pending is not None or self.state.awaiting is not None
        ):
            raise ValueError("cannot open a new goal while another is unresolved")
        fresh = RetrievalState.from_unknown(
            self.executor,
            self.story.frame_state,
            slot,
            slot,
            literal,
            resolution_channel="user",
            user_owner=owner,
        )
        prior_user_frame = (
            self.state.user_frame if self.state is not None else fresh.user_frame
        )
        self.state = replace(
            fresh,
            session_id=self.session_id,
            user_frame=prior_user_frame,
        )
        self.active_slot = slot

    def ask(self, slot: str) -> RunResult[RetrievalState]:
        """Propose the verifier-minted question; the turn stops WAITING."""

        return self.run_turn((ask_action(slot),))

    def answer(self, value: str) -> RunResult[RetrievalState]:
        """Inject a signed reply through the trusted return channel.

        The signature is minted by the verifier's ``reply_action`` — the shell
        cannot forge it and does not try to. A policy that guessed a value could
        never produce this signature, which is the whole point of the channel.
        """

        if self.state is None or self.state.awaiting is None:
            raise ValueError("no outstanding question to answer")
        reply = self.verifier.reply_action(self.state, value)
        return self.run_turn((reply,))

    def binding(self, slot: str) -> str | None:
        if self.state is None:
            return None
        return self.verifier.binding_value(self.state, slot)

    # -- leg 2: answer a visibility-derived belief query ------------------

    def false_belief_query(
        self,
        subject: str,
        predicate: str,
        *,
        observer: str = "sally",
    ) -> tuple[str | None, str | None]:
        """Derive an observer's belief vs the world's, from visibility alone.

        The Sally-Anne shape, but general: the observer witnesses the placement
        and not the move, so its belief frame and the world frame diverge with
        no leak between them. Uses this session's executor (belief.ownership
        subsystem); no optional dependency is touched.
        """

        believer = self.executor.open_frame(
            FrameSpec(frame=f"runtime.frames.belief_{observer}", owner=observer)
        )
        world = self.executor.open_frame(
            FrameSpec(frame="runtime.frames.belief_world", owner="world")
        )
        origin = Literal(subject, predicate, "basket")
        placement = FrameEvent(
            "placement", (origin,), (observer, "anne", "world"), (predicate,)
        )
        move = FrameEvent(
            "move",
            (origin.negated, Literal(subject, predicate, "box")),
            ("anne", "world"),
            (predicate,),
        )
        for event in (placement, move):
            believer = self.executor.observe_event(believer, event).next_state
            world = self.executor.observe_event(world, event).next_state
        believed = self.executor.belief_value(believer, subject, predicate)
        actual = self.executor.belief_value(world, subject, predicate)
        self.events.append(
            SessionEvent(
                "belief.ownership",
                "belief",
                Verdict.VERIFIED.value,
                None,
                f"{observer} believes {subject} {predicate} {believed!r}; "
                f"world holds {actual!r}",
            )
        )
        return believed, actual

    # -- leg 3: retrieve a corpus twin ------------------------------------

    def retrieve(self, key: str, *, slot: str = "answer") -> RunResult[RetrievalState]:
        """Walk the item-6 miss chain for one public key; return the run.

        A store-channel need over an open retrieval frame, threaded onto this
        session's id, walked by ``retrieval.run_miss_chain`` — the same ladder
        (exact -> neighborhood -> derivation -> tool -> ASK) the retrieval layer
        already ships, not a parallel dispatcher. The resulting context is
        pointable material; a corpus twin group surfaces on the exact rung when
        the key names a twin member.
        """

        frame = self.executor.open_frame(
            FrameSpec(frame="runtime.frames.harness_retrieval", retrieval="open")
        )
        need_state = RetrievalState.from_unknown(
            self.executor,
            frame,
            slot,
            key,
            Literal("request", "needs", key),
        )
        need_state = replace(need_state, session_id=self.session_id)
        run = run_miss_chain(self.verifier, need_state)
        verdict = (
            run.trace[-1].verification.verdict.value if run.trace else None
        )
        self.events.append(
            SessionEvent(
                "retrieve.five_store",
                "retrieve",
                verdict,
                run.stop_reason.value,
                f"key {key!r}: {len(run.final_state.context)} pointable item(s)",
            )
        )
        return run


# --------------------------------------------------------------------------
# One typed line (v0.12 item 5; docs/DESIGN-live-session.md)
# --------------------------------------------------------------------------
#
# v0.8's notes said the system could be driven. What existed was this boot
# list and a *recorded* session replayed by `scripts/session_run.py --check`.
# This section is the reclamation: after the list, read ONE line, route it to
# a program that already exists, print that program's own verdict, stop.
#
# Both routes are existing programs called through their public adapters. The
# rule that makes this honest is that neither refusal text is written here --
# the write gate's check name and the dispatcher's stop reason are printed as
# they come back. A paraphrase invented in this file would be a costume, and
# is exactly what P-LS3 calls a miss.
#
# Imports for the two routes are function-local on purpose: `session_run`
# imports `CoreSession` from this module, so pulling `write_stage` /
# `dispatcher` in at module scope risks an import cycle for every caller that
# only wanted to boot a matrix.

#: The path a free-text line is offered to. It is deliberately NOT registered:
#: no registered path claims arbitrary English, and inventing one is the
#: "fluent unregistered content emitted as a fact" that P-LS2 forbids.
UNREGISTERED_PATH = "tool.freeform_answer"

#: The one command word that reaches an exact answer. A literal head word,
#: not a phrase the shell interprets: `owns x ^ 2` routes, "who owns x^2?"
#: does not and is abstained on. That asymmetry is deliberate -- a command
#: is registered, English is not, and pretending otherwise is the costume.
OWNS_COMMAND = "owns"


def _looks_like_path(line: str) -> bool:
    """Closed form: is this line an *attempt* at a repository-relative path?

    A syntactic test, not a guess about intent. Prose carries whitespace; a
    proposal path does not, and either ends in `.json` or carries a
    separator. A path that does not exist still routes to the write gate on
    purpose, so the gate's own named refusal is what the person sees instead
    of a message this file made up.
    """
    if not line or any(ch.isspace() for ch in line):
        return False
    return line.endswith(".json") or "/" in line or "\\" in line


def _existing_file(repo_root: Path, line: str) -> bool:
    """True when the line names a regular file inside the repository."""
    try:
        return (repo_root / line).is_file()
    except (OSError, ValueError):
        # Windows rejects `?` and `:` in path components, so a typed question
        # raises here rather than answering False. A question is not a path.
        return False


def _route_write(repo_root: Path, line: str) -> dict:
    """Hand the line to the write gate exactly as the controller would."""

    from write_stage import (  # noqa: PLC0415
        WriteStagingState,
        WriteStagingVerifier,
        write_action,
    )

    verifier = WriteStagingVerifier(repo_root, staging_dir=None)
    result = verifier.evaluate(WriteStagingState(), write_action(line))
    return {
        "route": "write_gate",
        "status": result.verdict.value,
        "detail": result.reason,
        "evidence": list(result.evidence),
    }


def _route_dispatch(session: "CoreSession", line: str) -> dict:
    """Offer the line to the dispatcher as a need on an unregistered path."""

    from dispatcher import NeedDispatcher, RegisteredPath  # noqa: PLC0415
    from retrieval import RetrievalState  # noqa: PLC0415

    def build_state(_subsystem_id: str) -> "RetrievalState":
        frame = session.executor.open_frame(
            FrameSpec(frame="live_session", retrieval="open")
        )
        # The need's key is the typed text itself. Nothing is normalised,
        # completed, or defaulted -- P-LS5 is a property of not writing the
        # code that would fill a slot, not of a check that says we did not.
        return RetrievalState.from_unknown(
            session.executor, frame, "answer", line,
            Literal("request", "needs", line),
        )

    registry = {
        UNREGISTERED_PATH: RegisteredPath(
            UNREGISTERED_PATH, registered=False, build_state=build_state,
        )
    }
    dispatcher = NeedDispatcher.for_session(session, registry)
    result = dispatcher.dispatch(session.session_id, UNREGISTERED_PATH)
    return {
        "route": "dispatcher",
        # `DispatchResult` carries a StopReason and no Verdict at all, so
        # "verified" is unreachable on this route by construction (P-LS2).
        "status": result.stop_reason.value,
        "detail": result.reason,
        "missing_capability": UNREGISTERED_PATH,
        "materialized": result.materialized,
    }


def read_one_line(stream=None) -> str | None:
    """Read exactly one line. `None` means the stream ended without one."""

    import sys  # noqa: PLC0415

    handle = sys.stdin if stream is None else stream
    raw = handle.readline()
    if raw == "":
        return None
    return raw.strip()


def _route_ownership(repo_root: Path, session: "CoreSession", query: str) -> dict:
    """`owns <expr>` — the exact lookup, and the only route that can solve.

    Gated on the boot matrix, not on hope: the answer is read out of the
    committed corpus graph, so if `corpus.nodes` did not register, this
    route refuses instead of answering from somewhere else. That is the
    same registration rule §3.2 applies to every other subsystem.
    """

    from ownership import (  # noqa: PLC0415
        REQUIRES_SUBSYSTEM,
        QueryError,
        lookup,
        render,
    )

    if REQUIRES_SUBSYSTEM not in session.matrix.registered_ids():
        return {
            "route": "ownership",
            "status": "exhausted",
            "detail": (
                f"{REQUIRES_SUBSYSTEM} did not register on this boot; the "
                "ownership lookup reads the committed corpus graph and has "
                "nowhere else to read it from"
            ),
            "missing_capability": REQUIRES_SUBSYSTEM,
        }
    if not query:
        return {
            "route": "ownership",
            "status": "refused",
            "detail": f"{OWNS_COMMAND!r} needs a template expression after it",
        }
    try:
        answer = lookup(query, repo_root / "data")
    except QueryError as exc:
        return {"route": "ownership", "status": "refused", "detail": str(exc)}
    return {
        "route": "ownership",
        # Exact and total: every hosting statement, decided by the matcher's
        # own canonicaliser. `solved` here is a lookup that returned, not a
        # judgement that something is true, useful, or proved.
        "status": "solved" if answer.found else "exhausted",
        "detail": (
            f"{len(answer.hosts)} of {answer.searched} statements host "
            f"{answer.query!r}"
            if answer.found
            else f"no statement hosts {answer.query!r}"
        ),
        "answer": render(answer),
    }


def route_line(repo_root: Path, session: "CoreSession", line: str | None) -> dict:
    """The whole decision, as data, so a test can assert on it."""

    if line is None or not line:
        # P-LS5: a pause binds nothing. There is no default line, no
        # placeholder need, and no slot filled on the person's behalf.
        return {
            "line": None,
            "route": "none",
            "status": "waiting",
            "detail": (
                "no line was typed before the input ended; nothing was "
                "dispatched, nothing was staged, no slot was bound"
            ),
        }
    head, _, rest = line.partition(" ")
    if head.lower() == OWNS_COMMAND:
        return {"line": line, **_route_ownership(repo_root, session, rest.strip())}
    if _existing_file(repo_root, line) or _looks_like_path(line):
        return {"line": line, **_route_write(repo_root, line)}
    return {"line": line, **_route_dispatch(session, line)}


def render_verdict(verdict: dict) -> list[str]:
    """The structured stop, in the order a person reads it."""

    out = ["", "--- one typed line ---"]
    out.append(f"line    : {verdict['line'] if verdict['line'] else '(none typed)'}")
    out.append(f"route   : {verdict['route']}")
    out.append(f"status  : {verdict['status']}")
    out.append(f"detail  : {verdict['detail']}")
    for item in verdict.get("evidence", ()):
        out.append(f"evidence: {item}")
    if verdict.get("missing_capability"):
        out.append(f"missing : {verdict['missing_capability']}")
    for item in verdict.get("answer", ()):
        out.append(f"  {item}")
    return out


def main() -> int:
    """Print the offline boot matrix, then read one line and stop."""

    repo_root = Path(__file__).resolve().parent.parent
    session = CoreSession.boot(repo_root, offline=True)
    print(f"corollary kernel (offline) session {session.session_id[:12]}...")
    for line in session.matrix.render():
        print(line)

    typed = read_one_line()
    verdict = route_line(repo_root, session, typed)
    for row in render_verdict(verdict):
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
