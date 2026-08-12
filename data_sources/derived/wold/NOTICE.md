# WOLD derived extract — attribution

`lexicon.json` in this directory is a **derived work**: the 1,460 core LWT
meanings (concept list Haspelmath-2009-1460) of the World Loanword Database
with word forms for a declared six-vocabulary subset (English, Dutch,
Romanian, Japanese, Vietnamese, Mandarin Chinese), extracted deterministically
by `scripts/ingest_wold.py` from the CLDF tables of the pinned lexibank/wold
release.

- **Upstream:** lexibank/wold — <https://github.com/lexibank/wold>, the CLDF
  dataset of the World Loanword Database (<https://wold.clld.org>).
- **Release pinned:** `v4.2` (archive SHA-256 in `data_sources/manifest.json`).
- **License:** CC BY 4.0 — the archive's `LICENSE` (the full Creative Commons
  Attribution 4.0 International text) is vendored alongside this file as
  `LICENSE`; the archive's `metadata.json` declares `"license": "CC-BY-4.0"`.

**Required citations** (CC BY 4.0 attribution; carried verbatim from the
manifest entry and load-bearing for any reuse of this extract):

> Haspelmath, Martin & Tadmor, Uri (eds.) 2009. World Loanword Database.
> Leipzig: Max Planck Institute for Evolutionary Anthropology.
> https://wold.clld.org (CLDF dataset lexibank/wold v4.2)

> CLDF: Forkel et al. 2018, Cross-Linguistic Data Formats, Scientific Data
> 5:180205.

**Tier:** empirical only (house rule for lexical sources): this lexicon never
grounds a frame verdict and never appears in `verified_by`. Its only current
use is the measured reach number in `experiments/wold_reach.json` and the
"WOLD lexicon" section of `experiments/ANALYSIS.md`; no runtime path consumes
it yet.
