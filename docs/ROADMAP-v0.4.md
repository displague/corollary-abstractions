# v0.4 roadmap — reasoning chains

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
2. **Analogy depth diagnostic** — per-step teacher-forced error
   localization on the bit-identical 2416-example failure set
   (structure vs leaf steps, early vs late) BEFORE any fourth
   mechanism; positional encoding and length are eliminated.
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
10. **Tooling agenda from the misses** (BACKLOG-tracked): head-alias
    table (heads→heads, not heads→operators); per-head identity/algebra
    table with variable-slot identity binding (zero morph); fix
    specialize.py's rel-only guard and plain-binding suppression;
    groundedness v2 (pattern-membership through instantiated heads;
    recursive-definition handling); statistics seed script + the
    sum-to-one node that unblocks two twin groups; discrete↔continuous
    (sum/INTEGRAL) bridge; schema scope construct and past modality;
    trainers save checkpoints by default (two v0.3 claims are seed-
    reproducible only because --save-model postdated them).
