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

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, Protocol, TypeVar


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
            commit_run = getattr(verifier, "commit_run", None)
            if callable(commit_run):
                commit_run(deepcopy(trace))
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
