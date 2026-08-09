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
   close-time accounting rather than general LTL model checking.

   **Registered compose/frame prediction (before implementation or tests):**
   wiring adds no corpus or matcher change. A deterministic helper in
   `compose_assert.py` will obtain, rather than print by assertion, this exact
   runtime sequence from `FrameExecutor`: declared truth VERIFIED; contradiction
   REFUTED; missing trait UNKNOWN; suspended world contradiction UNKNOWN before
   admission and VERIFIED after `assert_literal`; clean close VERIFIED with all
   local truths demoted to `conjectured`; post-close check REFUSED. Existing
   global PROVEN/HYPOTHESIS/REFUSAL examples remain separate because frames do
   not manufacture proof or structural-family status.

   **Adjudication — fired:** `compose_assert.py` now obtains the registered
   seven-step sequence and exit demotions from `FrameExecutor`; none of those
   labels is locally reimplemented. The global PROVEN/HYPOTHESIS/REFUSAL
   examples remain report/corpus demonstrations, as predicted. The full suite
   moved 63 -> 65 tests with no corpus or report diff.

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

     **Registered 6a prediction (before implementation or tests):** this slice
     changes no corpus or matcher report. A retrieval session may be created
     only through a factory given an actual `UNKNOWN` adjudication; the factory
     rejects every other rung. One unified, read-only store loads five
     source kinds—corpus statement, node lexicon, twin/mirror ledger,
     decomposition index, and `verified_by` proof artifacts. Exact statement-id
     retrieval for `logic.boolean_laws.de_morgan_laws` returns pointable
     material from all five; a truncated id misses exact lookup but succeeds by
     deterministic token-neighborhood search. `POINT(position)` before
     retrieval is REFUSED, while pointing to a returned position VERIFIED-binds
     the pending slot and clears it. With an empty store the same two-action
     oracle cannot solve (capability-blind control); the miss remains UNKNOWN,
     adds no context, and cites honest abstention. A `frame_local` frame refuses
     before consulting any store and cites `ASK(slot)` as the only permitted
     escalation. Non-retrieval frame actions delegated through the wrapper are
     byte-for-byte verdict/evidence equivalent to `FrameAssertionVerifier`.

     **Adjudication — fired:** the initial store exposed 702 attributable items
     (209 corpus, 209 lexicon, 67 structural groups, 208 decomposition entries,
     9 proof-linked summaries). The exact query returns six items spanning all
     five kinds; the truncated query takes the neighborhood path. RETRIEVE then
     POINT solves in two accepted controller steps, while the empty-store
     control remains unsolved with unchanged state and ABSTAIN evidence. All
     guard, duplicate, malformed, delegation, and provenance predictions fire;
     the suite moves 70 -> 81 tests with no `data/` or `reports/` diff. VERIFIED
     labels the retrieval transaction, not its contents: every pointable item
     retains its corpus/derived/verified/proven status. **At 6a's landing,** ASK
     was only an explicit escalation in evidence; item 10a below now ships its
     return channel. External tools are not stores yet,
     token-neighborhood search is deterministic but unranked taste, and no
     learned policy chooses the point; open-language parsing into the canonical
     key remains unbuilt.

     The physics.frames slice grows the same loader without adapter changes to
     715 items (213 corpus, 213 lexicon, 69 structural groups, 211
     decomposition entries, 9 proof-linked summaries).

     **Review corrections:** the first POINT implementation checked only that a
     position existed, so an unrelated retrieval could vacuously close the
     slot. Review reproduced De-Morgan UNKNOWN -> retrieve modus ponens ->
     POINT(0) -> solved. POINT now rechecks the selected item's aliases against
     the pending slot's exact/neighborhood key constraint. A
     second review then showed that exact alias equality was itself
     insufficient: the symbol `a` names many unrelated lexica, so any one of
     them could still bind an `a` slot. POINT now requires the matching
     corpus/lexicon/proof views to resolve to one corpus owner. The same review
     found that the loader assumed optional `verified_by.reference` existed;
     artifact-only proof links now load and count their whole theorem-bearing
     artifact. Re-review then caught two interactions: an exact title could be
     rejected because another node neighborhood-matched it, and an accepted
     frame mutation could leave the original UNKNOWN stale. Exact matches now
     resolve owners only against exact matches, and pending needs retain their
     literal and re-adjudicate against current frame state before RETRIEVE or
     POINT; a non-UNKNOWN result is recorded in a resolution ledger and clears
     the retrieval need. A final precedence review showed that context
     retrieved under a different key could still supply a neighborhood match even when the
     pending key had an exact owner. The existence of an exact owner now blocks
     every neighborhood binding for that key. All five reproducers are
     permanent controls. The next protocol review found two fail-open edges:
     an empty JSON artifact could still produce a PROVEN summary, and unknown
     RETRIEVE/POINT transition names ran by kind alone. JSON proof artifacts
     now require applicable theorem transitions, while the verifier accepts
     only `lookup` and `bind`. Those controls bring the final suite to 89
     tests. A further proof-boundary review showed that file existence and a
     theorem label still did not establish machine checking. Proof summaries
     now authenticate only complete native JSON state–tactic–state rows;
     a referenced theorem must include a transition closing to `no goals`.
     Incomplete, unfinished, and unsupported artifact formats fail closed. That
     artifact-format control brings the suite to 90 tests. Identity review then
     required an artifact-only link to contain exactly one theorem; shared
     multi-theorem artifacts require an explicit reference. The same review
     stopped one- and two-character lexicon aliases from reverse-prefix
     matching longer truncated words. The scoped truncated-query and ambiguous
     proof controls bring the suite to 92 tests.

     **Key-grounding correction:** the preceding controls still trusted a
     caller-supplied `suggested_key`; a caller could pair any UNKNOWN literal
     with an unrelated but unambiguous key and then “solve” it. Session
     construction now requires the canonical query tokens to equal the
     unresolved literal's value. The parser must therefore put the desired
     retrieval target into frame state before the adapter runs. A mismatched
     De-Morgan-literal/Quadratic-Formula-key control is rejected, bringing the
     suite to 93 tests. This proves symbolic retrieval relative to a parsed
     request; it does not prove open-language request parsing.

     **Proof-trust correction:** a locally closing `no goals` row may represent
     one completed subgoal in a truncated extraction, not the whole theorem.
     The adapter now shares the controller's existing SHA-256 trust root for
     `prover/sample_triples.json`. Only that digest-pinned extraction can label
     proof material PROVEN; structurally valid local artifacts remain VERIFIED.
     The completed-subgoal control brings the suite to 94 tests.

     **Action-key correction:** grounding the session key was insufficient
     while RETRIEVE could substitute another alias or unrelated key. RETRIEVE
     now requires canonical equality with the pending literal's key before any
     store access. Neighborhood widening remains an internal deterministic
     fallback, not free policy metadata. The alias bypass control brings the
     suite to 95 tests.

     **Public-boundary correction:** because retrieval state is an immutable
     but public dataclass, factory validation alone did not prevent a forged
     pending key. RETRIEVE and POINT now recheck key/literal equality on every
     action. Proof trust likewise binds both the pinned digest and the canonical
     `lean4` system label. The forged-state and wrong-system controls bring the
     suite to 97 tests.

     **Five-store attribution correction:** owner resolution originally used
     only corpus/lexicon/proof views, so a unique decomposition-only key could
     retrieve but not bind. Binding now resolves by source tier: canonical
     statement views first, then unique decomposition ownership, then a unique
     structural-group record. Decomposition and twin-ledger controls bring the
     suite to 99 tests.

     **Context-provenance correction:** public state also allowed a caller to
     forge a pointable record whose aliases and owner looked valid. POINT now
     authenticates the complete selected record against the read-only store
     snapshot before resolving ownership. The invented-item control brings the
     suite to 100 tests.

     **Operator-preservation correction:** lexical token equality collapsed
     distinct closed forms such as multiplication and addition skeletons.
     Exact lookup and key grounding now normalize only case/whitespace while
     preserving operators; lexical tokens are reserved for neighborhood
     fallback. Two previously colliding shape-group keys bind distinct records,
     bringing the suite to 101 tests.

     **Transaction-provenance correction:** exact store membership did not
     prove that context arrived through RETRIEVE. The verifier now mints a
     session-local authenticated receipt over key, mode, and admitted item ids;
     POINT requires that receipt as well as store membership. Prefix matching
     also requires both query and alias tokens to be at least three characters,
     so a key like `7` cannot bind `IEEE 754`. These controls bring the suite to
     103 tests. Receipts are intentionally runtime-local; serializable session
     resumption remains open.

     **Session-replay correction:** a receipt bound only to one verifier could
     be copied between two same-key sessions. Each retrieval state now carries
     a random session id covered by the receipt signature. Copying admitted
     context/receipts into another session is REFUSED, bringing the suite to
     104 tests.

     **Tokenless-exact correction:** exact alias comparison now runs before the
     ASCII word-token check. A symbolic key such as `¬` can retrieve and bind
     an exact alias, while a tokenless non-match still has no neighborhood
     fallback. This brings the suite to 105 tests.

     **Frame-replay correction:** receipts now cover the immutable `FrameSpec`
     as well as verifier/session/key/material. Authenticated context from an
     open frame cannot be transplanted into a `frame_local` scope, bringing the
     suite to 106 tests.

     **Registered proof-link lint prediction (before implementation or
     adjudication):** the cheap first rung of semantic-link governance changes
     no corpus, matcher group, decomposition, or specialization report. The
     merged-graph validator will fail closed when a `verified_by` artifact is
     absent or malformed, when an explicit theorem reference is absent from
     that artifact, when a reference is claimed by more than one statement,
     when an artifact path escapes the repository, or when a reference-free
     link does not identify exactly one theorem.
     Existing data should remain green: all nine proof-linked statements use
     the committed native artifact, all 16 explicit references resolve, and
     each theorem reference has exactly one statement owner. Capability-blind
     controls will deliberately pair a valid theorem with the wrong statement:
     this cheap lint is predicted to ACCEPT that case, documenting that it
     checks provenance integrity and exclusive ownership—not theorem/statement
     semantic correspondence. The latter remains prover phase 2 work.

     **Adjudication — fired, including the predicted blind spot:** the merged
     corpus has nine proof-linked statements carrying 16 distinct theorem
     references; every reference resolves in the committed native artifact and
     every theorem has exactly one statement owner. Twelve fail-closed regression
     methods exercise eighteen missing/invalid/out-of-root artifact, malformed
     link/transition, missing or empty reference, ambiguous reference-free link,
     and shared-theorem cases. The deliberately unrelated gravity node citing valid
     `BooleanLaws.modus_ponens` remains accepted, as predicted: this rung makes
     proof provenance auditable but does not manufacture semantic
     correspondence. The suite moves 111 -> 126 tests; corpus data and all
     structural reports remain byte-identical.

     **Review corrections:** the first lint treated a theorem-name-only JSON
     row as a proof artifact, making the capability-blind control itself
     vacuous. Artifact parsing is now shared with retrieval: every row must be
     a complete state–tactic–state transition and the selected theorem must
     reach `no goals`; the false-association control cites the real committed
     Lean extraction. Review also demonstrated that malformed `verified_by`
     shapes bypassed the lint when optional `jsonschema` was absent, and that
     default CLI paths failed outside the repository root. The custom fallback
     now validates list/entry/system/artifact/field shapes itself, and only
     default paths are repository-anchored (explicit paths retain normal CWD
     semantics). All three reproducers are permanent controls.

     Re-review then found that whitespace-only proof states still satisfied the
     word “complete,” and that case-variant/unsupported system labels could
     split ownership even though retrieval accepts only `lean4`. All four
     transition fields are now nonblank, and validation rejects every proof
     system without a registered parser. Those reproducers are permanent too.
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

## Cognitive frames program (queued — docs/DESIGN-cognitive-frames.md)

10. The 2026-08-09 direction conversation mapped theory of mind, physical
    frames of reference, relational frame theory, self-verifying theories,
    and the BERT/WordNet lineage onto existing machinery; the design doc
    carries the full mapping, six registered predictions (P-CF1..6), and
    the sequencing. Queued items, in the design's order:

    - **SHIPPED (executable first cut) — 10a: ASK return channel as ToM
      entry** (the agreed next slice,
      reframed): the return path is the user-frame update rule; the user
      is an owned frame whose bindings arrive via ASK. Multi-turn
      golden-chicken revision is its acceptance test.

      **Registered 10a prediction (before implementation or tests):** this
      slice changes no corpus or structural report. UNKNOWN resolution gains a
      closed-form channel marker: durable-store needs remain RETRIEVE-only;
      explicitly user-private needs (and `retrieval: frame_local` authorial
      needs) may ASK, while neither channel silently falls through to the
      other. An accepted `ASK(clarify)` records one verifier-minted question in
      a persistent user-owned runtime frame and makes the generic Controller
      stop as WAITING, not SOLVED or EXHAUSTED. A later run over the same
      session accepts only a channel-signed reply bound to the exact session,
      immutable FrameSpec, user owner, question id, slot, unresolved literal,
      and answer value; it clears the pending UNKNOWN and records a user
      binding without asserting the answer as world truth, corpus truth, or a
      `verified_by` fact. Guessed signatures, a second verifier, answer
      mutation, and cross-question/session/frame replay are REFUSED with zero
      state mutation. The capability-blind policy may propose every public ASK
      argument except the channel secret and therefore cannot fabricate a user
      reply. Acceptance demo: an existing golden-chicken story receives the
      underspecified revision “make it lay eggs,” pauses to ask egg color, then
      resumes after the user answers “silver” and renders one coherent revision
      from the recorded binding. This is a two-turn symbolic conversation, not
      open-English intent parsing or learned dialogue.

      **Adjudication — fired:** `RetrievalNeed.resolution_channel` separates
      store and user-private holes before policy choice. ASK never touches the
      store for a user-private need; RETRIEVE refuses the same need before its
      store query. `ASK(clarify)` records a signed question in a persistent
      `UserFrame` and the unchanged generic controller stops with the new
      WAITING outcome. A second controller run over the same session accepts a
      channel-signed reply, clears only the exact still-UNKNOWN need, and adds a
      signed `UserBinding`; no frame assertion, corpus node, or epistemic status
      is promoted. Twenty-five controls cover guessed/second-verifier/mutated
      signatures; cross-question/session/frame/owner replay; forged public
      question/binding/pending state; stale resolution; closed frames; channel
      confusion; and the rule that every non-reply action is frozen while the
      branch waits. Suite: 130 -> 155. The golden-chicken demo pauses after
      “make it lay eggs,” asks `egg_color`, resumes on “silver,” and renders
      “Now the golden chicken laid silver eggs.” Corpus and structural reports
      remain byte-identical.

      **Honest boundary:** the HMAC proves that a value crossed the host's
      trusted return-channel method and was not proposed by the model policy;
      it does not authenticate the real-world identity of the human. `owner`
      is therefore a runtime attribution label, not identity proof. The demo
      begins from an already parsed symbolic revision and uses a deterministic
      renderer; open-English intent parsing, learned question wording, durable
      session serialization, FrameSpec ownership, visibility filtering, and
      nested beliefs remain later items.

      **Review corrections:** the first pass allowed an already consumed reply
      to solve a publicly reinstated identical need, permitted unsigned action
      dependencies after signing, and called a fresh empty frame an “existing
      story.” The verifier now keeps a private consumed-request ledger (with an
      auditable state mirror), both ASK transitions require empty dependencies,
      and the demo begins from the actual accepted three-beat oracle StoryState.
      Tests prove all three beats and the discharged obligation survive both
      conversation turns and appear in the revised rendering. The three exact
      reproducers are permanent controls.

      Re-review found consumption occurred during speculative verifier
      evaluation, so a goal callback exception could lose a valid answer before
      any accepted state was returned. `Controller.finish` now invokes an
      optional run-level commit hook only after goal/waiting callbacks succeed;
      ASK consumption moves there atomically. The exception-and-retry reproducer
      is the twenty-fifth control.
    - **SHIPPED (first cut) — 10b, physics.frames corpus lane**: velocity addition, acceleration
      invariance, inertial-frame definition, and the rotating frame as a
      scope that suspends an inertia law and admits centrifugal force —
      a fictitious force IS a frame-local invention licensed by
      suspension. Adjudicates P-CF2 (rotating frame lands in one family
      with cartoon_gravity — first evidence scope generalizes beyond
      fiction) and P-CF3 (Galilean addition twins an existing composition
      family). The slice added four nodes (209 → 213) from the MIT 8.01 and
      UVA Galilean references and resolved the frame-id convention: a frame id
      is the statement id of its scoped declaration node, so assertions point
      to a checked owner rather than an opaque near-collision.

      P-CF3 fired exactly at shape and typed levels:
      `physics.frames.galilean_velocity_addition` joined
      `algtop.homology.chain_rank_nullity` on `?0:V = +(?1:V, ?2:V)`.
      P-CF2 missed at every matcher level. That miss is the sharper result:
      rotating-frame scope and cartoon-fiction scope share the executable
      suspension contract, but the matcher reads only templates, and the
      physically honest rotating-frame template is a three-term additive
      correction rather than a temporal response law. Scope generalized in
      the schema/validator, not in signature equivalence. Counts moved
      28/29/28/30/5 → 29/30/29/31/5; specialization 626 → 655, with the
      29 new edges confined to the two additive physics statements.
    - **SHIPPED (first cut) — 10c, frame ownership + visibility-filtered updates**: `owner` on
      FrameSpec (additive schema change), `witnessed_by` on temporal
      events, divergence between an agent's frame and the world *derived*
      from event visibility rather than authored. Sally–Anne as the
      executable demo; adjudicates P-CF1. Nested frames follow later with
      their own leak controls.

      P-CF1 fired: the owner-scoped Sally declaration and unscoped world
      assertion validate with `owner` as the only scope-schema addition, and
      `scripts/theory_of_mind.py` derives Sally→basket while world→box because
      Sally witnesses placement but not movement. Events carry explicit
      removal/addition effects; a missed event id cannot later be replayed with
      forged visibility. Owned frames persist and refuse exit demotion. The
      two LOCATION statements also form one exact typed twin, but that match is
      not evidence for the runtime result. Corpus 213 → 215; suite 158 → 173;
      store 715 → 723. Nested beliefs remain open.

      **Review corrections:** the first event updater superseded only mutable
      assertions, so a declaration-backed basket belief survived a witnessed
      move and `check` verified both old and new locations. FrameState now
      records superseded declaration ids. The same review found assertions
      could introduce an owner absent from the declaration, and positive event
      values erased all same-predicate values even when the predicate was not
      functional. Owner now originates on the declaration; events explicitly
      declare and validate functional predicates. All three reproducers are
      permanent controls. Re-review then found two further fail-closed gaps:
      dependency-free validation treated explicit `owner: null` as absence,
      and one event could contain opposite effects for the same atom. Both are
      rejected at their construction boundaries and retained as controls. A
      final review caught the neighboring case of two positive values for one
      declared functional key; that ambiguity is likewise rejected.
    - **SHIPPED (external first cut) — 10d, WordNet retrieval store**: Open
      English WordNet 2025 JSON (72 MB, external, never in git; loader
      takes a path, feature gracefully absent without it) as a sixth
      store — synonym bridging for request terms, RFT relations at
      lexical scale, renderer variety with zero weight growth. Enters at
      `empirical`, never grounds a frame verdict, never appears in
      verified_by; the retrieval review's laundering controls gain a
      wordnet case before shipping. License recorded in the design doc:
      CC-BY 4.0 (OEWN) + Princeton WordNet license for inherited content;
      ATTRIBUTION file ships with the adapter. P-CF6 fired on eight fixed
      held-out request terms: the five-store control resolved 0/8 and the
      WordNet synonym rung resolved 8/8 to their expected corpus owners, with
      zero frame-verdict changes on the actual verifier path. Safe POINT
      binding is 7/8: `perseverance` reaches the right owner through two
      supporting synsets and is deliberately left unbound pending a sense cue.
      A capability-blind injected frame mutation is detected 8/8. The archive
      remains external; the loader
      indexes 107,519 synsets / 127,311 entry lemmas and records its SHA-256.
      Exact and token-neighborhood corpus retrieval retain precedence;
      ambiguous synonym bridges may be retrieved but cannot POINT-bind. No
      reduced extract ships. Suite 173 → 183.

      **Review correction:** the first binding rule pooled every sense of a
      lemma, and the first zero-verdict experiment compared an untouched frame
      to itself. Binding now requires exactly one supporting synset (bare
      lexical binding requires a monosemous lookup); the adjudicator executes
      RETRIEVE→POINT/REFUSED and must detect the injected mutation. Re-review
      found the ambiguity check could shadow an existing exact project match
      and the evaluator dereferenced missing next-state on a falsified case.
      Project exact/neighborhood ownership now runs first, and misses are
      counted rather than crashing.
    - **10e — masked skeleton modeling** (experiment track, GPU): BERT's
      masked-LM objective transposed to structure — mask a skeleton node,
      recover by pointing. Adjudicates P-CF5 (gains should concentrate in
      depth OOD, not in-distribution, if the objective teaches structure).
    - **10f — provability corpus: SHIPPED.** Six nodes in
      `data/provability` (K, necessitation, Löb, Con(T) := ¬□⊥,
      formalized Gödel II as the hand-authored Löb-at-falsum special
      case, Gödel II as the meta statement); Willard's exception is an
      invariant, not a node (existential content, no binder in the
      grammar). **P-CF4 fired both halves**: no twin at any level and
      `temporal_induction` spans two disciplines in the drift report.
      PV1/PV2/PV4 fired (all six singletons; 215 → 221 nodes with group
      counts frozen at 30/31/30/32/5, zero ladder violations; zero
      mechanical specialization edges, 655 stays 655). **PV3 missed and
      the miss is the finding**: the corpus self-grounds to 1.000 —
      groundedness accepts intra-corpus recurrence and pattern
      absorption as certification, filed in BACKLOG. The companion
      architectural rule — trust roots stay external; nothing
      self-attests — is recorded in the design doc §4, citable in
      review, and now stated by the corpus itself
      (□Con(T) → □⊥). Suite 183 tests green.
    - The RFT coverage table (design doc §3) becomes a living audit,
      re-adjudicated at each release; its one open cell (deixis) is
      closed by 10a+10b+past modalities jointly, not by a bespoke corpus.
