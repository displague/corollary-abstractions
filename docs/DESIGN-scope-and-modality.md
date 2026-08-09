# Design: scope, past modality, and strict order

Four schema/matcher gaps, filed separately in `docs/BACKLOG.md`, that turn out
to be one gap seen from four sides: **the graph can say that two heads are the
same, and it can say nothing else about how two heads are related.** Frames
need "this claim holds relative to that premise set"; the past fragment needs
"this head is the time-mirror of that one"; strict order needs "this head is
the irreflexive part of that one"; and the provenance asymmetry is the same
key name being admissible in one object and not its neighbour.

> **Implementation status (2026-08-08).** This document records the prediction
> and design baseline at 199 nodes. The scope schema and executor have since
> shipped, and the payoff in §4 has landed as ten nodes (the cartoon-gravity
> entry expands to a declaration/assertion pair): 213 nodes total after the
> physics reference-frame first cut, five
> mirror-only groups, and the `LT` strict-order correction. Historical baseline
> measurements below are intentionally retained as the before-state. Review
> caught one error in that baseline: heraldry/no-deus used an outer `ALWAYS`,
> only partially reversing the response law. The implemented past forms use
> `HISTORICALLY`; the matcher reverses the whole tree as one involution.
> Frame identifiers have also graduated from opaque registry-ready strings:
> each now resolves to the scoped declaration node whose `statement_id` owns
> the frame. The former `narrative.frames.premise_persistence` near-collision
> now points to `narrative.frame.premise_persistence` itself.

This was written as a design and draft: at that point nothing here was authored
into `data/`, the live schema was untouched, and the schema change existed only
as `docs/schema-drafts/equation-node.scope-draft.json`.

Everything numbered below was measured against the 199 nodes on this branch,
not estimated.

---

## 1. A scope construct for hypothetical frames

### 1.1 What has to be true of the answer

`docs/DESIGN-frames-and-retrieval.md` §1 asks for four things, and
`docs/BACKLOG.md` records that all four currently live in prose:

1. a frame declares a premise set P1..Pn;
2. inside the frame those premises occupy the **local VERIFIED tier**, so the
   epistemic ladder of `docs/DESIGN-epistemic-ladder.md` runs unchanged over a
   local corpus;
3. a later statement contradicting the frame is REFUTED-against-the-story,
   flagged exactly as a false physics claim would be;
4. frame truths never leak: on scope exit they demote to
   CONJECTURED-under-premise, and the boundary is "structural, not stylistic".

There is a fifth requirement that comes from the corpus rather than the design
document, and it is the one that decides the answer.

### 1.2 The measurement that eliminates the obvious design

`docs/BACKLOG.md` lists three fix shapes "in increasing order of work": a
`scope` field on a node, a `FRAME(premises, claim)` head, or a real scoped
construct in the grammar. The middle option is the one that looks most like
the rest of the system — the corpus already expresses quantification,
optimization and aggregation as opaque call heads — and it is the one that
must not be taken.

`narrative.frame.frame_consistency` is
`MEET(FRAMEPREMISE, NEG(FRAMEPREMISE)) = INCONSISTENCY`, whose typed skeleton
is `?0:P = MEET⟨?1:V, NEG⟨?1:V⟩⟩`, shared with:

    logic.boolean_laws.complement_laws        MEET(PROP1, NEG(PROP1)) = FALSITY
    narrative.frame.frame_consistency         MEET(FRAMEPREMISE, NEG(FRAMEPREMISE)) = INCONSISTENCY
    settheory.boolean_laws.complement_laws    MEET(SETA, NEG(SETA)) = EMPTYSET

Three disciplines, and the only structural bridge in the graph between fiction
and Boolean algebra. Wrapping the claim in a frame head gives

    FRAME(FRAMEID, MEET(FRAMEPREMISE, NEG(FRAMEPREMISE))) = INCONSISTENCY
      ->  ?0:P = FRAME⟨?1:P, MEET⟨?2:V, NEG⟨?2:V⟩⟩⟩      (measured)

which is a singleton at every level. The group drops from three members to
two and loses the narrative one. So:

> **Requirement 5.** The scope must live *beside* the template, never inside
> it. Any construct that enters `anonymized_template` is paid for in twins,
> and the frame node is precisely the node that cannot afford it.

This is not an argument against a grammar-level binder in general — the
wanted `MAX(body, binder, domain)` is still wanted — it is an argument that
*frame membership is metadata about an assertion, not part of the assertion*.
A story's claim that the chicken is golden has the same logical form whether
or not a frame is open around it. That is what makes frames cheap.

### 1.3 The three candidates, honestly

**(A) A top-level optional `scope` object on the node.**

    "scope": {
      "frame": "narrative.frames.cartoon_gravity",
      "role": "assertion",
      "suspends": ["physics.gravitation.newton_universal_gravitation"],
      "governed_by": ["narrative.frame.frame_consistency"],
      "on_exit": "conjectured",
      "retrieval": "frame_local"
    }

*For.* Exactly the `verified_by` precedent: one optional top-level property,
nothing added to `required`, no enum loses a member, so every existing node
stays valid — measured, 199/199 under the draft (§5). The matcher never reads
it, so twin groups are invariant by construction. `on_exit` reuses existing
`epistemic_status` members (`conjectured`, `assumed`), so frames need **no new
epistemic vocabulary at all** — requirement 4 is expressible today.

*Against.* Frame-level facts (`suspends`, `on_exit`, `retrieval`) are
duplicated on every node in the frame, and nothing but a lint keeps them in
agreement. A frame with no nodes yet cannot exist. Nested frames need a
`parent` string with no referential integrity behind it.

**(B) Frames as first-class corpus objects — a `frames/` registry.**

A second schema (`schema/frame.schema.json`), directories `data/*/frames.json`,
and `scope: {"frame": "...", "role": "..."}` on nodes as a *resolvable*
reference.

*For.* Single source of truth for each frame; nesting becomes a real edge;
frames can predate their contents, which the composition loop of
`DESIGN-frames-and-retrieval.md` §3 will need (a chapter opens a frame before
it asserts anything in it); running the ladder frame-locally becomes an
enumeration over a registry entry rather than a scan for a matching string.

*Against.* A second schema, a loader change in `scripts/validate_nodes.py`, a
`check_regeneration.py` story for a file class that currently has none, and a
seed-script convention per corpus. It also inherits every cross-corpus
friction already recorded: a frame in `data/narrative` that suspends a node in
`data/physics` is a cross-corpus reference, and `validate_nodes.py` currently
*fails* rather than warns on unresolved targets, so a frame authored on a
parallel branch cannot name what it suspends.

**(C) Scoped premise references inside `inferential_links`.**

*Against, decisively.* `inferential_links` is an `additionalProperties: false`
object whose six keys are all `required`, and whose semantics are
reciprocity-checked graph edges. Adding a seventh required key is a
**199-node migration** — every node in the corpus, nearly all of which will
never be in a frame. Making it optional inside an all-required object is an
inconsistency of its own. Worse, the semantics are wrong: frame membership is
not an entailment, "reciprocal" has no meaning for it, and there is nowhere to
put `on_exit` or `retrieval`, which are properties of the frame rather than of
any edge. Rejected.

### 1.4 Historical recommendation: (A) now, (B) later

> **Implemented amendment (physics.frames slice).** The first two live frames
> exposed conflicting precedents, so the reserved opaque namespace below was
> not retained. A frame id now resolves to its declaration node: the node's
> `statement_id` equals its own `scope.frame`, and assertions reference that
> declaration. This is still option (A)'s additive node-local representation,
> but it gains referential integrity without option (B)'s second schema. The
> original zero-edit migration claim below is preserved as the prediction that
> was later corrected; one near-collision required migration.

Adopt **(A)**, with `scope.frame` specified from day one as an identifier in a
reserved namespace (`<discipline>.frames.<name>`) rather than free text. Then
the registry, when it lands, is a *validator* upgrade: the string stops being
checked by pattern and starts being resolved against `frames.json`, and
`suspends`/`on_exit`/`retrieval` move off the node into the registry entry as
a deduplication. No node's `scope.frame` value changes. The duplication that
argues against (A) is exactly the pressure that will justify (B), and paying
it first is how we find out whether frames are worth a second schema.

**Migration cost of (A): zero.** No node changes; the field is optional; the
draft accepts all 199 current nodes unmodified (§5).

**Validator implications**, in the order they should be implemented:

1. *Pattern check* on `scope.frame`, and the frame-id pattern allows
   underscores in the first segment. `statement_id`'s pattern forbids them,
   which `docs/BACKLOG.md` records as a defect that forced `settheory.` to
   disagree with `data/set_theory/`; the draft declines to reproduce the bug
   in a new field rather than fixing it in an old one (that is a migration,
   not a draft).
2. *Frame-agreement lint*: all nodes sharing a `scope.frame` must agree on
   `suspends`, `on_exit` and `retrieval`. This lint is the (A)-shaped
   substitute for a registry, and the day it starts failing often is the day
   to build (B).
3. *Reference resolution* for `suspends` and `governed_by`. These must be
   **warn-only**, not fatal — `docs/BACKLOG.md` records that even one-sided
   `composed_with` cannot forward-reference a corpus on a parallel branch, and
   a frame that suspends a physics node is that exact case. This is the
   already-requested `pending`/`external` treatment, and frames are the third
   corpus to want it.
4. *Frame-local ladder run*: for each frame, collect the `role: declaration`
   premises plus the `role: assertion` templates and run the existing pipeline
   over that local set. A contradiction against a declaration is REFUTED; a
   contradiction against a corpus node **not** listed in `suspends` is also
   REFUTED, which is requirement 3 made mechanical.
5. *No matcher change.* `scripts/match_signatures.py` reads
   `structural_signature` only. Verified: no twin group at any level can move.

### 1.5 Worked example, in the corpus's own vocabulary

The frame is cartoon gravity: a body falls only once it notices it is
unsupported. It suspends one real node and nothing else.

Frame declaration node (`role: declaration`):

    scope.frame     narrative.frames.cartoon_gravity
    scope.suspends  ["physics.gravitation.newton_universal_gravitation"]
    scope.on_exit   conjectured
    scope.retrieval frame_local
    template        ALWAYS(IMPLIES(NOTICES(BODY), EVENTUALLY(FALLS(BODY))))
    typed skeleton  ALWAYS⟨IMPLIES⟨NOTICES⟨?0:V⟩, EVENTUALLY⟨FALLS⟨?0:V⟩⟩⟩⟩

Now the payoff of requirement 5. Probed with `scripts/specialize.py`'s matcher:

    temporal.response.response_pattern >= cartoon_fall     True
      binds TRIGGER -> NOTICES⟨?0⟩, RESPONSE -> FALLS⟨?0⟩
    temporal.response.response_pattern >= chekhov_gun      True
      binds TRIGGER -> PLANTED⟨?0⟩, RESPONSE -> DISCHARGED⟨?0⟩

A cartoon's physics is covered by the same LTL liveness pattern that covers
Chekhov's gun, with the same mechanism and the same binding shape. That is
`DESIGN-frames-and-retrieval.md`'s claim — "inside the frame, the epistemic
ladder operates unchanged over a LOCAL corpus" — as a measurement rather than
a promise. It is only available because the scope stayed out of the template.

What `suspends` buys, concretely: an assertion inside this frame that
contradicts `physics.gravitation.newton_universal_gravitation` is *not*
REFUTED, because the frame declared that node out of its local VERIFIED tier.
An assertion contradicting `physics.mechanics.hookes_law`, which the frame did
not suspend, still is. That is the difference between unlimited invention at
the boundary and licence inside it, and it is a list-membership test.

`narrative.frame.frame_consistency` itself stays **unscoped**, deliberately.
It is not a claim inside a frame; it is the law the checker runs, and it is
named by every frame's `governed_by`. The construct therefore promotes that
node from a statement the graph happens to contain into the cited rule of a
checking pass — while leaving its template, and its three-discipline twin,
untouched.

---

## 2. Past modality: PREV / ONCE / SINCE / HISTORICALLY

### 2.1 The template, and it needs nothing

`narrative.constraint.chekhov_gun` states one direction. Its converse — no
unheralded discharge, the anti-deus-ex-machina half, and the half authors
actually care about — is:

    ALWAYS(IMPLIES(DISCHARGED(ELEMENT), ONCE(PLANTED(ELEMENT))))

It parses in the current grammar unchanged, because `ONCE` is an ordinary call
head. Measured:

    typed skeleton  ALWAYS⟨IMPLIES⟨DISCHARGED⟨?0:V⟩, ONCE⟨PLANTED⟨?0:V⟩⟩⟩⟩

No schema change, no grammar change, no `HEAD_ALGEBRA` entry required. The
same holds for `PREV`, `SINCE` and `HISTORICALLY`; none of them collides with
the `sum_ prod_ lim_ max_ min_` big-operator prefix namespace, and none of the
four occurs among the 64 distinct call heads currently in `data/` (checked),
so no existing skeleton can shift under them. **Nothing in
this section touches `docs/schema-drafts/equation-node.scope-draft.json`**, and
nothing here is authored into `data/` — the payoff list is §4.

The node's own `equivalent_forms` already carries this expression, with the
scope note "it needs a PAST modality this corpus does not carry". The corpus
predicted its own next node.

### 2.2 The backlog's prediction, refined

`docs/BACKLOG.md` warns: "Adding one is cheap as a head, but note it will
*not* twin its future dual for the usual reason, so the corpus would gain a
statement and no structure."

At typed and shape level this is exactly right, and now measured. Each of the
five candidate past nodes scores **zero** typed hits and **zero** shape hits
against all 199 current nodes. Head literalism, as advertised.

It is wrong one level down, and the correction is worth more than the
original entry. Declaring the four mirror pairs

    ALWAYS ~ HISTORICALLY      EVENTUALLY ~ ONCE
    NEXT   ~ PREV              UNTIL      ~ SINCE

turns four of the five into exact matches with existing nodes (measured):

| proposed past node | template | lands on |
|---|---|---|
| `once_unfolding` | `ONCE(P) = JOIN(P, PREV(ONCE(P)))` | `temporal.modality.eventually_unfolding` |
| `past_duality` | `HISTORICALLY(P) = NEG(ONCE(NEG(P)))` | `temporal.modality.temporal_duality` |
| `since_unfolding` | `SINCE(A,B) = JOIN(B, MEET(A, PREV(SINCE(A,B))))` | `temporal.recurrence.until_unfolding` |
| `prev_distributes_over_meet` | `PREV(MEET(A,B)) = MEET(PREV(A), PREV(B))` | `temporal.modality.next_distributes_over_meet` |
| `heraldry_pattern` | `ALWAYS(IMPLIES(OUTCOME, ONCE(HERALD)))` | `temporal.response.response_pattern` |

That is five, not four — the response/heraldry pair lands too. And the
declaration is **safe against the existing corpus**: re-running the aliased
level over `data/` with the four mirror classes added produces the *identical*
set of groups with identical membership — 30 multi-member groups at the
aliased level either way, of which one is beyond typed (the `ordered_compose`
pair the report already prints). Nothing existing moves, because no current
pair differs only by a past/future head. The classes are inert until the past
nodes exist.

### 2.3 …but not as an alias class, and this is the design point

`HEAD_ALIASES` means "these two heads name one operation family". `EVENTUALLY`
and `ONCE` do not: one is an existential quantifier over the future, the other
over the past, and `ALWAYS(IMPLIES(P, EVENTUALLY(Q)))` (liveness) and
`ALWAYS(IMPLIES(P, ONCE(Q)))` (heraldry) are genuinely different claims that
an alias would silently pool.

They are images of one another under a declared involution — time reversal.
That is a real relation, it is a theorem of the Manna–Pnueli past fragment,
and it is *not* identity. So:

> Propose `MIRROR_CLASSES` alongside `HEAD_ALIASES`, consumed at its own
> reported level ("mirror twins"), never merged into `aliased`.

The report then says what it means: these two statements are the same
statement read backwards in time. Pooling them into `aliased` would repeat, in
a new place, the mistake §3 is about to find in an existing alias.

### 2.4 Groundedness, predicted

`decompose.py`'s recursive-definition detector (groundedness v2) fires on
exactly two nodes today, both unfoldings. `once_unfolding` and
`since_unfolding` are the same shape and should be expected to fire it too, so
they should grade 1.000 rather than 0.000. `no_deus_ex_machina` should behave
like `chekhov_gun` post-v2 (0.500): grounded via pattern membership in
`heraldry_pattern`, with `PLANTED⟨?0⟩` and `DISCHARGED⟨?0⟩` still ungrounded
because those heads occur in no other statement. Recorded as a prediction so
it can be adjudicated when the nodes land.

---

## 3. Strict versus reflexive order: LT, LEQ, and a live unsoundness

### 3.1 The recorded pair

`temporal.order.precedence_transitivity` uses `LEQ` and is a three-discipline
typed twin. `temporal.order.strict_precedence_asymmetry` uses `BEFORE` and is
a singleton at every level. `docs/BACKLOG.md` records this as the cheapest
demonstration that twin counts measure which head a statement is *allowed* to
use, and asks for "a way to declare `BEFORE` as the strict part of `LEQ`".

### 3.2 What is already there, and why it is wrong

`scripts/match_signatures.py` already contains

    HEAD_ALIASES = { ..., "BEFORE": "order_le", "LEQ": "order_le", ... }

justified as "temporal precedence IS an order relation". Under it, the
asymmetry node's aliased skeleton is (measured)

    IMPLIES⟨order_le⟨?0:V, ?1:V⟩, NEG⟨order_le⟨?1:V, ?0:V⟩⟩⟩

Read as a claim about the merged head, this says a reflexive order is
asymmetric — take `?0 = ?1` and it derives ⊥. The alias asserts something
false. It is harmless today for one reason only: the `order_le` class produces
**zero groups** (measured; removing both entries leaves 30 aliased groups with
identical membership). It is a trap armed and waiting for the first node that
happens to share an aliased shape with a `BEFORE` node.

This is the same error the mirror classes would make if they were filed as
aliases, found in the code rather than proposed: **a declared *relation*
between two heads was encoded as identity of two heads, because identity is
the only thing the table can say.**

### 3.3 Recommendation

Three parts, in order:

1. **Introduce `LT` as the abstract strict-order head**, mirroring the
   abstract `LEQ` the corpora already share, and make `BEFORE` an ordinary
   alias of it. That alias *is* honest — temporal precedence really is a
   spelling of strict order, the same way `MEET` is a spelling of conjunction
   and intersection. Cost, measured: `strict_precedence_asymmetry` renamed
   from `BEFORE` to `LT` remains a singleton at every level (no node in
   `data/` carries `LT`), so the rename is one template edit in
   `scripts/seed_temporal.py`, one corpus regeneration, **zero twin-group
   changes**. Not done here: it is a corpus edit, and this branch is design.
2. **Delete `order_le`.** It buys nothing (0 groups) and asserts a falsehood.
3. **Encode the strict/reflexive relation in `HEAD_ALGEBRA`, not as an
   alias.** The table is already the home for per-head properties with cited
   justification, and it already carries a field no pass consumes
   (`associative`), so an unconsumed `order` field has precedent:

        "LEQ": {"kind": "call", "order": {
                  "reflexive": True, "antisymmetric": True, "transitive": True,
                  "strict_part": "LT"},
                "provenance": "ASSERTED",
                # settheory.order.subset_transitivity,
                # geotop.predicates.containment_transitivity,
                # temporal.order.precedence_transitivity
               },
        "LT":  {"kind": "call", "order": {
                  "irreflexive": True, "asymmetric": True, "transitive": True,
                  "reflexive_closure": "LEQ"},
                "provenance": "ASSERTED",
                # temporal.order.strict_precedence_asymmetry
               },

   The bridge statement then becomes writable as an ordinary node, parsing
   today (measured):

        LT(ELEMA, ELEMB) = MEET(LEQ(ELEMA, ELEMB), NEG(LEQ(ELEMB, ELEMA)))
          ->  LT⟨?0:V, ?1:V⟩ = MEET⟨LEQ⟨?0:V, ?1:V⟩, NEG⟨LEQ⟨?1:V, ?0:V⟩⟩⟩

   which is the reflexive-closure relation *asserted in the corpus* rather
   than declared in a table — the same move `geotop.predicates.adjacency_symmetry`
   made for commutativity, and the same node that would justify the table
   entry. One declaration covers `⊆`/`⊂` and the numeric `<=`/`<` as well.

**Alias class or `HEAD_ALGEBRA`?** `HEAD_ALGEBRA`. An alias class is for heads
that may be *substituted* for one another; `LT` and `LEQ` may never be, since
every asymmetry and irreflexivity statement in the graph would become false.
The general rule this and §2.3 share, and the thing worth taking from this
document if nothing else is:

> Reserve `HEAD_ALIASES` for "same operation, different spelling". Everything
> else — mirror, strict part, reflexive closure, dual — is a *declared
> relation between distinct heads*, belongs in `HEAD_ALGEBRA` or in a
> separately reported level, and must never be reported as a twin.

---

## 4. Payoff: nodes that become writable

At design time nothing in this section was authored. Sections 2 and 3 needed no
schema change, so the payoff was a list, not a diff. The status banner above
records its later implementation.

**Needs only the past heads (no schema, no grammar, no table change):**

1. `narrative.constraint.no_deus_ex_machina` —
   `ALWAYS(IMPLIES(DISCHARGED(ELEMENT), ONCE(PLANTED(ELEMENT))))`. Chekhov's
   converse; the half that forbids the unheralded rescue. Already sitting in
   `chekhov_gun`'s `equivalent_forms` waiting for a head. Covered by (6) —
   probed, `MATCHES = True`, binding `OUTCOME -> DISCHARGED⟨?0⟩`,
   `HERALD -> PLANTED⟨?0⟩` — and *not* covered by
   `temporal.response.response_pattern`, which is the point: the future
   pattern cannot abstract a past statement.
2. `temporal.past.since_unfolding` —
   `SINCE(A,B) = JOIN(B, MEET(A, PREV(SINCE(A,B))))`. The mirror axiom of
   `until_unfolding`, character for character under time reversal. Mirror twin
   of `temporal.recurrence.until_unfolding`; predicted groundedness 1.000 via
   the recursive-definition detector.
3. `temporal.past.past_duality` — `HISTORICALLY(P) = NEG(ONCE(NEG(P)))`.
   Mirror twin of `temporal.modality.temporal_duality`.
4. `temporal.past.prev_distributes_over_meet` —
   `PREV(MEET(A,B)) = MEET(PREV(A), PREV(B))`. Mirror twin of
   `temporal.modality.next_distributes_over_meet`. Note `PREV` distributes
   over `MEET` at every position but is *not* self-dual at the trace origin,
   which is real content the future node does not have to carry — the first
   place where the mirror is imperfect and the corpus can say so.
5. `temporal.past.once_unfolding` — `ONCE(P) = JOIN(P, PREV(ONCE(P)))`.
   Mirror twin of `temporal.modality.eventually_unfolding`.
6. `temporal.response.heraldry_pattern` —
   `ALWAYS(IMPLIES(OUTCOME, ONCE(HERALD)))`. The abstraction (1) instantiates,
   and the mirror of `response_pattern`. Worth authoring *before* (1), so that
   the narrative node's `special_case_of` edge has a target and the pattern
   grades above its instance rather than below it.

**Needs the scope construct (§1) as well:**

7. `narrative.frames.cartoon_gravity` declaration + assertion pair (§1.5). The
   first nodes in the graph whose truth is explicitly relative, and the first
   test of `suspends` against a real physics node.
8. `narrative.frame.premise_persistence` —
   `ALWAYS(IMPLIES(HOLDS(PREMISE), SINCE(HOLDS(PREMISE), FRAMEOPENING)))`.
   The since-founding statement, and the only node on this list that needs
   **both** halves of this document: it says a frame premise has held
   continuously since the scope opened, which is `scope.on_exit`'s dual read
   from inside. Parses today (measured):
   `ALWAYS⟨IMPLIES⟨HOLDS⟨?0:V⟩, SINCE⟨HOLDS⟨?0:V⟩, ?1:P⟩⟩⟩`.

**Needs §3's `LT`:**

9. `temporal.order.strict_part_of_order` —
   `LT(A,B) = MEET(LEQ(A,B), NEG(LEQ(B,A)))`. The bridge that makes
   `strict_precedence_asymmetry`'s isolation a derivation rather than an
   accident of head choice.

Expected yield if all nine land: **five mirror-twin groups** where the corpus
has zero today, one new frame-local checking pass with two nodes to check, and
the graph's first statement relating a strict order to its reflexive closure.
The honest half: **zero new *typed* twins**. Every one of the five is a
mirror, and mirrors are reported separately precisely so nobody counts them as
typed twins.

---

## 5. The provenance `scope_note` fix, and the draft

### 5.1 The one-line change

`docs/BACKLOG.md`: `provenance` entries reject `scope_note` while
`equivalent_forms` entries accept it, two `additionalProperties: false`
objects in one node disagreeing about one key name. Measured across `data/`:

    equivalent_forms entries : 562, of which 498 carry a scope_note  (89%)
    provenance entries       : 648, of which   0 can

and `probstat.probability.two_component_mixture` smuggles two of them into
`bibliographic_entry` inside square brackets, where no bibliography consumer
can parse them. The change, in `$defs.reference.properties`:

    "scope_note": { "type": "string" }

That is the entire fix. `probstat.probability.two_component_mixture` would
then read:

    { "citation_key": "pearson1894",
      "bibliographic_entry": "Pearson, K. (1894). Contributions to the
        Mathematical Theory of Evolution. Phil. Trans. R. Soc. A, 185, 71-110.",
      "scope_note": "The founding paper: a two-component normal mixture fitted
        to Weldon's Naples crab measurements by the method of moments, which
        Pearson invented for the purpose." }

with the brackets removed from the bibliography. That is a corpus edit and is
not made here.

### 5.2 The draft, and what it does not contain

`docs/schema-drafts/equation-node.scope-draft.json` is a full copy of the live
schema plus exactly two additions: the `scope` object of §1 (with `$defs`
`frameScope` and `scopedPremise`) and the `scope_note` of §5.1. It is marked
DRAFT in `$id`, `title` and `$comment`, and the live schema is unchanged.

It deliberately contains **nothing** for §2 or §3. Past modality is a set of
call heads the grammar already parses; the order declaration belongs in
`HEAD_ALGEBRA`. A schema change that is not needed is a migration that is not
needed, and the draft says so in its own `$comment`.

### 5.3 Validation of the draft against the corpus

Run with `jsonschema` 4.26, Draft 2020-12, every node in `data/`:

    nodes checked : 199
    live schema   : 0 errors
    draft schema  : 0 errors
    PARITY        : OK

The draft was also checked to be a strict *extension* rather than a
loosening — it must still reject what the live schema rejects:

| probe | live | draft |
|---|---|---|
| node with a `scope` object (§1.5) | rejected (`'scope' was unexpected`) | **accepted** |
| provenance entry with `scope_note` (§5.1) | rejected (`'scope_note' was unexpected`) | **accepted** |
| unknown top-level key | rejected | rejected |
| `scope.role` outside its enum | — | rejected |
| unknown key inside `scope` | — | rejected |
| `scope` missing `role` | — | rejected |
| `scope.frame` not dotted-lowercase | — | rejected |
| `scope.suspends` not an array / duplicated ids | — | rejected |
| premise missing `expression` | — | rejected |

The draft also passes `Draft202012Validator.check_schema` — it is a valid
2020-12 schema, not merely valid JSON.

`scripts/validate_nodes.py` and `scripts/check_regeneration.py` are green on
this branch and untouched: 199 nodes across 21 corpora, 13 seeds regenerating
byte-identically.

---

## 6. Friction found while designing this

- **`scripts/validate_nodes.py` does not enforce the schema it reads.** It
  checks `required`, two enums and link reciprocity by hand; it never applies
  `additionalProperties: false`. Both defects §5.1 describes were caught by
  authors hitting a real JSON Schema validator elsewhere, not by the repo's
  own validator, which would accept a node with an invented top-level key
  today. `jsonschema` is installed in this environment; a real Draft 2020-12
  pass would cost about four lines and is the reason §5.3's parity table could
  be produced at all.
- **The alias table has one expressive level and three jobs.** §2.3 and §3.2
  are the same finding from opposite ends: `HEAD_ALIASES` says "identical",
  and the graph keeps needing "related". `order_le` is a live, currently
  inert, false assertion produced by that gap. Every future request of this
  shape — dual heads, adjoints, discrete/continuous pairs, the already-shipped
  `sum ~ INTEGRAL` — deserves re-examination against the distinction §3.3
  states.
- **The corpus keeps predicting its own next nodes in `equivalent_forms`, and
  nothing reads them.** `chekhov_gun` carries the exact converse template with
  a scope note explaining what head is missing; `frame_consistency` carries
  the scoped reading it cannot express. Both are machine-readable strings in a
  field the pipeline only prints. A lint that parsed `equivalent_forms`
  expressions and reported the heads they use which no `anonymized_template`
  carries would have generated §4's list mechanically.
- **`docs/BACKLOG.md` is 1072 lines and its Schema section is the fourth of
  five.** Four of this document's five inputs are in it, separated by 800
  lines of matcher findings. The file is doing the work of a design log and an
  issue tracker at once, and the design-relevant entries are the ones hardest
  to find.
