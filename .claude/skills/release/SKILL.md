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
.venv/Scripts/python.exe scripts/measure_compression.py --write-report reports/compression.json
```

At ingested scale (~12k nodes), **do not** rewrite
`reports/decompositions.json` as a release step. Live analysis is
the pin source (181k+ constituents; the committed file stays the
pre-scale ledger). TRIAGE-v0.11 §1.6 is the precedent. If a later
cycle needs a committed decompose report, it owes a summary-only
format and its own prediction — not a hundred-megabyte clobber.

**Do not tag while the complete-suite gate is PARTIAL.** Graph-
touching tests green during a slice is not “the suite is green.”
Re-run on the tip, or the notes must refuse that sentence and the
tag waits. v0.11's gate 7 is the precedent.

## 2. The document lifecycle (roadmap -> release notes -> next roadmap)

The version's roadmap is the release notes' starting point, and releasing
rotates the documents:

1. **Start from `docs/ROADMAP-vX.Y.md`.** For each planned item, determine
   its outcome from ANALYSIS.md / DISCOVERIES.md / commit history:
   *shipped* (with numbers), *partial* (what landed, what didn't), or
   *not started*.

   **Drift audit (part of this triage, every release):** the blogs,
   release notes, and closed roadmaps are the project's drift reminders.
   Re-read the *previous two* releases' notes and roadmaps — not just
   this cycle's — and ask explicitly: have any stated goals been lost
   through focus attrition or scope shifting rather than by decision?
   Anything found is named in the triage (carried or deliberately
   parked with the reason), never silently absent.

   **Product surfaces are goals.** A live prompt, a chat-shaped HTTP
   skin, a conversation a person can type into: if a prior roadmap's
   acceptance named them, they are in the audit. v0.8 item 1 asked for
   a live session with a text prompt; RELEASE-v0.8.0 said the system
   can now be driven; `scripts/harness.py` still prints a liveness
   list and exits. v0.9 called that an earned foundation. v0.11's
   first draft omitted the prompt. That is the shape this paragraph
   exists to catch — the same shape as the multi-corpus WRITE patch,
   on a surface instead of a corpus lane.

   **"Shipped" means the acceptance a newcomer can try.** If the
   acceptance was “a person types and sees ask or refuse,” libraries
   plus a recorded session are not that acceptance. Call them
   libraries. Leave the surface open or park it. Do not let a later
   roadmap inherit “driven” as a fact.

   **Every carried lane names its dependant, or is parked.** A "carried"
   item is not yet a plan — it is a deferral, and deferrals compound
   quietly. So for each item carried into the next roadmap, write down
   which of that roadmap's HEADLINE items depends on it. If one does, the
   lane is not a lane: it is a **prerequisite**, and it is ordered BEFORE
   its dependant rather than listed under carried-open work. If none
   does, park it in BACKLOG with the reason. An item carried a second
   time with no named dependant is the shape this rule exists to catch.
   (v0.10 earned it: the multi-corpus WRITE patch rode two cycles as the
   least prominent entry in a carried-lanes list, then turned out to
   block the cycle's headline authoring item — discovered by running the
   gate, not by reading the roadmap. See docs/TRIAGE-v0.10.md §2.)
2. **Write `docs/RELEASE-vX.Y.Z.md` from that triage**, using the
   section outline below. The governing rule: every claimed improvement
   is written as **Before → Now → Demonstrate** — what was the case
   before, what is the case now, and a runnable command or readable
   ledger line that shows the difference. Plain language first; numbers
   attached; no improvement without its demonstration.

   ### Release-notes section outline (accumulated from v0.1–v0.4)

   1. **Title + headline** — one line naming the cycle's character.
   2. **Links row** — previous release, closed roadmap, next roadmap,
      DISCOVERIES.
   3. **The headline finding** — the cycle's single most important
      result, as Before/Now/Demonstrate, with its table if it has one.
   4. **Roadmap triage** — shipped (with numbers), shipped-as-negative
      (falsifications and retractions are first-class results), carried.
   5. **What changed, per area** — each entry Before → Now →
      Demonstrate. A demonstration is a command the reader can run
      (quote it) or a specific line in a committed ledger (name it).
   6. **Discoveries of the cycle** — quote two or three from
      DISCOVERIES.md; link, don't duplicate.
   7. **Resolved from BACKLOG** — the pruned entries' record.
   8. **Honest limits carried forward** — including anything the cycle
      falsified about its own prior claims.
   9. **Assets** — every attached checkpoint carries its **story**: the
      claim it evidences, the before/after it belongs to, and the
      command that exercises it. An asset without a story does not
      ship. Note anything seed-reproducible-only.
   10. **Reproduce** — copy-paste commands from a fresh clone.
3. **Create `docs/ROADMAP-v<next>.md`.** Migrate every not-started and
   unfinished-half item there; seed it with the newly queued direction.
   Nothing planned is silently dropped — it either ships (release doc),
   carries (next roadmap), or is deliberately parked (BACKLOG, with the
   reason).

   **The forward-looking design item:** every next-roadmap strives to
   contain at least one strong, forward-looking design — inspired by
   what the previous releases proved or falsified — that leads into the
   next release's goals rather than only extending the current ones.
   It should be a direction the released evidence now makes possible or
   necessary, written as a design (what it unlocks, what it rests on),
   not just a task line. The strongest source is usually something the
   cycle produced BY ACCIDENT and nobody designed for — an unpredicted
   measurement, a prediction that missed in an interesting direction, a
   behaviour a review surfaced. Prefer one of those over an extrapolation
   of the current plan, and say what would falsify it.

   **Guard pins that moved get a decision, not a re-pin.** If a pinned
   guard has been re-measured and re-pinned against its own direction in
   more than one slice, triage is where that stops: either retire the pin
   with a written rationale, or register the drift as a scoring change
   owing its own prediction and experiment. Bring it to the maintainer as
   a QUESTION with the history in a table (pin as written, then each
   slice's measured value, and whether the load-bearing guard alongside
   it ever weakened). Re-pinning a third time inside a release is how a
   guard becomes a ratchet.
4. **Write the release's blog post in `docs/blog/`** — every release has
   had one since v0.5, and the skill did not say so until v0.10 shipped
   without one. It is not a summary of the release notes: the notes are
   the record, the post is the ARGUMENT — what the cycle believed going
   in, what actually happened, and what the project now owes. Title it
   for the finding, not the version (`how-much-of-it-fits.md`,
   `when-the-honest-baseline-wins.md`). Lead with the result that
   complicates the story rather than the one that flatters it; if the
   cycle produced a negative, that is the post. Link it from the release
   notes' links row.
5. **Prune `docs/BACKLOG.md`**: delete entries whose work shipped (they
   now live in the release doc); keep or migrate the rest; confirm new
   friction from the cycle is filed.
6. The old roadmap file stays in place as the historical plan-of-record —
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
models (rename assets to be self-describing). **Every asset must have
its story in the release notes' Assets section** (claim, before/after,
exercising command) — verify the notes and the upload list match
one-to-one before uploading:

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
