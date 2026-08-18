# Verified ambiguity — a row may not assert what the corpus can deny

Status: **draft for v0.15; no rows authored, nothing measured.**  Written
after v0.14's Q2 missed at 3/20, and deliberately before any v0.15 holdout
exists, so that the rule constrains the authoring rather than describing it.

## The failure this answers

v0.14 registered twenty rows predicted to ASK.  Four asked.  Eight bound
straight to the intended id, five bound elsewhere, three passed on vocabulary
the graph does not contain.  Meanwhile the eighteen rows that predicted *no*
ambiguity scored 18/18 on target recall.

So the failure was not distributed across the protocol; it sat entirely in
rows authored on the belief that the graph was ambiguous.  Their evidence for
that belief was a prose rationale — "several quadrilateral readings remain" —
which the scorer was explicitly forbidden to read.  Nothing anywhere checked
whether the corpus actually offered a second reading.

Q2 then scored "answered correctly without needing to ask" identically to
"answered wrongly", because a row that does not ASK has no follow-up, and a
row with no follow-up retains nothing.  Eight correct answers were recorded
as clarification failures.

## The constraint that makes it checkable

A checker that resolved the query would be worse than no checker.  Rows
verified against the resolver are rows authored to match the implementation,
which is the oracle every part of this discipline exists to prevent.

So the criterion must be **capability-blind**, and one already exists and is
already published: v0.14's control arm, which tokenizes committed titles with
`[a-z0-9]+`, scores token-set Jaccard, and sorts by score then id.  It is
reused here rather than restated, so there is one definition of blind.

## What a v0.15 ASK row must declare

Two id sets instead of one:

- `retained_ids` — readings that must survive the follow-up;
- `competing_ids` — readings the corpus really offers that the follow-up
  must eliminate.

v0.14 had only the first, and every one of its twenty ASK rows set it to a
singleton equal to the primary.  Its validator's fixed 58-credit shape in
fact *refused* a larger set, so Q2's "retains every declared id" clause was
equivalent to "retains the primary" and could never have tested anything
else.

## The four checks

1. **Competitors are named.**  An ASK declaring no `competing_ids` is a BIND
   that has not admitted it.
2. **The corpus does not already settle it.**  If the intended reading is the
   strictly best blind title match among the declared set, the graph
   discriminates and the honest prediction is BIND.
3. **Every declared reading is blind-visible.**  A reading outside the blind
   horizon for its own query is one only the author can find.
4. **The follow-up narrows.**  Applying it must keep every `retained_id` and
   eliminate at least one `competing_id`.  v0.14 checked only the first half,
   so a follow-up that changed nothing scored as a success.

Checks 2 and 4 read committed metadata only.  No resolver is constructed and
no query is resolved.

## What check 2 is measured to do

Run against v0.14's twenty ASK rows — the only rows that exist to test it
against — check 2 alone:

- refuses **0 of the 4** rows that genuinely asked;
- refuses **7 of the 16** that did not, including **5 of the 8** that bound
  straight to their intended reading.

It is therefore a one-sided filter: it does not cost a correctly-authored
row, and it removes a bit under half of the mis-authored ones.  That is worth
having and is **not sufficient alone**; checks 1, 3 and 4 are expected to
carry the rest, and cannot be validated this way because v0.14 rows carry no
`competing_ids` to check.

A richer criterion was tried and rejected on measurement.  Scoring against
each node's full committed inventory — title, meaning, keywords and glossary,
the same fields the exclusion veto reads — caught **fewer** bad rows (6 of 16)
and refused one row that genuinely asked.  Titles-only both performs better
and stays further from the resolver's own evidence, which is the property
that keeps this a construction check rather than an oracle.

## What this does not claim

It does not claim v0.15 will pass.  It does not predict a clarification
result, and it is not itself a shipping clause.  It is a refusal: a row whose
ambiguity the corpus denies cannot be committed, so the one-shot cannot be
spent measuring narrowing on a set that was never wide.
