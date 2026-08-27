# The guest axiom

**Status: design only.** Nothing here is implemented. This is the v0.23
course's selected direction (receipt:
`reports/design-direction-v0.23.json`, three isolated series, nine
rounds, fifteen directions). It is the maintainer's own long-recorded
goal, arrived at independently by an outside advisor and then chosen
over the metric-leading alternative by explicit orchestrator ruling —
the ruling and its cost are §2.

## 1. The boundary being moved, and the person it is for

The maintainer's standing question, quoted from the project's own
memory: *"Something can be predicated on assumptions, true or false,
and be verifiable under that pretext — those may be hidden variables,
suppositions on unknown framing constraints, can they not?"* Today the
system answers only over what the library already contains: a person
may **select** a statement but never **supply** a premise, so every
question that turns on an unstated assumption ends in refusal rather
than in a conditional answer.

GUEST AXIOM turns the supposition frame **inbound**. A person supplies
a hypothesis the library does not contain; the system serves a
**machine-checked implication** — *if what you assumed holds, this
follows* — with the guest hypothesis named, undischarged, and
explicitly not believed; or it refuses in a typed way. The human
capability: ignorance about a premise becomes an answer conditioned on
that premise, checkable by a stranger, that can never be mistaken for a
claim the system endorses.

**Not greenfield — the frame is built and served.** The verification
this design needs is already load-bearing in the tree:
`scripts/supposition.py:89-118` opens a `FrameExecutor` with
`on_exit="conjectured"` — the honesty guarantee that anything leaving a
supposition frame leaves as conjecture — and
`scripts/serve_chat.py:158-176` freezes a `conditional` answer status
that is **deliberately absent from `ANSWERING_STATUSES`**, so a
conditional answer scores **zero** useful throughput tokens by
construction (the incentive that would corrupt it is removed, not
policed). What does not exist is the frame turned inbound: a
person-supplied hypothesis, elaborated and checked, driving a served
implication. This design builds only that.

## 2. Why this direction, over the metric leader (orchestrator ruling)

Series 3 ranked NO-FLIP first on information-per-effort and **flagged
its own ranking** as the place a maintainer whose purpose is the
conversation would overrule it. The overrule is taken, on grounds
recorded so it is a decision and not a preference:

- **NO-FLIP measured its own emptiness in advance.** This cycle's R3
  rider proved **zero** library growth over the recorded-journal
  window (digest-identical corpora), so NO-FLIP's improvement channel
  is dead this cycle by its own B8, and its surviving regression half
  substantially re-runs the erratum probe R3 already shipped. Its
  named residual risk concedes the comparator may not see the one
  instability class a person would notice. It parks as **rider R-NF**
  (the regression census is a day, red-capable, and inherits a
  sensitivity-proven detector for the erratum lane's future).
- **GUEST AXIOM can run this cycle.** The referee's decisive finding:
  scoped to the **2,313** statements that round-trip through the
  verified English voice, it needs no intake this design does not
  have — the person supplies a hypothesis *about* a statement the
  voice can already speak. Only hypotheses whose pieces are nameless
  wait for ECHO or HANDLEBAR, and those are pilot-deferred, not
  blocking.
- **It is the goal.** Three cycles of plain-conversation work
  (v0.20's design, v0.21's failed proposer and served session ledger)
  were scaffolding for exactly this object. Choosing evidence over it
  a fourth time would be the focus-attrition the release drift audit
  exists to catch.

The other series' leads are scheduled or parked, not discarded (§8):
**ECHO** (is the served voice injective?) rides as **item 2** — it is
cheap, runs on committed instruments, and its collision result
directly licenses GUEST AXIOM's clarify-vs-conditional rule.
**STRANGER-GATE** (the write gate's overdue adversarial red-team,
discharging the standing prohibition) parks as a **v0.24
incumbent-candidate with a prohibition trigger**: it must run before
any untrusted stream reaches the gate, and nothing this cycle opens
one. **HANDBACK** (typed non-answer turns emitting an admitted-command
separator or unlock) parks as the rider that upgrades GUEST AXIOM's
decision rule next cycle. The three standing incumbent-candidates
(PREMISE LEDGER, CANARY-CURVE, TOLL) and the naming-layer question both
v0.22 censuses forced carry to the v0.24 course unchanged; PREMISE
LEDGER's necessity claim is explicitly **not** taken here — this design
claims premise **consumption** only.

## 3. The one new first-class object

`experiments/guest_dispositions.json` — append-only, one record per
sealed hypothesis:

- `hypothesis_id` · `source_stratum` ∈ {`recorded_question`,
  `maintainer_correction`, `nameless_probe`} · `hypothesis_text`
  (verbatim) · `hypothesis_normal_form` (the supposition atomizer's
  output — `supposition._atom`, inherited, negation-marker only) ·
  `target_statement_id` (the round-trippable statement the hypothesis
  is about; null only in the `nameless_probe` stratum)
- `disposition` ∈ {`CONDITIONAL`, `CLARIFY`, `REFUTED`,
  `GUEST_UNELABORABLE`, `GUEST_UNCONSUMED`, `GUEST_UNNAMED_PIECES`}
- `library_digest_before` · `library_digest_after` (the write-gate
  working-tree digest over `data/`, scoped and recomputed per session
  — the quarantine witness)
- `implication` (for `CONDITIONAL`: the served `guest → consequent`
  term, the guest hypothesis undischarged) · `consumed` (bool — the
  hypothesis appears in the checked term; a vacuous implication is
  refused `GUEST_UNCONSUMED`, never served) · `checker_invocation_digest`
  · `countermodel_ref` (for `REFUTED`)
- `receipt` (the served object; a `conditional`-status answer per the
  frozen wire schema, scoring zero throughput tokens)

## 4. Trusted and untrusted components

Trusted, review-carried: the supposition frame and its `on_exit`
quarantine, the atomizer, the external checker (pinned, by path, never
downloaded), the implication builder, the digest witness. Untrusted:
**the guest hypothesis text itself** — it is a person's untrusted
input, and the entire safety claim is that it can enter a *frame* and
drive a *checked implication* without ever entering the committed
library. No learned component appears in this slice; the person types,
exact code elaborates and checks. (When ECHO/HANDLEBAR intake later
lets a person name nameless pieces, that intake is the incumbent
plain-input proposer's territory, quarantined as it already is —
out of scope here.)

## 5. Construction prerequisites

- **G-P0 — the sealed hypothesis set, 50 hypotheses** (review
  G3-followup: the person-wrong control needs 20 real corrections for
  power, so the set is 30 + 20, not 40). Committed before any
  elaboration runs: the **30** recorded natural questions
  (`experiments/plain_question_set.json`) recast as hypotheses about
  their round-trippable targets, plus **20** sampled from the parked
  two-way-correction lane's real maintainer corrections
  (externally-sourced, not author-invented — the denominator-provenance
  constraint; these 20 are also §7's person-wrong sample). Every
  non-`nameless_probe` hypothesis's target must be in the 2,313
  round-trippable set; a hypothesis whose target is not is either
  recast or moved to the `nameless_probe` stratum. Sealed with a
  drawing rule committed before the draw.
- **G-P1 — the quarantine harness.** The digest-before/after machinery
  proven to fire: a deliberately-writing control session must move the
  digest and be caught, before any real guest session runs (the v0.21
  session-ledger B-control precedent — a fence that cannot catch a
  planted write is no fence).

## 6. Construction gate (numbers frozen now)

- **B1 — quarantine, part structural and part checked, stated as such
  (review G4).** `library_digest_before == library_digest_after`
  (`write_stage.durable_digest(data/)`, `scripts/write_stage.py:422` —
  the exact callable the session ledger and erratum probe already pin)
  for **100%** of the 50 guest sessions; a single mismatch fails the
  lane and is published as a containment defect. *What is structural:*
  the frame path itself is a pure in-memory evaluator — `FrameExecutor`
  (`scripts/frames.py:317-376`) has no `data/` write path — so the
  supposition frame **cannot** write by construction, and
  `on_exit="conjectured"` additionally keeps any escaped frame output
  out of the write-gate statuses (`serve_chat.py:163`) as
  defence-in-depth. *What is only checked:* the un-built implication
  builder, the checker invocation, and the `guest_dispositions.json`
  writer are protected by B1's per-session digest, **not** structurally
  prevented from touching `data/` — B1 proves they did not, run by run,
  and a mismatch is exactly the defect it exists to catch. The digest
  check can go red; that is why it is the gate and not a comment.
- **B2 — the fence works (G-P1).** The planted-write control session
  moves the digest and is caught, 1/1. *Meetable:* the write path's
  own digest machinery is committed and tested.
- **B3 — elaboration floor over the restricted population, with a
  minimum denominator (review G5).** Of the 50 minus the
  `nameless_probe` stratum, **≥40%** reach a checker verdict
  (`CONDITIONAL` or `REFUTED`) — **and** that restricted population must
  itself be ≥ **15** hypotheses, or the lane reports the recast-yield
  census as its finding rather than a rate over a tiny remainder (the
  30 recorded questions include 9 authored to exhaust, so the recast
  yield into the 2,313 is not assumed). *Meetability argument, required
  at registration:* the targets round-trip through the voice, so their
  terms elaborate under the pinned checker today; 40% allows for
  hypotheses that atomize but do not consume, and both numbers are
  re-frozen from a pilot (G-P0's first 10 recast questions, committed before the floor
  freezes) that prices the real rate **and** the recast yield, by dated
  amendment before the remaining 30 run.
- **B4 — no vacuous implication served.** Every `CONDITIONAL` record
  has `consumed == true` (the guest hypothesis appears in the checked
  term); a hypothesis that elaborates but is not consumed is refused
  `GUEST_UNCONSUMED`. *Meetable:* consumption is a structural check on
  the term, decided by exact code.
- **B5 — the decision rule, frozen.** `CLARIFY` when a separator is
  expressible (an admitted command distinguishes the rival readings —
  ECHO/HANDBACK's object; **pilot-deferred** since neither ships this
  cycle, so the frozen fallback is **always-conditional, never-ask**,
  and the contrast is itself a recorded finding); `CONDITIONAL` when no
  separator but the hypothesis elaborates and is consumed; typed
  refusal when neither. B5's ask-arm is scored only if ECHO's collision
  result licenses it (§8).
- **B6 — the nameless stratum is exploratory.** The `nameless_probe`
  hypotheses (targets outside the 2,313) carry **no floor**; their
  elaboration rate is reported whatever it is, and the modal outcome
  `GUEST_UNNAMED_PIECES` is a scored honest result, not a gap — it is
  the nameless-library finding reaching the intake channel.
- **B7 — person-wrong, the sharp disposition.** A `maintainer_correction`
  hypothesis asserting a served answer is wrong is an inbound
  supposition; `REFUTED` emits a checker countermodel as the artifact
  (the system telling a person they are wrong, with proof). Scored
  against the checker's verdict, never against the objector's claim.

## 7. Blind control and voiding sentence

The **person-wrong control** is the capability-blind arm: sham
objections — well-formed, uncited, derived from no served answer —
drawn from the same grammar, run through the same adjudicator, reusing
the session-ledger mutation controls (sham/uncited must move nothing).

**Frozen voiding sentence, mechanically evaluable (review G3).** The
person-wrong arm scores **20 real maintainer corrections** (G-P0 draws
20, not 10, from the parked two-way lane's log — the sample is enlarged
precisely so this test has power) against **20 sham objections**
(well-formed, uncited, derived from no served answer). *If a
two-sample test over the {REFUTED, CONDITIONAL, refused} partition
fails to reject the null that the two distributions are equal at
**α = 0.05** — the value is frozen here, not deferred — the adjudicator
is not demonstrably reading content over form, and the person-wrong
claim is UNDERPOWERED, not made, this cycle.* Distinguish the two
failure modes rather than collapsing them: a test that cannot reject
with n=20 each is `UNDERPOWERED` (the claim waits); a **perfect**
control score — shams `REFUTED` at the real corrections' rate — is a
positive void (the adjudicator refutes on shape, and its refutations of
real corrections certify nothing). Underpower does not void the other
dispositions; it withholds only the person-wrong claim.

Cheapest capability-blind baseline for the whole lane: a
frame-free arm that serves every guest hypothesis as an unconditional
answer (no quarantine, no implication). It must FAIL B1 (it writes) and
its served answers must be indistinguishable from noise under B4 — if
it passes anything, the conditional discipline bought nothing and the
run publishes that.

## 7a. Result gate — the sentence each disposition licenses (review G1)

The construction gate above proves the instrument sound; this gate says
what a reader may conclude from a committed record, and nothing wider:

- **R-G.CONDITIONAL** — a `CONDITIONAL` record with `consumed == true`,
  B1 held for its session, and a checker-returned implication licenses
  exactly: *"if the named guest hypothesis holds, the consequent
  follows."* It licenses no claim that the hypothesis holds, that the
  consequent is a library fact, or that the premise was necessary.
- **R-G.REFUTED** — licenses: *"the checker exhibits a countermodel to
  your objection,"* with the countermodel as the artifact. It licenses
  no claim about the objector's sincerity or competence, and it is
  withheld entirely if §7's person-wrong control is `UNDERPOWERED` or
  void.
- **R-G.CLARIFY** — licenses nothing this cycle; it is ECHO-gated
  (§8) and inert until item 2's collision result lands (§6 B5, §3's
  `CLARIFY` enum value is present for the schema but unreachable under
  the frozen never-ask fallback — review G6).
- **R-G refusals** — the typed refusals (`GUEST_UNELABORABLE`,
  `GUEST_UNCONSUMED`, `GUEST_UNNAMED_PIECES`) license the honest
  negative each names, and `GUEST_UNNAMED_PIECES` over the nameless
  stratum is the v0.22 nameless-library finding reaching the intake
  channel — a first-class result, not a gap.

**Residual risk the gate does not price (review G2).** Two, named and
unpriced. (1) **Authorship provenance:** G-P0 recasts 30
maintainer-authored questions (`plain_question_set.json`, whose own
header warns *"questions a maintainer wrote about this corpus are not
questions a stranger asks"*), so the hypotheses are the maintainer's,
not a stranger's — the same authorship contamination HANDLES named and
left unpriced. The 20 real maintainer corrections narrow it (they were
authored against served answers, not invented for this test) but do not
remove it; a stranger's guest hypotheses are the unmeasured population.
(2) **Ontology-shared closed world:** GUEST AXIOM elaborates over the
same voice and checker ECHO does, so it inherits ECHO's §7 risk — a
hypothesis elaborates because its pieces live in the same ~8,500-term
universe the renderer ranges over, and nothing here prices whether a
hypothesis phrased in a stranger's terms would elaborate at all. The
gate measures whether a *supplied, expressible* hypothesis yields a
checked implication; it does not measure whether a person's actual
assumption is expressible, and this design says so rather than pricing
it with an instrument that does not exist.

## 8. Stop conditions and non-claims

Stop conditions: B1 or B2 failure halts before real sessions (a fence
that leaks or cannot catch a write); any B5 ask-arm scoring without
ECHO's licensing collision result (item 2 gates it); the pilot reading
below 40% freezes the floor lower **or** stops with the elaboration
census as the finding. Non-claims: no claim the guest hypothesis is
**true** (it is named, undischarged, not believed); no claim of premise
**necessity** (PREMISE LEDGER's, incumbent — consumption only here); no
coverage over the nameless majority (its stratum is exploratory); no
prose-understanding claim (the atomizer is negation-marker only, its
self-limitation inherited); no person-satisfaction claim; the guest
text never enters the committed library and B1 is the proof.

**ECHO as item 2, and the composition.** ECHO (`docs/DESIGN-echo.md`,
this cycle's item 2) asks whether the served English voice is
**injective** — does a sentence determine the statement it came from,
adjudicated by the checker, with a collision table published
falsification-only. Its result licenses GUEST AXIOM's B5 ask-arm: where
ECHO shows injectivity, a sentence is a machine-decided binding and no
clarify is needed; where it shows **collisions**, the clarify arm is
exactly the right instrument for the colliding stratum, and ECHO hands
GUEST AXIOM a machine-sealed target population instead of an
author-chosen one. ECHO runs first; GUEST AXIOM's ask-arm is scored on
its result.

## 9. The suspended habit

Suspended for this cycle, scoped to the guest-hypothesis path only: the
rule that the system answers only over committed material. B1 is the
fence — the library is byte-identical before and after every guest
session, so "answers only over committed material" holds for the
*committed library* while the *served answer* may be conditioned on a
guest premise that is not in it. The suspension ends at the v0.23 gate
by that gate's verdicts.

## 10. Where status lands

ROADMAP-v0.23: item 1 this design + G-P0/G-P1; item 2 ECHO (its own
gate, licensing B5); riders R-NF (NO-FLIP regression census) and
HANDBACK (the separator object for next cycle's decision rule);
STRANGER-GATE parked with its prohibition trigger; the three standing
incumbent-candidates and the naming-layer question carried to the v0.24
course; the supplementary-family PREMISE LEDGER's necessity claim
recorded as the successor to this design's consumption-only scope.
ANALYSIS gets the registered run's numbers; DISCOVERIES gets the
clarify-vs-conditional decision if ECHO's collisions settle it; BACKLOG
gets the parks. The course receipt carries the full funnel and all
three series' leads.
