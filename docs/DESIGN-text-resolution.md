# Design — arbitrary text in, a checkable answer out (v0.13)

Registered **before** `scripts/measure_text_resolution.py` was run against
`experiments/text_resolution_queries.json`. The query set was authored first
and deliberately not by copying node titles, which would measure string
equality rather than resolution.

## 1. The goal, stated so it can fail

v0.13 should accept arbitrary text and return a response that is
**intelligible, passably correct, factual, logical, and grammatical** —
without an LLM and without canned template prose.

Three of those five are settled by construction rather than by effort, and
saying how is the whole design:

| property | how it is obtained | how it could still fail |
|---|---|---|
| grammatical | every sentence is lifted verbatim from committed corpus prose a person wrote and a schema validates | the corpus contains a badly-written sentence |
| factual | every sentence is attributed to the `statement_id` it came from; nothing is paraphrased | the corpus contains a false statement |
| logical | relations are `inferential_links` edges the corpus asserts and `validate_nodes` checks for reciprocity | an edge is wrong in the corpus |
| intelligible | the answer is ordered as a reference entry: what it is, what it says, how it is written formally, what it connects to | ordering is poor, or the quoted prose is boilerplate |
| correct | **the resolver picked the right statement** | ← this is the only one that is genuinely open |

So the measurement is aimed where the risk actually is: **resolution**, not
rendering. Rendering cannot invent a false sentence because it cannot write
one.

## 2. What is being measured

`resolve` queries: 28 phrasings of things the corpus contains, written as a
person might type them. `refuse` queries: 12 fluent, well-formed English
sentences about things the corpus does not contain.

The refuse arm is the load-bearing half. A resolver that claims everything
scores perfectly on coverage and is worse than useless, because it turns an
honest `exhausted` into a confident wrong answer. That failure was already
observed once during v0.12 (a single stray word `velocity` "resolving" a
Monty Python joke to two statements), which is why the control set exists at
all.

## 3. Registered predictions

- **T1 (coverage).** At least **70%** of `resolve` queries reach a statement
  (BIND or ASK). Below that, arbitrary text is not usefully supported and the
  claim fails regardless of how good the answers look.
- **T2 (refusal).** At least **90%** of `refuse` queries PASS to the
  dispatcher. This is deliberately stricter than T1: claiming something the
  corpus does not contain is a worse failure than missing something it does.
- **T3 (no silent guessing).** Of the `resolve` queries that BIND, **100%**
  bind to a statement whose corpus prose actually contains the matched query
  words. A BIND that cannot show its words is a guess wearing an id.
- **T4 (answers are quotations).** For every BIND, every sentence in the
  rendered answer appears verbatim in the committed corpus. Not a rate — any
  counterexample is a failure, because it would mean the renderer authored a
  claim.

T2 and T4 are the ones that must hold. T1 missing means "not ready yet"; T2
or T4 missing means the thing is *unsafe*, and no coverage number redeems it.

## 4. Adjudication

Run 1, against the rules as committed when T1–T4 were registered
(`experiments/text_resolution.json`):

| | result | threshold |
|---|---|---|
| **T1** coverage | **FIRED** — 0.9643 (27/28) | ≥ 0.70 |
| **T2** refusal | **FIRED** — 0.9167 (11/12) | ≥ 0.90 |
| **T3** shows its words | **FIRED** — 19/19 | all |
| **T4** verbatim quotation | **FIRED** — 19/19 | all |

All four fired as registered. Two failures were visible inside those
numbers and both are recorded rather than rounded away:

- **A false bind.** `translate this sentence into portuguese` bound to
  `provability.consistency.consistency_definition`, corroborated by
  `['into', 'sentence']` — "sentence" is a logic term, "into" a
  preposition. Two weak words agreeing, covering half the query.
- **A miss.** `greatest common divisor euclid` did not resolve; the corpus
  writes `gcd`.

**Post-hoc, and labelled as such.** After seeing that failure the rule was
tightened: closed-class function words were added to the stopword list, and
a match must now account for at least 60% of the query's content words
(`COVERAGE_FLOOR`) rather than merely having two words agree. The rationale
is stated in the code — *if half the query is unexplained, the half that
matched is a coincidence*. Re-run in
`experiments/text_resolution_posthoc.json`: **T2 rises to 1.000 (12/12)
with coverage unchanged at 0.9643**. This second run is NOT the registered
result; T2 is recorded as 0.9167 because that is what the committed rules
produced when the prediction was scored. The improvement is reported as an
improvement, not backdated.

The `gcd` miss is left standing. Fixing it means a synonym layer, which is
a design and not a patch.

## 5. Correction: fabrication is a frame, not a refusal

The first version of this design had two dispositions — resolve, or refuse
— and that was wrong. Arbitrary text wants conjecture, hypotheticals,
opinions and deliberate fiction. A system that refuses all four is honest
and useless; one that answers them as facts is dishonest. There is a third
option, and the project already had it: hold the claim in a **frame**, where
the check is consistency with the frame's premises rather than truth.

The corpus is already built for this. `narrative.frames.cartoon_gravity` is
a committed Frame Declaration; the narrative corpus carries story structure,
Chekhov's Gun and the no-deus-ex-machina condition as statements;
`epistemic_status` already ranges over `formal`, `derived`, `assumed`,
`conjectured`. A story is not an exception to the graph — it is a region of
it with different rules.

So there are three dispositions, not two:

| the text | route | status |
|---|---|---|
| grounded in the corpus | resolver → quoted answer | `solved` |
| conjecture, fiction, opinion | `suppose …` → a frame you own | `conjectured` |
| neither | dispatcher | `exhausted`, **and it offers the frame** |

`FrameSpec.on_exit` is `conjectured`, so nothing typed into a supposition
can leave as a fact. `open_frame` refuses a frame that declares a
contradiction and `assert_literal` refuses a claim contradicting one already
held — consistency is enforced by the executor, not by care. And the
unresolved branch no longer dead-ends: it names the `suppose` route rather
than taking it silently, which is the difference between *holding* a
supposition and *inventing* one.

**Not yet reachable:** contradiction between two typed claims. The executor
supports it; the surface does not, because P-LS6 keeps the session to one
line. Named here rather than left for a reader to discover.

## 6. What this design does not claim

- Not open-domain question answering. Outside the corpus the honest output is
  a refusal, and the refuse arm exists to keep that true.
- Not comprehension. The resolvers match words and structure. `owns x ^ 2`
  and "what is the cosine of a double angle" both work by lookup.
- Not multi-turn. P-LS6 stays parked; one line, then stop.
- Not a ranker. Where the query cannot separate candidates, the system asks
  with the candidates named. That seat stays empty on purpose.
