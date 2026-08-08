# AGENTS.md

Project-level agent instructions for `corollary-abstractions`.

## Objective

Cross-discipline ontology of mathematical statements (21 disciplines,
seed-generated corpora) + symbolic matchers (twins, specializations,
decomposition) + a measured experiment suite showing tiny models do
compositional work when every closed-form operation lives outside the
weights. Release notes and roadmaps live in `docs/RELEASE-v*.md` and
`docs/ROADMAP-v*.md`; use the highest-versioned files as the current
coordinates, and honor any closure banner when consulting older plans.

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

## The working method (any phase, any agent)

These generalize past the current scope of work; they are how this
project moves regardless of whether the phase is corpus growth,
experiments, tooling, prover, or docs.

1. **Orient from the four coordinates.** `docs/ROADMAP-v<current>.md`
   (what's planned and its live status), `experiments/ANALYSIS.md`
   (every result with its numbers), `docs/DISCOVERIES.md` (what was
   found), `docs/BACKLOG.md` (known friction with evidence). Together
   they answer where the project is; read them before proposing work.
2. **Predict, then adjudicate.** Register expectations in writing
   (seed docstrings, commit messages, roadmap items) BEFORE running the
   tool that judges them. Fired and missed are both reportable results;
   a falsified prediction is recorded as prominently as a confirmed
   one, and two public retractions are part of this repo's record.
3. **Vacuity-check every test.** Before claiming a split or metric
   stresses a capability, run the cheapest capability-blind baseline;
   if it scores perfectly, the test is vacuous for the claim. No
   single-seed comparisons where claims are made.
4. **Closed forms stay symbolic.** Anything with an exact answer
   (parsing, equality, status, addresses, lookups) is computed by code,
   never learned or improvised; models and judgment own only the
   genuinely graded residual. This applies to process too: statuses,
   coherence, and reciprocity are checked by tools, not by care.
5. **The discipline audits itself.** The same standards apply to our
   tooling as to the corpus — declared tables need justifying
   citations, uncited numbers get flagged as unfalsifiable, and a tool
   asserting a falsehood is a REFUTED finding to fix, not an
   embarrassment to hide.
6. **Parallelize from the BACKLOG.** Independent items with disjoint
   file ownership go to concurrent worktree agents; each delivery
   arrives with predictions adjudicated, BACKLOG entries updated in
   place (SHIPPED/PARTIAL, never silently deleted), and new friction
   filed with evidence.
7. **Statuses land as work lands.** Update the roadmap item the moment
   its work ships, with the one-line result attached — release triage
   should be a read-through, not archaeology.
8. **Releases follow the skill.** Ledger refresh, roadmap→release→next-
   roadmap rotation with closure banners, Before/Now/Demonstrate for
   every improvement, a story for every asset, honest limits always.
9. **Everything reproduces.** Corpora regenerate from seeds
   byte-identically (checked); experiments regenerate from committed
   generators and fixed seeds; checkpoints ship as release assets;
   licensed external data never enters git.

## Skills

- `.claude/skills/release/` — the release process (ledger refresh, doc
  rotation, tag, GitHub release with model assets).
- `.github/skills/corpus-authoring/` — corpus authoring via seeds (for
  Copilot/VS Code agents; mirrors ADDING_FORMULAE.md).
- `.github/skills/schema-and-links-governance/` — schema/link-integrity
  rules.
- Repository-wide Copilot guidance: `.github/copilot-instructions.md`.
