# v0.5.0 — A tiny model gets a world to reason inside

Baseline: [v0.4.0](RELEASE-v0.4.0.md). Plan of record:
[ROADMAP-v0.5.md](ROADMAP-v0.5.md) (closed); carried work:
[ROADMAP-v0.6.md](ROADMAP-v0.6.md). Findings:
[DISCOVERIES.md](DISCOVERIES.md). Public narrative:
[The world outside the weights](blog/the-world-outside-the-weights.md).

## The headline: the harness became executable

**Before:** the project had strong atoms — exact structural matching, a
pointer model that could recombine held-out structures at 1.000, a recurrent
address encoder that alone extrapolated past trained depth, and mathematical
axioms for fiction and time. But nothing executed those atoms as one ongoing
reasoning process. A three-beat story, a three-step proof, retrieval, and a
clarifying question were four disconnected aspirations.

**Now:** one bounded controller runs typed state through five actions:
`POINT`, `GEN`, `RETRIEVE`, `ASK`, and `WRITE`. The first four have executable
paths. Domain adapters decide truth: authenticated Lean-transition replay for
proof steps, frame consistency and temporal obligations for stories, and
receipt-bound extrinsic stores for retrieval. Rejected branches cannot mutate
accepted state. The same oracle loop completes a three-step proof replay and a
three-beat golden-chicken story. A second turn can ask the user for a
frame-private fact and resume without promoting the answer into world truth.

**Demonstrate:** 

```console
python scripts/oracle_controller_demo.py
python scripts/conversation.py
python scripts/theory_of_mind.py
python scripts/compose_assert.py
```

This is not yet a learned general solver. It is the executable environment in
which a tiny learned policy can safely become one: propose, verify, retain or
reject, retrieve or ask, and repeat.

## Roadmap triage

### Shipped

- **Oracle-first chained composition:** one controller, five-action protocol,
  immutable accepted state, auditable rejected branches, and shared proof/story
  execution. The learned policy and live PyPantograph search carry.
- **Frames as runtime state:** suspension, declaration boundaries, local
  invention, exit demotion, Chekhov obligations, no-deus heralding, owned belief
  frames, visibility-filtered events, and nested models of other agents.
- **Retrieval as an action:** 702 records at the first landing, then 723 before
  WordNet, across corpus, lexicon, structural groups, decomposition, and proof
  artifacts. Exact-first lookup, neighborhood fallback, authenticated receipts,
  honest abstention, and provenance-preserving POINT all execute.
- **Conversation as an action:** `ASK` pauses as WAITING, accepts a signed reply
  only for the exact frame/session/owner/question, and resumes from retained
  story state. User testimony binds a need without becoming corpus truth.
- **Temporal mirror relation:** five future/past mirror groups are reported
  separately from the four structural-twin levels; strict precedence now uses
  `LT`, retiring the false `BEFORE ~ LEQ` alias.
- **Four corpus lanes:** temporal/narrative payoff nodes, reference-frame
  physics, false-belief world/belief nodes, and six provability-logic nodes.
  The corpus is now 221 nodes across 22 disciplines, all owned by 14 seeds.
- **Proof provenance lint:** repository containment, transition shape, theorem
  closure, and unique statement ownership are checked. A deliberately wrong
  theorem-to-statement pairing remains the capability-blind proof that semantic
  correspondence is not yet checked.
- **External WordNet bridge:** optional Open English WordNet lookup moves eight
  fixed request terms from 0/8 to 8/8 owner coverage while changing zero frame
  verdicts; ambiguous polysemy remains unbindable. The 72 MB archive does not
  ship with this release.
- **Masked-skeleton pretraining:** 150,000 trained-depth trees, 51.8% held-out
  node recovery, and direct encoder transfer into the analogy pointer.

### Shipped as corrections and negative results

- The v0.4 recurrent result `0.226` was a favorable seed, not a stable point
  estimate. A second cold seed scored `0.087`; the honest two-seed result is
  `0.16 ± 0.07`. The fork verdict survives — both recurrent seeds remain an
  order of magnitude above lookup (`0.014`) and curriculum (`0.006`) — but the
  wall is noisier than one checkpoint suggested.
- Masked-skeleton warm starts score `0.215` and `0.187` OOD. Their mean (`0.201`)
  cannot be claimed as a lift over the cold mean (`0.157`) at n=2 because the
  difference lies inside cold variance. The supported result is stabilization:
  seed spread falls `0.139 → 0.029`, and the weak seed rises `+0.100`.
- The provability corpus self-grounded at 1.000 despite introducing dense new
  vocabulary. Groundedness therefore fails open through intra-corpus recurrence
  and broad pattern absorption; it is not a proof of external grounding.
- A registered nested-belief prediction incorrectly promised REFUTED where the
  semantics require UNKNOWN. Missing information is never contradiction. The
  original prediction and its correction remain together in the ledger.

### Carried to v0.6

- A learned tactic/story/tool policy and live PyPantograph search.
- Recurrence in pointer queries and decoder attention; depth remains far below
  1.0.
- Corpus-grounded rather than synthetic analogy quadruples.
- PROVEN-gated `WRITE`, including staged seed edits and human/prover audit.
- Open-language request parsing, expressive rendering, durable conversation
  serialization, and direct nested-frame mutation.
- Semantic checking of `verified_by`, provenance-split groundedness, ranked
  retrieval/tool choice, and general temporal model checking.
- A parse-first visual-structure experiment; see
  [DESIGN-visual-structure.md](DESIGN-visual-structure.md).

## See the improvement (Before → Now → Demonstrate)

### One reasoning loop

**Before:** proof replay and story composition were designs with no common
state machine. **Now:** both pass through `Controller`, with the same branch
trace and mutation boundary; the proof has three authenticated transitions and
the story has setup, complication, and resolution with one shared desire.
**Demonstrate:** `python scripts/oracle_controller_demo.py`.

### Fiction that obeys its own premises

**Before:** `frame_consistency` and Chekhov's gun were matched corpus laws but
not executable. **Now:** a frame can suspend a world law, declare local truth,
invent only through the suspension channel, reject contradiction, register a
planted element, require its discharge before close, reject an unheralded
payoff when the genre adopts no-deus, and demote local truths on exit.
**Demonstrate:** `python scripts/compose_assert.py` and
`python scripts/oracle_controller_demo.py`.

### Retrieval without status laundering

**Before:** every experiment received its knowledge context from the pipeline.
**Now:** an UNKNOWN can trigger exact or neighborhood lookup across six store
kinds; retrieved items retain their own epistemic status, and POINT requires a
session-local receipt binding the query, returned ids, frame, and verifier.
Misses remain UNKNOWN and end in ASK or honest abstention. **Demonstrate:**

```console
python scripts/retrieval.py
python scripts/retrieval.py quickening --wordnet C:\path\to\english-wordnet-2025-json.zip
python scripts/wordnet_eval.py C:\path\to\english-wordnet-2025-json.zip
```

### A real second turn

**Before:** the ladder could print an UNKNOWN as a question, but no answer
could return. **Now:** a parsed golden-chicken revision asks for a frame-private
slot, stops as WAITING, binds the signed response, and resumes with all three
story beats and the discharged obligation intact. The answer does not enter
`frame.asserted` or the corpus. **Demonstrate:**
`python scripts/conversation.py`.

### Beliefs are scoped worlds

**Before:** frames had no owner, so false belief had to be authored as a
contradiction. **Now:** Sally witnesses the marble placed in the basket but not
moved to the box. Her frame therefore answers basket while the world answers
box. Anne can hold a nested model of Sally, deriving second-order false belief;
an event reaches a nested child only when every owner on the path witnessed it.
**Demonstrate:** `python scripts/theory_of_mind.py` and the nested-frame tests in
`tests/test_frames.py`.

### Reference frames use the same scope machinery

**Before:** scope had only fictional users. **Now:** the corpus represents a
rotating physical frame as suspending an inertial law and admitting a local
centrifugal term. Galilean velocity addition mechanically typed-twins algebraic
topology's rank decomposition at `?0:V = +(?1:V, ?2:V)`. The predicted
cartoon-gravity template twin did not fire: shared execution semantics do not
imply identical equations. **Demonstrate:**

```console
python scripts/match_signatures.py
# inspect physics.frames.galilean_velocity_addition in the typed groups
```

### The model returned to the loop

**Before:** the GPU evidence stopped at one favorable recurrent seed (`0.226`).
**Now:** a fresh cold seed and two masked-skeleton warm starts expose both seed
variance and a reproducible stabilization effect. A release checkpoint can be
run without retraining against fresh held-out recombinations and fresh deeper
trees. **Demonstrate:**

```console
cd experiments
python demo_analogy_checkpoint.py \
  --checkpoint results/analogy_maskskel_s0.pt
```

The command deliberately prints both the 1.000 trained-depth capability and
the imperfect depth-OOD result. A demo that hides the wall would not
demonstrate this release's actual finding.

## Discoveries of the cycle

- A false belief can be a visibility result rather than an authored falsehood;
  the same placement/move events produce different scoped knowledge.
- Galilean velocity addition and chain rank-nullity are exact cross-discipline
  twins, while rotating physics and cartoon physics share a scope protocol but
  refuse a template twin.
- Löb's axiom and temporal induction share an archetype but correctly refuse
  every twin level; provability logic also exposed groundedness
  self-certification.
- Retrieval can change controller state without promoting the epistemic status
  of what it found, and an address is not an answer certificate.

The complete evidence and the deliberately retained near-misses live in
[DISCOVERIES.md](DISCOVERIES.md).

## Resolved from BACKLOG

This cycle closes the first executable cuts of frame ownership and event
visibility, physics reference frames, WordNet retrieval, nested belief models,
the provability corpus, runtime frame-id namespaces, ASK return flow,
Chekhov/no-deus evaluation, compose-to-frame delegation, and proof-artifact
integrity linting. Their remaining halves — deeper lexical traversal, nested
graft-back, semantic proof correspondence, general event binding, and learned
policy — moved to [ROADMAP-v0.6.md](ROADMAP-v0.6.md) or remain as evidenced
friction in [BACKLOG.md](BACKLOG.md).

## Honest limits

- The golden-chicken story is coherent and frame-checked but short and
  deliberately plain. It is not open-ended LLM-quality prose.
- Lean is authenticated committed-transition replay, not live search. Phase 2
  remains the first learned policy milestone.
- Four of five controller actions execute; `WRITE` is vocabulary only.
- RETRIEVE begins from an already parsed symbolic need. The system does not yet
  turn unrestricted English into that need or choose arbitrary external tools.
- ASK bindings are session-local runtime memory, not durable identity or truth.
- Theory of mind covers owned, visibility-derived belief and nested models in a
  controlled world; it is not unrestricted social reasoning.
- WordNet is an optional empirical vocabulary bridge, not mathematical
  evidence. Its archive is neither committed nor digest-pinned by this repo.
- The analogy task is synthetic. Exact trained-depth recombination is real;
  depth generalization remains low and variable.
- Nothing here stands against general LLM benchmarks yet. The 64 MB goal is a
  constraint and research direction, not a completed comparison.

## Assets and their stories

The following four assets attach to this release. All are fp32 and remain far
below the 64 MB system target.

- **`masked-skeleton-encoder-s0.pt`** — the structural pretraining artifact:
  150,000 trained-depth trees, three epochs, 51.8% held-out masked-node
  recovery. It exists to reproduce the warm-start boundary, not to answer by
  itself. Exercise it by passing it to `train_analogy.py --init-encoder`.
- **`analogy-masked-skeleton-warm-s0.pt`** — warm seed 0, test 1.000 / depth
  OOD 0.215. Together with seed 1 it supports the variance-stabilization claim.
  Exercise it with `demo_analogy_checkpoint.py`.
- **`analogy-masked-skeleton-warm-s1.pt`** — warm seed 1, test 1.000 / depth
  OOD 0.187. This is the weak-seed improvement half of the paired result
  (`+0.100` over cold seed 1).
- **`analogy-recurrent-cold-s1.pt`** — cold seed 1, test 1.000 / depth OOD
  0.087. This negative-control asset retires the old 0.226 point estimate and
  prevents the release from shipping only the favorable seed. Compare it with
  v0.4.0's `analogy_rec_s0.pt`.

The WordNet archive and every file under `experiments/data_real/` are excluded:
they are external/licensed data, not model assets.

## Reproduce from a fresh clone

```console
python scripts/check_regeneration.py
python scripts/validate_nodes.py
set PYTHONIOENCODING=utf-8
python scripts/match_signatures.py
python scripts/specialize.py
python scripts/decompose.py
python -m unittest discover -s tests
python scripts/oracle_controller_demo.py
python scripts/conversation.py
python scripts/theory_of_mind.py

gh release download v0.5.0 \
  --pattern analogy-masked-skeleton-warm-s0.pt \
  --dir experiments/results
cd experiments
python demo_analogy_checkpoint.py \
  --checkpoint results/analogy-masked-skeleton-warm-s0.pt
```

PowerShell users should set `$env:PYTHONIOENCODING='utf-8'` rather than the
`set` command above.
