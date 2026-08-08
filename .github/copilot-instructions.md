# Copilot instructions — corollary-abstractions

- Corpora under `data/*/nodes.json` are GENERATED. Never edit them
  directly; edit `scripts/seed_<discipline>.py` and regenerate
  (`docs/ADDING_FORMULAE.md` is the authoring guide;
  `scripts/check_regeneration.py` enforces coherence).
- Validate every corpus/schema change:
  `python scripts/check_regeneration.py && python scripts/validate_nodes.py`
  then `match_signatures.py` (zero parse problems / slot-schema gaps).
- Naming: statement ids `prefix.topic.name` with an underscore-free
  first segment; ALLCAPS template slots declared in slot_schema; call
  heads are matched literally — reuse established heads where honest.
- Commit messages explain why and how, not just what.
- Experiments live in `experiments/` (seed-deterministic; results in
  `experiments/ANALYSIS.md`); model checkpoints are distributed as
  GitHub release assets, never committed.
