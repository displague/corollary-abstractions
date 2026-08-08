# Adding statements to the corpus

**The seed scripts are the source of truth.** Every corpus under
`data/<discipline>/nodes.json` is the deterministic output of a
`scripts/seed_<discipline>.py`; `scripts/check_regeneration.py` enforces
this (a direct edit to any `nodes.json` is flagged as DRIFT and would be
clobbered by the next regeneration). The old template-CLI workflow
(`add_node.py`, editing JSON in place) is **deprecated** — the tool now
refuses to run without a legacy flag.

## The workflow

1. **Edit or create the seed.** For an existing discipline, edit its
   `scripts/seed_<discipline>.py`. For a new discipline, copy the most
   recent seed as your pattern (currently `seed_temporal.py` /
   `seed_ml.py` show the full house style, including registered
   predictions in the docstring).
2. **Register predictions before matching.** If you expect a new node to
   twin an existing family, write the prediction in the seed docstring
   first, then let the matcher adjudicate. Fired and missed are both
   reportable results; authoring-to-match must be declared.
3. **Regenerate and verify** (from repo root; `PYTHONIOENCODING=utf-8`
   on Windows):

   ```
   python scripts/seed_<discipline>.py
   python scripts/check_regeneration.py    # seed<->JSON coherence
   python scripts/validate_nodes.py        # schema + link reciprocity, merged graph
   python scripts/match_signatures.py      # twins; ZERO parse problems / slot gaps required
   python scripts/decompose.py             # constituent readout + groundedness
   python scripts/specialize.py            # general->specific edges
   ```

4. **Park findings.** New cross-discipline identities (or informative
   refusals) go in `docs/DISCOVERIES.md`; new tooling/schema friction
   goes in `docs/BACKLOG.md` with its evidence.

## Hard constraints (all learned the hard way — see BACKLOG for evidence)

- `statement_id`: first segment must be `[a-z0-9]+` — **no underscores**
  (use `settheory.`, `infotheory.`-style prefixes; the directory keeps
  the underscore).
- `constants` entries take `{symbol, description, value?}` — a `name`
  key fails validation.
- `symbol_lexicon.symbols` needs ≥1 scalar entry; operator/function
  symbols go in `functionals`.
- All six `inferential_links` lists are required; `entails` /
  `special_case_of` / `generalizes` / `equivalent_to` are
  reciprocity-checked over the **merged** graph — cross-corpus
  reciprocal edges require editing both seeds; one-sided cross-corpus
  edges are safe only via `composed_with`.
- Template grammar: identifiers, numbers, `+ - * / ^ ( )`, calls
  `NAME(...)` (args ORDERED, heads literal at every match level),
  bracket functionals `NAME[A|B]`, prefix big-ops `sum_i EXPR`,
  relations `= <= >=`. No binders/min/max — use opaque calls and note
  them honestly.
- Slot ids must not start with `sum_ prod_ lim_ max_ min_`; every
  template slot must appear in `slot_schema`.
- Reuse established call heads (`MEET/JOIN/NEG`, `CARD`, `LEQ`,
  `CONCAT`, LTL heads...) where mathematically honest — head literalism
  means a new vocabulary is quarantined from twinning; adopting a shared
  archetype_id is the cross-head channel when heads must differ.
- `epistemic_status` may be `conjectured`; machine-checked statements
  carry `verified_by` (see `seed_logic.py`'s VERIFIED_BY table and its
  drift check against the prover artifact).

## Corpus-wide invariants that will check your work

`validate_nodes.py` (schema + reciprocity), `match_signatures.py`
(parse/slot gaps, archetype drift), `check_regeneration.py`
(byte-identical regeneration, orphan corpora), and the release skill
runs all of them before any tag.
