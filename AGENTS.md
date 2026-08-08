# AGENTS.md

Project-level agent instructions for `corollary-abstractions`.

## Objective

Cross-discipline ontology of mathematical statements (21 disciplines,
seed-generated corpora) + symbolic matchers (twins, specializations,
decomposition) + a measured experiment suite showing tiny models do
compositional work when every closed-form operation lives outside the
weights. Current release notes: `docs/RELEASE-v0.3.0.md`; plan:
`docs/ROADMAP-v0.4.md`.

## Ground rules

- **Seeds are the source of truth.** Never edit `data/*/nodes.json`
  directly — edit `scripts/seed_<discipline>.py` and regenerate.
  `scripts/check_regeneration.py` enforces byte-identical coherence and
  flags orphan corpora. Full authoring guide: `docs/ADDING_FORMULAE.md`
  (grammar/schema constraints digested from `docs/BACKLOG.md`).
- After corpus or schema edits, run: `check_regeneration.py`,
  `validate_nodes.py` (merged graph), `match_signatures.py` (zero parse
  problems / slot gaps required), `decompose.py`, `specialize.py` —
  all with `PYTHONIOENCODING=utf-8` on Windows.
- Register twin predictions in seed docstrings before running the
  matcher; adjudicate honestly (fired and missed are both results).
  Park findings in `docs/DISCOVERIES.md`, friction in `docs/BACKLOG.md`.
- Commits carry the why (and how the path was determined), not just the
  what. Work in `.worktrees/` branches; merge to main and push promptly.
- Epistemic statuses are symbolic and closed-form
  (`docs/DESIGN-epistemic-ladder.md`); `verified_by` links statements to
  machine-checked Lean proofs (`prover/`).

## Skills

- `.claude/skills/release/` — the release process (ledger refresh, doc
  rotation, tag, GitHub release with model assets).
- `.github/skills/corpus-authoring/` — corpus authoring via seeds (for
  Copilot/VS Code agents; mirrors ADDING_FORMULAE.md).
- `.github/skills/schema-and-links-governance/` — schema/link-integrity
  rules.
- Repository-wide Copilot guidance: `.github/copilot-instructions.md`.
