# Roadmap v0.21 — the thing a conversation happens inside of

v0.20 ran two registered experiments and they came back pointing in
opposite directions. The foreign voice — withheld last cycle by its own
control — **cleared**, on a floor deliberately raised above the one it had
failed, and it is served. The brand-new conformance layer — built, wired,
and live — **voided on its own controls**, and it ships with the void
published on the route rather than with a rate.

One discipline produced both. Neither run was re-executed to read better.

That is the inheritance this cycle plans against, and it sets the two
items below. Item 1 is the capability the maintainer has been asking for
in plain words — *a plain conversation, in plain text* — and it finally
has an object to live in. Item 2 is the repair of the claim-kind the
conformance void took away.

## 1. Headline — the session, and plain text landing inside it

**One lane, two designs.** [DESIGN-session-ledger](DESIGN-session-ledger.md)
is the v0.21 course's selection
(receipt: `reports/design-direction-v0.21.json`). It was written as the
**completion** of [DESIGN-plain-input](DESIGN-plain-input.md), the
maintainer-seeded incumbent ROADMAP-v0.20 §5 ordered this course to
adjudicate explicitly. The adjudication is **ADOPTED**, in writing, and
the two documents are scheduled as **one lane** rather than as a headline
and a dependency:

- the **incumbent** supplies the intake — a small model proposes readings
  of plain text, exact code verifies each candidate, and framing that
  cannot be resolved is served as an explicit **supposition** rather than
  guessed;
- the **selection** supplies the object that intake writes into — the
  **session**: a committed, replayable, per-turn journal whose answers
  cite the assumptions they consumed.

**Why they are one lane and not two.** A supposition that does not persist
is a supposition the next turn silently forgets. Today
`scripts/supposition.py:96-107` builds a fresh executor per typed line and
throws the state away, and the served supposition receipt is a single key,
`{"derivation": "session"}` (`scripts/serve_chat.py:1092`). Plain input
without the journal would ship a conversation that cannot remember its own
premises; the journal without plain input would ship a filing cabinet
nobody types into.

**What is genuinely new, stated against what already exists.** Three
committed objects occupy parts of this ground and the design is built on
them by name rather than beside them: `experiments/harness_session.json`
(a recorded session at **leg** granularity, no per-answer digest chain),
`scripts/conversation.py:335-438` (durable session state with a
**keyed-MAC-per-binding** ledger and a monotone anti-rollback counter),
and `experiments/throughput_tasks.json` (the committed model for freezing
a conversation-shaped denominator before the scored party can move it).
What none of them is: **a per-turn journal of a served conversation with a
digest chain over served answers and per-answer citations of the
assumptions each answer consumed.** That — not "no session object exists"
— is the gap, and the design's own first draft got this wrong before
review corrected it (§4).

### 1.1 The construction prerequisites, ordered before any slice

These are **prerequisites, not lanes**: each is committed before the thing
it constrains exists, and item 1's slice 1 does not begin until P3's seal
is frozen.

- **P1 — the finite bound.** Compute and commit the bound on admitted
  commands per template class of the registered grammar. Series 1's FORK
  folded into this: the grammar is finite, so enumeration cost stops being
  an argument and becomes a number.
- **P2 — separator expressibility.** For ten hand-sealed ambiguous
  prompts, does any single admitted command distinguish the rival
  readings under exact evaluation? **If no separator exists for most, the
  clarifying-question arm has nothing to ask** and the conditional-answer
  arm wins by measurement rather than by preference. Committed either way;
  DISCOVERIES gets the answer if it decides the question.
- **P3 — the corpus, sealed ahead of the citer.** Three steps, each frozen
  before the next exists: (1) the **recording protocol** — a 60-session
  cap, a per-session turn cap, the **no-write-gate-turn rule** (a recorded
  session containing a corpus-mutating line is excluded whole and the
  exclusion is counted and published), and the recorder's code digest, all
  committed *before recording begins*; (2) **recording**, capped, with no
  record-until-the-counter-is-met; (3) the **seal** —
  `experiments/session_corpus_seal.json` carrying every journal's
  whole-file digest and an A/B split by the committed hash-derived rule
  reused verbatim from `throughput_tasks.json`. **Half B's first execution
  is the registered run.** Floor: **≥30 sessions and ≥120 turns
  corpus-wide, and ≥36 binding-dependent turns in half B's share alone.** If
  the capped protocol cannot reach the floor, **STOP** and publish
  *"multi-turn binding is rare in practice"* as the cycle's finding.

  > **Corrected 2026-08-26 by the design author.** This line previously read
  > *"Floor in half B's share alone: ≥30 sessions, ≥120 turns, ≥36
  > binding-dependent turns"*, attaching the half-B qualifier to all three
  > clauses. That was a **transcription artifact of this summary**, not the
  > design: in DESIGN-session-ledger §6 P3 the qualifier modifies the final
  > clause only, and the design's own meetability argument was authored for
  > a corpus-wide reading of the first two. Corrected here rather than
  > inherited by the next cycle. The full ruling — and the **retraction** of
  > the wrong justification the preregistration first gave for reading it
  > this way — is `experiments/session_ledger_prereg.json` amendment 4. Both
  > readings' numbers stay published in the corpus seal: half B holds 25
  > sessions, so under the compressed reading this cycle would have stopped.

**A placement rule the design fixes and this roadmap inherits.** Journals
live under `experiments/`, never under `data/` — `check_regeneration.py`
scans `data/` and `data_holdout/` and treats seeds as the source of truth
there, and a recorded session has no seed. v0.19's rotation already paid
for the lesson that an exclusion nobody decided is an exclusion by
accident; this one is decided in advance.

### 1.2 The slices

- **Slice 1 — the object, before any prose.** Journal and recorder wired
  into the existing typed-line session; `suppose …` lines become
  **Assumption** records instead of discarded state. **No learned
  component anywhere in slice 1.** Gate clauses B1–B8 and B10–B12 score
  slice 1.
- **Slice 2 — plain input lands inside the object.** The incumbent's
  proposer, unchanged in trust shape, writes its resolutions and
  suppositions into the same journal. **B9 is registered now and scored
  only when slice 2 exists**; it does not count toward slice 1's verdict.
  P1 and P2 inform the incumbent's open conditional-answer-versus-clarify
  question **before** the proposer is built.

### 1.3 The gate, in summary (the numbers are frozen in the design)

Construction (§7 of the design) — **B1** the seal exists before the
replayer and any edit to a sealed journal voids the run; **B2** unmutated
replay reproduces `answer_bytes_digest` for **every turn the seal
records**, one mismatch is red, with a 30-minute overrun published as a
finding before any verdict is read; **B3** every pin field perturbed
individually yields `stale-environment`, no sampling; **B4** mutating one
**cited** assumption on each binding-dependent turn changes the answer
digest or refuses by type — **100% or red**, misses published
individually; **B5** 60 sham assumptions, **0/60** flips; **B6** ≥30
mutations of live-but-uncited assumptions, **0** flips; **B7** every
refusal turn carries `receipt_digest` with an explicit (possibly empty,
never null) citation list; **B8** tamper detection **20/20** against an
adversary who *repairs the digest chain* — detection must come from the
keyed MACs or the out-of-band seal, never from chain arithmetic; **B10**
stateless equivalence — a turn citing nothing renders byte-identical to
the same line served statelessly; **B11** coherence, `check_regeneration`
green; **B12** citations are **read-derived** and independently
corroborated, one uncorroborated citation is red; **B13** a registered,
arm-blind 20-turn hand audit with a **≥16/20** floor.

Result (§9) — **R1**: on half B's first execution, every
binding-dependent turn's served answer carries its B12-corroborated
citations and replays under B2, with B4–B6 and B10 green and B13 ≥16/20.
If R1 holds the served claim is exactly: *recorded sessions replay, and
conditional answers name the assumptions they consumed.* **Nothing more.**

**The voiding sentence, already frozen:** *if mutating assumptions the
answer does not cite changes the served answer at any nonzero rate, the
replayer is keying on transcript bytes rather than assumption semantics,
and the multi-turn-assumption capability is void for this cycle.* A
perfect B4 beside any B5/B6 flip is a hash of the transcript, not
sensitivity.

**The named residual, priced only partway:** cited-but-inert assumptions.
B12 and B13 narrow it; B13's floor decides whether the claim ships with
the risk **named** or **measured**. The gate proves byte-dependence, and
byte-dependence is the claim — nothing stronger.

## 2. WITNESS — the conformance void's claim-kind successor

**Why it is item 2 and not item 1.** It moves what the system can *prove*,
not what a person can *do*, and the governance record has counselled twice
now against an instrument as a headline. It is scheduled rather than
parked because it is the named repair for a claim this cycle lost.

**What it repairs.** v0.20's conformance run served a `conform` route and
**voided** its own controls, so `NO_COUNTEREXAMPLE_FOUND` certifies
nothing universally — a sampler that finds no counterexample has told you
about its sample. WITNESS replaces sampling with a **discharged
obligation**: per-statement, checker-signed lemmas asserting that the
compiled evaluator and the statement agree over a declared domain.

**Named early rider — the C-E3 supplementary run, under §4.0's
bug-not-result clause.** Before (or alongside) WITNESS's first slice:
fix the substitution step `measure_conformance.py` never called (the
dead code at `:434-438`/`:463` is the committed evidence), then run the
adjudication **once** over the 25 sampled counterexamples the v0.20 run
left unadjudicated — bindings substituted, ground propositions handed
to the pinned checker's decision procedure — as a **supplementary
registered run**: its own dated prereg amendment naming this rider, a
new artifact (`experiments/conformance_ce3_supplement.json`), and
`conformance_run.json` never edited. Whatever it reads is the answer
the gap withheld: agreement strengthens the provisional labels'
credibility, disagreement is the first mechanically-confirmed corpus
error and files accordingly. It cannot un-void v0.20's run and does
not claim to. The late determinism checks (E5's two-run byte-identity
and C-E1's stability arm over the unmutated set) ride the same
commit, each with its dated lateness disclosure per §4.0(2).

**Its preregistration draft exists already**, recorded in the course
receipt at `outcomes.series_1.preregistration_draft` before this roadmap
was written, and quoted here rather than paraphrased:

> **lead:** WITNESS
> **fragment:** quantified linear arithmetic over Z and Q (decidable)
> **artifact:** target_manifest (60 sealed names + 10 out-of-fragment
> decoys, selection-predicate hash, checker pins) + agreement_lemma
> records (obligation forall x in D: eval(S)(x) <-> S(x); verdict in
> {discharged, not_discharged, rejected_trivial}; nontriviality_witness;
> proof + sandbox receipts) + mutant_ledger
> **gate:** B1 manifest sealed first; B2 >=40/60 discharge, all 60
> published; B3 50/50 seeded mutants of DISCHARGED parents rejected
> (49/50 voids); B4 self-comparison obligation must return
> rejected_trivial (one discharge voids the instrument); B5 nontriviality
> witness required; B6 sandbox >=1000 points per discharged evaluator,
> any disagreement voids the slice; B7 cold-machine replay; B8 both
> receipts or nothing; B9 one cycle, partials published
> **voiding_sentence:** If all 60 targets discharge and all 50 mutants are
> rejected on first attempt, or if any decoy discharges, the run is void
> and reports an instrument failure, not a capability
> **residual_risk:** the obligation is built from the compiler's own
> front-end reading of S — a uniform front-end misreading survives every
> clause; only an independent re-reading (second front-end or human
> transcription) prices it, and that is not in the slice

Three things in that draft are worth reading twice. **B4 is a
self-comparison trap**: an obligation comparing the instrument to itself
must come back `rejected_trivial`, and a single discharge voids the whole
instrument — the direct descendant of this cycle's recurring catch,
assertions written so they cannot go red (§4). **B3's 49/50 voids** — too
good is a failure, not a bonus. And the **voiding sentence forbids a clean
sweep**, which is the same shape as C-V3′'s pilot rule: an instrument that
cannot fail cannot confirm.

**Ordering obligation.** *Its compact design lands before its slice.* The
draft above is a course artifact, not a design; the reviewed
`docs/DESIGN-…` document is written and adversarially reviewed **first**,
on the convention ROADMAP-v0.19 and ROADMAP-v0.20 both used, and this
roadmap quotes the reviewed gate clauses once they exist rather than
inventing them in advance.

**And it carries a revival condition for a declined direction.** EXHIBIT
(meaning by discriminating instance) was declined **in writing by its own
series** because it builds on the layer whose conformance run voided. Its
revival condition is recorded in the receipt and is exactly this item: *it
revives only if a non-void conformance instrument ships first.* If WITNESS
clears, EXHIBIT becomes askable; if WITNESS voids, EXHIBIT stays declined
with a second reason.

## 3. Carried, with dependants named

The rule, unchanged: **every carried lane names its dependant, or it
parks.** A lane with a named headline dependant is not a lane — it is a
prerequisite, ordered before its dependant. What follows first records
where ROADMAP-v0.20 §5's table landed, then files this course's new parks.

### 3.1 Discharged by v0.20 — closed, not carried

| lane (ROADMAP-v0.20 §5) | outcome |
|---|---|
| **C-V4′ and the foreign wiring** | **SHIPPED.** C-V4′ read out on a new preregistration with verified-to-change-the-term mutations and counted discards; C-G1 cleared on both floors; the `in words` line is **served**, armed from the artifact. Closed |
| **The grouping-canonical question** | **MEASURED, then repaired.** `experiments/grouping_census.json` published the distribution before any rule was proposed, and `G1b` turned the question into an exhaustive 5,228-pair census. Closed; its unanswered half (is the redundancy load-bearing for a *reader*?) parks below with C-V3 |
| **DESIGN-plain-input** — the maintainer-seeded incumbent | **ADJUDICATED — ADOPTED**, explicitly, per §5's silence-is-not-a-disposition clause. It is **§1 of this roadmap**, jointly with the selection that completes it. Closed as a carried item |
| **`_route_ownership` receipt duplication** | **SHIPPED** with the before/after timing artifact it had owed for three cycles (`experiments/ownership_receipt_timing.json`). Closed |

### 3.2 Carried with a named dependant — these are prerequisites

| lane | named dependant | disposition |
|---|---|---|
| **P1 / P2 / P3** (DESIGN-session-ledger §6) | **§1 — this cycle** | not carried, **scheduled and ordered first**. §1.1 states each one; slice 1 does not begin until P3's seal is frozen |
| **WITNESS's compact design** | **§2 — this cycle** | not carried, **scheduled**. The reviewed design lands before the slice; the receipt's draft is the input, not the registration |
| **The C-E3 substitution gap** | **§2 — this cycle** | not carried, **scheduled as debt inside WITNESS's design**. v0.20's C-E3 handed the checker the raw universally quantified statement with its free variables unbound, so the sampled class was never adjudicated. Any successor that adjudicates a counterexample must substitute its bindings first, and WITNESS's obligations are closed terms by construction — the design says so or it inherits the same gap |

### 3.3 Parked, with triggers

| lane | trigger to unpark |
|---|---|
| **The cost ledger** (answers per joule and per dollar) | **FIFTH cycle parked, still owed.** DESIGN-grounded-throughput §10 named it *first* among two successors. Unpark still needs a metrology no cycle has designed — and that sentence has now been true for five rotations, which is the streak itself worth noticing rather than the sentence |
| **Ledger-first claims** (v0.17 course lead, gate L1–L13, hardened) | **Fifth pass-over — and the trigger's wording is corrected here rather than inherited.** *Amendment, 2026-08-25:* v0.17, v0.18 and v0.19 all wrote *"the first cycle after **the** throughput readout"*; ROADMAP-v0.20 §5 wrote *"**a** throughput readout"* in a row claiming the rule was unchanged. That one word turns an **overdue** trigger into one that cannot come due. **The original wording is restored**: the readout is v0.17's, it fired once, and v0.20 is the **fifth consecutive pass-over**. v0.20 produced no new throughput readout either — the witness book moved three digest leaves and nothing was measured through it — so the lane is overdue under both readings. Its mid-cycle lift trigger (a release quoting a number its artifact no longer supports) stands |
| **Load-bearing / premise-necessity** | **Recovered from the v0.19 rotation's carried table, where it silently disappeared.** It was a named row in ROADMAP-v0.17 §3 and ROADMAP-v0.18 §3 (*"parked, travels with it"*) and was absent from ROADMAP-v0.19 §4, ROADMAP-v0.20 §5 and BACKLOG. `DESIGN-ledger-first-claims` calls it that lane's *"own most likely successor"*, so it **travels with ledger-first** and unparks with it, never separately |
| **Realization parameters as data** | **Parked, and the trigger sentence is quoted again after two cycles of silence.** ROADMAP-v0.18 parked it with *"becomes askable only if R1 fires."* **R1 fired at 0.9991 in that same release.** v0.19 restated the park without the sentence and v0.20 folded it into a catch-all *"unchanged"* row. So the honest state is: **askable since v0.18, never scheduled, and askable is not scheduled.** It needs a design that says what the parameters buy over the committed grammar |
| **Open-English *input*** | **Parked, and the park is now converging on §1.** v0.18's follow-on asked whether the committed realization lexicon can run backwards as DESIGN-text-resolution §4's synonym layer. That is the *same territory* DESIGN-plain-input's proposer occupies from the other side, and DESIGN-plain-input records the lineage itself (INBOUND folded to *"the parked synonym layer + existing clarification loop"*). It stays parked as a **mechanism** and is explicitly **not** claimed by §1: §1 proposes readings and verifies them, it does not invert the lexicon. Unpark when §1's G-series names a reverse-lexicon candidate it needs |
| **The register's `mathlib_head` budget** | Carried unchanged. 1,706 of the 1,878 blocked statements are blocked by a **budget a maintainer can lift**, not by a design limit; the two buckets never merge into one "unsupported" number. Unpark is a resourcing decision, not a design one |
| **Licensed variant generation** | **PARKED, not carried — and the change of disposition is the point.** ROADMAP-v0.19 §4 named a dependant (*"item 2 of any future cycle that wants a ranker"*); ROADMAP-v0.20 §5 named **none** and carried it anyway, which is exactly the shape the carried-lane rule exists to catch. It parks here with its trigger unchanged: the realization grammar emits exactly one surface per term, so the preference seat has nothing to rank. **Unpark when a design says what licenses a *second* passing surface and why that is not decoration.** One new fact goes with it: DESIGN-plain-input argues that **the input side is where the ranker seat finally has a denominator**, because a plain utterance licenses several candidate queries by construction. That is a *candidate* dependant, not a commitment, and §1's slice 2 does not depend on this lane |
| **C-V3 (human) — the determinacy sheet** | Still **ABSENT**, and the claim it alone licenses is still not made. v0.20 bought **C-V3′, a machine reader**, and C-V3′ **voided**, so not even the machine claim is made. Unpark needs a non-maintainer marker — the same missing-population problem as STRANGER |
| **Is canonical bracketing load-bearing for a reader?** | New park, from §1's own honest half. G0's exposure counts say how much surface moved; only a human determinacy sheet could say whether it helped. Blocked on C-V3 above |
| **STRANGER** — outside-asker gap-object intake | Parked; unpark needs a population of askers this repository did not author. Cited by DESIGN-plain-input §5 G1 and by DESIGN-session-ledger §11 rather than re-encountered |
| **HOSTILE DICTATION** | Parked with the list's only **prohibition-shaped** trigger: it **MUST run before any untrusted stream reaches the write gate**. §1's proposer takes plain text from the maintainer on loopback and opens no such stream; a later cycle that does unparks this **first**, not alongside |
| **UNSAY / the withdrawal lane** | Parked; revisit **when withdrawal has a driver**. **RECALL's clause is appended to its trigger** by this course: *an over-broad impact set counts as failure, not caution.* A blast radius that over-reports is not a safe default — it is a wrong answer |
| **TWO RIGHTS**, full direction | Parked with an empty mathematical denominator by its own B0; the 125 notational candidates remain a census a future direction inherits, and the two halves of that reading are never quoted apart |
| **WORD OF HONOR** — the attested layer | Parked as the strongest thesis-level candidate, for a *shape* reason not a merit one. Its **extraction-discipline census** rides any cycle as an optional rider |
| **VERDICT**, **DEBT NOTES**, **COURIER**, **BORROWED PREMISES**, **SECOND VOICE**, **FORK/TWO-STEP/DEADLINE/THE GRADED NO**, DESIGN-block-vocabulary | Parked unchanged with the triggers recorded in `reports/design-direction-v0.19.json` and `reports/design-direction-v0.20.json`. **BORROWED PREMISES gains a note**: §1's supposition object is the maturation it was parked waiting for, so its next look is *after* §1 reads out, not before |
| Realization parameters as data; unless-receipts, detached receipt, residual ledger, antibody, two referees, wild text, negative space; resolver coverage lane, A3–A5, verified-ambiguity, range certification, W1–W3 | Unchanged |

### 3.4 New parks from the v0.21 course, with their probes

Every declined direction carries its disposition; these are quoted from
`reports/design-direction-v0.21.json` `selection.declined_with_lessons`
and filed in BACKLOG with the same lines.

| direction | park, and the probe or trigger that would unpark it |
|---|---|
| **ATLAS** — a total per-(statement × surface) obstruction map with witnesses | Parked **as a named instrument probe**, respecting the standing counsel against instrument-shaped headlines — and the direction was honest that *"it makes zero statements reachable."* Its **TWINS 500-pair probe** is listed standalone: under 10 hits collapses TWINS to *duplicate-of*, **and the near-zero is the result**. Residual to carry: **first-blocker bias** — cells record the first cause a surface tripped on, so stacked obstructions are under-reported |
| **DEMAND** — an obstruction ledger against a question dump the program did not author | Parked **as a named probe with its license and pin rule attached**: a static CC BY-SA question dump, **titles only**, digest-pinned, with the drawing rule committed **before decompression**. That rule is the park's whole value — it is the STRANGER problem with a licence-clean population attached |
| **ABSENCE** — snapshot-relative library-absence certificates | Parked **behind DEMAND** — let demand aim it. Unparking ABSENCE first would certify absences nobody asked about |
| **RATCHET** — archive-wide monotone-service replay | Parked; its **pin audit is named as a cheap rider any cycle can run**. HANDSHAKE merged into it, donating its refusal-receipt clause to §1 |
| **GRAFT** — person-taught macros over the registered grammar, reserved namespace | Parked. It is what survived LESSON under round-two constraints: the human-teaching arm needed strangers and was cut, and the **stateless half** — macros verified before serving — survived under a new name. Unpark alongside a stranger population, i.e. behind STRANGER or DEMAND |
| **IF** — checker-signed conditional reductions with a typed null | Parked; **build the anti-triviality predicate first when its turn comes.** Without it every reduction discharges and the instrument confirms itself — the B4 shape again |
| **TRANSPLANT** — a second exact non-math domain port scored by core edits | Parked **with its one-week core-edit probe recorded**. It was series 1's runner-up; the probe is the cheap version of its whole claim |
| **RECALL** | Not parked separately — **folded into the withdrawal lane** above, donating one clause to its trigger |
| **SPLICE**, **FORK**, **HANDSHAKE**, **LESSON**, **TWINS**, **EXHIBIT** | Folded rather than parked: SPLICE into WITNESS's commit lane; FORK into §1's P1 and P2; HANDSHAKE into RATCHET; LESSON into GRAFT; TWINS into ATLAS's probe-gated class; **EXHIBIT declined in writing by its own series**, revival condition in §2 |

### 3.5 Standalone probes any cycle may ride

Cheap, preregistered, both branches yield an artifact. None is scheduled
here, and naming them is what keeps them from becoming rumours: the two
riders v0.20 accepted and **did not run** — the **HOLES counting table**
(revive-or-close conjecture-foundry work with a number) and the
**delete-K ground-truth table** — carry forward unchanged; and **VERDICT's
week-one warrant census**, **DEBT NOTES' one-day hand-classification
probe**, **COURIER's one-day detached-receipt probe**, **WORD OF HONOR's
extraction-discipline census**, **RATCHET's pin audit**, **ATLAS's TWINS
500-pair probe** and **TRANSPLANT's one-week core-edit probe** join the
list.

Two riders accepted and unrun for a full cycle is worth one sentence
rather than silence: a rider is cheap by construction, so an unrun rider
is a scheduling fact and not a cost finding. If either is still unrun at
the v0.22 rotation, it stops being a rider and either becomes an item or
parks.

## 4. Governance

### 4.0 Maintainer-directed relaxations (dated 2026-08-26)

Three rules this project earned are hereby **narrowed to what their
incidents actually proved**, by maintainer direction ("some of these are
too restrictive and block progress" — the direction is quoted so the
authority is visible, per house style). Each relaxation states what it
replaces, what it keeps, and the incident that justified the narrowing.

1. **The bug-not-result clause.** The no-chase rule (a voided control is
   a result; do not repair it and re-run) applies to controls that RAN
   and read unfavourably. It does **not** apply to a control that
   provably **never executed** — an instrument gap is a bug, not a
   reading. When the gap is mechanical and demonstrable (v0.20's C-E3:
   the substitution step was never called; every invocation failed to
   elaborate; the dead code is committed as the evidence), the fix plus
   a **supplementary registered run** is permitted in the same or next
   cycle, under the existing precedent for successor runs
   (`foreign_voice_rate.json` → `foreign_voice_rate2.json`): its own
   dated prereg amendment, a **new** artifact, the original never
   edited or re-scored. What is kept: the original run's verdicts
   stand; the supplementary run cannot retroactively un-void anything —
   it answers the question the gap left unanswered, nothing more.
   **Applied immediately: §2 carries the C-E3 supplementary run as a
   named early rider.**
2. **Determinism-plus-commit replaces execute-once ceremony.** v0.20's
   voice run accidentally executed twice concurrently and reproduced
   **byte-for-byte across three process invocations** — demonstrating
   that for a deterministic runner the committed artifact and its
   reproduction ARE the protection, and run-counting adds cost without
   adding trust. Future preregs register "**artifact committed from a
   deterministic runner; reproductions welcome and recorded**" instead
   of "executed once." Late determinism checks (v0.20's unrun E5 and
   C-E1 stability arm) may be run after first reading **with a dated
   disclosure of the lateness** — a byte-identity check cannot be
   gamed by when it runs. What is kept: non-deterministic measurements
   (anything touching a model, a clock, or the network) remain
   execute-once with the run pre-announced.
3. **The meetable-floor rule.** Every frozen floor now ships with a
   **meetability argument** — a pilot, a construction argument, or a
   bounded-class analysis showing a *correct* instrument can reach it.
   A floor without one is a **construction defect discovered at
   registration time**, not a gate waiting to void. Origin: C-E1's
   0.99 flip floor was unmeetable by any correct sampler over `Nat`
   for whole mutation classes, and finding that out cost the cycle
   its conformance claim. (The machine-reader pilot already modelled
   the right shape: its floor was frozen **from a pilot**, before the
   arm.) What is kept: floors still freeze before the instrument
   exists — the meetability argument is part of the freeze, never a
   post-hoc adjustment.

**Explicitly not relaxed**, so this section cannot be read as a general
loosening: denominator sealing before the scored party can move it;
capability-blind controls with written voiding sentences; adversarial
review before merge; the main-checkout freeze during suite gates;
append-only corpora and seeds as source of truth; no-silent-disposal of
maintainer-seeded designs; and the record-over-rerun rule for controls
that ran and read unfavourably.

- **The course gate was INVOKED strictly for the third consecutive
  cycle.** `reports/design-direction-v0.21.json` records three isolated
  series, three rounds each — **nine rounds, fifteen round-one directions,
  $2.41** — run headless from an empty non-git directory outside the
  repository under a strict tool denylist, with session ids and per-round
  prompt hashes committed and the isolation mode inherited unchanged from
  the v0.20 receipt. The brief is **on file and hash-verified**
  (`reports/design-direction-v0.21-brief.txt`), and the receipt records a
  small piece of self-checking worth keeping: `series_1.r1` **equals** the
  brief hash **by construction**, because round one of series one *is* the
  brief — *"the equality is the checkable form of that sentence."* One
  strict cycle proved the wording could be met; two proved it was the
  practice; three is now the least interesting fact about it, which is the
  goal.
- **The cycle's evidence pattern: two registered runs, opposite verdicts,
  both published.** The voice cleared and is served; the formulas voided
  and the void is served beside the route. Neither outcome was available
  by choosing which run to report, because both floors were frozen before
  either instrument existed. **A cycle in which every registered run
  clears is a cycle whose floors were set where its arrows landed** — and
  the honest defence against that is not intent, it is preregistration
  that can go red.
- **The record-not-rerun doctrine got three exercises, and they are
  different in kind.** (1) The conformance review found the *record* around
  two controls false and **corrected the artifact in place** — 97 added
  lines, a single hunk, removing exactly those lines restores the file
  byte for byte — because a false sentence in a canonical artifact cannot
  be repaired by a note a reader may never open. (2) The voice review found
  two **stale prose strings** beside correct measured numbers in a
  byte-reproduced artifact, and the artifact was **left untouched** — a
  note inside it would have destroyed the byte-identity that was the
  reproduction proof — with the correction recorded in ANALYSIS instead.
  (3) The C-E3 misattribution was corrected **without re-running the
  measurement**, and the dead code that caused it was **left in place as
  the evidence for the correction**. Three exercises, three different
  right answers, and the deciding question each time was *what does the
  repair cost the reader's ability to check?*
- **The recurring catch of the cycle: assertions written so they cannot go
  red.** Not one wrong digest was found in either review. What was found
  was a gate computing its own evidence from a dict literal keyed by class
  name; a test comparing a file at HEAD to the same file in a clean
  worktree; a freeze list whose prose carried authority its machine check
  did not cover; and a test asserting *"the repository as it stands is
  dark"*, which was true the day it was written and red the day the system
  worked. **A green assertion that could not have gone red is not
  evidence**, and this is now a standing review question rather than a
  cycle's anecdote. §2's B4 is the same question turned into a gate clause.
- **A voided instrument stays in the gate.** C-V3′ voided and is published
  as a void, never as a rate; the conformance controls voided and the
  route serves the void. The successor in §2 exists because a claim-kind
  was lost, not because a control was inconvenient.
- **Headline selection remains part of the evidence trail.** When the v0.22
  course reports, its selection and every declined disposition are recorded
  here, in the receipt, and in the release notes.

## Release gate

v0.21 is ready only if:

- **P1, P2 and P3 are committed in order, before slice 1 begins**, with
  P3's protocol frozen before recording starts and its seal frozen before
  the replayer exists. **If P3's floor is not reached, the cycle STOPS**
  and publishes *"multi-turn binding is rare in practice"* as its finding —
  a published stop is a result; a quiet descope is not;
- **the session ledger ships its registered run** — half B's first
  execution, with B1–B8 and B10–B13 adjudicated and **R1** read out — or
  stops on a named stop condition with the reading published. **The
  voiding sentence governs**: any B5 or B6 flip voids the
  multi-turn-assumption capability and the journal survives as an
  instrument rather than as a capability;
- **B13's 20-turn arm-blind audit publishes its table beside the gate**,
  whichever way it reads, and below 16/20 the cited-but-inert residual is
  **promoted from named to measured** and the served line carries it;
- **slice 2's B9 is scored if and only if slice 2 exists**, and its absence
  is recorded rather than inferred;
- **WITNESS's reviewed design lands before its slice**, and the slice ships
  its registered run **or** publishes its stop. **B4's self-comparison
  obligation must return `rejected_trivial`** and **B3's mutant sweep must
  not be perfect** — a clean sweep or a discharged decoy voids the
  instrument and reports an instrument failure, not a capability;
- **any successor that adjudicates a counterexample substitutes its
  bindings before handing the term to a checker**, or says in writing that
  it inherits v0.20's C-E3 instrument gap;
- **no session-replay claim is made without B12's corroboration**, and no
  correctness claim is made at all — sessions are *reproducible*, not
  *correct*, and a wrong answer replays as faithfully as a right one;
- the **statelessness suspension ends at this gate by this gate's own
  verdicts** — state becomes a shipped property or is withdrawn, and B10 is
  the fence that makes either answer honest;
- `check_report_regeneration.py` runs in the release refresh with its
  verdicts in the notes;
- the full suite is green on a frozen tip with retained receipts;
- every unfinished item ships or parks in writing;
- the outside design inquiry is **invoked** for v0.22 — the forge skill run,
  or a written course-gate amendment by the maintainer — with the receipt
  named, and the v0.22 brief carries this cycle's readouts **including any
  void**, not only the ones that grew a number.
