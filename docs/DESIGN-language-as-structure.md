# Design: language as structure — text analysis and creation under the same kernel as proofs

Source: 2026-08-11 synthesis of the DESIGN series, plus a challenge to the
provisional claim that “surface English requires string templates.” The
challenge: natural language is formulaic on founding principles—identities,
subjects, modifiers, predicates, recursion, perspective, momentum (temporal
force), inequalities, comparison, variables—and analysis *and* creation of
text should flow under the same propose→verify discipline as a math prover.
A subsequent external review (same day) argued the first diagram under-specified
**discourse**: context/common ground, reference, scope/binding, pragmatics,
presupposition, information structure, morphosyntax, packed ambiguity, and
inference distinct from verification. That review is integrated in §5–§5.4;
the four conspicuously missing **coverage** pillars for “algebra rich enough
that an LLM is residual, not engine” are **discourse state, reference, scope,
pragmatics**.

A third review (context-blind; classical NLU/semantics lens) argued the doc
still inherits **pipeline assumptions** and misses **architecture** gaps:
intensional indices (fiction/belief vs world-truth), multi-strata legality,
gradience, joint inference vs feed-forward parse, load-bearing lexical
semantics, acquisition/CYC coverage failure mode, verifier tractability,
non-declarative semantic types, prosody, incrementality/dialogue update
semantics, and an undefended claim that the preference residual is “easier”
than generation. That review is integrated in §5.3–§5.3.2 and §6 (R10–R16);
accepted where it exposes real category errors, **refused where it demands
open-world NLU this project explicitly does not ship**.

Status: design guidance. Not an implementation slice. Corrects an
overstatement that appears in conversation and in thin readings of
“expressive rendering,” without retracting measured floors (parse-first,
closed-form equality, empirical WordNet boundary). Indexed from
`docs/BACKLOG.md` and related to:

| Document | What it already contributes |
|---|---|
| `DESIGN-concept-tokens.md` | Concept core vs extrinsic lexicon; realization is lookup/search, not weight-matrix English |
| `DESIGN-linguistic-twins.md` | **NL is another discipline corpus**; modifiers, comparisons, questions, bilingual twins |
| `DESIGN-epistemic-ladder.md` | Status is symbolic; weights only rank conjectures worth proposing |
| `DESIGN-frames-and-retrieval.md` | Fiction scopes; retrieval as action; story event as tactic; rendering as last step |
| `DESIGN-cognitive-frames.md` | ToM, physical frames, RFT coverage (coordination…deixis) |
| `DESIGN-scope-and-modality.md` | Scope beside template; past as mirror involution |
| `DESIGN-corpus-scale-and-programming.md` | Parse → address → pointer residual → external verifier (math *and* code) |
| `DESIGN-interactive-harness.md` | Microkernel session; registered paths; fluency never invents VERIFIED |
| `DESIGN-affect.md` | Attributed affect, not embedding-as-truth |
| `DESIGN-visual-structure.md` | Third modality: structure first, soft residual second |

---

## 1. The challenge, restated fairly

A prior conversational summary said, roughly: surface English is a thin
template layer; WordNet may dress licensed content; rich text is far.

That summary was **antagonistically useful** (it blocked WordNet-as-plot-engine
and fluency-as-truth) and **architecturally incomplete**. It treated
*implementation templates*—f-strings in the golden-chicken oracle—as if they
were a *design law*. They are not.

The challenge asserts a stronger and better-aligned claim already latent in
`DESIGN-linguistic-twins.md`:

> Natural language is not a new kind of object. It is another discipline
> whose statements have structural signatures. Surface forms are skins over
> shared skeletons.

If that claim is true for **analysis** (xlang/qa experiments: parse →
interlingua → residual lexicon alignment), it must be true for **creation**
in the dual direction. The *sentence-local* dual is still true but incomplete:

```text
# necessary but not sufficient (sentence-local dual)
analysis:   surface  →  parse  →  term(s)  →  verify / unify
creation:   intent   →  construct term  →  verify  →  realize surface
```

Multi-utterance language needs a **discourse state** in the loop (entities,
salience, common ground, temporal index, speaker/addressee)—see §5. The full
dual is closer to:

```text
analysis: surface → morphosyntax → candidate terms (possibly packed)
          → resolve against discourse → update discourse
          → world/frame/normative verify + entailment checks
creation: communicative goal → plan moves
          → construct term(s) under discourse + algebra
          → hard filters (legal) → preference ranking (preferred)
          → morphosyntactic realization → surface
          → discourse update
```

Creation is not “pick a template and fill blanks.” Creation is **term
construction under a grammar and a discourse**, then **morphosyntactic
realization**—the same duality as building a Lean proof term and
pretty-printing it. Templates are a *degenerate realizer* for a tiny grammar,
not the ontology of language.

This document accepts that challenge as the **target architecture** for
language, then states where the repo already sits, what would be self-deception,
and how the puzzle closes without becoming an LLM.

---

## 2. Symmetry map: linguistic constructs ↔ project machinery

These are not metaphors. They are the intended type alignment.

| Linguistic founding idea | Project structure | Status |
|---|---|---|
| Identity / sameness | Twin ladder; coordination (RFT) | Measured (formal); partial (NL) |
| Predication / statement | STMT / judgment; epistemic status on nodes | Designed; synthetic NL world ships |
| Subject / arguments | Typed slots; EVT(predicate, args…) in langgen | Synthetic bilingual world |
| Modifiers + recursion | Nested trees; commutative flatten for intersective stacks | Designed + OOD depth cliffs measured for residual |
| Variables / WH | UNKNOWN slots; unification (qa/solvex) | Measured (synthetic) |
| Inequalities / comparison | Order heads; CMP in linguistic twins | Formal order corpora + CMP design |
| Perspective / deixis | Owned frames; reference frames; tense | ToM + physics frames ship; deictic cell open as *composition* of them |
| Momentum / temporal force | Temporal modalities; plant/discharge obligations; precedence | Narrative + temporal_logic ship |
| Quantification / binders | Grammar heads (v0.10 formal priority); must be **explicit in NL algebra**, not smuggled into STMT | Formal coverage gap; NL scope/binding largely open |
| Discourse / common ground | Session + frames + obligation ledger (partial) | **No first-class multi-utterance discourse store yet** |
| Reference (he/that/ellipsis) | Entity ids + mention binds (story); visibility (ToM) | Span binds are local; anaphora/ellipsis across turns **open** |
| Speech acts / pragmatics | ASK vs GEN vs assert; WAITING channel; obligations | Partial; implication/presupposition **open** |
| Presupposition / accommodation | Frame premises + plant; no general accommodation calculus | **Open** |
| Information structure (topic/focus) | Absent as algebra | **Open** (preference inputs once legal set exists) |
| Morphosyntax | langgen linearizers; morphology corpus seeds | Thin; “linearize” must mean full morphosyntactic realization |
| Packed ambiguity | Matcher alternatives exist formally; NL parse is single-tree today | Candidate forests **open** |
| Entailment ≠ verification | specialize/twins/entails edges; compose ladder | Partial; not yet a unified NL inference layer |
| Communicative goal / planning | Controller policy; narrative constructors; need dispatch | Upstream planner distinct from “emit term” **under-specified** |
| Recursion / discrete infinity | Expression trees unbounded in principle | Depth-OOD is the honest wall for *learned residual*, not for symbolic trees |
| Contradiction | REFUTED vs frame/world | Ships |
| Question as equation | ASK / WH = open formula | Design + solvex-style demos |
| Translation | Twin + lexicon swap | xlang experiment |
| Proof of a sentence | Consistent extension of frame+world under narrative/logic laws | Story adapter is a *tiny* instance |

**Perspective and momentum** are not “vibes.” They are already first-class
elsewhere: owner/visibility is perspective; eventually/once/Chekhov is
temporal force. Realization must *expose* those structures, not replace them
with adjective choice. **Discourse** is the missing multi-turn home for the
same idea: what is given, who is salient, what the common ground already
holds.

---

## 3. Correction: what “templates” actually are

| Sense of “template” | Design status |
|---|---|
| **String template** (`f"{agent} wanted {desire}."`) | Provisional linearizer for a one-off demo. Not the architecture. |
| **Structural template / head schema** (corpus `template`, langgen STMT/EVT/CMP) | **The real grammar.** Same family as formal statement templates. |
| **Linearization rules** (SVO vs SOV; adjective order; question particle) | Part of the extrinsic *realization grammar*—deterministic or ranked among licensed variants. |
| **Lexicon entries** (concept id → word forms) | Extrinsic store; WordNet may enlarge *empirical* candidates. |

**Design law (replaces the overstatement):**

> Surface English is the **linearization** of a well-typed linguistic term
> (plus optional empirical packaging). It is not free generation, and it is
> not required to be a handful of f-strings—but every emitted token sequence
> must be recoverable to a term the kernel can re-parse and re-verify.

If re-parse fails, the emission is GIBBERISH or a realizer bug—not a “style
choice.”

That is the same honesty boundary as a proof pretty-printer that must not
emit text Lean cannot read back when fidelity is claimed.

---

## 4. Analysis and creation as one prover loop

### 4.1 Analysis (text → structure)

```text
string
  → parse (linguistic grammar / morphological hooks)
  → canonical term (interlingua / concept ids)
  → epistemic placement (UNKNOWN holes, VERIFIED if corpus-backed, …)
  → optional residual (sense choice, graded synonymy) with baselines
```

Measured lessons to keep:

- **Parse is the floor.** Char arms collapse; structure must be given or
  built by a real parser, not hoped for in weights
  (`DESIGN-linguistic-twins`, ANALYSIS).
- **Canon exposes residual size.** When the front-end already is the
  interlingua, the model has almost nothing left to learn—evidence that
  structure was the load-bearing part.
- **Equality and identity stay symbolic.** Soft classifiers do not own twins.

### 4.2 Creation (structure → text)

```text
goal or narrative/proof state
  → propose term constructors (GEN schemas / “tactics” of the linguistic calculus)
  → verify against world + frame + obligations + type rules
  → on success, linearize term → surface
  → optional residual ranks among licensed linearizations / lexicon picks
```

This is **propose → verify → repeat**, not **sample → hope**.

Golden-chicken today freezes a successful proof of a tiny story theorem.
The dual of a richer prover is a richer **linguistic/narrative calculus**,
not a larger bag of strings.

### 4.3 What “as easy as a math prover” honestly means

It means **the same control plane and the same epistemic discipline**, not
“equally solved today.”

Formal math already shows the real bottleneck: grammar **coverage** on open
sources is ~⅓ (v0.9). Natural language’s open coverage will be worse until
the linguistic head algebra and lexicon grow. Ease of *flow* in the
architecture can exist while *coverage* remains partial—exactly as Lean
search is easy to invoke and hard to solve at scale.

**Antagonistic reading of the aspiration:** if “as easy” means “fluent on
arbitrary English with no untranslatable remainder,” that is a different
product (frontier LLM). If it means “every sentence the system accepts or
emits is a typed object under laws, and search builds it,” that is this
project—and it is allowed to refuse most of the open web.

---

## 5. Completing the puzzle (higher-order architecture)

The puzzle pieces already on the table:

1. **Concept core** (ontology + skeletons)  
2. **Extrinsic lexicon** (words outside weights)  
3. **Epistemic ladder** (status closed-form)  
4. **Frames** (perspective, fiction, physics)  
5. **Temporal obligations** (momentum of plot)  
6. **Controller kernel** (propose/verify/trace)  
7. **Pointer residual** (only graded joints)  
8. **Coverage discipline** (measure reach before claiming scale)

The missing **keystone** is not “add WordNet to templates.” It is a single
**linguistic calculus** plus a **discourse state**, treated like any other
discipline under the kernel.

### 5.0 Evolved diagram (discourse-first)

The sentence-local sketch `surface ⇄ term algebra → verification` is kept as
the *inner* loop. The *outer* loop that makes multi-utterance language work:

```text
                    discourse / context / common ground
                    (entities, salience, topic/focus,
                     temporal index, speaker/addressee,
                     commitments, open obligations)
                              ↕
                ┌──────────────────────────┐
                │ Linguistic term algebra  │
                │                          │
                │ entity / event / state   │
                │ scope / quantification   │  ← first-class, not hidden
                │ tense / aspect / modal   │
                │ speech act / reference   │
                │ discourse relations      │
                │ narrative constructors   │
                └────────────┬─────────────┘
                     ▲       │
            parse    │       │ construct
         (forest OK) │       ▼
surface ── morphosyntax / realization ── surface
                     │
                     ▼
        candidate set C (jointly constrained; may re-enter parse)
                     │
           inference / constraint layer  (fragment-named)
              ↙          ↓          ↘
         index@world  index@frame  index@normative
         (corpus)     (belief/     (obligations,
                       fiction/     speech-act type
                       modal)       checks—not “true”)
                     │
                     ▼
        L1–L4 filtered realizations (task-relative hardness)
                     │
                     ▼
        preference over finite candidates only
        (shallow closed-form features—§5.3.5)
```

### 5.1 The four pillars (review-accepted gaps)

If the aim is an algebra rich enough that an LLM is **residual, not engine**,
four pillars were under-drawn in the first cut of this doc and must be
first-class:

| Pillar | Content | Partial machinery today | Gap |
|---|---|---|---|
| **Discourse state** | Introduced entities, salience, topic/focus, temporal context, speaker/addressee, common ground / commitments | Session ids; user frames; story beats; obligation ledger | No unified cross-utterance discourse object; no salience ranking |
| **Reference** | Pronouns, definites, deixis, ellipsis, “the former/do so” | Story `ElementMention` binds; ToM visibility; deictic *composition* plan in cognitive-frames | No anaphora resolver; no ellipsis reconstruction; binds are local spans |
| **Scope / quantification / binding** | Negation scope, ∀/∃, modality, conditionals, bound anaphora | Formal quantifier heads (v0.10); NEG; frame `scope` object | NL algebra must not bury these in STMT/MOD; binding theory largely unauthored |
| **Pragmatics / speech acts** | Assert vs question vs request vs command vs implication; felicity | `ActionKind` ASK/GEN; WAITING; narrative obligations | Presupposition, scalar implicature, indirect speech acts open |

These are **not** four new neural modules. They are four **symbolic state and
constructor families** the kernel must admit, with residuals only where
something remains graded (e.g. which salient entity a pronoun *might* pick
among legally consistent candidates).

### 5.2 Inventory of further linguistic structure (mapped, not ignored)

| Review item | Where it lives in this architecture | Legal vs preferred |
|---|---|---|
| Temporal/aspectual structure | Term algebra + temporal_logic + event ordering; aspect as constructors | Hard: inconsistent tense/aspect vs discourse time → REFUSED/REFUTED |
| Presupposition / accommodation | Frame premises + explicit accommodation moves that *update* discourse/common ground under rules | Hard: unaccommodatable presupposition → UNKNOWN/REFUSED, not silent invent |
| Information structure (topic/focus/given-new) | Features on terms *or* on realization requests; feeds preference among legal strings | Soft for packaging; hard if focus changes truth-conditions (clefts that smuggle claims) |
| Morphosyntactic realization | Agreement, case, inflection, articles, order, contractions—broader than “string linearize” | Hard: ill-formed morphosyntax is not a surface; soft: optional contractions/register |
| Ambiguity / underspecification | Parse → **packed forest** or candidate term set + constraints; discourse/world filters reduce | Hard filters first; preference only on survivors; may ASK if irreducible |
| Inference / entailment | Distinct from “is this accepted in the frame”: A⊢B, contradiction, equivalence, causal/temporal consequence via specialize/twins/compose + temporal laws | Hard symbolic where closed form exists; residual only for ranking *which* entailment to surface |
| Communicative goal / planner | **Upstream** of term construction: what move to make (answer, revise, plant, ask, abstain)—controller need-dispatch + narrative policy | Hard: illegal moves; soft: which legal move when several progress the goal |

### 5.3 Legality strata, intensional indices, and preference (architecture cut)

#### 5.3.0 The category error to fix first

A context-blind review correctly noted: **falsity is not illegality.** A hard
“world consistency” filter that blocks every false sentence would also block
lies, fiction, counterfactuals, hypotheticals, and attitude reports
(“John believes the earth is flat”). That would be a **category error** relative
to this repository—which already ships **frame-local VERIFIED** that can be
**world-REFUTED** (Sally’s basket; golden-chicken fiction; rotating-frame
suspensions).

So “world verifier as *the* hard gate on utterances” is **rejected**.
Verification is always **relativized to an index**:

| Index | Role | Example |
|---|---|---|
| **World / corpus tier** | Shared public commitments | Marble is in box |
| **Owned belief frame** | Agent’s information state | Sally: basket |
| **Fiction / hypothesis frame** | Premises under suspension | Golden chicken exists |
| **Modal / temporal index** | Accessibility / time | Eventually discharge plant |
| **Normative ledger** | Obligations, speech-act commitments | Chekhov outstanding |

Attitude and fiction operators belong **in the algebra** (or as constructors
that open/select an index), not as “illegal because false of the world.”

Asserting a world-false claim **as world-true** may still be REFUTED.
Reporting it **under BELIEVE(agent, ·)** or inside a fiction frame may be
VERIFIED relative to that index. The epistemic ladder already encodes this
discipline; the language architecture must **expose indices**, not collapse
them into one gate.

#### 5.3.1 Four notions of “legal” (do not conflate)

The second review noted the doc quietly mixed four notions. Split them:

| Stratum | Meaning | Default hardness | Notes |
|---|---|---|---|
| **L1 Grammatical** | Morphosyntactically well-formed in the active language | Hard (fragment) | Ill-formed → GIBBERISH / no parse |
| **L2 Semantically well-typed** | Well-typed term: arity, selectional types, speech-act type, scope binding | Hard (fragment) | Ill-typed → REFUSED as structure |
| **L3 Index-consistent** | Consistent with a **named** index (world, frame, time, modal base) | Hard *relative to index* | False-at-world can be true-at-belief |
| **L4 Normative / felicitous** | Obligations, speech-act conditions, social constraints | Hard *when declared* | Language-relative: see honorifics |

**Preferred** applies only after the strata the *current task* marks as hard
have been applied. Not every task uses L3-world; narrative generation uses
L3-fiction. Proof talk uses L3-corpus. User preference revision uses
L3-user-frame.

**Social deixis / honorifics (review accepted):** in Japanese/Korean-style
fragments, register can be **L1/L4 hard** given discourse social indices
(speaker/addressee status), not soft “style.” The hard/soft split is
**language- and fragment-relative**, not universal English prejudice.
English casual/formal variation may stay soft until a fragment declares
otherwise.

#### 5.3.2 Gradience (what we refuse to smuggle)

Vagueness (“tall”), coercion (“began the book”), loose talk, hyperbole,
metaphor, acceptability gradience: these **break a crisp admissible set** if
forced into classical truth-conditions for open English.

**Project stance (antagonistic and intentional):**

- The shipped product is a **growing closed fragment** with **declared**
  predicates whose evaluation is closed-form or index-relative.
- Open vague predicates are either **excluded from the fragment** (coverage
  miss), **typed as graded residual proposals** that never alone become
  VERIFIED, or **anchored** to explicit thresholds/comparatives in the algebra
  (`height(x) > θ` with θ bound).
- Metaphor/loose talk are **not** first-class generation targets. If admitted,
  they enter as **explicit operators** (METAPHOR, LOOSE) with denotations that
  do not launder into world VERIFIED.
- Acceptability gradience may inform **preference scores** among L1–L2 legal
  candidates; it does not replace L1–L2.

This is not a claim that natural language is crisp. It is a claim that **this
kernel only certifies what it can check**.

#### 5.3.3 Joint inference vs feed-forward pipeline

Review: attachment and sense need world/pragmatic information *during* parse;
a pure feed-forward forest-then-filter may be too weak; joint/abductive
inference is the real story.

**Accepted as factorization, not as “one neural joint model owns all layers.”**

```text
Processing order in the diagram is a *dependency factorization* for
engineering and tests—not a claim that humans or an optimal interpreter
must run left-to-right without revision.

Mechanism (project-shaped):
  - Maintain a candidate set C of (term, discourse-delta, index) triples
  - Constraints from L1–L4 eliminate or score candidates as soon as they fire
  - Parsers may emit packed forests; world/frame/discourse constraints may
    *re-enter* parse choice (re-rank or prune C) without becoming free prose
  - Residual proposers may suggest candidates into C; they never mark VERIFIED
  - Irreducible C → ASK / UNKNOWN / multi-answer report—not forced unique parse
```

That is joint **constraint solving over a finite candidate set**, not CYC-scale
abduction over open text, and not “the LLM is the joint model.”

#### 5.3.4 Lexical semantics is load-bearing (and must have a source)

Review: open-class meanings, selectional restrictions, idioms, constructions
carry most of the weight; the algebra’s easy skeleton is not enough.

**Where denotations come from in this project (ordered):**

| Source | Authority |
|---|---|
| Statement nodes / concept ids in `data/*` | VERIFIED inventory of predicates and identities |
| Typed slots + heads (selectional structure) | Hard L2 constraints |
| Composite concept tokens / idioms as **named constructs** with decompositions | Extrinsic composites, not free composition |
| Formal ingest (Lean-class) when correspondence holds | Extends inventory under coverage discipline |
| WordNet | Empirical sense candidates and glosses only |
| Open web unsupervised lexicon induction | **Not** an admission path to VERIFIED |

No romance: if the predicate is not in the inventory, the system cannot
honestly “know” it. Coverage growth is authoring + measured ingest (v0.9/v0.10
discipline), not hope.

#### 5.3.5 Preference residual: defended, narrowed

Review: ranking by “discourse coherence, focus, rhythm” re-imports full
competence; the residual becomes the engine through the back door.

**Load-bearing claim (now explicit):**

> A preference model is strictly easier than open generation **only if** its
> input is a **finite candidate set** already closed under L1–L2 (and task-
> relevant L3–L4), and its features are **closed-form or shallow**
> (length, template id frequency, focus-feature match to discourse topic
> tag, honorific-feature match, registered style id)—not free-form
> “understand coherence like an LLM.”

If a feature cannot be computed without unrestricted language understanding,
it **does not belong in preference**; either promote it to a symbolic
constraint or drop it. The residual ranks **labels of candidates**, it does
not invent candidates from ℝ^d prose space.

Baselines: uniform, frequency of realization pattern, length—always reported.

#### 5.3.6 Sense placement (unchanged core, sharpened)

**Sense is not style.** Wrong sense → wrong denotation → wrong index check.

| Stage | Sense handling |
|---|---|
| Parse / construct | Underspecified concept or explicit sense id; multi-sense stays multi-candidate in C |
| Index check | Sense fixed enough to evaluate at the index, **or** check the set and return UNKNOWN if verdicts disagree |
| Preference | Only among candidates already index-legal **and** denotationally equivalent for the check at hand |

Label:

```text
preference model over index-admissible realizations
(candidates already L1–L2 legal and task-L3/L4 legal)
```

### 5.3.7 Architecture gaps vs coverage gaps

| Kind | Examples | Response |
|---|---|---|
| **Coverage gaps** (second review) | Discourse store, anaphora, scope constructors, speech-act inventory | Grow algebra + state; pillars §5.1 |
| **Architecture gaps** (third review) | Intensional indices, legality strata, joint candidates, lexicon source, tractable fragments, non-declarative types, residual hardness proof | Fix definitions (this section); do not paper with more STMT bullets |

### 5.3.8 Further architecture items (third review)

| Item | Stance |
|---|---|
| **Non-declarative types** | Questions denote answer-sets / open terms; imperatives denote properties of future states or commanded updates—not truth-values. “Verify” means type-correct + felicitous + successful update/goal progress, not “true.” Algebra must type speech acts. |
| **Verifier tractability** | Entailment undecidable in general. Every shipped checker names a **fragment** (as formal coverage already does). No “world model of everything.” Frame problem: only registered fluents/events update. |
| **Acquisition / neologisms / CYC death** | Algebra extends by **seed authoring, measured coverage, PROVEN-WRITE path**—not self-expanding open NLU. Neologisms enter as UNKNOWN or empirical until authored. This is a deliberate anti-CYC control: refuse to pretend universal coverage. |
| **Prosody** | Primary carrier of focus/interrogativity in speech; punctuation is lossy. Treat as **optional modality** (like vision): symbolic prosody features when present; otherwise information-structure features underspecified. Not a v0.10 blocker. |
| **Incrementality / dialogue dynamics** | Left-to-right repair, split utterances, clarification, QUD, grounding acts. Discourse *state* needs **update semantics** (what each accepted move adds), not only a bag of entities. WAITING/ASK is a thin slice of clarification. Full incremental dialogue is later; design must not assume batch-only utterance pairs forever. |

### 5.4 Layers (order is load-bearing)

1. **Discourse / context state (symbolic, session-lived)**  
   Entities, salience, topic/focus, temporal index, speaker/addressee,
   common-ground commitments, open questions/obligations. Updated on every
   accepted utterance. Kernel session is the natural host (`DESIGN-interactive-harness`).

2. **Communicative intent / planner (symbolic + optional ranker)**  
   Chooses among registered moves: assert, ask, revise, plant, retrieve,
   abstain—before building a full sentence term.

3. **Term algebra (symbolic)**  
   Entity/event/state; **explicit** scope/quantification/binding; tense/
   aspect/modal; speech-act type; reference markers (as bindings into
   discourse, not free strings); discourse relations; narrative constructors;
   comparison/modifiers as already designed.

4. **Morphosyntactic realization (symbolic)**  
   Language-specific rules: order, agreement, inflection, articles,
   contractions. Replaces ad hoc f-strings. langgen A/B is the prototype.
   “Linearize” in older prose means this whole layer.

5. **Inference / constraint layer (symbolic, fragment-bounded)**  
   Entailment, contradiction, temporal/causal consequence, twin/specialize
   edges—**not** the same button as “accept this transition into state.”
   Inference *explains and projects*; verification *commits* at an index.
   Every checker names its decidable/search-bounded fragment (§5.3.8).

6. **Index-relative verifiers (symbolic)**  
   World/corpus, belief, fiction/hypothesis, modal/temporal, normative—**not**
   one world-truth gate. Fed by discourse-resolved, typed terms (including
   non-declarative types for questions/commands).

7. **Lexicon (extrinsic, load-bearing inventory)**  
   Concept/sense → forms **and** denotations anchored to authored/ingested
   nodes. Project lexicon first; WordNet sense *candidates* only. Idioms as
   composite constructs. Multi-sense stays in C until index checks resolve.

8. **Preference model (optional, tiny, soft, defended-narrow)**  
   Finite candidates + shallow features only (§5.3.5). Never invents denotation
   or coherence-from-prose.

9. **Kernel session**  
   WAITING, registered paths, boot matrix, discourse update semantics (even
   if initially thin), refuse unregistered inventiveness.

### 5.5 What grows when language “gets rich”

Richness is **depth of algebra + discourse machinery + lexicon coverage**,
not parameter count:

- discourse updates and reference resolution tests;
- scope/binding constructors with negative controls;
- presupposition/accommodation as explicit moves;
- packed parse forests with filter-then-rank;
- morphosyntax beyond three f-strings;
- planner coverage over speech acts;
- preference only after legality.

Depth-OOD and coverage measurements remain honesty instruments. If the
algebra claims relative clauses but realization only emits three patterns,
that is incomplete dual—not a reason to jump to neural prose.

### 5.6 Models and external corpora (repositioned)

| Fuel | Role for language-as-structure |
|---|---|
| Synthetic interlingua worlds (langgen) | Controlled proofs of residual size; extend with multi-turn discourse toys |
| Morphology / narrative / temporal nodes | Structural laws already in-graph |
| Formal Lean-class sources | Ingest spine for math/code; *not* NL teacher; scope/binder heads still relevant |
| WordNet | Empirical forms/relations; **sense candidates**, never structure authority |
| Wikipedia/COCA | Challenge sets for coverage / discourse hardness—not authorities |

A “grammar model” that **owns** structure from wiki text remains rejected.
A residual that **proposes** parses, reference candidates, or ranks
**legal** realizations is welcome once baselines exist.

---

## 6. Antagonistic realism: where the challenge can fail

Register these as ways the thesis dies or must be narrowed—not as excuses to
avoid trying.

**R1 — Open English is not a closed algebra today.**  
Underspecification, implicature, metaphor, and discourse anaphora exceed the
current term algebra. The honest product is a **growing closed fragment**,
not universal English. Coverage numbers must be published the way v0.9 did
for Lean sources.

**R2 — Creation without world *and discourse* coupling is confabulation.**  
A pure syntactic constructor that never hits frame/world checks—or that never
updates/respects common ground—can emit well-typed nonsense relative to the
conversation. Content and discourse verification are not optional “later.”

**R3 — Realization is not free of policy.**  
Word order and morphology encode information. Multiple legal realizations
exist; choosing among them is preference—not proof of understanding.

**R4 — The synthetic bilingual world is not the open web.**  
xlang/qa successes license the *architecture*, not a claim that full English
is solved. Same discipline as 221-node twins vs Goedel-scale coverage.

**R5 — Depth and discrete infinity still hurt residuals.**  
Unbounded modifiers are in the design; learned arms already show depth cliffs.
Symbolic trees scale; tiny nets may not. Prefer search over deeper constructors
to hoping recurrence invents English.

**R6 — Demo debt.**  
Golden-chicken still freezes prose in the oracle policy. Until briefs are
terms and sentences are realizations of verified terms, the *practice*
under-sells the *design*. That debt is engineering priority, not evidence
against the challenge.

**R7 — Hybrid edge discipline.**  
A larger model may propose candidate terms, reference resolutions, or
realizations. If it ever owns equality, twin identity, frame consistency, or
discourse commitment, the project has become a wrapper.

**R8 — Preference must not launder sense or reference.**  
If a ranker can change denotation (wrong WordNet sense, wrong pronoun
antecedent) and still display as VERIFIED, the strata cut has failed. Sense
and reference live in candidate set C and index checks (§5.3).

**R9 — Pillars without tests are prose.**  
Discourse/reference/scope/pragmatics as design labels without negative
controls are decoration. Each pillar needs at least one
REFUSED/REFUTED/UNKNOWN control before it is “shipped.”

**R10 — Falsity ≠ illegality.**  
A system that hard-fails every world-false string has regressed on frames/ToM.
Attitude and fiction operators must select indices; only *unguarded*
world-assertion of false content is world-REFUTED.

**R11 — One mushy “legal” score is a design bug.**  
L1–L4 must be separable in traces (grammatical vs typed vs index vs
normative), so debugging does not blame “the verifier” for honorific or
parse failures.

**R12 — Open gradience is not a silent soft gate.**  
Vague/metaphorical open English must not become VERIFIED by preference
score. Exclude, grade as proposal, or anchor—never launder.

**R13 — Residual hardness must remain true.**  
If preference features require unrestricted coherence understanding, the
architecture has failed open; shrink features or promote constraints
(§5.3.5).

**R14 — CYC death by coverage.**  
If algebra growth is unmeasured open authoring without coverage instruments
and refuse-paths, the project repeats classical NLU failure. v0.9 discipline
applies to NL fragments.

**R15 — Undecidable “world verifier.”**  
Any entailment/world check without a named fragment is an overclaim.

**R16 — Non-declaratives are not bools.**  
Verifying a question as true/false is a type error; speech-act types must
drive the check.

---

## 7. Registered predictions (before implementation)

**P-LS1 — Dual of parse.**  
There exists a realizer R and parser P on a non-trivial fragment such that
for terms t in a test suite, P(R(t)) =_canon t (canonical equality). Miss if
only hand-written strings pass round-trip.

**P-LS2 — Content refutation survives fluency.**  
A realization of a term that contradicts frame premises is REFUTED by the
same frame executor path as today’s trait checks, independent of wording
variants in the lexicon. Miss if synonym packaging bypasses REFUTED.

**P-LS3 — Oracle story becomes a brief.**  
Golden-chicken (or successor) can be expressed as a structured brief + search
or scripted constructors *without* storing full English sentences in the
policy, except as realizer outputs. Miss if policy still embeds whole beat
strings as the source of truth.

**P-LS4 — Preference only over index-admissible realizations.**  
Any learned or statistical ranker is evaluated against a frequency baseline
on the **same finite candidate set** after L1–L2 and task-L3/L4 filters;
unlicensed tokens cannot appear; no candidate that changes denotation is
admitted. Preference features are closed-form/shallow (§5.3.5) or the
prediction is withdrawn. Miss if the ranker emits OOV prose, alternate
senses, or requires unrestricted coherence modeling to beat frequency.

**P-LS5 — Coverage before scale claim.**  
A public coverage instrument for open English (or a declared fragment such as
“simple clauses + modifiers + CMP + WH”) reports expressible fraction before
any claim of prover-like text creation at scale. Miss if marketing outruns
measurement (v0.9’s lesson applied to NL).

**P-LS6 — Deixis is composition, not a lexicon.**  
I/you/here/now in generated or parsed text resolve through owner/frame/tense
machinery, not through WordNet person-deixis alone. Aligns with cognitive-
frames deictic cell.

**P-LS7 — Discourse state is load-bearing across turns.**  
A two-turn dialogue where turn 2 uses a pronoun or definite whose only legal
antecedent is introduced in turn 1 succeeds iff the discourse store carries
that entity; wiping the store (ablation) forces ASK/UNKNOWN/REFUSED rather
than a guessed referent. Miss if turn 2 “works” with empty discourse via
fluent default.

**P-LS8 — Packed ambiguity filters before prefer.**  
On a controlled scope or attachment ambiguity, the system retains multiple
candidates until a hard constraint (world/frame) eliminates all but a legal
subset; preference never runs on the raw unfiltered forest. Miss if a single
parse is forced without recording alternatives when the fragment claims
ambiguity support.

**P-LS9 — Inference is reportable without commit.**  
There exists a path that answers “does A entail B?” (or contradiction) using
symbolic machinery without writing B into world state as VERIFIED. Miss if
the only way to “infer” is to accept a state transition that mutates the
world. The checker names its fragment.

**P-LS10 — Index-relative false belief survives language.**  
A generated or parsed attitude report “Sally believes the marble is in the
basket” can be frame-local VERIFIED while world holds box, without the
utterance being treated as grammatically illegal. Miss if world-falsity
blocks the sentence at L1/L2 or as a single undifferentiated “illegal.”

**P-LS11 — Strata visible in the trace.**  
At least one demo/trace distinguishes L1 parse failure, L2 type failure,
L3 index REFUTED, and L4 normative REFUSED as separate stop reasons or
evidence tags. Miss if all four collapse to one error string.

**P-LS12 — Fiction assert vs world assert.**  
Inside an open fiction frame, asserting frame premises is index-legal; the
same string as unguarded world assertion is not automatically world-VERIFIED
on exit (demotion rules). Miss if fiction content leaks as world VERIFIED
via the realizer.

---

## 8. Work sequencing (compatible with v0.10)

v0.10 rightly prioritizes **formal** grammar heads and external verifiers.
Language-as-structure must not hijack that lane. Ordered so each step is
falsifiable:

1. **Name the debt:** treat golden-chicken strings as realization debt (this
   doc + BACKLOG).  
2. **Story briefs as terms:** desire/obstacle/outcome/plant as structured
   fields only; English only via R(·).  
3. **Round-trip tests (P-LS1)** on the existing langgen interlingua + both
   language realizers.  
4. **Minimal discourse store** for multi-turn entity intro + pronoun
   resolution (P-LS7)—even a toy two-entity world beats sentence-local only.  
5. **Expand linguistic constructors** (scope/binding first-class) only with
   coverage deltas and negative controls (P-LS8, R9).  
6. **WordNet** remains lexicon/sense-candidate plugin, never term algebra.  
7. **Preference models last**, over admissible sets only (P-LS4); sense not
   in the preference tail.  
8. **Open-English coverage instrument** when the fragment is worth measuring
   (P-LS5).  
9. **Entailment-without-commit** path where useful (P-LS9).

Formal ingest and linguistic calculus share the kernel and the epistemic
ladder; they do not share one rushed grammar. Discourse state should reuse
session/frame machinery rather than invent a second memory system.

---

## 9. Relation to the “template / WordNet / rich text” thread

| Claim from earlier discussion | Disposition |
|---|---|
| WordNet must not own plot or truth | **Stands** |
| Fluency must not invent VERIFIED | **Stands** |
| Surface English *requires* string templates | **Retracted as design law**; demoted to provisional realizer |
| Language is formulaic structure dual to equations | **Accepted as target**; already sketched in linguistic-twins |
| Analysis and creation under one prover-like loop | **Accepted**; creation = plan+construct+verify+realize+discourse-update |
| Sentence-local dual is enough | **Rejected**; discourse pillars are coverage gaps |
| World-truth as sole hard gate | **Rejected**; intensional indices (architecture) |
| One notion of “legal” | **Rejected**; L1–L4 strata, task-relative |
| Sense belongs in style residual | **Rejected**; denotation → candidate set / index check |
| Preference may use full coherence LLM | **Rejected**; residual hardness claim narrowed (§5.3.5) |
| Feed-forward only | **Softened**; factorization + joint candidate set C |
| Open gradience as soft VERIFIED | **Rejected**; fragment/anchor/propose only |
| Lexicon is residual packaging | **Softened**; denotations load-bearing, authored/ingested |
| Universal NLU / CYC acquisition | **Rejected**; measured coverage + refuse |
| Rich text from wiki/WordNet as structure | **Rejected** |
| Statistical non-neural weights | **OK** for preference over finite candidates |
| Neural structure-owner on open text | **Rejected** |

---

## 10. One-sentence north star

**Text is a morphosyntactic interface to typed, index-relative structure under
a discourse—not a place where world truth, common ground, or denotation is
invented by fluency—and the same kernel that proves a conjunction can, in
the fragment it actually implements, plan a speech act, construct a scoped
term at a named index, resolve reference, refuse type errors and failed
presuppositions, report entailments without silent commit, realize only
stratum-legal forms, rank a finite candidate set with shallow features, and
ask when the information state does not determine a unique move.**

That is the completion of the puzzle under antagonistic realism: coverage
pillars (discourse, reference, scope, pragmatics) plus architecture pillars
(intensional indices, legality strata, joint candidates, tractable fragments,
defended residual)—without surrendering the project to open-world NLU or a
back-door LLM engine.
