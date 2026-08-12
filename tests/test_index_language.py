"""P-LS10 / P-LS12: index-relative belief and fiction language outcomes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from index_language import (  # noqa: E402
    FRAGMENT_ID,
    IndexStatus,
    MultiIndexWorld,
    attitude_report_surface,
    fiction_premise_surface,
)


class FalseBeliefLanguageTests(unittest.TestCase):
    """P-LS10: attitude report legal at belief while world REFUTED."""

    def test_five_surface_variants_belief_ok_world_refuted(self) -> None:
        variants = [
            "the marble is in the basket",
            "marble is in the basket",
            "it is in the basket",
            "the marble remains in the basket",
            "basket holds the marble",
        ]
        self.assertGreaterEqual(len(variants), 5)
        content = "marble_location=basket"
        for content_surface in variants:
            world = MultiIndexWorld()
            surface = attitude_report_surface("Sally", content_surface)
            belief_st, world_st = world.utter_attitude(surface, content)
            self.assertEqual(
                belief_st,
                IndexStatus.VERIFIED,
                f"surface={surface!r} belief={belief_st}",
            )
            self.assertEqual(
                world_st,
                IndexStatus.REFUTED,
                f"surface={surface!r} world={world_st}",
            )
            self.assertNotEqual(belief_st, world_st)
            self.assertEqual(FRAGMENT_ID, "index.language.v1")

    def test_surface_is_load_bearing_mismatch_refused(self) -> None:
        world = MultiIndexWorld()
        # Claims basket content_fact but surface packages a different phrase
        # that is not registered / mismatched → REFUSED (not auto-VERIFIED).
        belief_st, world_st = world.utter_attitude(
            "Sally believes nonsense content",
            "marble_location=basket",
        )
        self.assertEqual(belief_st, IndexStatus.REFUSED)
        self.assertEqual(world_st, IndexStatus.REFUSED)

    def test_surface_wrong_content_package_refused(self) -> None:
        world = MultiIndexWorld()
        surface = attitude_report_surface(
            "Sally", "the marble is in the basket"
        )
        # Mismatched structured fact vs surface package
        belief_st, world_st = world.utter_attitude(
            surface, "marble_location=box"
        )
        self.assertEqual(belief_st, IndexStatus.REFUSED)
        self.assertEqual(world_st, IndexStatus.REFUSED)


class FictionAssertTests(unittest.TestCase):
    """P-LS12: fiction premise assert legal; no world VERIFIED leak on exit."""

    def test_five_fiction_premises_and_exit_non_leak(self) -> None:
        premises = [
            "trait=copper_eggs",
            "trait=sings",
            "location=coop",
            "desire=sunrise",
            "object=feather",
        ]
        self.assertGreaterEqual(len(premises), 5)
        world = MultiIndexWorld()
        for fact in premises:
            surface = fiction_premise_surface(fact)
            self.assertTrue(surface.startswith("suppose "))
            status = world.utter_fiction_assert(fact)
            self.assertEqual(
                status,
                IndexStatus.VERIFIED,
                f"fact={fact!r} status={status}",
            )
            self.assertFalse(world.world_has(fact))

        world.close_fiction()
        for fact in premises:
            # Closed frame refuses new asserts
            st = world.utter_fiction_assert(f"extra_{fact}")
            self.assertEqual(st, IndexStatus.REFUSED)
            # Promotion laundering refused; world not verified
            promo = world.promote_fiction_to_world(fact)
            self.assertEqual(promo, IndexStatus.REFUSED)
            self.assertFalse(world.world_has(fact))
        # Leaks counted as attempts, not as world verification
        self.assertEqual(world.world_verified_leaks, len(premises))
        self.assertTrue(all(not world.world_has(f) for f in premises))

    def test_world_starts_with_box_not_basket(self) -> None:
        world = MultiIndexWorld()
        self.assertTrue(world.world_has("marble_location=box"))
        self.assertFalse(world.world_has("marble_location=basket"))


if __name__ == "__main__":
    unittest.main()
