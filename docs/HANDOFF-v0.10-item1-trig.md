# Handoff — v0.10 item 1 (first grammar head: trigonometry)

Written at the pause point after v0.9.0 shipped. This is the working note for
whoever finishes v0.10 item 1 (possibly a fresh session). It records what landed,
the two ways forward the author was asked to choose between (option 1 = finish &
merge; option 2 = reconsider the footprint), and how to continue toward the rest
of v0.10.

## What landed

**v0.9.0 is released** — `main` at `7007d4f`, tag `v0.9.0`, GitHub release live,
blog + roadmap rotation done, 848-test suite green. `main` is clean and untouched
by the work below.

**The trig head is on branch `feature/v010-trig-head` (NOT merged)**, three commits
on top of `7007d4f`:
- `c1c8202` — trigonometry corpus + SIN/COS/TAN classifier support + coverage
  re-measurement + ledger recompute.
- `fc6949d` — adversarial-review fixes (inverse-trig superscript FP; equivalent-form nit).
- this handoff.

What the branch contains and proved:
- `scripts/seed_trigonometry.py` → `data/trigonometry/nodes.json`: **8 canonical
  identities** (Pythagorean, tangent def, sine/cosine angle-sum + double-angle
  special cases with a real `special_case_of`/`generalizes` pair, odd/even). Corpus
  **221 → 229 nodes, 22 → 23 disciplines**. Matcher parses every template
  (`parse_problems: 0`, `slot_schema_gaps: 0`); `check_regeneration` holds (15 seeds,
  no orphan); `validate_nodes` passes (229 nodes).
- `scripts/grammar_coverage.py`: forward `sin`/`cos`/`tan` moved from the trig
  BLOCKER into `_SUPPORTED_FUNCS`; inverse/reciprocal/hyperbolic trig stay gaps; a
  `list_or_iteration` blocker (`\[`) rejects list literals and `f^[n]` iteration.
- **Coverage delta (the head's justification), full-statement:**
  | source | before | after |
  |---|---|---|
  | miniF2F | 145 = 29.7% | 147 = 30.1% |
  | Lean-workbook | 19,077 = 64.1% | 19,532 = 65.7% |
  | Goedel-Pset-v1 (1.73M) | 567,429 = 32.8% | **606,937 = 35.0%** |
  Goedel-Pset audit clean (`foreign_glyphs=0, carrier_residual=0`).
- **Independent review passed**: 8 identities mathematically correct, delta honest
  (LOST=0), hyperbolics correctly blocked; the 2 findings it raised are fixed.
- **Honest null:** the trig nodes form NO new cross-discipline twins (SIN/COS heads
  distinguish `sin²+cos²=1` from `a²+b²=c²`); `group_counts` unchanged.

**Why it is not merged.** Growing the corpus 221→229 shifted ~20 deliberately
pinned numbers in the groundedness regression guards. This is **snapshot drift,
not a broken invariant** — every structural invariant still holds (same-corpus ⊆
conservative, `external_lower ≤ external`, the partition identities, multi-owner →
external). But those pins are the **registered v0.7 predictions GC4/GC5**, and the
test file's docstring says any movement "needs its own registered prediction." The
author paused rather than rewrite registered-prediction pins autonomously.

## Option 1 — finish & merge

Mechanical, low-risk. The new corpus is correct (reviewed); update each pinned
snapshot to its regenerated value, record the movement as the registered
acknowledgment the docstring asks for, get the suite green, merge.

### 1a. Update the pinned assertions (old → new)

`tests/test_decompose_channels.py`:
- `test_aggregate_totals_unchanged`: `mean_groundedness` 0.770 → **0.774**;
  `sum grounded_exact` 440 → **469**; `sum grounded_via_pattern` 75 → **87**;
  `count with constituents` 193 → **201**.
- `test_external_precedence_is_load_bearing_not_a_tie_break`: `len(exact)`
  440 → **469**; `len(multi)` 190 → **196**.
- `test_absorption_cross_discipline_share_does_not_beat_the_baseline`:
  `(a_best, a_all, len(absorbed))` (62, 36, 75) → **(74, 48, 87)**.
- `test_same_corpus_dominance_is_a_lower_bound`: generous 5 → **6**;
  conservative 12 → **13** (invariant `generous ⊆ conservative` still holds).
- `test_conservative_rollup_brackets_the_external_share`: external mean
  0.535 → **0.523**; `external_lower` 0.246 → **0.24**; exact-channel-external
  352 → **359**; least-independent-external 162 → **163**.
- `test_shipped_channel_scores_sum_within_rounding`: off-by-rounding count
  3 → **5** (and "219 shipped rows"/"considered" → **227** in the docstring/msg).
- `test_recursive_channel_is_reachable_at_min_family_one`: run it; update the
  pinned min-family-1 reachability figure to the reported value (it is a snapshot,
  not an invariant — recursive stays structurally empty at defaults).

`tests/test_matcher_mirror.py:70`: `nodes_analyzed` 221 → **229**. `group_counts`
is UNCHANGED (`{shape:30, typed:31, family:30, aliased:32, mirror:5}`) — the null.

`tests/test_verified_by.py:251` and `tests/test_proof_correspondence.py`
(regenerable-from-digest test): the validator prints "**229** statement nodes"
now, not 221 — update the substring/expected. Confirm the correspondence report's
merged-graph digest matches the regenerated `reports/proof_correspondence.json`
(trig nodes carry no `verified_by`, so they add no correspondence rows; the change
is the node-count/digest only).

> Method for any value you are unsure of: run the single failing test; unittest
> prints expected-vs-actual. The regenerated `reports/*.json` on this branch are
> the source of truth (already committed).

### 1b. Record the registered-prediction acknowledgment

Add a short block to `tests/test_decompose_channels.py`'s module docstring (or a
DISCOVERIES.md entry) stating: *v0.10 added `data/trigonometry` (8 atomic
identities); the groundedness aggregates moved by a CORPUS change, not a scoring
change — mean 0.770→0.774, exact 440→469, pattern 75→87, constituents 193→201.
The movement is same-corpus-dominated (the double-angle nodes grounded by their
angle-sum generalizations); no external/prior_corpus channel gained on the
provability regression case, and every GC5 partition identity still holds.* This
is what keeps GC4/GC5 meaningful for the next scoring change.

### 1c. Regenerate, gate, merge

```
PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/check_regeneration.py
… scripts/validate_nodes.py
… scripts/match_signatures.py --write-report reports/signature_matches.json
… scripts/specialize.py       --write-report reports/specializations.json
… scripts/decompose.py        --write-report reports/decompositions.json
… scripts/measure_compression.py --write-report reports/compression.json
… scripts/proof_correspondence.py --write-report reports/proof_correspondence.json
… -m unittest discover -s tests -p "test_*.py"          # must be green
```
Then ff-merge `feature/v010-trig-head` → `main` from the main checkout, push, sync
`loop`. Update `README` corpus counts 221→229 / 22→23. (No release; this is one
v0.10 slice.) The ANALYSIS §"v0.10 item 1" section is already written on the branch.

## Option 2 — reconsider the footprint

The finding worth weighing: **adding any discipline to the main corpus perturbs
the groundedness regression guards.** Three concrete alternatives, if you would
rather not pay that each head:

1. **Accept it as the cost of growth (recommended).** The guards are supposed to
   move when the corpus legitimately grows; option 1's acknowledgment is exactly
   the mechanism. Every future head pays a small, documented pin update. Simplest
   and most honest.
2. **Pick a deeper first head instead of trig.** Trig is only ~2–5% of coverage.
   The big remainder heads are relational/predicate (22% of Goedel-Pset), quantifier
   (~19%), and the function slot (~14%). A deeper head moves the number more per
   unit of corpus-guard churn — but each is a semantically harder grammar change,
   and each still adds exemplar nodes and moves the same guards. Trig's virtue was
   proving the "author head → measure delta" loop end-to-end cleanly; that loop is
   now proven, so a deeper head is the natural next.
3. **Separate the coverage-instrument grammar from the groundedness corpus.** Only
   if the guard churn becomes intolerable: let the classifier's supported-head set
   be justified by a *dedicated* exemplar corpus that is excluded from the
   groundedness ledger. This is more machinery and risks two sources of truth for
   "what heads exist"; not recommended unless heads are added in bulk.

If option 2 is chosen, the trig branch is still the reference implementation of the
methodology — keep it or cherry-pick the classifier change without the corpus.

## Continue toward v0.10 (after item 1 lands either way)

Per `ROADMAP-v0.10.md`, in dependency order:

- **Item 1 (more heads):** work the remainder backlog by coverage impact —
  relational/predicate head first (biggest gap), then quantifier/binder, then the
  function slot, then indexed aggregation. Each: author exemplar node(s) → make the
  classifier count it → re-run the instrument on all three sources → report the
  delta → update the GC pins. These are progressively harder grammar changes.
- **Item 2 (external verifier) is the pivot.** v0.9's hard finding: `verified_by`
  for ingested arithmetic is unreachable (offline, propositional-only correspondence,
  no Lean toolchain). Stand up a real external verifier (type-checker + tests → Lean)
  — it unblocks BOTH a real `verified_by` path AND the programming discipline (item 3).
- **Item 4 (author the covered subset)** and **item 5 (harness session)** follow
  once items 1–2 give honest, verifiable nodes to author.

Release gate for v0.10 is in `ROADMAP-v0.10.md`.
