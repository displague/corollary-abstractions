# The curve changed sign

*We asked whether a pile of imported mathematics starts explaining
itself. At thirty-two statements the answer was no. At twelve
thousand it was yes. That is a curve, not a victory lap.*

The [previous chapter](the-bag-still-wins.md) ended on a promise
and a refusal.

The promise: give the dumbest baseline in the project — a bag of
operators with no idea what a theorem *says* — one number both
sides are scored on, before either of us claims victory again.

The refusal: two imported statements had started pointing at each
other, and then two hundred and fifty-one more had done it at
scale, and we would not call that a finding. Two observations are
not a curve. Shared small integers are not structure. A rising
line means nothing until you know what chance produces.

Version 0.11 is the cycle that kept both of those.

The central wager of this project has not changed:

> If an operation has an exact answer, it should live outside
> the weights.

Parsing, equality, “are these the same formula?”, and “did this
check pass?” are exact. They should not be approximated by a
network. What we are allowed to *learn* is the leftover: which
structure matters, which proposal to try next. For that leftover
to mean anything, the world the leftover points at has to be
real — a graph of statements that actually refer to one another,
not a thicker catalogue of the same isolated lines.

So we asked a question a person can hold without our internals.

Imagine you import more and more pages of formal mathematics
into a library. Each page is a statement: an identity, an
inequality, a recurrence. Each statement is made of parts —
`x²`, a remainder, a product. After you have imported enough
pages, do those parts start having *homes* in other imported
pages? Does the library begin to explain itself, or do you just
have a thicker book?

Last time we had hundreds of imported pages, and a hunch. This
time we imported the rest of the ones our parser can honestly
read — 12,514 of them, 123 refused and counted — and we compared
the library to a fake one.

## What “explaining itself” means here

We do not count two statements as explaining each other just
because they both contain `x²`. That is sharing. Sharing is
symmetric and cheap. On a shelf of contest inequalities, almost
everything shares a square.

We count a part as *grounded in the imported layer* when the
best other owner we can find for it — the most independent
statement that contains it — is itself an imported statement.
Ownership is not symmetric. A fashionable square that already
belongs to the older, hand-written algebra does not count as
the new pages explaining themselves.

Then we build a fake library. Same operators, same small
numbers, same sizes of trees, reshuffled so that no real
statement is being copied. If the real library’s imported
parts have imported owners *more often* than the fake one,
something structural is happening. If not, we imported
coverage and told ourselves a story.

The comparison, and four predictions about its shape, were
written down *before* the 12,514 pages existed. That was the
point of the last chapter’s refusal. We were not allowed to
pick the test after seeing the data.

## The library at thirty-two pages is worse than a shuffle

Here is the difference between the real imported layer and the
fake one, as the pile grows.

| imported statements | real − fake |
|---:|---:|
| 8 | **−0.041** |
| 32 | **−0.024** |
| 128 | +0.046 |
| 512 | +0.042 |
| 12,515 | +0.063 |

*The last row is one larger than the 12,514 pages of this wave:
the imported layer also contains a single older statement from
an earlier experiment, and we did not exclude it to make the
number rounder.*

At eight statements, and again at thirty-two, the real library
sits *below* the shuffle. Shared squares and small numerals do
not beat random trees drawn from the same inventory. That is
exactly the size we actually had last time. If we had stopped
there — and we almost did; that was the honest limit of the
first wave — the publishable sentence would have been:
importing buys coverage, not structure. We would have been
obliged to write it.

The sign flips by one hundred and twenty-eight statements.
After that the gap is positive. At the full pile it is
forty-five times the shuffle’s seed-to-seed jitter. About
ninety-eight thousand of two hundred and eight thousand
considered parts have an imported owner. The older
hand-written layer barely moved: the new pages did not buy
this by leaning on the old ones.

We also asked the question that would have made the curve a
fact about `x²`. Delete the single most common part — a
squared slot, hosted by 6,870 statements — and see whether the
gap collapses. It *widens*, from 0.063 to 0.127. The fashionable
square belongs to the older algebra. It was diluting the rate,
not carrying it.

And the measurement we refused to take as the headline is, at
this scale, a vacuous 1.0. If you only ask whether a grounded
part’s shape also occurs somewhere else in the imported pile,
the answer is 181,270 out of 181,276. Sharing is nearly
universal on a shelf of olympiad inequalities. Ownership of
those same parts is 0.543. Reporting the first number as the
second is how a project talks itself into believing a curve.

None of this is a proof, a usefulness claim, or a certificate
that the 12,514 pages are true. They entered as formal
statements without a machine-checked bridge. A part having an
owner inside the library is a structural fact about the graph.

## The one number we promised the bag

The other headline is the one we already knew and finally
refused to split into two victories.

The operator bag still forms more pairs than the matcher. On
the full graph it forms 9,041,744 of them. The matcher forms
1,991. We registered, before this re-run, a single figure of
merit: of the pairs the bag forms, how many are the matcher’s
typed twins? **0.0220%.** A size-matched draw from the bag
recovers one real twin in 1,991.

The bag misses one pair, and we know which. The importer
prints a subtraction as “plus a negation”; a hand-written
double-angle cosine writes an ordinary minus. Same statement,
different ink — so the bag, which only looks at which symbols
turn up, sees two unrelated things and never puts them
together. The matcher pairs them anyway. It is the only true
pair in the whole comparison that the bag misses and we catch —
one, out of nine million it offered. The exception has a name,
and the denominator is finally in the open.

The bag still wins on volume. We still own correctness. The
last chapter said we would not call that a win until both
sides were scored on one number. This is that number. It is
not flattering, and it is not a retraction. It is what a
straw man that will not fall looks like in public.

## What this cycle is not

It is not a benchmark. The 12,514 pages came from one source —
a large set of contest-style inequalities — and the importer
was built to read that source. Measuring a library on the
shelf you built the cart for is a measurement. It is not a
test of whether the cart works on another warehouse.

It is not a person sitting down at a prompt. We still cannot
type a goal and watch the system ask or refuse. Version 0.8
said the system could be driven. What you can run today is a
boot list that exits, and a recorded session that replays
itself. That gap is named, not smoothed over. It is not this
finding.

It is not a claim that passing tests are proofs. We imported
more algorithms — factorial, double factorial, raising to a
power — with real test volume against the standard library.
A passing test is still a citation of a finite check. The
nodes stay formal.

## What we now owe

The sign flip is the accident nobody wrote down as the thing
to find. At the sizes we used to have, the real library loses
to a shuffle. Compounding is a large-pile fact. That accident
chose the next question, and the question was
[written down](../DESIGN-heldout-recovery.md) *before* this
post, so the post could not choose it after. That document is
dated and in the repository; you do not have to take our word
for the order.

Does the same shape — worse than chance at thirty-two, better
later — appear on a source the importer was not fitted to,
against a baseline that cannot see who owns what?

One holdout is not enough. A single small set of about one
hundred sixty competition problems sits exactly where *this*
library was still below the shuffle. Stopping there would
repeat last cycle’s mistake: publishing a size as a source.
So there are two.

The small test is those one hundred sixty problems: a
different flavour of formal math, at the size where a real
curve can look like chance. The scale test is a seeded sample
of about two thousand statements from a much larger formal
corpus, large enough for the sign to have flipped here if it
is going to.

Three answers are all publishable.

The shape recurs, and a name-only baseline cannot fake it.
Then something about the architecture, not about this one
shelf of inequalities, is doing the work.

The shape recurs, and the name-only baseline matches it.
Then “who owns this part” is not doing what we attributed to
it. Sharing dressed up as ownership, one source later.

The shape does not recur. This shelf compounded. The
architecture did not. Importing still buys coverage. It does
not buy a transferable claim that a library explains itself.
That is the more interesting negative, and it is the one a
later chapter will have to live with if the holdouts give it
to us.

The small model’s job is still not to contain the world. Its
job is to navigate a world whose relationships remain visible.
This cycle made one of those relationships measurable, and
discovered that it changes sign. The next cycle has to ask
whether the sign change travels, or whether we measured a
bookshelf.
