# v0.6 roadmap — learned choice inside a verified world

v0.5 made the harness executable. v0.6 asks whether a tiny learned policy can
use it: choose a proposal, tool, clarification, or abstention; survive rejected
branches; and improve without moving exact operations into weights.

The integration benchmark remains deliberately paired: a mathematical
derivation and a golden-chicken conversation must use the same controller with
different verifier adapters. Passing either alone is component evidence;
passing both is the first general-controller evidence.

## 1. From oracle to learned policy

Train the first small tactic/action policy over the controller's existing
action vocabulary `{POINT, GEN, RETRIEVE, ASK, WRITE}`. Start with the 155
native Lean state–tactic–state triples and live PyPantograph tactic application.
The model proposes; Lean adjudicates; rejected transitions remain branch
evidence and never enter accepted state.

Milestones:

1. Reproduce deterministic replay with live tactic application rather than
   committed-transition lookup.
2. Capability-blind search baseline: enumerate legal tactics with no learned
   ranking and report solved rate, nodes expanded, dead branches, and timeout.
3. Learned ranking at fixed search budget; compare against the blind baseline,
   not against no search.
4. One theorem not present as an extracted transition chain, solved through
   propose → verify → backtrack → continue.
5. Run the same policy interface over story actions. A domain-specific policy
   is acceptable for this release; a second bespoke controller is not.

**PARTIAL — milestones 1, 2, and 4 now have a live capability-blind rung.**
The generic controller performs bounded breadth-first branch search while a
PyPantograph adapter keeps verifier state private and asks Lean to adjudicate
each proposed tactic.  A fixed, unranked palette closes the held-out
``forall (P Q : Prop) (h : P ∧ Q), Q ∧ P`` in 9 expanded states / 86
proposals, after exploring accepted dead branches including ``clear h``.
Removing the two projection tactics exhausts at 10 states / 80 proposals.
The first registered palette prediction missed because bare ``intro`` produced
pretty-printed names that tactics could not call; that miss and the corrective
named-intro run remain in the ledger.  This is real live search and
backtracking, not learned choice; the learned milestone is adjudicated
separately below.

**PARTIAL — milestone 3 has its first result, and the strongest control wins.** A
27,688-parameter byte-GRU ranks eight tactic schemas while the existing
controller and Lean retain search and truth. Across three cold seeds,
theorem-held-out top-1 is 0.8125 (frequency 0.4375; shuffled labels
0.25/0.375/0.375). At the identical 64-state / 512-proposal live budget, all
three checkpoints close the held-out theorem in 71/63/61 proposals (mean
65.0, arbitrary palette 86); every projection ablation still exhausts at 80.
But the post-review state-blind frequency order closes in 64 proposals, one
better than the learned mean. P-TP5 is missed and the live learned-gain claim
is retracted. This clears the learned-policy *result* gate as a negative result,
not a win. It does not clear
milestone 5, five-action choice, imported-project search, or any solved-rate
benchmark; the shared story-policy rung remains open.

The policy may choose among admissible actions, arguments, and ranking. It may
not learn equality, frame consistency, receipt verification, theorem checking,
or closed-form dispatch predicates.

## 2. Conversation becomes a maintained user frame

ASK now returns one signed session-local binding. Turn that protocol into an
explicit conversation runtime:

- unify `retrieval.UserFrame` and owned `FrameState` without promoting user
  testimony to world truth;
- define binding lifetime (goal-local, session, superseded, expired) rather than
  inheriting forever-valid session memory accidentally;
- serialize and resume state with a documented trust boundary;
- parse a bounded family of natural requests into frame-private UNKNOWNs;
- support revisions such as “now make the chicken lay silver eggs,” preserving
  prior beats and explicitly superseding only the requested premise;
- distinguish derive, retrieve, ask, and abstain with an oracle dispatcher
  before learning the choice.

Acceptance demo: two users with different private preferences produce different
story revisions from the same public story state; neither preference changes
the corpus or the other user's frame.

## 3. PROVEN-gated WRITE

Implement the fifth controller action as staged storage, symmetric with
UNKNOWN-gated RETRIEVE:

- PROVEN may stage a durable write with proof artifact, theorem identity,
  source transition trace, and proposed seed edit;
- VERIFIED may stage a review request but cannot become a proof-linked corpus
  fact;
- CONJECTURED remains quarantined; frame-local facts stay in their frame;
- no runtime action edits `data/*/nodes.json` directly;
- regeneration, validation, matcher movement, and an explicit human/prover gate
  precede durable acceptance;
- every write produces a diffable receipt and can be rejected without changing
  the store.

Before a semantic WRITE can label a statement PROVEN, close the current
`verified_by` gap: regenerate or extract the theorem's formal skeleton and
check that it corresponds to the citing statement. Artifact integrity is not
proof correspondence.

## 4. Depth generalization: recurrence reaches the consumers

The recurrent address encoder is `0.16 ± 0.07` depth OOD across two cold seeds;
masked-skeleton pretraining stabilizes it (`0.139 → 0.029` spread) but does not
move the wall. Test the actual remaining hypothesis: the pointer query and
decoder attention consume deep addresses through depth-naive interfaces.

Run a registered ablation ladder, minimum three seeds per arm:

1. recurrent address encoder only (current control);
2. recurrent pointer-query construction;
3. recurrent decoder/attention consumption;
4. both consumers;
5. parameter-matched non-recurrent control.

Report trained-depth exact, depth-OOD exact, per-step/decile failure, parameter
count, and seed distribution. “GRU wins” is not the hypothesis; shared iterative
computation is. If another tied mechanism wins, adopt the mechanism and retire
the named component claim.

## 5. Corpus-grounded analogy

Replace synthetic-tree-only evaluation with quadruples derived from real twin
families and specialization bindings:

- A:B supplies a corpus-grounded structural transform;
- C comes from a held-out discipline/family member;
- D is instantiated symbolically and verified against matcher/specializer
  structure before it becomes a target;
- family, discipline, and vocabulary holdouts are separate splits;
- a symbolic resolver and nearest-template baseline run before the model.

The first target is modest: demonstrate one held-out cross-discipline
recombination whose output exists nowhere verbatim in context and whose every
step can be checked. Do not call synthetic 1.000 corpus generalization.

## 6. Retrieval grows from stores into tools

Current RETRIEVE is exact-first and deterministic over local stores. Extend it
without weakening provenance:

- ranked neighborhood search with a capability-blind lexical baseline;
- WordNet relation traversal (hypernym, antonym, entailment) with sense-level
  ambiguity retained, not flattened;
- source adapters for external tools whose results re-enter as pointable,
  provenance-bearing context;
- miss accounting: exact miss → neighborhood → derivation → tool → ASK for
  frame-private knowledge → explicit abstention;
- dead-end records as pruning evidence, including REFUTED tool results;
- truncation and ranking always announced.

External observations enter at an empirical or conjectured rung appropriate to
their source. A successful tool call verifies the transaction, not the claim it
returned.

## 7. Richer frames without semantic leakage

- Add a routed nested-frame mutation/graft-back API; today only witnessed events
  update models through a real flow.
- Generalize event binding beyond exact oracle-authored substrings while keeping
  the visible-plant/discharge anti-vacuity controls.
- Separate reusable `frame_consistency` content from its story-specific title.
- Move retrieval resolution channels and controller commit hooks into typed
  protocols.
- Explore deeper reference-frame physics: Galilean boosts as transformations,
  acceleration invariance, and rotating-frame terms with a physics verifier.
- Re-adjudicate the Relational Frame Theory coverage table; deixis must arise
  from owner/here/now frames rather than a bespoke label.
- Keep trust roots external. Provability-logic nodes describe why the harness
  must not certify its own soundness.

## 8. Visual structure lane (first multimodal experiment)

Do not begin with web-scale pixels. Begin where the project has exact structure:
mathematical diagrams born as SVG/TikZ/plot specifications. Full protocol:
[DESIGN-visual-structure.md](DESIGN-visual-structure.md).

First experiment: formula–diagram structural twins.

- deterministically render selected corpus statements into vector diagrams;
- retain the source scene graph as the oracle parse;
- compare a parsed-SVG pointer arm against a parameter-matched raster-pixel arm;
- hold out formula families, visual styles, and rendering parameters separately;
- ask the model to align diagram elements to symbolic slots and point to the
  shared skeleton; exact geometry/topology stays symbolic;
- include deliberately inconsistent diagrams so the geometry verifier is
  load-bearing.

The expected advantage is not “general vision from synthetic diagrams.” It is
an auditable first third modality: structure from source files, learned soft
correspondence under style variation, and exact verification afterward. A
future natural-image adapter may provide uncertain object/relation proposals,
but those proposals enter as observations with provenance, never as verified
facts.

## 9. Renderer and open-language boundary

The system can produce correct flat sentences; LLM-comparable prose is still
the least-designed component. Explore two arms:

1. richer exact templates over story/event/frame structure;
2. a small surface model constrained to point into an extrinsic lexicon and
   accepted symbolic content.

Evaluate premise preservation, temporal consistency, required-beat coverage,
lexical variety, and human preference separately. Fluency must not be allowed
to hide a changed fact. WordNet may broaden glosses, but it remains an empirical
lexical source and ambiguous senses require context.

## 10. Groundedness and governance repairs

- Split grounding provenance into external, prior-corpus, same-corpus, recursive,
  and pattern-absorption channels. The provability corpus's 1.000
  self-grounding is the regression case.
- Add report regeneration/coherence checks analogous to seed coherence.
- Check semantic theorem↔statement correspondence before expanding PROVEN
  retrieval or WRITE.
- Keep runtime frame ids in `runtime.frames.*`; corpus frames remain declaration
  node references.
- Preserve prediction text and attach corrections rather than silently editing
  falsified clauses.

## 11. Release gate

v0.6 is ready only if it contains:

- one learned-policy result against a capability-blind baseline;
- one real backtracking proof search or a published negative result explaining
  why it failed;
- one maintained multi-turn user-frame demonstration;
- one depth-consumer ablation with at least three seeds per arm;
- one corpus-grounded analogy evaluation;
- one visual-structure experiment or an explicit evidence-backed deferral;
- updated checkpoints whose release stories include both winners and
  load-bearing controls;
- the full seed/schema/matcher/decomposition/specialization/test suite green.

The target remains a complete system under 64 MB. That target does not license
an LLM-benchmark claim until an external benchmark is actually run.
