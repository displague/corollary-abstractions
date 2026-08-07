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

## equiv task: INCOMPLETE — two system crashes

The equiv/char run (longest job: char sequences of rewritten expressions
overflow toward the 512 cap) coincided with two machine-level crashes
(CLOCK_WATCHDOG_TIMEOUT 0x101), overnight and again ~08:40. That stop code
is a hardware watchdog (CPU core unresponsive), consistent with sustained
combined CPU+GPU load on a laptop. Training is **paused pending an explicit
go-ahead**; when resumed it should run throttled (smaller batch, capped GPU
power/clocks, one run at a time, thermals watched).

## Next

1. equiv A/B/C throttled rerun (the scientifically interesting task — no
   arm gets it "for free").
2. Size-reduction pass on the twins/canon winner (int8 dynamic quant,
   prune, accuracy-vs-bytes curve).
3. Scale corpus-side work (pure CPU, crash-safe): more disciplines, richer
   grammar, family-level tokenization stats.
