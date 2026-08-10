"""Offline regressions for the v0.7 proof-search curve (ROADMAP item 1).

Nothing here starts Lean.  These tests protect the parts that must be true
BEFORE a live number means anything:

* the held-out claim is checked against the training extraction, not asserted;
* the frequency baseline is the SAME construction that won in v0.6;
* every ranking arm receives the same candidate multiset, so a proposal-count
  difference is a schema-ordering difference and nothing else;
* the story arm rides the shared controller with a disjoint vocabulary.

The live adjudication lives in ``experiments/results/proof_curve.json`` and
``experiments/results/story_curve.json``; these tests are what make those
files interpretable.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
for _extra in (ROOT / "prover", ROOT / "scripts", ROOT / "experiments"):
    if str(_extra) not in sys.path:
        sys.path.insert(0, str(_extra))

import tactic_grammar as tg  # noqa: E402
import theorem_set  # noqa: E402
from controller import ActionKind  # noqa: E402
from curve_search import (  # noqa: E402
    ArbitraryRanker,
    FrequencyRanker,
    RankedSchemaPolicy,
    SyntaxRanker,
    V06_HELD_OUT,
    training_schema_counts,
)
from live_search import LiveLeanState  # noqa: E402


AFTER_INTRO = "P : Prop\nQ : Prop\nh : P ∧ Q\n⊢ Q ∧ P"
FRESH_GOAL = "\n⊢ forall (P Q : Prop) (h : P /\\ Q), Q /\\ P"
OPAQUE = "P : Prop\nQ : Prop\nh : ProofCurve.Both P Q\n⊢ ProofCurve.Both Q P"


class TheoremSetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.theorems = theorem_set.load()

    def test_set_is_versioned_and_digested(self) -> None:
        self.assertEqual(self.theorems.version, 1)
        self.assertEqual(self.theorems.label, "prover.curve@v1")
        self.assertEqual(len(self.theorems.sha256), 64)
        self.assertEqual(
            self.theorems.sha256, theorem_set.digest(self.theorems.path)
        )

    def test_digest_is_checkout_newline_invariant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lf = root / "lf.json"
            crlf = root / "crlf.json"
            lf.write_bytes(b'{\n  "x": 1\n}\n')
            crlf.write_bytes(b'{\r\n  "x": 1\r\n}\r\n')
            self.assertEqual(theorem_set.digest(lf), theorem_set.digest(crlf))

    def test_two_proof_families_at_minimum_each_with_members(self) -> None:
        sizes = {
            family: len(self.theorems.by_family(family))
            for family in self.theorems.families
        }
        self.assertGreaterEqual(len(sizes), 2)
        for family, size in sizes.items():
            self.assertGreaterEqual(size, 3, f"family {family} is too thin")

    def test_held_out_is_checked_against_the_training_extraction(self) -> None:
        """'Held out' must be a fact about sample_triples.json, not a label."""
        trained_ids = theorem_set.training_theorem_ids()
        trained_states = theorem_set.training_states()
        for theorem in self.theorems.theorems:
            self.assertTrue(theorem.held_out, theorem.id)
            self.assertNotIn(theorem.id, trained_ids)
            self.assertNotIn(theorem.proposition, trained_states)
            # The rendered fresh goal is the proposition verbatim; make sure
            # that exact string never appeared as an extracted state either.
            self.assertNotIn(f"⊢ {theorem.proposition}", trained_states)

    def test_every_witness_uses_only_registered_schemas(self) -> None:
        for theorem in self.theorems.theorems:
            for tactic in theorem.witness:
                self.assertIn(tg.action_schema(tactic), tg.SCHEMAS)

    def test_project_family_declares_a_project_and_init_family_does_not(self) -> None:
        for theorem in self.theorems.theorems:
            backend = self.theorems.backend_of(theorem)
            if theorem.family == "project_import":
                self.assertTrue(backend.needs_project, theorem.id)
                self.assertIn("ProofCurve", theorem.proposition)
            else:
                self.assertFalse(backend.needs_project, theorem.id)


    def test_state_level_leakage_control_stays_at_zero(self) -> None:
        """Theorem-identity holdout is not state-level holdout; measure both.

        The live control writes ``proof_curve_leakage.json``.  This regression
        exists so that a future theorem set cannot quietly introduce a proof
        state the v0.6 checkpoint was trained on -- which is the one way a
        "held out" label could still be false after every other check passes.
        """
        report = ROOT / "experiments" / "results" / "proof_curve_leakage.json"
        self.assertTrue(
            report.is_file(),
            "committed leakage evidence is missing; rerun experiments/tactic_curve.py",
        )
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["theorem_set"], self.theorems.provenance())
        self.assertEqual(
            payload["selected_theorem_ids"],
            [item.id for item in self.theorems.theorems],
        )
        self.assertEqual(
            payload["training_extraction"]["sha256"],
            theorem_set.digest(theorem_set.TRAINING_EXTRACTION),
        )
        trained_states = theorem_set.training_states()
        self.assertEqual(
            payload["training_extraction"]["distinct_states"],
            len(trained_states),
        )
        expected_arms = {
            "arbitrary", "frequency", "syntax",
            "learned_s0", "learned_s1", "learned_s2",
        }
        self.assertEqual(set(payload["arms"]), expected_arms)
        primary = json.loads(
            (ROOT / "experiments" / "results" / "proof_curve.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(payload["checkpoints"], primary["checkpoints"])
        for arm, arm_payload in payload["arms"].items():
            self.assertEqual(arm_payload["arm"], arm)
            self.assertGreater(arm_payload["distinct_states_across_set"], 0)
            self.assertEqual(
                arm_payload["training_states_compared"], len(trained_states)
            )
            self.assertEqual(arm_payload["states_in_training_extraction"], 0)
            self.assertEqual(
                {row["theorem"] for row in arm_payload["per_theorem"]},
                {item.id for item in self.theorems.theorems},
            )
            for row in arm_payload["per_theorem"]:
                self.assertEqual(
                    row["states_in_training_extraction"], 0,
                    f"{arm}: {row['theorem']}",
                )

    def test_primary_artifact_binds_theorem_and_project_sources(self) -> None:
        report = ROOT / "experiments" / "results" / "proof_curve.json"
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["theorem_set"], self.theorems.provenance())
        backend = self.theorems.backends["proofcurve"]
        recorded = payload["backend_projects"]["proofcurve"]
        assert backend.project is not None
        for field, filename in (
            ("source_sha256", "ProofCurve.lean"),
            ("toolchain_sha256", "lean-toolchain"),
            ("lakefile_sha256", "lakefile.toml"),
        ):
            self.assertEqual(
                recorded[field], theorem_set.digest(backend.project / filename)
            )
        self.assertEqual(len(recorded["olean_sha256"]), 64)

    def test_published_time_curves_recompute_from_serialized_runs(self) -> None:
        for filename, group_field in (
            ("proof_curve.json", "family"),
            ("story_curve.json", "split"),
        ):
            payload = json.loads(
                (ROOT / "experiments" / "results" / filename).read_text(
                    encoding="utf-8"
                )
            )
            for group, arms in payload["curve"].items():
                for arm, curve_payload in arms.items():
                    runs = [
                        run for run in payload["runs"]
                        if run["arm"] == arm
                        and (group == "ALL" or run[group_field] == group)
                    ]
                    recomputed = [
                        sum(
                            run["solved"] and run["seconds"] <= rung["seconds"]
                            for run in runs
                        )
                        for rung in curve_payload["time_curve"]
                    ]
                    self.assertEqual(
                        recomputed,
                        [rung["solved"] for rung in curve_payload["time_curve"]],
                        f"{filename}: {group}/{arm}",
                    )


class FrequencyBaselineTests(unittest.TestCase):
    def test_extraction_schema_matches_the_v06_mapper_row_for_row(self) -> None:
        """The frequency arm is only v0.6's winner if the mapping is v0.6's."""
        from train_tactic_policy import tactic_schema  # noqa: PLC0415

        rows = json.loads(
            (ROOT / "prover" / "sample_triples.json").read_text(encoding="utf-8")
        )
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(
                tg.extraction_schema(row["tactic"]),
                tactic_schema(row["tactic"]),
                row["tactic"],
            )

    def test_frequency_counts_come_from_the_v06_training_split(self) -> None:
        rows = json.loads(
            (ROOT / "prover" / "sample_triples.json").read_text(encoding="utf-8")
        )
        counts = training_schema_counts(rows)
        self.assertEqual(set(counts), set(tg.SCHEMAS))
        self.assertEqual(sum(counts.values()), 44)
        held_out_rows = [r for r in rows if r["theorem"] in V06_HELD_OUT]
        self.assertTrue(held_out_rows)

    def test_frequency_order_is_state_blind(self) -> None:
        rows = json.loads(
            (ROOT / "prover" / "sample_triples.json").read_text(encoding="utf-8")
        )
        ranker = FrequencyRanker(tuple(sorted(training_schema_counts(rows).items())))
        self.assertEqual(ranker.order(AFTER_INTRO), ranker.order(FRESH_GOAL))


class GrammarTests(unittest.TestCase):
    def test_parses_both_the_source_and_the_pretty_printed_spelling(self) -> None:
        fresh = tg.parse_state(FRESH_GOAL)
        self.assertIsNotNone(fresh)
        self.assertEqual(fresh.hypotheses, ())
        self.assertTrue(fresh.conclusion.startswith("∀"))
        later = tg.parse_state(AFTER_INTRO)
        self.assertEqual([h.name for h in later.hypotheses], ["P", "Q", "h"])
        self.assertEqual(later.conclusion, "Q ∧ P")

    def test_reads_only_the_first_goal_of_a_multi_goal_state(self) -> None:
        rendered = (
            "case left\nP : Prop\nQ : Prop\nh : P ∧ Q\n⊢ Q\n"
            "case right\nP : Prop\nQ : Prop\nh : P ∧ Q\n⊢ P"
        )
        goal = tg.parse_state(rendered)
        self.assertEqual(goal.case_label, "left")
        self.assertEqual(goal.conclusion, "Q")

    def test_inaccessible_binders_never_reach_argument_generation(self) -> None:
        """v0.6's first live run died here; the filter is a regression."""
        rendered = "P✝ : Prop\na✝ : P✝\n⊢ P✝"
        goal = tg.parse_state(rendered)
        self.assertEqual(goal.accessible, ())
        generated = tg.candidates(goal)
        self.assertEqual(generated["projection"], ())
        self.assertEqual(generated["clear"], ())

    def test_binder_names_cover_universals_then_fresh_arrow_names(self) -> None:
        goal = tg.parse_state("\n⊢ forall (P Q : Prop), P -> Q -> (P /\\ Q)")
        self.assertEqual(
            tg.leading_binder_names(goal), ("P", "Q", "h1", "h2")
        )

    def test_fresh_names_avoid_existing_context_names(self) -> None:
        goal = tg.parse_state("h1 : Prop\n⊢ h1 → h1")
        self.assertEqual(tg.leading_binder_names(goal), ("h2",))

    def test_projection_paths_follow_the_conjunction_tree(self) -> None:
        self.assertEqual(
            [path for path, _ in tg.projection_paths("P ∧ Q ∧ R")],
            [".left", ".right", ".right.left", ".right.right"],
        )
        self.assertEqual(
            [path for path, _ in tg.projection_paths("(P ∧ Q) ∧ R")],
            [".left", ".left.left", ".left.right", ".right"],
        )

    def test_opaque_project_types_still_offer_the_two_fields(self) -> None:
        """Lean does not unfold ``ProofCurve.Both``; Lean, not syntax, judges."""
        goal = tg.parse_state(OPAQUE)
        generated = tg.candidates(goal)
        self.assertEqual(
            generated["projection"], ("exact h.left", "exact h.right")
        )
        self.assertEqual(tg.goal_shape(goal), "atom")

    def test_bare_variables_offer_no_projection(self) -> None:
        goal = tg.parse_state("P : Prop\nhp : P\n⊢ P")
        self.assertEqual(tg.candidates(goal)["projection"], ())

    def test_clear_never_targets_a_sort_binder(self) -> None:
        goal = tg.parse_state(AFTER_INTRO)
        self.assertEqual(tg.candidates(goal)["clear"], ("clear h",))

    def test_syntax_order_reads_the_conclusion(self) -> None:
        self.assertEqual(tg.syntax_order(tg.parse_state(FRESH_GOAL))[0], "intro")
        self.assertEqual(tg.syntax_order(tg.parse_state(AFTER_INTRO))[0],
                         "constructor")
        atomic = tg.parse_state("P : Prop\nQ : Prop\nh : P ∧ Q\n⊢ P")
        self.assertEqual(tg.syntax_order(atomic)[0], "projection")
        assumption = tg.parse_state("P : Prop\nhp : P\n⊢ P")
        self.assertEqual(tg.syntax_order(assumption)[0], "assumption")
        disjunct = tg.parse_state("P : Prop\nQ : Prop\nhp : P\n⊢ P ∨ Q")
        self.assertEqual(tg.syntax_order(disjunct)[:2], ("left", "right"))

    def test_syntax_order_never_prefers_the_dead_branch(self) -> None:
        for rendered in (FRESH_GOAL, AFTER_INTRO, OPAQUE):
            self.assertEqual(tg.syntax_order(tg.parse_state(rendered))[-1],
                             "clear")

    def test_syntax_order_falls_back_to_arbitrary_where_syntax_is_silent(self) -> None:
        """On an opaque conclusion the blind arm has nothing to read."""
        order = tg.syntax_order(tg.parse_state(OPAQUE))
        self.assertEqual(
            order[:-1],
            tuple(s for s in tg.ARBITRARY_ORDER if s != "clear"),
        )

    def test_a_binder_named_case_is_not_swallowed_as_a_block_header(self) -> None:
        """Self-review: the header test used to run before the ``" : "`` test."""
        goal = tg.parse_state("case : Prop\nh : case\n⊢ case")
        self.assertEqual([h.name for h in goal.hypotheses], ["case", "h"])
        self.assertIsNone(goal.case_label)

    def test_unbalanced_parentheses_fail_soft_not_wrong(self) -> None:
        """A negative depth would silently disable every later split."""
        self.assertEqual(tg._split_top("a) ∧ b", "∧"), ["a)", "b"])

    def test_every_schema_is_reachable_from_action_schema(self) -> None:
        for tactic, schema in (
            ("clear h", "clear"), ("intro", "intro"), ("intro P Q", "intro"),
            ("constructor", "constructor"), ("assumption", "assumption"),
            ("exact h.left", "projection"), ("left", "left"),
            ("right", "right"), ("trivial", "trivial"),
        ):
            self.assertEqual(tg.action_schema(tactic), schema)
        with self.assertRaises(ValueError):
            tg.action_schema("simp")


class PolicyTests(unittest.TestCase):
    """The comparison is fair only if the arms share one candidate set."""

    def _actions(self, ranker, rendered: str):
        policy = RankedSchemaPolicy(ranker)
        state = LiveLeanState("t", rendered, "handle")
        return tuple(policy.propose_all(state, ()))

    def test_arms_differ_only_by_permutation(self) -> None:
        rows = json.loads(
            (ROOT / "prover" / "sample_triples.json").read_text(encoding="utf-8")
        )
        frequency = FrequencyRanker(
            tuple(sorted(training_schema_counts(rows).items()))
        )
        for rendered in (FRESH_GOAL, AFTER_INTRO, OPAQUE):
            sets = [
                sorted(
                    action.argument("tactic")
                    for action in self._actions(ranker, rendered)
                )
                for ranker in (ArbitraryRanker(), frequency, SyntaxRanker())
            ]
            self.assertEqual(sets[0], sets[1])
            self.assertEqual(sets[1], sets[2])
            self.assertTrue(sets[0])

    def test_ordering_actually_changes(self) -> None:
        arbitrary = self._actions(ArbitraryRanker(), AFTER_INTRO)
        syntax = self._actions(SyntaxRanker(), AFTER_INTRO)
        self.assertNotEqual(
            [a.argument("tactic") for a in arbitrary],
            [a.argument("tactic") for a in syntax],
        )

    def test_policy_only_ever_emits_gen_lean_tactic(self) -> None:
        for action in self._actions(SyntaxRanker(), AFTER_INTRO):
            self.assertIs(action.kind, ActionKind.GEN)
            self.assertEqual(action.name, "lean_tactic")
            self.assertEqual(len(action.arguments), 1)
            self.assertEqual(action.dependencies, ())

    def test_within_schema_order_is_fixed_across_arms(self) -> None:
        """Argument generation is shared; only the schema keys are permuted."""
        for ranker in (ArbitraryRanker(), SyntaxRanker()):
            tactics = [
                a.argument("tactic") for a in self._actions(ranker, AFTER_INTRO)
            ]
            projections = [t for t in tactics if t.startswith("exact ")]
            self.assertEqual(projections, ["exact h.left", "exact h.right"])


class StoryArmTests(unittest.TestCase):
    def setUp(self) -> None:
        import story_curve  # noqa: PLC0415

        self.story = story_curve

    def test_story_run_json_preserves_threshold_adjacent_time(self) -> None:
        """The old 4-decimal rounding turned 0.99996 into 1.0000."""
        run = self.story.StoryRun(
            brief="b", split="heldout", arm="a", solved=True,
            stop="solved", nodes=1, states=1, proposals=1, accepted=1,
            rejected=0, seconds=0.99996, solution=(), dead_branches=(),
            proposal_signatures=(),
        )
        serialized = run.as_json()["seconds"]
        self.assertEqual(serialized, run.seconds)
        self.assertLess(serialized, 1.0)

    def test_story_vocabulary_is_disjoint_from_the_tactic_vocabulary(self) -> None:
        self.assertFalse(set(self.story.STORY_SCHEMAS) & set(tg.SCHEMAS))

    def test_shared_controller_not_a_second_one(self) -> None:
        import controller  # noqa: PLC0415

        self.assertIs(self.story.SearchController, controller.SearchController)

    def test_briefs_split_by_story_identity(self) -> None:
        train = {b.id for b in self.story.BRIEFS if b.split == "train"}
        heldout = {b.id for b in self.story.BRIEFS if b.split == "heldout"}
        self.assertTrue(train and heldout)
        self.assertFalse(train & heldout)
        self.assertEqual(len(train) + len(heldout), len(self.story.BRIEFS))

    def test_every_generated_binding_is_accepted_by_the_frame(self) -> None:
        """Offsets are computed, so no brief may ship an unbindable span."""
        for brief in self.story.BRIEFS:
            verifier = brief.verifier()
            state = verifier.initial_state()
            for action in self.story.story_candidates(brief, state)["plant"]:
                verifier.bind_mentions(
                    action.argument("mention"), action.argument("binds")
                )

    def test_decoy_element_is_plantable_so_dead_branches_exist(self) -> None:
        for brief in self.story.BRIEFS:
            state = brief.verifier().initial_state()
            planted = {
                action.argument("element")
                for action in self.story.story_candidates(brief, state)["plant"]
            }
            self.assertIn(brief.element, planted)
            self.assertIn(brief.decoy_element, planted, brief.id)

    def test_syntax_story_ranker_follows_beat_structure(self) -> None:
        ranker = self.story.SyntaxStoryRanker()
        self.assertEqual(ranker.order("agent: a\ndesire: None\nbeats: 0")[0],
                         "introduce")
        self.assertEqual(
            ranker.order("setup: x\nbeats: 1")[0], "plant"
        )
        self.assertEqual(
            ranker.order(
                "setup: x\nbeats: 1\nobligation e: outstanding"
            )[0],
            "obstruct",
        )
        self.assertEqual(
            ranker.order("setup: x\ncomplication: y\nbeats: 2")[0], "resolve"
        )
        self.assertEqual(
            ranker.order(
                "setup: x\ncomplication: y\nresolution: z\nbeats: 3\n"
                "obligation e: outstanding"
            )[0],
            "discharge",
        )

    def test_frequency_story_order_is_degenerate(self) -> None:
        """P-SC3: five schemas, one firing each -- the count cannot rank."""
        rows: list[tuple[str, str]] = []
        for brief in self.story.BRIEFS:
            if brief.split == "train":
                rows.extend(self.story.oracle_walk(brief))
        counts = {}
        for _, schema in rows:
            counts[schema] = counts.get(schema, 0) + 1
        self.assertEqual(len(set(counts.values())), 1, counts)
        ranker = self.story.FrequencyStoryRanker(tuple(sorted(counts.items())))
        self.assertEqual(ranker.order(""), self.story.ARBITRARY_STORY_ORDER)

    def test_one_held_out_brief_solves_through_the_shared_controller(self) -> None:
        brief = next(b for b in self.story.BRIEFS if b.split == "heldout")
        run = self.story.run_brief(brief, self.story.SyntaxStoryRanker(), 64, 512)
        self.assertTrue(run.solved)
        self.assertEqual(
            run.solution,
            ("introduce", "plant", "obstruct", "resolve", "discharge"),
        )
        self.assertTrue(run.dead_branches, "no pruning evidence was preserved")


class BudgetDerivationTests(unittest.TestCase):
    def test_run_json_preserves_threshold_adjacent_time(self) -> None:
        """The old 3-decimal rounding turned 0.0199996 into 0.020."""
        from curve_search import RunRecord  # noqa: PLC0415

        record = RunRecord(
            theorem="t", family="f", arm="a", solved=True,
            stop_reason="solved", nodes=1, states=1, proposals=1,
            accepted=1, rejected=0, seconds=0.0199996, solution=(),
            dead_branches=(), accepted_signatures=(), proposal_signatures=(),
        )
        serialized = record.as_json()["seconds"]
        self.assertEqual(serialized, record.seconds)
        self.assertLess(serialized, 0.02)

    def test_solved_at_thresholds_both_axes(self) -> None:
        from curve_search import RunRecord, solved_at, solved_by_time  # noqa: PLC0415

        record = RunRecord(
            theorem="t", family="f", arm="a", solved=True, stop_reason="solved",
            nodes=8, states=11, proposals=64, accepted=10, rejected=54,
            seconds=0.1, solution=(), dead_branches=(),
            accepted_signatures=(), proposal_signatures=(),
        )
        self.assertTrue(solved_at(record, 8, 64))
        self.assertFalse(solved_at(record, 7, 64))
        self.assertFalse(solved_at(record, 8, 63))
        self.assertTrue(solved_by_time(record, 0.1))
        self.assertFalse(solved_by_time(record, 0.05))
        unsolved = RunRecord(
            theorem="t", family="f", arm="a", solved=False, stop_reason="budget",
            nodes=1, states=1, proposals=1, accepted=0, rejected=1,
            seconds=0.0, solution=(), dead_branches=(),
            accepted_signatures=(), proposal_signatures=(),
        )
        self.assertFalse(solved_at(unsolved, 64, 512))


if __name__ == "__main__":
    unittest.main()
