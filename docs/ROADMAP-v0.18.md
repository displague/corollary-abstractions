> **CLOSED at v0.18.0.** Where each item went: **item 1** (sans-template
> rendering) SHIPPED — R0 discharged first and published (2,172 of 12,777
> parseable, 17.0%, failure classes named per corpus), **R1 FIRES at
> 0.9991** (2,170 of 2,172, floor 0.90 of that same denominator; LOST = 0
> balances exactly, both refusals listed by id), R2 CLEAN (0 of 2,170
> surfaces carry a word outside the lexicon and the registered numeral
> pair), R5 pinned by a digest over all 2,170 served surfaces, and all
> three controls read out — C-R1 INFORMATIVE at an unbounded contrast
> (true 0.9991 vs scrambled 0.0000), C-R2 INFORMATIVE with zero of 3,722
> skeleton-changing mutations round-tripping to source, C-R3 HOLDS on all
> five pinned digests; see [RELEASE-v0.18.0](RELEASE-v0.18.0.md) headline
> and ANALYSIS. **Item 2** (the learned preference seat) **SHIPS EMPTY, in
> writing**, which is §9's registered outcome and not a miss: the grammar
> emits exactly one surface per term, so no candidate set exists for a
> ranker to order — licensed variant generation is named as the
> prerequisite and carried to [ROADMAP-v0.19](ROADMAP-v0.19.md) §4.
> **Release-gate obligations**, clause by clause: R0 published before R1
> was read; the registered run committed with its artifact; the empty seat
> read out; the first rendering commit **retired the v0.17 witness and
> sealed a successor book** under the SPEC post-run clause (one digest leaf
> moved, all 119 task records byte-identical, v0.17's results verified
> still frozen against their own `book_digest` pin); the refresh ran clean;
> and **the outside design inquiry was INVOKED, not reaffirmed** — three
> isolated series, nine rounds, receipt
> `reports/design-direction-v0.19.json`, with the incumbent
> DESIGN-block-vocabulary **adopted** rather than displaced. The strict
> wording this file restored is satisfied on its first use, and the loop §4
> opened is closed. The full-suite clause is open at `[SUITE-GATE-V18]` in
> the notes until the gate runs on the frozen tip.

# Roadmap v0.18 — the graph answered at wire speed; now make it speak

v0.17 put the knowledge graph behind an OpenAI-compatible endpoint and
timed it against a grounded 4B model holding the same committed records.
The kernel delivered 49 of 49 answerable tasks correctly with receipts at a
median 3,451 useful tok/s; the contender, told to quote verbatim, delivered
4, and its median was zero — so the frozen K = 5 is **satisfied unbounded
rather than measured** at the median, and reads 220× at the aggregate.

What that run also showed, task by task, is how small the surface it was
fast on really is. The kernel is fast because it *quotes* — and 12,515 of
the corpus's 12,777 nodes are ingestion records whose `statement_meaning`
is machine boilerplate, served with a disclaimer saying so. Quotation has
nothing worth quoting there. The authored vocabulary behind the definition
surface is 262 nodes.

This cycle moves that boundary — not by loosening the honesty rule and not
by adding a decoder, but by making the kernel **say its own structures**:
sentences composed by a realization grammar, each one gated by re-parsing
back to the exact term it claims to render, through a parser byte-frozen
before the realizer is written.

Governing design: [the graph speaks: sans-template rendering,
kernel-bound](DESIGN-sans-template-rendering.md) — **directed by the
maintainer** (2026-08-21, "bring phase 6 into the next release") and
separately *earned* by the registered trigger DESIGN-grounded-throughput
§10 wrote before the run. §10 named **two** successors and named the cost
ledger **first**; the directive selected the second. That is recorded here
and in §3, not absorbed.

**The design already produced this cycle's first finding — produced during
the v0.17 rotation, before a line of implementation exists.** Adversarial
review measured the committed tree and
**falsified the design's own first-draft floor**: the byte-frozen parser
parses `formal_statement.canonical_ascii` for **2,172 of 12,777 nodes
(17.0%)** — `lean_workbook.ground.v1`, which is 97.9% of corpus mass,
parses at 16.3%. A term that does not parse has no source skeleton to
round-trip to. So the corpus has outgrown its own template grammar, the
gate was rescoped to the parseable denominator before anything was built,
and **the parse-rate table ships as a first-class finding** naming, per
corpus and failure class, exactly where that happened.

## 1. Sans-template rendering (headline, architecture and product)

Implement DESIGN-sans-template-rendering in its §10 registered order, and
in no other:

1. the design (committed; its gate history note is part of the
   preregistration record);
2. the **lexicon file** — a first-class reviewed artifact mapping operator
   and constant heads to word forms — with its head coverage stated against
   the parseable corpus's head inventory before any sentence is realized;
3. the **byte-frozen parser and canonicalizer digests**, plus the
   **separately registered numeral pair** with its own tests (C-R3), all
   recorded in the prereg commit *before* `realize_term.py` exists;
4. `scripts/realize_term.py` + realization receipts + tests, wiring one new
   `in words   : <surface>` line into `answer.render`, emitted only when
   the round-trip gate passes at render time;
5. one registered full-corpus run → `experiments/realization_rate.json`,
   carrying R0's parse table and R1's round-trip rate.

**The gate is two-stage, and the roadmap says so because the distinction is
the whole claim.** Stage 1 is lexicon inversion — trusted, committed,
reviewed, bijective, and explicitly *not* an independent check. Stage 2 is
the byte-frozen structural re-parse, which has never seen the realizer and
is the part that can fail. Numerals are not a table but a genuine
algorithmic pair, registered separately, because an unregistered numeral
inverse is the hole this gate would otherwise leak through.

Gates **R0–R5 plus R2b** as frozen in the design: R0 the construction
prerequisite (publish the parse rate per corpus with failure classes named,
before R1's floor freezes; R1 is a fraction of the **parseable
denominator** and every sentence quoting R1 reports that denominator
beside it); R1 ≥ 90% round-trip over parseable terms, per-corpus floors
only where there are ≥ 50 parseable terms and smaller corpora reported
individually with every failure named, never averaged; R2 zero content
words outside the lexicon or the registered numeral pair; **R2b**
bijectivity enforced at lexicon load, refusing a table that is not
injective in either direction; R3 unparseable terms, uncovered heads and
failed re-parses all refuse at the surface, measured at 100%; R4 the skin's
T2 property re-adjudicated over the new line, with `test_serve_chat`'s
honesty oracle extended to it; R5 determinism.

Three blind controls, each with its voiding sentence. **C-R1 — the
scrambled realizer, in contrast form**: informative only if the true
realizer's pass rate is ≥ 20× the scrambled one's; if both are near zero
the gate is untested and the reading is void; if the scrambled realizer
passes ≥ 1% the gate is not reading the words and is void. A one-sided
threshold cannot tell "re-parse reads the words" from "re-parse rejects
everything", and this cycle does not get to find that out afterwards.
**C-R2 — the near-miss**, built only from swaps *verified to change the
canonical skeleton before realizing* (commutative-argument swaps and
alias-class synonyms round-trip to the source legitimately, and a control
that voids on correct behaviour is not a control), with a ≥ 50% floor of
mutations that re-parse to a *different* skeleton rather than failing to
parse. **C-R3 — the tautology probe**: parser, canonicalizer and inverter
digests recorded before the realizer is written; if implementing the
realizer requires changing the parser, the independence claim is void.

Both skins inherit the new line through A-IH6 — the TTY and the
chat-completions endpoint serve the same rendering the moment the engine
has it — and the capability sheet gains a `realization` row. No new HTTP
surface, and **no throughput claim**: `answer.py` and `harness.py` are
witnessed by the committed v0.17 task book, and a rendering change alters
their bytes. The v0.17 registered run is closed and its numbers stay frozen
against the digests they were measured under, so v0.18's first rendering
commit does **not** "re-seal" that book — the spec's re-seal rule is
pre-run and byte-identical only. Under the spec's **post-run clause**
(`docs/SPEC-chat-completions-skin.md` §6, added at the v0.17 rotation),
that commit **retires the v0.17 witness for future comparisons and seals a
new book of its own** — digests re-recorded, the dated reason in the
commit, and **the v0.17 artifact left untouched as the record of what was
measured**. Any future timed comparison starts from the new witness.

**Stop conditions, quoted so they are not renegotiated later.** Stop and
publish if R0 leaves **no corpus** with ≥ 50 parseable terms — that is a
finding about the corpus, and it is publishable. (The committed tree
already shows exactly one corpus will clear that bar:
`lean_workbook.ground.v1`, 2,040 parseable — so R1's per-corpus floor
applies to it alone and all 26 smaller corpora report individually, per
R1's own clause.) Stop and publish the failure list if R1 lands under 50%
of the parseable denominator. No "exploratory" relabeling in either case.

## 2. The learned preference seat (instrument lane, bounded, ships-empty allowed)

DESIGN-sans-template-rendering §9's seat. `scripts/preference.py` already
ships `preference.shallow.v1` with three registered deterministic features
and a frequency baseline; the genuinely empty seat is the *learned* ranker
that would sit above them. When the realization grammar admits several
round-trip-passing surfaces for one term, such a ranker may order them,
behind the tool admission bar whole: the comparator is the **incumbent**
(the seeded deterministic choice on the same candidates — named as the
incumbent, not mislabeled a blind baseline), OFF-not-crash, closed outputs.
The seat is safe by construction, because the refuse/serve decision is made
by the round-trip gate *before* ranking: a learned component can never be
the difference between refusing and serving a sentence.

If no ranker clears the bar in-cycle, **the seat ships empty, in writing**,
and v0.17's symbolic-only readout carries forward unchanged. That is an
honest outcome exactly as T6 was; it is not a miss and may not be reported
as one.

## 3. Carried, with dependants named

| lane | named dependant | disposition |
|---|---|---|
| **The cost ledger** — answers per joule and per dollar against hosted-model pricing | *none this cycle* | **parked, and named explicitly so it cannot vanish.** DESIGN-grounded-throughput §10 listed **two** successors to a fired T4 and listed this one **first**; the maintainer's directive selected the second. That is a choice between two registered successors, recorded here as a choice. It stays owed: DESIGN-sans-template-rendering §10 repeats it in its own forward list. Unpark needs a metrology this cycle has not designed (a measurement of energy and price that is not a vendor quote), which is exactly why it is parked rather than half-scheduled |
| Ledger-first claims (v0.17 course lead, gate L1–L13, hardened) | *none this cycle* | its own unpark rule made it a **headline candidate** the first cycle after the throughput readout — that is now — and it stays **parked** anyway, because the v0.18 headline is maintainer-directed to substrate Phase 6. Recorded, not dropped: design, gate and course receipt (`reports/design-direction-v0.17.json`) intact and preregistration-ready. Its mid-cycle lift trigger — a release again quoting a number its artifact no longer supports — stands unchanged |
| Open-English **input** | *none — explicitly out of scope of item 1* | parked. Item 1 renders terms the kernel already parses and does not read open English questions; the input side stays where DESIGN-text-resolution left it (FP floor 0.030, the lexical-semantics route refuted by measurement). One carve-out is stated in the design rather than discovered later: the stage-1 inverter *is* an open-English reader, however narrow — it reads only strings this cycle's own realizer produced, is not offered on the input side, and no request route calls it. Named follow-on if R1 fires: **can the committed lexicon run backwards as the synonym layer DESIGN-text-resolution §4 names** — the corpus writes `gcd`, people write "greatest common divisor" — as a design, not a patch |
| Realization *parameters* as data | *none* | parked; the linearization-rule row of DESIGN-language-as-structure §2's table, which `langgen` hardcodes as two word orders today. Becomes askable only if R1 fires |
| Chat-completions HTTP skin | — | **SHIPPED at v0.17.0**; five-cycle park history preserved in BACKLOG with a dated RESOLVED note. Its follow-on defects (context probe, `_route_ownership` receipt duplication, B-side notation asymmetry) are filed in BACKLOG, not carried as roadmap items |
| Sans-template open-prose rendering (substrate Phase 6) | — | **this cycle's item 1** |
| Unless-receipts, detached receipt, residual ledger, antibody, two referees, wild text, negative space, and the remaining course parks | *none* | parked with dispositions recorded in DESIGN-ledger-first-claims §2 and both course receipts |
| Load-bearing / premise-necessity | *named by ledger-first's residual* | parked, travels with it |
| Conservativity compiler, two witnesses, and older course parks | *none* | unchanged |
| Resolver coverage lane, A3–A5, verified-ambiguity, range certification, W1–W3 and the long tail | *none* | parked in BACKLOG, unchanged from the v0.15 drift audit |

## 4. Governance

Unchanged from v0.17, plus four entries this rotation owes. All four are
written decisions, not observations.

- **The outside design inquiry was NOT run for v0.18.** The standing
  receipt is `reports/design-direction-v0.17.json`, whose selected
  direction (ledger-first claims) is parked in §3 above with its reason.
  The obligation is **carried to the v0.19 gate**, and the brief that
  discharges it must carry **both** readouts — the throughput result and
  this cycle's realization result, whichever way R1 lands. Carrying only
  the flattering one would make the course a ratification.
- **A conflict between two governing texts, resolved in the open.**
  ROADMAP-v0.17's release gate wording is *"the outside design inquiry gate
  is discharged for v0.18 — run, or explicitly reaffirmed with the receipt
  named"*. The release skill's own wording is stricter: invoke the
  design-direction gate exactly once before drafting the next roadmap. The
  roadmap wording is looser, and **this cycle is cleared under the roadmap
  wording** — reaffirmed, receipt named, obligation carried — with the
  conflict recorded here rather than resolved by silence. This resolution
  is scoped to this cycle only, and it is the **orchestrator's recorded
  ruling under the maintainer's standing directive** ("bring phase 6 into
  the next release"), not a writer's judgment call; the maintainer can
  overrule it at any point before the v0.18 tag by asking for the inquiry
  to run. A **third** consecutive maintainer-directed
  headline without reopening the outside course requires a **written
  amendment to the course gate itself**, which is the maintainer's decision
  to make, not a rotation's.
- **Second consecutive maintainer-directed headline, recorded as
  first-class.** v0.17's governance addition says headline selection is
  part of the evidence trail, so this is written down rather than absorbed.
  What keeps it from being drift: the v0.18 direction coincides with a
  trigger registered *before* the run that fired it, the design was
  adversarially reviewed and had two of its own gates rewritten by
  measurement before commit, and the course obligation is reaffirmed rather
  than waived.
- **The instrument-first-headline suspension expires with its cycle.**
  DESIGN-grounded-throughput §9 suspended instrument-first headline
  selection **"for the v0.17 cycle"**; its lift trigger — a product-lane
  failure naming a missing instrument — **never fired**, because the
  product lane did not fail. So the suspension is neither lifted early nor
  extended by silence: it ends with the cycle it was scoped to, and the
  fact is recorded because an unrecorded expiry is the same drift as an
  unrecorded park. Nothing turns on it here — v0.18's headline is a product
  lane regardless — but the first cycle whose headline candidate *is* an
  instrument owes a fresh decision rather than an inherited one.

## Release gate

v0.18 is ready only if:

- R0 is discharged and published before R1's floor is read, with the parse
  table per corpus and its failure classes named;
- sans-template rendering ships its registered full-corpus run with R1–R5
  and R2b adjudicated and C-R1–C-R3 read out, **or** stops on a named §8
  stop condition with the reading published — a sub-50% R1 with its failure
  list, or a corpus too thin to give R1 a denominator, is a publishable
  result and not a failure to ship;
- the learned preference seat reads out (a registered ranker with its named
  incumbent comparator, or "seat ships empty" in writing);
- the first rendering commit retires the v0.17 witness and seals a **new**
  book — digests re-recorded, dated reason in the commit, the v0.17
  artifact left untouched as the record of what was measured (the spec's
  post-run clause, §6);
- `check_report_regeneration.py` runs in the release refresh with its
  verdicts in the notes;
- the full suite is green on a frozen tip with retained receipts;
- every unfinished item ships or parks in writing;
- the outside design inquiry is **invoked** for v0.19 — the forge skill
  run, or a written course-gate amendment by the maintainer — with the
  receipt named. This is the release skill's strict wording, deliberately
  restored in place of the looser "run or explicitly reaffirmed" that §4
  used to clear v0.18, and it closes the loop that ruling opened: a
  reaffirmation was available once, recorded once, and is not available
  again by inheritance. The v0.19 course brief carries both the throughput
  readout and the realization readout, whichever way each landed.
