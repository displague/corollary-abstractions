# Roadmap v0.15 — check the belief before spending the evidence

v0.14 spent a one-shot holdout discovering that its author's belief about the
collection was wrong. Three of its five misses were properties of the
evaluator, not the resolver: a clause with no causal path from the
intervention to its number, a stratum whose ambiguity the graph did not
contain, and a control that rewards the failure it was built to catch.

So this cycle's rule is the one v0.14 paid for: **anything computable from
committed sources is computed before anything measurable is measured.**

Governing designs: [compile the space before asking the
question](DESIGN-compile-before-query.md) (architecture), [the veto on a match
the corpus cannot support](DESIGN-coincidence-veto.md) (instrument).

## 1. Compile the space before asking the question (headline, architecture)

The direction chosen at v0.13 and deferred through v0.14's clarification
experiment. Its first slice asks whether two existing exact worlds can compile
and independently check a complete bounded possibility space before any target
is selected, so that failure to find a path becomes evidence that no path
exists *within the declared bound*.

Its own construction gate governs: if the two-world or resource gate misses,
it parks rather than manufacturing a toy world. Nothing here promises an
unrestricted negative.

## 2. The coincidence veto (headline, instrument)

Implement [DESIGN-coincidence-veto.md](DESIGN-coincidence-veto.md) in its
registered order:

1. commit the closed kind menu, the incompatibility table with a reason per
   row, and the complete slot inventory for the twenty-six qualifying groups —
   every aligned slot tagged or explicitly kind-unknown;
2. register the two-sided conflict prediction against the denominator that
   inventory establishes;
3. run the blind control first — case-folded symbol-name difference — and drop
   the direction if it agrees on 80 % or more of tagged slots;
4. adjudicate once.

No rate is frozen in advance, because the slot count is not yet known and a
convenient denominator is how the last cycle got its answer wrong.

**This item carries a standing suspension.** The published cross-field
structural match count does not appear in release notes or any evidence chain
until this reads out, or two release cycles pass.

**Live status (2026-08-20): adjudicated once, partially; suspension
EXTENDED.** Registered order held: inventory (77 aligned slots across 26
groups) before tags, blind control before flags. The name-difference control
passed (0.3958 agreement against the 0.80 drop threshold); the flag count
landed at 22 of 77, inside the registered 20–60 band, and all four named
directional calls held. The third control — tag permutation — is invalid by
an authoring-time scoping defect (the table only covers pairs that co-occur
under the authored tags), so the tags' information claim stays
unestablished, and a sensitivity analysis locates the instrument's
discrimination in a single exemption row (proposition-equals-set). Full
readout: ANALYSIS "v0.15 — the coincidence veto, adjudicated once
(partially)".

## 3. Make the gate affordable without weakening it

v0.14 measured the suite honestly and the answer was one module.
`test_write_stage` is 12,522.5 s of a 21,688 s suite; every shard beyond the
second is idle. The cost is not fixtures — its overhead is 8.5 s — it is that
`stage_write` runs the corpus-dependent pipeline on **every** candidate,
including candidates it refuses for a type error in a declared delta
dictionary. One test spends 1,096.4 s rejecting six malformed dictionaries.

Register the intended check order and its refusal identities **before**
touching the code, then reorder so corpus-independent checks run first.
Refusal becomes O(1); acceptance stays O(corpus).

Two constraints, both binding:

- tests assert on *which* check refused a candidate, so the expected refusal
  identity moves with the order and must be registered, not discovered;
- a staging gate is a trust boundary. No reordering may let a candidate reach
  a check it currently never survives to.

A cheaper second lane, unblocked: the split fixture is rebuilt once per class
and costs 179.3 s each time, 1,076 s of which is duplication of a
deterministic build over an immutable corpus.

**Live status (2026-08-20): first lane SHIPPED.** Check order registered
before the move (`afafbc4`), reorder landed (`82aef3e`): all 103 tests keep
their refusal identities, the worst test falls 1,096.4 s → 46.2 s, the
module 12,522.5 s → 10,770.9 s — fourteen percent, less than the defect's
shape suggested because only the seven declared-delta refusals were paying
for a corpus pass. Indicative comparison only; the like-for-like number
needs the gate tool at the v0.15 tip. The parallel floor is unmoved.

## 4. Carried, with dependants named

| lane | named dependant | disposition |
|---|---|---|
| Exclusion seam in the resolver | *none — shipped, uncredited* | stays as behaviour no gate credits; the spent sentence remains a regression test |
| Verified-ambiguity construction check | *none in this cycle* | **parked** in BACKLOG; drafted on `feature/v015-verified-ambiguity`, and a prerequisite for any successor clarification holdout rather than a lane of its own |
| Range certification across builds | *none — needs evidence the range moves* | **parked**; see BACKLOG |
| W1–W3, both rankers, `specialize.py` general index, proof-search depth, physics/affect/visual, HTTP skin, Open-English authoring | *none* | parked, unchanged |

## 5. Governance

Unchanged from v0.13, plus two rules this cycle earned:

- **A clause must have a causal path from the intervention to its number.**
  Q4 could not have fired whatever the candidate did. Construction checks now
  owe reachability, not only rows and provenance.
- **A frozen instrument may only assert things about objects that stop
  changing.** Two of v0.14's assertions were about the live import path and
  the working tree, and both were guaranteed to fail at the moment the cycle
  succeeded.

## Release gate

v0.15 is ready only if:

- the compile-before-query slice ships its bounded closure or parks in writing
  with its gate reading;
- the coincidence veto is adjudicated once, blind control first, with the
  suspension either lifted or extended in writing;
- any check reordering lands with its refusal identities registered
  beforehand, and the trust boundary argued explicitly;
- the full suite is green on a frozen tip with retained receipts;
- every unfinished item ships or parks in writing;
- the outside design inquiry gate is discharged — the isolation method that
  worked is recorded in `reports/design-direction-v0.15.json` and is reusable.
