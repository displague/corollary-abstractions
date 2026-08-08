# v0.5 roadmap — chains and frames

Theme: chained composition with the prover as verifier — each proposal
becomes the next step's premise, checked before it stands — plus the
frames implementation the scope design specified. The golden-chicken
demo and a multi-step derivation remain one milestone in two costumes.

## Carried (designs intact)

1. **Chained composition** (the thesis): define one controller protocol
   over typed frame state, unresolved slots, actions, verifier outcomes,
   accepted next state, and an auditable branch trace. Its complete action
   vocabulary is `POINT` (bind present context), `GEN` (propose symbolic
   structure, including a tactic or story transition), `RETRIEVE` (query an
   extrinsic store), `ASK` (query the user for frame-private information), and
   `WRITE` (stage a PROVEN result for durable storage). Verifier adapters own
   domain truth: PyPantograph/Lean for proofs, the frame-local ladder plus
   temporal and narrative axioms for stories, and matcher/executor checks for
   corpus operations. Dead branches remain in the trace as refutations and
   pruning evidence; they never become premises.

   **Oracle-first milestone:** before training a policy, a deterministic
   dispatcher must produce one 3-step derivation and one 3-beat story from the
   same loop. It resolves closed forms locally, retrieves when an appropriate
   store may bind an UNKNOWN, asks when only the interlocutor can bind it, and
   abstains when no resolver succeeds. This capability-blind baseline separates
   controller, state, tool, and verifier defects from policy defects. Only then
   does a tiny learned policy replace the oracle. Prover phase 2 (baseline
   tactic policy + PyPantograph search) supplies the first learned verifier-
   coupled policy.

   **PARTIAL — oracle baseline:** `scripts/controller.py` now enforces the
   shared contract and five-action vocabulary, immutable rejected branches,
   duplicate-dead-end pruning, and bounded termination. One loop executes a
   three-step replay of contiguous machine-extracted Lean transitions and a
   three-beat golden-chicken story; negative controls reject an unrecorded
   tactic, a wrong Lean state, out-of-order beats, and a frame-trait
   contradiction; mutation probes also prove rejected verifier and state-key
   hooks cannot alter accepted state through in-place side effects; policy and
   goal callbacks are isolated too. Epistemic controls prevent untrusted replay
   data from assigning PROVEN and distinguish an undeclared trait (UNKNOWN)
   from an explicitly denied one (REFUTED) (16/16
   tests). This proves the control-plane boundary, not
   policy generalization: only `GEN` has adapters, Lean is committed extraction
   replay rather than live PyPantograph, and the story verifier covers the
   three-beat/shared-desire/frame-trait subset rather than the full scoped
   ladder.
2. **Depth 0.226 → 1.0**: extend recurrence past the address encoder
   into the consumers (pointer queries / decoder attention are still
   depth-naive). The fork proved iteration over exposure; this finishes
   the job.
3. **Corpus-grounded analogy**: quadruples from twin families, targets
   verified against specialize bindings; skeleton-instantiated
   synthetic training, real-corpus eval.
4. **Frame executor**: the narrative axioms are already authored and matched —
   `frame_consistency` is a typed twin of the machine-checked Boolean
   complement law, and Chekhov's gun instantiates the temporal response
   pattern. Adopt the scope design (top-level scope object; frames registry as
   validator upgrade), migrate the remaining scope semantics out of
   `frame_consistency`'s prose, and build the runtime state manager that extends
   `compose_assert`'s ladder into a frame-local evaluator for those axioms.

   **PARTIAL — scope and finite obligations execute; first scoped nodes authored:**
   the live schema now carries the draft's optional `scope` object (the
   original 199 nodes validated unchanged; matcher report was byte-identical — `scope` is
   invisible to it, as designed). `validate_nodes.py` checks frame-id
   pattern, frame agreement across members (order-insensitive for
   set-valued fields), and suspends/governed_by resolution over the merged
   graph, without crashing on malformed scope values. `scripts/frames.py`
   executes the frame-local ladder: declarations load as the local
   VERIFIED tier and may contradict a world truth only if the frame
   explicitly suspends it (the boundary rule — the adversarial review's
   blocking finding was that declarations could smuggle contradictions
   past `suspends`); assertions adjudicate against declarations plus
   unsuspended world truths; a contradiction whose only grounding is
   suspended is UNKNOWN to read-only `check` and admissible via
   `assert_literal` as an act of invention, after which its negation is
   REFUTED; missing information is UNKNOWN never REFUTED; the world map
   itself is rejected if incoherent; and `close_frame` demotes every local
   truth to `on_exit` status — nothing leaks, closed frames refuse
   everything, double-close is an error. The golden-chicken oracle routes
   trait checks and temporal events through this executor on the same generic
   Controller. `plant` now opens a frame-local Chekhov obligation,
   `discharge` closes only its matching element, and an outstanding obligation
   REFUSES frame close without state change or demotion. The rendered setup
   must visibly plant the element and the discharge must cite text in the
   resolution, preventing a hidden-ledger pass. Item 5 subsequently authored
   the first shared-scope declaration/assertion pair for cartoon gravity and a
   scoped premise-persistence declaration. Still open: the check is finite
   close-time accounting rather than general LTL
   model checking, and `compose_assert`'s demo ladder is not yet wired to
   `frames.py`.

   **Registered obligation prediction (before implementation or tests):**
   planting an element creates one frame-local obligation under
   `narrative.constraint.chekhov_gun`; discharging that same element closes
   it. A close request with any obligation still outstanding is `REFUSED`,
   leaves the frame open, and emits no exit demotions. Discharging an element
   that was never planted is `UNKNOWN`, not `REFUTED`: the past-facing
   no-deus-ex-machina converse is item 5 work and must not be smuggled into
   the future-facing Chekhov law. Exact duplicate event retries are idempotent,
   while a fresh event id for an already-bound element is `REFUSED`; an
   unrelated discharge cannot close another element's obligation, and all
   obligation actions against a closed frame are `REFUSED`.

   **Adjudication:** fired on every listed branch. The first implementation
   also failed a vacuity audit before review: its obligation ledger could pass
   while the rendered setup omitted the plant. The story adapter now requires
   a visible setup mention and resolution-text evidence for discharge.
   Independent review then found that the mention could be unrelated and late,
   and that a duplicate plant duplicated prose; setup-only, element-binding,
   and end-to-end idempotence controls now close those paths.
   A later review clarified that the original phrase “duplicate plants” was
   too broad: accepting a fresh id without recording it allowed that id to
   change event kind later. Idempotence is now exact-event retry only; fresh ids
   are rejected and the corrected prediction is tested explicitly.
5. **DELIVERED — past modality + mirror level.** The nine design entries
   expanded to ten nodes because cartoon gravity is a declaration/assertion
   pair: six temporal nodes, four narrative nodes, and the graph's first two
   practical scope frames. The matcher reports five mirror-only groups
   separately from the unchanged 28/29/28/30 structural ladder; no mirror is
   counted as a typed twin. The false `BEFORE ~ LEQ` alias is gone: strict
   precedence uses `LT`, and `HEAD_ALGEBRA` records strict-part/reflexive-
   closure relations without claiming identity. Adjudication also exposed two
   limits: the registered groundedness values missed (0.667/0.500/1.000 for
   since/once/no-deus, rather than 1.000/1.000/0.500), and specialization rose
   622 → 626 with two intended temporal/narrative edges plus two algebraic
   false positives. Full evidence is in `experiments/ANALYSIS.md`.
6. **Retrieval and durable storage as actions.**
   - **6a — `RETRIEVE(key)`:** wire the ladder's closed-form UNKNOWN trigger to
     a unified query adapter over the lexicon, twin ledger, decomposition index,
     proof artifacts, and later external tools. Results re-enter context as
     pointable material. A miss degrades to neighborhood search, `ASK` when the
     missing value is frame-private, then honest abstention.
   - **6b — `WRITE(candidate)`:** the read-side symmetry is a PROVEN-gated
     durable write. A Lean-checked or equivalently machine-verified conclusion
     may be staged as a seed-level candidate with its proof and provenance;
     regeneration and the normal validation suite remain the commit gate.
     Lower ladder rungs stay conjectural or frame-local, and generated
     `data/*/nodes.json` is never edited directly.
7. **Attunement curves**; **model-in-the-loop grounded composition**;
   **expressive rendering** — as specified in ROADMAP-v0.4 and
   DESIGN-frames-and-retrieval.

## Tooling opens (BACKLOG-tracked)

8. typed_resort's tie (same defect the shape sort lost, one level up —
   fix must preserve membership); the commutative-path used_compound
   gap (+169 edges pending a decision on what "informative" means);
   reports/ regeneration check; the equivalent_forms-heads lint that
   would have generated the payoff list mechanically; provenance
   scope_note (one-line schema fix, drafted); BACKLOG.md structure
   (1000+ lines, needs sectioning by status); cost-weight
   falsifiability (author nodes that discriminate the weights, or
   accept them as conventions explicitly); trainers save checkpoints
   by default (complete the partial).

## Data lanes

9. Wikisem ingestion behind its preconditions (^ commutativity now via
   HEAD_ALGEBRA; atom classification; subterm granularity; license
   confirmation). Real-Spanish follow-ups. LeanDojo extraction scaled
   past the 155-triple seed corpus.
