# Chat-completions skin: protocol subset and trace-to-API mapping

**Status: specification, committed before implementation.** This is the
short spec that [DESIGN-grounded-throughput](DESIGN-grounded-throughput.md)
§10 places second in the preregistration order — after the design, before
the task book, the baseline manifest, and any code. P-IH6's adjudication
quotes this document. The substrate contract is
[DESIGN-interactive-harness](DESIGN-interactive-harness.md) §4.3 (A-IH6:
one session engine, two skins; the HTTP skin is a renderer over the same
structured records the TTY renders, never a second engine).

This spec was adversarially reviewed before commit; two of its clauses
are **recorded corrections to the governing designs**, marked ¶DEV-1 and
¶DEV-2 below, because a deviation without a record is the drift this
repository exists to catch.

**2026-08-27 compatibility amendment, recorded before implementation.**
Codex CLI 0.147.0 no longer accepts a `chat_completions` provider wire API;
its only custom-provider protocol is Responses. The amendment below adds a
second protocol renderer over the same `ChatEngine`. It is not a new engine,
does not consume `instructions` or tools, and must return the same rendered
answer bytes and `x_corollary` record as chat completions for the same input.

> **¶AMD-3 — a third profile, and the tool call it can make (2026-08-31).**
> `docs/DESIGN-protocol-uptake.md` §4 needs a served surface for protocol
> uptake, and neither shipped profile can host it honestly: the kernel
> profile's registered line grammar (§5) and abstention are published claims,
> and the conversation profile's closed two-slot request grammar (§3) declares
> any widening an engine change. This amendment therefore **registers a third
> profile, `corollary/protocol`**, whose request surface is the protocol
> runtime (`scripts/protocol_runtime.py`) over a **fresh session type** — not
> the slot-filling session, not kernel line routing.
>
> **What it amends, sentence by sentence:** §1's "two session objects" and "no
> third path"; §2's `/v1/models` row; §3's profile table and the unknown-model
> refusal; §4's request mapping (the served turn is the last *input item*) and
> §4.1's canonical prefix hash (extended with a typed serialization of every
> admitted tool-result item, **additively**); §4.2's refusal of non-message
> input items, for **exactly** the `function_call_output` type on **this**
> profile; §6, §6.1 and §6.2 for this profile's content rule, receipt row and
> need shape; §7 for the generated protocol block; §8's "no synthetic tool or
> reasoning item is introduced", plus the SSE lifecycle of the one
> function-call item; and §10's error list.
>
> **What it does not amend, and this is the load-bearing half:** the kernel
> profile's §5 line-grammar claim, the conversation profile's §3
> request-grammar claim, and those two profiles' generated capability-sheet
> blocks. `line_grammar`, `request_grammar` and the `honesty` string are
> byte-unchanged, asserted in `tests/test_serve_chat.py`. The `hello` turn
> that forced the protocol design reached the kernel profile, and **refusal
> is still that profile's honest answer**; the repaired entrance is the same
> bytes addressed to `corollary/protocol`.
>
> **`corollary.capabilities/2` does NOT bump, and here is the trigger being
> read rather than waved past.** ¶AMD-1 records the trigger exactly: *"the
> sheet is what publishes the alphabet, so widening the alphabet changes the
> sheet's contract."* AMD-3 widens nothing. The protocol profile transports
> `found`, `waiting` and `refused` — three statuses already in §5's frozen
> closed set — because its dispositions map onto them
> (`ENTER`/`SUSPEND`/`CONTINUE`/`RESUME`/`EXIT` → `found`, `ASK` → `waiting`,
> `REFUSED` → `refused`). What the sheet gains is *keys*:
> `profiles["corollary/protocol"]`, `protocol_grammar`, and
> `prompt_tool_adapters`. That is the additive shape /2 has already carried
> three times without a bump — `realization`, `conformance` and
> `foreign_voice` all entered that way. A client that enumerated the alphabet
> learns nothing new; a client that enumerates `profiles` reads one more key.
> Bumping here would spend the version number on the case the trigger was
> written to exclude and leave nothing to say the day the alphabet really does
> widen. **`corollary.chat` also stays at /1**: no status reachable on that
> wire changed, and ¶AMD-1's separate debt (the day a proposer is attached to
> a session this skin serves) is untouched by this amendment. Everything AMD-3
> adds to `x_corollary` is profile-scoped and optional — `uptake` on
> `corollary/protocol`, two extra keys inside that profile's `need` — and no
> byte of a kernel or conversation response moves.
>
> **One risk, recorded rather than discovered later.** §4.2's amendment is for
> exactly `function_call_output`, as the design's bullet list says. A host that
> replays its own `function_call` item back in `input` — which a Codex CLI
> running with `store: false` may do rather than using
> `previous_response_id` — is therefore still refused with `400
> invalid_input_item`. If B7's live round trip fails on that wire shape, it is
> a red or `UNTESTED` result and a further amendment's problem, not something
> this one may quietly widen to avoid.

## 1. What the engine actually is (three session objects, one engine)

The repository ships one session engine with **three session objects** — two
from the first cycle and one registered by ¶AMD-3 — and this spec serves all
three rather than pretending they are one:

- **`CoreSession`** (`scripts/harness.py:533`) — boots the capability
  matrix and routes the **registered line grammar** through
  `route_line(repo_root, session, line) -> dict`
  (`scripts/harness.py:2485`). No save/restore. Since v0.21 it also
  carries two optional fields — `assumptions` and, since slice 2,
  `proposer` — **`None` on every session this skin serves**, and
  attached only by the session ledger's recorder and replayer or by a
  gate runner (`docs/DESIGN-session-ledger.md` §3,
  `docs/DESIGN-plain-input.md` §2.2). ¶AMD-1 records the wire-schema
  debt that falls due the day either is attached here.
- **`ConversationSession`** (`scripts/conversation.py:126`) — the
  key-signed, owner-private slot-filling session:
  `say(utterance) -> Turn` (`scripts/conversation.py:253`) over the
  bounded request grammar (`scripts/request_grammar.py`).
- **`ProtocolSession`** (`scripts/protocol_runtime.py:276`) — ¶AMD-3's
  addition: the protocol runtime's uptake session, owning an episode stack,
  one pending need, and an append-only list of `ProtocolUptake` receipts.
  `submit_utterance(surface, context_signals)` and
  `submit_reply(request_id, answer, context_signals)` are its whole input
  surface. The utterance reaches the sealed protocol corpus
  (`protocol/protocols.json`) as an exact normalized lookup key and by no
  other channel; the returned witnesses, never the surface bytes, enter the
  admission predicate beside the context signals.

The first two drive the same `Controller`/verifier machinery
(`scripts/controller.py`); the third drives the protocol runtime's own
verifier over the sealed protocol corpus. **The skin still adds no path of
its own** — that is what "no third path" was always about, and it remains
true of a three-profile server: ¶AMD-3 registers a third *engine* object and
renders it, exactly as A-IH6 requires, rather than inventing a surface inside
this file. A chat conversation selects which object serves it via the
request's `model` field (§3). The TTY is today the interactive skin over `CoreSession`
(`harness.main()`, `scripts/harness.py:2593`); `ConversationSession` has
so far been driven by tests and a scripted demo printer, so HTTP is the
**first interactive skin** over that object — which is why its mapping
(§6.2) carries the P-IH6 adjudication.

**¶DEV-1 — replay, not resumption (a recorded deviation).**
DESIGN-interactive-harness §4.3 permits HTTP to *resume a durable
session* only through `ConversationSession.restore` after presenting a
key ring. This skin **does not resume durable sessions at all**: every
request is served by replay into a fresh session object (§4), no ledger
snapshot is imported, no stored authority is asserted, and
`save`/`restore` are not in the serving path. The §4.3 clause is
therefore not exercised rather than violated; durable restore over HTTP
remains unshipped and unclaimed (§10, non-claims). The one-owner,
loopback-only scope (§2) is what makes replay honest: there is no second
owner whose state a replayed conversation could touch.

## 2. Endpoints

`scripts/serve_chat.py`, stdlib only (`http.server`), bound to
`127.0.0.1`, one owner, no auth (per the substrate's shipped
single-session contract; multi-tenant auth is a stated non-goal).

| Method & path | Purpose |
|---|---|
| `POST /v1/chat/completions` | the OpenAI-compatible subset (§4–§6) |
| `POST /v1/responses` | Responses-compatible text subset for current Codex CLI (§4.2, §6, §8) |
| `GET /v1/models` | lists the three profiles (¶AMD-3) in the standard `data` list and the additive Codex `models` catalog |
| `GET /v1/capabilities` | the **capability sheet** (§7), vendor extension |

Anything else: `404` with a JSON error object in the OpenAI error shape.

## 3. Profiles (the `model` field)

| `model` | session object | grammar | one-line description |
|---|---|---|---|
| `corollary/kernel` | `CoreSession.boot(repo_root, offline=True, session_id=…)` | registered line grammar (§5) | corpus answers, exact evaluation, ownership, belief, story, refusals |
| `corollary/conversation` | the slot-filling session (`scripts/conversation.py:439`, `keyring=` an ephemeral per-conversation ring) | `request_grammar.parse_request` | signed slot-filling with minted clarification questions |
| `corollary/protocol` (¶AMD-3) | a **fresh** `protocol_runtime.ProtocolSession` over the sealed protocol corpus — *not* the slot-filling session and *not* kernel line routing | none: the request surface **is the protocol runtime**, which takes the normalized utterance as an exact corpus lookup key and admits a transition only from the returned witnesses and the declared context signals | an ordinary turn taken as a registered interaction move; materially different transitions pause instead of guessing |

Unknown `model` → `404` (error shape, code `model_not_found`), and the
refusal names all three profiles.

**¶AMD-3 replaced a fall-through, not an allowlist.** Until this amendment
`ChatEngine._fresh` read *"kernel, else the slot-filling session"*, so every
non-kernel model — registered or not — constructed the conversation profile's
demo session. Adding `corollary/protocol` to the model list alone would
therefore have served the new profile as the two-slot demo. `_fresh` and
`_render` are now explicit three-way dispatches over `serve_chat.PROFILES`
that raise rather than fall through, so a fourth profile cannot be
half-registered.

The protocol profile's context signals are derived from real session state or
are honestly absent, and nothing in between. `pending_need` is the session's
own pending need (its slot while one is open, the absence sentinel `ABSENT`
otherwise — and a reply reports the need it binds as no longer outstanding,
because the need a result answers is not a need outstanding *for* that
result); `protocol_stack` is the session's own stack through the runtime's
top summary. `quote_boundary`, `expected_output_slot` and `active_task` have
**no HTTP source event in this slice**: they carry `ABSENT` under the event
id `evt-http-no-source`, and the capability sheet publishes that fact rather
than hiding it, on the gloss row's precedent. Deriving a quote boundary from a
quoted-looking user line would be exactly the lexical trigger the protocol
design abolishes.

`corollary/kernel` uses the offline **boot**: the three optional probes
are forced OFF, so the served routes are the offline-registered ones and
the sheet says so (M-note: this is the offline *boot* of P-IH1's
scenario, not P-IH1's four-leg surface — two of those legs are
programmatic, not line-reachable).

The conversation profile's answerable surface is exactly the bounded
request grammar: two slots, closed value vocabularies, rules R0–R7
(`scripts/request_grammar.py:81-162`, `:325-334`). The sheet publishes
that grammar because it *is* the registered surface. Per **P-IH3**, no
demo name ("golden-chicken", "Sally–Anne") appears in `/v1/models`, the
sheet, or any served description; those names stay in selftests and
docs. The profile is described as what it is: the signed slot-filling
session. One boundary made explicit (implementation review,
2026-08-22): the session's own minted clarification prompt quotes its
slot literal — "the golden chicken's eggs" — and §6's verbatim-content
rule carries it; that is the engine's record crossing the wire, not a
listing or description, so P-IH3 (which governs help/UX destinations)
is not breached and the renderer does not scrub it (A-IH6 forbids
rewriting the record). A demo-neutral literal would be an engine
change, out of this cycle's scope.

## 4. Request mapping: messages in, session state out

Chat completions is stateless per request; the engine is stateful per
session. The mapping rule:

- The `messages` array's **user turns, in order**, are the session's
  input lines — and on `corollary/protocol`, so are its admitted
  tool-result items (¶AMD-3), which is the one place this sentence widens.
  Call the two together the **input items**; the served turn is the last of
  them, which on the two shipped profiles is the last user turn exactly as it
  always was, because a tool-result item cannot reach those profiles at all.
  Turn *n*'s response is computed by replaying input items
  1…*n* into a fresh session object and rendering the last result.
  Replay is deterministic: the kernel profile passes
  `session_id=sha256(prefix)` (the canonical message-prefix hash,
  §4.1) to `CoreSession.boot` — the parameter exists for exactly this
  (`scripts/harness.py:484-492`) — and the conversation profile derives
  its **owner** name from the same hash over an ephemeral ring (the
  constructor exposes `owner` and `keyring`,
  `scripts/conversation.py:439-442`). The engine's internal
  `RetrievalState.session_id` on that profile stays ephemeral and
  **never crosses the wire**; the wire field
  `x_corollary.session.profile_session_id` is the server-side
  conversation identity — the §4.1 prefix hash — on both profiles.
- The server MAY keep a session cache keyed by the prefix hash, feeding
  only the final user turn into a cached session. The cache is an
  optimization and must be replay-equivalent; the adjudicating tests run
  one scenario both ways (cold and cached) and assert identical bodies
  modulo `id` and `created` only — which is checkable because every
  `x_corollary` field is replay-invariant by construction (§6 defines
  no field, such as a replay counter, that could differ).
- `assistant` turns in the incoming array are the client's transcript
  claim, not an input channel. **Divergence check, defined exactly:**
  the claimed `content` string is compared to the replayed turn's
  `content`, both normalized by splitting on `"\n"`, `rstrip()`ing each
  line, and dropping trailing empty lines. Role must be `assistant`.
  Nothing else — not `x_corollary`, not whitespace inside a line's
  body — participates. Mismatch → `409`, code `transcript_divergence`.
- `system` turns are **accepted and ignored**, and the response says so:
  every ignored input is listed in `x_corollary.ignored` (§6). The
  engine has no system-prompt channel; inventing one would be a new
  answerable surface, which this cycle forbids.
- Sampling parameters (`temperature`, `top_p`, `n`, `seed`, …) are
  accepted and ignored, listed in `x_corollary.ignored`. There is
  nothing to sample: no token in the serving path is drawn from a
  generative model.
- **Tool-result items (¶AMD-3), `corollary/protocol` only.** A message
  `{"role": "tool", "call_id": …, "output": …}` — the chat-completions
  spelling of the Responses `function_call_output` item of §4.2 — is an input
  item, replayed through `ProtocolSession.submit_reply`. Its `call_id` binds
  to the pending `request_id` and **to nothing else**: an unknown, stale,
  cross-request, cancelled or repeated result is refused, the session stays
  WAITING where it was waiting, no stack mutation occurs, and no value is
  invented for the slot. On every other profile the item is a `400
  invalid_message`, unchanged, because no other profile has a pending request
  for one to bind to.
- **The protocol profile's session identity (¶AMD-3).** The runtime derives
  its `request_id` from its own session id, so a `call_id` can survive ¶DEV-1's
  replay only if that id is the same on every request of one conversation. The
  §4.1 prefix hash is not — it grows with the transcript — so this profile
  threads the canonical hash of the conversation's **first message item**, the
  one part of a transcript replay cannot change. The wire field
  `x_corollary.session.profile_session_id` is unchanged on all three profiles:
  it stays the §4.1 prefix hash of the current request.
- `stream: true` is supported (§8). `n != 1` → `400`. A request with no
  `messages` array or no user turn → `400`. An empty-string user turn is
  **served**, not rejected: it is the engine's registered empty line
  (§5 row 0, pinned by `tests/test_harness_line.py:360-366`).

### 4.1 Canonical prefix hash

`sha256` over the UTF-8 bytes of
`json.dumps([<serialized item> for each item in the prefix],
ensure_ascii=False, sort_keys=True, separators=(",", ":"))`. The prefix
for turn *n* is every message strictly before the final input item. The
same serialization discipline (call it **canonical-JSON/compact**) is
used everywhere this spec says "canonical": `json.dumps(value,
ensure_ascii=False, sort_keys=True, separators=(",", ":"))`, encoded
UTF-8.

**¶AMD-3 extends the per-item serialization, and the extension is additive.**
A message item serializes to `[role, content]`, exactly as it always did, so
a prefix of only role/content pairs hashes to the byte it hashed to before —
which is why every kernel and conversation replay test stays green and is
asserted to, against §4.1's rule written out independently in the suite. An
admitted tool-result item serializes to its **type token and its typed
payload**: `["function_call_output", {"call_id": …, "output": …}]`. Flattening
it into a string would have made two transcripts differing only in a tool
result's payload hash identically — so a tampered result would have been
served out of the untampered one's cache entry, and §4's divergence check
could never have seen it. Two such transcripts therefore hash differently and
the one whose assistant claim no longer matches the turn its own tool result
produces is refused with `409 transcript_divergence`; that pair is a test, not
a promise.

### 4.2 Responses request mapping

The Responses skin accepts `input` as either one string (one `user` turn) or
an array of message items. A message item has `role` and text-only `content`;
content may be a string or an array of `input_text`/`output_text` parts. The
skin converts those messages to §4's request mapping and calls the same
`ChatEngine.serve` method. Multimodal parts and non-message input items are
refused rather than guessed — **with exactly one amended exception, below**.

`instructions`, tool declarations, reasoning controls, sampling controls, and
other Responses fields are accepted but ignored and named in
`x_corollary.ignored`. In particular, this deterministic engine neither needs
nor uses a preprompt and never emits a tool call **except on
`corollary/protocol`'s one registered prompt path (¶AMD-3, §8)**.
`previous_response_id` resumes only an in-process replay transcript produced
by this server; an unknown id is refused. Nothing durable is restored,
preserving ¶DEV-1.

> **¶AMD-3, §4.2's amended refusal — exactly one item type, exactly one
> profile.** On `corollary/protocol`, an input item
> `{"type": "function_call_output", "call_id": …, "output": …}` is **admitted**
> and mapped onto §4's tool-result item. `call_id` and `output` must both be
> strings; a missing or empty `call_id` is a `400 invalid_input_item`, because
> a tool result with no call id binds to no pending request. Every other
> non-message item — a `reasoning` item, a `function_call` echo, a multimodal
> part — still refuses with `400`, on this profile and on every other, and a
> `function_call_output` on either shipped profile refuses too.
>
> The `output` string is mapped onto the pending need's `answer_schema` and
> **nothing is invented**: the result is a `{protocol_id, move_id}` pair drawn
> from the *pending candidate set*, or nothing at all. A bare move id, a
> `protocol_id/move_id` pair, and a JSON object carrying `move_id` (or the
> host's `value`/`answer`/`label`/`text`, including inside a single-element
> `answers` array) all resolve; an empty string, a cancellation, a free-form
> "Other", and a move that was never a candidate all resolve to nothing and are
> refused as `UNBOUND_ANSWER` with the session still WAITING. That is the
> design's rule that cancellation or an unavailable UI remains WAITING.
>
> A request whose `input` contributes only a `function_call_output` — the
> resume turn, with `previous_response_id` supplying the transcript — is
> accepted on this profile; the `missing_user_text` refusal still applies
> everywhere else.
>
> On this profile the Responses body keys `tools` and `tool_choice` are
> **acted on** and therefore do **not** appear in `x_corollary.ignored`:
> `tools` decides whether the registered adapter fires, and
> `tool_choice: "none"` suppresses the call (the need is still opened, and is
> presented as text). `parallel_tool_calls` stays in the ignored list, and
> honestly so — the client's value changes nothing, because this profile emits
> at most one call whatever it says — while the response body publishes
> `parallel_tool_calls: false`, which **agrees** with the catalog's
> `supports_parallel_tool_calls: false` for this profile. The shipped
> profiles' pre-existing disagreement between those two keys is out of this
> amendment's scope and is deliberately not copied here. The body's `tools`
> key echoes **exactly the declarations this profile took up** — the one
> registered adapter, or an empty list — rather than the client's whole
> advertisement, so a client can read what was and was not taken up.

> **¶AMD-2 — Codex model discovery is additive (2026-08-28).** A live
> Codex CLI 0.150.1 TUI replay reached `/v1/responses` but first warned that
> `corollary/kernel` had no metadata; its `/v1/models` probe rejected the
> standard OpenAI `{object, data}` list because it expected a top-level
> `models` array. The endpoint therefore keeps the standard list byte-for-byte
> in `data` and adds the catalog Codex reads. Each catalog item is deliberately
> text-only and non-agentic: `slug`, `display_name`, `description`, one inert
> `medium` reasoning level, `shell_type: "disabled"`, `visibility`,
> `supported_in_api`, `priority`, an
> empty instruction template, all three usage-instruction switches false,
> `support_verbosity: false`, a token truncation policy,
> `supports_parallel_tool_calls: false`,
> `experimental_supported_tools: []`,
> `input_modalities: ["text"]`, and the transport budget `context_window`.
> No executable shell, apply-patch, search, image, or tool-mode metadata is
> published.
> `tests/test_serve_chat.py::CapabilitySheet::test_model_list_serves_standard_and_codex_catalogs`
> pins the complete key set so a capability claim cannot enter quietly.
>
> The client-side launch also uses `--disable apps --disable plugins`: this
> standalone model cannot consume their instructions or calls, and a host-owned
> `codex_apps` MCP startup was the measured 13.5-second block before the user
> interrupted the first TUI turn. With the amendment and those switches, the
> unmodified CLI completed `hello` in 3.1 seconds with no provider, metadata,
> MCP, or skill-budget warning. These are compatibility observations, not a
> claim that the harness implements Codex's agent tools.

## 5. The registered line grammar is the request surface (kernel profile)

The kernel profile routes exactly `route_line`'s chain
(`scripts/harness.py:2485-2550`; this citation read `:1393-1437` until
v0.21, which DESIGN-plain-input §2.2 had already recorded as stale with
the instruction to correct it whenever a design next touched that file —
the session ledger did, and slice 2's row-12 pre-router moved it again,
from `:2272-2335` on 2026-08-26, and DESIGN-house-rules' `declare` row moved it again from `:2305-2368` on 2026-09-01 — that slice added a `declare` branch to the chain and an optional `symbols` field to `CoreSession`, so every citation into this file below the field list shifted by thirteen lines and is corrected in the same change) — first match wins, statuses verbatim:

| # | line form | route | statuses |
|---|---|---|---|
| 0 | empty | `none` | `waiting` |
| 1 | `narrow <corpus\|discipline\|word\|id> <value>` / `cancel` (only while candidates pend) | `resolver_context` | `found`, `waiting`, `canceled`, `cycle`, `hop_ceiling` |
| 2 | `owns <template-expr>` | `ownership` | `solved`, `exhausted`, `refused` |
| 3 | `suppose <claim>` | `evaluate` or `supposition` | `solved`, `held`, `waiting`, `refused` |
| 4 | `retract <assumption-id>` — **session ledger, v0.21** | `retraction` | `canceled`, `refused` |
| 5 | `twin <statement-id>` — **wiring step W1, §9** | `twin` | `found`, `exhausted`, `refused` |
| 6 | `reachable <world-id> <target-path>` — **wiring step W2, §9** | `closure` | `found`, `exhausted`, `refused` |
| 7 | `conform <statement-id> <bindings>` | `conform` | `found`, `refused` |
| 8 | story request (`story.is_story_request`) | `story` | `found`, `waiting`, `exhausted` |
| 9 | belief narration + `where does A think B is` | `belief` | `found`, `waiting`, `exhausted` |
| 10 | computable relation/expression | `evaluate` | `solved`, `refused` |
| 11 | repo-relative path | `write_gate` | `PROVEN`, `VERIFIED`, `REFUSED` (uppercase `Verdict` pass-through) |
| 12 | free text the graph claims | `resolver` | `found`, `waiting` |
| 13 | `what is X` / `define X` (dictionary word) | `gloss` | `found` — **unreachable on this profile**: the offline boot forces `retrieve.wordnet` OFF and `_route_gloss` then declines; the sheet lists the row as off rather than hiding it |
| 14 | everything else | `dispatcher` | `exhausted` |

**Row 4 is new in v0.21** and is the session ledger's lifecycle surface
(`docs/DESIGN-session-ledger.md` §3). The Assumption record's status
alphabet registers `retracted`, and supersession happens on its own when a
person re-supposes the same subject, so withdrawal is the one transition
that needed a word. **On this skin the row always refuses**: ¶DEV-1
replays every request into a fresh session and attaches no assumption set,
so `retract` finds no ledger and returns `refused` with
`refusal_type: unknown_assumption`. The row is published rather than
hidden for the same reason the gloss row is — a capability that is off is
a fact the sheet should carry.

**And the refusal is byte-identical with a ledger and without one.** An id
no live assumption carries refuses with one sentence in both cases. That is
not cosmetic: the first version rendered the two cases differently, the
session ledger's B10 caught it on ten turns of the sealed corpus, and it
stopped the slice before serving. A refusal that names whether a ledger
exists is session state reaching the bytes of an answer that consumed no
assumption (`docs/DESIGN-session-ledger.md` §7 B10; the repair is
registered in `experiments/session_ledger_prereg.json` amendment 3).

The rows for `conform` and the `evaluate` route's registered-bound
`refused` (E0e) were already served and already in `LINE_GRAMMAR`; they
are written into this table for the first time here, because a served
route missing from the normative table is the drift this document exists
to catch.

The **status alphabet is frozen as a closed set**, inconsistencies
included: lowercase `waiting, solved, refused, exhausted, found, held,
canceled, cycle, hop_ceiling, conditional` plus the write-gate's uppercase
pass-through, whose reachable values are `PROVEN`, `VERIFIED`, `REFUSED`
(`scripts/harness.py:854-860`; pinned by
`tests/test_harness_line.py:274,301`), plus `abstained` — the one
skin-assigned status, conversation profile only, declared in §6 for the
branch that runs no turn. The skin transports the engine's
vocabulary; it does not edit it. Normalization would be the renderer
rewriting the record, which A-IH6 forbids.

> **¶AMD-1 — `conditional` joins the alphabet (2026-08-26).** The set is
> frozen, so this is an amendment and not an addition made quietly.
> `docs/DESIGN-plain-input.md` §3b mints `conditional` for an answer served
> under a stated supposition: *a different speech act than an answer*, and
> the design's honesty argument requires it to have its own status rather
> than borrow one. `held` was the tempting reuse and is refused for a
> measured reason — `held` is already in `ANSWERING_STATUSES`
> (`scripts/serve_chat.py`), so reusing it would make every conditional
> answer score as an answer in the throughput metric, "precisely the
> accounting this design must not have". The shape has a precedent in this
> spec already: the `closure` route's certified negative is non-answering
> for scoring and carries its receipt verbatim (§6.1).
>
> **What bumped, and what did not.** `corollary.capabilities/1` →
> **`corollary.capabilities/2`**: the sheet is what publishes the alphabet,
> so widening the alphabet changes the sheet's contract.
> **`corollary.chat` stays at /1**, and not to save work — *no status
> reachable on that wire changed.* The proposer is attached to a
> `CoreSession` the way the session ledger attached `assumptions`: opt-in,
> `None` by default, set only by a recorder or a replayer. ¶DEV-1 replays
> every HTTP request into a fresh session that has neither, so this skin
> cannot emit `conditional` today. Bumping the wire schema would rewrite 732
> references including the session ledger's **closed** corpus seal and all
> 119 task records in `experiments/throughput_tasks.json` — moving a sealed
> denominator on account of a status that cannot appear in it.
>
> **The debt, recorded so it cannot be forgotten:** the day the proposer is
> attached to a session this skin serves, **`corollary.chat/2` is owed**.
>
> `conditional` is non-answering for scoring, and that is mechanical rather
> than documentary: `measure_throughput.NON_ANSWERING_STATUSES` carries it
> and `measure_throughput.useful_tokens_are_forfeited_by` is what the
> useful-token computation calls, so a conditional turn contributes zero
> useful tokens **whatever its content length**. Gate G7b drives that
> function directly rather than re-implementing its reasoning.

## 6. Response mapping: what `content` is, and what rides beside it

**`content` is the verbatim pass-through of the engine's rendered
answer, and nothing else.** It is the useful-token surface the
throughput metric counts, so the rule leaves the skin zero rendering
freedom:

- Kernel profile: `content` = `"\n".join((*reading, *answer))` when the
  verdict dict carries a `reading` (the `resolver_context` found case,
  `scripts/harness.py:1232-1241` — the TTY renders both, so the skin
  must too); else `"\n".join(answer)` when `answer` is present; else the
  `detail` string. The skin may not add, drop, reorder, re-render, or
  re-parameterize lines; the engine's rendering as committed at the
  task-book-seal tip is the rendering the registered run measures, and
  **any change to engine rendering after the task book seals voids the
  run** (this closes the verbosity-inflation hole: the skin has no
  selector, and the engine's selector is frozen by the seal).
- Conversation profile: `content` = `Turn.reply`, else `Turn.asked`,
  else — only when `Turn.abstained` — the skin-authored acknowledgement
  `"noted; {slot} stays unknown"` with `{slot}` = `turn.parsed.slot`
  (`scripts/request_grammar.py:167,172`; the abstain rule always
  populates it). A `Turn` with `abstained=True` carries no text
  (`scripts/conversation.py:278-281`), so this one string is
  unavoidable; it is **named as the single exception** to §10's
  no-skin-authored-tokens rule.

  The conversation profile's `x_corollary` fields, defined here because
  `Turn` carries no status of its own: `status` ∈ {`solved`, `waiting`,
  `abstained`} — the first two verbatim from
  `session.turns[-1].stop_reason.value` (the reply and ask shapes both
  run a turn, `scripts/conversation.py:305`, `:324`); `abstained` is a
  **spec-declared status** for the one branch that runs no turn
  (`:278-281`), listed in §5's frozen alphabet as skin-assigned on this
  profile only. `detail` = `ParsedRequest.rule_id` on an understood
  turn, `ParseFailure.reason` otherwise — both engine data
  (`scripts/request_grammar.py:167-196`). The abstention exclusion is
  therefore mechanical, not string-matched: **the stopwatch scores
  `status == "abstained"` as zero useful tokens**, and the same rule
  covers every clarification turn via `status == "waiting"`.

- **Protocol profile (¶AMD-3):** an `ASK` turn's `content` is the verifier's
  own minted prompt — a WAITING turn is a complete assistant turn that asks a
  question, exactly as on the conversation profile. Every other disposition
  renders a **minimal mechanical receipt summary**, read field by field out of
  the `ProtocolUptake` record:

  ```text
  disposition: ENTER
  family     : greeting
  protocol   : protocol.greeting.a
  move       : greet
  ```

  and, where no move was selected, `disposition` plus the verifier verdict
  that names which rule refused. This is an **inspectable rendering, not
  conversational prose**: no sentence bank, no stored templates (DESIGN §10's
  stop condition), and no phrase carrying information the record does not.
  The direction matters as much as the shape — **a rendered phrase never
  enters the admission predicate.** Replay reads user turns and admitted tool
  results; the assistant text this skin produced is compared for divergence
  and is never an input to a transition, which the suite asserts by feeding a
  served summary back as a user turn and getting a `REFUSED` lookup miss.

  This profile's `x_corollary` fields: `route` = `protocol`; `status` ∈
  {`found`, `waiting`, `refused`}, mapped from the disposition
  (`ENTER`/`SUSPEND`/`CONTINUE`/`RESUME`/`EXIT` → `found`, `ASK` → `waiting`,
  `REFUSED` → `refused`) and all three already in §5's frozen alphabet;
  `detail` = the verifier's own verdict (`ADMITTED`, `MATERIAL_AMBIGUITY`,
  `UNLICENSED`, `WAITING_LOCK`, `UNKNOWN_REQUEST`, `CONSUMED_REQUEST`,
  `UNBOUND_ANSWER`, `INVALID_INPUT`, `STACK_DEPTH_CAP`), which is what makes a
  refusal readable; and **`uptake`** = the `ProtocolUptake` record verbatim,
  present on *every* turn including `waiting` and `refused` ones, because
  DESIGN §3 requires `authority_delta` to be a present, plaintext, empty field
  on the ASK and REFUSED paths rather than something inferred from a digest.
  `uptake` is deliberately not the §6.1 receipt: the record is not a grounding
  claim.

Two scoring notes restated from the design so no implementer rediscovers
them: refusal and clarification turns contribute **zero** useful tokens
whatever their `content` length (so the dispatcher's echo of the user's
line, `scripts/harness.py:937-942`, inflates nothing), and the
stopwatch counts `content` itself, client-side, with the pinned baseline
tokenizer — it never reads the server's `usage` block. `usage` is
**informational only**, counted with the same tokenizer when the pinned
tokenizer file is present, omitted (never approximated) when it is not;
the tokenizer pin itself lands with the baseline manifest, later in the
preregistration order.

The seal-freeze above gets a **witness** so the void condition is
checkable rather than honor-system: the task book records canonical-LF
SHA-256 digests of the rendering modules (`scripts/answer.py`,
`scripts/evaluate.py`, `scripts/ownership.py`, `scripts/belief.py`,
`scripts/story.py`, `scripts/harness.py`, `scripts/closure_query.py` —
W2 renders through its `display_lines` — plus `scripts/resolver.py`,
`scripts/supposition.py`, `scripts/gloss.py`, and
`scripts/retrieval.py`, whose minted ids and prompts surface in answer
and waiting lines), and the registered run revalidates them before
timing anything. **Re-sealing rule (added 2026-08-22, before the
registered run):** a witnessed module may change before the registered
run only through an explicit re-seal — the change must alter no
rendered byte (proven by byte-identity tests), the book is rebuilt so
only `rendering_module_digests` moves (verified in the diff), and the
commit records the reason. After the registered run the original
sentence stands unqualified: a change voids the run. **Post-run clause
(added 2026-08-22, at v0.17 rotation):** the registered run's numbers
stay frozen against the digests they were measured under; a later
cycle that changes a witnessed module's rendered bytes does not
"re-seal" this book — it retires this witness for future comparisons
and seals a **new** book of its own, with the old artifact and its
digests left untouched as the record of what was measured.

Everything else rides in the vendor extension:

```jsonc
"x_corollary": {
  "schema": "corollary.chat/1",
  "profile": "corollary/kernel",
  "route": "resolver",            // or "conversation"
  "status": "found",              // engine vocabulary, verbatim
  "detail": "…",
  "evidence": ["…"],              // write-gate evidence when present
  "receipt": { … },               // always present; §6.1 fixes its shape per (route, answered?)
  "need": { "slot": "…", "prompt": "…" },   // §6.2 — conversation profile only
  "ignored": ["system[0]", "temperature"],
  "session": { "profile_session_id": "…" }  // = the §4.1 prefix hash; replay-invariant
}
```

`finish_reason` is always `"stop"`: a WAITING turn is a *complete*
assistant turn that asks a question, not a truncation.

### 6.1 Receipts

Receipts are keyed on **(route, answered?)**, not route alone: any
non-answering status — `exhausted`, `refused`, `waiting`, `canceled`,
`cycle`, `hop_ceiling`, `abstained`, uppercase `REFUSED` — carries no
grounding claim, **with two named exceptions, both on the `closure`
route**: `exhausted` is a *certified bounded negative* —
`closure_query` proves NOT_REACHABLE_WITHIN_HORIZON and mints a receipt
for it — so it is an **answering** turn carrying its
`closure-receipt/1` verbatim (the task book scores it as an answerable
task); and the `refused` minted for CORRUPT_TARGET also carries its
receipt verbatim, because `closure_query`'s own doctrine is that
CORRUPT_TARGET *is* an answer about the target's bytes — it stays a
refusal for scoring (zero useful tokens) but the wire does not strip
the certificate. Every other non-answering status gets
`{"missing_capability": …}` when the engine names one
(`scripts/harness.py:974-984`, `:1289-1295`, `:1322-1328`) and an empty
receipt otherwise. Answering turns populate per route, for T7's
client-side revalidation against committed artifacts:

| route (answered) | receipt fields |
|---|---|
| `resolver` / `resolver_context` | `statement_id`, `corpus_path` (the committed `data/*/nodes.json`), `node_sha256` = sha256 of the node's record serialized canonical-JSON/compact (§4.1) |
| `ownership` | `query_skeleton`, `hosts`, `searched`, `by_corpus` (top entries) — recheckable against `data/` |
| `twin` (W1) | `ledger_path` (`reports/signature_matches.json`), `level`, `group_index`, `member_ids` |
| `closure` (W2) | the `closure-receipt/1` object `closure_query.query` returns, verbatim |
| `evaluate` | `expression`, `exact` (evaluation turns only — a relation check has no single value and carries `expression` + `grounding` alone), `grounding: "computed"` — plus the engine's own honesty line in `content` ("no corpus statement was consulted") |
| `story` | `constraint_ids` (= `story.CONSTRAINT_IDS`, `scripts/story.py:57-62`), `corpus_path` (`data/narrative/nodes.json`) — the story's four constraints are committed corpus statements and the receipt says so |
| `belief`, `supposition` | `derivation: "session"` — derived entirely from the conversation's own typed narration or owned frame, no external artifact claimed |
| `write_gate` (`PROVEN`/`VERIFIED`) | `grounding: "working-tree"` — the gate's own `evidence` lines already ride in `x_corollary.evidence` (`scripts/harness.py:859`) and are the record |
| `conversation` (`solved`) | `binding: {slot, value, lifetime}`, `derivation: "user-frame"` |
| `protocol` (`found`) — ¶AMD-3 | `uptake_id`, `corpus_path` (`protocol/protocols.json`), `protocol_witnesses` (the node ids the selected move rested on), `grounding: "protocol-corpus"` — recheckable against the committed corpus |

A receipt never claims an artifact the answer did not rest on; routes
with no artifact say so (`"computed"` / `"session"`) instead of citing
something decorative.

Scoring against these receipts uses **subset assertion**: a task book's
`receipt_expect` (and `need_expect`) constrains only the keys it names —
every named key must match; absent keys are unconstrained. The wire may
carry more (e.g. `shortest_route` on a REACHABLE closure receipt) than
a task chooses to pin.

### 6.2 WAITING crosses the wire (P-IH6)

Two WAITING shapes exist and the spec refuses to blur them:

- **Kernel profile:** `route_line` never mints a `Need` — its WAITING
  results carry only `detail` (and sometimes `answer` lines listing
  candidates) and resume via `narrow …` / `cancel` exactly as the TTY
  does (`scripts/harness.py:1419`). No `need` field is emitted; there is
  nothing to put in it. The `cycle` and `hop_ceiling` terminators cross
  the wire as ordinary statuses — the server does not exit the way
  `harness.main()` does, but pending state clears exactly as
  `_route_pending_context` already clears it (`scripts/harness.py:1192,
  1213, 1245`).
- **Conversation profile:** a turn that asks carries
  `x_corollary.need` = `{slot, prompt}` — the exact two fields the
  `Need` protocol exposes (`scripts/harness.py:329-344`) — with
  `content` = the question. **The next user message is the reply**, and
  it binds through `verifier.reply_action` — the signed channel
  (`scripts/conversation.py:305` → `:248` → `scripts/retrieval.py:1615`)
  — mirroring
  `tests/test_ask.py::test_signed_reply_resumes_same_session_and_binds_user_frame`
  across the transport.
- **Protocol profile (¶AMD-3):** a turn that asks carries
  `x_corollary.need` = `{slot, prompt, request_id, options}`. The two extra
  fields are not decoration and are not available to the conversation
  profile's shape: `request_id` is what a `call_id` binds to, and `options`
  is the unresolved candidate move ids in canonical order — the same list the
  function-call arguments carry. Resumption has **two** channels and they are
  the same fact in two representations: a registered `function_call_output`
  whose `call_id` is that `request_id` (§4.2, §8), or, under the text
  fallback, the next tool-result item in the transcript. There is no
  "the next user message is the reply" rule here — a bare user turn while a
  need is pending is refused as `WAITING_LOCK`, because a protocol move is
  not a slot value and guessing which candidate a sentence meant is the thing
  the ASK exists to avoid.

**T1's WAITING leg is adjudicated on `corollary/conversation`**, the
profile that carries a need record; the spec says so here so the gate
does not discover it.

**The negative, stated as what the wire can falsify.** The transport
carries no signatures — signing is server-side, minted by the verifier
from the value the user actually sent. So the wire-adjudicable negative
is: (a) an unparseable or absent reply yields another ASK and never a
filled slot (`scripts/conversation.py:274-277`, `:310-325`); (b) a reply
naming a different slot while one is awaiting is refused with `409`, not
reinterpreted (`scripts/conversation.py:291`); (c) the server never
substitutes a default, placeholder, or invented value for a missing
slot — adjudicated by asserting the bound value equals the sent value,
byte for byte, and that no slot binds on any turn where the user sent
none. The in-process forgery negative
(`test_policy_cannot_guess_user_reply_signature`) stays adjudicated
where it lives — inside the process, where signatures exist; the HTTP
test does not pretend to mirror it.

## 7. The capability sheet (`GET /v1/capabilities`)

The self-configuration surface an attaching orchestrator reads once, the
way it reads a tool schema:

```jsonc
{
  "schema": "corollary.capabilities/1",
  "profiles": { "corollary/kernel": …, "corollary/conversation": … },
  "line_grammar": [ { "form": "owns <template-expr>", "route": "ownership",
                      "example": "owns x ^ 2", "statuses": ["solved","exhausted","refused"],
                      "served": true }, … ],
  "request_grammar": { "slot_phrases": …, "slot_values": …, "rules": … },
      // from request_grammar.SLOT_PHRASES / SLOT_VALUES / coverage()
  "boot_matrix": [ { "subsystem": "corpus.nodes", "liveness": "OK",
                     "optional": false, "detail": "…" }, … ],
  "statuses": { … the frozen closed alphabet of §5 … },
  "protocol_grammar": { … ¶AMD-3, generated from protocol/protocols.json … },
  "prompt_tool_adapters": [ { "name": …, "parameters_sha256": …,
                              "provenance": … } ],
  "honesty": "offline boot; unregistered paths abstain (P-IH4); no generative path"
}
```

The sheet is generated from the live objects (the boot matrix's records,
`request_grammar.SLOT_PHRASES`/`SLOT_VALUES`/`coverage()`, the routing
table) — never a hand-maintained copy that can rot. Rows the profile
cannot serve (gloss under offline boot) appear with `"served": false`
rather than disappearing. No demo name appears anywhere in the sheet
(P-IH3).

**¶AMD-3's two new blocks, and the three rows that did not move.**
`protocol_grammar` is generated from the sealed corpus itself — schema,
generator, normalization rule, predicate language, absence sentinel,
families, move kinds, context-signal ids, stack depth cap, and one row per
corpus move with its required signal-value predicates — so a regenerated
corpus republishes itself instead of disagreeing with a copy. It also
publishes `served_context_signals`: which signals this profile derives from
session state, and which three carry `ABSENT` because **no HTTP source event
exists for them in this slice**. That is the gloss row's precedent applied to
a signal: a client can see that a `quoted_datum` move is unreachable over
HTTP here, rather than discovering it from an unexplained refusal.
`prompt_tool_adapters` publishes every registered prompt adapter with its
**provenance**, because a registered adapter a reader cannot trace back to
U-P1's capture is indistinguishable from the guessed adapter the design
forbids. The kernel's `line_grammar` rows, the conversation's
`request_grammar`, and the `honesty` string are **byte-unchanged**, and the
suite asserts that positively rather than by omission.

## 8. Streaming

`stream: true` returns SSE chunks in the OpenAI chunk shape. Chunk
boundaries are rendered lines of `content` (already-accepted content
only; there is nothing else to stream), and **every chunk after the
first carries its leading `"\n"`**, so concatenating all deltas
reproduces `content` byte-for-byte — which is what keeps §4's
divergence comparison stable for a client that reassembles a streamed
turn and sends it back. The final chunk carries
`finish_reason: "stop"`; `x_corollary` rides on the final chunk; a
`usage` chunk is sent only when the client asks via
`stream_options.include_usage`, matching the OpenAI contract. One
honesty note for the gate: the kernel computes the whole verdict before
rendering, so time-to-first-useful-token ≈ time-to-completion; streaming
here is protocol fidelity, not a latency claim, and T4's TTFT leg is
expected to be won by being fast, not by streaming early.

The Responses endpoint emits the standard named SSE lifecycle through
`response.completed`: created, output-item added, content-part added, text
delta/done, content-part done, output-item done, completed. Text deltas
concatenate byte-for-byte to the same engine rendering. The completed
response carries `x_corollary`; **no synthetic tool or reasoning item is
introduced — and ¶AMD-3 does not introduce one either.** The one function-call
item this skin can emit is not synthetic: it is a verifier-minted, already
approved `ClarificationRequest` in the host's own representation, emitted only
on `corollary/protocol`, only for a need the turn actually opened, and only
when the request advertises a tool whose **name and parameters-schema digest
are both the registered pair**. No reasoning item is introduced anywhere, on
any profile.

> **¶AMD-3 — the registered prompt path and its SSE lifecycle.**
> The adapter registers for exactly the `(name, parameters_sha256)` pair
> recorded in `experiments/protocol_uptake_host_capture.json` (U-P1), read
> from that artifact rather than restated in code. A request advertising the
> right name with any other schema digest matches nothing and takes the text
> WAITING fallback of §6.2 — never a guessed adapter.
>
> When it fires, the response carries **exactly one output item** and it
> replaces the message item:
>
> ```jsonc
> { "id": "fc_…", "type": "function_call", "status": "completed",
>   "name": "request_user_input",
>   "call_id": "<the pending request_id>",
>   "arguments": "{\"questions\":[{\"id\":…,\"header\":\"protocol\",…}]}" }
> ```
>
> The arguments follow the capture's own `mapping_to_need` field by field: one
> question, `id` = the need's slot, `header` = the fixed literal `protocol`,
> `question` = the verifier-minted prompt, and one `{label, description}`
> option per unresolved candidate move id in canonical order. Question wording
> is outside the scored claim (DESIGN §4); the typed need and its exact
> binding are what count. One caveat is recorded rather than silently
> resolved: the captured tool's description asks for a snake_case `id`, and
> the mapping makes `id` the slot — `protocol_uptake.candidate_move`, dotted.
> The committed mapping is followed literally rather than sanitized into
> something the capture does not say; whether the installed host accepts it is
> exactly what B7 measures.
>
> **Its streaming lifecycle** is the function-call one, not the text one:
>
> `response.created` → `response.output_item.added` (the item with empty
> `arguments` and `status: "in_progress"`) → `response.function_call_arguments.delta`
> (the whole arguments string, in one delta) → `response.function_call_arguments.done`
> → `response.output_item.done` (the completed item) → `response.completed`.
>
> There are **no content-part events**, because a function-call item has no
> content parts; wrapping one in a synthetic text part is precisely the
> synthetic item the paragraph above refuses. Deltas concatenate
> byte-for-byte to the completed item's `arguments`, the same discipline the
> text lifecycle keeps, and the completed response carries `x_corollary`
> including `need`.

## 9. Wiring steps, declared before the task book

Two engine capabilities exist but have no typed-line form. Each gets a
**named wiring step** — surface wiring of an existing capability, not a
new answerable capability; if a step has not landed when the task book
seals, its task kind is dropped from the book with the reason recorded.

**¶DEV-2 — W1 corrects the design's twin assumption (a recorded
correction).** DESIGN-grounded-throughput §3 lists `twin_lookup` as an
unconditional task kind and §5 lists twins among "what the engine
already answers"; only `closure_reachability` was marked conditional.
Verified against the tree: `route_line` never calls
`CoreSession.retrieve` (`scripts/harness.py:745` has no caller in the
routing chain), so twin material is line-unreachable over *any* skin —
the design's assumption was wrong, and this paragraph is the dated
record of that correction (2026-08-21), not a quiet generalization of
the conditional clause. Consequence, stated so the gates keep their
teeth: `twin_lookup` becomes droppable-with-reason exactly like
`closure_reachability`; T5's per-kind ≥80% floor applies to every kind
in the **sealed** book; T3's ≥50-answerable-tasks floor is unaffected by
drops — if drops push the book below 50, that is T3's stop, not a
relabeling.

- **W1 — `twin <statement-id>`** → `CoreSession.retrieve`
  (`scripts/harness.py:745`), surfacing the `twin_ledger` material the
  miss chain already returns (`source == "twin_ledger"`,
  `scripts/retrieval.py:487-517`; ledger
  `reports/signature_matches.json`). Gated on `corpus.nodes` (the twin
  ledger is already a required corpus ledger, `scripts/harness.py:254`).
  Answer lines (frozen at implementation review, then by the seal):
  the twin level, the group's member statement ids, and the ledger
  path — nothing more. Only groups that **list the queried id** count
  (the miss chain also surfaces alias/skeleton-matched groups that do
  not contain it; reporting those would put other statements' members
  in a receipt about this one); the strongest level is reported, and
  `exhausted` therefore means "no group lists this id".
- **W2 — `reachable <world-id> <target-path>`** → `closure_query.query`
  (`scripts/closure_query.py:263`), against the committed closures under
  `reports/closures/` and registrations under `data/closure_worlds/`.
  Targets are **committed canonical-bytes files** (generated by a seed
  script from the registered worlds' adapters, house source-generation
  rules), because `query` refuses approximate targets by design
  (`scripts/closure_query.py:269-276`). The route accepts **only**
  target paths listed in `data/closure_targets/manifest.json` with a
  matching `world_id`, refusing anything else by name — otherwise every
  file in the repository becomes a mintable certified bounded negative,
  which is the self-fulfilling-arm hole reopened from the other side;
  the manifest gate also gives every receipt's `target_digest`
  committed provenance for T7. The committed target set MUST
  include adapter-generated states **absent from the closure**, so the
  kind has a real NOT_REACHABLE arm and cannot become self-fulfilling —
  floors: **≥ 3 reachable and ≥ 2 not-reachable targets per world where
  the adapter affords them**: a world whose verifier
  admits no valid state outside its closure (the single-state
  `visual.rt0000` is that world) records the shortfall in the target
  manifest instead of manufacturing a state, and the NOT_REACHABLE arm
  is carried by the worlds that afford it. Requires a new boot probe
  `closure.worlds` (OK/OFF, never FAIL, joining the six probes at
  `scripts/harness.py:516-523`) — classified as a **committed-artifact
  probe with `optional=False`**, not a member of
  `OPTIONAL_SUBSYSTEMS`: that flag means an optional *dependency
  family* the offline boot forces OFF (P-IH1 asserts all of them OFF
  offline), and committed files are not that; the kernel profile's
  offline boot must still serve W2. The route is ordered
  with the other head-guarded commands; the path-shaped-line branch
  cannot capture a `reachable …` line anyway, since `_looks_like_path`
  rejects any line containing whitespace and `_existing_file` tests the
  whole line (`scripts/harness.py:829-841`). Statuses map from the
  receipt's `outcome`: `REACHABLE → found`,
  `NOT_REACHABLE_WITHIN_HORIZON → exhausted`, `CORRUPT_TARGET →
  refused`, and every `QueryRefused` subclass → `refused` with the
  exception's name in `detail`.

Both steps land in `route_line` itself, so the TTY inherits them — that
is A-IH6 working as intended for the kernel profile (the conversation
profile has no TTY loop to inherit anything; §1).

## 10. Errors, and what never happens

- Malformed JSON, missing `messages`, no user turn, `n != 1` → `400`,
  OpenAI error shape. (An empty-string user turn is served; §4.)
- Responses input with no user text, a non-text part, or a non-message item →
  `400`; unknown `previous_response_id` → `404`. ¶AMD-3's one exception: a
  `function_call_output` item on `corollary/protocol` (§4.2), which may also
  be the request's only new input.
- A tool-result item on any profile but `corollary/protocol`, or one with a
  missing or non-string `call_id`/`output` → `400` (¶AMD-3).
- Unknown `model` → `404`, naming all three profiles.
- Conversation-profile cross-slot `ValueError`
  (`scripts/conversation.py:291`, `:302`) → `409`, code
  `slot_conflict`, the engine's message as the error string (distinct
  from `transcript_divergence` so a client can tell them apart).
- Transcript divergence (§4, exact comparison defined there) → `409`.
- **Never:** a token in `content` that is not a rendering of accepted
  engine output — with §6's abstention acknowledgement as the single
  named exception; a slot filled with a value the user did not send; a
  sampled token; a route not in §5's table **or §3's protocol row**; a second
  engine; a durable session resumed over HTTP (¶DEV-1 — replay only, restore
  stays unshipped and unclaimed this cycle); and, ¶AMD-3: a protocol move
  selected by a rendered phrase, a `call_id` bound to any request but the
  pending one, or an authority opened by a protocol transition —
  `authority_delta` is present and empty on every served uptake receipt.

## 11. Adjudication hooks

`tests/test_serve_chat.py` (new, in-process against a loopback server —
driven through the stock `openai` client, since T1's whole point is an
unmodified client; no network beyond loopback) adjudicates: T1's triangle with an unmodified
OpenAI-compatible client (WAITING leg on `corollary/conversation`,
§6.2); T2's adversarial free-text probe; P-IH6's signed round-trip and
its wire-falsifiable negative (§6.2 a–c); the cold/cached
replay-equivalence of §4 (identical bodies modulo `id` and `created`);
the capability sheet's liveness (generated, not copied) and its
demo-name lint (P-IH3); and W1/W2's statuses if wired. The full-suite
release gate runs it like every other test.

**¶AMD-3's hooks** live in the same file, in `ProtocolProfile`: the greeting
uptake summary; the ambiguous turn's text WAITING with `x_corollary.need`;
the registered tool's single function-call item and its arguments mapping; the
wrong-digest fallback, run against the **real** registration read from U-P1's
capture; the `function_call_output` resume and the four ways it is refused
(unknown, stale, cross-request, repeated) with the session still WAITING; the
cancelled result that invents no value; the §8 function-call SSE lifecycle;
and §4.1's two hash properties — additive for message-only prefixes, and
divergent for two transcripts differing only in a tool-result payload. The
positive tool arms register a **stand-in schema digest** through the same
registry the capture fills, with its own provenance, because the captured
schema's bytes are deliberately outside this repository (the capture records
digests, not requests); the live digest is exercised by B7 and by
`scripts/run_b7_roundtrip.py`, not by the suite.
