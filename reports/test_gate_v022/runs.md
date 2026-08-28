# v0.22.0 complete-suite gate

One run, green on the first attempt. Main checkout frozen from launch to
verdict. 105 test modules, one process, `scripts/time_tests.py` over the
in-process-generated module list.

| run | tip | result | log |
|---|---|---|---|
| 1 | `85515e9` | **2,789 ran, OK (skipped=5), 22,307.8 s (6 h 12 m)** | `run1-green.log` |

Up from v0.21.0's 2,632 tests by this cycle's new modules —
`test_handles_census`, `test_onestep_census`, `test_erratum_probe`,
`test_cold_receipt` — whose assertions include the **absence** of the
un-built handle table, pilot, and Q60 (item 1's stop clause fired, so
those artifacts do not exist and tests prove it), and the cold-receipt
harness's tree-restore proof (the program renamed away during the run,
byte-restored after).

No red runs this cycle, unlike v0.20 (two reds, cross-lane pin drift) and
v0.21 (three reds, an amendment chain and an append-only proof). Both of
this cycle's item lanes were censuses rather than witnessed-module edits,
so the freeze discipline that caught those drifts had nothing to catch.

The five skips are the standing set (three environment skips plus
`test_transliteration`'s two slow-regeneration cases, hand-run green and
unchanged since v0.19).
