/-
B-P — the identity witness of DESIGN-foreign-voice §3.2.

This program elaborates a term under the pinned toolchain and prints a
**binder-name-independent** serialization of the resulting `Expr`: constructor
tags, de Bruijn indices, constant names and universe levels, with the `Name`
field of every `forallE`, `lam` and `letE` DROPPED.

Binder-name independence is therefore a property of `ser`'s type, not of a
normalization pass over text.  Nothing downstream has to trust that a renamer
was applied correctly, because the name never reaches the string.  That is
what lets the loanword lexicon erase identifiers to slot indices without
putting information in a sentence that the gate cannot see.

## Hermetic rule, unchanged from the one the verifier already enforces

`import Lean` only.  No lake, no Mathlib, no network.  The pinned v4.32.2
binary is invoked DIRECTLY BY PATH by `scripts/foreign_voice_oracle.py`, which
resolves it through `external_verifier.toolchain_binary` and REFUSES rather
than downloading when it is absent.  This file is never compiled to an
`.olean` and never imported: the driver concatenates it with the `#ser`
commands into one temporary source file, so there is no build system to pin
and no artifact to go stale.

## Every term answers, and answers under its own tag

`#ser "tag" => term` prints exactly one line beginning `FVSER <tag> ` on
success and exactly one line beginning `FVERR <tag> ` on failure, because
elaboration errors are caught here rather than left to the frontend's
diagnostics.

That is a deliberate correction of how the B0 eligibility probe had to work.
That probe attributes diagnostics to statements BY LINE NUMBER, which made it
vulnerable to anything that suppresses a diagnostic — and the frontend's
100-error cutoff did exactly that, reporting 2,982 eligible against a truth of
2,319 until the option was frozen and the cutoff detected.  Here there is
nothing to attribute: the tag is in the payload.  A tag with no line at all is
a *parse* failure, which no elaborator can catch, and the driver reports it as
one rather than inferring silence means success.

`Term.withoutErrToSorry` is load-bearing: without it, `elabTerm` turns an
elaboration error into `sorryAx` and returns a term, so the serializer would
happily digest a proposition the corpus never wrote and B1 would compare two
elaborations of an error.

## What this file does NOT do

It does not check, prove, or evaluate anything.  A serialization is not a
verdict; `scripts/external_verifier.py:6–7` governs and this cycle mints no
`verified_by` links.  `#print axioms` is not invoked here and no `sorry`
appears in any term this program serializes.
-/

import Lean
open Lean Elab Command Meta

set_option autoImplicit false
set_option relaxedAutoImplicit false

namespace ForeignVoice

/-- The serialization.  Total, deterministic, and binder-name-free.

Every constructor of `Expr` is matched explicitly rather than through a
catch-all, so a future toolchain that adds one is a compile error here instead
of a silently-dropped subterm.  `mdata` is transparent: it carries elaborator
annotations, not meaning, and keeping it would make the witness depend on
which annotations the elaborator happened to attach. -/
partial def ser (e : Expr) : String :=
  match e with
  | .bvar i          => s!"(bv {i})"
  | .fvar _          => "(fv)"
  | .mvar _          => "(mv)"
  | .sort u          => s!"(sort {u})"
  | .const n us      => s!"(const {n} {us})"
  | .app f a         => s!"(app {ser f} {ser a})"
  | .lam _ t b _     => s!"(lam {ser t} {ser b})"
  | .forallE _ t b _ => s!"(all {ser t} {ser b})"
  | .letE _ t v b _  => s!"(let {ser t} {ser v} {ser b})"
  | .lit l           => s!"(lit {repr l})"
  | .mdata _ b       => ser b
  | .proj n i b      => s!"(proj {n} {i} {ser b})"

/-- One line per tag, always, so nothing has to be attributed by position. -/
def flatten (s : String) : String :=
  (s.replace "\n" " ").replace "\r" " "

end ForeignVoice

/-- `#ser "tag" => term` — elaborate and serialize, or report why not.

The two rejections after `instantiateMVars` are not tidiness.  `ser` maps
EVERY `.mvar` to the constant string `(mv)`, so a term that still carries an
unassigned metavariable is serialized to a string that erases which
metavariable it was: `#ser "a" => (1 2 3)` and `#ser "b" => (4 5 6 7)` are
different propositions and would digest identically.  A witness that says two
different things are the same is worse than no witness, so a residual
metavariable REFUSES.

`hasSorry` is the same failure by the other door.  `withoutErrToSorry` stops
`elabTerm` from turning its own errors into `sorryAx`, but a term whose SOURCE
contains `sorry` still elaborates cleanly to one — and every such term shares
the same `sorryAx` skeleton, so they too would collide.  Nothing in this cycle
serializes a proof, and this is where that is enforced rather than assumed. -/
elab "#ser " tag:str " => " t:term : command => do
  liftTermElabM do
    let name := tag.getString
    try
      let e ← Term.withoutErrToSorry (Term.elabTerm t none)
      Term.synthesizeSyntheticMVarsNoPostponing
      let e ← instantiateMVars e
      if e.hasExprMVar then
        logInfo s!"FVERR {name} residual metavariable: the elaborated term is \
          not fully determined, and every such term serializes to the same (mv)"
      else if e.hasSorry then
        logInfo s!"FVERR {name} the elaborated term contains sorryAx; nothing \
          in this cycle serializes a proof"
      else
        logInfo s!"FVSER {name} {ForeignVoice.ser e}"
    catch ex =>
      let msg ← ex.toMessageData.toString
      logInfo s!"FVERR {name} {ForeignVoice.flatten msg}"
