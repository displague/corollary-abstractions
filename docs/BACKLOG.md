# Backlog

Actionable friction found while working, kept here so it isn't lost in chat
or commit history. Each item names the evidence that motivated it.

## Filed after the v0.23 Codex harness trial (early v0.24 design input)

- **PROTOCOL UPTAKE -- design-only candidate, reviewed, not scheduled
  (2026-08-28).** The first ordinary input through the shipped Responses skin,
  `hello`, reached the proposition/corpus refusal path. The new design does not
  promote `hello` to a command: a builder-generated protocol vocabulary
  (`protocol/protocols.json`, deliberately outside `data/` and every existing
  corpus glob) and exact
  session signals jointly license uptake, served on a new `corollary/protocol`
  profile so neither shipped surface is widened; materially different surviving
  transitions reuse signed `ASK -> WAITING -> reply`; nested uptake resumes the
  exact parent. The Responses prompt-tool claim is separately gated and remains
  UNTESTED if the installed Codex host advertises no compatible tool schema.
  Evidence and the full 15-direction funnel:
  [DESIGN-protocol-uptake](DESIGN-protocol-uptake.md),
  `reports/design-direction-v0.24.json`.

- **DEPUTY -- live execution transport, parked behind its own design and
  STRANGER-GATE (2026-08-28).** The series-1 finalist survived only after shell,
  hostile input, and composition claims were removed. Its first admissible slice
  is maintainer-authored Python with pinned inputs, budgets, stdout/stderr/exit
  receipts, and no path to the PROVEN write gate. A reproducible run of the wrong
  program is its named residual risk. Unpark only through a separate design that
  checks semantic correspondence and keeps Python and shell authority distinct.

- **SHADOW -- exact abstraction with a loss ledger, parked as an answer-type
  candidate (2026-08-28).** The series-3 finalist evaluates formal syntax in one
  hand-authored abstract domain without calling the concrete evaluator, scores
  primarily where that evaluator declines, and refuses a new epistemic label.
  Unpark requires a rule-coverage prerequisite: its frozen proposal can ship an
  unexercised wrong rule green, the residual risk its own gate did not price.

- **The remaining early-course directions keep their folds.** OSTENSION and
  ABSENCE route to the naming-layer/separability question; CONTRAST to a future
  consequential-ambiguity experiment; INSTRUMENT to scoped observations;
  SCOREBOARD to the existing journal and the parked exact blast-radius
  question; UNSAY to dependency closure; NO, BECAUSE to refusal lifts;
  HANDSHAKE to naming; MIRROR to realization/ECHO; TWO CLOCKS to the independent
  second reader; GRAFT behind premise necessity; HALF-LIFE to ORPHAN. None is a
  floating roadmap promise.

## Filed at the v0.22 rotation (the two censuses, the drift audit, and the v0.23 course's parks)

- **SHIPPED — current Codex could not attach to the HTTP skin (2026-08-27).**
  Codex CLI 0.147.0 accepts only the Responses wire API for custom providers,
  while `scripts/serve_chat.py` exposed only `/v1/chat/completions`; the live
  failure was an exact `404 /v1/responses`. The skin now maps the text-only
  Responses subset onto the same `ChatEngine`, ignores and reports Codex's
  preprompt/tool fields, supports in-process `previous_response_id` replay,
  and was exercised end-to-end by the unmodified `codex.cmd` binary with no
  API key or explicit prompt argument in the interactive launch command. A
  2026-08-28 TUI replay exposed two host-integration frictions after that
  transport shipped: inherited `codex_apps` startup blocked the first turn,
  and Codex's model probe expected its additive catalog rather than only the
  standard OpenAI `data` list. The documented launch now disables Apps and
  plugins for the standalone text-only session, and `/v1/models` serves both
  catalog shapes.

- **The naming-layer question — how does a nameless library get names a person
  can ask by? (2026-08-27, forced by both v0.22 censuses).** A **first-class
  carried lane**, not a park with a trigger: H-P0 measured that only 417 of
  12,777 statements (3.26%) carry a specific typable handle, and the cross-census
  overlay found only 125 of the 9,048 one-step-consumable statements are nameable
  (`experiments/handles_census.json`, `experiments/onestep_census.json`). *The
  naming layer must be built, not indexed.* Candidate material recorded, not
  chosen: **name-derivation from the verified English renderings** the voice
  serves; the **S3 term store** priced at ~223.5 s batched over 2,313 covered
  statements (`handles_census.json` `s3_price`; the design addendum rounds to
  ~217 s). Carries to the **v0.24 course** unchanged. HANDLEBAR parks behind it.

- **ORPHAN — receipts that outlive the program (2026-08-27, the cold-census's own
  recorded next question).** Series-1 runner-up of the v0.23 course. The census
  found 1 of 19 receipt kinds SURVIVES and 10 NEED-PROGRAM; ORPHAN asks **which
  single pinned dependency converts the most NEEDS-PROGRAM kinds to SURVIVES**.
  Its value beyond the census: **it unparks TOLL's n=1 denominator** — the cost
  lane's metrology now has both an instrument (§2's harness) and a denominator
  path. Parked with its trigger.

- **SELF-SEED — provenance-typed growth by proof (2026-08-27, v0.23 series 2).**
  The commit half of the parked derivations lane, carrying the **novelty verdict
  the park lacked**; seeds mechanically drawn, the maintainer may not pick.
  Unpark when a cycle wants proof-gated, provenance-typed corpus growth.

- **UPSTREAM-PATCH — program-free defect reproducers to reviewed upstream
  (2026-08-27, v0.23 series 2).** The give-back direction. **Capped at UNTESTED**
  by the outside-participation constraint: a receipt whose adjudicator is a
  third-party reviewed upstream is one this repository cannot pin, so its
  survival cannot be tested here. Parked with its license discipline.

- **FOREIGN-SEAM's feasibility residue (2026-08-27, v0.23 series 2, cut).**
  Adjudicated cross-corpus divergence was **cut, cut defended**: within-ecosystem
  divergence is ingestion in a seam costume, and cross-assistant divergence needs
  an alignment language that exceeds one cycle. What remains parked is only a
  **feasibility spike** — no instrument is claimed, and the residue is recorded
  so a later cycle inherits the cut's reasoning rather than re-proposing it.

- **HANDLEBAR — reach-by-hole-term (2026-08-27, v0.23 series 1).** Parked behind
  the naming-layer question its shuffle limb would have probed; the shuffle limb
  was a candidate rider. Unpark when the naming-layer lane is scheduled and a
  hole-term reach is the mechanism it needs.

- **STRANGER-GATE — red-team the proven-material write gate (2026-08-27, v0.23
  series 2 lead, parked).** A **v0.24 incumbent-candidate with a PROHIBITION
  trigger**: it MUST run before any untrusted stream reaches the write gate, and
  nothing the v0.23 cycle opens one (GUEST AXIOM's guest text enters a *frame*,
  never the gate). Residual risk recorded: one head authors the attacks, the
  twins and the gate, so it measures whether the gate DISCRIMINATES, never
  whether the corpus is ADEQUATE; a PASS licenses "24 named evasions closed,"
  coverage unmeasured.

- **PREMISE LEDGER — necessity receipts (2026-08-27, v0.23 incumbent-candidate,
  capability-class).** From the v0.22 supplementary family series; the successor
  to GUEST AXIOM's consumption-only scope — receipts certifying assumption
  *necessity* by per-premise countermodels. LOADBEARING (v0.23 series 1) folded
  into it as independent convergence. Carries to the **v0.24 course** unchanged;
  its necessity claim is explicitly **not** taken by GUEST AXIOM this cycle.

- **The two review defects, fixed with headline numbers unmoved (2026-08-27).**
  Recorded so the fixes are not mistaken for silent edits. (1) `handles_census.json`
  and `skeleton_index.json` attested a `writer_sha256_lf` for a version of the
  writer that no longer existed — a provenance block nothing scores. (2)
  Underneath it, the `most_resolving` handle rankings ordered ties by
  `PYTHONHASHSEED`; the artifact's own *"recomputes byte-identical"* sentence was
  false. Both fixed (ties now break on the handle's own bytes); no coverage,
  distribution, split or union number moved.

## Filed at the v0.21 rotation (the drift audit, and the v0.22 course's parks)

- **The `conform` capability sheet advertises the asker's numbers; the route
  discards them; and the sheet's own example refuses (2026-08-26, from the
  rotation's drift audit).** A **product surface** claiming a behaviour it does
  not have, which is the one shape the drift-audit rule exists to catch on a
  live route rather than an absent one.

  **Three parts, each measured.**
  1. `scripts/serve_chat.py:635-637` publishes the `conformance` row's
     description as *"a committed statement compiled to an exact evaluator over
     the **asker's own numbers**, answering with a conformance record."*
     `scripts/harness.py:2192` parses the bindings with `find_bindings` and
     `:2229` calls `run(program, schema.digest)` **without them**. Typing
     `conform <id> a=2 b=2` produces byte-identical output to the bare line;
     the bindings are used only to name the ones the statement does not carry.
  2. `scripts/serve_chat.py:332` publishes the worked example
     `conform algebra.polynomial_equations.quadratic_formula a=1 b=-3 c=2`.
     Typed today it returns `status: refused`, `detail: does_not_parse`. **A
     published example is a product surface**, and an attaching orchestrator
     configures itself from this sheet — that is the sheet's stated purpose.
  3. `scripts/harness.py:2133-2155`'s docstring still reads *"registered, and
     refusing for now. A stub…"* and *"What it will do when `scripts/conform.py`
     lands is NOT sketched here"*, in a tree where `conform.py` landed and the
     route is live.
  4. **The README carried the same sentence** — *"statements that compile into
     something you can run against your own numbers"* — and is **corrected in
     place at this rotation**, with a dated parenthetical. It is the one
     document of the four that can be repaired without destroying evidence:
     a shipped release and a closed roadmap are records of what was written,
     and the code is the subject of the finding.

  **Why it was invisible for a cycle.** RELEASE-v0.20.0 named the underlying
  gap in its own honest limits — *"The route tests the sampler's points, not
  the asker's numbers"* — and then filed it **nowhere**: no BACKLOG entry, no
  ROADMAP-v0.21 row. A named honest limit with no owner is the same drift shape
  the v0.20 audit caught for *load-bearing / premise-necessity*.

  **Not patched at the rotation.** Widening or narrowing a served route is a
  behaviour change owing its own evidence and its own quarantine gate.
  **Two admissible discharges**, and the second is the honest minimum: either
  the route consumes the bindings, with a served diff and a control; **or** the
  description, the example and the docstring are corrected to say what the
  route does. Named in ROADMAP-v0.22 §4.3.

- **Slice 1's citing behaviour is unreachable from the typed prompt, and the
  release notes' first draft implied otherwise (2026-08-26, from adversarial
  review of the rotation drafts).** Not a defect in the slice — it is exactly
  what `DESIGN-session-ledger` specified, which names **no served surface** for
  slice 1 — but it is a gap between a claim's wording and a claim's acceptance,
  which is what this entry exists to hold.

  **The mechanism.** `harness.main()` boots
  `CoreSession.boot(repo_root, offline=offline)` (`scripts/harness.py:2425`)
  and never sets `session.assumptions`. Only
  `SessionRecorder.__post_init__` does
  (`scripts/session_recorder.py:121-128`). So `_route_supposition` reads
  `getattr(session, "assumptions", None)` (`harness.py:1714`), finds `None`,
  and holds the claim in a supposition frame **without declaring an Assumption
  record**. `retract <id>` therefore always refuses `unknown_assumption` at the
  prompt — correctly, and byte-identically to the ledger case, which is the
  **B10 repair working**.

  **What that costs a reader.** The release skill's rule is *"shipped means the
  acceptance a newcomer can try"*, and its worked example is a prior cycle
  claiming a system could be *driven* when `harness.py` printed a liveness list
  and exited. A newcomer here can type `suppose` and `retract` and watch them
  render; a newcomer **cannot** watch an answer cite an assumption without
  writing a recorder. R1's claim lives in `session_ledger_run4.json` and
  `tests/test_session_ledger.py`, and the run artifact says so in its own
  `where_the_claim_lives` field.

  **Filed rather than fixed**, because attaching a ledger to the CLI is a
  served-behaviour change owing its own evidence: B10's fence exists precisely
  to prove that ledger state does not reach uncited answers, and a surface that
  attaches one silently would move the thing B10 measures. Unpark condition: a
  design that says what a person-facing session is — where its key ring comes
  from, where its journal is written, and what B10 re-scores on it — before any
  route attaches an `AssumptionSet` outside the recorder.

- **The v0.19 course's two riders are named-and-unrun for a third rotation, so
  the stop rule fires and both park (2026-08-26).** Unrun through v0.20 and
  v0.21 since ROADMAP-v0.20 §3 scheduled them, and listed once more here. ROADMAP-v0.21 §3.5: *"If either is still
  unrun at the v0.22 rotation, it stops being a rider and either becomes an
  item or parks."* Neither the **HOLES counting table**
  (machine-enumerated skeleton gaps, counted, to *"revive-or-close FOUNDRY with
  a number"* — an afternoon's work by its own estimate) nor the **delete-K
  ground-truth table** (survived from ONE HOP, which *"surrendered to the prior
  course's excluded substitution chains"* — the direction went, the table
  stayed) has produced an artifact. **Both park.** Unpark condition, identical
  for each: a cycle that wants the answer schedules it **as an item**, with a
  number. Neither is listed as an available rider again, and delete-K is **not**
  unparked by TOLL, which measures cost rather than K. Both lineage sentences
  are restored here, because ROADMAP-v0.21 carried the two riders forward with
  the descriptions stripped and *"delete-K ground-truth table — carry forward
  unchanged"* is not a description of anything.

- **DESIGN-block-vocabulary's one untested property fell into a catch-all
  (2026-08-26, from the rotation's drift audit).** RELEASE-v0.19.0 named it
  deliberately: *"**What survives for any future unpark**, named so it is not
  lost: the design's **append-only, path-independent growth** property, which
  **no baseline in this probe tested**."* ROADMAP-v0.20 §5 kept it in the row;
  **ROADMAP-v0.21 folded the design into a catch-all and the property stopped
  being quoted anywhere in the carried record** — the exact pattern
  RELEASE-v0.20.0 condemned for *realization parameters as data* one page
  earlier. **Recovered**: quoted again in ROADMAP-v0.22 §4.3. Unpark needs a
  design saying what append-only path-independent growth buys that two indexes
  with one tag bit do not; the rest of the lane stays **parked by numbers**
  (0.9981 against that baseline).

- **Three clause deletions inside rows that said "unchanged", beyond the
  article v0.20 caught (2026-08-26).** Recorded so the next rotation greps for
  the restored wording rather than for the shortened one.
  - **Ledger-first claims**: the dependant went from *"none this cycle"* to
    *"none"*, the verb from *"It **became** a headline candidate"* (a fired
    event) to *"it **becomes**"* (a standing conditional), and the receipt path
    `reports/design-direction-v0.17.json` was compressed to *"receipt"*. All
    three restored in ROADMAP-v0.22 §4.3, beside the article v0.21 restored.
  - **Licensed variant generation**: the trigger lost **"for the same term"**,
    the qualifier that made it checkable, and the row lost its evidence
    sentence — *"A ranker is not blocked by the admission bar — it is blocked
    by the absence of anything to rank."* Both restored.
  - **Open-English input**: the worked example (**`gcd` vs "greatest common
    divisor"**) and the fired-trigger clause (**"and R1 firing is what made it
    askable"**) were both deleted at v0.20 and not restored at v0.21. Both
    restored — and the example is no longer hypothetical, because v0.21's run
    measured it at **zero enumerated candidates**.

- **A recovery undone by the vehicle it was undoing (2026-08-26).**
  ROADMAP-v0.21 recovered *realization parameters as data* into its own row
  with the trigger quoted — **and left it inside the catch-all row as well**,
  the catch-all whose *"unchanged"* was the thing the recovery was fixing. A
  lane in two rows with two dispositions has no readable disposition. It
  appears exactly once in ROADMAP-v0.22 §4.3. **Filed as a rule, not an
  incident**: when a lane is recovered out of a catch-all, delete it from the
  catch-all in the same edit.

- **`[SUITE-GATE-V20]` was never resolved, and v0.20's refresh clause never
  landed (2026-08-26).** The token appears **three** times outside
  RELEASE-v0.21.0 — in RELEASE-v0.20.0, in ROADMAP-v0.20's closed banner, and
  in **this entry**, which is a third occurrence its own first draft did not
  count. *(Corrected 2026-08-26 from adversarial review: both this entry and
  the release notes first read "exactly twice". A token-count audit that
  miscounts its own token is the cycle's recurring shape arriving inside the
  paragraph that catalogues it, and the miscount is left recorded rather than
  quietly replaced.)* It is a cross-reference to a section nobody wrote. So ROADMAP-v0.20's banner still
  declares **three** gate clauses open (refresh, full-suite, ships-or-parks)
  while RELEASE-v0.20.0 does report two suite runs; and
  `check_report_regeneration.py`'s three verdicts, which
  RELEASE-v0.20.0 said would *"land in this section then"*, never landed.
  **Neither document is edited** — a closed roadmap and a shipped release are
  the record of what was written. Filed so the pattern is visible:
  `[SUITE-GATE-V21]` is a promise somebody has to come back for, and a
  placeholder that is never resolved is a gate clause that quietly did not run.

- **ROADMAP-v0.20's banner and RELEASE-v0.20.0's drift audit contradict each
  other on 4d (2026-08-26).** The banner says the then-present served diff
  *"was never produced"*; the notes say it was *"discharged at this rotation"*;
  the committed `experiments/foreign_voice_wiring_served_diff.json` agrees with
  the notes (`sides.before.armed` and `sides.after.armed` both `true`,
  `answer_lines_moved` 0 of 14,830). The banner is wrong. Recorded rather than
  edited, for the same reason as the entry above.

- **Three stale citations in the previous two documents (2026-08-26).** Named,
  not edited, because correcting a line number inside a shipped release would
  make this audit's own evidence unreproducible.
  `RELEASE-v0.20.0` cites `serve_chat.py:515-537` for the `"claims": null`
  emission; that line is now **581**. Its 4d transition command reads
  `--before 8e1a3d1` while the artifact's own `regenerate_with` field reads
  `--before main`. And `ROADMAP-v0.20`'s pre-fix citations
  (`match_signatures.py:412`, `evaluate.py:182`) both land on different code
  now, because the fixes moved the files.

- **`retract <assumption-id>` is a published normative surface that never
  serves on the chat skin (2026-08-26, said on the day it ships).**
  `docs/SPEC-chat-completions-skin.md:175` registers the row; ¶DEV-1 replays
  every request into a fresh session with no assumption set, so the route
  always returns `refused`. That is correct behaviour and the spec says so.
  Filed anyway, because a published surface that never serves is exactly the
  fact that becomes a drift finding three rotations later if nobody names it
  on the day. Unpark condition: a chat skin that carries session state, which
  is a design and not a patch.

### Parked from the v0.22 course, with their probes and triggers

Quoted from `reports/design-direction-v0.22.json` rather than summarised away,
so a later cycle inherits the disposition and not a rumour.

- **CANARY-CURVE — declared scaling classes frozen before growth, plus the
  architecture-versus-smallness split (2026-08-26).** Series 3's lead, parked as
  a **named v0.23 incumbent-candidate**, and **the ordering reason is its own
  residual risk answered**: its 10× measurement-only shadow tier prices
  *statement count*, while the dimensions that actually bite intake —
  title-collision density, enumeration fan-out — may be sparser in the tail. So
  growth is measured **after** the enumeration layer exists, when density is
  measurable instead of missed. Its gate is worth keeping intact for whoever
  unparks it: **B4's deliberately-O(n²) canary declared O(n) must go RED at 10×
  with ≥3× margin or the whole run voids**, and **B3 makes zero RED among
  non-canary rows void the run as UNDER-DECLARED** — too clean is a failure.

- **TOLL — production cost against stranger-path re-check cost on a named floor
  machine (2026-08-26).** The fold of LEDGER and PAUPER, parked as a **v0.23
  incumbent-candidate beside CANARY-CURVE**, and **it is the first named unpark
  candidate the cost ledger has had in six rotations.** Its denominator waits
  on COLD RECEIPT's harness, and the receipt claims that composition
  **explicitly**: *"refusing it would mean the affordability claim marking its
  own homework."* **CEILING is TOLL's named successor** and routes with it —
  *no budget freezes before the cost distribution exists*, which is v0.21's
  mis-derived-floor lesson one lane over, and *a budget blown at 10× is a curve
  row, not a failure*.

- **TWO WITNESSES — checked independence of two readings (2026-08-26,
  DEMOTED).** Series 1's runner-up, first accepted as rider R2, then **demoted
  by the design review (H9) from rider to parked item-candidate**: its
  160-obligation mutation battery is a **WITNESS-slice-sized cost** — the whole
  v0.21 WITNESS slice budgeted 50 mutants — and a slice-sized cost is not a
  rider. **It parks with the conformance successor it serves**, because they are
  one problem: WITNESS cannot open without a second independent reading of `S`,
  and TWO WITNESSES' kernel-then-overlap probe is what would price one.

- **CROSSING — execution-licensed boundary crossings, both ways (2026-08-26).**
  The fold of REBUTTAL and EXIT SIGN. Parked **with its 20-real-corrections
  probe and its preregistered predicted split, 2 / 6 / 12** — committed now so
  the probe cannot be read after the fact.

- **LONG CON — sequence-level adversarial search over conversations
  (2026-08-26).** Retired to a **day-probe**: ten hand-written sequences, frozen
  budget, **mandatory plant**, and a committed near-miss taxonomy **even on a
  null**. The **write-gate prohibition is inherited** — HOSTILE DICTATION
  unparks first if any untrusted stream is ever opened.

- **BITROT — fault-injection scope for exactness on unfaithful hardware
  (2026-08-26).** Parked as a **day-probe**, and its **stop rule is recorded
  here** because the receipt carries only its controls: **any undetected
  changed-answer count > 0 stops the probe and publishes the narrowed scope; a
  clean 1,000 publishes the integrity-scope map and closes the probe.** Its
  never-read-bytes control is the point — *a detector catching unread flips is
  comparing the store to itself.*

- **NOTARY did not park — it became a schema field (2026-08-26).** Composable
  receipts and void propagation distilled into **one mandatory receipt column**,
  `route_voids[]`, machine-checked: *a receipt that traverses a published void
  and renders clean is a red result.* Recorded here so a later cycle looking for
  NOTARY finds where it went.

## Filed at the v0.21 session-ledger slice (P2's probe)

- **The resolver silently binds an ambiguous prose line and the receipt does
  not say a choice was made (2026-08-26, measured by P2).** Filed, not fixed:
  this is DESIGN-plain-input's territory and belongs to slice 2, which this
  commission did not build.

  **The measurement.** `experiments/session_p2_separator_probe.json` served
  ten hand-sealed ambiguous prompts as raw prose, on a fresh offline session
  each. Eight exhausted or waited, honestly. **Two came back `found`** — a
  grounded answer to a question the prose underdetermined, with nothing in
  the verdict recording that a reading had been selected. The seal's own
  `why_ambiguous` field for each of the two names the alternatives the
  system silently passed over.

  **The two fixtures, already committed, already sealed.**
  `experiments/session_p2_prompt_seal.json`:
  - **`p04`** — *"cosine of a double angle"*. Sealed readings: the identity
    itself (`twin trigonometry.identities.double_angle_cosine`) or the
    statement whose words these are (`double angle cosine identity`, the
    resolver row). Served: resolver, `found`.
  - **`p10`** — *"the quadratic formula with a=1 b=-3 c=2"*. Sealed
    readings: RUN the statement on those bindings
    (`conform algebra.polynomial_equations.quadratic_formula a=1 b=-3 c=2`),
    show me the statement (`quadratic formula`), or show me the family
    (`twin algebra.polynomial_equations.quadratic_formula`). The person
    supplied bindings, which most naturally reads as RUN; the served answer
    was the resolver's, `found`. All three routes are live, so this is a
    real three-way and not a hypothetical.

  **Why it is a defect and not a preference.** The repository's standing
  rule is `docs/DESIGN-text-resolution.md:53-56` — *"any counterexample is a
  failure, because it would mean the renderer authored a claim"* — and
  DESIGN-plain-input §5's G2 restates it as *every served interpretation is
  either verifier-confirmed or supposition-labelled.* A resolver `found` on
  an underdetermined line is neither: the graph confirmed that a statement
  matches those words, not that it is the statement the person meant.

  **The repair this is filed against.** DESIGN-session-ledger's Assumption
  record now exists and persists (slice 1, R1 HOLDS), so slice 2 can serve
  the residue as a named supposition — *assuming you meant X, the answer is
  Y* — rather than as an unmarked `found`. P1 constrains how: the resolver
  row is one of the nine OPEN classes, so an enumerating proposer has no
  finite target there and must propose-then-verify. And P2's own aggregate
  says the clarifying-question arm is expressible for 9 of 10, so slice 2
  cannot claim the conditional arm won by measurement.

  **How a repair proves itself.** Both prompt ids are the fixtures, their
  candidate-reading sets are already sealed and committed, and the seal's
  commit is an ancestor of the probe's (checked by
  `tests/test_session_prereqs.py`). A repair passes when p04 and p10 stop
  returning a bare `found` and start returning either a supposition-labelled
  answer naming the reading taken, or a clarification naming the sealed
  alternatives. **Re-running the probe re-measures it**: the number to move
  is `aggregate.raw_prompts_silently_bound_today`, currently **2**.

  > **SUPERSEDED 2026-08-26 by the entry below, and not deleted.** Slice 2
  > was built, wired and served, and it **cannot reach this defect**: its
  > proposer is confined by DESIGN-plain-input §2.2 to row 12 — the row
  > where nothing binds — and the silent binding happens at the resolver,
  > an earlier row that G4's quarantine protects by name. Serving all
  > thirty of the sealed plain questions measured the surface wider than
  > this entry's two fixtures suggested: **13 of 30 come back `found` from
  > the resolver before the proposer is consulted at all**, and p04's and
  > p10's own utterances are among the thirteen. The two fixtures stay
  > valid and stay sealed; the entry that carries the work forward is the
  > next one, with thirteen. Deleting this one would erase the smaller
  > measurement that found the defect first, and a superseded record that
  > is removed teaches nothing about how the estimate moved.
  > Evidence: `experiments/plain_input_prereg.json` amendments 3 and 4.

- **The resolver's pre-emptive binding is the standing defect, and its repair
  is a designed successor (2026-08-26, superseding the entry above).** Filed
  with thirteen committed fixtures and the mechanism published, per the
  orchestrator's ruling recorded verbatim in
  `experiments/plain_input_prereg.json` amendment 4.

  **The measurement.** Every question in the sealed
  `experiments/plain_question_set.json` served through a fresh offline
  `CoreSession`, proposer attached. Thirteen returned `found` from the
  **resolver**, before `_route_proposed` was consulted:
  `g1-03`, `g1-05`, `g1-06`, `g1-07`, `g1-10`, `g1-12`, `g1-14`, `g1-15`,
  `g1-17`, `g1-18`, `g1-19`, `g1-20`, `g1-22`. Five more (`g1-01`, `g1-11`,
  `g1-16`, `g1-21`, `g1-27`) were pre-empted at `waiting` by the resolver's
  own ASK subloop, which at least names its alternatives. Twelve reached the
  proposer. **The thirteen are the fixtures**; they are committed, in order,
  in a file whose commit is an ancestor of every proposer commit on this
  branch.
  **Candidate mechanism (2026-08-27, from the supplementary design
  series).** The outside referee's MEANING HANDSHAKE proposes the repair
  shape this entry lacked: *person-confirmation as the license* —
  "confirmation subsumes the old pre-emption: all thirteen exact-match hits
  become proposals and still await confirmation." Recorded as the candidate
  mechanism for this successor's own preregistration, not adopted here; the
  successor still owes its own prereg, control, and K re-measurement, and
  inherits the referee's UNNAMED_SCOPE typed refusal for questions over the
  nameless majority.

  **Why the obvious repairs are refused rather than untried.** Moving the
  proposer ahead of the resolver breaches G4 — *"a single differing verdict
  voids the whole reading"* — which is the gate that makes the rest of
  DESIGN-plain-input believable. Giving the resolver's BIND verdict a
  receipt naming its choice is technically safe (checked, not assumed:
  `harness.render_verdict` does not render `receipt`, the chat skin's
  `_resolution_receipt` builds its own from the answer lines, and the
  throughput book holds zero resolver-route tasks) but a receipt is neither
  a supposition label nor a clarification, so accepting it would be meeting
  a gate by re-reading it after seeing what was reachable.

  **What a successor owes, stated so it is scheduled rather than wished
  for.** A design that may touch the resolver row needs (1) its **own
  preregistration**, (2) its **own capability-blind control**, because G5's
  control is scoped to selection among enumerated candidates and says
  nothing about a changed bind rule, and (3) a **K re-measurement**: the
  resolver row is inside the serving path the throughput book scores, so a
  changed bind rule can move a sealed denominator that slice 2's
  `conditional` status provably cannot. Slice 2's own G4 does not transfer;
  the successor needs a new one written against whatever rows it moves.

  **What is NOT claimed, anywhere, because of this.** That slice 2 repairs
  the silent binding. It does not. Any release note quoting P2's defect
  beside slice 2 must say the defect is unrepaired, and slice 2's own R2
  licensing sentence carries the limit in the same sentence that claims the
  capability.

- **`PlainRouter._reserve` re-serves a chosen candidate through the CALLER's
  index, which spans `data_holdout/` (2026-08-26, from adversarial review of
  the merge candidate).** Measured zero; filed because zero-by-vocabulary is
  not zero-by-construction.

  **The asymmetry.** `candidate_enumerator` builds its index explicitly over
  `[repo_root / "data"]`, and slice 1's M9 finding is why: `default_index()`
  spans `data/` **and** `data_holdout/`, and **2,053 holdout ids sit in it**.
  But `plain_router.PlainRouter._reserve` copies `session.resolver_index`
  from its caller, and a recorder's index *is* `default_index()`. So a
  conditional answer's body — the verbatim engine answer §3b promises — is
  produced through an index that can see the holdout, while the candidate
  that named it was chosen from `data/` alone.

  **What was measured.** G8's third limb (*"or in any served answer"*) was
  **never executed by the registered run**, which reported G8 GREEN on two
  limbs of three. The reviewer executed it: 108 verified candidate lines
  re-served, **0** holdout ids, **0** divergent statuses. The runner now
  carries the limb and reads **0** over its own denominator of 120 lines (78
  distinct). Verdict unchanged either way.

  **Why it is filed and not patched.** Narrowing `_reserve`'s index after the
  run would change served behaviour the run measured. The repair belongs to
  whichever slice next touches the router: either `_reserve` builds its own
  `data/`-only index, or the recorder stops handing a holdout-spanning index
  to a session the proposer is attached to. Both are behaviour changes and
  both need their own G4.

- **The candidate enumerator's tiebreak is title length, which caps G1's
  ceiling invisibly (2026-08-26, from adversarial review).** On `g1-22`
  (*"what does the corpus say about the distributive law"*) the corpus
  contains **two correct readings that both verify** —
  `settheory.boolean_laws.distributivity_meet_over_join` and
  `logic.boolean_laws.distributivity_meet_over_join` — enumerated at ranks
  **21 and 23**, outside the frozen limit of 8. The model never saw them and
  its `NONE` was a **correct refusal against a mis-ranked list**.

  **The mechanism is one line.** The total order is *(descending word
  overlap, ascending title length, statement id)*
  (`candidate_enumerator.py:261`). Everything ties on the single shared word
  `law`, so the tiebreak is length and `Ohm's Law` outranks *Distributivity
  of Intersection over Union*.

  **Not repaired**: amendment 1 froze both the order and the limit precisely
  because they move the blind arm's chance baseline, so changing either after
  seeing the arms would move a control's baseline with the results in view.
  And a **longer list is not the fix** — raising the limit to 24 would have
  surfaced these two by accident of where they sorted, which is not a
  mechanism. The blocker is the same ranking-or-synonym layer
  `DESIGN-plain-input` §8.4 names. Recorded as design §8.5.

- **G5's collapse rule cannot tell selecting-well from selecting-often, and
  it is why the seat ships empty (2026-08-26, measured by the registered
  run).** The rule was frozen before the proposer existed and was scored as
  frozen; this entry is the successor's, not a re-reading of the run.

  **What the run measured.** The blind arm made **22** verified selections on
  the sealed thirty; the proposer made **17**; the rule required the blind
  arm to be at or below **8.5**. The blind draw was not lucky — its
  analytic expectation over the same candidate lists is **20.62** — and the
  registered consequence therefore fires exactly as written: *"the seat ships
  empty with the number."*

  **The mechanism, which is a defect in the METRIC and not in the result.**
  The rule counts a *verified selection* and cannot see a *correct refusal*.
  The model answered `NONE` on six questions; every one of those six had
  verified candidates available, and the blind arm — whose alphabet has no
  `NONE` — took them. On the nine questions authored to exhaust, the model
  selected for **zero** and the blind arm selected a verified candidate for
  **five**. The control rewards, in its blind arm, precisely the behaviour
  DESIGN-plain-input calls inventing.

  **What a successor's rule owes.** Score the BRANCH OUTCOME against the
  question's registered disposition (conditional / ask / exhaust) rather than
  the raw verified-selection count, so that declining an out-of-corpus
  question counts as success for both arms and the blind arm's inability to
  decline shows up as the incapacity it is. And freeze it with a
  **meetability argument** per ROADMAP-v0.21 §4.0(3) — a pilot or a
  construction argument that a *correct* proposer can reach the floor. This
  rule had none, which is the same defect class C-E1's 0.99 flip floor was.

- **`run_session_gate.score_b10`'s stateless arm does not inherit the
  journal's configuration (2026-08-26).** Its stateless side boots a session
  with **no proposer**, because slice 1 had none. On a slice-2 journal that
  compares two configurations rather than two states, and B10's own gloss is
  about state: *"session state may never leak into unconditional answers."*
  The registered run publishes both readings — slice 1's arm unchanged (RED
  on 5 turns) and a state reading with configuration held fixed (GREEN) —
  and the measured fact that reconciles them: **every one of the five misses
  is a turn the plain-input route served**, which is the entire behavioural
  change slice 2 makes and which G4 separately proves happens nowhere else.
  The fix is a parameter on the arm, not a new gate; filed so the next slice
  does not re-derive the argument.

- **Slice 2 turns some honest refusals into clarifying questions, which
  contradicts DESIGN-plain-input §7's own non-claim (2026-08-26, measured).**
  *"Not open-domain. Outside the corpus the honest output is still a refusal.
  A proposer that cannot find a registered query still exhausts."* Two of the
  sealed questions authored to exhaust — `g1-26` *"how do i change a tyre"*
  and `g1-29` *"what did i ask you before"* — came back `waiting` with corpus
  readings named.

  **The proposer is not what broke it.** On both, the model answered `NONE`:
  it found no registered query, exactly as §7 describes. What served the
  clarification is the **branch rule**, which fires on the count of VERIFIED
  candidates and never consults the model's `NONE`. "How do i change a tyre"
  came back offering *Average Rate of Change*, *Fundamental Theorem of
  Calculus* and the *Righthand Head Rule*.

  **Not repaired here, and the reason is the rule this repository lives by.**
  The branch rule is frozen in `plain_input_prereg.json` amendment 2, written
  against the design's own text *before the rule had ever run*. Changing it
  after watching it behave is the move that turns a preregistration into a
  narrative. Unpark condition: a successor prereg whose branch rule consults
  the proposer's `NONE`, with its own control — and note that letting a
  learned `NONE` suppress a clarification puts the model back on the
  refuse/serve boundary, which is the standing clause
  (`DESIGN-sans-template-rendering:337-340`) that must be argued, not
  assumed.

- **The synonym layer is still the blocker, and selection cannot substitute
  for it (2026-08-26, measured).** DESIGN-plain-input §2.3 names the `gcd`
  miss as the residue the proposer is aimed at. In the registered run,
  *"how do you compute the greatest common divisor recursively"* enumerated
  **zero candidates**: the proposer was never asked and row 12 exhausted
  exactly as before. Enumeration is by shared content words and the utterance
  shares none with a statement the corpus titles `gcd`. **You cannot select
  what was never enumerated** — so the parked synonym layer
  (`DESIGN-text-resolution:95-96`, *"a design and not a patch"*) is not
  reachable by this design at all, and any successor aimed at that residue
  has to build it rather than route around it. Five of the thirty sealed
  questions enumerate nothing for the same reason.

- **A verifier weaker than the proposer discards the proposer's correct
  answer, before any receipt exists (2026-08-26, measured).** On *"how do you
  compute a factorial iteratively"* the enumerator offered *Factorial,
  Iterative (TheAlgorithms)* first and the model selected it — the right
  reading. It did **not** verify: `word_match` requires a statement's own
  title to resolve back to that statement and this one binds elsewhere. The
  two candidates that did verify were both about the **double** factorial, so
  the person was asked to choose between two wrong readings while the right
  one was thrown away. *"Selection narrows; verification decides"* is working
  exactly as designed; this is the cost it buys, and the receipt cannot show
  what was discarded because the discard happens before a receipt exists.
  Filed as a receipt-shape question for a successor: a `candidates_discarded`
  field would make the loss visible without moving the trust shape.

- **Slice 2's wiring staled slice 1's sealed journals, and the closed corpus
  no longer replays against this tree (2026-08-26, measured).** Filed rather
  than repaired, because the repair touches a CLOSED seal and a PUBLISHED
  run.

  **The mechanism, measured and not inferred.** `scripts/harness.py` is in
  `build_throughput_tasks.RENDERING_MODULES`, so its digest is one leaf of
  every journal's `rendering_module_digests` pin. Slice 2's wiring commit
  added `_route_proposed` to that file. The sixty slice-1 journals record
  `09eda754…`; the tree now hashes `9dc6e660…`; `replay_session.compare_pins`
  therefore returns a mismatch and every replay refuses `stale-environment`.
  That is **B3's mechanism working**, not a failure — but it means slice 1's
  published R1 is a claim about the tree it was recorded against (`b388e6b`)
  and cannot be re-executed on this branch without re-recording.

  **The same edit left one debt that WAS payable and is paid.**
  `experiments/throughput_tasks.json` carries a digest witness over the same
  modules and went stale in the same commit; `tests/test_throughput_tasks.py`
  went red on it. The book is rebuilt and exactly one line moved — the
  harness witness — with no task, count or A/B assignment touched. It was
  caught by a suite the wiring commit did not run.

  **Why the journals are not re-recorded to match.** `record_session_corpus.py`
  exists for exactly this and slice 1 used it once already. Running it now
  would rewrite sixty committed journals and slice 1's **closed** seal, and
  the published `experiments/session_ledger_run4.json` scores those journals
  by the digests that seal carries — so a re-recording would leave a
  published run pointing at a corpus that no longer exists. A record that
  cannot be checked against the thing it measured is worse than a corpus that
  needs a re-recording.

  **What a repair looks like, when one is wanted.** Re-record at a fixed tree
  into a NEW seal (the `foreign_voice_rate.json` → `foreign_voice_rate2.json`
  successor pattern), retaining the prior seal byte for byte, and re-score B2
  and B3 against it. Its own commit, its own delta block, and the original
  never edited.

## Filed at the v0.20 rotation (the voice completed, the course, the drift audit)

- **`leanworkbook.skel.lean_workbook_50397` needs a seed regeneration, and no
  parser change can reach it (2026-08-25, promoted out of §4b's entry).**
  Filed as its own entry because it was the only live work left inside an
  otherwise-shipped one, and a residue buried in a LANDED blockquote is a
  residue nobody schedules. §4b made integer literals exact through the parse
  path, but this node's `inf` is **frozen into the committed
  `anonymized_template`** by `scripts/seed_lean_workbook.py`, and its
  `canonical_ascii` does not tokenize — so the parser never sees the literal
  that would be repaired. Unpark condition: a seed regeneration under
  AGENTS.md's seeds-are-the-source-of-truth rule, with the five checkers
  behind it re-run. Evidence: `experiments/exact_literals_prereg.json`
  (`non_claims[1]`); the diff surfaced `goedelpset.skel.goedel_pset_789185` in
  its place, so §4b repaired three served nodes but **not the three its own
  entry had listed**.

- **Load-bearing / premise-necessity — recovered after two cycles missing
  (2026-08-25, from the rotation's drift audit).** A named row in
  ROADMAP-v0.17 §3 and ROADMAP-v0.18 §3 (*"parked, travels with it"*), it is
  **absent by name from ROADMAP-v0.19 §4, ROADMAP-v0.20 §5 and this file**. It
  survived only inside `docs/DESIGN-ledger-first-claims.md`, which names it as
  that lane's *"own most likely successor"*. It **travels with ledger-first**
  and unparks with it, never separately. Named again in ROADMAP-v0.21 §3.3.
  Evidence: the two roadmaps' tables, and the design section.

- **Realization parameters as data: the unpark condition fired at v0.18 and
  the roadmaps stopped quoting it (2026-08-25, from the rotation's drift
  audit).** ROADMAP-v0.18 §3 parked it with *"becomes askable only if R1
  fires."* **R1 fired at 0.9991 in that same release.** ROADMAP-v0.19 restated
  the park **without the trigger sentence** and ROADMAP-v0.20 folded it into a
  catch-all row reading only *"unchanged"*. The honest state: **askable since
  v0.18, never scheduled, and askable is not scheduled.** Unpark condition,
  restored and quoted: the linearization-rule row of
  `docs/DESIGN-language-as-structure.md` §2's table, as a design saying what
  the parameters buy over the committed grammar.

- **Licensed variant generation — parked, after being carried twice with a
  vanishing dependant (2026-08-25, from the rotation's drift audit).**
  ROADMAP-v0.19 §4 named a dependant (*"item 2 of any future cycle that wants
  a ranker"*); ROADMAP-v0.20 §5 named **none** and carried it anyway, which is
  precisely what the carried-lane rule exists to catch. Parked here with its
  trigger unchanged: the realization grammar emits exactly one surface per
  term, so the preference seat has nothing to rank. **Unpark when a design
  says what licenses a *second* passing surface for the same term and why that
  is not decoration.** One new fact rides with it:
  `docs/DESIGN-plain-input.md` argues the **input** side is where the ranker
  seat finally has a denominator, because a plain utterance licenses several
  candidate queries by construction — a candidate dependant, not a commitment.

- **The ledger-first unpark trigger's article was edited from *the* to *a*
  (2026-08-25, from the rotation's drift audit; AMENDED).** ROADMAP-v0.17,
  v0.18 and v0.19 all wrote *"the first cycle after **the** throughput
  readout"* — a definite, one-shot event that fired at v0.17, making every
  cycle since a pass-over. ROADMAP-v0.20 §5 wrote *"**a** throughput
  readout"*, which converts an overdue trigger into one that cannot come due
  until a fresh throughput run happens — **in the same row that calls the rule
  "intact and not weakened by repetition."** The original wording is restored
  in ROADMAP-v0.21 §3.3 and the edit is recorded as an amendment rather than
  allowed to ride as an unchanged rule. Under either reading the lane is
  overdue: v0.20 produced **no new throughput readout** (three digest leaves
  moved in `experiments/throughput_tasks.json`; no
  `throughput_result*`/`throughput_trial_*`/`throughput_baseline` file changed
  at all).

- **The reader-determinacy question is empty on both sides and had no owner
  (2026-08-25).** **C-V3 (human)** has been **ABSENT** for two cycles — a
  single-maintainer repository has no non-maintainer to mark a determinacy
  sheet blind — and **C-V3′ (machine)** ran this cycle and **VOIDED**: served
  0.8417, skeleton 0.5000, ratio **0.594** against a 0.5 voiding threshold, so
  the reader was substantially supplying the mathematics rather than reading
  the words. Neither appeared in any carried table or in this file until now.
  The consequence is stated rather than implied: the project serves English
  sentences that are **provably faithful to the mathematics** and has **no
  evidence anyone can read them**. Unpark needs a population of markers this
  repository did not author — the same missing-population problem as
  **STRANGER**. Evidence: `experiments/c_v3_prime_arm.json`,
  `experiments/foreign_voice_rate2.json` (`c_v3`, `c_v3_prime`).

- **Is canonical bracketing load-bearing for a reader? (2026-08-25, the
  honest half of the grouping repair.)** `experiments/grouping_census.json`
  published the **exposure** counts — 435 of 2,313 covered surfaces change
  (18.81%), **151** statements lose **every** grouping word (the design's
  read-only prototype had previewed 150) — and labelled them exposure and
  **not readability**, in writing. One sealed surface canonicalizes to four
  disjuncts with no grouping word anywhere. Whether that helps or hurts a
  person is **not answered and not closed**; only a human determinacy sheet
  could answer it, so this entry **parks behind C-V3 above** rather than
  standing alone.

- **The v0.19 course's two accepted riders were scheduled and never ran
  (2026-08-25, from the rotation's drift audit).** ROADMAP-v0.20 §3 listed the
  **HOLES counting table** (machine-enumerated skeleton gaps, counted, to
  *"revive-or-close FOUNDRY with a number"*) and the **delete-K ground-truth
  table** (survived from ONE HOP, which surrendered to the prior course's
  excluded substitution chains) *"so they are **scheduled** rather than
  remembered."* Neither produced an artifact and neither was filed anywhere.
  They were remembered, not scheduled. **Stop rule, added here:** a rider is
  cheap by construction, so an unrun rider is a scheduling fact and not a cost
  finding — **if either is still unrun at the v0.22 rotation it stops being a
  rider and either becomes an item or parks with a reason.** Evidence:
  `reports/design-direction-v0.20.json`.

### Parked from the v0.21 course, with their probes and triggers

Quoted from `reports/design-direction-v0.21.json`
(`selection.declined_with_lessons`) rather than summarised away, so a later
cycle inherits the disposition and not a rumour.

- **ATLAS — a total per-(statement × surface) obstruction map with witnesses
  (2026-08-25).** Series 3's lead, **parked as a named instrument probe**
  respecting the standing counsel against instrument-shaped headlines — and
  the direction was honest about it in its own words: it *"makes zero
  statements reachable."* Its **TWINS 500-pair probe** is listed standalone:
  under 10 hits collapses TWINS to *duplicate-of*, **and the near-zero is the
  result**. Residual to carry into any unpark: **first-blocker bias** — cells
  record the first cause a surface tripped on, so stacked obstructions are
  under-reported.

- **DEMAND — an obstruction ledger against a question dump the program did
  not author (2026-08-25).** Series 3's runner-up, **parked as a named probe
  with its licence and pin rule attached**: a static CC BY-SA question dump,
  **titles only**, digest-pinned, with the **drawing rule committed before
  decompression**. That rule is the park's value: it is the STRANGER problem
  with a licence-clean population attached, and the drawing rule is what stops
  the population being chosen after the answers are seen.
  **Convergence note (2026-08-27).** The maintainer-directed supplementary
  design series (a different model family; receipt
  `reports/design-direction-v0.22.json` `supplementary_series`) was asked,
  as an outside examiner, to name the one methodological weakness none of
  its own directions addressed, and answered with this park's exact ground:
  *"who selected the problems, whose costs define success, and what
  prevents the benchmark from rewarding the programme's own ontology."*
  An independent cross-family arrival on parked territory is convergent
  evidence; DEMAND's unpark case strengthens accordingly.
  **Third arrival (2026-08-27, the v0.23 course).** Series 1's
  **STRANGER'S EXAM** — externally-calibrated refusals — folded into this lane
  as its **calibration upgrade**, recorded in
  `reports/design-direction-v0.23.json` `outcomes.series_1.folds` as *"the
  third independent arrival."* DEMAND now carries **triple convergence**: the
  original park, the v0.22 supplementary examiner's blind-spot answer, and the
  v0.23 series-1 fold. Still parked — it needs a population of askers this
  repository did not author — but three independent arrivals on the same
  missing-population problem is the unpark case accumulating, not a new lane.

- **ABSENCE — snapshot-relative library-absence certificates (2026-08-25).**
  Parked **behind DEMAND**; let demand aim it. Unparking ABSENCE first would
  certify absences nobody asked about.

- **RATCHET — archive-wide monotone-service replay (2026-08-25).** Parked;
  its **pin audit is named as a cheap rider any cycle can run**. HANDSHAKE
  (consumer trust contracts after offline verification) merged into it, and
  donated its refusal-receipt clause to the session-ledger lane.

- **GRAFT — person-taught macros over the registered grammar, reserved
  namespace (2026-08-25).** Parked, and the **transformation is the record**:
  LESSON (refusals that teach) was narrowed under round-two constraints, its
  human-teaching arm cut because it needs strangers, and its **stateless
  half** — macros verified before serving — survived under a new name. Unpark
  alongside a stranger population, i.e. behind STRANGER or DEMAND.

- **IF — checker-signed conditional reductions with a typed null
  (2026-08-25).** Parked; **build the anti-triviality predicate first when its
  turn comes.** Without it every reduction discharges and the instrument
  confirms itself — the same shape as WITNESS's self-comparison clause.

- **TRANSPLANT — a second exact non-math domain port scored by core edits
  (2026-08-25).** Series 1's runner-up, parked **with its one-week core-edit
  probe recorded**: the probe is the cheap version of the whole claim, and
  counting core edits is what makes "it ported" falsifiable.

- **EXHIBIT — meaning by discriminating instance (2026-08-25, declined in
  writing by its own series).** Not parked on a preference: it **builds
  meaning on the layer whose conformance run voided**. Its revival condition
  is recorded and is a schedule item rather than a mood — **a non-void
  conformance instrument ships first**, which is ROADMAP-v0.21 §2 (WITNESS).
  If WITNESS voids, EXHIBIT stays declined with a second reason.

- **RECALL — retraction with exact blast radius.** Not filed separately: it
  **folded back into the twice-parked withdrawal lane** (UNSAY), donating one
  clause to that lane's trigger — **an over-broad impact set counts as
  failure, not caution.** A blast radius that over-reports is not a safe
  default; it is a wrong answer.

## Filed at the v0.20 conformance run (2026-08-25)

> **Reviewed 2026-08-25.** The entries below were filed off the registered run
> and three of them quoted the run's prose rather than its rows. Corrections
> are inline and dated; the run artifact's `post_run_corrections` block is the
> record of authority and `tests/test_conform.py` recomputes it.
>
> **Pruned 2026-08-26 at the v0.21 rotation.** Three entries that this section
> carried are gone because their work shipped, and their record now lives in
> [RELEASE-v0.21.0](RELEASE-v0.21.0.md): the **C-E3 open-term gap** and the
> **C-E3-reached-none-of-the-775** entry, both discharged by
> `experiments/conformance_ce3_supplement.json` (25 of 25 confirmed, and all
> 25 holding over exact rationals — so the agreement prices
> arithmetic-implementation risk, not domain risk, and **discharges no
> correlated-interpretation label**); and **E5 / C-E1's second arm**,
> discharged by `experiments/conformance_e5_late.json` (E5 HOLDS
> byte-identical, dated late). What each entry *asked for* was delivered
> exactly as it specified — own registration, new writer, new artifact,
> `measure_conformance.py` unedited — which is why they close rather than
> carry.

- **C-E1's floor cannot be met by a correct sampler *on some mutation
  classes*, and the control needs two clauses rather than one (2026-08-25,
  narrowed the same day).** The conformance lane's perturbation control froze
  *"at least 99% of skeleton-changing mutations must flip at least one point
  verdict"* and measured **0.650 over 1,027 surviving mutations**, voiding
  every `NO_COUNTEREXAMPLE_FOUND` in the registered run. Part of the cause is
  in the specification: a skeleton-changing mutation need not be falsifiable
  *on the declared carrier*, and `lean_workbook_10012` and `_10039`'s
  `negate_a_coefficient` witnesses are unflippable over `Nat` for a reason no
  sampler can fix. **But part is the instrument**, and it is in the same
  published list: `lean_workbook_10087` mutates `(a-b)^2+(b-c)^2+(c-a)^2 >= 0`
  to `>= 1`, which flips at `a = b = c`, and the sampler drew 73 admitted
  points without finding one. The run has no instrument that partitions the
  two, so **the 0.650 cannot be attributed**. Repairs, both owed to the
  control's own registration: a second discard clause (discard mutations that
  cannot move a point verdict on the carrier), and a partitioned denominator
  so a sampler miss is never again published as a specification defect.
  Also owed and cheaper: `measure_conformance.py:190-192` counts an **errored**
  mutant point as a flip, which biased the 0.650 *upward* — the floor was
  missed despite the bias, and a corrected count can only be lower.

- **The sampler is not carrier-matched, and 78% of M is spent outside the
  carrier (2026-08-25).** Measured in E0f's pilot: of 691,000 candidate
  points, **539,382 were rejected by the declared `Nat` carrier and 51,791 by
  the guards**. The sampler draws from a rational pool with negatives. **A
  carrier-matched sampler is the named successor.** Not applied mid-cycle:
  the sampler is E7-frozen and its own pilot had been read.

  *Corrected 2026-08-25.* This entry originally added *"the effective budget
  per statement is far below M = 1,000 — the registered run's median admitted
  count across its counterexamples is two, and 46.2% of them came from a
  statement admitting exactly one point"*. **Withdrawn.**
  `scripts/conform.py:497` breaks on the first counterexample, so
  `points_admitted` on a NONCONFORMANT record counts admitted points *up to
  and including the falsifying one*; `admitted == 1` means the **first**
  admitted point falsified the statement, which is the sampler's best case
  rather than its worst. The finding stands on the pilot's split alone, which
  is all it ever needed.

- **WITNESS needs a second front-end BEFORE it needs anything else
  (2026-08-26, from W1's pilot — `experiments/witness_pilot.json`).** The
  slice stopped at W1 with **0 of 6 discharged**, and the reason is
  structural: the committed parser emits left-nested **binary** `+` and `*`
  nodes, so `eval_under_domain`'s hoisting is a no-op and *"what the
  evaluator computes"* and *"the statement as written"* are the same tree
  **for every statement inside the fragment**. Every obligation of the
  drafted shape is `P ↔ P` — all 6 drawn, and all 37 census candidates.

  > **Correction (2026-08-25, delta review).** This entry first said the
  > divergent class was *unreachable from the parser*. **It is reachable.** A
  > binary `+` whose first operand is a `neg` diverges (`b - a` for the
  > evaluator, `(0 - a) + b` as written), and the corpus carries **25 such
  > statements, 18 of them compiling** — against **0 n-ary nodes in 86,547**
  > and **0 leading-`inv` products**. What excludes them is the **fragment's
  > linearity predicate**, not the parser, and **0 of the 25 are inside the
  > census population**. The correction makes the entry stronger: the
  > divergent class exists and is non-linear, so a second front-end is needed
  > **before** fragment growth, not merely instead of it. The draft priced the single-front-end problem as a
  **residual risk** (*"a uniform front-end misreading survives every
  clause"*) and put the independent re-reading outside the slice; the pilot
  says that is backwards. **It is a construction prerequisite.** Unpark when
  a design says where the second reading comes from — a second front-end, or
  W2's human transcription promoted from audit to input. Until then WITNESS
  has no obligation with content, and no amount of gate machinery changes
  that. **Carry the counterfactual with the entry, because it is the
  evidence**: handed to `omega` with B4 switched off, the same six
  obligations were **accepted 6 of 6**, which is what an instrument without a
  self-comparison trap would have published as a capability.

- **W0's fragment predicate never asks whether a candidate RUNS
  (2026-08-25, from delta review).** Membership is: compiles, is quantified,
  is linear, and the obligation builder renders both readings. **Nothing
  asks whether the committed compiler admits a single point for it.** One of
  the 37 census candidates — `leanworkbook.skel.lean_workbook_plus_72430` —
  has **zero admitted points** at M = 1,000 and comes back `REFUSED`
  (`guard_measure_zero`), so its obligation would have been **vacuously**
  discharged had the slice opened: B5's nontriviality witness is the clause
  that would have caught it, and B5 is downstream of a manifest that was
  never sealed. Review found **two** such candidates; the C-1 fix removed one
  of them from the population for an unrelated reason, which is luck rather
  than design. **Filed for any reopening, not fixed here**: W0 would need a
  runnability clause, or B5 would need to run at census time rather than at
  discharge time. Fixing it now would be re-scoring a census the pilot has
  already read.

- **A deterministic runner whose artifact does not record its own invocation
  (2026-08-26, found while running E5 late).**
  `scripts/measure_conformance.py` defaults to `--ce1-limit 200
  --ce2-limit 400`; the registered run used **300 and 600**, and *nothing in
  `experiments/conformance_run.json` says so*. The values had to be
  **recovered by matching** `c_e1.statements_examined` and
  `c_e2.statements_compared` against the artifact before a reproduction could
  be attempted. Reproducibility that requires the reader to already know the
  arguments is not reproducibility; §4.0(2) now rests the whole protection on
  *"artifact committed from a deterministic runner"*, which makes this a
  hole in the load-bearing rule rather than a tidiness complaint. **The fix
  is one field** — record `argv` or the resolved limits in the artifact — and
  it belongs to the next writer that registers a run, not to a retroactive
  edit of a sealed one.

- **E4's injection probes cannot exercise the boundary they certify
  (2026-08-25, from review).** `scripts/measure_conformance.py:681` probes
  `[5]`, `[]`, `[0]` and `[7]` — four degenerate constants that all trip the
  same "degree >= 1" length check, and not one of them touches a
  *coefficient*, which is where the declared class actually lives. They
  therefore certified nothing about the defect they were pointed at: before
  2026-08-25 `rational_root_test([Fraction(1, 2), 1])` returned EXISTS with
  the witness `"0"` and `['x', 1]` raised, and the run's
  `all_out_of_class: true` was true of the four probes and of nothing else.
  The procedure is fixed and `tests/test_conform.py` now probes where it can
  fail; **the writer's probe list is deliberately NOT edited**, because it is
  the instrument that produced a scored gate and rewriting it after the fact
  would make this artifact's E4 row unattributable to the code that wrote it.
  Owed by the next registration: probes over the coefficient boundary, frozen
  with the class.

- **The artifact's 775 counterexample rows drop the
  correlated-interpretation label (2026-08-25, from review).** The label is
  emitted on every NONCONFORMANT runtime record
  (`scripts/conform.py:518-526`) and printed on the served answer
  (`scripts/harness.py:2023`), but the writer's projection at
  `scripts/measure_conformance.py:626-631` selects four fields and drops it,
  so `grep -c correlated_interpretation experiments/conformance_run.json`
  over the scored gates returns 0. A **writer defect**: the verdicts were
  labelled and the artifact's copy of them is not. Not backfilled — 775
  scored rows are not editable after the fact — so the repair is in the
  writer, for the next run.

- **A blanket `Nat` class row makes a quarter of the ground class decide at
  `0 = 0` (2026-08-25).** Truncating subtraction takes 69 of the 297 ground
  statements to `0 = 0`, honestly but uninformatively, and 13 more refuse
  because `Nat` has no negation **node** — a negative *numeral* evaluates
  fine, and the distinction is the one `scripts/conform.py:199-216` draws.
  The 69 is recomputed from the committed tree by
  `tests/test_conform.py::TheNatClampFigureIsRecomputable` (added 2026-08-25),
  so this entry's number can be checked; the *pre-fix* 76 lives only in the
  comment at `scripts/conform.py:202-207` and in commit `a58d642`'s message,
  because the clamping code that produced it was never committed. The row is
  right for Correction 4's witness
  and coarse for the class. **Per-statement or per-subclass domain rows are
  the repair**, and they are review work — one row at a time, which is what
  the schema's empty `statement_rows` records rather than hides.

- **The one-equation solve, sized and not built (2026-08-25).** 3,426
  statements are refused as `guard_measure_zero` because their guard carries
  an equality conjunct that rejection sampling never satisfies. The design
  sizes the reachable subset at 1,117 by a single additive rearrangement. It
  is a solver, it changes what the sampler is, and it belongs to its own
  registration.

## Filed at the v0.19 rotation (the foreign voice, and the probes)

- **The parser stores numerals as `float`, and two served statements print
  values that are wrong by 10^59 (2026-08-24, orchestrator's ruling —
  SCHEDULED; **LANDED 2026-08-24 as §4b, CLOSED 2026-08-25 with one residue
  refiled**).** `match_signatures.Parser` builds numeric literals as
  `("num", float(tok))` (`scripts/match_signatures.py:412`, and `:282` for
  the identifier path). Every literal wider than a double's 53-bit
  significand is destroyed at parse time, before any consumer sees it.
  Measured over the committed tree: **7 destroyed literal occurrences
  across 3 nodes — 5 distinct values, 4 lossy and 1 overflowing to
  `inf`.** The `inf` is a 421-digit literal in
  `leanworkbook.skel.lean_workbook_50397`. (A sixth scan hit, `05` in
  `leanworkbook.skel.lean_workbook_plus_43423`, is a **leading-zero
  round-trip artifact and not corruption** — the value survives; noted so a
  future scan does not re-file it.)

  **What makes this worse than a precision note: the wrong value is served
  and it looks exact.** Two ground-class statements return the **right
  verdict with wrong printed values** through the evaluate route today. For
  `leanworkbook.ground.lean_workbook_37421` the served value is
  `-4444444444444444000000000000000000000000000000000000000000000000000000000000`
  against a true `-4444…4444` (76 fours): they agree for **17 characters**
  and then diverge into zeros, an absolute error of **4.4 × 10^59** (a
  60-digit number). It is returned as `Fraction(…, 1)` — an *exact*
  rational type wrapping a value that is already destroyed, so nothing
  downstream can tell. `leanworkbook.ground.lean_workbook_plus_68304`
  (48-digit literals) is the second.

  **The sharp part, and it is an argument for the fix rather than against
  the design.** These are **the same two statements the v0.18 numeral pair
  refuses** as `unsupported_numeral` in `experiments/realization_rate.json`'s
  LOST block. On identical literals, one subsystem **refuses honestly** and
  the other **silently prints a corrupted value**. The realizer's registered
  numeral domain (`|n| < 10^15`) is the behaviour the evaluate path lacks;
  the repository already knows what the right answer looks like.

  > **LANDED 2026-08-24 (§4b), with two corrections to this entry's own
  > numbers.** `match_signatures.Parser` stores INTEGER literals exactly;
  > the three served nodes now print their exact digits
  > (`experiments/exact_literals_served_diff.json`: 0 answer lines moved of
  > 14,830, 3 evaluate-route renderings moved, 0 skeletons moved of 25,554
  > terms).
  >
  > **Correction 1 — the three nodes are not these three nodes.**
  > `leanworkbook.skel.lean_workbook_50397` cannot be repaired by a parser
  > change at all: its `inf` is frozen into the committed
  > `anonymized_template` by `scripts/seed_lean_workbook.py` at seed time,
  > and its `canonical_ascii` does not tokenize (it carries ` : Z)`), so the
  > parser never sees it. **FILED, still open: that node needs a seed
  > regeneration** under AGENTS.md's seeds-are-the-source-of-truth rule —
  > edit `scripts/seed_lean_workbook.py` and regenerate, with
  > `check_regeneration.py`, `validate_nodes.py`, `match_signatures.py`,
  > `decompose.py`, `specialize.py` behind it. It was deliberately NOT
  > smuggled into a parser commit. In its place the served diff surfaced
  > `goedelpset.skel.goedel_pset_789185`, whose served `right` printed as a
  > rounded `1e64`. Three served nodes repaired; not the same three.
  > *(**Promoted 2026-08-25** to its own top-level entry in "Filed at the
  > v0.20 rotation" above. It was the only live work left inside an otherwise
  > shipped entry, and a residue buried in a LANDED blockquote is a residue
  > nobody schedules.)*
  >
  > **Correction 2 — decimals stay `float`, and the reason is measured.**
  > Making them `Fraction` was tried first and the served-line diff refused
  > it: **199 statements LOST their `in words` line**, because
  > `numeral_words.number_to_words` accepts int and float and rejects a
  > Fraction as "not a number". Widening that retires the pinned numeral
  > pair and moves R2's registered numeral domain — a separate decision
  > needing its own registration. **So `float("0.1")` is still not exactly
  > one tenth: an evaluator that must decide `0.1 + 0.2 = 0.3` needs the
  > numeral domain widened first. Filed, not fixed.**
  >
  > **Follow-on (H1, 2026-08-25):** exact ints put an uncaught
  > `OverflowError` on a served route — `f"{value:g}"` raises above a
  > double's range where the float path had already saturated to `inf`.
  > `match_signatures.format_num` guards the three key builders and emits
  > what the float path emitted. A node keyed `inf` still has an
  > unrecoverable literal IN THE KEY; skeletons are a structural index, and
  > widening them is a corpus-wide change with its own seal.

  **Mitigation, stated so the severity is not overread:** this is a
  **display-only** defect — the verdicts are right, no `verified_by` link
  rests on a printed value, and the server is loopback-only and
  single-user. **Scheduled** into [ROADMAP-v0.20](ROADMAP-v0.20.md) §4's
  batched re-seal as **DESIGN-statements-that-run E0's exact-literal
  prerequisite**: an evaluator that decides statements cannot be built on a
  parser that destroys their literals. **Closes when §4's batched re-seal
  lands with its measurement.**

- **`^` is unbounded on a served path, and no measure-relevant subprocess
  call passes a timeout (2026-08-24, orchestrator's ruling — SCHEDULED;
  **LANDED 2026-08-24 as §4c, corrected 2026-08-25, CLOSED**).**
  `scripts/evaluate.py:182` computes `base ** int(exponent)` with **no size
  bound of any kind**. It is reachable from the typed line via
  `scripts/harness.py:1799` and `:1813` (both `computed =
  _route_evaluate(...)`) and therefore over HTTP through `serve_chat`.
  Measured: `(100+1)^1000` produces a **2,005-digit** result in well under
  a millisecond (0.007 ms here), and `2^200000` computes without complaint.

  **The failure mode is not the one you would guess, so it is recorded
  precisely.** The *computation* of a huge power succeeds; what fails is
  **printing** it — Python 3.11+ caps int→str at 4,300 digits, so a
  large-enough result raises an unhandled `ValueError` at render time
  rather than hanging or returning a megabyte of digits. A served path
  whose refusal is an uncaught exception is not refusing; it is crashing,
  and the two are different products.

  **Related, in the same batch:** **none** of the four `subprocess.run`
  calls in `scripts/external_verifier.py` (lines **279, 287, 425, 462**)
  passes a `timeout` — `grep -c timeout` over that file returns **0**. That
  is the file the design cites for its external-verifier lane, so an
  unbounded child process sits under the cost argument that lane rests on.

  > **LANDED 2026-08-24 (§4c), corrected 2026-08-25 after adversarial
  > review.** `evaluate.MAX_RESULT_DIGITS` is 4,300 — CPython's own
  > `sys.get_int_max_str_digits()` — and an oversized result raises
  > `evaluate.ResourceBound`, a named refusal the router serves as a
  > `refused` verdict rather than letting it fall through to a dispatcher
  > abstention.
  >
  > **The first fix did not hold, and the review found it.** §4c bounded the
  > `^` NODE, which is escapable in one line: `(10 ^ 4000) * (10 ^ 4000)`
  > builds two admissible powers and multiplies them, so nothing exceeded a
  > per-node bound and the PRINT raised the same uncaught `ValueError`. The
  > bound now sits at the **result-formatting boundary**
  > (`Evaluation.formatted`, `Verification._fmt`), which every served value
  > passes through by construction; the per-node check is kept so
  > `2^200000` still refuses before the power is built.
  > `experiments/exponent_bound.json` (writer:
  > `scripts/measure_exponent_bound.py`) records both sides EXECUTED:
  > **3 of 6 cases crashed while printing before, 0 after.**
  >
  > `(100+1)^1000` deliberately still SERVES: 2,005 digits, renders, value
  > right. This entry cites it as evidence of unboundedness, not as a
  > defect, and a bound that refused it would decline arithmetic the
  > evaluator can do.
  >
  > The four `external_verifier.py` subprocess calls carry named timeouts
  > (600/60/300/300 s); `grep -c timeout` returns 4. **Side effect worth
  > naming: that moved a digest pinned by `foreign_voice_prereg.json`, so
  > the v0.20 foreign preregistration should record it.**

  **Mitigation:** loopback-only, single user, and nothing untrusted reaches
  either path today — which is exactly why HOSTILE DICTATION is parked with
  a prohibition-shaped trigger (ROADMAP-v0.20 §5) rather than a wish.
  **Scheduled** into §4's batched re-seal as **E0e's resource bound with a
  typed refusal** — a bound that refuses by name, not an exception that
  escapes. **Closes when §4's batched re-seal lands with its measurement.**

- **C-V4 is mis-specified, and the re-specified control is scheduled rather
  than retrofitted (2026-08-24).** C-V4 is C-R2's descendant and inherited
  its mutation idea **without its load-bearing clause**: C-R2 verifies that
  every mutation changes the canonical TERM *before* it is rendered,
  discards the non-mutations, and counts the discards — v0.18 discarded 31
  that way, and the reason it had to was itself a finding (`a < b` and
  `b < a` share a skeleton, so an unverified near-miss set fills with
  non-mutations, every one "fails" to break identity, and the control voids
  a gate for behaving correctly). C-V4 mutates the rendered English and
  requires the elaborated digest to move, but never establishes the
  mutation *should* have moved it — so an unknown share of its
  `did_not_differ` cases may be non-mutations, and `drop_group`'s **0.80
  against a 0.90 floor** is scored against an uncleaned denominator.
  **This does not re-score the v0.19 run**, which is committed as it read
  and stays that way; C-V4′ is a **new preregistration with its own frozen
  digests**, scheduled in [ROADMAP-v0.20](ROADMAP-v0.20.md) §2, and the
  foreign `in words` wiring is gated behind it. Both branches are results:
  a cleared C-V4′ ships a voice, a voided C-V4′ publishes a bound on what
  digest-identity can certify at all. The transferable rule, worth applying
  to any future ported control: **port the discard rule first** — it is
  usually the part that was expensive to learn and the part that looks
  optional. Evidence: `experiments/foreign_voice_rate.json` `c_v4`.
  **Designed (2026-08-24):** [DESIGN-voice-completion](DESIGN-voice-completion.md)
  carries C-V4′ in full — the discard rule restored per mutation, the drawn
  **id lists** pinned rather than the seed (three of the five pools move with
  the grammar), `margin_to_floor` published per class, and `drop_group`
  **demoted to a confirmation** by an exhaustive census that tests every
  grouping-pair deletion rather than fifty. Its wiring rides
  [ROADMAP-v0.20](ROADMAP-v0.20.md) §4 as **4d**.

  > **CLOSED 2026-08-25 by the v0.20 registered run.** C-V4′ ran on its own
  > preregistration and **holds in every voiding class**;
  > `drop_group` reads **42 of 42** against a floor *raised* from 0.90 to
  > 0.95. **And the entry's own transferable rule was confirmed by
  > falsifying its author's prediction**: `drop_ascription` was
  > pre-registered at *"45 of 50 — exactly v0.19's reading"* and measured
  > **45 detected of 45 scored, with 5 discarded as non-mutations.** The
  > numerator held exactly; the **denominator** moved. So v0.19's 0.90 was
  > not five missed near-misses — it was **five mutations that were never
  > mutations**, exactly the failure mode this entry predicted the missing
  > clause would produce. v0.19's artifact is **not re-scored**; it stays
  > committed as it read. Evidence:
  > `experiments/foreign_voice_rate2.json` (`c_v4_prime.per_class`,
  > `c_v4_prime.point_prediction`).

- **`shift_group`'s `of_which_digest_moved` is wrong in a registered
  artifact, and is deliberately not fixed (2026-08-24).** It reads **33**
  where the true value is **0**: the field double-counts the 33 cases where
  the inverse refused. The class's rate of **1.00 is correct** and the
  verdict is unaffected — 49 differed = 33 inverse-refused + 16 elaboration
  errors, and the sub-counts are published separately in the same block, so
  a reader can derive the right number from the artifact itself. **Not
  fixed because fixing means re-running a registered artifact**, and
  re-running a registered run to make one accounting field prettier costs
  more honesty than it buys. If C-V4′ (above) re-runs this measurement
  under its own preregistration, the field is corrected there and this
  entry closes; it must not be corrected in place in the v0.19 artifact.

  > **CLOSED 2026-08-25 on exactly the trigger this entry wrote.** C-V4′
  > re-measured the class under its own preregistration, and the successor
  > artifact carries **no `of_which_digest_moved` field to be wrong**: it
  > publishes an `outcome_histogram` instead — `shift_group` **42 of 42
  > detected, 18 `digest_moved` + 24 `fverr`**, the two sub-counts side by
  > side with nothing summed on the reader's behalf. The v0.19 artifact's
  > field is **not touched**, per this entry's own last sentence. Evidence:
  > `experiments/foreign_voice_rate2.json`
  > (`c_v4_prime.per_class.shift_group`).

- **The release refresh masks its own steps' exit codes through a pipe
  (2026-08-24).** The refresh runs each step piped to `tail`, and a
  pipeline's exit status is the last command's — so when
  `check_regeneration.py` exited **1** on an orphan corpus during the
  v0.19 refresh, the non-zero status was swallowed and the failure was
  visible only because its message happened to fall inside the tail
  window. It was caught by luck, not by the pipeline. **A refresh that
  reports a step's output without reporting its exit code is not checking
  that step**, and the release skill's whole premise is that the refresh is
  a gate. Wanted, and small: `set -o pipefail` or `${PIPESTATUS[0]}`
  captured and printed per step, so a refusal is loud rather than
  legible-if-you-happen-to-look. Filed on the same reasoning as the
  register's two buckets: a check whose failure can go unread is a check
  nobody is running. Evidence: the v0.19 refresh, first pass;
  `docs/RELEASE-v0.19.0.md` "The refresh caught something, and it was not a
  ledger".

- **The capability sheet is silent about the withheld foreign voice, and
  the repo's own convention says it should not be (2026-08-24).**
  ROADMAP-v0.19 §1 planned a `foreign_voice` row quoting B1 from the
  artifact, the way `scripts/serve_chat.py:356-374` quotes the realization
  rate. The void meant the line was never wired, and the row was never
  added — so the string `foreign_voice` does not appear in
  `serve_chat.py` at all and the sheet's 13 `LINE_GRAMMAR` rows do not
  mention the lane. **Absent, not published-as-off**, which is the
  departure: the `gloss` row is the standing precedent for a capability
  the boot turns off, and it ships `"served": false` with a reason rather
  than vanishing. Consequence for the surface this project cares about: an
  attaching orchestrator cannot learn from the sheet that a foreign voice
  exists and is being withheld pending a control.

  **RESOLVED (2026-08-24, orchestrator's ruling): publish the row.** The
  sheet gains a `foreign_voice` row with `"served": false` whose reason is
  **sourced from the artifact**, the way the `realization` row quotes its
  rate rather than restating one in code. This is convention-following, not
  a new policy — `docs/SPEC-chat-completions-skin.md` §7 already says
  *"Rows the profile cannot serve (gloss under offline boot) appear with
  `served: false` rather than disappearing"* — and `gloss` is the standing
  precedent. A fix branch is in flight and merges before the gate. The rule
  that survives for any future withheld lane: **a rate is never published
  from a voided run; the void is.**


  > **LANDED — twice, and the second time is the interesting one.** v0.19
  > added the row `served: false` quoting the C-V4 void (fix/v019-sheet-row).
  > **ROADMAP-v0.20 §4d then found three defects in that row**
  > (DESIGN-voice-completion Correction 7, all confirmed in the tree): it had
  > no code path that set `served: true` AT ALL; it indexed
  > `c_v4["voided_classes"][0]` on a list that is empty when nothing voided,
  > and caught the `IndexError` — so an all-clear run would have been
  > published with the words "its record could not be read"; and it keyed off
  > that control's internal detail rather than the run's own verdict. None of
  > it was tested.
  >
  > 4d rewrote the row around `scripts/foreign_voice_arming.py`, the SAME
  > read `answer.render` uses, so the row and the line cannot disagree about
  > whether a surface exists. **Amended 2026-08-25:** the first arming rule
  > was `overall == "HOLDS" and not voided`, which returns False against the
  > real artifact — the run reads `FIRES` with C-V3′ voided deliberately and
  > non-blockingly by §8 — so the voice would have stayed dark forever,
  > reading a published non-claim as a failure. The gate is now the five
  > cycle-stopping controls (C-G1, C-V4′, B1, B3, B5) plus `FIRES`, and a
  > non-blocking void is published beside the armed surface rather than
  > counted against it. C-V3′ is published as a VOID and never as a number.
  > Evidence: `experiments/foreign_voice_wiring_served_diff.json` — 0 answer
  > lines moved of 14,830, the absent/absent proof the design asks for.

- **`_route_conform` is registered and refusing, and item 1 must not
  reopen the seal to use it (LANDED 2026-08-24, ROADMAP-v0.20 §4e;
  **CLOSED 2026-08-25**).**
  DESIGN-statements-that-run §5's wiring step landed with §4's batched
  retirement so item 1's slice never has to retouch `harness.py`. A
  `conform <statement-id> <bindings>` line is claimed by its own route and
  refused with `missing_capability: tool.conform` until
  `scripts/conform.py` exists — which is a different statement from the
  dispatcher's "the corpus does not ground this", and only one of them is
  true. Measured both sides in
  `experiments/conform_route_before_after.json`. The stub deliberately
  does NOT sketch the conformance record: the design spends its length
  refusing the universal reading such a verdict invites, and a stub that
  guessed at the shape would be the first place that caution got lost.

  **Closed 2026-08-25. Both conditions are discharged, and the second half
  of this entry's title did not survive.** `scripts/conform.py` landed
  (commit `a58d642`) and the sheet row flips to `served: true` against the
  registered run (commit `4506f83`; pinned by
  `tests/test_serve_chat.py::test_the_conformance_row_is_served_and_quotes
  _no_rate`). But the seal *was* reopened: moving `_route_conform` from
  refusing to answering changes `harness.py`'s rendered bytes, so `4506f83`
  rebuilt `experiments/throughput_tasks.json` — one leaf,
  `/rendering_module_digests/scripts/harness.py`, everything else
  byte-identical. This entry's hope that the batched retirement would make
  that unnecessary was wrong on the timing: the wiring had to follow the
  registered run, and §4's retirement was already behind it.
  `docs/SPEC-chat-completions-skin.md:237–258` governs and outranks the
  convenience, `DESIGN-statements-that-run.md` §8.1 now carries the dated
  amendment saying so, and §8's "no throughput claim" is unweakened — a
  timed comparison still starts a fresh seal cycle.

- **`probe_convention_pairs.py` has no argparse and writes on every
  invocation (2026-08-24).** `main()` takes no argv and calls
  `write_report()` unconditionally, so
  `python scripts/probe_convention_pairs.py --help` does not print help —
  it **ignores the flag, runs the full probe, and overwrites
  `experiments/convention_pairs_probe.json`**. Worse on Windows: without
  `PYTHONIOENCODING=utf-8` it crashes on a `≥` in the
  "top discriminator subterms" print and exits 1 **after** the file is
  already written, so the failure looks like a refusal and is not one. The
  probe is byte-reproducible (verified: a clean re-run leaves `git status`
  clean), so nothing is lost today — but every other registered runner in
  this repository has `--out`/`--no-write` and refuses rather than
  clobbers, and this one is the exception. Wanted: `--out` with a default,
  `--no-write`, and the print guarded. Small, and worth doing before
  anyone treats a re-run as a read.

- **`transliteration_served_diff.json`'s `digests.note` describes the
  wrong scope (2026-08-24).** It reads "The two differ exactly because
  lines were gained", but the two digests it annotates are **identical**
  (`b838ab54…` both) because that block is scoped to the 30
  `corpus_definition` task-book tasks, where `gained` is 0 — the book's
  tasks carry neither glyph. The note was written for the
  `corpus_wide_reading` block (6,414 gained) and sits beside the
  task-scoped one. **No number in the artifact is wrong; the sentence
  is**, and it invites a reader to quote `claim.gained: 0` as the lane's
  result, which would be a category error. Reported and **not fixed**, on
  the same rule as `shift_group`'s field: a registered artifact is not
  edited to read better. Correct it in the successor artifact if this
  measurement is ever re-run under its own preregistration.

- **Should the renderer emit a canonical bracketing at all? (2026-08-24)**
  The question `drop_group`'s void raises and that nobody has asked this
  repository. Two readings that want different work, and the cycle must not
  guess between them: either **the rendering is over-parenthesised**, in
  which case `drop_group` is detecting real redundancy in the surface and
  the fix is a minimal-bracketing rule with its own round-trip proof (the
  shape v0.18's five-level ladder already uses on the native path); or
  **the redundancy is load-bearing for a reader**, in which case a bracket
  elaboration erases may still be what makes a sentence readable aloud, and
  removing it makes the surface worse. **The honest first step is a
  measurement, not a change**: over the covered set, count how many
  grouping words the grammar emits that the term does not require, and
  publish the distribution before anyone proposes a rule. Registered as a
  probe in ROADMAP-v0.20 §3; both branches yield an artifact.

  > **CLOSED 2026-08-25 — the first reading, measured, and the second one
  > split out rather than absorbed.** The probe ran and published **before**
  > any rule was proposed, and git proves the ordering:
  > `experiments/grouping_census.json` landed at `4d09d95`, the canonical
  > renderer at `4fbcfb2`. It reads **604 redundant grouping pairs of 5,832
  > source pairs** (620 of 6,063 counting the 16 binder-group pairs stripped),
  > **1,208 of 11,664 emitted grouping words removed (10.36%)**, and **435 of
  > 2,313 covered surfaces change**. The over-parenthesised reading was true, and
  > the repair followed: `experiments/grouping_agreement.json` turns the
  > sampled question into an exhaustive one — **G1b, 5,228 of 5,228
  > grouping-pair deletions detected, zero blind**. **The second reading is
  > not closed with it**: whether the redundancy is load-bearing for a
  > *reader* is unanswered, and it is refiled as its own entry parked behind
  > C-V3 (above), because closing a two-branch question on one branch is how
  > the other branch disappears.

- **1,706 of the register's 1,878 blocked statements are a budget, not a
  design limit (2026-08-24).** The frozen register's two buckets are
  reported separately and **never summed**, because they are different
  kinds of fact: `registered_blocked_mathlib_head` (**1,706** — namespaced
  and bare Mathlib heads, and the `√` notation) is a **budget consequence a
  maintainer can lift** by paying for Mathlib coverage, while
  `registered_blocked_no_row` (**172**, across six named construct classes)
  is a **design consequence this cycle owns**. Filed rather than scheduled
  because lifting the first is a resourcing decision, not an engineering
  one — and filed at all so that a future reader does not find "1,878
  unsupported" and conclude the ceiling is structural. Merging the two
  numbers is the one thing this entry exists to prevent. Evidence:
  `data/foreign_voice/register.json` (`blocked_set_digest` `e51e5675…`,
  frozen in `297d1ea` before anything was rendered).

- **A six-statement gap between oracle-eligibility and coverage, recorded
  before someone finds it (2026-08-24).** B0b+c accepts **2,319**
  statements by oracle-eligibility while B1 covers **2,313**, and the
  register blocks **1,878** against B0b+c's **1,872** rejections. The
  difference is the two filters being different questions: a statement the
  oracle can *reach* may still carry a head with **no lexicon row**. The
  published arithmetic closes on the coverage partition (2,313 + 1,706 +
  172 = 4,191 residue; B3 closes at 10,605), which is the partition every
  quoted number uses. Filed as a reading note rather than a defect — but
  the artifact does not reconcile the two counts in place, so the next
  cycle to touch this should either state the relationship in the artifact
  or drop the eligibility count from the published gate line.

## Filed at the v0.18 rotation (sans-template rendering)

- **The realized surface cannot say a variable's name, and that is the
  biggest thing it cannot do (2026-08-23).** `canonicalize` erases slot
  identity, so every realized sentence says **"variable zero"** where the
  source says `x`. Registered honestly in
  `docs/DESIGN-sans-template-rendering.md` §8 as a non-claim before the run
  rather than discovered in the output. The source identifiers *do* ride in
  the receipt (`parameters.surface_slot_names`), so the information is not
  lost — it simply is not served. **Why this is not a small fix:** an
  identifier surface must be **R2-gated**, and R2's rule is that every
  content word traces to a lexicon row or the registered numeral pair.
  Corpus identifiers are neither. Admitting them means either a third
  registered source with its own injectivity and prefix-freeness
  obligations (`x` must not collide with a lexicon phrase or a numeral
  word), or a scheme that quotes them as opaque spans the reader can
  recover. Both are designs, not patches. Wanted before anyone tries: a
  count of how many distinct identifiers the parseable set actually
  carries, and a check on whether any of them collide with the 169 phrases
  already in the table.

- **`±` has a lexicon row that no committed statement exercises
  (2026-08-23).** The operators section carries six rows and `±` is one of
  them, but nothing in `data/` uses it, so the registered run's 2,170
  served surfaces never touch it. Review caught this and pinned
  `x = a ± b*c` EXACT by hand (L4) so the row is not merely decorative —
  but a hand-pinned case is a weaker guarantee than corpus exercise, and it
  is worth knowing this row is in that category. Two honest options when it
  next matters: author a statement that uses it, or move the row out of the
  table and let `±` refuse as an uncovered head until something needs it.
  Do not treat the current green test as coverage.

- **The parser collapses the conditional bar, and the realized sentence
  inherits that (2026-08-23).** `E[Y|X]` reads as a two-argument
  expectation and round-trips as one, so the surface renders the bar as
  "next argument". The distinction survives in the source term and is lost
  in the sentence. Registered as a non-claim in the design's §8 rather than
  left to be discovered by a reader of conditional-probability statements.
  This is a **parser** limitation surfaced by the renderer, not a renderer
  bug, and fixing it means touching `match_signatures.py` — which is
  digest-pinned as the realization gate's stage-2 parser, so it inherits
  the whole re-freeze discipline in ROADMAP-v0.19 §3a. Filed together with
  the transliteration lane because they are the same file and the same
  discipline.

- **The transliteration lane: two glyphs reach half the corpus, and the
  seal will not notice (2026-08-23).** Grounding for the v0.19 course
  measured that **6,414 of the 10,605 mute statements — 50.2% of the whole
  corpus — parse under the byte-frozen committed parser after substituting
  exactly two glyphs**, `≥`→`>=` and `≤`→`<=`. Scheduled as a registered
  probe in [ROADMAP-v0.19](ROADMAP-v0.19.md) §3a on v0.18's existing native
  path, deliberately **not** as a headline, because the preview makes it
  look easy and easy is what a register exists to keep honest. **Read the
  re-freeze discipline in that section before touching the tokenizer.** The
  part worth repeating here, because it is the part a green test would hide:
  `scripts/match_signatures.py` is **not** in the task book's
  `rendering_module_digests` (that witness lists eleven modules and this is
  not one of them), but widening the tokenizer changes *which* terms parse
  and therefore changes what `answer.render` emits — **rendered output moves
  while every witnessed module digest stands still.** The lane owes an
  explicit before/after diff of served answer lines, committed with the
  probe. Evidence: `docs/DESIGN-foreign-voice.md` §1 Correction 1 (a
  document under adversarial review at the v0.18 rotation — the figures may
  be restated with a dated correction).

  **v0.19.0 status note (2026-08-24): RESOLVED by shipping, and the
  discipline held.** The lane ran as a registered probe: parse rate
  **2,172 → 8,586 of 12,777 (17.0% → 67.2%)**, 6,414 newly reached against
  a pre-committed floor of 6,000, round-trip **6,414 of 6,414 (1.0000)**
  over the newly-reached set. The grounding figures were confirmed exactly,
  so the "may be restated" caveat above is discharged rather than
  outstanding. **The warning this entry existed for was the load-bearing
  part and it was answered**: the served-diff witness loaded the retired
  parser out of git in its own interpreter and diffed every rendered line
  over all 12,777 statements — **6,414 gained, 2,170 byte-identical, 0
  changed, 0 lost**, corpus-wide additive-only, with the witness's `gained`
  agreeing with the run's `newly_reached` at 6,414 exactly. The rest of the
  discipline executed whole: the amendment landed **before** the code, both
  parser pins were retired for future comparisons, both prior rates were
  declared **historical in writing** (v0.18 was not re-run, with the reason
  recorded), and **both old registered CLIs were closed** so neither can
  mint a rate blended across two parsers. Kept here rather than pruned
  because the witness-gap argument is the reusable part: the next cycle to
  touch a parser inherits it. Composition caveat that travels with the
  number: **one corpus, two distinct call heads** — it is not a
  lexicon-coverage claim. Evidence:
  `experiments/transliteration_rate.json`,
  `experiments/transliteration_served_diff.json`.

- **STRANGER — outside-asker gap-object intake, parked from the v0.19
  course (2026-08-23).** One of the fifteen round-one directions: outside
  askers score the system's answers *and its refusals*, and the gaps they
  find become first-class objects the graph can hold. Declined at selection
  and parked here with its degradation rule quoted from the course receipt
  rather than summarised away. Unpark condition, from the same receipt: it
  needs a population of outside askers whose questions were not authored by
  this repository, which is the same fresh-half problem the veto census and
  the clarification holdouts both hit — so it does not unpark on
  enthusiasm. Evidence: `reports/design-direction-v0.19.json`
  (`selection.declined.STRANGER`).

## Filed at the v0.17 rotation (grounded throughput)

- **The context probe reads `/api/ps` before the model is loaded, so it
  reports a capability as a setting (2026-08-22).**
  `scripts/measure_throughput.py`'s context probe queries `/api/ps` for the
  served context of the loaded model and falls back to `/api/show` when no
  loaded model reports one. On the registered B-grounded arm the model was
  not yet resident when the run started, so `/api/ps` came back empty and
  the fallback wrote **262144** — the model's *capability* — into
  `experiments/throughput_result_bgrounded.json`'s
  `materials_fit_bound_tokens`. The served context was **32768**, which the
  same file proves five times over: five `closure_reachability` tasks
  return HTTP 400 reading `request (130475 tokens) exceeds the available
  context size (32768 tokens)`. Consequence, bounded: only the
  pre-declared *secondary* median is affected, and recomputing it over the
  recorded `materials_tokens` at the true bound gives **0.0 over 44 tasks**
  — identical to the unrestricted median, verdict unchanged (ANALYSIS,
  v0.17 §"the grounded arm's secondary median, corrected in writing").
  The code was deliberately **left exactly as it ran**: a graded run is not
  re-executed to make its own file prettier. Wanted: probe after the warmup
  request rather than before it, and refuse the `/api/show` fallback for
  any field the result labels *observed* — `cannot-verify` is the honest
  reading there, per the WordNet-archive rule the tokenizer pin already
  follows. Evidence: `experiments/throughput_result_bgrounded.json`
  (`context_probe`, `summary.materials_fit_bound_source`, the five 400s in
  `per_task`).

- **`_route_ownership` throws away the object its own receipt needs
  (2026-08-22).** `scripts/harness.py:1052` runs the expensive
  `ownership.lookup`, renders it, and returns only the rendered string — so
  `serve_chat._ownership_receipt` must run the identical lookup a second
  time to cite the host set, roughly doubling the cost of the most
  expensive route on the surface (~3.4 s for `owns x ^ 2` — **measured
  2026-08-24, see the LANDED note below; this sentence used to say "not a
  committed timing artifact" and that is no longer true**). The skin
  mitigates with an
  `lru_cache` on the pure function rather than monkeypatching the engine,
  which would be the renderer editing the record. **Why the real fix was
  declined rather than missed:** `harness.py` is one of the eleven
  seal-witnessed rendering modules, and until the registered run completed,
  changing it would have voided the run. The fix now: have
  `_route_ownership` return the answer object (or its host set) in the
  verdict alongside `"answer": render(answer)`, and drop the cache — and it
  must ride a book **re-seal** under the spec's §6 rule, since after the
  registered run a witnessed-module change voids nothing but still moves a
  digest. Related consequence, same root: replayed prefix turns pass
  `with_receipt=False` (`scripts/serve_chat.py:815`) precisely to avoid a
  whole second corpus scan per replayed turn.

  **v0.18.0 status note (2026-08-23): still open, and the excuse has
  lapsed.** This is now the entry's second cycle. The reason it was
  declined at v0.17 — that `harness.py` was seal-witnessed by a run still
  in progress — no longer holds: the v0.17 run is closed and its numbers
  are frozen against their own artifact. What remains is that the fix moves
  a witnessed module's digest and therefore rides a book **re-seal**, and
  v0.18 has now made that procedure routine rather than novel (`5357740`
  retired the v0.17 witness and sealed a successor book, verified by
  structural diff: exactly one leaf moved). So the cost of doing this
  correctly is known and small. It is carried, not parked — but a third
  cycle without either the fix or a written decision to stop caring is the
  shape this file exists to catch, and the ~3.4 s figure above still has no
  timing artifact behind it, so **measure before spending**.

  **v0.19.0 status note (2026-08-24): third cycle, and DECIDED —
  SCHEDULED.** The v0.18 note named this exact situation one rotation ago:
  a third cycle without either the fix or a written decision is the shape
  this file exists to catch. The orchestrator's ruling of **2026-08-24** is
  **SCHEDULED**, not closed — the land-or-close clause is discharged by a
  landing plan, written up as **[ROADMAP-v0.20](ROADMAP-v0.20.md) §4** and
  carried in that roadmap's release gate.

  > **LANDED 2026-08-24 (ROADMAP-v0.20 §4a, `feature/v020-batch`), and the
  > three-cycle claim is now measured.** `_route_ownership` returns its
  > receipt in the verdict dict, matching `_route_twin` and
  > `_route_reachable`; the skin's `lru_cache` is gone. The artifact is
  > `experiments/ownership_receipt_timing.json`, written by
  > `scripts/measure_ownership_receipt.py`, and it carries **two** numbers
  > because the obvious measurement measures the wrong thing:
  >
  > - **distinct queries — the number the entry was about: 7208.8 ms ->
  >   3901.5 ms (1.85x, 3307 ms removed per turn).** Ten different `owns`
  >   lines, so the memo can never hit; this isolates the duplicate lookup.
  > - **the same query ten times: 3531.2 ms -> 3450.6 ms (1.02x).** Run as
  >   §4a literally specified, this warms the very `lru_cache` the fix
  >   removes, so nine of ten reps never paid the second lookup even before
  >   the fix. Kept, because it is a true statement about the shipped
  >   server — and reported beside the other, because quoting either alone
  >   misdescribes the fix.
  >
  > So the `~3.4 s` was roughly right about the SINGLE lookup (3.53 s
  > measured) and the cost this entry was really about — the duplicate —
  > was 3.31 s on top of it. Answer bytes and receipt contents are
  > identical on both sides, which is the part that would have made a
  > faster number worthless. Seal paid in §4's one batched retirement.

  The plan, so this entry and that one cannot drift apart: have
  `_route_ownership` return the answer object (or its host set) in the
  verdict dict alongside `"answer": render(answer)`, **matching the
  convention `_route_twin` and `_route_reachable` already follow**, and
  drop the `lru_cache`. It owes a **before/after measurement** — the
  `~3.4 s` above has now been quoted across three release cycles without
  ever acquiring a timing artifact, which is the small version of the drift
  this file catches, so the fix either publishes a real number or retires
  the claim — and it pays its **new-seal cost under the standing witness
  rule**, since `harness.py` is a witnessed rendering module. Two cycles
  have made that procedure routine (v0.18 retired the v0.17 witness; v0.19's
  transliteration lane retired two parser pins), so the cost is known and
  small. Placed early in v0.20 because it is small and because a fourth
  cycle of carrying it is the outcome the ruling exists to prevent. This
  entry closes when §4 lands with its measurement.

  > **CLOSED 2026-08-25 at the v0.20 rotation.** §4 landed with its
  > measurement — the LANDED note above is that measurement — so the
  > condition this entry set for itself is discharged and the entry stops
  > carrying. Three cycles from *"roughly doubling the cost of the most
  > expensive route"* to a committed artifact, and what closes it is not the
  > speedup: it is that **an unmeasured number quoted across three releases
  > now has a file behind it**, with the honest 1.02× arm published beside
  > the 1.85× one so neither can be quoted alone. Not a performance claim,
  > by the artifact's own words.

- **The B-side correctness rule is notation-limited on session-derived
  kinds, and that asymmetry is scoring, not capability (2026-08-22).**
  `belief_query` and `exact_value` tasks hand the contender no materials,
  and their checks require the kernel's own notation — `located_in(x) =
  place`, exact fractions — which a prose model rarely emits unprompted.
  Recorded in `experiments/throughput_baseline.json`
  (`arms.B-grounded.session_derived_kinds_note`) **before** the run rather
  than discovered after it, and the per-kind results are published so a
  reader can weigh it. It did not change the v0.17 verdict — the contender
  scored 0 of 16 on `corpus_definition`, a kind where it *was* handed the
  material verbatim — but any future cycle that quotes the B-side number
  owes this entry a citation. What would discharge it: a registered
  notation-normalizing check authored **before** its run, with a control
  showing the normalizer cannot manufacture agreement, plus a fresh half.
  Do not normalize against these spent tasks.

- **The input side has no synonym layer, and the realization lexicon is the
  first candidate that would not be a patch (2026-08-22).** The corpus
  writes `gcd`; people write "greatest common divisor". DESIGN-text-resolution
  §4 names the residual and its §7 records the refused lexical-semantics
  route (the morphology trade failed at 0.034 against a 0.030 ceiling and
  was reverted). `DESIGN-sans-template-rendering` §10 names the successor
  question in the right order: **if R1 fires**, the committed
  operator/constant lexicon — reviewed, bijective, and by then measured —
  can be asked whether it runs backwards as a synonym layer for the
  resolver. Parked deliberately behind that condition, and behind the v0.15
  standing rule that the resolver coverage lane unparks only with a
  mechanism justified independently of the score it would move. Note the
  boundary the design states rather than discovers: the realizer's stage-1
  inverter *is* an open-English reader, however narrow — it reads only
  strings the realizer itself produced, is not offered on the input side,
  and no request route calls it.

## The gate is one test, and now it is measured

- **`test_corpus_analogy_split.ControlTests.test_no_blind_control_can_see_the_answer`
  runs for 1 hour 34 minutes.** Measured with `scripts/time_tests.py`:

  | | seconds | share of module |
  |---|---:|---:|
  | `test_no_blind_control_can_see_the_answer` | **5,619.8** | 52% |
  | class fixtures (`setUpClass`, untimed) | ~4,700 | 44% |
  | 3 determinism / verification tests | ~445 | 4% |
  | the remaining 41 tests | ~1 | ~0% |
  | **module total** | **10,765** | |

  That single test is roughly **16% of the entire 592-minute serial gate**,
  and 41 of the module's 45 tests together cost about one second.

  **Three earlier explanations were folklore and are retracted here**: not
  "several tests reload the 12k graph" (four modules do, and they cache),
  not "the eight torch modules" (this module contains no torch), not imports
  (all 21 shard-0 modules import in 1.7s; `test_ask` runs 25 tests in
  0.013s).

  **Two independent costs, and they need different fixes.** The 5,620s test
  is a blind-control sweep — it exists to prove no capability-blind arm can
  see the answer, which is exactly the kind of guard this project should
  keep. Making it cheaper means sampling the control space with a registered
  argument about what sampling costs, not deleting it. The ~4,700s of class
  fixtures is separate, invisible to per-test timing, and untouched by any
  amount of test-level speedup.

  Wanted, in order: (1) time the whole suite per module now that the tool
  exists, so sharding can be balanced rather than round-robin — v0.12's
  split gave 5.8m / 186.6m / 319.7m for a 1.85x speedup where balance would
  have given close to 3x; (2) decide whether the blind-control sweep can be
  sampled; (3) find what the fixtures are doing.

  Evidence: v0.12 gate, 1,240 tests, 592m serial / 320m across three shards.
  `python scripts/time_tests.py --json t.json tests.test_corpus_analogy_split`

  **Receipt limitation:** the original 10,765-second command output was
  observed and recorded in commit history and this ledger, but its JSON file
  was not retained. These numbers are therefore human-readable evidence, not
  a byte-pinned raw timing asset. Reproduction costs roughly three hours on
  the recorded host. Do not infer balanced per-module shard weights from this
  one module; the whole-suite per-module pass in item (1) remains open.

  **v0.16.0 status note (2026-08-21):** wanted-item (1) — whole-suite
  per-module timing — is **DISCHARGED**, and twice: `reports/test_gate_v015/`
  and `reports/test_gate_v016/` both carry byte-pinned per-module receipts,
  so the "receipt limitation" above is superseded for those runs. Current
  numbers: the v0.16.0 gate is **1,427 tests / 20,837.8 s**, of which
  `test_write_stage` is 12,008.7 s (57.6%) and `test_corpus_analogy_split`
  is 4,569.1 s (21.9%) — v0.15 read 1,381 tests / 20,521.7 s. The blind
  control is now **4,289.6 s** inside `test_corpus_analogy_split`'s
  4,569.1 s module, so the 5,619.8 s / 10,765 s table above is an
  as-of-v0.12 reading, not a current one. Wanted-items (2) sampling the
  blind control and (3) accounting for the fixtures remain open.

## Parked at the v0.15 drift audit

Two goals were found lost to attrition rather than decision — v0.14
re-scoped the ambiguity lane to `when_to_ask` and nothing recorded what
that dropped. Converted to parks here so the loss has an owner and an
unpark condition.

- **The v0.13 ambiguity acceptances A3, A4, A5 are parked, not dropped.**
  A3 (every restatement is verbatim corpus), A4 (the Buffalo bar: enumerate
  the readings and name the one taken), A5 (coverage does not pay for it)
  were the ambitious half of DESIGN-ambiguity-and-context and were never
  scored; v0.13 published that honestly and v0.14's re-scope silently
  inherited their absence. Unpark condition: a successor clarification
  holdout designed after the verified-ambiguity construction check (also
  parked here) exists, because v0.14 proved that authoring ambiguity rows
  on belief measures the author. A2's own park (authored-after-the-fact
  follow-ups cannot recover it) stands separately.

- **The resolver coverage lane (the 0.833 / 0.030 point) is parked as a
  decision, not a hope.** v0.13 closed its coverage item correctly on a
  published trade; no roadmap since has owned moving the number, while
  three cycles improved the instruments around it. Recorded at v0.15:
  the lane unparks only with a mechanism justified independently of the
  score it would move (the standard the morphology trade already failed),
  and any future roadmap that claims resolver improvement owes this entry
  a citation.

## v0.13 conversational coverage: rejected morphology trade

- **SUSPENDED: the published cross-field match count is not a result.**  The
  matcher reports 975 typed twin groups, 34 of them spanning more than one
  namespace, and that figure has been cited as an achievement without ever
  being adjudicated against a two-sided prediction.  Shape collisions are
  cheapest exactly where the corpus is most formulaic, which is where most of
  the count comes from.  Until
  [the coincidence veto](DESIGN-coincidence-veto.md) reads out, or two release
  cycles pass, the number does not appear in release notes or in any evidence
  chain; it may appear in ANALYSIS with its denominator and this suspension
  named.  Same failure shape as the v0.14 clarification benchmark: a belief
  about the collection filed on the achievement side of the ledger.
  **v0.15 status: extended, not lifted.**  The veto's first adjudication was
  partial — two controls passed, the tag-permutation control invalid by an
  authoring-time scoping defect — and eight of twenty-six groups contain a
  conflicting slot.  ROADMAP-v0.16 item 2 is the decision point: the claim
  is established there, or the suspension expires at that release by this
  entry's own two-cycle clause, with the sensitivity analysis's one-row
  finding attached wherever the count is quoted.
  **v0.16 status: LIFTED, by its own read-out clause, with two permanent
  riders.**  The permutation control passed against a blind-authored full
  cross-product table it cannot starve (real 21 vs permuted 45–61; the
  blind author independently reproduced the proposition|set exemption).
  The count may now be cited — always with the conflicting readout (8 of
  26 groups) and the one-row finding beside it.  Established exploratory:
  the census has no fresh half, and the label stays.  Readout: ANALYSIS
  "the veto's information claim, established blind";
  `experiments/veto_full_cross_result.json`.

- **Range is uncertified while domain is certified.**  Committed digests prove
  that these sources produce this artifact byte-for-byte.  Nothing proves that
  the function from question to outcome is unchanged, so adding statements can
  pass every regeneration check truthfully while silently moving an answer
  nobody was looking at.  A sealed replay set reduced to a moved/unmoved bit
  would certify it.  Parked behind its own prerequisite: evidence that the
  range actually moves, since predicting churn from the source diff may
  explain most of it for free.  Raised by the v0.15 design inquiry.

- **`ceiling_table` is the split module's remaining duplication.**  The
  corpus/quadruple fixture went module-scoped at v0.15 (`fa0a174`; the
  1,076 s of per-class duplication is gone by construction), but
  `ControlTests.setUpClass` still spends ~2,179 s computing `ceiling_table`,
  and that cost was not touched.  Whether it can be cached, sampled under a
  registered replacement, or is simply the honest price of the control is
  unexamined.

- **`test_write_stage` is the release gate.**  Still the floor, at a lower
  number: the v0.15 registered reorder (`afafbc4` + `82aef3e`) made refusal
  O(1) — the worst test fell 1,096.4 s → 46.2 s and the module 12,522.5 s →
  10,770.9 s — but only the seven declared-delta refusals were paying for a
  corpus pass, so the module remains the serial floor of the suite and the
  parallel ceiling is unmoved.  It must not be sampled or trimmed without
  the same registered-replacement rule that protects the blind control.
  Evidence: `reports/test_gate_v014/` (v0.14 baseline), ROADMAP-v0.15 §3
  live status (v0.15 numbers), and the v0.15.0 release-gate timing receipt.

  **v0.16.0 status note (2026-08-21):** ~~10,770.9 s~~ was the *indicative*
  number and has since been retracted — it was not measured like-for-like
  against the 12,522.5 s baseline. Measured like-for-like, v0.15 reads
  **12,133.3 s** (a −3.1% reorder gain, not −14%), and the v0.16.0 gate
  reads **12,008.7 s**. The claim the entry makes is unchanged and if
  anything stronger: `test_write_stage` is still the serial floor, now
  57.6% of a 20,837.8 s / 1,427-test suite. Evidence now also
  `reports/test_gate_v015/` and `reports/test_gate_v016/`.

- **The outside design inquiry cannot be isolated on this platform, and the
  reason is not the tool list.**  Both previously unverified questions are now
  settled and both failed.  `tools: []` is read as unset, so the registry
  grants the agent every tool.  More decisively, an isolation probe found that
  a subagent's context carries the repository name and absolute path, the git
  branch and the five most recent commit subjects, the user's persistent
  memory index with prior-version direction and metrics, the user's name and
  email, and the session scratchpad path — none of which an agent definition
  can suppress, because the harness injects them.  One of those commit
  subjects names the incumbent forward direction, which the skill requires to
  be withheld from the outside agents, so the leak defeats the gate's purpose
  and not merely its letter.  Unblocking needs a context with no project,
  environment, git or memory injection; or the three inquiries run on a system
  that has never seen this repository, with only the brief and the replies
  carried back; or a maintainer decision to change what the gate requires.
  The vendor documentation confirms both halves and closes the question:
  *"There is no way to explicitly grant a subagent NO tools at all through
  frontmatter configuration"*, and a non-fork subagent *"receives every level
  of the CLAUDE.md hierarchy the main conversation loads"*, which only the
  built-in Explore and Plan agents skip and no field controls.  So this is a
  property of the platform, not a misconfiguration, and no restart or
  frontmatter change lifts it.  Two levers do exist should the gate ever be
  relaxed rather than met: `disallowedTools` can remove network and file
  access, and `includeGitInstructions: false` removes the git snapshot — and
  with it the commit subject that names the incumbent.  Neither can remove the
  project instructions.  A dialect-free brief is drafted and hashed and can be
  reused when a channel exists.  Evidence:
  `reports/design-direction-v0.15.json`.
  **Resolved in practice:** the channel now exists and has run twice — `claude
  -p` headless from an empty non-git directory whose path names no project,
  with `--strict-mcp-config` and a full tool denylist, one fresh session per
  series continued with `--resume`.  The residual gap (tools blocked rather
  than absent) is recorded in each receipt.  Kept here as the platform record;
  the working recipe lives in the forge skill and the receipts
  (`reports/design-direction-v0.15.json`, `reports/design-direction-v0.16.json`).

- **The gate measurement cannot run in the canonical checkout.**
  `time_tests.assert_clean_source` refuses when any gitignored `*.py`, `*.pyc`,
  `*.pyd`, `*.so` or `*.dll` sits outside `.venv/`, and `.worktrees/` is
  gitignored — so every sibling worktree AGENTS.md tells us to create, plus the
  stray `leandojo-scratch/venv`, trips it.  `plan_test_shards.py measure` also
  refuses an `--out-dir` inside the worktree it measures.  Both refusals are
  right and neither should be loosened; the consequence is that the run needs
  a detached checkout of the exact tip outside the repo, with `--out-dir`
  outside that too, invoked with `PYTHONDONTWRITEBYTECODE=1` so the parent
  process does not dirty what it is measuring.  Writing it down because it
  cost two failed starts to derive and is not documented anywhere.

- **v0.14's ASK stratum mostly measured a prediction, not a resolver.**  Of
  the 20 rows predicted to ASK, 8 bound directly to the intended id, 5 bound
  elsewhere, 3 passed on vocabulary the graph lacks (`figure`, `sided`,
  `nested`, `among`), and 4 asked.  The 18 rows not predicted to ASK scored
  18/18 recall.  Q2 scored "right without needing to ask" identically to
  "wrong", which is the metric's defect and not the resolver's.  At least one
  wrong bind is a row-authoring error: A-08 asked for "story constraint on
  setup and payoff" and the resolver returned `chekhov_gun`, which is that
  constraint, against an intended `no_deus_ex_machina`.  A successor metric
  needs a category for a correct bind on a row that predicted ambiguity, and
  a successor stratum needs rows whose ambiguity is verified in the graph
  before authoring rather than assumed.  Evidence:
  `experiments/when_to_ask_result.raw.json`.

- **Q4 was unfireable as registered.**  The mechanical precision arm never
  enters the candidate's masked path, so the clause measured the untouched
  baseline and reproduced it (pooled 0.03467 vs v0.13's 0.034).  Future
  preregistrations need a construction check that each shipping clause has a
  causal path from the intervention to its number; the current validator
  checks rows, ids, freshness and provenance but nothing about whether a
  prediction is reachable.  Evidence: v0.14 Q4 and DISCOVERIES.

- **Negative rows need to be decided by their negation, not merely to contain
  one.**  Q6 reached 1/16.  Seven of eight `negative_bind` rows bound
  correctly with the veto inert, so the stratum tested the resolver's ordinary
  competence and only incidentally the exclusion.  A successor stratum should
  require, at construction time, that the stripped query bind a vetoed id —
  which is checkable from committed metadata before any candidate exists.

- **Clarification is only tested against one intended reading.**  All 20 v0.14
  ASK rows declare a singleton `retained_ids`, and the validator's 58-credit
  shape refuses a multi-id set outright.  Q2 therefore cannot show that a
  follow-up preserves several simultaneously acceptable readings — the case
  where narrowing is most likely to discard one.  Evidence:
  `experiments/when_to_ask_holdout.json` and the v0.14 ANALYSIS entry.  A later
  cycle authoring multi-id retained sets needs a new holdout, not an edit to
  this one.

- **Morphology cannot ship on the measured precision trade.** The preregistered
  third holdout reached 24/24 under the closed-form surface expansion, but the
  fresh pinned-OEWN F4 arm claimed 34/1000 = **0.034**, above the 0.030 shipping
  ceiling. The resolver change was reverted, not tuned against either spent
  set. Unpark only with a new mechanism justified independently of these rows,
  plus a fourth registered holdout and a fresh mechanical seed.
- **Negative contrast is invisible to word overlap.** `interest accumulated
  without compounding` confidently bound
  `economics.finance.continuous_compounding`; a reach-only score counted it as
  covered while registered-target recall and wrong-BIND auditing exposed it.
  Wanted: an exact request representation in which negation or exclusion can
  veto a contradictory candidate. Do not add `without` to stopwords or patch
  this phrase: the spent row is evidence, not training data.
- **The exact-title vacuity control has almost no precision.** Its 0.9167
  target recall includes a tie of 14,571 ids, so it is only evidence that the
  holdout is not perfectly solvable by literal title overlap. A future
  coverage slice needs a blind baseline with a candidate-budget or ranking
  metric registered before its new holdout.

## Parked at v0.12 triage

- **PARKED: the write-recovery ranker (v0.12 item 6), because no fit was
  named.** `DESIGN-emergent-programming.md` P-Z1–P-Z4 wait on an
  unsaturated training leftover that is not write-recovery itself, not the
  parked family-holdout ranker, and not a re-fit of the vacant analogy
  (0.104 vs 0.1069) or tactic (65 vs 64) constructions. v0.12's roadmap
  said plainly: "if no fit is named by triage, park in BACKLOG rather than
  carry a third time as a floating ranker." No fit was named. Parked.
  **Unpark when** a design names the leftover and says what would falsify
  it. Note the nearest candidate the cycle produced: v0.12's resolver
  returns candidate sets and asks when it cannot choose, and
  disambiguation-among-candidates is a genuinely graded leftover that is
  not write-recovery — but it is *unmeasured*, which is why it is a note
  here and not an unpark. `DESIGN-ambiguity-and-context.md` A1 measures
  whether it exists at volume.

- **PARKED: groundedness-at-all does not admit against a local near-miss.**
  v0.13 stated the threshold, seeds, foil concept, and decision bars before
  inspecting scores, but the exact executable protocol and ledger first
  landed together. Treat the resulting paired one-head measurement as
  exploratory/post-hoc implementation evidence, not a fully auditable
  preregistered one-shot. All construction/vacuity checks passed, but the
  0.50 fixed-owner gate scored balanced accuracy only 0.505
  on miniF2F and 0.510 on Goedel-Pset; paired separation also missed
  (0.607 / 0.586). A small mean score margin survives (+0.0288 / +0.0245),
  but most foils are admitted. Artifact:
  `experiments/grounded_admission.json`; design and adjudication:
  `docs/DESIGN-grounded-admission.md`. The v0.12 random-tree probe was true;
  its proposed gate was not. **Do not unpark by tuning the threshold or a
  second mutation on these scored sources.** Unpark only with a new,
  independently motivated signal or semantic oracle, an executable protocol
  committed before measurement, and a fresh holdout.

- **PARKED: W1–W3 has no independently motivated fourth formal source.**
  `DESIGN-what-predicts-the-gap.md` needs four sources because three is an
  anecdote and concentration can predict self-grounding by construction.
  v0.13 did not author a fourth source for some other reason, so the design is
  not scored and does not carry again without a dependant.  Unpark only when a
  future headline independently requires another formal source; register the
  source purpose before using it in this predictor.

## Cognitive frames / lexical stores

The delivered first cuts (frame ownership, visibility-derived and nested
belief, physics frames, WordNet bridging, masked-skeleton pretraining, and the
provability corpus) now live in `docs/RELEASE-v0.5.0.md`. Remaining friction:

- **Unify ASK memory with owned frames: SHIPPED** (branch
  `feature/conversation-durable`, v0.7 item 2). `scripts/lifetimes.py` is the
  one contract: five states (`goal_local`, `session`, `durable`, `superseded`,
  `expired`) shared by `retrieval.UserBinding` and, through
  `belief_frame_lifetime`, by owned `FrameState`. The load-bearing split is
  **declared** versus **effective**: the declared lifetime is chosen once by
  the trusted return channel and covered by the binding's MAC, while
  `superseded`/`expired` are recomputed on every read from the private ledgers
  and the current goal and cannot be declared at all. A stored lifetime would
  not have been authority — anyone holding the public tuple could rewrite
  `superseded` back to `session`.
- **Deepen physical reference frames.** Add executable Galilean boosts,
  acceleration invariance, and rotating-frame terms without asserting that
  shared scope semantics imply template equivalence.
- **Traverse WordNet relations safely.** Hypernym, antonym, and entailment
  expansion need sense-level ambiguity, project-exact precedence, announced
  ranking/caps, and the existing empirical-only authority boundary. Renderer
  selection and any seed-regenerated reduced extract remain open.
- **Make depth evaluation unconditional and harder before another architecture
  fork.** The completed consumer matrix and its negative result now live in
  `docs/RELEASE-v0.6.0.md` and `experiments/ANALYSIS.md`. Remaining work is to
  score all 3,000 generated OOD rows or count capacity exclusions as failures;
  separate depth-4/depth-5 and per-step cliffs; add internal/composed
  transforms and wrapper-transfer shortcut baselines; use at least five seeds
  for small promoted effects; and test an alternative shared iterative
  mechanism before naming GRU uniquely. Freeze consumer expansion until those
  evaluation defects are repaired.
- **PARTIAL — implementation provenance is byte-strong but newline-fragile.**
  The depth run bound raw working-tree SHA-256 values; Windows patching left
  mixed LF/CRLF bytes, and rebase restored equivalent Git content as uniform
  CRLF. A reviewed manifest now binds each runtime hash to the canonical LF
  hash of run commit `25db073`, with fail-closed forgery controls. New runners
  should record Git blob ids or canonical text hashes at launch in addition to
  raw bytes, eliminating the need for a post-run line-ending bridge.
- **PARTIAL — Visual structure lane: the oracle exists, the arms do not.**
  ROADMAP-v0.7 item 8 steps 1–5 shipped in `experiments/visual/`: a
  deterministic renderer, a source scene graph with role-derived stable slot
  ids, six controlled-invalid classes, six gated exact checks each ablated
  into a unique escape, and an exact SVG round trip. P-VO1–P-VO7 were
  registered before the run and all fired (`experiments/ANALYSIS.md`).
  Remaining: step 6 — raster rendering, a parameter-matched pixel encoder,
  tokenization of the normalized tree, the shuffled-structure control
  (correct pixels, wrong scene graph), and style/family/structural-OOD
  splits. P-V1–P-V4 stay registered and unadjudicated until that runs.
- **Harden the degenerate near-miss before step 6 reports a number.** Of the
  six invalid classes, `degenerate_zero_leg` is the softest against a
  capability-blind surface baseline: an oracle-tuned SVG byte-length
  threshold reaches 0.802 balanced accuracy on it (every other class stays
  under 0.63, and the maximum over the whole matrix is 0.740). Collapsing a
  leg shrinks the figure's bounding box, which is exactly the kind of
  shortcut a raster arm could learn instead of geometry. Add a
  bounding-box-preserving degeneracy (collinear-but-not-shrunken) before the
  parsed-vector/raster comparison is scored.
- **The visual lane has one family, so "family OOD" is not yet available.**
  `DESIGN-visual-structure.md` names circle measurements, affine transforms,
  graph connectivity, SHM phase portraits and Lissajous figures as follow-on
  source-structured families. Step 6 can measure style OOD and structural
  variation within right triangles, but a family holdout needs a second
  renderer/verifier pair built to the same render/parse/invalidate/verify
  protocol. Do not name a family split until at least two non-isomorphic
  families exist — the same defect the v0.6 analogy lane was corrected for.
- **Split grounding provenance. SHIPPED (reporting half; the gate is not
  shipped and is not yet justified)** — branch `feature/grounding-channels`.
  `decompose.py` attributes every grounded constituent to one of `external`,
  `prior_corpus`, `same_corpus`, `recursive`, `pattern_absorption` and prints a
  per-corpus channel table. The CLI now emits `channels`/`channel_scores` per
  statement and a `channel_summary` block; **`reports/decompositions.json` as
  committed PREDATES the split and has neither** — it is the pre-split file,
  kept byte-stable on purpose, so "all 219 entries field-identical" is a
  statement about the pre-existing fields of a freshly generated report
  compared against it, not a description of the committed file's contents. See
  the report-regeneration item below. The aggregate is untouched (graph mean
  0.770, 440 exact / 75 pattern), because the split is attribution first. The
  regression case now reads out as intended: `provability.goedel_loeb.v1` keeps
  its 1.000 but resolves to `same_corpus` 0.775 + `pattern_absorption` 0.192
  against `external` 0.033 — a single constituent (`IMPLIES⟨?0:V, ?1:V⟩` from
  `logic.inference.contraposition`) is the corpus's entire extra-disciplinary
  content, and it is the only corpus the new `self_certifying` flag raises,
  under either owner rule. Pinned by `tests/test_decompose_channels.py`.
  **Still open before groundedness is used as an admission signal:**
  - The channel split reports, it does not gate. Nothing consumes
    `self_certifying`.
  - The BACKLOG's proposed remedy — gating the pattern channel's
    slot-swallows-call credit on the swallowed head being known outside the
    statement's own corpus — was deliberately NOT implemented here, since it
    would move aggregate scores and needs its own registered prediction.
    **The gating decision is still unjustified by measurement.** This entry
    previously claimed "the measurement that would justify it now exists: 62
    of the graph's 75 pattern-absorption constituents absorb a pattern owned
    outside the absorbing statement's discipline." That number is real but it
    justifies nothing on its own, because it was never put beside a baseline
    (AGENTS.md working method 3). Both readings, with the baseline: absorption
    is 62/75 (82.7%) by most-independent owner and 36/75 (48.0%) with ALL
    owners external — the other 26 have a same-corpus (25) or prior-corpus (1)
    co-owner. The exact channel, measured identically, is 352/440 (80.0%) and
    162/440 (36.8%). A wash by rate under either reading, and the exact
    channel dominates 5.7:1 by absolute count. What would justify the gate is
    a measurement that *survives* that comparison — e.g. that absorbed credit
    is disproportionately load-bearing for the scores a gate would move, or a
    registered prediction about the score movement itself. Both are unrun.
  - `external` shares are UPPER bounds (190 of 440 exact constituents are
    multi-owner and all are credited `external`). A gate must be argued
    against `external_lower` / `independent_lower`, now reported beside them:
    graph external 0.535 generous vs 0.246 conservative.
  - The `recursive` channel is structurally empty at the shipped defaults —
    a design consequence, not a corpus fact — so the split has four live
    channels. Reachable at `--min-family 1` (200 constituents, mean 0.316).
- **Regenerate `reports/decompositions.json` and check report coherence.**
  The committed report predates the channel split: it lacks `channels`,
  `channel_scores` and `channel_summary`, so the shipped file and the shipped
  CLI disagree about the schema of their own output, and nothing detects it.
  The adjudication numbers in this entry came from a scratch-directory run.
  Regenerating is not free — it is a large diff and wants the same
  byte-identity discipline the seeds get — so it belongs with ROADMAP-v0.7
  item 10's "report regeneration/coherence checks parallel to seed coherence"
  bullet and should land with it, not before it. Until then, treat every
  `reports/*.json` as a build artifact of an unknown commit.

  **v0.16.0 status note (2026-08-21):** the "nothing detects it" premise is
  **false** as of `scripts/check_report_regeneration.py`, which is run in the
  release refresh and enumerates each committed report against a fresh run:
  three ledgers regenerate clean, and `decompositions.json` is now a
  *declared* divergence carrying its citation (TRIAGE-v0.11 §1 gate table
  row 6 / §5; ground-truth claim b13), not an undetected drift. The closing
  sentence above — "treat every `reports/*.json` as a build artifact of an
  unknown commit" — is struck: the commit is now checkable. What remains
  genuinely undischarged here is narrower than the entry's title: the
  *regeneration* half. The committed `decompositions.json` still predates
  the channel split (no `channels` / `channel_scores` / `channel_summary`),
  and the adjudication numbers in this entry still come from a
  scratch-directory run, so the shipped file and the shipped CLI still
  disagree about the schema of their own output — the difference is that the
  disagreement is now declared and checked rather than silent. Whether to
  regenerate at all is a live call (see the 12k-scale entry below), and is
  what this entry should be read as tracking from here on.
- **Affect is design-gated, not embedding-first.** Directional review (2026-08-09)
  asked whether emotion classification maps/vectors belong beside math/science
  corpora. The answer is recorded in `docs/DESIGN-affect.md`: source-qualified
  relations, named dimensional slots, attributed affect propositions, and
  diagram twins are in-scope; continuous representations are graded
  observations/proposers, never truth stores.
  Do not open a free-text emotion benchmark or alter analogy train data until
  P-AFF1–P-AFF3 have frozen protocols and G-AFF4–G-AFF5 have load-bearing
  controls. First executable cut is narrative plant/discharge of an attributed
  character-response obligation
  under existing visibility rules, after the physics oscillation ladder and
  after belief/nested lifetime friction above is not the active critical path.

## Physics oscillation / multiplanar ladder

Evidence motivating this section: Hooke's law is already authored
(`physics.mechanics.hookes_law`) and its statistical_significance text calls it
the generator of harmonic motion, but no SHM, angular-frequency, period,
resonance, normal-mode, or multi-axis coupling node exists. Rotating-frame and
Galilean nodes ship as scope declarations without an executable multiplanar
dynamics companion. The depth-consumer dataset audit confirms neural training
is synthetic expression trees only—physics expansion
must enter the symbolic harness first, with twin predictions registered before
regenerate, not as mid-matrix train dilution.

- **Author the SHM / frequency seed slice (post depth-consumer matrix, or a
  disjoint worktree that does not touch experiment generators).** Minimal
  first cut in `scripts/seed_physics.py`: angular frequency ω=√(k/m),
  period–frequency relations (T=2π/ω, ω=2πf), and a displacement form
  x=A cos(ωt+φ) or energy partition, each under the explicit assumptions of an
  undamped linear mass–spring oscillator and with citations (Hooke 1678 already
  present; Fitzpatrick Waves / standard classical mechanics acceptable).
  Register twin and specialization predictions in the seed docstring before
  any matcher run—candidates include scaled-root forms, reciprocal scale
  pairs with existing ratio definitions, and energy kinship with
  `physics.mechanics.kinetic_energy`. Do not resspell Kepler III as SHM to
  force a twin; period–amplitude independence vs P²∝a³ is a contrast to keep
  honest.
- **Keep independent superposition, coupled modes, and reference frames
  distinct.** Orthogonal plane oscillations can form Lissajous figures without
  coupling; coupling parameters and normal-mode coordinates are a separate
  statement layer; pitch/
  roll/yaw-style measurement in a rotating frame is scope + local corrections
  already begun in `physics.frames.rotating_frame`. A composition demo
  (multi-axis oscillator described under a rotating frame) is valuable only
  after single-plane SHM exists and after “Deepen physical reference frames”
  above has executable terms—not a neural multi-body simulator in weights.
- **Resonance and normal modes are second rung.** Driven-frequency equality
  checks and two-mass modal coordinates need clear closed forms and
  vacuity-resistant tests (a constant “always resonate” baseline must fail).
  File matcher predictions separately; do not batch them into the first SHM
  slice if that would make adjudication unreadable.
- **Frequency-domain structure is a third, distinct rung.** Author Fourier
  series/transform, amplitude and phase spectrum, normal-mode eigenfrequency
  multiset, sampling/Nyquist controls, and power spectral density only after
  the time-domain oracle exists. A physical frequency spectrum distributes
  amplitude or power over temporal frequency; a statistical frequency table
  counts observations over categories or values. Their common word does not
  make them twins. Exact DFTs, coordinate transforms, and alias checks remain
  symbolic; a learned residual may later rank noisy peaks or select the
  relevant spectrum.
- **Separate three meanings of multiplanar rotation.** Extend the existing
  SO(3) rigid-transform/quaternion material with non-commuting 3D composition
  and Euler-angle coordinate caveats; author torsional SHM
  (`I θ'' = -κ θ`, `ω = √(κ/I)`) as the registered rotational analogue of the
  mass–spring equation; then treat higher-dimensional double rotation as
  simultaneous 2-plane blocks with independent angles. None of these is the
  same as a rotating reference frame's fictitious forces or two independent
  translational oscillations.
- **Diagram families after the visual oracle, not before.** Lissajous figures,
  phase portraits (x,v), and spring–mass free-body + x(t) plots are natural
  V1 follow-ons once the right-triangle renderer, source graph, and
  inconsistent-pair checks exist. Starting Lissajous before that oracle
  repeats the v0.6 visual deferral failure mode.
- **Controller actions over oscillator state are oracle-first.** When a
  physics-shaped verifier can check “period computed” or “drive frequency
  matches natural frequency,” add POINT/GEN proposals under the generic
  controller; only then consider a tiny ranking policy. Do not train a
  freestanding “physics LM.”

## Affect / emotion structure

Evidence: the proposed emotion-classification direction
(discrete taxonomies, Russell circumplex, PAD, Plutchik) plus the explicit
blog limit that ToM ships without rich motives/emotion/culture. RFT coverage
in DESIGN-cognitive-frames maps relational operants, not affect. Analogy
training (50k synthetic root transforms; ID exact 1.000; depth-OOD the real
wall) must not be redirected into sentiment tags mid-experiment.

- **DESIGN-affect.md is the admission document.** It treats Plutchik, Russell,
  and other maps as source-qualified models, not universal emotional laws. Any proposal to add emotion
  vectors, sentiment heads, or continuous affect embeddings must either fit
  that design’s layers (discrete / named dimensional / attributed /
  empirical-with-provenance) or be rejected as off-thesis. Predictions
  P-AFF1–P-AFF3 and gates G-AFF4–G-AFF5 are registered there before implementation.
- **First executable cut: attributed character-response obligations, not a
  corpus.** Reuse
  temporal plant/discharge and owned-frame visibility (Chekhov-shaped
  anti-vacuity: resolution refuses while a planted slight/fear/promise remains
  open). Negative controls: `witnessed_by` delivers information but a visible
  event with no explicit affect/report effect creates no emotion; unwitnessed
  events do not update the target's belief model; nested “Anne believes Sally
  is angry” uses nested frames without a
  new emotion modal. Depends on graft-back / lifetime clarity only insofar as
  the demo mutates nested models directly—prefer event-flow like Sally–Anne.
- **Optional discrete affect corpus only with matcher bets.** Plutchik
  opposites as mirror/opposition candidates (P-AFF1); intensity as order
  family only if templates are real. Seeds only; never hand-edit
  `data/*/nodes.json`.
- **No free-text emotion benchmark early.** P-AFF3 remains directional until
  its dataset, lexical holdout, baselines, seeds, metric, and effect threshold
  are frozen before training. If a sentiment split is ever opened, ship those
  baselines in the same artifact or refuse the claim.
- **Visual emotion maps share the visual protocol, not the physics equations.**
  Circumplex/wheel diagram twins wait on the same oracle ordering as
  Lissajous (G-AFF5). Inconsistent-sector negatives must make the geometry
  verifier load-bearing.
- **Do not merge affect with SHM by metaphor.** “Emotional resonance” remains
  prose until a registered structural prediction fires and is adjudicated.

## Frame registry

- **Owned binding lifetime is now explicit at the frame layer, but not yet
  unified with ASK.** Owned FrameState persists until an observed event
  supersedes a functional value; it refuses fiction-style exit/demotion.
  Retrieval `UserBinding` remains session-long and HMAC-attributed. 10c keeps
  that lifetime deliberately because conversation uses it as session memory;
  goal-local or expiring bindings require an explicit future policy and must
  not silently change the current contract.

- **Small filed items from the same review** (nits, no behavior defects):
  `physics.frames.rotating_frame` is governed by
  `narrative.frame.frame_consistency`, whose TITLE says "A Story May Not
  Contradict Its Own Premises" — content is generic, title is not; either
  generalize the title (seed edit, ripples into report/store text) or add
  an invariant note recording the deliberate cross-domain reuse.
  `resolution_channel` on RetrievalNeed is a validated string where the
  house pattern is Enum (Verdict, StopReason) — no laundering path exists,
  consistency only. **SHIPPED** (branch `feature/retrieval-tools`, v0.7
  item 6): `retrieval.Channel(str, Enum)` with `STORE`/`USER`.
  `RetrievalState.from_unknown` still accepts the legacy strings and still
  raises the same "must be 'store' or 'user'" message, so no caller
  changed. Side effect worth naming: the Enum's `repr` is part of the ASK
  HMAC scope, so a signed question whose channel is downgraded to a raw
  string no longer validates — a strengthening, and safe only because the
  secrets are process-local and no signature is persisted (v0.7 item 2
  must re-check this when keys become durable).
  `commit_run` is duck-typed via getattr rather than an
  optional VerifierAdapter protocol method, and an exception inside it
  would lose a fully-callbacked RunResult — theoretical, but the protocol
  should own the name. **SHIPPED** (same branch): `controller.RunCommitter`
  is a `runtime_checkable` optional protocol and `Controller.run` uses
  `isinstance` instead of `getattr`. The exception half is adjudicated
  rather than silently fixed: the protocol now *states* that a committer
  must not raise, and the controller deliberately does **not** swallow, on
  the grounds that returning a RunResult which claims a commit that failed
  is worse than losing the result. Covered by
  `tests/test_retrieval_tools.py::TypedProtocolTests::
  test_a_failing_commit_is_not_swallowed`.
  Still open from this seam: `SearchController` never calls `commit_run` at
  all, so a branching search commits no verifier-private effects. Harmless
  today (no verifier with ledgers is driven by it) and deliberately left
  alone rather than given semantics nothing has asked for.

## Retrieval stores

- **The WordNet archive digest is provenance, not tamper-evidence.**
  `WordNetIndex.load` records a per-load SHA-256, but nothing pins it: a
  re-zipped or edited archive loads with a fresh digest and no complaint.
  This is fine under the empirical-only trust model (WordNet records can
  never ground verdicts or enter verified_by), and no doc overclaims it —
  filed so that if lexical records ever gain more authority, digest
  pinning must arrive first. (Post-merge review of 745a46b, informational.)
  **Still open after v0.7 item 6, deliberately.** Relation traversal added
  `wordnet_relation` records that walk hypernym/antonym/entailment edges,
  which is *more* lexical surface, so the question was re-examined rather
  than inherited. It stays open because item 6 gave those records strictly
  less authority than the senses they came from: every relation record is
  `empirical` and **none of them can ever bind a slot**
  (`UnifiedKnowledgeStore.binding_match_mode` returns `None` for the source
  unconditionally). Digests were **not** pinned, and no doc claims they
  were. The trigger stands: pin before any lexical record becomes bindable.

- **Relation traversal is one hop only.** `relation_records` walks a single
  edge, because a one-hop edge can be re-derived from the archive by
  `contains_item` without keeping process state (`target in
  origin.relations[relation]`). Multi-hop paths would need either a stored
  path witness or a search inside the containment check, and an
  unauthenticatable pointable record is worse than a missing one. Filed
  rather than approximated. (v0.7 item 6.)

- **Process-local observation minting will not survive serialization —
  CONFIRMED and SCOPED OUT of v0.7 item 2.** The prediction was right and the
  restart shipped anyway, because the two do not collide yet: a session
  snapshot carries `RetrievalState`, which holds `PointableMaterial` and
  `RetrievalReceipt`, and a restored receipt still verifies (its MAC is
  key-ring derived). What does **not** survive is
  `LocalObservationAdapter.contains_item`, which certifies "this store minted
  exactly this record in this process". So a restored session can hold an
  observation-backed pointable whose `POINT` would now be REFUSED —
  a *stale refusal*, the same failure direction as the pruning item, and not a
  wrong binding. Not fixed here because the honest repairs are both larger than
  this item: a signed transaction receipt from the adapter (which needs the
  adapter to own a key), or re-fetch-on-load (which needs a retention and
  liveness policy). Concretely blocked on: the mint ledger has no retention
  rule, so a long-lived durable session would grow it without bound. Probe: save
  a session whose context came from the TOOL rung, restore it, and `POINT` at
  the observation. (v0.7 item 6 / a v0.8 item.)

- **Each ledger export invalidates every earlier snapshot.** `save()` issues a
  strictly increasing sequence from the private counter and `import_ledgers`
  refuses anything behind the high-water mark, which is what makes replaying an
  older *genuinely signed* ledger impossible. The price: "write two backups,
  restore the older one" is not supported, and neither is a backup taken before
  a later save. The alternative — marking freshness only when a snapshot is
  *admitted* — was rejected because it leaves a window in which an attacker who
  restores a stale snapshot before the legitimate owner simply wins. A real fix
  would need per-snapshot identity rather than a single per-scope counter.
  (v0.7 item 2, self-review.)

- **Session forking is not prevented, only rollback is.**
  `SessionKeyRing.admit_sequence` uses `>=`, so two processes may import the
  same snapshot at the same sequence and diverge into two conversations that
  each believe they are the one. `==` would have bricked any session that
  crashed between export and import. Registered in advance as P-DS7's second
  named weakness. What it would take: an import that also bumps the counter,
  plus a crash-recovery path that can distinguish "never imported" from
  "imported and lost". (v0.7 item 2.)

- **One root secret backs every scope.** HKDF separation means one session's
  keys tell you nothing about another's, but a reader of the keyfile can mint
  any binding for any owner in any session. Revocation is the only remedy and it
  is session-destroying. Deliberately not mitigated with per-owner roots or a
  hardware-held key: both would be untested ceremony around the same single
  file. Filed so the limit is quotable rather than discovered. (v0.7 item 2,
  P-DS7.)

- **The bounded request grammar is bounded by two demo slots.**
  `request_grammar.SLOT_PHRASES`/`SLOT_VALUES` cover `egg_color` and `tone`
  only. That is the mechanism working as designed — an unregistered value
  degrades to ASK rather than being passed through — but it means "growing"
  the grammar currently means hand-writing a value vocabulary per slot. Needed
  before a wider world: slot vocabularies derived from the frame's own
  declarations or from a corpus lexicon, without turning value admission into a
  similarity judgement. Also open: `ConversationSession.request_private_slot`
  falls back to a hard-coded golden-chicken literal for any slot it has not
  seen opened, which is fine for the demo and wrong for a general session.
  (v0.7 item 2 / item 9.)

- **The external observation adapter authenticates by minting, not by
  value.** An `Observation` carries its fetch timestamp, so a record cannot
  be re-derived by value the way a committed one can; `contains_item`
  therefore certifies "this store minted exactly this record in this
  process". That is the honest authority of a tool transaction, but it is
  process-local: it will not survive the serialization v0.7 item 2 is
  building. When sessions become durable, external records need either a
  signed transaction receipt or re-fetch-on-load. The mint ledger also
  keeps every transaction (two fetches of one observation are two real
  events with two timestamps), so it grows with tool retrievals rather
  than with source size — bounded and small today, but it wants an
  explicit retention rule before a long-lived session ships. (v0.7
  item 6.)

- **Session pruning assumes a static rung store — PARTIALLY CLOSED by
  scoping out.** v0.7 item 2 settled the half it was blocked on: pruning
  evidence is **not serialized**. `retrieval.LedgerSnapshot` carries the
  consumed-request and supersession ledgers and deliberately omits
  `_pruning`, so a restart re-pays for a branch instead of inheriting a
  refusal whose cause it cannot re-check. The reasoning is this item's own:
  a stale refusal that survives serialization is worse than one that dies
  with the process, and its loss costs a re-query rather than a wrong answer.
  **Still open** for the in-process case: a source that goes live mid-session
  leaves an earlier TOOL branch REFUSED for the rest of that session. The
  honest fix remains a re-consult policy (pruning evidence carries the source
  probe generation it was recorded under), not a wider state key. Original
  evidence below. (v0.7 item 6.)

- **Session pruning assumes a static rung store, and the TOOL rung breaks
  that by design.** `RetrievalVerifier._pruning` is keyed on
  `(session_id, state_key, action fingerprint)`, and `state_key` describes
  the *conversation*, never the *stores*. For the five committed sources
  that is sound — they are loaded once and read-only for the session's
  lifetime. It is not sound for the TOOL rung, whose whole point is
  reaching material this process does not own: an observation folder that
  gains a file, or a source that was down at the first fetch and up at the
  second, leaves the branch REFUSED from a dead end that is no longer dead.
  Probe: a source registered mid-session leaves the earlier rung refused
  for the rest of it. Deliberately **not** fixed by widening the key —
  hashing external source contents into a state key would make the key a
  liveness probe, re-query every source on every transition, and still race.
  The honest shape is a re-consult policy: pruning evidence for the TOOL
  rung carries the source probe generation it was recorded under, and a
  changed generation re-opens the branch rather than re-querying eagerly.
  Filed as a v0.7 **item 2 / item 6** follow-up because it must be settled
  together with durable sessions — a stale refusal that survives
  serialization is worse than one that dies with the process. Note the
  failure direction: this is a *stale refusal* (an answerable branch stays
  closed), not a wrong binding. `RetrievalVerifier.state_key`'s docstring
  states the assumption rather than implying soundness. (v0.7 item 6,
  external review 2026-08-10.)

## Nested frames

- **No graft-back API for nested-model mutation: SHIPPED** (branch
  `feature/frames-v07`, v0.7 item 7). `FrameExecutor.with_nested(parent,
  owner_path, new_child)` grafts a model back immutably and
  `route(state, owner_path, transition)` runs any executor transition
  inside a model and returns the ROOT, so an accepted mutation lands in
  place and a rejected branch still yields no next_state. Grafting is a
  REPLACEMENT, not an insertion: creation stays with `open_nested` and
  its refusals, and the graft re-checks the child-owner key, the closed
  ancestor rule, and the event-history subset invariant across the whole
  grafted subtree. The `replace(parent, children=...)` surgery is gone
  from the grandchild test; the poisoned-child test keeps it, now labelled
  a deliberate API bypass and paired with an assertion that `with_nested`
  refuses that same graft — which is the point, since surgery is the only
  remaining way to reach the loud RuntimeError that control exists for.
  (Nested-frames review, note 8; predictions P-NF4–P-NF6 in
  `tests/test_theory_of_mind.py`.)
  Still open: no consumer mutates a model directly yet — the affect slice
  should still prefer event flow (see the affect note above), and a
  `route`-driven controller adapter for nested belief is unbuilt.

## Language as structure (linguistic dual of the prover)

Evidence: DESIGN synthesis + discourse review + architecture review + **v0.10
loop coordinator review (post-quantifier merge)**. Full guidance P-LS1–P-LS13
with numeric registration: `docs/DESIGN-language-as-structure.md`. Spine to
keep: L1–L4, index-relative verification, R-register.

- **Quantifier row is no longer “v0.10 priority / coverage gap.”** Formal
  `FORALL`/`EXISTS` shipped (slot-recurrence binding). Inherit measured
  caveat: alpha-invariance is Barendregt **naming convention** (whole-
  statement injective rename only; sibling binders reuse slot names by
  design). NL must not invent a second binder calculus (§5.1, §5.4).

- **P-LS predictions need formal registration discipline.** Fragment id,
  suite N, metric floors, LOST policy, twin expectation, GC4/GC5 acks—before
  adjudication. Qualitative pass/miss alone is goalpost drift (R14).

- **P-LS5 = coverage-instrument pipeline shape** (pinned source → extract →
  precise refusal labels → audits 0 → dual-pass LOST=0 or disclosed). Same
  shape that moved Goedel 32.8%→43.2% and exposed parser artifacts.

- **P-LS1b LOST dual** for realizer/parser growth; pattern
  `scripts/verify_slice.py`.

- **P-LS4 operational:** every preference feature is a deterministic
  unit-tested pure function in-repo; untestable “coherence modeling” miss
  conditions are refused at review.

- **P-LS13 twin null / GC pins** when NL nodes enter `data/*`.

- **Sequencing:** story briefs + round-trip may proceed; **discourse store
  product wiring only after ROADMAP-v0.10 item 5 harness session** so a
  second memory system is never born. Standalone pure modules for unit tests
  are fine.

- **Retract templates-as-design-law; keep architecture gaps (indices, L1–L4,
  joint C, lexicon source, residual hardness).** Implementation may live on
  `feature/language-structure-impl` without blocking design merge.

## Interactive harness / agent OS

Evidence: directional design 2026-08-09 (integrate demos into one agent-like
experience; model composition; offline WordNet/wiki) with review rejecting a
slash-command **demo launcher** in favor of a **microkernel session** that
routes only along registered paths (registered ≠ PROVEN; PROVEN stays reserved
for digest-pinned Lean artifacts). Full mapping and predictions P-IH1–P-IH7:
`docs/DESIGN-interactive-harness.md`.

- **A2 cannot be recovered from authored-after-the-fact follow-ups.** The
  registered prediction named discipline, corpus, or second-word context and
  the two holdouts, but neither holdout froze its actual continuation or the
  reading that must survive.  A first scorer could therefore select favorable
  constraints, omit hard ASK rows, or discard the intended reading and still
  report halving.  Review stopped it before commit and before aggregate
  execution.  Unpark only with a fresh holdout that commits query,
  continuation, intended retained ids, capability-blind control, and complete
  provenance before the resolver sees it.  The spent holdouts stay spent.

- **Mechanics are live; demos are frozen policies.** `StoryVerifier` already
  mutates beats/obligations under GEN actions; `ConversationSession` opens and
  supersedes private slots; ToM derives belief from events. What is canned is
  `SequencePolicy` + oracle action lists (golden-chicken, scripted Sally–Anne).
  Do not ship `/golden_chicken` or `/tom` as product destinations—promote
  adapters to **subsystems** and demote scripts to **selftests**. Miss criterion
  for Phase 1 UX is P-IH3 (demo zoo).

- **WAITING must drive the input channel automatically.** Controller
  `StopReason.WAITING` is the tool-call equivalent of ASK. TTY/HTTP surfaces
  should prompt the user when the kernel pauses, then resume with a signed
  reply—users must not be taught a dedicated `/ask` command (P-IH2). Batch
  mode records need-input instead of inventing values.

- **No primary slash menu of limited demos.** The shell is need-driven: open
  UNKNOWNs, obligations, and user goals select among **registered** subsystem
  paths; unregistered paths abstain or ASK (P-IH4). Advanced debug overrides
  (`:trace`, `:status`, force action) are fine; a zoo of contrived prompts is
  not.

- **Boot capability matrix (kernel-style init).** On startup, probe corpuses,
  ledgers, narrative/belief/retrieve, optional WordNet/Lean/tools; print
  OK/OFF/FAIL with counts, digests, sizes—without requiring eager full loads
  (P-IH5). Named missing WordNet stays loud FAIL for that probe; ~~unnamed
  stays OFF~~. Wikipedia/COCA `data_real` is not a default subsystem.

  **v0.16.0 status note (2026-08-21):** the "unnamed stays OFF" clause is
  contradicted by shipped behaviour since `35f050f` ("Find the fetched
  archive without being told where it is"): manifest auto-detection means an
  *unnamed* WordNet resolves **ON** when the pinned archive is present where
  the manifest says it is. The half of the rule that survives is the loud
  one — env-set-but-missing still **FAIL**s, and fails by name. Read the
  clause as "unnamed stays OFF *only when no pinned archive is found*".

- **Status chrome and collapsed trace.** Map VERIFIED/SOLVED, REFUSED/REFUTED,
  WAITING (pulse), EXHAUSTED, BUDGET to characters/colors; stream optional CoT
  while running; **default collapsed** final view with expand-on-demand. Respect
  `NO_COLOR`.

- **Session object unifying adapters.** One process image: frames, user
  channels, stores, optional tools, unified action trace, budgets. Today each
  demo is a separate entrypoint with no shared session—this is the integration
  gap, not missing story physics.

- **Subsystem plugins for optional neural tools.** Span/analogy/tactic
  checkpoints register only after probe success; OFF degrades to symbolic
  paths. Reject neural MoE over incompatible vocabs as the integration strategy;
  accept long-term “many specialized models as loadable modules” under ActionKind
  I/O — **conditional on session-scoped loop detection that does not exist
  yet**.

- **BLOCKER (DISCHARGED at v0.16.0) — loop detection is run-local, not
  global.** `rejected` is a local
  inside `Controller.run()` (`scripts/controller.py:271` — stale line cite;
  the local is now at `scripts/controller.py:346`) and
  `SearchController`'s `seen_states`/`attempted` are likewise per-search: every
  pruning structure is discarded on return. A need dispatcher issues one run
  per hop, so a session can cycle among **registered** paths with pruning reset
  at each hop. Registration bounds *which* paths exist; it does not bound
  revisiting them. Fix is a session-scoped `(need, state_key)` /
  `(subsystem_id, state_key, fingerprint)` record threaded through every run
  (Phase 1) plus a session hop budget (Phase 2), adjudicated by **P-IH7**.
  Nothing that multiplies the hop graph — tool plugins especially — should land
  before it.

  **v0.16.0 status note (2026-08-21):** **P-IH7 was adjudicated and this
  blocker is DISCHARGED.** Session-scoped loop detection exists and is
  tested: `tests/test_session_dispatcher.py`, green in both the v0.15.0 and
  v0.16.0 release gates. The "nothing should land before it" hold no longer
  applies — the tool-plugin lane is unblocked as far as this blocker is
  concerned. The `Controller.run()` local described above is still a local;
  what changed is that the session dispatcher threads its own record across
  hops, so pruning is no longer discarded at each return.

- **Chat Completions–compatible HTTP skin (Phase 4).** Same session engine as
  TTY; represent WAITING to external harnesses without inventing slot values
  (P-IH6). Durable multi-session auth remains blocked on the verifier
  **instance** — HMAC keys *and* the consumed-request / supersession ledgers
  (`scripts/retrieval.py:741-744`) — so a `Session` is a handle to live
  authority, not a value object (see conversation item below; ROADMAP-v0.7
  item 2 is the scheduled fix).

  **v0.16.0 status note (2026-08-21):** three stale facts in the sentence
  above. (1) ROADMAP-v0.7 item 2 is no longer "the scheduled fix" — it
  **SHIPPED**; see the "Durable authenticated conversation resume: SHIPPED"
  entry earlier in this file. Durable multi-session auth is therefore not
  blocked. (2) The line cite `scripts/retrieval.py:741-744` is stale to the
  point of being wrong: those lines are now WordNet synset code. The real
  anchor for session restore is `ConversationSession.restore` — see
  [DESIGN-interactive-harness.md](DESIGN-interactive-harness.md) §3.3 and
  §4.3. (3) Park history, so the record is legible: this skin was parked at
  v0.13, v0.14 and v0.15; a fourth park is recorded at ROADMAP-v0.16 §3 and
  a fifth at ROADMAP-v0.17 §3. It is **unblocked in fact; unscheduled by
  choice, until now** — the honest status is a standing deferral, not a
  dependency.

  **v0.17.0 status note (2026-08-22): RESOLVED — the skin shipped.** Kept
  here rather than pruned, because five recorded parks are the drift record
  this file exists to hold, and deleting the entry would delete the
  evidence that the deferral was real. `scripts/serve_chat.py` serves
  `POST /v1/chat/completions`, `GET /v1/models` and `GET /v1/capabilities`
  over the two shipped session objects, stdlib-only and loopback-only, one
  owner, no auth — the substrate's shipped single-session scope, unchanged.
  **P-IH6 is adjudicated and fired**: WAITING crosses the boundary as a
  need record (`x_corollary.need` = `{slot, prompt}`), the next user
  message binds through the verifier's signed channel byte-for-byte, and
  the negatives are stated as what a signatureless wire can actually
  falsify — an unparseable reply asks again and never fills, a cross-slot
  reply is a `409` rather than a reinterpretation, and no slot binds on a
  turn where the user sent none
  (`tests/test_serve_chat.py::PIH6WireNegatives`). The blocker sentence at
  the top of this entry is fully struck: durable multi-session auth is not
  merely unblocked, it is **not used** — ¶DEV-1 of
  `docs/SPEC-chat-completions-skin.md` records that
  `ConversationSession.restore` is not in the serving path at all, because
  every request is served by replay into a fresh session object. Durable
  restore over HTTP therefore stays **unshipped and unclaimed**, which is a
  narrower and more honest status than "shipped". Evidence:
  [RELEASE-v0.17.0](RELEASE-v0.17.0.md); the spec; commit `8059b4a`.

- **Need dispatcher before learned global policy.** Closed-form dispatch from
  epistemic state and registered paths first; learned ranking among legal
  actions only with frequency/oracle baselines (tactic-policy negative result).

## Controller / harness

- **SHIPPED (split + ceilings) — corpus analogy is a real split; the model arm
  and an untyped-shape holdout remain open.** Branch
  `feature/corpus-analogy-v07`, `experiments/corpus_analogy_split.py`. The v0.6
  defect (40 rows, five targets, one ratio family, a blind last-slot rule at
  1.000) is closed: 914 rows dedup to **398 distinct targets** over **11 typed
  families / 10 untyped shapes**, 13 source and 15 target disciplines, 376 of
  398 carrying a compound-expansion leaf. Compound expansions became
  representable once B was recognized as part of the INPUT — its leaves are
  pointable where they stand — and the admission gate is literal: every token
  of D must occur in `A <sep> B <sep> C`. That gate also refuses head-identity
  collapses (the element is nowhere in the input) and settles that B's
  identity-free form is the target rather than the re-substituted `*(1, …)`.
  Three seedless holdout files; blind ceilings **0.400 / 0.932 / 0.398**, the
  v0.6 killer down to **0.000 / 0.011 / 0.048**. The v0.5 synthetic
  checkpoint's 1.000 still must never be cited as corpus transfer.
  Open:
  - **The headline ceiling is inflated by our own split.** Families are TYPED
    skeletons, so `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)` are two families and one
    head/arity shape. Nearest-template replay scores 1.000 exactly where a
    held-out row's untyped shape is still in training and ~0.10 where it is
    not; the family holdout's 0.400 is exactly
    `51/155 × 1.000 + 104/155 × 0.106`. The strict ceiling is **≈0.10–0.14**.
    Needed: an **untyped-shape holdout**. Deliberately NOT substituted after
    the fact — re-rolling a split against a measured ceiling launders the
    result — so it is queued, not quietly swapped in.
  - **The discipline holdout is near-vacuous** at 0.932, because 162 of its 176
    rows keep their untyped shape in training. Do not cite it alone as a
    difficulty result.
  - **The three axes are not orthogonal.** Holding out whole families empties
    five of ten disciplines out of training; at this corpus size some
    disciplines occur in only one skeleton. Pinned as a regression number
    rather than asserted away.
  - **The residual is metadata, and that bounds what a model can be credited
    with.** A solver reading only the token stream reaches 0.458/0.545/0.651;
    adding each slot's parameter/variable class and the identity table takes it
    to 1.000 on all three holdouts, because `Search` gates its arithmetic-
    identity rule on the class being `P`. With those declarations the task is
    closed-form, so the lane measures the pointing mechanism only.
  - **No model has been trained.** Every committed number is a control, and the
    GPU arm must be reported against the strict ceiling, not the headline.
  - Four families carry two or three examples; their per-family numbers are
    anecdotes, and more cross-discipline twins would fix that.

- **Durable authenticated conversation resume: SHIPPED** (branch
  `feature/conversation-durable`, v0.7 item 2). Owner-isolated sessions
  serialize to public JSON, a new process reloads a root key ring from a
  gitignored keyfile, re-imports signed anti-replay ledgers, and continues
  revising. Stale, forged, rolled-back, session-swapped, and revoked-key paths
  are each refused by a *named* reason (`session_keys.RefusalReason`). The
  ambient secret is never serialized: what crosses is a key id. The bounded
  slot-filling grammar landed with it (`scripts/request_grammar.py`), in-cycle
  as DESIGN §3.4 required.

  Still open, and now the actual next steps rather than a placeholder:
  transport/UI integration (the harness TTY and HTTP skins); unrestricted prose
  authoring (item 9, still last); learned question rendering; and the
  deterministic dispatcher across derivable/store/user/terminal channels before
  a learned chooser is evaluated. Limits shipped knowingly are filed above:

  **v0.17.0 status note (2026-08-22):** two of those four have moved.
  **Transport integration is done on the HTTP half** — the skin shipped
  (see the Phase 4 entry above); the TTY half was already live.
  **Unrestricted prose authoring is no longer "item 9, still last"**: it is
  scheduled as the **v0.18 headline** under
  [DESIGN-sans-template-rendering](DESIGN-sans-template-rendering.md),
  earned by a trigger DESIGN-grounded-throughput §10 registered before the
  run that fired it. Read the design before assuming what it covers: it
  renders *terms the kernel already parses* — corpus formal statements and
  session-accepted structures — under a two-stage gate whose second stage
  is a byte-frozen parser that never saw the realizer. It does **not** read
  open English on the input side, and it does **not** author narrative
  (`prose.py`'s closed-algebra gate stays the only narrative authority), so
  "unrestricted prose authoring" as this bullet's phrase means it is still
  not scheduled and the phrase should stop being used for the Phase 6
  slice. One number to carry into any planning: only **2,172 of 12,777**
  canonical terms (17.0%) parse under the committed grammar today, measured
  during the design's review, so the surface being opened is bounded by
  that and the design's R0 publishes the table. Learned question rendering
  and the deterministic dispatcher are unchanged and still open.
  root-key compromise, session forking, export invalidating earlier snapshots,
  and a two-slot grammar vocabulary.

- **SHIPPED (breadth), STANDING (verdict) — the one live theorem is now a
  24-theorem, four-family, five-rung solved-rate curve, and the learned arm
  still loses to a capability-blind order.** ROADMAP-v0.7 item 1.
  `prover/theorems_v1.json` + `prover/curve_search.py` +
  `experiments/tactic_curve.py`: 144 live PyPantograph runs, no replay in any
  arm, budgets 4/8/16/32/64 states and 32/64/128/256/512 proposals. At the
  middle rung (8, 64): syntax-aware blind 21/24, frequency (v0.6's winner)
  20/24, learned 18/21/19 (mean 19.33), arbitrary 17/24. Mean proposals:
  syntax 48.29 < learned 49.00 < frequency 51.58 < arbitrary 55.96 — the
  learned checkpoints DID overtake v0.6's winner across 24 theorems and still
  lose to the closed-form order. The v0.6 native-project blocker is closed:
  PyPantograph 0.3.15 only shells out to POSIX `printenv` when
  `project_path` is given WITHOUT `lean_path`, so passing the path explicitly
  bypasses it (no patch, no fork); `prover/lean/proofcurve/` is a 4.29.1-pinned
  Lake project matching the Pantograph build, so the 4.32.2 extraction
  project's toolchain mismatch is side-stepped rather than resolved. Still
  open, and now with evidence: only 60 of 155 extraction rows map to the
  eight-schema vocabulary; no model chooses among POINT/RETRIEVE/ASK/WRITE;
  and reconciling the 4.29.1 Pantograph build with the 4.32.2 `BooleanLaws`
  extraction project remains undone (see the new item below).

- **`implication_chain` is a vacuous budget family.** All six arms solve all
  seven members at the LOWEST rung (4 states / 32 proposals), including the
  two deeper members added specifically to fix this after a construction
  pilot exposed it; an eight-tactic witness still costs 11–15 proposals. The
  family separates arms only on mean proposals (syntax 9.29 vs frequency
  12.86). P-PC2's whole row missed because of it. The repair is structural —
  premises that must be *selected* rather than discharged in order, so the
  chain branches — not more theorems of the same shape.

- **The two prover Lake projects sit on different toolchains.** The
  extraction project (`.worktrees/prover-phase1/boollaws`, untracked) needs
  Lean 4.32.2 for `ExtractData.lean`'s `String.trimAscii`; the committed
  PyPantograph `repl.exe` is built at 4.29.1 and refuses to emit `ready.`
  against a mismatched project. `prover/lean/proofcurve/` avoids the problem
  by pinning 4.29.1, which means **live search has never run against the
  project the training triples came from**. Either rebuild `repl` at 4.32.2 or
  re-extract at 4.29.1 before claiming the trained policy and the live search
  share a project.

- **Cross-task dead-branch avoidance was measured and is absent.** The first
  artifact mislabeled every accepted off-path sibling as dead, including
  unexpanded frontier entries; independent review blocked it. The corrected
  frontier-aware ledger preserves 227 transitions whose complete queued
  subtrees were exhausted (`clear` 101, `constructor` 66), scored
  leave-one-theorem-out. Under the pooled ledger the learned arms re-propose
  known-dead signatures at 0.2063 against syntax's 0.2053 — no measurable
  avoidance. The ledger is also
  RUN-LOCAL: nothing carries it between runs, so no arm can actually use it.
  Making the dead-branch ledger an input to ranking (rather than only an
  output) is the obvious next experiment and is not built. The published
  aggregate shares are reproducible from `cross_task_dead_branches.arms`:
  it serializes each arm's hit counts, proposal denominator, share, and
  per-theorem counts. `RunRecord.as_json()` does omit the raw proposal and
  accepted signatures, however, so auditing *which* signatures contributed
  still requires a re-run; serialize those if signature-level inspection
  becomes a release claim. The committed state-leakage artifact is guarded
  fail-closed by `test_state_level_leakage_control_stays_at_zero`.

- **Breadth-first search leaves almost no ranking headroom in the story
  domain.** ROADMAP-v0.7 item 1's story arm (`experiments/story_curve.py`, 48
  runs over 8 briefs): the largest best-to-worst proposal spread on any brief
  is 1.07% (373 vs 377), against 65.6% on the proof side. Every arm expands
  exactly 32 nodes. `SearchController` expands each node's FULL candidate list
  and the story grammar fixes the solution at depth five, so the 31 nodes
  above it are expanded whatever the order — ranking can only save part of one
  node. The story curve is consequently a single step at the last rung. Any
  real story-side ranking result needs best-first or depth-limited search,
  which is a controller change and was deliberately not made this cycle
  (item 1 forbids a second controller). Also: the state-blind FREQUENCY
  baseline is degenerate here — each of the five schemas fires exactly once
  per story, so its order is the alphabetical order and the arm is
  byte-identical to `arbitrary`.

- **SHIPPED (both rungs) — `verified_by` is a checked edge; what it checks is
  structure, and structure cannot name an owner.** Rung one (provenance)
  remains as before: `validate_nodes.py` requires repository-contained
  artifacts whose every row is a complete state–tactic–state transition and
  whose selected theorem reaches `no goals`, resolves explicit or unambiguous
  reference-free theorem identities, and gives every theorem reference exactly
  one statement owner. Its capability-blind control — a valid Boolean theorem
  paired with an unrelated gravity statement — still PASSES there, deliberately.
  Rung two (semantics) is now `scripts/proof_correspondence.py` (branch
  `feature/proven-write`, v0.7 item 3), and that control now FAILS: the module
  reads a theorem's opening goal out of the artifact, translates the declared
  propositional fragment into the corpus template grammar, skeletonizes it with
  `match_signatures`' own tokenizer/parser/canonicalizer/`skeleton`, and
  compares it to the citing statement's declared form set. Over the 16
  committed links: 15 CORRESPONDS, 1 UNTRANSLATABLE, 0 MISMATCH.
  "Digest-pinned proof trust" may now be read as structural correspondence —
  and no further. A CORRESPONDS verdict says the theorem's opening goal
  SKELETONIZES to a form the citing statement declares. It does not say the
  statement is true and it is not semantic ownership: "byte integrity alone is
  not semantic ownership" is the floor this rung clears, not the ceiling it
  reaches. Four limits are load-bearing and open:
  - **structure is not ownership.** 12 of the 15 translatable links have at
    least one other committed statement declaring the same skeleton (the
    set-theory twins). Only the exclusive-ownership rule keeps one claimant;
    correspondence would accept the twin. Reported per link as
    `ambiguous_with`; see docs/DISCOVERIES.md.
  - **a slot class is not an object identity, and the first version of this
    check forgot it.** `match_signatures` folds every parameter-like slot into
    one class `P`, which is right for asking "same shape?" and unsound for
    asking "does this theorem prove this?": `MEET(PROP1, TRUTH) = TRUTH` and
    `MEET(PROP1, FALSITY) = FALSITY` skeletonized identically, so a Lean proof
    of `P ∧ ⊥ ↔ ⊥` certified the FALSE claim `P and true = true` through all
    fourteen WRITE gates. Correspondence now splits the lattice POLES (TOP,
    BOT) into distinct classes on both sides. Spellings of one pole (`TRUTH`
    and `UNIVERSE`) are deliberately still unified — that is the corpus's own
    cross-discipline claim, and separating them would delete the
    `ambiguous_with` admission rather than earn a stronger check. Constants
    the pole table does not name (`INCONSISTENCY`) match no Lean constant at
    all, which is fail-closed. Open: the pole table is a declaration, and any
    new lattice-bound spelling must be added to it or silently fails closed.
  - **the fragment is propositional.** `not_forall_iff_exists_not` is
    UNTRANSLATABLE (it binds a type and a predicate and quantifies). Extending
    to first order needs binder-aware templates the corpus grammar does not
    have; until then, that link is uncheckable rather than wrong, and the CLI
    reports it without failing.
  - **`equivalent_forms` is admitted as declared content.** Necessary — seven
    links would otherwise be false MISMATCHes — but it inherits whatever the
    corpus files there, including one-directional halves. See the
    DISCOVERIES entry; narrowing the field is a corpus-wide authoring
    decision.

- **NEW — `equivalent_forms` has two incompatible readings and now has a
  consumer that needs the strong one.** Nodes file dual laws (fine), notation
  variants (fine), and one-directional halves under one array:
  `logic.boolean_laws.double_negation` lists `P implies not(not P)`;
  `logic.inference.modus_ponens` lists the rule and sequent presentations;
  `logic.boolean_laws.absorption` lists the order form `P entails (P or Q)`.
  The proof-correspondence gate reads the array as "forms this statement
  asserts", so a theorem proving only a listed half would be accepted as
  proving the whole. Today nothing exploits it (all 16 committed links match
  a canonical, dual, or full-equivalence form), and the untranslatable
  entries fall out of the fragment anyway. Fix options, in preference order:
  add a `strength` field (`equivalent` / `weaker` / `presentational`) to
  `formalVariant` and admit only `equivalent`; or move halves to a separate
  `partial_forms` array. Either is a schema change across 221 nodes and needs
  its own slice.

- **PARTIAL — the common protocol is executable; WRITE remains.**
  `scripts/controller.py` now carries typed state + one of
  `{POINT, GEN, RETRIEVE, ASK, WRITE}` + symbolic verifier result + accepted
  next state + branch trace. The deterministic oracle runs both a three-step
  replay of contiguous machine-extracted Lean transitions and the three-beat
  golden-chicken story through that one controller. It enforces the key
  invariant: REFUTED/UNKNOWN/REFUSED branches cannot mutate accepted state.
  The capability-blind controls reject an unrecorded tactic, a changed Lean
  state, out-of-order story beats, and a frame-trait contradiction. Still open:
  `GEN` has proof/story/frame semantics, and `retrieval.RetrievalVerifier`
  layers executable `RETRIEVE` plus exact `POINT(position)` over the unchanged
  frame verifier. ASK now adds an authenticated pause/return adapter with a
  runtime user frame; `WRITE` now has both a gate (`scripts/write_stage.py`)
  and an adapter (`write_stage.WriteStagingVerifier`), completing the five-
  action surface. The adapter avoids the obvious category error by being exact
  about what the action IS: `WRITE(proposal)` means "put this proposal on the
  table", so the state it advances is a receipt ledger and not knowledge. A
  live
  PyPantograph verifier now plugs into the same controller for one bounded
  theorem search, but project-backed breadth and a shared proof/story learned
  policy remain open.

- **Temporal event grounding: substrings replaced by a typed binder,
  corpus grounding still open (PARTIAL).** Chekhov close-time obligations
  and governance-gated no-deus heralding both execute. The
  case-insensitive substring searches over oracle-authored prose are gone
  (branch `feature/frames-v07`, v0.7 item 7): a beat-creating transition
  carries `binds` records (`element@start:end`), the adapter validates each
  span against the frame's declared surface forms for that element id, and
  plant/discharge consult those typed records by element IDENTITY. All four
  controls survive and two strengthen — a plant still amends the visible
  setup beat (records are rebased onto the amended text), a discharge now
  requires a record ON the resolution beat (so "the evidence is really in
  the resolution" is structural, not a substring test), an unrelated
  mention fails by identity rather than spelling, and duplicate plants stay
  idempotent. The hidden-ledger control is now the sharper "identical prose,
  no bindings → UNKNOWN". Ids are decoupled from prose: an element id that
  never appears in the rendered story plants, discharges, and closes, which
  the substring check could not do. Predictions P-EB1–P-EB3 in
  `tests/test_controller.py`; demo output byte-identical.
  **REFUTED then fixed, on the record:** as first shipped (dd1cdd2) exact
  surface matching had no word-boundary rule, so a bound span could name a
  word FRAGMENT. With the shipped lexicon (`key` is a declared element) a
  story about a "donkey" and a "monkey" planted, discharged and CLOSED a
  key obligation while containing no key — independent post-commit review
  produced that run. The replaced substring check had the identical hole,
  so this was an inherited defect the migration advertised as fixed and had
  not. Bound spans now must sit on word boundaries; the reproduction is the
  control test. P-EB3's second clause is recorded as refuted-then-repaired
  rather than quietly rewritten.
  Still open: the element lexicon is the adapter's own declaration, not
  corpus-grounded event structure, and it is deliberately EXACT (a declared
  surface form, casing included) rather than a general semantic binder.
  Nothing yet links a bound element id to a corpus statement. Two known
  limits of a reference binder, filed rather than hidden: it checks
  REFERENCE, not polarity or modality — prose reading "there was no fallen
  feather" binds exactly as well as prose asserting one — and nothing stops
  two declared elements sharing a surface form, in which case the author's
  chosen id decides. Both need semantic event structure, not more string
  rules.

- **Past-mirror payoff exposed two specialization false positives.** The
  intended new edges are `response_pattern -> cartoon_gravity` and
  `heraldry_pattern -> no_deus_ex_machina`, both cost 4. The same run also
  derives `geotop.predicates.de9im_disjoint` as a generalization of
  `strict_part_of_order` and `prev_distributes_over_meet`, both cost 7. The
  graph moved 622 -> 626, but only half the delta is signal. Keep these cases
  in the category-compatibility adjudication rather than counting raw edge
  growth as progress.

- **Recursive-definition grounding is not a blanket 1.000 guarantee.** The
  registered payoff prediction expected SINCE and ONCE unfolding to inherit
  the earlier UNTIL/EVENTUALLY 1.000 results. They instead score 0.667 and
  0.500 because self-headed terms leave other compound constituents in the
  denominator that the current inventory does not recognize. Decide whether
  that is the intended metric or whether definitional grounding should cover
  the entire right-hand construction; preserve these two nodes as controls.

- **One loop across two domains is not yet generalized model weights.** A
  shared controller API can still hide two bespoke policies. After the oracle
  proves the infrastructure, evaluate the claim in explicit rungs: separate
  learned proof/story policies (learnability); one shared policy with thin
  verifier adapters (shared mechanism); held-out structures and greater chain
  depth (composition); then transfer to a third domain such as equation
  derivation or a science problem (cross-domain generalization). Report each
  rung separately. The golden-chicken story is the integration gate, not by
  itself evidence that the model has become a general-purpose solver.

- **PARTIAL — local retrieval initiation and point binding are executable.**
  `demo_answer.py` and solvex-v2
  show that, when a relevant knowledge base is already in context, the pointer
  can use it: held-out combinations reach 1.000 against three distractors, with
  a measured capability-blind floor of 0.31; deeper distractor-bearing inputs
  remain open at 0.69 OOD. `docs/DESIGN-frames-and-retrieval.md` already makes
  UNKNOWN the closed-form trigger for `RETRIEVE(key)`. The local adapter now
  unifies corpus summaries, node lexica, twin/mirror groups, decompositions,
  and proof artifacts into 702 attributable items; exact lookup falls back to
  deterministic token-neighborhood search, results enter immutable indexed
  context, and POINT binds one without promoting its epistemic status only
  when tiered attribution resolves a unique canonical statement owner,
  decomposition owner, or structural-group record. Ambiguous symbols remain
  context, not answers. Empty-
  store and unrelated-query controls remain UNKNOWN with ABSTAIN evidence and
  no mutation. A `frame_local` scope refuses before store access and emits
  `ASK(slot)`. The ASK return channel now ships as item 10a; still open here:
  external tool connectors,
  semantic/ranked neighborhood taste, open-language parsing of a request into
  the literal's canonical target key, learned item selection, and
  evaluation on deeper distractor-bearing stores rather than the deterministic
  oracle.

- **Retrieval is currently a linear scan over a committed snapshot.** The 715
  items are small enough that exact and token-neighborhood lookup need no
  index. Growth will require a regenerated query index with the same coherence
  discipline as reports; otherwise retrieval can silently lag the seeds. Any
  learned or embedding ranker belongs after the exact/neighborhood controls and
  must not replace source attribution or epistemic-status preservation.

- **Retrieval receipts are session-local: SHIPPED** (branch
  `feature/conversation-durable`, v0.7 item 2). Receipts now carry a `key_id`
  and are signed under a key derived from the durable ring rather than a
  process-local secret, so persisted state *does* resume a pending retrieval
  after a restart: `POINT` at a restored receipt is VERIFIED, and the same
  receipt with a rewritten signature is still REFUSED
  (`tests/test_session_durability.py::RetrievalReceiptDurabilityTests`). The
  ambient secret was never serialized; what crosses is a key id, and the root
  stays in the runtime-owned keyfile. Note the one rung this does not reach:
  TOOL-rung observations still fail `contains_item` after a restart (its own
  BACKLOG item above).

- **SHIPPED (staging; acceptance stays human) — model-initiated durable
  writes have a PROVEN gate.** `scripts/write_stage.py` (branch
  `feature/proven-write`, v0.7 item 3) is the PROVEN-gated dual of
  UNKNOWN-triggered `RETRIEVE`. A candidate names a SEED, never a corpus
  file, and carries seed source, proof artifact, pinned digest, theorem
  identity and transition trace. The gate matrix: PROVEN + CORRESPONDS stages
  a full candidate; VERIFIED stages a review-request record carrying no
  candidate content and executing no seed; CONJECTURED and frame-local are
  REFUSED; PROVEN with a MISMATCH **or** UNTRANSLATABLE correspondence is
  REFUSED, failing closed where the lint fails open. Acceptance pipeline, each
  step able to refuse: path containment, rung, new-seed/new-corpus ownership,
  repository-owned proof-manifest
  pin plus candidate digest pin, theorem
  closure, transition-trace membership, exclusive theorem ownership, scratch
  regeneration outside the repository, regeneration confinement (every other
  corpus byte-identical; exactly the declared statement added), semantic
  correspondence, structural unambiguity, schema/link validation of the merged
  scratch graph, declared-versus-measured matcher delta, repository byte-identity.
  Nothing accepts: a staged record carries `approval_granted: []` and
  promotion is a human editing the seed and running the ordinary loop.
  Receipts are deterministic and are written for refusals too.
  `ActionKind.WRITE` also has its first adapter: `WriteStagingVerifier` runs
  inside the ordinary `controller.py` loop, and the state it advances is a
  RECEIPT LEDGER of `(record_id, outcome)` pairs — no node, no seed source, no
  corpus content — so accepting a WRITE means a receipt exists, not that
  anything was learned. STAGED_CANDIDATE maps to PROVEN, STAGED_REVIEW_REQUEST
  to VERIFIED, everything else to REFUSED with no next state. Still open:
  - **RETRACTED AND FIXED — candidate code no longer executes.** Independent
    review showed that scratch cwd plus a post-hoc digest detects damage but
    cannot prevent or restore it. A candidate seed is now accepted only when
    its AST is the exact canonical envelope around a literal JSON corpus;
    trusted staging code materializes that data. Extra imports, callbacks,
    validator rewrites, and path tricks refuse at `declarative_seed` before
    any candidate-controlled action. The working digest now covers the
    repository-relevant state recursively (excluding `.git`, `.venv`,
    `.worktrees`, caches, the confined receipt directory, and ignored runtime
    experiment artifacts) as a concurrent-change backstop, not as a sandbox.
    The experiment exclusion is load-bearing: an unrelated checkpoint or log
    may be large and may change during a gate run, while committed experiment
    source and result JSON remain covered. Likewise, a candidate-supplied proof
    digest is no longer a
    trust root: `prover/proof-artifact-manifest.json` independently pins allowed
    artifacts, whose bytes are captured once and reused for digest, closure,
    trace, and correspondence.
  - **structural unambiguity is stricter than the corpus.** A candidate whose
    skeleton some committed statement already declares is refused, because
    correspondence cannot say which of them the theorem proves. That is right
    for new content and would reject a genuine second reading of a shared law;
    a disambiguating signal (discipline-typed slots, canonical objects) would
    let such candidates through honestly.
  - **Existing-corpus write-back remains open.** The declarative envelope is a
    complete single-corpus seed. It can safely stage a new seed/new corpus pair,
    but it cannot replace `seed_logic.py` (which owns logic and set theory) or
    another existing authoring program without potentially orphaning outputs.
    Such proposals now refuse at `seed_ownership`; an untracked new seed supplied
    through `seed_source_path` remains valid. The next rung needs a trusted,
    seed-aware patch format that preserves every output owned by the original
    seed; executing candidate code or treating a materialized JSON file as proof
    of the replacement seed is explicitly not that format.
  - **no acceptance path at all.** Reviewing a staged receipt and applying it
    is unautomated by design for now; a `--apply` that ran the ordinary loop
    under a human's signature is the obvious next rung and needs its own
    authority argument.

- **PARTIAL — ASK is executable; open dialogue and durable sessions remain.** An unresolved slot
  can be answerable but absent from every durable store because its source of
  truth is the interlocutor: desired tone, ambiguous referent, private fact, or
  unstated constraint. Define `ASK(slot)` as retrieval from the user for these
  frame-private UNKNOWNs. Its return value must bind the slot in mutable session
  state and resume the same controller branch, which implies a multi-turn frame
  lifecycle rather than a one-shot prompt wrapper. `RetrievalNeed` now marks
  store vs user resolution before policy choice; ASK records a signed question,
  pauses the generic controller as WAITING, and a channel-signed reply resumes
  the same session with a frame-private `UserBinding`. While waiting, every
  non-reply action is frozen. Signatures establish passage through the host
  return-channel API, not real-world human identity. Still open: ~~durable session
  serialization~~ (**v0.16.0 status note (2026-08-21):** struck as
  self-contradictory with the next sentences — durable authenticated resume
  **shipped** at ROADMAP-v0.7 item 2, `ConversationSession.restore`;
  `scripts/conversation.py`), actual UI/transport integration, open-English parsing,
  learned question rendering, and the deterministic dispatcher across
  derivable/store/user/terminal channels before a learned chooser is evaluated.
  Consumption is verifier-private but commits only through the controller's
  run-level commit hook after completion/waiting callbacks succeed. **Durable
  restoration now preserves that atomicity without serializing the secret**
  (v0.7 item 2): `commit_run` still owns every write, and what crosses a
  restart is a *signed snapshot of what it already committed*, never a
  re-derivation from public state. Import merges and can only ever *add*
  refusals — there is no path in which restoring removes a consumed request or
  an existing supersession.

- **PARTIAL — dead branches are traced and pruned; terminal taxonomy remains.**
  The controller records state-before, action, verifier verdict/reason/evidence,
  and state-after for every proposal. A rejected branch leaves state unchanged,
  and the same action at the same state is pruned as REFUSED on repetition;
  tests prove a later valid branch resumes from the pre-rejection state. Still
  open: serializable trace schema, dependency/result references richer than
  strings, and distinct terminal outcomes for contradicted, tool-missed,
  user-deferred, and budget-limited searches. Only independently PROVEN
  conclusions remain eligible for the durable `WRITE` path.

## Parser / matcher

- **No call juxtaposition.** `D(F)(POINT)` fails to parse (`parse_atom`
  returns after the first call). Forced the calculus corpus to reshape the
  chain rule via a `COMPOSE(...)` head. Support `expr(...)` application or
  document the `COMPOSE` convention as canonical.
- **Big-op prefix namespace hazard.** Identifiers starting `sum_ prod_ lim_
  max_ min_` silently become prefix big-operators; and `lim_h` (big-op) vs
  `LIM(...)` (plain call) produce different skeleton heads that can never
  twin. Normalize: lower-case the big-op head AND fold `LIM(` calls into the
  same head, or lint templates for the ambiguity.
- **Specialization matching (v2): SHIPPED** as `scripts/specialize.py`
  (slot-to-subtree absorption + identity-element binding for parameter
  slots, looseness-ranked). The recorded misses now fire: equation of
  exchange >= ideal gas law (absorption over the dimensional constant),
  Cobb-Douglas <= power-law rate (absorption), circumference <= affine
  family (identity). Remaining out of scope: *series-truncation* relations
  (simple interest as the first-order truncation of continuous
  compounding) need rewrite-based reasoning, not matching.
  **v3: SHIPPED** (branch `tooling/cheapest-derivation`): the matcher now
  returns the cheapest derivation rather than the first, so `looseness` has
  the `cost` companion axis the first-success entry below asked for.
- **Specialization noise control.** 236 edges among 67 nodes; looseness
  ranking surfaces tight ones, but variable slots can still bind numeric
  literals (trapezoid >= rectangle-perimeter binds HEIGHT->2). Consider
  category-compatibility constraints on bindings (V slots should not bind
  nums; P slots should not bind V-rooted subtrees).
- **Call args are ordered, so commutative call heads need an authoring
  convention.** `MEET`/`JOIN` are commutative in every model of a Boolean
  lattice, but the matcher flattens/sorts only the `op` heads in
  `COMMUTATIVE = {+, *}`; a `call` keeps its argument order. `MEET(X, TOP)`
  and `MEET(TOP, X)` are therefore different skeletons. The logic/set corpora
  twin only because `scripts/seed_logic.py` generates both from one shared
  format string and fixes the order (distinguished operand first, special
  element second). Fix: let a template declare commutative call heads, or
  lint for the same head appearing with permuted argument categories.
  **SHIPPED** as `HEAD_ALGEBRA` in `scripts/match_signatures.py` (branch
  `tooling/head-algebra`): a declared table of per-head commutativity,
  associativity, identity and annihilator, each entry citing the node that
  justifies it. `canonicalize` and `typed_resort` now sort the arguments of
  declared-commutative call heads (sort only — flattening would need the
  `associative` field, which no pass consumes). Adjudicated: **no twin group
  changed membership at any level**, exactly as predicted, because the
  corpora were authored to the convention the declaration now enforces; four
  nodes' skeleton *strings* reorder (`logic`/`settheory.boolean_laws.identity_laws`
  to `?0:V = MEET⟨?1:P, ?0:V⟩`, `logic.inference.modus_ponens` to
  `IMPLIES⟨MEET⟨?0, IMPLIES⟨?0, ?1⟩⟩, ?1⟩`, and
  `narrative.causality.precedence_causation_bridge` at aliased level). The
  convention is now robust rather than lucky: a future `MEET(TOP, X)` spelling
  lands in the same group as `MEET(X, TOP)`.
- **No binder syntax, so optimizations cannot be compared.** Channel capacity
  is `C = max over p(x) of I(X;Y)`: a maximization over a *family*, with a
  constraint set (the probability simplex). The grammar has identifiers,
  arithmetic, calls, prefix big-ops and relations — no binder — and the one
  spelling that looks natural, `max_p I(X;Y)`, collides with the `max_`
  big-operator namespace above and would silently drop the constraint set
  anyway. `infotheory.channel.channel_capacity` therefore uses an opaque
  `CAPMAX(objective, argument)` call: it parses, it records the dependency,
  and it makes the internal structure of the optimization invisible to the
  matcher. Every argmax/argmin/sup statement anyone adds later will hit this.
  Fix: a `MAX(body, binder, domain)` form (or a real binder node) that the
  canonicalizer treats as a scoped construct.
- **Specialization noise swamps big-op nodes.** All 11 specialization edges
  touching the new information-theory nodes are of the degenerate kind already
  noted under "Specialization noise control": a P slot binds the literal `1`
  and a V slot swallows an entire `sum⟨...⟩` subtree, producing e.g.
  `physics.mechanics.hookes_law >= infotheory.entropy.shannon_entropy` (Hooke's
  law "generalizes" Gibbs/Shannon entropy because `-(k*x)` matches
  `-(anything)`). Zero of the 11 is informative. Category-compatibility
  constraints on bindings, plus a rule that a variable slot may not absorb a
  big-operator subtree, would remove essentially all of them.
- **The genuine specialization we wanted does not fire.**
  `infotheory.entropy.uniform_entropy` (`H = k*LOG(N)`) really is
  `infotheory.entropy.shannon_entropy` (`H = -(k * sum_i p_i*LOG(p_i))`) with
  `p_i = 1/N`, and the same substitution takes Gibbs to Boltzmann's
  `S = kB ln W`. `specialize.py` cannot see it: collapsing a sum under a
  constant summand is a *rewrite* (algebraic simplification), not slot-to-
  subtree absorption. Same class as the recorded series-truncation miss. The
  edge is asserted by hand via `special_case_of`/`generalizes`, which means the
  most pedagogically important specialization in the corpus is the one the
  tooling cannot check.
- **Specialization matcher is arithmetic-only.** `COMMUTATIVE = {+, *}` and
  `IDENTITY = {+: 0, *: 1}` are hardcoded, so `specialize.py` finds *zero*
  edges touching the 18 logic/set_theory nodes even though those nodes
  literally state their own identity elements (`MEET(X, TOP) = X`,
  `JOIN(X, BOT) = X`) and their own annihilators. Generalizing IDENTITY to a
  per-head table sourced from `identity_laws`-style nodes would let e.g.
  De Morgan >= the degenerate one-operand case fire, and would give the
  Boolean corpora any specialization structure at all.
  **SHIPPED** (branch `tooling/head-algebra`): `IDENTITY` is gone, replaced by
  `match_signatures.identity_terms(head)` reading `HEAD_ALGEBRA`, and
  `specialize.py` additionally matches declared-commutative call heads in
  either argument order. The Boolean corpora now have specialization
  structure — four edges, all looseness 0, all cross-corpus in two of the four
  cases: `logic.boolean_laws.absorption >= logic.boolean_laws.idempotence`,
  `>= settheory.boolean_laws.idempotence`, and the two with
  `settheory.boolean_laws.absorption` as the general side, each binding the
  join operand to JOIN's declared identity BOT
  (`MEET(X, JOIN(X, BOT)) = MEET(X, X)`). Not the De Morgan edge the entry
  guessed at, but the same kind and arguably better: idempotence *is*
  absorption at the bottom of the lattice.
- **Discrete and continuous statements of one fact can never twin.** `sum_i X`
  parses to a call with head `sum`; `INTEGRAL(X)` parses to a call with head
  `INTEGRAL`. The two heads are unrelated strings, so the discrete and
  continuous forms of the *same* statement are structurally invisible to each
  other. The differential-geometry corpus produced the sharpest instance
  available: `difftop.vectorfields.poincare_hopf_index_theorem`
  (`EULERCHAR⟨?0:V⟩ = sum⟨?1:V⟩`) and `diffgeo.surfaces.gauss_bonnet_theorem`
  (`INTEGRAL⟨?0:V⟩ = *(?1:P, ?2:V)`) are the two halves of Chern's theorem —
  one theorem, proved from the other — and they share not one node. Same
  obstacle blocks probability normalization (`sum_i p_i = 1` vs
  `INTEGRAL(density) = 1`), every expectation, and every conservation law in
  the graph, all of which have both forms. This is bigger than the `lim_h` vs
  `LIM(...)` split already recorded above and has the same fix shape: a
  head-aliasing table (`sum` ~ `INTEGRAL` ~ `prod`, as accumulation operators)
  applied at a match level below `typed`, or an explicit `ACCUMULATE(...)`
  authoring convention that both forms adopt.
  **HALF SHIPPED** (branch `tooling/head-algebra`): `{"sum": "aggregate",
  "INTEGRAL": "aggregate"}` is now in `HEAD_ALIASES`, so the two heads *do*
  share a node at the ALIASED level. `prod` is deliberately not included — it
  is not linear aggregation, and no node in `data/` carries it. Adjudicated:
  **zero new twin groups.** All 23 sum/INTEGRAL-bearing nodes were rechecked;
  the four aliased groups containing `aggregate` are all pre-existing typed
  groups (weighted accumulation ×4, Shannon/Gibbs, cross-entropy ×2,
  FTC/Stokes-zero-form), none of which crosses the discrete/continuous divide.
  The alias removes one obstacle and reveals what was behind it: the three
  nodes whose right side is a bare `aggregate⟨?:V⟩` —
  `diffgeo.curves.arc_length_functional` (`?0:V = aggregate⟨?1:V⟩`),
  `difftop.degree.degree_regular_value_count` (`DEGREE⟨?0:V⟩ = aggregate⟨?1:V⟩`)
  and `difftop.vectorfields.poincare_hopf_index_theorem`
  (`EULERCHAR⟨?0:V⟩ = aggregate⟨?1:V⟩`) — are now separated *only* by whether
  the left side is a slot or a call, i.e. by the "same invariant, slot in one
  corpus and call head in another" entry in the Schema section. That entry was
  one obstacle among three for one pair; it is now the sole remaining obstacle
  for three pairs, and should be promoted accordingly. (The entry's other
  prediction, probability normalization, is untestable: `data/` has
  `sum_i p_i = 1` but no `INTEGRAL(density) = 1`.)
- **Three independent obstacles stacked on one pair.** Worth recording as a
  unit because fixing any one of them would not have made Gauss-Bonnet meet
  Poincaré-Hopf: (1) the `sum`/`INTEGRAL` head split above; (2) the Euler
  characteristic is a *slot* in Gauss-Bonnet and a *call head* in
  differential topology (see the Schema section); (3) Gauss-Bonnet carries an
  explicit `2*pi` normalization that the already-integer index sum does not, so
  even after (1) and (2) the arities differ. Any head-aliasing work should be
  tested against this pair, not against a single-obstacle example.
  **TESTED, one of three cleared** (branch `tooling/head-algebra`). After the
  `sum`/`INTEGRAL` alias the pair reads:
  - `difftop.vectorfields.poincare_hopf_index_theorem`:
    `EULERCHAR⟨?0:V⟩ = aggregate⟨?1:V⟩`
  - `diffgeo.surfaces.gauss_bonnet_theorem`: `aggregate⟨?0:V⟩ = *(?1:P, ?2:V)`

  Obstacle (1) is gone — both now carry `aggregate`. Obstacle (2) is intact:
  the Euler characteristic is the call head on one side and the `?2:V` slot on
  the other. Obstacle (3) is intact: the `2*pi` shows as an extra `*(?1:P, …)`
  against a bare aggregate. The pair remains blocked at every level, and the
  entry's warning was correct — a single-obstacle test (the ML
  `ACTIVATION`/`SIGMOID` pair, the morphology near-misses) would have declared
  head aliasing a success on the strength of a case it does not resolve.
- **A numeric literal in a slot position blocks an otherwise real match.**
  `diffgeo.curves.circle_curvature` is `CURVATURE = 1 / RADIUS` ->
  `?0:V = *(1, inv(?1:V))`, and the rate/density family (average rate of
  change, average speed, mass density, molarity) is
  `?0:V = *(?1:V, inv(?2:V))`. Curvature really is a density — turning per
  unit length — whose numerator has been normalized to 1, but the literal is
  not a slot and the arities differ, so nothing fires at shape, typed or
  family level. Authoring around it (inventing a `UNITLENGTH` numerator slot)
  would be a lie. Fix candidate: a match level in which a numeric literal may
  bind a parameter-like slot, which is the dual of the existing sign-absorption
  level; it should be reported separately from `typed` since it is strictly
  looser.
- **Wanted match level: slot recurrence, not slot shape.**
  `difftop.degree.brouwer_fixed_point` (`?0:V = SELFMAP⟨?0:V⟩`),
  `logic.boolean_laws.double_negation` (`?0 = NEG⟨NEG⟨?0⟩⟩`),
  `settheory.boolean_laws.idempotence` (`?0 = MEET⟨?0, ?0⟩`) and
  `calculus.integration.ftc_differentiation_part` (`?0 = D⟨INTEGRAL⟨?0⟩⟩`) are
  all "an operation that returns its argument" — fixed points, idempotents,
  involutions, left inverses — and no two of them twin, because they differ in
  arity and nesting depth. The family is defined by a *property* of the
  skeleton (one slot occurring on both sides of the relation at different
  depths) rather than by the skeleton itself, so twin detection cannot express
  it. Wanted: a structural *query* facility ("templates where slot S occurs on
  both sides of the relation") alongside the equality-based twin grouping.
- **Notation adoption is manual, and the corpus should say so out loud.**
  `diffgeo.stokes.stokes_theorem`
  (`INTEGRAL(D(FORM)) = BOUNDARYINTEGRAL(FORM)`) is the statement a geometer
  writes and it twins with nothing.
  `diffgeo.stokes.stokes_zero_form_case`
  (`INTEGRAL(D(F)) = F(ENDPOINT) - F(STARTPOINT)`) states the k=0 case in
  `calculus.integration.ftc_evaluation_part`'s own vocabulary and twins with it
  exactly. Both are honest; the difference is that an author who already knew
  the answer spelled the second one to match. Same pattern as
  `infotheory.mutualinfo.entropy_inclusion_exclusion` adopting CARD/MEET/JOIN.
  Two twin groups in the graph now exist because of hand translation rather
  than discovery, which is a real limit on any claim that the matcher *finds*
  cross-discipline structure. Worth a provenance flag on twin groups
  (`authored_to_match` vs `emergent`) so the ledger can report the two counts
  separately; `diffgeo.surfaces.gaussian_curvature_principal_product` joining
  `geometry.area_formulas.rectangle_area_formula` was emergent and should not
  be pooled with the two adopted ones.
- **Specialization noise now reaches nonsense.** The new corpora add edges like
  `chemistry.spectroscopy.beer_lambert_law >= diffgeo.surfaces.gauss_bonnet_theorem`
  (looseness 1, via identity) and
  `geometry.area_formulas.triangle_area_formula >= diffgeo.surfaces.gaussian_curvature_principal_product`.
  Beer-Lambert does not generalize Gauss-Bonnet. Same root cause as the
  entries above under "Specialization noise control" — variable slots absorbing
  arbitrary subtrees and parameter slots binding literals — and another vote
  for category-compatibility constraints on bindings.

- **Call heads are literal at every match level, so a new discipline's
  vocabulary is structurally quarantined.** `data/morphology` (10 nodes) fires
  **zero** twin groups at shape, typed *and* family level, and **zero**
  specialization edges (247 edges among 106 nodes, none touching it) — yet four
  of its skeletons are character-for-character an existing skeleton apart from
  one head string:

  | morphology | existing / predicted |
  |---|---|
  | `?0:V = CONCAT⟨?0:V, ?1:P⟩` (zero morpheme) | `?0:V = MEET⟨?0:V, ?1:P⟩` (logic + set identity laws) |
  | `?0:V = CONCAT⟨CONCAT⟨?1:V, ?2:V⟩, ?3:V⟩` (iterated affixation) | `?0:V = MOD⟨MOD⟨?1:V, ?2:V⟩, ?3:V⟩` (intensifier nesting, `docs/DESIGN-linguistic-twins.md`, not yet authored) |
  | `CATEGORY⟨?0:V⟩ = CATEGORY⟨CONCAT⟨?1:V, ?0:V⟩⟩` | `FEAT⟨?0:V⟩ = FEAT⟨CONCAT⟨?1:V, ?0:V⟩⟩` (both morphology; one theorem, Williams's Righthand Head Rule) |
  | `?0:V = CONCAT⟨?1:V, ?2:V⟩` (affixation) | `?0:V = REALIZE⟨?1:V, ?2:V⟩`, `?0:V = CAPMAX⟨?1:V, ?2:V⟩` |

  `seed_infotheory.py` escaped this by *adopting* the CARD/MEET/JOIN heads.
  Morphology cannot: adopting `MEET` for concatenation would assert
  commutativity and idempotence, which are false of words (`re-do` is not
  `do-re`). So faithful authoring alone cannot produce a twin, and the corpus
  most likely to need a new vocabulary is the one least able to match. Fix: a
  declared head-alias table (`CONCAT ~ MEET ~ MOD` as "opaque binary
  composition"), or a fourth match level below `shape` that erases call-head
  identity the way `shape` erases slot identity — reported separately so it
  cannot be mistaken for a typed twin.
- **`archetype_id` is currently the only cross-head channel, and it is filed as
  a lint.** `archetype_label_drift` now reports `identity_element_law` spanning
  `logic.boolean_laws.identity_laws`,
  `settheory.boolean_laws.identity_laws` and
  `morphology.wordformation.zero_morpheme_identity` — the hand-assigned label
  says one law, the skeletons say three, and the label is right.
  `morphology.derivation.category_from_affix` and
  `morphology.agreement.feature_percolation` share
  `right_hand_head_projection` for the same reason. Both entries are
  deliberate. Fix: promote "same archetype_id, skeletons differing only by call
  heads" from a drift warning to a *proposed head alias* output, which turns
  the lint into the discovery channel the previous item asks for.
  New strongest evidence (provability corpus, P-CF4):
  `provability.modal.loeb_axiom` adopts `temporal_induction` — argued, not
  convenient: Löb is well-founded induction along GL's accessibility
  relation (Segerberg), temporal induction is the same principle along
  successor — so a *discipline-named* label now spans a second discipline.
  The drift report is the only channel that carries the relationship (the
  skeletons cannot twin: BOX vs ALWAYS/NEXT heads, and the trees differ in
  exactly the reflection GL forbids). The label itself is now demonstrably
  too narrow for its extension; the promotion fix should also consider a
  rename pass for discipline-named archetype ids.
- **Per-head identity elements: third motivated head, and a new wrinkle.**
  `IDENTITY = {"+": 0, "*": 1}` in `specialize.py` is still arithmetic-only
  (recorded above for logic/set_theory). `morphology.wordformation.zero_morpheme_identity`
  states `CONCAT(STEM, EMPTY) = STEM`, so CONCAT is a third head declaring its
  own identity and getting nothing for it. The wrinkle morphology adds: the
  slot that should bind the identity is **variable-like**, not parameter-like —
  a zero morph *is* a morph, filling an affix slot with the empty string
  (`sheep` = sheep + ∅). The current rule ("variable-like slots may not
  vanish: a law does not lose its variables") is exactly what blocks the one
  edge worth having here, `iterated_affixation >= affixation` via
  `SUFFIX2 -> EMPTY`. Fix needs both parts: a per-head identity table sourced
  from identity-law nodes, and permission for a variable slot to bind an
  identity element *for a head whose identity the corpus has declared*.
  **SHIPPED** (branch `tooling/head-algebra`), both parts, and the predicted
  edge fires:
  `morphology.wordformation.iterated_affixation >= affixation`, looseness 0,
  via `SUFFIX1 -> EMPTY` — the *inner* affix vanishes rather than the outer
  one this entry guessed, which is the same law read the other way round
  (`CONCAT(CONCAT(STEM, ∅), SUFFIX) = CONCAT(STEM, SUFFIX)`) and puts the zero
  morph where a linguist would, between stem and suffix. Two more morphology
  edges came with it: `iterated_affixation >= zero_morpheme_identity` (both
  affixes empty) and `concat_associativity >= zero_morpheme_identity`. The
  mechanism is `match_via_head_identity`: a call whose vanishing argument is a
  slot collapses to its other argument. Note it is NOT the "arguments run out"
  rule generalized — a call has fixed arity, so the collapse is a rewrite of
  the pattern, and it needs its own non-triviality guard (below).
- **Associativity and commutativity are one package in the canonicalizer.**
  `COMMUTATIVE = {+, *}` gets flattening (associativity) and sorting
  (commutativity) together, and call heads get neither.
  `morphology.wordformation.concat_associativity` is the corpus's first
  associative-but-not-commutative operation, so `CONCAT(CONCAT(A,B),C)` and
  `CONCAT(A,CONCAT(B,C))` are different skeletons even though the node asserts
  they are the same string. Fix: let a template declare a call head associative
  (flatten only) independently of commutative (flatten and sort). CONCAT must
  never be added to `COMMUTATIVE`.
  **HALF SHIPPED** (branch `tooling/head-algebra`): `HEAD_ALGEBRA` separates
  the two declarations — `CONCAT` is `associative: True, commutative: False`,
  cited to `morphology.wordformation.concat_associativity` and to the corpus's
  own `re-do` is not `do-re` note — and `COMMUTATIVE` /
  `COMMUTATIVE_CALL_HEADS` are now *derived* from the table rather than
  hardcoded, so CONCAT cannot be added to `COMMUTATIVE` by accident. What is
  **not** shipped is a consumer: no pass reads `associative`, so
  `CONCAT(CONCAT(A,B),C)` and `CONCAT(A,CONCAT(B,C))` are still different
  skeletons. The remaining work needs a decision the commutative case did not:
  a flattened n-ary `CONCAT` has no spelling in the grammar, so either the
  skeleton renderer gains a variadic form or the canonicalizer
  right-associates instead of flattening.
- **`specialize.py` suppresses the plainest specializations of all.** Its
  filter is `if match(...) and (st.used_absorption or st.used_identity)`,
  justified in the docstring by "anything matchable without them is an exact
  twin and already in the skeleton report". That justification is false: two
  templates can match by *plain slot binding* and still have different
  skeletons, so they are in neither report. The topology corpora hit it twice
  in one seeding pass, both times on the relation the corpus most wanted:
  - `algtop.invariants.euler_characteristic_complex`
    (`EULERCHAR = VERTICES - EDGES + FACES`) covers
    `geotop.polyhedra.euler_polyhedron_formula` (`VERTICES - EDGES + FACES =
    2`) by binding `EULERCHAR -> 2`. Probed directly: `MATCHES = True,
    used_absorption = False, used_identity = False`.
  - `geotop.predicates.de9im_disjoint` (`MEET(REGA, REGB) = EMPTYSET`) covers
    `settheory.boolean_laws.complement_laws` (`MEET(SETA, NEG(SETA)) =
    FALSITY`) by binding `REGB -> NEG(SETA)`. Same probe result.
  A slot binding a numeric literal, and a slot binding a subtree with a call
  head, are the two commonest ways a general law becomes a special case, and
  both are dropped. Fix: report matches whose bindings are non-trivial (any
  slot bound to a `num`, or to a subtree of depth >= 1) even when neither
  absorption nor identity fired, and rank them by the same looseness score.
  Both edges are currently asserted by hand via `special_case_of` /
  `generalizes`.
- **Specialization noise, third confirmation.** All 16 specialization edges
  touching the 15 topology nodes are degenerate: `betti_number_rank`
  (`BETTI = CYCLERANK - BOUNDARYRANK`) "generalizes"
  `settheory.cardinality.inclusion_exclusion_two_sets` because a variable slot
  swallows a whole `CARD⟨...⟩` subtree. Zero are informative — the same
  outcome the information-theory corpus recorded. The proposed
  category-compatibility constraint on bindings is now supported by three
  independent corpora and should be considered load-bearing rather than nice
  to have.
- **No way to declare a call head commutative, so symmetry must be a node.**
  `geotop.predicates.adjacency_symmetry` exists only because
  `TOUCHES(A, B)` and `TOUCHES(B, A)` are different subtrees, and the corpus
  has no other way to say the head is symmetric. That is the same limitation
  already recorded above for `MEET`/`JOIN`, but seen from the other side:
  every Boolean-corpus node silently *assumes* commutativity of its head, and
  this is the first node in `data/` that *asserts* it. If a commutative-head
  declaration is added, this node is the test case for it.
  **SHIPPED** (branch `tooling/head-algebra`): `TOUCHES` is declared
  commutative in `HEAD_ALGEBRA` with this node as its cited justification —
  the only ASSERTED commutativity in the table, everything else being DERIVED
  or CONVENTION. Adjudicated against the test case, with a result worth
  keeping: **the node's own skeleton does not change**. Sorting uses
  `shape_key`, which erases slot identity, so `TOUCHES⟨?0, ?1⟩` and
  `TOUCHES⟨?1, ?0⟩` have equal sort keys and the stable sort leaves both
  alone. Declaring a head commutative therefore does *not* collapse a symmetry
  statement into a tautology, which is the desirable outcome (the node still
  says something) but also means this test case cannot demonstrate the
  feature. A head whose arguments differ in *shape* is what the sort acts on;
  `logic.inference.modus_ponens` is the only node in `data/` that supplies one.
- **The one relation nested inside a call argument matches nothing.**
  `geotop.measure.area_monotonicity` is
  `IMPLIES(LEQ(REGA, REGB), CARD(REGA) <= CARD(REGB))` — an order-preservation
  claim, with a lattice order in the premise and a numeric order in the
  conclusion. It parses cleanly (`parse_args` calls `parse_relation`), but it
  is the only such statement in the graph, so there is nothing to twin with.
  Not a bug; recorded so that a future monotone-functional node (entropy is
  monotone under coarsening, cardinality under inclusion, measure under
  containment) is written with *this* template rather than a fresh one.

- **Five heads now share the two-argument opaque-composition shape and none
  of them twin.** `?0 = HEAD⟨?1, ?2⟩` is carried by
  `morphology.wordformation.affixation` (CONCAT),
  `morphology.inflection.paradigm_realization` (REALIZE),
  `infotheory.channel.channel_capacity` (CAPMAX),
  `geotop.predicates.de9im_disjoint` (MEET) and
  `ml.recurrence.belief_state_update` (UPDATE). Five nodes, five heads, zero
  groups at shape, typed or family level. This is the cheapest available
  measurement of what head literalism costs, and it grows by one every time a
  corpus needs a vocabulary the graph does not already have.
- **Head literalism, now with a minimal reproducer inside one file.** The
  morphology entry above argues from four near-misses across corpus
  boundaries. `data/machine_learning` supplies the smallest possible case:
  `ml.recurrence.elman_rnn_hidden_state` is
  `?0:V = ACTIVATION⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` and
  `ml.recurrence.lstm_gate_activation` is
  `?0:V = SIGMOID⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` — the same string
  apart from one head token, authored by one hand in one file with no intent
  to hide the relationship — and they share no group at shape, typed *or*
  family level. `shape` is documented as the loosest level and it still
  cannot see a one-token difference. Any head-alias mechanism should be
  tested against this pair before the harder morphology ones.
- **A call head quarantines everything under it, including the corpus's
  largest family.** The argument of that `ACTIVATION(...)` is an affine map,
  and the affine family (`?0:V = +(?1:P, *(?2:P, ?3:V))`, five members across
  four disciplines) is the best-populated group in the graph. Nothing
  relates them. Worth separating from the head-alias item because *two*
  fixes are needed and neither suffices alone: erasing head identity would
  still leave the pre-activation as *multiple* linear regression (two
  weighted regressors) against a corpus that carries only the simple
  one-regressor form, so the arities differ as well.
- **No `min`, no `clip`, no piecewise form — the PPO ceiling.** Extends the
  "no binder syntax" entry above with a second family of missing constructs.
  `ml.policy.ppo_clipped_surrogate` needs a binary minimum and an interval
  clamp; the grammar has neither, and the natural spelling for the first
  collides with the `min_` big-operator namespace already recorded. Both are
  written as opaque calls (`MINOF`, `CLIPCALL`), which parse and record
  dependencies while hiding the entire mechanism — the clamp's flat gradient
  outside the trust region is what the method *is*. Consequence: the node is
  a singleton at every level and cannot be compared with TRPO's constrained
  form or any other trust-region method. Also: `MINOF` is commutative in
  every model and the matcher cannot know it, the same ordered-call-args
  problem `MEET`/`JOIN` and `TOUCHES` already have.
- **`*` means two different operations and the canonicalizer picks one.**
  `COMMUTATIVE = {+, *}` gets flattening *and* sorting, so `*` can only
  denote a commutative product. Machine learning needs it for matrix-vector
  application and for outer products, neither of which commutes.
  `ml.recurrence.linear_ssm_state_update` escapes only because S4D and Mamba
  use a *diagonal* state matrix, making the per-channel recurrence genuinely
  scalar; `ml.recurrence.mlstm_matrix_memory_update` cannot escape, since
  `v k^T` is irreducibly a rank-one matrix, and had to introduce an
  `OUTER(.,.)` head. That extra node is one of the two reasons the two
  state-update equations do not twin. Related to the CONCAT associativity
  entry above but distinct: there the head had no algebra declared, here the
  head has the *wrong* algebra declared. Fix shape: a non-commutative
  multiplication head, or a per-head associativity/commutativity table that
  `*` itself participates in.
  **PARTIALLY ADDRESSED** (branch `tooling/head-algebra`): the table exists and
  `*` participates in it — `HEAD_ALGEBRA["*"]` is now the source of truth for
  `COMMUTATIVE`, and its comment records the over-declaration by name
  (`OUTER`, `CROSS`). It is still declared commutative, because ~30 scalar
  products carrying the affine and rate families need it that way and nothing
  lets a single template opt out. So the *cost* is now written next to the
  declaration instead of only in this file, and the fix is unchanged: a second
  multiplication head, or per-node algebra overrides. `CROSS`'s antisymmetry
  stays inexpressible — the table carries boolean commutativity only, and
  inventing a third value for one node would declare more than `data/`
  justifies.
- **`specialize.py` plain-binding suppression, fourth instance, and the one
  the node most wanted.** `infotheory.entropy.surprisal`
  (`?0:V = neg(LOG⟨?1:V⟩)`) covers `ml.preference.dpo_preference_loss`
  (`?0:V = neg(LOG⟨SIGMOID⟨*(?1:P, +(?2:V, neg(?3:V)))⟩⟩)`) by binding the
  argument slot to the `SIGMOID⟨...⟩` subtree — and the relation is exact,
  since SIGMOID's output is the Bradley-Terry probability that the annotator
  preferred the chosen completion, so the DPO loss *is* the surprisal of the
  observed preference. Neither absorption nor identity fires, so the filter
  drops it, exactly as recorded for the two topology cases. Three corpora
  have now lost their headline specialization to this one filter.
- **Specialization noise, fourth confirmation, and now it reaches training
  objectives.** Of 47 specialization edges touching the 14 machine-learning
  nodes, the informative ones are three:
  `probstat.regression.slr_stochastic_specification >= linear_ssm_state_update`
  (intercept to 0, noise slot absorbing the autoregressive term — an AR(1)
  process is the regression of a series on its own past),
  `probstat.transform.affine_location_scale >= lora_low_rank_update`, and
  `boltzmann_softmax_policy >= chemistry.kinetics.arrhenius_equation`. The
  rest are the known degenerate kind:
  `physics.mechanics.hookes_law >= ml.objective.token_cross_entropy_loss`
  (Hooke's law "generalizes" the training loss of a language model, because
  `-(k*x)` matches `-(anything)`),
  `chemistry.spectroscopy.beer_lambert_law >= grpo_group_relative_advantage`,
  `geometry.area_formulas.triangle_area_formula >= boltzmann_softmax_policy`,
  `physics.mechanics.newton_second_law >= policy_probability_ratio`. Same
  root cause, same proposed fix (category-compatibility constraints on
  bindings, plus a rule that a variable slot may not absorb a call-rooted
  subtree), now supported by four independent corpora.
- **Two deliberate `skeletons_with_split_archetypes` entries.**
  `?0 = *(?1, EXP⟨neg(*(?2, ?3))⟩)` now spans `exponential_decay` and
  `normalized_exponential_tilt`, and `?0 = +(?1, neg(*(?2, ?3)))` spans four
  labels including `state_minus_scaled_correction` (gradient descent) and
  `value_minus_weighted_penalty` (the RLHF objective). Both are intentional:
  the skeletons are shared and the statements are not the same statement.
  `ml.policy.policy_probability_ratio` went the other way and adopted the
  existing `ratio_rate` label rather than minting one. Recorded because the
  lint cannot currently distinguish "same structure, genuinely different
  claim" from "same claim, drifting label", and this corpus deliberately
  produced both.

- **A numeric literal in a multiplicative position, third and fourth
  confirmations — and the specialization matcher already fixes half of it.**
  docs/BACKLOG.md records `diffgeo.curves.circle_curvature` (`1 / RADIUS`)
  being kept out of the rate/density family by a literal `1`. The
  numerical-analysis and graph-theory corpora hit the same wall twice more,
  from the other side: `graphtheory.degree.average_degree_from_edge_count`
  (`?0:V = *(2, ?1:V, inv(?2:V))`) versus the seven-member rate family
  (`?0:V = *(?1:V, inv(?2:V))`), and
  `numanalysis.rootfinding.bisection_interval_halving`
  (`?0:V = *(?1:V, inv(2))`) versus the same family with the literal in the
  denominator. The new information is that `specialize.py` **does** recover the
  first one — `calculus.differentiation.average_rate_of_change >=
  average_degree_from_edge_count` via absorption, binding
  `QUANTITY -> *(2, EDGES)`, and likewise from molarity — so the relation is
  reachable, just not as a twin. That is now a repeatable pattern worth naming
  in its own right (a twin-level miss recovered one level down, first recorded
  for the ML state-space update), and it argues the wanted "numeric literal may
  bind a parameter-like slot" match level should be specified as a *twin*
  level, since the specialization level already covers the case where the
  literal can be absorbed into a variable slot but not the case where it must
  bind a parameter slot (bisection).
- **`decompose.py` sees three relations the twin matcher structurally cannot,
  and the pattern is predictable.** All three come from one cause: decompose
  compares *expression sides*, so it is blind to the relation symbol and to
  slot recurrence across the relation. Instances from this seeding pass:
  1. `numanalysis.floatingpoint.machine_epsilon_bound`
     (`ROUNDOFF <= UNITROUNDOFF*EXACT`) is a whole-statement singleton purely
     because of the `<=`; decompose reports its right side as `*(?0:P, ?1:V)`,
     the expression side of Ohm's law, Newton's second law and circle
     circumference, recurring in 35 statements. Every error bound anyone adds
     will be isolated at twin level and connected at decomposition level.
  2. `numanalysis.rootfinding.fixed_point_iteration`
     (`?0:V = SELFMAP⟨?1:V⟩`) does not twin
     `difftop.degree.brouwer_fixed_point` (`?0:V = SELFMAP⟨?0:V⟩`) because of
     slot recurrence — but decompose reports its expression side as *being*
     Brouwer's expression side, since on one side of the relation the
     recurrence is invisible. The two tools disagree, both correctly, about
     the same pair.
  3. `numanalysis.rootfinding.newton_iteration` misses the whole
     iteration/update family over one `inv` node, and decompose finds its
     correction term `*(?0:V, inv(?1:V))` is the rate/density family's
     expression side (11 statements) — i.e. a Newton correction is a rate.
  Proposal: rather than three more match levels, have `match_signatures.py`
  cross-reference `decompose.py`'s side-forms and report "singleton at every
  level, but its expression side is a known form shared with N statements" as
  a fourth report section. It costs nothing new and it would have caught all
  three of these automatically.
- **Head literalism: the two-argument opaque-composition count reaches seven,
  two of them added in one pass.** `?0 = HEAD⟨?1, ?2⟩` is now carried by
  `morphology.wordformation.affixation` (CONCAT),
  `morphology.inflection.paradigm_realization` (REALIZE),
  `infotheory.channel.channel_capacity` (CAPMAX),
  `geotop.predicates.de9im_disjoint` (MEET),
  `ml.recurrence.belief_state_update` (UPDATE),
  `graphtheory.walks.adjacency_power_walk_count` (MATRIXPOWER) and
  `geomodel.surfaces.surface_normal_cross_product` (CROSS). Seven nodes, seven
  heads, zero groups at any level. The two new ones sharpen the diagnosis: both
  exist *because `*` is hardcoded commutative*. MATRIXPOWER cannot use `^`
  because matrix multiplication does not commute; CROSS cannot use `*` because
  it ANTI-commutes. This is the same root cause as
  `ml.recurrence.mlstm_matrix_memory_update`'s OUTER, and it means the
  per-head associativity/commutativity table already requested for CONCAT is
  now blocking four nodes in three corpora, not one. CROSS additionally needs
  a value the table cannot currently express (antisymmetric), and the cost is
  concrete: the cross product's magnitude is a rectangle area, and
  `?0:V = *(?1:V, ?2:V)` is a three-discipline group in the same graph.
- **Two inequalities, opposite in kind, indistinguishable to the matcher.**
  `numanalysis.floatingpoint.machine_epsilon_bound` (never attained, a
  guarantee) and `graphtheory.planarity.planar_edge_bound` (attained by every
  maximal planar graph, an extremal identity in disguise) are both singletons
  for the same mechanical reason — the relation symbol is part of the skeleton
  — and the graph has no way to say that the second is an equality on a
  subfamily while the first is not. Related to but distinct from the
  `geotop.measure.area_monotonicity` entry above: that one is isolated for
  being the only *nested* relation, these two for being non-`=` at top level.
  Wanted: a flag or slot-schema note distinguishing tight/attained bounds from
  loose ones, so an extremal statement can eventually be related to the
  equality case it saturates.

- **`specialize.py` cannot use a non-equation as a general pattern, so every
  inference rule in the graph is excluded from the general side.**
  `find_specializations` opens with `if gtree[0] != "rel": continue`, which
  silently drops any node whose canonical template is a bare call rather than a
  relation. That is **16 of 195 nodes**: `logic.inference.modus_ponens`,
  `logic.inference.ex_falso_quodlibet`, `logic.inference.reductio_ad_absurdum`,
  `settheory.order.subset_transitivity`,
  `settheory.order.empty_set_minimality`,
  `geotop.predicates.containment_transitivity`,
  `geotop.predicates.adjacency_symmetry`, `geotop.measure.area_monotonicity`,
  `algtop.homotopy.homotopy_invariance` and the seven rule-shaped nodes in
  `data/temporal_logic` / `data/narrative`. Concrete cost, and the case that
  found it: `temporal.response.response_pattern`
  (`ALWAYS(IMPLIES(TRIGGER, EVENTUALLY(RESPONSE)))`) covers
  `narrative.constraint.chekhov_gun`
  (`ALWAYS(IMPLIES(PLANTED(ELEMENT), EVENTUALLY(DISCHARGED(ELEMENT))))`) by
  binding `TRIGGER -> PLANTED(ELEMENT)`, `RESPONSE -> DISCHARGED(ELEMENT)`.
  Probed directly: `MATCHES = True, used_absorption = False,
  used_identity = False`. Two filters stacked — this one first, then the
  plain-binding suppression already recorded five times — so Chekhov's gun
  being an instance of an LTL liveness pattern has to be asserted by hand.
  Fix: drop the `rel` guard and gate on `op_count` alone (the guard's stated
  purpose, avoiding near-trivial patterns, is already served by
  `op_count(gtree) < 2`).
- **`decompose.py` rates a recursive definition as maximally ungrounded, which
  breaks the epistemic ladder's one graded rung: SHIPPED** (groundedness v2).
  `decompose.py` now detects a *definiendum* — a bare application of a named
  head to leaves whose head recurs, under a different head, on the other side
  of the relation — marks the statement `"recursive": true`, and drops its
  self-headed constituents from the DENOMINATOR rather than failing them.
  Measured: `temporal.recurrence.until_unfolding` **0.000 -> 1.000** (2
  `UNTIL⟨?1, ?0⟩` constituents excluded as definitional; the remaining
  `JOIN⟨...⟩`, `MEET⟨...⟩`, `NEXT⟨...⟩` all ground),
  `temporal.modality.eventually_unfolding` **0.500 -> 1.000**. Those two are
  the only nodes in the 197 the detector fires on, which took three guards to
  achieve — each was measured firing wrongly first: without a `call`-only
  restriction the Pythagorean theorem "defines" `^` and the ideal gas law
  "defines" `*`; without requiring the other side's root head to differ,
  `ALWAYS(ALWAYS(P)) = ALWAYS(P)`, `CATEGORY(CONCAT(STEM, AFFIX)) =
  CATEGORY(STEM)` and contraposition all read as definitions of their own head
  and had their denominators emptied to nothing, scoring 1.000 by vacuity. The
  loose version inflated the corpus mean to 0.862 on 13 spurious "recursive"
  nodes. Honest caveat: this fix *alone* would have dropped
  `eventually_unfolding` 0.500 -> 0.000, because excluding `EVENTUALLY⟨?0⟩`
  removes its one recognized constituent from the numerator too; it is only
  safe together with the pattern-membership fix below, and the two shipped
  together.
  Original report: `temporal.recurrence.until_unfolding`
  (`UNTIL(PROPA, PROPB) = JOIN(PROPB, MEET(PROPA, NEXT(UNTIL(PROPA, PROPB))))`)
  scores **groundedness 0.000** — the lowest of the seventeen nodes in that
  seeding pass, on an axiom of a fifty-year-old logic. Cause: all five of its
  non-trivial constituents contain `UNTIL`, the head being defined
  (`JOIN⟨?0, MEET⟨?1, NEXT⟨UNTIL⟨?1, ?0⟩⟩⟩⟩`, `MEET⟨?1, NEXT⟨UNTIL⟨?1, ?0⟩⟩⟩`,
  `NEXT⟨UNTIL⟨?1, ?0⟩⟩`, `UNTIL⟨?1, ?0⟩` twice), and the form inventory is
  built from *other* statements, where the head does not occur. Its Boolean
  neighbour `temporal.modality.next_distributes_over_meet` scores 0.600 with
  its `MEET⟨?0:V, ?1:V⟩` constituent recognized in 10 statements, so the
  contrast is internal to one corpus. Per `docs/DESIGN-epistemic-ladder.md`
  groundedness grades the UNGROUNDED rung, so a correct axiom currently lands
  where near-gibberish lands, and every recursive definition anyone adds
  (factorial, Fibonacci, a grammar production, the mu-calculus fragment) will
  land there too. Fix: while decomposing a statement, treat that statement's
  own root head as a known form.
- **Groundedness measures vocabulary overlap, so a new discipline's first
  corpus is guaranteed to grade as disorder.** Across the 17 nodes of
  `data/temporal_logic` + `data/narrative` the score is almost perfectly
  predicted by how many pre-existing heads the template reuses: 1.000 for the
  two nodes written entirely in adopted heads
  (`temporal.order.precedence_transitivity`,
  `narrative.frame.frame_consistency`), 0.400–0.750 for mixed templates, and
  0.000 for all five written only in heads the corpus introduced
  (`until_unfolding`, `chekhov_gun`, and the three
  `narrative.structure.*` unit definitions). This is the numeric form of the
  already-recorded "a new discipline's vocabulary is structurally quarantined".
  Sharper instance: `narrative.constraint.chekhov_gun` is written *entirely* in
  the temporal corpus's ALWAYS/IMPLIES/EVENTUALLY vocabulary and still scores
  0.000, because its constituents are `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` and
  `PLANTED⟨?0⟩` rather than `EVENTUALLY⟨?0⟩` — one extra unary head under the
  modality changes the skeleton. The general pattern it instantiates scores
  0.500 on the same formula shape, so an instance grades *lower* than its
  pattern, which inverts what the score is for.
  **The instance-below-its-pattern half is SHIPPED** (groundedness v2): a
  constituent that fails exact skeleton lookup is now re-tried with
  `specialize.py`'s matcher, every known form used AS PATTERN against it, so
  `EVENTUALLY⟨?0⟩` covers `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` by binding the slot to
  the instantiated call. Reported per constituent as `"grounded_via":
  "pattern"` with the form it instantiates, and counted separately from
  `grounded_exact`. Evidence gate: the match must bind some slot to a
  *named-head application*; slot-to-slot renaming is refused (that is a twin,
  and accepting it would grade P-vs-V category mismatches as grounding), and
  so are commutative absorption and identity-element binding, which are
  specialization and where `specialize.py`'s recorded noise lives — allowing
  them moves the mean by only +0.003 but credits e.g. Beer-Lambert's
  `?0:P * ?1:V * ?2:V` with grounding `?0:P * D⟨?1:V⟩` by vanishing a factor.
  Measured, 197 nodes: **corpus mean 0.700 -> 0.761**, 32 statements rise,
  **zero fall**, scores at 0.000 fall from 28 to 24, at 1.000 rise from 106 to
  124; 403 constituents ground exactly and 50 via pattern membership.
  `narrative.constraint.chekhov_gun` **0.000 -> 0.500** and its abstraction
  `temporal.response.response_pattern` **0.500 -> 1.000** — the inversion is
  gone (the instance no longer grades *below* its pattern), and the remaining
  gap is honest rather than mechanical: Chekhov's two ungrounded constituents
  are exactly `PLANTED⟨?0⟩` and `DISCHARGED⟨?0⟩`, heads that occur in no other
  statement.
  **The vocabulary-overlap half stays OPEN.** The four
  `narrative.structure.*` unit definitions are still 0.000 -> 0.000: they are
  written entirely in heads no other statement uses, so no pattern can cover
  them, and nothing short of the epistemic ladder distinguishing "new
  primitive" from "gibberish" will move them. The rest of that seeding pass
  did move — every other `data/temporal_logic` node now grades 1.000 — which
  narrows the quarantine claim to nodes introducing *unshared* heads rather
  than nodes in a new discipline.
  **Counterexample from the other direction (provability corpus, PV3
  missed): the score also fails OPEN.** All six `data/provability` nodes
  ground at **1.000** on arrival, though BOX occurs nowhere else in the
  graph: intra-corpus recurrence is unconditionally sufficient (BOX⟨?0:V⟩
  recurs across three sibling nodes, BOX⟨?0:P⟩ across the other three, and
  NEG⟨BOX⟨?0:P⟩⟩ is verbatim the consistency definition's expression side),
  and the pattern channel absorbs the box entirely (Löb's reflection
  premise IMPLIES⟨BOX⟨?0:V⟩, ?0:V⟩ grounds as an instance of ex falso's
  IMPLIES⟨?0:P, ?1:V⟩ by a slot swallowing the boxed subtree). So
  "unshared" in the quarantine claim means *occurring in one statement*,
  not *new to the graph*: a hermetic six-node corpus that reuses one new
  head densely self-certifies to the score's maximum in a single authoring
  act, while temporal's singleton narrative heads stay at 0.000. Combined
  with the until_unfolding self-reference defect, the ladder's one graded
  rung has now been measured failing in both directions (correct axiom at
  0.000; brand-new vocabulary at 1.000). Fix shape: report intra-corpus
  and extra-corpus grounding separately (provenance is in the inventory
  already), and gate the pattern channel's slot-swallows-call credit on
  the swallowed head being known outside the statement's own corpus.
  **HALF SHIPPED** (branch `feature/grounding-channels`) — the reporting half
  of a two-half fix, which is why ROADMAP-v0.7 item 10's first bullet reads
  SHIPPED (its own scope was the split) while this entry reads HALF SHIPPED
  (its scope includes the gate). `decompose.py` now attributes every grounded
  constituent to `external` / `prior_corpus` / `same_corpus` / `recursive` /
  `pattern_absorption`, and the fails-open corpus reads out as
  `same_corpus` 0.775 + `pattern_absorption` 0.192 + `external` 0.033 — the
  1.000 stands, but nothing about it is external any more, and the run flags
  `provability.goedel_loeb.v1` as the graph's only `self_certifying` corpus
  (aggregate >= 0.9 with external + prior <= 0.1; two other corpora at
  aggregate >= 0.9 are correctly not flagged, so the flag is not a restatement
  of the aggregate), under both the generous and the conservative owner rule.
  The gating half is untouched on purpose: it changes scores and therefore
  needs its own registered prediction. Recorded en route:
  `temporal.recurrence.until_unfolding`'s v2 repair from 0.000 to 1.000 is 3/3
  pattern absorption — the second fails-open half is bigger than the
  provability corpus.
  **Correction (2026-08-09, review).** This entry also recorded that "the
  pattern channel is where cross-discipline-looking credit concentrates
  graph-wide (62 of 75 absorbed patterns are owned outside the absorbing
  statement's discipline)". The 62/75 counts most-independent owners; with ALL
  owners external it is 36/75, the other 26 having a same-corpus (25) or
  prior-corpus (1) co-owner. The *inference* is withdrawn: the exact channel
  scores 352/440 (80.0%) and 162/440 (36.8%) on the same two readings, so
  absorption does not concentrate such credit — it is a wash by rate and the
  exact channel is 5.7:1 larger by count. Absorption is where that credit is
  *quarantined*, which was the design intent. See docs/DISCOVERIES.md for the
  retraction as filed.
- **`specialize.py` produces zero edges and zero noise on call-only corpora —
  fifth confirmation, from the other side.** 468 specialization edges over the
  merged graph, none touching either of the 17 new nodes in either direction.
  Same root cause as the recorded "specialize.py is arithmetic-only"
  (`COMMUTATIVE = {+, *}`, `IDENTITY = {+: 0, *: 1}`) that already gave
  `data/logic` and `data/set_theory` zero edges. The new information is that
  these corpora also contribute **zero degenerate noise**, because the noise
  mechanism (a variable slot absorbing arguments of a commutative arithmetic
  op) has nothing to bite on in a template made only of call heads. Any
  evaluation of the proposed category-compatibility constraint should note that
  the corpora it would clean up are exactly the corpora that get edges at all.
  **PARTIALLY RESOLVED** (branch `tooling/head-algebra`): with per-head
  identities, `data/logic`, `data/set_theory` and `data/morphology` now get
  edges — seven of them, every one looseness 0 and every one informative,
  which is a hit rate no arithmetic corpus in this graph comes close to. The
  "zero noise" observation survives intact and is now load-bearing evidence:
  the seven call-corpus edges added **zero** degenerate ones, because a call
  head is arity-fixed and cannot be absorbed into. `data/temporal_logic` and
  `data/narrative` are still at zero in both directions — they carry no head
  with a declared identity (`UNTIL`, `ALWAYS`, `EVENTUALLY`, `NEXT`), so the
  new mechanism has nothing to bite on there either.
- **Monotone endo-functions need a second monotonicity template, and the
  backlog's own request could not be honoured.** The
  `geotop.measure.area_monotonicity` entry above asks that a future
  monotone-functional node be written with *that* template
  (`IMPLIES(LEQ(REGA, REGB), CARD(REGA) <= CARD(REGB))`).
  `temporal.monotonicity.eventually_monotonicity` is the first such node and
  cannot: `CARD` is a valuation into the numbers, while `EVENTUALLY` maps the
  lattice of temporal properties into itself, so its conclusion must be a
  second `LEQ` and the honest template is
  `IMPLIES(LEQ(PROPA, PROPB), LEQ(EVENTUALLY(PROPA), EVENTUALLY(PROPB)))`.
  The two skeletons share their premise and differ in the kind of their
  conclusion, so no group forms. The request presumed every monotone functional
  is a valuation; monotone *endo*-functions are a second kind. The
  generalization the graph wants — `IMPLIES(LEQ(x, y), LEQ(F(x), F(y)))` with
  the numeric case as its specialization along a valuation — is also out of
  reach for `specialize.py`, since `<=` and `LEQ` are different relation kinds.
  Wanted: either a `LEQ` spelling of the numeric case, or a match level that
  treats a declared order relation and `<=` as one head.
- **The two-premise detachment shell is now the graph's most-populated
  non-family.** `IMPLIES⟨MEET⟨_, _⟩, _⟩` carries five nodes —
  `logic.inference.modus_ponens`, `settheory.order.subset_transitivity`,
  `geotop.predicates.containment_transitivity`,
  `temporal.order.precedence_transitivity` and
  `narrative.causality.precedence_causation_bridge` — and forms exactly one
  group (the three transitivity nodes). The three that group share a *slot
  pattern* ((0,1),(1,2) ⊢ (0,2)); the causation bridge conjoins two relations
  over the SAME pair and concludes a third over that pair. The distinction is
  real and the graph has no vocabulary for it: "same shell, different slot
  pattern" is currently indistinguishable from "unrelated" in every report.
  Companion to the recorded "slot recurrence, not slot shape" wanted level —
  that one asks for a query over slot recurrence within a statement, this one
  asks for the shell itself to be reportable as a weaker grouping.
- **Idempotence and involution cannot be related, and the reason is a fixed
  point rather than a head.** `temporal.modality.always_idempotence`
  (`ALWAYS⟨?0:V⟩ = ALWAYS⟨ALWAYS⟨?0:V⟩⟩`) is the fifth member of the recorded
  "operation that returns its argument" family and the first idempotent
  *modality*. Worth separating from the head-literalism entries because the
  blocker against `logic.boolean_laws.double_negation`
  (`?0:V = NEG⟨NEG⟨?0:V⟩⟩`) is not the head: NEG applied twice equals the bare
  slot, ALWAYS applied twice equals `ALWAYS⟨?0⟩`, so the two sides differ in
  depth. An idempotent has a fixed point an involution does not, and that is a
  property of the skeleton rather than a shape of it — the exact case the
  wanted structural-query facility has to cover.

- **An identity that collapses a call is a rewrite, and rewrites need their
  own non-triviality bar.** Found while shipping `HEAD_ALGEBRA`. The
  arithmetic identity rule is safe because a commutative op's arity is
  variable: binding `SHIFT -> 0` removes an *argument*. A call's arity is
  fixed, so `HEAD(a, e) = a` removes a *node*, and the pattern that survives is
  smaller than the one `op_count(gtree) >= 2` was checked against. Measured
  cost of not noticing: `specialize.py` went from 573 edges to **1080**, and
  500 of the 507 extra came from three templates —
  `geotop.predicates.de9im_disjoint` (`MEET(REGA, REGB) = EMPTYSET`
  collapsing to `REGA = EMPTYSET`), `morphology.wordformation.affixation` and
  `iterated_affixation` — each then matching every two-slot equation in the
  graph. Fixed by counting collapses and re-checking
  `op_count(gtree) - collapses >= 2`, which drops the count to 580. Recorded
  because every future algebraic rewrite (associative flattening, the wanted
  sum-collapse-under-constant-summand, series truncation) has the same shape:
  it shrinks the pattern, and the guard that made patterns non-trivial has to
  be evaluated on the pattern *as used*.
  **SHIPPED, and strengthened** (branch `tooling/cheapest-derivation`): the
  bar is no longer a post-filter over one derivation but a *constraint inside
  the search* (`Search.acceptable`, consulted per candidate derivation).
  A derivation that shrinks the pattern below the bar can no longer end the
  search; the matcher keeps looking and returns the cheapest derivation that
  passes. Re-measured on the 199-node corpus: with the guard removed the
  count goes 622 -> **1130** edges (+508, the same explosion the head-algebra
  work measured as 573 -> 1080), so the guard is still entirely load-bearing.
  The generalization the entry predicted also held: applying the *whole*
  acceptability test (guard + non-triviality) as a post-filter over the
  global minimum instead of as a search constraint yields only 463 edges —
  159 pairs whose cheapest derivation is degenerate but which have a
  perfectly good informative one. Any future rewrite inherits the constraint
  for free by being priced in the cost model.
- **First-success-wins search lets a weaker reading pre-empt a stronger one.**
  Second finding from the same work, and independent of it.
  `find_specializations` calls `match` once and keeps whatever it returns, so
  when a new mechanism is added, an edge that previously matched cleanly can
  come back with a degenerate derivation instead. Observed exactly once:
  `geotop.predicates.de9im_disjoint >= temporal.modality.next_distributes_over_meet`
  was matched by plain binding, and the identity rule found
  `REGB -> TRUTH` first, which then failed the collapse guard and deleted the
  edge. Worked around by running `match` twice per candidate pair, with head
  identities disabled on the first pass — the general principle being that a
  reading needing no algebra is always the better reading. That principle is
  not enforced *within* a pass (a collapse deep in a subtree can still
  pre-empt an argument swap higher up), and it will not scale to a third and
  fourth mechanism. Wanted: `match` returns the *cheapest* derivation rather
  than the first, e.g. by scoring mechanisms and searching best-first, which
  would also give `looseness` a companion "how much algebra did this need"
  axis.
  **SHIPPED** (branch `tooling/cheapest-derivation`). Every mechanism now
  carries a price — rename 0, slot->structure `1 + op_count(bound)`,
  absorption 1 per extra argument swallowed, arithmetic identity 2 per use,
  head-identity collapse 4 per use — and `Search` returns the minimum-cost
  *acceptable* derivation over the whole space (exhaustive DFS with
  branch-and-bound; cost is monotone along a derivation, so pruning at the
  incumbent is exact). The two-pass workaround is deleted: the guarded
  reproducer `de9im_disjoint >= next_distributes_over_meet` comes back via
  plain binding at cost 7 (7 structure + 0 algebra, 0 collapses), and it does
  so at every depth rather than only at the root, because acceptability is a
  search constraint now (see the entry above). Measured against the v2 count
  of 589 edges on the same 199 nodes: **622 edges, 33 gained, 0 lost.** All
  33 gains have one general node, `physics.circuits.ohms_law`
  (`POTENTIAL = FLOW * RESISTANCE`), and all 33 are the entry's own failure
  mode in its harshest form — v2's first success bound `FLOW -> QUANTITY,
  RESISTANCE -> inv(INTERVAL)`, a reading the informativeness filter scores
  as a bare renaming (see the `used_compound` entry below), so the pair was
  dropped entirely rather than re-derived as `FLOW -> QUANTITY*inv(INTERVAL),
  RESISTANCE -> 1` (cost 6), which is the same shape as the
  `beer_lambert_law`/`ABSORPTIVITY -> 1` edges the graph already carried.
  Of the 589 retained edges, 106 change `via` and 128 change bindings, always
  towards a cheaper reading: `newton_second_law >= triangle_area_formula` was
  `INERTIA -> 1` plus a three-factor absorption and is now `INERTIA ->
  CONSTANT` plus a two-factor one (the search stops paying for the identity
  rule when an honest binding is available). Cost range 1-12, median 6.
  Runtime *fell*: `find_specializations` 0.157s -> **0.111s** (best of 3,
  209383 search steps), 0.49s wall for the whole tool, because dropping the
  second pass buys more than exhaustive enumeration costs and the incumbent
  prunes the rest. No beam, no memo, no bound needed at this corpus size.
- **The commutative path never sets `used_compound`, so a slot swallowing a
  subtree inside `+`/`*` reads as a bare renaming.** Found while shipping the
  cost search, which is why the 33 gained edges above are all one node.
  `gen_commutative` assigns its bindings directly instead of recursing
  through the slot case of `gen_direct`, and only `gen_direct` sets the flag
  (v2 had the identical split between `match_commutative` and `match_direct`,
  so this is inherited, not introduced). Consequence: a match whose only
  novelty is `RESISTANCE -> inv(INTERVAL)` scores as "pure slot-to-slot
  renaming" and is filtered out, even though the module docstring explicitly
  lists "a slot binding structure (a compound subtree or a literal)" as
  informative. `looseness` and `structure_cost` both count that binding, so
  the flag is the only thing that disagrees. Measured cost of the bug:
  setting `compound=1` on non-slot commutative bindings takes the graph from
  **622 to 791 edges** (+169 beyond the 33 already recovered) and drops the
  median cost from 6 to 4, because the 33 ohms-law edges and many others then
  derive far more cheaply (the ohms-law pairs at cost 2 via plain compound
  binding rather than cost 6 via absorption + identity). Deliberately NOT
  fixed in the cheapest-derivation commit: it is a change to what "informative"
  means, a +169-edge adjudication in its own right, and mixing it in would
  have made the cost-search regression unreadable. Wanted: decide whether the
  non-triviality bar means "the pattern did work" (fix it) or "the pattern
  bound a subtree *where a leaf was written*" (document it), then land the
  edge-count change on its own with the usual per-family adjudication.
- **The same first-success bug was living in `decompose.py`, one import
  away, and cost the groundedness ladder two rungs.** `decompose.py` uses
  `specialize.match` as a predicate and then refuses the match if
  `used_absorption or used_identity` — i.e. it wants the no-algebra reading
  specifically. Under first-success it never got to ask: matching
  `*(?0:P, ?1:V)` against `*(?0:P, LOG(?1:V))`, the parameter slot's identity
  branch fires first (`?0 -> 1`, the rest absorbed), `match` returns True
  with the algebra flags set, and `pattern_cover` rejects a pattern that
  covers the subterm perfectly well by plain binding. The consequence was not
  "no grounding" but *worse* grounding: the coarser `*(?0:V, ?1:V)` was cited
  instead, which is the P-vs-V category mismatch `pattern_cover`'s own
  docstring says it refuses weaker matches to avoid. Routing the compatibility
  `match` through the cost search fixes it for free. Measured on the 199-node
  corpus: **10 of 198 nodes change constituents, corpus mean groundedness
  0.7634 -> 0.7660**, `calculus.differentiation.product_rule` 0.714 -> 0.857
  and `linearity_of_derivative` 0.778 -> 0.889, each gaining one
  `grounded_via_pattern` constituent. Not adjudicated here and the ledgers are
  deliberately not refreshed on this branch (see the entry below); wanted: a
  groundedness-owner pass over those 10 nodes' new citations, then a ledger
  refresh. Generalisation worth keeping: any consumer that asks a matcher
  "did you need mechanism X" is silently asking "was X on the first path you
  happened to take", which is not a question about the statements at all.
- **PRUNED at v0.16.0 — `reports/` regeneration is checked.** The entry
  that stood here (committed reports drifting from their writers,
  found via a 46-line compression diff at an old tip) shipped its fix as
  `scripts/check_report_regeneration.py`, run in the release refresh:
  three ledgers clean, `decompositions.json` a declared divergence with
  its citation. Its prune condition (the v0.16 headline ships or folds)
  was met by the adjudication. History: RELEASE-v0.16.0, ANALYSIS
  "voided by its own gate".
- **PARTIAL — `ingest_wold.py reach` is now in the release skill;
  a full generated-artifact census is not.** v0.11's programming
  second wave added six tokens and `experiments/wold_reach.json`
  stayed at 840 until the tag-tip suite (TRIAGE-v0.11 §1.7). The
  skill's step 1 now runs `ingest_wold.py reach` and treats a
  missing WordNet archive as **cannot verify**, not a skip. The
  broader “enumerate every committed generated artifact, re-run
  into a temp path, diff” fix is still the entry above
  (`reports/` having no regeneration check), which at v0.15 was
  absorbed into DESIGN-retraction-closure §4 / ROADMAP-v0.16
  item 1. Do not close that one just because WOLD is named.

  **v0.16.0 status note (2026-08-21):** the pointer "the entry above" now
  points at a **PRUNED** marker, which reads as a dead reference. Repointing:
  the broader census fix **shipped** as `scripts/check_report_regeneration.py`
  — see the "PRUNED at v0.16.0 — `reports/` regeneration is checked" marker
  immediately above and [RELEASE-v0.16.0.md](RELEASE-v0.16.0.md). This entry
  stays PARTIAL only for the `ingest_wold.py reach` half; the census half it
  deferred to is discharged.
- **PARTIAL — the wall-clock is written down; the two-tier gate is
  not built.** Full discover on the v0.11.0 tip: **1,123 tests,
  23,744s / 6h35m**. The “30+ minutes” figure is struck from the
  v0.12 handoff and the release skill. Named outlier:
  `test_write_stage.AcceptedCandidateTests.test_matcher_delta_is_measured_and_recorded`
  (6+ minutes, ~5.4 GB). Still wanted: a per-test timing pass, a
  faster fixture for graph-scale tests, and a *checked* two-tier
  gate (fast set per slice, full discover per tag) rather than
  prose in the skill.

  **v0.16.0 status note (2026-08-21):** two of the three "still wanted"
  items are discharged. The **per-test timing pass exists and has run
  twice** — `reports/test_gate_v015/` and `reports/test_gate_v016/`, the
  latter reading 1,427 tests / 20,837.8 s. The **faster fixture** landed
  (shared split fixture, `fa0a174`). The named outlier
  `test_matcher_delta_is_measured_and_recorded` no longer costs 6+ minutes:
  it reads **202.99 s**, mid-pack rather than worst. The still-open
  remainder of this entry is only the **CHECKED two-tier gate** — a fast set
  per slice and a full discover per tag, enforced rather than described in
  prose. The 1,123-test / 23,744 s v0.11 reading above stands as an
  as-of-v0.11 fact.
- **The cost weights are the first numbers in the matcher with no corpus
  citation.** `HEAD_ALGEBRA` was built on the house rule that every algebraic
  claim names the node that justifies it; `COST_IDENTITY = 2` and
  `COST_HEAD_COLLAPSE = 4` name nothing. They are defensible ordinally — a
  rewrite that erases a node should cost more than one that fills a slot in,
  which should cost more than a rename — and the ordinal facts are what the
  search actually uses, but the specific magnitudes decide ties between
  mechanisms and nothing in `data/` adjudicates them. Probed the whole
  algebra half of the model by sweeping each weight independently and
  diffing membership *and* per-edge derivations against the shipped report:
  `COST_HEAD_COLLAPSE` in {0, 1, 2, 3, 4, 5, 6, 7, 8, 20, 100},
  `COST_IDENTITY` in {0, 1, 2, 3, 5, 10}, `COST_ABSORB_ARG` in {0, 1, 2, 3}
  — **622 edges and identical membership in every one of the 21 runs**, with
  exactly one edge changing its *derivation* (at `COST_IDENTITY >= 3` and
  again at `COST_ABSORB_ARG = 0`). So on the 199-node corpus the graph is
  decided by the acceptability constraint and the structure cost; the algebra
  weights are currently unfalsifiable by the data, which is the real reason
  to be uneasy about them rather than a reason to relax. The exposure grows
  with every mechanism added, since each new one has to be priced against
  numbers nothing tests. Wanted: either derive the weights from something
  (edit distance on the skeleton? the epistemic ladder's rung ordering?) or
  record them as a declared, provenanced table the way head algebra is, so a
  future mechanism has to argue its price rather than pick one — and add a
  corpus pair that *does* discriminate, so the sweep above stops being flat.
- **The typed sort key orders P before V, which silently re-splits heads that
  a future alias would want to merge.** `typed_resort` sorts by a key in which
  `?P` precedes `?V`, so declaring MEET commutative moved
  `logic.boolean_laws.identity_laws` from `?0:V = MEET⟨?0:V, ?1:P⟩` to
  `?0:V = MEET⟨?1:P, ?0:V⟩`, while
  `morphology.wordformation.zero_morpheme_identity` keeps
  `?0:V = CONCAT⟨?0:V, ?1:P⟩` because CONCAT is (correctly) not commutative.
  The two identity laws are the pair `docs/BACKLOG.md` names as the
  head-literalism reproducer, and they are now *further* apart than before:
  same structure, different head, and now different argument order too. Harmless
  today (`CONCAT` and `MEET` share no alias class and must not), but it means
  any future "opaque binary composition" alias has to normalize argument order
  after aliasing, not before. Cheap fix when it lands: run the commutative sort
  inside `alias_heads`' output rather than only in `canonicalize`.
  **SHIPPED** (branch `tooling/matcher-consistency`), though the diagnosis was
  half right and the shipped fix is a different shape than the one proposed.
  The proposed fix — "run the commutative sort inside `alias_heads`' output" —
  was already in place: `load_nodes` computed `skeleton(canonicalize(
  alias_heads(tree)), classes)`, so both the shape sort and the typed re-sort
  already ran *after* aliasing. What was missing is that they read
  commutativity in the WRONG VOCABULARY: `COMMUTATIVE_CALL_HEADS` holds
  pre-alias spellings (`MEET`, `JOIN`, `MINOF`, `TOUCHES`), so the moment a
  commutative head joined an alias class its post-alias name would match
  nothing and the sort would silently stop. Now `canonicalize`, `typed_resort`
  and `skeleton` take the commutative-call set as a parameter, and the aliased
  level passes `ALIASED_COMMUTATIVE_CALL_HEADS` — the unaliased commutative
  heads plus every alias class *all* of whose members are declared
  commutative, which is what keeps `ordered_compose` non-commutative on
  CONCAT's evidence rather than inheriting it from a sibling.
  Measured, on the 199-node corpus: the set equals `COMMUTATIVE_CALL_HEADS`
  today (no declared-commutative head is aliased), so **zero aliased skeletons
  change and zero groups change membership** — 30 aliased groups before and
  after, every skeleton string byte-identical. The guard was verified by
  counterfactual instead: temporarily aliasing `MEET`/`JOIN` into an
  `opaque_compose` class, `MEET(PROP1, TRUTH) = PROP1` and
  `MEET(TRUTH, PROP1) = PROP1` split into `?0:V = opaque_compose⟨?0:V, ?1:P⟩`
  and `?0:V = opaque_compose⟨?1:P, ?0:V⟩` under the old lookup and share
  `?0:V = opaque_compose⟨?1:P, ?0:V⟩` under the new one.
  Adjudicated on this entry's own pair: **the MEET and CONCAT identity laws do
  NOT newly reach the aliased level, and no other pair does either.** They read
  `?0:V = MEET⟨?1:P, ?0:V⟩` and `?0:V = ordered_compose⟨?0:V, ?1:P⟩`. Sorting
  after aliasing cannot close that, and the entry's framing ("now *further*
  apart") over-blames the sort: the argument-order divergence is a
  *consequence* of a correct declaration, since CONCAT is non-commutative and
  its arguments must not be reordered at any level. The two are separated by a
  head, not by an order, and the only thing that would merge them is an alias
  class asserting that MEET and CONCAT are one operation family — which is
  false. What this entry really wanted, and what is now impossible to get wrong
  silently, is that the *hazard* be structural rather than remembered.
- **Commutative-head robustness reaches `typed` but not `shape`.** Probed on
  the pair the declaration was meant to make safe: `MEET(PROP1, TRUTH) = PROP1`
  and `MEET(TRUTH, PROP1) = PROP1` now share a typed skeleton
  (`?0:V = MEET⟨?1:P, ?0:V⟩`) — which is the whole point, and what makes the
  logic/set-theory twin robust rather than lucky — but their *shape* skeletons
  are `?0 = MEET⟨?0, ?1⟩` and `?0 = MEET⟨?1, ?0⟩`. Cause: `shape_key` erases
  slot identity, so two slot arguments compare equal, the sort is stable, and
  the placeholder indices are then assigned in the surviving order. The gap
  only opens when a slot RECURS across the relation, which is exactly the
  family the wanted "slot recurrence, not slot shape" match level is about.
  `shape` is documented as the loosest level and is here strictly stricter
  than `typed`, which inverts the ladder. Fix candidate: order commutative
  arguments by first-occurrence index of their slots over the whole statement
  (a fixpoint, since the indices depend on the order), or accept it and note
  in the report that `shape` is not a relaxation of `typed`.
  **SHIPPED** (branch `tooling/matcher-consistency`) as `shape_resort`, the
  shape-level counterpart of `typed_resort`. The entry's fix candidate names
  the difficulty correctly and then trips over it: there IS no order-independent
  key on a single argument, because the fact that distinguishes the two slots —
  that one of them RECURS on the other side of the relation — is a property of
  the whole statement, which is why first-occurrence ordering comes out a
  fixpoint. So the fix is a canonical form rather than a key: among the
  argument orders declared commutativity permits, take the one whose rendering
  is lexicographically smallest. Only the permutations WITHIN runs of equal
  `shape_key` are candidates (`canonicalize` has already fixed the order of
  everything distinguishable, from the argument multiset alone), so the
  candidate SET depends only on structure plus slot-recurrence pattern, `min`
  over it is order-independent, and — since an equal typed skeleton already
  implies an equal structure-plus-recurrence class — equal typed now FORCES
  equal shape. The ladder invariant holds by construction, and because the old
  skeleton is always one of the candidates, shape groups can only coarsen;
  none can split.
  Measured on the 199-node corpus:
  - Group counts unchanged at every level — shape 28, typed 29, family 28,
    aliased 30 before and after; **zero membership changes anywhere**, and
    typed/family/aliased skeleton strings byte-identical (the new sort runs
    only on the `slot_class is None` path). `decompose.py` and `specialize.py`
    reproduce their reports byte-for-byte.
  - Four shape skeleton STRINGS move to their canonical minimum:
    `calculus.differentiation.product_rule`, `diffgeo.surfaces.first_fundamental_form`,
    `ml.policy.ppo_clipped_surrogate`, and — the one worth reading —
    `geotop.predicates.adjacency_symmetry`, which goes from
    `IMPLIES⟨TOUCHES⟨?0, ?1⟩, TOUCHES⟨?1, ?0⟩⟩` to
    `IMPLIES⟨TOUCHES⟨?0, ?1⟩, TOUCHES⟨?0, ?1⟩⟩`. The node that exists only to
    say TOUCHES is commutative now renders, at shape level, as the tautology it
    became once the declaration replaced it.
  - `ladder_violations` is **0 after — and was 0 before**. Reported honestly:
    the inversion was never realized in `data/`, because every commutative-head
    statement in the corpus is authored in one order. It was a robustness hole,
    not a live defect, and the probe is what shows it: pre-fix,
    `MEET(TRUTH, PROP1) = PROP1` and `MEET(PROP1, TRUTH) = PROP1` had shape
    skeletons `?0 = MEET⟨?1, ?0⟩` and `?0 = MEET⟨?0, ?1⟩` while sharing one
    typed skeleton; post-fix both are `?0 = MEET⟨?0, ?1⟩`. Same for JOIN. The
    check now runs every invocation and prints to stdout, so a corpus that
    spells one the other way cannot reintroduce it unnoticed.
  - Cost: the whole corpus needs at most **24** candidate orderings for one
    statement (`economics.macroeconomics.gdp_expenditure_identity` and
    `geomodel.quaternions.unit_quaternion_constraint`, both four-term sums),
    489 summed over all 199 nodes, against a `SHAPE_ARRANGEMENT_BUDGET` of
    4096. Restricting to tie-blocks is what makes it cheap: unrestricted
    permutation would need 1152 for `first_fundamental_form` alone.
- **The typed sort has the same tie the shape sort just lost.** Found by the
  probe that verified `shape_resort`. `typed_key` distinguishes `?P` from `?V`
  but not one `?V` from another, so two variable-like arguments of a
  commutative head still fall through to the stable sort and keep their
  authored order. `MEET(SETA, JOIN(SETA, SETB)) = SETA` and the absorption law
  spelled `MEET(JOIN(SETB, SETA), SETA) = SETA` now share a shape skeleton and
  still split at typed (`MEET⟨?0:V, JOIN⟨?0:V, ?1:V⟩⟩` vs
  `MEET⟨?0:V, JOIN⟨?1:V, ?0:V⟩⟩`). Not urgent and not a ladder violation — it
  is the ladder pointing the right way, shape looser than typed — but it is
  the same defect one level up, and the same remedy applies: give
  `typed_resort` the `shape_resort` treatment, minimizing the rendering over
  tie-blocks of equal `typed_key` rather than over tie-blocks of equal
  `shape_key`. Deliberately not shipped with the shape fix, because it would
  change typed skeletons and therefore risk twin membership, which that change
  was required not to do.
- **An identity element has one abstract identity and several corpus
  spellings, and the report prints whichever is listed first.**
  `HEAD_ALGEBRA["JOIN"]["identity"]` is `("FALSITY", "EMPTYSET",
  "INCONSISTENCY")` because the same lattice bottom is spelled three ways in
  `data/logic`, `data/set_theory` and `data/narrative`. `specialize.py` tries
  the spellings in table order, so
  `settheory.boolean_laws.absorption >= settheory.boolean_laws.idempotence`
  reports `SETB -> FALSITY` — correct, but in the wrong corpus's vocabulary.
  Cosmetic today (four edges), and it will not stay cosmetic once more corpora
  declare identities. Fix: prefer the spelling that occurs in the *specific*
  node's `slot_schema`, falling back to table order. The deeper version of the
  same request is the recorded "same invariant, slot in one corpus and call
  head in another" lint — both want a notion of "these identifiers name one
  object" that the graph does not yet have.
  **SHIPPED** (branch `tooling/cheapest-derivation`), with one correction to
  the proposed fix: the specific node's own `slot_schema` is not enough.
  `settheory.boolean_laws.idempotence` is `MEET(SETA, SETA) = SETA` and
  declares no constant at all, so the node-level rule would have left the
  cited edge printing `FALSITY`. `spelling_ranker` therefore ranks spellings
  by the specific statement's `slot_schema` first, then by the union of every
  `slot_id` its *discipline* declares anywhere, then by table order; ties in
  derivation cost keep the first spelling tried, so the ranking decides the
  printed name. The corpus vocabularies are cleanly disjoint —
  `data/logic` {TRUTH, FALSITY}, `data/set_theory` and
  `data/geospatial_topology` {UNIVERSE, EMPTYSET}, `data/narrative`
  {INCONSISTENCY}, `data/morphology` {EMPTY} — so the discipline rule is
  decisive wherever it applies. Measured: the two edges with a set-theory
  *specific* flip `FALSITY` -> `EMPTYSET`
  (`logic.boolean_laws.absorption >= settheory.boolean_laws.idempotence` and
  `settheory.boolean_laws.absorption >= settheory.boolean_laws.idempotence`),
  the two with a logic specific correctly keep `FALSITY`, and the five CONCAT
  collapses report `EMPTY` as `sole`. Every edge that binds an ambiguous
  identity now carries an `identity_spellings` block naming the head and the
  basis (`specific-node` / `specific-discipline` / `table-order` / `sole`),
  and a table-order fallback additionally prints an
  `identity_spelling_note`. **Zero edges currently fall back**, which is the
  number to watch as corpora are added.

## Schema

- **`symbolToken.syntactic_category` lacks `functional`/`operator`** (unlike
  `signatureSlot`), so operator symbols (`D`, `f`, `g`) must go in
  `functionals` while `symbols` still demands `minItems: 1` — FTC part 1
  needed a scalar symbol it didn't naturally have. Either add the enum
  members or relax `minItems`.
- **`provenance` entries reject `scope_note`, `equivalent_forms` entries accept
  it.** Two `additionalProperties: false` objects in the same node disagree
  about the same key name, and there is no reason for the asymmetry: a citation
  needs to say *why* it is cited at least as often as an alternative notation
  needs to say when it applies. Found while authoring
  `probstat.probability.two_component_mixture`, where Pearson 1894 wants "the
  founding paper, a two-component normal mixture fitted to Weldon's crab
  measurements" and Huber 1964 wants "the same template with the weight read as
  a contamination fraction". Validation failed on both; the notes now sit
  inside `bibliographic_entry` in square brackets, which is unparseable by
  anything that consumes the bibliography. Fix: add `scope_note` (or `note`) to
  the provenance entry schema.

- **`statement_id` pattern forbids underscores in the first segment.**
  `^[a-z0-9]+(\.[a-z0-9_]+)+$` allows `_` in every segment except the
  discipline prefix, so `set_theory.boolean_laws.de_morgan_laws` fails
  validation and the corpus had to use `settheory.` while the directory and
  the `discipline` field stay `set_theory`. The prefix and the directory name
  now disagree, which is a trap for anything that derives one from the other.
  Fix: allow `[a-z0-9_]+` in the first segment too (there is no reason for the
  asymmetry), or document the prefix-vs-directory mapping in the schema.
- **Slot ids may not start with a big-op prefix either.** The hazard recorded
  above for templates extends to `slot_schema`: a slot literally named
  `SUM_TERM` or `MAX_RATE` would be eaten by the prefix big-operator rule
  before it was ever looked up, so a whole class of natural slot names is
  quietly unusable. The information-theory corpus works around it by naming
  indexed slots `WEIGHT_i`, `PROBABILITY_i`, `CODELENGTH_i` (suffix, not
  prefix). Worth a lint rather than folklore.
- **Cross-corpus entailment is blocked by reciprocity.** `entails` /
  `special_case_of` / `generalizes` require the reciprocal edge in the other
  corpus's file, so genuine cross-discipline entailments (physics average
  speed IS a special case of calculus average rate of change) go unrecorded;
  only `composed_with` (unchecked) is usable one-sided. Options: a repair
  tool that writes the reciprocal edge into the target corpus, or relax
  reciprocity to a warning for cross-corpus edges.
- **Even one-sided `composed_with` cannot forward-reference a corpus authored
  on a parallel branch.** `validate_nodes.py` requires every link target to
  resolve in the merged graph, and the merged graph is whatever `data/*/` holds
  on the current branch. `diffgeo.surfaces.gauss_bonnet_theorem` should point
  at `algtop.invariants.euler_characteristic_surface`, which a parallel branch
  is authoring; writing the edge now makes validation fail here and pass only
  after a merge, so the reference sits in prose and the edge is a documented
  one-line addition in `scripts/seed_diffgeo.py`. Two agents seeding
  interlocking corpora in parallel therefore cannot link to each other at all.
  Fix: a `pending`/`external` link list the validator warns on instead of
  failing, or a manifest of reserved ids that branches may reference before the
  corpus lands.
- **Same invariant, slot in one corpus and call head in another.** The Euler
  characteristic is a bare slot in `diffgeo.surfaces.gauss_bonnet_theorem`
  (where it is the number on the right-hand side) and a call `EULERCHAR(.)`
  throughout `data/differential_topology` (where it is an invariant applied to
  a space). Both readings are natural, and the matcher cannot relate a slot to
  a call head, so the two corpora cannot see that they discuss one integer.
  The same trap is open for every named quantity that is sometimes a value and
  sometimes a functional (entropy, degree, cardinality, expectation). Wanted: a
  lint that flags an identifier used as a slot id in one node and a call head
  in another, plus a documented convention for which reading wins.
  **LINT SHIPPED** (branch `tooling/matcher-consistency`) as
  `slot_vs_call_head_collisions` in `scripts/match_signatures.py`, reported in
  JSON and in a stdout block. A lint only — which reading wins is an authoring
  decision about the corpora and stays one; nothing is rewritten. Comparison is
  case-insensitive on the stem, with the bracket-call marker `[]` stripped
  (`E[X|Y]` parses to the head `E[]`) and nothing else: index suffixes like
  `WEIGHT_i` are part of the identifier an author chose, and folding them would
  invent collisions rather than find them. A name is only reported when some
  statement DISAGREES with another — one committing to it as an opaque value
  while another applies it as an operation. Mere co-occurrence is not a
  collision, which is why `SELFMAP` and `AGGREGATE_n` are excluded (every
  statement carrying them uses them both ways) while `F` is included
  (`calculus.integration.ftc_differentiation_part` uses it as a slot only).
  **7 names, 25 statements.** The three pairs this entry was promoted for all
  appear:
  - `eulerchar` — slot in `algtop.homology.betti_alternating_sum`,
    `algtop.invariants.euler_characteristic_complex`,
    `algtop.invariants.euler_characteristic_surface`,
    `diffgeo.surfaces.gauss_bonnet_theorem`; call head in
    `difftop.invariants.euler_characteristic_diffeomorphism_invariance`,
    `difftop.vectorfields.hairy_ball_theorem`,
    `difftop.vectorfields.poincare_hopf_index_theorem`. Four algebraic-topology
    nodes on the slot side, not the one this entry named — the gap is wider
    than Gauss-Bonnet vs Poincaré-Hopf.
  - `length` — slot in `diffgeo.curves.arc_length_functional` and
    `graphtheory.walks.adjacency_power_walk_count`; call head in
    `morphology.quantity.morpheme_count_additivity`.
  - `degree` — slot in `geomodel.bezier.endpoint_tangent`; call head in
    `difftop.degree.degree_multiplicativity` and
    `difftop.degree.degree_regular_value_count`.

  Four the entry did not predict, all real and all of its stated kind ("a named
  quantity that is sometimes a value and sometimes a functional"): `f` (the
  FTC/Stokes cluster, where `calculus.integration.ftc_differentiation_part`
  alone treats the function as a value), `outer` (slot in
  `calculus.differentiation.chain_rule` and
  `difftop.degree.degree_multiplicativity`, head in
  `ml.recurrence.mlstm_matrix_memory_update`), `scale` (slot in three
  physics/statistics nodes including `probstat.transform.z_standardization`,
  head in `probstat.limit.normal_approximation_sample_mean` — a disagreement
  *within* `data/statistics`), and `sequence` (slot in
  `probstat.limit.law_of_large_numbers`, head in
  `narrative.structure.story_sequence`). The convention half of this entry is
  still open: the lint names where a decision is outstanding, it does not make
  one.
- **A quarter of the corpus loses its logical form.** The grammar has no
  quantifier and no usable implication, so conditional and existential
  statements reduce to their conclusions: of the sixteen nodes in
  `data/differential_geometry` and `data/differential_topology`, four carry
  their real content in `regularity_conditions` instead of the template —
  `difftop.invariants.euler_characteristic_diffeomorphism_invariance` (loses
  "whenever M and N are diffeomorphic"),
  `difftop.vectorfields.hairy_ball_theorem` (loses "if a nowhere-vanishing
  field exists"), `difftop.degree.brouwer_fixed_point` (loses "there exists x"),
  and `difftop.morse.weak_morse_inequality` (loses "for every Morse function
  and every k"). Consequence for the ledger: twin density is not comparable
  across `statement_class`, because definitions keep their whole content in the
  template and theorems routinely do not. Same family as the missing binder
  recorded under Parser / matcher.

- **Cross-corpus reciprocity, now measured in edits per edge.** The entry
  above proposes a repair tool; `data/machine_learning` priced it.
  `ml.objective.token_cross_entropy_loss` and
  `infotheory.divergence.cross_entropy` are the same functional, so the
  reciprocal `equivalent_to` was worth writing — which meant editing
  `scripts/seed_infotheory.py`, regenerating `data/information_theory`, and
  carrying an unrelated corpus's diff on this branch. That is affordable
  once. It is not affordable for
  `ml.preference.grpo_group_relative_advantage`, whose relation to
  `probstat.transform.z_standardization` is the strongest in the corpus (an
  exact typed twin, and GRPO's advantage really is that transform applied to
  rewards) but which had to degrade to a one-sided `composed_with`: the
  reciprocal `generalizes` would have to go into `data/statistics/nodes.json`,
  and that corpus has **no seed script** — it is hand-maintained, so the edit
  could not be made the way every other corpus is edited. So the reciprocity
  requirement's real cost is not "write two edges", it is "be able to
  regenerate the other corpus", and one corpus in the repo fails that test.
  Either the repair tool lands, or reciprocity relaxes to a warning for
  cross-corpus edges, or `data/statistics` gets a `scripts/seed_statistics.py`
  like everything else.
- **Side conditions that carry the whole empirical claim have nowhere to go.**
  The differential-topology entry above records lost quantifiers. Machine
  learning loses a different class and loses it in the most-cited node:
  `ml.adaptation.lora_low_rank_update` is
  `?0:V = +(?1:P, *(?2:P, ?3:V, ?4:V))`, which says the update factors
  through a product — it does not and cannot say that the inner dimension is
  small, which is the entire hypothesis of the paper. Same shape of loss:
  parameter tying across time steps in the recurrence nodes (the reason RNNs
  generalize across sequence length), and the zero-initialization of one LoRA
  factor (the reason adaptation starts at the pretrained model). All three
  sit in `invariants` and `regularity_conditions` as prose. Consequence for
  the ledger, beyond the one already noted for `statement_class`: three
  papers (LoRA, PiSSA, LoftQ) share one skeleton and differ only in how the
  same slots are initialized, so skeleton count understates the corpus's
  content in a way that is invisible from the reports.

- **`specialize.py` plain-binding suppression, fifth instance, same target node
  as the first.** `geotop.polyhedra.euler_polyhedron_formula`
  (`VERTICES - EDGES + FACES = 2`) covers
  `graphtheory.trees.tree_edge_count` (`EDGES = VERTICES - 1`) by binding
  `FACES -> 1`: a plane tree has exactly one face. Plain slot-to-literal
  binding, no absorption, no identity, so the filter drops it — exactly as
  recorded for `algtop.invariants.euler_characteristic_complex` covering the
  *same* polyhedron-formula node, for DE-9IM disjointness covering the
  complement law, and for surprisal covering the DPO loss. That node is now
  the target of two suppressed specializations from two different corpora,
  which makes it the natural regression test for the proposed fix (report
  matches whose bindings are non-trivial even when neither absorption nor
  identity fired).
- **RESOLVED (corpus gap): both blocked twin groups now exist.** The entry
  below asked for two nodes in `data/statistics`. Both have landed:
  `probstat.probability.probability_normalization` (earlier) and
  `probstat.probability.two_component_mixture` (`corpus/gapfill`). The mixture
  node typed- *and* shape-twins `numanalysis.interpolation.linear_interpolation`
  and `geomodel.bezier.de_casteljau_step` with no respelling, so
  `scripts/seed_numgraph.py`'s prediction 2(b) moves from *not evaluable* to
  FIRED. Two things are worth keeping from the episode. (1) *Not evaluable* was
  the right verdict to record and it was payable later by one node — a corpus
  gap is a cheaper defect than a matcher gap, and the reports should keep
  distinguishing them. (2) The fix cost nothing in tooling: the `(1 - WEIGHT)`
  spelling parses as written, so no BACKLOG item blocked it. The gap was
  purely that nobody had authored the statement.
- **A statement whose two standard spellings land in two different twin groups,
  in one node.** `probstat.probability.two_component_mixture` records
  `f = w*f_1 + (1-w)*f_2` in its template (the two-point convex-combination
  group: interpolation, de Casteljau, mixture — three disciplines) and
  `f = sum_k w_k*f_k` in `equivalent_forms` (the four-discipline weighted-sum
  group: Bezier, barycentric, total probability, Betti). One model, two
  textbook spellings, two disjoint groups, neither spelling wrong. This is the
  already-recorded "same statement, two spellings, and only one of them
  matches" item with the sharpest evidence yet, because here *both* spellings
  match — just not each other — so it cannot be dismissed as authoring luck
  about which form fires. It is the same K-to-2 collapse `specialize.py` cannot
  do (recorded for uniform-vs-Shannon entropy and for de Casteljau as the
  degree-one Bernstein case), now visible inside a single node.
- **`specialize.py`'s `rel` guard: 17 nodes, not 16.**
  `logic.inference.hypothetical_syllogism` is the newest node whose canonical
  template is a bare call rather than a relation, so it is dropped from the
  general side along with the sixteen already listed below. Confirmed
  empirically: of 582 specialization edges over 199 nodes, **zero** touch
  either node added on `corpus/gapfill`, in either direction. The mixture node
  is excluded for the other recorded reason (a recurring parameter slot plus a
  numeric literal in a multiplicative position), so one branch supplied a fresh
  instance of both filters at once.
- **The corpus gap is now measurable: two twin groups are blocked by one
  missing node.** `data/statistics` carries the law of total probability,
  Bayes's rule, z-standardization and the CLT, but **not** the normalization
  axiom `sum_i p_i = 1` and **not** a two-component mixture
  `p = (1-w)*p_0 + w*p_1`. Consequently
  `geomodel.barycentric.barycentric_partition_of_unity` (`1 = sum⟨?0:P⟩`) is a
  singleton whose exact structural twin is a one-line addition away, and
  prediction 2 of `scripts/seed_numgraph.py` ("linear interpolation versus
  probability mixtures") could not be evaluated at all — there was nothing to
  compare against, which is a different outcome from a miss and was reported
  as such. Both would be fixed by two nodes in `data/statistics`. That corpus
  still has no seed script (recorded above under cross-corpus reciprocity),
  so the cheapest fix to the graph's connectivity is currently the one that
  requires hand-editing the one file nobody can regenerate.
- **Same statement, two spellings, and only one of them matches — now
  quantified.** `numanalysis.integration.trapezoidal_rule` twins
  `geometry.area_formulas.trapezoid_area_formula` at typed level *because it
  was written with the one-half as a `constant` slot*; the textbook spelling
  `h*(f(a)+f(b))/2` produces `*(?1:P, +(?2:V, ?3:V), inv(2))` and matches
  nothing. Same for `numanalysis.interpolation.linear_interpolation`, where
  the expanded form `START + PARAM*(FINISH - START)` would have joined the
  five-member affine family and the written form
  `(1-PARAM)*START + PARAM*FINISH` joins nothing (the parameter slot recurs).
  In both cases the two spellings are algebraically identical, one fires and
  one does not, and the choice is the author's. This is the
  `authored_to_match` versus `emergent` distinction already requested for twin
  groups, seen from the authoring side: the corpus needs a way to record
  "these two templates are the same statement" so that a *normalizer* could
  eventually choose the canonical spelling, rather than relying on the author
  having already known which one fires. Without it, twin counts measure
  authoring luck as much as mathematical structure.
- **A `weighted_accumulation` archetype label was minted rather than adopted,
  deliberately, and the lint cannot tell.** `?0 = sum⟨*(?1, ?2)⟩` now spans
  three labels — `alternating_rank_sum` (topology),
  `conditional_marginalization` (statistics) and `weighted_accumulation`
  (both new geometric-modeling nodes). Neither existing label could honestly
  cover a Bezier point or a barycentric combination, and the new label could
  not honestly replace them either, so the drift entry is correct and
  unfixable by renaming. Same situation the ML corpus recorded for
  `state_minus_scaled_correction`. The pattern is stable enough now to
  propose the fix concretely: let `archetype_id` be a list, or add an
  `archetype_family` field, so a node can say "my label is X, my structural
  family is Y" and the lint can check the second while leaving the first free.

- **No scope construct, so `docs/DESIGN-frames-and-retrieval.md`'s central
  mechanism cannot be stated in a template.** `narrative.frame.frame_consistency`
  (`MEET(FRAMEPREMISE, NEG(FRAMEPREMISE)) = INCONSISTENCY`) is an exact typed
  twin of `logic.boolean_laws.complement_laws` and
  `settheory.boolean_laws.complement_laws` — which is the intended result, and
  also the whole problem. Everything that makes it a *frame* law rather than a
  logic law is the scope: "within frame F", frame premises occupying the
  frame's local VERIFIED tier, and their reversion to
  CONJECTURED-under-premise on scope exit. The grammar has no binder and no
  scope construct, so all of that sits in `regularity_conditions` as prose and
  the graph cannot check the boundary that the design document says is
  "structural, not stylistic". Same family as the lost quantifiers recorded for
  differential topology and the missing binder recorded for channel capacity,
  but with a new consequence: this is the first time the gap costs a *design
  document's* mechanism rather than a single statement's content. Fix shapes,
  in increasing order of work: a `scope` field on a node naming the frame its
  claims are relative to; a `FRAME(premises, claim)` head; or a real scoped
  construct in the grammar shared with the wanted `MAX(body, binder, domain)`.

  **FIRST FIX SHAPE SHIPPED** (branch `feature/frame-executor`): the live
  schema carries the draft's optional `scope` object (frame id, role,
  premises, suspends, governed_by, on_exit, retrieval), `validate_nodes.py`
  enforces frame-id pattern / frame agreement / reference resolution, and
  `scripts/frames.py` executes the boundary at runtime — declarations as
  the frame-local VERIFIED tier, suspension-gated contradiction, demotion
  on exit (32/32 tests; matcher report byte-identical, so the twin this
  item celebrates is untouched). Still prose-bound: nothing migrates
  `frame_consistency`'s own `regularity_conditions` into structure, no
  corpus node carries `scope` yet, and the `FRAME(...)` head / grammar
  binder remain the deeper fix shapes for statements *about* scoped claims.
- **No past modality, so half of a two-directional law cannot be written.**
  `narrative.constraint.chekhov_gun` states one direction — every planted
  element is eventually discharged. Its converse, `ALWAYS(IMPLIES(
  DISCHARGED(e), ONCE(PLANTED(e))))`, is the half that forbids deus ex machina
  and is the half most authors care about; it needs a past-tense modality
  (`ONCE`/`H` in the Manna–Pnueli past fragment) that `data/temporal_logic`
  does not carry. Adding one is cheap as a head, but note it will *not* twin
  its future dual for the usual reason, so the corpus would gain a statement
  and no structure. Recorded so that whoever adds past LTL knows the expected
  yield up front.
- **A strict order and its reflexive closure cannot share a head, and the
  corpus now pays for it inside one file.**
  `temporal.order.precedence_transitivity` uses the abstract `LEQ` head and is
  a three-discipline typed twin;
  `temporal.order.strict_precedence_asymmetry` uses `BEFORE` and is a singleton
  at every level. The second could not honestly use `LEQ`, because asymmetry is
  false of a reflexive relation, so this is not an authoring slip — it is the
  cheapest available demonstration that twin counts measure which head a
  statement is *allowed* to use. Companion to the recorded
  `authored_to_match` vs `emergent` request: a provenance flag on twin groups
  should be readable alongside this pair, since one member of an adjacent pair
  from one author lands in a cross-discipline group and the other lands nowhere.
  Wanted: a way to declare `BEFORE` as the strict part of `LEQ` (an order and
  its strict/reflexive variants as one declared family), which would also cover
  `⊆`/`⊂` and `<=`/`<`.


## Real-data lanes

- **Wikisem (LREC2020 logical forms) ingestion.** Corpus located and
  downloaded (43MB, 839 article-level lambda forms + 5,953 CG trees; see
  experiments/data_real/lrec2020-logical-forms/INGEST_NOTES.md for source
  URLs, format, and a prototyped mapping onto the matcher AST). Before the
  lane runs: (1) add `^` to COMMUTATIVE for conjunction chains, (2) fix the
  atom-classification wart (bound vars -> slots, `CATEGORY:lemma` atoms ->
  named leaves) so skeletons stop half-lexicalizing, (3) subterm mining is
  the granularity — sentence segmentation via variable indices fails on
  806/839 articles. LICENSE: data files carry no license statement (paper
  CC-BY covers the paper only); local research use only, no redistribution
  of derivatives without written confirmation from the maintainer.
  **Step (1) is blocked on a name collision, not on effort** (branch
  `tooling/head-algebra`): it cannot be done in `HEAD_ALGEBRA`. In this grammar
  `^` is exponentiation — `Parser.parse_power`, and `SIDE1^2` in
  `geometry.right_triangles.pythagorean_theorem` is not `2^SIDE1` — while in
  Wikisem `^` is conjunction. Declaring `^` commutative would silently
  scramble the 30 nodes in `data/` that use it as a power, so the table
  records `^` in its "deliberately absent" list with this reason. The lane
  needs either a lane-local algebra table layered over `HEAD_ALGEBRA`, or an
  ingestion step that rewrites Wikisem's `^` to `MEET` — which is already
  declared commutative, and is the head `data/logic` uses for conjunction, so
  the ingested forms would twin the Boolean corpora for free. The second is
  cheaper and strictly better.

## Proof-correspondence input digests hash raw working-tree bytes (newline-fragile)

`check_corpus` records each named input's SHA-256 over the bytes it reads from
the working tree, and `test_committed_report_is_regenerable_from_digest_named_inputs`
compares that against the committed `reports/proof_correspondence.json`. Raw
working-tree bytes are checkout-dependent: on Windows `core.autocrlf` smudges an
LF blob to CRLF on disk, so an LF-committed input digests differently than the
committed report expects. This surfaced at the v0.7 release on
`prover/proof-artifact-manifest.json` (the one hashed input committed as LF
while its siblings are CRLF) and was closed for the release by pinning that file
to `eol=lf` in `.gitattributes`, so every checkout materializes it the way the
report and every non-Windows run already see it.

The pin fixes the concrete break; the general shape is still fragile — a future
LF-blob input under `data/`, `prover/`, or the artifact set would reintroduce
it. The durable fix is to digest **canonical Git content** (line-ending
normalized, or read via `git cat-file`) rather than raw working-tree bytes, the
same move the depth source manifest already made ("binds mixed runtime bytes to
canonical Git content", DISCOVERIES). Deferred: it is trust-boundary code and
wants its own adversarial review, not a release-eve change.

## v0.8 process and nit debt

- **Release checkpoints must be staged before their worktree is removed.** The
  v0.8 analogy-model and depth-interface `.pt` checkpoints were gitignored inside
  their feature worktrees; removing the worktrees after ff-merge deleted them.
  Because CUDA is nondeterministic the loss is not fatal (the committed result
  JSON is the faithful record and the scripts regenerate a same-band checkpoint),
  and v0.8 shipped the JSON as the asset instead — but the release flow should
  copy any intended checkpoint asset out of the worktree before `git worktree
  remove`. Filed as a release-process fix, not a code bug.
- **`experiments/train_corpus_analogy.py` CLI default is `--epochs 80` but the
  committed v0.8 run and artifact are at 120.** Fully disclosed in the artifact
  (`config.epochs: 120`), no integrity impact, but a reader running the default
  gets a slightly different (still in-band) number than the reported run. Align
  the default with the reported run for one-command reproducibility.
- **`experiments/depth_interface.py:65` `MAX_TRAINED_TARGET_LENGTH = 88` is
  hardcoded.** Correct today (verified max train target = 88), but a data change
  would silently desync it; compute it from the training data or add a guard test.

## Carrier table: ℝ≥0/NNReal subtraction is monus-family (v0.10 quantifier-slice review filing)

- **`ℝ≥0`/`NNReal` sits in the coverage classifier's `_FIELD_TYPES`
  (pre-existing, v0.9), but mathlib's NNReal subtraction is TRUNCATED —
  monus-family, not the field `-` head.** So `∀ x : ℝ≥0, x - 1 ≤ x` covers
  under a head that misreads its subtraction (division and `⁻¹` over NNReal
  are honest; only `-` is wrong). Realized instances not yet counted at 1.73M
  scale. The fix belongs to the carrier-honest number-field slice
  (ROADMAP-v0.10 item 1, last bullet): either move NNReal to a monus-like
  carrier class for `-` while keeping its field reading for `/`, or give
  truncated subtraction its own head there. Filed from the quantifier slice's
  adversarial review rather than patched inline, because splitting one
  type's carrier class per operator deserves its own measured slice.

## Verdict-backed ingestion should be a RULE, not a precedent (v0.10 item 2 review filing)

- **PARTIAL — the rule is real for programming nodes, not yet for Lean ingest.**
  v0.10 item 3 (`docs/DESIGN-programming-discipline.md` §6, P7):
  `scripts/seed_programming.py` will not emit a `verified_by` link unless a
  committed `python-tests` PASS names that `statement_id`. The drop-abs FAIL
  does not satisfy the rule. v0.11 item 3 re-confirmed the rule at volume
  (six new PASS nodes; the n-minus-2 FAIL also does not satisfy it;
  `docs/DESIGN-programming-second-wave.md` P-W7). The Lean-ingest half is
  still open.
- **Nothing forces a future *Lean-ingested* node to carry a verdict.**
  `external_verifier.verdict_ledger_errors` checks every verdict that EXISTS
  and every manifest `verdicts` entry that is DECLARED, but a new artifact
  whose manifest entry simply omits `verdicts` is cited exactly like the 16
  pre-verifier propositional links — so the next ingest could quietly skip
  the authority the slice was built to establish. The invariant worth adding:
  a `verified_by` link whose statement is INGESTED (or, more generally, whose
  manifest entry declares a `source` .lean file) must resolve to at least one
  PASS `lean4` verdict over that source claiming that statement. Not patched
  inline because it is a validator WIDENING, not a fix — the registered
  design (docs/DESIGN-external-verifier.md §3) deliberately froze the link
  vocabulary this slice, so the new rung belongs to the ingestion slice that
  needs it (roadmap item 3 or the next ingest), with its own prediction.

## TOKEN_RE is missing the standalone `<` `>` already in RELATIONS (v0.10 item 4)

- **SHIPPED** with the v0.11 skeleton emitter (`docs/DESIGN-skeleton-emitter.md`
  P-E1). `TOKEN_RE` now matches `<` `>` after `<=` `>=`. All 51 first-wave
  misses became authorable (302 ground). Two `√(expr)` cases ride the
  emitter's `SQRT` rewrite, not a second token-class hole. parse_problems
  stays 0.

## specialize.py is already minutes-scale at 508 nodes (v0.10 item 4)

- **PARTIAL — bounded for ingested scale, not solved as a general index.**
  v0.11 P-E4 skips any specialize pair whose general or specific is in
  an ingested discipline. The 713 curated edges are unchanged; the run
  finishes in minutes at 12,771 nodes. The exhaustive pairwise search
  is still the algorithm on the curated graph. A head-indexed filter
  remains the follow-on if curated scale grows. `decompose.py` got the
  sibling skip (ingested-only forms are not patterns; ingested
  statements skip `pattern_cover`, P-E5b).

## Remainder of the 12,681 unique-covered set needs a skeleton emitter

- **SHIPPED** (`docs/DESIGN-skeleton-emitter.md`). 12,514 authored
  (302 ground + 12,212 emitted); **123 excluded**, bucketed in
  `experiments/lean_workbook_emit.json`. Dominant exclusions: matcher
  `parse_fail` 54, chained inequalities 16, superscript inverse `⁻¹`,
  primes in names, set-builder braces. The matcher was not widened.
- **The test suite independently reloads the 12k-node graph.**
  `analyze` (~4 min), `load_nodes` (~90 s), and `measure` (~90 s) each
  run from several tests. A full `min_family=1` analyze was 20+ minutes
  and is skipped above 1,000 statements. ~~A shared fixture or a curated-
  only analyze path would bring the suite back under ten minutes.~~

  **v0.16.0 status note (2026-08-21):** the shared fixture **shipped**
  (`fa0a174`, built once per module with the pins proved not to move). The
  prediction struck above was **wrong**, and worth keeping visible as a
  wrong prediction: the v0.16.0 suite runs **20,837.8 s — 5h47m**, nowhere
  near ten minutes. What the fixture actually removed was *duplicated*
  reload work, not the floor. The floor is `test_write_stage` at 12,008.7 s
  (57.6%), which no graph-reload fixture touches. The lesson: per-class
  duplication and the serial floor are different costs, and only the first
  was ever in this entry's reach.
- **`reports/decompositions.json` is not regenerated at 12k scale.**
  Live `analyze` is 181,867 exact constituents with full owner lists —
  a hundred-megabyte artifact. The committed report stays the pre-scale
  file. The self-grounding curve did not need that artifact: it is a
  live `analyze_loaded` query with in-memory overlays
  (`experiments/self_grounding_curve.json`). A summary-only decompose
  report remains the follow-on if a committed ledger at this scale
  becomes load-bearing.

  **v0.16.0 status note (2026-08-21):** this is no longer an unexamined gap
  — it is a **declared divergence**, checked on every release refresh by
  `scripts/check_report_regeneration.py`, which regenerates the other three
  ledgers clean and reports `decompositions.json` as divergent *by
  declaration* with its citation attached. The declaring authority is
  [TRIAGE-v0.11.md](TRIAGE-v0.11.md) §1 gate table row 6 (and §5):
  `reports/decompositions.json` stays the pre-scale ledger, with live
  `analyze_loaded` as the pin source. Recorded as ground-truth claim b13.
  The entry stays open only as the standing question it always was: whether
  a summary-only decompose report at 12k scale ever becomes load-bearing.

## Parked at v0.10.0 release triage (no named dependant in ROADMAP-v0.11)

ROADMAP-v0.11 adopts the rule v0.10's drift audit produced: a carried lane
must name the headline item that depends on it, or be parked here in writing.
These two carried lanes have no dependant in v0.11 and are parked rather than
carried a third time under the word "open".

- **Proof-search curve depth.** Carried since v0.9 item 5. The proof curve
  (`prover/curve_search.py`) works and its 24-theorem result stands; deepening
  it serves no v0.11 headline item. Unpark when a cycle has a claim that needs
  deeper search — the likely trigger is a verifier-backed synthesis lane, not
  the corpus work.
- **The groundedness gate.** Carried since v0.9 item 5. v0.11 item 1
  answered the parking condition: self-grounding is a real signal
  (S1–S4 fired; the route-2 proxy is *not* the signal — it reads 1.0
  of grounded constituents while route-1 ISG of those is 0.543). A
  gate is now justifiable as a design, not a regime snapshot. Unparked
  for the next cycle that wants an admission signal; not designed here.
  Any gate must still beat the conservative/`external_lower` bracket
  and must not treat the proxy as ownership.

  **RE-PARKED in v0.12, because H1 failed.**
  `DESIGN-heldout-recovery.md` §8 set this condition in advance — "If H1
  fails, the gate stays undrawn — the parking condition returns" — and it
  returned. Held-out B (Goedel-Pset) at N=1,896 scores owner-attributed
  ISG **0.0254 against a null of 0.1513**, a gap of **−0.126** that grows
  *more* negative with N; held-out A (miniF2F) is below its null at every
  size. v0.11 unparked this gate on the strength of S1–S4 firing. One
  cycle later, two sources the emitter was not fitted to say that
  strength was source-specific, and the matched-N control (C1) shows the
  difference is source and not scale: at identical N=157 the fitted
  source scores +0.0496 and the holdout −0.0428.

  A threshold drawn now would be fitted to Lean-workbook's 0.473, which
  §8 forbids by name. **Unpark only when some source other than
  Lean-workbook shows a positive owner-attributed gap that survives its
  own null.** Note this is the *second* park of this item, and the second
  park is better evidenced than the first unpark was.

Both were honestly sequenced behind corpus work each time they were carried;
naming that is the point of the rule, not blaming the deferral.
