# The corpus as a vocabulary: recurrent blocks, template tokens, structured ids

**Status: maintainer-seeded design candidate, pre-course.** Seeded
2026-08-23 by maintainer direction during the v0.17 gate run, with a
standing instruction recorded verbatim so no course can quietly drop
it: *taken through the design loop, but not simply disregarded if that
doesn't bear something more inspired and better fitting — revisit this
directly.* This document is the **named candidate** the v0.19 design
course (which the ROADMAP-v0.18 gate requires to be invoked, not
reaffirmed) must adjudicate explicitly: adopted, superseded by
something measurably better-fitting, or parked with the measurement
that parked it. Silence is not a disposition.

## 1. The idea, as directed

Recurring surface patterns earn their own vocabulary entries,
self-expanding by measured recurrence: if "this is" recurs enough it
becomes a token, "this is a" a successor token, "this is a test"
another — until the vocabulary (say 2^24 ids) holds the corpus's
actual recurrence structure. Ids are not opaque: **structured bit
fields** carry a namespace/vocabulary partition, a length, format
instruction, repetition qualities — or a *sameness* dimension
(the same concept across languages or across corpora). Beyond flat
blocks, **template tokens** with slots: `"Hello {fragment},"`,
`"{nbit-1} = {nbit-2} + {nbit-3}"` — templates so recurrent across
the data that they warrant first-class tracking. This is close to
building a compression algorithm, so the same dictionaries should be
**natively consumable** (the compressed form is the access format,
not an archive), and dictionaries from separately compressed corpora
should **merge** so the merged corpus stays traversable. Small models
then read and write over this substrate — drafter-style block
comprehension — instead of characters, while the data stays extrinsic
and rapidly accessible.

## 2. What the committed tree already says (census run 2026-08-23, read-only)

A recurrence census over every `data/*/nodes.json` surface
(`statement_meaning` + `title`, 268,533 words across 12,777 nodes):

| measurement | value |
|---|---|
| words inside multi-word blocks recurring ≥ 32× | **88.5%** |
| greedy block encoding, dictionary of only **92** blocks | **3.9 words per emitted token** |
| ingested prose (12,515 meanings) distinct templates after slotting numerals/formulas | **5** |
| top-10 template coverage of ingested prose | **100.0%** |
| distinct `anonymized_template` values across 12,777 nodes | **11,904** |

Two poles, one lesson:

- **The prose layer is almost degenerate-recurrent.** Five templates
  generate all ingested meanings — because the seed scripts *did*
  generate them; `check_regeneration` proves the corpus byte-identical
  from its seeds every release. The corpus is already its own
  decompressor; what it lacks is the directed idea's substance: the
  latent template structure as a **first-class addressable format** —
  template id in high bits, slot fillers in low bits — instead of an
  accident of generation.
- **The formal layer's recurrence lives below whole statements.**
  11,904 distinct whole-statement templates means whole-statement
  blocks won't compress the math; but subterm recurrence is enormous
  and already measured — 6,884 statements host `x ^ 2`
  (`ownership`), 181k+ constituents in live decomposition, and the
  skeleton encoding measures **32.10×** against characters
  (`reports/compression.json`). The block dictionary's granularity
  must therefore be **per-layer**: whole-template for prose, subterm
  for terms.

And the repository's strongest prior result points the same
direction: the 2026-08 concept-token capstone measured canonical
concept tokens at **8.4×** compression over characters with *better*
out-of-distribution robustness, char arms at exact chance —
"parsing is the floor beneath which no gradient exists"
(`DESIGN-concept-tokens.md`, `experiments/ANALYSIS.md`). The directed
idea generalizes that measured result from formal terms to the whole
substrate, and makes the encoding double as the index.

## 3. What is genuinely new here (and what is not)

Not new, and must not be re-invented as if it were: byte-pair /
LZ-style dictionary induction over flat text is commodity; a 2^24
flat vocabulary is a tokenizer hyperparameter. The course should
refuse any version of this design that reduces to "train a bigger
BPE."

New, and worth a design:

1. **Ids with semantic bit fields.** High bits = namespace (corpus /
   language / realization space) or template id; low bits = slot
   filler or residual index; auxiliary bits = length, format,
   repetition. An id becomes an **address**: template × fillers = the
   node. Small-model consumption gets cheaper for exactly the reason
   the extrinsic-lexicon result predicted — embeddings can be
   *computed from the fields* (factorized: namespace embedding +
   filler embedding) instead of learned per-id, so the table stays
   small and the exact part stays outside the weights.
2. **Template tokens with typed slots**, aligned with the structure
   the kernel already owns (skeleton slots, not character offsets) —
   the v0.18 realization lexicon's operator↔words bijection is the
   smallest special case of this dictionary running in reverse.
3. **The dictionary as the index.** Every block id carries a posting
   list of statement ids; multi-word exact blocks are radically
   higher-precision retrieval keys than the single keywords the
   resolver fights its 0.030 false-positive floor with today. One
   artifact serves compression, retrieval, and rendering.
4. **Merge with identity.** Two corpora compressed separately merge
   by namespace bits plus a twin-resolution pass (the existing twin
   ledger IS the cross-namespace equivalence relation); the WOLD/
   WordNet lexicon (95.5% reach) is the cross-language sameness
   dimension the high bits were asked to carry.
5. **Self-expansion with a self-evaluation gate**, house-style: a
   block is promoted iff its recurrence clears a registered floor AND
   promotion strictly reduces total encoded size AND decode
   round-trips byte-identical. Promotion that fails any leg refuses.
   "Self-evaluated" means measured gates, not vibes.

## 3b. Runtime growth is the point, not a convenience

Clarified by the maintainer while this seed was being written, and
promoted here to a design constraint because it reorders the
priorities: **the corpora expand during runtime — more is added, and
what exists is not changed.** This system is not pretrained on world
knowledge — it consumes knowledge as it encounters it and learns
progressively; the self-expanding property is why the idea exists at
all. Additive growth on the corpus side is what makes the vocabulary
side clean: with neither statements nor ids ever mutating, there is
no invalidation problem anywhere in the design — only append, count,
promote. Consequences the course must treat as
requirements, not options:

- **Id stability under growth.** A vocabulary that re-tokenizes when
  it grows (retrained BPE reassigns every id) is disqualified by
  construction. Promotion is **append-only**: new blocks mint new ids
  inside their namespace; no existing id ever changes meaning. The
  structured bit fields make room for this natively — appending
  within a namespace is just the low bits counting up.
- **Promotion happens at write time.** The runtime ingestion path
  already exists and already has the right discipline: the WRITE
  gate stages PROVEN candidates with a declared
  `expected_matcher_delta` before measurement and refuses byte-drift.
  The dictionary extends the same pattern — a write carries its
  **expected vocabulary delta** (which blocks cross the promotion
  floor because of this statement), measured at the gate, receipted
  like everything else. Learning-by-encounter becomes: the statement
  lands in the graph, its recurrences land in the count ledger, and
  the ones that cross the registered floor become addressable — no
  gradient anywhere.
- **Regeneration discipline survives.** The reconciliation between
  "runtime-grown" and this repository's regeneration rule is an
  **append-only promotion ledger**: the dictionary's seed is its own
  event log, and replaying the log reproduces the dictionary
  byte-identically. `check_regeneration` gets one more artifact, not
  one exception.
- **The census is a snapshot, and says so.** §2's numbers describe
  today's tree; the design's gates must be stated over the ledger's
  replay (any prefix of history yields a valid dictionary), so the
  measured properties hold at every growth point, not just at the
  release that happened to measure them.

This is also the honest frame for the progressive-learning claim:
learning here is dictionary growth plus graph growth, both exact,
both receipted, immediately queryable — weights, when they appear at
all, only rank among licensed alternatives.

## 3c. Composition, and the criterion that decides how many templates

Directed follow-up (2026-08-23), recorded with its delegation: §2's
"five templates" is a snapshot of one generator's output, not a
design number — *the correct number should be based on what
effectively fits data*, and the id space could carry **composition
bits**: multiples, recursion, templates built from templates. The
maintainer leaves the determination to the design track explicitly —
the course is a relay where the idea is passed through several strong
readers who emerge with a better one — and this section is the first
pass.

**"What effectively fits data" has an exact name: minimum description
length.** The promotion gate's self-evaluation (§3, item 5) becomes
two-part MDL accounting: `total_bits = dictionary_bits +
encoded_corpus_bits`, and a candidate template (or block, or
composed rule) is admitted iff it strictly reduces the total. That
criterion answers the count question without anyone choosing a
number: five templates win only if a sixth costs more dictionary
than it saves in encoding — and it polices both failure directions
(under-templating leaves recurrence unpriced; over-templating turns
the dictionary into a copy of the corpus).

**Composition bits are grammar induction wearing an id format.** A
template whose slots accept *other template ids* — with a small depth
field — makes the dictionary a grammar, and admitting composed rules
under the same MDL gate is exactly what grammar-based compressors
(Re-Pair, SEQUITUR) do: promote the most valuable pair, recursively,
until promotion stops paying. The maintainer's "this is" → "this is
a" → "this is a test" chain is Re-Pair run at word granularity. For
the formal layer the composition grammar **already exists** — the
skeleton algebra is a recursive typed grammar over subterm ids — so
composition bits there mean addressing into it, not inventing a
second one.

**Why the neural mainstream stopped short of this (the directed
question, answered honestly).** BPE stops at subwords for reasons
that are real but contingent: a dense embedding table and softmax
scale with vocabulary size, and Zipf's law starves rare-token
gradients — a 2^24 *learned-per-id* table is untrainable, so vocabs
sit near 10^5 and stay subword so every token trains often enough.
The directed design dodges all three constraints at once, because
its ids are **not opaque**: embeddings can be computed from the bit
fields (namespace + template + filler — factorized, tiny tables),
which is the only regime where a 2^24 vocabulary is even coherent.
And models do not consume zstd streams because LZ77-family codes are
**position-dependent** — the same content gets different codes in
different windows, destroying the stable symbol→meaning mapping an
embedding requires. Compression optimizes bits; models need
referential stability. The design's append-only, stable-id
dictionary is precisely "a compressor whose codes are also symbols"
— LZ78/grammar-family, not LZ77 — and that, plus the posting-list
index and the exact/receipted corpus underneath, is the ground the
existing literature (large-vocab tokenizers, byte-latent patching,
speculative drafters) does not occupy.

The course inherits from this section: the MDL gate as the promotion
criterion; composition depth as a measured histogram, not a guess;
and the census script's successor must *induce* the dictionary under
MDL and report what the data chose.

## 3d. What the induction run measured (2026-08-23, `explore/v019-block-mdl`)

The §3c experiment ran (`scripts/measure_block_mdl.py` →
`experiments/block_mdl.json`, on its branch): Re-Pair with explicit
MDL accounting under three bit models, 19 tests, determinism and
byte-identical regeneration pinned. It corrected this design in five
places, and the corrections are binding on the course:

1. **MDL alone does not choose the count — the bit model does.**
   Under fixed-width codes the answer is quantized at power-of-two
   cliffs (the formal stream stopped dead at V=512, its rule count
   chosen by the code width, not the corpus). A named bit model is
   part of any preregistration, with the cliff flagged per arm.
   Measured counts: 186 rules (fixed-width, 1× dictionary price),
   94 (2× price), 80 (entropy-priced) — conclusions must survive the
   price doubling, and here they do (words/symbol moves 1%).
2. **The prefix-chain picture is not what MDL mints.** "this is" →
   "this is a" → "this is a test" describes left-extending
   successors; the criterion built balanced compositions ("this is" +
   "a test") and never minted the middle link. Composition is real
   (69 of 186 ids composed, depth ≤ 6 — a 3-bit depth field
   suffices); its shape is not the successor chain.
3. **The recurrence yield lives in the generator, which is the one
   place it does not count.** Split by authorship: the
   machine-generated ingested prose runs 10.47 words/symbol over 45
   word types; the 524 person-authored surfaces run **1.035** —
   essentially no block structure, ~4% over flat words. §2's 88.5%
   and both words-per-token figures measure one seed script's
   output. Every future denominator must name its population.
4. **The ratio headline is conceded to zstd, and the surviving claim
   is addressability — measured, and it is large.** zstd -19 beats
   the grammar 7.0× on the archive. But compressing the same
   surfaces as **separately addressable units** — the access pattern
   this design exists for — costs 6.25× MORE than the grammar even
   with a trained shared dictionary. The dictionary's value is being
   the corpus's *address space and index*, not its archive. The
   formal layer confirms §2's granularity split: a second flat
   grammar over operator tokens loses to zstd 3× and is not worth
   building — composition there addresses into the skeleton algebra
   that already exists.
5. **Runtime growth is lexical at the frontier, and
   path-independent.** The holdout increment minted 143 terminals
   against 12 rules — the write-gate's expected-vocabulary-delta is
   mostly new words, a cheaper object than §3b implied. And the
   grown dictionary came out **identical** to the monolithic one
   (both difference sets empty): growth here is not merely
   append-compatible but order-independent, a stronger property
   than §3b required and worth registering as a gate if the course
   adopts the design.

## 3e. What the address-space probe measured (2026-08-24, `explore/v019-address-probe`)

ROADMAP-v0.19 item 2 adopted this design bounded and scoped it to §4's
second bullet — *is the unified dictionary a real object, or two existing
objects wearing one id space?* — against three baselines taken from §4's
own falsifier list and **pre-registered in their own commit before any
measurement** (`experiments/address_space_probe_prereg.json`, ordering
asserted out of git by `tests/test_address_space_probe.py`). The probe ran
(`scripts/probe_address_space.py` → `experiments/address_space_probe.json`,
20 tests). **The answer is: two existing objects wearing one id space.**

| baseline (§4's own) | floor | measured | verdict |
|---|---:|---:|---|
| retrieval — the keyword channel | coverage 0.833 / FP 0.030 | **0.3256 / 0.2059** | **NOT BEATEN** |
| compression — zstd as an archive | 118,328 bits | 829,048 | **NOT BEATEN** (7.01×) |
| compression — zstd separately addressable | 5,182,024 bits | 829,048 | BEATEN (6.25×) |
| term layer — canon tokens | 8.44× (32.10× same-population) | **6.91×** | **NOT BEATEN** |

Four readings, and the first two are the ones that cost something.

1. **§3 item 3 is refuted as retrieval.** "Multi-word exact blocks are
   radically higher-precision retrieval keys than the single keywords the
   resolver fights its 0.030 false-positive floor with today" was built as
   a block channel and scored on the committed populations the floors were
   measured on. It is worse than the keyword channel on **both legs at
   once** — 0.3256 coverage against 0.9302, claiming 0.2059 of the authored
   refuse rows against 0.0294, same rows, same process. Under the keyword
   channel's own corroboration and convergence rules it reaches 0.0465.
   §3d correction 3 predicted this and the prereg registered the
   prediction: the blocks MDL mints are the generator's boilerplate, and
   boilerplate is the one thing a person never types.
2. **The addressability claim survives against scans and dies against a
   tag bit.** The unified id space touches 210,248× fewer bytes than
   grepping raw prose and 9,013× fewer than zstd-decompress-then-scan — and
   the prereg registered *in advance* that neither is evidence for
   unification, because both existing indexes already had it separately.
   The arm that isolates the variable is the same two indexes carrying
   **one tag bit** saying which owns the key. Against that, the unified
   space measures **0.9981** — very slightly *worse*, because merging 217
   block keys with 50,184 subterm skeleton keys grows the directory and
   buys one more binary-search probe. **What unification sells is dispatch,
   and a namespace bit already sells it cheaper.**
3. **The one baseline beaten is a restatement.** The addressable-zstd
   reading is arithmetic already published in `block_mdl.json`; the prereg
   registered it as such (E2) so it could not be read afterwards as this
   probe's finding.
4. **The cliff reproduced itself by accident.** A case-folded dictionary
   arm, added during construction because the keyword channel lowercases
   every query, merged terminals until `terminals + rules` landed on
   exactly 2048 = 2^11 and the fixed-width code refused every further
   mint — §3d correction 1, arrived at from a different direction. The arm
   is kept with `at_power_of_two_cliff` beside it.

**Disposition: the design parks with these numbers**, which is the rule
ROADMAP-v0.19 item 2 registered (*"Beat none of them and it parks with the
numbers"*) read as it was meant: of the two baselines that required this
probe to produce something new, both are NOT BEATEN. What is *not* parked
is the append-only, order-independent growth property §3d correction 5
measured, which no baseline here tested and which remains the strongest
uncontested thing this design has said.

Unpark needs a consumer that reads block ids for something the two
existing indexes cannot already do separately — §4's third bullet named
three candidates and this probe only built the first. It does not need
another retrieval arm.

## 4. Questions the course must answer before this becomes a preregistration

- **Fixed-width vs variable-length ids.** 2^24 fixed-width with
  semantic fields optimizes *access and comprehension*, not minimal
  bits — machine words, not gzip. Justify against a variable-length
  baseline or concede the compression-ratio headline to it and claim
  the index instead.
- **Where does the yield actually live?** The census says: prose
  compresses via ~100 blocks + 5 templates (already seed-derivable);
  terms compress via subterm ids (already skeleton-encoded). Is the
  unified dictionary a real object, or two existing objects wearing
  one id space? The honest answer may be "one id space IS the
  contribution" — addressability across layers — and the course
  should test that claim, not assume it.
- **Native consumption.** What concretely reads block ids: the
  resolver (block channel), the skin (block-id streaming as a vendor
  extension?), a small model (the drafter seat)? Each consumer needs
  its own capability-blind baseline; the small-model leg must clear
  the tool admission bar like every learned component.
- **The falsifier.** A blind baseline that must be beaten: for
  retrieval, the existing keyword channel at its measured floors; for
  compression, zstd-with-shared-dictionary over the same bytes; for
  the model leg, the same model over the canon token encoding already
  measured at 8.4×. If structured ids beat none of them, the design
  parks with the numbers.
- **Interaction with sans-template rendering (v0.18).** The realizer
  emits sentences from terms; the dictionary would store and address
  them. Sequencing matters: R0's parse-rate table (which terms are
  addressable at all) is input to any block-vocabulary denominator.

## 5. Non-claims of the seed

No neural component is proposed here — the maintainer's framing is
explicit that this is pre-neural substrate work; the drafter seat is
optional and bar-gated. No claim that this replaces the seeds or the
schema: the dictionary regenerates byte-identically from its
append-only promotion ledger (§3b), or it is nothing. No claim on v0.18's scope:
this seed waits for the v0.19 course by design, and the census above
is its evidence budget until then.
