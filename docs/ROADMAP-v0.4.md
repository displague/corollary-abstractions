# v0.4 roadmap — reasoning chains

> **CLOSED at v0.4.0** — historical plan-of-record. Triage: items 2 and
> 10's six SHIPPED entries are in [RELEASE-v0.4.0.md](RELEASE-v0.4.0.md)
> (the depth fork settled: recurrence 0.226 vs curriculum 0.006); items
> 1, 3–9 and the OPEN tooling entries carried to
> [ROADMAP-v0.5.md](ROADMAP-v0.5.md). Nothing dropped.

Theme: chained composition with the prover as verifier — each proposal
becomes the next step's premise, checked before it stands. Story
generation and derivational reasoning are one problem here
(DESIGN-frames-and-retrieval.md); the golden-chicken demo and a
multi-step derivation are the same milestone in two costumes.

## Carried from v0.3 (designs intact)

1. **Corpus-grounded analogy completion** — Ohm : circuits :: ? :
   mechanics → `F = m·a`, verified against `specialize.py` bindings and
   twin-ledger membership; quadruples sourced from twin families,
   constituents from `reports/decompositions.json`.
2. **Analogy depth diagnostic** — **SHIPPED**: per-step teacher-forced
   localization produced the exact 34=34 boundary (untrained path-
   embedding rows); the sinusoidal prescription was then FALSIFIED
   (representable is not integrated — the consumer is depth-naive), and
   the design fork ran empirically: the recurrent arm (depth as
   iteration, shared GRU cell over levels) is the first mechanism to
   move the wall at all (OOD 0.0139 → 0.226, 16x, zero deeper
   exposure); curriculum arm adjudication pending. Remaining open:
   closing the 0.226 → 1.0 gap.
3. **Prover phase 2** — baseline tactic policy on extracted triples
   (scale extraction first), PyPantograph best-first search,
   proved-vs-not as metric; concept-token vs subword encoding of proof
   states as milestone 3 on real formal data.
4. **Attunement curves** — symbolic-scaffold auxiliary losses vs
   without, measured as capability-vs-scale curves.
5. **Model-in-the-loop grounded composition** — learned skeleton+filler
   selection feeding compose_assert's ladder.

## New this cycle

6. **Chained composition** (the thesis): propose-verify-repeat over
   frame state; a plot event or derivation step is a tactic applied to
   state, checked against frame + corpus. First target: a 3-step
   derivation and a 3-beat story from the same loop.
7. **Frames implementation**: scoped premise sets over the ladder
   (schema scope construct is a filed gap); frame-local VERIFIED,
   revert-on-exit.
8. **Retrieval-as-action prototype**: RETRIEVE(key) as third action
   type, UNKNOWN-triggered, symbolic execution, miss → search →
   abstention.
9. **Expressive rendering**: richer realizer or a small pointer-only
   surface model over the extrinsic lexicon.
10. **Tooling agenda from the misses** (BACKLOG-tracked) — most items
    SHIPPED this cycle, pre-sorted for release triage:
    - **SHIPPED — head-alias match level** (declared classes; cashed the
      word/phrase recursion prediction with one authored node).
    - **SHIPPED — HEAD_ALGEBRA table** (per-head commutativity /
      identities with per-entry corpus citations; 7 new looseness-0
      edges incl. affixation via the zero morph on the linguistically
      correct inner position; Boolean corpora's first derivational
      structure; two empirically-found guards).
    - **SHIPPED — specialize.py rel-only guard + plain-binding
      suppression fixes** (Chekhov's gun formally an LTL liveness
      instance; Euler polyhedron = chi at 2; 589 edges, ranking holds).
    - **SHIPPED — groundedness v2** (pattern membership + recursive
      definitions; mean 0.700 → 0.763, 32 rise zero fall; open half:
      genuinely unshared heads, e.g. narrative structure units).
    - **SHIPPED — seed<->JSON coherence checker + statistics seed**
      (13 seeds byte-identical; sum-to-one node twinned barycentric on
      contact; GRPO<->z-score made reciprocal).
    - **SHIPPED — corpus gaps**: mixture node (convex-combination family
      x3 disciplines), hypothetical syllogism (transitivity family x4).
    - **PARTIAL — discrete↔continuous**: sum~INTEGRAL alias cleared
      blocker 1 for Gauss-Bonnet/Poincare-Hopf; still blocked by
      invariant-as-slot-vs-head (now blocking three pairs — lint
      promoted, open) and the 2*pi normalization.
    - **PARTIAL — checkpoint saving**: analogy trainer gained
      --save-model; not yet default across trainers.
    - OPEN: schema scope construct and past modality; cheapest-
      derivation search in specialize (first-success-wins won't scale
      past two mechanisms); aliased-level ordering normalization; shape
      vs typed ladder inversion under commutative-call sorting.
