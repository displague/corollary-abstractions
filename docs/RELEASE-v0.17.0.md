# v0.17.0 — the graph answered at wire speed, and the gate was not close

Sixteen releases defended a thesis with instruments. This one asked what
the thesis is *for*, and answered it with a stopwatch: the knowledge graph
now serves an OpenAI-compatible chat endpoint any agent harness can attach
to, and against a grounded 4B model holding the very same committed
records, it delivered correct receipt-bearing answers at 220 times the
aggregate throughput — and on the median, which is the statistic the gate
frozen at five actually names, the contender scored zero. The cycle was
built in preregistration order, and the reviews between the artifacts
killed four holes that would each have produced a defensible-looking
number: any repository file could be minted into a certified bounded
negative, a context setting we believed in was silently dropped by the
opponent's API layer, the contender was never told to quote the material it
was handed, and the transcript-divergence check paired assistant turns
FIFO instead of most-recent.

**Links** — previous release: [v0.16.0](RELEASE-v0.16.0.md) · closed plan:
[ROADMAP-v0.17](ROADMAP-v0.17.md) · next plan:
[ROADMAP-v0.18](ROADMAP-v0.18.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the answer was already written; the model had to type it](blog/the-answer-was-already-written.md)

## The headline finding

**Before.** The project's founding claim is that everything with a closed
form belongs in inspectable code, with weights carrying only the graded
residual. Sixteen releases defended that claim with instruments and never
once demonstrated its consequence for a person using the thing. There was
no HTTP surface at all — the Chat Completions skin had been parked five
consecutive cycles — and a design sweep on 2026-08-21 found **zero prior
mention** of throughput, latency, or cost-per-answer anywhere in BACKLOG or
any TRIAGE record.

**Now.** `scripts/serve_chat.py` serves the existing session engine over
`POST /v1/chat/completions` with a generated capability sheet at
`GET /v1/capabilities`, and one registered run of the sealed half of a
119-task book adjudicated all seven gate clauses. K = 5 was frozen in the
baseline manifest before the stopwatch existed. At the aggregate the
measured multiple is **220×**; at the median — which is the statistic T4
actually gates on — the contender scores zero, so **K = 5 is satisfied
unbounded rather than measured** there. Both readings are computed,
labelled and committed, and the release quotes both rather than picking
the flattering one.

| arm | correct with receipt | median perceived tok/s (the T4 statistic) | aggregate tok/s | median time to first useful token |
|---|---|---|---|---|
| **kernel** (this repository, over HTTP) | **49/49 = 100%**, and 100% in every kind | **3,451** | **1,936** | **25 ms** |
| **B-grounded** — the gated contender, same records injected verbatim | 4/49 = 8.2% | **0.0** | 8.79 | 45 ms |
| B-ungrounded — same model, cold; reported, never gated | 1/49 = 2.0% | 0.0 | 0.112 | 53 ms |
| **C1** — dump server: protocol-valid, maximum-rate, query-blind | 0/49 | 0.0 | 0.0 | — |
| **C2** — the kernel's own answers permuted across tasks | 0/49 | 0.0 | 0.0 | — |

Both controls carry voiding sentences and both read **0.0** against a 1%
threshold (34.5 tok/s on the median): the metric credits no bandwidth, and
the scoring separates right answers from wrong ones. C3 — the clause that
lets the baseline win and falsify the thesis at this scale — did not fire.
T5's usefulness floors (≥90% overall, ≥80% within every kind, 100% of
refusals refused, 100% of marked WAITING turns surfaced) held at
100/100/6-of-6/6-of-6, which is what makes the speed numbers admissible
at all — T5 is the design's precondition for reading T4, an adjudication
order, and the floors held with nothing to spare from perfect.

**The contender's failure is the thesis, not a strawman.** B-grounded
receives the same committed records the kernel's answer rests on, extracted
verbatim, under a frozen prompt template that — after a half-A trial —
explicitly tells it to reproduce the relevant content verbatim. It still
scored 0 of 16 corpus definitions and 0 of 5 twin lookups. Exact content
does not survive being sampled through a decoder, even when the decoder has
the content in front of it. That sentence is the cycle's product.

**Demonstrate.**

```
python scripts/serve_chat.py            # in one shell; 127.0.0.1:8377, no flags needed
curl -s http://127.0.0.1:8377/v1/capabilities
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"owns x ^ 2"}]}'
python -m unittest tests.test_serve_chat.T1Triangle tests.test_serve_chat.T2AdversarialProbe
```

The committed receipts are `experiments/throughput_result.json` (kernel),
`_bgrounded.json`, `_bungrounded.json`, `_dump.json` (C1) and `_c2.json`
(C2); the sealed book is `experiments/throughput_tasks.json`; the pinned
baseline is `experiments/throughput_baseline.json`. Full readout: ANALYSIS
"v0.17 — grounded throughput: the registered run, and the trials that made
it honest".

## Roadmap triage

**Shipped.** *Item 1 — grounded throughput.* Implemented end-to-end in the
design's registered order, every artifact committed before the one that
depends on it: the spec (`0e08bcb`), the W1/W2 wiring (`4b2e2de`), the
sealed task book (`ca2262c`) and its LF pin (`55b0473`), the baseline
manifest that freezes K (`9b635b6`), the skin (`8059b4a`), the stopwatch
(`38c9778`), and one registered run (`c345dc9`). All of T1–T7 are
adjudicated: T1, T2 and P-IH6 by the named gate classes in
`tests/test_serve_chat.py`; T3 by commit order (the book seals before the
skin answers a task); T4 above; T5 above; T6 by construction (below); T7 by
the stopwatch's per-task **receipt-subset scoring** — `receipt_ok` /
`strict_equal` re-validated client-side against the committed artifacts the
task book cites, on **61 of 61** half-B tasks rather than the design's
sampled 20 — supported by `tests/test_serve_chat.py`'s `node_sha256`
recheck. (The seal witness is a different mechanism and is not T7: the
run's `revalidate_rendering_digests` proves the *rendering modules* did not
move between sealing and timing.)

**Shipped as an honest readout, which is what the gate asked for.** *Item 2
— session-native small models.* T6 says: if a learned component operates in
the serving path it ships with its capability-blind baseline; **if none is
ready, the lane ships "symbolic-only this cycle" in writing.** It does. The
serving path boots offline — `CoreSession.boot(repo_root, offline=True)`,
not a flag but a fact, published in the capability sheet's `honesty` line —
so no learned component operates in it *by construction*, and no
checkpoint was brought to the admission bar this cycle: the headline lane
consumed it. The existing checkpoints are untouched and remain valid. The
successor seat is named rather than left vague:
[DESIGN-sans-template-rendering](DESIGN-sans-template-rendering.md) §9's
learned preference ranker — sitting above the deterministic
`preference.shallow.v1` that already ships — behind the same bar, in v0.18.

**Carried lanes (ROADMAP-v0.17 §3), with their dispositions.**

- *Chat-completions HTTP skin* — **RESOLVED by shipping**. Parked at v0.13,
  v0.14, v0.15, ROADMAP-v0.16 §3 and ROADMAP-v0.17 §3; the v0.16 rotation
  wrote that a fifth park means v0.18 owes a schedule or a retirement, and
  ROADMAP-v0.17 answered it early by making it the headline. The park
  history is annotated in BACKLOG, not deleted.
- *Ledger-first claims* — **stays parked, with the reason recorded.** Its
  own unpark rule says it becomes a headline **candidate** the first cycle
  after the throughput readout. That is now, and it is not being silently
  dropped: v0.18's headline is maintainer-directed to substrate Phase 6, so
  the lane is carried into [ROADMAP-v0.18](ROADMAP-v0.18.md) §3 parked, with
  its design, its hardened L1–L13 gate and its course receipt
  (`reports/design-direction-v0.17.json`) intact and preregistration-ready.
  Its mid-cycle lift trigger — a release again quoting a number its artifact
  no longer supports — stands unchanged.
- *Sans-template open-prose rendering* — its trigger fired. DESIGN-grounded-
  throughput §10 wrote, before the run, that if T4 fires this boundary
  becomes the next surface with a measured floor under it. It is v0.18's
  item 1.
- *The cost ledger* (answers per joule and per dollar against hosted
  pricing) — §10 named **two** successors to a fired T4 and named this one
  **first**; the maintainer's directive selected the other. Recorded as a
  choice between two registered successors, not as an omission: it is
  parked in [ROADMAP-v0.18](ROADMAP-v0.18.md) §3 and repeated in the new
  design's own forward list, because it needs a metrology neither cycle has
  designed.
- Everything else in §3 is unchanged and carried or parked as recorded there.

**Drift audit** (v0.15 and v0.16 re-read, per the rule). The audit's
long-running specimen closes this cycle: the HTTP skin — the conversational
surface carried since v0.8, parked five times — shipped. The v0.15 audit's two converted parks (the
v0.13 A3–A5 acceptances, the resolver coverage lane) are untouched and
remain parked with their unpark conditions. Nothing new was found lost to
attrition — but one thing is worth naming rather than leaving implicit:
this is the **second consecutive maintainer-directed headline**, and
ROADMAP-v0.18 §4 records it as a first-class governance note rather than
absorbing it.

## What changed, per area

### The skin was specified before it existed — and the spec corrected the design

**Before.** DESIGN-grounded-throughput assumed HTTP would resume durable
sessions and that twins were already answerable from a typed line.

**Now.** `docs/SPEC-chat-completions-skin.md` pins the protocol subset, the
two profiles, replay-per-request with a deterministic prefix-hash session
identity, the verbatim-content rule the throughput metric counts, receipts
keyed on (route, answered?), and the WAITING mapping P-IH6's adjudication
quotes. Two adversarial review rounds (2 Critical, 7 High, 10 Medium; then
1 High, 4 Medium) produced two corrections that are recorded in the
governing docs rather than silently absorbed: **¶DEV-1** —
`ConversationSession.restore` is *not* in the serving path, so the design's
§3 sentence and its §4.3 rationale stand on a narrower fact than first
written (replay needs no durable authority at all); **¶DEV-2** —
`route_line` never calls `CoreSession.retrieve`, so `twin_lookup` was never
line-answerable and became the second *conditional* task kind, with W1
joining W2 as a named wiring step.

**Demonstrate.** `docs/SPEC-chat-completions-skin.md` ¶DEV-1 (§1) and ¶DEV-2
(§9); the corrections quoted back into
[DESIGN-grounded-throughput](DESIGN-grounded-throughput.md) §3 and
[ROADMAP-v0.17](ROADMAP-v0.17.md) item 1.

### Twins and closures reached the typed line, behind gates the review made honest

**Before.** `CoreSession.retrieve` could surface twin material and
`closure_query.py` could answer reachability, and neither was reachable
from a line a person types.

**Now.** `twin <statement-id>` filters the twin ledger to groups that
actually list the queried id (the miss chain also returns alias-matched
groups naming *other* statements' members — a receipt about this id must
not quote those), strongest level first. `reachable <world-id>
<target-path>` runs `closure_query` against the committed closures behind a
new `closure.worlds` boot probe registered `optional=False` on purpose — the
optional flag means a dependency family the offline boot forces OFF, and
committed files are not that, so P-IH1 stays green and the offline kernel
profile still serves W2. Eight byte-exact closure targets are committed in
`data/closure_targets/`, seeded and arm-verified by calling the query and
refusing on disagreement.

Two High findings from the adversarial review are the reason this is worth
reading: **any repository file could be minted into a certified bounded
negative** (now only manifest-registered targets with a matching `world_id`
answer, everything else refuses by name), and **a truncated committed
closure crashed `route_line` instead of refusing** (now load/read/query
share one try, with the exception class in the detail).

**Demonstrate.**

```
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"twin algtop.homology.chain_rank_nullity"}]}'
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"reachable story.golden_chicken data/closure_targets/story.golden_chicken.reachable.0.state.json"}]}'
python -m unittest tests.test_wiring_routes
```

### The task book: 119 questions whose answers existed first

**Before.** The v0.14 clarification holdout was spent discovering that its
author's belief about the collection was wrong. The lesson: the receipt has
to exist before the question does.

**Now.** `experiments/throughput_tasks.json` — 119 tasks, seven kinds, 94
answerable (70 with both conditional kinds dropped; T3's floor is 50),
halves assigned by a frozen hash rule with half B sealed until the
registered run. `scripts/build_throughput_tasks.py` computes every expected
record itself from committed artifacts and can **prove it never ran the
engine**: stdlib-only imports, AST-extracted tables, quoted labels asserted
against module source, a clean-imports guard verified in the building
process, and a test that re-derives the guard from the builder's own AST.
The `scoring_rules` live in the book header so nothing is arguable after the
numbers land. The seal witness is the canonical-LF digest of eleven
rendering modules; the suite goes red if any of them changes, and the run
revalidates them before timing anything.

Two review rounds re-derived **the entire answer key independently** — 46
recomputed values, 73 verbatim artifact quotes, **zero disagreements** — and
reverified the frozen half rule over every task, with the shipped pool
ordering shown *less* hash-favorable than the alternatives it declined. What
review added before the seal, while adding was still legitimate: the
per-kind half-B floor was raised from 3 to 5 (at 3, T5's 80% gate turned on
a single answer), and coverage was widened where a dumb contender could have
pattern-matched — relation truth decorrelated from the operator glyph with
every false relation off by exactly one, non-integer and negative exact
values, all five twin levels, both world-fact narration forms.

**Demonstrate.** `python -m unittest tests.test_throughput_tasks` (53
tests); the counts block and `scoring_rules` are the book's own header.

### The baseline was pinned before K, and amended only before the run

**Before.** This repository had never measured itself against a language
model on **throughput, latency or cost per answer** — a sweep of BACKLOG
and every TRIAGE record on 2026-08-21 found no prior mention of any of the
three. (Capability comparisons against blind and learned baselines are
older than that and are not what this bullet claims.)

**Now.** `experiments/throughput_baseline.json` pins Qwen3-4B-Instruct-2507
(Apache-2.0, non-thinking, Q4_K_M, weights digest-pinned) on ollama 0.32.15,
vendor sampling untouched, tokenizer digest-pinned under the WordNet
refuse-not-skip rule — counting **refuses** (exit 2) when the tokenizer file
is absent or mismatched, because cannot-verify is not skip. The host is the
same throttled laptop, and **the GPU goes to the contender** while the
kernel stays CPU-bound I/O. With that commit, K = 5 froze.

Two amendments were made **before any timed run**, each dated in the
manifest: server-side context set to 32,768 via `OLLAMA_CONTEXT_LENGTH`
after review proved live that the `/v1` layer drops a `num_ctx` body field
(the earlier amendment was inert, and would have let ollama truncate the
grounded arm at its 4,096 default — inflating K by the exact mechanism the
manifest claimed to prevent), with 262,144 shown unrunnable on a 16 GiB GPU;
and the quote-verbatim prompt (`441ec91`) after a 5/45 half-A trial showed a
paraphrasing contender makes T4 vacuous.

**Demonstrate.** `experiments/throughput_baseline.json` —
`runtime.context.amended`, `arms.B-grounded.prompt_template_amended`, and
`arms.B-grounded.session_derived_kinds_note`, all dated, all pre-run.

### The skin: two profiles, zero rendering freedom

**Before.** No HTTP surface.

**Now.** `scripts/serve_chat.py`, stdlib only, loopback only, two profiles
over the two shipped session objects (`corollary/kernel`,
`corollary/conversation`), replay-per-request with a prefix-hash identity
and a replay-equivalent cache, SSE streaming whose deltas concatenate
byte-for-byte, a capability sheet generated from the live objects — never a
hand-maintained copy that can rot — with a build-time P-IH3 demo-name lint.
`content` is the verbatim pass-through of the engine's rendered answer and
nothing else; everything else rides in `x_corollary`.

A fresh-eyes adversarial review **could not construct any path** where
served content carries a byte the engine did not render — 200 KB lines, RTL
unicode, prompt injection, essays requested and refused — with the T2 oracle
re-implementing the join rule independently and mutation-checked for
vacuity. The one High: the transcript-divergence check paired assistant
claims FIFO instead of most-recent, rejecting truthful transcripts with
consecutive user turns. Fixed, and pinned from both directions.

**Demonstrate.** `python -m unittest tests.test_serve_chat` (68 tests);
`curl -s http://127.0.0.1:8377/v1/capabilities | python -m json.tool`.

### The stopwatch was built outside the machine it times

**Before.** No client-side timing harness existed, and nothing prevented one
from being written against the server it grades.

**Now.** `scripts/measure_throughput.py` speaks only the public HTTP API and
imports no engine module — AST-verified, plus a clean-imports guard that
runs *before* the result is written. It counts useful tokens with the
digest-pinned baseline tokenizer and refuses to count without it, scores the
sealed book's rules verbatim, and records in the result file every
interpretive choice a reader could otherwise argue about after the numbers
land: both metric readings (the T4 median and the design §3 aggregate, with
the refusal time-charge shown inert under the median and biting under the
aggregate), the B-side label-strip correctness rule with per-task residuals
(committed pre-run), sampling as requested-versus-applied, and observed
context against per-task `materials_tokens` so truncation is evidence rather
than a surprise. `scripts/dump_server.py` is control C1 incarnate. C2
derives **offline** from a result file, so the sealed half is never executed
twice.

**Demonstrate.**

```
python scripts/measure_throughput.py --system kernel --url http://127.0.0.1:8377 \
    --half A --out halfA.repro.json
python -m unittest tests.test_measure_throughput
```

Half A is the development half and needs no consent; `--half B` refuses
without `--registered`.

### The boot tax: the first trial timed a JSON parse

**Before.** The first half-A trial read **83 tok/s**. Every HTTP request
paid ~460 ms of `CoreSession.boot` in the live profile — 389 ms in the
commit's controlled measurement, the difference being serving load — and
405 ms of that was `UnifiedKnowledgeStore.load` re-parsing every committed
corpus, uncached, on every boot. The benchmark was measuring a cold cache,
not the mechanism the thesis claims.

**Now.** The store load is memoized on the resolved path triple. Boot **389
ms → 7.5 ms**; a definition task end-to-end over HTTP **674.8 ms → 7.5 ms**
median, back-to-back, bodies byte-identical. The shared-instance hazard was
audited by **AST, not grep**: every attribute written only at `__init__`,
frozen types throughout, and the single genuinely mutable path bypasses the
cache by construction — with two *interleaved* conversations through the
shared store matching fresh boots line for line, interleaved because a
serial test would hide exactly the leak being denied.

`scripts/retrieval.py` is a seal-witness module, so **the book was re-sealed
in the open** under a re-sealing rule added to the spec before the run:
byte-identity proven, the rebuild moves exactly one digest leaf, 119 tasks —
ids, halves and expected records — byte-identical, half-B seal undisturbed.
After the registered run the original sentence stands unqualified: a change
to a witnessed module voids the run.

**Demonstrate.** `025bd73`; the pre-fix number is in that commit message,
the post-fix half-A trial is
`experiments/throughput_trial_kernel_halfA.json` (median 2,207.8 tok/s), and
the registered run is `experiments/throughput_result.json`.

## Discoveries of the cycle

Quoted from [DISCOVERIES](DISCOVERIES.md):

- *"A benchmark that times a cold cache measures the cache."* 83 → 3,451
  tok/s with zero rendered bytes changed, and a sealed book re-sealed in the
  open to keep the fix honest.
- *"A grounded model must be told to quote, and even then it delivers
  fragments."* And the instruction did not move the score. The committed
  half-A trial carries the *amended* manifest's digest and reads 5/45; the
  5/45 attributed to the unamended prompt rests on the manifest's own
  rationale text rather than a second committed file. Registered: 4/49. The
  exact-content contract is the thesis's own diagnostic.
- *"The reviews were the instrument."* Any-repo-file-as-certified-negative,
  the inert `num_ctx`, an independently re-derived answer key with the
  hash-shopping alternatives shown declined, and a skin whose honesty could
  not be broken by a fresh adversary.
- *"WAITING crossed the wire without anyone inventing a value."* P-IH6,
  registered in v0.10 and unadjudicated through five parks, fired — with
  wire-falsifiable negatives.
- *"The corpus outgrew its own template grammar, and nothing had asked it
  to."* The v0.18 cycle's first finding, produced during this rotation:
  reviewing the forward design falsified its own 90%-of-12,777 floor by
  measurement — only **2,172 of 12,777** canonical terms (17.0%) parse at
  all, and the corpus that is 97.9% of the mass parses at 16.3%.

## Resolved from BACKLOG

- The **Chat Completions–compatible HTTP skin (Phase 4)** entry:
  **RESOLVED**, annotated with a dated note in place rather than pruned,
  because its park history (v0.13, v0.14, v0.15, ROADMAP-v0.16 §3,
  ROADMAP-v0.17 §3) is the drift record this repository keeps deliberately.
  P-IH6 is adjudicated there too.
- The `unrestricted prose authoring (item 9, still last)` language is
  updated: it is no longer last, it is the v0.18 headline, and it now points
  at [DESIGN-sans-template-rendering](DESIGN-sans-template-rendering.md).
- **Newly filed** this cycle: the context-probe defect (the grounded arm's
  bound read from `/api/show` because `/api/ps` was empty before the model
  loaded), the `_route_ownership` receipt duplication with its seal-cycle
  reason, the B-side notation asymmetry, and the open-English input synonym
  layer pointed at the sans-template design's §10 follow-on.

## Honest limits carried forward

- **At the median, K is satisfied but not measured.** T4 gates on the
  median of the per-task ratio, and the contender's median is zero, so the
  gate is met by a division that has no finite value. The number a reader
  can hold — 220× — is the *aggregate* reading, which is the design's §3
  sentence rather than T4's. Both are computed, labelled and committed in
  every result file's `metric_reconciliation`, and this release quotes both
  rather than the flattering one.
- **The grounded arm's secondary-median bound in its result file reads
  262144, and that is wrong.** The context probe ran before the model
  loaded, so `/api/ps` was empty and the code fell back to `/api/show`,
  which reports the model's *capability*, not the served context. The served
  context was 32,768 — proven five times in the same file by oversize HTTP
  400s reading `request (130475 tokens) exceeds the available context size
  (32768 tokens)`. The corrected restricted median over the
  recorded `materials_tokens` is **0.0 over 44 tasks**, so the verdict is
  unchanged. Filed in BACKLOG; the code was left exactly as it ran.
- **Closure materials do not fit this GPU in any configuration.** The
  largest MATERIALS block is ~130 k tokens; 32,768 was already the largest
  context whose KV cache fits 16 GiB. Five tasks errored 400 and are
  disclosed per task, not dropped. (The manifest disclosed the ~130 k figure
  before the run.)
- **`_route_ownership` recomputes its lookup for the receipt**, roughly
  doubling that route's cost. The fix belongs in `harness.py`, which was a
  sealed rendering module until the registered run completed, so it was
  declined deliberately and flagged rather than smuggled in. Filed.
- **B-side correctness on session-derived kinds is notation-limited.**
  `belief_query` and `exact_value` hand the model no materials, and their
  checks require kernel notation (`located_in(x) = place`, exact fractions)
  a prose model rarely emits unprompted. Recorded in the manifest before the
  run; per-kind results let a reader weigh it.
- **83 tok/s is the number from before the memoization.** The trial files
  tell that story; the number this release quotes is the registered one, and
  the two are not the ends of a speedup claim.
- **The claim covers the registered paths and nothing else.** No open-domain
  parity, no open-English input, no multi-tenant auth, no claim about larger
  models or other runtimes. Durable session restore over HTTP stays unshipped
  and unclaimed (¶DEV-1).
- **The small-model lane read out symbolic-only**, which is honest and is
  also a lane that has not moved this cycle.
- A passing Python test is not a Lean proof.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.** `git diff
--name-only v0.16.0..HEAD -- data/ experiments/` lists twenty-one paths and
**not one `.py`**: eight committed closure-target states plus their
manifest under `data/closure_targets/`, and twelve
`experiments/throughput_*.json` ledgers (the pinned baseline, the sealed
book, five registered results, five half-A trials). No training corpus
moved and no `experiments/*.py` changed, so the checkpoints attached to
**v0.6.0** remain accurate for this release. Committed in-repo instead, and
linked by path rather than uploaded: `experiments/throughput_tasks.json`,
`experiments/throughput_baseline.json`,
`experiments/throughput_result.json`, `experiments/throughput_result_bgrounded.json`,
`experiments/throughput_result_bungrounded.json`,
`experiments/throughput_result_dump.json`,
`experiments/throughput_result_c2.json`, the five
`experiments/throughput_trial_*_halfA.json` files, and the eight byte-exact
targets in `data/closure_targets/`.

## The outside design inquiry, discharged in the open

ROADMAP-v0.17's release gate required the v0.18 design inquiry to be
"discharged — run, or explicitly reaffirmed with the receipt named". It was
**not run for v0.18**. The standing receipt is
`reports/design-direction-v0.17.json`, whose selected direction —
ledger-first claims — is parked with its reason, and v0.18's headline came
by maintainer direction coinciding with a trigger DESIGN-grounded-throughput
§10 registered *before* the run that fired it.

Three things are recorded rather than absorbed, all in
[ROADMAP-v0.18](ROADMAP-v0.18.md) §4. **The obligation converts to the v0.19
gate**, and the brief that discharges it must carry **both** readouts — this
cycle's throughput result and v0.18's realization result, whichever way R1
lands — because carrying only the flattering one would make the course a
ratification. **A wording conflict between two governing texts was resolved
in the open**: ROADMAP-v0.17's clause is looser than the release skill's
own ("invoke the design-direction gate exactly once before drafting the next
roadmap"), this cycle is cleared under the roadmap wording, and that
resolution is scoped to this cycle only — v0.18's own release gate restores
the strict form, so the reaffirmation was available once and is not
available again by inheritance. **A third consecutive maintainer-directed
headline** would need a written amendment to the course gate itself, which
is the maintainer's decision and not a rotation's.

Separately, the instrument-first-headline suspension
(DESIGN-grounded-throughput §9) was scoped "for the v0.17 cycle" and its
lift trigger — a product-lane failure naming a missing instrument — never
fired, because the product lane did not fail. It is neither lifted early nor
extended by silence: it expires with its cycle, recorded, because an
unrecorded expiry is the same drift as an unrecorded park.

## The release refresh

Every generated ledger was regenerated on the tip and the working tree came
back byte-clean: 25 seeds byte-identical (`check_regeneration.py`), 12,777
nodes across 27 corpora valid (`validate_nodes.py`), `signature_matches`,
`specializations` and `compression` clean, `ingest_wold.py reach` re-run
against the pinned archive (1,395 of 1,460 core LWT meanings map, 95.5%;
1,394 of them through WordNet lemmas), and `check_report_regeneration.py`
reporting three ledgers clean with `decompositions.json` a **declared**
divergence carrying its TRIAGE-v0.11 citation.

## The suite at the tip

[SUITE-GATE-V17: full-suite verdict and timing at the frozen v0.17 tip land
here before the tag; the v0.16.0 receipt (1,427 tests, 0 failures, 3
skipped, 20,837.8 s, `reports/test_gate_v016/run2-green.time_tests.log`) is
the baseline, and this cycle adds four wholly new test modules —
`test_measure_throughput` (124), `test_serve_chat` (68),
`test_throughput_tasks` (53), `test_wiring_routes` (33).]

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/check_report_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py

# 1. boot the endpoint (loopback, offline boot, no auth, no flags needed)
python scripts/serve_chat.py

# 2. read the capability sheet the way an orchestrator would
curl -s http://127.0.0.1:8377/v1/capabilities | python -m json.tool

# 3. one exchange on each of the three routes the cycle wired or measured
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"owns x ^ 2"}]}'
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"twin algtop.homology.chain_rank_nullity"}]}'
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"reachable story.golden_chicken data/closure_targets/story.golden_chicken.reachable.0.state.json"}]}'

# 4. run the stopwatch on the development half (half B refuses without --registered)
python scripts/measure_throughput.py --system kernel --url http://127.0.0.1:8377 \
    --half A --out halfA.repro.json

# 5. the gates, by name
python -m unittest tests.test_serve_chat tests.test_throughput_tasks \
    tests.test_measure_throughput tests.test_wiring_routes
```

Counting useful tokens needs the digest-pinned tokenizer named in
`experiments/throughput_baseline.json` (`tokenizer.file`, gitignored); the
stopwatch **refuses** rather than approximating when it is absent, so step 4
reports cannot-verify without it. Reproducing the baseline arms
additionally needs ollama 0.32.15 with the pinned model and
`OLLAMA_CONTEXT_LENGTH=32768`.
