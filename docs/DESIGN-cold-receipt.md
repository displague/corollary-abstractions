# COLD RECEIPT — does the program's evidence survive the program's deletion?

**Status: DESIGN-ONLY.** Nothing here is built, no floor here is frozen, no run
is registered by this document. `ROADMAP-v0.22.md` §2 carries the ordering
obligation it discharges — *"Its compact design lands before its slice"*
(`docs/DESIGN-handles.md` §11) — and §5 names a census that must land before the
harness exists, on the WITNESS W0 precedent. Deviations from the outside draft
are marked **DELTA** with the finding that forced them.

**Revision (2026-08-27), after adversarial review.** The first version of this
document defined a provenance tag its own model case satisfied *both* values of
(C1), wrote B8's remedy for a container §6 had already rejected (C2), miscounted
the verdict store inside the section promising indicative-walked numbers (C3),
had the harness disable the producer of one of its own census fields (C4), and
asserted what its census must return (C5). Each is repaired below with the
finding that forced it. The class of the first and last is the one this cycle
keeps meeting: **a clause written so it could not go red, and a count asserted
where a census was registered.**

## 1. The claim-kind this repairs

This programme's most load-bearing sentence is not a number. It is
`docs/DESIGN-session-ledger.md:71-72`:

> a stranger, handed the journal, can replay it offline and get the same bytes
> or a typed refusal

That sentence and its siblings have **never been tested with the producer
deleted**. Every check supporting them runs inside the repository that wrote
them, using the code that wrote them. The tool the sentence points at,
`scripts/replay_session.py`, puts `scripts/` on `sys.path` from its own
`__file__` (`:69-71`) and imports `harness.CoreSession` and `harness.route_line`
(`:73-74`) — it *is* the program, and it finds the program by a route no `PATH`
controls. Handed only the journal, a stranger can do what
`experiments/session_corpus_seal.json` already says (*"every journal against the
digests below: yes, offline, with no key"*), and that is a check of **bytes**,
not of any claim the journal makes.

COLD RECEIPT does not improve the receipts. It **measures which of them survive
the program's absence**, kind by kind, and publishes the partition. The course's
tiebreak, quoted from `reports/design-direction-v0.22.json`
`outcomes.series_2.tiebreak_quoted`:

> prefer the direction whose null result still changes what the program says
> about itself -- the census cannot return a null

The census returns a partition whatever it finds: all-NEEDS-PROGRAM says this
tree's offline-checkability language is decoration and must be rewritten; a large
SURVIVES class says which sentences are earned and licenses none of the others; a
mixed reading names the boundary. **Every value changes what the programme says
about itself** — §13 turns that argument into a result gate rather than leaving
it as a motive.

## 2. Why this direction survived the course

Series 2 of the v0.22 course ran five round-one directions
(`round_one_funnel.series_2`): **ERRATUM**, **REBUTTAL**, **EXIT SIGN**, **COLD
RECEIPT**, **LONG CON**. The selection evidence, only as far as the receipt
carries it:

- **COLD RECEIPT led; ERRATUM was runner-up**, and the tiebreak quoted in §1 is
  the reason recorded. **ERRATUM did not park** — it was **demoted to a rider**,
  `experiments/erratum_probe.json`, with a floor of **1 designated planted flip**
  and a stop rule that decides its v0.23 candidacy by the real-flip count rather
  than by re-running it (`ROADMAP-v0.22.md` §3, `DESIGN-handles` §7's B9). A
  runner-up that becomes a rider is a disposition, not a shelf.
- **REBUTTAL and EXIT SIGN folded into CROSSING** — *"execution-licensed boundary
  crossings both ways; 20-real-corrections probe with a preregistered predicted
  split 2/6/12"* — which parks **with the probe named**
  (`selection.parked_with_reasons.CROSSING`).
- **LONG CON was retired to a day-probe** — *"ten hand-written sequences; frozen
  budget; mandatory plant; committed near-miss taxonomy even on a null;
  write-gate prohibition inherited."*
- The selection records the adoption in its own words
  (`selection.adopted_second`): *"COLD RECEIPT -> ROADMAP-v0.22 item 2 with the
  provenance clause added; compact design lands before its slice (the WITNESS
  precedent)."*

## 3. The frozen draft, quoted before it is elaborated

`reports/design-direction-v0.22.json`
`outcomes.series_2.preregistration_draft`, recorded **before ROADMAP-v0.22 was
written** — and checkable as written, since
`outcomes.series_1.preregistration_draft.note_on_selection` discloses that series
2's and 3's drafts were recorded at first writing and only the *selected* HANDLES
draft was added in the post-review patch of 2026-08-26. The **bold labels and
line breaks are this document's**; the receipt stores each field as one unwrapped
line and the strings are unaltered.

> **artifact:** cold/ bundle: census.json one record per receipt kind
> (emitting_routes, bundle_manifest, external_deps{name,pin_hash,role},
> recheck_procedure{raw_checker_invocation|program_replay|none}, verdict
> SURVIVES|NEEDS-PROGRAM|UNTESTED, verdict_evidence, blocking_dependency
> confirmed_by_removal, tamper_result 3 mutations, omission_result FAIL_LOUD,
> sham_result, pin_audit_ref, census_seal) + harness/ container recipe +
> path_audit + scramble_baseline + one worked stranger-path transcript
>
> **gate:** B1 unmapped emitting routes = 0; B2 >=1 kind SURVIVES (the
> raw-checker-invocation exception exists); B3 tamper 3x per kind 100% FAIL; B4
> omission FAIL LOUD naming the missing dependency, silent pass voids the
> harness; B5 sham-checker SURVIVES count = 0; B6 chance measured: 200 scrambled
> bundles; if 0 of 200 pass, publish the 1.5% rule-of-three upper bound as the
> chance rate; B7 100% NEEDS-PROGRAM carry confirmed_by_removal (a correct
> NEEDS-PROGRAM scores as a hit); B8 >=90% SURVIVES on first run voids pending
> audited-empty-PATH re-execution; B9 version-drift ceded to the pin audit,
> reference only; B10 census_seal fixed before the harness runs, later finds
> publish as census misses
>
> **voiding_sentence:** If any receipt kind is annotated SURVIVES while the
> pinned checker is replaced by the accept-all stub, the harness is measuring
> bundle presence rather than verification, and the claim is void for every kind
> in this census
>
> **added_clause_by_selection:** external_deps[].provenance in
> {third_party_pinned, program_configured}; any SURVIVES resting on a
> program_configured dependency downgrades to UNTESTED (the draft's own residual
> risk, priced before registration)
>
> **residual_risk:** the harness deletes the program's code while keeping the
> program's prepared world -- program absence is priced, environment provenance
> was not; the added clause is the repair

**The added clause is B11**, and where it lives matters: the receipt stores it in
`added_clause_by_selection`, *outside* the `gate` string, so a reader checking
B1–B10 against the draft finds ten clauses and not eleven. It is numbered B11
here and adjudicated exactly like the other ten.

**B6's tense.** `ROADMAP-v0.22.md` §2 and `DESIGN-handles` §11 record a *"tense
repair"* on B6 (review H8). Read against the receipt, **the draft's own string
already carries the conditional** — *"if 0 of 200 pass, publish…"* — so nothing
in the quote above needed changing, and this document does not claim to have
changed it. What the repair guards is the *reading*: an earlier paraphrase
dropped the *if* and turned a gate into a recorded outcome. The clause is a
prediction that can fail, and §7 budgets it as one.

## 4. `census.json` — one record per kind, every field's producer named

Field names are the draft's; the **producer** column is this document's, and is
the point: a census field with no named producer is one the harness invents at
run time.

| field | producer |
| --- | --- |
| `kind_id`, `emitting_routes[]` (`{route_id, writer_file, writer_symbol}`) | CR-P0's registry (§5); never minted by the harness |
| `bundle_manifest[]` | the harness, copying the files the kind's receipt names, plus their sha256 |
| `external_deps[]` | `{name, pin_hash, role, provenance, selection_provenance}`; `pin_hash` and `selection_provenance` from CR-P0 (§8), `provenance` assigned by the harness from the bytes (§8) |
| `recheck_procedure` | CR-P0 for the *declared* value, the harness for the *executed* one; a disagreement is a census miss under B10 |
| `verdict`, `verdict_evidence` | the harness, from the executed procedure alone — never from the declaration; evidence is the exact argv, exit code, stdout head |
| `blocking_dependency` + `confirmed_by_removal` | the harness's removal arm (B7) |
| `tamper_result` / `omission_result` / `sham_result` | the harness's three arms (§7) |
| `pin_table_ref` | **DELTA (H1)**, splitting the draft's `pin_audit_ref`: a pointer into `session_ledger.PIN_FIELDS`, reference only, never a verdict input |
| `pin_divergence[]` | **DELTA (H1)**: divergences the census observes and B9 declines to adjudicate, each `{pin_a, pin_b, values, adjudicated: false}` — §11's `proofcurve` case lands here |
| `census_seal` | CR-P0, sealed before the harness exists (B10) |

**The verdict vocabulary, stated hard.** `SURVIVES`: the procedure ran to a
correct verdict **with the program's script tree absent**, on the bundle and
`external_deps` alone. `NEEDS-PROGRAM`: the procedure requires this repository's
code, **confirmed by removal** rather than declared (B7) — a correct
NEEDS-PROGRAM scores as a hit, so the honest reading is not penalised.
`UNTESTED` is the downgrade sink: B11 lands here, and so does any kind whose
procedure the harness could not execute at all.

**Why `pin_audit_ref` splits, and what B9's cession actually is (H1).** B9 cedes
version drift *"to the pin audit"*. **RATCHET's pin audit is parked**
(`ROADMAP-v0.22.md:441`, *"RATCHET (+ its pin audit)"*), so the cession is a
**deferral to a lane that is not running**, not a hand-off to an instrument that
will adjudicate it. `pin_table_ref` points at what exists; `pin_divergence[]`
records what the census sees and nobody adjudicates. Writing that down is the
difference between ceding a question and losing it.

## 5. B1's meetability — the registry, registered rather than asserted

**B1 says unmapped emitting routes = 0, which is meetable only if a
machine-enumerable route registry exists.** The v0.21 lesson binds hardest here
(`DESIGN-handles`'s Status paragraph: the first version failed review for
*claiming ground the repository already occupies and citing producers that do
not exist*): **where coverage or counts are unknown, register the census; do not
assert the answer.** What follows separates what is machine-enumerable *today*
from what is not. Every number is **indicative** — a walk this document ran, not
a census it publishes.

**Machine-enumerable today, three partial registries:**

- **`serve_chat.py:259` `LINE_GRAMMAR`** — 15 entries of
  `{form, route, example, statuses, requires}`, already digest-pinned
  (`session_ledger.py:697`) and served over `GET /v1/capabilities`: the strongest
  evidence in the tree that a registry of this shape can be enumerated and
  frozen. **But it enumerates serving routes, not receipt kinds.** The route→kind
  map lives in `serve_chat.kernel_receipt` (`:1105-1149`), keyed on
  *(route, answered?)* and dispatching to distinct shapes — code, not a table.
- **`check_report_regeneration.py` `REGISTRY`** — report path → writer + argv,
  with a `DECLARED_SNAPSHOTS` companion; the repository's own precedent for
  *"which script produces which ledger, promoted from a comment to something
  executable."* Indicative coverage: **4 of the 13 `*.json` files at depth 1 of
  `reports/`, and 0 of the 111 `*.json` files at depth 1 of `experiments/`**
  (M4: depth 1 only — `experiments/sessions/` holds 136 more that this count
  deliberately excludes, because they are one kind's instances, not kinds).
- **`session_ledger.py:761` `PIN_FIELDS`** — the five pins B9 defers drift to.

**Not machine-enumerable today, and this is the finding:** no table anywhere maps
a receipt kind to its emitting routes and its recheck procedure. An indicative
walk reached **fifteen candidate kinds**, tabled so review can attack the count
rather than a summary. The count is *indicative* — not a floor, not a prediction,
and explicitly **not** what CR-P0 must return. *(If this document is ever trimmed,
this table moves into CR-P0's artifact rather than being summarised away: it is
the evidence for the paragraph above it.)*

| # | candidate kind | writer |
| --- | --- | --- |
| 1 | `x_corollary` per-route receipt (several shapes: `_resolution_receipt` `:1016` with `node_sha256`, `_ownership_receipt` `:1041`, `_evaluate_receipt` `:1064`, `_story_receipt` `:1097`, the `derivation`/`grounding` literals, `missing_capability`) | `serve_chat.py:1105` |
| 2 | `closure-receipt/1` certificate | `closure_query.py:64,278` |
| 3 | `conform` verdict receipt, built inline | `harness.py:2289` |
| 4 | `ownership` route receipt | `harness.py:1171` |
| 5 | `twin` route receipt | `harness.py:1917` |
| 6 | `write_stage` **staging** receipt — written at `:1652` via the atomic writer `_write_receipt_atomic` `:1538`, rendered from `StagingRecord` `:316` | `write_stage.py:1652` |
| 7 | `write_stage` **applied** receipt — `AcceptanceRecord` `:1905`, written at `:2152` (receipt-or-nothing, F3) | `write_stage.py:2152` |
| 8 | journal `Turn.receipt_digest` chain | `session_ledger.py:649`, written `session_recorder.py:199` |
| 9 | session **read log** (a deliberately separate writer) | `session_ledger.py:812` |
| 10 | external-verifier `Verdict` store — **15 committed: 3 `lean4`, 12 `python-tests`** (C3: the first version read 14 / 3 / 11 and was wrong against the tree) | `external_verifier.py:109` → `prover/verifier-verdicts/` |
| 11 | C-E3 probe `checker_receipt` | `conformance_ce3_supplement.py:395,605` |
| 12 | `radius-certificate` | `retraction_radius.py` → `reports/radius/*.cert.json` |
| 13 | provenance-graph edges | `report_provenance.py` / `provenance_graph.py` → `reports/provenance_graph.jsonl` |
| 14 | `plain_router` conditional-answer receipt | `plain_router.py:260` |
| 15 | registered-run artifacts, one level up | `experiments/session_ledger_run.json`, `experiments/conformance_run.json` |

**Two corrections the walk forced.** (1) There is **no `recheck_cmds` construct in
this repository**, under that or any adjacent name; the nearest real thing is
`scripts/radius_recheck.py`, which re-checks radius certificates and
**deliberately never imports their producer** — this design's closest existing
relative, and still program code. Its dependencies are pre-priceable today and
are recorded here so CR-P0 inherits them rather than discovering them: it reads
`schema/radius-certificate.schema.json` and `schema/provenance-graph.schema.json`
(`:13-14,63`) — **committed repository files, therefore bundle contents and not
`external_deps`** — and it imports third-party **`jsonschema`** (`:58`), which
**no manifest in this repository pins**: the only `pyproject.toml` is
`experiments/pyproject.toml` (torch, numpy, floor constraints, unrelated). Under
§8's test `jsonschema` is `program_configured`, and kind 12's SURVIVES therefore
downgrades unless the census pins its bytes. (2) `dump_server.py:169-178` emits a
**deliberately empty receipt beside a `"found"` status** as a committed voiding
control for the throughput metric; it is not a receipt kind, and a census that
counted it would be counting a sham the repository built on purpose.

> **CR-P0 — the route/kind registry census, a construction prerequisite.**
> Committed **before** any harness code exists (the WITNESS W0 pattern). It
> fixes: the executable enumeration rule; one `kind_id` per kind with its
> `emitting_routes[]` as `{route_id, writer_file, writer_symbol}`; the declared
> `recheck_procedure`; each dependency's `pin_hash` and `selection_provenance`;
> and the `census_seal` B10 freezes. It publishes **whichever way it reads**, and
> its count is **deliberately not predicted here**, because the census exists to
> measure the quantity a prediction would have to assume (R1's argument shape,
> `ROADMAP-v0.22.md` §3).
>
> **`excluded[]` — the register of what the rule deliberately skips (H2).** Every
> exclusion is a record `{path, line_range, reason}`, and the enumeration rule
> must reproduce the exclusion rather than depend on a maintainer having known
> about it. Seeded with `{scripts/dump_server.py, 169-178, "committed voiding
> control: an intentionally empty receipt beside a found status"}`. An exclusion
> that the rule cannot reproduce is a **census miss under B10**, not a judgement
> call — which is what stops `excluded[]` from becoming the place inconvenient
> kinds go.
>
> **The draft's own B1 stop, kept in force:** if the enumeration cannot be made
> machine-executable — if identifying a kind's emitting routes requires reading
> code rather than running a rule — then **B1 is not meetable, the harness does
> not open, and CR-P0 publishes as the result**: *the program cannot enumerate
> its own evidence, which is a stronger finding than any verdict the harness
> could have returned.* A hand-written kind list presented as a registry is the
> construction defect **ROADMAP-v0.21 §4.0(3)** exists to catch.

## 6. The harness — what containerization this workstation actually has

The draft says *"harness/ container recipe"*. **DELTA, forced by the machine —
and the reasoning is narrower than the first version's (M1).** This workstation
has `docker` **29.6.2** on PATH with a WSL2 backend (`Ubuntu-24.04`,
`docker-desktop`), both distros **Stopped**; `docker info` fails on
`npipe:////./pipe/dockerDesktopLinuxEngine`. Podman is absent. So a container is
*startable*, and the argument against it is **one limb, not three**:

**The receipts pin a digest of a Windows binary.** The C-E3 supplement records
`binary_sha256 567d145f…5ac7` over `lean.exe`, and the 3 committed `lean4`
verdicts record `"platform": "win32"` in their `environment` block. A Linux
container runs a *different binary* with a *different digest*, so a re-check
inside one cannot confirm the recorded pin — it can at best confirm some other
build of the same release. **A container would not be a colder re-check of these
receipts; it would be a re-check of different ones.**

*Two limbs the first version leaned on are withdrawn as wrong.* The resolver at
`external_verifier.py:196-217` is **not** Windows-bound — it selects
`"lean.exe" if os.name == "nt" else "lean"` and works on Linux. And the *"NEVER
downloads"* rule in that docstring binds **that function**, not a Dockerfile;
a container image that shipped a toolchain would not violate it. The digest limb
is the one that survives, and it is enough.

**So the harness is a clean-PATH subprocess environment, and this document says
out loud that it is weaker than a container.** Its shape: the bundle is copied
**outside the repository**; the program's script tree is **renamed away**
(`scripts/` → a sibling name the subprocess cannot resolve) so an import is an
error and not a silent fallback — rename rather than deletion, because it is
reversible and the audit can prove it happened; the subprocess runs with a
**constructed environment** (`PATH` reduced to the explicitly listed dependency
directories, `PYTHONPATH` empty, `PYTHONHOME` unset, cwd inside the bundle); and
**`path_audit.txt`** is the proof rather than the promise.

**What `path_audit.txt` must prove, and why `PATH` alone is not it (C2).** §1's
own exhibit is the counter-example: `replay_session.py:69-71` reaches `scripts/`
through `Path(__file__).resolve().parents[1]` and `sys.path.insert`. **No `PATH`
setting anywhere would have stopped it.** The audit therefore asserts two things,
not one:

1. **`scripts/` is unresolvable** — the rename happened, and an import of a known
   program module raises, with the traceback quoted.
2. **No `sys.path` entry resolves inside the repository** — the subprocess dumps
   its own resolved `sys.path` and every entry is shown to lie outside the
   repository root, alongside `PATH`'s entries with their listing digests, and
   every invoked dependency's resolved path and sha256.

**DELTA on B8, recorded with the finding.** The draft's remedy for a ≥90%
first-run reading is *"audited-empty-PATH re-execution"*. That remedy was written
for the container this section rejects; against a rename harness an empty `PATH`
proves nothing about the leak vector that actually exists. **B8's remedy is
replaced by re-execution under a `path_audit` carrying BOTH assertions above**,
and the substitution is recorded here rather than performed silently, because the
draft's wording is the thing a reader will check against.

**What this harness does NOT exclude, named so no reader has to find it:** the
Windows registry, `%USERPROFILE%` (and therefore `~/.elan`, where the checker
lives — §11), `.runtime/`, any system-wide Python and its `site-packages`, every
ambient DLL search path, and — **added by review (H3)** — **the harness's own
interpreter**. The 12 `python-tests` verdicts record
`{"python": "3.13.12", "mypy": "2.3.0", "platform": "win32"}`, and this
repository's `.venv/Scripts/python.exe` **is** Python 3.13.12 with mypy 2.3.0:
the recorded environment is this repo's virtualenv. It is pre-tagged
**`program_configured`** under §8, with the consequence stated where it bites:
**every python-based recheck's SURVIVES downgrades to UNTESTED** unless the
census pins the interpreter's and mypy's bytes. A container would exclude most of
this list. **This one does not, and every `SURVIVES` in this census is scoped to
that weaker exclusion.** The scope travels with the number; it is not a footnote.

**Ordering, because the rename breaks two of this design's own producers (C4).**
`session_ledger.pins()` — §4's producer for `pin_hash` — lives under `scripts/`
and imports `serve_chat` and `write_stage`; after the rename it cannot run. And
`write_stage`'s `working_tree_byte_identity` check takes a recursive digest of
the tree the rename mutates. Therefore: **the pin table is captured BEFORE the
rename, into the bundle, and its capture is part of CR-P0's artifact rather than
the harness's run.** The working-tree digest disturbance is named here as a
**known, reversible side effect** with its restore path — the rename is undone
and the tree is re-digested against the pre-rename value, and a mismatch is a
harness failure reported as such, never absorbed. A harness that silently altered
the tree it measures would be the defect this whole item exists to find.

## 7. The four arms, and which control each one is

**Tamper (B3), 3 mutations per kind, 100% must FAIL.** The three are *different in
kind*, not one shape run repeatedly — v0.21's B8 arms *"were one tamper shape run
twice"* (`ROADMAP-v0.22.md:556`, quoted rather than paraphrased, because the first
version of this document misquoted it as three). (1) **Content**: flip one byte of
a bundled artifact the receipt covers. (2) **Digest**: change the recorded digest
to match a tampered artifact, so a checker comparing only a file to its own
recorded hash passes. (3) **Binding**: swap two records between receipts, leaving
every file and digest internally consistent and the *attribution* wrong — the one
a presence-check cannot catch.

**Omission (B4), FAIL LOUD naming the missing dependency.** Remove a listed
`external_deps` entry and run; the procedure must fail **and name what is
missing**. **A silent pass voids the harness** — not the kind — because a
procedure that passes without its dependency was never using it. v0.21's B4
self-comparison trap in different clothes (`ROADMAP-v0.22.md` §2). **UNTESTED
escape (M5):** a kind with no removable dependency — a procedure that is pure
byte comparison against a bundled digest — has **no omission arm to run**, and
reads `UNTESTED` for `omission_result` with the reason recorded. It does not read
FAIL_LOUD by default and it does not read a silent pass; both would be verdicts
the arm never produced.

**Sham checker (B5), SURVIVES count = 0.** Every adjudicating dependency is
replaced by an accept-all stub of the same name and interface: for Lean kinds, a
program that prints nothing and exits 0; for digest-only kinds, a `sha256`
returning the expected value. Detection comes from running each kind against
**both a good and a known-bad bundle** — the stub passes the bad one. Any kind
still reading SURVIVES fires the voiding sentence for every kind in the census.

**Scrambled-bundle chance (B6), 200 bundles.** The chance a bundle passes its own
recheck procedure *without being the right bundle*, scrambled by the seeded
per-kind rule CR-P0 commits: reassign one kind's artifacts across that kind's own
records, preserving every file and every digest field's *shape*. **If 0 of 200
pass, publish 3/200 = 1.5% as a rule-of-three upper bound** — an upper bound on a
chance rate, never a measured rate, and never quoted as though 0 were the finding.

**Budgeted from measured cost, with a publish-the-overrun rule (H5), on
`DESIGN-session-ledger` §7's B2 precedent.** The C-E3 supplement's 50 committed
probes read **mean 0.351 s, median 0.349, max 0.380**. One scrambled bundle of
that kind is 25 rows × 2 probes = 50 invocations, so **200 bundles ≈ 10,000
invocations ≈ 59 minutes at the mean and ≈ 63 at the observed max — for that one
kind alone.** B6 is therefore an hour-scale arm per checker-invoking kind, not a
cheap one, and **if a B6 run exceeds 90 minutes for a single kind the overrun is
published as a finding before any chance rate is read.** A cost this design
predicted and then quietly exceeded would be a budget that could not go red.

**Which control is which, said once so no arm is mistaken for another.** B5's
known-bad bundle is the **negative control** — the instrument must be able to say
no. B6's scramble is the **vacuity control** — it prices what a bundle earns by
being *the right one* rather than by being *a bundle*. B3 is the tamper battery
and B4 the omission trap; neither is a control on the census's capability claim,
they are controls on the harness. And the **voiding sentence is the
capability-blind control**: the sham checker can void every kind at once, and it
is written to be able to.

## 8. Provenance, selection provenance, and the downgrade rule (B11)

**DELTA, forced by review (C1).** The draft's single `provenance` tag was **not
decidable**, and `lean.exe` satisfied both values of it: its bytes are a third
party's pinned release, and its presence at that path was arranged by this
machine. Under a mechanical downgrade that ambiguity would have taken B2's only
worked SURVIVES candidate to `UNTESTED` and fired §14's stop before the harness
opened — a clause that voids the run by being unreadable. The tag is therefore
split into two fields with separate tests and separate assigners.

**`provenance` — a test on the BYTES, assigned by the HARNESS.**
`third_party_pinned` **iff both** hold: (a) the census pins the dependency by a
digest **of the artifact that executes** — the binary's own bytes, not a file
that names a version — and (b) the pin identifies a third party's published
release. Otherwise `program_configured`. The harness runs the test from
`external_deps[].pin_hash` and the resolved path recorded in `path_audit.txt`,
and reads no declaration while doing it.

**`selection_provenance` — a test on the CHOICE, assigned by CR-P0.** Which
release was chosen and by what: `repository_file` (a committed pin file selects
it), `machine_state` (whatever the machine happened to have), `harness_constant`.
**B11 does not downgrade on this field.** It is recorded because the choice is a
real fact about the world the receipt was made in, and folding it into the bytes
test is exactly what made the single tag undecidable.

**The rule, unchanged in force and now decidable: any `SURVIVES` resting on a
dependency tagged `program_configured` downgrades to `UNTESTED`.** Not to
NEEDS-PROGRAM — the procedure may well be cold-checkable; what is unknown is
whether the world it ran in was prepared for it. The harness applies the
downgrade mechanically, so it cannot be argued away per kind.

**Three dependencies adjudicated here, in the text, so the test is visibly
two-sided:**

- **`lean.exe` v4.32.2 — `third_party_pinned`, and it does NOT downgrade.** The
  C-E3 supplement records `binary_sha256` over the executing binary and
  `leanprover/lean4:v4.32.2` is leanprover's published release, so (a) and (b)
  both hold. `selection_provenance = repository_file`
  (`prover/lean/normalizer/lean-toolchain` selects it out of four installed
  toolchains) — recorded, not downgraded. **B2's floor of one survives contact
  with B11**, which under the single tag it did not.
- **`.venv` Python 3.13.12 and mypy 2.3.0 — `program_configured`.** No digest of
  the interpreter or of mypy is pinned anywhere; `selection_provenance =
  machine_state`. Every python-based recheck downgrades until the census pins
  those bytes (§6).
- **`jsonschema` — `program_configured`, and worse: unpinned entirely.** No
  manifest in this repository names it (§5). `selection_provenance =
  machine_state`.

## 9. Trusted and untrusted

**Trusted:** CR-P0's committed registry and `census_seal`, digest-frozen before
the harness exists (E7's shape); the committed receipt artifacts themselves,
which the census reads and never rewrites; the pin table captured before the
rename (§6); and the third-party checker binaries **only to the extent their own
bytes are pinned** — which §8 makes a test rather than a habit.

**Untrusted:** the harness (which is why B3, B4, B5 and B8 exist, and why B4's
silent pass voids *the harness* rather than a kind); every **declared**
`recheck_procedure`, since B7 requires removal to confirm a NEEDS-PROGRAM and the
harness's executed procedure overrides the declaration on disagreement; the
**absence** of a failure, since a procedure that neither passes nor fails is
`UNTESTED` and never `SURVIVES`; and this workstation's ambient world, whose
unexcluded parts are listed in §6 rather than assumed away.

**No learned component anywhere** — not in enumeration, scrambling, tagging or
adjudication. There is no seat for one, and the absence is declared rather than
left to be noticed.

## 10. Meetability, floor by floor (ROADMAP-v0.21 §4.0(3))

> *Every frozen floor now ships with a meetability argument — a pilot, a
> construction argument, or a bounded-class analysis showing a correct instrument
> can reach it. A floor without one is a construction defect discovered at
> registration time, not a gate waiting to void.*

The rule admits exactly three forms. Each row below names which form it uses.

| floor | form | meetability argument |
| --- | --- | --- |
| **B1** | *pilot* | §5's CR-P0 **is** the pilot and carries the stop clause — the one floor whose meetability is a prerequisite rather than an argument. |
| **B2** | *construction, on one worked instance* | `conformance_ce3_supplement.json` carries per row the `substituted_proposition` verbatim, the template `example : (<prop> : Prop) := by decide`, each probe's `source_sha256`, the toolchain string and the binary digest — enough to rebuild the probe text, confirm its hash, run it and compare the exit code **with none of this program's code**. Review executed that path cold and it held (§12, CR-P1). **B2 stays a floor of one because one is the weakest defensible floor, not because only one such kind exists** (C5): kind 10, the `Verdict` store, is a second candidate on its face — a `python-tests` verdict records two pinned files with their sha256, an environment block, and prose `checks` — but **its invocation argv is not recorded**, so whether it is raw-recheckable is a question for CR-P0, not a claim here. |
| **B3** | *construction* | on the C-V4′ shape: each mutation provably changes an input the procedure reads, and a mutation without a witness of difference is discarded and counted before any rate. A kind whose procedure cannot be shown to read the mutated input yields no tamper arm and is `UNTESTED`, never a silent pass. |
| **B4** | *bounded-class analysis* | over the two classes a kind can fall in: a procedure that **invokes** a dependency fails on its removal by construction; a procedure that invokes **none** has no arm and reads `UNTESTED` (§7's escape). The classes are exhaustive, so the floor is reachable for every kind in either. The clause's real work is the **naming** requirement, a property of the harness's error handling. |
| **B5** | *construction* | an accept-all stub cannot produce a *correct* verdict on the known-bad bundle each kind is also run against. |
| **B6** | *bounded* | a deterministic seeded measurement, budgeted in §7 at ≈1 hour per checker-invoking kind with an overrun published as a finding. |
| **B7** | *construction, and the clause that makes the census non-punitive* | a correct NEEDS-PROGRAM scores as a hit, so the instrument has no incentive to over-read SURVIVES. |
| **B8** | *the too-good clause* | **WITNESS's B3** (`DESIGN-witnessed-conformance.md` §5's 49/50 — not this document's B3, which is tamper) in this cycle's clothes: a first run at ≥90% SURVIVES is likelier a harness that failed to remove the program than a repository of cold receipts. **Denominator and interaction, added by review (M6):** the clause applies only when the census holds **≥5 kinds**; below that a single SURVIVES in a one- or two-kind census would trip a percentage that means nothing, and B2's floor of one must never be what fires B8. The remedy is §6's two-assertion re-execution, not the draft's empty `PATH` (C2). |
| **B9** | *trivially* | reference only, and §4 records that the cession is a **deferral** to a parked lane. §11 says what that costs. |
| **B10** | *ordering* | CR-P0 commits first; later finds publish as **census misses**, counted, never folded back into the seal. |
| **B11** | *construction* | two tags with decidable tests and named assigners (§8), and a mechanical downgrade. |

## 11. The residual risk, quoted, and what remains unpriced

> the harness deletes the program's code while keeping the program's prepared
> world -- program absence is priced, environment provenance was not; the added
> clause is the repair

B11 prices it as far as two tags can. **What remains unpriced, named rather than
left to be found:**

**The checker binary is installed by this machine's elan.** `lean.exe` is a third
party's release whose bytes the C-E3 receipts pin, and it sits at
`~/.elan/toolchains/leanprover--lean4---v4.32.2/bin/lean.exe` because this
machine's `elan` put it there — four toolchains side by side (`v4.20.0`,
`v4.29.1`, `v4.32.2`, `v4.33.0`). §8 tags that `selection_provenance =
repository_file` and declines to downgrade on it, which is a **decision, not a
proof**: it says the choice is traceable to a committed file, not that the
installation was independent of this program's maintenance.

What the digest **does** prove: the bytes that ran are identified, so a reader
obtaining `lean` v4.32.2 from leanprover and finding the same digest is checking
the same program. What it does **not** prove: that the reader can obtain it
without a network (the hermetic rule binds the *program's* resolver, not the
reader); that the harness's environment is free of `elan`'s other arrangements —
`Path.home()` reads `USERPROFILE`/`HOME` from the environment, which §6's
constructed environment does **not** clear, and a reduced `PATH` is irrelevant to
it (L3); or that the pin covers the binary generally —
**`session_ledger.checker_toolchain_digest` (`:722`) is the sha256 of the
`lean-toolchain` *file*, a hash of the text that names a version, not of the
binary.** The C-E3 supplement's per-row `binary_sha256` is the only place the walk
found the binary's own bytes pinned.

**And the tree already holds an instance of the drift B9 defers.** Three
`lean-toolchain` files pin `v4.32.2` (`normalizer`, `ingested`, `session`); a
fourth, `prover/lean/proofcurve/lean-toolchain`, pins **`v4.29.1`**. Whether that
is deliberate or drift is **not determinable from the files**, and this design
does not decide it — it lands in `pin_divergence[]` (§4) with
`adjudicated: false`, so a divergence B9 defers to a parked lane is at least
visible where a reader meets the verdicts.

**A second unpriced item.** A receipt whose digest is taken over a
**program-defined canonicalization** is not offline-recheckable even in principle
without the program: `serve_chat`'s resolution receipt carries `node_sha256` =
`sha256(canonical_bytes(node))`, and `canonical_bytes` is this repository's
function. Such kinds are expected to read NEEDS-PROGRAM, and the census must
record the *reason* — `canonicalization_is_program_defined` — so the partition
distinguishes a kind that needs the program to **adjudicate** from one that needs
it only to **serialize**.

## 12. Construction prerequisites and deliverables

- **CR-P0 — the route/kind registry census (§5), committed BEFORE the harness**,
  with its stop clause, its `excluded[]` register, and the pin table captured
  before any rename (§6). Nothing else in this design exists until it lands.
- **CR-P1 — the reconstruction rule, FOUND AND PUBLISHED, before the general
  harness (M2).** The draft lists *"one worked stranger-path transcript"* among
  the artifacts; ordering it *first* is this document's DELTA, on the WITNESS W1
  precedent. Its job is not to assert that the C-E3 rows are re-checkable but to
  **derive and publish the exact rule** by which a bundle reconstructs a probe
  from the artifact: proposition → source text → `source_sha256` → invocation.
  **Meetability evidence: adversarial review executed that path cold and reached
  the recorded digest**, so the floor is met by demonstration rather than by
  argument. **And it published a finding that strengthens B2 rather than
  softening it:** the artifact records only the *positive* template
  (`"pattern": "example : (<prop> : Prop) := by decide"`); the **negative**
  probe's template — `example : (¬(<prop>) : Prop) := by decide` — and the
  trailing newline are **not recorded anywhere in the artifact** (the negation
  glyph appears zero times in it). A reconstructor must therefore infer half the
  rule, which is precisely the kind of gap CR-P1 exists to find *before* a
  verdict rests on it. **If the rule cannot be published as a rule, B2's floor of
  one is not meetable and the slice publishes that instead of opening.**
- **Deliverables, bound to the draft's artifact list (L7).** `census.json` sealed
  by CR-P0; `harness/` with `path_audit.txt` carrying §6's two assertions;
  **`scramble_baseline`, the artifact of B6 — the seeded scramble rule, the 200
  outcomes per kind, the elapsed time, and the rule-of-three bound if it applies
  — published whichever way B6 reads**; and CR-P1's reconstruction rule with its
  worked transcript. **The transcript keeps the draft's name, `stranger-path`,
  and the name is the draft's rather than this document's claim** (L6): what it
  contains is a *program-absent* re-check on this workstation, and §14's first
  non-claim governs how it may be described.

## 13. Result gate — the sentence each partition licenses

The gate above is construction. What the census would license is fixed here,
**before it runs**, on `DESIGN-session-ledger` §9's R1 shape — the capability
claimed and the number that licenses it, with *nothing more* attached.

**R-C** — B1 through B11 green, the voiding sentence not fired, and CR-P0 and
CR-P1 committed in order. Then the served sentence is: *for the receipt kinds
`census.json` names SURVIVES, the recorded verdict can be re-derived on this
workstation with the program's script tree renamed away and no `sys.path` entry
inside the repository, using only the bundle and dependencies tagged
`third_party_pinned`.* Nothing more — no rate, no other machine, no person.

**Every other partition is also a result, and each licenses exactly one
sentence.** This is §1's argument written as a gate rather than left as a motive:

| partition | the sentence it licenses |
| --- | --- |
| B1 unmeetable (CR-P0's stop) | *This program cannot enumerate its own evidence.* The harness does not open, and the census is the headline. |
| 0 kinds SURVIVE (B2 red) | *No receipt kind this program emits can be re-checked without the program.* Every offline-checkability sentence in the tree is withdrawn to a bytes-integrity sentence, and §14's suspended habit becomes permanent. |
| ≥1 SURVIVES, some NEEDS-PROGRAM | R-C's sentence, scoped to the named kinds, **with the NEEDS-PROGRAM kinds published by name** — B7 scores a correct NEEDS-PROGRAM as a hit, so this partition is a reading and not a shortfall. |
| all UNTESTED via B11 | *The program's evidence was re-checked in a world the program prepared, and nothing follows about its independence.* The census publishes the tags and claims no capability. |
| voiding sentence fires | **Instrument failure, not a capability.** No partition is published, and the sham-checker result is the artifact. |

**R-C failing on any clause serves nothing and publishes the readout.**

## 14. Stop conditions, non-claims, suspended habit, where status lands

**Stop and publish** if CR-P0's enumeration cannot be made machine-executable
(§5's stop); if CR-P1's reconstruction rule cannot be published as a rule (B2
unmeetable); if B4's omission arm passes silently (the harness is void, not the
kind); if the sham checker leaves any kind reading SURVIVES (the voiding
sentence, void for every kind in the census); or if the harness cannot be
constructed with a `path_audit` carrying **both** of §6's assertions.

**Non-claims:**

- **No stranger-success claim.** Nothing here shows a stranger can check
  anything. What the harness can show is **program-absent-harness success**: a
  procedure completed with this repository's script tree renamed away, on this
  Windows workstation, under §6's named weaker-than-a-container exclusions. No
  person outside this repository is in the instrument; STRANGER stays parked.
- **No version-drift claim**, deferred by B9 to a parked lane and priced in §11.
- **No composition claim.** Each kind is adjudicated alone; that kinds A and B
  each SURVIVE says nothing about a claim resting on both, and the census
  publishes no chain, closure, or coverage over kinds.
- **No coverage claim over the repository.** The census covers what CR-P0
  enumerates; later finds publish as census misses (B10), and a miss is evidence
  about the registry, not about the partition.
- **No retroactive effect.** A SURVIVES makes no past sentence true; a
  NEEDS-PROGRAM voids no run — it voids the *offline-checkability sentence* about
  that kind, and nothing else.
- **No security claim.** `scripts/_verifier_sandbox.py` states in its own
  docstring that it is a discipline boundary and not a security boundary — a
  sentence the 12 `python-tests` verdicts carry in their `checks` — and nothing
  here upgrades it.

**Suspended habit, for the duration of the slice:** no new artifact or document
may add a *"a stranger can check this offline"* sentence, in any wording, for a
kind this census has not classified. The tree already carries such sentences
honestly — `session_corpus_seal.json`'s `what_a_stranger_can_and_cannot_check` is
the model, because it states the negative half. The habit suspended is writing
the positive half without the harness behind it, which is the habit this item
exists to test.

**Where status lands.** `ROADMAP-v0.22.md` §2 carries the item and its
release-gate line; artifacts land under `cold/` with `census.json` sealed by
CR-P0; a stop publishes CR-P0 or CR-P1 as the headline with no capability
sentence shipped; ANALYSIS gets the partition's numbers; DISCOVERIES gets its
headline **if it moves what the program believed about its own checkability**,
which on §13's mapping it does at every value; BACKLOG gets nothing unless a
kind's repair is deferred, in which case it parks with the kind named.
