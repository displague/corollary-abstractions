#!/usr/bin/env python3
"""Runtime frame executor: the epistemic ladder evaluated inside a scope.

docs/DESIGN-frames-and-retrieval.md section 1, made executable. A frame is
opened from declarations (its local VERIFIED tier), assertions inside it are
adjudicated against those declarations plus the corpus's world truths minus
the frame's `suspends` list, and on exit every frame-local truth demotes to
the frame's `on_exit` epistemic status. Frame truths never leak.

Adjudication order and semantics (each is a deliberate design decision):

0. The boundary rule: a frame OPENS only if its declarations contradict no
   unsuspended world truth. "Invention is unlimited at the boundary" means
   unlimited once the contradicted truths are explicitly suspended -- a
   declaration is not a side door around `suspends`. (This was the
   blocking finding of the slice's adversarial review: without the check,
   any contradiction could be smuggled in by phrasing it as a premise.)
1. A literal matching a frame declaration or an accepted assertion is
   VERIFIED frame-locally, citing the premise that grounds it.
2. A literal contradicting a declaration or accepted assertion is REFUTED,
   citing the frame's governing law (narrative.frame.frame_consistency by
   default) and the contradicted premise. Explicitly denied premises
   (negative-polarity declarations) refute their positive assertion exactly
   as a false physics claim would be refuted.
3. A literal grounded by an UNSUSPENDED world truth is VERIFIED (agrees) or
   REFUTED (contradicts), citing the corpus statement_id that grounds it.
   The world itself must be coherent: a world mapping two statements to
   opposite polarities of one atom is rejected at construction, so
   adjudication cannot depend on iteration order.
4. A literal whose ONLY grounding is a SUSPENDED world truth is UNKNOWN to
   `check` (read-only adjudication: the suspension removed the grounding,
   and nothing else supplies one -- for either polarity). `assert_literal`
   may then ADMIT it as a new frame-local premise: suspension is the
   author's explicit invitation to rewrite that truth locally, and
   admission is an act of invention, not a verification. Once admitted,
   its negation is REFUTED by rule 2 -- inventions are consistent from the
   moment they are made.
5. A literal with no grounding anywhere -- neither declared nor denied in
   the frame, no world truth either way -- is UNKNOWN. Missing information
   is never REFUTED, and an ungrounded assertion with no suspension
   invitation is not silently admitted either.
6. A closed frame adjudicates nothing and admits nothing: `check` and
   `assert_literal` both REFUSE, and closing twice is a caller error.

The executor is a plain verifier component: it holds no mutable state, and
`FrameAssertionVerifier` adapts it to scripts/controller.py's contract so
frame evaluation rides the same generic loop as Lean replay and the story
oracle. Rejected branches cannot mutate accepted frame state -- that
invariant belongs to the Controller and is inherited, not reimplemented.

What this deliberately does NOT claim: temporal liveness (Chekhov
obligations) is not evaluated here; story state is not Lean-proved merely
because frame_consistency twins a Lean-backed Boolean law -- the executor
cites that law, the matcher established the twin, and those are the whole
of the connection.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from controller import Action, ActionKind, Verification, Verdict


FRAME_CONSISTENCY = "narrative.frame.frame_consistency"


@dataclass(frozen=True)
class Literal:
    """One atomic claim: subject's predicate has (or lacks) a value."""

    subject: str
    predicate: str
    value: str
    polarity: bool = True

    @property
    def atom(self) -> tuple[str, str, str]:
        return (self.subject, self.predicate, self.value)

    @property
    def negated(self) -> "Literal":
        return replace(self, polarity=not self.polarity)

    def describe(self) -> str:
        verb = "has" if self.polarity else "does not have"
        return f"{self.subject} {verb} {self.predicate}={self.value}"


@dataclass(frozen=True)
class FrameSpec:
    """A frame's boundary: identity, premises, suspensions, governance."""

    frame: str
    title: str = ""
    declarations: tuple[tuple[str, Literal], ...] = ()
    suspends: tuple[str, ...] = ()
    governed_by: tuple[str, ...] = (FRAME_CONSISTENCY,)
    on_exit: str = "conjectured"
    retrieval: str = "open"


@dataclass(frozen=True)
class FrameState:
    """Immutable frame-local state: spec plus accepted assertions."""

    spec: FrameSpec
    asserted: tuple[tuple[str, Literal], ...] = ()
    closed: bool = False

    @property
    def local_truths(self) -> tuple[tuple[str, Literal], ...]:
        return self.spec.declarations + self.asserted


@dataclass(frozen=True)
class Adjudication:
    """A frame-local ladder placement for one literal (no state change).

    ``suspended_grounds`` is non-empty exactly when the literal's only
    grounding corpus truths are suspended by the frame -- the structural
    marker `assert_literal` uses to admit the literal as an invention.
    """

    verdict: Verdict
    reason: str
    evidence: tuple[str, ...] = ()
    suspended_grounds: tuple[str, ...] = ()


@dataclass(frozen=True)
class DemotedClaim:
    """A frame truth after exit: same literal, demoted epistemic status."""

    claim_id: str
    literal: Literal
    epistemic_status: str
    frame: str


class FrameExecutor:
    """Evaluate literals against a frame's local tier plus the world.

    ``world`` maps corpus statement_ids to the ground literals they warrant;
    the caller declares that grounding explicitly, which keeps the executor
    honest about where each world truth comes from (a real statement_id the
    validator can resolve, never an unattributed fact).
    """

    def __init__(self, world: Mapping[str, tuple[Literal, ...]] | None = None):
        self.world: dict[str, tuple[Literal, ...]] = {
            sid: tuple(literals) for sid, literals in (world or {}).items()
        }
        polarity_of: dict[tuple[str, str, str], tuple[str, bool]] = {}
        for statement_id, truths in self.world.items():
            for truth in truths:
                prior = polarity_of.get(truth.atom)
                if prior is not None and prior[1] != truth.polarity:
                    raise ValueError(
                        "incoherent world: "
                        f"{prior[0]!r} and {statement_id!r} ground "
                        f"{truth.atom} with opposite polarities"
                    )
                polarity_of.setdefault(truth.atom, (statement_id, truth.polarity))

    def open_frame(self, spec: FrameSpec) -> FrameState:
        seen: dict[tuple[str, str, str], tuple[str, Literal]] = {}
        for premise_id, literal in spec.declarations:
            prior = seen.get(literal.atom)
            if prior is not None and prior[1].polarity != literal.polarity:
                raise ValueError(
                    f"frame {spec.frame!r} declares a contradiction: "
                    f"{prior[0]!r} vs {premise_id!r} on {literal.atom}"
                )
            seen.setdefault(literal.atom, (premise_id, literal))
            # The boundary rule: a declaration may contradict a world truth
            # only if the frame explicitly suspends that truth. Otherwise a
            # declaration would be a side door around `suspends` -- the
            # blocking finding of this slice's adversarial review.
            for statement_id, truths in self.world.items():
                if statement_id in spec.suspends:
                    continue
                for truth in truths:
                    if (
                        truth.atom == literal.atom
                        and truth.polarity != literal.polarity
                    ):
                        raise ValueError(
                            f"frame {spec.frame!r} premise {premise_id!r} "
                            f"contradicts corpus truth {statement_id!r}, "
                            "which the frame does not suspend"
                        )
        return FrameState(spec=spec)

    def check(self, state: FrameState, literal: Literal) -> Adjudication:
        spec = state.spec
        if state.closed:
            return Adjudication(
                Verdict.REFUSED,
                "frame is closed; its local tier adjudicates nothing",
                (spec.frame,),
            )

        for premise_id, truth in state.local_truths:
            if truth.atom != literal.atom:
                continue
            if truth.polarity == literal.polarity:
                return Adjudication(
                    Verdict.VERIFIED,
                    f"grounded by frame premise {premise_id!r}",
                    (spec.frame, premise_id),
                )
            if not truth.polarity:
                return Adjudication(
                    Verdict.REFUTED,
                    f"candidate asserts what frame premise {premise_id!r} "
                    "explicitly denied",
                    spec.governed_by + (premise_id,),
                )
            return Adjudication(
                Verdict.REFUTED,
                f"candidate contradicts frame premise {premise_id!r}",
                spec.governed_by + (premise_id,),
            )

        suspended_grounds: list[str] = []
        for statement_id, truths in self.world.items():
            for truth in truths:
                if truth.atom != literal.atom:
                    continue
                if statement_id in spec.suspends:
                    suspended_grounds.append(statement_id)
                    continue
                if truth.polarity == literal.polarity:
                    return Adjudication(
                        Verdict.VERIFIED,
                        f"grounded by unsuspended corpus truth {statement_id!r}",
                        (statement_id,),
                    )
                return Adjudication(
                    Verdict.REFUTED,
                    "candidate contradicts corpus truth "
                    f"{statement_id!r}, which this frame does not suspend",
                    spec.governed_by + (statement_id,),
                )

        if suspended_grounds:
            cited = ", ".join(repr(s) for s in suspended_grounds)
            return Adjudication(
                Verdict.UNKNOWN,
                "ungrounded here: the only grounding corpus truth is "
                f"suspended by this frame ({cited}); assert_literal may "
                "admit it as a new frame-local premise",
                (spec.frame,) + tuple(suspended_grounds),
                suspended_grounds=tuple(suspended_grounds),
            )

        return Adjudication(
            Verdict.UNKNOWN,
            "candidate is neither declared nor denied in this frame, and no "
            "corpus truth grounds it either way",
            spec.governed_by,
        )

    def assert_literal(
        self, state: FrameState, claim_id: str, literal: Literal
    ) -> Verification[FrameState]:
        if state.closed:
            return Verification(
                Verdict.REFUSED,
                "frame is closed; its local tier no longer accepts assertions",
                evidence=(state.spec.frame,),
            )
        finding = self.check(state, literal)

        if finding.verdict is Verdict.VERIFIED:
            # Already grounded: accept without duplicating the premise.
            return Verification(
                finding.verdict, finding.reason, state, finding.evidence
            )

        if finding.verdict is Verdict.UNKNOWN and finding.suspended_grounds:
            next_state = replace(
                state, asserted=state.asserted + ((claim_id, literal),)
            )
            return Verification(
                Verdict.VERIFIED,
                "admitted as a new frame-local premise: the only grounding "
                "corpus truth is suspended, and suspension is the author's "
                "explicit invitation to rewrite it locally",
                next_state,
                finding.evidence,
            )

        return Verification(
            finding.verdict, finding.reason, evidence=finding.evidence
        )

    def close_frame(
        self, state: FrameState
    ) -> tuple[FrameState, tuple[DemotedClaim, ...]]:
        if state.closed:
            raise ValueError(
                f"frame {state.spec.frame!r} is already closed; closing "
                "twice would re-emit its demotions"
            )
        demoted = tuple(
            DemotedClaim(
                claim_id=claim_id,
                literal=literal,
                epistemic_status=state.spec.on_exit,
                frame=state.spec.frame,
            )
            for claim_id, literal in state.local_truths
        )
        return replace(state, closed=True), demoted


class FrameAssertionVerifier:
    """Adapt FrameExecutor to the generic controller contract.

    Accepts GEN(assert_fact) with subject/predicate/value/polarity/claim_id
    arguments. RETRIEVE is REFUSED: either the frame forbids it
    (`retrieval: frame_local`) or no retrieval adapter is wired yet -- the
    two refusals carry distinct reasons so the trace records which limit
    applied.
    """

    name = "frame-local-ladder"

    def __init__(self, executor: FrameExecutor):
        self.executor = executor

    def state_key(self, state: FrameState) -> str:
        return (
            f"{state.spec.frame}|closed={state.closed}|"
            f"{[claim_id for claim_id, _ in state.asserted]!r}"
        )

    def evaluate(
        self, state: FrameState, action: Action
    ) -> Verification[FrameState]:
        if action.kind is ActionKind.RETRIEVE:
            if state.spec.retrieval == "frame_local":
                return Verification(
                    Verdict.REFUSED,
                    "frame declares this unknown unresolvable-by-retrieval "
                    "(retrieval: frame_local)",
                    evidence=(state.spec.frame,),
                )
            return Verification(
                Verdict.REFUSED,
                "no retrieval adapter is wired yet (BACKLOG: controller/harness)",
                evidence=(self.name,),
            )
        if action.kind is not ActionKind.GEN or action.name != "assert_fact":
            return Verification(
                Verdict.REFUSED,
                "frame ladder accepts only GEN(assert_fact)",
                evidence=(self.name,),
            )
        required = ("claim_id", "subject", "predicate", "value")
        arguments = dict(action.arguments)
        missing = [key for key in required if not arguments.get(key)]
        if missing:
            return Verification(
                Verdict.REFUSED,
                f"assert_fact has missing or empty arguments: {missing}",
                evidence=(self.name,),
            )
        polarity = arguments.get("polarity", "true")
        if polarity not in {"true", "false"}:
            return Verification(
                Verdict.REFUSED,
                f"assert_fact polarity must be 'true' or 'false', got "
                f"{polarity!r}",
                evidence=(self.name,),
            )
        literal = Literal(
            subject=arguments["subject"],
            predicate=arguments["predicate"],
            value=arguments["value"],
            polarity=polarity == "true",
        )
        return self.executor.assert_literal(state, arguments["claim_id"], literal)
