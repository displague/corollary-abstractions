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

## 8. Adjudication — after implementation (placeholder)

To be filled by the implementation commits; predictions above are frozen.
