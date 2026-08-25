# The voice completed: close the hole in the surface, then re-aim the control

**Status: design only.** Nothing here is implemented. This is v0.20's second
item, and it is **maintainer-directed**: the ruling of **2026-08-24** is that
the foreign voice withheld by v0.19's void **ships in v0.20**. A second
maintainer directive of the same date adds **C-V3′, the machine blind reader**
(§7), which replaces v0.19's ABSENT reader line with a measured number from a
pinned local model. Neither directive lowers a bar; the first chooses which of
two honest repairs the cycle takes, and the second buys an instrument the
cycle did not have.

This design **stands on [DESIGN-foreign-voice](DESIGN-foreign-voice.md) and
cites it rather than restating it.** Rule R, the lexicon rules L1/L2, the
oracle, the register, the authority boundary, B-P and the B0–B7 gate are all
that document's, unchanged and not re-argued here. What is new is two fixes,
one new control, and their ordering. Everything else is a citation.

## 1. The boundary being moved

v0.19 fired every gate and then voided on its own near-miss control.
`C-V4.drop_group` read **0.80 against a 0.90 floor**
(`experiments/foreign_voice_rate.json`, `c_v4.per_class.drop_group`), and a
voided control outranks a cleared floor, so 2,313 perfect round trips are on
disk and none is served. The capability sheet publishes the withholding rather
than hiding it (`scripts/serve_chat.py:412–487`) — right behaviour, and not a
substitute for the surface.

`drop_group` voids for one mechanical reason, stated exactly at
[ROADMAP-v0.20](ROADMAP-v0.20.md):133–134: **deleting a semantically redundant
bracket changes the sentence and not the term.** So a served sentence could
have a variant that reads differently and certifies identically, and a reader
could not tell which one the graph meant.

**The boundary moved is not "the rate goes up".** It is that *a redundant
grouping variant of a served sentence stops being constructible*. The blind
spot is not bounded more tightly — it is **removed from the grammar**, and the
control that measured it is re-aimed at what remains. What a person gains is
the foreign `in words` line for **2,313 statements** under a certification
whose controls can genuinely fail it, plus the register they already have.

Two fixes and one new instrument, in this order, because the second cannot be
justified without the first:

1. **Canonical-grouping rendering** — the renderer emits a grouping word only
   where precedence demands one (§3.1).
2. **C-V4′** — the re-specified control, with C-R2's missing clause restored
   and `drop_group`'s floor raised because redundant brackets no longer exist
   (§3.3), demoted to confirmation by **G1b** (§6).
3. **C-V3′** — the machine blind reader, which measures something no gate in
   this lineage has measured: whether the English determines the term *to a
   reader that is not the elaborator* (§7).

## 2. Grounding: five things the tree said that the plan assumed otherwise

> **Correction 1 (2026-08-24, grounding, before implementation): the renderer
> has no parse tree, so "canonical parenthesization" is a construction
> prerequisite and not an edit.** DESIGN-foreign-voice §3.1 says *"all
> precedence lives in the forward direction"*, which reads as though the
> renderer holds a precedence table. It does not.
> `scripts/foreign_voice.py:245–281` tokenizes `R(s)` into a **flat list** and
> `:301–319` emits one phrase per token, left to right; `(` and `)` are
> ordinary lexicon rows (`data/foreign_voice/lexicon.json`, `structural`)
> emitting `the quantity` / `end quantity`. The module's own docstring is the
> accurate statement: *"Precedence is carried, not rebuilt — `R(s)`'s own
> parentheses become `the quantity` / `end quantity` and none is added"*
> (`:24`), and the lexicon repeats it as a reading rule. **There is no arity,
> no precedence and no tree anywhere in the forward path.** Canonical grouping
> therefore requires a *new object*: a precedence-aware parser over the
> eligible dialect plus a canonical re-emitter. That is G-P, and it is a
> prerequisite with its own discharge, not a diff.

> **Correction 2 (2026-08-24, grounding): a parenthesis in this dialect has
> three kinds, and only one of them is a grouping bracket.** Type ascription —
> `(36 : Rat)` — and **binder groups** — `∃ (x y z : Rat),` — are *syntactic*
> brackets that no precedence rule may remove, and both render through the
> *same two rows* as a grouping bracket. Measured over the covered set:
> **149 statements carry at least one ascription, 215 ascription brackets in
> all**; **16 statements carry a binder-group bracket, 16 brackets** (one of
> them, `lean_workbook_54220`, is in the sealed hundred). After
> canonicalization **42 statements' only remaining bracket pair is an
> ascription.** So the rule must distinguish the three kinds in its *tree*,
> and every mutation pool in §3.3 is defined over **grouping pairs only**.
> This is why the rule ships as an artifact recording the classification per
> statement rather than as a regex over surfaces.

> **Correction 3 (2026-08-24, grounding): the canonicalization strips
> binder-group brackets, and that is a rule someone had to supply.** A single
> parenthesised binder group `∃ (x y z : Rat),` is re-emitted **without** its
> brackets as `∃ x y z : Rat,` — the two forms elaborate identically, and the
> bracketed form is the one the corpus wrote. This is a real change to 16
> surfaces that no precedence argument produces, so it is stated as its own
> clause of the rule (§3.1) rather than left as an emergent property of an
> implementation. The same applies to **tail-position propagation**: a binder
> body extends maximally right, so a binder needs brackets **iff it is not in
> tail position**, which is why `¬ ∃ x : Rat, p` is already canonical and
> needs none. Both rules are written into `grouping.json` because a reader
> reproducing this design must not have to reverse-engineer them from a
> program.

> **Correction 4 (2026-08-24, grounding): amending the lexicon moves every
> seeded sample in the cycle, and for three of the five classes the pool moves
> too.** The B0d id-selection seed is
> `sha256_lf(data/foreign_voice/lexicon.json)`, and the recorded value
> `3a3459d6edf903b9f0181f5617d478ba124209bde434fbc51988168402e81d16`
> **verifies against the committed file byte for byte.** The same seed drives
> C-V4's draws (`foreign_voice_prereg.json`, `c_v4.sample_rule`). The
> canonicalization contradicts the lexicon's committed `reading_rules` prose
> (*"PRECEDENCE IS CARRIED, NOT REBUILT"*), so that file **must** be amended
> and its digest **will** move. Worse than the seed moving: `drop_group` and
> `shift_group` admit on *"the quantity" appears in the surface*
> (`scripts/measure_foreign_voice.py:214–215`), and canonical rendering takes
> that pool from **1,549 to 1,399** — so even an unchanged seed would draw a
> different 50. **Seed-pinning cannot preserve those draws, and G3 therefore
> pins the drawn id lists themselves** (§3.4).

> **Correction 5 (2026-08-24, grounding): `match_signatures.py` is not a
> witnessed module, so the batch's retirement covers three modules, not
> four.** The witnessed set is the eleven at
> `experiments/throughput_tasks.json` (`rendering_module_digests`), quoted
> independently by the suite as `SEAL_WITNESS_MODULES`
> (`tests/test_throughput_tasks.py:52–66`) and tied to the book at `:532`, and
> `match_signatures.py` is not among them. Of ROADMAP-v0.20 §4's targets,
> **`harness.py` (4a) and `evaluate.py` (4c) are witnessed;
> `match_signatures.py` (4b) and `external_verifier.py` (4c's timeouts) are
> not.** DESIGN-foreign-voice §5 already named this gap and what it owes
> instead: a **before/after diff of served answer lines**, not a green digest
> test read as reassurance. §5's arithmetic is stated against the real set.

## 3. The first-class objects

### 3.1 The canonical grouping rule — a committed artifact with a digest

**`data/foreign_voice/grouping.json`** — frozen and digested **before the
renderer is changed**, reviewed the way rule R was reviewed and carrying the
same status: a *trusted, reviewed artifact, not renderer logic*.

```text
grouping_rule {
  rule_id, registered, design,
  levels[]          # token, precedence, associativity (left|right|none)
  prefix[]          # token, argument precedence
  binder_tail_rule  # a binder body extends maximally right: brackets iff NOT
                    #   in tail position  (Correction 3)
  binder_group_rule # a parenthesised binder group is re-emitted unbracketed
                    #   (Correction 3); 16 covered surfaces, 1 sealed
  ascription_rule   # (e : T) is SYNTAX, never a grouping pair, never removed
  emit_rule         # bracket iff the child's level is below the position's
                    #   minimum for that operand side
  pair_kinds        # grouping | ascription | binder_group, per statement
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
(`data/foreign_voice/b0d_sealed_renderings.json`; DESIGN-foreign-voice §6).
Changing the grammar invalidates the prediction for exactly the statements
whose bracketing moves.

**Measured, read-only, before any change: 15 of the 100 change; 85 are
byte-identical under the new rule.** The re-seal is therefore **15
hand-authored sentences**, not 100. B0d's pool is the *eligible* set and does
not depend on the grammar, so its seeded draw is grammar-independent and the
**seed pin alone suffices here** — B0d is the one place in this cycle where it
does (contrast Correction 4). The re-seal is a dated amendment commit
recording the pre-amendment sealed file's digest, the reason, the 15 ids, and
the fact that the other 85 are unchanged. **The v0.19 artifact is left
untouched** as the record of what was measured.

### 3.3 C-V4′ and its mutation-verification records

C-V4′ is ROADMAP-v0.20 §2's specification, adopted without softening:
**construct each mutation, elaborate the mutated *term* first, discard any
mutation whose term did not change, count the discards, and only then score
the survivors.** That is the C-R2 clause C-V4 inherited the idea from and left
behind. It is a **new preregistration with its own frozen digests** and is
**not** a re-score of v0.19's run.

> **A defect in the inherited control, found during grounding and fixed here.**
> The prereg says `drop_group` deletes *"one matched `the quantity` /
> `end quantity` pair"*, but the implementation deletes the **first opening and
> the first closing** independently
> (`scripts/measure_foreign_voice.py:256–262`, two `str.replace(…, 1)` calls).
> Those coincide only when the first bracket contains no nested bracket, and
> **3 of the sampled 50 nest**. C-V4′ deletes a **matched** pair, by index,
> from the parse the rule already computed. Both readings agree on v0.19's
> verdict (40 detected / 10 blind, 0.80), so this does not disturb the record —
> but under G1b, where the claim is that *every* grouping-pair deletion is
> detected, an unmatched deletion is not a grouping-pair deletion at all.

**`experiments/foreign_voice_cv4prime.json` carries one record per mutation:**

```text
mutation_record {
  statement_id, class, sample_index,
  pair_kind,                     # grouping | ascription | binder_group
  surface_before, surface_after,
  term_before_digest, term_after_digest,
  verified_to_change_the_term,   # the C-R2 clause, per mutation
  discarded, discard_reason,
  scored_outcome                 # digest_moved | fverr | did_not_differ
}
per_class { …, margin_to_floor }  # rate minus floor, signed, always published
```

The five classes, with the floors as the prereg **restructured** them — four
voiding classes and one excluded — and one floor raised:

| class | floor | pool | in pool | note |
|---|---|---|---|---|
| `drop_ascription` | 0.90 | 2,285 | yes | unchanged; read **exactly** 0.90 |
| `swap_binder` | 0.90 | 1,764 | yes | unchanged; read 1.00 |
| `shift_group` | 0.90 | 1,399 | yes | pool moves with the grammar |
| `drop_group` | **0.95** | 1,399 | yes | **raised**; demoted to confirmation by G1b |
| `drop_binder` | none | 2,162 | **no** | blind by construction; measured, never scored |

**`drop_group` under canonical rendering is a different mutation:** *deleting
one matched **grouping** pair must change the re-parsed term or fail to parse.*
Ascription and binder-group pairs are excluded by the rule's own
classification. The floor rises to 0.95 because the population of redundant
pairs is empty by construction — a mutation that cannot be a no-op should not
carry a 10% allowance for being one.

**The point prediction, pre-registered, and the direction with it.**
`drop_ascription`'s pool (2,285) does not move with the grammar and its drawn
50 are unchanged, so its outcome is predicted **45 of 50 — exactly v0.19's
reading** — and the prediction is committed before the run. *Measured
correction to the movers named at review:* **zero** of the 16 binder-group
statements fall in `drop_ascription`'s drawn 50 (or in `drop_group`'s), so
binder-group stripping cannot move it; the only candidate movers are the **6
of its 50 whose grouping changes** and oracle nondeterminism. **The direction
is pre-registered too:** a C-R2-clause discard in any of the five classes
means that class clears with **real margin** rather than by luck, and *that is
the finding* — `margin_to_floor` is published per class so the margin is read
rather than inferred.

**`drop_binder` stays a pre-registered measured boundary, quoted:**

> *"the preamble rule regenerates what this mutation deletes, so B1 cannot see
> it. This number IS the measured boundary of what B1 cannot see — the §8
> non-claim made quantitative — and it is excluded from the voiding pool by
> preregistration"* (`foreign_voice_rate.json`,
> `c_v4.per_class.drop_binder.reading`; the field ends without a full stop and
> is quoted here as it reads)

Canonical grouping does nothing to this class and is not claimed to.

### 3.4 The frozen id lists — because the seed can no longer carry them

**`data/foreign_voice/cv4_replay_ids.json`**, dated, committed before the
canonical renderer exists: for each of the five classes, the **50 statement
ids v0.19 actually drew**, plus each class's `admitting` count as the run
recorded it.

> **Correction 6 (2026-08-24, grounding): the ids are not in the run artifact
> and must be re-derived.** A sweep of `experiments/foreign_voice_rate.json`
> finds **no sample-id field anywhere** — `c_v4.per_class` carries counts
> only, and the 2,313 B1 receipts carry no mutation record. What *is*
> committed is the selection program: `_plan`
> (`scripts/measure_foreign_voice.py:282–300`) builds `pool` from the run's
> rows through `_admits` (`:205–216`), shuffles with
> `random.Random(int(seed_hex[:16], 16))`, and takes `sorted(shuffled[:50])`.
> Re-executing it against the committed rows and the **pre-amendment** lexicon
> reproduces every pool exactly — `drop_group` 1,549, `shift_group` 1,549,
> `drop_ascription` 2,285, `swap_binder` 1,764, `drop_binder` 2,162, all five
> matching the artifact — and the re-derived `drop_group` 50 reproduce its
> committed reading exactly (§6). **The derivation is therefore checkable
> rather than asserted**, and the artifact records the program, the inputs and
> the digests it was run against, so a reader can repeat it.

Seed-pinning survives **only for B0d**, whose pool is grammar-independent
(§3.2). Everywhere else the id list is the pin.

## 4. Trusted and untrusted

**Trusted:** everything DESIGN-foreign-voice §4 lists, unchanged — plus
**`data/foreign_voice/grouping.json`**, reviewed and digested, which joins
rule R and the lexicon as an authored artifact whose correctness is carried by
review and not by an independent check. The independent check is still the
pinned binary, which has never seen any of these three files.

**Untrusted and measured:** the canonicalizer's agreement with the pinned
parser (G1); the completeness of the no-redundant-bracket claim (G1b); the 15
re-authored sentences (G2's byte identity); the re-derived id lists (G3's
reproduction check); the C-R2 clause (C-V4′'s discard counts); the claim that
canonicalization closes the hole (C-G1); and **the machine reader itself**,
which is measured and never trusted — C-V3′ grades, and a model never decides
what is served (§7).

**The authority boundary is unchanged and is not weakened by this design.**
`scripts/external_verifier.py:6–7` — *"a passing check certifies what it
checks, not correctness in general"* — and `:35–40`: a verdict alone never
mints a `verified_by` link, and this cycle mints none.

## 5. Smallest slice, the batching arithmetic, and the combined ordering

- **The ROADMAP §3 probe first, already runnable read-only.** §3 requires the
  distribution published *before any bracketing rule is proposed*. §6's
  prototype is that measurement; it lands as
  `experiments/grouping_census.json` in the preregistration commit, and this
  design is admissible only behind it.
- **G-P:** the parser and canonical re-emitter, with `grouping.json` committed
  and digested **before** the renderer changes.
- **The dated lexicon amendment** (Correction 4): `reading_rules` corrected,
  the register re-frozen with the new `lexicon_digest_at_freeze` and a
  **byte-identical entry set** (G4); **`cv4_replay_ids.json` frozen** (§3.4);
  then **the dated re-seal** of the 15 (§3.2).
- **`scripts/foreign_voice.py` renders canonically.** Not a witnessed module —
  this change costs no seal.
- **One fresh registered run, `experiments/foreign_voice_rate2.json`**, its own
  prereg and its own frozen digests: B-P and B0a–B7 re-adjudicated, C-V1,
  C-V2, **C-V4′**, **C-G1**, **C-V3′**, and C-V3 (human) still ABSENT with its
  claim-gating sentence. **Only on ALL-CLEAR does the surface arm.**
- **The wiring — one line, arming itself from the artifact.** The foreign
  `in words   : <surface>` beside v0.18's, per DESIGN-foreign-voice §5's plan,
  emitted only with a passing identity receipt; the ingestion disclaimer
  stays; both skins inherit it through **A-IH6**
  (`docs/DESIGN-interactive-harness.md:811`).

### 5.1 The batch — five named changes, one retirement

| § | change | module | witnessed? |
|---|---|---|---|
| 4a | `_route_ownership` returns its receipt | `harness.py` | **yes** |
| 4b | exact literals | `match_signatures.py` | no (Correction 5) |
| 4c | bound on `^`; four timeouts | `evaluate.py` / `external_verifier.py` | **yes** / no |
| **4d** | **the foreign `in words` line + the sheet row** | **`answer.py`** / `serve_chat.py` | **yes** / no |
| **4e** | `_route_conform` (DESIGN-statements-that-run §5, `:831`) | `harness.py` | **yes** |

**Three witnessed modules, one retirement, one dated reason naming all five
changes, one successor book, prior artifact untouched** — the standing rule at
`docs/SPEC-chat-completions-skin.md:252–258`. The batch's obligation is
unchanged and this design takes no discount from it: **each change carries its
own before/after evidence — a shared seal is not a shared measurement.**

**4d's evidence obligation, stated precisely because it is unusual.** A
served-answer diff showing the foreign line **absent on both sides at batch
time** — because the run has not armed it yet — and **present only after the
clean run lands**. The absent/absent diff is not a null result; it is the
proof that the batch did not change served bytes, which is exactly what a
witnessed-module change owes.

**4d's scope includes a pre-existing defect it must fix.**

> **Correction 7 (2026-08-24, grounding): the sheet row cannot report an
> all-clear run at all — and it does not crash, which is worse.** Three
> findings, all in `foreign_voice_row` (`scripts/serve_chat.py:411–486`):
>
> **(a) It has no code path that sets `served: true`.** `row["served"]` is
> assigned exactly once, to `False`, at `:438`. Flipping the row is not a
> matter of removing a guard; the true branch does not exist and 4d writes it.
>
> **(b) The empty-list read is caught, so the failure is a plausible lie.**
> `voided_class = c_v4["voided_classes"][0]` at `:455` runs on a list that is
> **empty** when nothing voided, and the `except` tuple at `:459` explicitly
> names `IndexError`. So the row returns early with `served: false` and
> *"the foreign-voice surface is withheld; its record could not be read …
> (IndexError: list index out of range)"* — a clean run published with the
> same prose as a corrupt or missing file, on **exactly the branch this design
> exists to produce**.
>
> **(c) The guard keys off the wrong field.** It indexes
> `c_v4["voided_classes"]` while the run's own verdict lives at
> `verdicts["voided"]`. They agree in the shipped artifact
> (`["drop_group"]` and `["C-V4"]`, `overall: "VOID"`) and would both be empty
> on an all-clear run — but only the `c_v4` one is indexed, so the row's
> behaviour is decided by a field that is not the verdict.
>
> **And none of it is tested:** `tests/test_serve_chat.py` mentions neither
> `foreign_voice_row` nor `realization_row`. 4d fixes all three and adds the
> both-branch test G7 requires. This is a defect 4d inherits, not one this
> design introduces.

**The real flipping precedent is `realization_row`**
(`scripts/serve_chat.py:363–408`), which reads the registered run and
publishes `served: false` with a reason when the artifact is missing or
unreadable. 4d follows it. **What is genuinely new: 4d adds `answer.py`'s
first read of an `experiments/` artifact.** `_in_words` gates on its own
round trip, not on a run file, so arming a served line from a registered
artifact is a **new mechanism in that module**, and it is named as such rather
than smuggled in as "the existing pattern".

**The scheduling conflict, and how it resolves without a second retirement.**
ROADMAP-v0.20 §4 lands **before** item 1's first slice; the foreign line ships
**only** if C-V4′ and C-G1 clear, which is after the fresh run. Resolution:
**4d's code lands with the batch and arms itself from the artifact.** An
absent or voided `foreign_voice_rate2.json` emits no line. Code moves once,
the surface moves when the evidence says so, and a void costs no commit.

**Combined ordering, stated once:**

> the §3 probe publishes → `grouping.json` + the lexicon amendment + the id
> lists + the re-seal → the canonical renderer → **§4 (4a–4e) lands as ONE
> retirement** → the fresh registered run adjudicates and arms the surface or
> leaves it dark → **then** DESIGN-statements-that-run's slice.

That last edge is DESIGN-statements-that-run §5's own requirement (`:869–875`):
its route, exact-numeral path and resource bound all ride §4's retirement
rather than opening one. This design adds two passengers and no second
retirement.

## 6. Construction gate

> **The prototype, run read-only against the committed tree (2026-08-24),
> before anything was written.** A precedence-aware parser at the pinned
> toolchain's levels, a canonical re-emitter, and a token-stream comparison —
> **no file was modified.** Over the sealed hundred: **0 parse failures, 15
> changed, 85 byte-identical, 0 gained a bracket**; 27 of 217 pairs redundant.
> Over the covered 2,313: **0 parse failures, 435 changed (18.8%), 1,878
> already canonical**; **620 of 6,063 pairs redundant — 1,240 of 12,126
> emitted grouping words, 10.2%.** Statements admitting `drop_group` fall
> **1,549 → 1,399**. *The 1,549 reproduces the artifact's own `admitting`
> exactly*, as do all four other pools (§3.4).

**Pre-run prerequisites** — discharged before the registered run starts; a
miss stops the cycle and publishes: **G-P, G0, G1, G1b, G2, G3, G4(freeze),
G7**. **Run-carried** — adjudicated inside `foreign_voice_rate2.json`:
**G4(arithmetic), G5, G5b, G6**, and every control in §7.

- **G-P — construction prerequisite.** The parser and re-emitter exist in the
  tree with tests asserting (i) every covered statement round-trips
  `parse → emit → parse` to the same tree and (ii) emission is idempotent,
  `canon(canon(x)) == canon(x)`.

- **G0 — the §3 probe, published before the rule is proposed.**
  `experiments/grouping_census.json` carries the distribution above plus the
  **exposure counts**: **150 of 2,313 statements lose every grouping word**,
  and the per-statement delta distribution beside it. **These are labelled
  exposure, not readability** — they say how much surface changes, and nothing
  about whether the change helps a reader. **No floor**; a probe with a floor
  is an item. Its ordering *is* the gate.

- **G1 — the canonicalizer agrees with the pinned parser.**
  `experiments/grouping_agreement.json`: for every covered statement the
  pinned binary elaborates `R(s)` and `canon(R(s))` to **byte-identical
  serializations**. **Floor: 2,313 of 2,313 — no allowance.** One disagreement
  means `grouping.json` states a precedence the toolchain does not use, and
  one wrong level is wrong everywhere.

- **G1b — no redundant grouping bracket survives, over the whole set.** For
  **every** grouping pair in **every** canonical surface, deleting that pair
  must change the elaborated term or fail to elaborate. **Floor: 5,228 of
  5,228** — the count of surviving canonical grouping pairs, with the 215
  ascription and 16 binder-group pairs excluded by `pair_kind`. *Verified on
  the prototype: 5,228 tested, 5,228 detected, **zero blind**.* This is the
  structural claim stated exhaustively rather than sampled, and it **demotes
  C-V4′'s `drop_group` to a confirmation**: a 50-statement sample cannot
  establish what a 5,228-pair census establishes, and if the two disagree the
  census governs and the disagreement is the finding.

- **G2 — the re-seal reproduces.** `foreign_voice.py` reproduces all 100
  re-sealed renderings **byte-identically**, and the 85 unchanged ones are
  byte-identical to the **v0.19** seal as well. Divergences are reported,
  never repaired. **Floor: 100 of 100.**

- **G3 — the drawn id lists are pinned, and the pin is reproducible.**
  `cv4_replay_ids.json` is committed before the renderer changes, and a test
  re-executes `_plan` against the committed rows and the pre-amendment lexicon
  and asserts the five id lists and five `admitting` counts match. **B0d's
  seed pin stays**, and is recorded as a *consequence rather than a constant*:
  **the lexicon digest at the amendment commit's parent**, git-derivable
  rather than transcribed. The precedent is exact —
  `scripts/transliteration_served_diff.py` takes `--parent` (default
  `HEAD~1`), extracts the pre-amendment file with
  `git show {parent}:scripts/match_signatures.py`, and **refuses to write
  anything** unless that blob's LF sha256 equals the retired pin recorded in
  the prereg, because *"An in-memory revert re-types the old regex, and the
  digest check would then be checking the copy against itself. The blob from
  git IS the pre-amendment file."*
  (`scripts/transliteration_served_diff.py:357–360`, published as
  `why_the_committed_blob_and_not_an_in_memory_revert` at
  `experiments/transliteration_served_diff.json:38–39`). G3 derives the B0d
  seed the same way and refuses the same way. **Amending `tests/test_foreign_voice_b0d.py` to read
  the derived value is named as part of 4d's scope**, so the test moves with
  the seal rather than after it.

  > **A collection gap this gate must not inherit silently.**
  > `tests/git_ordering.py` — the helper every B0d/B4 ordering assertion runs
  > through — **defines `TestCase`s but carries no `test_` filename prefix, so
  > discovery does not collect it**, which `docs/RELEASE-v0.19.0.md:550–552`
  > already flagged for confirmation at a gate. G3's reproduction check is a
  > *collected* test in a `test_`-prefixed module, or it is a green assertion
  > that could not have been red — the exact failure mode that file's own
  > docstring says it exists to replace.

- **G4 — the register did not move.** `data/foreign_voice/register.json`
  re-freezes with the new `lexicon_digest_at_freeze` and a **byte-identical
  entry set**, and **B3's five buckets close at 10,605 with the same five
  numbers** (6,414 + 2,313 + 0 + 1,706 + 172). Canonical grouping changes
  *how* a statement is said, never *whether*.

- **G5 — C-V4′'s discard count for `drop_group` is zero.** Under canonical
  rendering a deleted grouping bracket **cannot** be a no-op, so a nonzero
  discard is not a data point — it is proof the canonicalizer emitted a
  bracket the term did not require, i.e. G-P is wrong.

- **G5b — no mutation pool contains a cross-kind record.** Every
  `mutation_record` in `drop_group` and `shift_group` carries
  `pair_kind == "grouping"`; **floors: zero ascription records, zero
  binder-group records**, read from the field rather than argued. The census
  publishes **1,518 beside 1,549**: **31 of v0.19's `drop_group` pool admitted
  only through an ascription or binder-group bracket** and were padding the
  denominator of a control about grouping. A `pair_kind` histogram is
  published beside `drop_group`'s rate.

- **G6 — B0a, B0b+B0c, B1, B2, B3, B5, B6, B7 re-adjudicated on the fresh
  run**, unchanged floors, from DESIGN-foreign-voice §6. B1's **composition
  sentence travels with every quotation** — *"n of N, of which X% is
  `lean_workbook.ground.v1`"* — with the distinct-term count beside it.

- **G7 — the surface is armed by the artifact, and a test says so.** With a
  voided or absent `foreign_voice_rate2.json`, `answer.render` emits no
  foreign line and the sheet row reads `served: false` with the reason; with a
  clean one, both flip. Asserted on **both** branches, and the clean branch is
  the one Correction 7 shows nobody had ever exercised.

## 7. Controls, each with its voiding sentence

- **C-G1 — the aiming test, and it is the only instrument that can say the
  hole closed.** Re-run the **old** `drop_group` mutation set — the same 50
  ids, from `cv4_replay_ids.json` (§3.4) — under canonical rendering. *If the
  old set does not move from its 0.80 to **≥ 0.95**, the canonicalization did
  not close the hole, this design's premise is false, and §8's stop fires.*

  **And the aggregate is not enough: the ten blind cases are reported by
  statement id, with a floor of 10 of 10.** Those ten are the concrete
  failures that voided v0.19; a design that fixed a rate while leaving one of
  them blind would have fixed the wrong thing. *If any of the ten is still
  blind, C-G1 voids regardless of the aggregate.*

  > **Preview, and it is a preview rather than a result.** Deleting the first
  > **matched** pair over the re-derived 50 gives **31 digest-moved / 9
  > parse-failed / 10 blind**, against the run's committed
  > `of_which_digest_moved: 31`, `of_which_fverr: 9`, `did_not_differ: 10`.
  > Under canonical rendering the same 50 give **39 / 9 / 0** with 2 no longer
  > admitting — **48 of 48 = 1.00**, and the blind set empty. *Two honest
  > qualifications:* the proxy's "same term" is its own canonical form, not the
  > oracle's serialized `Expr`; and the implementation's actual deletion is
  > first-open + first-close (§3.3), which on the 3 nesting statements reads
  > 32/8/10 instead — **the same verdict, a different split**, so the exact
  > triple match is partly fortuitous and is not evidence about which rule the
  > implementation used.

- **C-V4′ — the re-specified near-miss null (§3.3).** *Any class in the voiding
  pool below its floor voids the C-V4′ reading and, through it, the sentence B1
  is allowed to make.* Floors: four at 0.90, `drop_group` at 0.95.

  **The class most likely to void is named now rather than at the gate:**
  `drop_ascription` read **exactly 0.90 against a 0.90 floor** and this design
  does **nothing** for it. Its floor is neither raised nor lowered, its point
  prediction is 45 of 50, and if it voids it voids on a boundary that was
  visible before the run.

- **C-V3′ — the machine blind reader.** *Maintainer directive, 2026-08-24.*
  A **pinned local model** reads each served English sentence **blind — the
  term is never shown** — and reconstructs the formal term, scored against
  ground truth. Because C-V4's lesson is that a lax check flatters itself, the
  reconstruction is scored in the **discriminative** form as well: the reader
  selects among candidates that include **distractors built from the mutation
  classes** — a dropped grouping word, a swapped binder, a reassociated
  operator. A reader that cannot tell a served sentence from its near-miss is
  not reading it.

  > **Correction 8 (2026-08-24, grounding): the shared definition does not
  > **SUPERSEDED (2026-08-24, at the v0.19 tag).** Correction 8 was true when
  > written and is false now: `docs/DESIGN-plain-input.md` **merged to `main`
  > in `b6535e9`**, and its **§6 "The machine blind reader"** is the shared
  > definition this section was forced to supply for itself. The two agree on
  > every load-bearing term — pinned to `weights_blob_sha256`, labelled
  > machine-reader and never human, **grades only, never serves** — and the
  > seed hands the instrument here explicitly: *"it belongs to the voice
  > design's run, not to this one"*, adding that *"no `C-V3′` exists in the
  > tree today … so naming it is itself an act the voice design must ratify."*
  > **This section is that ratification.** Two differences are reconciled in
  > favour of the seed, because both make the control stricter: it inherits
  > **C-V3's voiding sentence unchanged** and keeps **the interleaved skeleton
  > arm**, which this section had replaced with mutation-class distractors —
  > the arm and the distractors are complementary and C-V3′ runs both. Its
  > third point is the seed's own and does not bind this run: a proposer and a
  > blind reader that are the same pinned model are not independent, which is
  > a hazard for *that* design's answers, not for a rendering this design
  > produced without a model. The original correction is kept below because a
  > dated finding that was acted on is not deleted when it expires.
  >
  > **Correction 8 (2026-08-24, grounding): the shared definition does not
  > exist yet, so this design cannot cite it as though it did.** The directive
  > names `docs/DESIGN-plain-input.md`'s machine-blind-reader section as the
  > shared instrument definition, written in parallel on branch
  > `design/v021-plain-input`. A sweep of **every ref in `refs/heads` and
  > `refs/remotes`** finds no such file on any of them — the branch exists and
  > its `docs/` tree matches `main`'s — and a content search for *blind
  > reader*, *machine blind*, *plain input* returns **no file in the tree at
  > all**. So the citation is **forward-looking, not a reference**: C-V3′
  > specifies the instrument here, in full, and the v0.21 design adopts *this*
  > text or supersedes it by dated reconciliation. Naming a path that does not
  > exist as the authority would make this section unreproducible.

  **Pinning, modelled on the v0.17 throughput infrastructure — with the part
  that does not exist named as a build.** `experiments/throughput_baseline.json`
  pins `model.name = Qwen3-4B-Instruct-2507`,
  `model.provider_tag = ollama:qwen3:4b-instruct`,
  `model.weights_blob_sha256 = 85e4a5b7b8ef0e48…`, `runtime.engine = ollama`,
  `runtime.version = 0.32.15`, loopback endpoint only
  (`http://127.0.0.1:11434`). C-V3′ pins the same fields in its own manifest.

  > **Correction 9 (2026-08-24, grounding): the refusal discipline covers the
  > tokenizer, not the model.** The quotable policy — *"gitignored local file,
  > digest-pinned here; token counting REFUSES (exit 2) when the file is absent
  > or its digest mismatches — cannot-verify, never skip (the WordNet-archive
  > rule)"* — is `tokenizer.policy`, enforced at
  > `scripts/measure_throughput.py:355–380` and tested at
  > `tests/test_measure_throughput.py:1040–1070`. **`weights_blob_sha256`
  > appears exactly once in the whole tree and nothing reads it at run time**;
  > the only live model check is a name-and-context probe (`:987–1073`). So
  > **C-V3′ must BUILD the model-side refusal, not inherit it**: absent or
  > digest-mismatched weights → refuse, never download, publish no number, with
  > the sibling test the tokenizer already has. That is a construction
  > prerequisite of this control and is priced as one.

  **What it does NOT inherit: sampling.** The throughput baseline runs at
  `temperature 0.7` with vendor defaults; **C-V3′ pins temperature 0** and
  declares its own sampling block. ollama's `/v1` layer **ignores** `top_k` and
  `repeat_penalty` (verified live 2026-08-22), which is why the throughput
  result records them as `sampling_requested` beside `sampling_source` and
  *"never as settings that took effect"* (`scripts/measure_throughput.py:669–677`).
  C-V3′ uses the same wording. **There is no `seed` field in the manifest or the
  request body anywhere in the tree**, so temperature-0 determinism is an
  assumption this repository has never tested — which is precisely what the
  pilot below must settle before any floor is frozen.

  **Its floor is a construction prerequisite, not a number picked now.** A
  pilot runs before the freeze and establishes (i) that the reader is
  **reproducible** — same input, same model, temperature 0, byte-identical
  output across two runs, which ollama does not guarantee and which this
  repository will not assume — and (ii) what a defensible floor is on the
  discriminative arm. **If reproducibility fails, C-V3′ publishes that failure
  as its result and reverts to ABSENT**, on exactly the reasoning §7 already
  applies to a 15-item arm: an instrument that cannot repeat itself can only
  void, never confirm.

  **It grades only. It never serves, and it never decides.** No model output
  reaches a served answer, gates a rendering, or mints a receipt; B6's
  no-learned-component rule is untouched because nothing learned sits in the
  render path, the inverse, rule R, the grouping rule, or the register.
  Everything it produces is **labelled MACHINE-reader throughout**, in the
  artifact and in every sentence that quotes it.

- **C-V1 — the skeleton-only renderer, one-sided by construction**, imported
  whole from DESIGN-foreign-voice §7 (`:662–665`) and re-run against the
  canonical surfaces. *"The control is informative only if the true renderer's
  identity rate on the same statement set is ≥ 20× the skeleton renderer's; if
  the skeleton renderer clears 1%, the gate is not reading the words and is
  void; if both are near zero, the gate is untested and the reading is void."*
  Canonical grouping **removes grouping words the skeleton renderer keeps**,
  so re-running it is not a formality.

- **C-V2 — the transliteration null**, unchanged. *If the null does not reach
  ≥ 99% identity, the harness — not the renderer — is what the run measured,
  and every other reading in the artifact is void.* The easy 6,414 are
  reported beside the residue and never counted inside it.

- **C-V3 (human) — still ABSENT, and the claim it alone licenses is still not
  made.** No determinacy sheet, no non-maintainer marking, therefore **no
  claim that a *person* can recover the mathematics determinately from the
  English**. C-V3′ does not substitute: a machine reader measures whether the
  sentence determines the term *to that machine*, which is a fact about a
  model, not about a reader. **The human-reader claim stays not-made**, and
  saying so is load-bearing precisely because a measured machine number is the
  most tempting thing in this design to over-read.

## 8. Stop conditions and non-claims

**Stop and publish** if G-P cannot be discharged; if **G1** finds a single
disagreement between `grouping.json` and the pinned parser; if **G1b** leaves
one grouping pair blind; if **G2**'s re-seal does not reproduce; if **G3**'s
id lists cannot be re-derived; if **G4** moves a register entry or a B3
bucket; if **G5**'s discard count is nonzero or **G5b** finds a cross-kind
record; if **C-G1** leaves `drop_group` below 0.95 **or any of the ten named
blind cases still blind**; or if any voiding-pool class of **C-V4′** misses
its floor.

**C-V3′ does not stop the cycle.** It is an instrument this cycle is buying,
not a gate the voice hangs on; if it cannot be made reproducible it publishes
that and reverts to ABSENT, and the voice's fate rests where §2 put it.

**And the plain sentence the maintainer's directive is owed: if the fresh run
voids again, the voice stays withheld and v0.21 inherits it.** A directive to
ship chooses the repair; it does not adjudicate the control. ROADMAP-v0.20 §2
priced that branch — *"a voided C-V4′ publishes a bound on what
digest-identity can certify at all"* — and a second void on a **re-specified**
control would say the blind spot is a property of elaboration-as-identity
rather than of one control's wording. That is the more interesting finding,
and the cycle publishes it as the result rather than as a shortfall.

**Non-claims, stated hard.**

- **No human-readability claim, and canonical grouping may cost readability.**
  The honest half of ROADMAP-v0.20 §3's second reading, with a live example:
  `lean_workbook_20627`, whose sealed surface reads *"the quantity variable
  zero equals twenty and also variable one equals minus sixteen end quantity
  or else …"*, canonicalizes to **four disjuncts with no grouping word
  anywhere**. §3's question *"is the redundancy load-bearing for a reader?"* is
  **not answered here and not closed here.** G0's exposure counts say how much
  moved; only C-V3 could say whether it helped, and it is ABSENT.
- **C-V3′ is a machine number and is never quoted as a reader number.**
- **Identity is still bounded, and C-V4′ is still how far.** One named class of
  erasure leaves the grammar; the relation is not made exact, and
  `drop_binder` at 0.18 is the standing measurement of the rest.
- **This is still a `lean_workbook` rate** — 99.9% of the covered set — with
  the composition sentence mandatory in every quotation.
- **No new reading capability, no truth claim, no `verified_by` links**, and
  no new HTTP surface: one line, one sheet row, both skins via A-IH6.
- **v0.19's numbers are not restated.** `foreign_voice_rate.json` stays
  committed as it read, VOID and all; B1's 1.0 never travels without its
  history; and the fresh run's rate is a **different number over a different
  grammar**.

## 9. The alternative this design declines, and why the directive settles it

**Keep token-faithful rendering; accept the blind spot as a permanent
non-claim.** A real option, and cheap: no grammar change, no regeneration, no
re-seal, no lexicon amendment, no id-list freeze, and the sealed hundred
stand. C-V4′'s C-R2 clause alone might even lift `drop_group` off 0.80. The
cycle would then serve sentences under a bound stated in prose: *a rendering
error confined to a redundant bracket is invisible to B1, and 10.2% of emitted
grouping words are redundant.*

**Why the directive favours canonical, argued rather than asserted.** A
measured bound is adequate for a number in an artifact and inadequate for a
**served** surface. Once the line is wired a reader is handed one sentence with
no way to know a differently-bracketed one would have certified identically —
the bound lives in a file they are not reading. Structural elimination is the
only repair that survives being served: after it the variant is not rare, it is
**ungrammatical**, and G1b says so over 5,228 pairs rather than over a sample.
And the cost was measured before being accepted — 15 sealed renderings, one
dated amendment, one id-list freeze, and a prototype that reproduced the
voiding measurement on the way in.

The declined alternative is **not** parked silently: if C-G1 or C-V4′ voids, it
is the standing fallback, and the cycle that takes it inherits this section as
its argument rather than re-deriving it.

## 10. How status lands

**Preregistration order:** this design; then `experiments/grouping_census.json`
(the §3 probe, ordering-gated); then `data/foreign_voice/grouping.json` with
its digest; then the dated lexicon amendment; then
`data/foreign_voice/cv4_replay_ids.json`; then the dated re-seal of the 15;
then G-P with its tests; then the canonical `foreign_voice.py`; then **§4's
single retirement carrying 4a–4e**; then the one registered run
`experiments/foreign_voice_rate2.json` carrying every gate, C-V1, C-V2, C-V4′
with its discard counts and `margin_to_floor`, **C-G1** with its ten named
cases, **C-V3′** labelled MACHINE-reader, and C-V3's ABSENT sentence.

**The prototype lands with the census, digested, as G-P's test target.**
`scripts/grouping_canonical_probe.py` — the read-only program that produced
every number in §6 — is committed beside `grouping_census.json` with its
LF digest recorded in the prereg. G-P's implementation must agree with it on
all 2,313 statements, so the design's own evidence becomes the new code's
first test rather than a claim nobody can re-run. Its two non-obvious rules,
**binder-group stripping** and **tail-position propagation**, are written into
`grouping.json` (Correction 3) so reproduction needs no reverse-engineering.

**Three landing obligations, owed and named rather than discovered at the
gate.** `main` is frozen for the v0.19 tag, so these land when it unfreezes:

1. **ROADMAP-v0.20 §4 gets a dated correction** — *"one commit's worth of
   witness retirement carrying three fixes"* becomes **five named changes**
   (4a receipt / 4b exact literals / 4c resource bound / 4d this wiring /
   4e `_route_conform`), each with its evidence obligation, and 4d's stated as
   the absent/absent-then-present served diff (§5.1).
2. **ROADMAP-v0.20 §2 and §5 gain this design's status note** — the
   maintainer's ship-directive of 2026-08-24 and C-V3′, recorded the way
   ROADMAP-v0.19 recorded DESIGN-foreign-voice's provisional sections.
3. **Inbound links** — ROADMAP-v0.20 §2/§3/§5 and
   `docs/DESIGN-foreign-voice.md` §10 currently point at no successor
   document; each gains a link to this one, because a design nothing links to
   is a design the next cycle rediscovers.

Fires, misses and voids land together in ROADMAP-v0.21, ANALYSIS, DISCOVERIES
and BACKLOG; the v0.20 blog's foreign-voice section follows from this document
and from [the void that measured what the gate could not
see](blog/the-void-that-measured-what-the-gate-could-not-see.md), whose closing
promise — *"Next release, either the sentences pass a control that can
genuinely fail them — or we learn the blind spot was never the control's
fault."* — is the sentence this design is written to keep either way.

**If the run clears, the question that becomes askable next** is the one
DESIGN-foreign-voice §10 named and this cycle finally has both halves of:
**cross-layer same-statement discovery** — the same statement recognised across
two grammars that never shared a parser, with 67.2% native and 2,313 foreign
statements both speaking.

## 11. Habits this design suspends

Three practices this repository has earned the right to rely on do **not**
hold this cycle, and saying so is cheaper than having a later reader assume
they did. *(This enumeration is the writer's.)*

- **"The seed is the pin."** Every prior cycle identified a sample by its
  seed, and that worked because pools were grammar-independent. Three of the
  five C-V4 pools move with this grammar (Correction 4), so **the id list is
  the pin** and the seed survives only for B0d. A later cycle that reaches for
  a seed to reproduce a sample must first ask whether its pool is stable.
- **"A cleared floor is a result."** B1 read 1.0 and certified nothing,
  because a voided control outranks it. This cycle adds a second layer: G1b's
  census outranks C-V4′'s sample on the same question, so **a cleared sample
  floor is not a result when a census disagrees with it** — and the design
  says in advance which one governs.
- **"A green witnessed-digest test means served output did not move."** False
  here in two directions: `match_signatures.py` moves served bytes while every
  witnessed digest stands still (Correction 5), and 4d moves a witnessed
  module while served bytes **do not** change until an artifact arms them
  (§5.1). Both directions owe a served diff, and neither is discharged by the
  seal.
