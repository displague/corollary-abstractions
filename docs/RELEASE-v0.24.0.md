# v0.24.0 — the ordinary turn became an uptake, and the tool bridge failed honestly

This cycle scheduled the smallest live failure the project had: `hello`,
typed at the shipped Codex-compatible surface, came back as an ungrounded
proposition. It ships as a **capability** — a third served profile on which
the same short utterance takes different *verified* interaction moves — and
as a **first-class negative** — the one bridge to an unmodified outside
program is RED, three steps of four, with both mechanisms named.

- **The ordinary turn is now an uptake.** On `corollary/protocol`, `hello`
  at a fresh root is a greeting `ENTER`; under a live probe the same four
  bytes are a `probe_reply`. Not by surface matching — by a sealed corpus
  witness and a context-position predicate, where a lookup miss licenses
  nothing. All **nine** scored gates green over **87** receipts; the
  voiding sentence did not fire; **R-U1** is licensed
  (`experiments/protocol_uptake_run.json`).
- **The tool bridge is red, and that is a result.** An unmodified
  codex-cli 0.150.1 received the one emitted `request_user_input`
  function-call item and bound a `function_call_output` to the **exact**
  pending request id — and the output it bound was its own router's
  refusal, *"request_user_input is unavailable in Default mode."* The same
  run showed a second, independent killer. **R-U2 is not licensed. This
  release claims no Codex prompt-tool support**
  (`experiments/protocol_uptake_b7.json`).
- **Nothing was widened after the red.** ¶AMD-3's §4.2 scope stayed exactly
  one item type on exactly one profile; the two successor probes are filed
  in [BACKLOG](BACKLOG.md), not folded into this cycle's claim.

**Links** — previous release: [v0.23.0](RELEASE-v0.23.0.md) · closed plan:
[ROADMAP-v0.24](ROADMAP-v0.24.md) · next plan:
[ROADMAP-v0.25](ROADMAP-v0.25.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the question it bound and would not ask](blog/the-question-it-bound-and-would-not-ask.md)
· this cycle's design: [DESIGN-protocol-uptake](DESIGN-protocol-uptake.md)
· forward design: [DESIGN-house-rules](DESIGN-house-rules.md)

## The headline finding: the same four bytes, two verified moves, and a pause where it cannot tell

**Before.** `hello` on the shipped surface reached `corollary/kernel`, which
routed it to a capability the boot matrix does not register and abstained.
That is honest and it is still the kernel profile's correct answer — it is
reproducible today, and this release deliberately did not change it:

```
$ curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"hello"}]}'
… "content": "the corpus does not ground this, and nothing here will pretend otherwise.
              to hold it as conjecture instead, type:  suppose hello"
… "route": "dispatcher", "status": "exhausted",
   "detail": "routed to 'tool.freeform_answer', which the boot matrix did not register;
              abstaining rather than inventing a path (P-IH4: registered paths only)"
```

**Now.** The same four bytes addressed to `corollary/protocol` are a
greeting, and the answer names the protocol node it rested on:

```
$ curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"corollary/protocol","messages":[{"role":"user","content":"hello"}]}'
… "content": "disposition: ENTER\nfamily     : greeting\nprotocol   : protocol.greeting.a\nmove       : greet"
… "route": "protocol", "status": "found", "detail": "ADMITTED",
   "receipt": { "corpus_path": "protocol/protocols.json",
                "protocol_witnesses": ["protocol.greeting.a"],
                "grounding": "protocol-corpus" }
```

The sealed 8×4 context/corpus product is **honest, not balanced** — it was
never force-fitted into a Latin rectangle, and its `REFUSED` cells are the
majority. Every cell below is the runtime's own selected label, and all
**32 of 32** reproduce the table sealed at U-P0 before the runtime existed:

| surface | `fresh_root` | `probe_outstanding` | `literal_slot` | `programming_task` |
|---|---|---|---|---|
| `hello` | **greeting** | **probe_reply** | REFUSED | REFUSED |
| `good morning` | greeting | REFUSED | REFUSED | REFUSED |
| `still here` | REFUSED | probe_reply | REFUSED | REFUSED |
| `ready` | REFUSED | **probe_reply** | REFUSED | **expected_output** |
| `hello world` | REFUSED | REFUSED | **quoted_datum** | **expected_output** |
| `forty-two` | REFUSED | REFUSED | quoted_datum | REFUSED |
| `ok` | REFUSED | REFUSED | REFUSED | expected_output |
| `done` | REFUSED | REFUSED | REFUSED | expected_output |

Three surfaces (`hello`, `ready`, `hello world`) take **two different
selected moves** across positions. That is the whole claim, and it is
bounded: four families, seven protocol nodes, thirteen moves, **18**
normalized lookup keys.

Where the corpus and the context together do not decide, the turn **pauses
behind a minted need** rather than guessing:

```
$ curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"corollary/protocol","messages":[{"role":"user","content":"hi"}]}'
… "status": "waiting", "detail": "MATERIAL_AMBIGUITY",
   "need": { "slot": "protocol_uptake.candidate_move",
             "request_id": "519b3f43…", "options": ["acknowledge", "greet"] }
```

**Demonstrate.** The durable launch, unchanged from v0.23 except for the
profile name — the contrast between these two commands *is* the finding:

```powershell
$env:PYTHONIOENCODING = "utf-8"; .\.venv\Scripts\python.exe scripts\serve_chat.py
# then, from another shell — the refusal:
codex.cmd --disable apps --disable plugins -m "corollary/kernel"   -c 'model_provider="corollary_local"' -c 'model_providers.corollary_local.name="Corollary Local"' -c 'model_providers.corollary_local.base_url="http://127.0.0.1:8377/v1"' -c 'model_providers.corollary_local.wire_api="responses"'
# and the greeting:
codex.cmd --disable apps --disable plugins -m "corollary/protocol" -c 'model_provider="corollary_local"' -c 'model_providers.corollary_local.name="Corollary Local"' -c 'model_providers.corollary_local.base_url="http://127.0.0.1:8377/v1"' -c 'model_providers.corollary_local.wire_api="responses"'
```

**The controls did not fire, and equality is not a firing.** The
view-ceilings were **computed at U-P0 from the honest table** — predicted
before the generator ran, then confirmed by it — not chosen after the fact:
`c_surface` **21/32**, `c_position` **21/32**, both under the **24/32**
exclusive-home degeneracy bound. Re-fit on the runtime's *selected moves*,
each restricted view scores **exactly** its ceiling, and the position-switch
control — the blunt one that selects `greeting` at `fresh_root` and
`REFUSED` everywhere else — scores **exactly** its frozen **17/32**.
Equality is what a non-leaking runtime looks like; exceeding a ceiling
would have voided the claim (`voiding_sentence.fired: false`), and the
voiding sentence is quoted in the artifact rather than paraphrased here.

**R-U1 is licensed, and its sentence is exactly this much** — quoted
verbatim from `experiments/protocol_uptake_run.json`,
`result_gates["R-U1"].licensed_sentence`:

> *"On the sealed protocol corpus and honest context product, the same
> short utterance takes different verified interaction moves from context
> and corpus evidence, and material ambiguity pauses instead of guessing."*

Nothing wider is licensed. **R-U3**, the bounded negative, is **not**
licensed either: it requires a failed B2/B3 or a fired blind control, and
neither happened.

## Roadmap triage

| item | outcome |
|---|---|
| **§1 PROTOCOL UPTAKE** | **SHIPPED, R-U1 GREEN.** Nine scored gates green over 87 receipts; 32/32 sealed cells; 8/8 refusals; 4/4 ambiguities WAITING; 8/8 nested trajectories replay byte-identically 3× each; depth-nine plant refused at the declared cap of 8; authority plant opens nothing; 7/7 B9 mutants fire; B10 regenerates all 87 receipts byte-identically under set equality both directions |
| **§1.1 the course's selection** | **RECORDED as a decision**, with a disposition for **every** incumbent (table in [ROADMAP-v0.24](ROADMAP-v0.24.md) §1.1). PROTOCOL UPTAKE was scheduled; STRANGER-GATE was **not displaced** — its trigger is a prohibition, not a candidacy, and the slice opens no untrusted stream toward the write gate. The cost ledger entered its **eighth** parked cycle |
| **§1 U-PRE** | **SHIPPED.** 7 of 9 candidate inputs survive; `prior_move` and `source_seed` **DELETED** before a schema existed to carry them (`experiments/protocol_uptake_upre.json`) |
| **§1 U-P0** | **SHIPPED.** Sealed corpus at `protocol/protocols.json`, deliberately **outside** `data/`; honest 8×4 table; ceilings 21 / 21 / 17 frozen in the prereg and recomputed by B1; 56 fixtures + 7 B9 mutants |
| **§1 U-P1** | **SHIPPED.** codex-cli 0.150.1 capture: 14 tools declared on the conversational turn, `request_user_input` at parameters digest `23ee6f1a…`, **with its Plan-mode caveat written down in advance** (`experiments/protocol_uptake_host_capture.json`) |
| **§1 AMD-3** | **SHIPPED.** Third profile registered; every amended spec sentence rewritten one at a time; `corollary.capabilities` stays at **/2** *in writing*, with the bump trigger read rather than waved past; adapter binds to the exact captured digest and nothing else. 236 tests green at that commit |
| **§1 B7** | **SHIPPED AS A NEGATIVE — RED, three steps of four, both mechanisms named.** A completed registered gate that failed, not an `UNTESTED`. R-U2 unlicensed; **no Codex prompt-tool support is claimed**; text `WAITING` is the shipped path. Two successor probes filed in BACKLOG, neither taken |
| **§1 R-U3** | **NOT LICENSED** either. The bounded negative requires a failed B2/B3 or a fired blind control; nothing failed and nothing fired |
| **§2 prerequisites** (GUEST AXIOM inbound / ECHO amendment / HANDBACK) | **UNTOUCHED, as designed.** §2 says they do not start unless §1's course names them as dependants. It did not. All three stay parked behind their unchanged triggers |
| **§3 carried lanes** | **CARRIED** to [ROADMAP-v0.25](ROADMAP-v0.25.md) §3, each with its trigger. STRANGER-GATE now carries a **second independent arrival** (CHOKE); PREMISE LEDGER carries **two** new convergent arrivals; MIRROR FRAGMENT and the DIMENSION rider candidate are new parks |
| **CR-P0 registry re-seal** | **SHIPPED** (the v0.23 suite gate's own filing). Census 183 → **190** files, 37 → **43** receipt-marked sites, 19 → **22** kinds, 10 → **11** exclusions; seal **`8aed3282…`** |
| **§4 `[SUITE-GATE-V24]`** | **OPEN at rotation.** See the placeholder section below |

### The negative, in full, because it is a first-class result

B7 asked for four steps: function-call item → host result →
`function_call_output` input → exact request resume, served on
`corollary/protocol`. Three happened.

1. The server emitted **one** `request_user_input` function-call item, with
   the verifier-minted prompt and both candidate moves as options.
2. The unmodified host **bound a `function_call_output` to the exact
   pending request id**. The binding half of the wire worked, unmodified,
   first try.
3. **The output it bound was its own router's refusal** —
   *"request_user_input is unavailable in Default mode."* The U-P1 capture
   had already recorded that the declaration says the tool "is only
   available in Plan mode," *and that the declaration nevertheless arrived
   in an ordinary exec-mode request*. The host advertises in every mode a
   tool it will execute in one.
4. Independently, the host **replayed its own `function_call` item inside
   the follow-up `input`** (the `store: false` wire habit ¶AMD-3 recorded
   in advance as its one risk), which §4.2's deliberately narrow amendment
   refuses as a non-message item.

Either mechanism alone kills the fourth step — and even if the echo were
admitted, the bound output is an error string, not a candidate move, so the
resume would refuse `UNBOUND_ANSWER`. The scripted self-check passes on
the same wire shapes over loopback, so **the server's half is demonstrably
not the cause**; that self-check attests nothing about the host, and the
artifact says so in its own `attests` field.

## What changed, per area

### The third served profile

**Before.** Two session objects and, in code, a fall-through: `_fresh` read
*"kernel, else the slot-filling session,"* so every non-kernel model —
registered or not — silently constructed the conversation profile's demo
session.

**Now.** Three session objects, three-way exhaustive dispatch with the
fall-through `else` branches removed, and `corollary/protocol` backed by a
fresh `protocol_runtime.ProtocolSession` — not the slot-filling session and
not kernel line routing. The kernel profile's §5 line-grammar claim, the
conversation profile's §3 request-grammar claim, and both shipped capability
blocks are **byte-unchanged**, asserted in `tests/test_serve_chat.py`.

**Demonstrate.** `GET /v1/models` now lists three profiles; the sheet's
`profiles` key has three members and `schema` still reads
`corollary.capabilities/2`:

```
$ curl -s http://127.0.0.1:8377/v1/capabilities | python -m json.tool | head -3
{ "schema": "corollary.capabilities/2", "profiles": { "corollary/kernel": …,
  "corollary/conversation": …, "corollary/protocol": … }, …
```

### The sealed protocol corpus, outside `data/`

**Before.** No protocol corpus existed. `data/` is the corpus root that
`scripts/check_regeneration.py` owns; putting protocol nodes there was one
of the three named construction refusals.

**Now.** `protocol/protocols.json` is generated by
`scripts/build_protocol_corpus.py`, lives **outside** `data/`, and has its
own dedicated checker committed at U-P0 — because a generated file no
checker owns is a file that drifts. Seven protocol nodes, four families,
thirteen moves, 18 normalized lookup keys, an `ABSENT` absence sentinel,
and a declared stack depth cap of 8.

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python scripts/check_protocol_regeneration.py   # exit 0
```

It regenerates the corpus **twice into a temporary directory**, never into
the repository, byte-compares, re-checks every frozen prereg digest, and
recomputes `c_surface`, `c_position` and the position-switch agreement from
the sealed fixture table rather than from the builder's own report.

### The input audit that deleted two fields before they could be carried

**Before.** The design named nine candidate semantic inputs — six context
signals and three witness fields.

**Now.** Seven survive. `prior_move` is deleted because **no transition rule
reads it**: family admission is decided by the four families' signal-value
predicates, suspension and resumption by `protocol_stack`, reply binding by
`pending_need`'s identity. `source_seed` is deleted because provenance
survives it — B1 resolves a witness through `protocol_node_id` to the
generated node and its single committed builder. A surviving `source_seed`
would owe a B9 mutant that cannot change any outcome, which B9 forbids.

**Demonstrate.** `experiments/protocol_uptake_upre.json`, `survivors.count:
7`; and the run's B9 row: **7/7 mutants fired**, one per survivor.

### The uptake receipts

**Before.** No receipt kind existed for an interaction move.

**Now.** 87 raw `ProtocolUptake` receipts land **before** the compact gate
metrics, so the compact artifact cannot claim a replay of records the raw
artifact does not carry. Every receipt carries `authority_delta` as a
**plaintext present-and-empty field**, read as a field rather than inferred
from a digest.

**Demonstrate.** `experiments/protocol_uptake_receipts.json` (87 records),
replayed by `scripts/check_protocol_receipts.py` — B10 is set equality in
both directions, so a missing record fails and an extra record fails. The
authority plant (`please enable write, python, and shell access`) is
`REFUSED`/`UNLICENSED` with **0 process starts** counted by
`sys.addaudithook` — a fact about the run, not a reading of the runtime's
imports — and **zero** `data/`-tree byte changes.

### The registry census re-seal (CR-P0)

**Before.** The v0.23 suite gate's run 1 went red on a stale seal, and the
filing said the artifact had not been re-sealed at rotation. This cycle
added eight scripts, so the same staleness would have recurred.

**Now.** Re-sealed against the tree this release actually ships:
`program_tree_files_scanned` **183 → 190**, receipt-marked sites **37 →
43**, kinds **19 → 22** (the `ProtocolUptake` receipt family and
`serve_chat`'s protocol receipt are receipt-marked program text now),
excluded sites **10 → 11**, seal **`8aed3282…`**. The ANALYSIS recall prose
follows the probe rather than leading it: wider-net sites **179**,
uncovered **161**, admitted **18**.

**Demonstrate.** `experiments/cold_registry_census.json`,
`counts.program_tree_files_scanned: 190`, `census_seal: "8aed3282…"`;
`tests/test_cold_receipt.py::TheCensusRecomputes`.

### SPEC ¶AMD-3

**Before.** The spec said "two session objects" and "no third path", and
§4.2 refused every non-message input item.

**Now.** Each load-bearing sentence is **rewritten rather than
contradicted**, one at a time, with the amendment naming exactly which
sentences it touches and — the load-bearing half — exactly which it does
not. `corollary.capabilities` stays at **/2** because its recorded bump
trigger is *widening the published status alphabet*, and the protocol
profile's dispositions land inside the frozen closed set
(`ENTER`/`SUSPEND`/`CONTINUE`/`RESUME`/`EXIT` → `found`, `ASK` →
`waiting`, `REFUSED` → `refused`). The sheet gains keys; /2 has absorbed
that additive shape three times before.

**Demonstrate.** `docs/SPEC-chat-completions-skin.md` ¶AMD-3 (§4.2, §8);
`prompt_tool_adapters` on the live sheet registers exactly one pair,
`("request_user_input", 23ee6f1a…)`, with its provenance path. Any other
parameters digest gets the text `WAITING` fallback, never a guessed adapter.

## Discoveries of the cycle

Quoted, not duplicated — see [DISCOVERIES](DISCOVERIES.md):

- **"The host bound the exact request and refused the tool in the same
  breath."** *"codex-cli 0.150.1's tool wire and its tool policy are
  separate machines with opposite answers… the host advertises in every
  mode a tool it will execute in one."* Status: near-miss, kept
  deliberately.
- **"An audit that names the forbidden name carries it."** U-P0's invariant
  (i) — that the two U-PRE-deleted field names appear nowhere in the sealed
  artifacts — *cannot* be enforced by code that searches for those names,
  because the enforcing code then contains them and trips its own check.
  The honest form is positive: every signal id must be a survivor, and the
  checker derives the deleted names from the audit artifact at run time.
  Same shape as v0.22's removal arm that could not go red.

## Resolved from BACKLOG

- **PROTOCOL UPTAKE — shipped as the v0.24 headline.** The entry filed
  after the v0.23 Codex harness trial is pruned; its record is this
  document.
- **The stale CR-P0 registry seal** (filed at the v0.23 suite gate) is
  discharged by the re-seal above.

Kept, deliberately: the **two B7 successor probes** — the Plan-mode router
question and the echoed-`function_call` admission question. Neither is
folded into this cycle's claim, and admitting the echoed item is a wire
question owing its own registered test and a dated amendment, never a
widening after a red. New parks from the v0.25 course are filed in
[BACKLOG](BACKLOG.md).

## Honest limits carried forward

- **The fixtures are construction fixtures**, authored by this repository.
  Exact conformance to the transition table does **not** establish that the
  table describes human convention. There is no population claim here.
- **B7 is RED.** No Codex prompt-tool support is claimed by this release.
  The shipped path when a turn cannot decide is the text `WAITING`
  fallback, and a host that advertises `request_user_input` at any other
  parameters digest gets that fallback rather than a guessed adapter.
- **The protocol vocabulary is small and sealed**: four families, seven
  nodes, thirteen moves, **18** normalized lookup keys. A surface outside
  those keys is a lookup miss, and a lookup miss licenses nothing.
- **¶DEV-1 means served sessions replay fresh.** This skin does not resume
  durable sessions; every HTTP request is served by replay into a fresh
  session object. A protocol episode stack therefore does not survive
  across HTTP turns of its own accord — the runtime derives its
  `request_id` from its own session id so a `call_id` can survive the
  replay, and that is the only continuity claimed. Durable restore over
  HTTP remains unshipped and unclaimed.
- **No English understanding, no private-intent recovery, no general social
  competence, no learned-policy claim.** The candidate proposer in this
  slice is closed-form. The seven non-claims are enumerated in
  `experiments/protocol_uptake_run.json`.
- **Everything v0.23 left open is still open.** GUEST AXIOM served no
  implication; ECHO produced no collision table; person-wrong is unfilled,
  not underpowered-from-a-sample; R-NF's 0/220 licenses nothing about
  future stability.
- **The forward design was falsified once before it shipped.** Three of
  DESIGN-house-rules' first-draft reuse claims were false of the code
  (`frames.close_frame` refuses owned frames; `FrameSpec.declarations`
  cannot hold an arity-3 application; the shipped template grammar cannot
  express a relational axiom). The review record ships **inside** the
  design; it was reworked, re-reviewed MERGE AFTER FIXES, and all four
  blockers are fixed. Nothing in it is implemented.
- **A live shipped-parser hazard is now named and unfixed.** That same
  review found that `match_signatures.py` silently rewrites any identifier
  beginning `sum_ / prod_ / lim_ / max_ / min_` into the corpus aggregate
  head, so `sum_total(x)` is reinterpreted as `aggregate` **with no
  refusal**. It is filed, and it is a named checker-fix candidate in
  [ROADMAP-v0.25](ROADMAP-v0.25.md) §2 — not fixed by this release.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.** `data/`
and every `experiments/*.py` are byte-identical to `v0.23.0`
(`git diff --name-only v0.23.0..v0.24.0 -- data/` lists **nothing at all**,
and `git diff --name-only v0.23.0..v0.24.0 -- experiments/` lists no
`.py` — only `ANALYSIS.md`, the re-sealed `cold_registry_census.json`, and
this cycle's five `protocol_uptake_*.json` ledgers), so the checkpoints
attached to **v0.6.0** remain accurate for this release. Measurement
ledgers are committed in-repo at `experiments/*.json` —
`protocol_uptake_run.json`, `protocol_uptake_receipts.json`,
`protocol_uptake_b7.json`, `protocol_uptake_upre.json`,
`protocol_uptake_host_capture.json`, `protocol_uptake_prereg.json`,
`protocol_uptake_fixtures.json` — plus the corpus at
`protocol/protocols.json` and the B7 evidence extract at
`reports/b7-codex-session.log`.

## Ledger refresh (the release gate requires these verdicts in the notes)

`scripts/check_regeneration.py` — **exit 0**: *"coherence OK: 25 seeds
regenerate committed data byte-identically across `data/`,
`data_holdout/`."*

`scripts/validate_nodes.py` — **exit 0**: *"Validation passed for 12777
statement nodes across 27 corpora."*

`scripts/check_report_regeneration.py` — **exit 0**, four verdicts:

```
reports/signature_matches.json clean
reports/specializations.json   clean
reports/compression.json       clean
reports/decompositions.json    declared_divergence (declared pre-scale snapshot;
                               TRIAGE-v0.11 gate table row 6 and §5 — live
                               analysis is the pin source)
```

Three clean, one **declared** divergence — declared, not discovered. That
fourth row is the v0.16 convention working as designed: at ~12k nodes the
committed decompose report is the pre-scale ledger and is reported rather
than regenerated.

`scripts/check_protocol_regeneration.py` — **exit 0** (this cycle's new
checker; it is B1's source-truth gate and it regenerates into a temporary
directory, never into the repository).

`scripts/ingest_wold.py reach` — **ran, exit 0**: WordNet-lemma reach
**1,394 / 1,460 = 95.5%** (mapped-any 1,395; unmapped 65; `langgen_vocab`
27; `corpus_node_tokens` 59) against the pinned gitignored archive present
on this machine, byte-identical to the committed
`experiments/wold_reach.json` — unchanged, because `data/` did not move. A
contributor without the archive gets the refusal, which is *cannot verify*,
never *skipped*.

At ingested scale `reports/decompositions.json` is **not** rewritten as a
release step; the committed file stays the declared pre-scale snapshot
(TRIAGE-v0.11 §1.6).

## Reproduce

From a fresh clone at this tag:

```
# 1. the two gates this cycle added
PYTHONIOENCODING=utf-8 python scripts/check_protocol_regeneration.py
PYTHONIOENCODING=utf-8 python -m unittest tests.test_protocol_corpus tests.test_protocol_runtime \
    tests.test_protocol_controls tests.test_protocol_gates

# 2. read the registered run's verdicts off the committed ledger
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/protocol_uptake_run.json',encoding='utf-8')); \
    print(d['gate_greens']); print(d['voiding_sentence']['fired']); \
    print(d['result_gates']['R-U1']['licensed_sentence'])"

# 3. the negative, read the same way
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/protocol_uptake_b7.json',encoding='utf-8')); \
    print(d['verdict'], d['self_check']['passed'])"

# 4. the live surface — both profiles, one server
python scripts/serve_chat.py &
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"hello"}]}'
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"corollary/protocol","messages":[{"role":"user","content":"hello"}]}'
curl -s http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
    -d '{"model":"corollary/protocol","messages":[{"role":"user","content":"hi"}]}'
```

`scripts/run_protocol_gates.py` is the registered-run writer. It **refuses
an existing output path** and refuses a dirty or wrong-tip scoring tree — a
registered run that can overwrite its own evidence is not registered — so
re-running it against the committed artifacts is expected to refuse. Read
the committed ledgers instead; `--allow-dirty` exists for pre-run testing
only and records `registered_before_the_run: false`, on which every §9
sentence is gated.

`registered_before_the_run` is **true by git ancestry**, not by the
operator's word: the prereg commit `d954114` is a strict ancestor of the
scoring tip `4d44b43`, the B10 checker and the deliberately broken controls
were committed **before** the runtime they measure (`e637a12` before
`66cec41`), and `git status --porcelain` was clean.

## The suite at the tip

`[SUITE-GATE-V24]` — **NOT YET RUN at this rotation.** The full
`unittest discover -s tests` on the frozen tip is the tag's gate, and the
skill forbids tagging while it is PARTIAL. This placeholder is resolved
before the tag with the run's counts, its wall-clock, and its retained
receipts under `reports/test_gate_v024/`, exactly as `[SUITE-GATE-V23]`
was closed with 2,852 tests OK (skipped=5), 32,646.0 s (9 h 4 m) at
`867ad5c` — or the notes refuse the sentence and the tag waits.

One gate state is already known and disclosed rather than discovered by the
run: **the live cold reading is scheduled after this rotation.**
`cold/census_run2.json` still pins the previous registry bytes, so its
provenance test is red until the re-read. That is a deliberate ordering
recorded at the CR-P0 re-seal commit — the ~1 h cold act runs at the end of
the cycle so it reads the tree the release actually ships, in v0.23's
order.
