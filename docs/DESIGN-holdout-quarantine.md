# Design — the holdout quarantine tier (`data_holdout/`)

Written during v0.12 item 1's prerequisite, *after* authoring miniF2F
revealed that the obvious path corrupts the thing being measured. It does
not edit [DESIGN-heldout-recovery.md](DESIGN-heldout-recovery.md); H1–H6
stay frozen. It settles a question that design left open: **where a
held-out corpus lives.**

## 1. The problem, measured

miniF2F emits 157 nodes through the unwidened emitter. Authoring them into
`data/` — the obvious reading of "author via the same emitter" — puts them
in the merged graph that every ledger and every pinned guard is computed
over. Both available discipline labels then distort the v0.11 channel split
that shipped in `v0.11.0`:

| variant | constituents | external (conservative) | `prior_corpus` | guards broken |
|---|---:|---:|---:|---:|
| v0.11 tagged / pinned | 181,909 | 0.391 | 286 | — |
| `data/`, discipline `minif2f` | 183,305 | **0.581** | **10** | 6 |
| `data/`, discipline `number_theory` | 183,305 | 0.389 | **26,014** | 7 |

The mechanism is `owner_channel`, which keys on corpus identity and
discipline overlap:

- A **novel** discipline overlaps nothing, so the holdout becomes a
  universal `external` donor. `external` outranks `prior_corpus`, so
  constituents across the graph get upgraded and the conservative external
  share inflates from 0.391 to 0.581. This is precisely the umbrella
  laundering `owner_channel`'s docstring exists to refuse — it says an
  umbrella label is "shared ground that must not be counted as external
  evidence."
- Sharing **`number_theory`** keeps the external share honest (0.389) but
  makes the holdout a 26,014-constituent `prior_corpus` donor to the
  12.5k Lean-workbook layer — paying grounding credit to the very corpus
  it is supposed to be independent of.

There is no free label. The constituent total moves either way, which alone
breaks two guards. So the label was not the mistake; **the premise was.**

## 2. The rule

> A held-out corpus is committed, versioned and gated like any other, and
> is invisible to the merged analysis graph until a measurement explicitly
> merges it.

A holdout that joins the graph every pin is computed over is not held out.
This is the same failure the recovery design already names in the other
direction (§4: "Mixing holdout-ISG with Lean-workbook owners would let the
12k layer gift the holdout a curve") — here the holdout gifts the published
layer an external-credit boost instead. One rule covers both.

## 3. What it costs, and what it keeps

Nothing structural: `decompose.load_trees(data_dir, keep)` has always taken
its root as a parameter, and `analyze_loaded`'s docstring already describes
the intended shape — *"the curve's many points share one `load_trees` of the
curated layer; only the ingested overlay changes."* The tier is that
sentence made into a directory.

Kept, versus an uncommitted or measurement-local holdout:

| benefit | how |
|---|---|
| git-versioned, browsable, reviewable | it is a normal committed corpus |
| schema-validated | `validate_nodes.py --nodes data_holdout/<name>/nodes.json` |
| byte-reproducible from its seed | `check_regeneration.py` now walks both roots |
| owned by a seed, no hand-edits | same orphan check, per root |

Given up: it is not in the default `validate_nodes.py` count, and it does
not appear in the ledgers. Both are the point.

Regeneration coherence is the guarantee a holdout must *least* afford to
lose — it is the entire claim that the sample was drawn mechanically rather
than chosen — so it is gated in `check_regeneration.py` rather than left to
whichever script happens to measure. Absent roots are skipped, not an error,
so a clone that has authored no holdout is unaffected.

## 4. Ingested-ness is separate from held-out-ness

Two flags that are easy to conflate:

- **Ingested** (`decompose.INGESTED_CORPUS_PREFIXES`,
  `measure_operator_bag.INGESTED_DISCIPLINES`) — authored in one mechanical
  act from a pinned extract. `minif2f` is registered in both. The
  registrations are inert while the holdout is unloaded, and load-bearing
  the moment a measurement merges the overlay: without them P-E5 would
  promote the holdout's forms to patterns and move grounding for every node
  in that run.
- **Held-out** — a fact about a *measurement's id set*, not about a corpus
  flag. Design §4 makes Lean-workbook curated-relative to the miniF2F
  curve. The same nodes are "ingested" globally and "curated" relative to
  the holdout, and that is not a contradiction.

Registering a corpus as ingested is the conservative direction: it can only
remove forms from the pattern set, never resurrect one.

## 5. What held-out B inherits

The Goedel-Pset sample (~2,048, design §3) lands in
`data_holdout/goedel_pset/` under the same rule, with the same two gates.
Its size is the reason the rule matters more there than here: 2,048 ingested
nodes carrying a novel discipline would move the external share further than
miniF2F's 157 did.

Whether the two holdouts may be loaded together in one measurement is **not**
settled here. H1–H6 are per-source predictions; a merged A+B run would need
its own null and its own written prediction before anyone runs it.

## 6. Falsifiable

If a later cycle shows that merging a holdout overlay in memory produces a
different curve than the same nodes committed to `data/` would have — beyond
the channel effects tabled in §1 — then this tier is hiding a real
interaction rather than a contamination, and the rule owes a revision. The
check is cheap and nobody has run it: author held-out B both ways once, and
diff the ISG curve.
