# Protocol is uptake, not a keyword

**Status: design only, reviewed; not scheduled.** Nothing in this
document is implemented. The active v0.23 work and the incumbent candidates
already named for the v0.24 course are not displaced. This design was forced by
the first ordinary turn through the new Codex-compatible surface: `hello` was
treated as an ungrounded proposition, although in that position it may have
been a greeting, a liveness probe, quoted material, or expected output. The
observed turn is an unscored anecdote, not a result: served on the
`corollary/kernel` profile, `hello` reached the corpus-refusal path and the
reply suggested `suppose hello`. It is reproducible with the durable harness
command recorded in `README.md`; no transcript receipt is claimed.

The design-course receipt is
[`reports/design-direction-v0.24.json`](../reports/design-direction-v0.24.json).
The dialect-free brief is committed beside it. The course selected the second
series' lead, named **DUTY** at rounds two and three; its round-one form was
STANDING ORDERS, repaired after the grounding round admitted its typed-event
dispatcher as vacuous: a
protocol move must be grounded in interaction position **and** corpus evidence,
not in a word trigger and not in an internal event wearing conversational prose.

## 1. The boundary and the person it serves

Today the served kernel accepts a registered line grammar. The conversation can
hold assumptions, dispatch registered needs, accept an `ASK`, stop as `WAITING`,
present the verifier-minted question over TTY or HTTP, bind a reply, and resume.
The Responses skin is text-only: it accepts tool declarations but names them as
ignored, publishes no supported tools, rejects tool-result input items, and
emits only assistant-message output items. None of those facts recognizes what
an ordinary conversational turn is doing.

The boundary moves when the system can record this narrower claim:

> Given these exact session signals and these named corpus relations, the
> system took this utterance as this interaction move, entered this registered
> transition, or asked because two materially different transitions remained.

A person gains an ordinary conversational entrance to an auditable session.
`hello` is not a command. The same bytes may be a greeting at a fresh root, a
liveness response while a probe is outstanding, a quoted datum in a literal
slot, or expected program output inside a programming task. Context and corpus
witnesses license the uptake together. Where they do not determine one
transition, the existing `ASK -> WAITING -> reply` channel carries the
clarification.

This is the system's **uptake**, not a claim about private human intent. A person
may repair it. No external large language model is invoked, and Codex is a host
surface rather than an unreported reasoner.

## 2. Why this direction survived

The three pressure-tested finalists were:

1. **DEPUTY** -- maintainer-authored Python enters as bounded, reproducible
   evidence. It survived only as a transport claim: it does not show that the
   system composes programs, and shell is separate authority.
2. **DUTY / protocol uptake** (series 2's post-repair name for round one's
   STANDING ORDERS) -- interaction position plus corpus evidence
   licenses a move; different legal transitions cause an exact pause. This is
   selected because it addresses the observed live-conversation failure
   **on a new profile that can host it**: the same `hello` bytes, addressed to
   `corollary/protocol`, get a corpus-and-context entrance. The kernel
   profile's refusal of that turn remains the shipped honest answer; this
   slice does not reopen it. The direction still changes what a person can
   do, without opening execution or durable writes.
3. **SHADOW** -- a hand-authored abstract semantics returns weaker checked
   answers with an exact loss ledger. It is a real new answer type, but it does
   not address the interaction boundary exposed by the live surface.

The selection imports one bounded lesson from each declined finalist. DEPUTY
requires every later execution design to separate **transport** from
**composition**, and Python from shell. SHADOW requires a protocol receipt to
name lost or unresolved alternatives rather than hiding them behind one label.
Neither is merged into this slice; this is one protocol design, not a platform.

All fifteen round-one directions retain a disposition:

| series | direction | disposition |
|---|---|---|
| 1 | OSTENSION | converged on the active unnamed-library question; its separability census parks there |
| 1 | CONTRAST | computed consequential stakes fold into a later ambiguity experiment, not this protocol constructor |
| 1 | INSTRUMENT | expiring environmental premises park behind a future observation design |
| 1 | DEPUTY | runner-up; retained as the separate execution-transport prerequisite in section 11 |
| 1 | ABSENCE | folded into OSTENSION's closed-fragment instrument |
| 2 | SCOREBOARD | folded into the existing journal and the parked exact blast-radius question |
| 2 | STANDING ORDERS | repaired into the selected protocol-uptake contract; forward duties remain a later protocol family |
| 2 | UNSAY | exact withdrawal blast radius parks behind dependency closure and premise necessity |
| 2 | NO, BECAUSE | proven enabling actions park as refusal-table work, not language understanding |
| 2 | HANDSHAKE | folded into the unnamed-library incumbent; an authenticated binding is not a correct referent |
| 3 | MIRROR | independent convergence on shipped round-trip realization and the current ECHO design |
| 3 | TWO CLOCKS | converged on the parked independent-second-reading lane |
| 3 | SHADOW | declined finalist; parks as a new answer-type candidate |
| 3 | GRAFT | parks behind premise necessity; composition before necessity would multiply unsupported premises |
| 3 | HALF-LIFE | converged on COLD RECEIPT's 1-of-19 finding and the parked ORPHAN successor |

### 2.1 Relation to the incumbent queue

This document does not silently replace PREMISE LEDGER, STRANGER-GATE,
CANARY-CURVE, TOLL, or the naming-layer question. It enters the v0.24 course as
a reviewed but unadjudicated candidate, with one grounded reason to be compared:
the shipped product surface now exposes an ordinary-turn failure that did not
exist when those candidates were written. STRANGER-GATE's prohibition remains
binding before any untrusted execution or write stream. This slice opens
neither.

## 3. The first-class object: an uptake receipt

One append-only `ProtocolUptake` record is emitted for every turn admitted to
the protocol path:

```text
ProtocolUptake {
  schema
  uptake_id
  session_id
  turn_id
  utterance_sha256
  utterance_source
  context_before_sha256
  context_signals[] {
    signal_id
    value
    source_event_id
  }
  protocol_witnesses[] {
    protocol_node_id
    relation
    source_seed
  }
  candidates[] {
    protocol_id
    move_id
    required_signal_predicates[] {
      signal_id
      required_value          # including the named absence sentinel
    }
    next_state_sha256
  }
  disposition              # ENTER | CONTINUE | SUSPEND | RESUME | EXIT |
                           # ASK | REFUSED
  selected_move_id         # null on ASK or REFUSED
  unresolved_move_ids[]
  stack_before[]            # protocol episode ids, root first
  stack_after[]
  authority_delta[]         # exact authorities the selected transition opens;
                            # required empty on ASK and REFUSED; a plaintext
                            # receipt field, not only a digest ingredient
  need {                    # null unless disposition == ASK
    request_id
    slot
    prompt
    answer_schema
  }
  verifier_verdict
  verifier_evidence[]
}
```

`uptake_id` is the canonical digest of the whole record with the `uptake_id`
field itself empty; `schema` is inside the digest. The utterance
reaches the transition through exactly one channel: its canonical normalized
form (NFC, casefolded, whitespace-trimmed) is the exact lookup key into the
sealed protocol corpus, and the returned `protocol_witnesses` -- never the
surface bytes -- enter the admission predicate together with `context_signals`.
A surface byte reaching the predicate outside that witness channel is the
lexical trigger this design abolishes. Under exact lookup the witness set is a
function of the surface, so a "witness-only" view of any fixture set is the
same marginal as a "surface-only" view; the fixture design in section 6 and
control B4 record that identity instead of pretending a third independent
factor. A lookup miss returns no witnesses and licenses no protocol move.
`protocol_witnesses` name nodes in the generated protocol corpus whose source
is `scripts/build_protocol_corpus.py`. Its output is
`protocol/protocols.json`, deliberately **outside** `data/`: putting it under
`data/*/nodes.json` would silently add it to the boot corpus count, merged
resolver graph, and every census over that graph. A dedicated regeneration
checker, `scripts/check_protocol_regeneration.py`, committed at U-P0, owns
this separate artifact. `context_signals` are a candidate set of **six** exact session facts, one
signal id each: `pending_need` (one structured value carrying the pending
need's identity and type, or the absence sentinel), `quote_boundary`,
`expected_output_slot`, `active_task`, `prior_move`, and `protocol_stack`.
U-PRE may delete any of these; U-P0 records the survivors. Absence is a
value, not a missing key: greeting's uniqueness on the 32 is a required
absence of probe/quote/output signals, not the mere presence of a
`fresh_root` id.

The stack is new interaction-control state, owned by the protocol runtime
module U-P0 names -- it lives beside session state, never inside any epistemic
frame -- and capped at **eight episodes** per session. Eight is four times
the deepest of the **eight nested/interruption fixtures** (those fixtures
reach depth two). It is a declared resource bound, not a measured number. A
ninth push is `REFUSED` before mutation. The depth-nine refusal plant is that
ninth push: it is a trajectory the plant itself has already filled to the
cap, not one of the eight nested fixtures, and it does not raise the cap.
The stack is **not** smuggled into `FrameExecutor.open_nested`: that method
currently owns nested belief models and explicitly does not design generic
nested fiction, much less conversational protocols. Stack snapshots make
enter, suspension, resumption, and exit replayable without claiming they
are epistemic frames.

The candidate proposer in this slice is closed-form; a learned ranker is a
later, separately gated proposal (section 6, step 5). Any proposer may only
rank corpus-witnessed moves whose required signal **value** predicates
all hold, including required absences. The protocol verifier alone admits
a transition. A rendered phrase never enters the admission predicate.

## 4. ASK and the host prompt are separate facts

`ASK` already exists. `ClarificationRequest` already carries a verifier-minted
`request_id`, `slot`, `prompt`, resolution channel, signature, and key id. The
generic harness currently exposes only `slot` and `prompt`; the Responses skin
returns those as `x_corollary.need` text and never emits a tool call.

The protocol path is served on a **new third profile, `corollary/protocol`**,
registered by AMD-3. Neither existing surface can host it honestly: the kernel
profile's registered line grammar and abstention are shipped, sheet-published
claims, and the conversation profile is the closed two-slot request grammar
whose spec section declares any widening an engine change. The protocol
profile mounts the protocol runtime and the existing in-process need machinery
over a fresh session type. Kernel line-grammar tests, conversation
request-grammar tests, and those two profiles' capability-sheet blocks
stay byte-unchanged. Shared listing tests (`GET /v1/models`, the
unknown-model 404 string, `corollary.capabilities` version) are AMD-3
edits, not frozen pins: today `ChatEngine._fresh` maps every non-kernel
model to `golden_chicken_revision_session`, so an allowlist-only edit
would serve the new profile as the two-slot demo. The triggering turn
arrived on the kernel profile and its honest answer there remains
refusal by design; the repaired entrance is the same turn addressed to
`corollary/protocol`, which the fresh-root greeting fixtures encode
directly.
B7's round trip runs against `corollary/protocol`, with the README durable
command's `-m` switched accordingly. The durable command itself is not edited
until that gate is built.

This design adds no user command named `ask`. When surviving candidates have
different `next_state_sha256` values, the verifier opens one signed request and
stops `WAITING`. When candidates differ in name but produce the same next state,
the verifier records the equivalence and takes the canonical lowest identifier;
asking would collect information the transition does not use.
(`next_state_sha256` digests the four-field projection sealed at U-P0; a move's
*name* is deliberately outside that projection, so two differently named
candidates can genuinely share a digest and this rule is reachable.)

The host adapter may represent that already-approved need in two ways:

- **Structured prompt tool.** Only if the incoming Responses request advertises
  a tool whose exact name and JSON-schema digest are registered at boot, emit
  one function-call item. `call_id` binds to the pending `request_id`; the tool
  result resumes only that request. An unknown, stale, cross-slot, or repeated
  result is refused.
- **Text WAITING fallback.** If no compatible tool is advertised, preserve the
  current complete assistant turn and `x_corollary.need`. Cancellation or an
  unavailable UI remains `WAITING`; no value is invented.

The actual tool name is not frozen from memory or documentation. Construction
prerequisite U-P1 captures what the installed Codex CLI sends. If it advertises
no compatible interactive prompt tool, the Codex-prompt result is **UNTESTED**.
The protocol core may still be measured, but the release may not claim Codex
prompt-tool support.

Question wording is outside the scored claim. It may be the verifier's existing
prompt, a structured UI over `answer_schema`, or a later corpus-grounded
realization. A hardcoded `Do you mean ...?` string and a fluent generated string
both score zero; only the typed need and its exact binding count.

## 5. Trusted and untrusted

**Trusted, exact code:** seed regeneration; session-state extraction; corpus
witness lookup; transition legality; candidate-state digesting; stack
push/suspend/resume/pop; signed request minting and binding; request/tool-call
identity; capability registration; resource and hop budgets; canonical receipts;
and every result-gate computation.

**Untrusted or graded:** the person's utterance; any learned candidate ordering;
question wording; the host UI; and a tool result until it binds through the
pending request. Corpus transition rules are trusted **as authored rules**, but
exact checking establishes conformance to those rules, not that the rules model
human convention correctly.

No LLM is a hidden component. No protocol move may authorize `WRITE`, process
creation, filesystem access, shell access, or network access. Those authorities
need separate contracts.

## 6. Preregistration and construction order

Before protocol runtime code is written:

1. **U-PRE -- schema audit, not a run.** Freeze the candidate schema and
   commit, for each semantic **input** field, a one-line necessity argument
   naming the transition rule whose outcome that field's value changes;
   delete every field with no such argument. Fixtures do not exist yet, so
   a necessity argument may not cite a fixture family. A field that would
   be constant on every later fixture has no transition rule and is
   deleted here. No runtime exists yet, so nothing is executed: the
   audit is a committed table, it licenses no result, and B9's mutants
   are later drawn from exactly the input fields that survive it. This
   document does not freeze a mutant count. Next-state projection fields
   are outputs; they are not in this audit and they are not B9 mutants.
   Their necessity is the section 4 equivalence rule (B6) and the
   empty-`authority_delta` predicate (B3).
2. **U-P0 -- source and fixture seal.** Commit
   `experiments/protocol_uptake_prereg.json`, the initial
   `scripts/build_protocol_corpus.py`, its generated corpus,
   `scripts/check_protocol_regeneration.py`, and
   `experiments/protocol_uptake_fixtures.json`. The manifest records all source
   paths and canonical digests, the context-product generator, expected uptake,
   control labels, the `context_signal` ids and `protocol_witness` fields
   that survived U-PRE, the four named context-position ids of
   section 6's product, the predicate language (exact value equality,
   including a named absence sentinel), the name of the protocol runtime
   module that owns the stack, the exact four-field next-state projection
   (`protocol_id`, `stack_after`, `pending_request_id`, `authority_delta`),
   the two computed view-ceilings `c_surface` and `c_position`, the
   position-switch control's frozen table-agreement, and each B9
   mutant's target fixture. `move_id` is
   deliberately outside the projection: a projection that digests the
   move's name could never certify two names as one transition, and the
   section 4 equivalence rule would be dead code. The fixtures are
   construction fixtures authored by this repository; they license no
   population claim about human conventions.
3. **U-P1 -- host-tool capture and spec amendment.** Record the tool names and
   schema digests from one unmodified `codex.cmd` request, with values/secrets
   absent. Register a prompt adapter only for an exact captured schema. No
   suitable tool means `host_prompt_status: untested`, not a guessed adapter.
   Before an adapter is implemented, commit `SPEC-chat-completions-skin.md`
   amendment AMD-3 and its tests. AMD-3 **registers the new
   `corollary/protocol` profile**. It does not amend the kernel profile's
   section 5 line-grammar claim, the conversation profile's section 3
   request-grammar claim, or either profile's generated sheet block.
   AMD-3 must:
   - rewrite SPEC §1 ("two session objects", "the skin adds **no third
     path**"), §2 (`GET /v1/models` "lists the two profiles"), and §8
     ("no synthetic tool or reasoning item is introduced") so those
     sentences remain true of a three-profile server;
   - add `corollary/protocol` to the profile table, with the protocol
     runtime as its request surface and a fresh session type (not
     `golden_chicken_revision_session`, not kernel line routing);
   - replace `ChatEngine._fresh`'s non-kernel else-branch (today every
     non-kernel model constructs `golden_chicken_revision_session`) with
     an explicit three-way dispatch; the unknown-model 404 string and
     the `/v1/models` listing tests that currently pin exactly
     `[corollary/kernel, corollary/conversation]` are AMD-3 edits;
   - bump or explicitly not-bump `corollary.capabilities/2` in writing;
   - replace "never emits a tool call" only on this profile's registered
     prompt path, remove handled tool fields from this profile's
     `x_corollary.ignored`, admit the exact function-call-output input
     item, and define its streaming events;
   - amend the spec's section 4.2 refusal of non-message input items for
     exactly that item type on this profile, and extend the section 4/4.1
     canonical prefix hash with a typed serialization of every admitted
     tool-result item, with a test that two transcripts differing only in
     a tool-result payload hash differently and trigger
     `transcript_divergence`. The extension is additive: a prefix of
     only `[role, content]` pairs hashes as it does today, so existing
     kernel and conversation replay tests stay green;
   - add a generated capability-sheet block for the protocol profile so
     the served sheet stays true of the server that serves it; kernel
     `line_grammar` and conversation `request_grammar` rows, and the
     kernel honesty string "unregistered paths abstain", stay
     byte-unchanged;
   - reconcile this profile's published tool-capability key set --
     `experimental_supported_tools`, `supports_parallel_tool_calls`
     (catalog test), and the Responses-body `parallel_tool_calls` /
     `tool_choice` / `tools` keys (streaming/ignored-fields tests, not
     the catalog test) -- with the captured capability. A pre-existing
     contradiction on the shipped profiles (`scripts/serve_chat.py`
     already emits `parallel_tool_calls: True` while the catalog
     publishes `supports_parallel_tool_calls: False`) is out of this
     slice's scope; AMD-3 must not copy it onto the protocol profile.
4. Commit the receipt-replay checker (the B10 instrument, distinct from the
   protocol-corpus regeneration checker of U-P0) and the deliberately broken
   controls before the runtime implementation. The result writer refuses an
   existing output path and a dirty or wrong-tip scoring tree.
5. Implement the deterministic oracle path first. A learned ranker, if later
   proposed, receives the same legal candidate set and its own frozen baseline;
   it is not part of this slice.

The fixture product contains **eight short surfaces**: two construction forms
for each of four bounded move families (`greeting`, `probe_reply`,
`quoted_datum`, `expected_output`). The four context positions are named
here, not deferred to U-P0:

- `fresh_root` -- no pending need, no quote boundary, no expected-output
  slot, empty protocol stack;
- `probe_outstanding` -- a live probe need;
- `literal_slot` -- quote boundary set;
- `programming_task` -- expected-output slot and active task set.

Each surface is placed in all four positions, producing **32 context-swap
fixtures**. There is no separate witness factor: under exact lookup the
witness set is a function of the surface (section 3), so a "witness
bundle" cannot be set independently of the surface without unsealing the
corpus.

The expected label at each cell is not a balancing rule and not a free
choice. It is the unique move family `F` such that the sealed corpus
witnesses the normalized surface under `F` **and** the position satisfies
`F`'s required signal **value** predicates, including required absences.
Zero matches is `REFUSED`. Required value-predicates are pairwise
exclusive on the 32 by construction, so a cell cannot have two matching
families. That is the **honest table**: a greeting-class surface at
`fresh_root` is a greeting because greeting requires the probe/quote/output
signals to be absent; the same surface at `probe_outstanding` is
`REFUSED` unless the corpus also witnesses it as `probe_reply` *and*
the probe predicate holds. It is never labelled `probe_reply` merely
to balance a column. Adding a live need to a fresh-root cell is a
move-switch or a refusal, not an ASK: it kills greeting's absence
predicate and, if the surface is dual-witnessed, leaves one selected
probe. That corruption is therefore not an ASK plant.

ASK fixtures are extra sealed rows, not cells of the 32. Each such
row has two corpus-witnessed moves whose required predicates both
hold and whose `next_state_sha256` values differ -- two greeting
protocols at `fresh_root` with different `protocol_id` (inside the
four-field projection) is enough. Those protocols' lookup keys are
**extra surfaces**, disjoint from the eight product surfaces: each of
the eight matches at most one node per family, so a 32 cell cannot
become the two-`next_state` ASK that family-level uniqueness would
miss. That is material ambiguity the 32 is forbidden to produce.

U-P0 seals the 8x4 table **generated by that rule** from the committed
surfaces and witness sets, then **computes** two view-ceilings from it:
`c_surface` is the number of cells the best function of surface alone
matches, and `c_position` the number the best function of position alone
matches. Both numbers are frozen in the prereg. If either equals 32/32,
that view is a sufficient statistic and the joint-uptake claim is
vacuous: **BLOCKED CONSTRUCTION**, no runtime. If either is 24/32 or greater,
the table is at least as separable as the exclusive-home shape (two
family-surfaces per column, six `REFUSED`, majority 24/32) and the
slice has not constructed a joint claim: **BLOCKED CONSTRUCTION**.
Those two refusals are the meetable degeneracy bounds. They are
construction checks on the table, not B4's runtime tripwire.

Eight is construction scope, not statistical power. The sealed table
must contain at least two surfaces that take two different selected
(not `ASK`/`REFUSED`) moves across positions -- that is the "same
utterance, different moves" claim as a construction check, not a
balancing requirement. Two exact corruptions per context position --
remove the protocol witness, remove the parent context event --
produce **8 refusal fixtures**. **Four ASK fixtures** are sealed
separately as above. Four stack transitions at depths one and two
produce **8 nested/interruption fixtures**, plus one depth-nine
refusal plant as scoped above. Two **equivalence fixtures** seal a
pair of differently named candidate moves whose four-field
projections coincide, so gate B6's proceed-without-asking leg has
fixtures that can fail. B6's WAITING leg is those four ASK fixtures:
at least two of them must be `WAITING`, or R-U1 may not claim that
material ambiguity pauses.

## 7. Construction gates

- **B1 -- source truth.** The dedicated protocol-corpus regeneration check
  (`scripts/check_protocol_regeneration.py`) passes byte-identically; schema
  validation and link checks pass; every witness resolves
  to a generated protocol node and its builder source. `data/*/nodes.json`, the
  merged resolver graph, and the boot corpus count remain byte-identical. One
  orphan or direct generated-file edit stops the slice. Recomputing
  `c_surface` and `c_position` from the sealed table must reproduce the
  frozen prereg numbers; a mismatch is a construction bug, not a leak.
- **B2 -- context and corpus change uptake.** All **32/32** context-swap
  fixtures produce their sealed-table move and transition. The same
  surface bytes reach different selected moves solely through declared
  context signals and corpus witnesses where the table says they do,
  and every selected move must cite at least one protocol witness in
  its receipt. The construction check that at least two surfaces take
  two different selected moves is part of this gate.
- **B3 -- ambiguity never guesses.** All **8/8** refusal fixtures end in
  `REFUSED`, and all **4/4** ASK fixtures end in `ASK`, as preregistered.
  No selected move, no protocol-stack mutation, and no authority delta
  may occur on those paths. The receipt field `authority_delta` is
  present and empty on those paths; emptiness is not inferred from a
  digest. The ASK branch's only writes are its own artifacts -- the
  signed request, the `WAITING` state, and the uptake receipt.
- **B4 -- lexical control loses.** Two capability-blind controls run over
  the sealed 32: a surface-only guesser (equivalently witness-only, by the
  section 3 identity) and a position-only guesser. `c_surface` and
  `c_position` remain the best restricted-view fits to the **sealed
  table**, frozen at U-P0 and recomputed by B1. B4 then **re-fits** each
  restricted-view classifier on the runtime's selected moves and scores
  that in-sample agreement. A table-faithful runtime matches the frozen
  ceilings with equality; equality is not a firing. Agreement **above**
  a frozen ceiling means the runtime's labels are a function of that
  view more than the table is -- a lexical trigger (surface-constant
  runtime scores 32/32) or a position switch -- and voids the fixture
  set. The table-fitted "predict `REFUSED`" majority is not the B4
  classifier; using it against the runtime cannot detect a lexical
  trigger, because that trigger disagrees with majority-`REFUSED` on
  every selected cell.
- **B5 -- exact nesting.** All **8/8** trajectories reproduce `stack_after` and
  resume the exact parent episode. Three arrival-order replays per trajectory
  produce byte-identical uptake order. A reply for the suspended child may not
  bind in its parent. The depth-nine plant is `REFUSED` without changing the
  stack.
- **B6 -- ask only for material ambiguity.** Every fixture with more than one
  distinct candidate `next_state_sha256` stops `WAITING`; every fixture whose
  candidates share one digest proceeds without asking. The four ASK
  fixtures must stop `WAITING`. Fewer than two sealed ASK fixtures at
  U-P0 is `BLOCKED CONSTRUCTION`; R-U1 may not claim a pause from an
  empty WAITING arm. The two sealed equivalence
  fixtures must proceed, select the canonical lowest move identifier,
  and record that the candidates grouped to one digest. The candidate
  set is committed in the receipt as `candidates[]`. The equivalence
  partition is the grouping of those candidates by
  `next_state_sha256`; it is derived at check time and is not a schema
  field (B9 forbids adding fields after U-P0).
- **B7 -- tool-wire round trip.** If U-P1 registered a compatible prompt tool,
  an unmodified Codex CLI must complete: function-call item -> host result ->
  function-call-output input -> exact request resume. The round trip is
  served on `corollary/protocol` (the `-m` of the README durable command,
  switched for this gate). Running it against `corollary/kernel` or
  `corollary/conversation` is not B7. Unknown, stale, cross-request,
  canceled, and repeated outputs remain unbound. If U-P1 found no tool,
  B7 is `UNTESTED`; it may not be reported green from the text fallback.
  The AMD-3 spec/catalog/ignored-field tests are part of this gate, not
  follow-up documentation.
- **B8 -- phrases carry no authority.** A planted prompt string naming
  `WRITE`, Python, and shell capabilities must open none of them. Zero process
  starts, zero stage records, and zero data-tree byte changes are required.
- **B9 -- corruption fires.** U-P0 seals one mutant per semantic input
  field that survived U-PRE. The candidate set is six context-signal ids
  and three protocol-witness fields; this document does not freeze the
  survivor count. Each mutant names the fixture it is applied to. A
  field that is constant on the 32 is mutated on a nested or ASK fixture
  that reads it, or it is deleted at U-PRE -- it is not a mutant that
  cannot fire. Every sealed mutant must change the selected move, move
  the receipt to `ASK`/`REFUSED`, or fail validation. Next-state
  projection fields are outputs and are not in this set. No schema field
  may be removed after U-P0; inert-field pruning belongs only to the
  U-PRE audit.
- **B10 -- replay.** The checker regenerates every receipt from the sealed input
  and obtains byte-identical records. Missing and extra uptake records fail set
  equality; the checker may not validate only records the runtime chose to emit.

## 8. Blind controls and voiding sentences

The primary capability-blind control is B4's surface-only classifier,
re-fit on the runtime.

> **If the best surface-only classifier of the runtime's selected moves,
> or the best position-only classifier of those moves, agrees with the
> runtime on more than `c_surface` or `c_position` cells of the sealed
> 32, the runtime leaked labels into that view and the protocol uptake
> claim is void.**

A second position-switch control selects `greeting` at `fresh_root` and
`REFUSED` elsewhere. U-P0 freezes this control's exact agreement with the
sealed table. The claim is void if the runtime's agreement with this
control **exceeds** that frozen table-agreement -- that is, if the
runtime *is* the position switch. Reporting the score without a threshold
is not a control.

The host control renders every need as ordinary assistant text. A perfect
conversation transcript under that control does **not** establish tool support;
it demonstrates only that the already-shipped text WAITING path still works.

## 9. Result gates and licensed sentences

- **R-U1 -- bounded protocol uptake.** Only if B1-B6 and B8-B10 pass: *"On the
  sealed protocol corpus and honest context product, the same short
  utterance takes different verified interaction moves from context and corpus
  evidence, and material ambiguity pauses instead of guessing."*
- **R-U2 -- Codex prompt tool.** Only if B7 runs and passes: *"The installed
  Codex host presented a verifier-approved need as a structured prompt tool,
  returned its result, and resumed the exact pending request."* Text WAITING
  cannot license this sentence.
- **R-U3 -- negative.** A failed B2/B3 or a fired blind control licenses the
  bounded negative with its confusion table. It does not license changing the
  surfaces, context product, or control after the score.

No gate licenses English understanding, recovery of private human intent,
general social competence, protocol behavior outside the sealed families,
learned policy quality, or any Python/shell capability.

## 10. Stop conditions, corruption boundary, and suspended habit

Stop before implementation if the protocol seed can express the four families
only by storing whole response templates; that would replace a hardcoded command
with a hardcoded sentence bank. Stop after construction on any direct generated
file edit, missing provenance, unverifiable tool schema, or checker that cannot
detect an omitted receipt. Stop the result claim if either blind control fires.

A construction refusal is not an unfavorable result: failure to build the
source/fixture seal or exact host adapter is `BLOCKED CONSTRUCTION`; a completed
registered run that misses B2/B3 is a bounded negative. A human trying the chat
is a demonstration, not scored evidence. Generated nodes are artifacts; their
seed is source truth. Exact conformance to a transition table does not establish
that the table correctly describes human convention.

For this slice only, and on the `corollary/protocol` profile only, the
protocol path is the request surface. Keep every existing kernel command
and every conversation-profile request as a regression path;
`corollary/kernel` and `corollary/conversation` request surfaces are
untouched. Shared listing and `_fresh` fallthrough are AMD-3, not
"untouched." Also suspend text-only Responses output only for an exact
U-P1 prompt adapter on `corollary/protocol`. No general tool support
follows.

## 11. The execution lesson, parked rather than smuggled in

DEPUTY is not part of the selected slice, but its refusals become prerequisites
for any later execution design:

- add an execution action separate from `WRITE`; the PROVEN write gate never
  executes candidate Python;
- prove transport first with maintainer-authored, input-pinned Python receipts;
  that result cannot be cited as program composition;
- keep output session-scoped evidence, never automatic corpus truth or proof;
- make shell a later authority with a separate capability and side-effect
  contract -- Python authority never implies shell authority;
- include exact interpreter, arguments, stdin, cwd, budgets, stdout, stderr,
  exit status, and source digests in the receipt;
- deny execution before process creation when the capability is absent; and
- require semantic correspondence to the requested task separately from mere
  byte reproducibility, since the most dangerous green receipt is a reproducible
  run of the wrong program.

The next askable question after R-U1 is therefore narrow: **can one registered
programming protocol open a maintainer-authored Python transport need, receive
its receipt, and resume its exact parent without granting write or shell
authority?** That question owes its own design and preregistration.

## 12. Where status lands

- **ROADMAP:** linked now as design-only v0.24 input. The v0.24 course
  must adjudicate it against the incumbent queue; this document does not schedule
  itself.
- **ANALYSIS:** records the three-series funnel and the lack of an empirical
  result. If implemented, raw uptake receipts land before compact metrics.
- **DISCOVERIES:** receives only measured surprises from the registered run,
  including a fired lexical control or a host with no usable prompt tool.
- **BACKLOG:** carries DEPUTY, SHADOW, and the other declined directions with
  triggers. Shipped parts are pruned only during release rotation.
- **HTTP SPEC and catalog:** before B7 implementation, AMD-3 adds the
  `corollary/protocol` profile and rewrites SPEC §1, §2, and §8 so
  "two session objects", "no third path", "lists the two profiles",
  and "no synthetic tool" remain true of the three-profile server.
  Shared listing tests, the unknown-model 404, `ChatEngine._fresh`'s
  else-branch, and `corollary.capabilities/2` are AMD-3 edits. The
  profile's one registered prompt path gets the full U-P1 tool-call
  scope. It does not amend kernel section 5, conversation section 3,
  or either existing sheet block. `/v1/models` names exactly the
  captured supported tool on this profile.
- **Release process:** `scripts/check_protocol_regeneration.py` joins the
  release skill's step-1 regeneration list in the release that commits it.
