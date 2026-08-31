# Roadmap v0.24 — an ordinary turn is an uptake, not a keyword

v0.23 scheduled a person-supplied premise and got three construction
findings: the sealed questions are not about the speakable 2,313 (G-P0
**0/21**), the native voice is not an echo instrument (ECHO **STOP_BEFORE_PILOT**,
**0/50** and **0/500**), and the recorded answering turns did not
regress (R-NF **0/220**). The inbound implication object does not exist.
B3 licensed that stop.

This cycle starts from the *live* failure the last ordinary turn already
showed, and from a design written before this roadmap: `hello` on the
shipped Codex-compatible surface was treated as an ungrounded
proposition. [DESIGN-protocol-uptake](DESIGN-protocol-uptake.md) is the
reviewed incumbent. The v0.24 course must still **adjudicate** it
against STRANGER-GATE's prohibition. This document does not silently
promote the incumbent to a scheduled capability.

**Links** — previous plan: [ROADMAP-v0.23](ROADMAP-v0.23.md) · previous
release: [RELEASE-v0.23.0](RELEASE-v0.23.0.md) · incumbent design:
[DESIGN-protocol-uptake](DESIGN-protocol-uptake.md) · receipt:
`reports/design-direction-v0.24.json`.

## 1. Headline — PROTOCOL UPTAKE, if the course keeps it

The course (not this file) decides whether protocol uptake outranks
STRANGER-GATE. If it does, the slice is the reviewed design: a third
served profile `corollary/protocol`, an honest 8×4 context/corpus table
whose view-ceilings are computed at U-P0, B4 re-fit on the runtime, ASK
on extra lookup keys disjoint from the 32, protocol corpus **outside**
`data/`. Kernel line grammar and conversation request grammar stay
sealed.

If STRANGER-GATE wins, this item parks with the prohibition trigger
intact and protocol uptake remains a reviewed design behind that
perimeter.

**Acceptance if scheduled:** U-P0/U-P1 construction order in the design;
B1–B6 and B8–B10 for R-U1; B7 separately licensed or UNTESTED. A
Latin-rectangle balance, a path on `corollary/kernel` or
`corollary/conversation`, or protocol nodes under `data/` is a
construction refusal.

### 1.1 The course's selection — recorded as a decision (2026-08-31)

**PROTOCOL UPTAKE is scheduled as the v0.24 headline.** The adjudication
against STRANGER-GATE is not a ranking between two schedulable items,
because STRANGER-GATE's trigger is a **prohibition, not a candidacy**: it
MUST run before any untrusted stream reaches the write gate
(ROADMAP-v0.23 §4.3). The recorded question is therefore whether this
slice opens such a stream. It does not, and that is checkable rather than
asserted:

- **The slice grants no authority.** DESIGN-protocol-uptake §5 forbids
  any protocol move from authorizing `WRITE`, process creation,
  filesystem, shell, or network access; B3 requires `authority_delta`
  present-and-empty on every ASK/REFUSED path as a plaintext receipt
  field, and B8 plants a prompt string naming `WRITE`/Python/shell
  capabilities and requires zero process starts, zero stage records,
  zero data-tree byte changes. The utterance stream stays untrusted and
  reaches only the exact-lookup witness channel, never the write gate.
- **Only this candidate has a fired, observed trigger.** The `hello`
  turn on the shipped Codex-compatible surface is a live ordinary-turn
  failure that existed before any design answered it. No incumbent's
  unpark trigger fired this cycle: the naming-layer question has
  candidate material but no chosen mechanism; PREMISE LEDGER's
  necessity claim was explicitly not taken at v0.23; CANARY-CURVE
  waits on an enumeration layer that does not exist; TOLL waits on
  ORPHAN's denominator.
- **The prohibition is honored in writing, here.** No untrusted
  execution or write stream opens in v0.24. STRANGER-GATE keeps its
  prohibition trigger intact and parked; the first future design that
  would open such a stream (DEPUTY is the named next asker,
  DESIGN-protocol-uptake §11) is blocked until STRANGER-GATE has run.

Declined dispositions, one per incumbent, so this selection is a
decision and not a preference:

| incumbent | disposition this course |
|---|---|
| **STRANGER-GATE** | **Not displaced, not run.** Prohibition trigger intact; nothing in this cycle's slice reaches the write gate (grounds above). It remains the mandatory precursor to any execution/write design |
| **The naming-layer question** | Carried to the v0.25 course unchanged; no dependant named this cycle. Candidate material (name-derivation from verified renderings; the ~223.5 s S3 term store) stands unspent |
| **PREMISE LEDGER** | Carried unchanged, capability-class; its necessity claim is again not taken. LOADBEARING stays folded into it |
| **CANARY-CURVE** | Carried unchanged, instrument-class; still blocked on the enumeration layer |
| **TOLL** (with CEILING routed to it) | Carried unchanged; instrument (cold-census harness) and denominator path (ORPHAN) recorded, denominator still n=1. The cost ledger enters its **eighth** parked cycle |
| **GUEST AXIOM inbound / ECHO amendment / HANDBACK (§2)** | Not named as dependants; all three stay parked behind their §2 triggers |

The §1 slice is therefore live, under its own acceptance line: U-PRE →
U-P0 → U-P1 construction order, B1–B6/B8–B10 for R-U1, B7 separately
licensed or UNTESTED, and the three named construction refusals.

## 2. Prerequisites that are not this cycle's headline

These do not start unless §1's course names them as dependants.

- **GUEST AXIOM inbound slice.** Unpark only with a drawing rule
  committed before a draw whose non-exhaust targets sit in
  `measure_foreign_voice.covered_rows` (or a dated amendment of that
  constructor), **and** an externally-sourced correction log whose
  commit is an ancestor of that draw. Do not invent
  `experiments/crossing_corrections.json` in the draw commit.
- **ECHO native-instrument amendment.** Unpark only with a dated
  amendment that either supplies a native external adjudicator and a
  disjoint reader, or scopes the collision claim to the second voice
  alone and says so. The 0/50 and 0/500 denominators stay.
- **HANDBACK.** Unpark when GUEST AXIOM has a restricted population ≥15
  **and** a collision or separator result licenses the ask-arm.

## 3. Carried, with dependants named

The naming-layer question, STRANGER-GATE, PREMISE LEDGER, CANARY-CURVE,
TOLL/ORPHAN, and the rest of ROADMAP-v0.23 §4.3 carry with the same
triggers unless the v0.24 course names a dependant. An item carried
here with no dependant is parked in [BACKLOG](BACKLOG.md).

**PROTOCOL UPTAKE does not displace STRANGER-GATE's prohibition.** No
untrusted execution or write stream opens this cycle unless
STRANGER-GATE has run.

## 4. Release gate (draft)

v0.24 is ready only if the course's selection is recorded with every
declined disposition; the selected slice meets its own construction
stops; STRANGER-GATE's prohibition is honored or discharged in writing;
`check_report_regeneration.py` verdicts are in the notes; the full
suite is green on a frozen tip; `[SUITE-GATE-V24]` is resolved.
