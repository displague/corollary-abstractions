# Plain text in: propose, verify, and name the hidden variable

**Status: maintainer-seeded design candidate, pre-course.** Seeded
2026-08-24 by maintainer direction, during the v0.20 rotation, with the
direction recorded verbatim so no course can quietly drop it. The goal,
in the maintainer's words:

> *are we on the path to me being able to hold a plain conversation with
> it, in plain text?* … *I do want that, if not v0.20 then v0.21.*

And the mechanism, also verbatim, which is the half that makes this a
design rather than a wish:

> *Something can be predicated on assumptions, true or false, and be
> verifiable under that pretext … those may be hidden variables —
> suppositions on unknown framing constraints.*

This document is the **named candidate** the v0.21 design course must
adjudicate explicitly: adopted, superseded by something measurably
better-fitting, or parked with the measurement that parked it. **Silence
is not a disposition.** The rule is the one ROADMAP-v0.20 §6 recorded
after the last seed completed its lifecycle: *"a park that cites a
measurement is a decision; a park that cites a preference is drift"*
(`docs/ROADMAP-v0.20.md:449-456`).

This seed also arrives with a lineage it must not hide. **Open-English
input is parked** (`docs/ROADMAP-v0.20.md:393`), and **INBOUND** — "open
English entering as structure" — was proposed in the v0.20 course and
**folded**, not adopted: `reports/design-direction-v0.20.json`
`outcomes.series_1.folds[0]` reads *"INBOUND -> the parked synonym layer
+ existing clarification loop, with the distractor precondition
recorded"*. Re-entry is legitimate in this repository, but only on the
terms ROADMAP-v0.20 §6 set for EVAL's return: **"Re-entry is legitimate
when it is evidenced and recorded; it is drift when it is neither"**
(`docs/ROADMAP-v0.20.md:438-442`). §3d names the evidence.

## 1. The idea, as directed

Plain text enters. A **small model** — the propose-and-verify seat the
language doctrine already blesses — proposes candidate interpretations
**as exact registered queries**. Exact code verifies each candidate.
Where the utterance **underdetermines** its meaning, the residue becomes
neither a refusal nor a silent guess: the missing framing is made an
**explicit supposition** — a hidden variable, named — and the answer is
served **conditionally under it**, with the receipt carrying the
assumption set. The served shape is:

> *assuming you meant X* [supposition S, stated] *, the answer is Y*
> [receipt].

The never-guess invariant survives because the guess is **explicit,
owned, and revocable**. The clarifying-question loop does not go away;
it becomes the branch taken when suppositions multiply past a declared
bound.

The one-line summary of the mechanism, in the tree's own vocabulary:
`suppose` today holds a claim **the person typed**
(`scripts/supposition.py:89` — `def suppose(text, *, owner="user")`).
This design lets the system **propose** the supposition, visibly, and
answer under it — never assert it, never keep it.

## 2. What the committed tree already says

### 2.1 The supposition machinery exists, and it is already honest

`scripts/supposition.py` is the "fabrication is a frame, not a refusal"
correction, built. Its properties, as committed:

- **Owner-held, and leak-proof by structure.** `suppose(text, *,
  owner="user")` (`scripts/supposition.py:89`, `:99`) opens a frame
  *"owned by the person who typed it, never the corpus"* (`:19`), with
  `FrameSpec.on_exit = "conjectured"` (`:21`, `:104`, `:115`) — *"nothing
  typed here can become a corpus fact, and no later answer can quote it as
  one."* The invariant is executed, not promised: *"Frame truths never
  leak"* (`scripts/frames.py:8`), an owned frame short-circuits the world
  loop (`:832-843`, *"world truths do not reach a belief frame
  unwitnessed"*), and contradictions are refused at `open_frame` /
  `assert_literal` (`:343-349`, `:884-916`).
- **The status word is already the right one.**
  `scripts/harness.py:1488-1490`: *"`waiting` and not `solved`: a
  supposition is held, not answered. Calling it solved would be the one
  word that turns fiction into a result."* The render closes with the
  honesty statement (`scripts/supposition.py:140-143`).
- **But the JSON receipt is nearly empty.** On the wire a supposition's
  receipt is one key: `scripts/serve_chat.py:927-928` returns
  `{"derivation": "session"}` for both `belief` and `supposition`, frozen
  at `docs/SPEC-chat-completions-skin.md:308`. **A conditional answer
  needs a real receipt and this is not one.** §3b writes the schema; it
  is the largest concrete build in the design.
- **And the frame is per-line, not session-scoped.** `suppose` builds a
  fresh `FrameExecutor()` and discards the `FrameState`
  (`scripts/supposition.py:96`, `:107`); only the frozen `Supposition`
  dataclass survives (`:66-74`) and `_route_suppose` never touches
  `session.state`. **There is no supposition that lives a session** — so
  "expires with the session" is something this design owes, not inherits.
  (Related subtlety: owned frames never demote on exit at all —
  `scripts/frames.py:1051-1053` — so `on_exit` guards the status rather
  than firing as a transition. The guarantee holds; the mechanism is not
  what the phrasing suggests.)
- **The three dispositions are already tabled**
  (`docs/DESIGN-text-resolution.md:114-120`): grounded → quoted answer,
  `solved`; conjecture → `suppose …`, `conjectured`; neither →
  dispatcher, `exhausted`, *"and it offers the frame"*. That section's
  closing line is the sentence this seed extends (`:126-128`): the
  unresolved branch *"names the `suppose` route rather than taking it
  silently, which is the difference between **holding** a supposition and
  **inventing** one."*

**So the whole novelty is one step, and it is a big one:** today the
system *offers* the frame — literally, at `scripts/harness.py:1030-1036`,
an ungroundable line comes back with *"to hold it as conjecture instead,
type: suppose …"* — and the person opens it. Here the system *proposes*
the frame, opens it **visibly**, and answers inside it. That step is
exactly where the doctrine can be broken, so §3b and §3c are the sections
that matter.

### 2.2 Where plain text lands today

`route_line` is a first-match-wins chain of thirteen rows
(`scripts/harness.py:1773-1824`; the spec's table is
`docs/SPEC-chat-completions-skin.md:159-173`, whose in-line citation to
`harness.py:1393-1437` is now **stale** and should be corrected to
`:1773-1824` when this design or any other touches that file). Row 12 is
`everything else → dispatcher → exhausted`
(`scripts/harness.py:1824`; `docs/SPEC-chat-completions-skin.md:173`).

**That is the whole surface this design touches.** Plain conversational
English that no route claims falls to row 12 and exhausts. The proposer
is a **pre-router for row 12 only**, and nothing else. That framing is
what makes the quarantine gate in §5 mechanical rather than rhetorical.

The status alphabet is **frozen as a closed set**
(`docs/SPEC-chat-completions-skin.md:175-184`): *"The skin transports
the engine's vocabulary; it does not edit it."* A new answer type is
therefore a **spec amendment with a version bump**, not a field added
quietly — §3b prices it.

### 2.3 The resolver's measured reality, stated with its caveat

| | measured | where |
|---|---:|---|
| dev coverage, registered run | **1.0** (28/28) | `experiments/text_resolution.json` `adjudication.T1.coverage` |
| dev coverage, post-hoc rules | **0.9643** (27/28) | `docs/DESIGN-text-resolution.md:68`, `:89-93` |
| in-corpus coverage, shipping rule | **0.833** | `docs/DESIGN-text-resolution.md:157` |
| false-positive floor, ships (F3) | **0.030** | `docs/DESIGN-text-resolution.md:144`; `experiments/false_positive_rate_f3.json:7` |
| morphology/synonym trade | **0.034**, reverted | `docs/BACKLOG.md:690-694`; `docs/DISCOVERIES.md:554-565` |

Two residuals stand, and this design inherits both:

- **The `gcd` miss.** *"`greatest common divisor euclid` did not resolve;
  the corpus writes `gcd`"* (`docs/DESIGN-text-resolution.md:80-81`), and
  *"Fixing it means a synonym layer, which is a design and not a patch"*
  (`:95-96`). The parked synonym layer is the residue this seed's
  proposer is aimed at.
- **The lexical-semantics route is refuted by measurement.**
  `docs/DESIGN-text-resolution.md:170-181`: WordNet hypernym roots put
  leaked glosses and real questions *"under the same small set of
  ancestors"*; *"the strongest available lexical alternative was tried
  and refuted. The next candidate is **structural** — the corpus states
  *relations*, and an everyday sentence usually does not."*

**A correction this seed makes to its own framing.** The refutation is
*not* recorded anywhere as "resolver expansion is a silent bind-rate
change." It is two measurements: hypernym roots do not separate
(`:170-175`), and the follow-on morphology expansion claimed 0.034
against a 0.030 ceiling and was **reverted, not tuned**
(`docs/BACKLOG.md:690-694`). The standing unpark rule is the nearest
thing to the silence argument, and it is worth quoting exactly because
this design must satisfy it: the lane *"unparks only with a mechanism
justified independently of the score it would move (the standard the
morphology trade already failed)"* (`docs/BACKLOG.md:530-536`).

**And one caveat that binds every gate below.**
`experiments/address_space_probe.json:31` records that *"the 1,000
sampled sentences of F3 were never committed — only 25 of the 30 claimed
ones are. The 0.030 denominator cannot be regenerated."* **No gate in
this design may inherit 0.030 as a live comparator.** A false-positive
comparison here must re-measure on a *committed* sample, or state that
it is comparing against a number whose denominator is gone.

### 2.4 The doctrine that licenses the seat, and the one that fences it

- **The creation loop.** `docs/DESIGN-language-as-structure.md:202-210`:
  propose constructors → verify → linearize → *"optional residual ranks
  among licensed linearizations"*, and the sentence at `:210`: **"This is
  propose → verify → repeat, not sample → hope."**
- **What the model may author.** `:422` — *"Residual proposers may
  suggest candidates into C; they never mark VERIFIED."* `:582-583`
  welcomes *"a residual that **proposes** parses, reference candidates, or
  ranks **legal** realizations … once baselines exist"*, right after
  `:581` rejects *"a 'grammar model' that **owns** structure from wiki
  text."* And `:465-466` — the residual *"ranks labels of candidates, it
  does not invent candidates from ℝ^d prose space."*
- **The tool admission bar** (`docs/DESIGN-interactive-harness.md:708-714`):
  closed outputs **or proposals only**; capability-blind baseline on the
  same path; missing checkpoint → **OFF, not crash**; tool-produced
  actions enter the session-scoped pruning record.
- **The standing clause the bar does not literally contain**, carried in
  the rendering designs and in both advisor briefs
  (`docs/DESIGN-sans-template-rendering.md:337-340`;
  `docs/DESIGN-foreign-voice.md:775-777`;
  `reports/design-direction-v0.20-brief.txt:7`): *"The refuse/serve
  decision is made by the round-trip gate **before** ranking, so a learned
  component is never the difference between refusing and answering."*
- **The empty seat, and why it is empty.**
  `docs/DESIGN-text-resolution.md:190-191`: *"Not a ranker. Where the
  query cannot separate candidates, the system asks with the candidates
  named. **That seat stays empty on purpose.**"* Restated
  `docs/DESIGN-ambiguity-and-context.md:79-80`.
- **Phase 2 vs Phase 6, which this design must not conflate.**
  `docs/DESIGN-interactive-harness.md:384-391` licenses a **bounded
  slot-filling grammar** that *"invents no slot, no path, and no fact; an
  unparseable utterance falls through to ASK"*; `:396-401` and `:732`
  keep **open prose authoring** at Phase 6, *"the last thing to land."*
  `docs/DESIGN-grounded-throughput.md:108` restates the boundary:
  *"`owns x ^ 2` routes; 'who owns x^2?' does not, and will not this
  cycle."* **This design is the Phase-2 half done by a proposer, not the
  Phase-6 half done early** — and §4's first question is whether that
  distinction survives contact.
- **The write gate is human.** `scripts/write_stage.py:76-80`: a staged
  candidate carries `approval_required: ["human_or_prover_review"]`;
  *"The system may prove a theorem and lay a candidate on the table; it
  may not put it in the corpus."*
- **Sentences, not conversation.**
  `docs/DESIGN-sans-template-rendering.md:153-164` states the language
  boundary and closes with exactly that phrase. This seed is the first
  document in the tree that proposes to cross it, and it should say so
  in those words.

## 3. What is genuinely new here (and what is not)

**Not new, and must not be re-invented as if it were:** an intent
classifier over utterances; a text-to-query seq2seq; RAG with an LLM
reading retrieved passages and answering in its own words. Each of those
puts the model between the person and the answer, which is the exact
arrangement this repository exists to be an alternative to. The course
should refuse any version of this design in which **the model's output
is read as content**.

New, and worth a design:

1. **The proposer emits queries, not answers.** Its entire output
   alphabet is the registered line grammar
   (`docs/SPEC-chat-completions-skin.md:159-173`) instantiated with
   corpus vocabulary. A candidate is a **string that route_line already
   accepts**; the model cannot emit anything else, and anything else it
   emits is discarded before verification, not repaired. This is
   `closed outputs … or proposals only` read literally, and it is
   testable by construction (every proposal is parsed by committed code).
2. **The residue is named, not absorbed.** Where two or more candidates
   verify, or where one verifies only under an assumption the utterance
   did not supply, the difference between them is lifted into a
   **supposition object**: a named hidden variable with a stated value.
   Nothing is chosen silently; the choice is *published as the condition
   of the answer*.
3. **A new answer type, first-class** — §3b. This is the part the design
   stands or falls on.
4. **Suppositions are session-scoped and expiring.** A supposition never
   reaches `data/*/nodes.json` — the flat prohibition
   (`scripts/write_stage.py:10-11`) is untouched — and it does not
   survive the session unless a human promotes it through the write gate
   (`scripts/write_stage.py:76-80`). A hidden variable is a *reading*,
   not a fact learned.
5. **Revocability is a surface, not a hope.** The person can say the
   supposition is wrong, and the answer that stood on it is withdrawn
   with the supposition. (This is where **UNSAY**'s parked blast-radius
   work becomes relevant — `docs/ROADMAP-v0.20.md:403` records it waiting
   for *"a driver"*. This design is a driver. Named, not claimed.)

### 3b. The conditional answer as a first-class object

The hard question, stated without softening: **a supposition converts a
refusal into an answer, and the standing rule forbids a learned
component from being the difference between refusing and answering.**

The design's answer is that **the answer type changes, and a
conditional-under-stated-supposition is a different speech act than an
answer.** That is only a real answer if the new type is a first-class
object with its own schema, its own status, and its own scoring — never
a decorated `solved`. Concretely:

**The object.** `ConditionalAnswer` carries:

| field | content |
|---|---|
| `route` | the registered route that actually produced the answer |
| `status` | **not** `solved` / `found` — see below |
| `suppositions` | ordered list of `{variable, value, source, why}`; `source` ∈ {`proposed`, `caller_declared`}; **non-empty by construction** |
| `answer_under` | the verbatim engine answer, unchanged from what that route would have emitted had the supposition been typed |
| `receipt` | the underlying route's receipt, plus the supposition set's digest |
| `alternatives_not_taken` | the other verified candidates, named, with their suppositions |
| `revoke` | the token that withdraws this answer and its supposition together |

On the wire it rides in `x_corollary`, whose required keys are already
fixed — `schema`, `profile`, `route`, `status`, `detail`, `receipt`
(`scripts/serve_chat.py:985-990`; normative at
`docs/SPEC-chat-completions-skin.md:263-276`, where `receipt` is *"always
present"*). `suppositions` is therefore a **receipt field**, not a new
envelope key, and the per-route receipt table
(`docs/SPEC-chat-completions-skin.md:300-310`) gains one row rather than
the envelope gaining a concept.

**The status, and here the tree contradicts the obvious move.** The
tempting option is to reuse `held` — already registered for the `suppose`
route (`docs/SPEC-chat-completions-skin.md:164`), already glossed *"held,
not answered"* (`scripts/harness.py:1488-1490`), zero alphabet change.
**But `held` is already an ANSWERING status.**
`scripts/serve_chat.py:141`:

```python
ANSWERING_STATUSES = frozenset({"solved", "found", "held", "PROVEN", "VERIFIED"})
```

So reusing `held` would make every conditional answer **score as an
answer** in the throughput metric, which is precisely the accounting this
design must not have. The course therefore chooses between:

- **Mint `conditional`, non-answering for scoring, receipt-carrying.**
  The alphabet is **frozen as a closed set**
  (`docs/SPEC-chat-completions-skin.md:175-184`;
  `scripts/serve_chat.py:126-134`), so this is a spec amendment with a
  version bump and a capability-sheet change — a real but bounded cost.
- **Reuse `held` and re-open `ANSWERING_STATUSES`**, which edits a
  frozen set from the other end and touches the `suppose` route's
  existing behaviour. Worse.

**The precedent that makes the mint workable** is already in the spec:
receipts are keyed on **(route, answered?)**, and the `closure` route
already has a status that is *non-answering for scoring* yet **carries
its receipt verbatim** because the negative is certified
(`docs/SPEC-chat-completions-skin.md:282-297`). A conditional answer is
the same shape: it carries evidence and is not scored as an answer. The
engine also already draws finer answer-type distinctions than the
alphabet suggests — `scripts/harness.py:1147-1154` explains why the
resolver returns `found` and not `solved`: *"Resolution locates a
statement whose words match; it does not answer a question … `solved` is
reserved for exact computation and exact lookup."* **A fourth grade
below `found` is a continuation of that reasoning, not a novelty.**

**The consequence, and it is the reason to believe the design is
honest:** refusal and clarification turns contribute **zero useful
tokens** to the throughput metric whatever their content length
(`docs/SPEC-chat-completions-skin.md:226-229`). With `conditional`
non-answering, **this design cannot inflate K by converting exhaustions
into conditionals.** The incentive that would corrupt it is removed by
the metric that already exists. Any course that proposes to score
conditionals as answers has to argue that in the open.

**And the invariant restated in its operative form:** the learned
component is never the difference between `exhausted` and `solved`. It
may be the difference between `exhausted` and `conditional`. Those are
not the same claim, because a conditional asserts nothing about the world
unconditionally — that is what `on_exit: conjectured` guards
(`scripts/supposition.py:21`).

### 3c. Why proposals are safe where resolver expansion was refused

The resolver change that was reverted (`docs/BACKLOG.md:690-694`) moved
a **rule** that every query passes through: it changed which queries
bind, globally and invisibly, and the price was a false-positive rate
above the shipping ceiling. It also failed the standing test that a
mechanism be *"justified independently of the score it would move"*
(`docs/BACKLOG.md:530-536`).

A proposer is a different object in three ways the course should check
rather than accept:

1. **Per-candidate, verified-or-refused.** Each proposal is
   independently run through committed code. A proposal that does not
   verify produces nothing — not a lowered threshold, not a weaker match.
   There is no global rule change to hide in.
2. **It cannot reach the rows that already work.** By construction the
   proposer only sees utterances row 12 already exhausted
   (`scripts/harness.py:1824`). Rows 0–11 are byte-identical with the
   proposer ON or OFF, and §5's quarantine gate is exactly that
   assertion, tested.
3. **It adds paraphrase and intent, not looser matching.** What the
   proposer buys over the resolver is the residue §2.3 named: `greatest
   common divisor euclid` → `gcd`; "who owns x squared" → `owns x ^ 2`;
   "does that hold if n is negative" → a supposition on `n`. The
   resolver's channel is *which words appear where*
   (`docs/DESIGN-text-resolution.md:162-164`); the proposer's channel is
   *which registered query a person plausibly meant*. Those are different
   signals, which is what the refuted-route's own successor note asked
   for — *"the next candidate is structural"*
   (`docs/DESIGN-text-resolution.md:179-181`).

**And the seat's occupant is already measured, which is the strongest
argument for confining it to proposing.** The v0.17 run put the same
pinned Qwen3-4B, handed the exact committed records the kernel's answer
rests on, at **4/49 = 8.2% correct with a median of 0.0 tok/s of useful
output**, against the kernel's 49/49 (`docs/RELEASE-v0.17.0.md:46-51`).
A model that cannot reliably *deliver* grounded content is exactly the
model that must never be on the serving path — and is still perfectly
capable of the much easier job of saying *"this might be `owns x ^ 2`"*
and letting committed code decide. **The design's confidence in the seat
is bounded by a number it already has**, which is the opposite of the
usual position.

**The honest residual risk**, stated so a reviewer does not have to find
it: proposals can be *wrong but verifiable*. "What is the cosine of a
double angle" and "what is the cosine of half an angle" both propose
verifiable queries; verification cannot tell which the person meant.
That is precisely the C-V4 lesson transplanted — a control that only
checks *that something verified* is measuring the verifier, not the
proposer. §5's distractor gate exists for this and is not optional.

### 3d. Lineage: BORROWED PREMISES, INBOUND, and what is new since

**BORROWED PREMISES** — *"conditional answers under quarantined
assumption sets"* — appears twice in the receipt and nowhere else:
`reports/design-direction-v0.20.json:74`
(`round_one_funnel.series_3[2]`) and `:114`
(`selection.declined["BORROWED PREMISES"]`), the latter reading *"parked;
likely the supposition frame's maturation - noted for when the API
attaches callers with real premise sets."* Restated at
`docs/ROADMAP-v0.20.md:404`, and given its fuller disposition in the
adopted design: `docs/DESIGN-statements-that-run.md:183-186` calls it
*"the closest of all parked directions to §3.3's guard object"*, with the
hand-off at `:1425-1428` — *"the same guard object seen from the asker's
side rather than the statement's."*

**A correction to how this seed was briefed.** The receipt says
*quarantined* assumption sets, and the phrases **"quarantine gates"** and
**"one leak voids"** appear **nowhere in this repository** — they must not
be quoted as BORROWED PREMISES' words. What the repository actually owns,
and what §5's G4 is written against, is the **frame-leak invariant**:
*"Frame truths never leak"* (`scripts/frames.py:8`), demotion on scope
exit (`docs/DESIGN-scope-and-modality.md:48`), and the no-telepathy rule
(`scripts/frames.py:832-843`).

**This design subsumes BORROWED PREMISES for the caller-declared case
and extends it.** Its unpark condition is external and unscheduled
(*"when the API attaches callers with real premise sets"*) because it
assumed premises arrive from *outside*. This design adds the case where
the system **proposes** the premise — strictly harder, and why the answer
type must be first-class rather than a header field. The `source` field
(`proposed` | `caller_declared`) is the seam: a caller-declared premise
set is the same object with the easy `source`.

**INBOUND** was folded in the v0.20 course to *"the parked synonym layer
+ existing clarification loop, with the distractor precondition
recorded"* (`reports/design-direction-v0.20.json`,
`outcomes.series_1.folds[0]`; the fold is repeated at
`docs/DESIGN-statements-that-run.md:209-214`). **The evidence that has
changed since**, which is what ROADMAP-v0.20 §6 requires a returning
direction to name:

- INBOUND proposed open English *entering as structure* — the Phase-6
  shape. This proposes open English **selecting among already-registered
  queries** — the Phase-2 shape (`docs/DESIGN-interactive-harness.md:384-391`).
  Different rung of the tree's own ladder.
- INBOUND had no answer for the underdetermined residue, which is why the
  fold sent it to the clarification loop. **The supposition frame is that
  answer**, and it was already built and already honest (§2.1).
- The fold recorded a **distractor precondition**. This design registers
  the distractor set as a *named gate* (§5, G3) rather than a
  precondition to be satisfied later.
- v0.19's C-V4 void taught the repository, at cost, that a structural
  gate cannot see the error class an evaluator can
  (`docs/ROADMAP-v0.20.md:45-61`). The same lesson applies here in
  reverse: verification cannot see proposal error, so the design carries
  a control aimed at proposals specifically.

Also touching this seed and named rather than left to be discovered:

- **HOSTILE DICTATION** is parked with *"the one trigger in this table
  that is a prohibition: it MUST run before any untrusted stream reaches
  the write gate"* (`docs/ROADMAP-v0.20.md:401`). **This design opens no
  such stream** — suppositions never reach the write gate, by §3 item 4 —
  and the course owes an explicit statement to that effect, because a
  plain-text intake surface is exactly what a later reader will suspect.
- **Licensed variant generation** is carried, three cycles running,
  because *"the realization grammar emits exactly one surface per term,
  so the learned preference seat has nothing to rank"*
  (`docs/ROADMAP-v0.20.md:389`; `docs/ROADMAP-v0.19.md:224` puts it
  sharpest: **"A ranker is not blocked by the admission bar — it is
  blocked by the absence of anything to rank."**). On the *input* side
  the opposite is true: a plain utterance licenses several candidate
  queries by construction. **The input side is where the ranker seat
  finally has a denominator**, and this design should say whether it
  intends to open it or keep asking (§4). Note that the deterministic
  ranker already exists and is closure-enforced —
  `scripts/preference.py` ships `preference.shallow.v1` with three
  registered pure features and raises on OOV (`:181`) — so the incumbent
  for any input-side ranking arm is written, not hypothetical.

## 4. Questions the course must answer before this becomes a preregistration

- **Is this Phase 2 or Phase 6?** The design claims Phase 2 — bounded
  filling of already-open slots — because every proposal is a registered
  query. But the *proposer* is unbounded English on the input side, which
  is the thing Phase 6 names. Either argue the boundary holds (the
  bound is on the **output** alphabet, not the input) or concede the
  design is Phase 6 arriving early and price it accordingly.
- **`held` or a new status?** §3b's two options. Reusing `held` costs
  nothing and reads slightly wrong; minting `conditional` reads right and
  amends a frozen alphabet. Pick, in writing, with the capability-sheet
  consequence stated.
- **What bounds the supposition count?** The tree has three bounds of
  this shape already, and they are precedents to argue from rather than
  re-derive: `MAX_CONTEXT_HOPS = 4` with visible `cycle` / `hop_ceiling`
  (`scripts/harness.py:1176`, loop `:1251-1360`,
  `docs/DESIGN-live-session.md:343-356`); **one** outstanding signed
  question per session (`scripts/retrieval.py:2622`); an unparseable
  utterance *"costs exactly one question"*
  (`scripts/conversation.py:257-261`); and the holdout's one-follow-up,
  25-id budget (`docs/DESIGN-when-to-ask.md:27`, `:135-137`). One
  supposition per answer is defensible; the number is a preregistration,
  and it should reuse `hop_ceiling` rather than mint a second ceiling.
- **Who verifies, exactly?** "Exact code verifies each candidate" covers
  thirteen routes of very different strength: `evaluate` computes; `owns`
  looks up; `resolver` matches words at a 0.030-era floor. **A candidate
  verified by the resolver is weaker evidence than one verified by
  evaluation**, and the receipt must say which — otherwise the design
  launders a weak match through a strong-sounding word.
- **Does the proposer see the corpus, and does that leak a holdout?**
  Proposals draw on corpus vocabulary, which means the proposer is shown
  vocabulary. What exactly? The holdout-quarantine discipline
  (`docs/DESIGN-holdout-quarantine.md`) applies and the course must say
  how.
- **What is the baseline?** Bar clause 2 requires a capability-blind
  baseline on the same path (`docs/DESIGN-interactive-harness.md:711`),
  refined at `docs/DESIGN-sans-template-rendering.md:334-337` to name an
  **incumbent** where one exists rather than mislabel it blind. Here the
  incumbent is *the resolver plus the clarification loop*; the blind
  control is *a random/frequency generator over the same grammar*. Both
  are needed and they answer different questions.
- **Does a conditional answer score as an answer?** §3b argues no and
  argues the existing metric makes that safe. A course wanting yes must
  say why the throughput incentive does not corrupt the design.

## 5. Candidate gates to sketch (a course will freeze them)

Sketched, not registered. A course freezes these with numbers, a
preregistration commit, and its own digests.

- **G1 — proposal coverage.** On a **preregistered plain-question set**
  committed before the proposer exists: what fraction of utterances yield
  at least one verified candidate? The denominator must name its
  population — the lesson the last seed learned the hard way
  (`docs/DESIGN-block-vocabulary.md:253`, after its headline number turned
  out to measure one generator script's boilerplate). Questions a
  maintainer wrote about this corpus are not questions a stranger asks;
  **STRANGER**'s park (`docs/ROADMAP-v0.20.md:394`) is the same fresh-half
  problem and should be cited, not re-encountered.
- **G2 — zero silent binds.** Every served interpretation is either
  verifier-confirmed **or** supposition-labelled. Not a rate: **any
  counterexample fails**, the standard T4 already carries — *"any
  counterexample is a failure, because it would mean the renderer authored
  a claim"* (`docs/DESIGN-text-resolution.md:53-56`).
- **G3 — the distractor set (the C-V4 lesson).** A preregistered set of
  **sentence pairs that differ in meaning and must not collapse to one
  interpretation** — the input-side analogue of C-V4's near-miss null
  (`docs/DESIGN-foreign-voice.md:689-700`). Voiding sentence, in C-V4's
  own form: *if the proposer maps a distractor pair to the same query
  above the registered floor, the design is measuring the verifier's
  tolerance and not the proposal, and the reading is void.* And C-V4's own
  failure mode is the warning: C-V4′ exists because C-V4 *"never
  establishes that the mutation should have moved"* what it measured
  (`docs/ROADMAP-v0.20.md:102-110`). **G3 must verify that its distractors
  really denote different registered queries before scoring** — the clause
  C-V4 dropped.
- **G4 — the quarantine invariant.** Unconditional answers **never
  change**: over a preregistered corpus of lines exercising rows 0–11
  (`docs/SPEC-chat-completions-skin.md:159-173`), every verdict dict is
  **byte-identical** with the proposer ON and OFF. Voiding sentence: *a
  single differing verdict voids the whole reading* — the house form of
  *"Frame truths never leak"* (`scripts/frames.py:8`), not a re-run of the
  differing case. Cheap, mechanical, and the gate that makes the rest of
  the design believable.
- **G4b — the supposition never grounds another answer.** A conditional
  answer's supposition must not be readable by any later turn as a
  premise. `scripts/frames.py:832-843` enforces the analogue for belief
  frames; G4b asserts it for proposed suppositions, which §2.1 shows must
  be **built** rather than inherited.
- **G5 — the blind control.** Replace the proposer with a
  **random/frequency candidate generator** over the same grammar and
  vocabulary; the conditional-answer rate must **collapse**. If frequency
  gets near the model, the recorded lesson applies — *"frequency can beat
  a weak learner"* (`docs/DESIGN-interactive-harness.md:393-395`) — and
  the seat ships empty with the number.
- **G6 — OFF, not crash.** With no model reachable, row 12 exhausts
  exactly as today. Bar clause 3 (`docs/DESIGN-interactive-harness.md:712`).
- **G7 — the supposition never becomes knowledge.** After a session of
  conditional answers, `data/*/nodes.json` is unchanged and
  `check_regeneration` is green.
- **Any false-positive comparison re-measures.** Per §2.3's caveat
  (`experiments/address_space_probe.json:31`) the 0.030 denominator cannot
  be regenerated; an FP claim here commits its own sample.

## 6. The machine blind reader

Second maintainer directive of the same date, recorded here because it
is a **cross-design instrument** and this seed is where it was written
down — but it **belongs to the voice design's run**, not to this one.

**The problem it solves.** C-V3, the determinacy sheet, requires thirty
rendered statements *"marked blind by a **non-maintainer**"*
(`docs/DESIGN-foreign-voice.md:678-681`). A single-maintainer repository
has no non-maintainer, so C-V3 has never run: **ABSENT**, with the
consequence recorded honestly — *"the claim it alone could license is
not made, here or anywhere"* (`docs/RELEASE-v0.19.0.md:49`), and *"the
claim is that the English determines the term **to the pinned
elaborator** — a claim about a machine"* (`docs/RELEASE-v0.19.0.md:407-410`).

**The directive.** A **pinned local model** (or a weak API model) serves
as the blind reader for determinacy checks — the C-V3 class of control —
across **all** rendering designs. Its terms:

- **Labelled machine-reader, never human.** The claim licensed is *"the
  English determines the term to an independent machine reader that never
  saw the term"* — strictly weaker than a readability claim, and the
  release wording carries the label every time. Same discipline
  `docs/RELEASE-v0.19.0.md:407-410` already used for the elaborator.
- **Pinned and seeded.** The v0.17 seat is pinned to the byte:
  `experiments/throughput_baseline.json` `model` —
  **Qwen3-4B-Instruct-2507**, Q4_K_M, `ollama:qwen3:4b-instruct`,
  `weights_blob_sha256: 85e4a5b7…`. A sheet marked by a weights-pinned,
  seeded model is **reproducible**, which no human sheet ever was.
- **Grades only, never serves.** It marks a preregistered sheet, enters
  no served path, ranks nothing, proposes nothing. Its output is an
  artifact, not an answer — which is why the tool admission bar does not
  apply and must not be cited as if it did.
- **Independence is the thing to prove**, and **this design fails that
  test against itself**: if the proposer and the blind reader are the same
  pinned model, a determinacy sheet over *this* design's conditional
  answers is not blind. Recorded now so nobody discovers it later.
- **Its own weakness is a feature.** The same model scored 8.2% on
  grounded delivery (`docs/RELEASE-v0.17.0.md:46-51`). A *weak* blind
  reader marking a rendering determinate is stronger evidence than a
  strong one doing so, because the failure C-V3 guards against is the
  reader supplying the mathematics itself — what a capable reader does and
  a weak one cannot.
- **It inherits C-V3's voiding sentence unchanged**
  (`docs/DESIGN-foreign-voice.md:685-687`). A machine reader can guess
  too, and the interleaved skeleton arm is what catches it.

**Disposition.** This unblocks **C-V3′ this cycle**, which belongs to
`docs/DESIGN-foreign-voice.md` §7 alongside C-V4′
(`docs/ROADMAP-v0.20.md:112-125`), not here. Recorded only so the directive
is not lost. Note that no `C-V3′` exists in the tree today — only `C-V4′`
is primed — so naming it is itself an act the voice design must ratify.

## 7. Non-claims of the seed

- **Not fluency.** Nothing here makes the system write better English.
  The output side is unchanged; the realizer and the corpus quotation
  rule (`docs/DESIGN-text-resolution.md:53-56`) still author every served
  sentence. A conditional answer is a *label wrapped around an existing
  answer*, not a generated one.
- **Not open-domain.** Outside the corpus the honest output is still a
  refusal (`docs/DESIGN-text-resolution.md:185-186`). A proposer that
  cannot find a registered query still exhausts.
- **The supposition is not knowledge.** It is never written to the graph;
  the flat prohibition on runtime writes stands
  (`scripts/write_stage.py:10-11`). It expires with the session unless a
  human promotes it through the write gate
  (`scripts/write_stage.py:76-80`). *"The system may prove a theorem and
  lay a candidate on the table; it may not put it in the corpus."* Note
  §2.1's finding: **the session-scoped supposition object does not exist
  today** and is part of the build, so "expires with the session" is a
  requirement this design owes, not a property it inherits.
- **The model never authors structure.** Proposals are drawn from the
  registered query grammar plus corpus vocabulary, and a proposal outside
  that alphabet is discarded, not repaired. *"Residual proposers may
  suggest candidates into C; they never mark VERIFIED"*
  (`docs/DESIGN-language-as-structure.md:422`).
- **Not a throughput claim.** §3b argues conditionals score as
  non-answering. This design must not appear in any sentence containing
  a K number.
- **Not multi-turn, yet.** P-LS6 and the one-line surface are unchanged
  by this seed; a supposition that persists across turns is a *different*
  design and the contradiction-between-two-typed-claims gap
  (`docs/DESIGN-text-resolution.md:130-132`) remains named and unfixed.
- **No claim on v0.20's scope.** This seed waits for the v0.21 course by
  design, and §2's census of the committed tree is its entire evidence
  budget until then.

## 8. Notes added after the seed — append-only

Nothing above this line is edited. A seed whose prose is repaired after it
is measured teaches the reader nothing about what it originally claimed,
and this document's own §3d complains about exactly that class of quiet
rewrite. So corrections arrive here, dated, quoting the sentence they
correct.

### 8.1 §4's Phase-2 argument was measured false, and the build exceeded it (2026-08-26)

**The sentence corrected.** §4's first question offers this defence of the
Phase-2 claim: *"Either argue the boundary holds (the bound is on the
**output** alphabet, not the input) or concede the design is Phase 6
arriving early and price it accordingly."* §3's item 1 states the same
argument positively: *"Its entire output alphabet is the registered line
grammar … A candidate is a **string that route_line already accepts**."*

**What measured it false.** Slice 1's construction prerequisite P1
(`experiments/session_p1_command_bound.json`) enumerated the registered
grammar class by class. Of **fifteen** template classes, **five are closed**
(34,863 admitted commands between them), **one is gated**, and **nine admit
countably infinite languages** — and two of those nine, the resolver row and
the complement row, are exactly where plain prose lands. P1's own finding
says it: *"an enumerating proposer has a finite target only because the
committed material is finite, never because the grammar is."* So *"route_line
accepts it"* is a **parse check**, not membership in a finite set, and a
proposer free to emit any accepted string has an **unbounded** output
alphabet. On the design's own argument, the Phase-2 claim would be false.

**What the implementation did instead, which is stronger.** The proposer
**never emits a query string at all.** Exact code
(`scripts/candidate_enumerator.py`) enumerates a finite candidate list from
committed material under `data/` only, and the model's entire output
alphabet is an **index into that list**, plus the token `NONE`
(`scripts/plain_proposer.py`). The list is capped at 8 and totally ordered,
both frozen in `experiments/plain_input_prereg.json` amendment 1. Selection
cannot reach a string that was not enumerated, so Phase 2 holds **by
construction** rather than by argument — and it is this repository's own
doctrine read literally: the residual *"ranks labels of candidates, it does
not invent candidates from ℝ^d prose space"*
(`docs/DESIGN-language-as-structure.md:465-466`).

**Why this note exists rather than an edit.** The design was right about the
disposition (Phase 2) and wrong about the reason. A reader who only met the
repaired reason would never learn that the repository's grammar is not
finite, which is the more useful fact and the one that constrains every
later proposer. Registered in full at
`experiments/plain_input_prereg.json` → `section_4_questions_answered.q1_phase_2_or_phase_6`.

### 8.2 §5's G9 was adjudicated NOT MET, and the defect it named is one row upstream (2026-08-26)

G9 is not a clause of this document — it was added by the slice-2
preregistration — but the **limit it exposes belongs to this design**, and a
reader of §2.2's placement rule should meet it here. §2.2 confines the
proposer to *"a pre-router for row 12 only, and nothing else"*. Row 12 is
the row where **nothing binds**. The silent binding P2 measured happens at
the **resolver**, an earlier row that §5's G4 protects by name. Measured on
the sealed thirty questions: **13 of 30 return `found` from the resolver
before the proposer is consulted at all**.

So this design can convert exhaustions into conditionals — §3b's whole safe
move — and it **cannot** touch a reading the resolver already took silently.
The adjudication, its reasons, and the ruling that fixed it are in
`experiments/plain_input_prereg.json` amendments 3 and 4; the defect is
filed in `docs/BACKLOG.md` with the thirteen question ids as its fixtures.

### 8.3 §7's "Not open-domain" non-claim was contradicted by the registered run (2026-08-26)

**The sentence measured false.** §7: *"**Not open-domain.** Outside the
corpus the honest output is still a refusal
(`docs/DESIGN-text-resolution.md:185-186`). A proposer that cannot find a
registered query still exhausts."*

**What the run measured.** Two of the sealed thirty questions authored to
exhaust came back as clarifications naming corpus readings rather than as
refusals: `g1-26` *"how do i change a tyre"* and `g1-29` *"what did i ask you
before"*. The first was offered *Average Rate of Change*, *Fundamental
Theorem of Calculus, Evaluation Part* and *Derivation Takes Its Category from
the Affix*.

**And the proposer is not what broke it, which is why this note belongs to
the design rather than to the model.** On both, the model answered `NONE` —
it found no registered query, exactly as §7 says. What served the
clarification is the **branch rule**, which fires on the count of *verified*
candidates and never consults the proposer's `NONE`. The rule is
`experiments/plain_input_prereg.json` amendment 2, and amendment 2 was
written against §3b's `alternatives_not_taken` field and §1's *"the branch
taken when suppositions multiply past a declared bound"* — it never met this
sentence. So two sentences of this document imply different branch rules, and
the run is what found that out.

**Not repaired.** The rule had already been frozen before it ran, and
changing it after watching it behave is the move this repository does not
make. It is filed in `docs/BACKLOG.md` with the unpark condition, and with
the warning that letting a learned `NONE` suppress a clarification puts the
model back on the refuse/serve boundary the standing clause
(`docs/DESIGN-sans-template-rendering.md:337-340`) keeps it off.

### 8.4 §2.3's motivating residual is out of this design's reach (2026-08-26)

§2.3 names the `gcd` miss as *"the residue this seed's proposer is aimed
at"*. In the registered run, *"how do you compute the greatest common divisor
recursively"* enumerated **zero candidates** — the proposer was never
consulted and row 12 exhausted exactly as before. Enumeration is by shared
content words and the utterance shares none with a statement the corpus
titles `gcd`.

**You cannot select what was never enumerated.** The trust shape §8.1 records
as stronger than the design's own argument — an index into a finite list — is
also what puts this residue out of reach: a selector's ceiling is its
enumerator's recall. The parked synonym layer, *"a design and not a patch"*
(`docs/DESIGN-text-resolution.md:95-96`), remains the blocker it was, and a
successor aimed at this residue has to build it rather than route around it.
