#!/usr/bin/env python3
"""Construction-only tests for the v0.14 clarification preregistration.

Nothing in this module calls a resolver on a registered v0.14 query.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from measure_when_to_ask import (  # noqa: E402
    BLIND_LIMIT,
    ProtocolError,
    SPEC_PATH,
    FORBIDDEN_PATH,
    MANIFEST_PATH,
    _candidate_resolvers,
    _context_constraint,
    _read_forbidden,
    _read_rows,
    _prior_queries,
    blind_followup,
    blind_initial,
    grammar_normalize,
    masked_rank_reference,
    parse_followup,
    parse_negative,
    reciprocal_candidate_load,
    recompute_forbidden_ids,
    validate_structure,
    verify_manifest,
)


def node(title: str, *, meaning: str = "", keywords: list[str] | None = None) -> dict:
    return {
        "title": title,
        "semantic_interpretation": {"statement_meaning": meaning},
        "keywords": keywords or [],
        "symbol_lexicon": {},
    }


class FrozenNegativeGrammar(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = {
            "keep": (node("finite area"), "x"),
            "drop": (node("square area", keywords=["square"]), "x"),
        }

    def test_exact_suffix_produces_positive_payload_and_veto(self) -> None:
        plan = parse_negative("FINITE   area WITHOUT square", self.corpus)
        self.assertEqual(plan.normalized_query, "finite area without square")
        self.assertEqual(plan.positive, "finite area")
        self.assertEqual(plan.required_tokens, ("square",))
        self.assertEqual(plan.veto_ids, ("drop",))

    def test_punctuation_conjunction_and_multiple_markers_refuse(self) -> None:
        malformed = (
            "finite area without square.",
            "finite area without square and circle",
            "finite,without circle without square",
        )
        for query in malformed:
            with self.subTest(query=query), self.assertRaises(ProtocolError):
                parse_negative(query, self.corpus)

    def test_empty_reduced_term_and_positive_refuse(self) -> None:
        def reducer(text: str) -> tuple[str, ...]:
            return () if text in {"square", "empty"} else ("known",)

        with self.assertRaisesRegex(ProtocolError, "TERM"):
            parse_negative("finite area without square", self.corpus, reducer)
        with self.assertRaisesRegex(ProtocolError, "positive"):
            parse_negative("empty without square", self.corpus, lambda _text: ())

    def test_inventory_uses_nested_symbol_lexicon_values(self) -> None:
        corpus = {
            "veto": ({
                **node("other"),
                "symbol_lexicon": {"symbols": [{"description": "square scale"}]},
            }, "x")
        }
        self.assertEqual(parse_negative("finite area without square", corpus).veto_ids, ("veto",))


class MaskAwareSelectionContract(unittest.TestCase):
    def test_lower_score_survivor_can_win_after_top_is_excluded(self) -> None:
        ranked = masked_rank_reference((("top", 1.0), ("lower", 0.7)), {"top"})
        self.assertEqual(ranked, (("lower", 0.7),))

    def test_non_veto_scores_and_order_are_invariant(self) -> None:
        scored = (("a", 0.8), ("b", 0.8), ("c", 0.3))
        baseline = masked_rank_reference(scored, ())
        masked = masked_rank_reference(scored, {"c"})
        self.assertEqual(masked, baseline[:2])

    def test_every_candidate_surface_obeys_same_mask(self) -> None:
        surfaces = {
            "expression": (("veto", 1.0), ("keep", 0.5)),
            "literal_id": (("veto", 1.0),),
            "word": (("veto", 0.9), ("keep", 0.7)),
        }
        for name, scored in surfaces.items():
            with self.subTest(surface=name):
                self.assertNotIn("veto", {sid for sid, _ in masked_rank_reference(scored, {"veto"})})

    def test_last_owner_mask_does_not_redefine_known_words(self) -> None:
        known_words = frozenset({"only_owner_word"})
        _allowed = masked_rank_reference((("only_owner", 1.0),), {"only_owner"})
        self.assertIn("only_owner_word", known_words)
        self.assertEqual(_allowed, ())

    def test_q1_q6_are_compatible_at_preselection_seam(self) -> None:
        full = masked_rank_reference((("excluded", 1.0), ("intended", 0.8)), {"excluded"})
        stripped = masked_rank_reference((("excluded", 1.0), ("intended", 0.8)), ())
        self.assertEqual(full[0][0], "intended")
        self.assertEqual(stripped[0][0], "excluded")


class BlindControl(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = {
            "a": (node("alpha beta"), "x"),
            "b": (node("alpha gamma"), "x"),
            "c": (node("delta"), "x"),
        }

    def test_initial_is_title_only_jaccard_then_id(self) -> None:
        self.assertEqual(blind_initial("alpha beta", self.corpus)[:2], ("a", "b"))

    def test_followup_uses_value_only_and_keeps_all_positive_ties(self) -> None:
        kind, value = parse_followup("narrow word alpha")
        self.assertEqual((kind, value), ("word", "alpha"))
        self.assertEqual(blind_followup(("a", "b", "c"), "narrow word alpha", self.corpus), ("a", "b"))

    def test_zero_match_preserves_initial_set(self) -> None:
        initial = ("a", "b", "c")
        self.assertEqual(blind_followup(initial, "narrow word absent", self.corpus), initial)

    def test_full_graph_or_over_budget_answer_scores_zero(self) -> None:
        candidates = tuple(f"id{i}" for i in range(BLIND_LIMIT + 1))
        self.assertEqual(reciprocal_candidate_load("id0", candidates), 0.0)
        self.assertEqual(reciprocal_candidate_load("id0", ()), 0.0)


class RegisteredConstruction(unittest.TestCase):
    def test_complete_preregistration_passes_without_scoring(self) -> None:
        receipt = validate_structure()
        self.assertEqual(receipt["rows"], 48)
        self.assertEqual(receipt["unique_primary_ids"], 38)
        self.assertEqual(receipt["follow_up_profile"], {"corpus": 6, "discipline": 6, "word": 8})

    def test_no_result_exists_in_preregistration(self) -> None:
        self.assertFalse((ROOT / "experiments" / "when_to_ask_result.raw.json").exists())
        self.assertFalse((ROOT / "experiments" / "when_to_ask_result.json").exists())

    def test_key_receipt_contains_no_external_text_or_keys(self) -> None:
        path = ROOT / "experiments" / "when_to_ask_oewn_keys.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual([arm["sample_size"] for arm in receipt["arms"]], [1000, 1000, 1000])
        self.assertNotIn("selected_keys", receipt)
        self.assertNotIn("texts", receipt)

    def test_existing_manifest_objects_and_trees_are_coherent(self) -> None:
        manifest = verify_manifest()
        base = "f38678953cd884e7c9578dae944bee0db6b16fb3"
        self.assertEqual(manifest["base_commit"], base)
        self.assertEqual({item["path"] for item in manifest["data_trees"]}, {"data", "data_holdout"})
        pinned = [manifest["scripts_tree"]["git_commit"]]
        pinned += [entry["git_commit"] for entry in manifest["existing_inputs"]]
        pinned += [entry["git_commit"] for entry in manifest["data_trees"]]
        self.assertEqual(set(pinned), {base})

    def test_forbidden_ids_recompute_from_the_pinned_spent_tree(self) -> None:
        frozen = json.loads(FORBIDDEN_PATH.read_text(encoding="utf-8"))
        recomputed = recompute_forbidden_ids()
        self.assertEqual(list(recomputed), frozen["forbidden_intended_ids"])
        self.assertEqual(len(recomputed), 88)

    def test_candidate_scoring_api_is_deliberately_absent(self) -> None:
        with self.assertRaisesRegex(ProtocolError, "candidate absent"):
            _candidate_resolvers()

    def test_follow_up_guards_refuse_before_the_one_shot_run(self) -> None:
        """Both new construction guards must be trippable, not decorative."""
        base = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        directory = tempfile.TemporaryDirectory(prefix="when-to-ask-followup-")
        self.addCleanup(directory.cleanup)

        def spec_with(mutate) -> Path:
            payload = deepcopy(base)
            for row in payload["rows"]:
                if row["expected_route"] == "ASK":
                    mutate(row)
                    break
            path = Path(directory.name) / "spec.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return path

        def drop_declared_reading(row: dict) -> None:
            # A corpus that exists but is not the retained id's own corpus.
            row["follow_up"]["value"] = "narrative.structure.v1"
            row["follow_up"]["class"] = "corpus"
            row["follow_up"]["line"] = "narrow corpus narrative.structure.v1"

        def diverge_from_runtime_parse(row: dict) -> None:
            # The scorer applies NFKC and the live shell does not, so a
            # fullwidth first letter leaves the two parses narrowing on
            # different VALUE strings while the declared fields still agree.
            value = row["follow_up"]["value"]
            fullwidth = chr(ord(value[0]) - ord("a") + 0xFF41) + value[1:]
            row["follow_up"]["line"] = row["follow_up"]["line"].replace(value, fullwidth)

        with self.assertRaisesRegex(ProtocolError, "drops its own declared retained ids"):
            validate_structure(spec_path=spec_with(drop_declared_reading))
        with self.assertRaisesRegex(ProtocolError, "differs from the runtime parse"):
            validate_structure(spec_path=spec_with(diverge_from_runtime_parse))

    def test_runtime_follow_up_parse_is_the_live_shell_parse(self) -> None:
        from harness import _context_constraint as live  # noqa: PLC0415

        for line in (
            "narrow word cube",
            "narrow corpus geometry.foundations.v1",
            "narrow  discipline   physics",
            "narrow word",
            "narrow id geometry.area_formulas.rectangle_area_formula",
        ):
            self.assertEqual(_context_constraint(line), live(line), line)


class FailClosedSchemas(unittest.TestCase):
    def _temporary_json(self, payload: object) -> Path:
        directory = tempfile.TemporaryDirectory(prefix="when-to-ask-schema-")
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "fixture.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_holdout_rejects_missing_extra_and_scalar_rows(self) -> None:
        base = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        mutations = []
        missing = deepcopy(base)
        del missing["rows"][0]["rationale"]
        mutations.append(missing)
        extra = deepcopy(base)
        extra["rows"][0]["oracle_hint"] = "forbidden"
        mutations.append(extra)
        scalar = deepcopy(base)
        scalar["rows"][0] = "not an object"
        mutations.append(scalar)
        top_extra = deepcopy(base)
        top_extra["result"] = 1
        mutations.append(top_extra)
        for payload in mutations:
            with self.subTest(kind=list(payload) if isinstance(payload, dict) else type(payload)):
                with self.assertRaises(ProtocolError):
                    _read_rows(self._temporary_json(payload))

    def test_holdout_rejects_wrong_field_types_and_nested_shapes(self) -> None:
        base = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        mutations = []
        for field, value in (
            ("query", 7), ("expected_route", ["ASK"]),
            ("primary_id", 9), ("retained_ids", "id"),
        ):
            changed = deepcopy(base)
            changed["rows"][0][field] = value
            mutations.append(changed)
        follow = deepcopy(base)
        follow["rows"][8]["follow_up"]["extra"] = True
        mutations.append(follow)
        negative = deepcopy(base)
        negative["rows"][0]["negative_span"] = "without square"
        mutations.append(negative)
        for payload in mutations:
            with self.assertRaises(ProtocolError):
                _read_rows(self._temporary_json(payload))

    def test_forbidden_ledger_rejects_schema_count_order_and_digest_drift(self) -> None:
        base = json.loads(FORBIDDEN_PATH.read_text(encoding="utf-8"))
        mutations = []
        extra = deepcopy(base)
        extra["unknown"] = 1
        mutations.append(extra)
        count = deepcopy(base)
        count["id_count"] = 87
        mutations.append(count)
        order = deepcopy(base)
        order["forbidden_intended_ids"][:2] = reversed(order["forbidden_intended_ids"][:2])
        mutations.append(order)
        digest = deepcopy(base)
        digest["ordered_ids_sha256"] = "0" * 64
        mutations.append(digest)
        for payload in mutations:
            with self.assertRaises(ProtocolError):
                _read_forbidden(self._temporary_json(payload))

    def test_prior_query_documents_fail_closed(self) -> None:
        malformed = (
            [],
            {"queries": "not a list"},
            {"queries": ["not an object"]},
            {"queries": [{"text": 4}]},
        )
        for payload in malformed:
            with self.assertRaises(ProtocolError):
                _prior_queries((self._temporary_json(payload),))

    def test_manifest_rejects_extra_missing_and_nested_shape_drift(self) -> None:
        base = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        mutations = []
        extra = deepcopy(base)
        extra["oracle"] = "no"
        mutations.append(extra)
        missing = deepcopy(base)
        del missing["raw_ledger_contract"]
        mutations.append(missing)
        nested = deepcopy(base)
        nested["data_trees"][0]["extra"] = 1
        mutations.append(nested)
        scalar = deepcopy(base)
        scalar["existing_inputs"][0] = "not an object"
        mutations.append(scalar)
        unsorted = deepcopy(base)
        unsorted["allowed_candidate_paths"] = list(reversed(unsorted["allowed_candidate_paths"]))
        mutations.append(unsorted)
        for payload in mutations:
            with self.assertRaises(ProtocolError):
                verify_manifest(self._temporary_json(payload))


if __name__ == "__main__":
    unittest.main()
