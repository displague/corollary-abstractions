# Prover phase 1 — real (stateBefore, tactic, stateAfter) extraction, native Windows

**Date:** 2026-08-07
**Host:** Windows 11 Home 10.0.26200, PowerShell 7
**Outcome:** SUCCESS. 16 theorems mirroring `data/logic/nodes.json`, **155 tactic
steps** extracted end to end, no WSL2, no `lean_dojo_v2` Python install.
Extractor exit code 0, zero `WARNING: Failed to process` lines.

Deliverables:

| File | Size | What |
|---|---|---|
| `prover/ExtractData.win.lean` | 20,463 B | patched tracer (origin + patch documented in its header) |
| `prover/sample_triples.json` | 38,316 B | 155 `{theorem, tactic, stateBefore, stateAfter}` objects |
| `prover/PHASE1_NOTES.md` | this file | |

Working area (plain dir, **not** a git worktree, untracked):
`C:\Users\displ\Documents\corollary-abstractions\.worktrees\prover-phase1\boollaws`

---

## Versions

| Thing | Version |
|---|---|
| elan | 4.2.3 (b6cec7e10 2026-06-08) |
| Lean | 4.32.2, `x86_64-w64-windows-gnu`, commit `f3b06c705e6c85f5314019d5d3baab0fec5b580c` |
| Lake | 5.0.0-src+f3b06c7 |
| Python (post-processing only) | 3.13 |
| `lean-dojo-v2` (source of `ExtractData.lean`) | 1.0.9 wheel, **not installed** — only unzipped |

Pristine `ExtractData.lean` sha256:
`b50bebdef8adde06d1f6948edc0ac52f67dd8b40045df72290a1f225049ffc50`

Toolchains already present from the feasibility run: `v4.20.0`, `v4.29.1`,
`v4.32.2`. Only `v4.32.2` is new enough (`String.trimAscii`).

---

## Exact commands that worked

Per-shell environment (PowerShell). `elan` is **not** on the default `PATH`, and
it is not visible from Git Bash at all:

```powershell
$env:Path = "$env:USERPROFILE\.elan\bin;$env:Path"
$env:PYTHONIOENCODING = "utf-8"     # proof states contain ⊢ ∧ ∨ ¬ → ∀ ∃ ↔ α
$env:DISABLE_REMOTE_CACHE = "1"
```

### 1. Minimal lake project (no mathlib, no network beyond the toolchain)

```
.worktrees\prover-phase1\boollaws\
  lakefile.toml       name = "boollaws"; defaultTargets = ["BooleanLaws"]; [[lean_lib]] name = "BooleanLaws"
  lean-toolchain      leanprover/lean4:v4.32.2
  BooleanLaws.lean    16 theorems (see below)
```

```powershell
Set-Location .worktrees\prover-phase1\boollaws
lake build
# info: boollaws: no previous manifest, creating one from scratch
# ✔ [2/3] Built BooleanLaws (402ms)
# Build completed successfully (3 jobs).
```

Built clean on the first attempt — no mathlib, no `lake update`, no network.

### 2. Patched extractor

Source: the wheel already downloaded during the feasibility run at
`.worktrees\leandojo-scratch\whl\lean_dojo_v2\lean_dojo\data_extraction\ExtractData.lean`
(equivalently `pip download lean-dojo-v2 --no-deps -d .\dl` + `Expand-Archive`).
Two lines patched inside `LeanDojo.Path.findLean`; a provenance header was
prepended and the result saved as `prover/ExtractData.win.lean`.

### 3. Trace

```powershell
$prefix = (lean --print-prefix).Trim()
# -> c:\Users\displ\.elan\toolchains\leanprover--lean4---v4.32.2
New-Item -ItemType Directory -Force .lake\packages | Out-Null
robocopy $prefix .lake\packages\lean4 /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
Copy-Item ..\..\..\prover\ExtractData.win.lean .\ExtractData.lean -Force
lake env lean --threads 8 --run ExtractData.lean noDeps
# EXIT=0, no output at all (silence == success; failures print
# "WARNING: Failed to process <path>")
```

> `robocopy` exits **1** on "files copied OK". PowerShell's `$LASTEXITCODE`
> therefore looks like a failure and can abort a `&&`-style chain. Ignore it or
> pipe to `Out-Null` and don't test the code.

Artifacts:

```
.lake\build\ir\BooleanLaws.ast.json    896,838 B
.lake\build\ir\BooleanLaws.dep_paths        79 B
```

`ast.json` top-level keys: `tactics` (155), `premises` (135), `commandASTs` (20).

### 4. Post-process to `sample_triples.json`

`ExtractData` records tactics as **byte offsets, not text** — you must slice the
source yourself. Theorem attribution is not in the JSON either; it is recovered
by matching each tactic's start offset to the last `^theorem <name>` before it.

```python
import json, re, pathlib
ast = json.loads(pathlib.Path(".lake/build/ir/BooleanLaws.ast.json").read_text("utf-8"))
src_b = pathlib.Path("BooleanLaws.lean").read_bytes()
src_t = src_b.decode("utf-8")
decls = sorted((len(src_t[:m.start()].encode("utf-8")), "BooleanLaws." + m.group(1))
               for m in re.finditer(r"^theorem\s+([A-Za-z_][\w']*)", src_t, re.M))
def owner(i):
    return max((s for s, _ in decls if s <= i), default=None)
out = []
for t in ast["tactics"]:
    a, b = t["pos"]["byteIdx"], t["endPos"]["byteIdx"]
    out.append({"theorem": dict(decls)[owner(a)],
                "tactic": src_b[a:b].decode("utf-8"),
                "stateBefore": t["stateBefore"],
                "stateAfter": t["stateAfter"]})
pathlib.Path("sample_triples.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
```

**No truncation was applied** — the largest proof state in this corpus is 125
characters. A `MAX_STATE = 4000` guard exists in the post-processor but never
fired. Final file is 38 KB, far under the 300 KB budget.

---

## Counts

- **Theorems:** 16 (all proved with explicit tactics; none `sorry`)
- **Tactic steps extracted:** 155 (155 distinct byte ranges — no duplicates)
- **Premises:** 135 · **commandASTs:** 20
- **Atomic tactic steps:** 106 · **structured/block steps:** 49
- **Steps whose `stateAfter` is `"no goals"`:** 74 (48%)
- **Longest `stateBefore` / `stateAfter`:** 125 / 125 chars

Per theorem (name → steps), and the `data/logic/nodes.json` node each mirrors:

| theorem | steps | corpus node |
|---|---|---|
| `de_morgan_not_or` | 16 | `logic.boolean_laws.de_morgan_laws` (dual, constructive) |
| `de_morgan_not_and` | 16 | `logic.boolean_laws.de_morgan_laws` (principal, classical) |
| `not_forall_iff_exists_not` | 14 | `logic.boolean_laws.de_morgan_laws` (quantifier form) |
| `double_negation` | 11 | `logic.boolean_laws.double_negation` |
| `absorption_and_or` | 9 | `logic.boolean_laws.absorption` |
| `absorption_or_and` | 10 | `logic.boolean_laws.absorption` (dual) |
| `identity_and_true` | 11 | `logic.boolean_laws.identity_laws` |
| `identity_or_false` | 9 | `logic.boolean_laws.identity_laws` |
| `non_contradiction` | 4 | `logic.boolean_laws.complement_laws` |
| `excluded_middle` | 5 | `logic.boolean_laws.complement_laws` |
| `idempotence_and` | 7 | `logic.boolean_laws.idempotence` |
| `idempotence_or` | 1 | `logic.boolean_laws.idempotence` (single `simp`) |
| `distrib_and_or` | 12 | `logic.boolean_laws.distributivity_meet_over_join` |
| `distrib_or_and` | 13 | `logic.boolean_laws.distributivity_meet_over_join` (dual) |
| `contraposition` | 13 | `logic.inference.contraposition` |
| `modus_ponens` | 4 | `logic.inference.modus_ponens` |

Head-token distribution over the 106 atomic steps:

```
exact 41 · intro 32 · constructor 13 · apply 7 · by_cases 4 · left 3
have 2 · right 1 · refine 1 · trivial 1 · simp 1
```

(`cases … with` never appears here — see quirk 3.)

---

## One full verbatim triple

Element index 19 of `prover/sample_triples.json`, byte-for-byte:

```json
{
 "theorem": "BooleanLaws.de_morgan_not_and",
 "tactic": "by_cases hp : P",
 "stateBefore": "case mp\nP Q : Prop\nh : ¬(P ∧ Q)\n⊢ ¬P ∨ ¬Q",
 "stateAfter": "case pos\nP Q : Prop\nh : ¬(P ∧ Q)\nhp : P\n⊢ ¬P ∨ ¬Q\n\ncase neg\nP Q : Prop\nh : ¬(P ∧ Q)\nhp : ¬P\n⊢ ¬P ∨ ¬Q"
}
```

---

## Data quirks relevant to future tokenization

**1. Proof-state grammar.** A state is a `\n\n`-separated list of goals; each goal
is `\n`-separated lines: an optional `case <tag>` line first, then hypothesis
lines `name₁ name₂ : Type`, then exactly one `⊢ <goal>` line. Multiple
hypotheses sharing a type are **collapsed onto one line** (`P Q : Prop`), so a
tokenizer cannot assume one binder per line. Case tags are dotted and
accumulate: `mp` → `mp.left` → `mpr.intro`; `by_cases` emits `pos`/`neg`,
`constructor` on `Iff` emits `mp`/`mpr`, on `And` emits `left`/`right`,
`cases` on `Or` emits `inl`/`inr`. The tag namespace is therefore a small,
learnable vocabulary — a good candidate for dedicated concept tokens.

**2. `"no goals"` is a literal sentinel**, not an empty string — 74 of 155 steps
end there. Any next-tactic model needs it as an explicit terminal symbol. There
is no separate "proof closed" marker.

**3. Structured tactics are captured as one span, swallowing their branches.**
`cases h with | inl … => … | inr … => …` is a single entry whose `stateAfter` is
`"no goals"` — the two-goal intermediate state is **never** emitted. Likewise a
focus bullet `· intro h; exact …` appears as one multi-line "tactic" whose
`stateBefore` is the full multi-goal state and whose `stateAfter` is the
remaining goals. The nested atomic steps *are* also emitted separately, so the
data is hierarchical, not a flat linear trace: 49 of 155 entries are containers
for other entries. Detect them with `"\n" in tactic or tactic.startswith("·")`.
**Implication for phase 2:** for a flat next-tactic dataset, either filter to
atomic entries, or write proofs with unstructured `cases h` + bullets so the
branch-producing step gets its own transition.

**4. Byte offsets, not text.** `pos`/`endPos` are `{"byteIdx": N}` objects
(UTF-8 byte offsets into the source), so slicing must be done on `bytes`, not
`str` — the source is full of 3-byte connectives and off-by-N is silent
corruption. `stateBefore`/`stateAfter` *are* plain strings.

**5. Unicode inventory in the states** (this corpus, both fields, all 155 steps):

```
¬ 326 · ⊢ 272 · ∧ 191 · ∨ 185 · → 167 · α 87 · ∀ 28 · ∃ 25 · ↔ 13
```

All BMP, all 3-byte UTF-8 except `α` (2-byte). `PYTHONIOENCODING=utf-8` is
mandatory on Windows or printing a state raises `UnicodeEncodeError` under
cp1252. Every one of these glyphs is a natural single concept token; a subword
tokenizer will otherwise shred them into byte fragments.

**6. Notation is pretty-printed, not source-faithful.** The states use `¬`/`∧`
even where a proof wrote `Not`/`And`, and `¬(P ∧ Q)` keeps `Not` folded rather
than unfolding to `(P ∧ Q) → False` — but after `intro`, the same proposition
*does* surface as goal `False`. So the same semantic object has two surface
forms depending on tactic history. Round-tripping tactic text against state text
is not exact.

**7. `.dep_paths` still has mixed separators** even with the cwd half of the
patch applied:

```
.lake\packages\lean4/src/lean\Init.lean
.lake\packages\lean4/src/lean\Init.lean
```

(two identical lines: `BooleanLaws.lean` declares no imports, so the synthesized
module header lists the implicit `Init` prelude twice and `findLean` resolves
both). Same for `defPath`
in `premises`: `.lake\packages\lean4/src/lean\Init\Core.lean`. Parse
tolerantly — normalize on `[\\/]+`. This is FEASIBILITY.md landmine 8 and it is
**not** fixed by the patch; the mixture comes from `packagesDir`'s
forward-slash literals being joined with backslash paths.

**8. `premises` carries a usable retrieval index for free** — `fullName`,
`modName`, `defPath`, and both use-site and definition-site line/column. 135
entries for 16 theorems, i.e. premise selection (README phase 5) can be
prototyped on the same extraction with no extra tooling.

---

## Deviations from FEASIBILITY.md's script

1. **Second patch line corrected.** FEASIBILITY.md's next-step block says to
   normalize `let cwd ← IO.currentDir` "the same way", and the copy left in
   `.worktrees\leandojo-scratch\lean4-example\` did it as
   `.replace "\\\\" "/"` — which in Lean is a *two*-backslash pattern that never
   matches, making that half of the patch a silent no-op. `ExtractData.win.lean`
   uses the single-backslash pattern `.replace "\\" "/"`. Effect: `findLean` now
   returns paths **relative** to the project root (`.lake\packages\lean4/...`)
   instead of absolute ones. Verified working; no regression.
2. **No `elan toolchain install stable` needed** — v4.32.2 was already present
   and was pinned directly in `lean-toolchain`.
3. **`pip download` skipped** — reused the 1.0.9 wheel already unzipped under
   `.worktrees\leandojo-scratch\whl\` during the feasibility run (sha256 of the
   pristine `.lean` recorded above so it can be re-verified against PyPI).
4. **Custom project instead of `lean4-example`** — the corpus had to mirror
   `data/logic/nodes.json`, so `boollaws` was written from scratch. Core Lean 4
   only; mathlib deliberately never fetched.
5. `--threads 8` as documented; the whole trace takes a few seconds for one
   module.

## Not done / next

- Nothing was committed; all three `prover/` files are left untracked for review.
- The `robocopy`'d stdlib (`.lake\packages\lean4`, ~1 GB) stays in the scratch
  dir; delete it when the artifacts are accepted.
- Phase 2 entry point is PyPantograph, already built natively at
  `.worktrees\leandojo-scratch\PyPantograph` (needs the Lean toolchain `bin` dir
  on `PATH` for the DLLs).
