"""The public ladder demo delegates frame status to FrameExecutor."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from compose_assert import execute_frame_ladder  # noqa: E402
from controller import Verdict  # noqa: E402


class ComposeAssertFrameTests(unittest.TestCase):
    def test_registered_runtime_sequence_and_exit_demotion(self) -> None:
        steps, demoted = execute_frame_ladder()

        self.assertEqual(
            [(step.label, step.verdict) for step in steps],
            [
                ("declared truth", Verdict.VERIFIED),
                ("contradicted declaration", Verdict.REFUTED),
                ("missing trait", Verdict.UNKNOWN),
                ("suspended contradiction before admission", Verdict.UNKNOWN),
                ("suspended contradiction admitted", Verdict.VERIFIED),
                ("clean frame close", Verdict.VERIFIED),
                ("post-close check", Verdict.REFUSED),
            ],
        )
        self.assertEqual(len(demoted), 3)
        self.assertEqual(
            {claim.epistemic_status for claim in demoted}, {"conjectured"}
        )
        self.assertEqual(
            {claim.claim_id for claim in demoted},
            {"golden", "not_silver", "cartoon_hover"},
        )

    def test_runtime_evidence_names_frame_rules_and_world_ground(self) -> None:
        steps, _ = execute_frame_ladder()
        by_label = {step.label: step for step in steps}

        self.assertIn(
            "narrative.frame.frame_consistency",
            by_label["contradicted declaration"].evidence,
        )
        self.assertIn(
            "physics.gravitation.newton_universal_gravitation",
            by_label["suspended contradiction before admission"].evidence,
        )
        self.assertIn(
            "narrative.frames.compose_assert_demo",
            by_label["post-close check"].evidence,
        )


if __name__ == "__main__":
    unittest.main()
