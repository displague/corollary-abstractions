# When the honest baseline wins

*How a proof-search curve, a restart-proof conversation, a false claim caught in
the act, and a geometry oracle turned single demonstrations into families with
baselines — and what it means when the cheap trick keeps winning*

Every previous release of this project could show you a capability once. One
live Lean theorem the system proved. One conversation it held. One analogy it
completed. A single demonstration is enough to say a thing is *possible*. It is
not enough to say the thing is *load-bearing* — that the learned model, the
maintained state, the verifier, are doing work a simpler mechanism could not do
just as well.

v0.7 is about the gap between those two claims. The plan was written in one
line: *breadth before benchmarks*. Take every capability we had shown once, and
turn it into a family of tasks with a declared, capability-blind baseline — a
cheap rule, a blind order, a structure-only check that could plausibly solve the
task without any of the machinery we are proud of. Then let that baseline try.

In nearly every lane, the baseline won, or the honest ceiling came in far below
the headline. This post is about why that is the good outcome, and about the
four lanes where the story is sharpest.

## The golden chicken learns to survive

We keep returning to a deliberately small example: a story about a golden
chicken. One person asks that their version lay silver eggs; another asks for
blue; the first changes their mind to copper. A large language model handles
this fluidly. Our system handles it *explicitly* — each preference is a signed,
owner-private binding over one shared public story, and changing your mind is an
authenticated supersession, not an overwrite.

In v0.6 that whole structure lived in a single process. Close it and the
signatures, the revocation ledger, the private keys were gone. The honest limit
we wrote down was blunt: the conversation could not survive its own restart.

In v0.7 it can. Two owners serialize their sessions to ordinary public JSON, the
process ends, a fresh process reloads a runtime-owned root key, re-derives each
session's signing key, and both owners keep revising. The public story comes
back byte-for-byte identical and still unasserted — the system has not decided
the chicken *is* golden, only that two people are telling compatible stories
about it.

The interesting part is what it refuses. A binding that was superseded before
the save is refused after the restart. A binding whose signature was forged is
refused. And — the case we flagged in advance as most likely to defeat us — a
genuinely signed *older* snapshot, replayed to roll the conversation back to a
state the owner had already moved past, is refused too. That last one cannot be
caught by any signature: the snapshot is authentic. It is caught by a private,
monotonic counter that the public file cannot lower. We registered that
prediction before writing the code, named it as the one most likely to miss, and
it held.

None of this makes the conversation fluent. The prose is still deliberately
flat. What it makes the conversation is *durable and correctable* — and those,
not fluency, are the properties we can actually verify.

## One theorem becomes a curve, and the learned ranker still loses

Last cycle we put a tiny neural network — 27,688 parameters — in charge of
*ordering* the tactics a live Lean process would try, and discovered that a
state-blind frequency ordering solved the same theorem in one fewer proposal.
That was one theorem. A skeptic could fairly say: of course a blind rule ties on
a single easy target.

So v0.7 built the family. Twenty-four held-out theorems across four proof
shapes, 144 live searches against a real Lean kernel with no replay anywhere,
solved-rate curves measured at five budgets. Four ranking arms — arbitrary,
frequency, a syntax-aware blind order, and the learned one — each handed the
*identical* set of candidate tactics, so that any difference between them is a
difference in *ordering* and nothing else.

The learned ranker lost again. At the intermediate budget the syntax-aware blind
order solved 21 of 24; the learned seeds solved 18, 21, and 19. We also checked
whether the learned arms at least avoided the branches that had already proven
dead across tasks — and they re-proposed known-dead moves at essentially the
same rate as the blind order. No avoidance. Every arm reaches every theorem at
the largest budget; the learned one simply gets there no more efficiently than a
rule you could write on an index card.

This is worth being clear about, because it would be easy to present as a
disappointment. It is not. The roadmap declared *in advance* that a learned loss
was a valid result. The point of the lane was never to crown the network; it was
to find out whether the network's residual beat the strongest cheap operation
that could have stayed outside the weights. The answer is no, over a family now,
not an anecdote — and knowing that is the result. The same policy protocol runs
in a second, story-shaped domain too, which tells us the *protocol* generalizes
even though the *controller* has no lever there to pull.

## A proof of a true theorem that staged a false claim

The lane I find most instructive is the one where the machinery nearly fooled
itself.

Part of v0.7 is a gate we call PROVEN-gated WRITE. The idea: before the system
is ever allowed to stage a change to its own durable knowledge, a machine-checked
Lean proof must *correspond* to the statement citing it — not merely exist, not
merely be unmodified, but actually be a proof of the thing claimed. We
regenerate a formal skeleton from the theorem's opening goal, translate it into
the corpus's own template grammar, and check it matches one of the forms the
citing statement declares.

An independent review of our own implementation found a hole, and it is a small,
sharp one. Our matcher, when it compares two statements, folds every
constant-like symbol into a single class. To the comparison, `TRUE` and `FALSE`
were the same symbol. So a genuine Lean proof of `P ∧ False ↔ False` — a true
theorem — was judged to *correspond* to the claim `P and True = True`, which is
false. The gate did not have a bug in its logic; the *evidence* it was consuming
was one notch weaker than the gate's own standard, and that gap was enough to
stage a false claim through all fourteen checks.

The fix was to stop keying constants by how they are spelled and start keying
them by which *pole* of the logical lattice they occupy — top versus bottom —
so `TRUE` and `FALSE` can never again collapse into one symbol, while two
different *spellings* of "top" still unify correctly. What makes this a good
story rather than an embarrassing one is that it is exactly the failure mode the
project's most reliable rule predicts: the boundary the author believes is
already covered is the one an independent reviewer should probe. On eight
consecutive trust-boundary slices this cycle, independent review found a
load-bearing defect the author's own review had missed. That is not eight
failures of care. It is eight demonstrations that adversarial review is not
optional decoration.

The honest boundary remains drawn in bright paint: structural correspondence is
not truth, and not ownership. It says the theorem's goal is one of the forms the
statement declares — a floor above "the bytes are unchanged," not a ceiling that
reaches "the statement is true."

## The analogy lane we rebuilt until the cheap rule died

In v0.6 we built our first corpus-grounded analogy task and then, in the same
release, showed that a blind rule — "move the new number into the last slot" —
solved all of it. A grounded task that a one-line heuristic solves perfectly is
not yet a test of anything.

So we rebuilt it until that rule scored zero. The new split has 398 distinct
targets across eleven structural families, cut into holdouts on three
independent keys, and the old last-slot rule now scores 0.000, 0.011, 0.048. By
the letter of the acceptance criterion, we could have stopped there and claimed a
non-trivial ceiling.

Instead the same adversarial habit turned on our own split, and found that our
"families" were *typed* skeletons — which meant a nearest-template rule could
still score perfectly wherever a held-out example's untyped shape was quietly
still present in training. The headline ceiling of 0.40 decomposes, almost
exactly, into "the fraction we genuinely held out" times a near-perfect score on
the rest. The strict ceiling is closer to 0.10–0.14. We wrote that down, in the
release notes, as a hole in our own measurement — and we did *not* quietly
re-roll the split to look better, because re-rolling a split against a ceiling
you have already measured is how a benchmark launders its own result. The
untyped-shape holdout the split should have been is left open, on the record, for
next cycle.

There is a second finding under it that matters more than the number: adding
exactly two declarations from the corpus takes a plain symbolic solver to a
perfect score on this task. Which means the lane, honestly described, measures
*pointing at the right structure*, not *reasoning*. No model score from it may be
sold as reasoning, and we said so before training any model at all — indeed, no
model has been trained here yet. The bar comes first.

## A ruler before a guess

The last lane inverts the usual order of machine-learning work. Before building
any visual model, we built the thing that could tell whether a visual model was
right: a deterministic renderer of right triangles, a generator of controlled
near-misses, and an exact verifier of incidence, length, and right angles.

The numbers are the kind you want from a ruler and not from a model: 240 valid
figures and 1,440 controlled invalids; the verifier accepts every valid and
rejects every invalid, each at exactly the one geometric check registered as its
gate; disable any single check and precisely that class of invalid slips through
while the others stay caught; 5,040 render-parse-verify round trips reproduce
byte-for-byte. No learned weights exist in this layer at all, and no capability-
blind surface baseline clears 0.742. Only now, with ground truth that cannot
itself be fooled, is it honest to train a model against it — which is next
cycle's work, not this one's.

## The through-line

Read together, these lanes describe a single discipline. In each one we built,
deliberately and in advance, the cheapest thing that could beat the machinery we
were testing — a blind tactic order, a last-slot rule, a structure-only check, a
surface classifier — and then reported what happened without adjusting the
target after seeing the result. The learned ranker lost. The analogy ceiling
collapsed under its own typing. A true proof was caught staging a false claim.
And a conversation that used to die on restart now refuses the forgeries and
rollbacks it should refuse.

None of this is a benchmark against a large language model, and the release notes
say so plainly: nothing here stands against general LLM fluency, and the
under-64-MB target is a constraint we chose, not a comparison we won. We have not
even earned the right to run such a comparison yet — the roadmap forbids it until
the system accepts genuinely open requests, which is the headline of the next
cycle.

What we have earned is narrower and, we think, more durable: a set of results
that survive their own strongest baselines, or that fail honestly and say where.
A capability shown once is a promise. A capability that beats the cheapest thing
that could replace it — or that loses to it, on the record, in advance — is a
measurement. v0.7 traded a handful of promises for measurements. When the honest
baseline wins, that is the measurement working.

*The full evidence, every registered prediction and its adjudication, and the
corrections we attached rather than edited away are in the release notes and in
`DISCOVERIES.md`. The next cycle's plan is in `ROADMAP-v0.8.md`: open-language
requests, the analogy model against that strict ceiling, and the proof-search
curve given the memory to finally beat its blind baseline — or lose to it
again.*
