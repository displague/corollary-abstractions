"""Contract and capability-blind controls for retrieval-as-action."""

from __future__ import annotations

import sys
import json
import shutil
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
    Verdict,
)
from frames import FrameAssertionVerifier, FrameExecutor, FrameSpec, Literal  # noqa: E402
from retrieval import (  # noqa: E402
    PointableMaterial,
    RetrievalItem,
    RetrievalState,
    RetrievalVerifier,
    UnifiedKnowledgeStore,
    point_action,
    retrieval_action,
)


DE_MORGAN = "logic.boolean_laws.de_morgan_laws"


class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.store = UnifiedKnowledgeStore.load(
            REPO_ROOT / "data", REPO_ROOT / "reports"
        )

    def setUp(self) -> None:
        self.executor = FrameExecutor()
        self.frame = self.executor.open_frame(
            FrameSpec(frame="retrieval.tests", retrieval="open")
        )
        self.state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            DE_MORGAN,
            Literal("request", "needs", DE_MORGAN),
        )

    def test_exact_query_unifies_all_five_committed_source_kinds(self) -> None:
        result = self.store.query(DE_MORGAN)
        self.assertEqual(result.mode, "exact")
        self.assertEqual(
            {item.source for item in result.items},
            {"corpus", "lexicon", "twin_ledger", "decomposition", "proof"},
        )
        statuses = {item.source: item.epistemic_status for item in result.items}
        self.assertEqual(statuses["proof"], "proven")
        self.assertEqual(statuses["corpus"], "derived")
        proof = next(item for item in result.items if item.source == "proof")
        self.assertIn("extracted transitions", proof.text)

    def test_truncated_id_uses_neighborhood_not_exact_lookup(self) -> None:
        result = self.store.query("logic.boolean_laws.de_morgan")
        self.assertEqual(result.mode, "neighborhood")
        self.assertIn(
            DE_MORGAN,
            {source_id for item in result.items for source_id in item.source_ids},
        )

    def test_truncated_word_does_not_reverse_match_one_letter_aliases(self) -> None:
        result = self.store.query("logic boolean absor")
        self.assertEqual(result.mode, "neighborhood")
        owners = {
            item.source_ids[0]
            for item in result.items
            if item.source in {"corpus", "lexicon", "proof"}
        }
        self.assertEqual(owners, {"logic.boolean_laws.absorption"})
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            "logic boolean absor",
            Literal("request", "needs", "logic boolean absor"),
        )
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(
            state, retrieval_action("logic boolean absor")
        )
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.VERIFIED)

    def test_short_nonexact_key_cannot_prefix_match_a_long_alias(self) -> None:
        key = "7"
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            key,
            Literal("request", "needs", key),
        )
        result = RetrievalVerifier(self.store, self.executor).evaluate(
            state, retrieval_action(key)
        )
        self.assertIs(result.verdict, Verdict.UNKNOWN)
        self.assertIsNone(result.next_state)
        self.assertIn("ABSTAIN", result.evidence)

    def test_unique_decomposition_only_key_can_bind_its_corpus_owner(self) -> None:
        key = "D⟨COMPOSE⟨?0:V, ?1:V⟩⟩"
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            key,
            Literal("request", "needs", key),
        )
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(state, retrieval_action(key))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        self.assertEqual(len(retrieved.next_state.context), 1)
        self.assertEqual(
            retrieved.next_state.context[0].item.source,
            "decomposition",
        )
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.VERIFIED)
        self.assertEqual(
            pointed.next_state.bindings[-1][1],
            "decomposition:calculus.differentiation.chain_rule",
        )

    def test_unique_structural_group_key_can_bind_the_group_record(self) -> None:
        key = "?0:V = ordered_compose⟨ordered_compose⟨?1:V, ?2:V⟩, ?3:V⟩"
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            key,
            Literal("request", "needs", key),
        )
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(state, retrieval_action(key))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        self.assertEqual(len(retrieved.next_state.context), 1)
        self.assertEqual(retrieved.next_state.context[0].item.source, "twin_ledger")
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.VERIFIED)
        self.assertTrue(pointed.next_state.bindings[-1][1].startswith("twin_ledger:"))

    def test_exact_skeleton_keys_preserve_distinct_operators(self) -> None:
        keys = (
            "?0 = *(?1, ?2, ?3)",
            "?0 = +(?1, *(?2, ?3))",
        )
        bound_ids = set()
        verifier = RetrievalVerifier(self.store, self.executor)
        for key in keys:
            with self.subTest(key=key):
                state = RetrievalState.from_unknown(
                    self.executor,
                    self.frame,
                    "answer",
                    key,
                    Literal("request", "needs", key),
                )
                retrieved = verifier.evaluate(state, retrieval_action(key))
                self.assertIs(retrieved.verdict, Verdict.VERIFIED)
                self.assertEqual(len(retrieved.next_state.context), 1)
                pointed = verifier.evaluate(
                    retrieved.next_state, point_action(0)
                )
                self.assertIs(pointed.verdict, Verdict.VERIFIED)
                bound_ids.add(pointed.next_state.bindings[-1][1])
        self.assertEqual(len(bound_ids), 2)

    def test_tokenless_symbol_can_exact_lookup_and_bind(self) -> None:
        key = "¬"
        item = RetrievalItem(
            item_id="corpus:logic.symbol.negation",
            source="corpus",
            title="Negation",
            text="logical negation",
            epistemic_status="formal",
            source_ids=("logic.symbol.negation",),
            aliases=(key,),
        )
        store = UnifiedKnowledgeStore((item,))
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            key,
            Literal("request", "needs", key),
        )
        verifier = RetrievalVerifier(store, self.executor)
        retrieved = verifier.evaluate(state, retrieval_action(key))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        self.assertEqual(retrieved.next_state.context[0].item, item)
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.VERIFIED)

    def test_retrieval_session_can_only_begin_from_unknown(self) -> None:
        known_frame = self.executor.open_frame(
            FrameSpec(
                frame="retrieval.known",
                declarations=(("known", Literal("x", "p", "v")),),
            )
        )
        with self.assertRaisesRegex(ValueError, "only from an UNKNOWN"):
            RetrievalState.from_unknown(
                self.executor,
                known_frame,
                "answer",
                DE_MORGAN,
                Literal("x", "p", "v"),
            )

    def test_retrieve_then_point_solves_and_binds_pointable_material(self) -> None:
        verifier = RetrievalVerifier(self.store, self.executor)
        run = Controller[RetrievalState](max_steps=2).run(
            self.state,
            SequencePolicy((retrieval_action(DE_MORGAN), point_action(0))),
            verifier,
            lambda state: state.pending is None,
        )
        self.assertTrue(run.solved)
        self.assertEqual(
            [entry.verification.verdict for entry in run.trace],
            [Verdict.VERIFIED, Verdict.VERIFIED],
        )
        self.assertTrue(run.final_state.context)
        self.assertEqual(
            [material.position for material in run.final_state.context],
            list(range(len(run.final_state.context))),
        )
        self.assertEqual(
            len({material.item.item_id for material in run.final_state.context}),
            len(run.final_state.context),
        )
        self.assertEqual(run.final_state.bindings[0][0], "answer")
        self.assertEqual(run.final_state.bindings[0][1], "corpus:" + DE_MORGAN)

    def test_point_before_retrieval_is_refused(self) -> None:
        result = RetrievalVerifier(self.store, self.executor).evaluate(
            self.state, point_action(0)
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIn("absent", result.reason)

    def test_retrieve_cannot_replace_pending_key_with_unrelated_key(self) -> None:
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(
            self.state,
            retrieval_action("logic.inference.modus_ponens"),
        )
        self.assertIs(retrieved.verdict, Verdict.REFUSED)
        self.assertIsNone(retrieved.next_state)
        self.assertIn("must equal", retrieved.reason)

    def test_ambiguous_single_symbol_cannot_bind_an_unrelated_lexicon(self) -> None:
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            "a",
            Literal("request", "needs", "a"),
        )
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(state, retrieval_action("a"))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        self.assertGreater(len(retrieved.next_state.context), 1)
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.REFUSED)
        self.assertIsNone(pointed.next_state)
        self.assertIn("key constraint", pointed.reason)

    def test_exact_title_wins_over_another_nodes_neighborhood_match(self) -> None:
        key = "Quadratic Formula"
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            key,
            Literal("request", "needs", key),
        )
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(state, retrieval_action(key))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.VERIFIED)

    def test_pending_key_blocks_cross_query_neighborhood_binding(self) -> None:
        key = "Quadratic Formula"
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            key,
            Literal("request", "needs", key),
        )
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(state, retrieval_action("quadratic form"))
        self.assertIs(retrieved.verdict, Verdict.REFUSED)
        self.assertIsNone(retrieved.next_state)
        self.assertIn("must equal", retrieved.reason)

    def test_frame_mutation_cannot_leave_a_stale_unknown_pointable(self) -> None:
        pending_literal = Literal("request", "needs", DE_MORGAN)
        world_id = "logic.boolean_laws.de_morgan_laws"
        executor = FrameExecutor({world_id: (pending_literal,)})
        frame = executor.open_frame(
            FrameSpec(frame="retrieval.mutable", suspends=(world_id,))
        )
        state = RetrievalState.from_unknown(
            executor, frame, "answer", DE_MORGAN, pending_literal
        )
        verifier = RetrievalVerifier(self.store, executor)
        retrieved = verifier.evaluate(state, retrieval_action(DE_MORGAN))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        deny_falls = Action.build(
            ActionKind.GEN,
            "assert_fact",
            {
                "claim_id": "hover",
                "subject": "request",
                "predicate": "needs",
                "value": DE_MORGAN,
                "polarity": "false",
            },
        )
        mutated = verifier.evaluate(retrieved.next_state, deny_falls)
        self.assertIs(mutated.verdict, Verdict.VERIFIED)
        self.assertIs(
            executor.check(mutated.next_state.frame, pending_literal).verdict,
            Verdict.REFUTED,
        )
        self.assertIsNone(mutated.next_state.pending)
        self.assertEqual(mutated.next_state.resolutions[-1].slot, "answer")
        self.assertIs(
            mutated.next_state.resolutions[-1].verdict, Verdict.REFUTED
        )

    def test_schema_valid_artifact_only_proof_link_loads(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data_dir = root / "data"
            reports_dir = root / "reports"
            corpus_dir = data_dir / "logic"
            corpus_dir.mkdir(parents=True)
            reports_dir.mkdir()
            artifact = root / "proof.json"
            artifact.write_text(
                json.dumps(
                    [
                        {
                            "theorem": "Example.t",
                            "tactic": "rfl",
                            "stateBefore": "⊢ True",
                            "stateAfter": "no goals",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            node = {
                "statement_id": "logic.example.artifact_only",
                "title": "Artifact-only proof link",
                "semantic_interpretation": {"statement_meaning": "Example"},
                "structural_signature": {
                    "anonymized_template": "?0:P = ?0:P",
                    "archetype_id": "identity",
                },
                "keywords": [],
                "epistemic_status": "verified",
                "symbol_lexicon": {"symbols": [], "operators": []},
                "verified_by": [
                    {"system": "lean4", "artifact": "proof.json"}
                ],
            }
            (corpus_dir / "nodes.json").write_text(
                json.dumps({"statement_nodes": [node]}), encoding="utf-8"
            )
            (reports_dir / "signature_matches.json").write_text(
                json.dumps(
                    {
                        "typed_twin_groups": [],
                        "family_twin_groups_beyond_typed": [],
                        "aliased_twin_groups_beyond_typed": [],
                        "mirror_twin_groups": [],
                        "shape_twin_groups": [],
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "decompositions.json").write_text(
                json.dumps({"decompositions": []}), encoding="utf-8"
            )

            store = UnifiedKnowledgeStore.load(data_dir, reports_dir)
            proof = next(item for item in store.items if item.source == "proof")
            # Post-review behavior: an untrusted extraction is conjectured,
            # never "verified", and carries the structured trust marker so
            # consumers need not parse item.text for it.
            self.assertEqual(proof.epistemic_status, "conjectured")
            self.assertFalse(proof.trusted)
            self.assertIn("1 extracted transitions", proof.text)
            self.assertIn("untrusted extraction", proof.text)

    def test_local_no_goals_row_cannot_authenticate_whole_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data_dir = root / "data"
            reports_dir = root / "reports"
            corpus_dir = data_dir / "logic"
            corpus_dir.mkdir(parents=True)
            reports_dir.mkdir()
            rows = [
                {
                    "theorem": "Example.t",
                    "tactic": "exact h",
                    "stateBefore": "case left\n⊢ P",
                    "stateAfter": "no goals",
                }
            ]
            (root / "proof.json").write_text(json.dumps(rows), encoding="utf-8")
            node = {
                "statement_id": "logic.example.local_close",
                "title": "Local close",
                "semantic_interpretation": {"statement_meaning": "Example"},
                "structural_signature": {
                    "anonymized_template": "?0:P = ?0:P",
                    "archetype_id": "identity",
                },
                "keywords": [],
                "epistemic_status": "verified",
                "symbol_lexicon": {"symbols": [], "operators": []},
                "verified_by": [
                    {
                        "system": "lean4",
                        "artifact": "proof.json",
                        "reference": "Example.t",
                    }
                ],
            }
            (corpus_dir / "nodes.json").write_text(
                json.dumps({"statement_nodes": [node]}), encoding="utf-8"
            )
            (reports_dir / "signature_matches.json").write_text(
                json.dumps(
                    {
                        "typed_twin_groups": [],
                        "family_twin_groups_beyond_typed": [],
                        "aliased_twin_groups_beyond_typed": [],
                        "mirror_twin_groups": [],
                        "shape_twin_groups": [],
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "decompositions.json").write_text(
                json.dumps({"decompositions": []}), encoding="utf-8"
            )
            store = UnifiedKnowledgeStore.load(data_dir, reports_dir)
            proof = next(item for item in store.items if item.source == "proof")
            self.assertEqual(proof.epistemic_status, "conjectured")
            self.assertFalse(proof.trusted)
            self.assertNotEqual(proof.epistemic_status, "proven")

    def test_artifact_only_link_requires_one_theorem_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data_dir = root / "data"
            reports_dir = root / "reports"
            corpus_dir = data_dir / "logic"
            corpus_dir.mkdir(parents=True)
            reports_dir.mkdir()
            rows = [
                {
                    "theorem": theorem,
                    "tactic": "rfl",
                    "stateBefore": "⊢ True",
                    "stateAfter": "no goals",
                }
                for theorem in ("Example.one", "Example.two")
            ]
            (root / "proof.json").write_text(json.dumps(rows), encoding="utf-8")
            node = {
                "statement_id": "logic.example.ambiguous_proof",
                "title": "Ambiguous proof",
                "semantic_interpretation": {"statement_meaning": "Example"},
                "structural_signature": {
                    "anonymized_template": "?0:P = ?0:P",
                    "archetype_id": "identity",
                },
                "keywords": [],
                "epistemic_status": "verified",
                "symbol_lexicon": {"symbols": [], "operators": []},
                "verified_by": [
                    {"system": "lean4", "artifact": "proof.json"}
                ],
            }
            (corpus_dir / "nodes.json").write_text(
                json.dumps({"statement_nodes": [node]}), encoding="utf-8"
            )
            (reports_dir / "signature_matches.json").write_text(
                json.dumps(
                    {
                        "typed_twin_groups": [],
                        "family_twin_groups_beyond_typed": [],
                        "aliased_twin_groups_beyond_typed": [],
                        "mirror_twin_groups": [],
                        "shape_twin_groups": [],
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "decompositions.json").write_text(
                json.dumps({"decompositions": []}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "ambiguous across theorems"):
                UnifiedKnowledgeStore.load(data_dir, reports_dir)

    def test_empty_json_artifact_cannot_create_proven_material(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data_dir = root / "data"
            reports_dir = root / "reports"
            corpus_dir = data_dir / "logic"
            corpus_dir.mkdir(parents=True)
            reports_dir.mkdir()
            (root / "proof.json").write_text("[]", encoding="utf-8")
            node = {
                "statement_id": "logic.example.empty_proof",
                "title": "Empty proof",
                "semantic_interpretation": {"statement_meaning": "Example"},
                "structural_signature": {
                    "anonymized_template": "?0:P = ?0:P",
                    "archetype_id": "identity",
                },
                "keywords": [],
                "epistemic_status": "verified",
                "symbol_lexicon": {"symbols": [], "operators": []},
                "verified_by": [
                    {"system": "lean4", "artifact": "proof.json"}
                ],
            }
            (corpus_dir / "nodes.json").write_text(
                json.dumps({"statement_nodes": [node]}), encoding="utf-8"
            )
            (reports_dir / "signature_matches.json").write_text(
                json.dumps(
                    {
                        "typed_twin_groups": [],
                        "family_twin_groups_beyond_typed": [],
                        "aliased_twin_groups_beyond_typed": [],
                        "mirror_twin_groups": [],
                        "shape_twin_groups": [],
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "decompositions.json").write_text(
                json.dumps({"decompositions": []}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "no complete theorem"):
                UnifiedKnowledgeStore.load(data_dir, reports_dir)

    def test_incomplete_or_unsupported_artifact_cannot_be_proven(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data_dir = root / "data"
            reports_dir = root / "reports"
            corpus_dir = data_dir / "logic"
            corpus_dir.mkdir(parents=True)
            reports_dir.mkdir()
            node = {
                "statement_id": "logic.example.bad_proof",
                "title": "Bad proof",
                "semantic_interpretation": {"statement_meaning": "Example"},
                "structural_signature": {
                    "anonymized_template": "?0:P = ?0:P",
                    "archetype_id": "identity",
                },
                "keywords": [],
                "epistemic_status": "verified",
                "symbol_lexicon": {"symbols": [], "operators": []},
                "verified_by": [
                    {"system": "lean4", "artifact": "proof.json"}
                ],
            }
            (corpus_dir / "nodes.json").write_text(
                json.dumps({"statement_nodes": [node]}), encoding="utf-8"
            )
            (reports_dir / "signature_matches.json").write_text(
                json.dumps(
                    {
                        "typed_twin_groups": [],
                        "family_twin_groups_beyond_typed": [],
                        "aliased_twin_groups_beyond_typed": [],
                        "mirror_twin_groups": [],
                        "shape_twin_groups": [],
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "decompositions.json").write_text(
                json.dumps({"decompositions": []}), encoding="utf-8"
            )
            (root / "proof.json").write_text(
                json.dumps(
                    [
                        {
                            "theorem": "Example.t",
                            "tactic": "intro",
                            "stateBefore": "⊢ P",
                            "stateAfter": "P : Prop\n⊢ P",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "does not close"):
                UnifiedKnowledgeStore.load(data_dir, reports_dir)

            node["verified_by"][0]["artifact"] = "proof.txt"
            (corpus_dir / "nodes.json").write_text(
                json.dumps({"statement_nodes": [node]}), encoding="utf-8"
            )
            (root / "proof.txt").write_text("theorem Example.t", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "cannot authenticate"):
                UnifiedKnowledgeStore.load(data_dir, reports_dir)

    def test_unknown_retrieval_and_point_transition_names_are_refused(self) -> None:
        verifier = RetrievalVerifier(self.store, self.executor)
        malformed = (
            Action.build(ActionKind.RETRIEVE, "delete", {"key": DE_MORGAN}),
            Action.build(ActionKind.POINT, "copy", {"position": "0"}),
        )
        for action in malformed:
            with self.subTest(action=action):
                result = verifier.evaluate(self.state, action)
                self.assertIs(result.verdict, Verdict.REFUSED)
                self.assertIsNone(result.next_state)
                self.assertIn("unknown", result.reason)

    def test_empty_store_is_capability_blind_failure_and_does_not_mutate(self) -> None:
        verifier = RetrievalVerifier(UnifiedKnowledgeStore(), self.executor)
        run = Controller[RetrievalState](max_steps=2).run(
            self.state,
            SequencePolicy((retrieval_action(DE_MORGAN), point_action(0))),
            verifier,
            lambda state: state.pending is None,
        )
        self.assertFalse(run.solved)
        self.assertEqual(run.final_state, self.state)
        self.assertIs(run.trace[0].verification.verdict, Verdict.UNKNOWN)
        self.assertIn("ABSTAIN", run.trace[0].verification.evidence)
        self.assertIs(run.trace[1].verification.verdict, Verdict.REFUSED)

    def test_unrelated_miss_is_unknown_with_no_context(self) -> None:
        key = "zxqv nonexistent theorem 998877"
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            key,
            Literal("request", "needs", key),
        )
        result = RetrievalVerifier(self.store, self.executor).evaluate(
            state, retrieval_action(key)
        )
        self.assertIs(result.verdict, Verdict.UNKNOWN)
        self.assertIsNone(result.next_state)
        self.assertIn("ABSTAIN", result.evidence)

    def test_frame_local_refuses_before_store_and_routes_to_ask(self) -> None:
        class StoreMustNotRun:
            def query(self, key: str, limit: int = 24):
                raise AssertionError(f"frame-local guard leaked query {key!r}")

        local_frame = self.executor.open_frame(
            FrameSpec(frame="story.private", retrieval="frame_local")
        )
        state = RetrievalState.from_unknown(
            self.executor,
            local_frame,
            "tone",
            "user preferred tone",
            Literal("user", "prefers", "user preferred tone"),
        )
        result = RetrievalVerifier(StoreMustNotRun(), self.executor).evaluate(
            state, retrieval_action("user preferred tone")
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIn("ASK(tone)", result.evidence)

    def test_frame_gen_delegation_preserves_verdict_reason_and_evidence(self) -> None:
        actions = (
            Action.build(
                ActionKind.GEN,
                "assert_fact",
                {
                    "claim_id": "unknown",
                    "subject": "x",
                    "predicate": "p",
                    "value": "v",
                },
            ),
            Action.build(
                ActionKind.GEN,
                "assert_fact",
                {"claim_id": "malformed"},
            ),
            Action.build(
                ActionKind.GEN,
                "plant",
                {"event_id": "bell_seen", "element": "brass bell"},
            ),
        )
        direct_verifier = FrameAssertionVerifier(self.executor)
        wrapped_verifier = RetrievalVerifier(self.store, self.executor)
        for action in actions:
            with self.subTest(action=action.name, arguments=action.arguments):
                direct = direct_verifier.evaluate(self.frame, action)
                wrapped = wrapped_verifier.evaluate(self.state, action)
                self.assertEqual(wrapped.verdict, direct.verdict)
                self.assertEqual(wrapped.reason, direct.reason)
                self.assertEqual(wrapped.evidence, direct.evidence)

    def test_duplicate_retrieval_cannot_claim_progress_without_new_context(self) -> None:
        verifier = RetrievalVerifier(self.store, self.executor)
        first = verifier.evaluate(self.state, retrieval_action(DE_MORGAN))
        self.assertIs(first.verdict, Verdict.VERIFIED)
        duplicate = verifier.evaluate(
            first.next_state, retrieval_action(DE_MORGAN)
        )
        self.assertIs(duplicate.verdict, Verdict.REFUSED)
        self.assertIsNone(duplicate.next_state)

    def test_retrieve_requires_pending_unknown_and_nonempty_key(self) -> None:
        verifier = RetrievalVerifier(self.store, self.executor)
        no_pending = RetrievalState(frame=self.frame)
        self.assertIs(
            verifier.evaluate(no_pending, retrieval_action(DE_MORGAN)).verdict,
            Verdict.REFUSED,
        )
        empty = Action.build(ActionKind.RETRIEVE, "lookup", {"key": ""})
        self.assertIs(verifier.evaluate(self.state, empty).verdict, Verdict.REFUSED)

    def test_factory_rejects_a_key_unrelated_to_the_unknown_literal(self) -> None:
        with self.assertRaisesRegex(ValueError, "unresolved literal's value"):
            RetrievalState.from_unknown(
                self.executor,
                self.frame,
                "answer",
                "Quadratic Formula",
                Literal("request", "needs", DE_MORGAN),
            )

    def test_retrieve_rejects_an_alias_of_the_pending_target(self) -> None:
        result = RetrievalVerifier(self.store, self.executor).evaluate(
            self.state,
            retrieval_action("De Morgan's Laws (Propositional Form)"),
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)
        self.assertIn("must equal", result.reason)

    def test_verifier_rejects_a_directly_forged_pending_key(self) -> None:
        forged = replace(
            self.state,
            pending=replace(self.state.pending, suggested_key="Quadratic Formula"),
        )
        result = RetrievalVerifier(self.store, self.executor).evaluate(
            forged, retrieval_action("Quadratic Formula")
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)
        self.assertIn("malformed", result.reason)

    def test_point_rejects_context_material_forged_outside_the_store(self) -> None:
        real = self.store.query(DE_MORGAN).items[0]
        forged_item = replace(real, item_id="corpus:forged.de_morgan")
        forged = replace(
            self.state,
            context=(PointableMaterial(0, forged_item),),
        )
        result = RetrievalVerifier(self.store, self.executor).evaluate(
            forged, point_action(0)
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)
        self.assertIn("authoritative retrieval store", result.reason)

    def test_point_rejects_authentic_item_without_retrieve_receipt(self) -> None:
        real = self.store.query(DE_MORGAN).items[0]
        injected = replace(
            self.state,
            context=(PointableMaterial(0, real),),
        )
        result = RetrievalVerifier(self.store, self.executor).evaluate(
            injected, point_action(0)
        )
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)
        self.assertIn("no valid RETRIEVE receipt", result.reason)

    def test_retrieve_receipt_cannot_replay_into_another_session(self) -> None:
        verifier = RetrievalVerifier(self.store, self.executor)
        admitted = verifier.evaluate(self.state, retrieval_action(DE_MORGAN))
        other = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            DE_MORGAN,
            Literal("request", "needs", DE_MORGAN),
        )
        self.assertNotEqual(admitted.next_state.session_id, other.session_id)
        replayed = replace(
            other,
            context=admitted.next_state.context,
            retrieval_receipts=admitted.next_state.retrieval_receipts,
        )
        result = verifier.evaluate(replayed, point_action(0))
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)
        self.assertIn("no valid RETRIEVE receipt", result.reason)

    def test_retrieve_receipt_cannot_cross_into_frame_local_scope(self) -> None:
        verifier = RetrievalVerifier(self.store, self.executor)
        admitted = verifier.evaluate(self.state, retrieval_action(DE_MORGAN))
        local_frame = self.executor.open_frame(
            FrameSpec(frame="retrieval.private", retrieval="frame_local")
        )
        transplanted = replace(admitted.next_state, frame=local_frame)
        result = verifier.evaluate(transplanted, point_action(0))
        self.assertIs(result.verdict, Verdict.REFUSED)
        self.assertIsNone(result.next_state)
        self.assertIn("no valid RETRIEVE receipt", result.reason)

    def test_derivative_records_inherit_weakest_member_status(self) -> None:
        """Review F1: no record may outrank its weakest member.

        Registered prediction: every twin_ledger record's status equals the
        weakest schema status among its members, every decomposition record
        equals its statement's own status, and no derivative record carries
        the retired hardcoded "verified" label.
        """
        nodes = {}
        for item in self.store.items:
            if item.source == "corpus":
                nodes[item.source_ids[0]] = item.epistemic_status
        strength = {
            "conjectured": 0,
            "empirical": 1,
            "asymptotic": 2,
            "assumed": 3,
            "derived": 4,
            "formal": 5,
        }
        checked = 0
        for item in self.store.items:
            if item.source == "twin_ledger":
                member_statuses = [nodes[sid] for sid in item.source_ids]
                expected = min(member_statuses, key=lambda s: strength[s])
                self.assertEqual(item.epistemic_status, expected, item.item_id)
                checked += 1
            elif item.source == "decomposition":
                self.assertEqual(
                    item.epistemic_status, nodes[item.source_ids[0]], item.item_id
                )
                checked += 1
            self.assertNotEqual(item.epistemic_status, "verified", item.item_id)
        self.assertGreater(checked, 200)

    def test_empirical_member_no_longer_gets_stronger_labeled_twin(self) -> None:
        """Review F1's live reproduction, inverted into a control."""
        empirical = [
            item
            for item in self.store.items
            if item.source == "twin_ledger"
            and any(
                other.source == "corpus"
                and other.source_ids[0] in item.source_ids
                and other.epistemic_status == "empirical"
                for other in self.store.items
            )
        ]
        self.assertTrue(empirical)
        for item in empirical:
            self.assertEqual(item.epistemic_status, "empirical", item.item_id)

    def test_real_store_proof_records_carry_structured_trust(self) -> None:
        proofs = [item for item in self.store.items if item.source == "proof"]
        self.assertTrue(proofs)
        for item in proofs:
            self.assertTrue(item.trusted, item.item_id)
            self.assertEqual(item.epistemic_status, "proven")

    def test_exact_truncation_is_reported_not_silent(self) -> None:
        """Review F6: the deterministic limit must announce what it dropped."""
        result = self.store.query("equality")
        self.assertEqual(result.mode, "exact")
        self.assertGreater(result.total, len(result.items))
        state = RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            "equality",
            Literal("request", "needs", "equality"),
        )
        verifier = RetrievalVerifier(self.store, self.executor)
        outcome = verifier.evaluate(state, retrieval_action("equality"))
        self.assertIs(outcome.verdict, Verdict.VERIFIED)
        self.assertIn("deterministically truncated", outcome.reason)

    def test_point_on_closed_frame_names_the_closure(self) -> None:
        """Review F5: the refusal reason must tell the true story."""
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(self.state, retrieval_action(DE_MORGAN))
        closed_frame = replace(retrieved.next_state.frame, closed=True)
        closed_state = replace(retrieved.next_state, frame=closed_frame)
        outcome = verifier.evaluate(closed_state, point_action(0))
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("closed", outcome.reason)
        self.assertNotIn("stale", outcome.reason)

    def test_trusted_digest_with_wrong_system_label_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data_dir = root / "data"
            reports_dir = root / "reports"
            corpus_dir = data_dir / "logic"
            corpus_dir.mkdir(parents=True)
            reports_dir.mkdir()
            shutil.copyfile(
                REPO_ROOT / "prover" / "sample_triples.json",
                root / "proof.json",
            )
            node = {
                "statement_id": "logic.example.wrong_system",
                "title": "Wrong proof system",
                "semantic_interpretation": {"statement_meaning": "Example"},
                "structural_signature": {
                    "anonymized_template": "?0:P = ?0:P",
                    "archetype_id": "identity",
                },
                "keywords": [],
                "epistemic_status": "verified",
                "symbol_lexicon": {"symbols": [], "operators": []},
                "verified_by": [
                    {
                        "system": "not-lean",
                        "artifact": "proof.json",
                        "reference": "BooleanLaws.modus_ponens",
                    }
                ],
            }
            (corpus_dir / "nodes.json").write_text(
                json.dumps({"statement_nodes": [node]}), encoding="utf-8"
            )
            (reports_dir / "signature_matches.json").write_text(
                json.dumps(
                    {
                        "typed_twin_groups": [],
                        "family_twin_groups_beyond_typed": [],
                        "aliased_twin_groups_beyond_typed": [],
                        "mirror_twin_groups": [],
                        "shape_twin_groups": [],
                    }
                ),
                encoding="utf-8",
            )
            (reports_dir / "decompositions.json").write_text(
                json.dumps({"decompositions": []}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "only verified_by system"):
                UnifiedKnowledgeStore.load(data_dir, reports_dir)


if __name__ == "__main__":
    unittest.main()
