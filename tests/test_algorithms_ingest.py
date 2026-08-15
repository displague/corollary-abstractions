"""TheAlgorithms/Python GCD ingest: manifest pin, license, citations.

The citation string is REQUIRED (MIT attribution) and load-bearing: tests
assert it verbatim in the manifest entry, the derived NOTICE, and the
extract. Archive-dependent regeneration uses the skip-if-archive-missing
pattern (the source files are gitignored).
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ingest_algorithms as ing  # noqa: E402

MANIFEST = json.loads(
    (REPO_ROOT / "data_sources" / "manifest.json").read_text(encoding="utf-8")
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

CITATION = (
    "TheAlgorithms and contributors. TheAlgorithms/Python. MIT License. "
    "https://github.com/TheAlgorithms/Python "
    "(commit f5988cc09713315817df6a7e327e258013a94440)."
)

DERIVED_DIR = REPO_ROOT / "data_sources" / "derived" / "algorithms"
ARCHIVE_DIR = REPO_ROOT / "data_sources" / "archives" / "algorithms"


def _source() -> dict:
    return next(
        s for s in MANIFEST["sources"] if s["id"] == "git-thealgorithms-python"
    )


class ManifestPin(unittest.TestCase):
    def test_entry_is_fully_pinned(self) -> None:
        src = _source()
        self.assertEqual(src["access"], "git")
        self.assertEqual(
            src["git_commit"], "f5988cc09713315817df6a7e327e258013a94440"
        )
        self.assertTrue(_HEX64.match(src["files"][0]["sha256"]))
        self.assertEqual(src["attribution"], CITATION)

    def test_license_records_mit_as_found(self) -> None:
        self.assertIn("MIT", _source()["license"])
        self.assertIn("4395a1dc4bda1d6054c45b4d1230c709c7398e6d66f1d0aff4b22d95973bea56",
                      _source()["license"])

    def test_declined_sources_are_absent(self) -> None:
        ids = {s["id"] for s in MANIFEST["sources"]}
        self.assertNotIn("git-ibm-project-codenet", ids)
        self.assertNotIn("git-thuva4-algorithms", ids)


class DerivedAttribution(unittest.TestCase):
    def test_notice_carries_the_citation(self) -> None:
        text = (DERIVED_DIR / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("TheAlgorithms and contributors. TheAlgorithms/Python. MIT License.", text)
        self.assertIn("https://github.com/TheAlgorithms/Python", text)
        self.assertIn("f5988cc09713315817df6a7e327e258013a94440", text)

    def test_extract_carries_the_citation_and_eight_functions(self) -> None:
        doc = json.loads((DERIVED_DIR / "extract.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["attribution"], CITATION)
        self.assertEqual(doc["license"], "MIT")
        self.assertEqual(
            [fn["name"] for fn in doc["functions"]],
            [
                "greatest_common_divisor",
                "gcd_by_iterative",
                "factorial",
                "factorial_recursive",
                "double_factorial_recursive",
                "double_factorial_iterative",
                "binary_exp_recursive",
                "binary_exp_iterative",
            ],
        )
        self.assertEqual(
            doc["source_files"],
            [
                "maths/greatest_common_divisor.py",
                "maths/factorial.py",
                "maths/double_factorial.py",
                "maths/binary_exponentiation.py",
            ],
        )
        names = [fn["name"] for fn in doc["functions"]]
        self.assertNotIn("binary_exp_mod_recursive", names)
        self.assertNotIn("binary_exp_mod_iterative", names)

    def test_vendored_license_is_mit(self) -> None:
        text = (DERIVED_DIR / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("MIT License", text)
        self.assertIn("TheAlgorithms", text)


class Regeneration(unittest.TestCase):
    def test_extract_regenerates_when_archive_present(self) -> None:
        needed = (
            "greatest_common_divisor.py",
            "factorial.py",
            "double_factorial.py",
            "binary_exponentiation.py",
        )
        if not all((ARCHIVE_DIR / name).is_file() for name in needed):
            self.skipTest("pinned TheAlgorithms files not in archives/")
        fresh = ing.extract()
        committed = json.loads(
            (DERIVED_DIR / "extract.json").read_text(encoding="utf-8")
        )
        self.assertEqual(fresh, committed)


if __name__ == "__main__":
    unittest.main()
