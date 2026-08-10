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
from frames import (
    CHEKHOV_GUN,
    FRAME_CONSISTENCY,
    NO_DEUS,
    FrameExecutor,
    FrameSpec,
    FrameState,
    Literal,
)


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


class MentionSyntaxError(ValueError):
    """A binding the adapter cannot turn into a record at all (-> REFUSED).

    Unparseable syntax AND spans that fall outside the text they annotate:
    both are structurally impossible records, not story claims the frame
    weighed and could not ground. An offset past the end of a beat is a
    malformed argument in the same sense a negative offset is -- the
    record cannot be constructed, so there is nothing to adjudicate.
    (Post-commit review of dd1cdd2, finding M3: the class docstring used
    to say "cannot parse", which the out-of-range case contradicted. The
    taxonomy is stated correctly here rather than papered over at the
    call site.)
    """


class MentionBindingError(ValueError):
    """A constructible binding the rendered text does not support.

    -> UNKNOWN: the record is well-formed and the frame simply cannot
    ground the claim it makes (undeclared element, or a span that is not
    a declared surface form of the element it names).
    """


@dataclass(frozen=True)
class NarrativeElement:
    """A story element id and the exact rendered forms that name it.

    Element identity is an ID, not prose. `surfaces` is the frame's
    declared lexicalization of that id -- the only spans a beat may bind
    to it. Matching is EXACT, deliberately: a declared surface form is an
    authoring decision (including its casing), never a fuzzy match the
    adapter improvises over whatever prose the oracle happened to write.

    Exact is necessary but was not sufficient. A bound span must also sit
    on WORD BOUNDARIES of the rendered text: without that, the declared
    surface "key" matched inside "donkey" and "monkey", and a story
    containing no key at all planted, discharged, and closed a key
    obligation -- an author could label a word FRAGMENT with any element
    id whose surface it happened to contain. Independent review found
    this after the first commit (dd1cdd2, finding H2); the old
    substring check had the identical hole, so this is the first version
    where "the element is visible here" is actually true.
    """

    element: str
    surfaces: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.element.strip():
            raise ValueError("a narrative element needs a non-empty id")
        if not self.surfaces:
            raise ValueError(
                f"element {self.element!r} declares no surface form; an "
                "element with no lexicalization can never be named visibly"
            )
        if any(not surface.strip() for surface in self.surfaces):
            raise ValueError("surface forms must be non-empty")


@dataclass(frozen=True)
class ElementMention:
    """A typed binding: this span of a beat's text names this element id."""

    element: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not self.element.strip():
            raise ValueError("a mention must name an element")
        if self.start < 0 or self.end <= self.start:
            raise ValueError(
                f"mention span [{self.start}, {self.end}) must be non-empty "
                "and start at a non-negative offset"
            )

    def shifted(self, offset: int) -> "ElementMention":
        return replace(self, start=self.start + offset, end=self.end + offset)

    def span_of(self, text: str) -> str:
        return text[self.start : self.end]


def _is_canonical_offset(part: str) -> bool:
    """One offset, one spelling: ASCII digits, no signs, no leading zeros.

    `str.isdigit()` alone is not enough in either direction -- it accepts
    superscripts and non-ASCII numerals that `int()` then rejects, and it
    accepts '0002' as a second spelling of 2.
    """

    if not part.isascii() or not part.isdigit():
        return False
    return part == "0" or not part.startswith("0")


def _is_word_char(character: str) -> bool:
    return character.isalnum() or character == "_"


def _on_word_boundaries(text: str, start: int, end: int) -> bool:
    """True when [start, end) is not spliced into a surrounding word.

    \\b semantics, computed not guessed: a boundary is required only where
    the span's own edge is a word character, so a declared surface may
    still begin or end with punctuation. This is what stops "key" from
    binding inside "donkey" -- the anti-vacuity property the exact-match
    rule alone did not deliver (post-commit review of dd1cdd2, H2).
    """

    if _is_word_char(text[start]) and start > 0 and _is_word_char(text[start - 1]):
        return False
    if (
        _is_word_char(text[end - 1])
        and end < len(text)
        and _is_word_char(text[end])
    ):
        return False
    return True


def parse_mention_bindings(spec: str) -> tuple[ElementMention, ...]:
    """Parse `element@start:end` records, `;`-separated. Closed form only.

    Offsets must be plain decimal digits. `int()` alone would accept
    '+2', ' 2 ', '0002' and '1_0' as spellings of the same offset, and a
    binding is an audit record: one offset, one spelling (post-commit
    review of dd1cdd2, finding L1).
    """

    mentions: list[ElementMention] = []
    for item in spec.split(";"):
        item = item.strip()
        if not item:
            continue
        element, at, span = item.rpartition("@")
        if not at or not element:
            raise MentionSyntaxError(
                f"binding {item!r} is not element@start:end"
            )
        start, colon, end = span.partition(":")
        if not colon:
            raise MentionSyntaxError(
                f"binding {item!r} has no start:end span"
            )
        if not all(_is_canonical_offset(part) for part in (start, end)):
            raise MentionSyntaxError(
                f"binding {item!r} needs plain decimal offsets"
            )
        offsets = (int(start), int(end))
        try:
            mentions.append(ElementMention(element, *offsets))
        except ValueError as error:
            raise MentionSyntaxError(str(error)) from error
    return tuple(mentions)


@dataclass(frozen=True)
class StoryBeat:
    """One rendered beat plus the typed element mentions inside its text.

    Mentions are produced when the beat is created and are anchored to
    offsets in THIS beat's rendered text -- so "the element is visible in
    this beat" is a structural property of the record, not a later search
    over prose.
    """

    role: str
    text: str
    mentions: tuple[ElementMention, ...] = ()

    def __post_init__(self) -> None:
        for mention in self.mentions:
            if mention.end > len(self.text):
                raise ValueError(
                    f"mention span [{mention.start}, {mention.end}) falls "
                    f"outside the {self.role!r} beat it annotates"
                )

    def names(self, element: str) -> bool:
        return any(mention.element == element for mention in self.mentions)


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
        frame="runtime.frames.golden_chicken",
        title="The golden chicken",
        declarations=(
            ("agent", Literal("story", "agent", "the golden chicken")),
            ("golden", Literal("the golden chicken", "trait", "golden")),
            (
                "no_silver",
                Literal("the golden chicken", "trait", "silver", polarity=False),
            ),
        ),
        # The story adopts both narrative constraint laws: Chekhov's gun is
        # enforced through the obligation ledger, and adopting the no-deus
        # converse makes an unheralded discharge REFUTED rather than
        # unadjudicated -- a coincidence-driven genre would simply omit it.
        governed_by=(FRAME_CONSISTENCY, CHEKHOV_GUN, NO_DEUS),
    )


# The story's declared elements. `key` is registered but never planted: it
# is the subject of the no-deus probe, so the refutation there rests on the
# ledger (nothing planted it) rather than on an unknown element id.
GOLDEN_CHICKEN_ELEMENTS = (
    NarrativeElement("fallen feather", ("fallen feather",)),
    NarrativeElement("key", ("key",)),
)


class StoryFrameVerifier:
    """Three-beat story grammar over the runtime frame executor.

    Beat ordering and desire preservation are the story grammar's own laws
    (narrative.structure.*); trait consistency and planted/discharged temporal
    obligations are delegated to the frame executor. One executor, two
    costumes.

    Element references are BOUND, not grepped (v0.7 item 7). A beat-creating
    transition may carry `binds`: `element@start:end` records naming spans of
    the text it is about to render. The adapter validates each record against
    the frame's declared elements -- the span must be an exact declared
    surface form of the element id it claims -- and stores it on the beat.
    plant and discharge then consult those typed records instead of running
    case-insensitive substring searches over oracle-authored prose (the
    BACKLOG's "Temporal event grounding remains demo-specific").

    The anti-vacuity controls the substring checks enforced are kept, and two
    of them get stronger:
      * A plant must still ALTER A VISIBLE BEAT -- the mention is appended to
        the rendered setup beat, and its records are rebased onto the amended
        text, so a ledger-only plant is impossible (the hidden-ledger
        regression the v0.5 review warned about).
      * A discharge must still be EVIDENCED BY THE RESOLUTION BEAT -- it now
        requires a mention record for that element on the resolution beat
        itself. "The evidence is really in the resolution text" stops being a
        substring check and becomes structural: a record's span is validated
        against the beat that carries it and cannot outlive it.
      * An unrelated mention still fails -- naming some OTHER element does not
        discharge this one, now by element identity rather than by spelling.
      * Element ids are decoupled from prose: an id never has to appear in the
        rendered text, and a span binds only if the frame declared that exact
        surface form for that id.

    The lexicon is the ADAPTER's, not the FrameSpec's: rendered surface forms
    are narrative-presentation semantics, and item 7's whole point is that
    they must not leak into the generic frame layer.
    """

    name = "narrative-three-beat-frame"

    def __init__(
        self,
        executor: FrameExecutor | None = None,
        spec: FrameSpec | None = None,
        elements: tuple[NarrativeElement, ...] | None = None,
    ):
        self.executor = executor or FrameExecutor()
        self.spec = spec or golden_chicken_frame_spec()
        self.elements = (
            GOLDEN_CHICKEN_ELEMENTS if elements is None else elements
        )

    def surfaces(self, element: str) -> tuple[str, ...] | None:
        for declared in self.elements:
            if declared.element == element:
                return declared.surfaces
        return None

    def bind_mentions(
        self, text: str, spec: str | None
    ) -> tuple[ElementMention, ...]:
        """Turn a `binds` argument into typed records against `text`.

        Raises MentionSyntaxError for a record that cannot be constructed
        at all -- unparseable, or a span outside `text` -- and
        MentionBindingError when the record is well formed but the
        rendered text does not support the claim it makes.
        """

        if not spec:
            return ()
        mentions = parse_mention_bindings(spec)
        for mention in mentions:
            if mention.end > len(text):
                raise MentionSyntaxError(
                    f"span [{mention.start}, {mention.end}) falls outside "
                    f"the {len(text)}-character text it binds"
                )
            surfaces = self.surfaces(mention.element)
            if surfaces is None:
                raise MentionBindingError(
                    f"the frame declares no narrative element "
                    f"{mention.element!r}; a binding may not invent one"
                )
            if mention.span_of(text) not in surfaces:
                raise MentionBindingError(
                    f"span {mention.span_of(text)!r} is not a declared "
                    f"surface form of element {mention.element!r}"
                )
            if not _on_word_boundaries(text, mention.start, mention.end):
                raise MentionBindingError(
                    f"span {mention.span_of(text)!r} is a word FRAGMENT "
                    f"here, not a mention of {mention.element!r}: the "
                    "rendered text continues the word on at least one side"
                )
        return mentions

    def initial_state(self) -> StoryState:
        return StoryState(frame_state=self.executor.open_frame(self.spec))

    def state_key(self, state: StoryState) -> str:
        return repr(state)

    def evaluate(
        self, state: StoryState, action: Action
    ) -> Verification[StoryState]:
        if state.frame_state.closed:
            return Verification(
                Verdict.REFUSED,
                "story frame is closed; it accepts no further transitions",
                evidence=(state.frame_state.spec.frame,),
            )
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

        if action.name in {"plant", "discharge"}:
            missing = [
                key for key in ("event_id", "element") if not args.get(key)
            ]
            if missing:
                return Verification(
                    Verdict.REFUSED,
                    f"{action.name} has missing or empty arguments: {missing}",
                    evidence=(self.name,),
                )
            mentions: tuple[ElementMention, ...] = ()
            if action.name == "plant":
                mention = args.get("mention")
                if tuple(beat.role for beat in state.beats) != ("setup",):
                    return self._order_refutation(
                        "a planted element must appear during the setup beat"
                    )
                if not mention:
                    return Verification(
                        Verdict.UNKNOWN,
                        "plant has no rendered mention in the story",
                        evidence=("narrative.constraint.chekhov_gun",),
                    )
                # Bindings are relative to the mention fragment; they are
                # rebased onto the amended beat below, once the fragment
                # has actually been rendered into the visible story.
                mentions, failure = self._bind_or_fail(
                    mention, args.get("binds"), CHEKHOV_GUN
                )
                if failure is not None:
                    return failure
                if not any(
                    record.element == args["element"] for record in mentions
                ):
                    return Verification(
                        Verdict.UNKNOWN,
                        "plant mention does not name the planted element",
                        evidence=("narrative.constraint.chekhov_gun",),
                    )
            else:
                if not state.beats or state.beats[-1].role != "resolution":
                    return self._order_refutation(
                        "a discharge must be evidenced by the resolution beat"
                    )
                resolution = state.beats[-1]
                if not resolution.mentions:
                    return Verification(
                        Verdict.UNKNOWN,
                        "the resolution beat binds no narrative element, so "
                        "no discharge is evidenced in the story",
                        evidence=("narrative.constraint.chekhov_gun",),
                    )
                if not resolution.names(args["element"]):
                    return Verification(
                        Verdict.UNKNOWN,
                        "the resolution beat does not name the discharged "
                        "element",
                        evidence=("narrative.constraint.chekhov_gun",),
                    )
            already_planted = action.name == "plant" and any(
                obligation.element == args["element"]
                for obligation in state.frame_state.obligations
            )
            transition = getattr(self.executor, action.name)
            result = transition(
                state.frame_state, args["event_id"], args["element"]
            )
            if not result.verdict.accepts:
                return Verification(
                    result.verdict,
                    result.reason,
                    evidence=result.evidence,
                )
            next_state = replace(state, frame_state=result.next_state)
            if action.name == "plant" and not already_planted:
                # The plant alters a VISIBLE beat, and its records travel
                # with the text: rebasing by the appended offset keeps every
                # span pointing at the same words it was validated against.
                previous = state.beats[-1]
                offset = len(previous.text) + 1
                amended = replace(
                    previous,
                    text=f"{previous.text} {mention}",
                    mentions=previous.mentions
                    + tuple(record.shifted(offset) for record in mentions),
                )
                next_state = replace(
                    next_state, beats=state.beats[:-1] + (amended,)
                )
            return Verification(
                result.verdict,
                result.reason,
                next_state,
                result.evidence,
            )

        if action.name == "introduce":
            if state.beats:
                return self._order_refutation("setup must be the first beat")
            desire = args.get("desire")
            if not desire:
                return Verification(Verdict.UNKNOWN, "setup has an unbound desire")
            text = f"{state.agent.capitalize()} wanted {desire}."
            mentions, failure = self._bind_or_fail(
                text, args.get("binds"), "narrative.structure.setup_introduction"
            )
            if failure is not None:
                return failure
            beat = StoryBeat("setup", text, mentions)
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
            text = f"But {obstacle} stood in the way."
            mentions, failure = self._bind_or_fail(
                text,
                args.get("binds"),
                "narrative.structure.complication_obstruction",
            )
            if failure is not None:
                return failure
            beat = StoryBeat("complication", text, mentions)
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
            mentions, failure = self._bind_or_fail(
                outcome,
                args.get("binds"),
                "narrative.structure.resolution_outcome",
            )
            if failure is not None:
                return failure
            beat = StoryBeat("resolution", outcome, mentions)
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

    def _bind_or_fail(
        self,
        text: str,
        spec: str | None,
        law: str,
    ) -> tuple[tuple[ElementMention, ...], Verification[StoryState] | None]:
        """Bind mentions, or hand back the verdict the failure deserves.

        An unreadable argument is REFUSED (no record can be built at all);
        a well-formed binding the rendered text does not support is
        UNKNOWN (the story cannot ground the claim).

        `law` is the statute the UNKNOWN actually rests on, supplied by
        the call site: Chekhov's gun when the binding serves a temporal
        obligation, the beat's own structure law when it does not. Citing
        chekhov_gun for a bad binding on a complication beat named a law
        the verdict did not rest on -- exactly what frames.py's evidence
        rule forbids ("never the frame's whole statute book"). Post-commit
        review of dd1cdd2, finding M4.
        """

        try:
            return self.bind_mentions(text, spec), None
        except MentionSyntaxError as error:
            return (), Verification(
                Verdict.REFUSED,
                f"element binding is unreadable: {error}",
                evidence=(self.name,),
            )
        except MentionBindingError as error:
            return (), Verification(
                Verdict.UNKNOWN,
                f"the rendered text does not support this binding: {error}",
                evidence=(law,),
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
            "plant",
            {
                **shared,
                "event_id": "fallen_feather_planted",
                "element": "fallen feather",
                "mention": "A fallen feather gleamed beside its nest.",
                # Offsets into the mention fragment above; the adapter
                # rebases them when the fragment joins the setup beat.
                "binds": "fallen feather@2:16",
            },
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
                # The resolution names two declared elements. Only the
                # feather was ever planted; 'key' is bound so the no-deus
                # probe stays a LEDGER refutation rather than an unknown id.
                "binds": "fallen feather@10:24;key@30:33",
            },
        ),
        Action.build(
            ActionKind.GEN,
            "discharge",
            {
                **shared,
                "event_id": "fallen_feather_used_as_key",
                "element": "fallen feather",
            },
        ),
    )


def story_oracle_run() -> RunResult[StoryState]:
    verifier = StoryFrameVerifier()
    return Controller[StoryState](max_steps=5).run(
        verifier.initial_state(),
        SequencePolicy(story_oracle_actions()),
        verifier,
        lambda state: (
            tuple(beat.role for beat in state.beats)
            == ("setup", "complication", "resolution")
            and bool(state.frame_state.obligations)
            and not any(
                obligation.outstanding
                for obligation in state.frame_state.obligations
            )
        ),
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

    close_result = FrameExecutor().close_frame(story.final_state.frame_state)
    _, demoted = close_result
    print("\nTEMPORAL OBLIGATIONS")
    for obligation in story.final_state.frame_state.obligations:
        print(
            f"  {obligation.element}: planted by {obligation.planted_by}; "
            f"discharged by {obligation.discharged_by}"
        )
    deus_probe = FrameExecutor().discharge(
        story.final_state.frame_state, "sudden_key", "a sudden magic key"
    )
    print("\nNO DEUS EX MACHINA (adopted by this frame)")
    print(
        f"  discharge of 'a sudden magic key' -> {deus_probe.verdict.value}"
    )
    print(f"  {deus_probe.reason}")

    print("\nON FRAME EXIT (truths demote; nothing leaks)")
    for claim in demoted:
        print(
            f"  {claim.literal.describe()} -> {claim.epistemic_status} "
            f"outside {claim.frame}"
        )
    print(
        "\nLIMIT: this demo's Lean steps are exact committed extraction "
        "replay. Separate PyPantograph paths now compare capability-blind "
        "search with a learned eight-schema tactic ranker; this demo invokes "
        "neither, and learned five-action choice remains unbuilt. The frame "
        "executor "
        "checks declarations, denials, suspensions, finite Chekhov-style "
        "obligations at frame close, and -- where a frame adopts the "
        "no-deus law -- refutes unheralded discharges under the strict "
        "event-order reading; this is not general LTL model checking."
    )
    return 0 if lean.solved and story.solved else 1


if __name__ == "__main__":
    raise SystemExit(main())
