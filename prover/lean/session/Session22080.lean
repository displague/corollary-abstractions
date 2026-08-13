/-
The statement the v0.10 item 5 session authors end to end, restated verbatim
from the pinned extract `data_sources/derived/lean_workbook/statements.json`
(HF Goedel-LM/Lean-workbook-proofs, revision
b731852af8d8ab11498fda27bce9020738c01c59, MIT; problems from Lean Workbook).

`lean_workbook_22080` is ground and decidable in CORE Lean — no Mathlib —
and it is deliberately a `%` statement where the first ingested bridge
(`Ingested.lean`, lean_workbook_1041) was a `∣` statement: the correspondence
rung's ground-arithmetic fragment declares both DIVIDES and MOD, and only
one of them had ever carried a node end to end.

This file is the pinned INPUT of two authorities and must stay byte-stable:
`scripts/external_verifier.py` records its sha256 in the committed verdict
and re-checks it on `recheck`, and `prover/ExtractData.win.lean` traced it to
produce the committed transition rows. Any edit invalidates both pins.

Exponent 30 is far below Lean's default `exponentiation.threshold` (256), so
`decide` evaluates rather than giving up — the boundary that made
`lean_workbook_10411` a committed FAIL in item 2, and that the session's
second leg deliberately walks into again.
-/

theorem lean_workbook_22080 : (2^30) % 1000 = 824 := by decide

#print axioms lean_workbook_22080
