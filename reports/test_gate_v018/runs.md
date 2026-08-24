# v0.18.0 complete-suite gate

One run, green: `scripts/time_tests.py` over the 79 `tests/test_*.py`
modules, one process, main checkout frozen for the duration,
`PYTHONIOENCODING=utf-8`.

| run | tip | result |
|---|---|---|
| 1 | 30bf74d | **1,827 ran, OK (skipped=3), 24,117.3 s (6h42m)** |

Up from v0.17.0's 1,705 by the cycle's three new modules —
`test_realization_lexicon` (37), `test_realize_term` (44),
`test_measure_realization` (26) — plus the wiring's additions to
`test_answers` and `test_serve_chat`. The three skips are the
pre-existing environment skips. First-run green is not luck; it is
the v0.17 gate's six-run tuition paid forward: module names built
in-process (no CRLF file), the shadow-import class fixed at both
sites, the environment-gated usage branch now tested where its
environment is real, and main untouched from launch to verdict.
