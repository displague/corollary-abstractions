# Design — groundedness-at-all as an admission signal

Written for ROADMAP-v0.13 item 4, before constructing or scoring any of the
near-miss foils below. The v0.12 number that motivated this design is a probe,
not a registered result: on miniF2F and Goedel-Pset, exact grounding by any
owner beat a distribution-matched random-tree null by 17.5–46.2 percentage
points at every measured size. This design asks the harder question the probe
did not ask: can that quantity reject a statement whose syntax is almost an
authored statement rather than a random tree?

The experiment does not decide truth, proof, usefulness, or semantic
coherence. It tests one bounded admission signal: how much of a candidate is
already an exact form in the committed graph.

## 1. The candidate-level signal

For a candidate statement, run `decompose.analyze_loaded` with
`pattern_membership=False` against the unchanged committed `data/` graph.
Let:

```
grounded_at_all = fixed-owned exact constituents / considered constituents
```

An exact constituent counts only when at least one of its recorded `owners`
is a statement in the fixed graph loaded from `data/`. Other candidates in
the measurement never count as owners. This exclusion is load-bearing:
scoring a batch must not let near-misses ground one another. Pattern
absorption stays off because the v0.12 probe was exact grounding and because
an admission gate should not inherit the known absorption false positives.

The registered gate is:

```
ADMIT iff considered > 0 and grounded_at_all >= 0.50
```

The threshold is fixed from the meaning of the scale — at least half the
candidate's non-trivial constituents must already be owned — not fitted to
the new foils. A zero-denominator candidate is refused, not admitted as the
decomposer's definitional `1.0` case.

This is deliberately narrower than the groundedness *epistemic status*.
Admission means only "not rejected as structurally ungrounded by this gate."
It cannot promote a statement to VERIFIED or PROVEN.

## 2. Positives and the harder foil

**Authentic arm.** Quarantined miniF2F and Goedel-Pset statements, parsed from
their committed `data_holdout/*/nodes.json` files. They remain outside
`data/`; neither source can become its own fixed owner.

**Plausible-but-ungrounded arm: one-head paired near-misses.** For each source
and seed, choose 64 authentic statements that can be paired as follows:

1. Parse the authentic template and enumerate non-root internal `call` and
   `op` nodes. Relation heads and leaves are never changed.
2. Pair candidate nodes only when they have the same node kind and arity,
   belong to different statements, and have different heads.
3. Swap the two heads. Each statement therefore receives exactly one changed
   head while retaining its relation, tree topology, arities, slots, numbers,
   and every child subtree.
4. Render and parse the result again; refuse the pair if either foil is not a
   valid template, canonicalizes to its authentic source, or changes the
   decomposer's `defined_head` classification.

Pairing is deterministic for seeds `20260818`, `20260819`, and `20260820`:
seeded order over statement ids and eligible paths, then the first 32
disjoint valid swaps. Each swap supplies two statement-level authentic/foil
pairs, for 64 pairs per source. No source may contribute fewer than 64 such
pairs for a seed; if it does, the construction misses and the experiment is
not resized after inspection.

This is harder than the v0.12 null in three checkable ways. Within every pair,
the head-blind tree is byte-identical. Across the 64-pair batch, swapped heads
preserve the exact multiset of head labels. Every leaf and every unchanged
subtree came from an authentic statement. The foil is a local mathematical
near-miss, not a tree sampled from an operator inventory.

The design calls the foil "ungrounded" prospectively because the changed
headed constituent and its containing ancestors have no entitlement to an
owner. The score is allowed to refute that description. If the committed
graph already owns most of those compositions, the gate misses; no second
mutation is tried.

## 3. Capability-blind baseline and vacuity

The blind baseline sees the head-stripped tree only: node kinds, arities,
relation, slots, and numbers, but no `call` or `op` head labels and no
decomposition fields. Authentic and foil members of every pair must therefore
have identical baseline input. Pairwise accuracy is exactly 0.5 with ties
worth half; balanced classification accuracy of either constant decision is
also 0.5.

The run is refused as vacuous if any of these construction invariants fails:

- fewer than 64 pairs for either source at any seed;
- any pair differs in head-blind shape, leaves, considered topology, or more
  than one head position;
- the authentic and foil batch head multisets differ;
- the blind paired baseline is not exactly 0.5.

The baseline does not read ids or paths. Ids exist only to make the ledger
auditable.

## 4. Registered predictions

All headline numbers are means over the three fixed seeds. Results are also
reported per source and per seed; no single-seed win is a claim.

- **G1 — admission.** At the registered 0.50 threshold, balanced accuracy is
  at least 0.70 on **each** source. Both authentic acceptance and foil
  rejection must be strictly above 0.50 on each source; a constant decision
  cannot fire G1.
- **G2 — paired separation.** Counting a tie as one half, the authentic member
  has higher `grounded_at_all` than its foil in at least 0.75 of pairs on
  **each** source.
- **G3 — non-vacuity.** All construction invariants in §3 hold on every seed,
  and the capability-blind paired baseline is exactly 0.50. If G3 misses, G1
  and G2 are `REFUSED`, not favorable results.
- **G4 — source robustness.** The mean authentic-minus-foil score margin is
  positive on both sources. miniF2F alone is not enough; Goedel-Pset alone is
  not enough.

`adjudicate()` computes these predicates from the ledger. Fired, missed, and
refused all land without changing this section.

## 5. Reproducibility and artifact

The implementation is a thin experiment script using the existing parser,
renderer, `load_trees`, `attach_extra`, and `analyze_loaded` APIs. It loads the
fixed graph once per run, evaluates each seed as one batch, and recomputes the
candidate score from `constituents[].owners` intersected with the frozen
fixed-id set. It does not edit seeds or corpora and does not call
`specialize.py`.

The committed ledger is `experiments/grounded_admission.json`. It records the
schema, source digests, seeds, threshold, every pair's source id, changed path
and two heads, authentic/foil scores and decisions, construction checks,
per-seed metrics, and closed-form adjudication. A byte-identical rerun is a
test requirement.

## 6. Consequence map

- G1–G4 fire: item 4 ships as a bounded exact-structure admission signal, with
  the truth/proof limitation attached.
- G3 fires but G1 or G2 misses: the harder foil defeats the signal. Publish
  the miss and park the gate; do not tune the threshold or mutation.
- G3 misses: repair only the construction invariant, then create a new design
  before scoring. Do not read an invalid run as evidence about admission.

## 7. Adjudication

The design above was committed at
`3fe54cf28bdbcf9870538daf888898c9b234ac21` before the foil was constructed
or scored. The first valid run used the three registered seeds and wrote
`experiments/grounded_admission.json`.

All construction checks passed on all six source/seed cells: 64
statement-level pairs per cell, identical head-blind trees and considered
topology within each pair, identical authentic/foil batch head multisets, and
blind paired accuracy 0.5. G3 **FIRED**, so the harder foil is valid and G1,
G2, and G4 are scored rather than refused.

| source (three-seed mean) | authentic acceptance | foil rejection | balanced accuracy | paired accuracy | mean score margin |
|---|---:|---:|---:|---:|---:|
| miniF2F | 0.8698 | 0.1406 | **0.5052** | 0.6068 | +0.0288 |
| Goedel-Pset | 0.6458 | 0.3750 | **0.5104** | 0.5859 | +0.0245 |

- **G1 MISSED.** Both balanced accuracies are effectively the blind 0.5
  baseline, far below 0.70. The gate admits authentic statements, but it also
  admits 85.9% of miniF2F foils and 62.5% of Goedel-Pset foils.
- **G2 MISSED.** The authentic statement outscores its paired one-head
  near-miss only 0.6068 / 0.5859 of the time with ties worth half, below 0.75
  on both sources.
- **G3 FIRED.** The miss is not a random-tree or label-balance artifact; every
  registered construction and vacuity check passed.
- **G4 FIRED.** Authentic scores are higher by +0.0288 / +0.0245 on average.
  That is a small diagnostic sensitivity, not an admission gate: it did not
  produce either registered separation result.

The v0.12 probe was true and its suggested consequence was false. Exact
grounding by any owner separates authentic corpora from random trees, but a
single arity-preserving head substitution retains enough known local parts to
pass the 0.50 gate. The threshold and mutation are not tuned after this miss.
Groundedness-at-all is parked as an admission signal.
