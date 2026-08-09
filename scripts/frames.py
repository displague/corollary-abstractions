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
   citing the violated law -- narrative.frame.frame_consistency -- and the
   contradicted premise. Evidence names the law a verdict rests on, never
   the frame's whole statute book: a trait contradiction does not cite the
   temporal laws the frame happens to adopt. Explicitly denied premises
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
6. `plant` registers one frame-local temporal obligation per element under
   Chekhov's gun; `discharge` closes the matching obligation. Repeating either
   accepted event is idempotent. An unheralded discharge (no prior plant)
   splits on governance: a frame that ADOPTS the past-facing converse --
   `narrative.constraint.no_deus_ex_machina` in `governed_by` -- REFUTES it,
   citing that law; a frame that does not adopt it leaves the discharge
   UNKNOWN, because coincidence-driven genres may reject the constraint
   deliberately (the corpus node's own regularity note). Adoption gives the
   STRICT event-order reading: the ledger is strictly sequenced, so a herald
   must be planted by an earlier event -- the corpus invariant anticipates
   exactly this ("strict narrative preparation still requires the executor's
   event-order check"); the law's inclusive same-position herald has no
   representation in this runtime, so under adoption a plant-less discharge
   is REFUTED, while the closest expressible encoding -- reusing the
   plant's own event id for the discharge -- is REFUSED as an id collision
   before the law is ever consulted. A deliberate narrowing, recorded here.
   Adoption also extends the non-adopting UNKNOWN's evidence to cite the
   adoptable law alongside Chekhov's gun.
7. A frame with an outstanding obligation REFUSES to close, remains open, and
   emits no demotions. A closed frame adjudicates nothing and admits nothing:
   every transition REFUSES, and closing twice is a caller error.

The executor is a plain verifier component: it holds no mutable state, and
`FrameAssertionVerifier` adapts it to scripts/controller.py's contract so
frame evaluation rides the same generic loop as Lean replay and the story
oracle. Rejected branches cannot mutate accepted frame state -- that
invariant belongs to the Controller and is inherited, not reimplemented.

What this deliberately does NOT claim: this finite close-time check is not a
general LTL model checker. Story state is not Lean-proved merely because
frame_consistency twins a Lean-backed Boolean law -- the executor cites that
law, the matcher established the twin, and those are the whole connection.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from controller import Action, ActionKind, Verification, Verdict


FRAME_CONSISTENCY = "narrative.frame.frame_consistency"
CHEKHOV_GUN = "narrative.constraint.chekhov_gun"
NO_DEUS = "narrative.constraint.no_deus_ex_machina"


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
    owner: str | None = None
    corpus_backed: bool = False
    title: str = ""
    declarations: tuple[tuple[str, Literal], ...] = ()
    suspends: tuple[str, ...] = ()
    governed_by: tuple[str, ...] = (FRAME_CONSISTENCY,)
    on_exit: str = "conjectured"
    retrieval: str = "open"

    def __post_init__(self) -> None:
        if self.owner is not None and not self.owner.strip():
            raise ValueError("frame owner must be non-empty when supplied")
        if self.corpus_backed:
            if self.frame.startswith("runtime.frames."):
                raise ValueError("a corpus-backed frame cannot use runtime.frames.*")
        elif not self.frame.startswith("runtime.frames."):
            raise ValueError(
                "a runtime-only frame must use the reserved runtime.frames.* namespace"
            )


@dataclass(frozen=True)
class FrameState:
    """Immutable frame-local state: spec plus accepted assertions."""

    spec: FrameSpec
    asserted: tuple[tuple[str, Literal], ...] = ()
    obligations: tuple["TemporalObligation", ...] = ()
    observed_events: tuple["FrameEvent", ...] = ()
    processed_event_ids: tuple[str, ...] = ()
    superseded_declarations: tuple[str, ...] = ()
    closed: bool = False

    @property
    def local_truths(self) -> tuple[tuple[str, Literal], ...]:
        declarations = tuple(
            pair
            for pair in self.spec.declarations
            if pair[0] not in self.superseded_declarations
        )
        return declarations + self.asserted


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


@dataclass(frozen=True)
class TemporalObligation:
    """One planted element and the event that eventually discharged it."""

    element: str
    planted_by: str
    discharged_by: str | None = None

    @property
    def outstanding(self) -> bool:
        return self.discharged_by is None


@dataclass(frozen=True)
class FrameEvent:
    """One state change and the agents allowed to learn from it.

    Only predicates explicitly listed in ``functional_predicates`` replace a
    prior positive value (location is functional; traits generally are not).
    """

    event_id: str
    effects: tuple[Literal, ...]
    witnessed_by: tuple[str, ...]
    functional_predicates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must be non-empty")
        if not self.effects:
            raise ValueError("an event must carry at least one effect")
        if any(not owner.strip() for owner in self.witnessed_by):
            raise ValueError("witnessed_by owners must be non-empty")
        if len(set(self.witnessed_by)) != len(self.witnessed_by):
            raise ValueError("witnessed_by owners must be unique")
        if any(not predicate.strip() for predicate in self.functional_predicates):
            raise ValueError("functional_predicates must be non-empty strings")
        if len(set(self.functional_predicates)) != len(self.functional_predicates):
            raise ValueError("functional_predicates must be unique")
        polarities: dict[tuple[str, str, str], bool] = {}
        for effect in self.effects:
            atom = (effect.subject, effect.predicate, effect.value)
            previous = polarities.setdefault(atom, effect.polarity)
            if previous is not effect.polarity:
                raise ValueError(
                    "an event may not carry contradictory effects for one atom"
                )
        effect_predicates = {effect.predicate for effect in self.effects}
        if not set(self.functional_predicates).issubset(effect_predicates):
            raise ValueError("functional_predicates must name an event effect")
        functional_values: dict[tuple[str, str], str] = {}
        for effect in self.effects:
            if (
                not effect.polarity
                or effect.predicate not in self.functional_predicates
            ):
                continue
            key = (effect.subject, effect.predicate)
            previous = functional_values.setdefault(key, effect.value)
            if previous != effect.value:
                raise ValueError(
                    "an event may not assign competing positive values to a "
                    "functional predicate"
                )


@dataclass(frozen=True)
class FrameCloseResult:
    """Explicit close disposition, while preserving tuple unpacking.

    Existing callers may continue to use ``closed, demoted = close_frame(...)``.
    New callers should inspect ``verdict`` so an incomplete frame cannot be
    mistaken for a clean close.
    """

    verdict: Verdict
    reason: str
    state: FrameState
    demoted: tuple[DemotedClaim, ...] = ()
    evidence: tuple[str, ...] = ()

    def __iter__(self):
        yield self.state
        yield self.demoted


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

    def observe_event(
        self, state: FrameState, event: FrameEvent
    ) -> Verification[FrameState]:
        """Update an owned belief frame iff its owner witnessed the event."""

        if state.closed:
            return Verification(
                Verdict.REFUSED,
                "frame is closed; it accepts no observed events",
                evidence=(state.spec.frame, event.event_id),
            )
        owner = state.spec.owner
        if owner is None:
            return Verification(
                Verdict.REFUSED,
                "visibility-filtered events require an owned belief frame",
                evidence=(state.spec.frame, event.event_id),
            )
        for prior in state.observed_events:
            if prior.event_id != event.event_id:
                continue
            if prior == event:
                return Verification(
                    Verdict.VERIFIED,
                    "event was already observed; retry is idempotent",
                    state,
                    (owner, event.event_id),
                )
            return Verification(
                Verdict.REFUSED,
                "event id already identifies different visibility or effects",
                evidence=(owner, event.event_id),
            )
        if event.event_id in state.processed_event_ids:
            return Verification(
                Verdict.REFUSED,
                "event id was already processed outside this owner's visibility; "
                "visibility cannot be rewritten after the event",
                evidence=(owner, event.event_id),
            )
        if owner not in event.witnessed_by:
            return Verification(
                Verdict.VERIFIED,
                f"event is invisible to owner {owner!r}; belief state is unchanged",
                replace(
                    state,
                    processed_event_ids=(
                        state.processed_event_ids + (event.event_id,)
                    ),
                ),
                (owner, event.event_id, "not_witnessed"),
            )

        asserted = list(state.asserted)
        superseded = set(state.superseded_declarations)
        for index, effect in enumerate(event.effects):
            # Functional-predicate update: a witnessed location change replaces
            # the prior value. Explicit negative and positive effects let the
            # world refute the old value without inventing exclusivity rules in
            # the generic Literal checker.
            functional = effect.predicate in event.functional_predicates

            def supersedes(prior: Literal) -> bool:
                return (
                    prior.subject == effect.subject
                    and prior.predicate == effect.predicate
                    and (
                        prior.value == effect.value
                        or (effect.polarity and functional and prior.polarity)
                    )
                )

            asserted = [
                pair
                for pair in asserted
                if not supersedes(pair[1])
            ]
            superseded.update(
                claim_id
                for claim_id, literal in state.spec.declarations
                if supersedes(literal)
            )
            asserted.append((f"{event.event_id}:{index}", effect))
        next_state = replace(
            state,
            asserted=tuple(asserted),
            observed_events=state.observed_events + (event,),
            processed_event_ids=state.processed_event_ids + (event.event_id,),
            superseded_declarations=tuple(sorted(superseded)),
        )
        return Verification(
            Verdict.VERIFIED,
            f"owner {owner!r} witnessed the event and updated its belief frame",
            next_state,
            (owner, event.event_id),
        )

    @staticmethod
    def belief_value(
        state: FrameState, subject: str, predicate: str
    ) -> str | None:
        """Return the latest positive value held for a functional predicate."""

        for _, literal in reversed(state.local_truths):
            if (
                literal.subject == subject
                and literal.predicate == predicate
                and literal.polarity
            ):
                return literal.value
        return None

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
                    (FRAME_CONSISTENCY, premise_id),
                )
            return Adjudication(
                Verdict.REFUTED,
                f"candidate contradicts frame premise {premise_id!r}",
                (FRAME_CONSISTENCY, premise_id),
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
                    (FRAME_CONSISTENCY, statement_id),
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
            (spec.frame,),
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

    def plant(
        self, state: FrameState, event_id: str, element: str
    ) -> Verification[FrameState]:
        """Register the future-facing half of Chekhov's liveness law."""

        if state.closed:
            return Verification(
                Verdict.REFUSED,
                "frame is closed; it accepts no temporal events",
                evidence=(state.spec.frame,),
            )
        for obligation in state.obligations:
            if obligation.discharged_by == event_id:
                return Verification(
                    Verdict.REFUSED,
                    f"event id {event_id!r} already identifies a discharge",
                    evidence=(CHEKHOV_GUN, event_id),
                )
            if (
                obligation.planted_by == event_id
                and obligation.element != element
            ):
                return Verification(
                    Verdict.REFUSED,
                    f"event id {event_id!r} already plants a different element",
                    evidence=(CHEKHOV_GUN, obligation.planted_by),
                )
        for obligation in state.obligations:
            if obligation.element == element:
                if obligation.planted_by != event_id:
                    return Verification(
                        Verdict.REFUSED,
                        f"element {element!r} was already planted by event "
                        f"{obligation.planted_by!r}; a fresh id is not an "
                        "idempotent retry",
                        evidence=(CHEKHOV_GUN, obligation.planted_by),
                    )
                return Verification(
                    Verdict.VERIFIED,
                    f"element {element!r} already has a registered obligation",
                    state,
                    (CHEKHOV_GUN, obligation.planted_by),
                )
        obligation = TemporalObligation(element=element, planted_by=event_id)
        return Verification(
            Verdict.VERIFIED,
            f"planting {element!r} registers a frame-local discharge obligation",
            replace(state, obligations=state.obligations + (obligation,)),
            (CHEKHOV_GUN, event_id),
        )

    def discharge(
        self, state: FrameState, event_id: str, element: str
    ) -> Verification[FrameState]:
        """Discharge a matching plant without inventing the past converse."""

        if state.closed:
            return Verification(
                Verdict.REFUSED,
                "frame is closed; it accepts no temporal events",
                evidence=(state.spec.frame,),
            )
        for obligation in state.obligations:
            if obligation.planted_by == event_id:
                return Verification(
                    Verdict.REFUSED,
                    f"event id {event_id!r} already identifies a plant",
                    evidence=(CHEKHOV_GUN, event_id),
                )
            if (
                obligation.discharged_by == event_id
                and obligation.element != element
            ):
                return Verification(
                    Verdict.REFUSED,
                    f"event id {event_id!r} already discharges a different element",
                    evidence=(CHEKHOV_GUN, event_id),
                )
        for index, obligation in enumerate(state.obligations):
            if obligation.element != element:
                continue
            if obligation.discharged_by is not None:
                if obligation.discharged_by != event_id:
                    return Verification(
                        Verdict.REFUSED,
                        f"element {element!r} was already discharged by event "
                        f"{obligation.discharged_by!r}; a fresh id is not an "
                        "idempotent retry",
                        evidence=(CHEKHOV_GUN, obligation.discharged_by),
                    )
                return Verification(
                    Verdict.VERIFIED,
                    f"element {element!r} was already discharged",
                    state,
                    (CHEKHOV_GUN, obligation.discharged_by),
                )
            discharged = replace(obligation, discharged_by=event_id)
            obligations = (
                state.obligations[:index]
                + (discharged,)
                + state.obligations[index + 1 :]
            )
            return Verification(
                Verdict.VERIFIED,
                f"discharging {element!r} satisfies its planted obligation",
                replace(state, obligations=obligations),
                (CHEKHOV_GUN, obligation.planted_by, event_id),
            )
        if NO_DEUS in state.spec.governed_by:
            return Verification(
                Verdict.REFUTED,
                f"unheralded discharge of {element!r}: no earlier event "
                "planted it, and this frame adopts the no-deus-ex-machina "
                "law (strict event-order reading)",
                evidence=(NO_DEUS,),
            )
        return Verification(
            Verdict.UNKNOWN,
            f"no planted obligation grounds discharge of {element!r}, and "
            "this frame does not adopt "
            "narrative.constraint.no_deus_ex_machina, so the unheralded "
            "discharge is unadjudicated rather than refuted",
            evidence=(CHEKHOV_GUN, NO_DEUS),
        )

    def close_frame(
        self, state: FrameState
    ) -> FrameCloseResult:
        if state.closed:
            raise ValueError(
                f"frame {state.spec.frame!r} is already closed; closing "
                "twice would re-emit its demotions"
            )
        if state.spec.owner is not None:
            return FrameCloseResult(
                Verdict.REFUSED,
                "owned belief frames persist and update; they do not demote on exit",
                state,
                evidence=(state.spec.owner, state.spec.frame),
            )
        outstanding = tuple(
            obligation for obligation in state.obligations if obligation.outstanding
        )
        if outstanding:
            elements = ", ".join(repr(item.element) for item in outstanding)
            return FrameCloseResult(
                Verdict.REFUSED,
                f"frame has outstanding Chekhov obligations: {elements}",
                state,
                evidence=(CHEKHOV_GUN,)
                + tuple(item.planted_by for item in outstanding),
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
        return FrameCloseResult(
            Verdict.VERIFIED,
            "frame closed with every temporal obligation discharged",
            replace(state, closed=True),
            demoted,
            (state.spec.frame,),
        )


class FrameAssertionVerifier:
    """Adapt FrameExecutor to the generic controller contract.

    Accepts GEN(assert_fact), GEN(plant), and GEN(discharge). Direct RETRIEVE is
    REFUSED at this adapter boundary: either the frame forbids it
    (`retrieval: frame_local`) or the caller must use retrieval.RetrievalVerifier,
    which layers pointable context over this verifier without duplicating GEN
    semantics. The two refusals carry distinct reasons in the trace.
    """

    name = "frame-local-ladder"

    def __init__(self, executor: FrameExecutor):
        self.executor = executor

    def state_key(self, state: FrameState) -> str:
        return (
            f"{state.spec.frame}|closed={state.closed}|"
            f"{[claim_id for claim_id, _ in state.asserted]!r}|"
            f"{state.obligations!r}"
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
                "RETRIEVE requires retrieval.RetrievalVerifier at this boundary",
                evidence=(self.name,),
            )
        if action.kind is not ActionKind.GEN:
            return Verification(
                Verdict.REFUSED,
                "frame ladder accepts only GEN transitions",
                evidence=(self.name,),
            )
        arguments = dict(action.arguments)
        if action.name in {"plant", "discharge"}:
            missing = [
                key for key in ("event_id", "element") if not arguments.get(key)
            ]
            if missing:
                return Verification(
                    Verdict.REFUSED,
                    f"{action.name} has missing or empty arguments: {missing}",
                    evidence=(self.name,),
                )
            transition = getattr(self.executor, action.name)
            return transition(
                state, arguments["event_id"], arguments["element"]
            )
        if action.name != "assert_fact":
            return Verification(
                Verdict.REFUSED,
                f"unknown frame transition {action.name!r}",
                evidence=(self.name,),
            )
        required = ("claim_id", "subject", "predicate", "value")
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
