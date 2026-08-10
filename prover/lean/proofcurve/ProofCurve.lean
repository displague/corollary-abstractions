/-
Project-import family for the v0.7 proof-search curve.

These declarations exist so that a held-out theorem can be *unstatable*
without a project import: `Server(imports=["Init"])` alone cannot elaborate
`ProofCurve.Both P Q`, so a solved run over this family is evidence that live
search reached beyond Lean's `Init` prelude.

They are `abbrev`, not `def`, on purpose: dot-notation projection
(`h.left`) resolves through a reducible definition, so the SAME eight tactic
schemas that cover the `Init` families also cover this one. Adding a schema
here would have confounded "project imports work" with "a bigger palette
works".
-/

namespace ProofCurve

/-- A project-owned name for conjunction. -/
abbrev Both (P Q : Prop) : Prop := P ∧ Q

/-- A project-owned name for disjunction. -/
abbrev Either (P Q : Prop) : Prop := P ∨ Q

/-- A project-owned name for a bare proposition. -/
abbrev Holds (P : Prop) : Prop := P

end ProofCurve
