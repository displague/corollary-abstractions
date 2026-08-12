"""P-LS9: entailment query does not mutate world; fragment named; N≥15."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from entailment import (  # noqa: E402
    FRAGMENT_ID,
    Relation,
    WorldProbe,
    query,
    registered_pairs,
)


class EntailmentQueryTests(unittest.TestCase):
    def test_registered_suite_n_ge_15(self) -> None:
        pairs = registered_pairs()
        self.assertGreaterEqual(len(pairs), 15)

    def test_all_registered_pairs_match_query(self) -> None:
        world = WorldProbe()
        for premise, conclusion, expected in registered_pairs():
            ans = query(premise, conclusion, world)
            self.assertEqual(ans.relation, expected, f"{premise}->{conclusion}")
            self.assertEqual(ans.fragment_id, FRAGMENT_ID)
            self.assertEqual(ans.world_mutations, 0)
        self.assertEqual(world.mutations, 0)
        self.assertEqual(world.facts, set())

    def test_query_never_mutates_world(self) -> None:
        world = WorldProbe()
        world.facts.add("preexisting")
        ans = query("p_and_q", "p", world)
        self.assertEqual(ans.relation, Relation.ENTAILS)
        self.assertEqual(world.mutations, 0)
        self.assertEqual(world.facts, {"preexisting"})

    def test_contradiction_symmetric(self) -> None:
        a = query("marble_in_box", "marble_in_basket")
        b = query("marble_in_basket", "marble_in_box")
        self.assertEqual(a.relation, Relation.CONTRADICTS)
        self.assertEqual(b.relation, Relation.CONTRADICTS)

    def test_unknown_outside_inventory(self) -> None:
        ans = query("not_a_real_prop", "also_fake")
        self.assertEqual(ans.relation, Relation.UNKNOWN)
        self.assertEqual(ans.fragment_id, FRAGMENT_ID)

    def test_independent(self) -> None:
        ans = query("all_birds_fly", "marble_in_box")
        self.assertEqual(ans.relation, Relation.INDEPENDENT)


if __name__ == "__main__":
    unittest.main()
