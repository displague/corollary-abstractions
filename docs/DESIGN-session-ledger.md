# The session ledger

**Status: design only.** Nothing here is implemented. This document is the
v0.21 course's selected direction (receipt:
`reports/design-direction-v0.21.json`), written as the **completion of
[DESIGN-plain-input](DESIGN-plain-input.md)** — the maintainer-seeded
incumbent ROADMAP-v0.20 §5 ordered this course to adjudicate explicitly.
Adjudication: **ADOPTED**. The incumbent supplies the intake (a small model
proposes readings; exact code verifies; unresolved framing is served as an
explicit supposition). This design supplies the object that intake writes
into: **the session** — the thing a conversation happens inside of,
committed, replayable, and receipted across turns.

## 1. The boundary being moved — and the precedents that bound it

Three committed objects already occupy parts of this ground, and this
design is built on them rather than beside them:

- **`experiments/harness_session.json`** (v0.10 item 5, written by
  `scripts/session_run.py`): a committed, recorded end-to-end session —
  four legs, a capability matrix, `corpus_before`/`corpus_after`, and
  `tree_unchanged_by_refusals`. `docs/DESIGN-live-session.md:38-41`
  already defines "recorded session" as a term of art. Its granularity is
  the **leg**, not the turn, and it carries no per-answer digest chain.
- **`scripts/conversation.py:335-438`** (`save`/`restore`): durable
  session state with a **keyed-MAC-per-binding** ledger snapshot, a
  monotone counter refusing rollback, `authoritative`/`superseded`
  status, and a `RestoreReport` naming admitted vs refused entries —
  exercised by ~40 tests in `tests/test_session_durability.py`. Its own
  comment (`:338-350`) argues *against* an envelope MAC, and
  `serve_chat.py`'s ¶DEV-1 rule quotes both halves: requests replay into
  fresh sessions, **and** `save`/`restore` are *not in the serving path*.
- **`experiments/throughput_tasks.json`**: a sealed multi-turn task
  corpus with `seal`, `counts`, `scoring_rules`,
  `rendering_module_digests`, and a real `turn_index` — the committed
  model for how a conversation-shaped denominator is frozen before the
  scored party can move it.

What none of them is: a **per-turn journal of a served conversation, with
a digest chain over served answers and per-answer citations of the
assumptions each answer consumed**. `scripts/supposition.py:96-107`
builds a fresh `FrameExecutor` per typed line and discards the
`FrameState`; the supposition receipt served today is one key,
`{"derivation": "session"}` (`scripts/serve_chat.py:1092`). A declared
assumption does not persist, and no committed object records which
answer depended on which assumption. That — not "no committed session
object exists" — is the gap.

**Re-entry, recorded per ROADMAP-v0.20 §6's rule.** Byte-exact session
re-run was registered once before — `DESIGN-v010-harness-session.md`
P5 — and adjudicated **MISSED IN KIND**: *a session that mutates the
corpus cannot re-run byte-identically, because the second run meets a
different world* (`scripts/session_run.py:22-30` carries the lesson).
What has changed to make replay askable now, stated so the re-entry is
evidenced rather than drift: (a) this design's recorded sessions are
**scoped to non-mutating turns only** — no write-gate line may appear in
a recorded session this cycle (frozen in §6 P3, before any seal); and
(b) every environment fact that moved bytes since v0.10 is now
digest-pinned (§3's pin table names each producer). Replay of a
non-mutating session against pinned corpora is P5's corrected guarantee
— *re-verifying the record* — extended from one session to a sealed
corpus of them.

**The human capability unlocked:** a person declares an assumption once,
converses under it, and gets answers that name which of their assumptions
each answer consumed — and a stranger, handed the journal, can replay it
offline and get the same bytes or a typed refusal. Plain conversation
(DESIGN-plain-input's goal, the maintainer's stated ambition) needs this
object under it: a supposition that does not persist is a supposition the
next turn silently forgets.

## 2. Why this direction survived the course

Three isolated series ran (nine rounds, fifteen directions; receipt as
above). The selection evidence, stated only as far as the receipt
carries it:

- **Series 1** (claim machinery) proposed enumeration-complete prose
  readings (FORK), found the completeness claim unreceiptable — prose
  has no semantics the exact layer can adjudicate — and folded itself
  into two probe artifacts for the incumbent (§6 P1, P2). Its lead,
  WITNESS (checker-signed evaluator-agreement lemmas; preregistration
  draft recorded in the receipt's `series_1.preregistration_draft`),
  goes to the next roadmap as item 2: it repairs the claim-kind the
  v0.20 conformance void measured, and it is deliberately not this
  headline because it moves what the system can prove, not what a
  person can do.
- **Series 2** (relationships over time) produced LEDGER — the session
  as a first-class object. Its round-one text, quoted in the receipt's
  `series_2.round_one_quote`, named the gap in the incumbent's frame —
  *"a conditional answer's condition lives in the person's head, not in
  any artifact"* — before the incumbent was disclosed to it at round
  two. Adopted here as §3–§8.
- **Series 3** (the library itself) produced ATLAS (a total obstruction
  map with witnesses — honest that it is an instrument: "makes zero
  statements reachable"), DEMAND (an obstruction ledger against a
  question dump the program did not author), and ABSENCE
  (snapshot-relative absence certificates). All three park with named
  probes (listed here and routed to BACKLOG by §13); the governance
  record counsels against instrument-shaped headlines, and the counsel
  held.

Declined with reasons, so the funnel is not waste: LESSON (refusals that
teach) was narrowed under round-two constraints to its stranger-free
half and renamed GRAFT (person-taught macros over the registered
grammar, reserved namespace) — the transformation is recorded in the
receipt; GRAFT parks. RECALL folded back into the twice-parked
withdrawal lane, donating one clause to its trigger (an over-broad
impact set counts as failure, not caution). HANDSHAKE merged into
RATCHET's archive replay, which parks with its **pin audit** named as a
cheap rider any cycle can run. IF (checker-signed reductions) parks
with its anti-triviality predicate noted as the confound-resolver to
build first when its turn comes. TRANSPLANT parks with its one-week
core-edit probe recorded. EXHIBIT was declined in writing by its own
series: it builds meaning on the layer whose conformance run voided,
and revives only if a non-void conformance instrument (item 2) ships
first.

## 3. The one new first-class object

`experiments/sessions/` — append-only, one journal per recorded session,
three record types. **A recorded session is not seed-regenerable and
must never live under `data/`**: `scripts/check_regeneration.py`
scans only `data/` and `data_holdout/`, seeds are the source of truth
there, and a journal has no seed. Journals live under `experiments/`
with a digest pin and a test, the committed pattern
`check_regeneration.py:97-100` names for hand-authored artifacts; a
G7-style coherence clause is in the gate (§7 B11).

Field names are the contract; implementation may extend, never rename
or repurpose. The record types (named to avoid colliding with the
tree's existing signed slot `binding`s in `conversation.py`):

**SessionHeader** — `session_id`, `created_utc`, `pins` (each with its
named producer, and perturbing any one must refuse):
`corpora_digest` (the write-gate's working-tree digest machinery,
scoped to `data/`), `line_grammar_digest` (sha256 of `LINE_GRAMMAR` as
rendered by the harness), `rendering_module_digests` (**the committed
name** — same derivation as `experiments/throughput_tasks.json`'s
field), `checker_toolchain_digest` (the pinned `lean-toolchain`
derivation `external_verifier` already uses), `capability_sheet_digest`
(sha256 of the served sheet bytes), and — slice 2 only, key omitted
until then, omission meaning "no proposer served" — `proposer_model_digest`
(the `.runtime/baseline` digest-pin pattern).

**Assumption** — `assumption_id`, `declared_at_turn`, `text_bytes`
(verbatim, never summarized), `normal_form` (from
`supposition.py:_atom`, whose self-limitation is inherited verbatim:
*"deliberately tiny: this is not negation parsing"* — three leading
negation markers, nothing else; §7 B4's conflict arm is scoped to
exactly that), `status` ∈ {`live`, `superseded`, `retracted`},
`superseded_by`, `mac` (per-record keyed MAC from the committed
`session_keys.py` ring — the mechanism `conversation.py:338-350`
already argued for, reused rather than reinvented).

**Turn** — `turn_index`, `input_bytes`, `resolution` {`kind` ∈
{`exact`, `supposition`, `refusal`}, `grammar_query`,
`assumption_id`}, `assumptions_declared[]`, `assumptions_cited[]`,
`live_set_digest` (digest of the live assumption set — not the set
itself; journal size stays linear), `result` {`kind`, `refusal_type`,
`answer_bytes_digest`}, `receipt_digest`, `prev_turn_digest`, `mac`.

**Citations are read-derived, not hand-placed.** `assumptions_cited` is
emitted by a read barrier on `normal_form` access inside the resolver:
a citation exists iff a read event exists, and §7 B12 checks the
correspondence mechanically. A declaring turn does **not** cite the
assumption it declares (`assumptions_declared` and `assumptions_cited`
are disjoint on that turn by construction), and declaring turns are
excluded from the binding-dependence denominator.

> **Note added 2026-08-26, after the slice-1 runs and their independent
> review.** B12's phrase *"recorded independently of the journal writer"*
> is worth pinning down, because the implementation's first run artifact
> overstated it. What is independent is the **writing**: two functions,
> two files, and the read log derived from the barrier's raw event list
> rather than from anything the journal writer computed. What is **not**
> independent is the source — both sides descend from the same in-memory
> `ReadBarrier`. So B12 corroborates that the journal writer neither
> dropped nor invented a citation, which is real and checkable and is what
> this clause is for. It does not corroborate the barrier itself: if the
> barrier recorded the wrong thing, both sides would carry it and agree.
> That is why §4 lists the read-barrier instrumentation as **trusted**
> code rather than measured, and why B4 — does the answer move when the
> cited assumption moves? — is the clause that tests the consumption the
> barrier claims to have seen.

**Bounds** (answering DESIGN-plain-input §4's question rather than
re-dropping it): live assumptions per session are capped by the same
ceiling family the incumbent recommends reusing (`hop_ceiling`'s
committed pattern); the cap is frozen at **8** live assumptions —
declaring a ninth refuses with a typed `assumption_budget` refusal.
Sessions are capped at **64** turns.

**Integrity.** Per-record MACs (keyed, `session_keys` ring) plus the
`prev_turn_digest` chain; the journal's whole-file digest lives
**out-of-band** in the corpus seal artifact (§6 P3), never inside the
journal it covers. §7 B8 states its threat model explicitly.

Tool: `scripts/replay_session.py` → `replay_report` {`turns_total`,
`turns_reproduced`, `first_divergence_turn`, `pin_mismatch[]`}. Any pin
mismatch yields a typed `stale-environment` refusal, never a guess.

## 4. Trusted and untrusted components

Trusted (exact code, review-carried): the journal writer, the
canonicalizer, the replayer, the MAC/digest machinery, the read-barrier
citation instrumentation. Untrusted and quarantined exactly as
DESIGN-plain-input draws it: the proposer model (slice 2 only) proposes
candidate readings; nothing it emits reaches a journal except through
exact verification, and supposition-conditional answers keep the
incumbent's rule — a `conditional` answer status scoring **zero** useful
tokens, so conditional service can never inflate the throughput claim
(inherited verbatim and re-tested, not restated).

## 5. Slices, in registered order

**Slice 1 — the object, before any prose.** Journal + recorder wired
into the existing typed-line session (`CoreSession` already threads
`session_id` and a typed `SessionEvent` trace; the recorder rides it).
Suppositions typed today (`suppose ...` lines) become Assumption
records instead of discarded state. No learned component anywhere in
slice 1. Gate clauses B1–B8 and B10–B12 run on slice 1.

**Slice 2 — plain input lands inside the object.** DESIGN-plain-input's
proposer, unchanged in trust shape, writes its resolutions and
suppositions into the same journal. B9 is slice 2's gate clause,
registered now, scored only when slice 2 exists; it does not count
toward slice 1's verdict. The incumbent's open question (conditional
answer vs clarifying question) is informed by P1/P2 **before** the
proposer is built.

## 6. Construction prerequisites (committed before implementation)

- **P1 — the finite bound.** Compute and commit the bound on admitted
  commands per template class of the registered grammar (series 1's
  fold: the grammar is finite; enumeration cost becomes a number).
- **P2 — separator expressibility.** For ten hand-sealed ambiguous
  prompts: does any single admitted command distinguish the rival
  readings under exact evaluation? If no separator exists for most, the
  clarifying-question arm has nothing to ask and the conditional-answer
  arm wins by measurement. Committed either way.
- **P3 — the corpus, sealed ahead of the citer.** In order, each frozen
  before the next exists: (1) the recording protocol — session count
  cap **60**, turn cap per session, the **no-write-gate-turn rule** (a
  recorded session contains no corpus-mutating line; a session that
  acquires one is excluded whole, the exclusion counted and published),
  and the recorder's code digest — all committed **before recording
  begins**; (2) recording, capped by the protocol, no
  record-until-the-counter-is-met (the STRANGER caveat from
  DESIGN-plain-input §5 G1 is inherited: these are maintainer-authored
  sessions and the claim is scoped to them — no stranger-usability
  claim); (3) the seal — `experiments/session_corpus_seal.json`
  carrying every journal's whole-file digest, the turn count, the
  binding-dependent count, and an A/B split by the committed
  hash-derived rule `half = 'B' if int(sha256(session_id)[:2],16) % 2
  else 'A'` (the `throughput_tasks.json` device, reused verbatim):
  implementation and debugging may exercise half A only; **half B's
  first execution is the registered run.** Floor: ≥**30** sessions,
  ≥**120** turns, ≥**36** binding-dependent turns in half B's share
  alone. If the capped protocol cannot reach the floor, STOP: publish
  "multi-turn binding is rare in practice" as the cycle's finding and
  build nothing further.

## 7. Construction gate (numbers frozen now)

- **B1.** P3's seal exists before the replayer is written; any edit to
  a sealed journal or the seal voids the run (the seal's digests are
  what B1 compares against).
- **B2.** Unmutated replay reproduces `answer_bytes_digest` for **every
  turn the seal records** — the denominator is the seal's own count,
  not a round number. One mismatch is red. No tolerance. (P5's scope
  rule makes this askable: no recorded turn mutates the corpus.)
  Budgeted from measured costs: pooled session boot is ~7.5 ms and a
  typed line serves in milliseconds, so full-corpus replay is minutes,
  not hours; if a replay run exceeds **30 minutes** the overrun is
  itself published as a finding before any verdict is read.
- **B3.** Each pin field perturbed individually must yield
  `stale-environment`, never an answer — every pin, no sampling.
- **B4.** Mutating one *cited* assumption (`text_bytes` +
  `normal_form` in the Assumption record **only**; the declaring
  turn's `input_bytes` untouched; the mutated journal is a fixture
  outside `experiments/sessions/`, never a valid journal) on each
  binding-dependent turn in half B → different `answer_bytes_digest`,
  or a typed conflict-refusal where the mutation flips `_atom`
  polarity (the only conflict `_atom` can see). **Every** turn must
  respond; each non-response is red, published individually with
  cause. 100% or red — the miss-budget the course draft allowed is
  dropped in favor of the house standard (no tolerance, misses
  published).
- **B5.** 60 sham assumptions (well-formed, never cited): **0/60**
  flips.
- **B6.** ≥30 mutations of *live but uncited* assumptions: **0** flips.
- **B7.** 100% of refusal turns carry `receipt_digest` with explicit
  `assumptions_cited` (empty allowed; null red).
- **B8.** Tamper control, threat model stated: the tamper script
  rewrites one turn's bytes **and recomputes every downstream
  `prev_turn_digest` consistently** — the naive-chain repair a
  file-holding adversary would perform. Detection must come from the
  keyed MACs (the tamperer holds no key) or the out-of-band seal
  digest, not from chain arithmetic. 20/20 or red. An arm where the
  tamperer does *not* repair the chain is run too, and reported, but
  passing only that arm is not passing B8.
- **B9** *(slice 2 only, registered now)*. The proposer's input at turn
  *j* contains no bytes from earlier turns other than assumption
  `normal_form`s. Any leak is red — history reaches the model only
  through the exact layer.
- **B10 — stateless equivalence.** Every turn with empty
  `assumptions_cited` must render byte-identical to the same line
  served statelessly. The quarantine made mechanical: session state may
  never leak into unconditional answers.
- **B11 — coherence.** `scripts/check_regeneration.py` green after
  recording (journals under `experiments/` leave `data/` untouched —
  the v0.10 artifact's `tree_unchanged_by_refusals` ancestor, extended
  to the whole corpus), and the seal's digests revalidate against the
  committed journals.
- **B12 — citations are earned.** For every turn in half B, the
  citation set equals the read-event set from the resolver's read
  barrier (recorded independently of the journal writer). One
  uncorroborated citation is red.
- **B13 — the 20-turn audit, registered.** 20 turns drawn by seeded
  rule from half B's binding-dependent set, arm-blind (drawn and
  ordered by the same sealed mixer as §8), hand-checked: does the
  answer's *meaning* depend on the cited assumption? Published as a
  table beside the gate; below **16/20** the residual risk in §11 is
  promoted from "named" to "measured against the claim" and the served
  line carries it.

## 8. Blind control and voiding sentence

Mutations for B4/B5/B6 are generated by one sealed script mixing the
three arms; the scorer sees no arm labels until after scoring.
**Voiding sentence, frozen now:** *If mutating assumptions the answer
does not cite changes the served answer at any nonzero rate, the
replayer is keying on transcript bytes rather than assumption
semantics, and the multi-turn-assumption capability is void for this
cycle; no session-replay claim is made.* A perfect B4 score beside any
B5/B6 flip is not sensitivity — it is a hash of the transcript, and it
voids.

Cheapest capability-blind baseline: a replayer that re-serves each line
statelessly, ignoring Assumption records entirely. Because B4's
mutation touches only the Assumption record and never the declaring
line's `input_bytes`, the stateless baseline **cannot** respond to any
B4 mutation — by construction, not by hope. It must pass B2 on
assumption-free sessions and must score 0 on B4. If it scores above 0
on B4, the mutation harness is leaking mutations into `input_bytes`
and the harness itself is red — fixed before anything is scored.

## 9. Result gate

The gate above is construction. The capability claimed, and the number
that licenses it: **R1** — on half B's first execution (the registered
run), every binding-dependent turn's served answer carries its
citations (B12-corroborated) and replays (B2), with B4–B6 and B10 green
and B13 ≥16/20. If R1 holds, the served claim is: *recorded sessions
replay, and conditional answers name the assumptions they consumed.*
Nothing more. R1 failing on any clause serves nothing and publishes the
readout.

## 10. Corruption, vacuity, and negative controls

B5/B6 are the corruption pair; B8 is journal-tamper with its threat
model; B10 is the leak control; B12 is the citation-corroboration
control; the stateless baseline is the vacuity control. Negative
honesty: sessions are *reproducible*, not *correct* — a wrong answer
replays as faithfully as a right one, and the artifact says so.

## 11. Stop conditions and non-claims

Stop conditions: P3's floor (stop, publish the finding); any B5/B6
flip (void, capability withheld, the journal survives as an
instrument); B10 or B12 failure stops the slice before serving.

Non-claims: no completeness over readings (the unreceiptable claim
series 1 refused); no correctness claim (reproducibility only); no
cross-session or cross-person memory; no portability beyond the one
workstation; no human-satisfaction claim; no stranger-usability claim
(P3's sessions are maintainer-authored — STRANGER's park is cited, not
re-encountered); supposition-conditional answers stay out of
throughput; nothing here claims the incumbent's proposer works (slice
2 carries DESIGN-plain-input's own gates unchanged); the machine
blind reader belongs to DESIGN-voice-completion's run and makes no
appearance here.

**Residual risk, named and priced only partway:** cited-but-inert
assumptions. `assumptions_cited` is emitted by the serving path — the
same party B4 scores — and an assumption mechanically threaded into
answer bytes flips B4 without the answer *meaning* depending on it.
B12 (read-derived citations) and B13 (the registered arm-blind hand
audit) narrow it; B13's floor decides whether the claim ships with the
risk named or measured. The gate proves byte-dependence; byte-
dependence is the claim served — nothing stronger.

## 12. The suspended habit

Suspended for this cycle, scoped to chat/harness sessions only: the
rule that the served surface is stateless one-line-in, one-answer-out.
B10 is the fence: statelessness remains byte-exact wherever no
assumption is cited. The suspension ends (state becomes a shipped
property, or is withdrawn) at the v0.21 gate, by that gate's own
verdicts.

## 13. Where status lands

The next roadmap's item 1 is this design + DESIGN-plain-input as one
lane; its item 2 is WITNESS (the conformance void's claim-kind
successor — preregistration draft in the course receipt; its compact
design lands before its slice). ANALYSIS gets the registered run's
numbers; DISCOVERIES gets P2's answer if it decides the
conditional-vs-clarify question; BACKLOG gets §2's parked probes with
their triggers. The course receipt carries the full funnel, the
LESSON→GRAFT transformation, and the series-2 round-one quotation §2
rests on.
