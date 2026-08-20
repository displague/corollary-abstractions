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
.venv/Scripts/python.exe scripts/check_report_regeneration.py  # reports/ ledgers regenerate; declared
                                                            # snapshots reported, not regenerated (v0.16)
.venv/Scripts/python.exe scripts/validate_nodes.py          # must pass
.venv/Scripts/python.exe scripts/match_signatures.py --write-report reports/signature_matches.json
.venv/Scripts/python.exe scripts/specialize.py     --write-report reports/specializations.json
.venv/Scripts/python.exe scripts/measure_compression.py --write-report reports/compression.json
.venv/Scripts/python.exe scripts/ingest_wold.py reach       # experiments/wold_reach.json; needs pinned WordNet archive
```

`ingest_wold.py reach` is not optional. v0.11's programming second
wave added six tokens and the committed reach ledger stayed at 840
until the full-suite gate; no slice-level run saw it
(TRIAGE-v0.11 §1.7). `run_reach()` **refuses** without the
gitignored WordNet archive (exit 2) so it cannot silently
undercount. Treat that refusal as **cannot verify**, not as a
skip: either fetch the pinned archive and re-run, or do not claim
the ledger was refreshed. A contributor without the archive must
not tag.

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

**Plan the suite from the measured cost, not from folklore.** Full
`unittest discover -s tests` on the v0.11.0 tip was **1,123 tests,
OK (skipped=3), 23,744s (6h35m)** — not “30+ minutes.” The cost
is concentrated: `test_write_stage.AcceptedCandidateTests.test_matcher_delta_is_measured_and_recorded`
alone ran 6+ minutes. A healthy run will look hung if you expect
half an hour. Two-tier is the honest gate: a named fast set per
slice, the full discover per tag, with the wall-clock written
down.

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
   **Mandatory design-direction gate — invoke exactly once before drafting the
   next roadmap.** Read and follow
   [`../forge-design-direction/SKILL.md`](../forge-design-direction/SKILL.md).
   This call satisfies the forge skill's release context; neither skill invokes
   the other again. It must produce or explicitly reaffirm a reviewed forward
   DESIGN document, or record that no outside direction survived grounding.
   If its isolated contexts or review cannot run, stop release rotation with a
   blocked gate: do not draft the next roadmap, write the blog, tag, or publish.

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
   without one. Format, voice, and the required last-section chain:
   [references/blog-posts.md](references/blog-posts.md). The notes are
   the record. The post is the argument a stranger can finish. Title it
   for the finding, not the version. Lead with the result that
   complicates the story; if the cycle produced a negative, that is the
   post. End looking forward to the next release *from the design the
   findings forced*, written before this post. Link it from the release
   notes' links row. Model:
   `docs/blog/the-world-outside-the-weights.md`.
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

### What to attach, and what not to

Two rules, and the second one exists because this section used to demand
work nobody did. v0.5.0 shipped four checkpoints and v0.6.0 shipped six;
**v0.7.0 through v0.11.0 shipped none at all** while the skill kept saying
"at minimum the demo checkpoint". Five silent no-ops is the drift this
skill warns about elsewhere, applied to itself.

**Rule 1 — upload only what a clone does not already have.** Committed
artifacts are distributed by git. `experiments/*.json` measurement ledgers
are tracked, so uploading them duplicates the repository and inflates the
release for nothing. Link them by path in the notes instead. Only
**gitignored** artifacts are candidates: `experiments/results/**/*.pt` is
the whole list today.

**Rule 2 — re-ship a checkpoint only when this cycle could have changed
it.** Before uploading, check whether the cycle touched anything a
checkpoint depends on:

```
git diff --name-only <previous-tag>..HEAD -- data/ experiments/
```

If no training data and no `experiments/*.py` changed, the existing
checkpoints are still exactly correct, and re-uploading identical bytes
under a new tag is noise that costs upload time and release size to say
nothing new.

When that is the case the notes **must say so explicitly** — which release
carries the still-valid checkpoints, that they remain accurate for this
version, and *why*, with the evidence that makes it checkable:

> **Assets.** No new checkpoint, and the existing ones are not re-shipped.
> `data/` and every `experiments/*.py` are byte-identical to `vA.B.C`
> (`git diff --name-only vA.B.C..vX.Y.Z -- data/ experiments/` lists no
> `.py`), so the checkpoints attached to **vN.N.N** remain accurate for
> this release. Measurement ledgers are committed in-repo at
> `experiments/*.json`.

Silence is the thing to avoid, not the absence of an upload. A release
with no assets and no sentence about assets leaves a reader unable to tell
"nothing changed" from "nobody looked".

**When you DO upload**, every asset carries its **story** in the notes'
Assets section — the claim it evidences, the before/after it belongs to,
and the command that exercises it. Verify the notes and the upload list
match one-to-one first:

```
gh release upload vX.Y.Z \
    experiments/results/solvex2_demo.pt#span-pointer-solvex2-treepos.pt
```

If a claimed result's checkpoint no longer exists **and this cycle's
claims rest on it**, retrain from the committed seed (repro commands in
README) rather than shipping nothing. Do not retrain a checkpoint that
belongs to an older cycle's claim merely to have something to attach.

## 5. Verify

- `gh release view vX.Y.Z` shows notes + assets.
- Fresh-clone sanity if time allows: the README quickstart commands run.

## Notes

- `gh` must be authenticated (`gh auth status`); the repo's remote is the
  release target.
- Never put licensed external data (experiments/data_real/) in assets.
- Release notes may quote docs/DISCOVERIES.md but should not duplicate
  it wholesale — link it.
