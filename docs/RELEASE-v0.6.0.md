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
- **Depth-consumer ablation:**
  [PENDING FIVE-ARM / THREE-SEED VERDICT — replace before release.]

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

[PENDING FINAL MEANS, PAIRED EFFECTS, P-DC1–P-DC7 VERDICTS, AND DEMONSTRATE
COMMAND AFTER THE COMPLETE MATRIX.]

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
- [PENDING depth discovery.]

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
- [PENDING depth limit.]
- Nothing here stands against general LLM benchmarks. The under-64-MB target is
  a system constraint, not an external-comparison result.

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

[PENDING depth winner/representative seeds and parameter-matched control,
selected only after the three-seed matrix. Every attached checkpoint gets its
exact result, role, SHA-256, and exercise command.]

The four masked-skeleton/recurrent analogy assets already shipped with v0.5.0;
v0.6 does not duplicate them without a new artifact-specific story.
- No licensed `experiments/data_real/` or WordNet archive.

An asset without a Before→Now claim and runnable story will not be uploaded.

## Reproduce from a fresh clone

```console
# After completing the Python/torch setup in README.md:
python scripts/check_regeneration.py
python scripts/validate_nodes.py
$env:PYTHONIOENCODING = 'utf-8'
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

# [PENDING depth reproduction command and released-asset demo]
```

The block uses PowerShell environment syntax; other shells should translate
the two environment assignments.
