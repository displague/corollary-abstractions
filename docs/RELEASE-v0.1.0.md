# v0.1.0 — The interface thesis, measured

First release. Everything below is reproducible from this repository
alone: all headline results run on synthetic worlds regenerated
bit-identically from committed generators and seeds (`experiments/*.py`,
seeds in the argparse defaults). No external data is required. The
licensed corpus samples under `experiments/data_real/` (user-supplied
corpusdata.org downloads, gitignored) feed only the auxiliary lexicon
profile in `experiments/results/wlp_profile.json` and no claim depends
on them.

## What the system does, in plain terms

**Language.** Two invented languages: one English-like ("the brave
farmer helps the tired cat"), one with disjoint vocabulary, verb-final
order, adjectives after nouns, and a question particle ("vermim gishim
rengig sulum ka" — "who does the brave farmer help?"). Hand a ~2 MB
(800k-parameter) model the foreign question and several English-like
statements — only one of which answers it — and it points at exactly
the right phrase. To do that it implicitly learned both grammars, a
bilingual dictionary nobody gave it, and that a question is a statement
with a hole whose answer fills the hole.

- **It composes.** Verb–noun combinations deliberately held out of
  training (the verb never co-occurred with the answer noun) are
  answered at 100% exact match, both seeds, on a test whose
  content-blind floor is independently verified at 0.31
  (`experiments/solvex2.py`).
- **It survives depth it never saw** — modifier stacks beyond any
  training example — at 0.97 exact match on the pure pointing task,
  *only* when ordinary non-AI code supplies each token's structural
  address (its ancestry path in the parse tree). Without that, 0.20;
  and on multi-statement input, absolute-position models fail even on
  seen data (0.29 ≈ floor).
- **Scale does not substitute for the interface.** Across 8x model
  width and 10x data, depth generalization under learned positions is
  flat (0.05–0.19, no knee); with symbolic addresses it is ≥0.95 in
  every cell, including a 32-wide model on 5k examples
  (`experiments/run_grid.py`).

**Mathematics and logic.** The same machinery, pointed at formulas,
discovers that different sciences keep writing the same equation
(`scripts/match_signatures.py`, `scripts/specialize.py`, 85 statement
nodes across 9 disciplines in `data/`): Coulomb's law and Newtonian
gravitation share one typed skeleton; the quantity theory of money is
the ideal gas law with a suppressed constant; compound interest,
population growth, and radioactive decay are a single exponential
family differing by a sign convention; the laws of logic and of sets
are one Boolean algebra, twin by twin. The language and math lanes are
one mechanism because *a question is an equation*: answering "who
chases the cat?" and solving `F = m·a` for `a` are both unification
against a statement with a hole — and the QA experiments measure
exactly that operation.

## The architecture thesis these results support

Keep outside the network everything that has a closed form — parsing,
canonicalization (query-time, not universal), equality, the lexicon,
and structural *addresses* — and a very small network does genuinely
compositional work on the graded residual. Measured along the way:
weight-stored lexicons are brittle (chance OOD) where extrinsic ones
lose nothing; embedding tables dominate tiny-model bytes (quantize,
don't prune; fp16 is free); canonicalization helps only when the query
is identity.

## Honest limits

- Controlled toy worlds: invented vocabulary, simple sentence types,
  synthetic formulas. Real-data lanes (Spanish morphology lexicon,
  Simple-English-Wikipedia logical forms, mathlib via LeanDojo) are
  staged, not run.
- The system points, classifies, and matches; it does not yet generate.
  The generation path (model emits concept trees; exact code renders
  surface text) is designed but unbuilt.
- One earlier "perfect score" (solvex v1) was an artifact of a
  too-easy test, caught by external audit; the corrected instrument
  (v2) has its vacuity check built in. Scaling-grid cells are single
  seed (trend claims only). v2 depth OOD is 0.69 — open headroom.
- Multi-seed rule: no single-seed comparison is trusted anywhere
  claims are made; 9-point seed spreads were observed at this scale.

## Reproduce

    python scripts/validate_nodes.py
    python scripts/match_signatures.py
    python scripts/specialize.py
    cd experiments
    python solvex2.py --out-dir data
    python train_span.py --arm struct --task-prefix solvex2 --positions tree --data-dir data --out results/repro.json

Full experiment narrative with every intermediate result and
retraction: `experiments/ANALYSIS.md`.
