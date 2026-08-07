# Overnight experiment analysis — 2026-08-07 morning

## Setup

Synthetic algebra world (`exprgen.py`): random expression trees rendered to
disguised ASCII (random names, commutative shuffles, `-`/`/` sugar, redundant
parens), labels verified by independent numeric evaluation (0 label errors in
audit). Two binary tasks, 50k train / 5k val / 5k test pairs each, plus a 3k
OOD split of *deeper* trees (depth 5-6 vs 2-4 trained):

- **twins**: same canonical skeleton under disguise? (tests whether a model
  can learn the canonicalization our symbolic front-end does exactly)
- **equiv**: equal modulo algebraic rewrites (distribute/factor, identity
  elements, power expansion)? Canonicalization alone cannot solve this.

One architecture for all arms — 4-layer transformer encoder, d=128,
~880k params — only the tokenization differs:

| arm | front-end does | vocab |
|---|---|---|
| char | nothing (raw ASCII) | 67 |
| struct | lex + parse (surface order kept) | 22 |
| canon | lex + parse + canonicalize | 22 |

## Milestone 2 (compression): PASSED

Mean sequence length, twins train split: char 104.4 -> struct 45.7 ->
canon 38.9 tokens. Concept-structured encoding is **2.7x shorter** than
characters on identical content.

## Milestone 3 (equal-size accuracy): twins task complete

| arm | test acc | OOD acc | train time |
|---|---|---|---|
| char | 0.562 | 0.499 | 574s |
| struct | 0.668 | 0.577 | 164s |
| canon | 0.709 | 0.598 | 125s |

Reading:

- The 880k-param char model barely beats chance in-distribution and is
  **exactly at chance (0.499) on deeper expressions** — it memorized surface
  statistics, learned no algebra. Each front-end increment adds real
  accuracy (+10.5 pts parse, +4.1 pts canonicalize) and transfers to OOD.
- Training cost fell 4.6x from char to canon for the same epochs — shorter
  sequences are quadratically cheaper under attention.
- Honest caveat: no arm *solved* twins at this size. 0.709 is far from the
  ~1.0 the symbolic front-end gets for free (canonical skeletons decide
  twins exactly). The experiment argues the design doc's division of labor:
  spend exact symbolic computation where it is exact, spend weights only on
  what has no closed form.

## equiv task (throttled rerun, batch 128): complete

| arm | test acc | OOD acc |
|---|---|---|
| char | 0.667 | 0.565 |
| struct | 0.742 | 0.652 |
| canon | 0.738 | 0.626 |

Reading — this is the informative negative result of the suite:

- Parsing is the universally load-bearing front-end step (+7.5 pts over
  char, and char is no longer at chance here because rewrite artifacts
  leave surface cues).
- **Canonicalization does NOT help on equiv** (tied on test, 2.6 pts worse
  OOD). It pays only when the task *is* canonicalization (twins: +4.1).
  Pre-normalizing can even destroy alignment cues a learner exploits.
  Design consequence: the symbolic front-end should expose *both* the
  surface parse and the canonical form as inputs, not replace one with the
  other — normalization is a query-time tool, not a universal encoding.

## Size reduction (accuracy-vs-bytes, CPU int8/pruning)

Both winners (twins/canon, equiv/struct), same pattern:

| rung | bytes | twins test/OOD | equiv test/OOD |
|---|---|---|---|
| fp32 | 3.53 MB | .709 / .598 | .742 / .652 |
| fp16 | 1.78 MB | .709 / .598 | .742 / .652 |
| int8 dynamic | 1.92 MB | .709 / .597 | .742 / .652 |
| prune50+int8 | 2.19 MB | .703 / .594 | .719 / .631 |
| prune70+int8 | 1.31 MB | .610 / .566 | .628 / .613 |

- fp16 is free: 2x smaller, zero accuracy change. int8 is also free on
  accuracy but *larger* than fp16 here because dynamic quant only touches
  Linear layers — embeddings/positions stay fp32. At this scale the
  embedding table is the size problem, exactly the design doc's thesis.
- 50% sparsity costs ~1-2 pts; 70% breaks (-8 to -11 pts). Sparse index
  overhead (4B/nnz) means pruning only pays at high sparsity — and high
  sparsity is where accuracy dies. For tiny models: quantize, don't prune.

## Crash context (resolved by throttling)

Two CLOCK_WATCHDOG_TIMEOUT (0x101) crashes coincided with the original
full-batch equiv/char runs. Throttled protocol (batch 128, one run at a
time, one compute domain at a time, 85C alarm) completed the entire queue
at a steady 58-60C with no incident. The throttle is now the house rule
for GPU work on this machine.

## xlang task (bilingual grammar world): predictions vs results

Registered predictions: char << struct << canon ~= 1.0; char worst OOD.

| arm | test acc | OOD acc | front-end gave |
|---|---|---|---|
| char | 0.576 | 0.564 | nothing |
| struct | 0.674 | 0.560 | both parse trees, native words |
| canon | 0.708 | 0.553 | canonical interlingua (concept ids) |

- **Confirmed**: the ladder direction on test. Parsing two grammars +
  bilingual dictionary from characters is hardest; each front-end
  increment helps.
- **Falsified, informatively**: canon was predicted ~1.0 because its
  positive pairs are *literally identical token streams* around the
  separator. It reached 0.708. An 880k-param encoder cannot reliably do
  exact cross-segment equality — a known transformer weakness (exact
  match/copy needs induction-head-like circuits this scale doesn't
  spare). Same ceiling visible in twins/canon (0.709): the twin tasks
  were bottlenecked by learned *comparison*, not by tokenization.
- **Falsified**: all arms collapse comparably on deeper modifier
  recursion (0.55-0.56); char was not distinctly worst OOD.

Design consequence, and it is the night's thesis sharpened from a new
direction: once the symbolic front-end has reduced a question to exact
stream equality, *the equality check itself belongs in the symbolic
layer* (where it is free and perfect), not in weights. Weights are for
the graded residual only: dictionary alignment (struct's real job),
soft/partial matches, semantics that survive after exact structure is
handled. "Emergent understanding" should be expected for the residual,
not for operations that have closed forms.

## qa task (QA-as-unification, cross-language): the residual is real

| arm | test acc | OOD acc |
|---|---|---|
| char | 0.500 | 0.500 |
| struct | 0.689 | 0.557 |
| canon | 0.644 | 0.592 |

- **char is at exact chance, in-distribution.** Raw text at this scale
  learns nothing about cross-lingual unification — not "less," nothing.
  The strongest single data point of the suite for the front-end floor:
  the residual (unification) is only learnable at all once parsing has
  been done for the model.
- struct vs canon, settled by 3 seeds each: test means overlap (struct
  0.648 +/- 0.045, canon 0.661 +/- 0.023 — the single-seed "struct wins
  test" was seed noise), but **canon generalizes better OOD in every
  seed** (0.587 +/- 0.016 vs 0.523 +/- 0.030, one struct seed at chance).
  Canonical interlingua shrinks what must generalize; surface parses
  leave word-order variance the model must absorb. Also notable: 9-point
  test spread across seeds for struct — tiny models are seed-sensitive
  here, so no single-seed claim from this suite should be trusted.

## Next

1. Hybrid head: symbolic-equality/unification bit + learned residual as
   model input; measure the lift over either alone.
2. Grow the family-level concept vocabulary from the corpus; measure
   milestone 2 compression on real statement nodes.
3. More disciplines (economics: compound interest should family-twin
   exponential growth/decay).
4. Multi-seed reruns before claiming struct/canon orderings on qa.
