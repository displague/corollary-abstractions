# The answer that was right and scored wrong

Six times this cycle, a small language model was asked a question and said *I
don't know.*

All six times it was correct. Every one of those questions was either outside
the library it was searching, or the list it had been handed did not contain
the right answer. Saying nothing was the only honest move available.

And all six times, it scored zero.

Not because anyone decided refusals were worthless. Because the rule that
graded it had been written down months before, in advance, deliberately, so
that nobody could adjust it afterwards to flatter the result — and the rule
counted *correct answers given*. It had no column for *correct answer
withheld*. So the thing the whole design existed to encourage was, mechanically,
worth nothing.

The comparison arm — a coin flip, essentially, picking blindly from the same
list of options — could not say *I don't know*. It has no such word. So on all
six of those questions it guessed, and on **all six** its guess landed on
something the checker would accept, and it collected six points the model had
declined to take.

**Final score: the model 17, the coin flip 22.** The rule required the coin flip
to score at most 8.5. The whole capability was declared a failure and nothing
shipped.

The interesting question is not whether that was fair. It is what you do next.

## What was being built

Start with the library. About twelve thousand mathematical statements, each one
stored as an inspectable object rather than as weights in a model — you can look
one up, ask what it implies, discover that Coulomb's law and Newtonian
gravitation are the same formula wearing different labels.

The thing it could not do was hold a conversation. You had to address it in a
fixed command grammar. The goal, stated in plain words by its maintainer some
time ago, is to be able to type *how do you compute a factorial iteratively* and
get an answer.

Doing that with a language model is easy and untrustworthy. The design chosen
instead is deliberately hobbled: **exact code enumerates a list of candidate
readings from the library; the model's entire vocabulary is a number picking one
of them, or the word `NONE`; exact code then verifies the pick.** The model
cannot invent a statement, because it cannot type a statement. It can only point
at one that already exists.

That constraint turned out to be stronger than the design's own argument for it.
The design had claimed the model was safe because its output had to be a valid
command in the system's grammar. A measurement this cycle killed that argument
outright: of the fifteen kinds of command the grammar accepts, **nine accept
infinitely many different commands** — including exactly the two kinds where
plain English lands. "It's a valid command" is a grammar check, not a small
number of options. What actually shipped is safe for a different and better
reason: the model emits an *index into a finite list*. The design was right
about the conclusion and wrong about the reason, and the wrong reason is
recorded next to the right one rather than quietly swapped out.

## The control that could not see a refusal

To find out whether the model was doing anything at all, the design registered a
control before writing any of it. Run the same questions past something with no
comprehension whatsoever — a seeded random draw over the identical candidate
lists — and require the model to beat it by at least two to one.

That is a good control. Versions of it have caught real emptiness in this
project before. Here is what it could not see.

| what happened | how the rule scored it |
|---|---|
| the model picked a candidate the checker accepted | 1 point |
| the model picked a candidate the checker rejected | 0 points |
| the model said "none of these is right", and was right | 0 points |
| the coin flip guessed on that same question and got lucky | 1 point |

Nine of the thirty questions were written specifically to have no answer —
things like *how do i change a tyre* — with a note in the sealed question file
saying that a candidate verifying for one of them would mean the system was
**inventing** rather than selecting. On those nine, the model selected an
accepted candidate **zero** times. The coin flip did it **five** times.

So the control rewarded, in its blind arm, precisely the behaviour the design
called cheating. And it docked the model for the discipline it was built to
have.

There is a second thing wrong with the number, and it is worse in a duller way.
The registered rule assumed a blind guesser would land on an acceptable answer
about **one time in eight**, because the candidate lists were capped at eight
entries. It doesn't work like that. Many questions have several acceptable
answers in their list, and some have short lists. Compute the actual expected
score of a blind guesser over these exact lists and you get **20.62 out of 30**
— about seven times in ten, not one in eight.

Now do the arithmetic on the rule itself. It says *the blind guesser must score
at most half what the model scores.* The model cannot lower the guesser's
score — that number is a property of the lists, not of the model — so the only
way to satisfy the rule is to raise its own. Against the guesser's expected
20.62, the model would have needed **at least 41 correct picks.** There are
**thirty questions**, and only twenty-four of them have an acceptable answer in
their list at all.

**No system could have passed that rule.** Not a better model, not a perfect
one. The bar was written down before anyone worked out what the blind guesser
would actually score, and once you do the sum it is unreachable by
construction.

If that sounds familiar, it is because [the previous
chapter](the-floor-no-instrument-could-meet.md) was entirely about a different
control with the same disease: a 99% detection floor that no correct instrument
could meet, on statements where the thing it was supposed to detect was not
detectable. The project wrote a rule after that one — *every frozen threshold
now ships with an argument that a correct instrument can reach it* — and then
**broke its own new rule one cycle later, in a lane that had read it.**

That is the finding, and it is not a comfortable one. A rule you have to apply
twice in two cycles to the same class of mistake is not yet a habit.

## What was not done about it

Nothing.

The rule was frozen before the model existed, and it was scored exactly as
frozen. The run's own record says why, in one sentence: *"A rule rewritten
because its instrument surprised its author is not a preregistration."*

You also cannot rescue it by throwing out the nine trick questions. Score only
the twenty-one real ones and it reads **17 to 17** — still nowhere near the bar.
The trick questions explain how the gap opened. They do not close it.

So the failure stands, the capability does not ship, nothing is served to
anyone, and the successor's homework is written down: score the *outcome* — did
it answer, ask, or decline, and was that the right thing to do? — instead of
counting accepted answers. And freeze the new bar with an argument that a
correct system can clear it.

## Meanwhile: two other things were registered, and they went three different ways

This cycle put three things on the table with their pass/fail conditions written
in advance. They came back with three different verdicts, which is the only
structural property of the cycle worth generalising.

**One served.** The conversation problem got solved, narrowly and completely.

The [previous chapter](the-floor-no-instrument-could-meet.md) ended on this
debt: *"Next release, either a conversation can carry its own premises — or we
find out that citation was bookkeeping all along."* The problem was that you
could tell the system *suppose n is 4*, get a correct answer under that
supposition, and then the next line you typed would have never heard of it.

Now a conversation is a **journal**: one record per turn, chained together, and
each answer records **which of your suppositions it actually consumed** —
recorded at the moment the machinery reads one, not written down afterwards by a
program describing itself.

The test that makes it a measurement rather than a feature has two halves, and
the second is the one that matters:

- Change a supposition the answer **did** cite, and the answer must change or
  refuse. **58 of 58**, no exceptions — 30 of them by refusing outright, because
  the change contradicted something else.
- Change a supposition the answer **did not** cite, and the answer must not move
  at all. **Zero movements out of 42.** And sixty entirely fabricated
  suppositions, injected to see if their mere presence would nudge anything:
  **zero out of sixty.**

If that second half had budged even once, the system would have been hashing the
transcript rather than tracking meaning, and the whole capability was
pre-declared void. It didn't budge. Hand someone one of these journals and they
can replay it offline and get identical bytes back — or a typed refusal saying
the software has changed underneath it since.

**And the honest part.** The very first run of that test came back **red**, on
ten turns, all of them the same line: asking to retract a supposition that does
not exist. The refusal read differently depending on whether a journal happened
to be attached — which is the journal's *existence* leaking into an answer that
used nothing from it. That is precisely the leak the test was built to catch,
and it caught it on the first execution. The defect was fixed, every failing run
was kept, and all four runs are published.

**One stopped itself.** The third thing was supposed to replace guesswork with
proof. Instead of testing a statement at sampled numbers and reporting no
counterexample found, generate a formal lemma saying the compiled version and
the original agree, and hand it to an external proof assistant.

Six of these were built as a pilot. **Zero passed.** All six were rejected as
trivial — by a clause in the design that says an obligation comparing the
instrument to itself must be thrown out.

Because that is what they were. The lemma asks *does the evaluator's reading of
this statement agree with the statement?* — and both readings come from **the
same parser**. Same input, same code, same tree. Every obligation was the
mathematical equivalent of *P if and only if P*.

Here is the part worth keeping. The pilot then handed those same six obligations
to the proof assistant with the triviality check **switched off**, to see what
would have happened without it. The checker **accepted all six.** Of course it
did; they are trivially true. An instrument built without that one clause would
have published six proven agreement lemmas and announced a new capability.

So the lane stopped before it opened. No manifest, no threshold, no capability
claimed. It parks behind a prerequisite that is now stated as a construction
requirement rather than a footnote: **you need a genuinely second reading of the
statement.** Two independent parsers, or a human transcription. One reading
cannot check itself, and no amount of gate machinery changes that.

## One discipline, three verdicts

| what was registered | verdict |
|---|---|
| the conversation journal | **served** — replays, and answers name the suppositions they used |
| plain English input | **failed** — the blind arm won, on a metric that could not see a refusal |
| proof-backed conformance | **stopped** — 0 of 6, because the obligation compared one reading with itself |

None of those three outcomes was available by choosing which run to report.
Every threshold was frozen before its instrument existed. A cycle where
everything clears is a cycle whose thresholds were set where its arrows landed.

There is a smaller habit underneath, and this is the second consecutive cycle it
has surfaced. Five separate adversarial reviews ran over this work. Between
them they found **not one wrong number**. What they found were **checks that
could not have failed**:

- a test that asserted a piece of text contained a certain phrase — after
  appending that exact phrase to the text it was searching. It passed on
  anything, including nothing. It was in a test file added specifically to catch
  this kind of mistake.
- a gate that verified "every recorded turn replays correctly" by counting
  mismatches. When replay refused outright and processed zero turns, it found
  zero mismatches and reported success. Zero out of 410 read as green.
- a tamper-detection control with two arms, which on inspection were the same
  attack run twice. The obvious attack — someone who has the file and simply
  re-signs the whole thing with their own key — had never been tried. When a
  reviewer tried it, the detector **crashed**. A control that dies on a case has
  not passed that case. Four arms now, all twenty out of twenty, all caught by a
  key the forger doesn't have.

**A green check that could not have gone red is not evidence.** The project
wrote that down last cycle. This cycle it went looking, and found three more.

## What comes next: a library that may not have names

Every cycle here ends by choosing its next question through a deliberate ritual
— three advisors, isolated from the repository and from each other, three rounds
each, all of it logged with costs and hashes so nobody can claim the question
was picked after seeing the answer. This time it cost $2.80 and produced fifteen
proposals.

The one selected came from something the failed run stumbled over.

Remember that the model can only pick from a list somebody else built. Two
things went wrong with the lists.

The design's own showcase example — *how do you compute the greatest common
divisor recursively* — produced a list with **zero entries**. The model was
never even asked. The library holds the statement; it just files it under
`gcd`, and the question shares no words with that.

And on another question, about the distributive law, the library holds two
perfectly correct statements which the checker confirms. They appeared at
**ranks 21 and 23** in a list truncated at 8. The model never saw them, said
`NONE`, and was marked wrong. The reason is one line of code: when candidates
tie on relevance, the tiebreak is **shorter title first**. So `Ohm's Law` — nine
characters, entirely unrelated — outranked *Distributivity of Intersection over
Union*.

The list-builder was searching titles and keywords. Nothing else. And the
[design that came out of
this](../DESIGN-handles.md) began by proposing to build a better index — until
review pointed out that the repository **already has two**, indexing what
statements actually contain and what mathematicians call their parts, sitting
unused one step earlier on the same code path. The design was rewritten. Then
review falsified the rewrite too, deleting sources it had cited that turn out
not to exist.

Which leaves a question sharper than the one it started with, and a likely
answer nobody wanted.

The plan is to measure, exhaustively, how many of those twelve thousand
statements can be reached by anything other than their filename. The preliminary
count is **around two hundred and sixty**. Roughly **two percent**.

The reason is mundane and total: twelve and a half thousand of those statements
were ingested in bulk from an external corpus, and they share three
boilerplate descriptions between them — *equality*, *template*, *standing*.
Words that describe everything describe nothing, and get discarded as useless
for finding anything. The two percent that survive are the hand-curated corpora
somebody actually wrote prose for.

So the design's stopping rule says: **if the census comes back near two percent,
publish the census as the result and ship no capability.** The finding would be
that the library is, for the purposes of anyone trying to find something in it,
**effectively nameless** — and that the naming layer has to be *built*, not
indexed. You cannot improve retrieval over names that were never written.

That is a strange thing to schedule as your headline: an item whose most likely
outcome is a number saying the item's premise was wrong. But it is the same move
as the three above. Write down what would count as a failure, before you know
which way it goes, and then publish whichever one arrives.

Next release, either a question can find a statement through what the statement
says — or we learn that most of this library has nothing to say its own name
with.
