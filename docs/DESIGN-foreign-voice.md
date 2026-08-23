# The loanword: the graph speaks a dialect it cannot read

**Status: design only.** Nothing here is implemented. First slice targets
v0.19, **selected by the outside design course** whose receipt is
`reports/design-direction-v0.19.json` and whose brief is committed beside
it as `reports/design-direction-v0.19-brief.txt` — the brief's
LF-canonical sha256 is `ddd55f3f7aa139e0…`, which is the value the receipt
already pinned as `brief_sha256_canonical_lf`, so the text the advisors
were given is on file rather than described. This is the course that
[ROADMAP-v0.18](ROADMAP-v0.18.md):226–233 requires to be *invoked*, not
reaffirmed, after two consecutive maintainer-directed headlines. Series 1
led with LOANWORD; the selection and every declined direction's
disposition are in §2.

This document is the second half of that gate: the course's final form was
the outline, and everything below has been checked against the committed
tree before being written down. **Four of the advisor's load-bearing
assumptions did not survive that check**, and a fifth failure — the shape
of the identity claim itself — was found by the adversarial review of this
document's first draft (§3.2, C-V4). All are corrected in place, dated,
with the measurement that corrected them, because a design that inherits
an outside idea without inspecting the machine it will run on is how a
course becomes a wish.

## 1. The boundary being moved, and what a person gains

v0.18 gave the kernel a voice for the terms it can parse. The registered
run put the round-trip rate at **0.9991 — 2,170 of 2,172 parseable terms**
(`experiments/realization_rate.json:697–704`), with zero round-trip
failures and two honest refusals. That result is the floor this design
stands on. It is also the result that names the problem: **2,172 of 12,777
is 17.0%.** The other **10,605 nodes (83.0%)** carry a
`formal_statement.canonical_ascii` the committed parser cannot read, and
for them `answer.render` still serves the ingestion disclaimer over
machine boilerplate. The corpus's mass is mute.

The advisor's proposal was to make it speak by borrowing: render English
from a frozen hand-authored lexicon over the *foreign* dialect's
constructors, and gate the rendering by feeding its literal inverse to the
**already-pinned external Lean checker**, using the checker's elaborated
term as the identity witness. The mechanism is sound and it is what §3
builds. But the shape of the 83% is not what the proposal assumed, and the
pinned checker is not the instrument the proposal assumed either.

> **Correction 1 (2026-08-23, grounding, before implementation): half the
> "foreign dialect" is the same grammar in a different alphabet.** A
> measurement over the committed tree: of the 10,605 mute statements,
> **6,414 parse under the byte-frozen committed parser after substituting
> exactly two glyphs** — `≥`→`>=` and `≤`→`<=`. That is **50.2% of the
> whole corpus**, mute for want of two rows in
> `scripts/match_signatures.py:287–289`'s ASCII-only `TOKEN_RE`, not for
> want of a bridge to another language. Calling those statements foreign
> and rendering them through a loanword pipeline would let this cycle
> claim a hard result for easy territory. They are excluded from the
> claim, named as **transliterable**, and handed to the roadmap as
> tokenizer work under v0.18's existing native path (§10 item 3a), with the
> ordering discipline §5 fixes so the two cycles cannot contaminate each
> other's numbers.
>
> **What is left is the design's actual territory: the 4,191-statement
> foreign residue (32.8% of the corpus)** — statements the parser cannot
> reach at any alphabet, because they carry quantifiers and typed binders
> (`∀ a b c : ℝ,`), logical connectives (`∧ ∨ ↔ → ¬`), type ascriptions
> (`(4:ℝ)`), and namespaced heads (`Real.sqrt`). **4,060 of the 4,191 are
> `lean_workbook.ground.v1`; the remaining 131 spread across 23 other
> corpora**, led by `logic.boolean_foundations.v1` (20 of 20) and
> `temporal_logic.linear_time.v1` (15 of 16). **Five corpora are mute in
> full** — nothing in them parses at all: `logic.boolean_foundations.v1`
> (20), `programming.core.v1` (9), `provability.goedel_loeb.v1` (6),
> `algebra.foundations.v1` (1), `ingested_arithmetic.session.v1` (1).

**What a person gains,** stated at the corrected scale. Today the answer
surface can say a proposition out loud for 17.0% of the graph. If this
design fires, it can say one out loud for the part of the remainder the
pinned oracle can adjudicate — and, for everything else, it can say
*exactly why not*, per construct, with a count. That second half is the
headline. A system that renders 60% of a corpus and shrugs at the rest has
told you nothing about the rest; a system that renders what it can and
hands you a frozen, digested inventory of what it cannot, with the
blocking construct named and counted, has told you the shape of its own
silence. Both skins inherit it through A-IH6 the moment the engine has it
(DESIGN-interactive-harness §4.3), and the capability sheet gains a row —
no new HTTP surface.

## 2. Why this direction survived, and every direction that did not

The v0.19 course ran three isolated series of three constraint rounds
each, under the isolation mode inherited unchanged from v0.17
(`reports/design-direction-v0.19.json`: headless `claude -p`, cwd an empty
non-git directory whose path carries no project name, strict MCP config
plus a denylist over every file, shell, network, agent and skill tool;
residual gap recorded — the tools exist and are blocked, not absent).
Cross-series exclusion was enforced in the hashed round-one prompts:
series 2 excluded series 1's five lines, series 3 excluded all ten. The
incumbent — [DESIGN-block-vocabulary](DESIGN-block-vocabulary.md), carrying
the maintainer's standing instruction recorded verbatim at
`docs/DESIGN-block-vocabulary.md:3–12` that it be *"taken through the
design loop, but not simply disregarded"*, and that **"Silence is not a
disposition"** — was withheld at round one and disclosed abstractly at
round two. All fifteen round-one directions differentiated from it
unprompted.

**Selected.** *LOANWORD* — the foreign-dialect voice with the pinned
checker as oracle, dual controls, and the untranslatable register as a
co-equal artifact rather than an appendix. It won on three counts the tree
confirms: it is the only direction whose claim is *falsifiable by an
authority this repository already trusts and did not build*; it addresses
the largest measured gap in the product surface (83.0%, and the corrected
32.8% after Correction 1); and its headline artifact is an inventory of
failure, which is the one kind of artifact this project has never been
able to fake.

**Adopted, not displaced.** *The incumbent.* DESIGN-block-vocabulary is
**adopted as bounded roadmap item 2** — the address-space probe with its
falsifiers pre-registered, held to its own §4 bar: beat the existing
keyword channel at its measured floors for retrieval, beat
zstd-with-shared-dictionary for compression, beat the canon token encoding
at 8.4× for the model leg, or park with the numbers
(`docs/DESIGN-block-vocabulary.md:294–299`). Its §4 sequencing bullet
(`:300–303`) already names the dependency this cycle satisfies: R0's
parse-rate table is input to any block-vocabulary denominator, and §6's
B0a/B0bc extend that table into the mute set. The maintainer's
no-silent-disposal instruction is discharged by adoption, in writing,
here.

**Declined, each with its disposition** — the no-proposal-wasted rule. The
first six dispositions are the course's own, recorded in the receipt's
`selection.declined`; the remaining seven are **this document's**, written
because a direction that dies at round one still earned a sentence, and
marked as the writer's so nobody mistakes them for advisor reasoning.

*From the receipt:*

- **FORK** (series 2 lead — counterfactual seed rebuild served as a diff):
  parked with a named trigger — it wants the voice layer first so its
  diffs are readable. Its residual risk, *mechanically perfect and
  semantically misnamed*, is partially priced by this design's register
  vocabulary.
- **TWO RIGHTS** (series 3 lead — served convention forks from co-present
  statements): its one-hour B0 grep is **adopted as a registered probe
  inside v0.19** (§10); the full direction waits on which branch the probe
  takes.
- **TWO-STEP** (series 1 runner-up — composed answers with per-step
  licensed receipts): parked, with its one-afternoon hand-probe named as a
  future cheap gate.
- **STRANGER** (outside askers scoring answers and refusals): gap-object
  intake parked to BACKLOG with the degradation rule quoted.
- **DEADLINE** (p99.9 latency contract with typed in-budget refusal):
  parked; near-zero marginal cost noted for a slack slice, since the
  stopwatch already exists (`scripts/measure_throughput.py`).
- **THE GRADED NO** (series 3 runner-up, NO SUCH THING + FINE PRINT
  merged): parked; the licensed-negative answer-type recorded as the
  strongest new-vocabulary candidate on file.

*Written here (2026-08-23):*

- **RUNNABLE** (statements compiled to evaluators of user quantities):
  parked — it needs the parseable denominator to be large, and R0 put that
  at 17.0%; it becomes cheap the moment the foreign residue is readable,
  which is the successor question this design names in §10.
- **SIDECAR** (user-owned graph layers through the write gate): parked to
  BACKLOG against DESIGN-write-append; it is a storage-authority
  direction, and the substrate's multi-owner storage is explicitly
  unsolved (DESIGN-grounded-throughput §2).
- **REDLINE** (the graph checks others' prose per-span): parked — its
  input side is open English, which DESIGN-text-resolution's FP floor of
  0.030 and DESIGN-sans-template-rendering §3's carve-out both put outside
  reach this cycle.
- **NEGATIVE SPACE** (typed refusals scored on consequence): folded into
  THE GRADED NO's park by the advisors' own disclosed collision with
  STRANGER's gap objects; the untranslatable register in §3.3 is the
  narrow, testable version of its idea and is shipping.
- **EXAMINER** (the graph examines a person): declined outright — it
  requires a human-subject apparatus, and a sweep of the tree returns none
  (Correction 4). A direction whose cheapest gate needs machinery the
  repository has never built is not a next cycle.
- **ROSETTA TRANSPORT** (method transport across twin skeletons): parked
  as the nearest neighbour of the *cross-layer same-statement discovery*
  question this design names as its own successor; running both at once
  would make neither falsifiable.
- **CONJECTURE FOUNDRY** (prover-certified self-originated statements):
  declined for this cycle on a hard tree fact — certification depends on
  the same pinned checker, and Correction 2 shows that checker carries no
  Mathlib heads. A foundry that can only conjecture inside core Lean's
  head vocabulary is a smaller idea than it sounds, and it should be
  reopened after the Mathlib budget question is decided, not before.

## 3. The first-class objects — three, and the third is co-equal

### 3.1 The loanword lexicon and the render path

**`data/foreign/loanword_lexicon.json`** — a frozen, hand-authored table
from the *dialect's* constructors to English phrases: relations (`≥` →
"is at least"), connectives (`∧` → "and also"), binder forms (`∀ … : T,` →
"for every … of type …"), type names, and grouping words. It inherits
v0.18's lexicon rules **whole, cited not restated**: prefix-freeness (L1)
and numeral-disjointness (L2) at `scripts/realization_lexicon.py:30–38`,
which `:39–41` explains are together what make stage one *"a table lookup
with no lookahead policy of its own"*; the R2b gate list B1–B7 at
`:43–79`, enforced at `:295–317`, where a table that fails any of them
raises `LexiconError` at load and *"nothing downstream gets a chance to
work around it"*.

**`scripts/foreign_voice.py`** — the renderer, and the inverse. All
precedence lives in the forward direction, as v0.18's realizer already
does it (`scripts/realize_term.py:41`). The inverse is **literal table
substitution only**: it *"never counts a bracket, never consults an arity
and never compares precedences"* (`scripts/realize_term.py:387–396`, the
discipline stated at `:25` as having "no precedence table, no bracket
counter"). Refusal is a closed vocabulary extending v0.18's nine reasons
(`scripts/realize_term.py:134–145`); a construct with no row **refuses at
the surface**, it does not improvise.

### 3.2 The oracle, and what it actually is

> **Correction 2 (2026-08-23, grounding): the pinned checker cannot emit
> an elaborated term, and it carries no Mathlib.** Both halves of the
> advisor's oracle assumption fail against the tree.
>
> **(a) No elaborated-term emission exists.** `check_lean4` invokes the
> pinned toolchain's `lean` binary directly by path, captures stdout and
> stderr, and adjudicates exactly three things: exit 0, no warnings, and
> the `#print axioms` footprint of the named reference contained in
> `ALLOWED_AXIOMS` (`scripts/external_verifier.py:205–350`, allowed set at
> `:81`). It also requires the literal string `theorem {reference} :
> {surface}` to appear in the pinned source (`:261`). Nothing in that path
> produces a term. The other candidate, `prover/ExtractData.win.lean`, is
> a LeanDojo-v2 fork that emits command **`Syntax`** ASTs, tactic traces,
> and premise records (`:118–121`) whose goal states are
> **pretty-printed strings** through `Meta.ppExpr` (`:154`, `:171`,
> `:185`) — surface syntax and rendered text, binder-name-dependent and
> width-dependent, not a serialized `Expr`. Its consumer
> `scripts/trace_to_triples.py:11–15` says the quiet part out loud: it
> *does not invent, reorder, or normalise anything*. **A sweep for
> `pp.all`, `pp.explicit`, `Expr.`, `elabTerm`, or `instantiateMVars`
> across every `.py`, `.lean` and `.md` in the tree hits nothing outside
> `prover/ExtractData.win.lean` itself** — whose hits are the `ppExpr` and
> `instantiateMVars` calls just cited, i.e. the pretty-printing path
> already ruled out, not a term path hiding elsewhere. **Elaborated-term
> emission is a construction prerequisite with its own registered step
> (B-P), not an assumption.**
>
> **(b) Mathlib is outside the hermetic budget — but that blocks *heads*,
> not *types*.** [DESIGN-external-verifier](DESIGN-external-verifier.md):40
> states it as design law — *"Core Lean only: Mathlib is not installable
> within the hermetic budget"* — and `:151–156` records a node left
> permanently unbridged because core Lean *cannot even parse* the Mathlib
> notation. The one pinned Lean source in the tree says the same
> (`prover/lean/ingested/Ingested.lean:5–8`), and its `lake-manifest.json`
> lists zero packages. Verified directly against the installed pinned
> toolchain (v4.32.2): `#check ℝ` and `#check Real.sqrt` both return
> **Unknown identifier**.
>
> The first draft of this design read that as "no `ℝ`, therefore the
> real-analysis mass of the corpus is unspeakable." **The review corrected
> it and the correction is adopted: the declared interpretation (§3.2,
> rule R) substitutes the *type*, so `ℝ`→`Rat`, `ℚ`→`Rat`, `ℤ`→`Int`,
> `ℕ`→`Nat` are carried, not blocked.** What stays blocked is Mathlib's
> **head vocabulary**, which has no core-Lean referent at all: `Real.sqrt`
> (1,177 mute statements), `Real.cos` (122), `Real.sin` (89), `Real.log`
> (66), the bare `sin`/`cos`/`tan`/`exp`/`log` heads, and `√`. The
> register entry is therefore `mathlib_head_vocabulary`, and it is
> narrower — and more honest — than the first draft's.

**The prerequisite, and the prototype that says it is buildable.**
`prover/lean/normalizer/Serialize.lean` — a Lean program that elaborates
one term and prints a **binder-name-independent** serialization by walking
`Expr` and emitting constructor tags, de Bruijn indices, constant names
and universe levels, **dropping the `Name` field of every `forallE`,
`lam`, and `letE`**. Binder-name independence is then a property of the
serializer's type, not a normalization pass over text.

A working prototype was built and run during this grounding (2026-08-23)
under exactly the constraints the verifier already enforces — the pinned
v4.32.2 binary invoked **directly by path**, `import Lean` only, no lake,
no Mathlib, no network. **It is retained in the tree** as
`prover/lean/normalizer/Serialize.prototype.lean` (LF sha256
`01a7cc2000b39a98…`), marked as a prototype and not as the B-P
deliverable, so the digests below are reproducible rather than remembered.
Re-run from that path, it produces:

- `∀ p q : Nat, p + q = q + p` and `∀ zzz www : Nat, zzz + www = www + zzz`
  → **byte-identical** 475-character serializations (sha256
  `25ec23fb13b33120…`);
- `∀ a b c : Rat, 9 * (a ^ 3 + b ^ 3 + c ^ 3) ≥ (a + b + c) ^ 3` and
  `∀ x y z : Rat, 9*(x^3+y^3+z^3) ≥ (x+y+z)^3` → **byte-identical**
  2,627-character serializations (sha256 `f89095af7546ebd1…`). Under
  Correction 2(b) this second pair is **in-territory**: it is a
  `Rat`-interpreted residue statement of exactly the kind B1 will score.

That is the identity witness the design needs, reachable inside the
standing hermetic rule. It remains a prerequisite: B-P discharges it in
the tree, with tests and a Python driver, before any gate number is read,
and the two pairs above are its first two test cases.

**The declared interpretation (rule R), frozen and reviewed.** Applied
identically to both sides: (i) substitute the type glyphs `ℝ`→`Rat`,
`ℚ`→`Rat`, `ℤ`→`Int`, `ℕ`→`Nat`; (ii) collect the free identifiers not
bound by an existing binder group and not in the frozen constant set;
(iii) if any remain, prepend `∀ <sorted free identifiers> : Rat,`. Rule R
is a **trusted, reviewed artifact with its own digest**, not inverter
logic — extending it is a diff with tests.

**The identity relation.** For a statement `s`:
`orig_elab_digest = sha256(serialize(elaborate(R(s))))`, and
`rt_elab_digest = sha256(serialize(elaborate(R(r))))` where
`r = literal_inverse(render(s))`. Identity holds iff the digests are
equal. **`orig_elab_digest` is recomputed in the same run and never
carried from ingest** — no such digest exists at ingest, and the rule is
written here so that it never starts existing. R is applied
independently on each side; **a preamble mismatch is a B1 failure, never a
repair.**

**What identity is, exactly — the review's correction, adopted verbatim.**
Identity holds **up to what elaboration erases and what the preamble rule
regenerates; a rendering error confined to either is invisible to B1;
C-V4 bounds how often that is the case.** This sentence is not a caveat
appended to a claim — it *is* the claim's shape, and §7's C-V4 exists to
put a measured number under it. Without C-V4, B1 could be scoring rule R
and the elaborator's own normalization rather than the rendering, and
nothing in the first draft of this design would have noticed.

> **Correction 3 (2026-08-23, grounding): the surface cannot be fed to the
> oracle by literal substitution alone, because Lean's default silently
> invents the missing half.** A 1,000-statement random sample of the mute
> set was fed to the pinned binary as `example : <statement> := by sorry`.
> With Lean's defaults, **680 of 1,000 (68.0%) "elaborated cleanly."**
> With `autoImplicit false` and `relaxedAutoImplicit false`, **1 of
> 1,000.** The 679-statement difference is Lean auto-binding every unknown
> identifier as an implicit variable of inferred type — including `ℝ`
> itself, which becomes an auto-bound *type* variable, turning `∀ θ : ℝ, …`
> into a statement about an arbitrary type. An oracle run at Lean's
> defaults would certify round trips between two elaborations of a
> proposition neither the corpus nor the reader ever wrote. **`autoImplicit
> false` is mandatory and is a gated setting (B5).** With it off, the
> surface must carry an explicit binder preamble, and choosing binder types
> is semantic work — so the advisor's "literal table substitution ONLY"
> rule survives *for the body* and is replaced *for the preamble* by rule
> R above.

### 3.3 The untranslatable register — the headline artifact

**`experiments/foreign_register.json`**, frozen and digested **before the
first render**. One row per excluded construct:

```text
register_entry {
  construct_id,              # mathlib_head_vocabulary, dependent_binder,
                             # implicit_argument, coercion, tactic_form,
                             # notation_overload, schematic_variable,
                             # interpretation_absent, ascii_pseudo_math
  surface_witness,           # one verbatim corpus occurrence
  reason,                    # closed vocabulary; why no row can be authored
  blocking_count,            # statements this construct alone blocks
  statement_ids[],           # the blocked set, exhaustively
}
register {
  entries[], blocked_set_digest, frozen_at,
  lexicon_digest_at_freeze, interpretation_digest_at_freeze
}
```

The register is not a limitations paragraph. It is the artifact a reader
consults to learn what the graph is silent about, it carries a digest so
that widening it later is a visible diff, and **B4 makes freezing it a
precondition of rendering anything**. Its largest entry is already known
and will be written in first: `mathlib_head_vocabulary`.

**Per-statement receipts carry the interpretation.** Every served
statement's receipt records an `interpretation_shift` field naming each
substitution rule R applied — `ℝ→Rat` above all — so that a reader of any
single answer can see that the term the oracle adjudicated is the
statement under a declared domain, not the statement as the corpus author
typed it. A rate quoted without that field beside it is a number
pretending to be a fact (§8).

## 4. Trusted and untrusted

**Trusted:** the committed corpus statements; the pinned toolchain and its
`lean-toolchain` file (digest-pinned in every verdict, re-hashed on
`recheck`); the loanword lexicon once committed; **rule R, the declared
interpretation**, reviewed the same way and carrying its own digest; and
**the byte-frozen parser `scripts/match_signatures.py`, LF-canonical
sha256 `65fead2f47b6a2ce…`**, which this cycle uses to compute the
transliterable/foreign split (B0a) and the C-V2 contrast, and which
therefore must not move under this cycle's feet — hence its place in B7's
freeze list and §5's ordering rule.

**Untrusted and measured:** the renderer (B1); the literal inverse (B1,
and C-V1 exists to prove the inverse is not the whole gate); the Lean-side
serializer (B-P, plus B5's two-run byte identity); the *sufficiency* of
rule R and the elaborator's normalization (C-V4 — the review's finding,
and the only instrument that bounds it); every rendered sentence
(per-statement identity gate, and a statement that fails refuses at the
surface — the honest degradation v0.18 already ships); and the register's
completeness (B3's arithmetic).

**The authority boundary, imported verbatim, because this design leans on
it harder than any before it.** `scripts/external_verifier.py:6–7`: *"a
passing check certifies what it checks, not correctness in general."* Here
that means precisely: a passing identity certifies **that the English
determines the term** under the declared interpretation, up to what
elaboration erases and rule R regenerates. It certifies nothing about the
statement's truth, nothing about whether the declared interpretation is
the one the corpus author meant, and nothing about the English being good
English. And `:35–40` governs the output: **a verdict alone never mints a
`verified_by` link**, and this cycle mints none.

> **A bookkeeping fact, recorded so nobody improvises it.** `check_lean4`
> pins its inputs through `resolve_contained_artifact`
> (`scripts/proof_artifacts.py:14–47`), which refuses anything that is not
> an existing, repository-relative, forward-slashed regular file. A
> per-statement committed verdict for thousands of statements is therefore
> not available and is not attempted. The registered run uses a **batch
> harness** that invokes the same pinned binary under the same hermetic
> rule and writes **one** run artifact; it is explicitly *not* the verdict
> ledger, mints no ledger entries, and `verdict_ledger_errors` is
> untouched by it. A small pre-registered sample (20 statements, ids fixed
> in the prereg commit) *does* go through `check-lean4` proper, with their
> sources committed, so that the batch harness's agreement with the ledger
> authority is itself measured rather than assumed.

## 5. Smallest slice

- **B-P first:** `prover/lean/normalizer/Serialize.lean` plus its Python
  driver, with tests asserting binder-name independence (the retained
  prototype's two pairs become the first two test cases) and two-run byte
  identity.
- The loanword lexicon over the constructors the **oracle-eligible**
  residue actually carries, with its head coverage stated in the file the
  way v0.18's lexicon states it, and the refusal path exercised by
  injection rather than accident.
- Rule R, committed with its digest, before either the lexicon's hand
  renderings or the serializer exist (B7's ordering).
- `scripts/foreign_voice.py` + per-statement receipts carrying
  `interpretation_shift` + the register, frozen and digested before the
  first render.
- One registered run, `experiments/foreign_voice_rate.json`, carrying
  B0's tables, B1's rate **with its covered-set composition**, B3's
  arithmetic, and every control's reading.
- Wire **one** new line into `answer.render`, beside v0.18's `in words`:
  `in words   : <surface>` for the foreign path too, emitted **only** with
  a passing identity receipt. The ingestion disclaimer stays. Both skins
  inherit it through A-IH6; the capability sheet gains a `foreign_voice`
  row that quotes B1 from the artifact rather than from a number pasted
  into code, exactly as `scripts/serve_chat.py:356–374` does for
  realization.
- **Seal bookkeeping.** This cycle touches `answer.py` again. v0.18's
  first rendering commit retired the v0.17 witness and sealed a new book;
  the same rule applies unchanged — v0.19's first foreign-voice commit
  retires the v0.18 witness for future comparisons, rebuilds the book as a
  new sealed artifact with the dated reason in the commit, and leaves the
  old artifact untouched as the record of what was measured.
- **Release obligations, named here rather than discovered at the gate.**
  `check_report_regeneration.py` runs in the release refresh with its
  verdicts in the notes; the full suite is green on a **frozen tip** with
  retained receipts; every unfinished item ships or parks in writing.
- **The ordering rule for the tokenizer work, because two cycles must not
  contaminate each other's numbers.** The `TOKEN_RE` change that makes the
  transliterable 6,414 natively parseable **may not land before v0.19's
  registered run**. That file is pinned as the stage-2 parser by
  `experiments/realization_prereg.json` (role `parser`, digest
  `65fead2f…`) and revalidated by **C-R3** in the v0.18 registered run, so
  when the change lands it retires that pin **for future comparisons only**
  by dated amendment; it does not amend `realization_rate.json`. Any new
  rate is a **new registered run with its own prereg and its own frozen
  digests**, and the alternative — declaring
  `experiments/realization_rate.json` a historical artifact measured under
  the pre-amendment parser — must be said in writing in the amendment
  commit. Silently letting a 0.9991 measured under one parser stand as a
  current fact about a different parser is the exact drift this repository
  exists to catch. ROADMAP-v0.19 item 3a carries the full re-freeze
  discipline, including the task-book gap it names: `match_signatures.py`
  is not among the witnessed `rendering_module_digests`, so widening the
  tokenizer moves served `in words` output while every witnessed digest
  stands still, and that lane owes a before/after diff of served answer
  lines rather than a green digest test read as reassurance.
- **A debt this cycle pays, found during grounding.** The C-R1 one-sided
  lesson and the prefix-free lesson — both load-bearing above — exist only
  in commit bodies (`9879b06`, `ccac853`) and module docstrings. Neither
  appears in `docs/DISCOVERIES.md` or `experiments/ANALYSIS.md`. This
  cycle lands both, dated, before it borrows them.

## 6. Construction gate (numbers frozen here)

> **Gate history (2026-08-23).** The course's B0 froze at *"a table of
> ≤300 entries must fully cover ≥40% of the 83%, or stop."* Grounding
> falsified that floor before implementation. The retirement is restated
> here over the **residue** — the design's actual territory, not the
> pre-correction 83% — because a gate must be retired on the numbers it
> would actually have been read against: over the 4,191-statement residue
> there are **421 distinct constructor tokens**, a **25-entry** table
> fully covers **55.0%** (clearing the ≥40% bar by **1.4×** at
> one-twelfth the budget), and a 300-entry table covers **98.76%**. The
> conclusion survives the honest denominator: a gate a preview clears
> before any work begins is not a gate. B0 below is rebuilt around the
> things that can actually fail.

- **B-P — construction prerequisite, discharged before B0 freezes.** The
  Lean-side serializer exists in the tree, runs under the hermetic rule
  (pinned binary by path, no lake, no Mathlib, no network), and its tests
  assert (i) binder-name independence on the registered pairs and (ii)
  byte-identical output across two runs. If B-P cannot be discharged, §8's
  first stop condition has fired and the cycle publishes the prerequisite
  as its finding.

- **B0a — the transliterable/foreign split.** Publish, per corpus, the
  mute set partitioned by the two-glyph swap under the frozen parser.
  **Floor: the foreign residue must be ≥ 2,000 statements**, or the claim
  has no territory and the cycle stops. *(Preview: 4,191 — 4,060
  lean_workbook, 131 across 23 other corpora.)*

- **B0b+B0c — the oracle's reach. One measurement, stated as one.** The
  first draft split these into "which statements have core-Lean
  vocabulary" and "does the interpretation elaborate", and the first of
  those was an **authored blocklist** — a regex naming what I guessed
  Lean would reject. The review was right that this is circular: a
  hand-written eligibility filter measures the filter. **Eligibility is
  therefore defined operationally, by outcome:** a residue statement is
  oracle-eligible **iff, after rule R, the pinned binary accepts it with
  `autoImplicit false`.** There is no blocklist. Running rule R over the
  residue and reading the acceptances *is* both gates, and the artifact
  reports it as a single table. **Floor: ≥ 1,000 accepted**, or the oracle
  cannot reach enough of the residue to gate anything and the cycle stops
  with the Mathlib-budget question named for the maintainer.

  > *(Preview, indicative — B0b+B0c remains the registered probe. Rule R
  > applied to all 4,191 residue statements, pinned v4.32.2 binary,
  > `autoImplicit false`: **2,319 accepted = 55.3% of the residue = 18.1%
  > of the corpus.** The 1,872 rejections are dominated by Mathlib heads —
  > `Real.sqrt` 2,531 occurrences, `sin` 430, `cos` 327, `Real.cos` 307,
  > `Real.sin` 189, `Real.log` 160, `tan` 48, `exp` 35. This supersedes
  > the first draft's 1,456, which came from the retired blocklist and was
  > additionally quoted against an impossible 1,500-statement sample of a
  > 1,456-statement set — an arithmetic impossibility the review caught
  > and this restatement removes.)*

  > **The branch this measurement forces, stated now rather than at the
  > gate.** The preview's acceptances are **2,316 lean_workbook and 3
  > everything else**: the five wholly-mute corpora and the other
  > Prop-valued and relational ones (`logic.boolean_foundations` 20,
  > `temporal_logic.linear_time` 15, `set_theory.boolean_foundations` 9,
  > `programming.core` 9, `narrative.story_grammar` 9,
  > `provability.goedel_loeb` 6, `graph_theory` 7) accept **zero**,
  > because rule R binds free identifiers at `Rat` and their statements
  > are propositions, not rationals. The branch is chosen at B0 time,
  > before any render, and whichever branch is taken is recorded:
  > **(i)** a **second declared interpretation** — Prop-valued, free
  > identifiers bound at `Prop`, connectives to core Lean's
  > `And`/`Or`/`Iff`/`Not` — is registered in-cycle with its own digest
  > and must pass B0b+B0c on its own denominator, in which case those
  > corpora enter the covered set carrying that interpretation in their
  > receipts; or **(ii)** it is not registered, and every one of those
  > statements is `registered_blocked_no_row` with reason
  > `interpretation_absent`. Branch (i) is the only route this design has
  > to a covered set that is not almost entirely one corpus, and that is
  > the honest reason to prefer it.

- **B0d — the inverse direction, unpreviewed and the real probe.** Over
  100 statements drawn from the oracle-eligible set by a **committed
  deterministic rule seeded from the lexicon digest** (no hand-picking,
  and the rule is in the prereg commit), hand-render each, apply the
  literal inverse, and elaborate the result. **≥ 90 of 100 must elaborate
  at all** — identity is B1's business; B0d only asks whether the inverse
  produces Lean. Nothing in the tree previews this number, and it is where
  word order, grouping words, and arity ambiguity will surface if they are
  going to.

  **The three-line separation the review required, adopted whole:** the
  lexicon digest and the inverse-table digest are frozen **before the
  hand-renderings exist** (B7's ordering extends to cover this); the 100
  ids follow from that digest by the committed rule; and the **100
  hand-renderings are committed verbatim in the prereg commit as a sealed
  prediction** that `foreign_voice.py` must later reproduce
  **byte-identically**, with every divergence reported in the run
  artifact. A hand probe whose outputs are never compared against the
  implementation is a rehearsal, not a gate.

- **B1 — identity floor.** **≥ 99.5%** of the covered set —
  `orig_elab_digest == rt_elab_digest`, both recomputed in the run.
  Failures are listed **exhaustively** (LOST = 0 discipline, v0.18's
  balance arithmetic imported). **Every sentence that quotes B1 states the
  covered set's composition in the same sentence** — "n of N, of which X%
  is `lean_workbook.ground.v1`" — because on the preview that X is 99.9%
  and a rate quoted without it reads as a corpus-wide fact that it is not.
  Per-corpus figures apply only to corpora with ≥ 50 covered statements;
  smaller ones report individually with every failure named, never
  averaged (the thin-denominator lesson, imported from the v0.17 task book
  through v0.18's R1).

- **B2 — rejection is failure, not a skip.** The oracle's three outcomes
  are distinguished and none is a silent drop
  (`scripts/external_verifier.py:71`). **FAIL** — the surface elaborated
  with errors — counts against B1. **REFUSED** — the toolchain is absent
  or an input escapes containment — **aborts the run**; it is not a data
  point, and a run with any refusal publishes zero rates. There is no
  third bucket.

- **B3 — rendered or registered, and the arithmetic closes.**

  ```text
  transliterable                     (B0a, frozen parser)
  + covered_served                   (identity held)
  + covered_failed                   (elaborated, digest differed — B1)
  + registered_blocked_mathlib_head  (oracle rejects on Mathlib heads)
  + registered_blocked_no_row        (no lexicon row / no interpretation)
  = 10,605  exactly
  ```

  The two `registered_blocked_*` buckets are **reported separately, never
  summed into one number**: the first is a budget consequence the
  maintainer can lift and the second is a design consequence this cycle
  owns, and merging them would hide which is which. Any statement in none
  of those five buckets is a bug in the census, not a rounding difference.

- **B4 — the register is frozen first.** `foreign_register.json` is
  committed with its `blocked_set_digest` in the preregistration commit,
  before `foreign_voice.py` renders anything. A post-freeze entry is
  permitted only as a *dated amendment commit that re-runs B1 from
  scratch*; an amendment chased **after** reading B1 is §8's stop.

- **B5 — determinism and hermeticity.** Same statement, same lexicon, same
  interpretation → byte-identical surface and byte-identical digest; two
  full runs on one tree produce byte-identical artifacts (precedent:
  `tests/test_measure_realization.py:139`). `autoImplicit false` and
  `relaxedAutoImplicit false` are asserted as *committed settings* by a
  test, not left to a flag. An absent pinned toolchain **refuses and never
  downloads**, asserted on every machine — the existing test is
  `tests/test_external_verifier.py:215`
  (`test_missing_toolchain_refuses_and_never_downloads`), deliberately not
  skipped, and this cycle's harness gains its sibling.

- **B6 — no learned component.** Nothing in the render path, the inverse,
  rule R, or the register is learned. §9 states what would have to be true
  for that to change, and it is not true this cycle.

- **B7 — the oracle is not the renderer, and the parser is not either.**
  Recorded in the preregistration commit, **before** `Serialize.lean` is
  written and **before** any hand-rendering exists: the lexicon digest,
  the inverse-table digest, rule R's digest, and
  **`scripts/match_signatures.py` at LF sha256 `65fead2f47b6a2ce…`** —
  the frozen parser, in the freeze list because B0a's split and C-V2's
  contrast are both computed with it and a parser that moves mid-cycle
  would move the denominator under the claim. The serializer's digest is
  recorded beside them (C-R3's discipline, imported). *If making the
  oracle agree requires editing the lexicon, the interpretation, or the
  parser, the independence claim is void and the change needs its own
  review naming the reason.*

## 7. Blind controls, each with its voiding sentence

- **C-V1 — the skeleton-only renderer, one-sided by construction.** A
  renderer that keeps grouping words and structural scaffolding and drops
  every content word, read back through the **committed** table — never
  through its own. The one-sidedness is not a stylistic choice; it is
  v0.18's measured lesson, imported: a two-sided scramble is a consistent
  renaming, still a bijection, and round-trips near-perfectly, so a
  two-sided control voids the reading for a reason that has nothing to do
  with whether the gate reads the words
  (`docs/DESIGN-sans-template-rendering.md` §7 C-R1; the pair of tests
  that aim it is `tests/test_measure_realization.py:207` and `:218`).
  *The control is informative only if the true renderer's identity rate on
  the same statement set is ≥ 20× the skeleton renderer's; if the skeleton
  renderer clears 1%, the gate is not reading the words and is void; if
  both are near zero, the gate is untested and the reading is void.*

- **C-V2 — the transliteration null, a positive control.** For every
  covered statement, also run a null path that emits the glyph-swapped
  Lean surface **verbatim, with no English in it at all**, and feeds that
  to the oracle. The null is not a contender; it exists to prove the
  oracle says yes for a reason. *If the null does not reach ≥ 99%
  identity, the harness — not the renderer — is what the run measured, and
  every other reading in the artifact is void.* Its second job is to keep
  Correction 1 honest in public: the null's rate on the **transliterable**
  6,414 is reported beside the renderer's rate on the residue, so a reader
  can see that the easy half was not counted.

- **C-V3 — the determinacy sheet, and the claim it alone can license.**
  Thirty rendered statements, sheet pre-registered, marked blind by a
  non-maintainer: for each, is the mathematical statement recoverable
  *determinately* from the English alone? **Fifteen C-V1 skeleton outputs
  are interleaved unlabelled — and that 15-item arm is flagged here as
  sub-threshold and advisory:** at n = 15 the control arm cannot support
  an inferential claim, so it is read as a smell test that can only ever
  *void*, never confirm. *If the skeleton control is marked determinate at
  ≥ half the true renderer's rate, the voice claim is void — the sheet is
  measuring the reader's mathematical guesswork, not the rendering.*

- **C-V4 — the near-miss null, and the control this design did not have.**
  C-R2's descendant, and the review's finding: B1 compares digests of
  elaborated terms, so any rendering error that elaboration erases, or
  that rule R silently regenerates, is invisible to it. C-V4 measures how
  large that blind spot is. Over a **pre-registered sample**, apply
  exactly one **mechanical mutation to the rendered English** — drop a
  grouping word; drop an ascription phrase; drop a binder phrase; swap two
  same-type binder names **in the preamble phrase only, leaving the
  occurrences alone**; reassociate one operator — then invert, elaborate,
  and compare. **The digest MUST differ.** *If fewer than 95% of
  mutations change the digest, B1 is measuring the preamble rule and not
  the rendering, and the reading is void.*

  The binder-swap mutation is expected to be the one that most often
  fails to move the digest, precisely because rule R regenerates the
  preamble from the inverse output. **That is the measurement, not a bug
  in the control** — it is the concrete form of "what the preamble rule
  regenerates", and a low number there is the design learning that its
  identity relation is thinner than it reads.

## 8. Stop conditions and non-claims

**Stop and publish** if B-P cannot be discharged under the hermetic rule
(the prerequisite is the finding, and the Mathlib-budget question goes to
the maintainer named); if B0a leaves fewer than 2,000 foreign residue
statements, or B0b+B0c fewer than 1,000 accepted; if B0d misses 90 of 100;
if the lexicon fails injectivity, prefix-freeness, or numeral-disjointness
at load (`LexiconError` is not a thing to work around); if **elaboration
is unstable across two runs** on the same tree — the oracle is then not a
function and no digest identity means anything; or if any post-freeze
register edit is chased **after** B1 has been read. In every case: publish
the reading and stop, with no "exploratory" relabeling.

**Non-claims, stated hard.**

- **Identity is bounded, and C-V4 is how far.** Identity holds **up to
  what elaboration erases and what the preamble rule regenerates; a
  rendering error confined to either is invisible to B1; C-V4 bounds how
  often that is the case.** No sentence in the release quotes B1 without
  this bound available in the same artifact.
- **This is a `lean_workbook` rate.** On the preview the covered set is
  99.9% `lean_workbook.ground.v1`. **The other 23 corpora contribute ≤ 130
  statements, reported individually, never averaged** — and under branch
  (ii) of B0b+B0c they contribute zero. A number that reads as "the corpus
  speaks" when one corpus is 99.9% of its denominator is the kind of
  sentence this project retracts later.
- **Not fluency, and not translation quality.** The sentences are
  invertible; their style is whatever the lexicon produces. C-V3 is the
  only instrument here that touches readability, and §7 says what happens
  when it cannot run.
- **Coverage percent is not the headline. The register is.** No release
  sentence leads with a coverage number. If the register is thin and the
  coverage is high, the cycle under-delivered on its actual product.
- **No internal-grammar reading capability is gained.** The committed
  parser reads exactly what it read before. The inverse is an
  open-English reader only in the narrow sense v0.18 already carved out —
  it reads only strings this cycle's own renderer produced, it is not
  offered on the input side, and no request route calls it.
- **No truth claim, and no `verified_by` links.**
  `scripts/external_verifier.py:6–7` and `:35–40` govern, unweakened.
- **No Mathlib *heads*.** Type glyphs are carried by rule R; heads are
  not. `Real.sqrt` (1,177 statements), `Real.cos` (122), `Real.sin` (89),
  `Real.log` (66) and the bare trigonometric and exponential heads stay
  unspoken this cycle, by a budget decision this document did not make and
  cannot unmake. This is narrower than the first draft's "no `ℝ`", and the
  narrowing is the review's, adopted.
- **The declared interpretation is an interpretation, not a discovery.**
  Where a statement's source meaning is over `ℝ` and rule R elaborates it
  over `Rat`, that is recorded per statement in the receipt's
  `interpretation_shift` field and named in every sentence that quotes B1.
  A rate measured under a substituted domain that does not say so is a
  number pretending to be a fact.
- **The transliterable half is not this cycle's result.** The 6,414
  statements of Correction 1 are reported, contrasted (C-V2), and handed
  to roadmap item 3a. If they are ever counted inside a foreign-voice rate,
  that rate is wrong.

## 9. The learned seat (closed this cycle, in writing)

B6 forbids a learned component anywhere in this design's path, and unlike
v0.18 §9 there is no bounded seat held open behind the bar. The reason is
specific rather than doctrinal: the only place a ranker could sit is
choosing among multiple identity-passing surfaces for one term, and this
cycle's renderer emits one surface per term by construction (B5's
determinism makes it so). A seat that cannot receive candidates is not a
seat. v0.18's realization ranker seat is unaffected and stays where it is;
if this cycle's lexicon later admits alternates, the seat opens **there**,
behind the tool admission bar whole, and never as the difference between
refusing and answering.

## 10. How status lands

**Preregistration order:** this design; then rule R and the lexicon and
inverse-table digests, plus the frozen parser digest (B7); then B0d's
committed id-selection rule and its 100 sealed hand-renderings; then B-P
(`Serialize.lean` + driver + tests); then the **frozen register** with its
`blocked_set_digest`; then `foreign_voice.py` + receipts + tests; then the
one registered run, `experiments/foreign_voice_rate.json`, carrying B0a,
B0b+B0c, B0d, B1 **with composition**, B3's five-bucket arithmetic, and
every control's reading including C-V4. Fires, misses, and voids land
together in ROADMAP-v0.19, ANALYSIS, DISCOVERIES, and BACKLOG; the v0.19
blog's forward section follows from this document. The release refresh
runs `check_report_regeneration.py` with its verdicts in the notes, and
the suite is green on a frozen tip with retained receipts before the tag.

**The v0.19 roadmap this design implies:**

1. **Headline — this design.** The foreign voice and its register.
2. **DESIGN-block-vocabulary, ADOPTED bounded.** The address-space probe,
   scoped to a single question — *is the unified dictionary a real object,
   or two existing objects wearing one id space?*
   (`docs/DESIGN-block-vocabulary.md:282–288`) — with its §4 falsifiers
   pre-registered before any measurement: the keyword channel at its
   measured floors, zstd-with-shared-dictionary, and the canon token
   encoding at 8.4×. Beat none of them and it parks with the numbers. Its
   denominator input is B0a/B0b+B0c's tables, per its own §4 sequencing
   bullet.
3. **Registered probes — cheap, pre-registered, both branches yield an
   artifact.** A probe that can only confirm is not a probe; both commit
   their result whichever way it lands.
   - **3a — the transliteration lane.** Widen `TOKEN_RE` so `≥` and `≤`
     are read natively, bringing the 6,414 transliterable statements onto
     v0.18's existing realizer path — no loanword pipeline, no oracle. It
     is a probe rather than a headline precisely because the preview makes
     it look easy, and easy is what the register exists to keep honest:
     the artifact publishes the parse rate **and** the round-trip rate
     over the newly reached set, because parsing is not rendering and
     v0.18's own R0/R1 split is why we know to separate them. §5's
     ordering rule and its re-freeze discipline govern it.
   - **3b — TWO RIGHTS B0, one hour, adopted from series 3.** Grep the
     committed corpora for **co-present statements that differ only by a
     convention choice** — the same mathematical content under two
     defensible conventions. If pairs exist, the artifact is a
     `ConventionPair` census, sealed before inspection, and the full
     direction becomes askable with a real denominator. If none exist, the
     artifact is the **registered negative**: a finding about how these
     corpora were authored — conventions fixed by the author and never
     forked — which is a fact about the graph nobody has written down.
     **The grep runs before either branch is preferred, and its result is
     committed either way.**

**The v0.18 lesson debt** (§5): C-R1 one-sided and prefix-free landed in
DISCOVERIES, dated, before this cycle borrows them.

**The course gate.** `reports/design-direction-v0.19.json`, with
`reports/design-direction-v0.19-brief.txt` beside it, is the receipt that
discharges ROADMAP-v0.18:226–233's strict wording — the forge skill
**invoked**, not reaffirmed, with the brief carrying both prior readouts
(throughput and realization), so the course could not be a ratification of
the flattering one.

**If B1 fires, the question that becomes askable next is cross-layer
same-statement discovery:** with the foreign residue rendered and the
parseable set already rendered (v0.18), the same mathematical statement
can be recognised across two grammars that never shared a parser — and
that is the first honest denominator this project has ever had for asking
whether its layers describe one world or two.
