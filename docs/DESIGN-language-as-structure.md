# Design: language as structure — text analysis and creation under the same kernel as proofs

Source: 2026-08-11 synthesis of the DESIGN series, plus a challenge to the
provisional claim that “surface English requires string templates.” The
challenge: natural language is formulaic on founding principles—identities,
subjects, modifiers, predicates, recursion, perspective, momentum (temporal
force), inequalities, comparison, variables—and analysis *and* creation of
text should flow under the same propose→verify discipline as a math prover.

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
in the dual direction:

```text
analysis:   surface string  →  parse  →  canonical term  →  verify / unify
creation:   goal / state    →  construct term  →  verify  →  linearize to surface
```

Creation is not “pick a template and fill blanks.” Creation is **term
construction under a grammar**, then **linearization**—the same duality as
building a Lean proof term and pretty-printing it, or building an expression
tree and rendering LaTeX. Templates are a *degenerate linearizer* for a tiny
grammar, not the ontology of language.

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
| Quantification / binders | Grammar heads (v0.10 formal priority) | Formal coverage gap; NL quantifiers later same spine |
| Recursion / discrete infinity | Expression trees unbounded in principle | Depth-OOD is the honest wall for *learned residual*, not for symbolic trees |
| Contradiction | REFUTED vs frame/world | Ships |
| Question as equation | ASK / WH = open formula | Design + solvex-style demos |
| Translation | Twin + lexicon swap | xlang experiment |
| Proof of a sentence | Consistent extension of frame+world under narrative/logic laws | Story adapter is a *tiny* instance |

**Perspective and momentum** are not “vibes.” They are already first-class
elsewhere: owner/visibility is perspective; eventually/once/Chekhov is
temporal force. Language linearization must *expose* those structures, not
replace them with adjective choice.

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
**linguistic calculus** treated like any other discipline:

```text
                    ┌─────────────────────────┐
                    │  Linguistic term algebra │
                    │  STMT, EVT, CMP, MOD, … │
                    │  + narrative constructors │
                    └───────────┬─────────────┘
              parse ▲           │ construct
                    │           ▼
         surface ───┴── linearize ── surface
                    │
                    ▼
         world/frame/obligation verifiers
                    │
                    ▼
         optional residual: lexicon rank, sense, style among legal forms
```

### 5.1 Layers (order is load-bearing)

1. **Term algebra (symbolic)**  
   Predicates, arguments, modifiers, quantifiers, comparison, speech-act
   type (assert/ask/command), perspective markers as *references to frames*,
   not as free adjectives.

2. **World coupling (symbolic)**  
   Terms that claim facts are checked against corpus/frame/ToM state. A
   beautiful sentence that asserts silver eggs in a golden-only frame is
   REFUTED—same as now.

3. **Linearization grammar (symbolic)**  
   Deterministic or multi-candidate rules from term + language id → string.
   Bilingual A/B in langgen is the prototype. This *replaces* ad hoc
   f-strings as the grammar grows.

4. **Lexicon (extrinsic, partly empirical)**  
   Concept → forms. Project lexicon first; WordNet as optional empirical
   expansion with sense ambiguity retained (BACKLOG). Never structure
   authority.

5. **Residual (optional, tiny)**  
   Rank legal linearizations; resolve graded synonymy; propose which legal
   constructor to try next in search. Always with frequency/template
   baselines.

6. **Kernel session**  
   Same harness: WAITING for user-private slots; registered paths only;
   boot matrix; refuse unregistered inventiveness.

### 5.2 What grows when language “gets rich”

Richness is **depth and coverage of the term algebra + lexicon**, not
parameter count:

- more constructors (relative clauses, embedding under believe/say, …);
- more linearization variants (register, language);
- more world-coupled predicates;
- narrative constructors that are real tactics (introduce/obstruct/… already
  sketch this).

Depth-OOD and coverage measurements remain the honesty instruments. If the
term algebra claims relative clauses but the linearizer only emits three
sentence patterns, that is an incomplete dual—not a reason to jump to neural
prose.

### 5.3 Models and external corpora (repositioned)

| Fuel | Role for language-as-structure |
|---|---|
| Synthetic interlingua worlds (langgen) | Controlled proofs of residual size |
| Morphology / narrative / temporal nodes | Structural laws already in-graph |
| Formal Lean-class sources | Ingest spine for math/code; *not* NL teacher |
| WordNet | Empirical forms/relations for lexicon search |
| Wikipedia/COCA | At best, *challenge sets* for coverage of open text—not authorities |

A “grammar model” that **owns** structure from wiki text remains rejected.
A residual that **proposes** parses into the linguistic calculus, or ranks
linearizations, is welcome once baselines exist.

---

## 6. Antagonistic realism: where the challenge can fail

Register these as ways the thesis dies or must be narrowed—not as excuses to
avoid trying.

**R1 — Open English is not a closed algebra today.**  
Underspecification, implicature, metaphor, and discourse anaphora exceed the
current term algebra. The honest product is a **growing closed fragment**,
not universal English. Coverage numbers must be published the way v0.9 did
for Lean sources.

**R2 — Creation without world coupling is confabulation.**  
A pure syntactic constructor that never hits frame/world checks can emit
well-typed nonsense relative to the story. Verification of *content* is not
optional “later.”

**R3 — Linearization is not free of policy.**  
Word order and morphology encode information. Multiple legal linearizations
exist; choosing among them is residual or style registry—not proof of
understanding.

**R4 — The synthetic bilingual world is not the open web.**  
xlang/qa successes license the *architecture*, not a claim that full English
is solved. Same discipline as 221-node twins vs Goedel-scale coverage.

**R5 — Depth and discrete infinity still hurt residuals.**  
Unbounded modifiers are in the design; learned arms already show depth cliffs.
Symbolic trees scale; tiny nets may not. Prefer search over deeper constructors
to hoping recurrence invents English.

**R6 — Demo debt.**  
Golden-chicken still freezes prose in the oracle policy. Until briefs are
terms and sentences are linearizations of verified terms, the *practice*
under-sells the *design*. That debt is engineering priority, not evidence
against the challenge.

**R7 — Hybrid edge discipline.**  
A larger model may propose candidate terms or linearizations. If it ever owns
equality, twin identity, or frame consistency, the project has become a
wrapper (corpus-scale design’s failure mode).

---

## 7. Registered predictions (before implementation)

**P-LS1 — Dual of parse.**  
There exists a linearizer L and parser P on a non-trivial fragment such that
for terms t in a test suite, P(L(t)) =_canon t (canonical equality). Miss if
only hand-written strings pass round-trip.

**P-LS2 — Content refutation survives fluency.**  
A linearization of a term that contradicts frame premises is REFUTED by the
same frame executor path as today’s trait checks, independent of wording
variants in the lexicon. Miss if synonym packaging bypasses REFUTED.

**P-LS3 — Oracle story becomes a brief.**  
Golden-chicken (or successor) can be expressed as a structured brief + search
or scripted constructors *without* storing full English sentences in the
policy, except as linearizer outputs. Miss if policy still embeds whole beat
strings as the source of truth.

**P-LS4 — Residual only among licensed forms.**  
Any learned or statistical ranker over linearizations or lexicon picks is
evaluated against a frequency/template baseline on the same candidate set;
unlicensed tokens cannot appear. Miss if the ranker can emit OOV prose that
still displays as VERIFIED.

**P-LS5 — Coverage before scale claim.**  
A public coverage instrument for open English (or a declared fragment such as
“simple clauses + modifiers + CMP + WH”) reports expressible fraction before
any claim of prover-like text creation at scale. Miss if marketing outruns
measurement (v0.9’s lesson applied to NL).

**P-LS6 — Deixis is composition, not a lexicon.**  
I/you/here/now in generated or parsed text resolve through owner/frame/tense
machinery, not through WordNet person-deixis alone. Aligns with cognitive-
frames deictic cell.

---

## 8. Work sequencing (compatible with v0.10)

v0.10 rightly prioritizes **formal** grammar heads and external verifiers.
Language-as-structure must not hijack that lane. Ordered so each step is
falsifiable:

1. **Name the debt:** treat golden-chicken strings as linearizer debt (this
   doc + BACKLOG).  
2. **Story briefs as terms:** desire/obstacle/outcome/plant as structured
   fields only; English only via L(·).  
3. **Round-trip tests (P-LS1)** on the existing langgen interlingua + both
   language linearizers.  
4. **Expand linguistic constructors** only with coverage deltas (same rule as
   formal heads).  
5. **WordNet** remains lexicon plugin after project lexicon, never term
   algebra.  
6. **Optional residual** rankers last, with baselines.  
7. **Open-English coverage instrument** when the fragment is worth measuring.

Formal ingest and linguistic calculus share the kernel and the epistemic
ladder; they do not share one rushed grammar.

---

## 9. Relation to the “template / WordNet / rich text” thread

| Claim from earlier discussion | Disposition |
|---|---|
| WordNet must not own plot or truth | **Stands** |
| Fluency must not invent VERIFIED | **Stands** |
| Surface English *requires* string templates | **Retracted as design law**; demoted to provisional linearizer |
| Language is formulaic structure dual to equations | **Accepted as target**; already sketched in linguistic-twins |
| Analysis and creation under one prover-like loop | **Accepted**; creation = construct+verify+linearize |
| Rich text from corpora as primary path | **Rejected** if corpora mean wiki/WordNet as structure; **accepted** if “corpora” means growing term algebra + lexicon + world nodes |
| Statistical non-neural weights | **OK** for ranking licensed linearizations/lexicon picks |
| Neural structure-owner on open text | **Rejected** |

---

## 10. One-sentence north star

**Text is a pretty-printer and a parser for a typed world—not a place where
the world is invented—and the same kernel that proves a conjunction can, in
the limit, prove a story beat and linearize it, refuse a contradiction, and
ask when a slot is frame-private.**

That is the completion of the puzzle: not more templates, not WordNet-as-
author, not a second controller for “language,” but the linguistic dual of
everything this repository already measures when it is honest.
