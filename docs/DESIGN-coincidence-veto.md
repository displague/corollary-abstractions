# The veto on a match the corpus cannot support

Status: **design only.  No tag, table, flag, or result exists.**  Scoped after
v0.14 and behind
[compile the space before asking the question](DESIGN-compile-before-query.md),
which remains the chosen architecture.  This is an instrument, not a
replacement for it.

## 1. The boundary being moved

The twin matcher finds statements from different fields that share an exact
structural skeleton, and 975 typed twin groups are committed today.  Thirty-four
of those span more than one top-level namespace and twenty-six of those are
entirely hand-authored.  The project reports that cross-field count as a
result.

Nothing in the repository can say whether any particular one of those matches
is real.  A shared skeleton means two statements have the same shape.  It does
not mean the things sitting in the aligned slots are the same kind of thing,
and where they are not, the match is a shape collision rather than a transfer
between fields.  The matcher cannot tell the difference, because the fact that
separates them is not in either statement: it is a fact *between* them, about
what their two glossaries name.

The capability this unlocks is small and specific.  A person reading a
cross-field match can be told, mechanically, that this particular one cannot
be a transfer — with the reason printed, in terms of the two entries' own
committed symbol names.  Not that the others are real.  Only that this one
is not.

## 2. Why this direction, and why not the other two

Three project-blind inquiries were run in isolation and pressure-tested twice
each.  All three arrived, uninstructed, at the same shape: a negative that is
**computed rather than measured**, spends no held-out evidence, and converts a
belief about the collection into something the build checks.  That is the shape
of the defect v0.14 died of, where a benchmark measured an author's belief
about ambiguity and the belief was wrong.

**The first direction was refused, and its refusal is kept.**  It proposed
certifying which statements no query can ever single out, by feature
subsumption under the frozen scoring rule.  Its own construction gate required
at least three victims among the hand-authored statements.  The census returns
zero of 262, because those statements carry a median of 43 discriminating
features and a minimum of nine, and strict subsumption cannot happen at that
density.  It cost a minute and no evidence.  Its finding is recorded in
DISCOVERIES and stands on its own: whatever makes clarification hard here, it
is not that statements are invisible.

**The second direction is parked, with a named prerequisite.**  It observed
that the committed digests certify the *domain* — these sources produced this
artifact, byte for byte — while nothing certifies the *range*, that the
function from question to outcome is unchanged.  Adding statements passes every
regeneration check truthfully while silently moving an answer nobody was
looking at.  That distinction is imported here as a lesson and is not built:
its own author put the cheap control, predicting churn from the source diff,
at roughly even money to defeat it, and it needs thirty builds or sixty days
before it can say anything.  It parks behind evidence that the range actually
moves.

**This direction survived because it is the only one that can be defeated by
its own subject matter.**  It does not extend reach, so the standing prior
against added reading power does not apply.  It has no positive vocabulary, so
it cannot manufacture a confident wrong answer.  And it is aimed at an artifact
this project already trusts and already publishes, which is where an
unadjudicated belief is most expensive.

### What the matcher already flags, and why this is not that

The report already carries two collision signals, and neither answers this
question.  `skeletons_with_split_archetypes` flags a shared skeleton whose
members carry different hand-assigned concept labels, and
`slot_vs_call_head_collisions` flags a name used both as a slot and as a call
head.  Label disagreement is not coincidence: `archetype_label_drift` shows
`affine_operator` spanning algebraic topology, calculus, economics and
statistics, which is the success case the project is built to find, not a
collision.

Checked rather than assumed: **none of the twenty-six are flagged by
`skeletons_with_split_archetypes`**, and twenty-three of them carry a single
archetype.  The existing machinery sees all of them as coherent.  Whatever
this instrument finds, it is not something already reported.

### The demonstration

Group `scaled_linear` matches `geometry.circle_formulas.circle_circumference`
with `physics.mechanics.newton_second_law` — the same skeleton, one product of
two factors equalling a third.  A person is shown the two statements and asked
whether a result about circumference transfers to force.  The instrument's
first question is whether the aligned slots hold quantities of compatible
kind; if length, dimensionless ratio and force cannot be reconciled by any row
of the table, the match is certified as shape and the certificate prints the
two symbol names that decide it.

This example is chosen as the demonstration because it is legible without
mathematics, not because its outcome is known.  It has not been tagged and no
flag exists.

## 3. The object

**A conflict flag, per cross-field twin group, per aligned slot.**  Exactly two
values:

- `conflicting` — the two aligned symbols carry kinds that a committed
  incompatibility row says cannot denote the same quantity;
- `unjudged` — anything else.

There is deliberately no `confirmed`.  The object has no vocabulary for
sameness and cannot be extended to one without a new design.  There is no
transitive closure, no graph, and no consequence from one flagged group to
any other.

Two committed inputs it needs:

- a **kind tag** per symbol occurrence in an aligned slot, drawn from a closed
  menu authored once — length, duration, rate-per-time, dimensionless ratio,
  count, probability, energy, concentration, and so on;
- an **incompatibility table**, a committed list of kind pairs that cannot be
  the same quantity, each row carrying its reason in words.

Both are authored by hand, and both live in their own committed files keyed
by statement id and symbol name.  Neither edits a node: corpora are
regenerated from authored generator scripts and are never touched in place,
so a tag that changed a node would break regeneration and would also make the
tag a corpus claim rather than an annotation about one.  Everything else is
computed.

## 4. Trusted and untrusted

Trusted: **a conflict certificate** — group id, slot index, the two statement
ids, the two symbol names as committed, their two kind tags, and the
incompatibility row that fired.  It is checkable by reading the two entries.

Untrusted, and unrepresented in the artifact:

- any assertion that two entries *are* the same statement;
- `unjudged`, which means nothing and is not a clean bill of health;
- any score, ranking, or count presented as a quality of the matcher;
- the kind tags themselves, which are one person's coarse labels and not a
  type system.

The asymmetry is the whole design.  A wrong tag damages only the groups
containing that symbol, and damages them toward a **false negative** — a real
cross-field transfer wrongly suppressed, which costs coverage.  It cannot
produce a confident wrong claim, because the object never speaks positively.

## 5. The smallest slice

The twenty-six cross-field twin groups whose members are all hand-authored.
The population predicate is committed and reproducible, not curated: a typed
twin group qualifies when its members span more than one top-level id
namespace and no member belongs to an ingested corpus.  Slot alignment is
read from the group's committed skeleton, never chosen by the person doing
the tagging.  That is a census of the eligible population, not a sample, so
there is no sampling argument and no held-out set is spent.  The ingested source is
excluded: formulaic generation makes shape collision cheap there, and its
internal matches are not what the published count is read as claiming.

## 6. Construction prerequisite, committed before any flag exists

The number of aligned slots is not known and must not be guessed, so no rate
is frozen here.  Before the comparison is implemented, one commit must land
containing:

- the closed kind menu;
- the incompatibility table with a reason per row;
- the complete slot inventory for the twenty-six groups — every aligned slot,
  with the symbol each member places in it, and a kind tag or an explicit
  `kind-unknown`;
- a two-sided prediction of the conflict count, registered against the slot
  denominator that inventory establishes.

Tags are authored per symbol without reference to which groups they would
flip.  A tag added or changed after any flag is visible invalidates the run.
This is the same freeze-first ordering v0.14 used, and the reason is the same:
the author's belief is exactly what is being tested.

## 7. Gates

**Construction gate.** The slot inventory regenerates byte-for-byte from
committed sources; every aligned slot is tagged or explicitly kind-unknown;
the incompatibility table is symmetric and contains no row pairing a kind with
itself.  Any failure refuses the run rather than reporting a result.

**Blind control, run first.** For each aligned slot, flag it conflicting when
the two symbol names differ as case-folded strings.  This ignores kinds
entirely and costs three lines.  If it agrees with the kind-based flags on
80% or more of tagged slots, the kind machinery bought nothing and the
direction is dropped.

**Result gate.** The registered two-sided prediction, adjudicated once.  A
conflict count at the floor says the ledger was clean and this instrument was
unnecessary; that publishes.  A count at the ceiling says the tags or the table
are wrong rather than the ledger, and that publishes too.  Neither outcome is a
failure of the run; only an unadjudicated one is.

## 8. Vacuity and negative controls

- The blind control above, run before the real one.
- A corruption check, whose direction is the point.  Authored tags encode
  which quantities are genuinely compatible, so they must flag **fewer**
  conflicts than tags permuted at random across the same symbols.  If a random
  assignment flags no more than the authored one, the tags carry no
  information and the result is void.  The comparison is against the mean of
  several permutations, fixed in the preregistration.
- A no-op check: a group whose aligned slots are all kind-unknown must produce
  no flag of either kind, not a default.

## 9. Non-claims

- No claim that any unflagged match is real.
- No claim of improved accuracy on any query set; end-to-end retrieval is not
  touched and no spent question is re-used.
- No claim about the ingested source beyond excluding it.
- No controlled vocabulary, no quantity index, no new retrieval surface — those
  were proposed, pressure-tested, and withdrawn.
- No claim that this changes what a clarifying question does.

## 10. The habit being suspended

**The published cross-field match count stops being cited as a result.**

It is reported as an achievement and has never been adjudicated against a
two-sided prediction, and it is drawn from a matcher whose collisions are
cheapest exactly where the corpus is most formulaic.  That is the same shape as
the clarification benchmark that failed in v0.14 — a belief about the
collection sitting on the achievement side of the ledger instead of the test
side.

Scope: release notes and any evidence chain.  The number may still appear in
ANALYSIS with its denominator and this suspension named.  Duration: until the
result gate above reads out, or two release cycles, whichever comes first.  If
the count survives adjudication it returns with a stated denominator and an
adjudicated slice behind it; if it does not, that publishes as prominently as
the count ever was.

## 11. Where status lands

ROADMAP for the cycle that schedules it, ANALYSIS for the adjudicated numbers
and the blind control, DISCOVERIES for what the conflict rate says about
structural matching across fields, and BACKLOG for the parked range-certifying
direction and its named prerequisite.
