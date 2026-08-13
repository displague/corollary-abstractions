# v0.10.0 — a real verifier, a corpus that grounds itself, and a blind baseline that still wins on count

The cycle that stopped asserting the bridge and built it: an external
verifier the repo can invoke, the first ingested statements carrying
machine-checked `verified_by`, programming as a discipline, one recorded
end-to-end session, and 251 authored ingested identities. It also produced
the most useful negative the project has had in three cycles.

Previous: [RELEASE-v0.9.0.md](RELEASE-v0.9.0.md) ·
Closed plan: [ROADMAP-v0.10.md](ROADMAP-v0.10.md) ·
Next: [ROADMAP-v0.11.md](ROADMAP-v0.11.md) ·
Triage & drift audit: [TRIAGE-v0.10.md](TRIAGE-v0.10.md) ·
Findings: [DISCOVERIES.md](DISCOVERIES.md)

---

## The headline finding: the operator bag still wins on count, and loses harder on precision

v0.9 asked the question this release had to answer: *a capability-blind
baseline beat the matcher on 221 curated nodes — does it still win when the
corpus is materially larger and machine-ingested?*

**Before.** On 221 hand-authored nodes, the operator-bag baseline (a
capability-blind bag-of-operators pairing) formed more twin pairs than the
structural matcher, which was recorded as an unresolved embarrassment.

**Now.** On 508 nodes, with 251 of them ingested from Lean-workbook, the bag
**still wins on pair count and loses harder on precision**:

| | pairs formed | precision |
|---|---|---|
| operator-bag baseline (blind) | **7,622** | 2.03% → **1.26%** (0.54% on ingested-only pairs) |
| structural matcher | **96** | **1.0** |

Scale did not rescue the baseline and did not rescue the matcher's count. It
separated them: the bag's advantage is volume, and volume got cheaper and
worse as the corpus grew, while the matcher formed 96 pairs and was right
about all of them. That is the honest shape of the result — **more pairs,
worse pairs** — and it is the number a reader should carry away.

**Demonstrate.** `python scripts/match_signatures.py` (twin ledger, 96 groups
across `{shape 35, typed 36, family 35, aliased 37, mirror 5}`); the baseline
comparison and its precision arithmetic are recorded in
`experiments/ANALYSIS.md` under the item-4 section.

### The second finding, which nobody designed for: ingestion compounds

**Before.** Ingested statements were assumed to accumulate — more rows, more
coverage, no claim about structure.

**Now.** Ingested statements **ground each other**. Item 5's session added a
second ingested node and the decomposition ledger immediately recorded it and
the first grounding each other's shared `2 ^ 30` subterm; item 4's first wave
reproduced that at scale with **614 `same_corpus` constituents inside the new
corpus**, and `^(2, 30)` now has a third owner (`lean_workbook_28978`). Exact
constituents went 552 → **1,235** while pattern stayed at 100.

This was not predicted. Item 5's registered prediction said the pins would
move by denominator dilution the way they had four times before; they moved
the other way. It is the seed of v0.11's forward-looking design — and it is
**not yet a measured curve**: no null model has been run, so "compounds" here
means "was observed twice at two scales", not "beats chance by X".

**Demonstrate.** `python scripts/decompose.py` — the `prior_corpus`
constituents on `numbertheory.ingested.lean_workbook_1041` and
`numbertheory.ingested.lean_workbook_22080`, both `^(2, 30)`, both carrying a
real shared discipline rather than the `mathematics` umbrella.

---

## Roadmap triage

**Shipped.**

- **Item 1 — four grammar heads**, each justified by the coverage delta it
  moved: trigonometry (SIN/COS/TAN), relational/predicate
  (EVEN/ODD/PRIME/IRRATIONAL + the `let`-desugaring fix), quantifier/binder
  (FORALL/EXISTS), and the embedded-quantifier atom-tree walk. Coverage on
  all three pinned sources: miniF2F 29.7% → **33.4%**, Lean-workbook
  64.1% → **71.5%**, Goedel-Pset 32.8% → **44.6%** (772,395 of 1,732,594).
  Zero matcher parse problems throughout.
- **Item 2 — the external verifier**, live with two backends behind one
  interface, and the first ingested `verified_by` grounded end to end.
- **Item 3 — programming as a first-class discipline**: three verified-code
  nodes, three PASS verdicts, and a structural-twin-over-code result against
  a capability-blind baseline.
- **Item 4 — authoring at scale, on hundreds**: the trusted append format
  plus a first wave of 251 parse-clean ground identities; 257 → 508 nodes,
  26 → 27 corpora, ledgers recomputed.
- **Item 5 — one real recorded session**, four legs, a node authored through
  the audited route.

**Shipped as negatives** (first-class results):

- The blind baseline still wins on count (above).
- **Fully ground statements are inert in all three ledger roles**: not
  generals, not specialize specifics, not decompose patterns. They
  participate only through shared subterms.
- **`specialize.py` hit a scale wall** — 87 minutes without writing a report
  on 508 nodes — because slot-free templates enumerate commutative subsets
  against every other node.
- **A guard was retired rather than re-pinned** (see Honest limits).

**Carried to [ROADMAP-v0.11.md](ROADMAP-v0.11.md).**

- Item 4's remainder: 12,681 unique-covered statements await a skeleton
  emitter. **Its dependant is named**: v0.11's self-grounding measurement.
- Item 6, the external benchmark — carried a **third** time, now with a
  named dependant instead of a silent carry.
- Item 7's lanes: proof-search depth and the groundedness gate.

---

## What changed, per area

**An external verifier the repo can actually invoke.**
*Before:* `verified_by` was offline and propositional-only; no program in the
repo could adjudicate a candidate statement. *Now:* `scripts/external_verifier.py`
is a transition authority with two live backends — `lean4` (the pinned
toolchain's binary invoked **directly by path**, so an absent toolchain is a
REFUSAL and never a download; PASS requires exit 0, no warnings, and an axiom
footprint inside `{propext, Classical.choice, Quot.sound}`) and `python-tests`
(`py_compile` → `mypy --strict` → `unittest` under an audit-hook sandbox that
the verdict calls a **discipline boundary, not a security boundary**).
Verdicts are committed, deterministic, never bare booleans, over
`{pass, fail, refused}`. *Demonstrate:*
`python scripts/external_verifier.py ledger`, and
`prover/verifier-verdicts/lean_workbook_1041.lean4.json` — axioms exactly
`[propext]`.

**The honesty boundary, stated and enforced.**
*Before:* nothing said what a passing check was worth. *Now:* **a passing
check certifies what it checks, not correctness in general** — written into
the design, repeated in each verdict's `checks` list, and load-bearing in the
corpus: `lean_workbook_10202` enters `formal` with **no** bridge because
Mathlib is outside the hermetic budget, and says so in its own node.
*Demonstrate:* `prover/verifier-verdicts/lean_workbook_10411.lean4.json` — a
committed **FAIL** for a statement that is true, ground, and still unprovable
under the shipped `exponentiation.threshold`. The verifier was not taught to
raise its own options.

**A recorded session, not a described one.**
*Before:* the harness had never been driven end to end on a real task.
*Now:* `experiments/harness_session.json` records four legs emitted from the
components' own structured objects: a need the corpus could not meet, the
verifier re-check, the WRITE gate's sixteen checks and the applied node; the
same need SOLVED by the next session; a same-shaped statement refused twice
(verifier `sorryAx`, then the gate at `theorem_closure`) with the tree
byte-identical; and the chicken probe abstaining in the dispatcher's own
words. *Demonstrate:* `python scripts/session_run.py --check`.

**Authoring into an existing corpus became possible.**
*Before:* the WRITE lane staged **new seed / new corpus pairs only** —
adding one statement to an existing corpus was impossible, so item 5 had to
create an entire corpus for a single node. *Now:* a trusted `append_nodes`
JSON format, parsed as data and never executed. *Demonstrate:* the 251-node
first wave in `data/lean_workbook/`, regenerated byte-identically by
`python scripts/check_regeneration.py`.

**The tracer's post-processor exists.**
*Before:* the code that turns `ExtractData`'s byte offsets into a
`verified_by` artifact lived only as a snippet in `PHASE1_NOTES.md`, so both
committed proof artifacts had been produced by code that no longer existed.
*Now:* `scripts/trace_to_triples.py`, with controls on attribution and a
refusal to write an empty artifact.

**Review economics.**
*Before:* adversarial review re-derived every mechanical check by hand
(~200–450k tokens per pass). *Now:* `scripts/verify_slice.py` runs
regeneration, ledger cleanliness, the matcher, audit fields, a per-row dual
pass, acknowledgment byte-intactness, guard arithmetic and the full suite,
and **names failing tests** rather than counting them. Review is then: run
the script, attack the design, sample rows, hunt one novel false positive.

---

## Discoveries of the cycle

Three, quoted from [DISCOVERIES.md](DISCOVERIES.md):

- **A `%` on ℕ decides without `propext`, where `∣` needs it.** A prediction
  that transferred one statement's axiom footprint to a different operator
  was wrong in the direction that makes the claim stronger — which is why a
  prediction must name the set, not the direction.
- **An audit hook that reads only `open`'s mode is not a write boundary.**
  The mode is `None` for every low-level open, so a sandboxed check wrote
  `__pycache__` into the repository while reporting PASS.
- **Fully ground statements are inert as generals, as specifics, and as
  patterns.** Their only structural participation is shared subterms — which
  is exactly why the self-grounding measurement is the right next question.

---

## Resolved from BACKLOG

- **The multi-corpus WRITE patch** — carried since v0.8, shipped as item 4's
  trusted append format.
- **`verified_by` for ingested arithmetic** — shipped as item 2's bridge.
- Newly filed and carried: `TOKEN_RE` missing standalone `<`/`>`;
  `specialize.py` minutes-scale at 508 nodes; the skeleton emitter for the
  12,681 remainder; verdict-backed ingestion as a rule rather than a
  precedent.

---

## Honest limits carried forward

- **"Thousands of ingested nodes" is not what shipped.** The first wave is
  251 parse-clean identities out of 302 predicted; 51 failed `TOKEN_RE` on
  standalone `<`/`>` already present in RELATIONS. The 12,681-statement
  remainder is unauthored.
- **Item 4 merged without the independent adversarial review** every other
  slice in this cycle received — the pass that found a real defect six times
  out of six. The slice self-reported its misses and the mechanical harness
  is green; anything a later review finds becomes a v0.11 fix. The release
  does not claim seven-for-seven review coverage.
- **A guard was retired, not satisfied.** The absorption rate-gap pin
  (`< 0.12`) moved in four consecutive slices — 0.164, 0.156, 0.159, 0.490 —
  and is now retired with its rationale recorded in
  `tests/test_decompose_channels.py`: it is a ratio whose denominator the
  corpus controls, so self-grounding ingestion moves it every time the corpus
  succeeds. The **count floor** it backed up has never weakened and
  strengthened to **5.31:1** (457 > 4 × 86); that is what refutes the
  retracted "absorption concentrates cross-discipline credit" inference.
- **Ingestion compounds is an observation, not a measurement.** Two scales,
  no null model. `docs/DESIGN-self-grounding-ingestion.md` registers the null
  and predictions S1–S4 *before* the data; none of them is adjudicated here.
- **The corpus is still formal-without-bridge at scale.** 21 `verified_by`
  links (18 `lean4`, 3 `python-tests`) across 508 nodes; the 251 ingested
  identities carry none.
- **v0.9's findings were never parked in DISCOVERIES.md** — caught by this
  cycle's drift audit. v0.10's are added here; v0.9's gap is recorded rather
  than backfilled from memory.

---

## Assets

**No model checkpoints ship with this release, and none is claimed.** Every
v0.10 result is symbolic: committed ledgers, committed verdicts, and a
committed session transcript. The artifacts a reader should check are in the
repository, not attached to the tag:

| artifact | the claim it evidences |
|---|---|
| `prover/verifier-verdicts/*.json` | the verifier ran, on pinned inputs, with the recorded axiom footprints — including one FAIL |
| `prover/ingested_triples.json`, `prover/session_triples.json` | real traced Lean transitions, digest-pinned in the manifest |
| `experiments/harness_session.json` | the recorded session, re-verifiable with `--check` |
| `experiments/*_coverage.json` | the grammar-reach numbers on all three pinned sources |
| `reports/*.json` | the twin, specialization, decomposition and correspondence ledgers at 508 nodes |

(The trained lanes from v0.6–v0.8 remain seed-reproducible-only, as
v0.8 and v0.9 recorded.)

---

## Reproduce

From a fresh clone (no GPU, no network beyond the pinned sources):

```
python scripts/check_regeneration.py    # 20 seeds regenerate byte-identically
python scripts/validate_nodes.py        # 508 nodes / 27 corpora green
python scripts/match_signatures.py      # twin ledger (96 groups)
python scripts/decompose.py             # groundedness channels
python scripts/proof_correspondence.py  # 18 lean4 links adjudicated
python scripts/external_verifier.py ledger   # every committed verdict re-checked
python scripts/session_run.py --check   # the recorded session's record re-verified
python -m unittest discover -s tests    # 1084 tests
```

The Lean-backed checks need the pinned toolchain (`leanprover/lean4:v4.32.2`)
and skip cleanly without it. The coverage instruments regenerate from the
committed extracts; re-deriving them from source needs the SHA-pinned
archives via `scripts/fetch_sources.py`.
