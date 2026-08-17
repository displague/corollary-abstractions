# The shelf, not the architecture

*Last time we found that an imported library starts explaining itself once
it gets big enough. This time we tried the same measurement on two libraries
we had not built the reader for. Both went the other way.*

The [previous chapter](the-curve-changed-sign.md) ended on a promise: the
curve we found was measured on one source, the shelf our importer was built
to read, and a benchmark that only re-reads that shelf is a re-measurement
rather than a test. We said we would take the question somewhere the reader
had never been.

We did, and the answer is not the one we wanted.

The wager of this project has not moved:

> If an operation has an exact answer, it should live outside the weights.

What we are allowed to *learn* is the leftover. For that leftover to be
worth anything, the world it points at has to be real — a library whose
pages genuinely refer to one another, rather than a thicker pile of
unrelated lines.

## The question, in the form a person can hold

Import pages of formal mathematics. Each page is made of parts — a square, a
remainder, a product. After enough pages, do those parts start having
*homes* on other imported pages?

Last time, on twelve and a half thousand pages of contest inequalities, the
answer was yes: worse than a shuffled fake at thirty-two pages, better from
one hundred twenty-eight, and clearly better at twelve thousand.

So we found two more shelves. One small — one hundred fifty-seven
competition problems, the kind with a year and a number in the name. One
large — nearly two thousand statements from a corpus of a million and a
half, formalised by a machine from word problems. Neither is a shelf we
tuned the reader for. Both were kept in quarantine, in a separate room from
the main library, so that measuring them could not quietly change the main
library's numbers.

## Both shelves went the other way

Here is the gap between each real shelf and its own shuffled fake, as the
pile grows.

| pages imported | small shelf | large shelf |
|---:|---:|---:|
| 8 | −0.016 | — |
| 32 | −0.010 | −0.009 |
| 128 | — | −0.046 |
| 512 | — | −0.093 |
| all | −0.043 | **−0.126** |

Not a curve that failed to turn upward. A curve running downhill, and
getting steeper. On the shelf we built the reader for, the same measurement
climbs to plus six points. On these two it falls to minus thirteen.

The obvious objection is size. The small shelf tops out at one hundred
fifty-seven pages, and that is below where the original curve changed sign,
so perhaps we simply never got far enough. We wrote that objection down as a
prediction before we tested it, then ran the *original* shelf at exactly one
hundred fifty-seven pages.

It scores **plus five**. The held-out shelf at the same size scores **minus
four**. Same measurement, same fake, same everything except which shelf.

So it is not size. It is the shelf.

## What we are retracting

Last chapter said ingestion compounds. That sentence was measured on one
source and we are taking it back as a general claim. Importing still buys
coverage — more statements, more parts, more reach. It does not buy a
library that explains itself, and it does not buy an argument about the
architecture. It bought us a fact about a shelf of olympiad inequalities,
which share their squares and their tricks because that is what olympiad
inequalities are.

The pages of the new shelves are not floating free, incidentally. Their
parts *are* explained — sixty to eighty percent of them — just by the older
hand-written layer and by the first shelf, rather than by each other. One
hundred fifty-seven competition problems do not have much to say to one
another. That is not a defect in them. It is what a diverse collection looks
like.

## The number that would have hidden all of it

Last chapter we described a measurement we refused to use: instead of asking
whether a part has an *owner* elsewhere in the imported layer, ask only
whether its shape *occurs* elsewhere. Sharing rather than ownership. We said
reporting it would be publishing a vacuous 1.0.

On these two shelves the rejected measurement reads **0.71** and **0.92**.
The real one reads **0.008** and **0.040**.

Had we shipped the easy number last time, these two shelves would have come
back looking like a triumph — seventy and ninety percent self-explanation —
on sources that in fact recover almost nothing. The whole of this chapter
would have been invisible, and we would have believed the opposite of the
truth with a table to prove it.

That is the strongest argument this project can make for its own habits, and
it costs a headline to make it.

## Meanwhile, the thing you can actually type into

The other half of the cycle is not the finding, and we want to be careful not
to sell it as one.

Since version 0.8 the notes have said the system could be driven. What
existed was a program that printed a list of what had loaded and exited. You
could not type anything. This cycle you can:

```
$ echo "what is the cosine of a double angle" | python scripts/harness.py
Double-Angle Cosine
The cosine of twice an angle is the difference of the squared cosine
and the squared sine.
formally   : cos(2*x) = cos(x)^2 - sin(x)^2
source     : trigonometry.identities.double_angle_cosine
```

Every sentence there was written by a person and stored in the library. The
program chose *which* sentence; it did not write one. Ask it arithmetic and
it computes exactly — thirds stay thirds, never 0.333. Ask it what someone
believes and it answers from that person's frame, so if Dotty watched Bob
walk into a room and Bob has since moved to the garden, it says Dotty thinks
he is in the room, and tells you the world disagrees. Ask it for a story and
it tells you one it can prove is well formed — the planted feather is
discharged, nothing arrives from nowhere — rather than inventing one.

Ask it something the library does not contain and it says so.

How often does it say so? On a thousand sentences pulled at random from a
dictionary — about hedgehogs and harbours and self-winding watches — it
wrongly claimed about three percent as library material. Not zero. We tried
three separate ways to push it lower, published the trade-off between
refusing too much and answering too little, and found that the most
promising idea — using a dictionary's own sense hierarchy to spot everyday
words — does not work at all. The abstraction tree is too shallow at the top
to tell a question about a game from a question about a curve.

## What we owe next

The retraction is the finding, and it closes one question by opening a
narrower one: if compounding is a property of a *shelf* rather than of the
method, then what property of a shelf predicts it? That question is
[written down](../DESIGN-what-predicts-the-gap.md), with its trap named in
advance — if self-explanation *is* concentration, then a concentration
statistic will "predict" it by construction, so the predictor ships with two
deliberately blind controls and the claim is about the difference.

And the typing surface has an obvious hole that this cycle measured rather
than guessed at: it answers well inside the library and thinly at its edges,
and it takes one line at a time. A question asked badly, or twice, or in a
way that could mean two things, gets a list and a shrug.

So the next chapter is about that, and the bar we have set for it is a
sentence that is famously, legitimately ambiguous:

> *Buffalo buffalo Buffalo buffalo buffalo buffalo Buffalo buffalo.*

Eight words, one city, one animal, one verb, and a single valid reading that
nothing short of context can find. We are not promising to parse it
correctly. [The design](../DESIGN-ambiguity-and-context.md) promises
something smaller and more honest: enumerate the readings, **say which one
was taken**, and let the next thing you type narrow it. Guessing right
without showing the reading counts as a failure, not a success.

It also names what would kill the whole idea. If it turns out that questions
about this library almost never come out ambiguous, then all that machinery
is a solution to a problem that will disappear on its own as the shelves
grow — so that gets measured first, before anything is built.

A small model's job was never to contain the world. It is to move through
one whose relationships stay visible. This cycle we learned that one of
those relationships was a property of a single shelf, and we said so out
loud. Next we find out whether the shelves can be asked a question badly and
still answer it.
