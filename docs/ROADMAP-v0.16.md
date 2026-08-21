> **CLOSED at v0.16.0.** Where each item went: **item 1** (retraction
> closure) adjudicated — R2 failed on both roots, capability VOID as
> frozen, instruments shipped unscored; see
> [RELEASE-v0.16.0](RELEASE-v0.16.0.md) headline and ANALYSIS. **Item
> 2** (veto information claim) read out ESTABLISHED, exploratory, with
> the suspension lifted under two permanent riders. **§3 carried
> lanes** moved to [ROADMAP-v0.17](ROADMAP-v0.17.md) §3 or stayed
> parked; the HTTP-skin paragraph escalates there. The **release gate**
> below was discharged clause by clause in the release notes.

# Roadmap v0.16 — say what a retraction costs before making one

v0.15 built the machine that turns "no path found" into evidence within a
bound. It also discovered, at its own release refresh, that the claim "two
ledgers are quietly stale on `main`" had itself gone quietly stale — one
drift healed at v0.11 with no accounting of what the stale window touched,
the other divergent by a decision recorded only in prose. Nothing in this
repository can say what else moves when one committed thing is found
wrong, and the claims *about* that gap are already exhibiting it. This
cycle builds the object that ends it.

Governing design: [retraction as an operation with a
receipt](DESIGN-retraction-closure.md) — chosen by the full outside course
(three isolated series, fifteen directions, receipts in
`reports/design-direction-v0.16.json`), then re-grounded against the
repository's actual retraction record, which materially changed the gate:
the two historical retractions are interpretation-shaped and calibrate the
graph's *floor*; the live anchor is the two stale-ledger drifts.

## 1. The retraction closure (headline, architecture)

Implement DESIGN-retraction-closure §5 in its registered order:

1. provenance blocks emitted by the four bare ledger writers themselves
   (the `proof_correspondence.json` precedent — writer name, input paths,
   SHA-256), never reconstructed after the fact;
2. the graph assembler over seeds, corpus files, ledgers, and anchored
   claims (`reports/provenance_graph.jsonl`);
3. the radius tool and the regeneration check — the BACKLOG's own proposed
   fix, absorbed as substrate, running beside `check_regeneration.py` in
   the release refresh;
4. hand-audited ground truth for the two adjudication roots — the healed
   silent drift of `compression.json` (stale from its last v0.10 write to
   `1090aa5`, repaired with no radius ever computed) and the declared
   divergence of `decompositions.json` (design §3 correction) — committed
   **before** the radius tool runs on them;
5. the two historical retractions replayed and reported at their true
   scope — calibration, explicitly not the gate.

**Live status (2026-08-20): ADJUDICATED — R2 failed on both roots,
capability VOID as frozen; the instruments ship unscored.** The seven
registered steps (design §6a) ran once: R5 fired (byte-identical
builds), R4 fired (the independently written recheck agrees on every
field, 0.108 s of 600), R6 reported both historical replays at their
true single-node scope, and the blind control came back 0/100 — the
edges carry information no shuffle reproduces. But Root A floods to 54
nodes against a cap of 33 with a clean 11/11 superset, Root B misses
the two number-only claims and reaches 106 against 48, and R3 anchors
2/14 release sections against a 0.90 floor. R1 fired as written
(353/353) and the wording is vacuous; the intended measure reads 0.800
all-five / 1.000 regenerable-four. Full readout: ANALYSIS "the
retraction closure: built, independently rechecked, voided by its own
gate". What survives unscored: writer provenance in all four ledger
writers, the regeneration check (now in the release refresh), the
graph/radius/recheck/control instruments, and the committed ground
truths as the bar any successor citation mechanism must meet. The
successor direction the void points at — citation discipline at
authoring time, not a better regex — is a candidate for the v0.17
course, not a patch to this cycle.

The gate is §6 as frozen: R1 writers emit ≥95% of ledger edges themselves
(fold checkpoint if a frozen instrument would have to be rewritten); R2
each live-drift closure is a superset of its pre-committed ground truth at
≤3× its size, one missed claim voids the capability, no patch-and-rerun;
R3 ≥90% of the current release's claims resolve to anchored nodes; R4 a
recheck re-derives every closure in ≤10 minutes; R5 two clean builds
reproduce `graph_sha256` byte-identically; R6 the historical replays are
reported, not scored. The blind control — 100 degree- and kind-preserving
edge shuffles, seeds committed in advance — **kills the capability** if
any shuffle satisfies R2 on both roots. Stop conditions and non-claims are
§7, and they are part of the item: conceptual dependency is out of scope
and every certificate says so.

## 2. The veto's information claim, established or expired (instrument)

v0.15 left the coincidence veto with two controls passed, one invalid by an
authoring-time scoping defect, and its information claim unestablished. The
suspension's own clause gives it two cycles. This item makes v0.16 decide
rather than drift:

1. author the incompatibility table over the **full kind cross-product**,
   blind — before looking at which pairs co-occur anywhere;
2. re-run the tag-permutation control against that table on the committed
   population (exploratory, labelled as such: the census has no fresh
   half);
3. search once for an unexamined population; the one candidate already
   measured (the nine in-field twin groups) was rejected at 29% name
   coverage, and that rejection stands unless a new population appears;
4. read out in writing: information claim established (control fails the
   shuffled tags), or **the suspension expires at this release by its own
   two-cycle clause and the cross-field match count returns to the ledger
   as an unadjudicated observation, never a result** — with the sensitivity
   analysis's one-row finding attached wherever the count is quoted.

No new rate is frozen: the population is a census, the run is exploratory,
and pretending otherwise is how controls get chosen after the fact.

**Live status (2026-08-20): READ OUT — established, exploratory;
suspension LIFTS with riders.** The 325-pair table was authored blind
in the isolation channel (brief hash and session in
`experiments/veto_full_cross_table.json`), the criterion was fixed
before it existed (`experiments/veto_full_cross_protocol.md`), and the
rerun with the committed v0.15 seed puts the real tags at 21
conflicting slots against a permuted span of 45–61 — below half the
permuted minimum. The blind table agrees with the scoped table on
43/44 shared pairs and independently reproduces the proposition|set
exemption, so the one-row finding is now a twice-made judgement. The
suspension lifts by its own clause, with the conflicting readout and
the one-row finding riding permanently beside any quotation of the
count. The population search closed in writing: no fresh half exists.
Full readout: ANALYSIS "the veto's information claim, established
blind".

## 3. Carried, with dependants named

| lane | named dependant | disposition |
|---|---|---|
| Regeneration check for `reports/` | **item 1, step 3** — a prerequisite, ordered inside the headline | absorbed from BACKLOG |
| Conservativity compiler (course series-2 lead) | *none this cycle* | **parked** — the strongest instrument candidate the course produced; enters a roadmap only after item 1 reads out, because its verdict vocabulary (NO_POWER / PUBLISH / DELETE_FIELD) presumes a provenance substrate to act on. See DESIGN-retraction-closure §2. |
| Two witnesses, absent author, expiring license, first light, load-bearing fiction → known blindness | *none* | **parked** with prerequisites priced in DESIGN-retraction-closure §2 and §8 — each becomes affordable only once scope is computable |
| HTTP skin | *none* | **parked a fourth cycle, by decision this time**: the blocker is unchanged (BACKLOG P-IH6, durable multi-session auth against a verifier *instance*), no v0.16 item depends on it, and scheduling it beside the headline would ship neither. The v0.17 rotation inherits this paragraph and the four-park history; it does not inherit silence. |
| Exclusion seam in the resolver | *none — shipped, uncredited* | unchanged; the spent sentence remains a regression test |
| Resolver coverage lane (0.833 / 0.030), A3–A5 ambiguity acceptances, verified-ambiguity check, range certification, W1–W3, both rankers, `specialize.py` index, proof-search depth, physics/affect/visual, Open-English authoring | *none* | parked in BACKLOG with reasons recorded at the v0.15 drift audit |

## 4. Governance

Unchanged from v0.15, plus the rule that cycle earned:

- **A control must be authored over the space it will be permuted across,
  not the space the data happens to occupy.** The veto's corruption
  control was scoped to authored co-occurrence and permutation starved it
  by construction. Scoping-for-reviewability and scoping-for-control are
  different acts; doing them in one table is how a control becomes
  unrunnable at exactly the moment it is needed.

## Release gate

v0.16 is ready only if:

- the retraction closure ships its first slice with R1–R6 adjudicated, or
  folds in writing at R1's checkpoint or on a clean control, with the
  reading published;
- item 2 reads out in writing — established, or expired under the
  suspension's own clause with the one-row finding attached;
- the regeneration check runs in the release refresh and its verdict on
  every committed ledger is in the notes;
- the full suite is green on a frozen tip with retained receipts;
- every unfinished item ships or parks in writing;
- the outside design inquiry gate is discharged for the next cycle — run,
  or explicitly reaffirmed with the receipt named.
