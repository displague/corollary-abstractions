# prover/ — tiny verifier-coupled prover (sub-project)

Status: phase 1 feasibility PROVEN NATIVE on Windows (2026-08-07, see
FEASIBILITY.md): real (stateBefore, tactic, stateAfter) triples extracted
from a Lean 4 repo via the patched ExtractData.lean under lake -- no WSL2,
no Python package install. PyPantograph interaction verified natively
(goal -> intro -> exact -> solved). The lean-dojo-v2 PYTHON package is
Windows-blocked by its deepspeed dependency, but phase 1 never needs it.
Phase 1 DELIVERED (2026-08-07, see PHASE1_NOTES.md): 155 tactic steps
extracted from 16 natively-proved theorems mirroring data/logic's Boolean
laws -- ExtractData.win.lean (provenance-headed patched tracer) +
sample_triples.json committed. Per the phase gate, phase 2 (baseline
tactic-prediction policy) may begin; the extraction's premises field
already provides the retrieval index phase 5 will want. WSL2 remains
unnecessary.

Phase 2's first rung landed in v0.6: ``live_search.py`` applies tactics
through PyPantograph and the domain-neutral ``SearchController`` performs
bounded breadth-first search over verifier-accepted states. A fixed, unranked
palette closed a held-out ``Init`` proposition in 9 expanded states / 86
proposals; removing its projection tactics exhausted in 10 / 80.

**Phase 3's first deliverable now exists** (ROADMAP-v0.7 item 1): a
multi-theorem held-out solved-rate curve, not a trace.

- ``prover/theorems_v1.json`` — 24 held-out theorems, four families
  (``conjunction``, ``implication_chain``, ``disjunction``,
  ``project_import``), each tagged with family, source, held-out status and a
  witness. **Versioning: additions create ``theorems_v2.json``; v1 is never
  edited once a published curve names its sha256.** "Held out" is checked
  against ``sample_triples.json`` by test, not asserted.
- ``prover/tactic_grammar.py`` — the roadmap's separation of *schema choice*
  from *tactic-argument generation*. A ranker orders eight schemas; this
  module computes concrete tactic text from the rendered goal. Every arm gets
  the identical candidate multiset and may only permute it.
- ``prover/curve_search.py`` + ``experiments/tactic_curve.py`` — four ranking
  arms over 144 live runs at five budget rungs. At 8 states / 64 proposals:
  syntax-aware blind 21/24, frequency 20/24, learned 18/21/19, arbitrary
  17/24; all arms 24/24 at v0.6's own maximum budget. Mean proposals 48.29 /
  51.58 / 49.00 / 55.96. The learned checkpoints overtook v0.6's frequency
  winner and still lost to a closed-form order. The learned arms were also
  slower in the recorded fixed-order host run; that timing is observational,
  not a counterbalanced latency claim.
- ``prover/lean/proofcurve/`` — a Lake project (run ``lake build`` once) that
  makes ``project_import`` a real family: an ``Init``-only server cannot even
  state its propositions. Native Windows project loading works by passing
  ``lean_path`` explicitly, which stops PyPantograph 0.3.15 from shelling out
  to POSIX ``printenv`` (FEASIBILITY.md landmine 12, now resolved).
- ``experiments/story_curve.py`` — the same policy protocol over story
  actions. Same ``SearchController``, domain weights, disjoint vocabulary.

The learned rung remains a LOSS, reported as a valid result.
``experiments/train_tactic_policy.py`` trains a 27,688-parameter byte-GRU over
60 atomic schema-mapped transitions. Three theorem-held-out seeds reach 0.8125
top-1 against a 0.4375 frequency baseline and 0.25–0.375 shuffled controls.
Checkpoints are gitignored and ship only as release assets. To demonstrate a
downloaded checkpoint:

```powershell
$env:PYTHONPATH = '<pantograph-venv>\Lib\site-packages'
$env:Path = "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.29.1\bin;$env:Path"
python experiments\train_tactic_policy.py --live `
  --demo-checkpoint experiments\results\tactic_policy_s1.pt
```

This is learned ordering over a fixed palette, not tactic generation or a
miniF2F solved-rate result.

To reproduce the v0.7 curve (same shell environment, plus one Lake build):

```powershell
cd prover\lean\proofcurve; lake build; cd ..\..\..
python experiments\tactic_curve.py     # 144 live runs, ~8 s
python experiments\story_curve.py      # 48 runs + 3 tiny trainings, ~95 s
```

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

- Use the native Windows path documented in `FEASIBILITY.md`: extraction via
  the patched Lean tracer and interactive proving via PyPantograph (tactic
  application over the Python RPC, `is_solved: True` on a real theorem) have
  both been demonstrated without WSL2. Imported-project live search and a
  24-theorem, four-family, five-rung solved-rate curve now exist as well
  (v0.7 item 1). What remains open is a learned gain over the strongest
  capability-blind order — the syntax-aware arm still wins — plus a family
  whose premises must be selected rather than discharged in order, a
  dead-branch ledger that survives between runs, and reconciling the 4.29.1
  Pantograph build with the 4.32.2 extraction project so live search can run
  against the project the training triples came from. The `lean-dojo-v2`
  Python package
  remains unavailable here because of its `deepspeed` dependency; introduce a
  Linux/WSL2 path only if a later phase actually requires that package.
- Phases 2-4 need GPU time (rentable; single consumer GPU is enough for a
  30M-param model).
- Do not start phase N+1 until phase N's deliverable exists and is committed.
