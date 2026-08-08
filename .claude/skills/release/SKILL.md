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
.venv/Scripts/python.exe scripts/check_regeneration.py      # seed<->JSON coherence; must pass
.venv/Scripts/python.exe scripts/validate_nodes.py          # must pass
.venv/Scripts/python.exe scripts/match_signatures.py --write-report reports/signature_matches.json
.venv/Scripts/python.exe scripts/specialize.py     --write-report reports/specializations.json
.venv/Scripts/python.exe scripts/decompose.py      --write-report reports/decompositions.json
.venv/Scripts/python.exe scripts/measure_compression.py --write-report reports/compression.json
```

## 2. The document lifecycle (roadmap -> release notes -> next roadmap)

The version's roadmap is the release notes' starting point, and releasing
rotates the documents:

1. **Start from `docs/ROADMAP-vX.Y.md`.** For each planned item, determine
   its outcome from ANALYSIS.md / DISCOVERIES.md / commit history:
   *shipped* (with numbers), *partial* (what landed, what didn't), or
   *not started*.
2. **Write `docs/RELEASE-vX.Y.Z.md` from that triage.** Shipped and
   partial items become the release narrative — measured results, honest
   limits, plain language first. Add anything significant that shipped
   *outside* the roadmap. Completed BACKLOG items that shipped this cycle
   move INTO this doc's record (a "resolved this release" list).
3. **Create `docs/ROADMAP-v<next>.md`.** Migrate every not-started and
   unfinished-half item there; seed it with the newly queued direction.
   Nothing planned is silently dropped — it either ships (release doc),
   carries (next roadmap), or is deliberately parked (BACKLOG, with the
   reason).
4. **Prune `docs/BACKLOG.md`**: delete entries whose work shipped (they
   now live in the release doc); keep or migrate the rest; confirm new
   friction from the cycle is filed.
5. The old roadmap file stays in place as the historical plan-of-record —
   do not delete it; the release doc references it. **Mark it closed**:
   prepend a banner stating the version it closed at and where each item
   went (shipped -> release doc; carried -> next roadmap, by number), so
   the file itself answers "what happened to this plan?".

## 2b. The other living docs (each one, every release)

- **README.md** — corpus counts (nodes/disciplines/cross-discipline
  markers), any new headline demonstration, results table if the suite
  grew. The README leads with what a newcomer can run.
- **docs/DISCOVERIES.md** — confirm all findings since the last release
  are parked (grep recent commits for twin/discovery language).
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
