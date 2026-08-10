"""ROADMAP-v0.7 item 2: conversation survives process boundaries.

Every test here is an attack or the acceptance scenario. The organising rule is
the repo's law that the author's fix is the unprobed boundary: each mechanism
built for this item gets a test that tries to defeat *that* mechanism, not a
test that watches it work.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from controller import Verdict  # noqa: E402
from conversation import (  # noqa: E402
    ConversationSession,
    acceptance_scenario,
    golden_chicken_revision_session,
    maintained_lifecycle,
    render_revision,
)
from frames import FrameSpec, FrameState, Literal  # noqa: E402
from lifetimes import (  # noqa: E402
    LIFETIME_PROTOCOL,
    Lifetime,
    belief_frame_lifetime,
    declarable,
)
from retrieval import UserBinding, ask_action  # noqa: E402
from session_keys import (  # noqa: E402
    KeyRingRefusal,
    KeyStatus,
    RefusalReason,
    SessionKeyRing,
    hkdf_sha256,
)
from session_state import (  # noqa: E402
    SessionFormatError,
    decode,
    encode,
    read_document,
    write_document,
)


class DurableFixture(unittest.TestCase):
    """A saved Alice session with one superseded answer, ready to attack."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.workdir = Path(self._tmp.name)
        self.keyfile = self.workdir / "keys.json"
        self.ring = SessionKeyRing.open(self.keyfile)

    def saved_alice(self) -> tuple[Path, UserBinding, ConversationSession]:
        alice = golden_chicken_revision_session("alice", self.ring)
        alice.say("make the eggs silver")
        stale = alice.state.user_frame.bindings[-1]
        alice.say("no, copper")
        path = self.workdir / "alice.session.json"
        alice.save(path)
        return path, stale, alice


class AcceptanceScenarioTests(DurableFixture):
    def test_acceptance_scenario_runs_end_to_end(self) -> None:
        """P-DS1/P-DS2/P-DS3/P-DS5: the release gate, as one transcript."""

        lines = acceptance_scenario(self.workdir, self.workdir / "gate.json")
        transcript = "\n".join(lines)
        self.assertIn("--- restart", transcript)
        self.assertIn("binding-superseded", transcript)
        self.assertIn("signature-mismatch", transcript)
        self.assertIn("ledger-rollback", transcript)
        self.assertIn("revoked-key-id", transcript)
        self.assertIn("copper eggs", transcript)
        self.assertIn("blue eggs", transcript)
        self.assertIn("gold eggs", transcript)

    def test_restart_keeps_owners_isolated_and_the_story_unasserted(self) -> None:
        alice = golden_chicken_revision_session("alice", self.ring)
        bob = golden_chicken_revision_session("bob", self.ring)
        public_story = alice.story_state
        alice.say("make the eggs silver")
        bob.say("in my version, make the eggs blue")
        alice_file = self.workdir / "a.json"
        bob_file = self.workdir / "b.json"
        alice.save(alice_file)
        bob.save(bob_file)

        reloaded = SessionKeyRing.open(self.keyfile)
        alice2, _ = ConversationSession.restore(alice_file, reloaded)
        bob2, _ = ConversationSession.restore(bob_file, reloaded)

        self.assertEqual(alice2.session_id, alice.session_id)
        self.assertEqual(alice2.story_state, public_story)
        self.assertEqual(bob2.story_state, public_story)
        self.assertIn("silver eggs", render_revision(alice2))
        self.assertNotIn("blue eggs", render_revision(alice2))
        self.assertIn("blue eggs", render_revision(bob2))
        self.assertEqual(alice2.state.frame.asserted, ())
        # Bob's binding must not authenticate inside Alice's restored session.
        bob_binding = bob2.state.user_frame.bindings[-1]
        self.assertIs(
            alice2.verifier.binding_refusal(alice2.state, bob_binding),
            RefusalReason.SIGNATURE_MISMATCH,
        )

    def test_restart_continues_revising(self) -> None:
        path, _stale, _alice = self.saved_alice()
        restored, _ = ConversationSession.restore(
            path, SessionKeyRing.open(self.keyfile)
        )
        restored.say("actually, make them gold")
        self.assertTrue(render_revision(restored).endswith("gold eggs."))
        self.assertEqual(
            [binding.value for binding in restored.state.user_frame.bindings],
            ["silver", "copper", "gold"],
        )

    def test_one_maintained_session_walks_all_five_stages(self) -> None:
        lines = maintained_lifecycle(ROOT)
        joined = "\n".join(lines)
        for stage in ("DERIVE", "RETRIEVE", "ASK", "REVISE", "ABSTAIN"):
            self.assertIn(stage, joined)
        self.assertIn("VERIFIED", lines[0])
        self.assertIn("context=0", joined)
        self.assertIn("frame.asserted is still empty", joined)


class PreRestartBindingTests(DurableFixture):
    def test_stale_pre_restart_binding_is_refused_by_name(self) -> None:
        """P-DS2, half one: superseded before the snapshot, dead after it."""

        path, stale, _ = self.saved_alice()
        restored, report = ConversationSession.restore(
            path, SessionKeyRing.open(self.keyfile)
        )
        self.assertIs(
            report.refusal_for(stale.request_id),
            RefusalReason.SUPERSEDED_BINDING,
        )
        surgery = replace(
            restored.state,
            user_frame=replace(
                restored.state.user_frame,
                bindings=(stale,),
                superseded_request_ids=(),
            ),
        )
        self.assertIs(
            restored.verifier.binding_refusal(surgery, stale),
            RefusalReason.SUPERSEDED_BINDING,
        )
        self.assertIsNone(restored.verifier.binding_value(surgery, "egg_color"))

    def test_forged_pre_restart_binding_is_refused_by_name(self) -> None:
        """P-DS2, half two -- and it must fail on the *binding*, not the file.

        The forgery is written into the session file and the file is read back
        normally. Nothing rejects the document; the restore succeeds. What
        refuses is the binding's own signature, which is the property item 2
        claims and the reason the envelope carries no MAC.
        """

        path, _stale, _ = self.saved_alice()
        document = read_document(path)
        state = decode(document["state"])
        genuine = state.user_frame.bindings[-1]
        forged = replace(genuine, value="chartreuse", signature="0" * 64)
        document["state"] = encode(
            replace(
                state,
                user_frame=replace(
                    state.user_frame,
                    bindings=state.user_frame.bindings + (forged,),
                ),
            )
        )
        write_document(path, document)

        restored, report = ConversationSession.restore(
            path, SessionKeyRing.open(self.keyfile)
        )
        self.assertIs(
            report.refusal_for(forged.request_id),
            RefusalReason.SIGNATURE_MISMATCH,
        )
        self.assertEqual(
            restored.verifier.binding_value(restored.state, "egg_color"),
            "copper",
        )

    def test_consumed_reply_replayed_after_restart_is_refused(self) -> None:
        """P-DS3: the consumed-request ledger crosses the boundary."""

        alice = golden_chicken_revision_session("alice", self.ring)
        alice.run_turn((ask_action("egg_color"),))
        asked_state = alice.state
        reply = alice.verifier.reply_action(asked_state, "silver")
        alice.run_turn((reply,))
        path = self.workdir / "alice.json"
        alice.save(path)

        restored, _ = ConversationSession.restore(
            path, SessionKeyRing.open(self.keyfile)
        )
        outcome = restored.verifier.evaluate(asked_state, reply)
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("already consumed", outcome.reason)
        self.assertIsNone(outcome.next_state)

    def test_restore_without_a_ledger_is_refused_not_defaulted(self) -> None:
        """The §3.3 failure mode: keys carried forward, ledgers re-minted empty."""

        path, _stale, _ = self.saved_alice()
        document = read_document(path)
        del document["ledgers"]
        write_document(path, document)
        with self.assertRaises(SessionFormatError) as caught:
            ConversationSession.restore(path, SessionKeyRing.open(self.keyfile))
        self.assertIn("re-admit consumed requests", str(caught.exception))


class LedgerAttackTests(DurableFixture):
    def test_ledger_rollback_is_refused(self) -> None:
        """P-DS5: an authentic snapshot, replayed out of order."""

        alice = golden_chicken_revision_session("alice", self.ring)
        alice.say("make the eggs silver")
        early = alice.ledgers()
        alice.say("no, copper")
        path = self.workdir / "alice.json"
        current = alice.save(path)
        self.assertGreater(current.sequence, early.sequence)

        document = read_document(path)
        document["ledgers"] = encode(early)
        rolled = self.workdir / "rolled.json"
        write_document(rolled, document)
        with self.assertRaises(KeyRingRefusal) as caught:
            ConversationSession.restore(rolled, SessionKeyRing.open(self.keyfile))
        self.assertIs(caught.exception.reason, RefusalReason.LEDGER_ROLLBACK)

    def test_truncated_ledger_is_refused_as_a_forgery(self) -> None:
        """Dropping entries is not rollback; it is tampering, and the MAC sees it."""

        path, _stale, _ = self.saved_alice()
        document = read_document(path)
        snapshot = decode(document["ledgers"])
        self.assertTrue(snapshot.superseded)
        document["ledgers"] = encode(replace(snapshot, superseded=()))
        truncated = self.workdir / "truncated.json"
        write_document(truncated, document)
        with self.assertRaises(KeyRingRefusal) as caught:
            ConversationSession.restore(
                truncated, SessionKeyRing.open(self.keyfile)
            )
        self.assertIs(caught.exception.reason, RefusalReason.SIGNATURE_MISMATCH)

    def test_forged_ledger_cannot_advance_the_counter(self) -> None:
        """Signature before sequence, or a forgery becomes a denial of service.

        If the counter were bumped before the MAC was checked, anyone able to
        write the session file could stamp sequence 10**9 and lock the real
        owner out forever. The check order in ``import_ledgers`` is what stops
        that, so it gets a test rather than a comment.
        """

        path, _stale, _ = self.saved_alice()
        document = read_document(path)
        snapshot = decode(document["ledgers"])
        document["ledgers"] = encode(
            replace(snapshot, sequence=10**9, signature="0" * 64)
        )
        poisoned = self.workdir / "poisoned.json"
        write_document(poisoned, document)
        ring = SessionKeyRing.open(self.keyfile)
        before = ring.high_water(f"session:{snapshot.session_id}")
        with self.assertRaises(KeyRingRefusal) as caught:
            ConversationSession.restore(poisoned, ring)
        self.assertIs(caught.exception.reason, RefusalReason.SIGNATURE_MISMATCH)
        self.assertEqual(ring.high_water(f"session:{snapshot.session_id}"), before)
        # The genuine file still restores.
        ConversationSession.restore(path, ring)

    def test_header_may_not_disagree_with_the_state_it_carries(self) -> None:
        """Self-review probe E: a rewritten inner owner must not slide through.

        The per-binding signatures already refused it, but they refused it as
        a *forgery* when the real defect was an inconsistent envelope. A
        refusal with the wrong stated reason teaches the next reader the wrong
        invariant, so the disagreement is now named where it happens.
        """

        path, _stale, _ = self.saved_alice()
        document = read_document(path)
        state = decode(document["state"])
        document["state"] = encode(
            replace(
                state,
                user_frame=replace(state.user_frame, owner="mallory"),
            )
        )
        swapped = self.workdir / "reowned.json"
        write_document(swapped, document)
        with self.assertRaisesRegex(SessionFormatError, "disagrees"):
            ConversationSession.restore(swapped, SessionKeyRing.open(self.keyfile))

    def test_rewriting_only_the_header_owner_is_refused(self) -> None:
        path, _stale, _ = self.saved_alice()
        document = read_document(path)
        document["owner"] = "mallory"
        swapped = self.workdir / "reheaded.json"
        write_document(swapped, document)
        with self.assertRaises(SessionFormatError):
            ConversationSession.restore(swapped, SessionKeyRing.open(self.keyfile))

    def test_public_supersession_can_kill_but_never_resurrect(self) -> None:
        """Self-review probe F, recorded as a limit rather than fixed.

        Anyone who can write the session file can *add* a request id to the
        public ``superseded_request_ids`` tuple and retire a live binding. That
        is a denial of service on unsigned public state and it is inherent —
        the same attacker could simply delete the binding. What they cannot do
        is the opposite, which is the property that matters: removing entries
        resurrects nothing, because the private ledger is consulted first.
        """

        alice = golden_chicken_revision_session("alice", self.ring)
        alice.say("make the eggs silver")
        live = alice.state.user_frame.bindings[-1]
        censored = replace(
            alice.state,
            user_frame=replace(
                alice.state.user_frame, superseded_request_ids=(live.request_id,)
            ),
        )
        self.assertIs(
            alice.verifier.binding_refusal(censored, live),
            RefusalReason.SUPERSEDED_BINDING,
        )
        alice.say("no, copper")
        stale = live
        resurrected = replace(
            alice.state,
            user_frame=replace(
                alice.state.user_frame,
                bindings=(stale,),
                superseded_request_ids=(),
            ),
        )
        self.assertIs(
            alice.verifier.binding_refusal(resurrected, stale),
            RefusalReason.SUPERSEDED_BINDING,
        )

    def test_ledger_cannot_be_moved_to_another_session(self) -> None:
        path, _stale, _ = self.saved_alice()
        other = golden_chicken_revision_session("mallory", self.ring)
        other.say("make the eggs blue")
        other_path = self.workdir / "mallory.json"
        other.save(other_path)

        document = read_document(other_path)
        document["ledgers"] = read_document(path)["ledgers"]
        swapped = self.workdir / "swapped.json"
        write_document(swapped, document)
        with self.assertRaises(KeyRingRefusal) as caught:
            ConversationSession.restore(swapped, SessionKeyRing.open(self.keyfile))
        self.assertIs(caught.exception.reason, RefusalReason.SESSION_MISMATCH)

    def test_restore_then_supersede_then_replay_the_first_file(self) -> None:
        """Restore-then-supersede ordering, probed from both directions.

        The interesting half is the second: after the restored session
        supersedes ``copper``, the *original* file -- which was authentic when
        it was written -- must no longer restore, because its ledger predates
        the new supersession. Otherwise "save, restore, revise, restore the old
        save" is a supported way to resurrect a replaced answer.
        """

        path, stale, _ = self.saved_alice()
        restored, _ = ConversationSession.restore(
            path, SessionKeyRing.open(self.keyfile)
        )
        restored.say("actually, make them gold")
        second = self.workdir / "alice.2.json"
        restored.save(second)

        again, report = ConversationSession.restore(
            second, SessionKeyRing.open(self.keyfile)
        )
        self.assertEqual(again.verifier.binding_value(again.state, "egg_color"), "gold")
        self.assertIs(
            report.refusal_for(stale.request_id), RefusalReason.SUPERSEDED_BINDING
        )
        self.assertEqual(len(report.admitted), 1)

        with self.assertRaises(KeyRingRefusal) as caught:
            ConversationSession.restore(path, SessionKeyRing.open(self.keyfile))
        self.assertIs(caught.exception.reason, RefusalReason.LEDGER_ROLLBACK)


class KeyIdentityTests(DurableFixture):
    def test_rotation_keeps_old_material_verifiable(self) -> None:
        path, _stale, _ = self.saved_alice()
        ring = SessionKeyRing.open(self.keyfile)
        first = ring.active_key_id
        second = ring.rotate()
        self.assertNotEqual(first, second)
        self.assertIs(ring.status(first), KeyStatus.RETIRED)
        self.assertIs(ring.status(second), KeyStatus.ACTIVE)

        restored, _ = ConversationSession.restore(path, ring)
        self.assertEqual(
            restored.verifier.binding_value(restored.state, "egg_color"), "copper"
        )
        restored.say("actually, make them gold")
        newest = restored.state.user_frame.bindings[-1]
        self.assertEqual(newest.key_id, second)
        self.assertEqual(
            restored.verifier.binding_value(restored.state, "egg_color"), "gold"
        )

    def test_key_id_confusion_between_rotated_keys_is_refused(self) -> None:
        """Relabelling a binding with a live generation must not launder it."""

        path, _stale, _ = self.saved_alice()
        ring = SessionKeyRing.open(self.keyfile)
        original = ring.active_key_id
        rotated = ring.rotate()
        restored, _ = ConversationSession.restore(path, ring)
        genuine = restored.state.user_frame.bindings[-1]
        self.assertEqual(genuine.key_id, original)

        relabelled = replace(genuine, key_id=rotated)
        self.assertIs(
            restored.verifier.binding_refusal(restored.state, relabelled),
            RefusalReason.SIGNATURE_MISMATCH,
        )
        unknown = replace(genuine, key_id="k-does-not-exist")
        self.assertIs(
            restored.verifier.binding_refusal(restored.state, unknown),
            RefusalReason.UNKNOWN_KEY_ID,
        )
        ring.revoke(original)
        self.assertIs(
            restored.verifier.binding_refusal(restored.state, genuine),
            RefusalReason.REVOKED_KEY_ID,
        )

    def test_revoked_key_refuses_the_whole_restore(self) -> None:
        path, _stale, _ = self.saved_alice()
        ring = SessionKeyRing.open(self.keyfile)
        ring.revoke(ring.active_key_id)
        with self.assertRaises(KeyRingRefusal) as caught:
            ConversationSession.restore(path, ring)
        self.assertIs(caught.exception.reason, RefusalReason.REVOKED_KEY_ID)

    def test_an_unrelated_keyring_cannot_restore(self) -> None:
        path, _stale, _ = self.saved_alice()
        stranger = SessionKeyRing.open(self.workdir / "stranger.json")
        with self.assertRaises(KeyRingRefusal) as caught:
            ConversationSession.restore(path, stranger)
        self.assertIs(caught.exception.reason, RefusalReason.UNKNOWN_KEY_ID)

    def test_default_verifiers_still_hold_unrelated_ephemeral_keys(self) -> None:
        """P-DS4's mechanism: the default is per-instance, never process-global."""

        one = golden_chicken_revision_session("alice")
        two = golden_chicken_revision_session("alice")
        self.assertNotEqual(one.verifier.key_id, two.verifier.key_id)
        one.say("make the eggs silver")
        lifted = one.state.user_frame.bindings[-1]
        self.assertIs(
            two.verifier.binding_refusal(one.state, lifted),
            RefusalReason.UNKNOWN_KEY_ID,
        )

    def test_derivation_separates_scope_and_domain(self) -> None:
        ring = SessionKeyRing.open(self.keyfile)
        key = ring.active_key_id
        base = ring.derive(key, "session:a", "binding")
        self.assertNotEqual(base, ring.derive(key, "session:b", "binding"))
        self.assertNotEqual(base, ring.derive(key, "session:a", "receipt"))
        self.assertEqual(base, ring.derive(key, "session:a", "binding"))
        self.assertEqual(len(base), 32)
        # A second root produces unrelated keys for the identical scope/domain.
        other = SessionKeyRing.open(self.workdir / "other.json")
        self.assertNotEqual(
            base, other.derive(other.active_key_id, "session:a", "binding")
        )

    def test_hkdf_expands_past_one_block(self) -> None:
        long = hkdf_sha256(b"secret", b"salt", b"info", 64)
        self.assertEqual(len(long), 64)
        self.assertEqual(long[:32], hkdf_sha256(b"secret", b"salt", b"info", 32))

    def test_keyfile_never_contains_a_session_secret(self) -> None:
        """The separation the whole item rests on, asserted rather than asserted-to."""

        path, _stale, _ = self.saved_alice()
        session_text = path.read_text(encoding="utf-8")
        keys = json.loads(self.keyfile.read_text(encoding="utf-8"))
        for record in keys["keys"]:
            self.assertNotIn(record["secret"], session_text)
        self.assertNotIn("secret", session_text)


class LifetimeProtocolTests(DurableFixture):
    def test_protocol_table_matches_the_enum(self) -> None:
        named = {row[0] for row in LIFETIME_PROTOCOL}
        self.assertEqual(named, {member.value for member in Lifetime})
        for name, may_declare, _, _ in LIFETIME_PROTOCOL:
            self.assertEqual(Lifetime(name).declarable, may_declare)

    def test_effective_lifetimes_cannot_be_declared(self) -> None:
        for name in ("superseded", "expired"):
            with self.assertRaisesRegex(ValueError, "effective lifetime"):
                declarable(name)
        with self.assertRaisesRegex(ValueError, "unregistered lifetime"):
            declarable("forever")

    def test_declared_lifetime_is_signed_not_editable(self) -> None:
        alice = golden_chicken_revision_session("alice", self.ring)
        alice.say("make the eggs silver")
        binding = alice.state.user_frame.bindings[-1]
        self.assertEqual(binding.lifetime, Lifetime.SESSION.value)
        promoted = replace(binding, lifetime=Lifetime.DURABLE.value)
        self.assertIs(
            alice.verifier.binding_refusal(alice.state, promoted),
            RefusalReason.SIGNATURE_MISMATCH,
        )
        nonsense = replace(binding, lifetime="superseded")
        self.assertIs(
            alice.verifier.binding_refusal(alice.state, nonsense),
            RefusalReason.UNDECLARABLE_LIFETIME,
        )

    def test_goal_local_binding_expires_when_the_slot_reopens(self) -> None:
        alice = golden_chicken_revision_session("alice", self.ring)
        alice.say("for now, make the eggs silver")
        binding = alice.state.user_frame.bindings[-1]
        self.assertEqual(binding.lifetime, Lifetime.GOAL_LOCAL.value)
        self.assertIs(
            alice.verifier.binding_status(alice.state, binding),
            Lifetime.GOAL_LOCAL,
        )
        alice.request_private_slot("egg_color")
        alice.run_turn((ask_action("egg_color"),))
        self.assertIs(
            alice.verifier.binding_status(alice.state, binding),
            RefusalReason.EXPIRED_BINDING,
        )
        self.assertIsNone(alice.verifier.binding_value(alice.state, "egg_color"))

    def test_durable_binding_crosses_sessions_and_session_binding_does_not(
        self,
    ) -> None:
        alice = golden_chicken_revision_session("alice", self.ring)
        alice.say("always make the eggs copper")
        durable = alice.state.user_frame.bindings[-1]
        self.assertEqual(durable.lifetime, Lifetime.DURABLE.value)

        alice.request_private_slot("tone")
        alice.say("make the tone whimsical")
        session_bound = alice.state.user_frame.bindings[-1]

        later = golden_chicken_revision_session("alice", self.ring)
        carried = replace(
            later.state,
            user_frame=replace(
                later.state.user_frame,
                bindings=(durable, session_bound),
            ),
        )
        self.assertNotEqual(later.session_id, alice.session_id)
        self.assertIs(
            later.verifier.binding_status(carried, durable), Lifetime.DURABLE
        )
        self.assertEqual(later.verifier.binding_value(carried, "egg_color"), "copper")
        self.assertIs(
            later.verifier.binding_refusal(carried, session_bound),
            RefusalReason.SIGNATURE_MISMATCH,
        )

    def test_durable_binding_is_owner_scoped_not_owner_free(self) -> None:
        alice = golden_chicken_revision_session("alice", self.ring)
        alice.say("always make the eggs copper")
        durable = alice.state.user_frame.bindings[-1]
        mallory = golden_chicken_revision_session("mallory", self.ring)
        stolen = replace(
            mallory.state,
            user_frame=replace(
                mallory.state.user_frame, bindings=(durable,)
            ),
        )
        self.assertIs(
            mallory.verifier.binding_refusal(stolen, durable),
            RefusalReason.SIGNATURE_MISMATCH,
        )

    def test_durable_supersession_is_filed_under_the_owner_scope(self) -> None:
        """Otherwise a durable answer replaced in session A revives in session B."""

        alice = golden_chicken_revision_session("alice", self.ring)
        alice.say("always make the eggs copper")
        first = alice.state.user_frame.bindings[-1]
        alice.say("no, always make the eggs gold")
        second = alice.state.user_frame.bindings[-1]

        later = golden_chicken_revision_session("alice", self.ring)
        carried = replace(
            later.state,
            user_frame=replace(
                later.state.user_frame, bindings=(first, second)
            ),
        )
        self.assertIs(
            later.verifier.binding_refusal(carried, first),
            RefusalReason.SUPERSEDED_BINDING,
        )
        self.assertEqual(later.verifier.binding_value(carried, "egg_color"), "gold")

    def test_belief_frames_answer_in_the_same_vocabulary(self) -> None:
        open_frame = FrameState(spec=FrameSpec(frame="runtime.frames.open"))
        self.assertIs(belief_frame_lifetime(open_frame), Lifetime.SESSION)
        self.assertIs(
            belief_frame_lifetime(replace(open_frame, closed=True)),
            Lifetime.EXPIRED,
        )
        corpus = FrameState(
            spec=FrameSpec(frame="corpus.frames.x", corpus_backed=True)
        )
        self.assertIs(belief_frame_lifetime(corpus), Lifetime.DURABLE)
        nested = FrameState(
            spec=FrameSpec(frame="runtime.frames.sally", owner="sally"),
            children=(
                ("anne", FrameState(spec=FrameSpec(frame="runtime.frames.anne"))),
            ),
        )
        self.assertIs(belief_frame_lifetime(nested), Lifetime.GOAL_LOCAL)
        # One replaced premise does not expire the frame that holds it.
        premise = replace(open_frame, superseded_declarations=("golden",))
        self.assertIs(belief_frame_lifetime(premise), Lifetime.SESSION)


class SessionCodecTests(DurableFixture):
    def test_codec_round_trips_the_whole_state(self) -> None:
        path, _stale, alice = self.saved_alice()
        document = read_document(path)
        self.assertEqual(decode(document["state"]), alice.state)
        self.assertEqual(decode(document["story_state"]), alice.story_state)

    def test_codec_refuses_unregistered_types_and_fields(self) -> None:
        with self.assertRaises(SessionFormatError):
            encode({"a": 1})
        with self.assertRaises(SessionFormatError):
            encode([1, 2])
        with self.assertRaises(SessionFormatError):
            decode({"$": "os.system", "f": {}})
        with self.assertRaises(SessionFormatError):
            decode({"$": "Literal", "f": {"subject": "a", "smuggled": "b"}})
        with self.assertRaises(SessionFormatError):
            decode("untagged-object" if False else {"no-tag": 1})

    def test_codec_preserves_tuple_identity(self) -> None:
        literal = Literal("a", "b", "c")
        self.assertEqual(decode(encode((literal,))), (literal,))
        self.assertIsInstance(decode(encode((literal,))), tuple)

    def test_wrong_schema_is_named(self) -> None:
        path, _stale, _ = self.saved_alice()
        document = read_document(path)
        document["schema"] = "corollary.session/999"
        write_document(path, document)
        with self.assertRaisesRegex(SessionFormatError, "expected"):
            read_document(path)


if __name__ == "__main__":
    unittest.main()
