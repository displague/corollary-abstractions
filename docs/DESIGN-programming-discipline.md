# Design — programming as a first-class discipline (ROADMAP-v0.10 item 3)

Committed BEFORE implementation. The registered predictions in §8 are floors
written down before any adjudication run; §8 also discloses exactly which
feasibility probes had already been executed when this note was written,
because a prediction registered after its experiment is not a prediction.

This slice executes the handoff in `docs/HANDOFF-v0.10-item3-parallel.md`.
It is built on the external verifier of item 2
(`docs/DESIGN-external-verifier.md`) and does not rebuild it.

## 1. What this slice is (and is not)

The architecture already runs, for every other discipline:

```
source  ->  parse  ->  canonical form  ->  structural address  ->  pointer residual  ->  verifier
```

Item 2 stood up the missing verifier. This slice swaps the *source* for code
and runs the same operations. The roadmap's claim under test, quoted: *"no
new machinery."* If a parallel matcher or a second verdict vocabulary looks
necessary, that is a finding to write down, not a workaround to ship.

Three deliverables, all required:

1. **One verified-code node type end-to-end** — pinned source, pinned
   candidate + tests, committed `python-tests` verdict, seed-generated
   node, validator green, and a corpus link whose vocabulary this note
   decides.
2. **One structural-twin-over-code result against a capability-blind
   baseline** — the baseline is the point; it is reported even if it wins.
3. **One synthesis-or-debug transaction adjudicated by the external
   verifier**, including at least one committed FAIL or REFUSED that is
   recorded rather than retried away.

What this slice is not: a code-search engine, a multi-language AST
canonicalizer, a CodeNet-scale ingest, or a claim that passing tests equal
a proof.

## 2. The vocabulary decision (the headline)

Item 2 froze `verified_by.system` to `lean4` and wrote, verbatim: *"a
`python-tests` verdict is a committed, recheckable authority for a
computational claim, but it does not enter the corpus's `verified_by`
vocabulary this slice — that is roadmap item 3's decision to make."*

**Decision: a `python-tests` verdict MAY ground a `verified_by` link, with
`system: "python-tests"`.** The field is the corpus's citation of a
committed verdict. The `system` tag names the check. The two systems are
not interchangeable, and the epistemic ladder is not silently widened.

Concretely:

- The link shape stays `{system, artifact, reference}`. No parallel
  `checked_by` field. The existing vocabulary carries the citation; a
  second field would be the second verdict vocabulary the roadmap told
  this slice not to invent.
- `system: "lean4"` continues to mean what it means today: a traced
  Lean transition-row artifact, exclusive theorem ownership, the
  correspondence rung's shape check. This is the closed form of the
  **PROVEN** rung (`docs/DESIGN-epistemic-ladder.md`).
- `system: "python-tests"` means: the cited artifact is digest-pinned in
  `prover/proof-artifact-manifest.json`, every manifest `verdicts` entry
  is a PASS whose `claim.statement_id` equals the citing node, and the
  verdict's backend is `python-tests`. The node stays
  `epistemic_status: "formal"`. This citation does **not** promote the
  node to PROVEN.
- The honesty boundary is inherited, not softened: a `python-tests` PASS
  certifies that the pinned candidate compiled, passed `mypy --strict`,
  and survived the pinned tests under the sandbox. It does not certify
  the candidate correct. Every programming node that carries the link
  records that sentence in `semantic_interpretation`.
- `proof_correspondence` scores **lean4 links only**. A python-tests
  citation is not a Lean goal and must not become UNTRANSLATABLE noise
  in the 16 / 1 / 0 table.
- `verified_by_errors` grows a second resolution path: `python-tests`
  does not run `select_closing_transitions` (that parser is Lean
  transition-rows). Cross-system attach is refused — a python-tests
  link may not cite a Lean triples file, and a lean4 link may not cite
  a Python candidate.
- Exclusive ownership still applies, keyed by `(system, reference)`.

Why not keep `verified_by` lean4-only and write `formal`-without-bridge
on every code node? Because then the verdict that verified the code is a
process fact, not a graph fact, and "verified-code node type end-to-end"
collapses to "we ran a check and then authored a node." Item 2 built
`python-tests` as a committed authority so this slice could cite it.

Why not add a CHECKED rung to the ladder? The ladder's closed forms are
load-bearing. Opening `verified_by.system` and keeping PROVEN =
`system == lean4` is the smaller, honest change. A new rung would be a
ladder redesign, not a programming-discipline slice.

Why not put the python-tests citation on the *Lean* artifact the way
item 2 already pinned
`lean_workbook_1041.python-tests.json` next to the lean4 verdict? That
pairing is a second authority over an *arithmetic claim*. A code node
has no Lean artifact. The citation has to live on the code artifact.

## 3. Source choice, license-gated before use

The handoff named three candidates. Each was gated against the house
rule: anything used goes through `data_sources/manifest.json` (pinned
URL + SHA-256, license field, `attribution` as the citation of record)
plus a `NOTICE.md` in the derived directory. Empirical-tier sources
never ground a `verified_by`. A smaller, cleanly-licensed source that
reaches the acceptance bar beats a large one that cannot be
redistributed.

| candidate | license found | verdict |
|---|---|---|
| `thuva4/Algorithms` | Apache-2.0 (`LICENSE` at repo root, fetched 2026-08-12) | **Declined as the primary source.** The repository is TypeScript. The item-2 verifier's live backend is `python-tests`; running TS would require a second backend, which is new machinery this slice is not licensed to add. Apache-2.0 would have permitted a derived extract. |
| `IBM/Project_CodeNet` | repo tools Apache-2.0; dataset often described as CDLA-2.0; **submissions carry their own terms** (handoff; CodeNet paper) | **Declined.** The test cases are what would make it fit `python-tests`, but submissions are not uniformly redistributable. Gating "before anything redistribution-adjacent" fails closed. |
| `TheAlgorithms/Python` | MIT (`LICENSE.md`, fetched 2026-08-12: "Copyright (c) 2016-2022 TheAlgorithms and contributors") | **Chosen.** Python source the existing backend can run; MIT permits a derived extract with attribution. |

The pinned unit is **one file**, not the repository: 
`maths/greatest_common_divisor.py` at commit
`f5988cc09713315817df6a7e327e258013a94440` (2026-08-03), via the same
per-file pin shape miniF2F uses (`raw_url_template` + per-file SHA-256).
A whole-repo archive is unnecessary for three functions and would put
a moving `master` in the reproducibility chain.

That file contains two implementations of Euclidean GCD
(`greatest_common_divisor`, recursive; `gcd_by_iterative`, a while-loop)
and a `main()` that still uses Python-2 `except` syntax. The extract
takes the two functions and drops `main()`. The third algorithm this
slice needs — Stein's binary GCD, the name-similar non-twin — is
**first-party**, disclosed as such, not laundered through the
TheAlgorithms pin.

A first-party Stein is not a hidden ingest. It exists so the twin
experiment has a capability-blind foil whose *name* overlaps the Euclid
pair (`gcd`) while its *recurrence* does not. Inventing a foil and
citing it as ingested would be the dishonesty; writing it down as
first-party is the alternative.

## 4. How code becomes a statement node — no new matcher

The existing template grammar is equation-like. The existing matcher
canonicalizes call heads and operators; it does not walk Python ASTs.
Adding an AST matcher would be the "new machinery" the roadmap put
under test.

**The canonical form of an algorithm, in this slice, is its recurrence,
not its control-flow.** Recursion versus a while-loop is an evaluation
strategy. Two implementations realize the same algorithm when they
realize the same remainder recurrence. That is the analog, for code, of
every other discipline's authored template: Coulomb and Newton are
twins because they were authored to one skeleton, not because a
physics-AST pass recovered it.

The Euclidean recurrence, written in the grammar the matcher already
parses (`NAME(...)` calls, `=` / `%`, no new binder):

```
GCD(?a, ?b) = ITE(EQ(?a, 0), ABS(?b), GCD(MOD(?b, ?a), ?a))
```

This is what `greatest_common_divisor` *says*
(`return abs(b) if a == 0 else greatest_common_divisor(b % a, a)`).
`gcd_by_iterative` (`while y: x, y = y, x % y; return abs(x)`) is the
same remainder recurrence with the opposite argument as the loop
condition. After slot renaming to the first-arg-zero orientation — a
declared, one-line authoring convention, recorded on both nodes — they
share the template above.

Stein's binary GCD does not. Its recurrence branches on parity and a
factor of two; the template will say so, with different heads
(`EVEN` already exists in number theory; `ITE` nesting; no `MOD`).
Name overlap is intentional and is the baseline's raw material.

New call heads this introduces, all inside the existing `NAME(...)`
grammar — not a new parser:

- `ITE` — ordered ternary (condition, then, else). Not commutative.
- `GCD` — binary. Declared commutative in `HEAD_ALGEBRA` with
  provenance `CONVENTION` (gcd is symmetric on ℕ; this slice does not
  author a separate commutativity theorem just to flip the provenance
  bit).
- `ABS` — unary.

`MOD` and `EQ` / `EVEN` already exist. No `WHILE`, no `ASSIGN`, no
`SEQ`: those would be the AST encoding this slice is declining. If a
later slice wants control-flow twins (two while-loops that are not
the same recurrence), that is a new head family with its own
measurement, not a silent extension of this one.

The "no new machinery" claim, stated so it can fail: the matcher
parses every programming template with zero parse problems and zero
slot gaps; `specialize.py` and `decompose.py` run unchanged; no
code-shaped pass is added to either.

## 5. The three acceptance deliverables, as they will be built

### 5.1 Verified-code node, end-to-end

Chain, parallel to item 2 §3, with the backend swapped:

1. TheAlgorithms file is digest-pinned in the manifest; the
   deterministic extract lands in
   `data_sources/derived/algorithms/` with `LICENSE` + `NOTICE.md`.
2. A typed candidate (the extracted function, mypy-strict, no `main`)
   and its pinned unittest live under `prover/pychecks/`.
3. `external_verifier.py check-python` emits a committed verdict
   under `prover/verifier-verdicts/`. The verifier is **not edited**
   (collision boundary).
4. The candidate is digest-pinned as a new entry in
   `prover/proof-artifact-manifest.json` with `verdicts: [that PASS]`.
   Additive field use, same file, same consumers: they already ignore
   unknown structure beyond `sha256` / `authority`.
5. `scripts/seed_programming.py` emits the node with
   `verified_by: [{system: "python-tests", artifact, reference}]`
   only if a committed PASS names that `statement_id`. Otherwise the
   seed refuses (the rule in §6).
6. `validate_nodes.py` re-checks the python-tests attach path;
   `external_verifier.verdict_ledger_errors` already re-hashes
   verdicts and manifest pins — that rung is inherited, not forked.

The same chain runs for the iterative extract and for the first-party
Stein candidate. Three PASS verdicts, three nodes, three manifest
entries.

### 5.2 Structural twin against a capability-blind baseline

Named set:

- T_rec = `programming.euclid.recursive` (TheAlgorithms
  `greatest_common_divisor`)
- T_it  = `programming.euclid.iterative` (TheAlgorithms
  `gcd_by_iterative`)
- T_st  = `programming.stein.binary` (first-party Stein)

**Matcher prediction:** T_rec and T_it typed-twin (and therefore
shape/family/aliased-twin: one new group of size 2). T_st is a
singleton.

**Capability-blind baseline:** two nodes are a pair iff the token
`gcd` occurs in both `statement_id`s. Cheapest possible name
baseline; it needs no parser. On this set it forms every pair among
the three (T_rec–T_it, T_rec–T_st, T_it–T_st). Precision 1/3 if the
Euclid pair is the only true positive; recall 1. The matcher, if P4
fires, has precision 1 and recall 1.

This is not vacuous: the baseline *does* recover the true pair, and
also recovers two false friends the matcher must refuse. A baseline
that scored 0 would have been the wrong control. Reporting the
precision split is the result, including the case where the matcher
ties or loses.

The house style of twin authoring is acknowledged, not hidden: T_rec
and T_it are authored to one template on purpose, the way
`temporal.order.precedence_transitivity` was authored onto the LEQ
transitivity skeleton. The matcher confirming the group is the
adjudication; the Stein foil is what stops that confirmation from
being a tautology against a name baseline.

### 5.3 Synthesis-or-debug, with a recorded negative

A fourth candidate, `prover/pychecks/gcd_euclid_drop_abs.py`, is the
recursive body with `abs` deleted (`return b if a == 0 else ...`).
The pinned tests include the TheAlgorithms doctest
`gcd(-3, 9) == 3`. The mutation compiles and type-checks; the tests
FAIL. That FAIL verdict is committed, referenced by no manifest
artifact and no node — the same shape as item 2's
`lean_workbook_10411` recorded failure. A "debug" step that restored
`abs` and re-ran would pass; we do not need to re-run the already-
passing T_rec candidate to know that. The recorded negative *is* the
transaction: a proposed edit, adjudicated, refused, kept.

No model proposes the mutation. Hybrid only at the edges; this slice
has no edge that needs one. The mutation is a pinned, declared
adversary, the way item 2's `14 ∣ 2^30 + 3^60` was.

## 6. Verdict-backed ingestion is a RULE for this discipline

Item 2 filed in `docs/BACKLOG.md`: nothing forces a future ingested
node to carry a verdict; a manifest entry that omits `verdicts` is
cited like the 16 pre-verifier links.

This slice makes the rule real **for programming nodes**, not for the
whole graph (widening the Lean side is a validator change that would
re-litigate item 2's frozen vocabulary, and the 16 propositional
links have no committed lean4 verdict to satisfy a blanket rule).

The rule, closed-form:

- `scripts/seed_programming.py` will not emit a `verified_by` link
  unless a committed verdict file exists, parses, has
  `backend == "python-tests"`, `verdict == "pass"`, and
  `claim.statement_id` equal to the node being emitted.
- A programming node without a bridge must carry the same
  node-level `formal`-without-bridge record item 2 required of
  `lean_workbook_10202`. This slice authors no such node; the
  branch is in the seed so the next author cannot skip it silently.
- A unit test constructs a would-be node whose statement_id has no
  PASS and asserts the seed-side check (or the validator-side
  equivalent) refuses it.

The BACKLOG item is marked PARTIAL: the rule is real for the
discipline that mints code nodes; the Lean-ingest half remains open
for the slice that next authors ingested Lean.

## 7. Artifacts and layout

```
docs/DESIGN-programming-discipline.md     this note (committed first)
scripts/ingest_algorithms.py              fetch-verify-extract; WOLD shape
scripts/seed_programming.py               the seed; the verdict-backed rule
data/programming/nodes.json               generated, never hand-edited
data_sources/manifest.json                + TheAlgorithms per-file pin
data_sources/derived/algorithms/          extract + LICENSE + NOTICE.md
prover/pychecks/gcd_euclid_recursive.py   typed candidate (T_rec)
prover/pychecks/test_gcd_euclid_recursive.py
prover/pychecks/gcd_euclid_iterative.py   typed candidate (T_it)
prover/pychecks/test_gcd_euclid_iterative.py
prover/pychecks/gcd_stein.py              first-party foil (T_st)
prover/pychecks/test_gcd_stein.py
prover/pychecks/gcd_euclid_drop_abs.py    debug mutation (no node)
prover/pychecks/test_gcd_euclid_drop_abs.py
prover/verifier-verdicts/*.json           committed python-tests verdicts
prover/proof-artifact-manifest.json       + 3 candidate entries (additive)
scripts/validate_nodes.py                 + python-tests attach path
scripts/proof_correspondence.py           skip non-lean4 links
scripts/match_signatures.py               + GCD commutative in HEAD_ALGEBRA
tests/test_algorithms_ingest.py           manifest / license / citations
tests/test_programming_discipline.py      P1–P8, baseline, recorded FAIL
```

Collision boundary, inherited from the handoff — do not edit these
while the loop agent's slices are in flight; after rebase, regenerate
ledgers and append-only-acknowledge pins, never text-merge JSON and
never touch another slice's registered acknowledgment:

`reports/*.json`, `experiments/wold_reach.json`,
`tests/test_decompose_channels.py`, `tests/test_matcher_mirror.py`,
`tests/test_verified_by.py`, `README.md`, `data/number_theory/`,
`scripts/seed_number_theory.py`, `scripts/retrieval.py`,
`scripts/external_verifier.py`.

Corpus counts move 253 → 256 (3 nodes; 24 → 25 disciplines). Links
17 → 20, all three new ones `system: python-tests`, so the
correspondence table stays 16 / 1 / 0. `group_counts` is predicted
in P9, not assumed null.

## 8. Registered predictions (floors), and what was already probed

Disclosure: before this note was written, four *source-gating* reads
ran over HTTPS (no repo artifacts, no matcher, no verifier, no seed):

1. `thuva4/Algorithms` `LICENSE` — Apache-2.0 full text; the
   repository listing is TypeScript (`package.json`, `tsconfig.json`,
   no Python implementations).
2. TheAlgorithms/Python `LICENSE.md` — MIT, copyright
   2016-2022 TheAlgorithms and contributors.
3. TheAlgorithms/Python `maths/greatest_common_divisor.py` at
   `master` (commit `f5988cc…` as of the fetch) — the two function
   bodies quoted in §4, plus a Python-2 `main()`.
4. Public description of Project CodeNet licensing (repo Apache-2.0;
   submissions carry their own terms).

P2 is therefore a *confirmation being pinned*, not a blind
prediction. P4's templates are written from (3), not from a matcher
run. Nothing else has been executed in this checkout: no
`check-python`, no `match_signatures`, no `seed_programming`, no
ledger regeneration. The rest of this section is registered blind.

- **P1** (blind, vocabulary): `verified_by.system == "python-tests"`
  is accepted by `verified_by_errors` for a programming node whose
  artifact is manifest-pinned and whose PASS verdict claims that
  node; the same link with `system: "lean4"` against a `.py`
  artifact is refused; a python-tests link against
  `prover/ingested_triples.json` is refused. `epistemic_status`
  remains `formal`. The PROVEN closed form
  (`docs/DESIGN-epistemic-ladder.md`) still requires `system ==
  "lean4"`. No node in `data/programming/` is treated as PROVEN.

- **P2** (probed, source): the committed manifest entry for
  TheAlgorithms records MIT as found in `LICENSE.md`, pins commit
  `f5988cc09713315817df6a7e327e258013a94440` and the SHA-256 of
  `maths/greatest_common_divisor.py`, and carries an `attribution`
  that is reproduced verbatim in
  `data_sources/derived/algorithms/NOTICE.md`. CodeNet and
  thuva4/Algorithms are absent from the manifest.

- **P3** (blind, end-to-end): T_rec, T_it, and T_st each carry a
  `verified_by` python-tests link; each cited verdict rechecks
  `pass`; `validate_nodes.py` is green over the merged graph
  including `data/programming/`.

- **P4** (blind, twins): T_rec and T_it share one typed skeleton
  and form a group of size 2 at shape, typed, family, and aliased.
  T_st is in none of those groups. Zero parse problems, zero slot
  gaps on the whole graph.

- **P5** (blind, baseline): the token-`gcd` baseline forms 3 pairs
  on {T_rec, T_it, T_st}; the matcher forms 1 (T_rec–T_it). Matcher
  precision 1.0 vs baseline precision 1/3; both recall the true
  pair. Reported in `experiments/ANALYSIS.md` regardless of which
  side one prefers to call a win — the matcher wins on precision,
  ties on recall.

- **P6** (blind, recorded negative):
  `gcd_euclid_drop_abs.py` against the negative-carrying tests is
  `verdict: fail`; the committed FAIL is referenced by no manifest
  artifact and no node; `recheck` reproduces `fail`. The T_rec PASS
  is unchanged.

- **P7** (blind, the rule): a programming node whose
  `statement_id` has no committed python-tests PASS cannot be
  emitted with a `verified_by` link. One unit test is the check.
  The BACKLOG "Verdict-backed ingestion should be a RULE" item is
  marked PARTIAL (programming only).

- **P8** (blind, honesty / non-interference):
  `proof_correspondence` over the merged graph stays 16 CORRESPONDS
  / 1 UNTRANSLATABLE / 0 MISMATCH — the three new links are not
  scored. Item 2's lean_workbook_1041 lean4 + python-tests pairing
  is byte-identical. A python-tests PASS is not read as PROVEN
  anywhere the ladder is consulted.

- **P9** (blind, ledgers): corpus 253 → 256, disciplines 24 → 25.
  `group_counts` moves, for the first time after five consecutive
  twin-null slices: shape 30 → 31, typed 31 → 32, family 30 → 31,
  aliased 32 → 33, mirror 5 unchanged (one new group of size 2).
  GC4 aggregate will move (new statements, new constituents); the
  exact mean is unrun. If a GC4/GC5 pin moves, a new append-only
  acknowledgment is added to `tests/test_decompose_channels.py`
  without editing the prior four. Pins in `test_matcher_mirror.py`
  and `test_verified_by.py` are updated the same way: take main's
  value, re-measure, acknowledge the movement, do not rewrite
  earlier acknowledgments.

- **P10** (blind, no new machinery): `specialize.py` and
  `decompose.py` run unchanged over the enlarged graph and exit 0.
  No code-shaped pass is added to either. Any specialization the
  cheapest-derivation graph happens to find is reported; none is
  required for acceptance (the Euclid pair are twins, not a
  general/specific nest, so a specialization null is the honest
  expectation).

Adjudication of P1–P10 lands in this file's §9 after implementation,
exact to the row. Disclosures append; the registered text is not
edited to match the outcome.

## 9. Adjudication — after implementation

§8 above is frozen as registered. Every prediction landed as written.
One disclosure at the end.

| # | outcome | where it is checked |
|---|---|---|
| P1 | **CONFIRMED** — three `python-tests` links accepted; cross-system attach refused both ways; nodes stay `formal`; PROVEN closed form still requires lean4 | `test_programming_discipline.Vocabulary`; `DESIGN-epistemic-ladder.md` |
| P2 | **CONFIRMED** — MIT as found in LICENSE.md, commit `f5988cc` pinned, citation verbatim in NOTICE + extract; CodeNet and thuva4 absent from the manifest | `test_algorithms_ingest.ManifestPin` |
| P3 | **CONFIRMED** — three PASS verdicts recheck; validator green over 256 / 25 | `test_programming_discipline.EndToEnd`; `validate_nodes.py` |
| P4 | **CONFIRMED exactly** — typed skeleton `GCD⟨?0:V, ?1:V⟩ = ITE⟨EQ⟨?0:V, 0⟩, ABS⟨?1:V⟩, GCD⟨?0:V, MOD⟨?1:V, ?0:V⟩⟩⟩` groups T_rec + T_it; T_st in no group; parse_problems [] and slot_schema_gaps [] | `test_programming_discipline.TwinsAndBaseline`; matcher stdout |
| P5 | **CONFIRMED** — token-`gcd` baseline forms 3 pairs; matcher forms 1; precision 1.0 vs 1/3; both recall the Euclid pair | `test_token_gcd_baseline_loses_on_precision` |
| P6 | **CONFIRMED** — drop-abs is `verdict: fail` on the negatives; cited by no manifest entry and no node; `recheck` reproduces fail | `test_drop_abs_is_a_committed_fail_cited_by_nothing` |
| P7 | **CONFIRMED** — `require_python_tests_pass` raises on a missing statement_id and on the drop-abs FAIL; BACKLOG item marked PARTIAL | `VerdictBackedRule`; `docs/BACKLOG.md` |
| P8 | **CONFIRMED** — correspondence stays 16 / 1 / 0 over 17 lean4 links; python-tests citations are skipped | `test_proof_correspondence` (count unmoved) |
| P9 | **CONFIRMED exactly** — 253 → 256, 24 → 25; group_counts 30/31/30/32/5 → 31/32/31/33/5; GC4 moved and the FIFTH acknowledgment was appended | `test_matcher_mirror`; `test_decompose_channels` |
| P10 | **CONFIRMED** — specialize.py and decompose.py ran unchanged, exit 0; no code-shaped pass added; no programming specialization edge claimed (the Euclid pair are twins) | this note; `scripts/specialize.py` stdout |

**Disclosure 1 — GCD commutativity reordered the recursive call.** §4
wrote the authored template as `GCD(MOD(INTB, INTA), INTA)` (TheAlgorithms
recursive orientation). The matcher, having been told GCD is commutative,
emits the typed skeleton `GCD⟨?0:V, MOD⟨?1:V, ?0:V⟩⟩`. That is the
declaration doing the job it was declared for, not a template rewrite.
The two Euclid nodes still share one skeleton; Stein still does not.
The authored template in the seed is unchanged.

**Disclosure 2 — P5's "statement_id" wording was sloppy.** The
registered baseline said "token `gcd` in both `statement_id`s". The
ids are `programming.euclid.*` / `programming.stein.binary`; the gcd
token lives in `keywords` (and the function names). A literal reading
of the registered wording forms 0 pairs and is a vacuous baseline.
The check that was meant — and that is what a name-blind control
actually has — is the keyword. Precision 1.0 vs 1/3 stands on that
reading. The registered sentence is not edited.

**The GC4 movement, exactly.** Mean groundedness 0.774 → 0.779, exact
531 → 550, pattern 99 → 100, statements-with-constituents 222 → 226,
external 0.490 → 0.499, external lower 0.221 → 0.223. Not item 2's
denominator dilution: the Euclid pair are self-headed GCD recurrences
at groundedness 1.0 (same_corpus 3 + external 1 each); Stein is 0.455
(9 exact + 1 pattern over 22 considered). Absorption count floor holds
(387 > 4 × 86). Rate gap 0.164 → 0.156. min-family-1 recursive 250 →
261 over 128 statements. Conservative same_corpus_dominant 15 → 16.
`defines_head` gains GCD (twice) and STEIN. The fifth acknowledgment
in `tests/test_decompose_channels.py` is where this has to survive.

**Disclosure 3 — a contained `.py` is not a verdict.** The first
`verified_by_errors` python-tests path accepted any repository-contained
candidate module. A hand-edited node citing
`prover/pychecks/gcd_euclid_drop_abs.py` (the committed FAIL, not in
the manifest) would have passed the provenance rung. The seed-side
rule (P7) would not have emitted it, but the validator is the
fail-closed gate. The path now requires the artifact to be a key in
`prover/proof-artifact-manifest.json`, so the inherited ledger rung
can demand a PASS that claims this statement. Found in the capped
adversarial review, not by a test we had written in advance.
