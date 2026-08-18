# Roadmap v0.14 — when should it ask?

The v0.13 candidate reached 24/24 questions and still could not ship: one
negative sentence bound the excluded concept and fresh false positives rose to
0.034.  The cycle also refused to score context after discovering that its
follow-up lines were not frozen.  v0.14 joins those facts in one fresh,
auditable question.

Governing design: [DESIGN-when-to-ask.md](DESIGN-when-to-ask.md).

## 1. Freeze the evaluator before the implementation (prerequisite)

Commit one executable preregistration containing:

- exactly 48 rows in the four registered strata;
- initial query, intended ids, expected route, exact follow-up, retained ids,
  and negative span for every applicable row;
- the frozen `without TERM` parser/veto skeleton;
- canonical-LF provenance and a manifest of every score-affecting Git object;
- automated text/id disjointness from all spent conversational sets;
- the exact 25-candidate title-only blind arm and negative-stripped ablation;
- pinned OEWN archive, seed 20260825, and stable sampling algorithm.

Malformed protocol is a refusal.  Absent or dropped targets are scored misses.
No row replacement after any score is visible.

## 2. Exact negative contrast and clarification (headline)

Implement only the preregistered grammar and run the holdout once.  Ship the
candidate only if Q1–Q6 all fire: zero wrong negative BINDs; negative-stratum
route/reach floors; follow-up halving with intended-reading retention; a
material blind-control gap; false positives no worse than 0.030; in-corpus
reach and target recall at least 0.833; and a causal stripped-ablation gap.

The spent “without compounding” row remains a public regression, never a
scored row.  A miss publishes and parks the implementation.

## 3. Make the release gate observable

Retain per-shard JSON receipts and module lists for the v0.13 gate.  Measure
whole-suite module wall-clock without overwriting the historical result, then
register a balanced assignment rule.  Investigate separately:

- the 5,620-second blind-control sweep;
- roughly 4,700 seconds of `test_corpus_analogy_split` fixture/runner gap;
- whether a sampled control can preserve the non-vacuity guarantee.

No optimization may weaken a capability-blind control without a registered
replacement.

## 4. Explicit parks

Not v0.14 work without a new dependant: grounded admission, W1–W3, write and
budget rankers, general specialization indexing, deeper proof search,
physics/affect/visual expansion, HTTP skin, and Open-English node authoring.
Their evidence remains in BACKLOG; silence is not a carry.

## Direction after this cycle

[Compile the space before asking the question](DESIGN-compile-before-query.md)
is the chosen architectural direction after v0.14's frozen clarification
experiment.  It is not a v0.14 implementation item or release gate.  Its first
slice asks whether two existing exact worlds can compile and independently
check complete bounded possibility spaces before any target is selected.  The
design explicitly suspends corpus growth, pair-count growth, and obligatory
learned arms for that slice.  If its two-world or resource construction gate
misses, it parks rather than manufacturing a toy world.

## Governance

- Predictions, executable scorers, rows, controls, and provenance land before
  the candidate implementation.
- A holdout runs once.  Raw output lands before compact views.
- Closed-form request structure stays symbolic; no negative-weight ranker.
- A wrong BIND cannot trade against coverage.
- Every status lands in this roadmap, ANALYSIS, DISCOVERIES, and BACKLOG as the
  work lands.

## Release gate

v0.14 is ready only if:

- the 48-row protocol passes its construction, overlap, and provenance checks;
- Q1–Q6 are adjudicated once, with misses as prominent as fires;
- the resolver candidate ships only on the complete conjunction;
- fresh precision and comparable coverage are both reported;
- the full suite is green on a frozen tip with retained shard receipts;
- every unfinished item above ships or parks in writing.
