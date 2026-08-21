> **CLOSED — historical triage record for v0.13.** Since v0.14 the roadmap
> triage lives inside the release notes ([RELEASE-v0.14.0.md](RELEASE-v0.14.0.md)
> and later); nothing here is current. Suite counts, gate readings, and
> open-friction lists below are as-of-v0.13 facts; several were later
> discharged (see [BACKLOG.md](BACKLOG.md) and later release notes).

# v0.13 release triage — coverage is not correctness

Written before the release notes so the calls are visible as calls.  The
forward design forced by the cycle is
[DESIGN-when-to-ask.md](DESIGN-when-to-ask.md), committed before the release
blog.  It does not reuse the spent wrong-BIND row as evaluation data.

## 1. Release gate

| gate | status |
|---|---|
| A1 measured first | **MET** — reviewed denominator 16 ASK / 62 registered in-corpus questions = **0.2581**, narrowly above 0.25 |
| third conversational holdout + fresh precision arm | **MET AS A REJECTED TRADE** — reach 24/24, target recall 23/24, one wrong BIND, F4 34/1000 = **0.034** against the 0.030 ceiling; resolver reverted |
| P-LS6 shipped or context parked | **MET** — bounded hard-intersection clarification shipped; A2/A3 parked unscored because continuations/readings were not frozen |
| grounded admission designed and tested or parked | **MET, PARKED** — harder foil measured; exact executable was not frozen before scoring, so result is exploratory; balanced accuracy 0.5052 / 0.5104 |
| every carried lane has a dependant or parks | **MET** — W1–W3 parks pending an independently motivated fourth source; no floating ranker carries |
| evidence names winners, losers, controls | **MET** — committed ledgers preserve all arms; no upload asset or checkpoint changed; §5 |
| complete suite green | **MET** — 1,282 tests across all 66 modules, 12 skips, zero failures at `04c4648`; [receipt](../reports/test_gate_v013.json) |

### 1.1 What the notes may claim

True: morphology reached every third-holdout query.  True: it also raised the
fresh false-positive rate and made one confident contradictory bind, so it did
not ship.  True: ASK is common enough to retain, but only by 0.0081 above its
registered line.  True: the prompt can persist and explicitly narrow an ASK,
cancel it, and terminate on a named cycle or four-hop ceiling.

False: the context aggregate fired.  It was never run; review rejected its
retroactive continuation rows.  False: groundedness-at-all is a preregistered
admission result.  Only its prose thresholds preceded scoring; executable
choices and ledger landed together.  False: 24/24 reach means 24 correct
answers.

### 1.2 Provenance corrections caught before release

- The first A1 artifact omitted three PASS outcomes from the promised
  denominator.  Review changed 16/59 = 0.2712 to **16/62 = 0.2581** and kept
  both numbers in the record.
- The compact holdout-3 ledger initially displaced the full blind candidate
  arrays.  The original staged Git blob was recovered without rerunning the
  spent scorer and now ships as the canonical raw artifact.
- Two compact-ledger digests described stale CRLF working copies; integration
  corrected them to the LF bytes Git stores.
- Grounded-admission source digests also depended on checkout newlines.
  Canonical-LF hashing and LF attributes now make a fresh checkout reproduce
  the metadata; the scored rows did not change.

These are release work, not embarrassing footnotes: a tool that cannot audit
its own evidence has not earned the claim it prints.

## 2. Roadmap outcomes

- **Item 1 — shipped as a negative.** The preregistration, implementation,
  raw/compact ledgers, F4 ledger, scorers, and tests ship.  The resolver change
  is exactly reverted.
- **Item 2 — partial, then parked.** A1 fired narrowly.  The live candidate
  object and corpus restatement mechanism exist.  A2/A3 are unadjudicated and
  A4 is unimplemented; review stopped an oracle-selectable scorer before run.
- **Item 3 — shipped, bounded.** P-LS6 persists resolver ASK state only.  It
  is not general conversational memory or story continuation.
- **Item 4 — exploratory negative, gate parked.** G1/G2 missed, G3/G4 fired,
  but executable chronology downgrades the result.  No threshold tuning.
- **Item 5 — designed, unscored, parked.** W1–W3 still needs a fourth source
  authored for an independent reason.

## 3. Drift audit against v0.11 and v0.12

| prior goal or debt | disposition in v0.13 |
|---|---|
| conversational coverage | measured on a third holdout; candidate rejected on precision/correctness |
| multi-turn P-LS6 | **SHIPPED**, narrowly for resolver clarification |
| ambiguity/context | A1 measured; A2/A3/A4 honestly parked rather than inferred |
| grounded admission | harder foil attempted; gate parked after chance-level exploratory result |
| W1–W3 predictor | parked; no fourth source and no dependant |
| write-recovery / budget-edit rankers | remain parked; no fit named |
| `specialize.py` general index, proof depth, physics/affect/visual, HTTP skin, Open-English authoring | remain parked; none serves the next headline |

The product-surface debt did not regress: the prompt still answers one line and
now consumes more, but only explicit `narrow`/`cancel` syntax touches pending
resolver state.  “Multi-turn” is not inherited as “general chat.”

## 4. What carries into v0.14

Only work named by [ROADMAP-v0.14.md](ROADMAP-v0.14.md) carries:

1. the executable preregistration skeleton and 48-row fresh clarification
   holdout required by `DESIGN-when-to-ask.md`;
2. exact negative-contrast representation under that frozen grammar;
3. a fresh OEWN precision arm and candidate-budget blind baseline;
4. measured gate receipts and better shard planning.

Grounded admission, W1–W3, both rankers, and domain expansion park in
[BACKLOG.md](BACKLOG.md) until a future headline names a dependant.

## 5. Assets

No new checkpoint.  The cycle changes resolver/session code and measurement
tools, not training data or model architecture.  Git-tracked JSON ledgers are
already distributed by the repository and are not duplicated as release
uploads.  The v0.5.0 and v0.6.0 checkpoint assets remain the latest applicable
model artifacts.

## 6. Complete-suite gate

The accepted gate froze exact tip `04c4648` into five detached worktrees.
Module placement began with v0.12's measured assignment, put the four new fast
modules on the previously light shard, and isolated
`test_corpus_analogy_split` from its 20 companions.  Every one of the 66
`test_*.py` modules appears exactly once: no duplicate, missing, or extra
assignment.

| shard | modules | tests | unittest seconds | skips | result |
|---:|---:|---:|---:|---:|---|
| 0 | 21 | 454 | 180.221 | 3 | OK |
| 1 | 1 | 45 | 8,275.830 | 0 | OK |
| 2 | 24 | 328 | 720.080 | 9 | OK |
| 3 | 10 | 169 | 3.914 | 0 | OK |
| 4 | 10 | 286 | 13,577.098 | 0 | OK |
| **total** | **66** | **1,282** | — | **12** | **OK** |

The five receipts span 13,594.690 seconds of parallel wall time (3h46m35s);
their individual runner times sum to 22,775.089 seconds.  The committed
[gate ledger](../reports/test_gate_v013.json) records the exact SHA, module
lists, starts, runner times, unittest times, exit codes, and excluded attempts.
The release-tag delta after `04c4648` is documentation and this receipt only.

Two earlier attempts are explicitly invalid.  Windows PowerShell 5 treated
native stderr as terminating under the first receipt script's `Stop` policy,
so it could not produce reliable logs and receipts.  A corrected PowerShell 7
run at `39e06bc` then honestly failed the byte-identical A1 artifact test:
P-LS6 had changed only the stateless resolver's module narrative, so its bytes
no longer matched A1's registered provenance.  The measured resolver blob was
restored at `04c4648`, its focused artifact test passed, and **all five shards
were rerun**.  No result from either invalid attempt is counted.
