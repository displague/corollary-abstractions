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
