# corollary-abstractions

Cross-discipline ontology of mathematical statements, a symbolic engine that
detects when different fields write the *same* formula ("structural twins"),
and an experiment suite showing that a **~2 MB neural model does genuinely
compositional language and math work** — provided everything with a closed
form (parsing, canonicalization, equality, the lexicon, structural
addresses) is computed *outside* the weights and handed to the model as an
interface. Latest release: [v0.5.0](docs/RELEASE-v0.5.0.md).

## Three headline demonstrations

**1. The matcher discovers that sciences repeat one another.** From 221
hand-authored statement nodes across 22 disciplines, structure alone:

```
$ python scripts/match_signatures.py
  skeleton: ?0:V = *(?1:P, ?2:V, ?3:V, inv(^(?4:V, 2)))
    - physics.gravitation.newton_universal_gravitation
    - physics.electromagnetism.coulombs_law
  skeleton: ?0:V = *(?1:P, EXP⟨*(?2:P, ?3:V)⟩)   [CROSS-DISCIPLINE]
    - calculus.growth.exponential_growth_law
    - chemistry.kinetics.first_order_integrated_rate_law
    - economics.finance.continuous_compounding
    - economics.finance.present_value_continuous
```

Coulomb's law *is* gravitation; compound interest, population growth, and
radioactive decay are one exponential family (the sign is a convention the
family-level matcher absorbs); the laws of logic and of sets are one Boolean
algebra, twin by twin. `scripts/specialize.py` goes further: the quantity
theory of money (`M·V = P·Q`) is the ideal gas law with its dimensional
constant suppressed — found mechanically, with the binding
`MONEY→PRESSURE, VELOCITY→VOLUME, PRICE_LEVEL→AMOUNT`.

**2. A tiny model answers foreign-language questions — and exact code makes
the answer fluent.** Two invented languages (different vocabularies, word
orders, question particles). The model gets a language-B question and three
language-A statements, and points at the answer; symbolic code parses,
canonicalizes, and renders it in either language:

```
$ cd experiments && python demo_answer.py
QUESTION (language B): wo chadult renmiz ka        # "who fears the fox?"
KNOWLEDGE (language A):
  - the quite clever wolf fears the wolf
  - the loud fox fears the teacher
  - the brave teacher fears the fox
MODEL POINTS AT: +( wolf MOD( clever quite ) )   [correct]
REALIZED (A): the quite clever wolf
REALIZED (B): chadult pomonb shikav
```

No learned decoder exists anywhere in that pipeline: every output word is
either pointed-at by the model or produced by exact code, so surface
hallucination is structurally impossible. First run self-bootstraps
(generates data, trains the ~800k-param pointer, ~4 min on GPU).

**3. One verified loop runs a proof and a story — then asks back.** The v0.5
controller uses the same typed state/action/branch protocol for three
authenticated Lean transitions and a three-beat golden-chicken story. The story
executor enforces scoped premises, Chekhov setup/payoff obligations, and
no-deus heralding. A second-turn demo pauses on a frame-private UNKNOWN, accepts
a signed user reply, and resumes without promoting that testimony into world
truth:

```console
$ python scripts/oracle_controller_demo.py
LEAN TRANSITION REPLAY: solved
GOLDEN CHICKEN: solved

$ python scripts/conversation.py
SYSTEM: What value should fill 'egg_color' for the golden chicken's eggs color?
USER: silver
SYSTEM: ... Now the golden chicken laid silver eggs.
```

`scripts/theory_of_mind.py` derives Sally's false belief from event visibility:
Sally answers basket while the world answers box. These are controlled symbolic
demonstrations, not yet an open-language learned policy.

## The models

Four small architectures, one shared recipe: a **4-layer pre-norm
Transformer encoder** (d_model=128, 4 heads, feed-forward 512, dropout
0.1) with task-specific heads. No pretrained weights anywhere; every
model trains from scratch in minutes on one consumer GPU.

| class | file | structure | params | used for |
|---|---|---|---|---|
| `TinyTransformer` | `experiments/train.py` | 4-layer encoder + CLS-pool MLP pair-classifier head | ~0.88M | twins / equiv / xlang / qa / syn / realsyn |
| `SpanPointer` | `experiments/train_span.py` | 4-layer encoder + per-position start/end span head | 0.82–0.91M (by positional variant) | solve-for-X answering; the demo checkpoint |
| `TreeSeq2Seq` | `experiments/train_gen.py` | 4-layer encoder + 2-layer autoregressive decoder | ~1.45M | the failed naive generator (kept as the negative result) |
| `PointerGen` / `AnalogyPointer` | `experiments/train_pgen.py`, `train_analogy.py` | 4-layer encoder + 2-layer decoder with pointer head and grounded copy embeddings | ~1.47M | generation-by-pointing; analogy completion |

Positional encoding is a first-class experimental variable, not a fixed
choice: absolute learned positions, tree-path addresses (per-level
table), sinusoidal level codes, and recurrent path composition (one
shared GRU cell walking each path) are selectable variants — the
positional ladder results in ANALYSIS.md come from exactly these
switches. The scaling grid varies encoder width 32–256 at fixed depth.

At fp32 these are 1.8–6.0 MB of weights (fp16 halves that at zero
accuracy cost — see the quantization ladder). Twenty-two claim-bearing
checkpoints ship across releases v0.3–v0.5. The smallness is the thesis: every
exact operation lives outside the weights, so the weights only carry
the graded residual.

## Measured findings (full narrative: `experiments/ANALYSIS.md`)

| finding | evidence |
|---|---|
| Parsing is the floor | raw-character models sit at exact chance on cross-language tasks — no gradient exists below the parse |
| Exact operations stay symbolic | learned equality tops out ~0.71 where the symbolic check is free and perfect |
| The lexicon lives outside the weights | weight-induced lexica reach ⅔ of ceiling in-distribution and collapse to chance OOD; the same lexicon supplied symbolically loses nothing |
| Composition needs addresses | with tree-path positions, held-out verb×noun combinations answer at 1.000 (both seeds); with learned positions the same model cannot even fit seen data |
| Scale does not buy generalization | across 8× width and 10× data, depth-OOD under learned positions is flat (~0.05–0.19); with symbolic addresses it is ≥0.95 in every cell, including 32-wide on 5k examples |
| Exposure does not generalize; iteration does | curriculum moved the depth cliff without removing it (0.006 OOD); a shared recurrent cell is the only mechanism to extrapolate, now honestly 0.16±0.07 across two seeds |
| Masked structure stabilizes, but does not solve depth | trained-depth-only masked-skeleton pretraining narrows recurrent seed spread 0.139→0.029; at n=2 it cannot claim a mean lift |
| Frames make local truth executable | one executor handles fictional premises, temporal obligations, owned belief, visibility-derived false belief, and nested models without leaking them into world truth |
| Retrieval does not promote its results | exact/neighborhood retrieval and POINT are receipt-bound; returned items retain their epistemic status, and misses ASK or abstain |
| Creating = pointing + realization | both learned decoders failed informatively (memorize, can't copy); pointing plus closed-form realization generates perfectly for any answer present in the input |

Two retractions are part of the record (a too-easy test caught by external
audit; a mid-run misreading) — see ANALYSIS.md. House rule: every split
must survive a capability-blind symbolic baseline, and no single-seed
comparison is trusted.

## Repository layout

```
schema/                 Mathematical Statement Node JSON schema
data/<discipline>/      statement corpora (22 disciplines, 221 nodes)
scripts/
  validate_nodes.py     schema + link-reciprocity validation (merged graph)
  match_signatures.py   twins plus a separate time-reversal mirror relation
  specialize.py         general->specific edges (absorption + identities)
  decompose.py          statements as constructs of named forms + groundedness
  compose_assert.py     global ladder + live frame-local executor statuses
  controller.py         shared v0.5 state/action/verifier loop
  retrieval.py          UNKNOWN -> five-store (+ optional WordNet) RETRIEVE
  wordnet_store.py      external OEWN JSON -> empirical lexical graph
  wordnet_eval.py       P-CF6 held-out synonym-bridge control
  conversation.py       ASK -> WAITING -> signed user reply -> resumed binding
  theory_of_mind.py     visibility-derived Sally-Anne false-belief control
  oracle_controller_demo.py  oracle proof-replay + golden-chicken baseline
  measure_compression.py concept-token compression (10.7x on the real corpus)
  seed_<discipline>.py  corpus generators (the authoring pattern)
experiments/
  exprgen / langgen / qagen / syngen / solvex2   synthetic-world generators
  train.py / train_span.py / train_gen.py / train_pgen.py   trainers
  pretrain_maskskel.py  masked-node pointer pretraining for analogy
  demo_analogy_checkpoint.py  released model on fresh shallow + deep analogies
  demo_answer.py        the end-to-end demo above (self-bootstrapping)
  run_grid.py           scaling-curve grid
  ANALYSIS.md           every result, prediction, and retraction
  data_real/            (gitignored) licensed corpus samples, user-supplied
prover/                 phase-gated Lean prover roadmap (see README there)
docs/                   design docs, release notes, BACKLOG
reports/                generated twin/specialization ledgers (committed)
```

## Setup & reproduce

Corpus tools need only Python 3.11+ (`pip install jsonschema` for full
schema checks). Experiments need the local venv:

```
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe torch numpy --index-url https://download.pytorch.org/whl/cu130
uv pip install --python .venv/Scripts/python.exe jsonschema
```

Everything headline is deterministic from committed seeds — no external
data required (the `experiments/data_real/` samples feed only auxiliary
profiling and are never committed):

```
python scripts/validate_nodes.py            # 221 nodes / 22 corpora green
python scripts/match_signatures.py          # twin ledger
python scripts/specialize.py                # specialization edges
python scripts/oracle_controller_demo.py    # one loop: 3 Lean replays + 3 story beats
python scripts/retrieval.py                 # exact five-store lookup then POINT
python scripts/retrieval.py quickening --wordnet C:\path\to\english-wordnet-2025-json.zip
python scripts/wordnet_eval.py C:\path\to\english-wordnet-2025-json.zip
python scripts/conversation.py              # two-turn golden-chicken clarification
python scripts/theory_of_mind.py            # Sally looks in basket; world says box
python -m unittest discover -s tests -v     # controller contracts + vacuity checks
cd experiments
python demo_answer.py                       # the demo (self-bootstraps)
python solvex2.py --out-dir data            # regenerate any dataset
python train_span.py --arm struct --task-prefix solvex2 --positions tree \
    --data-dir data --out results/repro.json   # re-verify the 1.000 result

# after: gh release download v0.5.0 --pattern \
#   analogy-masked-skeleton-warm-s0.pt --dir results
python demo_analogy_checkpoint.py --checkpoint \
    results/analogy-masked-skeleton-warm-s0.pt  # fresh shallow + deep examples
```

On Windows consoles set `PYTHONIOENCODING=utf-8` for the matcher scripts
(skeleton output uses `⟨⟩`).

## Design documents

- `docs/DESIGN-concept-tokens.md` — the model vision: concept vocabulary,
  extrinsic lexicon, composite tokens; milestone status updated per results
- `docs/DESIGN-linguistic-twins.md` — grammar as another discipline corpus:
  modifiers as recursive operators, questions as equations, languages as
  twins of one interlingua
- `docs/DESIGN-epistemic-ladder.md` — seven epistemic rungs, each with a
  closed form; status is symbolic, never learned
- `docs/DESIGN-frames-and-retrieval.md` — fiction as scoped premises;
  retrieval as an UNKNOWN-triggered action
- `docs/DESIGN-cognitive-frames.md` — theory of mind, reference frames,
  relational frames, provability, masked structure, and WordNet
- `docs/DESIGN-visual-structure.md` — the parse-first multimodal plan:
  formula/diagram twins, SVG structure, and a pixel control
- `docs/blog/` — accessible project narratives, including the v0.5 story
- `docs/RELEASE-v*.md` — release notes; highest version is current
- `docs/DISCOVERIES.md` — the human-readable findings ledger
- `docs/BACKLOG.md` — recorded friction, each item with its evidence
