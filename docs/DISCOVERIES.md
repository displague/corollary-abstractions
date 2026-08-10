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

- **A digest supplied by the claimant is a checksum, not a trust root; a
  post-hoc digest is detection, not containment.** The first PROVEN-WRITE
  implementation executed candidate Python in a scratch cwd, screened obvious
  paths, and digested the repository afterward. Independent review showed both
  category errors directly: the candidate could supply arbitrary proof bytes
  plus their matching digest, and code could damage the real repository before
  the after-digest reported the loss. The corrected boundary is declarative:
  candidate seed text must be the exact AST of a canonical literal-JSON
  envelope and is never executed; trusted code materializes it. Proof bytes
  must also match the independently maintained
  `prover/proof-artifact-manifest.json`, and one immutable snapshot feeds the
  digest, closure, trace, and correspondence checks. The reusable rule is that
  evidence and the authority authenticating it cannot arrive through the same
  untrusted channel. A later review added the source-of-truth corollary: a
  materialized corpus is not evidence that a replacement seed preserves every
  output of the original (one seed can own several corpora), so the v0.7 lane
  accepts new seed/new corpus pairs only. *v0.7 item 3 re-review; regressions in
  `tests/test_write_stage.py`* (2026-08-10)

- **Signing the envelope would have made the acceptance test prove nothing.**
  ROADMAP-v0.7 item 2's gate is "a stale or forged pre-restart binding is
  refused". The natural implementation puts a MAC over the whole session file,
  and it passes the gate — for the wrong reason. A forged binding inside a
  signed envelope is caught *by the envelope*, so the test says nothing about
  whether **bindings** authenticate, which is the property being claimed. The
  same move would have inverted the trust story the harness had been building,
  in which public state is public and untrusted and authority comes from
  per-record signatures plus verifier-private ledgers. The shipped session file
  therefore carries no MAC at all: anyone may edit it, the forgery test writes
  its binding *into the file* and reads it back normally, the restore succeeds,
  and the record is refused by its own signature. The general lesson is about
  test design more than cryptography — **a guard placed one layer above the
  property under test makes the test vacuous while making it pass**, and the
  only reliable defence is to forbid the guard in the registered prediction
  before the code exists (P-DS2 did). *Found while designing v0.7 item 2;
  regression: `tests/test_session_durability.py::PreRestartBindingTests::
  test_forged_pre_restart_binding_is_refused_by_name`* (2026-08-10)

- **A signature cannot see a replay; only a counter outside the message can.**
  Every other refusal in the durable-session design falls out of a MAC:
  tamper with a binding, a ledger, a key id, and the check fails. Rolling the
  ledger *back* does not. An earlier snapshot is authentic in every respect —
  correct key, correct session, correct owner, valid signature — and its only
  defect is being out of date, which is not a property any message can carry
  about itself. The fix is a monotone per-scope counter kept in the **private
  keyfile**, precisely because the public snapshot cannot lower what it cannot
  see. Two ordering details turned out to be load-bearing and are easy to get
  backwards: the signature must be checked *before* the counter is consulted
  (otherwise a forged snapshot claiming sequence 10⁹ locks the real owner out —
  a denial of service handed over free), and the admission test must be `>=`
  rather than `==` (otherwise a session that crashed between export and import
  is bricked). The `>=` buys rollback refusal and explicitly does not buy fork
  refusal; that trade is filed rather than hidden. *Registered in advance as
  P-DS5, the prediction most likely to miss; regressions:
  `LedgerAttackTests::test_ledger_rollback_is_refused` and
  `::test_forged_ledger_cannot_advance_the_counter`* (2026-08-10)

- **A lifetime that is stored is not a lifetime; it is a suggestion.** The
  first design gave `UserBinding.lifetime` the obvious job of holding the
  binding's current state, `session` becoming `superseded` when replaced. That
  is unusable as authority: the field lives in public state, so anyone holding
  the tuple writes it back. The shipped protocol splits **declared** from
  **effective** — the declared lifetime is chosen once by the trusted return
  channel and covered by the MAC, and `superseded`/`expired` are *recomputed on
  every read* from the private ledgers and the current goal, stored nowhere.
  A creating authority cannot declare them at all, because an answer that
  arrives already dead is a stranger state than the protocol wants to
  represent. The same split resolved what "durable" could mean operationally:
  a durable binding is signed under an **owner-scoped** key with neither
  session id nor frame spec in its payload, which is exactly what lets it cross
  into a new conversation and exactly why it is not frame-isolated. Reach and
  isolation are the trade, and the protocol table states it rather than leaving
  it to be discovered. *v0.7 item 2; `scripts/lifetimes.py`* (2026-08-10)

- **Durable state needs a durable place to record its retirement.** Probing
  this item's own fixes turned up a wrong-answer bug the item had introduced:
  supersession was filed on the verifier instance, which is correct for a
  session-scoped answer (it travels in that session's snapshot) and wrong for a
  durable one, whose whole point is being valid in conversations that instance
  will never meet. A durable answer replaced in session A came back to life in
  session B. The general shape is worth keeping: **whenever state is given a
  longer life than the thing that records its death, the death gets lost**, and
  the fix is not a wider check but moving the record to something that lives at
  least as long — here, the key ring, the design's only durable private state.
  *Found by adversarial self-review of v0.7 item 2, after the acceptance
  scenario was already green; regression:
  `LifetimeProtocolTests::test_durable_supersession_is_filed_under_the_owner_scope`*
  (2026-08-10)

- **A refusal with the wrong stated reason teaches the wrong invariant.** A
  session file's header carries convenience copies of the session id and owner
  that the state also holds. Rewriting only the *inner* `user_frame.owner` left
  the ledger check satisfied and pushed the whole disagreement onto the
  per-binding signatures — which did refuse it, so nothing was exploitable.
  But it was refused as a **forgery** when the actual defect was an
  inconsistent envelope, and a reader who traced that refusal would learn that
  the binding scheme guards envelope consistency, which it does not. The repair
  is not a stronger check but a check *in the right place*. Recorded because
  "the attack failed" is a weaker result than it looks when the reason is an
  accident of layering. *v0.7 item 2 self-review; regression:
  `LedgerAttackTests::test_header_may_not_disagree_with_the_state_it_carries`*
  (2026-08-10)
- **A shared search protocol can port perfectly and carry no lever with it.**
  ROADMAP-v0.7 item 1 asked for the same policy protocol over story actions
  "before claiming a general controller". It ports exactly: the identical
  `SearchController`, the identical ranker/argument-generator split, domain
  weights over the identical architecture, a disjoint vocabulary, and the
  frame verifier holding the same sole-authority position Lean holds. Every
  held-out brief solves. And the best-to-worst spread between six ranking arms
  on any brief is **1.07%** (373 vs 377 proposals) against **65.6%** on the
  proof side, with every arm expanding exactly 32 nodes. The cause is not the
  weights and not the domain's difficulty; it is the interaction of two
  choices that looked independent. Breadth-first search expands a node's FULL
  candidate list, and the story grammar admits exactly one legal ordering at
  depth five — so every node above the solution is expanded whatever order the
  ranker proposes, and ranking can only save part of one node. On the proof
  side the same controller leaves real headroom because solutions sit at
  depth 2-4 with many nodes per level, so a good order reaches a solving node
  *earlier in its level*. The transferable lesson is that "we ran the same
  protocol in a second domain" is a claim about plumbing, and the thing worth
  claiming — that ranking buys something — has to be measured separately in
  each domain, because the search regime, not the policy, decides whether
  there is anything for a ranking to buy.

- **Off the winning path is not the same as dead.** The first proof/story
  curve artifact classified every accepted transition outside the first BFS
  solution as a dead branch. That silently included siblings still waiting in
  the frontier when another branch solved. Independent review blocked the
  resulting 1,552-branch claim. The repaired controller records which child
  states were actually expanded and closes a branch only when its complete
  queued subtree was exhausted without proof. The valid proof count is 227,
  not 1,552; story runs preserve 96 closed transitions per arm, not 496. The
  substantive result survives on stronger evidence: learned pooled re-proposal
  share is 0.2063 versus syntax's 0.2053, no measurable avoidance. The general
  rule is broader than search: **a negative outcome needs evidence of
  exhaustion; non-selection only proves that something else finished first.**
  *v0.7 item 1 post-rebase adversarial review; regression:
  `SearchControllerTests::test_queued_but_unexpanded_sibling_is_not_called_dead`*
  (2026-08-10)

- **The learned ranker overtook the baseline that beat it and lost anyway.**
  v0.6 publicly retracted its live learned-gain claim when a state-blind
  frequency order solved its one theorem in 64 proposals against a learned
  mean of 65.0. Over 24 held-out theorems the same three shipped checkpoints
  now average 49.00 proposals against that frequency order's 51.58 — the
  retraction's specific comparison reversed with breadth. The verdict did not
  move, because the arm added this cycle is neither: a closed-form
  syntax-aware order reading the rendered goal takes 48.29, solves 21/24 at
  the middle budget against the learned mean of 19.33. In the one recorded,
  fixed-order host run it also finishes sooner, but that timing evidence is
  observational rather than counterbalanced. Two things follow. First, a negative result stated
  against one baseline is only as durable as that baseline — "learned loses"
  survived here, but "learned loses to frequency" did not. Second, the
  cheapest strong control is often the one nobody wrote yet: the syntax arm is
  forty lines of rules over text the verifier already renders.

- **Wall clock and proposal count can disagree, but one fixed-order run cannot
  explain why.** The learned arms need fewer Lean calls than arbitrary and
  frequency yet finish later in this recorded host run: at 0.02 s the blind
  arms solve 17/24 and learned solves 14/13/14. The first write-up attributed
  that gap to forward-pass cost. Independent review correctly narrowed it:
  fixed arm order and one sample leave warm-up and host drift confounded. The
  useful result is that proposal count is not a latency proxy; a causal timing
  claim needs repeated randomized or counterbalanced runs.

- **PyPantograph's Windows project blocker was a call that did not have to
  happen.** `prover/FEASIBILITY.md` recorded native project loading as broken
  because PyPantograph 0.3.15 resolves `LEAN_PATH` by shelling out to POSIX
  `printenv`. Reading `server.py` rather than patching it showed the guard is
  `if project_path and not lean_path` — supplying the path explicitly means
  the call never runs. Native, no fork, no patch, and a project-import family
  whose propositions an `Init`-only server refuses to elaborate at all. Worth
  keeping as a habit: a dependency's "unsupported on this platform" is often
  one conditional, and the conditional is usually cheaper to read than the
  workaround is to build.

- **A record can enter at the right rung and still usurp the wrong
  authority.** The whole contract around external retrieval is "a tool
  transaction proves what was fetched, not that its content is true", which
  reads as a *status* constraint — keep the record at `empirical`, and the
  ladder is safe. It is not sufficient. An observation file whose
  `observation_id` was set to a committed statement id bound that statement's
  UNKNOWN slot the moment a caller invoked the tool rung directly. The record
  never claimed to be `derived`; every status assertion in the suite passed.
  What it took was the *right to answer that key*, which the exact rung
  already owned. The miss chain would never have reached the tool rung for
  that key — but a verifier that depends on the policy walking the ladder in
  order has delegated its authority to the policy. The repair puts the
  outranking test where POINT is adjudicated, not where the chain is walked.
  The general lesson is that an epistemic ladder needs two independent guards
  — one on what a record may *claim*, one on what it may *answer* — and that
  a "rank" ordering only constrains the second if it is enforced at the
  binding boundary. *Found by adversarial self-review of v0.7 item 6, after
  all six deliverables' own tests were green; regression:
  `tests/test_retrieval_tools.py::ObservationAdapterTests::
  test_outside_record_cannot_answer_a_slot_a_committed_record_owns`*
  (2026-08-09)

  **CORRECTION (2026-08-10, external review).** The sentence originally
  printed here — "an external record binds only if nothing committed and
  nothing derivable matches the key at all" — was **false when written**, and
  the way it was false is the more useful finding. It described the *code*
  accurately: the outranking test consulted `item_match_mode` over
  `items + derivations`. It did not describe the *store*, because the WordNet
  synonym bridge reaches committed records through shared synset members,
  and no alias comparison can see that. With an archive loaded, one TOOL
  transaction emitted `[corpus:proven, wordnet:empirical,
  observation:conjectured]` for a single key and POINT bound **any** of the
  three: a conjectured outside note answered the slot a proven statement
  answers. A synset id impersonation (`observation_id: "a-n"`) bound for the
  same reason from the other side — a synset id is not a lemma, so the key
  reached nothing and looked unowned. The claim is now true, and true because
  the test enumerates the doors rather than describing one: alias,
  twin_ledger, WordNet bridge, synset-id impersonation, and the original
  `observation_id` case each have their own regression in
  `ObservationAuthorityDoorTests`. **The lesson worth more than the fix: the
  author's own repair was the unprobed boundary.** A guard written in
  response to a finding gets tested against *that* finding's path, and the
  test passes, and the passing test is then read as covering the guard. It
  covers one door. The discipline that follows is to enumerate every way a
  key can be *reached* before claiming what may *answer* it, and to write one
  regression per way rather than one per bug.

- **A prediction can be adjudicated FIRED while its own stated miss
  condition has already fired.** P-RT6 (session pruning) named its miss in
  advance and in writing: "*Miss* if pruning refuses a branch that would
  otherwise have been VERIFIED." The delivering commit recorded it FIRED. It
  had missed. `RetrievalVerifier.state_key` delegated its frame half to
  `FrameAssertionVerifier.state_key`, which keys on the frame's **name** plus
  its asserted claim ids, obligations and closed flag — omitting
  `declarations`, `suspends` and `owner`. Two same-named frames with
  contradictory premises therefore shared a pruning key, so a REFUTED dead
  end in one returned REFUSED for the other, whose branch evaluated fresh was
  VERIFIED; in belief frames that is Sally's dead end refusing Anne's branch
  and citing Sally's premise as the reason. The delegation is correct where
  it lives — `Controller.run`'s `rejected` set is run-local and one run holds
  one frame — and it is unchanged in `frames.py`; what was wrong was
  inheriting a run-local key for evidence that deliberately outlives the run.
  The mechanism of the mis-adjudication is the part to keep: all three cases
  the commit *did* exercise (a second dispatcher hop, another session, an
  advanced state) are cases where the key is supposed to differ or to match,
  and **none of them constructs two states that must not share a key**.
  Confirming a cache's hits is not testing a cache; the miss condition was
  about its collisions, and no probe went there. A registered prediction only
  does its job if something deliberately walks at its *miss* clause — writing
  the clause is not the same as testing it. Re-adjudicated MISSED-then-repaired
  (`repr(state.frame.spec)` joins the key, the same frame scope receipts are
  signed against); regressions:
  `tests/test_retrieval_tools.py::SessionPruningTests::
  test_same_named_frames_with_contradictory_premises_do_not_share_a_prune`
  and `::test_same_named_belief_frames_of_different_owners_do_not_share_a_prune`.
  *Found by external adversarial review of v0.7 item 6.* (2026-08-10)

- **Ranking a result set is safe exactly when ties keep the old order.**
  Adding a relevance score to neighborhood retrieval looked like a
  behaviour change waiting to happen: 339 committed tests bind by *position*,
  and several assert that POINT at position 0 verifies. It changed nothing.
  The reason is structural rather than lucky: the committed sources
  (corpus, lexicon, twin ledger, decomposition, proof) all alias the same
  statement id and title, so for any key they score **identically**, and a
  sort keyed on `(-score, source_order, item_id)` degenerates to the
  pre-existing order within every tie group. Ranking only reorders material
  that genuinely differs in overlap. Registered as P-RT3 before running, and
  it fired with zero test edits — which is the useful form of the result,
  because "ranking is a refinement of the old order" is a property a future
  scorer must preserve, not a coincidence to rediscover. (2026-08-09)

- **A representation borrowed from a matcher smuggled its assumptions into a
  proof gate, and a true theorem certified a false claim.** The twin matcher
  folds every parameter-like slot into one class `P`, which is exactly right
  for its question — "do these two statements have the same shape?" — and
  asserts nothing about truth. The correspondence check reused that front end
  on purpose, so that a proof link would be judged by the same grammar the
  corpus is grouped by rather than by a private re-implementation. The reuse
  was the right call and it carried one wrong assumption across the boundary:
  a lattice constant is not a placeholder. Under one shared class,
  `MEET(PROP1, TRUTH) = TRUTH` and `MEET(PROP1, FALSITY) = FALSITY` are the
  same skeleton, so a machine-checked Lean proof of `P ∧ ⊥ ↔ ⊥` — a TRUE
  theorem — adjudicated CORRESPONDS against the canonical claim
  `P and true = true` — a FALSE one — via the *canonical* route, and the WRITE
  gate staged it with all fourteen checks PASS. Nothing was bypassed; the
  evidence a gate consumed was weaker than the gate itself, which is the
  failure mode that survives review precisely because every check is green.
  The fix had to be narrower than the obvious one: keying constants by
  SPELLING would also close the hole and would silently delete every
  `ambiguous_with` report (the set-theory twins spell TOP as `UNIVERSE`),
  making the check look stronger while being less honest. Poles are
  separated; spellings of one pole are not. *near-miss; PROVEN-gated WRITE
  review* (2026-08-10)

- **The corpus's flagship cross-discipline twin is also the thing that stops
  a proof link from naming an owner.** `logic.boolean_laws.de_morgan_laws`
  and `settheory.boolean_laws.de_morgan_laws` share a skeleton character for
  character, and the logic node's own `statistical_significance` celebrates
  that: "both nodes state one theorem of one Boolean algebra, read once over
  propositions and once over subsets". Regenerating a formal skeleton from a
  Lean theorem and matching it against the citing statement therefore
  certifies STRUCTURE and cannot certify OWNERSHIP: for 12 of the 15
  translatable committed links, at least one other committed statement
  declares the very same skeleton, so a link that moved to the set-theory
  twin would still be CORRESPONDS. The property that makes this corpus
  valuable as an analogy graph is the property that makes structural
  correspondence insufficient as a proof gate. What actually keeps one
  claimant is the older, cheaper rule — `verified_by` theorems are
  exclusively owned — so the two checks are load-bearing together and
  neither is sufficient alone. `scripts/proof_correspondence.py` reports the
  claimants as `ambiguous_with`; the WRITE gate refuses to create new
  instances of the hole. *P-PW6 fired; PROVEN-gated WRITE* (2026-08-09)

- **`equivalent_forms` is a stronger claim than the corpus uses it for, and
  a proof gate reading it inherits the weakness.** A correspondence check
  cannot compare a Lean theorem only to `anonymized_template`: seven of the
  fifteen translatable committed links would be reported MISMATCH, six
  because they cite the DUAL law and one because it cites the bare
  `not(P and not P)` form. Every one of those forms is declared by the citing
  node, so the citations are honest and the naive gate is simply wrong. But
  admitting declared forms admits everything a node files there, and
  `logic.boolean_laws.double_negation` files the ONE-DIRECTIONAL
  `P implies not(not P)` as an "equivalent form" — so a theorem proving only
  that half would be accepted as proving the biconditional. The corpus has
  been using `equivalent_forms` as "related readings a human should see",
  and the first consumer that treats it as "forms this statement asserts"
  turns an editorial convenience into a soundness surface. Recorded rather
  than fixed: narrowing the field is a corpus-wide authoring decision, not a
  change one gate may make. *near-miss; PROVEN-gated WRITE* (2026-08-09)

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

- **Split by provenance, the self-certificate is one constituent wide — and
  absorption, not sibling recurrence, is the graph-wide leak.** Attributing
  every grounded constituent to a channel leaves `data/provability`'s 1.000
  intact but resolves it into `same_corpus` 0.775 + `pattern_absorption`
  0.192 against `external` 0.033: five of six nodes take no external credit
  at all, and the sixth's is a single `IMPLIES⟨?0:V, ?1:V⟩` matching
  `logic.inference.contraposition`. It is the only corpus in 22 where a
  near-perfect aggregate survives with almost nothing from outside its own
  authoring act, though four other corpora are same-corpus-dominant
  (`morphology`, `narrative`, `temporal_logic`, `differential_topology`).
  The unpredicted half is larger: **62 of the graph's 75 pattern-absorption
  constituents absorb a pattern owned outside the absorbing statement's
  discipline**, so slot-swallows-structure is where cross-discipline-looking
  credit concentrates everywhere, not only in the modal corpus. Sharpest
  single case: `temporal.recurrence.until_unfolding`, whose v2 repair from
  0.000 to 1.000 is 3/3 absorption. The `recursive` channel, meanwhile, is
  empty across the whole graph. *GC1–GC5 all fired, including the named
  same-corpus guess; two unpredicted results recorded* (2026-08-09)
  **CORRECTED 2026-08-09 (independent review of the channel-split delivery).
  The text above is the entry as filed and is left standing; three of its
  claims do not survive.**
  1. *The absorption headline is RETRACTED.* "62 of 75" counts each absorbed
     pattern's MOST INDEPENDENT owner; with ALL owners outside the discipline
     it is 36 of 75, the other 26 carrying a same-corpus (25) or prior-corpus
     (1) co-owner. Worse, the inference drawn from it never ran its own
     baseline: the exact channel is 352 of 440 (80.0%) best-owner external and
     162 of 440 (36.8%) all-owner external — statistically a wash against
     absorption's 82.7% / 48.0% under either reading, and 5.7:1 larger by
     absolute count. **Absorption is not where cross-discipline-looking credit
     concentrates; it is where such credit is quarantined**, which was the
     design intent all along. The narrow fact survives (most absorbed patterns
     do have an out-of-discipline owner, and the aggregate silently claimed
     that provenance); the "graph-wide leak" reading does not, and the BACKLOG
     entry that called it "the measurement that would justify" gating the
     pattern channel is demoted accordingly.
  2. *The empty `recursive` channel is a DESIGN consequence, not a data
     observation.* `analyze` subtracts the statement from every owner set, so
     at `min_family >= 2` the only path into the channel — `best_channel`'s
     empty-tally fallback — is unreachable and no corpus of any shape could
     have landed there. (An `owner == sid` branch in `owner_channel` looked
     like the mechanism and took zero calls at every `--min-family`; it is now
     an enforced precondition instead.) The channel is reachable at
     `--min-family 1`: 200 constituents over 105 statements, mean 0.316.
  3. *"Four same-corpus-dominant corpora" is a LOWER bound, and every
     `external` share is an UPPER bound.* Exact constituents take their most
     independent owner and 190 of 440 are multi-owner — all 190 credited
     `external`. Under the least-independent rule graph external falls
     0.535 → 0.246 (352 → 162 constituents), `logic` 0.812 → 0.442, `algebra`
     0.143 → 0.000, and the same-corpus-dominant list grows from 5 corpora to
     12. `channel_summary` now publishes both bounds. The headline is
     rule-invariant: provability's external is 0.033 either way and it is the
     only corpus flagged `self_certifying` under either rule. *GC6 registered
     and fired* (2026-08-09)

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

- **A compound expansion needs no counterpart vocabulary, because the source
  statement is already in the input.** v0.6's analogy lane refused compound
  specialization bindings on the grounds that leaves like `MASS` in
  `*(MASS, ^(SPEED, 2))` have no image in the target statement's vocabulary,
  and inventing one is inventing vocabulary. That framing was the whole
  limitation: B sits in the input beside A and C, so those leaves are pointable
  where they stand, and the target only needs the leaves the twin alignment
  covers to be translated. Replacing the argument with a literal gate — every
  token of D must occur in `A <sep> B <sep> C` — took the lane from one family
  and five targets to **11 families and 398 targets, 376 of them carrying a
  compound expansion**, and the same gate then answered two questions nobody
  had asked it: head-identity collapses are inadmissible (the collapse removes
  the element from B, so it exists only in `HEAD_ALGEBRA`), and B's
  identity-free form beats the re-substituted `*(1, …)` because a `1` the
  matcher supplied is not pointable either. *analogy / representation*
  (2026-08-10)

- **The residual in the grounded analogy lane is a declared slot class, not
  difficulty.** A symbolic solver reading only the token stream reaches
  0.458 / 0.545 / 0.651 exact across the three holdouts. Handing it exactly two
  corpus declarations — each slot's parameter/variable class and the identity
  table — takes the SAME solver to 1.000 on all three, because
  `specialize.Search` gates its arithmetic-identity rule on the class being
  `P`, which no reader of the tokens can recover. This falsified the registered
  P-CS2 ("closed-form from the input alone") in the useful direction: the gap
  between a token reader and a closed form is nameable and small, so the lane
  measures the pointing mechanism and a model result from it may never be
  reported as reasoning. *analogy / closed forms* (2026-08-10)

- **Our own family holdout leaked through the quotient we chose to name it
  with, and the leak WAS the ceiling.** Families are the matcher's TYPED
  skeletons, so `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)` are two families and one
  head/arity shape. Splitting the strongest blind control on that single bit:
  nearest-template replay scores **1.000** on held-out rows whose untyped shape
  is still in training and **0.106** where it is not, and the family holdout's
  headline 0.400 decomposes exactly as `51/155 × 1.000 + 104/155 × 0.106`. The
  discipline holdout's 0.932 is the same effect at 162 of 176 rows. The strict
  ceiling is ≈0.10–0.14. Recorded rather than repaired: an untyped-shape
  holdout is queued, not substituted, because re-rolling a split against a
  ceiling you have already measured is how a lane launders its own result.
  *analogy / split design / self-audit* (2026-08-10)

- **"Distinct families are non-isomorphic" is a tautology when family is
  defined by the isomorphism.** Two of this branch's tests were written to
  check the roadmap's "at least three non-isomorphic structural families" and
  both were initially vacuous — the first because it compared typed keys to
  themselves, the second because its independent witness keyed on operator
  heads and `*` is n-ary after canonicalization, so a two-factor and a
  three-factor product read as one shape. Only the arity-aware, class-blind
  witness can fail, and it is the one that exposed the P-vs-V collision above.
  A test of a definition needs a coarser instrument than the definition.
  *methodology* (2026-08-10)
