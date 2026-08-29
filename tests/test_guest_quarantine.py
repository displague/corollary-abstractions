#!/usr/bin/env python3
"""G-P1: a planted write under data/ moves the digest and is caught.

A fence that cannot go red is no fence. The real repository's data/ is
not the plant target; the control runs in a throwaway tree.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from guest_quarantine import (  # noqa: E402
    digest_data,
    planted_write_is_caught,
    session_unchanged,
)
from write_stage import durable_digest  # noqa: E402


class PlantedWriteControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="gp1-quarantine-")
        self.data = Path(self._tmp.name) / "data"
        self.data.mkdir()
        (self.data / "seed.txt").write_text("committed corpus stand-in\n", encoding="utf-8")
        self.addCleanup(self._tmp.cleanup)

    def test_planted_write_moves_the_digest_and_is_caught(self) -> None:
        result = planted_write_is_caught(self.data)
        self.assertTrue(result["caught"], result)
        self.assertTrue(result["restored"], result)
        self.assertEqual(result["digest_before"], result["digest_after_remove"])
        self.assertNotEqual(result["digest_before"], result["digest_after_plant"])

    def test_an_untouched_session_does_not_move_the_digest(self) -> None:
        before = digest_data(self.data)
        self.assertTrue(session_unchanged(self.data, before))
        self.assertEqual(digest_data(self.data), before)

    def test_the_callable_is_write_stage_durable_digest(self) -> None:
        self.assertEqual(digest_data(self.data), durable_digest(self.data))

    def test_the_real_data_tree_is_not_the_plant_target(self) -> None:
        real = durable_digest(REPO / "data")
        planted_write_is_caught(self.data)
        self.assertEqual(durable_digest(REPO / "data"), real)


if __name__ == "__main__":
    unittest.main()
