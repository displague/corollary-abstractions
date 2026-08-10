#!/usr/bin/env python3
"""Open-prose authoring of the golden-chicken conversation (harness Phase 6).

This is the v0.8 item-1 RELEASE-GATE surface: unrestricted prose authoring of
the accepted golden-chicken story plus an owner's signed egg-color binding,
"constrained to point into accepted content" (``docs/DESIGN-interactive-harness``
§9 Phase 6; ``docs/ROADMAP-v0.8.md`` item 1). It is a *different* problem from
:mod:`request_grammar` (Phase 2): that module *fills* an already-open slot from
a closed table; this one *authors* new surface over already-accepted facts. The
distinction the roadmap draws is load-bearing and kept here: the pointer may
vary word choice across renders but may never change, add, or drop an accepted
fact.

The **accepted facts** are exactly the story's beats (projected from the
oracle-accepted :class:`oracle_controller_demo.StoryState`) and the owner's
signed egg-color binding (from the durable :mod:`conversation` key ring).
Nothing is invented and nothing is dropped.

The **moved-fact control is a CLOSURE check, not a presence check.** The
constrained-pointer architecture makes closure tractable *by construction*: the
pointer emits only from per-fact surface banks and the exact-template arm from
whole fixed templates, so a faithful render must TILE completely into approved
surface segments — each segment an approved variant of specific accepted
fact(s) — with every accepted fact covered and NO segment outside the approved
set. Under that check an added premise, a negated fact, a right-value/wrong-owner
misattribution, and a dropped beat are all caught: the first three introduce a
segment that matches no approved variant, the last fails coverage. The check
does **not** trust ``rendered.provenance`` (a frozenset the renderer supplies —
self-attested, worthless against a lying renderer); it reads the surface. See
:func:`faithfulness`. This is the earlier presence-check's replacement after
independent adversarial review found four renderers it wrongly certified.

Scope, stated honestly: the control is COMPLETE for prose authored from the
approved surface algebra (both shipped arms and any renderer that composes from
the same banks/templates). A faithful paraphrase *outside* the banks would be
rejected as unapproved — that is the price of a sound closure check over a
constrained pointer, and it is the right price for a gate whose job is to prove
no accepted fact moved. Widening the approved algebra is adding bank rows, in a
diff, with tests — never loosening the closure.

Two arms, compared on the metrics the roadmap names SEPARATELY (no single
fluency scalar):

* :class:`ExactTemplateRenderer` — the "richer exact templates" arm: a small
  fixed rotation of elaborate templates over the same facts. High fidelity, low
  lexical variety.
* :class:`SurfacePointerRenderer` — the "constrained surface pointer": composes
  prose from per-slot surface banks selected DETERMINISTICALLY by a seed.

Determinism is mandatory (AGENTS.md bans ``random``/``Date.now``/unseeded
entropy — they break reproducibility): surface selection is a pure function of
``(seed, slot)`` via :func:`hashlib.sha256`, so a seed reproduces a render
byte-for-byte on any box.

Registered predictions (P-PR*), BEFORE adjudication. Upstream, the roadmap
acceptance line this satisfies reads: "the golden-chicken conversation is
authored in open prose that varies surface form while a control proves no
accepted fact moved, remains revisable across a serialize/restart, and degrades
to ASK — never to a guess." The conversation-layer P-CR1..P-CR3 (owner
isolation, supersession-with-provenance, testimony-not-asserted) are upstream in
:mod:`conversation` and are relied on, not re-litigated here.

P-PR1 (surface varies, facts do not). Across many seeds the surface pointer
    yields many DISTINCT surface strings while the extracted accepted-fact set
    is byte-identical across all of them.
    Test: ``test_surface_varies_but_facts_are_invariant``.
P-PR2 (the moved-fact control has teeth). A faithful render's fact set equals
    the accepted set AND carries every anchor; an adversary that moves a fact —
    a wrong egg color, or a deus-ex resolution that drops the planted feather —
    is CAUGHT by name (provenance mismatch and/or a missing/foreign anchor).
    Test: ``test_moved_fact_control_catches_the_adversaries``.
    CORRECTION (post-review, appended per AGENTS.md — original kept above):
    the original mechanism ("provenance mismatch and/or a missing/foreign
    anchor") was UNSOUND — a presence check that certified four fact-moving
    renderers (added premise, wrong owner, negation, dropped beat) as faithful.
    P-PR2 now stands on the CLOSURE control in :func:`faithfulness`: the render
    must tile entirely into approved surface segments covering exactly the
    accepted facts. The six adversaries (the two original + the review's four)
    are each CAUGHT; the adjudicating test now also asserts the four.
    CORRECTION 2 (post re-review, appended): the gate now also enforces ORDER —
    beat/temporal order consistent with the accepted StoryState and
    plant-before-discharge for every obligation — because order is part of the
    accepted story (the obligation ledger encodes plant->discharge). Three
    ordering adversaries (discharge-before-plant, full-reverse,
    resolution-before-complication) that closure+coverage alone certified are now
    CAUGHT with named reasons and pinned as regression tests.
P-PR3 (richer template vs pointer on lexical variety). Both arms score 1.0 on
    premise preservation, required-beat coverage, and temporal consistency, but
    the pointer's lexical variety (distinct-surface ratio, mean pairwise word
    Jaccard) STRICTLY exceeds the exact-template arm's.
    Test: ``test_two_arm_metric_comparison``.
P-PR4 (serialize/restart preserves facts; surface may differ). After
    save+restore over the durable key ring, the accepted-fact set the prose
    preserves is byte-identical to pre-restart; a re-render at a new seed
    differs in surface.
    Test: ``test_serialize_restart_preserves_facts``.
P-PR5 (unrenderable fact -> ASK, not guess). Authoring before the owner's
    binding exists (or naming a slot with no accepted fact) degrades to a
    WAITING ASK through the harness Need channel and fabricates no fact.
    Test: ``test_unrenderable_fact_degrades_to_ask``.
P-PR6 (none invented). No render, across all seeds and both arms, carries a
    content anchor outside the accepted fact set; each render's provenance
    equals the accepted set exactly.
    Test: ``test_no_render_invents_a_fact``.
    CORRECTION (post-review, appended): the original was scoped only to egg
    colors (an in-vocabulary foreign color word) and to self-attested
    provenance. "None invented" now means the CLOSURE property: no surface
    segment outside the approved set — added/negated/misattributed content of
    any kind, not only colors, is caught, and provenance is not trusted.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from harness import Need, pending_need
from oracle_controller_demo import StoryState


# --------------------------------------------------------------------------
# Accepted facts: projected from the accepted story + the owner's binding
# --------------------------------------------------------------------------

#: Function words dropped when deriving a fact's lexical anchors from its own
#: value phrase. Small and closed on purpose — anchors are the content tokens a
#: faithful surface must preserve, so a short curated stop-list beats a stemmer
#: (a stemmer is a similarity judgement, banned here for the same reason
#: ``request_grammar`` bans one).
_STOPWORDS = frozenset(
    {
        "the", "and", "for", "was", "who", "not", "did", "into", "with", "its",
        "that", "this", "from", "then", "now", "had", "has", "out", "use",
        "used", "until", "but", "yet", "once", "there", "they", "tell", "came",
        "day", "ever", "after", "beside", "near", "like", "come", "rest",
    }
)


def significant_tokens(phrase: str) -> tuple[str, ...]:
    """Content tokens of ``phrase`` (>=3 chars, not a stop-word), order-preserved.

    Derived from the phrase itself, so a fact's anchors are grounded in the
    accepted story text rather than a hand-picked constant. Deliberately not a
    stemmer or lemmatiser.
    """

    seen: list[str] = []
    for token in re.findall(r"[a-z']+", phrase.lower()):
        if len(token) >= 3 and token not in _STOPWORDS and token not in seen:
            seen.append(token)
    return tuple(seen)


@dataclass(frozen=True)
class Fact:
    """One accepted fact, its value, and the anchors a faithful surface carries.

    ``anchors`` are the content tokens that must appear (on word boundaries) in
    any faithful rendering of this fact. They are used by the premise-anchor and
    the temporal/beat *metrics*; the authoritative moved-fact gate is the
    closure check in :func:`faithfulness`, which does not depend on them. Facts
    are frozen and hashable so a fact set is a plain ``frozenset[Fact]``.
    """

    kind: str
    value: str
    anchors: tuple[str, ...]


def accepted_facts(story: StoryState, egg_color: str) -> frozenset[Fact]:
    """The accepted fact set: the story's beats plus the signed egg color.

    Every value is projected from structured state the runtime already trusts —
    the frame's declarations (affirmed trait), the oracle's agent and desire,
    the complication beat's obstacle, the temporal obligation ledger
    (planted/discharged, ONE fact per obligation so two obligations never
    collapse), the resolution beat's outcome clause — and the one user value the
    caller supplies. Anchors are derived from those values by
    :func:`significant_tokens`, so the control's ground truth is the real story.

    ``egg_color`` is a bare ``str`` and this function trusts its CALLER to have
    read it from the verifier-signed binding (e.g.
    ``verifier.binding_value(state, "egg_color")``); the signing boundary lives
    in :mod:`conversation`/:mod:`retrieval`, not here. What is genuinely fixed
    to *this* story — the golden-chicken agent, the sing-the-sunrise desire, the
    feather/coop beats — is fixed because the accepted StoryState fixes it, and
    is read from that state rather than hard-coded.
    """

    frame = story.frame_state
    agent = story.agent
    if agent is None:
        raise ValueError("accepted story has no declared agent to render")
    if story.desire is None:
        raise ValueError("accepted story has no bound desire to render")

    affirmed = None
    for _, literal in frame.spec.declarations:
        if literal.predicate == "trait" and literal.polarity:
            affirmed = literal.value
            break
    if affirmed is None:
        raise ValueError("accepted story declares no affirmed trait")

    obstacle = _complication_obstacle(story)
    outcome = _resolution_outcome(story)

    facts = {
        Fact("agent", agent, significant_tokens(agent)),
        Fact("trait", affirmed, (affirmed,)),
        Fact("desire", story.desire, significant_tokens(story.desire)),
        Fact("obstacle", obstacle, significant_tokens(obstacle)),
        Fact("outcome", outcome, significant_tokens(outcome)),
        Fact("egg_color", egg_color, (egg_color,)),
    }
    for obligation in frame.obligations:
        element = obligation.element
        facts.add(Fact("planted", element, significant_tokens(element)))
        if not obligation.outstanding:
            facts.add(
                Fact("discharged", element, significant_tokens(element))
            )
    return frozenset(facts)


def _complication_obstacle(story: StoryState) -> str:
    for beat in story.beats:
        if beat.role == "complication":
            match = re.fullmatch(r"But (.+) stood in the way\.", beat.text)
            if match:
                return match.group(1)
    return "the locked coop door"


def _resolution_outcome(story: StoryState) -> str:
    """The outcome clause of the resolution beat: from 'sang' to the end.

    The accepted resolution reads '...and sang until the sun rose'; the outcome
    fact is that fulfilment clause, read off the beat so its value/anchors track
    the real story rather than a constant.
    """

    for beat in story.beats:
        if beat.role == "resolution":
            match = re.search(r"(sang .*?)(?:\.|$)", beat.text)
            if match:
                return match.group(1).strip()
    return "sang until the sun rose"


# --------------------------------------------------------------------------
# Surface banks (the approved algebra both arms and the control share)
# --------------------------------------------------------------------------

#: Optional framing sentences. They carry NO fact; the empty lead is allowed.
LEADS: tuple[str, ...] = (
    "",
    "Here is how it went. ",
    "They say it happened like this. ",
    "The tale runs this way. ",
)
#: Verb that joins the agent to the (fixed, story-derived) desire clause.
DESIRE_VERB: tuple[str, ...] = ("wanted", "longed", "yearned", "wished", "set out")
#: Feather-plant sentences — every variant embeds the planted element verbatim.
FEATHER_SETUP: tuple[str, ...] = (
    "Nearby, a fallen feather gleamed beside its nest.",
    "Beside its nest lay a fallen feather.",
    "Close by, a fallen feather caught the light.",
    "A fallen feather rested by the nest.",
)
#: Complication sentences — obstacle plus an obstruction RELATION, never scenery.
COMPLICATION: tuple[str, ...] = (
    "But the locked coop door stood in the way.",
    "Yet the locked coop door barred the way.",
    "Trouble came: the locked coop door would not open.",
    "However, the locked coop door held fast.",
)
#: Resolution sentences — the feather-as-key discharge plus the fixed,
#: story-derived outcome clause 'sang until the sun rose'.
RESOLUTION: tuple[str, ...] = (
    "It used a fallen feather as a key, and sang until the sun rose.",
    "It turned the fallen feather into a key, and sang until the sun rose.",
    "It took the fallen feather for a key, and sang until the sun rose.",
    "With the fallen feather as a key, it went out and sang until the sun rose.",
)
#: Egg-color coda sentences — bind the color to the chicken, the accepted owner.
CODA: tuple[str, ...] = (
    "Now the golden chicken laid {color} eggs.",
    "From then on, the golden chicken's eggs came out {color}.",
    "And the golden chicken's eggs? {Color}, every one.",
    "Ever after the golden chicken laid eggs of {color}.",
)

#: The exact-template arm: whole fixed templates, five sentences each, in the
#: canonical role order (setup1, feather, complication, resolution, coda).
TEMPLATES: tuple[str, ...] = (
    "The golden chicken wanted to sing the sunrise awake. A fallen feather lay "
    "beside its nest. But the locked coop door stood in the way. It used the "
    "fallen feather as a key, and sang until the sun rose. Now the golden "
    "chicken laid {color} eggs.",
    "There was once a golden chicken who longed to sing the sunrise awake. "
    "Beside its nest a fallen feather had settled. Yet the locked coop door "
    "barred the way. Clever as it was, it turned the fallen feather into a key, "
    "and sang until the sun rose. From that day the golden chicken laid {color} "
    "eggs.",
    "They tell of a golden chicken that wished to sing the sunrise awake. A "
    "fallen feather glinted near its nest. But the locked coop door held fast. "
    "So it worked the fallen feather like a key, and sang until the sun rose. "
    "Ever after the golden chicken laid eggs of {color}.",
)

#: Role -> the accepted fact kinds a segment in that role expresses. Shared by
#: the renderers and the closure control so both read one source of truth.
_ROLE_KINDS: dict[str, frozenset[str]] = {
    "lead": frozenset(),
    "setup1": frozenset({"agent", "trait", "desire"}),
    "feather": frozenset({"planted"}),
    "complication": frozenset({"obstacle"}),
    "resolution": frozenset({"discharged", "outcome"}),
    "coda": frozenset({"egg_color"}),
}
#: The template roles in sentence order (five sentences per template).
_TEMPLATE_ROLES: tuple[str, ...] = (
    "setup1", "feather", "complication", "resolution", "coda"
)


# --------------------------------------------------------------------------
# A render: surface plus the (untrusted) provenance it declares
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rendered:
    """One authored surface plus the fact set the renderer *declares* it used.

    ``provenance`` is self-attested and the moved-fact control does NOT trust
    it; it is kept for reporting and for the P-PR6 provenance-equality assertion
    on honest renderers, never as the gate.
    """

    text: str
    provenance: frozenset[Fact]
    arm: str
    seed: int


@dataclass(frozen=True)
class ProseAsk:
    """The ONLY thing an unrenderable fact is allowed to cause: a question.

    Carries the verifier-minted prompt (through the harness :class:`Need`
    channel), never a fabricated value. Structurally distinct from
    :class:`Rendered` so a caller cannot mistake an ASK for authored prose.
    """

    slot: str
    prompt: str


def _seeded_choice(bank: tuple[str, ...], seed: int, salt: str) -> str:
    """Deterministically pick one bank entry from ``(seed, salt)`` (sha256)."""

    digest = hashlib.sha256(f"{seed}|{salt}".encode("utf-8")).digest()
    return bank[int.from_bytes(digest[:8], "big") % len(bank)]


def _fact_value(facts: frozenset[Fact], kind: str) -> str:
    for fact in facts:
        if fact.kind == kind:
            return fact.value
    raise KeyError(f"no accepted fact of kind {kind!r} to render")


def _setup1(agent: str, verb: str, desire: str) -> str:
    return f"{agent.capitalize()} {verb} {desire}."


# --------------------------------------------------------------------------
# Arm A: richer exact templates (fixed, elaborate, low variety)
# --------------------------------------------------------------------------


class ExactTemplateRenderer:
    """The "richer exact templates" comparison arm.

    A small fixed rotation of elaborate whole templates. Fidelity is total;
    lexical variety is bounded by the number of templates, which is exactly the
    property the pointer beats.
    """

    arm = "exact-template"

    def render(self, facts: frozenset[Fact], seed: int) -> Rendered:
        color = _fact_value(facts, "egg_color")
        template = TEMPLATES[seed % len(TEMPLATES)]
        return Rendered(template.format(color=color), facts, self.arm, seed)


# --------------------------------------------------------------------------
# Arm B: constrained surface pointer (varies words, never facts)
# --------------------------------------------------------------------------


class SurfacePointerRenderer:
    """Compose prose from per-slot surface banks; point only into accepted facts.

    Each bank varies connectives, framing verbs, clause shape and sentence lead
    while embedding the fact's content, so the surface varies combinatorially
    but every render tiles into approved segments. Selection is a pure function
    of the seed, so the variety is reproducible, not stochastic.
    """

    arm = "surface-pointer"

    def render(self, facts: frozenset[Fact], seed: int) -> Rendered:
        agent = _fact_value(facts, "agent")
        desire = _fact_value(facts, "desire")
        color = _fact_value(facts, "egg_color")
        lead = _seeded_choice(LEADS, seed, "lead")
        verb = _seeded_choice(DESIRE_VERB, seed, "verb")
        setup1 = _setup1(agent, verb, desire)
        setup2 = _seeded_choice(FEATHER_SETUP, seed, "feather")
        complication = _seeded_choice(COMPLICATION, seed, "complication")
        resolution = _seeded_choice(RESOLUTION, seed, "resolution")
        coda = _seeded_choice(CODA, seed, "coda").format(
            color=color, Color=color.capitalize()
        )
        text = f"{lead}{setup1} {setup2} {complication} {resolution} {coda}"
        return Rendered(text, facts, self.arm, seed)


# --------------------------------------------------------------------------
# The closure control: the render must tile into approved segments
# --------------------------------------------------------------------------


def _sentences(text: str) -> tuple[str, ...]:
    return tuple(m.strip() for m in re.findall(r"[^.?!]+[.?!]", text) if m.strip())


def approved_segments(accepted: frozenset[Fact]) -> dict[str, frozenset[str]]:
    """Every approved surface segment -> the accepted fact kinds it expresses.

    Built from the SAME banks and templates the renderers emit from, plus the
    story-derived agent/desire/color, so "approved variant of an accepted fact"
    is defined once. A segment absent from this map is, by definition, content
    the constrained pointer was never licensed to author.
    """

    agent = _fact_value(accepted, "agent")
    desire = _fact_value(accepted, "desire")
    color = _fact_value(accepted, "egg_color")

    approved: dict[str, frozenset[str]] = {}

    def add(segment: str, role: str) -> None:
        key = re.sub(r"\s+", " ", segment).strip()
        if key:
            approved[key] = approved.get(key, frozenset()) | _ROLE_KINDS[role]

    for lead in LEADS:
        if lead.strip():
            add(lead, "lead")
    for verb in DESIRE_VERB:
        add(_setup1(agent, verb, desire), "setup1")
    for segment in FEATHER_SETUP:
        add(segment, "feather")
    for segment in COMPLICATION:
        add(segment, "complication")
    for segment in RESOLUTION:
        add(segment, "resolution")
    for segment in CODA:
        add(segment.format(color=color, Color=color.capitalize()), "coda")
    for template in TEMPLATES:
        for sentence, role in zip(
            _sentences(template.format(color=color)), _TEMPLATE_ROLES
        ):
            add(sentence, role)
    return approved


def _tile(
    text: str, approved: dict[str, frozenset[str]]
) -> tuple[frozenset[str], str | None, tuple[frozenset[str], ...]]:
    """Consume ``text`` as a sequence of approved segments (longest-first).

    Returns the union of covered fact kinds, the first UNAPPROVED remainder (or
    ``None`` if the whole text tiled), and the ORDERED sequence of covered-kind
    sets for the segments actually matched — the substrate the ordering gate
    reads. A segment matches only up to a terminal-punctuation boundary and only
    when the next character is a space or end, so a segment cannot be spliced
    into a longer word.
    """

    norm = re.sub(r"\s+", " ", text).strip()
    segments = sorted(approved, key=len, reverse=True)
    pos = 0
    covered: set[str] = set()
    sequence: list[frozenset[str]] = []
    while pos < len(norm):
        if norm[pos] == " ":
            pos += 1
            continue
        match = None
        for segment in segments:
            end = pos + len(segment)
            if norm.startswith(segment, pos) and (
                end == len(norm) or norm[end] == " "
            ):
                match = segment
                break
        if match is None:
            return frozenset(covered), norm[pos:], tuple(sequence)
        covered |= approved[match]
        sequence.append(approved[match])
        pos += len(match)
    return frozenset(covered), None, tuple(sequence)


def _ordering_reasons(
    text: str, sequence: tuple[frozenset[str], ...], accepted: frozenset[Fact]
) -> list[str]:
    """Order is part of the accepted story; a scramble moves a fact.

    Two named teeth, applied only once the prose is otherwise closed and
    complete: (a) beat/temporal order consistent with the accepted StoryState
    (reuses :func:`_temporal_ok`, the same measurement the temporal metric
    uses), and (b) plant-before-discharge for every obligation — a discharge
    segment may not precede the plant that licenses it, which is exactly what the
    frame's obligation ledger encodes.
    """

    reasons: list[str] = []
    if not _temporal_ok(text, accepted):
        reasons.append("prose orders beats inconsistently with the accepted story")

    planted_positions = [i for i, kinds in enumerate(sequence) if "planted" in kinds]
    first_plant = min(planted_positions) if planted_positions else None
    discharged_elements = sorted(
        fact.value for fact in accepted if fact.kind == "discharged"
    )
    element = discharged_elements[0] if discharged_elements else "the planted element"
    for i, kinds in enumerate(sequence):
        if "discharged" in kinds and (first_plant is None or i < first_plant):
            reasons.append(f"prose discharges {element!r} before it is planted")
            break
    return reasons


def faithfulness(rendered: Rendered, accepted: frozenset[Fact]) -> tuple[str, ...]:
    """Named reasons a render moves a fact; empty tuple means faithful.

    The authoritative moved-fact gate. It reads the SURFACE (never the
    self-attested provenance) and proves three things: (1) *closure* — the prose
    tiles entirely into approved segments (:func:`approved_segments`); (2)
    *coverage* — those segments cover exactly the accepted fact kinds; and (3)
    *order* — the beats run in the accepted StoryState's order and no obligation
    is discharged before it is planted (:func:`_ordering_reasons`). An unapproved
    segment (added premise, negation, misattribution), an uncovered fact (dropped
    beat), a scrambled beat order, and a discharge-before-plant are each a named
    failure. Order is folded in because it is part of the accepted story: the
    frame's obligation ledger encodes plant->discharge, so a reversed narrative
    moves a fact just as surely as a substituted word does.
    """

    approved = approved_segments(accepted)
    accepted_kinds = {fact.kind for fact in accepted}
    covered, unapproved, sequence = _tile(rendered.text, approved)

    reasons: list[str] = []
    if unapproved is not None:
        reasons.append(
            "prose asserts content outside the accepted surface algebra: "
            f"{unapproved!r}"
        )
    missing = accepted_kinds - covered
    if missing:
        reasons.append(
            "prose does not express accepted fact(s): " + ", ".join(sorted(missing))
        )
    # ``covered`` can only hold accepted kinds (approved segments are built from
    # the accepted set), so an "extra kind" is structurally impossible; the
    # teeth against invention are the unapproved-segment branch above.
    #
    # Ordering is checked only once the prose is otherwise closed and complete:
    # a partial tiling (unapproved remainder) or a missing beat is already a
    # failure, and running the order gate on a truncated segment sequence would
    # add a misleading second reason to an already-caught render.
    if unapproved is None and not missing:
        reasons.extend(_ordering_reasons(rendered.text, sequence, accepted))
    return tuple(reasons)


def is_faithful(rendered: Rendered, accepted: frozenset[Fact]) -> bool:
    return not faithfulness(rendered, accepted)


class MovedColorRenderer(SurfacePointerRenderer):
    """Adversary: renders a DIFFERENT egg color than the signed binding.

    A positive control — it must be CAUGHT. Its coda binds a real but wrong
    color, which is not an approved coda for the accepted color, so closure
    rejects it on the coda segment. Its provenance is left EQUAL to the accepted
    set on purpose, to prove the gate does not lean on provenance.
    """

    arm = "adversary-moved-color"

    def __init__(self, wrong_color: str = "silver") -> None:
        self.wrong_color = wrong_color

    def render(self, facts: frozenset[Fact], seed: int) -> Rendered:
        honest = _fact_value(facts, "egg_color")
        base = super().render(facts, seed)
        text = base.text.replace(honest, self.wrong_color)
        return Rendered(text, facts, self.arm, seed)


class DeusRenderer(SurfacePointerRenderer):
    """Adversary: a deus-ex resolution that drops the planted fallen feather.

    Must be CAUGHT: the feather setup and resolution segments are rewritten to a
    sky-borne magic key (the no-deus violation the frame itself forbids), so
    those segments are unapproved and the planted/discharged facts go uncovered.
    Provenance is again left equal to accepted.
    """

    arm = "adversary-deus"

    def render(self, facts: frozenset[Fact], seed: int) -> Rendered:
        base = super().render(facts, seed)
        text = re.sub(
            r"(Nearby, |Beside its nest lay |Close by, )?[Aa] fallen feather[^.]*\.",
            "A sudden magic key appeared from the sky.",
            base.text,
            count=1,
        )
        text = re.sub(
            r"(It|With)[^.]*?sang until the sun rose\.",
            "It took the magic key, went outside, and sang until the sun rose.",
            text,
            count=1,
        )
        return Rendered(text, facts, self.arm, seed)


# --------------------------------------------------------------------------
# Metrics — each measured SEPARATELY (no single fluency scalar)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ProseMetrics:
    """The roadmap's metrics, reported side by side and never collapsed.

    ``human_preference`` is deliberately ``None``: out of scope for an automated
    slice and flagged deferred rather than faked with a proxy scalar.
    """

    arm: str
    renders: int
    premise_preservation: float
    required_beat_coverage: float
    temporal_consistency: float
    distinct_surface_ratio: float
    mean_type_token_ratio: float
    mean_pairwise_jaccard: float
    human_preference: None = None


#: Obstruction RELATIONS that make a complication a complication (not scenery).
_OBSTRUCTION_MARKERS: tuple[str, ...] = (
    "stood in the way",
    "barred the way",
    "would not open",
    "held fast",
)


def _has_word(text: str, token: str) -> bool:
    return re.search(rf"\b{re.escape(token)}\b", text.lower()) is not None


def _anchor_of(accepted: frozenset[Fact], kind: str) -> str:
    """A stable content token for ``kind`` (longest anchor), for the metrics."""

    for fact in accepted:
        if fact.kind == kind and fact.anchors:
            return max(fact.anchors, key=len)
    raise KeyError(kind)


def _beats_present(text: str, accepted: frozenset[Fact]) -> dict[str, bool]:
    """Required-beat coverage, grounded in accepted anchors.

    The complication beat requires the obstacle anchor AND an obstruction
    relation — a bare scenery mention of the obstacle word does not count (the
    drop-complication adversary keeps 'coop' as scenery; it must NOT read as a
    covered complication).
    """

    low = text.lower()
    setup = _has_word(text, _anchor_of(accepted, "agent")) and _has_word(
        text, _anchor_of(accepted, "desire")
    )
    complication = _has_word(text, _anchor_of(accepted, "obstacle")) and any(
        marker in low for marker in _OBSTRUCTION_MARKERS
    )
    resolution = _has_word(text, "key") and _has_word(
        text, _anchor_of(accepted, "outcome")
    )
    coda = _has_word(text, _fact_value(accepted, "egg_color"))
    return {
        "setup": setup,
        "complication": complication,
        "resolution": resolution,
        "coda": coda,
    }


def _temporal_ok(text: str, accepted: frozenset[Fact]) -> bool:
    """Beat order and plant-before-discharge, measured over the surface itself."""

    low = text.lower()

    def at(token: str) -> int:
        match = re.search(rf"\b{re.escape(token)}\b", low)
        return match.start() if match else -1

    setup = at(_anchor_of(accepted, "agent"))
    complication = at(_anchor_of(accepted, "obstacle"))
    resolution = at("key")
    coda = at(_fact_value(accepted, "egg_color"))
    feather = at(_anchor_of(accepted, "planted"))
    if min(setup, complication, resolution, coda) < 0:
        return False
    ordered = setup < complication < resolution < coda
    plant_before_discharge = feather < 0 or feather < resolution
    return ordered and plant_before_discharge


def _normalize_surface(text: str) -> str:
    """Whitespace/case-collapsed surface, so variety is not gamed by spacing."""

    return re.sub(r"\s+", " ", text.strip().lower())


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def measure(
    renders: tuple[Rendered, ...], accepted: frozenset[Fact]
) -> ProseMetrics:
    """Compute the five separately-reported metrics over a batch of renders."""

    if not renders:
        raise ValueError("cannot measure an empty batch of renders")
    arm = renders[0].arm
    n = len(renders)

    preserved = sum(is_faithful(r, accepted) for r in renders) / n
    covered = sum(all(_beats_present(r.text, accepted).values()) for r in renders) / n
    temporal = sum(_temporal_ok(r.text, accepted) for r in renders) / n

    surfaces = [_normalize_surface(r.text) for r in renders]
    distinct_ratio = len(set(surfaces)) / n
    word_sets = [set(re.findall(r"[a-z']+", s)) for s in surfaces]
    ttr = [
        len(set(re.findall(r"[a-z']+", s))) / max(1, len(re.findall(r"[a-z']+", s)))
        for s in surfaces
    ]
    mean_ttr = sum(ttr) / n
    distances = [
        1.0 - _jaccard(word_sets[i], word_sets[j])
        for i in range(n)
        for j in range(i + 1, n)
    ]
    mean_jaccard = sum(distances) / len(distances) if distances else 0.0

    return ProseMetrics(
        arm=arm,
        renders=n,
        premise_preservation=preserved,
        required_beat_coverage=covered,
        temporal_consistency=temporal,
        distinct_surface_ratio=distinct_ratio,
        mean_type_token_ratio=mean_ttr,
        mean_pairwise_jaccard=mean_jaccard,
    )


# --------------------------------------------------------------------------
# Authoring over a live conversation session — degrade to ASK, never guess
# --------------------------------------------------------------------------


def author_prose(
    session,
    renderer,
    seed: int,
    *,
    require_kind: str | None = None,
) -> Rendered | ProseAsk:
    """Author prose over a live conversation session, or ASK for a missing fact.

    The load-bearing branch is the failure one. If the owner's egg-color
    binding does not yet exist — or ``require_kind`` names a fact the accepted
    set does not contain — this does NOT invent a value, pick a default, or call
    a model: it opens (or keeps) a verifier-minted ASK and returns a
    :class:`ProseAsk` carrying that question. Only when every requested fact is
    accepted does it render.

    ``session`` is a :class:`conversation.ConversationSession`; the ASK reuses
    its harness Need channel (``state.awaiting``), not a second authority.
    """

    color = session.verifier.binding_value(session.state, "egg_color")
    if color is None:
        return _ask_for(session, "egg_color")

    facts = accepted_facts(session.story_state, color)
    if require_kind is not None and not any(
        fact.kind == require_kind for fact in facts
    ):
        return _ask_for(session, require_kind)

    return renderer.render(facts, seed)


def _ask_for(session, slot: str) -> ProseAsk:
    """Degrade to a WAITING ASK on ``slot`` through the harness Need channel."""

    from retrieval import ask_action  # local import: keep the import graph flat

    if session.state.awaiting is None or session.state.awaiting.slot != slot:
        if session.state.pending is None or session.state.pending.slot != slot:
            session.request_private_slot(slot)
        session.run_turn((ask_action(slot),))
    need: Need | None = pending_need(session.state)
    if need is None:  # pragma: no cover - ask_action always mints a question
        raise AssertionError("degrading to ASK did not mint a question")
    return ProseAsk(need.slot, need.prompt)


# --------------------------------------------------------------------------
# demo
# --------------------------------------------------------------------------


def _demo() -> int:
    from conversation import golden_chicken_revision_session

    session = golden_chicken_revision_session("alice")
    session.ask_and_reply("egg_color", "copper")
    color = session.verifier.binding_value(session.state, "egg_color")
    accepted = accepted_facts(session.story_state, color)

    pointer = SurfacePointerRenderer()
    template = ExactTemplateRenderer()

    print("ACCEPTED FACTS")
    for fact in sorted(accepted, key=lambda f: f.kind):
        print(f"  {fact.kind:<11} {fact.value!r} anchors={fact.anchors}")

    print("\nSURFACE POINTER (three seeds; same facts, different surface)")
    for seed in (1, 7, 42):
        print(f"  [{seed}] {pointer.render(accepted, seed).text}")

    print("\nEXACT TEMPLATE (three seeds; low variety by design)")
    for seed in (1, 7, 42):
        print(f"  [{seed}] {template.render(accepted, seed).text}")

    seeds = tuple(range(50))
    for renderer in (pointer, template):
        batch = tuple(renderer.render(accepted, s) for s in seeds)
        m = measure(batch, accepted)
        print(
            f"\nMETRICS {m.arm} (n={m.renders})\n"
            f"  premise_preservation={m.premise_preservation:.3f} "
            f"beat_coverage={m.required_beat_coverage:.3f} "
            f"temporal={m.temporal_consistency:.3f}\n"
            f"  distinct_surface_ratio={m.distinct_surface_ratio:.3f} "
            f"mean_TTR={m.mean_type_token_ratio:.3f} "
            f"mean_pairwise_jaccard={m.mean_pairwise_jaccard:.3f} "
            f"human_preference={m.human_preference}"
        )

    print("\nMOVED-FACT CONTROL (adversaries must be caught)")
    for adv in (MovedColorRenderer("silver"), DeusRenderer()):
        rendered = adv.render(accepted, 3)
        reasons = faithfulness(rendered, accepted)
        print(f"  {adv.arm}: caught={bool(reasons)}")
        for reason in reasons:
            print(f"     - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_demo())
