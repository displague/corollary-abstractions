# v0.7 roadmap — breadth before benchmarks

v0.6 put a learned proposer inside live verified search and discovered that a
strong state-blind baseline could still beat it. It also turned conversation
into maintained private state and built the first corpus-grounded analogy lane,
where an even simpler blind rule solved every admitted case. v0.7 follows those
results rather than scaling around them: broaden the tasks until state,
structure, and verification are demonstrably load-bearing.

The long-term target remains a complete system under 64 MB. No item below
licenses an LLM-benchmark comparison until the system accepts open requests and
the benchmark protocol measures the capability actually built.

## 1. From one live theorem to a proof-search curve

- Expand native PyPantograph search from one `Init` theorem to a versioned set
  of held-out theorems, including project imports and multiple proof shapes.
- Report solved-rate curves at fixed state/proposal/time budgets, not one trace.
- Compare learned ranking against arbitrary, frequency, and syntax-aware blind
  orders on every theorem.
- Separate schema choice from tactic-argument generation; keep Lean as the sole
  transition authority.
- Preserve accepted dead branches as pruning evidence and test whether learned
  ranking avoids them across tasks, not just once.
- Run the same policy protocol over story actions before claiming a general
  controller. Domain-specific weights are acceptable; a second controller is
  not.

Acceptance: at least two proof families and one story family, each with a
capability-blind baseline and a fixed-budget curve. A learned loss or tie is a
valid result.

## 2. Conversation survives process boundaries

- Define durable key identity, rotation, and revocation for ASK receipts and
  supersession records without serializing ambient secrets into public state.
- Unify `retrieval.UserFrame` and owned belief frames under an explicit lifetime
  protocol: goal-local, session, superseded, expired, durable.
- Parse a bounded but growing natural-request grammar into frame-private slots,
  including corrections, pronouns, and owner references.
- Preserve provenance when a user changes a preference; never promote testimony
  into corpus or frame truth merely because it persists.
- Exercise derive → retrieve → ask → revise → abstain in one maintained session.
- **From `docs/DESIGN-interactive-harness.md`:** durability is blocked by more
  than keys. `RetrievalVerifier` holds its HMAC secrets **and** its
  anti-replay/supersession ledgers on the instance
  (`scripts/retrieval.py:741-744`), so the harness `Session` is a handle to
  live authority, not a serializable value object. A restart that carried keys
  forward but not the ledgers would silently re-admit consumed requests. The
  bounded request grammar above is that design's **Phase 2** (in-cycle,
  filling already-open frame-private slots); unrestricted prose authoring is
  item 9 and lands last. Until this item ships, the harness HTTP skin must not
  pretend restarts are safe.

Acceptance: serialize, restart, authenticate, and continue the Alice/Bob
golden-chicken demo while a stale or forged pre-restart binding is refused.

## 3. PROVEN-gated WRITE and semantic proof correspondence

- Regenerate a formal skeleton for every `verified_by` theorem and check that it
  corresponds to the citing corpus statement; byte integrity alone is not
  semantic ownership.
- Let PROVEN stage a seed edit, proof artifact, theorem identity, and transition
  trace. VERIFIED may stage review only; CONJECTURED and frame-local content may
  not request durable promotion.
- Run regeneration, schema/link validation, matcher-delta prediction, and human
  or prover approval before acceptance.
- Make rejection leave the durable store byte-identical and retain a diffable
  receipt explaining why.

No runtime action may write `data/*/nodes.json` directly.

## 4. Depth follows the v0.6 consumer verdict

The five-arm verdict is negative and specific: address-only remains best at
`0.196 ± 0.064` conditional depth-OOD exact; query reaches `0.179 ± 0.025`,
memory `0.082 ± 0.027`, both recurrent consumers `0.039 ± 0.011`, and the
two-parameter-matched MLP `0.142 ± 0.014`, while every arm stays at shallow
ceiling. Carry forward recurrent address construction, freeze the consumer
expansion, and investigate the interface rather than a component name.
Required next evidence:

- remove the conditional-only OOD blind spot: either raise limits/constrain
  generation so all 3,000 generated examples are scored, or report both the
  current retained-set metric and an unconditional metric that counts capacity
  exclusions; keep generated/retained counts by depth;
- per-decode-step and depth-decile localization of the remaining cliff;
- at least five seeds for any small mean difference promoted to a headline;
- parameter-, compute-, and exposure-matched controls;
- a shallow wrapper-transfer baseline before calling the current five
  root-level transforms an analogy task;
- internal-subtree replacement, argument reordering, associative/distributive
  rewrites, nested substitution, inverse/converse operations, and two-step
  composition in separate rungs rather than one mixed generator;
- independent holdouts for vocabulary, skeleton/transform pair, complete
  transform family, depth, chain length, discipline, owner/visibility pattern,
  and narrative schema where applicable;
- a task whose deeper structure is corpus-grounded rather than synthetic only;
- one alternative shared iterative mechanism before concluding that GRU is
  uniquely necessary.

Only after the consumer matrix is closed, run dropout as a secondary paired
ablation (`0.0`, `0.1`, `0.2`) and measure OOD plus seed variance. Reallocate
evaluation budget away from additional in-distribution rows once every arm is
at ceiling and toward untruncated OOD, longer chains, held-out families, and
shortcut controls. Dropout is not the proposed repair for a perfect-ID/
collapsed-depth interface.

Treat v0.6's roughly 4.0–5.9 GiB observed footprint as a conservative recovery
protocol, not a permanent utilization target. If a later experiment benefits
from larger batches, run a separate throughput/safety ladder at 60%, 70%, then
80% whole-device occupancy, exercising train → atomic checkpoint → greedy OOD
evaluation at every rung. Record reserved and whole-device peaks independently.
Do not jump to 14 GiB on the current 15.92-GiB device: it exceeds the present
80% guard and approaches the two prior bugcheck footprints. Safety-cap changes
must not be mixed into an architecture comparison.

If no consumer arm materially beats recurrent addressing alone, freeze model
complexity and move effort to the interface/data boundary the ablation exposes.

## 5. Corpus analogy becomes a real split

The v0.6 lane had 40 rows but only five targets in one ratio family, and a blind
last-slot rule scored 1.000. Replace it with a task where that rule fails:

- represent compound specialization expansions with explicit pointable source
  leaves rather than inventing vocabulary;
- require at least three non-isomorphic structural families before a family
  split is named;
- separate family, discipline, and literal-vocabulary holdouts;
- deduplicate targets before counting examples;
- run symbolic, nearest-template, number/position heuristics, and shuffled
  controls before training;
- verify every D through the matcher/specializer and keep it absent from input.

Acceptance: a non-trivial capability-blind ceiling below 1.000 and a model
result reported against it. Synthetic 1.000 remains a mechanism result only.

## 6. Retrieval becomes tool use

- Add ranked neighborhood search with announced scores and caps.
- Traverse WordNet hypernym, antonym, and entailment relations without
  flattening sense ambiguity or raising lexical evidence above empirical.
- Add one external source adapter whose returned observations retain source,
  timestamp, query, and epistemic rung.
- Execute the complete miss chain: exact → neighborhood → derivation → tool →
  ASK for frame-private knowledge → explicit abstention.
- Store REFUTED and exhausted branches as reusable pruning evidence.
- Replace string-valued retrieval resolution channels and duck-typed
  controller commit hooks with typed protocols while preserving the existing
  five-action API, receipt checks, and verifier-owned authority boundaries.
- **From `docs/DESIGN-interactive-harness.md`:** the miss chain above is the
  harness need dispatcher, generalized from retrieval to every registered
  subsystem — that design cites this item rather than reinventing a parallel
  ladder. The subsystem registry it specifies is **the same seam** as the
  typed-protocols refactor above: one seam, one refactor, no second dispatch
  vocabulary. Note also that “store REFUTED and exhausted branches as reusable
  pruning evidence” is currently only true **within one run**: `rejected` is a
  local in `Controller.run()` (`scripts/controller.py:271`) and
  `SearchController`'s `seen_states`/`attempted` are per-search, so a
  multi-run dispatcher resets all pruning at every hop. Making that evidence
  session-scoped is a prerequisite here, adjudicated by P-IH7.

A successful tool transaction proves what was fetched, not that its content is
true.

## 7. Frames generalize without leaking semantics

- Add routed nested-frame mutation and graft-back with explicit owner paths.
- Replace exact oracle-authored event substrings with a typed event binder and
  retain visible-plant/discharge anti-vacuity controls.
- Generalize the story-titled `frame_consistency` interface for physics and
  belief users without weakening its law.
- Deepen reference-frame physics: executable Galilean boosts, acceleration
  invariance, and rotating-frame terms under a physics verifier.
- Build the oscillation ladder under explicit assumptions: linear undamped
  mass–spring SHM and ω/T/f first; independent orthogonal superposition versus
  genuine coupling second; resonance and normal modes third. Do not use
  Lissajous figures as evidence of coupling or collapse Kepler III into SHM.
- Add a frequency-domain rung after the time-domain oracle: Fourier series/
  transform, amplitude and phase spectrum, normal-mode eigenfrequency
  multiset, sampling/Nyquist controls, and power spectral density. Keep a
  physical frequency spectrum distinct from a statistical frequency table;
  both distribute quantities, but over different objects and units. DFTs,
  coordinate transforms, and alias checks stay symbolic; weights may rank or
  interpret noisy observed peaks only after the exact transform is available.
- Separate three meanings of multiplanar rotation. Extend the existing SO(3)
  rigid-transform/quaternion nodes with non-commuting 3D composition and Euler-
  angle coordinate caveats; author a torsional oscillator
  (`I θ'' = -κ θ`, `ω = √(κ/I)`) as the registered rotational-SHM candidate;
  then treat higher-dimensional double rotation as simultaneous 2-plane
  blocks with independent angles. Do not collapse any of these into rotating-
  reference-frame fictitious forces or ordinary two-axis translation.
- Add the first affect slice as an **attributed narrative-response
  obligation**, not inferred sentiment. `witnessed_by` may deliver an explicit
  report/effect but must never synthesize emotion from event type. The paired
  negative keeps the event visible while removing the affect/report effect and
  must leave affect UNKNOWN.
- Treat Plutchik, Russell, PAD, and constructionist structures as named source
  models. Continuous affect outputs remain empirical proposals with
  provenance; they cannot certify private feeling or mutate corpus truth.
- Re-adjudicate the Relational Frame Theory coverage table; deixis must emerge
  from owner/here/now frames rather than a bespoke label.
- Keep trust roots external. The system may verify receipts it minted, but it
  may not certify its own verifier soundness.

Acceptance for the new science/affect part of this item: cited seed-generated
SHM and torsional-oscillator statements with preregistered matcher outcomes;
one independent-versus-coupled negative control; and one executable attributed
response obligation where a visible event without an explicit affect/report
effect leaves affect UNKNOWN. Frequency-domain and higher-dimensional rotation
rungs may remain explicitly partial, but may not be conflated with the first
cut.

**DELIVERED (these two bullets only) — graft-back and the typed binder.**
`FrameExecutor.with_nested(parent, owner_path, new_child)` grafts a mutated
model back immutably and `route(state, owner_path, transition)` runs any
executor transition inside a model and hands back the ROOT, so a rejected
branch still produces no next state. Grafting REPLACES rather than inserts —
creation keeps `open_nested`'s refusals — and re-checks the child-owner key,
the closed-ancestor rule, and the event-history subset invariant across the
whole grafted subtree. The `replace(parent, children=...)` surgery is gone
from the grandchild test; the poisoned-child control keeps it as a documented
API bypass, because refusing that graft is exactly what makes surgery the only
route to the loud RuntimeError it tests. P-NF4–P-NF6 fire.

The story adapter's case-insensitive substring searches are gone. Beat-creating
transitions carry `binds` records (`element@start:end`); the adapter validates
each span against the frame's declared surface forms for that element id and
stores typed mentions on the beat, and plant/discharge consult those records by
element identity. Every anti-vacuity control survives, two structurally: a plant
still amends the VISIBLE setup beat (records are rebased onto the amended text),
and a discharge requires a record ON the resolution beat, so "the evidence is
really in the resolution" is no longer a substring test. The hidden-ledger
control sharpens to "identical prose, no bindings → UNKNOWN", and an element id
that never appears in the rendered story now plants, discharges, and closes —
something the substring check could not do. P-EB1–P-EB2 fire. P-EB3's second
clause was REFUTED by independent post-commit review and repaired in the same
branch: exact surface matching alone let a span name a word fragment, so a
story containing a "donkey" and a "monkey" planted, discharged and closed a
`key` obligation with no key in it — an inherited hole the substring check
shared and the migration had claimed to close. Bound spans now require word
boundaries, and that run is the control. The golden-chicken
demo's output is byte-identical. Still open: the element lexicon is the
adapter's own declaration rather than corpus-grounded event structure, surface
matching is deliberately exact, and no consumer mutates a nested model in a live
flow yet. The remaining bullets of this item are untouched.

## 8. Build visual ground truth before visual weights

The v0.6 visual experiment was explicitly deferred because no oracle layer
existed. Land it in this order:

1. deterministic right-triangle renderer — **SHIPPED** (`experiments/visual/`);
2. source scene graph with stable slot-to-element identities — **SHIPPED**;
3. controlled-invalid pair generator — **SHIPPED** (six near-miss classes);
4. exact incidence/length/right-angle verifier with ablation tests —
   **SHIPPED** (six gated checks, each ablated into a unique escape);
5. normalized SVG/tree input — **SHIPPED** (exact round trip);
6. only then, parameter-matched parsed-vector and raster arms — **OPEN**.

Steps 1–5 result: `N = 240` seeded valid figures and 1,440 controlled
invalids. The verifier accepts 240/240 valids and rejects 1,440/1,440
invalids, each at exactly the one check registered as its gate; disabling any
single check lets all 240 of that check's class through while the other five
classes stay fully rejected; 5,040 render→parse→verify round trips are exact
and re-render byte-identically; and no capability-blind surface baseline
exceeds 0.742 balanced accuracy on any class in any style. P-VO1–P-VO7 were
committed before the adjudicating run and all seven fired, with three
corrections attached rather than edited in: P-VO6's evidential base is the
240 valids, P-VO5 is a design invariant, and P-VO3 shows check separability
rather than a complete check set. Numbers, the two defects adversarial
review found, and the corrected blind baseline are in
`experiments/ANALYSIS.md`. No weights exist in this layer.

P-V1–P-V4 in `DESIGN-visual-structure.md` remain registered until step 6.
Natural images and medical imagery remain later domains with separate evidence
and governance requirements.

After the right-triangle oracle, follow-on source-structured families may
include SHM phase portraits, independently generated Lissajous figures, and
source-qualified emotion wheels/circumplex maps. They share the render/parse/
invalidate/verify protocol, not equations or epistemic authority.

## 9. Rendering and open-language requests

- Compare richer exact templates with a small constrained surface pointer that
  can vary words but not accepted facts.
- Measure premise preservation, temporal consistency, required-beat coverage,
  lexical variety, and human preference separately.
- Expand request parsing without treating WordNet senses as intent.
- Publish the first external benchmark only when its input/output contract maps
  honestly onto implemented capabilities; include memory and artifact size,
  latency, and abstention quality alongside accuracy.
- **From `docs/DESIGN-interactive-harness.md`:** this item owns **unrestricted
  prose authoring** — the harness's last phase, reached through a live session
  with a TTY and optional Chat-Completions surface over the same kernel. It
  does **not** own bounded slot-filling, which is item 2's in-cycle grammar.
  Keep the two separate: open authoring of new content is a different problem
  from filling a declared slot, and collapsing them defers item 2 past its own
  release gate.

The golden-chicken target is coherent, revisable conversation first; LLM-like
fluency is a separate measured axis.

## 10. Groundedness and release governance

- Split grounding into external, prior-corpus, same-corpus, recursive, and
  pattern-absorption channels; the provability corpus's 1.000 self-grounding is
  the regression case.
  **SHIPPED** (`feature/grounding-channels`): `decompose.py` attributes every
  grounded constituent to one channel and prints a per-corpus table;
  aggregates unchanged (graph mean 0.770, 440 exact / 75 pattern). Regression
  case reads out as `same_corpus` 0.775 + `pattern_absorption` 0.192 vs
  `external` 0.033, and provability is the only corpus flagged
  `self_certifying`. GC1–GC5 all fired. Open: the channels report but do not
  gate, and the graph-wide finding that 62 of 75 absorbed patterns are owned
  outside the absorbing statement's discipline is unaddressed.
- Add report regeneration/coherence checks parallel to seed coherence.
- Keep runtime frame ids under `runtime.frames.*`; corpus frames remain node
  references.
- Preserve every registered prediction and attach corrections rather than
  silently editing it.
- Continue mandatory adversarial review at trust boundaries; record both the
  defect and the regression that closes it.

## Release gate

v0.7 is ready only if it contains:

- a multi-theorem live proof-search curve with strong blind baselines;
- a durable authenticated conversation restart or an explicit negative result;
- one PROVEN-gated staged WRITE rejected or accepted through the full audit;
- a non-trivial multi-family corpus analogy split;
- the visual oracle layer and verifier, even if learned visual arms miss;
- one shared policy protocol demonstrated in both proof and story domains;
- updated assets whose notes explain winners, losers, and controls;
- the complete seed/schema/matcher/specializer/decomposer/test suite green.
