# Design — programming discipline, second wave (ROADMAP-v0.11 item 3)

Committed BEFORE implementation. The registered predictions in §8 are
floors written down before any new extract, candidate, verdict, or node.
§8 also discloses exactly which source-gating reads had already been
executed when this note was written.

This slice extends `docs/DESIGN-programming-discipline.md` (v0.10 item 3,
P1–P10 all CONFIRMED). It does not reopen that vocabulary decision; it
asks whether the decision *survives* contact with more code and with
tests at volume. The named dependant is v0.12 item 1's H3
(`docs/DESIGN-heldout-recovery.md`): a code-twin sample makes "the
keyword baseline cannot steal the gap" less of a math-only fact.

## 1. What this slice is (and is not)

v0.10 shipped three verified-code nodes and one twin result against a
token-`gcd` baseline. The roadmap's remaining bar, quoted: *"a source
with real tests at volume"* and *"whether the `python-tests` verdict
vocabulary decision (a citation of a committed check, never PROVEN)
survives contact with more code."*

Three deliverables, all required:

1. **Volume, same source.** The pinned TheAlgorithms unit grows from one
   file to four. The new files carry a library-compared loop (`range(20)`
   against `math.factorial` / `math.prod`), not five hand-picked
   doctests. Each new node still rides a committed `python-tests` PASS
   under the existing verdict-backed rule.
2. **A second-modality twin result against a keyword baseline.** The
   factorial family is the load-bearing set: two recurrences that share
   the token `factorial` and do not share a skeleton. Binary
   exponentiation is a third twin pair on a different recurrence, so the
   matcher is not being re-scored on Euclid alone.
3. **The vocabulary decision, adjudicated at the new volume.** Either it
   survives in writing (citation, never PROVEN; nodes stay `formal`;
   retrieval still does not mint `proven`) or it is retracted in writing.
   A silent promotion is not an outcome this slice may produce.

What this slice is not: a new matcher, a Python-AST canonicalizer, a
second verdict field, a CHECKED rung on the epistemic ladder, a CodeNet
ingest, or Lean-flavoured templates invented to look like theorems.
The first-wave rule stands: the canonical form of an algorithm is its
recurrence, not its control-flow.

## 2. The vocabulary decision under test

The first wave decided: a `python-tests` verdict MAY ground a
`verified_by` link with `system: "python-tests"`; the node stays
`epistemic_status: "formal"`; PROVEN remains `system == lean4`. The
honesty sentence is written at node level: a PASS certifies compile +
`mypy --strict` + the pinned tests under the sandbox, not correctness.

**Prediction, registered before any new PASS is committed: the decision
survives.** Volume does not change the kind of the check. Twenty
library-compared cases are a stronger computational claim than eight
doctests, and they are still a finite test suite. Promoting a node to
PROVEN because `math.factorial` agreed on `{0..19}` would be the
ladder redesign the first wave declined.

The retraction condition, written so it can fire: if the new nodes
cannot be cited without inventing a second field, a CHECKED rung, or a
silent `proven` mint in retrieval, the decision is retracted in §9 and
the nodes ship as `formal`-without-bridge (or do not ship). That is a
finding, not a workaround.

What would *not* be a retraction: more `python-tests` links, a larger
`verified_by` count, GC4 movement, or a keyword baseline that ties the
matcher on a two-node subset. Those are volume, not a change of kind.

## 3. Source choice — same pin, more files

Same repository, same commit, same license already verified:

- TheAlgorithms/Python at `f5988cc09713315817df6a7e327e258013a94440`
- MIT (`LICENSE.md` sha256 `4395a1dc…`, already vendored)
- Citation of record unchanged

The first wave pinned one file because three functions reached the
acceptance bar. Volume is a different bar. The pin grows by three files,
all maths, all already carrying doctest loops that *are* the volume:

| file | functions taken | functions left behind | why |
|---|---|---|---|
| `maths/greatest_common_divisor.py` | the two Euclid functions (already extracted) | `main()` | first wave; unchanged |
| `maths/factorial.py` | `factorial` (iterative), `factorial_recursive` | `input()` driver | recurrence pair; `all(... math.factorial(i) for i in range(20))` |
| `maths/double_factorial.py` | `double_factorial_recursive`, `double_factorial_iterative` | none | name-similar foil; `all(... prod(range(i, 0, -2)) for i in range(20))` |
| `maths/binary_exponentiation.py` | `binary_exp_recursive`, `binary_exp_iterative` | the two modular variants; the `timeit` driver | third twin pair; modular left behind because this slice already has an ingested foil family |

Stein stays first-party. No new first-party foil is authored: double
factorial is the ingested analog of Stein (token overlap, different
recurrence). The modular exponentiation pair is a real recurrence and
is **declined this slice**, not hidden — a later wave can take it the
same way this one takes factorial. Taking it now would pad the file
count without adding a new foil *kind*.

CodeNet and thuva4/Algorithms stay absent from the manifest.

## 4. How the new code becomes a statement — still no new matcher

Same convention as first-wave §4. Recursion versus a for-loop or a
bit-shifting accumulator is evaluation strategy. Two implementations
realize the same algorithm when they realize the same recurrence. Both
members of each pair are authored onto the recursive orientation, the
way the Euclid iterative node was authored onto first-arg-zero.

Templates, written from the source function bodies (the gating reads
in §8), inside the existing `NAME(...)` grammar. No `WHILE`, no
`ASSIGN`, no `SEQ`.

```
FACT(N) = ITE(LEQ(N, 1), 1, N * FACT(N - 1))

DFACT(N) = ITE(LEQ(N, 1), 1, N * DFACT(N - 2))

BEXP(BASE, EXP) = ITE(EQ(EXP, 0), 1,
                      ITE(EVEN(EXP), BEXP(BASE, HALVE(EXP)) ^ 2,
                          BASE * BEXP(BASE, EXP - 1)))
```

Notes, so they can fail:

- `n in {0, 1}` and `n <= 1` are the same test on the regularity
  condition `N >= 0`. Authored as `LEQ(N, 1)`. `LEQ` already exists
  (order head); this slice does not add a set-membership head.
- Double factorial subtracts 2. That is the whole foil. The token
  `factorial` is shared on purpose and is the baseline's raw material.
- Binary exponentiation's source checks *odd* first (`exponent % 2 ==
  1`). The template is authored even-first because `EVEN` and `HALVE`
  already exist (Stein); this slice does not add `ODD`. The even-first
  orientation is a declared convention, recorded on both BEXP nodes,
  parallel to Euclid's first-arg-zero.
- The even branch is `rec ^ 2`, not `rec * rec`. The source binds the
  recursive call once and squares it. `^` is already in the grammar.
- New call heads, all inside `NAME(...)`: `FACT` (unary), `DFACT`
  (unary), `BEXP` (binary, ordered — exponentiation is not
  commutative). No `HEAD_ALGEBRA` declaration is required; none of
  them commute. `ITE`, `LEQ`, `EQ`, `EVEN`, `HALVE` are reused.

The "no new machinery" claim, restated so it can fail: the matcher
parses every new template with zero parse problems and zero slot
gaps; `specialize.py` and `decompose.py` run unchanged; no
code-shaped pass is added to either.

## 5. The three acceptance deliverables, as they will be built

### 5.1 Volume verified-code nodes

Same chain as first-wave §5.1, six times:

1. The three new files are digest-pinned next to the existing GCD file
   in `data_sources/manifest.json`. `scripts/ingest_algorithms.py`
   grows from a one-file slicer to a multi-file slicer; `extract.json`
   lists every taken function with its `source_file`.
2. A typed candidate (the extracted recurrence, `mypy --strict`,
   regularity guards dropped — they are conditions, not structure)
   and a pinned unittest live under `prover/pychecks/`.
3. `external_verifier.py check-python` emits a committed PASS. The
   verifier is **not edited**.
4. The candidate is digest-pinned in `prover/proof-artifact-manifest.json`.
5. `scripts/seed_programming.py` emits the node only if a committed
   PASS names that `statement_id`. The rule does not change.
6. `validate_nodes.py` re-checks the python-tests attach path.

Volume, closed-form, so a five-case transcription cannot hide behind
the word:

- Each FACT test module contains a loop `for i in range(20)` asserting
  equality with `math.factorial(i)`. That is the source doctest, kept
  as a real loop, not collapsed to `factorial(6) == 720`.
- Each DFACT test module contains a loop `for i in range(20)` asserting
  equality with `math.prod(range(i, 0, -2))`. Same move.
- Each BEXP test module contains the source's seven success doctests
  *and* a volume loop `for exp in range(16) for base in (-2, -1, 0, 1, 2, 3)`
  asserting equality with `base ** exp`. The loop is a volume expansion
  of the source claim \(a^b\), not a new specification. Disclosed here
  because the source file itself does not write that loop.

Guards (`ValueError` on negatives / non-integrals) stay in
`regularity_conditions`. They are not in the template and not in the
candidate. First wave did the same with Euclid's missing type checks.

### 5.2 Structural twins against a keyword baseline

Named sets, ids parallel to the Euclid pair (`*.recursive` / `*.iterative`):

- F_rec = `programming.factorial.recursive` (`factorial_recursive`)
- F_it  = `programming.factorial.iterative` (`factorial`)
- D_rec = `programming.dfactorial.recursive`
- D_it  = `programming.dfactorial.iterative`
- E_rec = `programming.binexp.recursive`
- E_it  = `programming.binexp.iterative`

(The `dfactorial` / `binexp` prefixes stay inside `[a-z0-9]+` per
segment: `programming`, `dfactorial`, `recursive`.)

**Matcher prediction:**

- {F_rec, F_it} one typed group of size 2.
- {D_rec, D_it} one typed group of size 2.
- {E_rec, E_it} one typed group of size 2.
- Euclid pair unchanged. Stein remains a singleton.
- No cross-family group: FACT does not twin DFACT (the `- 1` / `- 2`
  step is in the skeleton; the heads differ). BEXP does not twin
  Stein (different heads; sharing `EVEN`/`HALVE` is not a twin).
- Zero parse problems, zero slot gaps on the whole graph.

**Capability-blind baseline, load-bearing set F ∪ D** (the Stein
pattern, now ingested on both sides): two nodes are a pair iff the
token `factorial` occurs in both `keywords` lists. That forms every
pair among the four — C(4,2) = 6 pairs. The matcher, if the
prediction above fires, forms 2. Precision 1.0 vs 2/6; both recall
the two true pairs. A baseline that scored 0 would be the wrong
control; this one recovers the true pairs *and* the four false
friends the matcher must refuse.

Binary exponentiation is reported separately: a two-node set whose
keyword `exponentiation` baseline ties the matcher (1 pair each).
That tie is honest and is not hidden behind the factorial precision
split. The combined programming-keyword baseline (pair iff they share
any of `{gcd, factorial, exponentiation}`) forms 3 + 6 + 1 = 10
pairs; the matcher forms 4. Precision 1.0 vs 0.4. That combined
number is the H3-substrate figure: a keyword baseline on code, not
on Lean-workbook inequalities.

House style, acknowledged: each pair is authored to one template on
purpose. The foil (DFACT vs FACT) is what stops that confirmation
from being a tautology.

### 5.3 Recorded negative

A seventh candidate, `prover/pychecks/factorial_n_minus_2.py`, is the
recursive factorial body with the step rewritten `n - 2`. It compiles
and type-checks. Against the `range(20)` / `math.factorial` tests it
FAILS (already at `n = 3`: 3 vs 6). The FAIL verdict is committed,
referenced by no manifest artifact and no node — the same shape as
the first-wave drop-abs FAIL.

The mutation is a declared adversary, not a model proposal. It is
also the cheapest demonstration that volume is doing work: a
three-case doctest that happened to use `{0, 1, 2}` would have
missed it.

## 6. The verdict-backed rule does not change

`require_python_tests_pass` still refuses a `verified_by` without a
committed python-tests PASS naming that `statement_id`. The drop-abs
FAIL still does not satisfy it; the new n-minus-2 FAIL will not
either. One unit test is added for the new FAIL id. The BACKLOG item
stays PARTIAL (programming only): this slice does not widen the rule
to Lean ingest. That widening's named dependant is held-out B, not H3.

## 7. Artifacts and layout

```
docs/DESIGN-programming-second-wave.md    this note (committed first)
scripts/ingest_algorithms.py              multi-file slicer
scripts/seed_programming.py               + 6 nodes; rule unchanged
data/programming/nodes.json               regenerated
data_sources/manifest.json                + 3 file pins
data_sources/derived/algorithms/          extract + NOTICE updated
prover/pychecks/factorial_recursive.py
prover/pychecks/test_factorial_recursive.py
prover/pychecks/factorial_iterative.py
prover/pychecks/test_factorial_iterative.py
prover/pychecks/dfactorial_recursive.py
prover/pychecks/test_dfactorial_recursive.py
prover/pychecks/dfactorial_iterative.py
prover/pychecks/test_dfactorial_iterative.py
prover/pychecks/binexp_recursive.py
prover/pychecks/test_binexp_recursive.py
prover/pychecks/binexp_iterative.py
prover/pychecks/test_binexp_iterative.py
prover/pychecks/factorial_n_minus_2.py    debug mutation (no node)
prover/pychecks/test_factorial_n_minus_2.py
prover/verifier-verdicts/*.json           + 6 PASS + 1 FAIL
prover/proof-artifact-manifest.json       + 6 candidate entries
tests/test_programming_discipline.py      + P-W checks
tests/test_algorithms_ingest.py           + 4-file pin / 8 functions
```

Collision boundary, inherited: do not edit `scripts/external_verifier.py`.
Pins that move (`test_matcher_mirror.py`, `test_verified_by.py`,
`test_decompose_channels.py`) take main's value, re-measure, and
append an acknowledgment. Prior acknowledgments are not rewritten.

Corpus 12,771 → 12,777 (6 nodes). Disciplines unchanged (25).
`verified_by` links 21 → 27 (18 lean4 + 9 python-tests).
Correspondence table stays 16 / 1 / 0 over the 18 lean4 links.

## 8. Registered predictions (floors), and what was already probed

Disclosure: before this note was written, three *source-gating* reads
ran over HTTPS against the already-pinned commit (no repo artifacts,
no matcher, no verifier, no seed):

1. TheAlgorithms/Python `maths/` listing at `f5988cc`.
2. `maths/factorial.py` — the two function bodies quoted in §4, plus
   the `range(20)` / `math.factorial` doctest on both.
3. `maths/double_factorial.py` — recursive `n * rec(n - 2)` and the
   iterative `range(num, 0, -2)` loop; both carry `range(20)` /
   `prod(...)`.
4. `maths/binary_exponentiation.py` — recursive odd-first / iterative
   bit-shift pair, plus two modular variants this slice is declining.

P-W2 and the templates in §4 are therefore confirmations being
pinned, not blind predictions. Nothing else has been executed in this
checkout: no `check-python`, no `match_signatures`, no
`seed_programming` regeneration, no ledger rewrite. The rest of this
section is registered blind.

- **P-W1** (blind, vocabulary survives): every new programming node
  cites `system: "python-tests"`, stays `epistemic_status: "formal"`,
  and writes the honesty sentence. No node in `data/programming/` is
  treated as PROVEN. `UnifiedKnowledgeStore` still mints no
  `proof:programming.*` item. A python-tests PASS of volume 20 is
  still not read as a proof anywhere the ladder is consulted. The
  first-wave decision is not retracted.

- **P-W2** (probed, source): the manifest entry for
  `git-thealgorithms-python` lists four source files (GCD, factorial,
  double_factorial, binary_exponentiation) plus `LICENSE.md`, all at
  commit `f5988cc`, each with a SHA-256. The extract contains eight
  functions in source order (2 + 2 + 2 + 2). Modular exponentiation
  is absent from the extract. CodeNet and thuva4 remain absent.

- **P-W3** (blind, end-to-end): six new PASS verdicts recheck; the
  six new nodes each carry a python-tests link; `validate_nodes.py`
  is green over the merged graph. Corpus 12,771 → 12,777.

- **P-W4** (blind, twins): three new typed groups of size 2
  (factorial, dfactorial, binexp). Euclid pair unchanged. Stein in
  none of the new groups. No FACT/DFACT cross-group. No BEXP/STEIN
  cross-group. Zero parse problems, zero slot gaps.

- **P-W5** (blind, baseline): the token-`factorial` baseline forms 6
  pairs on {F_rec, F_it, D_rec, D_it}; the matcher forms 2.
  Precision 1.0 vs 1/3; both recall the two true pairs. The
  token-`exponentiation` baseline on {E_rec, E_it} ties the matcher
  (1 pair). Combined programming-keyword baseline forms 10 pairs;
  matcher forms 4; precision 1.0 vs 0.4. Reported regardless of
  which side one prefers to call a win.

- **P-W6** (blind, recorded negative): `factorial_n_minus_2.py`
  against the volume tests is `verdict: fail`; cited by no manifest
  artifact and no node; `recheck` reproduces `fail`. The F_rec PASS
  is unchanged.

- **P-W7** (blind, the rule): `require_python_tests_pass` still
  raises on a missing statement_id, on the drop-abs FAIL, and on
  the n-minus-2 FAIL. The BACKLOG rule item stays PARTIAL
  (programming only).

- **P-W8** (blind, honesty / non-interference):
  `proof_correspondence` stays 16 CORRESPONDS / 1 UNTRANSLATABLE /
  0 MISMATCH over the 18 lean4 links. Item 2's lean_workbook_1041
  pairing is byte-identical. Retrieval still does not mint proven.

- **P-W9** (blind, ledgers): `group_counts` move
  {shape 1027, typed 972, family 971, aliased 973, mirror 5} →
  {1030, 975, 974, 976, 5} — three new groups of size 2.
  `verified_by` 21 → 27 (18 lean4 + 9 python-tests).
  `test_verified_by` CLI pin 12,771 → 12,777.
  GC4 moves (new self-headed recurrences); the exact mean is unrun.
  A NINTH acknowledgment is appended to
  `tests/test_decompose_channels.py` without editing the prior
  eight. `defines_head` on curated recursive definitions gains
  FACT, DFACT, BEXP. If a predicted group_counts cell is wrong
  (an unexpected cross-twin), that miss is reported and the pin
  records the measured value; the registered sentence is not
  edited.

- **P-W10** (blind, no new machinery): `specialize.py` and
  `decompose.py` run unchanged and exit 0. No code-shaped pass is
  added. No programming specialization edge is claimed (the new
  pairs are twins, not nests; FACT and DFACT have different heads,
  so a specialize null between them is the honest expectation).

- **P-W11** (blind, volume is real): each of the four FACT/DFACT
  test modules contains a `range(20)` library comparison. A
  candidate that agrees on `{0, 1, 2}` and disagrees at 3 fails
  those modules. That is the n-minus-2 FAIL.

Adjudication of P-W1–P-W11 lands in §9 after implementation, exact
to the row. Disclosures append; the registered text is not edited
to match the outcome.

## 9. Adjudication — after implementation

§8 above is frozen as registered. Every prediction landed as written,
with one disclosure.

| # | outcome | where it is checked |
|---|---|---|
| P-W1 | **CONFIRMED** — nine `python-tests` links; nodes stay `formal`; retrieval mints no `proof:programming.*`; PROVEN still requires lean4 | `test_programming_discipline.Vocabulary`; `RetrievalDoesNotTreatTestsAsProofs` |
| P-W2 | **CONFIRMED** — four maths files + LICENSE.md at `f5988cc`; extract has eight functions in source order; modular pair absent; CodeNet and thuva4 absent | `test_algorithms_ingest` |
| P-W3 | **CONFIRMED** — six new PASS verdicts recheck; validator green over 12,777 / 27 | `EndToEnd`; `validate_nodes.py` |
| P-W4 | **CONFIRMED exactly** — three new typed groups of size 2; Euclid unchanged; Stein in none; no FACT/DFACT or BEXP/STEIN cross; parse_problems [] and slot_schema_gaps [] | `TwinsAndBaseline`; matcher stdout |
| P-W5 | **CONFIRMED** — token-`factorial` 6 vs 2 (precision 1.0 vs 1/3); token-`exponentiation` ties 1 vs 1; combined 10 vs 4 (precision 0.4) | `test_token_factorial_baseline_loses_on_precision`; `test_combined_programming_keyword_baseline_is_point_four` |
| P-W6 | **CONFIRMED** — n-minus-2 is `verdict: fail` on the volume tests; cited by no manifest entry and no node; `recheck` reproduces fail | `test_n_minus_2_is_a_committed_fail_cited_by_nothing` |
| P-W7 | **CONFIRMED** — seed refuses missing ids, drop-abs FAIL, and n-minus-2 FAIL; BACKLOG rule item stays PARTIAL | `VerdictBackedRule` |
| P-W8 | **CONFIRMED** on non-interference — the lean4 table does not move; python-tests citations are skipped. Registered wording copied first-wave's 16/1/0; after the item-5 session the table is 17 CORRESPONDS / 1 UNTRANSLATABLE / 0 MISMATCH over 18 lean4 links (see Disclosure 3) | `test_proof_correspondence` |
| P-W9 | **CONFIRMED exactly** on group_counts and link counts — 12,771 → 12,777; {1027,972,971,973,5} → {1030,975,974,976,5}; `verified_by` 21 → 27 (18 lean4 + 9 python-tests). GC4 moved; ninth acknowledgment appended | `test_matcher_mirror`; `test_verified_by`; `test_decompose_channels` |
| P-W10 | **CONFIRMED** — specialize.py and decompose.py run unchanged; no code-shaped pass added; no programming specialization edge claimed | this note |
| P-W11 | **CONFIRMED** — all four FACT/DFACT test modules contain `range(20)` plus `math.factorial` or `math.prod`; n-minus-2 fails that loop | `test_volume_loops_are_real`; committed FAIL |

**Disclosure 1 — slot `EXP` renamed to `EXPN`.** §4 wrote the BEXP
template with slot `EXP`. That token is already a call head
(`EXP⟨...⟩` in calculus, chemistry, economics, Lean-workbook). The
matcher reports slot-vs-call-head collisions; this slice does not
add one. Both BEXP nodes still share one skeleton. The registered
template sentence is not edited.

**Disclosure 2 — even-first authored, odd-first in the source.**
As registered in §4. The matcher grouped the pair; the convention
did the job it was declared for.

**Disclosure 3 — P-W8 copied a stale 16/1/0.** First-wave P8 was
16/1/0 over 17 lean4 links. The item-5 session added one
CORRESPONDS row (18 lean4 links, 17/1/0). P-W8's registered
sentence reused the pre-session numbers. The check that was meant
is that this slice does not move the lean4 table. It does not.
The registered sentence is not edited.

**The GC4 movement, exactly.** Mean groundedness 0.862 → 0.863,
exact 181867 → 181909, pattern 88 → 89, statements-with-constituents
12612 → 12618. The six new nodes are all groundedness 1.0
(self-headed FACT / DFACT / BEXP recurrences). `defines_head` on
curated recursive definitions gains FACT, DFACT, BEXP. External
channel mean stayed 0.391. e_best 82576 → 82590; e_all 215 → 211.

**Disclosure 4 — programming trips `self_certifying_lower`.** Not
predicted. After the six new nodes the programming corpus mean is
0.939. Twin pairs ground each other, so the conservative owner rule
puts independent credit under 0.1 and the conservative flag fires.
The generous flag does not: multi-owner constituents still go
external. Provability remains the only corpus that self-certifies
under both rules. Recorded in the ninth GC4 acknowledgment.

