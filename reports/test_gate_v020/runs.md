# v0.20.0 complete-suite gate

Two runs, main checkout frozen from each launch to its verdict, both
receipts retained. 96 test modules per run, one process,
`scripts/time_tests.py` over the in-process-generated module list.

| run | tip | result | log |
|---|---|---|---|
| 1 | `e3ed3b5` | **2,326 ran, FAILED (failures=3, skipped=5), 21,715.8 s (6 h 02 m)** | `run1-red.log` |
| 2 | `3dc26d0` | **2,326 ran, OK (skipped=5), 21,828.9 s (6 h 04 m)** | `run2-green.log` |

## Run 1's three failures, adjudicated at `d7bccd9`

All three were ROADMAP-v0.20 §4b (exact integer literals) reaching code
the batch's targeted suites never listed:

1. `test_convention_probe.CensusReVerifies.test_provenance_digests_match_the_committed_inputs`
2. `test_convention_probe.Determinism.test_regenerates_byte_identically`
   — one cause, counted twice: `experiments/convention_pairs_probe.json`
   pins the digest of `reports/signature_matches.json` among its
   provenance inputs, and that report legitimately moved at the release
   refresh (4b changed the parser whose writer digest it records).
   Regenerated: **exactly one leaf differs** (the provenance digest
   row); every census number byte-identical. Precedent: v0.16's
   `ambiguity_rate` — numbers identical, pins moved, adjudicated rather
   than silently re-pinned.
3. `test_corpus_analogy_split.PointabilityTests.test_serialization_round_trips_on_every_authored_statement`
   — the real defect. `analogygen.serialize` converted every numeral to
   float before emitting, so `leanworkbook.ground.lean_workbook_37421`'s
   76-digit exact literal came back `4.444e+75`: a different term.
   `serialize` now emits exact ints as `str(int)` (curated spellings
   unchanged — `str` and `:g` agree on every small integer) and
   `corpus_analogy_split.deserialize` mirrors it, int first, float
   fallback. The failing suite test is the regression test.

The batch had verified 4b against every numeral surface it knew served —
25,554 skeletons, 14,830 answer lines, both byte-stable — and the suite
found the one serializer nobody named. A targeted suite proves the
surfaces you listed; the full gate proves the ones you forgot.

Run 2's tip also carries the maintainer-directed governance relaxations
(`3dc26d0`, ROADMAP-v0.21 §4.0): narrowed rules, recorded before the
tag so the tagged tree and the tested tree are the same tree.

The five skips are the standing set (three environment skips plus
`test_transliteration`'s two slow-regeneration cases, hand-run green
before the v0.19 gate and unchanged since).
