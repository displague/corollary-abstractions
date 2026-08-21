# v0.16.0 — the capability voided, the instruments survived

This cycle built the machine it had planned to build, watched that
machine fail the gate frozen for it, and shipped the failure with its
mechanism named — then, in the same cycle, took the instrument suspended
two releases ago and established its information claim with a table
authored blind. A void and an establishment, both preregistered, both
kept. The difference between them is the whole method.

**Links** — previous release: [v0.15.0](RELEASE-v0.15.0.md) · closed
plan: [ROADMAP-v0.16](ROADMAP-v0.16.md) · next plan:
[ROADMAP-v0.17](ROADMAP-v0.17.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the edges were real; the radius was not](blog/the-edges-were-real-the-radius-was-not.md)

## The headline finding

**Before.** Nothing in this repository could say what else moves when
one committed thing is found wrong. The v0.15 rotation found the claim
"two ledgers are quietly stale on main" had itself gone stale, and the
front page had carried a compression figure through five tagged releases
while its ledger was rewritten twice.

**Now.** The retraction closure was preregistered (`8b82e31`: schemas,
100 derived control seeds, and two hand-audited ground truths committed
before any assembler existed), built (a 1,046-node, 879-edge provenance
graph over committed bytes — 1,045 and 877 before the adjudication
registration itself joined it; writer-emitted lineage; a six-rule
citation scan frozen with a dated disclosure), independently rechecked,
and
**voided by its own gate**:

| clause | verdict | deciding number |
|---|---|---|
| R1 writers emit their own edges | fired as written, and the wording is vacuous | 353/353 — but writer edges point *out* of ledgers, so the denominator holds only citation edges; intended measure 0.800 all-five, 1.000 regenerable-four |
| R2 drifts explained superset-exactly | **FAILED both roots — capability VOID** | Root A 11/11 covered, 54 > 33 cap; Root B 14/16, 106 > 48 cap |
| R3 coverage floor | failed | 2/14 release sections anchor vs 0.90 — largely a v1 registry-scope artifact, reported as such |
| R4 independent recheck | fired | every field of both certificates re-derived by a checker that never saw the builder, 0.108 s of 600 |
| R5 byte reproducibility | fired | two builds, one graph |
| R6 historical replays reported, not scored | reported | both close as the root alone — interpretation-shaped retractions have no data lineage, the floor where the design put it |
| blind control | did not void | **0/100** shuffles reproduce the audited coverage |

**What the void means, precisely.** The edges carry real information —
no degree- and kind-preserving shuffle reproduces the coverage — but
lexical citation cannot be simultaneously complete and precise on this
document corpus: the flood arrives through a backticked field vocabulary
whose commonest word is `nodes` and the ordinary word "decomposition",
and the two unreachable claims cite only derived decimals. Published
claims cite numbers and concepts, not artifacts. That sentence is the
cycle's product, and the v0.17 design is built on it.

**Demonstrate.**

```
python scripts/radius_recheck.py reports/radius/root-a-compression.cert.json
python -m unittest tests.test_retraction_closure tests.test_radius_recheck
```

The first re-derives the committed Root A certificate from the graph and
the schemas alone — ten `ok:` lines from a tool whose commit predates the
builder's. The certificates and the blind-control report live under
`reports/radius/`; the per-rule attribution rides on the graph's own
edge tags in `reports/provenance_graph.jsonl`; the full readout is
ANALYSIS
"the retraction closure: built, independently rechecked, voided by its
own gate".

## The second finding: the veto's information claim, established blind

**Before.** v0.15 left the coincidence veto partially adjudicated: two
controls passed, the tag-permutation control invalid by an
authoring-time scoping defect, the suspension on the cross-field match
count extended.

**Now.** An isolated context — shown only the 26-kind menu and the
judging rules, brief hash pinned in
`experiments/veto_full_cross_protocol.md` alongside a readout criterion
fixed before the table existed — authored all 325 pairs of the full kind
cross-product. Against that table, the same permutation scheme with the
same committed seed and count puts the real tags at **21 conflicting
slots while the twenty registered permutations span 45–61**. Real sits
below half the permuted
minimum. The information claim is established, labelled exploratory
forever because the census has no fresh half. The blind table agrees
with the v0.15 scoped table on 43 of 44 shared pairs — and independently
exempts proposition|set, the single row the sensitivity analysis found
carrying the instrument. The load-bearing judgement has now been made
twice by authors who could not see each other.

**The suspension lifts** by its own read-out clause, with two permanent
riders wherever the count is quoted: the conflicting readout (8 of 26
groups) and the one-row finding.

**Demonstrate.** `python scripts/veto_full_cross_rerun.py` re-runs the
control from the committed table and seed;
`experiments/veto_full_cross_result.json` is the committed readout.

## Roadmap triage

**Shipped as a void, instruments kept.** Item 1 — see the headline. What
survives unscored and permanent: writer-emitted provenance blocks in all
four ledger writers; `check_report_regeneration.py` in the release
refresh (three ledgers clean, one declared divergence with its
citation — the first machine answer the reports directory has given);
the graph, radius, recheck, adjudicator, and shuffle control as green
instruments; and the 27-claim ground truth as the bar any successor
citation mechanism must meet.

**Shipped as an establishment.** Item 2 — read out in writing, criterion
fixed first, suspension lifted with riders.

**Drift audit** (v0.14 and v0.15 re-read): the v0.15 rotation's audit
recorded its two attrition losses days ago and nothing further surfaced
in this short cycle; the HTTP skin's fourth park was taken by decision
in ROADMAP-v0.16 §3, and ROADMAP-v0.17 escalates it — a fifth park
means v0.18 owes a schedule or a retirement. No goal was found lost.

## What changed, per area

### The ledgers sign their work

**Before.** Which script produces which ledger was knowable only from a
comment; nothing noticed a committed report diverging from its writer.

**Now.** All four writers emit provenance blocks (writer identity and
hash, every input path with canonical-LF SHA-256, no timestamps); the
three regenerable ledgers were regenerated with pure additive diffs and
byte-identical second runs; `check_report_regeneration.py` reports
clean/drift/declared per ledger and runs in the release refresh. A
declared snapshot is not a drift, and the checker knows the difference.

**Demonstrate.** `python scripts/check_report_regeneration.py` — four
lines, exit 0.

### The adjudication registered itself into its own radius

The §6a registration names both root ledgers, so committing it moved
both closures by one (53→54, 105→106) before the run. Recorded in the
notes' spirit: a claim about the graph is a claim in the graph.

### The next direction, chosen and hardened before this document

The rotation gate ran in full a second time: three isolated series,
nine hashed rounds, fifteen directions, receipts in
`reports/design-direction-v0.17.json`. All three series and the void
post-mortem converged independently on one direction — citation
discipline at authoring time. The selected design,
[DESIGN-ledger-first-claims](DESIGN-ledger-first-claims.md), was then
hardened by adversarial review before ROADMAP-v0.17 existed: the
population rule and covered document are sealed before scoring, and the
near-unfalsifiable precision clause was replaced by a path-token
baseline that can genuinely win.

## Discoveries of the cycle

Quoted from [DISCOVERIES](DISCOVERIES.md):

- *"A provenance graph can carry real information and still not price a
  radius."* Information and precision are different capabilities, and a
  blind control only tests the first.
- *"Published claims cite numbers, not artifacts."* Retrospective
  lineage over prose has a floor; citation discipline at authoring time
  is the successor.
- *"A claim about the graph is a claim in the graph."* Self-reference
  is not a paradox here; it is the object working.

## Resolved from BACKLOG

- The "reports/ has no regeneration check" entry: **pruned** — its fix
  shipped as `check_report_regeneration.py` and its own prune condition
  (v0.16's headline ships or folds) is met by the adjudication.
- The suspension entry: closed by lift, riders recorded in place.
- The gate-measurement and `ceiling_table` entries: unchanged, carried.

## Honest limits carried forward

- The void is a void: this repository still cannot certify a retraction
  radius, and every published claim outside the covered scope of the
  v0.17 design remains tethered to its evidence by nothing but memory.
  The v0.17 gate can fail too.
- R1's wording measured nothing; the honest numbers (0.800 / 1.000)
  ride beside it. A clause must name its denominator's direction.
- The veto's establishment is exploratory forever — census, no fresh
  half — and the two riders travel with every quotation of the count.
- R3's 0.143 is mostly registry scope (closures and veto ledgers are
  not graph artifacts in v1), not measured anchoring quality.
- The instruments kept from the void are green but unscored; keeping
  them is stewardship, not a claim.
- A passing Python test is not a Lean proof.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.** No
`experiments/*.py` changed since v0.15.0 and no training corpus moved —
the cycle's new committed surfaces are scripts, schemas, reports, and
the veto table — so the checkpoints attached to **v0.6.0** remain
accurate for this release. Committed in-repo instead: the provenance
graph and four radius certificates plus the blind-control report
(`reports/radius/`), the ground truths and shuffle seeds
(`data/retraction_closure/`), the blind full-cross table and rerun
result (`experiments/veto_full_cross_*.json`), and the two course
receipts (`reports/design-direction-v0.16.json`, `-v0.17.json`).

## The suite at the tip

[SUITE-GATE-V16: full-suite verdict and timing at the frozen v0.16 tip
land here before the tag; the v0.15.0 receipt is the baseline.]

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/check_report_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py
python -m unittest tests.test_retraction_closure tests.test_radius_recheck
python scripts/radius_recheck.py reports/radius/root-a-compression.cert.json
python scripts/veto_full_cross_rerun.py
python scripts/radius_blind_control.py --out blind_control.repro.json
# then diff blind_control.repro.json against the committed
# reports/radius/blind_control.json
```
