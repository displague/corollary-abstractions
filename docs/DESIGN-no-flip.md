# NO-FLIP — served-answer regression census

**Status: design draft.** This is v0.23 rider R-NF, the regression-only
residue of NO-FLIP. It does not reopen ERRATUM's improvement arm: R3 measured
a byte-identical corpus window, so there is no new library growth to credit.

## 1. Question

When the same recorded answering turns are served by today's program, does the
person receive a rendering with the same SHA-256 digest?

This is deliberately narrower than semantic equivalence. A changed member
order, changed witness route, or changed wording is visible to the person even
when both answers remain mathematically valid. R-NF calls that a regression
candidate and publishes it for adjudication; it does not canonicalize the
difference away.

## 2. Frozen population and denominator

The population is every turn in the 60 committed
`experiments/sessions/v021-s*.json` journals, excluding `.reads.json`, whose
recorded `result.kind` is in the shipped answering-status intersection:

| recorded kind | count |
|---|---:|
| `solved` | 160 |
| `found` | 60 |
| **answering total** | **220** |

The 110 `waiting`, 60 `refused`, 10 `exhausted`, and 10 `canceled` turns are
reported as excluded strata and are never pooled into the 220 denominator.
HANDBACK owns typed non-answer turns; ERRATUM already owns refusal-to-answer
flips. R-NF must not improve its result by changing this boundary after replay.

The journals' recorded `answer_bytes_digest` values are the historical side.
The live side is recomputed through the existing `CoreSession`, assumption
rebuild, `route_line`, and `session_ledger.answer_bytes_digest` path. Replay
uses the journal's own pins while separately reporting genuine live pin drift,
exactly as ERRATUM disclosed; otherwise the staleness gate would replace the
answer census with an environment-drift census. MACs remain unverified on this
path, so R-NF makes no authentication or forgery claim.

The 220-turn cohort never changes, but its live outcomes have a frozen,
disjoint classification. A live status in
`{solved, found, held, PROVEN, VERIFIED}` is `ANSWER_RETAINED` and proceeds to
the digest comparator. Every other live status is `ANSWER_LOST`; it remains in
the 220 denominator, is always a regression candidate, and is reported
separately from retained-answer digest mismatches. This is R-NF's answer-loss
case, not ERRATUM's refusal-to-answer direction and not HANDBACK's population
of turns that were already recorded as non-answers.

## 3. Comparator and the named residual risk

The primary comparator is literal equality of the recorded and live SHA-256
digests of the complete rendered answer bytes. It has no normalization table
and no learned judgment. A mismatch proves the rendered bytes changed. A match
is digest identity with SHA-256's negligible collision risk, not a mathematical
proof of byte identity. Neither outcome says the old or new answer is false.

Two capability-blind controls make the comparator choice visible:

1. **Shape-only:** compare only `(route, status)`. This represents the
   canonicalizing family the course review warned about: it can call two
   visibly different but equally valid answers identical.
2. **Always-changed:** label every pair changed. It detects every planted
   mutation but must also label all 220 unchanged self-pairs changed, proving
   that mutation sensitivity alone is vacuous.

The artifact reports primary and both controls separately. No aggregate score
combines them.

## 4. Sensitivity plants, fixed before the census

The plant source is the live answer to
`twin programming.euclid.recursive`, whose answer contains two member lines and
one ledger line. The source must still answer and must contain exactly those
three semantic rows before either mutation is accepted.

The two deterministic mutations preserve the same members and ledger:

- **MEMBER_ORDER:** reverse the two member rows.
- **LEDGER_POSITION:** move the ledger row before the member rows.

Both mutations are person-visible and set-equivalent to the source answer.
Before any comparator runs, a closed-form equivalence gate extracts the
`member` and `ledger` rows from the unmutated and mutated answer tuples and
requires identical row multisets, no duplicates, no additions or deletions,
and byte-identical non-answer fields. `MEMBER_ORDER` must differ only by the
reversal of the two member positions. `LEDGER_POSITION` must differ only by
moving the one ledger row before the unchanged member sequence. A miss is
`INVALID_PLANT` and stops before replay.

The exact comparator must detect 2/2. Shape-only must detect 0/2. The
always-changed control must detect 2/2 mutations and falsely mark 220/220
unchanged self-pairs. If any of those expectations misses, the real census is
`INVALID_CONTROL` and no real stability sentence is published.

## 5. Registration and ordering

Before the census runs, one commit must contain:

- `experiments/no_flip_prereg.json`, including the population counts, journal
  manifest digest, writer digest, mutation source, comparator definitions, and
  all gates below;
- `scripts/no_flip_census.py`;
- `tests/test_no_flip_census.py`.

The writer refuses a dirty tree, refuses unless those three registration inputs
were introduced by the current commit, revalidates every frozen digest before
replay, and creates `experiments/no_flip_census.json` once without replacement.
The result artifact lands only in a strict descendant commit. This is explicitly
a **commit-ordered registration** claim: Git proves the registered artifact did
not yet exist in that history. It cannot prove nobody privately explored the
same computation, and R-NF makes no stronger claim.

## 6. Gates and stop rules

- **B1 — population.** Exactly 60 journals, 410 total turns, and the frozen
  `160 solved + 60 found = 220` answering partition. Any discrepancy is
  `PREREGISTRATION_DISCREPANCY` before replay.
- **B2 — exact comparator sensitivity.** Both equivalent-render mutations are
  first proven equivalent by the closed-form multiset/order gate, then
  detected, 2/2.
- **B3 — hostile controls.** Shape-only detects 0/2; always-changed detects
  2/2 plants and falsely flags 220/220 unchanged self-pairs.
- **B4 — accounting.** Retained-answer digest matches, retained-answer digest
  mismatches, and `ANSWER_LOST` rows sum to 220; every journal and answering
  turn has exactly one receipt row.
- **B5 — no hidden canonicalizer.** The primary comparator implementation is
  pinned and accepts only the two recorded/live hex digests; it does not read
  answer structure, route, status, statement ids, or a lexicon.
- **B6 — publication completeness.** Every digest mismatch and `ANSWER_LOST`
  row is published member by member with session id, turn index, input bytes,
  recorded kind, recorded digest, live digest, live route, and live status.
  The published red-row count must equal retained-answer mismatches plus
  `ANSWER_LOST`; any absent field or row is `INVALID_ACCOUNTING`.
- **B7 — red-capable outcome.** Zero is published as
  `0/220 byte regressions in this recorded window`, never “answers cannot
  regress.” A nonzero count publishes with the same denominator and complete
  B6 rows. Neither outcome is a pass condition.

B1–B6 must fire for the census to be interpretable. A miss stops with
`INVALID_CONTROL`, `INVALID_ACCOUNTING`, or
`PREREGISTRATION_DISCREPANCY`. B7 is an outcome, not a pass condition: zero or
nonzero both publish.

## 7. Claims and non-claims

R-NF may claim only the rendered-answer digest regression count over these 220
recorded answering turns, plus the measured behavior of its controls. It makes
no claim about unrecorded sessions, waiting/canceled/refusal turns, semantic
correctness, mathematical equivalence, user preference, corpus improvement,
authentication, collision-free equality, or future stability. The detector is
retained as the ERRATUM lane's future regression instrument; a future run
requires a new registered window rather than overwriting this one.
