# prover/ — tiny verifier-coupled prover (sub-project)

Status: phase 1 feasibility PROVEN NATIVE on Windows (2026-08-07, see
FEASIBILITY.md): real (stateBefore, tactic, stateAfter) triples extracted
from a Lean 4 repo via the patched ExtractData.lean under lake -- no WSL2,
no Python package install. PyPantograph interaction verified natively
(goal -> intro -> exact -> solved). The lean-dojo-v2 PYTHON package is
Windows-blocked by its deepspeed dependency, but phase 1 never needs it.
Next: keep the patched extractor as prover/ExtractData.win.lean and run it
over a small theorem corpus; WSL2 deferred until the training layer, if
ever.

## Thesis

A small model cannot match a large model's stored knowledge, but it does not
need to when a verifier supplies ground truth. Lean checks every candidate
proof step, and search multiplies the policy's effective strength. This is the
AlphaZero structure applied to formal math, and it is the one setting where a
~30M-parameter model (≈64 MB at fp16) can legitimately stand next to much
larger models on a public benchmark.

Reference points (state of the field, for calibration):

- LeanDojo: open toolkit that extracts theorem/tactic data from mathlib and
  lets a program interact with Lean proof states
- ReProver: LeanDojo's retrieval-augmented baseline prover (~300M params)
- miniF2F: the standard formal-math benchmark this sub-project targets —
  not MMLU or other general LLM benchmarks

## Why the corpus is not `data/`

Hand-curated nodes cannot reach training scale; mathlib (100k+ theorems,
machine-extracted) is the training corpus. The `data/` ontology instead plays
two roles here:

1. evaluation and analysis: cross-discipline twin structure the trained
   policy should recover
2. tokenization: `docs/DESIGN-concept-tokens.md` — proof states and tactics
   re-encoded over concept tokens are this sub-project's experimental
   tokenizer, and milestone 3 of that design is tested here

## Phases

1. **Data**: extract (proof state, tactic) pairs from mathlib via LeanDojo.
   Deliverable: a reproducible extraction script and corpus statistics.
2. **Baseline policy**: small decoder (~30M params) with a conventional
   subword tokenizer; next-tactic prediction. Deliverable: top-k tactic
   accuracy on held-out theorems.
3. **Search**: best-first search over Lean proof states driven by the policy,
   Lean as the verifier. Deliverable: % of held-out theorems closed within a
   node budget; first miniF2F run.
4. **Concept tokens**: swap in the concept-token encoding from
   `docs/DESIGN-concept-tokens.md`; same parameter budget. Deliverable: the
   A/B against phase 2/3 that the design doc's milestone 3 demands.
5. **Retrieval / extrinsic lexicon**: premise selection over the ontology and
   mathlib as an external index (pointer head, not weights).

Each phase is useful even if the next never happens; stop whenever the
evidence says stop.

## Practical constraints

- Lean + LeanDojo run best on Linux; on this Windows machine use WSL2.
- Phases 2-4 need GPU time (rentable; single consumer GPU is enough for a
  30M-param model).
- Do not start phase N+1 until phase N's deliverable exists and is committed.
