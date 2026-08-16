# Design — what predicts the gap (forward-looking, for ROADMAP-v0.13)

Written during v0.12 **before H1–H6 were graded**, so the next cycle's
question cannot be chosen to flatter this cycle's post. It is not v0.12
scope and is not scored this cycle.

## 1. Where this came from (the accident, again)

v0.11 measured whether an ingested layer's parts acquire owners inside that
same layer, and found a shape nobody registered: below a matched null at
N=8 and N=32, above it from N=128. v0.12 asked whether that shape survives
a source the emitter was not fitted to.

On held-out A it did not. miniF2F sits **below** its null at every size,
and the gap widens negatively (−0.016 at 8, −0.010 at 32, −0.043 at 157).
Its parts are not ungrounded — XSG runs 0.70–0.81 — they are owned by the
curated and Lean-workbook layers instead of by each other.

That is a clean negative, and a bump unless it comes with a mechanism. The
mechanism question is this note.

## 2. The question

**Does owner-attributed self-grounding track a source's structural
concentration rather than anything recovered about structure?**

Lean-workbook is ~12.5k olympiad inequality drills: a narrow distribution
where subterms necessarily recur. miniF2F is 157 competition problems
spanning algebra, number theory and geometry: wide and sparse. If ISG is a
concentration statistic wearing a structure costume, then v0.11's headline
is a fact about inequality drills sharing AM-GM skeletons, exactly as
[DESIGN-heldout-recovery.md](DESIGN-heldout-recovery.md) §2's third answer
feared — and the interesting claim is not "ingestion compounds" but
"*here is the property that says in advance whether it will*."

## 3. The trap this design must not walk into

**A concentration statistic will "predict" ISG by construction if ISG is
concentration.** Sorting three sources by skeleton reuse and finding it
orders the ISG gaps proves nothing on its own; it may be the same number
twice. Any candidate predictor therefore ships with a
**capability-blind control**, and the claim is about the *difference*
between them, never about the predictor's correlation alone.

Second trap: **a three-point series that only works after the third point
is post-hoc.** The predictor and the control are registered here, before
Goedel-Pset's gap is known and before anyone sorts a table.

Third trap, already visible: **emit rate is not the predictor.** The pair
already in hand refutes it —

| source | emit rate | ISG gap |
|---|---:|---:|
| Lean-workbook (fitted) | 99.03% | +0.063 |
| miniF2F | 98.12% | −0.043 |

One percentage point apart, and the gap changed sign. Emit rate measures
the emitter's distance from home, which is a fact about the *tool*, not
about the source's structure. It may be reported as context. It is not a
candidate.

## 4. Candidates, registered

All are computed from the source's own templates. None may read `owners`,
`owner_channels`, or any `decompose` field — the same prohibition the
held-out design put on its keyword baseline.

- **P (predictor): skeleton-reuse concentration.** Over a source's
  statements, the fraction of family skeletons hosted by more than one
  statement, and the Gini coefficient of the host-count distribution.
  `reports/compression.json` already computes the underlying counts, so
  this is source-intrinsic and committed rather than invented for the
  occasion.
- **B1 (capability-blind control): unique-skeleton count per statement.**
  Distinct skeletons divided by statements. A pure counting statistic with
  no notion of which skeletons, or of sharing.
- **B2 (capability-blind control): operator-bag entropy.** Shannon entropy
  over the `{+,-,*,/,^,=}` glyph-set distribution — the same bag the
  figure of merit already uses, and one that cannot see structure at all.

## 5. Registered predictions (frozen before Goedel-Pset's gap is known)

- **W1.** Across the sources measured by then (Lean-workbook, miniF2F,
  Goedel-Pset, and any v0.13 addition), **P orders the sources the same
  way the ISG gap does.**
- **W2 (the one that matters).** **P orders them better than B1 and B2
  do.** If a capability-blind counting statistic orders the sources just
  as well, then "concentration predicts the gap" is a restatement of "the
  gap is a counting artifact," and the honest reading is that ISG measures
  redundancy. W2 missing is the *more* interesting result and must be
  reported as prominently as a hit.
- **W3 (falsifier for the whole frame).** A source constructed to be
  *concentrated but not self-grounding* — many statements sharing a
  skeleton whose owners are all curated — still shows a low ISG gap. If
  no such source can be constructed, P and ISG are not separable and this
  design is measuring one thing twice; say so and stop.

Four sources is the minimum for W1/W2 to be anything but a story. Three
points ordered correctly is an anecdote with error bars wider than the
effect.

## 6. What this does not license

- Not a widening of H1–H6, which stay frozen and belong to v0.12.
- Not a reason to relax `unique-covered`, widen the emitter, or pad N to
  make a fourth source appear.
- Not a claim that a concentrated corpus is a *better* corpus. If the
  finding is "ingestion compounds only when the source is redundant," that
  is a limit on the claim, not a recommendation to ingest redundancy.

## 7. Disclosed probe permitted in v0.12

v0.12 may look at committed compression numbers against the measured gaps
and report it **labelled unregistered**. It may not be graded, may not
appear as a v0.12 headline, and may not be described as a predictor. It
exists so v0.13 starts from a looked-at table rather than a hunch, and so
that the looking is on the record as having happened before the
predictions above were scored.
