# WITNESS — a discharged obligation instead of a sample

**Status: DESIGN-ONLY.** Nothing here is built, no floor here is frozen, no
run is registered by this document. ROADMAP-v0.21 §2 orders the reviewed
design *before* the slice; this is that document, and its §4 names a census
and a pilot that must land before the first floor can honestly freeze.

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
was written** — this design's input, not its registration. Verbatim:

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
- **Nothing outside the 60-name manifest** — not about the corpus, about
  `lean_workbook`, about statements the predicate did not admit, or about the
  fragment as a whole.
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
a promise. (3) It shows **a declared domain's rendering into the checker's
carrier can be checked rather than argued** —
`tests/test_conform_ce3_supplement.py` drives the same decision path over
fixtures that must come back refuted, which is B4's question in concrete form
and the template for how WITNESS shows its own clauses could have gone red.
**And nothing more:** twenty-five confirmations do not raise the credibility
of the 750 counterexamples nobody presented to a checker, do not touch a
voided control, and are not evidence that any statement is true.
