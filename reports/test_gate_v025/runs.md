# [SUITE-GATE-V25] — the full-suite gate for v0.25.0

The tag's gate is one complete `unittest discover -s tests -v` at the
frozen tip, logged OUTSIDE the hashed tree (`.runtime/`, the v0.23 run-1
lesson). Unlike v0.23 and v0.24, the logs are **not** retained in this
directory; §"Where run 1's log is" says why, and it is a finding of this
gate rather than a filing preference.

## Run 1 — RED by exactly three, all instrument

- tip `e66de24`, 3,281 tests in 24,209.9 s (6 h 43 m):
  `FAILED (failures=3, skipped=5)`.
- No gate verdict, no frozen number and no registered artifact is
  implicated by any of the three. Each is a check whose *rule* was
  narrower than the thing it was checking.

### The append-only reconstruction knew one marker shape; there are two

`tests/test_conform_ce3_supplement.py`,
`TheAmendmentIsDatedRetrospectiveAndAppendOnly`. The check undoes the
retirement chain on `experiments/conformance_prereg.json` and demands the
bytes sealed at `a98fa3cc` back. The evaluator row's
`retired_for_future_comparisons` marker sits mid-object and carries its own
trailing comma; the `parser` row's marker, appended 2026-09-01 by
`big-op-disclosure-2026-09-01` (`156e94f`), is that row's **last** key, so
the separating comma lands on the preceding line and the strip regex —
which required `},` — missed it.

`git diff 156e94f~1 HEAD` moves no sealed byte: the amendment is a pure
append, and so are the same lane's appends to `exact_literals_prereg.json`
and `echo_prereg.json`, which take the last-key shape too and whose tests
did not fire only because they have no reconstruction check. The rule now
undoes both placements with a brace-balanced match. An edit to a sealed row
still fails, because stripping a marker cannot put back bytes an edit
removed.

### B5's disclosure sweep walks a virtualenv that is not at the root

`tests/test_house_rules_run.py`, `ReviewFixTests`. The whole-repository
disclosure reported `added_after_the_seal_and_unclassified: 13` where the
committed artifact discloses 19 hits and no such bucket. All 13 were
`experiments/.venv/**` — third-party `site-packages` sources and two CUDA
DLLs read with `errors="ignore"` — because
`write_stage.INTEGRITY_EXCLUDED_RUNTIME` matches `.venv` as a **root**
prefix. A clean worktree of the same commit reports 19 and no bucket: the
number moved with what the operator had installed, which is not a property
of the tree it claims to describe.

The assertion was also aimed wrong. It ran against a LIVE re-run of the
gate and demanded the shape of the REGISTERED one, so any later addition to
the repository becomes a suite failure. It now asks the empty finding
bucket of the **committed** artifact — the only place it was ever a fact —
re-derives the published rule path by path against the live sweep, and
keeps one tooth that survives a growing repository: an unclassified path
git neither tracks nor ignores is a stray write and still fails.

The sweep-scope looseness is `scripts/**` and is filed in `docs/BACKLOG.md`
rather than fixed, so this repair opens no file the CR-P0 registry census
seals.

### A citation sweep re-pinned a line number inside a frozen quotation

`tests/test_plain_input.py`, `PreregIsVerbatim`. `[TRIAGE-V25-LOWS]`
(`2aadbfd`) corrected twelve stale `SPEC-chat-completions-skin.md`
citations in `docs/DESIGN-plain-input.md`. One of them sat **inside** the G4
clause that `experiments/plain_input_prereg.json` freezes verbatim — the
same commit that deliberately left the prereg's own copy of that citation
alone, on the ground that a stale citation inside a seal is a fact about the
seal. The design side of the same quotation is the same fact.

The clause's bytes are restored to the sealed text and the corrected pin is
carried in a dated note beside the clause. A sweep of every verbatim-pinned
string under `experiments/**` and every string literal under `tests/**`
against all five documents that commit touched finds this as the **only**
collision.

## Where run 1's log is, and why it is not in this directory

`.runtime/gate_v025_run1.log` (the `unittest -v` stderr stream, 557,261
bytes, `sha256 ccb5740261707c0c83961ad79a2b23527770b35beeb6009ca80a823704f9b0ef`)
and `.runtime/gate_v025_run1.log.out` (stdout, 4,201 bytes,
`sha256 885b66f84c8316c471e3005545a6b474b9baa153bb53a11345c7b9dde21abe7a`).

Retaining the stderr log here — the v0.23 and v0.24 practice — was tried and
**reverted**, because it breaks a published check. Three of the log's
`unittest -v` test-name lines contain admitted symbol names from the H-P0
corpus. `scripts/check_house_rules_receipts.py` re-sweeps the LIVE tree for
those names and compares the result with the disclosure committed in
`experiments/house_rules_verdicts.json`, which was scored at `32d505a` over
a tree of 19 such files. Adding the log makes it 20, and the checker the
release notes tell a reader to run from a fresh clone goes red four ways:

```
FAIL [b5-disclosure-count]          ... a second sweep finds 20
FAIL [b5-disclosure-paths]          ... sweep-only ['reports/test_gate_v025/run1-red.log']
FAIL [b5-disclosure-classification] ... 1 disclosed path(s) carry no classification
FAIL [b5-disclosure-classification] ... counts sum to 19 over 20 disclosed path(s)
```

That is not a defect this gate should route around by editing the log:
scrubbing three lines out of the evidence to make a checker pass is the
move the whole apparatus exists to prevent. So the log stays outside the
tree and is cited by digest.

The general shape is worth stating because it will recur: **between a
registered house-rules run and the next one, no file carrying an admitted
name can be added to the repository.** `docs/RELEASE-v0.25.0.md` already
obeys this — it tells the leak story without quoting a name — and
`tests/test_house_rules_run.py` says so in its own module docstring. The
published classification rule has no class for post-seal repository
content, which is the other half of the same gap; both are filed in
`docs/BACKLOG.md`.

## Run 2 — pending
