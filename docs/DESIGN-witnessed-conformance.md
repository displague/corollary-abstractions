# WITNESS — a discharged obligation instead of a sample

**Status: DESIGN-ONLY.** Nothing here is built, no floor here is frozen, no
run is registered by this document. ROADMAP-v0.21 §2 (*"WITNESS — the
conformance void's claim-kind successor"*, and its ordering obligation: *"Its
compact design lands before its slice"*) orders the reviewed design **before**
the slice; this is that document, and its §4 names a census and a pilot that
must land before the first floor can honestly freeze.

## 1. The claim-kind this repairs

v0.20's conformance layer shipped and **voided on its own controls**
(`conformance_run.json`: C-E1 missed 0.99 at 0.650, C-E2 voided at 1.75×
against a 10× floor). `NO_COUNTEREXAMPLE_FOUND` certifies nothing
universally — *a sampler that finds no counterexample has told you about its
sample* — and the 3,298 statements carrying it are void besides. WITNESS does
not sample better; it changes what is produced. Per statement, a
**checker-signed lemma** that the compiled evaluator and the statement agree
over a declared domain: a universal claim about that statement, where a clean
sample is a claim about the sample. Everything below exists to stop that from
becoming a claim the instrument cannot support.

## 2. The frozen draft, quoted before it is elaborated

`reports/design-direction-v0.21.json`
`outcomes.series_1.preregistration_draft`, recorded **before ROADMAP-v0.21
was written** — this design's input, not its registration. Its five fields
below carry the receipt's strings unaltered; the **bold labels and the line
breaks are this document's**, since the receipt stores each field as one
unwrapped line:

> **fragment:** quantified linear arithmetic over Z and Q (decidable)
>
> **artifact:** target_manifest (60 sealed names + 10 out-of-fragment decoys,
> selection-predicate hash, checker pins) + agreement_lemma records
> (obligation forall x in D: eval(S)(x) <-> S(x); verdict in {discharged,
> not_discharged, rejected_trivial}; nontriviality_witness; proof + sandbox
> receipts) + mutant_ledger
>
> **gate:** B1 manifest sealed first; B2 >=40/60 discharge, all 60 published;
> B3 50/50 seeded mutants of DISCHARGED parents rejected (49/50 voids); B4
> self-comparison obligation must return rejected_trivial (one discharge
> voids the instrument); B5 nontriviality witness required; B6 sandbox >=1000
> points per discharged evaluator, any disagreement voids the slice; B7
> cold-machine replay; B8 both receipts or nothing; B9 one cycle, partials
> published
>
> **voiding_sentence:** If all 60 targets discharge and all 50 mutants are
> rejected on first attempt, or if any decoy discharges, the run is void and
> reports an instrument failure, not a capability
>
> **residual_risk:** the obligation is built from the compiler's own
> front-end reading of S -- a uniform front-end misreading survives every
> clause; only an independent re-reading (second front-end or human
> transcription) prices it, and that is not in the slice

Three clauses are load-bearing in a way a reader should not have to infer.
**B4 is a self-comparison trap**: an obligation comparing the instrument to
itself must return `rejected_trivial`, and one discharge voids the whole
instrument. **B3's 49/50 voids** — too good is a failure. And the **voiding
sentence forbids a clean sweep**. All three are one rule, which ROADMAP-v0.21
§4 states as the cycle's recurring catch: *a green assertion that could not
have gone red is not evidence.*

## 3. What a slice would produce

Field names are the draft's; the elaboration is this document's.

**`target_manifest`** — sealed first (B1); nothing else exists until it is
committed. `selection_predicate` (executable, over the committed census),
`selection_predicate_hash`, `targets[]` (60 ids), `decoys[]` (10
out-of-fragment ids), `checker_pins` (toolchain string + binary digest, under
`scripts/external_verifier.py:196-217`'s never-download rule),
`census_digest`, `candidate_population` — how many the predicate admitted, so
a reader sees how much room the selection had.

**`agreement_lemma`** — one per target and per decoy: `statement_id`,
`domain` (carrier, division, subtraction — DESIGN-statements-that-run §3.3's
declared readings), `obligation` (the rendered
`forall x in D: eval(S)(x) <-> S(x)`), `verdict` in `{discharged,
not_discharged, rejected_trivial}`, `nontriviality_witness`, `proof_receipt`,
`sandbox_receipt`. B8 is **both receipts or nothing**: a proof receipt with
no sandbox receipt is not published as `discharged`.

**`mutant_ledger`** — 50 seeded mutants of DISCHARGED parents only (mutating
a parent that never discharged tests nothing): `parent_id`, `mutation_class`,
`mutant_obligation`, `verdict`, `rejected`, plus the **discard rule ported
first** — C-E1's paid-for lesson that a mutant canonicalising back to its
source is not a mutant, and is discarded and counted before any rate.

## 4. The fragment does not yet exist, and W0 is why

The draft names **quantified linear arithmetic over Z and Q**. Against this
repository's committed compiler that fragment is close to empty, and the
design says so here rather than at seal time. An indicative walk of every
statement `conform.compile_statement` admits — counting a conclusion linear
when no variable appears at degree > 1, in a product with another variable,
or under `inv` — reads: **66 free-variable statements linear on both sides,
every one declaring carrier `Nat`.** Zero `Int`, zero `Rat`. (The 293 linear
*ground* rows carry no quantifier and are E1's business.) Two structural
consequences: **60 targets out of ~66 candidates is not a selection, it is
the population** — a sealed predicate admitting 66 and taking 60 has almost
nothing to do, and the thin-denominator rule applies, so a manifest that is
91% of its own candidate set says so rather than presenting 60 as a sample;
and **`Nat` is not `Z`** — the schema declares Nat with `truncating` division
and `truncated-at-zero` subtraction, which are not the integers' operations,
so an obligation quantified over Z discharged about a Nat-declared statement
adjudicates a different statement.

**W0 — the fragment census, a construction prerequisite.** Before any
manifest, a committed census fixes the executable fragment predicate, the
candidate count, the carrier distribution, and whether the fragment is
`Nat`-with-declared-readings — in which case the draft's *"over Z and Q"* is
**amended in writing**, not quietly reread — or whether an `Int`/`Rat` schema
row set is authored first. **If the census admits fewer than 70 candidates
the 60-name manifest is withdrawn and the number is set from the census.** A
manifest that consumes its population is the construction defect §4.0(3)
exists to catch.

> **Amendment (2026-08-26), written after W0 ran and BEFORE anything is
> sealed.** `experiments/witness_fragment_census.json`, predicate digest in
> the artifact. **The census admits 45 candidates out of 12,777 statements
> walked, and all 45 declare carrier `Nat`.** The rule above fires, and three
> things follow, in writing rather than by reread:
>
> 1. **The 60-name manifest is WITHDRAWN.** The manifest is set to the
>    **whole population, 45 targets, and there is no selection at all** —
>    which is the honest form of the finding that 60 of 66 was never a
>    selection. A predicate that admits 45 and takes 45 cannot have chosen
>    favourably, and `target_manifest.candidate_population` equals
>    `len(targets)` so a reader sees it immediately. Decoys stand at 10,
>    drawn from the 4,242 compiled-and-quantified statements the predicate
>    rejected, by a recomputable rule (sorted by id, first ten).
> 2. **The fragment's WORDING is amended, not reread.** The draft said *"over
>    Z and Q"*; the tree declares `Nat` with `truncating` division and
>    `truncated-at-zero` subtraction for every admitted row, and those are not
>    the integers' operations. WITNESS's fragment is hereby **quantified
>    linear arithmetic over the declared `Nat` domain**. Nothing is claimed
>    about Z or Q this cycle.
> 3. **B2's floor is not yet a number**, and cannot be until W1 reads. The
>    draft's ≥40/60 is void along with the 60.
>
> The population is small, and the design says so where a rate would
> otherwise be quoted: **45 is a thin denominator**, every target is published
> by name, and no percentage of it is presented as a property of the corpus.

> **Second amendment (2026-08-25), correcting the first. Never an edit of
> it.** Delta review found the amendment above stale in seven places. The
> committed census (`experiments/witness_fragment_census.json`) reads **37
> candidates, not 45**; the decoy pool is **4,250, not 4,242**; and **no
> manifest of any size was sealed**, so the sentence *"the manifest is set to
> the whole population, 45 targets"* is **RETRACTED** — the slice stopped at
> W1 before any seal, and a manifest sentence in the present tense described
> something that never happened. What survives unchanged: the 60-name
> manifest is withdrawn, the fragment is `Nat` and not Z or Q, B2's 40/60 is
> void, and the denominator is thin enough that no percentage of it is ever
> quoted.
>
> **The whole chain, in prose, because four numbers appeared across two
> documents and only the last one is current.** **66** was §4's *indicative*
> walk, and it checked only the conclusion. The committed predicate holds
> **guards to the same linearity standard** — a linear conclusion under a
> quadratic guard is not a statement of linear arithmetic — and that is the
> single largest drop: **21 statements**, taking 66 to **45**. Then the
> predicate was executed against the obligation builder three times and lost
> three more groups: **3** carrying a literal that is not a `Nat` (45 → 42),
> **4** carrying a unary negation outside a `+` node (42 → 38), and **1**
> whose guard names a slot the binder does not bind (38 → **37**). Every one
> of those was found by *running the builder*, never by reading the
> predicate, which is why the predicate's last clause is now a call into it.
>
> **§8's non-claim is corrected by this amendment too.** It read *"Nothing
> outside the 60-name manifest"*; the 60-name manifest does not exist. The
> non-claim is now: **nothing outside the 37-name census population**, and in
> fact nothing at all, since nothing was discharged.

## 5. Meetable floors — ROADMAP-v0.21 §4.0(3)

> *Every frozen floor now ships with a meetability argument — a pilot, a
> construction argument, or a bounded-class analysis showing a correct
> instrument can reach it. A floor without one is a construction defect
> discovered at registration time, not a gate waiting to void.*

Its origin is C-E1's 0.99, unmeetable by any correct sampler over `Nat` for
whole mutation classes. **B2's ≥40/60 needs a PILOT**, the only honest
argument available: nothing in this tree knows what fraction of these
obligations a hermetic core-Lean `decide`-or-`omega` discharge reaches, and a
construction argument would be a guess with a number on it — which is what
0.99 was.

**W1 — the six-statement pilot.** Six statements drawn from W0's census by
the committed predicate and **named in the pilot artifact before any
obligation is written**, spanning the fragment's shapes: unguarded and
guarded; one, two and three variables; at least one box-constraint guard and
one that couples variables. Their obligations are built and discharged **by
hand-shaped Lean** — the point is to learn what the checker can do, not to
test a builder that does not exist — and **the floor is frozen from the
pilot's reading, in a dated amendment, BEFORE `target_manifest` seals**. If
the pilot discharges 2 of 6 the floor is not 40/60; if it discharges **0 of
6**, WITNESS publishes that as its result and the slice does not open.
**Precedent, named:** C-V3′'s machine reader, whose floor was *"a
construction prerequisite, not a number picked now"* and whose pilot ran
before the freeze (`docs/DESIGN-voice-completion.md:650-658`) — the document
that also records *"an instrument that cannot repeat itself can only void,
never confirm."*

> **Amendment (2026-08-26): W1 RAN AND READ 0 OF 6. THE SLICE DOES NOT
> OPEN.** `experiments/witness_pilot.json`. Six statements drawn by the
> committed rule, all six shape classes filled, one box guard and two
> coupling guards among them. **Every one came back `rejected_trivial`**, and
> so did all census candidates when the builder was run over the population.
> *(That population read 38 when this amendment was written and reads **37**
> after the C-1 builder fix below; the verdict is unchanged and the number is
> corrected rather than left to be inferred.)*
>
> **No floor is frozen**, because a floor is a fraction a correct instrument
> can reach and this one reached none. **No manifest is sealed.** No
> obligation builder runs over the population, no mutant ledger is built, no
> sandbox executes, and **no capability is claimed**.
>
> **Why the zero is structural, and therefore a finding rather than a
> shortfall.** The committed parser emits **left-nested binary** `+` and `*`
> nodes — `a - b + c` parses as `+(+(a, neg(b)), c)`, never as a flat
> three-operand node — so `eval_under_domain`'s hoisting has nothing to
> hoist. Within this fragment *"what the evaluator computes"* and *"the
> statement as written"* are the **same tree**, and the obligation is
> `P ↔ P` for every census candidate.
>
> > **Correction (2026-08-25, delta review).** The sentence above originally
> > ended *"for every term this parser can produce"*, and that was **false**.
> > A **binary** `+` whose FIRST operand is a `neg` still diverges: the
> > evaluator groups `+(neg(a), b)` as `b - a` and the written reading is
> > `(0 - a) + b`, which differ over `Nat`. The parser **does** emit that
> > shape — the pilot's computed `divergence_reachability` block counts
> > **0 n-ary nodes in 86,547 walked over 8,586 parsed statements, 0 leading
> > `inv` products, and 25 statements carrying a leading-`neg` sum, 18 of
> > which compile**. What keeps them out is the **fragment's linearity
> > predicate**, not the parser: **0 of the 25 are inside the census
> > population**. The claim is now computed in the artifact rather than
> > argued in prose, and a test goes red if either half flips.
>
> **The pilot's controls say the zero is a reading, not a broken pipeline.**
> A hand-built non-trivial obligation in exactly the divergent shape
> **discharges**; the same shape unguarded and false is **refused** by
> `omega`; and B4's self-comparison trap returns `rejected_trivial` through
> the ordinary tree comparison, with no branch that recognises being tested.
>
> **And the counterfactual is the whole point.** Every pilot obligation was
> handed to the checker anyway with the triviality test switched off:
> **`omega` accepted 6 of 6.** An instrument without B4 would have published
> six discharged agreement lemmas, cleared its gate, and reported a
> capability — from `P ↔ P`. That is not a hypothetical about some other
> design; it is this design's own output with one clause removed.
>
> **What this changes for WITNESS.** The draft priced the single-front-end
> problem as a *residual risk* — *"a uniform front-end misreading survives
> every clause"* — and put the independent re-reading out of the slice. The
> pilot's reading is stronger and less comfortable: it is not that a
> misreading survives the clauses, it is that **there is nothing else in the
> obligation**. An independent second reading of `S` is therefore a
> **construction prerequisite of any WITNESS slice**, not a residual to be
> narrowed later, and §6's W2 transcription audit is the cheapest form of it.
> That is this pilot's recommendation to the next cycle — and the correction
> above **strengthens** it rather than softening the stop. The divergent
> class exists and is **non-linear**, so growing the fragment to reach it
> would give the drafted obligation content, but that content would still be
> one front-end's parse compared with itself under two grouping rules. **A
> second front-end is needed BEFORE fragment growth, not instead of it.**

**B3's 50/50 has a construction argument, a different kind of claim.** B2 is
empirical; B3 asks whether a mutated statement still agrees with its parent's
evaluator, and for a mutation that provably changes the term's value
somewhere in the domain a *correct* checker cannot discharge it — the lemma
is false. So 50/50 is meetable **by construction, conditional on the
generator being verified-to-change-the-term** — the verification C-V4′
shipped and C-E1 lacked: *every seeded mutant carries a witness point at
which parent and mutant evaluate differently, computed and recorded before
the mutant enters the ledger; a mutant without one is discarded and counted.*
Without that clause 50/50 is unmeetable for the reason 0.99 was, and **the
clause is part of the freeze, not an implementation detail.** 49/50 still
voids: a perfect sweep more likely proves mutant rejection is trivial here,
which is B4's question wearing a different hat.

## 6. The obligation builder, and what it may not read

**B4 — the self-comparison rejection.** The builder is handed an obligation
whose two sides are the same object, `eval(S)(x) <-> eval(S)(x)`, and must
return `rejected_trivial`. **One discharge voids the instrument**: something
that discharges a tautology will discharge anything, and every other clause's
green goes uninformative at once.

**B5 — the nontriviality witness.** Every `discharged` lemma carries a point
in `D` where the body is *non-vacuous* — guard holds, both sides evaluate.
v0.20 already met this shape: `guard_measure_zero` refusals exist because an
equality conjunct admits a measure-zero set. A vacuous discharge is
`rejected_trivial`.

**Independence constraints.** The builder reads the **committed census's**
parse and the **schema's declared domain**. It does not read the evaluator's
*verdicts* or `conformance_run.json`, and never sees which statements v0.20
labelled NONCONFORMANT — a builder that knew the answers could select
obligations that discharge.

**The residual risk, quoted rather than paraphrased**, because it survives
every clause above:

> the obligation is built from the compiler's own front-end reading of S -- a
> uniform front-end misreading survives every clause; only an independent
> re-reading (second front-end or human transcription) prices it, and that is
> not in the slice

**Scope, stated hard.** Both sides of `eval(S)(x) <-> S(x)` come from one
parse by one front-end. If it reads `S` wrongly — the same way on both sides
— the obligation is true, discharges, and certifies agreement between two
readings of a statement nobody wrote. No clause B1–B9 sees this: every clause
is downstream of the parse. **Partial mitigations, named as partial:**

- **B6's sandbox executes the evaluator on ≥1000 points per discharged
  evaluator**, any disagreement voiding the slice. That prices a *proof path*
  diverging from the *execution path* — real and worth having — but **not** a
  front-end misreading, because the sandbox runs the same compiled evaluator
  the obligation was built from. Calling it a mitigation for the front-end
  risk would be the error this section exists to prevent.
- **W2 — the narrowing audit, registered now.** A **human transcription
  spot-check of 5 obligations**, drawn by a committed rule from the
  discharged set, transcribed by hand from the Lean source statement and
  compared to the built obligation. Five *narrows*, it does not price: it can
  find a systematic misreading and cannot bound one. Published whichever way
  it reads; one mismatch promotes the residual from **named** to
  **measured** and the served claim carries it.

## 7. Trusted and untrusted

**Trusted:** the committed parser, evaluator, sampler, census and domain
schema, digest-frozen before the builder exists (E7's shape); the pinned Lean
toolchain, **invoked by absolute path — no elan proxy, no lake, no Mathlib,
no network, never a download**; the committed corpus files.

**Untrusted:** the obligation builder (which is why B4 and B5 exist); the
checker's *silence* (a timeout is `not_discharged`, never `discharged`);
`sorry` in any form (an axiom audit per `external_verifier.py`'s
`#print axioms` containment, so a `sorry` surfacing as `sorryAx` fails though
the compiler exits 0); and every domain row, all authored here. **No learned
component anywhere** — not in selection, obligation construction or mutation;
there is no seat for one, and the absence is declared rather than left to be
noticed.

## 8. Stop conditions and non-claims

**Stop and publish** if W0's census admits fewer than 70 candidates (manifest
size withdrawn and reset from the census); if W1's pilot discharges 0 of 6
(the slice does not open); if the pilot cannot be run hermetically at all; if
B4's self-comparison obligation discharges, or any decoy discharges (the
instrument is void and reports an instrument failure, not a capability); or
if the mutation generator cannot produce witness-carrying mutants (B3's floor
is then unmeetable and is withdrawn before it is frozen, not left to void).

**Non-claims:**

- **No conformance rate.** Discharged lemmas are published by name, never as
  a percentage of a corpus; a discharge is a claim about one statement over
  one declared domain.
- **Nothing retroactive about v0.20's run.** `conformance_run.json` stays
  void; a discharged lemma about a statement that once read
  `NO_COUNTEREXAMPLE_FOUND` does not un-void that verdict, restore that run's
  controls, or license any sentence about the 3,298.
- **Nothing outside the census population** — not about the corpus, about
  `lean_workbook`, about statements the predicate did not admit, or about the
  fragment as a whole. *(Corrected 2026-08-25: this read "the 60-name
  manifest", which §4's first amendment had already withdrawn and which was
  never sealed at any size. See §4's second amendment.)*
- **The domain is still this repository's declaration.** A discharged lemma
  says evaluator and statement agree *under the domain the schema declared*,
  not that the schema read the source statement correctly — §6's residual,
  discharged by no clause here.
- **No `verified_by` links, no epistemic-ladder movement.** An agreement
  lemma is not a proof of the statement; it is a proof about the evaluator.
- **EXHIBIT's revival is conditional on a NON-VOID run** (ROADMAP-v0.21 §2);
  a voided WITNESS leaves it declined with a second reason.

## 9. What the C-E3 supplement does and does not feed into this

`experiments/conformance_ce3_supplement.json` (§2's early rider) read **25 of
25 sampled counterexamples confirmed** by the pinned checker on closed ground
propositions. Stated explicitly, either way:

**It does NOT feed the fragment choice.** All 25 rows are **nonlinear** —
squares, cubes, products of variables — and all declare carrier `Nat`. Not
one is in the draft's fragment, and a reading taken entirely outside a
fragment cannot bear on whether that fragment is the right one. §4's census
settles that, not the supplement.

**It DOES feed three premises.** (1) The pinned toolchain's `decide` reaches
closed `Nat` propositions of this corpus's size and shape — 25 of 25 reduced,
under half a second each, hermetically — the toolchain-reach premise behind
B6's sandbox and behind any `Nat` obligation at all. (2) The **substitution
discipline** is committed and tested: bindings land structurally at the
parsed tree's `slot` nodes, never textually, so WITNESS's *"obligations are
closed terms by construction"* clause inherits an implementation rather than
a promise.

> **Correction (2026-08-25, delta review): the sentence above was itself a
> promise, and W1 produced its counter-instance.** The C-E3 supplement does
> close its terms; the WITNESS obligation builder did **not**. It rendered
> guard conjuncts without checking that their slots are bound by the binder,
> and `lean_workbook_10679`'s guard names `c` while the sampler binds only
> `a` and `b`. Lean's `autoImplicit` quietly prepended `∀ {c : Nat}` and the
> checker returned **exit 0 on a strictly stronger proposition than the row
> it was filed under**, with no diagnostic. Inheriting a discipline from a
> sibling script is not the same as implementing it, and the gap was invisible
> precisely because the receipt looked clean. The builder now **refuses** an
> unbound slot as a typed refusal, every probe runs under
> `set_option autoImplicit false`, and the census lost one candidate to the
> new clause (38 → 37). (3) It shows **a declared domain's rendering into the checker's
carrier can be checked rather than argued** —
`tests/test_conform_ce3_supplement.py` drives the same decision path over
fixtures that must come back refuted, which is B4's question in concrete form
and the template for how WITNESS shows its own clauses could have gone red.
**And nothing more:** twenty-five confirmations do not raise the credibility
of the 750 counterexamples nobody presented to a checker, do not touch a
voided control, and are not evidence that any statement is true.
