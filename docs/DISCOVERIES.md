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
