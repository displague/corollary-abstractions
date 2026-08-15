# v0.11 release triage — gate status, drift audit, and what the notes may claim

Written before the release notes so the arguable calls are visible as
calls. The forward-looking design for v0.12 is committed first:
[DESIGN-heldout-recovery.md](DESIGN-heldout-recovery.md). The blog
is not written yet; the design is the thing it is not allowed to
choose after.

## 1. Release gate

`ROADMAP-v0.11.md` §"Release gate" lists seven conditions.

| # | gate condition | status |
|---|---|---|
| 1 | self-grounding curve with its null, S1–S4 adjudicated, route-1 vs route-2 stated | **MET** — route 1; S1–S4 fired; proxy labelled (1.000 vs ISG_of_grounded 0.543). `experiments/self_grounding_curve.json` |
| 2 | one registered figure of merit, matcher recall reported | **MET** — bag precision against typed twins = 0.0220%; matcher 1,990/1,991; named print-convention miss. `docs/DESIGN-fair-fight.md` |
| 3 | skeleton emitter, remainder authored or exclusion count | **MET** — 12,514 authored, 123 excluded (`experiments/lean_workbook_emit.json`) |
| 4 | external benchmark scheduled with its claim, or parked | **MET, scheduled** — item 1 beat its null; claim is the sign-flip-then-compounding shape on a held-out source (`DESIGN-heldout-recovery.md`). Not run this cycle |
| 5 | every carried lane names its dependant or is parked | **MET** — see §3 |
| 6 | updated assets whose notes explain winners, losers, controls | **MET** — ANALYSIS carries every slice; curve JSON and bag JSON are the regenerable assets. `reports/decompositions.json` is **not** rewritten (181k constituents) — disclosed, live `analyze_loaded` is the pin source |
| 7 | the complete suite green | **PARTIAL** — graph-touching tests green (156, 1 skipped: full-graph `min_family=1` at 12k). Full discover is 30+ minutes because several tests each reload the 12k graph. Must be re-run on the tip before the tag |

**What the notes may honestly claim.** "Ingestion compounds above a
matched null at thousands" is TRUE, with the sign flip attached, not
as a footnote. "The bag still wins on count" is TRUE (9.0M vs 1,991)
and is not the figure of merit. "Thousands of ingested nodes" is TRUE
(12,514). "The external benchmark ran" is FALSE — it is scheduled.
"The suite is green" is not yet a tag-time fact.

## 2. Drift audit vs v0.10's stated goals

v0.10 carried these into v0.11. What happened:

| carried from v0.10 / v0.11 plan | landed? |
|---|---|
| Self-grounding curve + null (v0.11 item 1) | **YES** — S1–S4 fired; shape was the accident |
| Fair-fight FoM (v0.11 item 2) | **YES** — 0.0220% |
| Skeleton emitter (prerequisite) | **YES** — 12,514 / 123 |
| Programming second wave (v0.11 item 3) | **NO — carried** to v0.12 with a named dependant (H3 of the held-out design). Not parked: item 2's FoM did not need code twins, so this slice did not start |
| External benchmark (carried a third time) | **SCHEDULED**, not run — the design now exists |
| Verdict-backed ingestion as a RULE | **carried** — named dependant: held-out B |
| `TOKEN_RE` `<` `>` | **YES** (P-E1) |
| `specialize.py` cost | **PARTIAL** — ingested skip; not a general index |
| Proof-search depth | stayed parked |
| Groundedness gate | **unparked**, not designed — constraints in DESIGN-heldout-recovery.md §8 |
| Physics / affect / oscillation / visual | stayed parked |

Nothing planned was silently dropped. Item 3 is the one unfinished
half that a reader could miss: it is named here and in ROADMAP-v0.12
item 3, not absorbed into "the headlines shipped."

**vs v0.9, one more time.** The external benchmark has now been
carried through v0.9, v0.10, and v0.11 without a run. This cycle
is the first that *could* have run it (the curve exists). Scheduling
it with a written design is not a fourth silent carry — the parking
condition was evaluated (curve was not flat) and the claim is
specified. A fourth cycle that does not run H1–H6 owes a park.

## 3. Carried lanes into v0.12

| lane | named dependant in v0.12 | disposition |
|---|---|---|
| Held-out recovery (this cycle's design) | headline | **ordered first** |
| Programming second wave | H3 (keyword baseline on a second modality) | carried; parked if holdout B is cut |
| Verdict-backed ingestion RULE | held-out B | carried |
| Groundedness gate | headline, after H1 | unparked; not drawn until H1 lands |
| `specialize.py` general index | *none* | stays PARTIAL / parked |
| Proof-search depth | *none* | stays parked |
| Physics / affect / visual | *none* | stay parked |

## 4. Questions for the notes, not for a maintainer

Unlike v0.10, no pin needs a retirement decision. The eighth GC4
acknowledgment is a corpus change (12,771 nodes), already written.
The rate-gap pin stays retired.

The one honesty bound the notes must not cross: **do not lead with
S1 without the sign flip.** A reader who only sees 0.473 vs 0.410
at N=12,515 has not been told the thing v0.11 actually found.

## 5. Assets

Symbolic cycle. No new checkpoint. The regenerable artifacts:

- `experiments/self_grounding_curve.json` — S1–S4
- `experiments/item4_operator_bag.json` — FF1–FF5
- `experiments/lean_workbook_emit.json` — 123 exclusions
- `experiments/skeleton_emitter_aggregates.json` — live decompose pins

`reports/decompositions.json` remains the pre-scale file. The notes
say so.
