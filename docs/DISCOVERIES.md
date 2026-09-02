# Discoveries

Cross-discipline identities found *mechanically* by the matchers — parked
here as they are identified, for separate analysis. Each entry: the claim in
plain language, the structural evidence, and status. Grows over time; the
ledger of record is `reports/signature_matches.json` and
`reports/specializations.json`.

Statuses: **exact** (typed twin or reciprocal equivalence in the corpus),
**family** (twin after sign/parameter absorption), **shape** (structure
matches, slot roles differ), **specialization** (general→specific with
bindings), **near-miss** (informative failure, kept deliberately).

---

## A containment gate whose mutants are prose is a gate that has never been run (2026-09-02)

**Claim.** HOUSE RULES' B3 asks that ">=30 seeded mutants attempt to move an
admitted symbol into a rendered answer's evidence, a written session
document, a journal, or a library path" and that "100% are stopped by the
shipped machinery or the checker". The 32 mutants sealed at H-PRE are
**descriptions of attempts**, not executable ones, and nothing in this
repository executes one. What the gate can therefore observe is that a
detector each mutant was mapped to — by an association authored in the
runner, not sealed with the mutant — fires on live material. Run 1 reported
"32/32 stopped" without that distinction, and the review found two of the
detectors could not have failed: one planted a name in a temporary directory
and found it again (carrying seven mutants), the other asserted that the
checker module holds no string constant equal to the run's output paths,
which is true of every module that never mentions them.

**Evidence.** `experiments/superseded/house_rules_verdicts.run1.json` (run 1,
`2ac8c9f`) against `experiments/house_rules_verdicts.json` (run 2), whose B3
row now leads with `mutants_are_descriptions_not_executions` and publishes
the sealed `stopper_mechanism` beside each mapped detector, a keyword table
matching detector mechanism CLASSES against those sentences, and per-detector
coverage counts. Two detectors repaired or retired, three mutants re-pointed;
32/32 stopped by a live detector at the same unchanged floor of 30.

**Status:** near-miss, kept deliberately. **What a containment gate must be
next time:** the mutants must be EXECUTABLE — a program that performs the
attempt against the live harness and returns what happened — and the seal
must carry a machine-readable detector id per mutant rather than a prose
sentence a later runner is free to interpret. Anything short of that measures
that a detector fires, which is a fact about the detector.

---

## A blind control on nineteen rows could not have voided anything (2026-09-02)

**Claim.** HOUSE RULES' B9 fits a surface-only admitter on half the
declaration corpus and voids the capability if it agrees with the checker on
the other half by more than ten points above that half's majority-class rate.
On the sealed corpus the entire registered family of 95 threshold rules tops
out at **0.736842** on the nineteen-row scored half, against a void threshold
of **0.784211**. **No member could have fired.** The fitted rule
`line_length:eq:28` additionally predicts REFUSED for every scored row, so
its reported agreement of 0.684211 equals the majority-class rate by
arithmetic and not by signal. A richer family authored after the score —
closed intervals and two-feature conjunctions over the same three allowed
inputs — reaches **0.789474** on the scored half, above the threshold, but
only when the rule is chosen by the half it is scored on; fitted honestly on
the fit half with a tie-break declared in advance it returns 0.684211 and
does not fire.

**Evidence.** `experiments/house_rules_verdicts.json`,
`construction_gate.B9`: `family_ceiling_on_scored_half`,
`fitted_rule_degenerates_on_scored_half`, `richer_family.fit_half_selected`,
`richer_family.ceiling_on_scored_half`. Prereg amendment
`amd-2026-09-02-b9-families`. R-H1's `caveat` field carries the finding
beside the licensed sentence.

**Status:** near-miss, kept deliberately. A control that cannot fire measures
nothing, and a nineteen-row held-out half moves 0.0526 per row. The next
slice to use a blind control must register the family, its tie-break and its
threshold before the run, and must check the family's own ceiling against the
threshold at registration time — which is a one-line computation that would
have caught this before any score existed.

---

## The system published an admitted symbol in its own grammar example (2026-09-02)

**Claim.** From `c87b0ca` through H-P1's first registered run, the `declare`
row of `serve_chat.LINE_GRAMMAR` carried, as its example line, the ADMITTED
fixture symbol of `hr-fx-s1-t01` — and so did
`experiments/session_p1_command_bound.json`, the generated artifact that
echoes the grammar, and the capability sheet served from it. That is b3-m08's
sealed vector verbatim ("the capability sheet is a committed generated
artifact inside `write_stage.working_tree_digest`... B5's sweep finds the
name") present in the committed tree while B3 scored b3-m08 STOPPED. B5 did
not see it because B5 is scoped to the run's OUTPUT tree, and the digest
detector b3-m08 was mapped to cannot see a name that is already committed.
**The adversarial review found it; no gate did.**

**Evidence.** `scripts/serve_chat.py:368` at `2ac8c9f`, and
`experiments/session_p1_command_bound.json:113` at the same tip. Repaired at
H-P1-FIX-FREEZE: the example is a placeholder verified absent from the
census, the schema and the whole fixture corpus, the generated artifact is
regenerated by its writer, and the `line_grammar_digest` moves with it. The
standing detector is `grammar_example_names`, which sweeps the served grammar
rows and their generated echo on every run and now carries b3-m08; a test
drives it red by planting a derived name in a grammar row.

**Status:** exact. The general shape is worth carrying: **an example is a
value, and a value drawn from a sealed corpus inherits that corpus's
prohibitions.** Every generated artifact that echoes an authored example is a
copy of that value, and a containment gate scoped to a run's outputs will
never look at any of them.

---

## The host bound the exact request and refused the tool in the same breath (2026-08-31)

**Claim.** codex-cli 0.150.1's tool wire and its tool policy are separate
machines with opposite answers. Given the one emitted `request_user_input`
function-call item, the host constructed a `function_call_output` whose
`call_id` is the exact pending verifier request id — the binding half of B7
worked unmodified — while the output payload it bound was its own router's
refusal, "request_user_input is unavailable in Default mode." The
declaration's Plan-mode caveat (captured at U-P1) governs execution, not
advertisement: the host advertises in every mode a tool it will execute in
one.

**Evidence.** `reports/b7-codex-session.log` (rollout extract);
`experiments/protocol_uptake_b7.json` verdict RED with the scripted
self-check green, so the server half is excluded as the cause. Second
independent mechanism in the same run: the host replayed its `function_call`
item inside the follow-up input (store:false), the exact wire shape ¶AMD-3
recorded in advance as its one risk.

**Status.** near-miss, kept deliberately. R-U2 unlicensed; the recorded next
probes (Plan-mode router behavior; a registered test for admitting the
echoed item) are in the B7 commit, not taken this cycle.

## An audit that names the forbidden name carries it (2026-08-31)

**Claim.** U-P0's invariant (i) — the two U-PRE-deleted input fields appear
nowhere in the sealed artifacts — cannot be enforced by code that searches
for those field names, because the enforcing code then contains the names
and trips its own check. The honest form is positive: every signal id must
be a survivor, and the checker derives the deleted names from the audit
artifact at run time.

**Evidence.** `scripts/build_protocol_corpus.py` (positive survivor check),
`scripts/check_protocol_regeneration.py` (names derived from
`experiments/protocol_uptake_upre.json`); the first drafts tripped invariant
(i) on themselves before the rewrite.

**Status.** near-miss (instrument), kept deliberately — the same shape as
v0.22's removal arm that could not go red: an enforcement that contains its
own violation.

## 0/220 rendered-answer digest regressions in the recorded window (2026-08-29)

**Claim.** Replaying the 220 recorded answering turns (`160 solved + 60
found`) through today's program yields byte-identical rendered-answer
SHA-256 digests. That is a measured zero, not a proof that answers cannot
regress.

**Evidence.** `experiments/no_flip_census.json`: digest_matches 220,
digest_mismatches 0, answers_lost 0. Exact plants 2/2, shape-only 0/2,
always-changed 2/2 plus 220/220 false positives on identical self-pairs.
B1–B6 FIRES. Live pins that moved: `rendering_module_digests`,
`capability_sheet_digest`. MACs unverified.

**Status.** Rider R-NF outcome. Detector retained for the erratum lane's
future window.

## A served voice is not one instrument just because both outputs are English (2026-08-28)

**Claim.** ECHO's proposed population contains two disjoint statement
universes with different readers and different adjudicators. The second voice
has a code-disjoint reader and external Lean checker; the native voice has
neither. Calling both surfaces “the voice” hid the construction boundary.

**Evidence.** `experiments/echo_population_audit.json`: native **8,584**,
second **2,313**, statement-id overlap **0**; B1 FIRES, B3 MISSES, B4 MISSES.
The second reader/renderer module intersection is empty and its checker probe
passes. The native reader and renderer share five modules, including
`realize_term.py` and `match_signatures.py`, and no external probe exists.

**Status.** Construction stop before pilot: 0/50 reserve and 0/500 registered
items rendered. No collision result exists to license GUEST AXIOM's ask arm.
Unpark only by adding the missing native instruments or by a dated scope
amendment that retracts the all-committed-speaking-set claim.

## The ingested library is effectively nameless — 417 of 12,777 statements can be named specifically enough to ask for (2026-08-27)

**Claim.** Reachability by name, not by title, is a property the whole
architecture assumed and never measured. Measured now: of 12,777 statements,
only **417 (3.26%)** carry a handle from either title-free index specific enough
for a person to type and reach them by — **263 (2.06%)** via the per-node
glossary (S-LEX), **306 (2.39%)** via the call-head inventory (S-INV). The
other **12,360** carry none.

**Evidence.** `experiments/handles_census.json`. The cause is measured:
**12,514 `lean_workbook` statements were ingested in bulk and carry nine
distinct glossary tokens between all of them**, six of which each blanket more
than 12,200 statements — so the specificity bound `K = 128` excludes them all,
and not one of the 12,514 has a specific S-LEX handle. No re-freeze of K rescues
the bulk: coverage of the bulk caps at **302 statements** at every K forever
(302 at K=302, at K=1024, at K=4096). The typable union is invariant at 417 for
all K in [80, 218].

**Status.** The design's §9 stop clause **fired**: *the ingested library is
effectively nameless; the naming layer must be built, not indexed.* No
capability sentence, no handle table, no Q60. Hostile review reproduced every
number to the digit, including row-level agreement on all 12,777 one-step
classifications; two instrument defects (a false writer attestation, a hash-seed
tie-order) were caught and fixed with no headline number moved.

## The library can compute far more than anyone can name to ask for — 125 of 9,048 consumable statements are nameable (2026-08-27)

**Claim.** Two censuses overlaid give the cycle's sharpest reading. Of the
**9,048** statements (70.8%) whose committed form has the shape of a one-step
consumer — a hypothesis it could discharge, a bound it could take — only **125**
carry a specific typable handle. The mass the program can *work on* and the mass
a person can *reach* are almost disjoint.

**Evidence.** `experiments/onestep_census.json`, `cross_census_reading` (against
`experiments/handles_census.json` at K = 128). This is an observation about two
committed censuses, not a verdict on either lane: shape is a parse question and
no prover ran, so no statement is claimed *consumable*, only consumer-*shaped*;
the 125 *carry* handles, and nothing is claimed reachable in service.

**Status.** R1's statement-side floor (200) is met 45× over; its question-side
half is DEFERRED with Q60 unsealed. The gap between computable and nameable is
what the v0.23 course's GUEST AXIOM approaches from the person's side.

## A receipt is cold-recheckable only when its adjudicator is not the program — and one executed case is all this measures (2026-08-27)

**Claim, scoped to what ran.** Across 19 receipt kinds this repository emits,
**one** was re-checked with its producer deleted. What separated it was not
richer evidence but a third party holding the decision: its verdict is an exit
code from a binary `leanprover` published, pinned by a digest of the executing
bytes. Ten kinds read NEEDS-PROGRAM under a two-limb removal arm. This is
**one executed positive case**, not a law — the generalization is the direction
the evidence points, and the sample is one.

**Evidence.** `cold/census_run2.json`. The surviving kind, the C-E3 probe
receipts, carries a probe template and a checker digest; steps 1–3 of its
recheck need no program and no checker, and step 4 needs the pinned third-party
binary and nothing of this repository.

**The negative half is only as strong as its arm, and the first arm was
broken.** Run 1 confirmed nine kinds NEEDS-PROGRAM by running
`python -S -I -c "import <module>"` with the tree renamed away. `-I` implies
`-E`, so `PYTHONPATH` was discarded and the module was never findable either
way: the check failed identically with the program PRESENT. Amendment 2 runs
both limbs with identical argv and environment, differing only in whether
`scripts/` exists, and requires the with-program limb to SUCCEED. Ten kinds now
pass that stricter pair. A confirmation that cannot go red is not a
confirmation, and the first version of this entry claimed one.

**The sharpest instance is the one that changed verdict.**
`retraction_radius:certify` carries an explicit `recheck_command` — the most
self-describing receipt in the tree. Amendment 2 removes what the descriptor
*runs* (`scripts/radius_recheck.py`) rather than what *wrote* the receipt, and
the with-program positive control fails: `radius_recheck` cannot import
`jsonschema`, which no manifest here pins. With the program fully present the
procedure still cannot run. So the kind reads **UNTESTED with `jsonschema`
named**, not NEEDS-PROGRAM. A receipt can be blocked by the world its program
was maintained in rather than by the program, and only a positive control can
tell the two apart.

**The corollary that cost the most to learn.** The reconstruction rule for the
one surviving kind is only HALF recorded in its own artifact: the positive probe
template appears 25 times, the negation glyph **zero** times. The negative
template, the trailing newline, and the fact that the digest covers the LF form
rather than the CRLF bytes handed to the compiler all live in the writer's
source and nowhere in the receipt. A kind can be genuinely cold-recheckable and
still not be self-describing (`cold/reconstruction_rule.json`).

**Status:** measured. Instrument controls green over their **one-kind**
denominator — tamper 3/3 FAIL on three distinct signatures, omission failing
loud, sham survivors 0 (structurally, see ANALYSIS), and 0 of 200 scrambled
bundles passing.

---

## A metric that counts successes cannot see a correct refusal (2026-08-26)

**Claim.** A capability-blind control that scores *accepted answers given*
will beat any instrument whose competence includes **declining**, because
declining scores zero and the blind arm cannot decline. The gap it reports is
not a measurement of the instrument; it is a measurement of the metric's
alphabet.

**Evidence.** `experiments/plain_input_run.json` `gates.G5`. A pinned small
model, selecting by index from exactly-enumerated candidate lists, made **17**
verified selections over thirty sealed questions. A seeded uniform draw over
the identical lists made **22**. The registered collapse rule required the
blind arm to score at most **half** the proposer's — **≤ 8.5** — so G5 reads
**RED** and the seat ships empty.

**And the draw was typical, not lucky**: the run publishes the blind arm's own
analytic expectation, **Σ verified/candidates per question = 20.62**, beside
the observed 22.

**The mechanism.** The model answered `NONE` on **six** questions — `g1-08`,
`g1-22`, `g1-26`, `g1-27`, `g1-29`, `g1-30` — and **every one of the six was a
correct refusal**, independently confirmed by review. Every one of those six
questions had verified candidates available, and the blind arm, whose output
alphabet contains no `NONE`, took them. On the **nine questions authored to
exhaust**, the model selected for **zero** and the blind arm selected a
verified candidate for **five**. *The control rewards, in its blind arm,
exactly the behaviour the design calls inventing.*

**A second defect in the same number, and it is the transferable one.** The
frozen chance rate was `1/8 = 0.125`, the reciprocal of the candidate limit.
The measured expectation is **0.687** — and the clause is therefore
**arithmetically unsatisfiable**. It reads *blind ≤ proposer ÷ 2*; the
proposer cannot lower the blind arm's score, so the only way to satisfy it is
to raise its own, and against a blind expectation of **20.62** that needs
**≥ 41.24 verified selections out of thirty questions** — of which only **24**
yield a verified candidate at all and the sealed ceiling is **21**. **No
proposer, however good, could have passed this clause.** Same disease as
C-E1's 0.99 flip floor one cycle earlier, and therefore the **second
incident** of the rule written to prevent it.

**Nothing was rewritten.** The rule was frozen before the proposer existed and
was scored as frozen: *"A rule rewritten because its instrument surprised its
author is not a preregistration."* And the red survives excluding all nine
exhaust-authored questions — **17 against 17**, still far above 8.5.

**The transferable rule: score the branch outcome against the question's
disposition, not the count of accepted answers.** Then declining an
unanswerable question counts as success for both arms, and the blind arm's
inability to decline shows up as the incapacity it is. Status: **measured**.
Evidence: `experiments/plain_input_run.json`,
`experiments/plain_input_corpus_seal.json` (`denominators.exhaust_authored`).

## An obligation built from one reading compares that reading with itself (2026-08-26)

**Claim.** A verification obligation of the form *"what the machinery computes
agrees with what the statement says"* has **no content** when both halves are
produced by the same front-end. It is `P ↔ P`, and a checker will discharge it
every time — cleanly, with a real receipt, about nothing.

**Evidence.** `experiments/witness_pilot.json`. Six obligations drawn by a
recomputable rule from a 37-candidate census; **0 discharged**, all six
`rejected_trivial` by the design's own self-comparison clause. The committed
parser emits left-nested **binary** `+` and `*` nodes, so the evaluator's
regrouping has nothing to regroup, and inside the linear fragment the two
readings are the identical tree.

**The counterfactual is the finding, not the zero.** The same six obligations
were handed to the pinned checker with the triviality test **switched off**:
**accepted 6 of 6**. An instrument built without that one clause would have
published six discharged agreement lemmas and reported a capability.

**And a related receipt was clean about the wrong statement.** Review found
one obligation carrying a free variable the sampler never bound; Lean's
`autoImplicit` silently prepended a binder, and `omega` returned exit 0 with
no diagnostic **on a strictly stronger proposition than the row it was filed
under**. Under `set_option autoImplicit false` the same source errors with
*unknown identifier*. Fixed as a typed refusal, `autoImplicit false` in every
preamble; **all six verdicts unchanged**.

**The transferable rule: an independent second reading is a construction
prerequisite, not a residual risk to price later.** The draft priced
single-front-end construction as a residual and put the second reading outside
the slice; the pilot says that is backwards. And fragment growth does not
substitute — the divergent class exists and is reachable (25 statements, 18 of
them compiling, against **0 n-ary nodes in 86,547 walked**) but is
**non-linear**, so reaching it would give the obligation content while leaving
it a comparison of one parse with itself. Status: **measured, and the lane
stopped**. Evidence: `experiments/witness_pilot.json`,
`experiments/witness_fragment_census.json`.

## A recorded conversation can carry its own premises, and the fence is what proves it (2026-08-26)

**Claim.** *Citing* the assumptions an answer consumed is only evidence if the
citation is **read-derived** and if uncited assumptions provably **cannot**
move the answer. Without the second half, a per-turn citation list is a hash
of the transcript wearing the word "because".

**Evidence.** `experiments/session_ledger_run4.json`, over a sealed corpus of
**60 sessions, 410 turns, 130 binding-dependent**. Mutating a **cited**
assumption changed the answer digest or produced a typed refusal on **58 of
58** binding-dependent turns in half B — **30 of them by refusing outright**.
Mutating a **live but uncited** assumption moved nothing: **0 flips of 42**.
Sixty **sham** assumptions, injected to see whether mere presence nudges
anything: **0 flips of 60**. A single flip in either of the last two would
have fired the frozen voiding sentence and declared the capability void for
the cycle.

**And the fence went red first, for a real reason.** On half B's first
execution, B10 — *a turn citing nothing must render byte-identically to the
same line served statelessly* — read **RED on ten turns**, all of them
`retract a999`: the refusal for an unheld id rendered differently depending on
whether a ledger was attached, which is the ledger's *existence* reaching an
answer that consumed nothing. Repaired under the suite-gate precedent, with
all four runs retained and the red published.

**And the citing surface is the recorder, not the prompt.** `harness.main()`
attaches no `AssumptionSet`; only `scripts/session_recorder.py` does. A person
typing at the CLI sees `suppose` and `retract` render and sees no answer cite
anything, because nothing is declared. The claim lives in the run artifact and
in `tests/test_session_ledger.py`, which is what the design asked for and is
not an acceptance a newcomer can try.

**What it does not claim, said where the claim is made.** Sessions are
**reproducible, not correct** — a wrong answer replays as faithfully as a
right one. B12's two sides descend from the same in-memory read barrier, so
"corroborated" is not "two independent instruments". B13's auditor is the
implementer, and all twenty drawn cases are the same easy shape. B1's ordering
clause **MISSED** and is published unreinterpreted. Status: **measured and
served**. Evidence: `experiments/session_ledger_run4.json`,
`experiments/session_corpus_seal.json`.

## A control that dies on a case has not passed that case (2026-08-26)

**Claim.** Two consecutive cycles of adversarial review, across four
independent lanes, found **zero wrong digests** and a recurring class of
defect underneath: **green checks incapable of failing.** v0.20 catalogued
four. v0.21, having written the lesson down, produced three more — one of them
inside a test file added to catch exactly this.

**Evidence.**

- **A needle appended to its own haystack.** A test read
  `assertIn("byte-frozen", field.lower() + " byte-frozen")` and therefore
  passed on any field content, including empty. Removing the append made it
  fail, because the field does not contain that phrase. It was in the suite
  written for the C-E3 rider — the branch that quotes the standing review
  question.
- **A verdict green on zero.** B2 requires unmutated replay to reproduce
  `answer_bytes_digest` for **every** turn the seal records. Its verdict
  counted per-turn divergences, and a `stale-environment` refusal produces
  none — so when a mid-review edit moved a pinned digest and every replay
  refused, **B2 reported GREEN having reproduced 0 of 410 turns**. *"Every
  turn" means every turn, and zero is not every.*
- **A tamper control with one arm run twice.** B8's two registered arms —
  rewrite a turn, with and without repairing the digest chain — **both leave
  the original MACs in place**, so both are caught by the same signature
  mismatch. The obvious forgery, an adversary who holds the file and re-signs
  every record under a ring they minted, had never been run; when a reviewer
  ran it the scorer **crashed** out of `session_keys.derive`. Two arms added,
  both **20/20**, both caught by a key the tamperer does not hold — a refusal
  to verify now scores as a detection, which is the house grammar rather than
  a convenience.

**And the discipline applied upward.** The orchestrator's own forward design
was **falsified twice by review before it landed** — once for claiming ground
the repository already occupies, once for citing producers that do not exist.
Status: **standing review question**, now written into gates rather than
restated as an anecdote. Evidence:
`experiments/conformance_ce3_supplement.json`,
`experiments/session_ledger_run4.json` (`construction_gate.B8`),
`reports/design-direction-v0.22.json` (`selection.selected`).

## A restored clause moved the denominator, not the numerator (2026-08-25)

**Claim.** When a control that scores "did the gate notice this break?"
inherits its mutation idea from an ancestor **without the ancestor's
verify-the-break-was-real clause**, its shortfall is not evidence about the
gate at all. It is evidence that some of its "breaks" were never breaks.

**Evidence.** v0.19's `drop_ascription` read **0.90 against a 0.90 floor** and
was reported as five near-misses the identity gate failed to catch. v0.20's
re-specified control restored the clause — construct the mutation, elaborate
the mutated **term** first, discard any mutation whose term did not change,
count the discards — and pre-registered a point prediction of **"45 of 50,
exactly v0.19's reading"**. Measured: **45 detected of 45 scored, with 5
discarded as non-mutations** (`experiments/foreign_voice_rate2.json`,
`c_v4_prime.per_class.drop_ascription`; `c_v4_prime.point_prediction` records
`held: false`).

**The numerator held exactly. The denominator moved.** So the earlier 0.90 was
not a gate missing five things — it was **five mutations that were never
mutations**, filling the denominator of a control about near-misses with
sentences that were not near-misses. The prediction was made by the same
person who restored the clause, and it was the clause that falsified it.

**The transferable rule, stated for any future ported control: port the
discard rule first.** It is usually the part that was expensive to learn and
the part that looks optional. Status: **measured**. Evidence:
`experiments/foreign_voice_rate2.json`, `experiments/foreign_voice_rate.json`
(`c_v4`, committed as it read and not re-scored).

## A green assertion that could not have gone red is not evidence (2026-08-25)

**Claim.** Two independent adversarial reviews and one merge, across two
unrelated lanes in one cycle, found **zero wrong digests** and a recurring
class of defect underneath them: **gates true in substance, enforced by
assertions that were incapable of failing.** The defect is not in what the
checks concluded — every conclusion held on re-derivation — but in whether
anything could have told the difference.

**Evidence**, five instances, each from a different mechanism:

- A gate asserting *"no cross-kind mutation record appears in these two
  classes"* computed each record's kind from a **dict literal keyed by class
  name**, so it would have read true whatever the mutations touched — and a
  cross-kind record is the one thing that gate exists to find. The real kind
  was already being returned by the selector and then discarded.
- A test comparing *"the 85 unchanged sealed renderings"* read the seal **at
  HEAD** and compared it to the same file in a clean worktree: a file compared
  to itself. It now locates the re-seal commit, reads its **parent's** blob,
  and is **proven** falsifiable by perturbing one of the 85.
- A pin file's **prose** carried a reader's full authority while its machine
  check covered exactly one field — so a freeze list shipped a **correct
  digest beside a false sentence** (*"Still 65fead2f…"* when the file was
  already `f5b2abba…`), and only a human ever reads the sentence.
- A claimed derivation was **enforced by nobody**: the replay script refused
  on the branch tip and no collected test ever performed the replay, so the
  strongest claim in the pin file rested on a program that could not run.
- A test asserted *"the repository as it stands is dark"* — true the day it
  was written, and destined to go **red for the system working**. Re-aimed at
  consistency: the served line appears exactly when the arming read says it
  should, on both branches.

**Consequence, adopted as a standing review question rather than a cycle's
anecdote.** Asking *"is this assertion true?"* is not enough; the question is
*"could this assertion have been false?"* — and where the answer is no, the
green is decoration. The next cycle's instrument turns it into gate text: a
**self-comparison obligation must be rejected as trivial, and a single
discharge voids the instrument**. Status: **measured**. Evidence: commits
`c0c3e94`, `bd08f45`, `416e97c`; `experiments/ANALYSIS.md`, "Adversarial
review of the v0.20 voice lane".

## A control whose floor no correct instrument could meet (2026-08-25)

**Claim** (narrowed 2026-08-25 after adversarial review; the earlier wording
claimed more than the run can support). C-E1, the conformance lane's
perturbation control, froze a floor of *"≥ 99% of skeleton-changing mutations
must flip at least one point verdict"*. The registered run measured **0.650
over 1,027 surviving mutations** and the control voided every
`NO_COUNTEREXAMPLE_FOUND` in the run. **Some mutation classes over `Nat` are
structurally unflippable, so the floor as written cannot be met by a correct
sampler *on those*.** What the run cannot do is say how much of the 0.650 is
that and how much is the sampler missing points it should have found — and it
found at least one of the latter.

**Evidence, and its limit.** A skeleton-changing mutation need not be
falsifiable on the *declared carrier*. Two of the twelve non-flipping
witnesses in `experiments/conformance_run.json` are genuine:
`leanworkbook.skel.lean_workbook_10012`'s `negate_a_coefficient` turns
`>= 9*x/4` into `>= -9*x/4`, and under the declared reading a negative
**numeral** evaluates while truncating division takes `1/4` to `0`, so the
right side is `0` and the left is a sum of `Nat` quantities — true at every
point that exists. `lean_workbook_10039`'s `negate_a_coefficient` (`60` →
`-60`) is the same shape. No point set can flip either.

**But `lean_workbook_10087` is a sampler miss, and it is in the same twelve.**
Its source is `(a-b)^2 + (b-c)^2 + (c-a)^2 >= 0`, mutated to `>= 1`. That is
flippable, at every point where `a = b = c`: the left side is `0`, and `0 >= 0`
holds where `0 >= 1` does not. The sampler drew **73 admitted points** and hit
no such point. That is precisely the failure the floor exists to catch, sitting
in the list published as evidence that the floor was unmeetable.

**So the honest partition is unmeasured.** The run reports one number, 0.650,
over a population containing both structurally-unflippable mutations and
sampler misses, and it has no instrument that separates them. The claim above
is stated over the classes where the structural argument is exhibited, and not
over the rate.

**Why it is the same lesson one level up.** v0.19's C-V4 inherited C-R2's
mutation idea without the clause that made it sound, and `drop_group`'s 0.80
was scored against a denominator that had never been cleaned. C-E1 ported
that discard rule — it discards mutations whose canonical *skeleton* did not
move, and counted the discards (0 on this tree). What it also needed, and
did not have, is a second clause: **discard mutations that cannot move a
point verdict on the carrier.** The transferable rule is now two sentences
rather than one: *port the discard rule first, and check that what survives
it is capable of the change you are about to require.*

**Status: near-miss, kept deliberately.** Recorded rather than repaired —
fixing a control after reading its number is the chase the design's §8
forbids. The corrected control belongs to its own registration, and it now
owes two clauses rather than one: discard mutations that cannot move a point
verdict on the carrier, **and** report the rate over a population that has
been partitioned, so a sampler miss can never again be published as a
specification defect.

## The declared domain spends the budget before the guard sees it (2026-08-25)

**Claim.** In the conformance lane, **78% of the sampling budget is consumed
by the declared carrier, not by the statements' guards.** Of 691,000
candidate points offered to the coupled guards in E0f's pilot, **539,382 were
rejected because they were not `Nat`** and only **51,791 by the guards
themselves**.

**Evidence.** `experiments/conformance_admission_pilot.json`. The sampler
draws from a rational pool with negatives; the `lean_workbook` class row
declares `Nat` on Correction 4's ground. The two gates are reported
separately, and that is the only reason this was visible — summed into one
admission number it would have been invisible.

**Consequence** (rewritten 2026-08-25: the original rested on an inverted
reading of a field, and the correction is worth more than the sentence it
replaces). The finding is the **split**, and the split alone: of every 1,000
candidate points offered, roughly 780 are spent before the statement's own
hypothesis is ever consulted. That is a property of the sampler's pool against
the schema's declared carrier, measured directly in the pilot, and it is why a
carrier-matched sampler is the named successor.

What this entry originally added — *"the effective budget per statement is far
below M = 1,000: the registered run's median admitted count across its 775
counterexamples is two"* — is **withdrawn**. `scripts/conform.py:497` breaks
out of the point loop on the first counterexample, so on a NONCONFORMANT
record `points_admitted` counts admitted points *up to and including the
falsifying one*. A median of two means half of those statements were falsified
within two admitted points; it is a measure of how **early** falsification
happened and carries no information about how many points the statement could
have been offered. Quoted as evidence of a thin budget it said the opposite of
what it meant, and it was never needed: the pilot's 539,382-to-51,791 split is
the whole finding on its own.

The successor was not applied mid-cycle because the sampler is E7-frozen and
its own pilot had already been read.

**Status: near-miss, kept deliberately.**


- **The gate's blind spot has a number now, and the number voided the gate
  (v0.19, C-V4, measured).**  The foreign-voice gate certifies a rendering
  by elaborating the English through a pinned external checker and
  comparing the elaborated term's digest to the source's.  The design
  wrote the limit of that method into its §3.2 as the claim's *shape*
  rather than as a caveat: identity holds **up to what elaboration erases
  and what the preamble rule regenerates**, and any rendering error
  confined to either is invisible.  C-V4 was built to put a number under
  that sentence — mutate the rendered English one mechanical step, invert,
  elaborate, and require the digest to move.  Four classes behave:
  `swap_binder` 1.00 (50/50), `shift_group` 1.00 (49/49),
  `drop_ascription` 0.90 (45/50).  The fifth, **`drop_group`, measures
  0.80 against a 0.90 floor frozen before the instrument existed** —
  **deleting a semantically redundant bracket changes the sentence and not
  the term** — and its voiding sentence voids the whole reading.  B1 had
  measured 1.0 (2,313 of 2,313); the void outranks it, and the consequence
  was taken rather than argued with: **the foreign `in words` line is not
  wired**, because serving under a voided certification is what the
  voiding sentence forbids.  Two readings make this a finding rather than
  a setback.  First, **a control that can only confirm is not a control**,
  and this one demonstrated it can do the other thing to the cycle that
  built it.  Second, the excluded class is the sharper number:
  `drop_binder` measures **0.18** and is **excluded from the voiding pool
  by preregistration** because the preamble rule regenerates exactly what
  it deletes — so 0.18 is not a miss, it is **the measured width of the
  blind spot**, the non-claim made quantitative.  A fresh-eyes review had
  put it at 1 of 24 by hand; the run re-measured rather than freezing a
  threshold at the number this project's own instrument produced.  The
  design's §7 binder-swap prediction was **refuted exactly as
  pre-registered**, at 1.00, in the direction that makes the control
  stronger.  Status: **measured**.  Evidence:
  `experiments/foreign_voice_rate.json` `c_v4`, `verdicts.overall = VOID`.

- **A control inherited without its load-bearing clause is a different
  control (v0.19, construction).**  C-V4 is C-R2's descendant and took
  C-R2's idea — mutate one step, require the identity to break — without
  the clause that makes C-R2 sound: **every mutation is verified to change
  the term BEFORE it is rendered**, with non-mutations discarded and the
  discards counted.  v0.18 discarded 31 that way, and the reason it had to
  was itself a finding: `a < b` and `b < a` share a skeleton, so a
  near-miss set built without verification is full of non-mutations, every
  one "fails" to break identity, and the control voids the gate **for
  behaving correctly**.  C-V4 mutates the rendered English and requires the
  digest to move, but never establishes the mutation *should* have moved
  it — so an unknown share of its `did_not_differ` cases may be
  non-mutations, and `drop_group`'s 0.80 is scored against an uncleaned
  denominator.  The general shape, which is the transferable part: **when
  a control is ported, port its discard rule first** — the discard rule is
  usually the part that was expensive to learn and the part that looks
  optional.  Recorded here rather than used to re-score: the v0.19 run is
  committed as it read, and the re-specified control (C-V4′, with the
  verification clause and its discards counted) is a **new
  preregistration** scheduled in ROADMAP-v0.20 §2, with the foreign wiring
  gated behind it.  Status: **construction**.

- **Two glyphs were half the wall, and the measurement completes (v0.19,
  measured).**  The v0.18 rotation measured, during a design grounding
  pass, that 6,414 of the 10,605 mute statements parse after substituting
  `≥`→`>=` and `≤`→`<=`.  This cycle executed it on the native path and
  the prediction landed exactly: **the parse rate goes 2,172 → 8,586 of
  12,777, from 17.0% to 67.2%**, with 6,414 newly reached against a
  pre-committed floor of 6,000.  Over the newly-reached set the v0.18
  realizer machinery — unchanged — round-trips **6,414 of 6,414
  (1.0000)**, 0 refused and 0 failed.  Three things keep this from being
  the flattering half of a story.  **The set is large and structurally
  narrow**: one corpus, **two** distinct call heads, 4,733 occurrences of
  `≥` and 1,681 of `≤` — numeric inequalities with almost no function
  application in them — so the 1.0000 establishes that the statements two
  glyphs unlock carry heads the lexicon already had, and explicitly **not**
  that the lexicon covers the corpus.  **No floor was pre-committed on the
  round-trip rate, deliberately and in writing beforehand**, because a low
  rate would have been the more interesting finding (reach without voice)
  and a floor is exactly what pressures a lane not to publish it.  And
  **additivity was proven, not asserted**: the witness loaded the retired
  parser out of git in its own interpreter and diffed every rendered line
  over all 12,777 statements — **6,414 gained, 2,170 byte-identical, 0
  changed, 0 lost**.  Status: **measured**.  Evidence:
  `experiments/transliteration_rate.json`,
  `experiments/transliteration_served_diff.json`.

- **A park with numbers is what discharging an instruction looks like
  (v0.19, pattern).**  A maintainer seeded `DESIGN-block-vocabulary` with a
  no-silent-disposal instruction attached.  The v0.19 course could have
  displaced it, or parked it with a paragraph; instead it was **adopted**
  as a bounded roadmap item, scoped to one question its own census raised,
  and measured against **three baselines taken from its own §4 falsifier
  list and preregistered in their own commit before any measurement**.  It
  then lost: retrieval **NOT BEATEN** on both legs at once (block channel
  0.3256 coverage / 0.2059 claim-rate against the keyword channel's 0.9302
  / 0.0294 **on the same rows in the same run**), term layer **NOT
  BEATEN** (6.91× against 8.44×), and the single baseline it beat was
  registered *in advance* as an arithmetic restatement of an existing
  ledger rather than a new finding.  The single question — *is the unified
  dictionary a real object, or two existing objects wearing one id space?*
  — is answered **two existing objects wearing one id space**: unification
  beats grep by 210,248× and a zstd-scan by 9,013× (which the prereg had
  already declared is evidence that an index beats a scan, not evidence for
  unification), and against two indexes carrying **one tag bit** it
  measures **0.9981**.  The transferable pattern is the lifecycle, not the
  outcome: **adopted → built → measured → parked by numbers**.  A park that
  cites a measurement is a decision; a park that cites a preference is
  drift.  One property survives untested for any future unpark — append-only,
  path-independent growth, which no baseline here probed.  Status:
  **measured**.  Evidence: `experiments/address_space_probe.json`;
  `docs/DESIGN-block-vocabulary.md` §3e.

- **Nobody in the authored graph disagrees about notation, and nobody had
  written that down (v0.19, registered negative).**  A one-hour probe swept
  the committed corpora for co-present statements saying the same
  mathematics under two defensible conventions.  Of 2,493 co-present pairs
  with differing canonical forms, 200 fork at a single discriminator
  subterm and **125 are convention-pair candidates — every one of them
  notational** (a glyph, a namespaced-versus-bare head spelling, or where
  somebody put a parenthesis).  **Zero are mathematical convention forks.**
  Inside the 26 hand-authored corpora the negative is unqualified: 1 of 125
  candidates touches an authored corpus and **0 have both members
  authored**.  The three famous clashes named in advance — sign
  conventions, the 0-in-ℕ boundary, 2π placement — return **0, 0, 0**, with
  the detectors proven live by injection so the zero is a reading rather
  than a broken sweep.  Two riders travel with it.  The **125 are a fact
  about an upstream dataset's ingestion**, not about a convention this
  graph holds twice, and the two numbers must never be quoted apart.  And
  the largest candidate class — **98 pairs forking `>=` against `≥`** — is
  the transliteration lane's territory seen from the other side: two probes
  aimed differently found one phenomenon, which is a fact about the corpus
  and not a coincidence of method.  A further first measurement fell out:
  the anonymized-template pass contributed **0** pairs the twin ledger did
  not already carry, out of 1,015 template-sharing pairs — the twin ledger
  is the stronger pool.  Status: **registered negative**.  Evidence:
  `experiments/convention_pairs_probe.json`.

- **Half the mute corpus was an alphabet problem, not a grammar problem
  (v0.19 grounding, measured).**  v0.18 shipped a voice for the 2,172
  parseable terms and named the silence honestly: **10,605 nodes (83.0%)**
  carry a `formal_statement.canonical_ascii` the committed parser cannot
  read.  The v0.19 course proposed treating that mass as a *foreign
  dialect* and borrowing a rendering for it through an external checker.
  Grounding measured the mass before the design committed to it, and the
  premise did not survive: **6,414 of the 10,605 parse under the
  byte-frozen committed parser after substituting exactly two glyphs** —
  `≥`→`>=` and `≤`→`<=`.  That is **50.2% of the whole corpus**, mute for
  want of two rows in an ASCII-only `TOKEN_RE`, not for want of a bridge
  to another language.  What is genuinely foreign is the **4,191-statement
  residue (32.8%)** — quantifiers and typed binders, logical connectives,
  type ascriptions, namespaced heads — of which **2,319 are
  oracle-eligible by outcome** under the frozen interpretation rule (an
  earlier blocklist-derived 1,456 was retired by the design review's
  operational definition); 4,060 of the 4,191 are
  `lean_workbook.ground.v1` and the remaining 131 spread across 23 small
  corpora, led by `logic.boolean_foundations.v1` (20, all of it) and
  `temporal_logic.linear_time.v1` (15, all of it).  Two things make this
  worth recording as a finding rather than a scoping note.  First, the
  measurement **took territory away from the design that proposed it**: a
  loanword pipeline over the transliterable half would have claimed a hard
  result for easy ground, so the 6,414 are excluded from the claim and
  handed to a separate probe on the existing native path.  Second, it
  reframes v0.18's own headline — 17.0% was never a statement about how
  much of this corpus is *structurally* beyond the grammar; roughly half
  of the gap is an encoding boundary that two rows close.  Status:
  **measured** (grounding finding, pre-implementation).  Evidence:
  `docs/DESIGN-foreign-voice.md` §1 Correction 1 — a document **under
  adversarial review at the v0.18 rotation**, so these figures may be
  restated with a dated correction; the claim recorded here is the
  measurement, not the design that quotes it.

- **Five design sentences were corrected by measurement, four of them
  before implementation could act on them (v0.18, construction).**  A
  design is a claim about a tree, and this cycle checked five of them
  rather than building on them.  (1) R1's floor was frozen at **90% of all
  12,777 terms**; only **2,172 (17.0%)** parse at all, so the floor was
  unmeasurable as written — R0 was created as a construction prerequisite
  and R1 rescoped to the parseable denominator (falsified at the *v0.17*
  rotation, before a line existed).  (2) The head calibration — 95 heads,
  39 singletons, a top-10 led by `IMPLIES` and `MEET` — read
  `anonymized_template`, **the wrong field for a cycle rendering
  `canonical_ascii`**; the parseable subset carries **64 heads, 35
  singletons, and neither `IMPLIES` nor `MEET` at all**, and the template
  side re-measured is 95 heads, **30** singletons, `MEET` (22,653) ahead of
  `IMPLIES` (10,202).  (3) C-R1 as written was a scrambled realizer; a
  *two-sided* scramble is a bijection and round-trips near-perfectly, so
  the control had to become one-sided by construction (own entry below).
  (4) `canonicalize` was credited with head aliasing and it does **none** —
  `alias_heads` is a separate pass only the ALIASED match level runs, and
  `MOD` vs `CONCAT` canonicalize to *different* skeletons at this gate's
  level — so alias-class swaps moved from C-R2's **exclusions into its
  set**, which made the control harder on the strength of a correction
  (`72cc7d6`).  (5) The receipt published **one** slot-name map, and the
  surface's numbering (first occurrence in `canonicalize()`'s tree)
  disagrees with `term_skeleton`'s `?N` (from `render_skeleton` over
  `shape_resort()`'s tree) on **110 of 2,170 served terms, 5.07%**; both
  maps are now published with a basis note.  No sentence and no verdict
  moved on that last one — `skeleton()` is invariant under slot renaming —
  **only a reader would have been misled**, on one term in twenty.  The
  transferable part is the shape: every one of the five was cheap to check
  and expensive to discover afterwards, and each is a **dated correction**
  in the design or in `experiments/realization_prereg.json`'s `corrections`
  list rather than a quiet patch.  Status: **construction**.

- **A two-sided scramble is a renaming (v0.18, C-R1, measured).**  A blind
  control that deranges a bijective lexicon must be **one-sided**: emit
  through the deranged table, read back through the **committed** one.  The
  implementation probe proved why the sentence has to be written down.
  Derange the table and then *also* read through that same deranged table
  and you have performed a consistent relabelling — still a bijection, so
  the round trip succeeds near-perfectly (4 of 4 pinned in tests).  Such a
  control would report a **near-perfect scrambled arm and void its own
  reading** under the ≥1% clause, for a reason with nothing to do with
  whether the gate reads the words.  Two corollaries were designed in for
  the same reason.  Grouping words and the slot marker are deliberately
  **untouched** by the scramble, because a scramble that broke
  parenthesisation would fail at the tokenizer and prove nothing about
  stage 2.  Slot indices are deliberately **not** scrambled, because
  `skeleton()` is invariant under slot renaming, so a bijective index
  scramble would pass 100% and measure nothing — only a *non-injective*
  one would move a skeleton, and that is a different control.  And the
  registered run keeps the two-sided run as the **aiming test** (7 of 7),
  which is what demonstrates the scramble breaks word identity rather than
  the grammar; if the two-sided arm had also failed, the contrast would
  have been measuring collateral damage.  Measured: true 0.9991 vs
  scrambled 0.0000, with the failure modes reported **separately** because
  "the control failed" is uninformative — 1,348 scrambled sentences parsed
  perfectly well and meant something else; 822 did not parse.  Status:
  **measured**.  Evidence: `experiments/realization_rate.json` `c_r1`;
  `9879b06`; `tests/test_realize_term.py`.

- **Longest match is a policy; prefix-freeness is the guarantee (v0.18,
  construction).**  The design required an inverter that is table-driven
  "with no operator-precedence or bracketing logic of its own", and
  longest-match decoding looks like enough until you write "plus" beside
  "plus or minus".  The lexicon loader therefore gates two properties that
  make longest match **provably the unique match**: **L1**, no phrase is a
  proper word-prefix of another; **L2**, no phrase word is a word the
  registered numeral pair can emit.  Both are checked constructively over
  the whole table — every ordered pair for L1, and the decode of all 169
  phrases concatenated for the unique-match claim — never sampled.  The
  consequences are recorded in the table itself rather than discovered
  later: `-` and `/` get **no rows**, because `canonicalize()` has already
  rewritten them into `neg` and `inv` and a second row for one glyph would
  break R2b injectivity; `~` gets no row because the frozen `TOKEN_RE` has
  no alternative for it and the row would be unreachable surface; and `neg`
  is *"the opposite of"* rather than *"the negative of"* because
  "negative" is numeral vocabulary and L2 forbids the collision.  The
  general lesson is that a bijection claimed over a phrase table is a claim
  about the *whole table at once*, and the cheap check is structural, not
  per-row.  Status: **construction**.  Evidence:
  `scripts/realization_lexicon.py` L1/L2; `data/realization/lexicon.json`
  `reading_rules`; `ccac853`.  Landed here at the v0.18 rotation to pay a
  recorded debt — this lesson and C-R1's had lived only in a commit body
  and a module docstring.

- **The first machine-ingested record with a voice (v0.18, shipped).**
  12,515 of this corpus's 12,777 nodes are ingestion records whose
  `statement_meaning` is boilerplate, served for five releases under the
  disclaimer *"this text is an ingestion record, not an explanation a
  person wrote"*.  `leanworkbook.ground.lean_workbook_13563` carries the
  `canonical_ascii` `1 + 1 = 2`, and now answers with the disclaimer **and**
  `in words   : two equals one plus one`, with a receipt showing the
  sentence re-parses to `2 = +(1, 1)` — the source skeleton, exactly.  What
  is worth recording is not the sentence, which is trivial, but that the
  system authored a sentence **no person wrote and no bank contained** and
  was still able to prove it.  The disclaimer stays: the ingestion record
  is still an ingestion record, and the realized line makes a claim about
  the *formal statement*, not about the prose.  R3 keeps the boundary
  honest by making refusal silent — a term that does not parse, an
  uncovered head, or a failed re-parse produces **no line at all**, not an
  error string and not a placeholder.  Status: **shipped**.  Evidence:
  `scripts/answer.py`; `experiments/realization_rate.json` `r5`;
  `5357740`.

- **The corpus outgrew its own template grammar, and nothing had asked it
  to (the v0.18 cycle's first finding, produced during the v0.17 rotation;
  measured).**  The forward design proposed rendering every committed
  canonical term into English under a round-trip gate, and froze its first
  draft floor at 90% of all 12,777 nodes.  Adversarial review did the one
  thing that floor assumed: it ran the committed parser over the source
  field.  `formal_statement.canonical_ascii` parses for **2,172 of 12,777
  nodes — 17.0%**.  The single ingested corpus that is **97.9% of corpus
  mass**, `lean_workbook.ground.v1`, parses at **16.3%**; the rest of its
  content is Lean/Unicode syntax outside the template grammar.  Exactly
  **one** corpus clears a 50-parseable-term bar (`lean_workbook.ground.v1`
  at 2,040), so a per-corpus floor applies to it alone and the other 26
  report individually.  A term that does not parse has no source skeleton
  to round-trip against, so the floor was not merely optimistic — it was
  **unmeasurable as written**, and it was falsified before implementation
  rather than by a failed run.  Two things make this a finding rather than
  a planning correction.  First, nobody had checked: the ownership,
  coverage and compression ledgers all count nodes, and none of them counts
  *parseable* nodes, because until something asked the graph to speak in
  sentences there was no reason to.  Second, the number is now a
  first-class published artifact rather than a footnote — the design's R0
  makes the parse table, per corpus and per failure class, a construction
  prerequisite that must be discharged **before** R1's floor is allowed to
  freeze.  Status: **measured** (design-review finding, pre-implementation).
  Evidence: `docs/DESIGN-sans-template-rendering.md` §1 and the §6 gate
  history note; the table itself ships with
  `experiments/realization_rate.json` at v0.18.

- **A benchmark that times a cold cache measures the cache (v0.17, measured).**
  The first half-A trial timed the product at **83 useful tok/s** and a
  profile said why: every HTTP request paid ~460 ms of `CoreSession.boot`, of
  which **405 ms was `UnifiedKnowledgeStore.load` re-parsing every committed
  corpus from JSON, uncached, on every boot**.  The mechanism the thesis
  claims — copy and compute rather than sample — was never what the stopwatch
  was reading.  Memoizing the store load on the resolved path triple took boot
  **389 ms → 7.5 ms** and one definition task end-to-end over HTTP
  **674.8 ms → 7.5 ms** median, with **zero rendered bytes changed** (bodies
  byte-identical back-to-back).  The registered run then read 3,451 tok/s.
  Two things make the fix admissible rather than convenient: the shared-instance
  hazard was audited by **AST**, not grep (every attribute written only at
  `__init__`, frozen types throughout, and the one genuinely mutable path
  bypasses the cache by construction), with two *interleaved* conversations
  through the shared store matching fresh boots line for line — interleaved
  because a serial test would hide exactly the leak being denied; and
  `scripts/retrieval.py` is a seal-witness module, so the sealed task book was
  **re-sealed in the open** under the spec's new explicit re-sealing rule
  (`docs/SPEC-chat-completions-skin.md` §6): byte-identity proven, exactly one
  digest leaf moved, ids/halves/expected records byte-identical, half B
  undisturbed.  Status: **measured**.  Evidence: commit `025bd73`;
  `experiments/throughput_trial_kernel_halfA.json` (post-fix half A, median
  2,207.8 tok/s) against `experiments/throughput_result.json`.

- **A grounded model must be told to quote, and even then it delivers
  fragments (v0.17, measured).**  B-grounded is not a strawman: it receives the
  same committed records the kernel's answer rests on, extracted verbatim.  Its
  first prompt template never said to reproduce them, so it paraphrased, and
  paraphrase does not survive an exact-content check — 5 of 45 on a half-A
  trial.  The instruction was amended **before** the registered run, on the
  fairness argument rather than a score argument (a floored contender makes T4
  vacuous, because a zero denominator turns K into infinity, and it disarms C3,
  the control that lets the baseline falsify the thesis).  **The instruction
  did not move the score.**  The committed half-A trial ran under the amended
  manifest — its `baseline_digest` `3be33a20…` is the amended file's canonical-LF
  digest, and the pre-amendment file hashes `64a0d7c2…` — and it read the same
  **5 of 45**; the registered half then read **4 of 49**, with **0 of 16** on
  corpus definitions and **0 of 5** on twin lookups, its only credits being
  4 of 13 exact values.  The amendment was right on its own argument and
  bought nothing, which is the honest reading and the one worth recording.
  The interesting part is that this is the thesis appearing
  inside the contender: **exact content does not survive being sampled through
  a decoder**, whether or not the decoder has the content in front of it.  The
  exact-content contract is therefore the thesis's own diagnostic, not merely
  its scoring rule.  Status: **measured**, with a named asymmetry recorded
  rather than papered over: `belief_query` and `exact_value` hand the model no
  materials, and their checks require kernel notation (`located_in(x) = place`,
  exact fractions) a prose model rarely emits unprompted
  (`experiments/throughput_baseline.json`, `arms.B-grounded.session_derived_kinds_note`).
  Evidence: `experiments/throughput_result_bgrounded.json`;
  `experiments/throughput_trial_bgrounded_halfA.json`; commit `441ec91`.

- **The reviews were the instrument: a preregistered benchmark held against
  its own authors (v0.17, construction).**  Four holes that would each have
  produced a defensible-looking number were closed by review *before* the run,
  and they are worth more than the number they protect.  (1) **Any repository
  file could be minted into a certified bounded negative** — the closure route
  would answer about any path handed to it, so an author could have grown the
  answerable set at will; now only manifest-registered targets with a matching
  `world_id` answer and everything else refuses by name (`4b2e2de`).  (2) **The
  `num_ctx` amendment was inert**: the OpenAI-compat `/v1` layer drops the
  body field, so the contender would have been silently truncated at ollama's
  4,096 default and K would have been inflated by the exact mechanism the
  manifest claimed to prevent; replaced by a server-side 32,768 that fits the
  GPU, with a pre-declared secondary median over the tasks whose materials fit
  (`38c9778`).  (3) **The answer key was re-derived independently** — 46
  recomputed values and 73 verbatim artifact quotes, zero disagreements — and
  the frozen half rule was reverified over every task with the shipped pool
  ordering shown **less** hash-favorable than the alternatives it declined, so
  hash-shopping is excluded by evidence rather than by assertion (`ca2262c`).
  (4) **A fresh-eyes adversarial review of the skin could not construct any
  path** where served `content` carries a byte the engine did not render —
  200 KB lines, RTL unicode, prompt injection, essays requested and refused —
  with the honesty oracle re-implementing the join rule independently and
  mutation-checked for vacuity (`8059b4a`).  Status: **construction**, recorded
  because the general lesson is transferable: a benchmark's authors are its
  most motivated adversary, and the cheapest place to catch them is the
  interval between preregistration and the run, while adding is still
  legitimate.

- **WAITING crossed the wire without anyone inventing a value (v0.17,
  P-IH6 adjudicated).**  The substrate design registered the prediction in
  v0.10 and it sat unadjudicated through five parks of the HTTP skin: can a
  clarification question reach an external harness, and be answered by it,
  without the server ever substituting a default for the missing slot?  It can.
  An unmodified OpenAI-compatible client completes the triangle — a
  receipt-bearing answer, a WAITING round-trip resumed by the next user
  message, and a refusal delivered as a refusal — and the need record crosses
  as `x_corollary.need` = `{slot, prompt}`, the exact two fields the `Need`
  protocol exposes, with the next message binding through the verifier's signed
  channel byte-for-byte.  The negatives are stated as what a **signatureless
  wire can actually falsify**, and all three are pinned: an unparseable or
  absent reply asks again and never fills; a reply naming a different slot
  while one is awaiting is a `409`, not a reinterpretation; no slot binds on a
  turn where the user sent none.  In the registered run the surviving half of
  that leg reads **6 of 6 marked WAITING turns surfaced**.  Status: **fired**.
  Evidence: `docs/SPEC-chat-completions-skin.md` §6.2; `tests/test_serve_chat.py`;
  `experiments/throughput_result.json` `summary.clarification_gate`.

- **Eight of twenty-six celebrated cross-field matches align quantities that
  cannot be the same (v0.15, measured).**  Circle circumference, Ohm's law and
  Newton's second law share one skeleton and were reported together as a
  cross-field structural match; `CIRCUMFERENCE` is a length, `POTENTIAL` is a
  voltage and `FORCE` is a force, so the match is shape.  The check that says
  so has no way to say the opposite: its two values are `conflicting` and
  `unjudged`, and the compatibility of Boolean with set algebra was declared
  before anything ran, so the four logic/set-theory groups came back unjudged
  as predicted.  A cheap control using symbol names alone agreed only 0.3958 of
  the time, so names do not stand in for kinds.

- **A control scoped to the thing it controls cannot control it (v0.15,
  construction defect).**  The veto's corruption control permutes the kind tags
  and requires the authored ones to flag fewer conflicts than chance.  It
  cannot: the incompatibility table was scoped to the pairs that co-occur under
  the authored tags, so permuted assignments raise pairs with no row and cannot
  fire - 107 of 133 against 24 of 75.  The baseline under-fires by
  construction.  Scoping a table to what is reviewable and scoping it to what a
  null hypothesis needs are different requirements, and satisfying the first
  silently destroyed the second.

- **No hand-authored statement is unreachable, and the reason is worth more
  than the check (v0.15 inquiry, computed).**  An outside line of reasoning
  proposed certifying which statements no query can ever single out: under
  this reader's +1-per-word scoring, the strongest possible query for a
  statement is all of its own discriminating features at once, so it can
  never be named alone exactly when some other statement's features are a
  superset of its own.  Computed over the 262 hand-authored statements, that
  set is **empty**.  The cause is that hand-authored statements carry a median
  of 43 discriminating features and a minimum of 9, so strict subsumption
  essentially cannot occur.  The proposal's own construction gate required at
  least three victims and refused it in about a minute, before any
  measurement and without spending anything.  Recorded because the negative is
  a fact about the collection rather than about the proposal: whatever makes
  clarification hard here, it is not that statements are invisible.

- **A parallel gate cannot be faster than its slowest module, and this one is
  57.7% of the suite (v0.14 item 3, measured).**  68 modules at a frozen tip:
  `test_write_stage` 12,522.5 s, `test_corpus_analogy_split` 8,045.0 s, and
  all 66 others 1,120.5 s combined.  The registered balanced assignment
  therefore predicts the same 12,523 s wall clock at 2, 5 and 8 shards, so
  the achievable speedup is 1.73x and the v0.13 gate's five shards were three
  more than the work can use.  The useful consequence is negative: the
  registered proposal to sample the capability-blind control could save at
  most 4,317 s of serial time and exactly zero wall clock, so it is refused
  on arithmetic rather than on principle and the control stays whole.

- **The fourth consecutive explanation of the slow suite was also folklore
  (v0.14 item 3, measured).**  The roadmap named a 5,620 s blind-control
  sweep and a ~4,700 s fixture gap.  Measured, the blind control is 4,317.0 s
  and the fixture gap is 3,434.2 s -- and neither is the problem, because
  `test_write_stage` costs 12,522.5 s and appears nowhere in the roadmap's
  investigation list.  Its fixture overhead is 8.5 s, so it is not a setup
  artifact but 103 real tests.  `scripts/time_tests.py` was written because
  three prior explanations had been folklore; the lesson repeating a fourth
  time, in the very document that commissioned the measurement, is the
  finding.

- **The corpus's own subject vocabulary is unreadable, and saying so does not
  fix anything (post-v0.14, exploratory).**  Measured over the whole graph,
  13 of 28 top-level id prefixes and 11 of 37 declared disciplines --
  `chemistry`, `economics`, `trigonometry`, `finance`, `combinatorics`,
  `computer_science`, `mathematics` -- occur in no word index, so the word
  naming a subject is the one word the resolver cannot see.  `load_trees` has
  always returned those disciplines and `build_index` has always discarded
  them.  Indexing them changed nothing on 140 spent queries, 15 of which
  contain a discipline word and could have moved, and cost one false positive
  per thousand (0.0300 to 0.0310).  Two lessons, and the second is the
  expensive one: a structural gap measured at corpus scale is still not
  evidence that closing it helps, and the queries the fix did improve were
  ones typed by hand after reading which rows had failed.  Branch
  `explore/v015-ask-boundary`; deliberately unmerged.

- **A capability-blind control can be beaten by the failure it was built to
  catch (v0.14 Q3, measured).**  Reciprocal candidate load pays `1/k` for
  returning the target in a small set, so the resolver's 0.7127 against the
  25-id blind arm's 0.0326 is largely a measure of how often it answered with
  exactly one id: 25 of its 30 recalled targets came back alone, mean `1/k`
  among them 0.9028.  The same decisiveness produced the wrong single BIND
  that missed Q1 and the 0.789 target recall that missed Q5.  A control that
  rewards small answers cannot separate precision from overconfidence, and
  the gap it reports must not be quoted as reading comprehension.

- **A preregistered clause the intervention cannot influence measures the
  baseline, not the intervention (v0.14 Q4, measured).**  The mechanical
  precision arm classifies OEWN sentences, which contain no `without TERM`
  structure, so the candidate's masked admission path is never entered and
  Q4 re-measured the untouched v0.13 resolver.  It reproduced v0.13's 0.034
  almost exactly — 0.024/0.038/0.042, pooled 0.03467 — which is a useful
  independent replication across three fresh disjoint samples and was never
  a test of the exclusion.  Registering it as a shipping clause guaranteed a
  miss.  Check, before freezing, that every clause has a path from the
  intervention to the number.

- **The fresh negative rows were easier than the sentence that motivated
  them (v0.14 Q6, measured).**  Stripping the declared negative span changed
  the bound on 1 of 16 rows, against a registered threshold of 4, and seven
  of eight `negative_bind` rows bound correctly without needing the veto at
  all.  The exclusion mechanism itself works — the spent v0.13 sentence moves
  from `continuous_compounding` to `simple_interest` by promoting a
  lower-scored survivor — but rows authored to *contain* negative structure
  are not the same as rows where negative structure *decides* the answer, and
  only the second kind can attribute a result to it.  See
  [[a-negative-veto-must-happen-before-candidate-selection]].

- **A frozen evaluator can freeze in its own expiry date (v0.14, pre-score).**
  Two preregistration tests asserted the absence of the candidate and of the
  result file by looking at the live import path and the working tree.  Both
  claims are about chronology, and both were written as claims about the
  present, so each was guaranteed to fail at exactly the moment the cycle
  succeeded — inside the one file the candidate commit may not modify.
  Freezing an evaluator therefore has a second requirement beyond running it
  early: every assertion in it must be phrased about an object that stops
  changing.  Git commits do; imports and directories do not.  Found by
  implementing the candidate, which is the only thing that could have found
  it.  See [[a-negative-veto-must-happen-before-candidate-selection]].

- **A negative veto must happen before candidate selection (v0.14 protocol,
  unmeasured).** Filtering only a resolver's final tuple makes the registered
  causal ablation incompatible with retained reach: when the stripped query
  uniquely selects the excluded reading, post-hoc deletion yields PASS instead
  of allowing a lower-scored non-contradictory reading to survive.  The frozen
  evaluator therefore masks candidate admission inside expression, literal-id,
  and word paths while preserving graph size, document frequencies, postings,
  known-word status, and ordering.  Synthetic checks cover the lower-score
  survivor, last-owner known word, and no-fallback terminal PASS.  This is a
  **design/construction finding only**; no fresh row has been resolved and no
  Q1–Q6 result exists.

- **Ambiguity is common enough to keep, but only just (v0.13 A1).** The
  registered development and two holdout sets contain 62 questions labelled
  `expect=resolve`: 43 BIND, 16 ASK, and 3 PASS. ASK therefore occupies
  **0.2581**, just above A1's 0.25 line; A1 FIRED. The first implementation
  reported 0.2712 (16/59) because it silently removed PASS outcomes. Review
  restored all registered in-corpus questions to the denominator. The verdict
  survives, but the stronger-looking margin does not. Holdout 2 alone is
  0.1875, so this is weak evidence for continuing the context lane, not a
  claim that ambiguity grows robustly across sets. Candidate-set size remains
  an explicitly unregistered probe (median 2, maximum 6), not A2 evidence.
  Regenerable from the pinned inputs in `experiments/ambiguity_rate.json` with
  `scripts/measure_ambiguity.py`. Status: **empirical**.

- **The surface-morphology candidate reaches the whole registered set and
  still loses the shipping conjunction (v0.13 item 1).** On the third
  disjoint hand-authored holdout, conservative variants over corpus-owned
  prose and glossary terms reached 24/24 and recalled 23/24 registered
  targets. But the fresh pinned-OEWN arm measured **0.034** (34/1000) against
  the **0.030**
  shipping ceiling, so the resolver change was reverted as preregistered.
  The one target miss was a confident contradiction: `without compounding`
  bound continuous compounding. Coverage is not correctness, and morphology
  cannot represent negative contrast. Independent review recovered the full
  raw one-shot ledger from its staged Git blob, so the weak 14,571-way blind
  tie is inspectable rather than surviving only as a count and preview.
  Status: **empirical, rejected trade**.

- **Groundedness-at-all beats random trees and fails local near-misses
  (v0.13 item 4).** A one-head foil keeps each statement's relation,
  unlabeled tree, leaves, arities, and the batch head histogram. Its threshold,
  seeds, concept, and decision bars were stated before score inspection, but
  its executable protocol first landed with the ledger; this is exploratory,
  not fully auditable preregistered evidence.
  Its capability-blind paired baseline is exactly 0.5. All construction
  checks fired, but the fixed 0.50 gate scored balanced accuracy 0.505 on
  miniF2F and 0.510 on Goedel-Pset; authentic-vs-foil paired accuracy was
  0.607 / 0.586. Authentic scores do retain a small mean margin (+0.0288 /
  +0.0245), which is evidence that the metric notices the edit and evidence
  that noticing is not enough to admit. The v0.12 probe was true against
  noise and false as permission for a gate. Regenerable:
  `scripts/measure_grounded_admission.py`. Status: **exploratory empirical
  near-miss; ledger labels G1/G2 missed, G3/G4 fired; gate parked**.

- **The sign flip does not travel; it was a fact about Lean-workbook
  (v0.12 item 1).** Two sources the emitter was not fitted to run the
  *other* way. miniF2F (157 nodes) sits below its matched null at every
  size: −0.016 at N=8, −0.010 at 32, −0.043 at 157. Goedel-Pset (1,896
  nodes) is below its null at every non-degenerate size and diverges
  monotonically: −0.009, −0.046, −0.093, **−0.126** at N=1,896, where
  ISG reads 0.0254 against a null of 0.1513. H1 **missed**. This is not
  a curve that failed to flip — it is a curve running the other way.
  Ingestion still buys coverage; it does not buy a transferable
  structure-recovery claim. Regenerable:
  `scripts/measure_heldout_recovery.py`. Status: **empirical**.

- **At matched N the fitted source compounds and the holdout does not
  (v0.12, C1).** Registered before the cell was computed. At *identical*
  N=157, same generator, same null, same seed protocol: Lean-workbook
  **+0.0496** (ISG 0.2419 vs null 0.1923), miniF2F **−0.0428**. Opposite
  in sign and separated by 1.9× the combined null spreads, with both
  nulls far from zero. So the negative is not an artifact of holdout
  size — the 128–512 objection is dead, because Lean-workbook shows the
  effect *at* 157. **Source, not scale.** Regenerable:
  `scripts/measure_self_grounding.py --sizes 157 --no-all`.
  Status: **empirical**.

- **The rejected proxy would have reported 71% and 92% self-grounding on
  sources that recover nothing (v0.12, H4).** Proxy vs owner-ISG:
  miniF2F 0.708 against 0.0077; Goedel-Pset 0.924 against 0.0404. Both
  far past the registered 0.2 margin. Had v0.11 shipped the sharing
  proxy as its headline, this cycle's negative would have been invisible
  — the refusal to use it is what makes the negative legible.
  Status: **empirical**.

- **The parts are grounded; they are grounded elsewhere (v0.12, H6).**
  XSG holds at 0.59–0.63 on Goedel-Pset and 0.70–0.81 on miniF2F across
  every size. Holdout subterms are not ungrounded — their owners are the
  curated and Lean-workbook layers. 157 competition problems and 1,896
  formalized word problems do not own one another. Status: **empirical**.

- **The emitter degrades measurably with distance from the source it was
  fitted to (v0.12).** Emit rate through the *unwidened* emitter:
  Lean-workbook 99.03%, miniF2F 98.12%, Goedel-Pset 92.58%. And 101 of
  Goedel-Pset's 114 `parse_fail` exclusions (66% of all 152) carry one
  unmapped constant, `Real.pi`. The coverage instrument admits those
  statements while the emitter cannot round-trip them, so **coverage
  overstates what is authorable** — a soft sampling frame inherited by
  every downstream count. Regenerable: `experiments/goedel_pset_emit.json`.
  Status: **exact**.

- **Groundedness-at-all survives the holdouts where self-grounding does
  not (v0.12, unregistered probe).** Exact grounding by *any* owner
  beats its null by +17.5 to +46.2 points on all three sources at every
  size, while ISG spreads 44× across the same sources (0.55% to 47.3%).
  The quantity an admission gate should rest on is "is this grounded at
  all", not "does it ground itself". **Unregistered** — computed after
  seeing the holdout data — and therefore not scored this cycle; it owes
  a design and a prediction, plus a harder foil than random trees.
  Status: **probe, unregistered**. Its proposed admission consequence was
  tested and refuted by the v0.13 near-miss above.

- **A holdout inside `data/` is not held out (v0.12).** Authoring
  miniF2F into the merged graph moves the published v0.11 channel split
  under *either* available discipline label: a novel discipline makes it
  a universal `external` donor (share 0.391 → 0.581, `prior_corpus` 286
  → 10), while `number_theory` makes it a 26,014-constituent
  `prior_corpus` donor to the very layer it must be independent of. The
  constituent total moves 181,909 → 183,305 either way. There is no free
  label, so the premise was wrong rather than the label:
  `data_holdout/` quarantines a corpus that stays git-versioned,
  schema-validated and byte-reproducible while being invisible to the
  merged graph. Status: **exact**.

- **Ingestion compounds, and the proxy would have lied about it (v0.11
  item 1).** At 12,515 ingested nodes, 47.3% of considered subterms have
  another ingested node as their most-independent owner, against a
  distribution-matched synthetic null of 41.0% (spread 0.14 points).
  The gap changes sign with scale: real is *below* the null at N=8 and
  32 and above it from N=128. Dropping the single most common subterm
  (`^(?0:V, 2)`, 6,870 hosts) *widens* the gap to 12.7 points — the
  popular term was curated-owned, not the carrier. The rejected
  shared-skeleton proxy reads 1.000 of grounded constituents at the
  same N; route-1 ISG of those same constituents is 0.543. Sharing is
  nearly universal; grounding is not. S1–S4 all fired. Regenerable:
  `scripts/measure_self_grounding.py`. Status: **empirical**.

- **The bag's figure of merit at thousands is 0.022% (v0.11 item 2).**
  On 12,771 nodes the operator-bag forms 9,041,744 pairs at 0.0220%
  precision against typed twins; the matcher forms 1,991 at 99.95%.
  The one miss is the already-named double-angle print convention.
  A size-matched draw from the bag recovers 1 twin in 1,991. Count
  still belongs to the bag; the only number that does not restate the
  bag's definition belongs to the matcher. FF1–FF5 all fired.
  Regenerable: `scripts/measure_operator_bag.py`. Status: **empirical**.

- **The first ingested-to-curated typed twin is the double-angle cosine
  (v0.11 emitter).** `leanworkbook.skel.lean_workbook_49137`
  (`COS(2*theta) = COS(theta)^2 + -(SIN(theta)^2)`) typed-twins
  `trigonometry.identities.double_angle_cosine`. The operator-bag
  misses the pair because the emitter prints subtraction as `+ -(...)`
  (a `+` glyph) and the curated node writes infix `-`. Matcher
  precision against the bag is therefore 1 − 1/N, not 1.0 — the first
  break of item 4's P3 at thousands. Status: **exact**.

- **The skeleton emitter authored thousands; that is substrate for the
  curve, not the curve (v0.11 prerequisite).** 12,514 unique-covered
  Lean-workbook statements now have matcher templates (302 ground +
  12,212 emitted); 123 remain excluded, bucketed
  (`experiments/lean_workbook_emit.json`). Corpus 508 → 12,771. The
  measurement that uses this layer is the self-grounding curve above.
  Status: **empirical** (substrate).

- **The ingested layer grounds itself at hundreds of nodes (v0.10 item 4).**
  614 of 681 exact constituents inside `lean_workbook.ground.v1` are
  `same_corpus`. A third statement now shares `^(2, 30)` with the two
  earlier ingested nodes (`leanworkbook.ground.lean_workbook_28978`),
  through `prior_corpus` / `number_theory`. Item 5's two-constituent
  anecdote was not a one-off: ingestion compounds. Status: **empirical**.

- **Operator-bag precision collapses when the corpus grows by ground
  identities (v0.10 item 4).** On the 257-node prior graph a capability-blind
  operator-bag (`same set of {+,-,*,/,^,=}`) forms 4,345 pairs against the
  matcher's 88 typed pairs (precision 2.03%). After ingesting 251 unique-
  covered Lean-workbook ground identities: bag 7,622 vs matcher 96
  (precision 1.26%); ingested-only, 1,489 vs 8 (precision 0.54%). Matcher
  precision against the bag stays 1.0 — same typed skeleton implies same
  glyphs. The eight new typed pairs are ingested-to-ingested parenthesization
  / commutativity twins of the same identity; none twin with a curated
  slotted law. The baseline that "won" on pair count on 221/257 still wins
  on pair count and loses harder on precision. Regenerable:
  `scripts/measure_operator_bag.py` → `experiments/item4_operator_bag.json`.
  Status: **empirical** (registered as P3 before the seed ran).

- **Recursive and iterative Euclid are one remainder recurrence; Stein is
  not, even though it is also named gcd (v0.10 item 3).**
  `programming.euclid.recursive` and `programming.euclid.iterative` (both
  from TheAlgorithms/Python, MIT) typed-twin on
  `GCD⟨?0:V, ?1:V⟩ = ITE⟨EQ⟨?0:V, 0⟩, ABS⟨?1:V⟩, GCD⟨?0:V, MOD⟨?1:V, ?0:V⟩⟩⟩`.
  First-party Stein is a singleton. A capability-blind token-`gcd` baseline
  forms all 3 pairs (precision 1/3); the matcher forms 1 (precision 1.0).
  Control-flow (recursion vs while) is evaluation strategy, not structure.
  Status: **exact** (typed twin, registered as P4/P5 before the matcher ran).

- **Factorial and double-factorial share a token and not a skeleton;
  binary exponentiation is a third recurrence pair (v0.11 item 3).**
  Same source, three more files, tests at volume (`range(20)` vs
  `math.factorial` / `math.prod`). Typed twins:
  `{programming.factorial.recursive, programming.factorial.iterative}`
  on `FACT⟨?0:V⟩ = ITE⟨LEQ⟨?0:V, 1⟩, 1, *(?0:V, FACT⟨-(?0:V, 1)⟩)⟩`;
  `{programming.dfactorial.*}` on the `N - 2` sibling; `{programming.binexp.*}`
  on even-first square-and-multiply. A token-`factorial` baseline forms
  6 pairs (precision 1/3); the matcher forms 2 (precision 1.0). Combined
  programming-keyword baseline 10 pairs vs 4, precision 0.4. The
  `python-tests` citation-not-PROVEN decision survives at this volume:
  nine programming nodes stay `formal`; retrieval still mints no
  `proof:programming.*`. Status: **exact** (P-W1/P-W4/P-W5, registered
  before the matcher ran).

- **At volume, the programming corpus is self-certifying under the
  conservative owner rule and not under the generous one (v0.11 item 3).**
  Nine nodes, eight at groundedness 1.0: corpus mean 0.939. Twin pairs
  ground each other, so the conservative (least-independent-owner) reading
  puts independent credit under 0.1 and trips `self_certifying_lower`.
  The generous reading still gives multi-owner constituents to external
  and does not trip the flag. Provability remains the only corpus that
  self-certifies under *both* rules. Status: **exact** (GC4 ninth
  acknowledgment; not predicted — a measurement).

- **The honest reach of the corpus grammar on uncontrolled formal math is about
  a third — measured, not asserted (v0.9).** A shared coverage instrument
  (`scripts/grammar_coverage.py`) reduced three real, digest-pinned Lean sources
  to head-algebra skeletons: miniF2F 29.7%, Lean-workbook 64.1%, Goedel-Pset-v1
  32.8% at 1.73M statements (full-statement, the conditional-node fraction). The
  two competition/olympiad-derived sources land near 30%; the one curated
  inequality set (64%) is the outlier. The untranslatable remainder is a
  prioritized, three-source-confirmed grammar-extension backlog: a
  relational/predicate head (the single largest 1.73M gap, `no_relation_in_goal`
  at 22%), a quantifier/binder head, a first-class function slot, indexed
  aggregation, and a carrier-honest number field. See
  `experiments/ANALYSIS.md` §§ grammar-coverage. Status: **empirical** (a
  measurement, reproducible byte-for-byte from the committed extracts / pinned
  parquets).

- **"The corpus carries head X" must be verified node-by-node, and against the
  actual operation — not the surface symbol (v0.9).** Independent adversarial
  review found the coverage classifier over-counting three separate ways, each
  corrected downward: it claimed `%`/`∣` as supported heads the corpus does not
  have (the only `MOD` in `data/` is morphology's linguistic *modifier*); it read
  `/` and `-` over ℕ/ℤ as real division/subtraction when they are `Nat.div`/
  `Int.div` (floor) and monus, so trivial statements like `(1 + 1/n)^n < 3` (over
  ℕ, just `1 < 3`) counted covered; and it was arity-blind to bare `log`, so a
  two-argument `log b x` (base-b log) passed with the same token set as
  `Real.log x`. The reusable rule: a supported head is a claim to check against
  the corpus and against the operation's real semantics under its carrier, never
  an assertion from the surface glyph. Status: **reference** (a methodology
  correction, with regression tests).

- **Offline, propositional-only verification cannot ground an ingested arithmetic
  `verified_by` (v0.9).** Verification in this repo is a manifest lookup plus a
  parse of a committed Lean transition-row artifact — no Lean toolchain — and the
  correspondence rung translates only the propositional fragment (not/and/or/
  implies over `Prop`). Ingested Lean-workbook / Goedel-Pset goals are arithmetic,
  hence UNTRANSLATABLE, so an ingested arithmetic theorem cannot earn a
  `verified_by` today. This is why v0.9 authored no `verified_by`-bridged nodes;
  building the arithmetic verifier is the precise, located wall v0.10 climbs.
  Status: **reference** (an architectural boundary, not a defect).

- **A digest supplied by the claimant is a checksum, not a trust root; a
  post-hoc digest is detection, not containment.** The first PROVEN-WRITE
  implementation executed candidate Python in a scratch cwd, screened obvious
  paths, and digested the repository afterward. Independent review showed both
  category errors directly: the candidate could supply arbitrary proof bytes
  plus their matching digest, and code could damage the real repository before
  the after-digest reported the loss. The corrected boundary is declarative:
  candidate seed text must be the exact AST of a canonical literal-JSON
  envelope and is never executed; trusted code materializes it. Proof bytes
  must also match the independently maintained
  `prover/proof-artifact-manifest.json`, and one immutable snapshot feeds the
  digest, closure, trace, and correspondence checks. The reusable rule is that
  evidence and the authority authenticating it cannot arrive through the same
  untrusted channel. A later review added the source-of-truth corollary: a
  materialized corpus is not evidence that a replacement seed preserves every
  output of the original (one seed can own several corpora), so the v0.7 lane
  accepts new seed/new corpus pairs only. *v0.7 item 3 re-review; regressions in
  `tests/test_write_stage.py`* (2026-08-10)

- **Signing the envelope would have made the acceptance test prove nothing.**
  ROADMAP-v0.7 item 2's gate is "a stale or forged pre-restart binding is
  refused". The natural implementation puts a MAC over the whole session file,
  and it passes the gate — for the wrong reason. A forged binding inside a
  signed envelope is caught *by the envelope*, so the test says nothing about
  whether **bindings** authenticate, which is the property being claimed. The
  same move would have inverted the trust story the harness had been building,
  in which public state is public and untrusted and authority comes from
  per-record signatures plus verifier-private ledgers. The shipped session file
  therefore carries no MAC at all: anyone may edit it, the forgery test writes
  its binding *into the file* and reads it back normally, the restore succeeds,
  and the record is refused by its own signature. The general lesson is about
  test design more than cryptography — **a guard placed one layer above the
  property under test makes the test vacuous while making it pass**, and the
  only reliable defence is to forbid the guard in the registered prediction
  before the code exists (P-DS2 did). *Found while designing v0.7 item 2;
  regression: `tests/test_session_durability.py::PreRestartBindingTests::
  test_forged_pre_restart_binding_is_refused_by_name`* (2026-08-10)

- **A signature cannot see a replay; only a counter outside the message can.**
  Every other refusal in the durable-session design falls out of a MAC:
  tamper with a binding, a ledger, a key id, and the check fails. Rolling the
  ledger *back* does not. An earlier snapshot is authentic in every respect —
  correct key, correct session, correct owner, valid signature — and its only
  defect is being out of date, which is not a property any message can carry
  about itself. The fix is a monotone per-scope counter kept in the **private
  keyfile**, precisely because the public snapshot cannot lower what it cannot
  see. Two ordering details turned out to be load-bearing and are easy to get
  backwards: the signature must be checked *before* the counter is consulted
  (otherwise a forged snapshot claiming sequence 10⁹ locks the real owner out —
  a denial of service handed over free), and the admission test must be `>=`
  rather than `==` (otherwise a session that crashed between export and import
  is bricked). The `>=` buys rollback refusal and explicitly does not buy fork
  refusal; that trade is filed rather than hidden. *Registered in advance as
  P-DS5, the prediction most likely to miss; regressions:
  `LedgerAttackTests::test_ledger_rollback_is_refused` and
  `::test_forged_ledger_cannot_advance_the_counter`* (2026-08-10)

- **A lifetime that is stored is not a lifetime; it is a suggestion.** The
  first design gave `UserBinding.lifetime` the obvious job of holding the
  binding's current state, `session` becoming `superseded` when replaced. That
  is unusable as authority: the field lives in public state, so anyone holding
  the tuple writes it back. The shipped protocol splits **declared** from
  **effective** — the declared lifetime is chosen once by the trusted return
  channel and covered by the MAC, and `superseded`/`expired` are *recomputed on
  every read* from the private ledgers and the current goal, stored nowhere.
  A creating authority cannot declare them at all, because an answer that
  arrives already dead is a stranger state than the protocol wants to
  represent. The same split resolved what "durable" could mean operationally:
  a durable binding is signed under an **owner-scoped** key with neither
  session id nor frame spec in its payload, which is exactly what lets it cross
  into a new conversation and exactly why it is not frame-isolated. Reach and
  isolation are the trade, and the protocol table states it rather than leaving
  it to be discovered. *v0.7 item 2; `scripts/lifetimes.py`* (2026-08-10)

- **Durable state needs a durable place to record its retirement.** Probing
  this item's own fixes turned up a wrong-answer bug the item had introduced:
  supersession was filed on the verifier instance, which is correct for a
  session-scoped answer (it travels in that session's snapshot) and wrong for a
  durable one, whose whole point is being valid in conversations that instance
  will never meet. A durable answer replaced in session A came back to life in
  session B. The general shape is worth keeping: **whenever state is given a
  longer life than the thing that records its death, the death gets lost**, and
  the fix is not a wider check but moving the record to something that lives at
  least as long — here, the key ring, the design's only durable private state.
  *Found by adversarial self-review of v0.7 item 2, after the acceptance
  scenario was already green; regression:
  `LifetimeProtocolTests::test_durable_supersession_is_filed_under_the_owner_scope`*
  (2026-08-10)

- **A refusal with the wrong stated reason teaches the wrong invariant.** A
  session file's header carries convenience copies of the session id and owner
  that the state also holds. Rewriting only the *inner* `user_frame.owner` left
  the ledger check satisfied and pushed the whole disagreement onto the
  per-binding signatures — which did refuse it, so nothing was exploitable.
  But it was refused as a **forgery** when the actual defect was an
  inconsistent envelope, and a reader who traced that refusal would learn that
  the binding scheme guards envelope consistency, which it does not. The repair
  is not a stronger check but a check *in the right place*. Recorded because
  "the attack failed" is a weaker result than it looks when the reason is an
  accident of layering. *v0.7 item 2 self-review; regression:
  `LedgerAttackTests::test_header_may_not_disagree_with_the_state_it_carries`*
  (2026-08-10)
- **A shared search protocol can port perfectly and carry no lever with it.**
  ROADMAP-v0.7 item 1 asked for the same policy protocol over story actions
  "before claiming a general controller". It ports exactly: the identical
  `SearchController`, the identical ranker/argument-generator split, domain
  weights over the identical architecture, a disjoint vocabulary, and the
  frame verifier holding the same sole-authority position Lean holds. Every
  held-out brief solves. And the best-to-worst spread between six ranking arms
  on any brief is **1.07%** (373 vs 377 proposals) against **65.6%** on the
  proof side, with every arm expanding exactly 32 nodes. The cause is not the
  weights and not the domain's difficulty; it is the interaction of two
  choices that looked independent. Breadth-first search expands a node's FULL
  candidate list, and the story grammar admits exactly one legal ordering at
  depth five — so every node above the solution is expanded whatever order the
  ranker proposes, and ranking can only save part of one node. On the proof
  side the same controller leaves real headroom because solutions sit at
  depth 2-4 with many nodes per level, so a good order reaches a solving node
  *earlier in its level*. The transferable lesson is that "we ran the same
  protocol in a second domain" is a claim about plumbing, and the thing worth
  claiming — that ranking buys something — has to be measured separately in
  each domain, because the search regime, not the policy, decides whether
  there is anything for a ranking to buy.

- **Off the winning path is not the same as dead.** The first proof/story
  curve artifact classified every accepted transition outside the first BFS
  solution as a dead branch. That silently included siblings still waiting in
  the frontier when another branch solved. Independent review blocked the
  resulting 1,552-branch claim. The repaired controller records which child
  states were actually expanded and closes a branch only when its complete
  queued subtree was exhausted without proof. The valid proof count is 227,
  not 1,552; story runs preserve 96 closed transitions per arm, not 496. The
  substantive result survives on stronger evidence: learned pooled re-proposal
  share is 0.2063 versus syntax's 0.2053, no measurable avoidance. The general
  rule is broader than search: **a negative outcome needs evidence of
  exhaustion; non-selection only proves that something else finished first.**
  *v0.7 item 1 post-rebase adversarial review; regression:
  `SearchControllerTests::test_queued_but_unexpanded_sibling_is_not_called_dead`*
  (2026-08-10)

- **The learned ranker overtook the baseline that beat it and lost anyway.**
  v0.6 publicly retracted its live learned-gain claim when a state-blind
  frequency order solved its one theorem in 64 proposals against a learned
  mean of 65.0. Over 24 held-out theorems the same three shipped checkpoints
  now average 49.00 proposals against that frequency order's 51.58 — the
  retraction's specific comparison reversed with breadth. The verdict did not
  move, because the arm added this cycle is neither: a closed-form
  syntax-aware order reading the rendered goal takes 48.29, solves 21/24 at
  the middle budget against the learned mean of 19.33. In the one recorded,
  fixed-order host run it also finishes sooner, but that timing evidence is
  observational rather than counterbalanced. Two things follow. First, a negative result stated
  against one baseline is only as durable as that baseline — "learned loses"
  survived here, but "learned loses to frequency" did not. Second, the
  cheapest strong control is often the one nobody wrote yet: the syntax arm is
  forty lines of rules over text the verifier already renders.

- **Wall clock and proposal count can disagree, but one fixed-order run cannot
  explain why.** The learned arms need fewer Lean calls than arbitrary and
  frequency yet finish later in this recorded host run: at 0.02 s the blind
  arms solve 17/24 and learned solves 14/13/14. The first write-up attributed
  that gap to forward-pass cost. Independent review correctly narrowed it:
  fixed arm order and one sample leave warm-up and host drift confounded. The
  useful result is that proposal count is not a latency proxy; a causal timing
  claim needs repeated randomized or counterbalanced runs.

- **PyPantograph's Windows project blocker was a call that did not have to
  happen.** `prover/FEASIBILITY.md` recorded native project loading as broken
  because PyPantograph 0.3.15 resolves `LEAN_PATH` by shelling out to POSIX
  `printenv`. Reading `server.py` rather than patching it showed the guard is
  `if project_path and not lean_path` — supplying the path explicitly means
  the call never runs. Native, no fork, no patch, and a project-import family
  whose propositions an `Init`-only server refuses to elaborate at all. Worth
  keeping as a habit: a dependency's "unsupported on this platform" is often
  one conditional, and the conditional is usually cheaper to read than the
  workaround is to build.

- **A record can enter at the right rung and still usurp the wrong
  authority.** The whole contract around external retrieval is "a tool
  transaction proves what was fetched, not that its content is true", which
  reads as a *status* constraint — keep the record at `empirical`, and the
  ladder is safe. It is not sufficient. An observation file whose
  `observation_id` was set to a committed statement id bound that statement's
  UNKNOWN slot the moment a caller invoked the tool rung directly. The record
  never claimed to be `derived`; every status assertion in the suite passed.
  What it took was the *right to answer that key*, which the exact rung
  already owned. The miss chain would never have reached the tool rung for
  that key — but a verifier that depends on the policy walking the ladder in
  order has delegated its authority to the policy. The repair puts the
  outranking test where POINT is adjudicated, not where the chain is walked.
  The general lesson is that an epistemic ladder needs two independent guards
  — one on what a record may *claim*, one on what it may *answer* — and that
  a "rank" ordering only constrains the second if it is enforced at the
  binding boundary. *Found by adversarial self-review of v0.7 item 6, after
  all six deliverables' own tests were green; regression:
  `tests/test_retrieval_tools.py::ObservationAdapterTests::
  test_outside_record_cannot_answer_a_slot_a_committed_record_owns`*
  (2026-08-09)

  **CORRECTION (2026-08-10, external review).** The sentence originally
  printed here — "an external record binds only if nothing committed and
  nothing derivable matches the key at all" — was **false when written**, and
  the way it was false is the more useful finding. It described the *code*
  accurately: the outranking test consulted `item_match_mode` over
  `items + derivations`. It did not describe the *store*, because the WordNet
  synonym bridge reaches committed records through shared synset members,
  and no alias comparison can see that. With an archive loaded, one TOOL
  transaction emitted `[corpus:proven, wordnet:empirical,
  observation:conjectured]` for a single key and POINT bound **any** of the
  three: a conjectured outside note answered the slot a proven statement
  answers. A synset id impersonation (`observation_id: "a-n"`) bound for the
  same reason from the other side — a synset id is not a lemma, so the key
  reached nothing and looked unowned. The claim is now true, and true because
  the test enumerates the doors rather than describing one: alias,
  twin_ledger, WordNet bridge, synset-id impersonation, and the original
  `observation_id` case each have their own regression in
  `ObservationAuthorityDoorTests`. **The lesson worth more than the fix: the
  author's own repair was the unprobed boundary.** A guard written in
  response to a finding gets tested against *that* finding's path, and the
  test passes, and the passing test is then read as covering the guard. It
  covers one door. The discipline that follows is to enumerate every way a
  key can be *reached* before claiming what may *answer* it, and to write one
  regression per way rather than one per bug.

- **A prediction can be adjudicated FIRED while its own stated miss
  condition has already fired.** P-RT6 (session pruning) named its miss in
  advance and in writing: "*Miss* if pruning refuses a branch that would
  otherwise have been VERIFIED." The delivering commit recorded it FIRED. It
  had missed. `RetrievalVerifier.state_key` delegated its frame half to
  `FrameAssertionVerifier.state_key`, which keys on the frame's **name** plus
  its asserted claim ids, obligations and closed flag — omitting
  `declarations`, `suspends` and `owner`. Two same-named frames with
  contradictory premises therefore shared a pruning key, so a REFUTED dead
  end in one returned REFUSED for the other, whose branch evaluated fresh was
  VERIFIED; in belief frames that is Sally's dead end refusing Anne's branch
  and citing Sally's premise as the reason. The delegation is correct where
  it lives — `Controller.run`'s `rejected` set is run-local and one run holds
  one frame — and it is unchanged in `frames.py`; what was wrong was
  inheriting a run-local key for evidence that deliberately outlives the run.
  The mechanism of the mis-adjudication is the part to keep: all three cases
  the commit *did* exercise (a second dispatcher hop, another session, an
  advanced state) are cases where the key is supposed to differ or to match,
  and **none of them constructs two states that must not share a key**.
  Confirming a cache's hits is not testing a cache; the miss condition was
  about its collisions, and no probe went there. A registered prediction only
  does its job if something deliberately walks at its *miss* clause — writing
  the clause is not the same as testing it. Re-adjudicated MISSED-then-repaired
  (`repr(state.frame.spec)` joins the key, the same frame scope receipts are
  signed against); regressions:
  `tests/test_retrieval_tools.py::SessionPruningTests::
  test_same_named_frames_with_contradictory_premises_do_not_share_a_prune`
  and `::test_same_named_belief_frames_of_different_owners_do_not_share_a_prune`.
  *Found by external adversarial review of v0.7 item 6.* (2026-08-10)

- **Ranking a result set is safe exactly when ties keep the old order.**
  Adding a relevance score to neighborhood retrieval looked like a
  behaviour change waiting to happen: 339 committed tests bind by *position*,
  and several assert that POINT at position 0 verifies. It changed nothing.
  The reason is structural rather than lucky: the committed sources
  (corpus, lexicon, twin ledger, decomposition, proof) all alias the same
  statement id and title, so for any key they score **identically**, and a
  sort keyed on `(-score, source_order, item_id)` degenerates to the
  pre-existing order within every tie group. Ranking only reorders material
  that genuinely differs in overlap. Registered as P-RT3 before running, and
  it fired with zero test edits — which is the useful form of the result,
  because "ranking is a refinement of the old order" is a property a future
  scorer must preserve, not a coincidence to rediscover. (2026-08-09)

- **A representation borrowed from a matcher smuggled its assumptions into a
  proof gate, and a true theorem certified a false claim.** The twin matcher
  folds every parameter-like slot into one class `P`, which is exactly right
  for its question — "do these two statements have the same shape?" — and
  asserts nothing about truth. The correspondence check reused that front end
  on purpose, so that a proof link would be judged by the same grammar the
  corpus is grouped by rather than by a private re-implementation. The reuse
  was the right call and it carried one wrong assumption across the boundary:
  a lattice constant is not a placeholder. Under one shared class,
  `MEET(PROP1, TRUTH) = TRUTH` and `MEET(PROP1, FALSITY) = FALSITY` are the
  same skeleton, so a machine-checked Lean proof of `P ∧ ⊥ ↔ ⊥` — a TRUE
  theorem — adjudicated CORRESPONDS against the canonical claim
  `P and true = true` — a FALSE one — via the *canonical* route, and the WRITE
  gate staged it with all fourteen checks PASS. Nothing was bypassed; the
  evidence a gate consumed was weaker than the gate itself, which is the
  failure mode that survives review precisely because every check is green.
  The fix had to be narrower than the obvious one: keying constants by
  SPELLING would also close the hole and would silently delete every
  `ambiguous_with` report (the set-theory twins spell TOP as `UNIVERSE`),
  making the check look stronger while being less honest. Poles are
  separated; spellings of one pole are not. *near-miss; PROVEN-gated WRITE
  review* (2026-08-10)

- **The corpus's flagship cross-discipline twin is also the thing that stops
  a proof link from naming an owner.** `logic.boolean_laws.de_morgan_laws`
  and `settheory.boolean_laws.de_morgan_laws` share a skeleton character for
  character, and the logic node's own `statistical_significance` celebrates
  that: "both nodes state one theorem of one Boolean algebra, read once over
  propositions and once over subsets". Regenerating a formal skeleton from a
  Lean theorem and matching it against the citing statement therefore
  certifies STRUCTURE and cannot certify OWNERSHIP: for 12 of the 15
  translatable committed links, at least one other committed statement
  declares the very same skeleton, so a link that moved to the set-theory
  twin would still be CORRESPONDS. The property that makes this corpus
  valuable as an analogy graph is the property that makes structural
  correspondence insufficient as a proof gate. What actually keeps one
  claimant is the older, cheaper rule — `verified_by` theorems are
  exclusively owned — so the two checks are load-bearing together and
  neither is sufficient alone. `scripts/proof_correspondence.py` reports the
  claimants as `ambiguous_with`; the WRITE gate refuses to create new
  instances of the hole. *P-PW6 fired; PROVEN-gated WRITE* (2026-08-09)

- **`equivalent_forms` is a stronger claim than the corpus uses it for, and
  a proof gate reading it inherits the weakness.** A correspondence check
  cannot compare a Lean theorem only to `anonymized_template`: seven of the
  fifteen translatable committed links would be reported MISMATCH, six
  because they cite the DUAL law and one because it cites the bare
  `not(P and not P)` form. Every one of those forms is declared by the citing
  node, so the citations are honest and the naive gate is simply wrong. But
  admitting declared forms admits everything a node files there, and
  `logic.boolean_laws.double_negation` files the ONE-DIRECTIONAL
  `P implies not(not P)` as an "equivalent form" — so a theorem proving only
  that half would be accepted as proving the biconditional. The corpus has
  been using `equivalent_forms` as "related readings a human should see",
  and the first consumer that treats it as "forms this statement asserts"
  turns an editorial convenience into a soundness surface. Recorded rather
  than fixed: narrowing the field is a corpus-wide authoring decision, not a
  change one gate may make. *near-miss; PROVEN-gated WRITE* (2026-08-09)

- **A near-miss that preserves length is what makes a geometry check
  falsifiable.** The obvious way to break a right angle — nudge the leg
  endpoint sideways — also changes that leg's length, so the length check
  catches it too and neither check can be shown load-bearing. Replacing the
  leg direction `v = (-q, p)` with `w = (q, p)` keeps the squared length
  identical (`p² + q²`) in exact integer arithmetic while rotating by
  `2·atan(q/p)`, giving a 1.53°–16.26° near-miss that only the right-angle
  check sees. With one such construction per check, all six visual-oracle
  checks ablate into a unique escape: disable one, exactly one invalid class
  of 240 passes and the other five stay fully rejected. The general lesson is
  that a verifier's checks are only separately testable if the negative set
  is built to isolate them. *P-VO2/P-VO3 fired; visual oracle* (2026-08-09)

- **A corpus of well-formed inputs cannot audit a verifier's soundness
  argument.** The visual oracle's six checks ablate cleanly — disable one,
  exactly one invalid class of 240 escapes — across 1,680 instances. Review
  still found a figure all six accepted: an angle annotation referencing a
  nonexistent vertex, which round-tripped through the SVG and verified `ok`.
  A second construction made a check skip its relation, so ablating a
  *different* check let the graph pass. Both occur 0 times in the generated
  corpus, which is exactly why the corpus could not find them. The results
  were right and the argument behind them was not yet sound; only inputs the
  generator never produces separate those two states. Both are now refused
  as malformed at the door rather than added as checks, since no controlled
  class exercises them and a check without a class is decoration.
  *adversarial review; visual oracle* (2026-08-09)

- **A capability-blind control can pass by being blind.** The visual lane's
  "max coordinate" surface baseline ran its number regex over the whole SVG
  and matched the `2000` in `http://www.w3.org/2000/svg`. It returned the
  same constant for every figure and scored a clean 0.500 on all six invalid
  classes — apparently confirming that the negatives are hard, actually
  measuring nothing. Reading numbers only from numeric attribute values
  raised its best cell to 0.740. A baseline that scores at chance deserves
  the same suspicion as one that scores perfectly: both can mean the
  instrument never saw the data. *self-audit* (2026-08-09)

- **Synthetic recombinant pointing does not transfer to corpus
  specialization.** Forty real A:B::C:D rows span six source and six target
  disciplines but only five distinct targets in one ratio family. Every D is
  rechecked by the specializer. Symbolic resolution and a blind last-slot
  number-transfer rule both score 1.000; the released synthetic checkpoint is
  0.000 exact on the RHS residual. The lane demonstrates verifiable corpus
  construction, not learned analogy. *P-CA1–P-CA4 retrospective labels;
  post-review corpus-grounded evaluation* (2026-08-09)

- **Conversation memory needs revocation, not just attribution.** A signed
  answer remains authentic after the user changes their mind. The maintained
  user frame therefore keeps both answers as provenance while a verifier-
  private committed supersession ledger makes the old one non-current. A
  public `superseded` tuple alone is forgeable and deletable. *P-CR2 fired;
  authenticated mutable-session result* (2026-08-09)

- **Two private perspectives can share one story without becoming story
  facts.** Alice's silver eggs and Bob's blue eggs render from owner-isolated
  bindings over an identical accepted golden-chicken state; neither value
  enters `frame.asserted`. *P-CR1/P-CR3 fired; maintained user-frame demo*
- **An address can generalize while a learned consumer destroys it.** In a
  five-arm, three-seed paired matrix, recurrent address-only remains best at
  `0.196 ± 0.064` conditional depth-OOD exact. Recurrent query construction
  reaches `0.179 ± 0.025`; recurrent memory `0.082 ± 0.027`; putting recurrence
  in both consumers collapses to `0.039 ± 0.011`; a two-parameter-matched
  level-aware MLP recovers to `0.142 ± 0.014`. Every arm is still at ceiling
  in distribution. Teacher-forced diagnostics locate the damage: address-only
  averages 0.910 on C-leaf copy and 1.000 on EOS, while memory recurrence falls
  to 0.705 and 0.913; both consumers fall to 0.677 on C-leaf. Shared iteration
  helped construct the address, but transforming that representation again at
  its consumers erased information the pointer needed. *P-DC1–3 missed;
  P-DC4 satisfied; three paired seeds* (2026-08-09)

- **The safe GPU protocol preserved the experiment and rejected the crash
  state.** Two identical Windows bugchecks occurred at final evaluation with
  `nvidia-smi` reporting 15,760/16,303 MiB (15.39/15.92 GiB). The first safety
  prediction was retracted because its post-cache-clear allocated-tensor
  measurand could not observe that state. Its replacement used logical batch
  192, microbatch 64, evaluation batch 32, a 70% allocator cap, atomic
  artifacts, separate reserved/whole-device telemetry, and an 80% absolute
  device guard. All 15 rows completed; maximum whole-device footprint was
  6,387,466,240 bytes and evaluation added at most 2,097,152 bytes. This makes
  near-full GPU occupancy strongly implicated in the repeatable failure, not
  proven as its sole hardware/driver cause. *P-DC5 retracted; P-DC6/7 fired*
  (2026-08-09)

- **Raw source-byte provenance is newline-fragile across Windows checkouts.**
  The completed depth runs correctly pinned the exact runtime bytes, but a
  later rebase changed mixed LF/CRLF working-tree bytes into semantically
  identical uniform CRLF. The analyzer still requires an exact raw-digest
  match first; a reviewed `depth_source_manifest.json` may bridge only those
  recorded runtime hashes to the canonical-LF hashes at clean run commit
  `25db073`, and forged or missing bridges refuse. Future launchers should
  record Git blob ids or canonical text hashes alongside raw hashes before a
  run starts. *post-run provenance finding; fail-closed bridge with regression
  controls* (2026-08-09)

- **Held-out tactic classification does not guarantee a search gain.** Three
  27,688-parameter byte-GRU rankers all score 0.8125 on four theorem-held-out
  groups (frequency 0.4375; shuffled-label controls 0.25–0.375) and solve live
  in 71/63/61 proposals. The arbitrary palette needs 86, but the stronger
  state-blind frequency order needs only 64—one better than the learned mean.
  Two seeds win and one loses; no mean learned advantage survives. *P-TP1–4
  fired against registered controls; corrective P-TP5 refuted the live-gain
  interpretation* (2026-08-09)

- **An accepted proof step can be a dead branch.** In live Lean search,
  ``clear h`` is kernel-accepted after introducing a conjunction hypothesis,
  but removes the only evidence needed to build the reversed conjunction.
  Breadth-first search retains that accepted transition as branch evidence and
  reaches the proof through another branch. This is the first controller trace
  in which backtracking is load-bearing rather than simulated by rejecting a
  no-op. *P-LS2's first registered run missed; corrective P-LS6 fired and
  satisfied P-LS2's substantive accepted-dead-branch criterion; live verifier
  result* (2026-08-09)

- **Rendered proof-state names are not necessarily callable proof-state
  names.** The first blind palette exhausted because Pantograph's bare
  ``intro`` rendered ``P✝``, ``Q✝``, and ``h✝`` while ``h.left`` and
  ``h.right`` failed as unknown identifiers. The registered prediction stays
  missed; a subsequent prediction added the ordinary ``intro P Q h`` tactic
  and the same search closed the theorem. A proof UI's text is an observation,
  not a lossless action interface. *P-LS2 initial form missed; P-LS6 fired*
  (2026-08-09)

- **Split by provenance, the self-certificate is one constituent wide — and
  absorption, not sibling recurrence, is the graph-wide leak.** Attributing
  every grounded constituent to a channel leaves `data/provability`'s 1.000
  intact but resolves it into `same_corpus` 0.775 + `pattern_absorption`
  0.192 against `external` 0.033: five of six nodes take no external credit
  at all, and the sixth's is a single `IMPLIES⟨?0:V, ?1:V⟩` matching
  `logic.inference.contraposition`. It is the only corpus in 22 where a
  near-perfect aggregate survives with almost nothing from outside its own
  authoring act, though four other corpora are same-corpus-dominant
  (`morphology`, `narrative`, `temporal_logic`, `differential_topology`).
  The unpredicted half is larger: **62 of the graph's 75 pattern-absorption
  constituents absorb a pattern owned outside the absorbing statement's
  discipline**, so slot-swallows-structure is where cross-discipline-looking
  credit concentrates everywhere, not only in the modal corpus. Sharpest
  single case: `temporal.recurrence.until_unfolding`, whose v2 repair from
  0.000 to 1.000 is 3/3 absorption. The `recursive` channel, meanwhile, is
  empty across the whole graph. *GC1–GC5 all fired, including the named
  same-corpus guess; two unpredicted results recorded* (2026-08-09)
  **CORRECTED 2026-08-09 (independent review of the channel-split delivery).
  The text above is the entry as filed and is left standing; three of its
  claims do not survive.**
  1. *The absorption headline is RETRACTED.* "62 of 75" counts each absorbed
     pattern's MOST INDEPENDENT owner; with ALL owners outside the discipline
     it is 36 of 75, the other 26 carrying a same-corpus (25) or prior-corpus
     (1) co-owner. Worse, the inference drawn from it never ran its own
     baseline: the exact channel is 352 of 440 (80.0%) best-owner external and
     162 of 440 (36.8%) all-owner external — statistically a wash against
     absorption's 82.7% / 48.0% under either reading, and 5.7:1 larger by
     absolute count. **Absorption is not where cross-discipline-looking credit
     concentrates; it is where such credit is quarantined**, which was the
     design intent all along. The narrow fact survives (most absorbed patterns
     do have an out-of-discipline owner, and the aggregate silently claimed
     that provenance); the "graph-wide leak" reading does not, and the BACKLOG
     entry that called it "the measurement that would justify" gating the
     pattern channel is demoted accordingly.
  2. *The empty `recursive` channel is a DESIGN consequence, not a data
     observation.* `analyze` subtracts the statement from every owner set, so
     at `min_family >= 2` the only path into the channel — `best_channel`'s
     empty-tally fallback — is unreachable and no corpus of any shape could
     have landed there. (An `owner == sid` branch in `owner_channel` looked
     like the mechanism and took zero calls at every `--min-family`; it is now
     an enforced precondition instead.) The channel is reachable at
     `--min-family 1`: 200 constituents over 105 statements, mean 0.316.
  3. *"Four same-corpus-dominant corpora" is a LOWER bound, and every
     `external` share is an UPPER bound.* Exact constituents take their most
     independent owner and 190 of 440 are multi-owner — all 190 credited
     `external`. Under the least-independent rule graph external falls
     0.535 → 0.246 (352 → 162 constituents), `logic` 0.812 → 0.442, `algebra`
     0.143 → 0.000, and the same-corpus-dominant list grows from 5 corpora to
     12. `channel_summary` now publishes both bounds. The headline is
     rule-invariant: provability's external is 0.033 either way and it is the
     only corpus flagged `self_certifying` under either rule. *GC6 registered
     and fired* (2026-08-09)

- **Löb's axiom and temporal induction are one archetype and refuse to be
  one skeleton.** `provability.modal.loeb_axiom`
  (`IMPLIES⟨BOX⟨IMPLIES⟨BOX⟨?0:V⟩, ?0:V⟩⟩, BOX⟨?0:V⟩⟩`) and
  `temporal.induction.temporal_induction_axiom`
  (`IMPLIES⟨ALWAYS⟨IMPLIES⟨?0:V, NEXT⟨?0:V⟩⟩⟩, IMPLIES⟨?0:V, ALWAYS⟨?0:V⟩⟩⟩`)
  share `temporal_induction` in the drift report — both internalize
  induction along a well-founded step relation — and twin at no level.
  The trees differ in exactly the axiom that separates the logics: Löb
  discharges reflection (□p→p) only under a box, LTL validates it
  outright. A discipline-named archetype now spans a second
  discipline — by argued adoption in the seed, an authoring claim the
  drift report carries, not a tool-discovered fact; only the no-twin
  half is a matcher outcome. *P-CF4 fired, archetype-shared near-miss*
  (2026-08-08)

- **A six-node corpus can self-certify perfect groundedness on a head the
  graph has never seen.** Every `data/provability` node grounds at 1.000
  on arrival: BOX recurrence across sibling nodes counts as known form,
  and the pattern channel lets ex falso's `IMPLIES⟨?0:P, ?1:V⟩` swallow
  Löb's boxed premise whole. Registered prediction PV3 expected quarantine
  (no node at 1.000, corpus below graph mean) and was refuted in full —
  the groundedness rung fails open for dense new vocabulary just as it
  fails closed for self-referential axioms (until_unfolding, 0.000). On a
  corpus about the vacuity of self-certification, the ladder accepted a
  self-certificate. *PV3 refuted; measured defect in the graded rung*
  (2026-08-08)

- **Gödel's box and Sally's box now share a namespace.** The slot/head
  collision lint gained `box: slot BOX vs head BOX⟨...⟩` —
  `narrative.world.marble_moved_box` binds BOX as the marble's container
  constant while the provability corpus uses BOX as the provability
  modality. Harmless (slots never match heads) and kept: the lint doing
  its job across maximally distant disciplines. *lint working as designed*
  (2026-08-08)

- **False belief is a visibility result, not an authored contradiction.** The
  same placement and move events update world/Anne but the move is invisible
  to Sally, so her owned frame retains basket while world holds box and refutes
  basket. No new verdict was needed. *P-CF1 fired, executable ToM control*
  (2026-08-09)

- **Belief content can twin world content while scope carries the disagreement.**
  Sally's `LOCATION(MARBLE)=BASKET` and the world's
  `LOCATION(MARBLE)=BOX` share `?0:P = LOCATION⟨?1:V⟩`; owner and visibility
  are deliberately outside the matcher key. *exact content twin, scoped
  interpretation differs* (2026-08-09)

- **Scope generalizes across domains without implying template equivalence.**
  The rotating-physics frame and cartoon gravity both resolve to declaration
  nodes, suspend an ordinary physics law, and admit local premises. P-CF2
  nevertheless misses at every matcher level because the former is an
  additive correction and the latter a temporal response. The executor-level
  sameness and signature-level difference are both real. *near-miss,
  scope/template boundary* (2026-08-09)

- **Galilean velocity addition is rank decomposition in another vocabulary.**
  `OBJECT_VELOCITY = RELATIVE_VELOCITY + FRAME_VELOCITY` and algebraic
  topology's `CHAINRANK = CYCLERANK + IMAGERANK` share the exact typed skeleton
  `?0:V = +(?1:V, ?2:V)`. P-CF3 fired without respelling the standard law
  -- though neither of the prediction's NAMED candidates (convex
  combination, vector addition) matched: the class fired through a
  skeleton not on the candidate list, joining a previously-singleton
  node. The candidate miss is recorded beside the class hit, per house
  precision discipline. *exact, cross-discipline* (2026-08-09)

- **Waiting is a controller outcome, not a failed proof search.** A valid ASK
  records one signed question and stops the generic controller as WAITING;
  EXHAUSTED still means policy had nothing more to propose, and SOLVED still
  means the goal closed. A later run resumes the same immutable session state.
  *conversation control-plane distinction, executable* (2026-08-09)

- **User testimony can be locally attributable without becoming world truth.**
  The ASK return path records a signed `UserBinding` in a runtime-owned user
  frame and clears its exact UNKNOWN, but adds no frame assertion or corpus
  fact. The signature proves host-channel passage, not human identity or content
  correctness. *ToM entry boundary, 25 adversarial controls* (2026-08-09)

- **Proof provenance integrity is cheaper than proof correspondence—and must
  not be confused with it.** The merged validator can establish that an
  artifact is repository-contained and well formed, that a cited theorem
  exists, and that exactly one statement owns its identity. It cannot establish
  that the theorem proves that statement: a deliberately unrelated gravity
  node citing valid `BooleanLaws.modus_ponens` passes the lint. *governance rung
  shipped; semantic edge remains open* (2026-08-08)

- **Retrieval can advance state without promoting knowledge.** A VERIFIED
  RETRIEVE transition now means the exact store operation succeeded; its six
  De-Morgan results retain distinct statuses, including a derived corpus node,
  mechanically verified structural/decomposition records, and a PROVEN Lean
  artifact summary. The subsequent POINT binds an item id, not an invented
  truth. *harness invariant, executable* (2026-08-08)

- **A pointable address is not an answer certificate.** The first adapter
  allowed any retrieved position to clear any UNKNOWN; modus ponens could
  therefore “answer” a De-Morgan request. A first correction rechecked the
  pending key against item aliases, but review then showed that `a` is an exact
  alias in many unrelated lexica. POINT now additionally requires matching
  corpus/lexicon/proof views to resolve to one corpus owner. Ambiguous context
  remains retrievable but cannot answer. *two review-found vacuities,
  corrected* (2026-08-08)

- **UNKNOWN is a live frame judgment, not a session-start label.** A pending
  retrieval literal can become VERIFIED or REFUTED after an accepted frame
  assertion. Keeping only its original UNKNOWN evidence allowed a later POINT
  to clear a stale need. The adapter now retains and re-adjudicates the literal;
  a delegated action that resolves it records the VERIFIED/REFUTED result and
  clears the retrieval need. *state-transition invariant, review correction*
  (2026-08-08)

- **Exact-before-neighborhood is binding semantics, not just query order.**
  `Quadratic Formula` exactly names one node while neighborhood-matching
  another node's `quadratic form`. Owner disambiguation must therefore compare
  exact owners only when the selected material matched exactly. *retrieval
  precedence invariant, review correction* (2026-08-08)

- **Retrieval actions cannot rewrite the pending question.** Earlier controls
  allowed context fetched under `quadratic form` to approach a pending
  `Quadratic Formula`, relying on POINT to reject the wrong owner. The final
  contract is stronger: RETRIEVE itself refuses any key not canonically equal
  to the UNKNOWN literal's value; neighborhood widening is internal. *cross-
  query vacuity, review correction* (2026-08-08)

- **Proof retrieval must honor the proof-link schema, not today's examples.**
  Every current `verified_by` entry names a theorem reference, but the schema
  permits an artifact-only link. Review supplied that absent-reference case;
  the loader now counts the whole theorem-bearing artifact instead of
  crashing. *schema-boundary correction* (2026-08-08)

- **A proof link is not PROVEN until its artifact contains applicable proof
  transitions.** An empty JSON artifact is structurally present but supplies
  no machine-checked evidence; nor does an arbitrary file or a row containing
  only a theorem label. The loader now authenticates complete native JSON
  state–tactic–state rows, requires an applicable transition to close to `no
  goals`, requires artifact-only links to identify exactly one theorem, and
  fails closed on malformed evidence. But even a locally closing row may be a
  completed subgoal in a truncated extraction. PROVEN therefore additionally
  requires the existing SHA-256 identity of the committed native extraction;
  structurally valid untrusted artifacts remain VERIFIED. *epistemic
  fail-closed rule, review correction* (2026-08-08)

- **Short algebraic aliases are context, not word-completion prefixes.** A
  truncated `absor` query reverse-matched every lexicon containing `a`, flooding
  its neighborhood with unrelated owners. Reverse-prefix matching now requires
  at least three characters; exact single-symbol retrieval remains possible,
  but cannot masquerade as lexical completion. *neighborhood precision,
  review correction* (2026-08-08)

- **A retrieval key is part of the UNKNOWN, not free policy metadata.** The
  adapter initially allowed callers to pair any unresolved literal with an
  unrelated key, making relevance true only by assertion. Session construction
  now requires the key to be the unresolved literal's value. Retrieval is thus
  verified relative to parsed frame state; whether open language was parsed
  correctly remains a separate capability. *capability-blind correction,
  review-blocking* (2026-08-08)

- **Factory invariants must be verifier invariants when state constructors are
  public.** A caller could bypass the session factory and forge a key/literal
  mismatch directly in the frozen dataclass. RETRIEVE and POINT now recheck the
  relation at the action boundary. *extension-boundary correction* (2026-08-08)

- **Pointable context is a capability and needs provenance checking.** A public
  state constructor could inject a record with plausible aliases and ownership
  but an invented id. POINT now requires exact membership in the authoritative
  store snapshot before binding. *capability-boundary correction* (2026-08-08)

- **Closed-form exactness must preserve operators.** Lexical tokenization made
  multiplication and addition skeletons with the same slots look identical.
  Exact retrieval now preserves punctuation/operators and uses lexical tokens
  only for neighborhood search. *symbolic-equality correction* (2026-08-08)

- **Exact symbolic lookup does not require word tokens.** Operators and
  non-Latin symbols may have no ASCII alphanumeric token at all. Exact alias
  comparison now precedes the neighborhood-token gate. *symbolic-input
  correction* (2026-08-08)

- **Store membership is not retrieval provenance.** Public state could inject
  a genuine item without an accepted RETRIEVE step. Verifier-minted receipts
  now bind the session key, match mode, and admitted item ids; POINT requires
  both the receipt and authoritative membership. *transaction-integrity
  correction* (2026-08-08)

- **A receipt belongs to a session, not merely a verifier.** One verifier may
  host several same-key sessions. Receipt signatures now cover a per-session
  nonce, so admitted context cannot be transplanted between them. *replay
  correction* (2026-08-08)

- **A retrieval receipt belongs to a frame contract too.** Signing only the
  session allowed open-frame context to move into a `frame_local` scope.
  Signatures now cover the immutable `FrameSpec`, preserving its retrieval
  boundary. *scope-replay correction* (2026-08-08)

- **Short exact keys must not become prefixes.** The key `7` is not an answer
  request for `IEEE 754`. Prefix neighborhood matching now requires at least
  three characters on each side; exact short aliases remain exact-only.
  *neighborhood vacuity correction* (2026-08-08)

- **A proof trust root authenticates metadata and bytes together.** A
  byte-identical Lean extraction labeled as another proof system must not
  inherit PROVEN. The native adapter now accepts the pinned digest only with
  the canonical `lean4` system label. *provenance-integrity correction*
  (2026-08-08)

- **Action kind and transition name are both part of the verifier protocol.**
  Dispatching every RETRIEVE as lookup and every POINT as bind allowed unknown
  names to appear as successful audited operations. The adapter now refuses
  names outside its declared vocabulary. *trace-integrity correction*
  (2026-08-08)

- **The external store is load-bearing at the controller level too.** The
  deterministic RETRIEVE→POINT oracle solves with the 702-item local store and
  cannot solve against an empty store: UNKNOWN leaves context unchanged, POINT
  is REFUSED, and ABSTAIN is cited. This is the retrieval adapter's capability-
  blind baseline, not a model-quality result. *negative control* (2026-08-08)

- **One statement id can join five knowledge views without becoming five
  mechanisms.** Querying De Morgan's law returns corpus meaning, lexicon,
  typed/shape group records, decomposition, and native Lean transition counts
  through one interface; a truncated id reaches the same neighborhood only
  after exact lookup misses. *integration, exact + neighborhood* (2026-08-08)

- **Pointability needs source-aware identity, not one universal owner field.**
  Corpus, lexicon, and proof records resolve to a statement; a decomposition
  resolves to its owning statement; a twin-ledger skeleton may identify the
  group itself. Tiered attribution now lets unique report-only keys bind without
  weakening canonical statement precedence. *five-store integration, review
  correction* (2026-08-08)

- **Time reversal is a relation, not an alias.** Five predicted pairs now
  appear at a separately reported mirror level: UNTIL/SINCE,
  EVENTUALLY/ONCE unfolding, NEXT/PREV distribution, future/past duality, and
  response/heraldry. The ordinary shape/typed/family/aliased counts remain
  28/29/28/30, so the new relation adds knowledge without manufacturing an
  equivalence claim. *mirror, 5 groups, predicted-and-landed* (2026-08-08)

- **A mirror must reverse the whole expression, not quotient each head.** The
  first implementation falsely grouped partially reversed nested modalities;
  it also exposed that heraldry/no-deus had kept an outer `ALWAYS` while
  reversing only EVENTUALLY to ONCE. A whole-tree involution initially reduced
  the result to four groups; correcting the past formulas to HISTORICALLY
  restores the fifth. The original five-group implementation is retracted.
  *self-audit, review-blocking correction* (2026-08-08)

- **A response law does not imply its trigger's converse.**
  `G(notices -> F(falls))` does not entail `not notices -> not falls`; the
  scoped cartoon hover is therefore an independently assumed assertion, not a
  derived consequence of the declaration. The false reciprocal links were
  removed before commit. *self-audit, refuted* (2026-08-08)

- **Temporal boundaries are part of the theorem.** SINCE/ONCE unfolding is
  valid here only after fixing PREV to the strong convention (false at trace
  origin); the exact heraldry mirror is correspondingly inclusive because
  ONCE includes now. Strict “prepared earlier” remains a stronger executor
  constraint. Separately, premise persistence must assert `HOLDS(p)`
  positively—an implication from `HOLDS(p)` becomes vacuous at the moment the
  premise disappears. *self-audit, boundary conditions corrected* (2026-08-08)

- **The matcher no longer asserts that strict precedence is reflexive.** The
  false `BEFORE ~ LEQ` alias was removed, strict precedence now uses `LT`, and
  `HEAD_ALGEBRA` records `LT` as the strict part of `LEQ` (and `LEQ` as its
  reflexive closure). No prior twin membership moved, exactly as predicted.
  *self-audit, corrected* (2026-08-08)

- **Groundedness v2 still depends on what surrounds a recursive head.** The
  new SINCE and ONCE unfoldings scored 0.667 and 0.500 rather than the
  predicted 1.000: excluding self-headed constituents does not make their
  remaining compound constituents recognizable. Conversely the
  no-deus-ex-machina instance scored 1.000 rather than 0.500 because exact
  PLANTED/DISCHARGED recurrence and heraldry-pattern coverage ground all of
  it. *prediction missed, metric boundary* (2026-08-08)

- **Scope has its first corpus users.** Cartoon gravity is represented as a
  shared-scope declaration/assertion pair that suspends Newtonian gravity,
  while premise persistence declares a frame-local invariant. These are the
  first authored nodes to exercise the already-live scope validator rather
  than leaving frame semantics in prose. *schema exercised* (2026-08-08)

- **Coulomb's law is Newtonian gravitation.** Same typed skeleton
  `?V = ?P·?V·?V / ?V²` — inverse-square pair coupling; only the names of
  the charges differ. *exact* (2026-08-06)

- **The quantity theory of money is the ideal gas law with its dimensional
  constant suppressed.** `M·V = P·Q` ⊑ `P·V = n·R·T` with bindings
  MONEY→PRESSURE, VELOCITY→VOLUME, PRICE_LEVEL→AMOUNT,
  OUTPUT→CONSTANT·TEMPERATURE. *specialization* (2026-08-07)

- **Compound interest, population growth, and radioactive decay are one
  law.** `?V = ?P·EXP(?P·?V)` after absorbing the decay sign into the free
  rate parameter; at the sign-exact level the family splits into exactly
  the two semantically correct pairs (compounding↔growth,
  discounting↔decay). *family* (2026-08-07)

- **Hooke's law joins Newton's second law, Ohm's law, and circle
  circumference** as one scaled-linear response family once its restoring
  sign is absorbed into stiffness. *family* (2026-08-07)

- **The laws of logic and the laws of sets are one Boolean algebra.** All
  seven lattice laws (De Morgan, distributivity, involution, absorption,
  identity, complement, idempotence) are exact twins over two carriers,
  recorded as reciprocal equivalences. *exact* (2026-08-07)

- **Shannon entropy is Gibbs entropy.** One skeleton
  `?V = −(?P · Σᵢ ?Vᵢ·log ?Vᵢ)`; Boltzmann's k_B and information's 1/ln 2
  land in the same parameter slot — the disciplines differ by a unit
  choice. *exact* (2026-08-07)

- **pH is the surprisal of proton activity.** `pH = −log(activity)` and
  `surprisal = −log(probability)` are typed twins — chemistry has been
  measuring an information quantity all along. Unplanned; found because
  both corpora made honest independent slot declarations. *exact*
  (2026-08-07)

- **A tangent-line linearization is an affine location-scale transform.**
  Calculus's local approximation and statistics' standardization are one
  structure `?V = ?P + ?P·?V`; CAPM and the Keynesian consumption function
  are members too. *exact* (2026-08-06/07)

- **Rate-of-change, speed, density, molarity, and elasticity are one
  ratio archetype** across calculus, physics, chemistry, and economics.
  *exact* (2026-08-06/07)

- **Entropy inclusion-exclusion is set-cardinality inclusion-exclusion**
  (Yeung's I-measure): `H(X∪Y) = H(X)+H(Y)−H(X∩Y)` matches
  `|A∪B| = |A|+|B|−|A∩B|` exactly. *exact* (2026-08-07)

- **Beer-Lambert absorbance generalizes the whole scaled-linear family**
  (set absorptivity to 1) and typed-twins triangle area — a scaled
  bilinear product is one thing whether it measures light attenuation or
  plane regions. *specialization / exact* (2026-08-07)

- **E = mc² is a geometric scaled-quadratic with the roles swapped.** It
  shape-twins circle area / sphere surface (`? = ?·?²`), but the squared
  quantity is the *constant* — the typed layer correctly refuses the
  identification while the shape layer records the kinship. *shape*
  (2026-08-06)

## Informative near-misses (kept deliberately)

- **Our headline depth number was a lucky seed, and pretraining is a
  stabilizer, not a lever.** Running the cold recurrent arm at seed 1
  (0.087 OOD) retired "0.226" as a point estimate: the honest 2-seed
  statement is 0.16 +/- 0.07 (fork verdict intact -- both seeds beat
  lookup/curriculum by an order of magnitude). Masked-skeleton
  pretraining (10e) collapsed that seed spread to 0.029 and lifted the
  weak seed +0.100 while leaving the strong seed roughly unchanged --
  gains the no-single-seed rule can call variance stabilization but not
  mean improvement at n=2. *P-CF5a partial, P-CF5b fired; single-seed
  rule applied to our own result* (2026-08-09)

- **Textbook mutual information does not twin its own I-measure form** —
  call heads are read literally. Shows precisely what adopting a shared
  abstraction (lattice heads) buys. (2026-08-07)

- **Inclusion-exclusion does not twin total probability.** Applying a
  non-idempotent functional (CARD) to idempotent lattice operations is
  what *manufactures* the correction term — the deliberate counterweight
  to idempotence. (2026-08-07)

- **Uniform entropy = Shannon at p=1/N is invisible to the matcher** —
  collapsing a sum is a rewrite, not slot absorption. Same substitution
  takes Gibbs to Boltzmann's S = k·ln W. First motivated test case for a
  rewrite-edge engine. (2026-08-07)

- **Modus ponens does not twin subset transitivity** — same detachment
  shell, different premise heads; LEQ chosen so hypothetical syllogism
  will twin for free when authored. (2026-08-07)

- **Word concatenation correctly refuses the logarithm analogy.**
  `LENGTH(CONCAT(A,B)) = LENGTH(A)+LENGTH(B)` and `LOG(X·Y) = LOG X + LOG Y`
  are both monoid homomorphisms — but the matcher will not twin them,
  because CONCAT is ordered and `·` commutes: the free monoid of morphs
  and the multiplicative reals are different structures sharing only an
  archetype. A refusal that encodes real mathematics. *near-miss*
  (2026-08-07)

- **The derivation/inflection distinction survives total anonymization.**
  `CATEGORY(CONCAT(STEM, X)) = CATEGORY(STEM)` vs `= CATEGORY(X)` differ
  in one argument index after every symbol is erased — the grammar
  distinction is pure structure. *exact-distinction* (2026-08-07)

- **Word-level and phrase-level recursion are one skeleton apart**
  (registered prediction): iterated affixation `CONCAT(CONCAT(s,x),y)`
  and intensifier nesting `MOD(MOD(a,i),j)` differ only in head string —
  authoring the MOD node makes the discrete-infinity-at-every-level
  claim mechanically checkable, pending head aliasing. *prediction*
  (2026-08-07)

- **Counting, entropy, Euler characteristic, and area are one law.** The
  inclusion-exclusion skeleton `CARD(JOIN(A,B)) = CARD(A)+CARD(B)−CARD(MEET(A,B))`
  fires as a typed twin across set theory, information theory, algebraic
  topology, and geospatial topology — four valuations on lattices,
  differing only in what they count; modularity is the only property the
  identity uses. *exact, 4 disciplines* (2026-08-07)

- **The Fundamental Theorem of Calculus is Stokes' theorem in dimension
  1** — the 0-form Stokes case and FTC's evaluation part share one typed
  skeleton, found by the matcher rather than asserted. *exact* (2026-08-07)

- **The flat metric line element is the Pythagorean theorem.**
  `ds² = du² + dv²` typed-twins `a² + b² = c²` — differential geometry's
  local statement is the school theorem. *exact* (2026-08-07)

- **Betti alternating sums are total-probability decompositions** (with
  a caveat: the (−1)^i signs collapse into the same parameter slot that
  holds probability weights — structural kinship, semantic distance
  recorded). *exact-with-caveat* (2026-08-07)

- **χ = 2−2g shape-twins the thermodynamic free energies** and joins the
  affine family only after sign absorption — correctly, since
  χ-decreasing-in-genus is a convention. *family/shape* (2026-08-07)

- **A prediction formally cashed:** seed_logic fixed the LEQ head so
  future transitivity statements would twin for free; geospatial
  containment transitivity fired against subset transitivity with the
  target defined before the source existed. *exact, predicted*
  (2026-08-07)

- **The plainest specializations are provably invisible to specialize.py**
  (near-miss upgraded to load-bearing): Euler's polyhedron formula IS
  combinatorial χ at χ=2, and DE-9IM disjointness IS the complement law —
  match() succeeds on both, the requires-absorption filter drops both.
  Direct probes on record. (2026-08-07)

- **GRPO's advantage is the z-score.** DeepSeek's 2024 group-relative
  advantage `(R − mean)/std` fired as an emergent typed twin of
  probstat's z-standardization — frontier RLHF machinery is a
  century-old statistical transform. *exact* (2026-08-07)

- **LLM sampling is exponential decay.** The Boltzmann/softmax factor
  joins the family of radioactive decay, compound interest, and
  discounting (5 nodes, 4 disciplines) — temperature sampling and
  half-lives are one parametric family. *family* (2026-08-07)

- **The PPO probability ratio is a rate.** It joins rate-of-change,
  speed, density, molarity, and elasticity — the ratio family now spans
  6 nodes in 5 disciplines including RL. *exact* (2026-08-07)

- **Linear regression generalizes the Mamba/S4 state update.** SLR ⊒
  the linear SSM recurrence with intercept→0 and the noise slot
  absorbing the transition term — the 1900s statistical model contains
  the 2020s sequence architecture. *specialization* (2026-08-07)

- **Affine location-scale generalizes LoRA.** `W = W₀ + s·BA` is the
  statistics transform with the scale factored low-rank. *specialization*
  (2026-08-07)

- **Gradient descent shape-twins the free energies** and typed-twins the
  KL-regularized RLHF objective — optimization steps and thermodynamic
  potentials share the value-minus-scaled-quantity skeleton. *shape/exact*
  (2026-08-07)

- **The type system sees the gating innovation.** mLSTM does not twin
  the SSM precisely because its gates are variable-like where SSM
  coefficients are parameter-like — the matcher's refusal isolates
  exactly what xLSTM added. Likewise gradient descent misses the affine
  family by one slot category: descent updates a variable, affine
  shifts by a parameter. *near-miss, load-bearing* (2026-08-07)

- **Statements are now readable as constructs of named forms**
  (derivational composition, scripts/decompose.py): 135/151 statements
  decompose into known constituents; 117 contain a constituent that IS
  another statement's expression side. The SSM update reads out as two
  scaled-linear constituents (the Ohm/circumference form, recurring in
  28 statements) joined by +; the Euler-characteristic surface formula
  contains Hooke's law's expression side; the valuation identity's
  constituents are the other valuation statements. Commitment #1 of the
  concept-token design — forms as constructs of forms — is mechanical.
  *derivational* (2026-08-07)

- **Gradient descent is Euler's method** — explicit Euler on the gradient
  flow, fired as a family twin; every training loop runs 1768
  mathematics. Newton's method *correctly* misses the family: its inv()
  is the second-order information, isolated by the refusal. *family +
  near-miss* (2026-08-07)

- **The trapezoidal rule is the trapezoid area formula** — exact typed
  twin across numerical analysis and geometry; the quadrature rule IS
  the shape it sums. *exact* (2026-08-07)

- **Bézier evaluation, barycentric reconstruction, total probability,
  and Betti sums are one weighted-sum law** (4 disciplines). *exact*
  (2026-08-07)

- **Newton's correction term is a rate** — invisible to whole-statement
  twinning, read out by decomposition as the ratio family's expression
  side (11 statements). And fixed-point iteration vs Brouwer's theorem:
  two tools, one pair, opposite correct answers (shared constituent,
  provably not twins). *derivational* (2026-08-07)

- **Time is an order structure.** Temporal precedence transitivity
  typed-twins subset transitivity and geospatial containment
  transitivity — before/⊆/within are one law across three disciplines.
  *exact (authored-to-match convention, surviving three corpora)*
  (2026-08-07)

- **Fiction obeys logic.** The narrative frame-consistency law
  typed-twins the machine-checked Boolean complement laws — story
  coherence IS non-contradiction, so the fictional-frame design
  inherits a proven theorem rather than a style rule. *exact*
  (2026-08-07)

- **Frame axioms and their first executor are implemented; full temporal logic
  is not.** The corpus already
  contains the story sequence, its setup/complication/resolution decomposition,
  narrative causality, Chekhov-style liveness, and frame consistency. The
  matcher already connects the last two to temporal response and Boolean
  non-contradiction. The runtime now opens schema-declared scope, evaluates
  declarations/assertions against a frame-local ladder, and prevents local
  truths from leaking on exit. Its next cut makes Chekhov's law executable as
  finite obligation accounting: a visible plant registers one element, only a
  matching discharge closes it, and a frame with an outstanding element
  REFUSES to close. The first implementation's hidden ledger passed without a
  plant in the rendered setup; the vacuity audit caught that, so story plants
  must now alter the visible beat and discharges must cite resolution text.
  Independent review then found late/unrelated plants and prose duplication on
  repeated plants; plants are now setup-only, evidence names the bound element,
  and idempotence covers both symbolic and rendered state.
  This evaluates the authored future-facing law at frame close; it is not a
  general LTL checker and does not enforce the unauthored past converse. The
  machine anchor remains structural — the matching Boolean law has a Lean
  proof — rather than a claim that story execution itself is Lean-proved.
  *status progression: declarative layer + scope executor + finite Chekhov
  obligations shipped* (2026-08-08)

- **One controller can carry a real proof trace and a story trace, but that is
  an interface result, not learned generalization.** A deterministic sequence
  policy drove the same bounded propose/verify/repeat loop through three
  contiguous state–tactic–state transitions from the committed Lean extraction
  (`intro hp`, `left`, `exact hp` → `no goals`) and through setup, complication,
  and resolution for the golden chicken. Negative controls were load-bearing:
  unrecorded tactics, altered Lean state, out-of-order beats, and a silver-trait
  contradiction all fail; a rejected story branch leaves no premise behind and
  a valid branch recovers. The remaining boundary is explicit: replay is not
  PyPantograph search, the story adapter is a small executable subset of the
  frame design, and no weights chose an action. *oracle integration baseline,
  16/16 contract tests, including mutable extension boundaries and adversarial
  epistemic-status inputs* (2026-08-08)

- **Temporal duality is the infinitary De Morgan.** ALWAYS/EVENTUALLY
  are MEET/JOIN over suffix chains; the twin is blocked by heads and
  arity but carried honestly on the shared archetype. *near-miss,
  channeled* (2026-08-07)

- **Idempotence and involution differ by a fixed point, not a head.**
  ALWAYS(ALWAYS(P)) keeps its base where NEG(NEG(P)) cancels — the
  matcher's refusal isolates the semantic distinction exactly.
  *near-miss, load-bearing* (2026-08-07)

- **An instance can grade less grounded than its pattern.** Chekhov's
  gun (0.000) vs its own response-pattern abstraction (0.500):
  instantiated heads hide pattern membership — a measured groundedness
  pathology, filed with the recursive-definition self-reference case
  (until-unfolding, 0.000). *pathology* (2026-08-07)

- **Consequence, subset, containment, and precedence are one law.**
  Hypothetical syllogism joined the transitivity family — four
  disciplines whose carriers share nothing but a partial order,
  categorically different from the Boolean twins (one algebra read
  twice): here the shared thing is only the order axioms. *exact, 4
  disciplines, predicted-and-landed* (2026-08-07)

- **Mixture distributions, linear interpolation, and de Casteljau are
  one convex combination** (3 disciplines) — and the same node's
  K-component spelling belongs to the *weighted-sum* family instead:
  the sharpest measured case of spelling-dependent twin membership,
  since both spellings match, just not each other. *exact + pathology*
  (2026-08-07)

- **The zero morph lands where a linguist would put it.** With CONCAT's
  declared identity (∅ from zero_morpheme_identity), iterated
  affixation specializes to plain affixation via the INNER position —
  `CONCAT(CONCAT(stem, ∅), suffix)` — the matcher independently
  choosing the linguistically standard analysis over the registered
  prediction's outer-position guess. *specialization, looseness 0*
  (2026-08-07)

- **The Boolean corpora gain their first specialization structure**:
  absorption ⊒ idempotence via JOIN's identity element (BOT), two edges
  cross-corpus — the lattice laws now relate derivationally, not just
  as twins. *specialization* (2026-08-07)

- **The audit caught our own table asserting a falsehood.** The
  order_le alias class (BEFORE~LEQ) declares a reflexive order that
  strict_precedence_asymmetry makes asymmetric — deriving ⊥ at x = x —
  inert only because the class yields zero groups. Found by the scope
  design's measurement pass; fix queued (LT strict head, the
  strict/reflexive relation into HEAD_ALGEBRA). The epistemic ladder's
  REFUTED rung, applied to the tooling itself. *self-audit* (2026-08-07)

- **WordNet increases lexical reach without acquiring epistemic authority.**
  P-CF6 fired on its capability-blind control. Eight request terms absent from
  the five committed retrieval stores (0/8) reached their expected corpus
  owner through Open English WordNet same-synset aliases (8/8). This was
  context expansion only: the frame executor's UNKNOWN verdict/evidence
  changed 0/8 times across the real verifier path, and an injected mutation
  was detected 8/8. WordNet records stayed `empirical` beside formal/proven
  neighbors. Safe binding was 7/8: the two senses supporting `perseverance` →
  `persistence` remain context until disambiguated. The useful boundary
  is sharper than “add a dictionary”: lexical coordination can propose where
  to look without becoming evidence that the pointed formal statement is
  true. *retrieval / epistemic boundary* (2026-08-09)

- **A compound expansion needs no counterpart vocabulary, because the source
  statement is already in the input.** v0.6's analogy lane refused compound
  specialization bindings on the grounds that leaves like `MASS` in
  `*(MASS, ^(SPEED, 2))` have no image in the target statement's vocabulary,
  and inventing one is inventing vocabulary. That framing was the whole
  limitation: B sits in the input beside A and C, so those leaves are pointable
  where they stand, and the target only needs the leaves the twin alignment
  covers to be translated. Replacing the argument with a literal gate — every
  token of D must occur in `A <sep> B <sep> C` — took the lane from one family
  and five targets to **11 families and 398 targets, 376 of them carrying a
  compound expansion**, and the same gate then answered two questions nobody
  had asked it: head-identity collapses are inadmissible (the collapse removes
  the element from B, so it exists only in `HEAD_ALGEBRA`), and B's
  identity-free form beats the re-substituted `*(1, …)` because a `1` the
  matcher supplied is not pointable either. *analogy / representation*
  (2026-08-10)

- **The residual in the grounded analogy lane is a declared slot class, not
  difficulty.** A symbolic solver reading only the token stream reaches
  0.458 / 0.545 / 0.651 exact across the three holdouts. Handing it exactly two
  corpus declarations — each slot's parameter/variable class and the identity
  table — takes the SAME solver to 1.000 on all three, because
  `specialize.Search` gates its arithmetic-identity rule on the class being
  `P`, which no reader of the tokens can recover. This falsified the registered
  P-CS2 ("closed-form from the input alone") in the useful direction: the gap
  between a token reader and a closed form is nameable and small, so the lane
  measures the pointing mechanism and a model result from it may never be
  reported as reasoning. *analogy / closed forms* (2026-08-10)

- **Our own family holdout leaked through the quotient we chose to name it
  with, and the leak WAS the ceiling.** Families are the matcher's TYPED
  skeletons, so `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)` are two families and one
  head/arity shape. Splitting the strongest blind control on that single bit:
  nearest-template replay scores **1.000** on held-out rows whose untyped shape
  is still in training and **0.106** where it is not, and the family holdout's
  headline 0.400 decomposes exactly as `51/155 × 1.000 + 104/155 × 0.106`. The
  discipline holdout's 0.932 is the same effect at 162 of 176 rows. The strict
  ceiling is ≈0.10–0.14. Recorded rather than repaired: an untyped-shape
  holdout is queued, not substituted, because re-rolling a split against a
  ceiling you have already measured is how a lane launders its own result.
  *analogy / split design / self-audit* (2026-08-10)

- **"Distinct families are non-isomorphic" is a tautology when family is
  defined by the isomorphism.** Two of this branch's tests were written to
  check the roadmap's "at least three non-isomorphic structural families" and
  both were initially vacuous — the first because it compared typed keys to
  themselves, the second because its independent witness keyed on operator
  heads and `*` is n-ary after canonicalization, so a two-factor and a
  three-factor product read as one shape. Only the arity-aware, class-blind
  witness can fail, and it is the one that exposed the P-vs-V collision above.
  A test of a definition needs a coarser instrument than the definition.
  *methodology* (2026-08-10)

## v0.8 — open prose, WRITE acceptance, and two honest negatives (2026-08-10)

- **A presence check is not a moved-fact control.** The first open-prose
  faithfulness gate verified that every accepted anchor word was present plus a
  narrow foreign-color scan; independent review built four renderers (added false
  premise, right-color/wrong-owner, negation, dropped beat) that all certified as
  faithful. The teeth only appear with a *closure* check: the prose must tile
  completely into approved fact-segments and cover exactly the accepted kinds,
  and ordering + plant-before-discharge must hold. Then all four adversaries — and
  temporally-scrambled renders — are caught. *(scripts/prose.py)*
- **A durable write is safe only when it is atomic, rolls back to byte-identity,
  and asserts a whole-tree delta of exactly the declared files.** PROVEN-WRITE's
  first acceptance path passed an adversarial review with no escape, but the
  robustness gaps it surfaced — non-atomic writes, a rollback flag set too late to
  clean a torn corpus, a receipt outside the rollback guard, and a data/-only
  after-check — are the difference between "detection" and containment.
  *(scripts/write_stage.py)*
- **On genuinely unseen structural shapes, a trained pointer matches a blind
  edit-distance replay and no more.** The corpus-analogy model arm scores
  0.104 ± 0.012 on the strict 0.1069 shape holdout — it clears no blind ceiling on
  any holdout. The residual this lane can learn on unseen shapes is not there;
  more parameters on the same distribution will not change that. *(experiments/ANALYSIS.md)*
- **The depth wall is an early-token failure, not a truncation artifact and not a
  deep-tail collapse.** Enlarging the copy interface budget does not move
  untruncated OOD (the 550 previously-excluded rows still score 0.0 — their targets
  exceed any budget the model trained on), and 0.751 of retained first-decode
  errors land in deciles 0–2. The interface, not the budget, is the object of
  study. *(experiments/depth_interface.py)*

## v0.10 — the verifier, the inert middle, and a baseline that scaled badly (2026-08-13)

*Process note, recorded because the drift audit caught it: **v0.9 shipped
without adding a section here.** Its findings live in `RELEASE-v0.9.0.md` and
`experiments/ANALYSIS.md` only. That gap is left as-is rather than
reconstructed from memory; this section covers v0.10.*

- **A capability-blind baseline can win on count and lose on precision, and
  scale separates the two.** At 221 curated nodes the operator bag simply
  beat the matcher on pair count. At 508 nodes with 251 ingested, the bag
  forms 7,622 pairs to the matcher's 96 — and its precision *falls* from
  2.03% to 1.26% (0.54% on ingested-only pairs) while the matcher's stays at
  1.0. More data made the blind baseline louder and worse, not better.
  *(experiments/ANALYSIS.md, item 4)*
- **Fully ground statements are inert in every ledger role.** They are not
  specialize generals (no slots to bind), not specialize specifics, and not
  decompose patterns. Their only structural participation is the subterms
  they share. A corpus of ground identities therefore grows coverage and
  same-corpus grounding while adding nothing to the generalization lattice.
  *(scripts/specialize.py, scripts/decompose.py; v0.10 item 4 design)*
- **`specialize.py` is quadratic in slot-free templates.** 68 first-wave
  templates with 8–30 operators ran 87 minutes without writing a report on
  the 508-node graph, because a slot-free tree enumerates commutative subsets
  against every other node and can only produce noise. Skipping slot-less
  candidate generals restores it to 0.41s with the 713 pre-ingest edges
  identical. *(docs/BACKLOG.md, v0.10 item 4)*
- **Ingested statements ground each other, and it showed up twice
  unprompted.** A second ingested statement was enough for the ledger to
  record it and the first grounding a shared `2 ^ 30`; 251 more produced 614
  `same_corpus` constituents inside the new corpus and a third owner for the
  same subterm. Both times the registered prediction expected denominator
  dilution instead. Not yet measured against a null.
  *(docs/DESIGN-self-grounding-ingestion.md)*
- **`%` on ℕ decides without `propext`; `∣` needs it.** A prediction that
  carried one statement's axiom footprint over to a different operator was
  wrong in the direction that makes the certificate stronger (empty axiom
  set). Name the set, not the direction.
  *(prover/verifier-verdicts/lean_workbook_22080.lean4.json)*
- **An audit hook that reads only `open`'s mode is not a write boundary.**
  The mode is `None` for every low-level open — `os.open`, `_io.FileIO`, and
  CPython's own bytecode writer — so a sandboxed check wrote `__pycache__`
  into the repository while reporting PASS. Read the flags too.
  *(scripts/_verifier_sandbox.py)*
- **A build directory inside a scratch tree is a performance bug with a
  correctness face.** `lake` materialises a 3 GB, 14,748-file toolchain copy
  under `prover/`, which the WRITE gate then copies per test and hashes twice
  per class: 13 tests went from 26s to 1394s, and a lean run touching it
  mid-class tripped the working-tree guard with a change no candidate had
  made. *(scripts/write_stage.py, SCRATCH_IGNORED)*
- **A guard that moves whenever the corpus succeeds is measuring the corpus.**
  The absorption rate-gap pin moved four times (0.164, 0.156, 0.159, 0.490);
  the last jump was self-grounding ingestion dropping the exact channel's
  external *rate* while its *count* grew. Retired in favour of the count
  floor, which strengthened to 5.31:1.
  *(tests/test_decompose_channels.py)*
- **Exhaustive bounded enumeration finds the transitions nobody thought to
  test.** The first two closures surfaced two unstated properties of the
  committed story world: `plant`/`discharge` never read their `desire`
  argument (routes differing only in desire converge), and re-planting an
  already-planted element is accepted idempotently (routes of length n and
  n+1 converge). Twelve convergence cells, all explained by those two
  mechanisms; equal end bytes demonstrate commutation on those cases, not
  narrative meaning. *(reports/closures/story.golden_chicken.closure.json)*
- **A world whose whole vocabulary is refusals closes honestly as one state.**
  The visual world''s six committed mutations exist to be caught, so its
  closure is one state and six named refusal edges - and four corruption
  classes are inapplicable there for want of an accepted edge or cell.
  Reporting the inapplicability is the control''s honesty, not its failure.
  *(reports/closures/visual.rt0000.closure.json)*
- **A provenance graph can carry real information and still not price a
  radius.** 0 of 100 degree- and kind-preserving shuffles reproduce the
  audited coverage, yet the true closures overflow their 3x caps.
  Information and precision are different capabilities, and a blind
  control only tests the first. *(reports/radius/, blind_control.json)*
- **Published claims cite numbers, not artifacts.** The two claims no
  frozen scan rule could reach quote only derived decimals - a pin
  history like "0.164, 0.156, 0.159, and then 0.490" - with no lexical
  trace of the ledger they came from. Retrospective lineage over prose
  has a floor; citation discipline at authoring time is the successor.
  *(data/retraction_closure/ground_truth_root_b.json, b12/b16)*
- **A claim about the graph is a claim in the graph.** Committing the
  adjudication registration - which names both root ledgers - added one
  claim node to each root''s radius before the run. Self-reference is
  not a paradox here; it is the object working.
  *(docs/DESIGN-retraction-closure.md section 6a)*
