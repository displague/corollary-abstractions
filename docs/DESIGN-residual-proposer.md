# Design — the residual is a budgeted edit (steering for v0.12 / v0.13)

Written during v0.11, *after* the programming second wave and *before*
any v0.11 tag or v0.12 blog, so the leftover cannot be chosen to
flatter either post. This note does not ship a ranker. It freezes
what a later ranker is allowed to be.

The destination and the residual were produced by a three-cycle
antagonist dialectic (thesis → live-number grounding → refinement),
then closed. The registered predictions in §7 are floors for a
**future** v0.13 implementation; they are not a claim that a model
has been run. No deck cell has been scored as a training label.

This note does not reopen [DESIGN-heldout-recovery.md](DESIGN-heldout-recovery.md).
H1–H6 stay frozen. Lean-workbook is not held-out.

## 1. The claim

A million-weight model can do compositional work on this world only
if it proposes and the world verdicts. By **v0.14** the README may
say that only if a from-scratch ranker of the overnight class, on
the real programming ontology, beats a registered keyword policy at
a budget *k* under a goal the world already computes: a
`python-tests` PASS, typed-twin of the source, and not a typed-twin
of the name-foil. The leftover is not pointing, not ISG, not
specialize-replay. It is which authored edit to try next. If that
number does not exist, or exists only as a leak, the README says
the world computes structure and the tiny model has not been shown
to add any.

The last time this project put a million-weight model on a residual
(corpus analogy, 1.49M, 3 seeds) it scored 0.104 ± 0.012 against an
unseen-shape floor of 0.1069. Tactic ranking: 65 proposals against
a 64-proposal frequency order. Growing the world since then is not
the same as cashing that leftover.

## 2. What this is for (and is not)

**For:** deciding what v0.12's held-out curve is permission for, and
what v0.13 must accept or park. **Not for:** training a coder, an
AST-to-recurrence extractor, promoting `python-tests` to PROVEN, a
fifth TheAlgorithms file, or widening matcher heads.

v0.11, before the tag, may re-run the suite and cut the tag.
Nothing else. A residual design slipped into the v0.11 notes would
choose v0.13's question from the post. This file is the thing the
post is not allowed to choose after.

## 3. The residual, named as a task

**Budgeted recurrence-preserving edit.** The model is not asked
whether two templates twin, whether a test passes, or what the
analogy target is. Those are closed forms. It is asked which
already-authored edit to try next, under a budget smaller than the
deck.

- **Inputs.** A source programming node (template + pinned
  candidate path). A goal that is itself a predicate the world
  already computes: `python-tests` PASS **and** typed-twin of the
  source **and** not a typed-twin of the name-foil (Stein for
  Euclid; a PASS-not-twin cell is required before a family may be
  held out). A frozen deck of candidate edits, identified only by
  id. The model does not see verdicts, owner ids, or matcher
  partners.
- **Proposal.** An ordering of deck ids, scored at a registered
  budget *k*.
- **What the world answers.** The existing `python-tests` sandbox
  (`py_compile`, `mypy --strict`, pinned tests). The matcher on
  authored templates. A WRITE-shaped honesty tax if a wrapper
  declares a matcher delta: mismatch is REFUSED. `python-tests`
  stays a citation. Nothing here is PROVEN.
- **Beat the bag.** The token-name proposer already measured on
  this foil set (gcd 1/3, factorial 1/3, combined 0.4), rewritten
  as a policy: at the same *k* it tries deck items that share the
  source's algorithm token. Same three-part predicate. Registered
  before the ranker runs. A frequency-order control rides with it.
  Exhaustive matcher-plus-tests is the sighted ceiling and is not
  a model score.

The current world can score every cell of an **authored** deck. It
cannot score an open Python mutation as a twin. There is no
AST-to-recurrence closed form; the first wave declined to build
one. Open generation waits on that extractor, or it stays out.
v0.13 is authored-deck ranking or it is not this residual.

## 4. v0.12 is an environmental pretest

H1–H6 stay frozen. They decide the environment, not the leftover.

| outcome | effect on this residual |
|---|---|
| H1 fails | Park the groundedness gate. The ranker still stages. Lean-workbook ISG was never the leftover. |
| H3 fails | Keyword can steal owner-shaped gaps. Keyword-at-*k* on this deck becomes the only remaining place the claim can be staged. |
| H3 fires | Substrate, not a reason to skip the ranker. |
| H2, H4, H5, H6 | Do not change the staging. |
| Lean-workbook "held-out" | Forbidden. A 20% slice is a split, not a source holdout. |

If H1 fails, do not train on Lean-workbook-shaped inequalities and
call it the claim. If H3 fires, do not write the README as if the
tiny model did the work.

## 5. v0.13 acceptance, exact enough to fail

The deck is the four families that already exist: Euclid, factorial,
double-factorial, binary-exponentiation. No fifth file. No AST
extractor. Drop-abs and n-minus-2 stay committed FAILs cited by
nothing; they are not the eval set.

**Cells that must exist.** Each family that is allowed to be held
out must contain at least one cell that PASSes the source's tests
and does not typed-twin the source. Euclid already has that cell:
`programming.stein.binary`. The iterative sibling is not that
cell — house style authors it onto the source template, so picking
it is pointing at a closed form. A deck of recursive / iterative /
drop-abs is vacant: tests do all the work and the matcher is a
spectator. Name-foils that fail the source's tests (double-factorial
against `math.factorial`) do not make the matcher load-bearing. A
family that cannot host a PASS-not-twin cell without a new source
or an extractor is **ineligible** to be held out. If that leaves no
eligible holdout, the model arm parks in writing.

[DESIGN-emergent-programming.md](DESIGN-emergent-programming.md)
fires that parking for *emergence*: this design will not add a
second Stein-kind just to unpark a family holdout. Budgeted-edit
ranking remains a later *trained* experiment if a second
PASS-not-twin cell is later authored for that purpose. It is not
the emergence vehicle.

**Holdout.** Cut by family, not by row. Train is the other
recurrences. Ids, paths, and comments carry no gold tokens
(`iterative`, `recursive`, `stein`). A leak is a refuse.

**Vacuity, any one parks the ranker.**

- Keyword-at-*k* is 1.0 on the holdout.
- The protocol is *k* = |deck|.
- Tests-only ranking agrees with the full predicate on the holdout
  (matcher idle).
- No eligible family.

**"The ranker won" may not mean.** Beating keyword on PASS-only.
Beating keyword when the iterative sibling is visible as an input
id. A single-seed comparison. `--apply`. Predicting the matcher
delta.

## 6. v0.14 still exists

A ranker that beats keyword-at-*k* on a frozen four-family deck is
a policy over cells authors already scored. It is not yet the
claim. What remains: a proposer that submits an append, meets a
WRITE refusal, and recovers — or open generation, which still
waits on an extractor this cycle will not build. The README still
may not say a tiny model refuses a wrong edit. Ranking a list that
already contains the no is not meeting the no.

## 7. Predictions to freeze before any deck cell is a label

Registered blind with respect to any ranker run. The deck's
existing twin/foil pins (P4/P5, P-W4/P-W5) are already adjudicated
and are not these.

- **P-BR1.** Keyword-at-*k* is strictly below 1.0 on the family
  holdout.
- **P-BR2.** Every holdout-eligible family has ≥1 PASS ∧ ¬typed-twin
  cell; if none are eligible, the model arm parks (this prediction
  *is* the parking condition).
- **P-BR3.** Ranker mean@*k* over three seeds beats keyword-at-*k*
  under the full three-part predicate. Miss is reportable.
- **P-BR4.** Tests-only top-*k* does not match full-predicate
  top-*k* on the holdout. If they match, the matcher was not
  load-bearing and P-BR4 misses.
- **P-BR5.** A leak audit (gold tokens in ids, paths, or comments)
  refuses the split. A split that only works with those tokens is
  not this task.

Fired and missed both go in §8. No cell is scored as a training
label before this list is committed. This file commits the list.

## 8. Adjudication — after a v0.13 ranker exists

§7 above is frozen as registered. Outcomes land here.

## 9. How this was produced (disclosure, not a prediction)

Three antagonist cycles, then this close:

1. Thesis: the leftover is a propose-and-verdict loop; v0.12 is
   permission; v0.14 is the README deadline.
2. Grounding: two public model losses (0.104 vs 0.1069; 65 vs 64);
   713 specialize edges unchanged; nine programming nodes already
   self-certify under the conservative rule; no model has received
   a verdict as a signal.
3. Close: budgeted edit on the four-family deck; Stein is the only
   current PASS-not-twin cell; ineligible families cannot be held
   out; P-BR1–P-BR5 frozen here.

The registered sentences in §7 are the floors. The dialectic is
not a result.
