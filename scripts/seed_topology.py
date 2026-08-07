#!/usr/bin/env python3
"""Seed data/algebraic_topology/nodes.json and data/geospatial_topology/nodes.json.

Two corpora, one script, because they are two readings of one subject and the
corpus should be able to say so structurally rather than in prose.

Algebraic topology assigns algebraic invariants to spaces; geospatial topology
(the GIS tradition descending from Egenhofer & Franzosa's point-set relations
and the DE-9IM matrix) asks which qualitative spatial relations survive
deformation of a map. They share an ancestor -- Euler's polyhedron formula,
which is simultaneously the first theorem of combinatorial topology and the
first fact a planar-graph GIS index relies on -- and they share a mechanism:
a *valuation* on a lattice of regions.

Three deliberate structural bets, all checkable by scripts/match_signatures.py:

1. **The valuation twin.** `CARD` in this corpus is not cardinality. In
   `algtop.invariants.euler_characteristic_valuation` it is the Euler
   characteristic; in `geotop.measure.area_inclusion_exclusion` it is area.
   Both are finitely additive, modular valuations on a lattice of sets, and
   inclusion-exclusion is one theorem about such valuations. The template is
   copied character for character from `scripts/seed_logic.py`:

       CARD(JOIN(A, B)) = CARD(A) + CARD(B) - CARD(MEET(A, B))

   so all four of set cardinality, Yeung's I-measure (entropy), Euler
   characteristic and Lebesgue area land on one typed skeleton:

       CARD⟨JOIN⟨?0:V, ?1:V⟩⟩
           = +(CARD⟨?0:V⟩, CARD⟨?1:V⟩, neg(CARD⟨MEET⟨?0:V, ?1:V⟩⟩))

   That is exactly the claim Rota's theory of valuations makes, and it is the
   reason the abstract heads were introduced in the first place.

2. **The order twin.** `geotop.predicates.containment_transitivity` reuses
   `scripts/seed_logic.py`'s `TPL_SUBSET_TRANSITIVITY` verbatim, so GIS
   containment (`ST_Contains` chaining) and set inclusion share
   `IMPLIES⟨MEET⟨LEQ⟨?0:V, ?1:V⟩, LEQ⟨?1:V, ?2:V⟩⟩, LEQ⟨?0:V, ?2:V⟩⟩`.
   That was predicted in seed_logic.py's commentary ("a future node for
   entailment transitivity would twin with this one exactly, without either
   corpus being rewritten"); this corpus is the test, and it passes.

3. **The affine bet.** `chi = 2 - 2g` is affine in the genus. Authored with
   *constant slots* rather than numeric literals -- following the precedent of
   `geometry.area_formulas.triangle_area_formula` (`CONSTANT * BASE * HEIGHT`
   for the 1/2) -- it joins the corpus's affine family at the matcher's
   `family` level, alongside CAPM, the Keynesian consumption function, the
   tangent-line linearization and the location-scale transform. Authored as
   `EULERCHAR = 2 - 2*GENUS` with literals it joins nothing at all, because
   numeric literals are not slots and the sign-absorption rule that reconciles
   `+ SLOPE*X` with `- SLOPE*X` only fires on parameter-like slots. The two
   spellings are recorded together (template vs `literal_constants` equivalent
   form) so the difference is visible rather than folklore.

   Note the two constants must be *different* slots (`CONSTANT`, `CONSTANT2`)
   even though both equal 2. That is not a dodge: the first is chi(S^2) and
   the second is the drop in chi per handle attached. They coincide
   numerically and mean different things, and only distinct slots reproduce
   the affine shape `+(?:P, *(?:P, ?:V))`.

Verified outcome of `python scripts/match_signatures.py` over the merged graph
(111 nodes, zero parse problems, zero slot-schema gaps):

    typed  CARD⟨JOIN⟨?0:V, ?1:V⟩⟩ = +(CARD⟨?0:V⟩, CARD⟨?1:V⟩,
                                       neg(CARD⟨MEET⟨?0:V, ?1:V⟩⟩))
           set_theory + information_theory + algebraic_topology
           + geospatial_topology        (4 disciplines, 1 archetype)
    typed  IMPLIES⟨MEET⟨LEQ⟨?0:V, ?1:V⟩, LEQ⟨?1:V, ?2:V⟩⟩, LEQ⟨?0:V, ?2:V⟩⟩
           set_theory + geospatial_topology
    typed  ?0:V = sum⟨*(?1:P, ?2:V)⟩
           algebraic_topology + statistics
    family ?0:V = +(?1:P, *(?2:P, ?3:V))
           the affine family, now 5 members across 4 disciplines
    shape  ?0 = +(?1, neg(*(?2, ?3)))
           chi = 2 - 2g alongside the Gibbs and Helmholtz free energies --
           unplanned, and the right verdict: both are "a fixed offset less a
           product", and the type split (chi's factors are constants, the free
           energies' are variables) is exactly why it stops at shape level.

Honest misses, recorded here and in docs/BACKLOG.md rather than engineered
away:

- `geotop.polyhedra.euler_polyhedron_formula` (`V - E + F = 2`) is literally
  `algtop.invariants.euler_characteristic_complex` (`EULERCHAR = V - E + F`)
  with the invariant slot pinned to 2. **Neither tool sees it.**
  match_signatures.py needs skeleton identity and a numeric literal is not a
  slot; specialize.py finds the match but discards it, because it only reports
  matches that *used* absorption or identity binding, and this one is a plain
  slot-to-literal bind. The edge is therefore asserted by hand via
  `special_case_of`/`generalizes` -- the same fate as the entropy
  specialization already recorded in docs/BACKLOG.md.
- `geotop.predicates.de9im_disjoint` (`MEET(A, B) = EMPTYSET`) generalizes
  `settheory.boolean_laws.complement_laws` (`MEET(A, NEG(A)) = BOT`) by the
  plain bind `B -> NEG(A)`, and is invisible for exactly the same reason.

  Both were probed directly against specialize.py's own `match()`:
  `MATCHES = True, used_absorption = False, used_identity = False` in each
  case, so the filter at the end of `find_specializations` is what drops them.

- The 16 specialization edges that do touch these corpora are all of the
  degenerate kind docs/BACKLOG.md already names under "Specialization noise
  control": `algtop.homology.betti_number_rank >= settheory.cardinality.
  inclusion_exclusion_two_sets` says that `b = Z - B` generalizes
  inclusion-exclusion, because a variable slot may swallow an entire
  `CARD⟨...⟩` subtree. Zero of the 16 is informative, which matches the
  information-theory corpus's experience exactly.
- The Euler-Poincare formula's alternating signs are unrepresentable. The
  grammar has no `(-1)^i` and no way to alternate over an index, so
  `EULERCHAR = sum_i COEFF_i*BETTI_i` hides the whole sign structure inside a
  parameter slot. The upside is an honest surprise: it becomes an exact typed
  twin of `probstat.probability.total_probability_partition`
  (`MARGINAL = sum_i CONDITIONAL_i*WEIGHT_i`). Both really are "a total
  decomposed as a weighted sum of indexed components"; what the matcher cannot
  tell you is that one set of weights is a probability distribution and the
  other alternates in sign.

Authoring constraints observed (docs/BACKLOG.md):

- `statement_id` forbids `_` in the first segment, so ids are `algtop.` and
  `geotop.` while the directories and `discipline` fields are
  `algebraic_topology` and `geospatial_topology`.
- `symbol_lexicon.symbols` requires >= 1 entry and its category enum has no
  `functional`, so every head (CARD, MEET, JOIN, LEQ, IMPLIES, INTERIOR,
  BOUNDARY, EXTERIOR, TOUCHES, HOMOLOGY, FUNDGROUP, ...) lives in
  `functionals` and each node keeps at least one scalar symbol.
- `constantToken` has no `name` key.
- Slot ids must not begin `sum_ prod_ lim_ max_ min_`; indexed slots use the
  suffix convention (`COEFF_i`, `BETTI_i`) established by the information
  theory corpus.
- Call arguments are ORDERED. The MEET/JOIN/LEQ argument order fixed by
  seed_logic.py (distinguished operand first) is preserved exactly, which is
  what makes the twins above hold by construction rather than by luck.
- Cross-corpus `entails`/`equivalent_to` need the reciprocal edge in the other
  corpus's file. Only the two corpora written *here* carry such edges between
  them; every reference into logic, set theory, information theory,
  statistics, calculus or geometry is one-sided `composed_with`.
"""

from __future__ import annotations

import json
import string
from pathlib import Path

# --------------------------------------------------------------------------
# Shared templates. Copied character for character from scripts/seed_logic.py
# so the twins cannot drift. Do not "tidy" the spacing or the argument order.
# --------------------------------------------------------------------------

TPL_INCLUSION_EXCLUSION = (
    "CARD(JOIN({a}, {b})) = CARD({a}) + CARD({b}) - CARD(MEET({a}, {b}))"
)
TPL_ORDER_TRANSITIVITY = (
    "IMPLIES(MEET(LEQ({a}, {b}), LEQ({b}, {c})), LEQ({a}, {c}))"
)


def render(tpl: str, **vocab: str) -> str:
    return tpl.format(**vocab)


def tpl_keys(tpl: str) -> list[str]:
    seen: list[str] = []
    for _, key, _, _ in string.Formatter().parse(tpl):
        if key and key not in seen:
            seen.append(key)
    return seen


# --------------------------------------------------------------------------
# Builders
# --------------------------------------------------------------------------


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="arithmetic"):
    return {"symbol": symbol, "name": name, "arity": arity,
            "operator_family": family}


def slot(sid, cat, role):
    return {"slot_id": sid, "syntactic_category": cat, "semantic_role": role}


def form(form_id, expression, notation_system="ascii", scope_note=None):
    out = {"form_id": form_id, "notation_system": notation_system,
           "expression": expression}
    if scope_note:
        out["scope_note"] = scope_note
    return out


def links(entailed_by=None, entails=None, equivalent_to=None,
          special_case_of=None, generalizes=None, composed_with=None):
    return {"entailed_by": entailed_by or [], "entails": entails or [],
            "equivalent_to": equivalent_to or [],
            "special_case_of": special_case_of or [],
            "generalizes": generalizes or [],
            "composed_with": composed_with or []}


def node(sid, title, cls, status, discipline, subfield, topic, canonical_objects,
         ascii_, latex, forms, archetype, template, slots, invariants,
         symbols, operators, meaning, significance, conditions, provenance,
         functionals=None, constants=None, index_sets=None, failure_modes=None,
         inferential_links=None, keywords=None):
    interpretation = {"statement_meaning": meaning,
                      "statistical_significance": significance,
                      "regularity_conditions": conditions}
    if failure_modes:
        interpretation["failure_modes"] = failure_modes
    out = {
        "statement_id": sid,
        "title": title,
        "statement_class": cls,
        "epistemic_status": status,
        "theory_context": {"disciplines": [discipline], "subfield": subfield,
                           "topic": topic,
                           "canonical_objects": canonical_objects},
        "formal_statement": {"canonical_ascii": ascii_, "canonical_latex": latex,
                             "equivalent_forms": forms},
        "structural_signature": {"archetype_id": archetype,
                                 "anonymized_template": template,
                                 "slot_schema": slots,
                                 "invariants": invariants},
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
    return out


# --------------------------------------------------------------------------
# Operators
# --------------------------------------------------------------------------

EQ = op("=", "equality", 2, "relational")
LE = op("<=", "less than or equal", 2, "relational")
ISO = op("iso", "group isomorphism", 2, "relational")
ADD = op("+", "addition", 2, "arithmetic")
SUB = op("-", "subtraction", 2, "arithmetic")
MUL = op("*", "multiplication", 2, "arithmetic")
SUM_OP = op("sum", "finite summation over a dimension index", 1, "arithmetic")
IMPL = op("implies", "material implication at the meta level", 2, "logical")
AND = op("and", "conjunction of premises", 2, "logical")
INTER = op("inter", "set intersection", 2, "set_theoretic")
UNION = op("union", "set union", 2, "set_theoretic")
SUBSET = op("subset", "subset inclusion", 2, "set_theoretic")
COMPL = op("^c", "complement relative to the ambient space", 1, "set_theoretic")
MEASURE = op("mu", "Lebesgue measure of a planar region", 1, "measure_theoretic")

# --------------------------------------------------------------------------
# Functional heads. The lattice heads carry the SAME translation-table style
# of description that scripts/seed_logic.py established, extended with the
# topological and geospatial readings, so the twin is documented at both ends.
# --------------------------------------------------------------------------

MEET_FN = {
    "notation": "MEET(.,.)", "name": "lattice meet", "input_arity": 2,
    "description": "Greatest lower bound. Realized as intersection of "
                   "subspaces/regions here, as conjunction in data/logic, as "
                   "set intersection in data/set_theory, and as the atom of a "
                   "shared information content in data/information_theory."}
JOIN_FN = {
    "notation": "JOIN(.,.)", "name": "lattice join", "input_arity": 2,
    "description": "Least upper bound. Realized as union of subspaces/regions "
                   "here, as disjunction in data/logic and as set union in "
                   "data/set_theory."}
NEG_FN = {
    "notation": "NEG(.)", "name": "lattice complement", "input_arity": 1,
    "description": "Complement relative to the ambient space. Realized as the "
                   "exterior-plus-boundary of a region here, as negation in "
                   "data/logic and as relative complement in data/set_theory."}
LEQ_FN = {
    "notation": "LEQ(.,.)", "name": "lattice order", "input_arity": 2,
    "description": "The partial order x <= y, equivalently MEET(x, y) = x. "
                   "Realized as spatial containment (OGC ST_Within / "
                   "ST_Contains) here, as entailment in data/logic and as "
                   "subset inclusion in data/set_theory."}
IMPLIES_FN = {
    "notation": "IMPLIES(.,.)", "name": "implication", "input_arity": 2,
    "description": "Meta-level 'if ... then' joining the premises of a rule to "
                   "its conclusion. Same head and same argument order as "
                   "data/logic and data/set_theory use for their inference "
                   "nodes."}


def card_fn(description: str) -> dict:
    return {"notation": "CARD(.)", "name": "valuation on the lattice",
            "input_arity": 1, "codomain": "reals", "description": description}


CARD_EULER = card_fn(
    "The Euler characteristic chi, used as the corpus's generic valuation "
    "head. chi is finitely additive and modular on the lattice of finite CW "
    "subcomplexes -- exactly the property CARD names in data/set_theory "
    "(counting measure) and in data/information_theory (Yeung's I-measure). "
    "Unlike cardinality it is signed and takes the value 0 on odd-dimensional "
    "closed manifolds, which is why it is a valuation rather than a measure.")

CARD_AREA = card_fn(
    "Planar Lebesgue measure (area) of a region, used as the corpus's generic "
    "valuation head. Area is a finitely additive, modular, monotone valuation "
    "on the lattice of measurable regions, which is the only property "
    "inclusion-exclusion uses -- hence the shared head with set cardinality, "
    "entropy and the Euler characteristic.")

INTERIOR_FN = {
    "notation": "INTERIOR(.)", "name": "topological interior", "input_arity": 1,
    "codomain": "open regions",
    "description": "Largest open set contained in the region; DE-9IM writes it "
                   "I(A) and it supplies the first row and column of the "
                   "nine-intersection matrix."}
BOUNDARY_FN = {
    "notation": "BOUNDARY(.)", "name": "topological boundary", "input_arity": 1,
    "codomain": "regions",
    "description": "Closure minus interior; DE-9IM writes it B(A). For a simple "
                   "polygon it is the ring, which is what a GIS actually stores."}
EXTERIOR_FN = {
    "notation": "EXTERIOR(.)", "name": "topological exterior", "input_arity": 1,
    "codomain": "open regions",
    "description": "Complement of the closure; DE-9IM writes it E(A). Its "
                   "presence is what makes the nine-intersection model able to "
                   "distinguish 'disjoint' from 'meets', which the four-"
                   "intersection model could not."}
CLOSURE_FN = {
    "notation": "CLOSURE(.)", "name": "topological closure", "input_arity": 1,
    "codomain": "closed regions",
    "description": "Interior joined with boundary; the smallest closed set "
                   "containing the region."}
TOUCHES_FN = {
    "notation": "TOUCHES(.,.)", "name": "adjacency predicate", "input_arity": 2,
    "codomain": "truth values",
    "description": "The OGC 'touches' relation: the two regions' closures meet "
                   "but their interiors do not. Argument order is written "
                   "explicitly on both sides of the statement precisely because "
                   "the matcher treats call arguments as ordered, which is what "
                   "lets the symmetry claim be visible as structure."}
HOMOLOGY_FN = {
    "notation": "HOMOLOGY(.)", "name": "singular homology functor",
    "input_arity": 1, "codomain": "graded abelian groups",
    "description": "H_*(X), the graded singular homology of a space with "
                   "integer coefficients. Written as a call rather than "
                   "expanded so that invariance is visible as a statement about "
                   "the functor rather than about any particular group."}
HOMOTOPYEQ_FN = {
    "notation": "HOMOTOPYEQUIVALENT(.,.)", "name": "homotopy equivalence",
    "input_arity": 2, "codomain": "truth values",
    "description": "There exist maps f: X -> Y and g: Y -> X with gf and fg "
                   "homotopic to the identities. Weaker than homeomorphism and "
                   "strictly stronger than having isomorphic homology."}
FUNDGROUP_FN = {
    "notation": "FUNDGROUP(.)", "name": "fundamental group", "input_arity": 1,
    "codomain": "groups",
    "description": "pi_1(X, x0), the group of homotopy classes of loops at a "
                   "basepoint under concatenation. The basepoint is suppressed "
                   "because the spaces named here are path-connected."}
RANK_FN = {
    "notation": "RANK(.)", "name": "rank of a finitely generated abelian group",
    "input_arity": 1, "codomain": "non-negative integers",
    "description": "Number of free generators, i.e. the dimension of the "
                   "rationalization. Torsion is invisible to it, which is the "
                   "whole reason Betti numbers lose information that homology "
                   "keeps."}

# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

HATCHER = {"citation_key": "hatcher2002",
           "bibliographic_entry": "Hatcher, A. (2002). Algebraic Topology. Cambridge: Cambridge University Press.",
           "url": "https://pi.math.cornell.edu/~hatcher/AT/ATpage.html"}
MUNKRES_AT = {"citation_key": "munkres1984",
              "bibliographic_entry": "Munkres, J. R. (1984). Elements of Algebraic Topology. Menlo Park: Addison-Wesley."}
MUNKRES_TOP = {"citation_key": "munkres2000",
               "bibliographic_entry": "Munkres, J. R. (2000). Topology (2nd ed.). Upper Saddle River: Prentice Hall."}
POINCARE = {"citation_key": "poincare1895",
            "bibliographic_entry": "Poincare, H. (1895). Analysis Situs. Journal de l'Ecole Polytechnique, 2nd series, 1, 1-121."}
EULER1758 = {"citation_key": "euler1758",
             "bibliographic_entry": "Euler, L. (1758). Elementa doctrinae solidorum. Novi Commentarii Academiae Scientiarum Petropolitanae, 4, 109-140."}
LAKATOS = {"citation_key": "lakatos1976",
           "bibliographic_entry": "Lakatos, I. (1976). Proofs and Refutations: The Logic of Mathematical Discovery. Cambridge: Cambridge University Press."}
RICHESON = {"citation_key": "richeson2008",
            "bibliographic_entry": "Richeson, D. S. (2008). Euler's Gem: The Polyhedron Formula and the Birth of Topology. Princeton: Princeton University Press."}
MASSEY = {"citation_key": "massey1991",
          "bibliographic_entry": "Massey, W. S. (1991). A Basic Course in Algebraic Topology. Graduate Texts in Mathematics 127. New York: Springer."}
EGENHOFER = {"citation_key": "egenhofer1991",
             "bibliographic_entry": "Egenhofer, M. J., Franzosa, R. D. (1991). Point-set topological spatial relations. International Journal of Geographical Information Systems, 5(2), 161-174.",
             "url": "https://doi.org/10.1080/02693799108927841"}
CLEMENTINI = {"citation_key": "clementini1993",
              "bibliographic_entry": "Clementini, E., Di Felice, P., van Oosterom, P. (1993). A small set of formal topological relationships suitable for end-user interaction. In Advances in Spatial Databases (SSD '93), LNCS 692, 277-295. Berlin: Springer."}
OGC_SFA = {"citation_key": "ogc2011sfa",
           "bibliographic_entry": "Open Geospatial Consortium (2011). OpenGIS Implementation Standard for Geographic Information -- Simple Feature Access, Part 1: Common Architecture, version 1.2.1. OGC 06-103r4.",
           "url": "https://www.ogc.org/standard/sfa/"}
WORBOYS = {"citation_key": "worboys2004",
           "bibliographic_entry": "Worboys, M. F., Duckham, M. (2004). GIS: A Computing Perspective (2nd ed.). Boca Raton: CRC Press."}
EGENHOFER_HERRING = {"citation_key": "egenhofer1990",
                     "bibliographic_entry": "Egenhofer, M. J., Herring, J. R. (1990). A Mathematical Framework for the Definition of Topological Relationships. Proceedings of the 4th International Symposium on Spatial Data Handling, 803-813."}
ROTA = {"citation_key": "rota1964",
        "bibliographic_entry": "Rota, G.-C. (1964). On the Foundations of Combinatorial Theory I: Theory of Moebius Functions. Zeitschrift fuer Wahrscheinlichkeitstheorie und Verwandte Gebiete, 2(4), 340-368."}
KLAIN_ROTA = {"citation_key": "klain1997",
              "bibliographic_entry": "Klain, D. A., Rota, G.-C. (1997). Introduction to Geometric Probability. Cambridge: Cambridge University Press."}
HALMOS_MEASURE = {"citation_key": "halmos1950",
                  "bibliographic_entry": "Halmos, P. R. (1950). Measure Theory. New York: D. Van Nostrand."}
STANLEY = {"citation_key": "stanley2011",
           "bibliographic_entry": "Stanley, R. P. (2011). Enumerative Combinatorics, Volume 1 (2nd ed.). Cambridge: Cambridge University Press."}
DAVEY_PRIESTLEY = {"citation_key": "davey2002",
                   "bibliographic_entry": "Davey, B. A., Priestley, H. A. (2002). Introduction to Lattices and Order (2nd ed.). Cambridge: Cambridge University Press."}

# --------------------------------------------------------------------------
# Canonical object lists
# --------------------------------------------------------------------------

ALGTOP_OBJECTS = ["topological space", "CW complex", "chain complex",
                  "homology group", "Euler characteristic"]
GEOTOP_OBJECTS = ["planar region", "simple feature geometry",
                  "nine-intersection matrix", "planar subdivision",
                  "lattice of regions"]

ALGTOP_SUBFIELD = "algebraic_topology"
GEOTOP_SUBFIELD = "geospatial_topology"

# --------------------------------------------------------------------------
# ALGEBRAIC TOPOLOGY
# --------------------------------------------------------------------------

ALGTOP_NODES = [
    node(
        sid="algtop.invariants.euler_characteristic_surface",
        title="Euler Characteristic of a Closed Orientable Surface",
        cls="theorem", status="formal",
        discipline="algebraic_topology", subfield=ALGTOP_SUBFIELD,
        topic="topological_invariants", canonical_objects=ALGTOP_OBJECTS,
        ascii_="chi(Sigma_g) = 2 - 2*g",
        latex="\\chi(\\Sigma_g) = 2 - 2g",
        forms=[
            form("literal_constants", "EULERCHAR = 2 - 2*GENUS",
                 scope_note="The same statement with the two 2s as numeric literals rather than constant slots. Recorded because the choice is load-bearing: with literals the node joins no twin group at all, since numeric literals are not slots and the matcher's sign-absorption rule fires only on parameter-like slots."),
            form("sphere", "chi(S^2) = 2",
                 scope_note="Genus 0; the value Euler's polyhedron formula pins down"),
            form("torus", "chi(T^2) = 0",
                 scope_note="Genus 1; the vanishing that makes the torus admit a nowhere-zero vector field"),
            form("non_orientable", "chi(N_k) = 2 - k",
                 scope_note="Non-orientable closed surface with k crosscaps; affine in k with half the slope, so the two families are cousins rather than instances"),
            form("gauss_bonnet", "INTEGRAL(GAUSSCURVATURE) = 2*pi*chi",
                 scope_note="Gauss-Bonnet: the same invariant computed by integrating curvature, which is how differential geometry reaches it"),
        ],
        archetype="affine_operator",
        template="EULERCHAR = CONSTANT - CONSTANT2*GENUS",
        slots=[
            slot("EULERCHAR", "variable", "topological_invariant"),
            slot("CONSTANT", "constant", "intercept_sphere_characteristic"),
            slot("CONSTANT2", "constant", "slope_cost_per_handle"),
            slot("GENUS", "variable", "handle_count"),
        ],
        invariants=[
            "Affine in the genus: one intercept and one slope, with the genus as "
            "the free variable. That is the whole content of the classification of "
            "closed orientable surfaces read numerically.",
            "The two constants are numerically equal (both 2) but semantically "
            "distinct: the intercept is chi(S^2) and the slope is the drop in chi "
            "caused by attaching one handle. They are authored as separate slots "
            "because collapsing them to one slot would destroy the affine shape.",
            "Strictly decreasing in the genus, so chi is a complete invariant for "
            "closed orientable surfaces: two such surfaces are homeomorphic exactly "
            "when their Euler characteristics agree.",
            "Homotopy invariant, hence homeomorphism invariant; it cannot "
            "distinguish a surface from anything homotopy equivalent to it.",
        ],
        symbols=[
            sym("chi", "variable", "topological_invariant",
                "Euler characteristic of the surface; an integer.", 0),
            sym("g", "variable", "handle_count",
                "Genus: the number of handles attached to the sphere, a "
                "non-negative integer.", 0),
        ],
        operators=[EQ, SUB, MUL],
        constants=[
            {"symbol": "2", "value": 2,
             "description": "chi of the 2-sphere, the base surface of the classification."},
            {"symbol": "2 (slope)", "value": 2,
             "description": "The decrease in chi per attached handle: a handle adds one 1-cell pair and one 2-cell, netting -2."},
        ],
        meaning="Every closed orientable surface is a sphere with some number of "
                "handles, and each handle costs exactly two units of Euler "
                "characteristic; so the invariant is a straight line in the genus.",
        significance="The corpus's test of whether a topological invariant can join "
                     "an *economic* structural family, and it does -- at the family "
                     "level, not the typed one. The typed skeleton is "
                     "`?0:V = +(?1:P, neg(*(?2:P, ?3:V)))`; the affine family "
                     "(CAPM, the Keynesian consumption function, the tangent-line "
                     "linearization, the location-scale transform) is "
                     "`?0:V = +(?1:P, *(?2:P, ?3:V))`. They meet only once "
                     "match_signatures.py absorbs the minus sign into the "
                     "parameter-like slope slot, which is exactly the right verdict: "
                     "the sign is a convention (chi decreasing in genus) and not "
                     "structure. Two further consequences are worth recording. "
                     "First, this node makes `affine_operator` span two shapes, so "
                     "the matcher's archetype-drift section now flags the label -- "
                     "correctly, because the hand-assigned label was always the "
                     "family-level claim. Second, the same statement written "
                     "`EULERCHAR = 2 - 2*GENUS` twins with nothing whatsoever, which "
                     "is the sharpest available demonstration that in this corpus "
                     "'is a fixed number a literal or a constant slot?' is a "
                     "structural decision and not a formatting one.",
        conditions=["The surface is closed (compact, without boundary), connected "
                    "and orientable",
                    "Genus is a non-negative integer"],
        failure_modes=[
            "Fails as stated for non-orientable surfaces: chi = 2 - k in the number "
            "of crosscaps, a different line, and the Klein bottle (chi = 0) is then "
            "indistinguishable from the torus by chi alone.",
            "Surfaces with boundary lose one unit of chi per boundary circle, so "
            "the formula must become chi = 2 - 2g - b; applying the closed form to "
            "a disc or an annulus is the standard error.",
            "In dimensions above 2 chi stops being a complete invariant and "
            "vanishes identically for odd-dimensional closed manifolds, so the "
            "intuition 'chi counts holes' does not survive the passage to 3-"
            "manifolds.",
        ],
        provenance=[HATCHER, MASSEY, MUNKRES_AT, RICHESON],
        functionals=[],
        inferential_links=links(
            entailed_by=["algtop.invariants.euler_characteristic_complex"],
            composed_with=["algtop.homology.betti_alternating_sum",
                           "calculus.approximation.tangent_line_linearization",
                           "probstat.transform.affine_location_scale"]),
        keywords=["Euler characteristic", "genus", "closed surface",
                  "classification of surfaces", "affine", "topological invariant"],
    ),
    node(
        sid="algtop.invariants.euler_characteristic_complex",
        title="Euler Characteristic of a Finite 2-Complex (Alternating Cell Count)",
        cls="definition", status="formal",
        discipline="algebraic_topology", subfield=ALGTOP_SUBFIELD,
        topic="topological_invariants", canonical_objects=ALGTOP_OBJECTS,
        ascii_="chi = V - E + F",
        latex="\\chi(X) = V - E + F",
        forms=[
            form("general_dimension", "chi = sum_i COEFF_i*CELLCOUNT_i",
                 scope_note="Arbitrary finite CW complex: the alternating sum of the number of i-cells, of which V - E + F is the 2-dimensional case"),
            form("unicode", "χ = |X^0| - |X^1| + |X^2|",
                 scope_note="Written with cell-set cardinalities"),
            form("graph", "chi = V - E",
                 scope_note="A finite graph is a 1-complex; chi is then the number of connected components minus the number of independent cycles"),
            form("triangulation", "chi = n_0 - n_1 + n_2",
                 scope_note="Simplicial form, with n_k the number of k-simplices in a triangulation"),
        ],
        archetype="alternating_cell_count",
        template="EULERCHAR = VERTICES - EDGES + FACES",
        slots=[
            slot("EULERCHAR", "variable", "topological_invariant"),
            slot("VERTICES", "variable", "zero_cell_count"),
            slot("EDGES", "variable", "one_cell_count"),
            slot("FACES", "variable", "two_cell_count"),
        ],
        invariants=[
            "Alternating in cell dimension: even-dimensional cells add, odd-"
            "dimensional cells subtract. The alternation is the entire reason the "
            "count is a topological invariant rather than an artefact of the chosen "
            "cell structure.",
            "Independent of the cell structure although every term in it is not: "
            "subdividing a face changes V, E and F individually while leaving the "
            "combination fixed. This is the corpus's clearest example of an "
            "invariant defined by a non-invariant recipe.",
            "All three counts are free variables of the same category, so the typed "
            "skeleton carries no parameter slot at all -- unlike the surface form, "
            "where the two 2s are constants.",
            "Extends verbatim to every finite dimension as the alternating sum over "
            "cell dimensions; the 2-dimensional case is written out only because "
            "the grammar has no alternating-sign construct.",
        ],
        symbols=[
            sym("chi", "variable", "topological_invariant",
                "Euler characteristic of the complex.", 0),
            sym("V", "variable", "zero_cell_count",
                "Number of vertices (0-cells).", 0),
            sym("E", "variable", "one_cell_count",
                "Number of edges (1-cells).", 0),
            sym("F", "variable", "two_cell_count",
                "Number of faces (2-cells).", 0),
        ],
        operators=[EQ, ADD, SUB],
        meaning="The Euler characteristic of a complex is obtained by counting its "
                "cells with alternating signs: vertices minus edges plus faces.",
        significance="The hinge node of this whole seeding effort. It is the "
                     "combinatorial definition that "
                     "`geotop.polyhedra.euler_polyhedron_formula` pins to the value "
                     "2, and it is the node the parallel differential-geometry "
                     "corpus reaches through Gauss-Bonnet, so its id is fixed by "
                     "contract. Structurally it is also an instructive miss: the "
                     "polyhedron formula is *literally this template with the "
                     "invariant slot bound to 2*, yet neither tool reports the "
                     "relation. match_signatures.py compares skeletons and a numeric "
                     "literal is not a slot; specialize.py finds the match but "
                     "suppresses it, because it only emits edges that used "
                     "absorption or identity-element binding and this one is a plain "
                     "slot-to-literal bind. The edge is therefore asserted by hand "
                     "below, joining the short list of relations in this repository "
                     "that the tooling cannot check.",
        conditions=["The complex is finite and of dimension at most 2 as written",
                    "Cells are attached along their boundaries in the CW sense"],
        failure_modes=[
            "Infinite complexes have no such count; chi is defined only when the "
            "cell counts are finite (or the homology is finitely generated).",
            "The count is invariant only under cell structures of the *same* space. "
            "Lakatos's history of the polyhedron formula is a catalogue of what "
            "happens when 'polyhedron' is left informal enough to admit "
            "non-complexes.",
            "Written as V - E + F it silently assumes there are no cells of "
            "dimension 3 or higher; a solid tetrahedron and its boundary surface "
            "have different Euler characteristics (1 and 2).",
        ],
        provenance=[HATCHER, MUNKRES_AT, POINCARE, LAKATOS],
        inferential_links=links(
            entails=["algtop.invariants.euler_characteristic_surface",
                     "algtop.invariants.euler_characteristic_valuation"],
            generalizes=["geotop.polyhedra.euler_polyhedron_formula"],
            composed_with=["algtop.homology.betti_alternating_sum"]),
        keywords=["Euler characteristic", "CW complex", "alternating sum",
                  "cell count", "combinatorial topology"],
    ),
    node(
        sid="algtop.invariants.euler_characteristic_valuation",
        title="Euler Characteristic is a Valuation (Inclusion-Exclusion for Subcomplexes)",
        cls="theorem", status="derived",
        discipline="algebraic_topology", subfield=ALGTOP_SUBFIELD,
        topic="topological_invariants", canonical_objects=ALGTOP_OBJECTS,
        ascii_="chi(A union B) = chi(A) + chi(B) - chi(A inter B)",
        latex="\\chi(A \\cup B) = \\chi(A) + \\chi(B) - \\chi(A \\cap B)",
        forms=[
            form("unicode", "χ(A ∪ B) = χ(A) + χ(B) − χ(A ∩ B)"),
            form("mayer_vietoris",
                 "... -> H_n(A inter B) -> H_n(A) (+) H_n(B) -> H_n(A union B) -> H_{n-1}(A inter B) -> ...",
                 scope_note="The Mayer-Vietoris long exact sequence, whose exactness makes the alternating sum of ranks telescope into the identity above"),
            form("disjoint_case", "chi(A union B) = chi(A) + chi(B) when A inter B = emptyset",
                 scope_note="Finite additivity as the degenerate case"),
            form("product", "chi(A x B) = chi(A) * chi(B)",
                 scope_note="The companion multiplicativity, which is a different structure and deliberately not stated as a node here"),
        ],
        archetype="inclusion_exclusion_correction",
        template=render(TPL_INCLUSION_EXCLUSION, a="SPACEA", b="SPACEB"),
        slots=[
            slot("SPACEA", "set", "subcomplex_operand"),
            slot("SPACEB", "set", "subcomplex_operand"),
        ],
        invariants=[
            "The Euler characteristic is a valuation: finitely additive with a "
            "modular correction term. Nothing in the statement mentions cells, "
            "homology or topology, which is precisely why it twins with counting "
            "and with entropy.",
            "Signed, unlike cardinality and area: chi can be negative, so the "
            "identity is genuinely an identity of valuations and not of measures. "
            "The correction term is subtracted for the same reason in all four "
            "corpora regardless.",
            "Symmetric in the two operands, since MEET and JOIN are.",
            "Derived from Mayer-Vietoris by taking alternating sums of ranks; "
            "exactness of the sequence is what makes the correction exactly one "
            "term rather than an error bound.",
            "Extends to n subcomplexes with alternating signs over all non-empty "
            "subsets -- the Moebius function of the Boolean lattice, the same "
            "combinatorics as the set-theoretic case.",
        ],
        symbols=[
            sym("A", "set", "subcomplex_operand",
                "A subcomplex of a finite CW complex.", 0),
            sym("B", "set", "subcomplex_operand",
                "A second subcomplex of the same complex.", 0),
        ],
        operators=[EQ, ADD, SUB, INTER, UNION],
        functionals=[CARD_EULER, MEET_FN, JOIN_FN],
        meaning="Gluing two subcomplexes adds their Euler characteristics and then "
                "removes the characteristic of the overlap, which would otherwise "
                "have been counted twice.",
        significance="The node that makes the corpus's valuation claim testable. It "
                     "is an exact typed twin of "
                     "`settheory.cardinality.inclusion_exclusion_two_sets`, "
                     "`infotheory.mutualinfo.entropy_inclusion_exclusion` and "
                     "`geotop.measure.area_inclusion_exclusion`, on the skeleton "
                     "`CARD⟨JOIN⟨?0:V, ?1:V⟩⟩ = +(CARD⟨?0:V⟩, CARD⟨?1:V⟩, "
                     "neg(CARD⟨MEET⟨?0:V, ?1:V⟩⟩))`, because all four reuse the "
                     "template string fixed in scripts/seed_logic.py. The claim the "
                     "twin encodes is Rota's: counting measure, Shannon entropy, "
                     "Lebesgue area and the Euler characteristic are four "
                     "valuations on lattices, and inclusion-exclusion is one theorem "
                     "about valuations. This is the strongest form of the corpus's "
                     "thesis -- not four analogous statements, one statement with "
                     "four interpretations of CARD -- and it is worth noting that "
                     "the four differ sharply elsewhere: counting is non-negative "
                     "and integral, entropy is non-negative and real, area is "
                     "non-negative and continuous, and chi is signed and integral. "
                     "Modularity is the only property the identity uses.",
        conditions=["A, B and A inter B are finite CW subcomplexes of a common "
                    "complex",
                    "The triple is excisive, so that Mayer-Vietoris applies",
                    "All Euler characteristics involved are finite"],
        failure_modes=[
            "Fails for pairs whose intersection is not a subcomplex; a "
            "CW-incompatible decomposition breaks exactness and with it the "
            "identity.",
            "For infinite complexes chi need not be defined, so the equation is "
            "vacuous rather than false.",
            "The n-fold expansion inherits the 2^n - 1 term count of set-theoretic "
            "inclusion-exclusion, and with signed values the terms do not merely "
            "cancel numerically but can do so catastrophically.",
        ],
        provenance=[HATCHER, ROTA, KLAIN_ROTA, MUNKRES_AT],
        inferential_links=links(
            entailed_by=["algtop.invariants.euler_characteristic_complex"],
            composed_with=["algtop.homology.betti_alternating_sum",
                           "geotop.measure.area_inclusion_exclusion",
                           "settheory.cardinality.inclusion_exclusion_two_sets",
                           "infotheory.mutualinfo.entropy_inclusion_exclusion"]),
        keywords=["Euler characteristic", "valuation", "inclusion-exclusion",
                  "Mayer-Vietoris", "modularity", "additivity"],
    ),
    node(
        sid="algtop.homology.betti_alternating_sum",
        title="Euler-Poincare Formula (Euler Characteristic as an Alternating Betti Sum)",
        cls="theorem", status="derived",
        discipline="algebraic_topology", subfield=ALGTOP_SUBFIELD,
        topic="homology", canonical_objects=ALGTOP_OBJECTS,
        ascii_="chi = sum_i (-1)^i * b_i",
        latex="\\chi(X) = \\sum_{i \\ge 0} (-1)^i b_i",
        forms=[
            form("explicit_signs", "chi = b_0 - b_1 + b_2 - b_3 + ...",
                 scope_note="Written out; the signs the template cannot express"),
            form("surface", "chi = 2 - 2g = b_0 - b_1 + b_2 = 1 - 2g + 1",
                 scope_note="Closed orientable surface, where b_0 = b_2 = 1 and b_1 = 2g"),
            form("cell_form", "chi = sum_i (-1)^i * c_i",
                 scope_note="The same alternating sum over cell counts; equality of the two sums IS the Euler-Poincare theorem"),
            form("rank_form", "chi = sum_i (-1)^i * RANK(HOMOLOGY_i)",
                 scope_note="Betti numbers spelled out as ranks of homology groups"),
        ],
        archetype="alternating_rank_sum",
        template="EULERCHAR = sum_i COEFF_i*BETTI_i",
        slots=[
            slot("EULERCHAR", "variable", "topological_invariant"),
            slot("COEFF_i", "parameter", "alternating_sign"),
            slot("BETTI_i", "variable", "component_rank"),
        ],
        invariants=[
            "A total decomposed as a weighted sum of indexed components: the "
            "invariant on the left is nothing but the components on the right "
            "combined with fixed weights.",
            "The weights are (-1)^i and are therefore *fixed by the index*, not "
            "free. The template grammar has no way to say this, so the sign lives "
            "in a parameter slot and the alternation is invisible to the matcher. "
            "This is a real loss and is recorded as such rather than papered over.",
            "Only finitely many Betti numbers are non-zero for a finite complex, so "
            "the sum is finite even when written over all dimensions.",
            "Torsion is invisible: Betti numbers are ranks, so two spaces with the "
            "same free part and different torsion share a chi. That the alternating "
            "sum of cell counts nonetheless equals the alternating sum of ranks is "
            "the content of the theorem, not a triviality.",
        ],
        symbols=[
            sym("chi", "variable", "topological_invariant",
                "Euler characteristic of the space.", 0),
            sym("b_i", "variable", "betti_number",
                "i-th Betti number: the rank of the i-th homology group.", 0),
        ],
        operators=[EQ, SUM_OP, MUL],
        index_sets=[{"notation": "i", "domain": "non-negative integers up to the "
                                                "dimension of the complex",
                     "description": "Homological degree. Only finitely many terms "
                                    "are non-zero for a finite complex."}],
        constants=[{"symbol": "(-1)^i",
                    "description": "The alternating sign attached to degree i. A "
                                   "fixed function of the index, occupying a "
                                   "parameter slot because the grammar has no "
                                   "index-dependent coefficient."}],
        meaning="The Euler characteristic is the alternating sum of the Betti "
                "numbers: the ranks of the homology groups combine with signs into "
                "the same integer the cell count produces.",
        significance="An honest surprise. Because the alternating signs collapse "
                     "into an opaque parameter slot, the typed skeleton is "
                     "`?0:V = sum⟨*(?1:P, ?2:V)⟩` -- which is character for "
                     "character the skeleton of "
                     "`probstat.probability.total_probability_partition` "
                     "(`MARGINAL = sum_i CONDITIONAL_i*WEIGHT_i`). The twin fires. "
                     "Is it real? Partly, and the partial answer is the useful one: "
                     "both statements decompose a total into a weighted sum of "
                     "indexed components, and both are instances of a valuation "
                     "evaluated on a decomposition. What the matcher cannot see is "
                     "that one family of weights is a probability distribution "
                     "(non-negative, summing to one) and the other alternates in "
                     "sign, which is the difference between an average and a "
                     "signed count. The archetype labels are left distinct "
                     "(`alternating_rank_sum` against "
                     "`conditional_marginalization`) so the matcher's "
                     "'identical structures with different archetype ids' section "
                     "flags the pair -- that flag is the finding, not a defect.",
        conditions=["The space has finitely generated homology in each degree and "
                    "non-zero homology in only finitely many degrees",
                    "Betti numbers are taken as ranks over the integers, or "
                    "equivalently dimensions over the rationals"],
        failure_modes=[
            "The template cannot express (-1)^i, so nothing checks that the weights "
            "alternate; a reader who trusts the anonymized template alone would "
            "take the statement to be an arbitrary weighted sum.",
            "Betti numbers computed with field coefficients of positive "
            "characteristic can differ from the integral ranks (universal "
            "coefficients), and the alternating sum is nevertheless the same chi -- "
            "a coincidence that regularly misleads.",
            "For spaces with infinitely many non-zero Betti numbers the sum "
            "diverges and chi is undefined; regularized versions exist but are not "
            "this statement.",
        ],
        provenance=[POINCARE, HATCHER, MUNKRES_AT, MASSEY],
        inferential_links=links(
            entailed_by=["algtop.homology.chain_rank_nullity",
                         "algtop.homology.betti_number_rank"],
            composed_with=["algtop.invariants.euler_characteristic_complex",
                           "algtop.invariants.euler_characteristic_surface",
                           "algtop.invariants.euler_characteristic_valuation",
                           "probstat.probability.total_probability_partition"]),
        keywords=["Euler-Poincare formula", "Betti number", "alternating sum",
                  "homology", "rank", "topological invariant"],
    ),
    node(
        sid="algtop.homology.betti_number_rank",
        title="Betti Number as Rank of Cycles Modulo Boundaries",
        cls="definition", status="formal",
        discipline="algebraic_topology", subfield=ALGTOP_SUBFIELD,
        topic="homology", canonical_objects=ALGTOP_OBJECTS,
        ascii_="b_n = rank(Z_n) - rank(B_n)",
        latex="b_n = \\operatorname{rank} Z_n - \\operatorname{rank} B_n",
        forms=[
            form("quotient", "b_n = rank(H_n) = rank(Z_n / B_n)",
                 scope_note="Betti number as the rank of the homology group itself"),
            form("kernel_image", "b_n = rank(ker d_n) - rank(im d_{n+1})",
                 scope_note="Cycles are the kernel of the boundary map, boundaries the image of the next one"),
            form("dimension", "b_n = dim_Q (H_n (x) Q)",
                 scope_note="Rationalized form, which is what makes rank subtraction legitimate"),
            form("graph", "b_0 = number of connected components, b_1 = E - V + b_0",
                 scope_note="1-complex case; the circuit rank a GIS planar-graph index computes"),
        ],
        archetype="rank_difference",
        template="BETTI = CYCLERANK - BOUNDARYRANK",
        slots=[
            slot("BETTI", "variable", "component_rank"),
            slot("CYCLERANK", "variable", "cycle_group_rank"),
            slot("BOUNDARYRANK", "variable", "boundary_group_rank"),
        ],
        invariants=[
            "A difference of two ranks, both of free abelian groups; the "
            "subtraction is legitimate because rank is additive on short exact "
            "sequences of finitely generated abelian groups.",
            "Torsion contributes nothing to either term, so the definition "
            "deliberately discards information that the homology group retains. "
            "Betti numbers are a lossy shadow of homology, and this is where the "
            "loss happens.",
            "Non-negative, since boundaries are cycles: the subtrahend indexes a "
            "subgroup of the group the minuend indexes.",
            "All three slots are variable-like; no parameter or constant appears, "
            "which distinguishes this skeleton from the free-energy differences it "
            "otherwise resembles in shape.",
        ],
        symbols=[
            sym("b_n", "variable", "component_rank",
                "n-th Betti number.", 0),
            sym("Z_n", "set", "cycle_group",
                "Group of n-cycles: the kernel of the n-th boundary map.", 0),
            sym("B_n", "set", "boundary_group",
                "Group of n-boundaries: the image of the (n+1)-st boundary map.", 0),
        ],
        operators=[EQ, SUB],
        functionals=[RANK_FN],
        meaning="The n-th Betti number counts the independent n-dimensional holes: "
                "the cycles that are not themselves boundaries, measured by rank.",
        significance="A structural miss worth naming. The skeleton "
                     "`?0:V = +(?1:V, neg(?2:V))` -- a bare difference of two "
                     "same-category quantities -- matches nothing in the corpus, "
                     "even though the corpus is full of differences. The nearest "
                     "candidates all differ by having a parameter or a product on "
                     "the right: the free-energy nodes are "
                     "`?0:V = +(?1:V, neg(*(?2:V, ?3:V)))` and the "
                     "z-standardization divides. The lesson is that two-term "
                     "differences are too small to carry structure; they twin only "
                     "when the terms themselves have shape. That is a useful "
                     "negative result about where the twin thesis has content.",
        conditions=["The chain complex is of finitely generated free abelian groups",
                    "Ranks are taken over the integers"],
        failure_modes=[
            "Over a field of positive characteristic the 'Betti numbers' are "
            "dimensions and can exceed the integral ranks wherever there is "
            "matching torsion, so the same name denotes different numbers.",
            "For infinitely generated chain groups the ranks may be infinite and "
            "the difference undefined.",
            "The formula invites the belief that homology is determined by Betti "
            "numbers; the lens space pair L(7,1) and L(7,2) have equal Betti "
            "numbers and different homotopy types.",
        ],
        provenance=[HATCHER, MUNKRES_AT, POINCARE, MASSEY],
        inferential_links=links(
            entails=["algtop.homology.betti_alternating_sum"],
            composed_with=["algtop.homology.chain_rank_nullity",
                           "algtop.homotopy.homotopy_invariance"]),
        keywords=["Betti number", "rank", "cycle", "boundary", "homology",
                  "torsion"],
    ),
    node(
        sid="algtop.homology.chain_rank_nullity",
        title="Rank-Nullity for the Boundary Homomorphism",
        cls="theorem", status="derived",
        discipline="algebraic_topology", subfield=ALGTOP_SUBFIELD,
        topic="homology", canonical_objects=ALGTOP_OBJECTS,
        ascii_="rank(C_n) = rank(ker d_n) + rank(im d_n)",
        latex="\\operatorname{rank} C_n = \\operatorname{rank}(\\ker \\partial_n) + \\operatorname{rank}(\\operatorname{im} \\partial_n)",
        forms=[
            form("linear_algebra", "dim(V) = nullity(T) + rank(T)",
                 scope_note="The rank-nullity theorem of linear algebra, of which this is the chain-complex instance"),
            form("cycles", "rank(C_n) = rank(Z_n) + rank(B_{n-1})",
                 scope_note="Naming the kernel the cycles and the image the boundaries one dimension down"),
            form("exact_sequence", "0 -> Z_n -> C_n -> B_{n-1} -> 0",
                 scope_note="The short exact sequence whose splitting over Q gives the rank identity"),
        ],
        archetype="rank_decomposition",
        template="CHAINRANK = CYCLERANK + IMAGERANK",
        slots=[
            slot("CHAINRANK", "variable", "chain_group_rank"),
            slot("CYCLERANK", "variable", "kernel_rank"),
            slot("IMAGERANK", "variable", "image_rank"),
        ],
        invariants=[
            "A conservation statement: the rank of the source splits exactly into "
            "what the map kills and what it produces, with no remainder.",
            "Holds for any homomorphism of finitely generated free abelian groups, "
            "not just boundary maps; the topology enters only through which map is "
            "chosen.",
            "Summing this identity over all degrees with alternating signs is what "
            "makes the cell count and the Betti sum agree -- the telescoping is the "
            "proof of the Euler-Poincare formula.",
            "Symmetric in its two summands as written, which is a small lie the "
            "shape tells: kernel and image play very different roles even though "
            "addition does not care.",
        ],
        symbols=[
            sym("C_n", "set", "chain_group",
                "Group of n-chains: the free abelian group on the n-cells.", 0),
            sym("d_n", "variable", "boundary_map",
                "The n-th boundary homomorphism C_n -> C_{n-1}.", 0),
        ],
        operators=[EQ, ADD],
        functionals=[RANK_FN],
        meaning="Every n-chain either dies under the boundary map or survives into "
                "its image, and counting free generators respects that split "
                "exactly.",
        significance="Included as the engine under the Euler-Poincare formula "
                     "rather than for its twinning prospects, and the matcher "
                     "agrees: `?0:V = +(?1:V, ?2:V)` matches nothing, because the "
                     "corpus's other additive identities all have more terms "
                     "(`economics.macroeconomics.gdp_expenditure_identity` has four) "
                     "or a correction term (every inclusion-exclusion node). It is "
                     "the smallest non-trivial equation in either topology corpus "
                     "and it twins with nothing -- a useful calibration for how much "
                     "structure a template needs before a twin means anything. Its "
                     "real weight in the graph is inferential: summing it with "
                     "alternating signs is the one-line proof that the two "
                     "definitions of the Euler characteristic agree.",
        conditions=["Chain groups are finitely generated and free",
                    "Ranks are taken over the integers or dimensions over a field"],
        failure_modes=[
            "Over a ring that is not a PID the kernel need not be free and the rank "
            "identity can fail.",
            "Infinite-dimensional chain complexes need the statement recast in "
            "terms of exact sequences rather than rank arithmetic.",
        ],
        provenance=[MUNKRES_AT, HATCHER, MASSEY],
        inferential_links=links(
            entails=["algtop.homology.betti_alternating_sum"],
            composed_with=["algtop.homology.betti_number_rank"]),
        keywords=["rank-nullity", "boundary map", "chain complex", "kernel",
                  "image", "exact sequence"],
    ),
    node(
        sid="algtop.homotopy.fundamental_group_circle",
        title="Fundamental Group of the Circle",
        cls="theorem", status="formal",
        discipline="algebraic_topology", subfield=ALGTOP_SUBFIELD,
        topic="homotopy", canonical_objects=ALGTOP_OBJECTS,
        ascii_="pi_1(S^1) iso Z",
        latex="\\pi_1(S^1) \\cong \\mathbb{Z}",
        forms=[
            form("degree", "[loop] |-> winding number",
                 scope_note="The isomorphism is given by the winding number, which is why it is computable"),
            form("covering", "R -> S^1, t |-> exp(2*pi*i*t)",
                 scope_note="The universal cover whose deck transformation group is Z; the proof is the lifting criterion applied to it"),
            form("torus", "pi_1(T^2) iso Z x Z",
                 scope_note="Product form, obtained from this one by the product formula for pi_1"),
            form("homology", "H_1(S^1) iso Z",
                 scope_note="Abelianization; for the circle pi_1 is already abelian so the two agree"),
        ],
        archetype="invariant_evaluation",
        template="FUNDGROUP(CIRCLE) = INTEGERS",
        slots=[
            slot("CIRCLE", "constant", "base_space"),
            slot("INTEGERS", "constant", "invariant_value"),
        ],
        invariants=[
            "A point evaluation of an invariant, not a law: both slots are fixed "
            "objects, so the statement has no free variable at all. That is exactly "
            "why it twins with nothing and should not be expected to.",
            "The isomorphism is canonical once an orientation is chosen; the "
            "generator is the class of the identity loop.",
            "Infinite and abelian, which is what makes the circle detect holes that "
            "homology also detects; for higher spheres pi_1 is trivial while H_n is "
            "not, and the two invariants part company.",
            "The first computation in algebraic topology from which anything else "
            "follows -- Brouwer in dimension 2, the fundamental theorem of algebra, "
            "Borsuk-Ulam in dimension 1 -- so its value in the graph is as a source "
            "of entailments, not as a shape.",
        ],
        symbols=[
            sym("S^1", "constant", "base_space",
                "The circle: the one-dimensional sphere.", 0),
            sym("Z", "constant", "invariant_value",
                "The additive group of integers.", 0),
        ],
        operators=[ISO],
        functionals=[FUNDGROUP_FN],
        constants=[
            {"symbol": "S^1",
             "description": "The circle, taken with any basepoint since it is path-connected."},
            {"symbol": "Z",
             "description": "The infinite cyclic group, generated by the class of the once-around loop."},
        ],
        meaning="Loops on a circle are classified up to homotopy by how many times "
                "they wind around it, with sign; concatenating loops adds winding "
                "numbers.",
        significance="Deliberately the odd node out in this corpus, and an honest "
                     "reported miss. Its skeleton `?0:P = FUNDGROUP⟨?1:P⟩` has two "
                     "constant slots and one unshared head, so it cannot twin with "
                     "anything and nothing was engineered to make it. It is included "
                     "because a topology corpus that contained only additive "
                     "invariants would misrepresent the subject: the fundamental "
                     "group is non-abelian in general, is not a valuation, and "
                     "obeys none of the inclusion-exclusion structure that the rest "
                     "of this corpus twins on. Recording a statement the matcher "
                     "provably cannot use is part of keeping the twin counts "
                     "meaningful.",
        conditions=["The circle is taken with its standard topology",
                    "Basepoint suppressed because the space is path-connected"],
        failure_modes=[
            "The analogous statement fails for higher spheres: pi_1(S^n) is trivial "
            "for n >= 2, so 'the sphere's group counts its hole' does not "
            "generalize.",
            "pi_1 is not abelian in general (the figure eight gives a free group on "
            "two generators), so intuitions transferred from this abelian case "
            "mislead badly.",
            "Homotopy groups above degree 1 are not computable by this kind of "
            "covering-space argument; pi_n(S^2) is non-trivial for infinitely many "
            "n and remains unknown in general.",
        ],
        provenance=[HATCHER, POINCARE, MUNKRES_TOP, MASSEY],
        inferential_links=links(
            composed_with=["algtop.homotopy.homotopy_invariance",
                           "algtop.invariants.euler_characteristic_surface"]),
        keywords=["fundamental group", "circle", "winding number",
                  "covering space", "homotopy"],
    ),
    node(
        sid="algtop.homotopy.homotopy_invariance",
        title="Homotopy Invariance of Homology",
        cls="theorem", status="formal",
        discipline="algebraic_topology", subfield=ALGTOP_SUBFIELD,
        topic="homotopy", canonical_objects=ALGTOP_OBJECTS,
        ascii_="if X is homotopy equivalent to Y then H_*(X) iso H_*(Y)",
        latex="X \\simeq Y \\implies H_*(X) \\cong H_*(Y)",
        forms=[
            form("maps", "f homotopic to g implies f_* = g_* on homology",
                 scope_note="The underlying statement about induced maps, from which the space-level version follows"),
            form("contractible", "X contractible implies H_n(X) = 0 for n > 0",
                 scope_note="The degenerate case: a homotopy equivalence to a point"),
            form("deformation_retract", "A a deformation retract of X implies H_*(A) iso H_*(X)",
                 scope_note="The form used in practice, e.g. the annulus retracting to its core circle"),
            form("consequence", "X homeomorphic to Y implies H_*(X) iso H_*(Y)",
                 scope_note="Homeomorphism invariance as the weaker corollary, which is what makes homology usable as a classification tool"),
        ],
        archetype="invariance_under_equivalence",
        template="IMPLIES(HOMOTOPYEQUIVALENT(SPACE1, SPACE2), HOMOLOGY(SPACE1) = HOMOLOGY(SPACE2))",
        slots=[
            slot("SPACE1", "set", "space_operand"),
            slot("SPACE2", "set", "space_operand"),
        ],
        invariants=[
            "An implication, not an equation: the statement licenses a transfer and "
            "is not reversible. Spaces with isomorphic homology need not be "
            "homotopy equivalent, and the asymmetric IMPLIES root records that.",
            "The two space slots occur once in each position on both sides, so the "
            "content is entirely in the pairing: whatever relation holds of the "
            "pair on the left forces the equality on the right.",
            "The same shell -- a premise about a pair implying an equality of a "
            "functional applied to each -- is what every invariance statement in "
            "mathematics has, which is why the node is authored with a generic "
            "IMPLIES head rather than topology-specific notation.",
            "Homotopy equivalence is strictly coarser than homeomorphism, so this "
            "is the stronger of the two invariance claims and the weaker as a "
            "classification tool.",
        ],
        symbols=[
            sym("X", "set", "space_operand", "A topological space.", 0),
            sym("Y", "set", "space_operand", "A second topological space.", 0),
        ],
        operators=[EQ, IMPL, ISO],
        functionals=[IMPLIES_FN, HOMOTOPYEQ_FN, HOMOLOGY_FN],
        meaning="Homology cannot tell apart spaces that can be continuously "
                "deformed into one another; it is an invariant of homotopy type, "
                "not of the space as a point set.",
        significance="The node that explains why the rest of this corpus is allowed "
                     "to exist. Euler characteristics and Betti numbers are computed "
                     "from a chosen cell structure, and it is invariance that makes "
                     "the answer a property of the space. Structurally it is a "
                     "reported miss: `IMPLIES⟨HOMOTOPYEQUIVALENT⟨?0:V, ?1:V⟩, "
                     "HOMOLOGY⟨?0:V⟩ = HOMOLOGY⟨?1:V⟩⟩` shares its outer IMPLIES "
                     "shell with `logic.inference.modus_ponens`, "
                     "`settheory.order.subset_transitivity`, "
                     "`geotop.predicates.containment_transitivity`, "
                     "`geotop.predicates.adjacency_symmetry` and "
                     "`geotop.measure.area_monotonicity`, and twins with none of "
                     "them, because the premises differ in head and arity. The "
                     "graph now holds seven IMPLIES-rooted nodes across four "
                     "disciplines falling into six distinct skeletons, of which "
                     "exactly one pair twins. That is the near miss seed_logic.py "
                     "first recorded between modus ponens and subset transitivity, "
                     "now with enough instances to say that a matcher abstracting "
                     "over premise *heads* would be earning its keep.",
        conditions=["Singular homology with any coefficient group",
                    "No finiteness or CW hypothesis is needed; the theorem is "
                    "general"],
        failure_modes=[
            "The converse is false: the Poincare sphere has the homology of S^3 and "
            "is not homotopy equivalent to it, which is exactly the failure that "
            "made the Poincare conjecture a conjecture.",
            "Homotopy invariance means homology cannot detect anything about "
            "embedding or metric structure; knot complements in S^3 all have the "
            "same homology, so knot theory needs finer invariants.",
            "Naive dimension arguments break: R^n is contractible for every n, so "
            "homology alone does not see dimension.",
        ],
        provenance=[HATCHER, MUNKRES_AT, MASSEY, POINCARE],
        inferential_links=links(
            entails=[],
            composed_with=["algtop.homology.betti_number_rank",
                           "algtop.invariants.euler_characteristic_surface",
                           "algtop.homotopy.fundamental_group_circle"]),
        keywords=["homotopy invariance", "homology", "deformation retract",
                  "homotopy equivalence", "functor"],
    ),
]

# --------------------------------------------------------------------------
# GEOSPATIAL TOPOLOGY
# --------------------------------------------------------------------------

GEOTOP_NODES = [
    node(
        sid="geotop.polyhedra.euler_polyhedron_formula",
        title="Euler's Polyhedron Formula",
        cls="theorem", status="formal",
        discipline="geospatial_topology", subfield=GEOTOP_SUBFIELD,
        topic="planar_subdivision", canonical_objects=GEOTOP_OBJECTS,
        ascii_="V - E + F = 2",
        latex="V - E + F = 2",
        forms=[
            form("unicode", "V − E + F = 2"),
            form("planar_graph", "V - E + F = 2 with F counting the unbounded face",
                 scope_note="Planar-graph form; the outer face must be counted, which is the commonest implementation bug in a topology-aware GIS"),
            form("subdivision", "NODES - EDGES + FACES = 1 + COMPONENTS",
                 scope_note="Planar subdivision with several connected components, the form an actual coverage-validation routine needs"),
            form("genus", "V - E + F = 2 - 2*GENUS",
                 scope_note="Polyhedra of higher genus; the constant 2 is chi(S^2) and nothing more"),
            form("descartes", "sum of angular defects = 4*pi",
                 scope_note="Descartes' theorem on the total angular defect, equivalent to the formula and roughly a century earlier"),
        ],
        archetype="alternating_cell_count_fixed",
        template="VERTICES - EDGES + FACES = 2",
        slots=[
            slot("VERTICES", "variable", "zero_cell_count"),
            slot("EDGES", "variable", "one_cell_count"),
            slot("FACES", "variable", "two_cell_count"),
        ],
        invariants=[
            "The right-hand side is a fixed number, not a slot: the theorem's whole "
            "force is that the alternating count is *always* 2, for every "
            "subdivision of a topological sphere.",
            "Invariant under refinement: adding a vertex on an edge adds one vertex "
            "and one edge, adding a diagonal adds one edge and one face. Every "
            "legal local move preserves the alternating sum, which is both the "
            "proof and the reason a GIS can subdivide a coverage freely.",
            "The value 2 is chi(S^2). Sphere-topology is the hypothesis, not "
            "convexity: any subdivision of any surface homeomorphic to a sphere "
            "works, and toroidal ones give 0.",
            "Constrains realizable planar graphs: with V >= 3 it forces E <= 3V - 6, "
            "which is why planar-graph spatial indexes have linear-size edge "
            "counts.",
        ],
        symbols=[
            sym("V", "variable", "zero_cell_count",
                "Number of vertices (nodes) of the subdivision.", 0),
            sym("E", "variable", "one_cell_count",
                "Number of edges (arcs) of the subdivision.", 0),
            sym("F", "variable", "two_cell_count",
                "Number of faces, including the unbounded exterior face for a "
                "planar drawing.", 0),
        ],
        operators=[EQ, ADD, SUB],
        constants=[{"symbol": "2", "value": 2,
                    "description": "The Euler characteristic of the sphere; the "
                                   "value the alternating count is pinned to."}],
        meaning="For any subdivision of a sphere -- equivalently any connected "
                "planar drawing counted with its outer face -- vertices minus edges "
                "plus faces is always two.",
        significance="The oldest node in either topology corpus and the one that "
                     "produced the most instructive tooling failure. It is exactly "
                     "`algtop.invariants.euler_characteristic_complex` with the "
                     "invariant slot bound to the literal 2, and *neither* matcher "
                     "reports the relation. match_signatures.py compares skeletons: "
                     "`2 = +(?0:V, ?1:V, neg(?2:V))` against "
                     "`?0:V = +(?1:V, ?2:V, neg(?3:V))`, and a numeric literal is "
                     "not a slot, so no twin at typed, family or shape level. "
                     "specialize.py *does* find the match -- the pattern slot "
                     "EULERCHAR binds the term 2 and the three counts bind "
                     "one-to-one -- but discards it, because it reports only "
                     "matches that used argument absorption or identity-element "
                     "binding, and this used neither. A plain slot-to-literal bind "
                     "is the single most common way a general law becomes a special "
                     "case, and it is precisely the case both tools drop. The edge "
                     "is asserted by hand via special_case_of/generalizes and the "
                     "gap is filed in docs/BACKLOG.md.",
        conditions=["The polyhedron's surface is homeomorphic to a sphere",
                    "The subdivision is connected and every face is a topological "
                    "disc",
                    "For a planar drawing, the unbounded face is counted"],
        failure_modes=[
            "Fails for toroidal and higher-genus polyhedra, where the count is "
            "2 - 2g; a GIS coverage on a torus-like topology (a road network on a "
            "sphere with tunnels) breaks validation routines that hard-code 2.",
            "Fails for disconnected subdivisions, which give 1 + (number of "
            "components); real-world coverages with islands hit this constantly.",
            "Fails for faces that are not discs -- a face with a hole (a polygon "
            "with an interior ring) must be cut before the count applies, which is "
            "why OGC simple features distinguish shells from holes.",
            "Lakatos's Proofs and Refutations is a book-length catalogue of the "
            "monsters that arise when 'polyhedron' is left informal; the history is "
            "a warning about stating this node's hypotheses casually.",
        ],
        provenance=[EULER1758, LAKATOS, RICHESON, WORBOYS],
        inferential_links=links(
            special_case_of=["algtop.invariants.euler_characteristic_complex"],
            composed_with=["geotop.point_set.interior_boundary_exterior_partition"]),
        keywords=["Euler formula", "polyhedron", "planar graph",
                  "planar subdivision", "coverage validation", "topological invariant"],
    ),
    node(
        sid="geotop.point_set.interior_boundary_exterior_partition",
        title="Interior-Boundary-Exterior Partition of a Region",
        cls="theorem", status="formal",
        discipline="geospatial_topology", subfield=GEOTOP_SUBFIELD,
        topic="point_set_relations", canonical_objects=GEOTOP_OBJECTS,
        ascii_="interior(A) union boundary(A) union exterior(A) = U",
        latex="A^{\\circ} \\cup \\partial A \\cup A^{e} = U",
        forms=[
            form("unicode", "A° ∪ ∂A ∪ Aᵉ = U"),
            form("disjointness",
                 "interior(A) inter boundary(A) = emptyset, and both are disjoint from exterior(A)",
                 scope_note="The other half of the partition: the three parts are pairwise disjoint, so together with exhaustiveness they partition the plane"),
            form("closure", "closure(A) = interior(A) union boundary(A)",
                 scope_note="Equivalent packaging; the exterior is then the complement of the closure"),
            form("nine_intersection",
                 "M(A,B)[i][j] = emptiness of (part_i(A) inter part_j(B)) for i, j in {interior, boundary, exterior}",
                 scope_note="The DE-9IM matrix this partition makes possible: three parts each side gives nine cells, and the eight realizable patterns for two regions are the OGC named predicates"),
        ],
        archetype="exhaustive_partition",
        template="JOIN(INTERIOR(REGION), JOIN(BOUNDARY(REGION), EXTERIOR(REGION))) = UNIVERSE",
        slots=[
            slot("REGION", "set", "region_operand"),
            slot("UNIVERSE", "constant", "top_element"),
        ],
        invariants=[
            "Exhaustive: every point of the ambient space lies in exactly one of "
            "the three parts, so the decomposition is a partition and not merely a "
            "cover.",
            "The single region slot occurs three times, once under each part "
            "operator. That repetition is the content: the three parts are three "
            "views of one object, which is what lets DE-9IM index them by name.",
            "The top element sits in a constant (parameter-like) slot, exactly as "
            "TRUTH and UNIVERSE do in data/logic and data/set_theory, so this node "
            "shares its treatment of the ambient universe with the Boolean corpora.",
            "Purely topological: it uses only interior, closure and complement, so "
            "it survives any homeomorphism of the plane. That invariance is the "
            "reason GIS calls these relations topological in the first place.",
            "The three-part split is what separates the nine-intersection model from "
            "the earlier four-intersection model; without the exterior, 'disjoint' "
            "and 'meets' cannot be told apart.",
        ],
        symbols=[
            sym("A", "set", "region_operand",
                "A region: a closed, regular subset of the plane, in OGC terms a "
                "simple feature geometry.", 0),
            sym("U", "constant", "top_element",
                "The ambient space, normally the plane or the sphere.", 0),
        ],
        operators=[EQ, UNION, INTER, COMPL],
        functionals=[JOIN_FN, INTERIOR_FN, BOUNDARY_FN, EXTERIOR_FN, CLOSURE_FN],
        constants=[{"symbol": "U",
                    "description": "The ambient embedding space; every DE-9IM "
                                   "statement is relative to a fixed choice of it, "
                                   "just as every complement in data/set_theory is."}],
        meaning="Every point of the plane is either inside a region, on its "
                "boundary, or outside it; those three parts cover the plane and "
                "overlap nowhere.",
        significance="The vocabulary node for the DE-9IM predicates: the "
                     "nine-intersection matrix is exactly the table of "
                     "MEET(part_i(A), part_j(B)) values, so this partition is what "
                     "makes the whole predicate algebra well posed. Structurally it "
                     "is a reported miss and expected to be one. Its skeleton "
                     "`?0:P = JOIN⟨INTERIOR⟨?1:V⟩, JOIN⟨BOUNDARY⟨?1:V⟩, "
                     "EXTERIOR⟨?1:V⟩⟩⟩` is one functional layer away from "
                     "`settheory.boolean_laws.complement_laws` "
                     "(`?0:P = MEET⟨?1:V, NEG⟨?1:V⟩⟩`) -- both say a thing and its "
                     "opposite exhaust the universe -- but the resemblance is "
                     "conceptual, not mechanical: the two templates differ in head "
                     "(JOIN against MEET), in arity and in the functional layer "
                     "interposed on each operand, so no reasonable matcher should "
                     "relate them and none does. It is recorded as a miss rather "
                     "than quietly dropped because the temptation to rewrite the "
                     "partition into a two-part `MEET(CLOSURE(R), NEG(CLOSURE(R))) "
                     "= EMPTYSET` purely to manufacture a match was real, and "
                     "taking it would have replaced the statement DE-9IM actually "
                     "needs -- three parts, nine cells -- with one that twins.",
        conditions=["A fixed ambient space U, normally the plane R^2 or the sphere",
                    "Regions are regular closed sets, so that boundary and interior "
                    "behave as intended",
                    "The parts are taken with respect to the same topology "
                    "throughout"],
        failure_modes=[
            "Non-regular geometries break it in practice: a polygon with a dangling "
            "edge or a zero-width sliver has interior points that a naive "
            "implementation places on the boundary, which is why OGC requires "
            "simple features to be valid before predicates are evaluated.",
            "Floating-point coordinates make boundary membership undecidable in "
            "practice; every production GIS carries a tolerance, and with a "
            "tolerance the three parts genuinely overlap.",
            "The partition is relative to the chosen ambient space: a curve in R^3 "
            "has empty interior, so a 'region' embedded one dimension too high "
            "collapses into its own boundary.",
        ],
        provenance=[EGENHOFER, EGENHOFER_HERRING, MUNKRES_TOP, OGC_SFA],
        inferential_links=links(
            entails=["geotop.predicates.de9im_disjoint"],
            composed_with=["geotop.predicates.adjacency_symmetry",
                           "geotop.polyhedra.euler_polyhedron_formula",
                           "settheory.boolean_laws.complement_laws"]),
        keywords=["interior", "boundary", "exterior", "DE-9IM",
                  "nine-intersection model", "point-set topology", "partition"],
    ),
    node(
        sid="geotop.predicates.containment_transitivity",
        title="Transitivity of Spatial Containment",
        cls="theorem", status="derived",
        discipline="geospatial_topology", subfield=GEOTOP_SUBFIELD,
        topic="predicate_algebra", canonical_objects=GEOTOP_OBJECTS,
        ascii_="if (A within B) and (B within C) then (A within C)",
        latex="A \\sqsubseteq B \\ \\land\\ B \\sqsubseteq C \\implies A \\sqsubseteq C",
        forms=[
            form("ogc", "ST_Within(A, B) and ST_Within(B, C) implies ST_Within(A, C)",
                 scope_note="OGC Simple Features spelling; the rule a spatial index uses to prune containment queries"),
            form("point_set",
                 "(forall p. p in A implies p in B) and (forall p. p in B implies p in C) implies (forall p. p in A implies p in C)",
                 scope_note="Unfolded to point membership, where the proof is hypothetical syllogism applied pointwise"),
            form("de9im", "within(A, B) iff I(A) inter I(B) non-empty and I(A) inter E(B) empty and B(A) inter E(B) empty",
                 scope_note="The DE-9IM cell pattern defining `within`, which is what makes the relation a partial order"),
            form("lattice", "(A inter B = A) and (B inter C = B) implies (A inter C = A)",
                 scope_note="Containment expressed through meet, which is how LEQ is defined in the shared template"),
        ],
        archetype="order_transitivity",
        template=render(TPL_ORDER_TRANSITIVITY, a="REGA", b="REGB", c="REGC"),
        slots=[
            slot("REGA", "set", "region_operand"),
            slot("REGB", "set", "region_operand"),
            slot("REGC", "set", "region_operand"),
        ],
        invariants=[
            "The middle region appears twice, as the consequent of the first "
            "premise and the antecedent of the second: transitivity is the chaining "
            "pattern and the repeated slot is the whole content.",
            "With reflexivity and antisymmetry it makes containment a partial "
            "order, which is the order underlying every MEET/JOIN statement in this "
            "corpus.",
            "Not an equation and not reversible, which puts it in the same "
            "structural family as modus ponens rather than with the additive "
            "identities.",
            "The template is scripts/seed_logic.py's TPL_SUBSET_TRANSITIVITY "
            "verbatim, with only the slot names changed. The twin therefore holds "
            "by construction and cannot drift.",
        ],
        symbols=[
            sym("A", "set", "region_operand", "A region (simple feature geometry).", 0),
            sym("B", "set", "region_operand", "A second region.", 0),
            sym("C", "set", "region_operand", "A third region.", 0),
        ],
        operators=[SUBSET, AND, IMPL],
        functionals=[IMPLIES_FN, MEET_FN, LEQ_FN],
        meaning="Containment chains: a parcel inside a block inside a district is "
                "inside that district.",
        significance="A prediction from another corpus, cashed. "
                     "scripts/seed_logic.py's commentary on "
                     "`settheory.order.subset_transitivity` says the lattice-"
                     "abstract LEQ head was chosen 'precisely so that a future "
                     "node ... would twin with this one exactly, without either "
                     "corpus being rewritten'. This is that node, written months "
                     "later in an unrelated subject, and it twins exactly: "
                     "`IMPLIES⟨MEET⟨LEQ⟨?0:V, ?1:V⟩, LEQ⟨?1:V, ?2:V⟩⟩, LEQ⟨?0:V, "
                     "?2:V⟩⟩`, same archetype id, no edits to data/set_theory. That "
                     "is the strongest available evidence that the abstract-head "
                     "convention is doing real work rather than being a way to "
                     "manufacture matches after the fact -- the target was fixed "
                     "before the source existed. Practically, this is also the rule "
                     "an R-tree relies on to prune containment queries, so the "
                     "abstract order and the production index are the same fact.",
        conditions=["A, B, C are valid simple-feature geometries in one coordinate "
                    "reference system",
                    "Containment is the OGC `within` relation, taken in its "
                    "non-strict sense"],
        failure_modes=[
            "Fails under mixed coordinate reference systems: 'within' computed "
            "after two different projections is not transitive, and this is a "
            "routine production bug rather than a theoretical curiosity.",
            "Tolerance-based implementations break transitivity: A within B and B "
            "within C each by a hair can leave A outside C by two hairs.",
            "The strict relation `properly within` is transitive but not reflexive, "
            "so results stated for `within` do not transfer verbatim -- the same "
            "trap as proper subset inclusion in data/set_theory.",
        ],
        provenance=[EGENHOFER, OGC_SFA, CLEMENTINI, DAVEY_PRIESTLEY],
        inferential_links=links(
            composed_with=["geotop.measure.area_monotonicity",
                           "settheory.order.subset_transitivity",
                           "logic.inference.modus_ponens"]),
        keywords=["containment", "transitivity", "partial order", "within",
                  "DE-9IM", "spatial predicate", "lattice order"],
    ),
    node(
        sid="geotop.predicates.adjacency_symmetry",
        title="Symmetry of Spatial Adjacency",
        cls="theorem", status="derived",
        discipline="geospatial_topology", subfield=GEOTOP_SUBFIELD,
        topic="predicate_algebra", canonical_objects=GEOTOP_OBJECTS,
        ascii_="if A touches B then B touches A",
        latex="A \\mathrel{\\mathsf{touches}} B \\implies B \\mathrel{\\mathsf{touches}} A",
        forms=[
            form("ogc", "ST_Touches(A, B) = ST_Touches(B, A)",
                 scope_note="OGC spelling; the equality form, which is the implication plus its converse"),
            form("de9im", "touches(A, B) iff I(A) inter I(B) empty and (B(A) inter B(B) non-empty or I(A) inter B(B) non-empty or B(A) inter I(B) non-empty)",
                 scope_note="DE-9IM definition; symmetry is visible as invariance of the pattern under transposing the matrix"),
            form("matrix_transpose", "M(A, B) = transpose(M(B, A))",
                 scope_note="The general fact: swapping the arguments transposes the nine-intersection matrix, so a predicate is symmetric exactly when its pattern is transpose-invariant"),
            form("adjacency_graph", "the region adjacency graph is undirected",
                 scope_note="The data-structure consequence: a topological coverage stores each shared edge once"),
        ],
        archetype="relation_symmetry",
        template="IMPLIES(TOUCHES(REGA, REGB), TOUCHES(REGB, REGA))",
        slots=[
            slot("REGA", "set", "region_operand"),
            slot("REGB", "set", "region_operand"),
        ],
        invariants=[
            "The two slots swap positions between premise and conclusion and appear "
            "nowhere else: argument exchange is the entire content of the "
            "statement.",
            "It is stated as an implication rather than an equality because the "
            "matcher treats call arguments as ordered, so the swap must be written "
            "out to be visible as structure. Recording symmetry this way is the "
            "corpus's only current means of saying that a head is commutative -- "
            "the limitation is on record in docs/BACKLOG.md.",
            "Symmetry plus irreflexivity makes adjacency a graph relation rather "
            "than an order, which is what separates it from containment.",
            "Follows from the transpose identity for the nine-intersection matrix: "
            "the touches pattern is invariant under transposition, and every "
            "symmetric DE-9IM predicate is symmetric for that reason.",
        ],
        symbols=[
            sym("A", "set", "region_operand", "A region.", 0),
            sym("B", "set", "region_operand", "A second region.", 0),
        ],
        operators=[IMPL],
        functionals=[IMPLIES_FN, TOUCHES_FN],
        meaning="If one region touches another along their shared boundary, the "
                "second touches the first: adjacency does not have a direction.",
        significance="Included to probe whether the corpus can express commutativity "
                     "of a call head at all, and the answer is: only by writing the "
                     "swap out by hand. The matcher flattens and sorts only the `+` "
                     "and `*` operators; a call keeps its argument order, so "
                     "TOUCHES(A, B) and TOUCHES(B, A) are different subtrees and "
                     "this node's whole point is to state that they are "
                     "interchangeable. It twins with nothing -- "
                     "`IMPLIES⟨TOUCHES⟨?0:V, ?1:V⟩, TOUCHES⟨?1:V, ?0:V⟩⟩` is the "
                     "only symmetry statement in the graph -- but it is the first "
                     "node anywhere in data/ that would let a future "
                     "commutative-head declaration be checked against something. "
                     "Every MEET and JOIN in the Boolean corpora quietly assumes "
                     "exactly this property of its head and none of them says so.",
        conditions=["A and B are valid simple-feature geometries with non-empty "
                    "interiors",
                    "Both are taken in the same coordinate reference system"],
        failure_modes=[
            "Undefined in the OGC sense when both arguments are points: two points "
            "cannot touch, since the relation requires a boundary intersection.",
            "Tolerance-based implementations can break symmetry when the two "
            "geometries have different vertex densities, so ST_Touches(A, B) and "
            "ST_Touches(B, A) genuinely disagree in production systems.",
            "Adjacency is not transitive, and the habit of reading 'related' "
            "relations as orders leads to treating an adjacency graph as a "
            "hierarchy.",
        ],
        provenance=[EGENHOFER, CLEMENTINI, OGC_SFA, WORBOYS],
        inferential_links=links(
            entailed_by=[],
            composed_with=["geotop.point_set.interior_boundary_exterior_partition",
                           "geotop.predicates.de9im_disjoint"]),
        keywords=["adjacency", "touches", "symmetry", "DE-9IM",
                  "region adjacency graph", "spatial predicate"],
    ),
    node(
        sid="geotop.predicates.de9im_disjoint",
        title="DE-9IM Disjointness Predicate",
        cls="definition", status="formal",
        discipline="geospatial_topology", subfield=GEOTOP_SUBFIELD,
        topic="predicate_algebra", canonical_objects=GEOTOP_OBJECTS,
        ascii_="disjoint(A, B) iff A inter B = emptyset",
        latex="\\mathsf{disjoint}(A,B) \\iff A \\cap B = \\emptyset",
        forms=[
            form("unicode", "A ∩ B = ∅"),
            form("de9im_pattern", "M(A, B) matches FF*FF****",
                 scope_note="The DE-9IM pattern for disjoint: interiors and boundaries all miss each other, exterior cells unconstrained"),
            form("negation", "disjoint(A, B) iff not intersects(A, B)",
                 scope_note="Disjoint and intersects are complementary predicates; OGC defines one as the negation of the other"),
            form("interiors", "interior(A) inter interior(B) = emptyset",
                 scope_note="The weaker interior-only condition, which permits touching; this is what distinguishes `disjoint` from `not overlaps`"),
        ],
        archetype="empty_meet_predicate",
        template="MEET(REGA, REGB) = EMPTYSET",
        slots=[
            slot("REGA", "set", "region_operand"),
            slot("REGB", "set", "region_operand"),
            slot("EMPTYSET", "constant", "bottom_element"),
        ],
        invariants=[
            "The meet lands on the bottom element of the lattice: disjointness is "
            "the statement that two regions have nothing below them in common.",
            "Symmetric in the two operands as a mathematical fact; the shared "
            "argument-order convention from scripts/seed_logic.py is followed so "
            "that the written form is the canonical one.",
            "The bottom element sits in a constant (parameter-like) slot, matching "
            "the treatment of FALSITY and EMPTYSET in the Boolean corpora.",
            "This is precisely the hypothesis under which the correction term of "
            "geotop.measure.area_inclusion_exclusion vanishes, so the two nodes are "
            "the general case and its degenerate one.",
            "Strictly stronger than 'the interiors are disjoint': two regions "
            "sharing only a boundary edge are adjacent, not disjoint, and the "
            "difference is one DE-9IM cell.",
        ],
        symbols=[
            sym("A", "set", "region_operand", "A region.", 0),
            sym("B", "set", "region_operand", "A second region.", 0),
        ],
        operators=[EQ, INTER],
        functionals=[MEET_FN],
        constants=[{"symbol": "emptyset",
                    "description": "The empty geometry: the least element of the "
                                   "lattice of regions, the same bottom element "
                                   "data/set_theory and data/logic use."}],
        meaning="Two regions are disjoint when they share no point at all -- not "
                "even a boundary point.",
        significance="The second instance of the corpus's newly identified tooling "
                     "gap, and the reason it is worth a backlog entry rather than a "
                     "shrug. This template *generalizes* "
                     "`settheory.boolean_laws.complement_laws` "
                     "(`MEET(SETA, NEG(SETA)) = EMPTYSET`) by the single "
                     "substitution REGB -> NEG(REGA): a set and its complement are "
                     "the extreme case of two disjoint sets. specialize.py performs "
                     "exactly that match internally and then throws it away, "
                     "because the match used neither argument absorption nor "
                     "identity-element binding -- it was a plain slot-to-subtree "
                     "bind, and the tool's filter ('anything matchable without them "
                     "is an exact twin and already in the skeleton report') is "
                     "false for patterns whose shapes differ for other reasons. "
                     "Two independent instances of the same false assumption, in "
                     "one seeding pass, from a corpus written without knowledge of "
                     "the filter.",
        conditions=["A and B are valid simple-feature geometries in one coordinate "
                    "reference system",
                    "Emptiness is exact, not up to tolerance"],
        failure_modes=[
            "Floating-point geometry makes exact emptiness undecidable; every "
            "production implementation is really testing 'disjoint up to a snapping "
            "tolerance', which is not a topological relation and is not transitive "
            "in any useful sense.",
            "Bounding-box prefilters answer a different question: box-disjoint "
            "implies disjoint, but not conversely, and treating the prefilter as "
            "the predicate is the classic spatial-index bug.",
            "The empty geometry is disjoint from everything including itself, which "
            "makes several OGC predicates degenerate and is normally excluded by "
            "hand.",
        ],
        provenance=[EGENHOFER, OGC_SFA, CLEMENTINI, HALMOS_MEASURE],
        inferential_links=links(
            entailed_by=["geotop.point_set.interior_boundary_exterior_partition"],
            composed_with=["geotop.measure.area_inclusion_exclusion",
                           "geotop.predicates.adjacency_symmetry",
                           "settheory.boolean_laws.complement_laws"]),
        keywords=["disjoint", "DE-9IM", "intersection", "empty geometry",
                  "spatial predicate", "lattice meet"],
    ),
    node(
        sid="geotop.measure.area_inclusion_exclusion",
        title="Area of a Union (Inclusion-Exclusion for Overlapping Regions)",
        cls="theorem", status="derived",
        discipline="geospatial_topology", subfield=GEOTOP_SUBFIELD,
        topic="measure_on_regions", canonical_objects=GEOTOP_OBJECTS,
        ascii_="area(A union B) = area(A) + area(B) - area(A inter B)",
        latex="\\mu(A \\cup B) = \\mu(A) + \\mu(B) - \\mu(A \\cap B)",
        forms=[
            form("unicode", "μ(A ∪ B) = μ(A) + μ(B) − μ(A ∩ B)"),
            form("disjoint_case", "area(A union B) = area(A) + area(B) when A inter B = emptyset",
                 scope_note="Finite additivity for disjoint regions, the degenerate case and the one a tessellated coverage relies on"),
            form("ogc", "ST_Area(ST_Union(A, B)) = ST_Area(A) + ST_Area(B) - ST_Area(ST_Intersection(A, B))",
                 scope_note="The identity as a SQL/MM invariant; a useful regression test for a geometry engine"),
            form("buffer", "area(buffer(A, r) union buffer(B, r)) <= area(buffer(A, r)) + area(buffer(B, r))",
                 scope_note="Subadditivity for buffers, which is this identity with the correction term dropped to an inequality"),
            form("n_regions", "area(union_i A_i) = sum over non-empty S of (-1)^(|S|+1) * area(inter_{i in S} A_i)",
                 scope_note="General form; the signs are the Moebius function of the Boolean lattice, exactly as in the counting case"),
        ],
        archetype="inclusion_exclusion_correction",
        template=render(TPL_INCLUSION_EXCLUSION, a="REGA", b="REGB"),
        slots=[
            slot("REGA", "set", "region_operand"),
            slot("REGB", "set", "region_operand"),
        ],
        invariants=[
            "Additive with a single correction term: the overlap is counted twice "
            "by the naive sum and subtracted once, so the identity is exact and not "
            "a bound.",
            "Reduces to plain additivity exactly when MEET(A, B) = EMPTYSET, which "
            "is the statement of geotop.predicates.de9im_disjoint.",
            "Symmetric in the two regions, since MEET and JOIN are.",
            "Area is a valuation on the lattice of regions: monotone, and modular "
            "in the sense this identity states. Every valuation -- counting "
            "measure, probability, Lebesgue area, the Euler characteristic -- "
            "satisfies the same equation, which is why the CARD head is shared "
            "rather than renamed.",
            "Extends to n regions with alternating signs over all non-empty subsets, "
            "the Moebius function of the Boolean lattice.",
        ],
        symbols=[
            sym("A", "set", "region_operand",
                "A measurable planar region.", 0),
            sym("B", "set", "region_operand",
                "A second measurable planar region.", 0),
        ],
        operators=[EQ, ADD, SUB, INTER, UNION, MEASURE],
        functionals=[CARD_AREA, MEET_FN, JOIN_FN],
        meaning="The area covered by two regions together is the sum of their areas "
                "less the area they share, because the overlap would otherwise be "
                "paid for twice.",
        significance="The node this corpus was most confident about, and it "
                     "delivers: an exact typed twin with "
                     "`settheory.cardinality.inclusion_exclusion_two_sets`, "
                     "`infotheory.mutualinfo.entropy_inclusion_exclusion` and "
                     "`algtop.invariants.euler_characteristic_valuation`, on the "
                     "skeleton `CARD⟨JOIN⟨?0:V, ?1:V⟩⟩ = +(CARD⟨?0:V⟩, CARD⟨?1:V⟩, "
                     "neg(CARD⟨MEET⟨?0:V, ?1:V⟩⟩))`. Four disciplines, one "
                     "skeleton, and the reason is not resemblance: counting "
                     "measure, Yeung's I-measure, Lebesgue area and the Euler "
                     "characteristic are four valuations on lattices, and "
                     "inclusion-exclusion is a theorem about valuations that "
                     "mentions none of them. It is also the most operational node "
                     "in the geospatial corpus -- double-counting overlapping "
                     "polygons is the single commonest error in area reporting from "
                     "a GIS, and the correction term is what a dissolve operation "
                     "computes.",
        conditions=["A and B are Lebesgue-measurable regions of finite area",
                    "Area is planar Lebesgue measure, or any finite modular "
                    "valuation on the lattice of regions",
                    "Both geometries are valid and in one coordinate reference "
                    "system"],
        failure_modes=[
            "Regions of infinite area make the subtraction meaningless; the "
            "identity needs finiteness, not merely measurability.",
            "Areas computed after different map projections are not comparable, so "
            "the identity holds per projection and fails across a reprojection "
            "boundary -- an equal-area projection is required before the arithmetic "
            "means anything on the sphere.",
            "The n-region expansion has 2^n - 1 terms and is numerically unstable "
            "when many similar-sized overlaps cancel; production dissolve "
            "operations compute the union geometry instead, for good reason.",
            "Transplanting the identity to a submodular set function (viewshed "
            "coverage, sensor coverage with occlusion) turns it into an "
            "inequality.",
        ],
        provenance=[HALMOS_MEASURE, ROTA, KLAIN_ROTA, STANLEY, OGC_SFA],
        inferential_links=links(
            entails=["geotop.measure.area_monotonicity"],
            composed_with=["geotop.predicates.de9im_disjoint",
                           "algtop.invariants.euler_characteristic_valuation",
                           "settheory.cardinality.inclusion_exclusion_two_sets",
                           "infotheory.mutualinfo.entropy_inclusion_exclusion"]),
        keywords=["inclusion-exclusion", "area", "union", "overlap", "valuation",
                  "modularity", "dissolve"],
    ),
    node(
        sid="geotop.measure.area_monotonicity",
        title="Monotonicity of Area under Containment",
        cls="theorem", status="derived",
        discipline="geospatial_topology", subfield=GEOTOP_SUBFIELD,
        topic="measure_on_regions", canonical_objects=GEOTOP_OBJECTS,
        ascii_="if (A within B) then area(A) <= area(B)",
        latex="A \\sqsubseteq B \\implies \\mu(A) \\le \\mu(B)",
        forms=[
            form("difference", "area(B) - area(A) = area(B minus A) when A within B",
                 scope_note="The sharper form: the gap is itself an area, which is what makes monotonicity follow from non-negativity"),
            form("buffer", "if r <= s then area(buffer(A, r)) <= area(buffer(A, s))",
                 scope_note="Buffer monotonicity: buffering by a larger radius contains buffering by a smaller one, so areas are ordered"),
            form("union", "area(A) <= area(A union B)",
                 scope_note="Union monotonicity, the instance obtained by taking the larger region to be a union"),
            form("subadditivity", "area(A union B) <= area(A) + area(B)",
                 scope_note="The companion inequality, which is inclusion-exclusion with the non-negative correction term dropped"),
        ],
        archetype="monotone_valuation",
        template="IMPLIES(LEQ(REGA, REGB), CARD(REGA) <= CARD(REGB))",
        slots=[
            slot("REGA", "set", "region_operand"),
            slot("REGB", "set", "region_operand"),
        ],
        invariants=[
            "An order-preserving map: the lattice order on the left is carried to "
            "the numeric order on the right, which is exactly what 'monotone "
            "valuation' means.",
            "Two orders appear in one statement and they are different orders -- "
            "LEQ between regions, `<=` between reals. The template keeps them "
            "typographically distinct on purpose, since collapsing them would claim "
            "a structural identity that does not hold.",
            "Follows from inclusion-exclusion plus non-negativity of area: "
            "area(B) = area(A) + area(B minus A) and the second term cannot be "
            "negative.",
            "This is where area and the Euler characteristic part company. Area is "
            "monotone; chi is not, since a subcomplex can easily have larger chi "
            "than the complex containing it. The inclusion-exclusion twin they "
            "share uses only modularity, and monotonicity is the extra property "
            "that measures have and general valuations do not.",
        ],
        symbols=[
            sym("A", "set", "region_operand", "A measurable region.", 0),
            sym("B", "set", "region_operand",
                "A second measurable region containing the first.", 0),
        ],
        operators=[LE, IMPL, SUBSET, MEASURE],
        functionals=[IMPLIES_FN, LEQ_FN, CARD_AREA],
        meaning="A region contained in another cannot have more area: enlarging a "
                "footprint never shrinks it.",
        significance="The node that keeps the valuation twin honest. Because "
                     "`geotop.measure.area_inclusion_exclusion` and "
                     "`algtop.invariants.euler_characteristic_valuation` share a "
                     "skeleton exactly, a reader could conclude that area and the "
                     "Euler characteristic are interchangeable. They are not, and "
                     "this node is the difference: area is monotone and chi is not. "
                     "Structurally it is a reported miss -- "
                     "`IMPLIES⟨LEQ⟨?0:V, ?1:V⟩, CARD⟨?0:V⟩ <= CARD⟨?1:V⟩⟩` matches "
                     "nothing: it and `algtop.homotopy.homotopy_invariance` are the "
                     "only two statements in the graph that nest a relation inside "
                     "a call argument, and they nest different ones. That is a fair "
                     "verdict on a fair statement: the corpus contains no other "
                     "order-preservation claim to twin with, and inventing one to "
                     "manufacture a match would be exactly the failure mode this "
                     "repository exists to avoid.",
        conditions=["A and B are Lebesgue-measurable regions of finite area",
                    "Containment is the OGC `within` relation, matching the LEQ "
                    "head used in geotop.predicates.containment_transitivity",
                    "Both geometries in one coordinate reference system"],
        failure_modes=[
            "Fails for signed or oriented areas: a polygon with reversed ring "
            "orientation reports negative area in many engines, and monotonicity is "
            "then false as stated.",
            "Fails across projections, since containment is projection-invariant "
            "but area is not; a contained region can report a larger area after a "
            "non-equal-area reprojection of only one of the two.",
            "Does not transfer to the Euler characteristic or to any signed "
            "valuation, which is the point of the node: the shared "
            "inclusion-exclusion skeleton uses modularity only, never "
            "non-negativity.",
        ],
        provenance=[HALMOS_MEASURE, KLAIN_ROTA, OGC_SFA, WORBOYS],
        inferential_links=links(
            entailed_by=["geotop.measure.area_inclusion_exclusion"],
            composed_with=["geotop.predicates.containment_transitivity",
                           "algtop.invariants.euler_characteristic_valuation"]),
        keywords=["monotonicity", "area", "containment", "valuation", "measure",
                  "buffer", "subadditivity"],
    ),
]

# --------------------------------------------------------------------------
# Emit
# --------------------------------------------------------------------------

CORPORA = [
    ("algebraic_topology", "algebraic_topology.invariants.v1", ALGTOP_NODES),
    ("geospatial_topology", "geospatial_topology.point_set_relations.v1",
     GEOTOP_NODES),
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
