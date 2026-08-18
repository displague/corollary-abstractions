# v0.13 roadmap — coverage, and questions asked badly on purpose

v0.12 asked whether v0.11's sign flip was a fact about the architecture or
about one shelf of olympiad inequalities. Two held-out sources answered:
the shelf. H1 missed, and "ingestion compounds" is retracted as a general
claim.

The same cycle built a prompt that answers — and measured it honestly
enough to know where it is thin. **In-corpus coverage is 0.833 on the first
text holdout.** That number is this cycle's headline target.

The forward-looking designs are committed and their predictions frozen
before any work starts:
[DESIGN-ambiguity-and-context.md](DESIGN-ambiguity-and-context.md) (A1–A5,
written from v0.12's accident) and
[DESIGN-what-predicts-the-gap.md](DESIGN-what-predicts-the-gap.md) (W1–W3,
written before H1–H6 were graded so it could not be chosen to flatter the
post).

**House rule (kept):** every carried lane names the headline item that
depends on it, or is parked in BACKLOG with a reason.

---

## 1. Coverage of the conversational surface (headline)

0.833 in-corpus coverage on holdout 1 is the weakest number v0.12 shipped,
and it is the price paid for precision: the published curve is 0.046 false
positives at 0.944 coverage, 0.030 at 0.833, 0.006 at 0.611.

The goal is to move *both* — coverage up without buying it back in false
positives — which means a signal that is not another threshold on the same
evidence. v0.12 refuted the obvious candidate: WordNet hypernym roots do not
separate leaked glosses from real questions.

Known coverage losses to attack, each with a named cause:

- **Morphology.** `derivatives` misses a corpus that writes `derivative`;
  `euclid` misses `euclidean`. One unknown content word is the difference
  between resolving and refusing.
- **Synonyms beyond the corpus glossary.** The `symbol_lexicon` fix caught
  "greatest common divisor"; nothing catches phrasings the corpus never
  names.
- **Corpus gaps mistaken for resolver gaps.** "conservation of momentum"
  does not resolve because no such statement exists. That is a corpus
  item, not a resolver item, and the two must be counted separately.

**Acceptance:** coverage measured on a **third** hand-authored holdout,
registered before the run, with the false-positive rate re-measured on a
fresh mechanical seed. Coverage up and F-rate not worse, or the trade is
published and the change is not shipped.

## 2. Ambiguity and context (headline, ambitious)

[DESIGN-ambiguity-and-context.md](DESIGN-ambiguity-and-context.md), A1–A5.

A question may be asked badly, more than once, and narrowed by what was
said before. The bar is
[Buffalo-class](https://en.wikipedia.org/wiki/Buffalo_buffalo_Buffalo_buffalo_buffalo_buffalo_Buffalo_buffalo):
grammatical, multiply parseable, resolvable only with sense and context.
The system is **not** required to pick the right reading unaided; it is
required to enumerate readings and **name the one it took**. Guessing
correctly without showing the reading is a miss.

**Prerequisite, ordered first:** measure **A1**. If in-corpus queries
almost always bind, the ASK substrate is an artifact of a small curated
layer and this item is machinery for a problem that will solve itself.

**Named dependant:** item 1 — restatement is also a coverage tool, because
a reading shown is a reading a person can correct.

## 3. Multi-turn context (P-LS6, unparked)

Parked since v0.12 and **enforced** by a test, so unparking is a decision
rather than a drift. It is the hard blocker for item 2: today one line is
read and the process stops, so a candidate set cannot survive to meet its
disambiguating follow-up.

Loop detection inside one dispatch is shipped and measured (v0.8). Across
two typed lines it is not, and P-LS6 says so. A multi-turn loop must
terminate by naming a cycle or at a visible hop ceiling, and must not claim
session memory it does not have.

**Named dependant:** item 2. This is a **prerequisite**, ordered before it.

**SHIPPED — P-LS6 FIRED.** The resolver clarification subloop persists an
ASK, accepts only explicit hard intersections, exposes `cancel`, and stops on
a named repeated state or four-hop ceiling.  New questions and registered
commands are not consumed as clarification.  The real binary and routing
suite cover those boundaries.  **Item 2 is parked at the measurement gate:**
A2 named a follow-up class but did not freeze the actual per-query follow-ups
or intended retained readings before both holdouts were spent.  Review
rejected an authored-after-the-fact protocol before any aggregate was run.
A2/A3 therefore remain unadjudicated; A4 remains unimplemented at this point.

## 4. Groundedness as an admission signal (from the accident)

v0.12's vacuity check turned up a quantity that survives the holdouts where
self-grounding does not: exact grounding by *any* owner beats its null by
+17.5 to +46.2 points on all three sources, while ISG spreads 44×.

This is **unregistered** — computed after seeing the holdout data — and is
therefore not a result yet. It owes a design, a registered prediction, and
a harder foil than random trees: a gate must reject *plausible but
ungrounded* statements, not merely noise.

**Named dependant:** none yet. If no design is written by v0.13 triage,
**park it in BACKLOG** rather than carry it as a floating quantity.

## 5. What predicts the gap (design carried, not scored)

[DESIGN-what-predicts-the-gap.md](DESIGN-what-predicts-the-gap.md), W1–W3.
Skeleton-reuse concentration as a predictor, with two capability-blind
controls, because a concentration statistic will "predict" ISG by
construction if ISG *is* concentration. Needs four sources; three is an
anecdote. **Not scored in v0.13** unless a fourth source is authored for an
independent reason.

## 6. Carried lanes

| lane | named dependant | disposition |
|---|---|---|
| Multi-turn context (P-LS6) | item 2 | **prerequisite**, ordered before it |
| Morphology / synonym layer | item 1 | **prerequisite** for the coverage number |
| Groundedness admission signal | *none yet* | item 4; park at triage if no design |
| What predicts the gap (W1–W3) | *none — needs a fourth source* | **carried as design** |
| Write-recovery ranker | *none — no fit named* | **parked** at v0.12 triage |
| Budgeted-edit ranker | *none* | **parked** (one foil cell) |
| Groundedness *gate* (ISG-based) | *none* | **parked**; unpark only when a non-Lean-workbook source shows a positive gap surviving its own null |
| `specialize.py` general index | *none* | parked |
| Proof-search depth | *none* | parked |
| Physics / affect / visual | *none* | parked |
| Chat-shaped HTTP skin | *none* | parked |
| Open-English node authoring | *none* | parked (last, as v0.8 said) |

## 7. Governance

Unchanged. Capability-blind baselines; negatives first-class; designs
before runs; guard pins that move get a decision. Two rules v0.12 earned
and this cycle inherits:

- **A holdout is scored once.** Its failures may not be used to tune the
  thing it measures; a second holdout is authored instead. v0.12 spent two
  hand-authored sets and three mechanical seeds this way.
- **Registered numbers are not re-scored.** A miss records that a
  prediction about a code state was wrong. Fixes are validated on fresh
  input, and the original number stands.

## Release gate

v0.13 is ready only if it contains:

- A1 measured **first**, and item 2 abandoned or reshaped in writing if it
  misses;
- coverage measured on a third registered holdout with the false-positive
  rate re-measured on a fresh mechanical seed, and the trade published if
  both did not improve;
- item 3 shipped with P-LS6 adjudicated, or item 2 parked in writing;
- item 4 designed with a registered prediction and a harder foil, or
  parked in BACKLOG;
- every carried lane naming its dependant or parked;
- updated assets with winners, losers and controls;
- the complete suite green, planned from the measured wall-clock.
