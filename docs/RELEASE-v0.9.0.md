# v0.9.0 — Ingestion coverage: the grammar's reach, measured on real formal math (and two walls it hit)

Baseline: [v0.8.0](RELEASE-v0.8.0.md). Plan of record:
[ROADMAP-v0.9.md](ROADMAP-v0.9.md) (closed); carried work and the next increment:
[ROADMAP-v0.10.md](ROADMAP-v0.10.md). The argument this cycle executed on:
[DESIGN-corpus-scale-and-programming.md](DESIGN-corpus-scale-and-programming.md).
Findings: [DISCOVERIES.md](DISCOVERIES.md). Adjudications and numbers:
[experiments/ANALYSIS.md](../experiments/ANALYSIS.md) (§§ "miniF2F / Lean-workbook /
Goedel-Pset grammar-coverage"). Public narrative:
[How much of it fits](blog/how-much-of-it-fits.md).

## The headline: the honest reach of the grammar on real formal math is about a third — measured, not asserted

v0.8 answered *method*. v0.9's headline was to make the corpus non-toy by
ingestion. The design doc set the honest first deliverable explicitly: **a
coverage number — what fraction of a real formal source expresses in the corpus
grammar at all — before any claim about scale.** This release delivers that, and
the roadmap's own item-1 acceptance names exactly this outcome: *"an honest
grammar-coverage measurement if the grammar's reach is the bottleneck."* It is.

**Before.** The corpus was 221 hand-authored nodes across 22 disciplines. Whether
the matcher / specializer / analogy claims survive contact with an uncontrolled,
larger body of formal math was unknown — untested outside the lab.

**Now.** A shared, adversarially-hardened coverage instrument
(`scripts/grammar_coverage.py`) has measured three real, digest-pinned formal
sources. The full-statement coverage — the fraction expressible as a conditional
Mathematical Statement Node `IMPLIES(MEET(hyps), goal)` — is:

| source | size | full-statement covered | duplicate rate | unique covered |
|---|---|---|---|---|
| miniF2F (Lean 3) | 488 | **145 = 29.7%** | — | 145 |
| Lean-workbook-proofs (Lean 4) | 29,750 | **19,077 = 64.1%** | 37.9% | ≥ 11,189 |
| Goedel-Pset-v1 (Lean 4) | **1,732,594** | **567,429 = 32.8%** | 34.6% | 386,375 |

**Demonstrate.** From the committed extracts, byte-for-byte:
`PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/ingest_minif2f.py coverage`
and `… ingest_lean_workbook.py coverage` reproduce the miniF2F and Lean-workbook
numbers from the committed statement extracts with no network; the 1.73M
Goedel-Pset number regenerates from its four pinned parquets. Each
`experiments/*_coverage.json` carries its own reason breakdown.

**The reading.** Two competition/olympiad-derived sources (miniF2F, Goedel-Pset)
land near **30%**; the one hand-curated inequality set (Lean-workbook) is the
outlier at 64%. So the grammar's honest reach on *uncontrolled* formal math is
**~a third** — and that is the finding the closed world of 221 nodes could never
produce. The untranslatable remainder is a *prioritized grammar-extension
backlog*, confirmed across three independent sources: a **quantifier/binder
head**, a **first-class function slot**, **indexed aggregation** (∑ ∏), a
**relational/predicate head** (at 1.73M the single largest gap is
`no_relation_in_goal`, 22% — model-formalized word problems are often not
(in)equations at all), and a **carrier-honest number field** (integer vs real
division, rational powers, the modulo/divides residue).

## Roadmap triage

**Shipped:**
- **Item 1 (make the corpus non-toy, by ingestion)** — shipped as the honest
  coverage measurement its acceptance clause allows. Three sources, reproducible,
  provenance-pinned by URL/SHA-256 and HF commit revision. The
  twin/specialization/decomposition ledgers were recomputed and are stable on the
  221-node graph (no enlarged graph, because the grammar's reach — not authoring
  effort — is the bottleneck).

**Shipped as a negative / an architectural finding (first-class results):**
- **`verified_by`-grounded ingestion is architecturally blocked, and now we know
  exactly why.** Verification in this repo is entirely offline — a manifest
  lookup plus a parse of a committed Lean *transition-row* artifact — with **no
  Lean toolchain**, and the correspondence rung translates only the
  **propositional fragment** (not/and/or/implies over `Prop`). Lean-workbook /
  Goedel-Pset goals are arithmetic, so they are UNTRANSLATABLE by that rung.
  Grounding a `verified_by` for ingested arithmetic therefore requires building a
  Lean-proof→transition-row extractor *and* an arithmetic correspondence — which
  is the item-2 external-verifier work. This is why no nodes were authored with
  `verified_by` links this cycle; doing so honestly is a v0.10 prerequisite, not
  an oversight.

**Carried to [ROADMAP-v0.10.md](ROADMAP-v0.10.md):**
- Item 1's *authoring* half (ingested nodes into the graph) — carried, because
  honest authoring wants either the `verified_by` path above or an explicit
  `formal`-without-bridge decision, and because rendering model-generated goals to
  zero-parse-problem templates is itself a build.
- Item 2 (programming as a first-class discipline) — not started.
- Item 3 (drive the open harness on a real session) — not started.
- Item 4 (external benchmark) and Item 5 (proof-search depth, multi-corpus WRITE
  patch, groundedness gate) — carried.
- Item 6 (physics/affect/oscillation/visual rungs) — remain parked.

## What changed, per area

**A shared coverage instrument, `scripts/grammar_coverage.py`.**
- *Before:* no way to ask "does this formal statement express in the corpus
  grammar?" of an external source.
- *Now:* a dialect-aware (Lean 3 + Lean 4) classifier that reduces a statement to
  a head-algebra skeleton and reports COVERED or the first construct with no head.
  A head counts as supported **only if a node in `data/*/nodes.json` carries it**
  — a test asserts this against the corpus, not memory.
- *Demonstrate:* `experiments/*_coverage.json` `grammar.supported_heads` vs
  `explicit_gaps_no_head_in_corpus`; `tests/test_minif2f_ingest.py`
  `CorpusHeadProvenance`.

**Three digest-pinned sources + a reproducibility contract.**
- *Before:* `data_sources/manifest.json` pinned only in-use lexical archives.
- *Now:* miniF2F (git commit + per-file SHA-256), Lean-workbook-proofs and
  Goedel-Pset-v1 (HF **commit revision** + parquet SHA-256, both MIT). HF fetches
  are **refused without a pinned revision** and SHA-verified after download
  (`scripts/fetch_sources.py`).
- *Demonstrate:* `python scripts/fetch_sources.py --verify`; the `files[]` SHA
  pins and `hf_revision` fields in `data_sources/manifest.json`.

**The scale test, aggregate-only.**
- *Before:* the largest measured formal set was 30k.
- *Now:* Goedel-Pset-v1 at **1.73M** statements, single-pass, via
  `scripts/ingest_goedel_pset.py`. A 1.73M-row extract would be ~300 MB, so this
  source commits only the small aggregate `experiments/goedel_pset_coverage.json`
  — which is **self-checking**: it carries false-positive audit counts
  (`covered_foreign_glyph_count`, `covered_carrier_residual_count`), both 0, and a
  test asserts it.
- *Demonstrate:* `experiments/goedel_pset_coverage.json` `audit` block;
  `tests/test_goedel_pset.py` `SelfCheckingAudit`.

**The classifier was hardened three times by adversarial review, each a correction
downward — and that is the honest core.**
- *Modulo/divides are gaps, not heads* (`%`, `∣` have no corpus head — the only
  `MOD` in `data/` is morphology's linguistic *modifier*): −86 miniF2F FPs.
- *Carrier-awareness:* over ℕ/ℤ, `/` is `Nat.div`/`Int.div` (floor), `-` is monus,
  `x^(1/3)` is `x^0` — the extract records each variable's carrier, and a
  `/`/`-`/`⁻¹` with no field signal over an integer carrier is a gap. This alone
  moved Lean-workbook 68.0% → 64.1% and miniF2F 31.4% → 29.7%.
- *Scale-surfaced glyph FPs* (`×`, `•`, `⊓`, `ℐ`/`𝕀`, `ℵ`, `⟨…⟩`) and an
  *arity-blind two-argument `log b x`* (base-b log, no head) — both caught only
  because 1.73M contains what 30k does not; both blocked, with regressions.
- *Demonstrate:* the "corrected … → …" notes in `experiments/ANALYSIS.md`; the
  regression tests in `tests/test_*_ingest.py` and `tests/test_goedel_pset.py`.

## Discoveries of the cycle

See [DISCOVERIES.md](DISCOVERIES.md). The two load-bearing ones:
- **"The corpus carries head X" is a claim to verify node-by-node, never assert.**
  Two review passes found the classifier claiming heads (`%`, `∣`) the corpus does
  not have, and treating `/`/`-` as field operations when the carrier was ℕ/ℤ.
  The reusable rule: a supported head must be checked against the actual corpus and
  the actual operation, not the surface symbol.
- **Offline propositional-only verification cannot ground an ingested arithmetic
  `verified_by`.** The bridge from a stated theorem to a machine-checked proof is a
  separate lane, and it currently reaches only propositional logic — the precise
  shape of the wall the next cycle has to climb.

## Honest limits carried forward

- **No nodes were authored into the graph.** The corpus is still 221 nodes / 22
  disciplines. The coverage measurement is the deliverable; the enlarged graph is
  not — deliberately, because the grammar's reach is the bottleneck.
- **`verified_by` for ingested arithmetic is ungroundable today** (no Lean
  toolchain; propositional-only correspondence). This gates item-1 authoring and
  overlaps item 2.
- **Items 2 (programming discipline) and 3 (a real harness session) did not
  start.** They are the substance of v0.10.
- **The 32.8%/64.1% numbers carry a disclosed residual:** a non-elaborating
  classifier cannot always distinguish a real division inside a field-coerced
  subexpression from a `Nat.div`, so a few mixed-carrier statements may still be
  over-counted — the true numbers are a hair lower, never higher.

## Assets

**This release ships no new model-weight assets.** Its claims rest on data and a
measurement, not a trained model: the faithful, reproducible artifacts are the
committed coverage measurements and their pinned sources —

- `experiments/{minif2f,lean_workbook,goedel_pset}_coverage.json` — the three
  coverage numbers, each self-describing; regenerable from the pinned sources.
- `data_sources/derived/{minif2f,lean_workbook}/statements.json` — the committed
  statement extracts (Apache-2.0 / MIT, attribution vendored) that make the two
  smaller numbers regenerate with no network.
- `data_sources/manifest.json` — the URL/SHA-256/revision pins that make every
  source re-fetchable and byte-verifiable.

External archives (miniF2F Lean files, the Lean-workbook / Goedel-Pset parquets)
are gitignored and never redistributed; the manifest is their reproduction
channel.

## Reproduce (from a fresh clone, PYTHONIOENCODING=utf-8, shared .venv)

```
# the two small sources regenerate from committed extracts, no network:
.venv/Scripts/python.exe scripts/ingest_minif2f.py coverage
.venv/Scripts/python.exe scripts/ingest_lean_workbook.py coverage
# the 1.73M scale test needs its pinned parquets first (MIT, ~828 MB):
.venv/Scripts/python.exe scripts/fetch_sources.py --fetch hf-goedel-pset-v1
.venv/Scripts/python.exe scripts/ingest_goedel_pset.py
# ledgers + suite (corpus unchanged at 221 nodes / 22 disciplines):
.venv/Scripts/python.exe scripts/check_regeneration.py
.venv/Scripts/python.exe scripts/validate_nodes.py
.venv/Scripts/python.exe -m unittest discover -s tests -p "test_*.py"   # 848 green
```
