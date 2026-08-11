"""Integrity of the external-source manifest and the fetch/verify logic.

The manifest is the reproducibility contract for v0.9 ingestion inputs: every
DIRECT source must pin a real SHA-256 so a fetch can be verified byte-for-byte,
and the verify logic must actually reject a mismatch. These tests do NOT touch
the network or the (gitignored) archives; they check structure and the pure SHA
logic on synthetic files.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import fetch_sources  # noqa: E402

MANIFEST = json.loads((REPO_ROOT / "data_sources" / "manifest.json").read_text(encoding="utf-8"))
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ManifestStructure(unittest.TestCase):
    def test_has_schema_and_sources(self) -> None:
        self.assertEqual(MANIFEST["schema_version"], 1)
        self.assertTrue(MANIFEST["sources"])

    def test_ids_and_urls_are_unique(self) -> None:
        ids = [s["id"] for s in MANIFEST["sources"]]
        urls = [s["url"] for s in MANIFEST["sources"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate source id")
        self.assertEqual(len(urls), len(set(urls)), "duplicate source url")

    def test_every_source_has_required_metadata(self) -> None:
        for s in MANIFEST["sources"]:
            for key in ("id", "url", "group", "access", "license", "purpose"):
                self.assertIn(key, s, f"{s.get('id')} missing {key}")
            self.assertTrue(s["url"].startswith("https://"), s["id"])

    def test_direct_sources_pin_a_real_sha_and_size(self) -> None:
        direct = [s for s in MANIFEST["sources"] if s["access"] == "direct"]
        self.assertTrue(direct)
        for s in direct:
            self.assertTrue(s.get("filename"), f"{s['id']} direct source needs a filename")
            self.assertTrue(_HEX64.match(s.get("sha256", "")), f"{s['id']} sha256 not 64-hex")
            self.assertIsInstance(s.get("size_bytes"), int)
            self.assertGreater(s["size_bytes"], 0)

    def test_direct_filenames_are_unique_in_the_archive_dir(self) -> None:
        # The span/wiki basename collision is resolved by distinct manifest
        # filenames; a collision here would overwrite one archive with another.
        names = [s["filename"] for s in MANIFEST["sources"] if s["access"] == "direct"]
        self.assertEqual(len(names), len(set(names)), "two direct sources share a filename")

    def test_gated_sources_are_marked(self) -> None:
        for s in MANIFEST["sources"]:
            if s["access"] == "hf-dataset-gated":
                self.assertIn("FORM-GATED", s["license"].upper().replace("-", "-") or "")


class VerifyLogic(unittest.TestCase):
    def test_sha256_matches_hashlib(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.bin"
            p.write_bytes(b"corollary" * 1000)
            self.assertEqual(fetch_sources._sha256(p), hashlib.sha256(b"corollary" * 1000).hexdigest())

    def test_verify_one_ok_missing_and_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            archive = Path(d)
            (archive / "a.zip").write_bytes(b"hello")
            good = hashlib.sha256(b"hello").hexdigest()
            self.assertEqual(
                fetch_sources._verify_one(archive, {"filename": "a.zip", "sha256": good, "size_bytes": 5})[0],
                "OK",
            )
            self.assertEqual(
                fetch_sources._verify_one(archive, {"filename": "a.zip", "sha256": "0" * 64, "size_bytes": 5})[0],
                "MISMATCH",
            )
            self.assertEqual(
                fetch_sources._verify_one(archive, {"filename": "missing.zip", "sha256": good})[0],
                "MISSING",
            )

    def test_env_token_reader_never_returns_a_stray_value(self) -> None:
        # With no HF_TOKEN in env and no .env line, the reader returns None
        # rather than something truthy — the fetcher must not invent a token.
        import os

        saved = os.environ.pop("HF_TOKEN", None)
        try:
            # Point the reader at a repo with no .env by monkeypatching the path.
            original = fetch_sources.REPO_ROOT
            with tempfile.TemporaryDirectory() as d:
                fetch_sources.REPO_ROOT = Path(d)
                try:
                    self.assertIsNone(fetch_sources._load_env_token())
                finally:
                    fetch_sources.REPO_ROOT = original
        finally:
            if saved is not None:
                os.environ["HF_TOKEN"] = saved


if __name__ == "__main__":
    unittest.main()
