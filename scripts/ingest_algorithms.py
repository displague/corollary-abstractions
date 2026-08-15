#!/usr/bin/env python3
"""Deterministic extract of the pinned TheAlgorithms/Python maths files.

Design: docs/DESIGN-programming-discipline.md (first wave, one file) and
docs/DESIGN-programming-second-wave.md (this wave, four files).

TheAlgorithms/Python is the chosen source: MIT, Python, and small enough
that a per-file pin reaches the acceptance bar. CodeNet was declined
(submission terms); thuva4/Algorithms was declined as the primary source
(TypeScript; the live verifier backend is python-tests).

Two stages, mirroring ingest_minif2f.py / ingest_wold.py:

  extract  pinned source files (SHA-256 verified against
           data_sources/manifest.json; gitignored under
           data_sources/archives/algorithms/)
           -> committed data_sources/derived/algorithms/extract.json
  check    committed extract.json is internally complete (no archive)

The GCD source file still contains a Python-2 ``except A, B`` in
``main()``, so the extract NEVER ast-parses a whole file. It slices
named function definitions by their ``def`` lines. That is a declared
transform, not a guess.

The two modular exponentiation functions in binary_exponentiation.py
are declined this slice (design §3) and are not sliced.

Determinism: source order, no timestamps, LF-only bytes via write_bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "data_sources" / "manifest.json"
ARCHIVE_DIR = REPO_ROOT / "data_sources" / "archives" / "algorithms"
EXTRACT_DIR = REPO_ROOT / "data_sources" / "derived" / "algorithms"
EXTRACT_PATH = EXTRACT_DIR / "extract.json"

MANIFEST_SOURCE_ID = "git-thealgorithms-python"

CITATION = (
    "TheAlgorithms and contributors. TheAlgorithms/Python. MIT License. "
    "https://github.com/TheAlgorithms/Python "
    "(commit f5988cc09713315817df6a7e327e258013a94440)."
)

# Per-file slice markers: inclusive start, exclusive end. Order is
# source-file order, then source order inside the file.
FILE_SLICES: tuple[dict, ...] = (
    {
        "filename": "greatest_common_divisor.py",
        "source_file": "maths/greatest_common_divisor.py",
        "functions": (
            ("greatest_common_divisor", "def greatest_common_divisor", "def gcd_by_iterative"),
            ("gcd_by_iterative", "def gcd_by_iterative", "def main"),
        ),
    },
    {
        "filename": "factorial.py",
        "source_file": "maths/factorial.py",
        "functions": (
            ("factorial", "def factorial(", "def factorial_recursive"),
            ("factorial_recursive", "def factorial_recursive", "if __name__"),
        ),
    },
    {
        "filename": "double_factorial.py",
        "source_file": "maths/double_factorial.py",
        "functions": (
            ("double_factorial_recursive", "def double_factorial_recursive",
             "def double_factorial_iterative"),
            ("double_factorial_iterative", "def double_factorial_iterative",
             "if __name__"),
        ),
    },
    {
        "filename": "binary_exponentiation.py",
        "source_file": "maths/binary_exponentiation.py",
        "functions": (
            ("binary_exp_recursive", "def binary_exp_recursive",
             "def binary_exp_iterative"),
            ("binary_exp_iterative", "def binary_exp_iterative",
             "def binary_exp_mod_recursive"),
        ),
    },
)

EXPECTED_FUNCTION_NAMES = [
    name
    for spec in FILE_SLICES
    for name, _start, _end in spec["functions"]
]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def serialize(doc: dict) -> bytes:
    return (
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def write_json(path: Path, doc: dict) -> None:
    path.write_bytes(serialize(doc))


def _load_manifest_source() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for src in manifest["sources"]:
        if src["id"] == MANIFEST_SOURCE_ID:
            return src
    raise KeyError(f"manifest source `{MANIFEST_SOURCE_ID}` not found")


def _verified_file(filename: str, expected_sha: str) -> bytes:
    path = ARCHIVE_DIR / filename
    if not path.is_file():
        raise SystemExit(
            f"MISSING: {path} not present. Fetch the pinned source first:\n"
            f"  see data_sources/manifest.json entry `{MANIFEST_SOURCE_ID}`"
        )
    data = path.read_bytes()
    digest = _sha256_bytes(data)
    if digest != expected_sha:
        raise SystemExit(
            f"SHA MISMATCH for {filename}:\n"
            f"  expected {expected_sha}\n  got      {digest}\n"
            "Refusing to work from unpinned bytes."
        )
    return data


def _slice_function(source: str, start_marker: str, end_marker: str) -> str:
    start = source.find(start_marker)
    if start < 0:
        raise SystemExit(f"extract: start marker not found: {start_marker!r}")
    end = source.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"extract: end marker not found: {end_marker!r}")
    body = source[start:end].strip()
    if not body.startswith("def "):
        raise SystemExit(f"extract: slice did not start at a def: {body[:40]!r}")
    return body + "\n"


def extract() -> dict:
    src = _load_manifest_source()
    files = {entry["filename"]: entry for entry in src["files"]}
    lic_meta = files["LICENSE.md"]
    lic_bytes = _verified_file(lic_meta["filename"], lic_meta["sha256"])
    license_text = lic_bytes.decode("utf-8")
    if "MIT License" not in license_text:
        raise SystemExit(
            "LICENSE.md does not contain 'MIT License'; refusing to extract"
        )
    functions = []
    source_files = []
    for spec in FILE_SLICES:
        meta = files[spec["filename"]]
        raw = _verified_file(meta["filename"], meta["sha256"])
        source = raw.decode("utf-8")
        source_files.append(spec["source_file"])
        for name, start, end in spec["functions"]:
            functions.append(
                {
                    "name": name,
                    "source_file": spec["source_file"],
                    "text": _slice_function(source, start, end),
                }
            )
    return {
        "source_id": MANIFEST_SOURCE_ID,
        "git_commit": src["git_commit"],
        "license": "MIT",
        "attribution": CITATION,
        "source_files": source_files,
        "functions": functions,
    }


def check_extract(doc: dict) -> None:
    if doc.get("source_id") != MANIFEST_SOURCE_ID:
        raise SystemExit("extract source_id drifted")
    if doc.get("attribution") != CITATION:
        raise SystemExit("extract attribution drifted from the citation of record")
    names = [fn["name"] for fn in doc.get("functions", [])]
    if names != EXPECTED_FUNCTION_NAMES:
        raise SystemExit(f"extract functions drifted: {names}")
    if "binary_exp_mod_recursive" in names or "binary_exp_mod_iterative" in names:
        raise SystemExit("extract took the declined modular pair")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("extract", "check"))
    args = parser.parse_args(argv)
    if args.stage == "extract":
        EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        doc = extract()
        write_json(EXTRACT_PATH, doc)
        license_src = ARCHIVE_DIR / "LICENSE.md"
        (EXTRACT_DIR / "LICENSE").write_bytes(license_src.read_bytes())
        print(f"wrote {EXTRACT_PATH.relative_to(REPO_ROOT).as_posix()}")
        return 0
    if not EXTRACT_PATH.is_file():
        raise SystemExit(f"missing committed extract: {EXTRACT_PATH}")
    check_extract(json.loads(EXTRACT_PATH.read_text(encoding="utf-8")))
    print("extract check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
