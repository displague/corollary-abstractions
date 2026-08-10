# v0.7.0 — Breadth before benchmarks

Baseline: [v0.6.0](RELEASE-v0.6.0.md). Plan of record:
[ROADMAP-v0.7.md](ROADMAP-v0.7.md) (closed); carried work:
[ROADMAP-v0.8.md](ROADMAP-v0.8.md). Findings:
[DISCOVERIES.md](DISCOVERIES.md). Adjudications and numbers:
[experiments/ANALYSIS.md](../experiments/ANALYSIS.md).

## The headline: single demonstrations became families with baselines

**Before:** v0.6 proved each capability once. One live Lean theorem. One
maintained conversation that could not survive its own process. One analogy
lane a blind rule solved perfectly. One learned ranker that lost to a frequency
order by a single proposal. The lesson of that release — *the learned residual
must beat the strongest cheap operation that could have stayed outside the
weights* — was a verdict about one theorem.

**Now:** every headline lane is a family with a declared capability-blind
baseline, and in every lane where a cheap operation could win, it was allowed
to and usually did. One theorem became a 24-theorem held-out set across four
proof families with fixed-budget solved-rate curves; the learned ranker still
loses, now to a *syntax-aware* blind order rather than a frequency one, over
144 live runs instead of one trace. Conversation now serializes, restarts under
a runtime-owned key ring, and refuses forged or rolled-back bindings without
signing its own public story. A PROVEN theorem can stage a durable seed through
fourteen gates and a real proof of a true theorem was caught staging a *false*
claim before the gate was hardened. The analogy lane was rebuilt until a blind
last-slot rule scores 0.000, and then we disclosed that our own split still
leaks and the strict ceiling is ≈0.10–0.14. A deterministic geometry oracle
accepts 240 valid figures and rejects 1,440 controlled invalids, each at exactly
its registered check.

**No new model weights ship in v0.7.** The proof-search curve is driven by the
*same* three byte-GRU checkpoints v0.6 already published; every other lane
delivers code, committed evidence, and — repeatedly — an honest negative.
This is a breadth-and-method release, and the assets section says so plainly.

**Demonstrate:**

```console
python scripts/conversation.py
python scripts/proof_correspondence.py
python experiments/corpus_analogy_split.py
python experiments/visual/verify.py
python scripts/decompose.py
```

## Roadmap triage

### Shipped

- **From one live theorem to a proof-search curve** (item 1). 24 held-out
  theorems in `conjunction` (6), `implication_chain` (7), `disjunction` (5) and
  `project_import` (6); set digest `af6f6cb7…`. 144 live PyPantograph runs, no
  replay in any arm, over budgets 4/8/16/32/64 states × 32/64/128/256/512
  proposals plus a wall-clock ladder. At the middle rung: syntax-aware blind
  21/24, frequency (v0.6's winner, rebuilt) 20/24, learned 18/21/19, arbitrary
  17/24; every arm reaches 24/24 at v0.6's own maximum budget. Schema choice is
  separated from tactic-argument generation and Lean stays the sole transition
  authority. **The learned arm loses** — item 1 declared a loss valid in
  advance.
- **Shared policy protocol in a second domain** (item 1, story family).
  `experiments/story_curve.py` drives eight briefs through the *same*
  `SearchController` with domain weights and a disjoint five-schema vocabulary.
  Every arm solves every brief, so the shared *protocol* is demonstrated while a
  general *controller* is explicitly not claimed: the best-to-worst spread is
  1.07% on the story side against 65.6% on the proof side.
- **Conversation survives process boundaries** (item 2). Serialize, restart
  under `SessionKeyRing.open(keyfile)`, re-admit surviving bindings, keep
  revising — with the public golden-chicken story byte-identical and unasserted.
  Forged, superseded, and rolled-back bindings are refused from the restored
  private ledger and monotone counter, never from an envelope MAC over the
  deliberately-unsigned public file. All seven registered P-DS predictions
  fired, including the one registered as most likely to miss (`ledger-rollback`).
- **PROVEN-gated WRITE and semantic correspondence** (item 3).
  `scripts/proof_correspondence.py` regenerates a formal skeleton from every
  `verified_by` theorem's goal and matches it against the citing statement:
  **15 CORRESPONDS, 1 UNTRANSLATABLE, 0 MISMATCH** over 16 committed links.
  `scripts/write_stage.py` stages a PROVEN new-seed/new-corpus pair through
  fourteen gates and accepts nothing; refusals leave `data/` byte-identical with
  a diffable receipt. Delivered for authenticated staging; existing-corpus edits
  and acceptance remain open.
- **Retrieval becomes tool use** (item 6). Ranked neighborhood search with
  announced scores and caps, one-hop WordNet relation traversal (every record
  `empirical`, none bindable), an offline observation adapter that retains
  source/timestamp/query/rung, the executable exact→neighborhood→derivation→
  tool→ASK→abstain miss chain, and session-scoped pruning — all with typed
  `Channel`/protocol seams replacing the string-valued channels.
- **Frames graft back without leaking semantics** (item 7, two bullets).
  `FrameExecutor.with_nested`/`route` graft a mutated nested model back
  immutably and re-check ownership, the closed-ancestor rule, and the
  event-history subset invariant across the whole subtree. The story adapter's
  substring searches are replaced by a typed event binder with word-boundary
  spans; every anti-vacuity control survives and the golden-chicken output is
  byte-identical.
- **Visual ground truth before visual weights** (item 8, steps 1–5). A
  deterministic right-triangle renderer, scene graph, controlled-invalid
  generator, exact incidence/length/right-angle verifier, and normalized SVG
  round trip. N = 240 valids and 1,440 invalids; the verifier accepts 240/240
  and rejects 1,440/1,440, each at its one registered gate; disabling any check
  lets exactly that class through; 5,040 round trips are byte-exact; no blind
  surface baseline exceeds 0.742. **No weights exist in this layer.**
- **Groundedness splits into channels** (item 10). `decompose.py` attributes
  every grounded constituent to external / prior-corpus / same-corpus /
  recursive / pattern-absorption and prints a per-corpus table; provability is
  the only corpus flagged `self_certifying`. Aggregates unchanged (graph mean
  0.770; 193/221 statements decompose). The channels report but do not yet gate.

### Shipped as corrections and negative results

- **The learned ranker loses to a *stronger* baseline than v0.6's.** A
  syntax-aware blind order (21/24 at the middle rung) beats every learned seed,
  and the frequency order it beat in v0.6 (20/24) also still beats learned.
- **No cross-task dead-branch avoidance.** Over branches shown genuinely dead
  (frontier-aware accounting, 227 accepted dead transitions), the learned arms
  re-propose known-dead signatures at 0.2063 versus syntax's 0.2053 — no
  measurable avoidance, now over the right denominator after review blocked the
  first, inflated ledger.
- **A true theorem staged a false claim.** Independent review found that
  constant-class collapse let a Lean proof of `P ∧ ⊥ ↔ ⊥` adjudicate CORRESPONDS
  against the false claim `P and true = true` and stage it. Fixed by keying
  constants on POLE, not spelling; re-adjudicated on the record.
- **The analogy ceiling is inflated by our own split.** Families are *typed*
  skeletons, so nearest-template replay scores 1.000 wherever a held-out row's
  untyped shape is still in training; the honest strict ceiling is ≈0.10–0.14,
  and the untyped-shape holdout that should have been the split is left open
  rather than re-rolled against a measured ceiling.
- **The analogy lane measures pointing, not reasoning.** Adding exactly two
  corpus declarations takes the symbolic solver to 1.000 on all three holdouts,
  so no model number from this lane may be sold as reasoning; and no model has
  been trained yet.
- **A groundedness inference failed its own baseline.** The "62 of 75 absorbed
  patterns are owned out-of-discipline" reading was retracted: the exact channel
  is a wash by rate and 5.7:1 by count, so absorption quarantines such credit
  rather than concentrating it.

### Carried to v0.8

- The proof-search curve's open edges: `implication_chain` is a vacuous budget
  discriminator, the dead-branch ledger is run-local and cannot feed ranking,
  and live search has never run against the 4.32.2 project the training triples
  came from.
- Corpus analogy's untyped-shape holdout and the model arm against the
  0.400/0.398 (strict ≈0.10–0.14) ceilings.
- PROVEN WRITE's existing-corpus, seed-aware declarative patch format and any
  acceptance path.
- The depth consumer/interface matrix per item 4, the remaining item-7 physics/
  affect/oscillation/rotation and frequency-domain rungs, and the groundedness
  *gate* (channels report but do not gate).
- **Item 9 — rendering and open-language requests — in full.** It was not a v0.7
  release-gate item; unrestricted prose authoring and the interactive harness's
  open surface are the first-class v0.8 headline.
- Visual step 6 (parameter-matched parsed-vector vs raster arms).

## See the improvement (Before → Now → Demonstrate)

### One live theorem becomes a solved-rate curve

**Before:** live search proved one held-out conjunction commutation and one
learned ranker lost to a frequency order by a single proposal — one trace, one
comparison. **Now:** 24 theorems across four families run through 144 live
PyPantograph searches with no replay, and four ranking arms (arbitrary,
frequency, syntax-aware, learned) receive the identical candidate multiset so a
proposal-count difference is a *schema-ordering* difference. The learned arm
loses to the syntax-aware blind order at every intermediate budget.
**Demonstrate:** the curve is committed at
`experiments/results/proof_curve.json` (theorem set `af6f6cb7…`); the live rerun
requires native Lean + PyPantograph per `prover/FEASIBILITY.md`, then
`python prover/curve_search.py`.

### The golden-chicken conversation survives a restart

**Before:** Alice and Bob held signed egg-color preferences that vanished with
the process; the HMAC secret and revocation ledger were not durably managed.
**Now:** both sessions serialize to public JSON, the verifiers are dropped, and
a fresh process reloads a runtime-owned root key, re-derives per-session signing
keys, and re-admits the surviving bindings — while a superseded, forged, or
rolled-back pre-restart binding is refused from the restored private ledger.
**Demonstrate:** `python scripts/conversation.py`.

### A proof of a true theorem is checked against the claim it certifies

**Before:** `verified_by` proved byte integrity — that a stored theorem was
unchanged — but not that the theorem's goal *means* what the citing statement
says. **Now:** correspondence regenerates a formal skeleton from the theorem's
opening goal, translates the propositional fragment, and matches it against the
statement's whole declared form set: 15 CORRESPONDS, 1 UNTRANSLATABLE (an
`α : Type` binder outside the declared fragment), 0 MISMATCH, and a
capability-blind gravity statement citing `modus_ponens` is MISMATCH.
**Demonstrate:** `python scripts/proof_correspondence.py`.

### The analogy lane refuses its own blind solution

**Before:** 40 rows, five targets in one ratio family, and "move B's new number
into C's last slot" scored 1.000. **Now:** 914 admitted rows dedup to 398
distinct targets over 11 typed families, cut on three seedless holdout keys; the
v0.6 killer scores 0.000 / 0.011 / 0.048; and the release itself discloses that
typed families inflate the headline ceiling and the strict ceiling is
≈0.10–0.14. **Demonstrate:** `python experiments/corpus_analogy_split.py`.

### Geometry gets an oracle before it gets a model

**Before:** the visual lane was a design and four registered predictions with no
renderer, scene graph, or verifier. **Now:** 240 seeded valid right triangles
and 1,440 controlled invalids, an exact verifier that accepts and rejects each
at its one registered check, and 5,040 byte-exact render→parse→verify round
trips — with no capability-blind surface baseline above 0.742 and no weights in
the layer. **Demonstrate:** `python experiments/visual/verify.py`.

## Discoveries of the cycle

- A stronger blind baseline than last cycle's still beats the learned ranker;
  the residual-must-beat-the-baseline verdict survives from one theorem to a
  four-family curve.
- Skeleton correspondence keyed on symbol *spelling* would have hidden a false
  claim behind constant-class collapse; keying on the lattice POLE both catches
  it and keeps the corpus's honest cross-spelling citations.
- Durable refusal cannot rest on signing the public story: a rolled-back but
  genuinely-signed snapshot is only caught by a private monotone counter, and
  the signature must be verified *before* the counter is consulted or a forged
  high-water mark locks the real owner out.
- A typed-skeleton split silently trains on the untyped shape it means to hold
  out; a lane can launder its own ceiling unless the holdout is cut on shape.
- Detection after arbitrary candidate code runs is not containment: PROVEN WRITE
  was narrowed to a literal-data envelope materialized by trusted code because
  scratch execution plus post-hoc digests let a candidate reach the real tree.
- The most empirically justified rule of the project held again: on eight
  consecutive trust-boundary slices, independent adversarial review found a
  load-bearing defect the author's own review had missed.

The full evidence and corrections live in
[DISCOVERIES.md](DISCOVERIES.md) and [experiments/ANALYSIS.md](../experiments/ANALYSIS.md).

## Honest limits

- The learned tactic ranker loses to a syntax-aware blind order and shows no
  cross-task dead-branch avoidance; no live learned efficiency claim survives.
- The story family has no ranking lever — every arm solves every brief — so the
  shared *protocol* is demonstrated but a general *controller* is not.
- PROVEN WRITE stages only a new-seed/new-corpus pair and accepts nothing;
  correspondence certifies STRUCTURE, not truth and not ownership between
  structural twins.
- Corpus analogy has no trained model; the strict ceiling is ≈0.10–0.14 and the
  untyped-shape holdout that would test it is still open.
- The visual layer is oracle-only; no parsed-vector or raster arm has run.
- Groundedness channels report but do not gate; `external` is an upper bound and
  the conservative counterpart is reported beside it.
- Conversation accepts a bounded symbolic request grammar, not open-ended
  dialogue; unrestricted prose authoring (item 9) is entirely v0.8.
- Nothing here stands against general LLM benchmarks. The under-64-MB target is
  a system constraint, not an external-comparison result.

## Assets and their stories

**v0.7 ships no new model-weight assets, and that is the honest state of the
release.** The proof-search curve is driven by the three byte-GRU tactic
checkpoints v0.6 already published; they are byte-identical here, which is why
the curve can name them by SHA-256 rather than re-uploading them:

| curve checkpoint | v0.6 release asset | SHA-256 |
|---|---|---|
| `learned_s0` | `tactic-policy-byte-gru-s0.pt` | `23b2586a08617b3c98cb1b20a98611905d8abe9ad7e8c79957f2351a7f69b82e` |
| `learned_s1` | `tactic-policy-byte-gru-s1.pt` | `098880070db5c7c9bfa4c0103fd50e55360b6dc02ca67bcd83ea3679469bd7d8` |
| `learned_s2` | `tactic-policy-byte-gru-s2.pt` | `641cd371431fc227e72e3130cdc15581382fd0387c60f358f145ac95d68f7df7` |

The three `story_policy_s{0,1,2}.pt` checkpoints produced by
`experiments/story_curve.py` are new, but they carry no differentiating result
(every arm solves every brief) and have no runnable demo path, so under this
project's rule — *an asset without a Before→Now claim and runnable story will
not be uploaded* — they stay unreleased reproducibility outputs.

The substantive v0.7 artifacts are committed evidence, not weights:
`experiments/results/proof_curve.json` (144-run curve with live provenance),
`experiments/results/proof_curve_leakage.json`,
`experiments/results/story_curve.json`, and the geometry oracle's seeded
figure/invalid corpus under `experiments/visual/`.

No licensed `experiments/data_real/` or WordNet archive ships, as in every prior
release.

## Release validation record

Validated on Windows on 2026-08-10 against `main` after the proof-curve and
proven-write merges:

- all 14 seeds regenerated their committed corpora byte-identically;
- schema/link validation passed for 221/221 nodes across 22 corpora;
- the matcher reported 30 shape, 31 typed, 30 family, 32 aliased, and 5 mirror
  groups, with zero ladder violations, parse problems, or slot-schema gaps;
- specialization regenerated 655 cheapest-derivation edges; decomposition
  covered 193/221 statements with mean groundedness 0.770;
- proof correspondence reported 15 CORRESPONDS / 1 UNTRANSLATABLE / 0 MISMATCH,
  reproducibly;
- the full unit suite (695 tests) passed.

The committed unit suite exercises the WRITE and verifier refusal logic against
fake backends and does **not** start Lean; the 144-run proof curve is
reproducible only where PyPantograph and the pinned Lean toolchain are
installed. Its recorded provenance (host, torch/GPU footprint, real Pantograph
elaboration-error dicts) is what attests liveness — no code path advances state
from a committed transition.

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
python scripts/proof_correspondence.py
python experiments/corpus_analogy_split.py
python experiments/visual/verify.py

# The live proof-search curve additionally requires native Lean +
# PyPantograph. Follow prover/FEASIBILITY.md's Windows procedure, then:
$env:PYTHONPATH = '<pantograph-venv>\Lib\site-packages'
$env:Path = "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.29.1\bin;$env:Path"
python prover/curve_search.py
```

The block uses PowerShell environment syntax; other shells should translate the
two environment assignments.
