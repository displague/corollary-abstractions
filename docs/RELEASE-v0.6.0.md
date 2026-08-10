# v0.6.0 — The small model meets a hard baseline

Baseline: [v0.5.0](RELEASE-v0.5.0.md). Plan of record:
[ROADMAP-v0.6.md](ROADMAP-v0.6.md) (closed); carried work:
[ROADMAP-v0.7.md](ROADMAP-v0.7.md). Findings:
[DISCOVERIES.md](DISCOVERIES.md). Public narrative:
[The small model meets a hard baseline](blog/the-small-model-meets-a-hard-baseline.md).

## The headline: learned choice is real, but not yet useful enough

**Before:** v0.5 had an executable propose→verify→repeat controller, but the
proof path replayed committed transitions and the story path used a
deterministic oracle. There was no live tactic search, no learned action ranker,
and no maintained correction after a user answered.

**Now:** the controller searches a live Lean process, keeps accepted dead
branches separate from accepted state, and solves a theorem absent from the
extracted transition chains. In a theorem-heldout evaluation, a 27,688-
parameter byte-GRU architecture learns tactic schemas at 0.8125 top-1 across
three seeds. Separate checkpoints trained on all 60 transitions drive live
search in 71/63/61 proposals. The strongest state-blind frequency order solves
in 64 proposals, one better than that all-data learned mean of 65.0. The policy
result is a negative result against the right baseline, not a claimed search
improvement; the heldout and live numbers do not come from the same weights.

The same cycle makes conversation maintained and revisable: Alice and Bob hold
different signed egg-color preferences over one public golden-chicken story,
and Alice can supersede silver with copper without changing world truth. It
also constructs the first corpus-grounded analogy lane—then shows that a blind
last-slot number rule solves it perfectly.

**Demonstrate:**

```console
python prover/live_search.py
python experiments/train_tactic_policy.py --live
python scripts/conversation.py
python experiments/corpus_analogy.py --out experiments/results/corpus_analogy_repro.json
```

This release's central lesson is methodological and architectural: the learned
residual must beat the strongest cheap operation that could have stayed
outside the weights.

## Roadmap triage

### Shipped

- **Live Lean search with real backtracking:** bounded breadth-first search over
  PyPantograph states solves held-out conjunction commutation in 9 expanded
  states / 86 proposals. An accepted `clear h` transition is a genuine dead
  branch. Removing projection tactics exhausts at 10 / 80.
- **First learned tactic ranker:** 27,688 parameters, three seeds, theorem-level
  holdout, shuffled-label controls, live fixed-budget evaluation, and
  projection ablation. The strongest frequency baseline wins by one proposal
  over the learned mean.
- **Maintained owner-private conversation:** Alice and Bob render silver and
  blue eggs from identical public story state; Alice revises silver to copper
  with authenticated supersession and provenance retention.
- **First corpus-grounded analogy construction:** 40 provenance-distinct rows,
  five distinct novel targets, six source and six target disciplines, and
  independent C→D specialization checks. The blind baseline's 1.000 prevents a
  learned-generalization claim.
- **Visual gate adjudication:** the parse-first V1 protocol remains registered,
  but the model experiment is explicitly deferred because its renderer, source
  graph, invalid-pair generator, and exact verifier do not yet exist.
- **Depth-consumer ablation:** address-only remains best at
  `0.196 ± 0.064` conditional depth-OOD. Query reaches `0.179 ± 0.025`,
  memory `0.082 ± 0.027`, both recurrent consumers `0.039 ± 0.011`, and the
  two-parameter-matched MLP `0.142 ± 0.014`. More recurrence at the consumers
  damages the copy interface rather than repairing depth.

### Shipped as corrections and negative results

- Held-out tactic classification did not imply live search efficiency. The
  arbitrary 86-proposal control was too weak; a state-blind frequency order
  needs 64, versus learned 71/63/61 (mean 65).
- Corpus grounding did not make the first analogy lane difficult. Forty rows
  collapse to five targets in one ratio family, and “move B's new number into
  C's last slot” scores 1.000.
- Copy-C and nearest-authored exact scores are novelty sanity checks forced by
  target admission, not capability baselines.
- P-CA1–P-CA4 were written before execution in an uncommitted working tree, so
  they are retained only as retrospective labels, not called preregistered
  predictions.
- The released v0.5 synthetic analogy checkpoint scores 0.000 on the grounded
  RHS residual. That shows operation/domain mismatch, not task hardness, because
  the blind rule already solves the lane.
- The visual experiment is deferred rather than manufactured without an
  independent oracle.

### Carried to v0.7

- Multi-theorem proof-search curves, tactic-argument generation, and a learned
  policy protocol exercised in both proof and story domains.
- Durable authenticated conversation restart and broader request parsing.
- PROVEN-gated staged WRITE plus semantic theorem↔statement correspondence.
- A non-trivial multi-family corpus analogy split with compound source leaves.
- Ranked retrieval, WordNet relation traversal, external tools, and complete
  miss/dead-end accounting.
- Nested-frame graft-back, typed event binding, deeper physics frames, and
  provenance-split groundedness.
- The SHM→independent-superposition→coupled-modes physics ladder, followed by
  attributed affect obligations whose visibility controls information rather
  than inferring emotion; `DESIGN-affect.md` records the admission gates.
- Fourier/spectral structure, torsional SHM, non-commuting 3D composition, and
  higher-dimensional 2-plane rotations remain staged follow-ons, each kept
  distinct from statistical frequency tables and rotating reference frames.
- The visual oracle layer followed by parsed-vector versus raster arms.
- Richer constrained rendering and an honestly scoped external benchmark.

## See the improvement (Before → Now → Demonstrate)

### Lean becomes a live verifier inside search

**Before:** the controller authenticated and replayed committed Lean
transitions. It could prove that a stored step was unchanged, but could not ask
Lean what a new tactic did. **Now:** `LiveLeanVerifier` owns a PyPantograph
session and `SearchController` performs bounded breadth-first search over
kernel-adjudicated successors. Valid dead ends remain branches, never accepted
history. **Demonstrate:** `python prover/live_search.py`.

The demo reports both the successful 9-state / 86-proposal trace and the
projection-free 10-state / 80-proposal exhaustion.

### A learned policy is judged against a strong blind order

**Before:** action choice was oracle or arbitrary. **Now:** a 27,688-parameter
byte-GRU architecture is evaluated with a theorem-group holdout, three seeds,
and shuffled labels. Separately trained all-data instances drive live search.
The classification result is stable; the all-data checkpoints' live mean does
not beat the state-blind frequency ranking. **Demonstrate:**

```console
python experiments/train_tactic_policy.py --live
cat experiments/results/tactic_policy.json
```

The result artifact records learned, arbitrary, frequency, shuffled, and
projection-ablated controls in one path.

### The golden-chicken conversation can change its mind

**Before:** ASK paused once and returned one signed answer. **Now:** owner-
isolated session state survives multiple goals. Alice chooses silver, Bob blue,
and Alice later supersedes silver with copper while both signed answers remain
provenance. Neither preference enters `frame.asserted` or the public story.
**Demonstrate:** `python scripts/conversation.py`.

The honest boundary is process restart: the HMAC secret and authoritative
revocation ledger are not yet durably managed.

### Real mathematical relationships generate an analogy target

**Before:** analogy completion used synthetic trees and five synthetic
operations. **Now:** each A:B::C:D row combines a committed specialization
edge with a typed cross-discipline twin, refuses an authored D, and re-runs the
specializer on C:D. **Demonstrate:**

```console
python experiments/corpus_analogy.py --out experiments/results/corpus_analogy_repro.json
cat experiments/results/corpus_analogy_repro.json
```

The example `RATE=QUANTITY/INTERVAL : WIDTHNEXT=WIDTH/2 ::
CONCENTRATION=AMOUNT/VOLUME : CONCENTRATION=AMOUNT/2` is fully traceable. The
same artifact reports why this is not yet a learning benchmark: one family,
five targets, and a 1.000 blind positional-number rule.

### Depth consumers

**Before:** the recurrent address encoder was the only mechanism with measured
depth extrapolation, but pointer-query construction and decoder-memory
consumption were still depth-naive. **Protocol now:** five arms × three paired
seeds compare address-only, recurrent query, recurrent memory, both consumers,
and a parameter-matched one-shot MLP. Every arm trains on 50,000 depth-2/3 rows,
selects on 5,000 validation rows, tests on 5,000 held-out-combination rows, and
reports conditional depth-OOD exact on 2,450 retained depth-4/5 rows from 3,000
generated. The release does not hide the 550 capacity exclusions.

| arm | parameters | ID exact mean | conditional depth-OOD s0 / s1 / s2 | OOD mean ± SD |
|---|---:|---:|---|---:|
| recurrent address only | 1,481,987 | 0.9999 | 0.284 / 0.171 / 0.134 | **0.196 ± 0.064** |
| recurrent query | 1,581,059 | 0.9998 | 0.186 / 0.204 / 0.146 | 0.179 ± 0.025 |
| recurrent memory | 1,581,059 | 0.9999 | 0.073 / 0.053 / 0.119 | 0.082 ± 0.027 |
| recurrent query + memory | 1,680,131 | 0.9999 | 0.030 / 0.054 / 0.033 | **0.039 ± 0.011** |
| one-shot level-aware MLP | 1,680,133 | 1.0000 | 0.131 / 0.134 / 0.162 | 0.142 ± 0.014 |

P-DC1, P-DC2, and P-DC3 **missed**: both recurrence loses to address on all
three paired seeds, neither single consumer materially improves, and the
matched MLP beats both recurrence on every seed. P-DC4's complete-matrix gate
is satisfied. P-DC5 remains publicly retracted because its allocated-tensor
measurand could not observe the crash state; its MiB/GiB wording stays
corrected on the record. P-DC6 and P-DC7 fired: all 15 rows completed, maximum
whole-device footprint was 6,387,466,240 bytes, and final evaluation added at
most 2,097,152 bytes over the train/validation high-water mark.

Teacher-forced diagnostics locate the damage. Address-only averages 0.910 on
C-leaf copy and 1.000 on EOS; memory recurrence falls to 0.705 and 0.913, while
both consumers fall to 0.677 on C-leaf. **Demonstrate:** download
`depth-address-recurrent-s0.pt` and run the fresh-example command in the asset
section below.

### Vision waits for ground truth

**Before:** the parse-first visual lane existed as a design and four registered
predictions. **Now:** the release gate inventories what is absent—no renderer,
source graph, SVG/TikZ assets, invalid-pair generator, or geometry verifier—and
records an explicit deferral. The next milestone is data-first, not a toy
pixel result. **Demonstrate:** read
`docs/DESIGN-visual-structure.md` and the adjudication in
`experiments/ANALYSIS.md`; repository inventory is reproducible with:

```console
rg --files | rg -i "\.(svg|tikz|png|jpg)$|scene.?graph|diagram.*render"
```

## Discoveries of the cycle

- An accepted proof step can be a dead branch: `clear h` is legal and destroys
  the only useful evidence.
- Rendered proof-state names are observations, not necessarily callable tactic
  identifiers; named introduction repaired the first registered search miss.
- Held-out classification is not deployment gain when a global frequency
  order solves the same search more cheaply.
- Authentic conversation correction requires revocation authority, not merely
  attributable historical bindings.
- Corpus provenance does not guarantee benchmark difficulty; the first real
  analogy lane is structurally solved by a blind rule.
- A recurrent address can extrapolate while learned transformations in its
  consumers destroy the information a pointer needs to copy.
- Raw source-byte provenance is newline-fragile on Windows; the reviewed depth
  source manifest binds mixed runtime bytes to canonical Git content, and new
  runs should record blob ids at launch.

The full evidence and corrections live in
[DISCOVERIES.md](DISCOVERIES.md).

## Resolved from BACKLOG

This cycle closes the first live PyPantograph search, first learned tactic
classification/search result, maintained in-process conversation revisions,
and first corpus-grounded analogy construction. It also closes the visual
release-gate decision by documenting why V1 must wait for an oracle layer.

Their unfinished halves—proof breadth, useful policy gain, durable session
authority, non-trivial analogy families, semantic WRITE, and visual ground
truth—move to [ROADMAP-v0.7.md](ROADMAP-v0.7.md). Entries in BACKLOG remain
where they record a narrower defect or design boundary rather than a milestone.

## Honest limits

- One tiny Lean theorem is live search, not a prover benchmark.
- The learned ranker loses by one proposal on mean to a state-blind frequency
  baseline; no live learned efficiency claim survives.
- The tactic vocabulary is eight schemas / ten concrete tactics over 60 usable
  transitions from 16 Boolean-law theorems.
- Conversation remains process-local and accepts a narrow symbolic request
  family; it is not open-ended dialogue or durable identity.
- The golden-chicken prose is coherent and revisable but deliberately flat,
  not LLM-comparable in richness.
- Corpus analogy has one family and a perfect blind solution.
- The synthetic checkpoint's 0.000 corpus-residual result is a domain-gap
  observation, not evidence of task difficulty.
- WRITE is still protocol vocabulary, not a durable action.
- Vision remains a reviewed protocol with no experiment.
- Affect and oscillation are reviewed future designs, not v0.6 executable
  capabilities beyond the already-shipped generic frame/event machinery.
- Depth OOD is conditional on 2,450/3,000 generated rows; 72 depth-4 and 478
  depth-5 rows exceed fixed capacity limits, so the harder depth is filtered
  more heavily.
- The depth task contains five root-level synthetic transforms, not temporal,
  perspective, proof, or story examples; no integrated learned model spans
  those symbolic capabilities yet.
- Nothing here stands against general LLM benchmarks. The under-64-MB target is
  a system constraint, not an external-comparison result.

## Release validation record

The release candidate was validated on Windows on 2026-08-09 after the final
depth integration and document rotation:

- all 14 seeds regenerated their committed corpora byte-identically;
- schema/link validation passed for 221/221 nodes across 22 corpora;
- the matcher reported 30 shape, 31 typed, 30 family, 32 aliased, and 5 mirror
  groups, with zero ladder violations, parse problems, or slot-schema gaps;
- specialization regenerated 655 cheapest-derivation edges; decomposition
  covered 193/221 statements with mean groundedness 0.770; concept compression
  remained 11.24× versus characters;
- all 271 unit tests passed;
- the oracle controller, maintained conversation, theory-of-mind,
  frame-local ladder, and corpus-analogy demonstrations completed, including
  the analogy lane's 1.000 blind control;
- live PyPantograph search reproduced 9 states / 86 proposals, its projection
  ablation exhausted at 10 / 80, and the seed-1 downloaded-checkpoint path
  reproduced the learned 63-proposal solution;
- the address-only depth checkpoint demo reproduced 1.000 exact on 100 fresh
  trained-depth rows and 0.280 exact on 100 fresh deep rows.

The six asset files below were rehashed from their source worktrees immediately
before release; their byte counts and SHA-256 values match the tables.

## Assets and their stories

The tactic assets evidence the honest live-search loss; they do **not** ship as
winners. All are 27,688-parameter models trained on all 60 usable transitions,
including the four theorems used by the separate heldout evaluation, and all
solve the live theorem. They are not the heldout-scoring weights. Their
different search costs are the story:

| release asset | seed | live proposals | bytes | SHA-256 |
|---|---:|---:|---:|---|
| `tactic-policy-byte-gru-s0.pt` | 0 | 71 | 114,433 | `23b2586a08617b3c98cb1b20a98611905d8abe9ad7e8c79957f2351a7f69b82e` |
| `tactic-policy-byte-gru-s1.pt` | 1 | 63 | 114,433 | `098880070db5c7c9bfa4c0103fd50e55360b6dc02ca67bcd83ea3679469bd7d8` |
| `tactic-policy-byte-gru-s2.pt` | 2 | 61 | 114,433 | `641cd371431fc227e72e3130cdc15581382fd0387c60f358f145ac95d68f7df7` |

**Before → Now → Demonstrate:** before, action order was fixed. Now, the tiny
architecture learns a theorem-heldout classification signal, while three all-
data checkpoints have a 65-proposal live mean that loses to the 64-proposal
state-blind frequency order. Download any live checkpoint and exercise it
without retraining:

```console
gh release download v0.6.0 --pattern tactic-policy-byte-gru-s1.pt --dir experiments/results
python experiments/train_tactic_policy.py --live --demo-checkpoint experiments/results/tactic-policy-byte-gru-s1.pt
```

The depth assets tell the negative result rather than selecting only a winner:

| release asset | role | seed ID / OOD exact | bytes | SHA-256 |
|---|---|---:|---:|---|
| `depth-address-recurrent-s0.pt` | best surviving address-only mechanism | 1.000 / 0.284 | 5,964,599 | `64920088e60b739ea8ca5921cce1a28b2acade06c4bb0b4110e48024cc749a77` |
| `depth-both-recurrent-s2.pt` | representative falsified both-consumer arm | 1.000 / 0.033 | 6,759,783 | `2c0fd4e31090aff7cc5159f8b4fb497435ac52622a982b20da3773f98e90f17d` |
| `depth-level-mlp-s2.pt` | two-parameter-matched non-recurrent consumer control | 1.000 / 0.162 | 6,766,501 | `36128823fc653c8e8ebaca35b745cdcc8d5f722957159656a36e501dfae15f2a` |

**Before → Now → Demonstrate:** before, only address construction iterated over
path levels, and the consumers were a plausible untested explanation of the
remaining wall. Now, the complete matrix refutes that explanation: recurrence
in both consumers is the worst arm, while the matched MLP partly recovers but
still trails address-only. Exercise the released best surviving checkpoint on
fresh shallow and deep examples without retraining:

```console
gh release download v0.6.0 --pattern depth-address-recurrent-s0.pt --dir experiments/results
python experiments/demo_analogy_checkpoint.py --checkpoint experiments/results/depth-address-recurrent-s0.pt --eval-size 100
```

The public names above are intentionally different from the training scripts'
local checkpoint names. This maintainer-side manifest is the executable
source→release mapping (paths are relative to the main checkout):

| source artifact | staged / release asset |
|---|---|
| `.worktrees/learned-tactic-policy/experiments/results/tactic_policy_s0.pt` | `tactic-policy-byte-gru-s0.pt` |
| `.worktrees/learned-tactic-policy/experiments/results/tactic_policy_s1.pt` | `tactic-policy-byte-gru-s1.pt` |
| `.worktrees/learned-tactic-policy/experiments/results/tactic_policy_s2.pt` | `tactic-policy-byte-gru-s2.pt` |
| `.worktrees/depth-consumers/experiments/results/depth_address_s0.pt` | `depth-address-recurrent-s0.pt` |
| `.worktrees/depth-consumers/experiments/results/depth_both_s2.pt` | `depth-both-recurrent-s2.pt` |
| `.worktrees/depth-consumers/experiments/results/depth_mlp_s2.pt` | `depth-level-mlp-s2.pt` |

The release operator copies those six files into a temporary staging directory
under the public names before `gh release upload`; GitHub's `file#label` syntax
sets only a display label and is not used as a rename mechanism.

```powershell
$assetStage = Join-Path $env:TEMP 'corollary-v0.6.0-assets'
New-Item -ItemType Directory -Force -Path $assetStage | Out-Null
Copy-Item .worktrees\learned-tactic-policy\experiments\results\tactic_policy_s0.pt "$assetStage\tactic-policy-byte-gru-s0.pt"
Copy-Item .worktrees\learned-tactic-policy\experiments\results\tactic_policy_s1.pt "$assetStage\tactic-policy-byte-gru-s1.pt"
Copy-Item .worktrees\learned-tactic-policy\experiments\results\tactic_policy_s2.pt "$assetStage\tactic-policy-byte-gru-s2.pt"
Copy-Item .worktrees\depth-consumers\experiments\results\depth_address_s0.pt "$assetStage\depth-address-recurrent-s0.pt"
Copy-Item .worktrees\depth-consumers\experiments\results\depth_both_s2.pt "$assetStage\depth-both-recurrent-s2.pt"
Copy-Item .worktrees\depth-consumers\experiments\results\depth_mlp_s2.pt "$assetStage\depth-level-mlp-s2.pt"
gh release upload v0.6.0 `
  "$assetStage\tactic-policy-byte-gru-s0.pt" `
  "$assetStage\tactic-policy-byte-gru-s1.pt" `
  "$assetStage\tactic-policy-byte-gru-s2.pt" `
  "$assetStage\depth-address-recurrent-s0.pt" `
  "$assetStage\depth-both-recurrent-s2.pt" `
  "$assetStage\depth-level-mlp-s2.pt"
```

The four masked-skeleton/recurrent analogy assets already shipped with v0.5.0;
v0.6 does not duplicate them without a new artifact-specific story.
- No licensed `experiments/data_real/` or WordNet archive.

An asset without a Before→Now claim and runnable story will not be uploaded.

## Reproduce from a fresh clone

```console
# After completing the Python/torch setup in README.md:
.\.venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING = 'utf-8'
python scripts/check_regeneration.py
python scripts/validate_nodes.py
python scripts/match_signatures.py
python scripts/specialize.py
python scripts/decompose.py
python -m unittest discover -s tests

python scripts/conversation.py
python experiments/corpus_analogy.py --out experiments/results/corpus_analogy_repro.json

# Reproduce the released synthetic-pointer corpus residual (0.000):
gh release download v0.5.0 --pattern analogy-masked-skeleton-warm-s0.pt --dir experiments/results
python experiments/corpus_analogy.py --checkpoint experiments/results/analogy-masked-skeleton-warm-s0.pt --out experiments/results/corpus_analogy_with_model.json

# Only these live-proof commands additionally require native Lean and
# PyPantograph 0.3.15. Follow prover/FEASIBILITY.md's Windows procedure, then:
$env:PYTHONPATH = '<pantograph-venv>\Lib\site-packages'
$env:Path = "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.29.1\bin;$env:Path"
python prover/live_search.py
python experiments/train_tactic_policy.py --live

# Recreate the complete registered depth matrix (one local CUDA GPU; hours):
python experiments/analogygen.py --out-dir experiments/data
python experiments/run_depth_consumers.py --data-dir experiments/data --results-dir experiments/results
python experiments/analyze_depth_consumers.py --results-dir experiments/results

# Or demonstrate the released best surviving checkpoint without retraining:
gh release download v0.6.0 --pattern depth-address-recurrent-s0.pt --dir experiments/results
python experiments/demo_analogy_checkpoint.py --checkpoint experiments/results/depth-address-recurrent-s0.pt --eval-size 100
```

The block uses PowerShell environment syntax; other shells should translate
the two environment assignments.
