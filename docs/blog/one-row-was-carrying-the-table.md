# One row was carrying the table

The last chapter ended with a promise and a suspension. This project's
matcher — the part that notices two statements from different sciences
wearing the same equation — had put the circumference of a circle beside
Newton's second law: one product of two factors equalling a third, in both.
That kind of match is the project's most attractive claim, and it had never
been tested against a prediction that could go either way. So we suspended
the count of such matches from our own release notes and promised a check
that can only say *no*: read what the symbols in the aligned slots actually
denote, and certify, where possible, that they cannot be the same kind of
quantity. It would have two verdicts, *conflicting* and *unjudged*, and
deliberately no way to say *confirmed*.

This cycle we ran it once, in the registered order, and the readout is in
two parts. The first part is the one we promised. The second is the one
that matters.

## The readout

The inventory came first, because a convenient denominator is how the
previous cycle got its answer wrong: twenty-six hand-authored cross-field
groups, seventy-seven aligned slots, committed before any tag existed.
Then the cheapest possible challenger, run before anything else was
allowed to fire: if lower-casing the symbol names reproduces the kind
labels, the whole apparatus is a rename detector. It does not — names
agree with kinds on 0.40 of the fully-tagged slots against a 0.80
tripwire, because a cross-field slot holds differently-named symbols
whether or not they denote the same thing.

Twenty-two of the seventy-seven slots came back *conflicting*, inside the
band registered in advance. And the match we put in print last chapter
read out the way the print said it would: circle circumference against
Newton's second law is **conflicting** — a length cannot be a force, no
matter how well the shapes align. Just as important is a pair that did
*not* fire: Boolean algebra and set algebra share their shape because they
are the same algebra, we said so before running anything, and the check
returned *unjudged* on every logic/set group. An instrument that flagged
those would be a liar in the direction it is supposed to be trusted.

## The part that matters

The third registered control never ran, and the defect is ours. To keep
the incompatibility table reviewable, it was authored only over kind pairs
that actually co-occur under the authored tags. That decision quietly
destroyed the control: permuting the tags produces pairs the table has no
opinion about, so the permuted baseline under-fires for reasons that have
nothing to do with whether the tags carry information. The comparison is
recorded as neither passing nor voiding, and the claim the control was
meant to establish stays unestablished.

So we asked the question a blunter way: vary the table and watch the
count. With no incompatibilities declared, 0 of 77 slots conflict. With
the authored table, 22. With every co-occurring pair declared
incompatible, 42. Then remove the table's six exemptions one at a time.
Five of them move the count by two at most.

The sixth — the row that says *a proposition and a set may be the same
thing* — moves it from 22 to 38.

One judgement was carrying the table. Declaring Boolean and set algebra
to be one algebra suppresses sixteen slots; everything else reduces to a
single blunt rule — quantities from different fields are different
quantities unless specifically excused. The check is not thirty-eight rows
of subtle dimensional reasoning. It is one very good textbook fact sitting
on a strong default. That is less flattering than a passing control, and
more useful: the instrument's trustworthiness now rests on one small,
checkable claim instead of on an artifact's bulk. The suspension on the
match count stays in force, extended in writing, because eight of
twenty-six groups contain a slot whose quantities cannot be the same —
which is the doubt the suspension was raised about, not an answer to it.

## The other kind of no

The cycle's second instrument answers a different question with the same
currency. Suppose a small, exactly-specified world — here, a story world
whose verifier enforces setup-before-payoff, and a diagram world whose six
committed mutations exist to be caught. Ask: *can this world reach this
exact state?* A search that finds nothing proves nothing; "no path found"
and "gave up" are indistinguishable.

So this cycle compiled the whole space first. Every state the story world
can reach within five actions — all seventy-five of them, every accepted
edge, every one of the 990 refusals, sealed under a digest — built by one
program and re-derived by an independently written checker that agreed
byte-for-byte on the first run. Twelve classes of deliberate corruption,
ninety applicable mutations, ninety caught. Now a query is a lookup
against a sealed object: one committed endpoint returns `REACHABLE` with a
five-action route that is replayed through the world's own verifier before
being printed. Change one word of that endpoint — an obstacle the world
never registered — and the answer is `NOT_REACHABLE_WITHIN_HORIZON`,
with the bound stated in the same sentence. The negative has a receipt.

The part nobody asked for: the design demanded at least four cases where
two different routes converge on the same state, as proof the enumeration
exercises composition. It found twelve, and decoding them exposed two
properties of the story world's committed code that no test had ever
stated — two of its transitions never read their `desire` argument, and
re-planting an already-planted element is silently accepted. The committed
demonstration route shows it live: the character is introduced wanting to
sing the sunrise awake, then plants two objects while ostensibly wanting
to out-crow a rooster, and the world accepts the arc. Exhaustive
enumeration read the code more thoroughly than its authors did.

## The honest boundary

Both worlds are small — horizons five and one — and nothing claims the
method scales past its frozen ceilings; a query answers reachability
within a bound, never possibility in general. The veto's information
claim is unestablished until a control exists that its own authoring
cannot starve. And the resolver that answers questions in the live prompt
is the same one that shipped three releases ago; this cycle improved the
instruments, not the system they measure.

## What a retraction costs

Here is the thread that ties the cycle together and hands it to the next
one. While building receipts for *no path* and *no match*, we went to
check a standing note that two of the project's published ledgers were
quietly stale on the main branch — and found the note itself had gone
stale. One drift was real but had been silently healed by a routine
refresh four releases ago, and nobody ever worked out which published
claims had consumed the stale numbers in between. The other "drift" was a
deliberate decision, recorded in prose that no artifact links to. The
repository has no receipt for the operation it performs on its own
beliefs: it has retracted results twice in its history, and both times
the blast radius was worked out by hand, by the author, after the fact —
and now even its claims about its own staleness were drifting unwatched.
Pulling that thread found one more: the front page had been advertising a
compression number measured on a 508-statement corpus for four releases
after the corpus grew to 12,777 and the true figure nearly tripled. The
drift was in our favour and nothing noticed, which is exactly as bad as
the other direction.

The next design was chosen before this post was written, by a process
built to resist our own momentum: three outside contexts, each isolated
from the repository and from each other, proposed fifteen directions
across three rounds of narrowing, with later series forbidden the earlier
series' ground. The direction that survived grounding — against the
repository's actual retraction record, which contradicted part of the
winning proposal and reshaped its gate — is the [retraction
closure](../DESIGN-retraction-closure.md): a provenance graph the ledger
writers emit themselves, and a certificate that names, for one falsified
node, every published claim downstream of it in the recorded lineage. The
gate is preregistered and can kill the capability: the computed radius of
each adjudicated drift must contain every claim a hand audit finds
first, and if shuffled edges explain the drifts as well as the real
ones, the graph carries no information and the cycle says so. The two
historical retractions are explicitly out of reach — they were shifts of
interpretation, not data lineage, and the design's first honesty is
refusing to pretend a graph prices those.

A system that keeps exact things outside the weights has to know what it
costs to unsay one of them. Next release, unsaying gets a receipt too.
