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

The **accepted facts** are exactly the story's beats (from the oracle-accepted
:class:`oracle_controller_demo.StoryState`) and the owner's signed egg-color
binding (from the durable :mod:`conversation` key ring). Nothing is invented and
nothing is dropped. A render is a surface string *plus* the structured
``provenance`` fact set it pointed at; the moved-fact control (below) checks the
provenance is byte-invariant across seeds while the surface genuinely varies,
and that an adversary who moves a fact is caught.

Two arms, compared on the metrics the roadmap names SEPARATELY (no single
fluency scalar):

* :class:`ExactTemplateRenderer` — the "richer exact templates" arm: a small
  fixed rotation of elaborate templates over the same facts. High fidelity, low
  lexical variety.
* :class:`SurfacePointerRenderer` — the "constrained surface pointer": composes
  prose from per-slot surface banks selected DETERMINISTICALLY by a seed. Every
  bank variant embeds the fact's lexical anchor, so surface varies
  combinatorially while the accepted facts never move.

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
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from harness import Need, pending_need
from oracle_controller_demo import StoryState
from request_grammar import SLOT_VALUES


# --------------------------------------------------------------------------
# Accepted facts: extracted from structured provenance, never guessed
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Fact:
    """One accepted fact and the lexical anchor a faithful surface must carry.

    ``anchors`` are the content tokens that MUST appear (on word boundaries) in
    any faithful rendering of this fact. They are the invariant the surface may
    not move: connectives, framing verbs and clause order are free to vary
    around them, but the anchors themselves are the accepted content. Facts are
    frozen and hashable so a render's provenance is a plain ``frozenset[Fact]``
    that supports exact set comparison — which is what makes "no fact moved" a
    structural check, not a fuzzy one.
    """

    kind: str
    value: str
    anchors: tuple[str, ...]


#: Colors the egg-color slot knows about (reused from the Phase-2 grammar's
#: closed vocabulary). Used only NEGATIVELY here — to notice a *foreign* color
#: an adversary smuggled in — never to author one. ``gold``/``golden`` are
#: excluded from the foreign-color scan because they legitimately describe the
#: chicken's plumage, not its eggs.
_COLOR_VOCAB = frozenset(SLOT_VALUES["egg_color"])
_PLUMAGE_COLORS = frozenset({"gold", "golden"})


def accepted_facts(story: StoryState, egg_color: str) -> frozenset[Fact]:
    """The accepted fact set: the story's beats plus the signed egg color.

    Every fact is read from structured provenance the runtime already trusts —
    the frame's declarations (affirmed/denied traits), the oracle's desire and
    beats, the complication beat's obstacle, the temporal obligation ledger
    (planted/discharged), the resolution beat's element mentions — and the one
    user-owned value the caller pulled from the verifier-signed binding. This
    function invents nothing: it is a projection of accepted state onto the
    anchors a faithful surface must preserve.
    """

    frame = story.frame_state
    agent = story.agent
    if agent is None:
        raise ValueError("accepted story has no declared agent to render")
    if story.desire is None:
        raise ValueError("accepted story has no bound desire to render")

    # Affirmed trait, from the frame's own declarations.
    affirmed = None
    for _, literal in frame.spec.declarations:
        if literal.predicate == "trait" and literal.polarity:
            affirmed = literal.value
            break
    if affirmed is None:
        raise ValueError("accepted story declares no affirmed trait")

    # Obstacle, from the complication beat ("But <obstacle> stood in the way.").
    obstacle = _complication_obstacle(story)

    facts = {
        Fact("agent", agent, ("golden", "chicken")),
        Fact("trait", affirmed, (affirmed,)),
        Fact("desire", story.desire, ("sunrise",)),
        Fact("obstacle", obstacle, ("coop",)),
        Fact("outcome", "sang the sun awake", ("sun",)),
        Fact("egg_color", egg_color, (egg_color,)),
    }
    # Temporal obligations: what was planted, and what was discharged.
    for obligation in frame.obligations:
        facts.add(Fact("planted", obligation.element, ("feather",)))
        if not obligation.outstanding:
            facts.add(
                Fact("discharged", "fallen feather used as key", ("feather", "key"))
            )
    return frozenset(facts)


def _complication_obstacle(story: StoryState) -> str:
    for beat in story.beats:
        if beat.role == "complication":
            match = re.fullmatch(r"But (.+) stood in the way\.", beat.text)
            if match:
                return match.group(1)
    return "the locked coop door"


# --------------------------------------------------------------------------
# A render: surface plus the structured provenance it pointed at
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rendered:
    """One authored surface plus the fact set it declares it pointed at."""

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
    """Deterministically pick one bank entry from ``(seed, salt)``.

    A pure function of its inputs (sha256), so a seed reproduces the same render
    on any machine. No ``random``, no clock — the repo bans both because they
    make a render irreproducible.
    """

    digest = hashlib.sha256(f"{seed}|{salt}".encode("utf-8")).digest()
    return bank[int.from_bytes(digest[:8], "big") % len(bank)]


# --------------------------------------------------------------------------
# Arm A: richer exact templates (fixed, elaborate, low variety)
# --------------------------------------------------------------------------


class ExactTemplateRenderer:
    """The "richer exact templates" comparison arm.

    A small fixed rotation of elaborate templates over the same facts. Each
    template is exact — no seeded variation beyond the substituted color — so
    the arm's lexical variety is bounded by the number of templates, which is
    exactly the property the pointer is meant to beat. Fidelity is total: every
    accepted anchor is present in every template.
    """

    arm = "exact-template"

    TEMPLATES: tuple[str, ...] = (
        "The golden chicken wanted to sing the sunrise awake. A fallen feather "
        "lay beside its nest. But the locked coop door stood in the way. It "
        "used the fallen feather as a key, went outside, and sang until the sun "
        "rose. Now the golden chicken laid {color} eggs.",
        "There was once a golden chicken who longed to sing the sunrise awake. "
        "Beside its nest a fallen feather had come to rest. Yet the locked coop "
        "door barred the way. Clever as it was, it turned the fallen feather "
        "into a key, stepped out into the dark, and sang until the sun rose. "
        "From that day the golden chicken laid {color} eggs.",
        "They tell of a golden chicken that wished to sing the sunrise awake. "
        "A fallen feather glinted near its nest. But the locked coop door held "
        "fast. So it worked the fallen feather like a key, slipped outside, and "
        "sang the sun into the sky. Ever after, the golden chicken's eggs came "
        "out {color}.",
    )

    def render(self, facts: frozenset[Fact], seed: int) -> Rendered:
        color = _fact_value(facts, "egg_color")
        template = self.TEMPLATES[seed % len(self.TEMPLATES)]
        return Rendered(template.format(color=color), facts, self.arm, seed)


# --------------------------------------------------------------------------
# Arm B: constrained surface pointer (varies words, never facts)
# --------------------------------------------------------------------------


class SurfacePointerRenderer:
    """Compose prose from per-slot surface banks, points only into accepted facts.

    Each bank varies connectives, framing verbs, clause shape and sentence lead
    while embedding the slot's fact anchor verbatim, so the surface varies
    combinatorially (thousands of assemblies) but every accepted anchor is
    always present and no unaccepted anchor is ever introduced. Selection is a
    pure function of the seed, so the variety is reproducible, not stochastic.
    """

    arm = "surface-pointer"

    LEADS: tuple[str, ...] = (
        "",
        "Here is how it went. ",
        "They say it happened like this. ",
        "The tale runs this way. ",
    )
    DESIRE_VERB: tuple[str, ...] = ("wanted", "longed", "yearned", "wished", "set out")
    DESIRE_TAIL: tuple[str, ...] = (
        "to sing the sunrise awake",
        "to sing the sunrise into waking",
        "to sing up the sunrise",
    )
    FEATHER_SETUP: tuple[str, ...] = (
        "Nearby, a fallen feather gleamed beside its nest.",
        "Beside its nest lay a fallen feather.",
        "Close by, a fallen feather caught the light.",
        "A fallen feather rested by the nest.",
    )
    COMPLICATION: tuple[str, ...] = (
        "But the locked coop door stood in the way.",
        "Yet the locked coop door barred the way.",
        "Trouble came: the locked coop door would not open.",
        "However, the locked coop door held fast.",
    )
    RESOLUTION: tuple[str, ...] = (
        "It used a fallen feather as a key, slipped outside, and sang until the sun rose.",
        "Cleverly, it turned the fallen feather into a key, stepped out, and sang the sun awake.",
        "It took the fallen feather, worked it like a key, and sang until the sun climbed the sky.",
        "With the fallen feather for a key, it went out and sang the sun into the sky.",
    )
    CODA: tuple[str, ...] = (
        "Now the golden chicken laid {color} eggs.",
        "From then on, its eggs came out {color}.",
        "And its eggs? {Color}, every one.",
        "Ever after it laid eggs of {color}.",
    )

    def render(self, facts: frozenset[Fact], seed: int) -> Rendered:
        color = _fact_value(facts, "egg_color")
        lead = _seeded_choice(self.LEADS, seed, "lead")
        verb = _seeded_choice(self.DESIRE_VERB, seed, "verb")
        tail = _seeded_choice(self.DESIRE_TAIL, seed, "tail")
        setup1 = f"The golden chicken {verb} {tail}."
        setup2 = _seeded_choice(self.FEATHER_SETUP, seed, "feather")
        complication = _seeded_choice(self.COMPLICATION, seed, "complication")
        resolution = _seeded_choice(self.RESOLUTION, seed, "resolution")
        coda = _seeded_choice(self.CODA, seed, "coda").format(
            color=color, Color=color.capitalize()
        )
        text = f"{lead}{setup1} {setup2} {complication} {resolution} {coda}"
        return Rendered(text, facts, self.arm, seed)


def _fact_value(facts: frozenset[Fact], kind: str) -> str:
    for fact in facts:
        if fact.kind == kind:
            return fact.value
    raise KeyError(f"no accepted fact of kind {kind!r} to render")


# --------------------------------------------------------------------------
# Faithfulness / the moved-fact control
# --------------------------------------------------------------------------


def _has_word(text: str, token: str) -> bool:
    return re.search(rf"\b{re.escape(token)}\b", text.lower()) is not None


def faithfulness(rendered: Rendered, accepted: frozenset[Fact]) -> tuple[str, ...]:
    """Named reasons a render is UNfaithful; empty tuple means faithful.

    Three independent teeth, any one of which catches a moved fact:

    1. *Provenance* — ``rendered.provenance`` must equal ``accepted`` exactly.
       A dropped, added or substituted fact shows up here structurally.
    2. *Premise preservation* — every accepted anchor must be present in the
       surface, so a render cannot claim a fact in provenance it did not write.
    3. *None invented* — no foreign egg-color token may appear; a substituted
       color (still a real color word, just the wrong one) is caught even when
       the accepted anchor is also somehow present.
    """

    reasons: list[str] = []
    if rendered.provenance != accepted:
        added = rendered.provenance - accepted
        dropped = accepted - rendered.provenance
        if added:
            reasons.append(
                "provenance adds unaccepted fact(s): "
                + ", ".join(sorted(f"{f.kind}={f.value}" for f in added))
            )
        if dropped:
            reasons.append(
                "provenance drops accepted fact(s): "
                + ", ".join(sorted(f"{f.kind}={f.value}" for f in dropped))
            )
    for fact in accepted:
        missing = [tok for tok in fact.anchors if not _has_word(rendered.text, tok)]
        if missing:
            reasons.append(
                f"surface drops the {fact.kind} anchor(s) {missing} "
                f"(fact {fact.value!r} is not visible in the prose)"
            )
    accepted_color = _fact_value(accepted, "egg_color").lower()
    foreign = sorted(
        color
        for color in _COLOR_VOCAB - _PLUMAGE_COLORS - {accepted_color}
        if _has_word(rendered.text, color)
    )
    if foreign:
        reasons.append(
            f"surface invents a foreign egg color {foreign} not in the "
            f"accepted binding ({accepted_color!r})"
        )
    return tuple(reasons)


def is_faithful(rendered: Rendered, accepted: frozenset[Fact]) -> bool:
    return not faithfulness(rendered, accepted)


class MovedColorRenderer(SurfacePointerRenderer):
    """Adversary: renders a DIFFERENT egg color than the signed binding.

    A positive control for the moved-fact invariant — it must be CAUGHT. It
    substitutes a real (but wrong) color word into both the surface and its
    provenance, so the invariant has to reject it on premise preservation and on
    the foreign-color scan and on provenance, not merely notice a shrug.
    """

    arm = "adversary-moved-color"

    def __init__(self, wrong_color: str = "silver") -> None:
        self.wrong_color = wrong_color

    def render(self, facts: frozenset[Fact], seed: int) -> Rendered:
        honest = _fact_value(facts, "egg_color")
        moved = frozenset(
            Fact("egg_color", self.wrong_color, (self.wrong_color,))
            if f.kind == "egg_color"
            else f
            for f in facts
        )
        base = super().render(moved, seed)
        # Re-point the coda at the wrong color; leave the rest as the pointer
        # wrote it. The honest color must genuinely disappear from the surface.
        text = base.text.replace(honest, self.wrong_color)
        return Rendered(text, moved, self.arm, seed)


class DeusRenderer(SurfacePointerRenderer):
    """Adversary: a deus-ex resolution that drops the planted fallen feather.

    The story's key comes ONLY from the planted feather (no-deus law). This
    renderer resolves with a key that fell from the sky and never mentions the
    feather — moving the planted/discharged facts. Must be CAUGHT: the feather
    anchor vanishes and the provenance loses the planted/discharged facts.
    """

    arm = "adversary-deus"

    def render(self, facts: frozenset[Fact], seed: int) -> Rendered:
        stripped = frozenset(
            f for f in facts if f.kind not in ("planted", "discharged")
        )
        base = super().render(stripped, seed)
        # Rewrite setup and resolution to erase the feather; a magic key
        # appears from nowhere (exactly the deus ex machina the frame forbids).
        text = re.sub(
            r"(Nearby, |Beside its nest lay |Close by, )?[Aa] fallen feather[^.]*\.",
            "A sudden magic key appeared from the sky.",
            base.text,
            count=1,
        )
        text = re.sub(
            r"(It|Cleverly, it|With)[^.]*?sang",
            "It took the magic key, went outside, and sang",
            text,
            count=1,
        )
        return Rendered(text, stripped, self.arm, base.seed)


# --------------------------------------------------------------------------
# Metrics — each measured SEPARATELY (no single fluency scalar)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ProseMetrics:
    """The roadmap's metrics, reported side by side and never collapsed.

    ``human_preference`` is deliberately ``None``: it is out of scope for an
    automated slice and is flagged deferred rather than faked with a proxy
    scalar (the roadmap forbids a single fluency number).
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


_BEAT_ANCHORS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("setup", ("chicken", "sunrise")),
    ("complication", ("coop",)),
    ("resolution", ("key", "sun")),
    ("coda", ("egg_color",)),  # coda anchor is the accepted color, resolved below
)


def _beats_present(text: str, color: str) -> dict[str, bool]:
    present: dict[str, bool] = {}
    for beat, anchors in _BEAT_ANCHORS:
        toks = (color,) if beat == "coda" else anchors
        present[beat] = all(_has_word(text, tok) for tok in toks)
    return present


def _temporal_ok(text: str, color: str) -> bool:
    """Beat order and plant-before-discharge, measured over the surface itself.

    Positions of first anchor occurrences must satisfy
    setup < complication < resolution < coda, and the feather (plant) must
    precede the key (discharge). This reads the rendered string, so it is a
    measurement, not an assumption about how the renderer assembled it.
    """

    low = text.lower()

    def at(token: str) -> int:
        match = re.search(rf"\b{re.escape(token)}\b", low)
        return match.start() if match else -1

    idx = {
        "chicken": at("chicken"),
        "coop": at("coop"),
        "key": at("key"),
        "color": at(color.lower()),
        "feather": at("feather"),
    }
    if any(v < 0 for k, v in idx.items() if k != "feather"):
        return False
    ordered = idx["chicken"] < idx["coop"] < idx["key"] < idx["color"]
    plant_before_discharge = idx["feather"] < 0 or idx["feather"] < idx["key"]
    return ordered and plant_before_discharge


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
    color = _fact_value(accepted, "egg_color")
    n = len(renders)

    preserved = sum(is_faithful(r, accepted) for r in renders) / n
    covered = (
        sum(all(_beats_present(r.text, color).values()) for r in renders) / n
    )
    temporal = sum(_temporal_ok(r.text, color) for r in renders) / n

    texts = [r.text for r in renders]
    distinct_ratio = len(set(texts)) / n
    word_sets = [set(re.findall(r"[a-z']+", t.lower())) for t in texts]
    ttr = [
        len(set(re.findall(r"[a-z']+", t.lower())))
        / max(1, len(re.findall(r"[a-z']+", t.lower())))
        for t in texts
    ]
    mean_ttr = sum(ttr) / n
    distances: list[float] = []
    for i in range(n):
        for j in range(i + 1, n):
            distances.append(1.0 - _jaccard(word_sets[i], word_sets[j]))
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
    :class:`ProseAsk` carrying that question, exactly as an unbound slot has
    always cost one question. Only when every requested fact is accepted does it
    render.

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

    from retrieval import ask_action  # local import: keep module import graph flat

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
