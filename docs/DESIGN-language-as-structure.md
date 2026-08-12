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
the four conspicuously missing pillars for “algebra rich enough that an LLM
is residual, not engine” are **discourse state, reference, scope, pragmatics**.

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
           inference / constraint layer
              ↙          ↓          ↘
           world       frame      normative
         verifier    verifier    verifier
         (truth)   (scope/ToM)  (obligations,
                                 speech-act felicity)
                     │
                     ▼
             legal realizations
             (semantically admissible set)
                     │
                     ▼
        preference model over that set only
        register · rhythm · focus packaging ·
        discourse coherence · style
        (NOT denotational sense choice — see §5.3)
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

### 5.3 Legal vs preferred (stronger distinction)

Keep two cut-points, never one mushy score:

```text
1. LEGAL (hard, symbolic)
   - well-typed term under the algebra
   - morphosyntactically realizable under the language
   - discourse-coherent (reference resolves; presuppositions satisfied or
     explicitly accommodated)
   - world/frame/normative verifiers accept (or status is honestly UNKNOWN)
   - speech-act felicity (e.g. cannot assert what frame REFUTES)

2. PREFERRED (soft, only over the legal set)
   - register, rhythm, focus packaging, discourse coherence *among* legal
     variants, style
   - frequency / tiny ranker / non-neural weights OK
   - baselines mandatory
```

**Sense is not style.** Choosing the wrong lexical sense changes denotation
and therefore truth-conditions. Placement rules:

| Stage | Sense handling |
|---|---|
| Parse / construct | Prefer **underspecified** concept or explicit sense id; WordNet multi-sense stays multi-candidate |
| Before or inside verification | Sense must be fixed enough that the proposition is checkable, **or** verification runs on a *set* of candidates and returns UNKNOWN if they disagree on verdict |
| Preference model | May rank among senses **only when all remaining candidates are already legal and denotationally equivalent for the current check** (true synonymy under project lexicon), not to “pick bank vs riverbank” after the fact |

So the label is not:

```text
optional residual: lexicon rank, sense, style among legal forms
```

but:

```text
preference model over semantically admissible realizations
```

with **sense disambiguation living in the legal pipeline** (or remaining
packed until resolved), not in the preference tail.

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

5. **Inference / constraint layer (symbolic)**  
   Entailment, contradiction, temporal/causal consequence, twin/specialize
   edges—**not** the same button as “accept this transition into state,”
   though both use closed forms. Verification *commits*; inference *explains
   and projects*.

6. **World / frame / normative verifiers (symbolic)**  
   Content truth, local scope, obligations/speech-act felicity—as now, but
   fed by discourse-resolved terms.

7. **Lexicon (extrinsic, partly empirical)**  
   Concept/sense → forms. Project lexicon first; WordNet optional. Multi-sense
   remains multi-candidate until legally resolved (§5.3).

8. **Preference model (optional, tiny, soft)**  
   Only over the admissible realization set. Never invents denotation.

9. **Kernel session**  
   WAITING, registered paths, boot matrix, refuse unregistered inventiveness.

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

**R8 — Preference must not launder sense.**  
If a ranker can change denotation (wrong WordNet sense, wrong pronoun
antecedent) and still display as VERIFIED, the legal/preferred cut has
failed. Sense and reference live in the hard pipeline (§5.3).

**R9 — Pillars without tests are prose.**  
Discourse/reference/scope/pragmatics as design labels without negative
controls (ambiguous pronoun with two legal genders, failed presupposition,
scope ambiguity that flips REFUTED) are decoration. Each pillar needs at
least one REFUSED/REFUTED/UNKNOWN control before it is “shipped.”

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

**P-LS4 — Preference only over admissible realizations.**  
Any learned or statistical ranker is evaluated against a frequency baseline
on the **same legal candidate set**; unlicensed tokens cannot appear; no
candidate that changes denotation relative to the verified term is admitted
to the set. Miss if the ranker can emit OOV prose or alternate senses that
still display as VERIFIED.

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
world.

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
| Sentence-local dual is enough | **Rejected**; discourse/reference/scope/pragmatics are first-class pillars |
| Sense belongs in style residual | **Rejected**; sense is denotational → legal pipeline |
| Legal vs preferred | **Hard cut**; preference only on admissible set |
| Rich text from corpora as primary path | **Rejected** if corpora mean wiki/WordNet as structure; **accepted** if “corpora” means growing term algebra + discourse + lexicon + world nodes |
| Statistical non-neural weights | **OK** for preference over legal realizations |
| Neural structure-owner on open text | **Rejected** |

---

## 10. One-sentence north star

**Text is a morphosyntactic interface to a typed world under a discourse—not a
place where the world or the common ground is invented—and the same kernel
that proves a conjunction can, in the limit, plan a speech act, construct a
scoped term, resolve reference, refuse a contradiction or failed
presupposition, realize only legal forms, rank preferences among them, and
ask when a slot is frame-private.**

That is the completion of the puzzle: not more templates, not WordNet-as-
author, not a second controller for “language,” but the linguistic dual of
everything this repository already measures when it is honest—with discourse
as the multi-turn home of the same discipline.
