#!/usr/bin/env python3
"""Seed<->JSON coherence check: committed data must equal what committed
seeds regenerate.

The seed scripts are the authored source of truth and the nodes.json files
their deterministic output — but nothing enforced that invariant, and
hand-edits to JSON would drift silently until the next regeneration
clobbered them (data/statistics lived in exactly that state). This tool
makes coherence a checked invariant:

1. refuses to run if data/ has uncommitted changes (so it cannot destroy
   in-progress work);
2. runs every scripts/seed_*.py from the repo root (seeds are
   deterministic and byte-idempotent by house rule);
3. reports any resulting git diff under data/ as DRIFT and restores the
   committed state;
4. reports any data/<discipline>/ directory owned by NO seed script.

Run in the release skill's step 1 and after any corpus authoring.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def sh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True)


def main() -> int:
    dirty = sh("git", "status", "--porcelain", "--", "data").stdout.strip()
    if dirty:
        print("REFUSING: data/ has uncommitted changes; commit or stash "
              "before checking regeneration:\n" + dirty)
        return 2

    seeds = sorted((REPO / "scripts").glob("seed_*.py"))
    failures = []
    for seed in seeds:
        r = subprocess.run([sys.executable, str(seed)], cwd=REPO,
                           capture_output=True, text=True)
        if r.returncode != 0:
            failures.append((seed.name, r.stderr.strip()[-400:]))
            print(f"  SEED FAILED: {seed.name}")
    # Trusted appends are data, not seed Python. Apply them after every
    # seed so a WRITE that landed data/<corpus>/appends/ still regenerates
    # (docs/DESIGN-write-append.md).
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        from seed_appends import AppendError, apply_appends  # noqa: E402
        apply_appends(REPO / "data")
    except AppendError as exc:
        failures.append(("seed_appends", str(exc)[:400]))
        print(f"  APPEND FAILED: {exc}")
    diff = sh("git", "diff", "--stat", "--", "data").stdout.strip()
    drift = bool(diff)
    if drift:
        print("DRIFT: committed data differs from regenerated data:")
        print(diff)
        sh("git", "checkout", "--", "data")
        print("(committed state restored)")
    else:
        print(f"coherence OK: {len(seeds)} seeds regenerate committed data "
              f"byte-identically")

    owned = set()
    for seed in seeds:
        text = seed.read_text(encoding="utf-8", errors="replace")
        for d in (REPO / "data").iterdir():
            if d.is_dir() and (f'"{d.name}"' in text or f"'{d.name}'" in text
                               or f"/{d.name}/" in text
                               or f'"data/{d.name}' in text
                               or d.name in text):
                owned.add(d.name)
    orphans = [d.name for d in sorted((REPO / "data").iterdir())
               if d.is_dir() and d.name not in owned]
    if orphans:
        print(f"ORPHAN CORPORA (no owning seed script): {', '.join(orphans)}")

    return 1 if (drift or failures or orphans) else 0


if __name__ == "__main__":
    raise SystemExit(main())
