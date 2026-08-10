#!/usr/bin/env python3
"""Phase-2 need dispatcher for the interactive harness (v0.8 item 1, slice 2).

This is the SECOND slice of v0.8 item 1 (``docs/ROADMAP-v0.8.md``) and the
Phase-2 deliverable of ``docs/DESIGN-interactive-harness.md`` §9. Phase 1
(``scripts/harness.py``) booted the capability matrix, ran one conversation
through the propose -> verify -> trace controller, and surfaced a pause as
``StopReason.WAITING``. It deliberately shipped *no* need dispatcher, no session
budget, and no cross-hop loop detection; ``RetrievalVerifier._pruning`` was left
as the untouched substrate a later slice would thread. This module is that
slice, and nothing else: it walks registered subsystem paths, bounds the hops
per need, and refuses a session-level cycle instead of spinning.

Three design rules from the design doc are load-bearing here and are NOT
re-decided:

* **One ladder, not two (§6.2).** A need is progressed by walking
  ``retrieval.run_miss_chain`` — exact -> neighborhood -> derivation -> tool ->
  ASK — the same ROADMAP-v0.7 item-6 chain the retrieve leg already uses. The
  dispatcher routes *between* registered subsystems; within a subsystem it does
  not invent a parallel rung vocabulary.
* **Registered paths only (§3.2, P-IH4).** A need routed to a path the boot
  matrix did not register is abstained with the missing capability named — never
  free-generated, never improvised. That is the anti-"command not found" rule.
* **Termination is not free (§3.1/§6.2, P-IH7).** The kernel's rejected sets,
  ``seen_states`` and budgets are run-local, so each ``run_miss_chain`` hop
  starts them empty. Two subsystems that re-open each other's need would cycle
  across hops forever. Two mechanisms are in play, with a clear division of
  labour (an adversarial review of this slice pinned it down, correcting an
  earlier framing that called both load-bearing for the same job):

    1. the verifier's session-scoped ``_pruning`` (``retrieval.PruningEvidence``)
       spans hops because this dispatcher reuses **one** verifier for every
       ``run_miss_chain`` call — a re-walk of one subsystem's own dead need
       costs zero store queries. This makes the walking CHEAP (and bounds the
       cost of the ``loop_detection=False`` interim path); it does not, by
       itself, NAME a cross-subsystem cycle.
    2. the dispatcher's own ``(need, state_key)`` visited-dead record is what
       actually catches and names the *cross-subsystem* A -> B -> A cycle,
       whose two legs have different verifier state keys and so are invisible to
       (1) alone. The refusal is cited from THIS record, not from the pruning
       count. This is exactly the third of §627's "three things still owed" —
       the two-subsystem case the landed retrieval substrate could not see by
       itself.

  The ``(need, state_key)`` key is frame-spec-qualified on both halves
  (``repr(state.frame.spec)`` inside the need identity, and again inside
  ``RetrievalVerifier.state_key``). That is the P-RT6 fix carried up to the
  dispatcher: a name-only key let one frame's dead end refuse another frame's
  live branch, and this dispatcher must not reintroduce that collision.

Out of Phase-2-but-not-this-slice scope, deferred and stated so: the bounded
slot-filling grammar, optional tool plugins (Phase 3), the Chat-Completions HTTP
skin (Phase 4), and the collapse/expand TTY chrome beyond a status line. The
``loop_detection`` switch below exists so a caller can observe the §6.2 interim
guarantee directly: with detection off, the dispatcher still terminates, but
only at the hop ceiling with BUDGET caution chrome rather than by naming the
cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Mapping

from controller import RunResult, StopReason
from retrieval import RetrievalState, RetrievalVerifier, run_miss_chain


#: §6.2's proposed interim hop ceiling. A session cannot dispatch a single need
#: more than this many times; the bound is what makes "never spins" true even
#: before loop detection has a chance to name a cycle.
DEFAULT_HOP_BUDGET = 8

#: The identity of a need as the dispatcher records it: the pending slot, its
#: suggested key, and the FULL frame spec (not the frame name). Frame-spec
#: qualification is the P-RT6 fix lifted to the dispatcher — two same-named
#: frames with different owners are different needs and must not share a
#: visited-dead entry.
NeedKey = tuple[str, str, str]


def need_identity(state: RetrievalState) -> NeedKey:
    """The dispatcher-level identity of one pending need.

    Requires a pending UNKNOWN; a state with nothing pending is not a need the
    dispatcher can route. ``repr(state.frame.spec)`` is deliberately the whole
    spec — name, owner, declarations, suspends, governance — so a name-only
    collision (P-RT6) cannot form here.
    """

    need = state.pending
    if need is None:
        raise ValueError("a dispatchable need must carry a pending UNKNOWN")
    return (need.slot, need.suggested_key, repr(state.frame.spec))


class DispatchOutcome(str, Enum):
    """What one dispatcher hop did with the need it was handed."""

    MATERIALIZED = "materialized"  # a miss-chain rung admitted pointable material
    WAITING = "waiting"            # the chain reached ASK; an input channel is owed
    DEAD = "dead"                  # the chain abstained; recorded as visited-dead
    CYCLE = "cycle"                # a visited-dead (need, state_key) was re-reached
    UNREGISTERED = "unregistered"  # routed to a path the matrix did not register


@dataclass(frozen=True)
class RegisteredPath:
    """One registered subsystem path the dispatcher may route a need to.

    ``registered`` mirrors the boot matrix: a path whose subsystem probed OFF or
    FAIL is present in the registry but unregistered, and routing to it abstains
    (P-IH4). ``build_state`` renders this path's need as a ``RetrievalState``
    threaded on the session id, so ``run_miss_chain`` can walk it. ``reopens``
    names the subsystem this path routes to when its own chain abstains — the
    edge that, closed into a loop, is the cross-subsystem cycle P-IH7 refuses.
    ``None`` means "this path is a leaf": a dead end here is an honest
    abstention with no further candidate.
    """

    subsystem_id: str
    registered: bool
    build_state: Callable[[str], RetrievalState]
    reopens: str | None = None


@dataclass(frozen=True)
class DispatchEvent:
    """One structured hop record. TTY/HTTP chrome is a renderer over these."""

    hop: int
    subsystem_id: str
    need_key: NeedKey | None
    state_key: str
    outcome: DispatchOutcome
    detail: str
    #: ``len(verifier.session_pruning_evidence(session_id))`` observed after this
    #: hop. It is monotone non-decreasing across a session precisely because the
    #: verifier's ``_pruning`` is NOT reset per hop; a test can read this column
    #: to prove the evidence genuinely spans hops.
    pruning_count: int
    run: RunResult | None = None


@dataclass(frozen=True)
class DispatchResult:
    """The terminal disposition of one dispatched need.

    ``stop_reason`` reuses the kernel vocabulary: SOLVED (a rung answered),
    WAITING (input owed), EXHAUSTED (honest abstention — including a named
    cycle), or BUDGET (the hop ceiling fired). ``cycle`` is populated only for a
    loop-detection stop and carries the exact ``(need, state_key)`` pair whose
    second visit was pruned, so the cycle is *named in the trace* rather than
    merely implied by a step cap (the P-IH7 miss condition).
    """

    stop_reason: StopReason
    events: tuple[DispatchEvent, ...]
    cycle: tuple[NeedKey, str] | None
    reason: str
    final_run: RunResult | None

    @property
    def materialized(self) -> bool:
        return self.stop_reason is StopReason.SOLVED


class NeedDispatcher:
    """Walk registered subsystem paths for one need, bounded and loop-safe.

    Holds ONE verifier for the whole dispatch so ``run_miss_chain``'s pruning
    evidence accumulates on it across hops instead of being rebuilt empty at
    each — the concrete meaning of "session-scoped" here. The registry is the
    set of registered (and deliberately-unregistered) paths; the hop budget is
    the §6.2 ceiling.
    """

    def __init__(
        self,
        verifier: RetrievalVerifier,
        registry: Mapping[str, RegisteredPath],
        *,
        hop_budget: int = DEFAULT_HOP_BUDGET,
        loop_detection: bool = True,
    ) -> None:
        if hop_budget < 1:
            raise ValueError("hop_budget must be positive")
        self.verifier = verifier
        self.registry = dict(registry)
        self.hop_budget = hop_budget
        self.loop_detection = loop_detection

    @classmethod
    def for_session(
        cls,
        session,
        registry: Mapping[str, RegisteredPath],
        *,
        hop_budget: int = DEFAULT_HOP_BUDGET,
        loop_detection: bool = True,
    ) -> "NeedDispatcher":
        """Bind a dispatcher to a booted :class:`harness.CoreSession`.

        Reuses the session's own verifier — a second verifier would be a second
        authority and a second pruning store, which is exactly what this slice
        must not create.

        Reconciles each path's ``registered`` flag against the boot matrix, so a
        hand-built registry cannot claim a matrix-OFF/FAIL subsystem is
        registered and get it walked. This makes P-IH4 hold **by construction**
        for every subsystem the matrix knows about, not merely by the caller's
        good faith (a review of this slice found the raw flag was gated by
        convention alone). A subsystem absent from the matrix — a synthetic or
        not-yet-booted path — keeps its declared flag; the matrix is the
        authority only over what it actually probed.
        """

        reconciled: dict[str, RegisteredPath] = {}
        for key, path in registry.items():
            try:
                matrix_registered = session.matrix.get(path.subsystem_id).registered
            except KeyError:
                reconciled[key] = path
                continue
            reconciled[key] = replace(path, registered=matrix_registered)
        return cls(
            session.verifier,
            reconciled,
            hop_budget=hop_budget,
            loop_detection=loop_detection,
        )

    def dispatch(
        self, session_id: str, initial_subsystem_id: str
    ) -> DispatchResult:
        """Route ``initial_subsystem_id``'s need until it terminates.

        Terminal stops, in the order they are tested each hop:

        * **UNREGISTERED -> EXHAUSTED** (P-IH4): the route names a path the
          matrix did not register; abstain with the capability named.
        * **CYCLE -> EXHAUSTED** (P-IH7): the ``(need, state_key)`` pair was
          already resolved dead this session; refuse it from stored pruning
          evidence rather than re-expanding it.
        * **MATERIALIZED -> SOLVED**: a miss-chain rung admitted material.
        * **WAITING**: the chain reached ASK; an input channel is owed.
        * **DEAD -> EXHAUSTED** (leaf) or route to ``reopens``.
        * **BUDGET**: the hop ceiling fired first — the interim §6.2 guarantee.
        """

        events: list[DispatchEvent] = []
        visited_dead: dict[tuple[NeedKey, str], DispatchEvent] = {}
        route = initial_subsystem_id

        for hop in range(self.hop_budget):
            path = self.registry.get(route)
            if path is None or not path.registered:
                detail = (
                    f"routed to {route!r}, which the boot matrix did not "
                    "register; abstaining rather than inventing a path "
                    "(P-IH4: registered paths only)"
                )
                events.append(
                    DispatchEvent(
                        hop,
                        route,
                        None,
                        "",
                        DispatchOutcome.UNREGISTERED,
                        detail,
                        len(self.verifier.session_pruning_evidence(session_id)),
                    )
                )
                return DispatchResult(
                    StopReason.EXHAUSTED, tuple(events), None, detail, None
                )

            state = replace(path.build_state(session_id), session_id=session_id)
            if state.pending is None:
                # A registered path that produced no routable need (no pending
                # UNKNOWN) is an honest dead end, not a crash. ``need_identity``
                # would raise here; abstain like any other leaf abstention
                # instead, so one misbehaving or already-resolved path cannot
                # take the whole dispatch down mid-session.
                detail = (
                    f"{path.subsystem_id!r} produced no routable need (no "
                    "pending UNKNOWN); abstaining rather than crashing"
                )
                events.append(
                    DispatchEvent(
                        hop,
                        path.subsystem_id,
                        None,
                        "",
                        DispatchOutcome.DEAD,
                        detail,
                        len(self.verifier.session_pruning_evidence(session_id)),
                    )
                )
                if path.reopens is None:
                    return DispatchResult(
                        StopReason.EXHAUSTED, tuple(events), None, detail, None
                    )
                route = path.reopens
                continue

            need_key = need_identity(state)
            state_key = self.verifier.state_key(state)
            pair = (need_key, state_key)

            if self.loop_detection and pair in visited_dead:
                prior = visited_dead[pair]
                pruning = self.verifier.session_pruning_evidence(session_id)
                detail = (
                    f"need {need_key!r} was already resolved dead at hop "
                    f"{prior.hop} by {prior.subsystem_id!r}; the dispatch cycle "
                    f"{prior.subsystem_id!r} -> {path.subsystem_id!r} is caught "
                    "by the dispatcher's visited-dead record and refused "
                    f"without re-expansion. ({len(pruning)} session pruning "
                    "record(s) made the prior walks cheap, but the cycle is "
                    "named by the visited-dead record, not by them.) "
                    "(P-IH7: session-level loop detection)"
                )
                events.append(
                    DispatchEvent(
                        hop,
                        path.subsystem_id,
                        need_key,
                        state_key,
                        DispatchOutcome.CYCLE,
                        detail,
                        len(pruning),
                    )
                )
                return DispatchResult(
                    StopReason.EXHAUSTED, tuple(events), pair, detail, None
                )

            run = run_miss_chain(self.verifier, state)
            pruning_count = len(
                self.verifier.session_pruning_evidence(session_id)
            )

            if run.final_state.context:
                detail = (
                    f"{path.subsystem_id!r} materialized "
                    f"{len(run.final_state.context)} pointable item(s)"
                )
                events.append(
                    DispatchEvent(
                        hop,
                        path.subsystem_id,
                        need_key,
                        state_key,
                        DispatchOutcome.MATERIALIZED,
                        detail,
                        pruning_count,
                        run,
                    )
                )
                return DispatchResult(
                    StopReason.SOLVED, tuple(events), None, detail, run
                )

            if run.final_state.awaiting is not None:
                detail = (
                    f"{path.subsystem_id!r} needs input: "
                    f"{run.final_state.awaiting.prompt}"
                )
                events.append(
                    DispatchEvent(
                        hop,
                        path.subsystem_id,
                        need_key,
                        state_key,
                        DispatchOutcome.WAITING,
                        detail,
                        pruning_count,
                        run,
                    )
                )
                return DispatchResult(
                    StopReason.WAITING, tuple(events), None, detail, run
                )

            dead = DispatchEvent(
                hop,
                path.subsystem_id,
                need_key,
                state_key,
                DispatchOutcome.DEAD,
                f"{path.subsystem_id!r} abstained; miss chain exhausted every "
                "registered rung with no pointable material",
                pruning_count,
                run,
            )
            events.append(dead)
            visited_dead[pair] = dead

            if path.reopens is None:
                detail = (
                    "every registered path abstained and none re-opens the "
                    "need; honest abstention"
                )
                return DispatchResult(
                    StopReason.EXHAUSTED, tuple(events), None, detail, None
                )
            route = path.reopens

        detail = (
            f"session hop budget of {self.hop_budget} reached without a "
            "terminal answer; stopping with BUDGET caution chrome (the §6.2 "
            "interim ceiling)"
        )
        return DispatchResult(StopReason.BUDGET, tuple(events), None, detail, None)
