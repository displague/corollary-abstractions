"""P-LS3: story brief is structured; English and binds come from realizers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from narrative_realize import (  # noqa: E402
    FRAGMENT_ID,
    GOLDEN_CHICKEN_BRIEF,
    NarrativeBrief,
    bind_spec,
    realize_outcome_used_as_key,
    realize_plant_gleamed_nest,
    span_of,
)
from oracle_controller_demo import (  # noqa: E402
    StoryFrameVerifier,
    story_oracle_actions,
    story_oracle_run,
)
from controller import Verdict  # noqa: E402


class RealizePatternsTests(unittest.TestCase):
    def test_plant_and_outcome_match_historical_oracle_prose(self) -> None:
        # Regression: surface must stay byte-identical to the old hardcoding
        # so existing beat assertions and demos do not silently drift.
        self.assertEqual(
            realize_plant_gleamed_nest("fallen feather"),
            "A fallen feather gleamed beside its nest.",
        )
        self.assertEqual(
            realize_outcome_used_as_key("fallen feather", "key"),
            (
                "It used a fallen feather as a key, stepped outside, "
                "and sang until the sun rose"
            ),
        )

    def test_binds_are_computed_not_hand_authored(self) -> None:
        brief = GOLDEN_CHICKEN_BRIEF
        mention = brief.realize_plant_mention()
        start, end = span_of(mention, brief.plant_surface)
        self.assertEqual(brief.plant_binds(), f"{brief.plant_element}@{start}:{end}")
        self.assertEqual(mention[start:end], brief.plant_surface)

        outcome = brief.realize_outcome()
        for part in brief.outcome_binds().split(";"):
            element, span = part.split("@")
            a, b = (int(x) for x in span.split(":"))
            surface = (
                brief.plant_surface
                if element == brief.plant_element
                else brief.decoy_surface
            )
            self.assertEqual(outcome[a:b], surface)

    def test_oracle_actions_contain_no_magic_bind_literals_as_source(self) -> None:
        # Policy path: binds on actions equal re-computed binds from realizers.
        actions = {a.name: a for a in story_oracle_actions()}
        plant = dict(actions["plant"].arguments)
        self.assertEqual(plant["binds"], GOLDEN_CHICKEN_BRIEF.plant_binds())
        self.assertEqual(
            plant["mention"], GOLDEN_CHICKEN_BRIEF.realize_plant_mention()
        )
        resolve = dict(actions["resolve"].arguments)
        self.assertEqual(resolve["binds"], GOLDEN_CHICKEN_BRIEF.outcome_binds())
        self.assertEqual(
            resolve["outcome"], GOLDEN_CHICKEN_BRIEF.realize_outcome()
        )

    def test_unknown_pattern_refuses_at_brief_construction(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            NarrativeBrief(
                id="bad",
                agent="a",
                desire="d",
                trait="t",
                denied_trait="u",
                plant_element="e",
                plant_surface="e",
                plant_pattern="not_a_pattern",
                decoy_element="k",
                decoy_surface="k",
                obstacle="o",
                outcome_pattern="used_as_key_and_sang",
            )
        self.assertIn(FRAGMENT_ID, str(ctx.exception))


class OracleStillSolvesTests(unittest.TestCase):
    def test_brief_driven_oracle_still_solves_five_verified_steps(self) -> None:
        run = story_oracle_run()
        self.assertTrue(run.solved)
        self.assertEqual(run.accepted_steps, 5)
        self.assertTrue(
            all(e.verification.verdict is Verdict.VERIFIED for e in run.trace)
        )
        self.assertIn("fallen feather", run.final_state.beats[0].text)
        self.assertIn("fallen feather as a key", run.final_state.beats[-1].text)

    def test_bind_spec_helper_matches_adapter_expectations(self) -> None:
        text = "xx fallen feather yy"
        self.assertEqual(
            bind_spec("fallen feather", text, "fallen feather"),
            "fallen feather@3:17",
        )

    def test_alternate_brief_same_patterns_also_solves(self) -> None:
        """P-LS3: second brief, same pattern inventory, different slots."""
        from controller import Controller, SequencePolicy
        from oracle_controller_demo import (
            NarrativeElement,
            StoryFrameVerifier,
        )

        brief = NarrativeBrief(
            id="copper_bell",
            agent="the copper bell",
            desire="to mark the hour",
            trait="copper",
            denied_trait="iron",
            plant_element="loose clapper",
            plant_surface="loose clapper",
            plant_pattern="gleamed_beside_nest",
            decoy_element="rope",
            decoy_surface="rope",
            obstacle="the frozen tower door",
            outcome_pattern="used_as_key_and_sang",
        )
        from frames import (
            CHEKHOV_GUN,
            FRAME_CONSISTENCY,
            NO_DEUS,
            FrameSpec,
            Literal,
        )

        spec = FrameSpec(
            frame="runtime.frames.copper_bell",
            title="copper bell",
            declarations=(
                ("agent", Literal("story", "agent", brief.agent)),
                ("copper", Literal(brief.agent, "trait", "copper")),
                (
                    "no_iron",
                    Literal(brief.agent, "trait", "iron", polarity=False),
                ),
            ),
            governed_by=(FRAME_CONSISTENCY, CHEKHOV_GUN, NO_DEUS),
        )
        elements = (
            NarrativeElement(brief.plant_element, (brief.plant_surface,)),
            NarrativeElement(brief.decoy_element, (brief.decoy_surface,)),
        )
        verifier = StoryFrameVerifier(spec=spec, elements=elements)
        run = Controller(max_steps=5).run(
            verifier.initial_state(),
            SequencePolicy(brief.oracle_actions()),
            verifier,
            lambda state: (
                tuple(b.role for b in state.beats)
                == ("setup", "complication", "resolution")
                and bool(state.frame_state.obligations)
                and not any(o.outstanding for o in state.frame_state.obligations)
            ),
        )
        self.assertTrue(run.solved)
        self.assertEqual(run.accepted_steps, 5)
        self.assertIn("loose clapper", run.final_state.beats[0].text)


class TraitDenyFluencyTests(unittest.TestCase):
    """P-LS2: trait packaging variants cannot launder silver to VERIFIED."""

    def test_twenty_silver_packages_all_refuted(self) -> None:
        from controller import Action, ActionKind
        from narrative_realize import SILVER_TRAIT_PACKAGES, package_trait_denotation
        from oracle_controller_demo import StoryFrameVerifier

        self.assertGreaterEqual(len(SILVER_TRAIT_PACKAGES), 20)
        initial = story_oracle_run().initial_state
        verifier = StoryFrameVerifier()
        for surface in SILVER_TRAIT_PACKAGES:
            trait = package_trait_denotation(surface)
            self.assertEqual(trait, "silver", surface)
            action = Action.build(
                ActionKind.GEN,
                "introduce",
                {
                    "agent": "the golden chicken",
                    "trait": trait,
                    "desire": "to sing the sunrise awake",
                },
            )
            result = verifier.evaluate(initial, action)
            self.assertIs(
                result.verdict,
                Verdict.REFUTED,
                f"package={surface!r} laundered to {result.verdict}",
            )

    def test_five_golden_package_controls_verified(self) -> None:
        from controller import Action, ActionKind
        from narrative_realize import package_trait_denotation
        from oracle_controller_demo import StoryFrameVerifier

        packages = (
            "golden",
            "appears golden",
            "gold-colored",
            "golden",
            "appears golden",
        )
        initial = story_oracle_run().initial_state
        verifier = StoryFrameVerifier()
        for surface in packages:
            trait = package_trait_denotation(surface)
            self.assertEqual(trait, "golden", surface)
            action = Action.build(
                ActionKind.GEN,
                "introduce",
                {
                    "agent": "the golden chicken",
                    "trait": trait,
                    "desire": "to keep watch",
                },
            )
            result = verifier.evaluate(initial, action)
            self.assertIs(result.verdict, Verdict.VERIFIED)


if __name__ == "__main__":
    unittest.main()
