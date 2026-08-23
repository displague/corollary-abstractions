# v0.18.0 — the graph speaks, and every sentence carries its own proof

Last cycle the graph answered at wire speed by quoting. This cycle it says
things nobody wrote: English sentences composed by a grammar from the
mathematics itself, each one gated at render time by feeding it back
through a parser that was byte-frozen before the writer existed and
checking that the exact source structure comes out. **2,170 of 2,172
parseable terms round-trip — 0.9991 — out of 12,777 corpus nodes**, and
that last clause is not a caveat bolted on afterwards: R0 is a gate, and it
makes the denominator impossible to quote the rate without.

The cycle's other product is less flattering and more useful. **Five
sentences in the governing design were corrected by measurement**, four of
them before they could mislead a run, and the fifth was a receipt field
that was wrong on one term in twenty.

**Links** — previous release: [v0.17.0](RELEASE-v0.17.0.md) · closed plan:
[ROADMAP-v0.18](ROADMAP-v0.18.md) · next plan:
[ROADMAP-v0.19](ROADMAP-v0.19.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the alphabet was half the wall](blog/the-alphabet-was-half-the-wall.md)

## The headline finding

**Before.** Every sentence this system served was either a verbatim
quotation or a composition from closed banks and f-string patterns. For the
12,515 ingested nodes whose `statement_meaning` is machine boilerplate,
`answer.render` served a disclaimer saying so — quotation had nothing worth
quoting. The formal statement was exact structure the kernel owned
completely, and the system could not say it out loud.

**Now.** `scripts/realize_term.py` linearizes a canonical term into an
English sentence and returns a **realization receipt**; `answer.render`
emits one new line, `in words   : <surface>`, and **only** when that
receipt reads `round_trip == "EXACT"`. Both skins inherit it through
A-IH6. The registered run executed once on the committed tree:

| gate | verdict | deciding number |
|---|---|---|
| **R0** — parse rate published *before* R1 is read | discharged | **2,172 of 12,777 parseable (0.1700)**; failure classes named — 10,432 unexpected character, 111 trailing tokens, 53 expected-delimiter, 6 `\|`, 2 `[`, 1 `>`. Stop condition did **not** fire: `lean_workbook` clears 50 parseable at 2,040 |
| **R1** — round-trip floor 0.90 of the parseable denominator | **FIRES** | **2,170 of 2,172 = 0.9991.** Zero round-trip failures; two refusals. Per-corpus floor applies to `lean_workbook` alone (FIRES at 0.9990); the other 26 corpora are reported individually, never averaged |
| **R2** — no invented surface | **CLEAN** | **0 of 2,170** served surfaces carry a word outside the lexicon and the registered numeral pair |
| **R5** — determinism | pinned | sha256 over all 2,170 served surfaces = `d3b6ee9b…`, first 25 by statement id pinned verbatim |
| **C-R1** — the scrambled realizer, one-sided by construction | **INFORMATIVE** | true 0.9991 vs scrambled **0.0000**; contrast unbounded against a ≥20× bar, nowhere near the ≥1% voiding bar |
| **C-R2** — the near-miss | **INFORMATIVE** | **3,722** skeleton-changing mutations, **0** round-tripped to the source, 3,720 re-parsed to a *different* skeleton (0.9995 against a 0.50 floor) |
| **C-R3** — the tautology probe | **HOLDS** | all five pinned artifacts byte-identical to what the preregistration commit recorded |

**LOST = 0 balances exactly**: 2,170 served + 0 round-trip failures + 2
refusals = 2,172, and both refusals are listed by statement id with their
full detail. They are the two oversized `lean_workbook` literals — one
76-digit, one 48-digit — **refusing rather than rounding**, because the
registered numeral pair's domain is `|n| < 10^15` and a numeral outside it
has no honest words.

**What C-R1's failure modes say, and why they are reported separately.**
"The control failed" is uninformative on its own. Of the 2,172 scrambled
sentences, **1,348 parsed perfectly well and meant something else**, and
822 did not parse at all. A control producing only the second would be
exercising the tokenizer, not demonstrating that stage 2 reads the words.

**Demonstrate.**

```
python scripts/realize_term.py --census
python -m unittest tests.test_realize_term tests.test_realization_lexicon
```

The registered artifact is `experiments/realization_rate.json`; the frozen
digests it revalidates are in `experiments/realization_prereg.json`. Full
readout: ANALYSIS "v0.18 — the graph speaks: the census, the registered run,
and three controls".

## The second finding: five design sentences, corrected by measurement

A design is a claim about a tree, and this cycle checked five of them. Four
were wrong before implementation could act on them; the fifth was wrong in
a published receipt. None was quietly patched — each is a **dated
correction** in the design or in
`experiments/realization_prereg.json`'s `corrections` list.

| the sentence as written | what measurement said | consequence |
|---|---|---|
| R1's floor is 90% of all 12,777 terms | only **2,172 (17.0%)** parse at all; a term that does not parse has no skeleton to round-trip to | falsified at the **v0.17 rotation, before implementation**. R0 was created as a construction prerequisite and R1 rescoped to the parseable denominator |
| the corpus carries 95 call heads, 39 singletons, a top-10 led by `IMPLIES` and `MEET` | that read `anonymized_template` — **the wrong field for this cycle**. The `canonical_ascii` parseable subset carries **64 heads, 35 singletons, and neither `IMPLIES` nor `MEET` at all**; re-measured on the template side it is 95 heads, **30** singletons, `MEET` (22,653) ahead of `IMPLIES` (10,202) | the lexicon was authored against the *measured* inventory and chose to cover both whole, so the refusal path is exercised **by injection, not by accident** |
| C-R1 is a scrambled realizer | a **two-sided** scramble — deranging the table and reading through that same deranged table — is a consistent relabelling, still a bijection, and round-trips near-perfectly (4 of 4 pinned in tests) | C-R1 is now **one-sided by construction** and says so in its own artifact body. The two-sided run is kept as the *aiming* test — 7 of 7 — which is what proves the scramble breaks word identity rather than the grammar |
| `canonicalize` aliases heads, so alias-class swaps must be excluded from C-R2 | it does **none**. `alias_heads` is a separate pass only the ALIASED match level runs, and `MOD` vs `CONCAT` canonicalize to **different** skeletons at the level this gate compares | alias-class swaps moved from C-R2's *exclusions* into its *set*. A test that had asserted the opposite was renamed to describe what it actually demonstrated — symmetric relations |
| the receipt publishes one slot-name map | the surface numbers slots by first occurrence in `canonicalize()`'s tree; `term_skeleton`'s `?N` come from `render_skeleton` over `shape_resort()`'s tree. **They disagree on 110 of 2,170 served terms (5.07%)** | the receipt now publishes **both** maps — `surface_slot_names` and `skeleton_slot_names` with `slot_index_basis` naming which is which. No sentence and no verdict moves (`skeleton()` is invariant under slot renaming); **only a reader would have been misled**, on one term in twenty |

The fourth of those is the one worth pausing on: it was found by writing a
control, and it *widened* the control's set rather than narrowing it. A
mutation the design had excluded as an artifact of canonicalization turned
out to be a legitimate near-miss, so C-R2 got harder, not easier, on the
strength of a correction.

## Roadmap triage

**Shipped.** *Item 1 — sans-template rendering.* Implemented in the
design's §10 registered order: the lexicon, numeral pair and frozen digests
(`ccac853`, with `e28f8d6` correcting two node-keyed operator rows before
the realizer landed), `realize_term.py` and its two-stage gate (`9879b06`),
the adversarial review closed at one High, six Medium and nine Low each
dated (`98ea2cf`), the one registered run (`ecb906d`), and the wiring
(`5357740`). Numbers in the headline.

**Shipped as an empty seat, in writing — which is what §9 registered.**
*Item 2 — the learned preference seat.* It ships empty, and the reason is
sharper than "no ranker was ready": **the realization grammar emits exactly
one surface per term**, so there is no candidate set for a ranker to order.
The seat was never blocked by the admission bar; it was blocked by the
absence of anything to rank. **Licensed variant generation** is named as
the prerequisite and carried to [ROADMAP-v0.19](ROADMAP-v0.19.md) §4 with
its unpark condition: a design that says what licenses a *second* passing
surface for the same term, and why that is not decoration. v0.17's
symbolic-only readout carries forward unchanged.

**The gate obligations, clause by clause.** R0 published before R1 was
read. The registered run committed with its artifact and byte-reproducible
(a second full run reproduces the same digest). The empty seat read out.
The first rendering commit **retired the v0.17 witness and sealed a
successor book** (below). The refresh ran clean. And **the outside design
inquiry was invoked, not reaffirmed** (below). The full-suite clause is
open at `[SUITE-GATE-V18]`.

**Drift audit** (v0.16 and v0.17 re-read, per the rule). Nothing was found
lost to attrition. Two lanes are now on their third recorded pass-over and
are named rather than left to erode: the **cost ledger**, which
DESIGN-grounded-throughput §10 listed *first* among two successors and
which has been passed over twice by direction and once by course; and
**ledger-first claims**, whose unpark rule made it a headline candidate at
v0.18 and again at v0.19, declined both times for a written reason. Both
carry into ROADMAP-v0.19 §4 with their triggers intact. One debt was found
and is being paid in this rotation rather than deferred again: two
load-bearing lessons from this cycle — C-R1's one-sidedness and the
prefix-free rule — existed **only** in commit bodies and module
docstrings, and are landed in DISCOVERIES here, dated, before v0.19 borrows
them.

## What changed, per area

### The lexicon, the numeral pair, and five digests frozen before the writer existed

**Before.** No realization lexicon existed, and nothing pinned the parser
that would grade a realizer.

**Now.** `data/realization/lexicon.json` is a first-class reviewed artifact
mapping operator and constant heads to word forms; `scripts/numeral_words.py`
is a **separately registered algorithmic pair** rather than a table,
because an unregistered numeral inverse is the hole the gate would
otherwise leak through. Five artifacts were byte-frozen and their digests
recorded **before** `realize_term.py` was written — the parser, the numeral
pair, the lexicon, the lexicon loader and (once it existed) the inverter —
and C-R3 revalidates all five in the registered run.

One correction landed between preregistration and the realizer, dated in
the prereg rather than folded in silently (`e28f8d6`): the first
preregistration commit emitted every operator row's **key** as its token,
which is correct for `+` and `*` but wrong for `inv` and `neg`, whose keys
are names rather than glyphs. `operator_tokens` was added with a loader
clause, and the B7 check that came with it was later found to inspect only
call-head keys — the one place the bug it was written for did not live.

The table is **prefix-free, not merely longest-match**, and that is a
guarantee rather than a policy: the loader gates L1 (no phrase is a proper
word-prefix of another) and L2 (no phrase word is a word the numeral pair
can emit), checked constructively over every ordered pair and over the
decode of all 169 phrases concatenated — never sampled. The consequences
are recorded in the table itself: `-` and `/` get no rows, `~` gets no row,
and `neg` reads *"the opposite of"* rather than *"the negative of"* because
"negative" is numeral vocabulary and L2 forbids the collision.

**Demonstrate.** `experiments/realization_prereg.json` — the five-entry
`frozen` list and the seven dated `corrections`; `python -m unittest
tests.test_realization_lexicon` (37 tests).

### The two-stage gate, and where the structure is allowed to live

**Before.** —

**Now.** The design's whole claim is a split, and the implementation puts
it where it can be checked. **All precedence lives in the forward
grammar**, as a five-level ladder read straight off the frozen recursive
descent (relation 0, sum 1, product 2, power 3, atom 4); a subterm gets
grouping words exactly when its own level is under the level its context
accepts, so parenthesisation is minimal and *the writer* decides it.
**Stage 1 gets none of that**: `delexicalize` takes the longest matching
phrase or a numeral run and emits tokens in surface order — no bracket
counter, no arity, no precedence table. A test hands it an *unbalanced*
grouping word and pins that it happily emits `(`, because noticing is stage
2's job. **Stage 2 is `tokenize → Parser → canonicalize → skeleton`**,
imported and never reimplemented — and a test greps the module to prove it
defines no parser of its own.

**Demonstrate.**

```
PYTHONIOENCODING=utf-8 python scripts/realize_term.py --term "1 + 1 = 2"
```

prints the whole receipt: `"surface": "two equals one plus one"`,
`"round_trip": "EXACT"`, `"term_skeleton": "2 = +(1, 1)"`, and the
`lexicon_entries` that were used. Exit 0 when the term is served, 1 when it
is not.

### The registered run, and why it needed a separate runner

**Before.** —

**Now.** `scripts/measure_realization.py`, in the repo's own `measure_*.py`
convention. The reason is worth stating because it is the kind of thing
that is invisible once done: `realize_term.py` is **digest-pinned as the
inverter**, so giving it a `--registered` mode would have moved the very
digest that certifies the number the mode produced. The five pinned modules
stay byte-frozen through the run. C-R2 needs to realize mutated *trees*, so
it reuses `realize_term`'s own linearizer, slot ordering and `reparse` with
local glue — same linearizer, same two-stage gate, transcribed entry point.

The run is **byte-reproducible, verified twice**: a second full pass over
`data/` at the run commit reproduced the artifact exactly, and re-running it
during this rotation produced canonical-LF sha256 `803fe00a…` — identical to
the committed file. No timestamp, no elapsed time, no absolute path rides
in the artifact, and a test asserts their absence over *keys* rather than
substrings. Wall clock is deliberately **not** recorded for that reason: the
run took 37.2 s at the run commit and 55.5 s when re-run here, and the
artifact is the same bytes either way.

**Demonstrate.** `experiments/realization_rate.json`; the `provenance`
block names the writer and every input with its canonical-LF digest.

### Two findings from building the controls, both now pinned as tests

**`a < b` and `b < a` are the same skeleton.** `<` is not symmetric, but
`render_skeleton` erases slot identity and renumbers by first occurrence,
so two bare slots either side of *any* relation are indistinguishable. A
near-miss set built on "non-symmetric relation implies swapping changes the
skeleton" would have been full of non-mutations, every one would have
"round-tripped to the source", and **the control would have voided the gate
for behaving correctly**. C-R2 now verifies every mutation against the
skeleton *before* realising and counts the discards — 31 in this run.

**A refusal path that would have shipped decorative.**
`revalidate_prereg(prereg_path=PREREG_PATH)` bound the module global at
definition time, so a caller pointing it at a different preregistration was
silently revalidated against the committed one and the run was written
anyway. The refusal test caught it by *failing to see a refusal*. The
default is now read at call time, `--prereg` exists, and the test asserts
exit 3, the reason on stderr, and that no file was created.

### The line, the refusal, and the first ingested record with a voice

**Before.** An ingested node answered with a disclaimer over machine
boilerplate and nothing else.

**Now.** `answer.render` emits `in words   : <surface>` when — and only
when — the realizer returns a served realization. **R3 is refusal at the
surface**, so a term that does not parse, an uncovered operator head and a
failed re-parse all produce **no line at all**: not an error string, not a
placeholder. Absence is the refusal, and the reason lives in the receipt
for anyone who calls the realizer directly. Both refusal arms are pinned to
ids named in the registered run's exhaustive refusal list, so a term that
stopped refusing shows up as a failing test rather than as a quietly better
number.

`leanworkbook.ground.lean_workbook_13563` now serves the ingestion
disclaimer **and** `in words   : two equals one plus one` — the first
machine-ingested record in this repository with a voice.

The capability sheet gains a `realization` row that quotes R1 **from
`experiments/realization_rate.json`** rather than from a number pasted into
the module, because a rate restated in code is a rate that goes stale — and
when the artifact is unreadable the row publishes `"served": false` with
the reason rather than a stale number. R4 extended `test_serve_chat`'s
honesty oracle over the new line (74 tests in that module now), and the
HTTP skin's verbatim pass-through of answer lines is now **asserted rather
than assumed**.

### The new seal: retire and re-seal, not re-seal in place

**Before.** v0.17's task book witnessed eleven rendering modules, and its
pre-run re-seal rule was byte-identical-only.

**Now.** This cycle changes `answer.py`'s rendered bytes, so the pre-run
rule does not apply. Under the **post-run clause** added to
`docs/SPEC-chat-completions-skin.md` §6 at the v0.17 rotation, this commit
does **not** re-seal the v0.17 book: it **retires that witness for future
comparisons and seals a successor book in its place**. Verified by
structural diff, not asserted — exactly one leaf moved
(`/rendering_module_digests/scripts/answer.py`), all 119 task ids, halves,
turns and expected records byte-identical, `half_b_seal` unchanged. And
v0.17's numbers were **verified still frozen against the artifact they were
measured under**: the `book_digest` recorded in every
`experiments/throughput_result*.json` (`6e60bcd5…`) is the canonical-LF
digest of the v0.17 book, while the successor book digests `416c802a…`. The
v0.17 artifacts and the v0.17.0 tag are untouched.

Two things were checked rather than assumed. The task book pins no rendered
answer text — `content_must_contain` holds corpus field values and no label
string appears anywhere in the task set — so a new line can move a digest
but cannot break a task's scoring. And `session_run --check` never calls
`answer.render`, so the recorded transcript needed no regeneration.

## Discoveries of the cycle

Quoted from [DISCOVERIES](DISCOVERIES.md):

- *"Five design sentences were corrected by measurement, four before
  implementation could act on them."* A design is a claim about a tree, and
  checking it is cheaper than a failed run.
- *"Half the mute corpus was an alphabet problem, not a grammar problem."*
  6,414 of the 10,605 unparseable statements — **50.2% of the whole
  corpus** — parse after substituting exactly two glyphs.
- *"A two-sided scramble is a renaming."* A control that deranges a
  bijective table and then reads through the *same* deranged table
  round-trips near-perfectly and voids the reading for a reason with
  nothing to do with the gate.
- *"The first ingested record with a voice."* One of 12,515 machine
  boilerplate nodes now says `two equals one plus one`, with a receipt
  proving the sentence re-parses to exactly that term.

Also landed here, dated, paying a debt this rotation's audit found: the
C-R1 one-sided lesson and the prefix-free rule, which until now existed
only in commit bodies and module docstrings.

## Resolved from BACKLOG

- The **"unrestricted prose authoring (item 9, still last)"** language is
  discharged as far as this slice goes: the Phase 6 rendering half shipped
  and is measured. The entry is annotated, not pruned, because the phrase
  covered more than this slice — open-English *input* and narrative
  authoring both remain out of scope and stay filed.
- **Newly filed** this cycle: the realizer follow-ons (an R2-gated
  identifier surface, `±` coverage, the conditional-bar note), the
  transliteration lane pointer with its re-freeze discipline, and the
  STRANGER gap-object intake parked from the v0.19 course with its
  degradation rule quoted.
- Still open and unchanged: `_route_ownership`'s receipt duplication. It is
  now on its second cycle. The seal reason that deferred it at v0.17 has
  lapsed — the v0.17 run is closed — so what remains is that the fix rides
  a book re-seal, which this cycle's successor seal has now made routine.

## Honest limits carried forward

- **The rate is 0.9991 of 17.0%.** R0 exists so that sentence cannot be
  split, and this release does not split it anywhere.
- **Slots do not speak their names.** `canonicalize` erases slot identity,
  so the realized surface says *"variable zero"*, not *"x"* — registered in
  the design as the served surface's biggest limitation. The source
  identifiers ride in the receipt, and an R2-gated identifier surface is
  named follow-on work rather than smuggled in.
- **The two receipt slot maps can disagree**, on 110 of 2,170 terms
  (5.07%). Both are now published with a basis note. The gate never
  depended on the numbering; a reader might have.
- **Conditional notation is collapsed by the parser.** `E[Y|X]` reads as a
  two-argument expectation and round-trips as one, so the realized sentence
  renders the bar as "next argument". Where the distinction matters it
  lives in the source term, not the surface.
- **Two terms refuse rather than round.** The registered numeral domain is
  `|n| < 10^15`; the 76-digit and 48-digit `lean_workbook` literals have no
  honest words, and refusing is the designed behaviour, not a miss.
- **C-R1 is one-sided on purpose**, and its two-sided counterpart is an
  aiming test rather than a control. Slot indices are deliberately not
  scrambled: `skeleton()` is invariant under slot renaming, so a bijective
  index scramble would pass 100% and measure nothing.
- **No throughput claim.** Rendering changes touch a seal-witnessed module,
  so any future timed comparison starts from the successor book, not from
  v0.17's numbers.
- **The learned seat is empty for a structural reason**, and the
  prerequisite is variant generation, not a better ranker.
- A passing Python test is not a Lean proof.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.** `git diff
--name-only v0.17.0..HEAD -- data/ experiments/` lists **five paths and not
one `.py`**: `data/realization/lexicon.json` (a new reviewed artifact — a
lexicon, not a training input), and four ledgers —
`experiments/realization_census.json`,
`experiments/realization_prereg.json`, `experiments/realization_rate.json`,
and `experiments/throughput_tasks.json` (the successor sealed book). No
training corpus moved and no `experiments/*.py` changed, so **the
checkpoints attached to v0.6.0 remain accurate for this release**.
Committed in-repo and linked by path rather than uploaded: the registered
run's artifact, the preregistration with its frozen digests and dated
corrections, the R0 census, and the lexicon itself.

## The outside design inquiry, invoked

ROADMAP-v0.18 restored the release skill's strict wording — the inquiry
must be **invoked**, not reaffirmed — after v0.18 itself was cleared under
a looser clause with the conflict recorded in the open. **On its first use,
the strict wording was satisfied.** The forge skill ran: three isolated
series, three rounds each, from an empty non-git directory outside the
repository under a full tool denylist, with session ids, costs and per-round
prompt hashes committed in `reports/design-direction-v0.19.json`. Fifteen
round-one directions, three finalists — LOANWORD, FORK, TWO RIGHTS — and a
selection with **every declined direction's disposition written down**.
Selected: LOANWORD → [DESIGN-foreign-voice](DESIGN-foreign-voice.md).

The maintainer-seeded incumbent, `DESIGN-block-vocabulary`, is **adopted as
a bounded roadmap item rather than displaced or quietly parked** — which is
how the no-silent-disposal instruction is discharged. All fifteen
directions differentiated themselves from the incumbent unprompted, and the
two cross-series near-collisions were disclosed by the advisors themselves.

The loop ROADMAP-v0.18 §4 opened is therefore closed: the reaffirmation was
available once, was recorded once, and was not taken again.

## The release refresh

Every generated ledger regenerated on the tip and the working tree came
back byte-clean: 25 seeds byte-identical, 12,777 nodes across 27 corpora
valid, `signature_matches`, `specializations` and `compression` clean,
`ingest_wold.py reach` re-run against the pinned archive (1,395 of 1,460
core LWT meanings map, 95.5%), and `check_report_regeneration.py` reporting
three ledgers clean with `decompositions.json` a **declared** divergence
carrying its TRIAGE-v0.11 citation.

## The suite at the tip

[SUITE-GATE-V18: full-suite verdict and timing at the frozen v0.18 tip land
here before the tag. The baseline is v0.17.0's gate — **1,705 tests, 0
failures, 3 skipped, 27,068.5 s (7 h 31 m)**, receipts in
`reports/test_gate_v017/` including the five pre-green runs. This cycle
adds three wholly new modules — `test_realize_term` (44),
`test_realization_lexicon` (37), `test_measure_realization` (26) — and
takes `test_serve_chat` from 68 to 74, so the expected count is 1,705 + 107
+ 6 plus whatever `test_answers` gained.]

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/check_report_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py

# 1. the R0 census -- the denominator, before any rate is read
python scripts/realize_term.py --census

# 2. realize one term at the command line, receipt and all
PYTHONIOENCODING=utf-8 python scripts/realize_term.py --term "1 + 1 = 2"

# 3. the registered run, re-run: byte-identical to the committed artifact
python scripts/measure_realization.py --out realization_rate.repro.json
python -c "import hashlib; f=lambda p: hashlib.sha256(open(p,'rb').read().replace(b'\r\n',b'\n')).hexdigest(); \
    print(f('realization_rate.repro.json') == f('experiments/realization_rate.json'))"

# 4. the served line: boot the skin and ask for a definition
python scripts/serve_chat.py            # in one shell; 127.0.0.1:8377, no flags needed
curl -sS http://127.0.0.1:8377/v1/capabilities | python -m json.tool   # the realization row
curl -sS http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"algtop.homology.betti_alternating_sum"}]}'

# 5. the refusal arm: parses, then refuses, and serves NO in-words line
curl -sS http://127.0.0.1:8377/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"corollary/kernel","messages":[{"role":"user","content":"leanworkbook.ground.lean_workbook_37421"}]}'

# 6. the gates, by name
python -m unittest tests.test_realize_term tests.test_realization_lexicon \
    tests.test_measure_realization tests.test_serve_chat tests.test_answers
```

Step 3 reproduces the headline number from the committed tree, and
**refuses with exit 3, writing nothing**, if any of the five preregistered
digests disagrees with what is on disk. Step 4's answer carries

```
in words   : variable zero equals the summation of the quantity variable one times the opposite of one to the power of variable two end quantity
```

under its `formally   :` line. Step 5's answer carries **no** `in words`
line and no explanation of the absence — that is R3 working, not a bug. The
five modules in step 6 are 201 tests together (44 + 37 + 26 + 74 + 20).
