> **CLOSED at v0.23.0.** This plan is the historical plan-of-record; it is not
> edited except for this banner. The headline was a construction census that
> returned a finding rather than an inbound implication, adjudicated against
> a stop clause frozen before the draw. Where each item went:
>
> - **§1 GUEST AXIOM** → **RELEASE-v0.23.0** headline. G-P0 recast yield
>   **0/21** into the 2,313; person-wrong **BLOCKED_NO_LOG**; no fifty
>   sessions; no `guest_dispositions.json`. B3's alternative fired. Unpark
>   conditions → [ROADMAP-v0.24](ROADMAP-v0.24.md) §2 and BACKLOG.
> - **§1 G-P1** → **SHIPPED.** Planted write caught 1/1 on a throwaway tree.
> - **§2 ECHO** → **RELEASE-v0.23.0**. Construction stop: native 8,584 /
>   second 2,313 / overlap 0; B3/B4 miss on native; **0/50** and **0/500**
>   rendered. No collision result. Native-instrument amendment → v0.24 §2.
> - **§3 R-NF** → **SHIPPED.** 0/220 rendered-answer digest regressions;
>   controls 2/2, 0/2, 2/2+220/220.
> - **§3 HANDBACK** → **PARKED** for v0.24 (BACKLOG). Always-conditional
>   never-ask is the recorded B5 fallback.
> - **PROTOCOL UPTAKE** → reviewed design, **ROADMAP-v0.24** incumbent
>   against STRANGER-GATE; not implemented this cycle.
> - **Release gate `[SUITE-GATE-V23]`** → **closed**: run 1 red at
>   `5984f27` (stale CR-P0 seal + verbose log in `working_tree_digest`);
>   run 2 green at `867ad5c` (2,852 OK, skipped=5, 9 h 4 m; receipts
>   `reports/test_gate_v023/`). RELEASE-v0.23.0 carries the verdict.
>
> Session-level GUEST AXIOM gates did not run and are not claimed.

# Roadmap v0.23 — the person supplies the premise, and the answer is an honest if-then

v0.22 registered two censuses and both came back findings rather than
capabilities. The library is **nameless** — 417 of 12,777 statements carry a
handle a person could type — and its evidence is **program-bound** — 1 of 19
receipt kinds survives the program's deletion. The sharpest sentence of the
cycle was the overlay: of the 9,048 statements the engine can consume in one
step, **125** carry a name a person could type. The library computes far more
than anyone can ask it for. (The 125 *carry* handles; nothing is claimed
reachable in service.)

For four cycles the project has built scaffolding toward one goal the maintainer
wrote down long ago: a plain conversation, where a person supplies an assumption
the library does not contain and gets an honest answer under it. v0.20 designed
the supposition frame; v0.21 served a session that remembers its suppositions
and failed a proposer that reads plain questions; v0.22 measured why the
proposer starved. This cycle builds the object those three were scaffolding for.

**It does not need names.** GUEST AXIOM turns the supposition frame *inbound* on
the 2,313 statements the voice can already speak — the part of the library that
does have something to say its own name with — so the nameless finding is what
clears its path rather than what blocks it.

## 1. Headline — THE GUEST AXIOM: an answer under an assumption the library lacks

[DESIGN-guest-axiom](DESIGN-guest-axiom.md) is the v0.23 course's selection
(receipt: `reports/design-direction-v0.23.json`). It is the maintainer's own
standing question — *"something can be predicated on assumptions, true or false,
and be verifiable under that pretext… hidden variables, suppositions on unknown
framing constraints"* — arrived at independently by the course's third series.

**The boundary being moved.** Today a person may **select** a statement the
library holds but never **supply** a premise it lacks, so every question turning
on an unstated assumption ends in refusal. GUEST AXIOM would serve a
**machine-checked implication** instead — *if what you assumed holds, this
follows* — with the guest hypothesis named, undischarged, and explicitly **not
believed**; or a typed refusal.

**SHIPPED as the recast-yield finding (2026-08-29), not as that implication.**
B3 already licensed the alternative: if the restricted population is below 15,
the lane reports the recast-yield census rather than a rate. G-P0 measured
**0 of 21** non-exhaust questions landing in the voice's 2,313 covered set;
person-wrong is **BLOCKED_NO_LOG**; ECHO stopped before the pilot, so B5's
ask-arm is unlicensed. No `guest_dispositions.json`, no 50 sessions, no
elaboration floor, no person-wrong score. The implication object does not
exist. The census is the result. Unpark needs a question set whose targets
actually sit in the 2,313 (or a dated amendment of the target constructor)
and an externally-sourced correction log whose commit is an ancestor of a
later draw.

**Not greenfield.** The frame is built and served: `scripts/supposition.py`
opens a `FrameExecutor` with `on_exit="conjectured"` (anything leaving a
supposition frame leaves as conjecture), and `scripts/serve_chat.py` freezes a
`conditional` status **outside** `ANSWERING_STATUSES`, so a conditional answer
scores zero useful throughput tokens by construction — the incentive that would
corrupt it is removed, not policed. What does not exist is the frame turned
inbound. This cycle measured why that inbound turn could not start on the
sealed question set it inherited.

### 1.1 Why this direction, over the metric leader — recorded as a decision

Series 3 ranked **NO-FLIP** first on information-per-effort and **flagged its own
ranking** as the point a maintainer whose purpose is the conversation would
overrule it. The overrule is taken, on grounds recorded in
`DESIGN-guest-axiom` §2 so it is a decision and not a preference:

- **NO-FLIP measured its own emptiness in advance.** This cycle's R3 rider
  proved **zero** library growth over the recorded-journal window
  (digest-identical corpora), so NO-FLIP's improvement channel is dead this
  cycle by its own logic, and its surviving regression half substantially
  re-runs the erratum probe R3 already shipped.
- **GUEST AXIOM can run this cycle.** Scoped to the **2,313** round-trippable
  statements, it needs no intake this design lacks — the person supplies a
  hypothesis *about* a statement the voice can already speak.
- **It is the goal.** Declining the plain-conversation object a fourth cycle
  would be the focus-attrition the drift audit exists to catch.

The NO-FLIP ranking becomes rider **R-NF** (§3), not a discard.

### 1.2 Construction prerequisites, ordered before any elaboration

- **G-P0 — SHIPPED as the recast-yield census (2026-08-29).** Drawing rule
  committed first (`experiments/guest_axiom_draw_rule.json`). The draw
  (`experiments/guest_hypotheses.json`) recast all 30 sealed questions by
  exact membership in the voice's 2,313 covered set: **0 of 21** non-exhaust
  questions named a unique covered id (the sealed `why` fields name curated-
  library ids the voice register blocks or never accepted). The 20 person-wrong
  corrections are **BLOCKED_NO_LOG** — `experiments/crossing_corrections.json`
  is absent; the rule predicted that and forbade inventing the pool. B3's
  restricted population is 0 (<15), so this cycle's recorded-question arm is
  the yield census, not a 40% floor over a remainder.
- **G-P1 — SHIPPED (2026-08-29).** `scripts/guest_quarantine.py` plants a
  write under a throwaway `data/` tree; `write_stage.durable_digest` moves
  and the plant is caught 1/1 (`tests/test_guest_quarantine.py`). The real
  repository `data/` is not the plant target. Real guest sessions still
  have not run.

### 1.3 The slice, the gate, the person-wrong disposition

**One new first-class object**: `experiments/guest_dispositions.json`, one record
per sealed hypothesis, `disposition` ∈ {`CONDITIONAL`, `CLARIFY`, `REFUTED`,
`GUEST_UNELABORABLE`, `GUEST_UNCONSUMED`, `GUEST_UNNAMED_PIECES`}, each with the
library digest before and after (the quarantine witness), the served implication
term, a `consumed` flag, and the checker invocation digest.

**The gate (numbers frozen in `DESIGN-guest-axiom` §6):**

- **B1 — quarantine, structural and checked.** `library_digest_before ==
  library_digest_after` for **100%** of the 50 sessions; one mismatch fails the
  lane as a containment defect. The frame path is a pure in-memory evaluator
  with no `data/` write path (structural); the implication builder, checker
  invocation and writer are protected by the per-session digest (checked). The
  digest check can go red — that is why it is the gate and not a comment.
- **B3 — elaboration floor over the restricted population.** ≥40% of the
  non-`nameless_probe` hypotheses reach a checker verdict, **and** that
  population is itself ≥15, or the lane reports the recast-yield census as its
  finding. Both numbers re-frozen from a 10-hypothesis pilot by dated amendment
  before the remaining 30 run (the 30 recorded questions include 9 authored to
  exhaust, so the recast yield is not assumed).
- **B4 — no vacuous implication served.** Every `CONDITIONAL` has
  `consumed == true`; a hypothesis that elaborates but is not consumed is refused
  `GUEST_UNCONSUMED`.
- **B7 — person-wrong, the sharp disposition.** A `maintainer_correction`
  hypothesis asserting a served answer is wrong is an inbound supposition;
  `REFUTED` emits a checker **countermodel** as the artifact — the system
  telling a person they are wrong, with proof. Scored against the checker's
  verdict, never against the objector's claim.

**The person-wrong control and voiding sentence (§7).** The person-wrong arm
scores **20 real maintainer corrections** against **20 sham objections**
(well-formed, uncited, derived from no served answer). If a two-sample test over
the {REFUTED, CONDITIONAL, refused} partition fails to reject the null that the
two distributions are equal at **α = 0.05** (frozen here, not deferred), the
adjudicator is not demonstrably reading content over form and the person-wrong
claim is **UNDERPOWERED, not made, this cycle**. A **perfect** control score —
shams REFUTED at the real corrections' rate — is a **positive void**: the
adjudicator refutes on shape. Underpower withholds only the person-wrong claim,
not the other dispositions.

**Result gate R-G**, per §7a, licenses one sentence per disposition and nothing
wider: a `CONDITIONAL` licenses *"if the named guest hypothesis holds, the
consequent follows"* — never that the hypothesis holds, that the consequent is a
library fact, or that the premise was necessary. **Premise necessity is not
claimed** (that is PREMISE LEDGER's, the incumbent-candidate — §4); this design
claims premise **consumption** only.

### 1.4 Stop conditions and non-claims

Stop if B1 or B2 fails (a fence that leaks or cannot catch a write) before real
sessions; if any B5 ask-arm scores without ECHO's licensing collision result; if
the pilot reads below 40% (freeze the floor lower **or** stop with the
elaboration census as the finding). Non-claims: no claim the guest hypothesis is
**true**; no premise-necessity claim; no coverage over the nameless majority
(its `nameless_probe` stratum is exploratory, and `GUEST_UNNAMED_PIECES` over it
is the v0.22 nameless-library finding reaching the intake channel — a scored
result, not a gap); no prose-understanding claim (the atomizer is
negation-marker only); the guest text never enters the committed library and B1
is the proof.

## 2. Item 2 — ECHO: STOPPED at construction before the pilot

[DESIGN-echo](DESIGN-echo.md) is series 1's lead, scheduled **before** item 1
because its collision result licenses GUEST AXIOM's clarify-vs-conditional B5
rule, it runs entirely on committed instruments, and its blind control is
already known to be hostile.

**The boundary.** The system can **speak** — verified English renderings gated by
an exact round trip — but has never checked that what it says **determines what
it meant**. ECHO hands each served sentence to a reader and asks whether the
source statement is reconstructed, the external checker adjudicating identity.

**The honest bound, stated on the page (review E1).** There is **no committed
sentence→term path that is not the renderer's own inverse** `delexicalize`;
pointing that path back at a sentence would be a checker validating its own
output — the arc's signature defect. So ECHO draws disjointness where it holds:

- **B3 — identity is checker-adjudicated.** `RECOVERED` may be set only by the
  external pinned checker, which shares no code with the renderer. This is the
  disjointness that matters for the truth of an identity verdict.
- **B4 — the reparser is newly authored, and honest about what that buys.**
  `scripts/echo_reparse.py` is a from-scratch longest-match table reader over the
  committed lexicon, importing neither `render` nor `delexicalize`; its import
  closure must be disjoint from the render/inverse pair or the run voids before
  rendering. It is **import-disjoint but not algorithmically independent** —
  because the committed lexicon is bijective, any faithful table inverse produces
  `delexicalize`'s token string. So `RECOVERED` is **bounded by lexicon
  bijectivity** and *guarded, not proven,* by the scramble arm.

**The robust half does not depend on the reparser at all.** The collision finding
(B6) — *do distinct statements render to identical sentences?* — is computed from
`render` plus the external checker's identity obligation, never from
`echo_reparse`. Collisions license item 1's **clarify** disposition and hand
GUEST AXIOM a machine-sealed colliding population instead of an author-chosen
one, regardless of the reparser's dependence.

**Blind control and voiding sentence.** The scramble arm permutes tokens within a
sentence, preserving the multiset (glossary tokens survive, order dies). Known
hostile: v0.20's machine-blind-reader control already measured that scrambled
sentences leak structure. If scramble recovery ≥ real recovery at equal or
greater checker time, the reader is riding surviving glossary tokens and **the
echo claim is void**. Separation below the pilot-frozen margin M is
`UNDERPOWERED`, not a pass.

**Result gate R-E**: the injectivity sentence is licensed only for a stratum
where the real arm beats the null by ≥M, beats scramble, and reports its
collisions. A collision-bearing stratum licenses **no** injectivity sentence — it
licenses item 1's clarify disposition. **Non-claims:** no reader-*meaning* claim
(that stayed voided in v0.21 — injectivity is not comprehension); no universal
injectivity; no rate is a capability; the renderer and reader are code-disjoint
but **ontology-shared**, searching a closed ~8,500-term universe, so ECHO can
clear every clause and license nothing about a stranger — the decoy-population
arm is a stated hole with no generator, priced by naming it.

**SHIPPED as a construction finding (2026-08-28).** The preregistration and
instruments landed before the once-only audit. The observed population matched
the frozen prediction exactly: native **8,584**, second voice **2,313**, overlap
**0**, union-of-the-two-sets **10,897**, with the resolver's **13 question
fixtures reported separately**. B1 fires. B3 and B4 miss on the native stratum:
its identity gate is the repository-authored matcher parser, not an external
checker, and its reader is its renderer (the same five-module closure). The
second voice alone has both a live external Lean adjudicator and an
import-disjoint reader. The gate therefore reads **STOP_BEFORE_PILOT**;
**0/50** pilot items and **0/500** registered items were rendered. No recovery,
scramble, collision, or injectivity result exists. Item 1's ECHO-dependent ask
arm remains unlicensed.

## 3. Riders — two, each with a floor and a stop rule

**R-NF — SHIPPED (2026-08-29).** **0/220** rendered-answer digest
regressions over the recorded answering turns
(`experiments/no_flip_census.json`). Controls: exact 2/2, shape-only 0/2,
always-changed 2/2 plants and 220/220 false positives on self-pairs.
Answer-loss class empty. Two live pins moved and are disclosed. Zero is
published as B7 requires, never as “answers cannot regress.”

**R-HANDBACK — PARKED for v0.24 (2026-08-29).** Typed non-answer turns would
emit an admitted-command separator or unlock (the fold of TWO-KEY BIND and
WANT-LIST). It was never a v0.23 capability: with ECHO stopped before the
pilot, GUEST AXIOM's B5 fallback is frozen **always-conditional, never-ask**,
and that contrast is the recorded finding. HANDBACK unparks when GUEST AXIOM
has a restricted population ≥15 **and** a collision or separator result
licenses the ask-arm.

## 4. Carried, with dependants named

The rule, unchanged: **every carried lane names its dependant, or it parks.**

### 4.1 Discharged by v0.22 — closed, not carried

| lane (ROADMAP-v0.22) | outcome |
|---|---|
| **§1 HANDLES / H-P0** | **SHIPPED as the census; §9 stop clause FIRED.** The nameless finding is the result. Closed as an item; the naming-layer question carries below |
| **§2 COLD RECEIPT design + census** | **SHIPPED**, reviewed before the slice; 1/10/8 partition, all B1–B11 green. Closed |
| **§3 R1 ONE STEP** | **SHIPPED.** Statement limb 45× floor; question limb DEFERRED (Q60 unsealed). Lane-opening decision carries below |
| **§3 R3 ERRATUM** | **SHIPPED.** 0 real flips, plant 1/1, zero-growth window. R3's v0.23 candidacy decided by the count: folded into R-NF, not re-run |
| **§4.0 relaxations** | **EXERCISED again** (bug-not-result twice; §5). Standing as rules |

### 4.2 Carried with a named dependant — these are prerequisites

| lane | named dependant | disposition |
|---|---|---|
| **G-P0 / G-P1** | **§1 — this cycle** | **both SHIPPED, and they are the item.** G-P0 is the recast-yield census (0/21 into the 2,313; correction arm BLOCKED_NO_LOG). G-P1's planted write is caught 1/1. No guest sessions. B5 remains unlicensed |
| **ECHO's collision result** | **§1's B5 ask-arm** | **UNAVAILABLE: construction stop.** ECHO rendered 0 pilot and 0 registered items; no collision result exists. Unpark only after the dated amendment named in DESIGN-echo §8 |

### 4.3 Parked, with triggers

| lane | trigger to unpark |
|---|---|
| **The naming-layer question** — *how does a nameless library get names a person can ask by?* | **The NEW first-class carried lane both v0.22 censuses forced.** Carries to the **v0.24 course** unchanged. Candidate material named, not chosen: name-derivation from the verified English renderings the voice serves; the S3 term store priced at ~223.5 s batched over 2,313 covered statements (`experiments/handles_census.json`, `s3_price`). HANDLEBAR parks behind it |
| **STRANGER-GATE** — the write gate's overdue adversarial red-team | **v0.24 incumbent-candidate with a PROHIBITION trigger**: it MUST run before any untrusted stream reaches the write gate, and nothing this cycle opens one (GUEST AXIOM's guest text enters a *frame*, never the gate — B1 is the proof). Its residual risk is recorded: one head authors the attacks, the twins and the gate, so it measures whether the gate DISCRIMINATES, never whether the corpus is ADEQUATE |
| **ORPHAN** — receipts that outlive the program | **Parked as the cold-census's own recorded next question** (which single pinned dependency converts the most NEEDS-PROGRAM kinds), series-1 runner-up. **It unparks TOLL's n=1 denominator** — the shift the v0.22 drift audit named: the cost lane's metrology now has both an instrument (§2's harness) and a denominator path (ORPHAN) |
| **PREMISE LEDGER** (supplementary-family) | **v0.23 incumbent-candidate, capability-class**, the successor to GUEST AXIOM's consumption-only scope — receipts certifying assumption *necessity* by per-premise countermodels. Carries to the **v0.24 course** unchanged; its necessity claim is explicitly **not** taken this cycle. LOADBEARING folded into it (independent convergence = evidence for it) |
| **CANARY-CURVE** and **TOLL** | **v0.23 incumbent-candidates, instrument-class**, carry to the **v0.24 course** unchanged. CANARY-CURVE measures growth after the enumeration layer exists; TOLL is the cost lane's metrology, now with a re-check instrument (§2) and ORPHAN's denominator path. CEILING routes with TOLL |
| **SELF-SEED** | Parked: the commit half of the parked derivations lane, with the novelty verdict the park lacked; seeds mechanically drawn, the maintainer may not pick. Unpark when a cycle wants provenance-typed growth by proof |
| **UPSTREAM-PATCH** | Parked: the give-back direction — program-free defect reproducers to reviewed upstream — capped at UNTESTED by the outside-participation constraint (a receipt whose adjudicator is a third party the repository cannot pin). Parked with its license discipline |
| **FOREIGN-SEAM** | **Cut, cut defended**: cross-assistant alignment language exceeds one cycle, and within-ecosystem divergence is ingestion in a seam costume. The honest residue is a **feasibility spike**, parked as such — no instrument is claimed |
| **HANDLEBAR** — reach-by-hole-term | Parked behind the naming-layer question its shuffle limb would have probed. Its shuffle limb was a candidate rider; parked with the lane it depends on |
| **DEMAND** — an obstruction ledger against an externally-sourced question distribution | **Parked, now with TRIPLE convergence.** The v0.22 supplementary series' programme-level blind spot (no prospectively sampled, externally sourced task distribution) was convergent evidence for it; the v0.23 course's **STRANGER'S EXAM folds into it as its calibration upgrade — the third independent arrival** (`reports/design-direction-v0.23.json`, `outcomes.series_1.folds`). Unpark needs a population of askers this repository did not author; still the missing-population problem behind STRANGER and C-V3 |
| **The resolver's pre-emptive binding** (v0.21's G9, NOT MET) | Parked with its 13 committed fixtures; **no v0.23 headline item depends on it**, and GUEST AXIOM touches no resolver score. Unpark needs its own prereg, its own capability-blind control, and a K re-measurement. THE MEANING HANDSHAKE's `UNNAMED_SCOPE` typed refusal and person-confirmation-subsuming-resolver-pre-emption lessons are recorded against it in BACKLOG |
| **The `conform` route advertises the asker's numbers and does not use them** | Parked unchanged from ROADMAP-v0.22 §4.3, verified not-patched this cycle; two admissible discharges intact (consume the bindings with a served diff and control, or correct the sheet/example/docstring). No v0.23 headline item depends on it |
| **The G5-metric successor** | Parked with its rule written down. R-NF now scores regression by outcome (0/220). GUEST AXIOM's person-wrong arm is **unfilled** (`BLOCKED_NO_LOG`), not a scored refusal. Unpark when a proposer lane is scheduled again |
| **TWO WITNESSES + the independent second reading** (with the parked conformance successor) | Parked together as item-candidates; the **BOUNDED OMNISCIENCE × SPLIT-SEMANTICS** strengthened unpark formulation from the v0.22 supplementary series stands, TWO JUDGES behind it. Fragment growth alone does not unpark WITNESS — the divergent class is reachable but non-linear |
| **The cost ledger** (answers per joule and per dollar) | **SEVENTH cycle parked**, counting basis unchanged (rotations since `DESIGN-grounded-throughput` §10: v0.17–v0.23). Still parked, still designing nothing for it this cycle — but its metrology **TOLL** now has an instrument (§2) and a denominator path (ORPHAN), which is the shift RELEASE-v0.22.0's drift audit records |
| **Ledger-first claims** (v0.17 course, gate L1–L13, hardened) — named dependant: ***none this cycle*** | **Seventh pass-over.** Trigger restored in wording: *it **became** a headline candidate the first cycle after the throughput readout* (a fired event at v0.17, receipt `reports/design-direction-v0.17.json`). v0.22 produced no throughput readout — `experiments/throughput_tasks.json` did not change at all. Load-bearing / premise-necessity travels with it and unparks with it |
| **Open-English input / the reverse-lexicon synonym layer** | **Parked, and the nameless finding is its definitive answer on the index side**: the lexicon the question would invert is the same glossary whose bulk (96.74% of the library) is boilerplate, so there is nothing to invert for it. The **mechanism** (inverting the lexicon) remains a distinct unanswered park; GUEST AXIOM works the 2,313-statement named remainder from the person's side. Folded under the naming-layer question |
| **Realization parameters as data** | Parked. Askable since v0.18 (R1 fired at 0.9991), never scheduled. Unpark needs a design saying what the parameters buy over the committed grammar |
| **The register's `mathlib_head` budget** | Parked (not "carried"): a resourcing decision, not a design one. `data/` did not move this cycle, so `blocked_total` 1,878 and `mathlib_head` 1,706 are byte-identical to v0.20/v0.21 |
| **HOSTILE DICTATION** | Parked with the prohibition trigger; STRANGER-GATE now carries the same prohibition explicitly and is the lane most likely to discharge it. The next lane to touch it owes a **shown** answer, not a stated one |
| **CROSSING, LONG CON, BITROT** | Parked unchanged (probes and stop rules recorded in ROADMAP-v0.22 §4.3) |
| **C-V3 (human) — the determinacy sheet; canonical-bracketing-load-bearing; STRANGER; UNSAY/RECALL; VERDICT, DEBT NOTES, COURIER, WORD OF HONOR (standalone probes, still unrun); ATLAS, ABSENCE, RATCHET, GRAFT, IF, TRANSPLANT, BORROWED PREMISES, and the v0.19/v0.20 catch-alls** | Parked unchanged with the triggers recorded in `reports/design-direction-v0.19/20/21/22.json`. IF's second reason stands (WITNESS's 0-of-6 is its empirical form); BORROWED PREMISES' next look is due now the supposition object has matured into GUEST AXIOM |

### 4.4 Early v0.24 input, not unparked

**PROTOCOL UPTAKE** is a design-only input to the v0.24 course, reviewed,
not scheduled, and displacing no incumbent. Its trigger is already observed:
the first ordinary turn through the shipped Codex-compatible surface treated
`hello` as an ungrounded proposition. [DESIGN-protocol-uptake](DESIGN-protocol-uptake.md)
specifies an honest (not force-balanced) context/corpus table whose
blind-control ceilings are computed from the U-P0 seal, a third served
profile `corollary/protocol`, the exact ASK boundary, bounded nested
resume, and a separately licensed Codex prompt-tool result. Execution
remains a separate parked design. The v0.24 course, not this fired
trigger, decides whether it outranks the incumbent queue.

### 4.5 New parks from the v0.23 course

Every declined direction carries its disposition, quoted from
`reports/design-direction-v0.23.json` and filed in [BACKLOG](BACKLOG.md):

| direction | disposition |
|---|---|
| **NO-FLIP** | metric leader, **overruled** → rider R-NF (regression half) |
| **TOMORROW'S DIFF** | folded → **NO-FLIP**, cut to the regression half (R3 measured zero growth, so the improvement channel is dead this cycle) |
| **AXIOM-BUDGET** | folded → **STRANGER-GATE** (the three-axiom PASS whitelist is the attack surface; a perimeter never attacked is the assertion that cannot go red) |
| **TWO-KEY BIND + WANT-LIST** | folded → **HANDBACK**, the rider |
| **THE OBJECTION SLOT** | folded → GUEST AXIOM's **person-wrong** disposition (REFUTED emits a countermodel) |
| **TWO READINGS** | folded → **ECHO** (voice read back, no person in loop) |
| **LOADBEARING** | folded → the **PREMISE LEDGER** incumbent (independent convergence) |
| **STRANGER'S EXAM** | folded → the parked **DEMAND** lane, third independent arrival |
| **STRANGER-GATE, ORPHAN, SELF-SEED, HANDLEBAR, UPSTREAM-PATCH, FOREIGN-SEAM** | parked (§4.3), each with its trigger |

## 5. Governance

- **The course gate was INVOKED strictly for the fifth consecutive cycle.**
  `reports/design-direction-v0.23.json` records three isolated series, three
  rounds each — **nine rounds, fifteen round-one directions, $2.99** — run
  headless from an empty non-git directory outside the repository under a strict
  tool denylist, isolation mode inherited unchanged from the v0.22 receipt. The
  brief is on file and hash-verified; `series_1.r1` equals the brief hash by
  construction. The v0.22 incumbent-candidates and the supplementary PREMISE
  LEDGER were disclosed at each round two, recorded in `exclusion_note`.

- **The v0.22 supplementary outside-family series carries its dispositions
  forward.** GPT-5.6-sol via codex produced **THE PREMISE LEDGER** (recorded as
  a v0.23 incumbent-candidate, capability-class), the **BOUNDED OMNISCIENCE ×
  SPLIT-SEMANTICS** strengthened conformance-successor formulation, and a
  programme-level blind spot — no prospectively sampled externally-sourced task
  distribution — that is **convergent evidence for the parked DEMAND direction**
  (§4.3). Nothing in the series contested the v0.22 incumbent.

- **Two censuses that returned findings are this cycle's evidence pattern.**
  v0.21 registered three outcomes with three verdicts; v0.22 registered two
  censuses and both came back findings against a frozen stop clause — the
  library is nameless, the evidence is program-bound. A published census is a
  result; a quiet descope is not. GUEST AXIOM inherits the shape: its floors are
  frozen before its instrument exists, and its pilot can stop the slice with the
  elaboration census as the finding.

- **§4.0's relaxations were exercised again, and audited.** Bug-not-result was
  used twice on the cold-receipt lane — the C-E3 supplement's removal arm was a
  provably-never-executed control (a bug, re-run under amendment 2), and the
  registry-half instance rule read `none` for two kinds holding thousands of
  instances. The line held: not once was a control that ran and read unfavourably
  repaired and re-run — the corrected two-limb arm read 1/10/8, and the honest
  number is smaller than run 1's, not larger.

- **The review gate binds the orchestrator, and both v0.23 designs are the
  evidence.** ECHO was falsified before landing — it claimed a code-disjoint
  reader the tree does not hold (there is no committed sentence→term path that is
  not the renderer's own inverse), and now builds one from scratch while stating
  on the page that it is import-disjoint but not algorithmically independent.
  GUEST AXIOM was falsified before landing — its draft lacked a result gate and a
  powered person-wrong control, both now frozen. This is the **second consecutive
  cycle** in which the selected designs failed their first review; a review gate
  that binds the measurements and not the person planning them has a hole in it,
  and this cycle closes it the only way it can be closed — an adversarial reader
  who checks the plan against the tree before it lands.

- **Headline selection remains part of the evidence trail.** When the v0.24
  course reports, its selection and every declined disposition are recorded in
  the roadmap, the receipt, and the release notes.

## Release gate

v0.23 is ready only if:

- **G-P0 and G-P1 are committed in order** (drawing rule, then draw, then
  planted-write control). **MET.** G-P0 sealed 30 recasts, **0/21** in the
  2,313, and **BLOCKED_NO_LOG** for the 20 person-wrong corrections. G-P1's
  planted write is caught 1/1. B3's licensed alternative fired: the
  recorded-question arm is that census, not a 40% floor.
- **B1's 50-session quarantine, the elaboration-pilot floor, person-wrong
  scoring, and the no-vacuous-CONDITIONAL clause did not run.** They are
  **not claimed**. There were no guest sessions. Publishing a 50/50
  quarantine over an empty remainder would be the rate-over-nothing B3
  exists to forbid. G-P1 remains the only executed fence (1/1, throwaway
  tree).
- **ECHO shipped before item 1 as a construction stop**, not as a collision
  result. Native B3/B4 miss; **0/50** and **0/500** rendered. No injectivity
  rate. Item 1's ask-arm stays unlicensed.
- **the guest hypothesis text never entered the committed library** — no
  guest session ran, and G-P1's plant is the fence that can go red. Not a
  50-session proof.
- **no premise-necessity claim, no prose-understanding claim, and no
  stranger-usability claim** is made anywhere; G-P0's authorship
  contamination travels with the 0/21.
- **R-NF shipped** 0/220 with hostile controls that can go red; **HANDBACK
  is parked** for v0.24 in writing.
- `check_report_regeneration.py` runs in the release refresh **with its
  verdicts in the notes**, and `ingest_wold.py reach` either runs or is
  reported as *cannot verify* rather than as a skip;
- the full suite is green on a frozen tip with retained receipts, and
  `[SUITE-GATE-V23]` is resolved rather than left as a placeholder;
- every unfinished item ships or parks **in writing**;
- the outside design inquiry for v0.24 is **named**:
  `reports/design-direction-v0.24.json`, reviewed DESIGN-protocol-uptake,
  reaffirmed (not re-run) as the incumbent against STRANGER-GATE. The brief
  already exists; this cycle's stops (G-P0 0/21, ECHO 0/50 and 0/500, R-NF
  0/220) travel with it.
