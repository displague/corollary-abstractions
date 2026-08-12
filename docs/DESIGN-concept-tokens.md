# Design: Concept Tokens and the Extrinsic Lexicon

Status: design intent, not yet implemented. This document records the model
vision behind the repository so the data and tooling work stays aimed at it.

## The idea

A small model whose vocabulary is made of *concepts* — formulae,
relationships, and recurring composite phrases — rather than word fragments,
with the surface lexicon (words, notation, grammar) stored *outside* the
weights and reached by reference.

The guiding intuition: a mind holds a concept before it finds the words. It
sometimes struggles to realize the concept lexically — considering candidate
words, even walking the alphabet or a mental dictionary. That failure mode is
evidence of an architecture: concepts and their lexical realizations are
stored separately, joined by a lookup that can miss. Traditional LLMs collapse
the two — words, grammar, and world knowledge all share the same weights,
which is a major reason they cannot be small.

## Three commitments

### 1. Forms as tokens, forms as constructs of forms

A formula's structural skeleton is a token. `?0 = *(?1:P, ^(?2:V, 2))` — the
skeleton `scripts/match_signatures.py` computes for circle area, sphere
surface area, and cube surface area — is *one* vocabulary item, not a string
of operator characters. Larger statements are constructs of smaller forms:
postulates and sentences are compositions over the concept vocabulary, the
same way this repo's statement nodes compose slots, operators, and other
statements via `inferential_links`.

The ontology in `data/` is therefore not a detour from the model — it is the
prototype of the model's vocabulary. Every archetype the matcher discovers is
a candidate concept token; every `equivalent_forms` list is that token's
surface-realization set.

### 2. The extrinsic lexicon

Words and notation are not stored in the weights. The model's core operates
over concept tokens; a separate, referenceable lexicon maps concepts to
surface forms (English words, LaTeX, ASCII notation, discipline-specific
symbols). Realization is a lookup — sometimes a search — not a weight matrix.

This is the load-bearing decision for the size budget, not just an aesthetic
one. In a small transformer the embedding table dominates: a conventional
50k-token vocabulary at 512 dimensions in fp16 is ~51 MB — nearly the entire
64 MB budget before a single reasoning layer exists. Moving lexical knowledge
into an external index (which can live on disk, be memory-mapped, and be
swapped per-domain) is the only way a model this small has room to reason.

Known machinery this maps onto, so we are not inventing from scratch:

- pointer/copy mechanisms (pointer-generator networks) — the model *points*
  into the lexicon rather than generating words from weights; this is the
  legitimate home of the original PGN instinct
- retrieval-augmented decoding (RETRO-style) — nearest-neighbor lookup into
  an external store during generation
- hashed / frozen / factorized embeddings — vocabulary scale without
  vocabulary-proportional weights

The "tip of the tongue" behavior comes for free: when the lexicon lookup is
ambiguous or misses, the model degrades exactly the way a mind does — it has
the concept and must search for the word (neighboring entries, synonyms,
alphabetic scan) instead of hallucinating fluent nonsense.

### 3. Composite tokens — comprehension nuggets

Training tokens may be much larger than today's subword pieces: combinations
of the most common words and phrases — nuggets so commonly reused they serve
as their own unit of comprehension. A composite token is a *pseudonym for its
thesaurical twin* of smaller, simpler expression, exactly as a complex
formula in one discipline is a twin of a simpler sibling in another (the
matcher's typed-twin groups are the formal-domain version of a thesaurus
entry).

Practical notes and honest caveats:

- This is aggressive BPE / multi-word tokenization taken seriously. It
  shortens sequences (helping a small recurrent/SSM core) and pre-compresses
  meaning.
- Sparsity risk: the larger the token, the fewer training occurrences it has.
  Composite tokens must earn their place by frequency, and every composite
  must remain decomposable to its simpler twin so the model can fall back.
- Canonicalization is exact in formal domains (two formulas either share a
  skeleton or they don't) and approximate in natural language (synonymy is
  graded). Start where it is exact.

## Architecture position (revised from the original sketch)

The original sketch assigned cognitive roles to layer types (GRU for proofs,
LSTM for reasoning, PGN inner loop, SSM outer wrapper). Trained networks do
not respect role assignments like that, and a four-architecture hybrid is
undebuggable at small scale. The revised position:

- one small end-to-end core (small transformer or Mamba-style SSM — the SSM
  instinct survives; it is the efficiency story for long contexts)
- concept-token vocabulary in, concept-token predictions out
- pointer/retrieval head into the extrinsic lexicon for surface realization
- search on the outside (see `prover/`): the model proposes, a verifier
  disposes — capacity we do not have to store in weights

The 64 MB target is then spent almost entirely on relational structure over
concepts, which is the part that was always supposed to generalize across
knowledge domains.

## What must be true for this to work (falsifiable milestones)

> **Status 2026-08-07** (details in experiments/ANALYSIS.md): milestone 1
> holding (49 stable skeletons over 67 nodes, zero parse failures);
> milestone 2 **passed** on synthetic (2.7x) and real corpus (8.4x with
> the skeleton vocabulary as the extrinsic store); milestone 3 **passed
> with a revision** — concept tokens beat subword everywhere tested, but
> the deeper result is that exact operations (equality, structure checks)
> must stay symbolic: the hybrid (symbolic bits + learned residual)
> strictly dominates every pure encoding, and is the only arm whose OOD
> accuracy exceeds in-distribution. Milestone 4 (round-trip) implicitly
> exercised by the bilingual world's canon arm. The extrinsic-lexicon
> commitment gained a second leg: weight-stored lexica are not just
> oversized but brittle (chance OOD), while the same lexicon supplied
> externally loses nothing.

1. Skeleton extraction scales: the matcher's canonical skeletons stay stable
   and discriminative as the corpus grows past hundreds of nodes.
2. Concept tokens compress: re-encoding statements over the concept
   vocabulary yields materially shorter sequences than character/subword
   encoding of the same corpus.
3. A tiny model over concept tokens beats the same-size model over subword
   tokens on a held-out formal task (e.g., predicting the corollary/twin
   relation, or tactic prediction in `prover/`).
4. The extrinsic lexicon round-trips: concept → surface form → parse →
   same concept, across at least two disciplines' notations.

If milestone 3 fails, the concept-token thesis fails, and the honest response
is to keep the ontology and matcher (useful regardless) and drop the model.

## Relationship to the rest of the repo

- `data/*/nodes.json` — seed concept inventory and surface-realization sets
- `scripts/match_signatures.py` — skeleton extraction; the future tokenizer's
  first pass and the source of twin/pseudonym structure
- `prover/` — the verifier-coupled task where a small model can genuinely
  punch above its weight class; first consumer of concept tokens
- `docs/DESIGN-language-as-structure.md` — NL analysis/creation as term
  algebra + linearization (the dual of prove/pretty-print); retracts string
  templates as design law while keeping parse-first and extrinsic lexicon
