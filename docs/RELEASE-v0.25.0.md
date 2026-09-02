# v0.25.0 — the person declares a symbol, and the review found what green was carrying

This cycle gave the person a way to tell the system what their own vocabulary
*is*, and then discovered — by adversarial review, not by any gate — that the
first registered run's green was resting on two checks that could not have
failed, a control that could not have fired, and a sealed name sitting in the
program's own worked example. It ships as a **capability** — twelve gates
green on repaired instruments, R-H1 licensed — and as a **method result**:
the run that produced the green is retained, superseded, and labelled with
exactly what it is and is not evidence of.

- **A declaration is now a decision on the record.** A person declares a
  relation symbol — name, arity, argument categories — and the system either
  admits it into a session-scoped ledger or refuses it with **exactly one**
  deciding clause, totally and by default toward refusal. **14,063** inputs
  decided with **0** fall-throughs; **8 of 8** refusal codes reached by a
  machine-enumerated sweep; a misused declared symbol refused **by name**
  where yesterday it was opaque text. All **twelve** gates GREEN,
  `gate_reds: []`, the voiding sentence unfired, **R-H1 licensed**
  (`experiments/house_rules_verdicts.json`).
- **The review moved four instruments, and the green narrowed.** B3 executes
  no mutant and now says so in the first field a reader meets; two of its
  detectors could not fail and are repaired or retired; B9's registered
  control family **could not have fired on this corpus** (ceiling 0.736842
  against a threshold of 0.784211) and that caveat now travels with R-H1's
  own sentence; and the served `declare` grammar example carried an
  **ADMITTED fixture symbol** through H-P0 and through run 1 — b3-m08's own
  sealed vector, sitting in the committed tree while B3 scored that mutant
  STOPPED.
- **The parser hazard is discharged as disclosure, not as a fix that never
  happened.** `sum_total(x)` **still** parses to `sum` and still loses
  `total`; what changed is that the capture is now recorded in the term's own
  receipt, totally, for all 17 real big-op templates as loudly as for the
  hazard. H-P0's `RESERVED_PREFIX` guard fires at the **declaration boundary
  only** and is not a parser fix.

**Links** — previous release: [v0.24.0](RELEASE-v0.24.0.md) · closed plan:
[ROADMAP-v0.25](ROADMAP-v0.25.md) · next plan:
[ROADMAP-v0.26](ROADMAP-v0.26.md) · release triage:
[TRIAGE-v0.25](TRIAGE-v0.25.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[the checks that could not have said no](blog/the-checks-that-could-not-have-said-no.md)
· this cycle's design: [DESIGN-house-rules](DESIGN-house-rules.md)
· forward design: [DESIGN-repairable-refusal](DESIGN-repairable-refusal.md)

## The headline finding: a fresh symbol, one deciding clause, and nothing that survives the turn

**Before.** A person could already `suppose x = 5` — a session-scoped
assumption, capped at 8, superseded by subject, consumed by `evaluate`. But a
supposition that is not a binding was held as an **opaque atom**: `suppose
parent(alice, bob)` stored normalized text and nothing more. The system could
not tell a well-formed use of the person's own vocabulary from a typo,
because the person had no way to say what their vocabulary *was*.

**Now.** A declaration line reaches a total function that returns exactly one
verdict with exactly one deciding clause, in a committed clause order, by
default toward refusal. One verdict kind ships —
`ADMITTED_DECLARED_SYMBOL` — and axioms, premises, conservativity, export,
persistence and truth are all refused **in writing** by the same function. A
use of a declared symbol at the wrong arity is refused as
`USE_ARITY_MISMATCH`, naming the declaration it violates.

**Demonstrate.** Read the twelve verdicts off the committed ledger:

```
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/house_rules_verdicts.json',encoding='utf-8')); \
    print(d['gate_greens']); print(d['gate_reds']); \
    print(d['voiding_sentence']['fired']); \
    print(d['result_gates']['R-H1']['licensed_sentence'])"
```

The twelve-gate table, as scored on run 2 at `f9719a2`:

| gate | verdict | what it measured |
|---|---|---|
| B1 | GREEN | **14,063** inputs decided — 14,024 machine-enumerated sweep mutants plus 39 sealed declaration fixtures — **0** fall-throughs, **0** deciding clauses outside the committed order, **39/39** fixtures on the seal, all **6** multi-ground fixtures' ground sets equal to the seal exactly |
| B2 | GREEN | **0** of 17 swept admitted names collide with the **286**-member committed census; `check_symbol_census.py` recomputes the census from source as a second program; both named cases refuse as sealed |
| B3 | GREEN | **32/32** sealed mutants stopped **by a live detector**, floor 30, 0 survivors, 0 uncovered, 0 class mismatches — and no mutant is executed by anything (below) |
| B4 | GREEN | `working_tree_digest` byte-identical (`c792b8cb…` → `c792b8cb…`); `durable_digest` over `data/` unmoved; 0 paths appeared, 0 vanished, **0** stage records |
| B5 | GREEN | **0** of the run's documents carry an admitted name; `session_state.encode` refuses both record types; a fresh session takes the opaque-atom path; **19** pre-existing repository files disclosed and mechanically classified |
| B6 | GREEN | **3/3** wrong-arity uses refuse `USE_ARITY_MISMATCH` naming the declaration; **5/5** undeclared applied atoms byte-identical to the pre-slice path on the empty-ledger arm **and 5/5 on the new populated arm** (4 symbols admitted) |
| B7 | GREEN | **8 of 8** refusal codes reached on the enumerated sweep against a floor of 6, no hand-only codes; the stateless control reaches **5 of 8**, and the difference is exactly the three session-state clauses |
| B8 | GREEN | removing `meet` from a census copy flips `hr-fx-s3-t25` to admitted; removing `statistic` from a schema copy flips `hr-fx-s1-t02` and `hr-fx-s2-t02`, and those two are **every** admitted fixture citing that category |
| B9 | GREEN | the voiding sentence did **not** fire — and the registered family could not have fired it (below) |
| B10 | GREEN | `7a47a8a` a **strict** ancestor of the scoring tip `32d505a`; all **7** frozen pins re-digested and unmoved; clean tree; `registered_before_the_run: true` |
| B11 | GREEN | import closures of **3** files each for `symbol_ledger.py`, `check_symbol_census.py` and `build_symbol_census.py`; **0** forbidden imports from a list naming `torch`, `numpy`, `transformers`, `openai`, `anthropic` and ten others |
| B12 | GREEN | **13/13** declare-then-use pairs resolve to the **LIVE** ledger key, accumulated in turn order; **16/16** reserved-prefix-adjacent mutants on their sealed verdict |

**R-H1 is licensed, and its sentence is exactly this much** — quoted verbatim
from `experiments/house_rules_verdicts.json`,
`result_gates["R-H1"].licensed_sentence`:

> *"A person can declare a fresh relation symbol with arity and argument
> categories; the system admits it into a session-scoped ledger or refuses
> with one deciding clause, totally; a misused declared symbol is refused by
> name where yesterday it was opaque text; and nothing declared survives the
> session or touches the library."*

**And the caveat travels with it**, in the artifact's own `caveat` field
rather than in a paragraph a reader can skip:

> *"The registered B9 family's ceiling on the scored half is 0.736842 against
> a threshold of 0.784211: NO MEMBER of the registered family could have
> fired the voiding sentence on this corpus. B9's green is therefore evidence
> that the registered control did not separate the verdict, and not evidence
> that no surface-only rule can."*

**R-H3, the bounded negative, is not licensed either.** Its clause names
"any failed construction gate B1–B8/B10/B11 or a fired B9"; there is no red
in scope and nothing fired. The scope was read off the clause rather than
widened to every scored gate, which is what `bool(reds)` would have done —
and did, in the freeze, until the review caught it.

## Roadmap triage

Adjudicated clause by clause against primary artifacts in
[TRIAGE-v0.25](TRIAGE-v0.25.md); that document is the source for every
disposition below. **Eleven §4 clauses: nine settled, two named open.**

| item | outcome |
|---|---|
| **§1 HOUSE RULES** | **SHIPPED, R-H1 GREEN.** Twelve gates green over 14,063 decided inputs; `gate_reds: []`; the voiding sentence unfired; **on the second registered run**, the first having been superseded after review |
| **§1.1 the course's selection** | **RECORDED as a decision** at commission (`d11e3fb`), with a disposition for **every** incumbent. HOUSE RULES scheduled; the `sum_total` lane ordered before H-P0; STRANGER-GATE **honored, not displaced** |
| **§1 H-PRE** | **SHIPPED** (`7a47a8a`). The fixture corpus sealed **before** any checker existed to fit it: 60 fixtures, 39 declarations, 13 admitted, 26 refused, all 8 refusal codes fired, plus the B3 mutant set and the `clause_order` copy the runner later had to be made to read |
| **§1 H-P0** | **SHIPPED** (`c87b0ca`, sealed at `e3e3980`). The census (**286** equality members over 12,777 templates, 5 prefix-guard entries), `scripts/symbol_ledger.py`, the `declare` grammar row, **and in the same change every pin that row moves** |
| **§1 H-P1** | **SHIPPED ON RUN 2** (`27d358d` freeze → `2ac8c9f` run 1 → `32d505a` fix-freeze → `f9719a2` run 2). Run 1 retained at `experiments/superseded/`, never re-scored |
| **§1 construction refusals** | **NONE OCCURRED.** (1) One verdict kind ships; axioms refused by the grammar, not by dead code. (2) No persistence: B5 green, 0 of the run's documents carry an admitted name. (3) No byte toward a generated library file: B4's `working_tree_digest` byte-identical, `durable_digest` unmoved, **0** stage records, and `git status --porcelain --untracked-files=all` after the run listed exactly the two declared output paths |
| **§1 R-H2** | **REPORTED, GATING NOTHING. 0 of 30.** None of the sealed inbound hypotheses parses as a declaration, counted under the more generous of two readings. The reading was pre-committed and stands |
| **§2 the `sum_total` lane** | **SHIPPED as disclosure** (`156e94f`, `249f463`), ordered **before** H-P0 exactly as §2 required, so H-P0's prefix guard cannot be read as having discharged it |
| **§2 B7 successor probes** (Plan-mode router / echoed `function_call`) | **CARRY, unrun, triggers unchanged.** Neither named a dependant by §1; the standing arithmetic travels with the second |
| **§2 GUEST AXIOM / ECHO / HANDBACK** | **PARK, unpark triggers unchanged.** No drawing rule, no dated amendment, no restricted population ≥15. GUEST AXIOM's B6 remains **unadjudicated, not discharged**, and is the lane's first act on unpark |
| **§2.1 refinement adoptions** | **ALL FOUR SHIPPED.** B12 round-trip identity (13/13 pairs, 16/16 mutants, reported *beside* R-H1 and deliberately not folded in); the B9 class-balance seal (`0.684211` / `0.784211` / 10 points, frozen before the run); the B5 harness-scope sentence; R-H2's pre-committed reading |
| **§3 carried lanes** | **CARRIED** to [ROADMAP-v0.26](ROADMAP-v0.26.md) §3, each with its trigger. The naming-layer question's own re-examination clause **fired and was answered NEGATIVE** at the v0.26 course. The cost ledger takes its **ninth** recorded pass-over |
| **CR-P0 registry re-seal** | **SHIPPED TWICE.** `11d62b8` re-sealed after H-P0 (190 → 194 files, `d3d9bdc6…` → `edb44684…`) and the cold reading re-attested it — partition **1 SURVIVES / 12 NEEDS-PROGRAM / 9 UNTESTED**, unmoved from v0.24. H-P1's two new programs then staled it again, and the rotation's own re-seal closes it: *"[CR-P0] Re-seal after H-P1's two programs: 196 files, two new kinds, and both moved pins are the grammar repair"* (**`[HASH-TO-CONFIRM-V25]`**) — 194 → **196** files, 43 → **47** receipt-marked sites, 22 → **24** kinds, seal `edb44684…` → `a4f38d55…` |
| **the live cold re-read** | **`[COLD-RUN2-V25]`** — see the placeholder section below |
| **§4 `[SUITE-GATE-V25]`** | **OPEN at rotation.** See the placeholder section below |

## The review, in full, because the repair is this cycle's result

An independent adversarial review of the freeze (`27d358d`) and the first
registered run (`2ac8c9f`) **reproduced every number in run 1** and returned
MERGE AFTER FIXES. Not one finding is arithmetic. All four are about what the
numbers were evidence *of*.

**F1 — B3 executes no mutant, and never said so.** The 32 mutants sealed at
H-PRE are **prose descriptions**; nothing in this repository executes one,
and the map from mutant id to detector is **authored in the runner** rather
than sealed with the mutant. Run 2's B3 row now leads with
`mutants_are_descriptions_not_executions` before any number, publishes each
mutant's sealed `stopper_mechanism` beside the detector mapped to it, checks
the detector's mechanism *class* against that sentence by a keyword table
published in the artifact, and prints per-detector coverage counts so no
prose number can drift. The mismatch list is **reported, never scored** — a
coarse instrument turned into a gate after a score is the move the
registration exists to forbid.

**F2 — two detectors could not fail.** `name_sweep` planted a string in a
`TemporaryDirectory` and found it again: a property of `str.__contains__`,
true of any tree, and it carried **seven** of the 32 mutants. It now runs the
sweep B5 runs — positive and negative controls on the real repository tree, a
planted control on the bytes the run is about to write, and the arm that can
go red, the unplanted pending output itself. The negative control's probe
name is **derived from a sha256** rather than written as a literal, because a
literal would live in the runner, the runner is inside the swept tree, and
the control would find its own source and report that the sweep matches
everything. (It did, on the first rehearsal. That failure is why the probe is
derived.) `checker_inputs_exclude_the_runs_outputs` asserted an absence true
of every module that never mentions those paths; it is **retired by name**,
and its mutant re-pointed to `name_sweep`.

**F3 — the blind control could not have fired.** The registered family of 95
threshold rules tops out at **0.736842** on the nineteen-row scored half
against a void threshold of **0.784211**. No member could have fired,
whatever the fit half selected. The fitted rule `line_length:eq:28`
additionally predicts one class for **every** scored row, which is why its
reported agreement of 0.684211 equals the majority-class rate to the digit —
by arithmetic, not by signal. Run 1 reported the equality and not the reason.
Both are fields now, the second program **re-enumerates** the family and
recomputes the ceiling rather than reading it, and a richer family (2,632
rules, fitted on the **fit half only** with a tie-break declared before the
fit) is reported whatever it says: it scores 0.684211 out of half and does
not fire. Its ceiling on the scored half is 0.789474 — above the threshold —
and is **labelled in the artifact for what it is**: selection on the half it
is scored on, not a control score. **The gate is still the registered
family**, because a control chosen after a result is not a control.

**F4 — the leak, which is the one that changed the tree.**
`serve_chat.LINE_GRAMMAR`'s `declare` row carried, as its example line,
`hr-fx-s1-t01`'s **ADMITTED fixture symbol** — from `c87b0ca` through run 1 —
and so did `experiments/session_p1_command_bound.json`, the generated
artifact that echoes the grammar, and the capability sheet served from it.
That is b3-m08's sealed vector verbatim, present in the committed tree while
B3 scored b3-m08 STOPPED. B5 could not see it because B5 is scoped to the
run's **output** tree, by design; the digest detector cannot see a name that
is already committed. **The review found it; no gate did.** The example is
now a placeholder checked against the census, the schema and the whole
fixture corpus before it was chosen; the generated artifact is regenerated by
its writer, not hand-edited; `line_grammar_digest` moves with it; and the
standing detector `grammar_example_names` sweeps the served grammar rows and
their generated echo on every run, with a test that drives it red by planting
a derived name in a grammar row.

**What the amendments do and do not do.** Five dated `amd-2026-09-02-*`
amendments carry all of it. No frozen prereg row is edited in place, and each
amendment states **in its own bytes** that it was authored **after** run 1's
score and that it loosens nothing: B3's floor is still 30 of 32, B7's is
still 6 of 8, B9's margin is still ten points, and R-H1's requirement list is
still B1–B11. The seven frozen pins are byte-identical across the repair.

**Run 1 is retained, never re-scored** (`experiments/superseded/`, with a
README saying exactly what it is). Its twelve-green table stands as the
record of what the run-1 runner scored. It is **not** evidence that the
capability was contained, because two of the checks behind B3 could not have
said otherwise. That distinction is why the files are kept rather than
deleted.

## What changed, per area

### The symbol ledger and the `declare` row

**Before.** `suppose parent(alice, bob)` stored normalized text. There was no
symbol ledger, no `declare` command word, and no way for a person to state a
name, an arity and argument categories.

**Now.** `scripts/symbol_ledger.py` is a pure, total, mutation-free decider
over a committed `CLAUSE_ORDER`, and the `declare` row is published in
`serve_chat.LINE_GRAMMAR`. The ledger is session-scoped runtime state that
`session_state.encode`'s closed `_TYPES` registry **refuses to serialize** —
asserted by B5 rather than promised.

**Demonstrate.** `experiments/house_rules_receipts.json` carries 39
per-fixture receipts, set-equal to the sealed declaration fixtures and each
decided on the clause the **seal** maps its code to;
`scripts/check_house_rules_receipts.py --replay` re-runs the runner at the
tip and compares byte for byte outside a named tip-dependent mask.

### The symbol census, and the two programs behind it

**Before.** No enumeration existed of the names the library already owns, so
"fresh" had no denominator.

**Now.** `experiments/symbol_census.json` holds **286** equality members over
12,777 templates plus 5 prefix-guard entries, built by
`scripts/build_symbol_census.py` and **recomputed from source** by a separate
program, `scripts/check_symbol_census.py`. Two sides, two programs, so a
mismatch can actually go red.

**Demonstrate.**

```
$ PYTHONIOENCODING=utf-8 python scripts/check_symbol_census.py
CENSUS OK: experiments/symbol_census.json reproduces from source — 286 equality
members over 12777 templates, 5 prefix-guard entries
```

### The `sum_total` capture: total disclosure, and exactly what the parser still does

**Before.** `scripts/match_signatures.py` rewrote any identifier beginning
`sum_ / prod_ / lim_ / max_ / min_` into the corpus aggregate head and
discarded everything after the first underscore, **with no refusal**. The
v0.25 review found it in code that ships.

**Now — and the release gate requires this stated precisely rather than
inferred from the absence of a complaint.** The parser **still** does it.
`Parser.parse_atom` (`scripts/match_signatures.py:541-563`) still tests
`BIG_OP_PREFIXES`, `sum_total(x)` still becomes a `("call", "sum", …)` node,
`sum_total` and `sum_anything` still produce one identical tree, and **no
refusal exists**. What `156e94f` added is exactly one thing: the branch now
appends a record to `Parser.rewrites` *before* it discards anything — the
rule name, the authored token verbatim with the author's own casing, its
index, the head it became, and the discarded characters — which `load_nodes`
hands to `ParsedNode.parse_rewrites` and which
`reports/signature_matches.json` republishes in two places. The tree is
unchanged; all 12,777 committed trees are unmoved.

**Why disclosure and not refusal — a census, not a preference.** Across
14,830 committed `anonymized_template` strings (13,950 distinct, over 40
files), exactly **17** hold a big-op-prefixed identifier: `sum_i` in 16 and
`lim_h` in 1, across nine disciplines. There is no `prod_`, `max_` or `min_`
occurrence at all. Genuine big-operator usage is real, and a refusal would
break sealed committed parses that are not defective. The heuristic that
*would* have separated them — all 17 real suffixes are single-letter index
names — is **deliberately not implemented**, because it is a new authored
judgement the design never priced and it would put the parser in the business
of deciding which captures deserve a record. The disclosure is **total**:
`sum_i` is recorded exactly as loudly as `sum_total`, and that totality is
what makes it judgement-free.

**What H-P0's prefix guard does NOT change.** `scripts/symbol_ledger.py`'s
guard fires at the **declaration boundary only** — a person typing `declare
sum_total(...)` is refused `RESERVED_PREFIX`. It does not run when a template
is parsed, it is not on `match_signatures.py`'s call path, and it changes the
behaviour of exactly **zero** committed templates. A reader who took
"declaring `sum_total` is refused" to mean "the parser no longer silently
rewrites `sum_total`" would be wrong, and this paragraph exists so that
reading is unavailable.

**The standing detector.** B12 — round-trip identity, with mutants seeded at
reserved-prefix-adjacent names — is what keeps the two surfaces from drifting
apart again. GREEN at `f9719a2`: 13/13 pairs against the live ledger key,
16/16 mutants.

**Demonstrate.** `reports/signature_matches.json`, the top-level
`parse_rewrites` section beside `parse_problems`, and the per-member field
inside twin groups; `scripts/check_report_regeneration.py` reads that report
**clean**, meaning the committed bytes equal what the changed writer produces
— the disclosure was regenerated by its own writer, never hand-edited.

### The registry census and the cold reading

**Before.** `experiments/cold_registry_census.json` was sealed at
`d3d9bdc6…` against v0.24's tree.

**Now.** Re-sealed twice, and each movement has a name. `11d62b8` re-sealed
after H-P0 — `program_tree_files_scanned` **190 → 194**, seal `d3d9bdc6…` →
`edb44684…` — and the live cold reading re-attested it in the v0.23 order
(registry committed **first**, then the re-read): partition **1 SURVIVES /
12 NEEDS-PROGRAM / 9 UNTESTED** over 22 kinds, identical to v0.24's, all
eleven gates B1–B11 green, R-C green. H-P1 then added two programs under
`scripts/**` and edited the served grammar, so the rotation's own re-seal
closes it: **194 → 196** files, **43 → 47** receipt-marked sites, **22 → 24**
kinds, **11 → 12** exclusions, seal `edb44684…` → `a4f38d55…`. The two new
kinds arrive **with** committed instances, because the registered run's
artifacts landed before the seal — a re-seal belongs after the last artifact
the cycle commits, and this rotation applied that lesson on the first try
rather than after a discarded run.

**Two pins moved with it, and both are the same repair.**
`line_grammar_digest` `43024c67…` → `6cf86f0c…` and `capability_sheet_digest`
`80f0ea19…` → `79a0f6dc…`. Neither is H-P0's `declare` row — that moved them
at `c87b0ca` and was sealed there. These are `32d505a`'s repair of the
grammar-example leak.

## Discoveries of the cycle

Quoted, not duplicated — see [DISCOVERIES](DISCOVERIES.md). All three are
surprises about **instruments**, not about the capability, which is the kind
this slice produced:

- **"A containment gate whose mutants are prose is a gate that has never been
  run."** *"What a containment gate must be next time: the mutants must be
  EXECUTABLE — a program that performs the attempt against the live harness
  and returns what happened — and the seal must carry a machine-readable
  detector id per mutant rather than a prose sentence a later runner is free
  to interpret."* Status: near-miss, kept deliberately.
- **"A blind control on nineteen rows could not have voided anything."**
  *"A control that cannot fire measures nothing, and a nineteen-row held-out
  half moves 0.0526 per row… the family's own ceiling must be checked against
  the threshold at registration time — which is a one-line computation that
  would have caught this before any score existed."* Status: near-miss.
- **"The system published an admitted symbol in its own grammar example."**
  *"An example is a value, and a value drawn from a sealed corpus inherits
  that corpus's prohibitions. Every generated artifact that echoes an
  authored example is a copy of that value, and a containment gate scoped to
  a run's outputs will never look at any of them."* Status: exact.

## Resolved from BACKLOG

- **HOUSE RULES — shipped as the v0.25 headline.** The design-input entry
  filed at the v0.25 course is pruned; its record is this document.
- **The `sum_total` silent-capture hazard**, filed at the v0.24 rotation
  against the v0.25 design review, is **discharged as disclosure** — with the
  parser's surviving behaviour stated above rather than glossed.
- **The stale registry seal** left knowingly by `156e94f` is discharged by
  the rotation's CR-P0 re-seal.

Kept, deliberately: the **two B7 successor probes**, unrun and untaken;
**GUEST AXIOM's B6**, still unadjudicated rather than discharged, filed by
the v0.24 deep triage and inherited unchanged; and the new standing items
this cycle leaves behind — B3's *described-not-executed* successor
requirement, B9's family question, and B3's `name_sweep` positive control's
coupling to a tree property, filed unfixed at `[TRIAGE-V25-LOWS]`. New parks
from the v0.26 course are filed in [BACKLOG](BACKLOG.md).

## Honest limits carried forward

- **The fixtures are construction fixtures**, authored by this repository.
  Exact conformance establishes nothing about what people will declare. There
  is no population claim here, and **R-H2's 0 of 30 is not one either** — the
  reading was pre-committed before the run: *approximately zero was expected,
  it is neither a failure nor evidence of demand, and it may not be read
  either way now.*
- **B3 measures detectors, not attempts.** No mutant is executed by this run
  or by any program in this repository. What the gate establishes is that
  each mapped detector was exercised on live material and fired. Anything
  short of executable mutants measures that a detector fires, which is a fact
  about the detector.
- **B9's green is narrower than it looks.** The registered family could not
  have fired on this corpus. B9 is evidence that *the registered control* did
  not separate the verdict, and not evidence that no surface-only rule can.
- **B5 evidences NO WRITES OBSERVED UNDER THIS HARNESS, never CANNOT WRITE.**
  The scope sentence travels with the verdict, and the whole-repository
  disclosure (19 pre-existing files, every one mechanically classified) is
  published so a reader can judge the scoping against a measurement rather
  than a description.
- **`has_command_word` is constant across all 39 declaration fixtures**, so
  one of the three allowed admitter inputs is degenerate — disclosed by the
  gate about itself.
- **The non-claims, verbatim** from
  `experiments/house_rules_verdicts.json`.`non_claims`:
  ledger-groundedness, never correspondence — an admitted declaration is
  well-formed and fresh, never true or useful; no axioms or premises about
  declared symbols, and no conservativity; no use-side CATEGORY checking; no
  natural-language declaration; no persistence, and no export toward library
  files; no behaviour on the served HTTP profiles beyond the published ¶DEV-1
  note; no claim about what people will declare once they can.
- **The parser still rewrites.** See above. The hazard is disclosed, not
  fixed, and the declaration-boundary guard is not a parser fix.
- **STRANGER-GATE has still never run.** This release evidences that **no
  untrusted stream was opened** — which is what the prohibition asks — and
  not that the write gate would survive one. Its recorded residual risk is
  unchanged: one head authors the attacks, the twins and the gate, so it can
  only measure whether the gate DISCRIMINATES, never whether the corpus is
  ADEQUATE. DEPUTY remains blocked behind it.
- **Everything v0.24 left open is still open.** B7 is still RED and no Codex
  prompt-tool support is claimed; GUEST AXIOM served no implication; ECHO
  produced no collision table; the ledger-first lane's non-comparability
  sentence still travels with it, because no throughput readout ran.
- **The forward design is unimplemented and was reworked twice.**
  [DESIGN-repairable-refusal](DESIGN-repairable-refusal.md) took **two**
  independent adversarial reviews; the second review's Critical was a defect
  the *first* rework introduced — the headline gate preregistered against an
  undefined symbol. Nothing in it is implemented, and its own residual risk
  is stated inside it: the algebra defines the corpus's difficulty.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.** `data/` and
every `experiments/*.py` are byte-identical to `v0.24.0`
(`git diff --stat v0.24.0..v0.25.0 -- data experiments/*.py` lists **nothing
at all**; the experiments tree moved only in `.json` ledgers,
`ANALYSIS.md`, and the retained `experiments/superseded/` run-1 pair), so the
checkpoints attached to **v0.6.0** remain accurate for this release.
Measurement ledgers are committed in-repo at `experiments/*.json` —
`house_rules_fixtures.json`, `house_rules_prereg.json`,
`house_rules_receipts.json`, `house_rules_verdicts.json`,
`symbol_census.json`, `big_op_disclosure_prereg.json`,
`session_p1_command_bound.json` and the re-sealed
`cold_registry_census.json` — plus the superseded run 1 at
`experiments/superseded/` with its README.

## Ledger refresh (the release gate requires these verdicts in the notes)

`scripts/check_regeneration.py` — **exit 0**: *"coherence OK: 25 seeds
regenerate committed data byte-identically across `data/`,
`data_holdout/`."*

`scripts/validate_nodes.py` — **exit 0**: *"Validation passed for 12777
statement nodes across 27 corpora."*

`scripts/check_report_regeneration.py` — **exit 0**, four verdicts:

```
reports/signature_matches.json clean
reports/specializations.json   clean
reports/compression.json       clean
reports/decompositions.json    declared_divergence (declared pre-scale snapshot;
                               TRIAGE-v0.11 gate table row 6 and §5 — live
                               analysis is the pin source)
```

Three clean, one **declared** divergence. Worth stating because this cycle
could have broken it: `156e94f` changed `scripts/match_signatures.py`, the
writer behind `signature_matches.json`, and that report reads **clean** —
the disclosure was regenerated by its own writer.

`scripts/check_symbol_census.py` — **exit 0** (this cycle's new second
program; it recomputes the census from source rather than reading the
artifact).

`scripts/ingest_wold.py reach` — **CANNOT VERIFY, and that is not a skip.**
The stage refuses (exit 2) because the manifest-pinned Open English WordNet
archive is absent:

```
MISSING: <repo>\data_sources\archives\english-wordnet-2025-json.zip not present.
Fetch the pinned source first:
  python scripts/fetch_sources.py --fetch wordnet-2025-json
```

`run_reach` treats the archive as **required, not optional**, in its own
words *"so the committed number is never a silent partial"*; the archive is
licensed external data and never enters git. What is **not** claimed: that
`experiments/wold_reach.json` is stale, or that it is current. Neither was
checked, because the check is exactly the thing that could not run. `data/`
did not move this cycle, so the committed artifact stands unexamined and that
is the honest state.

At ingested scale `reports/decompositions.json` is **not** rewritten as a
release step; the committed file stays the declared pre-scale snapshot
(TRIAGE-v0.11 §1.6).

## Two citations found stale and deliberately left alone

Both live inside sealed preregistration artifacts, and a stale citation
inside a seal is a fact about the seal:
`experiments/plain_input_prereg.json:127` quotes SPEC lines `:159-173` inside
a frozen `clause_verbatim` (today's correct range is `:401-412`), and
`experiments/session_ledger_prereg.json:219` says "§7's normative table" where
the normative line-grammar table is §5. The **eighteen** wrong line-number
citations that were fixable — all in documentation — were fixed at
`[TRIAGE-V25-LOWS]`, with the finding worth keeping: every section-,
paragraph- and anchor-form citation into the SPEC verified **correct**. What
rots is the citation that names a line.

## Reproduce

From a fresh clone at this tag:

```
# 1. the checkers this cycle added or exercised
PYTHONIOENCODING=utf-8 python scripts/check_symbol_census.py
PYTHONIOENCODING=utf-8 python scripts/check_house_rules_receipts.py

# 2. read the registered run's verdicts off the committed ledger
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/house_rules_verdicts.json',encoding='utf-8')); \
    print(d['gate_greens']); print(d['gate_reds']); \
    print(d['voiding_sentence']['fired']); \
    print(d['result_gates']['R-H1']['caveat'])"

# 3. the demand census, which gates nothing
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('experiments/house_rules_verdicts.json',encoding='utf-8')); \
    r=d['result_gates']['R-H2']; \
    print(r['parse_as_declarations'], 'of', r['population_size']); \
    print(r['precommitted_reading'])"

# 4. the parser disclosure, in the committed report
PYTHONIOENCODING=utf-8 python -c "import json; \
    d=json.load(open('reports/signature_matches.json',encoding='utf-8')); \
    print(list(d['parse_rewrites'])[:5])"

# 5. the superseded run, retained and labelled
cat experiments/superseded/README-house-rules-run1.md
```

`scripts/run_house_rules_gates.py` is the registered-run writer. It refuses
four ways before it scores anything — an existing output path (twice:
eagerly, and structurally through `open(..., "x")`), a dirty tree, a tip the
sealed H-PRE commit is not a **strict** ancestor of, and a `frozen` pin whose
digest has moved — so re-running it against the committed artifacts is
expected to refuse. Read the committed ledgers instead. `--allow-dirty` is a
rehearsal hatch that forces `registered_before_the_run: false`, on which every
§8 sentence gates: it can print a table and it can license nothing.

`registered_before_the_run` is **true by git ancestry**, not by the
operator's word: `git merge-base --is-ancestor 7a47a8a 32d505a` returns true
and the relation is **strict** (a same-commit relation would not have
counted), all seven frozen pins were re-digested and unmoved twice — by the
runner before scoring and by the second program after — and
`git status --porcelain` was clean.

## The cold reading at this rotation

`[COLD-RUN2-V25]` — **NOT YET LANDED in this document.** The registry was
re-sealed last, after every other artifact this rotation commits, and the
~1 h live cold re-read runs against the committed registry in v0.23's order.
This placeholder is resolved with the re-read's partition over 24 kinds, its
R-C verdict, and the commit that carries it — or the notes refuse the
sentence. The v0.25 predecessor is on the record for comparison: at
`11d62b8` the partition was **1 SURVIVES / 12 NEEDS-PROGRAM / 9 UNTESTED**
over 22 kinds with all eleven gates green, byte-stable against v0.24's.

A SURVIVES verdict travels with its scope, and the v0.24 standing rule
applies to whatever partition lands here: the cold harness is a clean-PATH
subprocess, deliberately weaker than a container — `%USERPROFILE%`, the
registry, ambient DLL paths and the harness's own interpreter are not
excluded.

## The suite at the tip

`[SUITE-GATE-V25]` — **NOT YET RUN at this rotation.** The full
`unittest discover -s tests` on the frozen tip is the tag's gate, and the
skill forbids tagging while it is PARTIAL. This placeholder is resolved
before the tag with the run's counts, its wall-clock, and its retained
receipts under `reports/test_gate_v025/`, exactly as `[SUITE-GATE-V24]` was
closed with 2,986 tests OK (skipped=5), 22,504.4 s (6 h 15 m) at `d1e37b9` —
or the notes refuse the sentence and the tag waits.

Plan the run from the measured cost, not from folklore: v0.24's gate took
four launches to get a verdict, and this cycle adds `tests/test_house_rules_*`
(132 tests in the run file alone) on top of that base.

One gate state is already known and disclosed rather than discovered by the
run: `tests/test_cold_receipt.py`'s
`test_the_seal_and_counts_recompute_from_the_committed_tree` was **red** from
`32d505a` until the rotation's CR-P0 re-seal, because the grammar repair
moved `line_grammar_digest` again. That is the same drift already recorded,
and the re-seal is the commit that closes it.
