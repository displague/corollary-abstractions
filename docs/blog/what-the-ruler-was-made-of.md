# What the ruler was made of

Suppose you want to know whether a new pair of glasses helps you read. The
careful way is to write the eye chart first, seal it, then put the glasses on.
Write the chart afterwards and you will unconsciously choose letters you can
already see.

We did the careful thing. We wrote the chart first — forty-eight questions,
frozen in a commit, with every expected answer and every follow-up line
recorded before a single line of the new code existed. Then we built the
glasses, put them on, and read the chart exactly once.

Five of the six predictions failed. That was not the surprise. The surprise
was that three of them failed because of the chart.

## The thing we were testing

The system holds about thirteen thousand precisely written statements from
many fields — geometry, chemistry, economics, topology, narrative structure.
You type an ordinary sentence and it does one of three things: names the
single statement you meant, asks one question that would settle which of
several you meant, or says it holds nothing on the subject.

The previous cycle had ended badly in an interesting way. Asked about
"interest accumulated **without** compounding", it confidently returned
continuous compounding — the one reading the sentence rules out. It had
answered twenty-four of twenty-four questions correctly and still could not
ship, because being right often is not the same as being trustworthy.

So this cycle asked a narrower question. Can an exact negative — the word
*without* and the thing it excludes — turn a confident contradiction into a
question or an honest refusal?

The mechanism works. The sentence that broke the last cycle now returns simple
interest instead of continuous compounding, and it does so in the way that
matters: not by deleting the wrong answer afterwards, but by making it
inadmissible *before* the search, so a lower-scoring but non-contradictory
reading can win. Delete-afterwards would have returned nothing at all.

That was the one thing the cycle set out to build, and it is the smallest part
of what it learned.

## Three ways a ruler can lie

**The first clause could not have been true.** One prediction said fresh false
positives would stay at or below 0.030 — a mechanical check that feeds the
system a few thousand dictionary sentences and counts how often it claims to
recognise one. But dictionary sentences do not contain the word *without*
followed by a concept to exclude. The new machinery never runs on them. The
clause was measuring the *old* system with fresh samples, and it duly
reproduced the old number: 0.024, 0.038, 0.042 across three independent
thousand-sentence draws, pooled 0.0347, against last cycle's 0.034.

As a replication that is genuinely useful — the number that sank the previous
cycle is real and reproducible. As a test of this cycle's change it was
unfireable the day it was written, because nothing the change did could move
it. A prediction needs a path from the thing you changed to the number you
read.

**The second clause rewarded the disease.** To show the system was doing
something a dumb baseline could not, we compared it against a deliberately
stupid method: match the words in the question against the words in each
statement's title, return the best twenty-five. Score both by how tightly they
narrow to the right answer — one divided by the number of candidates returned.

The system won enormously, 0.71 against 0.03. But that scoring pays for
confidence. Twenty-five of the thirty times it found the right answer, it
returned that answer *alone*. The measure rewards small answers, and returning
one small wrong answer is exactly the failure the whole cycle exists to fix. A
control that cannot tell precision from overconfidence is not a control.

**The third clause tested a belief about the collection.** This is the one
worth the whole cycle.

Twenty of the forty-eight questions were written to require a clarifying
question — cases where several statements genuinely compete and the system
should ask rather than guess. It scored three out of twenty. That looks like a
clarification failure.

It was not. Of those twenty questions:

| what actually happened | count |
|---|---|
| bound straight to the intended statement | 8 |
| bound to a different statement | 5 |
| said it held nothing | 3 |
| asked a clarifying question | 4 |

Eight of them got the right answer without needing to ask, and the scorer gave
that the same credit as getting it wrong — because a question that isn't asked
has no follow-up, and a follow-up that doesn't happen retains nothing.

Meanwhile the other twenty-eight questions, the ones nobody expected to be
ambiguous, recalled their target twenty-eight times out of twenty-eight.

Every failure in the cycle sat in questions written on the belief that the
collection was ambiguous. The collection mostly wasn't. One case makes the
point: asked for "story constraint on setup and payoff", the system returned
Chekhov's gun — which *is* the setup-and-payoff constraint — and was marked
wrong, because the person writing the chart had a different statement in mind.

The measurement was sound. The belief about what was being measured was not.

## The part that generalises

The obvious lesson is "check your benchmark." The useful one is sharper.

Every one of those three defects was **computable from material already
committed**, before anything was measured. Whether a clause can be affected by
the change is a question about code paths. Whether several statements genuinely
compete for a question is a question about the collection. Neither needed a
held-out set, and both were answered instead by spending one — a resource that,
by this project's own rules, cannot be spent twice.

So the rule the next cycle inherits is not "be careful". It is: *anything
computable from committed sources gets computed before anything measurable gets
measured.*

We tested that rule immediately, and it bit. An outside line of reasoning
proposed a plausible instrument: find the statements that no phrasing could
ever single out, because some other statement's readable features are a
superset of theirs. It came with its own kill condition — fewer than three
victims and the idea is not worth building. Computed over the collection: zero
out of two hundred and sixty-two. Statements here carry a median of
forty-three distinguishing features; strict subsumption essentially cannot
happen at that density.

The idea died in about a minute, having spent nothing. That is the rule
working, and the negative is the more useful half: whatever makes clarification
hard here, it is not that statements are invisible.

## The honest boundary

The system did not get better this cycle. The resolver that ships is the same
one that shipped before, at the same measured point. The new exclusion
machinery is in the code and no gate credits it, because its gate missed.

Nor is any of this a claim about language understanding. It is a claim about
one exact failure mode, one frozen chart, and what happened when we read it
once and published what it said.

## What comes next, and why

The next instrument is aimed at us.

The system finds statements from different fields that share an exact
structural shape — the same equation wearing different clothes. That is the
project's most attractive claim, and it has never been tested against a
prediction that could have gone either way. Shape collisions are cheapest
exactly where a collection is most formulaic, which is where most of ours comes
from.

So the next cycle builds something that can only say *no*: a check that reads
the two statements' own committed symbol glossaries and certifies, for a
particular cross-field match, that the things sitting in the aligned slots
cannot be the same kind of quantity. It has two possible values, *conflicting*
and *unjudged*, and deliberately no way to say *confirmed*. It cannot bless a
match. It can only refuse one.

There is a demonstration waiting in the data. One matched pair puts the
circumference of a circle beside Newton's second law — the same shape, one
product of two factors equalling a third. Whether that survives a check on what
the symbols denote is exactly the question, and we have not run it yet.

Until it reads out, the count of cross-field matches is suspended from use as a
result in this project's own release notes. It has sat on the achievement side
of the ledger long enough without being asked to defend itself. That is the
same mistake this cycle just made with clarification, caught one cycle earlier
than last time.
