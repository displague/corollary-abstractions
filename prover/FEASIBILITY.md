# LeanDojo-v2 on native Windows — feasibility report

**Date:** 2026-08-07
**Host:** Windows 11 Home 10.0.26200, RTX 5080 (16 GB), Git 2.52.0.windows.1
**Scratch area:** `C:\Users\displ\Documents\corollary-abstractions\.worktrees\leandojo-scratch` (plain dir, not a git worktree)
**Question:** Can LeanDojo-v2 run natively on Windows for prover phase 1 — extracting `(proof state, tactic)` pairs from a Lean 4 repo — or is WSL2 required?

---

## VERDICT: **NATIVE-PARTIAL** — and native is sufficient for phase 1

WSL2 is **not required** for phase 1. I extracted real `(stateBefore, tactic, stateAfter)` triples from a Lean 4 repo entirely natively on Windows.

The catch: **you cannot use the `lean_dojo_v2` Python package on native Windows** (its `deepspeed` dependency does not build). But phase 1 does not need it. The actual extractor is a *Lean* program — `ExtractData.lean` — shipped inside the wheel, and it runs natively once you apply a **one-line path-separator patch**. PyPantograph (the Lean RPC layer used for phase 2 interactive proving) also builds and runs natively.

| Component | Native Windows | Notes |
|---|---|---|
| elan + Lean 4 toolchain + `lake build` | **works** | first-class Windows support |
| `ExtractData.lean` tracer (the phase-1 payload) | **works after 1-line patch** | produces `.ast.json`, `.dep_paths` |
| PyPantograph `repl.exe` build + Python RPC | **works** | needs Lean DLL dir on `PATH` |
| `pip install lean-dojo-v2` | **BROKEN** | `deepspeed` wheel build fails |
| `lean_dojo_v2` Python `trace()` API | **BROKEN** | transitively imports `deepspeed`; also needs a live GitHub token |

---

## Versions installed

| Thing | Version |
|---|---|
| elan | 4.2.3 (b6cec7e10 2026-06-08) |
| Lean (lean4-example) | 4.32.2, `x86_64-w64-windows-gnu` |
| Lean (PyPantograph) | 4.29.1 |
| Python (scratch venv) | 3.13.12 |
| `lean-dojo-v2` | 1.0.9 (wheel downloaded; installed `--no-deps` only) |
| `pantograph` (PyPantograph) | 0.3.15 (`cp313-cp313-win_amd64` wheel, built locally) |

---

## What the docs say (step 1)

- **LeanDojo-v2 README**: requires Python ≥ 3.11, Git ≥ 2.25, `wget`, `elan`. Install: `pip install lean-dojo-v2`; Pantograph separately via `pip install git+https://github.com/stanford-centaur/PyPantograph`. No OS is stated, but all examples use `source .venv/bin/activate`.
- **CI (`.github/workflows/pytest.yml`)**: `runs-on: ubuntu-latest` only. No Windows or macOS runner. Installs elan via `elan-init.sh` piped to `sh`.
- **Original LeanDojo** docs list support as "Linux, Windows (**WSL**), macOS" — i.e. upstream has never claimed native Windows.
- **PyPantograph's role**: it is the Lean **RPC** layer — a `repl` binary the Python side talks to for interactive tactic application. It is needed for *proof search / interaction* (phase 2+), **not** for phase-1 corpus extraction.
- Encouraging counter-signal: PyPantograph's `build-pantograph.py` is explicitly Windows-aware:
  ```python
  repl_src = "repl.exe" if os.name == "nt" else "repl"
  ```

So the docs imply POSIX, but the code is not uniformly POSIX-only. Hence the empirical test below.

---

## Commands run, in order, with outcomes

### 1. Toolchain baseline
```powershell
elan --version   # -> NOT FOUND
python --version # -> Python 3.13.12
git --version    # -> git version 2.52.0.windows.1
```

### 2. Install elan natively
```powershell
winget install --id Lean.Elan -e
```
Installed **only the stub** `elan-init.exe` into
`%LOCALAPPDATA%\Microsoft\WinGet\Packages\Lean.Elan_Microsoft.Winget.Source_8wekyb3d8bbwe\`.
The advertised `elan`/`lake`/`lean` aliases were **not** created — `WinGet\Links` was empty. Must run the stub:
```powershell
& "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Lean.Elan_Microsoft.Winget.Source_8wekyb3d8bbwe\elan-init.exe" -y --default-toolchain none
```
-> `elan 4.2.3 (b6cec7e10 2026-06-08)` at `%USERPROFILE%\.elan\bin`. **Native, no WSL.**

### 3. `pip install lean-dojo-v2` — **FAILS**
```powershell
python -m venv .worktrees\leandojo-scratch\venv
.\venv\Scripts\pip.exe install lean-dojo-v2
```
Verbatim:
```
      [WARNING] Unable to import torch, pre-compiling ops will be disabled.
      DS_BUILD_OPS=1
      AssertionError: Unable to pre-compile ops without torch installed. Please install torch before attempting to pre-compile ops.
ERROR: Failed to build 'deepspeed' when getting requirements to build wheel
```
Retried with `DS_BUILD_OPS=0`, `setuptools`/`wheel`/`packaging` present, `--no-build-isolation`:
```
      running build_scripts
      creating build\scripts-3.13
      error: [Errno 2] No such file or directory: 'bin\\deepspeed.bat'
      ERROR: Failed building wheel for deepspeed
```
**`deepspeed` does not build on Windows** — its `setup.py` references a `bin/deepspeed.bat` entry-point script that is absent from the sdist. This is a known DeepSpeed Windows packaging defect, upstream of LeanDojo. `deepspeed>=0.7.0` is a **hard** `Requires-Dist` of `lean-dojo-v2`, so the plain install can never succeed natively.

### 4. Why this also kills the Python `trace()` API
Installed `--no-deps` plus the pure-Python tracing deps (`loguru networkx lxml tqdm toml gitpython PyGithub filelock psutil requests python-dotenv`), then:
```powershell
python -c "import lean_dojo_v2.lean_dojo"
```
```
  File ".../lean_dojo_v2/utils/common.py", line 16, in <module>
    from deepspeed.utils.zero_to_fp32 import convert_zero_checkpoint_to_fp32_state_dict
ModuleNotFoundError: No module named 'deepspeed'
```
`lean_dojo_v2/utils/common.py` lines 16–18 import `deepspeed` and `pytorch_lightning` **at module scope**, and `utils/__init__.py` re-exports from it — so the *data-extraction* code is transitively coupled to the *training* stack. An upstream layering defect, not a POSIX one.

With both stubbed out, the next wall:
```
  File ".../lean_dojo_v2/utils/constants.py", line 20
    raise ValueError("GITHUB_ACCESS_TOKEN environment variable must be set")
```
and with a dummy token set, `constants.py` **validates it over the network at import time**:
```
github.GithubException.BadCredentialsException: 401 {"message": "Bad credentials", ...}
```
So even on Linux, importing this package requires a real GitHub PAT and internet access.

### 5. Native Lean build — **works**
```powershell
git clone https://github.com/yangky11/lean4-example.git
cd lean4-example && lake build
```
-> `Build completed successfully.` Toolchain auto-downloaded (`lean-4.20.0-windows.tar.zst`). Native Lean 4 on Windows is solid.

### 6. Running the real tracer, `ExtractData.lean`
Replicated `trace.py::_trace()` by hand (`lake build` -> copy stdlib to `.lake/packages/lean4` -> copy `ExtractData.lean` -> `lake env lean --run`).

**First attempt (Lean 4.20.0) — version mismatch, not a Windows issue:**
```
ExtractData.lean:134:11: error: invalid field 'trimAscii', the environment does not contain 'String.trimAscii'
ExtractData.lean:410:2: error: failed to synthesize MonadState Trace TraceM
```
`ExtractData.lean` targets a newer Lean than lean4-example pins. Bumped `lean-toolchain` to `leanprover/lean4:v4.32.2` (`elan toolchain install stable`) -> **compiles clean**.

**Second attempt (Lean 4.32.2) — a genuine Windows bug:**
```
=== run ExtractData.lean ===
WARNING: Failed to process ...\lean4-example\Lean4Example.lean
```
Running the inner per-file command directly surfaced it:
```
PANIC at LeanDojo.Path.findLean ExtractData:274:2: assertion violation
uncaught exception: (`Inhabited.default` for `IO.Error`)
```

### 7. Root cause, proven
`ExtractData.lean` lines 261–262 strip build directories using **hardcoded forward slashes**:
```lean
let lean := olean.toString.replace ".lake/build/lib/lean/" ""
  |>.replace "build/lib/lean/" "" |>.replace "lib/lean/Lake/" "lib/lean/lake/Lake/"
```
On Windows `findOLean` returns backslashes, so no replacement fires and the derived `.lean` path does not exist, tripping `assert! ← path.pathExists` at line 274. Verified with a standalone Lean probe:
```
findOLean  = C:\...\lean4-example\.lake\build\lib\lean\Lean4Example.olean
split-count on forward-slash pattern (1 = NO match): 1
derived .lean path = C:\...\.lake\build\lib\lean\Lean4Example.lean
pathExists = false   (assert! at ExtractData:274 needs true)
```

### 8. The patch — **native tracing then works end to end**
Normalize separators before the replaces (plus the same for `IO.currentDir`):
```lean
let lean := olean.toString.replace "\\" "/" |>.replace ".lake/build/lib/lean/" ""
  |>.replace "build/lib/lean/" "" |>.replace "lib/lean/Lake/" "lib/lean/lake/Lake/"
```
Re-run:
```powershell
lake env lean --threads 4 --run ExtractData.lean noDeps   # EXIT=0, no warnings
```
Artifacts produced:
```
.lake/build/ir/Lean4Example.ast.json     35928 bytes
.lake/build/ir/Lean4Example.dep_paths       79 bytes
```
`ast.json` top-level keys: `tactics`, `premises`, `commandASTs` — **5 tactics, 18 premises**. Sample, i.e. exactly the phase-1 deliverable:
```json
{
 "stateBefore": "a b c : Nat\n⊢ a + b + c = a + c + b",
 "stateAfter":  "a b c : Nat\n⊢ a + (b + c) = a + c + b",
 "pos":    {"byteIdx": 103},
 "endPos": {"byteIdx": 113}
}
```
(`pos`/`endPos` are byte offsets into the source — slice the `.lean` file to recover the tactic text, here `add_assoc`.)

### 9. PyPantograph (phase 2 RPC) — also native
```powershell
git clone --recurse-submodules https://github.com/stanford-centaur/PyPantograph.git
git -C PyPantograph checkout f8aee320ee5550ea2677e414534618a61e7e1497
git -C PyPantograph submodule update --init --recursive
cd PyPantograph\src && lake build repl      # EXIT=0 -> .lake/build/bin/repl.exe (3,024,896 bytes)
cd .. && pip install .                      # -> pantograph-0.3.15-cp313-cp313-win_amd64.whl
```
First RPC attempt failed:
```
AssertionError: Server failed to emit ready signal: ; This could be caused by Lean version mismatch...
```
Running `repl.exe` directly gave exit `-1073741515` = `0xC0000135` **STATUS_DLL_NOT_FOUND**. It needs Lean's runtime DLLs (`libleanshared.dll`, `libInit_shared.dll`, …) which live in `<toolchain>\bin`. With that on `PATH`, `repl.exe` prints `ready.` and the full Python round-trip succeeds:
```
server started OK
goal_start -> ⊢ forall (a b : Nat), a + b = b + a
after 'intro a b' -> a : Nat / b : Nat / ⊢ a + b = b + a
after 'exact Nat.add_comm a b' ->
is_solved: True
```

---

## Windows landmines found (for future reference)

1. **`deepspeed` cannot build on Windows** — hard blocker for `pip install lean-dojo-v2`.
2. **`utils/common.py:16-18`** imports `deepspeed` + `pytorch_lightning` at module scope, coupling data extraction to training.
3. **`constants.py:20`** requires `GITHUB_ACCESS_TOKEN` and validates it over the network at import.
4. **`ExtractData.lean:261-262`** forward-slash-only path handling -> panic. *(patched above)*
5. **`cache.py:61`** shells out to `wget`: `execute(f"wget {url} -O {dirpath}.tar.gz")`. Avoid with `DISABLE_REMOTE_CACHE=1`; otherwise install wget or the remote-cache path dies. Remote cache is `https://dl.fbaipublicfiles.com/lean-dojo` (not downloaded — mathlib tarballs there are multi-GB).
6. **`trace.py:111`** — `str(p).replace("/build/lib/lean/", "/build/ir/")` never matches on Windows; produces spurious "Missing …" warnings in `check_files` (cosmetic, non-fatal).
7. **`traced_data.py:1163`** — `".lake/packages" in str(p)` never matches on Windows, so dependency files are **not filtered out**. Silent wrong behavior if the Python layer is ever used.
8. **`.dep_paths` output has mixed separators** (`.lake\packages\lean4/src/lean\Init.lean`) — parse tolerantly.
9. **elan via winget installs only the stub**; run `elan-init.exe -y` yourself.
10. **Lean DLL directory must be on `PATH`** to run any Lean-built `.exe` outside `lake env`.
11. Set `PYTHONIOENCODING=utf-8` — proof states contain `⊢` and Windows defaults to cp1252.
12. **Project discovery is not native-Windows-safe in PyPantograph 0.3.15 —
    RESOLVED 2026-08-10, no patch required.**
    Its Lake environment loader invokes POSIX `printenv LEAN_PATH`
    (`pantograph/utils.py::get_lean_path_async`), so `Server(project_path=…)`
    alone cannot discover imports from a Windows Lake project while base
    `Init` interaction works. The fix is a conditional, not a fork:
    `server.py` computes a path only when `project_path and not lean_path`, so
    **supplying `lean_path` explicitly means the `printenv` call never runs**.

    ```powershell
    cd prover\lean\proofcurve; lake build          # -> .lake\build\lib\lean\*.olean
    ```
    ```python
    Server(imports=["Init", "ProofCurve"],
           project_path=str(project),
           lean_path=str(project / ".lake" / "build" / "lib" / "lean"))
    ```

    Verified live on 2026-08-10 (ROADMAP-v0.7 item 1): 36 searches over six
    project-import theorems, with an `Init`-only control refusing the same
    propositions (`Unknown identifier 'ProofCurve.Both'`).
    `prover/live_search.PantographBackend` takes the optional `lean_path`
    argument; `prover/theorems_v1.json` declares it per backend.

    Two caveats that are NOT resolved:
    * the project must be pinned to the toolchain the bundled `repl.exe` was
      built with (4.29.1 here). The `BooleanLaws` extraction project is on
      4.32.2 — required for `ExtractData.lean`'s `String.trimAscii` — so the
      server refuses to emit `ready.` against it. `prover/lean/proofcurve/`
      side-steps this by pinning 4.29.1; nothing reconciles the two yet.
    * Lean's pretty printer does **not** unfold project `abbrev`s, so an
      imported `ProofCurve.Both P Q` stays opaque in the rendered goal. Any
      syntax-driven policy sees an atom where a conjunction stands. That is a
      useful stress, but it also means dot-notation projections must be
      *proposed and refused* rather than predicted.

---

## Next commands for phase 1 (native path)

**Strategy: drive `ExtractData.lean` directly. Do not install or import `lean_dojo_v2`.** Take the `.lean` file from the wheel, patch it, run it under `lake env lean`, and parse the resulting `.ast.json` yourself.

```powershell
# 0. Environment (per shell)
$env:Path = "$env:USERPROFILE\.elan\bin;$env:Path"
$env:PYTHONIOENCODING = "utf-8"
$env:DISABLE_REMOTE_CACHE = "1"

# 1. Get ExtractData.lean without installing the package
pip download lean-dojo-v2 --no-deps -d .\dl
Expand-Archive .\dl\lean_dojo_v2-1.0.9-py3-none-any.whl -DestinationPath .\whl -Force
# -> .\whl\lean_dojo_v2\lean_dojo\data_extraction\ExtractData.lean

# 2. Apply the separator patch (line ~261), replacing
#      let lean := olean.toString.replace ".lake/build/lib/lean/" ""
#    with
#      let lean := olean.toString.replace "\\" "/" |>.replace ".lake/build/lib/lean/" ""
#    and normalizing `let cwd ← IO.currentDir` the same way (line ~268).
#    Keep the patched copy under version control in prover/ as ExtractData.win.lean

# 3. Point the target Lean repo at a toolchain new enough for ExtractData.lean
#    (needs String.trimAscii — v4.20.0 is too old; v4.32.2 verified good)
elan toolchain install stable
Set-Content <repo>\lean-toolchain "leanprover/lean4:v4.32.2" -NoNewline

# 4. Trace
cd <repo>
lake build
$prefix = (lean --print-prefix).Trim()
New-Item -ItemType Directory -Force .lake\packages | Out-Null
robocopy $prefix .lake\packages\lean4 /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
Copy-Item <path>\ExtractData.win.lean .\ExtractData.lean
lake env lean --threads 8 --run ExtractData.lean noDeps    # omit "noDeps" to include dependencies

# 5. Harvest
Get-ChildItem -Recurse -Filter *.ast.json
#    each has {tactics: [{stateBefore, stateAfter, pos.byteIdx, endPos.byteIdx}], premises, commandASTs}
#    slice the source .lean file on the byte offsets to recover tactic text
```

**For phase 2 (interactive proof search), use PyPantograph, which is fully native:**
```powershell
git clone --recurse-submodules https://github.com/stanford-centaur/PyPantograph.git
git -C PyPantograph checkout f8aee320ee5550ea2677e414534618a61e7e1497
git -C PyPantograph submodule update --init --recursive
cd PyPantograph\src; lake build repl; cd ..
pip install .
# every shell that starts a Server needs the Lean DLLs:
$tc = "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.29.1\bin"
$env:Path = "$tc;$env:Path"
```

### If you later need the `lean_dojo_v2` Python layer (training, `TracedRepo`, benchmark generation)
That is the point to reach for **WSL2** — `deepspeed` is the blocker and it is not worth fighting. Nothing in phase 1 needs it. Note that even under WSL2 you must supply a valid `GITHUB_ACCESS_TOKEN`, and `DISABLE_REMOTE_CACHE=1` is advisable to avoid multi-GB `dl.fbaipublicfiles.com` pulls.

---

## Timeboxing notes
No single step exceeded 10 minutes. Largest downloads: Lean toolchains (~2 min each), PyPantograph submodules + `lake build repl` (~4 min). Mathlib was deliberately never fetched; `lean4-example` (2 theorems) was sufficient to exercise the full extraction path.
