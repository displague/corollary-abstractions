# The bag still wins

*We built the verifier we had been promising for two releases, bridged real
theorems into the corpus, and grew it from 221 nodes to 508. Then the dumbest
baseline in the project beat us on count again — and the way it beat us is the
most useful thing v0.10 produced.*

For a year the discipline of this project has been the same: nothing counts
until it beats a capability-blind baseline. Not "beats a weaker model" —
beats a method that has no idea what it is doing. The operator bag is our
favourite of these. It takes two statements, throws away all structure, keeps
a multiset of the operators that appear, and calls them a pair if the bags
look alike. It knows nothing about binding, precedence, carriers, or what a
theorem *says*. It is a straw man we cannot knock down.

On 221 hand-authored nodes it formed more twin pairs than our structural
matcher, and we wrote that down as an embarrassment to be resolved by scale.
The story we told ourselves was reasonable: of course a bag looks good on a
small curated corpus where everything shares an operator vocabulary; give it
real ingested mathematics and it will drown in noise while the matcher keeps
finding real structure.

So v0.10 gave it real ingested mathematics. Here is what came back.

| | pairs formed | precision |
|---|---|---|
| operator bag (blind) | **7,622** | 2.03% → **1.26%** |
| structural matcher | **96** | **1.0** |

The bag still wins on count. It wins by a factor of eighty. And its precision
fell by a third while it did — it is not finding more structure, it is
guessing more often and being wrong more often. The matcher formed ninety-six
pairs and was right about every one.

We could report that as a win. "Precision 1.0 versus 1.26%" is a sentence any
project would enjoy writing. But the honest framing is the uncomfortable one:
**scale did not resolve the disagreement, it separated the two axes.** The bag
owns volume. We own correctness. Nobody has yet shown that our ninety-six
pairs are the *right* ninety-six — precision at 1.0 is compatible with
finding a small, easy, correct subset and missing everything hard. We do not
report recall, because we do not have it. The next release has to define one
number both methods are scored on before either of us gets to claim victory
again.

## The bridge we actually built

The rest of v0.10 is the infrastructure that made that comparison possible at
all, and it is not nothing.

We built an **external verifier** the repo can invoke: a real one, calling a
real Lean toolchain's binary directly by path — never through a proxy that
might quietly download something — and requiring exit 0, no warnings, and an
axiom footprint inside a declared allowed set. It emits verdicts as committed
objects, not booleans, over `pass`, `fail`, and `refused`.

The most important line in that design is not about what it certifies. It is
this: **a passing check certifies what it checks, not correctness in
general.** Every verdict repeats it. And the corpus enforces it — one
ingested statement carries a full machine-checked bridge, and its neighbour
enters as `formal` with *no* bridge at all, saying in its own record that its
proof needs Mathlib and Mathlib is outside our hermetic budget. We shipped the
refusal next to the success on purpose.

We also shipped a **failure** as a first-class artifact. There is a statement
in the ledger, `lean_workbook_10411`, that is true, ground, and perfectly
ordinary — and the verifier cannot prove it, because its exponent exceeds
Lean's default evaluation threshold and `decide` gives up, closing the proof
with `sorryAx`. The compiler exits 0. The warning is easy to miss. Only the
axiom audit catches it. We committed that FAIL verdict rather than deleting
the statement or raising the threshold until it passed, because a verifier
that tunes its own options until the answer is yes is not an authority. A
ledger that contains nothing but passes is not a ledger.

## The thing nobody designed for

Then the corpus did something we had not asked it to.

A recorded session — the harness driven end to end for the first time, four
legs, everything emitted from the components' own records — authored one new
ingested statement: `2^30 mod 1000 = 824`. The registered prediction said the
groundedness aggregates would drift downward by dilution, the way they had
four times before when we added nodes that own nothing.

They went *up*. The new statement shares the subterm `2^30` with the only
other ingested statement in the corpus, `13 ∣ 2^30 + 3^60`, and the
decomposition ledger immediately recorded each as grounding the other. Two
constituents. Nobody wrote a rule for it; the ledger simply noticed, because
noticing is what it is for.

Then item 4 authored 251 more ingested identities and the same thing happened
at scale: **614 constituents grounded inside the new corpus**, and `2^30`
picked up a third owner. The ingested layer had started referring to itself.

This is the most interesting result in the release and we are deliberately
refusing to call it a finding. Two observations at two scales is not a curve,
and we have not run the null — ground arithmetic shares small integers for
boring reasons, and a rising line means nothing until you know what chance
produces. The design that will measure it, including its null model and four
predictions, was written *before* the 251-node corpus existed, precisely so
we could not pick the null after seeing the data. If the curve comes back
flat, ingestion buys coverage and not structure, and that changes what this
corpus is for. We would rather find that out than assume the flattering
answer.

## What we retired

One small thing, which is really a lesson about guards.

We had a pinned check asserting that two grounding channels' external-owner
*rates* stay within twelve points of each other. It moved in four
consecutive releases — 0.164, 0.156, 0.159, and then 0.490. Each time we
re-pinned it at the measured value with an argument, which is defensible
once and starts to look like a ratchet at three.

The fourth jump gave it away. The gap is a ratio, and ingestion changed its
denominator: 251 statements that ground each other flooded one channel with
internal owners, dropping its external *rate* while its external *count*
grew. Nothing about the behaviour we were guarding had changed. The pin had
started measuring the corpus's composition and calling it a property of the
algorithm — and it would have kept moving every single time ingestion
succeeded.

So we retired it, with the reasoning written where the assertion used to be,
and kept the count-based guard beside it, which has never weakened and got
stronger. **A guard that fails whenever the project succeeds is not
protecting anything.** That rule is now in our release process, alongside a
second one this cycle earned the hard way: every deferred lane must name the
headline item that depends on it, or be parked in writing. We learned that
because a lane we carried for two cycles as a minor entry in a list turned
out to be the thing blocking our headline feature — discovered not by reading
the roadmap but by running the gate and watching it refuse.

## Where this leaves us

508 nodes across 27 corpora. A verifier that works and says exactly what it
is worth. Twenty-one machine-checked links, three of them citing tests rather
than proofs and labelled as such. A session recorded end to end, including
the parts where it was refused. 1,084 tests.

And a blind baseline that still wins on count, a self-grounding effect we
refuse to call a curve until its null is run, and one slice that merged
without the adversarial review the other six got — which is in the release
notes, because the alternative is a release that reads better than it was.

Next release has three jobs: measure the self-grounding against its null,
give the baseline comparison a single number both sides are scored on, and
report our recall. If the bag beats us again on a fair metric, we will write
that down too.
