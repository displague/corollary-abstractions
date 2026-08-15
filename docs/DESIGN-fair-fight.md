# Design — matcher vs operator-bag, one figure of merit (ROADMAP-v0.11 item 2)

Committed BEFORE the comparison is re-run on the 12,771-node graph.
Named dependant: the skeptic sentence the release notes have to stand behind.

v0.10's headline negative is real and under-analysed. On 508 nodes the
operator-bag formed 7,622 pairs at 1.26% precision and the matcher 96 at
1.0. Count and precision were reported side by side, which lets either
side claim victory. This note picks one frame, registers it, and forbids
tuning the bag to lose.

## 1. What is not a fair frame

- **Raw pair count.** The bag is a grouping by a 6-glyph set. Larger
  groups win on count by construction. Declaring the bag the winner on
  count restates its definition.
- **F1 against a hidden gold.** There is no adjudicated twin census of
  the 12k ingested layer, and manufacturing one after seeing the pairs
  would choose the gold to fit the story.
- **F1 with the matcher as gold, or the bag as gold.** The two pair
  sets almost nest (every typed twin is a bag pair, save the one
  print-convention miss on this branch). F1 then collapses to
  `2p/(1+p)` of bag precision. It is a transform, not a second
  measurement.

## 2. The figure of merit

**Bag precision, treating the typed-skeleton relation as the definition
of a twin, reported next to matcher recall-against-the-bag, at the
full graph and on the ingested slice alone.**

That is one number the skeptic can hold: *of the pairs the bag forms,
what fraction are typed twins?* The matcher is not being scored as a
classifier against a richer gold — it *is* the gold, because "typed
twin" is a closed form this repo already computes. Recall is therefore
almost a definitional 1.0, and the one exception (if it survives at
this scale) must be named, not rounded away.

A size-matched control travels with it, so pair-count cannot be
smuggled back in: draw `|matcher|` pairs uniformly from the bag and
report how many are typed twins. The expected value of that draw *is*
bag precision. The control exists to make the "but the bag found more"
move pay a number.

The bag stays capability-blind. Its glyph set remains `{+,-,*,/,^,=}`.
It is not widened to `>=` / `<=` / `<` / `>` to chase ingested
inequalities, and it is not narrowed to lose. A glyph change is a
different baseline and needs its own note.

## 3. Registered predictions (before the 12,771-node re-run)

Written against the 508-node table and the emitter's already-measured
`group_counts` `{1027, 972, 971, 973, 5}`. The pair cardinalities are
not yet known; these are direction and floor claims, not point
estimates of the new pair counts.

- **FF1.** Bag precision on the full 12,771-node graph is strictly
  below the 508-node combined figure (1.26%). Ingesting thousands of
  same-glyph inequalities grows the bag faster than the matcher.
- **FF2.** Matcher precision against the bag is `1 − k/|matcher|`
  with `k` a named print-convention count, not a silent 1.0. On this
  branch `k ≥ 1` (`COS(2*theta) = COS(theta)^2 + -(SIN(theta)^2)` vs
  the curated infix-minus double-angle). If `k` grows, every extra
  miss is listed.
- **FF3.** Matcher recall against the bag is `1 − k/|matcher|` (the
  same `k`). The pair sets still almost nest.
- **FF4.** The size-matched bag draw at `k_draw = |matcher|` has
  expected precision equal to bag precision; a single committed-seed
  draw lands within 3× the Bernoulli standard error of that
  expectation. This is a check on the draw, not a second claim about
  the matcher.
- **FF5.** On the ingested-only slice, bag precision is lower than on
  the curated-only slice. The first-wave direction (0.54% ingested vs
  2.03% prior) survives thousands.

The skeptic sentence, also registered: **the bag still wins on count
and still loses on the only figure of merit that does not restate its
definition — precision against typed twins — and the matcher misses
only the pairs whose glyphs disagree by a printer convention.**

## 4. What this run is not

It is not a recall estimate against a human-adjudicated sample of
"should these be twins?". That sample does not exist at 12k and will
not be improvised after seeing the pairs. Route-1 owner identity (item
1) is a different question and is not reused as a twin gold.

It is not a retune of the bag. If the 12k graph makes the 6-glyph set
look foolish (most ingested statements are inequalities the bag cannot
see), that is a finding about the baseline's reach, reported as such,
not a reason to give it `>=`.

## 5. Cost

Pair sets are not materialised. Bag pairs are counted as `Σ C(|g|, 2)`
over glyph groups; the intersection is the matcher pairs whose two
members share a glyph set. The size-matched draw samples matcher-sized
index pairs from the groups without listing 10^6+ tuples. The generator
is `scripts/measure_operator_bag.py`; the committed table is
`experiments/item4_operator_bag.json`.

## 6. Adjudication (appended after the run; §1–§5 unedited)

`scripts/measure_operator_bag.py` → `experiments/item4_operator_bag.json`
on the 12,771-node graph. Pair sets counted, not materialised.

| slice | nodes | bag pairs | matcher pairs | bag precision | k |
|---|---:|---:|---:|---:|---:|
| curated | 256 | 4,341 | 88 | 2.03% | 0 |
| ingested | 12,515 | 9,010,102 | 1,879 | 0.0209% | 0 |
| full | 12,771 | 9,041,744 | 1,991 | 0.0220% | 1 |

- **FF1 FIRED.** Full-graph bag precision 0.0220% < 1.26%.
- **FF2 FIRED.** k = 1, named:
  `leanworkbook.skel.lean_workbook_49137` /
  `trigonometry.identities.double_angle_cosine`. Matcher precision
  1,990/1,991 = 0.9995.
- **FF3 FIRED.** Bag recall vs matcher = matcher precision vs bag =
  0.9995. The pair sets still almost nest.
- **FF4 FIRED.** Size-matched draw (seed 20260814): 1 twin in 1,991
  bag pairs (0.050%) against expected 0.0220%; SE 0.00033; within 3 SE.
- **FF5 FIRED.** Ingested 0.0209% < curated 2.03%.

Skeptic sentence, as registered: the bag still wins on count
(9,041,744 vs 1,991) and still loses on the only figure of merit that
does not restate its definition (0.0220% vs the matcher's 99.95%),
and the matcher misses only the one pair whose glyphs disagree by a
printer convention.
