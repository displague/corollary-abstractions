# COLD RECEIPT — does the program's evidence survive the program's deletion?

**Status: DESIGN-ONLY.** Nothing here is built, no floor here is frozen, no run
is registered by this document. `ROADMAP-v0.22.md` §2 carries the ordering
obligation it discharges — *"Its compact design lands before its slice"*
(`docs/DESIGN-handles.md` §11) — and §4 names a census that must land before the
harness exists, on the WITNESS W0 precedent. Deviations from the outside draft
are marked **DELTA** with the finding that forced them.

## 1. The claim-kind this repairs

This programme's most load-bearing sentence is not a number. It is
`docs/DESIGN-session-ledger.md:71-72`:

> a stranger, handed the journal, can replay it offline and get the same bytes
> or a typed refusal

That sentence and its siblings have **never been tested with the producer
deleted**. Every check supporting them runs inside the repository that wrote
them, using the code that wrote them. The tool the sentence points at,
`scripts/replay_session.py`, imports `harness.CoreSession` and
`harness.route_line` (`:73-74`) — it *is* the program. Handed only the journal, a
stranger can do what `experiments/session_corpus_seal.json` already says (*"every
journal against the digests below: yes, offline, with no key"*), and that is a
check of **bytes**, not of any claim the journal makes.

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
about itself**, which is why this is an item and not a probe.

## 2. The frozen draft, quoted before it is elaborated

`reports/design-direction-v0.22.json`
`outcomes.series_2.preregistration_draft`, recorded **before ROADMAP-v0.22 was
written** — and checkable as written, since the receipt's `note_on_selection`
discloses that series 2's and 3's drafts were recorded at first writing and only
the *selected* HANDLES draft was added in the post-review patch. The **bold
labels and line breaks are this document's**; the receipt stores each field as
one unwrapped line and the strings are unaltered.

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

**B6's tense is repaired per `docs/DESIGN-handles.md` §11 (review H8):** *"200
scrambled bundles; **if** 0 of 200 pass, publish the 1.5% rule-of-three upper
bound as the chance rate."* A gate, not a recorded outcome.

## 3. `census.json` — one record per kind, every field's producer named

Field names are the draft's; the **producer** column is this document's, and is
the point: a census field with no named producer is one the harness invents at
run time.

| field | producer |
| --- | --- |
| `kind_id`, `emitting_routes[]` (`{route_id, writer_file, writer_symbol}`) | CR-P0's registry (§4); never minted by the harness |
| `bundle_manifest[]` | the harness, copying the files the kind's receipt names, plus their sha256 |
| `external_deps[]` | `{name, pin_hash, role, provenance}`; `pin_hash` from the existing pin table (`session_ledger.py:747` `pins()`), `provenance` by §7 |
| `recheck_procedure` | CR-P0 for the *declared* value, the harness for the *executed* one; a disagreement is a census miss under B10 |
| `verdict`, `verdict_evidence` | the harness, from the executed procedure alone — never from the declaration; evidence is the exact argv, exit code, stdout head |
| `blocking_dependency` + `confirmed_by_removal` | the harness's removal arm (B7) |
| `tamper_result` / `omission_result` / `sham_result` | the harness's three arms (§6) |
| `pin_audit_ref` | reference only (B9); a pointer into the pin table, never a verdict input |
| `census_seal` | CR-P0, sealed before the harness exists (B10) |

**The verdict vocabulary, stated hard.** `SURVIVES`: the procedure ran to a
correct verdict **with the program's script tree absent**, on the bundle and
`external_deps` alone. `NEEDS-PROGRAM`: the procedure requires this repository's
code, **confirmed by removal** rather than declared (B7) — a correct
NEEDS-PROGRAM scores as a hit, so the honest reading is not penalised.
`UNTESTED` is the downgrade sink: B11 lands here, and so does any kind whose
procedure the harness could not execute at all.

## 4. B1's meetability — the registry, registered rather than asserted

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
  executable."* Indicative coverage: **4 of the 13 files under `reports/`, 0 of
  the 111 under `experiments/`.**
- **`session_ledger.py:761` `PIN_FIELDS`** — the five pins B9 cedes drift to.

**Not machine-enumerable today, and this is the finding:** no table anywhere maps
a receipt kind to its emitting routes and its recheck procedure. An indicative
walk reached **fifteen candidate kinds**, tabled so review can attack the count
rather than a summary. The count is *indicative* — not a floor, not a prediction,
and explicitly **not** what CR-P0 must return.

| # | candidate kind | writer |
| --- | --- | --- |
| 1 | `x_corollary` per-route receipt (several shapes: `_resolution_receipt` `:1016` with `node_sha256`, `_ownership_receipt` `:1041`, `_evaluate_receipt` `:1064`, `_story_receipt` `:1097`, the `derivation`/`grounding` literals, `missing_capability`) | `serve_chat.py:1105` |
| 2 | `closure-receipt/1` certificate | `closure_query.py:64,278` |
| 3 | `conform` verdict receipt, built inline | `harness.py:2289` |
| 4 | `ownership` route receipt | `harness.py:1171` |
| 5 | `twin` route receipt | `harness.py:1917` |
| 6 | `write_stage` **staging** receipt | `write_stage.py:1538` |
| 7 | `write_stage` **applied** receipt (receipt-or-nothing, F3 `:2146`) | `write_stage.py:1906` |
| 8 | journal `Turn.receipt_digest` chain | `session_ledger.py:649`, written `session_recorder.py:199` |
| 9 | session **read log** (a deliberately separate writer) | `session_ledger.py:812` |
| 10 | external-verifier `Verdict` store (14 committed: 3 `lean4`, 11 `python-tests`) | `external_verifier.py:109` → `prover/verifier-verdicts/` |
| 11 | C-E3 probe `checker_receipt` | `conformance_ce3_supplement.py:395,605` |
| 12 | `radius-certificate` | `retraction_radius.py` → `reports/radius/*.cert.json` |
| 13 | provenance-graph edges | `report_provenance.py` / `provenance_graph.py` → `reports/provenance_graph.jsonl` |
| 14 | `plain_router` conditional-answer receipt | `plain_router.py:260` |
| 15 | registered-run artifacts, one level up | `experiments/session_ledger_run.json`, `experiments/conformance_run.json` |

**Two corrections the walk forced.** (1) There is **no `recheck_cmds` construct in
this repository**, under that or any adjacent name; the nearest real thing is
`scripts/radius_recheck.py`, which re-checks radius certificates and
**deliberately never imports their producer** — this design's closest existing
relative, and still program code. (2) `dump_server.py:169-178` emits a
**deliberately empty receipt beside a `"found"` status** as a committed voiding
control for the throughput metric; it is not a receipt kind, and a census that
counted it would be counting a sham the repository built on purpose.

> **CR-P0 — the route/kind registry census, a construction prerequisite.**
> Committed **before** any harness code exists (the WITNESS W0 pattern). It
> fixes: the executable enumeration rule; one `kind_id` per kind with its
> `emitting_routes[]` as `{route_id, writer_file, writer_symbol}`; the declared
> `recheck_procedure`; and the `census_seal` B10 freezes. It publishes
> **whichever way it reads**, and its count is **deliberately not predicted
> here**, because the census exists to measure the quantity a prediction would
> have to assume (R1's argument shape, `ROADMAP-v0.22.md` §3).
>
> **The draft's own B1 stop, kept in force:** if the enumeration cannot be made
> machine-executable — if identifying a kind's emitting routes requires reading
> code rather than running a rule — then **B1 is not meetable, the harness does
> not open, and CR-P0 publishes as the result**: *the program cannot enumerate
> its own evidence, which is a stronger finding than any verdict the harness
> could have returned.* A hand-written kind list presented as a registry is the
> construction defect §4.0(3) exists to catch.

## 5. The harness — what containerization this workstation actually has

The draft says *"harness/ container recipe"*. **DELTA, forced by the machine.**
This workstation has `docker` **29.6.2** on PATH with a WSL2 backend
(`Ubuntu-24.04`, `docker-desktop`), both distros **Stopped**; `docker info` fails
on `npipe:////./pipe/dockerDesktopLinuxEngine`. Podman is absent. So a container
is *startable* — and the recipe would still be wrong, for a reason unrelated to
availability: **the pinned checker is a Windows-native binary.**
`scripts/external_verifier.py:196-217` resolves it as
`Path.home()/".elan"/"toolchains"/<mangled>/"bin"/"lean.exe"`, pinned by
`prover/lean/normalizer/lean-toolchain` = `leanprover/lean4:v4.32.2`. Putting
that inside a Linux container requires either **downloading a Linux toolchain** —
breaking the hermetic rule the same file states in its docstring (*"NEVER
downloads"*) and changing the very `binary_sha256` the receipts pin — or
bind-mounting a Windows `.exe` a Linux kernel cannot execute. **A container that
has to download the checker is not a colder environment; it is a different one.**

**So the harness is a clean-PATH subprocess environment, and this document says
out loud that it is weaker than a container.** Its shape: the bundle is copied
**outside the repository**; the program's script tree is **renamed away**
(`scripts/` → a sibling name the subprocess cannot resolve) so an import is an
error and not a silent fallback — rename rather than deletion, because it is
reversible and the audit can prove it happened; the subprocess runs with a
**constructed environment** (`PATH` reduced to the explicitly listed dependency
directories, `PYTHONPATH` empty, `PYTHONHOME` unset, cwd inside the bundle); and
**`path_audit.txt`** is the proof rather than the promise — every `PATH` entry
with its absolute path and a listing digest, every invoked dependency with its
resolved path and sha256, and the assertion that the program's script tree
resolves to nothing with the failed-resolution evidence quoted.

**What this harness does NOT exclude, named so no reader has to find it:** the
Windows registry, `%USERPROFILE%` (and therefore `~/.elan`, where the checker
lives — §9), `.runtime/`, any system-wide Python and its `site-packages`, and
every ambient DLL search path. A container would exclude most of those. **This
one does not, and every `SURVIVES` in this census is scoped to that weaker
exclusion.** The scope travels with the number; it is not a footnote.

## 6. The four arms, per kind

**Tamper (B3), 3 mutations per kind, 100% must FAIL.** The three are *different in
kind*, not one shape run three times — v0.21's B8 was found to be exactly that
(`ROADMAP-v0.22.md` §5). (1) **Content**: flip one byte of a bundled artifact the
receipt covers. (2) **Digest**: change the recorded digest to match a tampered
artifact, so a checker comparing only a file to its own recorded hash passes. (3)
**Binding**: swap two records between receipts, leaving every file and digest
internally consistent and the *attribution* wrong — the one a presence-check
cannot catch.

**Omission (B4), FAIL LOUD naming the missing dependency.** Remove a listed
`external_deps` entry and run; the procedure must fail **and name what is
missing**. **A silent pass voids the harness** — not the kind — because a
procedure that passes without its dependency was never using it. v0.21's B4
self-comparison trap in different clothes (`ROADMAP-v0.22.md` §2).

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

## 7. Provenance tagging and the downgrade rule (B11)

Each `external_deps[]` entry carries `provenance`:
**`third_party_pinned`** — bytes pinned by digest, pin identifying a third
party's release (`binary_sha256` `567d145f…5ac7` for `lean.exe` v4.32.2, as
`experiments/conformance_ce3_supplement.json`'s `checker` block already records,
is the model case); **`program_configured`** — presence, location, version
selection or content arranged by this program or this machine's setup.

**The rule: any `SURVIVES` resting on a `program_configured` dependency
downgrades to `UNTESTED`.** Not to NEEDS-PROGRAM — the procedure may well be
cold-checkable; what is unknown is whether the world it ran in was prepared for
it, and `UNTESTED` is the honest name for unknown. The harness applies the
downgrade mechanically from the tag, so it cannot be argued away per kind.

## 8. Meetability, floor by floor (ROADMAP-v0.21 §4.0(3))

> *Every frozen floor now ships with a meetability argument — a pilot, a
> construction argument, or a bounded-class analysis showing a correct instrument
> can reach it. A floor without one is a construction defect discovered at
> registration time, not a gate waiting to void.*

| floor | meetability argument |
| --- | --- |
| **B1** | *Not argued, deliberately.* §4's CR-P0 is the pilot and carries the stop clause — the one floor whose meetability is a prerequisite, not an argument. |
| **B2** | *By construction, one worked instance.* `conformance_ce3_supplement.json` carries per row the `substituted_proposition` verbatim, the template `example : (<prop> : Prop) := by decide`, each probe's `source_sha256`, the toolchain string and the binary digest. A reader with `lean` v4.32.2 rebuilds the probe text, confirms its hash, runs it, compares the exit code — **with none of this program's code**. That is the raw-checker-invocation exception the draft names; B2 is a floor of one because the walk found exactly one such pattern. |
| **B3** | *By construction*, on the C-V4′ shape: each mutation provably changes an input the procedure reads, and a mutation without a witness of difference is discarded and counted before any rate. A kind whose procedure cannot be shown to read the mutated input yields no tamper arm and is `UNTESTED`, never a silent pass. |
| **B4** | *By construction*: removing an invoked dependency produces a resolution failure. The clause's real work is the **naming** requirement, a property of the harness's error handling. |
| **B5** | *By construction*: an accept-all stub cannot produce a *correct* verdict on the known-bad bundle each kind is also run against. |
| **B6** | *Bounded*: a deterministic seeded measurement; 200 is a cost, not a bar. |
| **B7** | *By construction, and the clause that makes the census non-punitive*: a correct NEEDS-PROGRAM scores as a hit, so the instrument has no incentive to over-read SURVIVES. |
| **B8** | *The too-good clause*, B3's 49/50 in this cycle's clothes: a first run at ≥90% SURVIVES is likelier a harness that failed to remove the program than a repository of cold receipts, and it voids **pending** an audited-empty-PATH re-execution rather than terminally. |
| **B9** | *Trivially*: reference only. §9 says what that concedes. |
| **B10** | *By ordering*: CR-P0 commits first; later finds publish as **census misses**, counted, never folded back into the seal. |
| **B11** | *By construction*: a tag per dependency and a mechanical downgrade. |

## 9. The residual risk, quoted, and what remains unpriced

> the harness deletes the program's code while keeping the program's prepared
> world -- program absence is priced, environment provenance was not; the added
> clause is the repair

B11 prices it as far as a tag can. **What remains unpriced, named rather than
left to be found: the checker binary itself is program-installed.** `lean.exe` is
a third party's release, pinned in the C-E3 receipts by `binary_sha256`, and it
sits at `~/.elan/toolchains/leanprover--lean4---v4.32.2/bin/lean.exe` because
**this machine's `elan` put it there** — four toolchains are installed side by
side (`v4.20.0`, `v4.29.1`, `v4.32.2`, `v4.33.0`), and which one a receipt names
is a repository file's content.

That **does** prove the bytes that ran are identified: a reader obtaining `lean`
v4.32.2 from leanprover and finding the same digest is checking the same program.
It does **not** prove the reader can obtain it without a network (the hermetic
rule forbids the *program* downloading and says nothing about the reader); that
the harness's environment is free of `elan`'s other arrangements, since
`Path.home()` resolves under a clean `PATH` and §5 does not exclude
`%USERPROFILE%`; or that the pin covers the binary generally —
**`session_ledger.checker_toolchain_digest` (`:722`) is the sha256 of the
`lean-toolchain` *file*, a hash of the text that names a version, not of the
binary.** The C-E3 supplement's per-row `binary_sha256` is the only place the walk
found the binary's own bytes pinned. B9 cedes version drift to the pin audit;
this is what that cession costs.

**And the tree already holds an instance of the drift B9 cedes.** Three
`lean-toolchain` files pin `v4.32.2` (`normalizer`, `ingested`, `session`); a
fourth, `prover/lean/proofcurve/lean-toolchain`, pins **`v4.29.1`**. Whether that
is deliberate or drift is **not determinable from the files**, and this design
does not decide it — it records it as a `pin_audit_ref` the census must carry, so
a divergence B9 declines to adjudicate is visible where a reader meets the
verdicts.

**A second unpriced item.** A receipt whose digest is taken over a
**program-defined canonicalization** is not offline-recheckable even in principle
without the program: `serve_chat`'s resolution receipt carries `node_sha256` =
`sha256(canonical_bytes(node))`, and `canonical_bytes` is this repository's
function. Such kinds are expected to read NEEDS-PROGRAM, and the census must
record the *reason* — `canonicalization_is_program_defined` — so the partition
distinguishes a kind that needs the program to **adjudicate** from one that needs
it only to **serialize**. That distinction is a finding the harness can produce
and prose cannot.

## 10. Construction prerequisites

- **CR-P0 — the route/kind registry census (§4), committed BEFORE the harness**,
  with its stop clause. Nothing else in this design exists until it lands.
- **CR-P1 — one worked stranger-path transcript, on the B2 instance, before the
  general harness.** The draft lists the transcript among the artifacts; ordering
  it *first* is this document's DELTA, on the WITNESS W1 precedent (learn what
  the procedure can do before building a runner for it). It is a hand-executed
  cold re-check of one C-E3 row: reconstruct the probe text from
  `substituted_proposition` and `pattern`, confirm `source_sha256`, invoke the
  pinned binary by absolute path, compare the exit code. **If the hand-executed
  path cannot be completed, B2's floor of one is not meetable and the slice
  publishes that instead of opening.**

## 11. Stop conditions, non-claims, suspended habit, where status lands

**Stop and publish** if CR-P0's enumeration cannot be made machine-executable
(§4's stop); if CR-P1's hand-executed path cannot be completed (B2 unmeetable);
if B4's omission arm passes silently (the harness is void, not the kind); if the
sham checker leaves any kind reading SURVIVES (the voiding sentence, void for
every kind in the census); or if the harness cannot be constructed with a
`path_audit` proving the program's script tree unresolvable.

**Non-claims:**

- **No stranger-success claim.** Nothing here shows a stranger can check
  anything. What the harness can show is **program-absent-harness success**: a
  procedure completed with this repository's script tree renamed away, on this
  Windows workstation, under §5's named weaker-than-a-container exclusions. No
  person outside this repository is in the instrument; STRANGER stays parked.
- **No version-drift claim**, ceded to the pin audit per B9 and priced in §9.
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
  docstring that it is a discipline boundary and not a security boundary, and
  nothing here upgrades it.

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
which on the tiebreak's argument it does at every value; BACKLOG gets nothing
unless a kind's repair is deferred, in which case it parks with the kind named.
