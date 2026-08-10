"""Adjudication of the Phase-1 offline core session kernel (v0.8 item 1, slice 1).

Registered predictions. These entries are quoted from
``docs/DESIGN-interactive-harness.md`` §10, where they were registered on
2026-08-09 *before* any harness implementation. They are restated here verbatim
so the adjudicating tests sit beside the claim they decide, per the house rule
that a prediction is registered before it is adjudicated and its text is never
silently narrowed. If a leg needs an OFF subsystem, the correct response is to
mark the prediction MISSED and append a correction, not to edit the claim.

P-IH1 — Offline core session. *(prediction)* With WordNet/Lean/Torch OFF, a
    single session can still open a fiction frame, bind a private slot via
    WAITING, answer a visibility-derived belief query, and retrieve a corpus
    twin. If any of those requires an optional subsystem, the prediction text is
    wrong and must be corrected — not the offline claim silently narrowed.
    Adjudicated by a session with the optional probes forced OFF that drives all
    four legs in one session object, asserting no optional subsystem is
    registered, with COROLLARY_WORDNET unset. Miss if any leg needs an OFF
    subsystem or a second session.

P-IH2 — Every pausing subsystem can state its own need. *(prediction —
    strengthened)* Every subsystem that can pause must supply a
    human-presentable need record through the same typed channel, and the shell
    must render it without any subsystem-specific knowledge — no retrieval-shaped
    special case. Miss if the loop must branch on subsystem id to phrase a
    question, or if a non-retrieval subsystem can reach WAITING with no prompt
    the shell can render.

P-IH5 — Boot matrix honesty. *(prediction)* Startup output marks WordNet OFF
    when no archive is configured; naming a missing archive FAILs that probe
    rather than silently equating to OFF (preserves the loud named-path
    behavior).

Adjudications (recorded after implementation):
  P-IH1: FIRED — all four legs run in one offline session with zero optional
         subsystems registered (``test_p_ih1_*``).
  P-IH2: FIRED — a non-retrieval pausing subsystem reaches WAITING with a
         prompt, and the one ``render_need`` renders it and the retrieval
         ClarificationRequest through an identical, subsystem-blind path
         (``test_p_ih2_*``).
  P-IH5: FIRED — WordNet probes OFF when unset, OK when the named archive
         exists, and FAIL (not OFF) when a named archive is missing
         (``test_p_ih5_*``).
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import dataclass, replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    Controller,
    RunResult,
    SequencePolicy,
    StopReason,
    Verdict,
    Verification,
)
from frames import FrameExecutor, FrameSpec, Literal  # noqa: E402
from harness import (  # noqa: E402
    OPTIONAL_SUBSYSTEMS,
    CoreSession,
    Liveness,
    Need,
    pending_need,
    probe_corpus,
    probe_wordnet,
    render_need,
    render_stop,
)
from retrieval import RetrievalState, RetrievalVerifier, ask_action  # noqa: E402


def _twin_member_key() -> str:
    """A committed statement id that participates in a structural twin group.

    Read from the report at test time rather than hardcoded, so the corpus-twin
    leg is robust to seed regeneration rather than pinned to one theorem.
    """

    import json

    report = json.loads(
        (REPO_ROOT / "reports" / "signature_matches.json").read_text(
            encoding="utf-8"
        )
    )
    for field in ("typed_twin_groups", "mirror_twin_groups"):
        for group in report.get(field, []):
            members = group.get("members", [])
            if members:
                return members[0]["statement_id"]
    raise unittest.SkipTest("no twin group in signature_matches.json")


class BootMatrixTests(unittest.TestCase):
    def test_offline_boot_registers_no_optional_subsystem(self) -> None:
        session = CoreSession.boot(REPO_ROOT, offline=True)
        self.assertEqual(session.matrix.registered_optional_ids(), ())
        for subsystem_id in OPTIONAL_SUBSYSTEMS:
            record = session.matrix.get(subsystem_id)
            self.assertTrue(record.optional)
            self.assertIs(record.liveness, Liveness.OFF)
            self.assertFalse(record.registered)

    def test_required_subsystems_register_offline(self) -> None:
        session = CoreSession.boot(REPO_ROOT, offline=True)
        registered = set(session.matrix.registered_ids())
        for required in ("corpus.nodes", "narrative.story", "belief.ownership"):
            self.assertIn(required, registered)

    def test_liveness_is_not_the_verdict_palette(self) -> None:
        # docs §3.2: the boot matrix is a liveness channel, disjoint from the
        # verdict palette; a green matrix is not a soundness claim.
        liveness_values = {member.value for member in Liveness}
        verdict_values = {member.value for member in Verdict}
        self.assertFalse(liveness_values & verdict_values)

    def test_boot_lines_render_without_verdict_glyphs(self) -> None:
        session = CoreSession.boot(REPO_ROOT, offline=True)
        lines = session.matrix.render()
        self.assertTrue(any("corpus.nodes" in line for line in lines))
        self.assertTrue(lines[-1].startswith("registered paths:"))


class PIH1OfflineCoreSession(unittest.TestCase):
    """P-IH1: one offline session drives all four legs, no optional subsystem."""

    def setUp(self) -> None:
        # COROLLARY_WORDNET is not consulted at all under offline=True; the
        # prediction's "unset" condition is satisfied a fortiori.
        self.session = CoreSession.boot(REPO_ROOT, offline=True)

    def test_no_optional_subsystem_registered(self) -> None:
        self.assertEqual(self.session.matrix.registered_optional_ids(), ())

    def test_all_four_legs_in_one_session_object(self) -> None:
        s = self.session
        session_id = s.session_id

        # Leg 1+2: open a fiction frame and bind a private slot via WAITING.
        s.open_fiction_slot(
            "egg_color",
            Literal("the golden chicken's eggs", "color", "egg_color"),
        )
        asked = s.ask("egg_color")
        self.assertIs(asked.stop_reason, StopReason.WAITING)
        assert s.state is not None and s.state.awaiting is not None
        self.assertIn("egg_color", s.state.awaiting.prompt)
        answered = s.answer("silver")
        self.assertTrue(answered.solved)
        self.assertEqual(s.binding("egg_color"), "silver")
        # Testimony never entered the accepted story.
        self.assertEqual(s.state.frame.asserted, ())

        # Leg 3: a visibility-derived belief query.
        believed, actual = s.false_belief_query("marble", "located_in")
        self.assertEqual((believed, actual), ("basket", "box"))

        # Leg 4: retrieve a corpus twin.
        run = s.retrieve(_twin_member_key())
        self.assertTrue(run.final_state.context)
        self.assertTrue(
            any(m.item.source == "twin_ledger" for m in run.final_state.context)
        )

        # One session object, one id, throughout.
        self.assertEqual(s.session_id, session_id)
        self.assertEqual(s.state.session_id, session_id)
        # Still no optional subsystem was needed to do any of it.
        self.assertEqual(s.matrix.registered_optional_ids(), ())

    def test_no_second_session_was_constructed(self) -> None:
        # The verifier instance is shared across the ASK and RETRIEVE legs; a
        # second RetrievalVerifier would be a second authority (P-IH1 "or a
        # second session"). The retrieve leg must reuse self.verifier.
        s = self.session
        s.open_fiction_slot(
            "egg_color",
            Literal("the golden chicken's eggs", "color", "egg_color"),
        )
        s.ask("egg_color")
        s.answer("silver")
        verifier_before = s.verifier
        s.retrieve(_twin_member_key())
        self.assertIs(s.verifier, verifier_before)


# -- P-IH2: a second, non-retrieval pausing subsystem ----------------------


@dataclass(frozen=True)
class BeatNeed:
    """A pause record from a non-retrieval subsystem.

    Structurally a :class:`harness.Need` (slot + prompt) and NOTHING a renderer
    could branch on — no subsystem id, no verifier handle. That is the whole
    point: the shell renders it with the same code that renders retrieval's
    question.
    """

    slot: str
    prompt: str


@dataclass(frozen=True)
class ObligationState:
    """A narrative-obligation subsystem's state; may hold an outstanding need."""

    awaiting: BeatNeed | None = None
    discharged: bool = False


class ObligationVerifier:
    """A minimal non-retrieval subsystem that can pause for input.

    It shares nothing with retrieval except the kernel contract: propose ASK,
    the verifier mints a need on the state, the controller stops WAITING via the
    same ``is_waiting`` predicate. There is no ClarificationRequest, no HMAC, no
    store — just a different subsystem that legitimately needs to ask a human.
    """

    name = "narrative.obligation"

    def state_key(self, state: ObligationState) -> str:
        return repr(state)

    def evaluate(
        self, state: ObligationState, action: Action
    ) -> Verification[ObligationState]:
        if action.kind is ActionKind.ASK and action.name == "raise_need":
            slot = action.argument("slot") or ""
            need = BeatNeed(
                slot,
                f"Which beat discharges the {slot!r} obligation?",
            )
            return Verification(
                Verdict.VERIFIED,
                "obligation cannot be discharged without a chosen beat",
                replace(state, awaiting=need),
            )
        return Verification(
            Verdict.REFUSED,
            f"obligation subsystem does not offer {action.name!r}",
            evidence=(self.name,),
        )


class PIH2SubsystemAgnosticNeed(unittest.TestCase):
    """P-IH2: every pausing subsystem states its need through one typed channel;
    the shell renders it with no subsystem-specific knowledge."""

    def test_non_retrieval_subsystem_reaches_waiting_with_a_prompt(self) -> None:
        result = Controller(max_steps=2).run(
            ObligationState(),
            SequencePolicy(
                (Action.build(ActionKind.ASK, "raise_need", {"slot": "climax"}),)
            ),
            ObligationVerifier(),
            is_complete=lambda s: s.discharged,
            is_waiting=lambda s: s.awaiting is not None,
        )
        self.assertIs(result.stop_reason, StopReason.WAITING)
        need = pending_need(result.final_state)
        self.assertIsNotNone(need)
        assert need is not None
        self.assertIsInstance(need, Need)  # runtime_checkable structural match
        self.assertIn("climax", need.prompt)

    def test_one_renderer_serves_retrieval_and_non_retrieval_needs(self) -> None:
        # The retrieval need (a ClarificationRequest minted by RetrievalVerifier).
        executor = FrameExecutor()
        frame = executor.open_frame(
            FrameSpec(frame="runtime.frames.p_ih2_private")
        )
        verifier = RetrievalVerifier(_NoStore(), executor)
        retrieval_state = RetrievalState.from_unknown(
            executor,
            frame,
            "tone",
            "tone",
            Literal("story revision", "requested tone", "tone"),
            resolution_channel="user",
            user_owner="interlocutor",
        )
        asked = verifier.evaluate(retrieval_state, ask_action("tone"))
        assert asked.next_state is not None
        retrieval_need = pending_need(asked.next_state)
        self.assertIsNotNone(retrieval_need)

        # The non-retrieval need.
        beat_need = BeatNeed("climax", "Which beat discharges the 'climax' obligation?")

        # The SAME function renders both; it is handed a Need and can see only
        # slot + prompt. If the shell had to branch on subsystem id, one of
        # these would need a different call — it does not.
        for need in (retrieval_need, beat_need):
            assert need is not None
            rendered = render_need(need)
            self.assertIn(need.prompt, rendered)
            self.assertIn("...", rendered)  # the WAITING chrome, ASCII floor

    def test_render_stop_surfaces_the_need_generically(self) -> None:
        result = Controller(max_steps=2).run(
            ObligationState(),
            SequencePolicy(
                (Action.build(ActionKind.ASK, "raise_need", {"slot": "climax"}),)
            ),
            ObligationVerifier(),
            is_complete=lambda s: s.discharged,
            is_waiting=lambda s: s.awaiting is not None,
        )
        line = render_stop(result)
        self.assertIn("climax", line)

    def test_need_protocol_exposes_nothing_to_branch_on(self) -> None:
        # The contract a renderer is allowed to see is exactly {slot, prompt}.
        # A subsystem id on the protocol is what P-IH2 forbids.
        annotations = set(Need.__annotations__)
        self.assertEqual(annotations, {"slot", "prompt"})


class PIH5BootMatrixHonesty(unittest.TestCase):
    """P-IH5: unset WordNet is OFF; a named-missing archive is FAIL, not OFF."""

    def test_unset_archive_is_off(self) -> None:
        record = probe_wordnet(offline=False, env=None)
        self.assertIs(record.liveness, Liveness.OFF)
        self.assertTrue(record.optional)

    def test_named_missing_archive_is_fail_not_off(self) -> None:
        missing = str(REPO_ROOT / "no_such_wordnet_archive_xyz.zip")
        record = probe_wordnet(offline=False, env=missing)
        self.assertIs(record.liveness, Liveness.FAIL)
        self.assertFalse(record.registered)

    def test_named_present_archive_is_ok(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as handle:
            path = Path(handle.name)
        try:
            record = probe_wordnet(offline=False, env=str(path))
            self.assertIs(record.liveness, Liveness.OK)
            self.assertTrue(record.registered)
        finally:
            path.unlink()

    def test_offline_forces_off_even_when_named(self) -> None:
        record = probe_wordnet(offline=True, env=str(REPO_ROOT / "anything.zip"))
        self.assertIs(record.liveness, Liveness.OFF)


@dataclass(frozen=True)
class _PlainTerminalState:
    """A terminal-stop state that never opened a WAITING need channel.

    A non-retrieval subsystem (docs §10, e.g. a prover that SOLVED) is under no
    obligation to expose ``.awaiting``. It must still render.
    """


class ReviewFixRegressions(unittest.TestCase):
    """Regressions closing the two should-fix findings of the slice's
    independent adversarial review. Both were latent in the committed slice
    (every state it constructs happens to satisfy the assumption); the tests
    exercise the assumption directly so a later slice cannot reintroduce it."""

    def test_render_stop_terminal_state_without_a_need_channel(self) -> None:
        # Finding 1: render_stop consulted `.awaiting` unconditionally, so a
        # terminal stop over a state with no need channel crashed. It must now
        # touch `.awaiting` only on the WAITING branch.
        plain = _PlainTerminalState()
        result = RunResult(plain, plain, (), StopReason.SOLVED)
        line = render_stop(result)  # must not raise AttributeError
        self.assertIn("solved", line)
        self.assertIn("[OK]", line)

    def test_probe_corpus_fails_cleanly_when_required_ledger_absent(self) -> None:
        # Finding 2: boot only probed data/, but the store reads
        # reports/{signature_matches,decompositions}.json with no guard, so a
        # data-present/reports-absent checkout raised inside boot instead of a
        # clean FAIL. probe_corpus now owns that dependency.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data" / "logic").mkdir(parents=True)
            (root / "data" / "logic" / "nodes.json").write_text(
                "[]", encoding="utf-8"
            )
            # reports/ deliberately absent.
            record = probe_corpus(root)
            self.assertIs(record.liveness, Liveness.FAIL)
            self.assertFalse(record.optional)
            self.assertIn("ledger", record.detail)

    def test_probe_corpus_ok_when_data_and_ledgers_present(self) -> None:
        record = probe_corpus(REPO_ROOT)
        self.assertIs(record.liveness, Liveness.OK)


class _NoStore:
    """A store that must not be consulted for a user-private ASK."""

    def query(self, key: str, limit: int = 24):
        raise AssertionError("user-private ASK touched the store")

    def binding_match_mode(self, item, key: str):
        del item, key
        return None

    def contains_item(self, item) -> bool:
        del item
        return False


if __name__ == "__main__":
    unittest.main()
