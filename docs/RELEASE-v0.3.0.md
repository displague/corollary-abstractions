# v0.3.0 — Grounded composition and the epistemic ladder

Baseline: [v0.2.0](RELEASE-v0.2.0.md). Plan of record:
[ROADMAP-v0.3.md](ROADMAP-v0.3.md); carried items now live in
[ROADMAP-v0.4.md](ROADMAP-v0.4.md). Findings ledger:
[DISCOVERIES.md](DISCOVERIES.md).

## Roadmap triage

**Shipped — grounded sentence composition (roadmap #2).**
`scripts/compose_assert.py` composes English assertions and labels every
sentence by a closed-form epistemic verdict, all six tiers in one run:
PROVEN (quoting its Lean theorems), VERIFIED (family provenance
attached), HYPOTHESIS ("structurally admissible; empirically
unestablished"), UNKNOWN (a hole presented as an answerable question),
REFUTED (contradiction cited against a machine-checked law), REFUSED
("a claim without a known form is a shape, not a statement").
Hallucination control by construction. The model-in-the-loop selection
half carries to v0.4.

**Shipped as a measured negative — the analogy depth wall (roadmap #3).**
Non-extractive creation *composes*: 1.000/0.9998 exact on held-out
transform×skeleton combinations, structures existing nowhere in the
input, ~1.5M params. Depth does not transfer, and three positional
mechanisms (absolute, decoder tree-coordinates, tied path embeddings)
fail on a **bit-identical** set of 2416/2450 OOD examples — positional
encoding is ruled out entirely; length was ruled out separately (95.4%
of failures are within trained lengths). The per-step diagnostic
carries to v0.4.

**Carried (not started): corpus-grounded analogy, prover phase 2,
attunement curves** — all in ROADMAP-v0.4 with their designs intact.

## Shipped beyond the roadmap

- **The epistemic ladder** (`docs/DESIGN-epistemic-ladder.md`): six
  concepts — unknowns, disorder, conjecture, truth/provable, drift,
  falsehood — as one ladder whose every rung has a closed form. Status
  is symbolic, never learned; weights own one graded judgment: which
  conjectures are worth proposing. Schema gains `conjectured` and
  `verified_by`; 9 logic laws now link to all 16 machine-checked Lean
  theorems with a regeneration-failing drift check; ex falso, reductio,
  and ∅-minimality authored (the twin honestly *declined* — the
  alternate reading that would manufacture it is recorded, not taken).
- **Derivational composition** (`scripts/decompose.py`): every
  statement read as a construct of named forms — 167/195 decompose,
  141 contain a constituent that IS another statement's expression
  side, each with a groundedness score (disorder graded, not gated).
  The SSM update reads out as two scaled-linear constituents; Newton's
  correction term is a rate.
- **Corpus 137 → 195 nodes, 15 → 21 disciplines** (machine learning,
  numerical analysis, graph theory, geometric modeling, temporal logic,
  narrative). Registered-prediction highlights, adjudicated by the
  matcher: **GRPO's advantage is the z-score** (emergent typed twin);
  **gradient descent is Euler's method**; the trapezoidal rule is the
  trapezoid area formula; softmax sampling joins the exponential-decay
  family; regression generalizes the Mamba state update; affine
  location-scale generalizes LoRA; **time joins the order structures**
  (precedence ≅ subset ≅ containment transitivity); **fiction obeys
  logic** (narrative frame-consistency ≅ the machine-checked complement
  laws). Deep refusals on the record: idempotence vs involution differ
  by a fixed point; the type system isolates exactly what xLSTM's
  gating added.
- **Frames and retrieval-as-action** (`docs/DESIGN-frames-and-retrieval.md`):
  fiction as scoped falsehood-as-premise with the ladder running over a
  frame-local corpus; retrieval as the third action type with the
  UNKNOWN rung as its trigger and honest abstention on miss.
- **Compression at scale**: concept encoding now 10.73× vs characters
  on the real 195-node corpus (8.44× at 67 nodes) — reuse amortization
  arriving as predicted.
- **Release machinery**: this release is the first cut by the
  `release` skill, including the roadmap→release→next-roadmap rotation
  and model checkpoints as GitHub release assets.

## Resolved from BACKLOG this cycle

- Atomic statements previously fell off the groundedness ladder
  entirely (found via ex falso); now graded by their root.
- The prover→ontology bridge (`verified_by`) closed the recorded
  truth-vs-provable gap.

## Honest limits carried forward

The analogy depth wall (diagnosis pending, mechanisms eliminated);
chained composition unbuilt (the v0.4 thesis); head literalism
quarantining new-vocabulary corpora (ten two-argument heads, one shape,
zero groups); `specialize.py`'s rel-only guard excluding all 16
inference-rule nodes (found by probe); groundedness pathologies
(recursive definitions grade 0.0; an instance can grade below its
pattern); no schema scope construct for frames; single-seed scaling
cells remain trend-only claims.

## Assets (13 checkpoints — every claim-bearing trained model)

- `solvex2_demo.pt` — the span pointer behind the 1.000/0.69 extractive-
  answering result and `demo_answer.py` (embeds vocab + config; the repo's
  committed seeds supply the data).
- `twins_{char,struct,canon}.pt`, `equiv_{char,struct,canon}.pt` — the
  milestone-3 A/B/C suite; `twins_canon.pt` and `equiv_struct.pt` are also
  the quantization ladder's inputs (fp16-free / int8 results).
- `xlang_{char,struct,canon}.pt`, `qa_{char,struct,canon}.pt` — the
  cross-language twin and QA-as-unification classifiers.

Seed-reproducible only (no checkpoint was saved — trainers predated
`--save-model`): the analogy 1.000 composition result and the syn/hybrid
runs. Regenerate via the committed generators and trainers; saving
checkpoints by default is on ROADMAP-v0.4's tooling list.
