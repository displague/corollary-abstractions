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

## 1. What the engine actually is (two session objects, one engine)

The repository ships one session engine with **two session objects**, and
this spec serves both rather than pretending they are one:

- **`CoreSession`** (`scripts/harness.py:435`) — boots the capability
  matrix and routes the **registered line grammar** through
  `route_line(repo_root, session, line) -> dict`
  (`scripts/harness.py:1390`). No save/restore.
- **`ConversationSession`** (`scripts/conversation.py:126`) — the
  key-signed, owner-private slot-filling session:
  `say(utterance) -> Turn` (`scripts/conversation.py:253`) over the
  bounded request grammar (`scripts/request_grammar.py`).

Both drive the same `Controller`/verifier machinery
(`scripts/controller.py`); the skin adds **no third path**. A chat
conversation selects which object serves it via the request's `model`
field (§3). The TTY is today the interactive skin over `CoreSession`
(`harness.main()`, `scripts/harness.py:1461`); `ConversationSession` has
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
| `GET /v1/models` | lists the two profiles as models (stock clients probe it) |
| `GET /v1/capabilities` | the **capability sheet** (§7), vendor extension |

Anything else: `404` with a JSON error object in the OpenAI error shape.

## 3. Profiles (the `model` field)

| `model` | session object | grammar | one-line description |
|---|---|---|---|
| `corollary/kernel` | `CoreSession.boot(repo_root, offline=True, session_id=…)` | registered line grammar (§5) | corpus answers, exact evaluation, ownership, belief, story, refusals |
| `corollary/conversation` | the slot-filling session (`scripts/conversation.py:439`, `keyring=` an ephemeral per-conversation ring) | `request_grammar.parse_request` | signed slot-filling with minted clarification questions |

Unknown `model` → `404` (error shape, code `model_not_found`).

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
  input lines. Turn *n*'s response is computed by replaying user turns
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
- `stream: true` is supported (§8). `n != 1` → `400`. A request with no
  `messages` array or no user turn → `400`. An empty-string user turn is
  **served**, not rejected: it is the engine's registered empty line
  (§5 row 0, pinned by `tests/test_harness_line.py:360-366`).

### 4.1 Canonical prefix hash

`sha256` over the UTF-8 bytes of
`json.dumps([[role, content] for each message in the prefix],
ensure_ascii=False, sort_keys=True, separators=(",", ":"))`. The prefix
for turn *n* is every message strictly before the final user turn. The
same serialization discipline (call it **canonical-JSON/compact**) is
used everywhere this spec says "canonical": `json.dumps(value,
ensure_ascii=False, sort_keys=True, separators=(",", ":"))`, encoded
UTF-8.

## 5. The registered line grammar is the request surface (kernel profile)

The kernel profile routes exactly `route_line`'s chain
(`scripts/harness.py:1393-1437`) — first match wins, statuses verbatim:

| # | line form | route | statuses |
|---|---|---|---|
| 0 | empty | `none` | `waiting` |
| 1 | `narrow <corpus\|discipline\|word\|id> <value>` / `cancel` (only while candidates pend) | `resolver_context` | `found`, `waiting`, `canceled`, `cycle`, `hop_ceiling` |
| 2 | `owns <template-expr>` | `ownership` | `solved`, `exhausted`, `refused` |
| 3 | `suppose <claim>` | `evaluate` or `supposition` | `solved`, `held`, `waiting`, `refused` |
| 4 | `twin <statement-id>` — **wiring step W1, §9** | `twin` | `found`, `exhausted`, `refused` |
| 5 | `reachable <world-id> <target-path>` — **wiring step W2, §9** | `closure` | `found`, `exhausted`, `refused` |
| 6 | story request (`story.is_story_request`) | `story` | `found`, `waiting`, `exhausted` |
| 7 | belief narration + `where does A think B is` | `belief` | `found`, `waiting`, `exhausted` |
| 8 | computable relation/expression | `evaluate` | `solved` |
| 9 | repo-relative path | `write_gate` | `PROVEN`, `VERIFIED`, `REFUSED` (uppercase `Verdict` pass-through) |
| 10 | free text the graph claims | `resolver` | `found`, `waiting` |
| 11 | `what is X` / `define X` (dictionary word) | `gloss` | `found` — **unreachable on this profile**: the offline boot forces `retrieve.wordnet` OFF and `_route_gloss` then declines (`scripts/harness.py:850-867`); the sheet lists the row as off rather than hiding it |
| 12 | everything else | `dispatcher` | `exhausted` |

The **status alphabet is frozen as a closed set**, inconsistencies
included: lowercase `waiting, solved, refused, exhausted, found, held,
canceled, cycle, hop_ceiling` plus the write-gate's uppercase
pass-through, whose reachable values are `PROVEN`, `VERIFIED`, `REFUSED`
(`scripts/harness.py:841-847`; pinned by
`tests/test_harness_line.py:274,301`), plus `abstained` — the one
skin-assigned status, conversation profile only, declared in §6 for the
branch that runs no turn. The skin transports the engine's
vocabulary; it does not edit it. Normalization would be the renderer
rewriting the record, which A-IH6 forbids.

## 6. Response mapping: what `content` is, and what rides beside it

**`content` is the verbatim pass-through of the engine's rendered
answer, and nothing else.** It is the useful-token surface the
throughput metric counts, so the rule leaves the skin zero rendering
freedom:

- Kernel profile: `content` = `"\n".join((*reading, *answer))` when the
  verdict dict carries a `reading` (the `resolver_context` found case,
  `scripts/harness.py:1219-1228` — the TTY renders both, so the skin
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

Two scoring notes restated from the design so no implementer rediscovers
them: refusal and clarification turns contribute **zero** useful tokens
whatever their `content` length (so the dispatcher's echo of the user's
line, `scripts/harness.py:924-929`, inflates nothing), and the
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
sentence stands unqualified: a change voids the run.

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
(`scripts/harness.py:961-971`, `:1276-1282`, `:1309-1315`) and an empty
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
| `write_gate` (`PROVEN`/`VERIFIED`) | `grounding: "working-tree"` — the gate's own `evidence` lines already ride in `x_corollary.evidence` (`scripts/harness.py:846`) and are the record |
| `conversation` (`solved`) | `binding: {slot, value, lifetime}`, `derivation: "user-frame"` |

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
  does (`scripts/harness.py:1406`). No `need` field is emitted; there is
  nothing to put in it. The `cycle` and `hop_ceiling` terminators cross
  the wire as ordinary statuses — the server does not exit the way
  `harness.main()` does, but pending state clears exactly as
  `_route_pending_context` already clears it (`scripts/harness.py:1179,
  1200, 1232`).
- **Conversation profile:** a turn that asks carries
  `x_corollary.need` = `{slot, prompt}` — the exact two fields the
  `Need` protocol exposes (`scripts/harness.py:329-344`) — with
  `content` = the question. **The next user message is the reply**, and
  it binds through `verifier.reply_action` — the signed channel
  (`scripts/conversation.py:305` → `:248` → `scripts/retrieval.py:1615`)
  — mirroring
  `tests/test_ask.py::test_signed_reply_resumes_same_session_and_binds_user_frame`
  across the transport.

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
  "honesty": "offline boot; unregistered paths abstain (P-IH4); no generative path"
}
```

The sheet is generated from the live objects (the boot matrix's records,
`request_grammar.SLOT_PHRASES`/`SLOT_VALUES`/`coverage()`, the routing
table) — never a hand-maintained copy that can rot. Rows the profile
cannot serve (gloss under offline boot) appear with `"served": false`
rather than disappearing. No demo name appears anywhere in the sheet
(P-IH3).

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
`CoreSession.retrieve` (`scripts/harness.py:732` has no caller in the
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
  (`scripts/harness.py:732`), surfacing the `twin_ledger` material the
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
  whole line (`scripts/harness.py:816-828`). Statuses map from the
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
- Unknown `model` → `404`.
- Conversation-profile cross-slot `ValueError`
  (`scripts/conversation.py:291`, `:302`) → `409`, code
  `slot_conflict`, the engine's message as the error string (distinct
  from `transcript_divergence` so a client can tell them apart).
- Transcript divergence (§4, exact comparison defined there) → `409`.
- **Never:** a token in `content` that is not a rendering of accepted
  engine output — with §6's abstention acknowledgement as the single
  named exception; a slot filled with a value the user did not send; a
  sampled token; a route not in §5's table; a second engine; a durable
  session resumed over HTTP (¶DEV-1 — replay only, restore stays
  unshipped and unclaimed this cycle).

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
