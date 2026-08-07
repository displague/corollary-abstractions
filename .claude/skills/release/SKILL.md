---
name: release
description: Cut a versioned release of corollary-abstractions — refresh ledgers and docs, write release notes, tag, create a GitHub release with gh, and attach model checkpoints as assets. Use when the user asks to release, tag a version, or publish.
---

# Release process

Releases are the project's public checkpoints. A release is not just a tag:
it refreshes every generated ledger, updates the living docs, and publishes
model artifacts. Follow every step; skipping doc refresh is how v0.2.0
shipped without its notes file.

## 0. Preconditions

- Working trees clean, `main` == `origin/main` (push first if not).
- Decide the version `vX.Y.Z` (minor bump for new capabilities/corpora,
  patch for fixes). Check `git tag -l` for the last version.

## 1. Refresh generated state (all from repo root, PYTHONIOENCODING=utf-8)

```
.venv/Scripts/python.exe scripts/validate_nodes.py          # must pass
.venv/Scripts/python.exe scripts/match_signatures.py --write-report reports/signature_matches.json
.venv/Scripts/python.exe scripts/specialize.py     --write-report reports/specializations.json
.venv/Scripts/python.exe scripts/decompose.py      --write-report reports/decompositions.json
.venv/Scripts/python.exe scripts/measure_compression.py --write-report reports/compression.json
```

## 2. Update the living docs (each one, every release)

- **README.md** — corpus counts (nodes/disciplines/cross-discipline
  markers), any new headline demonstration, results table if the suite
  grew. The README leads with what a newcomer can run.
- **docs/RELEASE-vX.Y.Z.md** — NEW file, the release notes: what changed
  since the previous release doc, measured results with numbers, honest
  limits carried forward. Plain language first; skeletons second.
- **docs/DISCOVERIES.md** — confirm all findings since the last release
  are parked (grep recent commits for twin/discovery language).
- **docs/BACKLOG.md** — prune items that shipped; confirm new friction is
  filed.
- **experiments/ANALYSIS.md** — confirm every experiment since last
  release is recorded with its numbers.

## 3. Commit, tag, push

Commit doc updates (why-rich message per house style), then:

```
git tag -a vX.Y.Z -m "<one-paragraph summary>"
git push && git push origin vX.Y.Z
```

## 4. GitHub release with model assets

```
gh release create vX.Y.Z --title "vX.Y.Z — <headline>" \
    --notes-file docs/RELEASE-vX.Y.Z.md
```

Then attach model checkpoints — the trained artifacts the release's
claims rest on. At minimum the demo checkpoint; add any new headline
models (rename assets to be self-describing):

```
gh release upload vX.Y.Z \
    experiments/results/solvex2_demo.pt#span-pointer-solvex2-treepos.pt
```

Checkpoints are gitignored precisely so releases are their distribution
channel. If a claimed result's checkpoint no longer exists, retrain it
from the committed seed (the repro commands are in README) rather than
shipping nothing — assets make results reproducible without a GPU.

## 5. Verify

- `gh release view vX.Y.Z` shows notes + assets.
- Fresh-clone sanity if time allows: the README quickstart commands run.

## Notes

- `gh` must be authenticated (`gh auth status`); the repo's remote is the
  release target.
- Never put licensed external data (experiments/data_real/) in assets.
- Release notes may quote docs/DISCOVERIES.md but should not duplicate
  it wholesale — link it.
