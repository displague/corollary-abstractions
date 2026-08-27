# Echo — the voice read back

**Status: design only.** Nothing here is implemented. This is v0.23's
**item 2**, the lead of the course's first series (receipt:
`reports/design-direction-v0.23.json`). It is scheduled ahead of item 1
because its result licenses item 1's clarify-vs-conditional decision
rule (`docs/DESIGN-guest-axiom.md` §8), it runs entirely on committed
instruments, and its blind control is already known to be hostile.

## 1. The boundary being moved

The system can **speak** — it serves verified English renderings of
formal statements, licensed by an exact round trip through the pinned
checker — but it has never checked that what it says **determines what
it meant**. ECHO hands each served sentence to a **code-disjoint**
reader and asks whether the source statement is reconstructed, the
external checker adjudicating identity: a sentence becomes either the
library's first name-free address (the census found the library
nameless; a sentence that determines its statement is a name a person
did not have to type), or a **published collision finding** against a
capability already in service.

**What exists, and the one thing this design must build (review E1).**
`scripts/foreign_voice.py:369` renders and `:395` is its literal
inverse `delexicalize` — but they **share one module**, and the
committed round-trip witness `sha256(serialize(elaborate(...)))`
(`:16-17`) re-renders the inverse through `render` again: it is the
voice's own self-consistency gate, definitionally **not** an
independent reader reconstructing the statement. Pointing that path
back at a sentence would be the arc's signature defect — a checker
validating its own output. So ECHO's disjointness is drawn where it
actually holds and where a fresh instrument is cheap:

- **The identity adjudicator is code-disjoint by construction (B3):**
  the **external pinned checker** decides `RECOVERED`, and it shares no
  code with the renderer — it is a third party the repository did not
  author. This is the disjointness that matters for the truth of an
  identity verdict.
- **The reparser is newly authored (B4), and honest about what that
  buys (review E1a/E1b).** There is **no committed sentence→term path
  that is not `delexicalize`**: in this architecture "stage two" is the
  pinned Lean binary itself (`foreign_voice_lexicon.py:14-16` — "the
  stage-2 reader here is the pinned Lean binary … must never become an
  import-time dependency"), not a Python parser ECHO could plug into.
  So `scripts/echo_reparse.py` is a **from-scratch longest-match
  table-substitution reader** over the committed `data/foreign_voice/
  lexicon.json` rows, importing neither `render` nor `delexicalize`,
  whose emitted term text goes to the same external checker that is
  B3's adjudicator. It is import-disjoint from the renderer's inverse;
  it is **not algorithmically independent of it**, because the
  committed lexicon is bijective by its own load gate (F2 forward-
  injective, F3 reverse-injective, F4 identity both sides,
  `foreign_voice_lexicon.py:23-26`), so any faithful table inverse
  produces `delexicalize`'s token string on well-formed input. ECHO
  says this on the page rather than claiming an independence the tree
  denies: `RECOVERED` is **bounded by lexicon bijectivity** and
  *guarded* — not proven — by the scramble arm, which is exactly the
  test of whether recovery rode word order or only the surviving
  glossary bag.

**The robust half does not depend on echo_reparse at all.** The
collision finding (B6) — *do distinct statements render to identical
sentences?* — is computed from `render` plus the external checker's
identity obligation, never from echo_reparse, so the result that most
directly licenses item 1's clarify disposition holds regardless of the
reparser's algorithmic dependence. ECHO records, for the first time,
whether distinct statements collide in the voice; the reparser arm is
the weaker, honestly-bounded companion measurement.

## 2. The one new first-class object

`experiments/echo_ledger.json`:

- `manifest`: `population_id`, `population_size`, `draw_rule_sha256`,
  `seed`, `sample_n`, `frozen_before_first_render` (bool),
  `stratum_map`, `discrepancy` (free field — see B1's 2,313-vs-native
  resolution)
- `disjointness`: `renderer_sha256`, `reparser_sha256`,
  `shared_module_paths[]` (must be empty — B4)
- `budget`: `machine_id`, `toolchain_pin_sha256`,
  `checker_seconds_real`, `checker_seconds_scramble`,
  `checker_seconds_null`
- `items[]`: `item_id`, `arm` ∈ {`real`, `scramble`, `null`},
  `statement_id`, `parse_tree_sha256`, `stratum` ∈ {`native`,
  `elab_2313`, `resolver_fixture`}, `voice_id` ∈ {`native`, `second`},
  `rendered_sentence`, `sentence_sha256`, `reparse_status` ∈ {`PARSED`,
  `PARSE_FAIL`, `AMBIGUOUS_PARSE`, `NOT_SPOKEN`}, `reparse_terms[]`
  (**all** candidates, not the top one), `identity_verdict` ∈
  {`RECOVERED`, `NOT_RECOVERED`, `UNDECIDED`}, `checker_invocation_digest`,
  `checker_exit`, `checker_seconds`
- `collisions[]`: `sentence_sha256`, `member_statement_ids[]` (≥2),
  `pairwise[]{a, b, distinct: bool, invocation_id}`, `first_seen_item_id`
- `refusal_ledger[]`: `statement_id`, `refusal_type`,
  `named_missing_thing`, `scored_as` ∈ {`correct_refusal`, `miss`}
- `arms_summary[arm]`, `void_flags[]`, `preregistration_sha256`

## 3. Construction gate (numbers frozen now)

- **B1 — denominator provenance.** Population = the voice's sealed
  **committed-speaking** set — the statements a served voice renders,
  which is native ∪ the non-native `elab_2313` second-voice set ∪ the
  13 resolver-binding fixtures (review E2: `elab_2313` is *not* native,
  and the design must not label the population native-only). Chosen in
  prior cycles **before ECHO existed**; ECHO may not add or remove a
  member. `voice_id` is recorded per item and rates are reported **per
  voice**, never pooled; the resolver fixtures report separately. If
  the native set and the 2,313 name disjoint instruments rather than
  nested sets, register both under `stratum_map` and publish
  `discrepancy`; do not take a union figure as if it were one
  population.
- **B2 — sample.** n = **500**, drawn by committed rule and seed
  before any render, stratified across `voice_id` proportional to the
  committed-speaking set; no later capability re-scores these 500
  without disclosure. *Meetable:* the second voice's 2,313 identity
  round trips are already committed at ~4 minutes of checker time
  (v0.22 H-P0), and the native voice's per-statement round-trip cost is
  measured in the **pilot** (B5's 50-item reserve) and published in
  `budget` before the 500 render — B2 does not borrow the second
  voice's cost for the native arm.
- **B3 — identity is checker-adjudicated.** `RECOVERED` may be set
  **only** by the external checker accepting a term-identity
  obligation. String equality, digest equality, or renderer-side
  normalization may not set it. *Meetable:* the checker is the same
  one the voice already round-trips against.
- **B4 — reparser disjointness, checked at registration.**
  `reparser_sha256` is `scripts/echo_reparse.py` (newly authored), and
  `shared_module_paths` — the intersection of its import closure with
  the renderer's (`foreign_voice.render`/`delexicalize` and their
  transitive imports) — must be empty of the render/inverse pair. An
  import of either voids the run **before rendering**: a reader that is
  literally the renderer's own inverse module is comparing a thing to
  itself. The shared *leaf* material both legitimately use — the
  committed `lexicon.json` data and the external checker (the
  "stage-2" pinned binary, `foreign_voice_lexicon.py:14-16`, not a
  parser module) — is published in `shared_module_paths` with a
  per-path justification rather than silently permitted. The empty-set
  target is the `render`/`delexicalize` module import only; §1 states
  that echo_reparse, a re-authored inverse over a bijective lexicon, is
  import-disjoint but not algorithmically independent, so B4 buys code
  separation and B8's scramble arm does the work B4 cannot.
- **B5 — floor over an equal-cost null.** The null arm ignores the
  sentence and returns the population's most frequent parse-tree shape
  at equal `checker_seconds`. Real must exceed null by margin **M**.
  M is **pilot-deferred**: pilot = 50 items from a reserve disjoint
  from the 500; **freeze point** = M written into
  `preregistration_sha256` before any of the 500 renders.
- **B6 — collisions, exhaustive and falsification-only.** Items are
  bucketed by `sentence_sha256`; the pairwise checker identity
  obligation runs **only within a collision bucket** (distinct
  statements sharing a rendered sentence), so the cost is the sum of
  within-bucket pairs, not the full C(500,2) — a sentence seen once is
  no pair. Every bucket of size ≥2 is tested exhaustively and published
  as-is. Zero collisions certifies nothing, and `arms_summary` may not
  carry an "injectivity rate."
- **B7 — correct refusals cannot be bought.** `NOT_SPOKEN` scores
  `correct_refusal` iff typed and naming the missing thing; it enters
  neither numerator nor miss count. Rates report over `speaking_n`
  **and** over n. If refusal share exceeds the voice's committed
  non-speaking share by >5 points, the render path is behaving
  differently under test than in service → void.

## 4. Blind control and voiding sentence

The scramble arm applies a seeded within-sentence token permutation
preserving the exact token multiset — glossary tokens survive, order
dies. **Known-hostile**: v0.20's machine-blind-reader control already
measured that scrambled sentences leak structure, so a pass here is
hard-won, not assumed.

**Frozen voiding sentence, mechanically evaluable:** *If
`arms_summary[scramble].recovered / arms_summary[scramble].speaking_n`
≥ `arms_summary[real].recovered / arms_summary[real].speaking_n` at
`checker_seconds_scramble ≥ checker_seconds_real`, the reader is
recovering the source from surviving glossary tokens and not from the
sentence, and the echo claim is void.* Separation below M is
`UNDERPOWERED`, not a pass.

## 5. Result gate

**R-E:** the injectivity sentence — *a served sentence in this stratum
determines the statement it came from, checker-adjudicated* — is
licensed only for a stratum where the real arm beats the null by ≥M,
beats the scramble arm, and reports its collisions. A collision-bearing
stratum licenses no injectivity sentence; it licenses the **clarify**
disposition of item 1 and hands item 1 a machine-sealed colliding
population.

## 6. Trusted/untrusted, stop conditions, non-claims

Trusted: the committed renderer, the pinned external checker (the
disjoint identity adjudicator), the digest chain, and the **newly
authored** `scripts/echo_reparse.py` (exact code, review-carried, and
the one thing ECHO builds — it is trusted the way the realizer's
lexicon is: correctness by review, independence from the renderer by
B4's import audit). Untrusted: nothing learned appears. Stop: B4's
import audit finds a render/inverse import (before rendering); the pilot
fails to separate real from scramble on the 50-item reserve (publish,
do not run the 500); `UNDECIDED` exceeds 10% of the pilot (an
instrument that times out is unfit, and a timeout is never a pass).
Non-claims: no reader-**meaning** claim (that stayed voided in v0.21 —
injectivity is not comprehension); no universal injectivity; no
coverage claim for the second voice; no prose input; no person in the
loop; no rate is a capability.

## 7. The question that becomes askable, and the residual risk

If the gate fires: **can a served sentence be cited back as an
address?** — the first name-free handle the library has had, the
natural filler for a future HANDLEBAR hole, and a candidate 20th
receipt kind for the cold-receipt harness (a checker-adjudicated
identity obligation).

**Residual risk the gate does not price.** Renderer and reader are
code-disjoint but **ontology-shared**: both were built by one
maintainer against one grammar over the same nine glossary tokens, and
the reader searches a **closed universe** of ~8,500 known statements.
ECHO can recover the source not because the sentence carries the
statement but because the candidate space is small in exactly the way
the renderer ranges over it. Scrambling kills word order; it does not
touch the shared vocabulary prior or the closed world. So ECHO can
clear B5, defeat the scramble limb, commit a clean ledger — and still
license nothing about a stranger, for whom the term universe is open.
The missing arm is a decoy population of checker-valid statements never
ingested; it is absent because the program has no generator for it, and
this design states that hole rather than pricing it with an instrument
that does not exist.
