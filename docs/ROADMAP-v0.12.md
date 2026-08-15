# v0.12 roadmap — does the sign flip travel?

v0.11 measured ingestion on the source the emitter was built for
and found compounding *and* a shape nobody asked for: below chance
at N=32, above it from N=128. v0.12 asks whether that shape is a
fact about the architecture or a fact about Lean-workbook.

The design is committed and its predictions are frozen:
[DESIGN-heldout-recovery.md](DESIGN-heldout-recovery.md), written
during v0.11 triage *before* the v0.11 blog, so the next question
could not be chosen to flatter the post.

**House rule (kept):** every carried lane names the headline item
that depends on it, or is parked in BACKLOG with a reason.

---

## 1. Held-out structure recovery (headline)

Two holdouts, because one size already lied: miniF2F (163
full-statement-covered — the small-N test) and a seeded Goedel-Pset
sample (~2,048 unique-covered the emitter can parse — the scale
test). Same ISG question, route 1, same null. A keyword / operator-bag
baseline that is forbidden from seeing owner ids.

Lean-workbook is not held-out. A 20% slice of it is a split, not a
source holdout.

**Acceptance:** `experiments/heldout_recovery.json` with H1–H6
adjudicated exact to the row. H2 (the sign flip recurs at N=8/32)
is load-bearing. If H1 fails, the groundedness gate stays undrawn.

**Prerequisite, ordered before the scale cut:** emit the miniF2F
covered subset through the existing emitter (no matcher widening).
Named dependant: this item's small-N half.

## 2. Groundedness gate, designed after H1 (headline, gated)

Unparked in v0.11 because S1–S4 fired. Not designed there, on
purpose — a threshold fitted to Lean-workbook's 0.473 is a snapshot.
DESIGN-heldout-recovery.md §8 freezes three constraints: route 1
never the proxy; argue against `external_lower`; do not draw until
H1 lands.

**Acceptance:** a written gate with those three constraints, a
registered prediction about what it would refuse on the holdout,
and a conservative-bracket demonstration. If H1 fails, this item
is parked in BACKLOG in writing.

## 3. Programming discipline, second wave (carried from v0.11 item 3)

**SHIPPED on the v0.11 branch** (so H3 has its second-modality
sample). Same TheAlgorithms pin, three more files, six new nodes,
volume tests, vocabulary decision survives. The code-twin keyword
baseline is now a measured number (precision 0.4 combined, 1/3 on
the factorial foil set) rather than a planned control.
**Named dependant:** item 1's H3 — still load-bearing; this slice
supplied the sample, it did not run the holdout.

## 4. Verdict-backed ingestion as a RULE (carried)

**Named dependant:** item 1, held-out B. A Goedel-Pset node that
cites `verified_by` without a PASS is the case the rule exists to
refuse.

## 5. Carried lanes

| lane | named dependant | disposition |
|---|---|---|
| miniF2F emit through the existing emitter | item 1 small-N | **prerequisite**, ordered first |
| Goedel-Pset seeded sample | item 1 scale | **prerequisite**, ordered with it |
| Programming second wave | item 1 H3 | **SHIPPED** (sample exists; H3 still unrun) |
| Verdict RULE | item 1 B | carried |
| Groundedness gate | item 2 | gated on H1 |
| `specialize.py` general index | *none* | **parked** |
| Proof-search depth | *none* | **parked** |
| Physics / affect / visual | *none* | remain parked |

## 6. Governance

Unchanged from v0.11: capability-blind baselines; negatives
first-class; designs before runs; guard pins that move get a
decision. Independent review at every trust boundary — v0.11's
emitter slice and the measurement slice that followed it shared
one working tree; v0.12 does not repeat that.

## Release gate

v0.12 is ready only if it contains:

- the held-out curve with its null and the keyword baseline,
  H1–H6 adjudicated, Lean-workbook *not* reported as held-out;
- either the groundedness gate designed under §8's constraints,
  or a written park because H1 failed;
- item 3 shipped or parked with the H3 dependant evaluated;
- every carried lane naming its dependant or parked;
- updated assets with winners, losers, and controls;
- the complete suite green.
