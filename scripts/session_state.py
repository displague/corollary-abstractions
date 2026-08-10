#!/usr/bin/env python3
"""Serialize a conversation across a process boundary, honestly.

ROADMAP-v0.7 item 2's acceptance is "serialize, restart, authenticate, and
continue ... while a stale or forged pre-restart binding is refused". This
module owns the first and third verbs. Two decisions inside it are the whole
argument, and both are the kind that are easy to get backwards.

**The session file is unsigned public state, on purpose.**

The obvious implementation puts a MAC over the whole envelope. It is also the
implementation that makes the acceptance test vacuous. If the envelope were
signed, a forged binding inside it would be caught by the envelope check, and
passing the test would prove nothing about whether *bindings* authenticate —
the property item 2 actually claims. Worse, it would invert the trust story
this codebase has been building: public state is public, it is untrusted, and
authority comes from per-record signatures plus verifier-private ledgers. That
is exactly what
``test_public_state_surgery_cannot_resurrect_superseded_answer`` established
in-process, and durability must not weaken it into "the file was fine".

So the file carries no envelope MAC. Anyone may edit it. What they cannot do
is make an edited binding authoritative, because:

* every :class:`retrieval.UserBinding`, :class:`retrieval.ClarificationRequest`
  and :class:`retrieval.RetrievalReceipt` carries its own signature and its own
  key id, derived from a root key that is **not in the file**;
* the :class:`retrieval.LedgerSnapshot` — which *is* verifier-private state
  travelling through public space — is signed, and is sequence-stamped from a
  counter that is also not in the file.

Deleting the ledger snapshot does not help an attacker either: without it the
restore refuses outright rather than proceeding with empty ledgers, which is
the failure mode ``docs/DESIGN-interactive-harness.md`` §3.3 warned about
("a restart that carried keys forward but not the ledgers would silently
re-admit consumed requests").

**Everything is re-derived, nothing is re-minted.**

Restoring builds a fresh :class:`retrieval.RetrievalVerifier` over the *same*
key ring, re-imports the ledgers, and then re-checks the restored state before
handing it back. A binding that no longer authenticates is not dropped
silently: :func:`restore_session` reports every refusal with its named reason
so a caller can print the transcript the acceptance scenario needs.

The codec below is a tagged, closed-form dataclass encoder. It has a
registry: a type that is not in :data:`_TYPES` cannot be written and cannot be
read. That is deliberate — a generic "pickle anything" codec on a trust
boundary is how untyped objects get instantiated from a file an attacker
controls.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from controller import Verdict
from frames import (
    FrameEvent,
    FrameSpec,
    FrameState,
    Literal,
    TemporalObligation,
)
from oracle_controller_demo import ElementMention, StoryBeat, StoryState
from retrieval import (
    Channel,
    ClarificationRequest,
    LedgerSnapshot,
    PointableMaterial,
    RetrievalItem,
    RetrievalNeed,
    RetrievalResolution,
    RetrievalReceipt,
    RetrievalState,
    UserBinding,
    UserFrame,
)
from session_keys import KEY_SCHEMA

#: Version of the *session file* format. Distinct from ``KEY_SCHEMA``: the
#: envelope layout and the signing scheme can move independently, and pinning
#: them together would force a key migration for a cosmetic field rename.
SESSION_SCHEMA = "corollary.session/1"

#: The closed set of types this codec will construct. Adding a row is a diff;
#: there is no reflection over arbitrary module contents, because the file
#: being decoded is untrusted by construction.
_TYPES: dict[str, type] = {
    cls.__name__: cls
    for cls in (
        Channel,
        ClarificationRequest,
        ElementMention,
        FrameEvent,
        FrameSpec,
        FrameState,
        LedgerSnapshot,
        Literal,
        PointableMaterial,
        RetrievalItem,
        RetrievalNeed,
        RetrievalReceipt,
        RetrievalResolution,
        RetrievalState,
        StoryBeat,
        StoryState,
        TemporalObligation,
        UserBinding,
        UserFrame,
        Verdict,
    )
}


class SessionFormatError(ValueError):
    """The file is not a session this build can read."""


def encode(value: Any) -> Any:
    """Tagged encoding: dataclasses by field, tuples and enums explicitly."""

    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Enum):
        if type(value).__name__ not in _TYPES:
            raise SessionFormatError(f"unregistered enum {type(value).__name__}")
        return {"$": type(value).__name__, "v": value.value}
    if isinstance(value, str):
        return value
    if is_dataclass(value) and not isinstance(value, type):
        name = type(value).__name__
        if name not in _TYPES:
            raise SessionFormatError(f"unregistered dataclass {name}")
        return {
            "$": name,
            "f": {
                field.name: encode(getattr(value, field.name))
                for field in fields(value)
            },
        }
    if isinstance(value, tuple):
        return {"$": "tuple", "v": [encode(item) for item in value]}
    if isinstance(value, list):
        # Lists are not part of any state this codec carries; refusing them
        # keeps "tuple" and "list" from round-tripping into each other and
        # silently changing an equality comparison.
        raise SessionFormatError("lists are not a session state type")
    raise SessionFormatError(f"unencodable value of type {type(value).__name__}")


def decode(raw: Any) -> Any:
    """Inverse of :func:`encode`, constructing only registered types."""

    if raw is None or isinstance(raw, (bool, int, float, str)):
        return raw
    if not isinstance(raw, dict) or "$" not in raw:
        raise SessionFormatError(f"untagged value in session file: {raw!r}")
    tag = raw["$"]
    if tag == "tuple":
        return tuple(decode(item) for item in raw["v"])
    cls = _TYPES.get(tag)
    if cls is None:
        raise SessionFormatError(f"unregistered type tag {tag!r}")
    if isinstance(cls, type) and issubclass(cls, Enum):
        return cls(raw["v"])
    known = {field.name for field in fields(cls)}
    payload = raw.get("f", {})
    unknown = set(payload) - known
    if unknown:
        raise SessionFormatError(
            f"{tag} carries unknown fields {sorted(unknown)}"
        )
    return cls(**{name: decode(value) for name, value in payload.items()})


def session_document(
    session_id: str,
    owner: str,
    active_slot: str,
    state: RetrievalState,
    story_state: StoryState,
    ledgers: LedgerSnapshot,
) -> dict[str, Any]:
    """The public session file, as a plain dict. No envelope MAC. See module docstring."""

    return {
        "schema": SESSION_SCHEMA,
        "key_schema": KEY_SCHEMA,
        "session_id": session_id,
        "owner": owner,
        "active_slot": active_slot,
        "state": encode(state),
        "story_state": encode(story_state),
        "ledgers": encode(ledgers),
    }


def read_document(path: Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema") != SESSION_SCHEMA:
        raise SessionFormatError(
            f"{path} declares schema {raw.get('schema')!r}, expected "
            f"{SESSION_SCHEMA!r}"
        )
    if "ledgers" not in raw:
        # Named explicitly rather than defaulting to empty ledgers: an absent
        # ledger is the exact silent re-admission DESIGN §3.3 forbade.
        raise SessionFormatError(
            f"{path} carries no ledger snapshot; a restart without ledgers "
            "would re-admit consumed requests"
        )
    return raw


def write_document(path: Path, document: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
