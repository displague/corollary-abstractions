# Design — self-grounding ingestion, measured (forward-looking, for ROADMAP-v0.11)

Written during v0.10 triage, before item 4's corpus exists, so the null
model is registered before the number it judges. This is the release's
forward-looking design item; it does not ship in v0.10.

## 1. Where this came from (an accident, not a plan)

Item 5's session authored one node, `MOD(2 ^ 30, 1000) = 824`. It shares the
subterm `2 ^ 30` with the corpus's only other ingested statement,
`DIVIDES(13, 2 ^ 30 + 3 ^ 60)`, and the decomposition ledger immediately
recorded each as grounding the other through the `prior_corpus` channel —
the first two prior_corpus constituents in the corpus to carry a real shared
discipline (`number_theory`) rather than the `mathematics` umbrella.

Nobody designed that. The registered prediction for that slice said the pins
would move by denominator dilution, as they had four times before; they
moved the other way, because a second ingested statement was enough for the
ingested layer to start referring to itself.

Two constituents on 257 nodes is an anecdote. The interesting question is
whether it is the first point on a curve.

## 2. The question, and why both answers are worth having

As item 4 takes ingested nodes from 3 to thousands: **does the share of
subterms grounded INSIDE the ingested layer rise with corpus size, or
flatten?**

- **Rising, and faster than the corpus grows** — ingestion compounds. Each
  ingested statement makes the next one cheaper to ground, and the corpus
  is accumulating structure rather than rows. That is the claim the whole
  ingestion program has been betting on since v0.9, and it has never been
  measured.
- **Flat** — ingested statements are mutually alien: they share numerals and
  operators but not structure. Ingestion buys COVERAGE and not STRUCTURE,
  which would change what the corpus is for and would make the
  hand-authored layer the only place structure lives. This is the more
  interesting negative, and it is a publishable result rather than a
  setback.

Either way the number belongs in the v0.11 release notes, because the
project has been asserting the compounding story informally for two cycles.

## 3. The measurement

For a corpus with `N` ingested nodes, at several `N` (subsample the ingested
layer at, say, 8 / 32 / 128 / 512 / all, with the hand-authored corpora held
fixed):

- **ISG(N)** — ingested self-grounding: of all considered subterms in
  ingested nodes, the fraction whose owner is another INGESTED node. The
  decomposition channels already distinguish same-corpus, prior-corpus and
  external ownership, so this is a query over
  `reports/decompositions.json`, not new machinery.
- **XSG(N)** — cross-layer grounding: the fraction whose owner is a
  hand-authored node. Reported beside ISG, because a rise in ISG that comes
  entirely at XSG's expense is a redistribution, not compounding.
- Both reported with the raw counts, never percentages alone: at small `N`
  a single shared numeral moves the rate by whole points, which is exactly
  how item 5's two constituents could look like a trend.

**Sampling discipline.** Subsamples are drawn by a seeded, committed
selection (the same discipline the corpus sources use), and every point is
recomputed by the committed generator rather than interpolated. The curve is
committed as `experiments/self_grounding_curve.json`.

## 4. The null model, registered before the measurement

A rising ISG curve means nothing without knowing what rising curve *chance*
produces. Ground arithmetic statements share numerals for uninteresting
reasons — small integers are common — so the null is not zero.

**Null:** for each subsample size, generate a matched set of SYNTHETIC
ground statements over the same operator inventory and the same numeral
distribution as the real ingested layer (sampled from the observed
distribution, not uniform), skeletonize them through the same matcher front
end, and compute ISG the same way. The synthetic statements are structurally
random but distributionally identical.

**The claim to be tested is ISG_real(N) − ISG_null(N) > 0 and growing.** A
real curve that tracks the null says the corpus's ingested layer is sharing
numerals, not structure — the flat answer above, arrived at honestly instead
of by eyeballing a rising line.

Registered before any run:

- **S1** — ISG_real(N) is strictly greater than ISG_null(N) at the largest
  N, by more than the seed-to-seed spread of the null.
- **S2** — the gap widens with N (compounding), rather than being a constant
  offset (a fixed structural advantage that does not accumulate).
- **S3** — XSG does not fall by as much as ISG rises: the ingested layer
  gains owners without losing its connection to the hand-authored corpus.
- **S4** — the effect survives removing the single most common subterm
  (today that would be `2 ^ 30`): a curve carried by one popular term is a
  fact about that term, not about ingestion.

S4 is the one most likely to fail, and it is the one that would matter most.

## 5. What this rests on, and what it is not

Rests on: item 4 (a materially larger ingested corpus — this design is
unmeasurable without it), the decomposition channels as they already exist,
and the `prior_corpus` / `same_corpus` / `external` ownership distinction
that v0.7 argued for and v0.10 item 5 accidentally exercised.

It is **not** a claim that self-grounding implies correctness, usefulness,
or proof. A subterm having an owner inside the corpus is a structural fact
about the graph and nothing more — the same honesty boundary the external
verifier states about a passing check.

It also gives ROADMAP-v0.10 item 6 (the external benchmark, carried twice and
still unstarted) its most defensible shape: a structure-recovery claim the
architecture wins *because* of its design, measured on a corpus large enough
to be uncomfortable, against a null that a keyword baseline cannot beat by
construction.

## 6. Correction, before any measurement ran

§3 said ISG "is a query over `reports/decompositions.json`, not new
machinery". **That is wrong, and finding it now is why the design was
written before the slice.**

The committed ledger records, per constituent, its `channel`, an
`owner_channels` TALLY, `recurs_in_n_statements`, and `instance_of_statements`
— but **not the owner statement ids**. `same_corpus` / `prior_corpus` /
`external` answer *what kind of relationship* an owner has to the node, never
*which node* it was. "Grounded by another INGESTED node" is a question about
owner identity, and it cannot be asked of the committed artifacts. (The owner
sets do exist, inside `decompose.analyze`'s `channel_of`; they are discarded
before the report is written.)

Two honest routes, and the choice belongs to the v0.11 slice:

1. **Emit owner ids per constituent** — a small additive field in
   `decompose.py`, which makes ISG a real query and helps every future
   ownership question. Cost: it changes `reports/decompositions.json` for
   every node, so it must not be attempted while another slice is
   regenerating ledgers; it lands on a quiet main, with its own
   acknowledgment if any pin moves.
2. **Measure a weaker, well-defined proxy that IS computable today**: the
   fraction of an ingested node's grounded constituents whose *skeleton* also
   occurs as a subterm of at least one other ingested node. That is exactly
   the shape of the item-5 observation (`^(2, 30)` with
   `recurs_in_n_statements: 2`), and it is a fact about shared structure
   rather than about attributed ownership.

They are not the same measurement and must not be reported as if they were:
route 2 counts subterms two ingested statements HAVE IN COMMON, route 1
counts subterms one ingested statement GROUNDS IN another. Route 2 will read
higher, because sharing is symmetric and grounding is not. If the slice ships
route 2 for speed, the release must say which one the number is.

Recommended: route 1, because the owner id is the thing every later
ownership question also wants, and because a proxy reported as the real
measurement is how a project talks itself into believing a curve.
