# Handoff — ROADMAP-v0.10 item 3 (programming as a first-class discipline), run in PARALLEL

Written 2026-08-12 while item 2 (the external verifier) is being merged. This
is a self-contained work order for a second agent working **concurrently**
with the loop agent. It names the slice, the boundary that keeps the two from
colliding, and the house protocol the work has to follow.

## Who owns what (the collision boundary — read first)

The loop agent is finishing item 2 and then takes **item 5 (harness session)**
and **item 4 (author the covered subset)**, in that order. You take **item 3**.

**Files the loop agent is actively changing — do not edit them; you will
regenerate, not merge, the ones you need:**

| file | why |
|---|---|
| `reports/*.json` | ledgers; regenerate after rebase, never text-merge |
| `experiments/wold_reach.json` | recounts `data/` tokens; regenerate |
| `tests/test_decompose_channels.py` | GC4/GC5 pins + append-only acknowledgments |
| `tests/test_matcher_mirror.py` | `nodes_analyzed` + `group_counts` |
| `tests/test_verified_by.py` | link count + CLI node-count pin |
| `README.md` | corpus/discipline counts |
| `data/number_theory/`, `scripts/seed_number_theory.py` | item 2's ingested nodes |
| `scripts/retrieval.py`, `scripts/external_verifier.py` | item 2 landed changes here |

Yours alone: `data/programming/`, `scripts/seed_programming.py`, a new
`docs/DESIGN-programming-discipline.md`, new tests, and new
`data_sources/` manifest entries + derived extracts.

**Rebase rule (this is how the repo avoids ledger merge hell):** when the loop
agent's slices land, `git fetch && git rebase origin/main`, then **re-run the
generators** (`python scripts/match_signatures.py`, `specialize.py`,
`decompose.py`/`compression`, `proof_correspondence.py`, plus
`scripts/ingest_wold.py reach` if `data/` changed) and re-pin. Ledger JSON
conflicts are resolved by regeneration, never by editing the diff. Pins in the
three test files above are resolved by taking main's value and re-measuring on
top; if a pinned value moves because of YOUR nodes, that needs its own
**append-only registered acknowledgment** — never touch the existing ones.

## Where main stands right now

`main` @ `14a3bf3` + the item 2 slice (merging shortly, 5 commits ending
`c333c56`). After that merge: corpus **253 nodes / 24 disciplines**,
`verified_by` **17 links** (16 CORRESPONDS / 1 UNTRANSLATABLE / 0 MISMATCH),
`group_counts {shape 30, typed 31, family 30, aliased 32, mirror 5}` (fifth
consecutive twin null), GC4 mean 0.774 / 531 exact / 99 pattern / 222
statements-with-constituents, grammar coverage Goedel-Pset 44.6% /
Lean-workbook 71.5% / miniF2F 33.4%. Branch off `origin/main` **after** the
item 2 merge lands (ask, or poll `git log origin/main`), because item 3 is
built on the verifier.

## The item, verbatim from ROADMAP-v0.10

> The architecture runs the same operations over code with the verifier of
> item 2 swapped in. AST → canonical form → structural address → pointer
> residual → external verifier. A verified code snippet becomes nodes;
> structural-twin recovery, specialization, and propose→verify→repeat
> synthesis follow with no new machinery.
>
> **Acceptance:** one verified-code node type end-to-end, one
> structural-twin-over-code result against a capability-blind baseline, one
> synthesis-or-debug transaction adjudicated by the external verifier.

Three deliverables, all three required. "No new machinery" is the claim under
test — if you find yourself adding a parallel matcher or a second verdict
vocabulary for code, stop and write down why the existing one could not carry
it; that write-up is worth more than the workaround.

## What item 2 hands you (use it, do not rebuild it)

- `scripts/external_verifier.py` — `check-lean4`, `check-python`, `recheck`,
  `ledger`. The `python-tests` backend is exactly your verifier: `py_compile`
  → `mypy --strict` → `unittest` under `scripts/_verifier_sandbox.py`'s audit
  hook. Verdicts are committed, deterministic (LF, sorted keys, no
  timestamps, no machine paths), never bare booleans, over
  `{pass, fail, refused}`.
- **The honesty boundary, which you inherit and must not soften:** *a passing
  check certifies what it checks, not correctness in general.* A
  `python-tests` PASS says the pinned candidate compiled, type-checked and
  survived the pinned tests — not that it is correct.
- **The vocabulary decision is yours to make, with its own design note.**
  Item 2's design deliberately froze `verified_by.system` to `lean4` and
  wrote: *"a `python-tests` verdict is a committed, recheckable authority for
  a computational claim, but it does not enter the corpus's `verified_by`
  vocabulary this slice — that is roadmap item 3's decision to make."* Decide
  it explicitly, argue it, and register predictions either way.
- **A backlog item that is really yours:** `docs/BACKLOG.md` — "Verdict-backed
  ingestion should be a RULE, not a precedent". Nothing yet forces a new
  ingested node to carry a verdict; a manifest entry that omits `verdicts` is
  cited like the 16 pre-verifier links. If item 3 mints code nodes, make the
  rule real for them, with a prediction.
- Read `docs/DESIGN-external-verifier.md` §1–§3 and §8 before designing. §8's
  four disclosures are the failure modes you are most likely to repeat
  (machine paths in a committed ledger; an audit-hook rule that reads only
  `open`'s mode; a "recorded" negative that lives only in prose; pins
  elsewhere in the repo that assumed the old corpus shape).

## Sources — license-gate BEFORE use, and cite whatever you use

User-supplied candidates (also in memory `programming-discipline-sources.md`):

- `https://github.com/thuva4/Algorithms` — multi-language algorithm
  implementations. Check the LICENSE in the repo itself, not the README.
- `https://github.com/IBM/Project_CodeNet` — problems + submissions + **test
  cases** (the test cases are what make it fit the `python-tests` backend).
  CodeNet's own metadata is Apache-2.0 but **submissions carry their own
  terms** — gate before anything redistribution-adjacent.
- `https://huggingface.co/datasets/TheFinAI/ibm-project-codenet` — HF mirror;
  pin the revision + SHA if used.
- Papers for context: arXiv 2105.12655 (CodeNet), 2605.15607v2, 2602.16106v1.

**House rule (the user's hard constraint): anything used goes through
`data_sources/manifest.json` — pinned URL + SHA256, license field, and an
`attribution` field that IS the citation of record — plus a `NOTICE.md` in the
derived directory. If it is not cited there, it may not be used.** The WOLD
slice (`scripts/ingest_wold.py`, `data_sources/derived/wold/`) is the worked
example to copy: fetch → verify SHA → verify the license text *inside the
archive* → derive a committed extract → `tests/test_*_ingest.py` pins the
manifest entry, the license, and the citations. Empirical-tier sources never
ground a `verified_by`.

A smaller, cleanly-licensed source that reaches the acceptance bar beats a
large one you cannot redistribute. Say in the design note which you chose and
why.

## The protocol every slice in this repo follows

1. **Measure first.** No head, node type, or feature without the number that
   justifies it.
2. **Register the design BEFORE implementing.** Commit
   `docs/DESIGN-programming-discipline.md` as its own commit, with numbered
   predictions (P1, P2, …) written as floors, and an explicit disclosure of
   any probe you already ran (a prediction registered after its experiment is
   not a prediction). Adjudicate them in a §8-style section afterward, exact
   to the row, appending disclosures rather than editing the registered text.
3. **Corpus nodes are generated, never hand-edited.**
   `scripts/seed_programming.py` → `data/programming/nodes.json`;
   `python scripts/check_regeneration.py` must show byte-identical output and
   `python scripts/validate_nodes.py` must pass.
4. **Self-run the mechanical harness before asking anyone to review:**
   `python scripts/verify_slice.py --base <merge-base>` (add `--goedel` only
   if you touched `scripts/grammar_coverage.py` or an ingest script; it adds
   the 1.73M-row pass). It checks regeneration, ledger git-cleanliness, the
   matcher, audit fields, the per-row dual pass (LOST=0 is the standard), that
   the base's registered acknowledgments are byte-intact, guard arithmetic,
   and the full suite. **Run it AFTER committing your ledger regenerations** —
   the git-clean check compares against HEAD, so uncommitted regenerated
   reports read as a FAIL.
5. **Then an independent adversarial review, capped:** run `verify_slice`,
   attack the DESIGN (the one thing a script cannot), hand-adjudicate a ~20-row
   random sample of whatever you claim, and hunt one novel false-positive or
   bypass class. Every slice in this cycle has had a real defect found this
   way — five for five — so budget for fixes, not for a rubber stamp.
6. **ff-merge only**, after rebase. Push `origin/main`.

## Environment notes that will cost you an hour otherwise

- Work in a worktree: `git worktree add ./.worktrees/v010-programming -b
  feature/v010-programming origin/main`. Share the venv at
  `C:\Users\displ\Documents\corollary-abstractions\.venv` (`pytest` is NOT
  installed; the suite runs under `python -m unittest`).
- Set `PYTHONIOENCODING=utf-8` for every command — the console is cp1252 and
  will crash on `⊆`, `∣`, `⟨⟩`.
- `data_sources/archives/` is **gitignored and vanishes with a deleted
  worktree.** The pinned archives currently live in
  `.worktrees/v010-embedded-quantifiers/data_sources/archives` (goedel-pset,
  lean-workbook, minif2f, plus hardlinked `english-wordnet-2025-json.zip` and
  `wold-4.2.zip`); junction that directory into your worktree rather than
  re-downloading:
  `New-Item -ItemType Junction -Path <your-worktree>\data_sources\archives -Target <that path>`.
- **The full suite takes 45–70 minutes** (~1000 tests, many spawning
  subprocesses and real Lean). Run it in the FOREGROUND or as a tracked
  background job and do not start a second one — two concurrent runs starved
  each other and blew a 3600s timeout today. Backgrounded jobs die with the
  agent that started them; if a job is killed, kill its orphaned Python child
  too (`Get-Process python`) before rerunning.
- Lean is real here: elan with toolchains v4.20.0/v4.29.1/v4.32.2/v4.33.0.
  **Mathlib is out of the hermetic budget** — core Lean only.
- Commit incrementally with why-rich messages, so a session-limit kill loses
  nothing.

## Definition of done for item 3

- A committed design note with registered predictions and their adjudication.
- One **verified-code node type end-to-end**: source pinned and cited in the
  manifest → candidate + tests pinned → committed `python-tests` verdict →
  node(s) generated by seed → validator green → whatever link vocabulary your
  design argued for (and if the answer is "code nodes carry no `verified_by`",
  that must be written at node level, the way item 2 recorded
  `formal`-without-bridge).
- One **structural-twin-over-code result against a capability-blind
  baseline** — the baseline is the point; report it even if it wins.
- One **synthesis-or-debug transaction adjudicated by the verifier**,
  including at least one REFUSED or FAIL that is recorded rather than retried
  away.
- `verify_slice` green, full suite green, ledgers regenerated and committed,
  `experiments/ANALYSIS.md` carrying the numbers of record, and any moved pin
  covered by its own append-only acknowledgment.
