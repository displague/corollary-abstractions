# DESIGN: corpus scale and programming — where the effort goes after v0.8

Status: staging document for v0.9 and beyond. Written at the v0.8 release. It
records a deliberate change of emphasis, argued honestly, and it is the design
the v0.8 blog's closing section points to.

## The claim this document makes

Through v0.8 the project's limiting factor was **method**: could a tiny residual
model do compositional work if every closed form — parsing, canonicalization,
equality, the lexicon, structural addresses, verification — was computed outside
the weights and handed to it as an interface? Eight releases answered yes, and
answered it with unusual hygiene: every claim is forced to beat a capability-blind
baseline, negative results are first-class, and every trust boundary is
adversarially reviewed before it merges.

That question is now substantially answered. The limiting factor is no longer
method. It is the **scale and external relevance of the knowledge graph.** The
matcher, the specialization graph, the decomposition ladder, the proof-search
neighborhood, the analogy splits, the durable conversations, and the visual oracle
are all real and carefully measured — but they live inside a closed world of
**221 hand-authored nodes across 22 disciplines** that the author fully controls.
The moment the system meets an uncontrolled, larger, messier formal or
semi-formal body of knowledge, most of the current numbers become unknown. 221
hand-authored nodes cannot carry the thesis, and hand-authoring does not scale.

So the majority of effort now turns to two moves. Everything else in the backlog
is secondary until these two move.

## Move 1 — Make the corpus non-toy, by ingestion

**The authoring pattern is already the ingestion pattern.** A corpus is a
`seed_*.py` that emits statement nodes validated against the schema; the matcher,
specializer, and decomposer consume the generated `nodes.json`. Nothing about that
pipeline requires a human to *invent* each node. It requires a human (or a script)
to put a statement into the canonical form the schema demands. That is an
ingestion problem, not an authoring problem.

Candidate sources, roughly in order of how cleanly they map onto a Mathematical
Statement Node with a `verified_by` theorem:

- **miniF2F-style problem sets** — competition problems already formalized in
  Lean/Isabelle, small and clean, a natural first ingestion target that also
  connects directly to the existing proof-search lane.
- **Mathlib theorems** — a very large body of Lean statements; the subset whose
  goal is expressible in the corpus template grammar becomes nodes with real
  `verified_by` links, and the rest stretch the grammar honestly (each
  untranslatable form is a *finding* about the grammar's reach, exactly as v0.7's
  correspondence rung already treats them).
- **arXiv statements with existing Lean/Isabelle proofs** — formalized results
  that carry their own external verification.
- **A cleaned ProofWiki extract** — semi-formal but structured, a bridge between
  the fully-formal sources and natural mathematical prose.

**What this stresses, and why that is the point.** Thousands, then tens of
thousands, of nodes is where the structural-twin claim, the specialization graph,
and the residual-learning claims become interesting *outside the lab*. A blind
baseline that wins on 221 curated nodes may or may not win on 20,000 ingested ones
— and finding out is the whole game. Ingestion also breaks the closed world in the
ways that matter: duplicate and near-duplicate statements, inconsistent notation,
statements whose canonical form the grammar cannot yet express, and twin groups the
author did not hand-pick. Each of those is a real measurement the current corpus
cannot produce.

**The disciplines that must survive ingestion.** Ingestion may not launder
provenance. The existing rules are load-bearing precisely here:

- WordNet and any lexical/semi-formal source enters at `empirical`, never grounds
  a frame verdict, never appears in `verified_by`.
- A `verified_by` link is only as good as the correspondence rung that checks it
  (v0.7 item 3): an ingested theorem must correspond to the statement citing it,
  structurally, or the link is UNTRANSLATABLE/MISMATCH — never asserted.
- No runtime path writes `data/*/nodes.json`; ingested nodes are produced by a
  seed and regenerated, and — with v0.8's PROVEN-WRITE acceptance path — a cleared
  ingested candidate can be *applied* through the audited seed→regenerate→receipt
  route rather than hand-edited.
- Every ingestion run is reproducible: a fixed source snapshot (by digest) and a
  deterministic transform, so `check_regeneration` still holds byte-for-byte.

The near-term open problem is the **template grammar's reach**: how much of Mathlib
maps onto the corpus's MEET/JOIN/NEG/IMPLIES-over-slots grammar without dilution.
That is measured, not assumed; the honest first deliverable is a *coverage number*
— what fraction of a source ingests cleanly, and what the untranslatable remainder
looks like — before any claim about scale.

## Move 2 — Programming as a first-class discipline

The architecture is almost perfectly set up for code, and code is the clearest
route to a capability an outsider immediately understands and can test.

The mapping is the one the system already runs for physics and economics formulas,
with the verifier swapped:

```
source formula  : text -> parse -> canonical form -> structural address -> pointer residual -> Lean/algebra verifier
source program  : AST  -> canonical form           -> structural address -> pointer residual -> external verifier
                                                                                                  (Lean for properties,
                                                                                                   Z3 for SMT,
                                                                                                   or type-checker + unit tests)
```

A verified code snippet — a function with a property proof, an SMT-checkable
contract, or simply a typed signature plus passing unit tests — becomes another set
of nodes. Then the operations the system already performs acquire new meaning
without new machinery:

- **structural twins** across code: "find the algorithm structurally identical to
  this one in another language or another library" is the same head-algebra match
  the matcher runs over formulas.
- **specialization** over code: the cheapest-derivation graph relates a general
  routine to its specializations exactly as it relates a general theorem to its
  instances.
- **synthesis and debugging** become propose→verify→repeat over the same
  controller, with the external verifier (type-checker + tests, or Z3, or Lean) as
  the transition authority — the role live Lean already plays for the proof curve.

This also gives the corpus a natural, effectively unbounded growth path — GitHub
plus formal-verification tooling — which feeds back into Move 1.

## Guardrails (non-negotiable, carried from the whole project)

1. **Ship the open harness, then stop expanding surface area until it is
   load-bearing.** v0.8 opened unrestricted prose authoring; the first job is to
   let it actually drive the system (real users, or the author less constrained),
   not to add more surfaces.
2. **Hybrid only at the edges, never in the core.** A larger language model is fine
   as a *proposal generator* or a *fluent front-end* — but it must be filtered
   through the same closed-form interfaces and the same verifiers. The moment a
   large model owns structure or equality, the project has become a RAG+LLM wrapper
   with extra steps, and the thesis is gone. The tiny residual + symbolic
   everything-else is the interesting claim; do not dilute it.
3. **Keep the brutal internal baseline discipline, and add an external one.** Every
   claim still beats a capability-blind baseline internally. What is missing is an
   external, independently interesting benchmark the system can win *because of* the
   architecture, not in spite of a small corpus — e.g. structural-analogy recovery
   across formalized scientific papers, or verified code completion on a held-out
   library with formal specs. Such a benchmark forces the corpus to grow and gives
   outsiders a reason to care.
4. **No external LLM-benchmark comparison until the contract is honest.** Unchanged.
   The open harness earns the first half (the system accepts open requests); the
   benchmark's input/output contract must map onto the capability actually built
   before any comparison is licensed.

## What we deliberately would NOT do next

- Keep expanding the physics / affect / oscillation / visual rungs while the core
  graph is 221 nodes. They are elegant, but they are demonstrations inside the same
  closed world; they wait.
- Train more tiny models on the current data hoping for a breakthrough. The
  ceilings already say the residual on this distribution is small; more parameters
  on the same distribution will not change that. (v0.8's analogy model arm is the
  latest confirmation.)
- Chase general LLM fluency scores. A different game, correctly declined until the
  contract is honest.

## Staging into v0.9

v0.9's headline becomes Moves 1 and 2, with the open harness and the WRITE
acceptance path (both delivered in v0.8) as the *earned foundation* that makes them
tractable: the harness can drive ingestion and code sessions, and PROVEN-WRITE can
apply an ingested or synthesized node through an audited, reversible route. The
open lanes v0.8 did not reach — proof-search depth, the groundedness gate, the
existing-multi-corpus WRITE patch — carry forward, but re-scoped as *what a
non-toy corpus needs*, not as ends in themselves. The first honest deliverables are
coverage numbers: what fraction of a real formal source ingests cleanly, and what a
verified-code node looks like end-to-end through the existing pipeline.
