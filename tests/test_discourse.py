"""P-LS7 first cut: discourse store is load-bearing for anaphora."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from discourse import (  # noqa: E402
    FRAGMENT_ID,
    Anaphor,
    DiscourseEntity,
    DiscourseState,
    EntityKind,
)


class DiscourseStoreTests(unittest.TestCase):
    def test_introduce_then_resolve_it(self) -> None:
        feather = DiscourseEntity(
            "fallen_feather",
            EntityKind.NEUTER,
            surfaces=("fallen feather",),
        )
        state = DiscourseState().introduce(feather)
        hit = state.resolve(Anaphor.IT)
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual(hit.entity_id, "fallen_feather")
        self.assertEqual(state.fragment_id, FRAGMENT_ID)

    def test_most_salient_wins_among_compatible(self) -> None:
        a = DiscourseEntity("nest", EntityKind.NEUTER)
        b = DiscourseEntity("feather", EntityKind.NEUTER)
        state = DiscourseState().introduce(a).introduce(b)
        self.assertEqual(state.resolve("it").entity_id, "feather")
        # re-intro a → a most salient
        state = state.introduce(a)
        self.assertEqual(state.resolve(Anaphor.IT).entity_id, "nest")

    def test_gender_incompatibility_skips(self) -> None:
        hen = DiscourseEntity("hen", EntityKind.FEM)
        state = DiscourseState().introduce(hen)
        self.assertIsNone(state.resolve(Anaphor.HE))
        self.assertEqual(state.resolve(Anaphor.SHE).entity_id, "hen")

    def test_wipe_ablation_forces_miss(self) -> None:
        """P-LS7: empty store must not invent a referent."""
        state = (
            DiscourseState()
            .introduce(DiscourseEntity("feather", EntityKind.NEUTER))
            .wipe()
        )
        self.assertEqual(state.entities, ())
        self.assertIsNone(state.resolve(Anaphor.IT))
        self.assertIsNone(state.resolve(Anaphor.THAT))

    def test_unknown_anaphor_string_fails_closed(self) -> None:
        state = DiscourseState().introduce(
            DiscourseEntity("x", EntityKind.NEUTER)
        )
        self.assertIsNone(state.resolve("yonder"))

    def test_empty_entity_id_refused(self) -> None:
        with self.assertRaises(ValueError):
            DiscourseEntity("  ", EntityKind.NEUTER)


if __name__ == "__main__":
    unittest.main()
