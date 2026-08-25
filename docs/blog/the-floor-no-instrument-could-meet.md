# The floor no instrument could meet

Here is a way to fail a test that has nothing to do with being wrong.

Suppose you build a smoke detector and, to check it works, you set a
controlled fire in the room and require the alarm to sound. Sensible. Now
suppose that for one fire in three, the "fire" you set is a photograph of a
fire. The alarm stays silent, and you write down: *detection rate 65%, and we
needed 99%.*

The detector is fine. The **test** is broken, and the broken part is the
number you promised to hit before you knew what you were setting on fire.

That happened here this cycle, in a project that keeps its mathematical
knowledge as inspectable statements rather than as model weights. And the
interesting part is not that it happened. It is that the number was written
down first, so it could not be quietly adjusted afterwards — and that the
capability it condemned got published anyway, with the condemnation attached
to it.

## The thing that was being built

A library of about twelve thousand mathematical statements. Until now, each
one was a fact on a shelf: you could look it up, you could find out that
Coulomb's law and Newtonian gravitation are the same formula, but you could
not bring your own numbers to it.

The new capability turns a statement into something you can **run**. You hand
it your values; it computes; it tells you whether your numbers satisfy the
statement or hands you a case where they do not. Eight thousand and seventeen
statements compile into runnable form.

To find out whether the machinery actually works, the design registered a
control before writing any of it. Take a statement the library holds. Break
it in one mechanical way, so it should now be **false**. Run the checker. It
must notice, at least 99% of the time. If it does not, the whole run is void
and nothing may be reported as a rate.

It noticed 65% of the time.

## Why 99% was unreachable, and why that is a real result

The statements live over the **natural numbers** — zero, one, two, and up.
Nothing below zero exists there.

Now take a genuine statement: for any two numbers, `a² + b²` is at least
`2ab`. True. Break it by flipping a sign: `a² + b²` is at least **minus**
`2ab`. That should be a weaker, different claim — except over the naturals
there is no negative territory to fall into, so the broken statement is
**also true**, and there is no counterexample for anyone to find.

A perfect checker reports nothing. A broken checker reports nothing. On that
class of breakage, the two are indistinguishable, and **no correct instrument
could have hit the floor.**

So the finding is not "the checker is 65% good." It is: *this control's floor
was unmeetable on part of its own population, and the design did not know
that when it froze the number.*

That is the honest version, and there is a less flattering half that has to
travel with it. Not all of the 35% is the floor's fault. At least one
statement in the failing set is a **genuine miss** — the checker sampled
seventy-three values and did not find the one that would have broken it. So
the 65% is some mixture of "impossible to detect" and "failed to detect," and
**this run has no instrument that separates them.** The number cannot be
attributed, and the release says so instead of picking the flattering
reading.

## The control that only worked where it wasn't needed

There was a second control, and its failure is stranger.

Whenever the machinery finds a counterexample, that counterexample is
supposed to be handed to an **external proof assistant** — an independent
program with no stake in the outcome — for confirmation. Twenty-five of them
were handed over. The assistant confirmed **none**.

The reason turned out to be a missing line of code. A counterexample is a
statement plus the specific values that break it. The program handed over the
statement and **forgot the values** — so the external checker received
something with unfilled blanks in it and could not evaluate it at all. Every
single "could not decide" was the assistant saying *you have not told me what
the letters mean.*

The control did work on one group: statements with no letters in them at all,
where the text was already complete. Twelve of fifteen confirmed, zero
disagreements. Which is to say the control worked in exactly the cases where
it was not needed.

The tempting move is obvious — fix the line, rerun, publish better numbers.
That is not what happened. The measurement stands as it read; the **record**
around it was corrected; and the dead code that caused the bug was
deliberately **left in the file**, because it is the evidence for the
correction and deleting the evidence while filing the finding is the wrong
order.

## So it shipped void

The capability is live. You can type a statement's name and get an answer.
And every answer it gives carries this with it:

```
verdict    : NO_COUNTEREXAMPLE_FOUND
certifies  : tested at 37 admitted points and not falsified; this certifies
             nothing universally and is not evidence the statement is true
run void   : VOID — C-E1 missed its floor; every NO_COUNTEREXAMPLE_FOUND is void
```

There is **no success rate published anywhere** — not in the release, not in
the artifact, not on the wire. A search of the run's data file finds zero
fields that could serve as one. What is published instead is a sentence:
*3,298 statements were tested at their admitted points and not falsified, out
of 4,287 tested.* Not a percentage, because a percentage would invite exactly
the reading the control just took away.

Shipping a capability with its own indictment stapled to every answer is an
odd thing to do. The alternative was to ship it silently, or not to ship it,
and both of those are worse: one lies by omission and the other throws away a
working tool because its self-test was mis-specified.

## Meanwhile, the other run cleared

The [previous chapter](the-void-that-measured-what-the-gate-could-not-see.md)
ended on a debt. The library had learned to say its foreign-dialect statements
out loud in English — and scored perfectly, 2,313 out of 2,313, every sentence
checked by an external proof assistant. It was **not served anyway**, because
a control found that you could delete a redundant bracket from one of those
sentences, change what the sentence said, and the check would not notice. One
time in five.

The promise was: *next release, either the sentences pass a control that can
genuinely fail them — or we learn the blind spot was never the control's
fault.*

They passed. And the way they passed is worth the paragraph, because it was
not by improving the check.

The bracket was the problem, so **the brackets were made canonical**. The
renderer now emits exactly one bracketing for any given mathematical object.
If a bracket is there, deleting it changes the mathematics — because a bracket
that changed nothing would no longer have been emitted.

Then the old failing test was re-run, on a floor deliberately raised from 90%
to 95% — you do not get to declare victory against the bar you just tripped
over — and it came back **42 out of 42**. An exhaustive sweep backed it up:
every removable bracket in every rendered sentence, **5,228 of them, all
detected, none blind.**

Three sentences travel with that result because the project bound itself to
them in advance:

- **The denominator is a choice, and both numbers are published.** Eight of
  the fifty originally-failing statements no longer *have* a deletable
  bracket, because canonicalization removed it. Score the 42 that remain and
  you get 1.00. Keep all fifty in and you get **0.84 — below the floor.** You
  cannot detect a break you cannot construct, so scoring 42 is defensible.
  It is also a judgement call, and judgement calls get shown.
- **The ten worst cases are "seven detected and three no-longer-applicable,"
  never "all ten detected."** Ten specific statements were named by identifier
  *before* the fix was built. All ten are cleared. But "cleared" means two
  different things across them and the release says which.
- **The two runs' headline numbers are not comparable.** The old 0.80 and the
  new 1.00 measure different things. The number a reader can honestly compare
  is the raised-floor one: **42 of 42, floor 0.95.**

So the English sentences are served now. And the repair had a price, measured
rather than assumed: a separate control that checks the gate isn't just
rubber-stamping got **weaker**. Removing brackets left scrambled sentences
with less structure to survive being read back, so more of them now fail at
the parser before the real comparison happens — the share of that control's
work that actually exercises the gate fell from 42.5% to 22.4%. It still
holds. It does less.

## The reader who could not read

One more result, because it is the one most likely to be over-read.

Having taught the library to speak, the obvious question is whether anyone can
**understand** it. The honest test needs a person who did not write the
sentences, and a one-person project does not have one. So that test has never
run, and the claim it would license — *a human can recover the mathematics
from the English* — has never been made.

This cycle bought a substitute: a small language model, pinned to a specific
set of weights, reads each sentence **blind** — never shown the underlying
mathematics — and tries to reconstruct it. It scored 84%.

It also scored **50% on scrambled nonsense**. Which means well over half of
its apparent comprehension was coming from somewhere other than the sentence.
The control's rule, frozen in advance: if the nonsense score is at least half
the real score, the reader is supplying the mathematics rather than reading
it, and the result is void.

Ratio: 0.594. **Void.** The machine-reader claim is not made either.

So the project now serves English sentences that are provably faithful to the
mathematics — checked by an external proof assistant, exhaustively, with the
blind spot closed — and has **no evidence that anyone can read them.** Both of
those are true at once, and only writing both down keeps the first from
implying the second.

## What one discipline looks like from outside

Two registered experiments in one cycle. One cleared and shipped a feature.
One voided and shipped a feature with the void attached. Neither was re-run to
read better.

That symmetry is the only property of this cycle worth generalising, and it is
worth generalising because the alternative is so easy. A project that reports
only the runs that clear is not lying; it is just choosing, after the fact,
which measurements count. The defence against that is not good intentions. It
is writing the floor down before you know where your arrow will land, and then
being stuck with it.

There is a smaller habit underneath, and it came out of two independent
reviews this cycle. Not one wrong number was found in either. What was found
was a set of **checks that could not have failed**: a test comparing a file to
itself; a check whose evidence was computed from a hardcoded list of the very
thing it was supposed to verify; a claim enforced by a program that could no
longer run. All of them green. All of them worthless.

**A green check that could not have gone red is not evidence.** It is the
software equivalent of a smoke detector wired to a lamp.

## What comes next, and why it is a conversation

The next direction was chosen the way this project chooses them — three
advisors, isolated from the repository and from each other, fifteen proposals,
nine rounds, $2.41 — and it went somewhere the last two cycles were not going.

The maintainer's actual goal, stated in plain words some time ago, is to hold
**a plain conversation with this thing, in plain text.** Not commands. A
conversation.

The obstacle turns out to be smaller and more specific than "understand
English." It is that **there is no such thing as a session.** You can tell the
system to assume something — *suppose the numbers are integers* — and it will
answer under that assumption, correctly. And then the next line you type has
never heard of it. The assumption is built, used, and thrown away.

That is the gap the [committed
design](../DESIGN-session-ledger.md) closes, and it is deliberately narrow.
A conversation becomes a **journal**: one record per turn, chained together,
and every answer names **which of your assumptions it actually consumed** —
not because a person wrote the citation down, but because the machinery
records the moment it reads one. Hand that journal to a stranger and they can
replay it offline and get identical bytes, or a typed refusal saying the world
has changed underneath it.

The thing that makes it a measurement rather than a feature is the control,
and it is already frozen. Change an assumption the answer **did** cite: the
answer must change, on every single turn, no exceptions. Change an assumption
the answer **did not** cite: the answer must not move. **At all.** If a
sixty-item set of assumptions nobody cited can budge a single answer, then the
system is not tracking meaning — it is hashing the transcript — and the whole
capability is declared void for the cycle.

Which is the same shape as everything above: a way for the thing to fail
stated before it is built, and a published result either way.

Next release, either a conversation can carry its own premises — or we find
out that citation was bookkeeping all along.
