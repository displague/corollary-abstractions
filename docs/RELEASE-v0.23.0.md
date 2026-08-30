# v0.23.0 — the inbound turn had no population

This cycle scheduled a person-supplied premise and a machine-checked
implication. It got three **construction findings** instead, each against a
stop clause frozen before the instrument existed.

- **The sealed questions are not about the speakable remainder.** Of 21
  non-exhaust maintainer questions recast against the voice's 2,313 covered
  statements, **0** named a unique covered id. Nine more were exhaust by
  authorship. The 20 person-wrong corrections were **BLOCKED_NO_LOG**: the
  parked CROSSING probe was named and never sealed, and the draw refused to
  invent the pool.
- **The native voice is not an echo instrument.** ECHO's population is two
  disjoint universes (native **8,584**, second voice **2,313**, overlap
  **0**). Only the second voice has an external Lean adjudicator and an
  import-disjoint reader. The gate read **STOP_BEFORE_PILOT**: **0/50**
  reserve and **0/500** registered items rendered. No collision result
  exists to license GUEST AXIOM's ask-arm.
- **The recorded answering turns did not regress.** R-NF replayed **220**
  recorded answering turns (`160 solved + 60 found`) and published
  **0/220** rendered-answer digest regressions, with hostile controls that
  can go red (exact plants 2/2, shape-only 0/2, always-changed 2/2 and
  220/220 false positives on identical self-pairs). Zero is a count for
  this window, not a proof that answers cannot regress.

The implication object — `experiments/guest_dispositions.json`, fifty
sessions, a 40% elaboration floor, a person-wrong score — **does not
exist**. B3 already licensed that outcome: if the restricted population is
below 15, the lane reports the recast-yield census rather than a rate.

**Links** — previous release: [v0.22.0](RELEASE-v0.22.0.md) · closed plan:
[ROADMAP-v0.23](ROADMAP-v0.23.md) · next plan:
[ROADMAP-v0.24](ROADMAP-v0.24.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the inbound turn had no population](blog/the-inbound-turn-had-no-population.md)
· forward design: [DESIGN-protocol-uptake](DESIGN-protocol-uptake.md)

## The headline finding: the questions we had are not about the part that can speak

**Before.** [The previous chapter](blog/the-library-that-had-no-names.md)
ended on a wager paid in names: of 12,777 statements, 417 carry a typable
handle, and of the 9,048 the engine can consume in one step, 125 carry one.
It cleared a path: GUEST AXIOM would not need names. It would run on the
**2,313** statements the system can already speak in verified English, with
ECHO going first to ask whether a spoken sentence determines its statement.

**Now.** G-P0 recast the 30 sealed maintainer questions
(`experiments/plain_question_set.json`) by exact membership of statement
ids their `why` already named, against the same covered set the voice
already measured (`scripts/measure_foreign_voice.py:covered_rows`). The
resolver was not consulted. Result, from
`experiments/guest_hypotheses.json`:

| stratum | count |
|---|---:|
| exhaust-prior → `nameless_probe` by authorship | 9 |
| non-exhaust, unique covered id | **0** |
| non-exhaust, no unique covered id → `nameless_probe` | 21 |
| maintainer_correction | **0** (`BLOCKED_NO_LOG`) |

The named ids (`graphtheory.enumeration.complete_graph_edge_count`,
`programming.factorial.iterative`, …) are register-blocked or never
oracle-accepted. The 2,313 is 99.87% `lean_workbook`. The questions a
maintainer wrote *about this corpus* are not questions *about the 2,313*.
That is G-P0's authorship contamination made mechanical, not a comment.

ECHO, scheduled first, did not rescue the inbound turn. Native 8,584 and
second 2,313 are disjoint; native B3/B4 miss; **0/50** and **0/500**
rendered (`experiments/echo_population_audit.json`).

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/guest_hypotheses.json',encoding='utf-8')); \
    y=d['counts']['recast_yield']; print(d['correction_arm'], y['landed_in_covered_set'], \
    y['non_exhaust_questions'], y['exhaust_questions'])"
BLOCKED_NO_LOG 0 21 9
```

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/echo_population_audit.json',encoding='utf-8')); \
    print(d['construction_gate'], d['findings'][0]['evidence']['observed'])"
STOP_BEFORE_PILOT {'native_served': 8584, 'second_voice_served': 2313, 'statement_id_overlap': 0, ...}
```

## Roadmap triage

| item | outcome |
|---|---|
| **§1 GUEST AXIOM** | **SHIPPED as the recast-yield finding.** 0/21 into the 2,313; person-wrong BLOCKED_NO_LOG; no 50 sessions; no implication object. B3's alternative fired. |
| **§1 G-P1 fence** | **SHIPPED.** Planted write under a throwaway `data/` tree caught 1/1. Real corpus not the plant target. |
| **§2 ECHO** | **SHIPPED as construction stop.** B1 FIRES; native B3/B4 miss; 0/50 and 0/500 rendered. No collision result. |
| **§3 R-NF** | **SHIPPED.** 0/220 rendered-answer digest regressions; controls 2/2, 0/2, 2/2+220/220. Two live pins moved and are disclosed. |
| **§3 HANDBACK** | **PARKED** for v0.24. No collision result to attach a separator to. Always-conditional never-ask is the recorded B5 fallback. |
| **PROTOCOL UPTAKE** | **Reviewed design, not scheduled.** v0.24 incumbent against STRANGER-GATE. Receipt `reports/design-direction-v0.24.json`. Reaffirmed, not re-run, at this rotation. |

Session-level GUEST AXIOM gates (B1 50/50 quarantine, elaboration-pilot
floor, person-wrong α=0.05, no-vacuous-CONDITIONAL) **did not run and are
not claimed**. Publishing 50/50 over an empty remainder would be the
rate-over-nothing B3 forbids.

## What changed, per area

### Guest-axiom construction

**Before.** A design promised fifty inbound sessions on the 2,313.

**Now.** The drawing rule was committed first. The draw measured a zero
yield and an absent correction log, and stopped.

**Demonstrate.** `experiments/guest_axiom_draw_rule.json` is a strict git
ancestor of `experiments/guest_hypotheses.json`
(`tests/test_guest_axiom_draw.py`).
`scripts/guest_quarantine.py` / `tests/test_guest_quarantine.py` catch a
planted write 1/1.

### Echo construction

**Before.** A design promised a code-disjoint reader over “the voice.”

**Now.** There are two voices. Only one is instrumentable. The run stopped
before sampling.

**Demonstrate.** `experiments/echo_population_audit.json`,
`construction_gate: STOP_BEFORE_PILOT`.

### Recorded-answer regression

**Before.** ERRATUM measured 0 real flips over 410 turns in a zero-growth
window. R-NF is the regression-only residue: same journals, answering
turns only, exact rendered-answer bytes.

**Now.** 0/220 digest regressions. The comparator choice is visible: a
shape-only control misses both plants; an always-changed control flags
the entire self-pair set.

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/no_flip_census.json',encoding='utf-8')); \
    print(d['outcome']['sentence']); print(d['controls']['exact_detected'], \
    d['controls']['shape_only_detected'], d['controls']['always_changed_detected'])"
0/220 rendered-answer digest regressions in this recorded window
2 0 2
```

### Codex-compatible surface (this cycle's product work)

**Before.** Codex CLI 0.147+ accepts only the Responses wire API; the skin
exposed chat-completions and 404'd `/v1/responses`.

**Now.** `scripts/serve_chat.py` maps the text-only Responses request and
SSE lifecycle onto the existing engine. The durable launch is in
`README.md`. The first ordinary turn (`hello`) is still an ungrounded
proposition — that observation is the v0.24 design trigger, not a
capability.

**Demonstrate.** The README durable `codex.cmd` line against
`http://127.0.0.1:8377/v1` with `wire_api=responses`.

### Forward design

**Before.** No reviewed v0.24 direction.

**Now.** [DESIGN-protocol-uptake](DESIGN-protocol-uptake.md), status
**design only, reviewed; not scheduled.** Three-series receipt
`reports/design-direction-v0.24.json`. Architecture review forced a third
profile `corollary/protocol`, an honest (not Latin-rectangle) fixture
table, and B4 re-fit on the runtime. This rotation **reaffirms** that
document as the v0.24 incumbent; it does not re-run the isolated series.

## Discoveries of the cycle

Quoted, not duplicated — see [DISCOVERIES](DISCOVERIES.md):

- A served voice is not one instrument just because both outputs are English.
- 0/220 rendered-answer digest regressions in the recorded window.
- G-P0 recast yield 0/21 (ANALYSIS; BACKLOG).

## Resolved from BACKLOG

Shipped-as-finding this cycle and pruned from the *actionable* list only
where the work is done: ECHO's native-instrument gap remains filed (it is
the unpark). CROSSING's missing log remains filed (G-P0 named it). New
parks at cycle close: HANDBACK for v0.24; GUEST AXIOM inbound slice behind
a new sealed population.

## Honest limits carried forward

- GUEST AXIOM did not serve an implication. Do not read “the person
  finally speaks” from the v0.22 blog as having happened.
- ECHO did not produce a collision table. Always-conditional, never-ask
  is the B5 fallback.
- Person-wrong is unfilled, not UNDERPOWERED-from-a-sample.
- R-NF zero does not license future stability. Two live pins moved
  (`rendering_module_digests`, `capability_sheet_digest`).
- Protocol uptake is not implemented. Kernel `hello` remains refusal.

## The suite at the tip

**Green on run 2: 2,852 tests, OK (skipped=5), 32,646.0 s (9 h 4 m) at
the frozen tip `867ad5c`.** Receipts in `reports/test_gate_v023/`
(`run1-red.log`, `run2-green.log`, `runs.md`).

Run 1 at the rotation tip `5984f27` was red: 2,851 ran, FAILED
(failures=1, errors=11, skipped=5), 32,932.9 s (9 h 9 m). The failure
was a stale CR-P0 seal (`program_tree_files_scanned` 178→183; kinds
stayed 19). The eleven errors were a growing `unittest -v` log inside
`working_tree_digest`. Both are retained. The registry was re-sealed
at `4243a98`; the live cold reading was regenerated at `867ad5c`
(1,249-file clone-shaped digest). Run 2 used `time_tests.py` with the
log outside that digest.

The five skips are the standing set. Up from v0.22.0's 2,789 by this
cycle's new modules (`test_guest_axiom_draw`, `test_guest_quarantine`,
`test_echo_population_audit`, `test_no_flip_census`), growth in
`test_serve_chat`, and the harness `EXECUTABLE_KIND` guard.

## Assets

No new checkpoint, and the existing ones are not re-shipped. `data/` was
not the plant target for G-P1 and no training data changed this cycle.
Measurement ledgers are committed in-repo:
`experiments/guest_hypotheses.json`,
`experiments/echo_population_audit.json`,
`experiments/no_flip_census.json`.

## Reproduce

From a clone at this tag:

```
PYTHONIOENCODING=utf-8 python -m unittest tests.test_guest_axiom_draw tests.test_guest_quarantine tests.test_no_flip_census
PYTHONIOENCODING=utf-8 python -c "import json; print(json.load(open('experiments/guest_hypotheses.json',encoding='utf-8'))['counts']['recast_yield']['landed_in_covered_set'])"
```

`ingest_wold.py reach` **ran, exit 0**: WordNet reach **1,394/1,460 =
95.5%** against the pinned gitignored archive present on this machine,
byte-identical to the committed `experiments/wold_reach.json`. A
contributor without the archive gets the refusal, which is *cannot
verify*, never *skipped*.

`[SUITE-GATE-V23]` is resolved: run 2 green at `867ad5c`, receipts in
`reports/test_gate_v023/`. The rotation placeholder above is closed
with those numbers, not carried.
