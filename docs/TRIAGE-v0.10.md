> **CLOSED — historical triage record for v0.10.** Since v0.14 the roadmap
> triage lives inside the release notes ([RELEASE-v0.14.0.md](RELEASE-v0.14.0.md)
> and later); nothing here is current. Suite counts, gate readings, and
> open-friction lists below are as-of-v0.10 facts; several were later
> discharged (see [BACKLOG.md](BACKLOG.md) and later release notes).

# v0.10 release triage — gate status, drift audit, and the decisions that need a maintainer

Written before the release notes so the arguable calls are visible as calls,
not buried in prose. Two of them are the maintainer's, not mine.

## 1. Release gate: 7 of 7 (item 4 merged at `5653b22`)

`ROADMAP-v0.10.md` §"Release gate" lists seven conditions.

| # | gate condition | status |
|---|---|---|
| 1 | ≥1 new grammar head, each with its coverage delta on all three sources, zero parse problems | **MET** — four heads (trig, relational/predicate, quantifier/binder, embedded-quantifier walk); Goedel-Pset 32.8% → 44.6%, Lean-workbook 64.1% → 71.5%, miniF2F 29.7% → 33.4% |
| 2 | one ingested statement `verified_by`-grounded end to end, **or** a documented `formal`-without-bridge decision | **MET, both halves** — `lean_workbook_1041` bridged through a real Lean verdict; `lean_workbook_10202` recorded `formal`-without-bridge at node level because Mathlib is outside the hermetic budget |
| 3 | one verified-code node end to end + one structural-twin-over-code result vs a blind baseline | **MET** (item 3) — 3 code nodes, 3 PASS verdicts; matcher forms 1 pair at precision 1.0 where the token baseline forms 3 at 1/3 |
| 4 | **a real ingested source authored to a materially larger corpus**, ledgers recomputed | **MET on hundreds, not thousands** — item 4 merged (`5653b22`): the trusted `append_nodes` JSON format shipped (its own prerequisite, see §2), then a first wave of 251 parse-clean ground identities, 257 → 508 nodes / 26 → 27 corpora, formal-without-bridge, ledgers recomputed and byte-identical on regen. The remaining 12,681 unique-covered statements wait on a skeleton emitter (BACKLOG) |
| 5 | one real end-to-end harness session that produces or revises a node | **MET** (item 5) — four legs recorded, node applied through the audited route |
| 6 | updated assets whose notes explain winners, losers, and controls | **MET** — `experiments/ANALYSIS.md` carries every slice's numbers, negatives, and disclosures |
| 7 | the complete suite green | **MET** — 1084 tests, 4 skipped, on the merged tip |

**RESOLVED at triage: the gate is met and v0.10.0 is cut now** (maintainer
decision, §4). What the notes may honestly claim is bounded by what landed:
"a real ingested source authored to a materially larger corpus" is TRUE
(257 → 508, provenance intact, byte-identical regeneration); "thousands of
ingested nodes" is NOT — the first wave is 251 of 302 predicted parse-clean
ground goals, and 51 failed `TOKEN_RE` on standalone `<`/`>` that were
already in RELATIONS. The 12,681-statement remainder is not authored.

**The roadmap's real question was answered, on hundreds.** Does a
capability-blind baseline that won on 221 curated nodes still win on
ingested ones? The operator-bag baseline still wins on PAIR COUNT
(7,622 vs the matcher's 96) and loses harder on PRECISION (2.03% → 1.26%,
and 0.54% on ingested-only pairs) while the matcher's precision against the
bag stays 1.0. Reported as the headline it is, not buried: more pairs, worse
pairs.

**And ingestion compounds.** 614 `same_corpus` constituents inside the new
corpus; `^(2, 30)` now has a third owner (`lean_workbook_28978`). That is
item 5's two-constituent anecdote reproduced at hundreds — a data point for
`docs/DESIGN-self-grounding-ingestion.md`, NOT an adjudication of its S1–S4,
whose null model has not been run.

## 2. Drift audit vs v0.9's stated goals (the release skill's requirement)

v0.9 carried six things forward. What happened to each:

| carried from v0.9 | landed in v0.10? |
|---|---|
| Item 1's **authoring half** (ingested nodes into the graph) | **NO — carried a second time** (v0.10 item 4) |
| Item 2, programming as a first-class discipline | **YES** (v0.10 item 3) |
| Item 3, drive the open harness on a real session | **YES** (v0.10 item 5) |
| Item 4, an external benchmark | **NO — carried a second time**, not started |
| Item 5's lanes: proof-search depth, **multi-corpus WRITE patch**, groundedness gate | **NO — carried a second time** |
| Item 6, physics/affect/oscillation/visual rungs | still parked, deliberately |

**The finding this audit exists to produce.** The multi-corpus WRITE patch
was carried through two cycles as a minor lane in a list of "carried-open
lanes" — the least prominent item on the page. In v0.10 it became the thing
**blocking the headline authoring item**. Item 5 discovered this by running
the real gate rather than reasoning about it: the WRITE lane stages new
seed/new corpus pairs only, so adding one statement to an existing corpus is
impossible, and item 4's thousands of statements would need thousands of
one-node corpora. A deferral compounded into a blocker, and nothing in two
roadmaps noticed, because the lane was never re-read against the items that
depended on it. **Concrete process change for ROADMAP-v0.11: every carried
lane must name which of the cycle's headline items depends on it, or be
explicitly parked.** A lane with no named dependant is parked; a lane that
blocks a headline item is not a lane, it is a prerequisite and gets ordered
before its dependant.

**The second attrition signal, stated plainly:** the external benchmark
(v0.9 item 4 → v0.10 item 6) has now been carried twice without being
started. Its roadmap entry honestly says it depends on items 1–4, so this is
sequencing rather than neglect — but two cycles of silent carry is exactly
the pattern above. v0.11 must either schedule it with a date-shaped
commitment or park it in writing.

**What did NOT drift, worth saying because attrition audits only ever list
failures:** every headline item that was *started* in v0.10 finished, each
with a registered design committed before implementation and adjudicated
after; the independent-review-before-merge discipline held for six
consecutive slices and caught a real defect every time; and no slice merged
without the full suite green.

## 3. Maintainer decision #1 — the absorption rate-gap pin

Standing since the quantifier slice and re-pinned by **four** consecutive
slices against its original guard direction:

| slice | rate gap | count floor (`e_best` > 4 × `a_best`) |
|---|---|---|
| pin as written | < 0.12 | — |
| quantifier/binder (v0.10 item 1) | 0.164 | holds, 4.3:1 |
| programming (item 3) | 0.156 | holds |
| recorded session (item 5) | **0.159** | holds, 387 > 4 × 86 |
| item 4 first wave | **0.490** | holds and STRENGTHENS, 457 > 4 × 86 = 5.31:1 |

The count floor — the load-bearing guard — has never been weakened. What
moved is the *rate* reading: absorption's best-owner external rate leads the
exact channel's by ~16 points where the pin promised under 12. Each slice
re-pinned it at its measured value with an argument, which is defensible
once and starts to look like ratcheting at three. The retracted inference
("absorption concentrates cross-discipline credit") currently rests on count
dominance alone.

**DECIDED at triage: the < 0.12 rate pin is RETIRED, with the rationale
recorded where the assertion used to be** (`tests/test_decompose_channels.py`).
The fourth movement made the cause unmistakable: the gap is a ratio whose
denominator the corpus controls. Ingesting 251 identities that ground each
other added 614 `same_corpus` constituents to the exact channel, dropping
its external rate from ~70% to ~37% while absorption stayed at 86/100.
Absorption did not become more external — the exact channel became more
internally grounded, which is the result the ingestion program was after. A
guard that moves every time the corpus succeeds is measuring composition,
not the behaviour it guards.

What the pin was FOR survives: the retracted "absorption concentrates
cross-discipline credit" inference is refuted by the COUNT floor, which has
never weakened in any slice and is composition-robust in the direction that
matters — more exact credit strengthens it. A future rate-shaped guard owes
a composition-robust statistic and its own registered prediction, not a
fifth re-pin of this one.

## 4. Maintainer decision #2 — release scope

**DECIDED: cut v0.10.0 now.** Item 4 merged, so the hold this section
recommended is moot — the thing it was waiting for arrived. The gate is 7/7
and `verify_slice` passes on the merged tip (1084 tests, 4 skipped).

One disclosure the release owes, because it is the cycle's own standard:
**item 4 merged without the independent adversarial review the other six
slices each received** — the pass that found a real defect 6 times out of 6,
including twice in item 5's own work. The maintainer weighed that and chose
to ship: the slice self-reported its misses (302 → 251 on `TOKEN_RE`, the
disclosed P6–P8 skips, the rate-gap flag) rather than hiding them, and the
mechanical harness is green. Anything a later review finds becomes a v0.11
fix, and the release notes say so rather than implying seven-for-seven
review coverage.

## 5. Forward-looking design for ROADMAP-v0.11 (release-skill requirement)

The skill requires ≥1 strong forward-looking design item, inspired by what
the previous releases actually produced. The candidate is **self-grounding
ingestion, measured**, and it comes from a two-constituent observation in
item 5 that nobody designed for: the moment a second ingested statement
existed, it and the first grounded each other's shared `2 ^ 30` subterm
through the `prior_corpus` channel — the first prior_corpus constituents in
the corpus to carry a real shared discipline rather than the `mathematics`
umbrella.

That is the compounding hypothesis in miniature, and v0.11 can make it a
measurement rather than an anecdote: as ingested nodes go from 3 to
thousands (item 4), does the share of subterms grounded *inside* the
ingested layer rise superlinearly with corpus size, or does it flatten
because ingested statements are mutually alien? Both answers are
publishable, and the negative is the more interesting one: a flat curve
would say ingestion buys coverage but not structure, which would change what
the corpus is for. The instrument mostly exists — the decomposition channels
already distinguish same-corpus, prior-corpus and external ownership — so
the design work is the sampling and the null model (what grounding rate
would random ground statements over the same operator inventory produce?),
not new machinery. It also gives item 6's external benchmark its most
defensible shape: a claim about structure recovery that the architecture
wins *because* of its design, measured on a corpus large enough to be
uncomfortable.
