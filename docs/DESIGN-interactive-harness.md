# Design: interactive harness — microkernel agent OS over a verified world

Source conversation: 2026-08-09 (directional plan on integrating demos into one
agent-like experience; model composition; offline degradation), with review
corrections that reject a “slash-command demo launcher” in favor of a
**capability-driven session**: the system decides what is missing and how to
fulfill it along **registered paths** only. (“Registered” is deliberately not
“proven”: PROVEN is reserved for digest-pinned Lean artifacts. A registered
path is one a probe-initialized subsystem declared and the kernel will let a
verifier adjudicate; registration is not a verdict.)

Status: **kernel and dispatcher shipped; the live prompt did not.**
> **Status correction (2026-08-21):** the line above is stale and kept
> for the record. The live typed prompt SHIPPED at v0.12 and has grown
> since (`scripts/harness.py` reads lines, routes the registered
> grammar, answers with receipts, and asks/refuses; RELEASE-v0.14.0's
> drift audit retired the "claims a live session it does not have"
> warning with a runnable demonstration). Phases 0–2 of §9 are shipped
> and adjudicated (P-IH1/P-IH2 in `tests/test_session_offline.py`,
> P-IH7 in `tests/test_session_dispatcher.py`); Phases 3–6 are not.
> Phase 4 is scheduled by
> [DESIGN-grounded-throughput](DESIGN-grounded-throughput.md)
> (ROADMAP-v0.17 headline). Some §10 adjudicating-test names below
> predate the tests as landed; the tests themselves are authoritative.
`scripts/harness.py` prints a boot list and exits.
`scripts/dispatcher.py` routes registered paths.
`scripts/session_run.py --check` re-verifies one recorded session.
There is still no “read a goal, loop until done.” That first typable
slice is [DESIGN-live-session.md](DESIGN-live-session.md) (v0.12
item 5). Chat-shaped HTTP, multi-turn memory across two typed
lines, and open-English authoring of new nodes remain later. The
domain-neutral controller, frame executor, retrieval ASK channel,
story adapter, live Lean search, and specialist experiment models
already exist as libraries. This file is how they become one live
experience; do not read “shipped” in v0.8's notes as that
experience. Indexed from `docs/BACKLOG.md` (“Interactive
harness / agent OS”) and related to `docs/DESIGN-frames-and-retrieval.md`,
`docs/DESIGN-concept-tokens.md`, and `docs/ROADMAP-v0.7.md` items 2
(conversation across process boundaries, bounded request grammar), 6
(retrieval becomes tool use, miss chain, typed protocols), 7 (external trust
roots), and 9 (rendering and open-language requests). ROADMAP-v0.6 is closed
and historical; its conversation/policy threads live in the v0.7 items above.

---

## 1. Product claim (what this is not)

This is **not**:

- a menu of canned demos (`/tom`, `/golden_chicken`, `/demo_answer`);
- a chat LLM that free-generates answers and only later “checks” them;
- a neural MoE that soft-routes among incompatible checkpoints as if they were
  one brain;
- a product that requires WordNet, Wikipedia, Lean, or Torch to boot.

This **is**:

- a **microkernel agent OS** whose kernel is the propose → verify → trace
  controller (`scripts/controller.py`);
- **subsystems** (story mechanics, belief/visibility, retrieval stores, Lean
  search, optional neural tools) that register only when probe-initialized;
- a **session** that mutates live symbolic state under verifier rules;
- an **I/O surface** (CLI first, optional Chat Completions–compatible HTTP
  later) that looks agent-like: the system pauses for input when it needs it,
  shows verdict-colored status, and collapses intermediate trace by default.

The competitive surface is closer to an **auditable reasoning console / agent
kernel** than to an unrestricted assistant—and that is intentional.

---

## 2. What is already live vs what demos freeze

Review question: is golden-chicken a static module, or can it be dynamically
mutated in a live session? Same question for Sally–Anne and other “demos.”

### 2.1 Mechanics are live; demos are frozen policies

| Layer | Dynamic today? | Evidence |
|---|---|---|
| Story **adapter** (`StoryVerifier`) | **Yes** | Accepts `GEN` actions (`introduce`, complication/resolution beats, `plant` / `discharge`) and mutates `StoryState` / frame obligations under narrative constraints. Wrong order → REFUTED; missing trait → UNKNOWN; closed frame → REFUSED. |
| Story **oracle demo** | **No (scripted)** | `story_oracle_actions()` + `SequencePolicy` emit one fixed golden-chicken path. That path is a regression fixture, not the product API. |
| User-frame **bindings** | **Yes** | `ConversationSession` can open slots, ASK → WAITING, accept signed replies, supersede values (silver → copper), isolate owners (Alice vs Bob). Public story beats stay shared; private bindings do not enter `frame.asserted`. |
| Belief / ToM | **Yes (event-driven)** | Visibility-filtered `observe_event` derives false belief. The Sally–Anne script is a fixed event log; the executor is general. |
| Retrieval | **Yes** | Any key against five committed stores (+ optional WordNet). Demo CLI is one query, not the limit of the store. |
| Lean search | **Partly (backend general, target hardcoded)** | The generality is the Pantograph backend and BFS over registered tactic palettes; the *proposition* is not yet a parameter—`prover/live_search.py:83-84` hardcodes `HELD_OUT_THEOREM` / `HELD_OUT_PROPOSITION` (one held-out `Init` prop). Turning that into a versioned theorem set is ROADMAP-v0.7 item 1, not a harness deliverable. |
| Neural tools | **Offline specialists** | Separate processes/checkpoints; not session-native tools yet. |

**Design consequence:** the interactive system must expose **mechanics and
subsystems**, not demo scripts. Golden-chicken remains a **bootstrap fixture
and test** (like a kernel self-test), not a user-facing “mode.” A live session
opens *a* fiction frame (or reuses a declared frame), proposes beats or
accepts user-proposed content through the adapter, plants/discharges
obligations, and revises private slots—without a slash command named after the
poultry.

**Honest limit today:** open-English story authoring and free beat text are not
fully general; the adapter still expects structured action arguments. Live
mutation is real for **structured** transitions and user bindings; unrestricted
prose story-writing is a later surface (roadmap renderer / open-language
boundary), not a claim that the oracle sequence is already an LLM.

### 2.2 ASK is a channel, not a user-invoked command

Review question: should the user have to prompt `/ask`?

**No.** The controller already has `StopReason.WAITING` when
`is_waiting(state)` holds after an accepted ASK. That is the same shape as a
tool call in agent REPLs:

```text
policy/subsystem proposes ASK(slot)
verifier accepts → state.awaiting set
controller stops WAITING
shell/API: present question to human (or external agent)
shell/API: inject authenticated reply as next action
controller resumes until SOLVED | WAITING | EXHAUSTED | BUDGET | REFUSED path
```

User-facing product rule:

- If an input channel is available (TTY, WebSocket, HTTP turn), **WAITING is
  always surfaced** as a system question with pulsing/waiting chrome.
- The human never needs to know the word ASK.
- If no input channel exists (batch job), WAITING is a terminal stop with a
  machine-readable need-input record—not a hallucination of the slot value.

This is already how `conversation.ask_and_reply` works under the hood; the
harness generalizes it to every subsystem that can pause.

---

## 3. Architecture: kernel, subsystems, tools

### 3.1 Microkernel

**Kernel:** `Controller` / `SearchController` + typed
`ActionKind ∈ {POINT, GEN, RETRIEVE, ASK, WRITE}` + `Verification` + immutable
trace.

The kernel:

- does not know Lean, narrative, or WordNet;
- copy-isolates state at extension boundaries;
- prunes duplicate rejected `(state_key, action.fingerprint)` pairs **within a
  single `run()`**;
- in search mode, tracks `seen_states` so accepted cycles are not re-expanded
  **within a single `search()`**;
- enforces budgets (`max_steps` / `max_nodes` / `max_proposals`) **per run**.

Every one of those is run-scoped, which the table and scope correction below
make explicit; the session-level analogue does not exist yet.

**Loop / tree control (already present, must stay load-bearing) — and its
scope:**

| Mechanism | Where | Scope today | Role |
|---|---|---|---|
| Rejected-branch set | `Controller` | **per `run()`** (`scripts/controller.py:271`: `rejected` is a local, discarded when `run()` returns) | Same failed action on same state not retried forever *within one run* |
| Attempted set | `SearchController` | **per `search()`** (run-local) | Duplicate proposals pruned *within one search* |
| `seen_states` | `SearchController` | **per `search()`** (run-local) | Cycle detection on the accepted frontier *of one search* |
| Budgets | both | **per run/search** | EXHAUSTED vs BUDGET distinct stop reasons |
| Verifier REFUSED/REFUTED | adapters | per action, but verifier-instance ledgers persist (§3.3) | Domain illegal moves never mutate accepted state |

**Scope correction (design review, 2026-08-09).** An earlier draft of this
document described these as global or session-wide properties “already in the
kernel.” That is false. Every one of them is **run-local**. Under the §6.2
dispatcher each need is a separate `Controller.run()` / `SearchController`
invocation, so every pruning structure is reconstructed empty at each
dispatcher hop. Nothing in the kernel today prevents a session from cycling
among **registered** paths across hops: need A routes to subsystem X, whose
outcome re-opens need B, which routes back to X with the same state key, and
the rejected/seen sets that would have caught it were discarded at the
previous `return`. In-run loop control is real and must stay; **session-level**
loop control does not exist and is scheduled work, not an existing guarantee.

Consequently, session-scoped pruning is an explicit deliverable:

- **Phase 1** (§9): the `Session` owns a durable-for-the-session record of
  `(subsystem_id, state_key, action.fingerprint)` outcomes and of visited
  `(need, state_key)` pairs, threaded into each run rather than rebuilt.
- **Phase 2** (§9): the need dispatcher consults that record, and a session
  budget (total hops / total proposals across runs) produces a session-level
  EXHAUSTED/BUDGET stop with caution chrome — an honest refusal, never a
  silent spin. See **P-IH7**.

Future work: expose cycle/budget stats in the UI trace; optional iterative
deepening or best-first once multi-action learned policies exist—without
weakening exact rejection semantics.

### 3.2 Subsystems (not “demos”)

A **subsystem** is a registered capability pack:

```text
Subsystem = {
  id,                # e.g. narrative.frames, belief.visibility, store.corpus,
                     #      prover.lean_live, tool.span_pointer
  probe(),           # boot: available? version? size? error?
  adapter_factory,   # VerifierAdapter | store | tool handle
  registered_paths,  # closed set of action schemas / goals it can pursue
  degrade_policy,    # what the kernel does if probe fails
}
```

**This registry is the same seam as ROADMAP-v0.7 item 6's “replace
string-valued retrieval resolution channels and duck-typed controller commit
hooks with typed protocols.”** A subsystem descriptor is exactly a typed
protocol over adapter/store/tool handles. Build one seam, not two: the harness
registry should *be* the item-6 refactor's landing site, and neither should
ship a second parallel dispatch vocabulary.

**The item-6 half of that seam is now in the tree** (branch
`feature/retrieval-tools`), in the shape this table expects rather than a
retrieval-private one:

| Registry field | What item 6 shipped |
|---|---|
| `probe()` | `observation_adapter.SourceProbe` — `available` / `detail` / `record_count`, liveness only, and the dataclass deliberately carries no status field so it cannot be read as a rung |
| `adapter_factory` | `observation_adapter.ObservationSource` and `retrieval.RungStore`, both `runtime_checkable` protocols; `UnifiedKnowledgeStore` and `LocalObservationAdapter` satisfy them structurally |
| `registered_paths` | `retrieval.MISS_CHAIN` (the rung set) and `retrieval.WALKABLE_RELATIONS` (the lexical edge set) |
| `degrade_policy` | a store that implements no rung is REFUSED with the missing capability named (`"registers no 'derivation' rung; the miss chain may not improvise one"`), never routed around |

The last row is the registration rule made executable: an unregistered rung
name and an unregistered relation name are both refusals, not improvisations.
When Phase 1 builds the kernel registry it should wrap these protocols, not
restate them.

**Probe semantics: liveness only.** A passing probe asserts that a component
imported, loaded, or answered a smoke call — nothing more. **A probe never
raises any verdict's epistemic rung, and the boot matrix is not evidence of
verifier soundness.** `[ OK ] narrative.story` means the `StoryVerifier`
answered; it does not make that verifier's REFUTED judgments more trustworthy,
and a fully green matrix is not a certificate. This is the external-trust-roots
rule of ROADMAP-v0.7 item 7: “the system may verify receipts it minted, but it
may not certify its own verifier soundness.” Self-probes are self-issued
receipts. UI must therefore never render matrix status in the verdict palette
of §4.2 (no green `✓` shared with PROVEN/VERIFIED); OK/OFF/FAIL is a liveness
channel with its own chrome.

Examples:

| Subsystem id | Source code today | Boot probe |
|---|---|---|
| `corpus.nodes` | `data/*` + validate | node count, corpus ids, schema ok |
| `ledger.twins` | matcher reports / on-demand match | report digest or live run ok |
| `ledger.specializations` | specialize report | edge count |
| `narrative.story` | `StoryVerifier` + frames | import + open_frame smoke |
| `belief.ownership` | `frames` / `theory_of_mind` | owner + visibility smoke |
| `retrieve.five_store` | `retrieval.UnifiedKnowledgeStore` | build from repo root |
| `retrieve.wordnet` | optional OEWN zip | path + load + sha256 or OFF |
| `prover.lean_replay` | committed triples | digest pin |
| `prover.lean_live` | PyPantograph | import + one trivial check or OFF |
| `tool.span_pointer` | optional `.pt` | file + load or OFF |
| `tool.analogy_pointer` | optional `.pt` | file + load or OFF |
| `tool.tactic_rank` | optional GRU ckpt | file + load or OFF |

**Registration rule:** a subsystem may only contribute transitions on its
**registered_paths**. There is no “try every shell command until something works”
behavior (the Windows-vs-Linux LLM failure mode). If a path is unregistered,
the kernel does not invent it; it routes to another registered path, ASK, or
honest abstention.

Demos become **subsystem self-tests and regression oracles**, analogous to
initramfs checks—not user destinations.

### 3.3 Session (the process image)

```text
Session {
  capability_matrix,   # result of boot probes
  world_and_frames,    # owned frames, nested models, open fiction, obligations
  user_channels,       # signed UserFrame(s), WAITING slots
  stores,              # pointable context with epistemic status
  tools,               # optional neural / external tool handles
  trace,               # unified action log across subsystems
  budgets,             # remaining steps/nodes/proposals
  surface,             # cli | http.chat_completions | batch
}
```

One session can interleave story revision, belief queries, retrieval, and proof
search **because they share the kernel contract**, not because a monolith model
contains all skills.

**A `Session` is still not a value object — but it is now restorable.**
(ROADMAP-v0.7 item 2, SHIPPED. The paragraph this replaces said sessions were
process-local *by construction*; that is no longer true, and the correction is
recorded here rather than deleted.)

The old statement rested on two facts about `RetrievalVerifier`, and it was
right that both were load-bearing and wrong only about which of them was
essential:

- **the HMAC secrets** were minted per instance with `secrets.token_bytes`;
- **the ledgers** (`_consumed_ask_requests`, `_superseded_ask_bindings`) lived
  on the instance, and are what stop a replayed or superseded binding from
  being resurrected by public-tuple surgery
  (`tests/test_conversation_runtime.py::test_public_state_surgery_cannot_resurrect_superseded_answer`).

The warning that durability was blocked by **more than key management** was
correct and remains the design's sharpest point: a restart that carried keys
forward but not the ledgers would silently re-admit every consumed request.
What changed is that both halves now have a home outside the process, and
neither home is public state.

**What a session is now.** A handle to authority that is *derivable*, not a
handle to authority that is *alive*:

- **Keys** come from a `session_keys.SessionKeyRing` — root keys with ids,
  statuses (`active`/`retired`/`revoked`) and a monotone per-scope counter,
  kept in a runtime-owned keyfile (`CORO_SESSION_KEYFILE`, default
  `.runtime/session-keys.json`, gitignored). Per-session and per-owner signing
  keys are HKDF-SHA256 derived from `(root, key_id, domain|scope)`, so nothing
  ambient is ever serialized. Every receipt, question and binding names its
  `key_id`, which is what makes rotation representable and key-id confusion
  detectable.
- **Ledgers** travel as a signed `retrieval.LedgerSnapshot` inside the session
  file, stamped with a sequence number issued from the private counter. An
  absent snapshot **refuses the restore by name** rather than defaulting to
  empty ledgers — the failure this section originally warned about is now an
  error message, not a silence.
- **Pruning evidence is deliberately not carried.** See the BACKLOG item
  "session pruning assumes a static rung store": a stale refusal that survives
  serialization is worse than one that dies with the process, and its loss
  costs one re-query.

**The session file is unsigned public state, on purpose.** There is no envelope
MAC. An envelope MAC would have caught a forged binding at the envelope and so
proved nothing about whether *bindings* authenticate, which is the property
item 2 claims; it would also have inverted the trust story the rest of this
document builds. Anyone may edit a session file. What they cannot do is make an
edited record authoritative, because authority is per-record signatures plus
the restored private ledgers. Note the asymmetry this leaves, which is inherent
and recorded rather than fixed: an attacker with write access can *retire* a
live binding (add an id to the public `superseded_request_ids`) but can never
*resurrect* a retired one.

**Named refusals** (`session_keys.RefusalReason`) replace boolean failure at
every boundary: `unknown-key-id`, `revoked-key-id`, `signature-mismatch`,
`ledger-rollback`, `session-id-mismatch`, `schema-version-mismatch`,
`binding-signature-invalid`, `binding-superseded`, `binding-goal-expired`,
`request-already-consumed`, `undeclarable-lifetime`.

**Lifetime protocol** (`scripts/lifetimes.py`) unifies `retrieval.UserFrame`
bindings and owned belief frames under one vocabulary — `goal_local`,
`session`, `durable`, `superseded`, `expired` — split into *declared*
(chosen once by the trusted return channel, signed, immutable) and *effective*
(recomputed on every read from the ledgers and the current goal, never
stored). `superseded` and `expired` cannot be declared at all.

**What is still not durable, stated plainly.** Two limits are scoped out rather
than solved, both registered as P-DS7 before the work started:

1. **Root-key file compromise** is the scheme's weakest point. Every session
   key descends from one root secret; a reader of the keyfile can mint any
   binding for any owner in any session, and revocation is the only remedy.
2. **Session forking is not prevented.** Two processes may import the same
   snapshot at the same sequence and diverge. The counter enforces
   monotonicity, not uniqueness, because refusing a repeat import would brick
   any session that crashed between export and import.

§4.3's rule stands but for a narrower reason: HTTP may now resume a session,
and must resume it *through* `ConversationSession.restore` — it may not
reconstruct a verifier and assume authority.

### 3.4 Dispatcher: symbolic MoE first, learned policy later

Review accepts that open-language Shape C comes after earlier approaches.

> **Phase numbering:** **§9 is normative** (Phases 0–6, HTTP at 4). The list
> below is a *capability-maturity ordering* of the dispatcher itself and is
> subordinate to §9; each entry names its §9 phase. Where any other section of
> this document says “Phase *n*,” it means the §9 number.

**Dispatcher maturity (each mapped to its normative §9 phase):**

1. **Kernel session + boot matrix + WAITING I/O** (no demo menu) — §9 **Phase
   1**.
2. **Goal / need detector** over symbolic state: open UNKNOWN, undischarged
   obligation, unsolved goal, missing witness, empty retrieval → choose among
   registered paths (RETRIEVE vs ASK vs GEN vs search); plus session-level
   pruning and session budgets (§3.1) — §9 **Phase 2**.
3. **Bounded slot-filling grammar** — §9 **Phase 2**, *not* deferred to last.
   ROADMAP-v0.7 item 2 requires “a bounded but growing natural-request grammar
   into frame-private slots, including corrections, pronouns, and owner
   references,” and item 2 is part of the v0.7 **release gate**. This is
   in-cycle work: a closed, enumerable grammar that fills *already-open* slots
   on registered paths. It invents no slot, no path, and no fact; an
   unparseable utterance falls through to ASK, exactly as an unbound slot does
   today.
4. **Optional tools** as subsystems when probes succeed — §9 **Phase 3**.
5. **Learned ranking** among legal registered actions (vacuity baselines
   mandatory; tactic-policy lesson: frequency can beat a weak learner) — §9
   **Phase 5**.
6. **Unrestricted prose authoring and open-English render** constrained to
   point into accepted content — §9 **Phase 6**, and the last thing to land.
   This is ROADMAP-v0.7 item 9's surface pointer, a different problem from
   (3): open *authoring* of new content versus bounded *filling* of declared
   slots. Conflating them was what made an earlier draft defer all parsing to
   the final phase, contradicting item 2's release gate.

The “brain” that chooses the next path is initially **closed-form dispatch
predicates** (epistemic ladder + goal state), which is the project’s load-bearing
bet: *whether* to retrieve is not learned; *what* to try among legal options may
be ranked later.

### 3.5 Agent OS and many specialized models

Review vision: eventually an **agentic model OS**—kernel + data systems +
hundreds/thousands of specialized models plumbed dynamically, without a
traditional heavyweight OS for the reasoning plane.

Fit to house design:

| Layer | Analogy | Project mapping |
|---|---|---|
| Kernel | process scheduling, syscalls | controller actions, verify, budgets, trace |
| Drivers | hardware modules | subsystems after successful probe |
| Filesystems | durable stores | corpus, ledgers, proof artifacts, optional WordNet |
| Processes / containers | isolation | frame scopes, owner isolation, copy-isolated state |
| Dynamic modules | loadable .ko / plugins | optional `.pt` tools and external verifiers registered at runtime |
| Init | hardware detect | boot capability matrix (see §5) |

**Near term:** dozens of optional tools is fantasy if each needs a unique vocab
and no adapter. **Architecture must allow** hot registration of a tool that
speaks ActionKind in/out with provenance. **Neural MoE over today’s checkpoints
is still rejected** as the integration strategy; **dynamic plugin registration
of verified specialists** is accepted.

Long-term “thousands of models” only works if:

- each tool has a tiny, documented I/O schema;
- the kernel never treats tool logits as VERIFIED;
- missing tools degrade via `degrade_policy`, not crash;
- loop detection **becomes** session-scoped so it holds across tool hops. It is
  not there yet: today's pruning is run-local (§3.1), so each tool hop starts
  with an empty rejected/seen set. Registering a tool that can re-open a need
  it just failed is a live cycling risk until the Phase-2 session record lands
  (P-IH7). This is a precondition on “thousands of models,” not a description
  of the current kernel.

---

## 4. Surfaces: CLI agent REPL and Chat Completions–compatible HTTP

### 4.1 CLI / TTY agent loop (primary)

Not a slash-command catalog of demos. The default loop is:

```text
boot → print capability matrix (kernel-style)
read user goal (natural or structured)
while not terminal:
  dispatch registered path → propose actions
  on WAITING → prompt user (pulsing) → resume with signed reply
  on SOLVED → show final answer + collapsed trace
  on REFUSED/REFUTED → show reason + evidence
  on EXHAUSTED/BUDGET → show caution + partial trace + suggestions among registered alts
```

Structured overrides (power user / debug) remain available (`:trace`,
`:status`, `:budget`, force an action) but are **not** the conceptual model
taught first. Prefer hidden advanced commands over a demo zoo.

### 4.2 Visual status language (CLI and web)

Review: success / failure / waiting should be visually hinted (characters,
colors, pulsing), with expandable chain-of-thought that **defaults to collapsed**
when complete.

| Stop / verdict | Suggested chrome | Meaning |
|---|---|---|
| PROVEN / VERIFIED / SOLVED | green `✓` / steady | accepted transition or goal complete |
| REFUTED | red `✗` | content contradiction |
| REFUSED | red/orange `⊘` | illegal or unregistered path |
| UNKNOWN | amber `?` | open need; may trigger RETRIEVE/ASK |
| WAITING | cyan/pulse `…` / spinner | input channel required |
| EXHAUSTED | amber `∎` | policy has no further legal moves |
| BUDGET | amber `⏱` | node/step/proposal ceiling hit |

**Trace UX:**

- While running: stream subsystem steps (optional verbose).
- On completion: **collapse** intermediate CoT; show final render + one-line
  status; expand-on-demand for full action log (action, verdict, evidence ids).
- Never hide REFUSED/REFUTED inside a fluent paragraph without a status mark.

Plain terminals without color still get ASCII markers; color is progressive
enhancement (`NO_COLOR` respected).

**Trace events are structured records, not strings.** The session emits typed
events (action kind, subsystem id, verdict, evidence ids, budget counters,
run/hop index); TTY chrome — glyphs, color, pulsing, collapse state — is **one
renderer** over that stream. This is the seam that makes §4.3 possible at all:
the HTTP skin serializes the same records instead of scraping a terminal, and
a batch run writes them as the machine-readable need-input record of §2.2. No
verdict may exist only as a rendered character.

### 4.3 Chat Completions–compatible HTTP (second leg)

Expose the same session as a **drop-in channel** for existing agent harnesses
(OpenAI-compatible `POST /v1/chat/completions` shape, subset):

- Map assistant “tool calls” to kernel actions / WAITING needs where possible.
- Map tool results and user messages to resume actions (especially ASK replies).
- Stream tokens only for **surface rendering of already-accepted content** and
  status lines—not for inventing unverified facts.
- Return structured extensions (vendor fields) for verdict, evidence, capability
  matrix, and collapsed trace id.

**Non-goal:** full OpenAI tool-ecosystem parity or multi-tenant SaaS auth in the
first cut. **Goal:** one session engine, two skins (TTY + HTTP), so external
orchestrators can drive the kernel without forking it.

Durable authenticated single-session storage now exists (§3.3, ROADMAP-v0.7
item 2): a restart reloads a root key ring, re-imports signed ledgers, and
refuses a stale, forged, rolled-back or revoked binding by name. HTTP may
therefore resume a session — but only through `ConversationSession.restore`,
and only after presenting a key ring; reconstructing a verifier and assuming
authority is still forbidden. Two limits keep HTTP honest: **session forking is
not prevented** (two clients may restore the same snapshot and diverge), and
**multi-session storage across owners is untried** — the shipped contract is
one owner, one session id, restored in one place at a time.

---

## 5. Boot: capability matrix like kernel hardware detect

Review: startup should resemble Linux kernel init—detect “hardware” (corpuses,
ledgers, optional modules), versions/sizes, success/fail—not necessarily
eagerly “load” everything into RAM.

```text
corollary kernel 0.x starting …
[ OK ] corpus.nodes          22 corpora, 221 nodes, schema validate
[ OK ] ledger.twins          reports/signature_matches.json (or live)
[ OK ] ledger.specializations 655 edges
[ OK ] narrative.story       StoryVerifier smoke
[ OK ] belief.ownership      FrameExecutor smoke
[ OK ] retrieve.five_store   built
[OFF ] retrieve.wordnet      no archive (set COROLLARY_WORDNET=…)
[OFF ] prover.lean_live      pantograph unavailable
[OFF ] tool.span_pointer     no checkpoint
[ OK ] channel.tty           interactive
ready. registered paths: 14  optional off: 3
```

Rules:

- **OK** means the probe passed — the subsystem is *live* and may register its
  registered_paths. It is not a soundness claim (§3.2).
- **OFF** means absent optional dependency; degrade_policy active.
- **FAIL** means required subsystem broken → refuse to enter interactive mode
  (or enter read-only diagnose mode).
- Do not download corpora at boot. Do not require WordNet/wiki.
- Sizes/versions: node counts, report digests, archive sha256 when WordNet on,
  model param counts when tools on—**metadata**, not full materialization when
  avoidable.

This matrix is the answer to “what happens without WordNet/wiki?” made
user-visible every run (see §7).

---

## 6. User experience without demo names

### 6.1 Goals in, mechanics out

Examples of **natural** use (dispatcher maps to registered paths):

| User intent (any surface) | Kernel behavior |
|---|---|
| “The chicken’s eggs should be silver.” | If fiction frame open with private color slot → ASK path or direct signed bind if policy allows; render revision; no world promotion. |
| “Where will Sally look?” after events | Belief subsystem answers from owner frame; cite visibility. |
| “What is like Coulomb’s law here?” | RETRIEVE / twin ledger path; POINT to twin; show skeleton. |
| “Prove P∧Q → Q∧P” | If lean_live OK → search; else lean_replay only if pinned chain exists; else REFUSED with matrix hint. |
| Contradict frame premise | REFUTED with evidence—no soft rewrite. |

No `/golden_chicken` required. A **tutorial** may run the oracle sequence once
as `:selftest narrative` for developers.

### 6.2 System-driven need fulfillment

The loop is need-driven:

```text
open needs = UNKNOWNs ∪ undischarged obligations ∪ explicit user goals
for need in priority(open needs):
  candidates = registered_paths that declare they can progress need
  if none: ASK or abstain with reason
  else: rank (oracle / frequency / learned) → propose → verify
  if WAITING: yield to channel
  if cycle/budget: stop with caution chrome
```

This need→candidates→rank→verify→miss ladder is **not a new invention**: it is
ROADMAP-v0.7 item 6's miss chain — *exact → neighborhood → derivation → tool →
ASK for frame-private knowledge → explicit abstention* — lifted from retrieval
to every registered subsystem. The dispatcher should implement item 6's chain
generically rather than reinventing a parallel one, and item 6's “store
REFUTED and exhausted branches as reusable pruning evidence” is precisely the
session-scoped record §3.1 requires.

That chain is now **executable** rather than aspirational: `retrieval.
MISS_CHAIN` is the ordered rung set, `miss_chain_actions(key, slot)` renders it
as one proposable action per rung plus the terminal ASK, and each rung's
attempt lands in the controller trace with its own verdict. Two shapes there
are worth generalizing rather than re-deciding. First, **abstention is not an
action**: a chain that answers nothing stops EXHAUSTED with empty context and
a trace carrying one UNKNOWN per rung, so there is no ABSTAIN transition for a
policy to forge. Second, **ASK is proposed unconditionally** and its refusal
is informative — a public need gets “assigned to the durable store, not the
interlocutor”, a frame-private one gets the question — so reading the verdicts
top to bottom tells you which authority owned the answer, not merely that the
need went unmet.

This is the anti-“command not found” design, with one honest boundary. The
system never flails across unregistered OS shells: it only walks the
**registered** graph, and an unregistered path is REFUSED rather than
improvised. That part is true today and is enforced by registration, not by
loop detection.

What is **not** true today is the second half of the safety argument. Walking
only the registered graph does not by itself terminate: the kernel's rejected
sets, `seen_states`, and budgets are **run-local** (§3.1), and each iteration
of the loop above is a fresh run, so a session can cycle *among registered
paths* across dispatcher hops with every pruning structure reset. Bounded
registration prevents inventing paths; it does not prevent revisiting them.
Termination across hops requires the session-scoped record and session budget
scheduled in Phases 1–2, whose adjudicating test is **P-IH7**. Until that
lands, the dispatcher must be run under an explicit hop ceiling and stop with
caution chrome when it is reached — a stated budget is the interim guarantee,
not an unproven claim of global loop detection.

**Retrieval-side substrate: LANDED** (ROADMAP-v0.7 item 6, branch
`feature/retrieval-tools`). `RetrievalVerifier` now keeps
`retrieval.PruningEvidence` keyed by `(session_id, verifier state_key, action
fingerprint)`, written **only** from `commit_run` — the same commit gate the
anti-replay ledgers use, so a speculative `evaluate` cannot poison a session
with a dead end it merely considered. A second walk of item 6's miss chain
over the same unanswered need refuses all four rungs from stored evidence and
issues zero store queries
(`tests/test_retrieval_tools.py::SessionPruningTests::
test_a_second_dispatcher_hop_costs_no_store_queries`).

This is the *record*, not P-IH7. Three things are still owed before P-IH7 can
be adjudicated, and none of them is claimed here: the **session budget**
(§3.1), the dispatcher's `(need, state_key)` **cycle identification** in the
trace, and the two-subsystem cycle case itself — the landed evidence is keyed
on one verifier's state, so two subsystems re-opening each other's need still
need the dispatcher-level record to see the loop. What is now true is that the
substrate exists and is commit-gated, so Phase 1 builds on it rather than
inventing a parallel one. Note the asymmetry the implementation forced: only
REFUTED and exhausted (UNKNOWN/ABSTAIN) branches are recorded. REFUSED is
deliberately **not** — it is an authority or well-formedness answer whose
re-check costs one predicate, and caching authority answers is how a stale
refusal becomes a policy.

**Two limits of that key, for whoever builds Phase 1 on it.** External review
found the first as a live bug: the key delegated its frame half to
`FrameAssertionVerifier.state_key`, which keys on the frame *name* and omits
`declarations`/`suspends`/`owner`, so two same-named frames with contradictory
premises shared a prune and one's dead end closed the other's live branch. The
frame **scope** (`repr(state.frame.spec)`) is in the key now. The general form
matters more than the instance: a run-local dedup key is not automatically a
session-scoped evidence key, and evidence that outlives a run must be keyed on
everything the run was allowed to assume constant. The second limit is still
open and is an *assumption*, not an omission — the key describes the
conversation, never the stores, so a source that goes live mid-session leaves
an earlier branch REFUSED. A dispatcher that registers subsystems lazily will
hit this before the retrieval layer does; the shape filed in BACKLOG is a
probe-generation stamp on TOOL-rung evidence, not a wider state key.

---

## 7. Offline and optional dependencies (reshaped by the harness)

| Resource | Boot status | Runtime effect if OFF |
|---|---|---|
| Committed `data/*` | required | FAIL boot |
| Twin/specialize reports | preferred | can recompute or OFF with reduced retrieve |
| WordNet | optional | five-store only; no synonym bridge; identical to today’s unnamed absence |
| Wiki/COCA `data_real` | not a subsystem by default | irrelevant to interactive kernel unless a future real-text tool registers |
| Lean live | optional | proof goals degrade to replay-only or REFUSED |
| Torch + checkpoints | optional | tools OFF; pure symbolic session remains first-class |
| Interactive channel | tty/http/batch | WAITING handling differs (§2.2) |

**Dependent “demos”** become subsystem self-tests: if `tool.span_pointer` is
OFF, self-test skips; if user goal required it, dispatcher chooses another
path or abstains—never pretends the neural answer exists.

---

## 8. Model composition under the OS metaphor

Restated under review:

- **Today:** piece-by-piece specialists (evidence + optional tools).
- **Integrate by:** dynamic registration of tools behind ActionKind-compatible
  adapters (algorithmic stitch / plugin drivers).
- **Not by:** neural MoE over incompatible vocabs, or replacing the matcher
  with a classifier for equality.
- **Eventually:** many specialized models as loadable modules; one small
  concept-token core remains the long thesis for *general residual ranking*,
  not a requirement to boot the OS.

Tool admission bar (unchanged):

1. closed outputs (point/rank) or proposals only;
2. capability-blind baseline on the same path;
3. missing checkpoint → OFF, not crash;
4. tool-produced actions enter the **session-scoped** pruning record (§3.1),
   not only the run-local one.

---

## 9. Phased delivery

**This table is the normative phase numbering for the whole document.** §3.4's
dispatcher-maturity list is subordinate to it and maps entry-by-entry; any
“Phase *n*” elsewhere (including §10's predictions) means the number here.

| Phase | Deliverable | User-visible |
|---|---|---|
| **0** | This design + BACKLOG | none |
| **1** | Session object, boot matrix, TTY loop, WAITING channel, unified structured trace, **session-scoped pruning record** (§3.1); wire narrative + belief + retrieve as subsystems | agent-like CLI without demo menu; selftests optional |
| **2** | Need dispatcher over registered paths implementing the v0.7 item-6 miss chain; **session budget + session-level loop detection** (P-IH7); **bounded slot-filling grammar** (v0.7 item 2); collapse/expand trace UX; status chrome | system asks when needed; cycling need refuses instead of spinning; final answers default compact |
| **3** | Optional tool plugins (span/analogy/tactic) | matrix shows tools OK/OFF |
| **4** | Chat Completions–compatible HTTP skin | external harnesses attach |
| **5** | Learned multi-action ranking | only with baselines |
| **6** | Unrestricted prose authoring / open-English render (v0.7 item 9) | still kernel-bound |

Phase 1 must not ship a `/demo_*` surface. Developer selftests are fine.
Phase 2 must not ship a dispatcher that can loop: either P-IH7's test passes or
the hop ceiling of §6.2 is enforced and surfaced.

---

## 10. Registered predictions (before implementation)

Every entry below names the **adjudicating test** that decides it. A prediction
with no test that could fail is not a prediction, and this section separates
three kinds of claim that an earlier draft blurred: **predictions** (can be
falsified by the system's behavior), **policy commitments** (we control the
outcome, so being “surprised” is impossible), and **architectural commitments**
(design constraints, not empirical bets). Phase numbers are §9's.

These entries were revised before any implementation and before merge, in
response to the 2026-08-09 design review; the corrections are recorded here
rather than applied silently, per ROADMAP-v0.7 item 10.

**P-IH1 — Offline core session.** *(prediction)* With WordNet/Lean/Torch OFF, a
single session can still open a fiction frame, bind a private slot via WAITING,
answer a visibility-derived belief query, and retrieve a corpus twin. If any of
those requires an optional subsystem, the prediction text is wrong and must be
corrected—not the offline claim silently narrowed.
*Adjudicated by:* a new `tests/test_session_offline.py` that constructs a
session with the optional probes forced OFF and drives all four legs in one
session object, asserting no optional subsystem is registered; run under
`python -m unittest discover -s tests` with `COROLLARY_WORDNET` unset. Miss if
any leg needs an OFF subsystem or a second session.

**P-IH2 — Every pausing subsystem can state its own need.** *(prediction —
strengthened)* The original text (“no user-facing ASK command is required”) was
near-vacuous: `ClarificationRequest` already carries a signed `prompt` field
(`scripts/retrieval.py:763`), so retrieval's WAITING is presentable by
construction and the claim could not fail. The claim that can fail is the
**general** one: *every* subsystem that can pause must supply a
human-presentable need record through the same typed channel, and the shell
must render it **without any subsystem-specific knowledge** — no
retrieval-shaped special case. Miss if the TTY loop must branch on subsystem id
to phrase a question, or if a non-retrieval subsystem (narrative obligation,
belief gap, prover missing witness) can reach WAITING with no prompt the shell
can render.
*Adjudicated by:* extending `tests/test_ask.py` (see
`test_controller_stops_waiting_after_verified_question`) with a second,
non-retrieval pausing subsystem, plus a shell-render test asserting the
renderer is subsystem-agnostic.

**P-IH3 — No demo zoo.** *(POLICY COMMITMENT, not a prediction — re-labeled.)*
We author the help text and the surface, so we cannot be *surprised* by it;
registering it as a prediction was a category error. As a commitment: the
default help/UX will not list golden-chicken or Sally–Anne as destinations;
those names appear only in selftests and docs, and §9 **Phase 1** ships no
`/demo_*` surface. Breach is a review failure, not a negative result.
*Enforced by:* a lint/UX test asserting no demo name occurs in the help/command
table, alongside the existing oracle regressions in `tests/test_controller.py`
(`test_oracle_executes_three_verified_beats`) which keep the golden-chicken
sequence alive as a **selftest**.

**P-IH4 — Registered paths only.** *(prediction)* Given a goal that no
registered subsystem claims, the session abstains or ASKs rather than
free-generating an answer. Miss if fluent unregistered content is emitted as
VERIFIED.
*Adjudicated by:* a dispatcher test that submits a goal outside every
registered path and asserts the terminal stop is REFUSED/abstain with a reason,
extending the refusal patterns of `tests/test_retrieval.py`
(`test_point_before_retrieval_is_refused`).

**P-IH5 — Boot matrix honesty.** *(prediction)* Startup output marks WordNet
OFF when no archive is configured; naming a missing archive FAILs that probe
rather than silently equating to OFF (preserves today’s loud named-path
behavior).
*Adjudicated by:* a capability-matrix test paired with
`tests/test_wordnet_retrieval.py`, run twice — once with `COROLLARY_WORDNET`
unset (expect OFF) and once pointing at a nonexistent path (expect FAIL, not
OFF). Note this probe asserts liveness only (§3.2); a green matrix is not
evidence of verifier soundness.

**A-IH6 — One session engine, two skins.** *(ARCHITECTURAL COMMITMENT — split
out of the former P-IH6.)* The TTY and Chat-Completions surfaces are renderers
over the same session engine and the same structured trace stream (§4.2); a
second engine forked for HTTP is a design violation, not a surprising
observation. Enforced at review and by construction (§4.3's “one session
engine, two skins”).

**P-IH6 — WAITING survives the HTTP boundary.** *(prediction — the falsifiable
remainder.)* When §9 **Phase 4** exists, a WAITING state is representable to a
chat-completions client **without inventing slot values**: the client receives
a need record and resumes with an authenticated reply, and no default,
placeholder, or model-generated value is ever substituted for the missing slot.
Miss if the HTTP mapping can only proceed by supplying a value the user did not
send.
*Adjudicated by:* an HTTP-skin test mirroring
`tests/test_ask.py::test_signed_reply_resumes_same_session_and_binds_user_frame`
across the transport, plus a negative asserting an unsigned or absent reply
cannot bind (`test_policy_cannot_guess_user_reply_signature`).

**P-IH7 — Session-level loop detection.** *(prediction — newly registered,
2026-08-09 review.)* The kernel's rejected sets, `seen_states`, and budgets are
**run-local** (`scripts/controller.py:271`), so a multi-run dispatcher session
has no cycle protection today. Prediction: once §9 Phase 1's session-scoped
pruning record and Phase 2's session budget land, a session whose need cycles
**between two registered paths** terminates in bounded hops with REFUSED or an
explicit abstention/BUDGET stop, and never loops.
*Adjudicated by:* a new `tests/test_session_dispatcher.py` case in which two
registered subsystems each re-open the need the other just failed, with a
stated session budget (proposed: 8 dispatcher hops). The session must reach a
terminal stop within that budget, the stop must be REFUSED/abstain/BUDGET with
the cycle named in the trace, and the trace must show the second visit to a
`(need, state_key)` pair being pruned rather than re-expanded. **Miss** if the
session exceeds the hop ceiling, or if it terminates only because a wall-clock
or step cap fired without identifying the cycle. Adjudication is required
before any Phase-3 tool plugin registers, since tools multiply the hop graph
(§3.5, §8).

---

## 11. Non-goals (near term)

- Shipping Wikipedia or WordNet inside git.
- Neural MoE fusion of all release checkpoints.
- Full multi-tenant durable auth.
- Claiming Grok/ChatGPT open-domain parity.
- Replacing symbolic equality/twins with learned classifiers.
- Blocking the harness on depth-OOD analogy being solved.

---

## 12. Work items (dependency order)

1. Land this design; index in BACKLOG/README.
2. Implement `Session` + `CapabilityMatrix.probe()` + registry (no UI), as the
   typed-protocol seam of ROADMAP-v0.7 item 6 rather than a second one. The
   `Session` names its verifier instance; it does not serialize the HMAC
   authority or the anti-replay/supersession ledgers (§3.3).
3. **Session-scoped pruning record** (Phase 1): thread visited
   `(need, state_key)` and `(subsystem_id, state_key, fingerprint)` outcomes
   through every `run()` instead of rebuilding them empty per hop. Closes the
   false “loop detection already in the kernel” claim at session scope.
4. Structured trace events + TTY agent loop as one renderer over them: WAITING
   auto-prompt, status markers, collapsed trace.
5. Register narrative, belief, five-store as first subsystems; demos →
   selftests.
6. Need dispatcher (symbolic) over the item-6 miss chain, with **session
   budget** and cycle/budget surfacing; adjudicate **P-IH7**.
7. Bounded slot-filling grammar into already-open frame-private slots (v0.7
   item 2) — in-cycle, not deferred to the end.
8. Optional tools + HTTP skin as separate slices.
9. Only then learned global action ranking and unrestricted prose authoring
   (v0.7 item 9).

---

## 13. Relation to active training work

Depth-consumer and validation work on other agents stays on disjoint files.
Harness implementation should not touch analogy generators mid-matrix. Shared
`.venv` in the main checkout remains the environment for any later coding
worktree.
