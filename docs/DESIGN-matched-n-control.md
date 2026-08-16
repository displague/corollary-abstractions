# Design — the matched-N control (C1), v0.12

**Registered before the N=157 cell was computed or read.** This file exists
so that a comparison the cycle already half-had cannot be finished after the
fact.

C1 is **not** part of H1–H6. Those six are frozen in
[DESIGN-heldout-recovery.md](DESIGN-heldout-recovery.md) §5 and are not
widened, re-worded, or re-numbered by this note. C1 is a separate
prediction with its own experiment and its own committed artifact.

## 1. The objection this removes

Held-out A (miniF2F) sits below its matched null at every size:

| N | real ISG | null mean | gap |
|---:|---:|---:|---:|
| 8 | 0.0000 | 0.0163 | −0.0163 |
| 32 | 0.0000 | 0.0099 | −0.0099 |
| 157 | 0.0055 | 0.0482 | **−0.0428** |

Lean-workbook, the source the emitter was fitted to, was below its null at
N=8 and N=32 and **positive from N=128** (+0.046 at 128, +0.042 at 512,
+0.063 at 12,515).

The cheap objection is that these are different sizes. miniF2F's ceiling is
157, which sits *below* the 128–512 band where Lean-workbook's sign changed,
so "the shape did not recur" is currently confounded with "157 is too
small." A reader is entitled to that objection and it costs one curve point
to remove.

## 2. The experiment

Run the **existing** generator, `scripts/measure_self_grounding.py`, on
Lean-workbook at exactly **N=157** — the same size as held-out A's full
layer. Same selection-seed protocol, same null seeds, same `min_family`,
same `pattern_membership=False`.

Committed as `experiments/matched_n_control.json`, its own file. The v0.11
artifact `experiments/self_grounding_curve.json` is **not** edited: adding a
row by hand to a published curve and calling it a new experiment is the
thing this sentence exists to forbid.

## 3. C1, registered

> **C1.** At identical N=157, Lean-workbook's gap and miniF2F's gap have
> **opposite sign**, or differ by more than both nulls' seed-to-seed
> spreads combined.

**Fired** means size is not what separates the two sources: at the same N
the fitted source compounds and the held-out source does not. That isolates
*source* from *scale*, and it is the sentence v0.12 is allowed to publish.

**Missed** means the two gaps agree in sign and are within the nulls'
spread at matched N. Then size-matching does **not** settle
concentration-versus-structure, and that is written down as plainly as a
hit would be. A miss does not license a retry at a different N chosen to
make it fire.

## 4. What C1 is not

- Not a test of *why*. C1 separates source from scale. It says nothing
  about which property of a source is responsible. That question is the
  v0.13 design, written separately and deliberately **not** scored this
  cycle.
- Not a replacement for held-out B. B is the scale test and still owns
  H1/H3/H5/H6.
- Not a licence to widen the emitter, relax `unique-covered`, or pad N.

## 5. Vacuity check

The comparison is only meaningful if the null is non-zero at N=157 on both
sides. It is on miniF2F's (0.0482, from three seeds spanning 0.0404–0.0623).
If Lean-workbook's null at N=157 came back at or near zero, the matched
comparison would be two different degeneracies and C1 would be unreadable —
that must be reported rather than scored.
