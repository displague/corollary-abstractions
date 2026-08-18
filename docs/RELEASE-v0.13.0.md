# v0.13.0 — coverage is not correctness

The cycle that reached all 24 registered questions and refused to ship the
resolver: fresh false positives rose from 3.0% to 3.4%, and “interest
accumulated without compounding” confidently bound continuous compounding.

Previous: [RELEASE-v0.12.0.md](RELEASE-v0.12.0.md) ·
Closed plan: [ROADMAP-v0.13.md](ROADMAP-v0.13.md) ·
Next: [ROADMAP-v0.14.md](ROADMAP-v0.14.md) ·
Triage: [TRIAGE-v0.13.md](TRIAGE-v0.13.md) ·
Findings: [DISCOVERIES.md](DISCOVERIES.md) ·
Blog: [coverage is not correctness](blog/coverage-is-not-correctness.md)

---

## The headline finding: all questions reached, one answer contradicted

**Before.** v0.12 shipped a conservative text resolver at 0.833 in-corpus
coverage and 0.030 false positives.  Its known misses looked morphological:
plural spellings and `euclid` versus `euclidean`.

**Now.** A preregistered surface-morphology candidate reached every row in a
third hand-authored holdout, then failed the conjunction that guarded it.

| measure | registered bar | result |
|---|---:|---:|
| reach coverage | ≥ 0.875 | **24/24 = 1.000, fired** |
| intended-target recall | ≥ 0.833 | **23/24 = 0.9583, fired** |
| wrong single BINDs | 0 | **1, missed** |
| title-only blind recall | < 1 and below resolver | **0.9167 vs 0.9583, fired weakly** |
| fresh OEWN false positives | ≤ 0.030 | **34/1000 = 0.034, missed** |

The title-only control's apparent 0.9167 includes one 14,571-id tie; it proves
only that literal title overlap is not perfect.  The wrong BIND is more useful:
word overlap cannot represent an explicit exclusion.  The implementation was
exactly reverted.  The experiment, miss, raw ledger, and scorer ship; the
resolver change does not.

**Demonstrate.** Read
`experiments/text_resolution_holdout3_result.raw.json` and
`experiments/false_positive_rate_f4.json`; run
`python -m unittest tests.test_coverage_holdout3` without rerunning either
spent scorer.

---

## Roadmap triage

### Shipped

- **Item 3, bounded P-LS6.** Resolver ASK candidates survive input turns.
  Explicit `narrow corpus|discipline|word|id` performs hard intersection;
  `cancel`, repeated-state `cycle`, and a visible four-hop `hop_ceiling`
  terminate without guessing.  New queries and registered commands keep their
  ordinary routes.

### Shipped as negative evidence

- **Item 1.** Coverage rose to 1.000, correctness/precision missed, candidate
  reverted.
- **Item 4.** A harder grounded-admission foil leaves balanced accuracy at
  0.5052 / 0.5104.  The gate parks.  Because exact executable choices were not
  committed before scoring, this is explicitly exploratory evidence, not a
  registered one-shot result.

### Partial and parked

- **Item 2.** A1 fired narrowly: 16 ASK among all 62 registered in-corpus
  questions = **0.2581**.  The first artifact reported 0.2712 by silently
  excluding three PASS outcomes; review corrected and retained both numbers.
  A2/A3 were not scored because the spent holdouts never froze continuations
  or intended retained readings.  A4 was not implemented.
- **Item 5.** W1–W3 remains designed but unscored; no independently motivated
  fourth formal source exists, so it parks rather than floating another cycle.

## What changed, per area

### ASK became session state

**Before.** The prompt read one line; an ASK printed candidates and died with
the process.

**Now.** The exact candidate identifiers persist inside one `CoreSession`.
Clarification is typed and closed-form, not a ranker: zero matches preserve the
ASK, ties remain ASK, and a singleton is returned only with title/meaning text
quoted from the corpus.  Pending state is session-local.

**Demonstrate.** Pipe:

```console
double factorial
narrow word recursive
```

into `python scripts/harness.py --offline`, or run
`python -m unittest tests.test_context_narrowing tests.test_harness_line`.

### Ambiguity was measured before being sold

**Before.** ASK examples existed, but nobody knew whether they were a curated
edge case.

**Now.** A1's reviewed denominator includes every registered in-corpus query:

| set | registered | BIND | ASK | PASS | ASK rate |
|---|---:|---:|---:|---:|---:|
| development | 28 | 21 | 7 | 0 | 0.2500 |
| holdout 1 | 18 | 9 | 6 | 3 | 0.3333 |
| holdout 2 | 16 | 13 | 3 | 0 | 0.1875 |
| **pooled** | **62** | **43** | **16** | **3** | **0.2581** |

That is enough to retain the machinery and too weak to imply Buffalo-class
understanding.  Holdout 2 misses by itself.

**Demonstrate.** `python scripts/measure_ambiguity.py --out <temporary.json>`
reproduces `experiments/ambiguity_rate.json`; the committed artifact pins all
query, resolver, matcher, and corpus inputs.

### The discipline refused an evaluator

**Before.** A2 said a legal follow-up should halve ASK candidate sets, but the
holdouts contained only initial lines.

**Now.** Review found that authored-after-the-fact follow-ups could select
favorable candidates, omit hard rows, or halve while discarding the intended
reading.  No aggregate was run.  The scorer and rows do not ship.  The next
design fixes the denominator before another implementation exists.

**Demonstrate.** See `experiments/ANALYSIS.md`, “A2 protocol refused before
scoring,” and [DESIGN-when-to-ask.md](DESIGN-when-to-ask.md).

### Groundedness noticed the edit and could not admit

**Before.** v0.12 found groundedness-at-all separated real corpora from random
trees and proposed it as a possible admission signal.

**Now.** Against paired, locally plausible one-head edits it is effectively
chance: balanced accuracy **0.5052 / 0.5104**, paired accuracy **0.6068 /
0.5859**.  A small mean margin (+0.0288 / +0.0245) notices the edit but rejects
too few foils.  Executable chronology makes this exploratory, and the gate
parks without tuning.

**Demonstrate.** `python scripts/measure_grounded_admission.py --check` and
`python -m unittest tests.test_grounded_admission`.  Source provenance uses
canonical-LF hashes so Windows and fresh LF checkouts agree.

## Discoveries of the cycle

From [DISCOVERIES.md](DISCOVERIES.md): ambiguity is real but narrow; a
resolver can reach the whole set and still be wrong; negative contrast is not
word overlap; groundedness can notice a local edit without becoming an
admission decision.

## Resolved from BACKLOG

- P-LS6's one-line surface debt — **paid for resolver clarification**.
- The location of the slow gate — **measured**: one blind-control test costs
  5,619.8 seconds, while fixture/runner time costs roughly another 4,700.
- Three folklore explanations for gate cost — **retracted**.  The actionable
  timing and sampling questions remain.

## Honest limits carried forward

- Reach is not correctness.  The shipping resolver remains v0.12's 0.833 /
  0.030 point.
- P-LS6 is not general memory, implicit conversation, story continuation, or
  arbitrary prose context.  Only explicit resolver clarification persists.
- A2/A3/A4 are unadjudicated.  No favorable development probe is promoted to
  a result.
- Grounded admission is exploratory and parked; its ledger is reproducible but
  its executable protocol did not predate scoring.
- W1–W3, both rankers, HTTP skin, domain expansion, and deeper proof search are
  parked without dependants.
- A passing Python test is not a Lean proof.
- The complete suite passed at `04c4648`: **1,282 tests across all 66 test
  modules, 12 skips, zero failures**.  Five measured shards took 3h46m35s of
  parallel wall time; the slowest ran 286 tests in 13,577.098s.  The
  [gate ledger](../reports/test_gate_v013.json) preserves exact assignments,
  timings, exit codes, and the two excluded failed launcher/gate attempts.

## Assets

No new checkpoint and no duplicate JSON uploads.  `data/` and model-training
code are unchanged from v0.12.0; this cycle changes resolver/session code and
tracked measurement tooling.  The checkpoints attached to v0.5.0 and v0.6.0
remain the applicable model assets.  The new raw ledgers live in Git, where a
clone already receives them.

## Reproduce

From a fresh clone on Windows PowerShell:

```powershell
$env:PYTHONIOENCODING='utf-8'
python scripts/check_regeneration.py
python scripts/validate_nodes.py
python scripts/match_signatures.py --write-report reports/signature_matches.json
python scripts/specialize.py --write-report reports/specializations.json
python scripts/measure_compression.py --write-report reports/compression.json
python scripts/fetch_sources.py --fetch wordnet-2025-json
python scripts/ingest_wold.py reach
python -m unittest discover -s tests
```

Do not regenerate spent conversational scores as new results.  Their committed
raw ledgers and provenance tests are the release record.
