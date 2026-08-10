# Discoveries

Cross-discipline identities found *mechanically* by the matchers — parked
here as they are identified, for separate analysis. Each entry: the claim in
plain language, the structural evidence, and status. Grows over time; the
ledger of record is `reports/signature_matches.json` and
`reports/specializations.json`.

Statuses: **exact** (typed twin or reciprocal equivalence in the corpus),
**family** (twin after sign/parameter absorption), **shape** (structure
matches, slot roles differ), **specialization** (general→specific with
bindings), **near-miss** (informative failure, kept deliberately).

---

- **A near-miss that preserves length is what makes a geometry check
  falsifiable.** The obvious way to break a right angle — nudge the leg
  endpoint sideways — also changes that leg's length, so the length check
  catches it too and neither check can be shown load-bearing. Replacing the
  leg direction `v = (-q, p)` with `w = (q, p)` keeps the squared length
  identical (`p² + q²`) in exact integer arithmetic while rotating by
  `2·atan(q/p)`, giving a 1.53°–16.26° near-miss that only the right-angle
  check sees. With one such construction per check, all six visual-oracle
  checks ablate into a unique escape: disable one, exactly one invalid class
  of 240 passes and the other five stay fully rejected. The general lesson is
  that a verifier's checks are only separately testable if the negative set
  is built to isolate them. *P-VO2/P-VO3 fired; visual oracle* (2026-08-09)

- **A corpus of well-formed inputs cannot audit a verifier's soundness
  argument.** The visual oracle's six checks ablate cleanly — disable one,
  exactly one invalid class of 240 escapes — across 1,680 instances. Review
  still found a figure all six accepted: an angle annotation referencing a
  nonexistent vertex, which round-tripped through the SVG and verified `ok`.
  A second construction made a check skip its relation, so ablating a
  *different* check let the graph pass. Both occur 0 times in the generated
  corpus, which is exactly why the corpus could not find them. The results
  were right and the argument behind them was not yet sound; only inputs the
  generator never produces separate those two states. Both are now refused
  as malformed at the door rather than added as checks, since no controlled
  class exercises them and a check without a class is decoration.
  *adversarial review; visual oracle* (2026-08-09)

- **A capability-blind control can pass by being blind.** The visual lane's
  "max coordinate" surface baseline ran its number regex over the whole SVG
  and matched the `2000` in `http://www.w3.org/2000/svg`. It returned the
  same constant for every figure and scored a clean 0.500 on all six invalid
  classes — apparently confirming that the negatives are hard, actually
  measuring nothing. Reading numbers only from numeric attribute values
  raised its best cell to 0.740. A baseline that scores at chance deserves
  the same suspicion as one that scores perfectly: both can mean the
  instrument never saw the data. *self-audit* (2026-08-09)

- **Synthetic recombinant pointing does not transfer to corpus
  specialization.** Forty real A:B::C:D rows span six source and six target
  disciplines but only five distinct targets in one ratio family. Every D is
  rechecked by the specializer. Symbolic resolution and a blind last-slot
  number-transfer rule both score 1.000; the released synthetic checkpoint is
  0.000 exact on the RHS residual. The lane demonstrates verifiable corpus
  construction, not learned analogy. *P-CA1–P-CA4 retrospective labels;
  post-review corpus-grounded evaluation* (2026-08-09)

- **Conversation memory needs revocation, not just attribution.** A signed
  answer remains authentic after the user changes their mind. The maintained
  user frame therefore keeps both answers as provenance while a verifier-
  private committed supersession ledger makes the old one non-current. A
  public `superseded` tuple alone is forgeable and deletable. *P-CR2 fired;
  authenticated mutable-session result* (2026-08-09)

- **Two private perspectives can share one story without becoming story
  facts.** Alice's silver eggs and Bob's blue eggs render from owner-isolated
  bindings over an identical accepted golden-chicken state; neither value
  enters `frame.asserted`. *P-CR1/P-CR3 fired; maintained user-frame demo*
- **An address can generalize while a learned consumer destroys it.** In a
  five-arm, three-seed paired matrix, recurrent address-only remains best at
  `0.196 ± 0.064` conditional depth-OOD exact. Recurrent query construction
  reaches `0.179 ± 0.025`; recurrent memory `0.082 ± 0.027`; putting recurrence
  in both consumers collapses to `0.039 ± 0.011`; a two-parameter-matched
  level-aware MLP recovers to `0.142 ± 0.014`. Every arm is still at ceiling
  in distribution. Teacher-forced diagnostics locate the damage: address-only
  averages 0.910 on C-leaf copy and 1.000 on EOS, while memory recurrence falls
  to 0.705 and 0.913; both consumers fall to 0.677 on C-leaf. Shared iteration
  helped construct the address, but transforming that representation again at
  its consumers erased information the pointer needed. *P-DC1–3 missed;
  P-DC4 satisfied; three paired seeds* (2026-08-09)

- **The safe GPU protocol preserved the experiment and rejected the crash
  state.** Two identical Windows bugchecks occurred at final evaluation with
  `nvidia-smi` reporting 15,760/16,303 MiB (15.39/15.92 GiB). The first safety
  prediction was retracted because its post-cache-clear allocated-tensor
  measurand could not observe that state. Its replacement used logical batch
  192, microbatch 64, evaluation batch 32, a 70% allocator cap, atomic
  artifacts, separate reserved/whole-device telemetry, and an 80% absolute
  device guard. All 15 rows completed; maximum whole-device footprint was
  6,387,466,240 bytes and evaluation added at most 2,097,152 bytes. This makes
  near-full GPU occupancy strongly implicated in the repeatable failure, not
  proven as its sole hardware/driver cause. *P-DC5 retracted; P-DC6/7 fired*
  (2026-08-09)

- **Raw source-byte provenance is newline-fragile across Windows checkouts.**
  The completed depth runs correctly pinned the exact runtime bytes, but a
  later rebase changed mixed LF/CRLF working-tree bytes into semantically
  identical uniform CRLF. The analyzer still requires an exact raw-digest
  match first; a reviewed `depth_source_manifest.json` may bridge only those
  recorded runtime hashes to the canonical-LF hashes at clean run commit
  `25db073`, and forged or missing bridges refuse. Future launchers should
  record Git blob ids or canonical text hashes alongside raw hashes before a
  run starts. *post-run provenance finding; fail-closed bridge with regression
  controls* (2026-08-09)

- **Held-out tactic classification does not guarantee a search gain.** Three
  27,688-parameter byte-GRU rankers all score 0.8125 on four theorem-held-out
  groups (frequency 0.4375; shuffled-label controls 0.25–0.375) and solve live
  in 71/63/61 proposals. The arbitrary palette needs 86, but the stronger
  state-blind frequency order needs only 64—one better than the learned mean.
  Two seeds win and one loses; no mean learned advantage survives. *P-TP1–4
  fired against registered controls; corrective P-TP5 refuted the live-gain
  interpretation* (2026-08-09)

- **An accepted proof step can be a dead branch.** In live Lean search,
  ``clear h`` is kernel-accepted after introducing a conjunction hypothesis,
  but removes the only evidence needed to build the reversed conjunction.
  Breadth-first search retains that accepted transition as branch evidence and
  reaches the proof through another branch. This is the first controller trace
  in which backtracking is load-bearing rather than simulated by rejecting a
  no-op. *P-LS2's first registered run missed; corrective P-LS6 fired and
  satisfied P-LS2's substantive accepted-dead-branch criterion; live verifier
  result* (2026-08-09)

- **Rendered proof-state names are not necessarily callable proof-state
  names.** The first blind palette exhausted because Pantograph's bare
  ``intro`` rendered ``P✝``, ``Q✝``, and ``h✝`` while ``h.left`` and
  ``h.right`` failed as unknown identifiers. The registered prediction stays
  missed; a subsequent prediction added the ordinary ``intro P Q h`` tactic
  and the same search closed the theorem. A proof UI's text is an observation,
  not a lossless action interface. *P-LS2 initial form missed; P-LS6 fired*
  (2026-08-09)

- **Löb's axiom and temporal induction are one archetype and refuse to be
  one skeleton.** `provability.modal.loeb_axiom`
  (`IMPLIES⟨BOX⟨IMPLIES⟨BOX⟨?0:V⟩, ?0:V⟩⟩, BOX⟨?0:V⟩⟩`) and
  `temporal.induction.temporal_induction_axiom`
  (`IMPLIES⟨ALWAYS⟨IMPLIES⟨?0:V, NEXT⟨?0:V⟩⟩⟩, IMPLIES⟨?0:V, ALWAYS⟨?0:V⟩⟩⟩`)
  share `temporal_induction` in the drift report — both internalize
  induction along a well-founded step relation — and twin at no level.
  The trees differ in exactly the axiom that separates the logics: Löb
  discharges reflection (□p→p) only under a box, LTL validates it
  outright. A discipline-named archetype now spans a second
  discipline — by argued adoption in the seed, an authoring claim the
  drift report carries, not a tool-discovered fact; only the no-twin
  half is a matcher outcome. *P-CF4 fired, archetype-shared near-miss*
  (2026-08-08)

- **A six-node corpus can self-certify perfect groundedness on a head the
  graph has never seen.** Every `data/provability` node grounds at 1.000
  on arrival: BOX recurrence across sibling nodes counts as known form,
  and the pattern channel lets ex falso's `IMPLIES⟨?0:P, ?1:V⟩` swallow
  Löb's boxed premise whole. Registered prediction PV3 expected quarantine
  (no node at 1.000, corpus below graph mean) and was refuted in full —
  the groundedness rung fails open for dense new vocabulary just as it
  fails closed for self-referential axioms (until_unfolding, 0.000). On a
  corpus about the vacuity of self-certification, the ladder accepted a
  self-certificate. *PV3 refuted; measured defect in the graded rung*
  (2026-08-08)

- **Gödel's box and Sally's box now share a namespace.** The slot/head
  collision lint gained `box: slot BOX vs head BOX⟨...⟩` —
  `narrative.world.marble_moved_box` binds BOX as the marble's container
  constant while the provability corpus uses BOX as the provability
  modality. Harmless (slots never match heads) and kept: the lint doing
  its job across maximally distant disciplines. *lint working as designed*
  (2026-08-08)

- **False belief is a visibility result, not an authored contradiction.** The
  same placement and move events update world/Anne but the move is invisible
  to Sally, so her owned frame retains basket while world holds box and refutes
  basket. No new verdict was needed. *P-CF1 fired, executable ToM control*
  (2026-08-09)

- **Belief content can twin world content while scope carries the disagreement.**
  Sally's `LOCATION(MARBLE)=BASKET` and the world's
  `LOCATION(MARBLE)=BOX` share `?0:P = LOCATION⟨?1:V⟩`; owner and visibility
  are deliberately outside the matcher key. *exact content twin, scoped
  interpretation differs* (2026-08-09)

- **Scope generalizes across domains without implying template equivalence.**
  The rotating-physics frame and cartoon gravity both resolve to declaration
  nodes, suspend an ordinary physics law, and admit local premises. P-CF2
  nevertheless misses at every matcher level because the former is an
  additive correction and the latter a temporal response. The executor-level
  sameness and signature-level difference are both real. *near-miss,
  scope/template boundary* (2026-08-09)

- **Galilean velocity addition is rank decomposition in another vocabulary.**
  `OBJECT_VELOCITY = RELATIVE_VELOCITY + FRAME_VELOCITY` and algebraic
  topology's `CHAINRANK = CYCLERANK + IMAGERANK` share the exact typed skeleton
  `?0:V = +(?1:V, ?2:V)`. P-CF3 fired without respelling the standard law
  -- though neither of the prediction's NAMED candidates (convex
  combination, vector addition) matched: the class fired through a
  skeleton not on the candidate list, joining a previously-singleton
  node. The candidate miss is recorded beside the class hit, per house
  precision discipline. *exact, cross-discipline* (2026-08-09)

- **Waiting is a controller outcome, not a failed proof search.** A valid ASK
  records one signed question and stops the generic controller as WAITING;
  EXHAUSTED still means policy had nothing more to propose, and SOLVED still
  means the goal closed. A later run resumes the same immutable session state.
  *conversation control-plane distinction, executable* (2026-08-09)

- **User testimony can be locally attributable without becoming world truth.**
  The ASK return path records a signed `UserBinding` in a runtime-owned user
  frame and clears its exact UNKNOWN, but adds no frame assertion or corpus
  fact. The signature proves host-channel passage, not human identity or content
  correctness. *ToM entry boundary, 25 adversarial controls* (2026-08-09)

- **Proof provenance integrity is cheaper than proof correspondence—and must
  not be confused with it.** The merged validator can establish that an
  artifact is repository-contained and well formed, that a cited theorem
  exists, and that exactly one statement owns its identity. It cannot establish
  that the theorem proves that statement: a deliberately unrelated gravity
  node citing valid `BooleanLaws.modus_ponens` passes the lint. *governance rung
  shipped; semantic edge remains open* (2026-08-08)

- **Retrieval can advance state without promoting knowledge.** A VERIFIED
  RETRIEVE transition now means the exact store operation succeeded; its six
  De-Morgan results retain distinct statuses, including a derived corpus node,
  mechanically verified structural/decomposition records, and a PROVEN Lean
  artifact summary. The subsequent POINT binds an item id, not an invented
  truth. *harness invariant, executable* (2026-08-08)

- **A pointable address is not an answer certificate.** The first adapter
  allowed any retrieved position to clear any UNKNOWN; modus ponens could
  therefore “answer” a De-Morgan request. A first correction rechecked the
  pending key against item aliases, but review then showed that `a` is an exact
  alias in many unrelated lexica. POINT now additionally requires matching
  corpus/lexicon/proof views to resolve to one corpus owner. Ambiguous context
  remains retrievable but cannot answer. *two review-found vacuities,
  corrected* (2026-08-08)

- **UNKNOWN is a live frame judgment, not a session-start label.** A pending
  retrieval literal can become VERIFIED or REFUTED after an accepted frame
  assertion. Keeping only its original UNKNOWN evidence allowed a later POINT
  to clear a stale need. The adapter now retains and re-adjudicates the literal;
  a delegated action that resolves it records the VERIFIED/REFUTED result and
  clears the retrieval need. *state-transition invariant, review correction*
  (2026-08-08)

- **Exact-before-neighborhood is binding semantics, not just query order.**
  `Quadratic Formula` exactly names one node while neighborhood-matching
  another node's `quadratic form`. Owner disambiguation must therefore compare
  exact owners only when the selected material matched exactly. *retrieval
  precedence invariant, review correction* (2026-08-08)

- **Retrieval actions cannot rewrite the pending question.** Earlier controls
  allowed context fetched under `quadratic form` to approach a pending
  `Quadratic Formula`, relying on POINT to reject the wrong owner. The final
  contract is stronger: RETRIEVE itself refuses any key not canonically equal
  to the UNKNOWN literal's value; neighborhood widening is internal. *cross-
  query vacuity, review correction* (2026-08-08)

- **Proof retrieval must honor the proof-link schema, not today's examples.**
  Every current `verified_by` entry names a theorem reference, but the schema
  permits an artifact-only link. Review supplied that absent-reference case;
  the loader now counts the whole theorem-bearing artifact instead of
  crashing. *schema-boundary correction* (2026-08-08)

- **A proof link is not PROVEN until its artifact contains applicable proof
  transitions.** An empty JSON artifact is structurally present but supplies
  no machine-checked evidence; nor does an arbitrary file or a row containing
  only a theorem label. The loader now authenticates complete native JSON
  state–tactic–state rows, requires an applicable transition to close to `no
  goals`, requires artifact-only links to identify exactly one theorem, and
  fails closed on malformed evidence. But even a locally closing row may be a
  completed subgoal in a truncated extraction. PROVEN therefore additionally
  requires the existing SHA-256 identity of the committed native extraction;
  structurally valid untrusted artifacts remain VERIFIED. *epistemic
  fail-closed rule, review correction* (2026-08-08)

- **Short algebraic aliases are context, not word-completion prefixes.** A
  truncated `absor` query reverse-matched every lexicon containing `a`, flooding
  its neighborhood with unrelated owners. Reverse-prefix matching now requires
  at least three characters; exact single-symbol retrieval remains possible,
  but cannot masquerade as lexical completion. *neighborhood precision,
  review correction* (2026-08-08)

- **A retrieval key is part of the UNKNOWN, not free policy metadata.** The
  adapter initially allowed callers to pair any unresolved literal with an
  unrelated key, making relevance true only by assertion. Session construction
  now requires the key to be the unresolved literal's value. Retrieval is thus
  verified relative to parsed frame state; whether open language was parsed
  correctly remains a separate capability. *capability-blind correction,
  review-blocking* (2026-08-08)

- **Factory invariants must be verifier invariants when state constructors are
  public.** A caller could bypass the session factory and forge a key/literal
  mismatch directly in the frozen dataclass. RETRIEVE and POINT now recheck the
  relation at the action boundary. *extension-boundary correction* (2026-08-08)

- **Pointable context is a capability and needs provenance checking.** A public
  state constructor could inject a record with plausible aliases and ownership
  but an invented id. POINT now requires exact membership in the authoritative
  store snapshot before binding. *capability-boundary correction* (2026-08-08)

- **Closed-form exactness must preserve operators.** Lexical tokenization made
  multiplication and addition skeletons with the same slots look identical.
  Exact retrieval now preserves punctuation/operators and uses lexical tokens
  only for neighborhood search. *symbolic-equality correction* (2026-08-08)

- **Exact symbolic lookup does not require word tokens.** Operators and
  non-Latin symbols may have no ASCII alphanumeric token at all. Exact alias
  comparison now precedes the neighborhood-token gate. *symbolic-input
  correction* (2026-08-08)

- **Store membership is not retrieval provenance.** Public state could inject
  a genuine item without an accepted RETRIEVE step. Verifier-minted receipts
  now bind the session key, match mode, and admitted item ids; POINT requires
  both the receipt and authoritative membership. *transaction-integrity
  correction* (2026-08-08)

- **A receipt belongs to a session, not merely a verifier.** One verifier may
  host several same-key sessions. Receipt signatures now cover a per-session
  nonce, so admitted context cannot be transplanted between them. *replay
  correction* (2026-08-08)

- **A retrieval receipt belongs to a frame contract too.** Signing only the
  session allowed open-frame context to move into a `frame_local` scope.
  Signatures now cover the immutable `FrameSpec`, preserving its retrieval
  boundary. *scope-replay correction* (2026-08-08)

- **Short exact keys must not become prefixes.** The key `7` is not an answer
  request for `IEEE 754`. Prefix neighborhood matching now requires at least
  three characters on each side; exact short aliases remain exact-only.
  *neighborhood vacuity correction* (2026-08-08)

- **A proof trust root authenticates metadata and bytes together.** A
  byte-identical Lean extraction labeled as another proof system must not
  inherit PROVEN. The native adapter now accepts the pinned digest only with
  the canonical `lean4` system label. *provenance-integrity correction*
  (2026-08-08)

- **Action kind and transition name are both part of the verifier protocol.**
  Dispatching every RETRIEVE as lookup and every POINT as bind allowed unknown
  names to appear as successful audited operations. The adapter now refuses
  names outside its declared vocabulary. *trace-integrity correction*
  (2026-08-08)

- **The external store is load-bearing at the controller level too.** The
  deterministic RETRIEVE→POINT oracle solves with the 702-item local store and
  cannot solve against an empty store: UNKNOWN leaves context unchanged, POINT
  is REFUSED, and ABSTAIN is cited. This is the retrieval adapter's capability-
  blind baseline, not a model-quality result. *negative control* (2026-08-08)

- **One statement id can join five knowledge views without becoming five
  mechanisms.** Querying De Morgan's law returns corpus meaning, lexicon,
  typed/shape group records, decomposition, and native Lean transition counts
  through one interface; a truncated id reaches the same neighborhood only
  after exact lookup misses. *integration, exact + neighborhood* (2026-08-08)

- **Pointability needs source-aware identity, not one universal owner field.**
  Corpus, lexicon, and proof records resolve to a statement; a decomposition
  resolves to its owning statement; a twin-ledger skeleton may identify the
  group itself. Tiered attribution now lets unique report-only keys bind without
  weakening canonical statement precedence. *five-store integration, review
  correction* (2026-08-08)

- **Time reversal is a relation, not an alias.** Five predicted pairs now
  appear at a separately reported mirror level: UNTIL/SINCE,
  EVENTUALLY/ONCE unfolding, NEXT/PREV distribution, future/past duality, and
  response/heraldry. The ordinary shape/typed/family/aliased counts remain
  28/29/28/30, so the new relation adds knowledge without manufacturing an
  equivalence claim. *mirror, 5 groups, predicted-and-landed* (2026-08-08)

- **A mirror must reverse the whole expression, not quotient each head.** The
  first implementation falsely grouped partially reversed nested modalities;
  it also exposed that heraldry/no-deus had kept an outer `ALWAYS` while
  reversing only EVENTUALLY to ONCE. A whole-tree involution initially reduced
  the result to four groups; correcting the past formulas to HISTORICALLY
  restores the fifth. The original five-group implementation is retracted.
  *self-audit, review-blocking correction* (2026-08-08)

- **A response law does not imply its trigger's converse.**
  `G(notices -> F(falls))` does not entail `not notices -> not falls`; the
  scoped cartoon hover is therefore an independently assumed assertion, not a
  derived consequence of the declaration. The false reciprocal links were
  removed before commit. *self-audit, refuted* (2026-08-08)

- **Temporal boundaries are part of the theorem.** SINCE/ONCE unfolding is
  valid here only after fixing PREV to the strong convention (false at trace
  origin); the exact heraldry mirror is correspondingly inclusive because
  ONCE includes now. Strict “prepared earlier” remains a stronger executor
  constraint. Separately, premise persistence must assert `HOLDS(p)`
  positively—an implication from `HOLDS(p)` becomes vacuous at the moment the
  premise disappears. *self-audit, boundary conditions corrected* (2026-08-08)

- **The matcher no longer asserts that strict precedence is reflexive.** The
  false `BEFORE ~ LEQ` alias was removed, strict precedence now uses `LT`, and
  `HEAD_ALGEBRA` records `LT` as the strict part of `LEQ` (and `LEQ` as its
  reflexive closure). No prior twin membership moved, exactly as predicted.
  *self-audit, corrected* (2026-08-08)

- **Groundedness v2 still depends on what surrounds a recursive head.** The
  new SINCE and ONCE unfoldings scored 0.667 and 0.500 rather than the
  predicted 1.000: excluding self-headed constituents does not make their
  remaining compound constituents recognizable. Conversely the
  no-deus-ex-machina instance scored 1.000 rather than 0.500 because exact
  PLANTED/DISCHARGED recurrence and heraldry-pattern coverage ground all of
  it. *prediction missed, metric boundary* (2026-08-08)

- **Scope has its first corpus users.** Cartoon gravity is represented as a
  shared-scope declaration/assertion pair that suspends Newtonian gravity,
  while premise persistence declares a frame-local invariant. These are the
  first authored nodes to exercise the already-live scope validator rather
  than leaving frame semantics in prose. *schema exercised* (2026-08-08)

- **Coulomb's law is Newtonian gravitation.** Same typed skeleton
  `?V = ?P·?V·?V / ?V²` — inverse-square pair coupling; only the names of
  the charges differ. *exact* (2026-08-06)

- **The quantity theory of money is the ideal gas law with its dimensional
  constant suppressed.** `M·V = P·Q` ⊑ `P·V = n·R·T` with bindings
  MONEY→PRESSURE, VELOCITY→VOLUME, PRICE_LEVEL→AMOUNT,
  OUTPUT→CONSTANT·TEMPERATURE. *specialization* (2026-08-07)

- **Compound interest, population growth, and radioactive decay are one
  law.** `?V = ?P·EXP(?P·?V)` after absorbing the decay sign into the free
  rate parameter; at the sign-exact level the family splits into exactly
  the two semantically correct pairs (compounding↔growth,
  discounting↔decay). *family* (2026-08-07)

- **Hooke's law joins Newton's second law, Ohm's law, and circle
  circumference** as one scaled-linear response family once its restoring
  sign is absorbed into stiffness. *family* (2026-08-07)

- **The laws of logic and the laws of sets are one Boolean algebra.** All
  seven lattice laws (De Morgan, distributivity, involution, absorption,
  identity, complement, idempotence) are exact twins over two carriers,
  recorded as reciprocal equivalences. *exact* (2026-08-07)

- **Shannon entropy is Gibbs entropy.** One skeleton
  `?V = −(?P · Σᵢ ?Vᵢ·log ?Vᵢ)`; Boltzmann's k_B and information's 1/ln 2
  land in the same parameter slot — the disciplines differ by a unit
  choice. *exact* (2026-08-07)

- **pH is the surprisal of proton activity.** `pH = −log(activity)` and
  `surprisal = −log(probability)` are typed twins — chemistry has been
  measuring an information quantity all along. Unplanned; found because
  both corpora made honest independent slot declarations. *exact*
  (2026-08-07)

- **A tangent-line linearization is an affine location-scale transform.**
  Calculus's local approximation and statistics' standardization are one
  structure `?V = ?P + ?P·?V`; CAPM and the Keynesian consumption function
  are members too. *exact* (2026-08-06/07)

- **Rate-of-change, speed, density, molarity, and elasticity are one
  ratio archetype** across calculus, physics, chemistry, and economics.
  *exact* (2026-08-06/07)

- **Entropy inclusion-exclusion is set-cardinality inclusion-exclusion**
  (Yeung's I-measure): `H(X∪Y) = H(X)+H(Y)−H(X∩Y)` matches
  `|A∪B| = |A|+|B|−|A∩B|` exactly. *exact* (2026-08-07)

- **Beer-Lambert absorbance generalizes the whole scaled-linear family**
  (set absorptivity to 1) and typed-twins triangle area — a scaled
  bilinear product is one thing whether it measures light attenuation or
  plane regions. *specialization / exact* (2026-08-07)

- **E = mc² is a geometric scaled-quadratic with the roles swapped.** It
  shape-twins circle area / sphere surface (`? = ?·?²`), but the squared
  quantity is the *constant* — the typed layer correctly refuses the
  identification while the shape layer records the kinship. *shape*
  (2026-08-06)

## Informative near-misses (kept deliberately)

- **Our headline depth number was a lucky seed, and pretraining is a
  stabilizer, not a lever.** Running the cold recurrent arm at seed 1
  (0.087 OOD) retired "0.226" as a point estimate: the honest 2-seed
  statement is 0.16 +/- 0.07 (fork verdict intact -- both seeds beat
  lookup/curriculum by an order of magnitude). Masked-skeleton
  pretraining (10e) collapsed that seed spread to 0.029 and lifted the
  weak seed +0.100 while leaving the strong seed roughly unchanged --
  gains the no-single-seed rule can call variance stabilization but not
  mean improvement at n=2. *P-CF5a partial, P-CF5b fired; single-seed
  rule applied to our own result* (2026-08-09)

- **Textbook mutual information does not twin its own I-measure form** —
  call heads are read literally. Shows precisely what adopting a shared
  abstraction (lattice heads) buys. (2026-08-07)

- **Inclusion-exclusion does not twin total probability.** Applying a
  non-idempotent functional (CARD) to idempotent lattice operations is
  what *manufactures* the correction term — the deliberate counterweight
  to idempotence. (2026-08-07)

- **Uniform entropy = Shannon at p=1/N is invisible to the matcher** —
  collapsing a sum is a rewrite, not slot absorption. Same substitution
  takes Gibbs to Boltzmann's S = k·ln W. First motivated test case for a
  rewrite-edge engine. (2026-08-07)

- **Modus ponens does not twin subset transitivity** — same detachment
  shell, different premise heads; LEQ chosen so hypothetical syllogism
  will twin for free when authored. (2026-08-07)

- **Word concatenation correctly refuses the logarithm analogy.**
  `LENGTH(CONCAT(A,B)) = LENGTH(A)+LENGTH(B)` and `LOG(X·Y) = LOG X + LOG Y`
  are both monoid homomorphisms — but the matcher will not twin them,
  because CONCAT is ordered and `·` commutes: the free monoid of morphs
  and the multiplicative reals are different structures sharing only an
  archetype. A refusal that encodes real mathematics. *near-miss*
  (2026-08-07)

- **The derivation/inflection distinction survives total anonymization.**
  `CATEGORY(CONCAT(STEM, X)) = CATEGORY(STEM)` vs `= CATEGORY(X)` differ
  in one argument index after every symbol is erased — the grammar
  distinction is pure structure. *exact-distinction* (2026-08-07)

- **Word-level and phrase-level recursion are one skeleton apart**
  (registered prediction): iterated affixation `CONCAT(CONCAT(s,x),y)`
  and intensifier nesting `MOD(MOD(a,i),j)` differ only in head string —
  authoring the MOD node makes the discrete-infinity-at-every-level
  claim mechanically checkable, pending head aliasing. *prediction*
  (2026-08-07)

- **Counting, entropy, Euler characteristic, and area are one law.** The
  inclusion-exclusion skeleton `CARD(JOIN(A,B)) = CARD(A)+CARD(B)−CARD(MEET(A,B))`
  fires as a typed twin across set theory, information theory, algebraic
  topology, and geospatial topology — four valuations on lattices,
  differing only in what they count; modularity is the only property the
  identity uses. *exact, 4 disciplines* (2026-08-07)

- **The Fundamental Theorem of Calculus is Stokes' theorem in dimension
  1** — the 0-form Stokes case and FTC's evaluation part share one typed
  skeleton, found by the matcher rather than asserted. *exact* (2026-08-07)

- **The flat metric line element is the Pythagorean theorem.**
  `ds² = du² + dv²` typed-twins `a² + b² = c²` — differential geometry's
  local statement is the school theorem. *exact* (2026-08-07)

- **Betti alternating sums are total-probability decompositions** (with
  a caveat: the (−1)^i signs collapse into the same parameter slot that
  holds probability weights — structural kinship, semantic distance
  recorded). *exact-with-caveat* (2026-08-07)

- **χ = 2−2g shape-twins the thermodynamic free energies** and joins the
  affine family only after sign absorption — correctly, since
  χ-decreasing-in-genus is a convention. *family/shape* (2026-08-07)

- **A prediction formally cashed:** seed_logic fixed the LEQ head so
  future transitivity statements would twin for free; geospatial
  containment transitivity fired against subset transitivity with the
  target defined before the source existed. *exact, predicted*
  (2026-08-07)

- **The plainest specializations are provably invisible to specialize.py**
  (near-miss upgraded to load-bearing): Euler's polyhedron formula IS
  combinatorial χ at χ=2, and DE-9IM disjointness IS the complement law —
  match() succeeds on both, the requires-absorption filter drops both.
  Direct probes on record. (2026-08-07)

- **GRPO's advantage is the z-score.** DeepSeek's 2024 group-relative
  advantage `(R − mean)/std` fired as an emergent typed twin of
  probstat's z-standardization — frontier RLHF machinery is a
  century-old statistical transform. *exact* (2026-08-07)

- **LLM sampling is exponential decay.** The Boltzmann/softmax factor
  joins the family of radioactive decay, compound interest, and
  discounting (5 nodes, 4 disciplines) — temperature sampling and
  half-lives are one parametric family. *family* (2026-08-07)

- **The PPO probability ratio is a rate.** It joins rate-of-change,
  speed, density, molarity, and elasticity — the ratio family now spans
  6 nodes in 5 disciplines including RL. *exact* (2026-08-07)

- **Linear regression generalizes the Mamba/S4 state update.** SLR ⊒
  the linear SSM recurrence with intercept→0 and the noise slot
  absorbing the transition term — the 1900s statistical model contains
  the 2020s sequence architecture. *specialization* (2026-08-07)

- **Affine location-scale generalizes LoRA.** `W = W₀ + s·BA` is the
  statistics transform with the scale factored low-rank. *specialization*
  (2026-08-07)

- **Gradient descent shape-twins the free energies** and typed-twins the
  KL-regularized RLHF objective — optimization steps and thermodynamic
  potentials share the value-minus-scaled-quantity skeleton. *shape/exact*
  (2026-08-07)

- **The type system sees the gating innovation.** mLSTM does not twin
  the SSM precisely because its gates are variable-like where SSM
  coefficients are parameter-like — the matcher's refusal isolates
  exactly what xLSTM added. Likewise gradient descent misses the affine
  family by one slot category: descent updates a variable, affine
  shifts by a parameter. *near-miss, load-bearing* (2026-08-07)

- **Statements are now readable as constructs of named forms**
  (derivational composition, scripts/decompose.py): 135/151 statements
  decompose into known constituents; 117 contain a constituent that IS
  another statement's expression side. The SSM update reads out as two
  scaled-linear constituents (the Ohm/circumference form, recurring in
  28 statements) joined by +; the Euler-characteristic surface formula
  contains Hooke's law's expression side; the valuation identity's
  constituents are the other valuation statements. Commitment #1 of the
  concept-token design — forms as constructs of forms — is mechanical.
  *derivational* (2026-08-07)

- **Gradient descent is Euler's method** — explicit Euler on the gradient
  flow, fired as a family twin; every training loop runs 1768
  mathematics. Newton's method *correctly* misses the family: its inv()
  is the second-order information, isolated by the refusal. *family +
  near-miss* (2026-08-07)

- **The trapezoidal rule is the trapezoid area formula** — exact typed
  twin across numerical analysis and geometry; the quadrature rule IS
  the shape it sums. *exact* (2026-08-07)

- **Bézier evaluation, barycentric reconstruction, total probability,
  and Betti sums are one weighted-sum law** (4 disciplines). *exact*
  (2026-08-07)

- **Newton's correction term is a rate** — invisible to whole-statement
  twinning, read out by decomposition as the ratio family's expression
  side (11 statements). And fixed-point iteration vs Brouwer's theorem:
  two tools, one pair, opposite correct answers (shared constituent,
  provably not twins). *derivational* (2026-08-07)

- **Time is an order structure.** Temporal precedence transitivity
  typed-twins subset transitivity and geospatial containment
  transitivity — before/⊆/within are one law across three disciplines.
  *exact (authored-to-match convention, surviving three corpora)*
  (2026-08-07)

- **Fiction obeys logic.** The narrative frame-consistency law
  typed-twins the machine-checked Boolean complement laws — story
  coherence IS non-contradiction, so the fictional-frame design
  inherits a proven theorem rather than a style rule. *exact*
  (2026-08-07)

- **Frame axioms and their first executor are implemented; full temporal logic
  is not.** The corpus already
  contains the story sequence, its setup/complication/resolution decomposition,
  narrative causality, Chekhov-style liveness, and frame consistency. The
  matcher already connects the last two to temporal response and Boolean
  non-contradiction. The runtime now opens schema-declared scope, evaluates
  declarations/assertions against a frame-local ladder, and prevents local
  truths from leaking on exit. Its next cut makes Chekhov's law executable as
  finite obligation accounting: a visible plant registers one element, only a
  matching discharge closes it, and a frame with an outstanding element
  REFUSES to close. The first implementation's hidden ledger passed without a
  plant in the rendered setup; the vacuity audit caught that, so story plants
  must now alter the visible beat and discharges must cite resolution text.
  Independent review then found late/unrelated plants and prose duplication on
  repeated plants; plants are now setup-only, evidence names the bound element,
  and idempotence covers both symbolic and rendered state.
  This evaluates the authored future-facing law at frame close; it is not a
  general LTL checker and does not enforce the unauthored past converse. The
  machine anchor remains structural — the matching Boolean law has a Lean
  proof — rather than a claim that story execution itself is Lean-proved.
  *status progression: declarative layer + scope executor + finite Chekhov
  obligations shipped* (2026-08-08)

- **One controller can carry a real proof trace and a story trace, but that is
  an interface result, not learned generalization.** A deterministic sequence
  policy drove the same bounded propose/verify/repeat loop through three
  contiguous state–tactic–state transitions from the committed Lean extraction
  (`intro hp`, `left`, `exact hp` → `no goals`) and through setup, complication,
  and resolution for the golden chicken. Negative controls were load-bearing:
  unrecorded tactics, altered Lean state, out-of-order beats, and a silver-trait
  contradiction all fail; a rejected story branch leaves no premise behind and
  a valid branch recovers. The remaining boundary is explicit: replay is not
  PyPantograph search, the story adapter is a small executable subset of the
  frame design, and no weights chose an action. *oracle integration baseline,
  16/16 contract tests, including mutable extension boundaries and adversarial
  epistemic-status inputs* (2026-08-08)

- **Temporal duality is the infinitary De Morgan.** ALWAYS/EVENTUALLY
  are MEET/JOIN over suffix chains; the twin is blocked by heads and
  arity but carried honestly on the shared archetype. *near-miss,
  channeled* (2026-08-07)

- **Idempotence and involution differ by a fixed point, not a head.**
  ALWAYS(ALWAYS(P)) keeps its base where NEG(NEG(P)) cancels — the
  matcher's refusal isolates the semantic distinction exactly.
  *near-miss, load-bearing* (2026-08-07)

- **An instance can grade less grounded than its pattern.** Chekhov's
  gun (0.000) vs its own response-pattern abstraction (0.500):
  instantiated heads hide pattern membership — a measured groundedness
  pathology, filed with the recursive-definition self-reference case
  (until-unfolding, 0.000). *pathology* (2026-08-07)

- **Consequence, subset, containment, and precedence are one law.**
  Hypothetical syllogism joined the transitivity family — four
  disciplines whose carriers share nothing but a partial order,
  categorically different from the Boolean twins (one algebra read
  twice): here the shared thing is only the order axioms. *exact, 4
  disciplines, predicted-and-landed* (2026-08-07)

- **Mixture distributions, linear interpolation, and de Casteljau are
  one convex combination** (3 disciplines) — and the same node's
  K-component spelling belongs to the *weighted-sum* family instead:
  the sharpest measured case of spelling-dependent twin membership,
  since both spellings match, just not each other. *exact + pathology*
  (2026-08-07)

- **The zero morph lands where a linguist would put it.** With CONCAT's
  declared identity (∅ from zero_morpheme_identity), iterated
  affixation specializes to plain affixation via the INNER position —
  `CONCAT(CONCAT(stem, ∅), suffix)` — the matcher independently
  choosing the linguistically standard analysis over the registered
  prediction's outer-position guess. *specialization, looseness 0*
  (2026-08-07)

- **The Boolean corpora gain their first specialization structure**:
  absorption ⊒ idempotence via JOIN's identity element (BOT), two edges
  cross-corpus — the lattice laws now relate derivationally, not just
  as twins. *specialization* (2026-08-07)

- **The audit caught our own table asserting a falsehood.** The
  order_le alias class (BEFORE~LEQ) declares a reflexive order that
  strict_precedence_asymmetry makes asymmetric — deriving ⊥ at x = x —
  inert only because the class yields zero groups. Found by the scope
  design's measurement pass; fix queued (LT strict head, the
  strict/reflexive relation into HEAD_ALGEBRA). The epistemic ladder's
  REFUTED rung, applied to the tooling itself. *self-audit* (2026-08-07)

- **WordNet increases lexical reach without acquiring epistemic authority.**
  P-CF6 fired on its capability-blind control. Eight request terms absent from
  the five committed retrieval stores (0/8) reached their expected corpus
  owner through Open English WordNet same-synset aliases (8/8). This was
  context expansion only: the frame executor's UNKNOWN verdict/evidence
  changed 0/8 times across the real verifier path, and an injected mutation
  was detected 8/8. WordNet records stayed `empirical` beside formal/proven
  neighbors. Safe binding was 7/8: the two senses supporting `perseverance` →
  `persistence` remain context until disambiguated. The useful boundary
  is sharper than “add a dictionary”: lexical coordination can propose where
  to look without becoming evidence that the pointed formal statement is
  true. *retrieval / epistemic boundary* (2026-08-09)
