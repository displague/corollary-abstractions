# Handles

**Status: design only.** Nothing here is implemented. This is the v0.22
course's selected direction (receipt:
`reports/design-direction-v0.22.json`, which records the outside draft
verbatim in `outcomes.series_1.preregistration_draft`). The first
version of this document failed its adversarial review on the same
class of defect the v0.21 design first failed on — claiming ground the
repository already occupies and citing producers that do not exist —
and was rewritten on the verified base. Deviations from the outside
draft are marked DELTA with the finding that forced them.

## 1. The boundary being moved — corrected by what the tree already holds

The v0.21 intake run measured the bottleneck twice: one question
enumerated **zero** candidates (`docs/DESIGN-plain-input.md` §8.4) and
another had its correct readings buried at ranks 21/23 by a
title-length tie-break (§8.5). The first draft of this design read
those as "no non-title index exists." **Review falsified that.** The
committed resolver already holds two non-title indices over all 12,777
statements: `resolver.by_lexicon` (`scripts/resolver.py:264-277`),
over the per-node `symbol_lexicon` glossary — records on all 12,777
statements, 27,182 entries, though 93% of those are bulk-ingest
boilerplate (review N7; the human-named share is the curated ~2%, §3)
— and `resolver.inventory` (`scripts/resolver.py:284-288`), an index
over the four fields exclusions may read (title, meaning, keywords,
lexicon — not title-free; §3's S-INV uses the title-free
`template_call_heads` instead, review N2). Run live,
`resolve('greatest common divisor')` — the *phrase* — reaches
`programming.euclid.{iterative,recursive}` through `by_lexicon` today.
§8.4's recorded case is the full *question* ("how do you compute the
greatest common divisor recursively"), which still passes unresolved
(review N8); B5 gates on the question, and the phrase resolution is
evidence the names exist, not that the question already works.

**The real defect is narrower and worse:** the v0.21 candidate
enumerator (`scripts/candidate_enumerator.py:166-168`) builds its
haystack from `title` + `keywords` only. The proposer path was wired to
the weakest index on the tree while the stronger ones sat unused on the
same serving path, one route earlier. Reachability is not missing; it
is **unmeasured, un-gated, and unwired where the intake ambition needs
it**.

So the boundary this design moves (DELTA from the draft, which
proposed deriving a new index): **unify the committed non-title sources
into one first-class, gated handle table; measure what it reaches under
title deletion; and wire the candidate enumeration path to it.** The
human capability is unchanged: a person's question reaches a statement
through what the statement says and how mathematicians name its parts,
not through what somebody titled a file.

**The park this reopens, adjudicated in writing.**
`docs/BACKLOG.md:1373-1388` parks the resolver-coverage lane behind the
v0.15 standing rule: it unparks only with a mechanism justified
independently of the score it would move. Discharged here explicitly:
the mechanism is **candidate enumeration for the proposer path** — a
surface (`plain_input`) whose gate (G5) does not score resolver
coverage at all, and whose v0.21 red is the independent justification.
The resolver's own scores are not touched by this design (§9's fence),
so the rule's condition is met rather than evaded. The
lexicon-backwards question that entry names stays parked; §6 P-L
records what this design's census tells it.

## 2. Why this survived the course

Series 1 (inference and index machinery) produced HANDLES and ranked
it first on capability. Series 2 (the person and time) produced COLD
RECEIPT — does the program's evidence survive the program's deletion?
— which becomes ROADMAP-v0.22 item 2 with its draft recorded in the
receipt and one clause added before registration (the provenance
downgrade its own residual risk demanded). Series 3 (the substrate)
produced CANARY-CURVE (declared scaling classes; the
architecture-vs-smallness decomposition of the throughput headline)
and TOLL (the five-cycle-parked cost lane returning with a metrology).
Both park as **named incumbent-candidates for v0.23**; the ordering is
CANARY-CURVE's own residual risk answered — its shadow growth prices
statement count, not the density dimensions that bite (title
collisions, enumeration fan-out), so growth is measured **after** the
enumeration layer exists, when density is measurable instead of
missed.

The funnel kept, with dispositions: ONE STEP (CHAIN⊕BRIDGE;
answer-or-frontier where a correct refusal scores) survives as **rider
R1**, its depth-1 census able to close three parked lanes at once.
ERRATUM survives as **rider R3** (the flip-count probe deciding its
v0.23 candidacy). TWO WITNESSES — the kernel-then-overlap probe plus a
160-obligation mutation battery — was demoted by review from rider to
**parked item-candidate**: the battery is a WITNESS-slice-sized cost
(the whole v0.21 WITNESS slice budgeted 50 mutants), not a rider, and
it waits with the parked conformance successor it serves. NOTARY died
into a mandatory receipt column (`route_voids[]`, §4). CROSSING parks
with its 20-corrections probe and its preregistered predicted split
(2/6/12). LONG CON parks as a day-probe (frozen budget, mandatory
plant, committed taxonomy; the write-gate prohibition inherited).
BITROT parks as a day-probe **with its stop rule stated here since the
receipt carries only its controls: undetected-changed-answer count
>0 stops the probe and publishes the narrowed scope; a clean 1000
publishes the map and closes the probe.** CEILING is TOLL's named
successor (no budget freezes before the cost distribution exists — the
v0.21 mis-derived-floor lesson).

## 3. Sources, as the tree actually holds them (DELTA: rewritten from review)

**Record presence is not handle yield (review N1).** Every statement
carries a `symbol_lexicon` record; almost none of the ingested bulk
carries a *usable* one. The review measured it: with K=128, statements
holding ≥1 SPECIFIC handle are ~**263** via S-LEX and ~**306** via
S-INV — essentially the same curated ~2%, because 12,514
`lean_workbook` nodes share three boilerplate name pairs
("equality"/"template"/"standing") that K excludes as overbroad, and
S-INV's head distribution is dominated by universal heads (`IMPLIES`
9,403; `MEET` 8,160). §1's live gcd resolution comes from inside that
2%. **The authoritative coverage numbers are H-P0's to return, not
this table's to assert**; the indicative yields above are the review's
measurement, cited as the reason §9 and §10 are scoped the way they
are.

> **H-P0 has now returned them (2026-08-27,
> `experiments/handles_census.json`), and both indicative yields are
> exact**: 263 via S-LEX, 306 via S-INV, at K=128. Their union — the
> only reading that speaks to what a person could type, since S-SKEL
> reaches everything and nobody types a skeleton — is **417 of 12,777,
> 3.26%**.
>
> **One dated correction to the sentence above.** "Three boilerplate
> name pairs" was the review's approximation and is inexact in both
> directions. Measured over the 12,514: **nine** distinct glossary
> tokens (`emitted`, `equality`, `ground`, `ground_numeral`,
> `ingested_slot`, `numeral`, `slot`, `standing`, `template`), drawn
> from **six** distinct raw glossary strings, of which exactly **one** is
> an entry `name` — `equality`. The three words quoted are real and are
> among the nine; the count "three" and the word "name" are not. The
> finding the sentence carries is unaffected and is understated by it:
> nine tokens across 12,514 statements, none of them specific at any K
> that excludes boilerplate (§7 B2's dated adjudication).

| source | producer (committed code) | status |
|---|---|---|
| S-LEX: `symbol_lexicon` names | `resolver.by_lexicon`'s underlying per-node glossary | records on all 12,777; specific-handle yield ~2% (curated corpora); H-P0 measures |
| S-INV: call-head inventory | `match_signatures` `template_call_heads` over `anonymized_template` (`match_signatures.py:952,1038`) — title-free; *(the draft's `resolver._inventory_strings` citation was dropped by review N2: that function reads `title` and `keywords` and cannot pass B3's audit)* | recomputable, **not persisted** (aggregates only in `reports/signature_matches.json` — review N6); H-P0 commits the table |
| S-SKEL: family skeletons | recomputable by committed code (`measure_compression.py`); **strings not persisted** — the committed data is counts plus the twin groups' 2,537 ids | all 12,777 recomputable; H-P0 commits the id→skeleton table; a skeleton string is nothing a person types, and the design claims no human-question match for it |

Deleted from the draft (review C2): **S4 notation records** (no
producer exists — the only structured notation is 389 hand-authored
rows on 186 statements) and **S5 defeq alias buckets** (no defeq
machinery exists
anywhere in the tree). **S3 elaborated-term unfoldings** is demoted to
a priced question: only digests are persisted
(`scripts/foreign_voice.py:205-217` drops the payload), coverage would
be **2,319 oracle-eligible, of which 2,313 covered** (the two numbers
are subset, never summed — `docs/BACKLOG.md:1122-1133`'s anti-merge
rule, which the first draft violated), and term-store work is a later
slice if H-P0 prices it worth taking.

**H-P0 (construction prerequisite):** one committed census — per
source, exactly which statements it produces handles for, from which
committed producer, plus the id→skeleton table for S-SKEL, plus the
priced statement of what S3 term-serialization would cost — BEFORE any
handle table exists.

## 4. The first-class object

Three artifacts (review N4 restored the partition the L3 fix had
over-trimmed; the rider artifacts are the riders', listed in §11):
**`experiments/handles_table.json`** — one row per (statement,
handle): `statement_id` · `handle_token` · `producer` ∈ {S-LEX, S-INV,
S-SKEL} · `producer_run_id` · `resolves_to_count` · `specific: bool`
(§7 B2); **`experiments/handles_partition.json`** — one row per
statement: `class` ∈ {REACHABLE, RESIDUE} · `residue_cause` ∈ B4's
frozen vocabulary — the deliverable §10 names and §11 routes; plus the
enumeration receipt schema the table serves:
`experiments/handles_enum_receipts.json` with `question_id` ·
`candidates[{statement_id, handle_witnesses[]}]` · `budget_used` ·
`measured_verification_cost_s` · `outcome` ∈ {ENUMERATED,
REFUSE_NO_HANDLE_MATCH, REFUSE_OVERBROAD_ONLY} · `route_voids[]`
(non-optional — NOTARY's distillation: a receipt that traverses a
published void and renders clean is a red result).

**Candidate order under budget, frozen (review H6):** when handle
matches exceed the budget B, candidates are taken in ascending
`resolves_to_count`, ties broken by `statement_id` byte order —
specificity first, never string length (the §8.5 lesson), and the rule
is in the prereg, not the code comments.

## 5. Trusted and untrusted components (review H7)

Trusted, review-carried: the three producers (committed code), the
table builder, the ablation harness, the enumeration path, the
receipts. Untrusted: nothing in this slice — no learned component
touches any part of item 1 (the proposer consumes the enumeration
downstream under its own v0.21 gates, unchanged and unscored here).
The one boundary: `handles_table.json` is regenerable from committed
code and pinned corpora; it is an experiments artifact with a digest
pin and a regeneration test, never a corpus.

## 6. Construction prerequisites

- **H-P0** — the coverage census (§3), committed first.
- **H-P1 — the budget pilot (review H2):** measure per-candidate
  verification cost over ≥200 candidate verifications on half the
  question set's authoring drafts, publish the cost, and freeze B from
  it **in a dated amendment before Q60 seals** (the
  `DESIGN-witnessed-conformance.md` pilot-then-freeze shape). B is not
  40 until the pilot says so.
- **H-P2 — Q60 sealing:** 60 questions, 42 in-library / 18
  absent-target (30%), including §1's gcd question and the rank-21/23
  question; sealed with candidate-reading sets before the table
  exists. The 13 silent-bind questions from v0.21's sealed thirty are
  **a separate, third sealed subset** (review M4): they are scored
  only by B6's choice-event clause, never pooled with the 42/18.
- **P-L** — the lexicon-backwards park gets one census line from
  H-P0 (which S-LEX names also appear in the realization lexicon's
  English), recorded for that park's future unpark case; nothing else.

## 7. Construction gate (numbers frozen now; arguments per §4.0(3))

- **B1** Every handle carries a producer in {S-LEX, S-INV, S-SKEL} and
  a `producer_run_id`; one untagged handle is red. *Meetable:* all
  three producers are committed code today (§3's table cites them).
- **B2** Specificity K = **128**. *Meetable, argued on the right
  source (review H1):* S-SKEL buckets are small (mean 1.12 statements
  per skeleton, max family reuse 10 — `reports/compression.json`), so
  K never binds there; the argument that matters is S-INV/S-LEX, where
  universal tokens (`Nat`, `+`, `≤`) resolve to thousands and are
  exactly what K exists to exclude. H-P0 publishes the
  resolves-to-count distribution per source; if it shows K=128 strands
  whole corpora with no specific handle, K is re-frozen from H-P0's
  distribution by dated amendment BEFORE the table run — never after.

  > **Trigger adjudicated NOT FIRED (2026-08-27).** H-P0 ran and the
  > re-freeze condition is arguably met on its face: lean_workbook's
  > specific-S-LEX coverage is **0 of 12,514**. The adjudication, with
  > its numbers in `experiments/handles_census.json` `k_sensitivity`, is
  > that K stays **128** — (a) the corpus is not *wholly* stranded, since
  > S-INV gives **154** of those 12,514 a specific handle; (b) K=128 is
  > **interior to a plateau**, not on its edge — S-LEX's 263 is invariant
  > for K ∈ [22, 301] and S-INV's 306 and the union's 417 for K ∈ [80,
  > 218], so any re-freeze inside that range returns identical numbers;
  > and (c) decisively, **no re-freeze rescues the bulk.** The smallest K
  > at which S-LEX reaches a single lean_workbook statement is **302**,
  > and it gets there by admitting one token — `ground_numeral`, a
  > boilerplate `semantic_role` — which is precisely what K exists to
  > exclude; even then it caps at **302 statements, 2.41% of the bulk, at
  > every larger K forever**, because six of the bulk's nine glossary
  > tokens are each held by more than 12,200 statements. A re-freeze
  > cannot turn the finding around; it can only buy 2% of the bulk by
  > admitting the boilerplate the finding is about. What would change
  > this is a source that gives the bulk names, which is §9's headline
  > and a v0.23 rotation question, not a K question.
- **B3** Title ablation, red-able by construction (review H5):
  `title_derived` is not a token comparison — it is a **producer
  audit**: an AST check (the v0.21 G8-repair precedent) that the table
  builder and the enumeration path read neither `title` nor `keywords`
  fields, plus the ablation run where the title index is removed
  entirely and every Q60 answer re-derived. The clause goes red if the
  AST audit finds a read or if any enumeration receipt differs between
  title-present and title-absent runs (the index may not depend on
  titles even accidentally).
- **B4** Residue enumerated member-by-member with a cause from the
  frozen vocabulary {ALL_OVERBROAD, NO_LEXICON_ENTRY, NO_INVENTORY,
  UNCLASSIFIED}; UNCLASSIFIED > 5% of residue is red. *Meetable:*
  causes are structural predicates over the table.
- **B5** The gcd question enumerates its target at any rank (floor
  1/1). *Meetable:* `by_lexicon` already resolves it live; this clause
  pins that the unified table does not lose what the tree had.
- **B6** All 13 silent-bind questions emit `choice_events[]` or route
  through enumeration; 13/13. *Meetable:* routing and logging.
- **B7** Two sealed scoring classes, never aggregated; the blind
  chance rate is computed **per question from its enumerated candidate
  set** (review H4 — the G5 correction applied as G5 computed it:
  expected blind hits = Σ verified/candidates per question), published
  beside the observed rate. Absent-target refusals
  (`REFUSE_NO_HANDLE_MATCH`) score correct; over-refusal on the 42
  scores incorrect.
- **B8** The permuted-handle control (§8).
- **B9** Rider floors, each with its argument: **R1** (depth-1
  census): ONE STEP's build opens at ≥200 one-step-consumable
  statements AND ≥5/60 questions landing there — *the floor is a lane
  opener, not an instrument verdict; a miss closes the lane and the
  census publishes regardless; meetability is deliberately not argued
  because the census exists to measure it* (its stop rule: census
  committed, lane opens or closes, nothing else runs). **R3** (ERRATUM
  flip probe): floor = **1** designated planted flip detected in the
  replay harness (the mechanism check), real-flip count published with
  the growth window named; stop rule: zero real flips publishes the
  scale sentence and R3's v0.23 candidacy is decided by the count, not
  re-run. *(R2 removed — review H9: parked as an item-candidate with
  TWO WITNESSES, §2.)*
- **B10** H-P0 committed before the table; a handle from outside its
  censused coverage is red.

## 8. Blind control, vacuity control, and voiding sentence

**Permuted control:** the identical handle multiset reassigned across
statements by a seeded permutation, run against Q60 under the same
budget and sealed classes. **Frozen voiding sentence, mechanically
evaluable (review N5):** *Before any arm runs, the prereg publishes E =
the sum over the 42 present-target questions of each question's
per-candidate-set chance (B7's computation) and its standard deviation
σ under independent draws. If E ≥ 2.5, the candidate sets are too
loose to test and the run voids as unconstructable. Otherwise, if the
permuted index's present-target hit count is ≥ ⌈E + 2σ⌉, reachability
as defined here carries no signal and the capability claim is void
regardless of the true index's raw score.*

**Vacuity control (review H7):** the incumbent title+keyword
enumerator runs over the same Q60 as the cheapest capability-blind
baseline, **charged for candidate volume per the house precedent**
(`DESIGN-when-to-ask.md`'s reciprocal-load lesson — a baseline that
"recalls" by returning thousands pays 1/k). It must lose the gcd
question by construction; if it matches the handle table overall after
the volume charge, handles added nothing and the run publishes that.

**Corruption control:** 20 seeded table corruptions (wrong
statement_id on a real handle; fabricated handle token) must each
either change an enumeration receipt or be caught by the digest pin —
a corruption that changes nothing observable is itself published (it
means the corrupted region was dead weight).

## 9. Result gate

**R-H:** the capability sentence serves only if B1–B8 and B10 are
green AND the title-ablated table reaches ≥ the title index's
volume-charged score on the 42 (it must not be worse than what it
replaces) AND the 18 absent-target refusals hold. The served sentence,
frozen and **scoped to what H-P0 finds, never to the library** (review
N1): *for the statements H-P0's census shows carry a specific handle,
a question can reach them through their verified content and their
authored names, with titles deleted — under the maintainer-authored
question set and nothing wider.* **H-P0 stop clause:** if the census
reads specific-handle coverage near the review's indicative ~2%, the
slice publishes the census as the headline — *the ingested library is
effectively nameless; the naming layer must be built, not indexed* —
and the capability sentence does not ship; whether name-derivation
(from the verified English renderings the voice lanes already serve,
or elsewhere) becomes v0.23's work is the rotation's question, not
this slice's assumption. The resolver's own routes and scores are
untouched (the fence: `_route_resolver`'s served bytes byte-identical
before and after, tested — this design changes candidate enumeration
for the proposer path only).

## 10. Stop conditions and non-claims

Stop if B1, B3's audit, B8, or B10 fires — no partial index ships.
Non-claims: no reachability rate (the deliverable is the partition and
its enumerated residue); no ranking work beyond the frozen §4
truncation order; no hand- or model-authored synonyms; no claim the
residue is small, only complete; no claim a reachable statement is
correctly reachable; no stranger-usability claim — Q60 is
maintainer-authored, the authorship contamination is named, unpriced,
and inherited by every number here; no change to any resolver score or
served resolver byte.

## 11. Item 2, riders, and routing

**Item 2 — COLD RECEIPT** ships per the receipt's draft plus the
provenance clause (`external_deps[].provenance` ∈ {third_party_pinned,
program_configured}; any SURVIVES resting on program_configured
downgrades to UNTESTED), with one tense repair (review H8): B6 reads
*"200 scrambled bundles; **if** 0 of 200 pass, publish the 1.5%
rule-of-three upper bound as the chance rate"* — a gate, not a
recorded outcome. Its compact design lands before its slice.

Riders: **R1** (`experiments/onestep_census.json`) and **R3**
(`experiments/erratum_probe.json`), per B9. Parked: TWO WITNESSES +
the conformance successor (item-candidates, together); CANARY-CURVE
and TOLL (v0.23 incumbent-candidates, §2's ordering reason); CROSSING
(probe + predicted split recorded); LONG CON, BITROT (day-probes, stop
rules in §2). CEILING is TOLL's successor and routes with TOLL.
ANALYSIS gets the registered run's numbers; DISCOVERIES gets the
partition's headline if it moves what the program believed; BACKLOG
gets the parks; the course receipt carries the full funnel and all
three leads' drafts.
