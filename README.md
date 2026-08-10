# corollary-abstractions

Cross-discipline ontology of mathematical statements, a symbolic engine that
detects when different fields write the *same* formula ("structural twins"),
and an experiment suite showing that a **~2 MB neural model does genuinely
compositional language and math work** — provided everything with a closed
form (parsing, canonicalization, equality, the lexicon, structural
addresses) is computed *outside* the weights and handed to the model as an
interface. Latest release: [v0.6.0](docs/RELEASE-v0.6.0.md).

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
    - ml.policy.boltzmann_softmax_policy
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

**3. One verified loop searches a live proof and maintains a private story
revision.** The controller now asks Lean to apply tactics live and backtracks
from an accepted dead branch. The conversation runtime keeps Alice's and Bob's
egg-color revisions separate over one public golden-chicken story; Alice can
later supersede silver with copper without promoting any preference into world
truth:

```console
# This first command additionally needs PyPantograph + Lean; see the note
# immediately below this block.
$ python prover/live_search.py
blind palette: solved; nodes=9 ... proposals=86 ...
projection ablation: exhausted; nodes=10 ... proposals=80 ...

$ python scripts/conversation.py
SYSTEM/ALICE: ... Now the golden chicken laid silver eggs.
SYSTEM/BOB: ... Now the golden chicken laid blue eggs.
SYSTEM/ALICE: ... Now the golden chicken laid copper eggs.
```

`scripts/theory_of_mind.py` derives Sally's false belief from event visibility:
Sally answers basket while the world answers box. Separate all-data tactic
ranker checkpoints are also shipped, but their mean live search uses 65
proposals versus 64 for a state-blind frequency order. The architecture's
0.8125 theorem-heldout score comes from separately trained evaluation models,
not those live checkpoints. These are controlled results, not yet an
open-language or general proof policy.

Live proof search requires PyPantograph 0.3.15 and the matching Lean toolchain;
follow [`prover/FEASIBILITY.md`](prover/FEASIBILITY.md). The conversation and
theory-of-mind demos require only the ordinary project environment.

## The models

Five small architectures. Four share a **4-layer pre-norm Transformer
encoder** (d_model=128, 4 heads, feed-forward 512, dropout 0.1) with
task-specific heads; `TacticRanker` instead uses one shared byte-level GRU.
No pretrained weights anywhere; every model trains from scratch on one
consumer GPU.

| class | file | structure | params | used for |
|---|---|---|---|---|
| `TinyTransformer` | `experiments/train.py` | 4-layer encoder + CLS-pool MLP pair-classifier head | ~0.88M | twins / equiv / xlang / qa / syn / realsyn |
| `SpanPointer` | `experiments/train_span.py` | 4-layer encoder + per-position start/end span head | 0.82–0.91M (by positional variant) | solve-for-X answering; the demo checkpoint |
| `TreeSeq2Seq` | `experiments/train_gen.py` | 4-layer encoder + 2-layer autoregressive decoder | ~1.45M | the failed naive generator (kept as the negative result) |
| `PointerGen` / `AnalogyPointer` | `experiments/train_pgen.py`, `train_analogy.py` | 4-layer encoder + 2-layer decoder with pointer head and grounded copy embeddings | ~1.47M base; 1.48–1.68M depth-consumer arms | generation-by-pointing; analogy completion and address-consumer ablations |
| `TacticRanker` | `experiments/train_tactic_policy.py` | byte embedding + one shared GRU + schema head | 27,688 | held-out Lean tactic ranking inside live verified search |

Positional encoding is a first-class experimental variable, not a fixed
choice: absolute learned positions, tree-path addresses (per-level
table), sinusoidal level codes, and recurrent path composition (one
shared GRU cell walking each path) are selectable variants — the
positional ladder results in ANALYSIS.md come from exactly these
switches. The scaling grid varies encoder width 32–256 at fixed depth.

The fp32 checkpoint files are roughly 0.11–6.8 MB. The earlier pointer-model
quantization ladder found fp16 halved its weight footprint without measured
accuracy loss; that result is not silently generalized to every newer
architecture. Claim-bearing checkpoints ship as release assets rather than in
git. The smallness is the thesis: every
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
| Live search makes dead ends real | Lean accepts `clear h`, but the branch destroys the only conjunction evidence; bounded search retains and abandons it before solving elsewhere |
| Learned classification is not search gain | theorem-heldout evaluation models score 0.8125; separate all-data live checkpoints average 65 proposals and lose to a 64-proposal state-blind frequency order |
| Private conversation needs revocation | Alice and Bob maintain divergent revisions over one story; authenticated supersession changes Alice's silver eggs to copper without changing world truth |
| Corpus grounding is not task difficulty | 40 grounded analogy rows reduce to five targets in one ratio family; symbolic and blind last-slot number transfer both score 1.000 |

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
                        and the executable miss chain (exact -> neighborhood
                        -> derivation -> tool -> ASK -> abstention)
  text_keys.py          closed-form key canon, token matching, overlap score
  observation_adapter.py  offline external source: a declared folder of JSON
                        observations, capped at the empirical rung
  wordnet_store.py      external OEWN JSON -> empirical lexical graph
  wordnet_eval.py       P-CF6 held-out synonym-bridge control
  conversation.py       ASK -> WAITING -> signed user reply -> resumed binding
  theory_of_mind.py     visibility-derived Sally-Anne false-belief control
  oracle_controller_demo.py  oracle proof-replay + golden-chicken baseline
  measure_compression.py concept-token compression (11.24x on the real corpus)
  seed_<discipline>.py  corpus generators (the authoring pattern)
experiments/
  exprgen / langgen / qagen / syngen / solvex2   synthetic-world generators
  train.py / train_span.py / train_gen.py / train_pgen.py   trainers
  pretrain_maskskel.py  masked-node pointer pretraining for analogy
  train_tactic_policy.py  27k-param Lean tactic ranker + live controls
  corpus_analogy.py     twin + specialization -> verified real quadruples
  demo_analogy_checkpoint.py  released model on fresh shallow + deep analogies
  demo_answer.py        the end-to-end demo above (self-bootstrapping)
  run_grid.py           scaling-curve grid
  visual/               the visual ground-truth oracle: deterministic SVG
                        renderer, stable-slot scene graph, controlled
                        near-miss generator, exact ablated verifier, parser
                        (no weights; the learned arms are still deferred)
  ANALYSIS.md           every result, prediction, and retraction
  data_real/            (gitignored) licensed corpus samples, user-supplied
prover/
  live_search.py        bounded PyPantograph search with real dead branches
  README.md             phase status, artifacts, and trust boundary
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
.\.venv\Scripts\Activate.ps1
```

Live Lean search has one additional native dependency boundary: PyPantograph
0.3.15 plus the matching Lean toolchain. They are not installed by the commands
above. Follow [`prover/FEASIBILITY.md`](prover/FEASIBILITY.md), then set the
`PYTHONPATH` and Lean-toolchain `Path` shown in [`prover/README.md`](prover/README.md)
before running `live_search.py` or `train_tactic_policy.py --live`.

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
python scripts/retrieval.py --chain "ALWAYS(IMPLIES(PLANTED(ELEMENT), EVENTUALLY(DISCHARGED(ELEMENT))))"
                                            # walks the miss chain: exact and
                                            # neighborhood miss, derivation answers
python scripts/retrieval.py --chain --observations path\to\notes note.tide_gauge_2026
python scripts/wordnet_eval.py C:\path\to\english-wordnet-2025-json.zip
python scripts/conversation.py              # two-turn golden-chicken clarification
python scripts/theory_of_mind.py            # Sally looks in basket; world says box
python prover/live_search.py                # live Lean search + projection ablation
python experiments/train_tactic_policy.py --live  # learned vs strong blind order
python experiments/corpus_analogy.py --out experiments/results/corpus_analogy_repro.json
                                             # grounded rows + trivial blind baseline
cd experiments && python -m visual.genvisual adjudicate --n 240 --seed 11
                                             # visual oracle: P-VO1..P-VO7
python -m unittest discover -s tests -v     # controller contracts + vacuity checks
cd experiments
python demo_answer.py                       # the demo (self-bootstraps)
python solvex2.py --out-dir data            # regenerate any dataset
python train_span.py --arm struct --task-prefix solvex2 --positions tree `
    --data-dir data --out results/repro.json   # re-verify the 1.000 result

# after: gh release download v0.6.0 --pattern depth-address-recurrent-s0.pt --dir results
python demo_analogy_checkpoint.py --checkpoint results/depth-address-recurrent-s0.pt
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
- `docs/DESIGN-affect.md` — source-qualified emotion maps, attributed
  belief/story claims, and narrative obligations; weights may propose but do
  not certify affect
- `docs/DESIGN-interactive-harness.md` — microkernel agent OS: live session
  over registered subsystems, WAITING as ask-channel, boot capability matrix,
  optional Chat Completions skin; not a demo slash-menu
- `docs/DESIGN-visual-structure.md` — the parse-first multimodal plan:
  formula/diagram twins, SVG structure, and a pixel control. Its oracle layer
  is built (`experiments/visual/`); P-V1–P-V4 stay registered until the
  learned arms run
- `docs/blog/` — accessible project narratives, including the v0.6 story
- `docs/RELEASE-v*.md` — release notes; highest version is current
- `docs/DISCOVERIES.md` — the human-readable findings ledger
- `docs/BACKLOG.md` — recorded friction, each item with its evidence
