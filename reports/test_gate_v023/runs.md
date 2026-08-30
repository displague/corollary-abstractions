# v0.23.0 complete-suite gate

Two runs. Run 1 red, run 2 green. Main checkout frozen from launch to
verdict per run. Run 1 used `python -u -m unittest discover -s tests -v`
on the rotation tip; run 2 used `scripts/time_tests.py` over 109 modules,
with the log under `.runtime/` so `working_tree_digest` did not see it
grow.

| run | tip | result | log |
|---|---|---|---|
| 1 | `5984f27` | **2,851 ran, FAILED (failures=1, errors=11, skipped=5), 32,932.9 s (9 h 9 m)** | `run1-red.log` |
| 2 | `867ad5c` | **2,852 ran, OK (skipped=5), 32,646.0 s (9 h 4 m)** | `run2-green.log` |

## Run 1 (red)

Two independent causes, both scored rather than absorbed.

**The CR-P0 registry census was stale.**
`test_cold_receipt.TheCensusRecomputes.test_the_seal_and_counts_recompute_from_the_committed_tree`
compared committed seal `9aa301b76d026065…` to live `e8fabc6f290c94de…`.
Kinds stayed 19, sites 37, excluded 10. `program_tree_files_scanned`
moved 178→183 (the five scripts this cycle added:
`echo_population_audit`, `echo_reparse`, `guest_axiom_draw`,
`guest_quarantine`, `no_flip_census`) and three `serve_chat.py`
exclusion line-ranges shifted by seven. The rule was not amended; the
artifact was not re-sealed at rotation. Re-sealed at `4243a98` with the
writer; ANALYSIS recall prose followed the probe (151/135 → 156/140;
admitted 16 unchanged). The live `cold/census_run2.json` pin was
regenerated at `867ad5c` (1,249-file clone-shaped digest; partition
unchanged).

**A growing suite log was inside `working_tree_digest`.** Eleven
`WriteStageTestCase.tearDownClass` errors, one per subclass, all
`a WRITE-staging test changed the repository working tree`. The log
`reports/test_gate_v023/run1.log` is hashed; `unittest -v` appends every
result. Confirmed after the run: a static log leaves the digest equal;
appending one byte moves it. v0.22 avoided this because `time_tests.py`
is quiet during WRITE. This is process contamination, not a WRITE
escape.

## Run 2 (green)

Same standing five skips (three environment skips plus
`test_transliteration`'s two slow-regeneration cases, hand-run green
and unchanged since v0.19). One more test than run 1: the harness
`EXECUTABLE_KIND` guard added after run 1 crashed `run_scramble`. Up
from v0.22.0's 2,789 by this cycle's new modules —
`test_guest_axiom_draw`, `test_guest_quarantine`,
`test_echo_population_audit`, `test_no_flip_census` — growth in
`test_serve_chat`, and that one harness guard.
