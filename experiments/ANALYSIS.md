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

## v0.5 public ladder / frame-executor integration

Prediction was registered in `docs/ROADMAP-v0.5.md`: without changing corpus
or matcher output, the public `compose_assert.py` demo would source an exact
runtime sequence from `FrameExecutor`—VERIFIED declaration, REFUTED
contradiction, UNKNOWN missing trait, UNKNOWN suspended contradiction before
admission, VERIFIED admission, VERIFIED clean close with conjectured exit
demotions, then REFUSED post-close check. It fired exactly. Two tests assert
both the ordered verdicts and their rule/world/frame evidence. The existing
global PROVEN/HYPOTHESIS/REFUSAL examples remain separate because the frame
executor should not manufacture machine-proof or structural-family status.

## v0.5 UNKNOWN-triggered retrieval adapter

Prediction was registered in `docs/ROADMAP-v0.5.md` before implementation. A
read-only loader produces 702 pointable records from the committed local world:
209 corpus statements, 209 node-lexicon summaries, 67 twin/family/alias/mirror/
shape groups, 208 decomposition records, and 9 statement-level proof summaries
that inspect the referenced native Lean transition artifact. No corpus or
matcher report changes.

The registered exact query `logic.boolean_laws.de_morgan_laws` returns six
items spanning all five source kinds (two structural groups); the truncated
`logic.boolean_laws.de_morgan` misses exact equality and succeeds through the
deterministic token neighborhood. RETRIEVE appends stable positions 0..5 and a
subsequent POINT(0) binds the pending answer slot to the corpus item. Both are
VERIFIED transitions, but the material retains its own status: the corpus node
is `derived`, the structural/decomposition records are mechanically `verified`,
and the proof summary is `proven`. Successful access is not epistemic promotion.

The capability-blind control removes every store item while replaying the same
two-action oracle. RETRIEVE stays UNKNOWN with ABSTAIN evidence, context and
state remain unchanged, POINT is REFUSED, and the controller does not solve.
A session whose own canonical key is absent behaves identically. A
`retrieval: frame_local` state is
stronger: a spy store proves no query runs before REFUSED routes the unresolved
slot to `ASK(slot)`. Three delegated GEN outcomes—accepted, unknown, and
malformed—preserve the underlying frame verifier's verdict, reason, and
evidence exactly. Eleven retrieval tests move the suite 70 -> 81.

Honest boundary: this is an oracle-driven local adapter, not learned tool use.
The neighborhood is an unranked closed-form token relation; external tools
remain unbuilt, and at this 6a result's landing ASK had no return channel (the
later item-10a section records its implementation); POINT binds a retrieved record rather
than implementing every existing-context pointer task; and 702 items are small
enough for a linear scan. Those are the next scaling and policy experiments.

Independent review invalidated the first success control: POINT initially
validated only index existence, so the policy could retrieve modus ponens and
bind it to a De-Morgan slot. The store was load-bearing but answer relevance was
not. POINT now applies the same exact/token-neighborhood relation to the
selected item's aliases and the pending slot's registered key. The adversarial
sequence still retrieves context, but its POINT is REFUSED and the UNKNOWN
remains open. That reproducer is permanent; the original success-only test is
recorded as vacuous rather than counted as evidence. It is the twelfth
retrieval test and moved the full-suite count to 82.

A second independent review found that alias equality could still be vacuous:
the one-letter symbol `a` is an exact lexicon alias for many unrelated nodes,
and the first returned lexicon could bind an `a` slot. POINT now accepts a
matched item only when the corpus, lexicon, and proof views matching the key
resolve to one corpus owner. Retrieval can still expose an ambiguous
neighborhood, but ambiguity cannot clear UNKNOWN. The same review found a
schema mismatch: `verified_by.reference` is optional, while the loader indexed
it unconditionally. Artifact-only proof links now load and report the full
theorem-bearing artifact's transition count. At this review stage they retained
PROVEN status; the later identity and proof-trust controls below narrow that to
single-theorem, digest-pinned artifacts. The two new regression tests bring the
full suite at this stage to 84.

Re-review supplied two interaction controls. `Quadratic Formula` is an exact
title but also a token-neighborhood match for a different node's `quadratic
form`; mixing both match modes made the unambiguous exact result unbindable.
Owner resolution now respects exact-before-neighborhood precedence. Separately,
an accepted frame assertion could turn the pending literal from UNKNOWN to
REFUTED while leaving its old retrieval need pointable. Retrieval needs now
retain the adjudicated literal, and RETRIEVE/POINT recheck it against current
frame state. A stale need is REFUSED rather than clearing the slot. These two
controls originally brought the suite to 86. Final review refined the state
transition: if a delegated GEN makes the literal VERIFIED or REFUTED, that
verdict and evidence enter a resolution ledger and the now-resolved retrieval
need clears. This avoids both stale binding and an unrecoverable pending state.

The next review completed the precedence matrix: context retrieved for
`quadratic form` contained the first-fundamental-form node, which
neighborhood-matched a pending `Quadratic Formula` key. Because the binding
code considered only the selected item's mode, it could ignore the exact
quadratic-formula owner elsewhere in the store. POINT now refuses every
neighborhood binding whenever any exact owner exists for the pending key. The
cross-query reproducer is the seventeenth retrieval test and moves the suite to
87.

Protocol review then tested malformed proof and action inputs. An empty JSON
artifact previously yielded a PROVEN summary with zero transitions because
the absence check ran only when theorem rows existed. JSON proof links now
fail closed unless they contain at least one applicable theorem transition.
Likewise, dispatch had checked only `ActionKind`, allowing arbitrary RETRIEVE
or POINT names to appear as accepted trace operations; only the declared
`lookup` and `bind` names now execute. Both negative controls are permanent,
bringing the suite to 89.

The proof-boundary review went one level deeper: a non-JSON file, or a JSON row
containing only a theorem label, still satisfied file existence while proving
nothing machine-checked. The current adapter therefore authenticates only the
native artifact it understands: JSON rows with theorem, tactic, stateBefore,
and stateAfter strings, including a non-empty theorem and tactic. At least one
applicable transition must close to `no goals`; a well-shaped but truncated
trace is not a proof. Unsupported formats, incomplete rows, and unfinished
traces fail closed instead of receiving PROVEN. The added format control moves
the suite to 90.

Identity and neighborhood review added two more constraints. An artifact-only
link may authenticate a single-theorem artifact, but a shared multi-theorem
artifact cannot establish which theorem proves the statement without an
explicit `reference`; that ambiguity now fails closed. Separately,
reverse-prefix matching let a truncated word such as `absor` match ubiquitous
one-letter aliases such as `a`. Reverse prefixes shorter than three characters
are now ignored. The scoped `logic boolean absor` query resolves and binds the
intended owner without admitting those unrelated lexica. Both controls move
the suite to 92.

The last capability-blind review attacked the origin of the key itself. Before
the correction, a caller could create a De-Morgan UNKNOWN while supplying
`Quadratic Formula` as its suggested key; retrieval and POINT would faithfully
solve the wrong constraint. The session factory now requires canonical key
tokens to equal the unresolved literal's value. A mismatched pair fails before
store access. This moves the suite to 93 and narrows the claim honestly: the
adapter verifies retrieval relative to an already parsed symbolic request;
open-language parsing into that literal remains upstream and unproven here.

Proof-trust review then demonstrated that even an applicable `no goals` row can
close only a focused subgoal in a truncated extraction. Shape and a terminal
sentinel cannot authenticate the whole proof. Retrieval now reuses the Lean
replay adapter's existing SHA-256 trust root for the committed native
`sample_triples.json`: proof material from that exact extraction is PROVEN;
well-shaped, locally closing but untrusted artifacts remain VERIFIED. The new
completed-subgoal control moves the suite to 94.

Finally, session construction alone did not prevent RETRIEVE from substituting
another alias or unrelated key. A De-Morgan pending literal could retrieve by
its prose title and still bind the same record, leaving the action key as free
policy metadata. RETRIEVE now requires canonical equality with the pending
literal before store access. Exact lookup and deterministic neighborhood
widening operate on that fixed key. The alias-bypass control moves the suite to
95.

Public-boundary review then bypassed the factory by directly constructing the
frozen dataclasses with a forged key. Both RETRIEVE and POINT now recheck that
the pending key equals the unresolved literal's value before doing any work.
The proof trust root also now binds metadata as well as bytes: only the
canonical `lean4` system label can use the pinned Lean extraction digest. A
byte-identical artifact mislabeled as another prover is rejected. These two
controls move the suite to 97.

Five-store review then tested keys that exist only in structural reports. A
unique chain-rule constituent retrieved its decomposition record but could not
bind because owner resolution consulted only corpus, lexicon, and proof views.
Binding now uses explicit precedence: canonical statement views when present;
otherwise a unique decomposition owner; otherwise one uniquely matched
structural-group record. The chain-rule decomposition and iterated-composition
twin-group controls both bind, moving the suite to 99.

The final public-state review forged context rather than the key: an invented
item copied valid De-Morgan aliases and ownership while using an item id absent
from the store. POINT previously trusted that dataclass. It now authenticates
the complete selected record against the authoritative read-only snapshot
before applying match or owner rules. The forged-context control moves the
suite to 100.

Closed-form review then found that “exact” equality was still lexical:
`?0 = *(?1, ?2, ?3)` and `?0 = +(?1, *(?2, ?3))` both reduced to the digit
tokens 0/1/2/3, making two distinct committed shape groups ambiguous. Exact
lookup and pending-key equality now normalize only case and whitespace, keeping
every operator; word tokens are used only for neighborhood fallback. Both
skeletons retrieve and bind distinct group records, moving the suite to 101.

Transaction review then injected a genuine store item directly into public
context. Store membership alone could not prove that RETRIEVE had occurred.
The verifier now mints a session-local HMAC receipt over the canonical key,
query mode, and admitted item ids; POINT requires a valid receipt and exact
store membership. A separate short-key control showed `7` prefix-matching
`IEEE 754`; prefix neighborhood relations now require at least three characters
on both sides, while exact short aliases remain available. Both controls move
the suite to 103. Receipt serialization across process/session restart is not
implemented.

Receipt replay review then used one verifier for two same-key sessions and
copied session A's context/receipt into session B. The original signature did
not distinguish them. Retrieval state now has a random session id included in
every receipt signature; cross-session replay is REFUSED. Copying the complete
state remains the same logical session. The replay control moves the suite to
104.

Symbolic-input review then found exact lookup incorrectly gated by the presence
of ASCII word tokens. Exact alias equality now runs first, so a tokenless
closed-form key such as `¬` can retrieve and bind; only neighborhood fallback
requires lexical tokens. The tokenless exact control moves the suite to 105.

Frame-isolation review then preserved a valid session id and receipt while
replacing the open frame with a `frame_local` frame. Receipt signatures now
also cover the immutable `FrameSpec`, so the transplanted context is REFUSED.
The frame-replay control moves the suite to 106.

## Proof-link integrity lint (v0.5 follow-up)

The retrieval review separated two claims that had previously traveled under
one phrase. A digest can authenticate artifact bytes, but it cannot authenticate
the semantic claim that a cited theorem proves the corpus statement pointing
at it. The first, cheap governance rung is now executable in the merged-graph
validator: artifacts must stay inside the repository, exist, decode as
non-empty theorem-bearing JSON, resolve explicit references (or exactly one
reference-free theorem), and give each `(system, theorem)` identity one
statement owner.

The registered live-data prediction fired: nine statements carry 16 distinct
references, all 16 resolve, and none is multiply owned. Twelve fail-closed test
methods exercise eighteen absent, malformed, escaping, ambiguous, empty,
dangling, and multiply owned cases. The capability-blind control is the important result: an unrelated
gravity statement can cite a structurally valid `BooleanLaws.modus_ponens`
reference and this lint accepts it. The test therefore proves the boundary as
well as the feature. Suite: 111 -> 126. Full theorem-to-statement skeleton
comparison remains prover phase 2; until then, `verified_by` is authenticated
provenance rather than a machine-checked semantic edge.

Adversarial review invalidated the first artifact control: its fixture contained
only a theorem-name string, so the lint had authenticated no proof transition at
all. Parsing is now one shared closed-form operation used by validation and
retrieval; every artifact row carries theorem, tactic, state-before, and
state-after strings, and the selected theorem must close to `no goals`. The
false-association control now cites the real digest-pinned extraction. Review
also reproduced two boundary failures: malformed link shapes passed whenever
optional `jsonschema` was unavailable, and the default CLI could not find its
schema/data from a foreign CWD. The fallback now validates link shapes itself,
and repository-anchored defaults work from any CWD. All three failures are
retained as regressions.

Re-review found two narrower mismatches: whitespace-only proof states counted
as complete, and alternate system labels could evade shared ownership even
though retrieval supports only `lean4`. Completeness now requires nonblank
theorem, tactic, before-state, and after-state fields. Until a second parser is
registered, every non-`lean4` system fails validation. The four blank-field
cases and unsupported-system reproducer are retained.

## Conversational ASK return channel (v0.5 item 10a)

ASK is now a real two-transition protocol over the same generic controller as
proof replay, story composition, frames, and retrieval. A parsed UNKNOWN carries
a closed-form resolution channel (`store` or `user`). `ASK(clarify)` on a
user-private need records a verifier-signed question in persistent runtime
`UserFrame` state and stops the controller as WAITING. The next run accepts only
a return-channel signature bound to session, immutable FrameSpec, owner label,
question id, slot, unresolved literal, canonical key, channel, prompt, and
answer. It clears that exact still-UNKNOWN need and records a signed user
binding; it never asserts the answer into frame/world/corpus truth.

The capability-blind result is load-bearing: a policy sees every public action
field but not the verifier's per-instance secret, so a guessed reply is REFUSED
without mutation. Twenty-five controls additionally reject second-verifier,
post-signature mutation, cross-question/session/frame/owner replay, forged
public question/binding/pending state, stale needs, channel confusion, closed
frames, and all non-reply actions while waiting. The durable store is never
queried by ASK. Suite: 130 -> 155; 209 nodes and every structural report are
unchanged.

`scripts/conversation.py` is the first two-turn golden-chicken revision: “make
it lay eggs” leaves `egg_color` user-private, the controller waits and asks, the
host supplies “silver,” and the resumed session renders “Now the golden chicken
laid silver eggs.” This demonstrates symbolic pause/resume and attributable
session memory, not open-English intent parsing or learned prose. The signature
authenticates the host channel, not the human's real-world identity.

Adversarial review found three gaps. First, a consumed signed answer could be
replayed after public state reinstated the identical need and question. A
verifier-private consumed-request ledger now survives public-state rollback,
with request ids mirrored in user-frame state for audit. Second, unsigned
`Action.dependencies` could be added after reply signing; both ASK transitions
now require none. Third, the original demo began from a fresh empty FrameState,
so its “existing story revision” claim was vacuous. It now begins with the real
accepted three-beat `StoryState`; all beats and its discharged obligation remain
unchanged across both turns and are included in the revised rendering. Each
review reproducer is retained.

Re-review found a transaction-order defect: `_reply` consumed its private nonce
during speculative evaluation, before the controller's goal callback completed.
If that callback raised, no accepted state returned but retry was refused.
Controller termination now has an optional run-level commit hook; completion
and WAITING callbacks run first, then the retrieval verifier atomically commits
all accepted reply ids immediately before `RunResult` returns. The exact
exception-and-retry control proves an uncommitted answer remains usable while a
returned run remains replay-resistant. Suite: 155.

## Physical reference frames (v0.5 item 10b, first cut)

Four source-grounded physics nodes move the corpus 209 -> 213: inertial-frame
definition, Galilean velocity addition, Galilean acceleration invariance, and
a uniformly rotating-frame declaration. Only the rotating statement is scoped;
the two Galilean transformations are claims *about* relationships among frames,
not claims local to one frame. The rotating declaration suspends the explicit
inertial-frame criterion and admits centrifugal/Coriolis corrections locally.

The two registered predictions split. P-CF3 fired exactly: Galilean velocity
addition and `algtop.homology.chain_rank_nullity` share the typed skeleton
`?0:V = +(?1:V, ?2:V)`. P-CF2 missed at shape, typed, family, aliased, and
mirror levels. The miss is load-bearing: rotating dynamics is honestly a
three-term additive correction; cartoon gravity is honestly a temporal
liveness rule. Their commonality lives in scope metadata and executor rules,
which the signature matcher deliberately ignores. Rewriting either template
to force a twin would erase the result.

Matcher counts move 28/29/28/30/5 -> 29/30/29/31/5, entirely from the new
Galilean pair; mirror remains 5 and ladder violations remain zero. Decomposition
reports 185/213 statements with known forms and mean groundedness 0.762.
Specialization moves 626 -> 655 edges (566 cross-discipline). All 29 new edges
touch Galilean addition or the rotating-frame additive law; their cheapest
members are reasonable additive-arity specializations, while the costlier tail
remains analogy-like and is not counted as proof of physics transfer.

The slice also resolves the frame-id ambiguity exposed by the first scoped
nodes. `scope.frame` now resolves to the scoped declaration node with that same
`statement_id`; missing, unscoped, and assertion-owned ids fail validation.
This uses declaration nodes as the minimal frame registry and defers a second
artifact until metadata duplication demonstrates a need. Suite: 155 -> 158.

## Owned frames and visibility-derived false belief (v0.5 item 10c)

P-CF1 fires without a new epistemic verdict. `scope.owner` is the only corpus
schema addition: an owner-scoped Sally belief declaration and an unscoped
post-move world assertion validate in the merged graph. Runtime `FrameEvent`
records explicit effects plus `witnessed_by`; placement reaches Sally, Anne,
and world, while movement reaches only Anne and world. The resulting query is
Sally=basket and world=box. World also REFUTES basket because movement carries
both denial of the old location and assertion of the new one.

Eight focused controls cover the acceptance path, Anne's true belief,
unwitnessed-event visibility forgery, observed-event idempotence/collision,
unowned event refusal, persistent owned-frame close refusal, runtime/corpus
namespace separation, and malformed owner/event metadata. Missed event ids are
recorded without hidden effects, preventing later witness-set rewriting.

The corpus pair also forms a typed LOCATION twin; that is content evidence,
not theory-of-mind evidence. Counts move 213 -> 215 nodes and
29/30/29/31/5 -> 30/31/30/32/5. Specialization remains 655. Retrieval grows
715 -> 723 items. The suite moves 158 -> 173. ASK bindings deliberately remain
session-long; owned FrameState beliefs persist until a witnessed event
supersedes them. Unifying those two stores and nested belief frames remain open.

Adversarial review found three coupled representation defects. A witnessed
event filtered only `state.asserted`, leaving declaration-backed beliefs stale;
the validator allowed an assertion to introduce owner when its declaration had
none; and every positive effect silently replaced all same-predicate values,
including non-functional traits. The corrected state records superseded
declaration ids, declaration nodes are the sole origin of corpus ownership,
and `FrameEvent.functional_predicates` makes replacement explicit and
validated. Exact declaration-backed movement, assertion-owner introduction,
multi-valued trait preservation, and invalid functional markers are retained.
Independent re-review found two additional coherence holes: explicit
`owner: null` bypassed the dependency-free schema fallback, and an event could
carry both polarities of one atom with tuple-order semantics. Owner presence is
now distinguished from omission, and contradictory event effects fail during
`FrameEvent` construction. Both exact attacks are permanent regressions.
A final review found the neighboring order-dependence: one event could assign
two positive values to the same declared functional key. Construction now
requires a unique positive target per subject and functional predicate while
still permitting the explicit old-value denial plus new-value assertion used
by movement events.
## Optional WordNet retrieval store (v0.5 item 10d)

P-CF6 tests whether an external lexical graph increases request-term coverage
without changing symbolic truth. `scripts/wordnet_eval.py` fixes eight held-out
terms and expected corpus owners. The five committed stores score 0/8; the
Open English WordNet 2025 same-synset bridge puts the expected owner in context
for 8/8. Safe binding is 7/8: `perseverance` has two supporting synsets and is
refused without a sense cue. Across the same eight actual RETRIEVE→POINT (or
ambiguity-refusal) paths the frame executor changes 0 verdicts and 0 evidence
tuples. A capability-blind injected frame mutation is detected 8/8.

The external archive (SHA-256
`7d749f6e2c39e6970e4997839dcf6e42fd281f3c2fae0171d2192bae8cfa4b51`)
contains 107,519 parsed synsets and 127,311 indexed entry lemmas. It is never
copied into git. Each dynamic retrieval record is `empirical`, includes the
archive digest as provenance, and remains weaker than adjacent corpus/proof
records. Exact and token-neighborhood project matches run first. A unique
same-synset bridge may POINT-bind; an ambiguous bridge only expands context.
The five-store absence control is object-identical when the optional path is
missing. This is lexical coverage, not proof and not general semantic search.
The regression suite moves 173 -> 183.

Adversarial review found that the first implementation pooled senses and the
first verdict counter compared an untouched frame to itself. The corrected
binding rule requires one supporting synset (and one sense for a bare lexical
binding); the corrected adjudicator exercises the verifier and keeps the 7/8
safe-bind result public.
Re-review found two failure-path defects: WordNet ambiguity could shadow an
existing exact project alias during POINT, and the evaluator crashed when a
valid archive missed. The pre-WordNet binding contract now runs first for
project items; a fixture where the same item is both exact and lexically
bridged is retained. Missing results now remain reportable failed
adjudications.


## Masked skeleton modeling (10e): a stabilizer, not a lever -- and a seed correction

BERT's masked-LM objective transposed to structure: mask one tree node,
recover it by pointing into a candidate bag (pretrain_maskskel.py); the
pretrained encoder (embeddings, recurrent path cell, transformer, pointer
query) warm-starts the recurrent analogy arm via --init-encoder.
Pretraining data was ONLY trained-depth trees (the P-CF5b contamination
control). 150k trees, 3 epochs, 51.8% held-out masked recovery, 137s.

| arm | seed | test | depth OOD |
|---|---|---|---|
| cold recurrent (committed v0.4) | 0 | 1.000 | 0.226 |
| cold recurrent (new) | 1 | 1.000 | **0.087** |
| warm (maskskel init) | 0 | 1.000 | 0.215 |
| warm (maskskel init) | 1 | 1.000 | 0.187 |

**Adjudication of P-CF5a -- PARTIAL, and the honest reading cuts both
ways.** In-distribution is at ceiling everywhere, so any effect is OOD by
construction. The warm mean (0.201) exceeds the cold mean (0.157), but
the difference (+0.044) is smaller than the cold arm's own seed spread
(0.139), so NO mean-improvement claim survives the no-single-seed rule at
n=2. What the data does support: pretraining collapsed the seed spread
from 0.139 to 0.029 and lifted the weak seed by +0.100 -- masked skeleton
modeling is a **variance stabilizer**, not a wall-mover. P-CF5b FIRED:
the control held (no deeper exposure anywhere in pretraining).

**The correction that matters more than the experiment:** cold seed 1 at
0.087 shows the committed 0.226 was a favorable seed. The recurrent arm's
honest 2-seed statement is **0.16 +/- 0.07**. The v0.4 fork VERDICT
stands -- both cold seeds still beat lookup (0.014) and curriculum
(0.006) by an order of magnitude, so iteration-over-exposure is intact --
but "0.226" as a point estimate is retired; the wall's height is noisier
than one seed made it look. This is the house single-seed rule doing
exactly what it exists to do, to our own headline number.

## Live Lean search (v0.6 item 1, capability-blind rung)

The v0.5 proof demo replayed authenticated, committed transitions. This run
replaces replay with live PyPantograph tactic application and puts bounded
breadth-first branch search in the same domain-neutral controller module used
by the other action adapters. The public state contains only a verifier-minted
opaque handle and rendered goal; mutable Lean goal objects remain private.

Held-out target: ``forall (P Q : Prop) (h : P ∧ Q), Q ∧ P``. Its theorem name
is absent from all 155 phase-1 extraction rows. The capability-blind policy is
a fixed, unranked ten-tactic bag, repeated at every state; it is deliberately
not presented as a learned or general enumeration policy.

| arm | solved | expanded states | distinct states | proposals | accepted / rejected |
|---|---:|---:|---:|---:|---:|
| full fixed palette | yes | 9 | 12 | 86 | 11 / 75 |
| no ``h.left`` / ``h.right`` | no (exhausted) | 10 | 10 | 80 | 9 / 71 |

The solution is ``intro P Q h`` → ``constructor`` → ``exact h.right`` →
``exact h.left``. Three ``clear h`` proposals are accepted by Lean but sit
outside the solution path: the search genuinely abandons legal dead branches.
The projection ablation makes the two proof-producing actions load-bearing.

The first registered run missed. With only bare ``intro``, Pantograph rendered
inaccessible names ``P✝``, ``Q✝``, and ``h✝``; both arms exhausted after five
states (45 / 35 proposals). P-LS2 remains recorded as missed. P-LS6 was then
registered before adding ``intro P Q h`` and fired with the table above. The
lesson is an interface result, not a post-hoc success edit: pretty-printed
state text is not necessarily a callable tactic vocabulary.

This clears the live-application, blind-baseline, backtracking, and unseen-chain
rungs. It does not clear v0.6's learned-ranking gate, project-backed imports,
or a benchmark solved-rate claim. On native Windows, PyPantograph 0.3.15's
project loader currently calls POSIX ``printenv`` during ``LEAN_PATH``
discovery; base ``Init`` RPC is live, but the extracted Boolean-laws project
is not yet a live-search environment.

Pre-commit adversarial review found three boundary defects, all fixed with
regressions: eager tuple conversion could materialize an unbounded candidate
bag before enforcing the proposal budget; ignored extra tactic arguments could
change fingerprints and bypass duplicate pruning; and deduplicating only by
rendered goal discarded histories that a learned policy may legitimately use.
Candidate streams are now consumed only up to budget, tactic actions accept
exactly one named argument, and the Lean search key retains tactic history.
A re-review found that solved children were returned before entering the
distinct-state set (11 reported instead of 12) and that the source pin omitted
the post-checkout submodule update; both the metric and reproduction recipe are
corrected here rather than preserving a favorable undercount.

## Tiny tactic ranking (v0.6 item 1, learned rung)

The learned residual is intentionally narrow. A 27,688-parameter byte-GRU
reads at most the final 512 UTF-8 bytes of a rendered proof state and ranks
eight tactic schemas. It cannot apply a tactic, certify a proof, enumerate a
branch, synthesize a binder, or change the candidate vocabulary. Those remain
the live verifier and symbolic controller's work.

Training uses 60 atomic rows mapped from the 155 committed transitions;
multi-tactic blocks and tactics outside the bounded schema set are excluded.
Four complete theorem identities (16 mapped rows) are held out. Three cold
seeds use the same split. The capability-blind controls are the most-frequent
training label and independently shuffled training labels.

| seed | held-out top-1 | shuffled top-1 | live nodes | live proposals | no-projection |
|---:|---:|---:|---:|---:|---|
| 0 | 0.8125 | 0.250 | 8 | 71 | exhausted, 10 / 80 |
| 1 | 0.8125 | 0.375 | 7 | 63 | exhausted, 10 / 80 |
| 2 | 0.8125 | 0.375 | 7 | 61 | exhausted, 10 / 80 |
| global frequency order | 0.4375 | — | 7 | **64** | not rerun (same projection removal) |
| arbitrary palette | — | — | 9 | 86 | exhausted, 10 / 80 |

P-TP1 through P-TP4 fire against their registered controls. Learned ordering
reduces live proposals from the arbitrary palette's 86 to a three-seed mean of
65.0 at the same 64-state / 512-proposal budget. Every seed finds the same
four-step kernel-checked proof. Each
checkpoint is 114,433 bytes, far below both the 1 MiB registered ceiling and
the project's 64 MB aspiration.

**Corrective P-TP5 MISSED; live learned-gain claim retracted.** Review asked
the cheapest stronger question: what if the training-label frequencies rank
the same palette globally, with no access to the current state? That policy
solves in 64 proposals. Two learned seeds beat it (63, 61), one loses badly
(71), and the learned mean (65.0) is one proposal worse. There is no
three-seed live efficiency gain attributable to state-conditioned weights.
The 86→65 comparison measured a weak arbitrary ordering control. The 0.8125
theorem-held-out classification result remains real, as do the shuffled and
projection controls, but it did not translate into a mean search win here.

The important limitation is breadth. The live palette is ten concrete tactics
grouped into eight schemas, the theorem is one small `Init` proposition, and
the all-data checkpoint has seen only 60 usable states from 16 Boolean-law
theorems. Stable seed agreement does not turn this into a general prover. The
result establishes something narrower: the tiny model learns held-out schema
regularities, while a one-table frequency prior is at least as effective on
this single live proof. Next evidence must add project imports, many
held-out theorems, solved-rate curves at fixed budgets, and eventually action
choice beyond `GEN(lean_tactic)`.

Pre-commit review found that the first runner serialized the earlier blind
number instead of recomputing it beside each live experiment. The number was
correct here, but the comparison path was not self-auditing and could drift
under another budget. The runner now executes blind search in the same live
invocation and records its full trace counts. Review also found that a default
non-live run could overwrite the canonical live artifact; live and non-live
defaults now have distinct paths. Both attacks are permanent regressions.
Re-review then found the missing frequency-ranked live control; it beat the
learned mean and forced the public P-TP5 miss above. This is why capability-
blind baselines are run before model conclusions, even when the model metric
itself looks strong.

## Maintained user frames (v0.6 item 2)

The v0.5 ASK demo proved one pause and signed return. The v0.6 runtime retains
that verifier and accepted state across goals. Two owners begin from the same
public golden-chicken story; Alice binds `egg_color=silver`, Bob binds
`egg_color=blue`, and their renderers diverge while both copies of the public
story and both `frame.asserted` tuples remain byte-for-byte unchanged. This is
the release gate's maintained multi-turn demonstration, not two independent
prompt wrappers.

A third turn tests correction rather than accumulation. Alice reopens the same
UNKNOWN and replies `copper`. Her session id and story beats remain fixed;
both signed answers stay in her user-frame history; the silver request id moves
to an explicit superseded ledger; rendering selects copper. Supersession is
not trusted merely because its id appears in public state: `commit_run` records
it in verifier-private state, and a regression deletes the public marker and
new binding yet still cannot resurrect the old signed answer.

P-CR1–P-CR3 fire. The honest boundary is restart: bindings have an explicit
`session` lifetime, but signatures and the authoritative supersession ledger
are process-local. Serializing dataclasses without a key-lifecycle protocol
would create plausible-looking but unauthenticated memory, so durable resume
remains open rather than silently pickling the secret.

Adversarial review found that authenticating the bindings being revoked was
not enough: the first implementation still selected *which slot* to revoke
from forgeable public metadata. The exact current-request cross-slot forgery
now has a regression. `commit_run` derives the slot only from the authentic
new binding, then revokes only authentic older bindings for that slot. The
second review reproduced both forgery variants and found no remaining defect.

## Corpus-grounded analogy (v0.6 item 5)

The first grounded lane composes two facts already in the audited graph. A:B
is one committed cheapest-specialization edge; A:C is one typed twin crossing
disciplines. The transfer renames B's surviving slots into C's vocabulary,
forming D, and then asks the specializer afresh whether C:D holds. Rows are
admitted only when bindings are unambiguous slot renames plus numeric
substitutions and D is absent from every authored template.

That produces 40 quadruple rows spanning six source and six target disciplines,
but only one structural family (the ratio skeleton) and five distinct D
equations. All five are novel and every row is independently specialization-
accepted. The full symbolic resolver is 1.000 exact by checked construction.
Crucially, a capability-blind rule—take the one number newly visible in B and
replace C's last slot—also scores **1.000**. This first lane is therefore too
regular to test learned analogy. Copying C and retrieving the nearest authored
template score 0.000 exact, but review correctly identified those as novelty
sanity checks forced by admission, not capability baselines; nearest mean
character similarity is 0.773. The specialization ledger is load-bearing:
replacing it with an empty control yields zero quadruples.

The released `analogy_maskskel_s0` checkpoint is missing 16 literal corpus
tokens including the equality head. The evaluator derives that refusal from
the loaded vocabulary (a complete synthetic vocabulary control returns
AVAILABLE) rather than hard-coding it. For the legitimate learned
residual, the equality shell remains symbolic and the checkpoint sees
normalized A/B/C right-hand expression trees using only its exact training
vocabulary. Its exact score is **0.000**, versus 1.000 on its synthetic heldout
task. Retrospective P-CA3 is supported as a negative result: five learned synthetic
whole-tree transforms did not teach numeric slot specialization, even though
both tasks share the pointer realization mechanism. Because the blind baseline
solves this lane, the zero is a domain-gap observation, not evidence that the
corpus task is intrinsically hard.

P-CA1–P-CA4 are retained as retrospective labels: they were written in the
working tree before the run but not committed separately, so there is no
auditable preregistration and the ledger does not call them predictions. The
observed results meet the modest release gate—one
cross-discipline recombination whose absent output is checkable—but not the
roadmap's broader split ambition. Family holdout is refused because only one
family survives the strict admission rules; literal-vocabulary evaluation is
refused because the fixed checkpoint vocabulary has no honest unknown token.
The next grounded dataset must add compound-expansion source leaves and enough
families to train and hold out families separately.

## Visual-structure release-gate adjudication (v0.6 item 8)

The release gate permits either the first experiment or an evidence-backed
deferral. v0.6 takes the deferral. A repository-wide inventory found no SVG or
TikZ assets, no diagram renderer, no source-scene-graph schema, and no exact
geometry verifier. README, design, roadmap, and blog text discuss the proposed
lane; the only corpus occurrence is prose explaining why a three-variable
information diagram can mislead. In other words, none of V1's ground-truth
layer exists yet.

The protocol requires the source graph and deliberately inconsistent diagrams
before the parsed-vector and raster arms, because those artifacts define both
the oracle ceiling and the verifier ablation. Building all four together just
to satisfy a release checkbox would make the tests self-confirming. P-V1–P-V4
remain registered and unadjudicated. The next milestone is intentionally
non-neural: render one right-triangle family deterministically, preserve its
slot-to-element graph, generate one controlled-invalid counterpart, and prove
the exact geometry checks distinguish them. Model comparison begins only after
that foundation survives review.

## Visual oracle layer: the deferred foundation, built (v0.7 item 8, steps 1-5)

The v0.6 deferral named five missing artifacts. All five now exist under
`experiments/visual/`, and none of them contains a weight: this is steps 1-5
of item 8 only. **P-V1-P-V4 in `docs/DESIGN-visual-structure.md` remain
REGISTERED and UNADJUDICATED** — they compare model arms, and step 6 has not
been built.

Seven predictions (P-VO1-P-VO7) were committed in
`experiments/visual/__init__.py` at `c79eade`, before the run that judges
them, specifically so they would not repeat the v0.6 analogy retraction in
which predictions written in an uncommitted tree had to be downgraded to
retrospective labels.

Protocol: `N = 240` seeded valid right triangles (`--seed 11`), one
controlled invalid per class across six classes, 1,680 instances, three
render styles. Regenerate with
`python -m visual.genvisual adjudicate --n 240 --seed 11` from
`experiments/`.

### Verdict: seven of seven fired

| prediction | claim | result |
|---|---|---|
| P-VO1 | verifier accepts every seeded valid | 240/240 — **fired** |
| P-VO2 | rejects every controlled invalid, at exactly its registered check | 1,440/1,440, matrix diagonal — **fired** |
| P-VO3 | every gated check ablates into a specific escape | 6/6 checks — **fired** |
| P-VO4 | render → parse → verify is exact | 5,040 round trips — **fired** |
| P-VO5 | slot ids constant under parameter change | 1 id set, 1 role map — **fired** |
| P-VO6 | the two non-gated checks are verdict-redundant | 0 verdict changes; see correction C1 — **fired, on a narrower base than the wording implies** |
| P-VO7 | no capability-blind surface baseline solves a class | max balanced accuracy 0.742 across all three styles — **fired** |

### The ablation is what makes the verifier non-vacuous

Six checks are gated. Each invalid class is caught by exactly one of them,
and disabling that one check lets all 240 of its class through while the
other five classes stay 100% rejected and all 240 valids stay accepted:

| disabled check | class that escapes | escapes | other classes still rejected | valids still accepted |
|---|---|---:|---|---:|
| `incidence` | `edge_disconnected` | 240/240 | yes | 240 |
| `topology` | `hypotenuse_retargeted` | 240/240 | yes | 240 |
| `right_angle` | `right_angle_epsilon` | 240/240 | yes | 240 |
| `leg_lengths` | `leg_length` | 240/240 | yes | 240 |
| `nondegenerate` | `degenerate_zero_leg` | 240/240 | yes | 240 |
| `right_angle_slot` | `right_angle_mislabeled` | 240/240 | yes | 240 |

The leave-one-in dual is the same result read from the other side: each check
enabled *alone* rejects exactly 240 of the 1,440 invalids — its own class,
one sixth — with zero false rejections, and the six together reject all
1,440. The checks partition the negative set rather than overlapping on it.

An ablation is only readable if disabling one check cannot silently mute
another, so the checks report nothing about relations they cannot evaluate
and the complete registered slot inventory is a *precondition* that raises
rather than a check that votes. Every such silent branch is therefore
unreachable for a graph that got through the door: each check either
evaluates its relation or the graph never reached the verifier. The same
reasoning enforces the parameter contract — with `p == q` the equal-length
near-miss would be collinear with leg a and the right-angle break would fire
`nondegenerate` too, so out-of-contract parameters raise instead of scoring.

That diagonal did not come for free, and two design decisions bought it:

- **The right-angle break preserves both leg lengths exactly.** A
  perpendicular nudge would have changed the leg's length too, so the length
  check would have co-detected it and neither check could have been shown
  load-bearing. Instead the leg direction `v = (-q, p)` is replaced by
  `w = (q, p)`, which has the identical squared length `p^2 + q^2` and makes
  an exact angle of `2*atan(q/p)` with it. Over the direction pool that is a
  1.53°-16.26° near-miss with no floating point anywhere.
- **The degenerate class moves its own claim.** A zero-length leg whose claim
  still asserted a positive length is caught by the length check; adjusting
  the claim with the figure produces a scene that agrees with its own
  description and still is not a triangle, which is precisely what a
  nondegeneracy check is for. It is the only class permitted to touch the
  claim, and the mutation record says so.

Two further checks are implemented and deliberately **not** gated:
`pythagorean` (`|hyp|^2 == |leg_a|^2 + |leg_b|^2`) and `hypotenuse_claim`.
Both are implied by the gated set. Gating them would have given two classes a
second detector and vacated the ablation argument for the checks that earn
their place. **Six checks, six classes, no decoration.**

P-VO6 fired, but adversarial review showed its wording claims a wider
evidential base than it has, and the correction is attached to the
registration rather than folded into it (correction C1). The derived set is
a *superset* of the gated set, so a verdict can only move accept → reject;
every invalid is already a reject, and "never changes a verdict" is a
theorem there, not an observation. Only the 240 valids could ever have
falsified it. The report now also carries the numbers that do have content:
the derived checks fire on 480 of the 1,440 invalids — they are live
assertions, not dead code — and in 0 of those cases does one fire without a
failure of the specific gated check that implies it (`right_angle` +
`incidence` for `pythagorean`; those plus `leg_lengths` for
`hypotenuse_claim`). That, rather than the verdict count, is the evidence
that the exclusion was correct.

### Round trip and the anti-erasure control

`parse_svg(render_svg(g, style))` equals `normalize(g)` exactly for all 1,680
instances in all three styles, and the verifier's verdict *and its
failing-check list* are identical on source and parsed graphs — the parser
preserves violations, not just valid figures. The stronger control is that
`render_svg(parse_svg(svg), style)` reproduces `svg` byte for byte in
5,040/5,040 cases: normalization drops background, colours, fonts, text
labels, angle-marker path data and attribute order, and if any of that had
carried a relation the scene graph does not, the re-render could not
reconstruct the bytes.

### Capability-blind controls, including one on ourselves

P-VO7 fits three surface baselines on the valid corpus and scores them on
that same corpus, so their false-positive rate is zero by construction and
the reading is maximally favourable. Every render style is scored, not just
the default, because byte length is style-dependent: the maxima across all
three are 0.742 for the novelty rule and 0.848 for an oracle-tuned
threshold. Balanced accuracy on `plain`, novelty rule (oracle-tuned
threshold in parentheses):

| baseline | r.a. epsilon | leg length | disconnected | retargeted | degenerate | mislabeled |
|---|---|---|---|---|---|---|
| element count | 0.500 (0.500) | 0.500 (0.500) | 0.500 (0.500) | 0.500 (0.500) | 0.500 (0.500) | 0.500 (0.500) |
| SVG byte length | 0.500 (0.521) | 0.535 (0.621) | 0.508 (0.565) | 0.515 (0.558) | 0.638 (0.802) | 0.523 (0.544) |
| max coordinate | 0.579 (0.510) | 0.740 (0.533) | 0.627 (0.508) | 0.500 (0.500) | 0.623 (0.610) | 0.500 (0.500) |

Element count is at chance on every class because every mutation preserves
the element inventory; `hypotenuse_retargeted` and `right_angle_mislabeled`
are invisible to coordinate magnitude because neither changes one. Nothing
reaches 1.000, so the negative set is not a byte-counting exercise — but
`degenerate_zero_leg` at 0.802 under an oracle threshold (0.848 on the
`sparse` style) is the softest class and is filed in the BACKLOG as the
first thing to harden before step 6 reports a learned number.

**A control that could not see, corrected.** The first implementation of the
`coord_magnitude` feature ran its number regex over the whole SVG document
and matched the `2000` in the `http://www.w3.org/2000/svg` namespace URI. It
therefore returned the same constant for every instance and scored a clean
0.500 on all six classes — a baseline that "confirmed" the invalid set was
hard by being blind. It was repaired to read numbers only from numeric
attribute values before the reported run, which raised its best cell from
0.500 to 0.740. The uncorrected version would have made P-VO7 fire for the
wrong reason; recording it here rather than quietly fixing it is the point.

### What adversarial review found

Mandatory pre-commit review was run by an independent agent with no stake in
the result, and it found two defects that the 1,680-instance corpus could
not have surfaced, because the corpus never produces the inputs that trigger
them:

- **The verifier accepted a broken figure.** No gated check audits the acute
  angle annotations, and nothing resolved annotation or edge references, so
  an angle pointing at a nonexistent vertex — with a nonsense `measure`
  string — passed well-formedness, round-tripped through the SVG, and
  verified `ok`. Now refused at the door, not gated as a seventh check:
  no controlled class exercises it, and a check without a class is exactly
  the decoration this layer is built to avoid.
- **"No check can be silently muted" was a docstring, not a property.** An
  edge naming a nonexistent vertex made `incidence` skip its relation; with
  `topology` ablated the same graph verified `ok`. Reference resolution is
  now a precondition, and `verify` enforces it at the verdict boundary and
  raises rather than returning a verdict — a graph whose references do not
  resolve is not a figure that failed a check, it is not a figure.

Neither changes any published number: both were measured at 0 occurrences
across all 1,680 instances. That is the point worth keeping. The ablation
result was correct and the argument supporting it was not yet sound, and a
corpus that only ever contains well-formed inputs cannot tell you which is
which. Review also corrected P-VO6's evidential base (C1), relabelled P-VO5
as a design invariant (C2), scoped P-VO3 to separability rather than
completeness of the check set (C3), extended P-VO7 to all three styles, and
caught a false claim in this package's own exactness paragraph.

### What step 6 still needs

The oracle layer supplies a source graph, an SVG, a normalized parse, exact
verdicts with element-level localization, mutation records, and md5-stable
per-figure splits. It does **not** supply: raster rendering, a parameter-
matched pixel encoder, tokenization of the normalized tree, the
shuffled-structure control pairing correct pixels with a wrong scene graph,
style/family/structural-OOD split definitions beyond the single
right-triangle family, or any training loop. Those are step 6, and P-V1-P-V4
stay registered until it runs.

## Depth consumers: recurrence belongs at the address boundary (v0.6 item 4)

The earlier fork established a mechanism-level result: one shared GRU cell
walked over tree-path levels extrapolated beyond trained depth, while lookup
addresses and additional curriculum exposure did not. This matrix tested the
remaining hypothesis that the pointer query and decoder memory were
depth-naive consumers of that recurrent address.

The final protocol uses the same generated dataset and paired seeds for all
arms: 50,000 depth-2/3 training rows, 5,000 validation rows, 5,000 held-out
transformation/skeleton combinations at trained depth, and 3,000 generated
depth-4/5 OOD rows. Fixed capacity limits retain 2,450 OOD rows, so the metric
below is explicitly **conditional depth-OOD exact**: depth 4 retains
1,392/1,464; depth 5 retains 1,058/1,536. Twelve rows exceed the input limit and
538 the target limit. No excluded row is silently scored as success.

| consumer arm | parameters | trained-depth exact (s0/s1/s2) | conditional depth-OOD exact (s0/s1/s2) | OOD mean ± population SD |
|---|---:|---|---|---:|
| recurrent address only | 1,481,987 | 1.000 / 0.9996 / 1.000 | 0.284 / 0.171 / 0.134 | **0.196 ± 0.064** |
| recurrent query | 1,581,059 | 0.9998 / 0.9998 / 0.9998 | 0.186 / 0.204 / 0.146 | 0.179 ± 0.025 |
| recurrent memory | 1,581,059 | 1.000 / 0.9998 / 0.9998 | 0.073 / 0.053 / 0.119 | 0.082 ± 0.027 |
| recurrent query + memory | 1,680,131 | 1.000 / 0.9998 / 1.000 | 0.030 / 0.054 / 0.033 | **0.039 ± 0.011** |
| one-shot level-aware MLP | 1,680,133 | 1.000 / 1.000 / 1.000 | 0.131 / 0.134 / 0.162 | 0.142 ± 0.014 |

The registered materiality threshold was 0.15 absolute mean gain plus at least
two paired-seed gains of 0.15. **P-DC1 missed:** the both-consumer arm loses to
address on every seed and by 0.157 mean, even though all shallow seeds clear
the 0.99 floor. **P-DC2 missed:** neither query nor memory has a material mean
gain or a material paired-seed win, and both is weaker than either single
consumer. **P-DC3 missed:** the MLP is within two parameters as required, but
both recurrence beats it on zero seeds and loses by 0.103 mean. P-DC4's
fail-closed protocol gate is satisfied.

Teacher-forced diagnostics show this is not just whole-sequence compounding.
Address-only averages 0.813 accuracy on B-structure tokens, 0.910 on C-leaf
copy, and 1.000 on EOS. Query recurrence moves those to 0.790 / 0.874 / 1.000.
Memory recurrence preserves B-structure at 0.799 but drops C-leaf to 0.705 and
EOS to 0.913. Both consumers reach 0.731 / 0.677 / 0.997. The matched MLP sits
between them at 0.776 / 0.772 / 1.000. The consumer layers are not repairing a
depth-naive interface; they are perturbing an address representation that the
pointer already knew how to copy from.

The safety result is separate from the architecture verdict. Two pre-correction
runs ended in identical Windows bugchecks at the final-evaluation boundary
with `nvidia-smi` showing 15,760/16,303 MiB (15.39/15.92 GiB). P-DC5 remains
publicly retracted: clearing the CUDA cache before measuring peak allocated
tensors made its promised sub-12-GiB figure unable to observe the crash state.
P-DC6 and P-DC7 replace it with logical batch 192 accumulated through
64-example microbatches, evaluation batch 32, a 70% allocator cap, reserved and
whole-device telemetry, atomic outputs, and an absolute 80% device guard. Both
fired across all 15 rows. Maximum reserved memory was 5,028,970,496 bytes,
maximum whole-device footprint 6,387,466,240 bytes, and final evaluation added
at most 2,097,152 bytes over the train/validation device high-water mark.

Post-run integration exposed a provenance edge rather than a model result:
the raw implementation digests bound Windows working-tree bytes with mixed
LF/CRLF endings created by patching, while rebase checked out the same Git
content with uniform CRLF. Exact raw bytes remain the first analyzer gate.
`depth_source_manifest.json` is an explicit reviewed bridge from each recorded
runtime digest to the canonical LF digest at clean run commit `25db073`; the
fallback fires only when both sides match, and forged/missing bridge controls
refuse. Future runs should bind Git blob ids or canonical text hashes at launch
so checkout policy never needs a post-run bridge.

**Verdict:** preserve recurrence in address construction and freeze the
consumer expansion. “Iteration generalizes” remains supported at the address
boundary; “add recurrence wherever depth is consumed” is refuted. Next work
belongs at the interface and evaluation boundary: score all generated OOD
rows, localize capacity/decode failures by depth and step, add non-root and
composed transformations with shortcut controls, and test another shared
iterative mechanism before making a GRU-specific claim.

## Corpus analogy becomes a real split (v0.7 item 5)

The v0.6 lane reported its own vacuity: 40 rows, five distinct targets, one
ratio family, and a capability-blind rule — take the one number newly visible
in B and overwrite C's last slot — scoring **1.000**. This is the replacement.
No model is trained here; the split and the ceiling table are the slice, and
the model arm runs later against these ceilings as its bar.

### What changed in the construction

v0.6 admitted a row only when every binding was a bare slot rename or a
number, which is why compound expansions were excluded and why one family
survived. The unlock is that a compound expansion does not need a counterpart
in C's vocabulary, because **B is in the input**: its leaves are pointable
where they stand. D is B rewritten into C's vocabulary for the slots the twin
alignment covers, with expansion leaves carried verbatim, and the admission
gate is literal rather than argued — every token of D must occur in
`A <sep> B <sep> C` or the row is refused.

That single gate decided three questions that would otherwise have been
matters of taste:

- **head-identity collapses are refused** (4 rows), because the collapse
  *removes* the node from B, so the element it binds (`FALSITY`, `EMPTYSET`)
  appears nowhere in the input and would be conjured from `HEAD_ALGEBRA`;
- **arithmetic identities decide a representation question.** Substituting the
  pattern into C re-inserts `*(1, …)`; B, which is what the corpus writes, does
  not have it. B's form wins because a `1` the matcher supplied is not
  pointable. Fixing this moved the build from 581 to 914 rows — the earlier
  construction was refusing its own valid rows;
- **`=` orientation** is normalized away in the cross-check, because
  `Search.gen_direct` matches equalities in both directions.

Both constructions — specialize C directly, and translate B — are computed for
every row and must agree modulo those two normalizations. 20 rows still
disagree and are refused rather than explained.

### The split

914 admitted rows collapse to **398 distinct targets** (2.30x, against v0.6's
8.0x) over **11 typed families** and **10 untyped shapes**, 13 source and 15
target disciplines; **376 of 398** carry at least one compound-expansion leaf,
the thing v0.6 could not represent at all. Every D is specializer-accepted from
C under the same acceptability bar edge reporting uses, absent from every
authored template, and absent from its own input as a token sequence.

| family (typed skeleton of A and C) | n | disc. | example D |
|---|---:|---:|---|
| `?0:V = *(?1:P, ?2:V)` | 142 | 2 | `*(INERTIA, RESPONSE) = *(AMOUNT, CONSTANT, TEMPERATURE)` |
| `?0:V = *(?1:P, ?2:V, ?3:V)` | 85 | 2 | `*(PRESSURE, VOLUME) = *(CONSTANT, BASE, HEIGHT)` |
| `?0:V = +(?1:P, *(?2:P, ?3:V))` | 55 | 4 | `+(*(2, COEFFF, DU, DV), *(COEFFE, ^(DU, 2)), *(SLOPE, ^(DV, 2))) = ^(LINEELEMENT, 2)` |
| `?0:V = *(?1:V, ?2:V)` | 51 | 3 | `*(PARTONE, PARTTWO) = *(AMOUNT, CONSTANT, TEMPERATURE)` |
| `?0:V = *(?1:V, inv(?2:V))` | 30 | 5 | `CONDITION = *(2, EDGES, inv(INPUTPERTURB))` |
| `?0:V = +(?1:V, ?2:V)` | 14 | 2 | `2 = +(RELATIVE_VELOCITY, FACES, neg(EDGES))` |
| `?0:V = *(?1:P, ?2:V, +(?3:V, ?4:V))` | 12 | 2 | `AREA = *(+(VALUELEFT, neg(MEANREWARD)), inv(STDREWARD))` |
| `?0:V = *(?1:P, EXP⟨neg(*(?2:P, ?3:V))⟩)` | 3 | 3 | `PRESENT = *(FUTURE, EXP(neg(*(BARRIER, inv(*(GASCONST, TEMPERATURE))))))` |
| `?0:V = *(+(?1:V, neg(?2:P)), inv(?3:P))` | 2 | 2 | `STD = *(+(neg(CENTER), pm(SQRT(DISC))), inv(*(2, COEFF0)))` |
| `?0:V = MEET⟨?1:P, ?0:V⟩` | 2 | 2 | `SETA = MEET(SETA, JOIN(SETA, PROP2))` |
| `?0:V = neg(LOG⟨?1:V⟩)` | 2 | 2 | `SURPRISAL = neg(LOG(SIGMOID(*(BETA, +(LOGRATIOCHOSEN, neg(LOGRATIOREJECTED))))))` |

Family is the matcher's own `typed` skeleton, so "the families are
non-isomorphic" is true by definition and therefore worthless as evidence. The
number that can fail is the **untyped** one: 11 typed families collapse to 10
head/arity shapes, because `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)` differ only in a
slot class. That one collision turns out to explain every ceiling below.

Three holdout files, cut on three different keys, deterministically and without
a seed — families and disciplines alternate in descending-size order, and the
vocabulary holdout grows from the rarest target token upward to a declared 20%.
There is nothing to re-roll:

| holdout | train | held | key | held keys |
|---|---:|---:|---|---:|
| family | 243 | 155 | typed skeleton | 5 families |
| discipline | 222 | 176 | C's discipline | 7 disciplines |
| vocabulary | 315 | 83 | rarest target tokens | 57 tokens |

The pairwise Jaccard of the three holdout sets is 0.111, 0.139 and 0.257, so
these are three partitions rather than one wearing three names. They are **not
fully orthogonal**, and the shortfall is reported rather than asserted away:
holding out complete families also empties **five of ten** disciplines out of
training, because at this corpus size some disciplines occur in only one
skeleton. The discipline holdout is cleaner (7 of 8 families still trained) and
the vocabulary holdout keeps 6 of 10 families and 11 of 15 disciplines.

### The ceiling table

Every control was run before any training, and the predictions were committed
before any control existed.

| control | family | discipline | vocabulary |
|---|---:|---:|---:|
| **blind** copy C | 0.000 | 0.000 | 0.000 |
| **blind** copy B | 0.000 | 0.000 | 0.000 |
| **blind** last-slot number transfer *(v0.6's 1.000 rule)* | **0.000** | **0.011** | **0.048** |
| **blind** first-slot number transfer | 0.000 | 0.000 | 0.000 |
| **blind** positional rename | 0.026 | 0.028 | 0.048 |
| **blind** modal action pattern | 0.000 | 0.000 | 0.000 |
| **blind** nearest-template transfer | **0.400** | **0.932** | **0.398** |
| **blind** nearest authored template | 0.000 | 0.000 | 0.000 |
| **blind ceiling** | **0.400** | **0.932** | **0.398** |
| shuffled C — symbolic input-only | 0.000 | 0.000 | 0.000 |
| shuffled C — positional rename | 0.000 | 0.000 | 0.000 |
| shuffled C — nearest-template | 0.032 | 0.000 | 0.000 |
| *sighted* symbolic, input only | 0.458 | 0.545 | 0.651 |
| *sighted* symbolic, input + declared slot classes | **1.000** | **1.000** | **1.000** |
| *sighted* symbolic oracle | 1.000 | 1.000 | 1.000 |

Copy-C, copy-B and nearest-authored-template **cannot** exceed zero — admission
forbids it. v0.6 reported them as capability baselines and review corrected it;
they are kept as vacuity checks and excluded from the ceiling so the correction
cannot be un-made by accident.

### Predictions, adjudicated

**P-CS1 FIRED.** The v0.6 killer scores 0.000 / 0.011 / 0.048, inside its ≤0.05
bound on all three holdouts — narrowly on the vocabulary holdout (4 of 83 rows).
The rule that solved the entire previous lane now solves essentially none of it.

**P-CS2 FIRED, then MISSED, and the miss is the best result on this branch.**
The symbolic ceiling is 1.000, as predicted. But the *second* clause — that it
is 1.000 from the input alone — is false: a solver reading only
`A <sep> B <sep> C` reaches 0.458 / 0.545 / 0.651. Adding exactly two corpus
declarations, the parameter/variable class of each slot and the identity table,
takes the same solver to **1.000 on all three holdouts**. `Search` gates its
arithmetic-identity rule on the class being `P`, so a reader of the token
stream cannot recover it. The residual this lane leaves to something other than
the token stream is therefore not "difficulty" — it is a specific, nameable
piece of declared structure, which is a far sharper claim than the one
predicted. The v0.4 creation thesis still holds and is stated plainly: with the
slot classes in hand the task is closed-form, so this lane measures the
**pointing mechanism**, and no later model number may be sold as reasoning.

**P-CS3 half-fired.** Nearest-template transfer *is* the strongest blind
control on every holdout, by an order of magnitude over positional rename. Its
second clause was wrong twice over, and the second way is the interesting one.
The ratio skeleton `*(?1:V, inv(?2:V))` is not the largest family — it was the
*only* family in v0.6, and the prediction carried that assumption forward
unexamined; in this build it is fifth at 30 rows, behind `*(?1:P, ?2:V)` at 142.
Nor is it the most vulnerable: it scores **0.000** on the vocabulary holdout,
is not held out at all by the family split, and on the discipline holdout its
1.000 is shared with six other families. Size and target length were the wrong
mechanism entirely — the real one is untyped-shape leakage, below, which no
clause of P-CS3 anticipated.

**P-CS4 MISSED on both clauses.** The family holdout was predicted lowest and
the vocabulary holdout highest. Observed: vocabulary 0.398 is marginally the
lowest, family 0.400 next, and the **discipline holdout is by far the highest at
0.932** — nearly vacuous against a structure-replay baseline. Holding out a
target discipline barely matters, because the same skeletons recur across
disciplines and the answer rides on structure.

**P-CS5 MISSED AS WORDED.** The prediction asked for a ≥0.5 *absolute* collapse.
Shuffling C's leaves takes symbolic input-only from 0.458/0.545/0.651 to 0.000
and nearest-template from 0.400/0.932/0.398 to 0.032/0.000/0.000 — a 93–100%
*relative* collapse everywhere, but on the family holdout the absolute drop is
0.458 and 0.368, below the threshold, purely because the unshuffled score never
reached 0.5 there. The threshold was badly chosen; the substantive claim — no
control survives losing C — holds without exception.

**P-CS7 FIRED.** The blind ceiling is below 1.000 on all three holdouts, not
merely one, so the roadmap's acceptance condition is met with margin.

### What adversarial self-review found

Attacking our own split turned up one defect that changes how the ceilings
should be read, and it is the reason the `shape_leak` diagnostic exists.

**The family holdout leaks through the untyped shape, and that leak IS the
ceiling.** Families are typed skeletons; `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)`
are two families and one head/arity shape. Splitting nearest-template transfer
on the single bit "is this row's untyped shape still in training":

| holdout | rows w/ shape in train | score there | rows w/ unseen shape | score there |
|---|---:|---:|---:|---:|
| family | 51 | **1.000** | 104 | **0.106** |
| discipline | 162 | **1.000** | 14 | **0.143** |
| vocabulary | 63 | 0.492 | 20 | 0.100 |

The family holdout's 0.400 is exactly `51/155 × 1.000 + 104/155 × 0.106`. The
control is not demonstrating a capability; it is walking through a hole in the
split. The **strict ceiling is the unseen-shape column, ≈0.10–0.14**, and the
discipline holdout's 0.932 is explained entirely by 162 of its 176 rows keeping
their shape in training. The disciplined response is to report this rather than
re-roll the split after seeing the number: an untyped-shape holdout is filed as
required next evidence, not silently substituted for the committed one.

*Can a control see the answer through metadata?* Not in what it computes, but
review found the assurance was only a convention: every scorer, blind and
sighted, was handed one shared context object with the whole `Corpus` in it,
one attribute access away. Nothing read it — the ceilings are byte-identical
before and after — but "we checked that none of them do" is not the standard
this repo applies to its own tools. The context is now built as two separate
dicts and the blind one physically does not contain the corpus, so a control
that wanted the answer would have to edit `build_context` to reach it.
`authored_pairs` stays on the blind side because `nearest_authored_template`
needs it and is pinned at zero by admission.

That still left blindness as a claim about what eight functions *happen* to
read, because every control is handed the whole `Quadruple` and a `Quadruple`
owns `d_tree`. It is now executed instead of asserted: on each holdout, D is
poisoned on every held row (replaced by another row's D, which also poisons the
derived target and both leaf-provenance tuples) and each blind control must
return the identical guess. All eight do, on all three splits. Training rows
are left intact — replaying a training row's realization is the baseline's
whole point, and those labels are legitimately its own.

*Does dedup hold across splits?* Yes — dedup is by rendered target and is
applied before any split is cut, so no target can appear on both sides of any
holdout; it is pinned by test, as is order-independence. Dedup by target does
not by itself forbid the converse — two different Ds sharing one
`A <sep> B <sep> C` — which would make the lane ill-posed and let exact-input
retrieval masquerade as structure transfer. Measured: **398 distinct targets
over 398 distinct inputs**, so the task is a function of its input, and that is
now a test rather than a coincidence.

Two mistakes were caught by the tests rather than by reading. The family
non-isomorphism witness first keyed on operator heads alone, and `*` is n-ary
after canonicalization, so `*(?1:P, ?2:V, ?3:V)` and `*(?1:P, ?2:V)` read as one
shape; keying on head/arity fixed that and immediately exposed the sharper
P-vs-V collision above. And `head_kind` first guessed that call heads are
UPPERCASE identifiers — the corpus falsified it with `sum`, `lim` and
`AGGREGATE_n`, and 19 statements silently failed to round-trip. It is now a
declared table cited to the six `Parser` lines that build operator nodes, with a
test that re-derives the partition from every authored template.

### Limits

- The strict ceiling is ≈0.10–0.14, not the headline 0.40; the headline is
  inflated by untyped-shape leakage and must be quoted with that caveat.
- The discipline holdout is near-vacuous against structure replay and should
  not be cited as a difficulty result on its own.
- The three holdouts are not fully orthogonal; five of ten disciplines leave
  training when whole families do.
- D is a *derived structural target*, verified by the specializer, not an
  asserted truth. `*(PRESSURE, VOLUME) = *(CONSTANT, BASE, HEIGHT)` is a
  correct specialization of C and not a law of nature; nothing here enters the
  corpus or the epistemic ladder.
- Four families carry two or three examples, so their per-family numbers are
  anecdotes.
- No model has been run. Every number above is a control.

The three split files land in `experiments/data/`, which is gitignored by repo
policy, so they are regenerated rather than stored; the ceiling table itself is
committed at `experiments/results/corpus_analogy_v07_ceilings.json`. That is
only safe because the split rule takes no seed and no threshold to search over,
and because "regenerates exactly" is checked rather than trusted: a test writes
all three files twice, from two independent builds, through the same writer the
CLI uses, and compares them byte for byte — plus the checkout's own copies when
they exist. That test previously *skipped* when the files had not been built
yet, which is precisely the fresh-clone case where a gitignored dataset needs
the guarantee most; it can no longer skip.

Reproduce with:

```console
python experiments/corpus_analogy_split.py
python -m unittest tests.test_corpus_analogy_split
```
