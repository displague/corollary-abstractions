#!/usr/bin/env python3
"""Live Lean tactic application and capability-blind branch search.

Unlike ``scripts/oracle_controller_demo.py``, this module never looks up a
committed state/tactic/state transition.  A PyPantograph backend asks Lean to
apply every proposed tactic to a live goal.  The public controller state holds
only an opaque verifier-minted handle and rendered goal text; Pantograph's
mutable/lifetime-sensitive ``GoalState`` objects remain private to the adapter.

Registered predictions (P-LS, written before the live adjudicating run):

P-LS1. Live PyPantograph application closes the held-out proposition
    ``forall (P Q : Prop) (h : P ∧ Q), Q ∧ P`` through the generic
    SearchController.  This theorem is absent from ``sample_triples.json``;
    success therefore cannot be committed-transition replay.
P-LS2. A static, unranked tactic palette solves within 64 expanded states and
    512 proposals.  The trace contains an accepted ``clear h`` transition that
    removes the only conjunction premise, but the solution path excludes it:
    this is real branch abandonment, not a sequence with rejected no-ops.
P-LS3. Removing ``exact h.left`` and ``exact h.right`` from that same palette
    leaves the target unsolved under the same budgets.  The capability-blind
    control makes the projection tactics load-bearing.
P-LS4. Public-state forgeries (unknown handle, changed rendered goal, changed
    theorem, or changed tactic history) are REFUSED before Lean is called; a
    tactic failure is REFUSED and supplies no next state.
P-LS5. This slice changes no corpus or matcher report, and the existing oracle
    proof/story demo remains green.  It adds search, not a learned policy.

First live adjudication (prediction text above retained): P-LS2 MISSED and
P-LS1 remained unsatisfied.  The blind and ablated arms both exhausted after
5 states (45 / 35 proposals).  Pantograph's bare ``intro`` creates inaccessible
pretty-printed names ``P✝``, ``Q✝``, and ``h✝``; the registered ``h.left`` and
``h.right`` candidates therefore failed with ``Unknown identifier``.  Search
correctly retained the four accepted structural steps; the palette had failed
to preserve a callable binder.

Corrective prediction P-LS6 (registered before the second live run): adding
the single standard tactic ``intro P Q h`` to the otherwise unchanged static
palette preserves accessible binder names.  The full arm then satisfies
P-LS1's held-out proof and P-LS2's accepted-``clear h`` branch criterion within
the original budgets, while the projection ablation remains unsolved.  This is
a palette-interface correction, not learned ranking; both runs stay public.

Second live adjudication: P-LS1, P-LS2's substantive branch criterion,
P-LS3, and P-LS6 FIRED.  The full palette solved after 9 expanded states,
12 distinct states, and 86 proposals (11 accepted / 75 rejected), with the
four-step path ``intro P Q h`` -> ``constructor`` -> ``exact h.right`` ->
``exact h.left``.  Three accepted ``clear h`` branches were outside that
solution.  The projection ablation exhausted after 10 states and 80 proposals
(9 accepted / 71 rejected).  The theorem name is absent from all 155 committed
extraction rows.  P-LS4 fired in the adapter regression suite; P-LS5 is
adjudicated by the repository-wide validation recorded in the result ledger.

Honest boundary: the palette is hand-written and unranked.  Solving this small
propositional theorem demonstrates live verification and backtracking control,
not tactic-policy learning or miniF2F performance.
"""

from __future__ import annotations

import argparse
import secrets
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    BranchPolicy,
    SearchController,
    SearchResult,
    Verification,
    Verdict,
)


HELD_OUT_THEOREM = "heldout.and_commute"
HELD_OUT_PROPOSITION = "forall (P Q : Prop) (h : P ∧ Q), Q ∧ P"
BLIND_TACTICS = (
    "clear h",          # accepted only after introductions; genuine dead branch
    "intro P Q h",      # one fixed candidate preserving accessible binder names
    "intro",
    "constructor",
    "assumption",
    "exact h.left",
    "exact h.right",
    "left",
    "right",
    "trivial",
)
ABLATION_TACTICS = tuple(
    tactic for tactic in BLIND_TACTICS
    if tactic not in {"exact h.left", "exact h.right"}
)


class TacticRejected(Exception):
    """A well-formed live request that Lean refused as a tactic step."""


class LeanBackend(Protocol):
    name: str

    def start(self, proposition: str) -> object: ...
    def apply(self, goal: object, tactic: str) -> object: ...
    def render(self, goal: object) -> str: ...
    def solved(self, goal: object) -> bool: ...


@dataclass(frozen=True)
class LiveLeanState:
    theorem: str
    goal_text: str
    handle: str
    tactics: tuple[str, ...] = ()


class LiveLeanVerifier:
    """Verifier adapter over private live-Lean goal objects."""

    name = "lean-live-tactic-application"

    def __init__(self, backend: LeanBackend):
        self.backend = backend
        self._states: dict[str, tuple[LiveLeanState, object]] = {}

    def _mint(self, theorem: str, goal: object,
              tactics: tuple[str, ...]) -> LiveLeanState:
        state = LiveLeanState(
            theorem=theorem,
            goal_text=self.backend.render(goal),
            handle=secrets.token_urlsafe(24),
            tactics=tactics,
        )
        self._states[state.handle] = (state, goal)
        return state

    def start(self, theorem: str, proposition: str) -> LiveLeanState:
        if not theorem or not proposition:
            raise ValueError("theorem and proposition must be non-empty")
        return self._mint(theorem, self.backend.start(proposition), ())

    def state_key(self, state: LiveLeanState) -> str:
        return f"{state.theorem}\n{state.goal_text}\n{state.tactics!r}"

    def evaluate(
        self, state: LiveLeanState, action: Action
    ) -> Verification[LiveLeanState]:
        stored = self._states.get(state.handle)
        if stored is None or stored[0] != state:
            return Verification(
                Verdict.REFUSED,
                "live Lean state is not an exact verifier-minted capability",
                evidence=(self.name,),
            )
        if action.kind is not ActionKind.GEN or action.name != "lean_tactic":
            return Verification(
                Verdict.REFUSED,
                "live Lean accepts only GEN(lean_tactic)",
                evidence=(self.name,),
            )
        if action.dependencies:
            return Verification(
                Verdict.REFUSED,
                "lean_tactic accepts no caller-supplied dependencies",
                evidence=(self.name,),
            )
        tactic = action.argument("tactic")
        if tactic is None or not tactic.strip():
            return Verification(
                Verdict.REFUSED,
                "lean_tactic requires a non-empty tactic",
                evidence=(self.name,),
            )
        if action.arguments != (("tactic", tactic),):
            return Verification(
                Verdict.REFUSED,
                "lean_tactic accepts exactly one tactic argument",
                evidence=(self.name,),
            )

        try:
            next_goal = self.backend.apply(stored[1], tactic)
        except TacticRejected as exc:
            return Verification(
                Verdict.REFUSED,
                f"Lean rejected tactic: {exc}",
                evidence=(self.name, self.backend.name),
            )

        next_state = self._mint(
            state.theorem, next_goal, state.tactics + (tactic,)
        )
        solved = self.backend.solved(next_goal)
        return Verification(
            Verdict.PROVEN if solved else Verdict.VERIFIED,
            "Lean kernel accepted tactic"
            + (" and closed every goal" if solved else ""),
            next_state,
            (self.name, self.backend.name, state.theorem),
        )


@dataclass(frozen=True)
class StaticTacticPolicy(BranchPolicy[LiveLeanState]):
    """Capability-blind baseline: same ordered tactics at every state."""

    tactics: tuple[str, ...]

    def propose_all(self, state: LiveLeanState, trace) -> Iterable[Action]:
        del state, trace
        return tuple(
            Action.build(ActionKind.GEN, "lean_tactic", {"tactic": tactic})
            for tactic in self.tactics
        )


class PantographBackend:
    """Lazy optional PyPantograph adapter; importing the repo needs no wheel."""

    name = "PyPantograph/Lean4"

    def __init__(self, project_path: Path | None, imports: tuple[str, ...]):
        try:
            from pantograph.message import TacticFailure
            from pantograph.server import Server
        except ImportError as exc:
            raise RuntimeError(
                "PyPantograph is not installed in this Python environment; "
                "see prover/FEASIBILITY.md"
            ) from exc
        self._tactic_failure = TacticFailure
        self.server = Server(
            imports=list(imports),
            project_path=str(project_path) if project_path is not None else None,
        )

    def start(self, proposition: str) -> object:
        return self.server.goal_start(proposition)

    def apply(self, goal: object, tactic: str) -> object:
        try:
            return self.server.goal_tactic(goal, tactic)
        except self._tactic_failure as exc:
            raise TacticRejected(str(exc)) from exc

    def render(self, goal: object) -> str:
        return "no goals" if goal.is_solved else str(goal)

    def solved(self, goal: object) -> bool:
        return bool(goal.is_solved)

    def close(self) -> None:
        self.server._close()


def blind_search(
    verifier: LiveLeanVerifier,
    tactics: tuple[str, ...] = BLIND_TACTICS,
    max_nodes: int = 64,
    max_proposals: int = 512,
) -> SearchResult[LiveLeanState]:
    initial = verifier.start(HELD_OUT_THEOREM, HELD_OUT_PROPOSITION)
    return SearchController[LiveLeanState](
        max_nodes=max_nodes, max_proposals=max_proposals
    ).run(
        initial,
        StaticTacticPolicy(tactics),
        verifier,
        lambda state: state.goal_text == "no goals",
    )


def print_result(label: str, result: SearchResult[LiveLeanState]) -> None:
    print(
        f"{label}: {result.stop_reason.value}; nodes={result.nodes_expanded} "
        f"states={result.states_seen} proposals={result.proposals} "
        f"accepted={result.accepted_proposals} "
        f"rejected={result.rejected_proposals}"
    )
    if result.solved:
        print("  solution:")
        for entry in result.solution_trace:
            print(f"    {entry.action.argument('tactic')} -> "
                  f"{entry.verification.verdict.value}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=None,
                        help="optional Lake project; Init-only search needs none")
    parser.add_argument("--import", dest="imports", action="append",
                        default=["Init"])
    parser.add_argument("--max-nodes", type=int, default=64)
    parser.add_argument("--max-proposals", type=int, default=512)
    args = parser.parse_args()

    backend = PantographBackend(args.project, tuple(args.imports))
    try:
        full = blind_search(
            LiveLeanVerifier(backend), BLIND_TACTICS,
            args.max_nodes, args.max_proposals
        )
        print_result("blind palette", full)
        ablated = blind_search(
            LiveLeanVerifier(backend), ABLATION_TACTICS,
            args.max_nodes, args.max_proposals
        )
        print_result("projection ablation", ablated)
    finally:
        backend.close()

    if not full.solved or ablated.solved:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
