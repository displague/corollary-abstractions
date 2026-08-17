# Design — ambiguity, context, and comprehension checks (for ROADMAP-v0.13)

Written during v0.12 release triage, after H1–H6 were graded, as the
cycle's forward-looking design. It rests on something v0.12 produced by
accident rather than on an extrapolation of the plan.

## 1. The accident this comes from

v0.12's conversational surface was supposed to be one typed line reaching
two existing programs. What it actually produced, and nobody designed for,
is a resolver that **routinely returns candidate sets and asks**:

```
$ python scripts/resolver.py "parity"
10 statements match ['parity']
ambiguous: 10 candidates
  ? numbertheory.parity.dichotomy
  ? numbertheory.parity.even_double
  ...
name one of them, or narrow the query
```

Eight of twenty-eight development queries end in ASK, not BIND. That was
read as a shortfall — a bind is more satisfying than a question — and it is
the opposite. **Ambiguity is not the failure mode; it is the substrate.**
A system that produces a correct candidate set and admits it cannot choose
is one disambiguation step away from being useful, and the step it is
missing is *context*.

## 2. The target, stated so it can fail

> *Buffalo buffalo Buffalo buffalo buffalo buffalo Buffalo buffalo.*

The [canonical example](https://en.wikipedia.org/wiki/Buffalo_buffalo_Buffalo_buffalo_buffalo_buffalo_Buffalo_buffalo)
is grammatical, has one intended reading, and is unparseable without
knowing that `Buffalo` is a city, `buffalo` an animal, and `buffalo` a verb.
No amount of word overlap resolves it. What resolves it is:

1. **A lexicon that carries part of speech and sense** — which this project
   now has, in WordNet: `buffalo` is noun *and* verb, `Buffalo` a proper
   place.
2. **A grammar that admits all readings rather than guessing one** — the
   project's habit already; the matcher enumerates, it does not pick.
3. **Context that eliminates readings** — the thing that does not exist yet.
4. **A comprehension check**: restating the reading back, so a person can
   see which one was taken before an answer is built on it.

The ambition is not to parse that sentence for its own sake. It is that
**a question can be asked ambiguously, several times, and the system
narrows by accumulating context rather than by guessing.**

## 3. What must be built, in order

- **Multi-turn context (P-LS6, unparked).** The single hard blocker.
  Today one line is read and the process stops, so a candidate set cannot
  survive to meet its disambiguating follow-up. The frame executor already
  holds owner-scoped beliefs across assertions; what is missing is a
  session that persists them between lines. Loop detection inside one
  dispatch is shipped and measured (v0.8); across two typed lines it is
  not, and the parked debt says so.
- **A candidate set that survives the turn.** An ASK must become a live
  object the next line can narrow, not a printed list.
- **Restatement.** Before answering, the system says which reading it took,
  in the corpus's own words where they exist. This is a comprehension
  check, and it is the honest alternative to confidence: a wrong reading
  that is *shown* costs a correction, a wrong reading that is hidden costs
  trust.
- **Sense-aware lexical lookup.** WordNet part-of-speech and sense are
  already loaded; the resolver currently ignores both.

## 4. What this must NOT become

- **Not generation.** Restatement quotes; it does not paraphrase. The rule
  from v0.12 holds: grammar in, structured readout out, prose only where
  the corpus supplies it.
- **Not a parser for English.** The Buffalo sentence is a *test*, not a
  feature. If the only way to handle it is a general-purpose syntactic
  parser, that is a different project and this design has failed.
- **Not a ranker that guesses.** Where context does not disambiguate, the
  system asks. The empty seat stays empty until something earns it.

## 5. Registered predictions (frozen before any of it is built)

- **A1 (ambiguity is common enough to be worth resolving).** On the
  development and holdout query sets, at least **25%** of in-corpus
  queries end in ASK rather than BIND. If ambiguity is rare, context is a
  solution to a problem the corpus does not have, and this design is not
  worth its cost.
- **A2 (context narrows).** For queries that end in ASK, a single
  follow-up line naming a discipline, a corpus, or a second content word
  reduces the candidate set by at least **half**, measured over the ASK
  cases in both text holdouts.
- **A3 (restatement is checkable).** Every restatement is verbatim corpus
  or WordNet text, with zero authored sentences — asserted the same way
  T4 was, by substring check against committed data, not by review.
- **A4 (the Buffalo bar).** Given the three senses as committed lexicon
  entries, the system enumerates the readings of a Buffalo-class sentence
  and **names which one it took**, or reports that it cannot choose. It is
  not required to pick the right one unaided. Guessing correctly without
  showing the reading is a **miss**, not a pass.
- **A5 (coverage does not pay for it).** In-corpus coverage does not fall
  below the v0.12 shipping figure of **0.833** on holdout 1. Context is
  supposed to add resolution, not trade it away, and v0.12 already
  published the curve where precision is bought with recall.

A4 is the one most likely to be read as weak. It is deliberately weak:
requiring the right reading unaided is requiring a parser, and requiring the
system to *show* its reading is requiring honesty. The second is the one
this project can keep.

## 6. What would falsify the whole frame

If A1 misses — if in-corpus queries almost always bind — then the ASK
substrate is an artifact of a small curated layer and will vanish as the
corpus grows, and context-accumulation is machinery for a problem that
solves itself. Measure A1 **first**, before building any of §3.
