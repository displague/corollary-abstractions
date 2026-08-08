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

## See the improvement (Before → Now → Demonstrate)

**Depth generalization.** *Before:* the analogy model failed on deeper
trees at 0.014 OOD — bit-identically under three positional encodings —
and training on deeper examples made it *worse* (0.006). *Now:* the
recurrent address encoder extrapolates at 0.226 with no deeper
exposure. *Demonstrate:*
```
cd experiments
python -c "import json; [print(f, json.load(open(f))['ood_exact']) for f in ['results/analogy_s0.json','results/analogycur_table_s0.json','results/analogy_rec_s0.json']]"
# or retrain the winner from seed (~35 min GPU):
python train_analogy.py --level-code recurrent --data-dir data --out results/repro.json
```

**Head algebra.** *Before:* `MEET(TOP, X)` and `MEET(X, TOP)` were
different skeletons by authoring luck, and the Boolean laws had no
derivational relationships at all. *Now:* declared per-head algebra
makes orderings robust and absorption ⊒ idempotence fires. *Demonstrate:*
```
python scripts/specialize.py | grep idempotence
```

**Specialization search.** *Before:* first-success-wins silently
dropped every Ohm's-law generalization (a degenerate reading pre-empted
the good one) and paid identity costs when honest bindings existed.
*Now:* exhaustive cheapest-derivation — 622 edges, 33 recovered, none
lost, faster. *Demonstrate:*
```
python scripts/specialize.py | head -30        # looseness-0 edges lead
grep -c '"general": "physics.circuits.ohms_law"' reports/specializations.json
```

**Groundedness.** *Before:* Chekhov's gun scored 0.000 — below its own
abstraction — and recursive definitions graded as gibberish. *Now:*
pattern membership and recursion handling; mean 0.700 → 0.766, zero
statements fall. *Demonstrate:*
```
python scripts/decompose.py | head -3          # mean + least-grounded line
```

**Seed coherence.** *Before:* a hand-edit to any nodes.json drifted
silently until regeneration clobbered it; statistics had no seed at
all. *Now:* a checked invariant. *Demonstrate:*
```
python scripts/check_regeneration.py           # "coherence OK: 13 seeds..."
```

**Ladder soundness.** *Before:* the shape level could split what typed
united (inverted ladder), and slot-vs-head naming conflicts were
invisible. *Now:* equal-typed forces equal-shape by construction; the
lint names 7 conflicted names across 25 statements. *Demonstrate:*
```
python scripts/match_signatures.py | grep -A4 "slot and head"
```

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

## Assets (each with its story)

- `analogy_diag.pt` — the checkpoint behind the **34 = 34 diagnosis**:
  teacher-forced per-step evaluation of this model
  (`experiments/diagnose_analogy.py --checkpoint results/analogy_diag.pt`)
  localizes the depth failure to untrained path-embedding rows and
  reproduces the exact success/failure boundary.
- `analogy_sin_s0.pt` / `analogy_sin_s1.pt` — the **falsified
  prescription**: closed-form sinusoidal level codes that moved OOD only
  0.014 → 0.022, proving *representable is not integrated*. Negative
  results ship because the next person will otherwise re-run them.
- `analogy_rec_s0.pt` — the **fork winner**: depth-as-iteration at
  0.226 OOD with no deeper exposure, the only mechanism ever to move
  the wall. Load it against `data/analogy_ood.jsonl` to reproduce the
  16× gap over any lookup checkpoint.
- `analogycur_table_s0.pt` — the **fork loser**, kept deliberately:
  more exposure, worse extrapolation (0.006). The pair of fork
  checkpoints is the controlled comparison in artifact form.

v0.3.0's thirteen assets remain on that release; every result is also
seed-reproducible from committed code.
