# Repairable refusals: the "no" that says what would have worked

**Status: DESIGN ONLY.** Nothing here is implemented, and no number below is a
measurement **of the proposed capability**. Some numbers below *are*
measurements — of the shipped admitter, the committed census and this
machine's clock — and each says so where it appears. Selected by the v0.26 outside design course; receipt
[`reports/design-direction-v0.26.json`](../reports/design-direction-v0.26.json),
with the dialect-free brief committed beside it as
[`reports/design-direction-v0.26-brief.txt`](../reports/design-direction-v0.26-brief.txt).
Scheduling is the next roadmap's decision against its own incumbent queue;
this document does not schedule itself. **Lifecycle status, 2026-09-02:**
[ROADMAP-v0.26](ROADMAP-v0.26.md) §1 carries it as the headline *conditional
on that roadmap's own adjudication*, with §1.1 written in the
pre-adjudication "Not yet decided" shape ROADMAP-v0.25 §1.1 used before its
own commission. Nothing here is implemented, and §1's acceptance is the
roadmap's summary of §6-§9 rather than a second specification.

**It displaces no parked lane.** The slice executes nothing and opens no
durable write and no untrusted stream toward the write gate: the searcher
makes repeated calls to a pure function, and the corpus is a sealed committed
file. STRANGER-GATE's prohibition is therefore honored, not displaced. **The cycle
count is the FOURTH, settled 2026-09-02 by repairing the roadmap rather than
by choosing a number here.** This paragraph previously read "third or fourth"
because ROADMAP-v0.25 contradicted itself — §1.1 and §4.1 said "third
consecutive cycle", §3's table said "second cycle honored-not-displaced" —
and §11.2 M-7 flagged that rather than resolving it silently. The v0.25
rotation resolved it on the artifacts: ROADMAP-v0.23 §4.3's STRANGER-GATE row
adjudicated the prohibition in writing for v0.23 and is the row that created
the trigger, ROADMAP-v0.24 §1.1 adjudicated it again, and ROADMAP-v0.25 §1.1
a third time — so **v0.25 was the third and §3's row had omitted v0.23.** That
row now reads "third" with the reasoning dated in place, and this design's
first draft, which said fourth, was right. Nothing in this design turns on
the count. The cost
ledger's denominator is unchanged and this design does not unpark it: §2.3
declines, in writing, the one surface that would have. Whether that park is
carried again is the next roadmap's decision, not this document's.

**Inherited unchanged from [DESIGN-house-rules](DESIGN-house-rules.md):** no
persistence, no export toward library files, no axioms or premises about
declared symbols, no use-side category checking, no natural-language
declaration, and no claim about what people will declare once they can. This
design adds one claim kind and inherits every one of those refusals.

**This document was reworked after adversarial review**, and the record ships
inside it. The first draft was returned REWORK with one Critical and nine High
findings, every one verified against the code rather than against the draft's
prose. Three were structural: a containment clause that **could not pass** on
the very refusal class the design had extended its algebra to serve; a
capability-blind control that lived **strictly inside the searcher's own
search space**, so its voiding sentence was monotone by construction — the
exact v0.25 B9 defect the draft advertised as discharged; and a gate clause
that was **demonstrably false** when run against the shipped decider. §11
records all nineteen findings and what each became.

---

## 1. The boundary and the person it serves

The served line is `declare holds_for/2 (variable, variable)`, and the part
the admitter decides is the line **minus the command word** —
`_DECLARATION_RE`'s own comment says so, and it is load-bearing rather than
trivia: `decide('declare holds_for/2 (variable, variable)')` returns
`REFUSED / UNPARSED`, while `decide('holds_for/2 (variable, variable)')`
returns `ADMITTED_DECLARED_SYMBOL / c9_admit`. Both were run. Every "line" in
this design therefore has two forms, and §3.1 freezes which one each rule
reads.

So: `declare holds_for/2 (variable, variable)` is admitted, and `declare
pairs_up/2 (marsupial)` is refused — the refusal honest and exact: one
deciding clause, first hit in a committed order, totally and by default toward
refusal (`scripts/symbol_ledger.py`, `CLAUSE_ORDER`, `decide`).

*(`holds_for`, `pairs_up` and `marsupial` are placeholders written for this
document and verified absent from the sealed fixture corpus, the collision
census, the schema's category enum, the served grammar rows and their
generated echoes — the discipline `serve_chat.LINE_GRAMMAR`'s `declare` row
adopted after the 2026-09-02 grammar-example finding. §7's B8 puts this
document inside its own sweep's scope, so its examples obey the rule it
states. The first draft of this section did not: it quoted three sealed
fixture values, which is that finding's own vector, and it was caught before
commit by running the check rather than by re-reading the prose.)*

The clause names **which rule stopped the line**. It does not name **what
would have worked**. That asymmetry is not cosmetic here, because of who is on
the other side of it: the whole point of the declaration surface is that the
person is using vocabulary the program never authored. When the program
refuses a line drawn from its own corpus, the author can read the clause. When
it refuses `pairs_up/2 (marsupial)`, the person has to guess whether the count
is wrong, the word is wrong, or both — and there are nine categories, five
reserved prefixes, and 286 census members they cannot see.

**The boundary moves when this becomes recordable:** *for a declaration line
that reached the grammar's production and was then refused on a rule, the
system either exhibits the least-cost edit sequence, over an edit algebra
frozen as data before the corpus existed, that the unmodified admitter admits
— with exhaustive enumeration of the entire below-claimed-cost ball as the
proof of minimality, re-enumerated by a second program written against the
same frozen specification — or it reports that no repair exists within the
frozen bound, together with the size of the ball it searched.*

A refusal stops being a wall and becomes an instruction. That is the human
capability: not a better answer, a usable "no."

### 1.1 What this is not, stated before the design rather than after

- **It is not a suggestion.** `retrieval.ClarificationRequest.suggested_key`
  already exists, and it is a different object: it proposes a durable-store
  key for a datum that is *missing*, and `scripts/retrieval.py:1491` asserts
  the suggested key is `exact_key`-equal to the unresolved literal itself. It
  never edits the person's input. Nothing in this repository proposes a change
  to something the person wrote.
- **It is not spelling correction.** No edit-distance machinery exists on any
  serving path; the only such code in the tree is in
  `experiments/corpus_analogy.py`, a blind control for the analogy lane.
  (`check_report_regeneration.py` uses `difflib` to render a unified diff, not
  to match.)
- **It is not a model.** The searcher is exhaustive enumeration over a frozen
  finite algebra plus repeated calls to `symbol_ledger.decide`. No learned
  component participates in the search, and B6 asserts that by import closure
  rather than promising it. A pinned local model draws the *corpus*, and §4
  lists it as trusted-and-named rather than pretending it is not there.
- **It is not a remedy for an unparseable line.** §3.2 is explicit: the
  algebra reaches clauses c2–c5 and nothing else. A line that never reached
  the production has a remedy already — the published grammar row — and this
  design does not duplicate it.

---

## 2. Why this direction survived, and why the other two did not

The v0.26 course ran three isolated three-round series — fifteen round-one
directions — and the whole funnel, including every declined proposal and its
disposition, is in the receipt. The three finalists:

### 2.1 WITNESS (series 1) — declined, and folded into a park it improves

Necessity certificates over a turn's in-force assumption register, with a
constructor the parked lane has never had: a premise counts as **necessary**
only when ablating it drives the system into a refusal or signed question that
**names that premise**; mere output difference is demoted to `sensitive`. That
constructor is real and new, and it is the fourth independent arrival at the
carried PREMISE LEDGER lane — counting the earlier LOADBEARING fold and the
two (NEEDED-BY, COUNTERMODEL) the v0.25 course produced in one sitting.

Declined as a headline for two grounded reasons, neither of them taste:

1. **Its own residual risk is unpriced by its own gate, and lands where its
   control cannot reach.** A naming refusal may fire for *symbol lookup*
   rather than for derivation: if any binding or scope-resolution step
   mentions a premise by name, removing it produces a refusal naming it
   regardless of whether the answer's derivation consumed its content. Every
   such certificate is true as written and wrong as evidence. Its phantom
   control is unreferenced by construction, so the failure lives exactly among
   premises that *are* referenced but inert — precisely where the phantoms
   cannot go.
2. **Its denominator is unmeasured and plausibly below its own floor.** Its
   first clause stops the lane under 20 recorded turns carrying two or more
   assumptions in force. `session_ledger.LIVE_ASSUMPTION_CAP` is 8, but the
   recorded journals under `experiments/sessions/` have never been counted for
   this. That count is an afternoon's work and it is the lane's named
   prerequisite.

It parks with the constructor attached and the census named. That is progress
on a three-cycle park, not a schedule.

### 2.2 SEPARATOR (series 3) — declined; the highest-ceiling decline

Attack the program's own published cross-discipline identity claims with the
falsification-only pinned-point checker — an instrument coarser than, and
import-independent of, the matcher that made the claims — and publish, per
audited claim, either a separating substitution that kills it by name or an
honest silence that is never phrased as equivalence. Re-scoped under pressure
to EXACT, SPECIALIZATION and exhaustively-enumerated FAMILY entries only,
after conceding that a separator against a SHAPE entry refutes nothing that
was ever claimed.

It is declined here because it parks behind a pre-gate that this design does
not measure and should not pretend to: **at least 8 published EXACT /
SPECIALIZATION / exhaustively-enumerable FAMILY entries whose collapse chain
contains the alias table (`match_signatures.HEAD_ALIASES`) or the
prefix-truncation rule (`BIG_OP_PREFIXES`, five prefixes, still truncating at
HEAD and now disclosed in every parse receipt rather than refused, because
seventeen committed templates depend on it).** Below 8 the instrument has
nothing load-bearing to attack. Counting that population is an afternoon; it
is the lane's trigger, and it is not done here.

Its residual risk is recorded and travels with the park: the pinned-point
domain is drawn from the same committed templates the prefix rule was kept
for, so a clean run of concordant records could mean only that the domain
never looked where the difference lives.

### 2.3 NEAREST YES (series 2) — selected, and cut in half

Selected against the four questions the course asks.

- **It changes what a person can do**, on the surface the previous cycle just
  built, and in the direction the project's plain ambition points: a person
  speaking their own vocabulary gets told what the system would accept,
  instead of being told only that it refused.
- **Its trust boundary is exact and narrower than its claim.** The searcher
  never re-implements a clause; it calls the shipped total function. The
  admitter's bytes are pinned (B6). A repair is an offer that is never
  applied. The certificate copies the deciding clause and the refusal code
  from the admitter's own output rather than deriving them. Nothing is
  executed, written, or persisted.
- **It reuses substance that exists.** `symbol_ledger.decide` is pure, total,
  mutation-free and cheap to call, which is exactly what makes an exhaustive
  ball enumeration a construction rather than a wish; `load_inputs` already
  takes the census and schema paths as parameters, which is what makes §7.2's
  corruption arms real rather than ritual; and the registered-run refusal
  pattern exists (`scripts/run_*_gates.py`, with `run_house_rules_gates.py` as
  the immediate precedent).
- **It can be defeated before implementation and after.** Before the searcher
  is written: the corpus floors and B11b's triviality stop, both computable at
  R-PRE. After: a single unsound certificate, or B11's family ceiling coming
  in below its own threshold.

**On the checker, precisely, because the first draft got this wrong.** This
repository's existing "second program" checkers **re-derive** rather than
avoid imports: `scripts/check_house_rules_receipts.py` imports
`run_house_rules_gates`, `symbol_ledger` and `write_stage`, and
`scripts/check_symbol_census.py` imports `match_signatures`. Their value is
independent recomputation, not import disjointness.
`scripts/check_repair_certificates.py` would be the **first** checker in this
tree that is import-disjoint from the tool it checks — sharing only the
standard library and `symbol_ledger`, which both must import because both must
ask the same shipped admitter. B4 states that boundary exactly, and B5 states
what it does *not* buy.

**Cut in half on selection.** The series proposed two surfaces — declaration
lines and *budgets* — unified on the observation that a budget is an edit
algebra ordered by `≤` and that the least-sufficient search is itself the
partition witness a minted question owes. That unification is elegant and it
is **declined**: the budget surface belongs to the parked cost lanes — TOLL,
whose denominator is n=1, and the cost ledger, whose ninth consecutive
pass-over is recorded as a decision at ROADMAP-v0.25 §3 and §4. A design that
shipped it would unpark them by side effect. It is recorded in the receipt as
the strongest available successor mechanism for that park, and it is not taken
here.

### 2.4 The rest of the funnel

Full dispositions are in the receipt. The load-bearing ones:

- **Convergent arrivals at ground the project already holds**, recorded as
  evidence for those parks and not as lanes: an English reader by
  renderer-inversion (MIRROR FRAGMENT, second arrival, now with a cheap
  injectivity pre-test it did not have); structural addresses for the unnamed
  bulk (the naming-layer lane, second arrival); provisioned outside judges of
  the authored move vocabulary (second arrival, declined again on the same
  recorded lineage ceiling); a genuinely independent second reading of any
  claim (fourth arrival, now with an UNCOMPARED-below-overlap-floor
  discipline); pre-committed cost bounds (the cost lane, again).
- **A red-team of the existing durable-write gate** arrived a *third* time
  across cycles, and this time it carried a mechanism the park has never had:
  mutation of the gate itself, so a kill matrix measures **whether the attack
  corpus is adequate** rather than whether the gate discriminates. That is a
  direct answer to STRANGER-GATE's own recorded residual risk. It parks with
  the mechanism attached; nothing here schedules it.
- **Three genuinely new parks**, each with a named prerequisite: a per-gate
  audit of whether each capability-blind control could have fired at all
  (conceded by its own author to be an instrument rather than a headline, and
  to need a held-out defect chosen by a hand that never saw its category
  list); adversary-equivalence for the learned component, distinct from the
  absence-equivalence already proven by test, behind a census of
  legal-alternative set sizes; and a whole-committed-tree literal-lineage
  index with a fingerprint scheme, the structural successor to the
  grammar-example leak.
- **Three explicit folds**, which are themselves findings: a decomposition
  algebra folded because **no goal or proof-obligation object exists anywhere
  in this program** — a turn is served or refused and nothing outlives it as
  an open obligation, which is now named as a gap rather than assumed away; a
  partial-answer object folded as "the supposition channel with better words";
  and an inconsistency-exhibition lane folded because, with rules about
  declared symbols refused in writing, a scope is bindings plus opaque atoms
  and nothing derives inside it, so an exhibition is unreachable rather than
  merely rare. Refusing to state axioms has consequences, and this is one of
  them.

### 2.5 The re-examination ROADMAP-v0.25 §3 required

That roadmap bound this course: *"If §1's `declare` row ships, the
naming-layer question gains a second live surface and should be re-examined at
the v0.26 course, not silently re-carried."* Re-examined, and the answer is
negative and recorded as such: **`declare` does not advance the naming-layer
question.** A declared symbol is *fresh* by construction — clause
`c5_collides_with_library_symbol` refuses any name already a census member —
so the surface is built to bounce off the library's namespace rather than to
reach into it. The unnamed bulk is exactly as unreachable as it was. The lane
carries, now with COORDINATES' one transferable finding attached:
**exhaustiveness is separable from addressing** — a completeness certificate
("all and only") can be built over whatever naming already exists, so an
address language is not on the critical path of the program's first
completeness claim.

---

## 3. The first-class object

One new artifact kind: `repair_certificate/1`, one record per **refused line
that reached R-PRE's exclusions** — the scorable ones plus the `EXCLUDED` ones,
so the certificate set and the sealed refused population are in exact
correspondence and B3's denominator can be recomputed from either.

| field | meaning |
| --- | --- |
| `schema` | `corollary.repair-certificate/1` |
| `cert_id` | digest over the canonical record, the `symbol_ledger` spelling |
| `corpus_ref` | `{path, sha256_lf}` of the sealed corpus |
| `line_id` | the sealed corpus's id for the line; no line text is copied here |
| `served_digest` | `sha256_lf` of the served line, command word included |
| `input_digest` | `sha256_lf` of the `decided_text` — the served line minus the command word, normalized |
| `verdict_before` | `REFUSED` |
| `refusal_code_before` | copied from the admitter's verdict, never re-derived |
| `deciding_clause_before` | copied from the admitter's verdict, never re-derived |
| `also_grounds_for_before` | `grounds_for(...)` as returned, copied |
| `algebra_ref` | `{path, sha256_lf, algebra_id, k_max}` |
| `edit_sequence[]` | `{op_id, position, from_token, to_token, cost}` |
| `cost` | sum of the sequence's operation costs |
| `ball_size_searched` | distinct candidate lines enumerated |
| `ball_size_below_cost` | distinct candidates enumerated at cost strictly below `cost` |
| `ball_size_by_op` | per-`op_id` candidate counts, for B5's arithmetic check |
| `tie_count` | how many distinct edit sequences achieve `cost`; 1 means the repair is unique |
| `minimality` | `exhaustive_to_k` \| `not_established` |
| `verdict_after` | `ADMITTED_DECLARED_SYMBOL`, re-read from the admitter |
| `deciding_clause_after` | `c9_admit`, copied |
| `output_digest_after` | `sha256_lf` of the repaired normalized line |
| `inputs_ref` | the census and schema `{path, sha256_lf}` pair the admitter cited |
| `checker` | `{tool, tool_sha256_lf, import_disjoint_from_searcher: true, verdict}` |
| `status` | `ADMITTED_BY_REPAIR` \| `NO_REPAIR_WITHIN_K` \| `EXCLUDED` |

**The legal `(status, minimality)` cells, published here so that no cell is
decided after the score:**

| `status` | `minimality` | scores in B3? |
| --- | --- | --- |
| `ADMITTED_BY_REPAIR` | `exhaustive_to_k` | numerator and denominator |
| `NO_REPAIR_WITHIN_K` | `exhaustive_to_k` | denominator only |
| `EXCLUDED` | `not_established` | neither; counted at R-PRE |

No other cell is legal. `ADMITTED_BY_REPAIR` with `not_established` cannot
arise, because §3.1's bounds make the ball provably enumerable; if it ever
arises it is a construction defect and B3 goes red rather than the row being
dropped. This closes the first draft's hole, in which an unreachable
`BUDGET_EXHAUSTED` status could have shrunk the denominator after the run.

The **line text is deliberately absent** from the certificate. Corpus lines
are sealed values, and B8 exists because a sealed value copied into a
committed artifact is a containment failure a run-scoped sweep cannot see.
Certificates carry `line_id` and digests; the text lives in exactly one sealed
file.

### 3.1 The edit algebra, as data

`experiments/repair_algebra.json`, frozen at a commit that precedes the
existence of any searcher and of any corpus line. **It operates on
`decided_text`** — the served line minus the command word — because that is
what `parse_declaration` reads; the parsed positions are those of
`<name>/<arity> (<category>, ...)`. The stripping rule is one line
(`declare` plus one space, at the start, after normalization), it is frozen in
`repair_algebra.json` beside the operations, it is applied by
`scripts/draw_repair_corpus.py` at seal time, and both forms are stored, so no
later program has to guess which one a rule meant:

| `op_id` | effect | cost |
| --- | --- | --- |
| `category_substitute` | one category token becomes a *different* one of the schema's nine | 1 |
| `category_insert` | insert one schema category at a position | 1 |
| `category_delete` | delete one category | 1 |
| `arity_set` | replace the arity digits with a *different* integer in `1..arity_target_max` | 1 |
| `name_char_substitute` | one character of the normalized name becomes a *different* one in `[a-z0-9_]` | 1 |
| `name_char_insert` | insert one character of the declared alphabet | 1 |
| `name_char_delete` | delete one character, result still matching `^[a-z][a-z0-9_]*$` | 1 |

`k_max = 2`. The three name operations are what let a `RESERVED_PREFIX` or a
`COLLIDES_WITH_LIBRARY_SYMBOL` refusal be repairable at all; without them the
algebra would reach only clauses c2 and c3, and the yield would be a fact
about which clauses the algebra can touch rather than about the surface.

**The ball is finite, and its bound is computed rather than asserted.** Let
*L* be the normalized name's length and *c* the number of category tokens.
**`c` is not the arity `a`** — they differ exactly on
`ARITY_CATEGORY_MISMATCH`, which is the clause a good many of these lines will
carry, and conflating them was a review finding. With the frozen operation
bound `arity_target_max = 9`, the cost-1 ball is bounded above by

```
name      36L + 37(L + 1) + L
category  8c  + 9(c + 1)  + c
arity     arity_target_max - 1
```

These are **upper bounds, not sizes**: the `^[a-z]` first-character
constraint, the same-value exclusions written into the operation table, and
duplicate results all reduce them. The searcher records the deduplicated
`ball_size_searched` it actually enumerated together with `ball_size_by_op`.

**Three frozen exclusions bound the input, and they are what make the bound
hold:** `name_length_max = 24`, `category_count_max = 12`, `arity_max = 9`.
`_DECLARATION_RE`'s category group is `[^()]*`, which accepts arbitrarily many
tokens, so without `category_count_max` the ball is *unbounded on a line the
grammar accepts* — that omission was a review finding, not a hypothetical. A
line outside any bound is `EXCLUDED`, recorded and counted at R-PRE, never
deleted.

At those bounds the cost-1 ball is at most `1813 + 225 + 8 = 2046`, a second
step fans out to at most `2138`, and the cost-≤2 ball is bounded by
`2046 + 2046 × 2138 = 4,376,394` candidates. The frozen per-line
`ball_budget` is 8,000,000 evaluations, so the budget is **provably never
reached** under the exclusions — which is why there is no `BUDGET_EXHAUSTED`
status. The budget is retained as a defensive assertion: **a line that reaches
it means an exclusion leaked, and B3 goes red.** This is also why `k_max` is 2
and not 3: at this alphabet the cost-3 ball is bounded by about
`9.8 × 10^9` candidates — three orders of magnitude past the budget — and no
budget this slice could honestly declare would make it enumerable.

**The tie-break, frozen here, and why it is load-bearing rather than
housekeeping.** Minimal repairs are usually **not unique**, and on two of the
four reachable clauses they are wildly non-unique: measured against the
shipped admitter and the committed census, a name colliding with a library
symbol has **hundreds** of distinct cost-1 name edits that admit. Measured
over **all 286** name-shaped census members (baseline `<name>/1 (variable)`,
distinct admitting cost-1 name edits): **minimum 57, median 234, mean 320.5,
maximum 1329**, with 73 members below 200 and 76 above 400. The median name
length is 3, so the short names are the modal case and not an edge. *(An
earlier draft of this paragraph quoted six numbers in the range 219–379 and
described them as "the first six name-shaped members". They were the first six
**of length three to five** — a selection criterion presented as an
observation, which dropped the three genuinely-first members at 57, 151 and
142. The full distribution above replaces it, and §11.1 S-6 records the
correction, because a design that advertises checking its claims against the
code should not launder a filtered sample.)* Without a frozen order
the emitted repair is selector freedom, and two implementations of one
specification would disagree about what the minimal repair *is* while both
being right about its cost.

`repair_algebra.json` therefore freezes a total order on the ball: operations
in the table's listed order, then position ascending, then target token in the
declared alphabet's order (`a`–`z`, then `0`–`9`, then `_`; for categories,
the schema enum's own order). The emitted `edit_sequence` is the least element
under that order, so a certificate is a deterministic function of the line and
the algebra alone.

And because a repair drawn from a median of 234 ties means something very
different from a repair that is unique, every certificate carries `tie_count` and R-R2
publishes its distribution beside the yield. A high tie count is not a defect
— it is the honest shape of "change any one character" — but a design that
reported the repair without it would invite the reader to hear intent where
there is only a total order.

One consequence of that order is worth stating rather than discovering: the
name operations sit last in the table, so for a pure library-symbol collision
the least element is always `name_char_substitute` at position 0 with the
alphabetically least admitting character. **Every c5 certificate will carry
the same operation at the same position.** That is correct behaviour for a
frozen total order over a large tie set, and it is also exactly what §7.2's
vacuity check watches for, which is why the operation-frequency distribution
is published rather than summarized.

**Justification of the frozen numbers**, as §6 of the governing skill
requires — a disclaimer is not a justification:

- `k_max = 2`, `name_length_max = 24`, `category_count_max = 12`,
  `arity_target_max = arity_max = 9`: jointly the largest bounds under which
  the cost-≤2 ball stays under the budget by roughly a factor of two, computed
  above rather than chosen. One asymmetry they create is recorded rather than
  smoothed over: a line with 10 to 12 categories can never be repaired by
  `arity_set`, whose targets stop at 9, and needs more category deletions than
  `k_max` allows — so part of the accepted input space is unreachable by
  construction and will report `NO_REPAIR_WITHIN_K`. The bounds were chosen
  for the budget, not for coherence, and the budget itself (8,000,000) is
  chosen rather than derived.
- `|D| ≥ 58` and scorable `|D′| ≥ 38` (B1/B2): derived, but from the right
  quantity — and an earlier draft derived it from the wrong one and made
  things worse. That draft set the scorable floor at 40 because "one row moves
  agreement by `1/20 = 0.05`, half the ten-point margin." Per-row granularity
  is not what decides whether a control can fire; **rows above the majority**
  is. For a strict `k/n > m/n + 0.10`:

  | scored half `n` | rows above majority needed | operative bar |
  | --- | --- | --- |
  | 19 | `k > m + 1.9` → `m + 2` | 10.53 points |
  | **20** | `k > m + 2.0` → `m + 3` | **15.00 points** |
  | 29 | `k > m + 2.9` → `m + 3` | 10.34 points |

  A 20-row half is *strictly harder to fire* than the 19-row half whose
  failure the draft cited, because any multiple of ten pushes the strict
  inequality onto the next grid point. The floor is therefore **38** (19-row
  halves, operative bar 10.53 points), and the rule is general rather than
  magic: **R-PRE computes the operative bar from `n` and, if it exceeds 12
  points, drops rows from the scored half under a frozen rule until it does
  not** — all before any label exists. The artifact publishes the operative
  bar beside the nominal ten, because those are not always the same number and
  v0.25's failure lived in the gap.
- `60%` (B3): a **flat, frozen** declared bound whose only ground is that it
  must exceed one half, so a coin cannot reach it. It is not a maximum of
  anything. An earlier draft wrote it as `max(0.60, B11's derived floor)` and
  called the second term binding — but B11 sets a threshold on a *control's
  agreement* and defines no yield floor at all, so the headline gate was
  preregistered against an undefined symbol. There is one number here and it
  is 0.60.
- `12` executable containment mutants (B12): two per site type across five
  site types, plus two spare. This is **lower than HOUSE RULES B3's thirty**,
  and the trade is deliberate and recorded rather than silent: those thirty
  were prose descriptions, and the 2026-09-02 finding is that a described
  attempt measures the detector. Twelve that execute are worth more than
  thirty that do not, and if that judgement is wrong the number is the thing
  to move.

### 3.2 What the algebra can and cannot reach, stated before the run

`grounds_for` shows that on a **standalone sealed line** — one line, no
session, no prior admissions — clauses `c6_redefinition_attempt`,
`c7_collides_with_session_name` and `c8_symbol_budget` **cannot fire at all**:
each requires session state a sealed corpus line does not have
(`len(admitted) >= SYMBOL_CAP` needs a populated ledger). And a line that
fails `parse_declaration` returns `None`, so it has no parsed positions and
the algebra has nothing to operate on.

Therefore the algebra's reach is exactly clauses **c2–c5**:
`ARITY_CATEGORY_MISMATCH`, `CATEGORY_NOT_IN_SCHEMA`, `RESERVED_PREFIX`,
`COLLIDES_WITH_LIBRARY_SYMBOL`. Three consequences, all frozen now:

1. `UNPARSED` lines are `EXCLUDED` at R-PRE, counted and published, and are
   **not** scored as misses. Their remedy already exists and is the published
   grammar row.
2. c6/c7/c8 cannot appear in the scored population, and the run artifact says
   so rather than reporting three empty rows as coverage.
3. **B3's floor is conditional on the R-PRE class balance.** R-PRE seals the
   distribution of the scorable population by deciding clause *before* the
   searcher exists; if any single clause holds more than 70% of it, the run
   publishes the yield per clause and the aggregate figure is reported
   **without a pass**, because a floor met by one clause is a fact about that
   clause.

**One thing `UNPARSED` is narrower than it looks, checked rather than
assumed.** `normalize` applies NFC then casefold *before* the production is
matched, so a stranger writing `Holds_For/2 (variable, variable)` does not
get `UNPARSED` — it parses, with `symbol_name` casefolded and the original
kept in `raw_symbol_name`. Capitalization is silently normalized, not refused.

*(That sentence is the third containment leak this document caught in itself,
and the most instructive. Its first draft illustrated casefolding with the
capitalized spelling of a **sealed admitted symbol** — reasoning, wrongly,
that a different capitalization is a different string. It is not:
`run_house_rules_gates._sweep_tree_for_names` casefolds the tree before
matching, so the capitalized spelling is a hit, and the shipped B5 sweep
flagged this file as `added_after_the_seal_and_unclassified` — a **failing
test in this repository**, not a review note. B8 inherits the lesson
explicitly: **the sweep is over casefolded text, and a re-spelling is not an
escape.**)*
The `UNPARSED` class is therefore confined to genuinely malformed lines
(missing or unbalanced parentheses, an arity below 1, an empty category slot,
a name whose *normalized* form still fails `^[a-z][a-z0-9_]*$`), and R-PRE's
count should be read with that in mind rather than as a measure of how often
the stranger wrote something odd.

Extending the algebra to lexical repairs of unparseable lines is named here as
the recorded next extension and is not taken this cycle.

---

## 4. Trusted and untrusted

**Trusted, and named — including the one the first draft left out.**

- `experiments/repair_algebra.json` — committed data, frozen first.
- `scripts/draw_repair_corpus.py` — **new trusted code, and the most
  consequential component in the slice**, because it authors the entire scored
  population. It reuses `machine_reader.MANIFEST` and
  `machine_reader.verify_weights` for the weights pin, but it **cannot reuse
  `machine_reader.ask`**: that call path is hard-wired to forced-choice
  grading (`max_tokens: 4`, a system prompt demanding a single capital letter,
  and `_letter_of` rejecting anything else). A free-decode path with its own
  pinned `max_tokens`, system prompt and stop settings is new code, and all of
  it is digested into the corpus seal. **It also owns the command-word
  strip**: it stores each drawn line in both forms — `served_line` as written
  and `decided_text` as `parse_declaration` will read it — under the stripping
  rule frozen in `repair_algebra.json`, so no later program has to infer which
  form a rule meant.
- `scripts/repair_search.py` — the enumerator and searcher, new trusted code.
- `scripts/check_repair_certificates.py` — the second program, new trusted
  code.
- `scripts/symbol_ledger.py` — **unmodified and byte-pinned**. The searcher
  calls `decide` and `grounds_for` and reimplements neither.

**Untrusted, and it is data only.** The corpus lines. They are strings read
from a committed file; they authorize nothing, are executed by nothing, and
reach no generated library file. Their *provenance* — a non-author model — is
what makes the score meaningful, and is why B8's containment rules apply to
them.

**Absent by assertion, not by promise.** No learned component participates in
the *search*. B6 asserts that `repair_search.py`'s transitive import closure
contains no module that opens the loopback model endpoint, following B11's
precedent in DESIGN-house-rules. The model's participation is confined to
R-PRE, before the searcher exists, and is sealed.

---

## 5. The corpus, and the habit this suspends

**The established habit being suspended: scoring a capability against a corpus
the program authored itself.** Every scored gate this repository has run has
used self-authored fixtures; H-PRE's fixture seal is the current and best form
of that habit, and it is a good instrument for *construction* checks. It
cannot tell you whether a repair yield means anything, because the same hand
would have written the refusals and the algebra that repairs them.

**Scope and duration:** the declaration surface, this slice only. The scored
population must come from a non-author. Self-authored fixtures remain
admissible for the construction checks (B4–B9) and are **excluded from the
scored population by a committed check** (B2). If the non-author corpus does
not clear its floor, the slice publishes `UNTESTED` with the count — it does
not substitute fixtures.

**The non-author would be a machine stranger, and its ceiling is stated with
it.** `scripts/machine_reader.py` already pins one to the byte:
Qwen3-4B-Instruct-2507 at `Q4_K_M`, weights blob SHA-256 `85e4a5b7…4b18b9`,
loopback-only, temperature 0, with `verify_weights` refusing rather than
downloading on absence or mismatch. R-PRE **will** provision it with nothing
but the published grammar row — the `form` string and its example from
`serve_chat.LINE_GRAMMAR` — and ask it to write declaration lines, through the
new free-decode path §4 names. None of that exists yet; the present tense in
the first draft of this paragraph was a review finding, because
`machine_reader.ask` can only return a single capital letter.

What this buys is a corpus **not authored by the maintainer**. What it does
not buy is a fact about people: it is a machine non-author, not a user, and
the artifact header says so in those words.

**Two construction prerequisites this design must not skip.**

1. `machine_reader`'s own manifest records that no seed field exists anywhere
   in this tree, so "temperature-0 determinism" is an assumption this
   repository has never tested. The corpus seal therefore requires two decode
   passes to be **byte-identical**; if they are not, the corpus is not
   reproducible, it is not sealed, and the slice stops. This is a stop, not a
   caveat.
2. A temperature-0 model asked for 200 lines will repeat itself. The seal
   records `distinct_normalized_lines`, and `D` and `D′` are computed over
   **distinct** lines only, so one easy line emitted sixty times cannot carry
   a floor.

---

## 6. Preregistration and construction order

Three stages, in this order and no other, following v0.25's H-PRE → H-P0 →
H-P1 pattern and its gates-runner refusal discipline.

**R-PRE — freeze the algebra, then draw the corpus.** Commit
`experiments/repair_algebra.json` (operations, costs, `k_max`, the three
exclusions, and the closed-form ball formulas B5 checks against) and register
`scripts/repair_search.py` as **not existing at this commit**, the way
`experiments/house_rules_fixtures.json` registered `scripts/symbol_ledger.py`.
Then, in a later commit, draw and seal `experiments/repair_corpus.json`: 200
lines from the pinned stranger, its two byte-identical passes,
`distinct_normalized_lines`, the prompt digest, the weights digest, the
generator's own digest, and the runtime and sampling block; the refused subset
`D` computed by the unmodified admitter over distinct lines; the exclusions
applied and counted; the contamination-excluded scorable subset `D′`; its
class balance by deciding clause; and B11's registration-time family ceiling
and B11b's triviality figure. The sealed house-rules fixture lines are
asserted absent from both subsets.

**R-P0 — the searcher, the checker, and every pin they move.** The searcher,
the certificate schema, the import-disjoint checker, and — in the same change
— every pin the new artifacts move, which is H-P0's rule.

**R-P1 — the registered run.** On a clean tree, under the gates-runner
dirty/wrong-tip/moved-seal refusal pattern, with exactly two declared output
paths (`experiments/repair_certificates.json` and
`experiments/repair_verdicts.json`).

---

## 7. Construction gates

Every number is frozen here, before measurement, and §3.1 gives each one its
ground rather than only a disclaimer.

- **B0 — ordering, proved.** `repair_algebra.json`'s first commit is a strict
  ancestor of `repair_corpus.json`'s first commit, which is a strict ancestor
  of the scoring tip, proved with `git merge-base --is-ancestor` (strict:
  same-commit is not an ancestor) and recorded in the run artifact. The
  algebra was authored before any corpus line was read.
- **B1 — corpus floor.** The stranger writes 200 lines. If the refused subset
  over distinct lines has `|D| < 58`, the slice publishes `UNTESTED` with the
  count and stops.
- **B2 — contamination and scorability.** Two exclusions, both applied at
  R-PRE and both counted. First, contamination: a line is excluded if its
  **served** form (command word included, as the grammar row writes it) equals
  the grammar row's `form` or `example`, or is obtainable from that `example`
  by substituting a single census member or a single schema category — an
  exact string predicate, frozen in the R-PRE commit. The comparison is
  served-against-served deliberately: `form` and `example` both carry the
  command word, so comparing them against `decided_text` could never match and
  the arm would be a check that cannot fire, because "verbatim-derivable" is not computable and would have been
  selector freedom over the population. Second, scorability: `UNPARSED` lines
  and lines outside §3.1's three bounds are `EXCLUDED`. What remains is `D′`.
  If `|D′| < 38`, `UNTESTED`, stop. R-PRE then fixes the fit/held-out split and
  publishes the operative bar §3.1 derives. The intersection of `D` with the sealed
  house-rules fixture lines is asserted empty.
- **B3 — repair yield.** At least **60%** of `D′` — a flat frozen number, not
  a maximum over anything — carries `status = ADMITTED_BY_REPAIR` with
  `minimality = exhaustive_to_k`.
  `D′` is fixed at R-PRE and **cannot shrink after the run**: `EXCLUDED` is
  decided at registration, and there is no post-hoc exclusion status. A line
  that reaches `ball_budget`, or any certificate outside §3's legal
  `(status, minimality)` cells, turns this gate red rather than leaving the
  denominator. If §3.2's 70% class-concentration condition holds, the yield is
  published per clause and the aggregate carries no pass.
- **B4 — soundness, zero tolerance.** Every certificate verifies under
  `check_repair_certificates.py`, which re-runs the repaired line through the
  unmodified `symbol_ledger.decide`. One certificate claiming an admission
  that re-runs to a refusal fails the slice. This is 100%, not a rate.

  **What "import-disjoint" means here, exactly.** The checker's transitive
  import closure and the searcher's intersect in the standard library and in
  `symbol_ledger` alone — both must import the admitter, because both must ask
  the same shipped function. The first draft's claim that the checker "shares
  no imports with the searcher" was impossible and is withdrawn. The checker
  also reads the same committed `repair_algebra.json`, because checking
  against a different specification would check nothing.
- **B5 — minimality is exhaustive, and its blind spot is priced
  arithmetically.** For every `ADMITTED_BY_REPAIR` certificate the checker
  re-enumerates the below-claimed-cost ball from the frozen specification and
  confirms zero admissions.

  **That alone would be a rubber stamp, and the first draft's own text proved
  it:** that draft's cost-1 formula omitted `category_delete` entirely and
  indexed the category operations by arity instead of by category count. Two
  programs written from one specification by one hand can share exactly that
  omission and agree that a ball holds no cheaper repair while a cheaper
  repair sits in the slice they both skipped. So B5 has a second half that is
  arithmetic rather than agreement: each certificate carries
  `ball_size_by_op`, and the checker verifies those per-operation counts
  against the closed-form formulas frozen in `repair_algebra.json`. A missing
  operation is then a **count mismatch**, visible without either program
  noticing its own omission. `ball_size_below_cost = 0` at a claimed cost
  above 1 remains a construction defect, not a null result.
- **B6 — the admitter is untouched, and the search is unlearned.**
  `scripts/symbol_ledger.py` is byte-identical to its pinned digest across the
  slice, re-digested by the runner. `repair_search.py`'s transitive import
  closure contains no module that opens the loopback model endpoint, asserted
  by test. (`draw_repair_corpus.py` does open it, at R-PRE, by design and
  under seal.)
- **B7 — the repair is not a function of the clause order.** A committed test
  transposes two entries of `CLAUSE_ORDER` in a copy and shows that the only
  fields that move in any certificate are `deciding_clause_before`,
  `refusal_code_before` and `cert_id` (which digests them); every
  `also_grounds_for_before`, `edit_sequence`, `cost` and `status` is
  unchanged. The first draft asserted that only `deciding_clause_before`
  moves. That is false of the shipped code and the review demonstrated it by
  execution: `decide` selects by `min(held, key=REFUSAL_CODES.index)` and
  `REFUSAL_CODES` derives from `CLAUSE_ORDER`, so a multi-ground line changes
  its refusal code too — while `grounds_for` appends in a hardcoded order that
  the transposition does not touch, which is why `also_grounds_for_before` is
  the field that genuinely holds still.
- **B8 — containment, over the committed tree, with its carve-outs named.**
  No **whole served or decided corpus line**, no whole repaired line, no
  **source name from any corpus line**, and no **repaired name that is not a
  schema enum value** appears anywhere in the committed tree outside the
  sealed corpus file and the two declared output paths — swept over the whole tree, including documentation,
  generated artifacts, the served grammar rows and their generated echoes,
  fixtures, comments and file names. **The sweep casefolds before matching**,
  following `run_house_rules_gates._sweep_tree_for_names`, so a re-spelling of
  a sealed value is not an escape — §3.2 records the leak that established
  this the hard way.

  **The carve-outs are not a weakening; without them the gate is
  unsatisfiable.** A line refused `COLLIDES_WITH_LIBRARY_SYMBOL` is refused
  *precisely because* its name is a member of `experiments/symbol_census.json`
  — `grounds_for` tests `parsed.symbol_name in inputs.equality_members` — so
  that name is in the committed tree by definition, and the same holds for
  every category token, which lives in `schema/equation-node.schema.json`. The
  first draft's sweep would therefore have gone red on the exact refusal class
  §3.1 extended the algebra to serve. The carve-out list is frozen at R-PRE
  and is exactly: the census's `equality_members`, the schema's category enum,
  the reserved prefixes, and the algebra file's own operation vocabulary.

  **Source names are in the forbidden set because the leak this gate
  discharges was a leaked NAME**, not a whole line: the 2026-09-02 finding was
  a sealed fixture symbol landing in `LINE_GRAMMAR`'s `example`, and the
  instrument this gate follows, `_sweep_tree_for_names`, sweeps names. An
  earlier draft forbade whole lines and *repaired* names only — which left the
  fresh stranger-invented names on c2 and c3 lines quotable anywhere, and §3.1
  expects c2 to be a clause a good many lines carry. Note also that the census
  half of the *repaired*-name carve-out was dead and is gone: a repaired name
  that admits can never be a census member, because c5 would have fired.

  This gate is the direct discharge of the 2026-09-02 grammar-example finding:
  a check scoped to a run's outputs cannot see a value that is already
  committed. **This design document is itself in that scope**, which is why §1
  quotes only placeholders verified absent.
- **B9 — no library byte, no persistence.**
  `write_stage.working_tree_file_digests` — the per-path form
  `run_house_rules_gates._covered_paths` already uses, and not the whole-tree
  `working_tree_digest`, which the run's own output files would move — shows
  every covered path byte-identical across the registered run except the two
  declared output paths, with `write_stage.durable_digest` over `data/` as the
  narrow named control. `session_state.encode`'s closed `_TYPES` registry
  still refuses both declaration record types, asserted rather than assumed.
- **B10 — the run is registered.** Prereg committed before the run; sealed
  commit a strict ancestor of the tip; every `frozen` pin re-digested; a dirty
  tree or a wrong tip refuses. `--allow-dirty` sets
  `registered_before_the_run: false` and licenses nothing.
- **B11 / B11b — the blind control and the triviality floor.** §7.1.
- **B12 — executable, not described.** Every containment mutant in B8 is a
  **program that performs the attempt and returns what happened**, scored
  solely by whether the value landed in the committed tree and never by
  whether a detector fired, and each carries a machine-readable detector id
  **in the seal** rather than a prose sentence a later runner is free to
  interpret. At least **12** such mutants across the five site types (a
  generated library file, a served grammar row, a generated artifact echoing
  that row, a documentation file, a fixture file), at least two per site type.
  This is the direct discharge of the 2026-09-02 finding that a containment
  gate whose mutants are prose is a gate that has never been run; §3.1
  justifies the count and records that it is lower than the thirty prose
  mutants it replaces.

### 7.1 B11 — the blind control, and B11b — the triviality floor

**Why the first draft's control was void, stated plainly, because it was the
same defect this design claims to discharge.** That draft's family was "every
single operation of the algebra applied at a fixed position." Every member's
output is a **cost-1 point of the searcher's own ball**. So if any member
repairs a line, the exhaustive searcher repairs it at cost at most 1, and the
control's rate can never strictly exceed the searcher's — the voiding sentence
was monotone by construction and could fire only on an exact tie. That is
v0.25's B9 finding — *a control that cannot fire measures nothing* — rebuilt
inside the gate advertised as its remedy. An exhaustive searcher dominates any
control drawn from its own search space; a real control must therefore predict
the *outcome* without searching.

**B11, the blind control.** Family: **surface-only repairability predictors**,
registered before the run. Each member predicts the label
`ADMITTED_BY_REPAIR` / `NO_REPAIR_WITHIN_K` from features of the raw line
alone — its length, token count, comma count, name length, and the integer
after `/` — with **no access** to the census, the schema, the algebra, the
deciding clause, or `decide`. **One thing that buys the control more power
than "surface-only" sounds, disclosed rather than left to be found:** comma
count and the integer after `/` jointly recompute clause c2 exactly
(`commas + 1 ≠ arity` is `ARITY_CATEGORY_MISMATCH`), and c2 lines are
repairable at cost 1 by `arity_set` — so a two-feature conjunction is a
near-perfect predictor on one of the four reachable clauses. That is a
*stronger* control, which is what this gate wants, but it materially raises
the chance B11 fires, and it is not what a reader would assume from the word
"surface". The registered family is closed intervals over one feature and
two-feature conjunctions over the same five, with the tie-break frozen in the
same commit (lexicographically smallest feature name,
then smallest threshold). The scorable population is split in half at R-PRE,
the class balance of both halves is sealed there, a member is fitted on the
fit half, and its agreement is scored on the held-out half. This is HOUSE
RULES B9's shape, which is this repository's own precedent, and it is not a
subset of the searcher's ball because it never searches.

**The ceiling check, and the honest ordering it requires.** The label B11
predicts is the searcher's own output, so the family's ceiling **cannot** be
computed before the searcher runs — saying otherwise would be a circularity,
and the first draft's control could be checked at registration only because it
was a subset of the searcher and therefore measured nothing. The timing is
split instead, and both halves are enforced by the runner:

- **Frozen at R-PRE, before `repair_search.py` exists:** the family and its
  five features, the tie-break, the split of the scorable population into fit
  and held-out halves, both halves' class balance *by deciding clause* (which
  needs no searcher), the ten-point margin, the operative bar §3.1 derives
  from the split, the rule that a family ceiling below the voiding threshold
  is a **construction defect** rather than a pass, and — because an
  unregistered remedy is the escape hatch this gate exists to close — **the
  enrichment itself**: the family may be expanded exactly once, from
  single-feature closed intervals and two-feature conjunctions to
  **three-feature conjunctions over the same five features**, and no further.
  Three features is the cap. If the enriched family's ceiling is still below
  the threshold, the control is unfireable on this corpus and that is a
  **stop**, not a licence to keep adding members until one fits.
- **Computed at R-P1, the moment the labels exist and strictly before B3's
  aggregate is read:** the held-out half's majority-class rate *of the label*,
  then the whole registered family's maximum achievable agreement on that
  half, then — only if the ceiling clears the threshold — the fitted member's
  agreement. The runner emits these three in that order and **refuses to emit
  B3's fraction until the ceiling has been recorded**, so the ceiling can
  never be read after a yield it might have voided.

This is the one-line computation nobody had done at v0.25, placed at the
earliest point where it is not circular rather than at the earliest point that
sounds strongest.

**What that ordering does and does not buy, so it is not read as stronger than
it is.** The runner's refusal to emit B3 before the ceiling is a discipline in
the runner's own code, and a determined author could reorder it. The
*substantive* protection is elsewhere and does not depend on ordering at all:
the family, the five features, the tie-break, the split and the ten-point
margin are all frozen at R-PRE, so nothing about what voids the capability can
be chosen after seeing a number. The ordering protects the author's reasoning,
not the arithmetic, and that is the whole of its claim.

**And the degeneracy check v0.25 paid for.** That cycle's fitted rule
predicted REFUSED for every scored row, so its reported agreement equalled the
majority-class rate *by arithmetic rather than by signal*, and nothing in the
gate said so. Here the artifact must publish, beside the agreement figure, the
fitted rule's **predicted-class distribution on the scored half**. A rule that
predicts one class for every row is reported as degenerate and its agreement
is not read as evidence of anything — in either direction.

**B11b, by contrast, genuinely is a registration-time computation** — constant
edits plus `decide` need no searcher — which is why it can stop the slice
before `repair_search.py` is written at all.

**The voiding sentence, verbatim:** *If the best member of the registered
surface-only family, fitted on the fit half with the tie-break declared in
advance, agrees with the searcher's label on the held-out half by more than
ten points above that half's majority-class rate, then the repair verdict is
predictable from the line's surface alone, separable from every committed
input and from the deciding clause, the capability is void, and the slice
ships as an honest negative with its verdict table.*

**The coupling between B3 and B11, unpriced and therefore stated.** B11 can
fire only where the held-out majority-class rate `m` leaves room: at
`m = 0.85` it needs 100% agreement, and at `m ≥ 0.90` the threshold exceeds
1.0 and **no member can fire by arithmetic**. B3 requires a yield of at least
0.60, which makes `ADMITTED_BY_REPAIR` the majority class whenever B3 passes.
So the window where B3 passes *and* B11 can fire is roughly a yield in
`[0.60, 0.80]`: **the better the capability performs, the more likely its
blind control is structurally void.** That is the v0.25 B9 shape arriving
through the front door. B11's ceiling check detects it — that is what the
check is for — and the consequence is fixed here rather than negotiated
later: if the ceiling is unreachable because `m > 0.85`, the run reports the
capability **licensed but uncontrolled**, publishing `m`, the ceiling and the
yield together, and **R-R1's sentence is not written**. A high yield does not
buy its way past a control that could not have fired.

**B11b, the triviality floor** — what the constant-edit family is honestly
good for, and it is not nothing: it is the only one of the two that can be
computed before the searcher exists. Compute the best single constant edit's
admission rate on the scorable population at R-PRE. It is a subset of the searcher's ball and can
therefore never *void* anything, and it is not called a control. It can
**stop** the slice: if one fixed edit repairs at least **50%** of the scorable
population, the corpus is one systematic mistake rather than a surface worth
searching, and the slice stops and publishes that number.

### 7.2 Corruption, vacuity and negative controls

- **Corruption, two arms, both pointed at mutated copies** —
  `symbol_ledger.load_inputs` already takes both paths as parameters for
  exactly this reason. Remove one reserved prefix from a census copy: a line
  whose `also_grounds_for_before` is exactly `('RESERVED_PREFIX',)` must stop
  needing a repair at all. The sole-ground condition is not decoration —
  `sum_i` is simultaneously a census `equality_member` and reserved-prefixed
  (the only such member of the 286), and since c4 precedes c5, removing the
  prefix leaves `sum_i/1 (variable)` still refused on
  `COLLIDES_WITH_LIBRARY_SYMBOL` and still needing a repair. An unconditioned
  arm would go red on a plausible stranger line. Delete one
  category from a schema-enum copy: a certificate that repaired into that
  category must change. **The category is named in the prereg** — HOUSE RULES
  B8's precedent for naming a corruption arm's target — chosen at R-P1 as one
  an emitted certificate actually repaired into. Naming it matters because
  §3.1's tie-break orders category targets by the schema enum's own order, so
  repairs concentrate on early entries and deleting a late one would change
  nothing. A certificate unmoved by either mutation is not
  reading its committed inputs.
- **Vacuity.** The operation-frequency and cost distributions over all emitted
  `edit_sequence`s are published beside the yield. A searcher that only ever
  emits one operation is a constant repairer wearing a search's clothes, and
  B11b is the number that says so. Note which way this cuts, and how far it
  does **not** reach: a constant *name* edit can repair only c5 lines — it
  cannot touch a category or an arity — so "one constant edit clears B11b's
  50% floor" requires c5 lines to be **at least half of `D′`**, which is
  unknown until R-PRE publishes the class balance and which this design does
  not estimate. So the honest statement is conditional: *if* c5 dominates the
  scorable population, B11b is likely to stop the slice early and cheaply, and
  §3.2's 70% class-concentration rule would already be reporting per-clause in
  that regime. An earlier draft asserted the stop as "the single outcome this
  design most expects", which does not follow from the tie counts and is
  withdrawn.
- **Negative control.** `NO_REPAIR_WITHIN_K` lines are counted and their ball
  sizes published. They are the design's own blind spot, and §9 says so.

---

## 8. Result gates and the licensed sentence

**R-R1 — licensed only on B0–B12 all green.** *For a declaration line that
reached the grammar's production, was refused on one of clauses c2–c5, and was
drawn from a non-author corpus, the system exhibits the least-cost edit over a
pre-frozen algebra that the unmodified admitter admits, with exhaustive
enumeration below that cost as the proof and a second program's arithmetic on
the ball's per-operation counts as the check — or reports that no repair
exists within the frozen bound, together with the ball it searched.* Nothing
more. If any gate is red, this sentence is not written.

**R-R2 — reported regardless, gating nothing.** The distribution of `D′` by
deciding clause, the yield broken down by clause, the `tie_count`
distribution, and the counts of every exclusion. Its reading is pre-committed here: a clause with zero repairs is a
fact about the algebra's reach, not about the clause, and may not be read
either way after the fact.

**R-R3 — the bounded negative.** A failed B1, B2, B3, B11 or B11b licenses the
bounded negative with its verdict table; it does not license loosening any
clause after the score. The precedent for publishing a red is B7 at v0.24.

---

## 9. Stop conditions and non-claims

**Stops.** Any of these ends the slice rather than being repaired into a pass:
`|D| < 58`; `|D′| < 38`; the stranger's two decode passes not byte-identical;
B11b's triviality floor met; B11's family ceiling below its threshold at R-P1 and not
repairable by the registered enrichment; any B4 violation; any B6, B7, B8 or
B9 violation; the searcher found to re-implement any clause of the admitter;
any line reaching `ball_budget`, which would mean an exclusion leaked.

**Non-claims, published with the result.**

1. **A repair is an offer.** Nothing is auto-applied, and the person's line is
   never rewritten by the system.
2. **Minimality is not intent, and on two clauses it is barely even a
   choice.** The least edit in a declared algebra is not what the person
   meant, and no certificate says it is. Where `tie_count` runs to the
   hundreds — the normal case for a library-symbol collision — the emitted
   repair is the least element of a frozen total order over a large tie set,
   and nothing more is claimed for it.
3. **No claim about the algebra's coverage.** `NO_REPAIR_WITHIN_K` is counted,
   never diagnosed.
4. **No claim beyond clauses c2–c5.** Unparseable lines and the three
   session-state clauses are outside the capability, by §3.2 and in writing.
5. **No claim about people.** The corpus is machine-authored and
   single-lineage, and a non-author is not a user.
6. **Ledger-groundedness, never correspondence** — inherited. A repaired
   declaration is well-formed and fresh, never true or useful.
7. **No budget or cost surface**; TOLL and the cost ledger stay parked.
8. **No change** to the clause order, the alias table, the prefix rule, or any
   served behaviour beyond what R-P0's pins record.
9. **No persistence and no export** — the house-rules refusals are inherited
   whole, and B9 is their enforcement here.

**The residual risk this design's own gates do not price.** *The algebra
defines the corpus's difficulty.* B0 freezes the algebra before the stranger
writes, which prices anticipation-by-inspection but not
anticipation-by-familiarity: the same maintainer authors the operations, and
the `k_max = 2` ball lands where they already expect refusals to cluster. B3
then passes with every certificate sound and genuinely minimal *within the
algebra*, B4 and B5 hold, and B2 shows no contamination — and the artifact
reads as *"refusals on this surface are repairable"* while meaning only *"the
algebra covers the errors that were anticipated."* B11 prices predictability
of the *label*, not coverage of the *algebra*; nothing in B0–B12 measures the
refusals the algebra failed to admit. The clean fix is a second stranger
authoring the algebra blind to the surface; that is **named here and not taken
this cycle**, and its absence is the price being paid.

---

## 10. Where status lands

- **The next roadmap** links this design with an explicit lifecycle status and
  adjudicates it against the incumbent queue. This document schedules nothing.
- **ANALYSIS** receives R-P1's corpus counts, the yield with its clause
  breakdown, B11's family ceiling and held-out agreement beside the
  majority-class rate, B11b's figure, and the operation and cost
  distributions.
- **DISCOVERIES** receives only measured surprises: a fired voiding sentence,
  a met triviality floor, a B4 violation, or a clause the algebra provably
  cannot reach.
- **BACKLOG** carries the declined leads and folds with their triggers, all
  recorded in the course receipt: WITNESS behind its assumption-count census;
  SEPARATOR behind its 8-entry convention-dependence pre-gate; the write-gate
  mutation-adequacy mechanism against the STRANGER-GATE park; the per-gate
  control-ceiling audit behind its held-out-defect prerequisite;
  adversary-equivalence behind its legal-alternative census; the
  literal-lineage index; the missing goal object, newly named; and this
  design's own next extension, lexical repair of unparseable lines.
- **The next askable question, if R-R1 lands.** Refused declaration lines,
  each annotated by the least edit that admits, would be a corpus of
  declaration attempts this repository did not author.
  [DESIGN-house-rules](DESIGN-house-rules.md) §10 asked for its
  premise-grammar question to be priced against *the corpus of declarations
  this slice will have produced* — that is, against its own self-authored
  fixtures. A non-author corpus is a stronger thing than that section asked
  for, and it is stated here as stronger rather than attributed to it.

---

## 11. The review record

**Two** independent adversarial reviews were run, and the document was
reworked after each. The first returned **REWORK** on one Critical, nine High,
six Medium and three Low; §11.0 tabulates it. The second, run against the
reworked text, returned **REWORK** again on one Critical and six High — and
its Critical was a defect the first rework itself introduced: B3, the headline
gate, had been rewritten as `max(0.60, B11's derived floor)` while B11 was
being replaced, leaving the slice's pass condition preregistered against a
symbol that no section defines. §11.2 tabulates the second. §11.1 holds the
findings the design made against itself between them.

Every finding in all three tables was checked against the code, several by
execution. The count is the point: a design that is wrong in its headline gate
after one adversarial pass is a design that needed two.

### 11.0 The first review

What each finding became:

| finding | what was wrong | what it became |
| --- | --- | --- |
| **C-1** | B8 could not pass: a `COLLIDES_WITH_LIBRARY_SYMBOL` refusal's name is a census member by definition, so it is already in the committed tree | B8 rewritten with frozen carve-outs, scoped to whole lines plus non-census names |
| **H-1** | the blind control was a strict subset of the searcher's own ball, so the voiding sentence was monotone and could never strictly fire; and a `0.05 ≤ C < 0.60` band left a margin decaying to half a point | B11 replaced by a surface-only label predictor that never searches, with a family-ceiling check whose timing S-1 below then had to correct; the constant-edit family demoted to B11b, a stop, and never called a control |
| **H-2** | B7 was false against the shipped `decide`: `refusal_code_before` and `cert_id` move under a clause transposition too | B7 restated over the three fields that move and the four that do not |
| **H-3** | §1 claimed the checker "shares no imports with the searcher", which is impossible; and B5's re-enumeration could rubber-stamp a shared misreading of the spec | the claim withdrawn and stated exactly in B4; B5 given an arithmetic second half over `ball_size_by_op` |
| **H-4** | the cost-1 formula omitted `category_delete`, counted self-substitution, and indexed categories by arity rather than by category count | formula corrected and recomputed; the error is now cited in B5 as evidence the shared-misreading risk is real |
| **H-5** | `arity_set` had an unbounded codomain and nothing bounded the category-token count, so the ball was not finite on a line the grammar accepts; and `BUDGET_EXHAUSTED` was unreachable dead weight | `arity_target_max` and `category_count_max` frozen; `BUDGET_EXHAUSTED` removed as a status, the budget kept as a defensive assertion whose breach turns B3 red |
| **H-6** | the algebra was undefined on `UNPARSED` lines, which would have scored as misses; c6/c7/c8 cannot fire on a standalone line at all; B3's floor ignored a class balance R-PRE already computes | §3.2 added: the reach is c2–c5, `UNPARSED` is `EXCLUDED`, and B3's floor is conditional on the sealed class balance |
| **H-7** | no floor on the scored denominator, and no de-duplication rule for a temperature-0 generator | scorable floor raised to 40 and *derived* from B11's margin; `distinct_normalized_lines` sealed and `D`/`D′` computed over distinct lines |
| **H-8** | the claim that an import-disjoint checker precedent exists is refuted by the code — `check_house_rules_receipts.py` imports the runner it checks | §2.3 restated: the precedent is re-derivation, and this would be the first import-disjoint checker in the tree |
| **H-9** | `machine_reader.ask` cannot write a line (`max_tokens: 4`, single-letter output), and the program authoring the entire scored population was unnamed and missing from §4 | `scripts/draw_repair_corpus.py` named in §4 and R-PRE; §5 put in the future conditional |
| **M-1** | STRANGER-GATE cycle count off by one in the design and the receipt | corrected to third in both |
| **M-2** | `working_tree_digest` cannot express B9's per-path check | B9 names `working_tree_file_digests` |
| **M-3** | §10 misquoted DESIGN-house-rules §10, and the receipt used the misquote as a selection ground | corrected in both; the stronger fact stated without attributing it |
| **M-4** | "verbatim-derivable" was not computable and set the population | frozen as an exact string predicate in B2 |
| **M-5** | `status` and `minimality` had no stated invariant | the legal cross-product published in §3 |
| **M-6** | frozen numbers carried a disclaimer instead of a justification | §3.1 gives each its ground; the floors are now derived from B11's margin |
| **L-1** | TOLL's n=1 and the cost ledger's ninth pass-over were conflated | §2.3 names both rows |
| **L-2** | B12's 12 silently undercut HOUSE RULES B3's 30 | stated and defended in §3.1 |
| **L-3** | the budget is priced in calls and never in time | recorded here: `decide` measures about 15 µs per call on the maintainer's machine, roughly 95% of it the two digests it computes, so a worst-case ball is about 63 s and 200 lines about 3.5 hours. The searcher may enumerate with `parse_declaration` + `grounds_for` and call `decide` only on admitting candidates — measured at **2.08 µs** for the pair, not the 0.67 µs `grounds_for` costs on an already-parsed line, so the optimization pays about 7×, not 22×: roughly 9 s per worst-case line. R-P0 should do it, and B10's registered run should carry a wall-clock note |

### 11.1 Five more the design found in itself, after the review

The review is not the only instrument that ran. Five findings came from
applying this design's own rules and this repository's own instruments to this
design, and they are listed because most of them are the kind a reader should
be able to check.

| finding | what was wrong | what it became |
| --- | --- | --- |
| **S-1** | B11's ceiling was specified "at registration, before any searcher output exists" — but B11 predicts the **searcher's own label**, so that ordering is circular. The first draft's control could be checked at registration only because it was a subset of the searcher and therefore measured nothing: the same defect wearing the opposite face | §7.1 splits the timing — family, features, tie-break, split, clause-wise class balance, margin and the defect-rule frozen at R-PRE; ceiling and fitted agreement computed at R-P1 the moment labels exist and strictly before B3's aggregate, with the runner refusing to emit B3's fraction until the ceiling is recorded |
| **S-2** | no tie-break existed for equal-cost repairs, though a library-symbol collision admits **219 to 379** distinct cost-1 admitting name edits (measured against the shipped admitter and the committed census). "The minimal repair" was therefore selector freedom on two of the four reachable clauses | §3.1 freezes a total order on the ball and every certificate carries `tie_count`, with R-R2 publishing its distribution; the same measurement makes B11b's triviality stop the most likely outcome of the slice, which §7.2 now says in advance |
| **S-3** | §1's worked examples were three **sealed fixture values** — an admitted symbol, a refused symbol and a bogus category — which is the 2026-09-02 grammar-example finding's own vector, in a document whose B8 puts itself in scope | replaced with placeholders verified absent from the fixture corpus, the census, the schema enum, the served grammar rows and their generated echoes |
| **S-4** | §3.2 illustrated the admitter's silent casefolding with the **capitalized spelling of a sealed admitted symbol**, on the wrong assumption that a re-spelling is a different string | `run_house_rules_gates._sweep_tree_for_names` casefolds before matching, so the shipped B5 disclosure classified this file `added_after_the_seal_and_unclassified` and `tests.test_house_rules_run` went **red**. This was a failing test in the repository, not a review note — the previous cycle's instrument caught this cycle's design document. Fixed, and B8 now states that the sweep casefolds and a re-spelling is not an escape |
| **S-5** | B11's ordering claim was stronger than it can be, and the v0.25 degeneracy that motivated the whole gate was not itself checked | §7.1 states that the R-PRE freeze, not the ordering, is the substantive protection, and requires the fitted rule's predicted-class distribution on the scored half to be published beside its agreement, with a one-class rule reported as degenerate |

S-4 is the one worth carrying beyond this slice. A containment instrument
built in one cycle caught a leak in the next cycle's *prose*, before that
prose had any code under it — which is the strongest evidence available that
the instrument is scoped correctly, and it is a better argument for B12's
executable mutants than any sentence in §7 could be.

### 11.2 The second review

Run against the reworked text; **REWORK**, one Critical and six High. Its
verdict on the first rework is recorded too: B7, the ball arithmetic, §3.2's
reach derivation, B5's arithmetic second half and B11's escape from the
searcher's ball were all verified correct and non-cosmetic. These are what was
still wrong.

| finding | what was wrong | what it became |
| --- | --- | --- |
| **C-1** | **B3, the headline gate, had no evaluable threshold.** The first rework rewrote it as `max(0.60, B11's derived floor)` while B11 was being replaced; B11 sets a threshold on a *control's agreement* and defines no yield floor, and at the time the phrase "derived floor" occurred exactly once in the whole document — in that line. §3.1 then called the undefined term *binding*. R-R1's licensed sentence depended on it | B3 is a **flat frozen 0.60**, not a maximum over anything, with §3.1's honest ground (it must exceed one half so a coin cannot reach it) |
| **H-1** | the scorable floor of 40 was **derived backwards and made the cited failure worse**. What decides whether a control can fire is rows-above-majority, not per-row granularity: at n=19 a strict `k/n > m/n + 0.10` fires at `m+2` (bar 10.53 points); at n=20 it fires at `m+3` (bar **15** points), because any multiple of ten pushes the strict inequality onto the next grid point. The proposed floor was strictly harder to fire than v0.25's 19-row half whose failure it cited | floor is **38** (19-row halves, operative bar 10.53 points), and the rule generalized: R-PRE computes the bar from `n` and drops rows under a frozen rule if it exceeds 12 points. The artifact publishes the operative bar beside the nominal ten |
| **H-2** | §9's stop condition had an **undefined escape hatch** — "not repairable by the registered enrichment", where no enrichment was registered anywhere. The one stop that fires when the control turns out unfireable licensed widening the family *after* labels exist | the enrichment is frozen at R-PRE: one expansion, to three-feature conjunctions over the same five features, capped there; still-unfireable is a **stop** |
| **H-3** | **`decide` reads the line minus the command word**, so §1's opening assertion was false against the shipped code (`decide('declare holds_for/2 …')` → `REFUSED / UNPARSED`); §3.1 defined the algebra over a string `parse_declaration` cannot parse; no component stripped the word; and B2's contamination arm compared stripped lines against `declare`-prefixed strings, so it **could never fire** | both forms are stored (`served_line`, `decided_text`), the strip is frozen in the algebra file and owned by `draw_repair_corpus.py`, and B2 compares served-against-served |
| **H-4** | the tie-count measurement's **stated provenance was false**: "the first six name-shaped members of the census" were the first six *of length three to five*, a selection criterion presented as an observation, dropping the genuinely-first three at 57, 151 and 142. The design used that filtered sample to predict its own most likely outcome | the full distribution over all 286 members is reported — min 57, median 234, mean 320.5, max 1329, 73 below 200 and 76 above 400 — and the selection is disclosed |
| **H-5** | B8 forbade whole lines and *repaired* names but **not source names** — yet the 2026-09-02 leak it discharges was a leaked *name*, and the instrument it follows sweeps names. Fresh stranger-invented names on c2/c3 lines were quotable anywhere | source names added to the forbidden set under the same carve-outs |
| **H-6** | the **receipt re-asserted two defects the design says it fixed**: an imported lesson still claimed B11's ceiling is computed "at REGISTRATION, before any score exists" in "three frozen branches", and another still listed `BUDGET_EXHAUSTED` as one of three silences | both entries and the stale structural-findings entry rewritten to match §7.1 and §3 |

Its eight Medium and four Low findings were taken as well: the
"no number is a measurement" claim scoped (M-1); B11's two features that
reconstruct clause c2 disclosed (M-2); B8's dead census carve-out on repaired
names dropped (M-3); corruption arm 1 conditioned on a sole ground, because
`sum_i` is both reserved-prefixed and a census member (M-4); corruption arm 2's
target named in the prereg (M-5); the B3/B11 coupling stated with its
consequence fixed (M-6); ROADMAP-v0.25's self-contradiction on the
STRANGER-GATE cycle count flagged rather than silently resolved (M-7 —
**repaired at the v0.25 rotation on 2026-09-02**: §3's "second" was the
defective row, v0.25 is the third honored cycle and this design's cycle is the
fourth, which also means §11.0's M-1 "corrected to third in both" was a
correction *toward* the defect; §1 above and ROADMAP-v0.26 §1.1 carry the
determination and its evidence, and the course receipt is left unedited as a
record of the course as it ran); B11b's
prediction made conditional on c5's share (M-8); the ROADMAP §1.1→§3/§4 cite
corrected (L-1); the optimization's real cost measured at 2.08 µs rather than
0.67 (L-2); the certificate/population correspondence restated (L-3); and the
`category_count_max` / `arity_target_max` asymmetry recorded (L-4).
