# v0.17.0 complete-suite gate — the whole run history

All runs: `scripts/time_tests.py` over the 76 `tests/test_*.py`
modules, one process, main checkout, `PYTHONIOENCODING=utf-8`.
Red receipts are committed as failure excerpts with the full log's
SHA-256 recorded inside; the green log is committed whole.

| run | tip | result | cause, and what it taught |
|---|---|---|---|
| 0 | dde9435 | aborted before any test | `--json` arms `assert_clean_source`, which refuses the months of gitignored worktrees under `.worktrees/`; prior gates ran without `--json`, and so did every run below |
| 1 | dde9435 | 178 ran, 75 loader errors | operator error: CRLF in the module-list file left `\r` on 75 module names; the 178 `test_write_stage` tests that did load were green |
| 2 | dde9435 | 1,655 ran, **5 errors** (red receipt) | `experiments/tokenizers.py` shadows the installed `tokenizers` package for any module that runs after a test prepends `experiments/` to `sys.path` — five stopwatch classes green standalone, red in company; fixed at `979c155` |
| 3 | 979c155 | 1,705 ran, **1 failure** (red receipt) | the skin's `include_usage` streaming test — first diagnosed as the shadow's second site (`0c09d27`), which was **wrong** |
| 4 | 0c09d27 | 1,705 ran, **1 failure** (red receipt) | same test; the true defect was the TEST reading `usage` from `model_extra`, where the `openai` client never puts it — an environment-gated branch (the pinned tokenizer exists only in the main checkout) that had never executed anywhere until the gate ran where the environment is real; fixed at `b1f9a48` with the misdiagnosis corrected in the record |
| 5 | b1f9a48 | 1,705 ran, **1 error** (red receipt) | operator error, and the guard working: a docs merge landed in the main working tree mid-run, inside `WorkingTreeIntegrityTests`' window — the recursive tree digest caught its own operator; 1,704 of 1,705 otherwise green |
| 6 | ab45c23 | **1,705 ran, OK (skipped=3), 27,068.5 s** | the record |

The three skips are the pre-existing environment skips carried from
prior gates. No test was modified to pass except the two defects named
above, both committed with their stories, and no engine or serving
code changed between run 2's fix and the green run except the
mislabeled-but-harmless import hardening recorded at `0c09d27`.
