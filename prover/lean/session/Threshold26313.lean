/-
The statement the v0.10 item 5 session tries second and does NOT get to
author: `lean_workbook_26313`, restated verbatim from the same pinned extract
as `Session22080.lean`.

It is TRUE, it is ground, and it has the same shape as the statement the
session just bridged — `<numeral> ^ <numeral> % <numeral> = <numeral>`. The
only difference is the exponent: 2006 is above Lean's default
`exponentiation.threshold` (256), so `decide` does not evaluate and the
declaration closes with `sorryAx`. The compiler's exit code alone would let
that through; the external verifier's axiom audit is what does not.

Committed so the session's refusal leg runs against a real file rather than
a described one. Nothing cites it, and by design nothing can: its verdict is
not a PASS, so no manifest artifact may name it and no node may be minted
from it. Same-shape-but-refused is the pair worth keeping next to each other.
-/

theorem lean_workbook_26313 : (2^2006) % 7 = 4 := by decide

#print axioms lean_workbook_26313
