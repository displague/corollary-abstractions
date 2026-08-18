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
synonym table.  Before parsing, apply Unicode NFKC, casefold, collapse
whitespace only, and trim; punctuation is not erased.  A negative row must then
full-match the literal Python regex
`^(?P<positive>.+?) without (?P<term>[a-z0-9]+(?: [a-z0-9]+)?)$`, where TERM
is one or two ASCII tokens.  Reject the match if `positive` matches the
boundary regex `(?<![a-z0-9])without(?![a-z0-9])`.  Thus multiple markers,
including ones adjacent to punctuation, conjunction after TERM, and
punctuation after TERM are malformed rather than silently normalized.
`without` and that suffix are removed to form the negative-stripped ablation.
Set `required_tokens = tuple(reduce_text(TERM))` once and use that tuple for
construction checks, veto inventory, and scoring; an empty tuple is malformed.
A candidate requires TERM exactly when every required token occurs in the
union of `reduce_text` tokens from that candidate's
committed title, statement meaning, keywords, and `symbol_lexicon` values.  A
required candidate is vetoed; every other candidate is unchanged.  The
preregistration commit must contain the executable parser/veto skeleton and
this complete inventory.  Candidate code may implement only that frozen
algorithm—no row-specific licenses, mappings, exceptions, or new marker forms.

The veto acts **inside resolution before candidate selection**, not on a
resolver's returned tuple.  Parse the suffix, remove it to obtain the positive
payload, and pass the veto-id mask into the resolver.  All membership,
known-word, document-frequency, graph-size, posting, and ordering checks see
the original graph.  Expression, literal-id, and every word-based candidate
admission or accumulation path alone skips masked ids.  Masking the last owner
of a known word therefore cannot make that word unknown or change any
unmasked candidate's eligibility or score.  When an exact resolver recognized
the positive payload before masking but has zero allowed candidates, it
terminally PASSes rather than falling through to a weaker resolver.  Resolve
the positive payload exactly once.  There is no resolve-then-filter path and
no fallback or retry against the unmasked graph.  TERM is malformed when
`reduce_text(TERM)` is empty, or when the positive payload has no reduced
tokens; this prevents an empty-token universal veto or vacuous query.  At
construction time every negative row must veto at least one committed id and
must veto neither its primary id nor any retained id.  The stripped ablation
resolves the identical positive payload once with an empty mask.

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
- allowed follow-up class: `corpus`, `discipline`, or `word` (never `id` in
  this scored holdout);
- the complete set of intended ids that must survive the follow-up;
- whether negative/exclusion structure is present;
- a short author rationale that cannot be used by the scorer.

The 38 in-corpus rows have 38 distinct primary ids.  No score-credit-bearing
primary or retained id may occur in the complete forbidden union from earlier
sets, and no id may be reused across new rows.  ASK rows declare a nonempty
`retained_ids` set containing their primary id.  BIND and PASS rows declare no
retained ids.  Q3, Q5, blind initial credit, and every non-Q2 metric credit only that one
`primary_id`; Q2 alone uses and requires every declared retained id.  New
queries must also be mutually below the 0.50 trigram-Jaccard ceiling.
Construction does not inspect or
require candidate tuples; an absent primary or dropped retained id remains a
scored miss.

Every primary and retained id must exist exactly once in the merged `data/`
graph, never in `data_holdout/`; nodes from either
`decompose.INGESTED_CORPUS_PREFIXES` corpus (`lean_workbook` or
`ingested_arithmetic`) are ineligible.
The 38 primary ids span at least 10 top-level id prefixes, with no prefix used
by more than 6 rows.  The blind universe remains the complete sorted id set
from `data/`, including ids that are ineligible as authored targets.

The 20 ASK rows freeze 20 distinct primary ids and an exact follow-up-class
profile: 6 `corpus`, 6 `discipline`, and 8 `word`.  The structural validator
enforces those declarations.  This is a score-time capability profile, not a
license to inspect candidate tuples during construction.  The one-shot ledger
reports Q2 by class, including post-follow-up survivor sizes and singleton
counts.  In addition to retaining every declared id, halving must
fire on at least 5/6 corpus rows, 5/6 discipline rows, and 6/8 word rows as well
as 15/20 overall.  All 20 observed initial candidate tuples must be distinct;
at least 10 must contain four or more candidates and at least 4 must contain
eight or more.  Any profile miss fails Q2 and the shipping conjunction without
replacement.  Every observed initial ASK set must also contain at most 25 ids;
exceeding the registered reciprocal-load budget is a scored Q2/profile miss,
never a reason to replace the row.

Provenance has two chronological layers.  The preregistration manifest pins
every already-existing score-affecting Git object and enumerates the only
paths the later candidate commit may change; it cannot self-pin or invent a
future object id.  The raw one-shot ledger later pins the preregistration
commit/tree, candidate commit/tree and changed blobs, runtime, and canonical-LF
digests, and verifies that the candidate diff is clean and confined to those
declared paths.  Any mismatch refuses scoring.

The executable scorer, schema tests, holdout rows, source digests, and blind
baseline land in the same preregistration commit.  The mechanical arm uses
OEWN archive SHA-256
`7d749f6e2c39e6970e4997839dcf6e42fd281f3c2fae0171d2192bae8cfa4b51`,
seeds **20260825**, **20260826**, and **20260827**, and
`random.Random(seed).sample` over sentences sorted by
their stable OEWN key.  A key is `(synset_id, source_field, ordinal)`, where
`source_field` is `examples` or `definitions` and `ordinal` is the zero-based
position in that field.  Canonically reconstruct the v0.13 F4 pool with its
pinned historical commit/tree, scorer Git blob
`32dc0a0d45474dc5f2ba9d06d9f6f40e8fddb685`, WordNet-index dependency blobs,
and the current disclosed CPython runtime: visit sorted synset ids, then
examples followed by definitions, collapse whitespace with
`" ".join(text.split())`, accept lengths 20 through 120 characters inclusive,
and retain only the first acceptable sentence per synset.  CPython's committed
`random.Random(20260818).shuffle` produces the canonical 1,000-key exclusion.
The original run did not retain its keys or Python runtime, so identity with
the historical lost 1,000 is not claimed.  Conservatively exclude both the
canonical keys and every entry whose normalized text equals any of the 34
published F4 claimed texts.  All 34 published texts must be found in the pinned
archive, whether or not they occur in the canonical runtime reconstruction.
For v0.14, build the same one-per-synset pool, remove those exclusions, then
deduplicate the
survivor pool by normalized text while keeping its lexicographically first
three-part key.  Sort those unique survivors lexicographically by key.  In
seed order, apply CPython's `random.Random(seed).sample(pool, 1000)`, then
exclude every selected key and normalized text before constructing the next
arm.  The three 1,000-row arms are mutually disjoint and disjoint from the
recoverable canonical/text exclusions.  Absolute overlap with F4's 966
unpublished historical non-claims is unprovable.  The preregistration records
the Python implementation/version,
spent and prior-arm exclusion counts, and each ordered selected-key digest,
but no licensed sentence text or reversible stable-key payload.  Exact keys
are reconstructed only from the external pinned archive.  Any row-level
reconciliation uses one-way key digests.  Those choices land in that commit
too.  The candidate implementation lands second.  The holdout and three
mechanical arms run once.  Their raw ledger likewise excludes licensed text
and keys and is committed before any compact view.

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
protocol failures.  A `primary_id` absent from the initial candidate set is a
Q1/Q5 miss.  A declared `retained_id` removed by its follow-up is a Q2 miss.
Both stay in their denominators and in the raw ledger.

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
load**: `1/k` when the row's `primary_id` is present in an arm's `k` returned ids,
otherwise 0.  The reported summary is the arithmetic mean over all 38
in-corpus rows.  The resolver arm uses its complete BIND/ASK candidate set and
the same rule.  For **either** arm, `k=0` or `k>25` scores 0; otherwise the
`primary_id` scores `1/k`.  PASS scores 0.  Thus a full-graph answer is
over budget and inclusion alone cannot pass.

For each of the 20 clarification rows, the blind follow-up stage stays inside
its initial 25 ids, computes title-token Jaccard against the normalized exact
follow-up's VALUE string.  It obtains that string by applying the runtime's
exact `_context_constraint` parse and stripping only the literal
`narrow CLASS` prefix; normal normalization and tokenization then apply, with
no further namespace stripping.  It retains every id with score greater than
zero, ordered by that score then id.  If none score above zero it preserves
the initial 25, matching
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
- **Q4 — precision does not pay.** Across three fresh, mutually disjoint
  pinned-OEWN 1,000-sentence arms, pooled false positives are at most the
  v0.12 shipping ceiling, **0.030**.  Each seed's rate, the pooled 3,000-row
  rate, mean, and dispersion remain public; no weak seed is replaced.
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
