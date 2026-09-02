# v0.25 release triage — the §4 gate, item by item, on artifacts

Written before the rotation documents so the calls are visible as calls, in
the shape [ROADMAP-v0.25](ROADMAP-v0.25.md) §4 froze them. Every line below
names the artifact or commit that settles it. Where a gate line is **not
settled by this lane**, it says so and names who owns it, rather than being
quietly counted as met.

Method note, carried from the v0.24 deep triage (`449cac8`): a claim is
verified against the primary artifact — the committed JSON, the parser
source, the checker's exit code — and never against a release sentence that
describes it.

## 1. The §4 release gate

| §4 clause | disposition | evidence |
|---|---|---|
| the course's selection is adjudicated in this document, every declined disposition recorded | **MET** | ROADMAP-v0.25 §1.1, written at commission `d11e3fb`. Row-by-row dispositions for every incumbent; two questions answered in writing |
| the selected slice meets its construction stops, or ships as the honest negative its gates license | **MET — twelve green, no negative owed** | `experiments/house_rules_verdicts.json` at `f9719a2`: B1–B12 all GREEN, `gate_reds` empty, `voiding_sentence` unfired, R-H1 `green: true`, R-H3 `licensed: false` |
| the three construction refusals (§1) did not occur, or the slice stopped | **MET — none occurred** | (1) one verdict kind ships, `ADMITTED_DECLARED_SYMBOL`; axioms refused by the grammar (B6 3/3 wrong-arity refusals, B7 8/8 refusal codes on the sweep against a floor of 6). (2) No persistence: B5 GREEN, 0 of the run's documents carry an admitted name. (3) No byte toward a generated library file: B4 `working_tree_digest_byte_identical: true` (`c792b8cb…` before and after), `durable_digest` over `data/` unmoved, 0 stage records |
| **the `sum_total` hazard is discharged or parked in writing, and the notes do not let H-P0's prefix guard stand in for the shipped parser's behaviour** | **DISCHARGED — as disclosure, not refusal.** §2 below is the required sentence | `156e94f`, `249f463`; `scripts/match_signatures.py:541-563`; `reports/signature_matches.json` `parse_rewrites` |
| STRANGER-GATE's prohibition is honored or discharged in writing | **HONORED, third consecutive cycle — and now with run evidence, not only a design argument** | §3 below |
| the cost ledger's ninth pass-over is recorded as a decision | **RECORDED** | ROADMAP-v0.25 §1.1 and §3's cost-ledger row; §4 below restates it as a decision with its counting basis |
| `check_report_regeneration.py` verdicts are in the notes | **MET — verdicts in §5, exit 0** | run at this lane's tip |
| `ingest_wold.py reach` either runs or is reported as *cannot verify* rather than as a skip | **CANNOT VERIFY**, with the exact reason | §6 below |
| every unfinished item ships, carries, or parks in writing | **MET** | §7 (roadmap §2) and §8 (roadmap §3) |
| the outside design inquiry for v0.26 is named with its receipt | **NOT SETTLED BY THIS LANE — owned by the parallel v0.26 design course** | its deliverables are `docs/DESIGN-*.md` and `reports/design-direction-v0.26.json`; this lane touches neither |
| the full suite is green on a frozen tip with retained receipts, and `[SUITE-GATE-V25]` is resolved rather than left as a placeholder | **NOT SETTLED BY THIS LANE — the suite gate runs at the frozen tip after the rotation**, `[SUITE-GATE-V24]` / `d320fce` being the precedent | open |

## 2. The `sum_total` hazard, discharged — and exactly what the parser still does

§4 requires that these notes not let H-P0's prefix guard stand in for the
shipped parser's behaviour. So, precisely:

**What the shipped parser still does to a big-op suffix.** In
`scripts/match_signatures.py`, `Parser.parse_atom` (`:541-563`) tests
`tok.lower().startswith(BIG_OP_PREFIXES)`, where `BIG_OP_PREFIXES =
("sum_", "prod_", "lim_", "max_", "min_")` (`:92`). When it matches, the head
becomes `tok.lower().split("_", 1)[0]` and **everything after the first
underscore is discarded from the tree**. `sum_total(x)` therefore still
parses, still becomes a `("call", "sum", …)` node applied to the following
product, and still loses the characters `total`. `sum_total` and
`sum_anything` still produce one identical tree. **No refusal exists, and
none was added.** That is the shipped behaviour at this tip, stated here
rather than left to be inferred from the absence of a complaint.

**What changed at `156e94f`, and it is exactly one thing.** The branch now
appends a record to `Parser.rewrites` *before* it discards anything — the
rule name, the authored token verbatim with the author's own casing, its
index in the token stream, the head it became, and the discarded characters
— and `load_nodes` hands that record to `ParsedNode.parse_rewrites`, which
`reports/signature_matches.json` republishes in two places: a total
top-level `parse_rewrites` section beside `parse_problems`, and a per-member
field inside twin groups. The tree the branch returns is unchanged; all
12,777 committed trees are unmoved.

**Why disclosure and not refusal — a census, not a preference.** Across
14,830 committed `anonymized_template` strings (13,950 distinct, over the 40
committed files that carry one), exactly **17** hold a big-op-prefixed
identifier: `sum_i` in 16 and `lim_h` in 1, across nine disciplines. There is
no `prod_`, `max_` or `min_` occurrence in the committed corpus at all.
Genuine big-operator usage is therefore real, and a refusal would break
sealed committed parses that are not defective.

**The heuristic deliberately not implemented.** All 17 real suffixes are
single-letter index names, so "a word-shaped suffix is suspicious" would have
separated them from `sum_total` on today's corpus. It is not implemented,
because it is a new authored judgement the design never priced and it would
put the parser in the business of deciding which captures deserve a record.
The disclosure is **total** instead — `sum_i` is recorded exactly as loudly
as `sum_total` — and totality is what makes it judgement-free and safe to add
underneath a freeze.

**What H-P0's prefix guard does NOT change.** The guard is
`scripts/symbol_ledger.py:563-564`:
`if parsed.symbol_name.startswith(tuple(inputs.reserved_prefixes)):
held.append("RESERVED_PREFIX")`. It fires at the **declaration boundary
only** — a person typing `declare sum_total(...)` is refused with the code
`RESERVED_PREFIX`. It does not run when a template is parsed, it is not on
`match_signatures.py`'s call path, and it changes the behaviour of exactly
zero committed templates. A reader who took "declaring `sum_total` is
refused" to mean "the parser no longer silently rewrites `sum_total`" would
be wrong, and this paragraph exists so that reading is unavailable.

**The standing detector.** B12 — round-trip identity, an admitted name must
survive parsing byte-identically, with mutants seeded at
reserved-prefix-adjacent names — is what keeps the two surfaces from drifting
apart again. GREEN at `f9719a2`: 13/13 pairs against the live ledger key,
16/16 mutants.

**Citation corrected here.** DESIGN-house-rules §4's status note said the
branch "now lives in `parse_sum` around `match_signatures.py:541-563`". The
line range is right; the function is `Parser.parse_atom` — `parse_sum` is the
additive production at `:495`. Corrected in place with this lane.

**The one artifact `156e94f` knowingly left stale**, discharged in this same
rotation: `experiments/cold_registry_census.json`. That commit recorded why
it did not re-seal — re-sealing breaks `cold/census_run2.json` and
`cold/scramble_baseline_run2.json`, which list the registry as an input, and
would force a registered cold attestation to re-run as a side effect of a
parser disclosure — and assigned the re-seal to the CR-P0 lane. See §10.

## 3. STRANGER-GATE — honored, with run evidence

**The prohibition, verbatim** (ROADMAP-v0.25 §3): *"MUST run before any
untrusted stream reaches the write gate."* ROADMAP-v0.25 §1.1 adjudicated it
at commission as **honored, not displaced — third consecutive cycle.** What
this triage adds is that the argument is no longer only prospective: the
registered run scored the fences §1.1 promised, and they can be read off the
artifact.

| the §1.1 claim | what the run shows |
|---|---|
| the admission path executes nothing and writes nothing durable | B4 GREEN: `working_tree_digest` byte-identical `c792b8cb…` → `c792b8cb…`; `durable_digest` over `data/` unmoved; **0 stage records** |
| no declared symbol persists | B5 GREEN: 0 of the run's own documents carry an admitted name; 19 pre-existing repository files disclosed and classified (the sealed corpus and its readers, not run output) |
| the path carries no learned component | B11 GREEN: import closures of size **3** for each of `symbol_ledger.py`, `check_symbol_census.py` and `build_symbol_census.py` — each closing over only `match_signatures.py` and `report_provenance.py` — with **0** forbidden imports from a list naming `torch`, `numpy`, `scipy`, `sklearn`, `transformers`, `sentence_transformers`, `tensorflow`, `jax`, `openai`, `anthropic` |
| declared vocabulary cannot cross an HTTP turn | ¶DEV-1: the served profiles replay every request into a fresh session. B3's `fresh_session_has_no_ledger_entry` detector was exercised on live sessions and fired |

**Scope, travelling with the claim.** This is evidence that **no untrusted
stream was opened**, which is what the prohibition asks. It is not evidence
that the write gate would survive one — that is what STRANGER-GATE itself
would measure, and it has still never run. Its recorded residual risk is
unchanged and travels with the park: one head authors the attacks, the twins
and the gate, so it can only measure whether the gate DISCRIMINATES, never
whether the corpus is ADEQUATE. DEPUTY remains blocked behind it. CHOKE's
second independent arrival at its shape hardens the park's priority and
schedules nothing.

## 4. The cost ledger — ninth pass-over, recorded as a decision

Counting basis, unchanged: rotations since `DESIGN-grounded-throughput` §10,
i.e. v0.17 – v0.25 inclusive = **nine**. Each of the eight previous
pass-overs was recorded as a decision in its rotation's roadmap; this is the
ninth, recorded the same way rather than allowed to become attrition.

**The decision: nothing is scheduled for the cost ledger in v0.25.**

What moved this cycle is **metrology only**, and naming what moved is what
distinguishes a decision from a lapse:

- **instrument** — the v0.22 cold-census harness, which exists and runs
  (`harness/cold_harness.py`; it ran again in this rotation, §10);
- **denominator path** — ORPHAN, which now has a *shape*: THIN-VERIFIER, a
  ≤500-line stdlib-only verifier converting one program-dependent receipt
  kind, with a TCB document. Still no design choosing *which* pinned
  dependency converts the most NEEDS-PROGRAM kinds;
- **deciding probe** — PRICE FIRST's log-probe, folded into TOLL:
  pre-committed cost bounds with calibration.

None of the three ran as a registered lane, and the reason is recorded rather
than implied: **no v0.25 headline names any of them as a dependant**, and
TOLL's denominator is still n=1.

**Restated because it is the disclosure this lane owes:** the throughput
scorer moved after v0.17 and nothing has been re-measured through it, so
whenever the next readout happens it is **not a like-for-like comparison with
v0.17's** and owes that sentence in writing.
`experiments/throughput_tasks.json` did not change this cycle either.

## 5. `check_report_regeneration.py` verdicts

Run at this lane's tip, `.venv` interpreter, no arguments:

| ledger | verdict |
|---|---|
| `reports/signature_matches.json` | `clean` |
| `reports/specializations.json` | `clean` |
| `reports/compression.json` | `clean` |
| `reports/decompositions.json` | `declared_divergence` — declared pre-scale snapshot; TRIAGE-v0.11 gate table row 6 and §5; live analysis is the pin source |

**Exit 0. Nothing failed to regenerate, so nothing was regenerated here and
no report moved.** The one divergence is the declared one and is not a drift:
`reports/decompositions.json` stays the pre-scale ledger by the authority of
[TRIAGE-v0.11](TRIAGE-v0.11.md) §1 gate-table row 6 and §5, with live
`analyze_loaded` as the pin source. Regenerating it would destroy the
snapshot that decision preserved, which is why the checker refuses to.

Worth stating because §2 could have broken it: `156e94f` changed
`scripts/match_signatures.py`, the writer behind `signature_matches.json`.
That report reads **clean**, meaning the committed bytes equal what the
changed writer produces — the disclosure was regenerated by its own writer,
never hand-edited. This is the ninth consecutive release for which these
verdicts exist; RELEASE-v0.23.0 was the one break in the chain and carries a
dated addendum saying so.

## 6. `ingest_wold.py reach` — CANNOT VERIFY, with the reason

Run at this lane's tip:

```
python scripts/ingest_wold.py reach
MISSING: <repo>\data_sources\archives\english-wordnet-2025-json.zip not present.
Fetch the pinned source first:
  python scripts/fetch_sources.py --fetch wordnet-2025-json
exit 2
```

**This is a cannot-verify, not a skip, and the distinction is load-bearing.**
The reach stage requires the manifest-pinned Open English WordNet archive *by
construction* — `run_reach` treats it as **required, not optional**, in its
own words "so the committed number is never a silent partial". The archive is
licensed external data, and this repository's standing rule is that licensed
external data never enters git: it lives gitignored under
`data_sources/archives/` and must be fetched. It is absent in this
environment, so the stage refuses rather than computing a partial reach
number.

What is *not* claimed: that `experiments/wold_reach.json` is stale, or that
it is current. Neither was checked, because the check is exactly the thing
that could not run. The committed artifact stands unexamined this cycle, and
that is the honest state.

## 7. ROADMAP-v0.25 §2 — every prerequisite and small lane, disposed

| §2 item | disposition | evidence |
|---|---|---|
| **B7 successor probe 1 — Plan-mode router probe** | **CARRIES, unrun, trigger unchanged.** Not named a dependant by §1; not taken | ROADMAP-v0.25 §2. Unpark still needs a live run on `scripts/run_b7_roundtrip.py` with rollout evidence; a scripted self-check still cannot license B7 |
| **B7 successor probe 2 — the echoed-`function_call` admission question** | **CARRIES, unrun, trigger unchanged.** Not taken | ROADMAP-v0.25 §2. The standing arithmetic travels with it: even admitted, the bound output is an error string, so the resume refuses `UNBOUND_ANSWER` and B7 cannot turn green on the item alone |
| **The `sum_total` silent-capture hazard** | **SHIPPED** as disclosure, ordered before H-P0 exactly as §2 required | `156e94f` (parser + receipt + red-first test), `249f463` (design's hazard note dated). §2 above is the full discharge |
| **GUEST AXIOM inbound slice** | **PARKS, unpark unchanged** | No drawing rule was committed before a draw, and no externally-sourced correction log exists whose commit is an ancestor of a draw. `experiments/crossing_corrections.json` was not invented. The v0.24 triage's separate filing stands: B6 is **unadjudicated, not discharged**, and is the lane's first act on unpark |
| **ECHO native-instrument amendment** | **PARKS, unpark unchanged** | No dated amendment was written. The 0/50 and 0/500 denominators stay |
| **HANDBACK** | **PARKS, fourth cycle, trigger unchanged** | Blocked behind GUEST AXIOM's restricted population ≥15, which does not exist |
| **§2.1 — B12 round-trip identity gate** | **ADOPTED AND SHIPPED** | GREEN at `f9719a2`: 13/13 pairs, 16/16 mutants. Reported *beside* R-H1 and deliberately not folded into it, because B12 postdates DESIGN §8's R-H1 sentence — declared in the prereg before the score so neither reading could be chosen after it |
| **§2.1 — B9 class-balance seal** | **ADOPTED AND SHIPPED** | `experiments/house_rules_prereg.json.frozen_numbers`: `b9_scored_half_majority_class_rate: 0.684211`, `b9_void_threshold: 0.784211`, `b9_declared_margin_points: 10`, all frozen before the run |
| **§2.1 — B5 harness-scope sentence** | **ADOPTED AND SHIPPED** | `prereg.b5_scope_sentence`, and it travels on the verdict: B5 evidences **NO WRITES OBSERVED UNDER THIS HARNESS**, never CANNOT WRITE |
| **§2.1 — R-H2's pre-committed reading** | **ADOPTED AND SHIPPED** | `result_gates.R-H2`: 0 of 30, `gates_nothing: true`, counted under the more generous of two readings so the number can only be too high, with the pre-committed reading in the artifact — approximately zero was expected, it is neither a failure nor evidence of demand, **and it may not be read either way now** |
| **§2.1 — STRANGER's re-scope onto DEMAND's population question** | **RECORDED ON THE PARK, schedules nothing** | ROADMAP-v0.25 §2.1's own sentence; procuring the population is latency-bound and licenses nothing by itself |

## 8. ROADMAP-v0.25 §3 — every carried lane, disposed

No v0.25 headline named any of these as a dependant, which is the standing
rule's own test. Each row is therefore **carries** or **parks**, with the
trigger it carries.

| §3 lane | disposition | note |
|---|---|---|
| The naming-layer question | **CARRIES**, and its own clause now fires: §1's `declare` row **shipped**, so the question has the second live surface §3 named. §3 already orders it re-examined at the v0.26 course rather than silently re-carried; that re-examination belongs to the parallel design course, not this lane | HANDLE's anti-vacuity lesson travels with it; HANDLEBAR parks behind it |
| STRANGER-GATE | **CARRIES as a prohibition, honored** | §3 above |
| PREMISE LEDGER | **CARRIES**, third cycle, trigger unfired | No design taking the necessity claim was written. COUNTERMODEL is now named as the missing constructor |
| CANARY-CURVE | **CARRIES** unchanged | Still blocked on an enumeration layer that does not exist |
| TOLL (CEILING routes with it) | **CARRIES** unchanged | Denominator still n=1; neither ORPHAN's denominator nor the log-probe ran |
| The cost ledger | **PARKS — ninth pass-over, recorded as a decision** | §4 above |
| ORPHAN | **CARRIES**, now with THIN-VERIFIER as the successor's mechanism | Unpark needs a design choosing which pinned dependency converts the most NEEDS-PROGRAM kinds. §10's re-read leaves the partition's NEEDS-PROGRAM count where it was |
| MIRROR FRAGMENT | **PARKS** on its own pre-gate | ≥300 renderable entries each carrying ≥2 non-boilerplate content lemmas, and ≥40 distinct content lemmas. Not measured this cycle |
| DIMENSION | **PARKS** unchanged | Its unpark is a rider on a cycle whose headline touches evaluation; HOUSE RULES touched admission and refusal |
| EARNED ASK | **BINDS, unscheduled** | §1 minted no questions, so nothing this cycle tested it |
| LAPSE | **PARKS** | No observation channel exists |
| SELF-SEED, UPSTREAM-PATCH, FOREIGN-SEAM, HANDLEBAR, DEMAND, the resolver's pre-emptive binding, the `conform` route's advertised-and-unused bindings, the G5-metric successor, TWO WITNESSES, open-English input, realization parameters as data, the `mathlib_head` budget, HOSTILE DICTATION, CROSSING, LONG CON, BITROT, C-V3, the v0.19–v0.24 catch-alls | **CARRY** unchanged | Triggers in ROADMAP-v0.23 §4.3; receipt chain `reports/design-direction-v0.19…25.json`. None named as a dependant |
| Ledger-first claims (L1–L13) | **CARRIES**, with the non-comparability sentence attached | No throughput readout ran; `experiments/throughput_tasks.json` unchanged |
| VERDICT, DEBT NOTES, COURIER, WORD OF HONOR | **PARKED** — adjudicated in §3 this rotation and **not reopened here** | ROADMAP-v0.22 §3.5's standing obligation was discharged at the roadmap and binds the next rotation |

## 9. Citations found stale and deliberately left alone

Two live inside sealed preregistration artifacts and are **not edited**,
because a stale citation inside a seal is a fact about the seal:

- `experiments/plain_input_prereg.json:127` quotes
  `docs/SPEC-chat-completions-skin.md:159-173` inside a frozen G4
  `clause_verbatim`. Today's correct range is `:401-412`.
- `experiments/session_ledger_prereg.json:219` says "§7's normative table";
  the normative line-grammar table is **§5** (`:399-415`). §7 is the
  generated capability sheet.

One more is recorded rather than fixed:
`experiments/foreign_voice_prereg2.json`'s `parser` row disagreed with the
tree before `156e94f` and disagrees after; it was out of that lane's scope
and stays out of this one's.

The eighteen wrong **line-number** citations that were fixable — all in
documentation — were fixed at `[TRIAGE-V25-LOWS]`, with the finding worth
keeping: every section-, paragraph- and anchor-form citation into the SPEC
verified **correct**. What rots is the citation that names a line.

## 10. What this lane hands forward

- The CR-P0 registry re-seal and the live cold re-read — the last
  scripts-affecting act of the lane, taken after everything above, and
  `156e94f`'s named discharge for the census it knowingly left stale.
- `[SUITE-GATE-V25]`, open, to be resolved at the frozen tip.
- The v0.26 outside design inquiry and its receipt, owned by the parallel
  design course.
- Two standing items: B3's `name_sweep` positive control's coupling to a tree
  property (filed at `[TRIAGE-V25-LOWS]`), and — from the v0.24 triage, still
  open — GUEST AXIOM's unadjudicated B6.
