# The curve changed sign

*We finally ran the self-grounding measurement we had been talking
around for two releases. At thirty-two ingested statements we were
worse than chance. That is the finding. The part where we later
beat the null is what makes it a curve instead of a retraction.*

v0.10 ended with an anecdote we refused to promote. Two ingested
statements shared `2^30` and the ledger called each the other's
owner. Then 251 ground identities produced 614 `same_corpus`
constituents. We wrote down that ingestion *looked* like it
compounds, and we also wrote down that we had no null and no
curve. The next cycle's job was to stop talking.

So we authored the rest of the unique-covered Lean-workbook
statements the matcher can actually parse — 12,514 of them, 123
refused, the refusals counted — and we ran the measurement the
design had frozen *before* that corpus existed. Route 1: a
subterm is self-grounded when its most-independent owner is
another ingested node. Not when two statements happen to contain
it. Sharing is symmetric. Grounding is not.

Here is the curve.

| ingested nodes | real − null |
|---:|---:|
| 8 | **−0.041** |
| 32 | **−0.024** |
| 128 | +0.046 |
| 512 | +0.042 |
| 12,515 | +0.063 |

At the sizes we actually had last time, the real layer sits
*below* a distribution-matched synthetic null. Shared squares and
small numerals do not beat random trees drawn from the same
operators and the same digit frequencies. If we had stopped at
hundreds — and we almost did; that was v0.10's honest limit — the
publishable sentence would have been: ingestion buys coverage, not
structure. We would have been obliged to write it.

The sign flips by one hundred and twenty-eight statements. After
that the gap is positive and, at full scale, forty-five times the
null's seed-to-seed spread. 98,499 of 208,404 considered subterms
have an ingested most-independent owner. Cross-layer grounding
barely moves (0.423 → 0.397): the ingested layer did not buy this
by shedding the hand-authored one.

The prediction we thought would fail, failed in the other
direction. We asked whether the effect survived deleting the
single most common subterm, because a curve about `x²` is a fact
about `x²`. Deleting `^(?0:V, 2)` — 6,870 host statements —
*raises* the gap from 0.063 to 0.127. The fashionable square
belongs to the curated algebra. It was diluting the rate.

And the measurement we refused to take as the headline is, at this
scale, a vacuous 1.0. If you only ask whether a grounded
constituent's skeleton also occurs in some other ingested
statement, the answer is 181,270 / 181,276. Sharing is nearly
universal on a layer of olympiad inequalities. Owner-attributed
self-grounding of those same constituents is 0.543. Reporting the
first number as the second is how a project talks itself into
believing a curve.

None of this is a proof, a usefulness claim, or a certificate.
The 12,514 nodes are still formal-without-bridge. A subterm having
an owner inside the corpus is a structural fact about the graph.

The other headline is the one we already knew and finally gave a
single number. The operator bag — same set of `{+,-,*,/,^=}`, no
structure — still forms more pairs than the matcher. On 12,771
nodes it forms 9,041,744 of them. The matcher forms 1,991. Bag
precision against typed twins is **0.0220%**. That is the figure
of merit we registered before the re-run, because comparing raw
counts lets the bag win by definition and comparing precision
alone lets us win by changing the subject. A size-matched draw
from the bag recovers one typed twin in 1,991. The matcher misses
one pair, and we know which: the emitter prints subtraction as
`+ -(...)` and the curated double-angle cosine writes infix `-`.
Same skeleton, different glyphs. Precision 1.0 was always
compatible with finding a small correct subset. At least now the
denominator is in the open, and the one exception has a name.

What v0.11 does *not* do is pretend the Lean-workbook curve is a
benchmark. It is a measurement on the source the emitter was
fitted to. The next question is already written, and it was
written before this post: does the sign-flip-then-compounding
shape survive a source we did not fit, against a baseline that
cannot see owner ids? MiniF2F at 163 covered statements is the
small-N test — the size at which we now know a real curve can
look like chance. A seeded Goedel-Pset sample is the scale test.
If the shape dies, Lean-workbook compounded and the architecture
did not. That is the more interesting answer, and it is the one
we are obliged to prefer if the holdout gives it to us.

This post is the argument, not the inventory. After it was
drafted, a second programming wave put tests at volume without
calling them proofs, and a drift audit found the live prompt
v0.8 said was shipped still exits after a liveness list. Those
are in the [release notes](../RELEASE-v0.11.0.md). They are not
this finding.
