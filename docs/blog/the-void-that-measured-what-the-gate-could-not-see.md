# The void that measured what the gate could not see

The [last chapter](the-alphabet-was-half-the-wall.md) ended with a promise
that offered two outcomes: *next release, the graph either speaks a dialect
it cannot read — or it hands you a precise, counted inventory of its own
silence.*

It handed over the inventory.

Not because the rendering failed. The rendering scored **perfectly** — 2,313
of 2,313, every sentence checked by an external proof assistant with no
stake in the outcome. We are not serving those sentences anyway, because a
control we built to police that very score came back below its line, and the
line was drawn before the control existed.

This is the story of a cycle where three of four results made the claims
smaller, and the smaller claims are the ones worth having.

## What was being checked, and how

This project keeps its mathematical knowledge in inspectable statements
rather than model weights. Last cycle it learned to say those statements out
loud in English — but only the 17% its own parser could read. The rest, over
ten thousand statements, came from an external tool in a dialect this
project's grammar does not speak.

The plan was to borrow. Write a hand-made dictionary from that foreign
dialect into English, render a sentence, and then — this is the interesting
part — **check the sentence by feeding it to the external proof assistant
that produced the original**. If the assistant reads our English translation
back into exactly the same mathematical object it had before, the
translation is faithful.

That check has a subtle limit, and to the credit of whoever wrote the design,
the limit was written down as *the shape of the claim* rather than buried as
a caveat:

> Identity holds **up to what elaboration erases** and what the preamble rule
> regenerates.

In plainer words: the proof assistant *normalises* what it reads. Two
different English sentences can normalise to the same object. So the check
can only catch errors that survive normalisation — and it is structurally
blind to any error that does not.

Nobody knew how big that blind spot was. So the design specified a control
to measure it: take correct sentences, break each one in exactly one
mechanical way, and require the check to notice. Five kinds of breakage,
each with a floor of 90%, frozen before the instrument was built.

## The number that voided the cycle

Four of the five behaved. Swapping two variable names in the preamble:
caught 100% of the time. Reassociating an operator: 100%. Deleting a type
annotation: 90%, exactly on the line.

Deleting a redundant bracket: **80%**.

Which means: **you can delete a bracket from one of these sentences, change
what the sentence says, and the check will not notice** — one time in five
among the sampled mutations, though the control's own mis-specification
(below) means the true undetected-error rate could be lower, and pinning it
down is what the re-specified control is for next cycle. The bracket was
doing nothing the mathematics required — but it was doing something the
*sentence* required, and the gap between those two facts is precisely the
blind spot the design predicted, now with a number on it.

The floor was 90%. The measurement was 80%. The control's own voiding
sentence says what happens next, and it does not include a discussion.

**So the foreign sentences are not served.** Not one of them, despite a
perfect score, because serving a sentence under a certification whose own
control voided is exactly what that control exists to prevent. The perfect
score may only ever be quoted with the void attached — and it is, everywhere
in this release.

## The number that is not a failure

One of the five classes measured **0.18** — far worse — and it is not a
failure at all. It was **excluded from voiding in advance**, in writing,
because it is blind by construction: it deletes something the setup rules
automatically put back, so the check *cannot* see it, ever, by design.

That 0.18 is the most useful number in the run. It is not a miss; it is **the
measured width of the blind spot**, a sentence in the design converted into a
quantity. Before this cycle, "the check is blind to some things" was a true
statement of unknown importance. Now it has a size.

There is a small discipline here worth stealing. A reviewer had already
estimated that number by hand — 1 out of 24. The registered run
**re-measured it anyway**, rather than freezing the threshold at the value
the project's own reviewer had produced. Setting the bar where your arrow
landed is a way of never being wrong, and never being wrong is not the same
as being right.

## And the honest admission underneath

The control that voided this cycle is itself mis-specified, and the release
says so rather than using it as an escape hatch.

The previous cycle had a similar control with one extra rule: **verify that
each break actually changed the mathematics before you test whether the check
notices**. Breaks that change nothing get discarded, and the discards get
counted. That rule exists because without it, a control fills up with
non-breaks, "fails" to detect them, and voids a gate that was working
perfectly.

This cycle's control inherited the idea and left the rule behind. So some of
its 80% may be non-breaks.

The tempting move is obvious: point at the flaw, discount the void, ship the
feature. That is not what happened. **The run stands as it read.** The fixed
control is a fresh registration for next cycle, and the feature stays unwired
until it passes. If it voids again, that is a much more interesting finding
than the first void — it would mean the blind spot belongs to the *method*,
not to one control's wording.

## The one thing that grew

Meanwhile, the easy half of last chapter's discovery got executed, and it
worked exactly as predicted.

Two characters — `≥` written as `>=`, `≤` as `<=` — added to the list of
symbols the parser recognises:

| | statements | share of the library |
|---|---:|---:|
| the graph could say this before | 2,172 | 17.0% |
| **the graph can say this now** | **8,586** | **67.2%** |

Six thousand four hundred and fourteen statements gained a voice, and every
single one of them survives the round-trip check — 6,414 out of 6,414.

Three things keep that from being oversold, all of them published with the
number rather than discovered by a reader. The newly-reached statements are
**one corpus and two distinct operations** — numeric inequalities, almost
nothing else — so this proves the new statements use vocabulary the
dictionary already had, and proves nothing about coverage generally. **No
target was set for the round-trip rate**, deliberately and in writing
beforehand, because a *low* rate would have been the more interesting result
and a target is exactly what pressures a team not to publish one. And
additivity was **proven, not assumed**: the check loaded the old parser back
out of version control, in a separate process, and compared every rendered
line across all 12,777 statements. 6,414 gained, 2,170 unchanged
byte-for-byte, **0 changed, 0 lost.**

## Two more things that got smaller

**A design was adopted, built, measured, and parked — by numbers.** The
maintainer had seeded a proposal for a unified address space over the whole
library, with an instruction that it not be silently dropped. So it was not
dropped; it was *scheduled*, built, and measured against three baselines
taken from its own list of things it would have to beat. It beat one, and
that one had been declared in advance to be a restatement of an existing
result rather than a new finding. Its retrieval arm lost badly to the plain
keyword search it was supposed to replace — on the same queries, in the same
run, 0.33 against 0.93. The single question it was scoped to answer — *is the
unified dictionary one real object, or two existing objects sharing an id
space?* — came back: **two objects sharing an id space**, by a margin of
0.9981 against simply tagging which of the two you mean.

That is a complete lifecycle, and it is the point. A park that cites a
measurement is a decision. A park that cites a preference is drift.

**And a search for disagreement found none.** A one-hour probe swept the
library for statements saying the same mathematics under two defensible
conventions — the sort of thing where one textbook writes a sign one way and
another writes it the other. It found 125 candidates, and **every one of them
is notational**: a glyph, a spelling, where somebody put a parenthesis. Zero
mathematical convention forks. Inside the hand-authored material the negative
is total — not one pair with both halves authored here.

Which is a real fact about this library that nobody had written down: its
authors fixed their conventions and never forked them. And the largest group
of those 125 candidates is the `>=` versus `≥` split — the same two
characters from the section above, found by a completely different method.
Two probes aimed differently, one phenomenon.

## What next, and an idea that came back

The next headline was chosen the way this project chooses them: three
advisors, isolated from the repository and from each other, fifteen
proposals, nine rounds. The winner is **statements that decide
themselves** — take a statement the library holds and compile it into
something you can *run* against your own numbers, so it stops being a fact
on a shelf and becomes a thing that answers a question you brought.

What makes that worth a paragraph is not the idea. It is that **the same
idea was proposed last cycle and thrown out.**

It came back because the evidence changed, and the record says which
evidence: the void described above. A gate that checks structure cannot see
an error that structure erases — that is the whole finding of this release.
An evaluator can. It does not check that the sentence has the right shape;
it checks that the thing computes the right answer, which is exactly the
error class the bracket-deletion slipped through. Two cost arguments that
were guesses last time are measured facts now.

A selection process that only ever discards is a filter. One that lets a
rejected idea back in — **on stated new evidence, with the rejection still
in the record** — is doing the harder thing. The receipt calls that "the
funnel working," and files it as a governance result rather than a
footnote, because the difference between an evidenced return and simply
re-proposing something until it sticks is entirely a matter of what got
written down the first time.

Meanwhile the next cycle's most concrete work does not depend on any of
that, because the void wrote its own successor. The [re-specified
control](../ROADMAP-v0.20.md) carries the rule this one dropped: verify each
break actually changed the mathematics, discard the ones that did not, count
the discards, and only then score. The foreign sentences ship **if and only
if** it clears. And underneath it sits a question this project has never
asked itself — should the renderer emit a canonical bracketing at all? — for
which the honest first step is to *count* how many brackets the grammar emits
that the mathematics does not need, and publish the distribution before
anyone proposes a fix.

Both outcomes are results. That is the only property of this cycle worth
generalising: every one of its four readouts had a branch where the news was
bad, every one of those branches was written down before the measurement, and
three of the four took it.

Next release, either the sentences pass a control that can genuinely fail
them — or we learn the blind spot was never the control's fault.
