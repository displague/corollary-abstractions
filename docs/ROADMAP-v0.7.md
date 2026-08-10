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

**Status: SHIPPED** (branch `feature/proof-curve`). Acceptance is met with
four proof families and one story family; the learned result is a loss, which
this item declared valid in advance. Numbers, tables and the full adjudication
are in `experiments/ANALYSIS.md`; predictions P-PC1–P-PC7 and P-SC1–P-SC6 were
committed with no results attached before the adjudicating runs.

- **One theorem became 24.** `prover/theorems_v1.json` (sha256 `af6f6cb7…`)
  holds 24 held-out theorems in `conjunction` (6), `implication_chain` (7),
  `disjunction` (5) and `project_import` (6). "Held out" is checked against
  `prover/sample_triples.json` by test, not labelled. Versioning rule:
  additions create v2 and v1 is never edited once a curve names its digest.
  Every theorem carries a witness inside the eight registered schemas, never
  shown to a search arm, so an unsolved run is a ranking failure rather than
  an impossible target.
- **Curves, not a trace.** 144 live PyPantograph runs, no replay in any arm,
  budgets 4/8/16/32/64 states x 32/64/128/256/512 proposals plus a wall-clock
  ladder. At the middle rung: syntax-aware blind 21/24, frequency (v0.6's
  winner, rebuilt from the same rows under the same mapper) 20/24, learned
  18/21/19, arbitrary 17/24. All arms reach 24/24 at v0.6's own maximum
  budget. Deriving the curve by thresholding one deterministic maximum-budget
  run was validated by 24 fresh live re-runs at the middle rung, 24/24 in
  agreement.
- **Schema choice is separated from argument generation.**
  `prover/tactic_grammar.py` computes concrete tactic text from the rendered
  goal; a ranker only permutes the eight schemas. Every arm receives the
  identical candidate multiset (asserted by test), so a proposal-count
  difference is a schema-ordering difference. Lean remains sole transition
  authority throughout.
- **Project imports are live and native.** `prover/lean/proofcurve/` is a
  4.29.1-pinned Lake project; an `Init`-only server refuses its propositions
  outright, recorded as a live control. FEASIBILITY landmine 12 is bypassed
  rather than patched — PyPantograph only shells out to POSIX `printenv` when
  `project_path` is supplied without `lean_path`.
- **Exhausted branches preserved, cross-task avoidance measured and absent.**
  The first artifact wrongly counted every accepted off-path sibling as dead,
  including siblings still queued when BFS found a proof. Independent review
  blocked that claim. Frontier-aware accounting now records only 227 accepted
  transitions whose complete queued subtrees were expanded without a proof
  (`clear` 101, the plurality). Under the pooled yardstick the learned arms
  re-propose known-dead signatures at 0.2063 versus syntax's 0.2053: still no
  measurable avoidance, now over branches actually shown dead.
- **Story family: same protocol, no lever.** `experiments/story_curve.py`
  drives eight briefs (four held out by story identity) through the *same*
  `SearchController` with domain weights and a disjoint five-schema
  vocabulary. Every arm solves every brief — and the best-to-worst spread on
  any brief is 1.07% against 65.6% on the proof side, because breadth-first
  search expands every node's full candidate list above a depth-five
  solution. The shared protocol is demonstrated; a general *controller* is
  explicitly not claimed on this evidence.

Open, with evidence, in `docs/BACKLOG.md`: `implication_chain` is vacuous as a
budget discriminator (every arm solves all seven at the lowest rung); the
dead-branch ledger is run-local and cannot feed ranking; the Pantograph 4.29.1
build and the 4.32.2 extraction project still sit on different toolchains, so
live search has never run against the project the training triples came from;
and story-side ranking headroom would need a search change this item forbids.

Reproducibility note (review disclosure): the committed unit suite exercises
the verifier's REFUSED logic against a fake backend and does **not** start
Lean, so "469 green" attests refusal logic, not liveness; the 144-run curve
is reproducible only where PyPantograph + the pinned Lean toolchain are
installed. The recorded `proof_curve.json` carries live provenance (host,
torch/GPU footprint, a real Pantograph elaboration-error dict) and no code
path advances state from a committed transition — liveness rests on that,
not on the suite. Aggregate cross-task shares are recomputable from the
published hit counts and denominators; raw signature attribution still needs
a re-run because `runs[]` omits proposal signatures. The separate leakage
artifact is digest-bound to both theorem set and extraction and measures all
six traversal orders, not a syntax-only proxy.

## 2. Conversation survives process boundaries — SHIPPED

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

### Registered predictions (P-DS, before implementation)

Filed on branch `feature/conversation-durable` before a line of the durable
key ring, the ledger snapshot, or the request grammar existed. Adjudicated in
the shipping commit; a miss is recorded here as prominently as a hit.

- **P-DS1.** The acceptance scenario passes: two owner-isolated sessions
  serialize to public files, the process ends, a fresh process reloads the root
  key from a runtime-owned keyfile, re-derives per-session signing keys,
  re-admits the surviving bindings, and both owners keep revising — with the
  public story still byte-identical and still unasserted.
- **P-DS2.** Every pre-restart binding that was superseded before the snapshot
  is REFUSED after restart with the named reason `binding-superseded`, and a
  binding whose signature was invented is REFUSED as
  `binding-signature-invalid`. Neither refusal may depend on an envelope-level
  MAC over the public session file: the session file is deliberately
  **unsigned public state**, so the refusal has to come from the per-binding
  signature and the restored private ledger or the test is vacuous.
- **P-DS3.** Replaying a pre-restart ASK reply action after restart is REFUSED
  as an already-consumed request, because the consumed-request ledger is
  restored, not re-minted.
- **P-DS4.** Every pre-existing receipt, forgery, replay, and supersession test
  passes **unmodified** — in particular
  `test_second_verifier_cannot_accept_first_verifiers_question`, which requires
  that the default (no keyfile) verifier keeps a per-instance ephemeral root
  key rather than a process-global one.
- **P-DS5.** Rolling the serialized ledger back to a pre-supersession snapshot
  is REFUSED as `ledger-rollback`, because the private keyfile keeps a monotone
  per-session issue counter that the public snapshot cannot lower. This is the
  prediction most likely to miss: a signature alone cannot detect the replay of
  an *earlier, genuinely signed* snapshot, so if the counter is not consulted
  on the restore path the rollback silently succeeds.
- **P-DS6.** The bounded grammar parses every registered form (fill,
  correction, pronoun, owner reference, durable and goal-local declarations,
  abstention) and **degrades to ASK, never to a guess**, on an unregistered
  slot phrase, an unregistered value, or an unresolvable pronoun.
- **P-DS7 (named weakness).** The scheme's weakest point is expected to be
  **root-key file compromise**, not cryptanalysis: derivation is HKDF-SHA256
  from one root secret, so anyone who can read the keyfile can mint any
  binding for any owner in any session, and revocation is the only remedy.
  Second-weakest: nothing in this item prevents **session forking** — two
  processes may import the same snapshot at the same counter value and diverge
  — because refusing that would brick a session that crashed between export
  and import. Both are scoped out explicitly rather than papered over.

### Adjudication (branch `feature/conversation-durable`)

**All seven fired.** `scripts/conversation.py` runs the acceptance transcript;
`tests/test_session_durability.py` (38 tests) and `tests/test_request_grammar.py`
(23 tests) hold it.

- **P-DS1 CONFIRMED.** Alice and Bob serialize to public JSON, the verifiers
  are dropped, a new `SessionKeyRing.open(keyfile)` re-derives per-session
  keys, both sessions restore and keep revising. The public story stays
  byte-identical and `frame.asserted` stays empty on both sides.
- **P-DS2 CONFIRMED, and non-vacuously.** The forgery test writes its binding
  *into the session file* and reads it back: the restore succeeds, the record
  is refused `binding-signature-invalid`, and the rest of the conversation is
  unaffected. The superseded pre-restart binding is refused
  `binding-superseded` even with the public supersession tuple deleted. No
  envelope MAC exists to catch either, by design.
- **P-DS3 CONFIRMED.** A reply action minted before the save is refused after
  the restart as an already-consumed request.
- **P-DS4 CONFIRMED.** All 140 pre-existing retrieval/ASK tests pass
  unmodified, including
  `test_second_verifier_cannot_accept_first_verifiers_question` — the default
  verifier keeps a per-instance ephemeral ring. Full suite 432 → 493.
- **P-DS5 CONFIRMED — the prediction registered as most likely to miss.** A
  genuinely signed pre-supersession snapshot, replayed into a fresh restore, is
  refused `ledger-rollback` by the private monotone counter. A companion test
  checks the *ordering*: the signature is verified before the counter is
  consulted, so a forged snapshot claiming sequence 10⁹ cannot advance the
  high-water mark and lock the real owner out.
- **P-DS6 CONFIRMED.** Eight registered rules fire; six named failure reasons
  refuse; every failure degrades to a verifier-minted ASK with zero bindings
  written. A dedicated test asserts the bound directly — no utterance produces
  a value outside its slot's closed vocabulary.
- **P-DS7 CONFIRMED as written.** Both named weaknesses are real and shipped
  unfixed: root-key file compromise is total (mitigated only by revocation and
  `.gitignore`), and session forking is possible because `admit_sequence` uses
  `>=` rather than `==`. Filed in BACKLOG.

**Two defects found by attacking the fixes, both regressed.** (1) Durable
supersession was filed on the verifier instance, so a durable answer replaced
in one session revived in the next — a wrong-answer bug, now filed in the key
ring. (2) A session file's header could disagree with the state it carried;
the per-binding signatures refused it, but *as a forgery*, teaching the wrong
invariant. Details in `docs/DISCOVERIES.md`.

**Scoped out, deliberately:** pruning evidence is not serialized (a stale
refusal must not outlive the process that earned it), and each export
invalidates every earlier snapshot (the price of counter-based rollback
refusal).

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

**DELIVERED — all four bullets, with two limits that are structural rather than
unfinished.** `scripts/proof_correspondence.py` regenerates a formal skeleton
from every `verified_by` theorem's opening goal and matches it against the
citing statement: **15 CORRESPONDS, 1 UNTRANSLATABLE, 0 MISMATCH** over the 16
committed links, and the capability-blind control the provenance lint passes (a
gravity statement citing `BooleanLaws.modus_ponens`) is MISMATCH here.
`scripts/write_stage.py` stages a PROVEN candidate through path containment,
digest pin, closure, transition trace, exclusive ownership, scratch
regeneration, regeneration confinement, correspondence, structural
unambiguity, schema/link validation, declared-versus-measured matcher delta and
durable byte-identity; VERIFIED stages a content-free review request;
CONJECTURED and frame-local are REFUSED. Refusals write a deterministic,
diffable receipt and leave `data/` byte-identical, asserted by digest on every
path. Nothing accepts — `approval_granted` is always empty.

The two limits: correspondence certifies STRUCTURE, and 12 of the 15
translatable links have a committed structural twin that declares the same
skeleton, so exclusive ownership is what keeps one claimant (`ambiguous_with`
reports the rest; the WRITE gate refuses to create new instances). And
executing a candidate seed is contained by construction and screened, but not
sandboxed. Both are filed in `docs/BACKLOG.md` with the fixes they need.

### Registered predictions (P-PW1 – P-PW8), committed before the adjudicating run

Registered on branch `feature/proven-write` BEFORE `scripts/proof_correspondence.py`
or `scripts/write_stage.py` existed, so nothing below was written with a result in
hand. The declared translatable fragment is fixed here too, so "fail closed on the
rest" cannot be widened after seeing which theorem falls outside it:

> **Declared Lean fragment.** A goal state translates only if every hypothesis
> line binds names at type `Prop`, and the goal is built from `¬`, `∧`, `∨`, `→`,
> `True`, `False`, parenthesisation, those bound propositional names, and at most
> one TOP-LEVEL `↔`. Types, predicates, binders (`∀`, `∃`), arithmetic, nested
> `↔`, and every other Lean term are UNTRANSLATABLE, never MISMATCH.

- **P-PW1 — the link count is 16, not 9.** The brief says "the 9 real corpus
  links". Nine corpus *statements* carry `verified_by`; they cite **16**
  (statement, theorem) links, which is what `tests/test_verified_by.py` already
  asserts. The adjudication below is over all 16.
- **P-PW2 — 15 of 16 CORRESPOND, 1 UNTRANSLATABLE, 0 MISMATCH.** The exception is
  `logic.boolean_laws.de_morgan_laws → BooleanLaws.not_forall_iff_exists_not`,
  whose goal is `α : Type, F : α → Prop ⊢ (¬∀ (x : α), F x) ↔ ∃ x, ¬F x`: it
  binds a type and a predicate and quantifies, so it is outside the declared
  propositional fragment. This is a genuine finding about the corpus's citation
  reach, not a defect to paper over — the node *does* declare a matching
  first-order `equivalent_forms` entry, so the citation is honest and merely
  uncheckable at this rung.
- **P-PW3 — the capability-blind control flips.** `verified_by_errors` passes a
  real gravity statement citing `BooleanLaws.modus_ponens`
  (`tests/test_verified_by.py::test_wrong_statement_valid_theorem_is_capability_blind_control`).
  Correspondence must call
  `physics.gravitation.newton_universal_gravitation → BooleanLaws.modus_ponens`
  **MISMATCH**.
- **P-PW4 — hardest theorems to translate, named in advance.** Hardest, and
  predicted to FAIL: `not_forall_iff_exists_not` (P-PW2). Hardest that is
  predicted to SUCCEED: `non_contradiction` (`⊢ ¬(P ∧ ¬P)`) — a bare asserted
  proposition rather than an `↔`, so it needs the "an asserted proposition `A` is
  the equation `A = TOP`" normalisation, and even then it does **not** match its
  citing node's canonical template `MEET(PROP1, NEG(PROP1)) = FALSITY`; it can
  only match that node's declared `equivalent_forms` entry `not(P and not P)`.
  Third hardest: `excluded_middle`, matching only the declared *dual*.
- **P-PW5 — six links match the declared Boolean DUAL, not the canonical
  template.** `de_morgan_not_or`, `distrib_or_and`, `absorption_or_and`,
  `identity_or_false`, `idempotence_or`, `excluded_middle`. Comparing a
  regenerated skeleton against `anonymized_template` **alone** would therefore
  report six FALSE MISMATCHes and make the check unusable as a gate. The
  correspondence target must be the statement's whole *declared form set*
  (canonical template, its Boolean dual under the declared MEET/JOIN and
  TRUTH/FALSITY involution, and each translatable `equivalent_forms` entry), with
  the matched route recorded per link.
- **P-PW6 — skeleton correspondence cannot decide ownership between structural
  twins.** Every `logic.boolean_laws.*` statement shares its skeleton
  character-for-character with a `settheory.boolean_laws.*` statement (the corpus
  says so itself). Prediction: every translatable boolean-law link reports at
  least one non-owning corpus statement whose declared form set contains the same
  skeleton; the two `logic.inference.*` links report none. Exclusive theorem
  ownership (already enforced by `verified_by_errors`) is what breaks the tie,
  and the pair of checks together still cannot say *which* twin deserves it.
- **P-PW7 — the WRITE gate matrix.** PROVEN + CORRESPONDS → a full staged
  candidate; VERIFIED → a review-request record carrying no candidate content;
  CONJECTURED and frame-local → REFUSED. A PROVEN claim whose correspondence is
  MISMATCH **or** UNTRANSLATABLE → REFUSED, failing closed rather than
  downgrading to review.
- **P-PW8 — no runtime write reaches `data/`, and matcher deltas are predicted,
  not discovered.** A candidate naming `data/logic/nodes.json` as its edit target
  is REFUSED before any filesystem write; `data/` is byte-identical after every
  refusal; and a candidate whose *declared* matcher delta disagrees with the
  delta measured in the scratch checkout is REFUSED even though schema, link, and
  regeneration checks pass.

### Adjudication (corrections attached, never applied to the text above)

| prediction | verdict | result |
|---|---|---|
| P-PW1 | **FIRED** | 16 links from 9 citing statements; the brief's "9" counted statements |
| P-PW2 | **FIRED** | 15 CORRESPONDS / 1 UNTRANSLATABLE / 0 MISMATCH; the exception is `not_forall_iff_exists_not`, refused on its `α : Type` binder |
| P-PW3 | **FIRED** | the gravity control is MISMATCH here and still PASSES the provenance lint (both asserted, in different files) |
| P-PW4 | **FIRED** | `non_contradiction` needed the asserted-proposition normalisation AND matched only `equivalent_forms[non_contradiction]`, exactly as named in advance; `excluded_middle` matched only the dual |
| P-PW5 | **FIRED, with a correction** | the six named dual citations are exactly the six `dual_of_canonical` routes. The prediction's *consequence* was understated: the naive canonical-only reading produces **seven** false MISMATCHes, not six — P-PW4 had already named the seventh (`non_contradiction`) without P-PW5 counting it. Recorded in `test_p_pw5_canonical_template_alone_would_reject_seven`. |
| P-PW6 | **FIRED, with a correction** | the two `logic.inference.*` links have no structural claimant, as predicted. The boolean-law prediction was "every translatable one is ambiguous"; the measurement is **12 of 13**. `non_contradiction` is unambiguous *because* it is carried by a declared variant the set-theory twin does not file — the declared-form-set widening, argued for on other grounds, turns out to be the only thing that disambiguates anything. |
| P-PW7 | **FIRED** | gate matrix as registered, including PROVEN + UNTRANSLATABLE → REFUSED |
| P-PW8 | **FIRED** | `data/logic/nodes.json` as an edit target is refused at the first gate with no filesystem write; `data/` digest is identical before and after every refusal; an undeclared, partial, or wrong matcher delta refuses a candidate that passed every earlier stage |

Two defects the delivery found in itself, both fixed in branch and both
regression-tested: the synthesized TRUTH slot was classed variable-like on the
corpus side and constant-like on the Lean side, so `modus_ponens` matched its
own node through a weaker declared form (visible only because the matched route
is recorded); and the Boolean dual left an undeclared lattice bound in place,
producing the false form `JOIN(P, NEG(P)) = INCONSISTENCY` and making
`narrative.frame.frame_consistency` a spurious claimant of
`BooleanLaws.excluded_middle`.

Adversarial self-review added three gates that were missing: structural
unambiguity for new durable claims, completeness of declared transition rows (a
contentless row matched any artifact row), and containment on the CLI's
`seed_source_path` read.

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

**SHIPPED (the split and the ceilings; the model arm is still open).**
`experiments/corpus_analogy_split.py` replaces the v0.6 lane. Compound
expansions are admitted because B is IN THE INPUT, so its leaves are pointable
where they stand; the gate is literal — every token of D must occur in
`A <sep> B <sep> C` — and it is what refuses head-identity collapses and
decides that B's identity-free form, not the re-substituted `*(1, …)`, is the
target. 914 admitted rows dedup to **398 distinct targets** (2.30x, against
v0.6's 8.0x) over **11 typed families / 10 untyped shapes**, 13 source and 15
target disciplines, **376 of 398 carrying a compound-expansion leaf**. Three
holdout files cut on three keys, deterministic and seedless (pairwise holdout
Jaccard 0.111 / 0.139 / 0.257). Every D is specializer-accepted from C, absent
from every authored template, and absent from its own input as a sequence.

Blind ceilings **0.400 / 0.932 / 0.398** (family / discipline / vocabulary),
all below 1.000. The acceptance criterion has two halves: a *non-trivial*
ceiling below 1.000 (MET — family 0.400 and vocabulary 0.398 are
non-trivial; the discipline 0.932 is disclosed as near-vacuous, not
counted) *and a model result reported against it* (NOT yet met — no model
arm has run; this slice delivers the split and the bar, and item 5 stays
open for the model result against 0.400/0.398). **The v0.6 killer is dead:
the last-slot number rule scores 0.000 / 0.011 / 0.048** (P-CS1 fired).
P-CS1 and P-CS7 fired; P-CS3 half-fired; P-CS4 and P-CS5 missed and are
recorded as missed. (The registered set is P-CS1..5 and P-CS7 — there is no
P-CS6; the numbering skipped it at registration. Noted so the gap in the
sequence is not read as a dropped prediction.)

Two results matter more than the headline:

- **P-CS2's second clause was falsified, usefully.** The task is NOT closed-form
  from the token stream alone (0.458 / 0.545 / 0.651). Adding exactly two corpus
  declarations — each slot's parameter/variable class and the identity table —
  takes the same solver to 1.000 on all three holdouts, because `Search` gates
  its arithmetic-identity rule on the class being `P`. The residual is a named
  piece of declared structure, not difficulty. With it in hand the task is
  closed-form, so this lane measures the POINTING MECHANISM and no model number
  from it may be sold as reasoning.
- **The headline ceiling is inflated by a hole in our own split.** Adversarial
  review found that families are TYPED skeletons, so `*(?1:P, ?2:V)` and
  `*(?1:V, ?2:V)` are two families and one shape. Nearest-template replay
  scores 1.000 exactly where a held-out row's untyped shape is still in
  training and ~0.10 where it is not; the family holdout's 0.400 is exactly
  `51/155 × 1.000 + 104/155 × 0.106`. The **strict ceiling is ≈0.10–0.14**.

Still open, and required before the model arm is worth running:
- an **untyped-shape holdout**, which is the split this one should have been.
  It was NOT substituted after the fact, because re-rolling a split against a
  measured ceiling is how a lane launders its own result;
- the discipline holdout is **near-vacuous** (0.932; 162 of 176 rows keep their
  shape in training) and must not be cited alone as difficulty;
- the three axes are not fully orthogonal — holding out whole families empties
  five of ten disciplines out of training at this corpus size;
- no model has been trained; every number here is a control.

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

**Status: SHIPPED** (branch `feature/retrieval-tools`). All six bullets land in
`scripts/retrieval.py` plus two new modules, with the predictions registered in
`tests/test_retrieval_tools.py` before the implementation ran.

- **Ranked neighborhood.** `text_keys.overlap_score` is the closed form:
  `mean(query_coverage, alias_coverage, exact_token_share)` over the
  best-scoring alias, in `[0, 1]`, `1.0` iff the token sets are equal. Ties
  fall back to the pre-existing `(source, item_id)` order, so ranking refines
  the old order rather than replacing it — no existing binding outcome moved.
  A neighborhood transaction announces the score definition, the admitted
  score range, the cap, and — when the cap bites — the drop count *and* the
  score the cut fell at.
- **Relation traversal.** `UnifiedKnowledgeStore.relation_records` walks one
  hop of the registered set `{antonym, entailment, hypernym}` **per sense**:
  the record id names its origin synset, so two senses of one lemma that reach
  the same target stay two records. Every record is `empirical`, and **no
  relation record is ever bindable** — a hypernym is WordNet's claim about a
  sense, not an answer to the key. Multi-hop traversal is deferred, not
  approximated (BACKLOG).
- **External adapter.** `scripts/observation_adapter.py` reads a declared
  local directory of JSON observations, offline, with no network calls. Each
  observation retains source id, declared `recorded_at`, fetch timestamp, the
  exact query, its rung, and a per-file SHA-256. Rungs above `empirical` are
  refused at load with the file named.
- **Miss chain.** `MISS_CHAIN` + `miss_chain_actions` + `run_miss_chain` make
  the ladder executable: one RETRIEVE per rung, each separately verdicted in
  the controller trace, then ASK, then an EXHAUSTED stop with empty context as
  the explicit abstention. "Derivation" here means *retrieval over the
  committed specialization and decomposition edges* — a relation this repo
  already computed, not a deduction performed at query time.
- **Session pruning.** REFUTED and exhausted (UNKNOWN/ABSTAIN) branches from a
  *returned* run are recorded on the verifier under
  `(session_id, state_key, action fingerprint)`. A second dispatcher hop over
  the same need costs zero store queries. This is the retrieval-side substrate
  for P-IH7 only; the session budget and cycle report remain Phase-1/2
  dispatcher work.
- **Typed protocols.** `Channel` Enum replaces the validated
  `resolution_channel` string (legacy `"store"`/`"user"` callers unchanged);
  `controller.RunCommitter` is a `runtime_checkable` optional protocol that
  owns the `commit_run` name, and `RungStore`/`ObservationSource` are the
  registry-shaped handles §3.2 asks for. All 339 pre-existing tests — receipt,
  forgery, replay, supersession included — pass **unmodified**.

**External review repairs** (2026-08-10), both against claims this section
made:

- The session-pruning bullet above was delivered with **P-RT6 adjudicated
  FIRED while its own stated miss condition had fired.**
  `RetrievalVerifier.state_key` delegated its frame half to
  `FrameAssertionVerifier.state_key`, which keys on the frame *name* and omits
  `declarations`/`suspends`/`owner`, so two same-named frames with
  contradictory premises shared a pruning key and one's REFUTED dead end
  returned REFUSED for the other's VERIFIED branch. Repaired by adding
  `repr(state.frame.spec)` — the same frame scope receipts are signed against
  — and re-adjudicated **MISSED-then-repaired** on the record (DISCOVERIES,
  the prediction module's appended adjudication note, and the repairing
  commit). `frames.py`'s own key is unchanged: it is run-local and correct
  there. One assumption stays open and is now stated rather than implied —
  pruning treats the rung stores as static, which the TOOL rung violates by
  design (BACKLOG, "session pruning assumes a static rung store").
- The self-review's authority fix **covered one door.** POINT's outranking
  test consulted only `item_match_mode` over `items + derivations`, while the
  WordNet synonym bridge reaches committed records through shared synset
  members. One TOOL transaction emitted a proven statement and a conjectured
  outside note under one key, and POINT bound either. The test now also
  consults `_wordnet_resolution` (bridged committed records and the senses
  themselves outrank observations, matching the order `attempt` already
  emits; walked relation records do not, because they can never bind at all)
  and refuses an `observation_id` that names a loaded synset. Five doors,
  five regressions, in `ObservationAuthorityDoorTests`.

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
  **SHIPPED** (`feature/grounding-channels`) — this bullet's scope is the
  split itself, which is delivered; docs/BACKLOG.md's older entry reads HALF
  SHIPPED because its scope also covers the *gate*, which is not shipped and
  is not yet justified. `decompose.py` attributes every grounded constituent
  to one channel and prints a per-corpus table; aggregates unchanged (graph
  mean 0.770, 440 exact / 75 pattern). Regression case reads out as
  `same_corpus` 0.775 + `pattern_absorption` 0.192 vs `external` 0.033, and
  provability is the only corpus flagged `self_certifying` under either owner
  rule. GC1–GC5 all fired; GC6 (registered after review) fired.
  Open:
  - The channels report but do not gate.
  - `reports/decompositions.json` is STALE — it predates the split and lacks
    `channels` / `channel_scores` / `channel_summary`, so the committed report
    and the shipped CLI disagree about the output schema. Closes with the
    report-coherence bullet below.
  - The `recursive` channel is structurally empty at the shipped defaults (a
    consequence of subtracting the statement from every owner set, not a fact
    about `data/`), so the split has four live channels; it is reachable at
    `--min-family 1`.
  - Every per-corpus `external` is an UPPER bound under the most-independent
    owner rule (190 of 440 exact constituents are multi-owner, all credited
    `external`; graph external 0.535 generous vs 0.246 conservative). The
    conservative counterpart is now reported beside it and any future gate
    must be argued against the lower bound.
  - The "62 of 75 absorbed patterns are owned outside the absorbing
    statement's discipline" finding is CORRECTED, not merely unaddressed: it
    is 62/75 by best owner and 36/75 by all owners, and the inference that
    absorption concentrates such credit failed its own baseline — the exact
    channel is 352/440 and 162/440, a wash by rate and 5.7:1 by count.
    Retraction filed in docs/DISCOVERIES.md.
- Add report regeneration/coherence checks parallel to seed coherence. First
  claim on this bullet: `reports/decompositions.json`, stale since the channel
  split (see above and the named BACKLOG item).
- Keep runtime frame ids under `runtime.frames.*`; corpus frames remain node
  references.
- Preserve every registered prediction and attach corrections rather than
  silently editing it.
- Continue mandatory adversarial review at trust boundaries; record both the
  defect and the regression that closes it.

## Release gate

v0.7 is ready only if it contains:

- a multi-theorem live proof-search curve with strong blind baselines;
- a durable authenticated conversation restart or an explicit negative result
  — **MET** (item 2, branch `feature/conversation-durable`);
- one PROVEN-gated staged WRITE rejected or accepted through the full audit;
- a non-trivial multi-family corpus analogy split;
- the visual oracle layer and verifier, even if learned visual arms miss;
- one shared policy protocol demonstrated in both proof and story domains;
- updated assets whose notes explain winners, losers, and controls;
- the complete seed/schema/matcher/specializer/decomposer/test suite green.
