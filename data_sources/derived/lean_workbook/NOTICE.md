# Lean-workbook-proofs derived extract — attribution

`statements.json` in this directory is a **derived work**: the theorem
signatures (name, binders, hypotheses, goal) of the Goedel-LM
`Lean-workbook-proofs` dataset, extracted deterministically by
`scripts/ingest_lean_workbook.py`. The proofs are omitted (retrievable by
`problem_id` from the pinned parquet).

- **Upstream:** <https://huggingface.co/datasets/Goedel-LM/Lean-workbook-proofs>
- **Revision pinned:** `b731852af8d8ab11498fda27bce9020738c01c59`
  (`data/train-00000-of-00001.parquet`; SHA-256 in `data_sources/manifest.json`).
- **License:** MIT (upstream `LICENSE` vendored beside this file).
- **Provenance of the proofs:** Goedel-Prover — Lin et al., 2025,
  *"Goedel-Prover: A Frontier Model for Open-Source Automated Theorem Proving"*,
  arXiv:2502.07640. The problems derive from the **Lean Workbook** project.

The extract is used to measure how much of the dataset expresses in this
project's corpus grammar (see `experiments/lean_workbook_coverage.json` and the
"Lean-workbook grammar-coverage" section of `experiments/ANALYSIS.md`), and — in
a later phase — to author covered statements as nodes whose retained proof
grounds a `verified_by` link.
