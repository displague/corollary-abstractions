# The library that had no names

Imagine a reference library where every book is real, correct, and
cross-checked — and almost none of them have a title on the spine. You can
still reach a book, if you already know exactly what is inside it. You cannot
walk in and *ask* for one, because there is nothing to ask *by*.

That is the finding this cycle came back with, measured to the digit. And it
is not the finding anyone set out to prove. It is the one that arrived when two
separate attempts to measure the program honestly both came back as findings
about the program rather than as new things the program could do.

A stranger can carry away the whole cycle in one sentence: **this library can
compute far more than anyone can name to ask for, and most of the evidence it
produces cannot outlive the program that made it.**

## What the last chapter left owing

[The previous chapter](the-answer-that-was-right-and-scored-wrong.md) ended on
a debt. A small language model had been wired up to take a plain-English
question and pick, from a list the program built, which stored statement the
question was about. It failed — beaten by a coin flip on a scoring rule that
could not see a correct refusal. But the *interesting* failure was quieter: the
list-builder kept coming up empty. The design's own showcase question — *how do
you compute the greatest common divisor recursively* — produced a list of
**zero** candidates, even though the library holds exactly that statement. The
list-builder searched titles and keywords only, and the question shared no word
with the title `gcd`.

So the chapter closed with a wager: *next release, either a question can find a
statement through what the statement actually says — or we learn that most of
this library has nothing to say its own name with.*

This is the release where that wager was settled. It settled the second way.

## The census

The plan was to stop searching titles and start indexing what a statement
*contains* and what mathematicians *call its parts*. The repository turned out
to already hold two such indexes, sitting unused one step earlier on the same
code path — one over a per-statement glossary of the symbols it uses, one over
the operations that appear in its parsed form. Neither reads the title at all.

Before building anything on top of them, the cycle did the honest thing first:
it counted. Of the roughly twelve thousand eight hundred statements in the
library, how many can either index give a *specific* name to — a name that
points at a handful of statements rather than at thousands?

| index | statements it can specifically name | share |
|---|---|---|
| the glossary index | **263** | 2.06% |
| the operations index | **306** | 2.39% |
| **either one** (everything a person could plausibly type) | **417** | **3.26%** |

Ninety-seven percent of the library has no specific name from either index.
(`experiments/handles_census.json`.)

The reason is blunt and total. About twelve and a half thousand of these
statements were ingested in bulk from an outside corpus, and between all of
them they carry **nine** distinct glossary words — words like *equality*,
*slot*, *template*, *standing* — and six of those nine words each blanket more
than twelve thousand two hundred statements at once. A word that describes
almost everything describes nothing, and gets discarded as useless for finding
anything. What is left — the 3% with real names — is almost exactly the
hand-curated corpora that a person actually wrote prose for.

And there is no clever threshold that rescues the rest. The index has a knob
that controls how specific a name has to be to count; you can open it as wide
as you like, and the number of bulk statements that gain a specific name climbs
to **302** and then stops there, forever, at every setting. Three hundred and
two, out of twelve and a half thousand. You cannot tune your way to names that
were never written.

So the design carried a stopping rule, written down before the count was known:
*if the census comes back near two percent, publish the census as the result
and ship no capability.* It came back at two-to-three percent. The rule fired.
The verdict, in the design's own words: **the ingested library is effectively
nameless; the naming layer must be built, not indexed.**

## The sentence that is sharper than the number

A second, smaller count was taken alongside, and it is the one worth keeping.
Set aside naming entirely and ask a different question: how many statements are
shaped so that the engine could *do* something with them in a single step —
consume a hypothesis, discharge a bound? The answer is **9,048** of them, about
seventy percent (`experiments/onestep_census.json`).

Now overlay the two counts. Of those 9,048 statements the engine could compute
with, how many carry a name a person could type to ask for one?

**One hundred and twenty-five.**

The mass the program can *work on* and the mass a person can *reach* are almost
disjoint. The engine is holding nine thousand answers to questions no one has
any way to pose. That is not a bug in either count. It is the shape of the whole
project stated in two numbers: the computing got far ahead of the addressing.

(Every load-bearing number here was reproduced by an adversarial reviewer from
the committed artifacts — down to agreeing, statement by statement, on all
12,777 classifications. Two defects were caught in the process: two files
claimed a writer that did not exist, and a "most-reused" ranking whose ties
were being ordered by a hash seed rather than by anything real. Both were
fixed. Not one headline number moved.)

## The other census: evidence that cannot travel

The cycle ran a second measurement, on a different anxiety entirely, and it
came back the same species of answer.

The program produces *receipts* — little records that say "this was checked,
here is the proof." The natural assumption is that a receipt is portable: hand
it to a stranger and they can re-verify it without trusting you. The census
asked, bluntly, of nineteen distinct kinds of receipt the program emits: **if
you delete the program itself, how many of these can still be re-checked?**

| verdict | kinds | meaning |
|---|---|---|
| **SURVIVES** | **1** | re-checkable with the program gone |
| **NEEDS-PROGRAM** | **10** | re-check requires this repository's own code |
| **UNTESTED** | **8** | no re-check could even be attempted |

One of nineteen (`cold/census_run2.json`). The single survivor is a receipt
that names its checker — an external proof assistant, a third party the
repository did not write — and carries enough to rebuild the check from
scratch. A reviewer did exactly that, cold, with none of this project's code
present, and it held.

The lesson is in *which* receipt failed. The most self-describing receipt in
the whole tree — one that literally carries its own "here is the command to
re-check me" — came back **UNTESTED**. The command it names to re-check itself
depends on a library that nothing in the project pins, so the re-check cannot
run *even with the program fully present*. Carrying your own instructions is not
the same as being checkable. **Offline-checkability is earned by naming an
adjudicator that is not yourself — not by carrying a digest of your own work.**

## The instrument that caught itself

There is a methodology thread running under both censuses, and it is the third
finding.

The evidence-survival census, on its first run, reported nine receipt kinds as
"needs the program" — a healthy-looking result. Then review found that the arm
which was *supposed* to prove it — the step that deletes the program and shows
the re-check breaks — had a flaw that meant it broke the same way whether the
program was there or not. The test could not have come out any other way. It was
not measuring what it claimed.

This is the same shape the reviews have been catching for three cycles now: a
check that passes on everything, including nothing. What is new is the fix.
Rather than trust the deletion, the corrected census runs *two* arms for every
receipt: one with the program present that must **succeed**, and one with it
gone that must **fail**. A receipt only counts as "needs the program" if it
passes the first and fails the second — the program is made to demonstrate,
against itself, that the deletion is what did the damage. That correction is
why the honest number is one-of-nineteen and not something rosier.

An instrument that can catch itself measuring nothing is worth more than a
number that came out flattering. Both this cycle's headline results are
findings, not capabilities, and neither was available by choosing which run to
report: every threshold was frozen before the thing it judged existed.

## What comes next: the person finally speaks

For four cycles the project has been building scaffolding around one goal its
maintainer wrote down long ago — to let a person hold a plain conversation with
this library, supplying assumptions the library does not itself contain and
getting back an honest answer under them. A session that remembers its
suppositions was built last cycle. A proposer that reads plain questions was
built and failed. And now a census says the library cannot yet be addressed by
name at all.

That last finding is exactly what clears the way, because the next step does not
need names. [The design written for it](../DESIGN-guest-axiom.md) — written
before this post, so the next question could not be chosen after seeing the
answer — turns the conversation *inbound*. A person supplies a hypothesis the
library does not hold: *suppose this is true.* The system does not believe it,
does not file it, and does not guess. It hands back a machine-checked
implication — *if what you assumed holds, then this follows* — with the guest
assumption named, undischarged, and explicitly not endorsed. And when the
person's assumption contradicts what the library can prove, the system can tell
them so, and show the counterexample.

It runs, next cycle, on the roughly two thousand three hundred statements the
system can already speak aloud in verified English — the part of the library
that *does* have something to say its own name with. A companion measurement
([ECHO](../DESIGN-echo.md)) goes first, asking whether a sentence the system
speaks determines the statement it came from: the library's first name that a
person did not have to type.

The census said the library is nameless. The answer is not to invent names for
it. The answer is to let a person bring their own premise to the door — and to
prove, out loud, what follows from it.
