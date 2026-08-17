# v0.12.0 — the shelf, not the architecture

The cycle that took v0.11's finding to two sources it was not built for,
and watched it run the other way. It also made the prompt answer: a person
can now type a line and get an exact lookup, a computed value, a dictionary
sense, a belief derivation, a verified story, or a named refusal.

Previous: [RELEASE-v0.11.0.md](RELEASE-v0.11.0.md) ·
Closed plan: [ROADMAP-v0.12.md](ROADMAP-v0.12.md) ·
Next: [ROADMAP-v0.13.md](ROADMAP-v0.13.md) ·
Triage & drift audit: [TRIAGE-v0.12.md](TRIAGE-v0.12.md) ·
Findings: [DISCOVERIES.md](DISCOVERIES.md) ·
Blog: [the shelf, not the architecture](blog/the-shelf-not-the-architecture.md)

---

## The headline finding: the sign flip did not travel

**Before.** v0.11 measured whether an ingested layer's parts acquire owners
inside that same layer, on Lean-workbook, and found compounding with a shape
nobody registered: below a matched null at N=8 and 32, above it from 128.
The open question was whether that was a fact about the architecture or a
fact about one shelf of olympiad inequalities.

**Now.** Two sources the emitter was not fitted to run the *other way*.

| holdout | N | real ISG | null mean | gap |
|---|---:|---:|---:|---:|
| miniF2F | 8 | 0.00000 | 0.01626 | −0.01626 |
| | 32 | 0.00000 | 0.00991 | −0.00991 |
| | 157 | 0.00547 | 0.04823 | −0.04276 |
| Goedel-Pset | 32 | 0.00000 | 0.00936 | −0.00936 |
| | 128 | 0.00725 | 0.05354 | −0.04629 |
| | 512 | 0.01442 | 0.10750 | −0.09308 |
| | 1,896 | 0.02537 | 0.15125 | **−0.12588** |

**H1 missed.** This is not a curve that failed to flip — it is a curve
running the other way, diverging monotonically as the layer grows.
Lean-workbook's compounding is a fact about Lean-workbook.

**And it is source, not scale.** C1, registered before its cell was
computed, puts both at *identical* N=157 with the same generator, null and
seed protocol: Lean-workbook **+0.0496**, miniF2F **−0.0428** — opposite in
sign, separated by 1.9× the combined null spreads, both nulls far from zero.
The "157 is too small" objection is dead, because Lean-workbook shows the
effect at 157.

**Demonstrate.**
`python scripts/measure_heldout_recovery.py` → `experiments/heldout_recovery.json`
`python scripts/measure_self_grounding.py --sizes 157 --no-all` → `experiments/matched_n_control.json`

### A retraction, stated as one

v0.11's "ingestion compounds" is **retracted as a general claim.** It was
measured on one source; two held-out sources say the opposite. Ingestion
still buys coverage. It does not buy a transferable structure-recovery
claim. That is the cycle's result, and the design named it in advance as
"the more interesting negative".

---

## Roadmap triage

**Shipped.**

- **Item 1 — held-out recovery.** H1 **missed**, H2/H3/H4/H6 fired, H5
  missed conditionally. Two quarantined holdouts authored through the
  unwidened emitter: miniF2F 157 nodes, Goedel-Pset 1,896.
- **Item 4 — verdict-backed ingestion as a RULE.** Widened past
  `python-tests` to every ingested corpus, keyed on corpus identity.
- **Item 5 — one typed line.** P-LS1–P-LS5 all fired, and the surface grew
  well past its acceptance (see below).

**Shipped as a negative.**

- H1 itself. The headline is the miss.
- **B3 missed, 3:1.** Goedel-Pset exclusions are `parse_fail` 114 vs
  `emit:` 38, inverting both priors on the first sample large enough to
  test it.
- **S2, S5, R2 missed** on the runs that scored them. Each was repaired and
  the repair measured; none is re-scored.

**Parked, in writing.**

- **Item 2, the groundedness gate.** H1 failed, so §8's parking condition
  returned. Unpark only when a source other than Lean-workbook shows a
  positive owner-attributed gap surviving its own null.
- **Item 6, write-recovery ranker.** No fit named, so it parks rather than
  carrying a third time.
- **Item 7, budgeted-edit ranker.** Still one foil cell.

---

## What changed, per area

### Holdouts became a corpus tier

**Before.** A held-out corpus had nowhere to live.

**Now.** `data_holdout/` — committed, git-versioned, schema-validated,
byte-reproducible from its seed, and invisible to the merged graph.
Authoring miniF2F into `data/` instead moves the published v0.11 channel
split under *either* discipline label (external share 0.391 → 0.581, or
`prior_corpus` 286 → 26,014). There is no free label, so the premise was
wrong rather than the label.

**Demonstrate.** `python scripts/check_regeneration.py` →
`coherence OK: 22 seeds ... across data/, data_holdout/`

### The emitter degrades with distance from home

**Before.** One emit rate, on the source the emitter was built for.

**Now.** 99.03% (Lean-workbook) → 98.12% (miniF2F) → 92.58% (Goedel-Pset).
And 101 of Goedel-Pset's 114 `parse_fail`s carry one unmapped constant,
`Real.pi` — 66% of all exclusions from a single nullary. Not fixed: design
§3 forbids widening the emitter for a held-out source.

**Demonstrate.** `experiments/goedel_pset_emit.json`, key
`parse_fail_attribution`.

### The prompt answers

**Before.** `python scripts/harness.py` printed a boot list and exited.
v0.8's notes said the system could be driven; it could not.

**Now.** It reads one line and stops with a machine verdict:

```
$ echo "what is the cosine of a double angle" | python scripts/harness.py
Double-Angle Cosine
The cosine of twice an angle is the difference of the squared cosine and the squared sine.
formally   : cos(2*x) = cos(x)^2 - sin(x)^2
source     : trigonometry.identities.double_angle_cosine  [trigonometry.core.v1]

$ echo "when x=5, what is x ^ 2?" | python scripts/harness.py
exact      : 25

$ echo "dotty sees bob walk into the room. bob moves to the garden. Where does dotty think bob is?"
believes   : located_in(bob) = room
world says : located_in(bob) = garden
divergence : belief and world differ; the question asked for the belief
```

Every sentence is quoted from committed prose or WordNet; every value is
computed exactly with `Fraction`; every relation comes from committed
`inferential_links`. **The renderer cannot author a false sentence because
it cannot author a sentence.**

**Demonstrate.** `docs/DESIGN-live-session.md` §8; `python -m unittest tests.test_probes`

### Boot stopped lying

**Before.** `main()` hard-coded `offline=True`, a test invariant leaked into
the CLI, so the prompt reported subsystems OFF on machines that had them.

**Now.** It probes. Registered paths 3 → 5.

---

## Discoveries of the cycle

From [DISCOVERIES.md](DISCOVERIES.md): the sign flip does not travel; at
matched N the fitted source compounds and the holdout does not; the rejected
proxy would have reported 71% and 92% self-grounding on sources that recover
nothing; the holdouts' parts *are* grounded, just externally (XSG 0.59–0.81);
and groundedness-at-all survives where self-grounding does not — recorded as
an **unregistered probe**, not a result.

---

## Resolved from BACKLOG

- The external benchmark, carried through v0.9, v0.10 and v0.11 — **run**.
- Verdict-backed ingestion as a rule — **shipped**.
- The v0.8 live-prompt debt — **paid**.

---

## Honest limits carried forward

- **"Ingestion compounds" is retracted as a general claim.** See above.
- **The groundedness gate is parked, not designed.** Its unpark condition
  is written down.
- **Coverage overstates what is authorable.** The instrument admits
  statements the emitter cannot round-trip (`Real.pi`), and coverage is the
  sampling frame for both holdouts, so every downstream count inherits a
  soft frame.
- **The conversational surface is not the headline and its numbers are
  worse than its demonstrations.** In-corpus coverage 0.833–1.000 depending
  on the set. **False positives on unselected input: 3.0%** (F3, 1,000
  mechanically sampled WordNet sentences, threshold registered beforehand).
  One registered refusal prediction, **R2, missed at 0.80**.
- **The precision/recall trade is real and published**: no convergence
  0.046 FP / 0.944 coverage; winner-support 0.030 / 0.833 (ships); full
  intersection 0.006 / 0.611. Lexical semantics was tried as a way past it
  and **refuted** — WordNet hypernym roots do not separate the leaks.
- **Goedel-Pset N=8 is a degenerate cell** (real 0.0, all nulls 0.0) and is
  excluded from the trend rather than counted as agreement.
- **Multi-turn is parked** (P-LS6) and enforced by a test.
- A passing Python test is still not a proof.

---

## Assets

Symbolic cycle. No new checkpoint, and none is invented.

| artifact | story | command |
|---|---|---|
| `experiments/heldout_recovery.json` | H1–H6, both holdouts, the headline miss | `python scripts/measure_heldout_recovery.py` |
| `experiments/matched_n_control.json` | C1 — source, not scale | `python scripts/measure_self_grounding.py --sizes 157 --no-all` |
| `experiments/minif2f_emit.json` | held-out A census, 157/160 | `python scripts/seed_minif2f.py` |
| `experiments/goedel_pset_emit.json` | held-out B census + `Real.pi` attribution | `python scripts/seed_goedel_pset.py` |
| `data_holdout/*/nodes.json` | the quarantined corpora | `python scripts/check_regeneration.py` |
| `experiments/resolution_scale.json` | S1–S5, discrimination at corpus scale | `python scripts/measure_resolution_scale.py` |
| `experiments/text_resolution*.json` | T1–T4 and both text holdouts | `python scripts/measure_holdout_text.py` |
| `experiments/false_positive_rate*.json` | F1/F2/F3 on unselected input | `python scripts/measure_false_positive_f3.py` |

No asset without a story. No licensed external data.

---

## Reproduce

From a clone, `PYTHONIOENCODING=utf-8`:

```
python scripts/check_regeneration.py
python scripts/validate_nodes.py
python scripts/measure_heldout_recovery.py
python scripts/measure_self_grounding.py --sizes 157 --no-all
echo "what is the cosine of a double angle" | python scripts/harness.py
echo "when x=5, what is x ^ 2?" | python scripts/harness.py
python -m unittest tests.test_probes tests.test_readiness
```

The WordNet-backed routes need the pinned archive:
`python scripts/fetch_sources.py --fetch wordnet-2025-json`, then set
`COROLLARY_WORDNET`. Without it those routes report OFF and the dispatcher
abstains — they do not answer from an empty index.
