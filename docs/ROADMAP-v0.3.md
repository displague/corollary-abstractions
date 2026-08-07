# v0.3 roadmap — grounded composition

> **CLOSED at v0.3.0** — historical plan-of-record. Triage:
> item 2 shipped ([RELEASE-v0.3.0.md](RELEASE-v0.3.0.md)); item 3 shipped
> as a measured negative; items 1, 4, 5 and item 2's model-in-the-loop
> half carried to [ROADMAP-v0.4.md](ROADMAP-v0.4.md) (#1–#5). Corpus
> growth and release mechanics shipped. Nothing dropped.

Theme (user's framing): support the composition of sentences — including
sentences with mathematical grounding and accuracy — as the expression of
abstract reasoning, verifiable and emergent from the measured strengths:
pointing, tree addresses, extrinsic lexica, derivational decomposition,
and the prover's ground truth.

## Deeper experiments (release-gating for v0.3)

1. **Corpus-grounded analogy completion.** Move the analogy task from
   synthetic trees to the real corpus: given Ohm : circuits :: ? :
   mechanics, produce `F = m·a` — targets verified against
   `specialize.py` bindings and twin-ledger membership rather than
   generator labels. The decomposition report supplies constituents;
   the twin families supply the quadruples.

2. **Grounded sentence composition.** Extend the demo pipeline from
   answering to *asserting*: model selects a skeleton + fillers
   (concept tree), the renderer realizes it as a sentence, and
   `decompose.py` attaches the provenance line — "this claim is an
   instance of the scaled-linear family (28 statements)" — so every
   generated sentence carries its mathematical grounding. Hallucination
   check: a composed statement whose constituents match no known form
   is flagged, not asserted.

3. **The analogy depth wall, isolated.** Decoder tree-coordinates did
   not rescue depth OOD (0.014, both position schemes): the failing
   component is the leaf-ordinal correspondence — counting. Next probes,
   in order: tie decoder/encoder path embeddings (path-matching becomes
   dot-product-visible, replacing counting); if insufficient,
   path-relative pointer biasing. Whatever survives becomes the fourth
   entry in the interface catalogue (features, lexicon, addresses, ...).

4. **Prover phase 2 — baseline tactic policy.** Train the first policy
   on extracted triples (scale extraction beyond the 155 first);
   evaluate next-tactic accuracy; wire PyPantograph best-first search
   so proved-vs-not becomes the metric. Concept-token encoding of proof
   states (the closed unicode inventory) vs subword — milestone 3 on
   real formal data.

5. **Attunement curves.** With the symbolic-scaffold auxiliary losses
   (predict skeleton, predict family, predict unification outcome),
   measure whether the grounded-composition capabilities appear
   earlier/smaller than without — the user's attunement question as
   training-signal experiment.

## Corpus growth in this cycle

Numerical analysis, combinatorial graph theory, geometric modeling
(agents in flight) — chosen for their iteration/recurrence statements
(Newton's method, Euler's method vs gradient descent/SSM), counting
identities (handshake lemma, complete-graph edges), and convex/affine
constructions (lerp, Bézier weighted sums vs total probability).

## Release mechanics

The `release` skill (.claude/skills/release) now governs releases:
ledger refresh, living-docs update, annotated tag, `gh release create`
with notes, and model checkpoints attached as assets.
