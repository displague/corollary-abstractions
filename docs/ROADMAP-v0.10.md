# v0.10 roadmap — extend the grammar, build the verifier, then author

v0.9 measured the grammar's reach on real formal math and found it is about a
third, with a precise, three-source-confirmed list of the heads that are missing
and a hard architectural wall: `verified_by` for ingested arithmetic cannot be
grounded, because verification is offline and propositional-only. v0.10 turns
those two findings into the two builds that unblock actual corpus growth — and
only then authors nodes. Everything is downstream of
[RELEASE-v0.9.0.md](RELEASE-v0.9.0.md) and
[DESIGN-corpus-scale-and-programming.md](DESIGN-corpus-scale-and-programming.md).

The benchmark rule is unchanged: no external LLM-benchmark comparison until the
system accepts open requests *and* the benchmark's contract maps honestly onto the
capability built.

## 1. Extend the grammar to the heads the coverage measurement demanded (headline)

The v0.9 remainder is a prioritized backlog, confirmed across miniF2F,
Lean-workbook, and Goedel-Pset. Grow the head-algebra to reach it, each head
justified by a coverage delta, not by taste.

- A **relational / predicate head** (the single largest 1.73M gap:
  `no_relation_in_goal`, 22% — bare predicates and definitional goals).
- A **quantifier / binder head** (∀/∃ in the goal: ~11% + ~8% on Goedel-Pset).
- A **first-class function slot** (unknown-function application, ~14%).
- **Indexed aggregation** (∑ ∏, ~7%).
- A **carrier-honest number field** — integer vs real division as distinct heads,
  rational powers, and the modulo/divides residue — so these become *expressible*
  rather than *gaps*, without reintroducing the `Nat.div`-as-real over-count v0.9
  fixed.

Acceptance: each new head lands with the coverage number it moves on all three
committed sources (re-run the instrument; the delta is the evidence), and the
matcher parses every resulting template with zero parse problems / zero slot gaps.

## 2. An external verifier, and the honest `verified_by` path (headline)

v0.9 proved the bridge from a stated theorem to a machine-checked proof reaches
only propositional logic today. Build the missing half.

- Stand up an **external verifier** the repo can actually invoke — a
  type-checker + unit tests to start (Lean is the follow-on) — as the transition
  authority, the role live Lean already plays for the proof curve.
- Either (a) extend the correspondence rung to the **arithmetic fragment** and
  wire a Lean-workbook proof → committed transition-row artifact → manifest pin,
  so an ingested arithmetic theorem can earn a real `verified_by`; or (b) make the
  explicit, documented decision to author ingested theorems as `formal`
  *without* a `verified_by` bridge, and say so at every node.

Acceptance: one ingested statement carries a `verified_by` grounded end-to-end
through the real verifier (or a written, node-level record of why it is
`formal`-without-bridge), with the honesty boundary intact — a passing check
certifies what it checks, not correctness in general.

## 3. Programming as a first-class discipline (carried from v0.9 item 2)

**SHIPPED** on `feature/v010-programming` — 3 verified-code nodes
(253 → 256 / 25 disciplines), `python-tests` may ground `verified_by`
(PROVEN stays lean4), Euclid pair typed-twins against a token-`gcd`
baseline (precision 1.0 vs 1/3), drop-abs FAIL recorded and cited by
nothing. Design + adjudication: `docs/DESIGN-programming-discipline.md`.

The architecture runs the same operations over code with the verifier of item 2
swapped in. AST → canonical form → structural address → pointer residual →
external verifier. A verified code snippet becomes nodes; structural-twin
recovery, specialization, and propose→verify→repeat synthesis follow with no new
machinery.

Acceptance: one verified-code node type end-to-end, one structural-twin-over-code
result against a capability-blind baseline, one synthesis-or-debug transaction
adjudicated by the external verifier. **MET.**

## 4. Author the covered subset, then recompute the ledgers on the enlarged graph
   (carried from v0.9 item 1's authoring half)

With items 1–2 in hand, author the covered statements (starting from the
~11,189 unique-covered Lean-workbook set) as conditional Mathematical Statement
Nodes via the PROVEN-WRITE seed→regenerate route, and re-run the
twin/specialization/decomposition ledgers on the materially larger graph.

**PARTIAL** on `feature/v010-item4` — first wave 251 parse-clean unique-covered
ground identities (257 → 508 / 27 corpora), formal-without-bridge. Operator-bag
baseline still wins on pair count (7,622 vs 96) and loses harder on precision
(2.03% → 1.26%; 0.54% ingested-only). Ingested layer grounds itself: 614
same_corpus constituents inside the new corpus; `2^30` now has a third owner.
Trusted append format (Slice A) shipped. Remainder of the 12,681 waits on a
skeleton emitter. Design + adjudication: `docs/DESIGN-item4-authoring.md`,
`docs/DESIGN-write-append.md`.

Acceptance: a real ingested source authored to a materially larger node count,
provenance intact, reproducible byte-for-byte, and the ledgers recomputed and
reported — especially whether any capability-blind baseline that won on 221
curated nodes still wins on thousands of ingested ones. **MET on hundreds,
not thousands.**

## 5. Drive the open harness on a real session (carried from v0.9 item 3)

Drive at least one real ingestion-or-code session end-to-end through the harness
(boot matrix → need dispatch → open authoring/WRITE), degrading to ASK where the
request is unparseable. The "why did the chicken cross the road?" prompt is a good
adversarial probe that fluency stays at the edge and never earns a `verified_by`.

Acceptance: one real, non-trivial session recorded end-to-end that produces or
revises a node through the audited route, with the ASK-not-guess contract holding.

## 6. An external benchmark the architecture can win because of its design
   (carried from v0.9 item 4)

Design one external, independently interesting benchmark the system can win
*because of* the architecture — structural-analogy recovery across formalized
papers, or verified code completion on a held-out library with specs. It must
force the corpus to grow (depends on items 1–4) and map its contract honestly
before any comparison is licensed.

## 7. Carried-open lanes and parked rungs

- **Proof-search curve depth**, the **existing-multi-corpus WRITE patch**, and the
  **groundedness gate** carry forward (v0.9 item 5), now fed by items 1–4.
- Physics / affect / oscillation / frequency-domain / rotation rungs and the
  visual arms remain **parked** until the core graph is non-toy.

## 8. Governance carries forward

- Every claim beats a capability-blind baseline; negatives are first-class.
- Independent adversarial review at every trust boundary — the coverage
  instrument's review found real over-counts three times; keep that.
- Register predictions before adjudication; attach corrections rather than edit.
- Hybrid only at the edges: a larger model may propose or front-end, never own
  structure or equality.

## Release gate

v0.10 is ready only if it contains:

- at least one new grammar head, each with the coverage delta it moves on the
  three committed sources, and zero matcher parse problems;
- one ingested statement `verified_by`-grounded end-to-end through a real external
  verifier, or a documented `formal`-without-bridge authoring decision;
- one verified-code node type end-to-end with an external verifier, and one
  structural-twin-over-code result against a blind baseline;
- a real ingested source authored to a materially larger corpus, provenance
  intact, reproducible byte-for-byte, with the ledgers recomputed and reported;
- one real end-to-end harness session that produces or revises a node;
- updated assets whose notes explain winners, losers, and controls;
- the complete seed/schema/matcher/specializer/decomposer/test suite green.
