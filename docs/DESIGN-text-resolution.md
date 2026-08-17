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

## 4. What this design does not claim

- Not open-domain question answering. Outside the corpus the honest output is
  a refusal, and the refuse arm exists to keep that true.
- Not comprehension. The resolvers match words and structure. `owns x ^ 2`
  and "what is the cosine of a double angle" both work by lookup.
- Not multi-turn. P-LS6 stays parked; one line, then stop.
- Not a ranker. Where the query cannot separate candidates, the system asks
  with the candidates named. That seat stays empty on purpose.
