# Backlog

Actionable friction found while working, kept here so it isn't lost in chat
or commit history. Each item names the evidence that motivated it.

## Cognitive frames / lexical stores

The delivered first cuts (frame ownership, visibility-derived and nested
belief, physics frames, WordNet bridging, masked-skeleton pretraining, and the
provability corpus) now live in `docs/RELEASE-v0.5.0.md`. Remaining friction:

- **Unify ASK memory with owned frames.** `retrieval.UserBinding` remains
  session-long and HMAC-attributed while owned `FrameState` has functional-value
  supersession. Define one explicit lifetime and persistence contract before
  longer conversations.
- **Deepen physical reference frames.** Add executable Galilean boosts,
  acceleration invariance, and rotating-frame terms without asserting that
  shared scope semantics imply template equivalence.
- **Traverse WordNet relations safely.** Hypernym, antonym, and entailment
  expansion need sense-level ambiguity, project-exact precedence, announced
  ranking/caps, and the existing empirical-only authority boundary. Renderer
  selection and any seed-regenerated reduced extract remain open.
- **Treat masked pretraining as stabilization, not a wall-mover.** The v0.5
  result narrowed two-seed spread `0.139 → 0.029` but did not support a mean
  lift. The next experiment belongs in recurrent address consumers with at
  least three seeds per arm.
- **Split grounding provenance.** The six-node provability corpus self-grounded
  at 1.000 through same-corpus BOX recurrence and broad pattern absorption.
  Report external/prior, same-corpus, recursive, and pattern channels
  separately before using groundedness as an admission signal.
- **Visual structure lane.** Run the formula–diagram twins experiment in
  `docs/DESIGN-visual-structure.md`: source scene-graph oracle, parsed SVG arm,
  parameter-matched pixel control, and exact geometry verification.

## Frame registry

- **Owned binding lifetime is now explicit at the frame layer, but not yet
  unified with ASK.** Owned FrameState persists until an observed event
  supersedes a functional value; it refuses fiction-style exit/demotion.
  Retrieval `UserBinding` remains session-long and HMAC-attributed. 10c keeps
  that lifetime deliberately because conversation uses it as session memory;
  goal-local or expiring bindings require an explicit future policy and must
  not silently change the current contract.

- **Small filed items from the same review** (nits, no behavior defects):
  `physics.frames.rotating_frame` is governed by
  `narrative.frame.frame_consistency`, whose TITLE says "A Story May Not
  Contradict Its Own Premises" — content is generic, title is not; either
  generalize the title (seed edit, ripples into report/store text) or add
  an invariant note recording the deliberate cross-domain reuse.
  `resolution_channel` on RetrievalNeed is a validated string where the
  house pattern is Enum (Verdict, StopReason) — no laundering path exists,
  consistency only. `commit_run` is duck-typed via getattr rather than an
  optional VerifierAdapter protocol method, and an exception inside it
  would lose a fully-callbacked RunResult — theoretical, but the protocol
  should own the name.

## Retrieval stores

- **The WordNet archive digest is provenance, not tamper-evidence.**
  `WordNetIndex.load` records a per-load SHA-256, but nothing pins it: a
  re-zipped or edited archive loads with a fresh digest and no complaint.
  This is fine under the empirical-only trust model (WordNet records can
  never ground verdicts or enter verified_by), and no doc overclaims it —
  filed so that if lexical records ever gain more authority, digest
  pinning must arrive first. (Post-merge review of 745a46b, informational.)

## Nested frames

- **No graft-back API for nested-model mutation.** `nested()` navigates
  read-only, and `assert_literal`/`plant`/`discharge` on a navigated
  child return a detached state with no path back into the parent; deep
  tests resort to `replace(parent, children=...)` surgery. Events are
  the only real-flow channel that updates models in place. Add a
  `with_nested(parent, owner_path, new_child)` grafting helper (or
  routed variants of the mutators) before any consumer needs to mutate a
  model directly. (Nested-frames review, note 8; the test surgery is the
  evidence.)

## Controller / harness

- **PARTIAL — learned tactic classification works; live ranking does not beat
  the strongest blind order.** The 27,688-parameter byte-GRU has a real
  theorem-level holdout and three-seed controls, scoring 0.8125 against
  frequency 0.4375 and shuffled 0.25–0.375. Live runs take 71/63/61 proposals
  versus 86 for the arbitrary palette, but a state-blind global frequency
  order takes 64; the learned mean is 65.0. P-TP5 records the miss. Only 60 of
  155 extraction rows map to its eight-schema
  vocabulary; the live target is one `Init` theorem; concrete binder and
  projection candidates are supplied symbolically; and no model chooses among
  POINT/RETRIEVE/ASK/WRITE. Expand the atomic extractor, repair native project
  imports, report held-out solved rate over many theorems and fixed budget
  curves, then test the same policy interface on story actions. Do not call
  top-1 schema accuracy a proof-success rate or compare only to arbitrary
  palette order.

- **PARTIAL — live Lean application and branch search ship; learned ranking
  and native project imports remain open.** ``SearchController`` now explores
  verifier-accepted branches under independent node/proposal budgets, and the
  PyPantograph adapter closes one held-out ``Init`` proposition with an
  unranked fixed palette. The projection ablation is exhausted, making the
  tactic capability load-bearing. This is the capability-blind baseline, not
  a tactic-policy result. On native Windows, PyPantograph 0.3.15's project
  loader invokes POSIX ``printenv`` while resolving ``lake env``; the bundled
  ``BooleanLaws`` project therefore fails to populate ``LEAN_PATH`` even
  though base ``Init`` RPC works. Add a Windows path resolver or pass a
  validated explicit Lean path, and reconcile the current 4.29.1 Pantograph
  build with the extraction project's 4.32.2 toolchain before claiming live
  project-backed search.

- **PARTIAL — `verified_by` semantic correspondence remains unchecked node
  metadata; provenance integrity is now validated.** The
  retrieval slice's digest pins Lean artifact BYTES, and its loader checks
  the cited reference exists in the artifact and closes to `no goals` —
  but nothing checks that the theorem PROVES the statement citing it. Any
  committed node could cite `BooleanLaws.modus_ponens` and mint a "proven"
  retrieval record for an unrelated statement (post-merge review of
  5756007, finding F3; mitigated today only by the committed-data trust
  model). The cheap first rung is SHIPPED: `validate_nodes.py` now requires
  repository-contained artifacts whose every row is a complete
  state–tactic–state transition and whose selected theorem reaches `no goals`;
  resolves explicit or
  unambiguous reference-free theorem identities; and gives every theorem
  reference exactly one statement owner. Its capability-blind control pairs a
  valid Boolean theorem with an unrelated gravity statement and correctly
  demonstrates that this lint cannot detect the semantic lie. The remaining
  fix is prover phase 2 regenerating the statement's formal template from the
  Lean theorem and matching skeletons, which turns `verified_by` from
  provenance prose into a checked edge. Until that lands,
  "digest-pinned proof trust" must not be read as semantic correspondence
  (retrieval.py's trust-model docstring now says so).

- **PARTIAL — the common protocol is executable; WRITE remains.**
  `scripts/controller.py` now carries typed state + one of
  `{POINT, GEN, RETRIEVE, ASK, WRITE}` + symbolic verifier result + accepted
  next state + branch trace. The deterministic oracle runs both a three-step
  replay of contiguous machine-extracted Lean transitions and the three-beat
  golden-chicken story through that one controller. It enforces the key
  invariant: REFUTED/UNKNOWN/REFUSED branches cannot mutate accepted state.
  The capability-blind controls reject an unrecorded tactic, a changed Lean
  state, out-of-order story beats, and a frame-trait contradiction. Still open:
  `GEN` has proof/story/frame semantics, and `retrieval.RetrievalVerifier`
  layers executable `RETRIEVE` plus exact `POINT(position)` over the unchanged
  frame verifier. ASK now adds an authenticated pause/return adapter with a
  runtime user frame; `WRITE` remains vocabulary without an adapter. Lean
  replay is not live tactic application or search.

- **Temporal event grounding remains demo-specific.** Chekhov close-time
  obligations and governance-gated no-deus heralding both execute. The
  golden-chicken adapter's visible plant/discharge evidence is still an exact
  case-insensitive substring over oracle-authored prose rather than a general
  semantic event binder. Replace it with corpus-grounded event structure while
  retaining the hidden-ledger, unrelated-mention, order, and idempotence
  controls.

- **Past-mirror payoff exposed two specialization false positives.** The
  intended new edges are `response_pattern -> cartoon_gravity` and
  `heraldry_pattern -> no_deus_ex_machina`, both cost 4. The same run also
  derives `geotop.predicates.de9im_disjoint` as a generalization of
  `strict_part_of_order` and `prev_distributes_over_meet`, both cost 7. The
  graph moved 622 -> 626, but only half the delta is signal. Keep these cases
  in the category-compatibility adjudication rather than counting raw edge
  growth as progress.

- **Recursive-definition grounding is not a blanket 1.000 guarantee.** The
  registered payoff prediction expected SINCE and ONCE unfolding to inherit
  the earlier UNTIL/EVENTUALLY 1.000 results. They instead score 0.667 and
  0.500 because self-headed terms leave other compound constituents in the
  denominator that the current inventory does not recognize. Decide whether
  that is the intended metric or whether definitional grounding should cover
  the entire right-hand construction; preserve these two nodes as controls.

- **One loop across two domains is not yet generalized model weights.** A
  shared controller API can still hide two bespoke policies. After the oracle
  proves the infrastructure, evaluate the claim in explicit rungs: separate
  learned proof/story policies (learnability); one shared policy with thin
  verifier adapters (shared mechanism); held-out structures and greater chain
  depth (composition); then transfer to a third domain such as equation
  derivation or a science problem (cross-domain generalization). Report each
  rung separately. The golden-chicken story is the integration gate, not by
  itself evidence that the model has become a general-purpose solver.

- **PARTIAL — local retrieval initiation and point binding are executable.**
  `demo_answer.py` and solvex-v2
  show that, when a relevant knowledge base is already in context, the pointer
  can use it: held-out combinations reach 1.000 against three distractors, with
  a measured capability-blind floor of 0.31; deeper distractor-bearing inputs
  remain open at 0.69 OOD. `docs/DESIGN-frames-and-retrieval.md` already makes
  UNKNOWN the closed-form trigger for `RETRIEVE(key)`. The local adapter now
  unifies corpus summaries, node lexica, twin/mirror groups, decompositions,
  and proof artifacts into 702 attributable items; exact lookup falls back to
  deterministic token-neighborhood search, results enter immutable indexed
  context, and POINT binds one without promoting its epistemic status only
  when tiered attribution resolves a unique canonical statement owner,
  decomposition owner, or structural-group record. Ambiguous symbols remain
  context, not answers. Empty-
  store and unrelated-query controls remain UNKNOWN with ABSTAIN evidence and
  no mutation. A `frame_local` scope refuses before store access and emits
  `ASK(slot)`. The ASK return channel now ships as item 10a; still open here:
  external tool connectors,
  semantic/ranked neighborhood taste, open-language parsing of a request into
  the literal's canonical target key, learned item selection, and
  evaluation on deeper distractor-bearing stores rather than the deterministic
  oracle.

- **Retrieval is currently a linear scan over a committed snapshot.** The 715
  items are small enough that exact and token-neighborhood lookup need no
  index. Growth will require a regenerated query index with the same coherence
  discipline as reports; otherwise retrieval can silently lag the seeds. Any
  learned or embedding ranker belongs after the exact/neighborhood controls and
  must not replace source attribution or epistemic-status preservation.

- **Retrieval receipts are session-local.** POINT now requires a verifier-
  minted receipt proving which key/mode admitted which item ids. The HMAC key
  is intentionally process-local and signatures cover a random session id, so
  persisted frame state cannot yet resume a pending retrieval after restart. A
  durable session format needs explicit key lifecycle/versioning rather than
  serializing an ambient secret.

- **No model-initiated durable write path.** Durable knowledge is currently
  excellent but human/agent-mediated: edit a seed, regenerate, validate, and
  recompute every symbolic consequence. Add `WRITE(candidate)` as the
  PROVEN-gated dual of UNKNOWN-triggered `RETRIEVE`. The action must stage a
  seed-level authoring candidate carrying `verified_by` and provenance; it must
  never edit generated `data/*/nodes.json`, and it does not bypass review,
  byte-identical regeneration, schema/link validation, or matcher checks.
  VERIFIED-but-unproved material remains a human-curated corpus assertion;
  CONJECTURED material stays in a proposal queue; frame declarations remain
  session-local unless separately proved. This preserves correction-by-edit
  without turning policy output into trusted knowledge.

- **PARTIAL — ASK is executable; open dialogue and durable sessions remain.** An unresolved slot
  can be answerable but absent from every durable store because its source of
  truth is the interlocutor: desired tone, ambiguous referent, private fact, or
  unstated constraint. Define `ASK(slot)` as retrieval from the user for these
  frame-private UNKNOWNs. Its return value must bind the slot in mutable session
  state and resume the same controller branch, which implies a multi-turn frame
  lifecycle rather than a one-shot prompt wrapper. `RetrievalNeed` now marks
  store vs user resolution before policy choice; ASK records a signed question,
  pauses the generic controller as WAITING, and a channel-signed reply resumes
  the same session with a frame-private `UserBinding`. While waiting, every
  non-reply action is frozen. Signatures establish passage through the host
  return-channel API, not real-world human identity. Still open: durable session
  serialization, actual UI/transport integration, open-English parsing,
  learned question rendering, and the deterministic dispatcher across
  derivable/store/user/terminal channels before a learned chooser is evaluated.
  Consumption is verifier-private but commits only through the controller's
  run-level commit hook after completion/waiting callbacks succeed; durable
  restoration must preserve the same atomicity without serializing the secret.

- **PARTIAL — dead branches are traced and pruned; terminal taxonomy remains.**
  The controller records state-before, action, verifier verdict/reason/evidence,
  and state-after for every proposal. A rejected branch leaves state unchanged,
  and the same action at the same state is pruned as REFUSED on repetition;
  tests prove a later valid branch resumes from the pre-rejection state. Still
  open: serializable trace schema, dependency/result references richer than
  strings, and distinct terminal outcomes for contradicted, tool-missed,
  user-deferred, and budget-limited searches. Only independently PROVEN
  conclusions remain eligible for the durable `WRITE` path.

## Parser / matcher

- **No call juxtaposition.** `D(F)(POINT)` fails to parse (`parse_atom`
  returns after the first call). Forced the calculus corpus to reshape the
  chain rule via a `COMPOSE(...)` head. Support `expr(...)` application or
  document the `COMPOSE` convention as canonical.
- **Big-op prefix namespace hazard.** Identifiers starting `sum_ prod_ lim_
  max_ min_` silently become prefix big-operators; and `lim_h` (big-op) vs
  `LIM(...)` (plain call) produce different skeleton heads that can never
  twin. Normalize: lower-case the big-op head AND fold `LIM(` calls into the
  same head, or lint templates for the ambiguity.
- **Specialization matching (v2): SHIPPED** as `scripts/specialize.py`
  (slot-to-subtree absorption + identity-element binding for parameter
  slots, looseness-ranked). The recorded misses now fire: equation of
  exchange >= ideal gas law (absorption over the dimensional constant),
  Cobb-Douglas <= power-law rate (absorption), circumference <= affine
  family (identity). Remaining out of scope: *series-truncation* relations
  (simple interest as the first-order truncation of continuous
  compounding) need rewrite-based reasoning, not matching.
  **v3: SHIPPED** (branch `tooling/cheapest-derivation`): the matcher now
  returns the cheapest derivation rather than the first, so `looseness` has
  the `cost` companion axis the first-success entry below asked for.
- **Specialization noise control.** 236 edges among 67 nodes; looseness
  ranking surfaces tight ones, but variable slots can still bind numeric
  literals (trapezoid >= rectangle-perimeter binds HEIGHT->2). Consider
  category-compatibility constraints on bindings (V slots should not bind
  nums; P slots should not bind V-rooted subtrees).
- **Call args are ordered, so commutative call heads need an authoring
  convention.** `MEET`/`JOIN` are commutative in every model of a Boolean
  lattice, but the matcher flattens/sorts only the `op` heads in
  `COMMUTATIVE = {+, *}`; a `call` keeps its argument order. `MEET(X, TOP)`
  and `MEET(TOP, X)` are therefore different skeletons. The logic/set corpora
  twin only because `scripts/seed_logic.py` generates both from one shared
  format string and fixes the order (distinguished operand first, special
  element second). Fix: let a template declare commutative call heads, or
  lint for the same head appearing with permuted argument categories.
  **SHIPPED** as `HEAD_ALGEBRA` in `scripts/match_signatures.py` (branch
  `tooling/head-algebra`): a declared table of per-head commutativity,
  associativity, identity and annihilator, each entry citing the node that
  justifies it. `canonicalize` and `typed_resort` now sort the arguments of
  declared-commutative call heads (sort only — flattening would need the
  `associative` field, which no pass consumes). Adjudicated: **no twin group
  changed membership at any level**, exactly as predicted, because the
  corpora were authored to the convention the declaration now enforces; four
  nodes' skeleton *strings* reorder (`logic`/`settheory.boolean_laws.identity_laws`
  to `?0:V = MEET⟨?1:P, ?0:V⟩`, `logic.inference.modus_ponens` to
  `IMPLIES⟨MEET⟨?0, IMPLIES⟨?0, ?1⟩⟩, ?1⟩`, and
  `narrative.causality.precedence_causation_bridge` at aliased level). The
  convention is now robust rather than lucky: a future `MEET(TOP, X)` spelling
  lands in the same group as `MEET(X, TOP)`.
- **No binder syntax, so optimizations cannot be compared.** Channel capacity
  is `C = max over p(x) of I(X;Y)`: a maximization over a *family*, with a
  constraint set (the probability simplex). The grammar has identifiers,
  arithmetic, calls, prefix big-ops and relations — no binder — and the one
  spelling that looks natural, `max_p I(X;Y)`, collides with the `max_`
  big-operator namespace above and would silently drop the constraint set
  anyway. `infotheory.channel.channel_capacity` therefore uses an opaque
  `CAPMAX(objective, argument)` call: it parses, it records the dependency,
  and it makes the internal structure of the optimization invisible to the
  matcher. Every argmax/argmin/sup statement anyone adds later will hit this.
  Fix: a `MAX(body, binder, domain)` form (or a real binder node) that the
  canonicalizer treats as a scoped construct.
- **Specialization noise swamps big-op nodes.** All 11 specialization edges
  touching the new information-theory nodes are of the degenerate kind already
  noted under "Specialization noise control": a P slot binds the literal `1`
  and a V slot swallows an entire `sum⟨...⟩` subtree, producing e.g.
  `physics.mechanics.hookes_law >= infotheory.entropy.shannon_entropy` (Hooke's
  law "generalizes" Gibbs/Shannon entropy because `-(k*x)` matches
  `-(anything)`). Zero of the 11 is informative. Category-compatibility
  constraints on bindings, plus a rule that a variable slot may not absorb a
  big-operator subtree, would remove essentially all of them.
- **The genuine specialization we wanted does not fire.**
  `infotheory.entropy.uniform_entropy` (`H = k*LOG(N)`) really is
  `infotheory.entropy.shannon_entropy` (`H = -(k * sum_i p_i*LOG(p_i))`) with
  `p_i = 1/N`, and the same substitution takes Gibbs to Boltzmann's
  `S = kB ln W`. `specialize.py` cannot see it: collapsing a sum under a
  constant summand is a *rewrite* (algebraic simplification), not slot-to-
  subtree absorption. Same class as the recorded series-truncation miss. The
  edge is asserted by hand via `special_case_of`/`generalizes`, which means the
  most pedagogically important specialization in the corpus is the one the
  tooling cannot check.
- **Specialization matcher is arithmetic-only.** `COMMUTATIVE = {+, *}` and
  `IDENTITY = {+: 0, *: 1}` are hardcoded, so `specialize.py` finds *zero*
  edges touching the 18 logic/set_theory nodes even though those nodes
  literally state their own identity elements (`MEET(X, TOP) = X`,
  `JOIN(X, BOT) = X`) and their own annihilators. Generalizing IDENTITY to a
  per-head table sourced from `identity_laws`-style nodes would let e.g.
  De Morgan >= the degenerate one-operand case fire, and would give the
  Boolean corpora any specialization structure at all.
  **SHIPPED** (branch `tooling/head-algebra`): `IDENTITY` is gone, replaced by
  `match_signatures.identity_terms(head)` reading `HEAD_ALGEBRA`, and
  `specialize.py` additionally matches declared-commutative call heads in
  either argument order. The Boolean corpora now have specialization
  structure — four edges, all looseness 0, all cross-corpus in two of the four
  cases: `logic.boolean_laws.absorption >= logic.boolean_laws.idempotence`,
  `>= settheory.boolean_laws.idempotence`, and the two with
  `settheory.boolean_laws.absorption` as the general side, each binding the
  join operand to JOIN's declared identity BOT
  (`MEET(X, JOIN(X, BOT)) = MEET(X, X)`). Not the De Morgan edge the entry
  guessed at, but the same kind and arguably better: idempotence *is*
  absorption at the bottom of the lattice.
- **Discrete and continuous statements of one fact can never twin.** `sum_i X`
  parses to a call with head `sum`; `INTEGRAL(X)` parses to a call with head
  `INTEGRAL`. The two heads are unrelated strings, so the discrete and
  continuous forms of the *same* statement are structurally invisible to each
  other. The differential-geometry corpus produced the sharpest instance
  available: `difftop.vectorfields.poincare_hopf_index_theorem`
  (`EULERCHAR⟨?0:V⟩ = sum⟨?1:V⟩`) and `diffgeo.surfaces.gauss_bonnet_theorem`
  (`INTEGRAL⟨?0:V⟩ = *(?1:P, ?2:V)`) are the two halves of Chern's theorem —
  one theorem, proved from the other — and they share not one node. Same
  obstacle blocks probability normalization (`sum_i p_i = 1` vs
  `INTEGRAL(density) = 1`), every expectation, and every conservation law in
  the graph, all of which have both forms. This is bigger than the `lim_h` vs
  `LIM(...)` split already recorded above and has the same fix shape: a
  head-aliasing table (`sum` ~ `INTEGRAL` ~ `prod`, as accumulation operators)
  applied at a match level below `typed`, or an explicit `ACCUMULATE(...)`
  authoring convention that both forms adopt.
  **HALF SHIPPED** (branch `tooling/head-algebra`): `{"sum": "aggregate",
  "INTEGRAL": "aggregate"}` is now in `HEAD_ALIASES`, so the two heads *do*
  share a node at the ALIASED level. `prod` is deliberately not included — it
  is not linear aggregation, and no node in `data/` carries it. Adjudicated:
  **zero new twin groups.** All 23 sum/INTEGRAL-bearing nodes were rechecked;
  the four aliased groups containing `aggregate` are all pre-existing typed
  groups (weighted accumulation ×4, Shannon/Gibbs, cross-entropy ×2,
  FTC/Stokes-zero-form), none of which crosses the discrete/continuous divide.
  The alias removes one obstacle and reveals what was behind it: the three
  nodes whose right side is a bare `aggregate⟨?:V⟩` —
  `diffgeo.curves.arc_length_functional` (`?0:V = aggregate⟨?1:V⟩`),
  `difftop.degree.degree_regular_value_count` (`DEGREE⟨?0:V⟩ = aggregate⟨?1:V⟩`)
  and `difftop.vectorfields.poincare_hopf_index_theorem`
  (`EULERCHAR⟨?0:V⟩ = aggregate⟨?1:V⟩`) — are now separated *only* by whether
  the left side is a slot or a call, i.e. by the "same invariant, slot in one
  corpus and call head in another" entry in the Schema section. That entry was
  one obstacle among three for one pair; it is now the sole remaining obstacle
  for three pairs, and should be promoted accordingly. (The entry's other
  prediction, probability normalization, is untestable: `data/` has
  `sum_i p_i = 1` but no `INTEGRAL(density) = 1`.)
- **Three independent obstacles stacked on one pair.** Worth recording as a
  unit because fixing any one of them would not have made Gauss-Bonnet meet
  Poincaré-Hopf: (1) the `sum`/`INTEGRAL` head split above; (2) the Euler
  characteristic is a *slot* in Gauss-Bonnet and a *call head* in
  differential topology (see the Schema section); (3) Gauss-Bonnet carries an
  explicit `2*pi` normalization that the already-integer index sum does not, so
  even after (1) and (2) the arities differ. Any head-aliasing work should be
  tested against this pair, not against a single-obstacle example.
  **TESTED, one of three cleared** (branch `tooling/head-algebra`). After the
  `sum`/`INTEGRAL` alias the pair reads:
  - `difftop.vectorfields.poincare_hopf_index_theorem`:
    `EULERCHAR⟨?0:V⟩ = aggregate⟨?1:V⟩`
  - `diffgeo.surfaces.gauss_bonnet_theorem`: `aggregate⟨?0:V⟩ = *(?1:P, ?2:V)`

  Obstacle (1) is gone — both now carry `aggregate`. Obstacle (2) is intact:
  the Euler characteristic is the call head on one side and the `?2:V` slot on
  the other. Obstacle (3) is intact: the `2*pi` shows as an extra `*(?1:P, …)`
  against a bare aggregate. The pair remains blocked at every level, and the
  entry's warning was correct — a single-obstacle test (the ML
  `ACTIVATION`/`SIGMOID` pair, the morphology near-misses) would have declared
  head aliasing a success on the strength of a case it does not resolve.
- **A numeric literal in a slot position blocks an otherwise real match.**
  `diffgeo.curves.circle_curvature` is `CURVATURE = 1 / RADIUS` ->
  `?0:V = *(1, inv(?1:V))`, and the rate/density family (average rate of
  change, average speed, mass density, molarity) is
  `?0:V = *(?1:V, inv(?2:V))`. Curvature really is a density — turning per
  unit length — whose numerator has been normalized to 1, but the literal is
  not a slot and the arities differ, so nothing fires at shape, typed or
  family level. Authoring around it (inventing a `UNITLENGTH` numerator slot)
  would be a lie. Fix candidate: a match level in which a numeric literal may
  bind a parameter-like slot, which is the dual of the existing sign-absorption
  level; it should be reported separately from `typed` since it is strictly
  looser.
- **Wanted match level: slot recurrence, not slot shape.**
  `difftop.degree.brouwer_fixed_point` (`?0:V = SELFMAP⟨?0:V⟩`),
  `logic.boolean_laws.double_negation` (`?0 = NEG⟨NEG⟨?0⟩⟩`),
  `settheory.boolean_laws.idempotence` (`?0 = MEET⟨?0, ?0⟩`) and
  `calculus.integration.ftc_differentiation_part` (`?0 = D⟨INTEGRAL⟨?0⟩⟩`) are
  all "an operation that returns its argument" — fixed points, idempotents,
  involutions, left inverses — and no two of them twin, because they differ in
  arity and nesting depth. The family is defined by a *property* of the
  skeleton (one slot occurring on both sides of the relation at different
  depths) rather than by the skeleton itself, so twin detection cannot express
  it. Wanted: a structural *query* facility ("templates where slot S occurs on
  both sides of the relation") alongside the equality-based twin grouping.
- **Notation adoption is manual, and the corpus should say so out loud.**
  `diffgeo.stokes.stokes_theorem`
  (`INTEGRAL(D(FORM)) = BOUNDARYINTEGRAL(FORM)`) is the statement a geometer
  writes and it twins with nothing.
  `diffgeo.stokes.stokes_zero_form_case`
  (`INTEGRAL(D(F)) = F(ENDPOINT) - F(STARTPOINT)`) states the k=0 case in
  `calculus.integration.ftc_evaluation_part`'s own vocabulary and twins with it
  exactly. Both are honest; the difference is that an author who already knew
  the answer spelled the second one to match. Same pattern as
  `infotheory.mutualinfo.entropy_inclusion_exclusion` adopting CARD/MEET/JOIN.
  Two twin groups in the graph now exist because of hand translation rather
  than discovery, which is a real limit on any claim that the matcher *finds*
  cross-discipline structure. Worth a provenance flag on twin groups
  (`authored_to_match` vs `emergent`) so the ledger can report the two counts
  separately; `diffgeo.surfaces.gaussian_curvature_principal_product` joining
  `geometry.area_formulas.rectangle_area_formula` was emergent and should not
  be pooled with the two adopted ones.
- **Specialization noise now reaches nonsense.** The new corpora add edges like
  `chemistry.spectroscopy.beer_lambert_law >= diffgeo.surfaces.gauss_bonnet_theorem`
  (looseness 1, via identity) and
  `geometry.area_formulas.triangle_area_formula >= diffgeo.surfaces.gaussian_curvature_principal_product`.
  Beer-Lambert does not generalize Gauss-Bonnet. Same root cause as the
  entries above under "Specialization noise control" — variable slots absorbing
  arbitrary subtrees and parameter slots binding literals — and another vote
  for category-compatibility constraints on bindings.

- **Call heads are literal at every match level, so a new discipline's
  vocabulary is structurally quarantined.** `data/morphology` (10 nodes) fires
  **zero** twin groups at shape, typed *and* family level, and **zero**
  specialization edges (247 edges among 106 nodes, none touching it) — yet four
  of its skeletons are character-for-character an existing skeleton apart from
  one head string:

  | morphology | existing / predicted |
  |---|---|
  | `?0:V = CONCAT⟨?0:V, ?1:P⟩` (zero morpheme) | `?0:V = MEET⟨?0:V, ?1:P⟩` (logic + set identity laws) |
  | `?0:V = CONCAT⟨CONCAT⟨?1:V, ?2:V⟩, ?3:V⟩` (iterated affixation) | `?0:V = MOD⟨MOD⟨?1:V, ?2:V⟩, ?3:V⟩` (intensifier nesting, `docs/DESIGN-linguistic-twins.md`, not yet authored) |
  | `CATEGORY⟨?0:V⟩ = CATEGORY⟨CONCAT⟨?1:V, ?0:V⟩⟩` | `FEAT⟨?0:V⟩ = FEAT⟨CONCAT⟨?1:V, ?0:V⟩⟩` (both morphology; one theorem, Williams's Righthand Head Rule) |
  | `?0:V = CONCAT⟨?1:V, ?2:V⟩` (affixation) | `?0:V = REALIZE⟨?1:V, ?2:V⟩`, `?0:V = CAPMAX⟨?1:V, ?2:V⟩` |

  `seed_infotheory.py` escaped this by *adopting* the CARD/MEET/JOIN heads.
  Morphology cannot: adopting `MEET` for concatenation would assert
  commutativity and idempotence, which are false of words (`re-do` is not
  `do-re`). So faithful authoring alone cannot produce a twin, and the corpus
  most likely to need a new vocabulary is the one least able to match. Fix: a
  declared head-alias table (`CONCAT ~ MEET ~ MOD` as "opaque binary
  composition"), or a fourth match level below `shape` that erases call-head
  identity the way `shape` erases slot identity — reported separately so it
  cannot be mistaken for a typed twin.
- **`archetype_id` is currently the only cross-head channel, and it is filed as
  a lint.** `archetype_label_drift` now reports `identity_element_law` spanning
  `logic.boolean_laws.identity_laws`,
  `settheory.boolean_laws.identity_laws` and
  `morphology.wordformation.zero_morpheme_identity` — the hand-assigned label
  says one law, the skeletons say three, and the label is right.
  `morphology.derivation.category_from_affix` and
  `morphology.agreement.feature_percolation` share
  `right_hand_head_projection` for the same reason. Both entries are
  deliberate. Fix: promote "same archetype_id, skeletons differing only by call
  heads" from a drift warning to a *proposed head alias* output, which turns
  the lint into the discovery channel the previous item asks for.
  New strongest evidence (provability corpus, P-CF4):
  `provability.modal.loeb_axiom` adopts `temporal_induction` — argued, not
  convenient: Löb is well-founded induction along GL's accessibility
  relation (Segerberg), temporal induction is the same principle along
  successor — so a *discipline-named* label now spans a second discipline.
  The drift report is the only channel that carries the relationship (the
  skeletons cannot twin: BOX vs ALWAYS/NEXT heads, and the trees differ in
  exactly the reflection GL forbids). The label itself is now demonstrably
  too narrow for its extension; the promotion fix should also consider a
  rename pass for discipline-named archetype ids.
- **Per-head identity elements: third motivated head, and a new wrinkle.**
  `IDENTITY = {"+": 0, "*": 1}` in `specialize.py` is still arithmetic-only
  (recorded above for logic/set_theory). `morphology.wordformation.zero_morpheme_identity`
  states `CONCAT(STEM, EMPTY) = STEM`, so CONCAT is a third head declaring its
  own identity and getting nothing for it. The wrinkle morphology adds: the
  slot that should bind the identity is **variable-like**, not parameter-like —
  a zero morph *is* a morph, filling an affix slot with the empty string
  (`sheep` = sheep + ∅). The current rule ("variable-like slots may not
  vanish: a law does not lose its variables") is exactly what blocks the one
  edge worth having here, `iterated_affixation >= affixation` via
  `SUFFIX2 -> EMPTY`. Fix needs both parts: a per-head identity table sourced
  from identity-law nodes, and permission for a variable slot to bind an
  identity element *for a head whose identity the corpus has declared*.
  **SHIPPED** (branch `tooling/head-algebra`), both parts, and the predicted
  edge fires:
  `morphology.wordformation.iterated_affixation >= affixation`, looseness 0,
  via `SUFFIX1 -> EMPTY` — the *inner* affix vanishes rather than the outer
  one this entry guessed, which is the same law read the other way round
  (`CONCAT(CONCAT(STEM, ∅), SUFFIX) = CONCAT(STEM, SUFFIX)`) and puts the zero
  morph where a linguist would, between stem and suffix. Two more morphology
  edges came with it: `iterated_affixation >= zero_morpheme_identity` (both
  affixes empty) and `concat_associativity >= zero_morpheme_identity`. The
  mechanism is `match_via_head_identity`: a call whose vanishing argument is a
  slot collapses to its other argument. Note it is NOT the "arguments run out"
  rule generalized — a call has fixed arity, so the collapse is a rewrite of
  the pattern, and it needs its own non-triviality guard (below).
- **Associativity and commutativity are one package in the canonicalizer.**
  `COMMUTATIVE = {+, *}` gets flattening (associativity) and sorting
  (commutativity) together, and call heads get neither.
  `morphology.wordformation.concat_associativity` is the corpus's first
  associative-but-not-commutative operation, so `CONCAT(CONCAT(A,B),C)` and
  `CONCAT(A,CONCAT(B,C))` are different skeletons even though the node asserts
  they are the same string. Fix: let a template declare a call head associative
  (flatten only) independently of commutative (flatten and sort). CONCAT must
  never be added to `COMMUTATIVE`.
  **HALF SHIPPED** (branch `tooling/head-algebra`): `HEAD_ALGEBRA` separates
  the two declarations — `CONCAT` is `associative: True, commutative: False`,
  cited to `morphology.wordformation.concat_associativity` and to the corpus's
  own `re-do` is not `do-re` note — and `COMMUTATIVE` /
  `COMMUTATIVE_CALL_HEADS` are now *derived* from the table rather than
  hardcoded, so CONCAT cannot be added to `COMMUTATIVE` by accident. What is
  **not** shipped is a consumer: no pass reads `associative`, so
  `CONCAT(CONCAT(A,B),C)` and `CONCAT(A,CONCAT(B,C))` are still different
  skeletons. The remaining work needs a decision the commutative case did not:
  a flattened n-ary `CONCAT` has no spelling in the grammar, so either the
  skeleton renderer gains a variadic form or the canonicalizer
  right-associates instead of flattening.
- **`specialize.py` suppresses the plainest specializations of all.** Its
  filter is `if match(...) and (st.used_absorption or st.used_identity)`,
  justified in the docstring by "anything matchable without them is an exact
  twin and already in the skeleton report". That justification is false: two
  templates can match by *plain slot binding* and still have different
  skeletons, so they are in neither report. The topology corpora hit it twice
  in one seeding pass, both times on the relation the corpus most wanted:
  - `algtop.invariants.euler_characteristic_complex`
    (`EULERCHAR = VERTICES - EDGES + FACES`) covers
    `geotop.polyhedra.euler_polyhedron_formula` (`VERTICES - EDGES + FACES =
    2`) by binding `EULERCHAR -> 2`. Probed directly: `MATCHES = True,
    used_absorption = False, used_identity = False`.
  - `geotop.predicates.de9im_disjoint` (`MEET(REGA, REGB) = EMPTYSET`) covers
    `settheory.boolean_laws.complement_laws` (`MEET(SETA, NEG(SETA)) =
    FALSITY`) by binding `REGB -> NEG(SETA)`. Same probe result.
  A slot binding a numeric literal, and a slot binding a subtree with a call
  head, are the two commonest ways a general law becomes a special case, and
  both are dropped. Fix: report matches whose bindings are non-trivial (any
  slot bound to a `num`, or to a subtree of depth >= 1) even when neither
  absorption nor identity fired, and rank them by the same looseness score.
  Both edges are currently asserted by hand via `special_case_of` /
  `generalizes`.
- **Specialization noise, third confirmation.** All 16 specialization edges
  touching the 15 topology nodes are degenerate: `betti_number_rank`
  (`BETTI = CYCLERANK - BOUNDARYRANK`) "generalizes"
  `settheory.cardinality.inclusion_exclusion_two_sets` because a variable slot
  swallows a whole `CARD⟨...⟩` subtree. Zero are informative — the same
  outcome the information-theory corpus recorded. The proposed
  category-compatibility constraint on bindings is now supported by three
  independent corpora and should be considered load-bearing rather than nice
  to have.
- **No way to declare a call head commutative, so symmetry must be a node.**
  `geotop.predicates.adjacency_symmetry` exists only because
  `TOUCHES(A, B)` and `TOUCHES(B, A)` are different subtrees, and the corpus
  has no other way to say the head is symmetric. That is the same limitation
  already recorded above for `MEET`/`JOIN`, but seen from the other side:
  every Boolean-corpus node silently *assumes* commutativity of its head, and
  this is the first node in `data/` that *asserts* it. If a commutative-head
  declaration is added, this node is the test case for it.
  **SHIPPED** (branch `tooling/head-algebra`): `TOUCHES` is declared
  commutative in `HEAD_ALGEBRA` with this node as its cited justification —
  the only ASSERTED commutativity in the table, everything else being DERIVED
  or CONVENTION. Adjudicated against the test case, with a result worth
  keeping: **the node's own skeleton does not change**. Sorting uses
  `shape_key`, which erases slot identity, so `TOUCHES⟨?0, ?1⟩` and
  `TOUCHES⟨?1, ?0⟩` have equal sort keys and the stable sort leaves both
  alone. Declaring a head commutative therefore does *not* collapse a symmetry
  statement into a tautology, which is the desirable outcome (the node still
  says something) but also means this test case cannot demonstrate the
  feature. A head whose arguments differ in *shape* is what the sort acts on;
  `logic.inference.modus_ponens` is the only node in `data/` that supplies one.
- **The one relation nested inside a call argument matches nothing.**
  `geotop.measure.area_monotonicity` is
  `IMPLIES(LEQ(REGA, REGB), CARD(REGA) <= CARD(REGB))` — an order-preservation
  claim, with a lattice order in the premise and a numeric order in the
  conclusion. It parses cleanly (`parse_args` calls `parse_relation`), but it
  is the only such statement in the graph, so there is nothing to twin with.
  Not a bug; recorded so that a future monotone-functional node (entropy is
  monotone under coarsening, cardinality under inclusion, measure under
  containment) is written with *this* template rather than a fresh one.

- **Five heads now share the two-argument opaque-composition shape and none
  of them twin.** `?0 = HEAD⟨?1, ?2⟩` is carried by
  `morphology.wordformation.affixation` (CONCAT),
  `morphology.inflection.paradigm_realization` (REALIZE),
  `infotheory.channel.channel_capacity` (CAPMAX),
  `geotop.predicates.de9im_disjoint` (MEET) and
  `ml.recurrence.belief_state_update` (UPDATE). Five nodes, five heads, zero
  groups at shape, typed or family level. This is the cheapest available
  measurement of what head literalism costs, and it grows by one every time a
  corpus needs a vocabulary the graph does not already have.
- **Head literalism, now with a minimal reproducer inside one file.** The
  morphology entry above argues from four near-misses across corpus
  boundaries. `data/machine_learning` supplies the smallest possible case:
  `ml.recurrence.elman_rnn_hidden_state` is
  `?0:V = ACTIVATION⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` and
  `ml.recurrence.lstm_gate_activation` is
  `?0:V = SIGMOID⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` — the same string
  apart from one head token, authored by one hand in one file with no intent
  to hide the relationship — and they share no group at shape, typed *or*
  family level. `shape` is documented as the loosest level and it still
  cannot see a one-token difference. Any head-alias mechanism should be
  tested against this pair before the harder morphology ones.
- **A call head quarantines everything under it, including the corpus's
  largest family.** The argument of that `ACTIVATION(...)` is an affine map,
  and the affine family (`?0:V = +(?1:P, *(?2:P, ?3:V))`, five members across
  four disciplines) is the best-populated group in the graph. Nothing
  relates them. Worth separating from the head-alias item because *two*
  fixes are needed and neither suffices alone: erasing head identity would
  still leave the pre-activation as *multiple* linear regression (two
  weighted regressors) against a corpus that carries only the simple
  one-regressor form, so the arities differ as well.
- **No `min`, no `clip`, no piecewise form — the PPO ceiling.** Extends the
  "no binder syntax" entry above with a second family of missing constructs.
  `ml.policy.ppo_clipped_surrogate` needs a binary minimum and an interval
  clamp; the grammar has neither, and the natural spelling for the first
  collides with the `min_` big-operator namespace already recorded. Both are
  written as opaque calls (`MINOF`, `CLIPCALL`), which parse and record
  dependencies while hiding the entire mechanism — the clamp's flat gradient
  outside the trust region is what the method *is*. Consequence: the node is
  a singleton at every level and cannot be compared with TRPO's constrained
  form or any other trust-region method. Also: `MINOF` is commutative in
  every model and the matcher cannot know it, the same ordered-call-args
  problem `MEET`/`JOIN` and `TOUCHES` already have.
- **`*` means two different operations and the canonicalizer picks one.**
  `COMMUTATIVE = {+, *}` gets flattening *and* sorting, so `*` can only
  denote a commutative product. Machine learning needs it for matrix-vector
  application and for outer products, neither of which commutes.
  `ml.recurrence.linear_ssm_state_update` escapes only because S4D and Mamba
  use a *diagonal* state matrix, making the per-channel recurrence genuinely
  scalar; `ml.recurrence.mlstm_matrix_memory_update` cannot escape, since
  `v k^T` is irreducibly a rank-one matrix, and had to introduce an
  `OUTER(.,.)` head. That extra node is one of the two reasons the two
  state-update equations do not twin. Related to the CONCAT associativity
  entry above but distinct: there the head had no algebra declared, here the
  head has the *wrong* algebra declared. Fix shape: a non-commutative
  multiplication head, or a per-head associativity/commutativity table that
  `*` itself participates in.
  **PARTIALLY ADDRESSED** (branch `tooling/head-algebra`): the table exists and
  `*` participates in it — `HEAD_ALGEBRA["*"]` is now the source of truth for
  `COMMUTATIVE`, and its comment records the over-declaration by name
  (`OUTER`, `CROSS`). It is still declared commutative, because ~30 scalar
  products carrying the affine and rate families need it that way and nothing
  lets a single template opt out. So the *cost* is now written next to the
  declaration instead of only in this file, and the fix is unchanged: a second
  multiplication head, or per-node algebra overrides. `CROSS`'s antisymmetry
  stays inexpressible — the table carries boolean commutativity only, and
  inventing a third value for one node would declare more than `data/`
  justifies.
- **`specialize.py` plain-binding suppression, fourth instance, and the one
  the node most wanted.** `infotheory.entropy.surprisal`
  (`?0:V = neg(LOG⟨?1:V⟩)`) covers `ml.preference.dpo_preference_loss`
  (`?0:V = neg(LOG⟨SIGMOID⟨*(?1:P, +(?2:V, neg(?3:V)))⟩⟩)`) by binding the
  argument slot to the `SIGMOID⟨...⟩` subtree — and the relation is exact,
  since SIGMOID's output is the Bradley-Terry probability that the annotator
  preferred the chosen completion, so the DPO loss *is* the surprisal of the
  observed preference. Neither absorption nor identity fires, so the filter
  drops it, exactly as recorded for the two topology cases. Three corpora
  have now lost their headline specialization to this one filter.
- **Specialization noise, fourth confirmation, and now it reaches training
  objectives.** Of 47 specialization edges touching the 14 machine-learning
  nodes, the informative ones are three:
  `probstat.regression.slr_stochastic_specification >= linear_ssm_state_update`
  (intercept to 0, noise slot absorbing the autoregressive term — an AR(1)
  process is the regression of a series on its own past),
  `probstat.transform.affine_location_scale >= lora_low_rank_update`, and
  `boltzmann_softmax_policy >= chemistry.kinetics.arrhenius_equation`. The
  rest are the known degenerate kind:
  `physics.mechanics.hookes_law >= ml.objective.token_cross_entropy_loss`
  (Hooke's law "generalizes" the training loss of a language model, because
  `-(k*x)` matches `-(anything)`),
  `chemistry.spectroscopy.beer_lambert_law >= grpo_group_relative_advantage`,
  `geometry.area_formulas.triangle_area_formula >= boltzmann_softmax_policy`,
  `physics.mechanics.newton_second_law >= policy_probability_ratio`. Same
  root cause, same proposed fix (category-compatibility constraints on
  bindings, plus a rule that a variable slot may not absorb a call-rooted
  subtree), now supported by four independent corpora.
- **Two deliberate `skeletons_with_split_archetypes` entries.**
  `?0 = *(?1, EXP⟨neg(*(?2, ?3))⟩)` now spans `exponential_decay` and
  `normalized_exponential_tilt`, and `?0 = +(?1, neg(*(?2, ?3)))` spans four
  labels including `state_minus_scaled_correction` (gradient descent) and
  `value_minus_weighted_penalty` (the RLHF objective). Both are intentional:
  the skeletons are shared and the statements are not the same statement.
  `ml.policy.policy_probability_ratio` went the other way and adopted the
  existing `ratio_rate` label rather than minting one. Recorded because the
  lint cannot currently distinguish "same structure, genuinely different
  claim" from "same claim, drifting label", and this corpus deliberately
  produced both.

- **A numeric literal in a multiplicative position, third and fourth
  confirmations — and the specialization matcher already fixes half of it.**
  docs/BACKLOG.md records `diffgeo.curves.circle_curvature` (`1 / RADIUS`)
  being kept out of the rate/density family by a literal `1`. The
  numerical-analysis and graph-theory corpora hit the same wall twice more,
  from the other side: `graphtheory.degree.average_degree_from_edge_count`
  (`?0:V = *(2, ?1:V, inv(?2:V))`) versus the seven-member rate family
  (`?0:V = *(?1:V, inv(?2:V))`), and
  `numanalysis.rootfinding.bisection_interval_halving`
  (`?0:V = *(?1:V, inv(2))`) versus the same family with the literal in the
  denominator. The new information is that `specialize.py` **does** recover the
  first one — `calculus.differentiation.average_rate_of_change >=
  average_degree_from_edge_count` via absorption, binding
  `QUANTITY -> *(2, EDGES)`, and likewise from molarity — so the relation is
  reachable, just not as a twin. That is now a repeatable pattern worth naming
  in its own right (a twin-level miss recovered one level down, first recorded
  for the ML state-space update), and it argues the wanted "numeric literal may
  bind a parameter-like slot" match level should be specified as a *twin*
  level, since the specialization level already covers the case where the
  literal can be absorbed into a variable slot but not the case where it must
  bind a parameter slot (bisection).
- **`decompose.py` sees three relations the twin matcher structurally cannot,
  and the pattern is predictable.** All three come from one cause: decompose
  compares *expression sides*, so it is blind to the relation symbol and to
  slot recurrence across the relation. Instances from this seeding pass:
  1. `numanalysis.floatingpoint.machine_epsilon_bound`
     (`ROUNDOFF <= UNITROUNDOFF*EXACT`) is a whole-statement singleton purely
     because of the `<=`; decompose reports its right side as `*(?0:P, ?1:V)`,
     the expression side of Ohm's law, Newton's second law and circle
     circumference, recurring in 35 statements. Every error bound anyone adds
     will be isolated at twin level and connected at decomposition level.
  2. `numanalysis.rootfinding.fixed_point_iteration`
     (`?0:V = SELFMAP⟨?1:V⟩`) does not twin
     `difftop.degree.brouwer_fixed_point` (`?0:V = SELFMAP⟨?0:V⟩`) because of
     slot recurrence — but decompose reports its expression side as *being*
     Brouwer's expression side, since on one side of the relation the
     recurrence is invisible. The two tools disagree, both correctly, about
     the same pair.
  3. `numanalysis.rootfinding.newton_iteration` misses the whole
     iteration/update family over one `inv` node, and decompose finds its
     correction term `*(?0:V, inv(?1:V))` is the rate/density family's
     expression side (11 statements) — i.e. a Newton correction is a rate.
  Proposal: rather than three more match levels, have `match_signatures.py`
  cross-reference `decompose.py`'s side-forms and report "singleton at every
  level, but its expression side is a known form shared with N statements" as
  a fourth report section. It costs nothing new and it would have caught all
  three of these automatically.
- **Head literalism: the two-argument opaque-composition count reaches seven,
  two of them added in one pass.** `?0 = HEAD⟨?1, ?2⟩` is now carried by
  `morphology.wordformation.affixation` (CONCAT),
  `morphology.inflection.paradigm_realization` (REALIZE),
  `infotheory.channel.channel_capacity` (CAPMAX),
  `geotop.predicates.de9im_disjoint` (MEET),
  `ml.recurrence.belief_state_update` (UPDATE),
  `graphtheory.walks.adjacency_power_walk_count` (MATRIXPOWER) and
  `geomodel.surfaces.surface_normal_cross_product` (CROSS). Seven nodes, seven
  heads, zero groups at any level. The two new ones sharpen the diagnosis: both
  exist *because `*` is hardcoded commutative*. MATRIXPOWER cannot use `^`
  because matrix multiplication does not commute; CROSS cannot use `*` because
  it ANTI-commutes. This is the same root cause as
  `ml.recurrence.mlstm_matrix_memory_update`'s OUTER, and it means the
  per-head associativity/commutativity table already requested for CONCAT is
  now blocking four nodes in three corpora, not one. CROSS additionally needs
  a value the table cannot currently express (antisymmetric), and the cost is
  concrete: the cross product's magnitude is a rectangle area, and
  `?0:V = *(?1:V, ?2:V)` is a three-discipline group in the same graph.
- **Two inequalities, opposite in kind, indistinguishable to the matcher.**
  `numanalysis.floatingpoint.machine_epsilon_bound` (never attained, a
  guarantee) and `graphtheory.planarity.planar_edge_bound` (attained by every
  maximal planar graph, an extremal identity in disguise) are both singletons
  for the same mechanical reason — the relation symbol is part of the skeleton
  — and the graph has no way to say that the second is an equality on a
  subfamily while the first is not. Related to but distinct from the
  `geotop.measure.area_monotonicity` entry above: that one is isolated for
  being the only *nested* relation, these two for being non-`=` at top level.
  Wanted: a flag or slot-schema note distinguishing tight/attained bounds from
  loose ones, so an extremal statement can eventually be related to the
  equality case it saturates.

- **`specialize.py` cannot use a non-equation as a general pattern, so every
  inference rule in the graph is excluded from the general side.**
  `find_specializations` opens with `if gtree[0] != "rel": continue`, which
  silently drops any node whose canonical template is a bare call rather than a
  relation. That is **16 of 195 nodes**: `logic.inference.modus_ponens`,
  `logic.inference.ex_falso_quodlibet`, `logic.inference.reductio_ad_absurdum`,
  `settheory.order.subset_transitivity`,
  `settheory.order.empty_set_minimality`,
  `geotop.predicates.containment_transitivity`,
  `geotop.predicates.adjacency_symmetry`, `geotop.measure.area_monotonicity`,
  `algtop.homotopy.homotopy_invariance` and the seven rule-shaped nodes in
  `data/temporal_logic` / `data/narrative`. Concrete cost, and the case that
  found it: `temporal.response.response_pattern`
  (`ALWAYS(IMPLIES(TRIGGER, EVENTUALLY(RESPONSE)))`) covers
  `narrative.constraint.chekhov_gun`
  (`ALWAYS(IMPLIES(PLANTED(ELEMENT), EVENTUALLY(DISCHARGED(ELEMENT))))`) by
  binding `TRIGGER -> PLANTED(ELEMENT)`, `RESPONSE -> DISCHARGED(ELEMENT)`.
  Probed directly: `MATCHES = True, used_absorption = False,
  used_identity = False`. Two filters stacked — this one first, then the
  plain-binding suppression already recorded five times — so Chekhov's gun
  being an instance of an LTL liveness pattern has to be asserted by hand.
  Fix: drop the `rel` guard and gate on `op_count` alone (the guard's stated
  purpose, avoiding near-trivial patterns, is already served by
  `op_count(gtree) < 2`).
- **`decompose.py` rates a recursive definition as maximally ungrounded, which
  breaks the epistemic ladder's one graded rung: SHIPPED** (groundedness v2).
  `decompose.py` now detects a *definiendum* — a bare application of a named
  head to leaves whose head recurs, under a different head, on the other side
  of the relation — marks the statement `"recursive": true`, and drops its
  self-headed constituents from the DENOMINATOR rather than failing them.
  Measured: `temporal.recurrence.until_unfolding` **0.000 -> 1.000** (2
  `UNTIL⟨?1, ?0⟩` constituents excluded as definitional; the remaining
  `JOIN⟨...⟩`, `MEET⟨...⟩`, `NEXT⟨...⟩` all ground),
  `temporal.modality.eventually_unfolding` **0.500 -> 1.000**. Those two are
  the only nodes in the 197 the detector fires on, which took three guards to
  achieve — each was measured firing wrongly first: without a `call`-only
  restriction the Pythagorean theorem "defines" `^` and the ideal gas law
  "defines" `*`; without requiring the other side's root head to differ,
  `ALWAYS(ALWAYS(P)) = ALWAYS(P)`, `CATEGORY(CONCAT(STEM, AFFIX)) =
  CATEGORY(STEM)` and contraposition all read as definitions of their own head
  and had their denominators emptied to nothing, scoring 1.000 by vacuity. The
  loose version inflated the corpus mean to 0.862 on 13 spurious "recursive"
  nodes. Honest caveat: this fix *alone* would have dropped
  `eventually_unfolding` 0.500 -> 0.000, because excluding `EVENTUALLY⟨?0⟩`
  removes its one recognized constituent from the numerator too; it is only
  safe together with the pattern-membership fix below, and the two shipped
  together.
  Original report: `temporal.recurrence.until_unfolding`
  (`UNTIL(PROPA, PROPB) = JOIN(PROPB, MEET(PROPA, NEXT(UNTIL(PROPA, PROPB))))`)
  scores **groundedness 0.000** — the lowest of the seventeen nodes in that
  seeding pass, on an axiom of a fifty-year-old logic. Cause: all five of its
  non-trivial constituents contain `UNTIL`, the head being defined
  (`JOIN⟨?0, MEET⟨?1, NEXT⟨UNTIL⟨?1, ?0⟩⟩⟩⟩`, `MEET⟨?1, NEXT⟨UNTIL⟨?1, ?0⟩⟩⟩`,
  `NEXT⟨UNTIL⟨?1, ?0⟩⟩`, `UNTIL⟨?1, ?0⟩` twice), and the form inventory is
  built from *other* statements, where the head does not occur. Its Boolean
  neighbour `temporal.modality.next_distributes_over_meet` scores 0.600 with
  its `MEET⟨?0:V, ?1:V⟩` constituent recognized in 10 statements, so the
  contrast is internal to one corpus. Per `docs/DESIGN-epistemic-ladder.md`
  groundedness grades the UNGROUNDED rung, so a correct axiom currently lands
  where near-gibberish lands, and every recursive definition anyone adds
  (factorial, Fibonacci, a grammar production, the mu-calculus fragment) will
  land there too. Fix: while decomposing a statement, treat that statement's
  own root head as a known form.
- **Groundedness measures vocabulary overlap, so a new discipline's first
  corpus is guaranteed to grade as disorder.** Across the 17 nodes of
  `data/temporal_logic` + `data/narrative` the score is almost perfectly
  predicted by how many pre-existing heads the template reuses: 1.000 for the
  two nodes written entirely in adopted heads
  (`temporal.order.precedence_transitivity`,
  `narrative.frame.frame_consistency`), 0.400–0.750 for mixed templates, and
  0.000 for all five written only in heads the corpus introduced
  (`until_unfolding`, `chekhov_gun`, and the three
  `narrative.structure.*` unit definitions). This is the numeric form of the
  already-recorded "a new discipline's vocabulary is structurally quarantined".
  Sharper instance: `narrative.constraint.chekhov_gun` is written *entirely* in
  the temporal corpus's ALWAYS/IMPLIES/EVENTUALLY vocabulary and still scores
  0.000, because its constituents are `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` and
  `PLANTED⟨?0⟩` rather than `EVENTUALLY⟨?0⟩` — one extra unary head under the
  modality changes the skeleton. The general pattern it instantiates scores
  0.500 on the same formula shape, so an instance grades *lower* than its
  pattern, which inverts what the score is for.
  **The instance-below-its-pattern half is SHIPPED** (groundedness v2): a
  constituent that fails exact skeleton lookup is now re-tried with
  `specialize.py`'s matcher, every known form used AS PATTERN against it, so
  `EVENTUALLY⟨?0⟩` covers `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` by binding the slot to
  the instantiated call. Reported per constituent as `"grounded_via":
  "pattern"` with the form it instantiates, and counted separately from
  `grounded_exact`. Evidence gate: the match must bind some slot to a
  *named-head application*; slot-to-slot renaming is refused (that is a twin,
  and accepting it would grade P-vs-V category mismatches as grounding), and
  so are commutative absorption and identity-element binding, which are
  specialization and where `specialize.py`'s recorded noise lives — allowing
  them moves the mean by only +0.003 but credits e.g. Beer-Lambert's
  `?0:P * ?1:V * ?2:V` with grounding `?0:P * D⟨?1:V⟩` by vanishing a factor.
  Measured, 197 nodes: **corpus mean 0.700 -> 0.761**, 32 statements rise,
  **zero fall**, scores at 0.000 fall from 28 to 24, at 1.000 rise from 106 to
  124; 403 constituents ground exactly and 50 via pattern membership.
  `narrative.constraint.chekhov_gun` **0.000 -> 0.500** and its abstraction
  `temporal.response.response_pattern` **0.500 -> 1.000** — the inversion is
  gone (the instance no longer grades *below* its pattern), and the remaining
  gap is honest rather than mechanical: Chekhov's two ungrounded constituents
  are exactly `PLANTED⟨?0⟩` and `DISCHARGED⟨?0⟩`, heads that occur in no other
  statement.
  **The vocabulary-overlap half stays OPEN.** The four
  `narrative.structure.*` unit definitions are still 0.000 -> 0.000: they are
  written entirely in heads no other statement uses, so no pattern can cover
  them, and nothing short of the epistemic ladder distinguishing "new
  primitive" from "gibberish" will move them. The rest of that seeding pass
  did move — every other `data/temporal_logic` node now grades 1.000 — which
  narrows the quarantine claim to nodes introducing *unshared* heads rather
  than nodes in a new discipline.
  **Counterexample from the other direction (provability corpus, PV3
  missed): the score also fails OPEN.** All six `data/provability` nodes
  ground at **1.000** on arrival, though BOX occurs nowhere else in the
  graph: intra-corpus recurrence is unconditionally sufficient (BOX⟨?0:V⟩
  recurs across three sibling nodes, BOX⟨?0:P⟩ across the other three, and
  NEG⟨BOX⟨?0:P⟩⟩ is verbatim the consistency definition's expression side),
  and the pattern channel absorbs the box entirely (Löb's reflection
  premise IMPLIES⟨BOX⟨?0:V⟩, ?0:V⟩ grounds as an instance of ex falso's
  IMPLIES⟨?0:P, ?1:V⟩ by a slot swallowing the boxed subtree). So
  "unshared" in the quarantine claim means *occurring in one statement*,
  not *new to the graph*: a hermetic six-node corpus that reuses one new
  head densely self-certifies to the score's maximum in a single authoring
  act, while temporal's singleton narrative heads stay at 0.000. Combined
  with the until_unfolding self-reference defect, the ladder's one graded
  rung has now been measured failing in both directions (correct axiom at
  0.000; brand-new vocabulary at 1.000). Fix shape: report intra-corpus
  and extra-corpus grounding separately (provenance is in the inventory
  already), and gate the pattern channel's slot-swallows-call credit on
  the swallowed head being known outside the statement's own corpus.
- **`specialize.py` produces zero edges and zero noise on call-only corpora —
  fifth confirmation, from the other side.** 468 specialization edges over the
  merged graph, none touching either of the 17 new nodes in either direction.
  Same root cause as the recorded "specialize.py is arithmetic-only"
  (`COMMUTATIVE = {+, *}`, `IDENTITY = {+: 0, *: 1}`) that already gave
  `data/logic` and `data/set_theory` zero edges. The new information is that
  these corpora also contribute **zero degenerate noise**, because the noise
  mechanism (a variable slot absorbing arguments of a commutative arithmetic
  op) has nothing to bite on in a template made only of call heads. Any
  evaluation of the proposed category-compatibility constraint should note that
  the corpora it would clean up are exactly the corpora that get edges at all.
  **PARTIALLY RESOLVED** (branch `tooling/head-algebra`): with per-head
  identities, `data/logic`, `data/set_theory` and `data/morphology` now get
  edges — seven of them, every one looseness 0 and every one informative,
  which is a hit rate no arithmetic corpus in this graph comes close to. The
  "zero noise" observation survives intact and is now load-bearing evidence:
  the seven call-corpus edges added **zero** degenerate ones, because a call
  head is arity-fixed and cannot be absorbed into. `data/temporal_logic` and
  `data/narrative` are still at zero in both directions — they carry no head
  with a declared identity (`UNTIL`, `ALWAYS`, `EVENTUALLY`, `NEXT`), so the
  new mechanism has nothing to bite on there either.
- **Monotone endo-functions need a second monotonicity template, and the
  backlog's own request could not be honoured.** The
  `geotop.measure.area_monotonicity` entry above asks that a future
  monotone-functional node be written with *that* template
  (`IMPLIES(LEQ(REGA, REGB), CARD(REGA) <= CARD(REGB))`).
  `temporal.monotonicity.eventually_monotonicity` is the first such node and
  cannot: `CARD` is a valuation into the numbers, while `EVENTUALLY` maps the
  lattice of temporal properties into itself, so its conclusion must be a
  second `LEQ` and the honest template is
  `IMPLIES(LEQ(PROPA, PROPB), LEQ(EVENTUALLY(PROPA), EVENTUALLY(PROPB)))`.
  The two skeletons share their premise and differ in the kind of their
  conclusion, so no group forms. The request presumed every monotone functional
  is a valuation; monotone *endo*-functions are a second kind. The
  generalization the graph wants — `IMPLIES(LEQ(x, y), LEQ(F(x), F(y)))` with
  the numeric case as its specialization along a valuation — is also out of
  reach for `specialize.py`, since `<=` and `LEQ` are different relation kinds.
  Wanted: either a `LEQ` spelling of the numeric case, or a match level that
  treats a declared order relation and `<=` as one head.
- **The two-premise detachment shell is now the graph's most-populated
  non-family.** `IMPLIES⟨MEET⟨_, _⟩, _⟩` carries five nodes —
  `logic.inference.modus_ponens`, `settheory.order.subset_transitivity`,
  `geotop.predicates.containment_transitivity`,
  `temporal.order.precedence_transitivity` and
  `narrative.causality.precedence_causation_bridge` — and forms exactly one
  group (the three transitivity nodes). The three that group share a *slot
  pattern* ((0,1),(1,2) ⊢ (0,2)); the causation bridge conjoins two relations
  over the SAME pair and concludes a third over that pair. The distinction is
  real and the graph has no vocabulary for it: "same shell, different slot
  pattern" is currently indistinguishable from "unrelated" in every report.
  Companion to the recorded "slot recurrence, not slot shape" wanted level —
  that one asks for a query over slot recurrence within a statement, this one
  asks for the shell itself to be reportable as a weaker grouping.
- **Idempotence and involution cannot be related, and the reason is a fixed
  point rather than a head.** `temporal.modality.always_idempotence`
  (`ALWAYS⟨?0:V⟩ = ALWAYS⟨ALWAYS⟨?0:V⟩⟩`) is the fifth member of the recorded
  "operation that returns its argument" family and the first idempotent
  *modality*. Worth separating from the head-literalism entries because the
  blocker against `logic.boolean_laws.double_negation`
  (`?0:V = NEG⟨NEG⟨?0:V⟩⟩`) is not the head: NEG applied twice equals the bare
  slot, ALWAYS applied twice equals `ALWAYS⟨?0⟩`, so the two sides differ in
  depth. An idempotent has a fixed point an involution does not, and that is a
  property of the skeleton rather than a shape of it — the exact case the
  wanted structural-query facility has to cover.

- **An identity that collapses a call is a rewrite, and rewrites need their
  own non-triviality bar.** Found while shipping `HEAD_ALGEBRA`. The
  arithmetic identity rule is safe because a commutative op's arity is
  variable: binding `SHIFT -> 0` removes an *argument*. A call's arity is
  fixed, so `HEAD(a, e) = a` removes a *node*, and the pattern that survives is
  smaller than the one `op_count(gtree) >= 2` was checked against. Measured
  cost of not noticing: `specialize.py` went from 573 edges to **1080**, and
  500 of the 507 extra came from three templates —
  `geotop.predicates.de9im_disjoint` (`MEET(REGA, REGB) = EMPTYSET`
  collapsing to `REGA = EMPTYSET`), `morphology.wordformation.affixation` and
  `iterated_affixation` — each then matching every two-slot equation in the
  graph. Fixed by counting collapses and re-checking
  `op_count(gtree) - collapses >= 2`, which drops the count to 580. Recorded
  because every future algebraic rewrite (associative flattening, the wanted
  sum-collapse-under-constant-summand, series truncation) has the same shape:
  it shrinks the pattern, and the guard that made patterns non-trivial has to
  be evaluated on the pattern *as used*.
  **SHIPPED, and strengthened** (branch `tooling/cheapest-derivation`): the
  bar is no longer a post-filter over one derivation but a *constraint inside
  the search* (`Search.acceptable`, consulted per candidate derivation).
  A derivation that shrinks the pattern below the bar can no longer end the
  search; the matcher keeps looking and returns the cheapest derivation that
  passes. Re-measured on the 199-node corpus: with the guard removed the
  count goes 622 -> **1130** edges (+508, the same explosion the head-algebra
  work measured as 573 -> 1080), so the guard is still entirely load-bearing.
  The generalization the entry predicted also held: applying the *whole*
  acceptability test (guard + non-triviality) as a post-filter over the
  global minimum instead of as a search constraint yields only 463 edges —
  159 pairs whose cheapest derivation is degenerate but which have a
  perfectly good informative one. Any future rewrite inherits the constraint
  for free by being priced in the cost model.
- **First-success-wins search lets a weaker reading pre-empt a stronger one.**
  Second finding from the same work, and independent of it.
  `find_specializations` calls `match` once and keeps whatever it returns, so
  when a new mechanism is added, an edge that previously matched cleanly can
  come back with a degenerate derivation instead. Observed exactly once:
  `geotop.predicates.de9im_disjoint >= temporal.modality.next_distributes_over_meet`
  was matched by plain binding, and the identity rule found
  `REGB -> TRUTH` first, which then failed the collapse guard and deleted the
  edge. Worked around by running `match` twice per candidate pair, with head
  identities disabled on the first pass — the general principle being that a
  reading needing no algebra is always the better reading. That principle is
  not enforced *within* a pass (a collapse deep in a subtree can still
  pre-empt an argument swap higher up), and it will not scale to a third and
  fourth mechanism. Wanted: `match` returns the *cheapest* derivation rather
  than the first, e.g. by scoring mechanisms and searching best-first, which
  would also give `looseness` a companion "how much algebra did this need"
  axis.
  **SHIPPED** (branch `tooling/cheapest-derivation`). Every mechanism now
  carries a price — rename 0, slot->structure `1 + op_count(bound)`,
  absorption 1 per extra argument swallowed, arithmetic identity 2 per use,
  head-identity collapse 4 per use — and `Search` returns the minimum-cost
  *acceptable* derivation over the whole space (exhaustive DFS with
  branch-and-bound; cost is monotone along a derivation, so pruning at the
  incumbent is exact). The two-pass workaround is deleted: the guarded
  reproducer `de9im_disjoint >= next_distributes_over_meet` comes back via
  plain binding at cost 7 (7 structure + 0 algebra, 0 collapses), and it does
  so at every depth rather than only at the root, because acceptability is a
  search constraint now (see the entry above). Measured against the v2 count
  of 589 edges on the same 199 nodes: **622 edges, 33 gained, 0 lost.** All
  33 gains have one general node, `physics.circuits.ohms_law`
  (`POTENTIAL = FLOW * RESISTANCE`), and all 33 are the entry's own failure
  mode in its harshest form — v2's first success bound `FLOW -> QUANTITY,
  RESISTANCE -> inv(INTERVAL)`, a reading the informativeness filter scores
  as a bare renaming (see the `used_compound` entry below), so the pair was
  dropped entirely rather than re-derived as `FLOW -> QUANTITY*inv(INTERVAL),
  RESISTANCE -> 1` (cost 6), which is the same shape as the
  `beer_lambert_law`/`ABSORPTIVITY -> 1` edges the graph already carried.
  Of the 589 retained edges, 106 change `via` and 128 change bindings, always
  towards a cheaper reading: `newton_second_law >= triangle_area_formula` was
  `INERTIA -> 1` plus a three-factor absorption and is now `INERTIA ->
  CONSTANT` plus a two-factor one (the search stops paying for the identity
  rule when an honest binding is available). Cost range 1-12, median 6.
  Runtime *fell*: `find_specializations` 0.157s -> **0.111s** (best of 3,
  209383 search steps), 0.49s wall for the whole tool, because dropping the
  second pass buys more than exhaustive enumeration costs and the incumbent
  prunes the rest. No beam, no memo, no bound needed at this corpus size.
- **The commutative path never sets `used_compound`, so a slot swallowing a
  subtree inside `+`/`*` reads as a bare renaming.** Found while shipping the
  cost search, which is why the 33 gained edges above are all one node.
  `gen_commutative` assigns its bindings directly instead of recursing
  through the slot case of `gen_direct`, and only `gen_direct` sets the flag
  (v2 had the identical split between `match_commutative` and `match_direct`,
  so this is inherited, not introduced). Consequence: a match whose only
  novelty is `RESISTANCE -> inv(INTERVAL)` scores as "pure slot-to-slot
  renaming" and is filtered out, even though the module docstring explicitly
  lists "a slot binding structure (a compound subtree or a literal)" as
  informative. `looseness` and `structure_cost` both count that binding, so
  the flag is the only thing that disagrees. Measured cost of the bug:
  setting `compound=1` on non-slot commutative bindings takes the graph from
  **622 to 791 edges** (+169 beyond the 33 already recovered) and drops the
  median cost from 6 to 4, because the 33 ohms-law edges and many others then
  derive far more cheaply (the ohms-law pairs at cost 2 via plain compound
  binding rather than cost 6 via absorption + identity). Deliberately NOT
  fixed in the cheapest-derivation commit: it is a change to what "informative"
  means, a +169-edge adjudication in its own right, and mixing it in would
  have made the cost-search regression unreadable. Wanted: decide whether the
  non-triviality bar means "the pattern did work" (fix it) or "the pattern
  bound a subtree *where a leaf was written*" (document it), then land the
  edge-count change on its own with the usual per-family adjudication.
- **The same first-success bug was living in `decompose.py`, one import
  away, and cost the groundedness ladder two rungs.** `decompose.py` uses
  `specialize.match` as a predicate and then refuses the match if
  `used_absorption or used_identity` — i.e. it wants the no-algebra reading
  specifically. Under first-success it never got to ask: matching
  `*(?0:P, ?1:V)` against `*(?0:P, LOG(?1:V))`, the parameter slot's identity
  branch fires first (`?0 -> 1`, the rest absorbed), `match` returns True
  with the algebra flags set, and `pattern_cover` rejects a pattern that
  covers the subterm perfectly well by plain binding. The consequence was not
  "no grounding" but *worse* grounding: the coarser `*(?0:V, ?1:V)` was cited
  instead, which is the P-vs-V category mismatch `pattern_cover`'s own
  docstring says it refuses weaker matches to avoid. Routing the compatibility
  `match` through the cost search fixes it for free. Measured on the 199-node
  corpus: **10 of 198 nodes change constituents, corpus mean groundedness
  0.7634 -> 0.7660**, `calculus.differentiation.product_rule` 0.714 -> 0.857
  and `linearity_of_derivative` 0.778 -> 0.889, each gaining one
  `grounded_via_pattern` constituent. Not adjudicated here and the ledgers are
  deliberately not refreshed on this branch (see the entry below); wanted: a
  groundedness-owner pass over those 10 nodes' new citations, then a ledger
  refresh. Generalisation worth keeping: any consumer that asks a matcher
  "did you need mechanism X" is silently asking "was X on the first path you
  happened to take", which is not a question about the statements at all.
- **`reports/` has no regeneration check, and two of the four ledgers are
  already stale on `main`.** `scripts/check_regeneration.py` enforces
  seeds -> `data/` coherence and nothing else, so nothing notices when a
  committed report stops matching what its script produces. Found while
  regression-testing this branch: at `main` (6483a23, "Refresh all ledgers
  post-head-algebra"), re-running `measure_compression.py` and `decompose.py`
  with the *unmodified* v2 matcher already produces a 46-line diff in
  `reports/compression.json` and a 290-line diff in
  `reports/decompositions.json` — `logic.inference.hypothetical_syllogism` is
  missing from the compression ledger entirely and several `family_reuse`
  counts are one low, which smells like a corpus merge that refreshed some
  ledgers and not others. Both files are therefore left untouched here rather
  than refreshed, so that this branch's diff is only the matcher's doing.
  Fix: extend `check_regeneration.py` (or add a sibling) to re-run each
  report writer into a temp path and diff, and put it in the release skill's
  step 1 alongside the data check.
- **The cost weights are the first numbers in the matcher with no corpus
  citation.** `HEAD_ALGEBRA` was built on the house rule that every algebraic
  claim names the node that justifies it; `COST_IDENTITY = 2` and
  `COST_HEAD_COLLAPSE = 4` name nothing. They are defensible ordinally — a
  rewrite that erases a node should cost more than one that fills a slot in,
  which should cost more than a rename — and the ordinal facts are what the
  search actually uses, but the specific magnitudes decide ties between
  mechanisms and nothing in `data/` adjudicates them. Probed the whole
  algebra half of the model by sweeping each weight independently and
  diffing membership *and* per-edge derivations against the shipped report:
  `COST_HEAD_COLLAPSE` in {0, 1, 2, 3, 4, 5, 6, 7, 8, 20, 100},
  `COST_IDENTITY` in {0, 1, 2, 3, 5, 10}, `COST_ABSORB_ARG` in {0, 1, 2, 3}
  — **622 edges and identical membership in every one of the 21 runs**, with
  exactly one edge changing its *derivation* (at `COST_IDENTITY >= 3` and
  again at `COST_ABSORB_ARG = 0`). So on the 199-node corpus the graph is
  decided by the acceptability constraint and the structure cost; the algebra
  weights are currently unfalsifiable by the data, which is the real reason
  to be uneasy about them rather than a reason to relax. The exposure grows
  with every mechanism added, since each new one has to be priced against
  numbers nothing tests. Wanted: either derive the weights from something
  (edit distance on the skeleton? the epistemic ladder's rung ordering?) or
  record them as a declared, provenanced table the way head algebra is, so a
  future mechanism has to argue its price rather than pick one — and add a
  corpus pair that *does* discriminate, so the sweep above stops being flat.
- **The typed sort key orders P before V, which silently re-splits heads that
  a future alias would want to merge.** `typed_resort` sorts by a key in which
  `?P` precedes `?V`, so declaring MEET commutative moved
  `logic.boolean_laws.identity_laws` from `?0:V = MEET⟨?0:V, ?1:P⟩` to
  `?0:V = MEET⟨?1:P, ?0:V⟩`, while
  `morphology.wordformation.zero_morpheme_identity` keeps
  `?0:V = CONCAT⟨?0:V, ?1:P⟩` because CONCAT is (correctly) not commutative.
  The two identity laws are the pair `docs/BACKLOG.md` names as the
  head-literalism reproducer, and they are now *further* apart than before:
  same structure, different head, and now different argument order too. Harmless
  today (`CONCAT` and `MEET` share no alias class and must not), but it means
  any future "opaque binary composition" alias has to normalize argument order
  after aliasing, not before. Cheap fix when it lands: run the commutative sort
  inside `alias_heads`' output rather than only in `canonicalize`.
  **SHIPPED** (branch `tooling/matcher-consistency`), though the diagnosis was
  half right and the shipped fix is a different shape than the one proposed.
  The proposed fix — "run the commutative sort inside `alias_heads`' output" —
  was already in place: `load_nodes` computed `skeleton(canonicalize(
  alias_heads(tree)), classes)`, so both the shape sort and the typed re-sort
  already ran *after* aliasing. What was missing is that they read
  commutativity in the WRONG VOCABULARY: `COMMUTATIVE_CALL_HEADS` holds
  pre-alias spellings (`MEET`, `JOIN`, `MINOF`, `TOUCHES`), so the moment a
  commutative head joined an alias class its post-alias name would match
  nothing and the sort would silently stop. Now `canonicalize`, `typed_resort`
  and `skeleton` take the commutative-call set as a parameter, and the aliased
  level passes `ALIASED_COMMUTATIVE_CALL_HEADS` — the unaliased commutative
  heads plus every alias class *all* of whose members are declared
  commutative, which is what keeps `ordered_compose` non-commutative on
  CONCAT's evidence rather than inheriting it from a sibling.
  Measured, on the 199-node corpus: the set equals `COMMUTATIVE_CALL_HEADS`
  today (no declared-commutative head is aliased), so **zero aliased skeletons
  change and zero groups change membership** — 30 aliased groups before and
  after, every skeleton string byte-identical. The guard was verified by
  counterfactual instead: temporarily aliasing `MEET`/`JOIN` into an
  `opaque_compose` class, `MEET(PROP1, TRUTH) = PROP1` and
  `MEET(TRUTH, PROP1) = PROP1` split into `?0:V = opaque_compose⟨?0:V, ?1:P⟩`
  and `?0:V = opaque_compose⟨?1:P, ?0:V⟩` under the old lookup and share
  `?0:V = opaque_compose⟨?1:P, ?0:V⟩` under the new one.
  Adjudicated on this entry's own pair: **the MEET and CONCAT identity laws do
  NOT newly reach the aliased level, and no other pair does either.** They read
  `?0:V = MEET⟨?1:P, ?0:V⟩` and `?0:V = ordered_compose⟨?0:V, ?1:P⟩`. Sorting
  after aliasing cannot close that, and the entry's framing ("now *further*
  apart") over-blames the sort: the argument-order divergence is a
  *consequence* of a correct declaration, since CONCAT is non-commutative and
  its arguments must not be reordered at any level. The two are separated by a
  head, not by an order, and the only thing that would merge them is an alias
  class asserting that MEET and CONCAT are one operation family — which is
  false. What this entry really wanted, and what is now impossible to get wrong
  silently, is that the *hazard* be structural rather than remembered.
- **Commutative-head robustness reaches `typed` but not `shape`.** Probed on
  the pair the declaration was meant to make safe: `MEET(PROP1, TRUTH) = PROP1`
  and `MEET(TRUTH, PROP1) = PROP1` now share a typed skeleton
  (`?0:V = MEET⟨?1:P, ?0:V⟩`) — which is the whole point, and what makes the
  logic/set-theory twin robust rather than lucky — but their *shape* skeletons
  are `?0 = MEET⟨?0, ?1⟩` and `?0 = MEET⟨?1, ?0⟩`. Cause: `shape_key` erases
  slot identity, so two slot arguments compare equal, the sort is stable, and
  the placeholder indices are then assigned in the surviving order. The gap
  only opens when a slot RECURS across the relation, which is exactly the
  family the wanted "slot recurrence, not slot shape" match level is about.
  `shape` is documented as the loosest level and is here strictly stricter
  than `typed`, which inverts the ladder. Fix candidate: order commutative
  arguments by first-occurrence index of their slots over the whole statement
  (a fixpoint, since the indices depend on the order), or accept it and note
  in the report that `shape` is not a relaxation of `typed`.
  **SHIPPED** (branch `tooling/matcher-consistency`) as `shape_resort`, the
  shape-level counterpart of `typed_resort`. The entry's fix candidate names
  the difficulty correctly and then trips over it: there IS no order-independent
  key on a single argument, because the fact that distinguishes the two slots —
  that one of them RECURS on the other side of the relation — is a property of
  the whole statement, which is why first-occurrence ordering comes out a
  fixpoint. So the fix is a canonical form rather than a key: among the
  argument orders declared commutativity permits, take the one whose rendering
  is lexicographically smallest. Only the permutations WITHIN runs of equal
  `shape_key` are candidates (`canonicalize` has already fixed the order of
  everything distinguishable, from the argument multiset alone), so the
  candidate SET depends only on structure plus slot-recurrence pattern, `min`
  over it is order-independent, and — since an equal typed skeleton already
  implies an equal structure-plus-recurrence class — equal typed now FORCES
  equal shape. The ladder invariant holds by construction, and because the old
  skeleton is always one of the candidates, shape groups can only coarsen;
  none can split.
  Measured on the 199-node corpus:
  - Group counts unchanged at every level — shape 28, typed 29, family 28,
    aliased 30 before and after; **zero membership changes anywhere**, and
    typed/family/aliased skeleton strings byte-identical (the new sort runs
    only on the `slot_class is None` path). `decompose.py` and `specialize.py`
    reproduce their reports byte-for-byte.
  - Four shape skeleton STRINGS move to their canonical minimum:
    `calculus.differentiation.product_rule`, `diffgeo.surfaces.first_fundamental_form`,
    `ml.policy.ppo_clipped_surrogate`, and — the one worth reading —
    `geotop.predicates.adjacency_symmetry`, which goes from
    `IMPLIES⟨TOUCHES⟨?0, ?1⟩, TOUCHES⟨?1, ?0⟩⟩` to
    `IMPLIES⟨TOUCHES⟨?0, ?1⟩, TOUCHES⟨?0, ?1⟩⟩`. The node that exists only to
    say TOUCHES is commutative now renders, at shape level, as the tautology it
    became once the declaration replaced it.
  - `ladder_violations` is **0 after — and was 0 before**. Reported honestly:
    the inversion was never realized in `data/`, because every commutative-head
    statement in the corpus is authored in one order. It was a robustness hole,
    not a live defect, and the probe is what shows it: pre-fix,
    `MEET(TRUTH, PROP1) = PROP1` and `MEET(PROP1, TRUTH) = PROP1` had shape
    skeletons `?0 = MEET⟨?1, ?0⟩` and `?0 = MEET⟨?0, ?1⟩` while sharing one
    typed skeleton; post-fix both are `?0 = MEET⟨?0, ?1⟩`. Same for JOIN. The
    check now runs every invocation and prints to stdout, so a corpus that
    spells one the other way cannot reintroduce it unnoticed.
  - Cost: the whole corpus needs at most **24** candidate orderings for one
    statement (`economics.macroeconomics.gdp_expenditure_identity` and
    `geomodel.quaternions.unit_quaternion_constraint`, both four-term sums),
    489 summed over all 199 nodes, against a `SHAPE_ARRANGEMENT_BUDGET` of
    4096. Restricting to tie-blocks is what makes it cheap: unrestricted
    permutation would need 1152 for `first_fundamental_form` alone.
- **The typed sort has the same tie the shape sort just lost.** Found by the
  probe that verified `shape_resort`. `typed_key` distinguishes `?P` from `?V`
  but not one `?V` from another, so two variable-like arguments of a
  commutative head still fall through to the stable sort and keep their
  authored order. `MEET(SETA, JOIN(SETA, SETB)) = SETA` and the absorption law
  spelled `MEET(JOIN(SETB, SETA), SETA) = SETA` now share a shape skeleton and
  still split at typed (`MEET⟨?0:V, JOIN⟨?0:V, ?1:V⟩⟩` vs
  `MEET⟨?0:V, JOIN⟨?1:V, ?0:V⟩⟩`). Not urgent and not a ladder violation — it
  is the ladder pointing the right way, shape looser than typed — but it is
  the same defect one level up, and the same remedy applies: give
  `typed_resort` the `shape_resort` treatment, minimizing the rendering over
  tie-blocks of equal `typed_key` rather than over tie-blocks of equal
  `shape_key`. Deliberately not shipped with the shape fix, because it would
  change typed skeletons and therefore risk twin membership, which that change
  was required not to do.
- **An identity element has one abstract identity and several corpus
  spellings, and the report prints whichever is listed first.**
  `HEAD_ALGEBRA["JOIN"]["identity"]` is `("FALSITY", "EMPTYSET",
  "INCONSISTENCY")` because the same lattice bottom is spelled three ways in
  `data/logic`, `data/set_theory` and `data/narrative`. `specialize.py` tries
  the spellings in table order, so
  `settheory.boolean_laws.absorption >= settheory.boolean_laws.idempotence`
  reports `SETB -> FALSITY` — correct, but in the wrong corpus's vocabulary.
  Cosmetic today (four edges), and it will not stay cosmetic once more corpora
  declare identities. Fix: prefer the spelling that occurs in the *specific*
  node's `slot_schema`, falling back to table order. The deeper version of the
  same request is the recorded "same invariant, slot in one corpus and call
  head in another" lint — both want a notion of "these identifiers name one
  object" that the graph does not yet have.
  **SHIPPED** (branch `tooling/cheapest-derivation`), with one correction to
  the proposed fix: the specific node's own `slot_schema` is not enough.
  `settheory.boolean_laws.idempotence` is `MEET(SETA, SETA) = SETA` and
  declares no constant at all, so the node-level rule would have left the
  cited edge printing `FALSITY`. `spelling_ranker` therefore ranks spellings
  by the specific statement's `slot_schema` first, then by the union of every
  `slot_id` its *discipline* declares anywhere, then by table order; ties in
  derivation cost keep the first spelling tried, so the ranking decides the
  printed name. The corpus vocabularies are cleanly disjoint —
  `data/logic` {TRUTH, FALSITY}, `data/set_theory` and
  `data/geospatial_topology` {UNIVERSE, EMPTYSET}, `data/narrative`
  {INCONSISTENCY}, `data/morphology` {EMPTY} — so the discipline rule is
  decisive wherever it applies. Measured: the two edges with a set-theory
  *specific* flip `FALSITY` -> `EMPTYSET`
  (`logic.boolean_laws.absorption >= settheory.boolean_laws.idempotence` and
  `settheory.boolean_laws.absorption >= settheory.boolean_laws.idempotence`),
  the two with a logic specific correctly keep `FALSITY`, and the five CONCAT
  collapses report `EMPTY` as `sole`. Every edge that binds an ambiguous
  identity now carries an `identity_spellings` block naming the head and the
  basis (`specific-node` / `specific-discipline` / `table-order` / `sole`),
  and a table-order fallback additionally prints an
  `identity_spelling_note`. **Zero edges currently fall back**, which is the
  number to watch as corpora are added.

## Schema

- **`symbolToken.syntactic_category` lacks `functional`/`operator`** (unlike
  `signatureSlot`), so operator symbols (`D`, `f`, `g`) must go in
  `functionals` while `symbols` still demands `minItems: 1` — FTC part 1
  needed a scalar symbol it didn't naturally have. Either add the enum
  members or relax `minItems`.
- **`provenance` entries reject `scope_note`, `equivalent_forms` entries accept
  it.** Two `additionalProperties: false` objects in the same node disagree
  about the same key name, and there is no reason for the asymmetry: a citation
  needs to say *why* it is cited at least as often as an alternative notation
  needs to say when it applies. Found while authoring
  `probstat.probability.two_component_mixture`, where Pearson 1894 wants "the
  founding paper, a two-component normal mixture fitted to Weldon's crab
  measurements" and Huber 1964 wants "the same template with the weight read as
  a contamination fraction". Validation failed on both; the notes now sit
  inside `bibliographic_entry` in square brackets, which is unparseable by
  anything that consumes the bibliography. Fix: add `scope_note` (or `note`) to
  the provenance entry schema.

- **`statement_id` pattern forbids underscores in the first segment.**
  `^[a-z0-9]+(\.[a-z0-9_]+)+$` allows `_` in every segment except the
  discipline prefix, so `set_theory.boolean_laws.de_morgan_laws` fails
  validation and the corpus had to use `settheory.` while the directory and
  the `discipline` field stay `set_theory`. The prefix and the directory name
  now disagree, which is a trap for anything that derives one from the other.
  Fix: allow `[a-z0-9_]+` in the first segment too (there is no reason for the
  asymmetry), or document the prefix-vs-directory mapping in the schema.
- **Slot ids may not start with a big-op prefix either.** The hazard recorded
  above for templates extends to `slot_schema`: a slot literally named
  `SUM_TERM` or `MAX_RATE` would be eaten by the prefix big-operator rule
  before it was ever looked up, so a whole class of natural slot names is
  quietly unusable. The information-theory corpus works around it by naming
  indexed slots `WEIGHT_i`, `PROBABILITY_i`, `CODELENGTH_i` (suffix, not
  prefix). Worth a lint rather than folklore.
- **Cross-corpus entailment is blocked by reciprocity.** `entails` /
  `special_case_of` / `generalizes` require the reciprocal edge in the other
  corpus's file, so genuine cross-discipline entailments (physics average
  speed IS a special case of calculus average rate of change) go unrecorded;
  only `composed_with` (unchecked) is usable one-sided. Options: a repair
  tool that writes the reciprocal edge into the target corpus, or relax
  reciprocity to a warning for cross-corpus edges.
- **Even one-sided `composed_with` cannot forward-reference a corpus authored
  on a parallel branch.** `validate_nodes.py` requires every link target to
  resolve in the merged graph, and the merged graph is whatever `data/*/` holds
  on the current branch. `diffgeo.surfaces.gauss_bonnet_theorem` should point
  at `algtop.invariants.euler_characteristic_surface`, which a parallel branch
  is authoring; writing the edge now makes validation fail here and pass only
  after a merge, so the reference sits in prose and the edge is a documented
  one-line addition in `scripts/seed_diffgeo.py`. Two agents seeding
  interlocking corpora in parallel therefore cannot link to each other at all.
  Fix: a `pending`/`external` link list the validator warns on instead of
  failing, or a manifest of reserved ids that branches may reference before the
  corpus lands.
- **Same invariant, slot in one corpus and call head in another.** The Euler
  characteristic is a bare slot in `diffgeo.surfaces.gauss_bonnet_theorem`
  (where it is the number on the right-hand side) and a call `EULERCHAR(.)`
  throughout `data/differential_topology` (where it is an invariant applied to
  a space). Both readings are natural, and the matcher cannot relate a slot to
  a call head, so the two corpora cannot see that they discuss one integer.
  The same trap is open for every named quantity that is sometimes a value and
  sometimes a functional (entropy, degree, cardinality, expectation). Wanted: a
  lint that flags an identifier used as a slot id in one node and a call head
  in another, plus a documented convention for which reading wins.
  **LINT SHIPPED** (branch `tooling/matcher-consistency`) as
  `slot_vs_call_head_collisions` in `scripts/match_signatures.py`, reported in
  JSON and in a stdout block. A lint only — which reading wins is an authoring
  decision about the corpora and stays one; nothing is rewritten. Comparison is
  case-insensitive on the stem, with the bracket-call marker `[]` stripped
  (`E[X|Y]` parses to the head `E[]`) and nothing else: index suffixes like
  `WEIGHT_i` are part of the identifier an author chose, and folding them would
  invent collisions rather than find them. A name is only reported when some
  statement DISAGREES with another — one committing to it as an opaque value
  while another applies it as an operation. Mere co-occurrence is not a
  collision, which is why `SELFMAP` and `AGGREGATE_n` are excluded (every
  statement carrying them uses them both ways) while `F` is included
  (`calculus.integration.ftc_differentiation_part` uses it as a slot only).
  **7 names, 25 statements.** The three pairs this entry was promoted for all
  appear:
  - `eulerchar` — slot in `algtop.homology.betti_alternating_sum`,
    `algtop.invariants.euler_characteristic_complex`,
    `algtop.invariants.euler_characteristic_surface`,
    `diffgeo.surfaces.gauss_bonnet_theorem`; call head in
    `difftop.invariants.euler_characteristic_diffeomorphism_invariance`,
    `difftop.vectorfields.hairy_ball_theorem`,
    `difftop.vectorfields.poincare_hopf_index_theorem`. Four algebraic-topology
    nodes on the slot side, not the one this entry named — the gap is wider
    than Gauss-Bonnet vs Poincaré-Hopf.
  - `length` — slot in `diffgeo.curves.arc_length_functional` and
    `graphtheory.walks.adjacency_power_walk_count`; call head in
    `morphology.quantity.morpheme_count_additivity`.
  - `degree` — slot in `geomodel.bezier.endpoint_tangent`; call head in
    `difftop.degree.degree_multiplicativity` and
    `difftop.degree.degree_regular_value_count`.

  Four the entry did not predict, all real and all of its stated kind ("a named
  quantity that is sometimes a value and sometimes a functional"): `f` (the
  FTC/Stokes cluster, where `calculus.integration.ftc_differentiation_part`
  alone treats the function as a value), `outer` (slot in
  `calculus.differentiation.chain_rule` and
  `difftop.degree.degree_multiplicativity`, head in
  `ml.recurrence.mlstm_matrix_memory_update`), `scale` (slot in three
  physics/statistics nodes including `probstat.transform.z_standardization`,
  head in `probstat.limit.normal_approximation_sample_mean` — a disagreement
  *within* `data/statistics`), and `sequence` (slot in
  `probstat.limit.law_of_large_numbers`, head in
  `narrative.structure.story_sequence`). The convention half of this entry is
  still open: the lint names where a decision is outstanding, it does not make
  one.
- **A quarter of the corpus loses its logical form.** The grammar has no
  quantifier and no usable implication, so conditional and existential
  statements reduce to their conclusions: of the sixteen nodes in
  `data/differential_geometry` and `data/differential_topology`, four carry
  their real content in `regularity_conditions` instead of the template —
  `difftop.invariants.euler_characteristic_diffeomorphism_invariance` (loses
  "whenever M and N are diffeomorphic"),
  `difftop.vectorfields.hairy_ball_theorem` (loses "if a nowhere-vanishing
  field exists"), `difftop.degree.brouwer_fixed_point` (loses "there exists x"),
  and `difftop.morse.weak_morse_inequality` (loses "for every Morse function
  and every k"). Consequence for the ledger: twin density is not comparable
  across `statement_class`, because definitions keep their whole content in the
  template and theorems routinely do not. Same family as the missing binder
  recorded under Parser / matcher.

- **Cross-corpus reciprocity, now measured in edits per edge.** The entry
  above proposes a repair tool; `data/machine_learning` priced it.
  `ml.objective.token_cross_entropy_loss` and
  `infotheory.divergence.cross_entropy` are the same functional, so the
  reciprocal `equivalent_to` was worth writing — which meant editing
  `scripts/seed_infotheory.py`, regenerating `data/information_theory`, and
  carrying an unrelated corpus's diff on this branch. That is affordable
  once. It is not affordable for
  `ml.preference.grpo_group_relative_advantage`, whose relation to
  `probstat.transform.z_standardization` is the strongest in the corpus (an
  exact typed twin, and GRPO's advantage really is that transform applied to
  rewards) but which had to degrade to a one-sided `composed_with`: the
  reciprocal `generalizes` would have to go into `data/statistics/nodes.json`,
  and that corpus has **no seed script** — it is hand-maintained, so the edit
  could not be made the way every other corpus is edited. So the reciprocity
  requirement's real cost is not "write two edges", it is "be able to
  regenerate the other corpus", and one corpus in the repo fails that test.
  Either the repair tool lands, or reciprocity relaxes to a warning for
  cross-corpus edges, or `data/statistics` gets a `scripts/seed_statistics.py`
  like everything else.
- **Side conditions that carry the whole empirical claim have nowhere to go.**
  The differential-topology entry above records lost quantifiers. Machine
  learning loses a different class and loses it in the most-cited node:
  `ml.adaptation.lora_low_rank_update` is
  `?0:V = +(?1:P, *(?2:P, ?3:V, ?4:V))`, which says the update factors
  through a product — it does not and cannot say that the inner dimension is
  small, which is the entire hypothesis of the paper. Same shape of loss:
  parameter tying across time steps in the recurrence nodes (the reason RNNs
  generalize across sequence length), and the zero-initialization of one LoRA
  factor (the reason adaptation starts at the pretrained model). All three
  sit in `invariants` and `regularity_conditions` as prose. Consequence for
  the ledger, beyond the one already noted for `statement_class`: three
  papers (LoRA, PiSSA, LoftQ) share one skeleton and differ only in how the
  same slots are initialized, so skeleton count understates the corpus's
  content in a way that is invisible from the reports.

- **`specialize.py` plain-binding suppression, fifth instance, same target node
  as the first.** `geotop.polyhedra.euler_polyhedron_formula`
  (`VERTICES - EDGES + FACES = 2`) covers
  `graphtheory.trees.tree_edge_count` (`EDGES = VERTICES - 1`) by binding
  `FACES -> 1`: a plane tree has exactly one face. Plain slot-to-literal
  binding, no absorption, no identity, so the filter drops it — exactly as
  recorded for `algtop.invariants.euler_characteristic_complex` covering the
  *same* polyhedron-formula node, for DE-9IM disjointness covering the
  complement law, and for surprisal covering the DPO loss. That node is now
  the target of two suppressed specializations from two different corpora,
  which makes it the natural regression test for the proposed fix (report
  matches whose bindings are non-trivial even when neither absorption nor
  identity fired).
- **RESOLVED (corpus gap): both blocked twin groups now exist.** The entry
  below asked for two nodes in `data/statistics`. Both have landed:
  `probstat.probability.probability_normalization` (earlier) and
  `probstat.probability.two_component_mixture` (`corpus/gapfill`). The mixture
  node typed- *and* shape-twins `numanalysis.interpolation.linear_interpolation`
  and `geomodel.bezier.de_casteljau_step` with no respelling, so
  `scripts/seed_numgraph.py`'s prediction 2(b) moves from *not evaluable* to
  FIRED. Two things are worth keeping from the episode. (1) *Not evaluable* was
  the right verdict to record and it was payable later by one node — a corpus
  gap is a cheaper defect than a matcher gap, and the reports should keep
  distinguishing them. (2) The fix cost nothing in tooling: the `(1 - WEIGHT)`
  spelling parses as written, so no BACKLOG item blocked it. The gap was
  purely that nobody had authored the statement.
- **A statement whose two standard spellings land in two different twin groups,
  in one node.** `probstat.probability.two_component_mixture` records
  `f = w*f_1 + (1-w)*f_2` in its template (the two-point convex-combination
  group: interpolation, de Casteljau, mixture — three disciplines) and
  `f = sum_k w_k*f_k` in `equivalent_forms` (the four-discipline weighted-sum
  group: Bezier, barycentric, total probability, Betti). One model, two
  textbook spellings, two disjoint groups, neither spelling wrong. This is the
  already-recorded "same statement, two spellings, and only one of them
  matches" item with the sharpest evidence yet, because here *both* spellings
  match — just not each other — so it cannot be dismissed as authoring luck
  about which form fires. It is the same K-to-2 collapse `specialize.py` cannot
  do (recorded for uniform-vs-Shannon entropy and for de Casteljau as the
  degree-one Bernstein case), now visible inside a single node.
- **`specialize.py`'s `rel` guard: 17 nodes, not 16.**
  `logic.inference.hypothetical_syllogism` is the newest node whose canonical
  template is a bare call rather than a relation, so it is dropped from the
  general side along with the sixteen already listed below. Confirmed
  empirically: of 582 specialization edges over 199 nodes, **zero** touch
  either node added on `corpus/gapfill`, in either direction. The mixture node
  is excluded for the other recorded reason (a recurring parameter slot plus a
  numeric literal in a multiplicative position), so one branch supplied a fresh
  instance of both filters at once.
- **The corpus gap is now measurable: two twin groups are blocked by one
  missing node.** `data/statistics` carries the law of total probability,
  Bayes's rule, z-standardization and the CLT, but **not** the normalization
  axiom `sum_i p_i = 1` and **not** a two-component mixture
  `p = (1-w)*p_0 + w*p_1`. Consequently
  `geomodel.barycentric.barycentric_partition_of_unity` (`1 = sum⟨?0:P⟩`) is a
  singleton whose exact structural twin is a one-line addition away, and
  prediction 2 of `scripts/seed_numgraph.py` ("linear interpolation versus
  probability mixtures") could not be evaluated at all — there was nothing to
  compare against, which is a different outcome from a miss and was reported
  as such. Both would be fixed by two nodes in `data/statistics`. That corpus
  still has no seed script (recorded above under cross-corpus reciprocity),
  so the cheapest fix to the graph's connectivity is currently the one that
  requires hand-editing the one file nobody can regenerate.
- **Same statement, two spellings, and only one of them matches — now
  quantified.** `numanalysis.integration.trapezoidal_rule` twins
  `geometry.area_formulas.trapezoid_area_formula` at typed level *because it
  was written with the one-half as a `constant` slot*; the textbook spelling
  `h*(f(a)+f(b))/2` produces `*(?1:P, +(?2:V, ?3:V), inv(2))` and matches
  nothing. Same for `numanalysis.interpolation.linear_interpolation`, where
  the expanded form `START + PARAM*(FINISH - START)` would have joined the
  five-member affine family and the written form
  `(1-PARAM)*START + PARAM*FINISH` joins nothing (the parameter slot recurs).
  In both cases the two spellings are algebraically identical, one fires and
  one does not, and the choice is the author's. This is the
  `authored_to_match` versus `emergent` distinction already requested for twin
  groups, seen from the authoring side: the corpus needs a way to record
  "these two templates are the same statement" so that a *normalizer* could
  eventually choose the canonical spelling, rather than relying on the author
  having already known which one fires. Without it, twin counts measure
  authoring luck as much as mathematical structure.
- **A `weighted_accumulation` archetype label was minted rather than adopted,
  deliberately, and the lint cannot tell.** `?0 = sum⟨*(?1, ?2)⟩` now spans
  three labels — `alternating_rank_sum` (topology),
  `conditional_marginalization` (statistics) and `weighted_accumulation`
  (both new geometric-modeling nodes). Neither existing label could honestly
  cover a Bezier point or a barycentric combination, and the new label could
  not honestly replace them either, so the drift entry is correct and
  unfixable by renaming. Same situation the ML corpus recorded for
  `state_minus_scaled_correction`. The pattern is stable enough now to
  propose the fix concretely: let `archetype_id` be a list, or add an
  `archetype_family` field, so a node can say "my label is X, my structural
  family is Y" and the lint can check the second while leaving the first free.

- **No scope construct, so `docs/DESIGN-frames-and-retrieval.md`'s central
  mechanism cannot be stated in a template.** `narrative.frame.frame_consistency`
  (`MEET(FRAMEPREMISE, NEG(FRAMEPREMISE)) = INCONSISTENCY`) is an exact typed
  twin of `logic.boolean_laws.complement_laws` and
  `settheory.boolean_laws.complement_laws` — which is the intended result, and
  also the whole problem. Everything that makes it a *frame* law rather than a
  logic law is the scope: "within frame F", frame premises occupying the
  frame's local VERIFIED tier, and their reversion to
  CONJECTURED-under-premise on scope exit. The grammar has no binder and no
  scope construct, so all of that sits in `regularity_conditions` as prose and
  the graph cannot check the boundary that the design document says is
  "structural, not stylistic". Same family as the lost quantifiers recorded for
  differential topology and the missing binder recorded for channel capacity,
  but with a new consequence: this is the first time the gap costs a *design
  document's* mechanism rather than a single statement's content. Fix shapes,
  in increasing order of work: a `scope` field on a node naming the frame its
  claims are relative to; a `FRAME(premises, claim)` head; or a real scoped
  construct in the grammar shared with the wanted `MAX(body, binder, domain)`.

  **FIRST FIX SHAPE SHIPPED** (branch `feature/frame-executor`): the live
  schema carries the draft's optional `scope` object (frame id, role,
  premises, suspends, governed_by, on_exit, retrieval), `validate_nodes.py`
  enforces frame-id pattern / frame agreement / reference resolution, and
  `scripts/frames.py` executes the boundary at runtime — declarations as
  the frame-local VERIFIED tier, suspension-gated contradiction, demotion
  on exit (32/32 tests; matcher report byte-identical, so the twin this
  item celebrates is untouched). Still prose-bound: nothing migrates
  `frame_consistency`'s own `regularity_conditions` into structure, no
  corpus node carries `scope` yet, and the `FRAME(...)` head / grammar
  binder remain the deeper fix shapes for statements *about* scoped claims.
- **No past modality, so half of a two-directional law cannot be written.**
  `narrative.constraint.chekhov_gun` states one direction — every planted
  element is eventually discharged. Its converse, `ALWAYS(IMPLIES(
  DISCHARGED(e), ONCE(PLANTED(e))))`, is the half that forbids deus ex machina
  and is the half most authors care about; it needs a past-tense modality
  (`ONCE`/`H` in the Manna–Pnueli past fragment) that `data/temporal_logic`
  does not carry. Adding one is cheap as a head, but note it will *not* twin
  its future dual for the usual reason, so the corpus would gain a statement
  and no structure. Recorded so that whoever adds past LTL knows the expected
  yield up front.
- **A strict order and its reflexive closure cannot share a head, and the
  corpus now pays for it inside one file.**
  `temporal.order.precedence_transitivity` uses the abstract `LEQ` head and is
  a three-discipline typed twin;
  `temporal.order.strict_precedence_asymmetry` uses `BEFORE` and is a singleton
  at every level. The second could not honestly use `LEQ`, because asymmetry is
  false of a reflexive relation, so this is not an authoring slip — it is the
  cheapest available demonstration that twin counts measure which head a
  statement is *allowed* to use. Companion to the recorded
  `authored_to_match` vs `emergent` request: a provenance flag on twin groups
  should be readable alongside this pair, since one member of an adjacent pair
  from one author lands in a cross-discipline group and the other lands nowhere.
  Wanted: a way to declare `BEFORE` as the strict part of `LEQ` (an order and
  its strict/reflexive variants as one declared family), which would also cover
  `⊆`/`⊂` and `<=`/`<`.


## Real-data lanes

- **Wikisem (LREC2020 logical forms) ingestion.** Corpus located and
  downloaded (43MB, 839 article-level lambda forms + 5,953 CG trees; see
  experiments/data_real/lrec2020-logical-forms/INGEST_NOTES.md for source
  URLs, format, and a prototyped mapping onto the matcher AST). Before the
  lane runs: (1) add `^` to COMMUTATIVE for conjunction chains, (2) fix the
  atom-classification wart (bound vars -> slots, `CATEGORY:lemma` atoms ->
  named leaves) so skeletons stop half-lexicalizing, (3) subterm mining is
  the granularity — sentence segmentation via variable indices fails on
  806/839 articles. LICENSE: data files carry no license statement (paper
  CC-BY covers the paper only); local research use only, no redistribution
  of derivatives without written confirmation from the maintainer.
  **Step (1) is blocked on a name collision, not on effort** (branch
  `tooling/head-algebra`): it cannot be done in `HEAD_ALGEBRA`. In this grammar
  `^` is exponentiation — `Parser.parse_power`, and `SIDE1^2` in
  `geometry.right_triangles.pythagorean_theorem` is not `2^SIDE1` — while in
  Wikisem `^` is conjunction. Declaring `^` commutative would silently
  scramble the 30 nodes in `data/` that use it as a power, so the table
  records `^` in its "deliberately absent" list with this reason. The lane
  needs either a lane-local algebra table layered over `HEAD_ALGEBRA`, or an
  ingestion step that rewrites Wikisem's `^` to `MEET` — which is already
  declared commutative, and is the head `data/logic` uses for conjunction, so
  the ingested forms would twin the Boolean corpora for free. The second is
  cheaper and strictly better.
