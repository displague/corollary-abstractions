#!/usr/bin/env python3
"""The session journal — three record types, a read barrier, and a chain.

`docs/DESIGN-session-ledger.md` §3 is the contract and its field names are
binding: *"Field names are the contract; implementation may extend, never
rename or repurpose."* This module is slice 1 of that design and nothing
else. There is no learned component anywhere in it.

## What is genuinely new here

Today a supposition does not survive the line that typed it:
`supposition.py:96-107` builds a fresh `FrameExecutor` per typed line and
throws the `FrameState` away. So a person can declare a premise and the next
turn has already forgotten it. This module gives the premise somewhere to
live — an **Assumption** record with a status and a lifetime — and gives the
answer that consumed it somewhere to say so.

## The three record types

**SessionHeader** carries `session_id`, `created_utc` and five `pins`, each
from the producer §3 names. `proposer_model_digest` is absent, and its
absence is the design's own statement that no proposer served.

**Assumption** carries `assumption_id`, `declared_at_turn`, `text_bytes`
(verbatim, never summarized), `normal_form` (from `supposition._atom`,
whose self-limitation is inherited verbatim — *"deliberately tiny: this is
not negation parsing"*, three leading negation markers and nothing else),
`status` in {live, superseded, retracted}, `superseded_by`, and a per-record
keyed `mac`.

**Turn** carries `turn_index`, `input_bytes`, `resolution`,
`assumptions_declared`, `assumptions_cited`, `live_set_digest` (the digest,
never the set — the journal stays linear in turns), `result`,
`receipt_digest`, `prev_turn_digest` and its own `mac`.

## The read barrier, and what makes a citation earned

`assumptions_cited` is **read-derived**. The only path from an Assumption
into a served answer is :meth:`AssumptionSet.binding_for`, which logs a
:class:`ReadEvent` before it returns anything. A citation exists if and only
if a read event exists. The serving path never touches an Assumption's
binding by attribute — the field is `_binding`, private by name so a bypass
is visible to a reader and to a linter, and `tests/test_session_ledger.py`
asserts the serving module contains no such access.

The read log is written by :func:`write_read_log`, a different function from
:func:`write_journal`, into a different file. B12 compares the two. If the
journal writer ever dropped or invented a citation, the two would disagree —
which is the whole point of writing them apart.

## What persists, and what may not

A live assumption supplies **one thing**: a numeric binding for a name the
next turn's expression actually uses. That is the mechanism, stated plainly
so nobody has to infer it from behaviour:

* `suppose x = 5` records an Assumption whose `_binding` is `("x", 5)`. The
  turn renders **byte-identically to the same line served statelessly** —
  declaring changes the ledger, never the words.
* a later `x ^ 2` finds `x` free, asks the live set for it (the read event),
  and answers 25 — citing the assumption it consumed.
* `2 + 2` on the same session reads nothing and renders byte-identically to
  the stateless service of `2 + 2`. That is B10's fence and it is a test,
  not a promise.
* `suppose not x = 5` records polarity False. A later turn that needs `x`
  gets a typed `assumption_conflict` refusal naming the assumption, because
  computing under a premise the person withdrew would be answering a
  question they did not ask. This is the only conflict `_atom` can see, and
  §7 B4 scopes its conflict arm to exactly that.

**Supersession** matches on `subject` — an extension field derived at
declaration — and never on `normal_form`. That is deliberate: matching on
the normal form would fire the read barrier and put a citation on a
declaring turn, which §3 forbids by construction.

## Where journals live, and why not under `data/`

`experiments/sessions/`. A recorded session is not seed-regenerable and
`scripts/check_regeneration.py` treats seeds as the source of truth under
`data/` and `data_holdout/`. A journal has no seed, so it lives under
`experiments/` with a digest pin and a test — the committed pattern
`check_regeneration.py:97-100` names for hand-authored artifacts.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

JOURNAL_SCHEMA = "corollary.session-journal/1"
READ_LOG_SCHEMA = "corollary.session-read-log/1"
JOURNAL_DIR = "experiments/sessions"

#: §3's bounds, frozen by the design and repeated here as constants a caller
#: can read rather than numbers a caller must know.
LIVE_ASSUMPTION_CAP = 8
TURN_CAP = 64

#: §3's status alphabet for an Assumption. Closed; a fourth value would be a
#: repurposing of the field the design named.
ASSUMPTION_STATUSES = ("live", "superseded", "retracted")

#: §3's `resolution.kind` alphabet. Closed for the same reason.
RESOLUTION_KINDS = ("exact", "supposition", "refusal")

#: The served statuses that make a turn a refusal turn for B7's purposes.
#: `exhausted` is here because a turn that reached no answer carries no
#: grounding claim, and B7 is about every such turn carrying its receipt.
REFUSAL_STATUSES = frozenset({"refused", "exhausted", "REFUSED"})

#: Typed refusal names this module owns. Everything else derives its name
#: from the route that refused, so a refusal can always say what it was.
REFUSAL_ASSUMPTION_BUDGET = "assumption_budget"
REFUSAL_ASSUMPTION_CONFLICT = "assumption_conflict"
REFUSAL_UNKNOWN_ASSUMPTION = "unknown_assumption"

#: MAC domains, in `session_keys`' own vocabulary. Two domains under one
#: root are cryptographically unrelated (`session_keys.py:394-421`), so an
#: assumption's MAC can never authenticate a turn.
DOMAIN_ASSUMPTION = "ledger-assumption"
DOMAIN_TURN = "ledger-turn"

#: A binding a supposition can carry: `name = number`. Deliberately the same
#: shape `evaluate.BINDING` already reads off a typed line, so a session
#: assumption and a same-line binding mean the same thing by construction
#: rather than by two parsers agreeing.
_BINDING_CLAIM = re.compile(
    r"^([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)$"
)


def canonical(value) -> str:
    """SPEC §4.1's canonical-JSON/compact, used for every digest here."""

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# the read barrier
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadEvent:
    """One access to an assumption's normal form, by the serving path."""

    turn_index: int
    assumption_id: str


class ReadBarrier:
    """The only door between an Assumption and an answer.

    It is deliberately dumb: it appends, it never filters, and it has no
    opinion about whether a read was a good idea. Its value is that it is
    the ONLY door — a citation set computed from its events is a claim about
    what the serving path actually consumed, and a citation set assembled
    anywhere else would be a claim about what somebody meant.
    """

    def __init__(self) -> None:
        self.events: list[ReadEvent] = []
        self._turn: int | None = None

    def open_turn(self, turn_index: int) -> None:
        self._turn = turn_index

    def close_turn(self) -> tuple[str, ...]:
        """The ids read during the open turn, sorted and de-duplicated."""

        if self._turn is None:
            return ()
        seen = sorted(
            {
                event.assumption_id
                for event in self.events
                if event.turn_index == self._turn
            }
        )
        self._turn = None
        return tuple(seen)

    def record(self, assumption_id: str) -> None:
        if self._turn is None:
            raise RuntimeError(
                "a read outside a turn: the barrier records WHEN a read "
                "happened and a read with no turn cannot be cited by one"
            )
        self.events.append(ReadEvent(self._turn, assumption_id))

    def citations_by_turn(self) -> dict[int, tuple[str, ...]]:
        """The read log's own view, rebuilt from events alone (B12's side)."""

        out: dict[int, set[str]] = {}
        for event in self.events:
            out.setdefault(event.turn_index, set()).add(event.assumption_id)
        return {index: tuple(sorted(ids)) for index, ids in sorted(out.items())}


# --------------------------------------------------------------------------
# Assumption
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Assumption:
    """§3's Assumption record. Field names are the contract.

    `normal_form` is **`supposition._atom`'s own return value** — the pair
    `[atom, polarity]` — and not a prose rendering of it. That choice is
    what makes §7 B4 mean what it says. B4 mutates `text_bytes` and
    `normal_form` and **nothing else**, and requires either a different
    answer digest or a typed conflict refusal where the mutation flips
    polarity. If polarity lived in a field beside `normal_form`, the
    polarity arm would be mutating an extension rather than the field the
    gate names, and if the numeric binding were stored separately the value
    arm would leave the answer untouched. Everything semantic is derived
    from `normal_form`, so mutating `normal_form` is the only way to change
    what this record means — which is the property the gate assumes.

    `key_id` is an extension: `session_keys` records name the generation
    they were signed under (`session_keys.py:41-45`) so a ring holding
    several generations knows which one to consult.
    """

    assumption_id: str
    declared_at_turn: int
    text_bytes: str
    #: `[atom, polarity]`, verbatim from `supposition._atom`.
    normal_form: tuple
    status: str = "live"
    superseded_by: str | None = None
    key_id: str = ""
    mac: str = ""

    @property
    def atom(self) -> str:
        return str(self.normal_form[0])

    @property
    def polarity(self) -> bool:
        return bool(self.normal_form[1])

    @property
    def _binding(self) -> tuple[str, str] | None:
        """The numeric binding this assumption supplies, or None.

        Private by name: the only supported way to obtain a value is
        :meth:`AssumptionSet.binding_for`, which fires the read barrier
        first. A serving-path access to this property would be a bypass, it
        would be visible to a reader and a linter, and
        `tests/test_session_ledger.py` asserts the serving module contains
        none.
        """

        return _binding_of(self.atom)

    @property
    def subject(self) -> str:
        """What supersession matches on. Derived, never stored.

        Reading it does NOT fire the barrier, and that is deliberate rather
        than accidental: knowing that a person supposed *something about x*
        is not knowing what they supposed, so matching a re-declaration
        against it cannot put a citation on a declaring turn — which §3
        forbids by construction.
        """

        binding = self._binding
        return binding[0] if binding else self.atom

    def record(self) -> dict:
        """The journal's view: every §3 field, in §3's names."""

        return {
            "assumption_id": self.assumption_id,
            "declared_at_turn": self.declared_at_turn,
            "text_bytes": self.text_bytes,
            "normal_form": list(self.normal_form),
            "status": self.status,
            "superseded_by": self.superseded_by,
            "key_id": self.key_id,
            "mac": self.mac,
        }

    def mac_payload(self, session_id: str) -> dict:
        payload = self.record()
        payload.pop("mac")
        payload["session_id"] = session_id
        payload["domain"] = DOMAIN_ASSUMPTION
        return payload


@dataclass(frozen=True)
class Conflict:
    """A live assumption says the binding does NOT hold. Typed, not silent.

    Carries the ATOM rather than the whole normal form, and the field is
    named `atom` rather than `normal_form` on purpose: the serving path must
    contain no `.normal_form` access at all, so that a single grep is a
    sufficient check that the read barrier was not bypassed
    (`tests/test_session_ledger.py`). A field name that made the grep noisy
    would make the check worthless.
    """

    assumption_id: str
    atom: str


def normalize_claim(text: str) -> tuple[str, bool]:
    """`supposition._atom`, called rather than copied.

    Its self-limitation is inherited verbatim and is worth quoting where a
    reader will meet it: *"Deliberately tiny: this is not negation parsing,
    it is the one form a person types when they mean the opposite of
    something they just said."* Three leading markers, nothing else — and
    §7 B4's conflict arm is scoped to exactly that.
    """

    from supposition import _atom  # noqa: PLC0415

    return _atom(text)


def _binding_of(atom: str) -> tuple[str, str] | None:
    match = _BINDING_CLAIM.match(atom.strip())
    if match is None:
        return None
    return match.group(1), match.group(2)


class AssumptionSet:
    """The live set, its lifecycle, and the one door to a binding."""

    #: §3's frozen ceiling, exposed so the harness can quote it in a refusal
    #: rather than hardcode a second copy of the number.
    cap = LIVE_ASSUMPTION_CAP

    def __init__(self, session_id: str, barrier: ReadBarrier) -> None:
        self.session_id = session_id
        self.barrier = barrier
        self._by_id: dict[str, Assumption] = {}
        self._order: list[str] = []

    @property
    def pending_turn_index(self) -> int:
        """Which turn is being served, from the barrier's own bookkeeping.

        Read off the barrier rather than tracked twice: two counters that
        can disagree is a place for a `declared_at_turn` to be wrong while
        every digest around it stays right.
        """

        if self.barrier._turn is None:
            raise RuntimeError(
                "a declaration outside a turn: an Assumption records WHICH "
                "turn declared it, and there is no turn open"
            )
        return self.barrier._turn

    # -- reading ---------------------------------------------------------

    def all_records(self) -> list[dict]:
        return [self._by_id[key].record() for key in self._order]

    def live(self) -> tuple[Assumption, ...]:
        return tuple(
            self._by_id[key]
            for key in self._order
            if self._by_id[key].status == "live"
        )

    def get(self, assumption_id: str) -> Assumption | None:
        return self._by_id.get(assumption_id)

    def live_set_digest(self) -> str:
        """§3: the digest of the live set, never the set.

        Over (assumption_id, normal_form, polarity) for every live record,
        sorted. `status` is not in it because every member is live by
        construction, and a field that cannot vary adds no discrimination.
        """

        return digest(
            [
                [item.assumption_id, list(item.normal_form)]
                for item in sorted(self.live(), key=lambda a: a.assumption_id)
            ]
        )

    # -- the barrier's door ----------------------------------------------

    def binding_for(self, name: str) -> Fraction | Conflict | None:
        """The ONLY way a served answer obtains an assumption's value.

        Fires the read barrier before returning anything — including before
        returning a :class:`Conflict`, because refusing because of an
        assumption is consuming it just as much as computing with it is.
        Returns None when no live assumption binds `name`, and records
        nothing in that case: a name nobody supposed is not a citation.
        """

        for item in reversed(self.live()):
            if item._binding is None or item._binding[0] != name:
                continue
            self.barrier.record(item.assumption_id)
            if not item.polarity:
                return Conflict(item.assumption_id, item.atom)
            return Fraction(item._binding[1])
        return None

    def bound_names(self) -> frozenset[str]:
        """Which names the live set could bind — WITHOUT reading any value.

        This is what lets the serving path decide whether an assumption is
        even relevant before it consumes one. Names are not normal forms:
        knowing that somebody supposed something about `x` is not knowing
        what they supposed, so this is not a barrier bypass and a citation
        never follows from it alone.
        """

        return frozenset(
            item._binding[0] for item in self.live() if item._binding
        )

    # -- lifecycle -------------------------------------------------------

    def _next_id(self) -> str:
        """The next free `aNNN`. Skips taken ids so a replayer that already
        holds journal records cannot mint a collision."""

        index = len(self._order) + 1
        while f"a{index:03d}" in self._by_id:
            index += 1
        return f"a{index:03d}"

    def declare(self, text: str, turn_index: int) -> Assumption | str:
        """Record a declaration, or return a typed refusal name.

        Supersession is by `subject`, and the subject of a binding claim is
        its variable name: `suppose x = 7` after `suppose x = 5` supersedes,
        because two live values for one name is not a richer session, it is
        an ambiguous one.
        """

        atom, polarity = normalize_claim(text)
        binding = _binding_of(atom)
        subject = binding[0] if binding else atom
        if len(self.live()) >= LIVE_ASSUMPTION_CAP and not any(
            item.subject == subject for item in self.live()
        ):
            return REFUSAL_ASSUMPTION_BUDGET
        assumption_id = self._next_id()
        fresh = Assumption(
            assumption_id=assumption_id,
            declared_at_turn=turn_index,
            text_bytes=text,
            normal_form=(atom, polarity),
        )
        for key in self._order:
            existing = self._by_id[key]
            if existing.status == "live" and existing.subject == subject:
                self._by_id[key] = replace(
                    existing, status="superseded", superseded_by=assumption_id
                )
        self._by_id[assumption_id] = fresh
        self._order.append(assumption_id)
        return fresh

    def retract(self, assumption_id: str) -> Assumption | str:
        """Retract by id. Reads the normal form, so the turn cites it."""

        existing = self._by_id.get(assumption_id)
        if existing is None or existing.status != "live":
            return REFUSAL_UNKNOWN_ASSUMPTION
        self.barrier.record(assumption_id)
        retracted = replace(existing, status="retracted")
        self._by_id[assumption_id] = retracted
        return retracted

    # -- MACs ------------------------------------------------------------

    def sign_all(self, keyring, key_id: str) -> None:
        from session_keys import session_scope  # noqa: PLC0415

        scope = session_scope(self.session_id)
        key = keyring.derive(key_id, scope, DOMAIN_ASSUMPTION)
        for record_id in self._order:
            item = replace(self._by_id[record_id], key_id=key_id, mac="")
            mac = hmac.new(
                key, canonical(item.mac_payload(self.session_id)).encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            self._by_id[record_id] = replace(item, mac=mac)


def verify_assumption_mac(record: dict, session_id: str, keyring) -> bool:
    from session_keys import session_scope  # noqa: PLC0415

    payload = dict(record)
    claimed = payload.pop("mac", "")
    payload["session_id"] = session_id
    payload["domain"] = DOMAIN_ASSUMPTION
    key = keyring.derive(
        record.get("key_id", ""), session_scope(session_id), DOMAIN_ASSUMPTION
    )
    expected = hmac.new(
        key, canonical(payload).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, claimed)


# --------------------------------------------------------------------------
# Turn
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Turn:
    """§3's Turn record. Field names are the contract."""

    turn_index: int
    input_bytes: str
    resolution: dict
    assumptions_declared: tuple[str, ...]
    assumptions_cited: tuple[str, ...]
    live_set_digest: str
    result: dict
    receipt_digest: str
    prev_turn_digest: str
    #: EXTENSION: the typed `SessionEvent` records this turn produced. Inside
    #: the MAC payload, not beside it — an extension a tamperer could edit
    #: without invalidating a signature would be the hole B8 is about.
    session_events: tuple = ()
    key_id: str = ""
    mac: str = ""

    def record(self) -> dict:
        return {
            "turn_index": self.turn_index,
            "input_bytes": self.input_bytes,
            "resolution": self.resolution,
            "assumptions_declared": list(self.assumptions_declared),
            "assumptions_cited": list(self.assumptions_cited),
            "live_set_digest": self.live_set_digest,
            "result": self.result,
            "receipt_digest": self.receipt_digest,
            "prev_turn_digest": self.prev_turn_digest,
            "session_events": list(self.session_events),
            "key_id": self.key_id,
            "mac": self.mac,
        }

    def mac_payload(self, session_id: str) -> dict:
        payload = self.record()
        payload.pop("mac")
        payload["session_id"] = session_id
        payload["domain"] = DOMAIN_TURN
        return payload


def sign_turn(turn: Turn, session_id: str, keyring, key_id: str) -> Turn:
    from session_keys import session_scope  # noqa: PLC0415

    key = keyring.derive(key_id, session_scope(session_id), DOMAIN_TURN)
    staged = replace(turn, key_id=key_id, mac="")
    mac = hmac.new(
        key, canonical(staged.mac_payload(session_id)).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return replace(staged, mac=mac)


def verify_turn_mac(record: dict, session_id: str, keyring) -> bool:
    from session_keys import session_scope  # noqa: PLC0415

    payload = dict(record)
    claimed = payload.pop("mac", "")
    payload["session_id"] = session_id
    payload["domain"] = DOMAIN_TURN
    key = keyring.derive(
        record.get("key_id", ""), session_scope(session_id), DOMAIN_TURN
    )
    expected = hmac.new(
        key, canonical(payload).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, claimed)


# --------------------------------------------------------------------------
# the served verdict, digested
# --------------------------------------------------------------------------

#: What the person is TOLD, which is what `answer_bytes_digest` covers. The
#: echoed line is included here (unlike P2's probe, which was comparing
#: different lines): replay supplies the same input bytes, so the echo is
#: part of the record rather than a trivial discriminator.
_RENDER_KEYS = (
    "line",
    "route",
    "status",
    "detail",
    "evidence",
    "answer",
    "missing_capability",
    "reading",
)

#: The provenance half: where the answer came from and what it consumed.
_RECEIPT_KEYS = (
    "route",
    "status",
    "detail",
    "evidence",
    "receipt",
    "missing_capability",
)


def answer_bytes(verdict: dict) -> str:
    """The rendered stop, exactly as `harness.render_verdict` prints it."""

    from harness import render_verdict  # noqa: PLC0415

    return "\n".join(render_verdict(verdict))


def answer_bytes_digest(verdict: dict) -> str:
    return text_digest(answer_bytes(verdict))


def receipt_digest(
    verdict: dict, cited: tuple[str, ...], live_digest: str
) -> str:
    """B7's field: never null, and it carries the citations explicitly."""

    payload = {
        key: verdict.get(key) for key in _RECEIPT_KEYS if key in verdict
    }
    payload["assumptions_cited"] = list(cited)
    payload["live_set_digest"] = live_digest
    return digest(payload)


def resolution_kind(verdict: dict, declared: bool, lifecycle: bool) -> str:
    if declared or lifecycle:
        return "supposition"
    if verdict.get("status") in REFUSAL_STATUSES:
        return "refusal"
    return "exact"


def refusal_type(verdict: dict) -> str | None:
    status = verdict.get("status")
    if status not in REFUSAL_STATUSES:
        return None
    typed = verdict.get("refusal_type")
    if typed:
        return str(typed)
    return f"{verdict.get('route', 'unknown')}_{str(status).lower()}"


def grammar_query(verdict: dict) -> str | None:
    """The LINE_GRAMMAR row form that claimed this line."""

    from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

    route = verdict.get("route")
    for row in LINE_GRAMMAR:
        if row["route"] == route:
            return row["form"]
    return None


# --------------------------------------------------------------------------
# pins
# --------------------------------------------------------------------------


def line_grammar_digest() -> str:
    from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

    return text_digest(
        json.dumps(LINE_GRAMMAR, sort_keys=True, default=list)
    )


def rendering_module_digests(repo_root: Path) -> dict[str, str]:
    """throughput_tasks.json's field, by throughput_tasks.json's derivation.

    The module list and the digest function are READ from the builder rather
    than re-listed here. A second copy of a list is a second thing to rot,
    and "the same derivation as `experiments/throughput_tasks.json`'s field"
    is a claim this import makes true instead of asserting.
    """

    import build_throughput_tasks as builder  # noqa: PLC0415

    return {
        rel: builder.canonical_lf_sha256(rel)
        for rel in builder.RENDERING_MODULES
    }


def checker_toolchain_digest(repo_root: Path) -> str:
    """The `lean-toolchain` file `external_verifier._pin_inputs` pins."""

    path = repo_root / "prover" / "lean" / "normalizer" / "lean-toolchain"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capability_sheet_digest(repo_root: Path, matrix) -> str:
    """sha256 of the served sheet bytes, built from the live objects.

    The engine's `_matrix` is assigned from an already-booted offline
    session rather than letting `prewarm()` build one: prewarm also starts
    a pool refill thread and rebuilds the graph index, and a recorder has no
    use for either. The sheet bytes are the same either way — it is the same
    builder over the same matrix.
    """

    from serve_chat import ChatEngine, assert_no_demo_name  # noqa: PLC0415

    engine = ChatEngine(repo_root, pool_size=0)
    engine._matrix = matrix
    sheet = engine.capability_sheet()
    return text_digest(assert_no_demo_name(sheet, "session ledger pin"))


def pins(repo_root: Path, matrix) -> dict:
    """§3's pin table. `proposer_model_digest` is absent, and means so."""

    from write_stage import durable_digest  # noqa: PLC0415

    return {
        "corpora_digest": durable_digest(repo_root / "data"),
        "line_grammar_digest": line_grammar_digest(),
        "rendering_module_digests": rendering_module_digests(repo_root),
        "checker_toolchain_digest": checker_toolchain_digest(repo_root),
        "capability_sheet_digest": capability_sheet_digest(repo_root, matrix),
    }


PIN_FIELDS = (
    "corpora_digest",
    "line_grammar_digest",
    "rendering_module_digests",
    "checker_toolchain_digest",
    "capability_sheet_digest",
)


# --------------------------------------------------------------------------
# the journal
# --------------------------------------------------------------------------


GENESIS = "genesis"


def header_digest(header: dict) -> str:
    return digest(header)


def journal_document(
    header: dict, assumptions: list[dict], turns: list[dict]
) -> dict:
    return {
        "schema": JOURNAL_SCHEMA,
        "header": header,
        "assumptions": assumptions,
        "turns": turns,
    }


def serialize(document: dict) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_journal(path: Path, document: dict) -> str:
    """Write one journal. Returns its whole-file digest for the SEAL.

    The digest is RETURNED, never written into the file: §3 puts the
    journal's whole-file digest out-of-band in the corpus seal, because a
    digest that lives inside the thing it covers is a digest an editor
    updates.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    text = serialize(document)
    path.write_text(text, encoding="utf-8")
    return text_digest(text)


def write_read_log(path: Path, session_id: str, barrier: ReadBarrier) -> str:
    """The read-event log, written INDEPENDENTLY of the journal writer.

    Different function, different file, and its content is derived from the
    barrier's raw event list rather than from anything the journal writer
    computed. B12 compares the two; if they were written by one function
    the comparison would be a function comparing itself to itself.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "schema": READ_LOG_SCHEMA,
        "session_id": session_id,
        "events": [
            {"turn_index": event.turn_index, "assumption_id": event.assumption_id}
            for event in barrier.events
        ],
    }
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return text_digest(text)


def journal_path(repo_root: Path, session_id: str) -> Path:
    return repo_root / JOURNAL_DIR / f"{session_id}.json"


def read_log_path(repo_root: Path, session_id: str) -> Path:
    return repo_root / JOURNAL_DIR / f"{session_id}.reads.json"


def half_of(session_id: str) -> str:
    """The committed hash-derived split, reused verbatim from
    `experiments/throughput_tasks.json`'s seal."""

    return (
        "B"
        if int(hashlib.sha256(session_id.encode()).hexdigest()[:2], 16) % 2
        else "A"
    )


def is_binding_dependent(turn_record: dict) -> bool:
    """A turn whose ANSWER consumed an assumption.

    §3 excludes declaring turns from the binding-dependence denominator
    because a declaring turn cites nothing. The same reasoning excludes
    every lifecycle turn: a `retract` turn cites the assumption it retracts
    (it reads the normal form to name it), but what it produces is a
    lifecycle acknowledgement, not an answer that depends on the value. So
    the denominator is: non-empty citations AND `resolution.kind == "exact"`.
    Recorded in the prereg's dated amendment rather than decided here.
    """

    return bool(turn_record["assumptions_cited"]) and (
        turn_record["resolution"]["kind"] == "exact"
    )
