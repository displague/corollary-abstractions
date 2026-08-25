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
import json
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
    RetrievalItem,
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

#: Probes over data this repository *ships* rather than over an installed
#: dependency. They are deliberately NOT in :data:`OPTIONAL_SUBSYSTEMS`: that
#: tuple names the three optional dependency *families*, and P-IH1 asserts an
#: offline session registers none of them
#: (``tests/test_session_offline.py:106``). ``offline=True`` reproduces a box
#: where an optional install is absent — it has nothing to say about committed
#: files, which are present either way, so forcing this probe OFF offline
#: would withhold a route for a reason that is not true of the box. Recorded
#: non-optional so a green offline matrix keeps meaning what P-IH1 says it
#: means; the probe can never FAIL, so it can never block boot the way a
#: required FAIL does.
COMMITTED_ARTIFACT_SUBSYSTEMS = ("closure.worlds",)


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
            "no archive (fetch_sources.py --fetch wordnet-2025-json, "
            "or set COROLLARY_WORDNET=...)",
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


def probe_closure_worlds(repo_root: Path) -> CapabilityRecord:
    """OK when every registered closure world has a sealed closure beside it.

    Reads the committed manifest and registrations with plain JSON rather than
    importing the query stack: a boot probe must be able to say OFF about a
    checkout it cannot parse, and importing ``closure_query`` here would let a
    broken world raise out of ``boot`` instead.

    Never FAIL, on ``probe_lean``'s shape: an absent closure set is an absent
    artifact, and the ``reachable`` route degrades to a named refusal rather
    than bricking the session.
    """

    manifest = repo_root / "data" / "closure_worlds" / "manifest.json"
    if not manifest.is_file():
        return CapabilityRecord(
            "closure.worlds",
            Liveness.OFF,
            "no data/closure_worlds/manifest.json",
            False,
        )
    try:
        entries = json.loads(manifest.read_text(encoding="utf-8"))["files"]
        world_ids = [
            json.loads(
                (repo_root / entry["path"]).read_text(encoding="utf-8")
            )["world_id"]
            for entry in entries
        ]
    except (OSError, TypeError, ValueError, KeyError) as exc:
        return CapabilityRecord(
            "closure.worlds", Liveness.OFF, f"unreadable registrations: {exc}", False
        )
    closures = repo_root / "reports" / "closures"
    missing = [
        world_id
        for world_id in world_ids
        if not (closures / f"{world_id}.closure.json").is_file()
    ]
    if missing:
        return CapabilityRecord(
            "closure.worlds",
            Liveness.OFF,
            "no sealed closure for: " + ", ".join(missing),
            False,
        )
    return CapabilityRecord(
        "closure.worlds", Liveness.OK, f"{len(world_ids)} worlds registered", False
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

    Scope of THIS slice: a durable-for-the-session structured trace, the
    WAITING channel, and the v0.13 resolver clarification subloop.  The latter
    keeps only symbolic candidates, accepts explicit hard constraints, and
    terminates visibly on repetition or at its hop ceiling.  It is deliberately
    NOT the Phase-2 need dispatcher; ``_pruning`` on the verifier remains the
    substrate a later slice threads (P-IH7), untouched here.
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
    # A resolver ASK is a real session object, not terminal text.  The next
    # typed line narrows this exact candidate set; no candidate is chosen on
    # the person's behalf.  These fields deliberately hold only symbolic
    # graph identifiers and the person's own words.
    pending_candidates: tuple[str, ...] = ()
    pending_query: str | None = None
    pending_resolver: str | None = None
    context_hops: int = 0
    context_seen: set[tuple[tuple[str, ...], tuple[str, ...]]] = field(
        default_factory=set
    )
    resolver_index: object | None = None

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
        variable so an online boot honors the same archive the store does;
        with that unset it falls back to the manifest-pinned fetch location
        (``gloss.pinned_archive_path``), so a checkout that ran
        ``fetch_sources.py --fetch wordnet-2025-json`` registers the
        dictionary without configuration. The fallback only ever supplies a
        file that exists, so P-IH5's loud FAIL stays reserved for a path a
        person named by hand.
        """

        if wordnet_env is None and not offline:
            wordnet_env = os.environ.get("COROLLARY_WORDNET")
            if wordnet_env is None:
                from gloss import pinned_archive_path  # noqa: PLC0415

                pinned = pinned_archive_path(repo_root)
                if pinned is not None:
                    wordnet_env = str(pinned)

        records = (
            probe_corpus(repo_root),
            probe_narrative(),
            probe_belief(),
            probe_closure_worlds(repo_root),
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

#: Where fabrication is legal. Conjecture, hypotheticals, opinions and
#: outright fiction are not errors — they are claims that belong in a frame
#: the person owns, marked `conjectured`, never quotable as corpus fact.
SUPPOSE_COMMAND = "suppose"

#: Wiring step W1 (`docs/SPEC-chat-completions-skin.md` §9, ¶DEV-2). The twin
#: ledger is a REQUIRED_CORPUS_LEDGERS entry and `CoreSession.retrieve` has
#: surfaced its groups all along, but no typed line ever called that method,
#: so the material was line-unreachable over every skin. This command is the
#: surface, not a new capability: it adds no rung to the miss chain.
TWIN_COMMAND = "twin"

#: The one artifact a twin answer rests on, quoted rather than paraphrased.
TWIN_LEDGER_PATH = "reports/signature_matches.json"

#: The subsystem that owns the twin ledger — it is one of
#: :data:`REQUIRED_CORPUS_LEDGERS`, so `twin` is gated on the same probe the
#: corpus graph is.
CORPUS_SUBSYSTEM = "corpus.nodes"

#: The ledger's own group order (`scripts/retrieval.py:487-517`), strongest
#: first. A statement that appears in several groups is answered from the
#: strongest one so the level in the answer is a floor, not a coin toss.
TWIN_LEVEL_ORDER = ("typed", "family", "aliased", "mirror", "shape")

#: Wiring step W2 (§9). `closure_query` shipped as a standalone CLI wired
#: into no session route; this is its line form. `_looks_like_path` cannot
#: capture the line (it rejects anything containing whitespace), so ordering
#: it with the other head-guarded commands costs the write gate nothing.
REACHABLE_COMMAND = "reachable"

#: The subsystem `reachable` reads through. Gated for the same reason
#: ownership is: the answer is read out of committed closures, and with none
#: registered the route has nowhere else to read one from.
CLOSURE_SUBSYSTEM = "closure.worlds"

#: The registered target set, and the reason the route consults it at all
#: (spec §9). ``closure_query.query`` certifies a bounded negative for
#: *whatever bytes it is handed*, so an ungated route would mint a sealed
#: "not reachable within horizon N" receipt naming a real closure for every
#: file in the repository — the self-fulfilling-arm hole reopened from the
#: other side. Answering only about listed paths also gives each receipt's
#: ``target_digest`` committed provenance to recheck against.
CLOSURE_TARGET_MANIFEST = "data/closure_targets/manifest.json"


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


def _route_gloss(session: "CoreSession", line: str) -> dict | None:
    """A dictionary sense, when the corpus has nothing and WordNet does.

    Ordered AFTER corpus resolution on purpose: this project's statements
    outrank a dictionary entry for anything the graph actually holds. It
    runs before the dispatcher abstains, so "what is a chicken" gets a real
    human-written definition instead of a refusal — quoted, not generated.

    Gated on the boot matrix. Without the archive the route reports nothing
    and the dispatcher abstains as before, rather than silently answering
    from an empty index.
    """

    from gloss import REQUIRES_SUBSYSTEM, definitional_target, look_up  # noqa: PLC0415
    from gloss import render as render_gloss  # noqa: PLC0415

    if REQUIRES_SUBSYSTEM not in session.matrix.registered_ids():
        return None
    # Only when a definition was actually asked for. Firing on any line that
    # contains a dictionary word answered "tell me a story about a chicken"
    # by defining chicken, which is a non-sequitur dressed as an answer.
    word = definitional_target(line)
    if not word:
        return None
    gloss = look_up(word)
    if gloss is None or not gloss.found:
        return None
    return {
        "route": "gloss",
        # `found`, like resolution: a dictionary sense is not a settled
        # question and never a corpus fact.
        "status": "found",
        "detail": f"{word}: {len(gloss.senses)} dictionary sense(s)",
        "answer": render_gloss(gloss),
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
        # Not a dead end. Text the corpus cannot ground is still sayable --
        # as conjecture, in a frame the person owns. Offering the route
        # rather than taking it silently is the difference between holding a
        # supposition and inventing one.
        "answer": [
            "the corpus does not ground this, and nothing here will pretend "
            "otherwise.",
            f"to hold it as conjecture instead, type:  "
            f"{SUPPOSE_COMMAND} {line}",
        ],
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
        # The lookup's own result, carried the way `_route_twin` and
        # `_route_reachable` already carry theirs (`:1589`, `:1769`). This
        # route was the one that did not follow the convention: it ran the
        # expensive lookup, rendered five witness hosts out of thousands,
        # and dropped the object — so a renderer that had to cite the host
        # set could only run the identical lookup a second time. Returning
        # it is a convention alignment, not a new capability: every field
        # here is `ownership.Ownership`'s own, unrenamed and unsummarised.
        "receipt": {
            "query_skeleton": answer.query_skeleton,
            "hosts": list(answer.hosts),
            "searched": answer.searched,
            "by_corpus": [[corpus, count] for corpus, count in answer.by_corpus],
        },
    }


def _resolver_index(session: "CoreSession"):
    """Build the immutable graph index once per live session."""

    if session.resolver_index is None:
        from resolver import default_index  # noqa: PLC0415

        session.resolver_index = default_index()
    return session.resolver_index


def _route_resolver(
    repo_root: Path, session: "CoreSession", line: str
) -> dict | None:
    """Free text through the resolver chain. `None` means nobody claimed it.

    Returning `None` rather than a verdict is deliberate: an unclaimed line
    must still reach the dispatcher and be abstained on there, so P-LS2's
    guarantee is unchanged. This route can only ever turn an `exhausted`
    into a `solved` or a named `waiting` -- never into a fact the graph does
    not hold.
    """

    from ownership import REQUIRES_SUBSYSTEM  # noqa: PLC0415
    from resolver import ASK, BIND, render, resolve  # noqa: PLC0415

    if REQUIRES_SUBSYSTEM not in session.matrix.registered_ids():
        return None
    index = _resolver_index(session)
    outcome = resolve(line, index)
    if outcome.kind == BIND:
        _clear_pending(session)
        from answer import compose  # noqa: PLC0415
        from answer import render as render_answer  # noqa: PLC0415

        composed = compose(outcome.bound or "")
        body = (
            render_answer(composed)
            if composed is not None
            else render(outcome, index)
        )
        return {
            "route": "resolver",
            # `found`, not `solved`. Resolution locates a statement whose
            # words match; it does not answer a question or confirm an
            # assertion. Typing "the corpus contains a proof of the Riemann
            # hypothesis" should surface related statements, and calling
            # that `solved` would read as agreement. `solved` is reserved
            # for exact computation and exact lookup, where something really
            # was settled.
            "status": "found",
            "detail": f"{outcome.resolver}: {outcome.detail}",
            "answer": body,
        }
    if outcome.kind == ASK:
        # Ambiguity is a question containing the real alternatives. `waiting`
        # is the kernel's own word for "a person owes the next move", and no
        # candidate is chosen on their behalf (P-LS5).
        session.pending_candidates = outcome.candidates
        session.pending_query = line
        session.pending_resolver = outcome.resolver
        session.context_hops = 0
        session.context_seen.clear()
        return {
            "route": "resolver",
            "status": "waiting",
            "detail": f"{outcome.resolver}: {outcome.detail}",
            "answer": render(outcome, index),
        }
    return None


MAX_CONTEXT_HOPS = 4
NARROW_COMMAND = "narrow"
CANCEL_COMMAND = "cancel"
CONTEXT_KINDS = frozenset({"corpus", "discipline", "word", "id"})


def _context_constraint(line: str) -> tuple[str, str] | None:
    """Parse ``narrow KIND VALUE`` without guessing omitted structure."""

    parts = line.strip().split(maxsplit=2)
    if len(parts) != 3 or parts[0].casefold() != NARROW_COMMAND:
        return None
    kind = parts[1].casefold()
    value = parts[2].strip().casefold()
    if kind not in CONTEXT_KINDS or not value:
        return None
    return kind, value


def _narrow_candidates(
    index,
    candidates: tuple[str, ...],
    kind: str,
    value: str,
) -> tuple[str, ...]:
    """Apply one complete declared constraint; never rank or break a tie."""

    from answer import compose  # noqa: PLC0415
    from resolver import reduce_text  # noqa: PLC0415

    if kind == "id":
        return (value,) if value in candidates else ()
    if kind == "corpus":
        return tuple(
            sid for sid in candidates
            if index.corpus_of.get(sid, "").casefold() == value
        )
    if kind == "discipline":
        return tuple(
            sid
            for sid in candidates
            if (answer := compose(sid)) is not None
            and value in {discipline.casefold() for discipline in answer.disciplines}
        )
    words = tuple(reduce_text(value.replace("_", " ").replace(".", " ")))
    if len(words) != 1:
        return ()
    word = words[0]
    owners: set[str] = set()
    for postings in (index.by_keyword, index.by_lexicon, index.by_prose):
        owners.update(postings.get(word, ()))
    return tuple(sid for sid in candidates if sid in owners)


def _restatement(statement_id: str) -> tuple[str, ...]:
    """Verbatim corpus text naming the selected reading (A3)."""

    from answer import compose  # noqa: PLC0415

    answer = compose(statement_id)
    if answer is None:
        return ()
    # Labels are rendered by the shell; every value here is copied verbatim
    # from committed corpus fields.  Empty fields are omitted, never filled.
    return tuple(text for text in (answer.title, answer.meaning) if text)


def _clear_pending(session: "CoreSession") -> None:
    session.pending_candidates = ()
    session.pending_query = None
    session.pending_resolver = None
    session.context_hops = 0
    session.context_seen.clear()


def _route_pending_context(session: "CoreSession", line: str) -> dict:
    """Narrow the live ASK with one more line, or name why it stopped.

    Repeating a no-progress state is a visible cycle.  Four distinct
    no-decision hops hit a visible ceiling.  Both terminate rather than
    manufacturing a winner, which is P-LS6's load-bearing promise.
    """

    from resolver import ASK, Resolution, render  # noqa: PLC0415

    if line.strip().casefold() == CANCEL_COMMAND:
        _clear_pending(session)
        return {
            "route": "resolver_context",
            "status": "canceled",
            "detail": "pending candidate set canceled; no reading was chosen",
        }
    constraint = _context_constraint(line)
    if constraint is None:
        return {
            "route": "resolver_context",
            "status": "waiting",
            "detail": (
                "use 'narrow corpus VALUE', 'narrow discipline VALUE', "
                "'narrow word VALUE', 'narrow id VALUE', or 'cancel'; "
                "no reading was chosen"
            ),
        }

    index = _resolver_index(session)
    before = session.pending_candidates
    kind, value = constraint
    signature = (before, (kind, value))
    if signature in session.context_seen:
        original = session.pending_query or ""
        _clear_pending(session)
        return {
            "route": "resolver_context",
            "status": "cycle",
            "detail": (
                "context cycle: the same follow-up reached the same candidate "
                f"set for {original!r}; no reading was chosen"
            ),
        }
    session.context_seen.add(signature)
    session.context_hops += 1

    matched = _narrow_candidates(index, before, kind, value)
    remaining = matched or before

    if len(remaining) == 1:
        chosen = remaining[0]
        original = session.pending_query or ""
        restatement = _restatement(chosen)
        if not restatement:
            if session.context_hops >= MAX_CONTEXT_HOPS:
                _clear_pending(session)
                return {
                    "route": "resolver_context",
                    "status": "hop_ceiling",
                    "detail": (
                        f"visible hop ceiling {MAX_CONTEXT_HOPS} reached with "
                        "one unrenderable candidate; no reading was chosen"
                    ),
                }
            session.pending_candidates = remaining
            return {
                "route": "resolver_context",
                "status": "waiting",
                "detail": (
                    f"{chosen} is the sole candidate, but it has no committed "
                    "title or statement meaning to quote; no reading was chosen"
                ),
            }
        _clear_pending(session)
        return {
            "route": "resolver_context",
            "status": "found",
            "detail": (
                f"context narrowed {len(before)} candidates to {chosen}; "
                f"reading selected for {original!r}"
            ),
            "reading": restatement,
            "answer": (f"source     : {chosen}",),
        }

    if session.context_hops >= MAX_CONTEXT_HOPS:
        count = len(remaining)
        _clear_pending(session)
        return {
            "route": "resolver_context",
            "status": "hop_ceiling",
            "detail": (
                f"visible hop ceiling {MAX_CONTEXT_HOPS} reached with {count} "
                "candidate(s); no reading was chosen"
            ),
        }

    session.pending_candidates = remaining
    detail = (
        f"{kind}={value!r} narrowed {len(before)} candidates to {len(remaining)}"
        if matched
        else f"{kind}={value!r} matched none; kept {len(before)} candidates"
    )
    narrowed = Resolution(
        ASK,
        session.pending_resolver or "context",
        remaining,
        detail,
    )
    return {
        "route": "resolver_context",
        "status": "waiting",
        "detail": narrowed.detail,
        "answer": render(narrowed, index),
    }


def _route_story(session: "CoreSession", text: str) -> dict | None:
    """A story request, answered by the committed story the verifier checks.

    Gated on `narrative.story`. The system does not invent a story; it holds
    one and can show that it is well formed, so the status is `found` and
    never `solved`.
    """

    from story import REQUIRES_SUBSYSTEM, constraint_prose, is_story_request  # noqa: PLC0415
    from story import render as render_story  # noqa: PLC0415
    from story import tell  # noqa: PLC0415

    if not is_story_request(text):
        return None
    if REQUIRES_SUBSYSTEM not in session.matrix.registered_ids():
        return {
            "route": "story",
            "status": "exhausted",
            "detail": f"{REQUIRES_SUBSYSTEM} did not register on this boot",
            "missing_capability": REQUIRES_SUBSYSTEM,
        }
    told = tell()
    return {
        "route": "story",
        "status": "found" if told.solved else "waiting",
        "detail": (
            f"one committed story, verified: {told.accepted} beats accepted, "
            f"{told.rejected} rejected"
        ),
        "answer": render_story(told, constraint_prose()),
    }


def _route_belief(session: "CoreSession", text: str) -> dict | None:
    """`where does A think B is` — answered from A's frame, not the world.

    Gated on `belief.ownership`, the subsystem that owns frame reasoning. If
    it did not register, this route refuses rather than answering belief
    questions from somewhere else.
    """

    from belief import answer  # noqa: PLC0415
    from belief import render as render_belief  # noqa: PLC0415

    result = answer(text)
    if result is None:
        return None
    if "belief.ownership" not in session.matrix.registered_ids():
        return {
            "route": "belief",
            "status": "exhausted",
            "detail": "belief.ownership did not register on this boot",
            "missing_capability": "belief.ownership",
        }
    return {
        "route": "belief",
        # `found` for the same reason resolution is: this reports what an
        # agent believes, which is not a claim about the world.
        "status": "found" if result.place else "waiting",
        "detail": (
            f"{result.agent}: located_in({result.subject}) = {result.place}"
            if result.place
            else f"{result.agent}: located_in({result.subject}) not derivable"
        ),
        "answer": render_belief(result),
    }


def _route_evaluate(text: str) -> dict | None:
    """Compute, if the line contains something computable. Else `None`.

    Only wins when it can actually produce a value: an expression with an
    unbound variable, or no expression at all, falls through to the rest of
    the chain rather than refusing on everyone else's behalf.

    **A registered bound is the one exception (E0e, ROADMAP-v0.20 §4c).**
    `ResourceBound` means this route READ the line, understood it, and
    refuses it — so it returns a `refused` verdict naming the bound instead
    of `None`. Falling through would send `2^200000` to the dispatcher and
    end in a generic abstention, which tells the person the corpus does not
    ground their line when the truth is that this evaluator declines to
    render a number that wide.
    """

    from evaluate import EvalError, ResourceBound, evaluate, verify  # noqa: PLC0415
    from evaluate import render as render_eval  # noqa: PLC0415

    def _refusal(exc: Exception) -> dict:
        return {
            "route": "evaluate",
            "status": "refused",
            "detail": str(exc),
        }

    # A typed relation ("does 2+2=4?") is a question with an exact answer,
    # so it is decided before falling back to computing a value.
    try:
        checked = verify(text)
    except ResourceBound as exc:
        return _refusal(exc)
    except EvalError:
        pass
    else:
        return {
            "route": "evaluate",
            "status": "solved",
            "detail": f"{checked.relation} holds: {'yes' if checked.holds else 'no'}",
            "answer": checked.rendered(),
        }
    try:
        result = evaluate(text)
    except ResourceBound as exc:
        return _refusal(exc)
    except EvalError:
        return None
    return {
        "route": "evaluate",
        "status": "solved",
        "detail": f"{result.expression} = {result.formatted()}",
        "answer": render_eval(result),
    }


def _route_suppose(claim: str) -> dict:
    """Hold a typed claim inside a frame the person owns."""

    from supposition import render as render_supposition  # noqa: PLC0415
    from supposition import suppose  # noqa: PLC0415

    if not claim:
        return {
            "route": "supposition",
            "status": "refused",
            "detail": f"{SUPPOSE_COMMAND!r} needs a claim after it",
        }
    held = suppose(claim)
    return {
        "route": "supposition",
        # `waiting` and not `solved`: a supposition is held, not answered.
        # Calling it solved would be the one word that turns fiction into a
        # result.
        "status": "held" if held.accepted else "waiting",
        "detail": f"held as {held.status} in a frame you own",
        "answer": render_supposition(held),
    }


def _route_twin(session: "CoreSession", statement_id: str) -> dict:
    """`twin <statement-id>` — the committed twin ledger, through the miss chain.

    Walks ``CoreSession.retrieve``, which returns the ledger's groups as
    pointable material on the exact rung, and reports the group that lists
    this statement. Groups the chain returned for a *neighbouring* reason —
    an alias or skeleton match that does not list this id — are dropped
    rather than reported: the answer names member statement ids, and a group
    the statement is not in has none to name for it.

    Gated on `corpus.nodes`, which owns the ledger
    (``REQUIRED_CORPUS_LEDGERS``); the session's pending resolver ASK is not
    consulted or cleared, because `retrieve` opens its own frame and never
    touches ``session.state``.
    """

    if CORPUS_SUBSYSTEM not in session.matrix.registered_ids():
        return {
            "route": "twin",
            "status": "exhausted",
            "detail": (
                f"{CORPUS_SUBSYSTEM} did not register on this boot; the twin "
                "ledger is one of its required ledgers and there is nowhere "
                "else to read it from"
            ),
            "missing_capability": CORPUS_SUBSYSTEM,
        }
    if not statement_id:
        return {
            "route": "twin",
            "status": "refused",
            "detail": f"{TWIN_COMMAND!r} needs one statement id after it",
        }
    if any(ch.isspace() for ch in statement_id):
        return {
            "route": "twin",
            "status": "refused",
            "detail": (
                f"{TWIN_COMMAND!r} takes exactly one statement id; "
                f"{statement_id!r} carries whitespace"
            ),
        }

    run = session.retrieve(statement_id)
    groups = [
        material.item
        for material in run.final_state.context
        if material.item.source == "twin_ledger"
        and statement_id in material.item.source_ids
    ]
    if not groups:
        return {
            "route": "twin",
            "status": "exhausted",
            "detail": (
                f"no group in {TWIN_LEDGER_PATH} lists {statement_id!r} as a "
                "member; that is a statement about this committed ledger and "
                "says nothing about statements it does not cover"
            ),
        }

    def strength(item: RetrievalItem) -> tuple[int, int]:
        _, level, index = item.item_id.split(":", 2)
        order = (
            TWIN_LEVEL_ORDER.index(level)
            if level in TWIN_LEVEL_ORDER
            else len(TWIN_LEVEL_ORDER)
        )
        return order, int(index)

    chosen = min(groups, key=strength)
    _, level, index = chosen.item_id.split(":", 2)
    members = list(chosen.source_ids)
    return {
        "route": "twin",
        # `found`, like resolution: the ledger locates statements that share a
        # structure. It does not claim they say the same thing.
        "status": "found",
        "detail": (
            f"{level} twin group {index}: {len(members)} member statement(s)"
            + (
                f"; {len(groups)} groups list this statement and the "
                "strongest level is reported"
                if len(groups) > 1
                else ""
            )
        ),
        "answer": (
            f"level      : {level}",
            *(f"member     : {member}" for member in members),
            f"ledger     : {TWIN_LEDGER_PATH}",
        ),
        "receipt": {
            "ledger_path": TWIN_LEDGER_PATH,
            "level": level,
            "group_index": int(index),
            "member_ids": members,
        },
    }


#: `closure_query`'s three receipt outcomes, in this route's vocabulary. A
#: `CORRUPT_TARGET` receipt IS an answer, but it is not a grounding claim, so
#: it lands on `refused` beside the exceptions rather than on `found`.
CLOSURE_OUTCOME_STATUS = {
    "REACHABLE": "found",
    "NOT_REACHABLE_WITHIN_HORIZON": "exhausted",
    "CORRUPT_TARGET": "refused",
}


def _unregistered_target(repo_root: Path, world_id: str, target: str) -> str | None:
    """``None`` when ``target`` is a committed target of ``world_id``.

    Otherwise the reason, for a refusal that names the registered set rather
    than the file. A manifest that cannot be read is treated as no registered
    set at all: the route then refuses everything, which is the safe end of
    the failure — the unsafe end certifies bounded negatives about files
    nobody committed as targets.
    """

    manifest = repo_root / CLOSURE_TARGET_MANIFEST
    try:
        entries = json.loads(manifest.read_text(encoding="utf-8"))["files"]
        listed = [
            entry for entry in entries
            if entry["path"] == target.replace("\\", "/")
        ]
    except (OSError, TypeError, ValueError, KeyError) as exc:
        return (
            f"no readable target set at {CLOSURE_TARGET_MANIFEST} "
            f"({type(exc).__name__}); with none committed there is no "
            f"registered target to answer about"
        )
    if not listed:
        return (
            f"{target!r} is not listed in {CLOSURE_TARGET_MANIFEST}; "
            f"{REACHABLE_COMMAND!r} answers about the committed target set, "
            f"not about arbitrary repository files"
        )
    if not any(entry.get("world_id") == world_id for entry in listed):
        owners = sorted({str(entry.get("world_id")) for entry in listed})
        return (
            f"{target!r} is a committed target of {', '.join(owners)}, not "
            f"of {world_id}"
        )
    return None


def _route_reachable(repo_root: Path, session: "CoreSession", rest: str) -> dict:
    """`reachable <world-id> <target-path>` — one sealed closure, one target.

    The target is a *file* and not a phrase because
    ``closure_query.query`` refuses approximate targets by design: it takes
    the target's exact canonical bytes. The committed set under
    ``data/closure_targets/`` is what a typed line can name
    (``scripts/seed_closure_targets.py``), and only that set: see
    :data:`CLOSURE_TARGET_MANIFEST`.

    Every refusal below is the query layer's own — its exception class name
    travels in the detail — except the three this route owns: a malformed
    line, a target outside the registered set, and a listed target whose file
    is not there. None reaches the write gate: a line with whitespace in it is
    not a path shape, and this branch has already claimed it.
    """

    # Gated before the import, not after: with no closure set registered
    # there is nothing for the query stack to be loaded for.
    if CLOSURE_SUBSYSTEM not in session.matrix.registered_ids():
        return {
            "route": "closure",
            "status": "exhausted",
            "detail": (
                f"{CLOSURE_SUBSYSTEM} did not register on this boot; the "
                "reachability answer is read out of a sealed closure and has "
                "nowhere else to read one from"
            ),
            "missing_capability": CLOSURE_SUBSYSTEM,
        }

    from closure_check import load_closure  # noqa: PLC0415
    from closure_query import (  # noqa: PLC0415
        QueryRefused,
        display_lines,
        find_registration,
        query,
    )

    parts = rest.split()
    if len(parts) != 2:
        return {
            "route": "closure",
            "status": "refused",
            "detail": (
                f"{REACHABLE_COMMAND!r} takes exactly a world id and a "
                f"repository-relative target path; got {len(parts)} argument(s)"
            ),
        }
    world_id, target = parts
    try:
        registration = find_registration(world_id)
    except QueryRefused as exc:
        return {
            "route": "closure",
            "status": "refused",
            "detail": f"{type(exc).__name__}: {exc}",
        }
    closure_path = Path("reports") / "closures" / f"{world_id}.closure.json"
    if not (repo_root / closure_path).is_file():
        return {
            "route": "closure",
            "status": "refused",
            "detail": (
                f"{world_id} is registered but no sealed closure exists at "
                f"{closure_path.as_posix()}"
            ),
        }
    unregistered = _unregistered_target(repo_root, world_id, target)
    if unregistered is not None:
        return {"route": "closure", "status": "refused", "detail": unregistered}
    if not _existing_file(repo_root, target):
        return {
            "route": "closure",
            "status": "refused",
            "detail": (
                f"no target file at {target!r}; a query takes the target's "
                "exact canonical bytes, so there is nothing here to compare"
            ),
        }

    try:
        # `load_closure` reads and parses a committed file, so a truncated or
        # unreadable closure must refuse here rather than raise out of
        # `route_line` and end the session.
        closure = load_closure(repo_root / closure_path)
        target_bytes = (repo_root / target).read_bytes()
        receipt = query(closure, registration, target_bytes, repo_root)
    except QueryRefused as exc:
        return {
            "route": "closure",
            "status": "refused",
            "detail": f"{type(exc).__name__}: {exc}",
        }
    except (OSError, ValueError) as exc:
        return {
            "route": "closure",
            "status": "refused",
            "detail": f"{type(exc).__name__}: {exc}",
        }

    if receipt["outcome"] == "REACHABLE":
        detail = (
            f"{world_id}: reachable in {len(receipt['shortest_route'])} "
            f"action(s), replayed through the world's own verifier"
        )
    elif receipt["outcome"] == "NOT_REACHABLE_WITHIN_HORIZON":
        detail = (
            f"{world_id}: not reachable within horizon {receipt['horizon']} "
            f"of a closure that visited {receipt['visited_states']} states"
        )
    else:
        detail = (
            f"{world_id}: a state record carries this digest but different "
            "canonical bytes"
        )
    return {
        "route": "closure",
        "status": CLOSURE_OUTCOME_STATUS[receipt["outcome"]],
        "detail": detail,
        # The committed §7 display, not a second rendering of the same
        # receipt: the bound travels with the answer wherever it is shown.
        "answer": tuple(display_lines(receipt, closure, closure_path)),
        "receipt": receipt,
    }


#: Wiring step for DESIGN-statements-that-run §5. The route lands NOW, with
#: ROADMAP-v0.20 §4's batched retirement, so item 1's slice never has to
#: retouch `harness.py` and open a second retirement for one new branch. Its
#: own design states the dependency: the route, the exact-numeral path and the
#: resource bound "all ride §4's retirement rather than opening one".
CONFORM_COMMAND = "conform"

#: The capability `conform` needs and does not have. `scripts/conform.py` —
#: the compiler that turns a statement node into a conformance program — is
#: item 1's deliverable and does not exist yet, so the route refuses BY NAME
#: rather than pretending the line was never registered.
CONFORM_SUBSYSTEM = "tool.conform"


def _route_conform(repo_root: Path, session: "CoreSession", rest: str) -> dict:
    """`conform <statement-id> <bindings>` — registered, and refusing for now.

    A stub, and deliberately a *refusing* one rather than an absent one. The
    distinction is the whole reason it lands early: a line this repository
    intends to answer should say "that capability is not built yet" instead
    of falling through to the dispatcher's "the corpus does not ground this",
    which is a different and false statement about the same line.

    Shaped on `_route_twin` rather than on `_route_evaluate`, because the two
    routes answer different questions about a line. `_route_evaluate` returns
    `None` when it cannot READ the text, so an expression it does not
    recognise falls through to the rest of the chain rather than refusing on
    everyone else's behalf. `conform` is head-guarded: a line starting with
    the command word is unambiguously addressed to this route, so nothing
    else could claim it and falling through would only lose the reason.

    What it will do when `scripts/conform.py` lands is NOT sketched here.
    The design is explicit that a conformance verdict is about the asker's
    numbers and is worth exactly what its sampled points are worth, and a
    stub that guessed at the record shape would be the first place that
    caution got lost.
    """

    if CONFORM_SUBSYSTEM in session.matrix.registered_ids():  # pragma: no cover
        # Reachable only once item 1 registers the subsystem; the compiler
        # is its deliverable, not this stub's.
        raise NotImplementedError(
            "conform: the subsystem registered but no compiler is wired"
        )
    if not rest.strip():
        return {
            "route": "conform",
            "status": "refused",
            "detail": (
                f"{CONFORM_COMMAND!r} needs a statement id, and then the "
                f"bindings to test it at"
            ),
        }
    return {
        "route": "conform",
        "status": "refused",
        "detail": (
            f"{CONFORM_SUBSYSTEM} is not built on this tree; conformance "
            f"compiles a statement to an evaluator and there is nothing here "
            f"to compile it with. The line is registered and the capability "
            f"is not, which is a different thing from the corpus not "
            f"grounding it"
        ),
        "missing_capability": CONFORM_SUBSYSTEM,
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
    head = line.partition(" ")[0].casefold()
    if session.pending_candidates and head in {NARROW_COMMAND, CANCEL_COMMAND}:
        return {"line": line, **_route_pending_context(session, line)}
    head, _, rest = line.partition(" ")
    if head.lower() == OWNS_COMMAND:
        return {"line": line, **_route_ownership(repo_root, session, rest.strip())}
    if head.lower() == SUPPOSE_COMMAND:
        # A supposition that binds a variable and then asks about it is a
        # computation under a frame, not a claim to hold. `suppose x=5, what
        # is x^2` should answer 25, because the frame supplies the binding
        # and arithmetic is exact.
        computed = _route_evaluate(rest.strip())
        if computed is not None:
            return {"line": line, **computed}
        return {"line": line, **_route_suppose(rest.strip())}
    if head.lower() == TWIN_COMMAND:
        return {"line": line, **_route_twin(session, rest.strip())}
    if head.lower() == REACHABLE_COMMAND:
        return {"line": line, **_route_reachable(repo_root, session, rest)}
    if head.lower() == CONFORM_COMMAND:
        return {"line": line, **_route_conform(repo_root, session, rest)}
    told = _route_story(session, line)
    if told is not None:
        return {"line": line, **told}
    believed = _route_belief(session, line)
    if believed is not None:
        return {"line": line, **believed}
    computed = _route_evaluate(line)
    if computed is not None:
        return {"line": line, **computed}
    if _existing_file(repo_root, line) or _looks_like_path(line):
        return {"line": line, **_route_write(repo_root, line)}
    resolved = _route_resolver(repo_root, session, line)
    if resolved is not None:
        return {"line": line, **resolved}
    defined = _route_gloss(session, line)
    if defined is not None:
        return {"line": line, **defined}
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
    if verdict.get("reading"):
        out.append("reading :")
        for item in verdict["reading"]:
            out.append(f"  {item}")
    for item in verdict.get("answer", ()):
        out.append(f"  {item}")
    return out


def main() -> int:
    """Print the boot matrix, then dispatch typed lines until input ends."""

    repo_root = Path(__file__).resolve().parent.parent
    # Detect what is actually installed rather than forcing the absent case.
    # `offline=True` exists to reproduce a WordNet/Lean/Torch-less box on one
    # that has them, which is what P-IH1 boots under — a TEST invariant that
    # had leaked into the CLI, so the prompt reported three subsystems OFF on
    # a machine where they were present. The probes are the honest answer;
    # anything genuinely missing still reports OFF, and `--offline` restores
    # the forced-absent boot for anyone reproducing that case.
    import sys  # noqa: PLC0415

    offline = "--offline" in sys.argv[1:]
    session = CoreSession.boot(repo_root, offline=offline)
    mode = "offline" if offline else "detected"
    print(f"corollary kernel ({mode}) session {session.session_id[:12]}...")
    for line in session.matrix.render():
        print(line)

    # EOF after at least one turn ends quietly.  EOF before the first turn is
    # still rendered as WAITING so a closed input channel is visible.  A
    # resolver ASK survives between iterations in ``CoreSession``.
    turns = 0
    while True:
        typed = read_one_line()
        if typed is None and turns:
            break
        verdict = route_line(repo_root, session, typed)
        for row in render_verdict(verdict):
            print(row)
        turns += 1
        if typed is None or verdict["status"] in {"cycle", "hop_ceiling"}:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
