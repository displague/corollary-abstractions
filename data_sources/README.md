# Data sources

External corpora used or staged for v0.9 ingestion. The archives themselves are
**gitignored** (`data_sources/archives/`); reproducibility comes from
`manifest.json`, which pins each source URL and SHA-256.

## Workflow (follow this for every new corpus)

```console
python scripts/fetch_sources.py --list                 # what is registered
python scripts/fetch_sources.py --adopt ~/Downloads    # bind already-downloaded files by SHA
python scripts/fetch_sources.py --fetch                # download missing direct sources, verify SHA
python scripts/fetch_sources.py --fetch hf-proofcheck-prooflang   # HF datasets via the hf CLI
python scripts/fetch_sources.py --verify               # re-check local archives against pinned SHAs
```

- **Direct** sources download over HTTPS and are verified against the pinned
  SHA-256; a mismatch is refused and not saved.
- **HF** datasets fetch through the `hf` CLI, using `HF_TOKEN` from `.env`
  (gitignored, never printed). A fetch is **refused without a pinned
  `hf_revision`** (a bare `hf download` / `load_dataset` pulls the moving `main`
  and can't be reproduced); the pinned per-file SHA-256s are re-verified after
  download. Gated sets (e.g. GAIR/MathPile) need a human to accept the form on
  the dataset page first, and any use must cite the authors.
- **git** sources (miniF2F) are cloned manually; pin the commit SHA.

## Ingestion (source → committed derived extract → measurement)

The archive is gitignored, so an ingestion transform commits a **derived
extract** (`data_sources/derived/`, license permitting) and reads *that*, so the
downstream measurement regenerates in CI without the archive. miniF2F is the
first worked example:

```console
# stage 1 (needs the pinned archive; SHA-verified): Lean -> committed extract
python scripts/ingest_minif2f.py extract
# stage 2 (CI-regenerable from the committed extract): grammar-coverage measurement
python scripts/ingest_minif2f.py coverage
```

A second source, `Goedel-LM/Lean-workbook-proofs` (Lean 4, MIT, 29,750 proof-
carrying theorems), follows the same shape via `scripts/ingest_lean_workbook.py`
(extract needs pyarrow to read the pinned parquet; coverage is stdlib-only and
also reports a duplicate rate). Both share the classifier in
`scripts/grammar_coverage.py`.

A third source, `Goedel-LM/Goedel-Pset-v1` (Lean 4, MIT, **1.73M** statements,
`sorry` proofs), is the SCALE test via `scripts/ingest_goedel_pset.py`. Because a
1.73M-row extract would be ~300 MB, this one is **aggregate-only**: the 4 pinned
parquets are the reproducibility anchor and only the small
`experiments/goedel_pset_coverage.json` is committed (with a self-checking
false-positive audit baked in). It is not stdlib-CI-regenerable; reproduce it
manually with `python scripts/fetch_sources.py --fetch hf-goedel-pset-v1` then
`python scripts/ingest_goedel_pset.py`.

- Stage 1 verifies each Lean file against the SHA-256 pinned in `manifest.json`
  and refuses to extract from unpinned bytes; the extract carries the source's
  Apache-2.0 attribution.
- Stage 2 is a pure function of the committed extract and is guarded
  byte-for-byte by a regeneration test. See the coverage write-up in
  `experiments/ANALYSIS.md` (§ "miniF2F grammar-coverage").
- Committed JSON in `derived/` and `experiments/` is pinned `text eol=lf` in
  `.gitattributes` so the working tree stays LF regardless of `core.autocrlf`.

## Discipline

- Licensed/sample data is for **local research use** and is never redistributed
  through this repo.
- WordNet and any lexical/semi-formal source enters the ontology at `empirical`
  only — it never grounds a frame verdict and never appears in `verified_by`.
- To add a source: append an entry to `manifest.json` (URL + license + purpose),
  fetch it, then pin the SHA-256 the fetch reports.
