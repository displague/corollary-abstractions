# Roadmap v0.22 — how a question finds a statement, and whether the evidence outlives the program

v0.21 registered three things and got three different verdicts. The session
ledger **served**. Plain input **failed**, on a metric that could not see a
correct refusal. WITNESS **stopped itself** before it became an instrument,
because its obligation compared one parse with itself.

Two of those three point the same way. Plain input's proposer could not select
readings that were **never enumerated** — the design's own motivating question
returned zero candidates — and where readings *were* enumerated, the correct
ones sat at ranks 21 and 23 behind a title-length tiebreak. WITNESS's stop says
the same thing one layer down: a single reading of an object cannot check
itself.

So this cycle asks how a question reaches a statement at all, and what a piece
of evidence is worth when the program that produced it is gone.

## 1. Headline — HANDLES, and the census that may be the whole result

[DESIGN-handles](DESIGN-handles.md) is the v0.22 course's selection
(receipt: `reports/design-direction-v0.22.json`). It was **rebuilt twice under
adversarial review** before it landed, and both falsifications are why the item
is scoped the way it is.

**The boundary being moved.** Reachability of a statement should be a property
of its verified content and of how mathematicians name its parts — not of the
string somebody typed above it in a file.

**What review corrected, and it matters for what this item may claim.** The
first draft said the tree holds no non-title index. It holds two:
`resolver.by_lexicon` (`scripts/resolver.py:264-277`), over the per-node
`symbol_lexicon` glossary, and `resolver.inventory` (`:284-288`). Run live,
`resolve('greatest common divisor')` — the **phrase** — reaches
`programming.euclid.{iterative,recursive}` **today**. The real defect is
narrower and worse: v0.21's candidate enumerator builds its haystack from
`title` + `keywords` **only** (`scripts/candidate_enumerator.py:166-168`), so
the proposer path was wired to the weakest index on the tree while the stronger
ones sat unused **one route earlier on the same serving path**.

Reachability is not missing. It is **unmeasured, un-gated, and unwired where
the intake ambition needs it.**

### 1.1 The census-first framing, and the honest expected headline

**This item is scheduled expecting its stop clause to fire, and that is not a
hedge — it is the ordering the evidence forces.**

Review measured the indicative yield. With specificity K = 128, statements
holding at least one **specific** handle come to roughly **263 via S-LEX** and
**306 via S-INV** — essentially the same curated **~2%** of 12,777 — because
12,514 `lean_workbook` nodes share three boilerplate name pairs
(*equality* / *template* / *standing*) that K excludes as overbroad, and
S-INV's head distribution is dominated by universal heads (`IMPLIES` 9,403;
`MEET` 8,160). §1's live `gcd` resolution comes from inside that 2%.

So **H-P0's census is the deliverable, and the authoritative numbers are
H-P0's to return, not the design's to assert.** `DESIGN-handles` §9's **stop
clause**, quoted because it is the item's most likely outcome:

> if the census reads specific-handle coverage near the review's indicative
> ~2%, the slice publishes the census as the headline — *the ingested library
> is effectively nameless; the naming layer must be built, not indexed* — and
> the capability sentence does not ship.

**That is a first-class result, not a failure**, and it is exactly the shape
v0.21's three outcomes taught: a published stop is a result; a quiet descope is
not. Whether name-derivation — from the verified English renderings the voice
lanes already serve, or elsewhere — becomes v0.23's work is the **rotation's**
question, not this slice's assumption.

### 1.2 Construction prerequisites, ordered before the table exists

- **H-P0 — the coverage census.** One committed artifact: per source, exactly
  which statements it produces handles for, from which **committed producer**,
  plus the id→skeleton table for S-SKEL, plus a **priced statement** of what
  S3 term-serialization would cost. **Before any handle table exists.**
  The three sources, as the tree actually holds them:

  | source | producer (committed code) | status |
  |---|---|---|
  | **S-LEX** — `symbol_lexicon` names | the per-node glossary under `resolver.by_lexicon` | records on all 12,777; specific-handle yield ~2%; H-P0 measures |
  | **S-INV** — call-head inventory | `match_signatures` `template_call_heads` over `anonymized_template` (`match_signatures.py:952,1038`) — **title-free** | recomputable, **not persisted**; H-P0 commits the table |
  | **S-SKEL** — family skeletons | recomputable by `measure_compression.py`; strings not persisted | all 12,777 recomputable; H-P0 commits the id→skeleton table. **A skeleton string is nothing a person types**, and the design claims no human-question match for it |

  Deleted from the outside draft by review: **S4 notation records** (no producer
  exists — the only structured notation is 389 hand-authored rows on 186
  statements) and **S5 defeq alias buckets** (no defeq machinery exists
  anywhere in the tree). **S3 elaborated-term unfoldings** is demoted to a
  priced question: only digests are persisted
  (`scripts/foreign_voice.py:205-217`), and its coverage would be **2,319
  oracle-eligible, of which 2,313 covered** — two numbers that are subset,
  never summed.

- **H-P1 — the budget pilot.** Measure per-candidate verification cost over
  **≥200 candidate verifications** on half the question set's authoring drafts,
  publish the cost, and freeze the budget **B** from it in a **dated amendment
  before Q60 seals**. The `DESIGN-witnessed-conformance` pilot-then-freeze
  shape. **B is not 40 until the pilot says so** — the draft's 40 was a number
  with no meetability argument, which is the defect ROADMAP-v0.21 §4.0(3)
  exists to catch at registration time.

- **H-P2 — Q60 sealing.** Sixty questions, **42 in-library / 18 absent-target
  (30%)**, including §1's `gcd` question and the rank-21/23 question, sealed
  **with their candidate-reading sets before the table exists**. The **13
  silent-bind questions** from v0.21's sealed thirty are a **separate, third
  sealed subset** and are scored only by B6's choice-event clause — never
  pooled with the 42/18.

- **P-L** — the parked lexicon-backwards question gets exactly **one census
  line** from H-P0 (which S-LEX names also appear in the realization lexicon's
  English), recorded for that park's future unpark case. Nothing else; the park
  stays parked.

**The park this reopens, adjudicated in writing.** `docs/BACKLOG.md` parks the
resolver-coverage lane behind the v0.15 standing rule — it unparks only with a
mechanism justified independently of the score it would move. Discharged
explicitly: the mechanism is **candidate enumeration for the proposer path**, a
surface whose gate (v0.21's G5) does not score resolver coverage at all and
whose v0.21 red is the independent justification. **The resolver's own routes
and scores are untouched** (`DESIGN-handles` §9's fence), so the rule's
condition is met rather than evaded.

### 1.3 The slice

One slice, and it does not begin until H-P0, H-P1 and H-P2 are committed in
order.

**Build**: unify the three committed non-title sources into one first-class,
gated **handle table**; measure what it reaches **under title deletion**; and
wire the candidate-enumeration path to it. Three artifacts:

- `experiments/handles_table.json` — one row per (statement, handle):
  `statement_id` · `handle_token` · `producer` ∈ {S-LEX, S-INV, S-SKEL} ·
  `producer_run_id` · `resolves_to_count` · `specific: bool`.
- `experiments/handles_partition.json` — one row per statement: `class` ∈
  {REACHABLE, RESIDUE} · `residue_cause` from B4's frozen vocabulary. **This is
  the deliverable.**
- `experiments/handles_enum_receipts.json` — `question_id` ·
  `candidates[{statement_id, handle_witnesses[]}]` · `budget_used` ·
  `measured_verification_cost_s` · `outcome` ∈ {ENUMERATED,
  REFUSE_NO_HANDLE_MATCH, REFUSE_OVERBROAD_ONLY} · **`route_voids[]`,
  non-optional** — NOTARY's distillation: *a receipt that traverses a published
  void and renders clean is a red result.*

**Candidate order under budget, frozen now**: when handle matches exceed B,
candidates are taken in **ascending `resolves_to_count`**, ties broken by
`statement_id` byte order. **Specificity first, never string length** — that is
v0.21 §8.5's lesson turned into a rule, and it lives in the preregistration
rather than in a code comment.

**A later slice, only if H-P0 prices it worth taking**: S3 term-store work.
Not scheduled here.

### 1.4 The construction gate — numbers frozen now, every floor argued

Every clause below carries a meetability argument, per ROADMAP-v0.21 §4.0(3).

- **B1** — every handle carries a producer in {S-LEX, S-INV, S-SKEL} and a
  `producer_run_id`; **one untagged handle is red**. *Meetable:* all three
  producers are committed code today.
- **B2** — specificity **K = 128**. *Meetable, argued on the source that
  binds:* S-SKEL buckets are small (mean 1.12 statements per skeleton, max
  family reuse 10 — `reports/compression.json`), so K never binds there; the
  argument that matters is S-INV/S-LEX, where universal tokens (`Nat`, `+`,
  `≤`) resolve to thousands and are exactly what K exists to exclude. H-P0
  publishes the resolves-to-count distribution per source, and **if K = 128
  strands whole corpora with no specific handle, K is re-frozen from H-P0's
  distribution by dated amendment BEFORE the table run — never after.**
- **B3** — **title ablation, red-able by construction.** `title_derived` is
  **not** a token comparison; it is a **producer audit**: an AST check (the
  v0.21 G8-repair precedent) that the table builder and the enumeration path
  read neither `title` nor `keywords`, **plus** an ablation run with the title
  index removed entirely and every Q60 answer re-derived. Red if the AST audit
  finds a read, or if **any** enumeration receipt differs between
  title-present and title-absent runs.
- **B4** — residue enumerated **member by member** with a cause from the frozen
  vocabulary {ALL_OVERBROAD, NO_LEXICON_ENTRY, NO_INVENTORY, UNCLASSIFIED};
  **UNCLASSIFIED > 5% of residue is red.**
- **B5** — the `gcd` question enumerates its target at any rank, floor 1/1.
  *Meetable:* `by_lexicon` already resolves the phrase live. This clause pins
  that the unified table **does not lose what the tree already had.**
- **B6** — all 13 silent-bind questions emit `choice_events[]` or route through
  enumeration; **13/13**.
- **B7** — two sealed scoring classes, **never aggregated**; the blind chance
  rate is computed **per question from its own enumerated candidate set**
  (expected blind hits = Σ verified ÷ candidates per question) and published
  beside the observed rate. Absent-target refusals
  (`REFUSE_NO_HANDLE_MATCH`) **score correct**; over-refusal on the 42 scores
  incorrect.
- **B8** — the permuted-handle control (§1.5).
- **B9** — rider floors, each with its own argument (§3).
- **B10** — H-P0 committed before the table; **a handle from outside its
  censused coverage is red.**

**B7 is v0.21's G5 lesson made mechanical.** G5 froze a chance rate of 1/8
when the measured expectation was 0.687, and it counted verified selections so
it could not see a correct refusal. B7 computes the chance rate **per question
from the candidate set that question actually produced**, and it scores a
correct absent-target refusal as a hit. Neither change was available to G5
after the fact; both are frozen here before any arm runs.

**And §1.5's voiding sentence adds the check G5 had no version of at all: an
arithmetic test the run performs on its own clause before any arm runs.** G5's
clause was *blind ≤ proposer ÷ 2*, and against the blind arm's real expectation
of 20.62 that required **≥ 41 verified selections out of thirty questions** —
unsatisfiable by construction, and discoverable by one sum nobody did. §1.5
publishes **E** and **σ** first and **voids the run as unconstructable** if
E ≥ 2.5. A gate that can refuse its own design at registration time is the only
form of the meetable-floor rule that does not depend on somebody remembering
to apply it.

### 1.5 Blind control, vacuity control, and the voiding sentence

**Permuted control.** The identical handle multiset reassigned across
statements by a seeded permutation, run against Q60 under the same budget and
sealed classes.

**The voiding sentence, frozen and mechanically evaluable:**

> Before any arm runs, the prereg publishes **E** = the sum over the 42
> present-target questions of each question's per-candidate-set chance (B7's
> computation) and its standard deviation **σ** under independent draws. **If
> E ≥ 2.5, the candidate sets are too loose to test and the run voids as
> unconstructable.** Otherwise, if the permuted index's present-target hit
> count is **≥ ⌈E + 2σ⌉**, reachability as defined here carries no signal and
> the capability claim is **void regardless of the true index's raw score.**

The first limb is the direct repair of v0.21's mis-derived floor: **the run can
discover at registration time that its own control is unconstructable**, rather
than discovering after the arms have run that no correct instrument could have
met the number.

**Vacuity control.** The incumbent title+keyword enumerator runs over the same
Q60 as the cheapest capability-blind baseline, **charged for candidate volume**
per the house precedent (`DESIGN-when-to-ask`'s reciprocal-load lesson — a
baseline that "recalls" by returning thousands pays 1/k). It must lose the
`gcd` question by construction; **if it matches the handle table overall after
the volume charge, handles added nothing and the run publishes that.**

**Corruption control.** Twenty seeded table corruptions (wrong `statement_id`
on a real handle; fabricated handle token) must each either change an
enumeration receipt or be caught by the digest pin. **A corruption that changes
nothing observable is itself published** — it means the corrupted region was
dead weight.

### 1.6 Result gate, stop conditions, non-claims

**R-H:** the capability sentence serves only if **B1–B8 and B10 are green**
AND the title-ablated table reaches **≥ the title index's volume-charged score
on the 42** (it must not be worse than what it replaces) AND the **18
absent-target refusals hold**.

**The served sentence, frozen and scoped to what H-P0 finds rather than to the
library:**

> for the statements H-P0's census shows carry a specific handle, a question
> can reach them through their verified content and their authored names, with
> titles deleted — under the maintainer-authored question set and nothing
> wider.

**Stop** if B1, B3's audit, B8, or B10 fires. **No partial index ships.**

**Non-claims**, carried into every sentence this item produces: no reachability
rate (the deliverable is the partition and its enumerated residue); no ranking
work beyond the frozen truncation order; no hand- or model-authored synonyms;
no claim the residue is small, only that it is complete; no claim a reachable
statement is *correctly* reachable; **no stranger-usability claim** — Q60 is
maintainer-authored and the authorship contamination is named, unpriced, and
inherited by every number here; and **no change to any resolver score or served
resolver byte.**

**The residual the design names and does not price:** *specific-but-inhuman
handles* — near-unique internal tokens that pass every gate while no human
question contains them. B3's producer audit and H-P0's stop clause address the
index side; question authorship stays the unmeasured link, and it stays named.

## 2. COLD RECEIPT — does the program's evidence survive the program's deletion?

**Why it is item 2.** It moves what a *reader outside this repository* can
check, which is the standing gap behind STRANGER, C-V3 and every
maintainer-authored denominator this project has published. It is the second
adopted direction of the v0.22 course, and its preregistration draft was
recorded in the receipt **before this roadmap was written**, quoted rather than
paraphrased:

> **artifact:** `cold/` bundle: `census.json` one record per receipt kind
> (`emitting_routes`, `bundle_manifest`,
> `external_deps{name, pin_hash, role}`,
> `recheck_procedure{raw_checker_invocation | program_replay | none}`,
> verdict SURVIVES | NEEDS-PROGRAM | UNTESTED, `verdict_evidence`,
> `blocking_dependency confirmed_by_removal`, `tamper_result` 3 mutations,
> `omission_result` FAIL_LOUD, `sham_result`, `pin_audit_ref`, `census_seal`)
> + `harness/` container recipe + `path_audit` + `scramble_baseline` + one
> worked stranger-path transcript
>
> **gate:** B1 unmapped emitting routes = 0; B2 ≥1 kind SURVIVES (the
> raw-checker-invocation exception exists); B3 tamper 3× per kind 100% FAIL;
> B4 omission FAIL LOUD naming the missing dependency, silent pass voids the
> harness; B5 sham-checker SURVIVES count = 0; B6 chance measured: 200
> scrambled bundles; **if** 0 of 200 pass, publish the 1.5% rule-of-three
> upper bound as the chance rate; B7 100% NEEDS-PROGRAM carry
> `confirmed_by_removal` (a correct NEEDS-PROGRAM scores as a hit); B8 ≥90%
> SURVIVES on first run voids pending audited-empty-PATH re-execution; B9
> version-drift ceded to the pin audit, reference only; B10 `census_seal`
> fixed before the harness runs, later finds publish as census misses
>
> **voiding_sentence:** If any receipt kind is annotated SURVIVES while the
> pinned checker is replaced by the accept-all stub, the harness is measuring
> bundle presence rather than verification, and the claim is void for every
> kind in this census

**One clause added by the selection, before registration, and it is the
draft's own residual risk priced rather than deferred:**

> `external_deps[].provenance` ∈ {`third_party_pinned`, `program_configured`};
> **any SURVIVES resting on a `program_configured` dependency downgrades to
> UNTESTED.**

The residual it repairs, in the draft's words: *"the harness deletes the
program's code while keeping the program's prepared world — program absence is
priced, environment provenance was not."* A receipt that "survives" because the
program pre-arranged the world it is re-checked in has not survived anything.

**One tense repair from review**: B6 reads *"200 scrambled bundles; **if** 0 of
200 pass, publish the 1.5% rule-of-three upper bound as the chance rate."* A
gate, not a recorded outcome.

**Ordering obligation, on the WITNESS precedent.** *Its compact design lands
before its slice.* The draft above is a course artifact, not a design; the
reviewed `docs/DESIGN-…` document is written and adversarially reviewed
**first**, and this roadmap quotes the reviewed gate clauses once they exist
rather than inventing them in advance. WITNESS earned that convention the
expensive way this cycle: its design landed, and the pilot still stopped the
slice — which is the outcome the ordering exists to make cheap.

**B4's shape is the one to watch.** *Omission must FAIL LOUD naming the missing
dependency; a silent pass voids the harness.* That is v0.21's B4
self-comparison trap wearing different clothes, and v0.21 is the reason it is
in the gate rather than in the residual-risk paragraph.

## 3. Riders — two, each with a floor and a stop rule

Both are registered in `DESIGN-handles` §7's B9. Both publish an artifact
whichever way they read.

**R1 — ONE STEP's depth-1 census** (`experiments/onestep_census.json`). The
fold of CHAIN and BRIDGE: *answer-or-frontier*, where **both answering and a
correct refusal score** — v0.21's G5 lesson embodied in a direction rather than
argued about.

- **Floor**: the ONE STEP build opens at **≥200 one-step-consumable
  statements** AND **≥5 of 60 questions landing there**.
- **The floor is a lane opener, not an instrument verdict**, and **meetability
  is deliberately not argued** — the census exists to measure exactly the
  quantity a meetability argument would have to assume.
- **Stop rule**: census committed, lane opens or closes, **nothing else runs**.
  A miss closes the lane and the census publishes regardless.
- Its depth-1 census can close **three parked lanes at once**, which is why it
  is a rider and not a wish.

**R3 — ERRATUM's flip probe** (`experiments/erratum_probe.json`). Typed-delta
replay of served history against corpus growth.

- **Floor**: **1** designated *planted* flip detected in the replay harness —
  the mechanism check, not a yield claim. The real-flip count is published with
  the growth window named.
- **Stop rule**: zero real flips publishes the scale sentence, and **R3's v0.23
  candidacy is decided by the count, not by re-running it.**

**R2 was removed.** The v0.22 design review (H9) demoted TWO WITNESSES from
rider to **parked item-candidate**: its 160-obligation mutation battery is a
WITNESS-slice-sized cost — the whole v0.21 WITNESS slice budgeted 50 mutants —
and a slice-sized cost is not a rider. It waits with the parked conformance
successor it serves (§4.3).

**And the standing rider stop rule from ROADMAP-v0.21 §3.5 comes due at this
rotation.** It said: *if either of the v0.19 course's two accepted riders is
still unrun at the v0.22 rotation, it stops being a rider and either becomes an
item or parks with a reason.* Both — the **HOLES counting table** and the
**delete-K ground-truth table** — are still unrun. Unrun through v0.20 and
v0.21 since ROADMAP-v0.20 §3 scheduled them, and named without running a third
time here. The rule fires: **both park**, in §4.3, with their reasons. They are not listed as
available riders again.

## 4. Carried, with dependants named

The rule, unchanged: **every carried lane names its dependant, or it parks.** A
lane with a named headline dependant is not a lane — it is a prerequisite,
ordered before its dependant.

### 4.1 Discharged by v0.21 — closed, not carried

| lane (ROADMAP-v0.21) | outcome |
|---|---|
| **§1.1 P1 / P2 / P3** | **SHIPPED, in order, before slice 1.** P1 falsified the design's own finiteness argument; P2 did **not** decide the conditional-versus-clarify question and says so; P3 met its floor with margin and published the other reading's numbers too. Closed |
| **§1.2 slice 1 — the session ledger** | **SHIPPED and SERVED.** R1 HOLDS; the statelessness suspension ended by this gate's own verdict. Closed |
| **§1.2 slice 2 — plain input** | **SHIPPED AS A NEGATIVE.** R2 FAILS on G5 and G9; nothing is served. Closed as an item; its two successors carry below |
| **§2 — WITNESS's compact design** | **SHIPPED**, reviewed before the slice, exactly as the ordering obligation required. Closed |
| **§2 — the C-E3 substitution gap** | **DISCHARGED** by the supplementary run: 25/25 confirmed, and the exact-rational reading that says the agreement prices arithmetic-implementation risk rather than domain risk. Closed |
| **§2 — the C-E3 early rider and the late determinism checks** | **BOTH RAN.** E5 HOLDS byte-identical, dated late. Closed |
| **§4.0's three relaxations** | **ALL THREE EXERCISED**, and audited (§5). Closed as a governance question, standing as rules |

### 4.2 Carried with a named dependant — these are prerequisites

| lane | named dependant | disposition |
|---|---|---|
| **H-P0 / H-P1 / H-P2 / P-L** (`DESIGN-handles` §6) | **§1 — this cycle** | not carried, **scheduled and ordered first**. §1.2 states each one; the slice does not begin until all are committed |
| **COLD RECEIPT's compact design** | **§2 — this cycle** | not carried, **scheduled**. The reviewed design lands before the slice; the receipt's draft is the input, not the registration |
| **The v0.21 enumerator's title-only haystack** | **§1 — this cycle** | not carried, **it is the defect §1 exists to repair.** `candidate_enumerator.py:166-168` is where the proposer path met the weakest index on the tree |

### 4.3 Parked, with triggers

| lane | trigger to unpark |
|---|---|
| **The resolver's pre-emptive binding** (v0.21's G9, NOT MET) | **Parked with 13 committed fixtures** (`g1-03, 05, 06, 07, 10, 12, 14, 15, 17, 18, 19, 20, 22`), and it is parked rather than carried because **no v0.22 headline item depends on it** — §1's fence forbids touching any resolver score or served resolver byte. Unpark needs a design carrying three things it cannot borrow: its **own preregistration**, its **own capability-blind control** (G5's is scoped to selection among enumerated candidates and says nothing about a changed bind rule), and a **K re-measurement**, because the resolver row sits inside the serving path the throughput book scores |
| **The G5-metric successor** | **Parked with its rule written down**: score the **branch outcome against the question's registered disposition** (conditional / ask / exhaust) rather than the raw verified-selection count, so declining an out-of-corpus question counts as success for both arms and the blind arm's *inability* to decline shows up as the incapacity it is — and freeze it with a **meetability argument** per ROADMAP-v0.21 §4.0(3). Unpark when a proposer lane is scheduled again. **The correction is already at work elsewhere**: §1's B7 computes chance per question and scores absent-target refusals as hits, and R1's ONE STEP census scores correct refusals by construction |
| **TWO WITNESSES + the independent second reading** (with the parked conformance successor) | **Parked together as item-candidates, because they are one problem.** WITNESS parks behind a **construction prerequisite** — a second, independent reading of `S` (a second front-end, or W2's human transcription promoted from audit to input) — and TWO WITNESSES' kernel-then-overlap probe plus 160-obligation mutation battery is what would price one. Demoted from rider by review H9 (a slice-sized cost is not a rider). **Fragment growth alone does not unpark WITNESS**: the divergent class exists and is reachable (25 statements, 18 compiling) but is **non-linear**, so reaching it gives the obligation content while leaving it a comparison of one parse with itself |
| **EXHIBIT** | Stays declined, and the second reason is recorded as the accurate one: not that the successor voided, but that it **never became an instrument**, for a cause — single-front-end construction — EXHIBIT would inherit whole. Revives only behind the same prerequisite |
| **CANARY-CURVE** — declared scaling classes, and the architecture-vs-smallness split | **Named v0.23 incumbent-candidate.** The ordering is its **own residual risk answered**: its 10× shadow tier prices statement *count*, while the dimensions that actually bite intake — title-collision density, enumeration fan-out — may be sparser in the tail. So growth is measured **after** the enumeration layer exists, when density is measurable instead of missed |
| **TOLL** — production cost vs stranger-path re-check cost on a named floor machine | **Named v0.23 incumbent-candidate beside it, and it is the cost ledger's first named unpark candidate in six rotations** (see §5). Its denominator waits on §2's harness: the composition is claimed explicitly, because refusing it would mean the affordability claim marks its own homework. **CEILING is TOLL's named successor** and routes with it — *no budget freezes before the cost distribution exists*, which is v0.21's mis-derived-floor lesson applied one lane over; a budget blown at 10× is a curve row, not a failure |
| **CROSSING** — execution-licensed boundary crossings both ways | Parked with its **20-real-corrections probe** and its **preregistered predicted split (2 / 6 / 12)**. The prediction is committed now so the probe cannot be read after the fact |
| **LONG CON** — sequence-level adversarial search over conversations | Parked as a **day-probe**: ten hand-written sequences, frozen budget, **mandatory plant**, committed near-miss taxonomy **even on a null**. The **write-gate prohibition is inherited** — it opens no untrusted stream, and HOSTILE DICTATION unparks first if one ever does |
| **BITROT** — integrity-scope map of the unsealed complement | Parked as a **day-probe with its stop rule stated here**, since the receipt carries only its controls: **undetected-changed-answer count > 0 stops the probe and publishes the narrowed scope; a clean 1,000 publishes the map and closes the probe.** Its never-read-bytes control is the point — *a detector catching unread flips is comparing the store to itself* |
| **Slice 1's citing behaviour is unreachable from the typed prompt** | **New park, from adversarial review of the v0.21 rotation drafts.** `harness.main()` attaches no `AssumptionSet`; only `scripts/session_recorder.py` does, so at the CLI a `suppose` line renders without declaring an Assumption record and **no answer cites anything**. That is exactly what `DESIGN-session-ledger` specified — it names no served surface for slice 1 — and it is still a gap between the claim's wording and *"shipped means the acceptance a newcomer can try"*. Parked, not carried: **no v0.22 headline item depends on it**, and §1's fence forbids touching served routes. Unpark needs a design saying what a person-facing session **is** — where its key ring comes from, where its journal is written, and what B10 re-scores on it — before any route attaches a ledger outside the recorder. Attaching one silently would move the very thing B10 measures |
| **The `conform` route advertises the asker's numbers and does not use them** | **New park, from this rotation's drift audit, and it is a product surface.** `scripts/serve_chat.py:635-637` describes the route as *"an exact evaluator over the **asker's own numbers**"*; `scripts/harness.py:2192` parses the bindings and `:2229` calls `run(program, schema.digest)` **without them**. The sheet's own published example (`serve_chat.py:332`) refuses `does_not_parse` when typed, and `_route_conform`'s docstring still describes a stub in a tree where `conform.py` landed. RELEASE-v0.20.0 named the underlying gap in its honest limits and it was filed nowhere. **Not patched at a rotation** — widening or narrowing a served route is a behaviour change owing its own evidence and its own G4 — and parked rather than carried, because **no v0.22 headline item depends on it**. Unpark condition, and it has two admissible discharges: either the route consumes the bindings, with a served diff and a control; **or** the sheet's description, its example and the docstring are corrected to say what the route does, which is cheap and is the honest minimum |
| **DESIGN-block-vocabulary's one untested property** | **Recovered from the v0.21 catch-all, where it was dropped.** RELEASE-v0.19.0 named it deliberately — *"what survives for any future unpark, named so it is not lost: the design's **append-only, path-independent growth** property, which **no baseline in this probe tested**"* — and ROADMAP-v0.20 §5 kept it in the row. ROADMAP-v0.21 folded the design into a catch-all and the property stopped being quoted anywhere. Quoted again here. Unpark needs a design saying what append-only path-independent growth buys that two indexes with one tag bit do not; the rest of the lane is **parked by numbers** (0.9981 against that baseline) and stays parked |
| **The cost ledger** (answers per joule and per dollar) | **SIXTH cycle parked** — and for the first time the sentence changes. **Not that it was ever one sentence**, which is a correction this rotation owes: v0.17 wrote *"a metrology **neither cycle** has designed"*, ROADMAP-v0.18 *"a metrology **this cycle has not** designed"*, and ROADMAP-v0.19, v0.20 and v0.21 *"a metrology **no cycle** has designed."* The park is the streak; the wording never was. **TOLL is that metrology, named and parked as a v0.23 incumbent-candidate.** The lane is still parked and this cycle still designs nothing for it; what is new is that it now has a **named successor with a denominator**, and the streak is recorded as six rather than allowed to reset on the strength of a candidate. **The counting basis, stated so the number is checkable**: rotations since `DESIGN-grounded-throughput` §10 named this lane first among two successors to a fired T4 — v0.17, v0.18, v0.19, v0.20, v0.21 and this one |
| **Ledger-first claims** (v0.17 course lead, gate L1–L13, hardened) — named dependant: ***none this cycle*** | **Sixth pass-over, and three more edits are restored beside the article v0.21 restored.** The trigger, in its original wording and its original tense: *"It **became** a headline candidate the first cycle after **the** throughput readout"* — a definite, one-shot event that fired at v0.17, not a standing conditional. v0.20's row had flipped *became* → *becomes*, dropped *"this cycle"* from the dependant, and compressed the receipt path away; all three are restored here, with the receipt named: `reports/design-direction-v0.17.json`. **v0.21 produced no new throughput readout either**: against `v0.20.0`, `experiments/throughput_tasks.json` moved **exactly two lines**, both digest leaves inside `rendering_module_digests` (`scripts/evaluate.py`, `scripts/harness.py`), with `built_by`, `counts`, `schema`, `scoring_rules`, `seal` and **all 119 task records** byte-identical — and no `throughput_result*.json`, `throughput_trial_*.json` or `throughput_baseline.json` changed at all. Seal rebuilds, not measurements. **But the scorer moved and nothing was re-measured through it**: `scripts/measure_throughput.py` gained a rule-level forfeit for `conditional` **and for a missing status**, so the next readout is **not** a like-for-like comparison with v0.17's and owes that sentence in writing. The lane is overdue. Its mid-cycle lift trigger — a release quoting a number its artifact no longer supports — stands |
| **Load-bearing / premise-necessity** | Parked; **travels with ledger-first** and unparks with it, never separately. Named again here rather than allowed to disappear a second time |
| **Realization parameters as data** | Parked. **Askable since v0.18** (R1 fired at 0.9991), **never scheduled**, and askable is not scheduled. The trigger sentence is quoted a second consecutive rotation so it cannot fall out again. Unpark needs a design saying what the parameters buy over the committed grammar |
| **Open-English *input*** / the reverse-lexicon synonym layer | **Parked — with its worked example and its fired trigger restored, and the convergence on §1 stated precisely.** The question, in ROADMAP-v0.19's full wording: *can the committed realization lexicon run backwards as the synonym layer `DESIGN-text-resolution` §4 names (**`gcd` vs "greatest common divisor"**) — a design, not a patch, **and R1 firing is what made it askable**.* Both parentheticals were deleted at v0.20 and not restored at v0.21; they are restored here. **And the example is no longer hypothetical — v0.21 measured it**: *"how do you compute the greatest common divisor recursively"* enumerated **zero candidates**, and *"you cannot select what was never enumerated."* §1 approaches the same ground from the index side rather than by inverting the lexicon, so the **reverse-lexicon mechanism is still an unanswered park** — but it is no longer a park with no lane looking at it. **P-L** gives it one census line from H-P0 (which S-LEX names also appear in the realization lexicon's English), recorded for its future unpark case and nothing more. Unpark when a design says what running the lexicon backwards buys **over** the handle table §1 measures |
| **The register's `mathlib_head` budget** | Carried unchanged, and verified intact: `data/` did not move this cycle at all, so `blocked_set_digest`, `blocked_total` 1,878 and `mathlib_head` 1,706 are byte-identical to v0.20. The two buckets never merge into one "unsupported" number. Unpark is a resourcing decision, not a design one |
| **Licensed variant generation** | Parked, **with the trigger's checkable qualifier and its evidence sentence both restored**. The trigger, in ROADMAP-v0.19's wording: *unpark when a design says what licenses a **second** passing surface **for the same term** and why that is not decoration.* The qualifier *for the same term* was dropped at v0.20 and not restored at v0.21; without it the trigger is unfalsifiable. And the evidence sentence v0.18 paid to learn, absent from both later rows: ***a ranker is not blocked by the admission bar — it is blocked by the absence of anything to rank.*** The realization grammar emits exactly one surface per term, so the learned preference seat **had no candidate set to order and shipped empty**. **The candidate dependant v0.20 named — the input side supplying a denominator — did not materialise**: v0.21's proposer emits an *index into an enumerated list*, not a ranking over surfaces, so the ranker seat is no closer than it was. Recorded so the candidate is not carried as if it had strengthened |
| **C-V3 (human) — the determinacy sheet** | Still **ABSENT**, third consecutive cycle, and the claim it alone licenses is still not made. C-V3′ (machine) voided at v0.20, so neither reader claim exists. Unpark needs a non-maintainer marker — the same missing-population problem as **STRANGER**. §2's *one worked stranger-path transcript* is **not** that population and does not unpark this |
| **Is canonical bracketing load-bearing for a reader?** | Parked behind C-V3 above |
| **STRANGER** — outside-asker gap-object intake | Parked; unpark needs a population of askers this repository did not author. Cited by §1's non-claims rather than re-encountered — **Q60's authorship contamination is named, unpriced, and inherited by every number §1 produces** |
| **HOSTILE DICTATION** | Parked with the list's only **prohibition-shaped** trigger: it **MUST run before any untrusted stream reaches the write gate**. Neither §1's Q60 nor §2's harness opens one; LONG CON inherits the same prohibition. **And the next lane to touch this trigger owes a shown answer rather than a stated one.** v0.21 judged that its plain-text proposer opened no such stream, then shipped the proposer, and the judgement carries no test behind it. It is almost certainly right — the proposer's entire output alphabet is an index into a locally-enumerated list, which is a stronger fence than a stream audit — but *almost certainly right with nothing that could go red* is the exact shape this cycle's reviews kept finding |
| **UNSAY / the withdrawal lane** (with RECALL's clause) | Parked; revisit when withdrawal has a driver. RECALL's donated clause stands: *an over-broad impact set counts as failure, not caution* |
| **The HOLES counting table** | **PARKED — the §3.5 stop rule fired.** Accepted as a v0.19-course rider, scheduled in ROADMAP-v0.20 §3, unrun through v0.20 and v0.21. Three cycles unrun is not a cost finding, it is a scheduling fact, so it stops being a rider. Unpark condition: a cycle that wants to revive-or-close the conjecture-foundry lane schedules it **as an item**, with a number |
| **The delete-K ground-truth table** | **PARKED — the §3.5 stop rule fired**, same history, same reason. Unpark condition: a cycle that touches K's ground truth schedules it as an item. It is **not** unparked by TOLL, which measures cost rather than K |
| **ATLAS** (+ its TWINS 500-pair probe), **DEMAND**, **ABSENCE**, **RATCHET** (+ its pin audit), **GRAFT**, **IF**, **TRANSPLANT** | Parked unchanged with the triggers recorded in `reports/design-direction-v0.21.json`. **IF gains a second reason**: WITNESS's 0-of-6 is the empirical form of IF's own warning — *build the anti-triviality predicate first, or every reduction discharges and the instrument confirms itself* |
| **VERDICT**, **DEBT NOTES**, **COURIER**, **BORROWED PREMISES**, **SECOND VOICE**, **FORK/TWO-STEP/DEADLINE/THE GRADED NO**, **WORD OF HONOR**, **TWO RIGHTS** | Parked unchanged with the triggers recorded in `reports/design-direction-v0.19.json` and `reports/design-direction-v0.20.json`. **BORROWED PREMISES' next look is now due**: it was parked waiting for the supposition object to mature, and v0.21 shipped it. Its look is a rotation question, not a v0.22 item. **And four of these carry standalone probes that have now been named for two or three cycles with zero runs** — VERDICT's week-one warrant census, DEBT NOTES' one-day hand-classification probe, COURIER's one-day detached-receipt probe, and WORD OF HONOR's extraction-discipline census (*"an optional rider any cycle can run"*, named since v0.19). They stay available, and the count is written down so the **next** rotation applies §3's stop rule to them rather than rediscovering it |
| unless-receipts, detached receipt, residual ledger, antibody, two referees, wild text, negative space; resolver coverage lane (partially discharged by §1's fenced reopening), A3–A5, verified-ambiguity, range certification, W1–W3 | Unchanged |

### 4.4 New parks from the v0.22 course, with their probes

Every declined direction carries its disposition; these are quoted from
`reports/design-direction-v0.22.json` and filed in `docs/BACKLOG.md` with the
same lines. The folds, so a later cycle inherits dispositions rather than
rumours:

| direction | disposition |
|---|---|
| **CHAIN + BRIDGE** | folded → **ONE STEP**, rider R1 |
| **NOTARY** | folded → a **mandatory receipt column**, `route_voids[]`, machine-checked. It did not park; it became a schema field |
| **TWO WITNESSES** | rider → **parked item-candidate** by review H9 |
| **REBUTTAL + EXIT SIGN** | folded → **CROSSING**, parked with its probe and predicted split |
| **LONG CON** | retired to a **day-probe** |
| **LEDGER + PAUPER** | folded → **TOLL** |
| **CEILING** | → TOLL's named successor, routes with TOLL |
| **BITROT** | → **day-probe**, stop rule recorded |
| **ERRATUM** | series 2's runner-up → **rider R3** |

## 5. Governance

### 5.0 The supplementary outside series (dated 2026-08-27, maintainer-directed)

After this roadmap's course closed, the maintainer directed a
supplementary design series with **a different model family doing the
thinking** — GPT-5.6-sol via the codex CLI at maximum reasoning effort,
network-disabled, filesystem-isolated, from a neutral non-git directory,
in an academic register, with this course's full fifteen-direction
exclusion card disclosed in round one. Three rounds; brief and per-round
prompt hashes, flags, and the full adjudication in
`reports/design-direction-v0.22.json` `supplementary_series`; the three
round outputs committed at
`reports/design-direction-v0.22-supplementary/` by maintainer direction
(they are referee prospectuses, not chat — the transcript-dumping rule's
target is noise, and the maintainer asked to see the thinking).

Dispositions, so nothing is silently disposed:

- **The incumbent stands.** Nothing in the series contests HANDLES; the
  series' own intake proposal binds itself to the enumeration layer
  beneath it.
- **THE PREMISE LEDGER** (its lead: receipts certifying assumption
  *necessity* by per-premise countermodels, not mere consumption — aimed
  at the session ledger's own published byte-vs-semantic limitation) is
  recorded as a **third v0.23 incumbent-candidate, capability-class**,
  beside the instrument-class CANARY-CURVE and TOLL, with its
  preregistration-grade draft on file.
- **BOUNDED OMNISCIENCE × SPLIT-SEMANTICS** (its runner-up: a
  36-command closed island proving completeness and non-reflexive
  compiler correspondence in one artifact) is **adopted as the
  strengthened unpark formulation** of the parked conformance-successor
  lane; TWO JUDGES parks behind it as its later completion.
- **THE MEANING HANDSHAKE** contributes two bounded lessons (the
  `UNNAMED_SCOPE` typed refusal; person-confirmation subsuming the
  resolver pre-emption — both recorded in the relevant BACKLOG entries)
  and parks as a direction behind HANDLES, by its own
  recall-bounded-by-enumeration argument.
- **Its programme-level blind spot** — no prospectively sampled,
  externally sourced task distribution — is **convergent evidence for
  the parked DEMAND direction**, noted there.

- **The course gate was INVOKED strictly for the fourth consecutive cycle.**
  `reports/design-direction-v0.22.json` records three isolated series, three
  rounds each — **nine rounds, fifteen round-one directions, $2.80** — run
  headless from an empty non-git directory outside the repository under a
  strict tool denylist, with session ids and per-round prompt hashes committed
  and the isolation mode **inherited unchanged** from the v0.21 receipt. The
  brief is on file and hash-verified
  (`reports/design-direction-v0.22-brief.txt`), keeping the same self-check:
  `series_1.r1` **equals** the brief hash by construction, because round one of
  series one *is* the brief. **One provenance asymmetry is disclosed rather
  than left for a reader to find**: the receipt's own `note_on_selection`
  records that the *selected* direction's `preregistration_draft` block was
  added in the **post-review patch of 2026-08-26**, while series 2's and
  series 3's drafts were recorded at first writing. §2's claim that COLD
  RECEIPT's draft predates this roadmap is therefore checkable as written;
  HANDLES' draft is the one block that is not, and the receipt says so.
  **No incumbent design existed this cycle**; the
  occupied ground disclosed at each round two was the v0.21 outcome set and the
  standing parks, and that disclosure is recorded in the receipt's
  `exclusion_note` rather than asserted here.

- **The review gate binds the orchestrator, and this cycle is the evidence.**
  `DESIGN-handles` was **falsified twice by adversarial review before it
  landed**: first for claiming ground the repository already occupies (two
  committed non-title indices that resolve the motivating phrase today), then
  for citing producers that do not exist (S4 deleted, S5 deleted, S3 demoted).
  The receipt's own selection note records it, and the design marks every
  deviation from the outside draft as a **DELTA with the finding that forced
  it**. This is the second consecutive cycle in which the design a course
  selected failed its first review on **the same class of defect** — a design
  that does not know its own history proposes work already done. The defence is
  the one every measurement gets: an adversarial reader who checks the claim
  against the tree.

- **Five adversarial reviews, and every one found real defects.** WITNESS's
  delta review (a clean checker receipt about the wrong proposition, and a
  published mechanism false in the direction that flattered the stop); the
  C-E3 rider's review (an assertion that could not go red, **inside a suite
  added to catch exactly that**); the session-ledger merge review (a twin count
  wrong by ten thousand with every surrounding test green; a sweep whose
  published sentence was false; B8 crashing on the obvious forgery; B2 green on
  zero turns); the plain-input slice-2 review (G8 green on two limbs of three;
  the ranking that capped a ceiling invisibly); and the v0.22 design review.

- **The recurring find, for a second consecutive cycle: assertions that cannot
  go red.** v0.20 catalogued G5b's dict-literal evidence, a file compared to
  itself, a freeze list whose prose outran its machine check, and a test
  asserting *"the repository as it stands is dark."* v0.21 continued it with a
  **needle appended to its own haystack**, a **B2 verdict that counted
  divergences and so read green on zero reproductions**, and **B8 arms that
  were one tamper shape run twice**. Across five reviews: **zero wrong
  digests**. The recurring *shape* was a green check that could not have gone
  red; it sat beside defects of other kinds — a count wrong by ten thousand, a
  published sweep sentence that was false, a receipt filed under the wrong
  proposition — and the shape is what repeats, not the whole catalogue.
  This is now a standing review question and it is written into this cycle's
  gates rather than restated: §1's B3 is a **producer audit** rather than a
  token comparison, §1.5's voiding sentence can fire **at registration time**,
  and §2's B4 voids the harness on a silent pass.

- **ROADMAP-v0.21 §4.0's three relaxations were exercised for the first time,
  and the audit is honest.** All three were used, all three are kept, and one of them
  indicted this cycle.

  1. **Bug-not-result.** Used twice, correctly both times. The C-E3
     supplementary run adjudicated a control that **provably never executed** —
     new prereg amendment, new writer, new artifact, `measure_conformance.py`
     unedited so the dead code stays as the evidence. And session-ledger runs 2
     and 4 repaired **instrument** defects while leaving every **reading**
     standing: B10 read red under the repaired instrument exactly as it had
     under the broken one. **The line held**: not once was a control that ran
     and read unfavourably repaired and re-run.
  2. **Determinism-plus-commit.** Used for E5, run late with a dated lateness
     disclosure, and byte-identical. The artifact itself states what the
     lateness does not buy back: **E5 was a stop condition, and a stop
     condition checked after the thing it could have stopped had shipped is a
     check, not a gate.** The relaxation did not hide that; it is the reason
     the sentence exists.
  3. **The meetable-floor rule — and its second incident is inside the cycle
     that wrote it.** G5 froze a chance rate of `1/8 = 0.125` when the measured
     expectation over the same candidate sets was **20.62/30 ≈ 0.687**,
     making the clause **arithmetically unsatisfiable**: *blind ≤ proposer
     ÷ 2* would have needed **≥ 41 verified selections out of thirty
     questions**, of which only 24 yield a verified candidate at all. No
     proposer could have passed it. The rule was written
     because of C-E1's 0.99 flip floor; its second instance arrived one cycle
     later, in a lane that had read the rule. **A rule that has to catch the
     same defect twice in two cycles is not yet a habit**, which is why §1's
     B2, B7, B9 and the voiding sentence each carry an explicit meetability
     argument — including R1's, which argues **deliberately** that meetability
     cannot be argued, because the census exists to measure it.

- **A published stop is a result.** WITNESS stopped at its pilot and parked
  behind a construction prerequisite; plain input failed and served nothing;
  the session ledger held and served exactly one sentence. Three registered
  outcomes, three verdicts, and **not one of them was available by choosing
  which run to report** — every floor was frozen before its instrument existed.

- **Headline selection remains part of the evidence trail.** When the v0.23
  course reports, its selection and every declined disposition are recorded
  here, in the receipt, and in the release notes.

## Release gate

v0.22 is ready only if:

- **H-P0, H-P1 and H-P2 are committed in order, before the slice begins**, with
  H-P1's budget frozen from its pilot in a dated amendment **before Q60 seals**
  and Q60's candidate-reading sets sealed **before the table exists**;
- **H-P0's census publishes either way**, and **if it reads specific-handle
  coverage near ~2% the slice STOPS and publishes the census as the headline** —
  *the ingested library is effectively nameless; the naming layer must be
  built, not indexed* — with the capability sentence **not shipped**. A
  published stop is a result; a quiet descope is not;
- **the handle table ships its registered run** — B1–B8 and B10 adjudicated,
  **R-H** read out — **or** stops on a named stop condition with the reading
  published. **The voiding sentence governs, and its first limb fires before
  any arm runs**: E ≥ 2.5 voids the run as unconstructable;
- **B3's producer audit runs as an AST check, not a token comparison**, and the
  title-ablation run re-derives every Q60 answer; a single differing
  enumeration receipt between the title-present and title-absent runs is red;
- **the vacuity control's incumbent baseline is charged for candidate volume**,
  and if it matches the handle table after that charge, **the run publishes
  that handles added nothing**;
- **no resolver score moves and no served resolver byte moves** — the fence is
  tested, not asserted;
- **COLD RECEIPT's reviewed design lands before its slice**, and the slice ships
  its registered run **or** publishes its stop. **B4's omission arm must FAIL
  LOUD naming the missing dependency** — a silent pass voids the harness — and
  **no SURVIVES rests on a `program_configured` dependency** without being
  downgraded to UNTESTED;
- **R1 and R3 each publish an artifact whichever way they read**, with R1's
  census committed and its lane opened or closed, and R3's real-flip count
  published with its growth window named;
- **no stranger-usability claim is made anywhere**, and Q60's authorship
  contamination travels with every number §1 produces;
- **no reachability rate is published** — the deliverable is the partition and
  its enumerated residue;
- `check_report_regeneration.py` runs in the release refresh **with its verdicts
  in the notes**, and `ingest_wold.py reach` either runs or is reported as
  *cannot verify* rather than as a skip;
- the full suite is green on a frozen tip with retained receipts;
- every unfinished item ships or parks **in writing**;
- the outside design inquiry is **invoked** for v0.23 — the forge skill run, or
  a written course-gate amendment by the maintainer — with the receipt named,
  and the v0.23 brief carries this cycle's readouts **including any stop**, not
  only the ones that grew a number.
