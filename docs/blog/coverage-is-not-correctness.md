# Coverage is not correctness

Imagine a librarian who finds a shelf for every question.

You ask about interest accumulated *without* compounding.  The librarian
walks straight to **Continuous Compounding**, sets the book down with
confidence, and marks the request covered.

That is the result of this release.  A new resolver reached all 24 questions
in a test written before it existed.  It also gave one answer that contradicted
the question and raised false positives from 3.0% to 3.4%.  We reverted it.

The important number is not 24/24.  It is the one wrong answer that explains
why 24/24 was insufficient.

## The wager

The system is a library of mathematical statements.  It does not ask a model
to remember formulas; code indexes words and structure in a committed graph.
When exactly one statement fits, it binds.  When several fit, it asks.  When
nothing earns a claim, it passes to a named refusal.

The previous chapter,
[the shelf, not the architecture](the-shelf-not-the-architecture.md), found
that a structural effect measured on one formal corpus ran backwards on two
others.  It ended by turning toward the conversational shelf: measure the
surface, preserve ambiguity, and stop assuming a successful lookup is a
successful answer.

So we registered a simple bargain.  Add conservative spelling variants that
already occur in corpus-owned prose.  Score them once on a third hand-written
holdout and once on 1,000 newly sampled dictionary sentences.  Ship only if
coverage rises without worsening precision.

| question | bar | observed |
|---|---:|---:|
| Did some corpus statement become reachable? | at least 87.5% | **100%** |
| Was the intended statement retained? | at least 83.3% | **95.8%** |
| Did a wrong statement bind alone? | zero | **one** |
| Did random dictionary prose bind? | at most 3.0% | **3.4%** |

The conjunction failed twice.  Nothing was tuned against the spent rows.  The
candidate implementation was removed and the miss was kept.

## The word that changed the problem

“Without” is not another keyword.  It changes the role of the word after it.

A bag-of-words lookup sees *interest*, *accumulated*, and *compounding*.
Continuous compounding contains excellent matches for all three.  Adding
plural handling cannot help, and adding “without” to a stopword list would
make the contradiction easier to repeat.  The request contains a closed-form
constraint: exclude candidates that require compounding.

That distinction matters beyond this sentence.  More recall asks, “Did I find
something nearby?” Correctness asks, “Did the request rule that thing out?”
The first can improve while the second gets worse.

The cheap baseline made the same point from another direction.  Literal title
matching appeared to retain 91.7% of intended answers, but one “answer” was a
tie among 14,571 statement ids.  Inclusion without a candidate budget is not a
useful control.  A librarian who hands over the whole building has not found
the book.

## Asking exists, narrowly

Before building more context machinery, we measured whether ambiguity was
common enough to deserve it.  Across the development set and two earlier
holdouts, 16 of 62 registered in-corpus questions ended in ASK: **25.81%**,
just above the 25% line written in advance.

The margin is thin.  One holdout scores 18.75% by itself.  The first artifact
also looked stronger—27.12%—because its denominator silently dropped three
questions that passed instead of binding or asking.  Review restored all 62
promised questions.  The prediction still fired, but the flattering margin
did not survive.

That was enough to keep a bounded feature.  An ASK now survives the next input
line.  A person can explicitly narrow by corpus, discipline, word, or id; the
system intersects the candidate set rather than ranking it.  It can cancel,
name a repeated-state cycle, or stop at a visible four-hop ceiling.  A
singleton is shown only with text quoted from the corpus.

It is not general memory.  An unrelated command keeps its route.  Arbitrary
prose does not become a secret clarification.  The feature is exactly the
piece the evidence earned.

## The result we refused to manufacture

The context design also predicted that one follow-up would halve ambiguous
candidate sets.  The old holdouts, however, froze only their first lines.  They
did not say what the follow-up would be or which reading had to survive.

After candidate sets are visible, it is easy to write a “clarification” that
selects a convenient id.  It is also easy to report a halving that discarded
the answer the person meant.  Our first measurement tool allowed both.

Review stopped it before an aggregate run.  There is no A2 number in this
release.  Refusing that score is part of the result: preregistering a threshold
does not help if the evaluator can choose the denominator and labels later.

## A second gate that did not become a gate

The previous release found that real statements were more grounded than
random trees even when self-grounding failed.  We tried a harder foil: change
one internal operation while preserving the statement's relation, leaves,
arity, unlabeled tree, and batch head counts.

Groundedness noticed a small average difference, about 2.5–2.9 percentage
points.  It could not reject the foils.  Balanced accuracy was **50.52%** on
miniF2F and **51.04%** on Goedel-Pset.

That measurement is labeled exploratory.  Its thresholds and foil idea were
written before the scores, but the exact executable generator first entered
Git with the ledger.  Reproducible is not the same as preregistered.  The gate
parks without a tuned threshold.

## The next question is frozen now

The wrong bind and the refused context score point to one next experiment:
**when should the system ask instead of bind?**

The protocol is already committed in
[When should it ask?](../DESIGN-when-to-ask.md), before this post.  It fixes 48
rows and their strata, intended readings, exact follow-ups, an exact
`without TERM` veto grammar, a 25-candidate blind control, a negative-stripped
ablation, a fresh dictionary seed, and non-negotiable precision and coverage
floors.  A target that disappears is a scored miss, not an invalid row.

The wager for the next chapter is deliberately harder than “reach more.” An
exact negative constraint must stop every wrong negative bind without making
the system refuse everything difficult.  A frozen follow-up must narrow while
retaining the intended reading.  The blind librarian must pay for every book
it returns.  If any part misses, the candidate does not ship.

This release found every shelf.  The next one asks whether the system knows
when the shelf it found is the shelf the question excluded.
