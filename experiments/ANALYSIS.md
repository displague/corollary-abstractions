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
skeleton. The discipline holdout keeps 7 of 8 families in training — which is
NOT a virtue but the cause of its near-vacuity: with the leaky families
still trained, nearest-template reaches 0.932 (see the near-vacuous
verdict below), so this split cannot evidence model capability and no
model result on it may be quoted as meaningful. The vocabulary holdout
keeps 6 of 10 families and 11 of 15 disciplines.

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
predicted. Read the 1.000 with its circularity stated: the typed+oracle
control re-executes the builder's own construction line
(`canonicalize(rename(b, translate))`) with the same slot-class translation,
so it is near-definitional, not an independent solve — it measures that the
declared classes suffice for the pointing, not that a model would recover
them. The v0.4 creation thesis still holds and is stated plainly: with the
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
merely one. Stated against the full acceptance criterion ("a *non-trivial*
capability-blind ceiling below 1.000 *and a model result reported against
it*"): the split-and-ceilings half is met — the family (0.400) and
vocabulary (0.398) holdouts are non-trivial ceilings below 1.000 (the
discipline holdout at 0.932 is NOT non-trivial and is disclosed as
near-vacuous). The model-result half is NOT yet met: no model arm has run;
this slice delivers the split and the ceilings it must clear, and item 5
stays open for the model result reported against 0.400/0.398.

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
---

# From one live theorem to a proof-search curve (ROADMAP-v0.7 item 1)

`experiments/tactic_curve.py` -> `experiments/results/proof_curve.json`
`experiments/story_curve.py`  -> `experiments/results/story_curve.json`
Theorem set `prover/theorems_v1.json`, sha256
`af6f6cb73a06474f8e63a4c899028cf02149a7e0cc3c67b17eb4aa14f565b043`.

v0.6 rested its live-search claim on **one** `Init` theorem, one ordering
trace, and a learned proposer that a state-blind frequency order beat 64
proposals to 65.0. This lane replaces that point with a curve: 24 held-out
theorems in four families, six ranking arms, five budget rungs, **144 live
PyPantograph runs and no replayed transition in any arm**. Lean adjudicated
every transition; a refused tactic supplied no next state.

## Setup

**Held-out is checked, not labelled — at two levels.** No theorem id appears in
`prover/sample_triples.json` and no proposition appears as any extracted state
(`tests/test_proof_curve.py`). That is holdout by theorem identity and by
statement, which is *not* the same as state-level novelty: two different
theorems can pass through the same rendered proof state, and the v0.6
checkpoint was trained on rendered `stateBefore` strings. So the second level
is measured live rather than assumed —
`experiments/results/proof_curve_leakage.json`: **zero overlaps for every
arm** against 137 extracted training states. The six traversal-specific state
sets contain 162 / 149 / 149 / 153 / 151 / 151 distinct states for arbitrary,
frequency, syntax, and learned seeds 0/1/2 respectively. The first artifact
measured syntax alone and over-generalized it to the learned traversals;
independent review blocked that claim. The replacement is bound to the theorem
set digest, extraction digest, theorem ids, budgets, and all six arms.

The control ships in its own file on purpose: adding it after publication must
not perturb `proof_curve.json`, and the set file itself could not be amended to
describe it, because a published curve names `theorems_v1.json`'s sha256 and the
versioning rule forbids editing v1. The rule bit its own author on the first
occasion it could, which is the point of writing it down before it was needed.

Every theorem carries a *witness* inside the eight registered schemas;
the witness is never shown to a search arm and exists only so that an unsolved
run reads as a ranking failure rather than an impossible target.

**Schema choice is separated from tactic-argument generation.** A ranker
orders the eight schemas; `prover/tactic_grammar.py` turns a schema into
concrete tactic text by reading the rendered goal. Every arm receives the
*identical candidate multiset* for a state and can only permute it — asserted
by test — so a proposal-count difference is a schema-ordering difference.

| arm | what it is |
|---|---|
| `arbitrary` | schema declaration order, leading with `clear` |
| `frequency` | **v0.6's winner**, rebuilt from the same 44 training rows under the same mapper (pinned row-for-row by test) |
| `syntax` | closed-form rules over the rendered goal; blind to the capability under test (learning), not blind to state: it has no weights and no training data |
| `learned_s0/1/2` | the released v0.6 checkpoints, 27,688 parameters, used as shipped |

Retraining was considered and rejected: the new families are expressible in
the checkpoint's own vocabulary, so retraining would have replaced "does the
v0.6 artifact generalize?" with a different question.

**Project imports are live.** `prover/lean/proofcurve/` is a Lake project;
`import_control` records that an `Init`-only server refuses
`curve.project_import.both_commute` with "Unknown identifier
`ProofCurve.Both`". FEASIBILITY.md landmine 12 (POSIX `printenv` in
PyPantograph's `LEAN_PATH` discovery) is bypassed rather than patched:
`Server` only computes a path when `project_path` is given *without*
`lean_path`.

**One run per (theorem, arm) yields the whole curve.** `SearchController` is
deterministic BFS and every ranker is a pure function of the rendered state,
so a smaller-budget run is a strict prefix. 24 fresh live re-runs at the
middle rung agreed with the derived value in 24/24 cases (P-PC6).

## Solved-rate curve, all 24 theorems

| arm | (4,32) | (8,64) | (16,128) | (32,256) | (64,512) | mean proposals |
|---|---:|---:|---:|---:|---:|---:|
| arbitrary | 12 | 17 | 21 | 22 | 24 | 55.96 |
| frequency | 16 | 20 | 21 | 22 | 24 | 51.58 |
| **syntax** | 16 | **21** | 21 | 22 | 24 | **48.29** |
| learned_s0 | 16 | 18 | 21 | 22 | 24 | 49.04 |
| learned_s1 | 16 | 21 | 21 | 22 | 24 | 49.29 |
| learned_s2 | 16 | 19 | 21 | 22 | 24 | 48.67 |

Budgets are (expanded states, proposals). Every arm solves every theorem at
the maximum rung, which is exactly v0.6's registered live budget.

## Per family, at the registered middle rung (8 states / 64 proposals)

| family (n) | arbitrary | frequency | syntax | learned s0/s1/s2 (mean) |
|---|---:|---:|---:|---|
| conjunction (6) | 3 | 4 | **5** | 4 / 5 / 5 (4.67) |
| implication_chain (7) | 7 | 7 | 7 | 7 / 7 / 7 (7.00) |
| disjunction (5) | 3 | 3 | 3 | 3 / 3 / 3 (3.00) |
| project_import (6) | 4 | 6 | **6** | 4 / 6 / 4 (4.67) |

Mean proposals-to-solution by family:

| family | arbitrary | frequency | syntax | learned mean |
|---|---:|---:|---:|---:|
| conjunction | 61.67 | 54.00 | **52.17** | 53.17 |
| implication_chain | 12.43 | 12.86 | 9.29 | **9.05** |
| disjunction | 130.20 | 124.60 | **118.00** | 119.40 |
| project_import | 39.17 | 33.50 | **31.83** | 32.78 |

`implication_chain` is **vacuous as a budget discriminator**: every arm solves
all seven members at the lowest rung, including the two deeper members added
after a construction pilot exposed exactly this. An eight-tactic witness still
costs 11-15 proposals because the chain is nearly linear. Filed in BACKLOG;
the repair is premises that must be *selected* rather than discharged in
order, not more theorems of the same shape.

## Wall-clock curve (all 24), the axis that disagrees

| arm | 0.02 s | 0.05 s | 0.20 s | 1.00 s | 5.00 s |
|---|---:|---:|---:|---:|---:|
| arbitrary | 17 | 21 | 22 | 24 | 24 |
| frequency / syntax | 17 | 21 | 23 | 24 | 24 |
| learned_s0 | 14 | 17 | 21 | 24 | 24 |
| learned_s1 | 13 | 20 | 22 | 24 | 24 |
| learned_s2 | 14 | 19 | 22 | 24 | 24 |

A 27,688-parameter forward pass cost more than the local Lean round trip in
this recorded host run. Proposal count and observed wall time disagree about
the ranking; total search seconds were lower for the blind arms. This is an
observational result, not a stable timing estimate: arms ran in fixed order,
one timing sample each, and the committed evidence is not counterbalanced.

For reference, observed per-proposal times were arbitrary 0.631 ms, frequency
0.637 ms, syntax 0.651 ms, and learned 1.226 / 0.986 / 0.983 ms. These are
useful diagnostics, not a controlled performance comparison: fixed arm order
and one observation per cell leave warm-up and host drift confounded.

**Reproducibility caveat, stated rather than hidden.** Re-running the whole
lane reproduces every deterministic field exactly — solved, nodes, proposals,
solution path, dead branches, the full budget curve and every mean — but six
of the 30 all-family wall-clock cells differ from the first committed
artifact. The time ladder is a
measurement of this host on this run, not a reproducible constant. A stable
latency claim requires repeated, randomized or counterbalanced arm order.

## Exhausted branches preserved, and cross-task avoidance measured

The first artifact incorrectly treated every accepted transition outside the
first solution path as dead. In BFS, some are merely queued siblings that the
search never expanded. Independent review blocked the claim. The corrected
accounting recursively marks a transition only when its child was expanded
and every queued descendant was exhausted without a proof. It records 227
such transitions across 144 runs (`clear` 101, `constructor` 66, `right` 30,
`left` 24, `intro` 6). Signatures remain `(goal shape, schema)`.

| arm | dead branches | proposals | own-ledger share | pooled-ledger share |
|---|---:|---:|---:|---:|
| arbitrary | 48 | 1343 | 0.2338 | 0.2338 |
| frequency | 33 | 1238 | 0.1616 | 0.2221 |
| syntax | 33 | 1159 | 0.1553 | 0.2053 |
| learned_s0 | 41 | 1177 | 0.2065 | 0.2065 |
| learned_s1 | 35 | 1183 | 0.1589 | 0.2063 |
| learned_s2 | 37 | 1168 | 0.2063 | 0.2063 |

The *own* ledger is built leave-one-theorem-out from that arm's own runs; the
*pooled* ledger is the union over all arms and is the fair yardstick, because
an arm that accepts fewer dead branches shrinks its own ledger and then looks
virtuous for not revisiting it. Under the pooled ledger the learned mean is
0.2063 against syntax's 0.2053. **Learned ranking does not measurably avoid
branches proved dead on other tasks.** Its own-ledger aggregate is likewise
higher (0.1905 vs 0.1553). The ledger is run-local: nothing carries it
between runs, so no arm could have used it even in principle (BACKLOG).

## Prediction adjudication

- **P-PC1 FIRED** (blind) — syntax >= learned mean on all four families;
  21/24 vs 19.33/24 overall, with two ties and no learned win.
- **P-PC2 PARTIALLY MISSED** — 7 of 16 registered cells exact; the whole
  `implication_chain` row missed (guessed 5/5/6/5, observed 7/7/7/7) and the
  whole `project_import` row was underestimated by 1-2.
- **P-PC3 FIRED ON ITS LETTER, REFUTED IN SUBSTANCE** — syntax's margin over
  frequency is strictly smaller on `project_import` (1.67) than on
  `conjunction` (1.83), but 0.16 proposals is not a collapse, and by
  solved-rate `project_import` was the syntax arm's *best* family (6/6). The
  opacity mechanism is real and separately tested; it costs the blind arm the
  interior states, not the entrance, because every project theorem still opens
  on a visible universal quantifier.
- **P-PC4 FIRED after correction** (blind) — `clear` is the plurality of
  fully exhausted branches, and
  arbitrary's known-dead proposal share exceeds syntax's under both ledgers.
- **P-PC5 FIRED after correction, prediction under-specified** — learned is
  higher on both own (0.1905 > 0.1553) and pooled (0.2063 > 0.2053) ledgers.
  The earlier split verdict is retracted because it used the invalid
  off-path-is-dead definition. Substantively the 0.001 pooled margin supports
  no measurable avoidance, not a meaningful learned disadvantage.
- **P-PC6 FIRED** (blind) — 24/24 monotonicity re-runs agreed.
- **P-PC7 FIRED** — `Init`-only elaboration refused, live.

**Disclosure.** Construction pilots with the learned arms disabled were run
and discarded while the harness was built; they are why `implication_chain`
gained two deeper members and why the story briefs gained a plantable decoy.
Every prediction is marked blind or pilot-informed in
`experiments/tactic_curve.py`; the blind ones are P-PC1, P-PC4, P-PC5, P-PC6.

## Story family: same protocol, no lever

`experiments/story_curve.py`, 8 authored briefs (4 train / 4 held out by story
identity), 6 arms, 48 runs. The **same** `SearchController` (asserted
by object identity, not by name), the same ranker/argument-generator split,
`StoryFrameVerifier` as sole authority, a disjoint five-schema vocabulary and
its own weights — domain weights, not a second controller.

| arm | (4,32) | (8,64) | (16,128) | (32,256) | (64,512) | mean proposals |
|---|---:|---:|---:|---:|---:|---:|
| arbitrary / frequency / syntax | 0 | 0 | 0 | 0 | 8 | 373.0 |
| learned_s0 / learned_s1 | 0 | 0 | 0 | 0 | 8 | 373.0 |
| learned_s2 | 0 | 0 | 0 | 0 | 8 | 377.0 |

Held-out briefs alone give the same 0/0/0/0/4 shape for every arm.

The curve is a single step, and that is the finding. The largest
best-to-worst proposal spread on any brief is **1.07%**, against **65.6%** on
the proof side; every arm expands exactly 32 nodes. `SearchController` expands
each node's full candidate list and the story grammar fixes the solution at
depth five, so all 31 nodes above it are expanded whatever the order — ranking
can only save part of one node. P-SC1 (blind) fired, as did P-SC2 (learned
ties twice, loses once), P-SC3 (each schema fires exactly 4 times in the 20
training rows, so the frequency arm is byte-identical to `arbitrary` — a
  baseline that cannot differ is not a control), P-SC4, P-SC5 (96 fully
  exhausted transitions per arm; shares 0.1180 vs 0.1167) and P-SC6.

**"One shared policy protocol works in both domains" is true and nearly empty
as stated.** The protocol ports; the thing it buys does not. The story-side
headroom lives in best-first or depth-limited search, which would be a second
controller and was deliberately not built.

## GPU footprint

Nothing in the proof lane trains, so no batch ladder applies (ROADMAP-v0.7
item 4). Proof run: 42,545,152 B allocated / 56,623,104 B reserved peak, 276
MiB whole-device of 16,303 MiB (1.7%). The story run trains three
27,688-parameter rankers on 20 rows: 87,601,152 B allocated / 106,954,752 B
reserved. Both are two orders of magnitude below the 80% guard; the 60/70/80%
ladder was neither needed nor run, and no safety-cap change is mixed into
this comparison.

## Verdict

The v0.6 headline survives breadth and gets sharper. Across 24 held-out
theorems the learned checkpoints **overtook v0.6's own winner** (49.00 vs
51.58 mean proposals) and still lost to a closed-form syntax-aware order
(48.29) on proposals and on middle-budget solved rate (19.33 vs 21 of 24).
It was also faster in this one fixed-order host run, an observational result
that requires counterbalancing before becoming a latency claim. Live project-backed search works natively on
Windows. Dead branches are preserved and the cross-task avoidance question now
has a measured answer: no. The next honest move is not a bigger ranker; it is
a search that can actually spend a ranking — and a family whose premises must
be selected rather than discharged in order.

## v0.8 experiments (2026-08-10)

**Corpus-analogy model arm** (`experiments/results/corpus_analogy_model_arm.json`;
`train_corpus_analogy.py`, 1.49M params, 3 seeds, 120 epochs). Exact-match on each
holdout's held rows vs the frozen blind ceilings:

| holdout | model (mean ± sd) | blind ceiling | beats? |
|---|---|---|---|
| family | 0.168 ± 0.013 | 0.400 | no |
| discipline | 0.491 ± 0.012 | 0.9318 (near-vacuous) | no |
| vocabulary | 0.201 ± 0.028 | 0.3976 | no |
| shape (STRICT) | 0.104 ± 0.012 | 0.1069 | no |

The pointer is fully fit (train exact ≥ 0.9925); on unseen shapes it matches the
blind replay. The lane measures pointing, not reasoning (two corpus declarations —
per-slot P/V class + the identity table — make it closed-form), and the model does
not clear the pointing bar. P-CM1/CM2 MISSED, P-CM3/CM4 FIRED, registered before
the run; independently re-verified (fresh seeds 0.076/0.114, mean 0.095 < 0.1069).

**Depth interface** (`experiments/results/depth_interface.json`;
`depth_interface.py`, address arm, 3 seeds). The conditional-only OOD blind spot
removed: unconditional (correct/generated) reported beside retained (correct/kept),
with the 550 capacity exclusions (depth-4 72, depth-5 478) scored as failures, not
dropped. Address retained mean 0.196 vs unconditional 0.160. **P-DI2 (interface
manipulation, FIRED):** enlarging the copy budget (max_tgt 96→330, max_len 512→700)
to fully untruncate OOD does not move it — teacher-forced 0.166 untruncated vs 0.143
control unconditional, inside the pre-registered 0.15 bar, per-seed kept-row deltas
[-0.043, -0.003, +0.131] (seed noise); the excluded rows stay 0.0 even untruncated
(max trained target length 88 < the 96 boundary). **P-DI3 MISSED:** the retained
first-error mass is early (0.751 in deciles 0–2), not the predicted deep end. A
matched-control interface negative; the budget is not the depth bottleneck.

## v0.9 item 1 — miniF2F grammar-coverage: the first ingestion number

The v0.9 pivot's headline is "make the corpus non-toy by ingestion", and the
design doc (DESIGN-corpus-scale-and-programming.md) is explicit that the honest
first deliverable is a **coverage number** — what fraction of a real formal
source expresses in the corpus grammar at all — *before* any node is authored or
any scale is claimed. This is that measurement for miniF2F, the prime first
target.

**Instrument.** `scripts/ingest_minif2f.py`, two deterministic stages so the
number regenerates in CI without redistributing the source:

- `extract`: the pinned Lean-3 statement files (`test.lean`, `valid.lean` at
  commit `4e433ff5`, SHA-256 verified against `data_sources/manifest.json`,
  archive gitignored) → committed `data_sources/derived/minif2f/statements.json`
  (488 statement signatures: name, value binders, hypotheses, goal; proofs
  dropped; Apache-2.0 `LICENSE` + `NOTICE.md` vendored beside the extract). A
  count mismatch (≠ 244 per file) hard-fails, so parser drift cannot pass
  silently.
- `coverage`: the committed extract → committed
  `experiments/minif2f_coverage.json`. A pure function of the extract, guarded
  byte-for-byte by a regeneration test.

**What "covered" means, precisely, and the head-provenance rule.** A head counts
as *supported* only if a node in `data/*/nodes.json` actually carries it:
relations (`=  ≠  <  ≤  >  ≥  ↔`), the Boolean heads MEET/JOIN/NEG/IMPLIES,
arithmetic (`+ - * / ^`), and the three transcendental heads the corpus carries
(SQRT, LOG, EXP). A statement is COVERED only if it reduces to a skeleton whose
every **leaf** is a numeral or a numeric-typed bound variable and every
**internal node** is one of those heads. `nnreal` (ℝ≥0) and `ℕ+` count as numeric
slots — a positivity domain is a *regularity condition* on the leaf, not a
construct the grammar lacks. Everything else is UNTRANSLATABLE, tagged by the
first construct with no head.

Two numbers, both reported:

| coverage | test | valid | total |
|---|---|---|---|
| goal-only (drops hypotheses; upper bound) | 128/244 | 100/244 | **228/488 = 46.7%** |
| full-statement (goal AND all hypotheses reduce) | 84/244 | 61/244 | **145/488 = 29.7%** |

(These numbers were corrected **twice** by the shared classifier's evolution
during the Lean-workbook slice, both downward, both honest. First, making the
identifier regex Unicode-aware caught 5 goals of the form `σ.1 (σ.1 2) = 2` —
`σ` an unknown `Equiv` permutation invisible to an ASCII-only token pattern.
Then **carrier-awareness** (see the Lean-workbook review below) removed
integer-division / fractional-exponent false positives here too: over `ℕ`/`ℤ`,
`/` is `Nat.div`/`Int.div` (floor) and `x^(1/3)` is `x^0` — operations with no
corpus head. Net: full-statement `31.4% → 30.1% → 29.7%`, goal-only
`48.6% → 46.7%`. The instrument is shared, so a fix found on one source
re-measures the other — which is the point.)

Full-statement is the real ingestion number: a competition problem's hypotheses
carry its meaning, and dropping them to hit the goal changes the theorem. A node
authored honestly from miniF2F is the conditional `IMPLIES(MEET(hyps), goal)`,
and **29.7%** of miniF2F is expressible as such a node with the grammar as it
stands today.

**This number was corrected down by an independent adversarial review, and that
correction is the honest core of the result.** A first pass reported 60.7% /
44.7% by (wrongly) treating modulo `%` and divides `∣` as supported "because they
already appear in the corpus". They do not: grepping `data/*/nodes.json`, the
only `MOD` head is morphology's *linguistic modifier* and there is **no divides
head at all**. Review also caught a mathlib norm `∥a−b∥` slipping past an
ASCII-only `|` blocker, and two goals that are tuple-equalities `(p,q,r)=(2,4,8)`
whose pairing constructor is not a head. Reclassifying modulo/divides as the gaps
they are (−83 statements) and fixing the norm/tuple leaks (−3) moved the number
from 44.7% to **31.4%**. The lesson is the project's standing one: "the corpus
carries head X" is a claim to be verified node-by-node, not asserted — the
verifier now checks each supported head against `data/`.

**The untranslatable remainder is the finding** (full-statement, first-hit
construct, families merged; 335 of 488):

| construct | count | grammar gap |
|---|---|---|
| unknown function / sequence (`f x`, `a n`, arrow binder) | 70 | no first-class function slot |
| modulo (`%`, `[MOD n]`) | 60 | **no modulo head in the corpus** |
| big operator (`∑`, `∏`, `finset.sum`) | 54 | no indexed-aggregation head |
| divides (`∣`) | 23 | **no divides head in the corpus** |
| complex carrier (`ℂ`) | 18 | ℂ is not a leaf domain |
| existential goal (`∃`) | 17 | no quantifier head (goal position) |
| set / finset (`∈`, `.card`) | 15 | no membership/cardinality head |
| gcd / lcm | 15 | no number-theoretic combinator |
| absolute value / norm (`abs`, `\|·\|`, `∥·∥`) | 14 | no ABS/NORM head (cheap to add) |
| universal goal (`∀`) | 10 | no quantifier head |
| rational component (`.num`, `.denom`) | 9 | no field-accessor head |
| floor/ceil, `zmod`, factorial, primality, tuple, digits, trig, choose | 30 | assorted missing heads |

Two clusters dominate. **Number theory** (modulo 60 + divides 23 + gcd 15 +
digits/primality/choose ≈ 6 → ~104) is the single largest, and it is *structural*:
a slot-and-head grammar over first-order real/nat terms has no residue relation.
**Higher-order structure** (unknown functions 70 + big operators 54 → 124) is the
other: function-typed slots and bound-index aggregation are genuine grammar
extensions, not cosmetic gaps. Cheap wins (ABS/NORM 14, factorial 4) would nudge
the number a few points without touching either ceiling. Each untranslatable form
is a *scored finding about the grammar's reach*, exactly as v0.7's correspondence
rung treats an unprovable link.

**Honesty checks that survived the review.** (1) The false-positive sweep now runs
over a character whitelist (catching non-ASCII operators and constructors the
first sweep missed) as well as value-var-applied-as-function; after the fixes it
finds **zero** false positives in the 153 covered. (2) The `nnreal`/`ℕ+` numeric
slot decision and the ℂ/`zmod` carrier attribution are argued and tested. (3)
Both stages are byte-for-byte deterministic; `coverage` is a pure function of the
committed extract, guarded by a regeneration test; each supported head is now
asserted against `data/` rather than by memory.

**What this licenses next (not done here).** Authoring the 145 covered statements
as conditional Mathematical Statement Nodes via the PROVEN-WRITE seed→regenerate
route, each with a real `verified_by` link back to its miniF2F theorem, then
re-running the twin/specialization ledgers on the enlarged graph to see whether a
capability-blind baseline that won on 221 curated nodes still wins. That is the
release-gate work; this measurement is its honest precondition. 29.7% means a
miniF2F-backed corpus alone adds ~145 nodes (221 → ~366) while the untranslatable
70% is a *prioritized* grammar-extension backlog — number-theory residue and a
function slot first — rather than a vague "grow the corpus".

## v0.9 item 1 (cont.) — Lean-workbook grammar-coverage: the second source, at scale

miniF2F answered *whether* the coverage instrument works; Goedel-LM's
**Lean-workbook-proofs** answers what it says at scale, and it is the better
first ingestion target for authoring: **29,750 Lean 4 theorems each carrying a
real tactic proof** (not `sorry`), **MIT-licensed** (so a derived statement
extract may be committed), 16 MB. Unlike Goedel-Pset (statements with `sorry`),
its proofs can eventually ground a `verified_by` link.

**Instrument.** `scripts/ingest_lean_workbook.py`, the same two-stage shape as
miniF2F, sharing the classifier now factored into `scripts/grammar_coverage.py`.
The classifier was made **dialect-aware** for Lean 4 (capitalized namespaces
`Real.sqrt`/`Finset`/`Nat.Prime`, and the bare forms `sqrt`/`sin`/`Prime` that
appear under `open Real Nat`); every Lean-4 spelling is an *addition*, so miniF2F
still regenerates (its number moved only because the shared Unicode-identifier
fix corrected 5 latent false positives there — see the miniF2F note above). The
source parquet is pinned by **HF commit revision + file SHA-256**;
`fetch_sources.py` now refuses an unpinned HF fetch and SHA-verifies after
download. The extract stage needs pyarrow; the coverage stage is stdlib-only and
regenerates byte-for-byte from the committed extract.

**The numbers** (denominator = all 29,750 rows; the parser handled 100% of them):

| coverage | of rows |
|---|---|
| goal-only (upper bound) | 19,674 = **66.1%** |
| full-statement (goal AND all hypotheses reduce) | 19,077 = **64.1%** |

**64% — more than double miniF2F's 29.7% — and the gap is the finding, not an
error.** Lean Workbook is dominated by **algebraic inequalities over ℝ** with
positivity hypotheses (`0 < a ∧ 0 < b`, `a + b + c = 1`), which is precisely the
grammar's sweet spot; miniF2F carries far more number theory (modulo/divides) and
existential goals, which the grammar has no head for. Same instrument, two
sources, two honest and very different numbers — exactly what a coverage measure
is supposed to expose. (These figures are already *post*-review: an independent
adversarial pass caught the classifier accepting `/` and `-` over ℕ/ℤ as if they
were real division/subtraction — they are `Nat.div`/`Int.div` floor division and
monus, siblings of the modulo it already gaps — which had inflated the headline
to 68.0%. Carrier-awareness plus a fractional-exponent block corrected it to
64.1%; see the honesty section below.)

**But 64% of rows is not 64% of nodes: the duplicate rate is 37.9%.** Keyed on
the exact (whitespace-normalized) goal string, only **18,483 of 29,750** goals
are unique; the most repeated single goal appears **32 times**
(`(a+b+c)^5 ≥ 81·abc·(a²+b²+c²)`). Within the covered set, **11,189 unique
goals** back the 19,077 covered rows.

That 11,189 is a **floor** on the unique node yield, and both error directions
are worth naming. Keying on the goal string alone (a) *under*-counts nodes where
two rows share a goal but carry different hypotheses — genuinely distinct
conditional statements `hyps → goal` — and (b) *over*-counts uniqueness relative
to the deeper truth, because alpha-renamed / structurally-identical restatements
(same skeleton, different variable names or constants) still read as distinct
goal strings. Resolving both needs the structural-twin matcher, which is exactly
what the authoring phase runs on this data. So the honest statement is: **at
least ~11,189 unique covered statements** — a floor that is still a ~51× jump
over the current 221-node corpus, and the first chance to test the
twin/specialization claims outside a hand-curated world.

**The untranslatable remainder** (full-statement, first-hit family; 10,673 of
29,750):

| construct | count | note |
|---|---|---|
| universal goal (`∀`) | 1,957 | no quantifier head |
| unknown function / var applied | 1,049 | no first-class function slot |
| fractional exponent (`x^(1/3)`) | ~1,021 | rational power / `Nat.div` exponent — no head |
| big operator (`∑ ∏`) | 1,013 | no indexed-aggregation head |
| existential goal (`∃`) | 971 | no quantifier head |
| modulo (`%`, `[ZMOD n]`) | 922 | **no modulo head** |
| divides (`∣`) | 741 | **no divides head** |
| integer division / monus (`/`, `-` over ℕ/ℤ) | ~450 | **`Nat.div`/`Int.div`/monus — no head** |
| trig (`sin cos …`, bare under `open Real`) | 603 | no trig head |
| absolute value / norm | 567 | no ABS/NORM head (cheap) |
| set / finset | 464 | no membership/cardinality head |
| complex carrier (`ℂ`) | 268 | ℂ not a leaf domain |
| floor/ceil, gcd, binomial, factorial, tuple, min/max, zmod, matrix, deriv | ~640 | assorted missing heads |

Quantifiers (∀ + ∃ = 2,928) are the single largest block here — Lean Workbook
states many claims with an explicit binder the grammar cannot yet head — followed
by the same function-slot and big-operator structural gaps miniF2F flagged, the
number-theory residue (modulo + divides + integer-division = ~2,113), and the
fractional-power gap. The prioritized grammar-extension backlog is now confirmed
across two independent sources: **a quantifier/binder head, a function-typed slot,
indexed aggregation, and a carrier-honest number field (integer vs real division,
rational powers, the modulo/divides residue)** are where the reach has to grow.

**Honesty checks — and the review that moved the number 4 points.** Parser
fidelity was spot-checked by diffing extracted goals against the raw parquet
`full_proof` (faithful, no truncation); a character-whitelist sweep over all
19,077 covered statements finds **zero** foreign operator glyphs (a committed
test). The audit caught two real over-counts, in sequence. First, Greek-named
variables (`α β ω`) and mathlib `√`/`[ZMOD]` notation were invisible to an
ASCII-only classifier — a complex-`ω` statement was wrongly covered — fixed with a
Unicode-aware identifier class. Then an **independent adversarial review** found
the load-bearing one: the classifier treated `/` and `-` over `ℕ`/`ℤ` as real
division/subtraction, when over `ℕ` `a/b` is `Nat.div` (floor), `a-b` is monus,
and `x^(1/3)` is `x^0 = 1` — so trivial/vacuous statements like
`(1 + 1/n)^n < 3` (over ℕ, just `1 < 3`) were counted covered. That is the exact
sibling of the modulo gap already excluded. Carrier-awareness (the extract now
records each var's ℕ/ℤ/field carrier; a `/`/`-`/`⁻¹` with no field signal over an
integer carrier is a gap) plus a fractional-exponent block corrected the headline
**68.0% → 64.1%**, and re-corrected miniF2F **31.4% → 29.7%**. A bounded residual
remains and is disclosed: a non-elaborating classifier cannot always tell a real
division inside a field-coerced subexpression from a `Nat.div`, so a few
mixed-carrier statements may still be over-counted — the true number is a hair
lower, not higher. This is the standing rule again: a claimed head must be
verified against the actual operation, not the surface symbol.

**What this licenses next (not done here).** Author the ~11,189 unique covered
statements as conditional Mathematical Statement Nodes via the PROVEN-WRITE
seed→regenerate route, each retaining its `problem_id` so the pinned proof can be
attached as a **candidate `verified_by`** and adjudicated by the correspondence
rung (a passing tactic proof certifies what it checks, not correctness in
general). Then re-run the twin/specialization/decomposition ledgers on the
enlarged graph — the first honest test of whether a capability-blind baseline
that won on 221 curated nodes still wins on ~11k ingested ones.

## v0.9 item 1 (cont.) — Goedel-Pset-v1: the scale test (1.73M statements)

miniF2F sized the instrument; Lean-workbook ran it at 30k; **Goedel-Pset-v1**
runs it at **1,732,594 Lean 4 statements** — ~58× Lean-workbook, MIT-licensed,
Numina-derived, formalized by Goedel-Prover. Its proofs are `sorry` (unverified),
so it measures **grammar reach and redundancy at scale**, not verifiability
(Lean-workbook remains the source that can ground a `verified_by`).

**Reduced-commit, by necessity.** A 1.73M-row per-statement extract would be a
~300 MB JSON, so this source breaks the commit-the-extract pattern: a single-pass
tool (`scripts/ingest_goedel_pset.py`) reads the 4 **pinned parquets**
(SHA-256 + HF revision) and commits only the small aggregate
`experiments/goedel_pset_coverage.json`. Reproduction from the pinned parquets is
a documented manual step (needs pyarrow); it is not stdlib-CI-regenerable. To keep
that honest, the artifact is **self-checking**: it carries the false-positive
audit counts, and a committed test asserts both are 0.

**The numbers** (parser handled 1,732,426 / 1,732,594 = 99.99%; 168 unparsed):

| coverage | of rows |
|---|---|
| goal-only (upper bound) | 726,377 = **41.9%** |
| full-statement | 567,429 = **32.8%** |

duplicate rate **34.6%** (1,133,609 unique goals) → **386,375 unique covered
statements**. `audit: covered_foreign_glyph_count = 0, carrier_residual = 0`.

(Post-review: an independent adversarial pass caught one false-HIGH class the
self-audits are structurally blind to — the classifier was **arity-blind** to
bare `log`, so a two-argument `log b x` (a base-b logarithm = `Nat.log` /
`Real.logb`, no head) was accepted with the same token set as a one-argument
`Real.log x`. Self-contradictory, since `logb`/`Real.logb` was already rejected
~3,960 times. An arity-aware blocker for `log <atom> <atom>` fixed it, removing
~1,045 covered (568,474 → 567,429); one-argument `log x` stays supported. It
confirms the audit's real limit: `foreign_glyph = 0` means no stray glyph, not
"the covered set is clean" — an ASCII construct with no head still needs an
explicit blocker.)

**32.8% is the headline finding: half of Lean-workbook's 64.1%, and right next to
miniF2F's 29.7%.** This is exactly what the design doc predicted an uncontrolled,
larger, messier source would do — the 64% on Lean-workbook was the reach on a
*curated* inequality set, not the reach on formal math in general. Two competition
/ olympiad-derived sources (miniF2F, Pset) land near 30%; the one hand-selected
inequality set is the outlier. The instrument now has three points, and they say
the honest reach of the current grammar on real formal math is **~a third**.

**The remainder shifts shape at scale** (full-statement, first-hit family; of
1,163,952 untranslatable):

| construct | count | share |
|---|---|---|
| no relation in goal | 258,495 | 22.2% |
| unknown function / var applied | 160,176 | 13.8% |
| existential goal (`∃`) | 131,115 | 11.3% |
| universal goal (`∀`) | 89,099 | 7.7% |
| big operator (`∑ ∏`) | 81,130 | 7.0% |
| set / finset | 76,277 | 6.6% |
| trig | 60,689 | 5.2% |
| modulo / integer-division / monus (ℕ-ℤ) | 111,922 | 9.6% |
| absolute value / complex / divides / binomial / tuple | ~110,000 | ~9% |

The single largest gap is new: **`no_relation_in_goal` (22%)**. Numina word
problems formalize into a lot of goals that are not (in)equations at all — bare
predicates (`Even n`, `Collinear A B C`), definitional or membership claims,
conjunctions of non-relational facts. The grammar shapes relations over slots;
a fifth of a large model-formalized set simply is not that shape, and that is a
finding about the *source*, not a defect in the measure. The carrier residue
(modulo + integer-division + monus + divides = ~134k) is now correctly
**excluded** — without carrier-awareness those ~71k `/`-and-`-`-over-ℕ/ℤ
statements would have been counted covered, which is precisely the over-count the
Lean-workbook review caught, here at 20× the volume.

**Scale hardened the classifier, and the audit proved it.** The 1.73M run
surfaced 310 covered statements carrying operator/constructor glyphs absent from
the smaller sets — `×` (Prod / cross), `•` (SMul), `⊓`/`⊔` (lattice min/max),
`ℐ`/`𝕀` (imaginary unit), `ℵ₀` (cardinal), `⟨…⟩` (anonymous constructor). None
has a corpus head; all are now blocked, and the fix flows back through the shared
classifier to every source (Lean-workbook's covered count was unchanged — those
glyphs were already rejected there for other reasons — while 14 of its rejects
got the correct `vector_or_module_op` label). Variable-name glyphs that are
harmless (`ℓ`, Cyrillic, subscript modifiers `hᵣ`) were made visible instead, so a
domain-typed one can no longer hide. After the pass, `covered_foreign_glyph_count`
went 310 → 0; the self-checking audit is what makes that claim testable rather
than asserted.

**What this says for authoring.** At 32.8% with 34.6% duplicates, Pset alone would
yield ~387k unique covered nodes — ~1,750× the current 221 — but with `sorry`
proofs none is `verified_by`-grounded, so Lean-workbook (real proofs, ~11k unique
covered) remains the authoring source; Pset is the scale-and-diversity stress test
that says the grammar needs a **relational/predicate head and a quantifier head**
before ingestion at this scale stops discarding two-thirds of the material.

## v0.10 item 1 — the first grammar head, justified by its coverage delta: trigonometry (SIN/COS/TAN)

v0.9 measured the grammar's reach at ~a third and produced a prioritized list of
the heads it was missing. v0.10 item 1 is to grow the head-algebra to reach them,
each head justified not by taste but by **the coverage number it moves on the
three committed sources**. This is the first, and it establishes the loop.

The head chosen is trigonometry — bounded (three function heads like the existing
SQRT/LOG/EXP), and blocking a real slice of every source (`sin`/`cos`/`tan`). The
project's own rule is load-bearing here: **a head is legitimate only once a corpus
node carries it.** So the head is not added to the classifier by fiat; it is
authored into the corpus first.

**What was authored.** `scripts/seed_trigonometry.py` → `data/trigonometry/nodes.json`,
8 canonical identities that define the SIN/COS/TAN heads: the Pythagorean identity
`SIN(x)^2 + COS(x)^2 = 1`, the sine/cosine angle-sum laws and their double-angle
special cases (a real `special_case_of`/`generalizes` reciprocal pair), the
tangent definition `TAN = SIN/COS`, and the odd/even symmetries. The corpus grows
**221 → 229 nodes, 22 → 23 disciplines**. The matcher parses every new template
with **zero parse problems and zero slot gaps** (`reports/signature_matches.json`);
`check_regeneration` holds byte-for-byte.

**The coverage delta (the head's justification), full-statement, all three sources:**

| source | before (v0.9) | after | delta |
|---|---|---|---|
| miniF2F | 145 = 29.7% | 147 = 30.1% | +2 |
| Lean-workbook | 19,077 = 64.1% | 19,535 = 65.7% | +458 |
| Goedel-Pset-v1 (1.73M) | 567,429 = 32.8% | **607,047 = 35.0%** | **+39,618** |

Goedel-Pset's +2.2 points (unique covered 386,375 → 414,428) is the real evidence:
one head, authored from eight identities, unlocks ~40k statements that were
untranslatable the day before. The classifier change is the honest minimum —
forward `sin`/`cos`/`tan` move from the trig *blocker* into the supported-head
set, while inverse and reciprocal trig (`arcsin`, `cot`, `sec`, …) stay gaps,
because the corpus has no head for them.

**Scale surfaced one false positive, and the self-audit caught it.** Making trig
supported exposed a single covered statement carrying `sin^[n]` — the *n*-fold
*iterate* of sine (function composition), which is not the sine head at all. The
`[n]` iteration bracket had no blocker; a `[...]`-notation blocker (list literals
and function iteration, after the `[MOD` modulo blocker that owns its bracket) now
rejects it, and `covered_foreign_glyph_count` returned to 0. This is the v0.9
lesson holding: `sin` supported does not mean every `sin`-bearing string is
covered, and the committed audit is what makes that testable.

**An honest null.** The eight trig nodes formed **no cross-discipline twins**
(`reports/signature_matches.json` shows no `trigonometry` entry in any twin group).
The Pythagorean identity `SIN(x)^2 + COS(x)^2 = 1` does *not* twin with geometry's
Pythagorean theorem `a^2 + b^2 = c^2`, because the SIN/COS heads wrapping its slots
make a structurally different skeleton than bare legs — the matcher is right to
keep them apart. Adding a head extends *reach*, not necessarily the twin graph;
reporting the null is the point.

## v0.10 item 1 (cont.) — the relational/predicate head, and what the biggest bucket actually was

The remainder ranking said the next head is relational/predicate:
`no_relation_in_goal` was the single largest gap — 258,495 of 1.73M Goedel-Pset
statements (22.2% of the untranslatable set), plus 239 on Lean-workbook and 5 on
miniF2F. The house methodology is to measure before choosing, so the first step
was a predicate-head frequency ranking *inside* the bucket. The measurement
overturned the expectation.

**What actually populated the bucket (Goedel-Pset, 258,495 statements):**

| head / shape | count | share | note |
|---|---|---|---|
| `let`-prefixed goals | 226,631 | 87.7% | **a parser artifact, not a predicate** |
| bare prop-variable / unknown-application goals (`a`, `x`, `p`, …) | ~6,000 | 2.3% | unknowable: the goal is an opaque Prop |
| `False` | 4,119 | 1.6% | contradiction goals; `True` adds 430 |
| `Even` / `Odd` | 1,324 | 0.5% | + `IsEven`/`IsOdd` model-invented variants (141) |
| `Nat.Prime` (bare + negated) | 669 | 0.3% | `¬ Nat.Prime n` is the "not prime" shape |
| `Irrational` | 218 | 0.1% | almost all over `Real.sqrt` |
| `Filter.Tendsto`, `IsGreatest`, `StrictMonoOn`, geometry customs (`parallel`, `perp…`), `Function.Injective`, … | long tail | ~7% | function-slot or set-typed: not reachable without those heads |
| `Nat.Coprime` | 49 | 0.02% | 2-ary; would-cover simulation: 11 goal-only / 3 full |

(Lean-workbook's 239 ranked: `Nat.Coprime` 21, `Even` 15, `Function.Injective`
12, `False` 9, `¬Nat.Prime` 8, `Odd` 7 …; miniF2F's 5: `nat.prime` 2+1 negated,
`even` 1, one `∃`.)

**The dominant finding: 87.7% of the bucket was our own parser lying.** A
Goedel-Pset goal of the form `let x : ℝ := 4 … ; body` was being truncated at
the *binding's* `:=` — the scanner took the first depth-0 `:=` as the proof
terminator — so the classifier saw the two-token stub `let x`, which has no
relation, and filed a quarter-million statements under `no_relation_in_goal`.
The fix is not a new head at all: a `let` binding is a definitional equality,
and `=`-definition nodes are what the corpus already expresses definitions with
(`TAN(x) = SIN(x)/COS(x)`, `CONSISTENCY = NEG(BOX(FALSITY))`). The parser now
claims each `let`'s `:=` for its binding, splits the bindings into
`goal_lets` equations (`x = (4 : ℝ)`), and classifies them as goal conjuncts:
every binding RHS must reduce under the same blocker/carrier/symbol checks as
the goal, the body is classified on its own shape, and carrier-honesty is
preserved (a typed binding contributes its declared carrier; an untyped bare
numeral elaborates at ℕ, so `let n := 10; n / 4 = 2` is still the
`integer_division_no_head` gap, not real division).

**The predicate heads, chosen by the ranking:** parity (`EVEN`/`ODD`),
primality (`PRIME`), and irrationality (`IRRATIONAL`) — plus the prop constants
`TRUTH`/`FALSITY` that `data/logic` already carried (a bare `False` goal is the
contradiction node `IMPLIES(MEET(hyps), FALSITY)`). The corpus rule is
load-bearing as before: heads are authored FIRST. `scripts/seed_number_theory.py`
→ `data/number_theory/nodes.json`, 12 canonical statements: the parity algebra
(doubling, `2n+1`, odd = ¬even, the even/odd dichotomy, the two closure laws and
the two crossing laws of sums and products), two is prime and is the *only* even
prime, and the irrationality of `√p` for prime p with its classical instance
`√2` (a real `special_case_of`/`generalizes` pair, alongside
`even_double` ⊂ `even_product_absorbs`). Corpus **229 → 241 nodes, 23 → 24
disciplines**; matcher `parse_problems: 0`, `slot_schema_gaps: 0`;
`check_regeneration` holds.

The classifier accepts exactly what the corpus carries: a goal that is a bare
arity-1 application of a supported predicate (both dialects: `nat.prime`/`even`
and `Nat.Prime`/`Even`), a prop constant, or a top-level `¬`/`∧`/`∨`/`→`
composition of such atoms (MEET/JOIN/NEG/IMPLIES are corpus heads). The inner
term still passes every existing check — `Even (Finset.card S)` stays
`set_or_finset` — and three honesty guards came out of review lessons:
**arity** (`Even x y` is `predicate_extra_arg`, the 2-arg `log` lesson),
**carrier** (`Even x` over a declared ℝ var is `integer_predicate_field_carrier`:
over a field mathlib's `Even` is trivially true — not the integer-parity head),
and **naming the remainder precisely** (2-ary `Nat.Coprime` keeps its own
`coprime_no_head` label; relationless `∑`-goals now land in `big_operator`
instead of the undifferentiated no-relation bucket).

**The coverage delta (full-statement, all three sources), review-corrected:**

| source | before | after | delta |
|---|---|---|---|
| miniF2F | 147 = 30.1% | 151 = 30.9% | +4 |
| Lean-workbook | 19,532 = 65.7% | 19,570 = 65.8% | +38 |
| Goedel-Pset-v1 (1.73M) | 606,937 = 35.0% † | **673,521 = 38.9%** | **+66,584** |

† The slice's first-landed numbers (Goedel 679,586 = 39.2%, LW 19,574) carried
a cross-segment carrier-shielding over-count that adversarial review caught;
the correction is §"Review correction" below. The old baseline itself contained
1,146 rows of the same defect (goal↔hyp shielding predates this slice), so the
like-for-like corrected comparison is 605,791 → 673,521 = **+67,730**.

The `no_relation_in_goal` bucket itself: 258,495 → **9,540** on Goedel-Pset
(5 → 0 on miniF2F, 239 → 50 on Lean-workbook). It did not all become coverage —
most of it redistributed to its *true* labels (`∃`-goals, tuples, set-typed
lets), which is the honest outcome: the instrument now names the remainder
correctly instead of lumping it. The audited LOST count for the head extension
itself is **0** on every source: a full old-vs-new dual-classification pass
over all 1.73M rows shows the grammar changes dropped no previously covered
statement. (The review correction below then *deliberately* removes 1,146
old-baseline rows — but as over-counts being corrected, each with a per-row
audit trail, not as losses.)

**Scale surfaced a false-positive class again, and the audit caught it again.**
The first full run reported `covered_foreign_glyph_count = 6` — all six were
`let`-bound *lambdas* (`let f : ℝ → ℝ := (· * 60)`) or custom notation
(`a ⋆ b`): Lean's section dot `·` and the `⋆` glyph are invisible to the
identifier scan, so the bound name looked like a plain value. Two fixes, both
now regression-tested: a function-typed `let` sets the unknown-function flag
(its name is not a value slot), and a new `uninterpreted_notation` blocker
(`·`, `⋆`, `fun`/`λ`/`=>`) rejects anonymous functions wherever they appear
(28,924 statements now carry that precise label). Audit after:
`foreign_glyphs = 0, carrier_residual = 0`.

**Two honest disclosures.** (1) `unparsed` rose 168 → 192: 24 statements whose
multi-line lambda-`let` bindings the layout-approximating splitter refuses to
guess at; all 24 were previously *mis*parsed into the no-relation stub, none was
ever covered. (2) The duplicate rate FELL 34.6% → 24.1% (unique goals 1.13M →
1.32M): the old truncation had collapsed every `let x …` goal into the same
stub, so the previous dedup overcounted redundancy; unique covered goals rise
414,330 at 35.0% → **476,504** at 38.9%. (Correction note: this slice's commit
message and the first version of this paragraph misquoted the baseline as
414,428 — the committed v0.9 artifact pins `unique_covered_goals` = 414,330.
The commit message is immutable; this is the correction of record.)

**The twin null, a third time.** The 12 number-theory nodes form no new
cross-discipline twins — `group_counts` is unchanged
(`{shape: 30, typed: 31, family: 30, aliased: 32, mirror: 5}`). The predicate
heads wrapping the slots (`EVEN(n+m)` vs bare `a+b`) keep the skeletons apart
from the arithmetic corpora, exactly as SIN/COS did. Within the discipline the
grounding is real: the groundedness ledger's exact channel grew 469 → 495 and
the absorption guard holds without further weakening (exact-over-absorption
eases 4.9:1 → 4.7:1 by count, still clearly above the 4:1 floor; rate gap
0.116 < the 0.12 pin) — recorded as the second registered acknowledgment in
`tests/test_decompose_channels.py`.

### Review correction — the carrier signal must be segment-local (a caught over-count)

Independent adversarial review of this slice reproduced every headline claim
and then found the one it exists to find: `classify()` computed the field
signal (`: ℚ`/`: ℝ` ascription, coercion `↑`, `Real.` call, decimal literal)
over the WHOLE statement and passed it to every segment's carrier check. One
`: ℚ` in one binding therefore legitimized `/` and `-` over ℕ in *sibling*
segments — `Nat.div` and monus covered as if they were real division and
subtraction, precisely the over-count carrier-honesty exists to refuse. The
review's evidence rows make the semantics vivid: in Goedel-Pset-1082706 the
shielded `sample_size / total_students` is ℕ-division — it equals **0** in
Lean, and the covered statement is arithmetically false as formalized.

**The fix.** The signal is now segment-local (goal body, each `let` equation,
each hypothesis separately), and a field-**typed** `let` no longer sets the
statement-wide field carrier — its `(rhs : ℚ)` equation string is its own,
local signal. Integer-typed lets still register statement-wide, because an
integer carrier only ever *creates* gaps (the safe direction). Binder-declared
field variables (`(x : ℝ)`) remain statement-scoped — that is the pre-slice,
v0.9-reviewed semantics for variables that genuinely occur anywhere — which
leaves one disclosed asymmetry: `r^(n-1)` under an ℝ *binder* stays covered
while the same exponent monus under a ℚ-typed *let* is now a gap. Conservative
in exactly one direction. The `_carrier_residual` audit was un-blinded the same
way: it previously regexed the same concatenated text, so it was structurally
incapable of flagging this class; it now checks per segment, and the class it
would flag is regression-tested from both evidence rows.

**The correction, counted per row (triple-classifier pass: pre-slice /
slice-as-committed / fixed):**

| | count |
|---|---|
| rows losing coverage under the fix | **6,066** |
| — as `integer_division_no_head` (goal / hyp) | 3,300 / 476 |
| — as `nat_monus_no_head` (goal / hyp) | 1,905 / 382 |
| — as `integer_predicate_field_carrier` (argument-level hole, see below) | 3 |
| of the 6,066: already inside the OLD 606,937 baseline (goal↔hyp shielding predates the slice) | 1,146 |
| of the 6,066: inside this slice's new gain | 4,920 |
| rows gaining coverage (a ℚ-let no longer globally triggering the integer-predicate guard) | 1 |

Corrected numbers: Goedel-Pset full-statement **673,521 = 38.9%** (goal-only
829,949 = 47.9%, unique covered 476,504), Lean-workbook **19,570** (its 4
corrections are `Even ((3+√5)^n + (3−√5)^n)` — over ℝ, mathlib-`Even` is
trivially true of every real, so the formalization is vacuous and the corpus's
integer EVEN head must refuse it; all 4 were inside this slice's gain),
miniF2F unchanged at 151. The review estimated ~3,644 rows from a slightly
laxer segment notion; the uniform rule (every segment local, typed-let field
carriers local too) removes 6,066 — stricter than the review asked, in the
only honest direction, and it is what the evidence row 1082706 actually
requires. The same review follow-up closed the argument-level hole
(`Even ↑n`, `Odd (x : ℝ)`: field signal inside the predicate's own argument),
which realized 3 Goedel + 4 Lean-workbook corrections.

GC4/GC5 do not move (the corpus is unchanged at 241 nodes / 24 disciplines;
re-verified, not assumed), and the audit fields stay
`foreign_glyphs = 0, carrier_residual = 0` — now over a residual check that
can actually see the class it guards against. Corrections are first-class
here: the numbers above replace the slice's first-landed ones, and the commit
that landed them stays in history with this section as its correction of
record.

## v0.10 item 1 (cont.) — the quantifier/binder head: FORALL and EXISTS

After the relational/predicate slice, the two largest named gaps on
Goedel-Pset are the quantifier buckets: `existential_quantifier` 131,051 +
`universal_quantifier` 85,810 in the goal (12.5% of 1.73M), plus
`hyp:universal_quantifier` 10,063 + `hyp:existential_quantifier` 9,770
blocking full-statement coverage — 236,694 statements in all. Lean-workbook
carries 2,925 goal + 27 hyp; miniF2F 18 goal + 10 hyp. The house rule is to
measure before choosing, so the first step ranked what is actually inside the
buckets, with a prototype quantifier-prefix parser and a **would-cover
simulation**: strip the prefix, register the bound variables with their
declared carriers (untyped binders defaulting to ℕ, the same rule untyped
`let` numerals already follow), desugar bounded binders
(`∀ x > 0, P` → `x > 0 → P`, Lean's own elaboration), refuse shadowing, and
run the EXISTING classifier on the transformed statement.

**The ranked table (Goedel-Pset goal bucket, 216,861 statements):**

| shape | count | share | note |
|---|---|---|---|
| prefix chain, supported binder shapes | 143,462 | 66.2% | typed-numeric 109,048 + bounded/untyped 34,414 |
| — of which the body ALSO reduces (would-cover) | **60,223** | 27.8% | 53,920 with clean hypotheses; 3,093 via the ∃!-desugar |
| — body residue: unknown-function application | 28,033 | 12.9% | `f x`, sequence apps — the function-slot backlog |
| — body residue: non-prefix quantifier inside body | 21,779 | 10.0% | `∀ x, (∃ y, …) ∧ …` — stays a precise gap |
| — body residue: abs / monus / int-div / others | 31,427 | 14.5% | each keeps its precise pre-existing label |
| embedded quantifier (goal is not a quantifier prefix) | 48,812 | 22.5% | 25,260 inside →∧∨ composition, 12,776 iff-composed, **13,031 ¬-prefixed** (reachable: NEG is a head) |
| binder over unsupported domain | 23,595 | 10.9% | `f : ℝ → ℝ` 9,677; `ℝ × ℝ`/`Fin n`/custom structures 12,457; `Set`/`Finset`/`Polynomial` 1,461 |
| `∃!` unique existence | 7,099 | 3.3% | desugars to EXISTS/MEET/FORALL/IMPLIES/`=` — all carried |
| shadowed binder (bound name collides with an outer var) | 1,839 | 0.8% | refused precisely — per-name carriers are not tracked |
| quantifier inside a `let` binding | 987 | 0.5% | a Prop-valued binding; stays a gap |
| chain shapes | E 79,116 / A 77,595 / mixed 10,351 | | nesting is head-nesting, no new machinery |

Hyp buckets (19,833): the same analysis gives **11,287** would-cover (typed
8,204), directly unblocking full-statement coverage on rows whose goal already
reduces. Two guesses the measurement killed: the `∃ k, n = 2*k` parity-witness
shape is only **76 goal + 48 hyp** rows (the EVEN/ODD witness-definition nodes
are authored because they are the canonical definition of the heads' link to
EXISTS, not for bucket share), and single-equation `∃`-bodies (16,131) are
mostly NOT bare witnesses — 6,432 have the bound variable alone on one side.

### Design checkpoint (registered before the corpus was written)

**Representation.** Two new template heads, `FORALL(X, BODY)` and
`EXISTS(X, BODY)` — ordinary call heads to the matcher (non-commutative,
nothing declared in `HEAD_ALGEBRA`: binder exchange `∀x∀y = ∀y∀x` is true but
undeclared, the same honest under-declaration as associativity elsewhere).
The first argument is the bound variable's slot; binding structure is carried
by slot RECURRENCE in the skeleton (`FORALL⟨?0, EVEN⟨*(2, ?0)⟩⟩`), which the
skeleton's first-occurrence numbering makes alpha-invariant for free. Nested
quantifiers are nested head applications. Schematic predicate slots (`PRED`)
are applied as call heads, the established `F(ENDPOINT)` pattern from
calculus. Corpus first, as always: `data/logic` gains a `quantification`
topic (the classical first-order laws: instantiation, generalization, the two
quantifier De Morgan duals, the two distribution laws, ∀→∃ on an inhabited
domain, and the ∃!-expansion that grounds the classifier's desugar);
`data/number_theory` gains the EVEN/ODD existential-witness definitions,
tying the new head to the predicate heads of the previous slice.

**What the head claims.** A covered quantified statement reduces to a
skeleton whose every head the corpus carries — now including quantification
over a NUMERIC domain (a typed ℕ/ℤ/ℝ/ℚ binder or a defaulted-ℕ untyped one)
whose body reduces under every existing blocker/carrier/symbol check with the
bound variable as one more value slot. **What it does not claim:** the
template head does not carry the binder's domain (the node's `slot_schema`
does, exactly as for every other slot — carrier-honesty at ingestion does the
type work); it does not represent quantification over functions, sets,
tuples, `Fin n`, or custom structures (those keep precise labels — they are
the function-slot/structure backlog); it does not touch non-prefix
quantifiers except the ¬-prefixed chain, which is NEG-composition of a
carried head (the quantifier De Morgan nodes state exactly that composition).

**Carrier honesty, decided in advance.** (1) Quantifier-binder carriers are
SEGMENT-LOCAL in both directions: a `∀ x : ℝ` in the goal must not shield
Nat-division in a hypothesis (the review lesson), and a `∀ n : ℕ` in a
hypothesis must not manufacture gaps in the goal — the bound name cannot
occur outside its segment because shadowing is refused. (2) Untyped and
relation-bounded binders default to the ℕ carrier: Lean's own elaboration
defaults them absent a field signal, so `∀ x > 0, x + 1/x ≥ 2` IS a ℕ
statement as formalized (`1/x` is Nat.div) and stays
`integer_division_no_head`; a segment-local field signal lifts the default,
because the same signal is what pins Lean's unification to ℝ/ℚ. This is the
untyped-`let` rule applied to binders. (3) The pre-existing, disclosed
asymmetry stays: a statement-binder field variable is statement-scoped, so it
can shield a quantifier-ℕ-binder's monus *within the same segment* — the
`r^(n-1)` asymmetry from the segment-local review fix, inherited unchanged,
not widened. (4) `∃!` desugars to its Lean/FOL definition
(`ExistsUnique`: EXISTS + MEET + FORALL + IMPLIES + `=`, all carried heads),
grounded by the authored expansion node; classification-wise the uniqueness
clause re-checks the same body and adds one equation between two bound slots.

**Registered expectation (floors, from the simulation):** Goedel-Pset
full-statement +≈65,207 (53,920 goal-side + 11,287 hyp-side), goal-only
+≈60,223; Lean-workbook full +≈1,525; miniF2F full +≈8. Floors because the
simulation desugared only the FIRST quantified hypothesis per statement and
did not simulate ¬-prefixed chains at all. **What stays a gap, precisely
labeled:** embedded quantifiers in connective/iff position (~35,781 —
reaching them needs the flat segment checks restructured into an atom-tree
walk, a slice of its own), unsupported binder domains (~23,595), quantified
`let` bindings (987), shadowed binders (1,839), and every body whose inner
construct already had no head.

### The delta (adjudication of the registered floors), full-statement

| source | before | after | delta | registered floor |
|---|---|---|---|---|
| miniF2F | 151 = 30.9% | **161 = 33.0%** | +10 | +8 ✓ |
| Lean-workbook | 19,570 = 65.8% | **21,237 = 71.4%** | +1,667 | +1,525 ✓ |
| Goedel-Pset-v1 (1.73M) | 673,521 = 38.9% | **747,889 = 43.2%** | **+74,368** | +65,207 ✓ |

(Review-corrected: the slice first landed at Goedel 748,384 / LW 21,239;
adversarial review then caught the mixed-carrier chain shield — the
correction subsection below — which removed 495 + 2 over-counted covers.
These are the numbers of record.)

Goal-only: miniF2F 232 → 235 = 48.2%; Lean-workbook 20,180 → 21,885 = 73.6%;
Goedel-Pset 829,949 → **895,333 = 51.7%** (+65,384; unique covered goals
476,504 → **540,405**). Every floor was exceeded for the registered reasons:
the production classifier desugars EVERY quantified hypothesis (the
simulation stopped at the first) and reaches the ¬-prefixed chains the
simulation skipped. Goedel's full-statement gain decomposes as 60,844 goal-position + 13,524 hyp-position rows, drawn EXCLUSIVELY from the four
old quantifier buckets — no other reason class changed covered status, which
the dual pass verifies per row.

**LOST = 0, the house standard, on all three sources** — a per-row dual
classification pass (main @ d131e16, the numbers of record, vs this slice)
over all 1,732,594 Goedel rows and both committed extracts shows no
previously covered statement lost coverage, goal-only or full. The parser
was untouched and the pass asserts old/new parse agreement row-by-row;
`unparsed` stays 192 and the duplicate rate 24.1%.

### At 1.73M scale the audits fired three times, and each catch is now a test

1. `covered_foreign_glyph_count = 1`: Goedel-Pset-91093 covered
   `∃! x : ℚ, (2 ★ (2 ★ x)) = (1 ★ x) ∧ …` — the BLACK STAR operator is
   invisible to the identifier scan, the same class as `⋆` and the section
   dot from the relational slice. Classifier fix: the star family (★ ∗ ⊛)
   joins the `uninterpreted_notation` blocker; cost, exactly 1 covered row.
2. `covered_carrier_residual_count = 1`: Goedel-Pset-1326754
   `∃ (last : Rat), last = 1 /. 2` under an ℕ theorem binder — a LEGITIMATE
   cover (the segment's own binder declares the ℚ carrier; `divInt`
   coincides with rational division on these operands) that the AUDIT
   couldn't see, because it read only statement-level carrier flags. Audit
   fix, not a whitelist: `_carrier_residual` re-parses each segment's
   quantifier prefix with the shared extractor (the segmentation must be the
   one the classifier saw) while keeping its own independent carrier regex —
   and a test proves it still flags a ℕ-quantified division.
3. The step-1-style remainder inspection (before the numbers landed) caught
   the first cut of the binder-section parser labeling 10,691 rows
   `quantifier_malformed` when their binder merely contained parentheses
   (`∀ x ∈ Set.Icc (-3 : ℝ) (-1), …`, `∃ q : ℕ → (ℝ × ℝ), …`) — the same
   lesson as the `let` truncation: the biggest "malformed" bucket was the
   instrument's own parse. Fixed (group-lists require an all-whitespace
   residue; ⊆/∉-bounded and ⦃⦄ strict-implicit binders handled), the bucket
   collapses to **46** — mostly legal-but-mixed binder lists
   (`∀ (a : ℕ → ℝ) d, …`) the extractor refuses conservatively rather than
   truly unparseable text — and the 32 newly covered
   ⦃⦄-binder rows forced the audit-normalizer decision (binder brackets
   normalize; factorial `!` and set-builder braces stay foreign, asserted).

### What the buckets became (Goedel-Pset, goal position)

| label | rows | note |
|---|---|---|
| covered (was existential/universal_quantifier) | 65,841 | +35,255 from ∃-bucket, +30,586 from ∀-bucket |
| `quantifier_embedded` | 62,142 | connective/iff/let/nested position — the successor slice |
| `quantifier_function_binder` | 21,370 | with `unsupported_symbol:f` bodies (28k), the function-slot backlog |
| body residues under a supported prefix | ~55k | each keeps its pre-existing precise label (abs 43,472 †, monus 41,239 †, int-div 40,442 †, …) |
| `quantifier_shadowed_binder` | 2,779 | refused re-quantification of an outer name (`theorem (a b : ℤ) : ∀ a b, …`) |
| `quantifier_structure_binder` / `set_or_finset` | 1,409 / — | membership and ⊆-bounded binders rejoin the set bucket |
| `quantifier_over_sort` | 457 | second-order (`∀ p : Prop`) |
| `quantifier_malformed` | 46 | conservative parse-limit refusals (mixed group+bare binder lists like `∀ (a : ℕ → ℝ) d, …` — legal Lean the extractor declines to guess at) plus truly malformed text |

† statement-wide bucket totals after redistribution, not quantifier-only.
Hypothesis side: `hyp:quantifier_embedded` 1,234, `hyp:quantifier_function_binder`
411, `hyp:quantifier_shadowed_binder` 506, `hyp:quantifier_malformed` 3.
Lean-workbook's residue: `quantifier_function_binder` 275, `quantifier_embedded`
187, shadowed 60; miniF2F's: 5 embedded, 1 function-binder.

### Corpus, matcher, pins — and one guard direction that moved

Corpus 241 → **251** (24 disciplines): 8 quantifier laws in `data/logic`
(new `quantification` topic), 2 witness definitions in `data/number_theory`.
Matcher `parse_problems: 0`, `slot_schema_gaps: 0`, `ladder_violations: 0`;
`check_regeneration` byte-identical; `validate_nodes` green over 251. One
`verified_by` MOVED, not added: `not_forall_iff_exists_not` (14 steps in the
committed prover artifact) now sits on the node that states exactly what it
proves — still honestly UNTRANSLATABLE to the propositional-only
correspondence checker, so it remains reported-not-verified.

**The twin null, a FOURTH time:** `group_counts` is unchanged
(`{shape: 30, typed: 31, family: 30, aliased: 32, mirror: 5}`). The binder
heads wrapping PRED slots twin with nothing — quantifier De Morgan does not
twin with propositional De Morgan (the binder head is real structure), which
is the same honest separation SIN/COS and EVEN/ODD produced.

GC4 pins moved with the corpus growth (mean 0.776 → 0.781, exact 495 → 531,
pattern 91 → 99, constituents 212 → 222) under the THIRD registered
acknowledgment in `tests/test_decompose_channels.py`. The absorption COUNT
floor holds unweakened: e_best 369 > 4 × a_best 85, ratio **4.3:1** over the
4:1 floor. **One guard direction moved and is flagged for maintainer
review rather than absorbed:** the rate reading is no longer a wash —
absorption's best-owner external rate 85.9% vs the exact channel's 69.5%, a
16.4-point gap against the old < 0.12 pin. Cause: this slice's new exact
constituents ground almost entirely same-corpus (the quantifier laws ground
in one another), diluting exact's external rate, while its 8 absorbed
constituents (NEG- and MEET/JOIN-wrapped binder compositions) mostly absorb
external-owned patterns. The refutation of the retracted "absorption
concentrates cross-discipline credit" inference now rests on the count
dominance alone; the new gap is pinned at its measured value so further
drift is a fresh decision, and the decompose stdout sentence now describes
the data instead of repeating the v0.7 adjudication.

**Disclosed limits of this slice:** embedded quantifiers (62k Goedel goal
rows) need the flat segment checks rebuilt as an atom-tree walk; binder
domains beyond the numeric carriers (functions 21k, products/`Fin n`/custom
structures, sorts) wait on the function-slot and structure heads; shadowed
binders are refused (2.8k) because per-statement carrier flags cannot say
"x is ℝ here and ℕ there"; and the pre-existing statement-scoped-field
asymmetry is inherited unchanged — a theorem-level `(y : ℝ)` can still
shield a quantifier-ℕ-binder's monus within the same segment, the disclosed
`r^(n-1)`-class conservatism trade recorded at the segment-local review fix.
One further carrier-table item, review-filed for the next carrier slice
(also in docs/BACKLOG.md): `ℝ≥0`/`NNReal` sits in `_FIELD_TYPES`
(pre-existing, v0.9), but mathlib's NNReal subtraction is truncated —
monus-family, not the field `-` head — so `∀ x : ℝ≥0, x - 1 ≤ x` covers
under a head that misreads its subtraction. Realized instances not yet
counted; the fix belongs to the carrier-honest number-field slice
(ROADMAP-v0.10 item 1, last bullet), not to a one-line patch here.

### Review correction — the mixed-carrier chain shield (a caught over-count, fourth cycle)

Independent adversarial review of this slice reproduced the headline numbers
and caught the class this project's audits exist to catch, one level deeper
than the slice's own three catches: `_quantifier_segment` returned ONE field
flag for the whole segment, so a chain mixing carriers —
`∀ (d : ℚ) (n : ℕ), …` — let the ℚ binder shield a sibling ℕ binder's
Nat.div/monus in conjuncts that never touch `d`. The review's evidence rows
make the semantics vivid: `4 / m` with `m : ℕ` (Goedel-Pset-846154) is
Nat.div and the covered claim is value-breaking; the `(n − 2) · 180` polygon
rows (216780, 236097) cover a ℕ monus; a VACUOUS `a : ℝ` binder shielded
statement-ℤ `Int.div` (1684555); and a quantifier-ℝ binder shielded a
statement-ℕ `1/a` (968965). Credit where due: the finding is the review's.

**The fix, both halves.** (1) Classifier: when a chain's field carrier mixes
with an integer-or-unknown carrier — its own or the statement's — the field
flag is demoted for that segment, and the division/monus falls to the
integer reading's existing precise gap, the same conservative direction as
the ℕ default for untyped binders. An in-segment textual signal (`↑`, `: ℚ`
ascription, decimal) still legitimizes, exactly as everywhere else.
(2) Audit: `_carrier_residual`'s binder excuse now fires only for PURE-field
chains — before this, its `continue` and the classifier's shield fired on
the same one-boolean signal, so the audit was structurally blind to the
class it guards (the same un-blinding the segment-local review forced on the
concatenated-text audit). Both halves are regression-tested from the
evidence rows, with controls: the `∀ (n : ℕ)`-only variant already refused
correctly, pure-field chains keep dividing, `↑n / 2` keeps its coercion, and
int+field mixes keep `-` (integer subtraction is a real head).

**The correction, counted (per-row dual pass, slice-as-committed → fixed,
all 1.73M rows plus both extracts):** Goedel loses **495** full-statement
covers (331 `integer_division_no_head` + 94 `nat_monus_no_head` in goal
position, 42 + 28 in hypotheses; 457 goal-only), Lean-workbook loses **2**,
miniF2F **0**; no row gains. That is ~9× the review's 56 FLAGGED rows (~35
confirmed on hand-adjudication; the spot-verify later adjudicated ~10 of the
56 as legitimate covers), because the uniform rule also refuses the
elaboration-ambiguous
residue a text-level instrument cannot attribute — `n * (a₁ + aₙ) / 2`
mixes, and only Lean's elaborator knows whether the `/` landed in ℚ via
coercion; `∀ x > M` with `M : ℝ` binds x at ℝ, but the bound's type is
inference the classifier does not perform. Stricter than the review asked,
in the only honest direction — the same trade as the segment-local
correction (6,066 removed against an estimated 3,644).

**Corrected numbers of record:** Goedel-Pset full **747,889 = 43.2%**
(goal-only 895,333 = 51.7%, unique covered 540,405; like-for-like delta vs
the pre-slice record +74,368 full / +65,384 goal-only, LOST still 0 by the
re-run triple pass), Lean-workbook **21,237 = 71.4%**, miniF2F unchanged at
**161 = 33.0%**. Audits `foreign_glyphs = 0, carrier_residual = 0` — the
latter now over a check that can see mixed-chain shielding.

**Two smaller review corrections, same cycle.** (1) A corpus factual error:
`quantifier_negation_universal`'s invariant named "¬∃¬-to-¬∀" as the
intuitionistically surviving direction — a direction valid in no logic; the
valid one is ∃¬ → ¬∀, as the node's own failure_modes always said. Fixed in
the seed, regenerated (node COUNT unchanged, so GC4/GC5 do not move;
re-verified, not assumed). (2) The design note's "alpha-invariant for free"
is a Barendregt-style NAMING CONVENTION, not a theorem: first-occurrence
placeholder numbering is invariant under whole-statement injective renaming,
and the corpus templates deliberately reuse the `{x}` slot across sibling
binders — a future twin authored with distinct inner binder names would NOT
match until normalized. Recorded here so the convention is a documented
choice rather than an accidental claim.

## Language lane — WOLD lexicon: the first empirical multilingual source, and its measured reach (2026-08-12)

**What was pinned.** lexibank/wold `v4.2` (2026-07-17), the CLDF dataset of
the World Loanword Database — release zip SHA-256-pinned in
`data_sources/manifest.json` (`git-lexibank-wold`), license verified INSIDE
the archive (LICENSE = full CC Attribution 4.0 International text;
`metadata.json` declares `CC-BY-4.0`), required citations carried verbatim in
the manifest entry and `data_sources/derived/wold/NOTICE.md`. House rule
applies unchanged: a lexical source enters at **empirical** — it never
grounds a frame verdict and never appears in `verified_by`.

**The extract.** `scripts/ingest_wold.py extract` → committed
`data_sources/derived/wold/lexicon.json` (~0.8 MB): the 1,460 core LWT
meanings (Haspelmath-2009-1460) with word forms for a DECLARED six-vocabulary
subset — English, Dutch, Romanian, Japanese, Vietnamese, MandarinChinese
(11,155 forms). Why these six: English is the repo's realization language;
Dutch is the only vocabulary attesting all 1,460; Romanian is the
highest-coverage Romance vocabulary (Spanish — the natural pick next to
`corpusdata-span` — is only a DONOR language in WOLD, not one of the 41
recipient vocabularies; disclosed, not silently substituted); the last three
are the highest-coverage non-Indo-European vocabularies across three
families. Byte-identical regeneration from the SHA-verified zip, same
discipline as the miniF2F/Lean-workbook extracts.

**The reach number (measure before claiming).** Of the 1,460 meanings, how
many connect to vocabulary the repo has TODAY (`experiments/wold_reach.json`;
exact match after `lemma_key` normalization, no stemming)?

| target | vocab size | mapped | pct |
|---|---|---|---|
| langgen toy lexicon (`experiments/langgen.py`) | 41 | 27 | 1.8% |
| data/*/nodes.json metadata tokens | 817 | 58 | 4.0% |
| Open English WordNet lemmas (pinned OEWN 2025) | 127,311 | 1,394 | 95.5% |
| **mapped to any** | | **1,394** | **95.5%** |

Unmapped: **66** — plurals the no-stemming rule refuses to guess ("embers",
"gums"), pronouns and kin descriptions WordNet has no lemma for ("he/she/it",
"the mother's brother"). The honest reading: WOLD connects to the repo's
*lexical* layer (WordNet) almost completely, and to the repo's *own* concept
vocabulary barely at all (4%) — a concept→multilingual-forms bridge now
exists, but the corpus names ~60 of these everyday concepts. Nothing is
wired into any runtime path in this slice; the number is the deliverable.
## v0.10 item 1 (cont.) — embedded quantifiers: the atom-tree walk

*(2026-08-12, the successor slice the quantifier head named. Measured before
designed; designed before coded — this section is the registered checkpoint.)*

### Step 1 — what the 62,142-row bucket actually is

`quantifier_embedded` is a whole-segment blocker verdict: any ∀/∃ the prefix
extractor did not consume, anywhere in a checked text. Measured composition
(per-row dual pass of a prototype walk against main `82ca355`, all 1,732,402
parsed Goedel rows; positions and shapes from the effective checked text,
i.e. after any supported prefix was already extracted):

| position of the surviving ∀/∃ | rows | share |
|---|---|---|
| top of the goal body, under a connective | 36,584 | 58.9% |
| inside the BODY of a supported prefix chain | 24,801 | 39.9% |
| inside a `let` equation only | 757 | 1.2% |

Top shapes (connective signature at the split point × quantifier mix):
`∧`+forall 5,214+4,538, `→`+exists 3,034+1,702, `↔`+exists 2,658,
`∧`+exists 2,551+2,087, `∧`+forall-depth-2 2,309, `↔`+mixed 2,193,
`∧`+mixed 2,190, `↔`+forall 1,879, `→∧`+exists 1,688, `→`+forall 1,642 — the
iff-of-existence, claim-∧-witness, and hypothesis-∀ shapes the roadmap
predicted, plus long ∧-chains carrying one quantified conjunct.

**What the walk reaches, honestly:** 24,767 of 62,142 goal rows (39.9%)
would cover — every leaf reduces under the EXISTING machinery with no new
head. The other 60% fails a leaf check for reasons the flat blocker was
hiding behind the quantifier glyph, and redistributes to its own precise
labels: `unsupported_symbol:*` 12,989 (mostly `f`,`a`,`x` — the function-slot
backlog measured through one more veil), `no_relation_in_goal` 4,217,
residual `quantifier_embedded` 4,170 (term position: set-builders
`IsLeast {n | ∀ …}`, Prop-valued equalities `(∃ …) = False`, plus the 757
quantified lets — genuinely out), `absolute_value` 3,164, `nat_monus` 2,823,
`vector_or_module_op` 2,150, `quantifier_shadowed_binder` 1,923,
`integer_division` 1,498, `quantifier_function_binder` 1,262, and a long
precise tail. Hypothesis side: of 1,233 `hyp:quantifier_embedded`, 833
would cover. The bucket stays the top FEASIBLE pick: `set_or_finset`
(87,483) and `big_operator` (74,437) are larger but need heads the corpus
does not carry; this slice needs zero new heads.

### Design checkpoint (registered before the classifier changed)

**The walk.** Where the flat path's verdict on a GOAL-BODY or HYPOTHESIS
segment would be `quantifier_embedded` — and only there — the segment is
re-judged by an atom-tree walk: split the text at depth-0 ∧/∨/→/↔ (stopping
at the first depth-0 ∀/∃, whose Lean scope swallows everything rightward),
strip ¬-wrappers and whole-span parens per part, and recurse. Leaves are
either (a) quantifier-led: the EXISTING prefix extractor runs on the leaf,
its binder rules unchanged (ℕ-default for untyped/relation-bounded binders,
bounded-binder desugar, ∃! via the ExistsUnique expansion, precise refusals
for function/structure/sort/malformed binders), and the walk recurses into
the desugared body; or (b) quantifier-free: the leaf must be prop-shaped and
pass every existing blocker/carrier/symbol check. Nothing else changes:
`let` equations keep the `quantifier_embedded` refusal (a quantified let-RHS
is a Prop-valued binding), and a segment the flat path already judged some
other way is not re-judged — so the dual pass can lose nothing and gain only
from the two targeted buckets.

**Scope hygiene, decided in advance.** (1) Binder names are tracked PER
SUBFORMULA: a leaf's bound names extend the value slots and carriers for its
own subtree only. (2) Shadowing is refused on scope OVERLAP: a leaf binder
that collides with a statement binder, a domain var, or an ENCLOSING
quantifier's binder anywhere on its path is `quantifier_shadowed_binder`
(slot-recurrence binding cannot express two carriers for one name in one
scope chain). Disjoint SIBLING scopes reusing a name — `(∃ k, n = 2*k) ∨
(∃ k, n = 2*k+1)` — are alpha-independent and accepted: each occurrence of
the name sits inside exactly one binder's subtree, so skeleton recurrence
stays unambiguous. (3) Carrier honesty is leaf-local, which is strictly
finer than segment-local: a field signal in one conjunct legitimizes `/`/`-`
in that conjunct's subtree only — the mixed-carrier chain shield applies
per quantified leaf against the flags inherited on its path (a ℚ binder in
one branch cannot shield a sibling branch's Nat.div). The one disclosed
asymmetry is inherited unchanged, not widened: a statement-binder field
variable is statement-scoped and reaches every leaf, exactly as it reaches
every segment today. (4) A ∀/∃ that is not leaf-leading after the split —
term position (set-builder bodies, Prop-valued equality operands, function
arguments) — keeps the `quantifier_embedded` label; a recursion-depth cap
(40) refuses adversarially deep nests conservatively.

**Head carriage, verified node-by-node (no corpus change).** The walk
composes only heads the corpus already carries. FORALL/EXISTS under
connectives are exhibited by the 8 quantification laws + 2 witness
definitions: FORALL under IMPLIES (`universal_instantiation`,
`universal_implies_existential`), under NEG (`quantifier_negation_universal`),
under MEET (`universal_conjunction_distribution`, RHS), under `=`/IFF (both
De Morgan nodes, both distribution nodes); EXISTS under IMPLIES
(`existential_generalization`, subalternation), under NEG
(`quantifier_negation_existential`), under JOIN
(`existential_disjunction_distribution`, RHS), under `=`/IFF (De Morgan,
distribution, both witness definitions); nested quantifier-under-quantifier
and IMPLIES-under-FORALL-under-MEET-under-EXISTS
(`unique_existence_expansion`). Two pairs are not pairwise exhibited —
EXISTS directly under MEET, FORALL directly under JOIN — and the claim made
for them is exactly the head-wise standard in force since the miniF2F
write-up ("every internal node is a head the corpus carries"), the same
standard under which MEET/JOIN compositions of relation atoms have been
accepted since the relational slice. No new HEAD is required anywhere in the
walk, so the corpus does not change and the GC pins must not move — the
acknowledgment ledger stays at three entries.

**Registered expectation.** The simulation is an exact mirror of the
production hook (same extractor, same leaf checks), so these are point
expectations and floors at once: Goedel-Pset full **+24,874** (24,041
goal-position + 833 hyp-position) → 772,763 = 44.6%, goal-only **+24,767** →
920,100 = 53.1%; Lean-workbook full **+31** → 21,268 = 71.5%, goal-only +35;
miniF2F full **+2** → 163 = 33.4%, goal-only +2. LOST = 0 per row over all
1.73M + both extracts; every gain from `quantifier_embedded` /
`hyp:quantifier_embedded` only. Refused rows may only move to equal-or-finer
labels (the 12,989-row unmasking of `unsupported_symbol:*` is the largest
single redistributive effect, and is a finding in itself: the function-slot
demand is ~18% bigger than the named `quantifier_function_binder` bucket
shows).

### The delta (adjudication of the registered expectations), full-statement

| source | before | after | Δ | registered | verdict |
|---|---|---|---|---|---|
| miniF2F | 161 = 33.0% | **163 = 33.4%** | +2 | +2 | exact |
| Lean-workbook | 21,237 = 71.4% | **21,268 = 71.5%** | +31 | +31 | exact |
| Goedel-Pset-v1 | 747,889 = 43.2% | **772,763 = 44.6%** | +24,874 | +24,874 | exact |

Goal-only: Goedel 895,333 → **920,100 = 53.1%** (+24,767; unique covered
540,405 → 563,636), Lean-workbook 21,920 = 73.7% (+35), miniF2F 237 = 48.6%
(+2). Every registered value hit to the row — the simulation was an exact
mirror of the production hook, and the dual pass (verify_slice per-row over
all 1.73M + both extracts) proves LOST = 0 with every gain drawn from
`quantifier_embedded` / `hyp:quantifier_embedded` only. Unparsed stays 192;
the parser is untouched. Corpus unchanged (251 nodes / 24 disciplines,
exactly as the design checkpoint required), so the GC pins did not move,
README/nodes counts stand, and the acknowledgment ledger stays at three
entries.

### What the buckets became (Goedel-Pset, goal position)

`quantifier_embedded` collapses 62,142 → **4,170** (term-position residue:
set-builder bodies under `IsLeast/IsGreatest`, Prop-valued equality
operands, quantified lets 757, past-cap nests) and `hyp:quantifier_embedded`
1,233 → 50. The masked defects surface under their own names:
`unsupported_symbol:f` 49,030 → 55,045, `absolute_value` 43,472 → 46,636,
`nat_monus` 41,239 → 44,062, `integer_division` 40,442 → 41,940,
`no_relation_in_goal` 10,971 → 15,188, `vector_or_module_op` 10,783 →
12,933, `quantifier_function_binder` 21,370 → 22,632,
`quantifier_shadowed_binder` 2,779 → 4,702. The top of the gap table is now
`set_or_finset` 87,483 / `big_operator` 74,437 / `unsupported_symbol:f`
55,045 — the first two need heads the corpus does not carry (membership,
big operators), the third is the function-slot design the roadmap already
names. Lean-workbook's embedded residue: 2; miniF2F's: 2.

### The audit fired once at 1.73M, and the catch is a class fix

`foreign_glyphs=1`: Goedel-Pset-251446, a LEGITIMATE cover
(`(¬(∀ {α : ℝ} {n : ℕ} (h : …), ∃ x, …)) ∧ (∀ …)` — NEG∘FORALL against its
un-negated twin, every head carried) whose SECOND consecutive
implicit-binder brace group the audit normalizer left foreign — the old
pattern normalized only a brace group DIRECTLY after the quantifier glyph.
The normalizer now reaches every group of one binder section (crossing
earlier groups, never a comma — the section boundary — nor another brace;
set-builder `|` still excluded) and runs to a fixpoint; negative controls
pin that a brace past the binder comma and a set-builder inside the section
stay foreign. Audits end 0/0 legitimately. Suite 892 → 905 (+12 walk tests
including the negative-control matrix, +1 normalizer regression).

### Review correction — nesting defeated the mixed-carrier shield; the fix is atom contact (fifth cycle)

Independent adversarial review reproduced every mechanical check and then
found the class this slice's own design note failed to carry one level
down: `_tree_walk` demoted only a chain's OWN field carrier — an INHERITED
field flag was never revoked when a descendant leaf declared ℕ/ℤ/unknown
binders. The probe pair makes it exact: `∀ x : ℝ, x = x ∧ ∀ n : ℕ,
n/2*2 = n` covered while its single-chain spelling `∀ (x : ℝ) (n : ℕ), …`
refused — the registered statement-level rule, violated one nesting level
down. Realized rows: Goedel-Pset-704685 (a prefix `∃ l : ℝ` shielding
`4/a` under an inner untyped-ℕ `∀ a > 0`) and 1586260 (an unused statement
binder `(m : ℝ)` shielding `4/x` under ℕ-defaulted `∃ x y` conjuncts).
Credit where due: the finding, the probe pair, and the 1,259-row flip list
are the review's.

**The fix chosen: atom contact, not the blanket revoke.** The reviewer's
hand-adjudication showed most blanket-flips are honest Lean-coercion covers
— the field variable SHARES the atom (`x = f / g` with `x : ℝ` forces the
ℝ reading), which is attribution evidence a text-level instrument can act
on. So field carriers with decidable names now shield walk leaves BY NAME,
on atom contact only: (1) an unmixed quantifier chain's field-typed binder
names join the walk's contact set (gated by the `_q_field_unmixed`
predicate against inherited flags, so identical text gets identical
verdicts in prefix and embedded position); (2) a PURE-field statement's
value vars shield by name too — exact, not approximate, because
`value_vars` only ever holds numerically-typed names, so `has_field` with
no nat/int carrier means every one of them is field-typed; (3) a MIXED
statement keeps the blanket boolean — per-name types of statement binders
are not in the committed extracts, contact is undecidable there, and the
blanket is precisely the flat path's disclosed `r^(n-1)` asymmetry at its
pre-existing width. A leaf with no contact, no textual signal, and no
blanket is demoted to the integer reading's precise gap.

**The correction, counted (exact dual pass, pre-fix classifier vs fixed,
all 1.73M rows + both extracts):** Goedel removes **375** full covers (212
`nat_monus`, 131 `integer_division`, 19+13 hyp-side; 44 quantifier-origin,
319 pure-field-statement, 12 of them same-class rows the review's probe
variant missed) and **regains 7** the old blanket had FALSELY REFUSED —
`Odd p` / `Nat.Prime p` over genuine ℕ binders inside pure-field
statements, where the blanket leaked into the integer-predicate check and
misattributed the field carrier to `p` (`integer_predicate_field_carrier`);
contact fixes both directions, and `Even x` over an actual field var stays
refused because the var is its own contact. Net Goedel **−368** full /
−371 goal-only; Lean-workbook −1 (lean_workbook_15817, the known
honest-cover cost of atom granularity: `x` is pinned to ℝ by the atom that
touches `A`, but the bound conjunct `x − 2 ≠ 0` alone shows no evidence —
refused in the conservative direction, disclosed per precedent); miniF2F 0.
Of the review's 1,259 blanket-flips, 896 keep covering (contact or mixed
blanket, including 160 of the 204 quantifier-origin coercions the sample
adjudicated honest), 363 are removed.

**Numbers of record, corrected:** Goedel-Pset full **772,395 = 44.6%**
(goal-only **919,729 = 53.1%**, unique covered 563,296; like-for-like vs
base +24,506 full / +24,396 goal-only, LOST=0 by the re-run per-row pass),
Lean-workbook **21,267 = 71.5%** (goal-only 21,919, +30/+34 vs base),
miniF2F unchanged **163 = 33.4%**. Audits 0/0. Suite 905 → 912 (+4
nested-shield regressions incl. the probe pair and both realized-row
shapes with positive controls, +3 statement-origin contact/blanket pins).

**Two disclosures attached to the registered design, per house style.**
(1) The design checkpoint's carrier sentence — "the one disclosed asymmetry
is inherited unchanged, not widened" — was INACCURATE as written: the walk
as first landed also blanket-inherited QUANTIFIER-origin field flags into
nested leaves (204 realized rows had no statement field binder at all),
which is a widening this correction removes. The registered text stands
uncorrected above, as registered; this paragraph is the correction. (2) The
carrier-residual audit reads statement + outermost-chain carriers only; a
nested chain's carriers inside a desugared body are invisible to it, so the
ledger audit is structurally blind to this class in both directions — the
guard is the classifier's contact rule plus its regression tests. Making
the audit see nesting would mean reimplementing the walk inside it and
forfeiting its independence; left as a known limit, flagged for the next
review.

## v0.10 item 2 — the external verifier: what a passing check actually certifies (2026-08-12)

Design registered before implementation in `docs/DESIGN-external-verifier.md`
(predictions P1–P9 frozen in §7, adjudicated exact-to-the-row in §8). This
section is the numbers-of-record summary; the argument lives in that note.

**What shipped.** `scripts/external_verifier.py` is a transition authority
with two live backends behind one interface: `lean4` invokes the pinned
toolchain's binary DIRECTLY by path (an absent toolchain is a REFUSAL, never
a download) and requires exit 0, no warnings, and an axiom footprint inside
`{propext, Classical.choice, Quot.sound}`; `python-tests` runs
`py_compile` → `mypy --strict` → `unittest` under a CPython audit hook that
refuses sockets, subprocesses and out-of-sandbox writes — a **discipline**
boundary, not a security boundary, and the verdict's `checks` list says so
rather than claiming a jail. Verdicts are committed ledger objects (LF,
sorted keys, no timestamps, never a bare boolean) over
`{pass, fail, refused}`, and `recheck` re-runs one from its own pins.

**The honesty boundary, which is the point of the item:** a passing check
certifies what it checks, not correctness in general. A `lean4` PASS says
*this pinned source elaborates cleanly under this pinned toolchain and the
named theorem's axiom footprint is inside the allowed set* — not that the
theorem formalizes the prose statement citing it (that stays the
correspondence rung's separate, shape-only claim), and not anything about
bytes it did not pin.

**The first ingested `verified_by`, end to end.** `lean_workbook_1041`
(`13 ∣ 2^30 + 3^60`, from the pinned Lean-workbook extract) is ground
divisibility, decidable in **core Lean** — so the chain is buildable with
the toolchain actually installed: pinned source → PASS verdict (axioms
exactly `[propext]`) → transitions traced by `prover/ExtractData.win.lean`
(not hand-written) → digest pin in the manifest → the node's link →
`verified_by_errors` provenance re-check → correspondence CORRESPONDS. Links
16 → 17; corpus 251 → 253; validator green over 24 corpora.

**Where the bridge stops, recorded where it applies.** `lean_workbook_10202`
(`2^21 ≡ 1 [ZMOD 7]`) needs Mathlib, which is outside the hermetic budget
(multi-GB fetch, network at verification time); it enters `formal` with NO
link and writes that reason into its own `semantic_interpretation`.
`lean_workbook_10411` (`(2014^2015) % 121 = 34`) is TRUE, ground, and still
not provable by the shipped options — `decide` exceeds
`exponentiation.threshold` and closes the declaration with `sorryAx` — so it
is committed as a **FAIL verdict** over its own probe source, referenced by
no artifact and therefore backing nothing. The verifier was NOT taught to
raise the option until the check passed; a verifier that tunes its own
options is not an authority.

**The correspondence rung's second fragment.** Zero-hypothesis goals over
numerals and `+ * ^ % ∣ = ( )` only. `-` (monus), `/` (floor division),
order relations and every identifier are refused, not guessed — the v0.9
`Nat.div` carrier lesson applied to a new surface. Ground templates have no
slots, so CORRESPONDS is exact structural identity and a wrong literal is a
MISMATCH: the `DIVIDES(7, 2^30 + 3^60)` decoy citing the 13 theorem is
adjudicated MISMATCH, and so is a wrong exponent, while the prior 16 links
keep byte-identical verdict AND route.

**Ledger movement (P9).** `group_counts {shape 30, typed 31, family 30,
aliased 32, mirror 5}` — unchanged, the **fifth** consecutive twin null.
GC4 moved by DENOMINATOR DILUTION only: mean groundedness 0.781 → 0.774,
external 0.494 → 0.490, external lower 0.223 → 0.221, min-family-1 recursive
244 → 250 over 126 → 128 statements, with **not one constituent moving on
any channel** (531 exact / 99 pattern / 222 statements-with-constituents all
identical). Both new nodes are fully ground, own nothing anywhere in the
corpus, and contribute groundedness 0.0. The fourth registered
acknowledgment records exactly that, appended without touching the prior
three. Grammar-coverage numbers are untouched this slice by construction:
`scripts/grammar_coverage.py` and the three ingest scripts are byte-identical
to the base commit, so Goedel 44.6% / Lean-workbook 71.5% / miniF2F 33.4%
stand as measured in the previous slice.

**Disclosure.** The first FAIL verdict written embedded this checkout's
absolute path in `evidence.reason` and `evidence.output_tail` (Lean prints
absolute paths in diagnostics), which would have made a committed ledger
reproducible on exactly one machine. The design's byte-reproducibility
clause had named timestamps and key order and missed this. Fixed by folding
pinned inputs' own paths back to their repository-relative names before
anything is digested; both PASS verdicts regenerate byte-identically across
the fix, which is the evidence the fold touched only failing output.

**Second disclosure — the sandbox's write rule had a hole, and it fired.**
The design named ctypes and hostile C extensions as the audit hook's known
evasions. The hole that mattered was neither: the `open` audit event carries
`(path, mode, flags)` and the mode is `None` for every low-level open —
`os.open`, `_io.FileIO`, and CPython's own bytecode-cache writer — while the
hook read only the mode. A `python-tests` run with a cold cache **wrote
`__pycache__` into the repository** and still reported PASS, under a `checks`
line claiming out-of-sandbox writes are refused. The rule reads the flags
now, and the runner is invoked with `-B`; the committed verdict's evidence
digest is byte-identical across the fix, and the cold-cache run is now the
same run as the warm one. The discipline-boundary caveat stands as written —
it just was not the reason this one leaked.

**Third disclosure — the WOLD reach number moved, and moved on PROSE.** The
corpus-token target of the WOLD reach table above (dated 2026-08-12, earlier
the same day) recounts `data/*/nodes.json` metadata tokens, so the two
ingested nodes moved it: vocab 817 → **826**, mapped 58 → **59**, mapped-any
1,394 → **1,395**, unmapped 66 → **65**. The newly mapped meaning is `24-03`
= **WITHOUT** — which entered the token vocabulary from the phrase "formal
WITHOUT a bridge" in `lean_workbook_10202`'s own `semantic_interpretation`,
not from any mathematical content. Worth stating plainly: that target
measures the corpus's PROSE vocabulary as much as its concept vocabulary, so
it will drift with authoring style, and a reading of it as "concepts the
corpus names" is generous by exactly that much. The table above stands as
first measured; `experiments/wold_reach.json` carries the recount, and its
regeneration test is what caught the drift.

## v0.10 item 3 — programming as a first-class discipline

Design registered first: `docs/DESIGN-programming-discipline.md`. Adjudication
exact to the row in that file's §9. Numbers of record here.

**The vocabulary decision.** A `python-tests` verdict MAY ground a
`verified_by` link, with `system: "python-tests"`. PROVEN stays
`system == lean4`. The three programming nodes are `epistemic_status:
formal` and write the honesty boundary at node level. Correspondence
still scores 16 CORRESPONDS / 1 UNTRANSLATABLE / 0 MISMATCH over the 17
lean4 links; the three new citations are skipped, not UNTRANSLATABLE.

**Source.** TheAlgorithms/Python `maths/greatest_common_divisor.py` at
commit `f5988cc`, MIT, one-file pin. CodeNet declined (submission terms).
thuva4/Algorithms declined as primary (TypeScript). Stein is first-party
and disclosed as the name-similar non-twin.

**End-to-end.** Three PASS verdicts, three manifest entries, three nodes
generated by `seed_programming.py` under the verdict-backed rule. The
drop-abs mutation is a committed FAIL, cited by no artifact and no node;
`recheck` reproduces `fail`. Validator green over 256 nodes / 25 corpora.

**Twins vs the name baseline.** T_rec and T_it share the typed skeleton
`GCD⟨?0:V, ?1:V⟩ = ITE⟨EQ⟨?0:V, 0⟩, ABS⟨?1:V⟩, GCD⟨?0:V, MOD⟨?1:V, ?0:V⟩⟩⟩`
and form one group of size 2 at shape/typed/family/aliased. T_st is in
none of those groups. The token-`gcd` baseline forms all 3 pairs on the
named set. Matcher precision 1.0 vs baseline 1/3; both recall the true
pair. Zero parse problems, zero slot gaps.

**Ledgers (P9).** Corpus 253 → 256, disciplines 24 → 25. `group_counts`
{shape 31, typed 32, family 31, aliased 33, mirror 5} — the first
twin-group movement after five consecutive nulls, registered before the
matcher ran. GC4: mean 0.774 → 0.779, exact 531 → 550, pattern 99 → 100,
statements-with-constituents 222 → 226, external 0.490 → 0.499, external
lower 0.221 → 0.223. Not dilution: the Euclid pair are self-headed GCD
recurrences (groundedness 1.0); Stein is 0.455. Absorption count floor
holds (387 > 4 × 86). Rate gap 0.164 → 0.156. Fifth acknowledgment
appended to `tests/test_decompose_channels.py`.

**Specialization (P10).** `specialize.py` ran unchanged and exited 0. The
Euclid pair are twins, not a general/specific nest; no programming
specialization edge is claimed.
## v0.10 item 5 — one real session, recorded: the ingested layer starts grounding itself (2026-08-12)

Design and frozen predictions in `docs/DESIGN-v010-harness-session.md`;
§7 adjudicates P1–P7 exact to the row. The record itself is
`experiments/harness_session.json`, emitted from the components' own
structured objects (`SessionEvent`, `DispatchEvent`, verdict JSON,
`StagingRecord`, `AcceptanceRecord`) rather than re-typed prose, and
re-verifiable with `python scripts/session_run.py --check`.

**What ran.** One booted session, four recorded legs, no new surface.
(A) A need the corpus could not meet — `numbertheory.ingested.lean_workbook_22080`,
dispatched, every registered path abstained. The external verifier re-checked
its committed verdict over the pinned source `prover/lean/session/Session22080.lean`;
the transitions were traced by `prover/ExtractData.win.lean` and post-processed
by the new `scripts/trace_to_triples.py`; the WRITE gate ran **sixteen checks**
and applied the candidate, adding the node by regenerating the corpus from the
seed it accepted. (A′) The same need, dispatched again by the NEXT session:
**SOLVED, materialized** — the running session's store is a boot-time snapshot,
so the write it applied is not visible to itself, which is recorded rather than
hidden. (B) The same-shaped statement one exponent too large,
`(2^2006) % 7 = 4`: the verifier FAILED it on the axiom audit (`sorryAx`, the
default `exponentiation.threshold`), and the gate refused the candidate too, at
`theorem_closure`. Two independent refusals, working tree byte-identical.
(C) "why did the chicken cross the road?", routed to a path the boot matrix did
not register: `exhausted`, nothing minted, the abstention worded by the
dispatcher itself (P-IH4).

**The number that matters, and the prediction it broke.** Corpus 253 → 254,
`verified_by` links 17 → 18, `group_counts {30, 31, 30, 32, 5}` unchanged — a
SIXTH consecutive twin null, and the first one the WRITE gate checked ITSELF,
because it refuses a PROVEN candidate that has not declared its matcher delta
in advance ("an undeclared delta is an unregistered prediction"). But GC4 did
**not** move by denominator dilution the way the four previous corpus-growth
acknowledgments did: exact constituents 531 → **533**, statements with at
least one grounded constituent 222 → **224**, mean groundedness 0.774 →
**0.775 (up)**, external channel mean 0.490 → 0.488.

The reason is the result: the session's node is `MOD(2 ^ 30, 1000) = 824`, and
it shares the subterm `2 ^ 30` with the first ingested statement,
`DIVIDES(13, 2 ^ 30 + 3 ^ 60)`. Each grounds the other through the
`prior_corpus` channel — two new exact constituents, both `^(2, 30)`,
`recurs_in_n_statements: 2`, on the shared discipline `number_theory` rather
than the `mathematics` umbrella the corpus's other four prior_corpus
constituents carry. **The ingested layer began grounding itself.** Nothing was
taught to look for this; the decomposition ledger found it the moment a second
ingested statement existed. It is a two-constituent result on a 254-node
corpus and proves nothing about scale — but it is the first evidence that
ingestion compounds rather than merely accumulating, which is the whole bet of
ROADMAP-v0.10 item 4.

**What the gate taught the session, recorded because it constrains the next
one.** The declarative WRITE lane stages NEW seed / NEW corpus pairs only:
appending to an existing corpus "needs a trusted patch format"
(`seed_ownership`), the carried-open multi-corpus WRITE patch of ROADMAP-v0.10
§7. So the design's plan to append to `data/number_theory` was refused, and the
node landed in a new corpus `data/ingested_arithmetic/` — corpora 24 → 25. Until
that patch format lands, **no session can add a statement to an existing
corpus**, which is a real constraint on item 4's authoring-at-scale plan and is
better learned here than there.

**Disclosure.** P1 predicted the new verdict's axiom footprint would be
`[propext]`, by analogy with the first bridge. It is `[]`: `%` on ℕ decides
without propext where `∣` needed it. The prediction was wrong in a direction
that makes the claim stronger, which is exactly why it had to name the set
rather than the direction. P5 asked for a byte-identical re-run of the
transcript; a session that mutates the corpus cannot deliver that by
construction, so `--check` re-verifies the record instead. Both stand
uncorrected in §6 and adjudicated in §7.

**Post-rebase note (item 3 landed first).** The section above measured item 5
against `9553db9`. The programming-discipline slice merged first, so the
numbers as merged are: corpus 256 → **257** across 26 corpora, `verified_by`
21 links (18 lean4 + 3 python-tests), exact constituents 550 → **552**,
statements-with-constituents 226 → **228**, mean groundedness 0.779
(unchanged at three places), external 0.499 → **0.497**. Two corrections
follow from that ordering and are recorded rather than smoothed. (1) The
"sixth consecutive twin null" above is **wrong as merged**: item 3's Euclid
pair formed a new twin group and ended the streak first. `group_counts` is
genuinely unmoved by this node, but the streak claim belonged to the older
base. (2) The absorption rate-gap pin moved a third time, 0.156 → **0.159**,
because two new exact constituents change that channel's denominator; the
count floor holds unweakened (387 > 4 × a_best). That pin has now been
re-pinned against its original guard direction by three consecutive slices
and goes to release triage for sign-off. The self-grounding finding is
unaffected: both ingested statements still ground each other's `^(2, 30)`.

---

## v0.10 item 4 — first wave of covered ingest, and the baseline on hundreds

Registered in `docs/DESIGN-item4-authoring.md` (and Slice A's
`docs/DESIGN-write-append.md`) before the generator ran.

**What landed.** 251 parse-clean unique-covered Lean-workbook ground
identities as `data/lean_workbook/nodes.json` (257 → **508** nodes, 26 →
**27** corpora). Formal without `verified_by` (item 2 decision (b),
recorded on every node). The coverage instrument marked 302 such goals;
51 fail to tokenize because `TOKEN_RE` has `<=` `>=` but not standalone
`<` `>` even though both glyphs are already in `RELATIONS`. The seed
filters through the same parser the matcher uses. Slice A (trusted
`append_nodes` JSON, never executed) is the session-scale path; this
wave used a generator seed.

**The roadmap question.** Does a capability-blind baseline that won on
221 curated nodes still win on ingested ones? The operator-bag (same
set of `{+,-,*,/,^,=}`) still wins on pair count and loses harder on
precision:

| graph | bag pairs | matcher pairs | bag precision |
|---|---:|---:|---:|
| 257 prior | 4,345 | 88 | 2.03% |
| 251 ingested only | 1,489 | 8 | 0.54% |
| 508 combined | 7,622 | 96 | 1.26% |

Matcher precision against the bag stays **1.0**. The eight new typed
pairs are ingested-to-ingested parenthesization / commutativity twins;
none twin with a curated slotted law. Regenerable:
`scripts/measure_operator_bag.py`.

**Compounding, not accumulation.** Exact constituents 552 → **1235**;
614 of the new ones are `same_corpus` inside the new corpus. A third
statement now shares `^(2, 30)` with the two earlier ingested nodes.
Mean groundedness 0.779 → **0.577** because the new layer's own mean is
0.368, not because the old nodes were diluted by zeros. Pattern
membership stays 100.

**Rate-gap, flagged.** 0.159 → **0.490**. The exact channel's external
rate fell 70% → 37% while absorption stayed 86/100. The count floor
*strengthened* (4.5:1 → 5.3:1). This is the fourth re-pin against the
original guard direction and is queued for maintainer sign-off, not
absorbed as a new normal.

**Honest limit.** This is hundreds, not the 12,681 unique-covered set.
The rest wait on a skeleton emitter. `specialize.py` and `decompose.py`
needed scoring-adjacent skips (fully-ground trees are not specialize
endpoints; slot-free trees cannot be decompose patterns) to finish
inside the ledger timeout; the 713 pre-ingest specialization edges are
byte-identical.

---

## v0.11 prerequisite — skeleton emitter for the unique-covered remainder

Registered in `docs/DESIGN-skeleton-emitter.md` before the emitter
authored any new node. Bucket census of the 12,681 was measured
read-only before the emitter existed.

**What landed.** A Lean-surface → matcher-template emitter
(`scripts/emit_skeleton.py`). `TOKEN_RE` accepts standalone `<` `>`
(`<=` `>=` still win). Seed emits **12,514** ingested nodes (302
ground + 12,212 emitted) into `data/lean_workbook/nodes.json`. **123**
excluded, bucketed in `experiments/lean_workbook_emit.json`. Corpus
508 → **12,771**. Formal without `verified_by`.

**Matcher.** parse_problems **0**, slot_schema_gaps **0**.
`group_counts` `{35,36,35,37,5}` → `{1027,972,971,973,5}`. Shared
inequality skeletons twin (P-E3).

**Ledgers, bounded.** specialize skips ingested endpoints: **713**
edges unchanged (P-E4). decompose skips ingested-only patterns and
skips `pattern_cover` on ingested statements (P-E5b, disclosed after
an 8-minute no-output run). Exact **181,867**, pattern **88** (was
100: exact now owns former pattern-only skeletons), mean **0.862**,
statements-with-constituents **12,612**. Graph same_corpus 0.466 /
external 0.391; `lean_workbook.ground.v1` is same-corpus-dominant
(0.473 > 0.387). That is the curve's substrate, not S1–S4.

**Honest limit.** `reports/decompositions.json` is not rewritten at
this scale (181k constituents × owner lists). Live `analyze` is the
pin source.

---

## v0.11 item 1 — self-grounding curve against its null

Registered in `docs/DESIGN-self-grounding-ingestion.md` before the
12k corpus existed. Route 1 (owner ids), decided in writing before
this run. Generator: `scripts/measure_self_grounding.py`. Specialize
was not invoked. Pattern membership off; equivalent here because
ingested statements already skip `pattern_cover`.

**The question.** As ingested nodes go from 8 to 12,515, does the
share of considered subterms whose most-independent owner is another
ingested node rise faster than a distribution-matched synthetic null?

**S1–S4 all FIRED.**

| N | ISG_real | ISG_null | gap | XSG_real | considered (real) |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.018 | 0.059 | −0.041 | 0.423 | 111 |
| 32 | 0.098 | 0.122 | −0.024 | 0.400 | 492 |
| 128 | 0.229 | 0.183 | +0.046 | 0.428 | 1,939 |
| 512 | 0.308 | 0.266 | +0.042 | 0.413 | 8,546 |
| 12,515 | 0.473 | 0.410 | +0.063 | 0.397 | 208,404 |

Null spread at N=12,515 is 0.14 points (three seeds). The 6.3-point
gap is ~45× that spread.

Reading:

- **Small N is the design's own warning.** At 8 and 32 the real layer
  sits *below* the null. Two shared squares (`^(?0:V, 2)` is the most
  common real subterm at every N) and a handful of numerals do not
  beat random trees drawn from the same operator/numeral inventory.
  A curve stopped at hundreds could have been reported as "flat."
- **The sign flips by N=128 and the last gap is the largest.**
  Spearman(N, gap) = 0.90. 128 → 512 dips 0.046 → 0.042 (not a
  staircase); 12,515 is 0.063. Compounding is the trend.
- **XSG barely moves.** 0.423 → 0.397. The ingested layer did not
  buy self-grounding by shedding the curated one. S3's load-bearing
  half.
- **S4 is stronger than S1, which is the opposite of the feared
  failure.** Dropping `^(?0:V, 2)` (6,870 hosts, 26,321 occurrences)
  *raises* ISG_real to 0.541 and the gap to 0.127. The popular term
  is XSG-heavy — squares curated algebra already owns — so it was
  diluting the rate, not carrying it.
- **The proxy is almost 1.0 and is not the measurement.** At full N,
  181,270 / 181,276 grounded constituents have some ingested
  co-host (proxy 0.99997); only 98,499 have an ingested
  most-independent owner (ISG_of_grounded 0.543). Route 2 would have
  published "everything compounds." Mixed winning-channel owners: 2.

**Null honesty.** Synthetic trees, sampled from the observed head /
arity / numeral / slot / relation / size / discipline inventory, are
systematically shallower than the real Lean statements (68k vs 208k
considered at the same N). Smaller trees share `inv` / `neg` more
readily, which *raises* ISG_null. The real curve beat a null that
was easy to share and still won on owner-attributed grounding.

**What this is not.** Self-grounding is a structural fact about the
graph. It is not correctness, usefulness, or proof. The 12k nodes
remain formal-without-bridge.

---

## v0.11 item 2 — one figure of merit for the bag

Registered in `docs/DESIGN-fair-fight.md` before this re-run. The
figure of merit is bag precision against typed twins. The bag was
not retuned (glyphs still `{+,-,*,/,^,=}`).

**FF1–FF5 all FIRED.**

| slice | nodes | bag pairs | matcher pairs | bag precision | k |
|---|---:|---:|---:|---:|---:|
| 257 prior (v0.10) | 257 | 4,345 | 88 | 2.03% | 0 |
| 508 combined (v0.10) | 508 | 7,622 | 96 | 1.26% | 0 |
| 256 curated (now) | 256 | 4,341 | 88 | 2.03% | 0 |
| 12,515 ingested | 12,515 | 9,010,102 | 1,879 | 0.0209% | 0 |
| 12,771 full | 12,771 | 9,041,744 | 1,991 | **0.0220%** | 1 |

Matcher precision 1,990/1,991 = 0.9995. The one miss is
`leanworkbook.skel.lean_workbook_49137` vs
`trigonometry.identities.double_angle_cosine` (emitter `+ -(...)`
vs curated infix `-`). Size-matched draw (seed 20260814): 1 twin
in 1,991 bag pairs.

The skeptic sentence, as registered: the bag still wins on count
and still loses on the only figure of merit that does not restate
its definition, and the matcher misses only the print-convention
pair. F1 against either gold is `2p/(1+p)` of bag precision — a
transform, not a second measurement. Regenerable:
`scripts/measure_operator_bag.py`.

---

## v0.11 item 3 — programming second wave, volume, vocabulary survives

Design registered first: `docs/DESIGN-programming-second-wave.md`.
Adjudication exact to the row in that file's §9.

**The vocabulary decision survives.** Nine programming nodes cite
`system: "python-tests"`, stay `formal`, and write the honesty
sentence. Retrieval still mints no `proof:programming.*`.
Correspondence stays 16 / 1 / 0 over the 18 lean4 links. A
`range(20)` library comparison is a stronger computational claim
than eight doctests and is still not a proof.

**Source.** Same TheAlgorithms/Python pin, commit `f5988cc`, MIT.
Three files added: `maths/factorial.py`, `maths/double_factorial.py`,
`maths/binary_exponentiation.py`. Extract holds eight functions;
the two modular exponentiation variants were declined (already have
an ingested foil family). Stein stays first-party.

**Volume.** Each FACT/DFACT test module loops `range(20)` against
`math.factorial` / `math.prod`. BEXP adds a `range(16) × 6 bases`
loop against `**` as a disclosed expansion of the source \(a^b\)
claim. The n-minus-2 mutation agrees on `{0,1}` and fails at 3;
the volume loop is what catches it.

**Twins vs the keyword baseline (H3 substrate).** Three new typed
groups of size 2. Token-`factorial` baseline: 6 pairs, matcher 2,
precision 1.0 vs 1/3. Token-`exponentiation` on the two-node BEXP
set ties (1 vs 1). Combined programming-keyword baseline
(`gcd`/`factorial`/`exponentiation`): 10 pairs vs 4, precision 0.4.
group_counts {1027, 972, 971, 973, 5} → {1030, 975, 974, 976, 5}.

**Ledgers.** Corpus 12,771 → 12,777. `verified_by` 21 → 27
(18 lean4 + 9 python-tests). GC4: mean 0.862 → 0.863, exact 181867
→ 181909, pattern 88 → 89, with-constituents 12612 → 12618.
`programming.core.v1` now trips `self_certifying_lower` (mean 0.939)
but not the generous flag — first corpus besides provability to do
so. Ninth acknowledgment in `tests/test_decompose_channels.py`.
specialize.py still 713 curated edges; no programming nest claimed.

---

# v0.12 — the held-out cycle

## Item 1: held-out structure recovery (H1-H6)

Generator `scripts/measure_heldout_recovery.py`, route 1,
`pattern_membership=False`, null seeds 0/1/2, selection seed 20260816.
Each holdout is a quarantined corpus; the other holdout is never loaded
into a run, and everything in `data/` -- including the 12,514
Lean-workbook templates -- is the fixed curated-relative layer.

| holdout | N | real ISG | null mean | gap |
|---|---:|---:|---:|---:|
| miniF2F (A) | 8 | 0.00000 | 0.01626 | -0.01626 |
| | 32 | 0.00000 | 0.00991 | -0.00991 |
| | 157 | 0.00547 | 0.04823 | -0.04276 |
| Goedel-Pset (B) | 8 | 0.00000 | 0.00000 | 0.00000 (degenerate) |
| | 32 | 0.00000 | 0.00936 | -0.00936 |
| | 128 | 0.00725 | 0.05354 | -0.04629 |
| | 512 | 0.01442 | 0.10750 | -0.09308 |
| | 1896 | 0.02537 | 0.15125 | **-0.12588** |

H1 **MISSED** (real far below null, gap monotonically more negative).
H2 FIRED (both holdouts at/below null at N=8 and 32). H3 FIRED but
weakly -- bag_gap -0.0058 with the bag saturated at 0.9937 vs 0.9995,
so it discriminates nothing in a world where H1 missed. H4 FIRED
decisively (proxy - ISG_of_grounded: 0.7003 on A, 0.8835 on B). H5
MISSED and could not have fired -- it tests whether H1 survives dropping
the top subterm, and H1 never held; dropping `^(?0:V, 2)` moves the gap
-0.12588 -> -0.12474. H6 FIRED (isg_rise 0.0254 vs xsg_fall 0.0055).

Goedel-Pset N=8 is degenerate: real 0.0 with all three nulls 0.0. Two
zeros are not an agreement; excluded from the trend.

## C1: the matched-N control

Registered at 1b7b34f before the cell was computed.
`scripts/measure_self_grounding.py --sizes 157 --no-all`.

| source | real ISG | null mean | null seeds | gap |
|---|---:|---:|---|---:|
| Lean-workbook | 0.24194 | 0.19235 | 0.18203 / 0.20791 / 0.18710 | **+0.04959** |
| miniF2F | 0.00547 | 0.04823 | 0.04211 / 0.06225 / 0.04035 | **-0.04276** |

C1 FIRED on both clauses: opposite sign, and separated by 0.09235
against combined null spreads of 0.04778 (1.9x). Vacuity passed --
neither null near zero. Raw rates at matched N differ 44x; the proxy on
Lean-workbook at 157 reads 0.992, saturating for the third time in two
cycles.

## Emitter reach on unfitted sources

| source | considered | emitted | excluded | rate |
|---|---:|---:|---:|---:|
| Lean-workbook (fitted, v0.11) | 12,637 | 12,514 | 123 | 99.03% |
| miniF2F (held-out A) | 160 | 157 | 3 | 98.12% |
| Goedel-Pset (held-out B) | 2,048 | 1,896 | 152 | 92.58% |

Goedel-Pset exclusions: `parse_fail` 114 vs `emit:` 38 -- B3 MISSED,
a 3:1 inversion of both priors, and the first sample large enough to
test it. 101 of the 114 (88.6%) carry one unrewritten constant,
`Real.pi`, so 66% of all exclusions trace to a single unmapped nullary.
Not fixed: design §3 forbids widening the emitter for a held-out source.

## Item 5 and the conversational surface

P-LS1-P-LS5 all fired (`docs/DESIGN-live-session.md` §8). Routes added
after the refuse/abstain loop: exact ownership lookup, pooled-evidence
resolution, WordNet glosses, exact arithmetic and relation checking,
belief frames, the verified story.

Text resolution, registered before each run:

| | measure | result |
|---|---|---|
| T1/T2 | dev coverage / refusal | 1.0 / 0.9167 (T2 missed) |
| S1/S2 | curated self-bind / precision | 0.6985 / 0.9385 (S2 missed) |
| S5 | ingested structural reach | 0.8127 (missed) |
| R1-R4 | holdout 1 | 0.9444 / **0.80 (missed)** / 6/6 / 4/4 |
| R5-R8 | holdout 2, harder refuse arm | 0.9375 / 0.9167 / 6/6 / 4/4 |
| F1 | 500 unselected WordNet sentences | 0.046 |
| F2 | 1000, strict convergence | 0.008 |
| F3 | 1000, shipping code | **0.030** |

The precision/recall curve, measured not assumed:

| rule | false positives | in-corpus coverage |
|---|---:|---:|
| no convergence | 0.046 | 0.944 |
| winner-support (ships) | 0.030 | 0.833 |
| full intersection | 0.006 | 0.611 |

Refuted en route: WordNet hypernym roots do not separate leaked glosses
from real questions -- both land under the same shallow ancestors, so
the remaining error is not addressable by lexical semantics.

Cost: index build 3.98s over 12,777 nodes (219,416 subterm occurrences,
38,858 distinct skeletons), then 0.04us per resolution (~24M/sec),
single core, no GPU.

## v0.13 A1 — ambiguity-rate prerequisite

A1 was registered in `docs/DESIGN-ambiguity-and-context.md` before the
measurement: at least 25% of the development and holdout questions registered
as `expect=resolve` end in ASK. The reviewed result is:

| set | registered | BIND | ASK | PASS | ASK / registered |
|---|---:|---:|---:|---:|---:|
| development | 28 | 21 | 7 | 0 | 0.2500 |
| holdout 1 | 18 | 9 | 6 | 3 | 0.3333 |
| holdout 2 | 16 | 13 | 3 | 0 | 0.1875 |
| **pooled** | **62** | **43** | **16** | **3** | **0.2581** |

**A1 FIRED, narrowly.** The first implementation reported 0.2712 (16/59),
conditioning on BIND + ASK and silently excluding the three registered
holdout-1 questions that ended in PASS. That denominator contradicted the
query files' own definition of `expect=resolve` as corpus-covered. Review
corrected the denominator to all 62 registered in-corpus questions. The
verdict survives; its margin above 0.25 shrinks from 0.0212 to 0.0081, and
holdout 2 misses on its own. The initial number remains recorded because the
project reports corrections rather than erasing them.

The unregistered candidate-size probe is median 2, maximum 6, with 10 of 16
ASK sets at size two or three and none above ten. This describes the starting
shape; it does not adjudicate A2's registered claim that context halves those
sets. `experiments/ambiguity_rate.json` pins SHA-256 digests for all three
query files, the measurement/resolver sources, and the complete corpus-node
manifest so later query, implementation, or data drift is detectable without
rescoring this registered result.

---

# v0.13 — conversational coverage holdout 3

The complete set, scorer, fresh WordNet seed, archive digest and predictions
C3-1--C3-4/F4 were committed at `110fff4` before either new set was run.
The only implementation (`7a9c7c3`) applied conservative query-side surface
morphology to spellings already present in committed keyword, prose and
`symbol_lexicon` indexes. No holdout miss authored a rule.

Scored once:

| measure | registered bar | result |
|---|---:|---:|
| C3-1 reach coverage | >= 0.875 | **24/24 = 1.000, FIRED** |
| C3-2 registered-target recall | >= 0.833 | **23/24 = 0.9583, FIRED** |
| C3-3 wrong single binds | 0 | **1, MISSED** |
| C3-4 exact-title blind recall | < 1.0 and below resolver | **0.9167 vs 0.9583, FIRED** |
| F4 pinned-OEWN false positives | <= 0.030 | **34/1000 = 0.034, MISSED** |

Morphology 8/8 and lexicon 8/8 recalled their registered targets; controls
recalled 7/8. The miss is sharper than a refusal: `interest accumulated
without compounding` BINDs `economics.finance.continuous_compounding`. Word
overlap has no representation of the negative contrast in `without`.

The blind control is non-perfect but weak. One one-word title-overlap tie has
14,571 candidates; target inclusion in a set that large is not useful
resolution. It establishes only that exact title tokens do not attain 24/24,
not that the resolver wins a hard ranking baseline.

F4 used OEWN 2025 SHA-256
`7d749f6e2c39e6970e4997839dcf6e42fd281f3c2fae0171d2192bae8cfa4b51`,
seed 20260818, with no screening. Its 0.034 is four extra claims per thousand
above F3's 0.030. Because the preregistered gate required coverage up **and**
F-rate not worse, the conjunction failed. `98e0d36` reverted the resolver
exactly. The honest result is a rejected precision/coverage trade, not 1.000
shipping coverage. The fresh-seed comparison does not identify a causal
effect of morphology; it adjudicates the frozen shipping rule.

Regenerable from the spent specifications for audit only:
`scripts/measure_text_resolution_holdout3.py` and
`scripts/measure_false_positive_f4.py`. The committed ledgers are
`experiments/text_resolution_holdout3_result.json` and
`experiments/false_positive_rate_f4.json`; governance forbids using a rerun as
a new score.

**Raw-ledger repair, without a rerun.** Independent review found that the
committed holdout ledger was the compact post-run view. The full output was
recoverable from Git's object store because it had been staged first: blob
`16abf1c51f449a3067b562d1dbeb9c7ae0871804`, 749,574 LF bytes, SHA-256
`ffa68c7659c36a589f37e04a679d195b62c074cd564ca20f2ce7feb5c90b4532`.
It is now committed as `text_resolution_holdout3_result.raw.json` and retains
all blind candidate ids. The compact file is verified as one exact transform
of the raw rows (full list -> count + first 25; nothing else changes), not
called the one-shot ledger. `text_resolution_holdout3_provenance.json` records
preregistration tree `2aa1d3c`, candidate tree `564c9e8`, and the exact spec,
resolver, holdout-scorer and F4-scorer blobs. The recovery makes C3-4's baseline
inclusion independently inspectable; it does not make the 14,571-way tie a
strong baseline.

## v0.13 P-LS6 implementation; A2 protocol refused before scoring

P-LS6 **FIRED** on its bounded contract.  Resolver ASK state now survives
input turns and can be intersected only by explicit `narrow` constraints.
There is no relative score: zero matches preserve the ASK, ties keep asking,
and a singleton is returned only with a committed title or statement meaning.
`cancel`, repeated-state `cycle`, and a four-hop `hop_ceiling` are visible
terminal outcomes, and the real binary stops on the terminal statuses.
Registered commands and new questions escape clarification; a new ASK
replaces the prior one.  The focused context, harness, and probe suite ran 56
tests green (one skipped) before any aggregate experiment.

**A2 was not scored.** Its frozen sentence names three legal follow-up classes
and the ASK population in two existing holdouts, but those holdouts contain no
follow-up lines or intended retained readings.  An attempted v0.13 scorer
filled those fields after the resolver candidates were inspectable and did not
initially prove that every ASK row was included.  Review rejected that as an
oracle-selectable denominator before commit and before aggregate execution.
Publishing its favorable reductions would turn implementation knowledge into
a preregistered-looking result, so the tool and authored rows do not ship.
A2 and its aggregate A3 check remain unadjudicated.  A4's Buffalo-class
demonstration is also unimplemented and unadjudicated.

---

# v0.13 — groundedness-at-all admission

Design commit `3fe54cf28bdbcf9870538daf888898c9b234ac21` froze prose for
the 0.50 threshold, three seeds, foil concept, and G1–G4 bars before score
inspection. It did not contain the generator or tests: those first landed
together with this ledger at
`943c87cd9ddc7f381c8b20c316c4871c2e89707d`. The exact executable choices
were therefore not Git-frozen before the result. This section retains the
negative measurement as reproducible exploratory/post-hoc implementation
evidence, not a fully auditable preregistered one-shot.
Each source/seed cell contains 64 statement-level authentic/foil pairs. A
foil swaps one internal `call`/`op` head with a peer of the same kind and
arity. Relation, head-blind tree, leaves, considered topology, and the batch
head histogram are identical. Candidate-to-candidate owners are excluded;
only exact constituent owners already present in `data/` count.

| source (three-seed mean) | authentic acceptance | foil rejection | balanced accuracy | paired accuracy | authentic − foil score |
|---|---:|---:|---:|---:|---:|
| miniF2F | 0.8698 | 0.1406 | **0.5052** | 0.6068 | +0.0288 |
| Goedel-Pset | 0.6458 | 0.3750 | **0.5104** | 0.5859 | +0.0245 |

The exploratory ledger labels G3 **FIRED**: all six construction cells pass
and the blind paired baseline is 0.5. It labels G1 **MISSED**: balanced
accuracy is effectively chance on both sources, far below the prose-stated
0.70; G2 **MISSED**: paired accuracy is below 0.75 on both; and G4 **FIRED**:
the mean margin is positive on both, but only 2.5–2.9 points and produces no
usable admission decision.

Raw counts make the failure concrete. Of 192 examples per arm and source,
miniF2F admits 167 authentic statements and rejects only 27 foils;
Goedel-Pset admits 124 authentic statements and rejects 72 foils. The signal
recognizes a small average disturbance while retaining nearly all of the
local pieces that make the near-miss look grounded. The v0.12 unregistered
probe separated real corpora from random trees; this exploratory result is
evidence that the separation does not survive this implementation of a
plausible local edit. No threshold or mutation is tuned after the result. The
gate parks; a future registered claim needs precommitted executable code and a
fresh holdout.

**Release audit correction.** The scores and rows above are unchanged.  The
first ledger hashed two holdout files through a Windows CRLF working copy,
which did not match the LF bytes in Git on a fresh checkout.  Source digests
now use canonical-LF SHA-256 for all fixed and holdout inputs, and attributes
pin the generated holdout/emit ledgers to LF.  This repairs reproducibility;
it does not upgrade the exploratory provenance status.

---

# v0.14 — clarification preregistration (no result)

The evaluator prerequisite is frozen before candidate implementation.  It
contains exactly 48 rows: 8 negative BIND predictions, 8 negative ASK
predictions, 12 ordinary ASK predictions, 10 ordinary BIND predictions, and
10 PASS predictions.  The 38 distinct primary ids span 20 top-level prefixes;
the 20 ASK follow-ups are fixed at 6 corpus, 6 discipline, and 8 word
constraints.  Construction validation checks exact schemas, pairwise and
prior-query freshness below 0.50 trigram Jaccard, an independently
regenerable 88-id spent-set exclusion, target existence, and veto inventories.

The external precision arm is also construction-only: three 1,000-key OEWN
samples at seeds 20260825–20260827 have key digests
`f179218f…fd31`, `54b3d90f…6fba`, and `98cd28dc…84f8`.  They exclude the
canonical F4 reconstruction, all 34 published F4 claimed texts, normalized
duplicates, and prior new arms.  Because F4 did not retain the other 966 keys
or its Python runtime, absolute historical overlap is unprovable and is not
claimed.  No licensed text or reversible key is committed.

One registered ambiguity is resolved in writing before the run rather than
after it.  The design says non-Q2 metrics credit only `primary_id` while the
blind follow-up statistic is “computed identically to Q2”, and Q2 requires every
declared retained id.  All 20 ASK rows in fact declare a **singleton**
`retained_ids` equal to their own primary id, and the structural validator
enforces exactly 58 credit declarations, so a multi-id retained set is refused
rather than merely unused.  On this holdout the two readings therefore
coincide: Q2 retention, blind-arm retention, and primary retention are the same
predicate.  The consequence is recorded rather than repaired — v0.14 does not
test whether clarification preserves several simultaneously intended readings,
only whether it keeps the one intended reading while at least halving the set.

Implementing against the frozen evaluator immediately falsified two of its
own assertions, and the repair is recorded here rather than folded in
quietly.  `test_candidate_scoring_api_is_deliberately_absent` imported the
live resolver to prove no candidate existed, and
`test_no_result_exists_in_preregistration` checked the working tree for a
result file.  Both are true only until v0.14 succeeds: the first goes red the
moment `resolve_negative` lands, the second the moment the one-shot run
writes its ledger — and both live in a file the candidate commit is forbidden
to touch.  The release gate demanding a green suite at the frozen tip was
therefore unsatisfiable by construction.  Commit `3c17718` remains the
preregistration; the amendment re-asks both questions of that commit's Git
objects, which answer them permanently, and exercises the scorer's refusal
against a stub module that really lacks the API.  No row, threshold,
denominator, prediction, or scoring path changed, and the amendment landed
before any candidate output existed.

No v0.14 row has been resolved, no OEWN sentence has been classified, and no
Q1–Q6 score or candidate result exists.  The only executed checks are
construction/provenance and synthetic vacuity tests.  The raw-before-compact
one-shot path refuses until the preregistration is an ancestor of a clean,
allowlisted candidate commit.

---

# v0.14 — the one-shot clarification result (Q3 fired; Q1, Q2, Q4, Q5, Q6 missed)

The holdout and the three mechanical arms ran once, against preregistration
commit `d53bb2e` and candidate commit `71ef468`, with the candidate diff
confined to `scripts/resolver.py`, `tests/test_resolver.py`, and
`tests/test_when_to_ask_candidate.py`.  The raw ledger landed before this
view.  **The shipping conjunction is false and the resolver candidate does
not ship.**

| Clause | Registered bar | Observed | |
|---|---|---|---|
| Q1 contradictions stop binding | 0 wrong negative BINDs; 14/16 reach; 14/16 routes | **1** wrong BIND; **12/16** reach; **8/16** routes | miss |
| Q2 clarification retains the reading | 15/20 halved+retained; classes 5/6, 5/6, 6/8; 20 distinct tuples; 10 sets of 4+; 4 of 8+ | **3/20**; **1/6, 1/6, 1/8**; **18** distinct; **0** sets of 4+; **0** of 8+ | miss |
| Q3 the blind arm is materially weaker | gap ≥ 0.10 and blind fails Q2's bar | gap **0.6801** (0.7127 vs 0.0326); blind 6/20 | **fired** |
| Q4 precision does not pay | pooled ≤ 0.030 | **0.03467** (104/3000) | miss |
| Q5 coverage does not pay | reach ≥ 0.833 and target recall ≥ 0.833 | reach **0.921** (35/38); recall **0.789** (30/38) | miss |
| Q6 exclusion changes the decision | ≥ 4/16 stripped single BINDs to vetoed ids | **1/16** | miss |

## The resolver did not ask

The registered denominator assumed 20 rows would ASK.  Four did.  Thirteen
BOUND and three PASSed, and the initial candidate sets on those 20 rows were
sized `[0,0,0,1×13,2,2,2,3]` — not one set reached four candidates, let alone
the eight the profile required.  Q2's entire apparatus therefore measured
narrowing on sets that were already singletons, which is why halving fired on
3 rows rather than 15.  This is not a scoring accident to be reweighted: the
prediction was that the shipped clarification loop would have ambiguity to
work on, and on fresh rows it did not.

## Q3 fired, and the reason it fired is the reason the others missed

Reciprocal candidate load pays `1/k` for finding the target in a small set.
The resolver averaged 0.7127 against the 25-id blind arm's 0.0326, an enormous
gap — but 25 of the 30 rows where it recalled the target returned that target
alone, and the mean `1/k` among recalled rows was 0.9028.  The arm is
measuring decisiveness, and decisiveness is exactly what v0.13 had too much
of.  On the eight rows where the target was absent the score is 0 and the
control says nothing at all.  Q3 is a true result about the blind baseline
being weak; it is not evidence that the candidate reads questions well, and
it should not be quoted as one.

## Q4 could not have fired

The mechanical arm classifies OEWN sentences with the plain resolver, because
those sentences contain no `without TERM` structure.  The candidate changes
`resolve` only by adding a mask parameter that this path never sets, so Q4
re-measured the untouched v0.13 baseline on fresh samples and duly reproduced
it: 0.024, 0.038, 0.042 across seeds 20260825–20260827, pooled 0.03467, mean
0.03467, population σ 0.0077 — against v0.13's 0.034.  **Registering a clause
the intervention cannot influence is a preregistration defect, not a candidate
failure.**  What the arm did earn is worth keeping: three fresh, mutually
disjoint 1,000-sentence samples independently replicate the 0.034 figure that
sank v0.13, so that number was not a bad draw.

## What the exclusion actually did

The mechanism works where it was designed to work.  The spent v0.13 sentence
now binds `economics.finance.simple_interest` instead of
`economics.finance.continuous_compounding`, and it does so by promoting a
lower-scored survivor after the veto — a resolve-then-filter implementation
would have returned nothing there.  That is kept as a regression test and is
still not a score.

On the fresh negative stratum it barely mattered.  Stripping the negative
span changed the bound on **one** of 16 rows (N-B03, ASK → BIND on a vetoed
id), so Q6 reached 1/16 against a threshold of 4.  Seven of the eight
`negative_bind` rows already bound correctly without needing the exclusion,
which means the fresh negative rows were easier than the sentence that
motivated them.  The one wrong negative BIND, N-A04, bound
`difftop.vectorfields.poincare_hopf_index_theorem` where
`difftop.invariants.euler_characteristic_diffeomorphism_invariance` was
intended — a wrong reading the exclusion did not veto, because the excluded
term appears nowhere in the winner's committed text.

## Standing

Per the design's stop conditions the implementation parks.  No row is
replaced, no threshold is retuned, no fifth holdout is authored in this
cycle, and `without` does not become a stopword.  The exclusion seam stays in
the resolver as shipped behaviour that no gate credits.

---

# v0.14 — the release gate, measured (item 3)

Every test module run singly at frozen tip `55b4097`, receipts retained in
`reports/test_gate_v014/`.  **68 modules, 1,341 tests, 0 failures, 0 errors,
5 skipped.**  Serial wall clock **21,688 s = 6.02 h**, not the ~10 h the
cycle had been assuming.

## The suite is two modules

| module | seconds | share | fixture+overhead |
|---|---|---|---|
| `test_write_stage` | 12,522.5 | 57.7% | 8.5 s (0%) |
| `test_corpus_analogy_split` | 8,045.0 | 37.1% | 3,434.2 s (43%) |
| remaining 66 modules | 1,120.5 | 5.2% | — |

## Every item-3 investigation was aimed at the wrong place

The roadmap registered three things to investigate.  The measurement
contradicts two of them and omits the actual cost entirely.

- **"the 5,620-second blind-control sweep."**  The blind control is one test,
  `ControlTests.test_no_blind_control_can_see_the...`, and it costs
  **4,317.0 s** — 19.9% of the suite, not its dominant term.
- **"roughly 4,700 seconds of `test_corpus_analogy_split` fixture/runner
  gap."**  The gap is real and is **3,434.2 s**, 43% of that module.
- **`test_write_stage` is not named anywhere in the roadmap**, and it is
  **12,522.5 s** — more than everything else in the suite combined.  Its
  fixture overhead is 8.5 s, so this is not a setup artifact: it is 103 real
  tests, four of which cost 3,088 s between them.

That is the fourth consecutive time an explanation of this suite's cost has
been folklore, which is the pattern `scripts/time_tests.py` was written to
end.  It ended it by measuring.

## Sharding is not the lever

The registered assignment rule — descending module seconds, module-name tie;
assign to the lightest shard, shard-number tie — produces an identical
predicted parallel wall clock at 2, 5 and 8 shards: **12,523 s (3.48 h)**.
One module is a hard floor, so the maximum achievable speedup is **1.73x**
and every shard beyond the second is idle capacity.  The v0.13 gate's five
shards were already three more than the work can use.

## The sampled-control question answers itself

The third investigation asked whether a sampled capability-blind control
could preserve the non-vacuity guarantee, under a registered constraint that
no optimization may weaken such a control without a registered replacement.

It does not need to be answered on principle, because the measurement
disposes of it on arithmetic.  Sampling the blind control could remove at
most 4,317 s of *serial* time and **exactly zero** parallel wall clock, since
`test_write_stage` remains the floor at 12,522.5 s either way.  The
optimization buys nothing it would have to be justified against.  The control
stays whole, and not as a concession.

The one lever that would move this gate is `test_write_stage`, which nobody
had proposed touching because nobody had measured it.

---

# v0.15 - the coincidence veto, adjudicated once (partially)

Registered order followed: inventory committed, then tags and table and
prediction committed, then the blind control, then the flags.  Nothing was
authored after a flag was visible.

**Denominator.** 26 qualifying groups, **77 aligned slots**, 213 symbol
occurrences of which 35 are `kind-unknown`.  The slot count was unknown when
the design was written; it is what the committed inventory established.

**Blind control, run first.** Case-folded symbol-name difference agrees with
the kind-based labelling on **0.3958** of the 48 fully-tagged slots, against a
0.80 threshold.  The direction survives its cheapest challenger: names alone
do not reproduce the kinds, because almost every cross-field slot holds
differently-named symbols whether or not they denote the same quantity.

**Result.** **22 of 77 slots conflicting**, inside the registered band of
20-60, across **8 of the 26 groups**.  All four named directional calls held:

| call | predicted | observed |
|---|---|---|
| P1 `scaled_linear` | conflicting | conflicting |
| P2 logic + set-theory groups | not conflicting | unjudged |
| P3 `sum_of_squares` | not conflicting | unjudged |
| P4 rank against velocity | conflicting | conflicting |

P1 is the prediction the v0.14 release blog put in print, and its certificate
is readable: `CIRCUMFERENCE(length)` against `POTENTIAL(electric_potential)`
and against `FORCE(force)`.  Circle circumference, Ohm's law and Newton's
second law share the skeleton and cannot share a quantity.

P2 is the one that mattered most for the table's honesty.  Boolean algebra and
set algebra were declared compatible on their merits before anything ran, and
the four logic/set-theory groups came back unjudged.  A table that flagged
them would have been a liar in the direction the object is supposed to be
trustworthy.

## The corruption control is invalid, and it is my defect

The third registered control does not work, and it fails for a reason
introduced at authoring time rather than found in the data.

The incompatibility table was scoped to the 44 kind pairs that co-occur **under
the authored tags**, on the argument that a row which cannot fire is
unreviewable noise.  That argument is fine for reviewability and fatal for the
control.  Permuting the tags raises pairs the table has no row for: **107 of
133 permuted pairs are unrepresented, against 24 of 75 authored ones**.  The
permuted baseline is crippled by construction and under-fires for reasons that
have nothing to do with whether the authored tags carry information.

Authored 22 against a permuted mean of 19.3.  That comparison is not evidence
either way and is recorded as **neither passing nor voiding**.

So the run is **partially adjudicated**: two registered controls passed and one
could not run.  The instrument does not get to claim its tags carry
information until the control is repeated against a table authored over the
full kind cross-product, and that repetition is exploratory rather than
preregistered, because the population is a census with no fresh half.

## Standing

The suspension on the published cross-field match count is **extended, not
lifted**.  Eight of twenty-six hand-authored cross-field groups contain an
aligned slot whose quantities cannot be the same, which is the doubt the
suspension was raised about rather than an answer to it.

Two reporting bugs were found immediately after the first run and fixed before
anything was committed: the named-call comparison tested `unjudged` against the
string `not conflicting`, and the group lookup split a slash-joined archetype
name that the ledger stores as two entries.  Neither touched a flag; both had
made held calls look like misses.  The lookup now raises rather than returning
a default, so a name that matches nothing cannot read as a miss again.

## Where the veto's discrimination actually lives

The corruption control could not run, so the question it was meant to answer -
do these labels carry information - was asked a different way, by sensitivity
analysis on the committed artifacts.  This changes nothing already published
and re-scores nothing; it varies the table and reports what moves.

| table | conflicting slots |
|---|---|
| nothing incompatible | 0 of 77 |
| the authored table (38 incompatible, 6 exempt) | **22 of 77** |
| every co-occurring pair incompatible | 42 of 77 |

So the six exemptions suppress twenty slots and the thirty-eight
incompatibility rows do the rest.  Removing each exemption in turn:

| exemption removed | conflicting slots |
|---|---|
| `dimensionless_ratio` \| `elasticity` | 22 |
| `length` \| `point` | 22 |
| `dimensionless_ratio` \| `information` | 23 |
| `dimensionless_ratio` \| `linear_map` | 23 |
| `dimensionless_ratio` \| `probability` | 24 |
| **`proposition` \| `set`** | **38** |

One judgement carries the instrument.  Declaring Boolean algebra and set
algebra to be the same thing suppresses sixteen slots; every other exemption
moves the count by at most two.  The remaining thirty-eight rows are
close to a single rule: a cross-field slot conflicts unless specifically
excused.

This is a better answer than a passing corruption control would have been, and
a less flattering one.  The veto is not a thirty-eight-row table doing subtle
dimensional reasoning.  It is one very good domain judgement - Boolean and set
algebra are isomorphic, which is textbook - sitting on top of the observation
that quantities from different fields are usually different quantities.  Its
trustworthiness rests almost entirely on that one exemption being right, which
is a much smaller and much more checkable surface than the artifact's size
suggests.

It also explains the corruption control's behaviour rather than excusing it:
permuting tags destroys the one clustering that matters, so 22 against a
permuted 19.3 is noise around a mechanism dominated by a single row.

A properly powered corruption control still does not exist.  The obvious fresh
population - the nine hand-authored twin groups matching statements within one
field - was measured and rejected as too weak before being run: only 29% of its
fifty-one symbol occurrences are covered by names the committed tags already
carry, so most of its twenty-four slots would be undecidable.  Establishing the
information claim needs a table authored over the full kind cross-product
before any tag, re-run on a population that has not been examined.  Neither
exists today, and the claim stays unestablished rather than being propped up by
a control chosen after the fact.


# v0.15 - the bounded closure: built, independently checked, all six gates fired

Preregistration (`9fa4cba`) landed schemas, two frozen world registrations,
the generic checker, the twelve-class corruption battery, and four tests red
by construction; the builder landed after, wrote its own traversal and cell
derivation, and imported from the checker only the definitional pieces
(action enumeration and canonical bytes), so closure-vs-checker equality is
evidence, not a tautology. The independently written BFS matched the checker
byte-for-byte on the first run.

**Adjudication (registered order, decided numbers):**

| clause | verdict | deciding number |
|---|---|---|
| B1 two real worlds register | FIRED | 2 committed worlds, 0 invented |
| B2 blind closure finishes | FIRED | 75 states <= 512; 20 actions/state <= 32; 0.014 s <= 30 s; 450,040 B <= 8 MiB |
| B3 checking is complete | FIRED | checker ok on both; 74/74 predecessor witnesses; cells recomputed identically |
| B4 corruption always caught | FIRED | 90/90 applicable mutations rejected with a named first disagreement; 20 honestly inapplicable (all visual: no accepted edge or cell to corrupt); 0 false rejections; class-12 reorder normalizes to identical bytes 10/10 |
| B5 abstraction is shared | FIRED | 0 world-name literals in builder/checker/corruptor; byte-identical rebuilds |
| B6 composition is exercised | FIRED | 12 convergence cells vs the required 4 (story 12, visual 0) |

**The two closures** (`reports/closures/`): story.golden_chicken at horizon 5
- 75 states (55 interior / 20 boundary), 110 accepted edges, 990 refusal
edges, 12 cells, digest `27060b10...`; visual.rt0000 at horizon 1 - 1 state,
6 refusal edges, 0 cells, digest `40295aa1...`. The visual shape is the
honest one: its committed action vocabulary exists to be refused, and the
closure records that as six named refusal edges rather than dressing the
world up with invented moves.

**What the cells actually are.** Decoding the twelve cells finds two
mechanisms, both properties of committed code that no test had stated:
(1) planting an already-planted element is ACCEPTED idempotently - routes of
length n and n+1 converge on the same state bytes; (2) `plant` and
`discharge` never read their `desire` argument - routes differing only in
desire converge, including a plant whose desire contradicts the introduce it
follows. Per the design's own non-claim, equal end bytes demonstrate only
that the registered operations commute on these cases; they say nothing
about narrative meaning. But "the story world's obligation transitions are
desire-blind and re-plant-idempotent" is now a demonstrated fact about
`oracle_controller_demo.py` + `frames.py`, surfaced by exhaustive bounded
enumeration rather than by anyone thinking to test it - which is the
instrument doing the thing it was built to do.

**Limits, stated with the result:** the horizon-5 story closure and the
horizon-1 visual closure are small worlds; nothing here claims the method
scales past the frozen ceilings, and a query against these closures answers
reachability within the bound, never possibility in general. The corruption
battery's 20 inapplicable slots are a property of the visual world's shape
(no accepted edges, no cells), reported rather than padded. Human-selected
demonstration queries, when run, are demonstrations - the closures predate
them, and no query is scored.


# v0.16 - the retraction closure: built, independently rechecked, voided by its own gate

Preregistration (`20581cc`) landed the schemas, the hundred derived
control seeds, and the two hand-audited ground truths before any
assembler existed; the recheck was written by an agent forbidden to open
the builder (`a474101`, committed before the builder); the citation
scan's six generic rules were frozen (`0cc0c68`) with a dated
registration (`35dca02`) disclosing that the rule author had seen the
audit and two development closures. Then the seven registered steps ran
once, nothing edited, nothing rerun.

**Adjudication (registered order, decided numbers):**

| clause | verdict | deciding number |
|---|---|---|
| R1 writers emit their own edges | FIRED as written, and the wording is vacuous | 353/353 edges into ledger nodes non-inferred - but writer edges point OUT of ledgers, so the denominator holds only citation edges. Intended measure: 0.800 over all five ledgers (the declared snapshot's 27 edges are reconstructed), 1.000 over the regenerable four |
| R2 the drifts are explained, superset-exactly | **FAILED on both roots - capability VOID** | Root A: 11/11 covered, 54 > 33 cap. Root B: 14/16 covered (b12, b16 missed), 106 > 48 cap |
| R3 coverage floor | FAILED | 2/14 release-note sections anchor (0.143 vs 0.90); the release cites closures and veto ledgers the v1 registry does not carry |
| R4 independent recheck | FIRED | both certificates re-derived by the never-saw-the-builder checker, every field equal, 0.108 s of 600 |
| R5 byte reproducibility | FIRED | two builds, one graph, sha256_lf f7af36cb... |
| R6 historical replays reported, not scored | REPORTED | both close as the root alone (size 1): interpretation-shaped retractions have no data lineage, the floor where the design put it |
| blind control | did not void | **0/100** shuffles satisfy R2 on both roots; coverage collapses under every shuffle while degree preservation pins the sizes |

**What the void actually says.** The graph is not noise: no
degree-and-kind-preserving shuffle of its edges reproduces the audited
coverage, so the real edges carry consequence-relevant information. The
void is a *precision* failure with a clean mechanism, named per rule by
the committed edge tags: Root A's flood arrives through R-d's backticked
field vocabulary (34 of its 53 depth-1 claims, mostly the word `nodes`,
which is both a compression-ledger field and half the repository's
filenames); Root B's arrives through R-e's bare stem "decomposition" (34
claims) and R-c's writer mentions (30). And the two claims no rule
reaches (b12, b16) cite only derived decimals - 0.490 and its pin
history - with no lexical trace of their artifact. A scan strict enough
to stay inside 3x cannot reach them; a scan loose enough to reach them
cannot stay inside 3x. On this document corpus, with these rules,
lexical citation cannot price a retraction, and the gate was built to
say so.

**Self-reference, recorded.** The adjudication registration names both
root ledgers, so the registration section itself joined both radii
(53 -> 54, 105 -> 106). A claim about the graph is a claim in the graph.

**What survives the void, unscored:** writer-emitted provenance blocks
in all four ledger writers (byte-stable, additive); the regeneration
check that answers all four ledgers (three clean, one declared
divergence with its citation - the first machine answer the reports
directory has ever given); the graph, radius, recheck, adjudicator, and
control as green instruments; and the ground truths, which remain the
committed test any future citation mechanism must meet. Per section 7
the direction stops here for this cycle; what a successor owes is not a
better regex but a citation discipline at authoring time - claims that
name their artifacts - which is the design's own forward sentence, now
with a measured floor under it.


# v0.16 - the veto''s information claim, established blind

The v0.15 corruption control failed for an authoring-time reason: the
table only covered pairs that co-occur under the authored tags, so
permutation starved it. Item 2''s registered fix: author the table over
the FULL 26-kind cross-product (325 pairs), blind - an isolated context
shown only the kind menu and the judging rules (brief sha256_lf
e74f86ea..., session 1137c959, receipt in
experiments/veto_full_cross_table.json) - then rerun the same
permutation scheme with the same committed seed and count, criterion
fixed before the table existed (experiments/veto_full_cross_protocol.md):
established only if real sits strictly below the permuted 5th percentile.

**Result: real 21; permuted min 45, 5th percentile 45, mean 52.7, max
61.** Real is below half the permuted minimum. The authored kind tags
carry consequence-relevant information, and the claim is labelled
exploratory because the population is a census with no fresh half.

**Convergence, twice.** The blind table agrees with the v0.15 scoped
table on 43 of 44 shared pairs. The one disagreement - count|point,
"a rank is a position in an ordered space" against "a cardinality is
not a measured magnitude" - is a defensible reading, listed not
reconciled, and moves the real count 22 -> 21. And the blind author
independently exempted proposition|set, the single row the v0.15
sensitivity analysis found carrying the whole instrument, having never
seen that analysis. The veto''s load-bearing judgement has now been made
twice by authors who could not see each other.

**Standing.** The suspension''s own clause was "until the coincidence
veto reads out, or two release cycles pass". It has read out: the
name-difference control passed at v0.15, the permutation control now
passes against a table it cannot starve, and the flags sit where the
registered band said. The suspension LIFTS at v0.16, with two permanent
riders wherever the cross-field match count is quoted: the veto''s
conflicting readout rides with it (8 of 26 hand-authored groups contain
a slot whose quantities cannot be the same), and the one-row finding
rides with it (the instrument''s discrimination rests on the
proposition|set exemption - now made independently, twice).

**Population search, closed in writing.** The corpus has not changed
since the v0.15 measurement; the only candidate population (the nine
in-field twin groups) stays rejected at 29% name coverage. No fresh
half exists, which is why "exploratory" is part of this result''s name
and not a disclaimer to be shed later.


# v0.17 - grounded throughput: the registered run, and the trials that made it honest

Design: `docs/DESIGN-grounded-throughput.md` (maintainer redirect,
2026-08-21). Preregistration order, every artifact committed before the
one that depends on it: the design; `docs/SPEC-chat-completions-skin.md`
(`0e08bcb`); the W1/W2 wiring (`4b2e2de`); the sealed task book
`experiments/throughput_tasks.json` (`ca2262c`, LF-pinned `55b0473`); the
baseline manifest `experiments/throughput_baseline.json` (`9b635b6` -
K = 5 freezes here); then `scripts/serve_chat.py` (`8059b4a`) and
`scripts/measure_throughput.py` (`38c9778`); then one registered run
(`c345dc9`).

The book: 119 tasks over seven kinds, 94 answerable (70 with both
conditional kinds dropped; T3's floor is 50), halves by the frozen hash
rule, half B sealed - 61 tasks, 49 of them answerable. The seal witness is
the canonical-LF digest of eleven rendering modules, revalidated by the run
before anything is timed.

## The registered run (half B, first and only execution)

| arm | correct with receipt | median perceived tok/s (T4 statistic) | aggregate tok/s (design section-3 wording) | median TTFT-useful | useful tokens |
|---|---|---|---|---|---|
| kernel | **49/49 = 1.000** (1.000 in every kind) | **3,451.25** | 1,936.41 | **25.3 ms** | 5,784 |
| B-grounded (gated contender) | 4/49 = 0.082 | **0.0** | 8.79 | 45.1 ms | 188 |
| B-ungrounded (reported, never gated) | 1/49 = 0.020 | 0.0 | 0.112 | 53.0 ms | 20 |
| C1 dump server | 0/49 | 0.0 | 0.0 | none | 0 |
| C2 shuffled kernel | 0/49 | 0.0 | 0.0 | none | 0 |

Kernel refusals 6/6 refused; marked WAITING turns 6/6 surfaced. T5's floors
were 0.90 overall and 0.80 within every kind; the run cleared both at
1.000, so the speed numbers were legitimately readable at all.

**T4 adjudicates.** K = 5 froze at `9b635b6`, before the stopwatch existed.
Measured: **220x** at the aggregate (1,936.41 / 8.79) and **unbounded** at
the median, because the contender's median is zero. The TTFT leg holds too
- 25.3 ms against 45.1 ms. C3 did not fire: B-grounded neither met nor beat
the kernel at equal correctness, and it was not close on either axis.

**The controls, against their own voiding sentences.** C1 - protocol-valid,
maximum-rate, query-blind - must score under 1% of the kernel or the metric
is crediting bandwidth: **0.0**, against a 34.5 tok/s threshold on the
median. C2 - the kernel's own answers permuted across tasks by a Sattolo
cycle seeded from the book digest (`derangement_seed`
7953564568193198364, no fixed points by construction) - must score under 1%
or the scoring fails to separate right from wrong: **0.0**. C2 derived
**offline** from `experiments/throughput_result.json` (`--control-shuffle
--from`), so the sealed half was never executed twice. One reading worth
keeping: C2's clarification gate still reads 1.000, because permuting
*answers* does not permute *statuses* - the shuffled kernel still asks when
it should ask, and still scores zero, which is the scoring separating
content from shape.

## Trial-to-registered progression, and what each stage caught

Half A was the debugging half by construction; the stopwatch refuses
`--half B` without `--registered`. Every number below comes from a
committed file except the first, which is recorded in `025bd73`'s message
because the pre-fix trial file was superseded before the run.

| stage | kernel | B-grounded | what the stage caught |
|---|---|---|---|
| first half-A trial (pre-fix) | **83 tok/s** | - | the boot tax: ~460 ms of `CoreSession.boot` per request in the live profile (389 ms in the commit's controlled measurement; the gap is serving load), 405 ms of it `UnifiedKnowledgeStore.load` re-parsing every committed corpus, uncached |
| content-recording fix (`b906089`) | - | blank `content` on every record while five tasks scored correct | the response text lived only in `turns[]`; the number and the text behind it must tell one story |
| quote instruction amended (`441ec91`) | - | **5/45**, median 0.0, aggregate 8.79 | the contender paraphrased what the checks match exactly; a floored contender makes T4 vacuous and disarms C3 |
| post-memoization half-A trial (`025bd73`) | **45/45, median 2,207.78**, aggregate 725.41, TTFT 24.6 ms | - | boot 389 ms -> 7.5 ms; a definition task end-to-end over HTTP 674.8 ms -> 7.5 ms median, bodies byte-identical |
| **registered half B** (`c345dc9`) | **49/49, median 3,451.25**, aggregate 1,936.41, TTFT 25.3 ms | **4/49**, median 0.0, aggregate 8.79, TTFT 45.1 ms | - |

Two readings this table should not be allowed to blur.

**The quote instruction bought nothing.** The committed half-A B-grounded
trial carries `baseline_digest` `3be33a20...`, which is the *amended*
manifest's canonical-LF digest (the pre-amendment file hashes
`64a0d7c2...`), and it still read 5/45 - the same score the amendment's own
rationale reports for the unamended prompt. The amendment was made on the
fairness argument, before the run, and the record shows it did not move the
score. That is the honest reading, and it strengthens rather than weakens
the arm's standing: the contender was not floored by its instructions.

**The number the release quotes is the registered one.** 83 tok/s measured
a cold JSON parse, not a serving mechanism. It is kept here as the finding
it produced, not as the before-number of a speedup claim.

B-ungrounded's trial-to-registered movement (4/45 -> 1/49; aggregate 2.675
-> 0.112) is noise around a floor and is not interpreted. The arm is
reported, never gated, and its one job is to show the grounding gap in
numbers - which it does: 0.112 tok/s against the grounded arm's 8.79 and
the kernel's 1,936.41.

## Metric reconciliation: two readings, both computed, both labelled

The design's section-3 sentence defines perceived throughput as useful
tokens over client wall-clock with a refusal time charge; T4's gate
sentence takes the **median of the per-task ratio** over the half's
answerable tasks. Those are different statistics, and the stopwatch was
built to record both rather than to choose after the numbers landed
(`metric_reconciliation`, in every result file, with both design sentences
quoted verbatim inside it).

- **Under the median the refusal time charge is inert.** A refused
  answerable task scores zero useful tokens, so its ratio is zero at any
  denominator; the charge moves a zero to a zero. Recorded per arm as
  `refusal_time_charge_inert: true`, with the charged-task list beside it
  so the claim is checkable rather than asserted.
- **Under the aggregate the charge bites.** B-grounded's five
  context-overflow tasks are charged up to that arm's slowest correct
  answer (0.909773 s each), adding 2.569769 s to an 18.810595 s uncharged
  clock for a charged 21.380364 s. The kernel's charge list is empty.
- The kernel's non-answerable elapsed - 2.070535 s over 12 tasks - is
  excluded from the median and included in `elapsed_total_s`. Both are
  written down.

Every other interpretive choice a reader could have argued about after the
numbers landed is in the file too: sampling settings as
requested-versus-applied (the `/v1` layer drops `top_k`, verified live; the
model manifest applies it anyway), the B-side label-stripping correctness
rule with its per-task residuals (committed pre-run), and the observed
context length against per-task `materials_tokens`.

## The grounded arm's secondary median, corrected in writing

A secondary reading was pre-declared on 2026-08-22, before any timed run:
beside T4's registered median over all half-B answerable tasks, report the
same median restricted to tasks whose B-grounded materials fit the observed
context untruncated - so a reader can see how much of K rides on tasks the
baseline could not physically hold.

`experiments/throughput_result_bgrounded.json` records
`materials_fit_bound_tokens: 262144`, with the source string naming the
defect out loud: `/api/ps` reported no loaded model, because the model was
not loaded when the run started, so the probe fell back to `/api/show`,
which reports the model's *capability* rather than the served context. The
served context was **32,768**, and the same file proves it five times over
- five `closure_reachability` tasks return HTTP 400 carrying
`"request (130,475 ... 130,934 tokens) exceeds the available context size
(32768 tokens)"`. Recomputed over the recorded `materials_tokens` at the
true 32,768 bound, the restricted set is **44 tasks** and the restricted
median is **0.0** - identical to the unrestricted median. The verdict is
unchanged. The defect is filed in BACKLOG; the code was left exactly as it
ran, and the correction lives here rather than in a quiet re-run.

Related, and not a defect: the largest closure MATERIALS block measures
~130 k tokens. **Full closure grounding does not fit this hardware in any
configuration** - 32,768 was already the largest context whose KV cache
fits the 16 GiB GPU (131,072 and up would spill the model to CPU, a
strawman in the other direction), and the manifest disclosed that before
the run. Those five tasks are reported per task as errors, not silently
dropped.

## What this establishes, and what it does not

It establishes, for the registered paths only: a microkernel that copies
and computes its tokens delivers correct, receipt-bearing answers at a
median 3,451 useful tok/s where a grounded 4B instruct model holding the
same records - on the same throttled laptop, with the GPU assigned to the
*contender* - delivers 8.79 aggregate and a zero median. It does not
establish open-domain parity; the released numbers say so in the same
sentence. It says nothing about larger models, other runtimes, or
unregistered surfaces. And the contender's failure is not a failure of the
contender: it is the thesis appearing where the design predicted it would -
exact content does not survive being sampled through a decoder, even when
the decoder has the content in front of it.


# v0.18 - the graph speaks: the census, the registered run, and three controls

Design: `docs/DESIGN-sans-template-rendering.md` (maintainer-directed
Phase 6; trigger registered in DESIGN-grounded-throughput 10 before the run
that fired it). Preregistration order, every artifact committed before the
one that depends on it: the design; the lexicon, the numeral pair and the
frozen digests (`ccac853`, with `e28f8d6` correcting two node-keyed
operator rows); `realize_term.py` and its two-stage gate (`9879b06`); the
adversarial review closed at 1 High / 6 Medium / 9 Low, each dated
(`98ea2cf`); the one registered run (`ecb906d`); then the wiring
(`5357740`).

The claim is a split, so the implementation is judged on where it put the
structure. All precedence lives in the FORWARD grammar as a five-level
ladder read off the frozen recursive descent (relation 0, sum 1, product 2,
power 3, atom 4). Stage 1 (`delexicalize`) gets none of it - longest
matching phrase or numeral run, surface order, no bracket counter, no arity,
no precedence table; a test hands it an unbalanced grouping word and pins
that it emits `(` anyway, because noticing is stage 2's job. Stage 2 is
`tokenize -> Parser -> canonicalize -> skeleton`, imported and never
reimplemented, and a test greps the module to prove it defines no parser of
its own.

## R0: the census, and the denominator it publishes

R0 is a construction prerequisite, discharged and published BEFORE R1 is
read, because a floor frozen without a denominator is a wish.

| | count | rate |
|---|---:|---:|
| corpus nodes | 12,777 | |
| parseable under the byte-frozen parser | **2,172** | **0.169993** |
| `lean_workbook` nodes / parseable | 12,514 / 2,040 | 0.163017 |

Failure classes over the 10,605 that do not parse, named rather than
summarized: **10,432** unexpected character (Lean and Unicode syntax
outside the template grammar), **111** trailing tokens, **53**
expected-delimiter, **6** unexpected `|`, **2** unexpected `[`, **1**
unexpected `>`.

The stop condition did NOT fire: the rule was "stop if NO corpus has >= 50
parseable terms", and `lean_workbook` clears it at 2,040. That is also the
only corpus the per-corpus floor applies to; the other 26 are reported
individually and never averaged, per R1's own thin-denominator clause.

The census artifact (`experiments/realization_census.json`) and the
registered run agree exactly - 2,172 parseable, 2,170 exact, 0 failed, 2
refused - which is expected and is the point: the census is the
prerequisite table, regenerable, and the registered run is the sealed
reading of the same measurement under revalidated digests.

## The registered run

| gate | verdict | deciding number |
|---|---|---|
| R1 round-trip floor 0.90 of the parseable denominator | **FIRES** | 2,170 / 2,172 = **0.999079**; `lean_workbook` alone at 0.99902, also FIRES |
| R2 no invented surface | **CLEAN** | 0 of 2,170 served surfaces carry a word outside the lexicon and the registered numeral pair |
| R5 determinism | pinned | sha256 over all 2,170 served surfaces = `d3b6ee9bc278644a...`, first 25 by statement id pinned verbatim |
| C-R1 scrambled realizer (one-sided) | **INFORMATIVE** | true 0.999079 vs scrambled **0.0**; contrast unbounded vs a >= 20x bar; the >= 1% voiding bar nowhere near |
| C-R2 near-miss | **INFORMATIVE** | 3,722 mutations, 3,720 re-parsed to a DIFFERENT skeleton (0.999463 vs a 0.50 floor), **0** round-tripped to source |
| C-R3 tautology probe | **HOLDS** | all five pinned artifacts byte-identical to the preregistration commit's record |

**LOST = 0, balanced exactly.** 2,170 served + 0 round-trip failures + 2
refusals = 2,172, printed in the artifact as an arithmetic check rather
than a claim. Both refusals are listed by statement id with full detail:
`leanworkbook.ground.lean_workbook_37421` (76-digit literal) and
`leanworkbook.ground.lean_workbook_plus_68304` (48-digit), both
`unsupported_numeral` against the registered domain `|n| < 10^15`. They
refuse rather than round. A commit message earlier in the cycle called them
"two 76-digit literals"; the correction is recorded in the prereg (L2)
because a commit message cannot be corrected in place, and neither the
count nor the verdict moves.

**C-R1's failure modes, reported separately on purpose.** Of the 2,172
scrambled sentences: **1,348 parsed and meant something else**, **822** did
not parse, 2 refused before reading. Only the first population demonstrates
what the control is for. A scramble producing only the second would be
exercising the tokenizer. The derangement seed is derived from the
committed lexicon's own sha256_lf (`f2c22a5c...`), so it is a function of
the table under test rather than a number someone chose; 6 operator rows, 7
relation rows and 150 call-head rows moved.

**C-R2's construction check, and the 31 discards.** Every mutation is
applied to the canonical TREE and its skeleton compared to the source's
BEFORE any sentence exists; a mutation that does not change the skeleton is
discarded and never counted. 31 were discarded in this run. The reason is a
finding in its own right (below). The two mutations that failed to parse are
the same two oversized-numeral terms refusing in both arms.

## Two properties of the frozen grammar that the controls surfaced

**`a < b` and `b < a` are the same skeleton.** `<` is not symmetric, but
`render_skeleton` erases slot identity and renumbers by first occurrence,
so two bare slots either side of ANY relation are indistinguishable at the
level this gate compares. A near-miss set built on "non-symmetric relation
implies swapping changes the skeleton" would have been full of
non-mutations, every one would have "round-tripped to the source", and the
control would have voided the gate for behaving correctly.

**`canonicalize` does no head aliasing.** The design credited it with
aliasing and excluded alias-class swaps from C-R2 on that basis.
`alias_heads` is a separate pass that only the ALIASED match level runs,
and `MOD` vs `CONCAT` - one declared ordered_compose class - canonicalize
to DIFFERENT skeletons here. So alias-class swaps are legitimate
skeleton-changing near-misses and belong IN the mutation set. The control
got harder on the strength of a correction, which is the direction a
correction should move a control (`72cc7d6`).

## The corrected receipt numbering

Adversarial review's single High finding made a published receipt field
wrong. `parameters.slot_names` numbered slots by first occurrence in
`canonicalize()`'s tree - the order the SURFACE uses - while
`term_skeleton`'s `?N` come from `render_skeleton` walking
`shape_resort()`'s tree, and `shape_resort` re-orders arguments `shape_key`
cannot tell apart BEFORE the numbering happens.

Measured: the two disagree on **110 of the 2,170 served terms (5.0691%)**,
reproduced exactly. The compact corpus case is `p + q = (q + 1)^2`, where
the sentence says "variable zero" for `p` while the skeleton's `?0` is `q`.

The receipt now publishes BOTH maps - `surface_slot_names` and
`skeleton_slot_names`, with `slot_index_basis` naming which is which - that
corpus term is pinned in the curated set so the divergence is exercised,
and a test checks `skeleton_slot_names` against the actual `?N`
placeholders. **No sentence and no verdict moves**: `skeleton()` is
invariant under slot renaming, so the gate never depended on the numbering.
Only a reader matching the published names against `?N` would have been
misled, on one term in twenty. Recorded because "the gate was unaffected"
is the tempting sentence and it is not the whole sentence.

## Byte reproducibility and the separate runner

A second full run over `data/` reproduces the committed artifact's digest
exactly, and a third re-run during the v0.18 rotation reproduced it again:
canonical-LF sha256 `803fe00adb660a7b8536e61d6230904af9f496f997e959a3590dfa5e7c5ed3fe`,
identical to the committed file. No timestamp, no elapsed time, no absolute
path rides in the artifact, and a test asserts their absence over KEYS
rather than substrings. Wall clock is deliberately excluded for exactly
that reason - 37.2 s at the run commit, 55.5 s on the rotation re-run, same
bytes. 107 tests across the three realization modules green at the run
commit (44 + 37 + 26).

The runner is `scripts/measure_realization.py` rather than a `--registered`
mode on `realize_term.py`, and the reason is structural: `realize_term.py`
is digest-pinned as the inverter, so a registered mode would have moved the
very digest that certifies the number the mode produced. C-R2 needs to
realize mutated trees, so it reuses `realize_term`'s own `_Linearizer`,
`_slot_order` and `reparse` with local glue - same linearizer, same
two-stage gate, transcribed entry point.

One defect the refusal test caught by failing to SEE a refusal:
`revalidate_prereg(prereg_path=PREREG_PATH)` bound the module global at
definition time, so a caller pointing it at a different preregistration was
silently revalidated against the committed one and the run was written
anyway. The default is now read at call time, `--prereg` exists, and the
test asserts exit 3, the reason on stderr, and that no file was created.

## Indicative previews from the v0.19 grounding pass

Recorded here so the v0.19 gate can be read against numbers that already
existed, and labelled **INDICATIVE** because they were measured during a
design grounding pass, not under a preregistered run, and the design that
carries them (`docs/DESIGN-foreign-voice.md`) was **under adversarial
review at this rotation**. Each becomes a published B0 table under v0.19's
own gate, either confirming these or correcting them with a dated note.

| quantity | indicative value | share of 12,777 |
|---|---:|---:|
| mute nodes (do not parse) | 10,605 | 83.0% |
| of those, **transliterable** - parse after substituting `>=` for `≥` and `<=` for `≤` | **6,414** | **50.2%** |
| foreign residue (unreachable at any alphabet) | **4,191** | 32.8% |
| of the residue, oracle-eligible by outcome (pinned binary, rule R, autoImplicit false; an earlier blocklist-derived 1,456 retired by dated correction) | **2,319** | 18.1% |

The residue's shape, also indicative: 4,060 of the 4,191 are
`lean_workbook.ground.v1`; the remaining 131 spread across nine small
corpora, led by `logic.boolean_foundations.v1` (20, all of it) and
`temporal_logic.linear_time.v1` (15, all of it). The blocking constructs
named are quantifiers and typed binders (`forall a b c : R,`), logical
connectives, type ascriptions, and namespaced heads.

Elaborated-term serialization was prototyped under the pinned Lean binary
during the same pass, with **binder-name independence proven** on two
prototype pairs. That prototype becomes v0.19's B-P, discharged before its
B0 freezes.

**What the transliterable number does to this cycle's headline, stated
plainly.** 17.0% was never a claim that 83% of this corpus is structurally
beyond the grammar. Roughly half the gap is an encoding boundary that two
tokenizer rows close, and the honest reading of R1's 0.9991 is unchanged by
that - it is a rate over terms the parser can read, and the parser's reach
is a separate, now-measured question.

## What this establishes, and what it does not

It establishes that a realization grammar can linearize committed canonical
terms into English and that the sentences are recoverable: 2,170 of 2,172,
zero round-trip failures, zero invented words, with a shuffled-lexicon
contrast at zero and 3,722 near-misses none of which round-trips to its
source. It does not establish fluency - the sentences are correct and
re-parseable and their style is whatever the grammar produces. It does not
establish that slots speak their names; `canonicalize` erases slot identity
and the surface says "variable zero". It says nothing about the 83% the
parser cannot read, which is the next cycle's territory and, per the
numbers above, is two different problems rather than one.


# v0.19 - the foreign voice: every gate fired and the control voided it

Design: `docs/DESIGN-foreign-voice.md`, selected by the v0.19 outside
course (`reports/design-direction-v0.19.json`). Preregistration order,
every artifact committed before the one that depends on it: the design;
rule R (4 type substitutions, autoImplicit false, a deterministic
preamble); the loanword lexicon (bijective, L1/L2 imported from v0.18,
with a dated digraph correction); B0d's 100 SEALED hand-renderings; the
B-P serializer (`prover/lean/normalizer/Serialize.lean`, binder-name
independent, hermetic); the frozen register with its `blocked_set_digest`
(commit `297d1ea`, before `scripts/foreign_voice.py` existed, ordering
checked against git history); then `foreign_voice.py` and
`measure_foreign_voice.py`; then the one registered run.

Toolchain `leanprover/lean4:v4.32.2`. 22 frozen digests revalidated before
anything was measured (B7).

## Every gate

| gate | verdict | deciding number |
|---|---|---|
| B-P serializer, binder-name independent, hermetic | FIRES | prototype's two retained pairs reproduce at 475 and 2,627 characters; two-run byte-identical |
| B0a residue >= 2,000 | FIRES | 4,191 residue of 10,605 mute; 6,414 transliterable EXCLUDED |
| B0b+c accepted >= 1,000 | FIRES | 2,319 accepted, 1,872 rejected |
| B0d sealed hand-renderings >= 90 | FIRES | **100 of 100 reproduced byte-identically, 0 divergences** |
| B1 identity >= 0.995 of covered | FIRES | **2,313 of 2,313 = 1.0**; 2,176 distinct elaborated terms; 99.87% lean_workbook |
| B2 three outcomes, no silent drop | FIRES | outcomes {identity: 2313}; no refusal fired |
| B3 the arithmetic closes at 10,605 | FIRES | 6,414 + 2,313 + 0 + 1,706 + 172 = 10,605 |
| B4 register frozen first | FIRES | `297d1ea`, checked out of git history |
| B5 / B6 / B7 | FIRE | two runs byte-identical; no learned component; 22 digests revalidated |

**B0d deserves its own sentence.** 100 statements were hand-rendered and
SEALED before the implementation existed, as a prediction about what the
implementation would produce. The implementation reproduced all 100
**byte-identically**, with zero divergences, zero elaboration failures and
zero sealed-as-rendered statements that the renderer then refused. The
artifact records the rule that made that meaningful: *divergences are
reported, never repaired* - a divergence would have been a finding about
the grammar or the authoring, and editing the seal to agree would delete
it. None arose.

## The controls, and the one that voided

| control | verdict | reading |
|---|---|---|
| C-V1 skeleton renderer, one-sided | HOLDS | true 1.0 vs skeleton 0.0 over the same 2,313; misses split **983 elaborated-to-a-different-digest / 1,330 failed-to-elaborate** |
| C-V2 transliteration null, positive control | HOLDS | 1.0 identity over covered; over the transliterable 6,414: elaboration 0.9938, identity 1.0 |
| C-V3 determinacy sheet | **ABSENT** | the claim it alone licenses is NOT MADE |
| C-V4 near-miss null | **VOID** | `drop_group` 0.80 against 0.90 |
| **overall** | **VOID** | a voided control outranks a cleared floor |

**C-V1's split matters and is reported separately for the v0.18 reason.**
A skeleton rate of zero is only informative if the misses are
*elaborated-to-a-different-digest* - 983 here. The 1,330 that failed to
elaborate are cases where the pinned binary never got to compare two terms
at all, and a control producing only those would be exercising the
harness. One-sidedness is inherited deliberately from v0.18's C-R1 lesson:
a two-sided scramble is a consistent renaming and round-trips
near-perfectly.

**C-V2 is the positive control and carries the discipline sentence.** The
transliterable 6,414 are reported there and NOWHERE in B1. The artifact
states the rule flatly: if they are ever counted inside a foreign-voice
rate, that rate is wrong.

**C-V4, per class:**

| class | sample | differed | rate | floor | in voiding pool |
|---|---:|---:|---:|---:|---|
| swap_binder | 50 | 50 | **1.00** | 0.90 | yes |
| shift_group | 49 | 49 | **1.00** | 0.90 | yes |
| drop_ascription | 50 | 45 | 0.90 | 0.90 | yes |
| **drop_group** | 50 | 40 | **0.80** | 0.90 | **yes - VOIDS** |
| drop_binder | 50 | 9 | 0.18 | none | **no, blind by construction** |

The mechanism of the void: **deleting a semantically redundant bracket
changes the sentence and not the term**. That is §3.2's sentence -
*identity holds up to what elaboration erases and what the preamble rule
regenerates* - arriving with a number on it. The sentence was written as
the claim's shape rather than as a caveat precisely so a control would be
built to measure it. It was, and the measurement came back outside a floor
frozen before the instrument existed.

**drop_binder's 0.18 is not a miss.** It is excluded from the voiding pool
by preregistration because the preamble rule regenerates exactly what the
mutation deletes, so B1 structurally cannot see it. 0.18 IS the measured
width of B1's blind spot. A fresh-eyes review had independently measured 1
of 24 by hand; the registered run re-measured with this repository's own
renderer rather than freezing a threshold at the number that review
produced - the artifact records that reasoning in place, and a divergence
from 1-of-24 was declared reportable rather than reconcilable in advance.

**The §7 binder-swap prediction is REFUTED, exactly as pre-registered**, at
1.00 (50/50) - in the direction that makes the control stronger.

**Consequence, taken rather than argued with.** The foreign `in words`
line is NOT wired. B1's 1.0 is not quotable without the VOID beside it,
anywhere. The register is the headline artifact, which is what the design
said before the run.

## Two defects of this run's own instruments, both published

**C-V4 is mis-specified.** It inherited C-R2's mutation idea without
C-R2's load-bearing clause - every mutation verified to change the TERM
before it is rendered, non-mutations discarded, discards counted (v0.18
discarded 31). So an unknown share of C-V4's `did_not_differ` cases may be
non-mutations, and drop_group's 0.80 is scored against an uncleaned
denominator. The re-specified control is future work with its own
preregistration (ROADMAP-v0.20 §2), NOT a re-score: this run stands as it
read.

**An artifact field is wrong and is not fixed.** `shift_group`'s
`of_which_digest_moved` reads 33 where the true value is 0 - the field
double-counts the 33 cases where the inverse refused. The class's 1.00 is
correct and the verdict is unaffected: 49 differed = 33 inverse-refused +
16 elaboration errors. Fixing it means re-running a registered artifact,
which costs more than it buys. Reported here and in BACKLOG.

**One reconciliation a reader will want.** B0b+c accepts 2,319 by
oracle-eligibility while B1 covers 2,313, and the register blocks 1,878
against B0b+c's 1,872 rejections. The six-statement difference is
eligibility versus coverage: a statement the oracle can reach may still
carry a head with no lexicon row. The B3 arithmetic closes on the coverage
partition (2,313 + 1,706 + 172 = 4,191 residue), which is the partition
every published number uses.

## The register - the headline artifact

Frozen with `blocked_set_digest` e51e5675... before anything was rendered.
Seven entries, 1,878 statements, and the two buckets are reported
separately and NEVER summed.

| construct | bucket | statements |
|---|---|---:|
| namespaced and bare Mathlib heads, and the sqrt notation | mathlib_head | **1,706** |
| propositional, modal, provability and set-theoretic statements | no_row | 75 |
| house ASCII notation that is not Lean in any alphabet | no_row | 53 |
| variable exponents and other terms core Lean cannot instantiate | no_row | 38 |
| the coercion arrow | no_row | 4 |
| a decimal literal the numeral pair cannot spell | no_row | 1 |
| an integer literal outside the registered numeral domain | no_row | 1 |
| total | | **1,878** |

The 1,706 is a **budget consequence a maintainer can lift**; the 172 is a
**design consequence this cycle owns**. Merging them into one
"unsupported" figure would hide which is which, which is the shrug the
register exists to prevent.


# v0.19 - transliteration: two glyphs, and the native voice goes 17.0% -> 67.2%

Lane: ROADMAP-v0.19 item 3a, a registered probe rather than a headline -
deliberately, because the preview made it look easy.

| | statements | rate |
|---|---:|---:|
| parseable under the retired parser (65fead2f...) | 2,172 | 0.1700 |
| **parseable under the successor parser (f5b2abba...)** | **8,586** | **0.6720** |
| newly reached | **6,414** | floor 6,000, MET |
| newly reached that round-trip EXACTLY | **6,414 / 6,414** | **1.0000** (0 refused, 0 failed) |

**The denominator's composition, stated before the rate is read**, per
v0.18 R1's imported rule: the newly-reached set is **1 corpus and 2
distinct call heads** over 6,414 statements, with 4,733 occurrences of the
greater-or-equal glyph and 1,681 of less-or-equal. Numeric inequalities,
overwhelmingly, with almost no function application. LARGE AND
STRUCTURALLY NARROW.

**What the 1.0000 does and does not establish.** ESTABLISHES: the
statements two glyphs reach are the same grammar in every respect the
realizer touches, not only at the tokenizer. DOES NOT ESTABLISH that the
realization lexicon covers the corpus - it establishes that the newly
reached statements carry the heads it already had, which is a fact about
which statements two glyphs unlock.

**No floor was pre-committed on the round-trip rate, and the reason is
recorded before the reading.** A high rate is the dull finding; a LOW rate
would have been the interesting one - parsing bought reach without buying
voice - and a pre-committed floor is exactly what would have pressured
this lane not to publish it. v0.18's R1 floor was explicitly NOT imported:
it was frozen against a different denominator under a different prereg,
and borrowing it would let one cycle's adjudicated number grade another
cycle's work.

**Additivity, proven not asserted - and the witness carries TWO scopes
that a reader must not merge.** It loaded the RETIRED parser out of git in
its own interpreter and ran `answer._in_words` - the exact function
`render` uses to decide the line - before and after.

| scope | gained | unchanged | changed | lost |
|---|---:|---:|---:|---:|
| **corpus-wide, 12,777 statements** (`corpus_wide_reading`) | **6,414** | **2,170** served + 4,193 silent | **0** | **0** |
| the task book's 30 `corpus_definition` tasks (`claim`) | 0 | 30 | 0 | 0 |

The corpus-wide row is the additive-only claim. The task-book row is 0
gained because **the book's tasks carry neither glyph**, which is why the
successor book's expected records were untouched by the widening and why
that block's before/after digests are IDENTICAL. Quoting the `claim`
block's `gained: 0` as the lane's result would be a category error, and
the artifact's own `digests.note` invites exactly that error (see below).

The generator REFUSES to write the file if `changed` or `lost` is
non-zero, so additivity is enforced at write time rather than reported
after the fact. The witness's corpus-wide `gained` agrees with the run's
`newly_reached` at 6,414 exactly - the cross-check that keeps "newly
reached" from resting on the argument that only two characters differ
between the parsers.

**A second artifact defect, reported not fixed.** In the same file,
`digests.note` reads "The two differ exactly because lines were gained" -
but the two digests it annotates are byte-identical, because that block is
scoped to the 30 task-book tasks where `gained` is 0. The note was written
for the corpus-wide reading and sits beside the task-scoped one. No number
is wrong; the sentence is. Filed rather than corrected in place, on the
same rule as `shift_group`: a registered artifact is not edited to read
better.

## The re-freeze discipline, executed whole

ROADMAP-v0.19 §3a wrote this before the code existed, including the gap
nothing else would catch: `match_signatures.py` is NOT in the task book's
witness list, so widening the tokenizer moves **rendered output while every
witnessed module digest stands still**.

1. **The amendment landed BEFORE the code.** Both parser pins retired for
   future comparisons in `experiments/realization_prereg.json` and
   `experiments/foreign_voice_prereg.json`.
2. **Both prior rates DECLARED HISTORICAL in writing.** v0.18's 0.9991 and
   this cycle's foreign-voice run remain the artifacts of record for what
   was measured under the retired parser. v0.18 was NOT re-run, and the
   reason is recorded rather than inferred.
3. **Both old registered CLIs now REFUSE, by two different mechanisms**,
   and neither writes a file. `measure_realization` exits **4** with an
   explicit `closed_by_amendment` refusal naming the amendment, declaring
   `realization_rate.json` historical, pointing at the successor artifact,
   and offering `--no-write` to read the old numbers without overwriting
   the record. `measure_foreign_voice` exits **2** because its own **B7
   control** catches the moved parser digest (f5b2abba... where the prereg
   recorded 65fead2f...) and refuses to publish any rate. The second is the
   stronger of the two: the preregistration machinery closed that CLI with
   nobody having to remember to. Neither can mint a rate blended across two
   parsers - a rate is a claim about the reader it was measured under.
4. **The served diff is the gap's answer**, committed with the probe.
5. Two downstream ledgers regenerated **provenance-only** - every measured
   number identical.


# v0.19 - the address-space probe: one baseline beaten, and it was conceded in advance

Item 2. DESIGN-block-vocabulary was the maintainer-seeded incumbent the
v0.19 course ADOPTED rather than displaced, scoped to one question, against
three baselines taken from its own §4 falsifier list and preregistered in
their own commit before any measurement (ordering asserted out of git).

| baseline (the design's own) | floor | measured | verdict |
|---|---|---|---|
| retrieval - the resolver's keyword channel | 0.833 coverage / 0.030 FP | **0.3256 / 0.2059** | **NOT BEATEN** |
| compression - zstd as an archive | 118,328 bits | 829,048 | **NOT BEATEN** (7.01x) |
| compression - zstd separately addressable, shared dictionary | 5,182,024 bits | 829,048 | BEATEN (6.25x) |
| term layer - canon tokens | 8.44x (32.10x same-population) | **6.91x** | **NOT BEATEN** |

**Retrieval is not close, and both legs are required.** On the same rows in
the same run the keyword channel reaches 0.9302 (80 of 86) where the block
channel reaches 0.3256 (28 of 86), and claims 0.0294 of the rows it should
refuse where the block channel claims 0.2059. The prereg registered the
both-legs rule in advance so it could not be relaxed afterwards: a channel
that refuses everything scores FP 0.000 and coverage 0.000 and is not a
win; a channel that claims everything scores coverage 1.000 and is not a
win either.

This confirms DESIGN §3d correction 3 with a number: **MDL mints generator
boilerplate, and boilerplate is what a person never types.** The design's
§3 item 3 - that multi-word exact blocks are higher-precision retrieval
keys than single keywords - is refuted as retrieval.

**The one win was declared an arithmetic restatement in advance (E2).** The
addressable-zstd comparison recomputes something `experiments/block_mdl.json`
had already published; the prereg said so before the probe ran, so it could
not be read as a new finding afterwards.

**The single question, answered.** *Is the unified dictionary a real
object, or two existing objects wearing one id space?*

| comparison | ratio | reading |
|---|---:|---|
| unified vs grep over raw prose | 210,248x | an index beats a scan |
| unified vs zstd-decompress-then-scan | 9,013x | an index beats a scan |
| unified vs two separate indexes, both probed | 1.4408x | unification wins |
| **unified vs two indexes with one tag bit** | **0.9981x** | **unification LOSES** |

Workload: 50,401 queries, one per key in the unified space (217 block keys,
50,184 subterm skeleton keys). **Answer: TWO EXISTING OBJECTS WEARING ONE
ID SPACE.** A namespace bit sells dispatch fractionally cheaper than a
merged directory. The prereg had already registered that the grep and zstd
ratios are not evidence for unification - both existing indexes had that
advantage separately.

**Disposition: PARK WITH THE NUMBERS**, by the roadmap's own rule. One
property survives untested by any baseline here and is named for a future
unpark: append-only, path-independent growth.

The **no-silent-disposal instruction is fully discharged**: adopted ->
built -> measured -> parked by numbers, in the design's own §3e.


# v0.19 - TWO RIGHTS B0: a census that landed narrow, and the narrow reading is the finding

Item 3b, the one-hour probe adopted from the v0.19 course's series 3, with
both branches committed in advance.

| | count |
|---|---:|
| co-present pairs with differing canonical_ascii | 2,493 |
| forking at a single discriminator subterm | 200 |
| **convention-pair candidates** | **125** (213 distinct statements) |
| of those, **mathematical** convention forks | **0** |
| candidates touching an authored corpus | 1 |
| candidates with BOTH members authored | **0** |

Classification: notation_convention 114, commutation_reorder 41,
alpha_variant 24, bracketing_convention 11, domain_fork 6,
unclassified_difference 4. Verdicts: convention_pair_candidate 125,
near_duplicate 65, different_statement 6, unclassified 4.

**The famous clashes, swept with insertions allowed and detectors proven
live by injection:** sign_convention **0**, nat_zero_boundary **0**,
two_pi_placement **0**. Registered negative.

**The narrow reading, which is the finding.** Inside the 26 hand-authored
corpora the negative is unqualified: conventions were fixed by the author
and never forked, and nobody had written that down. Everything else is an
upstream dataset's authors writing one inequality two ways - a fact about
the ingestion, not about a convention this graph holds twice. **The two
halves must never be quoted apart.**

**The two probes were looking at one thing.** The single largest candidate
class is **98 pairs forking `>=` against the glyph**, which is item 3a's
territory from the other side. That is a fact about the corpus, not a
coincidence of method.

**A first measurement fell out.** The anonymized-template pass contributed
**0** pairs the twin ledger did not already carry, out of 1,015
template-sharing pairs. The twin ledger is the stronger pool, and this is
the first time that has been measured.

**Consequence:** the full TWO RIGHTS direction parks with an empty
mathematical denominator.

---

# v0.20 — the foreign voice completed (`experiments/foreign_voice_rate2.json`)

**Registered run, 2026-08-25.** Canonical grouping, C-V4′, C-G1, C-V3′.
Governing design: `docs/DESIGN-voice-completion.md`. Prereg:
`experiments/foreign_voice_prereg2.json` (24 frozen digests, all revalidated
before anything was measured).

**Artifact digest (LF sha256):**
`acb01a5f42c7bcdd5000aa9ca8e47981310fb955892907cef2d25ef4dfceeeca`,
6,741,627 bytes.

## The reading

**OVERALL FIRES.** B1 is **2,313 of 2,313 covered statements, holding 2,176
distinct elaborated terms, of which 99.9% is `lean_workbook.ground.v1`** —
the composition sentence travels with every quotation of that rate, all three
parts. B3 closes exactly at the current mute total: `0 + 2,313 + 0 + 1,706 +
172 = 4,191`.

**C-G1 cleared both floors.** The aggregate moved from v0.19's 0.80 to
**1.00** (42/42, floor 0.95), and the ten blind cases named by id *before the
canonical renderer existed* are **10 of 10 cleared** — seven detected, three
no-longer-admitting because canonicalization left them with no grouping pair
at all.

**C-V4′ holds in every voiding class**, and the point prediction was wrong in
the way that proves the restored C-R2 clause was worth restoring. It was
pre-registered at "45 of 50 — exactly v0.19's reading". Measured: **45
detected of 45 scored**, because the clause **discarded five**. The numerator
held exactly; the five that left the denominator are precisely the mutations
whose term never changed. `drop_ascription` read 0.90 in v0.19 not because
the gate missed five near-misses but because five of its "mutations" were not
mutations.

**C-V3′ (MACHINE-reader) VOID**: served 0.8417, skeleton 0.5000, ratio 0.594
against the inherited 0.5 threshold. It does not stop the cycle; the
machine-reader claim is simply not made. **C-V3 (human) stays ABSENT** and
the human-reader claim stays not-made.

## Provenance of the run itself — three executions, one reading

Recorded here rather than in the scored artifact, because the artifact's
**byte-identity is now the proof** and adding a note to it would destroy the
thing being proved.

1. **First attempt — REFUSED before scoring.** Its own guard fired:
   *"B0a recomputed differently; the denominator moved."* It wrote nothing.
   The cause was real and is a finding in its own right: commit `b1c9440` had
   already widened `TOKEN_RE` so `≥` and `≤` read natively — v0.19 §5's item
   3a, which that section ordered to land *after* v0.19's run, and which did.
   `match_signatures.py` is `f5b2abba…`, not v0.19's `65fead2f…`. The
   prereg's frozen row for it carried the **correct digest beside a false
   sentence** ("Still 65fead2f…"), which only a human reads and no machine
   compares. Fixed, dated, and the artifacts regenerated under the current
   parser — with the residue verified to be the same 4,191 statement ids, the
   eligible set the same 2,319, and **zero of 4,191 per-statement records
   differing**.
2. **Second attempt — executed TWICE, concurrently, by my error.** I read an
   empty log and a missing artifact as evidence the first launch had died and
   relaunched over it. The runner writes nothing until both passes finish —
   the property I built into it — so absence of output was the expected
   mid-run state, not a death. Both completed and both wrote identical bytes.
3. **Third execution — the clean registered one.** Single process, nothing
   else running, waited on directly. It reproduced the committed artifact
   **byte for byte**: same 6,741,627 bytes, same `acb01a5f…`, and `git
   status` reported no change to the working tree.

**All scoring executions were byte-identical.** That is a stronger statement
than B5's own gate, which compares two passes *inside* one process: this
compares across three separate process invocations, on two different days,
and gets the same file. The reading was never in doubt; the discipline was,
and "executed once" was the instruction.

## Adversarial review of the v0.20 voice lane — 2026-08-25

**No Critical.** The review independently re-derived the C-V4 id pins, the
4,191-statement residue set, the B0d seed pin, the lexicon rows and the
85-unchanged claim, and all were exact. What it found instead was a class of
defect worth naming: **gates that are true in substance but enforced by
assertions that could not have gone red.** The findings and their disposition
are below. `experiments/foreign_voice_rate2.json` was **not edited** — its
byte-identity is the reproduction proof — so everything here is either a
prospective code fix or a dated note.

### The committed artifact contains stale sentence strings beside correct numbers

`foreign_voice_rate2.json`'s **B3 gate sentence** reads *"the five buckets
close at 10,605 exactly"*, and its **G4 reading** reads *"B3 still 6,414 +
2,313 + 0 + 1,706 + 172 = 10,605"*. **Both strings are false about the tree
the run measured.** They are design prose from before `b1c9440` widened the
tokenizer.

**The measured fields beside them are correct.** B3 reports
`0 + 2,313 + 0 + 1,706 + 172 = 4,191` with `must_equal: 4191` and
`closes_exactly: true`. A reader comparing the sentence to the numbers sees
the numbers win, and the numbers are what the gate was adjudicated on. The
strings are not edited because the file's byte-identity is load-bearing; the
code string is fixed for future runs, and prereg2's copy is corrected by a
dated block.

### C-G1's denominator is a choice, and the alternative number

C-G1 removed the **8 statements that no longer admit** the mutation from both
sides, giving **42/42 = 1.00** against a 0.95 floor. **Keeping them in gives
42/50 = 0.84 — below the floor.** That is ship-versus-withhold, so the
treatment is registered in prereg2 as the choice it was, with obligations:

- **No release sentence may say "all ten detected."** The ten named cases are
  **7 detected and 3 no-longer-admit**, which are different facts.
- **C-G1's 1.00 is not the same quantity as v0.19's 0.80.** C-G1 measures the
  **term path** — delete a pair from the canonical token stream, elaborate.
  v0.19's 0.80 measured the **surface path** — mutate the English, invert,
  elaborate. The commensurable surface-path repair number is **C-V4-prime's
  `drop_group`: 42 of 42 on the raised 0.95 floor**, and that is the number
  release language should use to say the hole closed.

### A cost of canonical grouping, in C-V1's own numbers

C-V1's skeleton rate is 0.0 in both runs, but **what the misses are made of
shifted**: v0.19 had **983 elaborating to a different term and 1,330 failing
to elaborate** (57.5% in the failure bucket); v0.20 has **517 and 1,796**
(**77.6%**). Canonical rendering removes grouping words, so a scrambled
surface has less structure left to survive the trip back, and more of it now
dies at the parser instead of reaching a comparison. The artifact's own
caution names that bucket as the one where the gate never got to compare two
terms — so **the fraction of C-V1 that is actually testing the gate went
down**, from 42.5% of misses to 22.4%. The control still holds (517 genuine
different-term detections is not a small number), but it is doing less work
than it was, and that is a cost of the repair rather than a free improvement.

### C-V2's transliterable arm is now empty

`over_transliterable` reports **0 statements, elaboration 0.0, identity 0.0**
— not a failure, an empty set: the tokenizer widening absorbed those 6,414
into the natively parseable half. **C-V2's floor is met on the covered arm
alone (1.0 over 2,313).** The "easy half reported beside the residue" clause
of the design is now vacuous, and a reader must not read `0.0` there as a
measurement.

### Two smaller records

- **G7 is OWED, not cleared.** The arming artifact adjudicates it `NOT THIS
  LANE`, which is accurate — nothing in this lane touches `answer.py` or
  `serve_chat.py` — but a consumer must not read that as satisfied. It
  belongs to ROADMAP-v0.20 §4d.
- **A missed prediction.** DESIGN-voice-completion §7's C-G1 preview
  predicted **2** no-longer-admitting over the re-derived fifty. Measured:
  **8**. Direction right, magnitude four times off. The preview was labelled a
  preview and its proxy was *"its own canonical form, not the oracle's
  serialized `Expr`"*, which is exactly the gap that produces this — but a
  missed prediction is recorded, not rounded off.

### REVIEW-NOTES — adjudicated and deliberately not fixed

- **M6** — G2's tests exercise the wiring rather than the grammar. Accepted:
  **G1 is the independent grammar check** (2,313/2,313 against the pinned
  binary), and G2's job is that the seal and the renderer agree. Noted so the
  division of labour is explicit rather than assumed.
- **M10** — an FVERR counts as "detected" in C-V4-prime. Inherited from
  v0.19's C-V4 and published there and here as its own sub-count;
  `shift_group`'s 1.00 is 18 digest-moved and 24 FVERR, and the artifact says
  so.
- **M11** — already honestly reported in the commit record.
- **M3, M7, M8, L1, L3, L6, L8** — reviewed, judged not worth a commit at
  this stage. Recorded here so the record shows they were adjudicated rather
  than missed.
