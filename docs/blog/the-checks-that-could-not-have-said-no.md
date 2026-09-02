# The checks that could not have said no

A library has a rule: nothing goes on the shelves unless a cataloguer signs
for it. To prove the rule works, the librarian writes thirty-two little
stories about someone trying to sneak a book past the desk, and for each one
names the guard who would catch it.

Then somebody actually reads the guards' job descriptions. One of them turns
out to be *"stand in an empty room and confirm that a book placed in that
room is in that room."* It is a perfect guard. It has never been near the
desk. And it was answering for seven of the thirty-two stories.

That is this release, and a stranger can carry it in one sentence: **a set of
safety checks all came back green, and a review found that several of them
could not have come back any other way.** The capability underneath them is
real and it works. What was not real was the evidence that it was safe — and
the only instrument that noticed was a person reading the code.

## What the last chapter left owing

[The question it bound and would not ask](the-question-it-bound-and-would-not-ask.md)
ended on a promise about vocabulary. This project is, at bottom, a library of
mathematical statements with a strict rule against saying anything it cannot
ground. You could already tell it *suppose x = 5* and have that mean
something. Tell it *suppose parent(alice, bob)* and it kept the characters
and understood nothing — not because it disagreed with you, but because you
had never had a way to say what your vocabulary **is**.

So the debt was specific: let a person declare a symbol. A name, how many
arguments it takes, what kind of thing goes in each slot. Admit it, or refuse
it — with **exactly one** reason.

That shipped. `declare holds_for/2 (variable, variable)` is admitted into a
ledger that lives and dies with the conversation; `declare pairs_up/2
(marsupial)` is refused, with one clause named, because `marsupial` is not
one of the nine kinds the schema knows. From then on, using a declared symbol
with the wrong number of arguments is refused **by name**, where the day
before it was opaque text. Nothing declared survives the session. Nothing
declared reaches a library file.

The measurements are not small. Fourteen thousand and sixty-three inputs
decided, every one of them landing on exactly one verdict with exactly one
reason, **zero** falling through. The inputs were not hand-picked: a program
took every line in the sealed test corpus and mutated it — delete each word
once, then replace each word once with every other word that appears anywhere
in the corpus — which produced fourteen thousand cases nobody chose. All
eight possible refusal reasons were reached. Twelve gates green.

And then the review.

## The four things a review found that no gate did

An independent adversarial pass reproduced every number in the first
registered run and returned *merge after fixes*. Not one of its findings was
arithmetic. All four were about what the numbers were evidence **of**.

**The mutants were prose.** The thirty-two "attempts to smuggle a declared
symbol somewhere it must not go" are *descriptions* of attempts. Nothing in
the repository executes one. What the gate can honestly observe is that a
detector — mapped to each story by hand, in the runner, not sealed with the
story — fires on live material. Run one had reported "32/32 stopped" without
that distinction.

**Two detectors could not fail.** One of them created a temporary directory,
wrote a name into it, and then searched for the name and found it. That is a
fact about how string search works; it is true of any directory in the world;
and it was answering for seven of the thirty-two. The other asserted that a
particular module contains no text equal to the run's output filenames —
true of every module that never mentions them. It has been retired by name.

There is a small comedy inside the repair. The fixed version runs its search
against the *real* repository tree, with a control that is supposed to find
nothing. On the first rehearsal it found something: the control's own probe
string, written as a literal in the file doing the searching, which is itself
inside the tree being searched. The probe name is now derived from a hash so
it cannot exist anywhere in advance.

**The blind control could not fire.** This is the one that should travel
furthest. The design had committed, in advance, to trying to kill its own
result: fit a deliberately stupid rule that looks only at the *surface* of a
declaration line — how many words, how long, is the command word there — on
half the examples, then score it on the other half. If the stupid rule agrees
with the real checker by more than ten points above the base rate, then the
verdict never depended on the ledger or the schema at all, the capability is
void, and the release ships a negative.

The stupid rule scored 0.684211. The threshold was 0.784211. Comfortably
under, so the sentence did not fire.

Except: the **best** rule in the entire registered family of ninety-five tops
out at 0.736842 on that half. **No member could have fired it.** Whatever the
fitting half had chosen, the voiding sentence was unreachable. And the rule
that was chosen predicts the same answer for every single row — so its score
equalled the base rate by *arithmetic*, not by having learned anything.

| the number | what it is |
|---|---|
| 0.684211 | what the fitted rule scored |
| 0.684211 | the base rate on the same rows — identical, because the rule always says the same thing |
| 0.736842 | the best score **any** rule in the registered family could reach |
| 0.784211 | the score needed to void the capability |

A held-out half of nineteen rows moves 0.0526 per row. To clear ten points
strictly you need three more rows than the majority, not two — which is
fifteen points, not ten. Nobody had computed the family's own ceiling against
its own threshold. It is one line of arithmetic and it would have caught this
before any score existed.

**And the leak.** The program publishes a small grammar so a person can see
what to type, and the `declare` row carried an example line. The example was a
**sealed test symbol** — one of the ones the containment gate exists to keep
out of committed files. It sat in the served grammar, in the generated file
that echoes the grammar, and in the capability sheet served from it, through
the whole first run, while the gate scored that exact smuggling story as
*stopped*.

The gate could not see it for a reason that is worth keeping: the search is
scoped to the files the run **writes**. The name was already committed. A
containment check pointed at a run's outputs will never look at anything the
run did not produce.

An example is a value. A value drawn from a sealed corpus inherits that
corpus's prohibitions. Every generated artifact that echoes an authored
example is another copy of that value.

## What was done about it, and what was deliberately not

The first run is not deleted and not re-scored. It sits in
`experiments/superseded/` with a note saying what it is: the record of what
the run-one runner scored, and **not** evidence that the capability was
contained, because two of the checks behind that number could not have said
otherwise.

Five dated amendments carry every repair, and each one states in its own
bytes that it was written **after** the first score and that it loosens
nothing. The floor is still thirty of thirty-two. The margin is still ten
points. The seven pinned files are byte-identical across the repair. Then the
whole thing was run again, on the repaired instruments, and it is that second
run the release claims.

A richer family of 2,632 surface rules was also tried, because the obvious
question is whether a smarter stupid rule would have fired. Fitted honestly —
on the fitting half, with the tie-break declared before the fit — it scores
0.684211 and does not fire. Allowed to cheat, by picking the rule that does
best on the half it is scored on, it reaches 0.789474, above the threshold.
That number is published, and it is **labelled in the artifact as selection
on the scored half, which is not a control score**. It would have been very
easy to report the higher number as the good news that the control was
strong. It is the opposite.

The gate is still the family that was registered in advance, because a
control chosen after a result is not a control.

## The other thing that ships, which is a "no" the project chose not to give

There is a live hazard in code that ships today, found last cycle by
reviewing a design for code that did not yet exist. The template parser
rewrites any identifier beginning `sum_`, `prod_`, `lim_`, `max_` or `min_`
into an aggregate, discarding everything after the underscore. `sum_total(x)`
becomes `sum` applied to something, and `total` is gone. No refusal. And
`sum_total` and `sum_anything` produce one identical tree.

It would have been satisfying to refuse it. A census says not to: across
14,830 committed templates, exactly **seventeen** contain such an identifier
— sixteen `sum_i` and one `lim_h`, real big-operator index names in nine
disciplines. There is no `prod_`, `max_` or `min_` occurrence at all. A
refusal breaks seventeen sealed parses that are not defective.

There is a heuristic that would separate them — every one of the seventeen is
a single letter, so "a word-shaped suffix is suspicious" works perfectly on
today's corpus. It is **deliberately not implemented**, because it is a new
judgement nobody priced, and it would put the parser in the business of
deciding which captures deserve to be mentioned.

So the answer is total disclosure instead. The rewrite is now recorded in the
term's own receipt — the rule, the word as the author wrote it, the head it
became, the characters that were dropped — and `sum_i` is recorded exactly as
loudly as `sum_total`. Being total is what makes it judgement-free.

The parser still rewrites. That sentence is in the release notes on purpose,
because the new declaration surface *does* refuse `sum_total` when a person
declares it, and it would be very easy to read that as the parser having been
fixed. It has not been.

## What this does not license

It does not license "the system understands declarations." It licenses that a
total function decided fourteen thousand inputs with one reason each and no
fall-throughs, that a use at the wrong arity is refused by name, and that
nothing declared crossed into a file.

It does not license any claim about what people will declare. The test
corpus was written by this repository. Thirty sealed real inbound questions
from an earlier cycle were checked against the declaration grammar: **zero**
of them parse as declarations. That number was pre-committed before the run,
with its reading fixed in advance — approximately zero was expected, it is
neither a failure nor evidence of demand, **and it may not be read either way
now**.

And the green on the safety gates means something narrower than green. The
write check evidences *no writes observed under this harness*, never *cannot
write*. The blind control evidences that **the registered control** did not
separate the verdict — not that no surface rule can. That caveat is not in a
footnote; it is a field in the artifact, sitting beside the licensed
sentence.

## What comes next: a refusal that tells you what would have worked

Here is the gap the green half makes visible.

The whole point of letting a person declare their own vocabulary is that it
is **their** vocabulary — words the program never authored. When the program
refuses a line, it names the rule that stopped it. It does not name what
would have worked. If you wrote the corpus you can read the clause. If you
did not, you are guessing between nine categories, five forbidden prefixes,
and 286 names in a list you cannot see.

[The design written for that](../DESIGN-repairable-refusal.md) — written and
reviewed twice before this post — is one idea. Freeze a tiny algebra of edits
as **data**, before any test case exists: change a category, insert one,
delete one, change the arity, change one character of the name. Give each a
cost of 1. Then, when a line is refused, search *exhaustively* for the
cheapest edit sequence the unmodified admitter accepts — and prove it is the
cheapest by enumerating the entire ball of cheaper candidates and showing
none of them work. A second program, written against the same frozen
specification, re-enumerates and checks the arithmetic. If no repair exists
inside the bound, say that, and publish the size of the ball you searched.

A refusal stops being a wall and becomes an instruction.

What would count as a miss is written down before the work, and this time the
lessons above are gates rather than good intentions:

- **The corpus does not come from us.** Every scored gate this project has
  ever run used fixtures it wrote itself. Here the refused lines must come
  from a non-author — the digest-pinned local model already in the tree,
  provisioned with nothing but the published grammar row. It is a machine, not
  a person, and the artifact has to say so in those words. If it cannot
  produce 58 distinct refused lines, the slice publishes *untested* and stops.
- **The control's ceiling is computed before the headline number is read.**
  Exactly the one-line computation nobody did this cycle — and placed at the
  earliest point where it is not circular, not the earliest point that sounds
  strongest. A family that cannot fire is a **construction defect**, not a
  pass.
- **The mutants execute.** Twelve programs that actually perform the smuggling
  attempt and report what happened, each with a machine-readable detector
  named in the seal. Twelve that run are worth more than thirty that are prose,
  and if that trade is wrong the number is the thing to move.
- **The containment sweep covers the whole committed tree** — documentation,
  generated files, grammar rows and their echoes, comments, filenames — and it
  casefolds before matching, so re-spelling a sealed name is not an escape.
  The design document is inside its own sweep's scope, which is why its
  examples are placeholders verified absent from everything.

The design is also honest about a risk its own gates do not price, and it is
the interesting one: **the algebra defines the difficulty of the corpus.**
Freeze the edits before the stranger writes and you have priced looking at
the answers — but not familiarity. Every certificate could be sound, every
repair genuinely minimal *within the algebra*, and the result would read as
"refusals on this surface are repairable" while meaning only "the algebra
covers the mistakes we expected." The clean fix is a second stranger writing
the algebra blind. It is named, and it is not taken.

There is one more coupling worth stating, because it is this cycle's finding
walking back in through the front door. The yield gate wants at least 60% of
refusals repaired. The blind control can only fire when the majority class
leaves room — and above 90% it cannot fire by arithmetic at all. **The better
the capability performs, the more likely its control is structurally void.**
So the rule is fixed in advance: if the ceiling turns out unreachable, the run
reports the capability **licensed but uncontrolled**, publishes all three
numbers side by side, and the headline sentence is simply not written.

A high score does not buy its way past a check that could not have said no.
That is the whole lesson of this release, and next cycle it is a clause.

---

*Where the other fourteen ideas went.* The design came out of three isolated
outside inquiries — fifteen proposals, none of which had seen this
repository's plans. Two finalists were declined for reasons that are on the
record rather than on taste: **necessity certificates** for a turn's
assumptions (declined because a refusal that names a premise may be naming it
for a *lookup*, not because the answer needed it — and the control it
proposed cannot reach exactly that case; it parks behind an afternoon's
counting of recorded sessions) and **an attack on the project's own published
cross-discipline identity claims** with a deliberately coarser instrument
(the highest-ceiling decline; it parks behind counting whether at least eight
such claims even depend on the machinery it would attack). The selected
direction was itself **cut in half**: it had elegantly unified refusals with
*budgets*, and shipping the budget half would have quietly un-parked a cost
lane that has now been deliberately passed over nine consecutive times. It is
recorded as that park's best available mechanism, and not taken.

Six proposals independently re-invented ground this project already holds —
an English reader built by inverting its own writer; structural addresses for
the unnamed bulk of the library; a genuinely independent second reading of
any claim, arriving for the **fourth** time; pre-committed cost bounds,
again. Those are recorded as evidence *for* keeping those lanes parked, not
as new lanes. One arrived a **third** time at the overdue red-team of the
durable-write gate, and this time carried the piece that park has always
lacked: mutate the *gate* as well, so the kill matrix measures whether the
attack corpus is any good, rather than whether the gate can tell an attack
from a friend.

And three proposals folded, which is its own kind of finding. The most
useful: a proposal to split and rejoin a goal collapsed on the discovery that
**this program has no goal object at all** — nothing outlives a turn as an
open obligation. That is now filed as a named gap rather than an assumption.
The obligation that carried over from the last roadmap — *re-examine the
naming question once `declare` ships* — was examined, and the answer is
**no**: a declared symbol is fresh by construction, because the checker
refuses any name the library already owns. The declaration surface is built
to bounce off the library's namespace, not to reach into it. Recorded as a
negative, which is the only way an obligation like that gets discharged.
