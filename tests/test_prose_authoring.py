"""Adjudicating tests for open-prose authoring (P-PR1..P-PR6).

These bind the predictions registered in ``scripts/prose.py`` to falsifiable
behavior: surface varies while facts do not (P-PR1), the moved-fact control has
teeth (P-PR2), the pointer beats the exact template on lexical variety with both
at ceiling fidelity (P-PR3), facts survive a serialize/restart byte-stable
(P-PR4), an unrenderable fact degrades to ASK not a guess (P-PR5), and nothing
is invented (P-PR6).

The moved-fact control is a CLOSURE check (``prose.faithfulness``). Independent
adversarial review found the earlier presence check unsound: it certified four
fact-moving renderers as faithful. Those four — added premise, right-value/
wrong-owner, negation, dropped beat — are pinned here as regression cases that
must all be CAUGHT, alongside a proof that the gate ignores self-attested
provenance.
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
from prose import _beats_present  # noqa: E402
from session_keys import SessionKeyRing  # noqa: E402

SEEDS = tuple(range(50))

# Individual approved segments, reused to build the review's fact-moving and
# ordering adversaries by appending/replacing/reordering exactly one thing.
_SETUP1 = "The golden chicken wanted to sing the sunrise awake."
_FEATHER = "A fallen feather rested by the nest."
_COMPLICATION = "But the locked coop door stood in the way."
_RESOLUTION = "It used a fallen feather as a key, and sang until the sun rose."
_CODA = "Now the golden chicken laid copper eggs."

# A faithful body (setup..resolution) and a full faithful render.
_BODY = " ".join((_SETUP1, _FEATHER, _COMPLICATION, _RESOLUTION))
_FAITHFUL = _BODY + " " + _CODA


def _bound_session(owner: str = "alice", color: str = "copper", ring=None):
    session = golden_chicken_revision_session(owner, ring)
    session.ask_and_reply("egg_color", color)
    return session


def _accepted(session) -> frozenset[Fact]:
    color = session.verifier.binding_value(session.state, "egg_color")
    return accepted_facts(session.story_state, color)


def _as_render(text: str, accepted: frozenset[Fact], arm: str) -> Rendered:
    # provenance is set EQUAL to the accepted set on purpose: an adversary that
    # lies in provenance must still be caught by the surface-only closure gate.
    return Rendered(text, accepted, arm, 0)


def _adversaries(accepted: frozenset[Fact]) -> dict[str, Rendered]:
    """The review's four fact-moving renderers, each built to look faithful to a
    presence check (accepted anchors present, provenance == accepted)."""

    return {
        "added-premise": _as_render(
            _FAITHFUL
            + " The golden chicken was a thief who had poisoned the farmer's well.",
            accepted,
            "adversary-added-premise",
        ),
        "wrong-owner": _as_render(
            _BODY
            + " The neighbour's grey duck, not the golden chicken, laid the copper eggs.",
            accepted,
            "adversary-wrong-owner",
        ),
        "negation": _as_render(
            _BODY + " It did not really lay copper eggs at all; that was a lie.",
            accepted,
            "adversary-negation",
        ),
        # Drops the complication beat entirely (keeps only approved segments);
        # closure must catch the uncovered obstacle fact.
        "dropped-beat": _as_render(
            "The golden chicken wanted to sing the sunrise awake. "
            "A fallen feather rested by the nest. "
            "It used a fallen feather as a key, and sang until the sun rose. "
            "Now the golden chicken laid copper eggs.",
            accepted,
            "adversary-dropped-beat",
        ),
    }


class AcceptedFactsTests(unittest.TestCase):
    def test_facts_are_the_story_beats_plus_the_signed_binding(self) -> None:
        session = _bound_session(color="copper")
        facts = _accepted(session)
        self.assertEqual(
            {f.kind for f in facts},
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
        self.assertEqual(
            next(f for f in facts if f.kind == "egg_color").value, "copper"
        )

    def test_anchors_are_derived_from_the_story_not_hardcoded(self) -> None:
        facts = _accepted(_bound_session(color="copper"))
        # Anchors come from significant_tokens() over the real story values.
        self.assertEqual(
            next(f for f in facts if f.kind == "obstacle").anchors,
            ("locked", "coop", "door"),
        )
        self.assertEqual(
            next(f for f in facts if f.kind == "outcome").anchors,
            ("sang", "sun", "rose"),
        )


class SurfaceVariesFactsInvariantTests(unittest.TestCase):
    """P-PR1: surface varies across seeds; the accepted-fact set does not."""

    def test_surface_varies_but_facts_are_invariant(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        pointer = SurfacePointerRenderer()
        renders = [pointer.render(accepted, s) for s in SEEDS]
        for r in renders:
            self.assertEqual(r.provenance, accepted)
        self.assertGreaterEqual(len({r.text for r in renders}), 40)

    def test_render_is_deterministic_for_a_seed(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        pointer = SurfacePointerRenderer()
        self.assertEqual(
            pointer.render(accepted, 7).text, pointer.render(accepted, 7).text
        )


class MovedFactControlTests(unittest.TestCase):
    """P-PR2: faithful renders pass; every fact-moving adversary is caught."""

    def test_faithful_renders_pass_for_both_arms(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        for renderer in (SurfacePointerRenderer(), ExactTemplateRenderer()):
            for s in SEEDS:
                self.assertTrue(is_faithful(renderer.render(accepted, s), accepted))

    def test_closure_gate_ignores_self_attested_provenance(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        # Honest surface, EMPTY provenance -> still faithful (gate reads surface).
        faithful_lie = Rendered(_FAITHFUL, frozenset(), "surface-pointer", 0)
        self.assertTrue(is_faithful(faithful_lie, accepted))
        # Adversarial surface, provenance == accepted -> still caught.
        adversary = _as_render(
            _FAITHFUL + " A dragon then ate the farmer.", accepted, "x"
        )
        self.assertFalse(is_faithful(adversary, accepted))

    def test_moved_fact_control_catches_the_renderer_adversaries(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))

        moved = MovedColorRenderer("silver").render(accepted, 3)
        reasons = faithfulness(moved, accepted)
        self.assertFalse(is_faithful(moved, accepted))
        self.assertTrue(any("silver" in r for r in reasons))
        self.assertNotIn("copper", moved.text.lower())

        deus = DeusRenderer().render(accepted, 3)
        deus_reasons = faithfulness(deus, accepted)
        self.assertFalse(is_faithful(deus, accepted))
        self.assertTrue(any("magic key" in r or "planted" in r for r in deus_reasons))

    def test_review_four_adversaries_are_all_caught(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        # Sanity: the faithful skeleton the adversaries are built from passes.
        self.assertTrue(is_faithful(_as_render(_FAITHFUL, accepted, "x"), accepted))

        for name, adversary in _adversaries(accepted).items():
            with self.subTest(adversary=name):
                reasons = faithfulness(adversary, accepted)
                self.assertTrue(reasons, f"{name} was NOT caught")
                self.assertFalse(is_faithful(adversary, accepted))

        # Each one fails closure for the RIGHT reason.
        adv = _adversaries(accepted)
        self.assertTrue(
            any("thief" in r for r in faithfulness(adv["added-premise"], accepted))
        )
        self.assertTrue(
            any("duck" in r for r in faithfulness(adv["wrong-owner"], accepted))
        )
        self.assertTrue(
            any("lie" in r or "did not" in r for r in faithfulness(adv["negation"], accepted))
        )
        # Dropped beat: caught by uncovered coverage, not an unapproved segment.
        self.assertTrue(
            any("obstacle" in r for r in faithfulness(adv["dropped-beat"], accepted))
        )


class OrderingGateTests(unittest.TestCase):
    """The gate folds ORDER in: a scramble moves a fact even with no new atom.

    Each adversary below tiles fully into approved segments and covers every
    accepted fact kind (closure + coverage PASS); only ordering catches them.
    """

    def test_discharge_before_plant_is_caught(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        # Resolution (feather used as a key) precedes the feather's planting.
        text = " ".join((_SETUP1, _COMPLICATION, _RESOLUTION, _FEATHER, _CODA))
        reasons = faithfulness(_as_render(text, accepted, "adversary-dbp"), accepted)
        self.assertFalse(is_faithful(_as_render(text, accepted, "x"), accepted))
        self.assertTrue(
            any("before it is planted" in r for r in reasons), reasons
        )

    def test_full_reverse_is_caught(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        text = " ".join((_CODA, _RESOLUTION, _COMPLICATION, _FEATHER, _SETUP1))
        reasons = faithfulness(_as_render(text, accepted, "adversary-rev"), accepted)
        self.assertFalse(is_faithful(_as_render(text, accepted, "x"), accepted))
        self.assertTrue(
            any("orders beats inconsistently" in r for r in reasons), reasons
        )

    def test_resolution_before_complication_is_caught(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        text = " ".join((_SETUP1, _FEATHER, _RESOLUTION, _COMPLICATION, _CODA))
        reasons = faithfulness(_as_render(text, accepted, "adversary-rbc"), accepted)
        self.assertFalse(is_faithful(_as_render(text, accepted, "x"), accepted))
        self.assertTrue(
            any("orders beats inconsistently" in r for r in reasons), reasons
        )

    def test_faithful_order_passes(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        self.assertTrue(is_faithful(_as_render(_FAITHFUL, accepted, "x"), accepted))


class BeatDetectionTests(unittest.TestCase):
    """The complication beat needs the obstruction relation, not scenery."""

    def test_scenery_obstacle_word_is_not_a_covered_complication(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        scenery = (
            "The golden chicken wanted to sing the sunrise awake. "
            "A fallen feather rested by the coop. "
            "It used a fallen feather as a key, and sang until the sun rose. "
            "Now the golden chicken laid copper eggs."
        )
        beats = _beats_present(scenery, accepted)
        self.assertFalse(beats["complication"])  # 'coop' present, no obstruction

    def test_real_complication_is_covered(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        beats = _beats_present(_FAITHFUL, accepted)
        self.assertTrue(beats["complication"])


class TwoArmMetricTests(unittest.TestCase):
    """P-PR3: both arms preserve everything; pointer wins on lexical variety."""

    def test_two_arm_metric_comparison(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        pointer = SurfacePointerRenderer()
        template = ExactTemplateRenderer()

        pm = measure(tuple(pointer.render(accepted, s) for s in SEEDS), accepted)
        tm = measure(tuple(template.render(accepted, s) for s in SEEDS), accepted)

        for m in (pm, tm):
            self.assertEqual(m.premise_preservation, 1.0)
            self.assertEqual(m.required_beat_coverage, 1.0)
            self.assertEqual(m.temporal_consistency, 1.0)
            self.assertIsNone(m.human_preference)  # deferred, not faked

        self.assertGreater(pm.distinct_surface_ratio, tm.distinct_surface_ratio)
        self.assertGreater(pm.mean_pairwise_jaccard, tm.mean_pairwise_jaccard)
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

            del alice, ring
            reloaded = SessionKeyRing.open(keyfile)
            alice2, report = ConversationSession.restore(session_file, reloaded)
            self.assertEqual(len(report.refused), 0)

            accepted_post = _accepted(alice2)
            self.assertEqual(accepted_post, accepted_pre)
            self.assertEqual(
                pointer.render(accepted_post, 5).text, rendered_pre.text
            )
            self.assertNotEqual(
                pointer.render(accepted_post, 9).text, rendered_pre.text
            )
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
        self.assertIsNone(session.verifier.binding_value(session.state, "egg_color"))

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
        self.assertFalse(
            any(
                f.kind == "chicken_name"
                for f in accepted_facts(session.story_state, "copper")
            )
        )


class NoneInventedTests(unittest.TestCase):
    """P-PR6: no render across either arm invents a fact (closure clean)."""

    def test_no_render_invents_a_fact(self) -> None:
        accepted = _accepted(_bound_session(color="copper"))
        for renderer in (SurfacePointerRenderer(), ExactTemplateRenderer()):
            for s in SEEDS:
                r = renderer.render(accepted, s)
                self.assertEqual(r.provenance, accepted)
                self.assertEqual(faithfulness(r, accepted), ())


if __name__ == "__main__":
    unittest.main()
