# Retraction as an operation with a receipt

Status: **design only; chosen v0.16 direction. No graph, certificate, tool,
or replay exists.** The v0.15 cycle's incumbent
([compile the space before asking the question](DESIGN-compile-before-query.md))
remains the current architecture and is not superseded; this direction is
what follows it. Course receipt: `reports/design-direction-v0.16.json`.

## 1. The larger move

The project can regenerate every artifact byte-identically and still cannot
answer the question its own history asks most urgently: *if this input is
wrong, what exactly falls?* Reproducibility runs forward; consequence runs
backward, and scoping a correction is today a human estimate — which is
precisely where this project has failed before. The move is to make every
published claim carry its computed dependency closure, so that retraction
stops being an apology and becomes an operation with a receipt, and so the
program can state, before publishing, what it is risking.

## 2. How the direction was chosen, and what was declined

Three independent outside series ran under the forge-design-direction skill
(funnel form: five directions each, narrowed to three under reactive
constraints, one preregistration-shaped lead each), isolated by the headless
sandboxed channel the v0.15 receipt verified. Fifteen directions were
proposed; nothing here wastes them — each is either taken, declined with its
reason, or parked with its prerequisite named.

**Series 1** (no exclusions) proposed: certified absence by exhaustion
(*Empty Room*), computed retraction closure (*Blast Radius*), dual
independent verification with a disagreement ledger (*Two Witnesses*),
outside adversarial attestation (*Bounty Board*), and machinery-emitted
novel statements (*First Light*). Empty Room independently reinvented the
incumbent's bounded-negative territory — recorded as convergent evidence
that certified absence is a natural next claim-kind, and refolded toward
absence over the library's relationship spaces, where it ranked last on
rate: its fragment/confluence machinery is front-loaded and its first cycle
would mostly buy an unadjudicated remainder. Bounty Board folded into Two
Witnesses' optional outside lane. First Light was withdrawn by its own
series: a single interesting generated statement is the exact shape of bait
this program has swallowed twice, and it should return only after
retraction is cheap — which is this design's job. Two Witnesses is the
named runner-up of the whole course: every split between two code-disjoint
verifiers is information one maintainer cannot buy any other way, and its
first slice (the proof-assistant bridge as second witness) should be
considered for the cycle after next.

**Series 2** (series 1 excluded) proposed: premise-necessity witnesses
(*Load-Bearing*), discharged-obligation licenses for graded components
(*Learning License*), a proved translation property over the library's
parallel notations (*Conservativity Compiler*), exact answers in an
approximation-native discipline (*Tolerance Zero*), and a calibration
scoreboard of preregistered forecasts (*Outside Scoreboard*). Its final
ranked Conservativity first on information per unit effort, and the case is
real: the library's non-canonical `equivalent_forms` notations are believed
equivalent by construction and checked by nothing, and its verdict
vocabulary (NO_POWER / PUBLISH / DELETE_FIELD) is honest in every branch.
It is declined as the cycle's direction for one reason: it is an
instrument, self-terminating by design, and the direction slot belongs to
the architecture that other instruments — including this one — need
underneath them. It is the strongest candidate for the v0.16 instrument
lane beside this design, the way the coincidence veto sat beside
compile-before-query in v0.15. Tolerance Zero was dropped by its own
series (the pinned-license data rule removes the contact with real
approximate practice that gave it value). Learning License merged with
Outside Scoreboard into an expiring, build-breaking license mechanism —
parked with its prerequisite named: license revocations are retractions,
and revoking one safely wants computed scope. Load-Bearing parks behind
the same prerequisite plus a frozen `instantiable` denominator.

**Series 3** (both series and the project's own occupied ground excluded)
proposed: a machine-checkable metatheorem on matcher blindness (*Known
Blindness*), ex-ante rung-upgrade pricing (*Ticket Price*), record
sufficiency without its author (*Empty Chair*), the narrative checker
carrying geometry proof obligations (*Load-Bearing Fiction*), and
reproducibility as a dated environment warranty (*Cold Storage*). Ticket
Price died on its own contamination analysis (history-mined upgrades are
n<20 and author-shaped, and it is the most score-shaped proposal of the
fifteen). Empty Chair and Cold Storage merged into *Absent Author* —
machine-attested handoff with a gutted-checkout control — which won its
series and is parked here with admiration and a prerequisite: a stranger
attesting the record's sufficiency should have the provenance graph to
consult, and its own residual (one self-selected task) wants the
per-subsystem ablation that only comes later. Load-Bearing Fiction is the
series' runner-up and stays sequenced before Known Blindness, whose
best inputs are the mutation classes Fiction's gate fails to catch.

Blast Radius was selected because it is the only direction the others keep
citing as their own prerequisite; because it converts the program's
recorded failure mode from a habit into a checked operation; and because —
after grounding, below — it turns out to have a live, bleeding test case
on `main` today, which none of the other fourteen can claim.

## 3. Grounded against the record, including what the proposal got wrong

The outside series assumed the two public retractions carried a rich
dependency footprint and built its gate (closure ⊇ actual scope, ≤3×
excess) on replaying them. Inspection says otherwise, and the design
absorbs it rather than hiding it:

- **Retraction 1** ("recombination solved", commit `0daf970`): a 28-line
  edit to `experiments/ANALYSIS.md`. The 1.000 table survived as measured;
  what fell was the *interpretation*, killed by a content-free structural
  rule scoring 1.000 blind.
- **Retraction 2** ("struct wins test", commit `dc3ff14`): a 13-line edit
  plus four seed artifacts. The ordering fell to three-seed reruns; the
  headline char-at-chance finding stood.

Both retractions were interpretation-shaped, with a blast radius of one
file section each. The outside proposal's own residual-risk note — "the
falsified thing was never anybody's input" — is not a tail risk here; it
is what both labeled examples actually were. A gate load-bearing on their
replay would be fit to n=2 near-empty closures and would certify almost
nothing.

What the record supplies instead is stronger and current:

- The four core corpus ledgers (`reports/compression.json`,
  `decompositions.json`, `specializations.json`,
  `signature_matches.json`) carry **no provenance at all** — no writer
  name, no input identity. Which script produces which ledger is knowable
  only from a comment in `scripts/verify_slice.py`.
- Two of them are **already stale on `main`** (BACKLOG, "reports/ has no
  regeneration check"): re-running the unmodified writers produces a
  46-line diff in `compression.json` and a 290-line diff in
  `decompositions.json`, and `logic.inference.hypothetical_syllogism` is
  missing from the compression ledger entirely. Nothing noticed.
- The repo already owns the conventions this design needs, unevenly
  applied: `proof_correspondence.json` pins its inputs by SHA-256;
  `experiments/wold_reach.json` names its generator and source; the
  `test_gate_v014` manifest is the strongest provenance object in the
  repo. The gap is not invention; it is that the *core artifact chain* —
  seeds → data → reports → ANALYSIS claims → release claims — never
  adopted what the periphery already does.

So the first slice anchors on the live defect, keeps the historical
replays as calibration demonstrations reported at their true (small)
scope, and lets the two in-flight ledger drifts — real, current, with
ground truth auditable by hand — carry the load the retraction replays
cannot.

### Correction (2026-08-20, before any preregistration): the anchors moved

Re-verifying at the v0.15.0 release refresh: `compression.json`
regenerates **byte-identically** at the current tip. The 46-line drift
was real, but it was healed at the v0.11 release refresh
(`1090aa5`, "refresh the ledgers … fix the drift it found") — and no one
ever computed which published claims had consumed the stale ledger during
its stale window. `decompositions.json` does diverge from its writer, but
by a *documented decision* (TRIAGE-v0.11, gate table row 6 and §5: live
analysis is the pin source; the committed file stays the pre-scale
ledger), which is a
different epistemic object than silent staleness. The paragraph above
inherited "two ledgers are already stale on `main`" from a BACKLOG entry
describing an older tip — an unprovenanced claim that drifted, in a
design document about unprovenanced claims drifting. It stays visible
above, corrected here rather than rewritten, because it is this design's
own first exhibit.

The two R2 adjudication roots are therefore restated, both still real
and still hand-auditable:

- **Root A — the healed silent drift.** `compression.json` was stale
  from its last v0.10 write until `1090aa5`. The window, the diff, and
  every claim published against the stale bytes are reconstructable from
  git. Ground truth: the hand-audited list of claims that consumed the
  stale ledger inside that window. The radius certificate's
  falsification kind is `ledger_stale`; that the drift was repaired
  without one is the defect being priced.
- **Root B — the declared divergence.** `decompositions.json` is the
  pre-scale ledger by decision, and the decision lives in prose that no
  artifact links to. Ground truth: the hand-audited list of published
  claims that cite the committed file's numbers as *current*. A correct
  closure separates claims anchored to the declared snapshot from claims
  that silently assume freshness — if the second set is empty, the
  certificate proving it empty is the deliverable, not an embarrassment.

R2's superset-and-≤3× arithmetic is unchanged; only the roots' stories
are corrected. Everything else in this section stands as written.

## 4. The new objects

**The provenance graph** — `reports/provenance_graph.jsonl`, generated,
never hand-edited. One node per line:

```text
node_id, kind ∈ { seed_script | corpus_file | external_source |
                  report_ledger | ledger_section | analysis_claim |
                  release_claim },
content_sha256, produced_by, first_seen_build
```

and one edge per line:

```text
edge_id, from_node, to_node,
relation ∈ { derived_from | pinned_from | asserted_by | published_in },
emitted_by, inferred: bool
```

Edges are **emitted by the writers themselves at generation time**
(`inferred: false`), the way `proof_correspondence.json` already emits its
`inputs` block; an edge reconstructed after the fact by any other means is
`inferred: true` and excluded from every scored clause. Claims
(`analysis_claim`, `release_claim`) are nodes only when they carry a
machine-locatable anchor — a section heading plus a committed hash of its
text; prose with no anchor stays outside the graph and is listed as
unprovenanced, never silently omitted.

### Clarification (2026-08-20, before any builder): who counts as a writer

Read strictly, the paragraph above makes R2 unsatisfiable: a claim's
edges cannot be emitted by a ledger writer (the claim postdates the
write), and if every non-writer edge is excluded from every scored
clause, no scored closure can contain a claim. The intent is registered
here, before the assembler exists:

- `inferred: false` belongs to an edge whose emitter is a deterministic
  function of committed bytes, run at generation time. That is two
  cases: a **report writer** emitting its own input edges, and the
  **assembler** emitting structural and citation edges (claim
  `asserted_by` its section, section `published_in` its document, claim
  `derived_from` an artifact it cites) computed by a fixed, committed
  scan over the committed text. The assembler is those edges' writer;
  R5's byte-reproducibility clause covers them exactly as it covers the
  rest of the graph.
- `inferred: true` is reserved for edges added by hand or recovered
  heuristically where a writer should have emitted and did not — the
  committed `decompositions.json`, written before provenance blocks
  existed, is the standing example. These are excluded from every
  scored clause, including closure traversal.
- Scored closures (R2, and the blind control's shuffled closures)
  traverse `inferred: false` edges only.
- **The citation scan must not read the ground truth.** R2 compares a
  mechanically derived closure against an independently hand-audited
  list; an assembler that consumes
  `data/retraction_closure/ground_truth_*.json` would make the clause a
  tautology. A test enforces this by scanning the assembler's source,
  the same way the bounded-closure suite forbids world-name literals in
  the generic layer.

**The radius certificate** — `reports/radius/<cert_id>.cert.json`:

```text
cert_id, root_node,
root_falsification_kind ∈ { witness_invalid | source_unpinned |
                            standing_demoted | script_defect |
                            ledger_stale },
closure: [node_id], closure_size, depth_histogram,
unprovenanced_nodes: [node_id], inferred_edges_excluded: [edge_id],
graph_sha256, tool_version, recheck_command
```

**The regeneration check** — the BACKLOG's own proposed fix, absorbed as
this slice's substrate rather than a separate chore: each report writer
re-runs into a temp path and diffs against the committed ledger, and the
check runs beside `check_regeneration.py` in the release skill's refresh
step. A drift is a `ledger_stale` root, and its certificate is the tool's
first real work.

## 5. First slice

1. Add provenance blocks to the four bare ledgers, emitted by their own
   writers (writer name, input paths with SHA-256), following the
   `proof_correspondence.json` precedent.
2. Build the graph assembler over seeds, corpus files, ledgers, and the
   anchored claims of ANALYSIS and the current release notes.
3. Build the radius tool and the regeneration check.
4. Adjudicate the two live drifts: commit a hand-audited ground-truth list
   of every downstream claim the `compression.json` and
   `decompositions.json` drifts touch, BEFORE the radius tool runs on
   them.
5. Replay the two historical retractions and report their computed radii
   at their true scope, as calibration — explicitly not as the gate.

## 6. Construction gate (numbers frozen here)

- **R1 — writers emit their own edges.** ≥95% of edges into
  `report_ledger` and `ledger_section` nodes carry `inferred: false`.
  Mid-cycle checkpoint: if the writers cannot be made to emit without
  rewriting a frozen instrument, fold the direction and publish the fold.
- **R2 — the live drifts are explained, superset-exactly.** For each of
  the two stale-ledger roots, the computed closure must be a superset of
  the pre-committed hand-audited ground truth, with
  `closure_size ≤ 3 × |ground truth|`. One missed claim voids the
  capability; no patch-and-rerun — a re-run after any graph edit is a new
  preregistration.
- **R3 — coverage floor.** ≥90% of the current release's claims resolve
  to anchored nodes with complete inbound edges; the remainder are listed
  as unprovenanced on every certificate that touches them.
- **R4 — independent recheck.** A recheck script re-derives every
  published closure from `(graph, root)` in ≤10 minutes on the declared
  host, hashes matching.
- **R5 — byte reproducibility.** Two clean builds reproduce
  `graph_sha256` byte-identically, or every certificate in the cycle is
  void.
- **R6 — historical replays reported, not scored.** Both retraction
  replays are published with their actual (small) closures and the
  sentence that they are interpretation-shaped and therefore calibrate
  the graph's *floor*, not its adequacy.

**Blind control.** 100 degree-preserving, kind-preserving edge shuffles of
the real graph, seeds committed in advance, each run against both live
drift roots. *If one or more of the 100 shuffled graphs satisfies R2 on
both roots, the real edges carry no consequence-relevant information and
this capability is void.* A perfect-looking control kills the capability,
not the control.

## 6a. Adjudication registration (2026-08-20, before the single scored run)

The gate in §6 is unchanged. This section registers, before the one run
that counts, everything a reader needs to weigh what that run says.

**The frozen instrument.** The citation scan is the six generic rules
R-a–R-f as committed in `scripts/provenance_graph.py` at `38d6eb0`,
tagged per edge. No rule names a document, a claim, or a ground-truth
entry; a source-scanning test forbids the assembler and the radius tool
from ever reading `data/retraction_closure/ground_truth_*.json`.

**Disclosure, in full.** The rule author had sight of the committed
ground truth and of two development closures while selecting and twice
refining the rules (R-f added; R-d split into path components). The
protections are the pre-committed ground truth, the ≤3× cap, the
100-shuffle control, and the generic-rule constraint — but none of them
can price the residual "a human who had seen the audit chose the rules,"
so it is disclosed here instead of controlled away. Development passes
at the frozen commit already indicate R2 will fail on both roots; the
run below is still performed and adjudicated as registered, because the
alternative — tuning until it passes — is the practice this project
exists to end.

**R1, as worded, cannot miss.** Writer-emitted edges point out of ledger
nodes (ledger `derived_from` corpus), so "edges into `report_ledger`
nodes" contains citation edges only, and every citation edge is
`inferred: false` by the §4 clarification. R1 is adjudicated as written
and, beside it, the intended quantities are reported: the writer-emitted
fraction of ledger-provenance edges over all five ledgers, and over the
regenerable four.

**R3, operationalized.** "The current release's claims" = the
`release_claim` nodes of `docs/RELEASE-v0.15.0.md`. "Resolve to anchored
nodes with complete inbound edges" is read as: the claim node exists
(anchored by heading + content hash) and carries at least one
`inferred: false` `derived_from` citation edge. The wording gap between
"inbound" and the graph's outbound-citation orientation is noted rather
than reinterpreted silently.

**R6 roots.** Retraction 1 (`0daf970`): root
`claim:experiments/ANALYSIS.md#Emergence battery 1 — solve-for-X (span
pointing, recombination splits)`, kind `standing_demoted`. Retraction 2
(`dc3ff14`): root `claim:experiments/ANALYSIS.md#qa task
(QA-as-unification, cross-language): the residual is real`, kind
`witness_invalid`. In the v1 graph claims have no inbound
`derived_from`, so both closures are expected to be the root alone —
reported at that scope, calibrating the floor, never scored.

**Protocol, one pass in this order.** (1) build the graph twice and
byte-compare (R5); (2) certify Root A
(`ledger:reports/compression.json`, `ledger_stale`) and Root B
(`ledger:reports/decompositions.json`, `ledger_stale`) into
`reports/radius/`; (3) `radius_recheck` both certificates (R4); (4)
`radius_adjudicate` both against their ground truths (R2); (5)
`radius_blind_control` over all 100 committed seeds (the control); (6)
measure R3 over the release claims; (7) certify both R6 roots. No
artifact produced by these steps is edited and re-run; whatever they
say is the adjudication.

## 7. Stop conditions and non-claims

Stop on R1's checkpoint, on any R2 miss, or on a clean control. This
design never claims the closure is *sufficient* (that repairing the named
nodes restores correctness); never treats absence from a closure as a
negative certificate — absence claims belong to the incumbent's bounded
worlds and to nothing here; never assigns confidence to an edge (an edge
exists or it does not); never auto-retracts or gates a release on its own
output; and never claims to capture **conceptual dependency** — a
normalizer convention or schema decision shared by fifty artifacts and an
input to none is explicitly outside the graph, stated as this design's
standing limitation in every certificate, because both historical
retractions were exactly that shape and pretending the graph prices them
would repeat the failure it exists to end.

## 8. What becomes askable, and how this lands

If the gate fires: *which single committed input carries the most
published weight?* Inverting closures over all published claims ranks the
program's load-bearing beliefs by exposure rather than confidence — the
first honest way to decide what to verify next, and the precondition the
parked directions named: Expiring License's revocations, First Light's
external claims, and Absent Author's stranger all become affordable once
scope is computable.

Per the governance rules, no result belongs in ANALYSIS or DISCOVERIES
until construction is attempted. When the preregistration lands, its live
status enters the then-current roadmap; fires, misses, folds, and voids
land together in the roadmap, analysis, discoveries, and backlog, with the
release blog's forward-looking section following from this document rather
than preceding it.
