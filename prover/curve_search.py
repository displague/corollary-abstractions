#!/usr/bin/env python3
"""Multi-theorem live proof search, ranking arms, and fixed-budget curves.

ROADMAP-v0.7 item 1.  v0.6 shipped ONE live theorem, ONE trace, and a learned
proposer that a state-blind frequency order beat by a single proposal.  This
module turns that single point into a curve:

* a versioned held-out theorem set (:mod:`theorem_set`) instead of one
  hardcoded proposition;
* four ranking arms over the SAME candidate generator
  (:mod:`tactic_grammar`), so the only thing that varies is schema order;
* solved-rate at fixed state / proposal / wall-time budgets;
* accepted dead branches preserved per run, so "did learned ranking avoid
  branches that died elsewhere?" is a measurement rather than an anecdote.

Lean stays the sole transition authority.  Nothing here decides whether a
tactic works: :class:`~live_search.LiveLeanVerifier` asks Pantograph, and a
refused tactic supplies no next state.  There is no replay path in this
module at all -- a run either talked to Lean or it did not happen.

**Why one run per (theorem, arm) yields the whole curve.**
:class:`~controller.SearchController` is deterministic breadth-first search
and every ranker here is a pure function of the rendered state, so a run under
a smaller budget is a strict prefix of the same run under a larger one.  A run
that solved after ``k`` expanded nodes and ``p`` proposals therefore solves at
budget ``(N, P)`` exactly when ``k <= N and p <= P``.  Running at the maximum
budget once and thresholding is the same experiment as running the ladder,
minus the Lean round trips -- and :func:`verify_budget_monotonicity` re-runs a
sample at a lower budget against the derived prediction rather than trusting
the argument.
"""

from __future__ import annotations

import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol

PROVER_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROVER_ROOT.parent
for _extra in (REPO_ROOT / "scripts", PROVER_ROOT):
    if str(_extra) not in sys.path:
        sys.path.insert(0, str(_extra))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    SearchController,
    SearchResult,
)
from live_search import (  # noqa: E402
    LiveLeanState,
    LiveLeanVerifier,
    PantographBackend,
)
from tactic_grammar import (  # noqa: E402
    ARBITRARY_ORDER,
    SCHEMAS,
    action_schema,
    candidates,
    extraction_schema,
    frequency_order,
    goal_shape,
    parse_state,
    syntax_order,
)
from theorem_set import Backend, Theorem, TheoremSet  # noqa: E402


#: What ``PantographBackend.render`` prints for a closed goal.  The completion
#: test compares against this exact string, exactly as v0.6's ``blind_search``
#: did; Lean, not this module, decides when it is reached.
SOLVED_GOAL_TEXT = "no goals"


class SchemaRanker(Protocol):
    """Rank the eight schemas for one rendered state.  The ONLY graded call.

    An implementation may read the state (syntax-aware, learned) or ignore it
    (arbitrary, frequency).  It may not choose tactic arguments, apply
    tactics, or see the witness.
    """

    name: str
    state_aware: bool

    def order(self, rendered: str) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class ArbitraryRanker:
    """Fixed declaration order, leading with the registered dead branch."""

    name: str = "arbitrary"
    state_aware: bool = False

    def order(self, rendered: str) -> tuple[str, ...]:
        del rendered
        return ARBITRARY_ORDER


@dataclass(frozen=True)
class FrequencyRanker:
    """One global order from training-corpus schema counts.  State-blind.

    This is v0.6's winner: the arm that beat the learned proposer 64 to 65.0
    on the single live theorem.  It is reconstructed here from the same 44
    training rows, so the baseline the new curve must clear is the one that
    actually won.
    """

    counts: tuple[tuple[str, int], ...]
    name: str = "frequency"
    state_aware: bool = False

    def order(self, rendered: str) -> tuple[str, ...]:
        del rendered
        return frequency_order(dict(self.counts))


@dataclass(frozen=True)
class SyntaxRanker:
    """Closed-form rules over the rendered goal.  Capability-blind: no weights."""

    name: str = "syntax"
    state_aware: bool = True

    def order(self, rendered: str) -> tuple[str, ...]:
        return syntax_order(parse_state(rendered))


@dataclass(frozen=True)
class RankedSchemaPolicy:
    """The one policy protocol both domains use: rank schemas, expand args.

    ``propose_all`` is deliberately thin.  It reads the state once, asks the
    ranker for a schema order, and concatenates the fixed per-schema candidate
    lists.  Every arm therefore proposes the SAME multiset of tactics for a
    state and differs only in the order -- which is what makes a proposal-count
    comparison a ranking comparison.
    """

    ranker: SchemaRanker

    def propose_all(
        self, state: LiveLeanState, trace
    ) -> Iterable[Action]:
        del trace
        goal = parse_state(state.goal_text)
        available = candidates(goal)
        order = self.ranker.order(state.goal_text)
        return tuple(
            Action.build(ActionKind.GEN, "lean_tactic", {"tactic": tactic})
            for schema in order
            for tactic in available.get(schema, ())
        )


@dataclass(frozen=True)
class DeadBranch:
    """One accepted transition that led nowhere within this run's budget."""

    signature: tuple[str, str]
    tactic: str
    goal_shape: str
    schema: str
    depth: int


@dataclass(frozen=True)
class RunRecord:
    theorem: str
    family: str
    arm: str
    solved: bool
    stop_reason: str
    nodes: int
    states: int
    proposals: int
    accepted: int
    rejected: int
    seconds: float
    solution: tuple[str, ...]
    dead_branches: tuple[DeadBranch, ...]
    accepted_signatures: tuple[tuple[str, str], ...]
    proposal_signatures: tuple[tuple[str, str], ...]

    def as_json(self) -> dict[str, object]:
        return {
            "theorem": self.theorem,
            "family": self.family,
            "arm": self.arm,
            "solved": self.solved,
            "stop": self.stop_reason,
            "nodes": self.nodes,
            "states": self.states,
            "proposals": self.proposals,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "seconds": round(self.seconds, 3),
            "solution": list(self.solution),
            "dead_branches": [
                {
                    "goal_shape": item.goal_shape,
                    "schema": item.schema,
                    "tactic": item.tactic,
                    "depth": item.depth,
                }
                for item in self.dead_branches
            ],
        }


def _signature(entry) -> tuple[str, str]:
    shape = goal_shape(parse_state(entry.state_before.goal_text))
    return (shape, action_schema(entry.action.argument("tactic")))


def dead_branches(result: SearchResult[LiveLeanState]) -> tuple[DeadBranch, ...]:
    """Accepted transitions that are NOT on the returned solution path.

    For an unsolved run every accepted transition qualifies: nothing this run
    accepted reached a proof inside its budget.  Both cases are preserved --
    the roadmap asks for the evidence, not for a flattering subset.
    """
    on_path = {entry.index for entry in result.solution_trace}
    found: list[DeadBranch] = []
    for entry in result.trace:
        if not entry.accepted or entry.index in on_path:
            continue
        tactic = entry.action.argument("tactic") or ""
        shape, schema = _signature(entry)
        found.append(
            DeadBranch((shape, schema), tactic, shape, schema, entry.depth)
        )
    return tuple(found)


def run_theorem(
    verifier: LiveLeanVerifier,
    theorem: Theorem,
    ranker: SchemaRanker,
    max_nodes: int,
    max_proposals: int,
) -> RunRecord:
    """One live search.  Lean is asked about every proposed transition."""
    policy = RankedSchemaPolicy(ranker)
    initial = verifier.start(theorem.id, theorem.proposition)
    started = time.perf_counter()
    result = SearchController[LiveLeanState](max_nodes, max_proposals).run(
        initial,
        policy,
        verifier,
        lambda state: state.goal_text == SOLVED_GOAL_TEXT,
    )
    elapsed = time.perf_counter() - started
    accepted = tuple(
        _signature(entry) for entry in result.trace if entry.accepted
    )
    proposed = tuple(_signature(entry) for entry in result.trace)
    return RunRecord(
        theorem=theorem.id,
        family=theorem.family,
        arm=ranker.name,
        solved=result.solved,
        stop_reason=result.stop_reason.value,
        nodes=result.nodes_expanded,
        states=result.states_seen,
        proposals=result.proposals,
        accepted=result.accepted_proposals,
        rejected=result.rejected_proposals,
        seconds=elapsed,
        solution=tuple(
            entry.action.argument("tactic") or ""
            for entry in result.solution_trace
        ),
        dead_branches=dead_branches(result),
        accepted_signatures=accepted,
        proposal_signatures=proposed,
    )


class BackendPool:
    """One Pantograph server per backend, reused across every theorem/arm.

    Restarting the Lean process per run would triple the wall clock and make
    the time axis mostly process startup.  Goal states are minted per
    ``verifier.start`` and the public controller state is an opaque handle, so
    sharing the server does not share state between runs.
    """

    def __init__(self) -> None:
        self._backends: dict[str, PantographBackend] = {}

    def get(self, backend: Backend) -> PantographBackend:
        if backend.name not in self._backends:
            if backend.lean_path is not None and not any(
                backend.lean_path.glob("*.olean")
            ):
                # Without this, Pantograph fails with a generic "Server failed
                # to emit ready signal" whose own text blames a Lean version
                # mismatch.  Checking for compiled oleans (not merely for the
                # directory) also catches a half-finished or cleaned build,
                # which is the case that would otherwise start a server that
                # cannot resolve the imports.
                raise RuntimeError(
                    f"backend {backend.name!r} needs a built Lake project: no "
                    f"*.olean under {backend.lean_path}. Run `lake build` in "
                    f"{backend.project} first (prover/README.md)."
                )
            self._backends[backend.name] = PantographBackend(
                backend.project,
                backend.imports,
                lean_path=(
                    str(backend.lean_path) if backend.lean_path else None
                ),
            )
        return self._backends[backend.name]

    def verifier(self, backend: Backend) -> LiveLeanVerifier:
        return LiveLeanVerifier(self.get(backend))

    def close(self) -> None:
        for backend in self._backends.values():
            backend.close()
        self._backends.clear()


def solved_at(record: RunRecord, nodes: int, proposals: int) -> bool:
    """Would this deterministic run have solved under a smaller budget?"""
    return record.solved and record.nodes <= nodes and record.proposals <= proposals


def solved_by_time(record: RunRecord, seconds: float) -> bool:
    return record.solved and record.seconds <= seconds


def state_leakage(
    pool: "BackendPool",
    theorem_set: TheoremSet,
    ranker: SchemaRanker,
    training_states: frozenset[str],
    max_nodes: int,
    max_proposals: int,
) -> dict[str, object]:
    """How much of what search actually SEES was in the training extraction?

    The theorem set's holdout is by theorem identity and by statement, both
    checked.  That is not the same as state-level novelty: two different
    theorems can pass through the same rendered proof state, and the v0.6
    checkpoint was trained on rendered ``stateBefore`` strings.  Claiming "the
    checkpoint cannot have seen these" without measuring the intermediate
    states would be exactly the kind of unfalsifiable assertion AGENTS.md rule
    5 says to flag.  So it is measured, live, and reported as a number.
    """
    seen: set[str] = set()
    per_theorem: list[dict[str, object]] = []
    for theorem in theorem_set.theorems:
        verifier = pool.verifier(theorem_set.backend_of(theorem))
        policy = RankedSchemaPolicy(ranker)
        initial = verifier.start(theorem.id, theorem.proposition)
        result = SearchController[LiveLeanState](max_nodes, max_proposals).run(
            initial, policy, verifier,
            lambda state: state.goal_text == SOLVED_GOAL_TEXT,
        )
        states = {entry.state_before.goal_text for entry in result.trace}
        states.add(initial.goal_text)
        overlap = states & training_states
        seen |= states
        per_theorem.append(
            {
                "theorem": theorem.id,
                "distinct_states": len(states),
                "states_in_training_extraction": len(overlap),
                "examples": sorted(overlap)[:3],
            }
        )
    return {
        "arm": ranker.name,
        "distinct_states_across_set": len(seen),
        "states_in_training_extraction": len(seen & training_states),
        "training_states_compared": len(training_states),
        "per_theorem": per_theorem,
    }


def verify_budget_monotonicity(
    pool: BackendPool,
    theorem_set: TheoremSet,
    theorem: Theorem,
    ranker: SchemaRanker,
    nodes: int,
    proposals: int,
    predicted_solved: bool,
) -> dict[str, object]:
    """Re-run one (theorem, arm) at a smaller budget and check the derivation."""
    verifier = pool.verifier(theorem_set.backend_of(theorem))
    record = run_theorem(verifier, theorem, ranker, nodes, proposals)
    return {
        "theorem": theorem.id,
        "arm": ranker.name,
        "budget_nodes": nodes,
        "budget_proposals": proposals,
        "predicted_solved": predicted_solved,
        "observed_solved": record.solved,
        "agrees": bool(record.solved) == bool(predicted_solved),
    }


#: The four theorem identities v0.6 held out when it trained the checkpoint
#: and computed its frequency baseline.  Repeated here so the frequency arm is
#: rebuilt from exactly the rows that produced the 64-proposal winner.
V06_HELD_OUT = frozenset(
    {
        "BooleanLaws.double_negation",
        "BooleanLaws.identity_and_true",
        "BooleanLaws.distrib_and_or",
        "BooleanLaws.modus_ponens",
    }
)


def training_schema_counts(
    rows: Iterable[dict], held_out: frozenset[str] = V06_HELD_OUT
) -> dict[str, int]:
    """Schema counts over v0.6's own 44 training rows.  State-blind by design."""
    counts: Counter[str] = Counter()
    for row in rows:
        if row["theorem"] in held_out:
            continue
        schema = extraction_schema(row["tactic"])
        if schema is not None:
            counts[schema] += 1
    return {schema: counts.get(schema, 0) for schema in SCHEMAS}
