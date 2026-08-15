# Handoff — finish v0.11 (tag), then start v0.12

Self-contained work order. You do not need the prior chat.
Read this file, then `AGENTS.md`, then the files named in each
phase. Work in a `.worktrees/` branch; merge to `main` and push.

**Tip when this was written:** `main` @ `408bf64` (same as
`origin/main`). Last tag: `v0.10.0`. There is **no** `v0.11.0` tag.

---

## 0. What you are not doing

- Do not rewrite the v0.11 argument. The blog and notes exist.
- Do not implement the live prompt, a ranker, or a fifth algorithm
  file as part of *finishing v0.11*.
- Do not call Lean-workbook held-out.
- Do not promote a passing Python test to a proof.
- Do not rewrite `reports/decompositions.json` (12k-node live
  analysis is the pin; the committed file is pre-scale).
- Do not tag while the complete-suite gate is still PARTIAL.
- Do not invent matcher operators or an AST-to-recurrence
  translator.

---

## 1. Where the project is (plain)

Cross-discipline statements live as templates a matcher can parse.
Exact questions (parse, equality, twin, test verdict, write-gate
refuse) are answered by programs. Models own only the leftover.
Seeds regenerate `data/*/nodes.json`. Predictions are written
before the tool that judges them.

**Corpus:** 12,777 statement nodes, 27 corpora, 9 verified-code
nodes. 12,514 Lean-workbook templates (302 ground + 12,212
emitted), 123 excluded.

**v0.11 headlines (shipped, not tagged):**

| item | result | regenerate |
|---|---|---|
| Self-grounding curve | Real 0.473 vs random 0.410 at N=12,515. **Below** random at N=8/32, **above** from N=128. Sharing proxy 1.000; grounding of those parts 0.543 | `scripts/measure_self_grounding.py` |
| Figure of merit | Bag precision against typed twins **0.0220%** (1,990/9,041,744). Matcher 1,991 pairs, one named miss | `scripts/measure_operator_bag.py` |
| Skeleton emitter | 12,514 / 123 | `experiments/lean_workbook_emit.json` |
| Programming wave 2 | 6 more nodes, `range(20)` vs `math.factorial`/`math.prod`; citation ≠ proof | `tests.test_programming_discipline` |

**Docs already written (do not redo):**

| file | role |
|---|---|
| `docs/ROADMAP-v0.11.md` | **Closed** — banner says where each item went |
| `docs/RELEASE-v0.11.0.md` | Notes; lead with the sign flip |
| `docs/TRIAGE-v0.11.md` | Gate 6/7 MET, **7 PARTIAL** |
| `docs/blog/the-curve-changed-sign.md` | The argument (not the inventory) |
| `docs/ROADMAP-v0.12.md` | Next plan; item 5 is the live prompt |
| `docs/DESIGN-heldout-recovery.md` | H1–H6 frozen |
| `docs/DESIGN-live-session.md` | One typed line; P-LS1–P-LS5 |
| `docs/DESIGN-residual-proposer.md` | Budgeted-edit ranker; parked |
| `docs/DESIGN-emergent-programming.md` | Write-recovery ranker; waits on a fit |
| `.claude/skills/release/SKILL.md` | How to tag; product-surface audit |

**Honesty the notes already refuse:** “the suite is green,” “the
external benchmark ran,” “a person can type into the harness.”

`python scripts/harness.py` prints a liveness list and **exits**.
v0.8 claimed the system can be driven. That was libraries + a
recorded session (`python scripts/session_run.py --check`), not a
prompt.

---

## 2. Finish v0.11 (this is the only remaining gate)

Follow `.claude/skills/release/SKILL.md`. Document rotation is
**already done**. You own: refresh, suite on the **tip**, tag,
GitHub release.

### 2.1 Refresh (from repo root, `PYTHONIOENCODING=utf-8`)

```
python scripts/check_regeneration.py
python scripts/validate_nodes.py
python scripts/match_signatures.py --write-report reports/signature_matches.json
python scripts/specialize.py --write-report reports/specializations.json
python scripts/measure_compression.py --write-report reports/compression.json
python scripts/session_run.py --check
```

Skip `decompose.py --write-report reports/decompositions.json`.

If `signature_matches.json` / `specializations.json` move only
because the 12,777-node graph is live, that is expected. Do not
text-merge ledger JSON.

### 2.2 Suite on the tip

Full `unittest discover` is 30+ minutes (several tests each reload
12k nodes). One test is skipped on purpose: full-graph
`min_family=1` above 1,000 statements.

Minimum that must be green before the tag:

```
python -m unittest tests.test_programming_discipline tests.test_emit_skeleton tests.test_self_grounding tests.test_item4_operator_bag tests.test_algorithms_ingest tests.test_verified_by tests.test_matcher_mirror tests.test_proof_correspondence
```

Then as much of `python -m unittest discover -s tests` as the
clock allows. If anything fails, **fix it**; do not tag around it.

When the tip suite is green, update `docs/TRIAGE-v0.11.md` gate 7
from PARTIAL to MET (one line: command + date). The release notes
already refuse “green” as a prior fact; a one-line addendum after
the run is honest.

### 2.3 Tag and GitHub release

```
git tag -a v0.11.0 -m "Ingestion compounds above a matched random baseline at thousands, and sits below that baseline at thirty-two. Bag precision against typed twins is 0.0220%."
git push && git push origin v0.11.0
gh release create v0.11.0 --title "v0.11.0 — the curve changed sign" --notes-file docs/RELEASE-v0.11.0.md
```

**Assets:** symbolic cycle, no new checkpoint. Do not invent a
`.pt` upload. If `gh` wants assets, attach nothing extra unless
an existing demo checkpoint still has its story in the notes’
Assets table (it does not claim a new one).

Verify: `gh release view v0.11.0`.

### 2.4 Collision / pin files if the suite forces a pin move

Append-only acknowledgments, never rewrite prior ones:

- `tests/test_decompose_channels.py`
- `tests/test_matcher_mirror.py` (nodes 12777; groups 1030/975/974/976/5)
- `tests/test_verified_by.py` (27 links: 18 lean4 + 9 python-tests)

---

## 3. Pick up v0.12 (after the tag, or in a new worktree)

Order is load-bearing. Independent review at every trust
boundary. **Do not share one working tree** between the emitter
prerequisite and the measurement (v0.11 did; v0.12 must not).

### 3.1 First: held-out structure recovery (headline)

Design already frozen: `docs/DESIGN-heldout-recovery.md`.
Predictions **H1–H6** are not to be edited to match the outcome.

**Prerequisite, own worktree, before the scale cut:**

1. Emit the miniF2F covered subset through the **existing**
   emitter. No matcher widening. Named dependant: item 1 small-N
   (163 full-statement-covered).
2. Seed a Goedel-Pset sample (~2,048 unique-covered the emitter
   can parse). Named dependant: item 1 scale.

Then measure: same self-grounding question, route 1 (owner
identity, not the sharing proxy), same null, plus a keyword /
operator-bag baseline **forbidden from seeing owner ids**.

Acceptance: `experiments/heldout_recovery.json` with H1–H6
adjudicated exact to the row. H2 (sign flip at N=8/32) is
load-bearing. **Lean-workbook is not held-out.**

If H1 fails: park the groundedness gate in BACKLOG in writing.
Do not train on Lean-workbook-shaped inequalities and call it
the claim.

### 3.2 Then: groundedness gate (only if H1 fires)

`DESIGN-heldout-recovery.md` §8: route 1 never the proxy; argue
against the conservative external share; do not fit to
Lean-workbook’s 0.473.

### 3.3 Then: one typed line (item 5)

`docs/DESIGN-live-session.md`. Implement **only**:

- `scripts/harness.py` `main()`: after the boot list, read **one**
  line, stop with a structured verdict.
- Path → existing `scripts/write_stage.py`. A proposal that
  replaces a seed that owns a corpus must print `seed_ownership`
  and leave the tree byte-identical (P-LS3).
- Other text → existing `scripts/dispatcher.py`. Unregistered
  content is a question or exhausted, never verified (P-LS2).
- Do not read `experiments/harness_session.json` (P-LS4).
- Do not fill a slot the person did not type (P-LS5).

Not this slice: HTTP skin, any ranker, fifth algorithm file,
English that authors a new node, a second user line in the same
process (P-LS6 stays parked).

Adjudicate P-LS1–P-LS5 in `DESIGN-live-session.md` §8 after the
run. Do not edit §7.

### 3.4 Do not start unless a later design names a fit

**Write-recovery ranker** (`DESIGN-emergent-programming.md`,
P-Z1–P-Z4): waits on an unsaturated *non-programming* leftover
that is not write-recovery itself and not a re-fit of the vacant
analogy (0.104 vs 0.1069) or tactic (65 vs 64) constructions.
If no fit is named by v0.12 triage, **park in BACKLOG**.

**Budgeted-edit ranker** (`DESIGN-residual-proposer.md`): parked.
Only one cell passes the source’s tests and is not the same
remainder recurrence (`programming.stein.binary`). Do not author
a second foil this cycle to unpark it.

### 3.5 Already shipped, still a dependant

Programming second wave is on `main`. It supplies the code-twin
sample for H3 (keyword baseline on a second modality). You do
not re-do the wave. You **run H3** as part of item 1.

Verdict-backed ingest as a rule is real for programming nodes
only. Widening it to Lean is item 4: a Goedel-Pset node that
cites `verified_by` without a PASS must be refused.

---

## 4. House protocol (every slice)

From `AGENTS.md`:

1. Orient from `ROADMAP-v0.12.md`, `experiments/ANALYSIS.md`,
   `docs/DISCOVERIES.md`, `docs/BACKLOG.md`.
2. Predict, then adjudicate. Fired and missed are both results.
3. Vacuity-check every test (cheapest capability-blind baseline).
4. Closed forms stay symbolic.
5. Statuses land as work lands (update the roadmap item the
   moment it ships).
6. `PYTHONIOENCODING=utf-8` on Windows.
7. Seeds are the source of truth. Never edit `data/*/nodes.json`
   by hand.

Worktrees. Merge to `main`. Push.

---

## 5. Suggested first commands

```
git fetch
git log -1 --oneline origin/main    # expect 408bf64 or a later tag commit
git tag -l v0.11.0                  # empty until you cut it
git worktree add -b release/v0.11-tag .worktrees/v011-tag
# then §2.1–2.3 in that worktree
```

After the tag, a **separate** worktree for miniF2F emit
(`feature/v012-minif2f-emit`), not shared with the measurement
worktree (`feature/v012-heldout-recovery`).

---

## 6. If something looks missing

| “Where is X?” | answer |
|---|---|
| Interactive / conversational harness | Designed: `DESIGN-live-session.md`. Not typable. v0.12 item 5. |
| Recorded session | `python scripts/session_run.py --check` |
| Why no tag | Gate 7. Skill forbids tagging on a PARTIAL suite. |
| Why no new `.pt` | Symbolic cycle. Notes say so. |
| H1–H6 | `DESIGN-heldout-recovery.md` — not run |
| P-LS1–P-LS5 | `DESIGN-live-session.md` §7 — not implemented |
| P-Z1–P-Z4 | `DESIGN-emergent-programming.md` — no fit yet |
| P-BR1–P-BR5 | `DESIGN-residual-proposer.md` — parked |
