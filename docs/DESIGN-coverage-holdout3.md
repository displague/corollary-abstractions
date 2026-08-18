# Design — v0.13 conversational coverage holdout 3

This design, `experiments/text_resolution_holdout3.json`,
`scripts/measure_text_resolution_holdout3.py`, and
`scripts/measure_false_positive_f4.py` are committed together **before either
new sample is run**. Holdout 3 may be scored once. F4 may be sampled once.
Their misses remain results; neither set may become a development set.

## 1. Scope frozen from the roadmap

Only the three causes named in `ROADMAP-v0.13.md` item 1 are in scope:

1. conservative surface morphology (`derivatives`/`derivative`,
   `euclid`/`euclidean`);
2. synonyms already authored in the corpus's `symbol_lexicon`;
3. separating a resolver gap from a corpus gap.

No WordNet semantic relation is a resolver feature in this slice. Open English
WordNet supplies only the mechanically sampled false-positive arm. No holdout
3 failure may justify a new rule after this commit.

## 2. Holdout 3

The 24 in-corpus queries were written in one pass from committed statement
titles and glossary descriptions, without invoking `resolve`. They are
byte-disjoint from the development set and holdouts 1 and 2. Each row names an
expected statement id so a coincidental ASK is visible rather than counted as
semantic success.

Eight `morphology` rows deliberately vary number or the
`euclid`/`euclidean` surface. Eight `lexicon` rows paraphrase authored glossary
material. Eight `control` rows use ordinary alternate wording. The scorer
publishes both the historically comparable reach rate (BIND or ASK) and the
stricter target recall (expected id appears among candidates), plus wrong
single binds.

A capability-blind baseline ranks node titles by exact, unnormalised token
overlap. It has no morphology, glossary, resolver gates, or graph structure.
If it recalls every target, this holdout is vacuous for the claimed mechanism.

### Registered predictions

- **C3-1 (headline coverage).** At least 21/24 queries reach some statement:
  coverage >= **0.875**, strictly above v0.12's shipping 0.833.
- **C3-2 (target recall).** At least 20/24 expected statements appear among
  the returned candidates: target recall >= **0.833**.
- **C3-3 (no wrong certainty).** Every BIND is the registered target:
  wrong single binds = **0**.
- **C3-4 (non-vacuity).** Exact-title-overlap target recall is below **1.0**
  and below resolver target recall.

## 3. Fresh mechanical false-positive arm

F4 repeats the unscreened Open English WordNet protocol on a fresh fixed seed,
**20260818**, over 1,000 examples/glosses. It uses only the archive pinned in
`data_sources/manifest.json`:

- source: Open English WordNet 2025;
- SHA-256:
  `7d749f6e2c39e6970e4997839dcf6e42fd281f3c2fae0171d2192bae8cfa4b51`;
- environment variable: `COROLLARY_WORDNET`.

The script refuses to score any other bytes and records the digest in its
ledger.

### Registered prediction

- **F4.** At most **3.0%** of the 1,000 fresh, unscreened sentences reach a
  corpus statement. This is the v0.12 shipping rate, not a threshold chosen
  from the new sample.

## 4. Shipping rule

The resolver change ships only if C3-1 fires and F4 fires. Otherwise the
trade-off and all rows are published, but the resolver change is reverted;
experiment-only scorer, preregistration, and ledgers may remain. C3-2 through
C3-4 are honesty diagnostics and are reported whether they fire or miss.

## 5. One-shot adjudication

Preregistered at `110fff4c06bdbe0fcb31cc8606ec29ed9502f6f1`.
The morphology implementation was frozen at
`7a9c7c344fab7e6a3986be3ff224e6833a4a8052`, then both scorers ran once.

| prediction | result | disposition |
|---|---:|---|
| C3-1 coverage | **FIRED**, 24/24 = 1.000 | above 0.875 |
| C3-2 target recall | **FIRED**, 23/24 = 0.9583 | above 0.833 |
| C3-3 wrong certainty | **MISSED**, 1 wrong BIND | `without compounding` bound to continuous compounding |
| C3-4 blind control | **FIRED**, 0.9167 vs 0.9583 | weak: one title tie contains 14,571 ids |
| F4 false positives | **MISSED**, 34/1000 = 0.034 | worse than the 0.030 shipping ceiling |

The morphology and lexicon groups each recalled 8/8 targets; controls recalled
7/8. The sole target miss was not morphology: `interest accumulated without
compounding` confidently bound `economics.finance.continuous_compounding`.
The resolver scores matching words and has no closed-form representation of
the contrast contributed by `without`.

The shipping conjunction failed because F4 missed. Commit
`98e0d369eb183930bd7d918fc7edad8ecbc91457` therefore restores the resolver
and its tests exactly. The experiment is retained; the morphology change is
not shipped and these spent samples will not be rescored.
