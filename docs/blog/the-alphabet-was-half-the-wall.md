# The alphabet was half the wall

The [last chapter](the-answer-was-already-written.md) ended with a promise:
*next release, the graph says a sentence and hands you the proof that the
sentence is the term — or it says nothing at all.*

It says sentences now. Two thousand one hundred and seventy of them, each
with a proof attached. And the same run that produced them measured how
much of this library still cannot speak — which turned out to be a
different problem than anyone here thought it was.

## What was actually wrong

This project keeps its exact knowledge outside a model's weights, in a
library of mathematical statements anyone can inspect. Ask it about one and
it hands you back a sentence a person wrote, stored in the corpus, quoted
verbatim.

That works beautifully for the statements a person wrote. There are 262 of
them. There are also **12,515 statements that arrived by machine**, ingested
in bulk, and for those the human-readable field is boilerplate — the
software equivalent of a form letter. The system has been serving those
with a disclaimer for five releases: *this text is an ingestion record, not
an explanation a person wrote.* Quotation had nothing to quote.

But the *formal* statement was always there, and it is exact: a piece of
structure the system understands completely. `1 + 1 = 2` is not boilerplate.
So the question for this cycle was whether the library could say its own
mathematics out loud — in English, in sentences nobody had written down in
advance — without being allowed to make anything up.

## The trick, which is not a trick

The obvious way to turn structure into English is to write templates. This
project has done that before, and the ceiling is low: a template you did not
write is a sentence the system cannot say.

The alternative is a **grammar** — a set of rules that composes a sentence
out of the structure, so the sentences are not enumerated anywhere. That is
also the terrifying option, because a system that composes sentences is a
system that can compose a *wrong* sentence, fluently, with total confidence.

So the sentence is not trusted. It is **checked**, by reading it back:

1. The writer turns the term into English.
2. The reader turns that English back into a term.
3. If the recovered term is not **exactly** the one we started with, the
   sentence is not printed.

The reader is the crucial part, and the discipline is that the reader was
**frozen before the writer existed**. Its exact bytes were hashed and
committed in advance, so it cannot be quietly adjusted to agree with the
writer it grades. It is the same parser the rest of the system already
stands on, and it had never seen a realizer.

## The numbers

One run, on the committed library, executed once.

| | count | |
|---|---:|---|
| statements in the library | 12,777 | |
| statements the frozen reader can parse at all | **2,172** | 17.0% |
| of those, sentences that survive the round trip | **2,170** | **0.9991** |
| sentences that came out wrong | **0** | |
| statements that refused to try | 2 | |
| words used that were not in the dictionary | **0** | of 2,170 sentences |

The two refusals are worth a sentence each. They are both enormous number
literals — one 76 digits long, one 48 — and the machinery that spells
numbers in English is registered to work below a quadrillion. Rather than
round them, or approximate them, or emit something that *looks* like a
number, the writer declines. There is no `in words` line on those two
statements, and no apology either: absence is the refusal.

That 17.0% is not a footnote, and the project's own rules will not let it
become one. The gate that publishes the round-trip rate is required to
publish the denominator in the same sentence, so **0.9991 of 17.0%** is the
only form the headline is allowed to take.

Two blind controls stand behind it. Scramble the dictionary — map every
operator to the wrong word — and the same machinery scores **zero** out of
2,172; and the failure modes are counted separately, because it matters
enormously that 1,348 of those scrambled sentences **parsed perfectly well
and simply meant something else**, rather than collapsing into gibberish
the reader rejects on sight. Then take 3,722 correct sentences and corrupt
each by exactly one operator word: **not one of them** reads back as the
statement it came from.

## Five sentences that were wrong before anything was built

The result above is the deliverable. This next part is the one I would
actually take to another project.

A design document is a set of claims about a codebase, and claims about a
codebase can be *checked* rather than believed. This cycle checked five of
its own, and all five were wrong.

| what the design said | what the code actually said |
|---|---|
| render 90% of all 12,777 statements | only 2,172 parse at all — the target was not merely ambitious, it was unmeasurable |
| the library uses 95 operators, led by two named ones | that counted the wrong field. The field being rendered uses 64, and **neither** of those two appears in it at all |
| test the reader by scrambling the dictionary | scrambling *both* sides is just renaming things — it round-trips perfectly and would have declared the whole result void, for a reason having nothing to do with anything |
| the canonicaliser merges certain operators, so exclude them from the corruption test | it does no such thing. Those corruptions are legitimate, and belong **in** the test — which made the test harder |
| the receipt reports which variable is which | it reported two different numbering schemes as one, and they disagree on 110 sentences out of 2,170 |

Four of those were caught before a line of the thing was written. The fifth
was caught by review, and it is the interesting one: it changed **no
sentence and no verdict** — the check never depended on the numbering — so
the only person it could ever have misled was a human reading the receipt.
On one statement in twenty. It got fixed anyway, and published as a
correction with a date on it, because "the gate was unaffected" is the
tempting sentence and it is not the whole sentence.

There is a version of this cycle where all five of those go unchecked, the
run produces a number, and the number is defensible. That version is worse
in a way nobody would ever have detected.

## A small thing about seals

When the previous cycle timed this system against a language model, it
sealed the exact code that produced the answers — hashes committed
alongside the results, so nobody could improve the renderer afterwards and
quietly claim the old speed.

This cycle changes that renderer, on purpose. So what happens to last
cycle's numbers?

Nothing. That is the rule, and it was written down before it was needed:
you do not re-seal an old result to match new code. The old seal is
**retired**, a new one is created, and the old artifact stays exactly where
it is as the record of what was measured — verified, not asserted, by
checking that the hash recorded inside last cycle's results still matches
the file those results actually read. It does.

## What comes next, and why the title

Which brings us back to the 83% that cannot speak.

The obvious story about those 10,605 statements is that they are written in
a foreign language — a different mathematical dialect, from a different
tool, genuinely beyond this system's grammar. That was the story the next
design was built on, and before committing to it, somebody measured.

**Half of them are not foreign. They are the same grammar in a different
alphabet.** Substitute exactly two characters — `≥` becomes `>=`, `≤`
becomes `<=` — and **6,414 statements**, slightly over **half the entire
library**, parse under the reader that already exists. They were mute for
want of two rows in a table of which characters count as symbols.

What is left after that is the real thing: **4,191 statements** that no
alphabet fixes, because they carry constructions this grammar genuinely
does not have — quantifiers, typed variables, logical connectives. That is
the territory of the [next design](../DESIGN-foreign-voice.md), which
proposes to render them by borrowing, and to check the result not with this
project's own parser but with an **external proof checker** that was pinned
long ago and has no stake in the outcome. (That design is still under
adversarial review as I write this; its numbers here are the grounding
measurements, and the review may yet correct them, in which case the
corrections will be dated the way this cycle's five were.)

But the headline of that cycle is not the rendering rate. It is the
**register**: a frozen, published inventory of exactly what the system still
cannot say, construct by construct, with counts. A system that renders most
of a corpus and shrugs at the rest has told you nothing about the rest.

And the easy half is being deliberately set aside. Rendering 6,414
transliterable statements through a machine built for genuinely foreign ones
would let the next cycle claim a hard result for easy ground. So the two
glyphs get their own small, separate, honestly-labelled probe, and the
foreign-voice claim is measured on the 4,191 that earn the name.

Next release, the graph either speaks a dialect it cannot read — or it hands
you a precise, counted inventory of its own silence.
