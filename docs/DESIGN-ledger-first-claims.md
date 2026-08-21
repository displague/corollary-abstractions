# Claims are emitted, not written

**Status: design only, PARKED (2026-08-21, maintainer redirect).**
Nothing here is implemented. Chosen by the second full outside course
(three isolated series, fifteen directions, receipts and prompt hashes
in `reports/design-direction-v0.17.json`), grounded against the
repository, hardened by adversarial review — and then superseded as the
v0.17 headline by
[DESIGN-grounded-throughput](DESIGN-grounded-throughput.md) §2, which
records why. This document stays preregistration-ready as written; its
unpark condition is named in ROADMAP-v0.17 §3 (the first cycle after
the throughput readout, or immediately if a release again quotes a
number its artifact no longer supports).

## 1. The boundary being moved

Today a published quantitative sentence and the artifact that makes it
true are connected by nothing but the author's memory. This cycle
measured what that costs, twice: a front-page compression figure survived
five tagged releases after its ledger was rewritten (and the first hand
audit of that drift misattributed its era — the second audit caught the
first), and the retraction-closure gate voided retrospective lexical
lineage on precision — claims cite numbers and concepts, not artifacts,
so the radius of a retraction cannot be *recovered* at certifiable
precision (Root A: all 11 audited claims covered among 53 claim-sections
in the closure — 11/53 ≈ 0.208, where the certificate's `closure_size`
of 54 additionally counts the root; see ANALYSIS "voided by its own
gate").

The move: stop recovering lineage from finished prose and start emitting
prose *from* lineage. A quantitative sentence in the covered document
becomes a generated artifact of a typed citation — artifact id, digest,
field path — resolved at emission, refused at emission when the printed
value disagrees with the artifact. Blast radius is then read off the
graph, not searched for. What a person gains: the standing alarm this
repository has needed twice — *which committed claims are no longer
supported by their current artifacts* — asked continuously by machinery
instead of occasionally by a guilty audit.

The voided lexical scan is not repaired; it is **demoted to the
completeness linter**, the honest job its adjudication left it fit for.
It failed as a certifier on precision; a linter is a recall instrument,
and its false positives cost triage minutes, not trust. It flags the
sentence that cites nothing — the one failure authoring-time binding
structurally cannot catch.

## 2. Why this direction survived, and where the other fourteen went

The course's decisive fact is convergence. The void post-mortem named
"citation discipline at authoring time" before the course ran; series 1
proposed it independently at round one; series 2 and 3 each drafted a
variant, recognized the collision, and disclosed-and-replaced it. Four
independent arrivals at one direction — from one inside post-mortem and
three outside contexts that could not see each other — is the strongest
convergence either course has produced.

The other final leads, both preserved whole with their preregistration
drafts in the receipt:

- **Unless-receipts** (series 2 lead): read the 996 recorded refusal
  edges of the sealed worlds into constructive refusals — "not reachable
  within this bound *unless* one of these exactly enumerated assumption
  sets holds", completeness and minimality verified by recompilation.
  Declined for this cycle, not on merit but on sequence: it is a
  product-surface move over a two-world census, and its own final form
  says the word "capability" is only licensed by a third world sealed
  after the reader is frozen. It parks as the sealed-worlds successor,
  ready-shaped. Its constant-alphabet and nearest-k controls come with
  it.
- **Detached receipt** (series 3 lead): replay one emitted answer from
  its receipt alone, with a stranger-authored checker importing none of
  this repository's code. Declined because its own residual-risk
  statement gives the reason: the gate certifies self-containment while
  reading as though it certified correctness. One clause is imported
  instead (§5, L12 purity): the claims records this design commits must
  themselves be checkable without program imports, so the direction's
  soul rides along without its overclaim risk.

Round-one territory, all fifteen, disposed: *mutation corps* is priced
INSIDE this design's gate (L7/L8/L10 — the recheck this design leans on
faces stranger-authored mutants before any certificate counts); *the
refusal census* and *twenty questions* merged into a
construction-fact-labelled "negative space" and park behind the spent
clarification-holdout lesson; *the kill floor* died on an unregisterable
denominator and bequeathed its machine-stranger channel, used here for
mutant and deletion authorship; *second machine* reduced to an
environment-matrix checklist line on this design's artifact; *two
referees* parks with the sharpest open question of the course (a
dimension-vector-only control that could show the kind menu itself is
closed-form arithmetic) and a licensing gate on its disjoint source;
*wild text* parks as the prose-reach instrument, first by importance and
last by cost; *nothing vanishes* parks behind the working manual drift
audit with its unpark condition (the audit misses a loss the record
could have caught, or a second maintainer arrives); *half-life* folded
into detached receipt's vintage parameter and parks with it; *audit
clock* died honestly on constraint 1 (its output is testimony, not an
artifact); *antibody* parks with its reorder condition named — if the
frame/scope machinery proves cleanly queryable, it contends for the
cycle after next; *residual ledger* parks as the cheapest publishable
probe of the founding thesis, refused an aggregate number by its own
design.

## 3. The first-class object

`claims/<release>.claims.jsonl` — one record per quantitative sentence
of the covered document:

```text
claim_id, release, doc_path, sentence_index,
sentence_template            (person-authored, {value} slots),
citation { artifact_id, artifact_digest, field_path,
           writer_id, writer_digest },
resolved_value, render_rule, rendered_value,
narrowing { original_sentence, reason, class } | null,
generator_digest, emitted_at_commit
```

Companion artifacts: the regenerated covered document;
`lint/uncited.<release>.json` (the demoted scan's flags, with a
stranger-seeded recall evaluation and triage minutes);
`mutants/certificate_recheck.catalogue.json` (stranger-authored, sealed
before the recheck is touched); the radius certificate for one nominated
artifact, produced by the surviving radius machinery with its changes
declared rather than waved away: `radius_recheck.py` is reused
**unchanged** (it is the piece L7 prices, and it must not move);
`retraction_radius.py` gains an evaluation extension (the certificate
currently records no per-audit precision); the shuffle control gains a
single-root, edge-agreement mode (today it hardcodes both v0.16 roots
and scores the R2 cap). Typed-citation edges enter
`reports/provenance_graph.jsonl` as `inferred: false` edges whose
writer is the claims generator — a **registered third writer case**,
extending the retraction design's §4 clarification (which enumerates
two), to be added there as a dated amendment at preregistration time.
The clarification's anti-tautology rule extends with it: the generator
and the linter are forbidden, by the same source-scan test, from
reading the sealed audit of §7 step 3.

Trusted: the artifact digests, the writers' provenance blocks, the
recompilation-checked instruments. Untrusted and measured: the author's
citations (blind control, §6), the linter's recall (seeded deletions),
the recheck (mutation catalogue).

## 4. Smallest slice

Convert the v0.17 release notes' quantitative sentences to emitted
claims; run the linter over the whole document; nominate ONE artifact
and produce its certificate; adjudicate against a fresh hand audit of
the covered document committed before the generator runs. **The
population is defined by a sealed mechanical rule, not by feel** (§7
step 2): what counts as a quantitative sentence is a committed
function of the frozen document bytes — sentence splitting rule,
numeral test, exclusion of code fences, tables, and headings — and the
covered document's PROSE DRAFT is itself committed before the citation
pass begins, so the author cannot phrase-shift the denominator after
seeing gate pressure. The denominator is still authored — one person
writes the draft — but it is authored *before* scoring, and that
ordering is the whole discipline. (A crude digit-sentence count over
the v0.15 notes lands around thirty; the sealed rule, not that count,
defines the real number.) No retrospective conversion of past releases
— the 27-claim ground truth from the voided cycle stays the standing
bar for any future retrospective mechanism and is reported against,
never gated on, here.

## 5. Construction gate (numbers frozen here)

- **L1** ≥90% of the covered document's quantitative sentences — as
  counted by the sealed §7-step-2 rule over the frozen draft — emit from
  a typed citation; every non-verbatim conversion carries a `narrowing`
  record; one unlogged narrowing found in audit fails the clause.
- **L2** 100% of citations resolve; `rendered_value` differs from
  `resolved_value` only via a named `render_rule`; one unresolvable
  citation blocks emission of the DOCUMENT, loudly — never the release
  — and the two visible exits are fixing the citation or logging a
  narrowing.
- **L3** Linter recall 100% on 30 stranger-seeded citation deletions,
  seed batch digest sealed pre-run; 29/30 fails.
- **L4** Linter triage ≤60 maintainer-minutes for the document,
  measured from the lint report's own wall-clock fields with the triage
  log committed — usability is a gate, not a hope, and it is not
  self-attested prose.
- **L5** The certificate reproduces the fresh pre-committed hand audit
  of the covered document with zero misses. The audit uses the v0.16
  two-pass method with the roles split: the SWEEP is performed by the
  isolated channel over the frozen draft alone; the maintainer
  adjudicates. (Adapted from the outside proposal, whose original
  clause scored against the 27-claim set that mostly lives in documents
  this slice refuses to convert — an unsatisfiable scope, corrected
  here with the reason stated.)
- **L6** The typed-citation certificate must strictly beat the
  **path-token baseline** (§6, control B) on the sealed audit — fewer
  misses or, at equal misses, strictly higher precision. Ties void.
  (This replaces the outside proposal's precision-above-0.208 clause,
  which compared exact-by-construction citations against a loose scan
  and was close to unfalsifiable; 0.208 remains reported context, not
  a gate.)
- **L7** Before any certificate is committed: `radius_recheck.py` faces
  ≥15 stranger-authored mutants across ≥5 classes, catalogue sealed
  before the first commit touching the recheck; ≥95% of applicable
  mutants caught; escapes published and left standing this cycle. Below
  95%, certificates ship with `recheck.verdict: "unwarranted"` and the
  direction reports FAILED.
- **L8** If a content-free checker (digest well-formed, file non-empty,
  required keys present) catches ≥95% of that catalogue, the catalogue
  is void and L7 requires re-authoring, not re-scoring.
- **L9** Typed-citation edge agreement with the fresh audit must exceed
  the maximum agreement of the 100 committed shuffle seeds run against
  it. One shuffle matching it fails.
- **L10** The seed batch (L3) and the catalogue (L7) are authored by the
  isolated channel; the maintainer names classes only. Maintainer
  authorship of either voids that clause.
- **L11** Scope: one release document, one nominated artifact. No
  retrospective conversion.
- **L12** (imported from the detached-receipt lead) Purity: every
  `claims.jsonl` record is checkable from its own fields and the named
  digests by a checker importing no module of this repository; a record
  needing program code to verify is a defect, not a caveat. The shipped
  artifact carries a three-configuration environment-matrix line
  (locale/arch), foreign environments recorded "untested".
- **L13** If the covered document holds <25 quantitative sentences, the
  result ships labelled exploratory and carries no capability claim.

## 6. Blind controls

Two, both frozen, either able to void:

- **Control A — most-cited artifact.** Attach every quantitative
  sentence to the most-cited artifact in the library, ignoring content.
- **Control B — path token.** Attach each sentence to every artifact
  whose repo path or basename literally appears in that sentence —
  release notes print paths inline, so this is the strongest cheap
  lexical competitor, and it is precisely the strict variant the voided
  v0.16 scan never scored.

Voiding sentence, frozen: *if either control reproduces the fresh hand
audit's edge set with misses no greater and precision no lower than the
typed-citation certificate's, then typed citation adds nothing
measurable at this scale and this design is void.* The cheapest
baseline (cite nothing) is priced by L3's linter recall.

## 7. Preregistration order

1. this design, plus the dated third-writer amendment to
DESIGN-retraction-closure §4; 2. the claims schema, the linter-seed
rule, the **quantitative-sentence rule** (sentence splitting, numeral
test, exclusions — a committed function of document bytes), the
`.gitattributes` LF pins for `claims/`, `lint/`, `mutants/`, and the
`check_report_regeneration.py` registry entry for the claims file
(writer: the generator); 3. the covered document's frozen prose draft;
4. the fresh hand audit of that draft (sweep by the isolated channel,
adjudication by the maintainer); 5. the mutation catalogue, sealed;
6. the generator and the extended radius evaluation; 7. the one
registered run. A re-run after any edit to schema, rule, draft, audit,
or catalogue is a new preregistration.

## 8. Stop conditions and non-claims

Stop and publish if, in the first 10 conversions, more than 3 narrowings
carry class `not_a_function_of_artifact` — the premise that claims are
artifact-derived is then already false and the finding outranks the
feature. Stop on any L7 fold. Non-claims: nothing about
interpretation-shaped retractions (still no lineage); no completeness
for past releases; the linter certifies nothing; the resolver stays
parked; no benchmark, no product surface.

**The unpriced residual, named by its own author:** a citation that
resolves to an artifact *containing* the value rather than the artifact
the claim *rests on* survives every clause — resolvable, present, a real
edge no shuffle beats, and clean against an audit performed by the same
person holding the same belief. Pricing it requires premise-necessity
(deleting the cited artifact must break the claim), which is the parked
*load-bearing* direction from the v0.16 course; this design names that
park as its own most likely successor and does not unpark it.

## 9. Suspended habit

For the covered document, hand-writing quantitative sentences is
suspended: values print through citations or the sentence carries a
logged narrowing. Scope: the one covered document, this cycle. The habit
returns only if the gate voids.

## 10. How status lands

Preregistration enters the v0.17 roadmap as the headline architecture
item with L1–L13 quoted; fires, misses, folds, and voids land together
in roadmap, ANALYSIS, DISCOVERIES, and BACKLOG; the v0.17 release blog's
forward section follows from this document. The standing alarm (§1)
becomes the next design's candidate object only if the gate fires.
