# v0.11 roadmap — measure what ingestion actually bought

v0.10 authored ingested statements at hundreds and learned two things that
set this cycle's agenda: a capability-blind baseline still wins on pair
count while losing on precision, and ingested statements ground each other
in a way nobody designed for. v0.11 turns the second into a measurement and
makes the first a fair fight.

**House rule adopted this cycle (from v0.10's drift audit):** every carried
lane below **names the headline item that depends on it**, or is parked in
BACKLOG with a reason. A lane that blocks a headline item is not a lane — it
is a prerequisite, and it is ordered before its dependant. This exists
because the multi-corpus WRITE patch rode two cycles as the least prominent
entry in a carried-lanes list and then blocked v0.10's headline authoring
item.

---

## 1. Self-grounding ingestion, measured against a null (headline, forward-looking)

The design is committed and its predictions are frozen:
[DESIGN-self-grounding-ingestion.md](DESIGN-self-grounding-ingestion.md),
written *before* item 4's corpus existed so the null model could not be
chosen after seeing the curve.

The question: as ingested nodes go from hundreds to thousands, does the share
of subterms grounded **inside** the ingested layer rise faster than chance,
or flatten because ingested statements are mutually alien? Rising means
ingestion **compounds** — the bet the program has made informally since v0.9.
Flat means it buys coverage and not structure, which changes what the corpus
is for. The negative is the more interesting answer and is publishable either
way.

What v0.10 already put on the board, and what it is **not**: two ingested
statements grounding each other at n=2, and 614 `same_corpus` constituents at
n=251. That is two observations, not a curve, and no null has been run.

**Decision this slice owes, explicitly** (design §6): the ledger records
owner-channel *tallies* but not owner *ids*, so ISG as designed is not a
query over committed artifacts. Route 1 emits owner ids from `decompose.py`
(additive, rewrites every ledger row, needs a quiet `main`); route 2 measures
the shared-skeleton proxy, which reads **higher** because sharing is
symmetric and grounding is not. Pick one in writing; if the proxy ships, the
release says so.

**Acceptance:** a committed `experiments/self_grounding_curve.json` with real
and null curves at several corpus sizes, S1–S4 adjudicated exact to the row,
and S4 (does the effect survive deleting the most common subterm?) treated as
load-bearing rather than a footnote.

**Prerequisite, ordered before it:** the **skeleton emitter** for the
remaining 12,681 unique-covered statements (carried from v0.10 item 4).
Named dependant: this item — the curve needs thousands, not hundreds.

## 2. Make the baseline comparison a fair fight (headline)

v0.10's headline negative is real but under-analysed: the bag forms 7,622
pairs at 1.26% precision, the matcher 96 at 1.0. Count and precision are
being compared without a single figure of merit, which lets either side
claim victory.

- Define and register the comparison **before** re-running it: a recall
  estimate against an adjudicated sample, an F-style combination, or an
  explicit statement that precision-at-fixed-count is the only fair frame.
- Report the matcher's **recall** honestly. 96 pairs at precision 1.0 may be
  a small, correct answer to a large question.
- The baseline must stay capability-blind and must not be tuned to lose.

**Acceptance:** one registered metric, one table, and a sentence a skeptic
can hold the project to.

## 3. Programming discipline, second wave (carried from v0.10 item 3)

Item 3 shipped three verified-code nodes and a twin result against a blind
baseline. Extend to a source with real test cases at volume, and answer
whether the `python-tests` verdict vocabulary decision (a citation of a
committed check, never PROVEN) survives contact with more code.
**Named dependant:** item 2's fair-fight comparison, which is stronger with
code twins in the sample.

## 4. The external benchmark (carried a THIRD time — schedule or park)

Carried from v0.9 item 4 and v0.10 item 6, never started, each time honestly
sequenced behind the corpus work. Under this roadmap's own rule it now needs
a named dependant or a parking notice.

**Named dependant:** item 1. The self-grounding curve, if it beats its null,
*is* the benchmark's core claim — structure recovery on a corpus large enough
to be uncomfortable, against a null a keyword baseline cannot beat by
construction. If item 1 returns a flat curve, **this item is parked in
BACKLOG in writing**, because the architecture would then have no
structure-recovery claim worth benchmarking.

## 5. Carried lanes, each with its dependant named

| lane | named dependant | disposition |
|---|---|---|
| Skeleton emitter for the 12,681 remainder | item 1 | **prerequisite**, ordered first |
| Verdict-backed ingestion as a RULE (a manifest entry declaring a source must carry a PASS) | item 3 | carried |
| `TOKEN_RE` missing standalone `<` `>` | item 1 (51 statements it excluded) | carried |
| `specialize.py` cost at scale | item 1 (the curve re-runs ledgers) | carried |
| Proof-search depth | *none* | **parked** in BACKLOG |
| Groundedness gate | *none* | **parked** in BACKLOG |
| Physics / affect / oscillation / visual rungs | *none* | remain parked |

## 6. Governance

- Every claim beats a capability-blind baseline; negatives are first-class
  (v0.10 shipped four).
- Independent adversarial review at every trust boundary — it caught a real
  defect six times out of six in v0.10, and the one slice that skipped it is
  disclosed in the release notes rather than smoothed over.
- Designs registered before implementation, adjudicated after, corrections
  appended rather than edited into the prediction.
- **Guard pins that moved get a decision, not a re-pin** (v0.10 retired the
  absorption rate-gap pin under this rule).

## Release gate

v0.11 is ready only if it contains:

- the self-grounding curve with its null, S1–S4 adjudicated, and the route-1
  vs route-2 choice stated in the release notes;
- a registered, single figure of merit for the matcher-vs-baseline
  comparison, with the matcher's recall reported;
- the skeleton emitter, with the remainder authored or an explicit count of
  what it still excludes and why;
- either the external benchmark scheduled with its claim, or a written
  parking notice;
- every carried lane naming its dependant or parked in BACKLOG;
- updated assets whose notes explain winners, losers, and controls;
- the complete suite green.
