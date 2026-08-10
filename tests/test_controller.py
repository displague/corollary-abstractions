from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    Controller,
    SequencePolicy,
    StopReason,
    Verification,
    Verdict,
)
from oracle_controller_demo import (  # noqa: E402
    GOLDEN_CHICKEN_ELEMENTS,
    ElementMention,
    LeanReplayState,
    LeanReplayVerifier,
    NarrativeElement,
    StoryBeat,
    StoryFrameVerifier,
    StoryState,
    lean_oracle_run,
    parse_mention_bindings,
    story_oracle_actions,
    story_oracle_run,
)


def rebound(action: Action, **overrides: str) -> Action:
    """Rewrite one action's arguments (the oracle's authored bindings)."""

    arguments = dict(action.arguments)
    arguments.update(overrides)
    return Action.build(action.kind, action.name, arguments, action.dependencies)


class PassiveVerifier:
    name = "passive-isolation-probe"

    @staticmethod
    def state_key(state: list[str]) -> str:
        return repr(state)

    @staticmethod
    def evaluate(
        state: list[str], action: Action
    ) -> Verification[list[str]]:
        del state, action
        raise AssertionError("policy should stop before verifier evaluation")


class ControllerContractTests(unittest.TestCase):
    def test_public_action_vocabulary_is_complete(self) -> None:
        self.assertEqual(
            {kind.value for kind in ActionKind},
            {"POINT", "GEN", "RETRIEVE", "ASK", "WRITE"},
        )

    def test_rejected_verification_cannot_supply_next_state(self) -> None:
        bad = Verification(Verdict.REFUTED, "bad", next_state="mutated")
        with self.assertRaisesRegex(ValueError, "may not mutate"):
            bad.validate()

    def test_mutating_rejected_verifier_cannot_change_accepted_state(self) -> None:
        class MutatingVerifier:
            name = "mutation-probe"

            @staticmethod
            def state_key(state: list[str]) -> str:
                return repr(state)

            @staticmethod
            def evaluate(
                state: list[str], action: Action
            ) -> Verification[list[str]]:
                del action
                state.append("leaked from dead branch")
                return Verification(Verdict.REFUTED, "deliberate mutation probe")

        caller_state: list[str] = []
        run = Controller[list[str]](max_steps=1).run(
            caller_state,
            SequencePolicy((Action.build(ActionKind.GEN, "mutate"),)),
            MutatingVerifier(),
            lambda state: bool(state),
        )
        self.assertEqual(caller_state, [])
        self.assertEqual(run.initial_state, [])
        self.assertEqual(run.final_state, [])
        self.assertEqual(run.trace[0].state_before, [])
        self.assertEqual(run.trace[0].state_after, [])

    def test_mutating_state_key_cannot_change_accepted_state(self) -> None:
        class MutatingKeyVerifier:
            name = "state-key-mutation-probe"

            @staticmethod
            def state_key(state: list[str]) -> str:
                state.append("leaked from state_key")
                return repr(state)

            @staticmethod
            def evaluate(
                state: list[str], action: Action
            ) -> Verification[list[str]]:
                del state, action
                return Verification(Verdict.REFUTED, "deliberate key mutation probe")

        caller_state: list[str] = []
        run = Controller[list[str]](max_steps=1).run(
            caller_state,
            SequencePolicy((Action.build(ActionKind.GEN, "mutate-key"),)),
            MutatingKeyVerifier(),
            lambda state: bool(state),
        )
        self.assertEqual(caller_state, [])
        self.assertEqual(run.initial_state, [])
        self.assertEqual(run.final_state, [])
        self.assertEqual(run.trace[0].state_before, [])
        self.assertEqual(run.trace[0].state_after, [])

    def test_mutating_goal_cannot_change_accepted_state(self) -> None:
        class NoActionPolicy:
            @staticmethod
            def propose(state: list[str], trace: tuple[object, ...]) -> None:
                del state, trace
                return None

        def mutating_goal(state: list[str]) -> bool:
            state.append("leaked from goal")
            return False

        caller_state: list[str] = []
        run = Controller[list[str]]().run(
            caller_state,
            NoActionPolicy(),
            PassiveVerifier(),
            mutating_goal,
        )
        self.assertEqual(caller_state, [])
        self.assertEqual(run.initial_state, [])
        self.assertEqual(run.final_state, [])

    def test_mutating_policy_cannot_change_accepted_state(self) -> None:
        class MutatingPolicy:
            @staticmethod
            def propose(state: list[str], trace: tuple[object, ...]) -> None:
                del trace
                state.append("leaked from policy")
                return None

        caller_state: list[str] = []
        run = Controller[list[str]]().run(
            caller_state,
            MutatingPolicy(),
            PassiveVerifier(),
            lambda state: bool(state),
        )
        self.assertEqual(caller_state, [])
        self.assertEqual(run.initial_state, [])
        self.assertEqual(run.final_state, [])

    def test_duplicate_rejected_action_is_pruned(self) -> None:
        initial = StoryFrameVerifier().initial_state()
        invalid = Action.build(
            ActionKind.GEN,
            "resolve",
            {"agent": "the golden chicken", "desire": "x", "outcome": "done"},
        )
        run = Controller[StoryState](max_steps=2).run(
            initial,
            SequencePolicy((invalid, invalid)),
            StoryFrameVerifier(),
            lambda state: bool(state.beats),
        )
        self.assertEqual(run.stop_reason, StopReason.BUDGET)
        self.assertEqual(run.rejected_steps, 2)
        self.assertEqual(run.trace[0].verification.verdict, Verdict.REFUTED)
        self.assertEqual(run.trace[1].verification.verdict, Verdict.REFUSED)
        self.assertIn("duplicate", run.trace[1].verification.reason)
        self.assertEqual(run.final_state, initial)


class LeanReplayTests(unittest.TestCase):
    def test_oracle_replays_three_contiguous_extracted_steps(self) -> None:
        run = lean_oracle_run()
        self.assertTrue(run.solved)
        self.assertEqual(run.accepted_steps, 3)
        self.assertEqual(run.final_state.proof_state, "no goals")
        self.assertEqual(
            run.final_state.tactics, ("intro hp", "left", "exact hp")
        )
        self.assertEqual(run.trace[-1].verification.verdict, Verdict.PROVEN)

    def test_unrecorded_tactic_does_not_pass_replay_verifier(self) -> None:
        verifier = LeanReplayVerifier()
        valid = lean_oracle_run().initial_state
        action = Action.build(
            ActionKind.GEN, "lean_tactic", {"tactic": "exact imaginary_proof"}
        )
        result = verifier.evaluate(valid, action)
        self.assertEqual(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)
        self.assertIn("cannot adjudicate", result.reason)

    def test_untrusted_extraction_cannot_assign_proven(self) -> None:
        records = [
            {
                "theorem": "BooleanLaws.absorption_or_and",
                "tactic": "intro hp",
                "stateBefore": "fake start",
                "stateAfter": "fake middle 1",
            },
            {
                "theorem": "BooleanLaws.absorption_or_and",
                "tactic": "left",
                "stateBefore": "fake middle 1",
                "stateAfter": "fake middle 2",
            },
            {
                "theorem": "BooleanLaws.absorption_or_and",
                "tactic": "exact hp",
                "stateBefore": "fake middle 2",
                "stateAfter": "no goals",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fabricated.json"
            path.write_text(json.dumps(records), encoding="utf-8")
            run = lean_oracle_run(path)
        self.assertTrue(run.solved)
        self.assertEqual(run.trace[-1].verification.verdict, Verdict.VERIFIED)
        self.assertIn("digest is untrusted", run.trace[-1].verification.reason)

    def test_replay_is_state_sensitive(self) -> None:
        verifier = LeanReplayVerifier()
        valid = lean_oracle_run().initial_state
        wrong_state = replace(valid, proof_state=valid.proof_state + "\n-- changed")
        action = Action.build(
            ActionKind.GEN, "lean_tactic", {"tactic": "intro hp"}
        )
        self.assertEqual(
            verifier.evaluate(wrong_state, action).verdict, Verdict.REFUSED
        )


class StoryFrameTests(unittest.TestCase):
    def test_oracle_executes_three_verified_beats(self) -> None:
        run = story_oracle_run()
        self.assertTrue(run.solved)
        self.assertEqual(run.accepted_steps, 5)
        self.assertEqual(
            tuple(beat.role for beat in run.final_state.beats),
            ("setup", "complication", "resolution"),
        )
        self.assertTrue(
            all(entry.verification.verdict is Verdict.VERIFIED for entry in run.trace)
        )
        self.assertEqual(len(run.final_state.frame_state.obligations), 1)
        self.assertFalse(run.final_state.frame_state.obligations[0].outstanding)
        self.assertIn("fallen feather", run.final_state.beats[0].text)
        self.assertIn("fallen feather as a key", run.final_state.beats[-1].text)

    def test_out_of_order_beat_is_refuted_without_state_change(self) -> None:
        initial = story_oracle_run().initial_state
        resolution = next(
            action for action in story_oracle_actions()
            if action.name == "resolve"
        )
        result = StoryFrameVerifier().evaluate(initial, resolution)
        self.assertEqual(result.verdict, Verdict.REFUTED)
        self.assertIsNone(result.next_state)

    def test_trait_contradiction_is_refuted(self) -> None:
        initial = story_oracle_run().initial_state
        contradictory = Action.build(
            ActionKind.GEN,
            "introduce",
            {
                "agent": "the golden chicken",
                "trait": "silver",
                "desire": "to sing",
            },
        )
        result = StoryFrameVerifier().evaluate(initial, contradictory)
        self.assertEqual(result.verdict, Verdict.REFUTED)
        self.assertIn("explicitly denied", result.reason)

    def test_undeclared_compatible_trait_is_unknown_not_refuted(self) -> None:
        initial = story_oracle_run().initial_state
        undeclared = Action.build(
            ActionKind.GEN,
            "introduce",
            {
                "agent": "the golden chicken",
                "trait": "brave",
                "desire": "to sing",
            },
        )
        result = StoryFrameVerifier().evaluate(initial, undeclared)
        self.assertEqual(result.verdict, Verdict.UNKNOWN)
        self.assertIn("neither declared nor denied", result.reason)

    def test_rejected_branch_is_not_a_premise_for_recovery(self) -> None:
        initial = story_oracle_run().initial_state
        invalid = next(
            action for action in story_oracle_actions()
            if action.name == "resolve"
        )
        actions = (invalid,) + story_oracle_actions()
        run = Controller[StoryState](max_steps=6).run(
            initial,
            SequencePolicy(actions),
            StoryFrameVerifier(),
            lambda state: len(state.beats) == 3
            and bool(state.frame_state.obligations)
            and not state.frame_state.obligations[0].outstanding,
        )
        self.assertTrue(run.solved)
        self.assertEqual(run.rejected_steps, 1)
        self.assertEqual(run.accepted_steps, 5)
        self.assertEqual(run.trace[0].state_after, initial)
        self.assertEqual(run.trace[1].state_before, initial)

    def _story_through(
        self,
        verifier: StoryFrameVerifier,
        actions: tuple[Action, ...],
    ) -> StoryState:
        state = verifier.initial_state()
        for action in actions:
            result = verifier.evaluate(state, action)
            self.assertTrue(result.verdict.accepts, result.reason)
            state = result.next_state
        return state

    def test_ledger_only_discharge_is_unknown_without_a_bound_resolution(
        self,
    ) -> None:
        """The hidden-ledger control, now structural. The resolution beat
        renders identical prose but binds no element, so the ledger has
        nothing visible to point at and the discharge stays UNKNOWN."""
        verifier = StoryFrameVerifier()
        actions = story_oracle_actions()
        state = self._story_through(
            verifier, actions[:3] + (rebound(actions[3], binds=""),)
        )
        self.assertIn("fallen feather", state.beats[-1].text)
        self.assertEqual(state.beats[-1].mentions, ())
        result = verifier.evaluate(state, actions[-1])
        self.assertIs(result.verdict, Verdict.UNKNOWN)
        self.assertIsNone(result.next_state)
        self.assertIn("binds no narrative element", result.reason)

    def test_discharge_of_an_element_the_resolution_never_names_is_unknown(
        self,
    ) -> None:
        """The unrelated-mention control, by element identity: the
        resolution binds 'key' but not the feather being discharged."""
        verifier = StoryFrameVerifier()
        actions = story_oracle_actions()
        state = self._story_through(
            verifier, actions[:3] + (rebound(actions[3], binds="key@30:33"),)
        )
        result = verifier.evaluate(state, actions[-1])
        self.assertIs(result.verdict, Verdict.UNKNOWN)
        self.assertIsNone(result.next_state)
        self.assertIn("does not name", result.reason)

    def test_plant_is_setup_only_and_must_name_its_element(self) -> None:
        verifier = StoryFrameVerifier(
            elements=GOLDEN_CHICKEN_ELEMENTS
            + (NarrativeElement("brass bell", ("brass bell",)),)
        )
        actions = story_oracle_actions()
        setup = verifier.evaluate(verifier.initial_state(), actions[0]).next_state
        # A well-formed mention that binds a DIFFERENT declared element
        # does not plant this one: identity, not spelling.
        unrelated = rebound(
            actions[1],
            mention="A brass bell gleamed.",
            binds="brass bell@2:12",
        )
        finding = verifier.evaluate(setup, unrelated)
        self.assertIs(finding.verdict, Verdict.UNKNOWN)
        self.assertIsNone(finding.next_state)
        self.assertIn("does not name the planted element", finding.reason)

        state = setup
        for action in actions[2:4]:
            result = verifier.evaluate(state, action)
            self.assertTrue(result.verdict.accepts)
            state = result.next_state
        late = verifier.evaluate(state, actions[1])
        self.assertIs(late.verdict, Verdict.REFUTED)
        self.assertIsNone(late.next_state)
        self.assertIn("setup", late.reason)

    def test_duplicate_story_plant_does_not_duplicate_rendered_text(self) -> None:
        verifier = StoryFrameVerifier()
        actions = story_oracle_actions()
        setup = verifier.evaluate(verifier.initial_state(), actions[0]).next_state
        planted = verifier.evaluate(setup, actions[1]).next_state
        duplicate = verifier.evaluate(planted, actions[1])
        self.assertIs(duplicate.verdict, Verdict.VERIFIED)
        self.assertEqual(duplicate.next_state, planted)
        self.assertEqual(
            duplicate.next_state.beats[0].text.count("fallen feather"), 1
        )

    def test_typed_records_anchor_every_element_in_its_own_beat(self) -> None:
        """P-EB1: the records are real spans of the beat that carries them,
        so 'the element is visible here' needs no text search to confirm."""
        final = story_oracle_run().final_state
        setup, _, resolution = final.beats
        self.assertEqual(len(setup.mentions), 1)
        mention = setup.mentions[0]
        self.assertEqual(mention.element, "fallen feather")
        self.assertEqual(mention.span_of(setup.text), "fallen feather")
        self.assertTrue(setup.names("fallen feather"))
        self.assertEqual(
            [record.element for record in resolution.mentions],
            ["fallen feather", "key"],
        )
        for record in resolution.mentions:
            self.assertEqual(record.span_of(resolution.text), record.element)

    def test_closed_story_frame_refuses_new_beats(self) -> None:
        verifier = StoryFrameVerifier()
        state = story_oracle_run().final_state
        closed = verifier.executor.close_frame(state.frame_state).state
        result = verifier.evaluate(
            replace(state, frame_state=closed),
            Action.build(ActionKind.GEN, "introduce", {"desire": "again"}),
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIn("closed", result.reason)


class TypedEventBinderTests(unittest.TestCase):
    """v0.7 item 7: element references are bound, not grepped.

    Registered predictions (written before the binder was exercised):

    P-EB1. Typed records replace the substring searches without weakening
        them: every plant/discharge decision is made against
        element-identity records anchored to spans of a rendered beat,
        and the golden-chicken demo's output is byte-identical because
        only the CHECK changed, not the prose.
    P-EB2. The anti-vacuity controls survive as structure. A plant still
        alters a visible beat (records are rebased onto the amended setup
        text); a discharge is still evidenced by the resolution beat (it
        requires a record ON that beat); an unrelated mention still fails,
        now by element identity; and a ledger-only pass -- identical prose,
        no bindings -- is UNKNOWN.
    P-EB3. Ids stop depending on spelling. An element id that never
        appears in the rendered prose plants, discharges, and closes,
        which the old case-insensitive substring check could not do; and
        a span binds only if the frame declared that exact surface form,
        so an author cannot label arbitrary words with any id they like.
    """

    BELL_ELEMENTS = (
        NarrativeElement("brass_bell", ("The brass bell", "the brass bell")),
    )

    def _bell_actions(self) -> tuple[Action, ...]:
        shared = {"agent": "the golden chicken", "desire": "to ring in dawn"}
        return (
            Action.build(
                ActionKind.GEN, "introduce", {**shared, "trait": "golden"}
            ),
            Action.build(
                ActionKind.GEN,
                "plant",
                {
                    **shared,
                    "event_id": "bell_seen",
                    "element": "brass_bell",
                    "mention": "The brass bell hung silent.",
                    "binds": "brass_bell@0:14",
                },
            ),
            Action.build(
                ActionKind.GEN,
                "obstruct",
                {**shared, "obstacle": "the frayed bell rope"},
            ),
            Action.build(
                ActionKind.GEN,
                "resolve",
                {
                    **shared,
                    "outcome": "It rang the brass bell at last",
                    "binds": "brass_bell@8:22",
                },
            ),
            Action.build(
                ActionKind.GEN,
                "discharge",
                {**shared, "event_id": "bell_rung", "element": "brass_bell"},
            ),
        )

    def test_element_ids_are_decoupled_from_the_rendered_prose(self) -> None:
        """P-EB3: the id 'brass_bell' is never written in the story, so the
        replaced substring check could not have accepted this run at all."""
        verifier = StoryFrameVerifier(elements=self.BELL_ELEMENTS)
        state = verifier.initial_state()
        for action in self._bell_actions():
            result = verifier.evaluate(state, action)
            self.assertTrue(result.verdict.accepts, result.reason)
            state = result.next_state
        story = " ".join(beat.text for beat in state.beats)
        self.assertNotIn("brass_bell", story)
        self.assertIn("The brass bell hung silent.", state.beats[0].text)
        self.assertEqual(
            state.beats[0].mentions[0].span_of(state.beats[0].text),
            "The brass bell",
        )
        obligation = state.frame_state.obligations[0]
        self.assertEqual(obligation.element, "brass_bell")
        self.assertFalse(obligation.outstanding)
        closed = verifier.executor.close_frame(state.frame_state)
        self.assertIs(closed.verdict, Verdict.VERIFIED)

    def test_unreadable_bindings_refuse_and_ungrounded_ones_are_unknown(
        self,
    ) -> None:
        """Two failure classes, two verdicts: the adapter cannot READ the
        action (REFUSED) versus the story cannot GROUND it (UNKNOWN)."""
        verifier = StoryFrameVerifier()
        actions = story_oracle_actions()
        setup = verifier.evaluate(verifier.initial_state(), actions[0]).next_state
        for spec in (
            "fallen feather@2",
            "fallen feather@2:sixteen",
            "@2:16",
            "fallen feather@2:400",
            "fallen feather@9:2",
        ):
            result = verifier.evaluate(
                setup, rebound(actions[1], binds=spec)
            )
            self.assertIs(result.verdict, Verdict.REFUSED, spec)
            self.assertIsNone(result.next_state)
            self.assertIn("unreadable", result.reason)
        undeclared = verifier.evaluate(
            setup, rebound(actions[1], binds="silver egg@2:16")
        )
        self.assertIs(undeclared.verdict, Verdict.UNKNOWN)
        self.assertIn("declares no narrative element", undeclared.reason)

    def test_a_span_binds_only_a_declared_surface_form(self) -> None:
        """P-EB3's other half: the author may not label arbitrary words
        with any element id -- the span must be a declared surface."""
        verifier = StoryFrameVerifier()
        actions = story_oracle_actions()
        setup = verifier.evaluate(verifier.initial_state(), actions[0]).next_state
        misbound = verifier.evaluate(
            setup,
            rebound(
                actions[1],
                mention="A brass bell gleamed.",
                binds="fallen feather@2:12",
            ),
        )
        self.assertIs(misbound.verdict, Verdict.UNKNOWN)
        self.assertIsNone(misbound.next_state)
        self.assertIn("not a declared surface form", misbound.reason)
        # Casing is an authoring decision, not a fuzzy match: the demo
        # declares 'fallen feather', so 'Fallen feather' does not bind.
        cased = verifier.evaluate(
            setup,
            rebound(
                actions[1],
                mention="Fallen feather, it gleamed.",
                binds="fallen feather@0:14",
            ),
        )
        self.assertIs(cased.verdict, Verdict.UNKNOWN)
        self.assertIn("not a declared surface form", cased.reason)

    def test_mention_records_fail_closed_on_construction(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty"):
            ElementMention("fallen feather", 4, 4)
        with self.assertRaisesRegex(ValueError, "non-empty"):
            ElementMention("fallen feather", -1, 3)
        with self.assertRaisesRegex(ValueError, "must name an element"):
            ElementMention("  ", 0, 3)
        with self.assertRaisesRegex(ValueError, "outside"):
            StoryBeat("setup", "short", (ElementMention("x", 0, 99),))
        with self.assertRaisesRegex(ValueError, "no surface form"):
            NarrativeElement("fallen feather", ())
        self.assertEqual(
            parse_mention_bindings(" a@0:1 ; b@2:4 "),
            (ElementMention("a", 0, 1), ElementMention("b", 2, 4)),
        )
        self.assertEqual(parse_mention_bindings(""), ())


if __name__ == "__main__":
    unittest.main()
