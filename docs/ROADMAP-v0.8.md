# v0.8 roadmap — open requests, and closing the lanes v0.7 left open

**CLOSED — release gate met; v0.8.0 cut. Release notes:
[RELEASE-v0.8.0.md](RELEASE-v0.8.0.md). Next increment (a deliberate pivot to
corpus scale and programming): [ROADMAP-v0.9.md](ROADMAP-v0.9.md), argued in
[DESIGN-corpus-scale-and-programming.md](DESIGN-corpus-scale-and-programming.md).
Shipped: item 1 (open-prose harness), item 2 (analogy shape holdout + model arm),
item 4 (PROVEN-WRITE acceptance), item 5 (depth interface). Carried to v0.9:
items 3, 6, 7, 8 and the existing-multi-corpus WRITE patch, re-scoped as what a
non-toy corpus needs.**

v0.7 turned single demonstrations into families with capability-blind
baselines, and in nearly every lane the cheap baseline won or the honest
ceiling came in far below the headline. v0.8 does two things with that: it
*closes* the lanes v0.7 shipped open — the analogy model arm, the proof-curve
depth, WRITE acceptance, the groundedness gate — and it opens the one
release-gate-adjacent capability v0.7 deliberately deferred: **open-language
requests through the interactive harness**.

The long-term target is unchanged: a complete system under 64 MB. The
benchmark rule is unchanged and now binds this cycle directly — no external
LLM-benchmark comparison is licensed until the system accepts open requests
*and* the benchmark's input/output contract maps honestly onto the capability
actually built. Item 1 is where that contract is first earned.

## 1. Open-language requests and the interactive harness

Promoted from v0.7 item 9, and the cycle's headline. It absorbs the design on
`docs/DESIGN-interactive-harness.md` (branch `docs/interactive-harness-design`):
a microkernel agent kernel with live mechanics over frozen policy, need-driven
dispatch before open English, and a boot capability matrix — not a demo menu.

- Keep the two request surfaces separate and layered over one kernel: item 2's
  bounded in-cycle grammar (shipped) fills already-open frame-private slots;
  **this item owns unrestricted prose authoring of new content**, reached only
  through a live session with a TTY and an optional Chat-Completions-shaped web
  skin over the *same* kernel. Collapsing the two would defer item 2 past its
  own gate; they stay distinct.
- Compare richer exact templates against a small constrained surface pointer
  that may vary words but never the accepted facts.
- Measure premise preservation, temporal consistency, required-beat coverage,
  lexical variety, and human preference **separately** — no single fluency
  scalar.
- Expand request parsing without treating WordNet senses as intent.
- Land `StopReason.WAITING` as the ASK tool-call, the subsystem registry with
  `degrade_policy`, and loop detection, with P-IH1–P-IH7 adjudicated on the
  record (P-IH7 depends on session-scoped pruning, delivered in v0.7 item 6).

Acceptance: the golden-chicken conversation is authored in open prose that
varies surface form while a control proves no accepted fact moved, remains
revisable across a serialize/restart, and degrades to ASK — never to a guess —
on an unparseable request. Coherent revisable conversation first; LLM-like
fluency is a separate, separately-measured axis.

## 2. The corpus-analogy model arm against the strict ceiling

v0.7 shipped the split and the ceilings and then disclosed that typed families
inflate the headline: the strict ceiling is ≈0.10–0.14, not 0.400. Close it.

- Add the **untyped-shape holdout** that this split should have been — cut on
  shape, not typed skeleton — without re-rolling any existing split against a
  measured ceiling. **DELIVERED (branch `feature/analogy-shape`).** A fourth
  `SPLIT_NAMES` entry, `shape`, cuts on the twin's head/arity multiset with the
  same deterministic alternating-by-size rule as the other three (no seed, no
  threshold). 131 held rows / 267 train. **Blind ceiling 0.1069**
  (`nearest_template_transfer`), which lands squarely in the disclosed strict
  ~0.10–0.14 band and confirms it. The existing family/discipline/vocabulary
  ceilings (0.400 / 0.9318 / 0.3976) are byte-for-byte unchanged — the shape
  holdout is added, nothing is re-rolled. `shape_leak` reports **zero** holdout
  rows whose shape survives in training, so this ceiling is the honest
  unseen-shape regime with no leak left to inflate it, versus the family
  holdout's `51/155 × 1.000 + 104/155 × 0.106`. P-CS8 registered before the run
  and **fired on all four sub-claims** (adjudication in
  `experiments/corpus_analogy_split.py`). Honest caveats pinned in the tests:
  the shape holdout's target Jaccard with the family holdout is 0.437 (it is
  family's structural sibling, not a fourth orthogonal axis), and its
  `symbolic_input_only` is 0.290 — below the other three's 0.40–0.70 — while
  `symbolic_typed_input` stays 1.000, so the declared-classes residual is wider
  on unseen shapes, not narrower. **Still open: the model arm** (below) is a
  separate slice and trains nothing here.
- Train the first model arm and report it against 0.398/0.400 *and* the strict
  ≈0.10–0.14, with the two corpus declarations that make the task closed-form
  named as the thing the model is or is not internalizing.
- Keep the discipline holdout labelled near-vacuous (0.932); do not cite it
  alone as difficulty.

Acceptance: a trained model result reported against the strict ceiling, with the
pointing-versus-reasoning boundary restated so no number is sold as reasoning.

## 3. Proof-search curve gains depth

The v0.7 curve is a loss over 24 theorems; its open edges are structural.

- Run live search against the **4.32.2 extraction project the training triples
  came from** — v0.7 never did, because the 4.29.1 curve project and the 4.32.2
  triples sit on different toolchains.
- Make the dead-branch ledger **cross-run** so avoidance can actually feed
  ranking; v0.7's `rejected`/`seen_states` reset every hop.
- Retire `implication_chain` as a budget discriminator (every arm solves all
  seven at the lowest rung) or replace it with a discriminating family.
- Only then re-ask whether a learned order can beat the syntax-aware blind one
  when it is allowed to remember what was dead.

Acceptance: a curve where at least one family discriminates budget at the low
rung, run against the triples' own toolchain, with cross-run pruning available
to every arm. A learned loss remains a valid result.

## 4. PROVEN WRITE earns an acceptance path

v0.7 stages a new-seed/new-corpus pair through fourteen gates and accepts
nothing. Make acceptance real and safe.

- Design the seed-aware declarative patch format carried forward in v0.7, so an
  existing multi-corpus seed (`seed_logic.py` owns logic and set theory) can be
  edited without orphaning a co-owned corpus.
- Add the first acceptance path: a staged candidate that clears every gate is
  applied, regenerates `data/` deterministically, and leaves a receipt that
  reproduces the exact transition — with rejection still byte-identical.
- Keep the honesty boundary explicit: correspondence certifies STRUCTURE, and
  exclusive ownership, not skeleton identity, is what breaks a twin tie.

Acceptance: one PROVEN candidate accepted end-to-end and one refused, both with
diffable receipts, and no runtime path that writes `data/*/nodes.json` directly.

### Registered predictions (P-PA1 – P-PA4), committed before the adjudicating run

Registered on branch `feature/write-accept` BEFORE the acceptance path in
`scripts/write_stage.py` was written, so nothing below was scored with a result
in hand. Corrections are attached under each verdict rather than edited into the
prediction text. The acceptance boundary is fixed here so it cannot be widened
after seeing what passes:

> **What "accepted" means, and does not.** Acceptance means a receipt exists AND
> the audited seed was written and its corpus regenerated by trusted code so the
> declared delta was applied. It does NOT mean the statement is true.
> Correspondence still certifies STRUCTURE only, and exclusive ownership — not
> skeleton identity — is what breaks a twin tie. The accept path runs the FULL
> staging audit first and applies nothing that the gate would not stage.

- **P-PA1 — an accepted candidate regenerates `data/` deterministically and the
  receipt reproduces it.** The accepted corpus is materialized by the same
  trusted generator the gate uses, byte-for-byte as the canonical seed's own
  `main()` would produce it — so running the committed seed reproduces the
  applied `data/<corpus>/nodes.json` with no drift, and re-deriving from the
  receipt's recorded seed source reproduces the exact same corpus. The receipt
  records the seed path, corpus, node id, and the corpus/working-tree digests
  before and after.
- **P-PA2 — a refused candidate leaves the whole working tree byte-identical.**
  A candidate the gate refuses is applied by nothing: the accept path runs the
  audit first, returns the refusal with its diffable receipt, and writes no seed
  and no corpus. `data/` and every other trusted tree are byte-identical before
  and after, exactly as for staging.
- **P-PA3 — acceptance never writes `data/*/nodes.json` except via trusted
  seed-derived regeneration, and never executes candidate code.** The model
  supplies a declarative seed; trusted code parses it as data (never `exec`)
  and materializes the corpus. There is no runtime path on which the candidate
  hands over `nodes.json` bytes, and none on which the candidate seed is run.
- **P-PA4 — an accepted seed that would orphan a co-owned corpus is refused
  before any application.** Replacing an existing multi-corpus seed
  (`seed_logic.py` owns logic and set theory) with a single-corpus declarative
  envelope is refused at `seed_ownership` during the audit, so the accept path
  applies nothing and the working tree stays byte-identical. The seed-aware
  declarative patch that would let a co-owned corpus be edited safely is the
  carried-forward follow-up; the new-seed/new-corpus lane is the delivered gate.

## 5. Depth moves to the interface, not another component

The v0.6/v0.7 consumer matrix is a closed negative: address-only remains best
and more recurrence at the consumers damages the copy interface. Follow the
verdict.

- Remove the conditional-only OOD blind spot: score all generated examples or
  report both retained and unconditional metrics with capacity exclusions kept.
- Localize the remaining cliff per decode step and depth decile; add
  internal-subtree replacement, argument reordering, and two-step composition as
  separate rungs; add a corpus-grounded deep-structure task.
- Treat the interface/data boundary as the object of study; freeze model
  complexity until an interface change moves OOD.

Acceptance: one interface-level result (positive or negative) on untruncated
OOD with parameter/compute/exposure-matched controls, not another consumer arm.

## 6. Physics, affect, oscillation, and the frequency domain

The remainder of v0.7 item 7, under its stated assumptions.

- The SHM → independent-superposition → coupled-modes ladder; a torsional
  oscillator (`I θ'' = -κ θ`) as the registered rotational-SHM candidate;
  non-commuting 3D composition and higher-dimensional 2-plane rotation kept
  distinct from rotating-frame fictitious forces.
- A frequency-domain rung after the time-domain oracle — Fourier series/
  transform, amplitude/phase spectrum, normal-mode eigenfrequency multiset,
  sampling/Nyquist controls — with a physical spectrum kept distinct from a
  statistical frequency table.
- The first affect slice as an **attributed narrative-response obligation**:
  a visible event without an explicit affect/report effect leaves affect
  UNKNOWN; Plutchik/Russell/PAD/constructionist structures are named source
  models, never synthesized sentiment.

Acceptance: cited seed-generated SHM and torsional statements with preregistered
matcher outcomes, one independent-versus-coupled negative control, and one
executable attributed-response obligation. Frequency and higher-dimensional
rotation rungs may remain explicitly partial.

## 7. Groundedness gains a gate, and reports gain coherence checks

v0.7's channels report but do not gate.

- Argue and add a groundedness **gate** against the conservative lower bound
  (external 0.246, not the generous 0.535), not the upper one.
- Refresh `reports/decompositions.json` (stale since the channel split) and add
  report regeneration/coherence checks parallel to seed coherence.
- Keep the provability 1.000 self-grounding as the regression case; keep runtime
  frame ids under `runtime.frames.*`.

Acceptance: a channel gate justified against the lower bound, and a report whose
schema the shipped CLI agrees with, checked in CI.

## 8. Visual step 6, and a scoped look at a visual-corpus direction

- Land the parameter-matched parsed-vector versus raster arms over the v0.7
  right-triangle oracle (steps 1–5 shipped). P-V1–P-V4 remain registered.
- Follow-on source-structured families (SHM phase portraits, independently
  generated Lissajous, source-qualified emotion wheels) share the render/parse/
  invalidate/verify protocol, not equations or epistemic authority.
- **Investigation, not commitment:** survey whether the Gemini/Gemma/SigLIP/
  WebLI visual-corpus lineage suggests a direction for how visual comprehension
  could fit this architecture — parse-first structure handed to a tiny model as
  an interface, never pixels as intent. Output is a design note that may
  influence the v0.9 backlog; it licenses no weights this cycle.

Acceptance: one parsed-vector and one raster arm reported against the ≤0.742
blind baseline, and a written direction note. Natural and medical imagery remain
later domains with separate evidence and governance.

## 9. Governance carries forward

- Preserve every registered prediction; attach corrections rather than editing.
- Continue mandatory independent adversarial review at every trust boundary,
  and record both the defect and the regression that closes it — the rule that
  found a load-bearing defect on eight consecutive v0.7 slices.
- No external LLM-benchmark comparison until item 1's contract is earned.

## Release gate

**MET — v0.8.0 cut.**

- open-prose authoring of the golden-chicken conversation with a moved-fact
  control and a serialize/restart, degrading to ASK not a guess — **MET** (item 1;
  closure/coverage/ordering gate catches added/negated/misattributed/reordered
  facts; surface-variety 0.980 vs 0.060);
- a trained corpus-analogy model reported against the strict ≈0.10–0.14 ceiling
  — **MET** (item 2; 0.104 ± 0.012 on the 0.1069 shape holdout — an honest
  negative, beats no blind ceiling);
- one PROVEN WRITE accepted end-to-end through the full audit and one refused
  — **MET** (item 4; atomic seed→regenerate→receipt, whole-tree delta, refusal
  byte-identical);
- one interface-level depth result, positive or negative, on untruncated OOD
  — **MET** (item 5; enlarging the copy budget does not move OOD — a matched-control
  negative; blind spot removed);
- updated assets whose notes explain winners, losers, and controls — **MET**
  (RELEASE-v0.8.0.md; both trained lanes' negatives are recorded in committed
  result JSON, the faithful artifact since the checkpoints are seed-reproducible-only);
- the complete seed/schema/matcher/specializer/decomposer/test suite green
  — **MET** (14 seeds byte-identical, 221/221 nodes, matcher 30/31/30/32/5 with 0
  ladder violations, 655 specialization edges, 193/221 decompose @ 0.770,
  781 unit tests).
