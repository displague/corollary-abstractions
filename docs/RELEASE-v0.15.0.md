# v0.15.0 — the negative got a receipt

The cycle's rule was written on its first line: anything computable from
committed sources is computed before anything measurable is measured. Both
headline items obeyed it, and both paid out in the same currency — a *no*
you can hand to someone. A sealed closure now answers "that state is not
reachable within this horizon" as a checkable claim instead of a timeout,
and the cross-field veto's first adjudication found that its discrimination
rests on one domain judgement, which is a smaller and more checkable thing
than the table it lives in.

**Links** — previous release: [v0.14.0](RELEASE-v0.14.0.md) · closed plan:
[ROADMAP-v0.15](ROADMAP-v0.15.md) · next plan:
[ROADMAP-v0.16](ROADMAP-v0.16.md) · findings:
[DISCOVERIES](DISCOVERIES.md) · post:
[one row was carrying the table](blog/one-row-was-carrying-the-table.md)

## The headline finding

**Before.** A reachability question could only be answered by searching, and
a search that finds nothing proves nothing: "no path found" and "gave up"
were the same observation. v0.13 chose the direction and v0.14 deferred it.

**Now.** Two committed worlds — the story-frame world and the right-triangle
diagram world — were compiled into complete bounded possibility spaces
before any target was chosen, under a preregistration (`9fa4cba`) that
committed the schemas, the frozen world registrations, the generic checker,
and the full twelve-class corruption battery **before the builder existed**
(four gate tests red by construction). The builder landed after, with its
own independently written traversal, and matched the checker byte-for-byte
on the first run. All six registered gate clauses fired:

| clause | verdict | deciding number |
|---|---|---|
| B1 two real worlds register | fired | 2 committed worlds, 0 invented |
| B2 blind closure finishes inside frozen ceilings | fired | 75 states ≤ 512; 20 actions/state ≤ 32; 0.014 s ≤ 30 s; 450,040 B ≤ 8 MiB |
| B3 checking is complete | fired | 74/74 predecessor witnesses; cells recomputed identically |
| B4 corruption is always caught | fired | 90/90 applicable mutations rejected with a named first disagreement; 0 false rejections |
| B5 the abstraction is shared | fired | 0 world-name literals in builder/checker/corruptor; byte-identical rebuilds |
| B6 composition is exercised | fired | 12 convergence cells against the required 4 |

**Demonstrate.** Ask the sealed story closure about one exact endpoint —
the committed receipt is `reports/closures/story.golden_chicken.demo-receipt.json`:

```
python scripts/closure_query.py reports/closures/story.golden_chicken.closure.json target.bytes
```

With a committed depth-5 state's canonical bytes as the target, the answer
is `REACHABLE` with a five-action shortest route **replayed through the
world's own verifier** before being printed. Change one word of that state
— an obstacle the world never registered — and the answer is
`NOT_REACHABLE_WITHIN_HORIZON`, with the bound stated in the same breath:
75 states visited, horizon 5, nothing claimed about longer routes. That
sentence is the point of the whole item: the negative is now a property of
a sealed, independently checked object, not of a search that got tired.

### The instrument found something nobody asked it for

The design required at least four convergence cells (two routes, same end
state) as proof the closure exercises composition. It found twelve, and
decoding them surfaced **two properties of committed code that no test had
ever stated**: the story world's `plant` and `discharge` transitions never
read their `desire` argument, and re-planting an already-planted element is
accepted idempotently. The demo receipt shows the first one live — the
route's `introduce` carries *"to sing the sunrise awake"* while both
`plant` actions carry *"to out-crow the rooster"*, and the world accepts
the arc. Equal end bytes demonstrate only that the registered operations
commute on these cases, not anything about narrative meaning — but
"desire-blind and re-plant-idempotent" is now a demonstrated fact about
`oracle_controller_demo.py` + `frames.py`, surfaced by exhaustive bounded
enumeration rather than by anyone thinking to test it.

## Roadmap triage

**Shipped.**

- *Item 1 — compile the space before asking the question.* Preregistered,
  built, independently checked, adjudicated: six gates, six fires. The
  headline above. Full readout: ANALYSIS "the bounded closure: built,
  independently checked, all six gates fired".
- *Item 3 — make the gate affordable without weakening it.* Both lanes.
  The check order in `write_stage` was registered before the move
  (`afafbc4`), then reordered (`82aef3e`): all 103 tests keep their refusal
  identities, the worst test fell 1,096.4 s → 46.2 s, the module
  12,522.5 s → 10,770.9 s. The split fixture became module-scoped
  (`fa0a174`): six duplicate 179-second corpus builds removed by
  construction, every pinned control number byte-identical. The trust
  boundary held — no candidate reaches a check it previously never
  survived to, and the tests prove it by asserting *which* check refused.

**Shipped as a partial, suspension extended.**

- *Item 2 — the coincidence veto, adjudicated once.* Registered order held:
  inventory (26 groups, 77 aligned slots) before tags, blind control before
  flags. The name-difference control passed (0.3958 agreement against the
  0.80 drop bar); 22 of 77 slots flagged conflicting, inside the registered
  20–60 band; all four named directional calls held, including the one the
  v0.14 blog put in print (circle circumference against Newton's second
  law: conflicting) and the one that mattered for honesty (Boolean/set
  groups: unjudged, as declared on their merits beforehand). But the third
  control — tag permutation — is **invalid by an authoring-time scoping
  defect**: the incompatibility table only covers pairs that co-occur under
  the authored tags, so permutation starves it by construction. The tags'
  information claim stays unestablished, and the suspension on the
  published cross-field match count is **extended, not lifted**. What a
  sensitivity analysis found instead is in "What changed" below.

**Drift audit** (v0.13 and v0.14 re-read, per the rule):

- The v0.13 ambiguity acceptances **A3, A4, A5** — verbatim restatement,
  the Buffalo-class bar, coverage-does-not-pay — vanished when v0.14
  re-scoped the lane to `when_to_ask`, without a recorded decision. That is
  attrition, and this release converts it to a decision: parked in BACKLOG
  with the reason and the unpark condition.
- The **resolver coverage lane itself** (the 0.833 / 0.030 point) has been
  unowned since v0.13 closed it correctly on a published trade. Three
  cycles have improved the instruments while the resolver stood still.
  Recorded now as a deliberate park: it unparks with a mechanism justified
  independently of the score it would move, per the v0.13 morphology
  verdict.
- The live prompt is real and gained a behaviour this cycle (WordNet
  auto-detection, below). The HTTP skin is parked a third consecutive
  cycle on the same named blocker (P-IH6, durable multi-session auth).
  Still a park, not a loss — but three is the number at which the next
  roadmap must either schedule it or say why not.

## What changed, per area

### Where the veto's discrimination actually lives

**Before.** The cross-field match count sat on the achievement side of the
ledger, never tested against a prediction that could go either way.

**Now.** With the corruption control unrunnable, the information question
was asked by sensitivity analysis on the committed artifacts: vary the
table, report what moves. An empty table flags 0 of 77; the authored table
flags 22; declaring every co-occurring pair incompatible flags 42. Removing
exemptions one at a time moves the count by at most two — except
`proposition | set`, whose removal jumps 22 → 38. **One judgement carries
the instrument**: Boolean and set algebra are isomorphic (textbook), and
everything else is close to "cross-field slots conflict unless specifically
excused". Less flattering than a passing control, and more useful: the
veto's trustworthiness rests on one very checkable exemption, not on
thirty-eight rows of subtle dimensional reasoning.

**Demonstrate.** `experiments/veto_result.json` (flags and controls),
`experiments/veto_slot_inventory.json` (the denominator, committed first);
sensitivity table in ANALYSIS "the coincidence veto, adjudicated once
(partially)".

### The harness finds its dictionary

**Before.** A live session booted `[OFF] retrieve.wordnet no archive`
unless `COROLLARY_WORDNET` was set — with the pinned archive sitting in
`data_sources/archives/` the whole time. "What is butter" abstained for
want of an environment variable.

**Now.** `gloss.pinned_archive_path` reads the committed manifest and boot
resolves the archive itself when the variable is unset (`35f050f`). The
honesty semantics are untouched: a variable that is set but points at a
missing file still fails loudly rather than being rescued, and `--offline`
still suppresses the store.

**Demonstrate.** `python scripts/harness.py` with no environment — the boot
matrix prints `[ON] retrieve.wordnet` when the manifest archive is present.
Locator behaviour: `python -m unittest tests.test_gloss`.

### The gate, measured like-for-like at this tip

**Before.** The v0.15 reorder numbers were flagged "indicative comparison
only" — measured on a contended machine against v0.14's clean-run baseline.

**Now.** The full-suite timing run at the frozen tip `fa0a174` is in
flight as this file is first committed; its per-module table and verdict
land in this section, and the tag waits for them. (Patched before tag —
see the tagged version of this file for the numbers.)

## Discoveries of the cycle

Quoted from [DISCOVERIES](DISCOVERIES.md):

- *"Exhaustive bounded enumeration finds the transitions nobody thought to
  test."* Twelve convergence cells, all explained by two unstated
  properties of committed code.
- *"A world whose whole vocabulary is refusals closes honestly as one
  state."* The visual closure is one state and six named refusal edges, and
  four corruption classes are inapplicable there for want of anything to
  corrupt — reported as the control's honesty, not its failure.
- *"A guard that moves whenever the corpus succeeds is measuring the
  corpus."* The absorption rate-gap pin moved four times and is retired in
  favour of the count floor, which strengthened.

## The next direction, chosen before this document

The release-rotation gate ran in full this cycle: three isolated
outside contexts, three rounds each, cross-series exclusions, fifteen
directions total, receipts with prompt hashes in
`reports/design-direction-v0.16.json`. The selected direction is the
**retraction closure** — treat "this result is retracted" as an operation
with a receipt, over a provenance graph the writers emit — chosen partly
because repository inspection contradicted the outside proposal's framing
and the gate absorbed the correction. The design, including what the other
fourteen directions would have been and why they are not the direction, is
[DESIGN-retraction-closure.md](DESIGN-retraction-closure.md). It governs
[ROADMAP-v0.16](ROADMAP-v0.16.md).

## Resolved from BACKLOG

- The split-fixture duplication entry: discharged by `fa0a174` (the
  `ceiling_table` clause it carried survives as its own entry).
- The refusal-tests-pay-acceptance-cost entry: discharged by `afafbc4` +
  `82aef3e`, with the registration caution it demanded honoured.
- The reports-regeneration-check entry is **absorbed, not closed**: it is
  now a named component of DESIGN-retraction-closure §4, and the
  `wold_reach` dependant entry points there.

## Honest limits carried forward

- The suspension on the published cross-field structural match count is
  extended, not lifted. Eight of twenty-six hand-authored cross-field
  groups contain a slot whose quantities cannot be the same — which is the
  doubt the suspension was raised about, not an answer to it.
- The veto's information claim is unestablished: the corruption control
  cannot run against a table scoped to authored co-occurrence, and a
  properly powered replacement needs a full cross-product table and an
  unexamined population, neither of which exists.
- The two closures are small worlds at horizons 5 and 1. Nothing claims the
  method scales past the frozen ceilings, and a query answers reachability
  within the bound, never possibility in general.
- The resolver still ships at v0.12's 0.833 / 0.030 point. Three cycles of
  instrument work have not moved it, and this release records that as a
  decision rather than a hope.
- The README carried "11.24x" concept-token compression from v0.6.0 —
  the 221-node corpus where it was measured — through v0.14.0. It went
  false during v0.10 as the corpus grew; the 508-node ledger already read
  17.36x, and after `1090aa5` refreshed `compression.json` to 12,777
  nodes the same formula reads 32.10x. Corrected in this release, and
  recorded as a live specimen of the claim-drift class the v0.16 design
  prices: a published number whose supporting artifact was rewritten
  twice, with nothing to notice. (The first draft of this very bullet
  misattributed the number to the 508-node era — the second hand audit
  caught the first. That is not an irony to enjoy; it is the argument
  for a tool.)
- A passing Python test is not a Lean proof.

## Assets

**No new checkpoint, and the existing ones are not re-shipped.** No
`experiments/*.py` changed since v0.14.0 and no training corpus moved —
`git diff --name-only v0.14.0..v0.15.0 -- data/ experiments/` lists only
the new closure-world registrations, the veto ledgers, and ANALYSIS — so
the checkpoints attached to **v0.6.0** remain accurate for this release.
Committed in-repo instead: the two sealed closures and the demo receipt
(`reports/closures/`), the veto's five ledgers (`experiments/veto_*.json`),
and the design-course receipt (`reports/design-direction-v0.16.json`).

## Reproduce

From a fresh clone:

```
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
PYTHONIOENCODING=utf-8 python scripts/check_regeneration.py
PYTHONIOENCODING=utf-8 python scripts/validate_nodes.py
python -m unittest tests.test_bounded_closure         # six gates, 19 tests
python scripts/closure_build.py --out-dir rebuilt     # rebuild both closures
python -c "import json; a=json.load(open('rebuilt/story.golden_chicken.closure.json',encoding='utf-8')); b=json.load(open('reports/closures/story.golden_chicken.closure.json',encoding='utf-8')); print('digest match:', a['closure_digest']==b['closure_digest'])"
python -c "import json; s=json.load(open('reports/closures/story.golden_chicken.closure.json',encoding='utf-8'))['states']; d5=min((x for x in s if x['minimum_depth']==5), key=lambda x: x['state_digest']); open('target.bytes','wb').write(d5['canonical_state'].encode('utf-8'))"
python scripts/closure_query.py reports/closures/story.golden_chicken.closure.json target.bytes
python scripts/harness.py            # [ON] retrieve.wordnet, no env var needed
```
