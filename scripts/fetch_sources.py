#!/usr/bin/env python3
"""Fetch and verify external corpus sources against a pinned manifest.

External corpora are the v0.9 ingestion inputs. They stay OUT of the repo
(gitignored under ``data_sources/archives/``); reproducibility comes from
``data_sources/manifest.json``, which pins each source's URL and SHA-256. This
script is the workflow the roadmap's "digest-pinned source snapshot" rule names:
fetch a URL, verify its bytes hash to the recorded SHA, and refuse anything that
does not match — the same discipline the depth/proof manifests already use.

Never prints secrets. A Hugging Face token is read from ``.env`` (gitignored)
into the environment for the ``hf`` CLI only; it is never logged.

Usage (run from repo root, PYTHONIOENCODING=utf-8 on Windows):

    python scripts/fetch_sources.py --list
    python scripts/fetch_sources.py --verify
    python scripts/fetch_sources.py --adopt ~/Downloads      # copy already-downloaded files in by SHA
    python scripts/fetch_sources.py --fetch                  # download all missing direct sources
    python scripts/fetch_sources.py --fetch wordnet-2025-json
    python scripts/fetch_sources.py --fetch hf-proofcheck-prooflang   # via the hf CLI

Exit status is non-zero if any requested action left a source unverified.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data_sources" / "manifest.json"
_CHUNK = 1 << 20


def _load_manifest() -> dict:
    import json

    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _archive_dir(manifest: dict) -> Path:
    d = REPO_ROOT / manifest.get("archive_dir", "data_sources/archives")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(_CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_env_token() -> str | None:
    """Read HF_TOKEN from .env into the environment WITHOUT printing it."""
    if os.environ.get("HF_TOKEN"):
        return os.environ["HF_TOKEN"]
    env = REPO_ROOT / ".env"
    if not env.is_file():
        return None
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("HF_TOKEN=") and "=" in line:
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            if token:
                os.environ["HF_TOKEN"] = token
                return token
    return None


def _verify_one(archive_dir: Path, src: dict) -> tuple[str, str]:
    """Return (status, detail) for a direct source's local file."""
    filename = src.get("filename")
    if not filename:
        return "SKIP", "no filename (non-direct source)"
    path = archive_dir / filename
    if not path.is_file():
        try:
            shown = str(path.relative_to(REPO_ROOT))
        except ValueError:
            shown = str(path)
        return "MISSING", shown
    expected = src.get("sha256")
    if not expected:
        return "UNPINNED", f"sha256 not pinned; on-disk {_sha256(path)}"
    actual = _sha256(path)
    if actual == expected:
        return "OK", f"{src['size_bytes']} bytes, sha ok"
    return "MISMATCH", f"expected {expected[:12]}.. got {actual[:12]}.."


def _download(url: str, dest: Path, expected_sha: str | None) -> tuple[str, str]:
    """Download to a temp file, verify SHA, then atomically move into place."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(dest.parent), suffix=".part")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as out:
            req = urllib.request.Request(url, headers={"User-Agent": "corollary-fetch/1"})
            with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 (pinned URLs)
                shutil.copyfileobj(resp, out, _CHUNK)
        actual = _sha256(tmp)
        if expected_sha and actual != expected_sha:
            return "MISMATCH", f"expected {expected_sha[:12]}.. got {actual[:12]}.. (not saved)"
        os.replace(tmp, dest)
        if not expected_sha:
            return "UNPINNED", f"saved; RECORD sha256={actual}"
        return "OK", f"downloaded and verified ({actual[:12]}..)"
    finally:
        if tmp.exists():
            tmp.unlink()


def _fetch_hf(src: dict) -> tuple[str, str]:
    repo = src.get("hf_repo")
    if not repo:
        return "ERROR", "no hf_repo"
    token = _load_env_token()
    if src.get("access") == "hf-dataset-gated" and not token:
        return "GATED", f"needs HF_TOKEN + accepted form on {src['url']} — fetch manually"
    if shutil.which("hf") is None:
        return "ERROR", "hf CLI not found"
    cmd = ["hf", "download", f"hf://datasets/{repo}", "--repo-type", "dataset"]
    try:
        subprocess.run(cmd, check=True, cwd=str(REPO_ROOT))
    except subprocess.CalledProcessError as exc:
        hint = " (gated? accept the form on the dataset page)" if src.get("access") == "hf-dataset-gated" else ""
        return "ERROR", f"hf download failed ({exc.returncode}){hint}"
    return "OK", "hf download complete; pin per-file SHAs before ingest"


def cmd_list(manifest: dict) -> int:
    for src in manifest["sources"]:
        pinned = "pinned" if src.get("sha256") else src.get("access", "?")
        print(f"  {src['id']:<30} {src.get('group',''):<18} {pinned:<10} {src['url']}")
    return 0


def cmd_verify(manifest: dict) -> int:
    archive_dir = _archive_dir(manifest)
    bad = 0
    for src in manifest["sources"]:
        if src.get("access") != "direct":
            continue
        status, detail = _verify_one(archive_dir, src)
        print(f"  [{status:<9}] {src['id']:<30} {detail}")
        if status in ("MISMATCH",):
            bad += 1
    return 1 if bad else 0


def cmd_adopt(manifest: dict, source_dir: Path) -> int:
    """Copy already-downloaded files from source_dir into the archive dir by SHA."""
    archive_dir = _archive_dir(manifest)
    # Index candidate files in source_dir by SHA (only sizes present in manifest,
    # to avoid hashing an entire Downloads folder).
    wanted_sizes = {s["size_bytes"] for s in manifest["sources"] if s.get("size_bytes")}
    by_sha: dict[str, Path] = {}
    for path in source_dir.iterdir():
        if path.is_file() and path.stat().st_size in wanted_sizes:
            by_sha.setdefault(_sha256(path), path)
    adopted = missing = 0
    for src in manifest["sources"]:
        if src.get("access") != "direct":
            continue
        dest = archive_dir / src["filename"]
        if dest.is_file() and _sha256(dest) == src.get("sha256"):
            print(f"  [HAVE     ] {src['id']}")
            continue
        match = by_sha.get(src.get("sha256"))
        if match is None:
            print(f"  [MISSING  ] {src['id']} (no local file with sha {src.get('sha256','?')[:12]}..)")
            missing += 1
            continue
        shutil.copy2(match, dest)
        print(f"  [ADOPTED  ] {src['id']} <- {match.name}")
        adopted += 1
    print(f"adopted {adopted}, missing {missing}")
    return 1 if missing else 0


def cmd_fetch(manifest: dict, ids: list[str]) -> int:
    archive_dir = _archive_dir(manifest)
    selected = [s for s in manifest["sources"] if not ids or s["id"] in ids]
    if ids:
        known = {s["id"] for s in manifest["sources"]}
        for unknown in set(ids) - known:
            print(f"  [ERROR    ] unknown id {unknown!r}")
    bad = 0
    for src in selected:
        access = src.get("access")
        if access == "direct":
            dest = archive_dir / src["filename"]
            if dest.is_file() and _sha256(dest) == src.get("sha256"):
                print(f"  [HAVE     ] {src['id']}")
                continue
            status, detail = _download(src["url"], dest, src.get("sha256"))
            print(f"  [{status:<9}] {src['id']} {detail}")
            if status == "MISMATCH":
                bad += 1
        elif access in ("hf-dataset", "hf-dataset-gated"):
            status, detail = _fetch_hf(src)
            print(f"  [{status:<9}] {src['id']} {detail}")
            if status == "ERROR":
                bad += 1
        elif access == "git":
            print(f"  [MANUAL   ] {src['id']}: git clone {src['url']} (pin the commit SHA)")
        else:
            print(f"  [SKIP     ] {src['id']} (access={access})")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list manifest sources")
    parser.add_argument("--verify", action="store_true", help="verify local archives against pinned SHAs")
    parser.add_argument("--adopt", metavar="DIR", help="copy already-downloaded files from DIR into the archive dir by SHA")
    parser.add_argument("--fetch", nargs="*", metavar="ID", help="download sources (all, or the given ids)")
    args = parser.parse_args(argv)

    manifest = _load_manifest()
    if args.list:
        return cmd_list(manifest)
    if args.verify:
        return cmd_verify(manifest)
    if args.adopt is not None:
        return cmd_adopt(manifest, Path(args.adopt).expanduser())
    if args.fetch is not None:
        return cmd_fetch(manifest, args.fetch)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
