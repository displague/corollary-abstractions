# v0.21.0 complete-suite gate

Three runs, main checkout frozen from each launch to its verdict, all
receipts retained. 101 test modules per run, one process,
`scripts/time_tests.py` over the in-process-generated module list.

| run | tip | result | log |
|---|---|---|---|
| 1 | `de91713` | **2,632 ran, FAILED (failures=2, skipped=5), 21,126.9 s (5 h 52 m)** | `run1-red.log` |
| 2 | `d26cb04` | **2,632 ran, FAILED (failures=1, skipped=5), 21,498.3 s (5 h 58 m)** | `run2-red.log` |
| 3 | `7692220` | **2,632 ran, OK (skipped=5), 24,393.8 s (6 h 47 m)** | `run3-green.log` |

## Run 1's two failures — one missing amendment, adjudicated at `d26cb04`

`tests.test_conform_prereg` (E7 sweep) and `tests.test_conform_register`
(freeze check), one cause: the v0.21 session-ledger lane added
`free_names` to `scripts/evaluate.py`, rebuilt the throughput book for
the move, and never fed the **conformance** preregistration that froze
the same file. The freeze did its job one run later than it should have
been fed — v0.20's run-1 shape, one lane over. Repair: the
retirement-chain mechanics' third exercise — a dated RETROSPECTIVE
amendment (`conformance.prereg.amendment.evaluator-moved-2026-08-26`)
retiring the evaluator row with the run standing as measured under the
old digest, the successor pin in `exact_literals_prereg.json` (widened
by dated note into the terminal pin book for moved conformance-frozen
modules generally), and both guards re-aimed at the shared transitive
walk in `scripts/prereg_pins.py`.

## Run 2's one failure — the append-only proof met its second layer, adjudicated at `7692220`

`tests.test_conform_ce3_supplement`'s reversibility test proves the
prereg restores byte-for-byte when its amendment is deleted. It peeled
the `amendments` array but not the `retired_for_future_comparisons`
marker run 1's repair spliced onto the evaluator row — the mechanics
add **two** structures and the test modeled one. The append-only
property itself held; the test's model was one layer too shallow.
Re-aimed: removing both structures restores the sealed blob, and
anything else that moved still fails.

Run 3 green: up from v0.20.0's 2,326 tests by this cycle's five wholly
new modules (`test_conform_ce3_supplement`, `test_plain_input`,
`test_session_ledger`, `test_session_prereqs`, `test_witness`) plus
growth in existing ones. The five skips are the standing set.
