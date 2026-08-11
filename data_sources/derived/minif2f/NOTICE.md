# miniF2F derived extract — attribution

`statements.json` in this directory is a **derived work**: the theorem
signatures (name, binders, hypotheses, goal) of the miniF2F Lean-3 benchmark,
extracted deterministically by `scripts/ingest_minif2f.py`. Proofs are omitted.

- **Upstream:** miniF2F — <https://github.com/openai/miniF2F>
- **Commit pinned:** `4e433ff5cadff23f9911a2bb5bbab2d351ce5554`
  (`lean/src/test.lean`, `lean/src/valid.lean`; SHA-256s in
  `data_sources/manifest.json`).
- **Copyright:** © 2021 OpenAI. Authors: Kunhao Zheng, Kudzo Ahegbebu,
  Stanislas Polu, David Renshaw, OpenAI GPT-f.
- **License:** Apache License 2.0 — the full text is vendored alongside this
  file as `LICENSE`, satisfying Apache-2.0 §4(a). No NOTICE file was present in
  the upstream `lean/` tree; this file records the attribution required by §4(c)
  for the derivative.

The extract is used only to measure how much of the benchmark expresses in this
project's corpus grammar (see `experiments/minif2f_coverage.json` and the
"miniF2F grammar-coverage" section of `experiments/ANALYSIS.md`).
