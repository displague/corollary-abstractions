# The voice completed: close the hole in the surface, then re-aim the control

**Status: design only.** Nothing here is implemented. This is v0.20's second
item, and it is **maintainer-directed**: the ruling of **2026-08-24** is that
the foreign voice withheld by v0.19's void **ships in v0.20**. That directive
does not lower a bar; it chooses which of two honest repairs the cycle takes,
and this document says which, why, and what it costs.

This design **stands on [DESIGN-foreign-voice](DESIGN-foreign-voice.md) and
cites it rather than restating it.** Rule R, the lexicon rules L1/L2, the
oracle, the register, the authority boundary, B-P and the B0–B7 gate are all
that document's, unchanged and not re-argued here. What is new is two fixes
and their ordering. Everything else is a citation.

## 1. The boundary being moved

v0.19 fired every gate and then voided on its own near-miss control.
`C-V4.drop_group` read **0.80 against a 0.90 floor**
(`experiments/foreign_voice_rate.json`, `c_v4.per_class.drop_group`), and a
voided control outranks a cleared floor, so 2,313 perfect round trips are on
disk and none is served. The capability sheet publishes the withholding rather
than hiding it (`scripts/serve_chat.py:412–487`) — right behaviour, and not a
substitute for the surface.

`drop_group` voids for one mechanical reason, stated exactly at
[ROADMAP-v0.20](ROADMAP-v0.20.md):105–106: **deleting a semantically redundant
bracket changes the sentence and not the term.** So a served sentence could
have a variant that reads differently and certifies identically, and a reader
could not tell which one the graph meant.

**The boundary moved is not "the rate goes up".** It is that *a redundant
grouping variant of a served sentence stops being constructible*. The blind
spot is not bounded more tightly — it is **removed from the grammar**, and the
control that measured it is re-aimed at what remains. What a person gains is
the foreign `in words` line for **2,313 statements** under a certification
whose controls can genuinely fail it, plus the register they already have.

Two fixes, in this order, because the second cannot be justified without the
first:

1. **Canonical-grouping rendering** — the renderer emits a grouping word only
   where precedence demands one (§3.1).
2. **C-V4′** — the re-specified control, with C-R2's missing clause restored
   and `drop_group`'s floor raised because redundant brackets no longer exist
   (§3.3).

## 2. Grounding: four things the tree said that the plan assumed otherwise

> **Correction 1 (2026-08-24, grounding, before implementation): the renderer
> has no parse tree, so "canonical parenthesization" is a construction
> prerequisite and not an edit.** DESIGN-foreign-voice §3.1 says *"all
> precedence lives in the forward direction"*, which reads as though the
> renderer holds a precedence table. It does not.
> `scripts/foreign_voice.py:245–281` tokenizes `R(s)` into a **flat list** and
> `:301–320` emits one phrase per token, left to right; `(` and `)` are
> ordinary lexicon rows (`data/foreign_voice/lexicon.json`, `structural`)
> emitting `the quantity` / `end quantity`. The module's own docstring is the
> accurate statement: *"Precedence is carried, not rebuilt — `R(s)`'s own
> parentheses become `the quantity` / `end quantity` and none is added"*
> (`:22–30`), and the lexicon repeats it as a reading rule. **There is no
> arity, no precedence and no tree anywhere in the forward path.** Canonical
> grouping therefore requires a *new object*: a precedence-aware parser over
> the eligible dialect plus a canonical re-emitter. That is G-P below, and it
> is a prerequisite with its own discharge, not a diff.

> **Correction 2 (2026-08-24, grounding): not every `the quantity` is a
> grouping word.** Type ascription — `(36 : Rat)` — is a **syntactic**
> bracket that no precedence rule can remove, and it renders through the
> *same two rows* as a grouping bracket, with `:` → `of type` between them.
> Measured over the covered set: **149 of 2,313 statements carry at least one
> ascription, 215 ascription brackets in all**, and after canonicalization
> **42 statements' only remaining bracket pair is an ascription.** So the
> canonicalization rule must distinguish grouping from ascription in its
> *tree*, and the mutation pool in §3.3 is defined over grouping pairs only.
> This is not a caveat; it is why the rule ships as an artifact that records
> the classification per statement rather than as a regex over surfaces.

> **Correction 3 (2026-08-24, grounding): amending the lexicon moves every
> seeded sample in the cycle, including the one the aiming test needs.** The
> B0d id-selection seed is `sha256_lf(data/foreign_voice/lexicon.json)`, and
> the value recorded in `b0d_sealed_renderings.json` —
> `3a3459d6edf903b9f0181f5617d478ba124209bde434fbc51988168402e81d16` —
> **verifies against the committed file byte for byte.** The same seed drives
> C-V4's per-class draws (`foreign_voice_prereg.json`, `c_v4.sample_rule`).
> The canonicalization rule contradicts the lexicon's committed
> `reading_rules` prose (*"PRECEDENCE IS CARRIED, NOT REBUILT"*), so that file
> **must** be amended, so its digest **will** move, so the draw would move
> with it — and a moved draw makes §7's aiming test impossible to run,
> because the aiming test is defined as *the old mutation set re-scored*.
> **The amendment therefore pins both seeds to the recorded pre-amendment
> value in writing (G3), and that pin is load-bearing rather than tidy.**

> **Correction 4 (2026-08-24, grounding): `match_signatures.py` is not a
> witnessed module, so the batch's retirement covers three modules, not
> four.** The witnessed set is the eleven at
> `experiments/throughput_tasks.json` (`rendering_module_digests`), quoted
> independently by the suite as `SEAL_WITNESS_MODULES`
> (`tests/test_throughput_tasks.py:52–66`) and tied to the book at `:532`,
> and `match_signatures.py` is not among them. Of ROADMAP-v0.20 §4's targets, **`harness.py` (4a) and
> `evaluate.py` (4c) are witnessed; `match_signatures.py` (4b) and
> `external_verifier.py` (4c's timeouts) are not.** DESIGN-foreign-voice §5
> already named this gap and what it owes instead: a **before/after diff of
> served answer lines**, not a green digest test read as reassurance. §5's
> arithmetic below is stated against the real set.

## 3. The first-class objects

### 3.1 The canonical grouping rule — a committed artifact with a digest

**`data/foreign_voice/grouping.json`** — the rule, frozen and digested
**before the renderer is changed**, reviewed the way rule R was reviewed and
carrying the same status: a *trusted, reviewed artifact, not renderer logic*.
It holds one thing — the precedence and associativity of every constructor
the eligible residue carries, at the values the **pinned toolchain's own
parser** uses — plus the two structural exceptions:

```text
grouping_rule {
  rule_id, registered, design,
  levels[]        # token, precedence, associativity (left|right|none)
  prefix[]        # token, argument precedence
  binder_rule     # a binder body extends maximally right; bracket iff not in tail position
  ascription      # (e : T) is SYNTAX, never a grouping pair, never removed
  emit_rule       # bracket iff the child's level is below the position's minimum
  digest_of_source_of_truth
}
```

**Why it is an artifact and not code.** The rule is a claim about a parser
this repository did not write. If it is wrong, the inverse hands the pinned
binary a term that re-associates and B1 fails loudly, everywhere — the good
failure mode. A digested file makes widening it a diff with a review, as rule
R's §3.2 discipline requires, and it is what Correction 2's per-statement
classification is recorded against.

**The emitted grammar changes, and therefore every surface is regenerated** —
the honest headline of the cost. Every covered surface is re-derived from
`R(s)`, the sealed hundred move, and B0d's byte-identity test moves with them
(§3.2).

**What the rule does *not* do:** it never adds a bracket the source omitted. A
source statement parses, so the structure it denotes already follows
precedence, and the canonical form of a parsing source can only **remove**.
Checked rather than assumed — §6's prototype histogram has **no negative
bucket** across 2,313 statements.

### 3.2 The re-sealed hundred — a dated re-seal, with the reason and the cost

B0d's hundred hand-renderings are a **sealed prediction** that
`foreign_voice.py` must reproduce byte-identically
(`data/foreign_voice/b0d_sealed_renderings.json`;
DESIGN-foreign-voice §6, B0d's three-line separation). Changing the grammar
invalidates the prediction for exactly the statements whose bracketing moves.

**Measured, read-only, before any change (§6's prototype): 15 of the 100
change; 85 are byte-identical under the new rule.** The re-seal is therefore
**15 hand-authored sentences**, not 100 — and it is 15 rather than 100 *only*
because Correction 3's seed pin holds the draw still. The re-seal is a dated
amendment commit that records: the pre-amendment sealed file's digest, the
reason (grammar change, this design, named), the 15 ids, and the fact that
the other 85 are unchanged. **The v0.19 artifact is left untouched** as the
record of what was measured — the standing rule, not a new one.

### 3.3 C-V4′ and its mutation-verification records

C-V4′ is ROADMAP-v0.20 §2's specification, adopted here without softening:
**construct each mutation, elaborate the mutated *term* first, discard any
mutation whose term did not change, count the discards, and only then score
the survivors.** That is the C-R2 clause C-V4 inherited the idea from and
left behind (v0.18 discarded 31 that way). It is a **new preregistration with
its own frozen digests** and is **not** a re-score of v0.19's run.

**`experiments/foreign_voice_cv4prime.json` carries one record per mutation**,
and the record is a first-class object rather than a tally:

```text
mutation_record {
  statement_id, class, sample_index,
  pair_kind,                # grouping | ascription  (Correction 2)
  surface_before, surface_after,
  term_before_digest, term_after_digest,
  verified_to_change_the_term,   # the C-R2 clause, per mutation
  discarded, discard_reason,
  scored_outcome            # digest_moved | fverr | did_not_differ
}
```

The five classes are v0.19's, with the floors as the prereg **restructured**
them — four voiding classes and one excluded — and one floor raised:

| class | floor | in voiding pool | note |
|---|---|---|---|
| `drop_ascription` | 0.90 | yes | unchanged; read v0.19 at **exactly** 0.90 |
| `swap_binder` | 0.90 | yes | unchanged; read 1.00 |
| `shift_group` | 0.90 | yes | unchanged; read 1.00 |
| `drop_group` | **0.95** | yes | **raised**, and §6 says why it is justifiable |
| `drop_binder` | none | **no** | blind by construction; measured, never scored |

**`drop_group` under canonical rendering is a different mutation, stated
precisely:** *deleting one matched **grouping** pair must change the re-parsed
term or fail to parse.* Ascription pairs are excluded from the pool by the
rule's own classification, which is why Correction 2 is in this document and
not in a footnote. The floor rises to 0.95 because the population of
redundant pairs is empty by construction — a mutation that cannot be a no-op
should not be given a 10% allowance for being one.

**`drop_binder` stays a pre-registered measured boundary, quoted from the
run rather than paraphrased:**

> *"the preamble rule regenerates what this mutation deletes, so B1 cannot
> see it. This number IS the measured boundary of what B1 cannot see — the §8
> non-claim made quantitative — and it is excluded from the voiding pool by
> preregistration"* (`foreign_voice_rate.json`,
> `c_v4.per_class.drop_binder.reading`; the field ends without a full stop and
> is quoted here as it reads)

Canonical grouping does nothing to this class and is not claimed to. It reads
0.18 and is expected to read near 0.18 again; a large move is a reportable
finding, not a repair.

## 4. Trusted and untrusted

**Trusted:** everything DESIGN-foreign-voice §4 lists, unchanged — plus
**`data/foreign_voice/grouping.json`**, reviewed and digested, which joins
rule R and the lexicon as an authored artifact whose correctness is carried
by review and not by an independent check. The independent check is still the
pinned binary, which has never seen any of these three files.

**Untrusted and measured:** the canonicalizer's agreement with the pinned
parser (G1, and B1 wholesale — a wrong precedence level fails everywhere at
once); the re-seal's 15 re-authored sentences (G2's byte identity); the
mutation set's verified-to-change-the-term clause (C-V4′'s own discard
count); and the claim that canonicalization closes the hole (§7's C-G1, which
is the only instrument that can say so).

**The authority boundary is unchanged and is not weakened by this design.**
`scripts/external_verifier.py:6–7` — *"a passing check certifies what it
checks, not correctness in general"* — and `:35–40`: a verdict alone never
mints a `verified_by` link, and this cycle mints none.

## 5. Smallest slice, the batching arithmetic, and the combined ordering

- **The ROADMAP §3 probe first, already runnable read-only.** §3 requires the
  distribution published *before any bracketing rule is proposed*. §6's
  prototype is that measurement, run against the committed tree without
  changing a byte; it lands as `experiments/grouping_census.json` in the
  preregistration commit, and this design is admissible only behind it.
- **G-P:** the precedence-aware parser and canonical re-emitter, with
  `grouping.json` committed and digested **before** the renderer changes.
- **The dated lexicon amendment** (Correction 3): `reading_rules` corrected,
  **both seeds pinned to the pre-amendment value in writing**, the register
  re-frozen with the new `lexicon_digest_at_freeze` and a **byte-identical
  entry set** (G4). Then **the dated re-seal** of the 15 (§3.2).
- **`scripts/foreign_voice.py` renders canonically.** Not a witnessed module —
  this change costs no seal.
- **One fresh registered run, `experiments/foreign_voice_rate2.json`**, its own
  prereg and its own frozen digests: B-P and B0a–B7 re-adjudicated, C-V1,
  C-V2, **C-V4′**, §7's C-G1 aiming test, and **C-V3 still ABSENT with its
  claim-gating sentence**. **Only on ALL-CLEAR does the surface turn on.**
- **The wiring — one line, gating itself on the artifact.** The foreign
  `in words   : <surface>` beside v0.18's, per DESIGN-foreign-voice §5's
  original plan, emitted only with a passing identity receipt; the ingestion
  disclaimer stays; both skins inherit it through **A-IH6**
  (`docs/DESIGN-interactive-harness.md:811`); `foreign_voice_row` flips
  `served: false` → `true` with the new run as its source, reading the verdict
  from the artifact exactly as it reads the void today.

### The batch, and the arithmetic checked against §4's routing table

| § | fix | module | witnessed? |
|---|---|---|---|
| 4a | `_route_ownership` returns its receipt | `harness.py` | **yes** |
| 4b | exact literals | `match_signatures.py` | **no** (Correction 4) |
| 4c | bound on `^`; four timeouts | `evaluate.py` / `external_verifier.py` | **yes** / no |
| **4d** | **the foreign `in words` line** | **`answer.py`** | **yes** |

**Three witnessed modules, one retirement, one dated reason naming all four
fixes, one successor book, prior artifact untouched** — the standing rule at
`docs/SPEC-chat-completions-skin.md:252–258`, and the batching rule
ROADMAP-v0.20 §4 wrote down so a later cycle inherits it. The batch's own
obligation is unchanged and this design does not get a discount from it:
**each fix carries its own before/after evidence — a shared seal is not a
shared measurement.** 4b additionally owes the served-answer-line diff that
Correction 4's unwitnessed status makes necessary; the precedent tool exists
(`scripts/transliteration_served_diff.py`).

**The scheduling conflict, and how it resolves without a second
retirement.** ROADMAP-v0.20 §4 lands **before** item 1's first slice; the
foreign line ships **only** if C-V4′ clears, which is after the fresh run.
Those two facts look incompatible, and the resolution is the one already in
the tree: **4d's code lands with the batch and turns itself on from the
artifact.** An absent or voided `foreign_voice_rate2.json` emits no line —
the same gating `_in_words` already applies to itself
(`scripts/answer.py:210–215`) and `foreign_voice_row` already applies to the
sheet. So the code moves once, the surface moves when the evidence says so,
and a void costs no commit.

**Combined ordering, stated once:**

> the §3 probe publishes → `grouping.json` + the lexicon amendment + the
> re-seal → the canonical renderer → **§4 (4a–4d) lands as ONE retirement** →
> the fresh registered run adjudicates and flips the surface on or leaves it
> off → **then** DESIGN-statements-that-run's slice.

That last edge is the design's own requirement and matches
DESIGN-statements-that-run §5's: its route, its exact-numeral path and its
resource bound all ride §4's retirement rather than opening one, so §4 must
land first. This design adds a fourth passenger and no fourth retirement.

## 6. Construction gate

> **The prototype, run read-only against the committed tree (2026-08-24),
> before anything was written.** A precedence-aware parser at the pinned
> toolchain's levels, a canonical re-emitter, and a token-stream comparison —
> **no file was modified.** Over the sealed hundred: **0 parse failures, 15
> changed, 85 byte-identical, 0 statements gained a bracket**; 27 of 217
> bracket pairs are redundant. Over the covered 2,313: **0 parse failures,
> 435 changed (18.8%), 1,878 already canonical**; **620 of 6,063 bracket
> pairs are redundant — 1,240 redundant grouping words of 12,126 emitted,
> 10.2%.** Statements admitting a `drop_group` mutation fall **1,549 → 1,399**
> (and 1,357 once Correction 2's 42 ascription-only statements leave the
> pool). *The 1,549 reproduces `c_v4.per_class.drop_group.admitting`
> exactly*, which is the first sign the prototype and the run are counting
> the same thing.

- **G-P — construction prerequisite, discharged before G0 freezes.** The
  parser and re-emitter exist in the tree with tests asserting (i) every
  covered statement round-trips `parse → emit → parse` to the same tree and
  (ii) emission is idempotent — `canon(canon(x)) == canon(x)`. If G-P cannot
  be discharged, §8's first stop condition has fired.

- **G0 — the §3 probe, published before the rule is proposed.**
  `experiments/grouping_census.json` carries the distribution above, whichever
  way it reads. **No floor** — a probe with a floor is an item. Its ordering
  is the gate: proposing the rule before publishing the count is the failure.

- **G1 — the canonicalizer agrees with the pinned parser.** For every covered
  statement, the pinned binary elaborates `R(s)` and `canon(R(s))` to
  **byte-identical serializations**. **Floor: 2,313 of 2,313 — no allowance.**
  This is not a rate; a single disagreement means `grouping.json` states a
  precedence the toolchain does not use, and one wrong level is wrong
  everywhere. *Construction prerequisite for every number below.*

- **G2 — the re-seal reproduces.** `foreign_voice.py` reproduces all 100
  re-sealed renderings **byte-identically**, and the 85 unchanged ones are
  byte-identical to the **v0.19** seal as well. Divergences are reported,
  never repaired (B0d's standing clause). **Floor: 100 of 100.**

- **G3 — the seed pin is recorded, and the draw is provably unmoved.** The
  amendment commit records the pre-amendment lexicon digest and pins both
  seeds to it; a test asserts the B0d id list and each C-V4′ class draw are
  **identical to v0.19's**. Without this, §7's C-G1 cannot run at all.

- **G4 — the register did not move.** `foreign_voice_register.json` re-freezes
  with the new `lexicon_digest_at_freeze` and a **byte-identical entry set**,
  and **B3's five buckets close at 10,605 with the same five numbers**
  (6,414 + 2,313 + 0 + 1,706 + 172). Canonical grouping changes *how* a
  statement is said, never *whether*. A moved bucket means the change altered
  what is sayable, which is a different design and needs its own review.

- **G5 — C-V4′'s discard count for `drop_group` is zero.** Every constructed
  `drop_group` mutation is verified to change the term. Under canonical
  rendering a deleted grouping bracket **cannot** be a no-op, so a nonzero
  discard count is not a data point — it is proof the canonicalizer emitted a
  bracket the term did not require, i.e. G-P is wrong. *Construction check,
  frozen at zero, and it is the tightest self-check in this design.*

- **G6 — B0a, B0b+B0c, B1, B2, B3, B5, B6, B7 re-adjudicated on the fresh
  run**, unchanged floors, from DESIGN-foreign-voice §6. B1's **composition
  sentence travels with every quotation** — *"n of N, of which X% is
  `lean_workbook.ground.v1`"* — with the distinct-term count beside it.

- **G7 — the surface is turned on by the artifact, and a test says so.** With
  a voided or absent `foreign_voice_rate2.json`, `answer.render` emits no
  foreign line and the sheet row reads `served: false` with the reason.
  Asserted on **both** branches: a ship-gate exercised only on the shipping
  branch is not a gate.

## 7. Controls, each with its voiding sentence

- **C-G1 — the aiming test, and it is the only instrument that can say the
  hole closed.** Re-run the **old** C-V4 `drop_group` mutation set — the same
  50 statements, drawn by the same pinned seed (G3) — under canonical
  rendering, and read `drop_group`'s no-longer-blind reading. *If the old set
  does not move from its 0.80 to **≥ 0.95**, the canonicalization did not
  close the hole, this design's premise is false, and §8's stop fires — the
  surface stays withheld and no floor elsewhere rescues it.*

  > **Preview, and it is a preview rather than a result.** The prototype
  > reproduced the committed reading exactly: deleting the **first** matched
  > pair over the seeded 50 gives **31 digest-moved / 9 parse-failed / 10
  > blind**, against the run's committed `of_which_digest_moved: 31`,
  > `of_which_fverr: 9`, `did_not_differ: 10`. Three counts, three matches,
  > from a read-only re-implementation that never called the oracle. Under
  > canonical rendering the same 50 give **39 / 9 / 0** with 2 statements no
  > longer admitting the mutation — **48 of 48 = 1.00**. *This is a term-level
  > proxy, not the oracle's verdict:* the prototype's "same term" is its own
  > canonical form, and its "parse failure" is its own parser's. The
  > registered run re-measures through the pinned binary, and a divergence
  > from 31/9/10 is a reportable finding rather than a discrepancy to
  > reconcile.

- **C-V4′ — the re-specified near-miss null (§3.3).** *Any class in the
  voiding pool below its floor voids the C-V4′ reading and, through it, the
  sentence B1 is allowed to make.* Unchanged in force from v0.19; the floors
  are the prereg's four, with `drop_group` at 0.95.

  **The class most likely to void next is named now rather than at the
  gate:** `drop_ascription` read **exactly 0.90 against a 0.90 floor** last
  cycle — a single mutation from voiding — and this design does **nothing**
  for it. Its floor is not raised and not lowered. If it voids, it voids on a
  boundary that was visible before the run, and the cycle publishes that.

- **C-V1 — the skeleton-only renderer, one-sided by construction**, imported
  whole from DESIGN-foreign-voice §7 (`:662–665`) and re-run against the
  canonical surfaces. *"The control is informative only if the true renderer's
  identity rate on the same statement set is ≥ 20× the skeleton renderer's; if
  the skeleton renderer clears 1%, the gate is not reading the words and is
  void; if both are near zero, the gate is untested and the reading is
  void."* Canonical grouping **removes grouping words the skeleton
  renderer keeps**, so its scaffolding is thinner than it was — re-running it
  is not a formality.

- **C-V2 — the transliteration null**, unchanged. *If the null does not reach
  ≥ 99% identity, the harness — not the renderer — is what the run measured,
  and every other reading in the artifact is void.* Its second job stands:
  the easy 6,414 are reported beside the residue and never counted inside it.

- **C-V3 — ABSENT, and the claim it alone could license is still not made.**
  No determinacy sheet, no non-maintainer marking, therefore **no claim that
  a reader can recover the mathematics determinately from the English**. This
  is repeated here because §8 says canonicalization may make the sentences
  *harder* to read, and a design that changes the surface for a reader's sake
  while declining to measure readability would be claiming by implication.
  The unpark trigger recorded in v0.19's run is unchanged.

## 8. Stop conditions and non-claims

**Stop and publish** if G-P cannot be discharged; if **G1** finds a single
disagreement between `grouping.json` and the pinned parser; if **G2**'s
re-seal does not reproduce; if **G3**'s pin cannot be recorded, since C-G1
becomes unrunnable and the design's premise becomes unfalsifiable; if **G4**
moves a register entry or a B3 bucket; if **G5**'s discard count is nonzero;
if **C-G1** leaves `drop_group` below 0.95; or if any voiding-pool class of
**C-V4′** misses its floor.

**And the plain sentence the maintainer's directive is owed, said without
hedging: if the fresh run voids again, the voice stays withheld and v0.21
inherits it.** A directive to ship chooses the repair; it does not adjudicate
the control. ROADMAP-v0.20 §2 already priced that branch and it is priced the
same here — *"a voided C-V4′ publishes a bound on what digest-identity can
certify at all"*, and a second void on a **re-specified** control would say
the blind spot is a property of elaboration-as-identity rather than of one
control's wording. That is the more interesting finding, and the cycle
publishes it as the result rather than as a shortfall.

**Non-claims, stated hard.**

- **No readability claim, and canonical grouping may cost readability.** The
  honest half of ROADMAP-v0.20 §3's second reading, with a live example the
  prototype found: `lean_workbook_20627`, whose sealed surface reads *"the
  quantity variable zero equals twenty and also variable one equals minus
  sixteen end quantity or else …"*, canonicalizes to **four disjuncts with no
  grouping word anywhere**, because `∧` binds tighter than `∨`. §3's question
  *"is the redundancy load-bearing for a reader?"* is **not answered here and
  not closed here.** C-V3 alone could answer it and it is ABSENT. The claim is
  narrower and structural: a redundant-grouping *variant* cannot exist.
- **Identity is still bounded, and C-V4′ is still how far.** Identity holds
  *up to what elaboration erases and what the preamble rule regenerates*. One
  named class of erasure leaves the grammar; the relation is not made exact,
  and `drop_binder` at 0.18 is the standing measurement of the rest.
- **This is still a `lean_workbook` rate** — 99.9% of the covered set — with
  the composition sentence mandatory in every quotation.
- **No new reading capability, no truth claim, no `verified_by` links**, and
  no new HTTP surface: one line, one sheet row, both skins via A-IH6.
- **v0.19's numbers are not restated.** `foreign_voice_rate.json` stays
  committed as it read, VOID and all; B1's 1.0 never travels without its
  history; and the fresh run's rate is a **different number over a different
  grammar**. Quoting one as the other is the exact drift §5's ordering rules
  exist to catch.

## 9. The alternative this design declines, and why the directive settles it

**Keep token-faithful rendering; accept the blind spot as a permanent
non-claim.** A real option, and cheap: no grammar change, no regeneration, no
re-seal, no lexicon amendment, no seed cascade, and the sealed hundred stand.
C-V4′'s C-R2 clause alone might even lift `drop_group` off 0.80, since some of
its 10 blind cases could be discards rather than misses. The cycle would then
serve sentences under a bound stated in prose: *a rendering error confined to
a redundant bracket is invisible to B1, and 10.2% of emitted grouping words
are redundant.*

**Why the directive favours canonical, argued rather than asserted.** A
measured bound is adequate for a number in an artifact and inadequate for a
**served** surface. Once the line is wired a reader is handed one sentence
with no way to know a differently-bracketed one would have certified
identically — the bound lives in a file they are not reading. Structural
elimination is the only repair that survives being served: after it the
variant is not rare, it is **ungrammatical**. And the cost was measured before
being accepted — 15 sealed renderings, one dated amendment, one dated re-seal,
and a prototype that reproduced the voiding measurement 31/9/10 on the way in.
The directive chose a repair; the measurement is why this document agrees.

The declined alternative is **not** parked silently: if C-G1 or C-V4′ voids,
it is the standing fallback, and the cycle that takes it inherits this
section as its argument rather than re-deriving it.

## 10. How status lands

**Preregistration order:** this design; then `experiments/grouping_census.json`
(the §3 probe, ordering-gated); then `data/foreign_voice/grouping.json` with
its digest; then the dated lexicon amendment with **both seeds pinned**; then
the dated re-seal of the 15; then G-P with its tests; then the canonical
`foreign_voice.py`; then **§4's single retirement carrying 4a–4d**; then the
one registered run `experiments/foreign_voice_rate2.json` carrying every gate,
C-V1, C-V2, C-V4′ with its discard counts, **C-G1**, and C-V3's ABSENT
sentence. Fires, misses and voids land together in ROADMAP-v0.21, ANALYSIS,
DISCOVERIES and BACKLOG; the v0.20 blog's foreign-voice section follows from
this document and from
[the void that measured what the gate could not see](blog/the-void-that-measured-what-the-gate-could-not-see.md),
whose closing promise — *"Next release, either the sentences pass a control
that can genuinely fail them — or we learn the blind spot was never the
control's fault."* — is the sentence this design is written to keep either
way.

**If the run clears, the question that becomes askable next** is the one
DESIGN-foreign-voice §10 already named and this cycle finally has both halves
of: **cross-layer same-statement discovery** — the same mathematical statement
recognised across two grammars that never shared a parser, with 67.2% native
and 2,313 foreign statements both speaking.
