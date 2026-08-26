# v0.20.0 — two registered runs, opposite verdicts, and both of them published

Last cycle the foreign voice scored perfectly and was **withheld**, because a
control built to bound that score came back under its floor. This cycle that
control's successor was re-aimed at a repaired grammar, run against a floor
**raised** above the one the old control had failed, and it cleared. **The
foreign `in words` line is served.**

In the same cycle, a brand-new capability — statements that compile into
something you can run — was built, wired, and **voided on its own controls**.
It ships anyway, with the void published on the route it serves from, and
**no conformance rate exists anywhere in this repository**.

One discipline produced both outcomes. Every floor in both runs was frozen
before its instrument existed, and neither run was re-executed to read
better. When the records around two controls turned out to be wrong, the
**records** were corrected and the measurements were not repeated.

**Links** — previous release: [v0.19.0](RELEASE-v0.19.0.md) · closed plan:
[ROADMAP-v0.20](ROADMAP-v0.20.md) · next plan:
[ROADMAP-v0.21](ROADMAP-v0.21.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the floor no instrument could meet](blog/the-floor-no-instrument-could-meet.md)

## The headline finding: a repair that closed the hole, measured by the instrument that found it

**Before.** v0.19's `drop_group` control read **0.80** against a 0.90 floor.
Deleting a semantically redundant bracket changed the English sentence and
not the elaborated term, so the identity gate could not see the difference.
The overall verdict was VOID and the foreign line was never wired.

**Now.** The renderer emits a **canonical bracketing** — a committed
precedence rule with a digest — and the hole is gone from the grammar rather
than bounded more tightly. Every gate cleared and no cycle-stopping control
voided:

| gate / control | verdict | deciding number |
|---|---|---|
| **G1** — the canonicalizer agrees with the pinned parser | FIRES | **2,313 of 2,313** elaborate byte-identically; zero disagreements |
| **G1b** — no redundant grouping bracket survives, over the whole set | FIRES | **5,228 of 5,228** grouping-pair deletions detected; **zero blind** |
| **G2** — the re-seal reproduces | FIRES | **100 of 100** re-sealed renderings byte-identical; the 85 unchanged ones also byte-identical to v0.19's seal |
| **B1** — identity over the covered set | FIRES | **2,313 of 2,313**, holding **2,176** distinct elaborated terms, **99.9% `lean_workbook.ground.v1`** |
| **B3** — the arithmetic closes | FIRES | 0 + 2,313 + 0 + 1,706 + 172 = **4,191**, exactly the current mute total |
| **C-G1** — the aiming test | HOLDS | **42 of 42 = 1.00** against a 0.95 floor (**42/50 = 0.84** on the other admissible denominator, published beside it) |
| **C-V4′** — the re-specified near-miss null | HOLDS | every voiding class over its floor; `drop_group` **42/42** on a floor **raised to 0.95** |
| **C-V1** — the skeleton renderer | HOLDS | skeleton **0.0** against the true renderer's 1.0 |
| **C-V2** — the transliteration null | HOLDS | **1.0** over the covered set (floor 0.99); the transliterable arm is **vacuous — 0 statements** |
| **C-V3′** — the machine blind reader | **VOID** | ratio **0.594** against a 0.5 voiding threshold. Non-blocking; the machine-reader claim is not made |
| **C-V3** — the human determinacy sheet | **ABSENT** | no non-maintainer adjudicator exists; the human-reader claim is not made |
| **overall** | **FIRES** | `verdicts.overall` reads `FIRES`; `verdicts.voided` reads `["C-V3′"]` |

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python scripts/answer.py leanworkbook.skel.lean_workbook_7992
formally   : 2*x+1 >= 0 ↔ x >= -1/2
in words   : for every variable zero of type rational it holds that two times
             variable zero plus one at least equals zero exactly when variable
             zero at least equals minus one divided by two
```

That sentence comes from the **foreign** lane, not v0.18's realizer:
`answer._in_words` returns nothing for this statement, and
`answer._foreign_in_words` supplies the line only because
`answer._foreign_voice_armed()` reads the registered artifact and says the run
cleared. Two more with the same shape:
`leanworkbook.skel.lean_workbook_43951`,
`leanworkbook.skel.lean_workbook_31314`.

### Three sentences this release is bound to say, and says here first

The preregistration recorded these as release obligations before the numbers
existed (`experiments/foreign_voice_prereg2.json`, `H4`/`H5`), and they are
the difference between a repair and a flattering restatement.

1. **C-G1's denominator is a registered choice, and the alternative is
   published beside it.** Eight of the fifty replayed statements no longer
   admit a `drop_group` mutation at all under canonical rendering, because
   canonicalization left them with no grouping pair. Scoring the 42 that
   remain gives **1.00**; keeping all fifty in gives **42/50 = 0.84**, which
   is **below the floor**. The choice is defensible — you cannot detect a
   mutation that cannot be constructed — and it is a choice, so both numbers
   travel together.
2. **The ten named blind cases are 7 detected and 3 no-longer-admitting.**
   *Not* "all ten detected." Those ten were pinned by statement id before the
   canonical renderer existed, and all ten are cleared — zero still blind —
   but "cleared" means two different things across them and the release says
   which.
3. **C-G1's 1.00 is not the same quantity as v0.19's 0.80.** One measures the
   term path and the other the surface path. **The commensurable repair
   number is `C-V4′ drop_group`: 42 of 42, on a floor raised from 0.90 to
   0.95.** That is the comparison a reader can actually make.

### The prediction that missed, and why the miss is the finding

C-V4′ restored the clause C-V4 had inherited-without: **verify each mutation
changed the term before rendering it, discard the ones that did not, and
count the discards.** The design pre-registered a point prediction for
`drop_ascription` — *"45 of 50, exactly v0.19's reading"* — and it was
**wrong**.

Measured: **45 detected of 45 scored, with 5 discarded as non-mutations.**
The numerator held exactly. The **denominator** moved. So `drop_ascription`
read 0.90 in v0.19 not because the gate missed five near-misses, but because
five of its "mutations" were not mutations at all. The restored clause did
precisely the work it was restored to do, and it did it by falsifying the
prediction of the person who restored it.

### The cost of the repair, in the control's own numbers

Canonical grouping is not free, and the run's own C-V1 shows the price.
The skeleton renderer still scores **0.0** against the true renderer's 1.0,
so the gate demonstrably reads the words. But the *composition* of C-V1's
misses moved: v0.19 had **983** scrambled surfaces elaborating to a
*different* term against 1,330 that failed to elaborate at all; v0.20 has
**517** against **1,796**. The share of C-V1's misses that actually
**exercised** the identity comparison fell from **42.5% to 22.4%**.

Canonical rendering removes grouping words, so a scrambled surface has less
structure left to survive the trip back and more of it dies at the parser
before any comparison happens. 517 genuine different-term detections is not a
small number and the control still holds — but it is doing **less work** than
it was, and that is a **priced cost of canonical grouping** rather than a
free improvement.

### The instrument this cycle bought, which voided

**C-V3′, the machine blind reader**, was a maintainer directive: a pinned
local model reads each served English sentence **blind — the term is never
shown** — and reconstructs the formal term, scored both by reconstruction and
**discriminatively**, against distractors built from the mutation classes.

It **voided**. The served arm read **0.8417** (101 of 120) and cleared its own
0.5 floor. The **skeleton** arm — the same reader on scrambled surfaces — read
**0.5000** (20 of 40), and the ratio skeleton-over-served is **0.594** against
a voiding threshold of **0.5**. A reader that recovers half as much from
nonsense as from the real sentence is not reading the sentence; it is reading
the alphabet. So **the machine-reader claim is not made**, and C-V3′ is
published as a **void, never as a rate** — `serve_chat.py:515-537` emits
`"claims": null` for both C-V3 and C-V3′.

**And it does not stop the cycle**, by preregistration. The arming gate reads
**five cycle-stopping controls** — C-G1, C-V4′, B1, B3, B5 — plus
`overall == "FIRES"` (`scripts/foreign_voice_arming.py:80-96`). Its docstring
is explicit that the rule is *not* "nothing voided", because
`verdicts.voided` legitimately contains C-V3′. **C-V3 (human) stays ABSENT**
and the human-reader claim stays not-made; a measured machine number is the
most tempting thing in this lane to over-read, and it is the one number
nobody may quote as a reader number.

### The bookkeeping the run refused to proceed without

**B3 closes at 4,191, not at 10,605**, and the reason is a v0.19 lane landing
after v0.19's run. Two glyph equivalences widened `TOKEN_RE` at `b1c9440`, so
6,414 previously-transliterable statements became natively parseable: mute
**10,605 → 4,191**, transliterable **6,414 → 0**.

**The first execution of this cycle's run refused, and it was right to.** Its
own B0a guard fired — *"B0a recomputed differently; the denominator moved"* —
and it wrote nothing. The regeneration that followed verified, **before any
score was computed**, that the residue's **statement-id set is identical** to
the committed one: `scripts/measure_foreign_voice2.py:460-466` sorts the
recomputed and committed id lists and raises `RunRefusal` on any difference,
at line 460, while `b1()` does not run until line 482. Zero of 4,191
per-statement records differ.

**And the refusal is itself a finding.** The preregistration's frozen row for
`match_signatures.py` carried the **correct digest beside a false sentence** —
*"Still 65fead2f…"* when the file was already `f5b2abba…`. A freeze list is
machine-checked on exactly one field, while every other sentence in it
carries the same authority to a reader and none of the verification. **A
freeze list can carry a true digest beside a false sentence**, and only a
human ever reads the sentence.

### The reproduction proof, and what it is not

`experiments/foreign_voice_rate2.json` is **6,741,627 bytes** with LF sha256
`acb01a5f42c7bcdd5000aa9ca8e47981310fb955892907cef2d25ef4dfceeeca`, and
**three separate scoring process invocations on two different days produced
those same bytes** (`experiments/ANALYSIS.md`, *"Provenance of the run itself
— three executions, one reading"*). That is **stronger** than B5's own gate,
which compares two passes *inside* one process.

It is also the record of a process error reported rather than buried: the
second attempt ran **twice, concurrently**, because an empty log and a
missing artifact were read as a dead launch when they were the runner's
expected mid-run state. Both completed, both wrote identical bytes, and the
third execution — single process, waited on directly — reproduced the
committed file byte for byte with `git status` clean. **The reading was never
in doubt; the discipline was, and "executed once" was the instruction.**

## The second finding: a capability that voided on its own controls, and serves the void

**Before.** A statement in this library was a fact on a shelf. Nothing could
take one and *run* it against numbers a person brought.

**Now.** `experiments/conformance_run.json` — executed once, on a committed
tree (`commit c428cfb`). **8,017 statements compile** into conformance
programs against a floor of 5,000, which the artifact itself calls a
disclosed formality. And the run's overall verdict is:

> **VOID — C-E1 missed its floor; every `NO_COUNTEREXAMPLE_FOUND` in this run
> is void.**

| gate / control | verdict | deciding number |
|---|---|---|
| **E0b** — enough statements compile | MET | **8,017**, floor 5,000 |
| **E1** — the ground class decides without refusing | **MISSED** | 297 ground: **257 TRUE / 15 FALSE / 25 REFUSED** against a **zero-refusal** floor |
| **E2a** — statements admit a sampling point | MET | **96.0%** (4,114 of 4,287), floor 80% |
| **E3** — the corpus arithmetic closes | MET | **12,777 exactly** |
| **E4** — the constructed decidable class | MET | **110 of 110** against an independently keyed answer set |
| **C-E1** — the perturbation control | **VOID** | **0.650** flip rate against a **0.99** floor |
| **C-E2** — the guard contrast | **VOID** | **1.75×** against a **10×** floor |
| **C-E3** — external adjudication of counterexamples | **DID NOT EXECUTE** on the sampled class | 25 attempted, 0 adjudicated; the ground half agreed **12 of 15** |
| **E5**, **C-E1's second arm** | **UNRUN** | registered, never executed — a gap, not a void |

**E1's miss is a domain consequence, and the floor existed to find it.** All
25 refusals decompose into three kinds, each a consequence of the *declared*
Nat/int domain rather than a bug: **13 `negation_outside_carrier`**, **8
`evaluation_error` with detail *division by zero*** (truncating division), and
**4 `evaluation_budget_exceeded`**.

### C-E1: a floor no correct instrument could meet

**This is the cycle's most transferable finding, and it is bounded.** C-E1
mutates a statement so it *should* become false, and requires the sampler to
notice at ≥99%. It measured **0.650** over 1,027 mutations of 300 statements.

The mechanism is in the artifact: **some mutation classes over `Nat` are
structurally unflippable.** Mutating `a² + b² ≥ 2ab` into `a² + b² ≥ -2ab`
over the naturals produces a statement that is *still true*, because there is
no negative side of the carrier for it to fall off. **On those, no correct
instrument could reach the floor** — a perfect sampler would also report no
counterexample, because there is none.

**And the bound matters as much as the mechanism.** `lean_workbook_10087` — 73
admitted points, `≥ 0` mutated to `≥ 1` — is a **real sampler miss**, and it
sits in the same twelve. So the 0.650 is **not** entirely the floor's fault.
**The honest partition is unmeasured**: this run has no instrument that
separates structurally-unflippable mutants from genuine sampler misses, so
the 0.650 **cannot be attributed**, and the release does not attribute it.

Two more properties of that number, recorded rather than discovered later:
C-E1 counts an **errored** mutant point as a flip, a bias **toward** the floor
it missed anyway (so a corrected count can only be lower); and `per_class` is
a **four-row table of a five-class generator** — `reassociate_an_operator`
never fired, and it is exactly the class whose mutants the discard rule would
have caught, so `discarded_as_non_mutations: 0` is not evidence the discard
rule was idle.

### C-E3: a control that worked only where it was not needed

C-E3 exists to hand counterexamples to an external checker for independent
adjudication. It attempted **25** sampled counterexamples and adjudicated
**none of them** — and the reason is not the boundary the design predicted.

`measure_conformance.py:709-717` builds the adjudication list out of the raw
`canonical_ascii` and `:464` hands it to the checker unchanged. **The
record's own `counterexample.bindings` are never substituted.** So on a
sampled statement the text handed to the checker still carries **free
variables**, and all 25 "decide did not reduce in either direction" rows are
unknown-identifier elaboration failures. That is an **instrument gap**, not a
measured carrier boundary — and the carrier boundary was therefore **not
measured this cycle at all**.

What stands is the half that needed no substitution: **ground statements have
no free variables**, so for them the raw text *is* closed, and C-E3 confirmed
**12 of 15** ground verdicts with **zero disagreements**. A control that works
only where it is not needed is still a control that did not run.

The dead code that caused it — `_lean_expression` at `:434-438`, whose one
return sits behind a literal `if False else`, and `:463`, which assigns
`typed` and discards it on the next line — is **left in place**. It is the
evidence for the correction, and deleting the evidence while filing the
finding is the wrong order.

### 775 counterexamples, and not one published as a corpus error

E2 found **775** sampled counterexamples. **Zero were independently
adjudicated**, and none is published as a defect in anyone's corpus. §3.5's
clause was written before the run for exactly this.

Every served `NONCONFORMANT` verdict carries the correlated-interpretation
label at runtime (`conform.py:518-526`) and on the served line. **The 775 rows
in the artifact do not** — the writer's projection drops it
(`measure_conformance.py:626-631`). That is a writer defect, recorded, and
**775 scored rows are not backfilled after the fact.**

### What is served, and what is not claimed

**No conformance rate exists anywhere.** A raw-text search of
`conformance_run.json` finds zero `rate` keys outside the controls'
own `flip_rate` / `guarded_rate` / `guard_blind_rate`. The artifact publishes
a sentence instead of a rate:

> 3,298 statements were tested at their admitted points and not falsified,
> out of 4,287 samplable-and-schema-covered statements at M = 1000. **THIS
> CERTIFIES NOTHING UNIVERSALLY.**

**Demonstrate.** The route serves, and it serves the void with it:

```
$ echo "conform leanworkbook.skel.lean_workbook_10012 a=2 b=2" | python scripts/harness.py
  statement  : leanworkbook.skel.lean_workbook_10012
  verdict    : NO_COUNTEREXAMPLE_FOUND
  domain     : Nat, / is truncating, - is truncated-at-zero
  certifies  : tested at 37 admitted points and not falsified; this certifies
               nothing universally and is not evidence the statement is true
  points     : 37 admitted of 1000 sampled (159 guard-rejected, 804 outside the
               carrier, 0 errored)
  run void   : VOID — C-E1 missed its floor; every NO_COUNTEREXAMPLE_FOUND is void
```

A ground statement decides: `conform leanworkbook.ground.lean_workbook_plus_16115`
returns `DECIDED_FALSE` with `left : 0` and `right : 1`. An unrecognised
binding is **named, not dropped**: adding `qqq=3` appends
`ignored    : qqq — not a free variable of this statement`.

**One honest limit on that demonstration, stated because the line invites the
wrong reading.** The bindings are parsed today only to report ignored names —
`run(program, schema.digest)` never receives them, and `a=2 b=2` produces
byte-identical output to the bare line. **The route tests the sampler's
points, not the asker's numbers.** That is a real gap between what the design
wants and what shipped, and it is named here rather than left for a reader to
discover.

**And NIHIL's number is the one most likely to be misquoted, so it is written
the artifact's way.** E4 certifies a **procedure** — 110 of 110 on a
**constructed** decidable class, keyed independently of the procedure (the
with-root half built by factoring, the without-root half resting on the
rational root theorem). Its **corpus reach is not claimed**: the three corpus
statements in that shape all carry `sqrt`, a call head outside the evaluator,
so none is compiled by this cycle's machinery. **No corpus-coverage number is
quoted for NIHIL anywhere in this cycle, because the honest one is zero.**

## What changed, per area

### §4 — one witness retirement carrying five named changes

The batching rule from [ROADMAP-v0.20](ROADMAP-v0.20.md) §4: witnessed-module
changes that are individually small ride **one** retirement per cycle,
because the seal discipline prices a retirement and not a diff. What a batch
owes in exchange is that **each change carries its own before/after
evidence** — a shared seal is not a shared measurement. All five do.

**The successor book, verified structurally rather than by eye.** `git diff
--numstat v0.19.0..HEAD -- experiments/throughput_tasks.json` reads **3 3**,
and all three changed lines sit inside `rendering_module_digests`:
`scripts/answer.py`, `scripts/evaluate.py`, `scripts/harness.py`. **All 119
task records are byte-identical**, the kind/half split reproduces (94
answerable, A=45, B=49), and `half_b_seal` is unchanged — so the successor
book asks the same questions of the same halves. Three witnessed modules
moved, not five, exactly as §4's table predicted. `match_signatures.py`,
`external_verifier.py` and `serve_chat.py` are **not** witnessed and pay no
seal, which is why 4b and 4d owe served-line diffs instead.

#### 4a — the ownership receipt, and a claim measured after three cycles

**Before.** `_route_ownership` ran the expensive lookup, returned only the
rendered string, and the HTTP skin ran the identical lookup a second time to
cite the host set — mitigated with an `lru_cache`. The cost had been quoted
across three release cycles as *"~3.4 s"* **with no timing artifact behind
it**.

**Now.** The route returns the object in the verdict dict, matching what
`_route_twin` and `_route_reachable` already do, and the cache is dropped.

**Demonstrate.** `experiments/ownership_receipt_timing.json`:
**7,208.8 ms → 3,901.5 ms median on distinct queries, 1.85×**, 3,307 ms
removed per turn, with `answer_unchanged` and `receipt_unchanged` both true.

**And the honest number is published beside it, because the obvious
measurement measures the wrong thing.** Run exactly as §4a specified — the
same query ten times — the reading is **3,531.2 → 3,450.6 ms, 1.02×**,
because repeating one query warms the very memo the fix removes. The artifact
says in its own words that this is **not a performance claim** and that a
worse number would have been published too. What it closes is an
**unmeasured** entry, which is a different thing from a speedup.

#### 4b — exact integer literals

**Before.** `match_signatures.Parser` stored numeric literals as `float`, so
every literal wider than a double's significand was destroyed **at parse
time**. `lean_workbook_37421`'s served value agreed with the truth for 17
characters and then diverged by **4.4 × 10⁵⁹**, handed back as an `exact`
`Fraction` so nothing downstream could tell.

**Now.** Exact integers through the parse path. `lean_workbook_37421`'s
**76-digit** literal prints exactly.

**Demonstrate.** `experiments/exact_literals_served_diff.json`: **0 of 14,830
answer lines moved**; **3 evaluate-route renderings moved**, all three
expected and named
(`goedelpset.skel.goedel_pset_789185`,
`leanworkbook.ground.lean_workbook_37421`,
`leanworkbook.ground.lean_workbook_plus_68304`); `lines_moved.unexpected` is
empty; skeletons and shape keys **0 moved of 25,554** terms.

**Two things filed rather than smuggled.** Decimals stay `float`: making them
`Fraction` was tried first and the served diff **refused it**, because 199
statements lost their `in words` line — `number_to_words` accepts int and
float and rejects a `Fraction` as *"not a number"*. So `float("0.1")` is
still not one tenth, and that is a filed defect rather than a quiet one. And
**the three repaired nodes are not the three the backlog entry listed**:
`lean_workbook_50397` cannot be repaired by a parser change at all — its
`inf` is frozen into the committed template by the seed script — so it is
**filed open as a seed regeneration**, and `goedel_pset_789185` took its
place.

#### 4c — a power too wide to render refuses by name

**Before.** `evaluate.py` computed `base ** int(exponent)` with no bound on a
served path, and the failure mode was an **uncaught `ValueError` at print
time**. A served path whose refusal is an uncaught exception is not refusing.

**Now.** `evaluate.MAX_RESULT_DIGITS = 4300` with a typed
`evaluate.ResourceBound` refusal — and the check sits at the
**result-formatting boundary** (`Evaluation.formatted`, `Verification._fmt`),
not on the `^` node.

**Why it moved, which is the interesting part.** The first fix bounded the
operator, and the adversarial review escaped it in one line:
`(10 ^ 4000) * (10 ^ 4000)`. Two admissible powers, multiplied — nothing
exceeded a per-node bound, the value built, and the **print** raised the same
uncaught error the fix existed to abolish. **A bound on one operator is a
bound on one operator.** The per-node check is kept and is not redundant: it
refuses `2^200000` before the power is built, so an unrenderable request costs
a comparison instead of the arithmetic. One refuses early; the other refuses
always.

**Demonstrate.** `experiments/exponent_bound.json`, with both sides executed
in **child interpreters rooted at their own git worktrees** (the writer
refuses to record a comparison whose two sides loaded the same file):
**crashed while printing — before: 3 of 6 cases; after: 0.** The escape case
is in the case list permanently, so a future per-node-only bound cannot pass
this artifact again. **One divergence disclosed rather than quietly taken:**
`(100+1)^1000` at 2,005 digits is **still served**, contrary to §4c's landing
note. Four untimed `subprocess.run` calls in `external_verifier.py` were
given timeouts in the same change.

#### 4d — the foreign voice, wired dark and armed by evidence

**Before.** No foreign line existed on any surface, and the capability sheet's
`foreign_voice_row` had **no code path that set `served: true` at all**.

**Now.** One line in `answer.render` that **arms itself from the registered
artifact**: with `foreign_voice_rate2.json` absent or its blocking controls
voided, it emits nothing.

**Demonstrate — the absent/absent half first.**
`experiments/foreign_voice_wiring_served_diff.json` is the **batch-time**
artifact and reads `armed: false` on both sides, reason *"no registered run
at experiments/foreign_voice_rate2.json"*, with **0 of 14,830 answer lines
moved** and `in words` present on 9,721 statements on both sides. That is not
a null result: it is the proof that a witnessed-module change moved **no
served byte**. The run landed afterwards, at `2f882f0`, and the surface moved
with the evidence rather than with a second commit.

**The present side, discharged at this rotation.** The committed
`foreign_voice_wiring_served_diff.json` was regenerated on the armed tree:
`armed: true` on both sides, **0 of 14,830 answer lines moved**, `in words`
on **12,689** statements both sides — the surface is stable at its armed
state. The **transition itself** was measured once and is reproducible
rather than committed, because the artifact's schema was built to prove
the dark state and marks *any* movement STOP:
`python scripts/foreign_voice_wiring_served_diff.py --before 8e1a3d1`
(the commit v0.20 opened at) reads **2,968 statements' answers moved,
`in words` 9,721 → 12,689, armed false → true** — the in-words count rose
by exactly the moved count, which is the arming event and nothing else.
Beside it, `foreign_voice_arming.arming_state()` reports `armed: true`,
`verdict: FIRES`, all five blocking checks true, `non_blocking_voids:
["C-V3′"]`; **`tests/test_answers.py` asserts the served line appears
exactly when the arming read says it should** — replacing a test that had
hard-coded *"the repository as it stands is dark"*, which was true the day
it was written and would have gone **red for the system working**.

Four defects in the first version of that row were fixed before it shipped: a
valid-JSON-wrong-shape artifact raised `AttributeError` out of **a served
path** (four of five malformed shapes, measured); the armed branch had **no
test because nothing could reach it**; three sheet tests asserted "dark
today"; and `BLOCKING_CHECKS` wrote `C-V4'` with an ASCII apostrophe while
every artifact writes `C-V4′` (U+2032) — so **a real C-V4′ void would have
failed to match and been published as non-blocking beside an armed surface**.

#### 4e — `_route_conform`, landing refused

**Before.** A `conform` line fell through to the dispatcher and exhausted.

**Now.** A registered route that **refuses by name** until its compiler
exists, so item 1's slice never had to reopen the seal to add it.

**Demonstrate.** `experiments/conform_route_before_after.json`: two `conform`
lines move from `dispatcher / exhausted` to `conform / refused`; four control
lines are unchanged. It was wired live later, at `4506f83`, which **did**
move `harness.py`'s rendered bytes and rebuilt the witness book — one leaf,
119 task records byte-identical, `half_b_seal` unchanged. The design's §8.1
kept saying *"this slice does not seal its own witness book"* for a day after
the commit disclosed that it had; §8.1 now carries the dated amendment.
**No throughput claim is unlocked by any of this** — a timed comparison still
starts a fresh seal cycle.

### Three adversarial reviews, and what each one cost

| lane | Critical | what it found |
|---|---|---|
| **voice** | **none** | Independently re-derived the C-V4 id pins, the 4,191-statement residue, the B0d seed pin, the lexicon rows and the 85-unchanged claim — **all exact.** What it found instead was a *class*: **gates true in substance, enforced by assertions that could not have gone red** |
| **§4 batch** | **one** | A **vacuous seed-pin test** that compared the working tree against itself — and would have been **the sole merge conflict between the two lanes**. Fixed by **reverting** to the other lane's working instrument. Plus two real crash bugs: an uncaught `OverflowError` on a served route, and 4c's print-time blowup |
| **conform** | **one** | The **C-E3 misattribution** — 25 rows filed as a measured carrier boundary when they were an instrument gap. **Corrected in the record without re-running anything** |

**The governance finding of the cycle, and it is the one worth carrying
forward: assertions written so they cannot go red.** Not one wrong digest was
found in either review. What was found was:

- a gate (`G5b`) computing its own evidence from a **dict literal keyed by
  class name**, so *"no cross-kind record"* would have read true whatever the
  mutations actually touched — and a cross-kind record is the one thing G5b
  exists to find. The real data was already there and was being discarded;
- a test that read a file **at HEAD** and compared it to the same file in a
  clean worktree — a file compared to itself;
- a freeze list whose **prose** carried a reader's full authority while
  machine-checking exactly one field;
- a test asserting *"the repository as it stands is dark"*;
- a claimed derivation (`G3`) **enforced by nobody**: the replay script
  refused on the branch tip and no collected test ever performed the replay,
  so the strongest claim in the pin file rested on a program that could not
  run.

Every one is now falsifiable — the H2 "85 unchanged" check is **proven** red
by perturbing one of the 85, and git being unreadable is a **failure** rather
than a `skipTest`. **A green assertion that could not have gone red is not
evidence**, and ROADMAP-v0.21 §2 turns it into a gate clause.

### Integration: three post-merge failures, each meaningful

Merging the two lanes produced three reds, all adjudicated rather than
silenced:

1. **A one-hop pin walk against a two-hop chain.** The lexicon's B7 sweep
   walked **one** amendment hop while §4b made the parser's retirement a
   **two-hop chain** (realization → transliteration → exact literals). The
   sweep now uses `scripts/prereg_pins.check_frozen`, the shared **transitive
   walk** the batch built for exactly this, so a change past the *last*
   amendment still goes red.
2. **A real undeclared drift, caught by that same sweep.** 4c had moved
   `scripts/external_verifier.py`'s timeouts and **no preregistration recorded
   it.** Now recorded as a **dated amendment**, honest about being
   retrospective by one step — no run was open against the pin, so the window
   for a silent drift was empty.
3. **A hard-coded dark test**, re-aimed at consistency (above).

## Discoveries of the cycle

Quoted from [DISCOVERIES](DISCOVERIES.md); linked rather than duplicated:

- *"A control whose floor no correct instrument could meet."* C-E1 froze a
  99% flip floor for mutations that, over the declared `Nat` carrier, some
  classes cannot make false at all — with `lean_workbook_10087` in the same
  twelve as a genuine sampler miss, and the partition between them
  **unmeasured**.
- *"The declared domain spends the budget before the guard sees it."* Of
  691,000 candidate points offered to the coupled guards in the pilot,
  **539,382 — 78% — were consumed by the declared carrier before any
  statement's guard was consulted.**
- *"A restored clause moved the denominator, not the numerator."* v0.19's
  `drop_ascription` 0.90 was five fake mutations, not five missed near-misses.
- *"A green assertion that could not have gone red is not evidence."* The
  cycle's recurring catch, across two independent reviews and one merge —
  zero wrong digests found, five checks incapable of failing.

## Resolved from BACKLOG

- **`_route_ownership`'s receipt duplication — CLOSED.** Third-cycle friction,
  decided rather than carried a fourth time, and it landed with the
  **before/after timing artifact** the entry had owed for three cycles. The
  entry's own sentence — *"per a source comment, not a committed timing
  artifact"* — was **false after the landing and was replaced rather than left
  standing**.
- **The C-V4 mis-specification — CLOSED by C-V4′**, which holds in every
  voiding class with its discards counted.
- **`shift_group`'s artifact defect — CLOSED by re-measurement** under a new
  preregistration, exactly as the entry's own trigger specified.
- **The grouping-canonical question — CLOSED as asked**, and it is worth
  noting *how*: the probe published its distribution **before** any rule was
  proposed, and the census that followed turned a sampled question into an
  exhaustive one.
- **The capability sheet's `foreign_voice` row — CLOSED**, and it landed
  twice; the second landing found three defects in the first.
- **`_route_conform` — CLOSED against both conditions**, with the half of its
  own title that did not survive recorded rather than dropped: it was filed as
  *"item 1 must not reopen the seal to use it"*, and item 1 **did** reopen the
  seal, for the timing reason above. Closing an entry by discharging its
  conditions while ignoring the prediction it also made is how a backlog
  becomes a list of things that all worked out.
- **4b and 4c — CLOSED with corrections to their own numbers**, including the
  node list 4b's entry had wrong.
- **Newly filed**: the C-E3 substitution gap (debt for WITNESS's cycle);
  E5 and C-E1's stability arm as unrun registered work; the
  `lean_workbook_50397` seed regeneration; the `Fraction`-for-decimals
  refusal; and this course's seven new parks with their probes.

## Honest limits carried forward

- **No conformance rate exists, and `NO_COUNTEREXAMPLE_FOUND` certifies
  nothing universally.** The run is VOID by its own control's sentence, and
  the route publishes that void on every served answer.
- **The conform route does not evaluate the bindings a person types.** They
  are parsed only to name the ones the statement does not carry.
- **C-E1's 0.650 cannot be attributed.** Some of it is a floor no correct
  instrument could meet; some of it is real sampler misses; **this run has no
  instrument that partitions the two.**
- **C-E3 did not measure the carrier boundary.** It measured an instrument
  gap, and the ground half's 12 of 15 is the only part that stands.
- **E5 and C-E1's second arm are UNRUN**, so **this artifact has no
  byte-reproduction proof** and no sentence may call it reproduced.
- **The reader claims are not made — neither of them.** C-V3′ (machine)
  **VOID**; C-V3 (human) **ABSENT**. Nothing here says a *person* can recover
  the mathematics from the English, and the machine number is never quoted as
  a reader number.
- **C-G1's 1.00 travels with 42/50 = 0.84** and is never presented as the same
  quantity as v0.19's 0.80.
- **The ten named cases are 7 detected and 3 no-longer-admitting**, never "all
  ten detected".
- **Canonical grouping cost C-V1 reach** — the share of its misses that
  exercise the gate fell 42.5% → 22.4%.
- **Whether canonical bracketing helps or hurts a human reader is not
  answered**, and only C-V3 could answer it. One sealed surface canonicalizes
  to four disjuncts with no grouping word anywhere.
- **The committed run artifact carries two stale sentence strings** beside
  correct measured numbers (B3's *"close at 10,605 exactly"* and G4's echo of
  it). The **numbers** are what the gate was adjudicated on, and the artifact
  was **not edited**, because a note inside it would have destroyed the
  byte-identity that is the reproduction proof. Neither sentence is quoted
  anywhere in this document.
- **The census's 620 figure is *redundant or stripped*** — 604 redundant
  grouping pairs plus 16 binder-group pairs stripped. It is not 620 redundant.
- **This is still a `lean_workbook` rate**: 99.9% of the covered 2,313.
- **`K = 220×` is v0.17's number and stays v0.17's.** No throughput readout
  ran this cycle; the witness book was rebuilt for a digest leaf and nothing
  was measured through it.
- A passing Python test is not a Lean proof.

## Drift audit

*(RELEASE-v0.18.0, RELEASE-v0.19.0, ROADMAP-v0.18 and ROADMAP-v0.19 re-read in
full, per the rule. **No product-surface attrition this rotation** — both
skins carry the new work: `conform` is live on the typed line and over HTTP
with a `conformance` sheet row, and the foreign `in words` line is armed and
served. But the audit found six things, and four of them are genuine drift.)*

### The standing lanes, named again rather than allowed to erode

- **The cost ledger — FIFTH cycle parked, and the sentence is the same one.**
  `DESIGN-grounded-throughput` §10 named it **first** of two successors to a
  fired T4; the maintainer's directive took the other. Since then: *"unpark
  needs a metrology this cycle has not designed"* (v0.18), *"a metrology no
  cycle has designed"* (v0.19), *"…and that sentence has now been true for
  four rotations"* (v0.20). It is now true for **five**. The streak is the
  finding, not the sentence: a lane that has survived five rotations on an
  unchanged reason is either genuinely blocked or quietly abandoned, and the
  only thing distinguishing them is that somebody keeps writing it down.
- **Ledger-first claims — fifth pass-over, and the trigger did not fire.** Its
  unpark rule makes it a headline candidate the first cycle after a throughput
  readout. **v0.20 produced no new throughput readout.**
  `experiments/throughput_tasks.json` moved three times, but every change is
  inside `rendering_module_digests` — three digest leaves — and **no
  `throughput_result*.json`, `throughput_trial_*.json` or
  `throughput_baseline.json` changed at all.** Those are seal rebuilds, not
  measurements. **The trigger is not met, and saying so is the point of
  writing it down.**
- **Open-English input — parked, and the park is converging rather than
  eroding.** v0.18's follow-on asked whether the committed realization lexicon
  can run backwards as `DESIGN-text-resolution` §4's synonym layer. That is
  the same territory [DESIGN-plain-input](DESIGN-plain-input.md) approaches
  from the other side — and the plain-input seed **names the parked synonym
  layer as the residue its proposer is aimed at**, and records the lineage
  rather than hiding it. The convergence is worth stating precisely: the
  proposer is a **different mechanism**, so the reverse-lexicon question
  itself is still an unanswered park, and ROADMAP-v0.21 §3.3 keeps it as one.
- **The register's `mathlib_head` budget — carried, and verified intact.**
  `data/foreign_voice/register.json` changed only five provenance lines this
  cycle: `blocked_set_digest` is still `e51e5675…`, `blocked_total` still
  1,878, `mathlib_head` still 1,706. The two buckets never merged.

### Four things that drifted, named rather than left absent

1. **The ledger-first trigger's article changed from *the* to *a*, in a row
   that says the rule is unchanged.** v0.17, v0.18 and v0.19 all wrote *"the
   first cycle after **the** throughput readout"* — a definite, one-shot event
   that fired at v0.17, making every cycle since a pass-over.
   ROADMAP-v0.20 §5 rewrote it as *"**a** throughput readout"*, which converts
   an **overdue** trigger into one that cannot come due until a fresh
   throughput run happens — in the same row that calls the rule *"intact and
   **not** weakened by repetition."* **Both readings are stated here because
   they differ**: under the original wording this is the **fifth consecutive
   pass-over**; under v0.20's wording the trigger never came due.
   ROADMAP-v0.21 records this as **an amendment, dated**, rather than letting
   a one-word edit ride as an unchanged rule.
2. **"Load-bearing / premise-necessity" fell out of the carried table at the
   v0.19 rotation and landed nowhere.** It was a named row in ROADMAP-v0.17 §3
   and ROADMAP-v0.18 §3 (*"parked, travels with it"*). It is **absent by name
   from ROADMAP-v0.19 §4, from ROADMAP-v0.20 §5, and from BACKLOG.** It
   survives only inside `DESIGN-ledger-first-claims.md`, which calls it that
   lane's *"own most likely successor"*. **Recovered**: filed in BACKLOG with
   its trigger and named in ROADMAP-v0.21 §3.3 as travelling with ledger-first.
3. **"Realization parameters as data" had its unpark condition satisfied two
   cycles ago and the roadmaps stopped quoting the condition.** ROADMAP-v0.18
   parked it with *"becomes askable only if R1 fires."* **R1 fired at 0.9991**
   in the same release. ROADMAP-v0.19 restated the park **without the trigger
   sentence**; ROADMAP-v0.20 folded it into a catch-all row reading only
   *"unchanged"*. A trigger that fired and was then dropped from the record is
   the exact shape this audit exists to catch. **Recovered**: the condition is
   quoted again in ROADMAP-v0.21 §3.3, with the honest note that *askable* is
   not *scheduled*.
4. **Licensed variant generation lost its named dependant while staying
   "carried".** ROADMAP-v0.19 §4 named one — *"item 2 of any future cycle that
   wants a ranker"*. ROADMAP-v0.20 §5 says **none**, and carries it anyway.
   That is precisely the shape the carried-lane rule exists to catch: *an item
   carried a second time with no named dependant.* **Resolved by parking it**
   in ROADMAP-v0.21 §3.3 with its trigger — and with the one genuinely new
   fact recorded beside it: `DESIGN-plain-input` argues that **the input side
   is where the ranker seat finally has a denominator**, because a plain
   utterance licenses several candidate queries by construction. That is a
   *candidate* dependant, not a commitment.

### Two gate obligations this rotation found half-discharged

5. **The v0.19 course's two accepted riders were scheduled in writing and
   produced nothing.** ROADMAP-v0.20 §3 listed the **HOLES counting table**
   (*"revive-or-close FOUNDRY with a number"*) and the **delete-K ground-truth
   table** *"so they are **scheduled** rather than remembered."* Neither
   produced an artifact, neither is in BACKLOG, and neither appears in the
   v0.21 receipt. They were remembered, not scheduled. **Both carry forward in
   ROADMAP-v0.21 §3.5 with a stop rule**: unrun at the v0.22 rotation, a rider
   stops being a rider and either becomes an item or parks.
6. **4d's served diff was half-produced, and the record said it was
   complete — found by this audit, discharged before the tag.**
   ROADMAP-v0.20 §4d and the release gate both require the
   **absent/absent-then-present** diff. The absent/absent half was committed
   and correct, but `experiments/foreign_voice_wiring_served_diff.json` was
   written at **batch time**, still read `armed: false`, and was **stale
   against its own tree** — the run had landed afterwards, and the BACKLOG
   entry had closed citing the first half without noting the second was
   owed. Discharged at this rotation: the artifact is regenerated on the
   armed tree (`armed: true` both sides, 0 moved, `in words` 12,689 both
   sides), and the transition reading — **2,968 answers moved, 9,721 →
   12,689, armed false → true** against the cycle's opening commit — is
   recorded in the wiring section above with its reproduce command, kept
   out of the committed artifact because that schema deliberately marks
   any movement STOP (it exists to prove the dark state).

**And one more, which is a finding rather than drift.** The reader-determinacy
question is now empty on **both** sides — C-V3 (human) **ABSENT** for a second
cycle, C-V3′ (machine) **VOID** — and it appeared in no carried table and no
BACKLOG entry. It has one now (ROADMAP-v0.21 §3.3). A question that is
measured-negative for a machine and never attempted for a human is not
answered; it is unowned, and this release gives it an owner.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.**

`git diff --name-only v0.19.0..HEAD -- data/ experiments/` lists **twenty-nine
paths and not one `.py`**. `data/` **did** move this cycle — `data/domains/`
was added (the conformance domain schema and NIHIL's constructed class) and
five `data/foreign_voice/` artifacts were added or amended — so the question
Rule 2 asks was checked rather than assumed: **does any `experiments/` script
a checkpoint depends on read those directories?** It does not.
`grep -rln "data/domains\|data/foreign_voice" experiments/*.py` returns
nothing, and **no `experiments/*.py` file changed at all** this cycle. The
v0.6.0 training lanes generate their own data inside `experiments/` and never
read `data/`.

So **the checkpoints attached to [v0.6.0](RELEASE-v0.6.0.md) remain accurate
for this release**, and re-uploading identical bytes under a new tag would
cost upload time to say nothing new. Every measurement ledger is committed
in-repo at `experiments/*.json` and linked by path above rather than
duplicated as an asset.

## The next direction, chosen before this document

The outside design inquiry was **invoked** again — the **third consecutive
strict invocation**. Three isolated series, three rounds each: **nine rounds,
fifteen round-one directions, $2.41**, run headless from an empty non-git
directory outside the repository under a strict tool denylist, with session
ids and per-round prompt hashes committed in
`reports/design-direction-v0.21.json` and the brief on file and hash-verified.
The receipt carries one piece of self-checking worth keeping: `series_1.r1`
**equals** the brief hash **by construction**, because round one of series one
*is* the brief — *"the equality is the checkable form of that sentence."*

**Selected: `docs/DESIGN-session-ledger.md`** — the session as a first-class
object: a committed, replayable per-turn journal whose answers **cite the
assumptions they consumed**.

**And the incumbent was adjudicated explicitly, which ROADMAP-v0.20 §5
required in writing.** [DESIGN-plain-input](DESIGN-plain-input.md) — the
maintainer-seeded candidate for *plain conversation, in plain text* — is
**ADOPTED**, and the two documents ship as **one lane** in
[ROADMAP-v0.21](ROADMAP-v0.21.md) §1. The evidence for the adjudication is in
the receipt rather than in a preference: series 1 folded its prose-ambiguity
direction into **two probe artifacts for the incumbent**, and series 2's
round-one text named the incumbent's gap — *"a conditional answer's condition
lives in the person's head, not in any artifact; there is no object called the
session, so nothing about continuity can go red"* — **before the incumbent
was disclosed to it at round two.** Silence was not a disposition, and it was
not used as one.

**Adopted second: WITNESS** → ROADMAP-v0.21 §2, the conformance void's
claim-kind successor, with its preregistration draft recorded **in the
receipt** rather than invented afterwards. **EXHIBIT** was declined in writing
by its own series *because it builds on the layer whose conformance run
voided*, and its revival condition is exactly WITNESS shipping non-void.
ATLAS, DEMAND, ABSENCE, RATCHET, GRAFT, IF and TRANSPLANT park with their
probes and triggers; RECALL folded into the twice-parked withdrawal lane,
donating one clause to its trigger — *an over-broad impact set counts as
failure, not caution.*

### The design's own first draft failed its review, and that is worth a paragraph

`DESIGN-session-ledger`'s first draft claimed **no committed object for
continuity existed** — in a repository holding a recorded end-to-end session
artifact, a durable signed session with **keyed MACs per binding**, and a v0.10
adjudication (`P5`) that byte-exact session re-run had been asked for once and
came back **MISSED IN KIND**. The review caught it, and the committed version
stands on those precedents **by name**: replay is P5's *corrected* guarantee —
*re-verifying the record* — scoped to non-mutating sessions; integrity reuses
the committed `session_keys` MAC ring the first draft had unknowingly argued
against; and the corpus seal steals `throughput_tasks.json`'s A/B half device
so the citer cannot author its own denominator.

The discipline this repository applies to its measurements applies to the
orchestrator that plans them. A design that does not know its own history
proposes work that has already been done, or re-proposes work that has already
failed — and the only defence is the same one every run gets: an adversarial
reader who checks the claim against the tree.

## The release refresh

`[SUITE-GATE-V20]` covers the full-suite verdict; the generated-state chain is
reported here.

- `check_regeneration.py` — **25 seeds regenerate committed data
  byte-identically** across `data/`, `data_holdout/`
- `validate_nodes.py` — **12,777 statement nodes across 27 corpora**
- `signature_matches` and `compression` regenerated identically except their
  own churn
- `ingest_wold.py reach` — **95.5%** re-verified

**`check_report_regeneration.py` has not run in this rotation**, and the
release gate requires its verdicts in these notes. It runs with the full-suite
gate on the frozen tip, and its three verdicts land in this section then —
with `decompositions.json`'s **declared** divergence carrying its TRIAGE-v0.11
citation, as in the last three cycles. Saying "not yet" is the point: a
refresh step reported without its exit status is a step nobody checked, which
is a lesson this repository filed at the v0.19 rotation and does not get to
forget at the v0.20 one.

## The suite at the tip

Two runs, both retained in `reports/test_gate_v020/`, and the red one is
part of the record:

| run | tip | result |
|---|---|---|
| 1 | `e3ed3b5` | **2,326 ran, FAILED (failures=3, skipped=5), 21,715.8 s (6 h 02 m)** |
| 2 | `3dc26d0` | **2,326 ran, OK (skipped=5), 21,828.9 s (6 h 04 m)** |

**All three run-1 failures were the exact-literals change reaching code the
batch never listed.** Two were one pin: the convention census's provenance
digest for `reports/signature_matches.json`, which legitimately moved when
4b changed the parser the report records — regenerated with **exactly one
leaf differing** and every census number byte-identical (the v0.16
`ambiguity_rate` precedent: numbers identical, pins moved, adjudicated).
The third was real: `analogygen.serialize` floated every numeral before
emitting, so the 76-digit exact literal 4b taught the parser to keep came
back as `4.444e+75` — a different term. The serializer now emits exact
ints as `str(int)` (every curated spelling unchanged) and the split
deserializer mirrors it; the failing suite test is the regression test.
The batch had verified its change against every numeral surface it knew —
25,554 skeletons, 14,830 answer lines — and the suite found the one
serializer nobody named. **A targeted suite proves the surfaces you
listed; the full gate proves the ones you forgot.**

Run 2, at the fixed tip with the maintainer's governance relaxations
(ROADMAP-v0.21 §4.0) in the tree: **2,326 tests, 0 failures, 5 skips**,
up from v0.19.0's 2,106 by the cycle's **seven** wholly new modules —
`test_conform`, `test_conform_prereg`, `test_conform_register`,
`test_cv4_replay`, `test_grouping_agreement`, `test_grouping_canonical`,
`test_machine_reader` — and growth in thirteen existing ones. The five
skips are the standing set. Slowest single test remains
`test_corpus_analogy_split`'s blind control (~4,181 s), as measured and
expected.

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/check_report_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py

# On Windows every command below needs PYTHONIOENCODING=utf-8: these scripts
# print the glyphs this cycle is about, and cp1252 turns that into a
# UnicodeEncodeError and exit 1 -- which reads like a refusal and is not one.

# 1. the foreign voice, served -- a statement v0.18's realizer refuses
PYTHONIOENCODING=utf-8 python scripts/answer.py leanworkbook.skel.lean_workbook_7992

# 2. why that line is allowed to appear: the arming read, from the artifact
PYTHONIOENCODING=utf-8 python -c "import sys; sys.path.insert(0,'scripts'); \
    import foreign_voice_arming as a; s=a.arming_state('.'); \
    print(s['armed'], s['verdict'], s['non_blocking_voids'])"

# 3. the run's own verdict, read straight off the registered artifact
#    -> FIRES ['C-V3′'] []      (the voided control is the machine reader)
PYTHONIOENCODING=utf-8 python -c "import json; v=json.load(open('experiments/foreign_voice_rate2.json',encoding='utf-8'))['verdicts']; \
    print(v['overall'], v['voided'], v['missed'])"

# 4. the repair number that is commensurable with v0.19's 0.80, and C-G1's
#    two admissible denominators printed together, as the prereg requires
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('experiments/foreign_voice_rate2.json',encoding='utf-8')); \
    g=d['c_v4_prime']['per_class']['drop_group']; print('drop_group',g['detected'],'of',g['scored'],'floor',g['floor']); \
    a=d['c_g1']['aggregate']; print('C-G1',a['detected'],'of',a['scored'],'=',a['rate'],'-- and',a['detected'],'of 50 =',round(a['detected']/50,2))"

# 5. the exhaustive grouping census -- 5,228 of 5,228, zero blind
PYTHONIOENCODING=utf-8 python -c "import json; g=json.load(open('experiments/grouping_agreement.json',encoding='utf-8')); \
    print(g['g1']['agree'],'of',g['g1']['floor'],'agree,',len(g['g1']['disagreements']),'disagreements'); \
    print(g['g1b']['detected'],'of',g['g1b']['pairs_tested'],'detected,',g['g1b']['blind'],'blind')"

# 6. a statement that runs -- and the void it is served under
#    (the harness prints its liveness list first, then the typed line)
echo "conform leanworkbook.skel.lean_workbook_10012" | PYTHONIOENCODING=utf-8 python scripts/harness.py

# 7. the conformance run's verdict, and the sentence it publishes instead of a rate
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('experiments/conformance_run.json',encoding='utf-8')); \
    print(d['verdicts']['overall']); print(d['e2']['the_sentence_not_a_rate'])"

# 8. the section-4 batch, three readings that each need both halves
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('experiments/ownership_receipt_timing.json',encoding='utf-8')); \
    print('4a distinct queries:', d['distinct']['delta']['speedup'], 'x'); \
    print('4a same query x10 :', d['repeat']['delta']['speedup'], 'x  <- the honest arm, published beside it')"
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('experiments/exact_literals_served_diff.json',encoding='utf-8')); \
    print('4b answer lines moved:', d['answer_lines_moved']['count'], 'of', d['statements_rendered']); \
    print('4b evaluate route moved:', d['evaluate_route_moved']['count'], '-- all expected')"
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('experiments/exponent_bound.json',encoding='utf-8'))['crashed_while_printing']; \
    print('4c crashed while printing -- before:', len(d['before']), 'after:', len(d['after']))"
```

Reproducing the foreign-voice run additionally requires the pinned Lean
toolchain (`leanprover/lean4:v4.32.2`); without it the oracle refuses rather
than downloading anything, and publishes no partial rate. Reproducing C-V3′
additionally requires the pinned local model, and refuses — never
downloads — when the weights are absent or their digest mismatches.

**One command in [RELEASE-v0.19.0](RELEASE-v0.19.0.md)'s reproduce block is
now superseded, and this is the notice.** That block's step 3 reads
`experiments/foreign_voice_rate.json`, which is v0.19's **VOID** artifact and
stays committed exactly as it read. This cycle's run is a **different number
over a different grammar**, in `foreign_voice_rate2.json`, and the two are
never blended. v0.19's numbers are not restated anywhere in this document.
