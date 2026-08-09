# Design: affect as structure — emotion maps without weight-space sentiment

Source conversation: 2026-08-09, prompted by emotion-classification diagrams
and maps ([Emotion classification](https://en.wikipedia.org/wiki/Emotion_classification)),
and by the question of whether continuous “emotion vectors” belong in the
same program as math/science corpora, multiplanar oscillators, and the
symbolic controller. The finding that motivates this document: **the
competitive claim of this repository is exact structure outside weights;
affect enters only where it is structure with verifiers, not as a continuous
vibe table inside the model.** What follows is the mapping, the non-goals,
the staged work, and registered predictions that keep the mapping
falsifiable rather than decorative.

Status: design only. No affect corpus, no sentiment experiment, and no
change to analogy training data. Owned belief, nested models, narrative
obligations, and the visual-structure protocol already exist; this document
says how affect should reuse them and what it must not invent. Indexed from
`docs/BACKLOG.md` (“Affect / emotion structure” and the related oscillation
lane) and from `docs/DESIGN-cognitive-frames.md` sequencing.

---

## 1. Why this is easy to get wrong

Frontier LLMs already produce fluent affect language. A natural temptation is
to treat “emotion understanding” as continuous coordinates (valence–arousal,
PAD, or a learned embedding) and train a small model to regress them. That
path fights this project’s thesis on three fronts:

1. **Closed forms stay outside weights.** Exact identities, frame locality,
   and obligation discharge are not residual soft labels.
2. **Vacuity is cheap.** Keyword lexicons and frequency priors often solve
   free-text emotion tags; without a capability-blind baseline, a tiny
   classifier “win” is meaningless.
3. **The blog already states the honest limit.** Controlled theory of mind
   ships without “a rich model of motives, emotion, deception, or cultural
   context” (`docs/blog/the-world-outside-the-weights.md`). Filling that
   limit with embeddings would look like progress while abandoning the
   harness.

The useful question is therefore not “can we store emotion vectors?” but
“which parts of emotion taxonomies are exact relations, owned state, diagram
structure, or empirical observations with provenance?”

---

## 2. What the literature offers (project-usable cut)

Emotion classification is not one representation. Three families matter here:

| Family | Examples | Closed form available? |
|---|---|---|
| Discrete taxonomies | Ekman basics; Plutchik wheel (opposites, intensity rings, blends) | Yes: labels, opposition, order, licensed blends as edges |
| Dimensional spaces | Russell circumplex (valence × arousal); PAD | Partial: named axes, quadrants, polar/Cartesian slot transforms |
| Constructionist / appraisal | Emotion as assembled components under context | Harder: mostly procedural; late if at all |

Wikipedia-style “emotion vectors” usually mean continuous coordinates from
the second family or learned text embeddings. Only discrete relations and
**named** dimensional structure fit seeds, twins, frames, and diagram
oracles. Continuous coordinates may later enter as **empirical
observations** (tool or human rating), never as verified corpus truth and
never as the core vocabulary of the tiny model
(`docs/DESIGN-concept-tokens.md` remains concept/pointer oriented).

This is a different psychology slice from Relational Frame Theory. RFT is
already mapped in `docs/DESIGN-cognitive-frames.md` §3 as relational
operants (coordination, opposition, hierarchy, deixis, …). Affect is not
another RFT cell; it is local state and relational structure about
feeling/intensity, optionally constrained by narrative obligations.

---

## 3. Correct treatment: layers with verifiers

Treat affect as **structure with verifiers**, parallel to belief and fiction
scopes—not as weight-space sentiment.

| Layer | Representation | Outside weights | Learned residual (only later) |
|---|---|---|---|
| Discrete labels | Typed symbols or statement ids (`affect.basic.anger`, …) | Identity; membership in a declared basic set | Point to a label given structured cues |
| Plutchik-style relations | Opposite / adjacent / blend as explicit edges | Mirror-style opposition; composition rules | Rank which blend is licensed under a rule set |
| Dimensional map | Valence–arousal as exact polar or Cartesian slots with named quadrants | Coordinate transforms; quadrant membership predicates | Soft map from noisy text → nearest named region, then verify |
| Diagram twins | SVG circumplex / wheel with scene-graph ids | Sector geometry; label↔sector alignment; inconsistent-sector negatives | Style-robust pointing under redraw (`DESIGN-visual-structure.md`) |
| Narrative use | Character `owner` frame holds local affect literals | Consistency; update on witnessed events; no world leak | Propose next story action under obligations |
| Empirical scores | Continuous VAD or model scores from tools/humans | Provenance, epistemic rung (empirical/conjectured), never PROVEN by fluency | Optional ranking among already-admitted structured options |

Belief remains distinct: Sally’s false belief is about `located_in`, not about
`feels`. Affect may *coexist* on an owned frame (`marble located_in basket`
and `sally feels surprise` after a witnessed event) without collapsing the
two predicates into one mechanism.

### Frame semantics (reuse, do not fork)

- An **owned** frame may carry affect literals the way it carries location
  beliefs. Fiction frames may invent affect as premises; on exit they demote
  under existing `on_exit` rules.
- Updates follow **visibility**: a character’s affect changes only through
  events they witness (or through explicit self-report events with declared
  authority). Unwitnessed insults do not update the target’s frame any more
  than unwitnessed moves update Sally.
- Nested models: “Anne believes Sally is angry” is nested-frame content, not
  a special emotion modal. Graft-back API gaps already filed under Nested
  frames still apply.
- World tier does not absorb private affect. Public story state may record
  witnessed expressions; private felt state stays owner-local unless an
  event makes it public.

### Narrative obligations (first useful cut)

Before any affect corpus, the highest-value executable slice is plant /
discharge of character-affect obligations, reusing temporal machinery
already shipping for Chekhov and no-deus:

1. Plant: witnessed slight, promised comfort, declared fear of X.
2. Advance story time / beats.
3. Discharge: apology, revenge, comfort, or explicit cancellation with
   provenance.
4. Anti-vacuity: close or resolution fails if a planted affect obligation
   remains open (same refusal pattern as undischarged Chekhov elements).

That is comprehension as **constraint satisfaction under ownership**, not as
sentiment F1.

---

## 4. Incorrect treatment (explicit non-goals)

Near-term non-goals, registered so they are not “accidentally” implemented:

1. Continuous PAD / VAD tables inside model weights as the meaning of
   comprehension.
2. Training the current synthetic analogy pointer model on free-text emotion
   tags while depth-OOD addressing remains the open architecture question.
3. Claiming LLM competition on “emotional intelligence” before logic,
   temporal, belief, and mixed controller rungs are checkable on the same
   harness.
4. Collapsing affect into RFT coverage or into rotating-frame physics by
   metaphor alone (“oscillations of feeling” as a corpus skeleton).
5. Promoting tool sentiment scores to VERIFIED or PROVEN without external
   adjudicated ground truth and an epistemic rung appropriate to the source.
6. Mid-run changes to analogy dropout or train composition “to add emotion.”

---

## 5. Relation to multiplanar / oscillatory physics

A parallel directional question asked about frequency, SHM, multiplanar
coupling, Hooke, Kepler, and resonance. That lane is **physics corpus and
visual structure**, not affect:

- `physics.mechanics.hookes_law` already notes itself as generator of
  harmonic motion; SHM / ω / period / resonance nodes are the natural next
  physics seeds (see BACKLOG “Physics oscillation / multiplanar ladder”).
- Multiplanar dynamics (orthogonal components, coupling, Lissajous) and
  multiplanar *frames* (rotating-frame corrections already authored) compose
  under the cognitive-frames program.
- Diagram payoff (phase portraits, Lissajous) reuses
  `DESIGN-visual-structure.md` after the deferred triangle oracle exists.

Affect diagrams (Plutchik wheel, circumplex) may later share the **visual
protocol** with Lissajous and SHM plots. They do not share equations. Do not
author a single blended “emotion oscillator” archetype unless a real
structural twin is predicted and adjudicated honestly.

Sequencing relative to the neural/controller path (and to the side-channel
finding that analogy training is synthetic trees only):

```text
[current] depth-consumer matrix; learned tactic policy; user frames
    → physics SHM / frequency seeds + twin predictions (symbolic)
    → multiplanar / coupled modes + rotating-frame composition (symbolic)
    → controller actions over oscillator or frame state (oracle, then policy)
    → narrative affect obligations on owned frames
    → optional discrete affect corpus if matcher predictions justify it
    → diagram twins: Lissajous / SHM plots / emotion wheels (after visual oracle)
    → optional small pointer models per rung, always with frequency/copy baselines
```

---

## 6. Registered predictions (before any adjudicating implementation)

Predictions are registered here **before** seeds, obligations, or classifiers
exist. Fired and missed are both reportable; do not edit prediction text
after the fact—attach adjudication notes.

**P-AFF1 — opposition reuses mirror/opposition machinery.**
When Plutchik-style opposite pairs are authored as discrete relations (or as
mirror-involutive heads if a head form is justified), they twin or
mirror-group without inventing a new structural archetype solely for
emotion. A miss localizes what emotion opposition does not share with
existing NEG/mirror groups.

**P-AFF2 — affect obligations reuse temporal plant/discharge.**
A character-affect obligation (plant insult or fear → eventually response or
comfort) is executable with existing temporal eventually/once plant–discharge
and owned-frame visibility, without a new verdict enum. A miss means either
visibility rules or obligation close semantics need an explicit extension—and
that extension must be named, not smuggled into prose.

**P-AFF3 — free-text emotion tags are a vacuous early benchmark.**
At this parameter scale, a lexicon or frequency baseline will match or beat a
tiny learned classifier on unstructured emotion labels unless the task
supplies structured cues (frame state, event history, diagram sector). The
expected “win” for the project is structured navigation, not VAD regression.
If a learned arm beats strong blind baselines on free text without structure,
re-open the claim; until then treat free-text sentiment as out of scope.

**P-AFF4 — continuous scores stay empirical.**
Any continuous valence/arousal observation that enters the harness is stored
with provenance at an empirical or conjectured rung and cannot alone verify a
discrete affect literal. If a pipeline ever promotes a float to VERIFIED
without an external adjudicator, that is a REFUTED governance finding.

**P-AFF5 — visual circumplex/wheel follows V1 ordering.**
Emotion-map diagram twins are not started until a deterministic renderer,
source scene graph, and inconsistent-pair geometry checks exist for at least
one simpler family (right triangle first, per visual deferral). Starting
affect diagrams before that oracle repeats the visual-lane failure mode
already adjudicated in v0.6.

---

## 7. Work items (dependency order)

1. **Keep v0.6 neural/controller matrices unchanged.** No affect data in
   analogy generators; no dropout ablations “for emotion.”
2. **File and hold this design** as the admission gate against embedding-first
   proposals (this document).
3. **Physics oscillation ladder first** (separate BACKLOG section): Hooke →
   SHM → ω/T/f → resonance → multiplanar components; twin predictions in
   seed docstrings before regenerate.
4. **Narrative-affect obligation demo** after belief/visibility remains
   stable: one plant/discharge pair with visibility negative controls and a
   close-refusal when undischarged.
5. **Optional discrete `affect` corpus** only if P-AFF1-style edges are worth
   matcher adjudication; seeds only, never hand-edited `nodes.json`.
6. **Diagram families** only after visual oracle: SHM/Lissajous before or
   beside circumplex/wheel; same parsed-vector vs raster protocol.
7. **Learned residual last**, and only as pointer/rank under the executor;
   always report lexicon/frequency/copy baselines on the same split.

Acceptance for “affect is in the system” is **not** sentiment-F1 against an
LLM. It is: the same controller can discharge a planted character-affect
obligation under owned-frame rules while a physics derivation involving ω
from Hooke remains checkable—neither fact living only in weights.

---

## 8. Epistemic and schema notes

- Discrete affect literals on frames use the existing verdict ladder
  (`docs/DESIGN-epistemic-ladder.md`). Frame-local VERIFIED affect can be
  world-UNKNOWN or world-REFUTED (actor dissembling) without new tiers.
- Dimensional coordinates, when present, are either (a) exact symbolic slots
  in a dimensional-map statement, or (b) empirical observations. Do not add a
  float embedding table to concept vocabulary.
- WordNet emotion synsets, if retrieved, remain empirical lexical context
  under the existing store boundary; they do not ground VERIFIED affect.
- Cross-domain metaphors (entropy of mood, resonance of feelings) are prose
  until a registered structural prediction fires. Pattern absorption is not
  admission.

---

## 9. Sequencing relative to cognitive frames

Insert after nested belief and conversation lifetime work, not before:

1. Theory of mind / owned frames — SHIPPED first cuts.
2. Physics frames — SHIPPED first cut; deepen executable boosts/terms still open.
3. Nested models — SHIPPED first cut; graft-back API still open.
4. **Physics SHM / multiplanar corpus** — next high-value science lane.
5. **Affect obligations** — this document’s first executable cut.
6. Discrete affect corpus and visual emotion maps — only with predictions and
   oracle ordering above.

Every prediction P-AFF1..5 follows the house rule: registered before the
adjudicating tool runs; fired and missed are both reportable; misses land in
`docs/DISCOVERIES.md` with the same prominence as hits.
