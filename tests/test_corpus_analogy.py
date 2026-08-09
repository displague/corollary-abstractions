from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

from corpus_analogy import (  # noqa: E402
    build_quadruples,
    evaluate,
    literal_vocabulary_coverage,
    parse_template,
    pointer_row,
    raw_nodes,
    render,
)


class CorpusAnalogyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.quads = build_quadruples(
            ROOT / "data", ROOT / "reports" / "specializations.json")

    def test_live_corpus_has_novel_cross_discipline_quadruples(self) -> None:
        self.assertGreater(len(self.quads), 0)
        self.assertTrue(all(q.a_discipline != q.c_discipline
                            for q in self.quads))
        authored = {
            render(parse_template(
                node["structural_signature"]["anonymized_template"]))
            for node in raw_nodes(ROOT / "data").values()
        }
        self.assertTrue(all(render(q.actual[3]) not in authored
                            for q in self.quads))
        self.assertTrue(all(render(q.actual[2]) != render(q.actual[3])
                            for q in self.quads))

    def test_every_target_is_reconstructible_only_from_pointed_input(self) -> None:
        for quad in self.quads:
            row = pointer_row(quad)
            self.assertEqual(
                [row["tokens_struct"][i] for i in row["target_positions"]],
                row["target_tokens"],
            )
            first = row["tokens_struct"].index("<sep>")
            second = row["tokens_struct"].index("<sep>", first + 1)
            segments = (row["tokens_struct"][:first],
                        row["tokens_struct"][first + 1:second],
                        row["tokens_struct"][second + 1:])
            self.assertNotIn(row["target_tokens"], segments)

    def test_literal_checkpoint_vocabulary_is_not_silently_claimed(self) -> None:
        literal_slots = {slot for quad in self.quads
                         for tree in quad.actual for slot in _slots(tree)}
        normalized_slots = {slot for quad in self.quads
                            for tree in quad.normalized for slot in _slots(tree)}
        self.assertTrue(literal_slots - normalized_slots)

    def test_specialization_ledger_is_load_bearing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "specializations.json"
            empty.write_text('{"specialization_edges": []}\n', encoding="utf-8")
            self.assertEqual(build_quadruples(ROOT / "data", empty), [])

    def test_baselines_are_computed_on_the_live_targets(self) -> None:
        result = evaluate(
            None, ROOT / "data", ROOT / "reports" / "specializations.json")
        self.assertEqual(result["symbolic_exact"], 1.0)
        sanity = result["novelty_sanity_controls"]
        self.assertEqual(sanity["copy_c_exact"], 0.0)
        self.assertEqual(sanity["nearest_authored_exact"], 0.0)
        self.assertGreater(sanity["nearest_authored_mean_similarity"], 0.0)
        self.assertEqual(
            result["capability_blind"]["last_slot_number_transfer_exact"],
            1.0,
        )

    def test_vocabulary_refusal_depends_on_the_supplied_vocabulary(self) -> None:
        empty = literal_vocabulary_coverage(self.quads, set())
        all_tokens = {token for quad in self.quads for tree in quad.actual[:3]
                      for token in _serialize(tree)}
        complete = literal_vocabulary_coverage(self.quads, all_tokens)
        self.assertEqual(empty["status"], "REFUSED_FIXED_CHECKPOINT_VOCAB")
        self.assertEqual(complete["status"], "AVAILABLE")


def _slots(tree: tuple) -> set[str]:
    if tree[0] == "slot":
        return {tree[1]}
    if tree[0] == "num":
        return set()
    return set().union(*(_slots(child) for child in tree[2]))


def _serialize(tree: tuple) -> list[str]:
    from corpus_analogy import serialize
    return serialize(tree)


if __name__ == "__main__":
    unittest.main()
