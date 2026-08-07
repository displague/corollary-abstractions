# v0.2.0 — Creating resolved; the corpus becomes a web

(Retroactive notes for the v0.2.0 tag; supplements the annotated tag
message. Baseline: [v0.1.0](RELEASE-v0.1.0.md).)

## Creating

- **Extractive answering is solved without a decoder**: the span pointer
  (1.000 on audited held-out combos) plus closed-form parse/canonicalize/
  render generates fluent answers in either language — `demo_answer.py`,
  self-bootstrapping, now with English glosses produced by running the
  lexicon machinery in reverse.
- Both learned decoders failed informatively (a seq2seq that cannot copy;
  a pointer-generator that memorizes), defining the non-extractive
  frontier that v0.3's analogy work addresses.

## The corpus

- 85 → 137 nodes, 9 → 15 disciplines (morphology, differential
  geometry/topology, algebraic and geospatial topology).
- `docs/DISCOVERIES.md` created as the human-readable findings ledger.
  Headlines of this cycle: the **four-valuation identity** (counting,
  entropy, Euler characteristic, and area are one modular-valuation law),
  **Stokes-is-FTC** found mechanically, **pH is the surprisal of proton
  activity**, and morphology's *correct refusals* (the matcher declining
  the log-law analogy because concatenation does not commute).
- A registered authoring prediction was formally cashed (the LEQ head
  chosen so transitivity statements would twin — they did).

## Real data and the prover

- First real-data result: Spanish morphology same-lemma detection —
  char/weights own surface residuals (0.959 unseen lemmas / 0.811 hardest
  paradigms), the thesis's symmetric half measured.
- Wikisem (LREC 2020 logical forms) located, downloaded, ingestion
  prototyped (348 recurring semantic skeletons from real English).
- **Prover phase 1 delivered natively on Windows**: 155 (state, tactic,
  state) triples extracted from Lean proofs of this corpus's own Boolean
  laws; `prover/ExtractData.win.lean`, `sample_triples.json`,
  `PHASE1_NOTES.md`. WSL2 not required. Phase 2 unlocked.

## Honest limits carried forward

Non-extractive generation unsolved at tag time; specialization matcher
noise and its proven false-negative filter; head literalism quarantining
new-vocabulary corpora; discrete/continuous (`sum` vs `INTEGRAL`) divide;
single-seed scaling-grid cells (trend claims only).
