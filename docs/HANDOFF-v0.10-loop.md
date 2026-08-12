# Handoff — v0.10 loop state (through-v0.11 mission)

Written 2026-08-11 after the quantifier/binder head merged. This is the resume
point for the session loop (or a fresh session) working ROADMAP-v0.10 through
the v0.11 release. The durable numbers of record live in the committed
`experiments/*_coverage.json` + `experiments/ANALYSIS.md`; this file is the
process state.

## Where main stands (all merged, pushed, 892 green)

| slice | merge commit | corpus | Goedel full | LW | miniF2F |
|---|---|---|---|---|---|
| v0.9.0 baseline | `7007d4f` | 221/22 | 32.8% | 64.1% | 29.7% |
| trig head | `c5537d6` | 229/23 | 35.0% | 65.7% | 30.1% |
| relational/predicate + let-fix | `d131e16` | 241/24 | 38.9% | 65.8% | 30.9% |
| quantifier/binder | `f24ddeb` | 251/24 | **43.2%** | **71.4%** | **33.0%** |

Every slice followed: worktree agent implements (measure → design-register →
corpus → classifier → instruments → pins) → independent adversarial review →
fixes → spot-verify → ff-merge. The review caught a real over-count all three
times (head-not-carried class → carrier cross-segment shield → mixed-carrier
chain shield). Twin null has held four times (group_counts {30,31,30,32,5}).
GC4/GC5 pins carry three registered acknowledgments (append-only). The
absorption **rate-gap pin was re-pinned against its guard direction**
(0.12 → 0.164, count guard 4.3:1 held) — flagged to the maintainer; merging
implied provisional acceptance; revisit at release triage.

## TOKEN ECONOMY — the process change for the next slices (user-directed)

The reviews were thorough but token-heavy (~200–450k per agent pass, most of
it re-running instruments and re-deriving mechanical checks). **Before the
next slice, build the mechanical review harness** so agents verify by running
one script instead of re-discovering everything:

`scripts/verify_slice.py <base-commit>` (new, ~1 day of work) should
mechanically check and print a PASS/FAIL table for:
1. `check_regeneration` (seeds byte-identical), `validate_nodes`, matcher
   `parse_problems`/`slot_schema_gaps` == 0.
2. All report ledgers + all three coverage JSONs regenerate **git-clean**
   from the SHA-pinned archives (fetch check first; archives are gitignored
   and vanish with deleted worktrees — junction from a sibling worktree if
   present).
3. **Per-row dual pass** old-vs-new (the house LOST standard): parse
   agreement, cov→uncov list (must be 0 or every row printed), gain buckets
   (must come only from the targeted gap labels).
4. Audit fields 0/0, and the audit-sees-the-last-three-FP-classes regression
   tests.
5. GC pin diff report (which pinned values move; acknowledgments intact
   byte-wise), group_counts null check, absorption count-guard arithmetic.
6. Full suite.
With that script, the ADVERSARIAL REVIEW shrinks to: run the script + attack
the DESIGN (the one thing scripts can't do) + hand-adjudicate a ~20-row random
sample of new covers + hunt one novel FP class. Cap review agents' scope
accordingly; use cheaper models (sonnet/haiku) for the mechanical fix passes
and keep the big model for design review only. Implementation agents: run
long jobs synchronously (backgrounded jobs die when an agent stops — this bit
twice), and commit incrementally so a session-limit kill loses nothing.

## Next work, in order (ROADMAP-v0.10)

1. **More heads by measured impact** (measure first — the buckets moved):
   remaining Goedel gaps after quantifier: embedded quantifiers 62,142 goal
   rows (needs an atom-tree walk; named successor in ANALYSIS), big_operator
   ~77k pre-shift, set_or_finset ~68k, function binders 21,370 + function
   slot (~14% family), abs 43,472, monus 41,239, int-div 40,442 (the
   carrier-honest number field would convert these three from gaps to heads —
   NNReal `-` monus item filed in BACKLOG). Each slice: same pattern, plus
   the verify_slice harness FIRST.
2. **Item 2, the pivot: EXTERNAL VERIFIER** (type-checker + tests → Lean).
   Unblocks real `verified_by` for ingested arithmetic AND the programming
   discipline. User-supplied candidate sources for the programming phase
   (also in memory `programming-discipline-sources.md`): thuva4/Algorithms,
   IBM Project CodeNet (+ HF mirror `TheFinAI/ibm-project-codenet` — has
   test cases, apt for the verifier), arXiv 2105.12655, 2605.15607v2,
   2602.16106v1. License-gate through `data_sources/manifest.json` pins.
3. **Author the covered subset** (PROVEN-WRITE) → recompute ledgers at scale.
4. **Harness session** end-to-end; then **v0.10 release** via the release
   skill — which now REQUIRES the drift audit vs v0.9's goals (re-read the
   previous release's notes/roadmap for attrition) and ≥1 forward-looking
   design item seeding ROADMAP-v0.11. Then work v0.11 per that roadmap.

## Traps that bit this cycle (beyond the standing ones in memory)

- Session usage limits kill running agents mid-flight; their backgrounded
  shell jobs die with them. Resume via SendMessage (context survives); tell
  agents to run long jobs in the foreground.
- Agents that stop to "wait" on their own background jobs fire a completion
  notification and orphan the jobs — same fix.
- `data_sources/archives/` is gitignored: deleting a worktree deletes any
  archives fetched inside it. The Goedel parquets currently live in
  `.worktrees/v010-relational-head` and are junctioned into
  `.worktrees/v010-quantifier-head`. Junction or re-fetch (SHA-pinned) as
  needed; consider moving them to the main checkout's archives dir before
  deleting either worktree.
