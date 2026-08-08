# Quick reference

> The template-CLI workflow formerly documented here is deprecated —
> corpora are seed-owned (`scripts/seed_<discipline>.py`) and
> `check_regeneration.py` flags direct JSON edits as drift.

Authoring: see [ADDING_FORMULAE.md](ADDING_FORMULAE.md).
Verify cycle: seed -> check_regeneration -> validate_nodes ->
match_signatures -> decompose -> specialize.
Findings go to [DISCOVERIES.md](DISCOVERIES.md); friction to
[BACKLOG.md](BACKLOG.md); releases via the `release` skill.
