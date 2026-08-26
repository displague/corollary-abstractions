# v0.21.0 — three registered outcomes, three different verdicts, and every one published with its mechanism

Three things were registered this cycle. One **served**, one **failed
honestly**, and one **stopped itself before it became an instrument**. None of
the three was re-executed to read better, and each is published with the
mechanism that produced its verdict rather than with the number alone.

- **SERVED.** The session ledger holds. `R1 HOLDS` on gate run 4: *recorded
  sessions replay, and conditional answers name the assumptions they
  consumed.* Nothing more.
- **FAILED HONESTLY.** Plain input's `R2 FAILS`, and the failure is the
  finding: a **capability-blind arm beat the model — 22 verified selections
  against 17** — because the frozen metric counts verified selections and
  **structurally cannot reward a correct refusal**. All six of the model's
  `NONE` answers were verified correct refusals. The blind arm has no `NONE`
  in its alphabet.
- **STOPPED ITSELF.** WITNESS discharged **0 of 6** pilot obligations, every
  one `rejected_trivial`, because one shared front-end makes the obligation
  `P ↔ P`. Handed the same six obligations with the trap removed, the checker
  **accepted 6 of 6** — which is what an instrument without the trap would
  have published as a capability.

The governance layer that made all three readable was itself exercised for
the first time: ROADMAP-v0.21 §4.0's three maintainer-directed relaxations
were used, and audited honest, in the same cycle they were written.

**Links** — previous release: [v0.20.0](RELEASE-v0.20.0.md) · closed plan:
[ROADMAP-v0.21](ROADMAP-v0.21.md) · next plan:
[ROADMAP-v0.22](ROADMAP-v0.22.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the answer that was right and scored wrong](blog/the-answer-that-was-right-and-scored-wrong.md)

## The headline finding: a metric that could not see a correct refusal

**Before.** Plain prose reached the kernel and either resolved or exhausted.
The design's plan was to put a small model between the two: exact code
enumerates candidate readings, the model selects one, exact code verifies the
selection, and anything it cannot ground is served as a **named supposition**
rather than guessed. The control frozen before any of it existed:
a **capability-blind** arm — a seeded uniform draw over the same candidate
lists — must make at most **half** the model's verified selections, or the
seat ships empty.

**Now.** The arm was run, and the blind arm **won**.

| arm | verified selections on the sealed thirty | rule |
|---|---|---|
| the proposer (`ollama:qwen3:4b-instruct`, temperature 0) | **17** | — |
| the capability-blind seeded draw | **22** | required **≤ 8.5** |
| **G5** | | **RED** |

**And the draw was typical, not lucky** — the run publishes the blind arm's
own analytic expectation beside its observation: *sum over questions of
verified ÷ candidates* = **20.62**, against an observed **22**
(`experiments/plain_input_run.json`, `gates.G5.analysis`).

**The mechanism, and it is not flattering to the metric.** The rule counts a
**verified selection**. It has no way to score a **correct refusal**.

- The model answered `NONE` on **six** questions: `g1-08`, `g1-22`, `g1-26`,
  `g1-27`, `g1-29`, `g1-30`.
- **Every one of those six had verified candidates available**, and the blind
  arm — whose output alphabet contains no `NONE` — took them, on all six.
- Nine of the thirty sealed questions were **authored to exhaust**. The
  question set's own words: *"a candidate that verified for one of them would
  be the proposer inventing rather than selecting."* The model selected for
  **zero** of the nine. The blind arm selected a verified candidate for
  **five**.

So the control **rewards, in its blind arm, exactly the behaviour the design
calls inventing** — and penalises the model for the one thing the design
wanted from it.

**The floor itself was mis-derived, and that is the second incident of a rule
this cycle wrote.** The preregistration froze the blind arm's chance rate at
`1/8 = 0.125` — the reciprocal of the candidate limit. The measured
expectation is **20.62 / 30 ≈ 0.687**.

**And that makes the rule arithmetically unsatisfiable, which is the sharpest
form of the finding.** The clause is *blind ≤ proposer ÷ 2*. The proposer
cannot lower the blind arm's score — that is a property of the candidate lists
— so the only way to satisfy the clause is to **raise the proposer's**. Against
the blind arm's own expectation of 20.62 the proposer would need **≥ 41.24
verified selections**; against the observed 22 it would need **44**. There are
**thirty questions**, of which only **24** yield a verified candidate at all
and the sealed ceiling is **21**. **No proposer, however good, could have
passed this clause.** That is precisely what ROADMAP-v0.21 §4.0(3)'s
meetable-floor rule was written to prevent — after C-E1's 0.99 flip floor cost v0.20 its
conformance claim. **§4.0(3) now has its second incident, and it is inside
the cycle that authored the rule.**

**Nothing was rewritten because of any of this.** The collapse rule was frozen
before the proposer existed and was scored as frozen. The artifact says so in
its own words: *"A rule rewritten because its instrument surprised its author
is not a preregistration."*

**And the red survives the obvious objection.** Exclude all nine
exhaust-authored questions and re-score on the remaining twenty-one: the
proposer reads **17** (all seventeen of its verified selections were on
non-exhaust questions) and the blind arm reads **17** as well — still far
above the required 8.5. The exhaust-authored subset explains *why* the gap
opened; it does not close it.

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/plain_input_run.json',encoding='utf-8')); \
    g=d['gates']['G5']; print(g['verdict'], g['blind_verified_selections'], \
    'vs', g['proposer_verified_selections'], 'required <=', g['half_of_the_proposer']); \
    a=g['analysis']['the_draw_was_typical_not_lucky']; \
    print('blind expectation', a['expected_blind_verified_selections'], 'observed', a['observed'])"
RED 22 vs 17 required <= 8.5
blind expectation 20.62 observed 22
```

### What the red does and does not take away

**Nothing serves.** `CoreSession.proposer` defaults to `None`; `conditional`
is registered in the frozen status alphabet but sits **outside**
`ANSWERING_STATUSES` (`scripts/serve_chat.py:176`); and G7b proves the
zero-scoring is mechanical rather than documented — the same 160-token
content scores **160 useful tokens as `solved` and 0 as `conditional`**,
driven through `measure_throughput.build_records` with a `solved` arm as the
control that makes the zero evidence rather than a no-op.

**The trust shape came out stronger than the design argued for it.** The
design's §4 defended its Phase-2 disposition by claiming the proposer's output
alphabet is the registered line grammar. Slice 1's P1 measured that
**false**: of fifteen template classes, **five are closed** (34,863 admitted
commands between them), **one is environment-gated**, and **nine admit
countably infinite languages** — including the two rows where plain prose
lands (`experiments/session_p1_command_bound.json`). *"route_line accepts
it"* is a parse check, not membership in a finite set.

What was built instead is stronger: the proposer **never emits a query string
at all**. It emits an **index into an exactly-enumerated candidate list**,
plus the token `NONE` (`scripts/plain_proposer.py`;
`docs/DESIGN-plain-input.md` §8.1). Phase 2 holds by construction rather than
by argument — and the design's own argument for it is marked false where it
stands rather than quietly repaired.

### G9: the silent binding lives one row upstream, and is NOT MET

The defect slice 2 was aimed at — the resolver answering an underdetermined
prose line with a bare `found`, with nothing recording that a reading was
selected — **is not repaired by this slice, and the release says so in the
same sentence that reports the capability.**

`DESIGN-plain-input` §2.2 confines the proposer to **row 12**, the row where
nothing binds. The silent binding happens at the **resolver**, an earlier
row. Serving all thirty sealed questions measured the surface wider than P2's
two fixtures had suggested: **13 of 30 return `found` from the resolver
before `_route_proposed` is consulted at all** — upgrading P2's 2-of-10 —
with five more pre-empted at `waiting` by the resolver's own ASK subloop.
Only twelve reached the proposer.

G9 is **NOT MET by orchestrator ruling**, adjudicated in advance rather than
scored out of this run's numbers (`experiments/plain_input_prereg.json`
amendments 3 and 4), and its repair is a **designed successor** owing three
things: its own preregistration, its own capability-blind control (G5's is
scoped to selection among enumerated candidates and says nothing about a
changed bind rule), and a **K re-measurement**, because the resolver row sits
inside the serving path the throughput book scores. The **thirteen question
ids are committed as fixtures** in `docs/BACKLOG.md`.

### Three findings the run published about itself

- **F1 — the "not open-domain" non-claim was contradicted.** Two questions
  authored to exhaust came back as **clarifications naming corpus readings**:
  `g1-26` *"how do i change a tyre"* was offered *Average Rate of Change*,
  *Fundamental Theorem of Calculus, Evaluation Part* and *Derivation Takes Its
  Category from the Affix*. **The proposer is not what broke it** — it
  answered `NONE` on both. The **branch rule** fires on the count of verified
  candidates and never consults the model's `NONE`. Frozen in amendment 2
  before it had ever run, so it is published and filed rather than adjusted.
- **F2 — the design's own motivating example enumerates nothing.**
  §2.3 named the `gcd` miss as the residue the proposer is aimed at. *"how do
  you compute the greatest common divisor recursively"* enumerated **zero
  candidates**; the proposer was never asked. **You cannot select what was
  never enumerated.** Five other sealed questions enumerate nothing for the
  same reason. The parked synonym layer is still the blocker.
- **F3 — verification discarded a correct selection.** On *"how do you compute
  a factorial iteratively"* the enumerator offered *Factorial, Iterative
  (TheAlgorithms)* first and the model selected it — the right reading. It did
  not verify. The two candidates that did verify were both about the **double**
  factorial, so the person was asked to choose between two wrong readings while
  the right one was discarded **before any receipt existed**.

And one more, found only by adversarial review after the reading (§8.5 of the
design): on `g1-22`, *"what does the corpus say about the distributive law"*,
the corpus holds **two correct readings that both verify** —
`settheory.boolean_laws.distributivity_meet_over_join` and
`logic.boolean_laws.distributivity_meet_over_join` — enumerated at **ranks 21
and 23**, outside the frozen limit of 8. The mechanism is one line: the total
order is *(descending word overlap, ascending **title length**, statement id)*
(`scripts/candidate_enumerator.py:261`), everything ties on the single word
`law`, and `Ohm's Law` outranks *Distributivity of Intersection over Union*.
**The `NONE` was a correct refusal against a mis-ranked list**, and the run
counted it as a failed selection. Independent review reached the same reading
for all six refusals — *"all six NONEs verified correct refusals"*. Not
repaired: the order and the limit were frozen together **because they move the
blind arm's baseline**, and moving a control's baseline with the results in
view is the thing preregistration exists to prevent.

## The second outcome: the session, and it serves

**Before.** `scripts/supposition.py` built a fresh executor per typed line and
threw the state away. A `suppose …` line was built, used, and forgotten by the
next line; the served supposition receipt was a single key,
`{"derivation": "session"}`.

**Now.** A conversation is a **journal**: one record per turn, chained, with
per-record keyed MACs and an out-of-band seal, and every answer naming
**which assumptions it consumed** — recorded at the moment the machinery reads
one, not asserted by a writer.

`R1 HOLDS` (`experiments/session_ledger_run4.json`). The served claim,
exactly: ***recorded sessions replay, and conditional answers name the
assumptions they consumed.*** Nothing more.

| clause | reading |
|---|---|
| **B1** clause 1 — seal before replayer | **MISSED**, published unreinterpreted through all four runs |
| **B1** clause 2 — no sealed file edited | GREEN, 120 files checked, 0 edits |
| **B2** — unmutated replay reproduces every sealed turn | GREEN, **410 of 410**, 29.9 s against an 1,800 s budget |
| **B3** — every pin field perturbed individually | GREEN, **300 perturbations**, no sampling, 0 failures |
| **B4** — mutating a **cited** assumption changes the answer or refuses by type | GREEN, **58 of 58**, **30 of them by typed conflict refusal** |
| **B5** — sham assumptions must not flip an answer | GREEN, **0 flips of 60** |
| **B6** — mutating live-but-**uncited** assumptions | GREEN, **0 flips of 42** (registered denominator 30) |
| **B7** — every refusal turn carries a citation list | GREEN, 70 refusal turns, empty allowed, null red |
| **B8** — tamper detection against a chain-repairing adversary | GREEN, **20/20** on each of four arms, every detection from the keyed MAC or the out-of-band seal |
| **B9** — slice 2's clause | **NEVER** — registered, scored never, absence recorded rather than inferred |
| **B10** — stateless equivalence on uncited turns | GREEN, **0 misses of 260** |
| **B11** — coherence, `check_regeneration` green | GREEN, exit 0 |
| **B12** — citations are read-derived and corroborated | GREEN, **410 turns checked, 0 uncorroborated** |
| **B13** — arm-blind 20-turn hand audit | GREEN, **20 of 20** against a floor of **16** |
| **R1** | **HOLDS** |

The corpus behind it: **60 sessions sealed, A/B 35/25, 410 turns, 130
binding-dependent** (half B: 25 / 171 / 58) —
`experiments/session_corpus_seal.json`. Zero sessions were excluded by the
no-write-gate rule, and the seal publishes **both readings of the floor
sentence**, including the one under which this cycle would have stopped.

**Demonstrate.** A committed journal, replayed offline against the tree:

```
$ PYTHONIOENCODING=utf-8 python scripts/replay_session.py experiments/sessions/v021-p08.json
{
  "divergences": [],
  "first_divergence_turn": null,
  "pin_mismatch": [],
  "refusal": null,
  "session_id": "v021-p08",
  "stateless": false,
  "turns_reproduced": 9,
  "turns_total": 9
}
```

And the surface a person types at:

```
$ printf 'suppose n = 4\nsuppose t = 5\nn + t\n' | PYTHONIOENCODING=utf-8 python scripts/harness.py
...
line    : suppose n = 4
route   : supposition
status  : waiting
detail  : held as conjectured in a frame you own
  this is conjecture held inside a frame you own; it is not a corpus fact
  and nothing later will quote it as one
...
$ printf 'suppose x = 1\nretract a999\n' | PYTHONIOENCODING=utf-8 python scripts/harness.py
line    : retract a999
route   : retraction
status  : refused
detail  : no live assumption 'a999' in this session; nothing was changed
```

That `retract` line is not decoration — it is where B10 went red, twice, and
the story is below.

### Four runs, and why the first three are part of the record

| run | B10 | capability-blind baseline | B6 | B8 arms | R1 |
|---|---|---|---|---|---|
| 1 `session_ledger_run.json` | **RED**, 10 of 260 | RED (broken comparator) | 21 cases vs floor 30 | 2 | **FAILS** |
| 2 `session_ledger_run2.json` | **RED**, the same 10 | GREEN, 0/58 | 42 cases | 2 | **FAILS** |
| 3 `session_ledger_run3.json` | GREEN, 0/260 | GREEN, 0/58 | 42 cases | 2 | **HOLDS** |
| 4 `session_ledger_run4.json` | GREEN, 0/260 | GREEN, 0/58 | 42 cases | **4** | **HOLDS** |

**Run 1's red was real leakage, and the fence caught it.** All ten misses were
the same line — `retract a999`, an id the session does not hold. The refusal
rendered one way with a ledger attached and another without, which is the
ledger's *existence* reaching the bytes of an answer that consumed no
assumption. **B10 is the fence that makes "state is a shipped property" an
honest sentence**, and on its first execution it went red for a real reason.

The repair was adjudicated under the **suite-gate precedent** rather than the
no-chase rule: red is a construction defect in the object, fix the defect, run
fresh at the fixed tree, retain every receipt. That precedent applies here and
not elsewhere for a stated reason — **the §8 controls were green throughout**,
so there was no voided control for the no-chase rule to protect. Two candidate
fixes were written down before either was coded, and **(a) was chosen**:
widening the citation contract so the refusal cites what it read would have
meant a citation no longer implied the answer consumed a premise.

**Run 2** was a supplementary run under §4.0(1)'s instrument-gap half. Reading
run 1 exposed three defects in the *runner*, not in the object: a
capability-blind baseline that compared against the recorded digest instead of
against the unmutated stateless replay (measuring statelessness, not
mutation-response); B6's generator capped at **25 cases against its own floor
of 30** — §4.0(3)'s unmeetable-floor defect appearing *inside the instrument*;
and every zero-flip verdict checking its numerator and never its denominator.
B10 read red again, as a reading should.

**Run 4** is a second supplementary run, after independent review of the merge
candidate, and it is where B8 got teeth. The registered arms turned out to be
**one tamper shape run twice** — rewrite a turn, with and without repairing
the chain — both of which leave the original MACs in place. The obvious
forgery, an adversary who holds the file and **re-signs every record under
their own ring**, had never been run; when the reviewer ran it the scorer
**crashed** out of `session_keys.derive`. *A control that dies on a case has
not passed that case.* Two arms added, both 20/20, both detected by a key the
tamperer does not hold:

| arm | cases | detected | by |
|---|---|---|---|
| rewrite a turn, chain unrepaired | 20 | 20 | keyed MAC |
| rewrite a turn, chain repaired | 20 | 20 | keyed MAC |
| **foreign-ring re-sign** (file internally perfect) | 20 | 20 | keyed MAC |
| **blanked MAC and `key_id`** (the laziest forgery) | 20 | 20 | keyed MAC |

The same review found the cycle's recurring catch a third time: **B2 reported
GREEN having reproduced 0 of 410 turns**, because its verdict counted per-turn
divergences and a `stale-environment` refusal produces none. *"Every turn the
seal records" means every turn, and zero is not every.*

### The scope limits, stated where the claim is made rather than beside it

- **B1's first clause MISSED and stays missed.** The replayer was committed at
  `9a9cb45` and the seal at `a91e39d` — four minutes later, and in the wrong
  order. B1 is not in R1 and not among the stop conditions, so the run does not
  void; the miss is published unreinterpreted through all four runs. What the
  order taken gives is the stronger half (a replayer cannot be fitted to
  journals that do not exist) and what it gives up is the mirror guard: **the
  corpus was authored after the replayer, by the same hand.**
- **B10's scope is the ledger's state, not the resolver ASK subloop's.** The
  subloop is pre-existing session state and sits outside B10's denominator. No
  recorded session exercises it. That is a real limit on what B10 proves, and
  it is written into the run's own `the_suspended_habit_ends_here` field
  rather than into a footnote.
- **B12's two sides descend from the same in-memory `ReadBarrier`.** The field
  said *independent* until review corrected it. What B12 corroborates is that
  the journal's per-turn citation snapshot agrees with the barrier's raw event
  log — not that two unrelated instruments agree.
- **B13's auditor is the implementer.** The prereg registered that before the
  draw. A seeded blind draw does not make a self-audit independent; it makes it
  unsteerable turn by turn, which is less. All twenty drawn cases are the same
  easy shape, and the run says so.
- **Sessions are reproducible, not correct.** A wrong answer replays as
  faithfully as a right one. Nothing in the run is evidence that any answer is
  true.

### The statelessness suspension ends here, by this gate's own verdict

`DESIGN-session-ledger` §12 suspended the stateless one-line-in-one-answer-out
rule for this cycle and said the suspension would end at the v0.21 gate by
that gate's own verdicts. It does: **state is a shipped property of the
harness session**, and B10 — 260 uncited turns rendering byte-identically to
stateless service — is the fence that makes either answer honest.

**No surface was invented.** `DESIGN-session-ledger` names no capability-sheet
row, no route and no status for slice 1, and none was added. The one grammar
row that did change is `retract <assumption-id>`, which the Assumption status
alphabet required — and on the chat skin it always refuses, because ¶DEV-1
replays every request into a fresh session.

## The third outcome: an instrument that refused to become one

**Before.** v0.20's conformance run served a `conform` route and **voided its
own controls**, so `NO_COUNTEREXAMPLE_FOUND` certifies nothing universally.
WITNESS was scheduled as the claim-kind successor: replace sampling with a
**discharged obligation** — per-statement, checker-signed lemmas asserting
that the compiled evaluator and the statement agree over a declared domain.

**Now.** The design landed, W0 and W1 ran, and **the slice stopped before it
opened**.

| stage | reading |
|---|---|
| **W0** — the fragment census | **37 candidates** of 12,777, all carrier `Nat`; the draft's 60-name manifest **withdrawn** under the design's own <70 rule |
| **W1** — the pilot | **0 of 6 obligations discharged**, every one `rejected_trivial` |
| **B4** — the self-comparison trap | **met**: the trap obligation returns `rejected_trivial`, rejected by the ordinary tree comparison rather than by a branch that recognises it |
| **the counterfactual** | the same six obligations handed to `omega` with the triviality test **switched off** were **accepted 6 of 6** |
| **the slice** | **STOPPED.** No manifest sealed, no floor frozen, no obligation builder run over the population, no mutant ledger, no capability claimed |

**The reason is structural, not incidental.** The drafted obligation
`∀ x ∈ D: eval(S)(x) ↔ S(x)` compares the conformance evaluator's grouping of
a statement with the statement as written — and **both sides descend from one
front-end's parse**. The committed parser emits left-nested **binary** `+` and
`*` nodes, so the evaluator's hoisting has nothing to hoist. Inside W0's
linear fragment the two readings are the same tree, and every obligation is
`P ↔ P`.

**The counterfactual is why the stop is worth reading.** An instrument without
B4's self-comparison clause would have published **six discharged agreement
lemmas and reported a capability.** The trap is the direct descendant of
v0.20's recurring catch — assertions written so they cannot go red — turned
into a gate clause, and the first thing it did was stop its own lane.

**The census chain, in prose, because four numbers appeared across two
documents and only the last is current** (`DESIGN-witnessed-conformance` §4's
dated amendment): **66** was the indicative walk, checking only the
conclusion. Holding **guards** to the same linearity standard is the single
largest drop — 21 statements, **66 → 45**. Then the predicate was executed
against the obligation builder and lost three more groups: 3 carrying a
literal that is not a `Nat` (**45 → 42**), 4 carrying a unary negation outside
a `+` node (**42 → 38**), and 1 whose guard names a slot the binder does not
bind (**38 → 37**). Every one was found by **running the builder**, never by
reading the predicate.

**Disposition: WITNESS PARKS**, behind a named **prerequisite** rather than a
trigger — *a second, independent reading of `S`* (a second front-end, or W2's
human transcription promoted from audit to input). Fragment growth alone does
not unpark it: the divergent class **exists and is reachable** — 25 statements
carry a binary `+` whose first operand is a `neg`, 18 of them compiling,
against **0 n-ary nodes in 86,547 walked** — but it is **non-linear**, so
reaching it would give the obligation content while leaving it a comparison of
one parse with itself.

**EXHIBIT stays declined, with the accurate second reason.** Its revival
condition reads *"it revives only if a non-void conformance instrument ships
first"*, and §2's fallback describes what happens *"if WITNESS voids."*
Neither occurred. The recorded second reason is the true one: the successor
**never became an instrument**, for a cause — single-front-end construction —
that EXHIBIT would inherit whole.

### The review that caught a clean receipt about the wrong statement

One Critical, and it is the kind worth reading twice: `witness_obligation.build`
rendered guard conjuncts without checking their slots were bound.
`lean_workbook_10679`'s guard reads `b < c` while the sampler binds only `a`
and `b`, so the obligation went out carrying a free `c` — **Lean's
`autoImplicit` prepended an implicit binder**, and `omega` returned exit 0 with
no diagnostic **on a strictly stronger proposition than the row it was filed
under**. Verified both ways: under `set_option autoImplicit false` the same
source errors with *unknown identifier `c`*.

Fixed as a **typed refusal** — a variable the sampler never bound is not one
this slice may quantify over on the statement's behalf — with
`autoImplicit false` in every probe's preamble. The cascade cost one census
candidate (38 → 37) and moved all six probe digests. **All six verdicts
unchanged.** *A checker receipt is only evidence about the term you think you
sent it.*

## The §4.0 rider paid out: the question v0.20's instrument gap withheld

ROADMAP-v0.21 §4.0(1) narrowed the no-chase rule to controls that **ran** and
read unfavourably, and carried the C-E3 supplementary run as a named early
rider under it. It ran.

**Before.** v0.20's C-E3 built its adjudication list out of each record's raw
`canonical_ascii` and never substituted the record's own
`counterexample.bindings`, so all 25 sampled propositions reached the checker
with **free variables** and every one failed at elaboration. That was an
**instrument gap**, and the carrier boundary was therefore not measured at
all.

**Now.** `experiments/conformance_ce3_supplement.json` — its own dated prereg
amendment, a **new** writer, a **new** artifact, and
`scripts/measure_conformance.py` **not edited**, because the dead
`_lean_expression` at `:434-438` is the evidence for the correction.

- **25 of 25 sampled counterexamples `confirmed_counterexample`** by the
  pinned checker (`leanprover/lean4:v4.32.2`, `by decide`, both directions,
  always both) on **closed** ground propositions — bindings substituted
  structurally at the parsed tree's `slot` nodes, not textually.
- **And all 25 hold over exact rationals.** One extra evaluation per row, added
  by review: every confirmed counterexample **still holds** when the same
  statement is read over exact rationals with signed subtraction. So these are
  products of the **declared domain** — truncating `/`, truncated-at-zero `-`
  over `Nat` — and not of the source statements.

**What the agreement therefore prices is arithmetic-implementation risk, not
domain risk.** Two independent implementations of the *same declared
arithmetic* compute the same values and the same failures. It prices nothing
about whether that declared arithmetic is the right reading of the Lean source
statement, the correlated-interpretation label is untouched, **and a reader
who takes 25/25 as evidence the corpus is wrong has read the artifact
backwards.**

**A clean sweep is exactly the shape §4's standing question interrogates**, so
the artifact answers it: the refuted path is demonstrably reachable —
`tests/test_conform_ce3_supplement.py::TheRenderingMeansToLeanWhatItMeansToTheEvaluator`
drives the same `decide_both_directions` over seven fixtures, four of which
come back `refuted_counterexample` on the same code path against the same
pinned binary. *That is the difference between an instrument that did not go
red and one that could not.*

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    a=json.load(open('experiments/conformance_ce3_supplement.json',encoding='utf-8'))['aggregate']; \
    print('adjudicated', a['adjudicated'], a['by_verdict']); \
    print('hold over exact rationals', a['rows_that_hold_over_exact_rationals'], 'of', a['of_confirmed_rows'])"
adjudicated 25 {'confirmed_counterexample': 25}
hold over exact rationals 25 of 25
```

### E5, run late and dated as late

§4.0(2) replaced execute-once ceremony with determinism-plus-commit and
permitted late determinism checks **with a dated disclosure of the lateness**.
`experiments/conformance_e5_late.json` is that disclosure.

**E5 HOLDS**: `scripts/measure_conformance.py` executed twice in two fresh
processes on the tree at `a98fa3c`, each writing outside the repository —
**byte-identical**, sha256 `f55ba4a9…`, zero differing fields by recursive
structural diff. C-E1's stability arm **rides the same evidence**: an
identical artifact is a superset of *0 of N unmutated statements changed
verdict*. And a third run at the registered limits reproduces the committed
`conformance_run.json` but for `commit` and its hand-added corrections block.

**What the lateness does not buy back, in the artifact's own words:** E5 was a
**stop condition** of the design, and *a stop condition checked after the
thing it could have stopped had already shipped is a check, not a gate.*

## Roadmap triage

Every item of [ROADMAP-v0.21](ROADMAP-v0.21.md), with its outcome.

### Shipped

| item | outcome |
|---|---|
| **§1.1 P1** — the finite bound | **SHIPPED, and it falsified its own premise.** `experiments/session_p1_command_bound.json`: 15 template classes, **5 closed (34,863 admitted commands), 1 gated, 9 admitting countably infinite languages** — including the two rows where plain prose lands. *"An enumerating proposer has a finite target only because the committed material is finite, never because the grammar is."* |
| **§1.1 P2** — separator expressibility | **SHIPPED, and it did NOT decide the question it was asked to.** 9 of 10 sealed ambiguous prompts admit a separating command (8 of 10 at the act level), so the clarifying-question arm has something to ask and the conditional-answer arm **did not win by measurement**. Published either way, as registered |
| **§1.1 P3** — the sealed corpus | **SHIPPED.** 60 sessions, 410 turns, 130 binding-dependent, A/B 35/25; 0 excluded by the no-write-gate rule; floor met with margin, **and the roadmap's compressed reading's numbers published beside it** |
| **§1.2 slice 1** — the journal | **SHIPPED and SERVED.** R1 HOLDS on run 4; B1–B8 and B10–B13 adjudicated; B9 scored NEVER |
| **§1.2 slice 2** — plain input | **SHIPPED AS A NEGATIVE.** Built, wired, run, and **R2 FAILS** on two clauses. Nothing is served |
| **§2 early rider** — the C-E3 supplementary run | **SHIPPED.** 25/25 confirmed, all 25 holding over exact rationals |
| **§2 ride-along** — E5 and C-E1's stability arm | **SHIPPED, dated late.** E5 HOLDS byte-identical |
| **§2** — WITNESS's compact design | **SHIPPED.** `docs/DESIGN-witnessed-conformance.md`, written and adversarially reviewed before the slice, on the ROADMAP-v0.19/v0.20 convention |

### Shipped as a negative — first-class results

| item | outcome |
|---|---|
| **§1's R2** | **FAILS.** G5 RED (22 vs 17 against ≤8.5) and G9 NOT MET. The seat ships empty, with the number |
| **§2 WITNESS's slice** | **STOPPED at the pilot**, 0 of 6, and **PARKED** behind a named construction prerequisite — an independent second reading of `S`. There is a reviewed design, two committed artifacts and a published reading, and **no instrument** |
| **§1.1 P2's own question** | Did not decide. Recorded as not-decided rather than resolved by preference |
| **§4's own §4.0(3)** | Its **second incident** is inside this cycle: G5's mis-derived chance rate. The rule cites itself |

### Carried

Every carried lane is either ordered before a named ROADMAP-v0.22 headline
item (in which case it is a **prerequisite**, not a lane) or **parked in
BACKLOG with its reason**. The v0.21 successor set is in
[ROADMAP-v0.22](ROADMAP-v0.22.md) §3; the parks are in
[BACKLOG](BACKLOG.md).

- **The resolver-binding repair** — carried as a **designed successor**, with
  its 13 committed fixtures, its three owed pieces (prereg, control, K
  re-measurement), and no headline dependant in v0.22. **Parked**, named.
- **The G5-metric successor** — carried with its rule stated: score the branch
  outcome against the question's registered disposition, not the raw
  verified-selection count, and freeze it with a meetability argument.
  **Parked**, named; ROADMAP-v0.22's rider R1 (ONE STEP) embodies the same
  correction on a different lane, which is where the lesson goes to work.
- **TWO WITNESSES + independent second reading** — **parked item-candidates,
  together**, because they are the same problem: the conformance successor
  cannot open without a second reading, and TWO WITNESSES' 160-obligation
  battery is what would price one. Demoted from rider to item-candidate by the
  v0.22 design review (H9): a WITNESS-slice-sized cost is not a rider.

## What changed, per area

### The object: a per-turn journal with keyed MACs and an out-of-band seal

**Before.** `experiments/harness_session.json` recorded a session at **leg**
granularity with no per-answer digest chain; `scripts/conversation.py` held
durable state with keyed MACs per binding; `experiments/throughput_tasks.json`
was the model for freezing a conversation-shaped denominator. None of them was
a per-turn journal of a served conversation with citations of the assumptions
each answer consumed.

**Now.** `scripts/session_ledger.py`, `scripts/session_recorder.py` and
`scripts/replay_session.py`, with the seal's digests kept **out of band** —
`experiments/session_corpus_seal.json` holds each journal's whole-file digest
and never puts it inside the journal it covers, *"because a digest that lives
inside the thing it covers is a digest an editor updates."*

**Demonstrate.** `experiments/sessions/v021-s03.json` turn 4 — input `n + t`,
`assumptions_cited: ["a001","a002"]`, `result.kind: solved` — and the
citations are read-derived, not asserted:

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/sessions/v021-s03.json',encoding='utf-8')); \
    [print(t['turn_index'], repr(t['input_bytes']), 'cites', t['assumptions_cited']) \
     for t in d['turns'] if t['assumptions_cited']]"
2 'n ^ 2' cites ['a001']
3 't ^ 2' cites ['a002']
4 'n + t' cites ['a001', 'a002']
```

**And what replay verifies is narrower than what the journal carries, stated
in the seal itself:** `replay_session.py` compares pins and re-serves lines. It
never derives a key and never calls `verify_turn_mac`, *"so a journal whose
every signature was forged would replay exactly as well as an authentic one."*
That is a division of labour, not a gap — replay asks whether the record
reproduces, the MAC ring asks who wrote it — and the seal says so rather than
letting a reader assume one covers the other.

### The proposer, wired dark and scored

**Before.** Row 12 of the line grammar exhausted on unrecognised prose.

**Now.** `scripts/candidate_enumerator.py` builds a finite candidate list from
committed material under `data/` **only**; `scripts/plain_proposer.py` asks the
pinned model for an **index**; `scripts/plain_router.py` routes row 12; and
`conditional` joins the frozen status alphabet outside `ANSWERING_STATUSES`.
The model is pinned by weight-blob digest and **refuses rather than
downloads** on absence or mismatch, verified before any question is asked.

**Demonstrate.** `experiments/plain_proposer_determinism.json` — P4, two
passes, byte-identical, at temperature 0 — with its honest limit attached in
the run artifact: *"byte-identity across two passes on one machine on one day
is not a proof of determinism. It is the strongest check this repository has
ever run on a model call, and it is reported as that and nothing more."*

**And the throughput scorer changed, which is disclosed rather than buried.**
G7b's zero is mechanical because `scripts/measure_throughput.py` gained
`FORFEITING_STATUSES` and a `useful_tokens_are_forfeited_by(status)` the gate
calls **directly** — *"the difference between checking the mechanism and
checking a copy of the mechanism."* Two properties of that change matter to
anyone who later re-measures:

- It is **scoped**, and the first draft was not. Applying the wide
  `NON_ANSWERING_STATUSES` wholesale zeroed
  `closure_reachability/story.golden_chicken.unreachable.0`, **a task whose
  `exhausted` IS its answer** — a certified bounded negative carrying its
  closure receipt. The suite caught it, which is the only reason that is a
  fixed bug rather than a silently deflated number. The narrowing is kept as a
  fixture.
- **A `None` status now forfeits too** — *"a turn whose status never arrived is
  not a turn that answered."* That is new behaviour on a scoring path, and it
  is stated here because **no throughput number was re-measured through it.**
  `K = 220×` remains v0.17's reading of v0.17's scorer; a future readout runs
  through a scorer that has moved, and this paragraph is where a reader
  learns that before comparing.

**And G8's holdout fence has a channel the runner never checked.** The clause
has three limbs — prompts, candidate lists, **and any served answer**. The
runner executed two and reported GREEN. The reviewer executed the third by
hand before ruling: 108 verified candidate lines re-served, **0 holdout ids, 0
divergent statuses**; the runner now carries the limb and reads **0** over its
own denominator of 120 lines (78 distinct). Both numbers are published, and
neither is the other's correction. The channel is real:
`PlainRouter._reserve` copies the **caller's** index, and a recorder's index
spans `data/` and `data_holdout/` — the same 2,053-id span slice 1's M9
finding measured. `_reserve` is **not** patched, because narrowing it after
the run would change served behaviour the run measured. Filed.

### One debt paid, one debt filed, and the reason they differ

Slice 2's wiring commit added `_route_proposed` to `scripts/harness.py`, which
is in `build_throughput_tasks.RENDERING_MODULES`. Two committed artifacts pin a
digest over that file and both went stale.

**Paid.** `experiments/throughput_tasks.json` was rebuilt through its own
writer — never hand-edited — and **exactly one line moved**: the harness
witness, `09eda754…` → `9dc6e660…`. No task, no count, no A/B assignment, no
profile. *A sealed denominator is not moved by refreshing a witness of the tree
it witnesses, and the one-line diff is the evidence for that sentence rather
than the assurance of it.*

**Across the whole cycle the book moved two lines, not one**, and the earlier
one is worth naming because it was the same defect caught earlier: the
session-ledger slice edited `harness.py` and `evaluate.py`, both witnessed, and
rebuilt neither — *"the seal witness was witnessing a tree that no longer
existed."* Review found it as five red tests. **Two consumers of one
derivation, one of them updated**: the journals' pin table reads
`rendering_module_digests` from the builder directly and had moved correctly;
the book's copy had not, because nothing in the ledger's lane reads the book.
Against `v0.20.0` the net diff is **two digest leaves** — `scripts/evaluate.py`
and `scripts/harness.py` — with `built_by`, `counts`, `schema`,
`scoring_rules`, `seal` and **all 119 task records byte-identical**.

**Filed, with its measurement.** The sixty slice-1 journals pin the same digest
inside `rendering_module_digests`, so **every slice-1 replay now refuses
`stale-environment` at HEAD**. That is B3's mechanism working, and it is not
repairable here: re-recording would rewrite sixty committed journals and slice
1's **closed** seal, leaving the published `session_ledger_run4.json` pointing
at a corpus that no longer exists. *A record that cannot be checked against
the thing it measured is worse than a corpus that needs a re-recording.* The
successor pattern is named in BACKLOG — re-record at a fixed tree into a
**new** seal, prior seal retained byte for byte, B2 and B3 re-scored.

**Demonstrate — the refusal, which is the honest state of a fresh clone:**

```
$ PYTHONIOENCODING=utf-8 python scripts/replay_session.py experiments/sessions/v021-s03.json
REFUSED: stale-environment — rendering_module_digests, capability_sheet_digest;
nothing was replayed and nothing is claimed
```

**And the sixth registered pin finally works.** `DESIGN-session-ledger` §3
listed `proposer_model_digest` as *"slice 2 only, key omitted until then."*
Before this cycle, a journal that carried it would have been refused on every
replay — `compare_pins` treats an unknown recorded pin as a mismatch,
deliberately, *"so the pin table's own growth is not invisible to B3."* A
journal made unreplayable by obeying its own design. `OPTIONAL_PIN_FIELDS` now
registers it, and the constant lives in the **replayer** rather than the
ledger for a measured reason: the recording protocol pins
`recorder_code_digest` over `session_ledger.py` and `session_recorder.py`, and
the suite went red inside two minutes when the constant was put there. *A
comment would have been an argument; the pin was a test.*

### Five adversarial reviews, and what each one cost

| lane | verdict | what it found |
|---|---|---|
| **WITNESS delta review** | 1 Critical, 2 Highs | A **clean checker receipt about the wrong proposition** — an unbound guard slot that `autoImplicit` silently bound, so `omega` returned exit 0 on a strictly stronger statement. Also: the published mechanism for the stop was **false in the direction that flattered it** (the divergent class was called unreachable; it is reachable and non-linear) |
| **C-E3 rider review** | GO, five fixes | An assertion that **could not go red inside a suite added to catch exactly that** — `assertIn("byte-frozen", field.lower() + " byte-frozen")` appended its own needle to the haystack. Plus the per-row honest non-claim the design required and the rows lacked, and the exact-rational computation that says which risk 25/25 actually priced |
| **session-ledger merge review** | 1 Critical, 3 Highs, 2 Mediums | A twin count wrong by **ten thousand** with every test around it green (12,589 → 2,537 ids; closed total 44,915 → 34,863); a sweep whose published sentence — *"exactly two routes may read the ledger"* — was **false**, because it walked only functions whose own name began with `_route` and only `getattr`; **B8 crashing on the obvious forgery**; **B2 green on zero turns**; and a floor reading that was right for a **retracted** reason |
| **plain-input slice-2 review** | 3 defects + the tidy pass | **G8 reported GREEN on two limbs of three**; the enumerator's title-length tiebreak capping G1's ceiling invisibly; a reply parser looser than its own doctrine; and, in the tidy pass, a **miscounted note inside the miscount catalogue** |
| **v0.22 design review** | **falsified the design twice** | See below |

**The recurring find, for the second consecutive cycle: assertions that cannot
go red.** v0.20's catalogue was G5b's dict-literal evidence, a file compared to
itself, a freeze list whose prose outran its machine check, and a test
asserting *"the repository as it stands is dark."* This cycle continued it with
a **needle appended to its own haystack**, a **B2 verdict that counted
divergences and so read green on zero reproductions**, and **B8 arms that were
one shape run twice**. Zero wrong digests were found in any of the five
reviews. The defects were all in what a green check was capable of failing.

**And the discipline applied upward.** The orchestrator's own v0.22 design was
**falsified twice by review before it landed**: its first version claimed no
non-title index existed, in a tree that holds two (`resolver.by_lexicon` over
the per-node `symbol_lexicon`, and `resolver.inventory`), and cited producers
that do not exist (S4 notation records, S5 defeq alias buckets — deleted; S3
demoted to a priced question). The receipt records it in its own selection
note. A review gate that binds the measurements and not the person planning
them is a review gate with a hole in it.

## Discoveries of the cycle

Quoted from [DISCOVERIES](DISCOVERIES.md); linked rather than duplicated:

- *"A metric that counts successes cannot see a correct refusal."* G5's blind
  arm beat the proposer 22 to 17 because six correct `NONE` answers scored
  zero and the blind arm, which cannot decline, took the candidates they
  declined — and the floor itself was unmeetable, at `1/8` frozen against
  `0.687` measured.
- *"An obligation built from one reading compares that reading with itself."*
  WITNESS's 0 of 6, with the counterfactual — 6 of 6 accepted with the trap
  removed — as the evidence for what the trap bought, and the independent
  second reading promoted from residual risk to construction prerequisite.
- *"A conversation can carry its own premises, and the fence is what proves
  it."* 58 of 58 cited-mutation responses, against **0 flips of 42** uncited
  and **0 of 60** sham. One flip would have voided the capability.
- *"A control that dies on a case has not passed that case."* B8's registered
  arms were one tamper shape run twice; the obvious forgery crashed the
  scorer. Filed with the cycle's other two incapable-of-failing checks — the
  needle appended to its own haystack, and B2 green on zero reproductions.

## Resolved from BACKLOG

- **The C-E3 substitution gap — CLOSED**, under §4.0(1) and exactly as the
  entry itself specified it must be: its own dated registration, a new writer,
  a new artifact, and `measure_conformance.py` unedited. 25 of 25 confirmed.
- **E5 and C-E1's stability arm — CLOSED, run late and dated late.** The
  entry's sentence *"`conformance_run.json` therefore has no byte-reproduction
  proof"* is **superseded** and was replaced rather than left standing.
- **4d's half-produced served diff — CLOSED.** The regenerated artifact reads
  `armed: true` on both sides; the entry's outstanding half was discharged at
  the v0.20 rotation and the entry is pruned here.
- **P2's silent-binding entry — SUPERSEDED, not deleted**, by the thirteen-
  fixture entry that replaces it. The superseded record stays, because a
  removed one teaches nothing about how the estimate moved (2 of 10 → 13 of
  30).
- **Newly filed**: the resolver-binding successor with its 13 fixtures; G5's
  metric defect with the successor's rule; `PlainRouter._reserve`'s
  holdout-spanning index; the enumerator's title-length tiebreak; the
  branch rule that never consults `NONE`; the synonym layer as the standing
  blocker; the discarded-correct-selection receipt shape; slice-2's staling of
  slice-1's sealed journals; WITNESS's second-front-end prerequisite; W0's
  missing runnability clause; a deterministic runner that does not record its
  own invocation; and the v0.22 course's parks with their probes.

## Honest limits carried forward

- **The resolver's silent binding is NOT repaired.** 13 of 30 sealed questions
  bind at `found` before the proposer is consulted. Any sentence quoting P2's
  defect beside slice 2 must say the defect is unrepaired.
- **Nothing from slice 2 is served.** `conditional` exists in the alphabet and
  scores zero useful tokens; the proposer is attached to no session the chat
  skin serves.
- **G5's floor was unmeetable and the red stands anyway.** Both facts are
  published; neither cancels the other, and the rule was not rewritten after
  the instrument surprised its author.
- **Slice 1's sealed journals no longer replay against this tree.** Every
  slice-1 replay refuses `stale-environment` at HEAD. Slice 1's published R1 is
  a claim about the tree it was recorded against (`b388e6b`).
- **B1's first clause missed**, and the corpus was authored after the replayer
  by the same hand.
- **B12's corroboration is not two independent instruments.** Both sides
  descend from the same in-memory `ReadBarrier`.
- **B13's auditor is the implementer**, and all twenty drawn cases are the same
  easy shape.
- **Sessions are reproducible, not correct.**
- **No stranger-usability claim, anywhere.** Q30's plain questions and P3's
  sessions are maintainer-authored, about a corpus the author knows. STRANGER's
  park is cited, not re-encountered.
- **WITNESS has no instrument**, and the conformance void is unchanged.
  `NO_COUNTEREXAMPLE_FOUND` still certifies nothing universally and **no
  conformance rate exists anywhere.**
- **C-E3's 25/25 prices arithmetic-implementation risk, not domain risk.** The
  correlated-interpretation label stands on every NONCONFORMANT verdict, and
  the sweep says nothing about the other 750 counterexamples.
- **E5 was a stop condition checked after the thing it could have stopped had
  shipped.** That makes it a check, not a gate.
- **The reader claims are still not made — neither of them.** C-V3′ (machine)
  VOID at v0.20; C-V3 (human) ABSENT for a third cycle.
- **`K = 220×` is v0.17's number and stays v0.17's.** No throughput readout ran
  this cycle. Against `v0.20.0`, `experiments/throughput_tasks.json` moved
  **exactly two lines**, both digest leaves inside `rendering_module_digests`
  (`scripts/evaluate.py` and `scripts/harness.py`); `built_by`, `counts`,
  `schema`, `scoring_rules`, `seal` and **all 119 task records** are
  byte-identical, and no `throughput_result*.json`, `throughput_trial_*.json`
  or `throughput_baseline.json` changed at all. Those are seal rebuilds, not
  measurements. **But the scorer itself moved** — `measure_throughput.py`
  gained a rule-level forfeit for `conditional` and for a missing status — and
  **nothing was re-measured through it**, so the next readout is not a
  like-for-like comparison with v0.17's and must say so.
- A passing Python test is not a Lean proof.

## Drift audit

*(RELEASE-v0.19.0, RELEASE-v0.20.0, ROADMAP-v0.19 and ROADMAP-v0.20 re-read in
full, per the rule.)*

**This rotation's audit found a product surface that advertises a behaviour it
does not have.** That is the shape the rule's own paragraph exists to catch,
and it is the first time it has caught one on a *live* route rather than on an
absent one.

### The product-surface finding: the sheet says "the asker's own numbers", and the route discards them

RELEASE-v0.20.0 named the gap in its own honest limits: *"The bindings are
parsed today only to report ignored names — `run(program, schema.digest)` never
receives them… **The route tests the sampler's points, not the asker's
numbers.**"* It was named and then **filed nowhere** — not in BACKLOG, not in
ROADMAP-v0.21. A named honest limit with no owner is exactly the drift shape
the v0.20 audit itself caught for *load-bearing / premise-necessity*.

And the **capability sheet says the opposite**.
`scripts/serve_chat.py:635-637` publishes the `conformance` row's description
as:

> *"a committed statement compiled to an exact evaluator over the **asker's
> own numbers**, answering with a conformance record"*

while `scripts/harness.py:2192` parses the bindings and `:2229` calls
`run(program, schema.digest)` **without them**. ROADMAP-v0.20 §1's own summary
of what shipped says the same thing the sheet says: *"`conform
<statement-id> <bindings>` on both skins."*

**And the sheet's published worked example does not work.**
`scripts/serve_chat.py:332` advertises
`conform algebra.polynomial_equations.quadratic_formula a=1 b=-3 c=2`. Typed
today:

```
$ echo "conform algebra.polynomial_equations.quadratic_formula a=1 b=-3 c=2" \
    | PYTHONIOENCODING=utf-8 python scripts/harness.py
route   : conform
status  : refused
detail  : does_not_parse: nothing was computed, and the named construct says why.
          A refusal is not a negative result about the statement
```

A published example **is** a product surface. An attaching orchestrator reads
the capability sheet once and configures itself from it — that is the sheet's
whole stated purpose — so a row that names a behaviour the route does not have,
beside an example that refuses, is a wrong answer given to a machine.

**And `_route_conform`'s docstring still describes a stub** — *"registered, and
refusing for now… What it will do when `scripts/conform.py` lands is NOT
sketched here"* — in a tree where `conform.py` landed and the route is live.

**And the README carried the same sentence** — *"statements that compile into
something you can run against your own numbers"* — which is **corrected in
place at this rotation**, because a README is the first surface a newcomer
reads and it is the one document here that may be repaired without destroying
anyone's evidence.

**Recovered here rather than left absent**: filed in [BACKLOG](BACKLOG.md) with
its three parts (the sheet's description, the broken example, the stale
docstring) and named in [ROADMAP-v0.22](ROADMAP-v0.22.md) §4.3 with its trigger.
**Nothing is patched in this rotation**, because narrowing or widening a served
route at a rotation is a behaviour change owing its own evidence — but the
sentence *"the route tests the sampler's points, not the asker's numbers"* now
has an owner.

### Two gate obligations v0.20 shipped undischarged, and this rotation inherits the shape

1. **`check_report_regeneration.py` never ran for v0.20.** ROADMAP-v0.20's
   release gate required it — *"runs in the release refresh with its verdicts
   in the notes"* — and RELEASE-v0.20.0 said, honestly, *"has not run in this
   rotation… its three verdicts land in this section then."* **They never
   landed.** The section still reads "not yet". So the same clause is open
   again, and this release does not get to write it as though the precedent
   were clean: it is the **second** consecutive rotation to publish the gate
   step as pending.
2. **`[SUITE-GATE-V20]` was never resolved.** The token appears exactly twice
   in the whole tree — once in RELEASE-v0.20.0 and once in ROADMAP-v0.20's
   closed banner — and it is a cross-reference to a section that was never
   written. ROADMAP-v0.20's banner therefore **still declares three gate
   clauses open** (refresh, full-suite, ships-or-parks) even though
   RELEASE-v0.20.0 does report two suite runs with their wall-clocks. The
   banner and the notes were never reconciled. **Named here, not edited** —
   a closed roadmap is the historical plan-of-record — and `[SUITE-GATE-V21]`
   in this document is written knowing that a placeholder is a promise
   somebody has to come back for.

### A contradiction between v0.20's two records, unresolved until now

ROADMAP-v0.20's closed banner says 4d's then-present served diff **"was never
produced"**. RELEASE-v0.20.0's drift audit says it was **"discharged at this
rotation"**, and the committed artifact agrees: `sides.before.armed` and
`sides.after.armed` both read `true`, `answer_lines_moved` reads **0** of
**14,830**. The banner is wrong and the notes are right. Recorded rather than
silently corrected in a closed document.

### The rider stop rule comes due, and it fires

ROADMAP-v0.21 §3.5 set it: *"If either is still unrun at the v0.22 rotation, it
stops being a rider and either becomes an item or parks."* Both the **HOLES
counting table** and the **delete-K ground-truth table** are still unrun, for a
**third** consecutive cycle — no artifact exists for either. **The rule fires:
both park**, in ROADMAP-v0.22 §4.3, with their reasons, and neither is listed
as an available rider again.

**Four more standalone probes have now been named for two or three cycles with
zero runs** — VERDICT's week-one warrant census, DEBT NOTES' one-day
hand-classification probe, COURIER's one-day detached-receipt probe, and WORD
OF HONOR's extraction-discipline census (*"an optional rider any cycle can
run"*, named since v0.19). They stay on the list, and the count is written down
so the next rotation can apply the same stop rule to them rather than
rediscover it.

### Two lanes drifted inside rows that said "unchanged" — the same shape as last cycle's four

The v0.20 audit caught the ledger-first trigger's **article** (*the* → *a*). It
did not catch the rest of the edits in the same rows.

1. **Ledger-first claims lost three more things beside the article.** Its named
   dependant went from *"none this cycle"* to *"none"* (the scoping qualifier
   dropped); its verb went from *"It **became** a headline candidate"* — a
   past, fired event — to *"it **becomes** a headline candidate"*, a standing
   conditional, which reinforces exactly the reading the article change made;
   and the receipt path `reports/design-direction-v0.17.json` was compressed to
   *"receipt"*. The article was restored at v0.21. **The tense and the
   dependant qualifier are restored in ROADMAP-v0.22 §4.3**, and the count is
   stated once: this is the **sixth** consecutive pass-over under the original
   wording, and v0.21 produced **no new throughput readout** either.
2. **Licensed variant generation lost the qualifier that made its trigger
   checkable.** ROADMAP-v0.19 wrote *"what licenses a second passing surface
   **for the same term**"*; v0.20 and v0.21 both quote the shortened form. And
   its evidence sentence — *"A ranker is not blocked by the admission bar — it
   is blocked by the absence of anything to rank"* — is absent from both.
   **Both restored in ROADMAP-v0.22 §4.3**, with one honest correction beside
   them: v0.20 recorded `DESIGN-plain-input` as a *candidate* dependant,
   because a plain utterance was argued to license several candidate queries.
   **It did not materialise** — v0.21's proposer emits an **index into an
   enumerated list**, not a ranking over surfaces — so the candidate is
   recorded as not-strengthened rather than carried as if it had been.

### Open-English input lost its worked example and its fired trigger, at the same rotation the audit was catching that exact shape elsewhere

ROADMAP-v0.19's row read: *"can the committed realization lexicon run backwards
as the synonym layer `DESIGN-text-resolution` §4 names (**`gcd` vs "greatest
common divisor"**) — a design, not a patch, **and R1 firing is what made it
askable**."* ROADMAP-v0.20 deleted both parenthetical facts — the worked example
and the fired-trigger clause — in a row otherwise unchanged, and v0.21 restored
the framing without restoring either.

**That the same rotation caught the identical deletion for *realization
parameters as data* and missed it here is the finding**, not the deletion. Both
restored in ROADMAP-v0.22 §4.3 — and the example is no longer hypothetical:
v0.21 **measured** it. *"How do you compute the greatest common divisor
recursively"* enumerated **zero candidates**, and the run's own words are *"you
cannot select what was never enumerated."*

### One recovery from last rotation was undone by the vehicle it was undoing

ROADMAP-v0.21 recovered *realization parameters as data* into its own row with
the trigger sentence quoted — **and left it inside the catch-all row as well**,
the same catch-all whose *"unchanged"* was the thing the recovery was fixing.
A lane in two places with two dispositions is a lane whose disposition is
unreadable. It appears exactly **once** in ROADMAP-v0.22 §4.3.

### A property named for future unpark, dropped into a catch-all

RELEASE-v0.19.0 named it deliberately: *"**What survives for any future
unpark**, named so it is not lost: the design's **append-only,
path-independent growth** property, which **no baseline in this probe
tested**."* ROADMAP-v0.20 §5 kept it in the row. **ROADMAP-v0.21 folded
DESIGN-block-vocabulary into a catch-all and the property is no longer quoted
anywhere in the carried record.** That is precisely the pattern
RELEASE-v0.20.0 condemned one page earlier. **Recovered**: quoted again in
ROADMAP-v0.22 §4.3.

### `mathlib_head` sits in the parked table wearing the word "carried"

ROADMAP-v0.21 §3.3 is titled *"Parked, with triggers"* and the
`mathlib_head` row inside it reads *"Carried unchanged"* — with **no named
dependant**, for the third rotation running. That is the shape the carried-lane
rule exists to catch, and the rule was applied to *licensed variant generation*
in the same table and not to this one. **Resolved by parking it explicitly** in
ROADMAP-v0.22 §4.3, with the verification that costs nothing: `data/` did not
move at all this cycle, so `blocked_total` 1,878 and `mathlib_head` 1,706 are
byte-identical to v0.20 and the two buckets never merged.

### The one prohibition-shaped trigger is still asserted rather than shown

HOSTILE DICTATION carries the only prohibition in the parked table: *"it MUST
run before any untrusted stream reaches the write gate."* ROADMAP-v0.21 judged
that §1's proposer *"takes plain text from the maintainer on loopback and opens
no such stream."* **v0.21 then shipped that proposer**, and the judgement still
carries no measurement or test behind it. The judgement is almost certainly
right — the proposer's entire output alphabet is an index into a
locally-enumerated list, which is a stronger fence than any stream audit — but
*almost certainly right* is what every green-check-that-could-not-go-red looked
like before somebody checked. ROADMAP-v0.22 §4.3 keeps the park and records
that the next lane to touch this trigger owes a **shown** answer rather than a
stated one.

### Stale citations in the previous two documents, named and not edited

- **RELEASE-v0.20.0** cites `serve_chat.py:515-537` for the `"claims": null`
  emission. That line is now **581**; 510–545 is the `foreign_voice_row`
  docstring. The claim is true; the line numbers are not.
- **RELEASE-v0.20.0**'s 4d transition command reads
  `--before 8e1a3d1`, while the committed artifact's own `regenerate_with`
  field reads `--before main`. Both run; the two records disagree about the
  canonical invocation.
- **ROADMAP-v0.20**'s pre-fix code citations — `match_signatures.py:412` for
  the float literal, `evaluate.py:182` for the unbounded power — both now land
  on different code, because the fixes moved the files. Historical by nature;
  a reader following them lands wrong.

None of the three is edited: a closed roadmap and a shipped release are the
record of what was written, and correcting a line number inside them would make
this audit's own evidence unreproducible.

### One surface shipping this cycle that will never serve on one skin, named at the moment it ships

`retract <assumption-id>` is now a normative row in
`docs/SPEC-chat-completions-skin.md`. **On the chat skin it always refuses**,
because ¶DEV-1 replays every request into a fresh session with no assumption
set attached. That is correct behaviour and it is written into the spec — but a
published surface that never serves is exactly the kind of fact that becomes a
drift finding three rotations later if nobody says it out loud on the day it
ships. Said.

### The standing lanes, verified rather than restated

- **The cost ledger — SIXTH cycle parked, and the streak's own record is not
  monotone.** ROADMAP-v0.19 wrote *"third cycle"*; RELEASE-v0.19.0 wrote
  *"fourth recorded pass-over"* for the same rotation; **ROADMAP-v0.20
  contradicts itself inside one document** — §5's row says *"fourth cycle…
  true for four rotations"* while §1.1 says *"a fifth rotation"* —
  and RELEASE-v0.20.0 says *"FIFTH"*. RELEASE-v0.20.0 also wrote *"the
  sentence is the same one"* while quoting **three different sentences**
  (v0.18's *"a metrology **this cycle** has not designed"* against v0.19's and
  v0.20's *"a metrology **no cycle** has designed"*). ROADMAP-v0.22 §4.3 states
  **six**, counting rotations since `DESIGN-grounded-throughput` §10 named it,
  and says which reading it is counting. **And for the first time the lane has
  a named successor**: TOLL, parked as a v0.23 incumbent-candidate, is the
  metrology six rotations of the same sentence have been waiting for. The lane
  is still parked; what changed is that the sentence is no longer *"a metrology
  no cycle has designed."*
- **Ledger-first claims — sixth pass-over, trigger not met.** v0.21 produced no
  new throughput readout: against `v0.20.0`,
  `experiments/throughput_tasks.json` moved **exactly two lines**, both digest
  leaves inside `rendering_module_digests`, with all 119 task records, the
  counts, the scoring rules and the seal byte-identical — and no
  `throughput_result*.json`, `throughput_trial_*.json` or
  `throughput_baseline.json` changed at all.
- **Load-bearing / premise-necessity — the v0.20 recovery held.** Named in
  ROADMAP-v0.21 §3.3 and again in ROADMAP-v0.22 §4.3, travelling with
  ledger-first.
- **The register's `mathlib_head` budget — intact.** `data/` did not move.
- **No other product-surface attrition.** Both skins carry every route the
  previous two roadmaps' acceptances named: `foreign_voice_row` reads
  `served: true`, the foreign `in words` line reproduces RELEASE-v0.20.0's
  block byte-for-byte, `evaluate`'s bounded-power refusal is live, and
  `tool.conform` registers. The `conform` finding above is about what a live
  route **claims**, not about a route that went missing.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.**

`git diff --name-only v0.20.0..HEAD -- data/ experiments/` lists **161 paths
and not one `.py`**, and `data/` did not move at all this cycle — every path is
under `experiments/`, and every one is a `.json` artifact, a recorded journal
under `experiments/sessions/`, or `ANALYSIS.md`. No training data changed and
no `experiments/*.py` changed, so **the checkpoints attached to
[v0.6.0](RELEASE-v0.6.0.md) remain accurate for this release** and
re-uploading identical bytes under a new tag would cost upload time to say
nothing new.

Every measurement ledger is committed in-repo at `experiments/*.json` and
linked by path above rather than duplicated as an asset. Licensed external
data (`experiments/data_real/`) is never attached.

## The next direction, chosen before this document

The outside design inquiry was **invoked strictly for the fourth consecutive
cycle**. `reports/design-direction-v0.22.json` records three isolated series,
three rounds each — **nine rounds, fifteen round-one directions, $2.80** — run
headless from an empty non-git directory outside the repository under a strict
tool denylist, with session ids and per-round prompt hashes committed and the
isolation mode inherited unchanged from the v0.21 receipt. The brief is on file
and hash-verified (`reports/design-direction-v0.22-brief.txt`), with the same
self-check kept: `series_1.r1` **equals** the brief hash by construction,
because round one of series one *is* the brief.

**Selected: [`docs/DESIGN-handles.md`](DESIGN-handles.md)** — reachability as a
property of what a statement *says* and how mathematicians name its parts,
rather than of the string somebody typed above it.

**And the design was falsified twice by its own review before it landed**,
which is the paragraph worth keeping. Its first version claimed the tree had no
non-title index. Review measured that false: `resolver.by_lexicon`
(`scripts/resolver.py:264-277`) and `resolver.inventory` (`:284-288`) both
exist over all 12,777 statements, and `resolve('greatest common divisor')` —
the *phrase* — reaches `programming.euclid.{iterative,recursive}` **today**.
The real defect turned out to be narrower and worse: the v0.21 candidate
enumerator builds its haystack from `title` + `keywords` **only**
(`scripts/candidate_enumerator.py:166-168`), so the proposer path was wired to
the weakest index on the tree while the stronger ones sat unused **one route
earlier on the same serving path**. Reachability is not missing; it is
unmeasured, un-gated, and unwired where the intake ambition needs it.

Then review falsified the rebuild too — sources without committed producers
were deleted (S4 notation records, S5 defeq alias buckets), S3 was demoted to a
priced question, and the coverage claim was cut down to what a census will
find.

**Which is why the honest expected headline of v0.22's item 1 is the census
itself.** With K = 128, the review's indicative measurement puts statements
holding at least one *specific* handle at roughly **263 via S-LEX and 306 via
S-INV — the same curated ~2%** — because 12,514 `lean_workbook` nodes share
three boilerplate name pairs that K excludes as overbroad. `DESIGN-handles`
§9's **H-P0 stop clause** makes that a first-class result rather than a
failure: if the census reads near ~2%, the slice publishes the census as its
headline — *the ingested library is effectively nameless; the naming layer must
be built, not indexed* — and the capability sentence does not ship.

**Adopted second: COLD RECEIPT** → [ROADMAP-v0.22](ROADMAP-v0.22.md) §2, with
one clause added before registration (its own residual risk, priced) and its
compact design landing before its slice, on the WITNESS precedent.
**CANARY-CURVE and TOLL** park as named **v0.23 incumbent-candidates**, and the
ordering is CANARY-CURVE's own residual risk answered: its shadow tier prices
statement *count*, not the density dimensions that bite, so growth is measured
**after** the enumeration layer exists. **TOLL is the five-cycle-parked cost
lane returning with a metrology** — the first named unpark candidate that lane
has had in six rotations.

## The release refresh

`[SUITE-GATE-V21]` covers the full-suite verdict; the generated-state chain is
reported here.

- `validate_nodes.py` — **12,777 statement nodes across 27 corpora**, green
- `check_regeneration.py` — **25 seeds regenerate committed data
  byte-identically** across `data/` and `data_holdout/`, exit 0. Reported
  independently by B11 inside the registered run, which also verifies the
  journals left `data/` untouched and every seal digest revalidates
- `signature_matches`, `specializations` and `compression` — regenerated with
  the release refresh at `[SUITE-GATE-V21]`
- `ingest_wold.py reach` — **not run in this rotation.** It refuses without the
  gitignored pinned WordNet archive, and that refusal is *cannot verify*, not
  *skipped*. It runs with the full-suite gate on the frozen tip and its verdict
  lands here then. No reach number is claimed in this document.
- `check_report_regeneration.py` — **has not run in this rotation**, and the
  release gate requires its verdicts in these notes. It runs on the frozen tip
  with the full-suite gate, with `decompositions.json`'s **declared** divergence
  carrying its TRIAGE-v0.11 citation, as in the last four cycles.

Saying "not yet" is the point: a refresh step reported without its exit status
is a step nobody checked.

## The suite at the tip

`[SUITE-GATE-V21]` — the full `unittest discover -s tests` run on a frozen tip,
with retained receipts in `reports/test_gate_v021/`, lands here with its
wall-clock, its failure count and its skip list. **The tag waits on it.** The
v0.20 baseline is 2,326 tests, OK (skipped=5), 21,828.9 s (6 h 04 m).

This cycle adds five wholly new test modules — `test_conform_ce3_supplement`,
`test_plain_input`, `test_session_ledger`, `test_session_prereqs`,
`test_witness` — and grows several existing ones. Per-slice suites were green
at each landing; **a targeted suite proves the surfaces you listed, and the
full gate proves the ones you forgot**, which is v0.20's own lesson and the
reason this section is a placeholder rather than a number.

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/check_report_regeneration.py

# On Windows every command below needs PYTHONIOENCODING=utf-8: these scripts
# print glyphs cp1252 cannot encode, and the UnicodeEncodeError reads like a
# refusal and is not one.

# 1. the session, typed: a supposition that persists, and the answer that cites it
printf 'suppose n = 4\nsuppose t = 5\nn + t\n' | PYTHONIOENCODING=utf-8 python scripts/harness.py

# 2. an unknown id refuses by name -- the line B10 went red on, twice
printf 'suppose x = 1\nretract a999\n' | PYTHONIOENCODING=utf-8 python scripts/harness.py

# 3. replay a committed journal offline: identical bytes, or a typed refusal
PYTHONIOENCODING=utf-8 python scripts/replay_session.py experiments/sessions/v021-p08.json
#    -> 9 of 9 reproduced, no divergences
PYTHONIOENCODING=utf-8 python scripts/replay_session.py experiments/sessions/v021-s03.json
#    -> REFUSED: stale-environment. Slice 2's wiring moved a pinned module
#       digest; that is B3 working, and it is filed in BACKLOG rather than
#       repaired by rewriting a closed seal.

# 4. the session gate's own verdict, read off the registered artifact
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('experiments/session_ledger_run4.json',encoding='utf-8')); \
    print(d['result_gate']['verdict'], '--', d['result_gate']['served_claim_if_it_holds'])"

# 5. plain input's red, and the mechanism beside it
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('experiments/plain_input_run.json',encoding='utf-8')); \
    print(d['result_gate_R2']['verdict'], d['result_gate_R2']['failed_clauses']); \
    g=d['gates']['G5']; print('G5', g['verdict'], g['blind_verified_selections'], 'vs', g['proposer_verified_selections'], \
    'required <=', g['half_of_the_proposer']); \
    a=g['analysis']['the_draw_was_typical_not_lucky']; print('blind expectation', a['expected_blind_verified_selections'])"

# 6. WITNESS's stop, and the counterfactual that makes B4 concrete
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('experiments/witness_pilot.json',encoding='utf-8')); \
    print(d['reading']['discharged'], 'of', d['reading']['drawn'], '--', d['reading']['rejected_trivial'], 'rejected_trivial'); \
    c=d['the_counterfactual_that_makes_B4_concrete']; \
    print('with the trap removed the checker accepted', c['obligations_the_checker_accepted'], 'of', c['of'])"

# 7. the C-E3 rider, and what its clean sweep actually prices
PYTHONIOENCODING=utf-8 python -c "import json; a=json.load(open('experiments/conformance_ce3_supplement.json',encoding='utf-8'))['aggregate']; \
    print(a['adjudicated'], a['by_verdict']); \
    print('hold over exact rationals:', a['rows_that_hold_over_exact_rationals'], 'of', a['of_confirmed_rows'])"

# 8. the conform route still serves its own void, unchanged by any of this
echo "conform leanworkbook.skel.lean_workbook_10012" | PYTHONIOENCODING=utf-8 python scripts/harness.py
```

Reproducing the plain-input run additionally requires the pinned local model
(`ollama:qwen3:4b-instruct`, weights blob sha256 `85e4a5b7…`); it **refuses**
— never downloads — when the weights are absent or their digest mismatches, and
publishes no partial rate. Reproducing the C-E3 supplement, the WITNESS pilot
and E5 requires the pinned Lean toolchain (`leanprover/lean4:v4.32.2`), invoked
by absolute path with no elan proxy, no lake, no Mathlib and no network.

**One command in [RELEASE-v0.20.0](RELEASE-v0.20.0.md)'s reproduce block now
has a caveat, and this is the notice.** Its foreign-voice and conformance
commands still run unchanged and their artifacts are untouched. But
`conformance_run.json` remains **VOID** and this cycle's C-E3 supplement does
not un-void it — the two artifacts are never blended, and the supplement's
25/25 is never quoted as a conformance number.
