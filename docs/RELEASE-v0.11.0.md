# v0.11.0 — the curve changed sign

The cycle that measured whether ingestion compounds, and found a
shape nobody asked for: worse than chance at thirty-two statements,
better from one hundred twenty-eight. It also made the matcher-vs-bag
fight a single figure of merit, authored the rest of the templates
the matcher can parse, and put programming tests at volume without
calling them proofs.

Previous: [RELEASE-v0.10.0.md](RELEASE-v0.10.0.md) ·
Closed plan: [ROADMAP-v0.11.md](ROADMAP-v0.11.md) ·
Next: [ROADMAP-v0.12.md](ROADMAP-v0.12.md) ·
Triage & drift audit: [TRIAGE-v0.11.md](TRIAGE-v0.11.md) ·
Findings: [DISCOVERIES.md](DISCOVERIES.md) ·
Blog: [the curve changed sign](blog/the-curve-changed-sign.md)

---

## The headline finding: at thirty-two we were below chance

**Before.** v0.10 saw two ingested statements share `2^30`, then
614 same-source parts inside 251 ground identities. No random
baseline. No curve. “Compounds” meant “seen twice.”

**Now.** Owner identity, not sharing: a part is self-grounded when
its most-independent owner is another ingested statement. At
12,515 ingested nodes the real rate is 0.473 against a
distribution-matched random baseline of 0.410. The gap changes
sign:

| ingested statements | real − random |
|---:|---:|
| 8 | **−0.041** |
| 32 | **−0.024** |
| 128 | +0.046 |
| 512 | +0.042 |
| 12,515 | +0.063 |

Sharing is nearly universal on this layer (the rejected proxy
reads 1.000 of grounded parts). Grounding of those same parts is
0.543. Dropping the most common part (`x²`) *widens* the gap to
0.127: the popular term was owned by the older hand-authored
layer, not carrying the effect.

**Demonstrate.**
`python scripts/measure_self_grounding.py` →
`experiments/self_grounding_curve.json`.

---

## Roadmap triage

**Shipped.**

- **Item 1 — self-grounding curve.** Route 1 (owner identity).
  S1–S4 fired. Sign flip attached, not a footnote.
- **Item 2 — one figure of merit.** Bag precision against typed
  twins = **0.0220%** (1,990 / 9,041,744). Matcher 1,991 pairs,
  precision 0.9995; one named print-convention miss.
- **Item 3 — programming second wave.** Six more verified-code
  nodes (factorial, double-factorial, binary exponentiation) with
  `range(20)` library comparisons. Citation-not-proof survives.
  Name-baseline precision 0.4 combined, 1/3 on the factorial foil
  set. One recorded fail (`n-2`) cited by nothing.
- **Prerequisite — skeleton emitter.** 12,514 authored (302
  ground + 12,212 emitted), 123 excluded.

**Shipped as a negative / accident.**

- The sign flip itself. A curve stopped at hundreds would have
  been “ingestion does not compound.”
- Sharing is not grounding (proxy 1.0 vs 0.543).
- Programming corpus trips the conservative self-certifying flag
  (mean 0.939) and not the generous one.

**Scheduled, not run.**

- External benchmark → v0.12 item 1 (held-out recovery on two
  sources the emitter was not built for). Design frozen before
  this post.

**Designed, not implemented (forward-looking).**

- Budgeted-edit ranker — parked unless a second “passes tests,
  different recurrence” foil exists.
- Write-recovery ranker — waits on a training leftover that is
  not write-recovery itself.
- One typed line after the boot list — v0.12 item 5. Reclaims
  the live prompt v0.8 claimed.

**Carried / parked.** Verdict rule (Lean half) → v0.12 item 4.
Groundedness gate → v0.12 item 2, after H1. Specialize index,
proof-search depth, physics/affect/visual, HTTP skin,
open-English new nodes, multi-turn dispatch memory: parked.

---

## What changed, per area

### Ingestion compounds, with a sign flip

**Before.** Anecdote at two scales, no random baseline.

**Now.** Curve at five sizes; real below random at 8 and 32,
above from 128.

**Demonstrate.** `experiments/self_grounding_curve.json`;
`docs/DESIGN-self-grounding-ingestion.md` § adjudication.

### One figure of merit

**Before.** Bag wins on count, matcher wins on precision; either
side could claim victory.

**Now.** Bag precision against typed twins is the number:
0.0220%. Count still belongs to the bag (9.0M vs 1,991).

**Demonstrate.** `python scripts/measure_operator_bag.py`;
`docs/DESIGN-fair-fight.md`.

### Remainder authored, refusals counted

**Before.** 302 unique-covered Lean-workbook statements had
templates; 12,681 waited.

**Now.** 12,514 authored, 123 excluded, bucketed.

**Demonstrate.** `experiments/lean_workbook_emit.json`;
`python scripts/emit_skeleton.py` (from the pinned extract).

### Programming at volume, still not a proof

**Before.** Three gcd nodes; a handful of doctest cases.

**Now.** Nine nodes; `range(20)` vs `math.factorial` /
`math.prod`; citation-not-proof survives.

**Demonstrate.**
`python -m unittest tests.test_programming_discipline -v`;
`docs/DESIGN-programming-second-wave.md`.

### Corpus

**Before.** 508 nodes (v0.10 end), then 12,771 after the emitter.

**Now.** 12,777 (six programming nodes in the second wave).
27 corpora. 9 verified-code nodes.

**Demonstrate.**
`python scripts/validate_nodes.py` prints
`12777 statement nodes across 27 corpora`.

---

## Discoveries of the cycle

From [DISCOVERIES.md](DISCOVERIES.md): ingestion compounds and
the proxy would have lied; bag figure of merit 0.0220%; first
ingested-to-curated typed twin (double-angle cosine, print
convention); factorial / double-factorial share a token and not a
skeleton; programming corpus self-certifying only under the
conservative owner rule.

---

## Resolved from BACKLOG

- `TOKEN_RE` standalone `<` `>` — shipped with the emitter.
- Remainder of the unique-covered set — shipped; 123 excluded,
  counted.
- Programming second wave — shipped.

---

## Honest limits carried forward

- The held-out curve has **not** been run. Lean-workbook is not
  held-out.
- `reports/decompositions.json` is still the pre-scale file.
  Live analysis is the pin source at this size.
- The full test discover is 30+ minutes (several tests each
  reload 12k nodes). Graph-touching tests were green during the
  slices; **the complete suite must be re-run on the tip before
  anyone treats “green” as a tag-time fact.**
- `python scripts/harness.py` still prints a boot list and
  exits. v0.8 said the system can be driven. That was libraries
  plus a recorded session, not a prompt. Named in triage; scheduled
  as v0.12 item 5; **not** implemented in this tag.
- A passing Python test is still not a proof.
- Grammar reach on uncontrolled formal math is still about a
  third.

---

## Assets

Symbolic cycle. No new checkpoint.

| artifact | story | command |
|---|---|---|
| `experiments/self_grounding_curve.json` | sign flip + S1–S4 | `python scripts/measure_self_grounding.py` |
| `experiments/item4_operator_bag.json` | 0.0220% figure of merit | `python scripts/measure_operator_bag.py` |
| `experiments/lean_workbook_emit.json` | 12,514 / 123 | `python scripts/emit_skeleton.py` |
| `experiments/skeleton_emitter_aggregates.json` | live decompose pins at scale | cited from tests |

No asset without a story. No licensed external data.

---

## Reproduce

From a clone, `PYTHONIOENCODING=utf-8`:

```
python scripts/check_regeneration.py
python scripts/validate_nodes.py
python scripts/measure_self_grounding.py
python scripts/measure_operator_bag.py
python scripts/session_run.py --check
python -m unittest tests.test_programming_discipline tests.test_emit_skeleton tests.test_self_grounding
```

`python scripts/harness.py` still only prints the boot list.
That is the honest current binary, and the next cycle’s first
typable work after the held-out curve.
