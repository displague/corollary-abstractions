# v0.14 release gate — measured test inventory

Every `tests/test_*.py` module run one at a time at a single frozen tip,
`55b4097ef7ab0238ec099fffa6bd4694ee991f7d`, with a per-module receipt and log
retained here.  `manifest.json` is the tool's own record; `shard-plan-5.json`
is the registered balanced assignment derived from it.

**Result: 68 modules, 1,341 tests, 0 failures, 0 errors, 5 skipped.**
Serial wall clock 21,688 s (6.02 h).

The measurement had to run from a detached checkout outside the repository
with `--out-dir` outside that again, because the tool refuses to write inside
the tree it measures and refuses to measure at all while a gitignored
executable sits outside `.venv/`.  See BACKLOG for the invocation.

Two modules are 94.8% of the suite:

| module | seconds | share | fixture+overhead |
|---|---|---|---|
| `test_write_stage` | 12,522.5 | 57.7% | 8.5 s (0%) |
| `test_corpus_analogy_split` | 8,045.0 | 37.1% | 3,434.2 s (43%) |
| everything else (66 modules) | 1,120.5 | 5.2% | — |

`shard-plan-5.json` therefore puts one module in shard 0, one in shard 1, and
all 65 remaining modules in shards 3 and 4 for a combined 717 s.
