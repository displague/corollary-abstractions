#!/usr/bin/env python3
"""Domain-neutral propose -> verify -> repeat controller.

The controller deliberately knows no Lean, narrative, retrieval, or rendering
semantics. A policy proposes one of the five public action kinds; a verifier
adapter either returns an accepted next state or a rejected branch. Rejected
branches are recorded and can never mutate the accepted state.

This is the oracle-first control plane specified by docs/ROADMAP-v0.5.md.
Learned policies may replace ``SequencePolicy`` later without changing the
state/action/verifier contract proved here.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, Iterable, Protocol, TypeVar, runtime_checkable


StateT = TypeVar("StateT")


class ActionKind(str, Enum):
    """The complete public action vocabulary of the v0.5 controller."""

    POINT = "POINT"
    GEN = "GEN"
    RETRIEVE = "RETRIEVE"
    ASK = "ASK"
    WRITE = "WRITE"


class Verdict(str, Enum):
    """Symbolic outcomes; only PROVEN and VERIFIED advance state."""

    PROVEN = "PROVEN"
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    UNKNOWN = "UNKNOWN"
    REFUSED = "REFUSED"

    @property
    def accepts(self) -> bool:
        return self in {Verdict.PROVEN, Verdict.VERIFIED}


class StopReason(str, Enum):
    SOLVED = "solved"
    WAITING = "waiting"
    EXHAUSTED = "exhausted"
    BUDGET = "budget"


@dataclass(frozen=True)
class Action:
    """One typed controller action with stable, auditable arguments."""

    kind: ActionKind
    name: str
    arguments: tuple[tuple[str, str], ...] = ()
    dependencies: tuple[str, ...] = ()

    @classmethod
    def build(
        cls,
        kind: ActionKind,
        name: str,
        arguments: dict[str, str] | None = None,
        dependencies: tuple[str, ...] = (),
    ) -> "Action":
        return cls(
            kind=kind,
            name=name,
            arguments=tuple(sorted((arguments or {}).items())),
            dependencies=dependencies,
        )

    def argument(self, key: str) -> str | None:
        return dict(self.arguments).get(key)

    @property
    def fingerprint(self) -> tuple[object, ...]:
        return (self.kind.value, self.name, self.arguments, self.dependencies)


@dataclass(frozen=True)
class Verification(Generic[StateT]):
    """A verifier's exact disposition of one proposed action."""

    verdict: Verdict
    reason: str
    next_state: StateT | None = None
    evidence: tuple[str, ...] = ()

    def validate(self) -> None:
        if self.verdict.accepts and self.next_state is None:
            raise ValueError(f"{self.verdict.value} must supply next_state")
        if not self.verdict.accepts and self.next_state is not None:
            raise ValueError(
                f"{self.verdict.value} may not mutate accepted state"
            )


@dataclass(frozen=True)
class TraceEntry(Generic[StateT]):
    index: int
    state_before: StateT
    action: Action
    verification: Verification[StateT]
    state_after: StateT

    @property
    def accepted(self) -> bool:
        return self.verification.verdict.accepts


class Policy(Protocol[StateT]):
    def propose(
        self, state: StateT, trace: tuple[TraceEntry[StateT], ...]
    ) -> Action | None: ...


class VerifierAdapter(Protocol[StateT]):
    name: str

    def state_key(self, state: StateT) -> str: ...

    def evaluate(self, state: StateT, action: Action) -> Verification[StateT]: ...


@runtime_checkable
class RunCommitter(Protocol[StateT]):
    """Optional verifier capability: commit verifier-private effects once.

    ROADMAP-v0.7 item 6 / BACKLOG "commit_run duck-typed": the controller used
    to reach for this hook with ``getattr(verifier, "commit_run", None)``, so
    the *name* had no owner and a typo in an adapter was a silent no-op. The
    protocol owns the name now. It stays **optional** — a verifier with no
    private ledgers implements nothing and the controller is unchanged — which
    is why it is a separate ``runtime_checkable`` protocol rather than a
    method added to :class:`VerifierAdapter`.

    Contract:

    * called at most once per :meth:`Controller.run`, with the returned run's
      own (already copy-isolated) trace;
    * called only when a :class:`RunResult` is actually being returned, so a
      speculative ``evaluate`` outside a run commits nothing;
    * **must not raise.** The same backlog note observed that an exception
      here loses a fully-callbacked ``RunResult``. That is still true and is
      deliberate: an implementation whose authority commit failed must not
      have its failure swallowed while the caller receives a run that claims
      the commit happened. Losing the result is the honest outcome; the fix
      belongs in the committer, which is why the protocol states the duty.

    One behaviour change from the ``getattr`` version is deliberate and is
    recorded here rather than repaired. The old code paired the lookup with
    ``callable(...)``; ``isinstance`` against a ``runtime_checkable``
    ``Protocol`` checks that the attribute *exists*, not that it is callable,
    so a verifier declaring ``commit_run`` as a non-callable now raises
    ``TypeError`` at commit time instead of being skipped. That is the point.
    Skipping is precisely the silent no-op this protocol was introduced to
    abolish, and a verifier that owns the name without implementing it is
    malformed in the same way as one whose commit raises: the loud failure
    names the offender, and a swallowed one hands back a run claiming a commit
    that never ran. A ``callable`` guard would have restored the silence under
    a different spelling.
    """

    def commit_run(self, trace: tuple["TraceEntry[StateT]", ...]) -> None: ...


class BranchPolicy(Protocol[StateT]):
    """Enumerate candidate actions for one state, in policy order."""

    def propose_all(
        self, state: StateT, trace: tuple["SearchTraceEntry[StateT]", ...]
    ) -> Iterable[Action]: ...


class Goal(Protocol[StateT]):
    def __call__(self, state: StateT) -> bool: ...


@dataclass(frozen=True)
class RunResult(Generic[StateT]):
    initial_state: StateT
    final_state: StateT
    trace: tuple[TraceEntry[StateT], ...]
    stop_reason: StopReason

    @property
    def solved(self) -> bool:
        return self.stop_reason is StopReason.SOLVED

    @property
    def accepted_steps(self) -> int:
        return sum(entry.accepted for entry in self.trace)

    @property
    def rejected_steps(self) -> int:
        return len(self.trace) - self.accepted_steps


@dataclass(frozen=True)
class SearchTraceEntry(Generic[StateT]):
    """One proposal in a branching search, linked to its parent transition."""

    index: int
    parent: int | None
    depth: int
    state_before: StateT
    action: Action
    verification: Verification[StateT]
    state_after: StateT
    queued: bool

    @property
    def accepted(self) -> bool:
        return self.verification.verdict.accepts


@dataclass(frozen=True)
class SearchResult(Generic[StateT]):
    """Auditable outcome of bounded breadth-first branch search."""

    initial_state: StateT
    final_state: StateT | None
    trace: tuple[SearchTraceEntry[StateT], ...]
    solution_tail: int | None
    stop_reason: StopReason
    nodes_expanded: int
    states_seen: int

    @property
    def solved(self) -> bool:
        return self.stop_reason is StopReason.SOLVED

    @property
    def proposals(self) -> int:
        return len(self.trace)

    @property
    def accepted_proposals(self) -> int:
        return sum(entry.accepted for entry in self.trace)

    @property
    def rejected_proposals(self) -> int:
        return self.proposals - self.accepted_proposals

    @property
    def solution_trace(self) -> tuple[SearchTraceEntry[StateT], ...]:
        if self.solution_tail is None:
            return ()
        path: list[SearchTraceEntry[StateT]] = []
        cursor: int | None = self.solution_tail
        while cursor is not None:
            entry = self.trace[cursor]
            path.append(entry)
            cursor = entry.parent
        path.reverse()
        return tuple(path)


@dataclass
class SequencePolicy(Generic[StateT]):
    """Deterministic oracle: emits a registered sequence, then stops."""

    actions: tuple[Action, ...]
    _cursor: int = field(default=0, init=False)

    def propose(
        self, state: StateT, trace: tuple[TraceEntry[StateT], ...]
    ) -> Action | None:
        del state, trace
        if self._cursor >= len(self.actions):
            return None
        action = self.actions[self._cursor]
        self._cursor += 1
        return action


class Controller(Generic[StateT]):
    """Execute a bounded policy against one symbolic verifier adapter.

    State is copy-isolated at every extension boundary. This costs more than
    sharing a mutable object, but it makes the controller's central invariant
    true for arbitrary adapters: a policy, goal, or rejected verifier branch
    cannot mutate the accepted state or previously recorded trace snapshots.
    The intended states are small symbolic records; a future large-state
    adapter should use persistent structures before weakening this boundary.
    """

    def __init__(self, max_steps: int = 32):
        if max_steps < 1:
            raise ValueError("max_steps must be positive")
        self.max_steps = max_steps

    def run(
        self,
        initial_state: StateT,
        policy: Policy[StateT],
        verifier: VerifierAdapter[StateT],
        is_complete: Goal[StateT],
        is_waiting: Goal[StateT] | None = None,
    ) -> RunResult[StateT]:
        initial_snapshot = deepcopy(initial_state)
        state = deepcopy(initial_state)
        entries: list[TraceEntry[StateT]] = []
        rejected: set[tuple[str, tuple[object, ...]]] = set()

        def finish(stop_reason: StopReason) -> RunResult[StateT]:
            """Commit verifier-private effects only with a returned run state."""
            trace = deepcopy(tuple(entries))
            result = RunResult(
                initial_snapshot,
                deepcopy(state),
                trace,
                stop_reason,
            )
            if isinstance(verifier, RunCommitter):
                verifier.commit_run(deepcopy(trace))
            return result

        if is_complete(deepcopy(state)):
            return finish(StopReason.SOLVED)

        for index in range(self.max_steps):
            action = policy.propose(deepcopy(state), deepcopy(tuple(entries)))
            if action is None:
                return finish(StopReason.EXHAUSTED)

            branch_key = (
                verifier.state_key(deepcopy(state)),
                action.fingerprint,
            )
            if branch_key in rejected:
                verification = Verification[StateT](
                    verdict=Verdict.REFUSED,
                    reason="duplicate rejected action pruned for this state",
                    evidence=(verifier.name,),
                )
            else:
                raw_verification = verifier.evaluate(deepcopy(state), action)
                raw_verification.validate()
                verification = deepcopy(raw_verification)

            next_state = (
                deepcopy(verification.next_state)
                if verification.verdict.accepts
                else deepcopy(state)
            )
            assert next_state is not None
            entries.append(
                TraceEntry(
                    index=index,
                    state_before=deepcopy(state),
                    action=action,
                    verification=verification,
                    state_after=deepcopy(next_state),
                )
            )

            if verification.verdict.accepts:
                state = next_state
                if is_complete(deepcopy(state)):
                    return finish(StopReason.SOLVED)
                if is_waiting is not None and is_waiting(deepcopy(state)):
                    return finish(StopReason.WAITING)
            else:
                rejected.add(branch_key)

        return finish(StopReason.BUDGET)


class SearchController(Generic[StateT]):
    """Bounded breadth-first propose -> verify -> branch search.

    This is the branching counterpart of :class:`Controller`, not Lean search
    hidden in a prover adapter.  Verifiers still own domain truth, policies
    still own candidate order, and only VERIFIED/PROVEN transitions enter the
    frontier.  Rejections and accepted-but-cyclic transitions remain in the
    trace but cannot mutate another branch.

    ``max_nodes`` counts states whose action set is expanded.  The independent
    ``max_proposals`` ceiling prevents one policy call from hiding an unbounded
    action bag inside a small node budget.
    """

    def __init__(self, max_nodes: int = 64, max_proposals: int = 1024):
        if max_nodes < 1:
            raise ValueError("max_nodes must be positive")
        if max_proposals < 1:
            raise ValueError("max_proposals must be positive")
        self.max_nodes = max_nodes
        self.max_proposals = max_proposals

    def run(
        self,
        initial_state: StateT,
        policy: BranchPolicy[StateT],
        verifier: VerifierAdapter[StateT],
        is_complete: Goal[StateT],
    ) -> SearchResult[StateT]:
        initial_snapshot = deepcopy(initial_state)
        root = deepcopy(initial_state)
        entries: list[SearchTraceEntry[StateT]] = []
        frontier: deque[tuple[StateT, int | None, int]] = deque(
            [(root, None, 0)]
        )
        seen_states = {verifier.state_key(deepcopy(root))}
        attempted: set[tuple[str, tuple[object, ...]]] = set()
        nodes_expanded = 0

        def finish(
            reason: StopReason,
            final_state: StateT | None = None,
            solution_tail: int | None = None,
        ) -> SearchResult[StateT]:
            return SearchResult(
                initial_state=initial_snapshot,
                final_state=deepcopy(final_state),
                trace=deepcopy(tuple(entries)),
                solution_tail=solution_tail,
                stop_reason=reason,
                nodes_expanded=nodes_expanded,
                states_seen=len(seen_states),
            )

        if is_complete(deepcopy(root)):
            return finish(StopReason.SOLVED, root)

        while frontier:
            if nodes_expanded >= self.max_nodes:
                return finish(StopReason.BUDGET)
            if len(entries) >= self.max_proposals:
                return finish(StopReason.BUDGET)
            state, parent, depth = frontier.popleft()
            nodes_expanded += 1
            actions = policy.propose_all(
                deepcopy(state), deepcopy(tuple(entries))
            )

            for action in actions:
                if len(entries) >= self.max_proposals:
                    return finish(StopReason.BUDGET)
                state_key = verifier.state_key(deepcopy(state))
                branch_key = (state_key, action.fingerprint)
                if branch_key in attempted:
                    verification = Verification[StateT](
                        Verdict.REFUSED,
                        "duplicate action pruned for this search state",
                        evidence=(verifier.name,),
                    )
                else:
                    attempted.add(branch_key)
                    raw = verifier.evaluate(deepcopy(state), action)
                    raw.validate()
                    verification = deepcopy(raw)

                next_state = (
                    deepcopy(verification.next_state)
                    if verification.verdict.accepts
                    else deepcopy(state)
                )
                assert next_state is not None
                child_key = verifier.state_key(deepcopy(next_state))
                queued = verification.verdict.accepts and child_key not in seen_states
                index = len(entries)
                entries.append(
                    SearchTraceEntry(
                        index=index,
                        parent=parent,
                        depth=depth + 1,
                        state_before=deepcopy(state),
                        action=action,
                        verification=verification,
                        state_after=deepcopy(next_state),
                        queued=queued,
                    )
                )

                if not verification.verdict.accepts:
                    if len(entries) >= self.max_proposals:
                        return finish(StopReason.BUDGET)
                    continue
                seen_states.add(child_key)
                if is_complete(deepcopy(next_state)):
                    return finish(StopReason.SOLVED, next_state, index)
                if queued:
                    frontier.append((next_state, index, depth + 1))

                if len(entries) >= self.max_proposals:
                    return finish(StopReason.BUDGET)

        return finish(StopReason.EXHAUSTED)
