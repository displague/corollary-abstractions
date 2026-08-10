"""P-CF1 controls: owned frames derive false belief from event visibility."""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import Verdict  # noqa: E402
from frames import FrameEvent, FrameExecutor, FrameSpec, Literal  # noqa: E402


BASKET = Literal("marble", "located_in", "basket")
NOT_BASKET = BASKET.negated
BOX = Literal("marble", "located_in", "box")
PLACE = FrameEvent(
    "place", (BASKET,), ("sally", "anne", "world"), ("located_in",)
)
MOVE = FrameEvent(
    "move", (NOT_BASKET, BOX), ("anne", "world"), ("located_in",)
)


def belief(owner: str):
    executor = FrameExecutor()
    state = executor.open_frame(
        FrameSpec(frame=f"runtime.frames.belief_{owner}", owner=owner)
    )
    return executor, state


class TheoryOfMindTests(unittest.TestCase):
    def test_sally_false_belief_is_derived_from_missing_the_move(self) -> None:
        executor, sally = belief("sally")
        _, world = belief("world")

        sally = executor.observe_event(sally, PLACE).next_state
        world = executor.observe_event(world, PLACE).next_state
        sally_after_move = executor.observe_event(sally, MOVE).next_state
        world_after_move = executor.observe_event(world, MOVE).next_state

        self.assertEqual(executor.belief_value(sally_after_move, "marble", "located_in"), "basket")
        self.assertEqual(executor.belief_value(world_after_move, "marble", "located_in"), "box")
        self.assertIs(executor.check(sally_after_move, BASKET).verdict, Verdict.VERIFIED)
        self.assertIs(executor.check(world_after_move, BASKET).verdict, Verdict.REFUTED)
        self.assertEqual(sally_after_move.observed_events, (PLACE,))
        self.assertEqual(world_after_move.observed_events, (PLACE, MOVE))

    def test_anne_witnesses_the_move_and_updates(self) -> None:
        executor, anne = belief("anne")
        anne = executor.observe_event(anne, PLACE).next_state
        anne = executor.observe_event(anne, MOVE).next_state
        self.assertEqual(executor.belief_value(anne, "marble", "located_in"), "box")

    def test_unwitnessed_event_cannot_be_replayed_with_forged_visibility(self) -> None:
        executor, sally = belief("sally")
        sally = executor.observe_event(sally, PLACE).next_state
        missed = executor.observe_event(sally, MOVE)
        forged = replace(MOVE, witnessed_by=("sally", "anne", "world"))
        replay = executor.observe_event(missed.next_state, forged)
        self.assertIs(replay.verdict, Verdict.REFUSED)
        self.assertIs(replay.next_state, None)
        self.assertEqual(executor.belief_value(missed.next_state, "marble", "located_in"), "basket")

    def test_observed_event_retry_is_idempotent_but_collision_refuses(self) -> None:
        executor, sally = belief("sally")
        first = executor.observe_event(sally, PLACE)
        retry = executor.observe_event(first.next_state, PLACE)
        collision = executor.observe_event(
            first.next_state,
            replace(PLACE, effects=(BOX,)),
        )
        self.assertIs(retry.verdict, Verdict.VERIFIED)
        self.assertEqual(retry.next_state, first.next_state)
        self.assertIs(collision.verdict, Verdict.REFUSED)

    def test_witnessed_move_supersedes_declaration_backed_belief(self) -> None:
        executor = FrameExecutor()
        state = executor.open_frame(
            FrameSpec(
                frame="runtime.frames.declared_belief",
                owner="sally",
                declarations=(("initial", BASKET),),
            )
        )
        visible_move = replace(MOVE, witnessed_by=("sally", "anne", "world"))
        moved = executor.observe_event(state, visible_move).next_state
        self.assertEqual(executor.belief_value(moved, "marble", "located_in"), "box")
        self.assertIs(executor.check(moved, BASKET).verdict, Verdict.REFUTED)
        self.assertIn("initial", moved.superseded_declarations)

    def test_nonfunctional_positive_values_accumulate(self) -> None:
        executor, sally = belief("sally")
        red = FrameEvent(
            "red", (Literal("marble", "has_trait", "red"),), ("sally",)
        )
        round_ = FrameEvent(
            "round", (Literal("marble", "has_trait", "round"),), ("sally",)
        )
        sally = executor.observe_event(sally, red).next_state
        sally = executor.observe_event(sally, round_).next_state
        self.assertIs(
            executor.check(sally, Literal("marble", "has_trait", "red")).verdict,
            Verdict.VERIFIED,
        )
        self.assertIs(
            executor.check(sally, Literal("marble", "has_trait", "round")).verdict,
            Verdict.VERIFIED,
        )

    def test_ambiguous_nonfunctional_belief_value_refuses_to_guess(self) -> None:
        """Review finding 4: with two accumulated positives, there is no
        'the' belief -- belief_value must raise, not answer the latest."""
        executor, sally = belief("sally")
        red = FrameEvent(
            "red", (Literal("marble", "has_trait", "red"),), ("sally",)
        )
        round_ = FrameEvent(
            "round", (Literal("marble", "has_trait", "round"),), ("sally",)
        )
        sally = executor.observe_event(sally, red).next_state
        sally = executor.observe_event(sally, round_).next_state
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            executor.belief_value(sally, "marble", "has_trait")

    def test_world_truths_do_not_reach_belief_frames_unwitnessed(self) -> None:
        """Review F1 (telepathy): an owned frame adjudicates only local
        truths -- a corpus world truth must not verify or refute a belief
        the owner never witnessed."""
        executor = FrameExecutor(
            {"physics.test.marble_location": (BOX,)}
        )
        state = executor.open_frame(
            FrameSpec(frame="runtime.frames.belief_sally", owner="sally")
        )
        state = executor.observe_event(state, PLACE).next_state
        finding = executor.check(state, BOX)
        self.assertIs(finding.verdict, Verdict.UNKNOWN)
        self.assertIn("unwitnessed", finding.reason)
        # The unowned control keeps world grounding.
        fiction = executor.open_frame(FrameSpec(frame="runtime.frames.tale"))
        self.assertIs(executor.check(fiction, BOX).verdict, Verdict.VERIFIED)

    def test_owned_declarations_may_diverge_from_world_without_suspension(self) -> None:
        """Review F1 companion: belief diverges, fiction rewrites. A
        world-false initial belief opens without suspension; the identical
        unowned declaration is still boundary-rule rejected."""
        executor = FrameExecutor(
            {"physics.test.marble_location": (BOX,)}
        )
        believed = FrameSpec(
            frame="runtime.frames.belief_sally",
            owner="sally",
            declarations=(("initial", BOX.negated),),
        )
        opened = executor.open_frame(believed)
        self.assertIs(executor.check(opened, BOX.negated).verdict,
                      Verdict.VERIFIED)
        with self.assertRaisesRegex(ValueError, "does not suspend"):
            executor.open_frame(
                FrameSpec(
                    frame="runtime.frames.tale",
                    declarations=(("premise", BOX.negated),),
                )
            )

    def test_owned_frames_have_no_suspension_invention_channel(self) -> None:
        """Belief acquires content by witnessing, fiction by inventing:
        assert_literal on an owned frame must not admit through suspends."""
        executor = FrameExecutor(
            {"physics.test.marble_location": (BOX,)}
        )
        state = executor.open_frame(
            FrameSpec(
                frame="runtime.frames.belief_sally",
                owner="sally",
                suspends=("physics.test.marble_location",),
            )
        )
        result = executor.assert_literal(state, "guess", BOX.negated)
        self.assertIs(result.verdict, Verdict.UNKNOWN)
        self.assertIsNone(result.next_state)

    def test_unowned_frame_cannot_consume_attributed_events(self) -> None:
        executor = FrameExecutor()
        state = executor.open_frame(FrameSpec(frame="runtime.frames.unowned"))
        result = executor.observe_event(state, PLACE)
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIs(result.next_state, None)

    def test_owned_frame_persists_instead_of_demoting_on_close(self) -> None:
        executor, sally = belief("sally")
        sally = executor.observe_event(sally, PLACE).next_state
        result = executor.close_frame(sally)
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertEqual(result.state, sally)
        self.assertEqual(result.demoted, ())

    def test_runtime_and_corpus_frame_namespaces_are_explicit(self) -> None:
        with self.assertRaisesRegex(ValueError, "reserved runtime.frames"):
            FrameSpec(frame="narrative.frames.synthetic")
        with self.assertRaisesRegex(ValueError, "corpus-backed"):
            FrameSpec(frame="runtime.frames.synthetic", corpus_backed=True)
        corpus = FrameSpec(
            frame="narrative.frames.cartoon_gravity", corpus_backed=True
        )
        self.assertTrue(corpus.corpus_backed)

    def test_owner_and_event_metadata_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "owner must be non-empty"):
            FrameSpec(frame="runtime.frames.blank_owner", owner=" ")
        with self.assertRaisesRegex(ValueError, "event_id"):
            FrameEvent(" ", (BOX,), ("sally",))
        with self.assertRaisesRegex(ValueError, "at least one effect"):
            FrameEvent("empty", (), ("sally",))
        with self.assertRaisesRegex(ValueError, "must be unique"):
            FrameEvent("duplicate", (BOX,), ("sally", "sally"))
        with self.assertRaisesRegex(ValueError, "must name an event effect"):
            FrameEvent("wrong_function", (BOX,), ("sally",), ("has_trait",))
        with self.assertRaisesRegex(ValueError, "contradictory effects"):
            FrameEvent("incoherent", (BOX, BOX.negated), ("sally",))
        cupboard = Literal("marble", "located_in", "cupboard")
        with self.assertRaisesRegex(ValueError, "competing positive values"):
            FrameEvent(
                "ambiguous_location",
                (BOX, cupboard),
                ("sally",),
                ("located_in",),
            )


class NestedBeliefTests(unittest.TestCase):
    """Nested belief models (the last queued v0.5 cognitive slice).

    Registered predictions (written before adjudication, house rule):

    P-NF1. Second-order false belief is DERIVED purely from witnessed_by
        sets with no new verdict logic: after Anne alone witnesses the
        move, Anne's own frame answers box while Anne's embedded model of
        Sally answers basket -- and check() on the model refutes box.
        (ADJUDICATED: fired in substance, one clause MIS-REGISTERED and
        corrected on the record -- check() on the model leaves box
        UNKNOWN, not REFUTED, and that is the correct semantics: missing
        information is never REFUTED, and a belief model never refutes
        what the modeled agent lacks grounds against. The review caught
        the registered text contradicting its own adjudicating test.)
    P-NF2. Isolation is bidirectional by construction: a parent truth
        never grounds a check inside the child model, and a child truth
        never grounds a check in the parent, using the unchanged check().
    P-NF3. Mutual visibility gates model updates: an event witnessed by
        the parent but not the modeled agent updates the parent and
        leaves the model untouched -- the parent knowingly diverges from
        its model of the other agent.

    Graft-back predictions (v0.7 item 7, registered before the API was
    exercised; BACKLOG "No graft-back API for nested-model mutation"):

    P-NF4. `with_nested` is a pure structural replacement: grafting the
        state `nested()` just returned back at the same path is the
        identity on the parent, and grafting a MUTATED model changes
        exactly that model's tier -- the holder's own truths, obligations
        and event history are untouched, so isolation (P-NF2) survives
        direct mutation exactly as it survives event flow.
    P-NF5. `route` carries the executor's own verdict outward and hands
        back the ROOT, never a detached child: an accepted mutation is
        visible through `nested(root, path)` at any depth, and a rejected
        one returns next_state None, so the root cannot move on a
        rejected branch (the controller invariant, inherited).
    P-NF6. Every ill-formed graft refuses BEFORE producing a state --
        unknown path, absent target, owner-key mismatch, closed ancestor,
        and a poisoned event history all raise. Consequence: the loud
        RuntimeError inside nested delivery becomes reachable only by
        deliberate dataclass surgery, so its control test must document
        itself as bypassing the API rather than using it.
    """

    def _anne_modeling_sally(self):
        executor = FrameExecutor()
        anne = executor.open_frame(
            FrameSpec(frame="runtime.frames.belief_anne", owner="anne")
        )
        anne = executor.open_nested(
            anne, FrameSpec(frame="runtime.frames.anne_models_sally",
                            owner="sally")
        )
        return executor, anne

    def test_second_order_false_belief_is_derived(self) -> None:
        executor, anne = self._anne_modeling_sally()
        anne = executor.observe_event(anne, PLACE).next_state
        move_without_sally = FrameEvent(
            "move", (NOT_BASKET, BOX), ("anne", "world"), ("located_in",)
        )
        anne = executor.observe_event(anne, move_without_sally).next_state

        self.assertEqual(
            executor.belief_value(anne, "marble", "located_in"), "box"
        )
        model_of_sally = executor.nested(anne, ("sally",))
        self.assertEqual(
            executor.belief_value(model_of_sally, "marble", "located_in"),
            "basket",
        )
        self.assertIs(
            executor.check(model_of_sally, BOX).verdict, Verdict.UNKNOWN
        )
        self.assertIs(
            executor.check(model_of_sally, BASKET).verdict, Verdict.VERIFIED
        )

    def test_isolation_is_bidirectional(self) -> None:
        executor, anne = self._anne_modeling_sally()
        anne_only = FrameEvent(
            "secret", (Literal("key", "located_in", "drawer"),),
            ("anne",), ("located_in",)
        )
        anne = executor.observe_event(anne, anne_only).next_state
        model_of_sally = executor.nested(anne, ("sally",))
        self.assertIs(
            executor.check(
                model_of_sally, Literal("key", "located_in", "drawer")
            ).verdict,
            Verdict.UNKNOWN,
        )
        # Review should-fix 5: the child-to-parent half through a REAL
        # flow -- the child opens with a declaration the parent never
        # holds; no state surgery required.
        executor2 = FrameExecutor()
        parent = executor2.open_frame(
            FrameSpec(frame="runtime.frames.belief_anne", owner="anne")
        )
        parent = executor2.open_nested(
            parent,
            FrameSpec(
                frame="runtime.frames.anne_models_sally",
                owner="sally",
                declarations=(
                    ("d1", Literal("door", "located_in", "hall")),
                ),
            ),
        )
        self.assertIs(
            executor2.check(
                parent, Literal("door", "located_in", "hall")
            ).verdict,
            Verdict.UNKNOWN,
        )
        self.assertIs(
            executor2.check(
                executor2.nested(parent, ("sally",)),
                Literal("door", "located_in", "hall"),
            ).verdict,
            Verdict.VERIFIED,
        )

    def test_mutual_visibility_gates_model_updates(self) -> None:
        executor, anne = self._anne_modeling_sally()
        anne = executor.observe_event(anne, PLACE).next_state
        before = executor.nested(anne, ("sally",))
        anne_only_move = FrameEvent(
            "move", (NOT_BASKET, BOX), ("anne",), ("located_in",)
        )
        anne = executor.observe_event(anne, anne_only_move).next_state
        after = executor.nested(anne, ("sally",))
        self.assertEqual(before.asserted, after.asserted)
        self.assertEqual(
            executor.belief_value(anne, "marble", "located_in"), "box"
        )

    def test_grandchild_needs_every_owner_on_the_path(self) -> None:
        executor, anne = self._anne_modeling_sally()
        model_of_sally = executor.nested(anne, ("sally",))
        nested_model = executor.open_nested(
            model_of_sally,
            FrameSpec(frame="runtime.frames.sally_models_ben", owner="ben"),
        )
        anne = executor.with_nested(anne, ("sally",), nested_model)
        partial = FrameEvent(
            "partial", (BASKET,), ("anne", "sally"), ("located_in",)
        )
        anne = executor.observe_event(anne, partial).next_state
        grandchild = executor.nested(anne, ("sally", "ben"))
        self.assertEqual(grandchild.asserted, ())
        # The cut is exactly at ben's tier: sally's model DID update.
        self.assertEqual(
            executor.belief_value(
                executor.nested(anne, ("sally",)), "marble", "located_in"
            ),
            "basket",
        )
        # Review should-fix 2: the leaf-only-bug discriminator -- ben
        # witnessed but the INTERMEDIATE sally did not; nothing below the
        # break in the path may update.
        skip_middle = FrameEvent(
            "skip", (BOX,), ("anne", "ben"), ("located_in",)
        )
        anne = executor.observe_event(anne, skip_middle).next_state
        self.assertEqual(
            executor.nested(anne, ("sally", "ben")).asserted, ()
        )
        self.assertEqual(
            executor.belief_value(
                executor.nested(anne, ("sally",)), "marble", "located_in"
            ),
            "basket",
        )
        full = FrameEvent(
            "full", (BOX,), ("anne", "sally", "ben"), ("located_in",)
        )
        anne = executor.observe_event(anne, full).next_state
        grandchild = executor.nested(anne, ("sally", "ben"))
        self.assertEqual(
            executor.belief_value(grandchild, "marble", "located_in"), "box"
        )

    def test_parent_cannot_learn_through_eyes_it_does_not_have(self) -> None:
        """Review should-fix 3: an event invisible to the parent leaves
        the model untouched even when the modeled agent witnessed it, and
        the visibility-rewrite guard keeps parent and child consistent."""
        executor, anne = self._anne_modeling_sally()
        sally_only = FrameEvent(
            "sally_only", (BASKET,), ("sally",), ("located_in",)
        )
        anne = executor.observe_event(anne, sally_only).next_state
        model = executor.nested(anne, ("sally",))
        self.assertEqual(model.asserted, ())
        self.assertEqual(model.processed_event_ids, ())
        rewrite = FrameEvent(
            "sally_only", (BASKET,), ("anne", "sally"), ("located_in",)
        )
        replay = executor.observe_event(anne, rewrite)
        self.assertIs(replay.verdict, Verdict.REFUSED)
        self.assertIn("cannot be rewritten", replay.reason)

    def test_cannot_nest_inside_a_closed_frame(self) -> None:
        executor, anne = self._anne_modeling_sally()
        closed = replace(anne, closed=True)
        with self.assertRaisesRegex(ValueError, "closed frame"):
            executor.open_nested(
                closed, FrameSpec(frame="runtime.frames.x", owner="ben")
            )

    def test_broken_subset_invariant_fails_loudly(self) -> None:
        """Review should-fix 6: a child refusal inside recursion must
        surface, not silently fork parent and model histories.

        DELIBERATE API BYPASS. The poisoned state is built with raw
        `replace` because `with_nested` now REFUSES exactly this graft
        (asserted below): a model whose event history is not a subset of
        its holder's. The surgery is the point -- it is the only way left
        to reach the RuntimeError, which is the control this test exists
        for. Real flows and the graft API can no longer construct it.
        """
        executor, anne = self._anne_modeling_sally()
        poisoned_child = replace(
            executor.nested(anne, ("sally",)),
            processed_event_ids=("z",),
        )
        with self.assertRaisesRegex(ValueError, "subset invariant"):
            executor.with_nested(anne, ("sally",), poisoned_child)
        anne = replace(anne, children=(("sally", poisoned_child),))
        event = FrameEvent("z", (BASKET,), ("anne", "sally"), ("located_in",))
        with self.assertRaisesRegex(RuntimeError, "subset invariant"):
            executor.observe_event(anne, event)

    def test_graft_back_replaces_exactly_one_model_tier(self) -> None:
        """P-NF4: regrafting is the identity; a mutated graft moves only
        the model's own tier, never its holder's."""
        executor, anne = self._anne_modeling_sally()
        anne = executor.observe_event(anne, PLACE).next_state
        model = executor.nested(anne, ("sally",))
        self.assertEqual(executor.with_nested(anne, ("sally",), model), anne)

        planted = executor.plant(model, "letter_seen", "the letter")
        grafted = executor.with_nested(anne, ("sally",), planted.next_state)
        self.assertEqual(
            executor.nested(grafted, ("sally",)).obligations,
            planted.next_state.obligations,
        )
        # The holder's own tier is untouched: isolation survives direct
        # mutation exactly as it survives event flow.
        self.assertEqual(grafted.obligations, ())
        self.assertEqual(grafted.asserted, anne.asserted)
        self.assertEqual(grafted.observed_events, anne.observed_events)
        # And the input parent is unchanged -- frozen dataclasses, no
        # in-place edit of the spine.
        self.assertEqual(executor.nested(anne, ("sally",)).obligations, ())

    def test_grafting_reaches_a_grandchild_through_its_owner_path(self) -> None:
        executor, anne = self._anne_modeling_sally()
        anne = executor.with_nested(
            anne,
            ("sally",),
            executor.open_nested(
                executor.nested(anne, ("sally",)),
                FrameSpec(
                    frame="runtime.frames.sally_models_ben", owner="ben"
                ),
            ),
        )
        ben = executor.nested(anne, ("sally", "ben"))
        declared = executor.with_nested(
            anne,
            ("sally", "ben"),
            replace(
                ben,
                asserted=(("d", Literal("door", "located_in", "hall")),),
            ),
        )
        self.assertIs(
            executor.check(
                executor.nested(declared, ("sally", "ben")),
                Literal("door", "located_in", "hall"),
            ).verdict,
            Verdict.VERIFIED,
        )
        for path in ((), ("sally",)):
            self.assertIs(
                executor.check(
                    executor.nested(declared, path),
                    Literal("door", "located_in", "hall"),
                ).verdict,
                Verdict.UNKNOWN,
            )

    def test_routed_mutation_returns_the_root_and_rejections_do_not(self) -> None:
        """P-NF5: route hands back the ROOT on accept and nothing on a
        rejected branch."""
        executor, anne = self._anne_modeling_sally()
        planted = executor.route(
            anne,
            ("sally",),
            lambda model: executor.plant(model, "letter_seen", "the letter"),
        )
        self.assertIs(planted.verdict, Verdict.VERIFIED)
        root = planted.next_state
        self.assertEqual(root.spec.frame, anne.spec.frame)
        self.assertEqual(
            executor.nested(root, ("sally",)).obligations[0].element,
            "the letter",
        )
        self.assertEqual(root.obligations, ())

        discharged = executor.route(
            root,
            ("sally",),
            lambda model: executor.discharge(model, "letter_read", "the letter"),
        )
        self.assertIs(discharged.verdict, Verdict.VERIFIED)
        self.assertFalse(
            executor.nested(discharged.next_state, ("sally",))
            .obligations[0]
            .outstanding
        )

        unheralded = executor.route(
            root,
            ("sally",),
            lambda model: executor.discharge(model, "gift", "a sudden gift"),
        )
        self.assertIs(unheralded.verdict, Verdict.UNKNOWN)
        self.assertIsNone(unheralded.next_state)
        # A closed ancestor REFUSES like any other closed frame: 'closed'
        # is a verdict in this executor, never an exception.
        shut = executor.route(
            replace(anne, closed=True),
            ("sally",),
            lambda model: executor.plant(model, "letter_seen", "the letter"),
        )
        self.assertIs(shut.verdict, Verdict.REFUSED)
        self.assertIsNone(shut.next_state)
        self.assertIn("closed", shut.reason)
        with self.assertRaisesRegex(KeyError, "no embedded model"):
            executor.route(anne, ("ben",), lambda model: model)
        # The degenerate empty route is the root itself.
        at_root = executor.route(
            anne, (), lambda state: executor.plant(state, "own", "her own plan")
        )
        self.assertEqual(at_root.next_state.obligations[0].element, "her own plan")
        self.assertEqual(at_root.next_state.children, anne.children)

    def test_graft_refusals_are_principled(self) -> None:
        """P-NF6: every ill-formed graft raises before producing state."""
        executor, anne = self._anne_modeling_sally()
        model = executor.nested(anne, ("sally",))
        with self.assertRaisesRegex(ValueError, "non-empty owner path"):
            executor.with_nested(anne, (), model)
        with self.assertRaisesRegex(KeyError, "ben"):
            executor.with_nested(anne, ("ben",), model)
        with self.assertRaisesRegex(KeyError, "no embedded model"):
            executor.with_nested(anne, ("ben", "sally"), model)
        # Grafting replaces; creation keeps open_nested's refusals.
        ben_model = executor.open_frame(
            FrameSpec(frame="runtime.frames.anne_models_ben", owner="ben")
        )
        with self.assertRaisesRegex(KeyError, "open_nested creates one"):
            executor.with_nested(anne, ("sally", "ben"), ben_model)
        with self.assertRaisesRegex(ValueError, "child-owner key"):
            executor.with_nested(anne, ("sally",), ben_model)
        with self.assertRaisesRegex(ValueError, "closed frame"):
            executor.with_nested(replace(anne, closed=True), ("sally",), model)
        # A self-model stays refused through the graft door. At the graft
        # site itself the child-owner key check subsumes it (an anne-owned
        # model cannot be keyed 'sally' in the first place), so the case
        # that needs its own guard is a self-model buried INSIDE a grafted
        # subtree, where no key check would catch it.
        with self.assertRaisesRegex(ValueError, "declares owner"):
            executor.with_nested(anne, ("sally",), ben_model)
        self_model = replace(
            model,
            children=(
                (
                    "sally",
                    executor.open_frame(
                        FrameSpec(
                            frame="runtime.frames.sally_models_sally",
                            owner="sally",
                        )
                    ),
                ),
            ),
        )
        with self.assertRaisesRegex(ValueError, "itself"):
            executor.with_nested(anne, ("sally",), self_model)

    def test_graft_rejects_a_model_carrying_a_forged_history(self) -> None:
        """The subset invariant is checked over the whole grafted subtree,
        not just its root: a poisoned grandchild refuses too."""
        executor, anne = self._anne_modeling_sally()
        anne = executor.observe_event(anne, PLACE).next_state
        model = executor.nested(anne, ("sally",))
        forged = replace(
            PLACE, witnessed_by=("sally", "anne", "world"), effects=(BOX,)
        )
        with self.assertRaisesRegex(ValueError, "subset invariant"):
            executor.with_nested(
                anne, ("sally",), replace(model, observed_events=(forged,))
            )
        with_ben = executor.open_nested(
            model, FrameSpec(frame="runtime.frames.sally_models_ben", owner="ben")
        )
        poisoned = replace(
            with_ben,
            children=(
                (
                    "ben",
                    replace(
                        with_ben.child("ben"), processed_event_ids=("ghost",)
                    ),
                ),
            ),
        )
        with self.assertRaisesRegex(ValueError, "subset invariant"):
            executor.with_nested(anne, ("sally",), poisoned)

    def test_nesting_refusals_are_principled(self) -> None:
        executor = FrameExecutor()
        fiction = executor.open_frame(FrameSpec(frame="runtime.frames.tale"))
        anne = executor.open_frame(
            FrameSpec(frame="runtime.frames.belief_anne", owner="anne")
        )
        with self.assertRaisesRegex(ValueError, "OWNED parent"):
            executor.open_nested(
                fiction,
                FrameSpec(frame="runtime.frames.x", owner="sally"),
            )
        with self.assertRaisesRegex(ValueError, "must be owned"):
            executor.open_nested(
                anne, FrameSpec(frame="runtime.frames.inner_tale")
            )
        with self.assertRaisesRegex(ValueError, "itself"):
            executor.open_nested(
                anne, FrameSpec(frame="runtime.frames.self", owner="anne")
            )
        nested = executor.open_nested(
            anne, FrameSpec(frame="runtime.frames.m", owner="sally")
        )
        with self.assertRaisesRegex(ValueError, "already embeds"):
            executor.open_nested(
                nested, FrameSpec(frame="runtime.frames.m2", owner="sally")
            )


if __name__ == "__main__":
    unittest.main()
