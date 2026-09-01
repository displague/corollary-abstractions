# [SUITE-GATE-V24] — the full-suite gate for v0.24.0

The tag's gate is one complete `unittest discover -s tests -v` at the
frozen tip, logged OUTSIDE the hashed tree (`.runtime/`, the v0.23 run-1
lesson) and retained here. Four launches; one red with receipts, one
near-green killed by the operator, one killed at startup, one green.

## Run 1 — RED by exactly three, all instrument

- tip `ac45507`, 2,986 tests in 22,180.8 s (6 h 10 m):
  `FAILED (failures=2, errors=1, skipped=5)` — `run1-red.log`.
- **R-NF `replay_path` freeze-group drift**: AMD-3's registered edit to
  `scripts/serve_chat.py` changed a file the no-flip prereg had frozen.
  The fix is the mechanic the prereg pins already owned for rows,
  extended to freeze groups: a dated amendment plus
  `retired_for_future_comparisons`, never an in-place edit
  (`experiments/no_flip_prereg.json`, `scripts/no_flip_census.py`).
- **`--allow-dirty` rehearsal counted as registered**:
  `run_protocol_gates.py` computed `registered_before_the_run` from tree
  state alone; under the flag it now forces `false` — a rehearsal is
  never a registered run.
- **B7-pending assertion frozen in pre-artifact shape**:
  `test_protocol_gates.py` demanded `gates_pending == ["B7"]` after B7
  had in fact run; the expectation is now conditional on the committed
  B7 artifact's existence.

All three fixed in `cf5cba5` \[GATE-FIX-V24\]; the fixes moved
receipt-marked line ranges, so the CR-P0 registry was re-sealed
(`d3d9bdc6…`, commit `be21a40`) and the cold reading re-attested against
the committed seal (`d1e37b9`) before any re-run.

## Run 2 — killed by the operator, ~35 tests short of a verdict

- tip `d1e37b9`, killed at `test_write_stage` after **2,950 ok, zero
  test-level reds** — `run2-killed-partial.log`, retained honestly.
- A killed run has no verdict and licenses nothing; it is recorded
  because 2,950 green tests are evidence about the tree even when they
  are not a gate result.

## Run 3 — killed 214 log lines in

- Relaunched, then stopped again almost immediately (at
  `test_cold_receipt`). Two consecutive kills were read as a deliberate
  operator stop; the gate waited for explicit direction instead of
  relaunching. No log retained — nothing in 214 lines outlived run 2's
  partial.

## Run 4 (final) — GREEN

- tip `d1e37b9`, relaunched on the maintainer's "run it":
  **2,986 tests in 22,504.4 s (6 h 15 m), `OK (skipped=5)`** —
  `run3-green.log` (the log kept run 3's `.runtime/` filename; it is the
  fourth launch and the only completed re-run).
- The 18 `FAIL`-bearing lines in the log are diagnostics printed by
  `TheCheckCanGoRed` adversarial tests that themselves pass (`... ok`);
  0 failures, 0 errors, 5 skips (the same 5 environment-conditional
  skips as every gate since v0.21).

The green run is the gate. Run 1's reds changed instruments, never
results: no frozen number, no gate verdict, and no registered artifact
moved between `ac45507` and `d1e37b9` except the three fixes and the
registry re-seal they forced.
