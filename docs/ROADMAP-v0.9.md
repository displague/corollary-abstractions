# v0.9 roadmap — scale and code: break the closed world

v0.8 closed the lanes v0.7 left open and opened the one it deferred: the
interactive harness can now author unrestricted prose, and PROVEN-WRITE can apply
a change through an audited, reversible route. Method is substantially answered.
The limiting factor is now the **scale and external relevance of the knowledge
graph** — still 221 hand-authored nodes. v0.9 makes closing that the headline. The
argument is in [DESIGN-corpus-scale-and-programming.md](DESIGN-corpus-scale-and-programming.md);
this roadmap stages it.

The two delivered v0.8 capabilities are the **earned foundation**: the open harness
can drive ingestion and code sessions, and PROVEN-WRITE can apply an ingested or
synthesized node without hand-editing `data/`. Everything below leans on them.

The benchmark rule is unchanged and binds harder as the corpus grows: no external
LLM-benchmark comparison until the system accepts open requests *and* the
benchmark's input/output contract maps honestly onto the capability built.

## 1. Make the corpus non-toy, by ingestion (headline)

Hand-authoring does not scale; the `seed_*.py` + schema pattern is already an
ingestion pipeline. Turn it toward real verified sources.

- Ingest a first real source — miniF2F-style formalized problems and/or a Mathlib
  subset whose goals express in the corpus grammar — as statement nodes with real
  `verified_by` links, from a **digest-pinned source snapshot** and a
  **deterministic transform**, so `check_regeneration` still holds byte-for-byte.
- Report a **coverage number** before any scale claim: what fraction of the source
  ingests cleanly, and what the untranslatable remainder looks like (each
  untranslatable form is a finding about the grammar's reach, scored like v0.7's
  correspondence rung — never asserted).
- Preserve every provenance discipline through ingestion: lexical/semi-formal
  sources enter at `empirical`, never ground a frame verdict, never appear in
  `verified_by`; ingested nodes are applied via PROVEN-WRITE's seed→regenerate→
  receipt route, not hand-edited.
- Re-run the structural-twin, specialization, and decomposition ledgers on the
  enlarged graph and report what moves — especially whether any capability-blind
  baseline that won on 221 curated nodes still wins on thousands of ingested ones.

Acceptance: a real verified source ingested to a materially larger node count (or
an honest coverage measurement if the grammar's reach is the bottleneck), with
provenance intact, reproducible byte-for-byte, and the twin/specialization ledgers
recomputed and reported.

## 2. Programming as a first-class discipline (headline)

The architecture runs the same operations over code that it runs over formulas,
with the verifier swapped.

- Land the pipeline for a first code discipline: AST → canonical form → structural
  address → pointer residual → **external verifier** (a type-checker + unit tests
  to start; Z3 for SMT contracts, or Lean for properties, as follow-ons). A
  verified code snippet becomes a set of nodes.
- Demonstrate the existing operations acquiring code meaning with no new machinery:
  structural-twin recovery across code (same-algorithm, different surface),
  specialization over routines, and propose→verify→repeat synthesis/debugging with
  the external verifier as the transition authority (the role live Lean plays for
  the proof curve).
- Keep the honesty boundary: a passing type-check + tests certifies what it checks,
  not correctness in general; a property proof certifies the property.

Acceptance: one verified-code node type end-to-end through the pipeline, one
structural-twin-over-code result against a capability-blind baseline, and one
synthesis-or-debug transaction adjudicated by an external verifier.

## 3. Drive the open harness on real sessions

v0.8 built the open surface; v0.9 makes it load-bearing rather than expanding it.

- Drive at least one real ingestion or code session end-to-end through the harness
  (boot matrix → need dispatch → open authoring/WRITE), degrading to ASK where the
  request is unparseable, never guessing.
- Expand request parsing only as a real session demands it; do not add new surfaces
  (web skin, tool plugins) until the TTY surface is genuinely used.

Acceptance: one real, non-trivial session recorded end-to-end that produces or
revises a node through the audited route, with the ASK-not-guess contract holding.

## 4. An external benchmark the architecture can win because of its design

The missing piece is external relevance.

- Design one external, independently interesting benchmark the system can win
  *because of* the architecture, not in spite of a small corpus — e.g.
  structural-analogy recovery across formalized scientific papers, or verified code
  completion on a held-out library with formal specs.
- The benchmark must force the corpus to grow (it depends on items 1/2) and must
  map its input/output contract honestly onto the built capability before any
  comparison is licensed.

Acceptance: a benchmark specification with a capability-blind baseline and a first
measurement — a loss or tie is valid, as always.

## 5. Carried-open lanes, re-scoped as what a non-toy corpus needs

The open lanes v0.7/v0.8 did not reach carry forward, but re-scoped as means to
items 1–2 rather than ends:

- **Proof-search curve depth** (v0.8 item 3): now naturally fed by an ingested
  theorem set larger than 24; run against the triples' own toolchain, with a
  cross-run dead-branch ledger, and re-ask whether a learned order can beat the
  blind one at scale.
- **Existing-multi-corpus WRITE patch** (v0.8 item 4 remainder): the seed-aware
  declarative patch so an ingested edit can touch a co-owned seed without orphaning
  a corpus — a prerequisite for ingesting into existing disciplines.
- **The groundedness gate** (v0.8 item 7): argued against the conservative lower
  bound, now on the enlarged graph where the channel split is no longer near-vacuous.

## 6. Deliberately parked until the core graph is non-toy

Tracked, not worked, per the design doc: the physics / affect / oscillation /
frequency-domain / rotation rungs and the visual parsed-vector/raster arms. They
are elegant, but they are demonstrations inside the same closed world; they wait
until items 1–2 have moved.

## 7. Governance carries forward

- Every claim beats a capability-blind baseline; negatives are first-class.
- Independent adversarial review at every trust boundary — now including the
  ingestion transform and the code verifier boundary.
- Register predictions before adjudication; attach corrections rather than edit.
- **Hybrid only at the edges:** a larger model may propose or front-end, but never
  own structure or equality. The moment it does, the thesis is gone.
- No external LLM-benchmark comparison until item 3's contract is earned and item
  4's contract maps honestly.

## Release gate

v0.9 is ready only if it contains:

- a real verified source ingested to a materially larger corpus (or an honest
  grammar-coverage measurement), reproducible byte-for-byte, provenance intact;
- one verified-code node type end-to-end with an external verifier, and one
  structural-twin-over-code result against a blind baseline;
- one real end-to-end harness session that produces or revises a node through the
  audited route;
- the twin/specialization/decomposition ledgers recomputed on the enlarged graph
  and reported;
- updated assets whose notes explain winners, losers, and controls;
- the complete seed/schema/matcher/specializer/decomposer/test suite green.
