#!/usr/bin/env python3
"""Oracle-first v0.5 demo: one controller, proof replay and story execution.

The proof adapter replays three contiguous transitions previously extracted
from Lean into prover/sample_triples.json. It does NOT claim live tactic search.
The story adapter executes setup -> complication -> resolution against a small
frame-state verifier. Both travel through scripts/controller.py unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path

from controller import (
    Action,
    ActionKind,
    Controller,
    RunResult,
    SequencePolicy,
    Verification,
    Verdict,
)
from frames import FrameExecutor, FrameSpec, FrameState, Literal


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRIPLES = REPO_ROOT / "prover" / "sample_triples.json"
LEAN_THEOREM = "BooleanLaws.absorption_or_and"
LEAN_TACTICS = ("intro hp", "left", "exact hp")
TRUSTED_TRIPLES_SHA256 = (
    "8dcc31e4d95cf8443194e5eb64872a0db308475b9424ccf2b760b086a52180d7"
)


@dataclass(frozen=True)
class LeanReplayState:
    theorem: str
    proof_state: str
    tactics: tuple[str, ...] = ()


class LeanReplayVerifier:
    """Exact membership/replay adapter over machine-extracted Lean triples."""

    name = "lean-extracted-transition-replay"

    def __init__(self, triples_path: Path = DEFAULT_TRIPLES):
        raw = triples_path.read_bytes()
        records = json.loads(raw.decode("utf-8"))
        self.triples_path = triples_path
        self.extraction_sha256 = hashlib.sha256(raw).hexdigest()
        self.trusted_extraction = self.extraction_sha256 == TRUSTED_TRIPLES_SHA256
        self._transitions = {
            (row["theorem"], row["stateBefore"], row["tactic"]): row["stateAfter"]
            for row in records
        }

    def state_key(self, state: LeanReplayState) -> str:
        return f"{state.theorem}\n{state.proof_state}"

    def evaluate(
        self, state: LeanReplayState, action: Action
    ) -> Verification[LeanReplayState]:
        if action.kind is not ActionKind.GEN or action.name != "lean_tactic":
            return Verification(
                Verdict.REFUSED,
                "Lean replay accepts only GEN(lean_tactic)",
                evidence=(self.name,),
            )
        tactic = action.argument("tactic")
        if tactic is None:
            return Verification(
                Verdict.REFUSED,
                "lean_tactic requires a tactic argument",
                evidence=(self.name,),
            )
        key = (state.theorem, state.proof_state, tactic)
        state_after = self._transitions.get(key)
        if state_after is None:
            return Verification(
                Verdict.REFUSED,
                "transition is absent from the committed Lean extraction; "
                "replay cannot adjudicate it",
                evidence=(self.name, str(self.triples_path)),
            )
        next_state = replace(
            state,
            proof_state=state_after,
            tactics=state.tactics + (tactic,),
        )
        proof_closed = state_after == "no goals"
        verdict = (
            Verdict.PROVEN
            if proof_closed and self.trusted_extraction
            else Verdict.VERIFIED
        )
        reason = "exact state/tactic/state transition found in extraction"
        if proof_closed and not self.trusted_extraction:
            reason += "; final state is not PROVEN because the extraction digest is untrusted"
        return Verification(
            verdict,
            reason,
            next_state,
            (
                self.name,
                str(self.triples_path),
                f"sha256:{self.extraction_sha256}",
            ),
        )


def lean_oracle_run(triples_path: Path = DEFAULT_TRIPLES) -> RunResult[LeanReplayState]:
    verifier = LeanReplayVerifier(triples_path)
    records = json.loads(triples_path.read_text(encoding="utf-8"))
    first = next(
        row
        for row in records
        if row["theorem"] == LEAN_THEOREM and row["tactic"] == LEAN_TACTICS[0]
    )
    initial = LeanReplayState(LEAN_THEOREM, first["stateBefore"])
    actions = tuple(
        Action.build(ActionKind.GEN, "lean_tactic", {"tactic": tactic})
        for tactic in LEAN_TACTICS
    )
    return Controller[LeanReplayState](max_steps=3).run(
        initial,
        SequencePolicy(actions),
        verifier,
        lambda state: state.proof_state == "no goals",
    )


@dataclass(frozen=True)
class StoryBeat:
    role: str
    text: str


@dataclass(frozen=True)
class StoryState:
    """Story progress on top of a real frame state, not beside one."""

    frame_state: FrameState
    desire: str | None = None
    beats: tuple[StoryBeat, ...] = ()

    @property
    def agent(self) -> str | None:
        """The frame's declared agent, or None if the spec omits one."""
        for _, literal in self.frame_state.spec.declarations:
            if literal.predicate == "agent" and literal.polarity:
                return literal.value
        return None


def golden_chicken_frame_spec() -> FrameSpec:
    return FrameSpec(
        frame="narrative.frames.golden_chicken",
        title="The golden chicken",
        declarations=(
            ("agent", Literal("story", "agent", "the golden chicken")),
            ("golden", Literal("the golden chicken", "trait", "golden")),
            (
                "no_silver",
                Literal("the golden chicken", "trait", "silver", polarity=False),
            ),
        ),
    )


class StoryFrameVerifier:
    """Three-beat story grammar over the runtime frame executor.

    Beat ordering and desire preservation are the story grammar's own laws
    (narrative.structure.*); trait consistency is delegated to the frame
    executor, which adjudicates every trait literal against the frame's
    declarations and the unsuspended world exactly as scripts/frames.py
    documents. One executor, two costumes.
    """

    name = "narrative-three-beat-frame"

    def __init__(
        self,
        executor: FrameExecutor | None = None,
        spec: FrameSpec | None = None,
    ):
        self.executor = executor or FrameExecutor()
        self.spec = spec or golden_chicken_frame_spec()

    def initial_state(self) -> StoryState:
        return StoryState(frame_state=self.executor.open_frame(self.spec))

    def state_key(self, state: StoryState) -> str:
        return repr(state)

    def evaluate(
        self, state: StoryState, action: Action
    ) -> Verification[StoryState]:
        if action.kind is not ActionKind.GEN:
            return Verification(
                Verdict.REFUSED,
                "story adapter currently accepts only GEN transitions",
                evidence=(self.name,),
            )
        args = dict(action.arguments)
        if state.agent is None:
            return Verification(
                Verdict.REFUSED,
                "story frame declares no agent premise; the adapter cannot "
                "adjudicate agent-bound beats",
                evidence=(self.name,),
            )
        if args.get("agent") not in {None, state.agent}:
            return Verification(
                Verdict.REFUTED,
                "candidate changes the frame's declared agent",
                evidence=("narrative.frame.frame_consistency",),
            )
        trait = args.get("trait")
        if trait is not None:
            finding = self.executor.check(
                state.frame_state,
                Literal(state.agent, "trait", trait),
            )
            if finding.verdict is Verdict.REFUTED:
                return Verification(
                    Verdict.REFUTED,
                    "candidate asserts a trait explicitly denied by the "
                    f"frame ({finding.reason})",
                    evidence=finding.evidence,
                )
            if finding.verdict is not Verdict.VERIFIED:
                return Verification(
                    Verdict.UNKNOWN,
                    "candidate trait is neither declared nor denied in this "
                    f"frame ({finding.reason})",
                    evidence=finding.evidence,
                )

        if action.name == "introduce":
            if state.beats:
                return self._order_refutation("setup must be the first beat")
            desire = args.get("desire")
            if not desire:
                return Verification(Verdict.UNKNOWN, "setup has an unbound desire")
            beat = StoryBeat(
                "setup", f"{state.agent.capitalize()} wanted {desire}."
            )
            return Verification(
                Verdict.VERIFIED,
                "setup binds agent and desire inside the frame",
                replace(state, desire=desire, beats=(beat,)),
                ("narrative.structure.setup_introduction",),
            )

        if action.name == "obstruct":
            if len(state.beats) != 1 or state.beats[0].role != "setup":
                return self._order_refutation("complication requires one setup")
            if args.get("desire") != state.desire:
                return self._desire_refutation()
            obstacle = args.get("obstacle")
            if not obstacle:
                return Verification(Verdict.UNKNOWN, "complication has no obstacle")
            beat = StoryBeat(
                "complication", f"But {obstacle} stood in the way."
            )
            return Verification(
                Verdict.VERIFIED,
                "complication obstructs the setup's bound desire",
                replace(state, beats=state.beats + (beat,)),
                ("narrative.structure.complication_obstruction",),
            )

        if action.name == "resolve":
            if tuple(beat.role for beat in state.beats) != ("setup", "complication"):
                return self._order_refutation(
                    "resolution requires setup followed by complication"
                )
            if args.get("desire") != state.desire:
                return self._desire_refutation()
            outcome = args.get("outcome")
            if not outcome:
                return Verification(Verdict.UNKNOWN, "resolution has no outcome")
            beat = StoryBeat("resolution", outcome)
            return Verification(
                Verdict.VERIFIED,
                "resolution closes the setup's bound desire",
                replace(state, beats=state.beats + (beat,)),
                (
                    "narrative.structure.resolution_outcome",
                    "narrative.structure.story_sequence",
                ),
            )

        return Verification(
            Verdict.REFUSED,
            f"unknown story transition {action.name!r}",
            evidence=(self.name,),
        )

    @staticmethod
    def _order_refutation(reason: str) -> Verification[StoryState]:
        return Verification(
            Verdict.REFUTED,
            reason,
            evidence=("narrative.structure.story_sequence",),
        )

    @staticmethod
    def _desire_refutation() -> Verification[StoryState]:
        return Verification(
            Verdict.REFUTED,
            "beat does not preserve the desire bound by the setup",
            evidence=(
                "narrative.structure.setup_introduction",
                "narrative.structure.complication_obstruction",
                "narrative.structure.resolution_outcome",
            ),
        )


STORY_DESIRE = "to sing the sunrise awake"


def story_oracle_actions() -> tuple[Action, ...]:
    shared = {"agent": "the golden chicken", "desire": STORY_DESIRE}
    return (
        Action.build(
            ActionKind.GEN,
            "introduce",
            {**shared, "trait": "golden"},
        ),
        Action.build(
            ActionKind.GEN,
            "obstruct",
            {**shared, "obstacle": "the locked coop door"},
        ),
        Action.build(
            ActionKind.GEN,
            "resolve",
            {
                **shared,
                "outcome": (
                    "It used a fallen feather as a key, stepped outside, "
                    "and sang until the sun rose"
                ),
            },
        ),
    )


def story_oracle_run() -> RunResult[StoryState]:
    verifier = StoryFrameVerifier()
    return Controller[StoryState](max_steps=3).run(
        verifier.initial_state(),
        SequencePolicy(story_oracle_actions()),
        verifier,
        lambda state: tuple(beat.role for beat in state.beats)
        == ("setup", "complication", "resolution"),
    )


def _print_run(label: str, run: RunResult[object]) -> None:
    print(f"\n{label}: {run.stop_reason.value}")
    for entry in run.trace:
        print(
            f"  {entry.index + 1}. {entry.action.kind.value}:{entry.action.name} "
            f"-> {entry.verification.verdict.value}"
        )
        print(f"     {entry.verification.reason}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triples", type=Path, default=DEFAULT_TRIPLES)
    args = parser.parse_args()

    lean = lean_oracle_run(args.triples)
    story = story_oracle_run()
    _print_run("LEAN TRANSITION REPLAY", lean)
    _print_run("GOLDEN CHICKEN", story)
    print("\nSTORY")
    for beat in story.final_state.beats:
        print(f"  {beat.role.upper()}: {beat.text}")

    _, demoted = FrameExecutor().close_frame(story.final_state.frame_state)
    print("\nON FRAME EXIT (truths demote; nothing leaks)")
    for claim in demoted:
        print(
            f"  {claim.literal.describe()} -> {claim.epistemic_status} "
            f"outside {claim.frame}"
        )
    print(
        "\nLIMIT: Lean steps are exact committed extraction replay; "
        "live PyPantograph search remains unbuilt. The frame executor "
        "checks declarations, denials and suspensions; Chekhov-style "
        "temporal obligations are not yet evaluated."
    )
    return 0 if lean.solved and story.solved else 1


if __name__ == "__main__":
    raise SystemExit(main())
