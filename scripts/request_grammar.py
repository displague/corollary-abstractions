#!/usr/bin/env python3
"""A bounded, closed-form grammar for filling already-open frame-private slots.

ROADMAP-v0.7 item 2: "parse a bounded but growing natural-request grammar into
frame-private slots, including corrections, pronouns, and owner references."
``docs/DESIGN-interactive-harness.md`` §3.4 pins what that is and is not: this
is harness **Phase 2**, a closed enumerable grammar that fills *already-open*
slots on *already-registered* paths. It invents no slot, no path, and no
value. Unrestricted prose authoring is item 9 and lands last.

Three properties are the contract, and each one is a table below rather than a
paragraph:

**Bounded.** :data:`SLOT_PHRASES`, :data:`SLOT_VALUES`, :data:`OWNER_WORDS`,
:data:`CORRECTION_MARKERS`, :data:`ABSTENTION_PHRASES` and :data:`RULES` are
the entire language. Growing the grammar means adding a row, in a diff, with a
test. There is no learned component, no similarity fallback, and no "closest
match" — those are the three ways a bounded parser becomes an unbounded
guesser.

**Closed-form.** Every rule is a literal template over those tables, tried in a
fixed order, first match wins. Two rules never vote. The parse of an utterance
is a function of the tables and the open goal, so it is reproducible and
diffable in exactly the sense AGENTS.md's "closed forms stay symbolic" means.

**Degrades to ASK, never to a guess.** :func:`parse_request` returns either a
:class:`ParsedRequest` or a :class:`ParseFailure` carrying a *named* reason.
There is no third outcome and no confidence score. A caller that receives a
failure must open (or keep open) an ASK for the slot — which is precisely what
an unbound slot does today, so an unparseable utterance costs a question and
never a wrong binding. The registered value tables are what make this real: if
the user says an unregistered colour, the honest answer is a question, because
a parser that accepted arbitrary trailing words would be authoring content.

The vocabulary is small on purpose. It covers the demo's world (a story's
colour and tone slots) and it says so; a wider world is a wider table, not a
different mechanism.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from lifetimes import Lifetime


class Intent(str, Enum):
    """What the utterance asks the runtime to do with an open slot."""

    #: Provide the value for the slot the runtime is waiting on.
    FILL = "fill"
    #: Replace the current answer for a slot that already has one.
    CORRECT = "correct"
    #: Decline to answer; the runtime must abstain rather than invent.
    ABSTAIN = "abstain"


class FailureReason(str, Enum):
    """Why a parse failed, by name. Every one of these degrades to ASK."""

    #: Nothing in :data:`RULES` matched the utterance at all.
    NO_RULE = "no-rule-matched"
    #: The utterance named a slot phrase that is not registered.
    UNREGISTERED_SLOT = "unregistered-slot-phrase"
    #: The utterance offered a value the slot's closed vocabulary lacks.
    UNREGISTERED_VALUE = "unregistered-value"
    #: A pronoun with no open slot or no prior binding to resolve against.
    UNRESOLVED_PRONOUN = "unresolved-pronoun"
    #: An owner reference that names nobody this session knows.
    UNKNOWN_OWNER = "unknown-owner"
    #: An owner reference to somebody other than the speaker.
    FOREIGN_OWNER = "foreign-owner"


# --- the tables -------------------------------------------------------------

#: Surface phrase -> slot name. Registered slots only; an unrecognised noun
#: phrase is a named failure, never a new slot.
SLOT_PHRASES: dict[str, str] = {
    "the eggs": "egg_color",
    "the egg color": "egg_color",
    "the egg colour": "egg_color",
    "egg color": "egg_color",
    "egg colour": "egg_color",
    "eggs": "egg_color",
    "the tone": "tone",
    "tone": "tone",
    "the mood": "tone",
}

#: Slot -> its closed value vocabulary. A value outside this set is
#: ``unregistered-value``: the parser will not pass through arbitrary text,
#: because passing it through is how a slot-filler becomes an author.
SLOT_VALUES: dict[str, tuple[str, ...]] = {
    "egg_color": (
        "silver",
        "gold",
        "golden",
        "blue",
        "copper",
        "green",
        "red",
        "black",
        "white",
    ),
    "tone": ("whimsical", "formal", "dark", "playful", "solemn"),
}

#: First-person owner references. These resolve to the *speaking* owner, which
#: the caller supplies; the grammar never learns who is talking.
OWNER_WORDS: tuple[str, ...] = ("mine", "my", "my version", "my copy", "me")

#: Third-person owner references. Registered so they can be *refused* by name
#: rather than silently ignored: one owner may not revise another's frame, and
#: "make hers blue" must produce ``foreign-owner``, not a shrug.
FOREIGN_OWNER_WORDS: tuple[str, ...] = (
    "hers",
    "his",
    "theirs",
    "her version",
    "his version",
    "their version",
)

#: Pronouns that stand in for the slot currently under discussion.
SLOT_PRONOUNS: tuple[str, ...] = ("it", "them", "that", "those")

#: Markers that make an utterance a correction rather than a first answer.
CORRECTION_MARKERS: tuple[str, ...] = (
    "no",
    "nope",
    "actually",
    "sorry",
    "instead",
    "wait",
    "on second thought",
)

#: Whole utterances that decline to answer.
ABSTENTION_PHRASES: tuple[str, ...] = (
    "i don't know",
    "i dont know",
    "no idea",
    "you choose",
    "you decide",
    "whatever you like",
)

#: Lifetime declarations. The user, not the policy, chooses how long an answer
#: outlives its goal -- which is why these are surface phrases with a table
#: and not an inferred property.
LIFETIME_MARKERS: tuple[tuple[str, Lifetime], ...] = (
    ("always", Lifetime.DURABLE),
    ("remember that", Lifetime.DURABLE),
    ("remember", Lifetime.DURABLE),
    ("from now on", Lifetime.DURABLE),
    ("just this once", Lifetime.GOAL_LOCAL),
    ("for now", Lifetime.GOAL_LOCAL),
    ("just for this", Lifetime.GOAL_LOCAL),
)

_ARTICLES = ("the ", "a ", "an ")
_TRAILING = (" instead", " please", " this time", " for me")


@dataclass(frozen=True)
class ParsedRequest:
    """One utterance, resolved against the open goal. Never a guess."""

    rule_id: str
    intent: Intent
    slot: str
    value: str | None
    owner: str
    lifetime: Lifetime = Lifetime.SESSION

    @property
    def revises(self) -> bool:
        return self.intent is Intent.CORRECT


@dataclass(frozen=True)
class ParseFailure:
    """A refusal to parse, carrying the reason and what the caller must ask.

    ``ask_slot`` is the slot the caller should open an ASK for. It is present
    even on failure whenever the open goal makes it obvious, because the whole
    point of degrading to ASK is that the runtime keeps making progress by
    *asking*, not by stopping.
    """

    reason: FailureReason
    utterance: str
    ask_slot: str | None = None
    detail: str = ""


def normalize(text: str) -> str:
    """Lowercase, strip punctuation to spaces, collapse whitespace.

    Deliberately not stemming, spell-correcting, or lemmatising: each of those
    is a similarity judgement, and a similarity judgement inside a bounded
    grammar is the unbounded guesser this module refuses to be.
    """

    lowered = text.strip().lower()
    lowered = re.sub(r"[^a-z0-9']+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _strip_articles(phrase: str) -> str:
    for article in _ARTICLES:
        if phrase.startswith(article):
            return phrase[len(article):]
    return phrase


def _strip_trailing(text: str) -> tuple[str, bool]:
    """Remove registered trailing softeners; report whether one meant 'instead'."""

    corrected = False
    changed = True
    while changed:
        changed = False
        for tail in _TRAILING:
            if text.endswith(tail):
                corrected = corrected or tail == " instead"
                text = text[: -len(tail)].strip()
                changed = True
    return text, corrected


def _leading_lifetime(text: str) -> tuple[str, Lifetime | None]:
    for marker, lifetime in LIFETIME_MARKERS:
        if text == marker:
            return "", lifetime
        if text.startswith(marker + " "):
            return text[len(marker) + 1:].strip(), lifetime
    return text, None


def _leading_correction(text: str) -> tuple[str, bool]:
    for marker in CORRECTION_MARKERS:
        if text == marker:
            return "", True
        if text.startswith(marker + " "):
            return text[len(marker) + 1:].strip(), True
    return text, False


def _leading_owner(text: str) -> tuple[str, str | None]:
    """Return the remainder and ``"self"``/``"foreign"``/``None``."""

    for word in FOREIGN_OWNER_WORDS:
        if text == word or text.startswith(word + " "):
            return text[len(word):].strip(), "foreign"
    for word in sorted(OWNER_WORDS, key=len, reverse=True):
        if text == word:
            return "", "self"
        if text.startswith(word + " "):
            return text[len(word) + 1:].strip(), "self"
    if text.startswith("in my version "):
        return text[len("in my version "):].strip(), "self"
    if text == "in my version":
        return "", "self"
    return text, None


def _split_slot_and_value(
    text: str, open_slot: str | None
) -> tuple[str | None, str | None, FailureReason | None]:
    """Resolve ``<slot phrase>? <value>`` against the registered tables.

    Longest slot phrase first, so ``"the egg color"`` is never read as the
    bare ``"eggs"`` of a different row. A leading pronoun binds to the open
    slot; without an open slot it is ``unresolved-pronoun`` rather than a
    default.
    """

    remainder = text
    slot = None
    for pronoun in SLOT_PRONOUNS:
        if remainder == pronoun or remainder.startswith(pronoun + " "):
            if open_slot is None:
                return None, None, FailureReason.UNRESOLVED_PRONOUN
            slot = open_slot
            remainder = remainder[len(pronoun):].strip()
            break
    if slot is None:
        for phrase in sorted(SLOT_PHRASES, key=len, reverse=True):
            if remainder == phrase:
                return SLOT_PHRASES[phrase], None, FailureReason.UNREGISTERED_VALUE
            if remainder.startswith(phrase + " "):
                slot = SLOT_PHRASES[phrase]
                remainder = remainder[len(phrase) + 1:].strip()
                break
    if slot is None:
        slot = open_slot
    if slot is None:
        return None, None, FailureReason.UNRESOLVED_PRONOUN
    remainder = _strip_articles(remainder).strip()
    if not remainder:
        return slot, None, FailureReason.UNREGISTERED_VALUE
    vocabulary = SLOT_VALUES.get(slot)
    if vocabulary is None:
        return slot, None, FailureReason.UNREGISTERED_SLOT
    if remainder in vocabulary:
        return slot, remainder, None
    # One registered adjustment: a value phrase may keep a trailing noun that
    # repeats the slot ("silver eggs"). Only registered slot nouns qualify.
    for phrase in sorted(SLOT_PHRASES, key=len, reverse=True):
        if remainder.endswith(" " + phrase) and SLOT_PHRASES[phrase] == slot:
            candidate = remainder[: -(len(phrase) + 1)].strip()
            if candidate in vocabulary:
                return slot, candidate, None
    return slot, None, FailureReason.UNREGISTERED_VALUE


#: The rule table, in trial order. Each row is ``(rule_id, description)``; the
#: matching itself is :func:`parse_request`, which walks these prefixes in
#: exactly this sequence. Keeping the ids and descriptions as data is what
#: lets a test enumerate coverage instead of trusting a docstring.
RULES: tuple[tuple[str, str], ...] = (
    ("R0-abstain", "a registered whole-utterance declination"),
    ("R1-bare-value", "a bare registered value for the open slot"),
    ("R2-correction", "a correction marker followed by a value or slot phrase"),
    ("R3-imperative", "make/let/have <slot phrase> <value>"),
    ("R4-owner", "a first-person owner reference scoping the request"),
    ("R5-foreign-owner", "a third-person owner reference, refused by name"),
    ("R6-pronoun", "a slot pronoun resolved against the open goal"),
    ("R7-lifetime", "a lifetime marker declaring durable or goal-local"),
)

_IMPERATIVES = ("make", "let", "have", "set", "change", "turn")


def parse_request(
    utterance: str,
    open_slot: str | None = None,
    owner: str = "user",
    answered_slots: tuple[str, ...] = (),
) -> ParsedRequest | ParseFailure:
    """Parse one utterance into a slot fill, a correction, or a named failure.

    ``open_slot`` is the slot the runtime is currently waiting on (or would
    reopen); ``answered_slots`` are the slots this owner has already bound,
    which is the only thing that distinguishes a FILL from a CORRECT when the
    utterance itself carries no correction marker.

    The return type is a union with no third arm on purpose. Callers get
    either a resolved request or a reason to ask, and there is nowhere to put
    a maybe.
    """

    text = normalize(utterance)
    if not text:
        return ParseFailure(FailureReason.NO_RULE, utterance, open_slot)

    if text in ABSTENTION_PHRASES:
        if open_slot is None:
            return ParseFailure(FailureReason.NO_RULE, utterance, None)
        return ParsedRequest(
            "R0-abstain", Intent.ABSTAIN, open_slot, None, owner
        )

    text, trailing_correction = _strip_trailing(text)
    text, lifetime = _leading_lifetime(text)
    text, marked_correction = _leading_correction(text)
    if lifetime is None:
        # A correction may carry its own lifetime declaration ("no, always
        # copper"), so the marker is looked for on both sides of the
        # correction word. Checking only before it made the whole utterance
        # unparseable, which the grammar then correctly -- and uselessly --
        # degraded to a question. Found by
        # test_durable_supersession_is_filed_under_the_owner_scope.
        text, lifetime = _leading_lifetime(text)
    if not text:
        return ParseFailure(
            FailureReason.UNREGISTERED_VALUE, utterance, open_slot,
            "a marker with nothing after it names no value",
        )

    rule = "R2-correction" if marked_correction else "R1-bare-value"
    if lifetime is not None:
        rule = "R7-lifetime"

    text, owner_ref = _leading_owner(text)
    if owner_ref == "foreign":
        return ParseFailure(
            FailureReason.FOREIGN_OWNER, utterance, open_slot,
            "one owner may not revise another owner's private frame",
        )
    if owner_ref == "self" and rule in ("R1-bare-value", "R2-correction"):
        rule = "R4-owner"

    for imperative in _IMPERATIVES:
        if text == imperative:
            text = ""
            break
        if text.startswith(imperative + " "):
            text = text[len(imperative) + 1:].strip()
            if rule in ("R1-bare-value",):
                rule = "R3-imperative"
            # "change" is itself a correction verb; "make" is not.
            marked_correction = marked_correction or imperative == "change"
            break

    # A second owner reference may follow the imperative ("make mine copper").
    text, inner_owner = _leading_owner(text)
    if inner_owner == "foreign":
        return ParseFailure(
            FailureReason.FOREIGN_OWNER, utterance, open_slot,
            "one owner may not revise another owner's private frame",
        )
    if inner_owner == "self" and rule in ("R1-bare-value", "R3-imperative"):
        rule = "R4-owner"

    if not text:
        return ParseFailure(
            FailureReason.UNREGISTERED_VALUE, utterance, open_slot,
            "no value was named",
        )

    started_with_pronoun = any(
        text == pronoun or text.startswith(pronoun + " ")
        for pronoun in SLOT_PRONOUNS
    )
    slot, value, failure = _split_slot_and_value(text, open_slot)
    if failure is not None:
        return ParseFailure(failure, utterance, slot or open_slot)
    assert slot is not None and value is not None
    if started_with_pronoun and rule in ("R1-bare-value", "R3-imperative"):
        # The pronoun is the more specific fact about the utterance than the
        # imperative that carried it: "make it gold" is a pronoun resolution
        # that happens to be phrased as a command, and reporting it as a plain
        # imperative hid which mechanism resolved the slot.
        rule = "R6-pronoun"

    corrects = (
        marked_correction
        or trailing_correction
        or slot in answered_slots
    )
    intent = Intent.CORRECT if corrects else Intent.FILL
    if corrects and rule == "R1-bare-value":
        rule = "R2-correction"
    return ParsedRequest(
        rule,
        intent,
        slot,
        value,
        owner,
        lifetime if lifetime is not None else Lifetime.SESSION,
    )


def coverage() -> tuple[tuple[str, str], ...]:
    """The rule table, for a test or a CLI to enumerate."""

    return RULES
