# The graph speaks: sans-template rendering, kernel-bound

**Status: design only.** Nothing here is implemented. First slice
targets v0.18, **directed by the maintainer** (2026-08-21: "bring
phase 6 into the next release") — and separately *earned* by a
registered trigger. [DESIGN-grounded-throughput](DESIGN-grounded-throughput.md)
§10 wrote, before the run: *"If T4 fires, the question that becomes
askable next is the cost ledger — answers per joule and per dollar
against hosted-model pricing — and the sans-template rendering
boundary (substrate Phase 6) becomes the next surface with a measured
floor under it."* T4 fired — the kernel's registered median was 3,451
tok/s at 100% correctness while the grounded contender's median was
zero, so the frozen K = 5 multiple is satisfied unbounded rather than
measured (`experiments/throughput_result.json`,
`…_bgrounded.json`). §10 named **two** successors, the cost ledger
first; the maintainer's directive selects the second, and the cost
ledger parks in ROADMAP-v0.18 with that recorded. Direction and
trigger agree on the boundary; both are recorded here because a course
selection without a record is the drift this repository exists to
catch.

## 1. The boundary being moved, and what a person gains

Substrate Phase 6 ("unrestricted prose authoring / open-English
render, still kernel-bound", DESIGN-interactive-harness §9) has a
shipped half and a parked half, and the parked half is the one with
the word **sans-template** in it:

- **Shipped (v0.8):** `scripts/prose.py` authors varied prose whose
  faithfulness gate is *complete over a closed approved algebra* —
  its own docstring says widening the surface means adding bank rows,
  never loosening the closure. Every sentence the system serves today
  is either a verbatim quotation (`answer.py`, `gloss.py`) or a
  composition from closed banks and f-string patterns
  (`prose.py`, `narrative_realize.py`, `oracle_controller_demo.py`).
- **Parked:** prose whose surface is *not* enumerated anywhere — no
  bank, no whole-sentence template — and is still kernel-bound.

The governing doctrine names the mechanism.
[DESIGN-language-as-structure](DESIGN-language-as-structure.md) §3
replaced the overstatement (its §9 disposition table records "surface
English requires string templates" as **retracted as design law**)
with: *"Surface English is the linearization of a well-typed
linguistic term (plus optional empirical packaging) … every emitted
token sequence must be recoverable to a term the kernel can re-parse
and re-verify."* That law is stated for *linguistic* terms; this
design **extends its mechanism to mathematical canonical terms** — an
extension claimed here on its own feet, not smuggled in as the law's
own warrant, and the round trip is still the teeth. The shipped
precedent is `experiments/langgen.py`: two invented languages,
opposed word orders, round-trip **1.0/1.0 at N = 500** with the LOST
dual at zero (`tests/test_langgen_roundtrip.py`), and the measured
verdict that for extractive answers *no learned decoder should
exist* — the renderer realizes the tree; every generated word is
pointed-at or produced by exact code (`experiments/ANALYSIS.md`,
xlang capstone).

**What a person gains.** Today 12,515 of the corpus's 12,777 nodes
are ingestion records whose `statement_meaning` is machine
boilerplate; `answer.render` serves them with the disclaimer *"this
text is an ingestion record, not an explanation a person wrote"* —
quotation has nothing worth quoting there. The formal statement,
though, is exact structure. If the kernel can **say its own
structures in open English** — sentences composed by a realization
grammar, not drawn from banks, each gated by re-parsing back to the
exact term it claims to render — the definition surface stops being a
quotation engine with a 262-node authored vocabulary and starts
speaking about the structures it can parse. Through A-IH6, both skins
inherit it: the TTY and the chat-completions endpoint serve the same
new rendering the moment the engine has it.

**The honest denominator, measured before this design was reviewed
into its current form:** the committed parser parses
`formal_statement.canonical_ascii` for **2,172 of 12,777 nodes
(17.0%)** — the rest is Lean/Unicode syntax outside the template
grammar (`lean_workbook.ground.v1`, 97.9% of corpus mass, parses at
16.3%). A term that does not parse has no source skeleton to
round-trip to, so this cycle's rendering claim is scoped to the
parseable terms, and the parse-rate table itself ships as a
first-class finding — it names, per corpus and failure class, exactly
where the corpus outgrew its own template grammar (R0, §6).

## 2. Why this direction, and its relation to the course process

The maintainer directed Phase 6 into v0.18 in the same turn that
commissioned the v0.17 cycle ("continue with the next two releases and
bring phase 6 into the next release"). This is the **second
consecutive cycle whose headline is maintainer-directed rather than
course-selected**, and the rotation records that as a first-class
decision rather than absorbing it: the outside design inquiry was not
run for v0.18; the standing receipt is
`reports/design-direction-v0.17.json`; the obligation carries to the
v0.19 gate, whose course brief must carry **both** readouts (the
throughput result and this design's realization result); and a third
consecutive directed headline without reopening the outside course
requires a written amendment to the course gate itself — a decision
that belongs to the maintainer, named in ROADMAP-v0.18's governance
section. What keeps this cycle honest meanwhile: the registered
trigger quoted above named this boundary before the run that fired
it, and this design was adversarially reviewed — two of its gates
were rewritten by measurement before commit (§6's history note).

## 3. The first-class object: a realization with a receipt

**`scripts/realize_term.py`** — a realization grammar that linearizes
a parseable canonical term into an English sentence, and a
**realization receipt**:

```text
realization {
  statement_id | session_ref,
  term_skeleton,            # canonical skeleton of the SOURCE term
  surface,                  # the emitted English sentence
  reparse_skeleton,         # what the reading path recovered from surface
  round_trip ∈ { EXACT | FAILED },   # skeleton equality after canonicalize
  lexicon_entries[],        # every (operator|constant → words) row used
  parameters { order, … },  # the realization parameters applied
}
```

**The gate is two-stage, and only the second stage is the independent
reader** (this paragraph replaced a self-contradictory first draft;
the review that forced it is part of the preregistration record):

- **Stage 1 — lexicon inversion (trusted, committed, reviewed).** The
  surface is de-lexicalized back to template tokens by the *same
  committed lexicon table used forward*, read in reverse. This is not
  an independent check and is not claimed as one: it is a bijective
  table whose entries are reviewed in a diff with tests, exactly the
  rule `prose.py`'s banks live by. Bijectivity is itself gated
  (**R2b**): forward and reverse readings of every row compose to the
  identity on both sides, and a table that is not injective in either
  direction refuses at load. **Numerals are not a table**: the
  English-numeral realization ("eight hundred twenty-four" ↔ `824`)
  is a genuine algorithmic pair, registered separately with its own
  tests and its own scrambled-numeral control (§7 C-R1 covers it),
  because an unregistered numeral inverse is the hole this gate would
  otherwise leak through.
- **Stage 2 — structural re-parse (independent).** The de-lexicalized
  token string is parsed by the **byte-frozen committed parser**
  (`match_signatures.Parser` + `canonicalize`) and compared to the
  source skeleton. Stage 2 has never seen the realizer; it is the
  part that can fail. The inverter is permitted but must be
  table-driven, with **no operator-precedence or bracketing logic of
  its own** — all structure comes from word order the forward grammar
  emitted and stage 2 independently re-derives; the inverter's digest
  is recorded beside the parser's (C-R3).

What the round trip proves is therefore precise and bounded: **the
sentence's structure is recoverable**, given a lexicon whose
correctness is carried by review, not by the gate.

**The language boundary, stated before anyone is disappointed.** This
cycle renders *terms the kernel already parses*: corpus formal
statements and session-accepted structures. It does not parse open
English questions — the input side stays exactly where
DESIGN-text-resolution left it (FP floor 0.030; the lexical-semantics
route refuted by measurement, its §4 residuals standing) — with one
carve-out stated plainly: **the stage-1 inverter is an open-English
reader, however narrow; it reads only strings this cycle's own
realizer produced, is not offered on the input side, and no request
route calls it.** And it does not render narrative or affect —
`prose.py`'s closed-algebra gate stays the only narrative authority.
Sentences, not conversation.

## 4. Trusted and untrusted

Trusted: the committed canonical terms; the byte-frozen parser and
canonicalizer (the same code the ownership and evaluate routes stand
on); the realization *lexicon file* once committed (a first-class,
reviewed artifact; extending it is a diff with tests). Untrusted and
measured: the realization grammar (R1–R5); the numeral pair (its own
registration); every emitted sentence (per-sentence round-trip gate at
render time — a sentence that fails re-parse is **refused at the
surface**, the honest degradation); and any ranking component (§9).

## 5. Smallest slice

- The lexicon over the operator/constant heads the parseable corpus
  actually carries. **Calibration corrected by implementation
  (2026-08-23):** the first draft's figures (95 heads, 39 singletons,
  top-10 led by `IMPLIES` and `MEET`) read the `anonymized_template`
  inventory — the wrong field for this cycle. The `canonical_ascii`
  parseable subset carries **64 heads, 35 singletons, and neither
  `IMPLIES` nor `MEET` at all**; on the template side the re-measured
  truth is 95 heads, 30 singletons, `MEET` (22,653) ahead of
  `IMPLIES` (10,202). Heads without lexicon rows refuse, they do not
  improvise — and the shipped lexicon chose to cover both inventories
  whole, so the refusal path is exercised by injection, not accident.
- `realize_term.py` + receipts; wire ONE new line into
  `answer.render`: `in words   : <surface>` emitted **only when the
  round-trip gate passes at render time**, for authored and ingested
  nodes alike — the ingestion disclaimer stays, and the realized
  sentence gives parseable records a voice the boilerplate never had.
- The registered full-corpus run (`experiments/realization_rate.json`)
  reporting R0's parse table and R1's round-trip rate.
- Both skins inherit the new line through A-IH6; the capability sheet
  gains a `realization` row. No new HTTP surface.
- **Seal bookkeeping (recorded here so nobody improvises it):**
  `answer.py` and `harness.py` are witnessed by the committed v0.17
  task book, whose test asserts digests against the current tree. The
  v0.17 registered run is closed and its numbers stay frozen against
  the digests they were measured under; a post-run rendering change
  cannot "re-seal" that book (the spec's re-seal rule is pre-run and
  byte-identical only — its post-run clause, added at the v0.17
  rotation, governs here). v0.18's first rendering commit therefore
  **retires the v0.17 witness for future comparisons and rebuilds the
  book as a new sealed artifact** — digests re-recorded, the dated
  reason in the commit, the old artifact left untouched as the record
  of what was measured — and the book's digest test moves with it.

## 6. Construction gate

> **Gate history (2026-08-22):** the first draft froze R1 at 90% of
> all 12,777 terms. Adversarial review measured the committed tree
> and falsified that floor before implementation: only 17.0% of
> `canonical_ascii` terms parse at all. The floor below is scoped to
> the parseable denominator, and R0 exists because a number frozen
> without justification is how a gate becomes a wish.

- **R0 — construction prerequisite, discharged before R1 freezes.**
  Publish the parse rate of the source field under the byte-frozen
  parser, per corpus, failure classes named
  (`experiments/realization_rate.json` carries it). R1's floor is a
  fraction of the **parseable denominator**, reported beside it in
  every sentence that quotes R1. If the parseable denominator is
  below 50 nodes in every corpus but one, §8's stop condition has
  fired and the cycle publishes that instead.
- **R1 — round-trip floor.** ≥ 90% of parseable terms realize to a
  sentence whose re-parse canonicalizes to the source skeleton,
  overall. Per-corpus floors apply only to corpora with ≥ 50
  parseable terms; smaller corpora are reported individually with
  every failure named, never averaged (the v0.17 task book's
  thin-denominator lesson, imported). Failures are listed
  exhaustively (LOST = 0 discipline).
- **R2 — no invented surface.** Every content word in every emitted
  sentence traces to a lexicon row or the registered numeral pair;
  the receipt's `lexicon_entries` proves it, and a sweep asserts zero
  words outside those two sources across the full run. (This is R2's
  own floor — it parallels, but does not borrow, P-LS4's
  candidate-set 0-OOV floor, which governs a different domain.)
- **R2b — bijectivity.** Stated in §3; enforced at lexicon load.
- **R3 — refusal at the surface.** A term that does not parse, a term
  with an uncovered head, and a sentence that fails re-parse all
  refuse (`in words` line absent, reason available) — measured: 100%
  of injected uncovered-head and unparseable-term cases refuse; zero
  round-trip failures served.
- **R4 — the served surface stays honest.** The skin's T2 property is
  re-adjudicated over the new line: content remains a rendering of
  accepted engine output; the realized sentence appears only with a
  passing receipt; `test_serve_chat`'s honesty oracle extends to it.
- **R5 — determinism.** Same term, same lexicon, same parameters →
  byte-identical sentence.

## 7. Blind controls, each with its voiding sentence

- **C-R1 — the scrambled realizer, as a contrast, and one-sided by
  construction.** Realization emits through a shuffled lexicon
  (operators mapped to the wrong words, numerals through a scrambled
  digit map) and the reading path uses the **committed** table — never
  the shuffled one. The implementation probe (2026-08-23) proved why
  this must be said: a two-sided scramble is a consistent renaming,
  still a bijection, and round-trips near-perfectly — the control
  would void the reading for a reason with nothing to do with whether
  the gate reads the words. *The control is informative only if the
  true realizer's round-trip pass rate on the same term set is ≥ 20×
  the scrambled realizer's; if both are near zero the gate is
  untested and the reading is void; if the scrambled realizer passes
  ≥ 1% the gate is not reading the words and is void.*
- **C-R2 — the near-miss.** Mutations one operator word away from
  correct, **constructed only from swaps verified to change the
  canonical skeleton before realizing** (commutative-argument swaps
  and alias-class synonyms round-trip to the source legitimately —
  `canonicalize` sorts commutative arguments and aliases heads, and a
  control that voids on correct behavior is not a control). *If any
  skeleton-changing near-miss round-trips to the SOURCE skeleton,
  canonicalization is collapsing a distinction and the gate is
  void.* Floor: ≥ 50% of the mutation set must re-parse to a
  *different* skeleton rather than fail to parse — below that the
  set is exercising the tokenizer, not the canonicalizer, and the
  control is uninformative.
- **C-R3 — the tautology probe.** The parser+canonicalizer are
  byte-frozen before the realizer is written (digests recorded in the
  prereg commit); the inverter's digest is recorded beside them. *If
  implementing the realizer requires changing the parser, the
  independence claim is void and the change needs its own review
  naming the reason.*

## 8. Stop conditions and non-claims

Stop and publish if R0 leaves **no corpus** with ≥ 50 parseable terms
(the head/grammar inventory is thinner than the ownership ledgers
imply — a finding about the corpus; the tree already shows exactly one
corpus will clear that bar — `lean_workbook.ground.v1`, 2,040
parseable — so R1's per-corpus floor applies to it alone and all 26
smaller corpora report individually, per R1's own clause); if R1 lands
under 50% of the parseable denominator (linearization-with-round-trip
is the wrong mechanism at this grammar's scale — publish the failure
list and stop, no "exploratory" relabeling).

Non-claims: **no open-English input** this cycle (§3's carve-out
sentence governs the inverter); **no narrative prose**; **no claim of
fluency** — the sentences are correct and re-parseable, and their
style is whatever the grammar produces; **no throughput claim** —
rendering changes touch seal-witnessed modules, so any future timed
comparison starts a fresh seal cycle (§5's bookkeeping note); and
**no claim that slots speak their names** — `canonicalize` erases
slot identity, so the realized surface says "variable zero", not
"x"; the source identifiers ride in the receipt
(`parameters.slot_names`) and an R2-gated identifier surface is named
follow-on work, not smuggled in (registered honestly 2026-08-23 as
the served surface's biggest limitation).

## 9. The optional learned seat (bounded, behind the bar)

The *learned* preference seat is genuinely empty —
`scripts/preference.py` ships `preference.shallow.v1` with three
registered deterministic features and a frequency baseline, and the
empty seat named in DESIGN-text-resolution and
DESIGN-ambiguity-and-context is the ranker that would sit above
them. When the realization grammar admits multiple
round-trip-passing surfaces for one term, a learned ranker may order
them, behind the tool admission bar whole: comparator = the
**incumbent** (the seeded deterministic choice on the same
candidates — named as the incumbent, not mislabeled a blind
baseline), OFF-not-crash, closed outputs. The refuse/serve decision
is made by the round-trip gate *before* ranking, so a learned
component is never the difference between refusing and answering. If
no ranker clears the bar in-cycle, the seat ships empty again, in
writing — the v0.17 lane's symbolic-only readout carries forward
unchanged.

## 10. How status lands

Preregistration order: this design; the lexicon file with its head
coverage stated; the frozen parser+canonicalizer digests and the
registered numeral pair (C-R3); then `realize_term.py` + receipts +
tests; then the one registered full-corpus run
(`experiments/realization_rate.json`, R0 table + R1 rate). Fires,
misses, and voids land in ROADMAP-v0.18, ANALYSIS, DISCOVERIES,
BACKLOG; the v0.18 blog's forward section follows from this document.
If R1 fires, the questions that become askable next: the input side
(can the committed lexicon run backwards as the synonym layer
DESIGN-text-resolution §4 names — the corpus writes `gcd`, people
write "greatest common divisor" — a design, not a patch); realization
*parameters* as data (the linearization-rule row in
DESIGN-language-as-structure §2's table, which langgen hardcodes as
two word orders today); and the cost ledger that
DESIGN-grounded-throughput §10 named first, still parked, still owed.
