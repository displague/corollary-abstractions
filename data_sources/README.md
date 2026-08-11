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
  (gitignored, never printed). Gated sets (e.g. GAIR/MathPile) need a human to
  accept the form on the dataset page first, and any use must cite the authors.
- **git** sources (miniF2F) are cloned manually; pin the commit SHA.

## Discipline

- Licensed/sample data is for **local research use** and is never redistributed
  through this repo.
- WordNet and any lexical/semi-formal source enters the ontology at `empirical`
  only — it never grounds a frame verdict and never appears in `verified_by`.
- To add a source: append an entry to `manifest.json` (URL + license + purpose),
  fetch it, then pin the SHA-256 the fetch reports.
