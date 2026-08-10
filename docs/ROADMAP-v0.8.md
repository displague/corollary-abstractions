# v0.8 roadmap — open requests, and closing the lanes v0.7 left open

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
  measured ceiling.
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

v0.8 is ready only if it contains:

- open-prose authoring of the golden-chicken conversation with a moved-fact
  control and a serialize/restart, degrading to ASK not a guess;
- a trained corpus-analogy model reported against the strict ≈0.10–0.14 ceiling;
- one PROVEN WRITE accepted end-to-end through the full audit and one refused;
- one interface-level depth result, positive or negative, on untruncated OOD;
- updated assets whose notes explain winners, losers, and controls;
- the complete seed/schema/matcher/specializer/decomposer/test suite green.
