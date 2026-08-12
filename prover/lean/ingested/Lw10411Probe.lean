/-
The NEGATIVE half of the ingestion probe: `lean_workbook_10411`, restated
verbatim from the same pinned extract as `Ingested.lean`
(`data_sources/derived/lean_workbook/statements.json`, HF Goedel-LM/
Lean-workbook-proofs, revision b731852af8d8ab11498fda27bce9020738c01c59, MIT).

This statement is TRUE and it is ground and decidable in principle, yet the
shipped toolchain does not prove it: `decide` on `2014^2015` exceeds Lean's
default `exponentiation.threshold` (256), so the elaborator gives up and the
declaration is closed by `sorryAx` — with exit code 0 and a warning.

It is committed, and checked, precisely because of that. Design prediction
P8(a) (docs/DESIGN-external-verifier.md) says this must be RECORDED AS A FAIL:
never silently passed on the exit code, and never rescued by raising the
threshold inside the verifier — a verifier that tunes its own options until
the check passes is not an authority. The committed verdict
`prover/verifier-verdicts/lean_workbook_10411.lean4.json` is that record, and
the axiom audit is what produces it.

No corpus node cites this file. Its verdict is a non-PASS ledger entry: it is
referenced by no manifest artifact, so it can back nothing, which is the
verdict vocabulary working as designed.
-/

theorem lean_workbook_10411 : (2014^2015) % 121 = 34 := by decide

#print axioms lean_workbook_10411
