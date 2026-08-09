"""Frame-executor contract tests, including the slice's negative controls.

Registered predictions (written before adjudication, per house rule):

P1. Adding the optional `scope` object to the live schema changes zero
    validation outcomes across the 199 committed nodes (adjudicated by
    `python scripts/validate_nodes.py` on the unchanged corpus).
P2. The matcher's group counts are byte-identical after this slice: the
    matcher never reads `scope` (adjudicated by regenerating
    reports/signature_matches.json and diffing group_counts).
P3. Routing golden-chicken trait checks through the executor preserves the
    oracle demo's external behavior exactly: same verdicts, same beat
    texts, same solved status (adjudicated by the pre-existing
    test_controller.py story tests passing unmodified in their assertions).
    This was adjudicated for the preceding frame slice; the current temporal
    slice intentionally adds a visible plant sentence and two transitions.
P4. Suspension is asymmetric by construction: the same contradicting
    literal is locally admissible iff the grounding corpus truth appears
    in the frame's `suspends` (adjudicated by the paired controls below).
P5. A planted element blocks frame close until its matching discharge; the
    refused close preserves the open state and emits no demotions. Exact
    event retries are idempotent, fresh ids for bound elements are refused,
    and closed frames refuse temporal events.
    (Historical note: P5 originally predicted unplanted discharge stays
    UNKNOWN "because the past-facing converse is not yet executable" -- the
    no-deus slice made it executable, so the verdict now splits on
    governance; see P6-P8.)

Registered predictions for the no-deus slice (written before adjudication):

P6. A frame that adopts narrative.constraint.no_deus_ex_machina in
    `governed_by` REFUTES an unheralded discharge, citing that law, and the
    refutation leaves the obligation ledger and frame state unchanged.
P7. A frame that does not adopt the law keeps the UNKNOWN verdict for the
    same discharge -- genre choice, per the corpus node's own regularity
    notes. (Adjudication note: "unchanged" holds for verdict and
    next_state; the reason AND the evidence tuple both changed, the
    latter now citing the adoptable law alongside Chekhov's gun. The
    review caught the original wording underselling this.)
P8. Adoption changes nothing on the lawful path: plant-then-discharge is
    VERIFIED and close is clean, and the golden-chicken oracle (which now
    adopts the law) still solves with identical beats.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    Controller,
    SequencePolicy,
    Verdict,
)
from frames import (  # noqa: E402
    FRAME_CONSISTENCY,
    NO_DEUS,
    FrameAssertionVerifier,
    FrameExecutor,
    FrameSpec,
    Literal,
)
from oracle_controller_demo import (  # noqa: E402
    StoryFrameVerifier,
    story_oracle_run,
)
from validate_nodes import scope_errors  # noqa: E402


GRAVITY = "physics.gravitation.newton_universal_gravitation"
WORLD = {GRAVITY: (Literal("unsupported objects", "behavior", "fall"),)}


def cartoon_spec(suspends: tuple[str, ...]) -> FrameSpec:
    return FrameSpec(
        frame="narrative.frames.cartoon_gravity",
        declarations=(
            ("agent", Literal("story", "agent", "the coyote")),
        ),
        suspends=suspends,
    )


def chicken_spec() -> FrameSpec:
    return FrameSpec(
        frame="narrative.frames.golden_chicken",
        declarations=(
            ("golden", Literal("the chicken", "trait", "golden")),
            (
                "no_silver",
                Literal("the chicken", "trait", "silver", polarity=False),
            ),
        ),
    )


def no_deus_spec() -> FrameSpec:
    """chicken_spec plus adoption of the no-deus-ex-machina law."""
    base = chicken_spec()
    return FrameSpec(
        frame=base.frame,
        declarations=base.declarations,
        governed_by=(FRAME_CONSISTENCY, NO_DEUS),
    )


class NoDeusTests(unittest.TestCase):
    """P6-P8: the past-facing converse, executable and governance-gated."""

    def setUp(self) -> None:
        self.executor = FrameExecutor()

    def test_adopting_frame_refutes_unheralded_discharge(self) -> None:
        state = self.executor.open_frame(no_deus_spec())
        result = self.executor.discharge(state, "sudden_key", "a magic key")
        self.assertIs(result.verdict, Verdict.REFUTED)
        self.assertIsNone(result.next_state)
        self.assertIn("unheralded", result.reason)
        self.assertIn(NO_DEUS, result.evidence)

    def test_refuted_discharge_leaves_ledger_and_close_unaffected(self) -> None:
        state = self.executor.open_frame(no_deus_spec())
        planted = self.executor.plant(state, "feather_seen", "fallen feather")
        refuted = self.executor.discharge(
            planted.next_state, "sudden_key", "a magic key"
        )
        self.assertIs(refuted.verdict, Verdict.REFUTED)
        self.assertIsNone(refuted.next_state)
        discharged = self.executor.discharge(
            planted.next_state, "feather_used", "fallen feather"
        )
        close = self.executor.close_frame(discharged.next_state)
        self.assertIs(close.verdict, Verdict.VERIFIED)
        self.assertTrue(close.state.closed)

    def test_non_adopting_frame_keeps_unknown_with_adoption_pointer(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        result = self.executor.discharge(state, "sudden_key", "a magic key")
        self.assertIs(result.verdict, Verdict.UNKNOWN)
        self.assertIsNone(result.next_state)
        self.assertIn("does not adopt", result.reason)
        self.assertIn(NO_DEUS, result.evidence)

    def test_adapter_passes_through_the_refutation(self) -> None:
        run = story_oracle_run()
        self.assertTrue(run.solved)
        action = Action.build(
            ActionKind.GEN,
            "discharge",
            {
                "event_id": "sudden_key_used",
                "element": "key",
                "evidence_text": "used a fallen feather as a key",
            },
        )
        result = StoryFrameVerifier().evaluate(run.final_state, action)
        self.assertIs(result.verdict, Verdict.REFUTED)
        self.assertIn(NO_DEUS, result.evidence)
        self.assertIn("unheralded", result.reason)

    def test_adoption_changes_nothing_on_the_lawful_path(self) -> None:
        state = self.executor.open_frame(no_deus_spec())
        planted = self.executor.plant(state, "feather_seen", "fallen feather")
        self.assertIs(planted.verdict, Verdict.VERIFIED)
        discharged = self.executor.discharge(
            planted.next_state, "feather_used", "fallen feather"
        )
        self.assertIs(discharged.verdict, Verdict.VERIFIED)
        close = self.executor.close_frame(discharged.next_state)
        self.assertIs(close.verdict, Verdict.VERIFIED)
        self.assertTrue(close.demoted)


def assert_action(
    claim_id: str, literal: Literal
) -> Action:
    return Action.build(
        ActionKind.GEN,
        "assert_fact",
        {
            "claim_id": claim_id,
            "subject": literal.subject,
            "predicate": literal.predicate,
            "value": literal.value,
            "polarity": "true" if literal.polarity else "false",
        },
    )


def temporal_action(name: str, event_id: str, element: str) -> Action:
    return Action.build(
        ActionKind.GEN,
        name,
        {"event_id": event_id, "element": element},
    )


class FrameLadderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.executor = FrameExecutor(WORLD)

    def test_declaration_grounds_matching_assertion(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        finding = self.executor.check(
            state, Literal("the chicken", "trait", "golden")
        )
        self.assertIs(finding.verdict, Verdict.VERIFIED)
        self.assertIn("golden", finding.evidence)

    def test_declaration_plus_explicit_negation_is_refuted(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        finding = self.executor.check(
            state, Literal("the chicken", "trait", "silver")
        )
        self.assertIs(finding.verdict, Verdict.REFUTED)
        self.assertIn("explicitly denied", finding.reason)
        self.assertIn("narrative.frame.frame_consistency", finding.evidence)

    def test_undeclared_compatible_property_stays_unknown(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        finding = self.executor.check(
            state, Literal("the chicken", "trait", "brave")
        )
        self.assertIs(finding.verdict, Verdict.UNKNOWN)
        self.assertIn("neither declared nor denied", finding.reason)

    def test_contradiction_of_suspended_corpus_truth_is_admissible(self) -> None:
        state = self.executor.open_frame(cartoon_spec(suspends=(GRAVITY,)))
        hover = Literal("unsupported objects", "behavior", "fall", polarity=False)
        finding = self.executor.check(state, hover)
        self.assertIs(finding.verdict, Verdict.UNKNOWN)
        self.assertEqual(finding.suspended_grounds, (GRAVITY,))
        admitted = self.executor.assert_literal(state, "hover", hover)
        self.assertIs(admitted.verdict, Verdict.VERIFIED)
        self.assertIn("admitted", admitted.reason)

    def test_same_contradiction_without_suspension_is_refuted(self) -> None:
        state = self.executor.open_frame(cartoon_spec(suspends=()))
        hover = Literal("unsupported objects", "behavior", "fall", polarity=False)
        finding = self.executor.check(state, hover)
        self.assertIs(finding.verdict, Verdict.REFUTED)
        self.assertIn("does not suspend", finding.reason)
        self.assertIn(GRAVITY, finding.evidence)
        rejected = self.executor.assert_literal(state, "hover", hover)
        self.assertIs(rejected.verdict, Verdict.REFUTED)

    def test_declaration_cannot_bypass_the_suspension_gate(self) -> None:
        spec = FrameSpec(
            frame="narrative.frames.cartoon_gravity",
            declarations=(
                (
                    "hover",
                    Literal(
                        "unsupported objects", "behavior", "fall",
                        polarity=False,
                    ),
                ),
            ),
            suspends=(),
        )
        with self.assertRaisesRegex(ValueError, "does not suspend"):
            self.executor.open_frame(spec)
        opened = self.executor.open_frame(
            FrameSpec(
                frame=spec.frame,
                declarations=spec.declarations,
                suspends=(GRAVITY,),
            )
        )
        finding = self.executor.check(
            opened,
            Literal("unsupported objects", "behavior", "fall", polarity=False),
        )
        self.assertIs(finding.verdict, Verdict.VERIFIED)

    def test_suspension_does_not_verify_either_polarity_via_check(self) -> None:
        state = self.executor.open_frame(cartoon_spec(suspends=(GRAVITY,)))
        falls = Literal("unsupported objects", "behavior", "fall")
        self.assertIs(self.executor.check(state, falls).verdict, Verdict.UNKNOWN)
        self.assertIs(
            self.executor.check(state, falls.negated).verdict, Verdict.UNKNOWN
        )

    def test_incoherent_world_is_rejected_at_construction(self) -> None:
        with self.assertRaisesRegex(ValueError, "incoherent world"):
            FrameExecutor(
                {
                    "physics.one": (Literal("x", "p", "v"),),
                    "physics.two": (Literal("x", "p", "v", polarity=False),),
                }
            )

    def test_closed_frame_refuses_check_and_double_close(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        closed, _ = self.executor.close_frame(state)
        finding = self.executor.check(
            closed, Literal("the chicken", "trait", "golden")
        )
        self.assertIs(finding.verdict, Verdict.REFUSED)
        with self.assertRaisesRegex(ValueError, "already closed"):
            self.executor.close_frame(closed)

    def test_already_grounded_assertion_does_not_duplicate_premises(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        result = self.executor.assert_literal(
            state, "again", Literal("the chicken", "trait", "golden")
        )
        self.assertIs(result.verdict, Verdict.VERIFIED)
        self.assertEqual(result.next_state.asserted, ())

    def test_agreeing_unsuspended_corpus_truth_grounds_assertion(self) -> None:
        state = self.executor.open_frame(cartoon_spec(suspends=()))
        falls = Literal("unsupported objects", "behavior", "fall")
        finding = self.executor.check(state, falls)
        self.assertIs(finding.verdict, Verdict.VERIFIED)
        self.assertIn(GRAVITY, finding.evidence)

    def test_open_frame_rejects_contradictory_declarations(self) -> None:
        spec = FrameSpec(
            frame="narrative.frames.broken",
            declarations=(
                ("a", Literal("x", "trait", "golden")),
                ("b", Literal("x", "trait", "golden", polarity=False)),
            ),
        )
        with self.assertRaisesRegex(ValueError, "declares a contradiction"):
            self.executor.open_frame(spec)

    def test_accepted_assertion_becomes_frame_local_premise(self) -> None:
        state = self.executor.open_frame(cartoon_spec(suspends=(GRAVITY,)))
        hover = Literal("unsupported objects", "behavior", "fall", polarity=False)
        result = self.executor.assert_literal(state, "hover", hover)
        self.assertIs(result.verdict, Verdict.VERIFIED)
        follow_up = self.executor.check(result.next_state, hover)
        self.assertIs(follow_up.verdict, Verdict.VERIFIED)
        self.assertIn("hover", follow_up.evidence)
        contradiction = self.executor.check(result.next_state, hover.negated)
        self.assertIs(contradiction.verdict, Verdict.REFUTED)

    def test_frame_truths_demote_on_exit_and_frame_closes(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        accepted = self.executor.assert_literal(
            state, "still_golden", Literal("the chicken", "trait", "golden")
        )
        closed, demoted = self.executor.close_frame(accepted.next_state)
        self.assertTrue(closed.closed)
        self.assertTrue(demoted)
        for claim in demoted:
            self.assertEqual(claim.epistemic_status, "conjectured")
            self.assertEqual(claim.frame, "narrative.frames.golden_chicken")
        late = self.executor.assert_literal(
            closed, "late", Literal("the chicken", "trait", "golden")
        )
        self.assertIs(late.verdict, Verdict.REFUSED)
        self.assertIn("closed", late.reason)

    def test_outstanding_obligation_refuses_close_without_mutation(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        planted = self.executor.plant(state, "feather_seen", "fallen feather")
        self.assertIs(planted.verdict, Verdict.VERIFIED)

        close = self.executor.close_frame(planted.next_state)
        self.assertIs(close.verdict, Verdict.REFUSED)
        self.assertIs(close.state, planted.next_state)
        self.assertFalse(close.state.closed)
        self.assertEqual(close.demoted, ())
        self.assertIn("narrative.constraint.chekhov_gun", close.evidence)

    def test_matching_discharge_allows_clean_close(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        planted = self.executor.plant(state, "feather_seen", "fallen feather")
        discharged = self.executor.discharge(
            planted.next_state, "feather_used", "fallen feather"
        )
        self.assertIs(discharged.verdict, Verdict.VERIFIED)
        obligation = discharged.next_state.obligations[0]
        self.assertEqual(obligation.discharged_by, "feather_used")

        close = self.executor.close_frame(discharged.next_state)
        self.assertIs(close.verdict, Verdict.VERIFIED)
        self.assertTrue(close.state.closed)
        self.assertTrue(close.demoted)

    def test_unrelated_discharge_is_unknown_and_cannot_close_obligation(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        planted = self.executor.plant(state, "feather_seen", "fallen feather")
        unrelated = self.executor.discharge(
            planted.next_state, "bell_rung", "brass bell"
        )
        self.assertIs(unrelated.verdict, Verdict.UNKNOWN)
        self.assertIsNone(unrelated.next_state)
        self.assertIn("does not adopt", unrelated.reason)
        close = self.executor.close_frame(planted.next_state)
        self.assertIs(close.verdict, Verdict.REFUSED)

    def test_duplicate_plant_and_discharge_are_idempotent(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        planted = self.executor.plant(state, "feather_seen", "fallen feather")
        duplicate_plant = self.executor.plant(
            planted.next_state, "feather_seen", "fallen feather"
        )
        self.assertIs(duplicate_plant.verdict, Verdict.VERIFIED)
        self.assertIs(duplicate_plant.next_state, planted.next_state)
        discharged = self.executor.discharge(
            planted.next_state, "feather_used", "fallen feather"
        )
        duplicate_discharge = self.executor.discharge(
            discharged.next_state, "feather_used", "fallen feather"
        )
        self.assertIs(duplicate_discharge.verdict, Verdict.VERIFIED)
        self.assertIs(duplicate_discharge.next_state, discharged.next_state)

    def test_fresh_ids_are_not_idempotent_retries(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        planted = self.executor.plant(state, "feather_seen", "fallen feather")
        second_plant = self.executor.plant(
            planted.next_state, "feather_seen_again", "fallen feather"
        )
        self.assertIs(second_plant.verdict, Verdict.REFUSED)
        discharged = self.executor.discharge(
            planted.next_state, "feather_used", "fallen feather"
        )
        second_discharge = self.executor.discharge(
            discharged.next_state, "feather_used_again", "fallen feather"
        )
        self.assertIs(second_discharge.verdict, Verdict.REFUSED)

        cross_kind = self.executor.discharge(
            planted.next_state, "feather_seen_again", "fallen feather"
        )
        self.assertIs(cross_kind.verdict, Verdict.VERIFIED)

    def test_closed_frame_refuses_temporal_events(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        close = self.executor.close_frame(state)
        planted = self.executor.plant(close.state, "late", "fallen feather")
        discharged = self.executor.discharge(
            close.state, "later", "fallen feather"
        )
        self.assertIs(planted.verdict, Verdict.REFUSED)
        self.assertIs(discharged.verdict, Verdict.REFUSED)

    def test_event_id_conflicts_are_order_independent(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        first = self.executor.plant(state, "event_a", "feather").next_state
        second = self.executor.plant(first, "event_b", "bell").next_state

        conflict = self.executor.plant(second, "event_b", "feather")
        self.assertIs(conflict.verdict, Verdict.REFUSED)
        self.assertIsNone(conflict.next_state)
        self.assertIn("different element", conflict.reason)

    def test_event_id_cannot_change_temporal_event_kind(self) -> None:
        state = self.executor.open_frame(chicken_spec())
        planted = self.executor.plant(state, "feather_seen", "feather")
        same_id_discharge = self.executor.discharge(
            planted.next_state, "feather_seen", "feather"
        )
        self.assertIs(same_id_discharge.verdict, Verdict.REFUSED)

        discharged = self.executor.discharge(
            planted.next_state, "feather_used", "feather"
        )
        same_id_plant = self.executor.plant(
            discharged.next_state, "feather_used", "bell"
        )
        self.assertIs(same_id_plant.verdict, Verdict.REFUSED)


class FrameControllerTests(unittest.TestCase):
    def test_rejected_transition_leaves_state_and_premises_unchanged(self) -> None:
        executor = FrameExecutor(WORLD)
        verifier = FrameAssertionVerifier(executor)
        spec = FrameSpec(
            frame="narrative.frames.golden_chicken",
            declarations=chicken_spec().declarations,
            suspends=(GRAVITY,),
        )
        initial = executor.open_frame(spec)
        refuted = assert_action(
            "c1", Literal("the chicken", "trait", "silver")
        )
        accepted = assert_action(
            "c2",
            Literal("unsupported objects", "behavior", "fall", polarity=False),
        )
        run = Controller(max_steps=3).run(
            initial,
            SequencePolicy((refuted, accepted)),
            verifier,
            lambda state: any(cid == "c2" for cid, _ in state.asserted),
        )
        self.assertTrue(run.solved)
        self.assertEqual(run.rejected_steps, 1)
        self.assertIs(run.trace[0].verification.verdict, Verdict.REFUTED)
        self.assertEqual(run.trace[0].state_after, initial)
        self.assertEqual(run.trace[1].state_before, initial)
        self.assertEqual(
            [cid for cid, _ in run.final_state.asserted], ["c2"]
        )

    def test_malformed_polarity_is_refused_not_negated(self) -> None:
        executor = FrameExecutor()
        verifier = FrameAssertionVerifier(executor)
        state = executor.open_frame(chicken_spec())
        action = Action.build(
            ActionKind.GEN,
            "assert_fact",
            {
                "claim_id": "c1",
                "subject": "the chicken",
                "predicate": "trait",
                "value": "golden",
                "polarity": "True",
            },
        )
        result = verifier.evaluate(state, action)
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIn("polarity", result.reason)

    def test_frame_local_retrieval_is_refused(self) -> None:
        executor = FrameExecutor()
        spec = FrameSpec(
            frame="narrative.frames.golden_chicken",
            retrieval="frame_local",
        )
        verifier = FrameAssertionVerifier(executor)
        result = verifier.evaluate(
            executor.open_frame(spec),
            Action.build(ActionKind.RETRIEVE, "lookup", {"key": "real chickens"}),
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIn("unresolvable-by-retrieval", result.reason)

    def test_temporal_actions_use_the_generic_controller_contract(self) -> None:
        executor = FrameExecutor()
        initial = executor.open_frame(chicken_spec())
        run = Controller(max_steps=2).run(
            initial,
            SequencePolicy(
                (
                    temporal_action("plant", "feather_seen", "fallen feather"),
                    temporal_action("discharge", "feather_used", "fallen feather"),
                )
            ),
            FrameAssertionVerifier(executor),
            lambda state: bool(state.obligations)
            and not state.obligations[0].outstanding,
        )
        self.assertTrue(run.solved)
        self.assertEqual(run.accepted_steps, 2)
        self.assertTrue(
            all(
                entry.verification.verdict is Verdict.VERIFIED
                for entry in run.trace
            )
        )


class StoryAdapterRobustnessTests(unittest.TestCase):
    def test_agentless_frame_refuses_instead_of_crashing(self) -> None:
        verifier = StoryFrameVerifier(
            spec=FrameSpec(frame="narrative.frames.agentless")
        )
        result = verifier.evaluate(
            verifier.initial_state(),
            Action.build(
                ActionKind.GEN, "introduce", {"desire": "to sing"}
            ),
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIn("no agent premise", result.reason)


def scoped_node(node_id: str, scope: dict) -> dict:
    return {"statement_id": node_id, "scope": scope}


class ScopeValidatorTests(unittest.TestCase):
    def test_valid_scope_produces_no_errors(self) -> None:
        nodes = [
            {"statement_id": "narrative.frame.frame_consistency"},
            {"statement_id": GRAVITY},
            scoped_node(
                "narrative.frames.golden_chicken",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                    "suspends": [GRAVITY],
                    "governed_by": ["narrative.frame.frame_consistency"],
                },
            ),
        ]
        self.assertEqual(scope_errors(nodes), [])

    def test_frame_id_must_resolve_to_its_declaration_node(self) -> None:
        nodes = [
            scoped_node(
                "narrative.stories.golden_chicken_setup",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                },
            )
        ]
        errors = scope_errors(nodes)
        self.assertTrue(any("must resolve to its declaration node" in e for e in errors))

    def test_frame_id_cannot_name_an_unscoped_or_assertion_node(self) -> None:
        unscoped = [
            {"statement_id": "narrative.frames.golden_chicken"},
            scoped_node(
                "narrative.stories.golden_chicken_setup",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                },
            ),
        ]
        assertion = [
            scoped_node(
                "narrative.frames.golden_chicken",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "assertion",
                },
            )
        ]
        self.assertTrue(
            any("must identify a scoped declaration node" in e for e in scope_errors(unscoped))
        )
        self.assertTrue(
            any("must identify a scoped declaration node" in e for e in scope_errors(assertion))
        )

    def test_bad_frame_pattern_and_role_are_flagged(self) -> None:
        nodes = [
            scoped_node(
                "narrative.stories.bad",
                {"frame": "NotAFrame", "role": "story"},
            )
        ]
        errors = scope_errors(nodes)
        self.assertTrue(any("frame-id pattern" in e for e in errors))
        self.assertTrue(any("scope.role" in e for e in errors))

    def test_unresolvable_and_self_references_are_flagged(self) -> None:
        nodes = [
            scoped_node(
                "narrative.stories.dangling",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "assertion",
                    "suspends": ["physics.gravitation.not_a_real_node"],
                    "governed_by": ["narrative.stories.dangling"],
                },
            )
        ]
        errors = scope_errors(nodes)
        self.assertTrue(any("missing node" in e for e in errors))
        self.assertTrue(any("self-reference" in e for e in errors))

    def test_frame_members_must_agree_on_frame_properties(self) -> None:
        nodes = [
            {"statement_id": GRAVITY},
            scoped_node(
                "narrative.frames.golden_chicken",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                    "suspends": [GRAVITY],
                },
            ),
            scoped_node(
                "narrative.stories.two",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "assertion",
                    "suspends": [],
                },
            ),
        ]
        errors = scope_errors(nodes)
        self.assertTrue(any("disagree on `suspends`" in e for e in errors))

    def test_malformed_scope_values_error_instead_of_crashing(self) -> None:
        nodes = [
            scoped_node("narrative.stories.null_scope", None),
            scoped_node(
                "narrative.stories.scalar_premises",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                    "premises": 42,
                },
            ),
            scoped_node(
                "narrative.stories.string_premises",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                    "premises": "p1",
                },
            ),
            scoped_node(
                "narrative.stories.non_dict_premise",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                    "premises": [None],
                },
            ),
        ]
        errors = scope_errors(nodes)
        self.assertTrue(
            any("null_scope" in e and "must be an object" in e for e in errors)
        )
        self.assertTrue(
            any("scalar_premises" in e and "must be a list" in e for e in errors)
        )
        self.assertTrue(
            any("string_premises" in e and "must be a list" in e for e in errors)
        )
        self.assertTrue(
            any(
                "non_dict_premise" in e and "must be objects" in e
                for e in errors
            )
        )

    def test_reordered_set_valued_lists_are_not_a_disagreement(self) -> None:
        nodes = [
            {"statement_id": GRAVITY},
            {"statement_id": "narrative.frame.frame_consistency"},
            scoped_node(
                "narrative.frames.golden_chicken",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                    "governed_by": [
                        GRAVITY,
                        "narrative.frame.frame_consistency",
                    ],
                },
            ),
            scoped_node(
                "narrative.stories.two",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "assertion",
                    "governed_by": [
                        "narrative.frame.frame_consistency",
                        GRAVITY,
                    ],
                },
            ),
        ]
        self.assertEqual(scope_errors(nodes), [])

    def test_trailing_newline_in_frame_id_is_flagged(self) -> None:
        nodes = [
            scoped_node(
                "narrative.stories.sneaky",
                {"frame": "narrative.frames.golden_chicken\n", "role": "assertion"},
            )
        ]
        errors = scope_errors(nodes)
        self.assertTrue(any("frame-id pattern" in e for e in errors))

    def test_conflicting_premise_expressions_are_flagged(self) -> None:
        nodes = [
            scoped_node(
                "narrative.stories.one",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                    "premises": [
                        {"premise_id": "p1", "expression": "TRAIT(CHICKEN, GOLD)"}
                    ],
                },
            ),
            scoped_node(
                "narrative.stories.two",
                {
                    "frame": "narrative.frames.golden_chicken",
                    "role": "declaration",
                    "premises": [
                        {"premise_id": "p1", "expression": "TRAIT(CHICKEN, TIN)"}
                    ],
                },
            ),
        ]
        errors = scope_errors(nodes)
        self.assertTrue(any("conflicting expressions" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
