# Statements that run: the corpus takes your numbers, and refuses to call agreement proof

**Status: design only.** Nothing here is implemented. First slice targets
v0.20, **selected by the outside design course** whose receipt is
`reports/design-direction-v0.20.json` and whose brief is committed beside it
as `reports/design-direction-v0.20-brief.txt`; the receipt pins that brief at
LF-canonical sha256 `11c676b63bf0adbc…`, so the text the advisors were given
is on file rather than described. This document discharges
[ROADMAP-v0.20](ROADMAP-v0.20.md) §1's dated **status note** (`:31–44`),
which records that this design landed on disk during the rotation **awaiting
adversarial review** and that every sentence in that section describing the
*design* rather than the *course receipt* is provisional until the review
closes. The review has closed; this is the reviewed text, and it is item 1 of
the cycle — its gate, its controls and its stop conditions.

This document is the second half of that gate. The course's final form was
the outline; everything below has been checked against the committed tree
before being written down. **Eight of the advisor's load-bearing assumptions
did not survive that check** — including the headline count, the identity of
the object being compiled, and the meaning of the direction's most exciting
answer type. Seven were found by grounding against the tree; **Correction 2
was found by the adversarial review of this document's first draft**, and is
numbered in document order with the rest rather than appended. Eight is the
count, stated once here and nowhere else. All are corrected in place, dated,
with the measurement that corrected them, because a design that inherits an outside idea without
inspecting the machine it will run on is how a course becomes a wish.

## 1. The boundary being moved, and what a person gains

Two lanes have brought the corpus to the edge of this question and stopped
there.

The **calculator** half exists and is wired. `scripts/evaluate.py` reads a
person's typed bindings and computes exactly over `Fraction`s — *"`1/3` is
one third, not 0.333…"* (`scripts/evaluate.py:24–30`) — and
`scripts/harness.py:1437–1470` routes to it, deciding a typed relation
before falling back to computing a value. Both skins reach it: the chat
skin's `_evaluate_receipt` (`scripts/serve_chat.py:763–789`) already emits
`{"expression", "exact", "grounding": "computed"}`. But the module's own rule
is that **the corpus is never consulted** (`scripts/evaluate.py:32–39`): it
computes about what you typed and claims nothing about any statement.

The **corpus** half exists and is inert. 12,777 statements carry a
`formal_statement.canonical_ascii`, and as of v0.19's transliteration lane
**8,586 of them (67.2%) parse under the committed parser** — up from 2,172
(17.0%) on two glyph equivalences
(`experiments/transliteration_rate.json` `parse_rate`,
`scripts/match_signatures.py:319`). Those statements can be quoted, matched,
rendered into English and served with receipts. **None of them can be put to
a number.**

The boundary this design moves is the one between those two halves. A
statement compiled to an evaluator lets a person type *their own* quantities
and get back a **conformance record**: which points were tested, what each
side evaluated to exactly, whether the relation held, and — the part that
matters most — **exactly what that verdict is worth.** The product ambition
this serves is the standing one: a person converses with exact knowledge and
gets receipts at wire speed. What is new is that the receipt can now be about
*their* numbers rather than only about the corpus's rows.

**What a person gains, and the single sentence that bounds it.** For the
ground statements — closed arithmetic with no free variable — the answer is a
**decision**: exact rational evaluation settles it, and the record is a
proof-shaped object. For everything else — and everything else is 96.5% of
the territory — sampling a statement at points is **falsification-only**. A
counterexample decides. **Agreement at M points certifies nothing
universally, and this design never lets the served surface pretend
otherwise.** That is not a caveat appended to the claim; it *is* the claim's
shape, and §3.4, §6 E2 and §8 are three different enforcements of the same
sentence.

## 2. Why this direction survived, and every direction that did not

### 2.1 The lineage: a dropped direction returning on new evidence

**EVAL is RUNNABLE, returned.** The v0.19 course proposed *RUNNABLE —
statements compiled to evaluators of user quantities* at series 1 round one
(`reports/design-direction-v0.19.json` `round_one_funnel.series_1`), and it
did not survive to that series' lead or runner-up. Its disposition sentence
was written by the writer of the winning design, and it named a number as the
reason:

> **RUNNABLE** (statements compiled to evaluators of user quantities):
> parked — *it needs the parseable denominator to be large, and R0 put that
> at 17.0%*; it becomes cheap the moment the foreign residue is readable…
> — `docs/DESIGN-foreign-voice.md:157–160`

**That condition was met by the same cycle that wrote it.** v0.19's
transliteration lane took the parseable denominator from 17.0% to **67.2%**
on two glyph rows, and the artifact says so in one sentence: *"8586 of 12777
statements parse (0.6720), of which 6414 are newly reached by two glyph
equivalences; 2172 parsed before"* (`experiments/transliteration_rate.json`
`parse_rate.sentence`). A park written against a measured blocker, and the
blocker measurably lifted, is the funnel working rather than a direction
sneaking back. It is recorded as such in the receipt
(`reports/design-direction-v0.20.json` `selection.lineage_note`) and again
here.

Two further facts made the return worth taking rather than merely permitted,
and both are measured rather than argued:

- **The error class an evaluator catches is invisible to every structural
  gate this repository has.** v0.19's C-V4 voided the foreign-voice gate by
  showing that *deleting a semantically redundant bracket changes the
  sentence and not the term*, and the gate cannot see the difference
  (`experiments/foreign_voice_rate.json` `c_v4`,
  `verdicts.overall = VOID`; `docs/DISCOVERIES.md:15–46`). Every gate in the
  tree adjudicates *structure* — skeletons, digests, elaborated terms.
  **None of them asks whether a statement is true of any number at all.** An
  evaluator asks a question no committed instrument asks.
- **Both cost discounts the course cited are facts, not hopes.** Exact
  rational arithmetic over parsed terms is committed and witnessed
  (`scripts/evaluate.py`); a compiled check that emits a typed verdict
  receipt with pinned inputs is committed and has a preregistered gate
  (`scripts/external_verifier.py`, `docs/DESIGN-external-verifier.md` P5).
  This design builds a third thing out of two existing ones rather than a
  first thing out of nothing.

### 2.2 The funnel, whole

Three isolated series of three constraint rounds each, under the isolation
mode the receipt records as **inherited from
`reports/design-direction-v0.19.json`, reused unchanged** (which had itself
inherited it from v0.17's): headless
`claude -p`, cwd an empty non-git directory whose path carries no project
name, strict MCP config plus a denylist over every file, shell, network,
agent and skill tool (`reports/design-direction-v0.20.json`
`enforced_isolation_mode`; the residual gap is unchanged — the tools exist
and are blocked, not absent). Cross-series exclusion was enforced inside the
hashed round-one prompts: series 2 excluded series 1's five lines, series 3
excluded all ten. **Fifteen round-one directions; three leads; one
selection.** Four collisions with prior-course or parked ground were
disclosed by the advisors themselves rather than caught by the writer
(`selection.convergence_note`).

**Selected.** *EVAL* — series 2's lead, with *NIHIL* folded into it as a
second answer type rather than a second direction ("one mechanism"). It won
on three counts the tree confirms: it makes a claim about **the user's own
inputs**, which no lane in this repository has ever made; its central failure
mode is a *finding* rather than a setback (§3.5); and its honest boundary is
sharp enough to write down before any measurement, which is the property this
project has learned to select for.

**Declined, each with its disposition** — the no-proposal-wasted rule. The
first eight are the course's own, recorded in the receipt's
`selection.declined` and reproduced faithfully; the four round-one directions
that died before their series' round two get their sentence from this
document, marked as the writer's.

*From the receipt:*

- **WORD OF HONOR** (series 3 lead — the attested layer,
  parameterize-never-unlock): **parked as the strongest thesis-level
  candidate.** Its first slice is seed-reading, which is instrument-shaped,
  and the governance record counsels against an instrument as a headline —
  the framing is the **course brief's own**
  (`reports/design-direction-v0.20-brief.txt:47–48`, *"headline drift toward
  instruments about its own evidence"*), carried into
  `docs/ROADMAP-v0.20.md` §5:291, not something ROADMAP §1 says. Its
  **extraction-discipline census is named as an optional rider any cycle can
  run** — including this one, if slack appears (§10).
- **VERDICT** (series 1 lead — entailed/contradicted/not-grounded over
  third-party claims): parked. Its **week-one warrant census** — how much
  negation and mutual-exclusivity the corpus actually carries — is named as a
  **cheap standalone probe**, and it is the probe that decides whether the
  direction has a denominator at all.
- **COURIER** (series 1 runner-up — DETACHED RECEIPT narrowed to quotation
  and evaluation classes): parked. Quotation and evaluation receipts are
  **likely near-detached already**; the probe is one day and may ride any
  cycle. It is the nearest neighbour of this design's own receipt (§3.1), and
  running both at once would make neither falsifiable.
- **DEBT NOTES** (series 3 runner-up — refusals naming their repair,
  flip-on-write replayed): parked **with the strongest product-resonance note
  on file** and its **one-day hand-classification probe** named. Natural
  companion to any future intake lane.
- **HOSTILE DICTATION** (series 2 runner-up — red-teaming the write gate):
  parked **with a named trigger: it MUST run before any untrusted stream
  reaches the write gate.** Nothing in this design opens such a stream (§4),
  and that is stated here so the trigger is not silently approached.
- **UNSAY** (withdrawal with computable blast radius over served receipts):
  parked. Blast radius over served receipts is **mechanical now that receipts
  are served objects**; revisit when withdrawal has a driver.
- **BORROWED PREMISES** (conditional answers under quarantined assumption
  sets): parked; **likely the supposition frame's maturation**, noted for
  when the API attaches callers with real premise sets. It is the closest of
  all parked directions to §3.3's guard object, and §10 names the hand-off.
- **SECOND VOICE** (diagrams that re-parse, testing void transfer): parked;
  the void-transfer question is well-formed and **waits on a committed
  picture syntax**.
- **NIHIL** (decision-procedure grounded negatives): **not declined —
  folded**, whole, as EVAL's second answer type (§3.4). One mechanism, one
  gate, one artifact.
- **ROSETTA** (certified dialect transport): **out**, on a number rather
  than a preference — 98 of 125 forks are already closed natively and the
  residual ~27 pairs do not buy a transport layer. The v0.19 convention
  census is why that number exists (`docs/DISCOVERIES.md:123–144`).
- **ONE HOP** (bounded licensed derivation with the ranker's one sanctioned
  job): surrendered by its own series to the prior course's excluded
  substitution chains; **the delete-K ground-truth table survives as a
  rider** (§10).
- **HOLES** (machine-enumerated skeleton gaps proposed and proven): folded to
  a counting-table free rider — **revive-or-close CONJECTURE FOUNDRY with a
  number** (§10). The advisors disclosed the collision with FOUNDRY
  themselves.

*Also from the receipt, in `outcomes.*.folds` rather than
`selection.declined` — recorded here so the funnel reads whole:*

- **INBOUND** (open English entering as structure): the receipt folds it into
  **the parked synonym layer plus the existing clarification loop, with the
  distractor precondition recorded** (`outcomes.series_1.folds`). The input
  side stays where DESIGN-text-resolution left it (FP floor 0.030) and where
  `docs/DESIGN-sans-template-rendering.md` §3's carve-out put it; nothing here
  moves it.
- **DETACHED RECEIPT** (offline-verifiable portable receipts, in its
  unnarrowed form): **present in the receipt as COURIER's source** —
  `outcomes.series_1.runner_up` records COURIER as *"DETACHED RECEIPT
  narrowed to quotation+evaluation classes"*, so the direction is disposed of
  by COURIER's park above rather than separately. The narrowing is the
  receipt's, not this document's.

*Written here (2026-08-24), for the one round-one direction the receipt
leaves without a disposition, and for one gloss of the writer's own:*

- **DOWNSTREAM** (a controlled claim about an attached agent's work product):
  parked. Its cheapest gate needs a population of attached agents this
  repository did not author — the same fresh-half problem the veto census and
  STRANGER both hit, and a direction whose denominator must be recruited is
  not a next cycle.
- **NIHIL's standalone form** (a register of grounded negatives at corpus
  scale): the *fold* is the receipt's (`outcomes.series_2.folds`, *"NIHIL ->
  into EVAL (one mechanism)"*, and it is recorded above); what is written here
  is only the **reason the standalone direction is not separately revivable**,
  which §6 E4 makes precise — its
  corpus reach is **three statements**, and a direction sized by its reach
  would be dishonest while a *mechanism* sized by its procedure is not. The
  mechanism ships; the corpus-scale ambition does not.

## 3. The first-class objects

Five objects. Two are records, one is a schema, one is a decision procedure,
and one is a register. The register is co-equal, on the v0.19 pattern
(`docs/DESIGN-foreign-voice.md` §3.3), and §6 E0c makes freezing it a
precondition of computing anything.

### 3.1 The compiled evaluator, and the honest denominator

> **Correction 1 (2026-08-24, grounding, before implementation): the course's
> "~12,700 decidable candidates" is off by a factor of forty-three at the
> only reading that matters.** A read-only census over `data/*/nodes.json`,
> parsing `formal_statement.canonical_ascii` with the committed
> `match_signatures.Parser` and classifying against the committed evaluator's
> actual inventory:
>
> **The walk is shape-first, and the order is stated because the buckets
> depend on it:** parse → is the top level a relation? → is it a *single*
> relation? → are all heads inside the evaluator? → are all operators and the
> relation itself decidable?
>
> ```text
> 12,777  statement nodes
>  4,191  canonical_ascii does not parse (v0.19's foreign residue)  -> out
>  8,586  parses                                       (0.6720, matches the lane)
>     10  parses but is not a top-level relation                        -> out
>      1  nested relation (a relation inside a relation's argument)      -> out
>     98  carries a call head outside the evaluator (sin, exp, sqrt, …)  -> out
>      1  top-level relation is `approx`, which the evaluator cannot decide -> out
>  8,476  evaluable-shaped  (66.3% of the corpus)
>    297    ground and closed  -> genuinely DECIDED by exact evaluation
>  8,179    carry free variables -> point-testable only, never decided
> ```
>
> **110 statements are excluded and 109 constructs explain them — the
> difference is one statement, and it is stated rather than rounded away.**
> The single nested-relation statement **also carries a call head**, so it is
> attributable to two constructs and lands in whichever bucket the walk
> reaches first. 110 is the count of excluded *statements*; 109 is the count
> excluded for exactly one reason. E3's arithmetic partitions statements, not
> constructs, so it uses 110 — and the register, which is indexed by
> construct, must therefore **not** sum its `blocking_count` fields and expect
> 110 (M-9, §6 E3).
>
> **8,476, not 12,700 — and only 297 of those are decided.** The gap between
> those two numbers is this design's entire honesty problem, and §3.4 is where
> it is written into the record's own schema rather than into a footnote.
>
> The inventory that produces the exclusions is small and is worth stating,
> because "the evaluator" sounds larger than it is. `_eval_tree`
> (`scripts/evaluate.py:151–188`) implements exactly five operators — `+`,
> `*`, `neg`, `inv`, `^` (integer exponents only, `:178–182`) — and
> `_RELATIONS` (`:193–199`) decides exactly five — `=`, `<`, `>`, `<=`, `>=`.
> The parser emits more than that: **`pm` (`±`) is a node the parser produces
> (`scripts/match_signatures.py:378–380`) and the evaluator has no rule
> for**, and three of the parser's eight relations — `approx`, `~`, `=>_d`
> (`:77`) — are not arithmetic relations at all. Every call head is out: 98
> parseable statements carry one, led by `sin` (17), `exp` (15), `cos` (13),
> `sum` (10), `concat` (9), `D` (7) and `log` (7) — and `sqrt` (2), which
> ranks **sixteenth** by count and is named here only because §3.4's NIHIL
> exemplars need it, not because it is a large blocker.

**`scripts/conform.py`** — the compiler. It takes a statement node and
produces a **conformance program**: a guard (§3.3), a conclusion, and the
free variables both range over. It calls no new arithmetic: evaluation is
`evaluate._eval_tree` and `evaluate._RELATIONS`, unchanged, so that the
thing being tested and the thing already served through
`scripts/harness.py:1437` are the *same* arithmetic rather than two
implementations that agree today.

The compiled-check precedent is the external-verifier lane, and this design
inherits its **verdict shape** deliberately: a typed record with
`schema_version`, `claim`, `checks`, `inputs`, `environment`, `verdict`,
`evidence` (`scripts/external_verifier.py:94–123`, required-field tuple at
`:525–534`), three outcomes with no fourth bucket
(`PASS`/`FAIL`/`REFUSED`, `:68–71`), and the authority sentence quoted rather
than paraphrased: *"a passing check certifies what it checks, not correctness
in general"* (`:6–7`). What it does **not** inherit is that lane's
*execution model*: `check_python_tests` runs untrusted candidate code in a
subprocess under an audit hook that is *"a DISCIPLINE boundary, not a
security boundary"* (`scripts/_verifier_sandbox.py:11–16`) and — a fact found
during this grounding and worth recording where someone will see it —
**neither of its `subprocess.run` calls passes a `timeout`**
(`scripts/external_verifier.py:425–441`, `:462–481`). Nothing in this design
runs authored code. The only executable object is a tree the committed parser
produced, walked by committed arithmetic, in-process. §4 states the one
resource bound that this nonetheless requires.

### 3.2 The conformance record

```text
conformance_record {
  statement_id,
  compiled_from,             # "formal_statement.canonical_ascii" |
                             #   "structural_signature.anonymized_template"
  domain,                    # the declared domain (§3.3) or ABSENT
  guard { conjuncts[], source_field },
  free_variables[],          # each: {name, kind, bound_value?}
                             #   kind ∈ { variable | parameter | constant }
                             #   read from slot_schema[].syntactic_category;
                             #   ONLY kind=variable is sampled (§3.2.1)
  points_tested[],           # each: {bindings, guard_held, left, right,
                             #   outcome ∈ { holds | fails | evaluation_error }}
  points_admitted,           # points that satisfied every guard conjunct
  points_rejected,           # sampled but guard-excluded; never scored
  points_errored,            # admitted, but evaluation raised (see below)
  points_sampled,            # M, the sampling budget actually spent
  sampler_seed,              # E5 derives it from the schema digest; a run
                             #   that does not RECORD it is not reproducible
  provenance {               # §3.5 clause 3 requires this stated with any
    corpus_id,               #   finding, so the record carries it rather
    epistemic_status,        #   than leaving it to a later prose sentence
    bridge,                  #   e.g. "formal-without-bridge"
  },
  verdict ∈ { DECIDED_TRUE | DECIDED_FALSE
            | NO_COUNTEREXAMPLE_FOUND | NONCONFORMANT
            | UNDECLARED_DOMAIN | REFUSED },
  certifies,                 # the literal sentence §3.4 fixes per verdict
  counterexample,            # present iff NONCONFORMANT; the exact bindings
  evaluator_digest, parser_digest, sampler_digest, domain_schema_digest,
  refusal_reason,            # closed vocabulary; present iff REFUSED
}
```

Four fields exist because a measurement forced them.

**`compiled_from` exists because of Correction 3**, below: the field the
advisor assumed *is* the statement is, for most of the territory, a fragment
of it.

**`points_admitted` and `points_rejected` are separate counts, never
summed.** A statement whose guard admits zero sampled points has a
conformance record that says nothing at all, and a design that reports
"0 counterexamples in 1,000 points" over 1,000 rejected points would be
publishing a vacuity as a result. §6 E0f/E2a put a floor under admission
directly.

**`points_errored` is the third outcome, and it exists because two is one too
few.** A point can be admitted by the guard and still fail to evaluate:
division by zero inside the conclusion (`scripts/evaluate.py:174–176`), a
non-integer exponent (`:180–181`), or — until E0's exact path lands — a
literal the parser destroyed. **An errored point is not a counterexample and
is not agreement**, and collapsing it into either is how a branch cut becomes
a corpus finding. It is counted, reported, and excluded from both numerators.
A statement whose admitted points *all* error is `REFUSED`, not
`NO_COUNTEREXAMPLE_FOUND`. This mirrors the external-verifier lane's rule that
its three outcomes admit no fourth bucket and no silent drop
(`scripts/external_verifier.py:68–71`).

**`certifies` is a literal sentence, not a flag.** It is emitted from a
closed table keyed on `verdict`, so that the sentence a reader sees is
generated by the same code path that computed the verdict and cannot drift
from it.

**`free_variables[].kind` exists because of Correction 2**, and it is the
correction that decides whether this design can touch the authored corpora at
all.

#### 3.2.1 Not every free identifier is a variable

> **Correction 2 (2026-08-24, adversarial review, before implementation): a
> sampler that treats every free identifier as a variable falsifies the
> authored core by construction.** The first draft's `free_variables[]` was a
> flat list of the tree's slots. Over `lean_workbook` that is nearly harmless;
> over the authored corpora it is fatal, and the review measured why.
>
> **Of the 52 authored free-variable candidates, 51 are `=`-relations and 1 is
> `>=`.** They are not universally quantified inequalities at all — they are
> **definitions**: `A = pi*r^2`, `V = (4/3)*pi*r^3`, `G = H - T*S`,
> `F = m*a`. One side is the quantity being defined; the other side defines
> it. Sampling both sides independently does not test such a statement, it
> refutes it — and the review's pilot did exactly that:
>
> > **binding `pi` to `9/8` falsified `geometry.volume_formulas
> > .sphere_volume_formula`, and sampling `A` independently of `s` falsified
> > `geometry.area_formulas.square_area_formula` (`A = s^2`).**
>
> Neither statement is wrong. The sampler was. **That pilot is the finding**,
> and it is recorded here rather than in a run artifact because it changed the
> design before the design was built.
>
> The data model already carries what is needed, in the field the first draft
> read past: `structural_signature.slot_schema[].syntactic_category`, whose
> values are `variable`, `parameter` and `constant`. Three rules follow, and
> they are rules rather than heuristics because each is keyed on a committed
> declaration:
>
> - **Sample only `kind = variable`.** A `parameter` is held fixed across a
>   statement's point set — `eps` in Beer–Lambert, `k` in Hooke's law — and a
>   sampler that varies it is testing a different statement.
> - **Bind `kind = constant` from the schema, never sample it.** `pi` is
>   declared a `constant` slot with a value in
>   `symbol_lexicon.constants[]` (`geometry.area_formulas.circle_area_formula`
>   declares `CONSTANT` / `geometric_constant`, value `3.14159265359`). And
>   **binding it is not sufficient either**: that declared value is a
>   twelve-digit decimal, not π, so an exact-rational equality test against it
>   is false for a second, independent reason. A statement whose constants are
>   irrational-valued approximations is `REFUSED` with **`named_constant`**,
>   not tested.
> - **Refuse definitional equalities with `defined_output`.** Where the
>   top-level relation is `=` and one side is a single slot whose declared
>   role appears in the schema's **reviewed output-role list**, the statement
>   is a definition and this cycle does not test it. The role vocabulary is
>   *not* closed in the corpus — `output` (23 rows), `area_measure`,
>   `volume_measure`, `topological_invariant` all appear — so the list is a
>   **reviewed artifact in the domain schema**, extended by diff with tests,
>   never inferred by a regex over role strings. That is review work, and
>   naming it as such is the honest alternative to guessing.
>
> **What this costs, stated plainly:** most of the 52 authored statements
> leave the tested set and enter the register. The design accepts that. A
> conformance lane that reported 51 counterexamples across twelve authored
> corpora would not be finding errors; it would be publishing its own
> misreading as a corpus finding, which is precisely the failure §3.5 exists
> to prevent — caught here by a review rather than there by a reader.

> **Correction 3 (2026-08-24, grounding): `canonical_ascii` is not the
> statement. For 6,490 of the 8,179 free-variable candidates it is the
> conclusion with the hypotheses deleted.** Take
> `leanworkbook.skel.lean_workbook_10009` (`data/lean_workbook/nodes.json`).
> Its `canonical_ascii` reads
>
> ```text
> a^3 + b^3 + c^3 + (15 * a * b * c)/4 ≥ 1/4
> ```
>
> and is false at `a = b = c = 0`. Its `structural_signature
> .anonymized_template` — and its `formal_statement.equivalent_forms
> [emitted_skeleton]`, same string — reads
>
> ```text
> IMPLIES(MEET(MEET(MEET(a >= 0, b >= 0), c >= 0), a + b + c = 1),
>         a^3 + b^3 + c^3 + 15*a*b*c/4 >= 1/4)
> ```
>
> The point that falsifies the first satisfies the second's first three
> conjuncts — `a >= 0`, `b >= 0`, `c >= 0` all **hold** at zero — and
> violates the **fourth**, `a + b + c = 1`. Which conjunct does the work
> matters: the three that hold are box constraints a sampler enters easily,
> and the one that fails is the equality that E0d shows is measure-zero.
> **A sampler pointed at `canonical_ascii` manufactures counterexamples that
> are not counterexamples**, and it would manufacture them at scale: the
> census counts **6,490 of 8,179 (79.4%)** whose template's top head is
> `IMPLIES`, all of them `lean_workbook.ground.v1`. This is the single
> correction that most changes the design — the compiled object is the
> *template*, not the ascii field, and §3.3 is the schema that says so.
>
> The good news is measured too, and it is why the direction survives the
> correction: the guards are **recoverable with machinery that already
> exists.** `MEET` is a **declared** call head with a commutativity and
> identity row (`scripts/match_signatures.py:146–167`); `IMPLIES` carries no
> row in `HEAD_ALGEBRA` and parses as an ordinary call head under the same
> grammar (`:421–424`) — which is all this design needs, since it reads the
> antecedent structurally rather than algebraically. **6,257 of the 6,490
> antecedents (96.4%) consist entirely of relations
> the committed evaluator can decide** — no call heads, no operators outside
> the five. The remaining 233 are register entries, not silent drops.
>
> **The consequent agreement, at both readings, because one of them is
> misleading alone.** The template's consequent is tree-identical to the
> parsed `canonical_ascii` in **6,405 of 6,490 — 85 differ raw**. But 83 of
> those 85 differ only in spellings `canonicalize` erases (`a - b` against
> `a + -(b)`, commutative argument order): **after canonicalization exactly 2
> differ.** Quoting 85 alone would overstate the disagreement by a factor of
> forty; quoting 2 alone would hide that the raw fields do differ and that a
> naive string comparison sees it. Both numbers travel together.
>
> **And the 2 are not what "the template is the authority" would predict.**
> Both are **decimal-precision divergences in which the template is the
> *less* precise field**: `leanworkbook.skel.lean_workbook_26545` writes
> `0.5627387450` in `canonical_ascii` and `0.562739` in the template, and
> `leanworkbook.skel.lean_workbook_plus_68586` writes `190.3676248` against
> `190.368`. The emitter rounded. So the rule is **split rather than
> blanket**: the template is the authority **for the guard**, which is the
> only place it carries information the ascii field lacks; where the
> *consequent* differs after canonicalization, **both are reported, neither is
> silently preferred, and the statement is refused with
> `numeral_beyond_exact_parse`** until a reviewer decides which literal the
> corpus meant. Two statements, named now, before the run.

### 3.3 The domain and branch-cut schema, and the register that catches its absence

> **Correction 4 (2026-08-24, grounding): a NONCONFORMANT verdict is a domain
> disagreement before it is a corpus error.** Running the committed evaluator
> over all 297 ground statements gives **287 agreements and 10
> disagreements** — a number that reads, at first glance, like ten corpus
> defects found in an afternoon. It is not. Eight of the ten are
> **statements that are true under integer semantics and false under rational
> semantics**, and the difference is one operator: Lean's `/` on `ℕ`
> truncates. `leanworkbook.ground.lean_workbook_plus_26988` states
> `2017 - (2017 / 3) = 1345`, which is exactly right over `ℕ`
> (`2017/3 = 672`) and exactly wrong over `ℚ` (`4034/3`). Adjudicated
> against the pinned toolchain v4.32.2 invoked directly by path under the
> standing hermetic rule, `by decide` over `Nat`: **8 of the 10 hold; only 2
> fail under both readings** — `leanworkbook.ground.lean_workbook_plus_16115`
> and `leanworkbook.ground.lean_workbook_plus_46623`.
>
> **The design consequence is structural, not cosmetic.** A conformance
> engine that does not carry a domain does not produce wrong answers
> occasionally; it produces a verdict whose meaning is undefined. Domain is
> therefore a **required input**, and its absence is a **refusal with a
> register entry**, never a default.

**`data/domains/domain_schema.json`** — a frozen, hand-authored, reviewed
table, carrying its own digest, on the rules v0.19's lexicon lives by
(`scripts/realization_lexicon.py:30–38`; a table that fails its load gate
raises rather than degrading). Each row declares, for a statement class or a
statement id: the **carrier** (`Nat` | `Int` | `Rat`), the **reading of
`/`** (`truncating` | `exact`), the reading of `-` (`truncated-at-zero` |
`signed`), and the **branch cuts** the evaluator must refuse rather than
choose (division by zero; `0^0`; a rational exponent, which
`scripts/evaluate.py:180–181` already refuses in the one place it can arise).

**What the data model actually carries, and what it does not** — the
ten-by-hand probe, run as an indicative preview; the registered probe in §6
E0c stands and is not replaced by this.

The authored corpora carry real domain information, in three fields:
`structural_signature.slot_schema[].syntactic_category` (`variable` |
`parameter` | `constant`) and `.semantic_role`;
`symbol_lexicon.symbols[].semantic_role`; and
`semantic_interpretation.regularity_conditions[]`. Sampled by hand:
`numbertheory.parity.even_double` carries *"Integer argument: parity is a
property of the ring of integers, not of the rationals or reals"*;
`algebra.polynomial_equations.quadratic_formula` carries *"a ≠ 0 (otherwise
not quadratic)"*; `chemistry.solutions.molarity_definition` carries *"Nonzero
volume"*; `algtop.invariants.euler_characteristic_surface` carries *"Genus is
a non-negative integer"*; `calculus.differentiation.average_rate_of_change`
carries *"Nonzero interval extent"*. These are **free English**, not a
machine-readable type — the schema above is what turns them into one, by
review, one row at a time.

**And for the statements that need it, the model carries nothing.** Over the
8,179 free-variable candidates, `regularity_conditions` is present on all of
them and is the identical boilerplate string on **8,127**;
`symbol_lexicon.symbols[].semantic_role` is the literal token
`ingested_slot` on **8,127**; and `slot_schema[].semantic_role` is
*"value in an ingested covered statement"* on **22,867 slot rows**. The
authored-core roles that carry meaning — `output` (23), `input` (11),
`state_variable` (7) — total **fewer than 100 rows across the whole
free-variable set.** The domain of `a`, `b`, `c` in
`lean_workbook_10009` is `ℝ` in the Lean source and is **not recorded
anywhere in the node**.

**So the register is not an appendix; it is where most of the territory
lands this cycle.** `experiments/conformance_register.json`, frozen and
digested **before the first verdict**, one row per blocking construct, on
v0.19's schema:

```text
register_entry {
  construct_id,        # domain_absent, division_semantics_undeclared,
                       #   guard_unevaluable, guard_measure_zero,
                       #   head_outside_evaluator, relation_undecidable,
                       #   numeral_beyond_exact_parse, operator_pm,
                       #   defined_output, named_constant,      (§3.2.1)
                       #   exponent_variable,                   (below)
                       #   evaluation_budget_exceeded           (§6 E0e)
                       # operator_pm is declared and measures ZERO (below)
  surface_witness,     # one verbatim corpus occurrence
  reason,              # closed vocabulary; why no verdict can be computed
  blocking_count,      # statements this construct alone blocks
  statement_ids[],     # the blocked set, exhaustively
}
register { entries[], blocked_set_digest, frozen_at,
           schema_digest_at_freeze, evaluator_digest_at_freeze,
           parser_digest_at_freeze, sampler_digest_at_freeze }
```

**`operator_pm` is declared and blocks nothing — measured, and said out
loud.** The parser emits a `pm` node for `±`
(`scripts/match_signatures.py:378–380`) and the evaluator has no rule for it,
so the construct is real. But the census finds **zero** evaluable-shaped
statements carrying `pm`, or indeed any operator outside the five: the
`operator_outside_evaluator` bucket is empty. The row stays in the closed
vocabulary because the grammar can produce the node and a future corpus can
carry it, and it ships with a **blocking_count of 0** rather than being
quietly omitted — a register that lists only its populated rows is a register
that cannot show you a zero. **This is also why E1's zero-refusals floor is
achievable today rather than aspirational:** all 297 ground statements
already decide under the committed evaluator with no refusals, so the floor
tests that the exact-literal path and the domain schema did not *introduce* a
refusal, which is the thing that could actually go wrong.

**`exponent_variable`** is the construct the review's typing rule makes
visible: `evaluate._eval_tree` refuses a non-integer exponent
(`scripts/evaluate.py:180–181`), so a statement whose exponent is a
**sampled variable** rather than a literal cannot be tested without the
sampler choosing which powers are legal — a semantic choice the sampler has
no authority to make. `economics.production.cobb_douglas_production_function`
(`Y = A*K^alpha*L^beta`) is the witness: `alpha` and `beta` are declared
`parameter`, not `variable`, and under §3.2.1 they are held rather than
sampled — but where such an identifier is declared `variable`, the statement
is refused with this construct rather than sampled at integer powers the
author never wrote.

**Which entry is largest, corrected.** The first draft said `domain_absent`,
and that was wrong in a way worth recording: **`domain_absent` does not apply
to `lean_workbook.ground.v1` at all.** That corpus gets a **class row** in
the domain schema — one row, covering all 12,514 nodes, declaring
`carrier: Nat`, `/`: *truncating*, `-`: *truncated-at-zero*, on the
provenance ground that these statements are restatements of Lean-workbook
problems whose source semantics Correction 4 measured directly. One reviewed
row covers 98% of the corpus, and inventing 12,514 per-statement rows to
express one fact would be bookkeeping theatre.

`domain_absent` is therefore **scoped to the authored corpora**, where the
domain genuinely varies statement by statement and where
`regularity_conditions` carries it in free English that no row yet
formalises. **The largest register entry is expected to be
`guard_measure_zero` (up to 3,476, per E0d), followed by
`head_outside_evaluator`** — and which is actually largest is E3's
arithmetic to report, not this paragraph's to predict.

### 3.4 The two answer types, and the exact shape of each claim

**Type one — CONFORMANCE.** Six verdicts, and the `certifies` sentence each
one is permitted to carry, fixed here. **Every verdict has a row**, including
the two that say nothing was computed, because a verdict without a
`certifies` sentence is the one a reader will fill in themselves:

| verdict | when | `certifies`, verbatim |
|---|---|---|
| `DECIDED_TRUE` | closed statement, declared domain, relation holds | *"decided exactly under the declared domain; no sampling was involved"* |
| `DECIDED_FALSE` | closed statement, declared domain, relation fails | *"decided exactly under the declared domain; this is a disagreement between the statement and the declared domain, not yet a claim about either"* |
| `NONCONFORMANT` | a point satisfying every guard at which the conclusion fails | *"a counterexample was found and is printed; a counterexample decides. The domain under which it was found was declared by this repository — see the adjudication field"* |
| `NO_COUNTEREXAMPLE_FOUND` | M sampled, N admitted, none falsifying | *"tested at N admitted points and not falsified; **this certifies nothing universally** and is not evidence the statement is true"* |
| `UNDECLARED_DOMAIN` | C-E3 disagreed, or the schema covers no row for this statement | *"no domain was established for this statement, so no verdict about it is claimed; this is not a finding about the statement"* |
| `REFUSED` | any register construct applies | *"nothing was computed, and the named construct says why; a refusal is not a negative result about the statement"* |

The last two rows exist because the first draft had neither, and a record
that emits `REFUSED` with an empty `certifies` invites exactly the reading
those two sentences forbid — that the system tried and the statement lost.

That fourth row is the design's central honesty boundary and the reason the
field is called `NO_COUNTEREXAMPLE_FOUND` rather than anything with the word
*conforms* in it. **Most lean_workbook statements are universally quantified
inequalities** — the census puts the top-level relation at `>=` for 4,982 and
`<=` for 1,694 of the 8,179, with `=` at 1,145 — and point-sampling tests
them without deciding them. The asymmetry is total: one falsifying point
settles the statement; a million agreeing points settle nothing. Every place
that number can be seen carries the sentence with it, on the rule v0.19's B1
lives by (`docs/DESIGN-foreign-voice.md` §8).

**Type two — NIHIL, a decided non-existence.** A pinned decision procedure
over a fixed class, returning a **decided negative** rather than a failure to
find. The first procedure is the **rational-root test over integer-coefficient
univariate polynomials**: the candidate set is finite, every candidate is
evaluated exactly, and the record is the enumeration. Its exemplar is in the
corpus — `numbertheory.irrationality.sqrt_two_irrational` states
`irrational(sqrt(2))`, and `x^2 - 2 = 0` has no rational root because ±1 and
±2 all fail. The second is a **parity argument** over the same class of
ground statements the evaluator already decides.

```text
nihil_record {
  class_id,            # rational_root_univariate | parity
  instance,            # the term the procedure was run on
  procedure_digest,    # the committed decision procedure's digest
  candidates_enumerated, candidates_refuted,   # exhaustive, printed
  verdict ∈ { NO_SUCH_OBJECT | EXISTS(witness) | OUT_OF_CLASS },
  certifies,           # a CLOSED TABLE keyed on verdict, exactly as §3.2's is
}
```

> **Correction 5 (2026-08-24, grounding): NIHIL's gate certifies the
> procedure, and it must, because its corpus reach is three statements.** A
> sweep of the tree for non-existence and irrationality claims returns
> `numbertheory.irrationality.sqrt_two_irrational`,
> `numbertheory.irrationality.sqrt_prime_irrational`, and
> `leanworkbook.skel.lean_workbook_49423` (`Irrational (Real.sqrt 2)`).
> **All three carry `sqrt` or `Real.sqrt`, which is a call head outside the
> evaluator, so none of the three is compiled by this cycle's machinery.**
> The advisor's framing — a decided non-existence answer *type* — survives
> whole; the temptation to size it by corpus coverage does not. E4 therefore
> scores the procedure over a **constructed** class with committed instances,
> and **no sentence in the release quotes a NIHIL corpus coverage number**,
> because the honest one is zero.

### 3.5 The finding-of-findings clause, written before one is found

**A NONCONFORMANT verdict on a committed statement is a corpus error that no
structural gate in this repository could have seen.** Every gate the tree
carries adjudicates structure: skeleton equality, round-trip identity,
elaborated-term digests. A statement can pass all of them and be false. If
this cycle finds one, that is the strongest result available to it — and
exactly for that reason, **its handling is written now, before the run,
rather than composed in the excitement of finding one.**

1. **The verdict is provisional until the domain is independently
   adjudicated.** Correction 4 is the reason: 8 of 10 apparent errors were
   domain disagreements. **Every** NONCONFORMANT verdict carries the
   correlated-interpretation label — not only those whose domain row looks
   suspect — because **every** domain row in this cycle was authored by this
   repository, and a label applied conditionally would imply that the
   unlabelled ones had an independent domain when none of them does. The
   label is discharged per counterexample by C-E3 (§7) or it stands; a
   NONCONFORMANT verdict is **not published as a corpus error** while it
   stands.
2. **The corpus is not edited by the run.** The counterexample lands in the
   run artifact and in `docs/DISCOVERIES.md`; the statement node is
   untouched by the measuring commit. Repair, if any, is a separate,
   later, reviewed commit citing the artifact — the same separation v0.19
   used when it refused to re-score C-V4 (`docs/ROADMAP-v0.20.md`:44–50).
3. **The provenance is stated with the finding.** All 12,514
   `lean_workbook.ground.v1` nodes are `formal-without-bridge` by
   ROADMAP-v0.10's decision (b) — *"the Lean-workbook proof is not re-checked
   under this repo's hermetic core-Lean budget; `epistemic_status` formal
   records provenance, not a certificate"* (node invariant, verbatim). A
   counterexample against such a node is a defect **in the restatement or in
   the declared domain**, and the release says which of the two it is or says
   it does not know.
4. **Zero is a result and gets the same paragraph.** If the registered run
   finds no counterexample anywhere, that is published as the reading, with
   its denominator and its admitted-point counts — not quietly dropped for
   being undramatic.

**Disclosed here, because the census already ran:** the ground-class sweep
above found 10 disagreements, of which 8 are domain-attributable and 2
(`lean_workbook_plus_16115`, `lean_workbook_plus_46623`) fail under `ℕ` as
well. Those two are **named now, before the registered run**, so that
finding them again cannot be presented as a discovery the gate made. The
registered run re-measures them under the frozen schema, and the gate's real
subject is the 4,470 statements the census did **not** reach.

## 4. Trusted and untrusted

**Trusted:** the committed corpus statements; the **byte-frozen parser**
`scripts/match_signatures.py` and its `canonicalize`, which this design pins
because Correction 3's whole apparatus reads a second field through it;
`scripts/evaluate.py`'s arithmetic, which is committed, tested, witnessed and
already served; the **domain schema** once committed — a first-class,
reviewed artifact with its own digest, extended only by a diff with tests;
the pinned Lean toolchain (v4.32.2) and its containment rules
(`scripts/proof_artifacts.py:14–48`).

**Untrusted and measured:** the compiler `conform.py` (E1, E2); the
**sampler** (C-E1, and E2's admission floor exists because a sampler that
cannot enter a guard region measures nothing); the *sufficiency* of the
domain schema (C-E3 — the only instrument that bounds it); every served
verdict (a statement whose domain is absent, whose guard is unevaluable, or
whose head is outside the inventory **refuses at the surface** with a
register entry, the honest degradation v0.18 and v0.19 both ship); and the
register's own completeness (E3's arithmetic).

**The user's input is untrusted, and one bound follows from that** — found
during this grounding and stated here rather than discovered at runtime. A
person's bindings enter as `Fraction`s (`scripts/evaluate.py:56–58, 83–88`)
and are then fed to `^`, which computes `base ** int(exponent)` with **no
size bound** (`:178–182`). `(100 + 1) ^ 1000` already evaluates in this tree,
which is the point: the operation is exact and therefore unbounded. That path
is live today through `scripts/harness.py:1813` and reachable through the
chat skin (`scripts/serve_chat.py:763–789`), and this design **widens what
reaches it**. It is BACKLOG-filed as a known issue whose standing mitigation
is the skin's loopback-only, single-owner bind
(`scripts/serve_chat.py:104–106`); E0e's bound and typed refusal are owed by
ROADMAP-v0.20 §4's batched witness item (§5). It is a robustness bound, not a
security claim, and it is not presented as one.

**The authority boundary, imported verbatim.**
`scripts/external_verifier.py:6–7`: *"a passing check certifies what it
checks, not correctness in general."* Here that means precisely: a
conformance record certifies **that the committed arithmetic, over the
declared domain, produced these values at these points.** It certifies
nothing about the statement's truth in general, nothing about whether the
declared domain is the one the statement's author meant, and — for every
`NO_COUNTEREXAMPLE_FOUND` — nothing at all beyond the points printed.
`:35–40` governs the output: **a verdict alone never mints a `verified_by`
link, and this cycle mints none.**

**No untrusted stream reaches the write gate.** Conformance records are
artifacts and served lines; nothing here proposes a node, and HOSTILE
DICTATION's named trigger (§2.2) is therefore not approached by this design.
Stated so that a later slice cannot approach it by accident.

## 5. Smallest slice

- **E0's exact-numeral path first** (§6), because every number below is
  otherwise measured in floating point.
- **`data/domains/domain_schema.json`**, committed with its digest, before
  the compiler exists (E7's ordering), with its head coverage stated in the
  file the way v0.18's lexicon states it, and the refusal path exercised **by
  injection rather than accident**.
- **`experiments/conformance_register.json`**, frozen and digested before the
  first verdict (E0c).
- **`scripts/conform.py`** — compiler, guard recovery, sampler, the two
  record types, tests.
- **One registered run**, `experiments/conformance_run.json`, carrying E0's
  tables, E1's ground decision with every disagreement listed exhaustively,
  E2's admitted-point and falsification tables **with their denominators in
  the same sentence**, E3's arithmetic, E4's NIHIL certification, and every
  control's reading including C-E2's guard-blind arm.
- **Wire ONE new route**, `_route_conform` in `scripts/harness.py`, beside
  the existing `_route_evaluate` (`:1437–1470`) and following its shape
  exactly: return `None` on a refusal so the line *"falls through to the rest
  of the chain rather than refusing on everyone else's behalf"* (`:1439–1443`).
  Both skins inherit it through A-IH6; the capability sheet gains a
  `conformance` row read from the run artifact rather than from a number
  pasted into code, exactly as `scripts/serve_chat.py:355–395` does for
  realization — **but what it quotes is the `certifies` sentence, not a
  rate.** A sheet row reading `conformance: 0.98` would be the single most
  misleading object this design could ship, because the number it invites a
  reader to form is the universal claim §3.4 spends its whole length
  refusing. The row carries the verdict *vocabulary*, the denominators, and
  the sentence; if the artifact is missing it publishes `served: false` with
  the reason, on the existing precedent. No new HTTP surface.
- **No new line in `answer.render`.** A conformance verdict is about the
  asker's numbers, not about the statement's record, and putting it under
  `formally` would make a reference entry claim something it does not claim.
  The `in words` precedent (`scripts/answer.py:210–215`) is the shape a
  future *statement-level* line would take if one is ever justified; this
  cycle does not take it.
- **Seal bookkeeping: ONE retirement for the cycle, and this slice does not
  own it.** `scripts/harness.py`, `scripts/evaluate.py` and
  `scripts/answer.py` are three of the eleven witnessed
  `rendering_module_digests` (`tests/test_throughput_tasks.py:52–66`;
  `experiments/throughput_tasks.json:83–95`). Adding `_route_conform` changes
  `harness.py`'s rendered bytes, and so does E0's exact-numeral path and
  E0e's bound wherever they land — under
  `docs/SPEC-chat-completions-skin.md:252–258` each such change would retire
  the current witness and seal a successor book.

  **The orchestrator's ruling is that the cycle pays that cost once.** All
  witnessed-module work in v0.20 is **batched into ROADMAP-v0.20 §4's already
  scheduled re-seal** — one retirement, one dated reason naming every change
  it covers, one successor book, the prior artifact untouched. A cycle that
  retires the same witness three times for three items produces a book whose
  reason nobody can read, which is the outcome the standing rule exists to
  prevent.

  **This design's own requirement, stated here rather than assumed: §4 lands
  before this slice.** §4 is scheduled early in ROADMAP-v0.20 for its own
  reasons; this slice **depends** on that ordering, because its route, its
  exact-numeral path and its resource bound all ride §4's retirement rather
  than opening one. If §4 slips, this slice slips with it or ships without
  touching a witnessed module — and which of the two is chosen is written
  down, not improvised.

- **The two live defects are BACKLOG-filed known issues, not this design's
  stop conditions.** Correction 6's float literals
  (`match_signatures.py:411–412`) and §4's unbounded exponent
  (`evaluate.py:178–182`) are **pre-existing defects in witnessed modules that
  this design found and did not create.** They are filed in
  `docs/BACKLOG.md` as known issues with their mitigation stated — the HTTP
  skin is **loopback-only, one owner, no auth**, not a flag
  (`scripts/serve_chat.py:104–106`, `HOST = "127.0.0.1"`) — so the exponent
  defect's blast radius is a local operator's own session, and the literal
  defect affects three named nodes. **Their repairs are discharged by §4's
  batched item**, which is why E0 and E0e below are prerequisites *of that
  item* rather than independent stop conditions of this one. A design that
  turned two inherited defects into its own stop conditions would be able to
  fail for reasons that have nothing to do with whether its idea works.
- **Release obligations, named here rather than discovered at the gate.**
  `check_report_regeneration.py` runs in the release refresh with its
  verdicts in the notes; the full suite is green on a **frozen tip** with
  retained receipts; every unfinished item ships or parks in writing.

## 6. Construction gate

> **Gate history (2026-08-24).** The course's gate for EVAL was framed over
> "~12,700 decidable statements". Correction 1 falsified that denominator
> before implementation — the real figure is 8,476 evaluable-shaped, of which
> 297 are decided — and Correction 3 then showed that the *object* being
> counted was the wrong field for 79.4% of the remainder. **Both retirements
> are recorded rather than quietly re-scoped**, because a gate must be
> retired on the numbers it would actually have been read against. The gates
> below are rebuilt around the things that can now fail. **Four of them —
> E0, E0c, E0e and E0f — are construction prerequisites rather than frozen
> floors**, and two of those (E0, E0e) are discharged by ROADMAP-v0.20 §4's
> batched witness item rather than by this slice (§5). The R0 lesson
> (`docs/DESIGN-sans-template-rendering.md` §6) is that a number frozen
> without justification is how a gate becomes a wish, and none of the four can
> be given a defensible floor before the thing it names exists. The adversarial
> review of this document's first draft removed one such number — a 90% that
> had nothing under it — and E0f is what replaced it.

- **E0 — exact numerals, a construction prerequisite discharged before any
  floor freezes.**

  > **Correction 6 (2026-08-24, grounding): the exactness claim fails at the
  > parser's numeral.** The advisor's premise was that the corpus's exact
  > rationals make bounds computable exactly. The corpus's rationals are
  > exact; **the parser's are not.** `Parser.parse_atom` stores
  > `("num", float(tok))` (`scripts/match_signatures.py:411–412`), and
  > `evaluate._eval_tree` recovers a `Fraction` from that double
  > (`scripts/evaluate.py:152–153`). **The walk, stated so the denominator can
  > be reproduced:** every `formal_statement.canonical_ascii` in
  > `data/*/nodes.json`, **parsed or not**, scanned by the numeral pattern —
  > 12,777 nodes, **82,636 numeric literals**. (The parseable-only walk gives
  > 54,351, and quoting *that* denominator here would be wrong: one of the
  > three affected nodes,
  > `leanworkbook.skel.lean_workbook_50397`, **does not parse**, so a
  > parseable-only denominator would exclude a node the numerator counts.)
  > Of the 82,636, **7 literals in 3 nodes are destroyed**: 6 lose
  > precision and 1 overflows to `inf` (that same node). Two of those are in the
  > 297-statement ground class, and both currently return the **right verdict
  > with the wrong values** — `leanworkbook.ground.lean_workbook_37421`
  > evaluates both sides to `-4444444444444444000000…`, off by roughly 10⁶⁰
  > from the literal the corpus wrote, and the relation holds only because
  > the same rounding was applied twice. A conformance record prints `left`
  > and `right`. **Printing a number that is not the number, under a heading
  > that says "exact", is the failure this project exists to refuse.**

  E0 publishes the exact-literal census (the three ids named) and delivers an
  **exact literal path** — the term carries the literal's source text, or the
  evaluator reads it from the source span — with a test asserting exact
  round-trip on all three. **E0 is discharged by ROADMAP-v0.20 §4's batched
  witness item, not by this slice, and it is not a stop condition of this
  design** (§5). The defect is pre-existing, BACKLOG-filed and inherited; what
  this design owes is the census that found it and the requirement that **no
  conformance record prints a `left` or `right` value until the exact path is
  in place.** Until then the record emits `evaluation_error` rather than a
  number, which is E3's third outcome and not a silent rounding.

- **E0b — the guard-recovery table, published before E2 freezes.** Per corpus
  and per field, the partition of the 8,476 evaluable-shaped statements into
  ground / guarded-and-recoverable / guarded-but-unevaluable / unguarded.
  **Floor: ≥ 5,000 statements must compile to a guard-plus-conclusion program
  under the frozen schema**, or the direction has no territory and the cycle
  stops with the table as its finding. **This floor is a disclosed formality
  and is labelled one here rather than left to look like a risk**: the preview
  in the same bullet is 8,243, so the floor sits 39% below a number already
  measured. It is kept because a floor the run could in principle miss —
  if the frozen schema or the typing rule of §3.2.1 excludes far more than
  expected — is worth more than no floor, and because retiring it silently
  after seeing the preview is the drift this section exists to prevent.
  *(Preview, indicative — E0b remains the registered measurement: 297 ground;
  6,490 guarded of which **6,257** fully evaluable and 233 not; 1,689
  unguarded — 1,637 `lean_workbook.ground.v1` and 52 across twelve authored
  corpora. Total compiling: **8,243**.)*

- **E0c — the domain schema, a construction prerequisite, frozen before any
  verdict.** The schema exists, loads under its own gate, and covers every
  statement the run will attempt. **No floor is frozen on its coverage**,
  because the honest measurement is how *little* it covers: the register is
  the artifact. What is gated is the ordering — a verdict computed before the
  schema's digest is committed is void — and the refusal, which is E3's
  business. **E0c also publishes E2's denominator**, which is *not* the whole
  samplable set but **the samplable set intersected with schema coverage**:
  `4,470 ∩ schema-covered`, stated as a number in the artifact before E2 is
  read, so that a rate can never be quoted against a denominator the schema
  had not actually reached.

- **E0d — the samplable denominator, unpreviewed in its consequences and the
  real probe.** This is where the direction can quietly become vacuous, and
  the mechanism is arithmetic rather than engineering: **an equality
  constraint is measure-zero under sampling.** Of the 6,257 recoverable
  guards, **3,476 (55.6%) carry an equality conjunct** — `a + b + c = 1` and
  its kin — which naive rejection sampling will satisfy essentially never.
  The remaining **2,781 are inequality-only**, and **2,061 of those are box
  constraints alone** (`slot REL num`, e.g. `0 < a`), directly samplable per
  variable; the other 720 couple variables and need rejection.
  **The samplable denominator is therefore 1,689 + 2,781 = 4,470.** The 297
  ground statements are **not** in it: they are decided by E1 and carry no
  free variable to sample, and adding them would inflate the sampling
  denominator with statements no sampler ever touches. E0d publishes that
  partition before E2 is read.
  *(Named successor, previewed only to size it honestly: of the 3,476
  equality-guarded, 2,567 carry exactly one equality conjunct and **1,117**
  of those have a variable solvable by a single additive rearrangement. A
  one-equation solve would reach them. It is **not** in this slice — it is a
  solver, it changes what the sampler is, and it belongs to its own
  registration.)*

- **E0e — the resource bound, discharged by the same batched item.** Exact
  arithmetic over user-supplied exponents is unbounded (§4), and that is a
  **pre-existing defect on a path that is already live**, mitigated today only
  by the skin's loopback-only bind (`scripts/serve_chat.py:104–106`). A
  committed bound on exponent magnitude and total evaluation work, with a
  **typed refusal** in the closed vocabulary and a test that injects the
  overflowing case, is **owed by ROADMAP-v0.20 §4's batched witness item**
  (§5) and is a prerequisite of *that* item, not a stop condition of this
  design. What this design owes is the refusal vocabulary — a bound the
  compiler hits emits `REFUSED` with `evaluation_budget_exceeded`, never a
  truncated answer — and the ordering requirement that §4 lands first.

- **E1 — the ground class is decided, exhaustively.** All 297 ground
  statements produce `DECIDED_TRUE` or `DECIDED_FALSE` under the frozen
  schema and the exact literal path. **Floor: zero refusals in the ground
  class** — a closed arithmetic statement with a declared domain that the
  evaluator cannot decide is a hole in the inventory, not a data point. Every
  `DECIDED_FALSE` is listed exhaustively with both exact values (LOST = 0
  discipline), and each is routed through §3.5's clause before it is named
  anything.

- **E0f — the admission pilot, an E0-series construction prerequisite
  published before E2 freezes.** The first draft of this design froze an
  admission floor at 90%. **That number had nothing under it** — the sampler
  did not exist, and 2,061 of the 2,781 inequality-only guards are box
  constraints that will admit trivially while the other **720 couple their
  variables** (`a >= 2*b`, `0 < a` together) and are the only ones whose
  admission rate is in genuine doubt. A floor set at 90% over a set that is
  74% trivial is a floor calibrated by the easy majority.

  E0f therefore **measures before it freezes**: run the committed sampler at
  M = 1,000 over **the 720 coupled guards**, publish the admission
  distribution, and only then freeze E2a's floor in a dated amendment to this
  design. Both branches yield an artifact. If coupled-guard admission is high,
  E2a's floor is set over the whole samplable set with the pilot as its
  justification; if it is low, the coupled set is reported separately and E2's
  denominator narrows to what the sampler actually reaches — which is a
  finding about these guards, not a failure of the cycle.

- **E2 — the falsification claim, and its two clauses.** Over E0c's
  denominator, with **M = 1,000 sampled points per statement** frozen here:
  - **E2a — admission.** A statement that admits zero points gets `REFUSED`
    with `guard_measure_zero`, never `NO_COUNTEREXAMPLE_FOUND`. **Its floor
    is frozen by E0f's amendment and is deliberately absent from this
    document**, because the R0 lesson is that a number frozen without
    justification is how a gate becomes a wish, and this is the one number in
    the design that cannot be justified before the sampler runs.

    > **E0f's amendment (2026-08-25, after the pilot, before E2 was read).**
    > The pilot ran the committed sampler at M = 1,000 over the **691**
    > coupled guards this tree carries — the design predicted 720; the
    > difference is Correction 2's typing rule, applied before the guard
    > partition, and it is reconciled in `experiments/conformance_prereg.json`.
    > Artifact: `experiments/conformance_admission_pilot.json`.
    >
    > **Measured: 591 of 691 coupled guards (85.5%) admit at least one point.
    > Mean admission rate 3.4%, median 1.2%, best 435 of 1,000.**
    >
    > **E2a's floor is therefore frozen at: ≥ 80% of the samplable-and-
    > schema-covered set must admit at least one point at M = 1,000.**
    > Justified by the pilot rather than by preference: 80% sits 5.5 points
    > below a number measured on the HARDEST slice, and the rest of the
    > samplable set is box constraints and unguarded statements that admit
    > more easily. **It is labelled a disclosed formality on E0b's model** —
    > a floor the run could in principle miss is worth more than no floor,
    > and retiring it silently after seeing the preview is the drift §6
    > exists to prevent.
    >
    > **The floor is on the SHARE OF STATEMENTS ADMITTING, not on the
    > admission rate**, and that choice is the pilot's doing. A median rate of
    > 1.2% would make a rate-floor either vacuous or arbitrary, while the
    > condition E2a actually cares about is whether a statement admits
    > *anything* — because a statement admitting nothing must be `REFUSED`
    > with `guard_measure_zero` rather than reported as not-falsified.
    >
    > **A finding the pilot produced that the design did not ask for, recorded
    > because it bounds what M means.** Of the 691,000 candidates offered,
    > **539,382 (78%) were rejected by the declared CARRIER and only 51,791 by
    > the guards.** The sampler draws from a rational pool with negatives; the
    > `lean_workbook` class row declares `Nat`. So most of M is spent on
    > candidates the schema excludes before any guard is consulted, and the
    > effective budget per statement is far below 1,000. The two gates are
    > reported separately in the artifact for exactly this reason — summing
    > them would have hidden which one did the work. **A carrier-matched
    > sampler is a named successor**, not a fix applied mid-cycle: changing
    > the sampler now would edit an E7-frozen artifact after its pilot had
    > been read.
  - **E2b — the sentence, not a rate.** Every reported figure travels with
    its admitted-point denominator and its `certifies` sentence in the **same
    sentence**. **There is no floor on the counterexample rate, and freezing
    one would be incoherent**: a low rate means the corpus is sound and a
    high rate means it is not, and both are results. Freezing a floor here
    would be pre-committing to a preferred finding.

- **E3 — verdict or register, and the arithmetic closes.**

  ```text
  ground_decided                 (E1)
  + samplable_no_counterexample  (E2)
  + samplable_nonconformant      (E2)
  + undeclared_domain            (C-E3 downgrades, and schema misses)
  + refused_domain_absent        (register; authored corpora only)
  + refused_guard_unevaluable    (register)
  + refused_guard_measure_zero   (register)
  + refused_typed_slot           (register; defined_output, named_constant,
                                  exponent_variable — §3.2.1)
  + refused_head_or_relation     (register)
  + not_evaluable_shaped         (4,191 unparseable + 110 excluded = 4,301)
  = 12,777  exactly
  ```

  **This partitions statements, and every statement lands in exactly one
  bucket.** The register does not: it is indexed by *construct*, and one
  statement can carry two blocking constructs (M-2's nested-relation case is
  the measured instance). **So the register's `blocking_count` fields are
  never summed and never reconciled against this arithmetic** — the first
  draft implied they could be, and that would have double-counted. The
  register reports, per construct, how many statements that construct alone
  blocks; this table reports where each statement went. Two questions, two
  objects, and the artifact says which is which.

  The `refused_*` buckets are **reported separately and never summed into one
  "unsupported" number** — v0.19's rule, whose reason it restates: some are
  consequences a maintainer can lift by authoring schema rows and some are
  consequences this design owns, and merging them hides which is which. Any
  statement in none of those buckets is a bug in the census, not a rounding
  difference.

- **E4 — NIHIL certifies its procedure.** Over a **committed constructed
  class** of ≥ 100 integer-coefficient univariate polynomials, half with a
  rational root and half without, the procedure returns
  `EXISTS(witness)` / `NO_SUCH_OBJECT` **correctly on every committed
  instance** — the instance list is frozen in the preregistration commit and
  the floor is *all of it*, whatever its size, because "100 of 100" over a
  class declared as "≥ 100" is a floor that cannot be checked — with
  every candidate enumeration printed. `OUT_OF_CLASS` is returned — not
  guessed — for every instance outside the class, measured by injection.
  **No corpus-coverage number is quoted for NIHIL** (Correction 5).

- **E5 — determinism.** Same statement, same schema, same sampler seed →
  byte-identical conformance record; two full runs on one tree produce
  byte-identical artifacts (precedent:
  `tests/test_measure_realization.py:259`,
  `test_two_runs_are_byte_identical`). The sampler's seed is derived from
  the schema digest by a committed rule, so the point set is a function of
  committed artifacts rather than of a wall clock.

- **E6 — no learned component.** Nothing in the compiler, the guard recovery,
  the sampler, the domain schema or the decision procedures is learned. §9
  states what would have to be true for that to change, and it is not true
  this cycle.

- **E7 — the compiler is not the arithmetic, and the parser is not either.**
  Recorded in the preregistration commit, **before** `conform.py` is written:
  the digests of `scripts/match_signatures.py`, `scripts/evaluate.py`, the
  domain schema, and the sampler. *If making a conformance verdict come out
  right requires editing the parser, the arithmetic, or the schema, the
  independence claim is void and the change needs its own review naming the
  reason.*

## 7. Blind controls, each with its voiding sentence

- **C-E1 — the perturbation control, with C-V4′'s discard clause ported
  first.** The transferable lesson from v0.19 is explicit and this control
  obeys it before it does anything else: *"when a control is ported, port its
  discard rule first — the discard rule is usually the part that was
  expensive to learn and the part that looks optional"*
  (`docs/DISCOVERIES.md:48–72`). C-V4 inherited C-R2's mutation idea and left
  behind the clause that made it sound, and `drop_group`'s 0.80 was scored
  against a denominator that had never been cleaned
  (`docs/ROADMAP-v0.20.md`:40–50).

  So: construct each mutation on the **term**; **canonicalize the mutated
  term and discard any mutation whose canonical skeleton did not change**;
  **count the discards**; only then compile and sample. v0.18 discarded 31
  that way and the reason it had to was itself a finding — `a < b` and
  `b < a` share a skeleton. Five classes: negate a coefficient; perturb a
  numeric literal; flip a relation; drop a summand; reassociate one operator.
  Each surviving mutation is sampled over the **same admitted point set** as
  its source.

  **Floor: ≥ 99% of skeleton-changing mutations must flip at least one point
  verdict.** *If fewer than 99% flip, the sampler is not testing the term and
  every `NO_COUNTEREXAMPLE_FOUND` in the run is void.* Second arm, and it is
  the false-alarm half: **0 of N unmutated statements may change verdict
  across two runs.** *If any does, E5 has failed and the reading is void.*
  **One-sided by construction**, on C-R1's measured lesson: the mutation is
  applied to the term and read by the **committed** evaluator, never by a
  mutated one, because a consistently mutated pair is a renaming and
  round-trips for a reason that has nothing to do with what the gate reads
  (`docs/DISCOVERIES.md:214–239`).

- **C-E2 — the guard-blind arm: the capability-blind baseline, and a positive
  control that must fail.** This is **this design's cheapest capability-blind
  baseline**, named as such rather than left implicit: it is the same sampler
  with the one capability under test — hypothesis recovery — removed, and
  nothing else changed. Run it over `canonical_ascii` **alone**, hypotheses
  discarded, and count the counterexamples it manufactures. This control
  exists to prove Correction 3 in public, and it is the only instrument that
  can show the guard apparatus is load-bearing rather than decorative.

  **Scored only where the guarded arm can be scored**, which the first draft
  got wrong by pointing it at all 6,490. A statement whose guard admits zero
  points has no guarded rate to compare against, so including it would make
  the contrast a division by a vacuum. **The comparison set is the
  inequality-only guarded statements whose guarded arm admitted ≥ 1 point —
  at most 2,781, and exactly what E0f/E2a report** — and both arms run over
  the **identical admitted point set**, on C-E1's discipline, so that the two
  numbers differ by the guard and by nothing else.

  **The 3,476 measure-zero equality-guarded statements are reported as a
  separate, explicitly non-informative row.** Their guard-blind arm will
  produce counterexamples in abundance and their guarded arm will produce
  nothing at all, and a ratio computed across that pair would look
  spectacular while measuring only that one arm never ran. Naming the row
  non-informative in the artifact is the alternative to letting it inflate
  the contrast.

  *The control is informative only if the guard-blind arm's counterexample
  rate on the comparison set is ≥ 10× the guarded arm's; if the two rates are
  within 10×, the guard is doing no work, the recovery apparatus is
  decoration, and the reading is void.* A second baseline is reported beside
  it at near-zero cost — **a trivial always-conforms arm**, which emits
  `NO_COUNTEREXAMPLE_FOUND` for every statement without evaluating anything.
  *If the true sampler's counterexample count does not exceed the
  always-conforms arm's (which is zero by construction), the run found
  nothing and no conformance claim is made.* It is a floor, not a contender,
  and it exists so that "we found no counterexamples" can never be reported
  without the arm that also finds none sitting next to it.

- **C-E3 — the independent interpretation, and the residual it exists to
  price.** The course recorded EVAL's residual as **correlated
  interpretation**, and Correction 4 gave it a face: this repository writes
  both the domain schema and the evaluator, so a NONCONFORMANT verdict may be
  scoring the schema rather than the corpus. The mitigation is an authority
  this repository already trusts and did not build.

  **What is adjudicated is the instantiated counterexample, not the
  statement.** This is the fix that makes the control reach the sampled set
  at all: a universally quantified statement cannot be handed to `decide`,
  but **a counterexample is a closed proposition.** Substitute the record's
  exact bindings into the conclusion, emit the resulting ground proposition,
  and settle it with `by decide` under the declared carrier on the **pinned
  Lean toolchain v4.32.2**, invoked directly by path under the standing
  hermetic rule (no lake, no Mathlib, no network). So the control covers
  **every `DECIDED_FALSE` from E1 *and* every `NONCONFORMANT` from E2** —
  where the first draft could only reach the 297 ground statements, this
  reaches every counterexample the cycle produces, which is the set the
  finding-of-findings clause actually cares about.

  *If the independent adjudicator disagrees with the evaluator on any
  instantiated counterexample whose carrier the schema declares, the schema is
  wrong: every NONCONFORMANT verdict in the run is downgraded to
  `UNDECLARED_DOMAIN`, no corpus-error claim is published, and the schema is
  re-registered with its own new run.*

  > **Correction 7 (2026-08-24, grounding): the independent adjudicator
  > reaches `Nat` and `Int` and does not reach `Rat`.** Verified against the
  > installed pinned binary. Over `Nat`, `by decide` settles all ten
  > ground disagreements and reports two of them false — the probe works, and
  > it is what produced Correction 4. Over `Rat`, `by decide` **does not
  > reduce**: core Lean's `instDecidableEqRat` gets stuck without Mathlib's
  > `norm_num`, and Mathlib is outside the hermetic budget as design law
  > (`docs/DESIGN-external-verifier.md:40`). **So C-E3 reaches counterexamples
  > over `Nat` and `Int` — which is the whole of the `lean_workbook` class row
  > and where every measured disagreement lives — and does not reach `Rat` or
  > `ℝ`.** Where it cannot run, the honest non-claim applies instead and is
  > stated in the artifact **per counterexample**: *"no independent
  > adjudication was available for this carrier; the verdict is this
  > repository's arithmetic under this repository's schema."* A design that
  > silently let the reachable half stand for the whole would be doing the
  > thing this control was added to prevent.

- **C-E4 — the tautology probe.** Parser, evaluator, schema and sampler are
  digest-frozen in the preregistration commit before `conform.py` exists
  (E7), and the run revalidates them the way
  `measure_throughput.revalidate_rendering_digests` does
  (`scripts/measure_throughput.py:1076–1090`). *If implementing the compiler
  requires changing any of the four, the independence claim is void and the
  change needs its own review naming the reason.*

## 8. Stop conditions and non-claims

**Stop and publish** if **E0b** compiles fewer than 5,000 statements; if
**E0f's pilot** cannot be run at all, or if **E2a** misses the floor E0f's
amendment freezes (the guards are tighter than sampling can reach — a real
finding about what these statements are, publish the distribution and stop);
if **ROADMAP-v0.20 §4's batched witness item does not land**, in which case
this slice ships without touching a witnessed module or parks in writing
(§5) — note that **E0 and E0e are prerequisites of §4's item and are
explicitly *not* stop conditions of this design**, because two inherited
defects should not be able to stop an idea that did not cause them; if the
**domain schema fails its load gate** (a
schema that will not load is not a thing to work around); if **E5's two runs
diverge** — the sampler is then not a function and no verdict means anything;
or if any post-freeze register or schema edit is chased **after** E1 or E2
has been read. In every case: publish the reading and stop, with no
"exploratory" relabeling.

**Non-claims, stated hard.**

- **Agreement is not proof, and this is the claim's shape rather than a
  caveat.** `NO_COUNTEREXAMPLE_FOUND` certifies nothing universally. No
  sentence in the release, the blog, the capability sheet or a served answer
  pairs a conformance figure with the word *verified*, *proved*, *holds*, or
  *conforms* without the printed point count beside it.
- **No interval bounds — Correction 8 (2026-08-24, grounding): the advisor's
  premise for them is retired.** The
  course's final form named "agreement bounds" over exact rationals. There is
  **no interval arithmetic in this tree** — `_eval_tree` has five operators
  and one scalar type — and Correction 6 showed the exactness premise fails
  at the parser's numeral before any bound could be computed. Interval
  certification is a **named successor**, not a quiet omission, and the
  `conformance_record` schema carries no `bounds` field, so that nothing can
  half-implement one.
- **No decision for the 8,179.** A universally quantified inequality is not
  decided by this cycle at any point count. The 297 ground statements are
  decided; nothing else is.
- **This is a `lean_workbook` denominator, and after Correction 2 it is
  almost purely one.** Of the 8,243 compiling statements, 8,191 are
  `lean_workbook.ground.v1` and **52 come from twelve authored corpora** — and
  of those 52, **51 are definitional `=`-relations that §3.2.1 refuses** with
  `defined_output` or `named_constant`, leaving **one** (`difftop.morse
  .weak_morse_inequality`, the single `>=`) as a candidate. So the tested set
  is, to within one statement, one corpus. Every authored statement is
  **reported individually and never averaged** (the thin-denominator rule),
  and no sentence describes this cycle as having tested "the corpus". A figure
  that reads that way when one corpus is 99.99% of its denominator is the kind
  of sentence this project retracts later.
- **No corpus-coverage number for NIHIL.** Correction 5: the honest figure is
  three statements, none of them compilable this cycle. The procedure is
  certified; the reach is not claimed.
- **No `verified_by` links and no epistemic-ladder movement.**
  `scripts/external_verifier.py:6–7` and `:35–40` govern, unweakened. A
  conformance record is not a proof artifact and never enters
  `prover/verifier-verdicts/`.
- **No throughput claim.** This slice touches a seal-witnessed module
  (`harness.py`), so any future timed comparison starts a fresh seal cycle
  (§5's bookkeeping note). The cost ledger stays parked and stays owed, for a
  fifth rotation.
- **No open-English input.** Bindings are read by the committed
  `BINDING` regex (`scripts/evaluate.py:56–58`) — a name, an equals sign and
  a literal number, *"nothing that could itself need evaluating, so a binding
  can never smuggle in a computation."* The input side stays where
  DESIGN-text-resolution left it.
- **The declared domain is a declaration, not a discovery.** Where the
  schema reads a statement over `Nat` that its Lean source wrote over `ℝ`,
  the record says so in its `domain` field and every sentence quoting a rate
  names it. A rate measured under a substituted domain that does not say so
  is a number pretending to be a fact — v0.19's sentence, applying unchanged.

### 8.1 Habits deliberately suspended this cycle

The house checklist asks that a design name the standing habits it is *not*
following, so that a reader does not read an omission as an oversight. Four:

- **A new capability does not get an `answer.render` line.** The habit since
  v0.18 is that a new engine capability surfaces as a line under `formally`.
  Suspended here on the reasoning in §5: a conformance verdict is about the
  asker's numbers, and a reference entry that carried one would be claiming
  something about the statement that no verdict in §3.4 supports.
- **This slice does not seal its own witness book.** The habit is that a
  rendering-adjacent change retires the witness and seals a successor.
  Suspended by the orchestrator's batching ruling (§5): **one retirement for
  the cycle**, owned by ROADMAP-v0.20 §4, with this design's ordering
  requirement stated instead.
- **One gate number is deliberately absent from this document.** The habit is
  that §6 freezes every floor before implementation. E2a's admission floor is
  not frozen here; E0f measures it first and a dated amendment freezes it
  (§6). The R0 lesson is the authority, and the alternative — a plausible 90
  with nothing under it — is what the first draft did.
- **The capability sheet does not quote a rate.** The habit, set by the
  `realization` row, is that the sheet quotes the registered run's headline
  number. Suspended because this lane's headline number does not mean what a
  rate appears to mean; the sheet quotes the `certifies` sentence instead
  (§5).

## 9. The learned seat (closed this cycle, in writing)

E6 forbids a learned component anywhere in this design's path, and the reason
is specific rather than doctrinal. The only place a ranker could sit is
**choosing which points to test** — and a learned sampler is precisely the
component that could make `NO_COUNTEREXAMPLE_FOUND` mean less than it says,
by learning to avoid the region where a statement fails. That is the
difference between refusing and answering wearing a different hat, and the
standing rule forbids it. The seat stays closed here even behind the tool
admission bar.

The one seat that could honestly open later is **ranking which of several
admitted point sets to *show* a person** once the verdict is already
computed — an ordering over evidence the gate has already produced, never an
input to the gate. It is named so that a future cycle proposing it has a
sentence to argue against rather than a blank. v0.18's realization ranker seat
is unaffected and stays where it is.

## 10. How status lands

**This design is ROADMAP-v0.20 §1**, and it does not displace anything below
it there. §2's C-V4′ re-specification and the foreign wiring gated behind it,
§3's grouping-canonical probe, and §4's `_route_ownership` landing are all
owed by v0.19's own readouts and stand unchanged. **§4 is scheduled early and
this design's §5 depends on that ordering** — §4 retires the current witness
first, and this slice retires the book §4 seals.

**Preregistration order:** **ROADMAP-v0.20 §4's batched witness item first**,
carrying E0's exact literal path (its three named test cases) and E0e's
resource bound, and paying the cycle's one witness retirement (§5); then this
design; then the domain schema with its `lean_workbook` class row and its
reviewed output-role list, plus the frozen digests of parser, evaluator and
sampler (E7); then the **frozen register** with its `blocked_set_digest`
(E0c, which also publishes E2's `4,470 ∩ schema-covered` denominator); then
`conform.py` + records + tests; then **E0f's admission pilot over the 720
coupled guards, and the dated amendment that freezes E2a**; then the one
registered run, `experiments/conformance_run.json`,
carrying E0b, E0d, E0f, E1, E2 **with denominators**, E3's ten-bucket
arithmetic, E4, and every control's reading including C-E2's guard-blind arm
and C-E3's per-statement availability. Fires, misses and voids land together
in ROADMAP-v0.20, `experiments/ANALYSIS.md`, `docs/DISCOVERIES.md` and
`docs/BACKLOG.md`; the v0.20 blog's forward section follows from this
document.

**Riders accepted by the course, carried here** (`selection.declined
.riders_accepted`) — each is an afternoon, and each commits its result
whichever way it lands:

- **The HOLES counting table.** Enumerate the skeleton gaps the ledgers
  already imply and publish the count, so that **CONJECTURE FOUNDRY is
  revived or closed with a number** rather than carried a fourth time. The
  advisors disclosed the collision themselves.
- **The delete-K ground-truth table**, surviving ONE HOP's surrender: for K
  deleted statements, whether the remaining graph licenses their recovery.

**Probes named by the course as cheap and standalone, filed rather than
scheduled** — recorded here because a named probe that appears in no document
is a park that will fade: VERDICT's **week-one warrant census** (how much
negation and mutual-exclusivity the corpus carries — the probe that decides
whether that direction has a denominator); COURIER's **one-day
near-detachment probe** over quotation and evaluation receipts; DEBT NOTES'
**one-day hand-classification probe**; and WORD OF HONOR's
**extraction-discipline census**, an optional rider any cycle may run.

**Carried and unchanged by this selection:** every row of ROADMAP-v0.20 §5,
including the register's `mathlib_head` budget (1,706 statements blocked by a
budget a maintainer can lift), licensed variant generation, ledger-first
claims with its unpark rule intact, the cost ledger — **fifth rotation, still
owed, still without a metrology any cycle has designed** — open-English
input, STRANGER, TWO RIGHTS' empty mathematical denominator, and
DESIGN-block-vocabulary's completed park.

**The course gate.** `reports/design-direction-v0.20.json`, with
`reports/design-direction-v0.20-brief.txt` beside it and pinned by hash, is
the receipt that discharges ROADMAP-v0.19's course clause — the forge skill
**invoked**, not reaffirmed, for the second strict cycle in a row. The brief
carried the void, the park and the negative alongside the 67.2%, per
ROADMAP-v0.20 §1's requirement that a brief carrying only the flattering
readout would be describing a different cycle.

**If E1 and E2 read out, the questions that become askable next:** the
**one-equation solve** that would reach the 1,117 equality-guarded statements
E0d sizes and names; **interval certification**, which needs the exact
literal path E0 builds and would turn `NO_COUNTEREXAMPLE_FOUND` into
something with a bound under it — the first honest route this project has to
a universal claim over a continuum; and **BORROWED PREMISES**, which is the
same guard object seen from the asker's side rather than the statement's, and
whose park (§2.2) is written so that this hand-off is the natural one.
