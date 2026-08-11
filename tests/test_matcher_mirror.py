"""Regression tests for the v0.5 past/mirror payoff."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from match_signatures import (  # noqa: E402
    COMMUTATIVE_CALL_HEADS,
    HEAD_ALGEBRA,
    HEAD_ALIASES,
    Parser,
    build_report,
    canonicalize,
    load_nodes,
    mirror_skeleton,
    time_reverse_heads,
    tokenize,
)
from validate_nodes import scope_errors  # noqa: E402


EXPECTED_MIRRORS = {
    frozenset(
        {
            "temporal.recurrence.until_unfolding",
            "temporal.past.since_unfolding",
        }
    ),
    frozenset(
        {
            "temporal.modality.temporal_duality",
            "temporal.past.past_duality",
        }
    ),
    frozenset(
        {
            "temporal.modality.next_distributes_over_meet",
            "temporal.past.prev_distributes_over_meet",
        }
    ),
    frozenset(
        {
            "temporal.modality.eventually_unfolding",
            "temporal.past.once_unfolding",
        }
    ),
    frozenset(
        {
            "temporal.response.response_pattern",
            "temporal.response.heraldry_pattern",
        }
    ),
}


class MirrorReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        nodes, problems = load_nodes(REPO_ROOT / "data")
        cls.report = build_report(nodes, problems)

    def test_registered_group_counts_include_physics_frames_slice(self) -> None:
        self.assertEqual(self.report["nodes_analyzed"], 229)
        self.assertEqual(
            self.report["group_counts"],
            {
                "shape": 30,
                "typed": 31,
                "family": 30,
                "aliased": 32,
                "mirror": 5,
            },
        )
        self.assertEqual(self.report["ladder_violations"], [])

    def test_sally_belief_and_world_location_share_content_not_scope(self) -> None:
        expected = {
            "narrative.belief.sally_marble_basket",
            "narrative.world.marble_moved_box",
        }
        groups = [
            {member["statement_id"] for member in group["members"]}
            for group in self.report["typed_twin_groups"]
        ]
        self.assertIn(expected, groups)

    def test_galilean_addition_fires_and_scope_only_prediction_misses(self) -> None:
        typed_groups = {
            frozenset(member["statement_id"] for member in group["members"])
            for group in self.report["typed_twin_groups"]
        }
        self.assertIn(
            frozenset(
                {
                    "algtop.homology.chain_rank_nullity",
                    "physics.frames.galilean_velocity_addition",
                }
            ),
            typed_groups,
        )
        rotating = "physics.frames.rotating_frame"
        cartoon = "narrative.frames.cartoon_gravity"
        for level in (
            "shape_twin_groups",
            "typed_twin_groups",
            "family_twin_groups_beyond_typed",
            "aliased_twin_groups_beyond_typed",
            "mirror_twin_groups",
        ):
            self.assertFalse(
                any(
                    {rotating, cartoon}.issubset(
                        {member["statement_id"] for member in group["members"]}
                    )
                    for group in self.report[level]
                ),
                level,
            )

    def test_only_the_five_registered_mirror_groups_are_reported(self) -> None:
        actual = {
            frozenset(member["statement_id"] for member in group["members"])
            for group in self.report["mirror_twin_groups"]
        }
        self.assertEqual(actual, EXPECTED_MIRRORS)

        typed_pairs = {
            frozenset((left, right))
            for group in self.report["typed_twin_groups"]
            for index, left in enumerate(
                member["statement_id"] for member in group["members"]
            )
            for right in [
                member["statement_id"] for member in group["members"]
            ][index + 1 :]
        }
        self.assertTrue(EXPECTED_MIRRORS.isdisjoint(typed_pairs))

    def test_strict_order_is_related_to_but_not_aliased_with_leq(self) -> None:
        self.assertEqual(HEAD_ALIASES["BEFORE"], HEAD_ALIASES["LT"])
        self.assertNotIn("LEQ", HEAD_ALIASES)
        self.assertEqual(HEAD_ALGEBRA["LEQ"]["order"]["strict_part"], "LT")
        self.assertEqual(
            HEAD_ALGEBRA["LT"]["order"]["reflexive_closure"], "LEQ"
        )

    def test_time_reversal_is_global_and_involutive(self) -> None:
        def tree(expression: str) -> tuple:
            return canonicalize(Parser(tokenize(expression)).parse())

        future = tree("ALWAYS(EVENTUALLY(PROP))")
        full_past = tree("HISTORICALLY(ONCE(PROP))")
        partial = tree("HISTORICALLY(EVENTUALLY(PROP))")
        classes = {"PROP": "variable"}

        self.assertEqual(
            canonicalize(
                time_reverse_heads(time_reverse_heads(future)),
                COMMUTATIVE_CALL_HEADS,
            ),
            future,
        )
        self.assertEqual(
            mirror_skeleton(future, classes),
            mirror_skeleton(full_past, classes),
        )
        self.assertNotEqual(
            mirror_skeleton(future, classes),
            mirror_skeleton(partial, classes),
        )


class AuthoredScopeTests(unittest.TestCase):
    def test_first_scope_pair_agrees_and_resolves_in_the_merged_graph(self) -> None:
        all_nodes = []
        for path in sorted((REPO_ROOT / "data").glob("*/nodes.json")):
            corpus = json.loads(path.read_text(encoding="utf-8"))
            all_nodes.extend(corpus["statement_nodes"])
        self.assertEqual(scope_errors(all_nodes), [])

        pair = {
            node["statement_id"]: node["scope"]
            for node in all_nodes
            if node["statement_id"].startswith(
                "narrative.frames.cartoon_gravity"
            )
        }
        self.assertEqual(
            set(pair),
            {
                "narrative.frames.cartoon_gravity",
                "narrative.frames.cartoon_gravity_hover",
            },
        )
        self.assertEqual(
            pair["narrative.frames.cartoon_gravity"]["role"], "declaration"
        )
        self.assertEqual(
            pair["narrative.frames.cartoon_gravity_hover"]["role"],
            "assertion",
        )
        for scope in pair.values():
            self.assertIn(
                "physics.gravitation.newton_universal_gravitation",
                scope["suspends"],
            )
            self.assertEqual(scope["retrieval"], "frame_local")

    def test_hover_is_frame_assumed_not_falsely_entailed(self) -> None:
        corpus = json.loads(
            (REPO_ROOT / "data" / "narrative" / "nodes.json").read_text(
                encoding="utf-8"
            )
        )
        nodes = {node["statement_id"]: node for node in corpus["statement_nodes"]}
        declaration = nodes["narrative.frames.cartoon_gravity"]
        hover = nodes["narrative.frames.cartoon_gravity_hover"]

        self.assertNotIn(
            "narrative.frames.cartoon_gravity_hover",
            declaration["inferential_links"].get("entails", []),
        )
        self.assertNotIn(
            "narrative.frames.cartoon_gravity",
            hover["inferential_links"].get("entailed_by", []),
        )
        self.assertEqual(hover["epistemic_status"], "assumed")
        self.assertTrue(
            hover["structural_signature"]["anonymized_template"].startswith(
                "IMPLIES(NEG"
            )
        )
        declaration_forms = {
            form["expression"]
            for form in declaration["formal_statement"]["equivalent_forms"]
        }
        self.assertNotIn(
            "unsupported bodies do not fall until they notice",
            declaration_forms,
        )

    def test_past_response_nodes_declare_past_box_metadata(self) -> None:
        nodes = {}
        for discipline in ("temporal_logic", "narrative"):
            corpus = json.loads(
                (REPO_ROOT / "data" / discipline / "nodes.json").read_text(
                    encoding="utf-8"
                )
            )
            nodes.update(
                (node["statement_id"], node)
                for node in corpus["statement_nodes"]
            )

        for statement_id in (
            "temporal.response.heraldry_pattern",
            "narrative.constraint.no_deus_ex_machina",
        ):
            operators = {
                operator["symbol"]
                for operator in nodes[statement_id]["symbol_lexicon"]["operators"]
            }
            self.assertIn("H", operators)
            self.assertNotIn("G", operators)

        heraldry = nodes["temporal.response.heraldry_pattern"]
        self.assertTrue(
            any(
                "at or before" in condition
                for condition in heraldry["semantic_interpretation"][
                    "regularity_conditions"
                ]
            )
        )

    def test_past_recurrence_and_opening_persistence_boundaries(self) -> None:
        nodes = {}
        for path in sorted((REPO_ROOT / "data").glob("*/nodes.json")):
            corpus = json.loads(path.read_text(encoding="utf-8"))
            nodes.update(
                (node["statement_id"], node)
                for node in corpus["statement_nodes"]
            )

        for statement_id in (
            "temporal.past.since_unfolding",
            "temporal.past.once_unfolding",
        ):
            conditions = nodes[statement_id]["semantic_interpretation"][
                "regularity_conditions"
            ]
            self.assertTrue(any("Strong PREV" in value for value in conditions))

        persistence = nodes["narrative.frame.premise_persistence"]
        self.assertEqual(
            persistence["structural_signature"]["anonymized_template"],
            "ALWAYS(MEET(HOLDS(PREMISE), SINCE(HOLDS(PREMISE), FRAMEOPENING)))",
        )
        self.assertTrue(
            any(
                "opening declaration" in condition
                for condition in persistence["semantic_interpretation"][
                    "regularity_conditions"
                ]
            )
        )


if __name__ == "__main__":
    unittest.main()
