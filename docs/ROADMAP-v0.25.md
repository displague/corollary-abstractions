# Roadmap v0.25 — the person declares a symbol, if the course's selection survives adjudication

v0.24 scheduled the smallest live failure the project had and got both a
capability and a negative. The capability: on a third served profile, the
same four bytes take **different verified interaction moves** — `hello` is a
greeting at a fresh root and a `probe_reply` under a live probe, by sealed
corpus witness and context predicate, never by surface bytes — with all nine
scored gates green over 87 receipts and both blind controls scoring
*exactly* their frozen ceilings (21, 21, 17), which is what a non-leaking
runtime looks like. The negative: **B7 is RED**. An unmodified codex-cli
0.150.1 bound a `function_call_output` to the exact pending request id and
the payload it bound was its own router's refusal, *"request_user_input is
unavailable in Default mode."* A tool that is captured and advertised is
not thereby a tool that can be called. No Codex prompt-tool support is
claimed, and nothing was widened after the red.

Two things v0.24 falsified about its own plans travel into this one. First,
the negative above: the design had recorded the Plan-mode caveat *in
advance*, and the run still went further than the caveat predicted and
still failed — which is why B7 reads RED rather than UNTESTED. Second, the
forward design for **this** cycle did not survive its first review: three of
[DESIGN-house-rules](DESIGN-house-rules.md)'s reuse claims were false of the
code, the draft tripped its own stop-before-implementation clause, and the
rework sheds frames and premises entirely. That review record ships inside
the design. This repository publishes its retractions.

This cycle starts from that reworked design. As with v0.24, **this document
does not silently promote the incumbent to a scheduled capability**: §1 is
conditional on the roadmap's own adjudication against the incumbent queue,
and STRANGER-GATE's prohibition is a prohibition, not a candidacy.

**Links** — previous plan: [ROADMAP-v0.24](ROADMAP-v0.24.md) · previous
release: [RELEASE-v0.24.0](RELEASE-v0.24.0.md) · incumbent design:
[DESIGN-house-rules](DESIGN-house-rules.md) · receipt:
`reports/design-direction-v0.25.json` · this cycle's post:
[the question it bound and would not ask](blog/the-question-it-bound-and-would-not-ask.md)

## 1. Headline — HOUSE RULES, if the course's selection survives the roadmap's own adjudication

The v0.25 course ran three isolated three-round series — fifteen round-one
directions, **$2.53** total, headless from an empty non-git directory under
a strict tool denylist — and selected **HOUSE RULES**
(`reports/design-direction-v0.25.json`). Six of the fifteen independently
re-arrived at parked or carried ground and are recorded as convergent
evidence rather than as lanes; a seventh, ERRAND, survived its series only
as CHOKE, a **second independent arrival at STRANGER-GATE's own shape**.

**The boundary being moved.** A person can already *suppose* a claim:
`suppose x = 5` declares a session-scoped assumption, capped at 8,
superseded by subject, cited by read barrier, consumed by `evaluate`. But a
supposition that is not a binding is held as an **opaque atom** — `suppose
parent(alice, bob)` stores normalized text — so the system cannot tell a
well-formed use of the person's own vocabulary from a typo, because the
person has no way to tell the system what their vocabulary *is*. The
boundary moves when this becomes recordable: *given this declaration line,
the system either admitted a fresh relation symbol — name, arity, argument
categories — into a session-scoped symbol ledger, or refused it with
exactly one deciding clause, totally and by default toward refusal; and
from that turn on, a supposition applying the declared symbol is checked
against the declaration exactly, with misuse refused by name instead of
held as opaque text.*

**One verdict kind ships:** `ADMITTED_DECLARED_SYMBOL`. Axioms about
declared symbols, conservativity, export, persistence, and truth are all
refused **in writing** by the same total function. The axiom question is
real and is deliberately the *next* askable question, priced against a
corpus of real declarations this slice would be the first to produce.

**Why the demand claim is deliberately weak.** The design does **not** cite
v0.23's 0-of-21 recast yield as demand for declarations — the review
corrected that gloss, and it stands corrected here: 0/21 is a
*rendering-coverage* fact, not a vocabulary-gap measurement. The claim is
structural instead: the person's side of the conversation has vocabulary
the program never authored, and today every use of it is opaque.

**If the adjudication does not keep it,** this item parks with the design
reviewed and unimplemented, and the incumbent queue is unchanged.

### Acceptance if scheduled

- **Construction order, in the design's order and no other:**
  **H-PRE** (fixture seal — `experiments/house_rules_fixtures.json` from a
  committed builder: ≥8 admitted-path exercises across ≥3 arities and ≥4
  categories, each of the eight refusal codes fired at least once, plus the
  B3 mutant set; a refusal code no grammatical fixture can fire is deleted
  here, U-PRE-style) → **H-P0** (census, checker, ledger module, the
  `declare` grammar row, **and in the same change every pin that row
  moves** — `line_grammar_digest` consumers, the position-indexed
  `experiments/session_p1_command_bound.json`, the CR-P0 registry re-seal,
  the generated capability-sheet row) → **H-P1** (the registered run on a
  clean tree, under v0.24's gates-runner dirty/wrong-tip refusal pattern,
  with exactly two declared output paths).
- **Gates B1–B11** as frozen in DESIGN-house-rules §7, with B9's voiding
  sentence: *if the surface-only admitter's out-of-half agreement with the
  checker exceeds the scored half's majority-class rate by more than ten
  points, the verdict is separable from every ledger and schema input, the
  capability is void, and the slice ships as an honest negative.* The
  8/3/4 floors, B3's ≥30, B7's 6-of-8 and B9's ten-point margin are
  **declared construction bounds, not measurements**, and the notes must
  say so.
- **R-H2 is reported regardless and gates nothing:** the count of the 30
  sealed inbound hypotheses that parse as declarations (expected ~0), any
  nonzero rows quoted verbatim. It cannot pass or fail the slice — the
  only honest corpus of declaration requests is the one the capability
  creates.
- **Three construction refusals.** Any one of them stops the slice rather
  than being repaired into a pass:
  1. **An axiom or premise about a declared symbol admitted in-slice.**
     One verdict kind ships; connectives, binders and relational axioms are
     refused by the grammar, not by dead code.
  2. **Persistence of any declared symbol.** No written session document,
     journal, or durable artifact from the run may contain an admitted
     fixture symbol name, swept over the run's full output tree (B5), and a
     fresh session's use of an admitted symbol must take the opaque-atom
     path.
  3. **Any byte toward a generated library file.**
     `write_stage.working_tree_digest` byte-identical across the registered
     run except the two declared output paths (B4), with `durable_digest`
     over `data/` as the narrow named control.
- **Non-claims, published with the result:** ledger-groundedness, never
  correspondence — an admitted declaration is well-formed and fresh, never
  true or useful; no use-side *category* checking; no natural-language
  declaration; no behaviour on the served HTTP profiles beyond the
  published ¶DEV-1 note; no claim about what people will declare once they
  can.

### 1.1 The course's selection — to be adjudicated, and recorded as a decision

**Not yet decided.** v0.24 §1.1 is the shape this section owes: a recorded
decision with a disposition for **every** incumbent, not a preference. The
adjudication has two questions this time.

- **Does the slice open an untrusted stream toward the write gate?** On the
  design's own account it does not — no execution, no durable write, no
  learned component on the admission path (enforced by an import-closure
  assertion), and B4/B5 are the fences that can go red. If that survives
  scrutiny, STRANGER-GATE's prohibition is honored rather than displaced,
  exactly as in v0.24. **CHOKE's second independent arrival at
  STRANGER-GATE's shape hardens that park's priority and does not schedule
  it.**
- **Does any incumbent have a fired trigger this cycle?** The naming-layer
  question now has a genuinely new candidate mechanism (HANDLE, §3);
  PREMISE LEDGER has two new independent arrivals; TOLL has a named
  deciding log-probe. Convergence is evidence *for* a park, not a trigger,
  and the adjudication must say which of those is which in writing.

## 2. Prerequisites and small lanes that are not this cycle's headline

These do not start unless §1's adjudication names them as dependants —
except the second, which is scheduled on its own terms and says why.

- **The two B7 successor probes.** Filed at the red, neither taken in
  v0.24, neither a dependant of §1.
  1. **Plan-mode router probe.** The host advertises `request_user_input`
     in every mode but its router executes it only in Plan mode, and no
     exec-mode flag reaches that switch. Whether Plan mode completes the
     round trip is **unmeasured**. Unpark needs a live run and its
     rollout evidence, on the same instrument
     (`scripts/run_b7_roundtrip.py`), with the same rule: a scripted
     self-check cannot license B7.
  2. **The echoed-`function_call` admission question.** A `store: false`
     host replays its own `function_call` item in `input`, which ¶AMD-3's
     deliberately narrow §4.2 scope refuses. Admitting it is a **wire
     question owing its own registered test and a dated amendment** —
     never a widening after a red. Note the standing arithmetic: even if
     the echo were admitted, the bound output is an error string, not a
     candidate move, so the resume refuses `UNBOUND_ANSWER`. Admitting the
     item alone cannot turn B7 green, and a probe that claims otherwise is
     scoring the wrong thing.
- **The `sum_total` silent-capture hazard — a named checker-fix candidate,
  and it STANDS ALONE.** The v0.25 adversarial review found that the
  shipped template parser rewrites any identifier beginning `sum_ /
  prod_ / lim_ / max_ / min_` into the corpus aggregate head
  (`scripts/match_signatures.py`, `HEAD_ALIASES` / `BIG_OP_PREFIXES`), so
  `sum_total(x)` is silently reinterpreted as `aggregate` **with no
  refusal**.

  **The decision, made here rather than deferred: it does not ride H-P0.**
  H-P0's census carries the reserved prefixes as a *prefix guard* so a
  **declared** `sum_total` refuses `RESERVED_PREFIX` — but that converts
  the hazard only at the declaration boundary. The shipped parser keeps
  rewriting, and if §1 shipped alone a reader could mistake "declaring
  `sum_total` is refused" for "the parser no longer silently rewrites
  `sum_total`." The second is still false. So this is a separate small
  lane with its own acceptance: **a refusal or a disclosure, never a
  silent rewrite** — either the parser refuses the capture by name, or the
  rewrite is recorded in the term's own receipt where a reader can see it
  — plus a test that goes red on the current behaviour. If §1 is scheduled,
  this lane is ordered **before** H-P0 so H-P0's census cannot be read as
  having discharged it; if §1 parks, this lane still runs.

- **GUEST AXIOM inbound slice.** Unpark unchanged from ROADMAP-v0.24 §2:
  a drawing rule committed before a draw whose non-exhaust targets sit in
  `measure_foreign_voice.covered_rows` (or a dated amendment of that
  constructor), **and** an externally-sourced correction log whose commit
  is an ancestor of that draw. Do not invent
  `experiments/crossing_corrections.json` in the draw commit.
- **ECHO native-instrument amendment.** Unpark unchanged: a dated
  amendment that either supplies a native external adjudicator and a
  disjoint reader, or scopes the collision claim to the second voice alone
  and says so. The 0/50 and 0/500 denominators stay.
- **HANDBACK.** Unpark when GUEST AXIOM has a restricted population ≥15
  **and** a collision or separator result licenses the ask-arm. Third
  cycle parked, trigger unchanged.

## 3. Carried, with dependants named

The rule is unchanged: **every carried lane names its dependant, or it
parks in [BACKLOG](BACKLOG.md) with the reason.** ROADMAP-v0.23 §4.3 is
still the parent list; only the rows whose state moved this cycle are
restated here.

| lane | state entering v0.25 | trigger to unpark |
|---|---|---|
| **The naming-layer question** — *how does a nameless library get names a person can ask by?* | Carried a **third** course unchanged, but no longer without a mechanism: the v0.25 course produced **HANDLE** (total canonical addresses for the unnamed bulk, decidable and injective), which survived to round two at rank 3. Its recorded anti-vacuity lesson travels with it — an address scheme that is total and injective can still be unaskable, so a HANDLE slice owes a person-side reachability arm, not just a construction proof | A design naming the mechanism *and* what would falsify its usefulness. HANDLEBAR parks behind it. If §1's `declare` row ships, the naming-layer question gains a second live surface and should be re-examined at the v0.26 course, not silently re-carried |
| **STRANGER-GATE** — the write gate's overdue adversarial red-team | **Prohibition trigger intact, second cycle honored-not-displaced, now with a second independent arrival.** ERRAND→**CHOKE** re-derived its shape from an isolated context that had never seen it — the static quarantine check plus the red-team that discharges or confirms the prohibition. Convergence hardens the park's priority; it is not itself a trigger | MUST run before any untrusted stream reaches the write gate. Its residual risk is unchanged and recorded: one head authors the attacks, the twins, and the gate, so it measures whether the gate DISCRIMINATES, never whether the corpus is ADEQUATE. DEPUTY remains the named next asker, blocked behind it |
| **PREMISE LEDGER** (supplementary-family, capability-class) | Carried unchanged for a **third** cycle, now with **two** new convergent arrivals in one course: **NEEDED-BY** (minimality certificates by replay-ablation → its measurement arm) and **COUNTERMODEL / WITNESSED-NO** (witnessed-no via finite countermodels → the *constructor* the incumbent still lacks, plus a new answer kind). LOADBEARING stays folded into it | A design that takes the necessity claim — explicitly not taken at v0.23, v0.24, or here. The countermodel constructor is now named as the missing half, which is progress on the park, not on the schedule |
| **CANARY-CURVE** (instrument-class) | Carried unchanged | Still blocked on an enumeration layer that does not exist |
| **TOLL** (cost-lane metrology; CEILING routes with it) | Carried unchanged, and now with a **named deciding mechanism**: PRICE FIRST folded into it with its log-probe — pre-committed cost bounds with calibration. Instrument (the v0.22 cold-census harness) and denominator path (ORPHAN) already recorded | Denominator still n=1. Unpark needs ORPHAN's denominator or the log-probe run as its own registered lane |
| **The cost ledger** (answers per joule and per dollar) | **NINTH parked cycle**, counting basis unchanged (rotations since `DESIGN-grounded-throughput` §10: v0.17–v0.25). Nothing was designed for it this cycle either. Its metrology now has an instrument, a denominator path, **and** a deciding probe — which is the only thing that moved | Named here so the ninth pass-over is a decision on the record and not attrition |
| **ORPHAN** — receipts that outlive the program | Carried, now with a **shape**: THIN-VERIFIER (a ≤500-line stdlib-only verifier converting one program-dependent receipt kind, with a TCB document) independently re-arrived at it and folds in as the successor's mechanism | Unparks TOLL's n=1 denominator. Unpark needs a design choosing *which* pinned dependency converts the most NEEDS-PROGRAM kinds — the cold census's own recorded next question |
| **MIRROR FRAGMENT** — an exact-grammar English reader provably disjoint from the renderer's module closure | **New park, and the highest-ceiling decline of the v0.25 course.** The named successor to the plain-input lane | Its own pre-gate, exactly: **≥300 renderable entries each carrying ≥2 content lemmas outside the nine boilerplate glossary words, and ≥40 distinct content lemmas overall.** Below that the reader has nothing to read that is not boilerplate |
| **DIMENSION** — dimensioned quantities with outward-rounded enclosures | **New park, as a strong RIDER candidate** rather than a headline: a discipline upgrade on an already-exact path moves the person-facing boundary least | Unpark as a rider on a cycle whose headline touches evaluation. Residual risk recorded and carried: **a dimensionally degenerate family yields a coherent, provenance-clean table whose mismatch gates are never exercised** — internal consistency is what the numbers buy, correspondence is not on the ledger |
| **EARNED ASK** | Not a lane: a **constraint on any future ASK arm**, recorded so it binds without being scheduled. Any question the admissibility path mints must carry a partition witness, and precondition failure returns the ambiguity rather than a fallback question | Binds the next lane that mints questions; §1 mints none |
| **LAPSE** — observation-backed claims that expire and re-open exactly | New park | No observation channel exists. Its replay harness is noted as machinery shared with the erratum/no-flip lane |
| **SELF-SEED, UPSTREAM-PATCH, FOREIGN-SEAM, HANDLEBAR, DEMAND, the resolver's pre-emptive binding, the `conform` route's advertised-and-unused bindings, the G5-metric successor, TWO WITNESSES + the independent second reading, ledger-first claims, open-English input / the reverse-lexicon synonym layer, realization parameters as data, the register's `mathlib_head` budget, HOSTILE DICTATION, CROSSING, LONG CON, BITROT, C-V3 and the v0.19–v0.22 catch-alls** | Carried unchanged, with the triggers recorded in ROADMAP-v0.23 §4.3 and the `reports/design-direction-v0.19/20/21/22/25.json` receipts. **No v0.25 headline item names any of them as a dependant** | As recorded there. DEMAND keeps its triple convergence; TWO WITNESSES now has a **third** arrival (TWO KILNS, a second independently written generator) |

**HOUSE RULES does not displace STRANGER-GATE's prohibition.** No untrusted
execution or write stream opens this cycle unless STRANGER-GATE has run.

## 4. Release gate (draft)

v0.25 is ready only if:

- the course's selection is **adjudicated in this document** with every
  declined disposition recorded, v0.24 §1.1's shape;
- the selected slice meets its own construction stops, or the slice ships
  as the honest negative its gates license — a fired B9 or a failed
  construction gate is a **result**, and B7's red at v0.24 is the
  precedent for publishing one;
- the three construction refusals (§1) did not occur, or the slice stopped;
- **the `sum_total` hazard is discharged or parked in writing**, and the
  notes do not let H-P0's prefix guard stand in for the shipped parser's
  behaviour;
- STRANGER-GATE's prohibition is honored or discharged in writing, and the
  cost ledger's ninth pass-over is recorded as a decision;
- `check_report_regeneration.py` verdicts are **in the notes**, and
  `ingest_wold.py reach` either runs or is reported as *cannot verify*
  rather than as a skip;
- every unfinished item ships, carries, or parks **in writing**;
- the outside design inquiry for v0.26 is named with its receipt;
- the full suite is green on a frozen tip with retained receipts, and
  **`[SUITE-GATE-V25]` is resolved rather than left as a placeholder**.
