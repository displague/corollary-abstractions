/-
GROUNDING PROTOTYPE -- not the B-P deliverable.

Built and run 2026-08-23 during the reality inspection for
docs/DESIGN-foreign-voice.md, to answer one question before the design
assumed the answer: can the PINNED toolchain emit a binder-name-independent
serialization of an elaborated term, under the hermetic rule the external
verifier already enforces?

It can. Run with the pinned v4.32.2 `lean` binary invoked DIRECTLY BY PATH
(no elan proxy, no lake, no Mathlib, no network):

    ~/.elan/toolchains/leanprover--lean4---v4.32.2/bin/lean Serialize.prototype.lean

Binder-name independence is a property of `ser`'s type, not of a
normalization pass over text: the `Name` field of every `forallE`, `lam`
and `letE` is dropped and de Bruijn indices carry the binding structure.
The four outputs below pair up byte-identically:

  #1 = #2  475 chars, sha256 25ec23fb13b33120...   (p q  vs  zzz www)
  #3 = #4  2627 chars, sha256 f89095af7546ebd1...  (a b c vs x y z, and
                                                    differing whitespace)

This file is retained per the v0.19 adversarial review (H4) so the design's
quoted digests are reproducible rather than remembered. B-P still owes the
real artifact: prover/lean/normalizer/Serialize.lean, with tests, a Python
driver, and the two pairs above as its first two test cases.
-/

import Lean
open Lean Elab Command Meta
set_option autoImplicit false

partial def ser (e : Expr) : String :=
  match e with
  | .bvar i        => s!"(bv {i})"
  | .fvar _        => "(fv)"
  | .mvar _        => "(mv)"
  | .sort u        => s!"(sort {u})"
  | .const n us    => s!"(const {n} {us})"
  | .app f a       => s!"(app {ser f} {ser a})"
  | .lam _ t b _   => s!"(lam {ser t} {ser b})"
  | .forallE _ t b _ => s!"(all {ser t} {ser b})"
  | .letE _ t v b _ => s!"(let {ser t} {ser v} {ser b})"
  | .lit l         => s!"(lit {repr l})"
  | .mdata _ b     => ser b
  | .proj n i b    => s!"(proj {n} {i} {ser b})"

elab "#ser " t:term : command => do
  liftTermElabM do
    let e ← Term.elabTerm t none
    Term.synthesizeSyntheticMVarsNoPostponing
    let e ← instantiateMVars e
    logInfo (ser e)

#ser (∀ p q : Nat, p + q = q + p)
#ser (∀ zzz www : Nat, zzz + www = www + zzz)
#ser (∀ a b c : Rat, 9 * (a ^ 3 + b ^ 3 + c ^ 3) ≥ (a + b + c) ^ 3)
#ser (∀ x y z : Rat, 9*(x^3+y^3+z^3) ≥ (x+y+z)^3)
