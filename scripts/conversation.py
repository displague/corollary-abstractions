#!/usr/bin/env python3
"""Maintained user-frame conversation that survives a process boundary.

Registered predictions (P-CR, before executing the expanded demo):

P-CR1. Two owners starting from one identical public golden-chicken state can
    answer the same private slot differently; each renderer uses only its own
    signed binding and neither session mutates the shared story or the other.
P-CR2. A later reply for the same owner and slot explicitly supersedes the
    earlier request id, preserves both bindings as provenance, and renders only
    the new value. Session identity and accepted story beats remain stable.
P-CR3. Across all turns, user testimony clears the pending UNKNOWN but never
    enters ``frame.asserted`` or corpus state. Dropping the verifier still drops
    the signing authority; this is maintained in-process state, not a durable
    authenticated restart format.

**P-CR3 is now half-retracted, deliberately.** ROADMAP-v0.7 item 2 shipped the
durable restart P-CR3 said did not exist, so its second sentence no longer
describes this module. What survives of it is the part that matters and was
never about durability: user testimony still clears a pending UNKNOWN without
ever entering ``frame.asserted`` or corpus state, before *and* after a restart.
What changed is only *where the authority lives* — no longer in a secret that
dies with the process, but in a root key the runtime owns outside public state
(:mod:`session_keys`). Dropping the verifier still drops nothing an attacker
can use: the ring, not the instance, is the authority, and the ring is a file
this process holds and revokes. Registered predictions are corrected in place
with the correction attached, never silently edited (AGENTS.md).

The durable predictions themselves are P-DS1..P-DS7 in ``docs/ROADMAP-v0.7.md``
item 2, registered before any of this was written.
"""

from __future__ import annotations

import argparse
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path

from controller import Controller, RunResult, SequencePolicy, StopReason
from frames import FrameExecutor, FrameSpec, Literal
from lifetimes import LIFETIME_PROTOCOL, Lifetime, belief_frame_lifetime
from oracle_controller_demo import StoryState, story_oracle_run
from request_grammar import (
    Intent,
    ParseFailure,
    ParsedRequest,
    parse_request,
)
from retrieval import (
    LedgerSnapshot,
    RetrievalState,
    RetrievalVerifier,
    UnifiedKnowledgeStore,
    ask_action,
    point_action,
    run_miss_chain,
)
from session_keys import KeyRingRefusal, RefusalReason, SessionKeyRing
from session_state import (
    SessionFormatError,
    decode,
    encode as encode_snapshot,
    read_document,
    session_document,
    write_document,
)


class EmptyStore:
    """ASK must not consult a durable store for a user-private slot."""

    def query(self, key: str, limit: int = 24):
        raise AssertionError(f"ASK unexpectedly queried durable store for {key!r}")

    def binding_match_mode(self, item, key: str):
        del item, key
        return None

    def contains_item(self, item) -> bool:
        del item
        return False


@dataclass(frozen=True)
class Turn:
    """One utterance and what the runtime did with it — including nothing."""

    utterance: str
    parsed: ParsedRequest | ParseFailure
    reply: str | None = None
    asked: str | None = None
    abstained: bool = False

    @property
    def understood(self) -> bool:
        return isinstance(self.parsed, ParsedRequest)


@dataclass(frozen=True)
class RestoreReport:
    """What a restart re-admitted, and what it refused by name.

    Refusals are *reported*, not raised, once the ledger has authenticated: a
    session whose fifth binding was tampered with should still come back with
    its first four, and the operator should be told exactly which record died
    and why. A refusal that only shows up as a missing value is the silent
    failure this item exists to abolish.
    """

    session_id: str
    owner: str
    key_id: str
    sequence: int
    admitted: tuple[tuple[str, str, str], ...] = ()
    refused: tuple[tuple[str, str, RefusalReason], ...] = ()

    def refusal_for(self, request_id: str) -> RefusalReason | None:
        for candidate, _slot, reason in self.refused:
            if candidate == request_id:
                return reason
        return None


@dataclass
class ConversationSession:
    """Persist accepted symbolic state and per-turn traces across user input.

    "Persist" now means two different durations and the difference is explicit.
    Within a process this is the same maintained state it always was. Across
    processes, :meth:`save` writes public state plus a signed ledger snapshot
    and :meth:`restore` rebuilds a verifier over the *same* key ring. What is
    never written is the root key: it lives in the ring's private keyfile, and
    a session file is useless without it.
    """

    state: RetrievalState
    verifier: RetrievalVerifier
    story_state: StoryState
    controller: Controller[RetrievalState] = field(
        default_factory=lambda: Controller(max_steps=8)
    )
    turns: list[RunResult[RetrievalState]] = field(default_factory=list)
    active_slot: str = "egg_color"
    said: list[Turn] = field(default_factory=list)
    slot_literals: dict[str, Literal] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._remember_pending()

    def _remember_pending(self) -> None:
        """Keep the literal shape each slot was opened with.

        Reopening a slot has to re-pose *the same* unresolved literal, or the
        reopened goal is a different question wearing the same slot name. This
        used to be a hard-coded golden-chicken literal, which was invisible
        while one demo owned the file and wrong the moment a second need
        (``tone`` in :func:`maintained_lifecycle`) shared the class.
        """

        pending = self.state.pending
        if pending is not None:
            self.slot_literals.setdefault(pending.slot, pending.unresolved_literal)

    # -- identity ---------------------------------------------------------

    @property
    def owner(self) -> str:
        return self.state.user_frame.owner

    @property
    def session_id(self) -> str:
        return self.state.session_id

    def answered_slots(self) -> tuple[str, ...]:
        """Slots this owner currently has an authoritative answer for."""

        seen = []
        for binding in self.state.user_frame.bindings:
            if binding.slot in seen:
                continue
            if self.verifier.binding_value(self.state, binding.slot) is not None:
                seen.append(binding.slot)
        return tuple(seen)

    def lifetime_of(self, slot: str) -> Lifetime | RefusalReason | None:
        """The effective lifetime of the newest binding for ``slot``."""

        for binding in reversed(self.state.user_frame.bindings):
            if binding.slot == slot:
                return self.verifier.binding_status(self.state, binding)
        return None

    # -- turns ------------------------------------------------------------

    def run_turn(self, actions) -> RunResult[RetrievalState]:
        result = self.controller.run(
            self.state,
            SequencePolicy(tuple(actions)),
            self.verifier,
            is_complete=lambda state: (
                state.pending is None
                and self.verifier.binding_value(state, self.active_slot)
                is not None
            ),
            is_waiting=lambda state: state.awaiting is not None,
        )
        self.state = result.final_state
        self.turns.append(result)
        return result

    def request_private_slot(self, slot: str) -> None:
        """Open a new goal while retaining this owner's session memory."""
        if self.state.pending is not None or self.state.awaiting is not None:
            raise ValueError("cannot open a new goal while another is unresolved")
        literal = self.slot_literals.get(
            slot, Literal("the golden chicken's eggs", "color", slot)
        )
        fresh = RetrievalState.from_unknown(
            self.verifier.frame_executor,
            self.state.frame,
            slot,
            slot,
            literal,
            resolution_channel="user",
            user_owner=self.state.user_frame.owner,
        )
        self.state = replace(
            fresh,
            session_id=self.state.session_id,
            user_frame=self.state.user_frame,
        )
        self.active_slot = slot
        self.slot_literals.setdefault(slot, literal)

    def ask_and_reply(
        self,
        slot: str,
        value: str,
        lifetime: Lifetime | str = Lifetime.SESSION,
    ) -> None:
        if self.state.pending is None:
            self.request_private_slot(slot)
        if self.state.awaiting is None:
            asked = self.run_turn((ask_action(slot),))
            if asked.stop_reason is not StopReason.WAITING:
                raise AssertionError("ASK did not pause for user input")
        reply = self.verifier.reply_action(self.state, value, lifetime)
        answered = self.run_turn((reply,))
        if not answered.solved:
            raise AssertionError("authenticated reply did not resume the goal")

    def say(self, utterance: str) -> Turn:
        """One natural utterance, parsed by the bounded grammar or asked about.

        The failure branch is the load-bearing one. When the grammar does not
        recognise the utterance, this method does not guess a value, does not
        pick the nearest registered one, and does not fall back to a model: it
        opens (or keeps) an ASK for the slot and returns the named reason. An
        unparseable sentence therefore costs exactly one question — the same
        price an unbound slot has always cost.
        """

        open_slot = (
            self.state.awaiting.slot
            if self.state.awaiting is not None
            else self.state.pending.slot
            if self.state.pending is not None
            else self.active_slot
        )
        parsed = parse_request(
            utterance, open_slot, self.owner, self.answered_slots()
        )
        if isinstance(parsed, ParseFailure):
            turn = Turn(utterance, parsed, asked=self._degrade_to_ask(parsed))
            self.said.append(turn)
            return turn
        if parsed.intent is Intent.ABSTAIN:
            turn = Turn(utterance, parsed, abstained=True)
            self.said.append(turn)
            return turn
        assert parsed.value is not None
        if (
            self.state.awaiting is not None
            and self.state.awaiting.slot != parsed.slot
        ):
            # An outstanding question owns the branch; every other transition
            # is frozen (retrieval._ask/_reply enforce it). Raising here rather
            # than dropping the question keeps that invariant visible instead
            # of letting the session quietly abandon a WAITING slot.
            raise ValueError(
                f"{self.state.awaiting.slot!r} is awaiting a reply; "
                f"{parsed.slot!r} cannot be answered first"
            )
        if parsed.intent is Intent.CORRECT and self.state.pending is None:
            self.request_private_slot(parsed.slot)
        elif (
            self.state.pending is not None
            and self.state.pending.slot != parsed.slot
        ):
            raise ValueError(
                f"utterance answers {parsed.slot!r} while {self.state.pending.slot!r} "
                "is the open goal"
            )
        self.ask_and_reply(parsed.slot, parsed.value, parsed.lifetime)
        turn = Turn(utterance, parsed, reply=parsed.value)
        self.said.append(turn)
        return turn

    def _degrade_to_ask(self, failure: ParseFailure) -> str:
        """The only thing an unparseable utterance is allowed to cause.

        Not a nearest-match, not a default, not a model call: a question. The
        returned prompt is the verifier-minted one, so the fallback path runs
        through exactly the same signed ASK machinery a planned question does.
        """

        if self.state.awaiting is not None:
            return self.state.awaiting.prompt
        slot = failure.ask_slot or self.active_slot
        if self.state.pending is None:
            self.request_private_slot(slot)
        slot = self.state.pending.slot
        asked = self.run_turn((ask_action(slot),))
        if asked.stop_reason is not StopReason.WAITING:
            raise AssertionError("degrading to ASK did not pause for input")
        assert self.state.awaiting is not None
        return self.state.awaiting.prompt

    # -- durability -------------------------------------------------------

    def ledgers(self) -> LedgerSnapshot:
        return self.verifier.export_ledgers(self.session_id, self.owner)

    def save(self, path: Path) -> LedgerSnapshot:
        """Write the public session file plus its signed ledger snapshot.

        The file is *not* signed as a whole. See :mod:`session_state` for the
        argument; the short version is that an envelope MAC would make the
        forged-binding acceptance test prove nothing.

        **Each export invalidates every earlier one.** Issuing a snapshot bumps
        the private monotone counter, and a restore refuses anything behind the
        high-water mark. That is what makes attack 3 (replaying an older,
        genuinely signed ledger) impossible, and its price is that "save two
        copies and restore the first" is not supported. The alternative --
        marking freshness only when a snapshot is *admitted* -- would leave a
        window in which an attacker who restores a stale snapshot before the
        legitimate owner does simply wins. Refusing the convenience was the
        cheaper trade; the constraint is filed in BACKLOG rather than hidden.
        """

        snapshot = self.ledgers()
        write_document(
            Path(path),
            session_document(
                self.session_id,
                self.owner,
                self.active_slot,
                self.state,
                self.story_state,
                snapshot,
            ),
        )
        return snapshot

    @classmethod
    def restore(
        cls, path: Path, keyring: SessionKeyRing
    ) -> tuple["ConversationSession", RestoreReport]:
        """Rebuild a session in a new process, authenticating as we go.

        Raises :class:`session_keys.KeyRingRefusal` when the *ledger* fails —
        an unknown or revoked key, a rollback, a snapshot from another
        session. Those are not partial failures: without an authentic ledger
        there is no basis for admitting anything, and proceeding with empty
        ledgers is the exact silent re-admission this item forbids.

        Individual records that fail after that are reported in the
        :class:`RestoreReport` rather than raised, so a tampered binding is
        named and skipped while the rest of the conversation continues.
        """

        document = read_document(Path(path))
        state: RetrievalState = decode(document["state"])
        story_state: StoryState = decode(document["story_state"])
        snapshot: LedgerSnapshot = decode(document["ledgers"])
        # The envelope's identity fields are convenience copies of what the
        # state already carries, and a copy that can disagree with its
        # original is a place for confusion to hide. Self-review probe E:
        # rewriting only the inner ``user_frame.owner`` left the ledger check
        # satisfied and pushed the whole disagreement onto the per-binding
        # signatures. Those did refuse it -- but "refused for the wrong stated
        # reason" is how a later reader learns the wrong invariant.
        if (
            document["session_id"] != state.session_id
            or document["owner"] != state.user_frame.owner
        ):
            raise SessionFormatError(
                "session file header disagrees with the state it carries: "
                f"header {document['owner']}/{document['session_id']}, state "
                f"{state.user_frame.owner}/{state.session_id}"
            )
        executor = FrameExecutor()
        verifier = RetrievalVerifier(EmptyStore(), executor, keyring)
        verifier.import_ledgers(
            snapshot, document["session_id"], document["owner"]
        )
        session = cls(
            state=state,
            verifier=verifier,
            story_state=story_state,
            active_slot=document["active_slot"],
        )
        admitted: list[tuple[str, str, str]] = []
        refused: list[tuple[str, str, RefusalReason]] = []
        for binding in state.user_frame.bindings:
            status = verifier.binding_status(state, binding)
            if isinstance(status, Lifetime) and status.authoritative:
                admitted.append((binding.request_id, binding.slot, status.value))
            else:
                reason = (
                    status
                    if isinstance(status, RefusalReason)
                    else RefusalReason.SUPERSEDED_BINDING
                )
                refused.append((binding.request_id, binding.slot, reason))
        report = RestoreReport(
            session_id=document["session_id"],
            owner=document["owner"],
            key_id=snapshot.key_id,
            sequence=snapshot.sequence,
            admitted=tuple(admitted),
            refused=tuple(refused),
        )
        return session, report


def golden_chicken_revision_session(
    owner: str = "interlocutor",
    keyring: SessionKeyRing | None = None,
) -> ConversationSession:
    executor = FrameExecutor()
    accepted_story = story_oracle_run().final_state
    frame = accepted_story.frame_state
    state = RetrievalState.from_unknown(
        executor,
        frame,
        "egg_color",
        "egg_color",
        Literal("the golden chicken's eggs", "color", "egg_color"),
        resolution_channel="user",
        user_owner=owner,
    )
    return ConversationSession(
        state=state,
        verifier=RetrievalVerifier(EmptyStore(), executor, keyring),
        story_state=accepted_story,
    )


def render_revision(session: ConversationSession) -> str:
    color = session.verifier.binding_value(session.state, "egg_color")
    if color is None:
        raise ValueError("egg_color has no authenticated user binding")
    accepted_story = " ".join(
        beat.text if beat.text.endswith((".", "!", "?")) else f"{beat.text}."
        for beat in session.story_state.beats
    )
    return f"{accepted_story} Now the golden chicken laid {color} eggs."


# --------------------------------------------------------------------------
# derive -> retrieve -> ask -> revise -> abstain, in ONE maintained session
# --------------------------------------------------------------------------


def maintained_lifecycle(repo_root: Path) -> tuple[str, ...]:
    """Walk all five stages of ROADMAP-v0.7 item 2's lifecycle in one session.

    One ``session_id``, one user frame, one verifier, five needs. The session
    id and the accumulated user frame are asserted to be identical at every
    stage; that is what makes it one conversation rather than five demos in a
    row. Each stage returns its own verdict line.
    """

    executor = FrameExecutor()
    spec = FrameSpec(
        frame="runtime.frames.conversation_lifecycle",
        title="One maintained conversation",
        declarations=(
            ("teller", Literal("the teller", "role", "narrator")),
        ),
        retrieval="open",
    )
    frame = executor.open_frame(spec)
    store = UnifiedKnowledgeStore.load(repo_root / "data", repo_root / "reports")
    verifier = RetrievalVerifier(store, executor)
    lines: list[str] = []

    # 1. DERIVE -- the frame already entails it; no store is consulted.
    derived = executor.check(frame, Literal("the teller", "role", "narrator"))
    lines.append(
        f"DERIVE   {derived.verdict.value}: 'the teller role' came from the "
        "frame's own declarations; no retrieval was attempted"
    )

    # 2. RETRIEVE -- a public key the corpus owns, through the miss chain.
    key = "logic.boolean_laws.de_morgan_laws"
    state = RetrievalState.from_unknown(
        executor, frame, "law", key, Literal("request", "needs", key)
    )
    session_id = state.session_id
    chain = run_miss_chain(verifier, state)
    state = chain.final_state
    rungs = ", ".join(
        f"{entry.action.argument('rung') or entry.action.kind.value}="
        f"{entry.verification.verdict.value}"
        for entry in chain.trace
    )
    lines.append(f"RETRIEVE {rungs}; context={len(state.context)} item(s)")
    bound = verifier.evaluate(state, point_action(0))
    if bound.next_state is not None:
        state = bound.next_state
    lines.append(f"POINT    {bound.verdict.value}: {bound.reason}")

    # 3. ASK -- a frame-private slot the corpus cannot own.
    private = RetrievalState.from_unknown(
        executor,
        frame,
        "tone",
        "tone",
        Literal("the retelling", "tone", "tone"),
        resolution_channel="user",
        user_owner="alice",
    )
    state = replace(private, session_id=session_id, user_frame=state.user_frame)
    session = ConversationSession(
        state=state, verifier=verifier, story_state=story_oracle_run().final_state,
        active_slot="tone",
    )
    session.say("make the tone whimsical")
    lines.append(
        f"ASK      bound tone={verifier.binding_value(session.state, 'tone')!r} "
        f"lifetime={session.lifetime_of('tone').value}"
    )

    # 4. REVISE -- a correction supersedes without erasing provenance.
    session.say("no, formal")
    provenance = tuple(
        binding.value for binding in session.state.user_frame.bindings
    )
    lines.append(
        f"REVISE   tone={verifier.binding_value(session.state, 'tone')!r}; "
        f"provenance retained {provenance}"
    )

    # 5. ABSTAIN -- every registered rung misses and no rung improvises.
    missing = "logic.boolean_laws.no_such_law_exists_anywhere"
    unanswerable = RetrievalState.from_unknown(
        executor, frame, "answer", missing, Literal("request", "needs", missing)
    )
    unanswerable = replace(
        unanswerable,
        session_id=session_id,
        user_frame=session.state.user_frame,
    )
    exhausted = run_miss_chain(verifier, unanswerable)
    lines.append(
        f"ABSTAIN  {exhausted.stop_reason.value}: context="
        f"{len(exhausted.final_state.context)}; every registered rung missed "
        f"{missing!r} and none invented material"
    )
    assert exhausted.final_state.session_id == session_id
    assert session.state.session_id == session_id
    assert session.state.frame.asserted == ()
    lines.append(
        f"SESSION  one id {session_id[:12]}... across all five stages; "
        "frame.asserted is still empty -- no testimony was promoted"
    )
    return tuple(lines)


# --------------------------------------------------------------------------
# the acceptance scenario
# --------------------------------------------------------------------------


def acceptance_scenario(workdir: Path, keyfile: Path) -> tuple[str, ...]:
    """Serialize, restart, authenticate, continue — and refuse the attacks.

    Everything after ``--- restart ---`` runs against verifiers built from a
    *reloaded* key ring, with the pre-restart verifier instances dropped. The
    only thing that crosses the boundary is the keyfile (private, on disk) and
    the two session files (public, editable by anyone).
    """

    lines: list[str] = []
    ring = SessionKeyRing.open(keyfile)
    lines.append(f"KEYRING  active={ring.active_key_id} keyfile={keyfile.name}")

    alice = golden_chicken_revision_session("alice", ring)
    bob = golden_chicken_revision_session("bob", ring)
    assert alice.story_state == bob.story_state

    alice.say("make the eggs silver")
    bob.say("in my version, make the eggs blue")
    lines.append("ALICE    'make the eggs silver'")
    lines.append(f"SYSTEM   {render_revision(alice)}")
    lines.append("BOB      'in my version, make the eggs blue'")
    lines.append(f"SYSTEM   {render_revision(bob)}")

    stale = alice.state.user_frame.bindings[-1]
    # A genuinely signed ledger from BEFORE the supersession. Kept for attack
    # 3: this is the snapshot a signature check alone cannot reject, because
    # nothing about it is forged -- it is simply out of date.
    rollback = alice.ledgers()

    alice.say("no, copper")
    lines.append("ALICE    'no, copper'")
    lines.append(f"SYSTEM   {render_revision(alice)}")

    unparseable = alice.say("make the eggs chartreuse")
    assert isinstance(unparseable.parsed, ParseFailure)
    lines.append(
        f"ALICE    'make the eggs chartreuse' -> {unparseable.parsed.reason.value}; "
        f"degraded to ASK: {unparseable.asked}"
    )
    alice.say("copper")
    lines.append("ALICE    'copper' (answering the question the parser asked)")

    alice_file = workdir / "alice.session.json"
    bob_file = workdir / "bob.session.json"
    saved = alice.save(alice_file)
    bob.save(bob_file)
    lines.append(
        f"SAVE     {alice_file.name} + {bob_file.name}; ledger sequence "
        f"{saved.sequence} (attacker holds the still-valid signature for "
        f"sequence {rollback.sequence}); no root key in either file"
    )

    # --- restart: every in-process authority is dropped here ---------------
    del alice, bob, ring
    lines.append("--- restart: new process image, verifiers discarded ---")

    reloaded = SessionKeyRing.open(keyfile)
    alice2, alice_report = ConversationSession.restore(alice_file, reloaded)
    bob2, bob_report = ConversationSession.restore(bob_file, reloaded)
    lines.append(
        f"RESTORE  alice key={alice_report.key_id} seq={alice_report.sequence} "
        f"admitted={len(alice_report.admitted)} refused={len(alice_report.refused)}"
    )
    for request_id, slot, reason in alice_report.refused:
        lines.append(f"         REFUSED {slot} {request_id[:8]}: {reason.value}")
    lines.append(f"SYSTEM   (alice, post-restart) {render_revision(alice2)}")
    lines.append(f"SYSTEM   (bob, post-restart)   {render_revision(bob2)}")
    assert alice2.session_id == alice_report.session_id
    assert alice2.story_state == bob2.story_state

    alice2.say("actually, make them gold")
    lines.append("ALICE    'actually, make them gold' (after the restart)")
    lines.append(f"SYSTEM   {render_revision(alice2)}")

    # --- attack 1: replay a stale pre-restart binding ----------------------
    surgery = replace(
        alice2.state,
        user_frame=replace(
            alice2.state.user_frame,
            bindings=(stale,),
            superseded_request_ids=(),
        ),
    )
    reason = alice2.verifier.binding_refusal(surgery, stale)
    lines.append(
        f"ATTACK   replay the pre-restart 'silver' binding with the public "
        f"supersession tuple deleted -> REFUSED {reason.value}"
    )
    assert reason is RefusalReason.SUPERSEDED_BINDING
    assert alice2.verifier.binding_value(surgery, "egg_color") is None

    # --- attack 2: forge a binding outright --------------------------------
    forged = replace(stale, value="chartreuse", signature="0" * 64)
    forged_reason = alice2.verifier.binding_refusal(alice2.state, forged)
    lines.append(
        f"ATTACK   forge a binding for egg_color -> REFUSED "
        f"{forged_reason.value}"
    )
    assert forged_reason is RefusalReason.SIGNATURE_MISMATCH

    # --- attack 3: roll the ledger back to before the supersession ---------
    # The snapshot below is authentic. Its signature verifies, its key id is
    # live, its session and owner match. The ONLY thing wrong with it is that
    # it predates the supersession -- which is exactly the class of replay a
    # MAC cannot see, and exactly what the private counter is for.
    rolled_back = workdir / "alice.rolled-back.json"
    document = read_document(alice_file)
    document["ledgers"] = encode_snapshot(rollback)
    write_document(rolled_back, document)
    try:
        ConversationSession.restore(rolled_back, SessionKeyRing.open(keyfile))
    except KeyRingRefusal as exc:
        lines.append(
            f"ATTACK   restore a genuinely signed pre-supersession ledger "
            f"(seq {rollback.sequence} < {saved.sequence}) -> REFUSED "
            f"{exc.reason.value}"
        )
        assert exc.reason is RefusalReason.LEDGER_ROLLBACK
    else:  # pragma: no cover - the attack must not succeed
        raise AssertionError("ledger rollback was admitted")

    # --- attack 4: revoke the key and try again ----------------------------
    # On a copy of the keyfile: revocation is destructive by design, and a
    # demo that bricked the operator's real ring would be a bug, not a proof.
    revoked_keyfile = workdir / "revoked-keys.json"
    revoked_keyfile.write_text(keyfile.read_text(encoding="utf-8"), encoding="utf-8")
    revoking = SessionKeyRing.open(revoked_keyfile)
    revoking.revoke(revoking.active_key_id)
    try:
        ConversationSession.restore(alice_file, revoking)
    except KeyRingRefusal as exc:
        lines.append(
            f"ATTACK   restore under a revoked key -> REFUSED {exc.reason.value}"
        )
        assert exc.reason is RefusalReason.REVOKED_KEY_ID
    else:  # pragma: no cover - the attack must not succeed
        raise AssertionError("a revoked key restored a session")

    lines.append(
        "STATUS   owner-isolated bindings survived a real process boundary; "
        "the story was never asserted; every stale, forged, rolled-back, and "
        "revoked path was refused by name"
    )
    return tuple(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keyfile",
        type=Path,
        help="runtime-owned root keyfile (default: a temporary one)",
    )
    parser.add_argument(
        "--lifecycle",
        action="store_true",
        help="also walk derive -> retrieve -> ask -> revise -> abstain",
    )
    args = parser.parse_args()

    print("LIFETIME PROTOCOL")
    for name, may_declare, authoritative_while, becomes in LIFETIME_PROTOCOL:
        declared = "declarable" if may_declare else "computed"
        print(f"  {name:<11} ({declared}) authoritative while {authoritative_while}")
        print(f"  {'':<11}  -> {becomes}")
    print()

    with tempfile.TemporaryDirectory() as raw:
        workdir = Path(raw)
        keyfile = args.keyfile or (workdir / "session-keys.json")
        for line in acceptance_scenario(workdir, keyfile):
            print(line)

    if args.lifecycle:
        print()
        for line in maintained_lifecycle(Path(__file__).resolve().parent.parent):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
