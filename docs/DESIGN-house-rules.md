# House rules: the person declares a symbol, and the system decides on the record

**Status: IMPLEMENTED AND MEASURED through H-P1, on a superseding second
registered run (2026-09-02).** Selected by the v0.25 course, reworked after
adversarial review falsified its first draft (below), scheduled by
`docs/ROADMAP-v0.25.md` §1. Course receipt:
[`reports/design-direction-v0.25.json`](../reports/design-direction-v0.25.json);
the dialect-free brief is committed beside it. This document does not
displace any parked lane or the STRANGER-GATE prohibition — the slice opens
no execution, no durable write, and no untrusted stream toward the write
gate.

**The construction, in order, with its commits.**

| stage | commit | what landed |
| --- | --- | --- |
| H-PRE | `7a47a8a` | the fixture seal, before any checker existed |
| H-P0 | `c87b0ca` | the census, `scripts/symbol_ledger.py`, the `declare` row, and every pin the row moves |
| H-P0-FIX | `e3e3980` | the clause-order discriminator sealed; corpus amendment 1, B9 re-anchored PRE-RUN |
| CR-P0 | `11d62b8` | the cold reading re-attests the H-P0 registry |
| H-P1-FREEZE | `27d358d` | `experiments/house_rules_prereg.json`, the runner, the second program, 100 tests |
| H-P1 (run 1) | `2ac8c9f` | the first registered run — **SUPERSEDED**, retained at `experiments/superseded/` |
| H-P1-FIX-FREEZE | this change | the review's fixes, five dated prereg amendments, the run-1 retirement |
| H-P1-RUN2 | the commit adding `experiments/house_rules_verdicts.json` | the superseding registered run |

**Run 1 was reviewed and superseded, and that is part of this design's
record.** An independent adversarial review reproduced every number in run 1
and returned MERGE AFTER FIXES. Its findings were not arithmetic: B3 executes
no mutant and never said so; two of B3's detectors could not fail; B9's
control family was unregistered and structurally unable to fire on this
corpus; and the served `declare` grammar example carried an ADMITTED fixture
symbol — b3-m08's own vector — through H-P0 and through run 1, while B3
scored that mutant STOPPED. All four are repaired or disclosed at
H-P1-FIX-FREEZE, the preregistration carries five dated `amd-2026-09-02-*`
amendments recording that every one of them was authored AFTER run 1's score
and loosens nothing, and run 1's artifacts are kept with a README saying what
they are and are not evidence of. The measured readout is in
`experiments/ANALYSIS.md`; three findings are in `docs/DISCOVERIES.md`.

**The review that forced the rework is part of this design's record.** The
first draft claimed the declaration would enter as an owned frame whose
premises were anonymized-template axioms, demoted on exit by the shipped
machinery. All three legs were false of the code: `frames.close_frame`
REFUSES owned frames ("owned belief frames persist and update; they do not
demote on exit", `scripts/frames.py:1052-1057`), `FrameSpec.declarations`
holds subject-predicate-value `Literal`s that cannot represent an arity-3
application, and the shipped template grammar
(`scripts/match_signatures.py:420-520`) parses a bare applied term or one
infix comparison — no connectives, no binders, no relational axiom. That
tripped the draft's own stop-before-implementation clause. This rework
sheds frames and premises entirely rather than pricing new machinery as
"reuse."

## 1. The boundary and the person it serves

A person can already *suppose* a claim: `suppose x = 5` declares a
session-scoped assumption through `AssumptionSet.declare`
(`scripts/session_ledger.py:454`), capped at 8, superseded by subject,
cited by read barrier, and consumed by `evaluate` through `_live_bindings`
(`scripts/harness.py:1512`). A supposition that is not a binding is held
as an **opaque atom**: `suppose parent(alice, bob)` stores normalized
text. The system cannot tell a well-formed use of the person's own
vocabulary from a typo, because the person has no way to tell the system
what their vocabulary *is*. The v0.23 census recorded the adjacent
coverage wall exactly: **0 of 21** non-exhaust inbound questions landed in
the 2,313-id renderable covered set
(`experiments/guest_hypotheses.json`, `recast_yield`,
`nameless_because_no_unique_covered_id: 21`). That is a
rendering-coverage fact, not a vocabulary-gap measurement — the pilot
question's subject exists in three corpora the voice cannot speak — and
this design does not cite it as demand for declarations. The demand claim
here is deliberately weaker and structural: the person's side of the
conversation has vocabulary the program never authored, and today every
use of it is opaque.

The boundary moves when this narrower claim becomes recordable:

> Given this declaration line, the system either admitted a fresh relation
> symbol — name, arity, argument categories — into a session-scoped symbol
> ledger, or refused it with exactly one deciding clause, totally and by
> default toward refusal; and from that turn on, a supposition applying
> the declared symbol is checked against the declaration exactly, with
> misuse refused by name instead of held as opaque text. Nothing declared
> reaches a generated library file or survives the session.

One verdict kind ships: **ADMITTED_DECLARED_SYMBOL**. Axioms about
declared symbols, conservativity, export, persistence, and truth are all
refused in writing by the same total function. The axiom question is
real and is deliberately the *next* askable question (§10): expressing
`parent(x,y) and parent(y,z) => grandparent(x,z)` needs a premise grammar
the shipped template parser does not have, and pricing that extension
belongs to a slice that has a corpus of real declarations to price it
against.

## 2. Why this direction survived

The course ran three isolated three-round series (fifteen round-one
directions, receipt on file). Six of the fifteen independently reinvented
parked or carried ground and were recorded as convergent evidence rather
than lanes: assumption-necessity by ablation (→ PREMISE LEDGER, with the
countermodel *constructor* noted as what the incumbent still lacks),
witnessed-no countermodels (→ the same incumbent's mechanism, second
arrival), portable certificates (→ the cold-census/ORPHAN successor, with
a ≤500-line stdlib-only verifier shape recorded), the obstruction map (→
the v0.21 ATLAS park), a second independent generator (→ the two-witnesses
park, third arrival), and pre-committed cost bounds (→ TOLL, with the
deciding log-probe named). ERRAND additionally re-arrived at the parked
execution outline and survived its series only as CHOKE — a second
independent arrival at STRANGER-GATE's own shape, hardening that park.
The series leads:

1. **STRANGER** — provisioned outside judges audit the authored move
   vocabulary. Declined as headline: its own round-three residual risk
   caps the claim at agreement-inside-one-model-lineage, and an
   instrument-first headline repeats the drift the v0.17 redirect
   corrected. Its provisioning pattern is retained by name for any later
   outside-judge or unrehearsed-input arm.
2. **DIMENSION** — dimensioned quantities with outward-rounded enclosures.
   Declined as headline: a discipline upgrade on an already-exact path
   moves the person-facing boundary least. Parked as a strong rider
   candidate with its degenerate-family risk recorded.
3. **HOUSE RULES** — selected, then cut down by review from
   "quarantined axiom" to "checked declaration" (the preamble above). It changes what a
   person can *do* on the program's goal axis and it reuses substance
   that actually exists: the supposition ledger's declaration discipline,
   the registered line grammar, and the committed schema's category
   vocabulary.

Runner-up of the selected series: **MIRROR FRAGMENT** — an exact-grammar
English reader provably disjoint from the renderer's module closure. It is
the highest-ceiling decline and parks as the named successor to the
plain-input lane behind its own pre-gate (≥300 renderable entries each
carrying ≥2 content lemmas outside the nine boilerplate glossary words,
and ≥40 distinct content lemmas overall).

Imported bounded lessons: from DIMENSION, the honesty sentence that these
checks certify **ledger-groundedness, never correspondence** — an admitted
declaration is well-formed and fresh, never true or useful. From STRANGER,
the corpus-of-a-different-speech-act risk is promoted from residual to a
handled construction fact (§6). From the series-3 survivor EARNED ASK
(rank 3, not taken): if the admissibility path ever mints a question, it
must carry a partition witness, and precondition failure returns the
ambiguity rather than a fallback question — recorded as a constraint on
any future ASK arm; this slice mints no questions.

## 3. The first-class objects

Two records, both session-scoped, produced by a new module —
`scripts/symbol_ledger.py`, named here as **new trusted code**, built in
`AssumptionSet`'s discipline (cap, supersession refusal, refusal names,
read-barrier-style citation) but not pretending to be it.

```text
PersonSymbolDeclaration {
  schema                     # corollary.person-symbol-declaration/1
  decl_id                    # canonical digest of the record, decl_id empty
  session_id
  turn_index
  source_line                # verbatim bytes after the command word
  symbol_name                # normalized: NFC, casefold, [a-z][a-z0-9_]*
  arity                      # integer >= 1
  argument_categories[]      # length == arity; each from the schema's
                             # 9-member symbolToken syntactic_category
                             # enum (schema/equation-node.schema.json:
                             # 479-491). These are the schema's slot-role
                             # categories, not a domain-of-individuals
                             # sort theory, and the design says so: the
                             # check they buy is exact role agreement
                             # between declaration and use, nothing more.
}

AdmissibilityVerdict {
  schema                     # corollary.admissibility-verdict/1
  verdict_id
  decl_id
  verdict                    # ADMITTED_DECLARED_SYMBOL | REFUSED
  refusal_code               # COLLIDES_WITH_LIBRARY_SYMBOL |
                             # RESERVED_PREFIX |
                             # COLLIDES_WITH_SESSION_NAME |
                             # REDEFINITION_ATTEMPT |
                             # CATEGORY_NOT_IN_SCHEMA |
                             # ARITY_CATEGORY_MISMATCH |
                             # SYMBOL_BUDGET | UNPARSED | NONE
  deciding_clause            # exactly one clause id; the clause
                             # evaluation ORDER is committed in the
                             # checker and quoted in the prereg:
                             # UNPARSED, ARITY_CATEGORY_MISMATCH,
                             # CATEGORY_NOT_IN_SCHEMA, RESERVED_PREFIX,
                             # COLLIDES_WITH_LIBRARY_SYMBOL,
                             # REDEFINITION_ATTEMPT,
                             # COLLIDES_WITH_SESSION_NAME, SYMBOL_BUDGET
                             # — first hit decides, which is what makes
                             # "exactly one" true rather than asserted
  schema_digest              # sha256_lf of schema/equation-node.schema.json
  census_ref                 # path + sha256_lf of the COMMITTED symbol
                             # census artifact the collision check ran
                             # against (§4)
}
```

A use-side check rides the existing supposition route, changing no
grammar: when a supposition's atom parses as an applied term
`name(arg, ...)` whose casefolded head is a **declared** session symbol,
the use is checked against the declaration — wrong argument count refuses
`USE_ARITY_MISMATCH`, and the refusal names the declaration.
`USE_ARITY_MISMATCH` is **not** a third record and not an
`AdmissibilityVerdict` code: it is a new refusal name in the supposition
ledger's existing refusal vocabulary (the `assumption_budget` /
`unknown_assumption` family, `scripts/session_ledger.py:120-122`),
carried where those already are. An applied
atom whose head is *not* declared takes today's opaque-atom path
byte-unchanged — no new refusal, no behavior change, which is the
regression fence. (Argument-category checking on uses is deliberately not
claimed: a supposition argument is surface text with no category evidence,
and inventing one would be the imputation this repository refuses. The
declaration's categories are checked at declaration time against the
schema enum, and they buy exact declaration-vs-declaration supersession
identity; use-side category checking waits for a slice with typed
arguments.)

**Non-persistence is a lifetime fact plus a gate, not a codec accident.**
The symbol ledger is runtime session state in the protocol-stack precedent
(owned by its module, beside session state); neither record type is
registered in `session_state._TYPES`, so `encode` refuses them — but the
review is right that the codec is not the fence, because a symbol could in
principle ride a registered type. The fence is B5: no written session
document, journal, or durable artifact contains an admitted symbol name,
checked over the run's full output tree.

The budget is a declared bound in the supposition ledger's style: at most
**4** admitted symbols per session (`LIVE_ASSUMPTION_CAP` is 8;
declarations are heavier objects; the bound is declared, not measured).
The fifth is `SYMBOL_BUDGET`, refused before any ledger mutation.

## 4. The collision census — the namespace that can actually collide

There is no global symbol table, and the first draft's four-name census
was falsified by review: the namespace a fresh `[a-z][a-z0-9_]*` head can
collide with is not the relational operator glyphs, it is the **call-head
and lexicon vocabulary**, including one live silent-capture hazard — the
shipped template parser rewrites any identifier starting with
`sum_ / prod_ / lim_ / max_ / min_` into a corpus aggregate head
(`match_signatures.py`, the big-op branch, with `HEAD_ALIASES`), so
`sum_total(x)` would be silently reinterpreted as `aggregate` with no
refusal. *(Status, 2026-09-01: the ROADMAP-v0.25 §2 lane shipped ahead of
H-P0 as total disclosure — commit `156e94f` records every big-op capture,
`sum_i` as loudly as `sum_total`, in the term's own `parse_rewrites`
receipt with all 12,777 committed trees unmoved; the branch lives in
`Parser.parse_atom` at `match_signatures.py:541-563`. The census prefix guard
below is still owed here at H-P0, and B12 remains the standing detector.)*

A committed artifact, `experiments/symbol_census.json`, generated by a
committed builder at H-P0 and re-generated by its checker, holds the
census as data: the union of

- all **five** `symbol_lexicon` categories across the merged graph
  (`symbols`, `operators`, `functionals`, `constants`, `index_sets`;
  today 221 + 40 + 95 + 37 + 12 distinct members, of which the
  name-shaped subset is what the comparison can reach — operator glyphs
  like `±` cannot collide with a `[a-z][a-z0-9_]*` name and are carried
  as members without pretending they guard anything),
- **the leading identifier extracted from every functional notation** —
  `rank(·)` contributes `rank`, `closure(·)` contributes `closure` —
  because the notation string itself can never equal a declared name and
  review found `rank` and `closure` covered by no other source,
- every call head extracted from every committed
  `anonymized_template`,
- `HEAD_ALIASES` keys and targets, `COMMUTATIVE_CALL_HEADS`, and the
  parser's reserved big-op prefixes (`BIG_OP_PREFIXES`) as a **prefix
  guard**: a declared name *starting with* a reserved prefix refuses
  `RESERVED_PREFIX`, because equality cannot see a rewrite that happens
  at tokenization,

with one normalization rule on both sides: NFC + casefold before
comparison (the supposition path's existing `.lower()` is equivalent on
the declared alphabet, and the rule says so rather than stating two).
Corpus heads are uppercase — `GCD` — and a declared `gcd` colliding with
it is the point, not an accident. `COLLIDES_WITH_SESSION_NAME` unions the
session's admitted symbols, the supposition ledger's binding subjects
(`AssumptionSet.bound_names()`), and the **applied-term heads** of live
non-binding suppositions where one parses — the whole-atom subject
(`parent(alice, bob)`) can never equal a declared name, so the head
(`parent`) is what enters the comparison.

## 5. Trusted and untrusted

**Trusted, exact code — new, and named as new:** `scripts/symbol_ledger.py`
(the ledger, the admissibility checker with its committed clause order,
the use-side arity check); the census builder and its checker.
**Trusted, exact code — reused:** the template parser's atom production
(`parse_atom`/`parse_args` — the same code the reserved-prefix rewrite
lives in, which is exactly why the prefix guard is a census member) for
applied-atom detection; the line-grammar dispatch; the supposition ledger it stands
beside; the schema's category enum; `write_stage.working_tree_digest` as
the write fence (`durable_digest` covers `data/` only and its own
docstring names the `scripts/` escape; the gate uses the wider digest and
keeps the narrow one as a named control, the `guest_quarantine.py`
framing).

**Untrusted or unvouched:** the person's declaration line; every *use* of
a declared symbol (a checked use is well-formed, never true — it remains a
supposition with the supposition ledger's existing evidence status);
whether the person's categories mean what the schema's categories mean.

No learned component sits anywhere on the admission path — enforced by an
import-closure assertion in the `echo_population_audit.import_closure`
pattern (`DESIGN-echo.md` §3), which is the mechanism the first draft
miscited. No declaration opens `WRITE`, process creation, filesystem,
shell, or network authority. The capability is scoped to the **CLI
harness session**: the served Responses skin replays every request into a
fresh session (¶DEV-1), so session vocabulary cannot exist across HTTP
turns there; the capability sheet publishes the row with that note, the
way the `retract` row already publishes its own ¶DEV-1 limitation.

## 6. Preregistration and construction order

The v0.23 census corpus cannot be this design's denominator: its 30
hypotheses are questions recorded before declaration existed as a speech
act, and the only honest corpus of declaration requests is the one this
capability creates. The two jobs the first draft asked of one corpus are
split:

1. **H-PRE — fixture seal.** Commit `experiments/house_rules_fixtures.json`
   generated by a committed builder: authored declaration and use lines
   that (a) exercise the admitted path at least **8** times, across at
   least 3 distinct arities and 4 distinct categories; (b) fire each of
   the eight refusal codes at least once; and (c) include the B3 mutant
   set. The 8/3/4 floors and B3's ≥30, B7's 6-of-8, and B9's ten-point
   margin below are all **declared construction bounds, not
   measurements**. Because the per-session cap is 4 and the admitted
   floor is 8, the fixture corpus necessarily spans multiple sessions,
   and `SYMBOL_BUDGET`'s fixture is a fifth declaration inside one of
   them — stated here so the corpus shape is sealed, not improvised. A
   refusal code no grammatical fixture can fire is deleted here,
   U-PRE-style — and two of the first draft's codes are **already
   deleted by this rule at design time**: `UNBOUND_VARIABLE` (no
   premises means no variables to bind) and
   `REQUIRES_CONSERVATIVITY_VERDICT` (no clause could fire it;
   conservativity is refused as out-of-scope by `UNPARSED`'s grammar,
   not by a dead code). Fixtures are construction fixtures; they license
   no population claim about what people will declare.
2. **H-P0 — census, checker, grammar row, and named pin movements.**
   Commit `experiments/symbol_census.json` + builder + checker; the
   ledger module; the `declare` production — a `harness.route_line`
   branch and `serve_chat.LINE_GRAMMAR` row (`declare <name>/<arity>
   (<category>, ...)`, route `declaration`, statuses `held`/`refused`)
   — and, in the same change, every pin the row moves:
   `line_grammar_digest` consumers, the position-indexed
   `experiments/session_p1_command_bound.json` regenerated via
   `scripts/measure_command_bound.py --check` (an inserted row shifts
   every later class index; the `retract` precedent recorded exactly
   this cost), the CR-P0 registry-census re-seal, and the generated
   capability-sheet row. `declare` is disclosed against prior art: the
   shipped `define X` row is a WordNet gloss lookup (the word, not the
   act), and `suppose` is the discipline precedent (the cap, the
   supersession, the refusal names), not the object.
3. **H-P1 — the registered run.** Replay the fixture corpus through the
   committed checker on a clean tree (the v0.24 gates-runner's
   dirty/wrong-tip refusal pattern). The run's declared output paths —
   the complete B4 exclusion list, fixed here — are exactly two:
   `experiments/house_rules_verdicts.json` and
   `experiments/house_rules_receipts.json`. As a separate **reported arm
   with no threshold**, run the 30 sealed census hypotheses through the
   declaration parser and report how many parse as declarations at all
   (expected ~0; any that do are found demand, quoted verbatim). That
   number cannot pass or fail the slice.

## 7. Construction gates

- **B1 — totality and one deciding clause.** Over the sealed fixtures
  AND a machine-enumerated input sweep (every fixture line mutated by
  single-token deletion/substitution from the fixture alphabet — an
  enumerated set, not an authored one): 100% receive exactly one verdict
  with exactly one `deciding_clause`, zero fall-throughs. Exclusivity is
  the committed clause order doing its job on inputs the author did not
  pick.
- **B2 — freshness against the committed census.** Zero admissions
  collide with any member of the committed `symbol_census.json` (the
  checker compares against the committed artifact; the census *checker*,
  a separate invocation, proves the artifact matches a fresh
  recomputation — two sides, two programs, so a mismatch can actually go
  red). The `sum_total` fixture must refuse `RESERVED_PREFIX`; a fixture
  head equal to a casefolded corpus call head must refuse
  `COLLIDES_WITH_LIBRARY_SYMBOL`.
- **B3 — containment.** ≥30 seeded mutants attempt to move an admitted
  symbol into a rendered answer's evidence, a written session document, a
  journal, or a library path. 100% are stopped by the shipped machinery
  or the checker — not by test assertions reading the mutant's name. One
  survivor fails the slice.
- **B4 — write prohibition, wide.** `write_stage.working_tree_digest` is
  byte-identical before and after the full registered run (excluding the
  run's own declared output paths, named in the prereg);
  `durable_digest` over `data/` is the narrow named control. Zero stage
  records exist.
- **B5 — non-persistence.** No written session document, journal, or
  durable artifact from the run contains any admitted fixture symbol
  name (swept over the run's full output tree); `session_state.encode`
  refuses both record types; a fresh session's use of an admitted
  fixture symbol takes the opaque-atom path (the declaration is gone).
  The verdict travels with its scope: this evidences *no writes observed
  under this harness*, never *cannot write* — the standing
  SURVIVES-with-scope rule from the v0.24 deep triage applies here too.
- **B6 — the use-side check is live and fenced.** Every fixture use of a
  declared symbol with wrong arity refuses `USE_ARITY_MISMATCH` naming
  the declaration; every fixture use of an *undeclared* applied atom
  produces byte-identical behavior to the same line on a tip without
  this slice (the regression fence, checked by replaying those lines
  against both code paths).
- **B7 — vacuity, adversarial.** Separate from H-PRE's authored corpus:
  the machine-enumerated B1 sweep must hit at least 6 of the 8 refusal
  codes without any sweep input having been authored toward a code; a
  code reachable only by hand-crafted fixtures is reported by name in
  the artifact. All-admitted or all-UNPARSED on the sweep is BLOCKED
  CONSTRUCTION.
- **B8 — corruption.** Remove one member from a copy of the census: the
  fixture admission that member blocked must flip to admitted (the
  freshness verdict moves). Remove one category from a copy of the
  schema enum: every fixture declaration citing that category must flip
  to `CATEGORY_NOT_IN_SCHEMA`. Both mutations name their target fixture
  in the prereg.
- **B9 — the blind control.** A surface-only admitter (token count, line
  length, presence of the command word; no census, no schema, no ledger)
  is fitted on a **held-out half** of the fixture corpus and scored on
  the other half, on the 2-valued verdict. The threshold is anchored to
  the scored half's majority-class rate, with a declared ten-point
  margin (a bound, not a measurement). Because the fixture corpus is
  self-authored, that majority-class rate is a number the author
  influences: the class balance is **sealed at H-PRE and reported beside
  the agreement figure**, so the void condition is not tunable after the
  fact. **Voiding sentence, frozen:**
  *if the surface-only admitter's out-of-half agreement with the checker
  exceeds the scored half's majority-class rate by more than ten points,
  the verdict is separable from every ledger and schema input, the
  capability is void, and the slice ships as an honest negative.*
- **B10 — freezing.** Fixtures, mutants, census, budget, and digests
  commit before the checker runs them; the run artifact cites the sealed
  commit; a dirty or wrong-tip tree refuses.
- **B11 — no learned path.** The import-closure assertion over the
  checker and ledger, in the `echo_population_audit` pattern.
- **B12 — round-trip identity (added by the post-triage refinement round,
  2026-08-31).** The census and the sweep test *refusal*; this gate tests
  that an *admitted* name survives parsing unchanged: for every admitted
  fixture symbol, declare then use, and assert the surface the use-side
  checker resolves is byte-identical to the ledger key. Mutants for this
  gate are seeded specifically at reserved-prefix-adjacent names. The
  ordered parser fix (the `sum_total` lane) is necessary but not
  sufficient — without this gate there is no standing detector for the
  regression, only a one-time fix.

## 8. Result gates and licensed sentences

- **R-H1** (B1–B11 green): *"A person can declare a fresh relation symbol
  with arity and argument categories; the system admits it into a
  session-scoped ledger or refuses with one deciding clause, totally; a
  misused declared symbol is refused by name where yesterday it was
  opaque text; and nothing declared survives the session or touches the
  library."*
- **R-H2 — the demand census, reported regardless:** the count of the 30
  sealed inbound hypotheses that parse as declarations, any nonzero rows
  quoted verbatim. No threshold; no claim. **The reading is pre-committed
  here, before any run:** approximately zero is the expected result and is
  neither a failure (the capability never claimed to serve those
  questions) nor evidence of demand — the number may not be read either
  way after the fact.
- **R-H3 — negative.** Any failed construction gate B1-B8/B10/B11 or a
  fired B9 licenses the bounded negative with its verdict table; it does
  not license loosening a clause after the score.

No gate licenses: axioms or premises about declared symbols;
conservativity; truth or usefulness of any declaration; use-side
*category* checking; natural-language declaration; persistence; export
toward library files; any behavior on the served HTTP profiles beyond
the published ¶DEV-1 note; or any claim about what people will declare
once they can.

## 9. Stop conditions and the suspended habit

Stop before implementation if the declaration form cannot express the
sealed fixtures inside the registered grammar without parser exceptions.
Stop after construction on any B3/B4/B5/B6 instance, any fall-through, or
the B9 voiding sentence. A refusal-heavy fixture design is not failure; a
checker that cannot be made total is.

Suspended habit, scoped and dated: for this slice only, the rule that
"session vocabulary is program-authored" is suspended for exactly one
symbol kind — first-order relation symbols with schema-category-annotated
argument slots — at session scope, in a ledger, without axioms. Nothing
else about the vocabulary discipline moves.

## 10. Where status lands

- **ROADMAP-v0.25:** links this design as the course's selected
  direction; the roadmap's own adjudication schedules or parks it against
  the incumbent queue (STRANGER-GATE's prohibition is untouched by this
  slice and is not displaced by it).
- **ANALYSIS:** receives H-P1's fixture numbers and the R-H2 census.
  **Delivered** — `experiments/ANALYSIS.md`, the run-2 section, carrying the
  twelve-gate table, B9's registered and richer-family numbers, R-H2 0/30
  with its precommitted reading, and B5's scope sentence.
- **DISCOVERIES:** only measured surprises — a fired B9, a nonzero R-H2,
  and the review's `sum_total` silent-capture find is already parked
  there-shaped: a reserved-prefix rewrite with no refusal is a live
  hazard of the shipped parser that this design converts into a named
  refusal. **Delivered** — three rows dated 2026-09-02: B3's
  described-not-executed finding and what a containment gate must be next
  time; B9's control-strength finding on a nineteen-row scored half; and the
  grammar-example leak the review found in the committed tree. None of the
  three is a surprise about the capability; all three are surprises about the
  instruments, which is the kind this slice produced.
- **BACKLOG:** carries the declined leads and folds with their triggers
  (recorded in the course receipt); MIRROR FRAGMENT parks behind its
  pre-gate; DIMENSION parks as a rider candidate.
- **The next askable question, if R-H1 lands:** what premise grammar do
  real declarations need — priced against the corpus of declarations this
  slice will have produced, with the grammar extension's pin movements
  named before any axiom is admitted.
