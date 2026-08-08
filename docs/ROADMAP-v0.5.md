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
5. **Past modality + mirror level**: author the nine payoff nodes
   (heraldry pattern before Chekhov's converse), add the
   separately-reported mirror level, fix order_le → LT with the
   strict/reflexive relation in HEAD_ALGEBRA.
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
