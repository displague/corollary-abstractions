# Design — skeleton emitter for the unique-covered remainder (ROADMAP-v0.11 prerequisite)

Committed BEFORE the emitter authors any new node. Predictions in §5 are
floors. Named dependant: ROADMAP-v0.11 item 1 (the self-grounding curve
needs thousands, not hundreds).

This is the design `docs/DESIGN-item4-authoring.md` §1 deferred: a
translator from Lean surface to a matcher template, not a silent
expansion of the first wave.

## 1. Scope, argued

The coverage instrument marks 12,681 unique Lean-workbook goals
full-statement-covered. Item 4 authored **251** parse-clean ground
identities. A read-only census of the committed extract (before this
emitter existed) splits the rest:

| bucket | n | why the first wave dropped it |
|---|---:|---|
| already authored (ground, parse-clean) | 251 | — |
| ground, `TOKEN_RE` / `√(expr)` fail | 51 | matcher hole, not a coverage hole |
| ASCII field inequality, with hyps | 6,538 | variables + `∧` hyps + `≥` |
| ASCII field inequality, goal only | 1,518 | variables + `≥` |
| ASCII equation, with variables | 860 | variables |
| `Real.sqrt` / `log` / `exp` | 1,324 | Lean head spelling, juxtaposition |
| quantifier prefix | 1,163 | `∀`/`∃` need `FORALL`/`EXISTS` wrapping |
| `Real.sin` / `cos` / `tan` | 306 | Lean head spelling, juxtaposition |
| other (nat/int mix, goal-level `∧`, …) | 588 | mixed |
| Greek letters in the surface | 23 | `TOKEN_RE` is ASCII |
| predicates (`Even` / `Odd` / `Prime`) | 15 | juxtaposition application |
| **remainder (not first-wave)** | **12,335** | |
| unique-covered after skip-names | 12,637 | 12,681 minus already-authored elsewhere |

"Covered" still does not mean "has a matcher template." The emitter is
the missing function: Lean surface → a string `tokenize`/`Parser` accept,
using only heads the corpus already carries. Failures are counted, not
forced.

**This slice authors every unique-covered statement whose emitted
template parses.** What still fails is the exclusion census the roadmap
asked for, committed as `experiments/lean_workbook_emit.json`.

Already-authored ids (`leanworkbook.ground.*` and the five
`SKIP_NAMES`) stay. New nodes use `leanworkbook.skel.<name>` so the
first-wave ids do not churn.

## 2. What the emitter is

A Lean-fragment parser + printer, `scripts/emit_skeleton.py`, reused by
`scripts/seed_lean_workbook.py`. It is not a second coverage classifier:
`grammar_coverage.classify` remains the admission gate; the emitter only
runs on `full_ok` statements.

Translations, all onto existing heads:

| Lean surface | matcher template |
|---|---|
| `Real.sin x` / `sin x` | `SIN(x)` |
| `Real.sqrt a` / `√(expr)` | `SQRT(a)` / `SQRT(expr)` |
| `Real.log` / `Real.exp` | `LOG` / `EXP` |
| `Even n` / `Odd` / `Nat.Prime` / `Irrational` | `EVEN(n)` / `ODD` / `PRIME` / `IRRATIONAL` |
| `a ≥ b` / `≤` / `<` / `>` | `a >= b` / `<=` / `<` / `>` |
| `a ≠ b` | `NEG(a = b)` (no `≠` head; negation of equality) |
| `A ∧ B` / `∨` / `¬` / `→` | `MEET` / `JOIN` / `NEG` / `IMPLIES` |
| `A ↔ B` | `MEET(IMPLIES(A, B), IMPLIES(B, A))` |
| `∀ x : ℝ, P` / `∃ x, P` | `FORALL(x, P)` / `EXISTS(x, P)` (nested for chains) |
| hyps `H1`, `H2` ⊢ `G` | `IMPLIES(MEET(H1, H2), G)` |
| Greek `α`, `ψ₁`, `π` | `alpha`, `psi1`, `pi` (ASCII slots; `TOKEN_RE` stays ASCII) |

Type ascriptions are stripped. Juxtaposition of a known head and an atom
is application (`SIN x` → `SIN(x)`), binding tighter than `^`.

If the printer's output fails `template_parses`, the statement is
**excluded**, with the parse error in the census. The matcher is not
widened to invent Lean-flavoured syntax.

## 3. `TOKEN_RE` (carried lane, ships here)

`RELATIONS` already contains `<` and `>`. `TOKEN_RE` matches `<=` `>=`
but not standalone `<` `>`. That hole is why 51 ground goals are
covered-but-unauthored. The fix is the character class, with `<=` `>=`
kept as **earlier alternatives** so they still win.

Two of the 51 are `√(expr)` rather than `√digits`; those join the
emitter's `SQRT(...)` rewrite, not a second token-class hole.

## 4. Cost: ingested statements are not specialize / pattern endpoints

Item 4 needed P6–P8 because fully-ground trees exploded
`specialize.py` / `decompose.py`. The remainder **has slots**. The same
explosion returns, worse, if 8,000 slotted inequalities become
generals or decompose patterns.

The curve is a decomposition-side exact-owner query
(`docs/DESIGN-self-grounding-ingestion.md` §7). It must not re-run the
specializer. So:

- **specialize:** skip any pair whose general or specific is in an
  ingested discipline (`lean_workbook`, `ingested_arithmetic`). The 713
  curated edges stay; ingested statements participate in twins and in
  decompose exact lookup, not in specialization.
- **decompose patterns:** a form enters `forms_by_head` only if at least
  one owner is **not** ingested. Exact `side_forms` / `subterm_hosts`
  still index ingested skeletons — that is the ISG substrate.
  **P-E5b (disclosed after a 8-minute no-output run):** ingested
  *statements* also skip `pattern_cover`. Trying curated patterns
  against 12k slotted inequalities is the same explosion P8 stopped
  for ground trees. The curve is an exact-owner query; pattern
  membership stays a curated-only measurement. Pattern is predicted
  to stay 100.

## 5. Registered predictions

Disclosure: the bucket counts in §1 were measured by a read-only pass
over the committed extract before this emitter existed. After the
emitter existed and **before the seed wrote any node**, a second
read-only pass measured emit-or-exclude: **302** ground (the original
251 plus all 51 TOKEN_RE / `√(expr)` misses — P-E1 fired in full) and
**12,212** emitted of 12,335 remainder (**123** excluded). Dominant
exclusions: `parse_fail` 54, chained inequalities (`a >= b >= c`, 16),
superscript inverse `⁻¹` (12), trailing tokens. No seed had been run;
no ledger had been regenerated.

- **P-E1** (TOKEN_RE): `a < b` and `a > b` tokenize. `a <= b` / `a >= b`
  still produce the two-character tokens (earlier alternatives).
  Committed `parse_problems` stays empty. At least 49 of the 51
  first-wave misses become authorable as ground (the two `√(expr)`
  ride the emitter rewrite).
- **P-E2** (probed count): the seed emits the 251 first-wave nodes
  unchanged in id, plus every remaining unique-covered statement whose
  emitted template parses. `check_regeneration` is byte-identical.
  Zero matcher parse problems / slot gaps. The emitted count and the
  exclusion census land in `experiments/lean_workbook_emit.json`
  **before** any "thousands" claim.
- **P-E3** (blind): `group_counts` moves. Shared inequality skeletons
  (`a + b >= c`, AM-GM shapes, …) will twin. The movement is reported.
- **P-E4** (specialize skip): the 713 pre-ingest specialization edges
  are a subset of the new report (identical on the curated pair set).
  No new edge has an ingested endpoint. The run finishes in minutes.
- **P-E5** (decompose): pattern-as-ingested-only-form does not happen
  (no `forms_by_head` entry whose owners are all ingested). Exact
  constituents grow. Pattern may grow from curated-pattern cover of
  ingested constituents; if it does, the number is reported. Mean /
  exact / pattern / statements-with-constituents all change and each
  change is a corpus change, acknowledged like the seventh
  GC4 acknowledgment, not a silent re-pin.
- **P-E6**: no new node carries `verified_by`. Correspondence table
  stays 17 / 1 / 0 over lean4 links.
- **P-E7**: the authored ingested count is **thousands**, not hundreds
  — or the exclusion census says why it is not, bucket by bucket.

## 6. What this is not

It is not a claim that an emitted skeleton is a proof, a twin, or a
self-grounding finding. It is the substrate item 1's curve asked for.
S1–S4 stay unadjudicated until the curve runs on this corpus.

It is not a widening of `TOKEN_RE` to Unicode identifiers. Greek is
transliterated; a future Unicode ident class is a separate prediction.

It is not specialize-at-scale. That stays the carried
`specialize.py` cost item, now bounded by the ingested skip rather
than left as a wall in front of the curve.

## 7. Adjudication — after the emitter and seed ran

§5 is frozen as registered.

| # | outcome | evidence |
|---|---|---|
| P-E1 | **CONFIRMED** | `a < b` / `a > b` tokenize; `<=` `>=` still win. All 51 first-wave misses became authorable (302 ground). |
| P-E2 | **CONFIRMED** | 302 ground + **12,212** emitted = **12,514** ingested nodes. 123 excluded (`experiments/lean_workbook_emit.json`). `validate_nodes` 12,771. Matcher parse_problems **0**, slot_schema_gaps **0**. |
| P-E3 | **CONFIRMED** | `group_counts` `{35,36,35,37,5}` → `{1027,972,971,973,5}` on 12,771 nodes. Shared inequality skeletons twin. |
| P-E4 | **CONFIRMED** | 713 specialization edges, identical curated pair set. No ingested endpoint. Search 25.9s after load. |
| P-E5 | **CONFIRMED, with P-E5b PARTIAL** | Exact **181,867**. Pattern **88** (not 100): ingested skip of `pattern_cover` plus exact lookup now owning former pattern-only skeletons. Mean **0.862**. Statements-with-constituents **12,612**. Graph same_corpus 0.466 / external 0.391; lean_workbook same_corpus-dominant (0.473 > 0.387). That is substrate, not S1–S4. |
| P-E6 | **CONFIRMED** | No new `verified_by`. |
| P-E7 | **CONFIRMED** | 12,514 authored ingested nodes (thousands). 123 excluded, bucketed. |

**Disclosure — `reports/decompositions.json` is not regenerated at this scale.** 181k constituents with full owner lists is a hundred-megabyte artifact. Live `analyze` is the source of the pins; the committed report stays the pre-scale file. Filed in BACKLOG.

**The curve is unblocked, not run.** S1–S4 remain unadjudicated.
