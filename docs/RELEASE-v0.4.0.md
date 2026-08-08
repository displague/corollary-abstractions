# v0.4.0 — The fork verdicts and the self-auditing toolchain

Baseline: [v0.3.0](RELEASE-v0.3.0.md). Plan of record:
[ROADMAP-v0.4.md](ROADMAP-v0.4.md) (closed); carried items in
[ROADMAP-v0.5.md](ROADMAP-v0.5.md). Findings: [DISCOVERIES.md](DISCOVERIES.md).

## The headline: exposure does not generalize; iteration does

The analogy depth wall — three positional mechanisms failing on a
bit-identical example set — was diagnosed exactly (the 34 = 34 result:
success coincides with staying inside trained tree levels), its first
prescription falsified honestly (closed-form level codes moved nothing:
representable is not integrated), and then settled by a controlled fork:

| arm | train depths | OOD | OOD exact |
|---|---|---|---|
| lookup addressing | 2–3 | 4–5 | 0.014 |
| lookup + curriculum | 2–4 | 5–6 | **0.006** |
| **recurrent (one shared cell per level)** | 2–3 | 4–5 | **0.226** |

Curriculum — *more* exposure — did worse at its own one-level
extrapolation than the baseline at its own: lookup addressing memorizes
the levels it sees and falls off the same cliff wherever it stands. The
recurrent arm, with less exposure, is the only mechanism showing true
extrapolation (16×). Depth-as-iteration is the direction; closing
0.226 → 1.0 (recurrence extended into the address *consumers*) heads
ROADMAP-v0.5.

## The toolchain grew up — and audited itself

Six backlog items shipped as parallel agent deliveries (two waves, six
agents, zero merge conflicts):

- **HEAD_ALGEBRA**: declared per-head commutativity/identities, every
  entry citing its justifying corpus node. Payoffs at looseness 0:
  affixation specializes via the zero morph on the *linguistically
  correct inner position*; the Boolean laws gain their first
  derivational structure (absorption ⊒ idempotence).
- **Cheapest-derivation search**: exhaustive branch-and-bound that is
  *faster* than the greedy search it replaced; acceptability moved
  inside the search after proving that "did you need mechanism X"
  questions secretly meant "was X on the first path" — a bug found
  alive in decompose.py one import away and fixed. 622 edges (33
  recovered, 0 lost, 128 re-derived cheaper).
- **Groundedness v2**: both measured pathologies fixed (instance-below-
  pattern; recursive definitions); corpus mean 0.700 → 0.766, 32
  statements rise, zero fall.
- **Matcher consistency**: the match ladder now holds *by construction*
  (equal typed forces equal shape); the slot-vs-head lint ships,
  finding 7 names across 25 statements.
- **Seed↔JSON coherence**: check_regeneration.py makes seed ownership a
  checked invariant (13 seeds byte-identical; the founding statistics
  corpus gained its seed, its sum-to-one axiom, and the reciprocal
  GRPO↔z-score edge).
- **Head-alias level**: declared head classes; the registered
  word/phrase-recursion prediction cashed (one skeleton, aliased).

**The self-audit result of the cycle**: the scope design's measurement
pass caught our own alias table asserting a falsehood (`order_le`
declares a reflexive order that asymmetry makes derive ⊥ at x = x,
inert only by luck) — the epistemic ladder's REFUTED rung applied to
the tooling itself. Fix specified (LT strict head; relation into
HEAD_ALGEBRA), carried to v0.5.

## Corpus

199 nodes / 21 disciplines, all seed-owned. New families:
**transitivity across four disciplines** (consequence ≅ subset ≅
containment ≅ precedence — carriers sharing only the order axioms) and
the **convex-combination family** (mixtures ≅ interpolation ≅
de Casteljau), which also produced the sharpest spelling-dependence
case yet (one node whose two standard spellings each twin a different
family). Docs periphery retired the deprecated direct-JSON workflow
everywhere it was still taught.

## Design for v0.5

`docs/DESIGN-scope-and-modality.md` + draft schema (validates 199/199):
scope lives *beside* the template (wrapping it was measured destroying
the fiction↔Boolean bridge); past modality needs only new call heads
plus a separately-reported **mirror** level; nine payoff nodes listed
including Chekhov's converse, ordered pattern-before-instance.

## Resolved from BACKLOG this cycle

The six shipped items above, plus: specialize's rel-only guard and
plain-binding suppression (Chekhov's gun formally an LTL liveness
instance); atomic-statement grounding; the missing-statistics-seed gap.

## Honest limits carried forward

Depth 0.226 → 1.0 open (recurrence not yet in consumers); cost weights
are the matcher's first corpus-unfalsifiable numbers (21-run sweep
invariant — unease recorded); the typed sort carries the tie the shape
sort just lost; genuinely-unshared heads still ground at 0.0
(narrative units); reports/ lacks its own regeneration check;
chained composition, frames implementation, corpus-grounded analogy,
prover phase 2, attunement all carried with designs intact.

## Assets (this cycle's claim-bearing checkpoints)

- `analogy_diag.pt` — the model behind the 34=34 diagnosis
- `analogy_sin_s0.pt` / `analogy_sin_s1.pt` — the falsified sinusoidal
  prescription (negative results ship too)
- `analogy_rec_s0.pt` — the recurrent arm's 0.226 (the fork winner)
- `analogycur_table_s0.pt` — the curriculum arm's 0.006 (the fork loser)

v0.3.0's thirteen assets remain on that release; all results are
seed-reproducible from committed code.
