#!/usr/bin/env python3
"""One lifetime vocabulary for user bindings and owned belief frames.

ROADMAP-v0.7 item 2: "unify ``retrieval.UserFrame`` and owned belief frames
under an explicit lifetime protocol: goal-local, session, superseded, expired,
durable." Before this module those two kinds of runtime-owned state answered
the same question with different words — a binding was a string ``"session"``
that nothing read, and a frame was a pile of booleans (``closed``,
``superseded_declarations``, ``corpus_backed``) that each caller re-interpreted
in place. The protocol below is the shared answer, and it is *closed-form*: no
caller is allowed to invent a sixth state or to decide a lifetime by judgment.

Declared versus effective
-------------------------

The distinction is the whole design, and it exists because of a trap. A
lifetime that is stored as mutable public data is not authority — anyone
holding the tuple can rewrite ``"superseded"`` back to ``"session"``. So:

* the **declared** lifetime is chosen once, at creation, by an authority that
  signs it into the record (for a user binding, the trusted return channel;
  see :func:`declarable`). It never changes, and it is covered by the MAC;
* the **effective** lifetime is *computed* on every read from the declared
  one plus verifier-private ledgers plus the current goal. It is never
  stored, so there is nothing to tamper with.

``SUPERSEDED`` and ``EXPIRED`` are therefore effective-only: a reply may not
declare them (that would be an answer that arrives already dead), and no
public edit can impose them or remove them.

The protocol
------------

===============  ================  ==================================  ==========================
Lifetime         Declarable        Authoritative while                 Becomes
===============  ================  ==================================  ==========================
``goal_local``   yes               the goal it answered is still the    ``EXPIRED`` when that slot
                                   most recent one opened for its slot  is reopened
``session``      yes (default)     its session lives, across restarts   ``SUPERSEDED`` when a newer
                                   of the *same* session id             answer binds the same slot
``durable``      yes               its owner exists, in any session      ``SUPERSEDED`` by a newer
                                   and any frame                        durable answer, same slot
``superseded``   no                never                                terminal; kept as provenance
``expired``      no                never                                terminal; kept as provenance
===============  ================  ==================================  ==========================

Two consequences worth stating rather than leaving implicit. First,
``session`` surviving a restart is not a contradiction: a restart continues
*one* session id under a restored ledger, so what dies with the process is the
*process*, not the session. Second, ``durable`` is signed under an
owner-scoped key with neither session id nor frame spec in its payload — that
is precisely what lets it cross a restart into a new conversation, and equally
what means a durable binding is *not* frame-isolated. It is the one lifetime
that trades isolation for reach, which is why only an explicit request can
declare it.

Nothing here promotes testimony. Every lifetime in this table describes how
long a *user-owned, frame-private* answer stays authoritative for rendering.
None of them is a path into ``frame.asserted`` or into ``data/``; a binding
that has been authoritative for a year is still testimony.
"""

from __future__ import annotations

from enum import Enum


class Lifetime(str, Enum):
    """How long one piece of runtime-owned state stays authoritative."""

    #: Valid only while the goal that opened it is the current goal.
    GOAL_LOCAL = "goal_local"
    #: Valid for one conversation, across restarts of that conversation.
    SESSION = "session"
    #: Valid across conversations for one owner; the only cross-session class.
    DURABLE = "durable"
    #: Replaced by a newer answer for the same slot. Provenance, not authority.
    SUPERSEDED = "superseded"
    #: Its goal was reopened, or its frame closed. Provenance, not authority.
    EXPIRED = "expired"

    @property
    def authoritative(self) -> bool:
        """Whether state in this lifetime may still answer a slot."""

        return self in _AUTHORITATIVE

    @property
    def declarable(self) -> bool:
        """Whether a creating authority may *choose* this lifetime."""

        return self in _DECLARABLE

    @property
    def crosses_sessions(self) -> bool:
        """Whether this lifetime is signed under an owner-scoped key."""

        return self is Lifetime.DURABLE


_AUTHORITATIVE = frozenset(
    {Lifetime.GOAL_LOCAL, Lifetime.SESSION, Lifetime.DURABLE}
)
_DECLARABLE = frozenset({Lifetime.GOAL_LOCAL, Lifetime.SESSION, Lifetime.DURABLE})

#: The full protocol as data, so a test can assert on the table rather than on
#: prose, and so the CLI can print it. Ordered longest-lived last.
LIFETIME_PROTOCOL: tuple[tuple[str, bool, str, str], ...] = (
    (
        Lifetime.GOAL_LOCAL.value,
        True,
        "the goal it answered is still the newest goal for its slot",
        "expired when that slot is reopened",
    ),
    (
        Lifetime.SESSION.value,
        True,
        "its session id lives, across authenticated restarts",
        "superseded by a newer answer for the same slot",
    ),
    (
        Lifetime.DURABLE.value,
        True,
        "its owner exists, in any session and any frame",
        "superseded by a newer durable answer for the same slot",
    ),
    (
        Lifetime.SUPERSEDED.value,
        False,
        "never; retained only as provenance",
        "terminal",
    ),
    (
        Lifetime.EXPIRED.value,
        False,
        "never; retained only as provenance",
        "terminal",
    ),
)


def declarable(raw: str | Lifetime) -> Lifetime:
    """Parse a requested lifetime, refusing the effective-only ones.

    Raises :class:`ValueError` for an unregistered string *and* for
    ``superseded``/``expired``: a creating authority that could declare those
    could hand back an answer that was born dead, which is a stranger state
    than any this protocol wants to represent.
    """

    try:
        lifetime = Lifetime(raw)
    except ValueError as exc:
        registered = ", ".join(member.value for member in Lifetime)
        raise ValueError(
            f"unregistered lifetime {raw!r}; registered: {registered}"
        ) from exc
    if not lifetime.declarable:
        raise ValueError(
            f"{lifetime.value!r} is an effective lifetime, computed from the "
            "ledgers; it cannot be declared at creation"
        )
    return lifetime


def belief_frame_lifetime(frame_state) -> Lifetime:
    """Classify an owned belief frame in the same vocabulary, closed-form.

    This is the unification half of item 2. It reads only fields
    ``frames.FrameState`` already has, in a fixed precedence, so two callers
    cannot disagree about what a frame's lifetime is:

    1. ``closed`` frames are ``EXPIRED`` — a closed frame accepts no further
       transition, which is exactly what expiry means here;
    2. ``corpus_backed`` frames are ``DURABLE`` — their content outlives every
       session because it is committed corpus, not runtime state;
    3. a frame with a non-empty ``children`` tuple that is *nested inside*
       another owner's model is ``GOAL_LOCAL``; nesting is how this codebase
       represents a model opened for one purpose;
    4. everything else is ``SESSION``.

    ``SUPERSEDED`` is deliberately **not** returned for a frame with
    ``superseded_declarations``: those name individual declarations that were
    replaced, not the frame. Reporting the frame as superseded because one of
    its premises was would be the same category error the binding side avoids
    by computing supersession per binding.
    """

    if getattr(frame_state, "closed", False):
        return Lifetime.EXPIRED
    spec = getattr(frame_state, "spec", None)
    if spec is not None and getattr(spec, "corpus_backed", False):
        return Lifetime.DURABLE
    if getattr(frame_state, "children", ()) and getattr(spec, "owner", None):
        return Lifetime.GOAL_LOCAL
    return Lifetime.SESSION
