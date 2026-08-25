# Roadmap v0.20 — the headline is pending; the debts are not

v0.19 was the cycle where three of four readouts made the claims smaller.
The foreign voice's registered run fired every gate and then **voided on
its own near-miss control**, so the line it certified is not served. The
address-space probe **lost to its blind baseline on both retrieval legs**
and parked with the numbers. The convention census found **zero**
mathematical convention forks and retired the direction that wanted them.
Only the transliteration lane grew anything: **two glyphs took the native
voice from 17.0% to 67.2%**.

That leaves this cycle with an unusually well-specified inbox. Two of the
carried lanes below are not vague deferrals — they are **named successors
to a void**, with the work they owe already written down by the run that
voided.

## 1. Headline — statements that decide themselves (EVAL)

The outside design inquiry ran and reported: three isolated series, three
rounds each, **nine rounds** and **fifteen** round-one directions for
**$3.12**, receipt in `reports/design-direction-v0.20.json` (brief
`11c676b6…`). Finalists: **VERDICT** (series 1), **EVAL** (series 2),
**WORD OF HONOR** (series 3).

**Selected: `series 2 lead: EVAL -> docs/DESIGN-statements-that-run.md`** —
*statements that decide themselves*, with NIHIL's grounded negatives folded
in as a second answer type rather than carried as a rival. The receipt puts
the candidate population at **~12,700 decidable candidates** and names the
residual the design has to answer for: **correlated interpretation**.

> **Status note (2026-08-24, at rotation).** `DESIGN-statements-that-run.md`
> landed on disk during this rotation and is **awaiting adversarial
> review**; it carries `Status: design only`. Its preregistration order,
> gate clauses and controls are quoted into this roadmap once that review
> closes, so that what lands here is the reviewed text rather than the
> draft — the E0 / E0e references in §4 below are the two the batched
> re-seal is scheduled against and are named by the orchestrator's ruling,
> not lifted from an unreviewed section. Every sentence in this
> section that describes the *design* rather than the *course receipt* is
> therefore provisional and may move with a dated correction — the same
> convention ROADMAP-v0.19 used for DESIGN-foreign-voice, and for the same
> reason. The course facts above are quoted from the committed receipt and
> are not provisional.

**The lineage note, which is the part worth reading twice.** EVAL is
**RUNNABLE returned**. The receipt says it plainly:

> EVAL is RUNNABLE returned: proposed in the v0.19 course (series 1) and
> DROPPED at its round two; it returns on new evidence — the C-V4 void
> proved the error class an evaluator catches is invisible to every
> structural gate, and both cost discounts (exact rational arithmetic; the
> external-verifier lane) are measured facts. A dropped direction returning
> with new evidence is the funnel working, recorded as such.

That is this cycle's governance result as much as its direction. A funnel
that only ever discards is a filter; a funnel that lets a direction back in
**when the evidence changes, and says which evidence** is doing the job it
exists for. The evidence in question is v0.19's own void: an evaluator
catches exactly the error class that a structural gate — including the one
that voided last cycle — cannot see. The two cost discounts are measured
facts rather than hopes, which is why the return is admissible.

**What the brief carried**, so the selection could not be a ratification of
the flattering half: the transliteration result (17.0% → 67.2%, one corpus,
two call heads), **the foreign-voice VOID with its mechanism** — not the
1.0 the void makes unquotable — the address-space park with its 1-of-3, and
the convention-census negative. Three of those four took something away.

### 1.1 Readout (2026-08-25) — the run is VOID, and that is the result

`DESIGN-statements-that-run.md` shipped through its registered run,
`experiments/conformance_run.json`, executed once on a committed tree. The
preregistration order held **with one slip, which the slip's own commit
confesses**: §4's batched item, then the design, then the domain schema with
E7's frozen digests, then the frozen register, then `conform.py`, then E0f's
pilot and its dated amendment freezing E2a, then the run, then the wiring —
except that **E4's instance list was not frozen in the preregistration commit
the design requires**. It landed in its own commit, `43061e2`, still before
`conform.py` scored a single E4 instance and before any E4 number existed, and
that commit records the slip in its message rather than presenting the order
as clean. Naming it here too, because an order that "held" in one document and
is confessed in another is not a record a reader can use.

The class's `instance_set_digest` is now **recomputable rather than
asserted**: `tests/test_conform.py::TheE4InstanceSetDigestIsRecomputable`
rebuilds it from the committed coefficient lists. Before that test the writer
copied the key verbatim (`measure_conformance.py:686`) and nothing in the tree
could have detected a list edited after the freeze.

**Overall: VOID.** C-E1's own sentence governs — every
`NO_COUNTEREXAMPLE_FOUND` in the run is void — so the lane's headline number
is withdrawn by its own control before anyone quotes it.

- **Met:** E2a (96.0% of 4,287 admit a point, floor 80%), E3 (closes at
  12,777 exactly), E4 (110 of 110), C-E4 (nothing was measured through a
  moved instrument).
- **Missed:** E1 — 25 refusals in a ground class the design predicted would
  have none, decomposing into 13 `negation_outside_carrier`, 8 truncating
  division-by-zero and 4 `evaluation_budget_exceeded`. All three are
  consequences of the *declared domain*, which is what the floor existed to
  detect.
- **Void:** C-E1 (0.650 against 0.99) and C-E2 (1.75x against 10x).
- **Unrun (a gap, not a void):** **E5**, the two-run byte-identity arm, and
  **C-E1's second arm**, the false-alarm half (*0 of N unmutated statements
  may change verdict across two runs*). Both were registered in §6/§7 and
  neither was executed. A void is a control that ran and failed its own
  condition; these have no voiding sentence to fire and are evidence in
  neither direction. The consequence to keep in front: **this artifact has no
  byte-reproduction proof**, so no sentence may call it reproduced. Filed in
  `docs/BACKLOG.md` for the rotation rather than executed after the fact.

**775 counterexamples, none published as a corpus error.** §3.5's clause 1
was written before the run for exactly this: zero were independently
adjudicated.

> **Corrected 2026-08-25, after adversarial review.** The two numbers this
> paragraph used to lean on do not say what they were read as saying, and the
> corrections are recorded in the run artifact's dated `post_run_corrections`
> block and recomputed from its own rows by `tests/test_conform.py`.
>
> - **"Zero adjudicated" stands; its reason changes.** C-E3 attempted **25**
>   sampled counterexamples (not 27 — two ground `DECIDED_FALSE` ids carry a
>   `skel.` prefix and were mis-sorted), and every one failed because
>   `measure_conformance.py:709-717` handed Lean the **raw universally
>   quantified statement with its free variables unbound** instead of the
>   instantiated counterexample. That is an elaboration failure on an open
>   term — an **instrument gap** — and **not** Correction 7's carrier
>   boundary, which this cycle did not measure. C-E3's 12 confirmations
>   (of 15, not of 13) stand: ground statements have no free variables.
> - **"46.2% admitted a single point" was read backwards.**
>   `conform.py:497` breaks on the first counterexample, so
>   `points_admitted` counts admitted points *up to and including the
>   falsifying one*. `admitted == 1` means the **first** point falsified the
>   statement — the sampler's best case. The number measures how early
>   falsification happened, not how thin the sampling was. The thin-sampling
>   finding is real and rests on E0f's pilot, not on these counts.
> - **"33.2% turn on a value clamped to zero"** is `left == "0"` (257/775);
>   the falsifying-side-zero figure is 278/775 = **35.9%**.
> - **The label is on the verdicts, not on the artifact's rows.** Every
>   NONCONFORMANT verdict carries the correlated-interpretation label at
>   runtime and on the served answer; the 775 rows in the artifact omit it,
>   because the writer's projection drops it. A writer defect, recorded — 775
>   scored rows are not backfilled after the fact.
> - Also corrected: C-E1 scores an **errored** mutant point as a flip, a bias
>   *toward* the floor it missed anyway; its `per_class` table has four rows
>   of a five-class generator, and the never-fired fifth class is the one
>   whose mutants would have been discarded; and C-E2's "both arms over the
>   identical admitted point set" is false of the code, which drops the guard
>   and so admits a strict superset on the blind arm.
>
> Nothing was re-run. §8's no-chase rule governs: a measurement is not
> re-executed to make a record come out better, so the record moved instead.

**The two transferable findings** are in `docs/DISCOVERIES.md`: a control
whose floor no correct instrument could meet, and a declared domain that
spends 78% of the sampling budget before any guard is consulted.

**What is now live:** `conform <statement-id> <bindings>` on both skins,
`tool.conform` registering through a committed-artifact probe, and a
`conformance` sheet row that publishes the verdict vocabulary, the
denominators and the run's own VOID — and no rate, by design.

## 2. The C-V4 successor, and the wiring gated behind it

This is the cycle's most concrete debt, and it comes with its
specification already written.

> **Status note (2026-08-24, after rotation).** This lane now has a design:
> [DESIGN-voice-completion](DESIGN-voice-completion.md), which landed and was
> adversarially reviewed during this rotation and carries
> `Status: design only`. It is **maintainer-directed**, and the directive is
> quoted rather than summarised — the ruling of **2026-08-24** is that *the
> withheld foreign voice **ships in v0.20***. A second directive of the same
> date adds **C-V3′, the machine blind reader**, whose cross-design definition
> was written down in [DESIGN-plain-input](DESIGN-plain-input.md) §6 and which
> that seed explicitly hands to **this** lane's run: *"it belongs to the voice
> design's run, not to this one"*.
>
> **What the directive does and does not do.** It chooses which of two honest
> repairs the cycle takes — canonical-grouping rendering over accepting the
> measured blind spot as a permanent non-claim — and it **does not adjudicate
> the control**. The design says so in the plain form this roadmap should
> inherit: *if the fresh run voids again, the voice stays withheld and v0.21
> inherits it.* The gate below is unchanged by the directive.
>
> **What moved in the design that this section predates.** Its review turned
> the grouping-canonical question from §3's probe into a **census** — every
> grouping-pair deletion over every canonical surface, floor 5,228 of 5,228 —
> which **demotes C-V4′'s `drop_group` to a confirmation** rather than
> replacing it. And the sample pins moved: three of the five C-V4 pools change
> with the grammar, so the drawn **id lists** are pinned rather than the seed.
> Every sentence in this section describing the *design* rather than the
> *v0.19 record* is therefore superseded by that document where the two
> differ, on the same convention §1 uses for DESIGN-statements-that-run.

**What went wrong, precisely.** C-V4 inherited C-R2's mutation idea and
left behind C-R2's load-bearing clause: **every mutation is verified to
change the term *before* it is rendered**, with non-mutations discarded and
the discards counted (v0.18 discarded 31 that way). C-V4 mutates the
rendered English and requires the elaborated digest to move — but it never
establishes that the mutation *should* have moved it. So an unknown share
of its `did_not_differ` cases may be mutations that changed nothing about
the term at all, and `drop_group`'s 0.80 is measured against a denominator
that has not been cleaned.

**C-V4′ — the re-specified control.** Same five classes, plus the missing
clause: construct each mutation, elaborate the mutated *term* first,
discard any mutation whose term did not change, count the discards, and
only then score the surviving set against the per-class floors. It is a
**new preregistration with its own frozen digests**, and it is explicitly
**not a re-score of v0.19's run** — that artifact is committed as it read
and stays that way.

**The wiring is gated behind it, and the gate is not negotiable.** The
foreign `in words` line ships **only** if C-V4′ clears its floors. If
C-V4′ voids again, the line stays unwired and the register stays the
product — and that second void would be a much more interesting finding
than the first, because it would mean the blind spot is a property of
elaboration-as-identity rather than of one control's specification.

**Both branches are results.** A cleared C-V4′ ships a voice; a voided
C-V4′ publishes a bound on what digest-identity can certify at all.
Neither outcome permits quoting B1's 1.0 without its history.

## 3. The grouping-canonical question the void raised

`drop_group` voids because **deleting a semantically redundant bracket
changes the sentence and not the term**. Sitting underneath that is a
question nobody has asked this repository: *should the renderer emit a
canonical bracketing at all?*

Two readings, and they want different work:

- **The rendering is over-parenthesised.** If the grammar emits grouping
  words a reader does not need and the term does not require, then
  `drop_group` is detecting a real redundancy in the *surface*, and the fix
  is a minimal-bracketing rule with its own round-trip proof — the same
  shape v0.18's five-level ladder already uses on the native path.
- **The redundancy is load-bearing for a reader.** A bracket that
  elaboration erases may still be what makes an English sentence readable
  aloud, in which case removing it makes the surface worse and the control
  is measuring something the design should keep.

**These are not the same repair and the cycle must not guess.** The honest
first step is a measurement, not a change: over the covered set, count how
many grouping words the grammar emits that the term does not require, and
publish the distribution before anyone proposes a rule. Registered as a
probe rather than an item — both branches yield an artifact.

### The course's two accepted riders

The v0.20 receipt accepted exactly two riders, and they are cheap by
construction. Both are listed here so they are scheduled rather than
remembered:

- **The HOLES counting table** (an afternoon). HOLES folded out of series 1
  as *"a counting-table free rider"* whose job is to **revive-or-close
  FOUNDRY with a number** — machine-enumerated skeleton gaps, counted.
  Either the count supports reviving conjecture-foundry work or it closes
  it, and both are results.
- **The delete-K ground-truth table.** Survives from series 3's ONE HOP,
  which the receipt records as *"surrendered to the prior course's excluded
  substitution chains"* — the direction went, the table stayed.

Neither is a headline and neither should grow into one; a rider that starts
asking for a design is a rider that has become an item and needs to say so.

### Named standalone probes inherited from the parked list

Cheap, pre-registered, both branches yield an artifact — the same rule §3a
and §3b ran under last cycle. Any of these may ride this cycle or a later
one; none is scheduled here, and that is the point of naming them:

- **VERDICT's week-one warrant census** — how much negation and
  mutual-exclusivity the corpus carries. The answer bounds whether a
  claim-adjudication layer has a denominator at all.
- **DEBT NOTES' one-day hand-classification probe** — the receipt's
  strongest product-resonance note attached to the cheapest test in the
  list.
- **COURIER's one-day probe** — are quotation and evaluation receipts
  already near-detached? If yes, a detached-receipt layer is mostly
  bookkeeping rather than a build.
- **WORD OF HONOR's extraction-discipline census** — named in the receipt
  as an optional rider **any cycle can run**, which is how a parked
  thesis-level candidate keeps a pulse without becoming a headline.

## 4. One witness retirement, five named changes — and it lands before item 1

> **Dated correction (2026-08-24, after both design reviews closed).** This
> section was written as *"one witness retirement, three fixes"*. Two more
> witnessed-module changes were scheduled after it was written — **4d**, the
> foreign-voice wiring from [DESIGN-voice-completion](DESIGN-voice-completion.md)
> §5.1, and **4e**, `_route_conform` from
> [DESIGN-statements-that-run](DESIGN-statements-that-run.md) §5 — and both
> ride this retirement rather than opening their own. The batching rule below
> is what forces that, so the numeral is corrected here and everywhere it
> appears rather than left to read as a third count. **The retirement is still
> ONE; only the number of changes it carries moved.**

**This section is one commit's worth of witness retirement carrying five
named changes, and it is ordered BEFORE item 1's first slice.** All five
touch `harness.py`, `answer.py` or the evaluate path — modules the task book
witnesses — so done separately they would cost five retirements and five
successor books. Batched, they cost **one**. The design requires the ordering
independently: an evaluator that decides statements cannot be built on a
parser that destroys their literals, so E0's exact-literal prerequisite has
to be true before item 1 has anything sound to stand on.

**Three witnessed modules move, not five.** `harness.py` (4a, 4e),
`evaluate.py` (4c) and `answer.py` (4d) are on the witness list;
`match_signatures.py` (4b), `external_verifier.py` (4c's timeouts) and
`serve_chat.py` (4d's sheet row) are **not**
(`tests/test_throughput_tasks.py:52–66`, tied to the book at `:532`). The
unwitnessed ones pay no seal and owe a **served-answer-line diff** instead —
the discipline `docs/DESIGN-foreign-voice.md` §5 already named, with
`scripts/transliteration_served_diff.py` as the working precedent.

| # | change | module | witnessed? | why it is in this batch |
|---|---|---|---|---|
| 4a | `_route_ownership` returns its receipt in the verdict dict | `harness.py` | yes | third-cycle friction; the land-or-close clause discharged by a landing plan |
| 4b | **exact literals** — the parser stops storing numerals as `float` | `match_signatures.py` | no | **E0's prerequisite.** 7 destroyed literal occurrences across 3 nodes; two served statements print values wrong by 4.4 × 10^59 while looking exact |
| 4c | **a resource bound on `^`, refusing by name** | `evaluate.py` / `external_verifier.py` | yes / no | **E0e.** `base ** int(exponent)` is unbounded on a served path, and its current failure mode is an uncaught `ValueError` at print time rather than a refusal |
| 4d | **the foreign `in words` line, the sheet row, and the b0d seed-pin test** | `answer.py` / `serve_chat.py` | yes / no | **DESIGN-voice-completion §5.1.** The line arms itself from the registered artifact, so the code lands with the batch and the surface moves only when the evidence says so |
| 4e | **`_route_conform`** | `harness.py` | yes | **DESIGN-statements-that-run §5.** Its own slice states the dependency: the route rides this retirement rather than opening one |

**Batching rule, stated so a later cycle inherits it rather than
rediscovers it:** witnessed-module changes that are individually small
should ride **one** retirement per cycle. The seal discipline prices a
retirement, not a diff, so five separate small commits pay five times for
the same thing. What the batch owes in exchange is that each change carries
its **own** before/after evidence — a shared seal is not a shared excuse
for a shared measurement. **This batch grew from three changes to five
without growing its retirement, which is the rule working rather than the
rule bending.**

Third-cycle friction opened this section, and this rotation **decides it
rather than carrying it again**. The v0.18 note said a third cycle without
either the fix or a written decision to stop caring is the shape BACKLOG
exists to catch; the orchestrator's ruling (2026-08-24) is **SCHEDULED**,
and this is the landing plan that discharges the land-or-close clause.

### 4a — `_route_ownership` returns its receipt

**The defect.** `_route_ownership` runs the expensive `ownership.lookup`,
renders it, and returns only the rendered string — so
`serve_chat._ownership_receipt` must run the identical lookup a second time
to cite the host set. The skin mitigates with an `lru_cache` on the pure
function rather than monkeypatching the engine, which would be the renderer
editing the record.

**The fix, and it is a convention alignment rather than an invention.**
Have `_route_ownership` return the answer object (or its host set) in the
verdict dict alongside `"answer": render(answer)`, **matching what
`_route_twin` and `_route_reachable` already do**, and drop the cache. The
shape exists in the tree; this route is the one that does not follow it.

**What it owes, in order:**

- a **before/after measurement** — the entry has been quoted across three
  release cycles at `~3.4 s` with **no timing artifact behind it**, so the
  fix publishes a real one or the claim it repairs is retired unmeasured;
- its **new-seal cost, paid under the standing witness rule** —
  `harness.py` is a witnessed rendering module, so the commit retires the
  current witness for future comparisons and seals a successor book, dated
  reason in the commit, prior artifact untouched. Two cycles have made that
  procedure routine (v0.18 retired v0.17's witness; v0.19's transliteration
  lane retired two parser pins), so the cost is known and small;
- **early placement**, because it is small and because a fourth cycle of
  carrying it is the outcome this ruling exists to prevent.

**Not a performance claim.** The measurement is published to close an
unmeasured entry, not to headline a speedup — and per the standing rule, a
rendering-adjacent change starts a fresh seal rather than inheriting an old
run's numbers.

### 4b — exact literals (DESIGN-statements-that-run E0's prerequisite)

`match_signatures.Parser` stores numeric literals as `float`
(`scripts/match_signatures.py:412`), so every literal wider than a double's
significand is destroyed **at parse time**, before any consumer sees it.
Measured: **7 destroyed occurrences across 3 nodes** (5 distinct values —
4 lossy, 1 overflowing to `inf` on a 421-digit literal). Two ground-class
statements return the **right verdict with wrong printed values**;
`lean_workbook_37421`'s served value agrees with the truth for 17
characters and then diverges, an absolute error of **4.4 × 10^59**, handed
back as an `exact` `Fraction` so nothing downstream can tell.

The repository already knows the right shape of the answer: **the same two
statements are refused honestly** by v0.18's registered numeral pair
(`|n| < 10^15`) as `unsupported_numeral`. One subsystem refuses; the other
silently corrupts. That asymmetry is the argument.

**Owes:** exact integer literals through the parse path; the two affected
served statements shown right before and wrong after in the commit; and a
statement of what the evaluate path does at the boundary the numeral pair
refuses at — refuse by name, not print an approximation.

### 4c — a resource bound on `^`, refusing by name (E0e)

`scripts/evaluate.py:182` computes `base ** int(exponent)` with **no
bound**, reachable from the typed line (`harness.py:1799`, `:1813`) and
over HTTP. `(100+1)^1000` yields 2,005 digits in under a millisecond;
`2^200000` computes. The current failure mode is the one worth fixing
deliberately: the computation succeeds and the **printing** raises an
uncaught `ValueError` (Python caps int→str at 4,300 digits). **A served
path whose refusal is an uncaught exception is not refusing.**

**Owes:** a registered bound with a **typed refusal** — the same
refuse-by-name discipline R3 and the numeral pair already use — plus the
four untimed `subprocess.run` calls in `scripts/external_verifier.py`
(lines 279, 287, 425, 462; `grep -c timeout` returns **0**) given timeouts,
since that file carries the external-verifier lane the design's cost
argument rests on.

### 4d — the foreign voice wiring (DESIGN-voice-completion §5.1)

**The change.** One new line in `answer.render` — `in words   : <surface>`
for the foreign path, beside v0.18's — plus the `foreign_voice` sheet row
flipping to `served: true`, and the `tests/test_foreign_voice_b0d.py`
amendment that reads the seed pin as a git-derived value rather than a
transcribed constant.

**Why it can land before the run that authorises it.** The line **arms itself
from the registered artifact**: with `experiments/foreign_voice_rate2.json`
absent or voided it emits nothing. So the code moves once, with this batch,
and the surface moves later — or never — without a second commit. The
precedent is `realization_row` (`scripts/serve_chat.py:363–408`), which reads
the registered run and publishes `served: false` with a reason when the
artifact is unreadable. What is genuinely new is named rather than smuggled:
**4d adds `answer.py`'s first read of an `experiments/` artifact**, since
`_in_words` gates on its own round trip and not on a run file.

**A pre-existing defect 4d must fix, and it is a silent corruption rather
than a crash.** `foreign_voice_row` reads `c_v4["voided_classes"][0]`
(`scripts/serve_chat.py:455`) on a list that is **empty** when nothing voided.
The `except` tuple at `:459` **catches** `IndexError`, so an all-clear run is
not a traceback — it is published with the same *"its record could not be
read"* prose as a corrupt or missing file, on exactly the branch the voice
design exists to produce. Worse, the row has **no code path that sets
`served: true` at all** (`row["served"]` is assigned `False` once, at `:438`),
and it keys off `c_v4["voided_classes"]` rather than the run's own
`verdicts["voided"]`. **Neither `foreign_voice_row` nor `realization_row` is
covered by any test.** 4d writes the true branch, corrects the field, and adds
the both-branch test.

**Owes:** the **absent/absent-then-present served diff** — the foreign line
shown **absent on both sides at batch time**, because no run has armed it yet,
and **present only after the clean run lands**. The absent/absent half is not
a null result; it is the proof that a witnessed-module change moved no served
byte, which is exactly what the seal discipline asks a witnessed change to
demonstrate.

### 4e — `_route_conform` (DESIGN-statements-that-run §5)

**The change.** One new route in `scripts/harness.py`, beside the existing
`_route_evaluate` and following its shape exactly, returning `None` on a
refusal so the line falls through the chain rather than refusing on everyone
else's behalf.

**Why it is here rather than in item 1's slice.** Its own design says so:
the route, the exact-numeral path and the resource bound *"all ride §4's
retirement rather than opening one"*, and that slice **depends** on this
section landing first. Listing it here is what makes that dependency a
schedule rather than an intention.

**Owes:** its own before/after evidence, on the same rule as every other
member of this batch — one seal is not one measurement.

**Both 4b and 4c are display-and-liveness fixes on a loopback-only,
single-user server, and neither is a security claim.** They are scheduled
because item 1 needs them true, and because HOSTILE DICTATION is parked
with a trigger that fires **before** any untrusted stream reaches these
paths (§5) — not because anything untrusted reaches them today.

## 5. Carried, with dependants named

| lane | named dependant | disposition |
|---|---|---|
| **C-V4′ and the foreign wiring** | **§2 — this cycle** | not carried, **scheduled**; it is the named successor to a void and the run that voided wrote its specification. **Designed at [DESIGN-voice-completion](DESIGN-voice-completion.md)** (maintainer-directed, 2026-08-24; §2's status note); its wiring rides §4 as **4d** |
| **The grouping-canonical question** | §3's probe | registered probe; measure before repairing. **The probe kept its ordering and the repair now has a design** — [DESIGN-voice-completion](DESIGN-voice-completion.md) §6 publishes the census *before* proposing the rule, and its G1b turns the question into an exhaustive gate rather than a sample |
| **[DESIGN-plain-input](DESIGN-plain-input.md)** — plain text in, propose-and-verify, hidden variables named | **the v0.21 course** | **maintainer-seeded candidate, pre-course** (2026-08-24). Not scheduled this cycle and not parked: it is the **named candidate the v0.21 course must adjudicate explicitly** — adopted, superseded by something measurably better-fitting, or parked with the measurement that parked it. **Silence is not a disposition.** Its §6 also carries the cross-design **machine blind reader** definition, which it hands to §2's run rather than keeping |
| **The register's `mathlib_head` budget** | *none* | carried. 1,706 of the 1,878 blocked statements are blocked by a **budget a maintainer can lift**, not by a design limit. It is filed rather than scheduled because lifting it is a resourcing decision, and the register's whole point is that the two buckets never merge into one "unsupported" number |
| **Licensed variant generation** | *none* | carried unchanged from v0.19 §4: the realization grammar emits exactly one surface per term, so the learned preference seat has nothing to rank. Unpark when a design says what licenses a *second* passing surface and why that is not decoration |
| **`_route_ownership` receipt duplication** | **§4 — this cycle** | not carried, **SCHEDULED** by the orchestrator's ruling of 2026-08-24. The land-or-close clause is discharged by a landing plan rather than by a fourth pass; §4 carries the fix, the before/after measurement the entry has owed for three cycles, and its new-seal cost |
| Ledger-first claims (v0.17 course lead, gate L1–L13, hardened) | *none* | **parked, rule intact, fourth pass-over.** Design, gate and receipt stay preregistration-ready. Its standing unpark rule is unchanged and is **not** weakened by repetition: it becomes a headline candidate the first cycle after a throughput readout, and its mid-cycle lift trigger — a release quoting a number its artifact no longer supports — stands. Recorded again rather than allowed to fade |
| The cost ledger (answers per joule and per dollar) | *none* | **parked, fourth cycle, still owed.** DESIGN-grounded-throughput §10 named it *first* among two successors. Unpark still needs a metrology no cycle has designed, and that sentence has now been true for four rotations — which is itself worth noticing |
| Open-English **input** | *none* | parked. v0.18's follow-on stands: can the committed realization lexicon run backwards as the synonym layer DESIGN-text-resolution §4 names? A design, not a patch |
| **STRANGER** — outside-asker gap-object intake | *none* | parked in BACKLOG with its degradation rule quoted. Unpark needs a population of askers this repository did not author — the same fresh-half problem the veto census hit |
| **TWO RIGHTS**, full direction | *none* | **parked with an empty mathematical denominator**, by its own B0. The 125 notational candidates remain as a census a future direction inherits, and the two halves of that reading must never be quoted apart |
| DESIGN-block-vocabulary | *none* | **park complete.** Adopted → built → measured → parked by numbers (§3e). The one surviving untested property, append-only path-independent growth, is named there for any future unpark |
| FORK, TWO-STEP, DEADLINE, THE GRADED NO | *none* | parked with the triggers recorded in `reports/design-direction-v0.19.json` |
| **WORD OF HONOR** — the attested layer, parameterize-never-unlock | *none* | **parked as the strongest thesis-level candidate**, and parked for a *shape* reason rather than a merit one: its first slice is seed-reading, which is **instrument-shaped**, and the governance record counsels against an instrument as a headline. Its **extraction-discipline census is named as an optional rider any cycle can run**. This is the one park in the list where the receipt says the direction is stronger than the thing that beat it, so it does not quietly decay |
| **VERDICT** — entailed / contradicted / not-grounded over third-party claims | *none* | parked; its **week-one warrant census** — how much negation and mutual-exclusivity the corpus actually carries — is **named as a cheap standalone probe** and is listed in §3 below |
| **DEBT NOTES** — refusals naming their repair, flip-on-write replayed | *none* | parked **with the strongest product-resonance note** in the receipt, and its **one-day hand-classification probe** named; the receipt calls it a natural companion to any future intake lane |
| **HOSTILE DICTATION** — red-teaming the write gate | *none* | parked **with a named trigger, and it is the one trigger in this table that is a prohibition**: it **MUST run before any untrusted stream reaches the write gate**. Nothing this cycle opens such a stream; if a later cycle does, this unparks first, not alongside |
| **COURIER** — DETACHED RECEIPT narrowed to quotation + evaluation classes | *none* | parked; quotation/evaluation receipts are **likely near-detached already**, so the probe is **one day and may ride any cycle** |
| **UNSAY** — withdrawal with computable blast radius over served receipts | *none* | parked; blast radius over served receipts is **mechanical now that receipts are served objects** — revisit **when withdrawal has a driver**. (Note the lineage: this is the voided v0.16 retraction radius returning on changed ground, and the advisors disclosed the collision themselves) |
| **BORROWED PREMISES** — conditional answers under quarantined assumption sets | *none* | parked; **likely the supposition frame's maturation** — noted for when the API attaches callers with real premise sets |
| **SECOND VOICE** — diagrams that re-parse, testing void transfer | *none* | parked; the **void-transfer question is well-formed** and waits on a committed picture syntax |
| Realization parameters as data; unless-receipts, detached receipt, residual ledger, antibody, two referees, wild text, negative space; resolver coverage lane, A3–A5, verified-ambiguity, range certification, W1–W3 | *none* | unchanged |

**The seeded candidate, recorded here so the v0.21 course cannot inherit it
as a rumour.** [DESIGN-plain-input](DESIGN-plain-input.md) was seeded by
maintainer direction during this rotation, with the direction quoted verbatim
in the document rather than paraphrased. It is **pre-course by construction**:
it does not compete for v0.20 and it is not parked, because a park needs a
measurement and none has been taken. The instruction it carries is the one
§6 records as fully discharged for the last seed — *"a park that cites a
measurement is a decision; a park that cites a preference is drift"* — and the
lifecycle that discharged it, **adopted → built → measured → parked by
numbers**, is the standard this one is owed too. The v0.21 course adjudicates
it **explicitly**, and **silence is not a disposition**.

## 6. Governance

- **The course gate was INVOKED strictly again — the second consecutive
  strict invocation, and the loop the v0.18 rotation opened is now closed
  twice over.** ROADMAP-v0.18 restored the release skill's strict wording
  (*invoked*, not reaffirmed) after v0.18 itself was cleared under a looser
  clause with the conflict recorded in the open, and wrote that the
  reaffirmation "was available once, recorded once, and is not available
  again by inheritance." v0.19 discharged the strict form on its first use
  (`reports/design-direction-v0.19.json`); **v0.20 has now discharged it
  again** (`reports/design-direction-v0.20.json`) — three isolated series,
  nine rounds, fifteen directions, $3.12, session ids and per-round prompt
  hashes committed, isolation mode inherited unchanged from the v0.19
  receipt. One strict cycle proves the wording can be met; two proves it is
  the practice rather than an exception, which is what the v0.18 ruling was
  betting on.
- **A dropped direction returned, and the funnel recorded why.** EVAL was
  proposed in the v0.19 course and dropped at its round two; it is this
  cycle's selection. The receipt's `lineage_note` names the evidence that
  changed — the C-V4 void, and two measured cost discounts — rather than
  letting a re-proposal pass as a fresh idea. **Re-entry is legitimate when
  it is evidenced and recorded; it is drift when it is neither**, and the
  distinction only exists because the funnel keeps receipts across cycles.
- **The advisors disclosed their own collisions, four times.** The receipt
  records HOLES vs CONJECTURE FOUNDRY, UNSAY vs the voided retraction
  radius, ONE HOP vs substitution chains, and NIHIL vs the grounded-negatives
  cut — *"four honest disclosures across three series"*. An isolated advisor
  flagging that its idea touches claimed ground is the isolation working
  without the isolation having to be perfect.
- **The no-silent-disposal instruction is fully discharged.** The
  maintainer seeded DESIGN-block-vocabulary; v0.19 adopted it bounded,
  built the probe, measured it against three of its own pre-registered
  baselines, and parked it **by numbers** in the design's own §3e. Adopted
  → built → measured → parked is the complete lifecycle, and it is worth
  recording as the pattern rather than as one item's outcome: a park that
  cites a measurement is a decision; a park that cites a preference is
  drift.
- **A voided control does not become a lesser control.** C-V4 voided this
  cycle's headline and stays in the gate. The successor in §2 exists
  because the control was **under**-specified, not because it was
  inconvenient, and the distinction is the whole reason §2 is a new
  preregistration rather than an edit.
- **Headline selection remains part of the evidence trail.** When the
  v0.20 course reports, its selection and every declined disposition are
  recorded here, in the receipt, and in the release notes.

## Release gate

v0.20 is ready only if:

- **EVAL ships its registered run** — `docs/DESIGN-statements-that-run.md`
  implemented in its own preregistration order, with its gates adjudicated
  and every control read out — **or stops on a named stop condition with
  the reading published**. A published stop is a result; a quiet descope is
  not. (The design is in draft with adversarial review to follow, so its
  gate clauses are named here once it is committed — this roadmap does not
  invent them in advance.) **Its first slice does not begin until §4 has
  landed**: E0's exact-literal prerequisite is not a nicety, and an
  evaluator built over a parser that destroys literals would be measuring
  its own substrate's defect;
- the design's named residual, **correlated interpretation**, is answered
  by a control rather than by prose, or the run says which part of its
  claim that residual bounds;
- **C-V4′ reads out** — a new preregistration with its own frozen digests,
  scored over a verified-to-change-the-term mutation set, with its discards
  counted; and **the foreign `in words` line ships only if C-V4′ clears**,
  with the register shipping either way;
- the grouping-canonical probe publishes its distribution, whichever way it
  reads, **before** any bracketing rule is proposed;
- **§4 lands FIRST, as one witness retirement carrying five named changes**
  (corrected 2026-08-24 from three; the retirement is still one), and
  before item 1's first slice: **4a** `_route_ownership` returns its
  receipt in the verdict dict (the convention `_route_twin` and
  `_route_reachable` already follow), cache dropped, with the
  **before/after timing artifact** the entry has owed for three cycles;
  **4b** exact literals through the parse path, with the two corrupted
  served statements shown right; **4c** a registered bound on `^` that
  **refuses by name rather than raising**, plus timeouts on the four
  untimed `subprocess.run` calls; **4d** the foreign `in words` line and
  its sheet row, arming themselves from the registered artifact, with the
  **absent/absent-then-present served diff** and the silent-corruption
  defect in `foreign_voice_row` fixed; **4e** `_route_conform`. Each
  change carries its own evidence — one seal is not one measurement;
- `check_report_regeneration.py` runs in the release refresh with its
  verdicts in the notes;
- the full suite is green on a frozen tip with retained receipts;
- every unfinished item ships or parks in writing;
- the outside design inquiry is **invoked** for v0.21 — the forge skill
  run, or a written course-gate amendment by the maintainer — with the
  receipt named, and the v0.21 brief carries this cycle's readouts
  including any void, not only the ones that grew a number.
