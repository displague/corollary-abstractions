# Design — the external verifier and the honest `verified_by` path (ROADMAP-v0.10 item 2)

Committed BEFORE implementation. The registered predictions in §7 are floors
written down before any adjudication run; §7 also discloses exactly which
feasibility probes had already been executed when this note was written,
because a prediction registered after its experiment is not a prediction.

## 1. What the verifier IS (and is not)

`scripts/external_verifier.py` is a **transition authority**: a program the
repo can invoke that executes a named check against pinned inputs and emits a
committed verdict. It plays for candidate statements and candidate code the
role live Lean already plays for the proof curve (`prover/curve_search.py`):
the thing that says whether a proposed transition is legal, *and nothing
else*.

**The honesty boundary, stated exactly (roadmap wording): a passing check
certifies what it checks, not correctness in general.** A verdict names the
check it ran; nothing downstream may read it as more. Concretely:

- a `lean4` PASS certifies: *this pinned `.lean` source elaborates with exit 0,
  no warnings, under this pinned toolchain, and the named theorem's axiom
  footprint is inside the allowed set*. It does not certify that the theorem
  formalizes the prose statement citing it (that is the correspondence rung's
  separate, shape-only claim), and it does not certify anything about any
  other theorem in the file's future edits (the digest pin freezes the bytes).
- a `python-tests` PASS certifies: *this pinned candidate module compiles,
  passes `mypy --strict` under the recorded mypy version, and its pinned test
  module passes under the sandboxed runner*. It does not certify the candidate
  correct — only that it survived exactly those tests.
- a FAIL or REFUSED verdict certifies nothing about falsity; it records that
  this check, under this environment, did not pass (or was not run).

Two backends stand behind one interface:

- **`lean4` — live, not stubbed.** Found installed: elan 4.2.3 with toolchains
  v4.20.0 / v4.29.1 / v4.32.2 / v4.33.0 (`~/.elan`). The verifier invokes the
  pinned toolchain's `lean.exe` **directly by path** — never through the elan
  proxy — so an absent toolchain is a REFUSAL, never a network download.
  Core Lean only: **Mathlib is not installable within the hermetic budget**
  (multi-GB cache fetch, network at verification time), so statements whose
  only known proof needs Mathlib stay unbridged — that is decision (b) below,
  taken for that half only.
- **`python-tests` — live.** `py_compile` (candidate + tests) → `mypy
  --strict` (mypy 2.3.0, installed into the project venv for this slice;
  runs offline) → `unittest` in a subprocess whose runner installs a CPython
  audit hook refusing sockets, subprocesses, and writes outside the sandbox
  directory. The audit hook is a **discipline boundary, not a security
  boundary** (ctypes or a hostile C extension could evade it); the verdict
  says so in its `checks` list rather than claiming a jail.

Hybrid only at the edges: no model proposes anything here; the verifier is
pure adjudication of pinned bytes.

## 2. The interface: a verdict is never a bare boolean

One check run emits one verdict JSON (LF bytes, sorted keys, **no
timestamps** — verdicts are committed ledgers and must be byte-reproducible):

```json
{
  "schema_version": 1,
  "backend": "lean4",
  "claim": {
    "statement_id": "numbertheory.ingested.lean_workbook_1041",
    "surface": "13 ∣ 2^30 + 3^60",
    "reference": "lean_workbook_1041"
  },
  "checks": ["elaborates: exit 0, stderr empty, no warnings",
             "axiom audit: axioms ⊆ {propext, Classical.choice, Quot.sound}",
             "surface containment: claim.surface is a substring of the pinned source"],
  "inputs": {"prover/lean/ingested/Ingested.lean": "<sha256>",
             "prover/lean/ingested/lean-toolchain": "<sha256>"},
  "environment": {"toolchain": "leanprover/lean4:v4.32.2",
                  "lean_version": "<`lean --version` line>",
                  "platform": "win32"},
  "verdict": "pass",
  "evidence": {"exit_code": 0, "output_sha256": "<sha256 of captured output>"}
}
```

`verdict` ∈ {`pass`, `fail`, `refused`}. REFUSED is for checks that could not
run (missing toolchain, unpinnable input, digest mismatch against an expected
pin); FAIL is for checks that ran and did not pass. Both are first-class:
a refusal is recorded, never silently skipped.

CLI: `check` (run a backend, write a verdict), `recheck <verdict>` (re-hash
every pinned input, re-run the same backend, and compare — divergence is
nonzero exit), `ledger` (validate every committed verdict + manifest chain,
see §3). Hermetic rules for every mode: inputs must be repository-contained
(same `resolve_contained_artifact` boundary the proof artifacts use), no
network (lean by direct toolchain path; python under the audit hook; mypy
offline), environment recorded in the verdict.

## 3. How a verdict becomes a `verified_by` entry — or is refused

**A verdict alone never mints a `verified_by` link.** The link vocabulary is
unchanged this slice: `system` stays `lean4`-only in
`validate_nodes.verified_by_errors`, and the link shape stays frozen at
`{system, artifact, reference}`. The chain for an ingested statement is:

1. the pinned Lean source (`prover/lean/ingested/Ingested.lean`) proves the
   theorem; the **external verifier** emits a PASS verdict over its digest;
2. the **tracer** (`prover/ExtractData.win.lean`, the phase-1 route) extracts
   the real state–tactic–state transitions from the same pinned source into a
   committed transition-row artifact (`prover/ingested_triples.json`);
3. the artifact is **digest-pinned** in `prover/proof-artifact-manifest.json`,
   whose entry now also names its `source` (the .lean file) and its
   `verdicts` (the committed verdict paths) — additive fields; existing
   consumers (`write_stage`, `retrieval`) read only `sha256`/`authority`;
4. the node cites `{system: lean4, artifact, reference}` exactly as the 16
   existing links do; `verified_by_errors` re-checks provenance (containment,
   complete transitions, closure to `no goals`, exclusive ownership);
5. `proof_correspondence` re-checks SHAPE — extended this slice with a
   ground-arithmetic fragment (§5) so the new link is CORRESPONDS rather than
   UNTRANSLATABLE.

The validator gains a **re-check rung** (`external_verifier.verdict_ledger_errors`,
wired into `validate_nodes.py` main): every committed verdict must parse, be
internally complete, have every pinned input present with matching sha256, and
every manifest `verdicts` reference must point at a PASS verdict whose
`claim.statement_id` equals the statement that cites that artifact. Fail
closed on all of it. A passing check on the WRONG statement must not attach:
if node X cites an artifact whose verdict claims statement Y, that is an
error, symmetric to the existing capability-blind control in
`tests/test_verified_by.py`.

Refusals that keep a verdict OUT of `verified_by`: verdict ≠ pass; digest
drift between verdict and committed bytes; claim/citer mismatch; a backend
other than `lean4` (a `python-tests` verdict is a committed, recheckable
authority for a computational claim, but it does not enter the corpus's
`verified_by` vocabulary this slice — that is roadmap item 3's decision to
make, with its own design note).

## 4. The either/or decision: HYBRID, argued

Roadmap item 2 offers (a) extend the correspondence rung to the arithmetic
fragment and bridge one Lean-workbook proof end-to-end, or (b) document that
ingested theorems stay `formal` without a bridge, at node level.

**Decision: (a) for the core-Lean-decidable fragment, (b) for the
Mathlib-dependent remainder, each recorded where it applies.**

- (a) is executed for `lean_workbook_1041` (`13 ∣ 2^30 + 3^60`, from the
  pinned Lean-workbook extract `data_sources/derived/lean_workbook/
  statements.json`, source manifest-pinned at HF revision `b731852…`, MIT).
  It is ground divisibility over ℕ — decidable in **core Lean** by `decide`,
  no Mathlib — so the full chain of §3 is buildable today with the toolchain
  actually present. One statement, end to end, is the acceptance bar.
- (b) is recorded at node level for `lean_workbook_10202`
  (`2^21 ≡ 1 [ZMOD 7]`): `ZMOD` is Mathlib's `Int.ModEq` notation; core Lean
  cannot even parse it, and Mathlib is outside the hermetic budget. The node
  enters the corpus as `epistemic_status: "formal"` with NO `verified_by`
  link and carries the written record (in `semantic_interpretation`) of
  exactly why: *formal-without-bridge, decision (b) of this design, because
  its proof requires Mathlib and the repo's verifier is core-Lean-only.*
  Every future ingested node without a bridge must carry the same record.

Why not (b) everywhere (simpler)? Because the toolchain IS present and a
real bridge IS reachable — taking (b) wholesale would document a limitation
the environment does not have. Why not (a) everywhere? Because pretending
the Mathlib fragment is bridgeable would either stall the slice on a
multi-GB non-hermetic install or, worse, tempt a hand-written "transition
artifact" no Lean run produced. The hybrid states each boundary where it
actually lies.

## 5. The correspondence rung's ground-arithmetic fragment

`proof_correspondence.py` currently translates only goals whose hypotheses
all bind `Prop` names. A second, **disjoint** fragment is added: a goal state
with **zero hypothesis lines** whose goal text consists only of numerals and
`+ * ^ % ∣ = ( )` translates to the corpus template grammar as ground
arithmetic — `∣` → `DIVIDES(l, r)`, `%` → `MOD(l, r)` (already declared
`ordered_compose` in the head algebra), `+ * ^` as the matcher's own
operators, numerals as numeric literals. A bare proposition is normalised to
`<expr> = TRUTH` by the same `as_equation` rule as the propositional side.
The two fragments cannot collide: one requires Prop binders, the other
refuses any hypothesis line and any letter.

Deliberate refusals, carrier-honesty (the v0.9 `Nat.div` lesson): `-` (Nat
subtraction is monus), `/` (Nat division is floor division), order relations
(`< ≤`), and any identifier — all UNTRANSLATABLE, never guessed. Every
operator admitted is one whose corpus reading and Lean reading coincide on
ground ℕ terms. Comparison stays skeleton-equality via the matcher's own
front end; ground templates have no slots, so a match here is exact
structural identity of the ground equation — and a wrong literal (the decoy
`DIVIDES(7, …)`) is a MISMATCH, not a near-miss.

## 6. Artifacts and layout

```
docs/DESIGN-external-verifier.md          this note (committed first)
scripts/external_verifier.py              the authority (check / recheck / ledger)
prover/lean/ingested/{lakefile.toml,lean-toolchain,Ingested.lean}
                                          pinned core-Lean project (v4.32.2)
prover/ingested_triples.json              traced transition rows (tracer, not hand-written)
prover/verifier-verdicts/*.json           committed verdicts (LF, deterministic)
prover/proof-artifact-manifest.json       + entry: sha256, authority, source, verdicts
scripts/seed_number_theory.py             + 2 ingested nodes (1041 bridged, 10202 (b)-recorded)
scripts/proof_correspondence.py           + ground-arithmetic fragment
scripts/validate_nodes.py                 + verdict-ledger rung in main()
tests/test_external_verifier.py           verdict honesty, hermetic refusal, negative
                                          controls, recheck path
```

Corpus counts move 251 → 253 (README, `test_matcher_mirror`,
`test_verified_by` CLI pin); links 16 → 17. If the GC4/GC5 pins move, a
FOURTH registered acknowledgment is appended to `test_decompose_channels.py`
— never touching the prior three; if they do not move, none is written.

## 7. Registered predictions (floors), and what was already probed

Disclosure: before this note was written, three feasibility probes ran in a
scratch directory (no repo artifacts): (i) `13 ∣ 2^30 + 3^60 := by decide`
elaborates under core v4.32.2 with axioms `[propext]`; (ii) the `ZMOD`
statement fails to parse under core v4.32.2; (iii)
`(2014^2015) % 121 = 34 := by decide` FAILS under default options
(`exponentiation.threshold 256` → `sorryAx`). P1, P2 and P8a are therefore
*confirmations being pinned*, not blind predictions; the rest are registered
blind, before any implementation exists.

Named test set: T1 = `lean_workbook_1041`, T2 = `lean_workbook_10411`,
T3 = `lean_workbook_10202`, plus the mutations named below.

- **P1** (probed): `lean4` backend PASSES T1's pinned source; axiom audit
  reports exactly `[propext]`. The verdict's `checks` list names elaboration
  + axiom audit + surface containment and nothing more.
- **P2** (probed): T3 under the core toolchain FAILS (parse error); the
  committed record is the node-level (b) statement, and no machinery — not
  the verifier, not the seed, not the validator — upgrades T3 past `formal`.
- **P3** (blind): the wrong-statement mutation `14 ∣ 2^30 + 3^60 := by
  decide` (a FALSE claim) FAILS: `decide` evaluates to false, lean exits
  nonzero, verdict `fail`. The verifier never converts a failing check into
  anything but `fail`.
- **P4** (blind): a `sorry` proof of the TRUE T1 statement is caught by the
  axiom audit (`sorryAx` in the axiom set) even where the compiler exit code
  alone would pass it (exit 0 + warning). Verdict `fail`, reason names the
  axiom.
- **P5** (blind): `python-tests` PASSES the pinned computational check of T1
  (`(2**30 + 3**60) % 13 == 0` under pinned unittest); FAILS the mutated
  test asserting `% 14 == 0`; REFUSES/FAILS a candidate that attempts
  `socket.getaddrinfo` or a write outside the sandbox directory, with the
  audit event named in the verdict.
- **P6** (blind): correspondence — the new T1 link is CORRESPONDS via route
  `canonical`, `ambiguous_with` EMPTY (no other node declares this ground
  skeleton); all 16 existing links keep byte-identical verdict+route; a decoy
  node declaring `DIVIDES(7, 2 ^ 30 + 3 ^ 60)` citing T1's theorem is
  MISMATCH.
- **P7** (blind): the validator ledger rung fails closed on each of:
  (i) verdict input digest ≠ committed bytes, (ii) manifest `verdicts` entry
  whose verdict is not `pass`, (iii) PASS verdict whose `claim.statement_id`
  differs from the citing node (wrong-statement attach), (iv) missing verdict
  file. Each is one test.
- **P8** — what the verifier will NOT certify on the named set:
  (a, probed) T2 under shipped options — recorded FAIL, never silently
  passed and never proved by raising options inside the verifier;
  (b) truth of any statement beyond the executed check; (c) semantic
  correspondence (that stays the correspondence rung's separate shape-only
  verdict); (d) anything Mathlib-dependent.
- **P9** (blind): corpus growth 251 → 253 moves no `group_counts` bucket
  (both new skeletons are ground and twin-less). GC4 aggregate movement, if
  any, is small and same-corpus-dominated; adjudicated against the pin file,
  with the acknowledgment appended only if a pin actually moves.

Adjudication of P1–P9 lands in this file's §8 after implementation, exact to
the row.

## 8. Adjudication — after implementation

§7 above is frozen as registered. Every prediction landed as written; two
things the design did NOT say are disclosed at the end, in the house style
(the registered text is never edited to match the outcome).

| # | outcome | where it is checked |
|---|---|---|
| P1 | **CONFIRMED** — `verdict: pass`, `evidence.axioms == ["propext"]`, three `checks` and no more | `prover/verifier-verdicts/lean_workbook_1041.lean4.json`; `test_external_verifier.VerdictObjectHonesty` |
| P2 | **CONFIRMED** — T3 unbridged, `formal`, reason written into the node | `test_the_mathlib_node_stays_unbridged_and_says_why` |
| P3 | **CONFIRMED** — `14 ∣ 2^30 + 3^60` elaborates to a `decide` failure, verdict `fail` | `LeanNegativeControls.test_false_statement_fails` |
| P4 | **CONFIRMED** — `sorry` on the TRUE statement exits 0 with a warning and is caught by the axiom audit naming `sorryAx` | `test_sorry_fails_on_the_axiom_audit` |
| P5 | **CONFIRMED** — pinned check passes; `% 14` mutation fails; `socket.getaddrinfo` and an out-of-sandbox write are refused with the audit event named in `evidence.sandbox_refusals` | `PythonNegativeControls` (4 tests) |
| P6 | **CONFIRMED exactly** — the ingested link is CORRESPONDS via `canonical`, `ambiguous_with` empty, the prior 16 links keep byte-identical verdict+route, and the `DIVIDES(7, …)` decoy is MISMATCH | `GroundArithmeticFragmentTests` (11 tests) |
| P7 | **CONFIRMED** — all four fail-closed paths, one test each | `AttachRule` (5 tests) |
| P8a | **CONFIRMED, and now committed as a record** — see the disclosure below | `prover/verifier-verdicts/lean_workbook_10411.lean4.json`; `CommittedNegativeRecord` |
| P9 | **CONFIRMED** — `group_counts {30, 31, 30, 32, 5}` unchanged, a FIFTH consecutive twin null; GC4 moved and the FOURTH acknowledgment was appended | `test_matcher_mirror`; `test_decompose_channels` docstring |

**The GC4 movement, exactly.** Mean groundedness 0.781 → 0.774, external
channel mean 0.494 → 0.490, external lower 0.223 → 0.221, and at
`min_family=1` recursive 244 → 250 over 126 → 128 statements. NOT ONE
constituent moved on any channel (exact stays 531, pattern 99,
statements-with-constituents 222); both ingested nodes are fully ground and
own nothing, so they contribute groundedness 0.0 and every per-statement
mean shifts by exactly the two added zeros. Pure denominator dilution — the
adjudication is in the acknowledgment appended to
`tests/test_decompose_channels.py`, which is where it has to survive.

**Disclosure 1 — the committed FAIL verdict carried machine paths.** §2 said
verdicts must be byte-reproducible and named the two hazards it had thought
of (timestamps, key order). It missed a third: Lean prints the ABSOLUTE
source path in every diagnostic, so the first `lean_workbook_10411` verdict
written embedded this checkout's home directory in `evidence.reason` and
`evidence.output_tail`, and its `output_sha256` would have differed on every
clone even where the outcome was identical. Fixed in
`external_verifier._relativize`: the pinned inputs' own absolute paths are
folded back to the repository-relative names the verdict already pins (and
the python sandbox's scratch directory to a fixed token) before anything is
digested or recorded — nothing else in the tool's output is rewritten, so a
diagnostic naming some other file stays visible as itself. Both PASS
verdicts regenerate byte-identically across the change, which is the
evidence that the fold touched only failing output.
`LedgerBytesArePortable` is the regression.

**Disclosure 2 — "recorded FAIL" had nowhere to live.** P8(a) promised T2
would be *recorded* as a FAIL, and the implementation as first landed
recorded it only in this note's prose. A ledger that contains nothing but
passes is not a ledger, so the negative is now a first-class committed
entry: `prover/lean/ingested/Lw10411Probe.lean` (the statement restated
verbatim from the same pinned extract, with no `set_option` escape hatch)
and its FAIL verdict, which sits in the ledger, re-hashes green, and is
referenced by no manifest artifact — so it can back nothing. That is the
`{pass, fail, refused}` vocabulary of §2 doing the job it was declared for.

**Disclosure 3 — the sandbox's write rule had a hole, and it fired.** §1
called the audit hook a discipline boundary and named ctypes and hostile C
extensions as its known evasions. The hole that actually mattered was
neither: the `open` audit event carries `(path, mode, flags)` and the MODE
IS `None` for every low-level open — `os.open`, `_io.FileIO`, and CPython's
own bytecode-cache writer — while the hook read only the mode. This was not
hypothetical. A `python-tests` run with a cold cache **wrote `__pycache__`
into the repository** and still reported PASS, under a `checks` line that
claims writes outside the sandbox are refused. The rule now reads the flags
as well, and the runner is invoked with `-B` so no legitimate check needs
that write; the committed verdict's evidence digest is byte-identical across
the fix, and the cold-cache run is now the same run as the warm one. Two
regressions pin it. The discipline-boundary caveat still stands as written —
it was just not the reason this one leaked.

**Disclosure 4 — the ingested link touched three existing pins.** §6
predicted the corpus-count pins (README, `test_matcher_mirror`,
`test_verified_by`) and the link count. It did not anticipate that three
tests iterating the correspondence `EXPECTED` table assume ONE artifact file
and that every CORRESPONDS link has a structural twin: the ingested link
lives in its own traced artifact and has no twin at all. Fixed by giving the
table an explicit `ARTIFACT_OF` map and stating the no-twin case as its own
assertion rather than an exemption — both are P6's own predictions turned
into checks, but the need for them was discovered, not foreseen.
