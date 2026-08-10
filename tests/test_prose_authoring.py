"""Adjudicating tests for open-prose authoring (P-PR1..P-PR6).

These bind the predictions registered in ``scripts/prose.py`` to falsifiable
behavior: surface varies while facts do not (P-PR1), the moved-fact control has
teeth (P-PR2), the pointer beats the exact template on lexical variety with both
at ceiling fidelity (P-PR3), facts survive a serialize/restart byte-stable
(P-PR4), an unrenderable fact degrades to ASK not a guess (P-PR5), and nothing
is invented (P-PR6).
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from conversation import (  # noqa: E402
    ConversationSession,
    golden_chicken_revision_session,
)
from prose import (  # noqa: E402
    DeusRenderer,
    ExactTemplateRenderer,
    Fact,
    MovedColorRenderer,
    ProseAsk,
    Rendered,
    SurfacePointerRenderer,
    accepted_facts,
    author_prose,
    faithfulness,
    is_faithful,
    measure,
)
from session_keys import SessionKeyRing  # noqa: E402

SEEDS = tuple(range(50))


def _bound_session(owner: str = "alice", color: str = "copper", ring=None):
    session = golden_chicken_revision_session(owner, ring)
    session.ask_and_reply("egg_color", color)
    return session


def _accepted(session) -> frozenset[Fact]:
    color = session.verifier.binding_value(session.state, "egg_color")
    return accepted_facts(session.story_state, color)


class AcceptedFactsTests(unittest.TestCase):
    def test_facts_are_the_story_beats_plus_the_signed_binding(self) -> None:
        session = _bound_session(color="copper")
        facts = _accepted(session)
        kinds = {f.kind for f in facts}
        # Every accepted beat/binding, nothing else.
        self.assertEqual(
            kinds,
            {
                "agent",
                "trait",
                "desire",
                "obstacle",
                "outcome",
                "planted",
                "discharged",
                "egg_color",
            },
        )
        color_fact = next(f for f in facts if f.kind == "egg_color")
        self.assertEqual(color_fact.value, "copper")


class SurfaceVariesFactsInvariantTests(unittest.TestCase):
    """P-PR1: surface varies across seeds; the accepted-fact set does not."""

    def test_surface_varies_but_facts_are_invariant(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        pointer = SurfacePointerRenderer()
        renders = [pointer.render(accepted, s) for s in SEEDS]

        # Facts byte-invariant across every seed.
        for r in renders:
            self.assertEqual(r.provenance, accepted)
        # Surface genuinely varies: the vast majority of seeds are distinct.
        distinct = {r.text for r in renders}
        self.assertGreaterEqual(len(distinct), 40)

    def test_render_is_deterministic_for_a_seed(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        pointer = SurfacePointerRenderer()
        self.assertEqual(
            pointer.render(accepted, 7).text, pointer.render(accepted, 7).text
        )


class MovedFactControlTests(unittest.TestCase):
    """P-PR2: faithful renders pass; adversaries that move a fact are caught."""

    def test_faithful_renders_pass_for_both_arms(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        for renderer in (SurfacePointerRenderer(), ExactTemplateRenderer()):
            for s in SEEDS:
                self.assertTrue(is_faithful(renderer.render(accepted, s), accepted))

    def test_moved_fact_control_catches_the_adversaries(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))

        moved = MovedColorRenderer("silver").render(accepted, 3)
        reasons = faithfulness(moved, accepted)
        self.assertTrue(reasons)
        self.assertFalse(is_faithful(moved, accepted))
        self.assertTrue(any("egg_color" in r or "egg color" in r for r in reasons))
        # The honest color genuinely left the surface.
        self.assertNotIn("copper", moved.text.lower())

        deus = DeusRenderer().render(accepted, 3)
        deus_reasons = faithfulness(deus, accepted)
        self.assertTrue(deus_reasons)
        self.assertFalse(is_faithful(deus, accepted))
        self.assertTrue(any("feather" in r for r in deus_reasons))
        self.assertNotIn("feather", deus.text.lower())


class TwoArmMetricTests(unittest.TestCase):
    """P-PR3: both arms preserve everything; pointer wins on lexical variety."""

    def test_two_arm_metric_comparison(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        pointer = SurfacePointerRenderer()
        template = ExactTemplateRenderer()

        pm = measure(tuple(pointer.render(accepted, s) for s in SEEDS), accepted)
        tm = measure(tuple(template.render(accepted, s) for s in SEEDS), accepted)

        # Fidelity axes at ceiling for BOTH arms.
        for m in (pm, tm):
            self.assertEqual(m.premise_preservation, 1.0)
            self.assertEqual(m.required_beat_coverage, 1.0)
            self.assertEqual(m.temporal_consistency, 1.0)
            self.assertIsNone(m.human_preference)  # deferred, not faked

        # Lexical variety strictly higher for the pointer, on two measures.
        self.assertGreater(pm.distinct_surface_ratio, tm.distinct_surface_ratio)
        self.assertGreater(pm.mean_pairwise_jaccard, tm.mean_pairwise_jaccard)
        # And the template arm is genuinely low-variety (bounded by templates).
        self.assertLessEqual(tm.distinct_surface_ratio, 0.1)
        self.assertGreaterEqual(pm.distinct_surface_ratio, 0.9)


class SerializeRestartTests(unittest.TestCase):
    """P-PR4: accepted facts survive a real process boundary byte-stable."""

    def test_serialize_restart_preserves_facts(self) -> None:
        pointer = SurfacePointerRenderer()
        with tempfile.TemporaryDirectory() as raw:
            workdir = Path(raw)
            keyfile = workdir / "keys.json"
            ring = SessionKeyRing.open(keyfile)

            alice = _bound_session("alice", "copper", ring)
            accepted_pre = _accepted(alice)
            rendered_pre = pointer.render(accepted_pre, 5)
            self.assertTrue(is_faithful(rendered_pre, accepted_pre))

            session_file = workdir / "alice.session.json"
            alice.save(session_file)

            # Restart: drop every in-process authority, reload from the ring.
            del alice, ring
            reloaded = SessionKeyRing.open(keyfile)
            alice2, report = ConversationSession.restore(session_file, reloaded)
            self.assertEqual(len(report.refused), 0)

            accepted_post = _accepted(alice2)
            # The fact set the prose preserves is byte-identical across restart.
            self.assertEqual(accepted_post, accepted_pre)
            # Same seed reproduces the surface; a new seed varies it.
            self.assertEqual(
                pointer.render(accepted_post, 5).text, rendered_pre.text
            )
            self.assertNotEqual(
                pointer.render(accepted_post, 9).text, rendered_pre.text
            )
            # Revisable after restart: a new binding moves the color fact only.
            alice2.say("actually, make them gold")
            accepted_revised = _accepted(alice2)
            self.assertEqual(
                {f for f in accepted_revised if f.kind != "egg_color"},
                {f for f in accepted_pre if f.kind != "egg_color"},
            )
            self.assertEqual(
                next(f for f in accepted_revised if f.kind == "egg_color").value,
                "gold",
            )


class AskNotGuessTests(unittest.TestCase):
    """P-PR5: an unrenderable fact degrades to a WAITING ASK, never a guess."""

    def test_unrenderable_fact_degrades_to_ask(self) -> None:
        session = golden_chicken_revision_session("alice")  # no binding yet
        pointer = SurfacePointerRenderer()

        result = author_prose(session, pointer, seed=1)
        self.assertIsInstance(result, ProseAsk)
        self.assertEqual(result.slot, "egg_color")
        self.assertTrue(result.prompt)
        # No fact was fabricated to fill the prose.
        self.assertIsNone(session.verifier.binding_value(session.state, "egg_color"))

        # Answering the very question the author asked lets it render.
        reply = session.verifier.reply_action(session.state, "copper")
        session.run_turn((reply,))
        rendered = author_prose(session, pointer, seed=1)
        self.assertIsInstance(rendered, Rendered)
        self.assertIn("copper", rendered.text.lower())

    def test_naming_an_unaccepted_fact_kind_asks_rather_than_invents(self) -> None:
        session = _bound_session(color="copper")
        pointer = SurfacePointerRenderer()
        result = author_prose(session, pointer, seed=1, require_kind="chicken_name")
        self.assertIsInstance(result, ProseAsk)
        self.assertEqual(result.slot, "chicken_name")
        # The story never gained a chicken_name fact.
        self.assertFalse(
            any(f.kind == "chicken_name" for f in _accepted_no_reopen(session))
        )


def _accepted_no_reopen(session) -> frozenset[Fact]:
    # The ASK reopened a pending 'chicken_name' slot; read facts off the story
    # + the still-intact egg_color binding, which the ASK never touched.
    return accepted_facts(session.story_state, "copper")


class NoneInventedTests(unittest.TestCase):
    """P-PR6: no render across either arm invents a fact."""

    def test_no_render_invents_a_fact(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        for renderer in (SurfacePointerRenderer(), ExactTemplateRenderer()):
            for s in SEEDS:
                r = renderer.render(accepted, s)
                self.assertEqual(r.provenance, accepted)
                # faithfulness() folds the foreign-anchor scan; empty == clean.
                self.assertEqual(faithfulness(r, accepted), ())


if __name__ == "__main__":
    unittest.main()
