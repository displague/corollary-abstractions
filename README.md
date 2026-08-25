# corollary-abstractions

Cross-discipline ontology of mathematical statements, a symbolic engine that
detects when different fields write the *same* formula ("structural twins"),
and an experiment suite showing that a **~2 MB neural model does genuinely
compositional language and math work** — provided everything with a closed
form (parsing, canonicalization, equality, the lexicon, structural
addresses) is computed *outside* the weights and handed to the model as an
interface. Latest release: [v0.20.0](docs/RELEASE-v0.20.0.md) — **two
registered runs, opposite verdicts, both published.** The foreign-dialect
renderer that v0.19 withheld now **clears and is served**: the grammar emits
a **canonical bracketing**, so the blind spot that voided last cycle is gone
rather than bounded — **5,228 of 5,228** grouping-pair deletions detected with
**zero blind**, and the control that had read 0.80 reads **42 of 42 on a floor
raised to 0.95**. In the same cycle a brand-new capability — statements that
compile into something you can **run** against your own numbers, 8,017 of
them — **voided on its own controls** and ships with the void published on
every answer it gives. **No conformance rate exists anywhere**, because a
control whose floor no correct instrument could meet took it away. See [the
floor no instrument could
meet](docs/blog/the-floor-no-instrument-could-meet.md).
[v0.19.0](docs/RELEASE-v0.19.0.md) is the floor under it: two glyph
equivalences took the **native voice from 17.0% to 67.2% of the corpus**
(2,172 → **8,586 of 12,777** parseable, additive-only: 0 changed, 0 lost),
and the **register** — a frozen, counted inventory of the 1,878 statements
the system still cannot say — ships beside the voice rather than instead of
it. [v0.18.0](docs/RELEASE-v0.18.0.md) is the floor under *that*: sentences no
person wrote, each gated by re-parsing back to the exact term it renders.
[v0.17.0](docs/RELEASE-v0.17.0.md) still stands behind it: served over an
OpenAI-compatible endpoint, 49/49 correct with receipts at a median 3,451
useful tok/s against a grounded 4B model's 4/49 and a median of zero.
The grammar-reach measurement from [v0.9.0](docs/RELEASE-v0.9.0.md)
still stands: about a third on uncontrolled formal math.

## Six headline demonstrations

**0. Point any OpenAI-compatible client at it.** Since
[v0.17.0](docs/RELEASE-v0.17.0.md) the same session engine the prompt
drives is served over HTTP — stdlib only, loopback only, offline boot, no
generative path anywhere in it. An attaching orchestrator reads the
capability sheet once and configures itself from the registered line
grammar, the way it reads a tool schema:

```
$ python scripts/serve_chat.py          # in one shell; 127.0.0.1:8377, no flags
$ curl -s http://127.0.0.1:8377/v1/capabilities | python -m json.tool
{ "schema": "corollary.capabilities/1",
  "profiles": { "corollary/kernel": ..., "corollary/conversation": ... },
  "line_grammar": [ { "form": "owns <template-expr>", "route": "ownership",
                      "example": "owns x ^ 2", "served": true }, ... ],
  "honesty": "offline boot; unregistered paths abstain (P-IH4); no generative path" }

$ curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"owns x ^ 2"}]}'
```

The reply's `content` is the engine's rendered answer verbatim — the skin
has zero rendering freedom — and everything else (route, status, receipt,
what the request asked for and was ignored) rides in an `x_corollary`
vendor field. A clarification question crosses the wire as a need record
and the next message answers it; nothing ever invents a slot value.

**1. You can type at it.** Since [v0.12.0](docs/RELEASE-v0.12.0.md) the
prompt returns a machine verdict. In v0.13 a resolver ASK can survive the next
line and accept an explicit hard constraint; cancellation, repeated-state
cycles, and a four-hop ceiling terminate without guessing. Every sentence it
prints was written by a person and stored in the corpus, or comes from Open
English WordNet; every value is computed exactly; every relation is a
committed link. Since v0.18 it *does* author one line — the `in words`
rendering of the formal statement — and that line is emitted only when the
sentence re-parses to exactly the term it renders (below).

```
$ echo "what is the cosine of a double angle" | python scripts/harness.py
Double-Angle Cosine
The cosine of twice an angle is the difference of the squared cosine and the squared sine.
formally   : cos(2*x) = cos(x)^2 - sin(x)^2
in words   : the cosine of the quantity two times variable zero end quantity equals the cosine of the quantity variable zero end quantity to the power of two plus the opposite of the quantity the sine of the quantity variable zero end quantity to the power of two end quantity
source     : trigonometry.identities.double_angle_cosine  [trigonometry.core.v1]

$ echo "when x=5, what is x ^ 2?" | python scripts/harness.py
exact      : 25

$ echo "owns x ^ 2" | python scripts/harness.py
6884 of 12777 statements host 'x ^ 2'

$ "double factorial`nnarrow word recursive" | python scripts/harness.py --offline
reading : Double Factorial, Recursive (TheAlgorithms)
```

That `in words` line is one long line, printed whole. It is not a template
and not a quotation: a grammar composed it from the term, and it is served
only because re-parsing it recovers `cos⟨*(2, ?0)⟩ = +(^(cos⟨?0⟩, 2),
neg(^(sin⟨?0⟩, 2)))` — the source skeleton, exactly. A term that does not
parse, an operator with no lexicon row, or a sentence that fails the round
trip produces **no line at all**: absence is the refusal. It says
"variable zero" rather than "x" because canonicalization erases slot
identity; the source identifiers ride in the receipt, not the sentence.

```
$ PYTHONIOENCODING=utf-8 python scripts/realize_term.py --term "1 + 1 = 2"
  "surface": "two equals one plus one",
  "round_trip": "EXACT",
```

**Since v0.20 there is a second `in words` line, for statements the native
grammar cannot read at all.** Those come from an external prover's dialect,
and they are rendered by borrowing — then checked by handing the English back
to the **external proof assistant that produced the original** and requiring
it to elaborate to the identical term:

```
$ PYTHONIOENCODING=utf-8 python scripts/answer.py leanworkbook.skel.lean_workbook_7992
formally   : 2*x+1 >= 0 ↔ x >= -1/2
in words   : for every variable zero of type rational it holds that two times
             variable zero plus one at least equals zero exactly when variable
             zero at least equals minus one divided by two
```

That line **arms itself from evidence**: `scripts/answer.py` reads the
registered run and emits nothing unless five named controls cleared. Voided or
absent artifact, no line — and the capability sheet says so with its reason.
It is served today because the run reads `FIRES`; you can check that yourself
in one command, and the answer is the same one the renderer asked:

```
$ PYTHONIOENCODING=utf-8 python -c "import sys; sys.path.insert(0,'scripts'); \
    import foreign_voice_arming as a; s=a.arming_state('.'); \
    print(s['armed'], s['verdict'], s['non_blocking_voids'])"
True FIRES ['C-V3′']
```

**And since v0.20 a statement can be run rather than only looked up.** `conform`
compiles a statement into a program over its declared domain and searches for a
counterexample. It publishes what it can and cannot certify, in the answer:

```
$ echo "conform leanworkbook.skel.lean_workbook_10012" | PYTHONIOENCODING=utf-8 python scripts/harness.py
  statement  : leanworkbook.skel.lean_workbook_10012
  verdict    : NO_COUNTEREXAMPLE_FOUND
  domain     : Nat, / is truncating, - is truncated-at-zero
  certifies  : tested at 37 admitted points and not falsified; this certifies
               nothing universally and is not evidence the statement is true
  points     : 37 admitted of 1000 sampled (159 guard-rejected, 804 outside the
               carrier, 0 errored)
  run void   : VOID — C-E1 missed its floor; every NO_COUNTEREXAMPLE_FOUND is void
```

The last line is not a bug report; it is the registered run's own verdict,
read off the artifact on every call. A ground statement decides outright —
`conform leanworkbook.ground.lean_workbook_plus_16115` returns `DECIDED_FALSE`
with the two sides printed. **There is no conformance rate**, here or
anywhere: the control that would have licensed one voided, and the reason is
worth reading, because it is a floor no correct instrument could have met.

Ask it something the corpus does not contain and it says so: on 1,000
sentences sampled from a dictionary the shipping resolver wrongly claims 3.0%
as corpus material. A morphology candidate reached 1.000 on a fresh holdout
but scored 3.4% false positives and one wrong BIND, so it was reverted. The
shipping in-corpus point remains 0.833 coverage / 0.030 false positives.

**2. The matcher discovers that sciences repeat one another.** From 12,777
statement nodes across 27 corpora (263 curated including 9 verified-code
and the recorded-session ingest — 263 by corpus curation, of which 262
carry person-authored prose, the recorded-session ingest node being curated
while its prose is an ingestion record — + 12,514 unique-covered Lean-workbook
statements with matcher templates — 302 ground + 12,212 emitted), plus two
**quarantined holdout corpora** in `data_holdout/` (miniF2F 157,
Goedel-Pset 1,896) that are deliberately invisible to the merged graph,
structure alone:

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

**3. A tiny model answers foreign-language questions — and exact code makes
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

**4. One verified loop searches a live proof and maintains a private story
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

**5. A sealed closure answers "unreachable" as evidence, not as a timeout.**
Since [v0.15.0](docs/RELEASE-v0.15.0.md), two committed worlds — the story
frame and the right-triangle diagram — have their complete bounded
possibility spaces compiled, independently checked, and sealed under a
digest (`reports/closures/`). A query is a lookup against that sealed
object: `REACHABLE` comes with a shortest route replayed through the
world's own verifier; a state the world cannot reach within the horizon
gets `NOT_REACHABLE_WITHIN_HORIZON` with the bound stated in the answer:

```
$ python scripts/closure_query.py reports/closures/story.golden_chicken.closure.json target.bytes
...
outcome: REACHABLE
shortest_route: 5 action(s), replayed through the world's own verifier
...
```

The enumeration also read the code more thoroughly than its authors: twelve
route-convergence cells decoded into two previously unstated properties of
the committed story world (its obligation transitions are desire-blind, and
re-planting is idempotent).

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
| A bounded negative can carry evidence | two worlds' complete horizon-bounded spaces compile and check independently (75 and 1 states, byte-identical rebuilds); 90/90 applicable corruptions caught; "not reachable within the bound" is a property of the sealed object |
| A veto can rest on one row | the cross-field kind check flags 22/77 aligned slots, but removing one exemption (proposition = set) moves it to 38 while every other removal moves it by ≤2 — the instrument is one textbook judgement on a strong default |
| Information is not precision | the provenance graph's edges are real (0/100 degree-and-kind-preserving shuffles reproduce the audited coverage) yet the retraction radius voided its own gate: lexical citation floods past its 3× cap and misses claims that cite only derived numbers |
| A blind author repeats the load-bearing call | an isolated context shown only the 26-kind menu ruled all 325 pairs, agreed with the incumbent table on 43/44 shared pairs, independently made the proposition=set exemption, and put real tags at 21 conflicts against a permuted floor of 45 |
| Grounding moves answering into another speed class | one registered run on a sealed half: 49/49 correct with receipts at a median 3,451 useful tok/s (1,936 aggregate) and 25 ms to first useful token, against a grounded 4B model holding the same records at 4/49, a zero median and 8.79 tok/s aggregate — gate frozen at 5× beforehand, so 220× at the aggregate. A max-rate query-blind server and the kernel's own answers shuffled between tasks both score 0.0 |
| Exact content does not survive a decoder | the contender is handed the source records verbatim and told to quote them, and still returns 0/16 corpus definitions and 0/5 twin lookups; the quote instruction did not move its score (5/45 before, 5/45 after) |
| A composed sentence can carry its own proof | a realization grammar linearizes canonical terms into English and re-parses each sentence through a byte-frozen parser: 2,170 of 2,172 parseable terms round-trip exactly (0.9991 — of 12,777 corpus nodes), 0 wrong sentences, 0 words outside the lexicon and the registered numeral pair, 2 oversized numerals refusing rather than rounding. Shuffled lexicon scores 0.0000; none of 3,722 one-operator near-misses round-trips to its source |
| A design's claims about a tree are checkable before they cost a run | five sentences in the governing design were corrected by measurement — an unmeasurable 90% floor (only 17.0% parse), a head inventory read off the wrong field (64 heads, not 95), a control that a two-sided scramble would have voided, an aliasing behaviour the canonicaliser does not have, and a receipt whose two slot numberings disagree on 5.07% of terms |
| Two glyphs were half the wall | adding `≥`→`>=` and `≤`→`<=` to the tokenizer takes the parseable set 2,172 → 8,586 of 12,777 (17.0% → 67.2%); all 6,414 newly-reached statements round-trip exactly, and a witness running the retired parser out of git proves the change additive corpus-wide (0 changed, 0 lost). Caveat published with the rate: one corpus, two call heads — not a lexicon-coverage claim |
| A gate's blind spot can be measured, and the measurement can void the gate | rendering the foreign dialect scored 2,313/2,313 identity through a pinned external checker, and the near-miss control voided it at `drop_group` 0.80 against a 0.90 floor — deleting a semantically redundant bracket changes the sentence and not the term. The line is not served; the excluded `drop_binder` class measures 0.18, which is the blind spot's published width |
| A park with numbers is what discharging an instruction looks like | a maintainer-seeded design was adopted bounded, built, and measured against three of its own pre-registered baselines: retrieval NOT BEATEN on both legs (0.3256/0.2059 against the keyword channel's 0.9302/0.0294, same rows same run), term layer NOT BEATEN (6.91× vs 8.44×), and the one win conceded in advance as a restatement. Unified vs two indexes with one tag bit: 0.9981 — two objects wearing one id space |
| This graph's authors never forked a convention | a census of 2,493 co-present differing pairs finds 125 convention-pair candidates, every one notational and zero mathematical; 0 have both members in a hand-authored corpus, and sign conventions, the 0-in-ℕ boundary and 2π placement return 0/0/0 with detectors proven live by injection |
| A blind spot can be removed from the grammar rather than bounded | canonical bracketing means a rendered bracket the mathematics does not need is never emitted, so deleting one must change the term: **5,228 of 5,228** grouping-pair deletions detected across every canonical surface, zero blind. The control that read 0.80 last cycle reads **42 of 42 on a floor raised to 0.95**, the foreign `in words` line is served, and the price is published too — the share of the skeleton control's misses that exercise the gate fell 42.5% → 22.4% |
| A restored clause moves the denominator, not the numerator | the re-specified control verified each mutation changed the term *before* rendering it, and discarded five: `drop_ascription` reads **45 detected of 45 scored**, falsifying its own pre-registered 45-of-50 prediction. Last cycle's 0.90 was not five missed near-misses — it was five mutations that were never mutations |
| A control's floor can be unmeetable by a correct instrument | the conformance run's perturbation control froze a 99% flip floor and measured **0.650**, voiding every `NO_COUNTEREXAMPLE_FOUND` in the run. Part is the floor — mutations that cannot be made false over the declared `Nat` carrier — and part is a real sampler miss in the same published list, and **the run has no instrument that partitions them**. 8,017 statements compile and the route serves with the void on every answer; no conformance rate exists anywhere |
| A reader that scores half as well on nonsense is not reading | a pinned local model read served sentences blind and reconstructed the term at 0.8417 — and scored 0.5000 on scrambled surfaces, ratio 0.594 against a 0.5 voiding threshold frozen in advance. The machine-reader claim is not made; the human-reader claim has never been attempted, because a one-maintainer repository has no non-maintainer to mark a sheet blind |

Two retractions are part of the record (a too-easy test caught by external
audit; a mid-run misreading) — see ANALYSIS.md. House rule: every split
must survive a capability-blind symbolic baseline, and no single-seed
comparison is trusted.

## Repository layout

```
schema/                 Mathematical Statement Node JSON schema
data/<discipline>/      statement corpora (27 corpora, 12,777 nodes)
data_holdout/<name>/    quarantined holdouts (miniF2F 157, Goedel-Pset 1,896)
                        committed and byte-reproducible, invisible to the
                        merged graph — a holdout inside data/ is not held out
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
  measure_compression.py concept-token compression (32.10x char-to-concept
                        at 12,777 nodes; the long-quoted 11.24x was the
                        221-node v0.6 corpus — see RELEASE-v0.15.0 limits)
  closure_worlds.py     the two registered worlds behind one 4-op contract
  closure_build.py / closure_check.py   independent builder + checker pair
  closure_corrupt.py / closure_query.py twelve-class corruption battery;
                        query a sealed closure and get a receipted answer
  provenance_graph.py   committed-bytes provenance graph (writer lineage +
                        six frozen citation rules, tagged per edge)
  retraction_radius.py / radius_recheck.py  certifier + never-saw-the-builder
                        recheck; radius_blind_control.py 100-shuffle control
  check_report_regeneration.py  do committed ledgers match their writers
                        (declared snapshots reported, not regenerated)
  serve_chat.py         OpenAI-compatible chat skin over the session engine
                        (stdlib, loopback, offline boot, capability sheet)
  realize_term.py       canonical term -> English sentence, gated by a
                        re-parse through the byte-frozen parser; --census
                        publishes R0's denominator, --term shows a receipt
  realization_lexicon.py  the reviewed lexicon loader: injectivity,
                        prefix-freeness, numeral-disjointness, all gated
  numeral_words.py      the registered numeral pair (|n| < 10^15, exact
                        decimals, Fractions as "N over M"); refuses outside
  measure_realization.py  the registered realization run and its three
                        controls; refuses (exit 3) on any prereg digest drift
  build_throughput_tasks.py  the sealed task book, computed from committed
                        artifacts and provably never run against the engine
  measure_throughput.py the client-side stopwatch (public HTTP API only)
  dump_server.py        control C1: max-rate, query-blind, scored the same
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
python scripts/validate_nodes.py            # 12,777 nodes / 27 corpora green
python scripts/check_report_regeneration.py # committed ledgers match writers
python scripts/match_signatures.py          # twin ledger
python scripts/specialize.py                # specialization edges
python scripts/oracle_controller_demo.py    # one loop: 3 Lean replays + 3 story beats
python scripts/retrieval.py                 # exact five-store lookup then POINT
python scripts/retrieval.py quickening --wordnet data_sources\archives\english-wordnet-2025-json.zip
                                            # (the harness itself now finds the
                                            # manifest-pinned archive unaided)
python scripts/closure_query.py reports/closures/story.golden_chicken.closure.json target.bytes
                                            # ask the sealed closure; REACHABLE
                                            # routes replay through the verifier
python scripts/retrieval.py --chain "ALWAYS(IMPLIES(PLANTED(ELEMENT), EVENTUALLY(DISCHARGED(ELEMENT))))"
                                            # walks the miss chain: exact and
                                            # neighborhood miss, derivation answers
python scripts/retrieval.py --chain --observations path\to\notes note.tide_gauge_2026
python scripts/wordnet_eval.py data_sources\archives\english-wordnet-2025-json.zip
python scripts/conversation.py              # two-turn golden-chicken clarification
python scripts/theory_of_mind.py            # Sally looks in basket; world says box
python scripts/realize_term.py --census     # 8,586 of 12,777 parseable (67.2%)
                                            # -- 2,172 before the two glyphs
PYTHONIOENCODING=utf-8 python scripts/realize_term.py --term "x >= 1"
                                            # "variable zero is at least one";
                                            # newly reachable since v0.19
python -c "import json; v=json.load(open('experiments/foreign_voice_rate.json',encoding='utf-8'))['verdicts']; print(v['overall'], v['voided'])"
                                            # VOID ['C-V4'] -- the foreign line
                                            # is certified by nothing, so it is
                                            # not served
PYTHONIOENCODING=utf-8 python scripts/realize_term.py --term "1 + 1 = 2"
                                            # one sentence and its receipt
python scripts/measure_realization.py --out realization_rate.repro.json
                                            # the registered run, byte-identical
                                            # to experiments/realization_rate.json;
                                            # exit 3 and writes nothing if any of
                                            # the five preregistered digests moved
python scripts/serve_chat.py                # the chat endpoint on 127.0.0.1:8377
curl -s http://127.0.0.1:8377/v1/capabilities            # the capability sheet
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' `
    -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"owns x ^ 2"}]}'
python scripts/measure_throughput.py --system kernel --url http://127.0.0.1:8377 `
    --half A --out halfA.repro.json         # the stopwatch on the development half
                                            # (half B is sealed and refuses without
                                            # --registered; counting useful tokens
                                            # needs the digest-pinned tokenizer named
                                            # in experiments/throughput_baseline.json,
                                            # and refuses rather than approximating)
python prover/live_search.py                # live Lean search + projection ablation
python experiments/train_tactic_policy.py --live  # learned vs strong blind order
python experiments/corpus_analogy.py --out experiments/results/corpus_analogy_repro.json
                                             # grounded rows + trivial blind baseline
cd experiments && python -m visual.genvisual adjudicate --n 240 --seed 11
                                             # visual oracle: P-VO1..P-VO7
python -m unittest discover -s tests -v     # controller contracts + vacuity checks
# 1,827 tests, 0 failures, 3 skipped at v0.18.0 -- 6h42m serial (24,117.3s),
# green on the first run; test_write_stage still the bulk of it. Receipts:
# reports/test_gate_v018/ (baselines: test_gate_v017/ incl. its five
# pre-green runs, test_gate_v016/, test_gate_v015/). v0.18's new modules:
# test_realize_term (44), test_realization_lexicon (37),
# test_measure_realization (26); test_serve_chat 68 -> 74.
# 2,106 tests, 0 failures, 5 skipped at v0.19.0 -- 6h03m serial (21,767.5s),
# green on the first run, second cycle in a row. Receipts:
# reports/test_gate_v019/ (baselines: test_gate_v018/, test_gate_v017/
# incl. its five pre-green runs). The 5 skips: 3 standing environment
# skips + test_transliteration's 2 slow-regeneration cases, hand-run
# green (44/44, 180s) before the gate.
# [SUITE-GATE-V20] v0.20.0's full-suite count, timing and skip list land
# here when the gate runs on the frozen tip; receipts to
# reports/test_gate_v020/. This cycle adds seven new modules
# (test_conform, test_conform_prereg, test_conform_register,
# test_cv4_replay, test_grouping_agreement, test_grouping_canonical,
# test_machine_reader) and grows thirteen existing ones. Rotation-time
# targeted runs on the merged tree: 386 green across the nine
# conform-adjacent modules, 512 green across the fourteen batch-adjacent
# ones.
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
- `docs/DESIGN-language-as-structure.md` — text analysis/creation as the dual
  of prove→pretty-print; terms + linearize, not string templates as law;
  WordNet as lexicon only
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
- `docs/DESIGN-compile-before-query.md` — shipped at v0.15: compile a
  complete small possibility space before choosing a target, then return a
  replayable path or an exact negative within the declared bound; the two
  sealed closures in `reports/closures/` are its evidence
- `docs/DESIGN-retraction-closure.md` — adjudicated at v0.16: retraction
  as an operation with a receipt. Built, independently rechecked, and
  voided by its own gate on precision; the instruments and ground truths
  survive unscored, and the §3 correction + §6a registration are the
  worked example of a design auditing itself
- `docs/DESIGN-grounded-throughput.md` — **measured at v0.17** (maintainer
  redirect, 2026-08-21): the knowledge graph served through an
  OpenAI-compatible chat API by a microkernel of small programs and
  optional small models, with a preregistered claim that grounded,
  receipt-bearing answer tokens arrive many-fold faster than a language
  model can generate them. T1–T7 adjudicated on one registered run of a
  sealed 119-task book; both blind controls read 0.0. The protocol subset
  is pinned in `docs/SPEC-chat-completions-skin.md`
- `docs/DESIGN-sans-template-rendering.md` — **measured at v0.18**: the
  kernel says its own structures in open English, each sentence gated by
  re-parsing back to the exact term it renders through a byte-frozen
  parser that never saw the realizer. R1 fired at 0.9991 over the 2,172
  terms parseable **at v0.18**; R2 clean; all three controls read out.
  Five of its own sentences were corrected by measurement, four before
  implementation. The parseable denominator moved to 8,586 at v0.19 —
  that 0.9991 is the artifact of record for what was measured under the
  **retired** parser, declared historical in writing rather than re-run
- `docs/DESIGN-foreign-voice.md` — **measured at v0.19, and VOID**: render
  the statements the parser *cannot* read by borrowing a lexicon, and gate
  the result with the already-pinned external Lean checker rather than a
  parser this project owns. Every B-gate fired — including 100 of 100
  sealed hand-renderings reproduced byte-identically, and identity 2,313
  of 2,313 — and then **C-V4 voided the reading** at `drop_group` 0.80
  against a 0.90 floor, so **the line is not wired** and that identity
  rate never travels without the void. Its headline artifact is the
  **register**: a frozen, digested inventory of the 1,878 statements the
  system cannot say, in two buckets that are never summed — 1,706 a
  budget a maintainer can lift, 172 a design consequence this cycle owns
- `docs/DESIGN-voice-completion.md` — **v0.20 item 2, maintainer-directed**
  (2026-08-24): the withheld voice ships, and the repair is structural
  rather than tighter bookkeeping. The renderer emits a grouping word only
  where precedence demands one, so the redundant-bracket variant that voided
  C-V4 **stops being constructible** — measured read-only before being
  chosen: 620 of 6,063 bracket pairs are redundant, 15 of the 100 sealed
  renderings change, and every grouping-pair deletion over the whole covered
  set is detected, 5,228 of 5,228. C-V4′ is re-specified with C-R2's missing
  clause, its drawn **id lists** pinned rather than its seed, and **C-V3′,
  a machine blind reader**, replaces a control that was ABSENT because a
  single-maintainer repository has no non-maintainer. The human-reader claim
  stays not-made. If the fresh run voids again, the voice stays withheld and
  v0.21 inherits it
- `docs/DESIGN-plain-input.md` — **maintainer-seeded candidate for v0.21**
  (2026-08-24), pre-course: plain text enters, a small model proposes
  candidate interpretations, the kernel verifies them, and the **hidden
  variable** — the assumption an answer is predicated on — is named rather
  than silently assumed. The v0.21 course must adjudicate it explicitly;
  **silence is not a disposition**. Its §6 carries the cross-design machine
  blind reader definition and hands it to the voice design's run
- `docs/DESIGN-block-vocabulary.md` — **adopted, built, measured, and
  parked BY NUMBERS at v0.19** (§3e), which is the full lifecycle a
  maintainer's no-silent-disposal instruction is owed. Scoped to one
  question — is the unified dictionary a real object, or two existing
  objects wearing one id space? — against three baselines pre-registered
  from its own concessions. It beat one, and that one was declared in
  advance to be an arithmetic restatement; retrieval lost on both legs at
  once and the term layer read 6.91× against 8.44×. Answer: **two
  existing objects wearing one id space** (0.9981 against two indexes
  carrying one tag bit). Untested by any baseline and named for a future
  unpark: append-only, path-independent growth
- `docs/DESIGN-ledger-first-claims.md` — parked whole (course-chosen,
  review-hardened, preregistration-ready): claims are emitted, not
  written — published quantitative sentences become generated artifacts
  of typed citations, with the voided scan demoted to a completeness
  linter
- `docs/blog/` — accessible project narratives, including the v0.8 story
- `docs/RELEASE-v*.md` — release notes; highest version is current
- `docs/DISCOVERIES.md` — the human-readable findings ledger
- `docs/BACKLOG.md` — recorded friction, each item with its evidence
