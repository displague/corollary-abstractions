# Design — author the covered Lean-workbook subset (ROADMAP-v0.10 item 4, first wave)

Committed BEFORE the generator runs. Predictions in §4 are floors.
Depends on Slice A (`docs/DESIGN-write-append.md`).

## 1. Scope, argued

The coverage instrument marks 21,267 Lean-workbook statements
full-statement-covered, 12,681 unique goals. Most of those goals still
carry binders, `Real.sin`, or inequalities the template grammar can
*accept as covered* without yet *emitting* a skeleton. Authoring all
12k without a template emitter would either invent Lean-flavoured
templates the matcher cannot parse, or silently drop the "zero parse
problems" rule.

The first wave is the subset whose goal is **ground arithmetic** after
stripping Lean type ascriptions: numerals and `+ - * / ^ = ≤ ≥ ∣ √ ( )`
only. Measured before this note's implementation: **302 unique goals**.
That is a material jump from 257 nodes, provenance intact (the pinned
extract), and every template is one the matcher already parses.

The rest of the 12,681 wait on a skeleton emitter — a separate design,
not a silent expansion of this wave.

Already-authored ids (`lean_workbook_1041`, `10202`, `22080`, and any
other `numbertheory.ingested.*`) are skipped.

## 2. How they enter

A new seed, `scripts/seed_lean_workbook.py`, reads the committed
extract and emits `data/lean_workbook/nodes.json`. This is the
seed→regenerate route, not 302 calls to `accept_write`. WRITE-append
(Slice A) remains the session-scale path; a generator seed is the
scale path. Epistemic status is `formal` **without** `verified_by`:
these proofs are not re-checked under the hermetic core-Lean budget
(item 2 decision (b), recorded at node level).

## 3. The question this wave answers

Does any capability-blind baseline that won on the curated graph still
win on hundreds of ingested ground identities?

Baseline (cheapest, capability-blind): two statements are a pair iff
they use the **same set of operator glyphs** `{+,-,*,/,^,=}` (no
structure). The matcher pairs by typed skeleton. Report precision and
recall of each against the other as if the matcher groups were the
reference, and the reverse — both numbers, neither hidden.

## 4. Registered predictions

Disclosure: the 302 count was measured by a read-only classify pass
over the committed extract before this generator existed. No seed was
run; no ledger was regenerated.

- **P1** (probed count): the seed emits 302 minus any already-authored
  ingested ids (expected 302 or 301). `check_regeneration` is
  byte-identical. Zero matcher parse problems / slot gaps.
- **P2** (blind): `group_counts` moves. Ground identities share
  skeletons (`N = N`, `N * N = N`, …). The movement is reported, not
  assumed null.
- **P3** (blind): the operator-bag baseline forms strictly more pairs
  than the matcher (it cannot see argument structure). Matcher
  precision against that bag is the number of record. Both figures
  land in `experiments/ANALYSIS.md`.
- **P4** (blind): GC4 moves by adding constituents, not by dilution
  alone. The absorption **rate-gap pin is not silently re-pinned** if
  it moves — flagged for the queued maintainer sign-off.
- **P5** (blind): no node in this wave carries `verified_by`. The
  correspondence table stays 16 / 1 / 0 over lean4 links.

## 5. Adjudication — after the generator runs

§4 is frozen as registered.
