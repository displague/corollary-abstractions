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

## Experiments

- **Buffered subprocess logging.** train.py prints don't flush through
  run_all.py's redirect until process exit; add flush/`-u` for live tailing.

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
