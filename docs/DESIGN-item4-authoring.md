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

| # | outcome | evidence |
|---|---|---|
| P1 | **PARTIAL** | Seed emits **251**, not 302. `check_regeneration` is byte-identical (20 seeds). Zero matcher parse problems / slot gaps. The miss is the 51 unique-covered ground goals `TOKEN_RE` cannot tokenize: standalone `<` `>` are in `RELATIONS` but not in the character class (plus two `√(expr)` forms the seed's `SQRT_BARE` does not wrap). Filed in `docs/BACKLOG.md`. |
| P2 | **CONFIRMED** | `group_counts` moved `{31,32,31,33,5}` → `{35,36,35,37,5}` on 508 nodes / 27 corpora. Eight new typed pairs, all ingested-to-ingested (parenthesization / commutativity of the same ground identity). Zero ingested-to-curated typed pairs. |
| P3 | **CONFIRMED** | Operator-bag forms **7,622** pairs; matcher forms **96**. Matcher precision against the bag is **1.0**. Bag precision against the matcher is **0.0126** (was **0.0203** on the 257-node prior graph; **0.0054** on the 251 ingested nodes alone). The capability-blind baseline still "wins" on pair count and loses harder on precision. `experiments/item4_operator_bag.json`, `scripts/measure_operator_bag.py`. |
| P4 | *pending* | Waiting on `decompose.py` over 508 nodes. The absorption rate-gap pin will be flagged, not silently re-pinned, if it moves. |
| P5 | **CONFIRMED** | No node in this wave carries `verified_by`. Correspondence table stays **17 / 1 / 0** over 18 lean4 links (the registered "16 / 1 / 0" was the pre-item-5 count; this wave did not move the table item 5 left). |

**Disclosure 1 — 302 was a coverage count, not a parse count.** §1 said "every template is one the matcher already parses." That was wrong: the coverage instrument marks `<` `>` goals `full_ok` because `RELATIONS` contains them; `tokenize` still raises. The 251-after-filter is the honest first wave, not a silent narrowing after the fact — the seed's `template_parses` gate is the same parser the matcher uses.

**Disclosure 2 — WRITE-append was not the scale path.** §2 said a generator seed is the scale path. Confirmed: 251 nodes entered through `scripts/seed_lean_workbook.py`, not 251 calls to `accept_write`. Slice A's append lane remains the session-scale path.

**The roadmap question, answered on this wave (hundreds, not thousands).** The operator-bag baseline that "won" on pair count on the curated graph still wins on pair count (7,622 vs 96). It does not win on precision, and ingesting 251 ground identities made that worse (2.03% → 1.26% combined, 0.54% ingested-only). The matcher still only pairs shared typed skeletons. The rest of the 12,681 unique-covered goals wait on a skeleton emitter; that is a separate design, not a silent expansion of this wave.

## 6. Fully-ground statements are not generals (disclosed, then implemented)

Probed, not blind: `specialize.py` ran 87 minutes on the 508-node graph
without writing a report. The cause is the 68 first-wave templates with
8–30 operators (long sums and products) used as *patterns* against 507
other nodes. A fully ground tree has no slots to bind; the only matches
it can produce are algebra-swallowing noise (a 30-term sum absorbing
into another sum). That is not a general→specific edge.

Registered before the skip lands:

- **P6** (disclosed): skip a candidate general whose parsed tree has no
  slots. The 713 committed pre-ingest edges are a subset of the new
  report (no curated general is fully ground). No new edge has a
  fully-ground general. The run finishes inside `verify_slice`'s
  2-hour ledger timeout. New edges of the form *slotted general →
  ground specific* may appear and are reported.

This is a scoring-adjacent filter, not a silent timeout. The 87-minute
probe is the evidence; the skip is the decision.

Probed further: P6 alone (skip as general, keep as specific) still ran
past 25 minutes. Slotted laws matching *into* 30-operator ground sums
is the remaining explosion. A second measurement on the committed
pre-ingest report: 254 fully-ground nodes exist in the 508-node graph
(251 first-wave + the three earlier ingested arithmetic nodes); **zero**
of the 713 committed edges touch any of them.

- **P7** (disclosed): skip a fully-ground statement as a specific as
  well. Specialization is a slot-binding relation; a ground identity
  participates in the twin ledger, not this one. The 713 pre-ingest
  edges stay (none had a ground endpoint). The run finishes in
  minutes, not hours.

- **P8** (disclosed, performance, scoring-identical): `decompose.py`'s
  `forms_by_head` index skips slot-free trees. `pattern_cover` already
  refuses any pattern that does not bind a named-head call, so a
  slot-free tree can never be accepted as a pattern; leaving it in the
  index only burns the 250-attempt budget on 30-operator ground sums.
  Exact skeleton lookup (`side_forms` / `subterm_hosts`) is unchanged,
  so the `2^30` prior_corpus pair and any new exact shared subterms
  still count. Predicted: every GC4 aggregate that does not depend on
  the new nodes is identical to the 257-node report; the run finishes
  in minutes.
