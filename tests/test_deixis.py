"""P-LS6: deixis composes owner/here/now — not lexicon person features."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from deixis import (  # noqa: E402
    FRAGMENT_ID,
    DeicticIndex,
    DeicticToken,
    resolve_deictic,
    resolve_dialogue_turn,
)


class DeixisCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = DeicticIndex(
            speaker_id="alice",
            addressee_id="bob",
            here_id="kitchen",
            now_id="t0",
        )

    def test_fragment_id(self) -> None:
        self.assertEqual(FRAGMENT_ID, "deixis.compose.v1")

    def test_ten_resolutions_use_index_not_lexicon(self) -> None:
        """Floor: 10/10 use frame-like index fields."""
        cases = [
            ("i", "alice"),
            ("I", "alice"),
            ("you", "bob"),
            ("YOU", "bob"),
            ("here", "kitchen"),
            ("HERE", "kitchen"),
            ("now", "t0"),
            ("Now", "t0"),
            (DeicticToken.I, "alice"),
            (DeicticToken.YOU, "bob"),
        ]
        self.assertGreaterEqual(len(cases), 10)
        for token, expected in cases:
            self.assertEqual(
                resolve_deictic(token, self.index),
                expected,
                msg=f"token={token!r}",
            )

    def test_missing_index_fails_closed(self) -> None:
        for token in ("i", "you", "here", "now"):
            self.assertIsNone(resolve_deictic(token, None))

    def test_unknown_token_fails_closed(self) -> None:
        self.assertIsNone(resolve_deictic("yonder", self.index))

    def test_wordnet_person_alone_is_not_enough(self) -> None:
        """Without index, even person-looking tokens do not resolve."""
        # Simulates "lexicon said this is a person pronoun" with no index.
        self.assertIsNone(resolve_deictic("i", None))
        self.assertIsNone(resolve_deictic("you", None))

    def test_dialogue_turn_batch(self) -> None:
        got = resolve_dialogue_turn(("i", "you", "here", "now"), self.index)
        self.assertEqual(
            got,
            {
                "i": "alice",
                "you": "bob",
                "here": "kitchen",
                "now": "t0",
            },
        )

    def test_empty_index_fields_refused(self) -> None:
        with self.assertRaises(ValueError):
            DeicticIndex("alice", "bob", "kitchen", "  ")


if __name__ == "__main__":
    unittest.main()
