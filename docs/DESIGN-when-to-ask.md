# When should it ask? — a fresh clarification protocol

Status: **design for v0.14; no holdout rows authored and no scores run.**
Written after v0.13's coverage/context audits and before the v0.13 release
blog.  This document registers the protocol that the next roadmap depends on.
The concrete holdout, executable scorer, and provenance manifest must be a
separate Git commit before the implementation and result commits.  Git proves
that ordering; it cannot prove what somebody ran locally before committing,
so the eventual report must retain that limitation.

## 1. The accident that forces the question

v0.13's candidate resolver reached 24/24 questions and still could not ship.
It confidently mapped “interest accumulated **without** compounding” to
continuous compounding, while a fresh mechanical false-positive arm rose from
the shipping ceiling of 0.030 to 0.034.  Coverage was not correctness.

The same cycle found ASK on 16/62 registered in-corpus questions and built a
bounded clarification loop.  But A2 could not be scored honestly: the two
spent holdouts froze initial questions, not their continuation lines or the
reading that each continuation must retain.  Authoring those fields after
candidate inspection would make the evaluator an oracle.

The next question is therefore not “how do we bind more?” It is:

> Can an exact negative constraint turn a confident contradiction into ASK or
> REFUSE, and can one follow-up frozen with the query narrow the candidate set
> without losing its intended reading?

## 2. Representation before ranking

Negation and exclusion are closed-form request structure.  The resolver may
extract a typed constraint such as `exclude(compounding)` only when a declared
surface rule licenses it.  The constraint is a veto: a candidate explicitly
requiring the excluded concept cannot BIND.  It is not negative weight in a
score and it cannot make another candidate win by relative advantage.

The first protocol deliberately freezes one grammar rather than an expandable
synonym table.  A negative row ends in the exact normalized suffix
`without TERM`, where TERM is one or two `[a-z0-9]+` tokens and no conjunction
or punctuation follows it.  `without` and that suffix are removed to form the
negative-stripped ablation.  A candidate requires TERM exactly when every TERM
token occurs in the union of `reduce_text` tokens from that candidate's
committed title, statement meaning, keywords, and `symbol_lexicon` values.  A
required candidate is vetoed; every other candidate is unchanged.  The
preregistration commit must contain the executable parser/veto skeleton and
this complete inventory.  Candidate code may implement only that frozen
algorithm—no row-specific licenses, mappings, exceptions, or new marker forms.

The allowed outcomes remain BIND, ASK, and PASS.  After every veto, zero
survivors deterministically PASS, one BINDs, and more than one ASK.  The
resolver never erases the word and retries.  The existing P-LS6 loop may then
intersect that exact set with one declared `corpus`, `discipline`, `word`, or
`id` constraint.

## 3. The fourth conversational holdout

The new holdout contains **48 rows in four fixed primary strata**:

- 16 in-corpus negative/exclusion rows: 8 expected BIND and 8 expected ASK;
- 12 ordinary ambiguous in-corpus rows expected ASK;
- 10 ordinary non-negative in-corpus rows expected BIND;
- 10 out-of-corpus rows expected PASS.

Thus Q1 has 16 rows, Q2 has 20 ASK rows, and the in-corpus reach/target
denominator is 38.  A shortage in any stratum refuses shipping; it does not
resize the denominator.  The holdout is authored once and committed before
the candidate implementation.  Every row contains all of:

- initial query;
- expected route: BIND, ASK, or PASS;
- intended statement id, or an explicit `none` for refusal rows;
- exact follow-up line, where clarification is expected;
- allowed follow-up class;
- the complete set of intended ids that must survive the follow-up;
- whether negative/exclusion structure is present;
- a short author rationale that cannot be used by the scorer.

The executable scorer, schema tests, holdout rows, source digests, and blind
baseline land in the same preregistration commit.  The mechanical arm uses
OEWN archive SHA-256
`7d749f6e2c39e6970e4997839dcf6e42fd281f3c2fae0171d2192bae8cfa4b51`,
seed **20260825**, and `random.Random(seed).sample` over sentences sorted by
their stable OEWN identifier; those choices land in that commit too.  The
candidate implementation lands second.  The holdout and mechanical arm run
once.  Raw output is committed before any compact view.

Freshness is checked mechanically.  Normalize with Unicode NFKC, casefold,
replace every non-alphanumeric run by one space, and trim.  No normalized
query may equal a development/holdout-1/holdout-2/holdout-3 query, and
character trigram Jaccard similarity to every prior query must be below
**0.50**.  The preregistration scorer runs the committed v0.13 resolver over
all four prior sets and freezes the union of every BIND id, every ASK candidate
id, and every holdout-3 registered target as `forbidden_intended_ids`; none of
the 38 new intended ids may occur in that union.  The scorer emits the complete
text and id overlap report.  A row that violates a bound invalidates the
protocol before scoring; no replacement is allowed after any score is seen.

Wrong row counts, unknown classes, duplicate queries, overlap violations,
missing inputs, dirty score-affecting code, or provenance mismatch are hard
protocol failures.  An intended id absent from the initial candidate set is a
Q1/Q5 miss.  An intended id removed by its follow-up is a Q2 miss.  Both stay
in their denominators and in the raw ledger.

## 4. Capability-blind controls

Literal title inclusion was too weak: it “recalled” one row by returning
14,571 ids.  The next blind arm must pay for candidate volume.

For every in-corpus row each arm reports target retention and candidate count.
The **blind arm** tokenizes the normalized initial query and each committed
statement title with `[a-z0-9]+`, scores token-set Jaccard, sorts descending by
score and then ascending by statement id, and returns the first **25** ids.
Its universe is the exact sorted statement-id set from merged `data/` only
(never `data_holdout/`), frozen with canonical-LF source and combined digests
in the preregistration manifest.
No stopword list, glossary, corpus field, resolver index, follow-up, or
negative marker is visible.  The target score is **reciprocal candidate
load**: `1/k` when any intended id is present in an arm's `k` returned ids,
otherwise 0.  The reported summary is the arithmetic mean over all 38
in-corpus rows.  The resolver arm uses its complete BIND/ASK candidate set and
the same rule.  For **either** arm, `k=0` or `k>25` scores 0; otherwise a
retained intended id scores `1/k`.  PASS scores 0.  Thus a full-graph answer is
over budget and inclusion alone cannot pass.

For each of the 20 clarification rows, the blind follow-up stage stays inside
its initial 25 ids, computes title-token Jaccard against the normalized exact
follow-up, and retains every id with score greater than zero, ordered by that
score then id.  If none score above zero it preserves the initial 25, matching
the runtime's no-guess zero-match rule.  Its halving-and-retention statistic is
computed identically to Q2.  Ties never disappear through an arbitrary top-1.

The **negative-stripped ablation** deletes only each row's declared negative
span, retains every positive token, and runs the candidate resolver unchanged.
It is adjudicated separately below; it cannot be cited as a causal control if
its registered prediction misses.

## 5. Registered predictions

- **Q1 — contradictions stop binding.** Wrong single BINDs on negative or
  exclusion rows are **0**.  The v0.13 spent sentence is never a scored row;
  it is a public regression only.  On the 16-row negative stratum, at least
  **14/16** intended ids remain reachable (BIND or ASK) and at least **14/16**
  routes equal their frozen expected route, preventing blanket abstention.
- **Q2 — clarification retains the intended reading.** On every row expected
  to ASK, the frozen follow-up retains every declared intended id and reduces
  the candidate set by at least half on at least **75%** of rows.
- **Q3 — the blind arm is materially weaker.** Resolver mean reciprocal
  candidate load exceeds the 25-id blind arm by at least **0.10**, and the
  blind arm does not meet Q2's halving-and-retention bar.
- **Q4 — precision does not pay.** On a fresh pinned-OEWN 1,000-sentence arm,
  false positives are at most the v0.12 shipping ceiling, **0.030**.
- **Q5 — coverage does not pay.** BIND-or-ASK reach on the 38 fresh in-corpus
  rows is at least **0.833**, directly comparable to the v0.12 shipping
  figure.  Separately, registered-target recall is at least **0.833**; that is
  a new v0.14 correctness floor, not the old coverage metric.
- **Q6 — exclusion changes the decision.** The negative-stripped ablation
  produces at least **4/16** single BINDs to candidates that the full query's
  declared TERM would exclude, while the full arm meets Q1.  If it does not,
  this experiment cannot attribute the result to negative structure.

The shipping conjunction is Q1 through Q6.  Every denominator above must be
nonzero and exactly its registered size.  A coverage increase cannot trade
against a wrong BIND or a precision miss.  If any clause misses, the candidate
resolver does not ship; every result and miss does.

## 6. Vacuity and interpretation

Before the one-shot run, synthetic tests must prove that:

1. removing negative structure makes at least one authored construction
   impossible to distinguish, without using a spent row;
2. a full-graph blind answer fails the candidate budget;
3. a follow-up that halves the set while dropping the intended reading fails;
4. zero matches preserve ASK or PASS rather than manufacturing a winner;
5. all result fields derive from the raw ledger and score-affecting Git objects
   are digest-pinned with canonical-LF hashing.

This design does not promise general language understanding, a learned
ranker, or Buffalo syntax.  It asks whether one exact failure mode earns a
better decision boundary and whether the already-shipped clarification state
can be evaluated without an oracle.

## 7. Stop conditions

Do not patch a spent miss, add `without` to stopwords, tune thresholds after
the fresh run, or author a fifth holdout in the same cycle.  If the conjunction
misses, park the implementation and use the failure to design a later question.
If the executable protocol is not committed before the rows are run, the
measurement is exploratory and cannot satisfy this design.
