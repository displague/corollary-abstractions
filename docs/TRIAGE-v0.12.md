# v0.12 release triage — gate status, drift audit, and what the notes may claim

Written before the release notes so the arguable calls are visible as
calls. The forward-looking design for v0.13 is committed first:
[DESIGN-what-predicts-the-gap.md](DESIGN-what-predicts-the-gap.md), written
*before* H1–H6 were graded so the next cycle's question could not be chosen
to flatter this cycle's post. The blog leads with the negative
([the-shelf-not-the-architecture.md](blog/the-shelf-not-the-architecture.md)).

## 1. Release gate

`ROADMAP-v0.12.md` §"Release gate" lists eight conditions.

| # | gate condition | status |
|---|---|---|
| 1 | held-out curve with null and keyword baseline, H1–H6 adjudicated, Lean-workbook not reported as held-out | **MET** — `experiments/heldout_recovery.json`; H1 missed, H2/H3/H4/H6 fired, H5 missed conditionally; Lean-workbook is the fixed curated-relative layer in every run |
| 2 | groundedness gate designed, or a written park because H1 failed | **MET, parked** — H1 missed, so §8's parking condition returned. Written into `docs/BACKLOG.md` with the unpark condition |
| 3 | item 3 shipped or parked with the H3 dependant evaluated | **MET** — shipped on the v0.11 branch; H3 **run** this cycle and fired weakly, disclosed as near-vacuous |
| 4 | item 5 shipped (P-LS1–P-LS5 adjudicated) or parked | **MET** — all five fired; `DESIGN-live-session.md` §8 |
| 5 | item 6 run only if a fit was named, otherwise parked | **MET, parked** — no fit named; parked in BACKLOG rather than carried a third time |
| 6 | every carried lane names its dependant or is parked | **MET** — see §3 |
| 7 | updated assets with winners, losers and controls | **MET** — ten regenerable artifacts; §5 |
| 8 | the complete suite green | **MET** — see §1.1 |

### 1.1 The suite, on the tip

`python -m unittest discover -s tests`, run on the tagged tip. Planned from
the measured cost rather than folklore: v0.11 recorded 6h35m, and this
cycle added ~150 tests. Result recorded in §6 below.

**What the notes may honestly claim.** "The shape did not recur" is TRUE and
is the headline. "At matched N the fitted source compounds and the holdout
does not" is TRUE (C1, registered before its cell). "A person can type and
get an answer" is TRUE and is new. "Ingestion compounds" is **no longer a
general claim** — it is a claim about Lean-workbook, and the notes say so.
"The groundedness gate is designed" is FALSE; it is parked. "Arbitrary text
is answered correctly" is FALSE — the measured false-positive rate on
unselected input is 3.0%.

## 2. Drift audit vs v0.10 and v0.11's stated goals

The rule is to re-read the *previous two* cycles, not just this one.

| carried from v0.10 / v0.11 | landed? |
|---|---|
| External benchmark (carried v0.9, v0.10, v0.11) | **RUN, at last** — two held-out sources, H1–H6 adjudicated. The fourth-cycle park is not owed |
| Verdict-backed ingestion as a RULE | **SHIPPED** — widened past `python-tests` to every ingested corpus |
| Groundedness gate | **RE-PARKED** with evidence; second park better evidenced than the first unpark |
| Live prompt / typable surface (v0.8 claimed "driven") | **SHIPPED** — and then some; see §4 |
| `specialize.py` general index | still PARTIAL, still parked, no dependant |
| Proof-search depth | stayed parked |
| Physics / affect / oscillation / visual | stayed parked |
| Chat-shaped HTTP skin | stayed parked, no dependant |
| Open-English authoring of new nodes | stayed parked (last, as v0.8 said) |
| Multi-turn dispatch memory (P-LS6) | stayed parked, and now **enforced** by a test |

**The v0.8 surface debt is paid.** v0.8 said the system could be driven;
`harness.py` printed a boot list and exited. v0.9 called that an earned
foundation, v0.11 named it focus attrition and scheduled it. This cycle a
person can type a line and get an exact answer, a dictionary sense, a
computed value, a belief derivation, a verified story, a named refusal, or
a conjecture held in a frame they own. That debt does not carry again.

**One new drift risk, named now.** The conversational surface grew well past
item 5's acceptance (§4). It was not in the roadmap, it is the largest body
of code in the cycle, and it is *not* the headline. Naming it here stops a
later roadmap inheriting "arbitrary text works" as a fact.

## 3. Carried lanes into v0.13

| lane | named dependant in v0.13 | disposition |
|---|---|---|
| Coverage of the conversational surface | **headline** (item 1) | **ordered first** |
| Ambiguity and context across turns (P-LS6) | headline — Buffalo-class parsing needs it | **unparked**, ordered with item 1 |
| Groundedness gate | *none until a non-Lean-workbook source shows a positive gap* | **parked**, condition written |
| Write-recovery ranker | *none — no fit named* | **parked** at triage, as the rule requires |
| Budgeted-edit ranker | *none* | **parked** (one foil cell) |
| What predicts the gap (W1–W3) | v0.13 design item, not scored | **carried as design** |
| `specialize.py` general index | *none* | stays parked |
| Proof-search depth | *none* | stays parked |
| Physics / affect / visual | *none* | stay parked |
| Chat-shaped HTTP skin | *none* | stays parked |
| Open-English node authoring | *none* | stays parked |

## 4. The unplanned half, disclosed

Item 5 asked for one typed line reaching two existing programs. What shipped
is that plus six routes: exact ownership lookup, pooled-evidence resolution
over four indexes, WordNet glosses, exact arithmetic and relation decision,
belief frames with false-belief separation, and the verified chicken story.

This is disclosed rather than sold because:

- **It is not the headline.** The cycle's result is the negative on H1.
- **Its numbers are worse than its demonstrations.** In-corpus coverage
  0.833–1.000 depending on the set; false positives 3.0% on unselected
  input; one registered refusal prediction (R2) **missed at 0.80**.
- **Three of its five quality properties are structural, not earned.**
  Grammatical, factual and logical hold because answers are quoted from
  committed prose, attributed, and related by committed links. The
  renderer cannot author a false sentence because it cannot author a
  sentence. Only *correct* is at risk, and only the resolver can fail it.

## 5. Assets

Symbolic cycle. No new checkpoint. The regenerable artifacts:

- `experiments/heldout_recovery.json` — H1–H6, both holdouts
- `experiments/matched_n_control.json` — C1
- `experiments/minif2f_emit.json`, `experiments/goedel_pset_emit.json` — emitter census and exclusions
- `data_holdout/minif2f/nodes.json`, `data_holdout/goedel_pset/nodes.json` — the quarantined corpora
- `experiments/text_resolution.json`, `..._holdout_result.json`, `..._holdout2_result.json`
- `experiments/resolution_scale.json` — S1–S5
- `experiments/false_positive_rate*.json` — F1, F2, F3

`reports/decompositions.json` remains the pre-scale file, as in v0.11.

## 6. The tip suite

Recorded after the run: see the release notes' honest-limits section for the
wall-clock and skip list. The tag waits on it; the skill forbids tagging on
a PARTIAL gate and v0.11's gate 7 is the precedent.

## 7. Questions the notes must not dodge

1. **H1 missed.** The notes lead with that, not with C1.
2. **R2 missed at 0.80** on the first text holdout. The improvement to
   0.9167 came on a second holdout after a fix; the registered miss stands.
3. **S2 and S5 missed** on the runs that scored them; both were repaired and
   the repairs measured, but the registered numbers are not re-scored.
4. **"Ingestion compounds" is retracted as a general claim.** v0.11 measured
   it on one source. Two held-out sources say the opposite. The retraction
   is first-class, not a footnote.
