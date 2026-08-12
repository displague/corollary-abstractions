/-
Ingested Lean-workbook statements, restated verbatim from the pinned extract
`data_sources/derived/lean_workbook/statements.json` (HF Goedel-LM/
Lean-workbook-proofs, revision b731852af8d8ab11498fda27bce9020738c01c59, MIT;
problems from Lean Workbook). Core Lean only -- no Mathlib import, so every
proof here is checkable by the pinned toolchain in `lean-toolchain`
(leanprover/lean4:v4.32.2) with no network and no cache fetch.

This file is the pinned INPUT of two authorities and must stay byte-stable:
  * scripts/external_verifier.py (backend lean4) records its sha256 in the
    committed verdict and re-checks it on `recheck`;
  * prover/ExtractData.win.lean traced it to produce
    prover/ingested_triples.json (digest-pinned in
    prover/proof-artifact-manifest.json).
Any edit invalidates both pins; that is the point of the pins.

The proof is `decide`: kernel-checked evaluation of the decidable ground
proposition. The axiom audit below prints the theorem's true footprint --
expected `[propext]`, and scripts/external_verifier.py FAILS the check if
the printed set is not contained in {propext, Classical.choice, Quot.sound}
(in particular a `sorry` would surface here as sorryAx even though the
compiler exits 0).
-/

theorem lean_workbook_1041 : 13 ∣ 2^30 + 3^60 := by decide

#print axioms lean_workbook_1041
