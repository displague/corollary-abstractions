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
