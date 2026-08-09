# Design: cognitive frames — one program behind theory of mind, reference frames, and relational deixis

Source conversation: 2026-08-09, prompted by five external references (theory
of mind; physical frames of reference incl. MIT 8.01 ch. 11 and Galilean
relativity; relational frame theory; Willard's self-verifying theories; BERT/
BookCorpus/WordNet). The finding that motivates this document: **four of the
five map onto machinery this repository already ships, and the fifth names
the storage bet the repository exists to test.** What follows is the mapping
in full, the staged work it implies, and the registered predictions that make
the mapping falsifiable rather than decorative.

Status: ASK's runtime user frame and return channel are now executable
(`scripts/conversation.py`); physical frames, FrameSpec ownership/visibility,
WordNet, masked skeletons, provability, and nesting remain queued. Each section
ends with its work items; ROADMAP-v0.5 section 10 and BACKLOG's "Cognitive
frames / lexical stores" section index them.

---

## 1. Theory of mind is frames with owners

A false-belief task is representable in `scripts/frames.py` today with zero
new mechanism. The Sally–Anne task, transcribed:

- World tier: `marble located_in box` (the marble was moved).
- Sally's frame: declaration `marble located_in basket` (she saw it placed,
  did not see the move) — frame-local VERIFIED.
- "Where will Sally look?" is answered from *her* frame. Her belief is
  frame-locally VERIFIED and world-REFUTED simultaneously — which is exactly
  the state our scope machinery exists to hold without leaking, and exactly
  what an epistemic ladder without scopes cannot represent at all.

We crossed the ToM threshold once already without naming it: `ASK` exists
because some UNKNOWNs are **frame-private to the interlocutor**. That is a
theory-of-mind claim — the system models the user as an agent whose frame
contains authoritative bindings unavailable to any store.

What is genuinely missing, in dependency order:

1. **Frame ownership.** `FrameSpec` gains an optional `owner` (an agent
   identifier). An owned frame is a belief state; an unowned frame remains a
   fiction/hypothetical. `on_exit` semantics differ: a fiction's truths
   demote to `conjectured`; a belief frame does not "exit" — it persists and
   *updates*.
2. **Visibility-filtered updates.** An agent's frame updates only through
   events that agent witnessed. The obligation ledger already gives us a
   strictly-sequenced event record; ToM needs a per-agent visibility set on
   events (`witnessed_by`). Sally's frame receives the placement event but
   not the move event; the divergence between her frame and the world is
   then *derived*, not authored — which is the difference between
   representing a false belief and merely asserting one.
3. **Nested frames.** "Anne believes that Sally believes the marble is in
   the basket" is a frame opened inside a frame. The executor's
   open/check/close cycle composes naturally (a FrameState holding a child
   FrameState), but nesting multiplies the demotion rules and needs its own
   negative controls (a grandchild truth must not leak into either ancestor;
   an ancestor's suspension must be inheritable-or-not by explicit choice,
   not accident).
4. **The user frame — first runtime cut SHIPPED.** Multi-turn golden-chicken revision ("now make the
   chicken lay silver eggs") requires a persistent owned frame for the
   interlocutor: what they have been told, what they have asked for, which
   of their bindings arrived via ASK. This makes the ASK return channel and
   ToM the same slice viewed from two sides — the return channel *is* the
   user-frame update rule. The shipped cut keeps a signed, runtime-owned
   `UserFrame` beside retrieval state, pauses the generic controller as WAITING,
   and resumes from a channel-signed reply. It does not yet add `owner` to
   `FrameSpec`; that schema-level belief ownership remains item 10c.

**Registered prediction P-CF1 (falsifiable at authoring time):** a
Sally–Anne corpus node pair (belief-frame declaration vs world assertion)
will validate under the existing scope schema with `owner` as the only
schema addition, and the false-belief answer will be derivable by the
existing executor given visibility-filtered events — no new verdict logic.

Work items: schema `owner` field (additive, like `scope`); `witnessed_by`
on temporal events; nested-frame negative controls; Sally–Anne executable
demo; user-frame persistence (post-ASK-slice).

---

## 2. Physical frames of reference are the same scope construct

The pun on "frame" is not a pun; the mapping is structural and testable.

- A **rotating reference frame** suspends Newton's first law and admits
  centrifugal/Coriolis terms as frame-local dynamics premises. That is
  *literally* the executor's `suspends` + admit-as-invention path: **a
  fictitious force is a frame-local invention licensed by suspending an
  inertia law.** The narrative and physics instances differ only in which
  law is suspended and what is admitted.
- **Galilean invariance** splits physics exactly along the seam the frame
  executor already cuts: laws are frame-invariant (world tier — F = ma holds
  in every inertial frame), measurements are frame-local (velocity is
  meaningless without a frame and demotes on exit). MIT 8.01 ch. 11's
  relative-velocity algebra (u' = u − v) is the transformation between
  frame-local tiers; Galileo's ship argument is the statement that no
  frame-local measurement distinguishes inertial frames — i.e., the world
  tier is exactly the frame-transformation invariants.
- The matcher already handles a declared structural transformation: the
  **mirror level** treats time reversal as an involution on heads. A
  Galilean boost is the same shape one abstraction over — a declared
  transformation under which a family of statements is closed. If frames of
  reference enter the corpus, "invariant under boost" is to physics what
  "mirror twin" is to temporal logic.

**Registered prediction P-CF2:** an authored `physics.frames.rotating_frame`
node (suspends an inertia/first-law node, admits a centrifugal-force
premise) will land in one structural family with
`narrative.frames.cartoon_gravity` — both are frames that suspend a physics
law and admit a local dynamics premise. If this twin fires, it is the first
evidence that the scope construct generalizes beyond fiction, which is the
claim the whole frame program rests on. If it misses, the miss is
reportable: it localizes what fiction-scope and physics-scope do NOT share.

**Registered prediction P-CF3:** Galilean velocity addition will twin or
family with an existing composition/addition skeleton (candidate: the
convex-combination or vector-addition families) rather than forming a new
archetype — relative motion is composition, not new structure.

Work items: `physics.frames` corpus lane (velocity addition, acceleration
invariance, rotating-frame admission, inertial-frame definition) authored
with scope objects; P-CF2/P-CF3 adjudication; a frame-transformation note
in DESIGN-scope-and-modality if the boost-as-declared-transformation idea
graduates to a matcher level.

**Adjudication (v0.5 first cut):** P-CF3 fired and P-CF2 missed. Galilean
velocity addition joined `algtop.homology.chain_rank_nullity` at shape and
typed levels on the exact additive skeleton `?0:V = +(?1:V, ?2:V)`.
Precision the fired verdict owes (post-merge review): **neither named
candidate matched** — the convex-combination family's skeleton
(`?0 = +(*(?1,?2), *(?3,+(1,neg(?1))))`) is structurally incompatible with
the bare additive form, and no vector-addition family existed at all. The
class prediction (existing composition/addition skeleton, no new
archetype) fired via a skeleton that was not on the candidate list, around
a node that had been a SINGLETON until this pair formed. Fired-in-class,
missed-in-candidates: both halves are the record. The
rotating-frame declaration did not group with cartoon gravity at any level:
its honest equation is a three-term apparent-acceleration correction, whereas
cartoon gravity is a temporal liveness rule. The shared content is in
`scope.suspends`, declaration ownership, and frame-local premise admission —
fields the signature matcher intentionally does not read. This is evidence
that the scope executor generalizes across domains, not evidence that every
scope declaration has one mathematical skeleton.

---

## 3. Relational frame theory is our matcher described as psychology

RFT's claim: cognition is built from learned relational operants — frames of
coordination, opposition, distinction, comparison, hierarchy, temporal,
causal, and deictic relations — with three signature properties: **mutual
entailment** (A>B ⊢ B<A), **combinatorial entailment** (A>B ∧ B>C ⊢ A>C),
and **transformation of stimulus function** (what is learned about A
transfers to B through the relation). Read against this repository:

| RFT relational frame | Repository mechanism | Status |
|---|---|---|
| Coordination (sameness) | Twin ladder (shape/typed/family/aliased) | SHIPPED, measured |
| Opposition | Mirror level; NEG handling; denied premises | SHIPPED (mirror: 5 groups) |
| Distinction | Slot-vs-head lint; typed slot categories | SHIPPED |
| Comparison | Order corpora; LT/LEQ strict/reflexive relation | SHIPPED (post-order_le fix) |
| Hierarchy | subset/containment/generalizes; specialization edges | SHIPPED (655 edges) |
| Temporal | temporal_logic corpus; past modalities; obligations | SHIPPED |
| Causal | precedence_causation_bridge (precedence + enablement) | SHIPPED |
| **Deictic (I/you, here/there, now/then)** | — | **OPEN — the one empty cell** |

- Mutual entailment is the LT/converse machinery.
- Combinatorial entailment is *literally* the four-discipline transitivity
  family and every derivation edge specialize.py emits: **derived relational
  responding with machine adjudication**, which RFT as a psychology never
  had an executable instance of. That is the leapfrog: RFT theorizes that
  untrained relations emerge from trained ones; our derivation graph
  produces and *verifies* them.
- Transformation of stimulus function is the A:B::C:D recombinant pointer
  (1.000 held-out at trained depth): what holds of one skeleton member
  transfers through the relation to another.
- The deictic cell decomposes exactly into the rest of this document:
  I/you = frame ownership (§1), here/there = reference frames (§2),
  now/then = the shipped past modalities. **The three directions are one
  direction**, and the coverage table is the audit that shows it.

Work items: keep the table above as a living coverage audit (re-adjudicate
at each release); author the deictic cell only through §1/§2 machinery
(no bespoke deixis corpus — deixis is what ownership + reference frames +
tense jointly produce); cite RFT in the blog/README positioning when the
deictic cell closes.

---

## 4. Self-verifying theories: a boundary to keep, and a corpus to write

Willard's self-verifying systems escape Gödel's second incompleteness
theorem by weakening arithmetic until consistency is provable internally.
Two consequences for us, in order of importance:

1. **Architectural principle (keep, never build):** this repository's trust
   roots are deliberately external — Lean verifies, independent adversarial
   review audits, seeds regenerate, digests pin. Nothing in the system
   attests to its own soundness, and nothing should: the receipt system is
   the closest approach, and its per-session key means receipts prove
   *freshness of retrieval*, never *correctness of content*. Any future
   slice that drifts toward self-attestation (a verifier verifying its own
   verdicts, a WRITE gated by the writer's own scoring) should be caught by
   review with this section as the cited rule.
2. **Corpus opportunity — provability logic.** GL (Gödel–Löb logic) is a
   modal logic with □ read as "provable": K axiom, Löb's axiom
   □(□p→p)→□p, no reflection. Its shape against our shipped
   `temporal.induction.temporal_induction_axiom` is a genuinely interesting
   **registered prediction P-CF4:** Löb and temporal induction will share an
   archetype (nested-implication-under-modality silhouette) but NOT a typed
   twin — an archetype-shared near-miss like ALWAYS/MEET, because the modal
   laws differ in exactly the way that matters (induction has the reflection
   GL forbids). A small `provability` corpus (Löb, Gödel II as a statement,
   a consistency assertion, Willard's exception as the boundary case) would
   make the mathematics of self-reference itself corpus subject matter —
   the discipline where `verified_by` links are most poetic, since Lean can
   check Löb.

Work items: provability corpus lane (post-physics.frames; smaller);
P-CF4 adjudication; the architectural principle recorded here is itself the
deliverable for the trust boundary.

---

## 5. BERT, BookCorpus, and WordNet: the storage bet, named

The human-created "metadata graph about all English words" from the
pre-LLM era is **WordNet** (Princeton, Miller, 1985–): synsets (sense
equivalence classes), hypernymy, antonymy, meronymy. FrameNet and ConceptNet
are its cousins. The comparison with BERT cuts exactly along this
repository's thesis line:

**What BERT did that we deliberately refuse:** buy knowledge with
parameters — 110M weights over BookCorpus + Wikipedia, opaque,
correction-by-retrain. Our measured counter-evidence at miniature scale:
weight-learned lexicon collapses to chance OOD (0.508) while the same
lexicon supplied symbolically holds 0.587 and the hybrid reaches 0.805;
880k-param encoders cap ~0.71 on exact comparison the symbolic layer does
perfectly for free. BERT solved these with scale; we solve them by refusing
to ask weights to do closed-form work.

**Convergences already in the repo:** the span-pointer extractive answerer
is structurally BERT's SQuAD head at ~1/130th the parameters, minus
pretraining. Twin classification is BERT's sentence-pair task, solved
symbolically.

**Two things worth taking:**

1. **Masked skeleton modeling.** BERT's masked-LM objective transposed to
   structure: mask a node in a canonical skeleton (or a level in a tree
   path), recover it by *pointing*, over corpus skeletons and generated
   instances. A self-supervised pretraining objective the tiny models have
   never had, native to the pointer architecture, and cheap to try against
   the existing analogy/solvex baselines. Registered prediction P-CF5:
   masked-skeleton pretraining improves the recurrent arm's depth OOD
   (0.226 →) more than it improves in-distribution scores — if the
   objective teaches structure rather than content, its gains should
   concentrate where structure is the bottleneck.
2. **WordNet as a retrieval store — see §6.** WordNet failed to compose
   with statistical NLP because nothing could verify it or point into it.
   We have both: RETRIEVE returns pointable material with receipts, and the
   ladder keeps lexical knowledge at its honest epistemic station.

**Already leapfrogged (state it once, in the blog, then stop):** WordNet's
synsets are prose-defined equivalence classes; our twin groups are the same
idea with canonical skeletons, typed slots, machine adjudication, and Lean
anchors where the discipline allows. "WordNet for formal structure" is a
fair one-line description of the corpus.

---

## 6. WordNet integration: assessed against the actual download

Inspected artifact: `C:\Users\displ\Downloads\english-wordnet-2025-json.zip`
(Open English WordNet 2025, JSON edition, from
github.com/globalwordnet/english-wordnet). 73 files, **72 MB uncompressed**:
`entries-*.json` (lemma → part-of-speech → senses → synset ids) and
`<pos>.<lexname>.json` synset files (definition, examples, members,
typed relations — attribute, hypernym, etc., plus interlingual `ili` ids).
Verified by direct read: entry `'tween` → sense → synset `00252367-r`;
synset `able` carries definition, four examples, members, and attribute
edges. The shape maps one-to-one onto `RetrievalItem`:

    item_id:  wordnet:<synset-id>
    source:   "wordnet"
    title:    members joined (the synset's lemmas)
    text:     definition + examples
    epistemic_status: "empirical"     # lexicographic observation, never more
    source_ids: (synset-id, *related synset ids)
    aliases:  (*members, synset-id)

**Meaningful-extension verdict: yes, on three concrete paths; otherwise
skip it.** The gate the user set ("only if it extends knowledge/thought/
response meaningfully") is met by:

1. **Open-vocabulary glossing for ASK/render.** Today a request term
   outside the corpus's aliases is a dead UNKNOWN. With a wordnet store,
   the miss chain gains a rung: unknown term → synset lookup → synonym
   members → retry corpus aliases through the synonyms. "Thesaurical
   twins" — the phrase from the project's founding conversation — becomes a
   literal mechanism: WordNet coordination relations bridging user
   vocabulary to corpus vocabulary.
2. **RFT coverage at lexical scale (§3).** Synonymy = coordination,
   antonymy = opposition, hypernymy = hierarchy — the relational-frame
   taxonomy instantiated over ~120k synsets instead of 213 statements,
   giving the neighborhood-fallback real semantic structure instead of
   token overlap.
3. **Renderer enrichment without weight growth.** The demo's English gloss
   comes from a toy lexicon; WordNet members + examples give the symbolic
   renderer lexical variety with zero parameters — the leapfrog claim in
   its most demonstrable form.

**Epistemic discipline (non-negotiable):** wordnet records enter at
`empirical` and are `trusted=True` only in the provenance sense (file
digest), never in the proof sense; a wordnet record must never ground a
frame verdict above UNKNOWN→admission, and never appears in `verified_by`
chains. The status-laundering controls from the retrieval review (F1) apply
verbatim and must gain a wordnet case before the store ships.

**License (recorded before any use, per house rule):**

- Open English WordNet: **CC-BY 4.0** (per github.com/globalwordnet/
  english-wordnet). Redistribution permitted with attribution.
- Inherited Princeton WordNet content: Princeton WordNet 3.0 license
  (wordnet.princeton.edu/license-and-commercial-use) — permissive,
  requires the Princeton copyright notice and disclaimer to accompany the
  data.
- The downloaded zip contains **no license file**, so obligations are
  recorded here by reference and must ship in an ATTRIBUTION note beside
  any store artifact.
- **Storage decision:** 72 MB does not enter git. The zip stays external
  (current path above; loader takes a `--wordnet` path argument, feature
  absent when the file is absent — same graceful-absence pattern as the
  jsonschema fallback). Because CC-BY permits it, a *derived, reduced*
  extract (e.g., only synsets reachable from corpus/lexicon terms, likely
  <2 MB) MAY be committed with attribution — decide when the adapter
  lands, and if committed, the extract regenerates from the zip via a
  seed-style script under `check_regeneration`-equivalent discipline.

**Registered prediction P-CF6:** the wordnet store will improve the
demo's request-term coverage (measurable: fraction of held-out English
paraphrase terms that resolve to a corpus alias through synonym bridging)
without changing a single frame verdict — if any verdict changes, the
laundering controls failed and the slice is rejected.

Work items: `wordnet` store adapter behind the existing
`UnifiedKnowledgeStore` interface with graceful absence; laundering
negative controls; ATTRIBUTION file; synonym-bridging rung in the miss
chain; reduced-extract decision; P-CF6 adjudication.

---

## 7. Sequencing

1. **ASK return channel — SHIPPED executable first cut.** Its return path is
   the runtime user-frame update rule; schema-level FrameSpec ownership remains
   in step 3.
2. **physics.frames corpus lane — SHIPPED first cut.** P-CF3 fired; P-CF2
   missed for the scope/template boundary described in §2. Frame ids now
   resolve to their declaration nodes.
3. **Frame ownership + visibility-filtered updates** + Sally–Anne demo
   (P-CF1) — after ASK, before nesting.
4. **WordNet store adapter** (P-CF6) — independent of 2–3; can run as a
   parallel worktree slice; license/attribution ships with it.
5. **Masked skeleton modeling** (P-CF5) — experiment track, GPU-bound,
   schedulable whenever the GPU is free.
6. **Provability corpus** (P-CF4) and **nested frames** — later; smaller;
   both benefit from the earlier slices' conventions.

Every prediction P-CF1..6 follows the house rule: registered here before
any adjudicating tool runs; fired and missed are both reportable; misses
are recorded in DISCOVERIES with the same prominence as hits.
