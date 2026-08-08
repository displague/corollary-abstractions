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

## syn task (thesaurus induction under unification), 2 seeds/arm

Language B has 2-3 interchangeable words per concept; the synonym clusters
appear nowhere in the input. The struct-canon gap directly measures how
much thesaurus the weights learned.

| arm | test acc | OOD acc |
|---|---|---|
| char | 0.506 | 0.513 |
| struct (must induce thesaurus) | 0.600 | **0.508** |
| canon (gold thesaurus) | 0.660 | 0.587 |

- canon reproduces qa/canon (0.660/0.587 vs 0.661/0.587) almost exactly —
  as it must, since gold concept ids make the tasks identical. A free
  internal-consistency check on the whole pipeline, passed.
- struct learned *some* thesaurus in-distribution (0.600 vs the 0.660
  ceiling: roughly two-thirds of the achievable signal) — but **collapses
  to chance OOD (0.508)** while gold-lexicon canon holds 0.587. The
  weight-learned lexicon is partial AND brittle: it does not survive
  deeper recursion.
- This is the extrinsic-lexicon thesis measured, and it upgrades the
  claim: externalizing the lexicon is not only a size play (the embedding
  table finding) but a **robustness** play. A lexicon in weights at this
  scale is worse in-distribution and worthless out-of-distribution
  compared to the same lexicon supplied symbolically.

## Milestone 2 on the real corpus (67 nodes, 7 disciplines)

Mean tokens per statement (scripts/measure_compression.py):

| encoding | tokens | vs char |
|---|---|---|
| char | 37.5 | 1x |
| struct (parse tokens) | 13.6 | 2.77x |
| concept (family-skeleton id + slot fillers) | 4.4 | **8.44x** |

The synthetic-world 2.7x reproduced almost exactly at the struct level
(2.77x) on real statements — and the full concept encoding adds another
3x on top. Honest accounting: concept decoding requires the skeleton
vocabulary (49 skeletons for 67 nodes, 1.37 nodes/skeleton, 8 reused),
which is precisely the extrinsic structure lexicon — the cost lives in
the reference store, not the stream, and amortizes as reuse grows. The
most-reused skeletons are exactly the cross-discipline families (ratio
5, exponential 4, affine 4, scaled-linear 4, scaled-quadratic 3): reuse
concentration and cross-discipline generality are the same phenomenon.

Specialization matcher v2 shipped corpus-side (scripts/specialize.py):
the recorded arity misses now fire (equation of exchange >= ideal gas;
Cobb-Douglas <= power-law rate; Beer-Lambert generalizes the
scaled-linear family) — see reports/specializations.json.

## Hybrid head (syn task, 2 seeds): the capstone

Two symbolic feature tokens prepended to the struct stream: a
lexicon-blind structural-unification bit (WH matches anything, leaf
identity erased) and the WH-role. The bit alone scores 0.738 with
perfect rejection precision — already above every learned arm.

| arm | test | OOD |
|---|---|---|
| char | 0.506 | 0.513 |
| struct | 0.600 | 0.508 |
| canon (gold lexicon) | 0.660 | 0.587 |
| shape-bit alone (no learning) | 0.738 | — |
| **hybrid (bit + learned lexicon)** | **0.746** | **0.805** |

OOD accuracy EXCEEDS in-distribution accuracy — unique in the suite. The
symbolic feature is depth-invariant, and deeper trees break shape more
often, so the symbolic share of the decision *grows* exactly where the
learned share collapses. Hybrid beats the gold-lexicon arm by 9 points
test and 22 OOD: fusing symbolic exactness with the learned residual
strictly dominates choosing either.

This closes the experimental arc the suite was built for. The measured
division of labor, end to end: the symbolic layer parses always,
canonicalizes when the query is identity, performs all exact
comparisons, and contributes depth-invariant structural evidence; the
weights hold only the graded residual (lexical alignment); the lexicon
and the skeleton vocabulary live outside the weights for both size
(embedding tables dominate tiny models) and robustness (weight-stored
lexica die OOD). Every clause is now a measurement, not a design bet.

## Emergence battery 1 — solve-for-X (span pointing, recombination splits)

Answer a cross-language WH-question by pointing (start, end) at the
answer span in the statement. Test = ONLY held-out verb x noun combos;
ood = held-out combos + deeper recursion. 2 seeds/arm, exact match:

| arm | test (novel combos) | OOD (deeper) |
|---|---|---|
| struct | 0.999 | 0.203 |
| hybrid | 1.000 | 0.206 |

- **RETRACTED (user audit): "recombination is solved" was an
  overclaim.** A content-free structural rule (WH position in the
  question names the role; bracket-counting locates that role's
  constituent in the statement) scores 1.0000 on test AND ood — the
  label never depends on lexical content, so the held-out-combo split
  cannot stress composition. Zero literal train/test duplicates
  (construction forbids them); the flaw was a shortcut, not leakage.
  The 1.000 shows only that the pointer learns a structural rule the
  symbolic layer computes exactly anyway — one more entry for "exact
  ops stay symbolic." A real recombination test needs content to be
  load-bearing: solvex-v2 adds distractor statements so selecting the
  right one requires cross-language matching of the fixed role.
- **Depth is the wall, and it is a pointer failure, not a comparison
  failure**: the hybrid's structural features do not help because the
  breakdown is absolute position embeddings failing to extrapolate to
  longer sequences. Depth/length generalization is now isolated as THE
  frontier across the whole suite (every task's OOD collapse traces to
  it).
- Next probe follows the house pattern (symbolic carries what it knows
  exactly): replace linear positions with tree coordinates from the
  parse (depth + sibling index) — depth-invariant by construction — and
  measure OOD recovery.

### Positional-encoding ladder (struct arm, 2 seeds each)

| positions | test | OOD | failure mode |
|---|---|---|---|
| absolute | 0.999 | 0.203 | no extrapolation to longer sequences |
| local (depth, sib), no segment id | 0.385 | 0.000 | cross-segment collision: question and KB tokens share (depth, sib) coordinates, so the pointer cannot even separate the two trees in-distribution (seeds bit-identical) |
| local (depth, sib) + segment | 0.694 | 0.505 | aliasing: identical (word, depth, sib) across subtrees are indistinguishable to a pointer (seeds bit-identical — deterministic ties) |
| **ancestry paths** | **1.000** | **0.973** | (one seed: 1.000 OOD — perfect depth extrapolation) |

(The no-segment rung's artifacts, `solvex_struct_tree_s{0,1}.json`, were
recovered after sitting untracked: the +256-parameter delta to the
committed `tree2` run — exactly a 2×128 segment embedding — identifies
them as the first tree-coordinate attempt, run before the segment id was
added. Recorded because the rung explains WHY the segment id exists:
local coordinates fail across segments before they fail across depth.)

**Depth generalization — the wall behind every OOD collapse in the
suite — falls when position = symbolic tree address.** Ancestry paths
(per-token sequence of sibling indices, level-wise embedded, per-side +
segment id) are unique per node (no aliasing) and level-wise
in-distribution as trees deepen (span-boundary tokens keep shallow
paths). With the shortcut audit in mind, the ladder's meaning narrows and
sharpens: the task is PURE structural pointing (content irrelevant), so
this cleanly isolates addressing with no lexical confound — absolute
positions cannot even point structurally at unseen depths (0.203);
ancestry paths can (0.973, one seed perfect). The claim that survives:
the symbolic front-end's third contribution is addresses. The
recombination claim moves to solvex-v2.

Implication for the model design: positional encoding is not a
hyperparameter here, it is part of the symbolic/learned interface.
"Discrete infinity" behavior appears when the addressing scheme is
recursion-aware.

Ported to the classifiers (2 seeds each):

| task+treepos | test | OOD | abs-position baseline |
|---|---|---|---|
| xlang struct | 0.897 | 0.724 | 0.674 / 0.560 (canon: 0.708 / 0.553) |
| syn hybrid | 0.726 | 0.791 | 0.746 / 0.805 |

Tree addressing transforms tasks whose difficulty is structural
alignment (xlang: +22 test, +16 OOD, beating even gold-interlingua
canon -- related constituents in the two languages get related
coordinates, so comparison is aligned rather than learned) and is
neutral where the residual is lexical (syn unchanged). The interface
contributes exactly what it encodes; the division of labor stays
clean.

## Next

1. Tree-structural positional encoding for solvex OOD (in progress).
2. Binding category-compatibility constraints for specialize.py noise.
3. Prover phase 1: LeanDojo-v2 native-Windows attempt (WSL2 only if
   Lean tracing forces it).
4. Ingest Rasmussen-Schuler LREC2020 corpus (2k sentences + lambda
   forms) as the real language-logic bridge.


## Scaling grid: emergence curves for depth generalization

16 cells: width {32,64,128,256} x data {10%,100%} x positions {abs,tree},
solvex (pure structural pointing after the shortcut audit), single seed
per cell (trend claims only).

| width | data | abs test/OOD | tree test/OOD |
|---|---|---|---|
| 32 | 10% | 0.243 / 0.050 | 0.932 / 0.964 |
| 32 | 100% | 0.955 / 0.183 | 1.000 / 0.995 |
| 64 | 10% | 0.501 / 0.043 | 1.000 / 1.000 |
| 64 | 100% | 0.994 / 0.187 | 1.000 / 1.000 |
| 128 | 10% | 0.836 / 0.125 | 1.000 / 0.990 |
| 128 | 100% | 1.000 / 0.178 | 1.000 / 0.946 |
| 256 | 10% | 0.969 / 0.137 | 1.000 / 1.000 |
| 256 | 100% | 1.000 / 0.186 | 1.000 / 1.000 |

The curve answer: under absolute positions OOD is FLAT (~0.05-0.19)
across 8x width and 10x data -- scale buys in-distribution accuracy and
zero extrapolation; there is no knee to wait for at these budgets. Under
tree addresses the property is present at every cell including the
smallest (32-wide, 5k examples, ~0.96 OOD). Depth generalization here is
an interface property, not an emergent-with-scale property. For the
model design this is the strongest budget argument yet: the symbolic
interface substitutes for orders of magnitude of scale on exactly the
capability the 64MB target cannot buy with parameters.


## solvex-v2 verdict: recombination re-established, on an audited instrument

Content load-bearing (K=3 distractor KB, dictionary on the critical
path), held-out verb x noun combos, 2 seeds:

| positions | val (seen) | test (held-out combos) | OOD (deeper) |
|---|---|---|---|
| abs | 0.29 | 0.25 | 0.06 |
| tree | 1.000 | **1.000 / 1.000** | 0.69 |

- The retracted v1 claim returns in a stronger, sound form: with
  symbolic tree addresses the model composes seen parts into never-
  seen-together combinations PERFECTLY, on a split whose capability-
  blind floor is verified at 0.31.
- Under absolute positions the model cannot even learn the SEEN cases
  (0.29 = floor): on multi-statement input, structural addressing is
  not a robustness aid but a precondition for the compositional
  learning problem to be tractable at all.
- Honest headroom: depth OOD is 0.69 on v2 (vs 0.97 on the pure-
  pointing v1) — deeper KBs with distractors remain open.


## Generation attempt 1 (answer-tree decoder): informative failure

Naive seq2seq (tree-path encoder + 2-layer autoregressive decoder over
concept tokens), exact-tree match, 2 seeds: test 0.107/0.022, OOD ~0.00
-- against 1.000/0.69 for span-pointing on identical data. The failure
is in-distribution, so it is not recombination breaking: a small
decoder has no reliable mechanism to COPY variable-length content
through cross-attention, even content the encoder demonstrably
localizes perfectly.

The architecture prescribes its own fix, and it is the component the
project's original sketch contained: a pointer-generator. Generation at
this scale should emit pointer actions into the input (proven at 1.000)
plus rare vocabulary tokens for structure, with the extrinsic lexicon
translating pointed surface words to concepts deterministically.
Creating = iterated pointing + symbolic realization. Queued as the next
build.


## Generation attempt 2 (pointer-generator) and the resolution

Pointer-gen (GEN/COPY actions, grounded copy embeddings): val 0.44 on
seen combos but 0.038 on held-out — it memorizes content associations
where the span head composes. Both learned decoders fail the same way.

The resolution is better than fixing the decoder: for extractive
answers NO learned decoder should exist. The span head finds the
constituent (1.000/0.69, compositional); parsing the span,
canonicalizing, and inverting the lexicon are closed-form; the renderer
realizes the tree in either language. demo_answer.py runs this pipeline
end to end: foreign question + KB in, fluent answer out in both
languages, every generated word either pointed-at or produced by exact
code. Creating-by-pointing is complete for extractive tasks.

The measured boundary of the creating question, for v0.2: learned
generation is needed exactly where the answer exists nowhere in the
input — non-extractive synthesis (analogy completion: emit F = m*a
given Ohm : circuits :: ? : mechanics, verifiable against
specialize.py bindings). Both decoder failures say that frontier will
need its own mechanism, not a bigger decoder.


## realsyn (first real-data task): the prediction that favors char, confirmed

Same-lemma detection on real Spanish Wikipedia morphology (9,208 lemmas,
lemma-disjoint splits, hard prefix-sharing negatives), char arm, 2 seeds:
test 0.959 / OOD 0.811 (OOD = the 460 highest-fanout paradigms).

The same encoding that sits at exact chance on every structural task
learns real morphology well -- because here the signal is surface-
visible and the repo has no closed form for lemmatization of unseen
forms. This is the thesis's honesty check passed in the other
direction: weights are not weak, they are for the residual, and when
the residual genuinely lives in the surface they own it. The division
of labor is symmetric, and both halves are now measured.

## Analogy completion: non-extractive creation composes

A : B :: C : D with B = f(A), C a re-skinned A, D = f(C) existing
nowhere in the input. Pointer-only decoder (structure from B, fillers
from C; no free-generation steps). 2 seeds:

| | val | test (held-out transform x skeleton) | OOD (deeper) |
|---|---|---|---|
| absolute decoder positions | 1.000 | **1.000 / 0.9998** | 0.014 |

- **The creating frontier is crossed at trained depth**: the model
  produces trees that exist nowhere in its input, on combinations never
  seen together, at ~1.5M params — because the factorization leaves
  only the analogy itself (the A<->C correspondence across
  vocabularies) to be learned, and closes the free-generation channel
  that sank both prior decoders.
- The OOD collapse is the absolute-position failure in a NEW location:
  the decoder's target-position embedding. Deeper trees mean longer
  action sequences into untrained positions. Fix in flight, by the
  house pattern: decoder positions = the target's own tree coordinates,
  computable incrementally from the emitted prefix's bracket structure
  even at inference.

### Analogy depth wall: three probes, one identical failure set

Absolute positions, decoder tree-coordinates, and tied encoder/decoder
path embeddings all yield OOD = 0.0139 — the SAME 34/2450 examples
succeed under every mechanism and seed. A bit-identical failure set
across architectures means the wall is not positional encoding: the
determinant lives in the data-model relationship (suspects: a shared
structural constraint making most deep examples unlearnable as encoded,
or cross-segment correspondence breaking at scale). Next step is a
diagnostic, not a fourth mechanism: per-step teacher-forced error
localization on OOD (structure vs leaf steps, early vs late). Queued
for v0.3's experiment 3; length was already ruled out (95.4% of kept
OOD targets are within trained length range).

### The depth wall, solved as a diagnosis: 34 = 34

Teacher-forced per-step diagnosis (diagnose_analogy.py) on the fresh
checkpoint: OOD failure is immediate (88% of first errors in the first
two deciles), C-leaf selection collapses to 0.139, EOS is perfect --
so neither drift nor length. The unified account: trained trees reach
tree level 5; path embeddings are per-level LOOKUP rows; tokens at
levels > 5 carry untrained rows. Verification: exactly 34 kept OOD
examples stay within level 5, and exactly those 34 succeed --
bit-identically across absolute, tree-coordinate, and tied-path
mechanisms, which all shared the same per-level lookup and therefore
could not differ. C-leaf steps fail worst because leaves live deepest;
solvex survived depth because span targets sit at shallow levels.

Prescription (v0.4): the address ENCODING must generalize over depth --
functional level codes (sinusoidal levels, or path-recurrent
composition where level k+1's code derives from level k's) instead of
enumerated embedding rows. The interface catalogue's addresses entry
gains a requirement: closed form over depth, not a table.

### Sinusoidal prescription falsified: the consumer is depth-naive

Closed-form level codes (shared sib table x fixed sinusoidal level
modulation; no depth-indexed parameter anywhere) moved OOD only 0.0139
-> 0.0218 (2 seeds; test unchanged). The 34=34 diagnosis correctly
located the failure boundary, but untrained rows were symptom, not
cause: making deep levels REPRESENTABLE does not teach the network what
to DO with codes never active during training. The transformation
consuming the addresses is itself depth-naive.

This is the syn lesson from the opposite direction -- defined is not
integrated -- and it forks the v0.4 depth item into a design choice:
(a) curriculum exposure to deeper trees (teaches the consumer, but
redefines what OOD means and must be labeled as such), or
(b) architectural recurrence over levels (process paths level-by-level
with shared weights so depth is iteration, not vocabulary -- the
recurrent instinct from the project's original sketch returning in a
precise, motivated role). Both carry to v0.4 as a decision point.

### Depth fork verdict: exposure does not generalize; iteration does

| arm | train depths | OOD depths | OOD exact |
|---|---|---|---|
| table lookup (baseline) | 2-3 | 4-5 | 0.014 |
| table + curriculum | 2-4 | 5-6 | **0.006** |
| recurrent (GRU over levels) | 2-3 | 4-5 | **0.226** |

Curriculum FAILED: deeper exposure with lookup addressing just moves
the cliff one level out -- the consumer memorizes the levels it sees
and falls off the same edge. The recurrent arm, with LESS exposure, is
the only mechanism showing true extrapolation (16x over baseline).
Depth-as-iteration -- one shared cell applied once per level -- is the
direction; the open work is closing 0.226 -> 1.0 (deeper recurrent
integration: the pointer/decoder still consume addresses through
depth-naive attention). The original architecture sketch's recurrent
instinct survives its controlled test.

## v0.5 oracle-first controller baseline

Prediction registered in `docs/ROADMAP-v0.5.md`: before a learned policy, one
deterministic controller must execute a three-step derivation and a three-beat
story, with capability-blind negative controls so an accept-everything verifier
cannot satisfy the milestone.

Command:

```
PYTHONIOENCODING=utf-8 python scripts/oracle_controller_demo.py
python -m unittest discover -s tests -v
```

Result: **PARTIAL PASS, 16/16 contract tests.** The same generic controller
replayed three contiguous machine-extracted Lean transitions for
`BooleanLaws.absorption_or_and`:

```
intro hp  -> left -> exact hp -> no goals
```

and executed the golden-chicken frame's setup, complication, and resolution.
Each accepted step supplies a next state; each rejected step is recorded but is
forbidden to mutate accepted state. Repeating the same rejected action at the
same state is pruned. A rejected resolution-before-setup branch followed by the
valid three actions still solves, proving the dead branch did not become a
premise.

The vacuity controls all failed as predicted: an unrecorded tactic, the right
tactic at an altered Lean state, a resolution before its setup/complication,
and changing the declared golden trait to silver. The Lean adapter therefore
does exact membership/replay over `prover/sample_triples.json`; it does not
accept arbitrary text. The story adapter enforces beat order, the desire shared
by all three authored narrative nodes, and declared frame traits.

Honest boundary: this proves the controller interface and oracle integration,
not a general solver. Only `GEN` has executable adapters. The Lean path replays
previously machine-extracted transitions; it does not call PyPantograph live and
does no search. The story path implements the smallest three-beat/frame-trait
subset, not the scope schema, temporal liveness checking, retrieval, ASK, or
WRITE. No learned policy chooses any action yet.

The pre-commit review supplied an additional adversarial control the frozen
demo states had hidden: a verifier receiving a mutable list could mutate it in
place and return REFUTED, leaking the dead branch into accepted state despite
`next_state=None`. The controller now copy-isolates state at every policy,
goal, verifier, trace, and result boundary; the exact mutation reproducer is
the eleventh test. A second review found the same opening in `state_key`; that
hook is now copy-isolated and its reproducer is test twelve. Tests thirteen and
fourteen exercise mutating goal and policy callbacks, completing the extension-
boundary audit. This deliberately favors correctness over large-state
performance while controller states are small symbolic records.

The final review caught two status shortcuts. First, `--triples` accepted an
arbitrary JSON file, so a fabricated transition ending in the literal
`no goals` could receive PROVEN. PROVEN is now gated by the SHA-256 identity of
the committed machine-extracted artifact; a structurally replayable but
untrusted input can finish only as VERIFIED. Second, any trait absent from the
frame declarations was called REFUTED, confusing lack of evidence with a
contradiction. Frame state now carries explicit declared and denied traits:
`silver` is REFUTED because this frame denies it, while undeclared `brave` is
UNKNOWN. The two adversarial cases are tests fifteen and sixteen.

### Frame executor and finite Chekhov obligations

The next registered prediction was that a planted element would create one
frame-local obligation under `narrative.constraint.chekhov_gun`, a matching
discharge would close it, and `close_frame` would REFUSE without mutation or
demotion while anything remained outstanding. The deliberately asymmetric
negative control predicted that an unplanted discharge would be UNKNOWN rather
than REFUTED: Chekhov's authored future-facing implication cannot prove its
past-facing converse.

Result: **PASS, 55/55 contract tests after integration.** The immutable frame
state now carries an obligation ledger. `GEN(plant)` and `GEN(discharge)` run
through the same Controller/Verification contract as assertions, story beats,
and Lean replay. Duplicate plants are idempotent; an unrelated discharge does
not alter the ledger; closed frames refuse temporal events; and a refused close
returns the exact still-open state with no demotions. Once every element is
discharged, close succeeds and the existing frame-truth demotion rule runs.

The first implementation failed its vacuity audit before review: it was
possible for the hidden ledger to say “feather planted” while the rendered
setup never mentioned a feather. The story adapter now requires the plant to
amend an existing visible beat and requires discharge evidence to occur in the
rendered resolution. The golden-chicken oracle therefore executes five
verified transitions while retaining three story beats: introduce, visibly
plant the fallen feather, obstruct, resolve using the feather, and discharge.
Its completion predicate requires both the three-beat sequence and a nonempty,
fully discharged ledger.

Independent review then broke the visible grounding in two more ways: it moved
the plant after the resolution with unrelated prose, and repeated an otherwise
idempotent plant to duplicate the setup sentence. Planting is now setup-only,
both plant and discharge evidence must name the bound element, and a duplicate
plant changes neither the obligation ledger nor the rendered beat. Both
review reproducers are permanent negative controls.

A second review found that event-id uniqueness depended on obligation order:
an early same-element idempotence return could hide a later obligation using
that event id for another element. Conflict detection now scans the whole
ledger before any idempotent return, and event ids cannot change kind between
plant and discharge. The exact two-obligation ordering reproducer and both
cross-kind collisions are covered.

A third review showed that “duplicate” was underspecified. A fresh id for an
already-planted element had been accepted as idempotent without being recorded,
so the same id could later identify a discharge. The corrected contract is
narrower and auditable: only the exact same event-id retry is idempotent; a
fresh id for an element whose plant or discharge is already bound is REFUSED.
The earlier broad wording is corrected in the roadmap, and the fresh-id case is
now an explicit negative control rather than being counted as a pass.

Honest boundary: this is finite obligation accounting at frame close, not a
general LTL model checker. It executes the one authored
`ALWAYS(PLANTED(e) -> EVENTUALLY(DISCHARGED(e)))` use case. It neither derives
past facts nor refutes an unheralded outcome; the now-authored heraldry pattern
and no-deus-ex-machina converse are not yet wired into the executor. Scoped
corpus nodes now exist, but no learned policy chooses these temporal
transitions.

## v0.5 past modality, mirror relation, and first scoped nodes

Prediction was registered in `scripts/seed_temporal.py` before authoring,
regeneration, or matching. The nine design entries expanded to ten nodes
because cartoon gravity is a declaration/assertion pair. The structural
prediction fired exactly: 199 -> 209 nodes; the existing
shape/typed/family/aliased counts stayed 28/29/28/30; and a separately reported
mirror level contains exactly five mirror-only groups (UNTIL/SINCE,
EVENTUALLY/ONCE unfolding, NEXT/PREV distribution, future/past duality, and
response/heraldry). Zero mirror pairs leaked into typed twins. Replacing the
false `BEFORE ~ LEQ` alias with `LT`, plus strict-part/reflexive-closure entries
in `HEAD_ALGEBRA`, moved no prior membership.

The groundedness prediction missed in both directions. SINCE unfolding scored
0.667 and ONCE unfolding 0.500, not 1.000: recursive self-head exclusion leaves
other unrecognized compounds in the denominator. No-deus-ex-machina scored
1.000, not 0.500, because its PLANTED/DISCHARGED constituents recur exactly and
the heraldry pattern covers the whole instance. The corpus mean is now 0.768.
This is evidence about the metric boundary, not grounds to rewrite the
prediction after seeing it.

Specialization moved 622 -> 626 edges (538 cross-discipline). Two additions are
the intended semantic links: response-pattern -> cartoon-gravity and
heraldry-pattern -> no-deus-ex-machina, each cost 4. Two are noise:
`de9im_disjoint` -> `strict_part_of_order` and ->
`prev_distributes_over_meet`, each cost 7. The first scoped nodes validate as a
shared cartoon-gravity frame plus premise persistence. The matcher deliberately
ignores scope, so scope changed execution/validation semantics without changing
structural identity.

Independent review invalidated the first apparent five-group result. The
initial matcher quotiented each modal head independently, so a partially
reversed nested formula could look mirrored; the authored heraldry pattern
also changed EVENTUALLY to ONCE while incorrectly retaining outer ALWAYS.
With a true whole-tree involution that corpus produced only four groups. The
past formulas were corrected to HISTORICALLY and the matcher now keys each
statement by the orbit of its typed skeleton and its globally reversed
skeleton. An adversarial mixed formula (`HISTORICALLY(EVENTUALLY(P))`) is a
permanent negative control. The corrected five-group result is the claim; the
first result is retracted.

The same review refuted a hand-authored entailment in the scoped example:
`G(notices -> F(falls))` does not entail `not notices -> not falls`. The hover
is now an independently assumed frame assertion, with no reciprocal entailment
links. Scope agreement remains the point of the pair; a false causal inference
is not smuggled in to make it a derivation.

A later semantic pass tightened three more boundaries. PREV is now explicitly
strong (false at the trace origin), which is required for the authored
SINCE/ONCE recurrences. The exact response/heraldry mirror is intentionally
inclusive—ONCE means at or before, so strict earlier preparation remains an
executor/event-order responsibility. And opening-premise persistence is a
positive `ALWAYS(MEET(HOLDS(p), SINCE(HOLDS(p), opening)))` obligation; the
earlier implication became vacuously true if the premise disappeared and is
retracted. The node is explicitly restricted to opening declarations rather
than later accepted assertions.
