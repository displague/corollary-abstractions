#!/usr/bin/env python3
"""Seed data/temporal_logic/nodes.json and data/narrative/nodes.json together.

Two corpora, one script, for the reason scripts/seed_logic.py gives for logic
and set theory: they are not analogous subjects that happen to rhyme, they are
one subject seen twice. Linear temporal logic is an algebra of statements about
the future; a story grammar is an algebra of statements about the future that
happens to be told rather than verified. `docs/DESIGN-frames-and-retrieval.md`
puts both on the build order for the same reason -- "story generation and
abstract reasoning are one problem here; the chicken is the friendlier
costume" -- so this file authors them as one authoring act, with reciprocal
edges where the two corpora genuinely meet.

Authoring stance: reuse the lattice heads
-----------------------------------------

`scripts/seed_logic.py` established MEET / JOIN / NEG / LEQ / IMPLIES / TOP /
BOT as the *abstract* lattice vocabulary, so that the propositional and
powerset readings of one theorem land on one skeleton. Temporal logic is a
Boolean algebra with four extra operators bolted on, so every Boolean part of
every statement below is written with those same heads. That is not decoration:
it is what lets `temporal.order.precedence_transitivity` land character for
character on `settheory.order.subset_transitivity`, and what lets
`narrative.frame.frame_consistency` land on `logic.boolean_laws.complement_laws`.
The four modal heads (ALWAYS, EVENTUALLY, NEXT, UNTIL) and the narrative heads
(SEQUENCE, INTRODUCE, OBSTRUCT, RESOLVE, BEFORE, ENABLES, CAUSES, PLANTED,
DISCHARGED) are new, and every place where a new head costs a match is recorded
rather than engineered away.

Predictions registered BEFORE running scripts/match_signatures.py
-----------------------------------------------------------------

P1. **Temporal duality is a modal De Morgan.**
    `ALWAYS(PROP) = NEG(EVENTUALLY(NEG(PROP)))` versus
    `logic.boolean_laws.de_morgan_laws`. Honest expectation: **no typed twin**
    -- different heads, different arity (De Morgan is binary in its operands,
    the modal duality is unary). Registered so the *archetype* channel can be
    tested instead: the node adopts the existing `de_morgan_duality`
    archetype_id, which should produce an `archetype_label_drift` entry
    spanning three skeletons. Under docs/BACKLOG.md's proposal that drift be
    promoted from a lint to a "proposed head alias" output, that entry is the
    finding.
    VERDICT: see "Adjudication" below.

P2. **Until-unfolding is a recurrence, kin to the state-update family.**
    `UNTIL(PROPA, PROPB) = JOIN(PROPB, MEET(PROPA, NEXT(UNTIL(PROPA, PROPB))))`
    versus `ml.recurrence.belief_state_update` and
    `ml.recurrence.linear_ssm_state_update`. Expectation: no whole-statement
    twin (the ML nodes are arithmetic, this is lattice-algebraic). The real
    question registered here is whether `scripts/decompose.py` reads the
    constituents into known families even when no whole twin fires.
    VERDICT: see "Adjudication" below.

P3. **NEXT distributes over MEET is a homomorphism statement.**
    `NEXT(MEET(PROPA, PROPB)) = MEET(NEXT(PROPA), NEXT(PROPB))` versus
    `morphology.semantics.compositionality`
    (`MEANING(CONCAT(A,B)) = COMPOSE(MEANING(A), MEANING(B))`) and
    `morphology.quantity.morpheme_count_additivity`
    (`LENGTH(CONCAT(A,B)) = LENGTH(A) + LENGTH(B)`). Expectation: no twin, and
    the reason is worth stating precisely rather than as "different heads" --
    see the adjudication.
    VERDICT: see "Adjudication" below.

P4 (flagship). **Precedence transitivity MUST typed-twin the LEQ transitivity
    family.** `temporal.order.precedence_transitivity` is authored with
    scripts/seed_logic.py's `TPL_SUBSET_TRANSITIVITY` shape verbatim, only the
    slot names changed, exactly as `geotop.predicates.containment_transitivity`
    was. If time's order does not join set inclusion and region containment in
    one typed group, the reuse convention does not work.
    VERDICT: see "Adjudication" below.

P5 (flagship). **Fiction obeys logic.**
    `narrative.frame.frame_consistency`
    (`MEET(FRAMEPREMISE, NEG(FRAMEPREMISE)) = INCONSISTENCY`) should typed-twin
    `logic.boolean_laws.complement_laws` and
    `settheory.boolean_laws.complement_laws`. A firing means the graph cannot
    tell a constraint on a made-up world from a postulate of Boolean algebra --
    which is the intended reading of docs/DESIGN-frames-and-retrieval.md's
    frame mechanism, made mechanical.
    VERDICT: see "Adjudication" below.

P6. **ALWAYS-idempotence will not twin logic idempotence.**
    `ALWAYS(ALWAYS(PROP)) = ALWAYS(PROP)` versus
    `logic.boolean_laws.idempotence` (`MEET(PROP, PROP) = PROP`) and
    `logic.boolean_laws.double_negation` (`NEG(NEG(PROP)) = PROP`). Expectation:
    no twin at any level; the node joins docs/BACKLOG.md's recorded
    "slot recurrence, not slot shape" family instead, and adopts the
    `idempotent_operation` archetype so the archetype channel carries it.
    VERDICT: see "Adjudication" below.

P7. **Chekhov's gun is an LTL response pattern, and `specialize.py` should say
    so.** `narrative.constraint.chekhov_gun` is
    `temporal.response.response_pattern` with TRIGGER -> PLANTED(ELEMENT) and
    RESPONSE -> DISCHARGED(ELEMENT). That is a plain slot-to-subtree binding,
    which docs/BACKLOG.md already records `specialize.py` as suppressing, so the
    honest expectation is a miss. Registered anyway because the *reason* for
    the miss turned out to be a second, previously unrecorded filter.
    VERDICT: see "Adjudication" below.

P8 (v0.5 payoff, registered before authoring/regeneration/matching).
    The design's nine numbered payoff entries expand to **ten nodes** because
    `narrative.frames.cartoon_gravity` is a declaration/assertion pair.
    Prediction: the merged graph moves 199 -> 209 nodes while the existing
    shape/typed/family/aliased group counts remain 28/29/28/30. The four
    declared time-reversal pairs produce exactly five separately reported
    mirror-only groups: since/until, past/future duality, prev/next
    distribution, once/eventually unfolding, and heraldry/response. None may
    be counted as a typed twin. Removing the false BEFORE~LEQ `order_le` alias,
    spelling strict precedence with LT, and declaring the strict/reflexive
    relation in HEAD_ALGEBRA change zero existing group memberships. The two
    cartoon nodes validate as the graph's first shared scope and change no
    matcher key because `scope` remains outside `structural_signature`.
    Groundedness predictions from the design: since_unfolding and
    once_unfolding score 1.000 through recursive-definition detection;
    no_deus_ex_machina scores 0.500 through heraldry-pattern membership.
    VERDICT: open; adjudicate below only after all required tools run.

Adjudication (written after running the tools; skeletons quoted verbatim)
------------------------------------------------------------------------

P1  MISSED as a twin, FIRED on the archetype channel -- as predicted.
      temporal   ALWAYS⟨?0:V⟩ = NEG⟨EVENTUALLY⟨NEG⟨?0:V⟩⟩⟩
      logic/set  JOIN⟨NEG⟨?0:V⟩, NEG⟨?1:V⟩⟩ = NEG⟨MEET⟨?0:V, ?1:V⟩⟩
    Two independent blockers, and naming both matters because removing either
    alone changes nothing: (a) the heads differ (ALWAYS/EVENTUALLY vs
    MEET/JOIN), which head literalism makes fatal at *every* level including
    `shape`; (b) the arity differs -- De Morgan relates two operands, the modal
    duality one. A head-alias table alone would not fire this pair; it is the
    same two-blocker situation docs/BACKLOG.md records for the RNN
    pre-activation versus the affine family.
    Choice of channel, and why: the node adopts `de_morgan_duality` rather
    than minting `duality_via_involution`. The adoption is honest, not a
    convenience. `logic.boolean_laws.de_morgan_laws` already carries the
    quantifier form `not(forall x. F(x)) = exists x. not F(x)` as an
    `equivalent_form`, and its own invariants say the law "generalizes verbatim
    to arbitrary arities and, in a complete Boolean algebra, to infinite meets
    and joins". ALWAYS is exactly the infinitary MEET over the suffixes of a
    trace and EVENTUALLY exactly the infinitary JOIN; the modal duality is that
    infinitary De Morgan restricted to the future. So the label is right and
    the skeletons are three -- the same situation morphology recorded when
    `zero_morpheme_identity` adopted `identity_element_law`. The report prints
      `de_morgan_duality: logic.boolean_laws.de_morgan_laws,
       settheory.boolean_laws.de_morgan_laws,
       temporal.modality.temporal_duality`
    under "Archetype ids spanning multiple structures", which is the only
    cross-head channel the graph has.

P2  MISSED as a twin (as expected), and the decomposition readout is a sharper
    -- and worse -- result than the one registered. The until-unfolding
    skeleton is
      JOIN⟨?0:V, MEET⟨?1:V, NEXT⟨UNTIL⟨?1:V, ?0:V⟩⟩⟩⟩ = UNTIL⟨?1:V, ?0:V⟩
    against `?0:V = UPDATE⟨?1:V, ?2:V⟩` (belief state) and
    `?0:V = +(*(?1:P, ?2:V), *(?3:P, ?4:V))` (linear SSM). Nothing could have
    fired: one is lattice-algebraic and self-referential, the others are
    arithmetic and flat. That much was expected.
    The prediction as registered asked whether `decompose.py` would read the
    constituents into known families anyway. It does NOT, and the node scores
      groundedness 0.000 -- the lowest of all seventeen nodes added here,
    on a statement that is an axiom of a fifty-year-old logic. Every one of its
    five non-trivial constituents contains `UNTIL`, the head being defined:
    `JOIN⟨?0, MEET⟨?1, NEXT⟨UNTIL⟨?1, ?0⟩⟩⟩⟩`, `MEET⟨?1, NEXT⟨UNTIL⟨?1, ?0⟩⟩⟩`,
    `NEXT⟨UNTIL⟨?1, ?0⟩⟩`, and `UNTIL⟨?1, ?0⟩` twice. A form inventory built
    from *other* statements' subterms can never ground any of them, because the
    defining occurrence is the only occurrence in the graph. Its plain Boolean
    neighbours do fine by contrast --
    `temporal.modality.next_distributes_over_meet` scores 0.600 and its
    `MEET⟨?0:V, ?1:V⟩` constituent is reported as recurring in 10 statements
    and as the expression side of `geotop.predicates.de9im_disjoint`.
    So the finding is not "the graph sees the pieces but not the loop". It is
    that **self-reference makes a statement maximally ungrounded**: the
    recursion swallows every constituent, and docs/DESIGN-epistemic-ladder.md's
    groundedness score -- which grades the UNGROUNDED rung -- therefore rates a
    correct axiom at 0.000, the value it would give near-gibberish. Every
    recursive definition anyone adds (factorial, Fibonacci, a grammar
    production, the mu-calculus fragment) will be graded the same way. The fix
    shape is small and specific: when scoring a statement, treat the statement's
    own root head as a known form, so that a self-referential constituent is
    grounded in the statement being defined. New backlog item, and the first
    measured defect in the ladder's one graded rung.

P3  MISSED, and the structural relationship is sharper than "different heads".
      temporal        MEET⟨NEXT⟨?0:V⟩, NEXT⟨?1:V⟩⟩ = NEXT⟨MEET⟨?0:V, ?1:V⟩⟩
      compositionality COMPOSE⟨MEANING⟨?0:V⟩, MEANING⟨?1:V⟩⟩ = MEANING⟨CONCAT⟨?0:V, ?1:V⟩⟩
      morpheme count   LENGTH⟨CONCAT⟨?0:V, ?1:V⟩⟩ = +(LENGTH⟨?0:V⟩, LENGTH⟨?1:V⟩)
    All three are `H(f(a,b)) = g(H(a), H(b))`: one projection applied to a
    composite on one side, the same projection applied to the parts and
    recombined on the other. They differ in exactly one respect -- how many of
    the three positions (projection H, inner composer f, outer composer g) are
    filled by *distinct* heads. Compositionality uses three distinct heads;
    morpheme-count uses two heads and an arithmetic `+`; the NEXT law uses two
    heads with **f = g**, because NEXT is an endomorphism of the lattice rather
    than a homomorphism onto a different structure. So the temporal node is the
    degenerate, most-collapsed member of the family, and it is degenerate in the
    direction that ought to make matching *easier*, not harder.
    The consequence is a cleaner argument than the ones already in
    docs/BACKLOG.md: erasing call-head identity (the proposed fourth match
    level) would make the temporal law and compositionality match, since both
    become `H⟨F⟨?0, ?1⟩⟩ = G⟨H⟨?0⟩, H⟨?1⟩⟩` with H, F, G free -- but it would
    *also* wrongly merge the morpheme-count law, whose right-hand recombiner is
    a commutative `+` that the canonicalizer sorts while CONCAT and MEET stay
    ordered. A head-alias mechanism therefore needs to alias heads to heads,
    not heads to operators. Recorded.

P4  FIRED. Flagship. Three disciplines, one skeleton, verbatim:
      IMPLIES⟨MEET⟨LEQ⟨?0:V, ?1:V⟩, LEQ⟨?1:V, ?2:V⟩⟩, LEQ⟨?0:V, ?2:V⟩⟩
        - settheory.order.subset_transitivity          (set_theory)
        - geotop.predicates.containment_transitivity   (geospatial_topology)
        - temporal.order.precedence_transitivity       (temporal_logic)
    Containment of sets, containment of regions and precedence of instants are
    one theorem about one partial order, and the matcher says so without being
    told. The honesty caveat is the one docs/BACKLOG.md asks for under
    `authored_to_match` vs `emergent`: all three are authored to match. The
    template is one shared shape that three seed scripts copied on purpose. What
    that buys is still real -- it is a convention that demonstrably survives
    three independent corpora and does not drift -- but it is a convention
    working, not a discovery.
    One thing the reuse costs, stated because it is a genuine imprecision:
    temporal precedence between *distinct* events is strict and irreflexive,
    while LEQ is the reflexive lattice order. The node is therefore authored
    over the reflexive relation "occurs no later than", which is a true partial
    order on instants and is what transitivity is a theorem about. Strictness is
    carried separately by `temporal.order.strict_precedence_asymmetry`, which
    P8 originally recorded as paying a BEFORE-head singleton price -- see the
    superseded banner on P8 below for how the LT rename cashed that note.

P5  FIRED. Flagship. Three disciplines, one skeleton:
      ?0:P = MEET⟨?1:V, NEG⟨?1:V⟩⟩
        - logic.boolean_laws.complement_laws        (logic)
        - settheory.boolean_laws.complement_laws    (set_theory)
        - narrative.frame.frame_consistency         (narrative)
    A constraint on what a story may assert inside its own frame is
    indistinguishable, to the matcher, from the postulate that makes a lattice
    Boolean. That is the intended result: docs/DESIGN-frames-and-retrieval.md
    claims a fiction is a hypothetical frame in which "the epistemic ladder
    operates unchanged over a LOCAL corpus", and a contradiction against a frame
    premise is "flagged exactly as a false physics claim would be". The twin
    group is that claim, mechanized.
    Authored to match, and declared so: `MEET`, `NEG` and a constant-category
    result slot were chosen because they are the heads the Boolean corpora use.
    An author who spelled this `CONTRADICTS(assertion, premise)` would have got
    a singleton, and the statement would have been no less true.
    What the template cannot say is the part that makes it a *frame* law: that
    the scope is local, and that the premise is VERIFIED inside the frame and
    CONJECTURED-under-premise outside it. The grammar has no scope construct, so
    the whole of "within a frame" lives in `regularity_conditions` as prose.
    Backlog item, and the same family as the missing quantifier already recorded
    for differential topology.

P6  MISSED at every level, as predicted; archetype channel FIRED.
      temporal          ALWAYS⟨?0:V⟩ = ALWAYS⟨ALWAYS⟨?0:V⟩⟩
      logic idempotence ?0:V = MEET⟨?0:V, ?0:V⟩
      double negation   ?0:V = NEG⟨NEG⟨?0:V⟩⟩
    Note what separates the temporal node from double negation, since it is not
    the obvious thing: both are "one unary head applied twice equals it applied
    once", but NEG applied twice equals the *bare slot*, while ALWAYS applied
    twice equals `ALWAYS⟨?0⟩`. The idempotent has a fixed point that the
    involution does not, so the two sides differ in depth and no equality-based
    grouping can relate them. This is a fifth member for docs/BACKLOG.md's
    recorded "slot recurrence, not slot shape" wanted-level (Brouwer fixed
    point, double negation, set idempotence, FTC part 1), and the first one that
    is an idempotent *modality*.
    Archetype: adopts `idempotent_operation`, giving a drift entry across three
    skeletons.

P7  MISSED, and the reason is a filter docs/BACKLOG.md had not recorded.
      response pattern  ALWAYS⟨IMPLIES⟨?0:V, EVENTUALLY⟨?1:V⟩⟩⟩
      Chekhov           ALWAYS⟨IMPLIES⟨PLANTED⟨?0:V⟩, EVENTUALLY⟨DISCHARGED⟨?0:V⟩⟩⟩⟩
    Probed directly with `specialize.match`, verbatim output:
      MATCHES = True | used_absorption = False | used_identity = False
      bindings: {'TRIGGER': 'PLANTED(ELEMENT)', 'RESPONSE': 'DISCHARGED(ELEMENT)'}
    -- the plain-binding suppression docs/BACKLOG.md already records five times.
    But `specialize.py` never even reaches that filter here: `find_specializations`
    skips any pattern whose canonical tree is not a relation
    (`if gtree[0] != "rel": continue`), and the response pattern is a bare LTL
    formula. Counted across the merged graph, **16 of 195 nodes** have non-`rel`
    templates and are therefore excluded from the general side of specialization
    matching outright: algtop.homotopy.homotopy_invariance,
    geotop.predicates.{containment_transitivity, adjacency_symmetry},
    geotop.measure.area_monotonicity,
    logic.inference.{modus_ponens, ex_falso_quodlibet, reductio_ad_absurdum},
    settheory.order.{subset_transitivity, empty_set_minimality}, and the seven
    rule-shaped nodes this file adds. Every inference rule and every relational
    predicate in the graph is in that list. New backlog item, independent of the
    plain-binding one and strictly upstream of it.
    The edge is asserted by hand (`special_case_of` / `generalizes`, reciprocal
    across the two corpora this file owns), which is the outcome docs/BACKLOG.md
    predicts for every plain-binding case.

P8-payoff  STRUCTURE FIRED; GROUNDEDNESS MISSED.
    The graph moved 199 -> 209 nodes and the existing structural ladder stayed
    exactly shape/typed/family/aliased = 28/29/28/30. The separately reported
    mirror level contains exactly the five registered mirror-only groups, with
    zero ladder violations and no mirror group counted as typed. Removing
    BEFORE~LEQ, using LT, and recording strict-part/reflexive-closure relations
    moved no old membership. Both scoped cartoon nodes validate together.
    Groundedness did not follow the registered values: since_unfolding is
    0.667 (not 1.000), once_unfolding is 0.500 (not 1.000), and
    no_deus_ex_machina is 1.000 (not 0.500). Self-headed terms are excluded,
    but other unmatched compounds remain in the recursive nodes' denominators;
    the narrative instance instead gains exact PLANTED/DISCHARGED recurrence
    plus heraldry-pattern coverage. Specialization moved 622 -> 626: the two
    intended cost-4 edges are response_pattern -> cartoon_gravity and
    heraldry_pattern -> no_deus_ex_machina; two cost-7 de9im_disjoint edges are
    noise and are recorded in docs/BACKLOG.md.
    Independent review then found that the registered response/heraldry pair
    was only partially reversed: EVENTUALLY became ONCE while the outer ALWAYS
    incorrectly stayed future-facing. Under a real whole-tree involution the
    first authored formulas yielded four, not five, mirror groups. The past
    formulas now use HISTORICALLY, the matcher applies one global involution,
    and the corrected corpus yields five. The initial five-group result from
    per-head quotienting is retracted as a vacuous implementation of "mirror".

P10 (unregistered). **Zero specialization edges, and zero specialization
    noise.** `specialize.py` produces 468 edges over the merged graph and not
    one of them touches either new corpus, in either direction. That is the
    fifth independent confirmation of the recorded "specialize.py is
    arithmetic-only" limit (`COMMUTATIVE = {+, *}`, `IDENTITY = {+: 0, *: 1}`),
    after logic, set theory, topology and geospatial topology. The new
    information is the other half: four previous corpora reported that all or
    nearly all of their specialization edges were *degenerate noise*, and these
    two report none at all. Templates written entirely in call heads generate
    neither signal nor noise, because the noise mechanism -- a variable slot
    absorbing arguments of a commutative arithmetic op -- has nothing to bite
    on. The proposed category-compatibility constraint should be evaluated
    against that: the corpora it would clean up are exactly the corpora that
    currently get edges.

P8 (unregistered, found while authoring). **[SUPERSEDED by the past-mirror
    slice: `strict_precedence_asymmetry` was renamed to the LT head and now
    aliases into `strict_order` alongside narrative's BEFORE, so the singleton
    price described below no longer exists. The paragraph is kept verbatim as
    the record of what the convention cost before the rename; the retired
    skeleton it quotes is no longer in any corpus.]**
    **The BEFORE head measures what the
    LEQ convention is worth, inside one corpus.**
    `temporal.order.precedence_transitivity` (LEQ) is a three-discipline typed
    twin; `temporal.order.strict_precedence_asymmetry` (BEFORE) is
      IMPLIES⟨BEFORE⟨?0:V, ?1:V⟩, NEG⟨BEFORE⟨?1:V, ?0:V⟩⟩⟩
    and is a singleton at every level. Same corpus, same author, same subject
    matter, adjacent nodes -- one adopts the abstract head and joins a
    cross-discipline group, one uses the natural head and joins nothing. It is
    the cheapest available demonstration that the twin count measures authoring
    convention, and it is a *deliberate* pair: `strict_precedence_asymmetry`
    could not honestly be written with LEQ, because asymmetry is false of a
    reflexive order.

P9 (unregistered). **The story-unit trio triples the opaque-binary-composition
    count in one file.** `?0 = HEAD⟨?1, ?2⟩` was carried by seven heads across
    five corpora (docs/BACKLOG.md). `narrative.structure.setup_introduction`
    (INTRODUCE), `narrative.structure.complication_obstruction` (OBSTRUCT) and
    `narrative.structure.resolution_outcome` (RESOLVE) make it ten -- and these
    three were written in one sitting, by one hand, with *identical* intent and
    identical shape, and no two of them twin each other. Previous entries argued
    head literalism from cross-corpus near misses; this is three nodes in
    consecutive lines of one list. All three adopt morphology's
    `binary_composition_definition` archetype, so the drift report prints the
    four-way group that the twin report cannot.

Decomposition readout (scripts/decompose.py, groundedness per node)
--------------------------------------------------------------------

    1.000  temporal.order.precedence_transitivity
    1.000  narrative.frame.frame_consistency
    0.750  temporal.monotonicity.eventually_monotonicity
    0.667  temporal.modality.always_idempotence
    0.667  temporal.order.strict_precedence_asymmetry
    0.600  temporal.modality.next_distributes_over_meet
    0.500  temporal.modality.temporal_duality
    0.500  temporal.modality.eventually_unfolding
    0.500  temporal.response.response_pattern
    0.400  temporal.induction.temporal_induction_axiom
    0.250  narrative.causality.precedence_causation_bridge
    0.000  temporal.recurrence.until_unfolding
    0.000  narrative.constraint.chekhov_gun
    0.000  narrative.structure.story_sequence
    0.000  narrative.structure.setup_introduction
    0.000  narrative.structure.complication_obstruction
    0.000  narrative.structure.resolution_outcome

Two things this ranking says that no other report does.

1. **Groundedness tracks head reuse almost exactly.** The two nodes at 1.000
   are the two that adopted existing heads wholesale (LEQ/MEET/IMPLIES;
   MEET/NEG); everything in the middle mixes reused Boolean heads with new
   modal ones; the five at 0.000 use only heads this file introduced. The
   score is measuring vocabulary overlap with the existing graph, which is a
   defensible reading of "how much of this is made of known parts" -- but it
   means a new discipline's first corpus is *structurally guaranteed* to grade
   as disorder, no matter how well formed it is. docs/BACKLOG.md's
   "a new discipline's vocabulary is structurally quarantined" entry now has a
   numeric version.

2. **Chekhov's gun scores 0.000 while being written entirely in the temporal
   corpus's own vocabulary.** `ALWAYS(IMPLIES(PLANTED(ELEMENT),
   EVENTUALLY(DISCHARGED(ELEMENT))))` shares ALWAYS, IMPLIES and EVENTUALLY
   with temporal.response.response_pattern, and grounds on none of them,
   because its constituents are `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` and
   `PLANTED⟨?0⟩` rather than `EVENTUALLY⟨?0⟩` -- one extra unary head under
   the modality changes the skeleton. The general node it instantiates scores
   0.500 on the identical formula shape. So the instantiation of a known
   pattern grades lower than the pattern, which inverts what the score is for.
   Same root cause as the head-literalism entries, now visible in the ladder
   rather than in the twin report.

Story-grammar sourcing
----------------------

The narrative corpus is not invented. Propp (1928) established that folktales
decompose into a fixed inventory of functions in a fixed order; Rumelhart
(1975) wrote the first explicit rewrite grammar for stories
(Story -> Setting + Episode); Labov and Waletzky (1967) derived
orientation/complication/resolution from oral personal narrative rather than
from literature. Those three are the sources for the structure nodes.
Trabasso and van den Broek (1985) supply the causal-network reading behind
`narrative.causality.precedence_causation_bridge`; Ryan (1991), Lewis (1978)
and Doležel (1998) supply the possible-worlds reading behind
`narrative.frame.frame_consistency`. The point of the corpus is that these are
*laws* in the corpus's sense -- they have templates, slots, failure modes and
falsifying cases -- not that stories are mathematics.

Authoring constraints observed (all from docs/BACKLOG.md)
---------------------------------------------------------

- `statement_id` may not contain `_` in its first segment, so ids are
  `temporal.*` while the directory and the `discipline` field are
  `temporal_logic` -- the same split `settheory.`/`set_theory`,
  `infotheory.`/`information_theory` and `ml.`/`machine_learning` carry.
  `narrative` needs no split.
- The grammar has no binder, so "for every suffix of the trace" is not
  expressible; ALWAYS and EVENTUALLY are opaque unary heads and their
  semantics live in `functionals` descriptions and `regularity_conditions`.
- Call arguments are ORDERED. The expansion laws fix LTL's own argument order
  (`q or (p and X(p U q))`, disjunct-first) and `UNTIL(hold, goal)` fixes
  hold-first; `BEFORE(earlier, later)`, `ENABLES(cause, effect)`,
  `CAUSES(cause, effect)`, `INTRODUCE(agent, desire)`,
  `OBSTRUCT(desire, obstacle)`, `RESOLVE(desire, outcome)` and
  `SEQUENCE(first, second, third)` all fix an order anything added later must
  keep. Following scripts/seed_logic.py, MEET/JOIN keep the distinguished or
  repeated operand first.
- No slot id begins `sum_ prod_ lim_ max_ min_`; none here does.
- `symbolToken.syntactic_category` has no `functional` member, so every modal
  and narrative head lives in `functionals`, and each node still carries at
  least one scalar `symbols` entry.
- `constantToken` has keys {symbol, description, value?} only.
- Every slot appearing in a template is declared in `slot_schema`.
- Cross-corpus `entails` / `special_case_of` / `generalizes` / `equivalent_to`
  need the reciprocal edge in the target corpus's file. This script owns both
  of its corpora, so the Chekhov/response-pattern pair is written reciprocally;
  every edge into a corpus this script does not own is one-sided
  `composed_with`.
- Run the matcher with PYTHONIOENCODING=utf-8 on Windows: the report prints
  ⟨ ⟩ skeletons.
"""

from __future__ import annotations

import json
from pathlib import Path


# --------------------------------------------------------------------------
# Builders (same shape as scripts/seed_morphology.py)
# --------------------------------------------------------------------------


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="logical"):
    return {"symbol": symbol, "name": name, "arity": arity,
            "operator_family": family}


def slot(sid, cat, role):
    return {"slot_id": sid, "syntactic_category": cat, "semantic_role": role}


def links(entailed_by=None, entails=None, equivalent_to=None,
          special_case_of=None, generalizes=None, composed_with=None):
    return {"entailed_by": entailed_by or [], "entails": entails or [],
            "equivalent_to": equivalent_to or [],
            "special_case_of": special_case_of or [],
            "generalizes": generalizes or [],
            "composed_with": composed_with or []}


def node(sid, title, cls, status, subfield, topic, ascii_, latex, forms,
         archetype, template, slots, invariants, symbols, operators,
         meaning, significance, conditions, provenance, disciplines,
         functionals=None, constants=None, index_sets=None, failure_modes=None,
         inferential_links=None, keywords=None, canonical_objects=None,
         scope=None):
    context = {"disciplines": disciplines, "subfield": subfield, "topic": topic}
    if canonical_objects:
        context["canonical_objects"] = canonical_objects
    interpretation = {"statement_meaning": meaning,
                      "statistical_significance": significance,
                      "regularity_conditions": conditions}
    if failure_modes:
        interpretation["failure_modes"] = failure_modes
    out = {
        "statement_id": sid, "title": title, "statement_class": cls,
        "epistemic_status": status,
        "theory_context": context,
        "formal_statement": {"canonical_ascii": ascii_, "canonical_latex": latex,
                             "equivalent_forms": forms},
        "structural_signature": {"archetype_id": archetype,
                                 "anonymized_template": template,
                                 "slot_schema": slots, "invariants": invariants},
        "symbol_lexicon": {"symbols": symbols, "operators": operators,
                           "functionals": functionals or [],
                           "index_sets": index_sets or [],
                           "constants": constants or []},
        "semantic_interpretation": interpretation,
        "inferential_links": inferential_links or links(),
        "provenance": provenance,
    }
    if keywords:
        out["keywords"] = keywords
    if scope:
        out["scope"] = scope
    return out


# --------------------------------------------------------------------------
# Lexicon fragments
# --------------------------------------------------------------------------

EQ = op("=", "equality of algebra elements", 2, "relational")
LTL_EQUIV = op("=", "temporal equivalence (same set of satisfying traces)",
               2, "logical")
AND = op("and", "conjunction", 2, "logical")
OR = op("or", "disjunction", 2, "logical")
NOT = op("not", "negation", 1, "logical")
IMPL = op("implies", "material implication", 2, "logical")
ENTAILS = op("|-", "entailment / trace inclusion", 2, "logical")
PRECEDES = op("<", "strict temporal precedence", 2, "relational")
PRECEQ = op("<=", "temporal precedence or coincidence", 2, "relational")
BOX = op("G", "always (globally) modality", 1, "logical")
DIAMOND = op("F", "eventually (finally) modality", 1, "logical")
CIRCLE = op("X", "next-state modality", 1, "logical")
UNTIL_OP = op("U", "strong until", 2, "logical")
PAST_BOX = op("H", "historically modality", 1, "logical")
PAST_DIAMOND = op("P", "once modality", 1, "logical")
PREVIOUS = op("Y", "previous-state modality", 1, "logical")
SINCE_OP = op("S", "strong since", 2, "logical")
CONCAT_OP = op("+", "ordered concatenation of story parts", 2, "arithmetic")

# --- lattice heads reused verbatim from scripts/seed_logic.py --------------
# Their descriptions repeat the translation table and add the temporal /
# narrative reading, so that the reuse is documented at the point of reuse.

MEET_FN = {
    "notation": "MEET(.,.)", "name": "lattice meet", "input_arity": 2,
    "codomain": "temporal properties (sets of traces)",
    "description": "Greatest lower bound in the Boolean lattice: conjunction "
                   "in data/logic, intersection in data/set_theory, and here "
                   "the intersection of the trace sets two temporal properties "
                   "denote. The head is reused rather than renamed so that "
                   "Boolean sub-structure inside a temporal statement stays "
                   "visible to the matcher."}
JOIN_FN = {
    "notation": "JOIN(.,.)", "name": "lattice join", "input_arity": 2,
    "codomain": "temporal properties (sets of traces)",
    "description": "Least upper bound in the Boolean lattice: disjunction, "
                   "union, and here the union of trace sets. Argument order "
                   "follows scripts/seed_logic.py's convention, distinguished "
                   "operand first."}
NEG_FN = {
    "notation": "NEG(.)", "name": "lattice complement", "input_arity": 1,
    "codomain": "temporal properties (sets of traces)",
    "description": "Boolean complement: negation, relative complement, and here "
                   "complementation of a trace set within the set of all "
                   "traces. It is the involution that makes the modal duality "
                   "ALWAYS = NEG . EVENTUALLY . NEG hold."}
LEQ_FN = {
    "notation": "LEQ(.,.)", "name": "lattice order", "input_arity": 2,
    "description": "The partial order x <= y, equivalently MEET(x, y) = x. "
                   "Realized as entailment in data/logic, subset inclusion in "
                   "data/set_theory, region containment in "
                   "data/geospatial_topology, and here in two readings that the "
                   "corpus keeps apart on purpose: over instants it is 'occurs "
                   "no later than' (a genuine partial order, hence reflexive); "
                   "over properties it is trace-set inclusion, i.e. entailment."}
IMPLIES_FN = {
    "notation": "IMPLIES(.,.)", "name": "implication", "input_arity": 2,
    "description": "Material implication where the statement is an "
                   "object-language formula, and the meta-level 'if ... then' "
                   "where the statement is a rule. Same head and same double "
                   "reading as scripts/seed_logic.py."}

# --- modal heads (new) ----------------------------------------------------

ALWAYS_FN = {
    "notation": "ALWAYS(.)", "name": "always (globally)", "input_arity": 1,
    "codomain": "temporal properties (sets of traces)",
    "description": "G phi: phi holds at every position of the trace from now "
                   "on. Semantically the infinitary MEET over all suffixes; the "
                   "grammar has no binder (docs/BACKLOG.md), so the "
                   "quantification over suffixes is carried by this opaque head "
                   "rather than written out. That is exactly why the modal "
                   "duality below cannot twin the finitary De Morgan law."}
EVENTUALLY_FN = {
    "notation": "EVENTUALLY(.)", "name": "eventually (finally)",
    "input_arity": 1, "codomain": "temporal properties (sets of traces)",
    "description": "F phi: phi holds at some position from now on. Semantically "
                   "the infinitary JOIN over suffixes, dual to ALWAYS. Liveness "
                   "properties are the ones that need it; safety properties do "
                   "not."}
NEXT_FN = {
    "notation": "NEXT(.)", "name": "next state", "input_arity": 1,
    "codomain": "temporal properties (sets of traces)",
    "description": "X phi: phi holds at the immediately following position. The "
                   "only modality that is a *function* on positions rather than "
                   "a quantifier over them, which is why it distributes over "
                   "every Boolean connective, including NEG -- ALWAYS and "
                   "EVENTUALLY distribute over only one each."}
UNTIL_FN = {
    "notation": "UNTIL(hold, goal)", "name": "strong until", "input_arity": 2,
    "codomain": "temporal properties (sets of traces)",
    "description": "phi U psi: psi holds at some future position and phi holds "
                   "at every position strictly before it. Argument order is "
                   "fixed hold-first, goal-second, matching the usual infix "
                   "reading. 'Strong' means psi is required to occur; the weak "
                   "variant (which permits phi forever) is recorded as an "
                   "equivalent form, not as a separate head."}
HISTORICALLY_FN = {
    "notation": "HISTORICALLY(.)", "name": "historically",
    "input_arity": 1, "codomain": "temporal properties (sets of traces)",
    "description": "H phi: phi has held at every position from the trace "
                   "origin through now; the time-reversal mirror of ALWAYS."}
ONCE_FN = {
    "notation": "ONCE(.)", "name": "once", "input_arity": 1,
    "codomain": "temporal properties (sets of traces)",
    "description": "P phi: phi held at some position at or before now; the "
                   "time-reversal mirror of EVENTUALLY."}
PREV_FN = {
    "notation": "PREV(.)", "name": "previous state", "input_arity": 1,
    "codomain": "temporal properties (sets of traces)",
    "description": "Y phi: phi held at the immediately preceding position. "
                   "This corpus fixes strong previous semantics: Y phi is "
                   "false at the trace origin. That boundary choice is "
                   "required by the SINCE and ONCE unfoldings below."}
SINCE_FN = {
    "notation": "SINCE(hold, origin)", "name": "strong since",
    "input_arity": 2, "codomain": "temporal properties (sets of traces)",
    "description": "phi S psi: psi held at some past position and phi has "
                   "held continuously since; hold-first, origin-second."}
HOLDS_FN = {
    "notation": "HOLDS(.)", "name": "frame proposition holds",
    "input_arity": 1,
    "description": "Lifts a declared frame premise into the temporal trace "
                   "of that frame's evolving state."}
BEFORE_FN = {
    "notation": "BEFORE(earlier, later)", "name": "strict precedence",
    "input_arity": 2,
    "description": "The strict happens-before relation between two events: "
                   "irreflexive, asymmetric, transitive. Argument order is "
                   "fixed earlier-first. Deliberately NOT spelled with the "
                   "lattice head LEQ, because LEQ is the reflexive order and "
                   "asymmetry is false of a reflexive relation -- the honest "
                   "spelling costs every twin the head could have bought, which "
                    "is the point the adjacent transitivity node measures."}
LT_FN = {
    "notation": "LT(earlier, later)", "name": "abstract strict order",
    "input_arity": 2,
    "description": "The irreflexive strict part of LEQ. BEFORE is temporal "
                   "logic's concrete spelling and aliases only to LT, never "
                   "to the reflexive LEQ head."}
RESPONSE_KEYWORDS = ["liveness", "response pattern", "specification pattern"]

# --- narrative heads (new) ------------------------------------------------

SEQUENCE_FN = {
    "notation": "SEQUENCE(first, second, third)", "name": "ordered episode sequence",
    "input_arity": 3, "codomain": "stories",
    "description": "Ordered composition of story parts: the parts are laid out "
                   "in narrated order, first argument earliest. Written as a "
                   "call because call arguments are ORDERED in the matcher and "
                   "narrative order is the entire content of the claim -- the "
                   "same reason data/morphology writes CONCAT as a call rather "
                   "than reusing MEET."}
INTRODUCE_FN = {
    "notation": "INTRODUCE(agent, desire)", "name": "setup constructor",
    "input_arity": 2, "codomain": "story parts",
    "description": "The operation that builds a setup out of an agent and the "
                   "agent's want. Argument order fixed agent-first. Propp's "
                   "initial situation and Labov-Waletzky's orientation are the "
                   "two sources for the pairing."}
OBSTRUCT_FN = {
    "notation": "OBSTRUCT(desire, obstacle)", "name": "complication constructor",
    "input_arity": 2, "codomain": "story parts",
    "description": "The operation that builds a complication by placing an "
                   "obstacle against an existing desire. Argument order fixed "
                   "desire-first: the desire must already exist, which is what "
                   "makes the story parts ordered rather than a set."}
RESOLVE_FN = {
    "notation": "RESOLVE(desire, outcome)", "name": "resolution constructor",
    "input_arity": 2, "codomain": "story parts",
    "description": "The operation that closes a desire with an outcome, "
                   "satisfying or defeating it. Argument order fixed "
                   "desire-first, matching OBSTRUCT."}
ENABLES_FN = {
    "notation": "ENABLES(earlier, later)", "name": "narrative enablement",
    "input_arity": 2,
    "description": "The earlier event makes the later one possible: it "
                   "establishes a precondition without forcing the outcome. "
                   "Trabasso and van den Broek's causal-network relation, "
                   "weaker than CAUSES and stronger than mere precedence."}
CAUSES_FN = {
    "notation": "CAUSES(cause, effect)", "name": "narrative causation",
    "input_arity": 2,
    "description": "The relation a reader posits between two story events. "
                   "Deliberately a narrative head and not a physical one: the "
                   "node that uses it asserts what readers infer, not what the "
                   "world does."}
PLANTED_FN = {
    "notation": "PLANTED(.)", "name": "element introduced in the setup",
    "input_arity": 1,
    "description": "Holds at a position when the story element has been "
                   "explicitly presented to the audience. Unary so that the "
                   "Chekhov constraint is a property of one element rather than "
                   "a relation between two."}
DISCHARGED_FN = {
    "notation": "DISCHARGED(.)", "name": "element consumed by the plot",
    "input_arity": 1,
    "description": "Holds at a position when the planted element has done "
                   "narrative work. 'The gun goes off' in Chekhov's own "
                   "example; 'paid off' in screenwriting usage."}
NOTICES_FN = {
    "notation": "NOTICES(.)", "name": "notices unsupported state",
    "input_arity": 1,
    "description": "Cartoon-frame trigger: the body becomes aware that it is "
                   "unsupported."}
FALLS_FN = {
    "notation": "FALLS(.)", "name": "falls", "input_arity": 1,
    "description": "Cartoon-frame response whose ordinary-world grounding is "
                   "explicitly suspended inside the frame."}

INCONSISTENCY_CONST = {
    "symbol": "bottom",
    "description": "The falsum of the frame's local lattice: the property no "
                   "trace and no story-state satisfies. Written as a constant "
                   "slot so that the frame law lands on the same "
                   "parameter-like result position that FALSITY and EMPTYSET "
                   "occupy in logic.boolean_laws.complement_laws and "
                   "settheory.boolean_laws.complement_laws."}


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

PNUELI1977 = {"citation_key": "pnueli1977",
              "bibliographic_entry": "Pnueli, A. (1977). The Temporal Logic of Programs. Proceedings of the 18th Annual Symposium on Foundations of Computer Science (FOCS), 46-57."}
MANNA_PNUELI = {"citation_key": "manna1992",
                "bibliographic_entry": "Manna, Z., Pnueli, A. (1992). The Temporal Logic of Reactive and Concurrent Systems: Specification. New York: Springer."}
PRIOR1957 = {"citation_key": "prior1957",
             "bibliographic_entry": "Prior, A. N. (1957). Time and Modality. Oxford: Clarendon Press."}
EMERSON1990 = {"citation_key": "emerson1990",
               "bibliographic_entry": "Emerson, E. A. (1990). Temporal and Modal Logic. In J. van Leeuwen (ed.), Handbook of Theoretical Computer Science, Volume B, 995-1072. Amsterdam: Elsevier."}
CLARKE1999 = {"citation_key": "clarke1999",
              "bibliographic_entry": "Clarke, E. M., Grumberg, O., Peled, D. A. (1999). Model Checking. Cambridge, MA: MIT Press."}
BAIER2008 = {"citation_key": "baier2008",
             "bibliographic_entry": "Baier, C., Katoen, J.-P. (2008). Principles of Model Checking. Cambridge, MA: MIT Press."}
KRIPKE1963 = {"citation_key": "kripke1963",
              "bibliographic_entry": "Kripke, S. A. (1963). Semantical Considerations on Modal Logic. Acta Philosophica Fennica, 16, 83-94."}
LAMPORT1978 = {"citation_key": "lamport1978",
               "bibliographic_entry": "Lamport, L. (1978). Time, Clocks, and the Ordering of Events in a Distributed System. Communications of the ACM, 21(7), 558-565."}
DWYER1999 = {"citation_key": "dwyer1999",
             "bibliographic_entry": "Dwyer, M. B., Avrunin, G. S., Corbett, J. C. (1999). Patterns in Property Specifications for Finite-State Verification. Proceedings of the 21st International Conference on Software Engineering (ICSE), 411-420."}
VARDI1986 = {"citation_key": "vardi1986",
             "bibliographic_entry": "Vardi, M. Y., Wolper, P. (1986). An Automata-Theoretic Approach to Automatic Program Verification. Proceedings of the 1st IEEE Symposium on Logic in Computer Science (LICS), 332-344."}
ALLEN1983 = {"citation_key": "allen1983",
             "bibliographic_entry": "Allen, J. F. (1983). Maintaining Knowledge about Temporal Intervals. Communications of the ACM, 26(11), 832-843."}
HUGHES1996 = {"citation_key": "hughes1996",
              "bibliographic_entry": "Hughes, G. E., Cresswell, M. J. (1996). A New Introduction to Modal Logic. London: Routledge."}
BLACKBURN2001 = {"citation_key": "blackburn2001",
                 "bibliographic_entry": "Blackburn, P., de Rijke, M., Venema, Y. (2001). Modal Logic. Cambridge Tracts in Theoretical Computer Science 53. Cambridge: Cambridge University Press."}
LAMPORT1977 = {"citation_key": "lamport1977",
               "bibliographic_entry": "Lamport, L. (1977). Proving the Correctness of Multiprocess Programs. IEEE Transactions on Software Engineering, SE-3(2), 125-143."}
TARSKI1955 = {"citation_key": "tarski1955",
              "bibliographic_entry": "Tarski, A. (1955). A Lattice-Theoretical Fixpoint Theorem and its Applications. Pacific Journal of Mathematics, 5(2), 285-309."}

PROPP1928 = {"citation_key": "propp1928",
             "bibliographic_entry": "Propp, V. (1928/1968). Morphology of the Folktale (2nd ed., trans. L. Scott, rev. L. A. Wagner). Austin: University of Texas Press."}
RUMELHART1975 = {"citation_key": "rumelhart1975",
                 "bibliographic_entry": "Rumelhart, D. E. (1975). Notes on a Schema for Stories. In D. G. Bobrow and A. Collins (eds.), Representation and Understanding: Studies in Cognitive Science, 211-236. New York: Academic Press."}
LABOV1967 = {"citation_key": "labov1967",
             "bibliographic_entry": "Labov, W., Waletzky, J. (1967). Narrative Analysis: Oral Versions of Personal Experience. In J. Helm (ed.), Essays on the Verbal and Visual Arts, 12-44. Seattle: University of Washington Press."}
MANDLER1977 = {"citation_key": "mandler1977",
               "bibliographic_entry": "Mandler, J. M., Johnson, N. S. (1977). Remembrance of Things Parsed: Story Structure and Recall. Cognitive Psychology, 9(1), 111-151."}
TRABASSO1985 = {"citation_key": "trabasso1985",
                "bibliographic_entry": "Trabasso, T., van den Broek, P. (1985). Causal Thinking and the Representation of Narrative Events. Journal of Memory and Language, 24(5), 612-630."}
BREMOND1973 = {"citation_key": "bremond1973",
               "bibliographic_entry": "Bremond, C. (1973). Logique du recit. Paris: Editions du Seuil."}
TODOROV1969 = {"citation_key": "todorov1969",
               "bibliographic_entry": "Todorov, T. (1969). Grammaire du Decameron. Approaches to Semiotics 3. The Hague: Mouton."}
PRINCE1973 = {"citation_key": "prince1973",
              "bibliographic_entry": "Prince, G. (1973). A Grammar of Stories: An Introduction. The Hague: Mouton."}
FREYTAG1863 = {"citation_key": "freytag1863",
               "bibliographic_entry": "Freytag, G. (1863). Die Technik des Dramas. Leipzig: S. Hirzel."}
CHEKHOV1889 = {"citation_key": "chekhov1889",
               "bibliographic_entry": "Chekhov, A. P. (1889). Letter to A. S. Lazarev (Gruzinsky), 1 November 1889. In S. Karlinsky and M. H. Heim (eds., trans., 1973), Anton Chekhov's Life and Thought: Selected Letters and Commentary. Berkeley: University of California Press."}
SCHANK1977 = {"citation_key": "schank1977",
              "bibliographic_entry": "Schank, R. C., Abelson, R. P. (1977). Scripts, Plans, Goals and Understanding: An Inquiry into Human Knowledge Structures. Hillsdale, NJ: Lawrence Erlbaum."}
RYAN1991 = {"citation_key": "ryan1991",
            "bibliographic_entry": "Ryan, M.-L. (1991). Possible Worlds, Artificial Intelligence, and Narrative Theory. Bloomington: Indiana University Press."}
LEWIS1978 = {"citation_key": "lewis1978",
             "bibliographic_entry": "Lewis, D. (1978). Truth in Fiction. American Philosophical Quarterly, 15(1), 37-46."}
DOLEZEL1998 = {"citation_key": "dolezel1998",
               "bibliographic_entry": "Dolezel, L. (1998). Heterocosmica: Fiction and Possible Worlds. Baltimore: Johns Hopkins University Press."}
WALTON1990 = {"citation_key": "walton1990",
              "bibliographic_entry": "Walton, K. L. (1990). Mimesis as Make-Believe: On the Foundations of the Representational Arts. Cambridge, MA: Harvard University Press."}
GENETTE1980 = {"citation_key": "genette1980",
               "bibliographic_entry": "Genette, G. (1980). Narrative Discourse: An Essay in Method (trans. J. E. Lewin). Ithaca: Cornell University Press."}
MANI2010 = {"citation_key": "mani2010",
            "bibliographic_entry": "Mani, I. (2010). The Imagined Moment: Time, Narrative, and Computation. Lincoln: University of Nebraska Press."}
COLERIDGE1817 = {"citation_key": "coleridge1817",
                 "bibliographic_entry": "Coleridge, S. T. (1817). Biographia Literaria; or, Biographical Sketches of My Literary Life and Opinions, Volume II, Chapter XIV. London: Rest Fenner."}


# --------------------------------------------------------------------------
# Shared symbol fragments
# --------------------------------------------------------------------------

PROP_SYMS = [
    sym("p", "variable", "temporal_proposition",
        "An arbitrary temporal property: a set of infinite traces over the "
        "atomic propositions of the system."),
    sym("q", "variable", "temporal_proposition",
        "A second arbitrary temporal property, independent of p."),
]
EVENT_SYMS = [
    sym("a", "variable", "event_operand",
        "An event, identified with the instant at which it occurs."),
    sym("b", "variable", "event_operand", "A second event."),
    sym("c", "variable", "event_operand", "A third event."),
]

TEMPORAL_OBJECTS = ["infinite trace", "temporal property", "Kripke structure",
                    "linear order of instants"]
NARRATIVE_OBJECTS = ["story", "story part", "story event", "narrative frame"]


# --------------------------------------------------------------------------
# Temporal-logic corpus
# --------------------------------------------------------------------------

TEMPORAL_NODES = [

    node("temporal.modality.temporal_duality",
         "Temporal Duality (Always as Not-Eventually-Not)",
         "identity", "formal", "linear_temporal_logic", "modal_duality",
         "always(p) = not(eventually(not p))",
         "\\Box p \\equiv \\lnot \\Diamond \\lnot p",
         [{"form_id": "dual", "notation_system": "ascii",
           "expression": "eventually(p) = not(always(not p))",
           "scope_note": "The mirror half; either direction defines one modality from the other"},
          {"form_id": "unicode", "notation_system": "ascii",
           "expression": "G p ≡ ¬F¬p",
           "scope_note": "Model-checking notation, G for globally and F for finally"},
          {"form_id": "quantifier", "notation_system": "ascii",
           "expression": "not(forall i >= now. p at i) = exists i >= now. not(p at i)",
           "scope_note": "Unfolded over trace positions; this is the first-order De Morgan law of logic.boolean_laws.de_morgan_laws, restricted to the future"},
          {"form_id": "safety_liveness", "notation_system": "ascii",
           "expression": "the complement of a safety property is a liveness property",
           "scope_note": "The reading that makes the duality operationally useful: a counterexample to G p is a witness for F not-p, which is why finite counterexamples exist for safety and not for liveness"}],
         "de_morgan_duality",
         "ALWAYS(PROP) = NEG(EVENTUALLY(NEG(PROP)))",
         [slot("PROP", "variable", "temporal_proposition")],
         ["ALWAYS is the infinitary MEET over trace suffixes and EVENTUALLY the "
          "infinitary JOIN, so this statement is De Morgan's law taken to the "
          "limit -- the same law logic.boolean_laws.de_morgan_laws already "
          "carries in its `quantifier` equivalent form.",
          "Only one free operand appears, twice, so the law constrains the "
          "operators and says nothing about any relation between operands. That "
          "is precisely why it cannot twin the binary De Morgan law: the "
          "arities differ before the heads are even compared.",
          "NEG appears on both sides at different depths; the law holds because "
          "NEG is an involution (logic.boolean_laws.double_negation), which is "
          "what lets each modality be eliminated in favour of the other.",
          "Self-dual as a pair: swapping ALWAYS with EVENTUALLY maps the stated "
          "form onto its mirror, so one half proves the other.",
          "The archetype_id `de_morgan_duality` is adopted from the Boolean "
          "corpora on purpose. The skeletons differ and the label does not, "
          "which is the drift entry docs/BACKLOG.md proposes promoting into a "
          "head-alias discovery channel."],
         PROP_SYMS[:1], [LTL_EQUIV, NOT, BOX, DIAMOND],
         "Saying a property holds at every future moment is exactly denying "
         "that it ever fails; the two modalities are each other's negation "
         "sandwiched between negations.",
         "The corpus's test of whether the archetype channel can carry a "
         "relationship the skeleton channel structurally cannot. It cannot twin "
         "logic.boolean_laws.de_morgan_laws -- head literalism blocks "
         "ALWAYS/EVENTUALLY against MEET/JOIN, and the arity blocks it a second "
         "time -- so the node adopts the `de_morgan_duality` archetype instead, "
         "and the matcher's `archetype_label_drift` section reports the three-"
         "way spread. The relationship is not an analogy: an infinite Boolean "
         "algebra's De Morgan law for arbitrary meets and joins, restricted to "
         "the suffixes of one trace, IS this statement. Operationally the "
         "duality is why model checkers report safety violations as finite "
         "counterexamples and liveness violations as lassos.",
         ["Linear time: each state has exactly one successor, so 'the future' "
          "is a single trace rather than a branching tree",
          "Classical two-valued semantics, with NEG an involution",
          "Traces are infinite, so every suffix is non-empty and both "
          "modalities are total"],
         [PNUELI1977, PRIOR1957, EMERSON1990, BAIER2008, KRIPKE1963],
         ["temporal_logic"],
         functionals=[ALWAYS_FN, EVENTUALLY_FN, NEG_FN],
         failure_modes=[
             "Fails in branching time as stated: CTL's AG p is dual to EF not-p, "
             "not to AF not-p, so the path quantifier must flip along with the "
             "modality. Transplanting the LTL duality to CTL is the standard "
             "error.",
             "Fails over finite traces unless the semantics is fixed: on a "
             "finite word, weak and strong readings of the modalities diverge, "
             "and LTLf has to choose which of G and F is the dual of which.",
             "Intuitionistically the elimination direction fails for the same "
             "reason double negation does; constructive temporal logics keep "
             "one implication only."],
         inferential_links=links(
             entails=["temporal.modality.eventually_unfolding"],
             composed_with=["temporal.modality.always_idempotence",
                            "temporal.monotonicity.eventually_monotonicity",
                            "logic.boolean_laws.de_morgan_laws",
                            "logic.boolean_laws.double_negation"]),
         keywords=["temporal duality", "De Morgan", "always", "eventually",
                   "modal logic", "safety", "liveness"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.recurrence.until_unfolding",
         "Expansion Law for Until",
         "axiom", "formal", "linear_temporal_logic", "fixpoint_expansion",
         "(p until q) = q or (p and next(p until q))",
         "p \\mathbin{\\mathcal{U}} q \\equiv q \\lor (p \\land \\mathrm{X}(p \\mathbin{\\mathcal{U}} q))",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "p U q ≡ q ∨ (p ∧ X(p U q))",
           "scope_note": "The standard infix spelling"},
          {"form_id": "fixpoint", "notation_system": "ascii",
           "expression": "p U q = least fixpoint of Z. (q or (p and next Z))",
           "scope_note": "Mu-calculus reading: until is the LEAST fixpoint, which is what forces q to actually occur"},
          {"form_id": "weak_until", "notation_system": "ascii",
           "expression": "p W q = q or (p and next(p W q)), taken as the GREATEST fixpoint",
           "scope_note": "Weak until satisfies the same expansion equation; only the choice of fixpoint distinguishes them, which is why the equation alone does not define the operator"},
          {"form_id": "automaton", "notation_system": "ascii",
           "expression": "one state, one self-loop guarded by p, one exit guarded by q",
           "scope_note": "The expansion law read as the transition relation of the Buechi automaton that Vardi-Wolper construction builds"}],
         "fixpoint_expansion_law",
         "UNTIL(PROPA, PROPB) = JOIN(PROPB, MEET(PROPA, NEXT(UNTIL(PROPA, PROPB))))",
         [slot("PROPA", "variable", "temporal_proposition"),
          slot("PROPB", "variable", "temporal_proposition")],
         ["The defined head UNTIL occurs on both sides, once at the root and "
          "once under NEXT inside its own definition. That self-reference is "
          "the recurrence, and it is the one thing neither match_signatures.py "
          "nor decompose.py can see: the matcher compares whole skeletons and "
          "decompose compares expression sides, so a subterm that repeats the "
          "statement's own head is just another subterm to both.",
          "The equation is satisfied by two operators, strong and weak until; "
          "only the side condition 'least fixpoint' picks out the strong one. "
          "The template therefore under-determines the node, and the missing "
          "content lives in regularity_conditions -- the same loss "
          "docs/BACKLOG.md records for quantifiers in differential topology.",
          "Argument order is doubly load-bearing: UNTIL is hold-first, and the "
          "JOIN puts the goal disjunct first because that is the order the "
          "operator is read in and the order the automaton takes its exit.",
          "One step of the recurrence is one step of the trace, so iterating "
          "the equation generates the unrolling q, p and X q, p and X(p and "
          "XX q), ... -- the same relationship an SSM state update has to its "
          "impulse response.",
          "Every other LTL operator is a special case of this one (F q = true "
          "U q, G p = not(true U not p)), so the corpus keeps the expansion law "
          "as an axiom and derives the eventually-unfolding from it."],
         PROP_SYMS, [LTL_EQUIV, AND, OR, CIRCLE, UNTIL_OP],
         "Waiting for a goal while a condition holds means either the goal is "
         "already met, or the condition holds now and the same wait continues "
         "from the next moment.",
         "Registered as a prediction against the state-update family "
         "(ml.recurrence.belief_state_update, "
         "ml.recurrence.linear_ssm_state_update) and it misses, as expected: "
         "those are arithmetic and flat, this is lattice-algebraic and "
         "self-referential. What the miss exposes is more useful than a hit "
         "would have been. scripts/decompose.py scores this node's groundedness "
         "at 0.000 -- the lowest of the seventeen nodes added with it, on a "
         "statement that is an axiom of a fifty-year-old logic -- because all "
         "five of its non-trivial constituents contain UNTIL, the head being "
         "defined, and a form inventory built from other statements can never "
         "match them. Its plainly Boolean neighbour "
         "temporal.modality.next_distributes_over_meet scores 0.600 by "
         "comparison, its MEET constituent recognized as recurring in ten "
         "statements. So self-reference does not merely go unnoticed; it drives "
         "the epistemic ladder's one graded rung to the value it reserves for "
         "near-gibberish. Every recursive definition anyone adds -- factorial, "
         "Fibonacci, a grammar production, the mu-calculus fragment -- will be "
         "graded the same way, and the fix is small: score a statement's own "
         "root head as a known form while decomposing it.",
         ["Infinite traces, so 'some future position' is well defined",
          "Least-fixpoint reading: the goal must eventually hold. Under the "
          "greatest-fixpoint reading the same equation defines weak until, and "
          "the template cannot distinguish them",
          "Monotonicity of the unfolding functional in Z, which Tarski's "
          "theorem needs for the fixpoints to exist"],
         [PNUELI1977, MANNA_PNUELI, BAIER2008, VARDI1986, TARSKI1955],
         ["temporal_logic"],
         functionals=[UNTIL_FN, NEXT_FN, MEET_FN, JOIN_FN],
         failure_modes=[
             "Read as a definition, it is wrong: the equation has two solutions "
             "and picks neither. Implementations that translate the expansion "
             "law directly into a transition relation without a fairness or "
             "acceptance condition silently implement weak until.",
             "The recursion is guarded by NEXT; dropping the NEXT gives an "
             "unguarded equation with no unique solution and a "
             "non-terminating tableau.",
             "Over finite traces the last position has no successor, so NEXT "
             "must be split into weak and strong variants before the law can be "
             "stated at all."],
         inferential_links=links(
             entails=["temporal.modality.eventually_unfolding"],
             composed_with=["temporal.modality.next_distributes_over_meet",
                            "temporal.modality.temporal_duality",
                            "ml.recurrence.belief_state_update",
                            "ml.recurrence.linear_ssm_state_update"]),
         keywords=["until", "expansion law", "fixpoint", "recurrence",
                   "Buechi automaton", "linear temporal logic"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.modality.eventually_unfolding",
         "Expansion Law for Eventually",
         "identity", "derived", "linear_temporal_logic", "fixpoint_expansion",
         "eventually(p) = p or next(eventually(p))",
         "\\Diamond p \\equiv p \\lor \\mathrm{X}\\Diamond p",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "F p ≡ p ∨ XF p"},
          {"form_id": "dual", "notation_system": "ascii",
           "expression": "always(p) = p and next(always(p))",
           "scope_note": "The dual unfolding, obtained by applying temporal.modality.temporal_duality to both sides; it is a GREATEST fixpoint where this one is a least fixpoint"},
          {"form_id": "from_until", "notation_system": "ascii",
           "expression": "eventually(p) = (true until p)",
           "scope_note": "Why this node is derived rather than axiomatic: substitute PROPA := TRUTH in the until expansion and simplify by the identity laws"}],
         "fixpoint_expansion_law",
         "EVENTUALLY(PROP) = JOIN(PROP, NEXT(EVENTUALLY(PROP)))",
         [slot("PROP", "variable", "temporal_proposition")],
         ["The same expansion shape as temporal.recurrence.until_unfolding with "
          "one operand instead of two, and it does not twin it: the arity "
          "differs and the head differs, so the two halves of one axiom scheme "
          "sit in separate groups. Both carry the archetype "
          "`fixpoint_expansion_law`, which is the only channel that records the "
          "relationship.",
          "Least fixpoint again, and again the equation alone does not say so: "
          "the greatest fixpoint of the same functional is the constant true.",
          "The dual unfolding for ALWAYS has skeleton "
          "ALWAYS⟨?0:V⟩ = MEET⟨?0:V, NEXT⟨ALWAYS⟨?0:V⟩⟩⟩ -- identical to this "
          "one apart from two head strings -- and would be a third non-twinning "
          "member of the same family. It is recorded as an equivalent form "
          "rather than authored as a node, because a third copy would measure "
          "nothing the first two do not already measure.",
          "Progress, not just possibility: because the fixpoint is least, "
          "iterating the unfolding must terminate, which is why liveness "
          "checking searches for an accepting cycle rather than a reachable "
          "state."],
         PROP_SYMS[:1], [LTL_EQUIV, OR, CIRCLE, DIAMOND],
         "Something happens eventually exactly when it happens now or it "
         "eventually happens starting from the next moment.",
         "Authored as the one-operand case of the until expansion so that the "
         "corpus carries the pair, and the pair is what shows the cost: two "
         "instances of one axiom scheme, written by one hand in one file "
         "minutes apart, with skeletons "
         "`EVENTUALLY⟨?0:V⟩ = JOIN⟨?0:V, NEXT⟨EVENTUALLY⟨?0:V⟩⟩⟩` and "
         "`JOIN⟨?0:V, MEET⟨?1:V, NEXT⟨UNTIL⟨?1:V, ?0:V⟩⟩⟩⟩ = UNTIL⟨?1:V, ?0:V⟩`, "
         "sharing no group at shape, typed or family level. The shared "
         "archetype_id is the entire recorded relationship, which is the case "
         "docs/BACKLOG.md's head-alias proposal is meant to cover.",
         ["Infinite traces",
          "Least-fixpoint reading",
          "Derived from temporal.recurrence.until_unfolding by substituting the "
          "top element for the hold condition, which needs the identity laws of "
          "the underlying Boolean algebra"],
         [PNUELI1977, MANNA_PNUELI, EMERSON1990, BAIER2008],
         ["temporal_logic"],
         functionals=[EVENTUALLY_FN, NEXT_FN, JOIN_FN, ALWAYS_FN],
         failure_modes=[
             "Mistaking the least fixpoint for the greatest turns 'eventually' "
             "into 'possibly forever deferred'; the equation is satisfied by "
             "the constant-true property, which is not what F means.",
             "Over finite traces the unfolding terminates at the last position "
             "and F p becomes decidable by inspection, so results about "
             "liveness checking do not transfer from infinite to finite "
             "semantics."],
         inferential_links=links(
             entailed_by=["temporal.recurrence.until_unfolding",
                          "temporal.modality.temporal_duality"],
             composed_with=["temporal.modality.next_distributes_over_meet",
                            "temporal.response.response_pattern"]),
         keywords=["eventually", "expansion law", "least fixpoint",
                   "liveness", "unfolding"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.modality.next_distributes_over_meet",
         "Next Distributes over Conjunction",
         "axiom", "formal", "linear_temporal_logic", "modal_homomorphism",
         "next(p and q) = next(p) and next(q)",
         "\\mathrm{X}(p \\land q) \\equiv \\mathrm{X}p \\land \\mathrm{X}q",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "X(p ∧ q) ≡ Xp ∧ Xq"},
          {"form_id": "self_dual", "notation_system": "ascii",
           "expression": "next(not p) = not(next p)",
           "scope_note": "NEXT commutes with negation too, which no other modality does; together with this law it makes NEXT a Boolean-algebra endomorphism"},
          {"form_id": "join", "notation_system": "ascii",
           "expression": "next(p or q) = next(p) or next(q)",
           "scope_note": "The join half, which follows from the meet half and the negation law"},
          {"form_id": "always_half", "notation_system": "ascii",
           "expression": "always(p and q) = always(p) and always(q), but always(p or q) is strictly stronger than always(p) or always(q)",
           "scope_note": "The contrast that makes NEXT special: G distributes over meet only, F over join only, X over both"}],
         "modal_meet_homomorphism",
         "NEXT(MEET(PROPA, PROPB)) = MEET(NEXT(PROPA), NEXT(PROPB))",
         [slot("PROPA", "variable", "temporal_proposition"),
          slot("PROPB", "variable", "temporal_proposition")],
         ["A homomorphism statement in the exact sense of "
          "morphology.semantics.compositionality and "
          "morphology.quantity.morpheme_count_additivity: one projection "
          "applied to a composite on one side, the same projection applied to "
          "the parts and recombined on the other.",
          "It is the *degenerate* member of that family, because the "
          "recombining operation equals the composing operation. "
          "Compositionality has three distinct heads (MEANING, CONCAT, "
          "COMPOSE), the morpheme count has two heads and an arithmetic `+`, "
          "and this has two heads with the composer used twice -- NEXT is an "
          "endomorphism of one lattice, not a homomorphism onto another. "
          "Collapsing in the direction that ought to make matching easier still "
          "produces no group, because head identity is literal at every level.",
          "NEXT is the only LTL modality that is a function on positions rather "
          "than a quantifier over them, and that is the whole proof: the "
          "successor of a position is unique, so every Boolean connective "
          "commutes with it.",
          "Symmetric in the two operands, since MEET is; the ordered-call "
          "problem docs/BACKLOG.md records for MEET applies here as it does "
          "everywhere else in the Boolean corpora.",
          "This is the K axiom of normal modal logic specialized to a "
          "functional accessibility relation, plus the converse -- normal modal "
          "logics get only one direction."],
         PROP_SYMS, [LTL_EQUIV, AND, OR, NOT, CIRCLE],
         "Whether two things hold together at the next moment is settled by "
         "whether each of them holds at the next moment: looking one step ahead "
         "does not disturb conjunction.",
         "Registered as a prediction against "
         "morphology.semantics.compositionality, and the honest report is a "
         "miss with an informative reason. The three homomorphism statements in "
         "the graph differ in exactly how many of the three positions "
         "(projection, inner composer, outer composer) carry distinct heads: "
         "three, two-plus-an-operator, and two. Erasing call-head identity -- "
         "the fourth match level docs/BACKLOG.md proposes -- would join this "
         "node to compositionality, since both become "
         "`H⟨F⟨?0, ?1⟩⟩ = G⟨H⟨?0⟩, H⟨?1⟩⟩`. It would NOT join the morpheme-count "
         "law, whose recombiner is a commutative `+` that the canonicalizer "
         "flattens and sorts while CONCAT and MEET stay ordered. So the "
         "proposed alias table must alias heads to heads and not heads to "
         "operators, and this trio is the regression test for that distinction.",
         ["Linear time with a total successor function: every position has "
          "exactly one next position",
          "Infinite traces, so NEXT is total and needs no weak variant",
          "Classical Boolean semantics for the connectives"],
         [PNUELI1977, EMERSON1990, HUGHES1996, BLACKBURN2001, BAIER2008],
         ["temporal_logic"],
         functionals=[NEXT_FN, MEET_FN, NEG_FN],
         failure_modes=[
             "Fails for ALWAYS over join and for EVENTUALLY over meet, and the "
             "failure is the interesting direction: F(p and q) is strictly "
             "stronger than F p and F q, because the two need not happen at the "
             "same moment. Pattern-matching this law onto the other modalities "
             "is the standard error.",
             "Fails in branching time for the path-quantified next unless the "
             "quantifier is fixed: EX(p and q) is not EX p and EX q, since the "
             "witnesses may be different successors.",
             "Over finite traces the last position has no successor and the "
             "weak/strong split reappears; the law survives for one variant and "
             "not the other."],
         inferential_links=links(
             entails=["temporal.induction.temporal_induction_axiom"],
             composed_with=["temporal.recurrence.until_unfolding",
                            "temporal.modality.eventually_unfolding",
                            "morphology.semantics.compositionality",
                            "morphology.quantity.morpheme_count_additivity"]),
         keywords=["next", "distributivity", "homomorphism", "K axiom",
                   "endomorphism", "modal logic"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.modality.always_idempotence",
         "Idempotence of Always",
         "identity", "derived", "linear_temporal_logic", "modal_idempotence",
         "always(always(p)) = always(p)",
         "\\Box\\Box p \\equiv \\Box p",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "GG p ≡ G p"},
          {"form_id": "dual", "notation_system": "ascii",
           "expression": "eventually(eventually(p)) = eventually(p)",
           "scope_note": "The dual, obtained through temporal.modality.temporal_duality"},
          {"form_id": "axiom_four", "notation_system": "ascii",
           "expression": "always(p) implies always(always(p))",
           "scope_note": "Axiom 4 of modal logic S4; the converse is axiom T, and LTL validates both because the suffix relation is a reflexive transitive order"},
          {"form_id": "closure", "notation_system": "ascii",
           "expression": "ALWAYS is an interior operator: deflationary, monotone and idempotent",
           "scope_note": "The topological reading; EVENTUALLY is the matching closure operator"}],
         "idempotent_operation",
         "ALWAYS(ALWAYS(PROP)) = ALWAYS(PROP)",
         [slot("PROP", "variable", "temporal_proposition")],
         ["One free operand, one head, applied once on one side and twice on "
          "the other: the law says something about the operator alone.",
          "Idempotence, not involution, and the difference is what blocks the "
          "match with logic.boolean_laws.double_negation. NEG applied twice "
          "returns the *bare operand* (`?0 = NEG⟨NEG⟨?0⟩⟩`), while ALWAYS "
          "applied twice returns `ALWAYS⟨?0⟩`. The idempotent has a fixed point "
          "the involution lacks, the two sides differ in depth, and no "
          "equality-based grouping can relate the two shapes.",
          "Equivalent to reflexivity plus transitivity of the suffix relation: "
          "axiom T gives one inclusion and axiom 4 the other, so LTL's frame "
          "condition is exactly what makes this an equality rather than an "
          "implication.",
          "Fifth member of docs/BACKLOG.md's recorded 'slot recurrence, not "
          "slot shape' family (Brouwer fixed point, double negation, set "
          "idempotence, FTC part 1) and the first that is an idempotent "
          "modality rather than an idempotent operation on elements.",
          "The archetype_id `idempotent_operation` is adopted from "
          "logic.boolean_laws.idempotence and "
          "settheory.boolean_laws.idempotence deliberately; the label is right "
          "and the skeletons are three."],
         PROP_SYMS[:1], [LTL_EQUIV, BOX, DIAMOND],
         "Requiring that a property always hold, always, asks for nothing "
         "beyond requiring that it always hold: the modality saturates after "
         "one application.",
         "Predicted to miss logic.boolean_laws.idempotence and it does, at "
         "every level -- `ALWAYS⟨?0:V⟩ = ALWAYS⟨ALWAYS⟨?0:V⟩⟩` against "
         "`?0:V = MEET⟨?0:V, ?0:V⟩`. Two independent blockers again: the head, "
         "and the arity (MEET is binary with a repeated operand, ALWAYS is "
         "unary and nested). Its nearer miss is double negation, and the "
         "analysis of *why* that one also fails is the node's contribution: "
         "involution and idempotence differ by exactly whether the operator has "
         "a fixed point, which is a property of the skeleton rather than a "
         "shape of it -- the structural-query facility docs/BACKLOG.md asks "
         "for. The archetype channel carries what the skeleton channel cannot.",
         ["Reflexive and transitive suffix relation, which linear time supplies "
          "automatically",
          "Infinite traces",
          "Both directions valid: the S4 axioms T and 4 together"],
         [PNUELI1977, HUGHES1996, BLACKBURN2001, KRIPKE1963, EMERSON1990],
         ["temporal_logic"],
         functionals=[ALWAYS_FN, EVENTUALLY_FN],
         failure_modes=[
             "Fails for the mixed modalities: GF p (infinitely often) and FG p "
             "(eventually forever) are genuinely different properties, and "
             "GFGF p = GF p while FGFG p = FG p -- the collapse is only within "
             "a single modality, and the fairness hierarchy lives in the mixed "
             "ones.",
             "Fails in modal logics whose accessibility relation is not "
             "transitive; axiom 4 is precisely the transitivity condition, so "
             "the law is a frame property masquerading as an algebraic one.",
             "Fails for the temporal-past mirror in logics with both directions "
             "unless the past relation is also transitive."],
         inferential_links=links(
             entailed_by=["temporal.induction.temporal_induction_axiom"],
             composed_with=["temporal.modality.temporal_duality",
                            "temporal.monotonicity.eventually_monotonicity",
                            "logic.boolean_laws.idempotence",
                            "logic.boolean_laws.double_negation"]),
         keywords=["idempotence", "always", "S4", "axiom 4", "interior operator",
                   "fixed point"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.induction.temporal_induction_axiom",
         "Temporal Induction",
         "axiom", "formal", "linear_temporal_logic", "induction",
         "always(p implies next(p)) implies (p implies always(p))",
         "\\Box(p \\to \\mathrm{X}p) \\to (p \\to \\Box p)",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "G(p → Xp) → (p → Gp)"},
          {"form_id": "rule", "notation_system": "ascii",
           "expression": "from |- p implies next(p), infer |- p implies always(p)",
           "scope_note": "The induction rule; the axiom internalizes it, exactly as the deduction theorem relates a rule to an implication"},
          {"form_id": "invariance", "notation_system": "ascii",
           "expression": "an inductive invariant is a p closed under the transition relation and true initially",
           "scope_note": "The engineering reading: this axiom is what licenses proving a safety property by exhibiting an invariant, which is how every model checker discharges G"},
          {"form_id": "arithmetic", "notation_system": "ascii",
           "expression": "(P(0) and forall n. (P(n) implies P(n+1))) implies forall n. P(n)",
           "scope_note": "Peano induction; positions of a trace are the naturals and NEXT is the successor, so this is the same principle over a different index"}],
         "temporal_induction",
         "IMPLIES(ALWAYS(IMPLIES(PROP, NEXT(PROP))), IMPLIES(PROP, ALWAYS(PROP)))",
         [slot("PROP", "variable", "temporal_proposition")],
         ["One free operand occurring four times at three different depths: the "
          "whole content is the reuse, exactly as in "
          "settheory.order.subset_transitivity where the middle element's two "
          "occurrences are the law.",
          "The only node in this corpus whose root IMPLIES is meta-level (a "
          "rule) and whose inner IMPLIES is object-level (a formula). "
          "scripts/seed_logic.py's IMPLIES head is documented as carrying both "
          "readings, so the ambiguity is inherited rather than introduced, but "
          "the matcher cannot tell the two apart and would happily group a rule "
          "with a formula.",
          "Not reversible and not an equation, which places it structurally "
          "with logic.inference.modus_ponens rather than with the expansion "
          "laws.",
          "The step hypothesis is guarded by ALWAYS, so the premise must hold at "
          "every position, not merely at the first. Dropping the ALWAYS gives a "
          "statement that is false on any trace where p becomes true late.",
          "Peano induction over the positions of the trace, with NEXT as "
          "successor. The corpus carries no arithmetic induction node, so this "
          "is currently a singleton whose obvious twin does not exist yet."],
         PROP_SYMS[:1], [IMPL, BOX, CIRCLE, ENTAILS],
         "If a property is preserved by every single step, then holding it once "
         "is enough to hold it forever after.",
         "The bridge between the corpus's temporal vocabulary and the way "
         "safety properties are actually proved: not by inspecting the infinite "
         "future but by exhibiting a one-step invariant. Structurally it is a "
         "singleton at every level, and the reason is worth recording because "
         "it is a corpus gap rather than a tool limit -- the graph carries no "
         "node for mathematical induction over the naturals, so the statement "
         "this one is an instance of is simply absent. Compare the recorded "
         "case where two twin groups were blocked by one missing statistics "
         "node: the cheapest connectivity fix for this node is authoring "
         "arithmetic induction somewhere in the graph, in this template.",
         ["Well-founded, discrete time: positions are order-isomorphic to the "
          "naturals, so there is no limit position at which the step hypothesis "
          "could fail to reach",
          "The step hypothesis must hold at every position, not just where p "
          "does",
          "Infinite traces"],
         [MANNA_PNUELI, PNUELI1977, LAMPORT1977, CLARKE1999, BAIER2008],
         ["temporal_logic"],
         functionals=[ALWAYS_FN, NEXT_FN, IMPLIES_FN],
         failure_modes=[
             "Fails over dense or continuous time: with no immediate successor "
             "there is no step for the hypothesis to be about, which is why "
             "real-time logics replace induction with well-founded ranking "
             "arguments.",
             "The invariant one starts with is usually too weak to be "
             "inductive, and strengthening it is undecidable in general; this "
             "is the practical content of the axiom and the reason invariant "
             "generation is a research area rather than a step.",
             "It licenses nothing about liveness: no amount of one-step "
             "reasoning establishes an EVENTUALLY, which needs a well-founded "
             "measure instead."],
         inferential_links=links(
             entails=["temporal.modality.always_idempotence"],
             entailed_by=["temporal.modality.next_distributes_over_meet"],
             composed_with=["temporal.order.precedence_transitivity",
                            "logic.inference.modus_ponens"]),
         keywords=["induction", "invariant", "safety", "always", "next",
                   "model checking"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.order.precedence_transitivity",
         "Transitivity of Temporal Precedence",
         "theorem", "derived", "event_order", "precedence_order",
         "if (a no-later-than b) and (b no-later-than c) then (a no-later-than c)",
         "a \\preceq b \\ \\land\\ b \\preceq c \\implies a \\preceq c",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "(a ⪯ b) ∧ (b ⪯ c) → (a ⪯ c)"},
          {"form_id": "timestamps", "notation_system": "ascii",
           "expression": "(t(a) <= t(b)) and (t(b) <= t(c)) implies (t(a) <= t(c))",
           "scope_note": "Unfolded through an occurrence-time map; transitivity of precedence is transitivity of <= on the reals pulled back along t"},
          {"form_id": "happens_before", "notation_system": "ascii",
           "expression": "Lamport's happens-before is the smallest transitive relation containing program order and message order",
           "scope_note": "The distributed-systems reading: transitivity is not a theorem there but the closure condition that defines the relation"},
          {"form_id": "lattice", "notation_system": "ascii",
           "expression": "(a meet b = a) and (b meet c = b) implies (a meet c = a)",
           "scope_note": "Precedence expressed through meet, which is how LEQ is defined in the template"}],
         "order_transitivity",
         "IMPLIES(MEET(LEQ(EVENTA, EVENTB), LEQ(EVENTB, EVENTC)), LEQ(EVENTA, EVENTC))",
         [slot("EVENTA", "variable", "event_operand"),
          slot("EVENTB", "variable", "event_operand"),
          slot("EVENTC", "variable", "event_operand")],
         ["The middle event appears twice, once as the consequent of the first "
          "premise and once as the antecedent of the second: transitivity is "
          "the chaining pattern and the repeated slot is the whole content.",
          "The template is scripts/seed_logic.py's TPL_SUBSET_TRANSITIVITY "
          "verbatim with only slot names changed -- the same move "
          "scripts/seed_topology.py made for "
          "geotop.predicates.containment_transitivity. The three-way twin "
          "therefore holds by construction and cannot drift.",
          "LEQ is the REFLEXIVE order 'occurs no later than'. Strict precedence "
          "is not a partial order in the lattice sense (it is irreflexive), and "
          "the corpus keeps the two apart: strictness lives in "
          "temporal.order.strict_precedence_asymmetry, whose BEFORE head buys "
          "no twins at all. The pair is the corpus's cheapest measurement of "
          "what adopting an abstract head is worth.",
          "With reflexivity and antisymmetry this makes precedence a partial "
          "order; adding totality makes it the linear order that gives linear "
          "temporal logic its name.",
          "Not an equation and not reversible, which puts it structurally with "
          "logic.inference.modus_ponens rather than with the expansion laws."],
         EVENT_SYMS, [PRECEQ, AND, IMPL],
         "Order chains: if one event is no later than a second and the second "
         "no later than a third, the first is no later than the third.",
         "The flagship prediction of this seeding pass, registered before the "
         "matcher was run and fired exactly: "
         "`IMPLIES⟨MEET⟨LEQ⟨?0:V, ?1:V⟩, LEQ⟨?1:V, ?2:V⟩⟩, LEQ⟨?0:V, ?2:V⟩⟩` now "
         "spans set inclusion, region containment and temporal precedence -- "
         "three disciplines, one theorem about one partial order, no analogy "
         "involved. The claim it supports is narrow and worth stating narrowly: "
         "all three are `authored_to_match` in docs/BACKLOG.md's sense, so this "
         "is a convention that survived three independent corpora without "
         "drifting, not a structure the matcher discovered. What it "
         "demonstrates is that the abstract-head convention scales, which is "
         "the prerequisite for time being visible to the same machinery that "
         "sees sets -- and time being visible is what "
         "docs/DESIGN-frames-and-retrieval.md needs before 'beginning precedes "
         "middle precedes end' can be checked rather than asserted.",
         ["Events identified with the instants at which they occur",
          "Precedence read non-strictly, so the relation is reflexive and is a "
          "genuine partial order",
          "A single timeline: in a partial-order model of concurrency the "
          "relation stays transitive but stops being total"],
         [LAMPORT1978, ALLEN1983, MANNA_PNUELI, PRIOR1957, BAIER2008],
         ["temporal_logic"],
         functionals=[LEQ_FN, MEET_FN, IMPLIES_FN],
         failure_modes=[
             "Strict precedence between simultaneous events is not derivable "
             "from this: a ⪯ b and b ⪯ a is consistent (they coincide), so "
             "inferring 'a before b' from the non-strict relation is the "
             "standard error.",
             "Physical simultaneity is frame-dependent for spacelike-separated "
             "events, so the relation is only a partial order on events in "
             "relativistic settings -- transitivity survives, totality does "
             "not.",
             "Human and narrative time routinely violates totality (flashbacks, "
             "parallel plots), which is why narrative.causality."
             "precedence_causation_bridge uses the strict head instead."],
         inferential_links=links(
             composed_with=["temporal.order.strict_precedence_asymmetry",
                            "temporal.induction.temporal_induction_axiom",
                            "settheory.order.subset_transitivity",
                            "geotop.predicates.containment_transitivity"]),
         keywords=["transitivity", "precedence", "partial order",
                   "happens-before", "event order"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.order.strict_precedence_asymmetry",
         "Asymmetry of Strict Precedence",
         "theorem", "derived", "event_order", "precedence_order",
         "if (a before b) then not (b before a)",
         "a \\prec b \\implies \\lnot (b \\prec a)",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "a ≺ b → ¬(b ≺ a)"},
          {"form_id": "irreflexivity", "notation_system": "ascii",
           "expression": "not (a before a)",
           "scope_note": "The special case a = b; asymmetry implies irreflexivity, and with transitivity the converse also holds"},
          {"form_id": "no_time_travel", "notation_system": "ascii",
           "expression": "the happens-before relation is acyclic",
           "scope_note": "The operational reading: an event cannot be in its own causal past, which is what makes vector clocks and topological sorting of a trace possible"}],
         "strict_order_asymmetry",
         "IMPLIES(LT(EVENTA, EVENTB), NEG(LT(EVENTB, EVENTA)))",
         [slot("EVENTA", "variable", "event_operand"),
          slot("EVENTB", "variable", "event_operand")],
         ["The two operands swap places between premise and conclusion, so the "
          "content is the failure of symmetry -- the exact opposite of "
          "geotop.predicates.adjacency_symmetry, which exists only to assert "
          "that its head IS symmetric. The two nodes are the positive and "
          "negative answers to the same unaskable question, and the graph has "
          "no way to say either except by writing a node.",
          "Authored with the abstract strict-order head LT rather than LEQ, "
          "because asymmetry is false of any reflexive relation. BEFORE is an "
          "honest alias of LT; the former BEFORE-to-LEQ alias asserted a false "
          "identity and has been removed.",
          "Singleton at shape, typed and family level. Its neighbour "
          "temporal.order.precedence_transitivity, written with LEQ, is a "
          "three-discipline typed twin. Same corpus, same author, adjacent "
          "nodes, same subject matter -- the entire difference is which head "
          "the statement could honestly use.",
          "The concrete BEFORE spelling remains in data/narrative, where "
          "narrative.causality.precedence_causation_bridge uses it in the same "
          "reading. Both corpora are authored by scripts/seed_temporal.py, so "
          "the head's argument order (earlier first) is fixed once for both.",
          "Asymmetry plus transitivity makes LT a strict partial order; "
          "the reflexive closure is the LEQ of the adjacent node, and the two "
          "nodes together are the standard strict/non-strict pair."],
         EVENT_SYMS[:2], [PRECEDES, IMPL, NOT],
         "If one event happens strictly before another, the second cannot also "
         "happen strictly before the first: time does not double back.",
         "Authored to measure what the abstract-head convention costs when it "
         "cannot honestly be used. docs/BACKLOG.md argues head literalism from "
         "cross-corpus near misses; this node argues it from an adjacent pair "
         "inside one file, where one statement about the order of events joins "
         "a three-discipline group and the next joins nothing, purely because "
         "the second statement is about strictness and strictness is what LEQ "
         "does not have. It also supplies the corpus's second asymmetry-versus-"
         "symmetry pair (after geospatial adjacency), which is the regression "
         "case for any future declaration that a call head is symmetric: the "
         "declaration must be refusable, not merely absent.",
         ["Events identified with instants, and distinct events with distinct "
          "instants -- simultaneity makes the relation a strict partial order "
          "rather than a strict total one",
          "A single consistent timeline, so the relation is acyclic",
           "Strict reading throughout: LT is irreflexive"],
         [LAMPORT1978, ALLEN1983, PRIOR1957, MANI2010],
         ["temporal_logic"],
         functionals=[LT_FN, NEG_FN, IMPLIES_FN],
         failure_modes=[
             "Cyclic-time models (recurrence in cosmology, modular clocks in "
             "protocols) drop it, and every algorithm that topologically sorts "
             "events breaks with them.",
             "Closed timelike curves in general relativity are the physical "
             "counterexample; the relation stays a preorder but loses "
             "asymmetry.",
             "Narrative discourse order routinely reverses story order "
             "(Genette's analepsis), so the relation must be stated over story "
             "time and not over telling time -- which is a distinction the "
             "template does not carry."],
         inferential_links=links(
             composed_with=["temporal.order.precedence_transitivity",
                            "temporal.order.strict_part_of_order",
                            "narrative.causality.precedence_causation_bridge",
                            "geotop.predicates.adjacency_symmetry"]),
         keywords=["asymmetry", "strict order", "before", "acyclicity",
                   "happens-before", "head literalism"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.monotonicity.eventually_monotonicity",
         "Monotonicity of Eventually",
         "theorem", "derived", "linear_temporal_logic", "operator_monotonicity",
         "if p entails q then eventually(p) entails eventually(q)",
         "p \\vDash q \\implies \\Diamond p \\vDash \\Diamond q",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "(p ⊑ q) → (F p ⊑ F q)"},
          {"form_id": "always", "notation_system": "ascii",
           "expression": "if p entails q then always(p) entails always(q)",
           "scope_note": "Every LTL modality is monotone; the ALWAYS half follows from this one by temporal.modality.temporal_duality"},
          {"form_id": "traces", "notation_system": "ascii",
           "expression": "trace-set inclusion is preserved: if [[p]] subset [[q]] then [[F p]] subset [[F q]]",
           "scope_note": "The semantic form, which is what makes this a statement about an order-preserving map rather than about implication"},
          {"form_id": "fixpoint_precondition", "notation_system": "ascii",
           "expression": "monotonicity of the unfolding functional is the hypothesis of the Knaster-Tarski theorem",
           "scope_note": "Why the node matters: without it the least fixpoint in temporal.recurrence.until_unfolding is not guaranteed to exist"}],
         "order_preserving_modality",
         "IMPLIES(LEQ(PROPA, PROPB), LEQ(EVENTUALLY(PROPA), EVENTUALLY(PROPB)))",
         [slot("PROPA", "variable", "temporal_proposition"),
          slot("PROPB", "variable", "temporal_proposition")],
         ["An order-preservation claim: the same order relation appears in "
          "premise and conclusion, with a functional applied to both sides of "
          "the conclusion. That is the shape "
          "geotop.measure.area_monotonicity introduced, and "
          "docs/BACKLOG.md explicitly asks the next monotone-functional node to "
          "be written with *that* template.",
          "It could not be. area_monotonicity's conclusion is "
          "`CARD(REGA) <= CARD(REGB)`, a NUMERIC comparison, because "
          "cardinality maps a lattice into the numbers. EVENTUALLY maps the "
          "lattice of temporal properties into itself, so its conclusion must "
          "be another LEQ. Writing `CARD` here would have asserted that a "
          "temporal property has a size. The backlog request presumed every "
          "monotone functional is a valuation; monotone ENDO-functions are a "
          "second kind and need a second template.",
          "Consequently the two nodes share no group: "
          "`IMPLIES⟨LEQ⟨?0:V, ?1:V⟩, LEQ⟨EVENTUALLY⟨?0:V⟩, EVENTUALLY⟨?1:V⟩⟩⟩` "
          "against "
          "`IMPLIES⟨LEQ⟨?0:V, ?1:V⟩, CARD⟨?0:V⟩ <= CARD⟨?1:V⟩⟩`. The premises "
          "are identical and the conclusions differ in kind.",
          "LEQ carries its second reading here: over properties it is trace-set "
          "inclusion, i.e. entailment, not the instant order the adjacent "
          "precedence node uses. One head, two readings, both honest, and "
          "nothing in the template records which is meant.",
          "Monotonicity is the hypothesis every fixpoint in this corpus needs, "
          "so the node is load-bearing for temporal.recurrence.until_unfolding "
          "rather than decorative."],
         PROP_SYMS, [ENTAILS, IMPL, DIAMOND, BOX],
         "Weakening what you ask for weakens what you ask to happen eventually: "
         "if every trace satisfying the first property satisfies the second, "
         "the same holds once both are put under 'eventually'.",
         "The corpus's second monotone-functional node, and it records a "
         "refinement of an existing backlog item rather than satisfying it. "
         "docs/BACKLOG.md asked that future monotone statements adopt "
         "geotop.measure.area_monotonicity's template so the family could form; "
         "this one cannot, because that template hard-codes a valuation into "
         "the numbers and EVENTUALLY is an endo-function on the lattice. The "
         "generalization the graph actually wants is "
         "`IMPLIES(LEQ(x, y), LEQ(F(x), F(y)))` with the numeric case as its "
         "specialization along a valuation -- which is a relationship "
         "scripts/specialize.py cannot express either, since `<=` and `LEQ` are "
         "different relation kinds. Recorded so that the third monotone node "
         "does not repeat the choice blindly.",
         ["Entailment read semantically, as inclusion of trace sets",
          "Both properties interpreted over the same trace alphabet",
          "Infinite traces, so EVENTUALLY is total"],
         [BAIER2008, EMERSON1990, TARSKI1955, MANNA_PNUELI, BLACKBURN2001],
         ["temporal_logic"],
         functionals=[EVENTUALLY_FN, LEQ_FN, IMPLIES_FN, ALWAYS_FN],
         failure_modes=[
             "Antitone contexts break it: EVENTUALLY under a negation reverses "
             "the inclusion, so the law must not be applied inside an odd "
             "number of NEGs, which is where hand proofs usually go wrong.",
             "Monotone does not mean continuous: a monotone functional need not "
             "commute with infinite joins, and the fixpoint characterizations "
             "that need continuity (not merely monotonicity) do not follow from "
             "this node.",
             "The converse is false. F p entailing F q says nothing about p "
             "entailing q, since the two may hold at different positions."],
         inferential_links=links(
             composed_with=["temporal.modality.temporal_duality",
                            "temporal.recurrence.until_unfolding",
                            "temporal.modality.always_idempotence",
                            "geotop.measure.area_monotonicity"]),
         keywords=["monotonicity", "order preservation", "eventually",
                   "Knaster-Tarski", "entailment", "trace inclusion"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.response.response_pattern",
         "Response Pattern (Every Trigger Is Eventually Answered)",
         "model_specification", "assumed", "specification_patterns", "liveness",
         "always(trigger implies eventually(response))",
         "\\Box(t \\to \\Diamond r)",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "G(t → F r)"},
          {"form_id": "named", "notation_system": "ascii",
           "expression": "the Response (leads-to) pattern, global scope",
           "scope_note": "Dwyer, Avrunin and Corbett's survey found that response and absence/universality together account for a majority of real specifications"},
          {"form_id": "leadsto", "notation_system": "ascii",
           "expression": "t ~> r",
           "scope_note": "Lamport's leads-to operator, defined as exactly this formula"},
          {"form_id": "instances", "notation_system": "ascii",
           "expression": "every request is eventually served; every lock acquired is eventually released; every planted element is eventually used",
           "scope_note": "The third instance is narrative.constraint.chekhov_gun, which is why this node carries a `generalizes` edge into data/narrative"}],
         "liveness_response_pattern",
         "ALWAYS(IMPLIES(TRIGGER, EVENTUALLY(RESPONSE)))",
         [slot("TRIGGER", "variable", "temporal_proposition"),
          slot("RESPONSE", "variable", "temporal_proposition")],
         ["A bare formula, not an equation: the statement IS the specification, "
          "so there is nothing on the other side of a relation. That has a "
          "mechanical consequence the corpus had not recorded -- "
          "scripts/specialize.py's `find_specializations` skips any pattern "
          "whose canonical tree is not a `rel`, so this node and every "
          "rule-shaped node in the graph can never be the GENERAL side of a "
          "specialization edge.",
          "The strongest liveness pattern that is still monotone in both slots, "
          "which is what makes it usable as a template that other statements "
          "instantiate.",
          "Unbounded: nothing constrains how long the response takes. Bounding "
          "it needs metric time, which this grammar has no way to write.",
          "The two slots are independent, so the pattern says nothing about the "
          "trigger recurring; `always` on the outside is what makes it apply to "
          "every occurrence rather than the first."],
         [sym("t", "variable", "trigger_condition",
              "The condition whose every occurrence must be answered."),
          sym("r", "variable", "response_condition",
              "The condition that must eventually follow each trigger.")],
         [BOX, DIAMOND, IMPL],
         "Whenever the trigger holds, the response must hold at some later "
         "moment -- for every occurrence of the trigger, not merely the first.",
         "Authored so that a narrative law can be a *special case* of a "
         "verified temporal pattern rather than an analogy to one. "
         "narrative.constraint.chekhov_gun is this formula with "
         "TRIGGER := PLANTED(ELEMENT) and RESPONSE := DISCHARGED(ELEMENT), and "
         "the pair is written with reciprocal generalizes / special_case_of "
         "edges because scripts/seed_temporal.py owns both corpora. The "
         "registered prediction was that scripts/specialize.py would confirm "
         "the edge mechanically; it does not, for two stacked reasons -- the "
         "plain-binding suppression docs/BACKLOG.md already records five times, "
         "and, before that even applies, the `rel`-only guard on patterns. So "
         "the most load-bearing edge between these two corpora is hand-asserted, "
         "which is exactly the outcome the backlog predicts.",
         ["Infinite traces, so 'eventually' is not vacuously satisfiable by "
          "termination",
          "Fairness assumptions must be supplied separately: without them a "
          "scheduler may starve the response forever and the specification is "
          "unimplementable rather than violated",
          "Unbounded response time; a deadline needs a metric temporal logic"],
         [DWYER1999, LAMPORT1977, MANNA_PNUELI, PNUELI1977, BAIER2008],
         ["temporal_logic"],
         functionals=[ALWAYS_FN, EVENTUALLY_FN, IMPLIES_FN],
         failure_modes=[
             "Vacuously satisfied when the trigger never occurs, which makes it "
             "a weak specification and a common source of green test suites "
             "that check nothing.",
             "No counterexample is finite: a violation is an infinite trace "
             "where the trigger occurs and the response never does, so bounded "
             "model checking cannot refute it without a lasso.",
             "Says nothing about *which* response answers which trigger; with "
             "repeated triggers a single response satisfies them all, which is "
             "almost never the intent."],
         inferential_links=links(
             generalizes=["narrative.constraint.chekhov_gun",
                          "narrative.frames.cartoon_gravity"],
             composed_with=["temporal.modality.eventually_unfolding",
                            "temporal.modality.always_idempotence"]),
         keywords=RESPONSE_KEYWORDS + ["leads-to", "eventually", "always",
                                        "Chekhov"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.past.since_unfolding",
         "Expansion Law for Since",
         "axiom", "formal", "past_temporal_logic", "fixpoint_expansion",
         "(a since b) = b or (a and previous(a since b))",
         "a \\mathbin{\\mathcal{S}} b \\equiv b \\lor (a \\land \\mathrm{Y}(a \\mathbin{\\mathcal{S}} b))",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "a S b ≡ b ∨ (a ∧ Y(a S b))",
           "scope_note": "The standard past-time unfolding"}],
         "fixpoint_expansion_law",
         "SINCE(PROPA, PROPB) = JOIN(PROPB, MEET(PROPA, PREV(SINCE(PROPA, PROPB))))",
         [slot("PROPA", "variable", "temporal_proposition"),
          slot("PROPB", "variable", "temporal_proposition")],
         ["The defined SINCE head recurs under PREV, so groundedness v2 should "
          "recognize the same recursive-definition structure as UNTIL.",
          "Time reversal maps this statement to until_unfolding but does not "
          "make SINCE and UNTIL interchangeable operations.",
          "The recurrence uses strong PREV, false at the trace origin; weak "
          "previous would make the base case false."],
         PROP_SYMS, [LTL_EQUIV, AND, OR, PREVIOUS, SINCE_OP],
         "A condition has held since an origin exactly when the origin holds "
         "now, or the condition holds now and the same claim held previously.",
         "The recursive past operator that makes premise persistence writable.",
         ["Finite traces with a distinguished origin", "Strong since semantics",
          "Strong PREV is false at the origin"],
         [PRIOR1957, MANNA_PNUELI, EMERSON1990, BAIER2008],
         ["temporal_logic"],
         functionals=[SINCE_FN, PREV_FN, JOIN_FN, MEET_FN],
         inferential_links=links(
             composed_with=["temporal.recurrence.until_unfolding",
                            "temporal.past.once_unfolding"]),
         keywords=["since", "past time", "fixpoint", "recurrence"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.past.past_duality",
         "Past Temporal Duality",
         "identity", "formal", "past_temporal_logic", "modal_duality",
         "historically(p) = not(once(not p))",
         "\\mathrm{H}p \\equiv \\lnot\\mathrm{P}\\lnot p",
         [{"form_id": "dual", "notation_system": "ascii",
           "expression": "once(p) = not(historically(not p))"}],
         "de_morgan_duality",
         "HISTORICALLY(PROP) = NEG(ONCE(NEG(PROP)))",
         [slot("PROP", "variable", "temporal_proposition")],
         ["HISTORICALLY and ONCE are the universal and existential modalities "
          "over the prefix ending now.",
          "The mirror relation to future duality is time reversal, not aliasing."],
         PROP_SYMS[:1], [LTL_EQUIV, NOT, PAST_BOX, PAST_DIAMOND],
         "A property has always held in the past exactly when it has never "
         "failed in the past.",
         "Supplies the past half of temporal De Morgan duality.",
         ["Classical two-valued semantics", "A trace with a fixed origin"],
         [PRIOR1957, MANNA_PNUELI, EMERSON1990], ["temporal_logic"],
         functionals=[HISTORICALLY_FN, ONCE_FN, NEG_FN],
         inferential_links=links(
             composed_with=["temporal.modality.temporal_duality"]),
         keywords=["past duality", "historically", "once", "De Morgan"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.past.prev_distributes_over_meet",
         "Previous Distributes over Meet",
         "theorem", "derived", "past_temporal_logic", "modal_homomorphism",
         "previous(a and b) = previous(a) and previous(b)",
         "\\mathrm{Y}(a \\land b) \\equiv \\mathrm{Y}a \\land \\mathrm{Y}b",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "Y(a ∧ b) ≡ Ya ∧ Yb"}],
         "unary_homomorphism_over_meet",
         "PREV(MEET(PROPA, PROPB)) = MEET(PREV(PROPA), PREV(PROPB))",
         [slot("PROPA", "variable", "temporal_proposition"),
          slot("PROPB", "variable", "temporal_proposition")],
         ["PREV reads both operands at the same preceding position.",
          "At the origin the equation survives under either uniform weak or "
          "strong previous semantics, though PREV is not self-dual there."],
         PROP_SYMS, [LTL_EQUIV, AND, PREVIOUS],
         "Looking back one step after conjoining is the same as looking back "
         "one step for each conjunct.",
         "The time-reversal mirror of NEXT distributing over MEET.",
         ["One consistent convention for PREV at the trace origin"],
         [PRIOR1957, MANNA_PNUELI, EMERSON1990], ["temporal_logic"],
         functionals=[PREV_FN, MEET_FN],
         inferential_links=links(
             composed_with=["temporal.modality.next_distributes_over_meet"]),
         keywords=["previous", "distribution", "meet", "past time"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.past.once_unfolding",
         "Expansion Law for Once",
         "theorem", "derived", "past_temporal_logic", "fixpoint_expansion",
         "once(p) = p or previous(once(p))",
         "\\mathrm{P}p \\equiv p \\lor \\mathrm{Y}\\mathrm{P}p",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "Pp ≡ p ∨ YPp"}],
         "fixpoint_expansion_law",
         "ONCE(PROP) = JOIN(PROP, PREV(ONCE(PROP)))",
         [slot("PROP", "variable", "temporal_proposition")],
         ["ONCE recurs beneath PREV, so the recursive-definition detector has "
          "the same evidence it has for eventually_unfolding.",
          "The base case includes the current position.",
          "PREV is the strong previous operator and is false at the origin."],
         PROP_SYMS[:1], [LTL_EQUIV, OR, PAST_DIAMOND, PREVIOUS],
         "Something has happened once if it happens now or had happened by the "
         "previous position.",
         "Makes finite past search an explicit recurrence.",
         ["Finite prefixes with a distinguished origin",
          "Strong PREV is false at the origin"],
         [PRIOR1957, MANNA_PNUELI, EMERSON1990], ["temporal_logic"],
         functionals=[ONCE_FN, PREV_FN, JOIN_FN],
         inferential_links=links(
             composed_with=["temporal.modality.eventually_unfolding",
                            "temporal.past.since_unfolding"]),
         keywords=["once", "unfolding", "past time", "recurrence"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.response.heraldry_pattern",
         "Inclusive Heraldry Pattern (Every Outcome Has a Herald)",
         "model_specification", "assumed", "specification_patterns",
         "past_response",
         "historically(outcome implies once(herald))",
         "\\mathrm{H}(o \\to \\mathrm{P}h)",
         [{"form_id": "named", "notation_system": "ascii",
           "expression": "every outcome has a herald at or before it"}],
         "liveness_response_pattern",
         "HISTORICALLY(IMPLIES(OUTCOME, ONCE(HERALD)))",
         [slot("OUTCOME", "variable", "temporal_proposition"),
          slot("HERALD", "variable", "temporal_proposition")],
         ["The pattern quantifies over every outcome occurrence and demands a "
          "witness in its inclusive prefix.",
          "It is the past-facing structural mirror of response_pattern, not a "
          "future liveness requirement.",
          "Because ONCE includes the current position, this minimal mirror "
          "does not by itself enforce strict earlier-than ordering."],
         [sym("o", "variable", "outcome_condition", "An observed outcome."),
          sym("h", "variable", "herald_condition", "Its required preparation.")],
         [PAST_BOX, PAST_DIAMOND, IMPL],
         "Whenever an outcome occurs, some herald holds then or occurred "
         "earlier.",
         "The general pattern that makes no-deus-ex-machina an instance rather "
         "than an isolated maxim.",
         ["A trace prefix including the current position",
          "ONCE ranges over positions at or before the current outcome"],
         [MANNA_PNUELI, PRIOR1957, DWYER1999, MANI2010], ["temporal_logic"],
         functionals=[HISTORICALLY_FN, ONCE_FN, IMPLIES_FN],
         inferential_links=links(
             generalizes=["narrative.constraint.no_deus_ex_machina"],
             composed_with=["temporal.response.response_pattern"]),
         keywords=["heraldry", "past response", "preparation", "once"],
         canonical_objects=TEMPORAL_OBJECTS),

    node("temporal.order.strict_part_of_order",
         "Strict Part of a Reflexive Order",
         "identity", "formal", "event_order", "strict_reflexive_bridge",
         "a < b = (a <= b) and not(b <= a)",
         "a < b \\iff (a \\leq b \\land \\lnot(b \\leq a))",
         [{"form_id": "set_order", "notation_system": "ascii",
           "expression": "A proper-subset B iff A subseteq B and not(B subseteq A)"}],
         "strict_part_of_partial_order",
         "LT(EVENTA, EVENTB) = MEET(LEQ(EVENTA, EVENTB), NEG(LEQ(EVENTB, EVENTA)))",
         [slot("EVENTA", "variable", "event_operand"),
          slot("EVENTB", "variable", "event_operand")],
         ["LT is irreflexive because LEQ in both directions is excluded.",
          "The equation relates distinct heads; it does not license substituting "
          "LT for LEQ in asymmetry statements."],
         EVENT_SYMS[:2], [EQ, PRECEDES, PRECEQ, AND, NOT],
         "The strict order consists of the non-strict comparisons whose reverse "
         "comparison does not hold.",
         "Repairs the false BEFORE-to-LEQ alias with an asserted bridge.",
         ["LEQ is antisymmetric and reflexive"],
         [LAMPORT1978, ALLEN1983, MANNA_PNUELI], ["temporal_logic"],
         functionals=[LT_FN, LEQ_FN, MEET_FN, NEG_FN],
         inferential_links=links(
             composed_with=["temporal.order.strict_precedence_asymmetry",
                            "temporal.order.precedence_transitivity"]),
         keywords=["strict order", "partial order", "LT", "LEQ"],
         canonical_objects=TEMPORAL_OBJECTS),
]


# --------------------------------------------------------------------------
# Narrative corpus
# --------------------------------------------------------------------------

NARRATIVE_NODES = [

    node("narrative.structure.story_sequence",
         "Story Structure (Setup, Complication, Resolution)",
         "model_specification", "empirical", "story_grammar", "macrostructure",
         "story = sequence(setup, complication, resolution)",
         "S \\to \\Sigma \\cdot \\Kappa \\cdot \\Rho",
         [{"form_id": "rewrite", "notation_system": "ascii",
           "expression": "Story -> Setting + Episode; Episode -> Event + Reaction",
           "scope_note": "Rumelhart's original rewrite grammar, of which this template is the flattened three-part reduction"},
          {"form_id": "labov", "notation_system": "ascii",
           "expression": "orientation + complicating action + resolution",
           "scope_note": "Labov and Waletzky's clause categories, derived from oral personal narrative rather than from literature; the abstract and the coda are omitted here because they are optional"},
          {"form_id": "freytag", "notation_system": "ascii",
           "expression": "exposition, rising action, climax, falling action, denouement",
           "scope_note": "Freytag's five-part dramatic arc; the three-part form is its coarsening, with climax as the boundary between the second and third parts"},
          {"form_id": "propp", "notation_system": "ascii",
           "expression": "initial situation, villainy/lack, liquidation of the lack",
           "scope_note": "Propp's functions grouped into the same three phases; his claim is that the ORDER is invariant even where functions are absent, which is the content this template encodes"}],
         "ordered_three_part_composition",
         "STORY = SEQUENCE(SETUP, COMPLICATION, RESOLUTION)",
         [slot("STORY", "variable", "whole_story"),
          slot("SETUP", "variable", "story_part"),
          slot("COMPLICATION", "variable", "story_part"),
          slot("RESOLUTION", "variable", "story_part")],
         ["SEQUENCE is a call, so its arguments are ORDERED by the matcher, and "
          "order is the entire empirical claim: Propp's finding is not that "
          "folktales contain these phases but that they contain them in this "
          "sequence. Writing the composition with a commutative operator would "
          "have thrown away the content.",
          "The same reason data/morphology writes CONCAT as a call rather than "
          "reusing MEET -- and, like CONCAT, SEQUENCE gets no algebra from the "
          "matcher: it is associative in every model (a three-part story "
          "grouped either way is the same story) and there is no way to say so, "
          "which is the associativity gap docs/BACKLOG.md records for "
          "morphology.wordformation.concat_associativity.",
          "Ternary rather than nested binary, on purpose. The nested spelling "
          "SEQUENCE(SEQUENCE(SETUP, COMPLICATION), RESOLUTION) would have "
          "matched morphology.wordformation.iterated_affixation's shape modulo "
          "the head, and would have asserted a constituency the story grammars "
          "do not agree on -- Rumelhart brackets setting against episode, "
          "Labov and Waletzky do not bracket at all.",
          "Every part is variable-like, so the typed skeleton "
          "`?0:V = SEQUENCE⟨?1:V, ?2:V, ?3:V⟩` carries no parameter positions: "
          "there is no distinguished constant in a story.",
          "Recursion is real and unrepresented: a complication is routinely "
          "itself a story. The template is flat because the grammar has no way "
          "to declare a slot's admissible kind as the node's own output."],
         [sym("s", "variable", "whole_story",
              "A story: the object the grammar assigns a structure to."),
          sym("x", "variable", "story_part",
              "A story part -- a span of narrated material playing one "
              "structural role.")],
         [EQ, CONCAT_OP],
         "A story is its setup, its complication and its resolution, laid out "
         "in that order.",
         "The node that makes the corpus's thesis testable on stories: a story "
         "grammar is a grammar, so its productions are statements with "
         "templates, slots and failure modes like any other. Structurally it is "
         "a singleton -- SEQUENCE is a ninth head with no relatives -- and the "
         "near miss is worth naming: "
         "morphology.wordformation.iterated_affixation is "
         "`?0:V = CONCAT⟨CONCAT⟨?1:V, ?2:V⟩, ?3:V⟩`, the same ordered "
         "three-way composition spelled with a binary head. One is a story and "
         "one is a word, both are ordered concatenations of three pieces, and "
         "the difference between them is a bracketing decision plus a head "
         "string. Neither the arity nor the head can be changed here without "
         "asserting something the sources do not support, so the miss is "
         "structural rather than authorial.",
         ["Well-formed narrative: the sources are descriptive generalizations "
          "over corpora (Propp's 100 Afanasyev tales, Labov and Waletzky's oral "
          "interviews), not definitions of narrative",
          "Story order, not discourse order: the sequence is the order of "
          "narrated events, and the telling may permute it",
          "One episode. Multi-episode and multi-plot stories iterate the "
          "structure, which this flat template does not express"],
         [PROPP1928, RUMELHART1975, LABOV1967, FREYTAG1863, MANDLER1977],
         ["narrative"],
         functionals=[SEQUENCE_FN],
         failure_modes=[
             "In medias res openings and framed narratives present the parts "
             "out of order, so the claim must be about story time and not "
             "telling time (Genette's order/discourse distinction). Applying it "
             "to the text as read misclassifies most modern fiction.",
             "Unresolved and anti-narrative forms (much modernist short "
             "fiction, some oral genres) simply omit the third part; the "
             "grammar then either over-generates or declares real stories "
             "ill-formed, which is the standard objection to story grammars.",
             "Story grammars were shown in the 1980s to describe recall better "
             "than they describe texts; treating the template as a claim about "
             "texts rather than about readers' schemas overstates it."],
         inferential_links=links(
             composed_with=["narrative.structure.setup_introduction",
                            "narrative.structure.complication_obstruction",
                            "narrative.structure.resolution_outcome",
                            "temporal.order.precedence_transitivity",
                            "morphology.wordformation.iterated_affixation"]),
         keywords=["story grammar", "Propp", "Rumelhart", "narrative structure",
                   "ordered composition", "macrostructure"],
         canonical_objects=NARRATIVE_OBJECTS),

    node("narrative.structure.setup_introduction",
         "Setup as Agent Plus Desire",
         "definition", "empirical", "story_grammar", "story_parts",
         "setup = introduce(agent, desire)",
         "\\Sigma = \\mathrm{intro}(A, D)",
         [{"form_id": "labov", "notation_system": "ascii",
           "expression": "orientation: who, when, where, and in what situation",
           "scope_note": "Labov and Waletzky's orientation clauses; the desire is what distinguishes a setup from a description"},
          {"form_id": "propp", "notation_system": "ascii",
           "expression": "initial situation + the lack that motivates the quest",
           "scope_note": "Propp's functions alpha and a: the family is introduced, then something is missing"},
          {"form_id": "screenwriting", "notation_system": "ascii",
           "expression": "a character who wants something",
           "scope_note": "The standard working formulation; the desire is load-bearing because it is what the complication obstructs"}],
         "binary_composition_definition",
         "SETUP = INTRODUCE(AGENT, DESIRE)",
         [slot("SETUP", "variable", "story_part"),
          slot("AGENT", "variable", "agent_operand"),
          slot("DESIRE", "variable", "goal_operand")],
         ["An agent alone is a description; a desire alone is an abstraction. "
          "The setup is the pair, which is why the head is binary and not two "
          "unary ones.",
          "Argument order is fixed agent-first and is not arbitrary: the desire "
          "is predicated of the agent, so the second slot depends on the first. "
          "The matcher keeps call arguments ordered, so the convention is "
          "enforced rather than merely documented.",
          "The DESIRE slot recurs in "
          "narrative.structure.complication_obstruction and "
          "narrative.structure.resolution_outcome. That shared slot across "
          "three nodes is the real structure of the three-part form -- one "
          "object introduced, obstructed and closed -- and it is invisible to "
          "the matcher, which compares one statement at a time and has no "
          "cross-statement variable.",
          "The archetype_id `binary_composition_definition` is adopted from "
          "morphology.wordformation.affixation deliberately. `word = "
          "CONCAT(stem, suffix)` and `setup = INTRODUCE(agent, desire)` are the "
          "same archetype under different heads, and the drift report is where "
          "the graph says so."],
         [sym("u", "variable", "story_part", "A story part."),
          sym("g", "variable", "goal_operand",
              "A desire: the state of affairs an agent is trying to bring "
              "about.")],
         [EQ],
         "A setup introduces someone and what that someone wants.",
         "First of three story-unit definitions that together triple the count "
         "of nodes carrying `?0 = HEAD⟨?1, ?2⟩` with a private head. "
         "docs/BACKLOG.md records seven such heads across five corpora "
         "(CONCAT, REALIZE, CAPMAX, MEET, UPDATE, MATRIXPOWER, CROSS) with zero "
         "groups between them; INTRODUCE, OBSTRUCT and RESOLVE make ten, and "
         "unlike the earlier seven these three were written in consecutive "
         "lines of one list, by one hand, with identical intent and identical "
         "shape. If any evidence could justify the proposed head-alias level, a "
         "trio that a single author produced in a single sitting and that the "
         "matcher still refuses to group is it. The archetype channel carries "
         "what the skeleton channel will not: all three adopt morphology's "
         "`binary_composition_definition`, so the drift section prints the "
         "four-way spread.",
         ["A protagonist with a goal; agentless narratives (natural-process "
          "accounts, some experimental fiction) fall outside",
          "The desire must be legible to the audience by the end of the setup, "
          "which is a claim about reception, not about the text",
          "One agent per setup; ensemble stories iterate the schema"],
         [PROPP1928, LABOV1967, RUMELHART1975, BREMOND1973, PRINCE1973],
         ["narrative"],
         functionals=[INTRODUCE_FN],
         failure_modes=[
             "Mystery and suspense structures deliberately withhold the desire "
             "until after the complication, inverting the order; the schema "
             "then describes the reader's reconstruction rather than the text.",
             "Character-driven literary fiction often has a desire so diffuse "
             "that the slot cannot be filled, which is the commonest objection "
             "to goal-based story models.",
             "Confusing the agent's desire with the author's theme fills the "
             "slot with something the complication cannot obstruct, and the "
             "three-node chain silently breaks."],
         inferential_links=links(
             composed_with=["narrative.structure.story_sequence",
                            "narrative.structure.complication_obstruction",
                            "narrative.structure.resolution_outcome",
                            "morphology.wordformation.affixation"]),
         keywords=["setup", "orientation", "agent", "desire", "story grammar",
                   "head literalism"],
         canonical_objects=NARRATIVE_OBJECTS),

    node("narrative.structure.complication_obstruction",
         "Complication as Obstructed Desire",
         "definition", "empirical", "story_grammar", "story_parts",
         "complication = obstruct(desire, obstacle)",
         "\\Kappa = \\mathrm{obstruct}(D, O)",
         [{"form_id": "labov", "notation_system": "ascii",
           "expression": "complicating action: the clauses that answer 'and then what happened?'",
           "scope_note": "Labov and Waletzky's central category, the one whose presence they take to define narrative"},
          {"form_id": "propp", "notation_system": "ascii",
           "expression": "villainy: the antagonist causes harm or the hero is dispatched",
           "scope_note": "Propp's function A, the move that starts the tale proper"},
          {"form_id": "bremond", "notation_system": "ascii",
           "expression": "a possibility opens, is actualized or not, succeeds or fails",
           "scope_note": "Bremond's triadic sequence, which makes obstruction a branch point rather than an event"}],
         "binary_composition_definition",
         "COMPLICATION = OBSTRUCT(DESIRE, OBSTACLE)",
         [slot("COMPLICATION", "variable", "story_part"),
          slot("DESIRE", "variable", "goal_operand"),
          slot("OBSTACLE", "variable", "obstacle_operand")],
         ["Argument order is desire-first, and the order carries a "
          "precondition: the desire must already exist for the obstacle to "
          "obstruct it. That dependency is what makes the three story parts "
          "ordered rather than a set, and it is stated here rather than in the "
          "sequence node because it is a fact about this operation.",
          "The obstacle need not be an antagonist. Nature, institutions, and "
          "the agent's own contradictions fill the slot, which is why the head "
          "takes the obstacle as an operand rather than presupposing a "
          "character.",
          "Same shape as narrative.structure.setup_introduction and "
          "narrative.structure.resolution_outcome and no twin with either: "
          "`?0:V = OBSTRUCT⟨?1:V, ?2:V⟩` versus "
          "`?0:V = INTRODUCE⟨?1:V, ?2:V⟩` versus "
          "`?0:V = RESOLVE⟨?1:V, ?2:V⟩`. One token apart, three times over, in "
          "one file.",
          "Adopts `binary_composition_definition` for the same reason its two "
          "siblings do."],
         [sym("u", "variable", "story_part", "A story part."),
          sym("o", "variable", "obstacle_operand",
              "An obstacle: whatever stands between the agent and the desire.")],
         [EQ],
         "A complication is what happens when something stands in the way of "
         "what the agent wants.",
         "Second of the three story-unit definitions. Its own contribution "
         "beyond the head-literalism measurement is the DESIRE slot it shares "
         "with the setup and the resolution: the three nodes are chained "
         "through one object, and the chain is exactly the 'each proposal "
         "becomes the next step's premise' composition that "
         "docs/DESIGN-frames-and-retrieval.md names as the hard remaining gap. "
         "The corpus can state the three links; it has no way to state that "
         "they share a binding, because slot identity is local to a statement. "
         "Any chained-composition work will need a cross-statement binding "
         "notion, and this trio is the smallest test case for one.",
         ["A desire established earlier, which the obstacle acts against",
          "The obstruction must be consequential: an obstacle overcome without "
          "cost is not a complication, which is a judgment the template cannot "
          "encode",
          "One complication per episode; nested and serial complications "
          "iterate the schema"],
         [LABOV1967, PROPP1928, BREMOND1973, RUMELHART1975, TODOROV1969],
         ["narrative"],
         functionals=[OBSTRUCT_FN],
         failure_modes=[
             "Slice-of-life and lyric forms have no obstruction and are still "
             "read as narratives by most audiences, so the definition marks a "
             "prototype rather than a boundary.",
             "Treating the obstacle as necessarily an antagonist produces the "
             "flattened villain-driven reading that Propp's own material does "
             "not support (his function A covers lack as well as villainy).",
             "An obstacle introduced after the fact to justify a resolution is "
             "the standard failure of plotting, and the template cannot "
             "distinguish it from a planted one -- which is precisely what "
             "narrative.constraint.chekhov_gun exists to catch."],
         inferential_links=links(
             composed_with=["narrative.structure.story_sequence",
                            "narrative.structure.setup_introduction",
                            "narrative.structure.resolution_outcome",
                            "narrative.causality.precedence_causation_bridge"]),
         keywords=["complication", "obstacle", "conflict", "story grammar",
                   "complicating action"],
         canonical_objects=NARRATIVE_OBJECTS),

    node("narrative.structure.resolution_outcome",
         "Resolution as Closed Desire",
         "definition", "empirical", "story_grammar", "story_parts",
         "resolution = resolve(desire, outcome)",
         "\\Rho = \\mathrm{resolve}(D, W)",
         [{"form_id": "labov", "notation_system": "ascii",
           "expression": "resolution: the clauses following the last complicating action",
           "scope_note": "Labov and Waletzky define it positionally, which is why the definition here is by role rather than by content"},
          {"form_id": "propp", "notation_system": "ascii",
           "expression": "liquidation of the lack; the initial misfortune is repaired",
           "scope_note": "Propp's function K, which closes the move opened by function A"},
          {"form_id": "negative", "notation_system": "ascii",
           "expression": "resolve(desire, defeat)",
           "scope_note": "Tragedy fills the outcome slot with the desire's defeat; the slot is an outcome, not a success"}],
         "binary_composition_definition",
         "RESOLUTION = RESOLVE(DESIRE, OUTCOME)",
         [slot("RESOLUTION", "variable", "story_part"),
          slot("DESIRE", "variable", "goal_operand"),
          slot("OUTCOME", "variable", "outcome_operand")],
         ["The outcome slot is neutral between success and defeat. A schema "
          "that only accepted satisfaction would exclude tragedy, which is the "
          "commonest way goal-based story models are made too narrow.",
          "Argument order desire-first, matching "
          "narrative.structure.complication_obstruction, so the two "
          "operations on a desire read the same way.",
          "Closure is about the desire, not about the world: a resolution "
          "settles the question the setup raised, and may leave everything else "
          "open. That is what makes the third slot an outcome rather than a "
          "final state.",
          "Third instance of `?0:V = HEAD⟨?1:V, ?2:V⟩` in this file and the "
          "tenth in the graph, adopting `binary_composition_definition` with "
          "its siblings."],
         [sym("u", "variable", "story_part", "A story part."),
          sym("w", "variable", "outcome_operand",
              "An outcome: how the desire is settled, favourably or not.")],
         [EQ],
         "A resolution settles the desire the story opened with, one way or the "
         "other.",
         "Third of the three story-unit definitions, and the one that shows the "
         "trio is not a redundancy: setup, complication and resolution are "
         "three different operations on one shared object, and only the fact "
         "that the graph cannot express the sharing makes them look "
         "interchangeable. The matcher sees three unrelated binary heads; a "
         "reader sees one desire being introduced, obstructed and closed. That "
         "gap -- structure the author can state in prose and the tooling cannot "
         "see -- is the same gap the chained-composition work in "
         "docs/DESIGN-frames-and-retrieval.md has to close, and it appears here "
         "in its smallest form.",
         ["A desire established earlier and obstructed in between",
          "Closure judged relative to the desire, not to the story world",
          "One resolution per episode"],
         [LABOV1967, PROPP1928, RUMELHART1975, BREMOND1973, GENETTE1980],
         ["narrative"],
         functionals=[RESOLVE_FN],
         failure_modes=[
             "Deus ex machina fills the outcome slot with something the story "
             "never planted; the template accepts it, and only "
             "narrative.constraint.chekhov_gun's converse reading rules it out.",
             "Serial and open-ended forms defer resolution indefinitely by "
             "design, so the schema describes the episode and not the work.",
             "Reading the outcome slot as necessarily favourable turns the "
             "definition into a definition of comedy."],
         inferential_links=links(
             composed_with=["narrative.structure.story_sequence",
                            "narrative.structure.setup_introduction",
                            "narrative.structure.complication_obstruction",
                            "narrative.constraint.chekhov_gun"]),
         keywords=["resolution", "outcome", "closure", "story grammar",
                   "denouement"],
         canonical_objects=NARRATIVE_OBJECTS),

    node("narrative.causality.precedence_causation_bridge",
         "Precedence Plus Enablement Reads as Causation",
         "model_specification", "assumed", "narrative_causality",
         "causal_inference",
         "if (a before b) and (a enables b) then (a causes b)",
         "(a \\prec b) \\land \\mathrm{En}(a,b) \\implies \\mathrm{Ca}(a,b)",
         [{"form_id": "post_hoc", "notation_system": "ascii",
           "expression": "post hoc ergo propter hoc",
           "scope_note": "The fallacy this node states as a LAW -- of narrative, not of the world. Readers do infer causation from succession, and story grammars have to model that"},
          {"form_id": "forster", "notation_system": "ascii",
           "expression": "'The king died and then the queen died' is a story; 'the king died and then the queen died of grief' is a plot",
           "scope_note": "Forster's distinction: plot is precedence plus a stated enablement, which is exactly the premise conjunction here"},
          {"form_id": "causal_network", "notation_system": "ascii",
           "expression": "events on the causal chain from opening to outcome are recalled better and judged more important",
           "scope_note": "Trabasso and van den Broek's empirical result, which is the evidence that this inference is real in readers"}],
         "precedence_to_causation",
         "IMPLIES(MEET(BEFORE(EVENTA, EVENTB), ENABLES(EVENTA, EVENTB)), CAUSES(EVENTA, EVENTB))",
         [slot("EVENTA", "variable", "event_operand"),
          slot("EVENTB", "variable", "event_operand")],
         ["The two-premise detachment shell `IMPLIES⟨MEET⟨_, _⟩, _⟩` now has "
          "five members in the graph -- modus ponens, subset transitivity, "
          "containment transitivity, temporal precedence transitivity and this "
          "node -- and only the three transitivity nodes form a group. The "
          "shell is shared, the slot pattern is not: transitivity chains "
          "(0,1)(1,2) to (0,2) while this conjoins two relations over the SAME "
          "pair and concludes a third over that pair. The difference is "
          "genuine, and it is why the shell alone is not a family.",
          "BEFORE aliases to the strict_order class that "
          "temporal.order.strict_precedence_asymmetry's LT head also joins, "
          "in the same strict reading and the same argument order; since the "
          "LT rename, this narrative node is the only remaining concrete "
          "BEFORE spelling. Both corpora are authored by "
          "scripts/seed_temporal.py, so the sharing is an authoring fact "
          "rather than a coincidence, recorded with reciprocal composed_with "
          "edges.",
          "ENABLES is strictly weaker than CAUSES: it supplies a precondition "
          "without forcing the outcome. Having both heads is what keeps the "
          "node from being the bare fallacy -- precedence alone is not enough, "
          "and the second premise is where the narrative work happens.",
          "Stated as a model_specification and assumed, not derived. It is a "
          "claim about what readers infer, defensible from Trabasso and van den "
          "Broek's recall data, and false as a claim about the world."],
         EVENT_SYMS[:2], [PRECEDES, AND, IMPL],
         "When one story event comes before another and makes it possible, the "
         "audience reads the first as having caused the second.",
         "The bridge that makes data/narrative depend on data/temporal_logic "
         "rather than merely resemble it: narrative causality is defined over "
         "the precedence relation the temporal corpus axiomatizes, using that "
         "corpus's head. Structurally it is a singleton, and the near miss is "
         "instructive -- it wears the same two-premise shell as the "
         "transitivity family and cannot join it, because the shell is a "
         "shape and the family is a slot pattern. Recorded because the shell is "
         "now the graph's most-populated non-family: five nodes, one skeleton "
         "prefix, two groups.",
         ["Story time, not discourse time: the precedence is between events as "
          "they happen, and the telling may reorder them",
          "An enablement the story has made available to the reader; a "
          "connection only the author knows does not license the inference",
          "Read as descriptive of narrative comprehension, not as a valid "
          "inference about events"],
         [TRABASSO1985, BREMOND1973, PROPP1928, MANI2010, SCHANK1977],
         ["narrative"],
         functionals=[BEFORE_FN, ENABLES_FN, CAUSES_FN, MEET_FN, IMPLIES_FN],
         failure_modes=[
             "It is the post hoc fallacy, and stating it as a law of narrative "
             "does not make it a law of anything else. A corpus that used this "
             "node to reason about the world would be wrong in the standard "
             "way.",
             "Deliberate subversion (unreliable narration, red herrings) "
             "exploits the inference precisely because readers make it, so the "
             "law describes a default that competent authors suspend.",
             "Enablement is not transitive in the way precedence is: a enables "
             "b and b enables c does not give a enables c once an intervening "
             "choice is involved, so chaining this node is unsound."],
         inferential_links=links(
             composed_with=["temporal.order.strict_precedence_asymmetry",
                            "temporal.order.precedence_transitivity",
                            "narrative.structure.complication_obstruction",
                            "logic.inference.modus_ponens"]),
         keywords=["causality", "precedence", "post hoc", "plot", "enablement",
                   "causal network"],
         canonical_objects=NARRATIVE_OBJECTS),

    node("narrative.constraint.chekhov_gun",
         "Chekhov's Gun (Every Planted Element Is Discharged)",
         "model_specification", "assumed", "narrative_constraints",
         "narrative_liveness",
         "always(planted(e) implies eventually(discharged(e)))",
         "\\Box(\\mathrm{Pl}(e) \\to \\Diamond\\,\\mathrm{Di}(e))",
         [{"form_id": "chekhov", "notation_system": "ascii",
           "expression": "if in the first act you have hung a pistol on the wall, then in the following one it should be fired; otherwise do not put it there",
           "scope_note": "Chekhov's own formulation, from the 1889 letter to Lazarev"},
          {"form_id": "ltl", "notation_system": "ascii",
           "expression": "G(planted -> F discharged)",
           "scope_note": "The response pattern of temporal.response.response_pattern, instantiated; the maxim IS a liveness specification"},
           {"form_id": "converse", "notation_system": "ascii",
            "expression": "historically(discharged(e) implies once(planted(e)))",
            "scope_note": "The other half is now authored separately as narrative.constraint.no_deus_ex_machina"}],
         "liveness_response_pattern",
         "ALWAYS(IMPLIES(PLANTED(ELEMENT), EVENTUALLY(DISCHARGED(ELEMENT))))",
         [slot("ELEMENT", "variable", "story_element")],
         ["Exactly temporal.response.response_pattern with "
          "TRIGGER := PLANTED(ELEMENT) and RESPONSE := DISCHARGED(ELEMENT). "
          "A dramaturgical maxim from 1889 is a liveness specification in the "
          "sense Pnueli defined in 1977, and the corpus can say so with an "
          "edge rather than an essay.",
          "The single slot recurs under both unary heads, which is the whole "
          "content: it must be the SAME element that is planted and "
          "discharged. A version with two independent slots would be satisfied "
          "by any story in which anything at all happens.",
          "The edge to the general pattern is asserted by hand. "
          "scripts/specialize.py cannot check it for two stacked reasons: its "
          "`find_specializations` skips patterns whose tree is not a relation, "
          "and the response pattern is a bare formula; and even past that "
          "guard, the binding is plain slot-to-subtree, which the "
          "absorption-or-identity filter suppresses. Both are recorded in "
          "docs/BACKLOG.md, the first newly.",
          "A safety-shaped intuition with a liveness formula: authors read it "
          "as 'do not plant what you will not use', which is a prohibition, "
          "while the formula is an obligation. The two differ exactly in "
          "whether a counterexample is finite, and the formula's reading is the "
          "right one -- an unfired gun is only a fault once the story ends."],
         [sym("e", "variable", "story_element",
              "A story element -- an object, a fact, a character trait -- that "
              "the narration has presented to the audience.")],
         [BOX, DIAMOND, IMPL],
         "Anything the story deliberately shows the audience must eventually do "
         "narrative work; nothing is introduced for nothing.",
         "The node that makes 'narrative laws are laws' mechanical rather than "
         "rhetorical. It is not analogous to a temporal specification -- it is "
         "one, instantiated, and carries reciprocal special_case_of / "
         "generalizes edges to temporal.response.response_pattern because "
         "scripts/seed_temporal.py owns both corpora and could write the "
         "reciprocal edge that docs/BACKLOG.md records as unaffordable across "
         "corpora authored separately. Two further things it demonstrates. "
         "First, the constraint is *falsifiable in the corpus's own terms*: a "
         "story that plants an element and never discharges it violates a "
         "formula, not a taste. Second, its most useful half -- the converse "
         "that forbids deus ex machina -- cannot be written at all, because the "
         "grammar has no past modality; the corpus therefore states one "
          "direction of a two-directional law; the past-facing direction now "
          "lives in narrative.constraint.no_deus_ex_machina.",
         ["Finite, completed narratives: over an unfinished story every "
          "obligation is merely outstanding, which is the standard reason "
          "serials evade the constraint",
          "Deliberate planting. Incidental detail is not covered, and the "
          "template cannot distinguish the two -- the distinction is the "
          "author's intent",
          "Read as a compositional norm (a model specification), not as an "
          "empirical generalization about published fiction"],
         [CHEKHOV1889, PROPP1928, DWYER1999, PNUELI1977, MANI2010],
         ["narrative"],
         functionals=[ALWAYS_FN, EVENTUALLY_FN, IMPLIES_FN, PLANTED_FN,
                      DISCHARGED_FN],
         failure_modes=[
             "Red herrings in detective fiction are planted precisely so as not "
             "to be discharged in the expected way, so the genre systematically "
             "violates the letter of the constraint while obeying its spirit "
             "(the herring's discharge is misdirection).",
             "Realist and modernist texts include unmotivated detail on "
             "purpose (Barthes's reality effect); applying the constraint to "
             "them mistakes a norm of well-made plotting for a norm of "
             "fiction.",
             "The formula is vacuously satisfied by a story that plants "
             "nothing, and it says nothing about proportion -- a trivially "
             "discharged element satisfies it as fully as a load-bearing one."],
         inferential_links=links(
             special_case_of=["temporal.response.response_pattern"],
             composed_with=["narrative.structure.setup_introduction",
                            "narrative.structure.resolution_outcome",
                            "narrative.constraint.no_deus_ex_machina",
                            "temporal.modality.eventually_unfolding"]),
         keywords=["Chekhov's gun", "liveness", "response pattern", "planting",
                   "payoff", "narrative constraint"],
         canonical_objects=NARRATIVE_OBJECTS),

    node("narrative.constraint.no_deus_ex_machina",
         "No Deus Ex Machina (Inclusive Herald Condition)",
         "model_specification", "assumed", "narrative_constraints",
         "narrative_heraldry",
         "historically(discharged(e) implies once(planted(e)))",
         "\\mathrm{H}(\\mathrm{Di}(e) \\to \\mathrm{P}\\,\\mathrm{Pl}(e))",
         [{"form_id": "maxim", "notation_system": "ascii",
           "expression": "no resolution may depend on an element the story never prepared"}],
         "liveness_response_pattern",
         "HISTORICALLY(IMPLIES(DISCHARGED(ELEMENT), ONCE(PLANTED(ELEMENT))))",
         [slot("ELEMENT", "variable", "story_element")],
         ["The same element slot recurs in outcome and herald positions; a "
          "different planted object cannot justify the discharge.",
          "This is Chekhov's past-facing converse but not its logical "
          "consequence; a coherent story normally adopts both constraints.",
          "ONCE includes the current position, so strict narrative preparation "
          "still requires the executor's event-order check."],
         [sym("e", "variable", "story_element", "The element used by the plot.")],
         [PAST_BOX, PAST_DIAMOND, IMPL],
         "Anything used to resolve the plot must be presented no later than "
         "the outcome that uses it.",
         "Turns the anti-deus-ex-machina half from an equivalent-form note into "
         "a separately checkable constraint.",
         ["Completed narratives", "Deliberate plot-relevant outcomes"],
         [CHEKHOV1889, PROPP1928, MANI2010, PRIOR1957], ["narrative"],
         functionals=[HISTORICALLY_FN, ONCE_FN, IMPLIES_FN, PLANTED_FN, DISCHARGED_FN],
         failure_modes=[
             "An element planted at the exact discharge position satisfies "
             "this inclusive mirror; strict anti-deus ordering needs PREV(ONCE) "
             "or the executor's event sequence.",
             "Mystery and surprise can conceal a herald from the audience while "
             "still making it available in retrospect.",
             "Coincidence-driven genres may reject the constraint deliberately."],
         inferential_links=links(
             special_case_of=["temporal.response.heraldry_pattern"],
             composed_with=["narrative.constraint.chekhov_gun"]),
         keywords=["deus ex machina", "heraldry", "setup", "payoff", "once"],
         canonical_objects=NARRATIVE_OBJECTS),

    node("narrative.frames.cartoon_gravity",
         "Cartoon Gravity Frame Declaration",
         "model_specification", "assumed", "fictional_frames",
         "cartoon_physics",
         "a body falls eventually after noticing it is unsupported",
         "\\Box(\\mathrm{notices}(b) \\to \\Diamond\\,\\mathrm{falls}(b))",
         [{"form_id": "cartoon_rule", "notation_system": "ascii",
           "expression": "once a body notices it is unsupported, it eventually falls"}],
         "liveness_response_pattern",
         "ALWAYS(IMPLIES(NOTICES(BODY), EVENTUALLY(FALLS(BODY))))",
         [slot("BODY", "variable", "story_body")],
         ["The declaration instantiates the same response shape as Chekhov's "
          "gun while remaining explicitly local to one fictional frame.",
          "The frame suspends exactly the cited ordinary-world gravity node."],
         [sym("b", "variable", "story_body", "An unsupported cartoon body.")],
         [BOX, DIAMOND, IMPL],
         "Inside this cartoon, awareness rather than loss of support triggers "
         "the fall.",
         "The first corpus declaration whose epistemic force is explicitly "
         "frame-local rather than world-global.",
         ["The cartoon-gravity frame is open"],
         [MANI2010, RYAN1991, WALTON1990], ["narrative"],
         functionals=[ALWAYS_FN, EVENTUALLY_FN, IMPLIES_FN, NOTICES_FN, FALLS_FN],
         inferential_links=links(
             special_case_of=["temporal.response.response_pattern"],
             composed_with=["narrative.frame.frame_consistency"]),
         keywords=["cartoon gravity", "fictional frame", "suspension"],
         canonical_objects=NARRATIVE_OBJECTS,
         scope={
             "frame": "narrative.frames.cartoon_gravity",
             "role": "declaration",
             "frame_title": "Cartoon gravity",
             "premises": [{
                 "premise_id": "noticed_fall",
                 "expression": "ALWAYS(IMPLIES(NOTICES(BODY), EVENTUALLY(FALLS(BODY))))",
             }],
             "suspends": ["physics.gravitation.newton_universal_gravitation"],
             "governed_by": ["narrative.frame.frame_consistency"],
             "on_exit": "conjectured",
             "retrieval": "frame_local",
         }),

    node("narrative.frames.cartoon_gravity_hover",
         "Cartoon Gravity Frame Assertion",
         "proposition", "assumed", "fictional_frames", "cartoon_physics",
         "if the body has not noticed, it does not fall",
         "\\lnot\\mathrm{notices}(b) \\to \\lnot\\mathrm{falls}(b)",
         [{"form_id": "gag", "notation_system": "ascii",
           "expression": "the coyote may stand in mid-air until looking down"}],
         "frame_local_assertion",
         "IMPLIES(NEG(NOTICES(BODY)), NEG(FALLS(BODY)))",
         [slot("BODY", "variable", "story_body")],
         ["The assertion is licensed only inside the frame that suspends the "
          "ordinary gravity node.",
          "Outside that frame it demotes to conjectured rather than becoming a "
          "claim about physical bodies."],
         [sym("b", "variable", "story_body", "The same cartoon body.")],
         [IMPL, NOT],
         "Before awareness, the unsupported cartoon body remains aloft.",
         "The assertion half of the first real scope pair and a concrete test "
         "of declaration/assertion agreement metadata.",
         ["The cartoon-gravity frame is open", "The body has not yet noticed"],
         [MANI2010, RYAN1991, WALTON1990], ["narrative"],
         functionals=[IMPLIES_FN, NEG_FN, NOTICES_FN, FALLS_FN],
         failure_modes=["Invalid outside the declared frame."],
         inferential_links=links(
             composed_with=["narrative.frame.frame_consistency"]),
         keywords=["cartoon gravity", "hover", "frame-local assertion"],
         canonical_objects=NARRATIVE_OBJECTS,
         scope={
             "frame": "narrative.frames.cartoon_gravity",
             "role": "assertion",
             "frame_title": "Cartoon gravity",
             "premises": [{
                 "premise_id": "noticed_fall",
                 "expression": "ALWAYS(IMPLIES(NOTICES(BODY), EVENTUALLY(FALLS(BODY))))",
             }],
             "suspends": ["physics.gravitation.newton_universal_gravitation"],
             "governed_by": ["narrative.frame.frame_consistency"],
             "on_exit": "conjectured",
             "retrieval": "frame_local",
         }),

    node("narrative.frame.premise_persistence",
         "Opening-Premise Persistence",
         "axiom", "formal", "fictional_frames", "frame_temporality",
         "an opening premise remains held and has held since the frame opened",
         "\\Box(\\mathrm{holds}(p) \\land (\\mathrm{holds}(p)\\,\\mathcal{S}\\,o))",
         [{"form_id": "session", "notation_system": "ascii",
           "expression": "premises declared at frame opening remain available until frame exit"}],
         "frame_premise_persistence",
         "ALWAYS(MEET(HOLDS(PREMISE), SINCE(HOLDS(PREMISE), FRAMEOPENING)))",
         [slot("PREMISE", "variable", "frame_premise"),
          slot("FRAMEOPENING", "constant", "frame_opening_event")],
         ["The same premise recurs on both sides and SINCE anchors it to the "
          "frame-opening event.",
          "The outer MEET keeps HOLDS(PREMISE) positive, so removal violates "
          "the law instead of making an implication vacuously true.",
          "Scope metadata supplies the boundary that the temporal template "
          "alone cannot identify."],
         [sym("p", "variable", "frame_premise", "A declared local premise."),
          sym("o", "constant", "frame_opening_event", "The scope boundary.")],
         [BOX, AND, SINCE_OP],
         "A premise declared when the frame opens remains available from that "
         "boundary through the current state.",
         "Connects mutable session state to the past-time corpus explicitly.",
         ["One open frame with a distinguished opening event",
          "PREMISE is an opening declaration, not a later assertion"],
         [RYAN1991, LEWIS1978, PRIOR1957, MANNA_PNUELI], ["narrative"],
         functionals=[ALWAYS_FN, MEET_FN, HOLDS_FN, SINCE_FN],
         inferential_links=links(
             composed_with=["temporal.past.since_unfolding",
                            "narrative.frame.frame_consistency"]),
         keywords=["frame premise", "persistence", "since", "session state"],
         canonical_objects=NARRATIVE_OBJECTS,
         scope={
             "frame": "narrative.frame.premise_persistence",
             "role": "declaration",
             "frame_title": "Premise persistence",
             "premises": [{
                 "premise_id": "frame_open",
                 "expression": "HOLDS(PREMISE)",
             }],
             "suspends": [],
             "governed_by": ["narrative.frame.frame_consistency"],
             "on_exit": "conjectured",
             "retrieval": "frame_local",
         }),

    node("narrative.frame.frame_consistency",
         "Frame Consistency (A Story May Not Contradict Its Own Premises)",
         "axiom", "formal", "fictional_frames", "frame_logic",
         "premise and (not premise) = inconsistency",
         "\\varphi \\land \\lnot\\varphi \\equiv \\bot",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "φ ∧ ¬φ ≡ ⊥"},
          {"form_id": "scoped", "notation_system": "ascii",
           "expression": "within frame F: if F declares phi, then any later assertion of not-phi derives bottom against F",
           "scope_note": "The reading the node is FOR; the scope quantifier 'within frame F' is exactly what the grammar cannot express, so it lives in regularity_conditions"},
          {"form_id": "ladder", "notation_system": "ascii",
           "expression": "frame premises occupy the frame's VERIFIED tier; a contradicting assertion is REFUTED-against-the-story",
           "scope_note": "docs/DESIGN-epistemic-ladder.md's rungs applied to a local corpus, per docs/DESIGN-frames-and-retrieval.md"},
          {"form_id": "possible_worlds", "notation_system": "ascii",
           "expression": "a fiction picks out a set of worlds; an inconsistent fiction picks out none",
           "scope_note": "Lewis's and Dolezel's account; the empty set of worlds is the bottom element, which is why the constant slot is the right home for it"}],
         "complement_annihilation",
         "MEET(FRAMEPREMISE, NEG(FRAMEPREMISE)) = INCONSISTENCY",
         [slot("FRAMEPREMISE", "variable", "frame_premise"),
          slot("INCONSISTENCY", "constant", "bottom_element")],
         ["Authored with MEET, NEG and a constant-category result slot on "
          "purpose, so that the skeleton is "
          "logic.boolean_laws.complement_laws's character for character. "
          "docs/BACKLOG.md's `authored_to_match` versus `emergent` "
          "distinction applies and the answer is authored: an author who wrote "
          "`CONTRADICTS(assertion, premise)` would have produced a singleton "
          "and an equally true statement.",
          "INCONSISTENCY is declared `constant`, hence parameter-like, which is "
          "what puts it in the same result position that FALSITY and EMPTYSET "
          "occupy. The category, not the shape, is what completes the match.",
          "What the template cannot say is the part that makes this a FRAME "
          "law: the scope. 'Within a frame' is a quantifier over a local "
          "corpus, the grammar has no binder and no scope construct, and so the "
          "entire distinguishing content sits in regularity_conditions as "
          "prose. Same family of loss as the missing quantifiers "
          "docs/BACKLOG.md records for differential topology, and the first "
          "time it has cost the corpus a *design document's* central "
          "mechanism.",
          "Nothing here is special to fiction, which is the finding. The law "
          "governing what a made-up world may assert is the postulate that "
          "makes a lattice Boolean, and the matcher cannot tell them apart.",
          "The reciprocal `equivalent_to` edge to the two Boolean nodes is NOT "
          "written: it would require editing scripts/seed_logic.py and "
          "regenerating two corpora on this branch, the cross-corpus "
          "reciprocity cost docs/BACKLOG.md prices in edits per edge. A "
          "one-sided composed_with is written instead."],
         [sym("phi", "variable", "frame_premise",
              "A premise declared by the fictional frame -- a proposition that "
              "is true in the story world by stipulation.")],
         [EQ, AND, NOT],
         "Inside a story's own frame, a premise and its denial cannot both "
         "hold: asserting both empties the set of worlds the story picks out.",
         "The second flagship prediction, and it fires: "
         "`?0:P = MEET⟨?1:V, NEG⟨?1:V⟩⟩` now spans "
         "logic.boolean_laws.complement_laws, "
         "settheory.boolean_laws.complement_laws and this node. Fiction obeys "
         "logic, and the matcher demonstrates it by being unable to tell which "
         "of the three is about made-up worlds. That is the intended reading of "
         "docs/DESIGN-frames-and-retrieval.md -- inside a frame 'the epistemic "
         "ladder operates unchanged over a LOCAL corpus', and chapter three's "
         "silver chicken is 'flagged exactly as a false physics claim would "
         "be'. The design document asserts it; this node makes the graph agree. "
         "The honest limit is equally important: the twin fires on the "
         "*Boolean* content, and the frame content -- locality of scope, "
         "premises reverting to CONJECTURED-under-premise on scope exit -- is "
         "invisible to the matcher, because the grammar has no scope construct. "
         "So the corpus can now check the consistency law and cannot yet check "
         "the boundary that makes it a frame law rather than a logic law.",
         ["A declared frame with an explicit premise set, which extends the "
          "corpus locally per docs/DESIGN-frames-and-retrieval.md",
          "The premise and its denial evaluated in the SAME frame; comparing "
          "assertions across frames is not a contradiction, and the template "
          "cannot mark which frame it is in",
          "Classical two-valued semantics inside the frame, which is a "
          "stipulation about the story world and not a fact about it",
          "Frame truths do not leak: on scope exit the premises revert to "
          "conjectured-under-premise, a boundary the template cannot express"],
         [RYAN1991, LEWIS1978, DOLEZEL1998, WALTON1990, COLERIDGE1817],
         ["narrative"],
         functionals=[MEET_FN, NEG_FN],
         constants=[INCONSISTENCY_CONST],
         failure_modes=[
             "Impossible fictions are a real genre: time-travel paradoxes and "
             "Escher-style worlds assert inconsistent premises deliberately, "
             "and readers accept them locally rather than deriving everything. "
             "A frame checker that applied explosion would reject work that "
             "audiences read successfully, which argues for a paraconsistent "
             "frame logic and against this node as the last word.",
             "Real fictions are incomplete rather than inconsistent: most "
             "questions about a story world have no answer, so the frame's "
             "local corpus is partial and the absence of a premise must not be "
             "read as its denial.",
             "Retconning is a deliberate frame edit, not a contradiction; "
             "without a notion of frame VERSION the law flags every revised "
             "canon as inconsistent."],
         inferential_links=links(
             composed_with=["narrative.constraint.chekhov_gun",
                            "narrative.structure.story_sequence",
                            "logic.boolean_laws.complement_laws",
                            "settheory.boolean_laws.complement_laws",
                            "logic.inference.reductio_ad_absurdum"]),
         keywords=["fictional frame", "consistency", "possible worlds",
                   "complement law", "epistemic ladder", "suspension of disbelief"],
         canonical_objects=NARRATIVE_OBJECTS),
]


CORPORA = [
    ("temporal_logic", "temporal_logic.linear_time.v1", TEMPORAL_NODES),
    ("narrative", "narrative.story_grammar.v1", NARRATIVE_NODES),
]


def main() -> None:
    for directory, corpus_id, nodes in CORPORA:
        corpus = {
            "schema": "../../schema/equation-node.schema.json",
            "corpus_id": corpus_id,
            "discipline": directory,
            "version": "1.0.0-alpha",
            "statement_nodes": nodes,
        }
        out = Path("data") / directory / "nodes.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print(f"wrote {len(nodes)} {directory} nodes -> {out}")


if __name__ == "__main__":
    main()
