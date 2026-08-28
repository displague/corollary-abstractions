# v0.22.0 — two censuses, two findings: the library is nameless and its evidence is program-bound

This cycle scheduled two measurements and expected two capabilities. It got two
**findings** instead, and both are first-class results because both were
adjudicated against a stop clause frozen before the number was known.

- **The library is nameless.** Of 12,777 statements, **417 (3.26%)** carry a
  handle specific enough for a person to type and reach them by; the other
  **12,360** carry none. The design's stop clause fired, and firing it is the
  result: *the ingested library is effectively nameless; the naming layer must
  be built, not indexed.*
- **The evidence is program-bound.** Of 19 kinds of receipt this program emits,
  **1 survives** the program's deletion, **10 need the program** to re-check,
  and **8 could not be tested at all.** Offline-checkability is earned by naming
  an adjudicator that is not the program — not by carrying a digest of your own
  work.

And a third result runs under both, on the methodology the arc keeps sharpening:
**a removal arm that could not go red, caught by the program on itself.** The
evidence-survival census's first run rested on a step that failed identically
whether the program was present or absent; the corrected run makes the program
demonstrate, against itself, that the deletion is what broke the re-check. That
self-catch is the reason the honest number is 1-of-19 and not something rosier.

**Links** — previous release: [v0.21.0](RELEASE-v0.21.0.md) · closed plan:
[ROADMAP-v0.22](ROADMAP-v0.22.md) · next plan:
[ROADMAP-v0.23](ROADMAP-v0.23.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the library that had no names](blog/the-library-that-had-no-names.md)

## The headline finding: the library cannot be asked for what it can compute

**Before.** v0.21's plain-input proposer failed partly because the list-builder
it read from searched **titles and keywords only**
(`scripts/candidate_enumerator.py:166-168`). The design's own showcase question
enumerated **zero** candidates for a statement the library holds. The v0.22
design (`docs/DESIGN-handles.md`) proposed to reach statements by what they
*contain* and what mathematicians *call their parts* instead — and review found
the repository already holds two such non-title indices sitting unused one route
earlier on the same serving path. The open question was how much of the library
those indices can specifically name.

**Now.** H-P0's census answered it, and the answer fired the design's §9 stop
clause. The capability sentence does not ship; the census is the result.

| index (title-free) | statements it specifically names | share of 12,777 |
|---|---|---|
| **S-LEX** — per-node `symbol_lexicon` glossary | **263** | 2.06% |
| **S-INV** — call-head inventory over the parsed form | **306** | 2.39% |
| **typable union** (everything a person could plausibly type) | **417** | **3.26%** |
| **residue** — no specific handle from either | **12,360** | 96.74% |

The cause is measured, not inferred. **12,514 `lean_workbook` statements were
ingested in bulk and carry nine distinct glossary tokens between all of them —
and six of those nine each blanket more than 12,200 statements at once.** A
token that describes almost everything is exactly what the specificity bound
`K = 128` exists to exclude, so not one of the 12,514 has a specific S-LEX
handle. The 263 S-LEX names are exactly the 263 hand-curated statements.

**And no re-freeze of K rescues the bulk.** The census swept K and published the
plateau: the typable union sits at **417 for every K in [80, 218]**, and the
bulk's specific-S-LEX coverage stays **0** until K crosses 302, where it jumps
to **302 statements and caps there forever** (302 at K=302, at K=1024, at
K=4096). Three hundred and two rescuable names out of twelve and a half
thousand, at any setting. *You cannot tune your way to names that were never
written.*

**The cross-census sentence is the sharpest number the cycle produced.** Rider
R1's depth-1 census found **9,048** statements (70.8%) shaped so the engine
could consume them in one step. Overlay the two censuses: of those 9,048, only
**125** carry a specific typable handle
(`experiments/onestep_census.json`, `cross_census_reading`). The mass the
program can *work on* and the mass a person can *reach* are almost disjoint —
**the library can compute far more than anyone can name to ask for.**

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/handles_census.json',encoding='utf-8')); \
    u=d['union']; print('typable union', u['specific_handle_union_typable'], \
    '=', u['specific_handle_union_typable_pct'], '%'); \
    s=d['sources']; print('S-LEX', s['S-LEX']['coverage']['statements_with_specific_handle'], \
    'S-INV', s['S-INV']['coverage']['statements_with_specific_handle']); \
    p=d['k_sensitivity']['plateaus']['typable union']; \
    print('union invariant for K in', p['invariant_for_K_in'])"
typable union 417 = 3.2637 %
S-LEX 263 S-INV 306
union invariant for K in [80, 218]

$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/onestep_census.json',encoding='utf-8'))['cross_census_reading']; \
    print(d['with_a_specific_typable_handle'], 'of', d['one_step_consumable_strict'], \
    'one-step-consumable statements carry a specific handle')"
125 of 9048 one-step-consumable statements carry a specific handle
```

### The stop clause fired, and firing it is the finding

`DESIGN-handles` §9's clause is quoted because it is the item's outcome, not its
risk: *if the census reads specific-handle coverage near the review's indicative
~2%, the slice publishes the census as the headline — the ingested library is
effectively nameless; the naming layer must be built, not indexed — and the
capability sentence does not ship.*

The orchestrator's dated adjudication (`DESIGN-handles` §9 addendum, 2026-08-27;
`docs/ROADMAP-v0.22.md` §1 banner) fires it on **two independent grounds**:

1. **Cap-at-302.** Coverage read 3.26% — inside the clause's ambit — and cannot
   be rescued by any re-freeze of K, because the bulk caps at 302 forever.
2. **Population-consuming manifest.** Sealing Q60's 42 in-library targets
   against a 417-statement handle population would be a manifest consuming its
   own population — the same construction defect §4.0(3) exists to catch, and
   the same shape that stopped WITNESS at 60-of-66 last cycle.

So H-P1, H-P2, the handle table and the registered run **do not occur this
cycle**; the tree asserts their absence in tests. R1's lane-opening decision
goes to the rotation with its statement limb at **45× its floor** (9,048 against
a floor of 200) and its **question limb DEFERRED** — Q60 is unsealed, and
producing a number from unsealed drafts would be the sealed-after-the-fact
defect the discipline exists to prevent.

### The review reproduced every number, and caught two defects under the headline

The census was reproduced by hostile review to the digit — including **row-level
agreement on all 12,777 one-step classifications**. Two defects were caught and
fixed, and **no headline number moved** (commit `4447a7b`,
`experiments/handles_census.json`, `experiments/skeleton_index.json`):

- **A false writer attestation.** Both artifacts recorded a
  `provenance.writer_sha256_lf` for a version of the writer that no longer
  existed — the artifacts were generated, the writer was then edited (to fix a
  cold-start note, itself a repair of a sentence that could not go red), and
  neither was regenerated. *A provenance block that nothing scores is a block
  that nothing scores*, and every surrounding test stayed green.
- **A hash-seed tie-order defect underneath it.** Regenerating exposed that the
  `most_resolving` handle rankings ordered their ties by `PYTHONHASHSEED`: the
  lists reordered across seeds and at one seed a tied handle dropped off the
  list entirely. The artifact's own sentence *"Everything else recomputes
  byte-identical"* was false when written. Ties now break on the handle's own
  bytes — the rule `DESIGN-handles` §4 already freezes one layer up. No
  coverage number, distribution, quantile, corpus split or union moved.

## The second finding: does the program's evidence survive the program's deletion?

**Before.** The project publishes *receipts* — records asserting that a thing was
checked. Whether a receipt is portable — re-checkable by a stranger without the
program — had never been measured. It is the standing gap behind STRANGER,
C-V3 and every maintainer-authored denominator the project has published.

**Now.** COLD RECEIPT enumerated 19 receipt kinds and ran each through a harness
that deletes the program and asks whether the receipt can still be re-checked
(`docs/DESIGN-cold-receipt.md`; `cold/census_run2.json`).

| verdict | kinds | meaning |
|---|---|---|
| **SURVIVES** | **1** | re-checkable with the program tree gone |
| **NEEDS-PROGRAM** | **10** | re-check requires this repository's code (each with a succeeding with-program control *and* a failing program-absent limb) |
| **UNTESTED** | **8** | no re-check procedure could be executed |

All of **B1–B11 green**, the voiding sentence **not fired**, `R-C` licenses §13's
third partition: *the survival sentence, scoped to the named kinds, with the
NEEDS-PROGRAM kinds published by name* (`cold/result_gate_run2.json`).

**The one SURVIVES kind, and a stranger replicated it repo-free.** It is the
C-E3 raw-checker invocation
(`conformance_ce3_supplement:decide_both_directions`): its committed artifact
carries a probe template and a pinned checker digest — enough to rebuild the
check and hand it to an **external** proof assistant (`lean.exe`, a third party
the repository did not author). Review executed that path cold, with none of
this project's code present, and it held (`DESIGN-cold-receipt` §12, CR-P1;
`cold/evidence/recheck_good.json`: `PASS rows 25/25`).

**The verdict that flipped on the corrected arm is the lesson.** The most
self-describing receipt in the tree — `retraction_radius:certify`, which carries
its own `recheck_command` — reads **UNTESTED**. The rechecker it names,
`radius_recheck`, imports `jsonschema`, which nothing in the tree pins, so
`import radius_recheck` fails with the program **fully present**. Carrying your
own instructions is not the same as being checkable:
**offline-checkability is earned by naming an adjudicator that is not the
program, not by carrying digests.**

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('cold/census_run2.json',encoding='utf-8')); \
    print(d['counts']); print('voiding fired:', d['voiding_sentence']['fired'])"
{'kinds': 19, 'SURVIVES': 1, 'NEEDS-PROGRAM': 10, 'UNTESTED': 8}
voiding fired: False

$ PYTHONIOENCODING=utf-8 python -c "import json; \
    g=json.load(open('cold/result_gate_run2.json',encoding='utf-8')); \
    print('SURVIVES:', g['verdicts']['SURVIVES']); \
    print('R-C green:', g['R_C']['green'])"
SURVIVES: ['conformance_ce3_supplement:decide_both_directions']
R-C green: True
```

### The methodology headline: a removal arm that could not go red

**Before (run 1).** The first census (`cold/census.json`, retained) reported
**9 NEEDS-PROGRAM**. Its removal arm ran `python -S -I -c "import <module>"`,
and since Python 3.11 `-I` implies `-E` and `-P` — so `PYTHONPATH` was ignored
and the program tree was never on the child's path at all. The import failed
**identically** with `scripts/` present and absent. The arm could not go red for
the reason it claimed, and all nine `confirmed_by_removal` verdicts rested on
it. That is the arc's recurring shape — an assertion that cannot fail — arriving
inside the census built to price survival.

**Now (run 2).** Under ROADMAP-v0.21 §4.0(1)'s bug-not-result relaxation — *an
arm that never executed as designed is a bug, not a reading* — amendment 2
re-ran the census with **two limbs per kind**: a with-program **positive
control** that must SUCCEED, and the program-absent limb that must FAIL. A kind
that fails both ways reads UNTESTED with its true blocking dependency named
(`cold/census_run2.json`, `amendment`). The corrected reading is 1 / 10 / 8.

**And the registry half was corrected in the same amendment.** Run 1's instance
rule read `none` for **two kinds holding 160 and 2,313 committed instances**
(commit `d2ac619`); the fix is why the harness had real denominators to test.
Run 1's artifacts are retained unedited, both seals recorded.

**What the arms priced, each a number rather than an assertion:**

- **B6** — 200 scrambled bundles, 10,000 checker invocations, **0 passed**, in
  57 minutes against a 59-minute estimate (`cold/scramble_baseline.json`). The
  1.5% is published as a **rule-of-three upper bound**, never as a measured rate
  and never as though 0 were the finding.
- **B3 / B4 / B5** are green over a **one-kind denominator** — the single kind
  whose procedure executed program-absent — and say nothing about the other 18.
  B4's omission arm failed loud naming `lean.exe`; no SURVIVES rested on a
  `program_configured` dependency, so B11 downgraded nothing. Three census
  misses are published under B10.

## Roadmap triage

Every item of [ROADMAP-v0.22](ROADMAP-v0.22.md), with its outcome.

### Shipped

| item | outcome |
|---|---|
| **§1 HANDLES / H-P0** — the coverage census | **SHIPPED as its registered result: the census.** 417/12,777 typable specific handles; the §9 stop clause **adjudicated FIRED** on two grounds. The library is nameless; the naming layer must be built, not indexed |
| **§2 COLD RECEIPT** — the reviewed compact design | **SHIPPED**, before its slice, on the WITNESS ordering precedent (`docs/DESIGN-cold-receipt.md`) |
| **§2 COLD RECEIPT** — the evidence-survival census | **SHIPPED, then amended.** `cold/census_run2.json`: 1 SURVIVES / 10 NEEDS-PROGRAM / 8 UNTESTED; all B1–B11 green; R-C licenses the partition |
| **§3 R1 ONE STEP** — the depth-1 census | **SHIPPED.** 9,048 one-step-consumable (statement limb 45× its floor); the cross-census 125-of-9,048 reading is the cycle's sharpest sentence |
| **§3 R3 ERRATUM** — the flip probe | **SHIPPED.** 0 real flips over 410 replayed turns; plant detected 1/1; 0 statements added in the window |
| **§5.0 supplementary series** — the outside-family design series | **SHIPPED.** GPT-5.6-sol via codex, isolated, academic register; dispositions in `reports/design-direction-v0.22.json` `supplementary_series` |

### Shipped as a finding — first-class results

| item | outcome |
|---|---|
| **§1's capability sentence** | **NOT SHIPPED, by the stop clause.** No handle table, no Q60 seal, no registered run. The census is the deliverable, and it is a published stop, not a quiet descope |
| **R1's question limb** | **DEFERRED**, not estimated. Q60 is unsealed and this slice was forbidden to seal it; the lane-opening decision goes to the rotation |
| **The removal arm (run 1)** | **A methodology finding.** An arm that could not go red, caught by the two-limb correction — the program made to demonstrate against itself |

### Carried

Every carried lane is ordered before a named ROADMAP-v0.23 headline item (a
**prerequisite**) or **parked in BACKLOG with its reason**. The v0.22 successor
set is in [ROADMAP-v0.23](ROADMAP-v0.23.md); the parks are in
[BACKLOG](BACKLOG.md).

- **The naming-layer question** — *how does a nameless library get names a person
  can ask by?* — is the **NEW carried lane both censuses forced**, and it is the
  rotation's question, not this slice's assumption. Carried to the v0.23 course
  as a first-class lane; candidate material (name-derivation from the verified
  English renderings; S3's priced term store) named, not chosen.
- **TWO WITNESSES + the independent second reading** — parked item-candidates,
  together, unchanged.
- **CANARY-CURVE and TOLL** — v0.23 incumbent-candidates, and **TOLL's shift is
  named** (see the drift audit): the cost lane's named metrology now has a
  re-check-cost instrument in §2's harness.

## What changed, per area

### The three non-title indices, measured under title deletion for the first time

**Before.** The proposer path read `title` + `keywords` only; the resolver's two
non-title indices (`resolver.by_lexicon`, `resolver.inventory`) sat unused one
route earlier on the same serving path, never measured for coverage.

**Now.** H-P0 committed one artifact per source with the producer named and
title-freeness recorded (`experiments/handles_census.json`, `sources`): S-LEX
records on all 12,777 (`reads_title_or_keywords: false`); S-INV is recomputable
from `match_signatures.template_call_heads` and **committed here for the first
time**; S-SKEL is recomputable and its id→skeleton table committed
(`experiments/skeleton_index.json`) — *a skeleton string is nothing a person
types, and the census claims no human-question match for it.*

**Demonstrate.** The boilerplate finding, read off the artifact:

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    b=json.load(open('experiments/handles_census.json',encoding='utf-8'))['boilerplate_finding']; \
    print('bulk', b['bulk_statements'], 'distinct glossary tokens', \
    b['distinct_glossary_tokens_over_the_bulk'], 'name tokens', \
    b['distinct_name_tokens_over_the_bulk'], b['the_name_tokens'])"
bulk 12514 distinct glossary tokens 9 name tokens 1 ['equality']
```

### S3 term-serialization, priced but not taken

**Before.** The term store S3 would need does not exist: the pinned oracle keeps
only a `sha256` of each serialization (`scripts/foreign_voice.py:182-191`).

**Now.** H-P0 prices it rather than deferring it: **2,319 oracle-eligible, of
which 2,313 covered** (a subset, never summed with the eligible count), and a
**measured** runtime estimate. Building the term store for one term per covered
statement would cost **~223.5 s batched** (`handles_census.json`,
`s3_price.runtime_estimate.projected_seconds`; the `DESIGN-handles` §9 addendum
rounds this to ~217 s — see honest limits). The naming-layer
lane inherits this price as candidate material, not as a scheduled build.

### The evidence-survival harness, and what it can and cannot say

**Before.** No harness deleted the program and re-checked a receipt.

**Now.** `cold/` holds the census, the two-limb evidence, a path audit, a
200-bundle scramble baseline, and a reconstruction rule. The scope is stated in
the artifact: **B3/B4/B5 score over a one-kind denominator** and the partition,
not a rate, is the deliverable. **No reachability rate and no survival rate is
published anywhere** — the deliverable is the partition and its named kinds.

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('cold/census_run2.json',encoding='utf-8')); \
    b6=d['gate']['B6']; print('scramble bundles', b6['bundles'], 'passed', b6['passed'], \
    'rule-of-three upper bound', b6['rule_of_three_upper_bound'])"
scramble bundles 200 passed 0 rule-of-three upper bound 0.015
```

## Discoveries of the cycle

Quoted from [DISCOVERIES](DISCOVERIES.md); linked rather than duplicated:

- *"The ingested library is effectively nameless."* Of 12,777 statements, 417
  (3.26%) carry a specific typable handle, and no re-freeze of K rescues the
  bulk — it caps at 302 forever. The naming layer must be built, not indexed.
- *"The library can compute far more than anyone can name to ask for."* Of the
  9,048 one-step-consumable statements, 125 carry a specific handle. The
  computable mass and the reachable mass are almost disjoint.
- *"A receipt is cold-recheckable only when its adjudicator is not the program."*
  1 of 19 receipt kinds survives program deletion; the most self-describing
  receipt in the tree reads UNTESTED because the rechecker it names cannot run
  even with the program present.
- *"A confirmation that cannot go red is not a confirmation, and the first
  version of this entry claimed one."* Run 1's removal arm failed identically
  with the program present or absent; the two-limb correction makes the program
  demonstrate against itself that the deletion is what broke the re-check.

## Resolved from BACKLOG

- **The v0.21 enumerator's title-only haystack — MEASURED, not repaired.** The
  defect §1 existed to price is now quantified: the stronger indices reach only
  3.26% specifically, so wiring them in would not have rescued the intake
  ambition. Filed forward as the naming-layer question.
- **Newly filed**: the naming-layer question as a first-class carried lane; the
  cold-census's own next question (ORPHAN — which single pinned dependency
  converts the most NEEDS-PROGRAM kinds); the v0.23 course's parks
  (SELF-SEED, UPSTREAM-PATCH, HANDLEBAR, FOREIGN-SEAM's feasibility residue,
  STRANGER-GATE); and the two review defects (the false writer attestation and
  the hash-seed tie-order), both fixed with headline numbers unmoved.

## Honest limits carried forward

- **No capability sentence shipped for HANDLES.** The census is the result; the
  handle table, H-P1, H-P2 and Q60 do not exist and the tree asserts their
  absence.
- **No reachability rate and no survival rate exists anywhere.** Both censuses
  deliver a **partition**. "Reachable" is never claimed for the 125 — they
  **carry** handles; whether a handle reaches a statement in service is
  unmeasured, because no table and no question set was built.
- **Q60's authorship contamination is named and unpriced** — but Q60 was not
  sealed this cycle, so no maintainer-authored denominator was produced. No
  stranger-usability claim anywhere.
- **COLD RECEIPT's B3/B4/B5 speak for one kind.** The tamper, omission and sham
  arms ran over the single kind whose procedure executed program-absent; they
  say nothing about the other 18.
- **The one SURVIVES kind rests on an external checker.** It survives because it
  names an adjudicator the repository did not write; that is the point, and it
  is not a claim the *other* 18 could be made to survive.
- **The S3 price is a projection, not a build.** ~223.5 s batched is the
  census's own estimate over 2,313 covered statements; the two-terms-per-
  statement scope is published beside it and the two are alternatives, not
  addends. The design addendum rounds it to ~217 s; the census artifact's
  projection is 223.5 s and is the number of record.
- **`K = 220×` is still v0.17's number.** No throughput readout ran this cycle,
  and **`experiments/throughput_tasks.json` did not move at all** — it is not
  among the seven `data/`+`experiments/` paths that changed since v0.21.0. The
  scorer that moved in v0.21 is still un-re-measured; the next readout is not a
  like-for-like comparison with v0.17's.
- **No resolver score or served resolver byte moved.** The §1 fence held; and
  because the slice stopped at the census, nothing was wired to any serving
  path at all.
- A passing Python test is not a Lean proof.

## Drift audit

*(RELEASE-v0.20.0, RELEASE-v0.21.0, ROADMAP-v0.20 and ROADMAP-v0.21 re-read in
full, per the rule.)*

**This rotation's audit found no new product-surface over-advertisement, and one
goal deliberately carried rather than lost.** The two censuses are diagnostic
work, not surface work, so the audit's main task is to confirm the
plain-conversation surface that ROADMAP-v0.21 was built around is carried by
decision, not dropped by attrition.

### The plain-conversation surface: carried into v0.23 by decision, named here

ROADMAP-v0.21 titled itself *"the thing a conversation happens inside of"* and
named, in plain words, *a plain conversation, in plain text*. Its slice 2 (a
person types plain text and gets a proposed-and-verified answer) **shipped as a
negative** — the proposer served nothing. v0.22 did not schedule that surface;
it scheduled the census that diagnoses **why** the proposer starved (the
nameless library). That is not attrition: the surface is carried into
**ROADMAP-v0.23 as GUEST AXIOM** (`docs/DESIGN-guest-axiom.md`), the
maintainer's own long-recorded goal, and it runs on the 2,313 statements the
voice can already speak — the part of the library that *does* have names. Named
here so a later rotation inherits a decision, not a silence.

### The cost ledger: SIXTH cycle parked, and the sentence changes again

The lane (answers per joule and per dollar) is parked a **sixth** time. The
counting basis is unchanged — rotations since `DESIGN-grounded-throughput` §10
named it first among two successors: v0.17, v0.18, v0.19, v0.20, v0.21, and this
rotation (v0.22). RELEASE-v0.20.0 and ROADMAP-v0.21 read *fifth*; ROADMAP-v0.22
§4.3 read *sixth* and, for the first time, named a successor — **TOLL** — and the
v0.23 rotation makes it the seventh (ROADMAP-v0.23 §4.3). **The shift this
rotation records:** TOLL is no longer only a name. §2's COLD RECEIPT harness is a
**re-check-cost instrument**, and the v0.23 course parks **ORPHAN** explicitly as
the lane that *"unparks TOLL's n=1 denominator"*
(`reports/design-direction-v0.23.json`). The lane is still parked and this cycle
still designs nothing for it — but its metrology now has an instrument and a
denominator path, which is more than *"a metrology no cycle has designed"* ever
had.

### Ledger-first claims: SIXTH pass-over, trigger not met, and cleaner than ever

The v0.17-course lane (gate L1–L13, hardened) is parked a sixth time, named
dependant *none this cycle*, receipt `reports/design-direction-v0.17.json`. Its
trigger — *it **became** a headline candidate the first cycle after the
throughput readout* (a fired, one-shot event at v0.17, not a standing
conditional) — is restored in wording. **v0.22 produced no new throughput
readout, and this cycle is the cleanest such statement yet:**
`experiments/throughput_tasks.json` **did not change at all** — it is absent
from the seven-path `data/`+`experiments/` diff since v0.21.0. Load-bearing /
premise-necessity travels with this lane and unparks with it, never separately.

### Open-English input: the nameless finding is its definitive answer on the index side

The reverse-lexicon synonym-layer question — *can the committed realization
lexicon run backwards (gcd vs "greatest common divisor")?* — **now has a
definitive answer on the index side**: the census measured that the lexicon the
question would invert is the same glossary whose bulk is boilerplate, so there is
nothing to invert for 96.74% of the library. The reverse-lexicon **mechanism**
is still an unanswered park (inverting the lexicon is a different design from
enumerating the index), but the convergence is now measured, not hypothesised.
Carried to v0.23 folded under the naming-layer question, where GUEST AXIOM works
the 2,313-statement named remainder from the person's side instead.

### The `conform` route still advertises the asker's numbers, and is still not patched

RELEASE-v0.21.0's audit caught the `conformance` capability-sheet row describing
*"the asker's own numbers"* against a route that discards them
(`scripts/serve_chat.py:635-637` vs `scripts/harness.py:2229`), filed it in
BACKLOG and parked it in ROADMAP-v0.22 §4.3. **Verified unchanged this rotation:**
`scripts/` did move (five files), but none touched that route's binding
behaviour, and narrowing or widening a served route at a rotation remains a
behaviour change owing its own evidence. It carries, parked, with its two
admissible discharges intact.

### `[SUITE-GATE-V22]` resolved at the tag, as V20 and V21 were

The drafter's caution was misplaced and is corrected here rather than shipped:
`[SUITE-GATE-V20]` and `[SUITE-GATE-V21]` were **not** left unresolved — both
carry their run tables and committed receipts (`reports/test_gate_v020/`,
`reports/test_gate_v021/`, each with the red runs retained). `[SUITE-GATE-V22]`
is resolved the same way: the placeholder existed only in the drafted notes
between the rotation and the frozen-tip gate, and the gate ran green on the
first attempt (above). It is named through its lifecycle and then closed, not
carried.

None of the previous two closed documents is edited: a closed roadmap and a
shipped release are the record of what was written.

## The next direction, chosen before this document

The outside design inquiry was **invoked strictly for the fifth consecutive
cycle**. `reports/design-direction-v0.23.json` records three isolated series,
three rounds each — **nine rounds, fifteen round-one directions, $2.99** — run
headless from an empty non-git directory outside the repository under a strict
tool denylist, isolation mode **inherited unchanged** from the v0.22 receipt,
brief on file and hash-verified (`series_1.r1` equals the brief hash by
construction).

**Selected: [`docs/DESIGN-guest-axiom.md`](DESIGN-guest-axiom.md)** — the
supposition frame turned **inbound**: a person supplies a hypothesis the library
does not contain, and the system serves a machine-checked implication naming it
undischarged and not believed. It is the maintainer's own long-recorded goal,
arrived at independently by series 3, and **chosen over the metric leader
NO-FLIP by explicit orchestrator ruling** recorded as a decision in the design's
§2: NO-FLIP's improvement channel is dead this cycle (R3's zero-growth window),
its regression half re-runs the erratum probe, and GUEST AXIOM can run this cycle
on the 2,313 round-trippable statements.

**Item 2: [`docs/DESIGN-echo.md`](DESIGN-echo.md)** — is the served voice
injective? Scheduled *before* item 1 because its collision result licenses GUEST
AXIOM's clarify-vs-conditional rule.

**And both v0.23 designs were falsified by review before landing**, which is the
discipline binding the orchestrator continuing: ECHO's first draft claimed a
code-disjoint reader the tree does not hold (there is no committed sentence→term
path that is not the renderer's own inverse; ECHO now builds one from scratch and
says on the page that it is import-disjoint but not algorithmically independent).
GUEST AXIOM's draft lacked a result gate and a powered person-wrong control; both
are now frozen (§7a, §7). This is the second consecutive cycle in which the
selected designs failed their first review — the review gate binds the person
planning the work, not only the measurements.

## The release refresh

The full-suite verdict is in *The suite at the tip* below; the generated-state
chain is reported here, all of it run at rotation start.

- `validate_nodes.py` — **12,777 statement nodes across 27 corpora**, green.
- `check_regeneration.py` — seeds regenerate committed data byte-identically,
  exit 0.
- `signature_matches`, `specializations`, `compression` — regenerated at
  rotation start byte-identical to the committed reports, exit 0.
- `ingest_wold.py reach` — **ran, exit 0**: WordNet reach **1,394/1,460 =
  95.5%** against the pinned gitignored archive present on this machine. A
  contributor without the archive gets the refusal, which is *cannot verify*,
  never *skipped*.
- `check_report_regeneration.py` — **ran, exit 0**: `signature_matches` /
  `specializations` / `compression` clean, `decompositions` **declared_divergence**
  with its TRIAGE-v0.11 citation — the full chain green in one pass at rotation
  start, the two-cycle pending streak closed at v0.21 and held here.

A refresh step reported without its exit status is a step nobody checked; every
step above carries one.

## The suite at the tip

**Green on the first run: 2,789 tests, OK (skipped=5), 22,307.8 s (6 h 12 m)
at the frozen tip `85515e9`.** The log is in `reports/test_gate_v022/`
(`run1-green.log`, `runs.md`) — one run, no reds, unlike v0.20 (two) and v0.21
(three); the freeze discipline that caught those cross-lane pin drifts had
nothing to catch this cycle because both item lanes were censuses, not
witnessed-module edits. Up from v0.21.0's 2,632 by this cycle's new modules —
`test_handles_census`, `test_onestep_census`, `test_erratum_probe`,
`test_cold_receipt` — whose assertions include the **absence** of the un-built
handle table, pilot and Q60, and the cold harness's tree-restore proof. The
five skips are the standing set. A targeted suite proves the surfaces you
listed; the full gate proves the ones you forgot — and this time there were
none forgotten.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.**

`git diff --name-only v0.21.0..HEAD -- data/ experiments/` lists **seven paths
and not one `.py`**, and `data/` did not move at all this cycle — every path is
under `experiments/` (six `.json` census/index artifacts and `ANALYSIS.md`), and
the new `cold/` bundle is likewise all committed JSON and evidence. No training
data changed and no `experiments/*.py` changed, so **the checkpoints attached to
[v0.6.0](RELEASE-v0.6.0.md) remain accurate for this release** and re-uploading
identical bytes would cost upload time to say nothing new.

Every measurement ledger is committed in-repo (`experiments/*.json`,
`cold/*.json`) and linked by path above rather than duplicated as an asset.
Licensed external data (`experiments/data_real/`) is never attached.

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py

# On Windows every command below needs PYTHONIOENCODING=utf-8: these scripts
# print glyphs cp1252 cannot encode, and the UnicodeEncodeError reads like a
# refusal and is not one.

# 1. the naming census: 417 of 12,777 typable specific handles, the plateau,
#    and the bulk's nine-token cause
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/handles_census.json',encoding='utf-8')); \
    print(d['union']['specific_handle_union_typable'], 'of', d['corpus']['statements']); \
    print('K plateau [80,218]:', d['k_sensitivity']['plateaus']['typable union']['invariant_for_K_in'])"

# 2. the cross-census sentence: 125 of 9,048 consumable statements are nameable
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/onestep_census.json',encoding='utf-8'))['cross_census_reading']; \
    print(d['with_a_specific_typable_handle'], 'of', d['one_step_consumable_strict'])"

# 3. the evidence-survival partition, and that the voiding sentence did not fire
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('cold/census_run2.json',encoding='utf-8')); \
    print(d['counts'], 'voiding fired', d['voiding_sentence']['fired'])"

# 4. the erratum flip probe: zero real flips, plant detected 1/1
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/erratum_probe.json',encoding='utf-8')); \
    print('real flips', d['real_flips']['count'], 'over', d['real_flips']['turns_replayed'], 'turns'); \
    p=d['planted_flip']; print('planted flip detected', p['detected'], 'of floor', p['floor'])"
```

Reproducing the one SURVIVES kind's repo-free re-check requires the pinned Lean
toolchain (`leanprover/lean4:v4.32.2`), invoked by absolute path with no elan
proxy, no lake, no Mathlib and no network — exactly as a stranger holding only
the C-E3 bundle would invoke it.
