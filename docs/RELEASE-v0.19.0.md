# v0.19.0 — three readouts, and every one of them made the claim smaller

This is the cycle where the instruments earned their keep by taking things
away. A control this project built specifically to bound its own headline
**voided that headline**, so the feature it certified is not served. A
probe adopted from the maintainer's own design **lost to its blind
baseline on both legs** and parked with the numbers. A census went looking
for competing mathematical conventions and **found none**, which retires
the direction that wanted them.

And in between, the one thing that got bigger: **two glyph equivalences
took the native voice from 17.0% of the corpus to 67.2%.**

Nothing here was re-run to look better. Every artifact is committed as it
read.

**Links** — previous release: [v0.18.0](RELEASE-v0.18.0.md) · closed plan:
[ROADMAP-v0.19](ROADMAP-v0.19.md) · next plan:
[ROADMAP-v0.20](ROADMAP-v0.20.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the void that measured what the gate could not see](blog/the-void-that-measured-what-the-gate-could-not-see.md)

## The headline finding: a perfect rate, and the control that voids it

**Before.** v0.18 gave the kernel a voice for the 2,172 terms its parser
could read, and named the silence: 10,605 nodes (83.0%) it could not. The
v0.19 design proposed to render the genuinely foreign part of that residue
by borrowing — a hand-authored loanword lexicon over Lean's constructors —
and to gate it not with a parser this project owns but with the
**already-pinned external Lean checker**, using the checker's elaborated
term as the identity witness.

**Now.** The whole preregistration chain landed in order, and the
registered run reads **VOID**.

| gate / control | verdict | deciding number |
|---|---|---|
| **B-P** — the serializer exists and is binder-name independent | FIRES | prototype's two retained pairs reproduce at 475 and 2,627 characters; hermetic, two-run byte-identical |
| **B0a** — the residue has territory (≥ 2,000) | FIRES | **4,191** foreign residue of 10,605 mute (6,414 transliterable, excluded) |
| **B0b+c** — the oracle can reach enough of it (≥ 1,000) | FIRES | **2,319** accepted, 1,872 rejected |
| **B0d** — the sealed hand-renderings, the real probe | FIRES | **100 of 100 reproduced byte-identically. Zero divergences.** |
| **B1** — identity floor ≥ 99.5% of the covered set | FIRES | **2,313 of 2,313 = 1.0**, holding 2,176 distinct elaborated terms, 99.9% `lean_workbook` |
| **B2** — rejection is a failure, not a skip | FIRES | outcomes `{identity: 2313}`; no silent drop |
| **B3** — the arithmetic closes | FIRES | 6,414 + 2,313 + 0 + 1,706 + 172 = **10,605**, exactly |
| **B4** — the register is frozen first | FIRES | committed in `297d1ea`, before `foreign_voice.py` existed; ordering checked against git history |
| **B5 / B6 / B7** | FIRE | two runs byte-identical; no learned component; 22 frozen digests revalidated before anything was measured |
| **C-V1** — the skeleton renderer, one-sided | HOLDS | true 1.0 vs skeleton **0.0** over the same 2,313; misses split 983 elaborated-to-a-different-digest / 1,330 failed-to-elaborate |
| **C-V2** — the transliteration null, a positive control | HOLDS | 1.0 identity over the covered set; over the transliterable 6,414, elaboration 0.9938 and identity 1.0 |
| **C-V3** — the determinacy sheet | **ABSENT** | the claim it alone could license is **not made**, here or anywhere |
| **C-V4** — the near-miss null | **VOID** | **`drop_group` 0.80 against its 0.90 floor** |
| **overall** | **VOID** | a voided control outranks a cleared floor |

**What the void actually says, and it is a real finding.** B1 compares the
*digests of elaborated terms*. So any rendering error that elaboration
erases — or that rule R's preamble silently regenerates — is invisible to
it. C-V4 exists to put a number under that blind spot, by mutating rendered
English one step and requiring the digest to move. Four of its five classes
behave: `swap_binder` 1.00, `shift_group` 1.00, `drop_ascription` 0.90. The
one that fails is `drop_group` at **0.80** — deleting a semantically
redundant bracket **changes the sentence and not the term**.

That is the design's own sentence — *identity holds up to what elaboration
erases and what the preamble rule regenerates* — **arriving with a number
on it**. The sentence was written into §3.2 as the claim's shape rather
than as a caveat, and C-V4 was built to measure it. It did. The measurement
came back outside the floor, and the floor was frozen before the instrument
existed.

**The consequence, stated hard.** The foreign `in words` line is **not
wired**. Serving a sentence under a certification whose own control voided
is precisely what the voiding sentence forbids, and no amount of "but B1
was 1.0" changes that. **B1's 1.0 may only ever be quoted with the VOID
beside it**, and this document does not quote it anywhere else.

**And the consequence has a second half, because a withheld capability
still has to be declared.** ROADMAP-v0.19 §1 planned a `foreign_voice` row
in the capability sheet quoting B1 from the artifact. The void meant the
line was never wired, and the rotation found the sheet had **no such row at
all** — the lane absent from it rather than published as off. That is not a
judgement call: the governing convention is written down in
[SPEC-chat-completions-skin](SPEC-chat-completions-skin.md) §7 —

> Rows the profile cannot serve (gloss under offline boot) appear with
> `"served": false` rather than disappearing.

— and `gloss` is the standing precedent for exactly this shape. **Resolved
rather than filed:** the sheet publishes a `foreign_voice` row with
`"served": false` whose reason is **sourced from the artifact**, the same
way the `realization` row quotes its rate from
`experiments/realization_rate.json` rather than from a number pasted into
the module. So an attaching orchestrator learns from the sheet that a
foreign voice exists, that it is withheld, and *why* — which is the honest
state of this cycle rendered as machine-readable capability rather than as
release prose. A rate is never published from a voided run; the void is.

**One number that is not a failure at all.** `drop_binder` measured
**0.18** — and it is *excluded from the voiding pool by preregistration*,
because it is blind by construction: the preamble rule regenerates exactly
what that mutation deletes, so B1 structurally cannot see it. That 0.18 is
not a miss; it **is the measured boundary of B1's blind spot**, the §8
non-claim made quantitative. A fresh-eyes review had independently measured
1 of 24 by hand; the registered run re-measured it rather than
preregistering a threshold at the number this project's own instrument had
produced.

**And a prediction refuted exactly as registered.** The design's §7
predicted binder-swap mutations would be a weak class. They measured
**1.00, 50 of 50** — the prediction is refuted, in the direction that makes
the control *stronger*, and it is recorded rather than absorbed.

**Demonstrate.** `experiments/foreign_voice_rate.json` — `verdicts.overall`
reads `VOID` and `verdicts.voided` reads `["C-V4"]`. Full readout: ANALYSIS
"v0.19 — the foreign voice: every gate fired and the control voided it".

### The register: the inventory of silence, which is the headline artifact

The design said before the run that the register — not the rendering rate —
would be this cycle's headline artifact, on the grounds that *a system that
renders most of a corpus and shrugs at the rest has told you nothing about
the rest*. The void makes that literal: the rate is unquotable and the
register is what ships. It is frozen with its `blocked_set_digest`
(`e51e5675…`) in `297d1ea`, before anything was rendered.

| blocking construct | bucket | statements |
|---|---|---:|
| namespaced and bare Mathlib heads, and the `√` notation | `mathlib_head` | **1,706** |
| propositional, modal, provability and set-theoretic statements | `no_row` | 75 |
| house ASCII notation that is not Lean in any alphabet | `no_row` | 53 |
| variable exponents and other terms core Lean cannot instantiate | `no_row` | 38 |
| the coercion arrow `↑` | `no_row` | 4 |
| a decimal literal the numeral pair cannot spell | `no_row` | 1 |
| an integer literal outside the registered numeral domain | `no_row` | 1 |
| **total** | | **1,878** |

**The two buckets are reported separately and never summed into one
"unsupported" figure**, because they are different kinds of fact: the 1,706
is a **budget consequence a maintainer can lift** by paying for Mathlib
coverage, and the 172 is a **design consequence this cycle owns**. Merging
them would hide which is which — which is exactly the shrug the register
exists to prevent.

**The mis-specification, named rather than argued around.** C-V4 inherited
C-R2's mutation idea *without* C-R2's load-bearing clause — that every
mutation is **verified to change the term before it is rendered**. C-R2
discards non-mutations and counts the discards; C-V4 does not, so some of
its `did_not_differ` cases may be mutations that never changed the term at
all. A re-specified control that carries the verification clause is
**future work, not a re-score**: this run is committed as it read, and the
successor control gets its own preregistration. Recorded in ROADMAP-v0.20
as a carried lane with the foreign wiring gated behind it.

**An artifact defect, reported and not fixed.** `shift_group`'s
`of_which_digest_moved` reads **33** where the true value is **0** — the
field double-counts the 33 cases where the inverse refused. The class's
rate of 1.00 is correct and the verdict is unaffected (49 differed = 33
inverse-refused + 16 elaboration errors). Fixing the field means re-running
a registered artifact, which costs more honesty than it buys. Filed.

## The second finding: two glyphs, and half the corpus

**Before.** The native voice reached 17.0% of the corpus. v0.18's own
rotation had measured why: half the mute mass was not foreign at all, just
two characters away from parseable.

**Now.** `≥`→`>=` and `≤`→`<=`, added to the tokenizer on the existing
native path:

| | statements | rate |
|---|---:|---:|
| parseable under the retired parser | 2,172 | 0.1700 |
| **parseable now** | **8,586** | **0.6720** |
| newly reached | **6,414** | floor was 6,000 — **met** |
| newly reached that round-trip exactly | **6,414 of 6,414** | **1.0000**, 0 refused, 0 failed |

**The caveat travels with the number, verbatim, because the artifact makes
it.** The newly-reached set is **one corpus and two distinct call heads**
over 6,414 statements — 4,733 occurrences of `≥` and 1,681 of `≤`, numeric
inequalities almost without function application in them. It is *large and
structurally narrow*. A 1.0000 round-trip over it **does not establish that
the realization lexicon covers the corpus**; it establishes that the
statements two glyphs unlock carry heads the lexicon already had.

**No floor was pre-committed on that second rate, deliberately, and the
reason is recorded before the reading rather than after it**: a high rate
says the newly-reached statements are the same grammar in every respect
that matters; a low rate would have been the *more* interesting
finding — parsing bought reach without buying voice — and a pre-committed
floor is exactly what would have pressured this lane not to publish it.
v0.18's R1 floor was explicitly **not** imported: it was frozen against a
different denominator under a different preregistration.

**Additive-only, proven rather than asserted — and the witness reports two
scopes, which must not be confused.** It loaded the **retired parser out of
git in its own interpreter** and ran `answer._in_words`, the exact function
`render` uses to decide the line, before and after.

- **Corpus-wide** (`corpus_wide_reading`, the claim that matters): over all
  12,777 statements, **6,414 gained, 2,170 unchanged byte-identically,
  4,193 still silent, 0 changed, 0 lost.**
- **Over the task book** (`claim`, scoped to the 30 `corpus_definition`
  tasks — the only kind whose expected content is a rendered entry):
  **0 gained, 30 unchanged, 0 changed, 0 lost.** The book's tasks carry
  neither glyph, so the successor task book's expected records were
  untouched by the widening. That is why the two digests in that block are
  *identical*.

The generator refuses to write the file at all if `changed` or `lost` is
non-zero, so additivity is enforced rather than reported.

**Demonstrate.** `experiments/transliteration_rate.json` and
`experiments/transliteration_served_diff.json`; the successor parser digest
`f5b2abba…` supersedes `65fead2f…`.

### The re-freeze discipline, executed whole

This lane edits a file that two registered runs had pinned. ROADMAP-v0.19
§3a wrote the discipline before the code existed, and it was followed to
the letter:

- **The amendment landed before the code.** Both parser pins were retired
  *for future comparisons* in `experiments/realization_prereg.json` and
  `experiments/foreign_voice_prereg.json`.
- **Both prior rates were declared HISTORICAL in writing.** v0.18's 0.9991
  and this cycle's foreign-voice run remain the artifacts of record for
  what was measured under the retired parser. **v0.18 was not re-run**, and
  the reason is recorded rather than left to inference.
- **Both old registered CLIs now refuse to run, by two different
  mechanisms**, and neither writes a file. `measure_realization` exits
  **4** with an explicit closed-by-amendment refusal that names the
  amendment, calls `realization_rate.json` a historical artifact, points at
  the successor, and offers `--no-write` for reading the old numbers
  without overwriting the record. `measure_foreign_voice` exits **2**
  because **its own B7 control catches the moved parser digest** —
  `f5b2abba…` where the preregistration recorded `65fead2f…` — and refuses
  to publish any rate. The second is the better of the two: the
  preregistration machinery closed that CLI without anyone having to
  remember to. **Neither can mint a rate blended across two parsers**,
  which is the whole point — a rate is a claim about the reader it was
  measured under.
- Two downstream ledgers were regenerated **provenance-only** — every
  measured number identical.

The gap ROADMAP-v0.19 §3a named in advance is the one this discipline
covers: `match_signatures.py` is **not** in the task book's witness list,
so a tokenizer change moves *rendered output* while every witnessed digest
stands still. The served diff is that gap's answer, committed with the
probe.

## The third finding: a probe that parked, by its own rule

**Before.** `DESIGN-block-vocabulary` was the maintainer-seeded incumbent
the v0.19 course **adopted rather than displaced** — the no-silent-disposal
instruction discharged by scheduling it, bounded, against three baselines
taken from its own §4 falsifier list and preregistered in their own commit
before any measurement.

**Now.** It ran, and it **parks with the numbers**.

| baseline (the design's own) | floor | measured | verdict |
|---|---|---|---|
| retrieval — the resolver's keyword channel | coverage 0.833 / FP 0.030 | **0.3256 / 0.2059** | **NOT BEATEN** |
| compression — zstd as an archive | 118,328 bits | 829,048 | **NOT BEATEN** (7.01× worse) |
| compression — zstd separately addressable | 5,182,024 bits | 829,048 | BEATEN (6.25×) |
| term layer — canon tokens | 8.44× | **6.91×** | **NOT BEATEN** |

**One of three, and it is the pre-conceded one.** The compression win was
registered *in advance* (E2) as an arithmetic restatement of the existing
MDL ledger rather than a new finding. The two baselines that needed this
probe to produce something new both lost, and retrieval is not close: on
the **same rows in the same run**, the block channel reaches 0.3256 where
the keyword channel reaches 0.9302, and claims 0.2059 of the rows it should
refuse where the keyword channel claims 0.0294.

**The single question is answered, and the answer is no.** *Is the unified
dictionary a real object, or two existing objects wearing one id space?*
The unified space beats grep by 210,248× and a zstd-scan by 9,013×, which
the preregistration had already declared **is not evidence for
unification** — it is evidence that an index beats a scan, and both indexes
already had that separately. Against two indexes carrying **one tag bit**,
unification measures **0.9981**. A namespace bit sells dispatch fractionally
cheaper than a merged directory. Answer: **two existing objects wearing one
id space.**

**What survives for any future unpark**, named so it is not lost: the
design's append-only, path-independent growth property, which **no baseline
in this probe tested**.

**Demonstrate.** `experiments/address_space_probe.json` — `verdict.
disposition_read_honestly`; the design's own §3e records all four readings.

## The fourth finding: nobody in this graph disagrees about notation

**Before.** The v0.19 course's TWO RIGHTS direction wanted statements that
say the same mathematics under two defensible conventions. Its one-hour B0
probe was adopted with both branches committed in advance.

**Now.** The census branch landed, and **landed narrow — and the narrow
reading is the finding.** Of 2,493 co-present pairs with differing
canonical forms, 200 fork at a single discriminator subterm and **125 are
convention-pair candidates. Every one is notational** — a glyph, a
namespaced-versus-bare head spelling, or where somebody put a parenthesis.
**Zero are mathematical convention forks.**

Inside the hand-authored corpora the registered negative is **unqualified**:
1 of 125 candidates touches an authored corpus and **0 have both members
authored**. Conventions here were fixed by the author and never forked, and
nobody had written that down. The three famous clashes the roadmap named —
sign conventions, the 0-in-ℕ boundary, 2π placement — return **0, 0, 0**,
with the detectors proven live by injection so the zero is a reading and
not a broken sweep.

**And the two probes turned out to be looking at one thing.** The single
largest candidate class — **98 of 125 pairs forking `>=` against `≥`** — is
the transliteration lane's territory seen from the other side. That is a
fact about the corpus, not a coincidence of method.

**Consequence.** The full TWO RIGHTS direction **parks with an empty
mathematical denominator**. One further measurement fell out: the
anonymized-template pass contributed **0** pairs the twin ledger did not
already carry, out of 1,015 template-sharing pairs — the twin ledger is the
stronger pool, measured for the first time.

## Roadmap triage

**Shipped as a void, instruments kept.** *Item 1.* Every gate fired; C-V4
voided; the line is not wired. What survives unscored and permanent: the
register (the inventory of silence — 1,706 `mathlib_head` and 172 `no_row`,
reported separately because the first is a budget consequence a maintainer
can lift and the second is a design consequence this cycle owns); the B-P
serializer with binder-name-independent digests; B0d's 100 sealed
hand-renderings, which the later implementation reproduced **byte-identically
100 of 100** — a preregistration that predicted its own implementation's
output exactly; and rule R.

**Shipped as a product number.** *Item 3a.* 17.0% → 67.2%, with its
composition caveat and its additive-only proof.

**Shipped as a park-by-numbers.** *Item 2.* The no-silent-disposal
instruction is now **fully discharged**: adopted → built → measured →
parked *by numbers*, in the design's own §3e. That is the complete
lifecycle a park is supposed to have.

**Shipped as a registered negative.** *Item 3b.* Narrow census, zero
mathematical forks, direction parked.

**Drift audit** (v0.17 and v0.18 re-read). Nothing lost to attrition. Two
lanes reach their fourth recorded pass-over and are named again rather than
allowed to erode: the **cost ledger** and **ledger-first claims**, both
carried to ROADMAP-v0.20 with their triggers intact. The
`_route_ownership` receipt duplication reached its **third** cycle, which
is what the v0.18 note said would force a decision — and the decision was
taken rather than deferred: **SCHEDULED**, as a named early item in
[ROADMAP-v0.20](ROADMAP-v0.20.md) §4, with the fix, the before/after
measurement it has owed for three cycles, and its new-seal cost all written
down. A land-or-close clause discharged by a landing plan is the audit
working as intended.

## Discoveries of the cycle

Quoted from [DISCOVERIES](DISCOVERIES.md):

- *"The gate's blind spot has a number now, and the number voided the
  gate."* Deleting a semantically redundant bracket changes the sentence
  and not the term: `drop_group` 0.80 against a 0.90 floor.
- *"Two glyphs were half the wall, and the measurement completes."* 17.0%
  → 67.2%; the prediction made at the v0.18 rotation, executed and
  confirmed at 6,414 of 6,414.
- *"A park with numbers is what discharging an instruction looks like."*
  Adopted, built, measured, parked — the block-vocabulary lifecycle end to
  end.
- *"A control inherited without its load-bearing clause is a different
  control."* C-V4 took C-R2's mutation idea and left behind
  verify-the-term-changed.

## Resolved from BACKLOG

- The **transliteration lane pointer** filed at the v0.18 rotation is
  **RESOLVED by shipping**, including the re-freeze discipline it warned
  about and the served-diff witness it demanded. Annotated in place with
  its numbers rather than pruned.
- The **STRANGER intake** entry is unchanged and still parked.
- **Newly filed**: the C-V4 mis-specification and its re-specified
  successor; the `shift_group` artifact defect; the grouping-canonical
  rendering question the void raises; and the register's `mathlib_head`
  bucket as a lift-able budget rather than a design limit.
- `_route_ownership`'s receipt duplication: third cycle, and **decided —
  SCHEDULED** as ROADMAP-v0.20 §4 rather than carried a fourth time. The
  entry stays open until that item lands with its measurement, which is the
  condition written into it.
- The capability sheet's missing `foreign_voice` row: **resolved**, not
  filed — the row ships `"served": false` with an artifact-sourced reason,
  per SPEC §7's standing convention.

## Honest limits carried forward

- **The foreign voice is not served, and B1's 1.0 does not travel alone.**
  The overall verdict is VOID. Every quotation of that rate in this
  repository carries the void beside it.
- **B1's blind spot is 0.18 wide on `drop_binder`** by its own measurement,
  and that class is excluded from voiding by preregistration — which makes
  it a published boundary, not a hidden one.
- **C-V4 is mis-specified**, and the re-specified control is future work.
  Nothing about this run is re-scored on that basis.
- **`shift_group`'s `of_which_digest_moved` is wrong in the artifact** (33,
  true 0). The rate and verdict are unaffected. Not fixed, because fixing
  means re-running a registered artifact.
- **C-V3 is ABSENT and the claim it licenses is not made**: nothing here
  says a *reader* can recover the mathematics from the English. The claim
  is that the English determines the term **to the pinned elaborator** —
  a claim about a machine.
- **67.2% is a parse rate over one corpus and two call heads.** It is not a
  lexicon-coverage claim, and the artifact says so in three places.
- **The address-space probe's one win was conceded in advance.** Reading it
  as a compression result would be reading a restatement as a finding.
- **The TWO RIGHTS negative is about the 26 authored corpora.** The 125
  notational candidates are a fact about an upstream dataset's ingestion,
  and the two numbers must not be quoted apart.
- **99.9% of the covered foreign set is one corpus.** 2,313 statements
  holding 2,176 distinct terms.
- A passing Python test is not a Lean proof.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.** `git diff
--name-only v0.18.0..HEAD -- data/ experiments/` lists **eighteen paths and
not one `.py`**: seven reviewed `data/foreign_voice/` artifacts (rule R,
the loanword lexicon, the register, B0d's sealed renderings with their ids
and appendix, the eligibility preview) and eleven `experiments/` ledgers
(the four registered readouts, their three preregistrations, the amended
`realization_prereg.json`, the served diff, and two provenance-only
regenerations). No training corpus moved and no `experiments/*.py` changed,
so **the checkpoints attached to v0.6.0 remain accurate for this release**.
Everything is committed in-repo and linked by path rather than uploaded.

## The next direction, chosen before this document — and it is a returning one

The outside design inquiry was **invoked** again, which makes this the
**second consecutive strict invocation** and closes twice over the loop
ROADMAP-v0.18 opened when it restored the release skill's wording and wrote
that a reaffirmation "was available once, recorded once, and is not
available again by inheritance."

Three isolated series, three rounds each — **nine rounds, fifteen
round-one directions, $3.12** — from an empty non-git directory outside the
repository under a full tool denylist, with session ids and per-round
prompt hashes committed in `reports/design-direction-v0.20.json` (brief
`11c676b6…`; isolation mode inherited unchanged from the v0.19 receipt).
Finalists **VERDICT**, **EVAL**, **WORD OF HONOR**.

**Selected: EVAL → `docs/DESIGN-statements-that-run.md`** — statements that
decide themselves, with NIHIL's grounded negatives folded in as a second
answer type. ~12,700 decidable candidates; named residual, *correlated
interpretation*. The design is in draft with adversarial review to follow,
so [ROADMAP-v0.20](ROADMAP-v0.20.md) §1 carries its gate clauses once it is
committed rather than inventing them in advance.

**The lineage is the finding.** EVAL is **RUNNABLE returned** — proposed in
the *v0.19* course and **dropped at its round two**, returning now on stated
new evidence, quoted from the receipt:

> the C-V4 void proved the error class an evaluator catches is invisible to
> every structural gate, and both cost discounts (exact rational
> arithmetic; the external-verifier lane) are measured facts. A dropped
> direction returning with new evidence is the funnel working, recorded as
> such.

That evidence is **this release's own void**. A structural gate cannot see
an error that elaboration erases; an evaluator checks what the thing
*computes*, which is exactly the class `drop_group` slipped through. A
funnel that only discards is a filter; one that readmits an idea **on
recorded evidence, with the original rejection still in the record**, is
doing the harder thing — and the difference between that and re-proposing
something until it sticks is entirely what got written down the first time.

**Every declined direction carries its disposition**, and one deserves
naming here: **WORD OF HONOR is parked as the strongest thesis-level
candidate** — parked for *shape*, not merit, because its first slice is
seed-reading and the governance record counsels against an instrument as a
headline. Its extraction-discipline census rides as an optional rider any
cycle can run. **HOSTILE DICTATION** is parked with the list's only
prohibition-shaped trigger: it **MUST run before any untrusted stream
reaches the write gate**. VERDICT, DEBT NOTES, COURIER, UNSAY, BORROWED
PREMISES and SECOND VOICE are parked with their one-line dispositions, and
two riders were accepted — the HOLES counting table (revive-or-close
FOUNDRY with a number) and the delete-K ground-truth table. All are carried
into ROADMAP-v0.20 §3 and §5.

The advisors disclosed **four** collisions with prior-course or parked
ground themselves — HOLES vs CONJECTURE FOUNDRY, UNSAY vs the voided
retraction radius, ONE HOP vs substitution chains, NIHIL vs the
grounded-negatives cut. Isolation working without needing to be perfect.

## The release refresh

Every generated ledger regenerated on the tip, and **the working tree came
back byte-clean after the full chain**:

- `check_regeneration.py` — *"coherence OK: 25 seeds regenerate committed
  data byte-identically across `data/`, `data_holdout/`"*
- `validate_nodes.py` — *"Validation passed for 12777 statement nodes
  across 27 corpora."*
- `signature_matches`, `specializations` and `compression` all
  regenerated; `check_report_regeneration.py` reads **clean / clean /
  clean**, with `decompositions.json` a **declared** divergence carrying
  its TRIAGE-v0.11 citation
- `ingest_wold.py reach` — **1,395 of 1,460** core LWT meanings map
  (95.5%), **1,394** of them through WordNet lemmas

### The refresh caught something, and it was not a ledger

The first pass did not come back clean: **`check_regeneration.py` exited 1
on `data/foreign_voice` as an orphan corpus** — a directory under `data/`
that no seed script generates. That is the check working. The
investigation is the part worth recording, because it found the *second*
directory in the same position and the reason nobody had noticed:
**`data/realization` was escaping the same orphan check only by a
name-coincidence substring match in an unrelated seed.** It had been
exempt since v0.18 by accident, not by decision, and the check would have
kept passing it indefinitely.

Both are now **registered explicitly** as hand-authored preregistration
directories (`20eb26b`), with the reason written into the source rather
than into a commit message: their regeneration discipline lives in their
own digest pins and tests — `experiments/realization_prereg.json`,
`experiments/foreign_voice_prereg.json` — and not in a seed script. The
commit's own sentence is the rule it establishes: **"an exclusion that
exists by accident is an exclusion nobody decided."**

**A second lesson, smaller and worth writing down before it costs
something.** The refresh runs its steps through a pipe to `tail`, and a
pipeline's exit status is the *last* command's — so `check_regeneration`'s
exit 1 was masked, and the failure was visible only because its message
happened to be inside the tail window. A refresh that reports a step's
output without reporting its exit code is not checking that step. Filed
with the same reasoning as the register's two buckets: a check whose
failure can go unread is a check nobody is running.

## The suite at the tip

[SUITE-GATE-V19: full-suite verdict and timing at the frozen v0.19 tip land
here before the tag. The baseline is v0.18.0's gate — **1,827 tests, 0
failures, 3 skipped, 24,117.3 s (6 h 42 m), green on the first run**,
receipt in `reports/test_gate_v018/`. Measured for this rotation: the **13
test modules this cycle added or changed run 381 tests, 0 failures**
(`test_foreign_voice` 34, `test_foreign_voice_lexicon` 47,
`test_foreign_voice_oracle` 24, `test_foreign_voice_register` 22,
`test_foreign_voice_b0d` 17, `test_measure_foreign_voice` 26,
`test_transliteration` 44 with 2 skipped, `test_address_space_probe` 20,
`test_convention_probe` 17, `test_block_mdl` 19, plus the realization and
skin modules they touch). `tests/git_ordering.py` defines TestCases but has
no `test_` prefix, so discovery does not collect it — worth confirming that
is intentional at the gate. The 2 skips in `test_transliteration` and any
Lean-dependent skips are the ones to account for.]

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/check_report_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py

# On Windows every command below needs PYTHONIOENCODING=utf-8: these scripts
# print the very glyphs this cycle is about, and cp1252 turns that into a
# UnicodeEncodeError and exit 1 -- which reads like a refusal and is not one.

# 1. the native voice after two glyphs: 8,586 of 12,777 parse
PYTHONIOENCODING=utf-8 python scripts/realize_term.py --census

# 2. one newly-reached statement, rendered and round-tripped
#    -> "variable zero is at least one", round_trip EXACT
PYTHONIOENCODING=utf-8 python scripts/realize_term.py --term "x >= 1"

# 3. the void, read straight off the registered artifact
python -c "import json; d=json.load(open('experiments/foreign_voice_rate.json',encoding='utf-8')); \
    v=d['verdicts']; print(v['overall'], v['voided'], v['summary'])"

# 4. the register -- the inventory of silence, and the cycle's headline artifact
PYTHONIOENCODING=utf-8 python -c "import json; r=json.load(open('data/foreign_voice/register.json',encoding='utf-8')); \
    [print(e['blocking_count'], e['bucket'], e['construct_class']) for e in r['entries']]; \
    print('total', r['blocked_total'])"

# 5. the address-space probe's honest reading, and the single question
python -c "import json; v=json.load(open('experiments/address_space_probe.json',encoding='utf-8'))['verdict']; \
    print(v['baselines_beaten'], v['baselines_beaten_detail']); print(v['the_single_question']['answer'])"

# 6. the convention-pair census and its registered negative
python -c "import json; d=json.load(open('experiments/convention_pairs_probe.json',encoding='utf-8')); \
    print(d['census']['counts_by_verdict']); print(d['famous_clash_sweep']['counts'])"
```

Step 1 now reads **8,586 of 12,777**; the `2,172` in
`experiments/realization_rate.json` is the historical figure under the
retired parser and is not re-measured.

**Two commands in [RELEASE-v0.18.0](RELEASE-v0.18.0.md)'s reproduce block
are now dead, deliberately, and this is the notice.** That block's
`python scripts/measure_realization.py --out realization_rate.repro.json`
exits **4** and writes nothing, so the digest comparison on the following
line then fails on a missing file. Both are supposed to be dead: re-running
that run today would blend two cycles' denominators into one rate neither
cycle's floor can be checked against. To read the v0.18 numbers without
overwriting the record, the refusal names the way — `--no-write`.
`measure_foreign_voice` refuses too, at exit **2**, through its own B7
digest check.

Reproducing the foreign-voice run additionally requires the pinned Lean
toolchain (`leanprover/lean4:v4.32.2`) — though in this tree it never gets
that far, because B7 refuses first. Without the toolchain the oracle
refuses rather than downloading anything, and publishes no partial rate.
