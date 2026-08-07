# Backlog

Actionable friction found while working, kept here so it isn't lost in chat
or commit history. Each item names the evidence that motivated it.

## Parser / matcher

- **No call juxtaposition.** `D(F)(POINT)` fails to parse (`parse_atom`
  returns after the first call). Forced the calculus corpus to reshape the
  chain rule via a `COMPOSE(...)` head. Support `expr(...)` application or
  document the `COMPOSE` convention as canonical.
- **Big-op prefix namespace hazard.** Identifiers starting `sum_ prod_ lim_
  max_ min_` silently become prefix big-operators; and `lim_h` (big-op) vs
  `LIM(...)` (plain call) produce different skeleton heads that can never
  twin. Normalize: lower-case the big-op head AND fold `LIM(` calls into the
  same head, or lint templates for the ambiguity.
- **Specialization matching (v2): SHIPPED** as `scripts/specialize.py`
  (slot-to-subtree absorption + identity-element binding for parameter
  slots, looseness-ranked). The recorded misses now fire: equation of
  exchange >= ideal gas law (absorption over the dimensional constant),
  Cobb-Douglas <= power-law rate (absorption), circumference <= affine
  family (identity). Remaining out of scope: *series-truncation* relations
  (simple interest as the first-order truncation of continuous
  compounding) need rewrite-based reasoning, not matching.
- **Specialization noise control.** 236 edges among 67 nodes; looseness
  ranking surfaces tight ones, but variable slots can still bind numeric
  literals (trapezoid >= rectangle-perimeter binds HEIGHT->2). Consider
  category-compatibility constraints on bindings (V slots should not bind
  nums; P slots should not bind V-rooted subtrees).
- **Call args are ordered, so commutative call heads need an authoring
  convention.** `MEET`/`JOIN` are commutative in every model of a Boolean
  lattice, but the matcher flattens/sorts only the `op` heads in
  `COMMUTATIVE = {+, *}`; a `call` keeps its argument order. `MEET(X, TOP)`
  and `MEET(TOP, X)` are therefore different skeletons. The logic/set corpora
  twin only because `scripts/seed_logic.py` generates both from one shared
  format string and fixes the order (distinguished operand first, special
  element second). Fix: let a template declare commutative call heads, or
  lint for the same head appearing with permuted argument categories.
- **No binder syntax, so optimizations cannot be compared.** Channel capacity
  is `C = max over p(x) of I(X;Y)`: a maximization over a *family*, with a
  constraint set (the probability simplex). The grammar has identifiers,
  arithmetic, calls, prefix big-ops and relations — no binder — and the one
  spelling that looks natural, `max_p I(X;Y)`, collides with the `max_`
  big-operator namespace above and would silently drop the constraint set
  anyway. `infotheory.channel.channel_capacity` therefore uses an opaque
  `CAPMAX(objective, argument)` call: it parses, it records the dependency,
  and it makes the internal structure of the optimization invisible to the
  matcher. Every argmax/argmin/sup statement anyone adds later will hit this.
  Fix: a `MAX(body, binder, domain)` form (or a real binder node) that the
  canonicalizer treats as a scoped construct.
- **Specialization noise swamps big-op nodes.** All 11 specialization edges
  touching the new information-theory nodes are of the degenerate kind already
  noted under "Specialization noise control": a P slot binds the literal `1`
  and a V slot swallows an entire `sum⟨...⟩` subtree, producing e.g.
  `physics.mechanics.hookes_law >= infotheory.entropy.shannon_entropy` (Hooke's
  law "generalizes" Gibbs/Shannon entropy because `-(k*x)` matches
  `-(anything)`). Zero of the 11 is informative. Category-compatibility
  constraints on bindings, plus a rule that a variable slot may not absorb a
  big-operator subtree, would remove essentially all of them.
- **The genuine specialization we wanted does not fire.**
  `infotheory.entropy.uniform_entropy` (`H = k*LOG(N)`) really is
  `infotheory.entropy.shannon_entropy` (`H = -(k * sum_i p_i*LOG(p_i))`) with
  `p_i = 1/N`, and the same substitution takes Gibbs to Boltzmann's
  `S = kB ln W`. `specialize.py` cannot see it: collapsing a sum under a
  constant summand is a *rewrite* (algebraic simplification), not slot-to-
  subtree absorption. Same class as the recorded series-truncation miss. The
  edge is asserted by hand via `special_case_of`/`generalizes`, which means the
  most pedagogically important specialization in the corpus is the one the
  tooling cannot check.
- **Specialization matcher is arithmetic-only.** `COMMUTATIVE = {+, *}` and
  `IDENTITY = {+: 0, *: 1}` are hardcoded, so `specialize.py` finds *zero*
  edges touching the 18 logic/set_theory nodes even though those nodes
  literally state their own identity elements (`MEET(X, TOP) = X`,
  `JOIN(X, BOT) = X`) and their own annihilators. Generalizing IDENTITY to a
  per-head table sourced from `identity_laws`-style nodes would let e.g.
  De Morgan >= the degenerate one-operand case fire, and would give the
  Boolean corpora any specialization structure at all.
- **Discrete and continuous statements of one fact can never twin.** `sum_i X`
  parses to a call with head `sum`; `INTEGRAL(X)` parses to a call with head
  `INTEGRAL`. The two heads are unrelated strings, so the discrete and
  continuous forms of the *same* statement are structurally invisible to each
  other. The differential-geometry corpus produced the sharpest instance
  available: `difftop.vectorfields.poincare_hopf_index_theorem`
  (`EULERCHAR⟨?0:V⟩ = sum⟨?1:V⟩`) and `diffgeo.surfaces.gauss_bonnet_theorem`
  (`INTEGRAL⟨?0:V⟩ = *(?1:P, ?2:V)`) are the two halves of Chern's theorem —
  one theorem, proved from the other — and they share not one node. Same
  obstacle blocks probability normalization (`sum_i p_i = 1` vs
  `INTEGRAL(density) = 1`), every expectation, and every conservation law in
  the graph, all of which have both forms. This is bigger than the `lim_h` vs
  `LIM(...)` split already recorded above and has the same fix shape: a
  head-aliasing table (`sum` ~ `INTEGRAL` ~ `prod`, as accumulation operators)
  applied at a match level below `typed`, or an explicit `ACCUMULATE(...)`
  authoring convention that both forms adopt.
- **Three independent obstacles stacked on one pair.** Worth recording as a
  unit because fixing any one of them would not have made Gauss-Bonnet meet
  Poincaré-Hopf: (1) the `sum`/`INTEGRAL` head split above; (2) the Euler
  characteristic is a *slot* in Gauss-Bonnet and a *call head* in
  differential topology (see the Schema section); (3) Gauss-Bonnet carries an
  explicit `2*pi` normalization that the already-integer index sum does not, so
  even after (1) and (2) the arities differ. Any head-aliasing work should be
  tested against this pair, not against a single-obstacle example.
- **A numeric literal in a slot position blocks an otherwise real match.**
  `diffgeo.curves.circle_curvature` is `CURVATURE = 1 / RADIUS` ->
  `?0:V = *(1, inv(?1:V))`, and the rate/density family (average rate of
  change, average speed, mass density, molarity) is
  `?0:V = *(?1:V, inv(?2:V))`. Curvature really is a density — turning per
  unit length — whose numerator has been normalized to 1, but the literal is
  not a slot and the arities differ, so nothing fires at shape, typed or
  family level. Authoring around it (inventing a `UNITLENGTH` numerator slot)
  would be a lie. Fix candidate: a match level in which a numeric literal may
  bind a parameter-like slot, which is the dual of the existing sign-absorption
  level; it should be reported separately from `typed` since it is strictly
  looser.
- **Wanted match level: slot recurrence, not slot shape.**
  `difftop.degree.brouwer_fixed_point` (`?0:V = SELFMAP⟨?0:V⟩`),
  `logic.boolean_laws.double_negation` (`?0 = NEG⟨NEG⟨?0⟩⟩`),
  `settheory.boolean_laws.idempotence` (`?0 = MEET⟨?0, ?0⟩`) and
  `calculus.integration.ftc_differentiation_part` (`?0 = D⟨INTEGRAL⟨?0⟩⟩`) are
  all "an operation that returns its argument" — fixed points, idempotents,
  involutions, left inverses — and no two of them twin, because they differ in
  arity and nesting depth. The family is defined by a *property* of the
  skeleton (one slot occurring on both sides of the relation at different
  depths) rather than by the skeleton itself, so twin detection cannot express
  it. Wanted: a structural *query* facility ("templates where slot S occurs on
  both sides of the relation") alongside the equality-based twin grouping.
- **Notation adoption is manual, and the corpus should say so out loud.**
  `diffgeo.stokes.stokes_theorem`
  (`INTEGRAL(D(FORM)) = BOUNDARYINTEGRAL(FORM)`) is the statement a geometer
  writes and it twins with nothing.
  `diffgeo.stokes.stokes_zero_form_case`
  (`INTEGRAL(D(F)) = F(ENDPOINT) - F(STARTPOINT)`) states the k=0 case in
  `calculus.integration.ftc_evaluation_part`'s own vocabulary and twins with it
  exactly. Both are honest; the difference is that an author who already knew
  the answer spelled the second one to match. Same pattern as
  `infotheory.mutualinfo.entropy_inclusion_exclusion` adopting CARD/MEET/JOIN.
  Two twin groups in the graph now exist because of hand translation rather
  than discovery, which is a real limit on any claim that the matcher *finds*
  cross-discipline structure. Worth a provenance flag on twin groups
  (`authored_to_match` vs `emergent`) so the ledger can report the two counts
  separately; `diffgeo.surfaces.gaussian_curvature_principal_product` joining
  `geometry.area_formulas.rectangle_area_formula` was emergent and should not
  be pooled with the two adopted ones.
- **Specialization noise now reaches nonsense.** The new corpora add edges like
  `chemistry.spectroscopy.beer_lambert_law >= diffgeo.surfaces.gauss_bonnet_theorem`
  (looseness 1, via identity) and
  `geometry.area_formulas.triangle_area_formula >= diffgeo.surfaces.gaussian_curvature_principal_product`.
  Beer-Lambert does not generalize Gauss-Bonnet. Same root cause as the
  entries above under "Specialization noise control" — variable slots absorbing
  arbitrary subtrees and parameter slots binding literals — and another vote
  for category-compatibility constraints on bindings.

- **Call heads are literal at every match level, so a new discipline's
  vocabulary is structurally quarantined.** `data/morphology` (10 nodes) fires
  **zero** twin groups at shape, typed *and* family level, and **zero**
  specialization edges (247 edges among 106 nodes, none touching it) — yet four
  of its skeletons are character-for-character an existing skeleton apart from
  one head string:

  | morphology | existing / predicted |
  |---|---|
  | `?0:V = CONCAT⟨?0:V, ?1:P⟩` (zero morpheme) | `?0:V = MEET⟨?0:V, ?1:P⟩` (logic + set identity laws) |
  | `?0:V = CONCAT⟨CONCAT⟨?1:V, ?2:V⟩, ?3:V⟩` (iterated affixation) | `?0:V = MOD⟨MOD⟨?1:V, ?2:V⟩, ?3:V⟩` (intensifier nesting, `docs/DESIGN-linguistic-twins.md`, not yet authored) |
  | `CATEGORY⟨?0:V⟩ = CATEGORY⟨CONCAT⟨?1:V, ?0:V⟩⟩` | `FEAT⟨?0:V⟩ = FEAT⟨CONCAT⟨?1:V, ?0:V⟩⟩` (both morphology; one theorem, Williams's Righthand Head Rule) |
  | `?0:V = CONCAT⟨?1:V, ?2:V⟩` (affixation) | `?0:V = REALIZE⟨?1:V, ?2:V⟩`, `?0:V = CAPMAX⟨?1:V, ?2:V⟩` |

  `seed_infotheory.py` escaped this by *adopting* the CARD/MEET/JOIN heads.
  Morphology cannot: adopting `MEET` for concatenation would assert
  commutativity and idempotence, which are false of words (`re-do` is not
  `do-re`). So faithful authoring alone cannot produce a twin, and the corpus
  most likely to need a new vocabulary is the one least able to match. Fix: a
  declared head-alias table (`CONCAT ~ MEET ~ MOD` as "opaque binary
  composition"), or a fourth match level below `shape` that erases call-head
  identity the way `shape` erases slot identity — reported separately so it
  cannot be mistaken for a typed twin.
- **`archetype_id` is currently the only cross-head channel, and it is filed as
  a lint.** `archetype_label_drift` now reports `identity_element_law` spanning
  `logic.boolean_laws.identity_laws`,
  `settheory.boolean_laws.identity_laws` and
  `morphology.wordformation.zero_morpheme_identity` — the hand-assigned label
  says one law, the skeletons say three, and the label is right.
  `morphology.derivation.category_from_affix` and
  `morphology.agreement.feature_percolation` share
  `right_hand_head_projection` for the same reason. Both entries are
  deliberate. Fix: promote "same archetype_id, skeletons differing only by call
  heads" from a drift warning to a *proposed head alias* output, which turns
  the lint into the discovery channel the previous item asks for.
- **Per-head identity elements: third motivated head, and a new wrinkle.**
  `IDENTITY = {"+": 0, "*": 1}` in `specialize.py` is still arithmetic-only
  (recorded above for logic/set_theory). `morphology.wordformation.zero_morpheme_identity`
  states `CONCAT(STEM, EMPTY) = STEM`, so CONCAT is a third head declaring its
  own identity and getting nothing for it. The wrinkle morphology adds: the
  slot that should bind the identity is **variable-like**, not parameter-like —
  a zero morph *is* a morph, filling an affix slot with the empty string
  (`sheep` = sheep + ∅). The current rule ("variable-like slots may not
  vanish: a law does not lose its variables") is exactly what blocks the one
  edge worth having here, `iterated_affixation >= affixation` via
  `SUFFIX2 -> EMPTY`. Fix needs both parts: a per-head identity table sourced
  from identity-law nodes, and permission for a variable slot to bind an
  identity element *for a head whose identity the corpus has declared*.
- **Associativity and commutativity are one package in the canonicalizer.**
  `COMMUTATIVE = {+, *}` gets flattening (associativity) and sorting
  (commutativity) together, and call heads get neither.
  `morphology.wordformation.concat_associativity` is the corpus's first
  associative-but-not-commutative operation, so `CONCAT(CONCAT(A,B),C)` and
  `CONCAT(A,CONCAT(B,C))` are different skeletons even though the node asserts
  they are the same string. Fix: let a template declare a call head associative
  (flatten only) independently of commutative (flatten and sort). CONCAT must
  never be added to `COMMUTATIVE`.
- **`specialize.py` suppresses the plainest specializations of all.** Its
  filter is `if match(...) and (st.used_absorption or st.used_identity)`,
  justified in the docstring by "anything matchable without them is an exact
  twin and already in the skeleton report". That justification is false: two
  templates can match by *plain slot binding* and still have different
  skeletons, so they are in neither report. The topology corpora hit it twice
  in one seeding pass, both times on the relation the corpus most wanted:
  - `algtop.invariants.euler_characteristic_complex`
    (`EULERCHAR = VERTICES - EDGES + FACES`) covers
    `geotop.polyhedra.euler_polyhedron_formula` (`VERTICES - EDGES + FACES =
    2`) by binding `EULERCHAR -> 2`. Probed directly: `MATCHES = True,
    used_absorption = False, used_identity = False`.
  - `geotop.predicates.de9im_disjoint` (`MEET(REGA, REGB) = EMPTYSET`) covers
    `settheory.boolean_laws.complement_laws` (`MEET(SETA, NEG(SETA)) =
    FALSITY`) by binding `REGB -> NEG(SETA)`. Same probe result.
  A slot binding a numeric literal, and a slot binding a subtree with a call
  head, are the two commonest ways a general law becomes a special case, and
  both are dropped. Fix: report matches whose bindings are non-trivial (any
  slot bound to a `num`, or to a subtree of depth >= 1) even when neither
  absorption nor identity fired, and rank them by the same looseness score.
  Both edges are currently asserted by hand via `special_case_of` /
  `generalizes`.
- **Specialization noise, third confirmation.** All 16 specialization edges
  touching the 15 topology nodes are degenerate: `betti_number_rank`
  (`BETTI = CYCLERANK - BOUNDARYRANK`) "generalizes"
  `settheory.cardinality.inclusion_exclusion_two_sets` because a variable slot
  swallows a whole `CARD⟨...⟩` subtree. Zero are informative — the same
  outcome the information-theory corpus recorded. The proposed
  category-compatibility constraint on bindings is now supported by three
  independent corpora and should be considered load-bearing rather than nice
  to have.
- **No way to declare a call head commutative, so symmetry must be a node.**
  `geotop.predicates.adjacency_symmetry` exists only because
  `TOUCHES(A, B)` and `TOUCHES(B, A)` are different subtrees, and the corpus
  has no other way to say the head is symmetric. That is the same limitation
  already recorded above for `MEET`/`JOIN`, but seen from the other side:
  every Boolean-corpus node silently *assumes* commutativity of its head, and
  this is the first node in `data/` that *asserts* it. If a commutative-head
  declaration is added, this node is the test case for it.
- **The one relation nested inside a call argument matches nothing.**
  `geotop.measure.area_monotonicity` is
  `IMPLIES(LEQ(REGA, REGB), CARD(REGA) <= CARD(REGB))` — an order-preservation
  claim, with a lattice order in the premise and a numeric order in the
  conclusion. It parses cleanly (`parse_args` calls `parse_relation`), but it
  is the only such statement in the graph, so there is nothing to twin with.
  Not a bug; recorded so that a future monotone-functional node (entropy is
  monotone under coarsening, cardinality under inclusion, measure under
  containment) is written with *this* template rather than a fresh one.

- **Five heads now share the two-argument opaque-composition shape and none
  of them twin.** `?0 = HEAD⟨?1, ?2⟩` is carried by
  `morphology.wordformation.affixation` (CONCAT),
  `morphology.inflection.paradigm_realization` (REALIZE),
  `infotheory.channel.channel_capacity` (CAPMAX),
  `geotop.predicates.de9im_disjoint` (MEET) and
  `ml.recurrence.belief_state_update` (UPDATE). Five nodes, five heads, zero
  groups at shape, typed or family level. This is the cheapest available
  measurement of what head literalism costs, and it grows by one every time a
  corpus needs a vocabulary the graph does not already have.
- **Head literalism, now with a minimal reproducer inside one file.** The
  morphology entry above argues from four near-misses across corpus
  boundaries. `data/machine_learning` supplies the smallest possible case:
  `ml.recurrence.elman_rnn_hidden_state` is
  `?0:V = ACTIVATION⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` and
  `ml.recurrence.lstm_gate_activation` is
  `?0:V = SIGMOID⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` — the same string
  apart from one head token, authored by one hand in one file with no intent
  to hide the relationship — and they share no group at shape, typed *or*
  family level. `shape` is documented as the loosest level and it still
  cannot see a one-token difference. Any head-alias mechanism should be
  tested against this pair before the harder morphology ones.
- **A call head quarantines everything under it, including the corpus's
  largest family.** The argument of that `ACTIVATION(...)` is an affine map,
  and the affine family (`?0:V = +(?1:P, *(?2:P, ?3:V))`, five members across
  four disciplines) is the best-populated group in the graph. Nothing
  relates them. Worth separating from the head-alias item because *two*
  fixes are needed and neither suffices alone: erasing head identity would
  still leave the pre-activation as *multiple* linear regression (two
  weighted regressors) against a corpus that carries only the simple
  one-regressor form, so the arities differ as well.
- **No `min`, no `clip`, no piecewise form — the PPO ceiling.** Extends the
  "no binder syntax" entry above with a second family of missing constructs.
  `ml.policy.ppo_clipped_surrogate` needs a binary minimum and an interval
  clamp; the grammar has neither, and the natural spelling for the first
  collides with the `min_` big-operator namespace already recorded. Both are
  written as opaque calls (`MINOF`, `CLIPCALL`), which parse and record
  dependencies while hiding the entire mechanism — the clamp's flat gradient
  outside the trust region is what the method *is*. Consequence: the node is
  a singleton at every level and cannot be compared with TRPO's constrained
  form or any other trust-region method. Also: `MINOF` is commutative in
  every model and the matcher cannot know it, the same ordered-call-args
  problem `MEET`/`JOIN` and `TOUCHES` already have.
- **`*` means two different operations and the canonicalizer picks one.**
  `COMMUTATIVE = {+, *}` gets flattening *and* sorting, so `*` can only
  denote a commutative product. Machine learning needs it for matrix-vector
  application and for outer products, neither of which commutes.
  `ml.recurrence.linear_ssm_state_update` escapes only because S4D and Mamba
  use a *diagonal* state matrix, making the per-channel recurrence genuinely
  scalar; `ml.recurrence.mlstm_matrix_memory_update` cannot escape, since
  `v k^T` is irreducibly a rank-one matrix, and had to introduce an
  `OUTER(.,.)` head. That extra node is one of the two reasons the two
  state-update equations do not twin. Related to the CONCAT associativity
  entry above but distinct: there the head had no algebra declared, here the
  head has the *wrong* algebra declared. Fix shape: a non-commutative
  multiplication head, or a per-head associativity/commutativity table that
  `*` itself participates in.
- **`specialize.py` plain-binding suppression, fourth instance, and the one
  the node most wanted.** `infotheory.entropy.surprisal`
  (`?0:V = neg(LOG⟨?1:V⟩)`) covers `ml.preference.dpo_preference_loss`
  (`?0:V = neg(LOG⟨SIGMOID⟨*(?1:P, +(?2:V, neg(?3:V)))⟩⟩)`) by binding the
  argument slot to the `SIGMOID⟨...⟩` subtree — and the relation is exact,
  since SIGMOID's output is the Bradley-Terry probability that the annotator
  preferred the chosen completion, so the DPO loss *is* the surprisal of the
  observed preference. Neither absorption nor identity fires, so the filter
  drops it, exactly as recorded for the two topology cases. Three corpora
  have now lost their headline specialization to this one filter.
- **Specialization noise, fourth confirmation, and now it reaches training
  objectives.** Of 47 specialization edges touching the 14 machine-learning
  nodes, the informative ones are three:
  `probstat.regression.slr_stochastic_specification >= linear_ssm_state_update`
  (intercept to 0, noise slot absorbing the autoregressive term — an AR(1)
  process is the regression of a series on its own past),
  `probstat.transform.affine_location_scale >= lora_low_rank_update`, and
  `boltzmann_softmax_policy >= chemistry.kinetics.arrhenius_equation`. The
  rest are the known degenerate kind:
  `physics.mechanics.hookes_law >= ml.objective.token_cross_entropy_loss`
  (Hooke's law "generalizes" the training loss of a language model, because
  `-(k*x)` matches `-(anything)`),
  `chemistry.spectroscopy.beer_lambert_law >= grpo_group_relative_advantage`,
  `geometry.area_formulas.triangle_area_formula >= boltzmann_softmax_policy`,
  `physics.mechanics.newton_second_law >= policy_probability_ratio`. Same
  root cause, same proposed fix (category-compatibility constraints on
  bindings, plus a rule that a variable slot may not absorb a call-rooted
  subtree), now supported by four independent corpora.
- **Two deliberate `skeletons_with_split_archetypes` entries.**
  `?0 = *(?1, EXP⟨neg(*(?2, ?3))⟩)` now spans `exponential_decay` and
  `normalized_exponential_tilt`, and `?0 = +(?1, neg(*(?2, ?3)))` spans four
  labels including `state_minus_scaled_correction` (gradient descent) and
  `value_minus_weighted_penalty` (the RLHF objective). Both are intentional:
  the skeletons are shared and the statements are not the same statement.
  `ml.policy.policy_probability_ratio` went the other way and adopted the
  existing `ratio_rate` label rather than minting one. Recorded because the
  lint cannot currently distinguish "same structure, genuinely different
  claim" from "same claim, drifting label", and this corpus deliberately
  produced both.

- **A numeric literal in a multiplicative position, third and fourth
  confirmations — and the specialization matcher already fixes half of it.**
  docs/BACKLOG.md records `diffgeo.curves.circle_curvature` (`1 / RADIUS`)
  being kept out of the rate/density family by a literal `1`. The
  numerical-analysis and graph-theory corpora hit the same wall twice more,
  from the other side: `graphtheory.degree.average_degree_from_edge_count`
  (`?0:V = *(2, ?1:V, inv(?2:V))`) versus the seven-member rate family
  (`?0:V = *(?1:V, inv(?2:V))`), and
  `numanalysis.rootfinding.bisection_interval_halving`
  (`?0:V = *(?1:V, inv(2))`) versus the same family with the literal in the
  denominator. The new information is that `specialize.py` **does** recover the
  first one — `calculus.differentiation.average_rate_of_change >=
  average_degree_from_edge_count` via absorption, binding
  `QUANTITY -> *(2, EDGES)`, and likewise from molarity — so the relation is
  reachable, just not as a twin. That is now a repeatable pattern worth naming
  in its own right (a twin-level miss recovered one level down, first recorded
  for the ML state-space update), and it argues the wanted "numeric literal may
  bind a parameter-like slot" match level should be specified as a *twin*
  level, since the specialization level already covers the case where the
  literal can be absorbed into a variable slot but not the case where it must
  bind a parameter slot (bisection).
- **`decompose.py` sees three relations the twin matcher structurally cannot,
  and the pattern is predictable.** All three come from one cause: decompose
  compares *expression sides*, so it is blind to the relation symbol and to
  slot recurrence across the relation. Instances from this seeding pass:
  1. `numanalysis.floatingpoint.machine_epsilon_bound`
     (`ROUNDOFF <= UNITROUNDOFF*EXACT`) is a whole-statement singleton purely
     because of the `<=`; decompose reports its right side as `*(?0:P, ?1:V)`,
     the expression side of Ohm's law, Newton's second law and circle
     circumference, recurring in 35 statements. Every error bound anyone adds
     will be isolated at twin level and connected at decomposition level.
  2. `numanalysis.rootfinding.fixed_point_iteration`
     (`?0:V = SELFMAP⟨?1:V⟩`) does not twin
     `difftop.degree.brouwer_fixed_point` (`?0:V = SELFMAP⟨?0:V⟩`) because of
     slot recurrence — but decompose reports its expression side as *being*
     Brouwer's expression side, since on one side of the relation the
     recurrence is invisible. The two tools disagree, both correctly, about
     the same pair.
  3. `numanalysis.rootfinding.newton_iteration` misses the whole
     iteration/update family over one `inv` node, and decompose finds its
     correction term `*(?0:V, inv(?1:V))` is the rate/density family's
     expression side (11 statements) — i.e. a Newton correction is a rate.
  Proposal: rather than three more match levels, have `match_signatures.py`
  cross-reference `decompose.py`'s side-forms and report "singleton at every
  level, but its expression side is a known form shared with N statements" as
  a fourth report section. It costs nothing new and it would have caught all
  three of these automatically.
- **Head literalism: the two-argument opaque-composition count reaches seven,
  two of them added in one pass.** `?0 = HEAD⟨?1, ?2⟩` is now carried by
  `morphology.wordformation.affixation` (CONCAT),
  `morphology.inflection.paradigm_realization` (REALIZE),
  `infotheory.channel.channel_capacity` (CAPMAX),
  `geotop.predicates.de9im_disjoint` (MEET),
  `ml.recurrence.belief_state_update` (UPDATE),
  `graphtheory.walks.adjacency_power_walk_count` (MATRIXPOWER) and
  `geomodel.surfaces.surface_normal_cross_product` (CROSS). Seven nodes, seven
  heads, zero groups at any level. The two new ones sharpen the diagnosis: both
  exist *because `*` is hardcoded commutative*. MATRIXPOWER cannot use `^`
  because matrix multiplication does not commute; CROSS cannot use `*` because
  it ANTI-commutes. This is the same root cause as
  `ml.recurrence.mlstm_matrix_memory_update`'s OUTER, and it means the
  per-head associativity/commutativity table already requested for CONCAT is
  now blocking four nodes in three corpora, not one. CROSS additionally needs
  a value the table cannot currently express (antisymmetric), and the cost is
  concrete: the cross product's magnitude is a rectangle area, and
  `?0:V = *(?1:V, ?2:V)` is a three-discipline group in the same graph.
- **Two inequalities, opposite in kind, indistinguishable to the matcher.**
  `numanalysis.floatingpoint.machine_epsilon_bound` (never attained, a
  guarantee) and `graphtheory.planarity.planar_edge_bound` (attained by every
  maximal planar graph, an extremal identity in disguise) are both singletons
  for the same mechanical reason — the relation symbol is part of the skeleton
  — and the graph has no way to say that the second is an equality on a
  subfamily while the first is not. Related to but distinct from the
  `geotop.measure.area_monotonicity` entry above: that one is isolated for
  being the only *nested* relation, these two for being non-`=` at top level.
  Wanted: a flag or slot-schema note distinguishing tight/attained bounds from
  loose ones, so an extremal statement can eventually be related to the
  equality case it saturates.

- **`specialize.py` cannot use a non-equation as a general pattern, so every
  inference rule in the graph is excluded from the general side.**
  `find_specializations` opens with `if gtree[0] != "rel": continue`, which
  silently drops any node whose canonical template is a bare call rather than a
  relation. That is **16 of 195 nodes**: `logic.inference.modus_ponens`,
  `logic.inference.ex_falso_quodlibet`, `logic.inference.reductio_ad_absurdum`,
  `settheory.order.subset_transitivity`,
  `settheory.order.empty_set_minimality`,
  `geotop.predicates.containment_transitivity`,
  `geotop.predicates.adjacency_symmetry`, `geotop.measure.area_monotonicity`,
  `algtop.homotopy.homotopy_invariance` and the seven rule-shaped nodes in
  `data/temporal_logic` / `data/narrative`. Concrete cost, and the case that
  found it: `temporal.response.response_pattern`
  (`ALWAYS(IMPLIES(TRIGGER, EVENTUALLY(RESPONSE)))`) covers
  `narrative.constraint.chekhov_gun`
  (`ALWAYS(IMPLIES(PLANTED(ELEMENT), EVENTUALLY(DISCHARGED(ELEMENT))))`) by
  binding `TRIGGER -> PLANTED(ELEMENT)`, `RESPONSE -> DISCHARGED(ELEMENT)`.
  Probed directly: `MATCHES = True, used_absorption = False,
  used_identity = False`. Two filters stacked — this one first, then the
  plain-binding suppression already recorded five times — so Chekhov's gun
  being an instance of an LTL liveness pattern has to be asserted by hand.
  Fix: drop the `rel` guard and gate on `op_count` alone (the guard's stated
  purpose, avoiding near-trivial patterns, is already served by
  `op_count(gtree) < 2`).
- **`decompose.py` rates a recursive definition as maximally ungrounded, which
  breaks the epistemic ladder's one graded rung.**
  `temporal.recurrence.until_unfolding`
  (`UNTIL(PROPA, PROPB) = JOIN(PROPB, MEET(PROPA, NEXT(UNTIL(PROPA, PROPB))))`)
  scores **groundedness 0.000** — the lowest of the seventeen nodes in that
  seeding pass, on an axiom of a fifty-year-old logic. Cause: all five of its
  non-trivial constituents contain `UNTIL`, the head being defined
  (`JOIN⟨?0, MEET⟨?1, NEXT⟨UNTIL⟨?1, ?0⟩⟩⟩⟩`, `MEET⟨?1, NEXT⟨UNTIL⟨?1, ?0⟩⟩⟩`,
  `NEXT⟨UNTIL⟨?1, ?0⟩⟩`, `UNTIL⟨?1, ?0⟩` twice), and the form inventory is
  built from *other* statements, where the head does not occur. Its Boolean
  neighbour `temporal.modality.next_distributes_over_meet` scores 0.600 with
  its `MEET⟨?0:V, ?1:V⟩` constituent recognized in 10 statements, so the
  contrast is internal to one corpus. Per `docs/DESIGN-epistemic-ladder.md`
  groundedness grades the UNGROUNDED rung, so a correct axiom currently lands
  where near-gibberish lands, and every recursive definition anyone adds
  (factorial, Fibonacci, a grammar production, the mu-calculus fragment) will
  land there too. Fix: while decomposing a statement, treat that statement's
  own root head as a known form.
- **Groundedness measures vocabulary overlap, so a new discipline's first
  corpus is guaranteed to grade as disorder.** Across the 17 nodes of
  `data/temporal_logic` + `data/narrative` the score is almost perfectly
  predicted by how many pre-existing heads the template reuses: 1.000 for the
  two nodes written entirely in adopted heads
  (`temporal.order.precedence_transitivity`,
  `narrative.frame.frame_consistency`), 0.400–0.750 for mixed templates, and
  0.000 for all five written only in heads the corpus introduced
  (`until_unfolding`, `chekhov_gun`, and the three
  `narrative.structure.*` unit definitions). This is the numeric form of the
  already-recorded "a new discipline's vocabulary is structurally quarantined".
  Sharper instance: `narrative.constraint.chekhov_gun` is written *entirely* in
  the temporal corpus's ALWAYS/IMPLIES/EVENTUALLY vocabulary and still scores
  0.000, because its constituents are `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` and
  `PLANTED⟨?0⟩` rather than `EVENTUALLY⟨?0⟩` — one extra unary head under the
  modality changes the skeleton. The general pattern it instantiates scores
  0.500 on the same formula shape, so an instance grades *lower* than its
  pattern, which inverts what the score is for.
- **`specialize.py` produces zero edges and zero noise on call-only corpora —
  fifth confirmation, from the other side.** 468 specialization edges over the
  merged graph, none touching either of the 17 new nodes in either direction.
  Same root cause as the recorded "specialize.py is arithmetic-only"
  (`COMMUTATIVE = {+, *}`, `IDENTITY = {+: 0, *: 1}`) that already gave
  `data/logic` and `data/set_theory` zero edges. The new information is that
  these corpora also contribute **zero degenerate noise**, because the noise
  mechanism (a variable slot absorbing arguments of a commutative arithmetic
  op) has nothing to bite on in a template made only of call heads. Any
  evaluation of the proposed category-compatibility constraint should note that
  the corpora it would clean up are exactly the corpora that get edges at all.
- **Monotone endo-functions need a second monotonicity template, and the
  backlog's own request could not be honoured.** The
  `geotop.measure.area_monotonicity` entry above asks that a future
  monotone-functional node be written with *that* template
  (`IMPLIES(LEQ(REGA, REGB), CARD(REGA) <= CARD(REGB))`).
  `temporal.monotonicity.eventually_monotonicity` is the first such node and
  cannot: `CARD` is a valuation into the numbers, while `EVENTUALLY` maps the
  lattice of temporal properties into itself, so its conclusion must be a
  second `LEQ` and the honest template is
  `IMPLIES(LEQ(PROPA, PROPB), LEQ(EVENTUALLY(PROPA), EVENTUALLY(PROPB)))`.
  The two skeletons share their premise and differ in the kind of their
  conclusion, so no group forms. The request presumed every monotone functional
  is a valuation; monotone *endo*-functions are a second kind. The
  generalization the graph wants — `IMPLIES(LEQ(x, y), LEQ(F(x), F(y)))` with
  the numeric case as its specialization along a valuation — is also out of
  reach for `specialize.py`, since `<=` and `LEQ` are different relation kinds.
  Wanted: either a `LEQ` spelling of the numeric case, or a match level that
  treats a declared order relation and `<=` as one head.
- **The two-premise detachment shell is now the graph's most-populated
  non-family.** `IMPLIES⟨MEET⟨_, _⟩, _⟩` carries five nodes —
  `logic.inference.modus_ponens`, `settheory.order.subset_transitivity`,
  `geotop.predicates.containment_transitivity`,
  `temporal.order.precedence_transitivity` and
  `narrative.causality.precedence_causation_bridge` — and forms exactly one
  group (the three transitivity nodes). The three that group share a *slot
  pattern* ((0,1),(1,2) ⊢ (0,2)); the causation bridge conjoins two relations
  over the SAME pair and concludes a third over that pair. The distinction is
  real and the graph has no vocabulary for it: "same shell, different slot
  pattern" is currently indistinguishable from "unrelated" in every report.
  Companion to the recorded "slot recurrence, not slot shape" wanted level —
  that one asks for a query over slot recurrence within a statement, this one
  asks for the shell itself to be reportable as a weaker grouping.
- **Idempotence and involution cannot be related, and the reason is a fixed
  point rather than a head.** `temporal.modality.always_idempotence`
  (`ALWAYS⟨?0:V⟩ = ALWAYS⟨ALWAYS⟨?0:V⟩⟩`) is the fifth member of the recorded
  "operation that returns its argument" family and the first idempotent
  *modality*. Worth separating from the head-literalism entries because the
  blocker against `logic.boolean_laws.double_negation`
  (`?0:V = NEG⟨NEG⟨?0:V⟩⟩`) is not the head: NEG applied twice equals the bare
  slot, ALWAYS applied twice equals `ALWAYS⟨?0⟩`, so the two sides differ in
  depth. An idempotent has a fixed point an involution does not, and that is a
  property of the skeleton rather than a shape of it — the exact case the
  wanted structural-query facility has to cover.

## Schema

- **`symbolToken.syntactic_category` lacks `functional`/`operator`** (unlike
  `signatureSlot`), so operator symbols (`D`, `f`, `g`) must go in
  `functionals` while `symbols` still demands `minItems: 1` — FTC part 1
  needed a scalar symbol it didn't naturally have. Either add the enum
  members or relax `minItems`.
- **`statement_id` pattern forbids underscores in the first segment.**
  `^[a-z0-9]+(\.[a-z0-9_]+)+$` allows `_` in every segment except the
  discipline prefix, so `set_theory.boolean_laws.de_morgan_laws` fails
  validation and the corpus had to use `settheory.` while the directory and
  the `discipline` field stay `set_theory`. The prefix and the directory name
  now disagree, which is a trap for anything that derives one from the other.
  Fix: allow `[a-z0-9_]+` in the first segment too (there is no reason for the
  asymmetry), or document the prefix-vs-directory mapping in the schema.
- **Slot ids may not start with a big-op prefix either.** The hazard recorded
  above for templates extends to `slot_schema`: a slot literally named
  `SUM_TERM` or `MAX_RATE` would be eaten by the prefix big-operator rule
  before it was ever looked up, so a whole class of natural slot names is
  quietly unusable. The information-theory corpus works around it by naming
  indexed slots `WEIGHT_i`, `PROBABILITY_i`, `CODELENGTH_i` (suffix, not
  prefix). Worth a lint rather than folklore.
- **Cross-corpus entailment is blocked by reciprocity.** `entails` /
  `special_case_of` / `generalizes` require the reciprocal edge in the other
  corpus's file, so genuine cross-discipline entailments (physics average
  speed IS a special case of calculus average rate of change) go unrecorded;
  only `composed_with` (unchecked) is usable one-sided. Options: a repair
  tool that writes the reciprocal edge into the target corpus, or relax
  reciprocity to a warning for cross-corpus edges.
- **Even one-sided `composed_with` cannot forward-reference a corpus authored
  on a parallel branch.** `validate_nodes.py` requires every link target to
  resolve in the merged graph, and the merged graph is whatever `data/*/` holds
  on the current branch. `diffgeo.surfaces.gauss_bonnet_theorem` should point
  at `algtop.invariants.euler_characteristic_surface`, which a parallel branch
  is authoring; writing the edge now makes validation fail here and pass only
  after a merge, so the reference sits in prose and the edge is a documented
  one-line addition in `scripts/seed_diffgeo.py`. Two agents seeding
  interlocking corpora in parallel therefore cannot link to each other at all.
  Fix: a `pending`/`external` link list the validator warns on instead of
  failing, or a manifest of reserved ids that branches may reference before the
  corpus lands.
- **Same invariant, slot in one corpus and call head in another.** The Euler
  characteristic is a bare slot in `diffgeo.surfaces.gauss_bonnet_theorem`
  (where it is the number on the right-hand side) and a call `EULERCHAR(.)`
  throughout `data/differential_topology` (where it is an invariant applied to
  a space). Both readings are natural, and the matcher cannot relate a slot to
  a call head, so the two corpora cannot see that they discuss one integer.
  The same trap is open for every named quantity that is sometimes a value and
  sometimes a functional (entropy, degree, cardinality, expectation). Wanted: a
  lint that flags an identifier used as a slot id in one node and a call head
  in another, plus a documented convention for which reading wins.
- **A quarter of the corpus loses its logical form.** The grammar has no
  quantifier and no usable implication, so conditional and existential
  statements reduce to their conclusions: of the sixteen nodes in
  `data/differential_geometry` and `data/differential_topology`, four carry
  their real content in `regularity_conditions` instead of the template —
  `difftop.invariants.euler_characteristic_diffeomorphism_invariance` (loses
  "whenever M and N are diffeomorphic"),
  `difftop.vectorfields.hairy_ball_theorem` (loses "if a nowhere-vanishing
  field exists"), `difftop.degree.brouwer_fixed_point` (loses "there exists x"),
  and `difftop.morse.weak_morse_inequality` (loses "for every Morse function
  and every k"). Consequence for the ledger: twin density is not comparable
  across `statement_class`, because definitions keep their whole content in the
  template and theorems routinely do not. Same family as the missing binder
  recorded under Parser / matcher.

- **Cross-corpus reciprocity, now measured in edits per edge.** The entry
  above proposes a repair tool; `data/machine_learning` priced it.
  `ml.objective.token_cross_entropy_loss` and
  `infotheory.divergence.cross_entropy` are the same functional, so the
  reciprocal `equivalent_to` was worth writing — which meant editing
  `scripts/seed_infotheory.py`, regenerating `data/information_theory`, and
  carrying an unrelated corpus's diff on this branch. That is affordable
  once. It is not affordable for
  `ml.preference.grpo_group_relative_advantage`, whose relation to
  `probstat.transform.z_standardization` is the strongest in the corpus (an
  exact typed twin, and GRPO's advantage really is that transform applied to
  rewards) but which had to degrade to a one-sided `composed_with`: the
  reciprocal `generalizes` would have to go into `data/statistics/nodes.json`,
  and that corpus has **no seed script** — it is hand-maintained, so the edit
  could not be made the way every other corpus is edited. So the reciprocity
  requirement's real cost is not "write two edges", it is "be able to
  regenerate the other corpus", and one corpus in the repo fails that test.
  Either the repair tool lands, or reciprocity relaxes to a warning for
  cross-corpus edges, or `data/statistics` gets a `scripts/seed_statistics.py`
  like everything else.
- **Side conditions that carry the whole empirical claim have nowhere to go.**
  The differential-topology entry above records lost quantifiers. Machine
  learning loses a different class and loses it in the most-cited node:
  `ml.adaptation.lora_low_rank_update` is
  `?0:V = +(?1:P, *(?2:P, ?3:V, ?4:V))`, which says the update factors
  through a product — it does not and cannot say that the inner dimension is
  small, which is the entire hypothesis of the paper. Same shape of loss:
  parameter tying across time steps in the recurrence nodes (the reason RNNs
  generalize across sequence length), and the zero-initialization of one LoRA
  factor (the reason adaptation starts at the pretrained model). All three
  sit in `invariants` and `regularity_conditions` as prose. Consequence for
  the ledger, beyond the one already noted for `statement_class`: three
  papers (LoRA, PiSSA, LoftQ) share one skeleton and differ only in how the
  same slots are initialized, so skeleton count understates the corpus's
  content in a way that is invisible from the reports.

- **`specialize.py` plain-binding suppression, fifth instance, same target node
  as the first.** `geotop.polyhedra.euler_polyhedron_formula`
  (`VERTICES - EDGES + FACES = 2`) covers
  `graphtheory.trees.tree_edge_count` (`EDGES = VERTICES - 1`) by binding
  `FACES -> 1`: a plane tree has exactly one face. Plain slot-to-literal
  binding, no absorption, no identity, so the filter drops it — exactly as
  recorded for `algtop.invariants.euler_characteristic_complex` covering the
  *same* polyhedron-formula node, for DE-9IM disjointness covering the
  complement law, and for surprisal covering the DPO loss. That node is now
  the target of two suppressed specializations from two different corpora,
  which makes it the natural regression test for the proposed fix (report
  matches whose bindings are non-trivial even when neither absorption nor
  identity fired).
- **The corpus gap is now measurable: two twin groups are blocked by one
  missing node.** `data/statistics` carries the law of total probability,
  Bayes's rule, z-standardization and the CLT, but **not** the normalization
  axiom `sum_i p_i = 1` and **not** a two-component mixture
  `p = (1-w)*p_0 + w*p_1`. Consequently
  `geomodel.barycentric.barycentric_partition_of_unity` (`1 = sum⟨?0:P⟩`) is a
  singleton whose exact structural twin is a one-line addition away, and
  prediction 2 of `scripts/seed_numgraph.py` ("linear interpolation versus
  probability mixtures") could not be evaluated at all — there was nothing to
  compare against, which is a different outcome from a miss and was reported
  as such. Both would be fixed by two nodes in `data/statistics`. That corpus
  still has no seed script (recorded above under cross-corpus reciprocity),
  so the cheapest fix to the graph's connectivity is currently the one that
  requires hand-editing the one file nobody can regenerate.
- **Same statement, two spellings, and only one of them matches — now
  quantified.** `numanalysis.integration.trapezoidal_rule` twins
  `geometry.area_formulas.trapezoid_area_formula` at typed level *because it
  was written with the one-half as a `constant` slot*; the textbook spelling
  `h*(f(a)+f(b))/2` produces `*(?1:P, +(?2:V, ?3:V), inv(2))` and matches
  nothing. Same for `numanalysis.interpolation.linear_interpolation`, where
  the expanded form `START + PARAM*(FINISH - START)` would have joined the
  five-member affine family and the written form
  `(1-PARAM)*START + PARAM*FINISH` joins nothing (the parameter slot recurs).
  In both cases the two spellings are algebraically identical, one fires and
  one does not, and the choice is the author's. This is the
  `authored_to_match` versus `emergent` distinction already requested for twin
  groups, seen from the authoring side: the corpus needs a way to record
  "these two templates are the same statement" so that a *normalizer* could
  eventually choose the canonical spelling, rather than relying on the author
  having already known which one fires. Without it, twin counts measure
  authoring luck as much as mathematical structure.
- **A `weighted_accumulation` archetype label was minted rather than adopted,
  deliberately, and the lint cannot tell.** `?0 = sum⟨*(?1, ?2)⟩` now spans
  three labels — `alternating_rank_sum` (topology),
  `conditional_marginalization` (statistics) and `weighted_accumulation`
  (both new geometric-modeling nodes). Neither existing label could honestly
  cover a Bezier point or a barycentric combination, and the new label could
  not honestly replace them either, so the drift entry is correct and
  unfixable by renaming. Same situation the ML corpus recorded for
  `state_minus_scaled_correction`. The pattern is stable enough now to
  propose the fix concretely: let `archetype_id` be a list, or add an
  `archetype_family` field, so a node can say "my label is X, my structural
  family is Y" and the lint can check the second while leaving the first free.

- **No scope construct, so `docs/DESIGN-frames-and-retrieval.md`'s central
  mechanism cannot be stated in a template.** `narrative.frame.frame_consistency`
  (`MEET(FRAMEPREMISE, NEG(FRAMEPREMISE)) = INCONSISTENCY`) is an exact typed
  twin of `logic.boolean_laws.complement_laws` and
  `settheory.boolean_laws.complement_laws` — which is the intended result, and
  also the whole problem. Everything that makes it a *frame* law rather than a
  logic law is the scope: "within frame F", frame premises occupying the
  frame's local VERIFIED tier, and their reversion to
  CONJECTURED-under-premise on scope exit. The grammar has no binder and no
  scope construct, so all of that sits in `regularity_conditions` as prose and
  the graph cannot check the boundary that the design document says is
  "structural, not stylistic". Same family as the lost quantifiers recorded for
  differential topology and the missing binder recorded for channel capacity,
  but with a new consequence: this is the first time the gap costs a *design
  document's* mechanism rather than a single statement's content. Fix shapes,
  in increasing order of work: a `scope` field on a node naming the frame its
  claims are relative to; a `FRAME(premises, claim)` head; or a real scoped
  construct in the grammar shared with the wanted `MAX(body, binder, domain)`.
- **No past modality, so half of a two-directional law cannot be written.**
  `narrative.constraint.chekhov_gun` states one direction — every planted
  element is eventually discharged. Its converse, `ALWAYS(IMPLIES(
  DISCHARGED(e), ONCE(PLANTED(e))))`, is the half that forbids deus ex machina
  and is the half most authors care about; it needs a past-tense modality
  (`ONCE`/`H` in the Manna–Pnueli past fragment) that `data/temporal_logic`
  does not carry. Adding one is cheap as a head, but note it will *not* twin
  its future dual for the usual reason, so the corpus would gain a statement
  and no structure. Recorded so that whoever adds past LTL knows the expected
  yield up front.
- **A strict order and its reflexive closure cannot share a head, and the
  corpus now pays for it inside one file.**
  `temporal.order.precedence_transitivity` uses the abstract `LEQ` head and is
  a three-discipline typed twin;
  `temporal.order.strict_precedence_asymmetry` uses `BEFORE` and is a singleton
  at every level. The second could not honestly use `LEQ`, because asymmetry is
  false of a reflexive relation, so this is not an authoring slip — it is the
  cheapest available demonstration that twin counts measure which head a
  statement is *allowed* to use. Companion to the recorded
  `authored_to_match` vs `emergent` request: a provenance flag on twin groups
  should be readable alongside this pair, since one member of an adjacent pair
  from one author lands in a cross-discipline group and the other lands nowhere.
  Wanted: a way to declare `BEFORE` as the strict part of `LEQ` (an order and
  its strict/reflexive variants as one declared family), which would also cover
  `⊆`/`⊂` and `<=`/`<`.


## Real-data lanes

- **Wikisem (LREC2020 logical forms) ingestion.** Corpus located and
  downloaded (43MB, 839 article-level lambda forms + 5,953 CG trees; see
  experiments/data_real/lrec2020-logical-forms/INGEST_NOTES.md for source
  URLs, format, and a prototyped mapping onto the matcher AST). Before the
  lane runs: (1) add `^` to COMMUTATIVE for conjunction chains, (2) fix the
  atom-classification wart (bound vars -> slots, `CATEGORY:lemma` atoms ->
  named leaves) so skeletons stop half-lexicalizing, (3) subterm mining is
  the granularity — sentence segmentation via variable indices fails on
  806/839 articles. LICENSE: data files carry no license statement (paper
  CC-BY covers the paper only); local research use only, no redistribution
  of derivatives without written confirmation from the maintainer.
