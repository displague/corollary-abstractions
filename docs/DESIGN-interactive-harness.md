# Design: interactive harness — microkernel agent OS over a verified world

Source conversation: 2026-08-09 (directional plan on integrating demos into one
agent-like experience; model composition; offline degradation), with review
corrections that reject a “slash-command demo launcher” in favor of a
**capability-driven session**: the system decides what is missing and how to
fulfill it along **registered, proven paths** only.

Status: design only. No REPL, HTTP API, or subsystem registry is implemented
here. The domain-neutral controller, frame executor, retrieval ASK/WAITING
channel, story adapter, live Lean search, and specialist experiment models
already exist as libraries and scripted demos; this document specifies how they
become one live experience. Indexed from `docs/BACKLOG.md` (“Interactive
harness / agent OS”) and related to `docs/DESIGN-frames-and-retrieval.md`,
`docs/DESIGN-concept-tokens.md`, and ROADMAP-v0.6 conversation / policy items.

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
| Lean search | **Yes (bounded)** | BFS over registered tactic palettes; not a single canned theorem only—though the public demo targets one held-out Init prop. |
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
- prunes duplicate rejected `(state_key, action.fingerprint)` pairs;
- in search mode, tracks `seen_states` so accepted cycles are not re-expanded;
- enforces budgets (`max_steps` / `max_nodes` / `max_proposals`).

**Loop / tree control (already present, must stay load-bearing):**

| Mechanism | Where | Role |
|---|---|---|
| Rejected-branch set | `Controller` | Same failed action on same state not retried forever |
| Attempted set | `SearchController` | Duplicate proposals pruned |
| `seen_states` | `SearchController` | Cycle detection on accepted frontier |
| Budgets | both | EXHAUSTED vs BUDGET distinct stop reasons |
| Verifier REFUSED/REFUTED | adapters | Domain illegal moves never mutate accepted state |

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
  proven_paths,      # closed set of action schemas / goals it can pursue
  degrade_policy,    # what the kernel does if probe fails
}
```

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
**proven_paths**. There is no “try every shell command until something works”
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

### 3.4 Dispatcher: symbolic MoE first, learned policy later

Review accepts that open-language Shape C comes after earlier approaches.

**Phase order (unchanged intent, reframed):**

1. **Kernel session + boot matrix + WAITING I/O** (no demo menu).
2. **Goal / need detector** over symbolic state: open UNKNOWN, undischarged
   obligation, unsolved goal, missing witness, empty retrieval → choose among
   registered paths (RETRIEVE vs ASK vs GEN vs search).
3. **Optional tools** as subsystems when probes succeed.
4. **Learned ranking** among legal registered actions (vacuity baselines
   mandatory; tactic-policy lesson: frequency can beat a weak learner).
5. **Open-English parse/render** constrained to point into accepted content.

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
- loop detection remains global across tool hops.

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

Durable authenticated multi-session storage remains open (process-local HMAC
authority today); HTTP must not pretend restarts are safe until that contract
exists.

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

- **OK** means probe passed; subsystem may register proven_paths.
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

This is the anti-“command not found” design: the system never flails across
unregistered OS shells; it only walks the registered graph, with loop
detection already in the kernel.

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
4. loop detection includes tool-produced actions.

---

## 9. Phased delivery

| Phase | Deliverable | User-visible |
|---|---|---|
| **0** | This design + BACKLOG | none |
| **1** | Session object, boot matrix, TTY loop, WAITING channel, unified trace; wire narrative + belief + retrieve as subsystems | agent-like CLI without demo menu; selftests optional |
| **2** | Need dispatcher over registered paths; collapse/expand trace UX; status chrome | system asks when needed; final answers default compact |
| **3** | Optional tool plugins (span/analogy/tactic) | matrix shows tools OK/OFF |
| **4** | Chat Completions–compatible HTTP skin | external harnesses attach |
| **5** | Learned multi-action ranking | only with baselines |
| **6** | Open-English parse/render | still kernel-bound |

Phase 1 must not ship a `/demo_*` surface. Developer selftests are fine.

---

## 10. Registered predictions (before implementation)

**P-IH1 — Offline core session.** With WordNet/Lean/Torch OFF, a single session
can still open a fiction frame, bind a private slot via WAITING, answer a
visibility-derived belief query, and retrieve a corpus twin. If any of those
requires an optional subsystem, the prediction text is wrong and must be
corrected—not the offline claim silently narrowed.

**P-IH2 — WAITING is the ask tool-call.** No user-facing command named ASK is
required for the private-slot path when a TTY channel exists; the shell
surfaces WAITING automatically. Miss if users must type a dedicated ask
command to complete the path.

**P-IH3 — No demo zoo.** The default help/UX does not list golden-chicken or
Sally–Anne as destinations; those names appear only in selftests/docs. Miss if
Phase 1 ships a slash menu of demos as the primary model.

**P-IH4 — Registered paths only.** Given a goal that no registered subsystem
claims, the session abstains or ASKs rather than free-generating an answer.
Miss if fluent unregistered content is emitted as VERIFIED.

**P-IH5 — Boot matrix honesty.** Startup output marks WordNet OFF when no
archive is configured; naming a missing archive FAILs that probe rather than
silently equating to OFF (preserves today’s loud named-path behavior).

**P-IH6 — HTTP skin parity.** When Phase 4 exists, the same session engine
backs TTY and chat-completions; a WAITING state is representable to the HTTP
client without inventing slot values.

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
2. Implement `Session` + `CapabilityMatrix.probe()` + registry (no UI).
3. TTY agent loop: WAITING auto-prompt, status markers, collapsed trace.
4. Register narrative, belief, five-store as first subsystems; demos → selftests.
5. Need dispatcher (symbolic) with cycle/budget surfacing.
6. Optional tools + HTTP skin as separate slices.
7. Only then learned global action ranking and open-English.

---

## 13. Relation to active training work

Depth-consumer and validation work on other agents stays on disjoint files.
Harness implementation should not touch analogy generators mid-matrix. Shared
`.venv` in the main checkout remains the environment for any later coding
worktree.
