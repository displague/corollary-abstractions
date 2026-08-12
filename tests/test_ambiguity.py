"""P-LS8: hard-filter forest before prefer; no silent unique when multi."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from ambiguity import (  # noqa: E402
    FRAGMENT_ID,
    AmbiguityOutcome,
    AmbiguityItem,
    ForestCandidate,
    HardConstraint,
    hard_filter,
    make_attachment_suite,
    resolve_forest,
)


class PackedAmbiguityTests(unittest.TestCase):
    def test_suite_m_ge_15_with_two_plus_candidates(self) -> None:
        suite = make_attachment_suite()
        self.assertGreaterEqual(len(suite), 15)
        for item in suite:
            self.assertGreaterEqual(len(item.candidates), 2, item.item_id)

    def test_hard_filter_before_prefer_never_on_raw_forest(self) -> None:
        suite = make_attachment_suite()
        prefer_ran_on_raw = 0
        for item in suite:
            # Force prefer_when_multi with a prefer that would pick first of RAW
            raw_first = item.candidates[0]

            def prefer_raw(survivors, pick=raw_first):
                # If called with unfiltered forest equal to all candidates,
                # we would wrongly unique-resolve. hard path must not do that
                # when constraints eliminate.
                return survivors[0]

            result = resolve_forest(
                item, prefer_when_multi=False, prefer=prefer_raw
            )
            self.assertFalse(
                result.preferred_invoked,
                f"{item.item_id}: preference must not run by default",
            )
            if len(item.constraints) > 0:
                # Survivors must be subset after filter
                surv_ids = {c.candidate_id for c in result.survivors}
                all_ids = {c.candidate_id for c in item.candidates}
                self.assertTrue(surv_ids <= all_ids)
                if len(result.survivors) == 1:
                    self.assertEqual(result.outcome, AmbiguityOutcome.UNIQUE)
                elif len(result.survivors) > 1:
                    self.assertEqual(result.outcome, AmbiguityOutcome.MULTI)
                else:
                    self.assertEqual(result.outcome, AmbiguityOutcome.UNKNOWN)

    def test_multi_not_silent_unique_when_unfiltered(self) -> None:
        item = AmbiguityItem(
            item_id="plain_multi",
            surface="saw the man with the telescope",
            candidates=(
                ForestCandidate("h", "attach_high", "k1"),
                ForestCandidate("l", "attach_low", "k2"),
            ),
            constraints=(),
        )
        result = resolve_forest(item)
        self.assertEqual(result.outcome, AmbiguityOutcome.MULTI)
        self.assertEqual(len(result.survivors), 2)
        self.assertFalse(result.preferred_invoked)
        self.assertEqual(result.fragment_id, FRAGMENT_ID)

    def test_constraint_reduces_to_unique(self) -> None:
        low = ForestCandidate("l", "attach_low", "k2")
        high = ForestCandidate("h", "attach_high", "k1")
        item = AmbiguityItem(
            item_id="blocked_low",
            surface="s",
            candidates=(high, low),
            constraints=(
                HardConstraint("no_low", lambda c: c.candidate_id != "l"),
            ),
        )
        result = resolve_forest(item)
        self.assertEqual(result.outcome, AmbiguityOutcome.UNIQUE)
        self.assertEqual(result.survivors[0].candidate_id, "h")
        self.assertEqual(len(result.eliminated), 1)

    def test_all_eliminated_is_unknown(self) -> None:
        item = AmbiguityItem(
            item_id="none",
            surface="s",
            candidates=(
                ForestCandidate("a", "r1", "k1"),
                ForestCandidate("b", "r2", "k2"),
            ),
            constraints=(HardConstraint("block_all", lambda c: False),),
        )
        result = resolve_forest(item)
        self.assertEqual(result.outcome, AmbiguityOutcome.UNKNOWN)
        self.assertEqual(result.survivors, ())

    def test_prefer_oov_refused(self) -> None:
        item = AmbiguityItem(
            item_id="multi",
            surface="s",
            candidates=(
                ForestCandidate("a", "r1", "k1"),
                ForestCandidate("b", "r2", "k2"),
            ),
        )
        ghost = ForestCandidate("ghost", "r", "k")

        def prefer_oov(survivors):
            return ghost

        with self.assertRaises(ValueError):
            resolve_forest(item, prefer_when_multi=True, prefer=prefer_oov)

    def test_item_requires_two_candidates(self) -> None:
        with self.assertRaises(ValueError):
            AmbiguityItem(
                item_id="solo",
                surface="s",
                candidates=(ForestCandidate("a", "r", "k"),),
            )


if __name__ == "__main__":
    unittest.main()
