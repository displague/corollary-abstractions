# Registered check order for the WRITE staging gate

Status: **registered, not yet implemented.**  This document exists to be
committed *before* any check moves, because the reordering changes which check
refuses a candidate and that is what the tests assert on.  ROADMAP-v0.15 item 3.

## The measured problem

`test_write_stage` is 12,522.5 s of a 21,688 s suite — 57.7 %, more than every
other module combined — and its fixture overhead is 8.5 s, so this is real test
work rather than setup.  One `stage_write` call costs about 180 s and the
module makes roughly seventy of them.  The single worst test,
`ValidationAndDeltaTests.test_delta_declared_with_the_wrong_type_is_refused`,
spends **1,096.4 s rejecting six malformed dictionaries**.

The cause is exact and is not a slow algorithm.  `_compare_declared_delta`
takes the measurement as an argument, so `match_signatures.load_nodes` and
`build_report` have already run over 12,777 nodes by the time it is called.
Its first five refusals never read that measurement:

- the declaration is not a dict;
- the declaration carries unknown keys;
- the declaration omits required keys;
- a declared count is not an `int`;
- `new_typed_twin_partners` is not a list of strings.

Each of those is a fact about a dictionary the caller supplied.  None of them
needs the corpus.

## What moves

Split the function, and nothing else:

- **`_validate_declared_delta(candidate)`** — pure.  Raises
  `matcher_delta_prediction` for the five conditions above.  Reads no corpus,
  no snapshot, no measurement.
- **`_compare_declared_delta(candidate, measured)`** — unchanged in meaning.
  Keeps the value comparison, which genuinely needs the measurement.

The validator is called immediately before `_measure_matcher_delta`, at both
call sites.

## Why the refusal identities cannot move

This is the constraint that makes the change safe, and it is checkable rather
than asserted.

The only work skipped between the old position and the new one is
`_measure_matcher_delta` itself, which **measures and does not refuse**.  It
raises no `Refusal`.  So a candidate that previously reached the type check
still reaches it, with the same identity `matcher_delta_prediction`, and no
candidate reaches a check it did not reach before.

The 46 refusal assertions across 16 distinct identities in
`tests/test_write_stage.py` are the contract.  None of their identities change,
because the moved refusals keep the name they already raise.

## Why the trust boundary is not weakened

A staging gate must never let a candidate reach a check it currently never
survives to.  This reordering only ever refuses **earlier**: the set of
candidates that reach any given later check is unchanged or smaller.  Nothing
is skipped for an accepted candidate — acceptance still runs the measurement
and still compares values, because the value comparison is the thing that
cannot be done without the corpus.

## Registered expectation

The four type/shape refusals stop paying for a corpus pass.  On the numbers
above, the worst test should fall from 1,096.4 s toward the cost of six
dictionary inspections, and the module total should drop by roughly the number
of refusal-only `stage_write` calls times ~180 s.

**No figure is frozen here beyond the direction**, because the count of
refusal-only calls has not been measured.  What is registered is the
falsifiable claim: *module wall clock falls materially and all 46 refusal
assertions keep their current identities.*  If identities move, the change is
reverted rather than the tests updated.

## Non-claims

- No claim that the suite becomes affordable; the parallel floor is this one
  module and it will still dominate.
- No claim about `test_corpus_analogy_split`, whose 3,434 s of per-class
  fixture rebuild is a separate and unblocked lane.
- No change to what any check decides, only to when it runs.

## Measured outcome

**Registration was wrong about the size, right about the direction.**  The
document first said four pure refusals; the `new_typed_twin_partners` list
check is corpus-independent too, so it is five.  Corrected above rather than
left right-in-code and wrong-on-paper.

| | before | after |
|---|---|---|
| `test_delta_declared_with_the_wrong_type_is_refused` | 1,096.4 s | **46.2 s** |
| `tests.test_write_stage` (103 tests) | 12,522.5 s | **10,770.9 s** |

All 103 tests pass and every refusal assertion keeps its identity, which was
the contract.

The module drop is **14 %**, far less than the defect's shape suggested, and
the reason is worth recording: only the *declared-delta* refusals were paying
for a corpus pass.  The other identities — `declarative_seed` with ten
assertions, `seed_ownership`, `path_containment` and the rest — already refuse
before the measurement.  Seven assertions were over-paying, not forty, and the
worst test alone accounts for about 1,050 s of the 1,752 s saved.

**The comparison is indicative, not a receipt.**  The 12,522.5 s figure was
measured by `plan_test_shards` in an isolated checkout at a frozen tip with
bytecode writing disabled; the 10,770.9 s figure was a plain `unittest` run in
a working tree.  A like-for-like number needs the gate tool re-run at the
v0.15 tip, and the release gate will produce one.

What this does not do is change the parallel floor.  At 10,770.9 s this module
is still the largest by an order of magnitude and still sets the wall clock for
any shard count.  The next lever is the one already parked: the split fixture's
179.3 s rebuild, paid once per class rather than once per module.

