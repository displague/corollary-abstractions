#!/usr/bin/env python3
"""Runtime frame executor: the epistemic ladder evaluated inside a scope.

docs/DESIGN-frames-and-retrieval.md section 1, made executable. A frame is
opened from declarations (its local VERIFIED tier), assertions inside it are
adjudicated against those declarations plus the corpus's world truths minus
the frame's `suspends` list, and on exit every frame-local truth demotes to
the frame's `on_exit` epistemic status. Frame truths never leak.

Adjudication order and semantics (each is a deliberate design decision):

-1. Ownership splits the semantics in two (post-merge review of 4cc2194):
   FICTION (unowned) rewrites the world, so it must suspend what it
   overwrites -- the boundary rule and world-grounding below apply to it.
   BELIEF (owned) diverges from the world without touching it: an owned
   frame adjudicates ONLY its local truths (declarations + witnessed
   events + accepted assertions), world truths never ground or refute a
   belief unwitnessed (no telepathy), world-false initial beliefs are
   legitimate declarations needing no suspension, and the
   suspension-invention channel does not exist for it (belief acquires
   content by witnessing, fiction by inventing). Rules 0 and 3-4 below
   therefore apply only to unowned frames.
   Belief frames NEST: an owned frame may embed a model of another agent
   (`open_nested`), whose truths are the parent owner's beliefs about
   the modeled agent's beliefs. Tiers are isolated by construction --
   ancestors and descendants adjudicate only their own local truths --
   and models update under MUTUAL visibility: every owner on the path
   must be in the event's witnessed_by, so a parent that witnesses alone
   knowingly diverges from its model of the other. Fiction does not nest
   (no owner to attribute a model to; suspension inheritance undesigned)
   and self-models are refused (an owner's own frame holds its beliefs).
   `nested` navigates read-only; `with_nested` grafts a mutated model back
   at an explicit owner path and `route` runs a frame-LOCAL transition
   (assert/plant/discharge) inside a model and returns the ROOT state, so a
   rejected branch still cannot mutate accepted state. `observe_event` is
   deliberately NOT routable: events reach a model through its parent's
   delivery, and the graft's subset check refuses a model whose history its
   holder never saw. Grafting is checked, not trusted: it replaces an
   existing model (creation stays with `open_nested` and its refusals),
   keeps the child-owner key equal to the model's declared owner, refuses
   to graft into a closed frame, and re-checks the subset invariant that
   `observe_event`'s loud RuntimeError assumes -- a model's event history
   is a subset of its parent's, so the only way to break it remains
   deliberate dataclass surgery.
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
from typing import Callable, Mapping

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
    # Nested belief models, keyed by the modeled agent's owner id: Sally's
    # frame may embed her model of Anne. A child's truths are the PARENT
    # OWNER'S beliefs about the child owner's beliefs -- they live only
    # here, never in local_truths, so ancestor and descendant tiers cannot
    # ground or refute each other by construction.
    children: tuple[tuple[str, "FrameState"], ...] = ()

    def child(self, owner: str) -> "FrameState | None":
        for child_owner, child_state in self.children:
            if child_owner == owner:
                return child_state
        return None

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
            # OWNED frames are exempt on principle, not oversight: fiction
            # REWRITES the world and must suspend what it overwrites; a
            # belief frame DIVERGES from the world without touching it, so
            # a world-false initial belief is legitimate content (the same
            # rule that keeps world truths from grounding belief checks).
            if spec.owner is not None:
                continue
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

    def open_nested(
        self, parent: FrameState, child_spec: FrameSpec
    ) -> FrameState:
        """Embed a belief model of another agent inside an owned frame.

        Belief nesting only: fiction has no owner to attribute a model to,
        and nested fiction's suspension-inheritance rules are undesigned --
        both refuse rather than guess. Self-models are refused too: an
        owner's model of itself is just its frame.
        """
        if parent.closed:
            raise ValueError("cannot nest inside a closed frame")
        if parent.spec.owner is None:
            raise ValueError(
                "nested frames require an OWNED parent: nested fiction's "
                "suspension-inheritance rules are undesigned (leak controls "
                "exist for belief nesting only)"
            )
        if child_spec.owner is None:
            raise ValueError(
                "a nested frame models an agent's beliefs and must be owned"
            )
        if child_spec.owner == parent.spec.owner:
            raise ValueError(
                f"owner {parent.spec.owner!r} cannot nest a model of "
                "itself; its own frame already holds its beliefs"
            )
        if parent.child(child_spec.owner) is not None:
            raise ValueError(
                f"parent already embeds a model of {child_spec.owner!r}"
            )
        # Models start blank: an event delivered BEFORE this model was
        # opened is not back-filled, and an idempotent retry of it after
        # opening is a global no-op (review note 9, deliberate).
        child_state = self.open_frame(child_spec)
        return replace(
            parent,
            children=parent.children + ((child_spec.owner, child_state),),
        )

    def nested(self, state: FrameState, owner_path: tuple[str, ...]) -> FrameState:
        """Navigate to the embedded model at owner_path (may be empty)."""
        current = state
        for owner in owner_path:
            child_state = current.child(owner)
            if child_state is None:
                raise KeyError(
                    f"no embedded model of {owner!r} at this level"
                )
            current = child_state
        return current

    def with_nested(
        self,
        parent: FrameState,
        owner_path: tuple[str, ...],
        new_child: FrameState,
    ) -> FrameState:
        """Replace the model at owner_path, immutably, invariants intact.

        The read-only counterpart of `nested`: mutators applied to a
        navigated model return a DETACHED state with no path home, so
        without this every deep consumer reached for
        `replace(parent, children=...)` surgery -- which silently accepts
        any tree at all (nested-frames review, note 8).

        This is a REPLACEMENT, not an insertion: creation stays with
        `open_nested`, which owns the refusals that make a model
        well-formed (owned parent, owned child, no self-model, no
        duplicate key). A graft therefore refuses a path that does not
        already exist, rather than quietly inventing a model at the tip
        and skipping those gates.

        Every structural invariant `observe_event` relies on is re-checked
        against the grafted subtree, not assumed:
        the child-owner key equals the model's declared owner (the key is
        how delivery matches an owner against witnessed_by -- a mismatched
        key would route events by one name and adjudicate them under
        another); no frame on the path is closed (the same reason
        `open_nested` refuses a closed parent); and the model's event
        history stays a SUBSET of its holder's. That last one is the
        premise of the loud RuntimeError inside nested delivery: with it
        checked here, breaking it requires deliberate dataclass surgery
        rather than an ordinary graft, which is exactly what the control
        test now documents itself as doing.
        """

        if not owner_path:
            raise ValueError(
                "with_nested needs a non-empty owner path: an empty path "
                "names the root frame, and replacing a frame with itself "
                "is not a graft"
            )
        if parent.closed:
            raise ValueError("cannot graft into a closed frame")
        holder = parent
        for owner in owner_path[:-1]:
            child_state = holder.child(owner)
            if child_state is None:
                raise KeyError(f"no embedded model of {owner!r} at this level")
            if child_state.closed:
                raise ValueError("cannot graft into a closed frame")
            holder = child_state
        target = owner_path[-1]
        if holder.child(target) is None:
            raise KeyError(
                f"no embedded model of {target!r} at this level; grafting "
                "replaces an existing model and open_nested creates one"
            )
        self._check_model(holder, target, new_child)
        grafted = replace(
            holder,
            children=tuple(
                (owner, new_child if owner == target else state)
                for owner, state in holder.children
            ),
        )
        # Rebuild the spine outwards: every ancestor is a frozen dataclass,
        # so the graft is a fresh chain of parents, never an in-place edit.
        for depth in range(len(owner_path) - 1, 0, -1):
            ancestor = self.nested(parent, owner_path[:depth - 1])
            owner = owner_path[depth - 1]
            grafted = replace(
                ancestor,
                children=tuple(
                    (key, grafted if key == owner else state)
                    for key, state in ancestor.children
                ),
            )
        return grafted

    def route(
        self,
        state: FrameState,
        owner_path: tuple[str, ...],
        transition: Callable[[FrameState], Verification[FrameState]],
    ) -> Verification[FrameState]:
        """Run a frame-local transition inside a model and graft it back.

        `transition` receives the model at owner_path and returns the
        executor's own Verification; on an ACCEPTING verdict the returned
        next_state is the ROOT frame with the mutated model grafted in, so
        the caller keeps holding the root and never a detached child.

        A rejected branch is passed through untouched. That gate reads the
        VERDICT, not the presence of a state: `transition` is an arbitrary
        caller-supplied callable, so a rejecting verdict that carries a
        state would otherwise be grafted into the root and handed back --
        the "rejected branches cannot mutate accepted state" invariant
        enforced by the controller through Verification.validate(), which
        is not in this loop. Checked here rather than assumed, because a
        convention held by care is not an invariant (post-commit review of
        dd1cdd2, finding H1).

        Frame-LOCAL only. `observe_event` is deliberately not routable:
        events reach a model through its parent's delivery, so routing one
        directly would give the model a history its holder never saw, and
        the graft's subset check refuses it. That refusal is the design,
        not a gap.

        An empty path routes to the root itself (the degenerate identity
        route), which keeps callers from special-casing depth zero.

        A closed frame on the path REFUSES rather than raising: "closed"
        is a verdict everywhere else in this executor (close_frame,
        observe_event, every transition), and a caller routing into a
        closed ancestor deserves the same disposition it would get for
        routing into the closed frame directly. A path that does not
        exist still raises, and is checked FIRST at each level, so a
        nonexistent path is a KeyError even when the root is closed
        (an unroutable path is a caller mistake either way; reporting it
        as "closed" would hide the typo). `with_nested` raises for the
        same closed frame because it is the structural primitive -- route
        is the verdict-returning door, and the two layers answer in their
        own currencies.
        """

        current = state
        for depth, owner in enumerate(owner_path):
            child_state = current.child(owner)
            if child_state is None:
                raise KeyError(f"no embedded model of {owner!r} at this level")
            if current.closed:
                return Verification(
                    Verdict.REFUSED,
                    "frame is closed; it accepts no routed transitions",
                    evidence=(current.spec.frame,) + owner_path[:depth],
                )
            current = child_state
        result = transition(current)
        if not owner_path or not result.verdict.accepts:
            return result
        if result.next_state is None:
            # A malformed accepting verdict; hand it back so the
            # controller's Verification.validate() names the offender
            # instead of an AttributeError inside the graft.
            return result
        return Verification(
            result.verdict,
            result.reason,
            self.with_nested(state, owner_path, result.next_state),
            result.evidence,
        )

    def _check_model(
        self, holder: FrameState, child_owner: str, child: FrameState
    ) -> None:
        """Assert one holder/model pair is well-formed, then recurse."""

        if holder.spec.owner is None:
            raise ValueError(
                "nested frames require an OWNED parent: nested fiction's "
                "suspension-inheritance rules are undesigned (leak controls "
                "exist for belief nesting only)"
            )
        if child.spec.owner != child_owner:
            raise ValueError(
                f"graft would break the child-owner key: model keyed "
                f"{child_owner!r} declares owner {child.spec.owner!r}"
            )
        if child.spec.owner == holder.spec.owner:
            raise ValueError(
                f"owner {holder.spec.owner!r} cannot nest a model of "
                "itself; its own frame already holds its beliefs"
            )
        if child.closed:
            # Unreachable today (close_frame REFUSES owned frames), but
            # observe_event's FIRST guard is `closed` -> REFUSED, which
            # the nested-delivery RuntimeError would then convert into a
            # loud failure. "Every invariant re-checked" has to mean it.
            raise ValueError(
                f"graft would embed a CLOSED model of {child_owner!r}; "
                "delivery to it would refuse and break nested recursion"
            )
        processed = set(holder.processed_event_ids)
        unknown = [
            event_id
            for event_id in child.processed_event_ids
            if event_id not in processed
        ]
        if unknown:
            raise ValueError(
                f"graft would break the subset invariant: model "
                f"{child_owner!r} processed events {unknown!r} its holder "
                "never saw; events reach a model only through its parent"
            )
        witnessed = {event.event_id: event for event in holder.observed_events}
        for event in child.observed_events:
            if witnessed.get(event.event_id) != event:
                raise ValueError(
                    f"graft would break the subset invariant: model "
                    f"{child_owner!r} observed {event.event_id!r} with "
                    "visibility or effects its holder did not observe"
                )
        seen: set[str] = set()
        for owner, grandchild in child.children:
            if owner in seen:
                raise ValueError(f"model keys must be unique; {owner!r} repeats")
            seen.add(owner)
            self._check_model(child, owner, grandchild)

    def observe_event(
        self, state: FrameState, event: FrameEvent
    ) -> Verification[FrameState]:
        """Update an owned belief frame iff its owner witnessed the event.

        Nested models update under MUTUAL visibility: the parent's model
        of a child agent updates only when the parent witnessed the event
        AND the child agent is also in its witnessed_by set -- the parent
        may attribute the observation to the child. An event the parent
        witnessed alone updates the parent and leaves its models unchanged
        (the parent now knowingly diverges from its model of the other).
        Delivery recurses, so grandchild models need every owner on the
        path to have witnessed.
        """

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
        children = state.children
        if children:
            updated_children = []
            for child_owner, child_state in children:
                if child_owner in event.witnessed_by:
                    delivered = self.observe_event(child_state, event)
                    if delivered.next_state is None:
                        # Unreachable through real flows: a child's event
                        # history is a subset of its parent's, so the
                        # parent's guards fire first. If it fires, the
                        # subset invariant is broken and continuing would
                        # silently fork parent and model histories.
                        raise RuntimeError(
                            "nested delivery refused; the child's event "
                            "subset invariant is broken: "
                            + delivered.reason
                        )
                    updated_children.append(
                        (child_owner, delivered.next_state)
                    )
                else:
                    updated_children.append((child_owner, child_state))
            children = tuple(updated_children)
        next_state = replace(
            state,
            asserted=tuple(asserted),
            observed_events=state.observed_events + (event,),
            processed_event_ids=state.processed_event_ids + (event.event_id,),
            superseded_declarations=tuple(sorted(superseded)),
            children=children,
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
        """Return the single positive value held for a functional predicate.

        Refuses to guess: if the frame simultaneously holds more than one
        distinct positive value for (subject, predicate) -- which can only
        happen when the predicate was never marked functional in any
        observed event -- there is no "the" belief, and silently answering
        the latest one would invent a preference the frame does not hold
        (post-merge review of 4cc2194, finding 4).
        """

        values: list[str] = []
        for _, literal in reversed(state.local_truths):
            if (
                literal.subject == subject
                and literal.predicate == predicate
                and literal.polarity
                and literal.value not in values
            ):
                values.append(literal.value)
        if len(values) > 1:
            raise ValueError(
                f"belief_value({subject!r}, {predicate!r}) is ambiguous: the "
                f"frame holds {len(values)} distinct positive values "
                f"{values!r}; the predicate was not treated as functional"
            )
        return values[0] if values else None

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

        if spec.owner is not None:
            # Owned frames are BELIEF states and adjudicate only local
            # truths: world facts the owner never witnessed must not ground
            # or refute the owner's beliefs (the telepathy the visibility
            # design exists to prevent -- post-merge review of 4cc2194, F1).
            # Divergence from the world is the phenomenon, not an error.
            return Adjudication(
                Verdict.UNKNOWN,
                f"owner {spec.owner!r} holds no belief about this; world "
                "truths do not reach a belief frame unwitnessed",
                (spec.frame, spec.owner),
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
