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

A fourth review (v0.10 loop coordinator, post-quantifier-merge) held the
L1–L4 / index-relative / R-register spine and required: (1) inherit the
**shipped** `FORALL`/`EXISTS` representation and alpha-convention caveat;
(2) **numeric registration** for every P-LS (fragment, suite size, floors);
(3) P-LS5 = formal **coverage-instrument pipeline** shape; (4) **LOST dual**
for round-trip growth; (5) **twin-null / GC4–GC5** discipline for NL corpus
entries; (6) **operational** P-LS4 (unit-tested pure feature functions);
(7) discourse **after** harness session so no second memory is born. Applied
in §2, §5.1, §5.4, §7–§8.

Status: design guidance. Implementation may proceed on a **separate** branch
(`feature/language-structure-impl`) without blocking on this doc’s merge;
predictions still bind adjudication. Corrects an
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
| Quantification / binders | **Shipped formal:** `FORALL(X, BODY)` / `EXISTS(X, BODY)` as ordinary non-commutative call heads; binding via **slot recurrence** in the skeleton (`FORALL⟨?0, EVEN⟨*(2, ?0)⟩⟩`). See §5.1 scope pillar and ANALYSIS quantifier slice (`f24ddeb` family). | Formal: measured (Goedel full-statement **43.2%** post-quantifier). **Alpha-invariance is a Barendregt-style naming convention**, not free: first-occurrence numbering is invariant under *whole-statement injective* renaming; sibling binders in templates deliberately reuse `{x}` — a twin with distinct inner binder names will **not** match until normalized. NL surface scope/binding still largely open. |
| Discourse / common ground | Session + frames + obligation ledger (partial) | **No first-class multi-utterance discourse store yet** (and must not fork a second memory—§8) |
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
| **Scope / quantification / binding** | Negation scope, ∀/∃, modality, conditionals, bound anaphora | **Formal shipped:** `FORALL`/`EXISTS` call heads + slot-recurrence binding (quantifier merge); NEG; frame `scope` object for fiction/physics. Measured caveat: alpha-invariance only under whole-statement injective renaming (Barendregt naming convention); sibling binders share slot names by design — distinct-name twins miss. | **Do not re-promise “explicit scope” in the abstract** — inherit this representation for formal terms and for any NL term that lowers to the same algebra. NL-specific gaps: surface quantifier syntax, bound anaphora across discourse, modality/conditionals as NL constructors. Binding theory for pronouns remains open. |
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
   Entity/event/state; quantification/binding via the **existing** formal
   representation where applicable—`FORALL(X, BODY)` / `EXISTS(X, BODY)` as
   non-commutative call heads with binding by slot recurrence (not a second
   binder calculus)—plus the documented alpha-convention limit (sibling
   templates reuse binder slots; distinct inner names do not twin until
   normalized); tense/aspect/modal; speech-act type; reference markers (as
   bindings into discourse, not free strings); discourse relations; narrative
   constructors; comparison/modifiers as already designed.

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
Golden-chicken prose-as-policy is the debt. Implementation may clear it via
`narrative.realize.v1` briefs (P-LS3) while this doc is still under review;
adjudication still requires the registered floors, not vibes.

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

Registration discipline matches formal v0.10 slices: each prediction pins a
**named fragment**, **suite size**, and **numeric floors** where applicable.
Qualitative pass/miss alone is not enough (R14 / goalpost drift). When a
fragment grows, mechanical dual-pass / LOST accounting is mandatory from day
one (`scripts/verify_slice.py` is the pattern: mechanical 80% as one command;
judgment only for design attack + sampled adjudication).

### Registration template (required fields)

For every P-LS before its adjudicating implementation:

| Field | Meaning |
|---|---|
| `fragment_id` | Grammar + lexicon scope (e.g. `langgen.xlang.v1`, `narrative.realize.v1`) |
| `lexicon_n` / `pattern_n` | Closed inventory sizes |
| `suite` | Generator + seed + **N ≥ floor** (machine-generated preferred) |
| `metric floors` | Exact rates or counts registered in advance |
| `LOST policy` | LOST=0 on dual-pass unless `--allow-losses` with row-by-row disclosure |
| `twin expectation` | When touching `data/*`: register group_counts / twin null or expected Δ **before** regen (formal null has held four consecutive head slices; NL must do the same) |
| `GC4/GC5` | Budget for pin movement; append-only registered acknowledgments (harness-checked) |

### Predictions

**P-LS1 — Dual of parse (round-trip).**  
- **Fragment:** `langgen.xlang.v1` (interlingua STMT/ASK/CMP/EVT + MOD; LEX_A and
  LEX_B as in `experiments/langgen.py`; both language realizers).  
- **Suite:** N ≥ **500** machine-generated terms from `gen_tree` at depth ≤ 2,
  fixed seed registered in the test module; both langs A and B.  
- **Floor:** exact canonical equality `canonicalize(P(R(t))) == canonicalize(t)`
  on **≥ 0.98** of the suite per language (allow documented refuse class for
  free modifier-order surface shuffle if R is non-deterministic—then R must
  offer a deterministic mode for the suite).  
- **Miss:** hand-picked suite only; or rate below floor; or LOST > 0 on a
  later fragment grow without disclosure (P-LS1b).

**P-LS1b — Round-trip LOST dual (mechanical).**  
When the realizer/parser fragment grows, every term that previously
round-tripped must still round-trip. Implement as a dual-pass over a pinned
suite file (or regenerate-at-base vs new), same spirit as
`verify_slice.py` dual-pass: **LOST=0** or every loss printed and counted.
Miss if growth silently drops prior round-trips.

**P-LS2 — Content refutation survives fluency.**  
- **Fragment:** `narrative.realize.v1` + golden-chicken frame (or successor
  brief).  
- **Suite:** N ≥ **20** realization variants that only swap licensed
  synonym/packaging for trait-denying content (silver vs golden) plus N ≥ 5
  controls that stay frame-legal.  
- **Floor:** **20/20** denying variants → L3 frame REFUTED (or equivalent
  separable tag); **0** laundering to VERIFIED via wording.  
- **Miss:** any denying variant accepted as index-VERIFIED.

**P-LS3 — Oracle story becomes a brief.**  
- **Fragment:** `narrative.realize.v1` (named plant/outcome patterns only).  
- **Suite:** golden-chicken oracle path + at least one alternate brief using
  the same patterns with different slots.  
- **Floor:** oracle still **5/5** VERIFIED steps; policy/module source of
  truth has **zero** hand-authored `@start:end` bind literals (binds only via
  `span_of`/`bind_spec` on realized text).  
- **Miss:** full beat strings or magic binds remain the policy source.

**P-LS4 — Preference only over index-admissible realizations (operational).**  
- **Fragment:** declared candidate generator + preference feature registry.  
- **Operational miss (testable):** every preference feature **must** exist as
  a **deterministic, unit-tested function** in the repo (pure: candidates +
  discourse snapshot → score/order key). A feature that cannot be written that
  way is **refused at review time**, not discovered at evaluation.  
- **Suite:** fixed candidate sets of size K ≥ 3 per item; N ≥ 30 items.  
- **Floor:** ranker cannot emit outside the candidate set (**0** OOV);
  frequency baseline reported on the same set; learned/stat ranker does not
  beat frequency by using any non-registered feature.  
- **Miss:** OOV emission; or a feature lands without a unit test; or
  denotation-changing candidates enter the set.

**P-LS5 — Coverage instrument (pipeline shape, not reinvented).**  
Adopt the formal coverage pipeline **verbatim**:

```text
pinned source → deterministic extract → classifier with precise refusal labels
  → audit fields must be 0 → per-row dual pass on every grammar change
  (LOST=0 or disclosed row-by-row)
```

- **Fragment:** declared NL fragment (initially e.g. simple clauses +
  modifiers + CMP + WH over a pinned synthetic or small extract).  
- **Suite:** pinned corpus/extract with SHA; refusal taxonomy registered
  before the run (expect precision to pay the way formal did: Goedel
  **32.8% → 43.2%** this cycle, with the largest “relation” gain revealed as a
  **parser artifact** only because labels were precise).  
- **Floor:** publish expressible fraction + refusal histogram before any
  scale/prover-like-text claim; audits analogous to
  `foreign_glyphs`/`carrier_residual` = 0.  
- **Miss:** marketing a rate without pinned source, refusal labels, or
  dual-pass discipline.

**P-LS6 — Deixis is composition, not a lexicon.**  
- **Fragment:** owner/frame/tense machinery + toy dialogue suite N ≥ 10.  
- **Floor:** **10/10** I/you/here/now resolutions use frame ownership /
  reference-frame / tense state; WordNet person-synset-only path is not
  sufficient for pass.  
- **Miss:** any pass that keys only on lexical person features.

**P-LS7 — Discourse state is load-bearing across turns.**  
- **Fragment:** session-shaped discourse store (after harness session—§8);
  toy entities N_kinds ≥ 2.  
- **Suite:** N ≥ 30 two-turn scripts (intro entity → anaphor).  
- **Floor:** **≥ 0.95** resolve when store intact; **1.0** miss (no invented
  referent) after wipe ablation on the same scripts.  
- **Miss:** wipe still “resolves”; or discourse is a second memory parallel to
  session rather than hosted by it.

**P-LS8 — Packed ambiguity filters before prefer.**  
- **Fragment:** declared ambiguity suite (scope or attachment), M ≥ 15 items
  with ≥ 2 candidates each.  
- **Floor:** preference never invoked on unfiltered forest; after hard
  filters, remaining set recorded; if >1 remain, system reports multi or
  ASK—not a silent unique parse.  
- **Miss:** forced unique parse with no alternative record when fragment
  claims ambiguity support.

**P-LS9 — Inference is reportable without commit.**  
- **Fragment:** named entailment fragment (e.g. story or formal mini-suite)
  N ≥ 15 pairs.  
- **Floor:** answers entailment/contradiction with **0** world mutations on
  the pure-query path; fragment id present on every answer.  
- **Miss:** only path mutates world to “infer.”

**P-LS10 — Index-relative false belief survives language.**  
- **Fragment:** Sally–Anne + realization of attitude report.  
- **Suite:** N ≥ 5 surface variants.  
- **Floor:** **5/5** frame-local VERIFIED / world box without L1/L2 illegal.  
- **Miss:** world-falsity collapses to undifferentiated illegal.

**P-LS11 — Strata visible in the trace.**  
- **Fragment:** harness or demo trace schema.  
- **Suite:** four injected failures (one per L1–L4).  
- **Floor:** **4/4** distinct tags/reasons.  
- **Miss:** collapsed single error string.

**P-LS12 — Fiction assert vs world assert.**  
- **Fragment:** golden-chicken (or successor) frame open/close.  
- **Suite:** N ≥ 5 fiction-premise asserts + exit check.  
- **Floor:** in-frame index-legal; **0** world-VERIFIED leaks on exit
  (demotion).  
- **Miss:** realizer path promotes fiction to world VERIFIED.

**P-LS13 — Twin null (or registered Δ) for NL corpus entries.**  
When NL nodes enter `data/*` via linguistic-twins / morphology / narrative
paths: **before** regen, register expected `group_counts` movement or
**twin null** (unchanged), matching the formal honesty instrument that has
held four consecutive head slices. Budget GC4/GC5 pin movement and
append-only registered acknowledgments (mechanically checked by
`verify_slice.py` acks).  
- **Miss:** silent twin churn or unacknowledged GC pin drift.

---

## 8. Work sequencing (compatible with v0.10)

v0.10 rightly prioritizes **formal** grammar heads and external verifiers.
Language-as-structure must not hijack that lane. Ordered so each step is
falsifiable and **dependencies are explicit**:

1. **Name the debt:** treat golden-chicken strings as realization debt (this
   doc + BACKLOG).  
2. **Story briefs as terms (P-LS3):** structured fields + named realizers;
   binds computed; register fragment `narrative.realize.v1`.  
3. **Round-trip (P-LS1) + LOST dual (P-LS1b):** langgen fragment; machine
   suite N ≥ 500; wire into a `verify_slice`-style check as soon as a slice
   owns the fragment.  
4. **ROADMAP-v0.10 item 5 — harness session first.** Prove the session shape
   (boot matrix, need dispatch, shared session memory) **before** promoting
   discourse to a product path.  
5. **Minimal discourse store (P-LS7)** — **only after step 4**, hosted **on**
   the session machinery so a **second memory system is never born**. A
   standalone pure module for unit tests is fine; wiring into conversation
   must not fork session state.  
6. **Scope/binding for NL** reuses formal `FORALL`/`EXISTS` + slot recurrence
   where terms lower to that algebra; do not invent a parallel binder
   calculus. Surface/discourse binding gaps close with coverage deltas and
   negative controls (P-LS8, R9).  
7. **WordNet** remains lexicon/sense-candidate plugin, never term algebra.  
8. **Preference models last (P-LS4):** features as unit-tested pure
   functions only.  
9. **NL coverage instrument (P-LS5)** when the fragment is worth measuring —
   same pipeline shape as formal.  
10. **Entailment-without-commit (P-LS9)** where useful.  
11. **Twin null / GC acks (P-LS13)** on every NL corpus touch.

Formal ingest and linguistic calculus share the kernel and the epistemic
ladder; they do not share one rushed grammar.

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
