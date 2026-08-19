# v0.14.0 — the instruments were the finding

The candidate did not ship. Five of six registered predictions missed, and
three of those five missed for reasons that belong to the evaluator rather
than to the resolver. That is the cycle: a protocol built to be honest was
honest about itself.

**Links** — previous release: [v0.13.0](RELEASE-v0.13.0.md) · closed plan:
[ROADMAP-v0.14](ROADMAP-v0.14.md) · next plan:
[ROADMAP-v0.15](ROADMAP-v0.15.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[what the ruler was made of](blog/what-the-ruler-was-made-of.md)

## The headline finding

**Before.** v0.13 ended with a resolver that answered 24 of 24 questions and
still could not ship: it read "interest accumulated **without** compounding"
and confidently returned continuous compounding, while fresh false positives
rose to 0.034. The cycle also refused to score its clarification loop, having
discovered that its follow-up lines were never frozen.

**Now.** v0.14 froze a 48-row evaluator before the implementation existed, ran
it once, and published the result. Q3 fired. Q1, Q2, Q4, Q5 and Q6 missed.

| clause | registered bar | observed | |
|---|---|---|---|
| Q1 contradictions stop binding | 0 wrong BINDs; 14/16 reach; 14/16 routes | 1; 12/16; **8/16** | miss |
| Q2 clarification retains the reading | 15/20 halved and retained | **3/20** | miss |
| Q3 the blind arm is materially weaker | gap ≥ 0.10 | **0.6801** (0.7127 vs 0.0326) | fired |
| Q4 precision does not pay | pooled ≤ 0.030 | **0.03467** | miss |
| Q5 coverage does not pay | reach and recall ≥ 0.833 | 0.921; **0.789** | miss |
| Q6 exclusion changes the decision | ≥ 4/16 | **1/16** | miss |

**Demonstrate.** `experiments/when_to_ask_result.raw.json` is the one-shot
ledger, committed before the compact view derived from it. Re-adjudicate it
with:

```
PYTHONIOENCODING=utf-8 python -c "import json;d=json.load(open('experiments/when_to_ask_result.raw.json'))['adjudication'];print({k:d[k]['fired'] for k in ('Q1','Q2','Q3','Q4','Q5','Q6')})"
```

### Why the misses are the result

**Q2 measured a belief, not a resolver.** Of the twenty rows predicted to ASK,
**eight bound directly to the intended id**, five bound elsewhere, three
passed on vocabulary the graph does not contain, and four asked. The eighteen
rows that predicted no ambiguity scored 18/18 on target recall. Every failure
sits in rows authored on the belief that the collection was ambiguous, and the
scorer gave the same credit to answering correctly without asking as to
answering wrongly. Row A-08 asked for *"story constraint on setup and payoff"*
and the resolver returned `narrative.constraint.chekhov_gun` — which is that
constraint — and was marked wrong against an intended
`narrative.constraint.no_deus_ex_machina`.

**Q4 could not have fired.** The mechanical precision arm classifies OEWN
sentences, which contain no `without TERM` structure, so the candidate's
masked admission path is never entered. The clause re-measured the untouched
v0.13 resolver and reproduced it: 0.024, 0.038 and 0.042 across three fresh
disjoint 1,000-sentence samples, pooled 0.03467, against v0.13's 0.034. That
is a genuine independent replication of the number that sank the last cycle,
and it was never a test of this one's intervention.

**Q3 fired for the reason the others missed.** Reciprocal candidate load pays
`1/k`, and 25 of the 30 rows where the resolver recalled its target returned
that target alone. The arm measures decisiveness, which is precisely what
v0.13 had too much of. The gap is a true statement about the blind baseline
being weak; it is not evidence the candidate reads questions well.

## Roadmap triage

**Shipped.**

- *Item 1 — freeze the evaluator before the implementation.* 48 rows in four
  registered strata, exact schemas, an independently regenerable 88-id spent
  set, a three-arm pinned-OEWN key receipt, and a fail-closed provenance
  manifest, all committed before any candidate existed.
- *Item 3 — make the release gate observable.* Measured at a frozen tip, with
  per-module receipts retained in `reports/test_gate_v014/`.

**Shipped as a negative.**

- *Item 2 — exact negative contrast and clarification.* Adjudicated once,
  missed, parked. The exclusion mechanism itself works where it was aimed:
  the spent v0.13 sentence now binds `economics.finance.simple_interest`
  instead of `economics.finance.continuous_compounding`, by promoting a
  lower-scored survivor after the veto. A resolve-then-filter implementation
  would have returned nothing there. It is kept as a regression test and is
  not a score.
- *The gate's own investigation list was wrong.* See below.

**Carried, each with its dependant named.** See
[ROADMAP-v0.15](ROADMAP-v0.15.md) §carried. Everything without a dependant is
parked in [BACKLOG](BACKLOG.md) with its reason.

**Drift audit.** Re-reading v0.12 and v0.13: the standing warning that the
project claims a live session it does not have is **no longer true**, and this
release retires it. A person can type a line and get an answer, and the
clarification loop v0.13 shipped is reachable from that surface:

```
printf 'area\nnarrow corpus geometry.foundations.v1\n' | python scripts/harness.py
```

prints an ambiguous set, then `corpus='geometry.foundations.v1' narrowed 10
candidates to 8`. The acceptance v0.8 wrote — a person types and sees ask or
refuse — is met. No other prior goal was found lost to attrition.

## What changed, per area

### The release gate is measured, and its premise was wrong

**Before.** The plan named a 5,620-second capability-blind sweep and roughly
4,700 seconds of fixture gap as the things to investigate.

**Now.** 68 modules, **1,341 tests, 0 failures, 0 errors, 5 skipped**, serial
wall clock **21,688 s (6.02 h)**. The blind control is 4,317.0 s and the
fixture gap 3,434.2 s — and neither is the problem. `test_write_stage` costs
**12,522.5 s, 57.7 % of the suite**, more than everything else combined, and
appears nowhere in the item that commissioned the measurement. Its fixture
overhead is 8.5 s, so it is 103 real tests rather than a setup artifact.

The registered balanced assignment predicts the **same 12,523 s wall clock at
2, 5 and 8 shards**, because one module is a hard floor. Maximum speedup
1.73×; the five-shard v0.13 gate had three shards more than the work can use.

That disposes of the third investigation without invoking its principle:
sampling the capability-blind control could remove 4,317 s of serial time and
**exactly zero** wall clock. The control stays whole because the optimization
buys nothing, not as a concession.

**Demonstrate.** `reports/test_gate_v014/manifest.json` and
`reports/test_gate_v014/shard-plan-5.json`; shard 0 holds one module, shard 1
holds one, and shards 3 and 4 hold all 65 others for a combined 717 s.

### The resolver learned to refuse a contradiction

**Before.** An exclusion could only have run on the answer, and by then the
only reading left to filter was the wrong one.

**Now.** `resolver.resolve_negative` parses one frozen surface rule, computes
the excluded concept's owners from the corpus, and passes that set into a
single resolution as an admission mask. There is no second pass and no
unmasked retry. Graph size, document frequencies, postings, known-word status,
query coverage and result ordering all read the original graph, so removing
one candidate cannot change another's eligibility.

**Demonstrate.** `python -m unittest tests.test_resolver` — the class
`ItDoesNotRepeatTheSpentExclusionFailure` asserts the old path still binds the
excluded reading, that the exclusion reaches `simple_interest` instead, and
that the survivor was promoted rather than the winner merely deleted.

### The evaluator was repaired once, before any score existed

Two of its own assertions could not survive the cycle succeeding: one proved
no candidate existed by importing the live resolver, the other proved no
result existed by checking the working tree. Both go red exactly when v0.14
succeeds, inside a file the candidate commit is forbidden to touch — so the
gate's "full suite green" clause was unsatisfiable as written. Both now ask
their question of commit `3c17718`'s Git objects. No row, threshold,
denominator or scoring path moved, and the repair landed before any candidate
output existed.

## Discoveries of the cycle

Three of the cycle's findings, quoted from [DISCOVERIES](DISCOVERIES.md):

- *"A capability-blind control can be beaten by the failure it was built to
  catch."* Reciprocal load rewards small answers, so it cannot separate
  precision from overconfidence.
- *"A preregistered clause the intervention cannot influence measures the
  baseline, not the intervention."* Q4 had no causal path from the change to
  its number.
- *"A frozen evaluator can freeze in its own expiry date."* Every assertion in
  a frozen instrument must be phrased about an object that stops changing.
  Git commits do; imports and directories do not.

## Resolved from BACKLOG

- The v0.13 want for an executable clarification gate: delivered as
  `scripts/measure_when_to_ask.py`, which now reports construction, overlap
  **and** provenance, and refuses a follow-up the live shell would parse
  differently or that cannot keep its own declared reading.
- The v0.13 morphology trade stays rejected; nothing in this cycle reopens it.

## Honest limits carried forward

- The shipping resolver is still v0.12's 0.833 / 0.030 point. This cycle
  shipped no resolver improvement.
- Q4's replication says the 0.034 false-positive rate is real and reproducible
  across fresh samples. It does not say the exclusion helps precision, because
  the exclusion never runs on that path.
- All twenty ASK rows declared a singleton retained set, and the validator's
  fixed credit shape refuses a larger one, so Q2's retention clause was
  equivalent to primary retention. v0.14 cannot show that clarification
  preserves several simultaneously intended readings.
- The published cross-field structural match count is **suspended** from use
  as a result until it is adjudicated. It has never been tested against a
  two-sided prediction, and shape collisions are cheapest exactly where the
  corpus is most formulaic. See
  [the coincidence veto](DESIGN-coincidence-veto.md) §10.
- Nothing certifies that the function from question to outcome is unchanged
  across builds. The committed digests certify only that the same sources
  produce the same artifact.
- A passing Python test is not a Lean proof.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.** `data/` and
every `experiments/*.py` are byte-identical to `v0.13.0` —
`git diff --name-only v0.13.0..v0.14.0 -- data/ experiments/` lists no `.py`
and no corpus file — so the checkpoints attached to **v0.6.0** remain accurate
for this release. Measurement ledgers are committed in-repo:
`experiments/when_to_ask_result.raw.json` (one-shot ledger),
`experiments/when_to_ask_result.json` (compact view),
`experiments/when_to_ask_holdout.json` (the 48 rows), and
`reports/test_gate_v014/` (per-module suite receipts).

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py
PYTHONIOENCODING=utf-8 python scripts/measure_when_to_ask.py validate
printf 'area\nnarrow corpus geometry.foundations.v1\n' | python scripts/harness.py
python -m unittest tests.test_when_to_ask_prereg tests.test_when_to_ask_candidate tests.test_resolver
```

`measure_when_to_ask.py score` refuses to run: the one-shot output already
exists and is never overwritten.
