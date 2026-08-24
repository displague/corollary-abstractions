#!/usr/bin/env python3
"""Seed<->JSON coherence check: committed data must equal what committed
seeds regenerate.

The seed scripts are the authored source of truth and the nodes.json files
their deterministic output — but nothing enforced that invariant, and
hand-edits to JSON would drift silently until the next regeneration
clobbered them (data/statistics lived in exactly that state). This tool
makes coherence a checked invariant:

1. refuses to run if a corpus root has uncommitted changes (so it cannot
   destroy in-progress work);
2. runs every scripts/seed_*.py from the repo root (seeds are
   deterministic and byte-idempotent by house rule);
3. reports any resulting git diff under a corpus root as DRIFT and
   restores the committed state;
4. reports any <root>/<discipline>/ directory owned by NO seed script.

Two corpus roots, both checked identically:

- `data/` — the merged analysis graph. Every ledger, every pinned guard,
  and `validate_nodes.py`'s default run are computed over exactly this.
- `data_holdout/` — quarantined corpora (v0.12 held-out sources). Committed,
  versioned, schema-checkable and byte-reproducible like any other corpus,
  but deliberately invisible to the merged graph: a holdout that joins the
  graph every pin is computed over is not held out. `decompose.load_trees`
  takes its root as a parameter, so a measurement merges the overlay in
  memory instead (see scripts/seed_minif2f.py for the measured reason).

Regeneration coherence is the one guarantee a holdout must NOT lose — it
is the whole claim that the sample was drawn mechanically rather than
chosen — so it is checked here rather than left to the measurement.

Run in the release skill's step 1 and after any corpus authoring.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Corpus roots, in report order. `data_holdout/` may legitimately not exist
# in a clone that has authored no holdout yet; absent roots are skipped, not
# an error.
CORPUS_ROOTS = ("data", "data_holdout")


def sh(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True)


def present_roots() -> list[str]:
    return [r for r in CORPUS_ROOTS if (REPO / r).is_dir()]


def main() -> int:
    roots = present_roots()
    dirty = sh("git", "status", "--porcelain", "--", *roots).stdout.strip()
    if dirty:
        print(f"REFUSING: {'/, '.join(roots)}/ has uncommitted changes; "
              "commit or stash before checking regeneration:\n" + dirty)
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
    roots = present_roots()
    diff = sh("git", "diff", "--stat", "--", *roots).stdout.strip()
    drift = bool(diff)
    if drift:
        print("DRIFT: committed data differs from regenerated data:")
        print(diff)
        sh("git", "checkout", "--", *roots)
        print("(committed state restored)")
    else:
        print(f"coherence OK: {len(seeds)} seeds regenerate committed data "
              f"byte-identically across {'/, '.join(roots)}/")

    # Hand-authored preregistration artifacts, not seeded corpora: their
    # regeneration discipline lives in their own digest pins and tests
    # (experiments/realization_prereg.json, experiments/foreign_voice_prereg
    # .json), not in a seed script. Registered here explicitly because
    # data/realization was previously escaping the orphan check only by a
    # name-coincidence substring match in an unrelated seed -- an exclusion
    # that exists by accident is an exclusion nobody decided.
    hand_authored_prereg = {"realization", "foreign_voice"}

    orphans: list[str] = []
    for root in roots:
        owned = set(hand_authored_prereg) if root == "data" else set()
        for seed in seeds:
            text = seed.read_text(encoding="utf-8", errors="replace")
            for d in (REPO / root).iterdir():
                if d.is_dir() and (f'"{d.name}"' in text or f"'{d.name}'" in text
                                   or f"/{d.name}/" in text
                                   or f'"{root}/{d.name}' in text
                                   or d.name in text):
                    owned.add(d.name)
        orphans.extend(f"{root}/{d.name}"
                       for d in sorted((REPO / root).iterdir())
                       if d.is_dir() and d.name not in owned)
    if orphans:
        print(f"ORPHAN CORPORA (no owning seed script): {', '.join(orphans)}")

    return 1 if (drift or failures or orphans) else 0


if __name__ == "__main__":
    raise SystemExit(main())
