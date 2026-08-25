> **CLOSED at v0.19.0.** Every item read out, and three of the four
> readings are smaller than the plan hoped for. **Item 1** (the foreign
> voice) shipped its full preregistration chain and its registered run, and
> the run is **VOID**: every B-gate FIRES — B0a 4,191 residue, B0b+c 2,319
> accepted, B0d **100 of 100 sealed hand-renderings reproduced
> byte-identically with zero divergences**, B1 **1.0 (2,313 of 2,313)**, B3
> closing exactly at 10,605, B5 byte-identical — and C-V1 and C-V2 both
> HOLD, but **C-V4 voids on `drop_group`, 0.80 against its 0.90 floor**, so
> the overall verdict is VOID and B1's 1.0 may not be quoted without it.
> **The foreign `in words` line is therefore NOT wired**: serving under a
> voided certification is exactly what the voiding sentence forbids. The
> **register** is the headline artifact, as the design's own rule said it
> would be. **Item 2** (the address-space probe) is **PARKED WITH THE
> NUMBERS** by its own rule — 1 of 3 baselines beaten and it is the
> pre-conceded one; the single question is answered *two existing objects
> wearing one id space* (tag-bit ratio 0.9981). **Item 3a**
> (transliteration) is the cycle's product number: **two glyphs take the
> native voice from 17.0% to 67.2%**, 6,414 statements gained against a
> floor of 6,000, round-trip 1.0000 over the newly-reached set, served diff
> additive-only corpus-wide. **Item 3b** (TWO RIGHTS B0) landed as a
> **narrow census and an unqualified registered negative**: 125 notational
> candidates, **zero** mathematical convention forks, and the famous
> clashes a clean zero — so the full direction parks with an empty
> denominator. See [RELEASE-v0.19.0](RELEASE-v0.19.0.md) and ANALYSIS.
> **Release-gate obligations**: B-P discharged before B0 froze; B0
> published all four parts before implementation; the register shipped
> frozen and digested; both registered probes committed their artifacts;
> the v0.18 lesson debt was paid at that rotation; the re-freeze discipline
> was executed whole (amendment before code, both prior rates declared
> historical in writing, both old registered CLIs closed so neither can
> mint a blended rate). The **v0.20 course ran and selected** — see
> [ROADMAP-v0.20](ROADMAP-v0.20.md). Full suite: **2,106 green
> (5 skips) at 67a1506, first run** — reports/test_gate_v019/.

# Roadmap v0.19 — say the part you cannot read, or say exactly why not

v0.18 gave the kernel a voice and a receipt for every sentence it speaks.
The registered run put the round-trip rate at **0.9991 — 2,170 of 2,172
parseable terms** — with zero round-trip failures and two honest refusals.
That is the floor this cycle stands on. It is also the result that names
the problem out loud, because R0's rule makes it impossible to quote the
first number without the second: **2,172 of 12,777 is 17.0%**. The other
**10,605 nodes (83.0%)** carry a `formal_statement.canonical_ascii` the
committed parser cannot read, and for them `answer.render` still serves the
ingestion disclaimer over machine boilerplate. The corpus's mass is mute.

The v0.19 course went looking for the boundary worth moving next and
returned one: borrow. Render English for the foreign dialect from a frozen
hand-authored lexicon, and gate it not by a parser this project owns but by
the **already-pinned external Lean checker**, using the checker's
elaborated term as the identity witness. The headline artifact is not the
rendering rate. It is the **register**: a frozen, digested inventory of
what the system cannot say, with the blocking construct named and counted.
A system that renders 60% of a corpus and shrugs at the rest has told you
nothing about the rest.

Governing design: [the loanword: the graph speaks a dialect it cannot
read](DESIGN-foreign-voice.md) — selected by the outside course, three
isolated series, nine rounds, receipt
`reports/design-direction-v0.19.json`.

> **Status note (2026-08-23, at rotation).** DESIGN-foreign-voice is
> **under adversarial review as this roadmap is drafted.** Its numbers and
> gate names are quoted here from the document as it stands; corrections
> the review lands will be dated in the design and reflected here rather
> than absorbed, exactly as v0.18's five corrections were. Every sentence
> in item 1 below that depends on the design's unreviewed content is a
> sentence that may move.

**The grounding pass already corrected the direction before implementation,
and the correction is a finding in its own right.** The advisor's proposal
assumed the 83% was foreign. It is not — **half of it is the same grammar
in a different alphabet**. Of the 10,605 mute statements, **6,414 parse
under the byte-frozen committed parser after substituting exactly two
glyphs**, `≥`→`>=` and `≤`→`<=`. That is **50.2% of the whole corpus**,
mute for want of two rows in an ASCII-only `TOKEN_RE`, not for want of a
bridge to another language. Rendering those through a loanword pipeline
would let this cycle claim a hard result for easy territory, so they are
**excluded from the claim, named transliterable, and handed to item 3**.
What is left is the design's actual territory: the **4,191-statement
foreign residue (32.8%)** — quantifiers and typed binders, logical
connectives, type ascriptions, namespaced heads — of which **2,319 are
oracle-eligible by outcome** (accepted by the pinned binary under the
frozen interpretation rule with `autoImplicit false`; the design review
retired an earlier blocklist-derived 1,456 in favor of this operational
definition — a dated correction, not a silent move).

## 1. The foreign voice and its register (headline)

Implement DESIGN-foreign-voice in its §10 registered order, and in no
other:

1. the design (committed; its dated corrections are part of the
   preregistration record);
2. **B-P first** — `prover/lean/normalizer/Serialize.lean` plus its Python
   driver, with tests asserting **binder-name independence** (prototyped
   during grounding under the pinned binary and proven) and two-run byte
   identity. Nothing downstream is meaningful if the identity witness is
   not stable, so it is discharged before B0 freezes;
3. the **loanword lexicon** over the constructors the oracle-eligible
   residue actually carries, head coverage stated in the file the way
   `data/realization/lexicon.json` states it, with the refusal path
   exercised **by injection rather than by accident**;
4. the **frozen register** with its `blocked_set_digest`, digested before
   the first render — B4 exists so the inventory of silence cannot be
   edited after seeing what the renderer failed on;
5. `scripts/foreign_voice.py` + per-statement receipts + tests;
6. one registered run, `experiments/foreign_voice_rate.json`, carrying
   B0a–B0d's tables, B1's rate over the covered set, B3's arithmetic, and
   every control's reading.

**The gate is B-P and B0–B7.** B0 is an **abort probe** run before any
implementation and published either way — B0a the transliterable/foreign
split (preview: 4,191), B0b+B0c the oracle's reach as one measurement,
eligibility by outcome (preview: 2,319), and **B0d the inverse
direction, unpreviewed and the real probe**. B1 is the identity floor at
**≥ 99.5%** of the covered set. B2 makes rejection a **failure, not a
skip** — the oracle's three outcomes are distinguished and a rejection
counts against the rate. B3 requires the arithmetic to close exactly:
`transliterable + covered_served + covered_refused + registered_blocked =
10,605`, printed in the artifact, with any statement in none of those
categories a construction failure. B4 freezes the register first. B5 is
determinism and hermeticity. B6 forbids any learned component in the render
path or the inverse. B7 keeps the oracle from becoming the renderer.

Three controls, each with a voiding sentence: **C-V1** the skeleton-only
renderer, one-sided by construction — the v0.18 lesson applied on purpose,
not rediscovered; **C-V2** the transliteration null, whose rate on the
**6,414 transliterable** statements is reported beside the renderer's rate
on the residue, so a reader can see the easy territory being declined
rather than take the claim on trust; **C-V3** the determinacy sheet and the
claim it alone can license.

**Seal bookkeeping, unchanged from the rule v0.18 established.** This cycle
touches `answer.py` again. v0.19's first foreign-voice commit **retires the
v0.18 witness for future comparisons, rebuilds the task book as a new
sealed artifact** with the dated reason in the commit, and leaves the v0.18
artifact untouched as the record of what was measured.

**A debt this cycle pays before it borrows.** Two load-bearing lessons from
v0.18 — C-R1's one-sidedness and the prefix-free rule — lived only in
commit bodies and module docstrings. Both land in DISCOVERIES, dated, in
this rotation, before item 1 leans on them.

## 2. The address space, probed (DESIGN-block-vocabulary, ADOPTED bounded)

The maintainer-seeded incumbent is **adopted, not displaced and not
silently parked** — which is how the no-silent-disposal instruction is
discharged. It is scoped to a single question its own census raised:
**is the unified dictionary a real object, or two existing objects wearing
one id space?** Prose compresses via ~100 blocks and 5 templates, already
seed-derivable; terms compress via subterm ids, already skeleton-encoded.
The honest answer may be that *one id space IS the contribution* —
addressability across layers — and this slice tests that claim rather than
assuming it.

**First slice: the address-space probe.** One consumer, the resolver's
block channel, measured against blind baselines **pre-registered before any
measurement** — and taken from the design's own §4 concessions rather than
invented to be beatable:

- for retrieval, **the existing keyword channel at its measured floors**;
- for compression, **zstd-with-shared-dictionary** over the same bytes —
  the ratio headline is already conceded to zstd, and this probe does not
  try to win it back;
- for the term layer, **the canon token encoding at 8.4×**.

**Beat none of them and it parks with the numbers.** Its denominator input
is item 1's B0a/B0b tables, per the design's own sequencing bullet, so it
is ordered after B0 publishes.

## 3. Registered probes (cheap, pre-registered, both branches yield an artifact)

A probe that can only confirm is not a probe. Both of these commit their
result whichever way it lands.

**3a — The transliteration lane.** Two glyph rows, `≥`→`>=` and `≤`→`<=`,
added to the tokenizer on **v0.18's existing native path** — no loanword
pipeline, no oracle. Preview says this reaches **6,414 statements, 50.2% of
the corpus**. It is a probe rather than a headline precisely because the
preview makes it look easy, and easy is what the register exists to keep
honest: the artifact must publish the parse rate *and* the round-trip rate
over the newly-reached set, because parsing is not rendering and v0.18's
own R0/R1 split is the reason we know to separate them.

> **Re-freeze discipline — read before touching the tokenizer.** This lane
> edits `scripts/match_signatures.py`, and that file is **pinned as the
> stage-2 parser by `experiments/realization_prereg.json`** and revalidated
> by **C-R3** in the v0.18 registered run (role `parser`, digest
> `65fead2f…`). Three rules follow, and none of them is optional.
> 1. **v0.18's numbers stay frozen against the digests they were measured
>    under.** Changing the parser does not amend `realization_rate.json`;
>    it retires that pin for future comparisons. Any new rate is a **new
>    registered run** with its own prereg and its own frozen digests.
> 2. **A re-freeze is a preregistration act, not a fix-up.** The new parser
>    digest is recorded before the run that quotes it, exactly as
>    `ccac853` recorded the first five.
> 3. **The gap the seal does not cover, named so nobody discovers it
>    later.** `match_signatures.py` is *not* in the task book's
>    `rendering_module_digests` (that witness lists eleven modules and this
>    is not one of them). But widening the tokenizer changes *which* terms
>    parse, and therefore changes what `answer.render` emits on its
>    `in words` line — **rendered output moves while every witnessed module
>    digest stands still.** The book's witness cannot catch it. So this
>    lane owes an explicit before/after diff of served answer lines over
>    the task book's own corpus tasks, committed with the probe, rather
>    than a green digest test read as reassurance.

**3b — TWO RIGHTS B0, one hour, adopted from course series 3.** Grep the
committed corpora for **co-present statements that differ only by a
convention choice** — the same mathematical content under two defensible
conventions. If pairs exist, the artifact is a `ConventionPair` census
sealed before inspection, and the full direction becomes askable with a
real denominator. If none exist, the artifact is **the registered
negative**: a finding about how these corpora were authored — conventions
fixed by the author and never forked — which is a fact about the graph
nobody has written down. The grep runs **before either branch is
preferred**, and its result is committed either way.

## 4. Carried, with dependants named

| lane | named dependant | disposition |
|---|---|---|
| **Licensed variant generation** | **item 2 of any future cycle that wants a ranker** | carried as the named prerequisite v0.18 discovered by shipping: the realization grammar emits **exactly one** surface per term, so the learned preference seat had no candidate set to order and shipped empty. A ranker is not blocked by the admission bar — it is blocked by the absence of anything to rank. Unpark when a design says what licenses a *second* passing surface for the same term and why that is not decoration |
| Ledger-first claims (v0.17 course lead, gate L1–L13, hardened) | *none this cycle* | **parked, rule intact and unchanged.** It became a headline candidate the first cycle after the throughput readout and has now been passed over twice, both times for a recorded reason rather than by drift. Design, gate and course receipt (`reports/design-direction-v0.17.json`) stay preregistration-ready; the mid-cycle lift trigger — a release quoting a number its artifact no longer supports — stands |
| The cost ledger (answers per joule and per dollar) | *none* | parked, third cycle, still owed. DESIGN-grounded-throughput §10 named it **first** among two successors and the directive took the second; DESIGN-foreign-voice §10 repeats it in its forward list. Unpark still needs a metrology no cycle has designed |
| Open-English **input** | *none — out of scope of item 1* | parked. Item 1 renders a dialect it cannot read; it does not read open English on the input side either. The v0.18 follow-on stands: **can the committed realization lexicon run backwards as the synonym layer** DESIGN-text-resolution §4 names (`gcd` vs "greatest common divisor") — a design, not a patch, and R1 firing is what made it askable |
| Realization parameters as data | *none* | parked; the linearization-rule row of DESIGN-language-as-structure §2's table |
| **STRANGER — outside-asker gap-object intake** | *none* | **parked to BACKLOG** with the degradation rule quoted, per the course receipt's declined dispositions |
| FORK, TWO-STEP, DEADLINE, THE GRADED NO | *none* | parked with the triggers each advisor named, recorded in `reports/design-direction-v0.19.json`. FORK wants the voice layer first so its diffs are readable; THE GRADED NO's licensed-negative answer-type is recorded as the strongest new-vocabulary candidate |
| Unless-receipts, detached receipt, residual ledger, antibody, two referees, wild text, negative space, and the older course parks | *none* | unchanged |
| Resolver coverage lane, A3–A5, verified-ambiguity, range certification, W1–W3 and the long tail | *none* | parked in BACKLOG, unchanged from the v0.15 drift audit |

## 5. Governance

- **The course gate was satisfied strictly, on its first use, and the loop
  is closed.** ROADMAP-v0.18 restored the release skill's strict wording —
  *invoked*, not reaffirmed — after v0.18 was cleared under a looser
  clause with the conflict recorded. This cycle the forge inquiry was
  **run**: three isolated series, nine rounds, session ids, costs and
  prompt hashes in `reports/design-direction-v0.19.json`, a funnel of
  fifteen directions, three finalists (LOANWORD, FORK, TWO RIGHTS), and a
  selection with every declined direction's disposition written down. The
  reaffirmation that cleared v0.18 was available once and was not taken
  again.
- **The third-directed-headline clause is moot for this cycle.** v0.18's
  §4 said a third consecutive maintainer-directed headline would require a
  written amendment to the course gate itself. v0.19's headline is
  **course-selected**, so the clause never came due. It is not repealed —
  it stands for whenever a directed headline next appears — and recording
  that it went unused is the point of having written it down.
- **The incumbent was adopted, not disposed of.** The maintainer's
  no-silent-disposal instruction on DESIGN-block-vocabulary is discharged
  by item 2 rather than by a park paragraph. A course that quietly
  outranks its own incumbent is a course grading itself.
- **Headline selection remains part of the evidence trail**, and
  instrument-first headline selection is once again governed by nothing
  but the ordinary rule: the v0.17 suspension expired with its cycle and
  has not been renewed.

## Release gate

v0.19 is ready only if:

- **B-P is discharged before B0 freezes**, with binder-name independence
  and two-run byte identity asserted by tests;
- **B0 publishes all four parts before any implementation**, both
  branches, and the cycle **stops** on B0's own abort condition if it
  fires — a published abort with its tables is a result, not a failure to
  ship;
- the foreign voice ships its registered run with B1–B7 adjudicated and
  C-V1–C-V3 read out, **or** stops on a named §8 stop condition with the
  reading published;
- **the register ships frozen and digested**, whatever its size — the
  inventory of silence is the headline artifact and does not become
  optional if the rendering rate is good;
- item 2's address-space probe reports against all three pre-registered
  baselines, and **parks with its numbers** if it beats none;
- both registered probes commit their artifacts, whichever branch they
  land on;
- the v0.18 lesson debt is paid — C-R1 one-sided and prefix-free in
  DISCOVERIES, dated — before item 1 borrows either;
- the first foreign-voice commit retires the v0.18 witness and seals a new
  book, with the dated reason in the commit and the v0.18 artifact left
  untouched;
- `check_report_regeneration.py` runs in the release refresh with its
  verdicts in the notes;
- the full suite is green on a frozen tip with retained receipts;
- every unfinished item ships or parks in writing;
- the outside design inquiry is **invoked** for v0.20 — the forge skill
  run, or a written course-gate amendment by the maintainer — with the
  receipt named, and the v0.20 course brief carries the realization
  readout, the foreign-voice readout and the register, whichever way each
  landed.
