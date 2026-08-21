# Grounded tokens arrive at wire speed

**Status: design only.** Nothing here is implemented. First slice targets
v0.17, superseding the ledger-first-claims headline **by maintainer
redirect, 2026-08-21** — recorded below in §2, because a direction
change without a recorded decision is the attrition this repository
keeps catching in itself.

## 1. The boundary being moved, and the claim

The project's founding thesis is that everything with a closed form
belongs in inspectable code, with weights carrying only the graded
residual. Sixteen releases have defended that thesis with instruments.
What has never been demonstrated is its *consequence for a consumer*:

**A microkernel — small programs plus, optionally, small models —
grounded by extrinsic data, algorithmic comprehension, and logic,
delivers useful answer tokens many-fold faster than a language model
generating the same content from weights.**

The mechanism is structural, not clever engineering. An autoregressive
model *samples* every token, so its ceiling is decode rate. The kernel
*copies and computes* most of its tokens — person-authored corpus
sentences, exactly evaluated values, replayed receipts, sealed-closure
verdicts — so its ceiling is I/O. Grounding does not merely make answers
more trustworthy; it moves answer delivery into a different throughput
class. That is a measurable claim with a falsifiable gate, and it has
never been registered anywhere in this repository (a sweep performed
for this design, 2026-08-21, found zero prior mention of throughput,
latency, or cost-per-answer across BACKLOG and every TRIAGE record;
the sweep's corrections landed as that day's dated hygiene notes in
those files).

What a person gains if the gate fires: the knowledge graph becomes a
**conversational surface any agent harness can attach to** — an
OpenAI-compatible chat-completions endpoint where codex, claude,
copilot, or opencode-class orchestrators drive the kernel like a model,
receive receipt-bearing answers at wire speed, and get honest WAITING
questions and refusals instead of confabulation.

## 2. Why this direction, and what it supersedes

This design was not selected by an outside course; it was **directed by
the maintainer** (2026-08-21), who named the drift it corrects: three
consecutive cycles whose center of gravity was the project's own
evidence apparatus — the coincidence veto (v0.15), the retraction
radius (v0.16), and the planned citation discipline (v0.17 draft) —
whatever each roadmap's headline labels said, while the conversational
surface the roadmaps have carried since v0.7 sat parked five cycles. The instruments were real and are kept; the drift
was headline selection, and the recorded governance answer to a
maintainer decision is to write it down and build. The v0.17 course's
receipt (`reports/design-direction-v0.17.json`) and the hardened
[DESIGN-ledger-first-claims](DESIGN-ledger-first-claims.md) stay on
file, preregistration-ready; that design **parks whole** with its
unpark named in ROADMAP-v0.17 §3.

The substrate design this one stands on is
[DESIGN-interactive-harness](DESIGN-interactive-harness.md), whose
Phases 0–2 are shipped and adjudicated — P-IH1/P-IH2 in
`tests/test_session_offline.py`, P-IH7 in
`tests/test_session_dispatcher.py`, with the registered-paths and
boot-honesty commitments (P-IH4, P-IH5) enforced across the line-surface
and retrieval suites; all green in the v0.15 gate and v0.16's green run
(`reports/test_gate_v015/`, `test_gate_v016/run2-green`). Phase 4, the
Chat Completions skin, was specified in §4.3 with its architecture rule
(A-IH6: one session engine, two skins) and its falsifiable prediction
(P-IH6: WAITING crosses the HTTP boundary without anyone inventing a
slot value). The five-cycle park on that phase cited a blocker —
durable session authority bound to a verifier instance — that
ROADMAP-v0.7 item 2 has since **fixed** for the shipped scope
(`ConversationSession.restore` over a signed ledger snapshot and a
derivable key ring; one owner, one session, restored in one place at a
time), a fact the v0.16 park paragraph had not caught up with. What
item 2 deliberately did NOT solve stays unsolved and in scope-bounds
here: session forking (two clients importing one snapshot, P-DS7) and
multi-owner storage. The skin is unblocked in fact for the
single-session scope and was unscheduled by choice. This design
schedules it at that scope.

## 3. The first-class objects

**The skin** — `scripts/serve_chat.py`: an HTTP server exposing a
subset of `POST /v1/chat/completions` over the existing `Session` /
`ConversationSession.restore` engine, per DESIGN-interactive-harness
§4.3. One session engine, two skins: the server is a *renderer* over
the same structured trace events the TTY renders — verdict, evidence
ids, capability matrix, and collapsed-trace id ride in vendor extension
fields; WAITING returns as an assistant turn carrying the need record;
the client's next message resumes it; streamed tokens are only ever
renderings of accepted content. No token is sampled from a generative
model anywhere in the serving path this cycle.

**The language boundary, stated before anyone is disappointed by it.**
The engine speaks the harness's **registered line grammar** — the
bounded, documented request surface the typed prompt already accepts —
and open English stays substrate Phase 6, not smuggled in here (`owns
x ^ 2` routes; "who owns x^2?" does not, and will not this cycle).
"Any agent harness can attach" is still true in the way agents attach
to every CLI tool: the attaching orchestrator adapts to the tool's
grammar. The skin therefore serves a **capability sheet** — the line
grammar, the registered paths, and the boot matrix — as a vendor
extension an orchestrator can read once and self-configure from, the
way it reads a tool schema. Task-book turns are written in the
registered grammar; nothing new becomes answerable this cycle, and
that sentence stays true.

**The task book** — `experiments/throughput_tasks.json`: N ≥ 100
preregistered conversations, each a typed record:

```text
task_id, kind ∈ { corpus_definition | exact_value | twin_lookup |
                  closure_reachability | belief_query | refusal_due |
                  clarification_due },
                # closure_reachability is CONDITIONAL: closure_query.py
                # is a standalone CLI today, wired into no session
                # route. Item 1 carries the wiring as a named step; if
                # unwired when the task book seals, the kind is dropped
                # from the book with that reason recorded, not padded.
turns[] { role, content },
expected { outcome ∈ answer|refuse|ask, check ∈ exact|receipt|verdict,
           artifact_refs[] },
half ∈ A|B          (assigned by frozen hash rule; B sealed until the run)
```

Answerable tasks are constructed FROM committed artifacts (the receipt
exists before the question does — the lesson of the spent v0.14
clarification holdout); refusal tasks are verified absences.

**The stopwatch** — `scripts/measure_throughput.py` plus
`experiments/throughput_result.json`: a client-side harness that speaks
only the public API (no imports from the serving process), records per
task: wall-clock to first token, wall-clock to stream end, token count,
correctness verdict against `expected`, receipt-coverage bit. **Useful
tokens are defined exactly**: the tokens of the assistant message
`content` field only — the rendered answer text — under the pinned
baseline tokenizer (one tokenizer counting both contenders); vendor
extension payloads, receipt structures, ids, and digests never count.
Perceived throughput for a system = useful tokens ÷ client wall-clock,
where the numerator counts only correctly-and-receipted answers, the
denominator counts every task's elapsed time, and an answerable task
the system REFUSES contributes zero tokens plus a frozen time charge
equal to that system's slowest correct answer — so a refusal is never
a cheap way to shed a hard task's clock. Speed at being wrong, and
speed at declining, both score as slowness.

**The baseline manifest** — `experiments/throughput_baseline.json`,
committed BEFORE any measurement and before K freezes: the comparison
model (a small open-weights instruct model), its runtime, quantization,
tokenizer digest, sampling settings, and the host hardware — the same
throttled machine the kernel runs on, which favors the baseline (the
kernel is CPU-bound I/O; the model gets the GPU). The baseline runs
**two arms**: **B-grounded**, the gated contender, receives the same
committed artifacts the kernel's answer rests on, injected into its
context, and must decode the answer — this is the arm that isolates
the mechanism, because a grounded model can be RIGHT and is still
bound by sampling rate, so "many-fold" measures the delivery class
and not the model's ignorance of a private corpus; and **B-ungrounded**,
reported but never gated, the same model answering cold — expected to
fail correctness on corpus-specific tasks, kept because the gap between
the arms is itself the grounding story told in numbers.

## 4. Trusted and untrusted

Trusted: the committed artifacts the answers are copied/computed from;
the session engine's verifiers; the task book's expected records (each
carrying its artifact refs). Untrusted and measured: the skin's protocol
fidelity (T1), its honesty under an adversarial client (T2), the
throughput claim itself (T5), and any learned component in the dispatch
path (T6 — capability-blind baseline mandatory, the house bar).

## 5. Smallest slice

Serve the existing session engine — nothing new becomes answerable this
cycle — through the skin; author the task book from what the engine
already answers (corpus definitions, exact evaluation, twins,
visibility-derived belief, the refusal/ask sets, and — if the one named
wiring step lands — the sealed closures' reachability receipts); run
the stopwatch against the kernel and both baseline arms once. The
demonstration a stranger can run: point any OpenAI-compatible client at
`serve_chat.py`, read the capability sheet it serves, and speak the
registered grammar it teaches.

## 6. Construction gate (numbers frozen here)

- **T1 — an unmodified client completes the triangle.** A stock
  OpenAI-compatible client library, unforked, completes: one answerable
  query returning a receipt-bearing answer; one WAITING round-trip
  resumed by the next user message; one refusal delivered as a refusal.
  This adjudicates **P-IH6** as registered in the substrate design.
- **T2 — honesty crosses the wire.** Every P-IH4 refusal case in the
  task book stays refused at the API; no response ever contains a token
  that is not a rendering of accepted content (enforced by construction
  — there is no generative path — and probed by an adversarial-client
  test that tries to elicit free text).
- **T3 — the task book precedes the answers.** Committed, halves
  assigned by hash, half B sealed, before `serve_chat.py` first answers
  any task. Fewer than 50 answerable tasks is a **stop** (§8), not a
  softer label.
- **T4 — the baseline is pinned before K.** `throughput_baseline.json`
  committed before any timed run; then **K = 5** freezes: the kernel's
  median perceived throughput over half-B answerable tasks must be
  ≥ 5× **B-grounded's**, at correctness ≥ B-grounded's, with median
  time-to-first-useful-token also lower. "Many-fold" is claimed at 5×;
  the measured multiple is reported whatever it is, and B-ungrounded's
  numbers are reported beside it unscored.
- **T5 — usefulness gates throughput.** Correctness and receipt
  coverage are scored before any speed number is read. The kernel must
  answer ≥ 90% of half-B answerable tasks correctly with receipts
  **overall and ≥ 80% within every kind** (a whole kind cannot be
  sacrificed to the average), refuse 100% of the refusal set, and
  surface a renderable WAITING need on 100% of the `clarification_due`
  set; below any of those, the throughput comparison is not run and
  the miss is the result.
- **T6 — the small-model lane degrades honestly.** If a learned
  component (ranker or router) operates in the serving path, it ships
  with its capability-blind baseline measured on the same tasks and
  loses nothing on T2/T5; if none is ready, the lane ships
  "symbolic-only this cycle" in writing. A learned component may never
  be the difference between refusing and answering.
- **T7 — receipts survive the transport.** For 20 sampled answers, the
  vendor-extension receipt fields are re-validated from the client side
  against the committed artifacts they cite (the detached-receipt
  lesson, imported as one clause, not a cycle).

## 7. Blind controls, each with its voiding sentence

- **C1 — the dump server.** A server that streams corpus text at
  maximum rate, ignoring the query: raw bandwidth incarnate, and under
  a correct metric it scores approximately zero. *If C1's perceived
  throughput exceeds 1% of the kernel's, the metric as implemented is
  crediting bandwidth, and the metric is void.* (The clause guards the
  implementation of the denominator, which is where a metric quietly
  rots; a C1 score of zero is the expected reading, not a vacuous one,
  because the same scoring code produced it.)
- **C2 — the shuffled kernel.** The kernel with answers permuted across
  tasks: fast, receipt-shaped, wrong. *If C2's perceived throughput
  exceeds 1% of the kernel's, either the scoring or the task book's
  expected records fail to separate right from wrong answers, and the
  run is void.*
- **C3 — the grounded baseline may win.** B-grounded is a genuine
  contender, not a prop: it holds the same artifacts and can be fully
  correct. *If B-grounded meets or beats the kernel on perceived useful
  throughput at equal correctness, the thesis is falsified at this
  scale — sampling was not the bottleneck — and that is the published
  result.*

## 8. Stop conditions and non-claims

Stop and publish if T1 cannot be met without forking the client (the
API subset was mischosen); if WAITING cannot cross the boundary without
an invented value (P-IH6 misses — the substrate prediction fails, which
outranks this design); if the task book cannot reach 50 answerable
tasks under the sealed rules (the engine's registered surface is
thinner than believed — a finding about the product, not the
benchmark, and the one rule for that case: stop, no "exploratory"
relabeling).

Non-claims, stated hard: **no open-domain parity** — the claim covers
the registered paths and nothing else, and the released numbers say so
in the same sentence; **no sans-template generality this cycle** —
answers render through the existing realization layer (person-authored
sentences, linearized terms, computed values); unrestricted prose
authoring stays Phase 6 of the substrate design and is not smuggled in
as a throughput feature; **no multi-tenant auth**, one owner, one
session, per the substrate's shipped contract; **the baseline is not
strawmanned** — it runs with the GPU, warm, at its vendor-recommended
settings, and its tokenizer counts both sides.

## 9. The habit suspended

For the v0.17 cycle, **instrument-first headline selection is
suspended**: no new governance or meta-evidence instrument may be a
roadmap headline item. Scope: headline selection only — the shipped
instruments keep running (the regeneration check stays in the release
refresh; receipts stay receipts) and small instrument fixes ride as
minor items. The suspension lifts when a product-lane failure names a
missing instrument, which is the direction dependency running the way
the maintainer redirect says it should.

## 10. How status lands

The preregistration order: this design; the skin's protocol subset and
trace-to-API mapping (a short committed spec, since P-IH6's adjudication
quotes it); the task book with sealed half; the baseline manifest; then
implementation; then the one registered run. Fires, misses, folds, and
voids land together in ROADMAP-v0.17, ANALYSIS, DISCOVERIES, and
BACKLOG; the v0.17 release blog's forward section follows from this
document. If T4 fires, the question that becomes askable next is the
cost ledger — answers per joule and per dollar against hosted-model
pricing — and the sans-template rendering boundary (substrate Phase 6)
becomes the next surface with a measured floor under it.
