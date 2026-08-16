# Design — held-out structure recovery (forward-looking, for ROADMAP-v0.12)

Written during v0.11 release prep, *before* the v0.11 blog post, so the
next cycle's question is chosen from the evidence and not from the
argument we will make about it. This is the release's forward-looking
design item; it does not ship in v0.11.

## 1. Where this came from (an accident, not the plan)

v0.11 asked whether ingested self-grounding outruns a
distribution-matched null as the layer grows from 8 to 12,515. S1–S4
all fired. That is the planned result.

The accident is the *shape* of the curve, which nobody wrote down as
the thing to find:

| N | ISG_real − ISG_null |
|---:|---:|
| 8 | **−0.041** |
| 32 | **−0.024** |
| 128 | +0.046 |
| 512 | +0.042 |
| 12,515 | +0.063 |

At the sizes v0.10 actually had, the real layer sits *below* chance.
Shared squares and numerals do not beat random trees drawn from the
same inventory. A curve stopped at hundreds — the honest limit of the
first wave — could have been published as "ingestion does not
compound." The sign flips by N=128. Compounding is a large-N fact.

Two other accidents travel with it:

- **The rejected proxy is 1.0.** At full N, 181,270 / 181,276 grounded
  constituents have some ingested co-host. Route-1 ISG of those same
  constituents is 0.543. Sharing is nearly universal on this layer.
  Grounding is not. Any later measurement that reports the proxy as
  ISG is publishing a vacuous 1.0.
- **S4 inverted.** Dropping the most common subterm (`^(?0:V, 2)`,
  6,870 hosts) *raises* the gap from 0.063 to 0.127. The popular term
  was curated-owned. It was diluting the rate, not carrying it. The
  feared failure (a curve about one fashionable square) is the
  opposite of what happened.

v0.11 item 4 — the external benchmark, carried three times — was
scheduled rather than parked because S1 fired. This note is what that
scheduling *is*. A benchmark that only re-runs Lean-workbook at N=12k
is a re-measurement, not a held-out.

## 2. The question

**Does the sign-flip-then-compounding shape survive a source the
emitter was not fitted to, against a baseline that cannot see owner
ids?**

Three answers, all publishable:

- **The shape recurs, and beats a keyword baseline.** Structure
  recovery is a fact about the architecture, not about Lean-workbook
  inequalities. That is the claim v0.9 item 4 has been waiting to
  make.
- **The shape recurs, and the keyword baseline matches the real
  curve.** Then owner identity is not doing the work we attributed to
  it — the proxy lesson, one source later.
- **The shape does not recur.** Lean-workbook's compounding is a
  fact about that set (olympiad inequalities that share AM-GM
  skeletons). Ingestion still buys coverage. It does not buy a
  transferable structure-recovery claim. The more interesting
  negative, and the one a blog will have to live with if it happens.

The v0.11 null is not enough on its own for a "benchmark." A keyword
baseline that is *forbidden from reading `owners`* is the
capability-blind arm the architecture is supposed to beat by
construction.

## 3. Two held-outs, because one size lied to us once

A single held-out at N≈160 would be the v0.10 mistake again: it sits
in the regime where Lean-workbook itself was below the null.

**Held-out A — miniF2F, the small-N test.** The committed extract
already exists (`data_sources/derived/minif2f/statements.json`).
Full-statement coverage is 163 / 488 (33.4%). Competition problems,
not inequality drills. Author via the same emitter, unique-covered,
formal-without-bridge. The curve is run at 8 / 32 / all. This cut
can *fail* H1 and that is a result: 163 nodes is exactly the size at
which we now know a real curve can look like chance.

**Held-out B — a seeded Goedel-Pset sample, the scale test.** The
coverage instrument already walked 1.73M statements. Author a
committed, seeded sample of unique-covered goals the emitter can
parse (target 2,048, or whatever the emitter actually emits —
counted, not padded). Different distribution from Lean-workbook
(the 1.73M gap table is the prior). Curve at 8 / 32 / 128 / 512 /
all. This is the N at which Lean-workbook's sign flipped and then
held.

Lean-workbook itself is **not** held-out. A random 20% slice of it
is a split, not a source holdout. Do not report a Lean-workbook
split as H1.

Already-authored ids are skipped. The emitter is not widened for
these sources; exclusions are counted, as v0.11 did.

## 4. The measurement

Same definitions as v0.11, route 1, no silent switch to the proxy:

- **ISG(N)** — of considered subterms in the *held-out ingested*
  nodes, the fraction whose most-independent owner is another
  ingested node from that same held-out layer. Lean-workbook nodes,
  if present in the graph, count as **curated-relative to the
  holdout** (XSG or `prior_corpus` / `external` as the channels
  already decide). Mixing holdout-ISG with Lean-workbook owners
  would let the 12k layer gift the holdout a curve.
- **XSG(N)** — fraction whose most-independent owner is *not* in
  the holdout ingested layer (hand-authored, or the other ingested
  corpus). Reported beside ISG.
- **Proxy(N)** — the rejected control: grounded constituent whose
  skeleton occurs in some other holdout-ingested node. Labelled.
  Never the headline.
- **Keyword / bag baseline** — two holdout statements "ground" a
  shared subterm iff they share the operator-bag glyph set
  `{+,-,*,/,^,=}` (the same capability-blind bag item 2 already
  used). The baseline is forbidden from reading `owners`,
  `owner_channels`, or any decompose field. Its "ISG" is a
  co-occurrence rate over bags, not over attributed owners. The
  claim is that this rate does not produce ISG_real − ISG_null > 0
  growing with N.

Each point is recomputed by the committed generator
(`scripts/measure_self_grounding.py` or a thin sibling that pins
the holdout id set). Specialize is not invoked. Pattern membership
off. Subsamples seeded and committed.

The curve is committed as `experiments/heldout_recovery.json`.

## 5. Registered predictions (frozen before any holdout is authored)

Written against v0.11's Lean-workbook curve and the committed
miniF2F / Goedel-Pset coverage numbers. No holdout node has been
emitted for this design.

- **H1** (scale, held-out B): at the largest authored Goedel-Pset
  N, ISG_real > ISG_null by more than that null's seed-to-seed
  spread. Same predicate as S1, new source.
- **H2** (sign flip, both holdouts): at N=8 and N=32, ISG_real ≤
  ISG_null on at least one holdout. The v0.11 small-N deficit is
  predicted to be a size effect, not a Lean-workbook effect. If
  both holdouts sit *above* the null at N=32, H2 fails and the
  sign flip was source-specific.
- **H3** (keyword cannot steal the gap): on held-out B at largest
  N, the bag/keyword co-occurrence "ISG" minus its own matched
  null is ≤ 0, or is smaller than the owner-ISG gap by more than
  the owner-null spread. A baseline that cannot see `owners`
  cannot reproduce the owner-attributed gap.
- **H4** (proxy is not ISG): on both holdouts at largest N,
  proxy − ISG_of_grounded > 0.2. If the proxy and ISG agree, the
  0.457 Lean-workbook gap was a fact about that layer's
  redundancy, not about the measurement.
- **H5** (S4-style, held-out B): H1 survives deleting the single
  most common holdout subterm. Direction is *not* predicted —
  v0.11's popular term diluted ISG; a holdout's popular term
  might carry it. Either way the number is reported.
- **H6** (XSG): on held-out B, XSG does not fall by as much as
  ISG rises from N=8 to N_max (the S3 shape).

H2 is the one most likely to be read as a failure if it fires, and
it is the one that would matter most. A holdout that beats chance
at N=32 would say Lean-workbook's early deficit was about
inequality drills sharing squares, not about size.

## 6. What this rests on, and what it is not

Rests on: the v0.11 emitter and its exclusion discipline, route-1
owner ids, `analyze_loaded` (so the curve does not re-parse 12k
templates per point), the ingested specialize / pattern skips, and
the committed miniF2F and Goedel-Pset extracts.

It is **not** a claim that a held-out ISG gap implies the holdout
statements are true, useful, or proved. Formal-without-bridge
stays. It is not a widening of the emitter to chase coverage. It
is not the groundedness gate (see §8).

## 7. Cost, inherited and new

- The curve is decomposition-only. Specialize stays skipped for
  ingested endpoints.
- miniF2F at 163 nodes is cheap. A 2,048-node Goedel-Pset overlay
  on the existing 12,771-node graph is the cost to plan for:
  `analyze_loaded` with `keep` / `extra`, not a full
  `decompose.py` rewrite of `reports/decompositions.json`.
- `TOKEN_RE` already has `<` `>`. Greek is transliterated. New
  exclusion buckets on Goedel-Pset are counted, not forced.

## 8. The groundedness gate (unparked, not designed here)

v0.11 unparked the gate because S1–S4 fired. This note does **not**
specify the gate. Three constraints any later design must inherit,
or it is designing against a regime:

1. The gate reads route-1 owner identity, never the proxy.
2. It is argued against `external_lower` / `independent_lower`,
   not against the generous external share.
3. It is not fitted to Lean-workbook's 0.473. H1–H6 land first;
   a threshold chosen before the holdout runs is a snapshot of
   this source.

If H1 fails, the gate stays undrawn — the parking condition
returns.

## 10. Adjudication — H1–H6 after the run (v0.12)

§5 is frozen as registered and is not edited here. Artifact:
`experiments/heldout_recovery.json`, from
`scripts/measure_heldout_recovery.py` (route 1, `pattern_membership=False`,
null seeds 0/1/2, selection seed 20260816). Both holdouts are quarantined
corpora; the other holdout is never loaded into a run.

**The curves.**

| holdout | N | real ISG | null mean | gap |
|---|---:|---:|---:|---:|
| miniF2F (A) | 8 | 0.00000 | 0.01626 | −0.01626 |
| | 32 | 0.00000 | 0.00991 | −0.00991 |
| | 157 | 0.00547 | 0.04823 | −0.04276 |
| Goedel-Pset (B) | 8 | 0.00000 | 0.00000 | 0.00000 |
| | 32 | 0.00000 | 0.00936 | −0.00936 |
| | 128 | 0.00725 | 0.05354 | −0.04629 |
| | 512 | 0.01442 | 0.10750 | −0.09308 |
| | 1896 | 0.02537 | 0.15125 | **−0.12588** |

| | outcome |
|---|---|
| **H1** (scale, B) | **MISSED** |
| **H2** (sign flip) | **FIRED** |
| **H3** (keyword cannot steal it) | **FIRED**, but weakly — see below |
| **H4** (proxy is not ISG) | **FIRED**, decisively |
| **H5** (S4-style, B) | **MISSED**, and conditional on H1 |
| **H6** (XSG) | **FIRED** |

**H1 — MISSED.** At N=1,896 the real rate is 0.02537 against a null mean
of 0.15125: the holdout sits **far below** its matched null, and the gap
grows *monotonically more negative* with N (−0.009 → −0.046 → −0.093 →
−0.126). This is not a curve that failed to flip; it is a curve running the
other way. Lean-workbook's compounding is a fact about Lean-workbook.

This is §2's third answer, the one the design called the more interesting
negative: **ingestion still buys coverage. It does not buy a transferable
structure-recovery claim.**

**H2 — FIRED**, on both holdouts, at both small sizes. But note what it is
worth now: H2 predicted the small-N deficit was a size effect rather than a
Lean-workbook effect. It fired, and H1's miss shows the deficit was not a
*stage* the holdouts would grow out of. H2 firing is therefore consistent
with the negative, not a consolation for it.

**H3 — FIRED, and the firing is weak.** `bag_gap` = −0.0058 ≤ 0, so the
predicate is satisfied. The honest reading is that the capability-blind bag
cannot steal a positive gap because **there is no positive gap to steal**,
and the bag is itself saturated at this scale: 0.9937 real against 0.9995
null, both ≈ 1.0. H3 was designed to discriminate in a world where H1
fired. In this world it is nearly vacuous and is reported as such rather
than counted as a win.

**H4 — FIRED, decisively, and it is the result that most earns its keep.**

| holdout | proxy | ISG of grounded | difference |
|---|---:|---:|---:|
| miniF2F | 0.7080 | 0.0077 | **0.7003** |
| Goedel-Pset | 0.9240 | 0.0404 | **0.8835** |

Both far above the registered 0.2. Had v0.11 shipped the sharing proxy as
its headline, these two holdouts would have reported 71% and 92%
"self-grounding" on sources that recover essentially nothing. The refusal
to use the proxy is what makes this cycle's negative legible at all.

**H5 — MISSED, and it could not have fired.** H5 asks whether H1 survives
deleting the most common holdout subterm. H1 did not hold, so there was no
gap to survive. Dropping `^(?0:V, 2)` moves the gap from −0.12588 to
−0.12474 — it changes essentially nothing, which does at least say the
negative is not an artifact of one fashionable square. Recorded as a miss
because the predicate is written on H1, not re-scored as a pass on a
technicality.

**H6 — FIRED.** XSG falls by 0.0055 while ISG rises by 0.0254 from N=8 to
N=1,896. The S3 shape holds: the holdout's parts do not stop having owners
as the layer grows, they simply keep having *external* ones. XSG stays near
0.59–0.63 throughout. The parts are grounded; they are grounded by the
curated and Lean-workbook layers, not by each other.

**One degenerate cell, disclosed.** Goedel-Pset at N=8 has real 0.0 and all
three nulls 0.0, so its gap is exactly 0.0. That cell is vacuous — two
zeros, not a measured agreement — and is excluded from any reading of the
trend. The trend is carried by 32 / 128 / 512 / 1896.

**What this licenses, with C1 attached.** See
[DESIGN-matched-n-control.md](DESIGN-matched-n-control.md): at identical
N=157 the fitted source scores +0.0496 and the held-out source −0.0428,
opposite in sign and separated by 1.9× the combined null spread. So the
negative is **not** an artifact of holdout size. Source, not scale.

**Consequence for the groundedness gate.** §8's parking condition returns:
H1 failed, so the gate stays undrawn and is parked in `docs/BACKLOG.md` in
writing. Nothing is fitted to Lean-workbook's 0.473.

## 9. What v0.12 owes besides this

Named so they do not ride as lanes:

| item | relation to this design |
|---|---|
| Programming second wave (v0.11 item 3) | **SHIPPED; named dependant: H3.** The code-twin sample now exists (factorial foil set, combined keyword precision 0.4). If this design is cut to miniF2F-only, the sample remains; H3 itself would then have no holdout B to run on. |
| Verdict-backed ingestion as a RULE | named dependant: held-out B. A Goedel-Pset sample that cites `verified_by` without a PASS is the case the rule exists to refuse. |
| `specialize.py` general index | none. Remains PARTIAL. Unpark when a curated-scale growth needs it. |

Item 3 is not silently parked. It is sequenced: holdout B's
keyword-baseline claim is stronger with a second modality in the
sample, and weaker (and parked) if that sample is never authored.
