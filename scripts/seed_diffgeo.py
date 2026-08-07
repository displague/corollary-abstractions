#!/usr/bin/env python3
"""Seed data/differential_geometry/nodes.json and data/differential_topology/nodes.json.

Two corpora, one script, because the statements interleave: Gauss-Bonnet is a
differential-geometry theorem whose right-hand side is a differential-topology
invariant, and Poincare-Hopf is its combinatorial half. Splitting them across
two files while generating them together keeps the shared vocabulary (EULERCHAR,
DEGREE, INTEGRAL, D) literally identical, which matters because the matcher
compares call heads character for character.

WHY THESE STATEMENTS
--------------------

The corpus is chosen to test three specific cross-discipline predictions and to
record what happens when they fail.

1. *The line element is infinitesimal Pythagoras.* Authored to fire, and it
   does. `diffgeo.surfaces.euclidean_line_element`

       LINEELEMENT^2 = DU^2 + DV^2

   lands on the typed skeleton

       +(^(?0:V, 2), ^(?1:V, 2)) = ^(?2:V, 2)

   shared character for character with geometry.right_triangles.
   pythagorean_theorem. The authoring choice that makes it work is squaring the
   *left* slot rather than naming the left slot `DS2`: `DS2 = DU^2 + DV^2` has a
   bare slot on the left and would never meet a statement whose left side is a
   square. It also uses Pythagoras' own archetype id, `sum_of_squares`, so the
   matcher's label-drift check stays quiet.

2. *The fundamental theorem of calculus is Stokes' theorem in dimension one.*
   Authored to fire, and it does -- but only after adopting notation.
   `diffgeo.stokes.stokes_theorem` states the general fact as

       INTEGRAL(D(FORM)) = BOUNDARYINTEGRAL(FORM)

   and that template can never twin with calculus.integration.
   ftc_evaluation_part, because FTC spells the boundary integral out as the
   signed two-point evaluation `F(UPPER) - F(LOWER)` while Stokes keeps it in
   one opaque call. So a second node, `diffgeo.stokes.stokes_zero_form_case`,
   states the 0-form case -- the gradient theorem for a line integral on a
   manifold -- in FTC's own vocabulary:

       INTEGRAL(D(F)) = F(ENDPOINT) - F(STARTPOINT)

   which is the typed skeleton

       INTEGRAL⟨D⟨?0:V⟩⟩ = +(F⟨?1:V⟩, neg(F⟨?2:V⟩))

   exactly. Keeping both nodes is the point: the pair measures the distance
   between "the same theorem" and "the same template", and the general node is
   the honest one. This follows the precedent set by scripts/seed_infotheory.py,
   which adopted the set-theory CARD/MEET/JOIN heads to make Yeung's I-measure
   twin with inclusion-exclusion.

3. *Curvature of a circle is a rate.* Predicted, and it FAILS. K = 1/R is
   written honestly as

       CURVATURE = 1 / RADIUS   ->   ?0:V = *(1, inv(?1:V))

   and the rate/density family (calculus.differentiation.average_rate_of_change,
   physics.kinematics.average_speed, physics.materials.mass_density,
   chemistry.solutions.molarity_definition) is

       RATE = QUANTITY / INTERVAL   ->   ?0:V = *(?1:V, inv(?2:V))

   Three slots against two slots and a numeral: the numerator of a curvature is
   the literal 1, not a free quantity, so the two are different arities and no
   twin fires at any level. Writing `UNITLENGTH / RADIUS` would force the match
   and would be a lie -- there is no unit-length quantity in K = 1/R. Recorded
   as an honest miss; see docs/BACKLOG.md.

Two more twins were found rather than sought:

- `diffgeo.surfaces.gaussian_curvature_principal_product`
  (`GAUSSCURVATURE = PRINCIPAL1 * PRINCIPAL2`) joins geometry.area_formulas.
  rectangle_area_formula on `?0:V = *(?1:V, ?2:V)`. It uses the existing
  `bilinear_product` archetype id. That group is small because most products in
  the corpus have a parameter-like factor (Newton's second law, Ohm's law), and
  a product of two genuinely free variables is rarer than it looks.
- Nothing at all twins with the Gauss-Bonnet node. See the report in the commit
  message and docs/BACKLOG.md: `INTEGRAL⟨?0:V⟩ = *(?1:P, ?2:V)` is a singleton,
  and it is a singleton *next to* its own combinatorial half, Poincare-Hopf
  (`EULERCHAR⟨?0:V⟩ = sum⟨?1:V⟩`), because the matcher treats `sum_i` (a prefix
  big-operator, head `sum`) and `INTEGRAL(...)` (a call, head `INTEGRAL`) as
  unrelated heads.

AUTHORING CONSTRAINTS OBSERVED (all from docs/BACKLOG.md)
--------------------------------------------------------

- `statement_id` may not contain `_` in its first segment, so the prefixes are
  `diffgeo.` and `difftop.` while the directories and `discipline` fields are
  `differential_geometry` and `differential_topology`. Same split the set-theory
  and information-theory corpora already carry.
- `constantToken` has no `name` key.
- `symbol_lexicon.symbols` requires at least one scalar entry and cannot hold
  functionals, so INTEGRAL / D / DEGREE / EULERCHAR / BOUNDARYINTEGRAL / COMPOSE
  live in `functionals`.
- Identifiers beginning `sum_ prod_ lim_ max_ min_` are silently parsed as
  prefix big-operators. Used deliberately in `sum_i SIGN_i` and `sum_i INDEX_i`;
  avoided everywhere else. Indexed slot ids therefore carry the index as a
  *suffix* (`SIGN_i`, `CRITICALCOUNT_k`), never a prefix.
- Call arguments are ORDERED. `COMPOSE(OUTER, INNER)` follows the order fixed by
  scripts/seed_calculus.py's chain rule, so degree multiplicativity and the
  chain rule are comparable even though they do not (see report) twin.
- The grammar has no binder and no quantifier. Brouwer's theorem is really
  "there exists x with f(x) = x"; the template records only the fixed-point
  equation `FIXEDPOINT = SELFMAP(FIXEDPOINT)` and the existential lives in
  `semantic_interpretation`. Same class of loss as infotheory's CAPMAX.
- Every slot appearing in a template is declared in `slot_schema`.

CROSS-CORPUS LINK NOT WRITTEN
-----------------------------

A parallel branch is authoring algebraic topology and will own the Euler
characteristic nodes (planned ids `algtop.invariants.euler_characteristic_surface`
and neighbours). The instruction was to point at them with a one-sided
`composed_with`, which is the only cross-corpus link kind the validator does not
require a reciprocal for -- but scripts/validate_nodes.py *does* require every
link target to resolve in the merged graph, and `data/algebraic_topology/` does
not exist on this branch. Adding the edge now would make validation fail here
and pass only after a merge. So the reference is recorded in prose (see
`diffgeo.surfaces.gauss_bonnet_theorem` and `difftop.invariants.*`) and the edge
is left as a one-line change once algtop lands: add

    "algtop.invariants.euler_characteristic_surface"

to GAUSS_BONNET_LINKS' `composed_with` below. Recorded in docs/BACKLOG.md as a
forward-reference gap.
"""

from __future__ import annotations

import json
from pathlib import Path


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="arithmetic"):
    return {"symbol": symbol, "name": name, "arity": arity, "operator_family": family}


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
         meaning, significance, conditions, provenance, disciplines=None,
         functionals=None, constants=None, index_sets=None, failure_modes=None,
         inferential_links=None, keywords=None, canonical_objects=None):
    context = {"disciplines": disciplines or ["differential_geometry"],
               "subfield": subfield, "topic": topic}
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
    return out


# --------------------------------------------------------------------------
# Lexicon fragments
# --------------------------------------------------------------------------

EQ = op("=", "equality", 2, "relational")
GE = op(">=", "greater than or equal", 2, "relational")
ADD = op("+", "addition", 2, "arithmetic")
SUB = op("-", "subtraction", 2, "arithmetic")
MUL = op("*", "multiplication", 2, "arithmetic")
DIV = op("/", "division", 2, "arithmetic")
POW = op("^", "exponentiation", 2, "arithmetic")
SUM = op("sum", "finite summation over an index set", 1, "arithmetic")

INTEGRAL_FN = {
    "notation": "INTEGRAL(.)", "name": "integration_operator", "input_arity": 1,
    "codomain": "real",
    "description": "Integral of the argument over the region fixed by the "
                   "statement's context -- a curve, a surface, or an oriented "
                   "manifold with boundary. Written as an opaque call because "
                   "the template grammar has no binder, so neither the domain "
                   "nor the measure is visible to the matcher; the same head "
                   "scripts/seed_calculus.py uses, deliberately, so the "
                   "operator identities line up."}

BOUNDARY_INTEGRAL_FN = {
    "notation": "BOUNDARYINTEGRAL(.)", "name": "boundary integration operator",
    "input_arity": 1, "codomain": "real",
    "description": "Integral of the argument over the induced-orientation "
                   "boundary of the region INTEGRAL runs over. A separate head "
                   "rather than INTEGRAL with a second argument, because the "
                   "region is not a slot anywhere in this grammar; the price is "
                   "recorded in the Stokes node's significance field."}

D_FN = {"notation": "D(.)", "name": "exterior derivative", "input_arity": 1,
        "codomain": "differential form",
        "description": "Exterior derivative, taking a k-form to a (k+1)-form. "
                       "Shares a head with scripts/seed_calculus.py's "
                       "differentiation operator on purpose: on a 0-form in one "
                       "variable the two are the same operator, which is what "
                       "makes the FTC twin more than a pun."}

F_FN = {"notation": "f(.)", "name": "potential function", "input_arity": 1,
        "codomain": "real",
        "description": "A smooth real-valued function -- a 0-form -- evaluated "
                       "at a point. The head is spelled `F` to match "
                       "calculus.integration.ftc_evaluation_part's antiderivative "
                       "head exactly; call heads are compared literally, so the "
                       "spelling is what lets the twin fire."}

COMPOSE_FN = {"notation": "COMPOSE(.,.)", "name": "map composition",
              "input_arity": 2, "codomain": "smooth map",
              "description": "Composition of an outer map with an inner map, "
                             "argument order fixed to match "
                             "calculus.differentiation.chain_rule. Call "
                             "arguments are ordered for the matcher, so this "
                             "convention has to be stated rather than assumed."}

SELFMAP_FN = {"notation": "SELFMAP(.)", "name": "continuous self-map",
              "input_arity": 1, "codomain": "point of the same space",
              "description": "A continuous map of a space to itself, evaluated "
                             "at a point. Distinguished from a general smooth "
                             "map because the fixed-point statement needs the "
                             "domain and codomain to be the same object."}

DEGREE_FN = {"notation": "DEGREE(.)", "name": "Brouwer degree", "input_arity": 1,
             "codomain": "integer",
             "description": "Degree of a smooth map between compact oriented "
                            "manifolds of the same dimension: the signed count "
                            "of preimages of a regular value, independent of "
                            "which regular value is chosen and invariant under "
                            "smooth homotopy."}

EULERCHAR_FN = {"notation": "EULERCHAR(.)", "name": "Euler characteristic",
                "input_arity": 1, "codomain": "integer",
                "description": "Euler characteristic of a manifold. Held as a "
                               "*call* throughout data/differential_topology "
                               "because there it is an invariant applied to a "
                               "space, and as a *slot* in Gauss-Bonnet because "
                               "there it is the number appearing on the "
                               "right-hand side. The corpus-wide consequence of "
                               "that split is recorded in docs/BACKLOG.md."}

IDX_PREIMAGE = {"notation": "i in f^{-1}(y)", "domain": "finite preimage of a regular value",
                "description": "Index running over the finitely many preimages "
                               "of a regular value under a smooth map of "
                               "compact manifolds."}
IDX_ZEROS = {"notation": "i in Zero(V)", "domain": "finite zero set of a vector field",
             "description": "Index running over the isolated zeros of a smooth "
                            "vector field on a compact manifold."}

TWOPI_CONST = {"symbol": "2*pi", "value": 6.283185307179586,
               "description": "The normalizing constant in Gauss-Bonnet. It is "
                              "a genuine fixed constant, not a free parameter, "
                              "which is why the slot is declared `constant` and "
                              "the typed skeleton carries a P there. Its "
                              "presence is also why Gauss-Bonnet cannot twin "
                              "with Poincare-Hopf, whose index sum is already "
                              "normalized."}
HALF_CONST = {"symbol": "1/2", "value": 0.5,
              "description": "The conventional factor in the energy functional. "
                             "It exists to make the first variation of energy "
                             "the geodesic equation without a stray 2; nothing "
                             "geometric depends on it."}


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

DOCARMO1976 = {"citation_key": "docarmo1976",
               "bibliographic_entry": "do Carmo, M. P. (1976). Differential Geometry of Curves and Surfaces. Englewood Cliffs: Prentice-Hall."}
DOCARMO1992 = {"citation_key": "docarmo1992",
               "bibliographic_entry": "do Carmo, M. P. (1992). Riemannian Geometry. Boston: Birkhauser."}
MILNOR1965 = {"citation_key": "milnor1965",
              "bibliographic_entry": "Milnor, J. W. (1965). Topology from the Differentiable Viewpoint. Charlottesville: University Press of Virginia."}
MILNOR1963 = {"citation_key": "milnor1963",
              "bibliographic_entry": "Milnor, J. W. (1963). Morse Theory. Annals of Mathematics Studies 51. Princeton: Princeton University Press."}
GP1974 = {"citation_key": "guillemin1974",
          "bibliographic_entry": "Guillemin, V., Pollack, A. (1974). Differential Topology. Englewood Cliffs: Prentice-Hall."}
SPIVAK1965 = {"citation_key": "spivak1965",
              "bibliographic_entry": "Spivak, M. (1965). Calculus on Manifolds: A Modern Approach to Classical Theorems of Advanced Calculus. New York: W. A. Benjamin."}
SPIVAK1999 = {"citation_key": "spivak1999",
              "bibliographic_entry": "Spivak, M. (1999). A Comprehensive Introduction to Differential Geometry, Volume 1 (3rd ed.). Houston: Publish or Perish."}
LEE2013 = {"citation_key": "lee2013",
           "bibliographic_entry": "Lee, J. M. (2013). Introduction to Smooth Manifolds (2nd ed.). Graduate Texts in Mathematics 218. New York: Springer."}
GAUSS1827 = {"citation_key": "gauss1827",
             "bibliographic_entry": "Gauss, C. F. (1828). Disquisitiones generales circa superficies curvas. Commentationes Societatis Regiae Scientiarum Gottingensis Recentiores, 6, 99-146."}
BONNET1848 = {"citation_key": "bonnet1848",
              "bibliographic_entry": "Bonnet, O. (1848). Memoire sur la theorie generale des surfaces. Journal de l'Ecole Polytechnique, 19(32), 1-146."}
CHERN1944 = {"citation_key": "chern1944",
             "bibliographic_entry": "Chern, S.-S. (1944). A Simple Intrinsic Proof of the Gauss-Bonnet Formula for Closed Riemannian Manifolds. Annals of Mathematics, 45(4), 747-752.",
             "url": "https://doi.org/10.2307/1969302"}
POINCARE1885 = {"citation_key": "poincare1885",
                "bibliographic_entry": "Poincare, H. (1885). Sur les courbes definies par les equations differentielles. Journal de Mathematiques Pures et Appliquees, 4e serie, 1, 167-244."}
HOPF1927 = {"citation_key": "hopf1927",
            "bibliographic_entry": "Hopf, H. (1927). Vektorfelder in n-dimensionalen Mannigfaltigkeiten. Mathematische Annalen, 96(1), 225-249."}
MORSE1925 = {"citation_key": "morse1925",
             "bibliographic_entry": "Morse, M. (1925). Relations between the Critical Points of a Real Function of n Independent Variables. Transactions of the American Mathematical Society, 27(3), 345-396."}
BROUWER1911 = {"citation_key": "brouwer1911",
               "bibliographic_entry": "Brouwer, L. E. J. (1911). Ueber Abbildung von Mannigfaltigkeiten. Mathematische Annalen, 71(1), 97-115."}
CARTAN1899 = {"citation_key": "cartan1899",
              "bibliographic_entry": "Cartan, E. (1899). Sur certaines expressions differentielles et le probleme de Pfaff. Annales Scientifiques de l'Ecole Normale Superieure, 3e serie, 16, 239-332."}
STOKES1854 = {"citation_key": "stokes1854",
              "bibliographic_entry": "Stokes, G. G. (1854). Smith's Prize Examination Paper, Question 8. Cambridge. (The theorem first appeared in an 1850 letter from Kelvin to Stokes.)"}
BOTT1982 = {"citation_key": "bott1982",
            "bibliographic_entry": "Bott, R., Tu, L. W. (1982). Differential Forms in Algebraic Topology. Graduate Texts in Mathematics 82. New York: Springer."}


# --------------------------------------------------------------------------
# Differential geometry
# --------------------------------------------------------------------------

DG = ["differential_geometry"]

GAUSS_BONNET_LINKS = links(
    # One-sided, unchecked-for-reciprocity edges only. The algebraic-topology
    # id `algtop.invariants.euler_characteristic_surface` belongs here too and
    # is omitted solely because the validator requires targets to resolve and
    # that corpus is authored on a parallel branch; see the module docstring.
    composed_with=["difftop.vectorfields.poincare_hopf_index_theorem",
                   "difftop.invariants.euler_characteristic_diffeomorphism_invariance",
                   "diffgeo.surfaces.gaussian_curvature_principal_product"])

DIFFGEO_NODES = [

    node("diffgeo.curves.arc_length_functional", "Arc Length of a Parameterized Curve",
         "definition", "formal", "curves", "length_functional",
         "L = INTEGRAL(|c'(t)|)",
         "L(c) = \\int_a^b \\lVert c'(t) \\rVert \\, dt",
         [{"form_id": "riemannian", "notation_system": "ascii",
           "expression": "L(c) = INTEGRAL(sqrt(g(c'(t), c'(t))))",
           "scope_note": "On a Riemannian manifold the speed is measured by the metric tensor g"},
          {"form_id": "first_fundamental_form", "notation_system": "ascii",
           "expression": "L = INTEGRAL(sqrt(E*u'^2 + 2*F*u'*v' + G*v'^2))",
           "scope_note": "For a curve on a surface, the integrand is the first fundamental form evaluated on the velocity"},
          {"form_id": "reparameterization", "notation_system": "ascii",
           "expression": "L(c o phi) = L(c) for every orientation-preserving reparameterization phi",
           "scope_note": "The invariance that makes length a property of the image, not of the parameterization"}],
         "accumulated_density", "LENGTH = INTEGRAL(SPEED)",
         [slot("LENGTH", "variable", "output"),
          slot("SPEED", "variable", "integrand_density")],
         ["Length is an accumulation of a pointwise density along a "
          "one-dimensional domain. Nothing in the template names the domain: the "
          "grammar has no binder, so `INTEGRAL(.)` is an opaque call and the "
          "interval, the measure and the orientation are all invisible to the "
          "matcher.",
          "Invariant under reparameterization, which is the property that "
          "distinguishes this functional from diffgeo.curves.geodesic_energy_"
          "functional and is the reason length has no distinguished minimizing "
          "parameterization.",
          "Homogeneous of degree one in the velocity, so the integrand carries an "
          "absolute value or a square root and the functional is not smooth at "
          "velocities that vanish.",
          "Additive over concatenation of curves, which is the property that "
          "makes it a *measure* on paths rather than merely a number attached to "
          "them."],
         [sym("L", "variable", "output", "Arc length of the curve."),
          sym("t", "variable", "curve_parameter",
              "Parameter along the curve, ranging over a compact interval."),
          sym("c", "variable", "curve",
              "Smooth parameterized curve into the ambient manifold.")],
         [EQ],
         "The length of a curve is the accumulated speed of any parameterization "
         "of it.",
         "The first of two length-like functionals authored here to test whether "
         "the matcher can see the discrete/continuous divide. It cannot. The "
         "typed skeleton `?0:V = INTEGRAL⟨?1:V⟩` is a singleton in the whole "
         "graph, and the near-miss worth naming is with probability "
         "normalization: `sum_i p_i = 1` and `INTEGRAL(density) = 1` are the same "
         "statement in the discrete and continuous cases, but `sum_i` parses to "
         "the head `sum` while `INTEGRAL(.)` parses to the head `INTEGRAL`, so "
         "they can never meet. (No sum-to-one node exists in data/statistics "
         "today; the closest is probstat.probability.total_probability_partition, "
         "`MARGINAL = sum_i CONDITIONAL_i*WEIGHT_i`, whose skeleton "
         "`?0:V = sum⟨*(?1:P, ?2:V)⟩` differs from this one in head *and* in "
         "summand shape. So the miss here is structural, not an accident of "
         "which nodes happen to exist.) Recorded in docs/BACKLOG.md.",
         ["Curve piecewise smooth on a compact parameter interval",
          "Ambient space carries a metric, so that speed is defined",
          "Orientation is irrelevant: length is unsigned"],
         [DOCARMO1976, DOCARMO1992, LEE2013],
         disciplines=DG,
         functionals=[INTEGRAL_FN],
         failure_modes=[
             "Arc length is not defined for merely continuous curves; "
             "rectifiability is an extra hypothesis and fails for typical "
             "Brownian paths and for the graph of x*sin(1/x) near zero.",
             "The functional is not smooth where the velocity vanishes, so "
             "variational arguments about length routinely switch to the energy "
             "functional and transfer the conclusion back."],
         inferential_links=links(
             composed_with=["diffgeo.curves.geodesic_energy_functional",
                            "diffgeo.surfaces.first_fundamental_form"]),
         keywords=["arc length", "functional", "reparameterization invariance",
                   "accumulation", "curve"],
         canonical_objects=["parameterized curve", "Riemannian metric"]),

    node("diffgeo.curves.geodesic_energy_functional", "Geodesic Energy of a Curve",
         "definition", "formal", "curves", "energy_functional",
         "E = (1/2) * INTEGRAL(|c'(t)|^2)",
         "E(c) = \\tfrac{1}{2}\\int_a^b \\lVert c'(t)\\rVert^2 \\, dt",
         [{"form_id": "riemannian", "notation_system": "ascii",
           "expression": "E(c) = (1/2)*INTEGRAL(g(c'(t), c'(t)))",
           "scope_note": "Metric form; the integrand is a quadratic form in the velocity"},
          {"form_id": "cauchy_schwarz", "notation_system": "ascii",
           "expression": "L(c)^2 <= 2*(b - a)*E(c)",
           "scope_note": "Cauchy-Schwarz, with equality exactly for constant-speed parameterizations -- the inequality that lets energy stand in for length"},
          {"form_id": "euler_lagrange", "notation_system": "ascii",
           "expression": "first variation of E vanishes iff the covariant acceleration of c vanishes",
           "scope_note": "Critical points of E are exactly the geodesics, parameterized proportionally to arc length"}],
         "scaled_accumulated_square", "ENERGY = CONSTANT * INTEGRAL(SPEED^2)",
         [slot("ENERGY", "variable", "output"),
          slot("CONSTANT", "constant", "normalizing_factor"),
          slot("SPEED", "variable", "integrand_density")],
         ["Quadratic where diffgeo.curves.arc_length_functional is homogeneous of "
          "degree one, and that single difference is the whole of why energy is "
          "the functional one actually varies: it is smooth at zero velocity and "
          "its critical points are parameterized, whereas length's are not.",
          "NOT reparameterization invariant. Energy sees how fast the curve is "
          "traversed; length does not. Minimizing energy therefore selects "
          "constant-speed representatives, which is a feature and not a defect.",
          "The leading factor is a fixed convention, declared `constant` so that "
          "the typed skeleton carries a P there. It exists only to make the first "
          "variation come out without a factor of two.",
          "Critical points coincide with those of length among constant-speed "
          "curves (Cauchy-Schwarz), which is what licenses the standard "
          "bait-and-switch in the proof of the existence of geodesics."],
         [sym("E", "variable", "output", "Energy of the curve."),
          sym("t", "variable", "curve_parameter", "Parameter along the curve."),
          sym("c", "variable", "curve", "Smooth parameterized curve.")],
         [EQ, MUL, POW],
         "The energy of a curve is half the accumulated squared speed of a "
         "particular parameterization of it.",
         "A deliberate near-miss with geometry.area_formulas.circle_area_formula. "
         "That node is `AREA = CONSTANT * RADIUS^2`, typed skeleton "
         "`?0:V = *(?1:P, ^(?2:V, 2))`; this one is "
         "`?0:V = *(?1:P, INTEGRAL⟨^(?2:V, 2)⟩)`. The two differ by exactly one "
         "call wrapper, and the wrapper is doing real work -- the difference "
         "between a scaled square and an accumulated scaled square is the "
         "difference between a formula and a functional. The matcher's "
         "specialization pass (scripts/specialize.py) will not bridge it either, "
         "since absorbing an INTEGRAL into a variable slot is a rewrite rather "
         "than a slot-to-subtree binding. Worth keeping as a calibration point: "
         "one wrapper is enough to separate two skeletons, and that is the "
         "correct behaviour.",
         ["Curve piecewise smooth on a compact parameter interval",
          "Ambient space carries a Riemannian metric",
          "The parameter interval is fixed: energy depends on it, unlike length"],
         [DOCARMO1992, MILNOR1963, LEE2013],
         disciplines=DG,
         functionals=[INTEGRAL_FN],
         constants=[HALF_CONST],
         failure_modes=[
             "Energy is not a geometric invariant of the image of the curve. "
             "Comparing the energies of two curves parameterized over different "
             "intervals compares parameterizations, not shapes.",
             "In Lorentzian signature the integrand is not positive and the "
             "functional is not bounded below, so the direct method of the "
             "calculus of variations does not apply and geodesics have to be "
             "found some other way."],
         inferential_links=links(
             composed_with=["diffgeo.curves.arc_length_functional",
                            "diffgeo.surfaces.first_fundamental_form"]),
         keywords=["energy functional", "geodesic", "calculus of variations",
                   "constant speed", "Cauchy-Schwarz"],
         canonical_objects=["parameterized curve", "Riemannian metric", "geodesic"]),

    node("diffgeo.curves.circle_curvature", "Curvature of a Circle",
         "proposition", "derived", "curves", "curvature",
         "K = 1 / R", "\\kappa = \\frac{1}{R}",
         [{"form_id": "radius_of_curvature", "notation_system": "ascii",
           "expression": "R = 1 / K",
           "scope_note": "The inverse reading: the osculating circle of a general curve has radius 1/K"},
          {"form_id": "frenet", "notation_system": "ascii",
           "expression": "|T'(s)| = K for a unit-speed parameterization",
           "scope_note": "Curvature as the rate of turning of the unit tangent with respect to arc length"},
          {"form_id": "total_turning", "notation_system": "ascii",
           "expression": "INTEGRAL(K) = 2*pi over one full circle of any radius",
           "scope_note": "Total curvature is radius-independent -- the one-dimensional shadow of Gauss-Bonnet"}],
         "reciprocal_of_scale", "CURVATURE = 1 / RADIUS",
         [slot("CURVATURE", "variable", "output"),
          slot("RADIUS", "variable", "scale")],
         ["A reciprocal, not a ratio. The numerator is the literal 1 -- there is "
          "no quantity being divided by an extent -- which is exactly why this "
          "node does not join the rate/density family; see the significance "
          "field.",
          "Scale-antivariant: doubling the radius halves the curvature, so "
          "curvature carries dimension 1/length and is the natural quantity to "
          "integrate against length.",
          "Constant along the curve, which characterizes circles and lines among "
          "plane curves up to rigid motion; the limit R -> infinity gives the "
          "straight line with curvature 0.",
          "Independent of parameterization and of orientation up to sign, so the "
          "unsigned version stated here is a property of the point set."],
         [sym("K", "variable", "output", "Curvature of the circle."),
          sym("R", "variable", "scale", "Radius of the circle, strictly positive."),
          sym("s", "variable", "arc_length_parameter",
              "Arc length parameter, in which curvature is the turning rate.")],
         [EQ, DIV],
         "A circle curves at a rate equal to the reciprocal of its radius: small "
         "circles turn fast, large ones slowly.",
         "The corpus's cleanest example of a predicted twin that correctly does "
         "*not* fire. The rate/density family -- calculus.differentiation."
         "average_rate_of_change, physics.kinematics.average_speed, "
         "physics.materials.mass_density, chemistry.solutions.molarity_definition "
         "-- all sit on `?0:V = *(?1:V, inv(?2:V))`, a three-slot skeleton. This "
         "node is `?0:V = *(1, inv(?1:V))`: two slots and a numeric literal. The "
         "arities differ on the right-hand side, so no twin fires at shape, typed "
         "or family level, and none should. Forcing it would mean inventing a "
         "`UNITLENGTH` slot for the numerator, and there is no unit length in "
         "K = 1/R -- the 1 is a genuine constant of the reciprocal, not an "
         "elided quantity. The honest reading is that curvature is a *density* "
         "(turning per unit length) whose numerator has been normalized away, and "
         "that the matcher is right to treat a normalized density and a general "
         "ratio as different structures.",
         ["Circle of strictly positive radius in the Euclidean plane",
          "Unsigned curvature; the signed version depends on a choice of normal",
          "Curvature measured with respect to arc length, not an arbitrary parameter"],
         [DOCARMO1976, SPIVAK1999],
         disciplines=DG,
         failure_modes=[
             "Read as a definition of curvature it is circular: curvature is "
             "defined by the Frenet equations and this is the computed value for "
             "one family of curves.",
             "The formula is Euclidean. On a sphere a geodesic circle of the same "
             "intrinsic radius has a different geodesic curvature, which is the "
             "whole content of Gauss-Bonnet's boundary term."],
         inferential_links=links(
             composed_with=["diffgeo.curves.arc_length_functional",
                            "diffgeo.surfaces.gauss_bonnet_theorem"]),
         keywords=["curvature", "circle", "reciprocal", "osculating circle",
                   "honest miss"],
         canonical_objects=["plane curve", "circle", "Frenet frame"]),

    node("diffgeo.surfaces.first_fundamental_form", "First Fundamental Form (Metric Line Element)",
         "definition", "formal", "surfaces", "metric",
         "ds^2 = E*du^2 + 2*F*du*dv + G*dv^2",
         "ds^2 = E\\,du^2 + 2F\\,du\\,dv + G\\,dv^2",
         [{"form_id": "matrix", "notation_system": "matrix_notation",
           "expression": "ds^2 = [du dv] * [[E, F], [F, G]] * [du dv]^T",
           "scope_note": "The symmetric matrix of the metric in the coordinate frame; E*G - F^2 > 0 is positive-definiteness"},
          {"form_id": "inner_products", "notation_system": "ascii",
           "expression": "E = <x_u, x_u>, F = <x_u, x_v>, G = <x_v, x_v>",
           "scope_note": "Coefficients as inner products of the coordinate tangent vectors"},
          {"form_id": "tensor", "notation_system": "ascii",
           "expression": "ds^2 = g_ij * dx^i * dx^j",
           "scope_note": "Index notation; the two-dimensional case written out is the classical form above"}],
         "quadratic_form_in_two_differentials",
         "LINEELEMENT^2 = COEFFE*DU^2 + 2*COEFFF*DU*DV + COEFFG*DV^2",
         [slot("LINEELEMENT", "variable", "infinitesimal_distance"),
          slot("COEFFE", "variable", "metric_coefficient_uu"),
          slot("COEFFF", "variable", "metric_coefficient_uv"),
          slot("COEFFG", "variable", "metric_coefficient_vv"),
          slot("DU", "variable", "coordinate_differential_first"),
          slot("DV", "variable", "coordinate_differential_second")],
         ["A general quadratic form in two differentials. The cross term carries "
          "a literal 2 because the form is symmetric and F is counted twice; that "
          "2 is a genuine numeral, not a slot, and it is what keeps this skeleton "
          "apart from any three-term sum with free coefficients.",
          "The coefficients are declared `variable`, not `constant`: they are "
          "functions of position on the surface, and treating them as parameters "
          "would falsely make the metric flat.",
          "Positive-definite exactly when E > 0 and E*G - F^2 > 0. The template "
          "cannot express that side condition, so it lives in "
          "regularity_conditions -- the grammar has relations but no way to "
          "attach a constraint to a definition.",
          "Everything intrinsic to the surface -- lengths, angles, areas, "
          "geodesics, and by Gauss's Theorema Egregium the Gaussian curvature "
          "itself -- is a function of these three coefficients and their "
          "derivatives alone."],
         [sym("s", "variable", "infinitesimal_distance",
              "Element of arc length on the surface."),
          sym("E", "variable", "metric_coefficient_uu",
              "Coefficient of du^2; the squared length of the first coordinate tangent."),
          sym("F", "variable", "metric_coefficient_uv",
              "Coefficient of the cross term; the inner product of the two coordinate tangents."),
          sym("G", "variable", "metric_coefficient_vv",
              "Coefficient of dv^2; the squared length of the second coordinate tangent."),
          sym("u", "variable", "coordinate_first", "First surface coordinate."),
          sym("v", "variable", "coordinate_second", "Second surface coordinate.")],
         [EQ, ADD, MUL, POW],
         "The squared length of an infinitesimal displacement on a surface is a "
         "quadratic form in the coordinate increments, with three position-"
         "dependent coefficients.",
         "The general form of which geometry's Pythagorean theorem is the "
         "constant-coefficient case. That relationship is real but is not visible "
         "to the matcher at this node: the typed skeleton here is "
         "`+(*(2, ?0:V, ?1:V, ?2:V), *(?3:V, ^(?1:V, 2)), *(?4:V, ^(?2:V, 2))) = "
         "^(?5:V, 2)`, a three-term sum, against Pythagoras' two-term "
         "`+(^(?0:V, 2), ^(?1:V, 2)) = ^(?2:V, 2)`. Specializing one to the other "
         "requires setting E = G = 1 and F = 0 and then *deleting* the vanishing "
         "term, which is an algebraic rewrite rather than a slot binding, and "
         "scripts/specialize.py does slot bindings. That is the same class of "
         "miss docs/BACKLOG.md already records for uniform entropy against "
         "Shannon entropy. The corpus therefore carries "
         "diffgeo.surfaces.euclidean_line_element as a separate node, where the "
         "twin does fire -- the specialization is asserted by hand via "
         "special_case_of and the twin is checked by machine only at the "
         "specialized end.",
         ["Regular parameterized surface patch, so the coordinate tangents are independent",
          "E > 0 and E*G - F^2 > 0 (positive-definiteness)",
          "Coefficients smooth functions of the coordinates"],
         [DOCARMO1976, GAUSS1827, SPIVAK1999],
         disciplines=DG,
         failure_modes=[
             "The coefficients are coordinate-dependent; comparing E, F, G across "
             "two parameterizations of the same surface compares charts, not "
             "geometry. Only invariants built from them (curvature, area) are "
             "meaningful.",
             "Positive-definiteness fails on the coordinate singularities of "
             "common charts -- the poles in spherical coordinates -- where the "
             "form degenerates without the surface doing anything."],
         inferential_links=links(
             generalizes=["diffgeo.surfaces.euclidean_line_element"],
             composed_with=["diffgeo.curves.arc_length_functional",
                            "diffgeo.surfaces.gaussian_curvature_principal_product"]),
         keywords=["first fundamental form", "line element", "metric tensor",
                   "quadratic form", "Theorema Egregium"],
         canonical_objects=["regular surface", "coordinate chart", "metric tensor"]),

    node("diffgeo.surfaces.euclidean_line_element", "Euclidean Line Element (Flat Metric)",
         "proposition", "derived", "surfaces", "metric",
         "ds^2 = du^2 + dv^2", "ds^2 = du^2 + dv^2",
         [{"form_id": "cartesian", "notation_system": "ascii",
           "expression": "ds^2 = dx^2 + dy^2",
           "scope_note": "The plane in Cartesian coordinates: E = G = 1, F = 0"},
          {"form_id": "finite_difference", "notation_system": "ascii",
           "expression": "(delta_s)^2 = (delta_x)^2 + (delta_y)^2",
           "scope_note": "The finite version is the Pythagorean theorem; the differential version is the same statement in the limit"},
          {"form_id": "polar", "notation_system": "ascii",
           "expression": "ds^2 = dr^2 + r^2*dtheta^2",
           "scope_note": "The same flat metric in polar coordinates -- E = 1, F = 0, G = r^2 -- showing the coefficients are chart artifacts"}],
         "sum_of_squares", "LINEELEMENT^2 = DU^2 + DV^2",
         [slot("LINEELEMENT", "variable", "infinitesimal_distance"),
          slot("DU", "variable", "coordinate_differential_first"),
          slot("DV", "variable", "coordinate_differential_second")],
         ["The metric coefficients have disappeared: E = G = 1 and F = 0, so the "
          "quadratic form is the identity form and the statement is a bare sum of "
          "squares.",
          "The left slot is squared rather than being a bare output slot. That is "
          "the load-bearing authoring choice: `DS2 = DU^2 + DV^2` would put a "
          "plain slot on the left and could never meet a statement whose left "
          "side is a square, whereas `LINEELEMENT^2 = ...` meets "
          "geometry.right_triangles.pythagorean_theorem exactly.",
          "Flat: the Gaussian curvature computed from these coefficients is "
          "identically zero, which is why the same coefficients hold in every "
          "Cartesian chart and why no chart of the sphere can achieve them.",
          "Symmetric in the two differentials, an isotropy the general first "
          "fundamental form does not have."],
         [sym("s", "variable", "infinitesimal_distance", "Element of arc length."),
          sym("u", "variable", "coordinate_first", "First Cartesian coordinate."),
          sym("v", "variable", "coordinate_second", "Second Cartesian coordinate.")],
         [EQ, ADD, POW],
         "In a flat chart, the squared length of an infinitesimal displacement is "
         "the sum of the squares of the coordinate increments.",
         "The corpus's cleanest cross-discipline typed twin and the one this "
         "corpus was partly built to produce. Its typed skeleton "
         "`+(^(?0:V, 2), ^(?1:V, 2)) = ^(?2:V, 2)` is shared character for "
         "character with geometry.right_triangles.pythagorean_theorem, and it "
         "carries the same archetype id, `sum_of_squares`, so no label drift is "
         "reported. The claim the twin encodes is not an analogy: the Euclidean "
         "line element *is* the Pythagorean theorem, applied to an infinitesimal "
         "right triangle and integrated. Every other node in this corpus is "
         "downstream of that identification -- the first fundamental form is what "
         "you get when the right triangle is allowed to be skew and to vary from "
         "point to point, and Gaussian curvature is the obstruction to making "
         "these coefficients hold in any chart at all. The twin is also a small "
         "argument for the corpus's method: the connection is obvious once "
         "written this way, and completely invisible if the left-hand side is "
         "named `DS2`.",
         ["Flat chart on a Euclidean plane, or a Cartesian chart on any flat surface",
          "Coordinates orthonormal at the point in question",
          "Statement is pointwise; it holds in a chart, not on a curved surface globally"],
         [DOCARMO1976, SPIVAK1999, LEE2013],
         disciplines=DG,
         failure_modes=[
             "No chart of a curved surface has this line element on an open set; "
             "assuming it locally is the flat-earth error and it is detectable "
             "precisely by the Gaussian curvature.",
             "In polar or any non-Cartesian coordinates the same flat metric looks "
             "different, so the form of the line element is not by itself evidence "
             "of curvature."],
         inferential_links=links(
             special_case_of=["diffgeo.surfaces.first_fundamental_form"],
             composed_with=["diffgeo.curves.arc_length_functional"]),
         keywords=["line element", "flat metric", "Pythagorean theorem",
                   "sum of squares", "typed twin"],
         canonical_objects=["Euclidean plane", "Cartesian chart"]),

    node("diffgeo.surfaces.gaussian_curvature_principal_product",
         "Gaussian Curvature as the Product of Principal Curvatures",
         "definition", "formal", "surfaces", "curvature",
         "K = k1 * k2", "K = \\kappa_1 \\kappa_2",
         [{"form_id": "shape_operator", "notation_system": "ascii",
           "expression": "K = det(S)",
           "scope_note": "Determinant of the shape operator, whose eigenvalues are the principal curvatures"},
          {"form_id": "fundamental_forms", "notation_system": "ascii",
           "expression": "K = (L*N - M^2) / (E*G - F^2)",
           "scope_note": "Ratio of the determinants of the second and first fundamental forms"},
          {"form_id": "theorema_egregium", "notation_system": "ascii",
           "expression": "K is a function of E, F, G and their first two derivatives alone",
           "scope_note": "Gauss's Theorema Egregium: the extrinsic definition above computes an intrinsic quantity"},
          {"form_id": "sphere", "notation_system": "ascii",
           "expression": "K = 1/R^2 on a sphere of radius R",
           "scope_note": "Both principal curvatures equal 1/R; the product is the square"}],
         "bilinear_product", "GAUSSCURVATURE = PRINCIPAL1 * PRINCIPAL2",
         [slot("GAUSSCURVATURE", "variable", "output"),
          slot("PRINCIPAL1", "variable", "extremal_curvature_first"),
          slot("PRINCIPAL2", "variable", "extremal_curvature_second")],
         ["A product of two free variables, not a scaled variable: both factors "
          "are declared `variable`, which is what puts this node in the "
          "`?0:V = *(?1:V, ?2:V)` group rather than the much larger "
          "`*(?:P, ?:V)` group that Newton's second law and Ohm's law occupy.",
          "The product is symmetric in the two factors, and so is the geometry: "
          "there is no ordering of principal curvatures that the definition "
          "depends on.",
          "Sign-carrying in a way a product of lengths is not. Both curvatures "
          "negative gives K > 0 (a sphere-like point), opposite signs gives "
          "K < 0 (a saddle), and one vanishing gives K = 0 (a cylinder), so the "
          "sign of the product classifies the local shape.",
          "Invariant under isometry by the Theorema Egregium, even though both "
          "factors individually are not -- bending a plane into a cylinder "
          "changes k1 and k2 while their product stays zero. The twin with "
          "rectangle area is structural only; area is a product of two "
          "independent quantities, curvature a product of two constrained ones."],
         [sym("K", "variable", "output", "Gaussian curvature at a point."),
          sym("k1", "variable", "extremal_curvature_first",
              "First principal curvature: maximal normal curvature at the point."),
          sym("k2", "variable", "extremal_curvature_second",
              "Second principal curvature: minimal normal curvature at the point.")],
         [EQ, MUL],
         "The Gaussian curvature at a point is the product of the two extreme "
         "normal curvatures there.",
         "An unsought twin, which makes it more interesting than the sought ones. "
         "Its typed skeleton `?0:V = *(?1:V, ?2:V)` is shared with "
         "geometry.area_formulas.rectangle_area_formula (`AREA = DIM1 * DIM2`), "
         "and with nothing else in the graph -- most products in the corpus have "
         "a parameter-like factor (`FORCE = INERTIA * RESPONSE`, "
         "`POTENTIAL = FLOW * RESISTANCE`) and land on a different typed "
         "skeleton. So the group is exactly 'the product of two quantities both "
         "free to vary', and the two members are area and curvature. That is not "
         "a coincidence dressed up: Gaussian curvature is the area distortion of "
         "the Gauss map, the limiting ratio of the area of the spherical image to "
         "the area of the patch, so a product of two orthogonal rates is precisely "
         "the right shape for it. This node adopts the existing archetype id "
         "`bilinear_product` so the matcher's split-archetype check stays quiet.",
         ["Regular surface with a chosen unit normal field, so the shape operator is defined",
          "Point at which the surface is twice differentiable",
          "Sign convention: K is independent of the normal's orientation even though k1 and k2 are not"],
         [DOCARMO1976, GAUSS1827, SPIVAK1999],
         disciplines=DG,
         failure_modes=[
             "The principal curvatures are extrinsic and change under bending; "
             "only their product is intrinsic, so reading either factor as a "
             "property of the surface's own geometry is wrong.",
             "At umbilic points the principal directions are undefined even though "
             "the curvatures are equal, so formulas that pick a principal frame "
             "break there while this product does not."],
         inferential_links=links(
             composed_with=["diffgeo.surfaces.first_fundamental_form",
                            "diffgeo.surfaces.gauss_bonnet_theorem"]),
         keywords=["Gaussian curvature", "principal curvature", "shape operator",
                   "Theorema Egregium", "bilinear product"],
         canonical_objects=["regular surface", "shape operator", "Gauss map"]),

    node("diffgeo.surfaces.gauss_bonnet_theorem", "Gauss-Bonnet Theorem (Closed Surface)",
         "theorem", "derived", "surfaces", "curvature_topology_bridge",
         "INTEGRAL(K) = 2*pi*chi",
         "\\int_M K \\, dA = 2\\pi \\chi(M)",
         [{"form_id": "with_boundary", "notation_system": "ascii",
           "expression": "INTEGRAL(K) + BOUNDARYINTEGRAL(k_g) = 2*pi*chi(M)",
           "scope_note": "Version for a compact surface with boundary; the geodesic curvature of the boundary makes up the difference"},
          {"form_id": "genus", "notation_system": "ascii",
           "expression": "INTEGRAL(K) = 4*pi*(1 - g)",
           "scope_note": "For an orientable closed surface of genus g, using chi = 2 - 2g"},
          {"form_id": "sphere", "notation_system": "ascii",
           "expression": "INTEGRAL(1/R^2) over a sphere of radius R = (1/R^2)*(4*pi*R^2) = 4*pi = 2*pi*2",
           "scope_note": "The radius cancels: every round sphere has the same total curvature, which is the theorem in one line"},
          {"form_id": "triangle", "notation_system": "ascii",
           "expression": "angle sum of a geodesic triangle - pi = INTEGRAL(K) over the triangle",
           "scope_note": "The local form; the excess of the angle sum over pi is the enclosed curvature"}],
         "normalized_topological_invariant", "INTEGRAL(CURVATURE) = CONSTANT * EULERCHAR",
         [slot("CURVATURE", "variable", "integrand_density"),
          slot("CONSTANT", "constant", "normalizing_factor"),
          slot("EULERCHAR", "variable", "topological_invariant")],
         ["The left side is analytic and depends on the metric at every point; "
          "the right side is an integer times a fixed constant and depends on "
          "nothing but the homeomorphism type. The whole content of the theorem "
          "is that the two sides are equal, and the template makes that "
          "asymmetry visible as `call = constant * slot`.",
          "The normalizing constant is declared `constant`, not `parameter`: it "
          "is 2*pi and nothing else. That declaration is what puts a P in the "
          "typed skeleton and, as noted in the significance field, is one of the "
          "two reasons this node cannot twin with its own combinatorial half.",
          "Deforming the metric moves curvature around the surface but cannot "
          "change the integral, so the statement is a conservation law for total "
          "curvature under smooth deformation.",
          "The Euler characteristic slot is held as a bare slot here and as a "
          "call `EULERCHAR(.)` throughout data/differential_topology, because "
          "here it is a number on the right-hand side and there it is an "
          "invariant applied to a space. The matcher cannot relate a slot to a "
          "call head, so the same invariant is structurally invisible across the "
          "two corpora; recorded in docs/BACKLOG.md."],
         [sym("K", "variable", "integrand_density",
              "Gaussian curvature, integrated against the area element."),
          sym("chi", "variable", "topological_invariant",
              "Euler characteristic of the surface: an integer, 2 for the sphere, "
              "0 for the torus, 2 - 2g in general."),
          sym("M", "set", "domain",
              "Compact oriented surface without boundary."),
          sym("pi", "constant", "normalizing_factor",
              "Half the normalizing constant; the factor is 2*pi.")],
         [EQ, MUL],
         "The total Gaussian curvature of a closed surface equals 2*pi times its "
         "Euler characteristic: bending the surface redistributes curvature but "
         "never changes the total, which is fixed by how many holes it has.",
         "The bridge node this corpus was built around, and the one that twins "
         "with nothing. Its typed skeleton `INTEGRAL⟨?0:V⟩ = *(?1:P, ?2:V)` is a "
         "singleton across all twelve corpora, and the interesting part is that "
         "it is a singleton *next to its own other half*. "
         "difftop.vectorfields.poincare_hopf_index_theorem says the same thing "
         "with a sum of integer indices where this says an integral of a smooth "
         "density -- Chern's proof derives one from the other -- yet its skeleton "
         "is `EULERCHAR⟨?0:V⟩ = sum⟨?1:V⟩` and the two share not one node. Three "
         "separate features of the matcher each independently block the match: "
         "`sum_i` becomes the head `sum` while `INTEGRAL(.)` becomes the head "
         "`INTEGRAL`, and the two are unrelated strings; the Euler characteristic "
         "is a slot here and a call head there; and Gauss-Bonnet carries an "
         "explicit normalizing constant that the already-integer index sum does "
         "not. None of the three is a bug exactly, but together they mean the "
         "corpus's single most famous curvature-to-topology identity produces no "
         "machine-visible structure at all. That is the most useful negative "
         "result in this corpus and it is recorded in docs/BACKLOG.md rather than "
         "papered over. (A parallel branch is authoring algebraic topology and "
         "will own `algtop.invariants.euler_characteristic_surface`; the "
         "`composed_with` edge to it is a one-line addition to this node once "
         "that corpus lands -- see the module docstring for why it is not written "
         "yet.)",
         ["Compact surface without boundary; with boundary an extra geodesic-curvature term appears",
          "Orientable, or the statement is read on the orientation double cover",
          "Metric smooth enough for the curvature to be integrable",
          "Curvature integrated against the Riemannian area element, not the coordinate measure"],
         [GAUSS1827, BONNET1848, CHERN1944, DOCARMO1976, SPIVAK1999],
         disciplines=["differential_geometry", "differential_topology"],
         functionals=[INTEGRAL_FN],
         constants=[TWOPI_CONST],
         failure_modes=[
             "The theorem constrains the total, not the distribution. A surface "
             "with chi = 0 may be wildly curved everywhere as long as the "
             "positive and negative curvature cancel; concluding 'flat' from "
             "'total curvature zero' is the standard error.",
             "For surfaces with boundary the equality fails without the geodesic "
             "curvature term, and quoting the closed-surface form for a disk "
             "gives 0 = 2*pi.",
             "The higher-dimensional generalization is not the same statement: "
             "Chern-Gauss-Bonnet integrates the Pfaffian of the curvature form, "
             "which reduces to K only in dimension two, and there is no version "
             "in odd dimensions because the Euler characteristic vanishes there."],
         inferential_links=GAUSS_BONNET_LINKS,
         keywords=["Gauss-Bonnet", "total curvature", "Euler characteristic",
                   "topological invariant", "bridge node", "honest miss"],
         canonical_objects=["compact oriented surface", "Gaussian curvature",
                            "Euler characteristic"]),

    node("diffgeo.stokes.stokes_theorem", "Stokes' Theorem for Differential Forms",
         "theorem", "derived", "exterior_calculus", "integration_by_parts",
         "INTEGRAL(d(omega)) = BOUNDARYINTEGRAL(omega)",
         "\\int_M d\\omega = \\int_{\\partial M} \\omega",
         [{"form_id": "divergence_theorem", "notation_system": "ascii",
           "expression": "INTEGRAL(div(V)) = BOUNDARYINTEGRAL(<V, n>)",
           "scope_note": "The (n-1)-form case in R^n: Gauss's divergence theorem"},
          {"form_id": "classical_stokes", "notation_system": "ascii",
           "expression": "INTEGRAL(<curl(V), n>) = BOUNDARYINTEGRAL(<V, T>)",
           "scope_note": "The 1-form case on a surface in R^3: the Kelvin-Stokes curl theorem"},
          {"form_id": "greens_theorem", "notation_system": "ascii",
           "expression": "INTEGRAL(D(Q)/D(x) - D(P)/D(y)) = BOUNDARYINTEGRAL(P*dx + Q*dy)",
           "scope_note": "The 1-form case in the plane: Green's theorem"},
          {"form_id": "ftc", "notation_system": "ascii",
           "expression": "INTEGRAL(D(F)) = F(b) - F(a)",
           "scope_note": "The 0-form case on an interval: the fundamental theorem of calculus, stated as a node of its own"}],
         "boundary_transfer_operator", "INTEGRAL(D(FORM)) = BOUNDARYINTEGRAL(FORM)",
         [slot("FORM", "functional", "integrand_form")],
         ["One slot, appearing twice. The whole statement is that differentiating "
          "inside the region and restricting to the boundary are the same "
          "operation, and the single repeated slot is what says so.",
          "Duality between the exterior derivative and the boundary operator: d "
          "is adjoint to the boundary map under integration, which is why "
          "d o d = 0 and boundary o boundary = 0 are the same fact seen from two "
          "sides.",
          "Dimension-free. The same template covers the fundamental theorem of "
          "calculus, Green's theorem, the Kelvin-Stokes curl theorem and the "
          "divergence theorem; every classical vector-calculus integral theorem "
          "is an instance with a different form degree.",
          "The region is not a slot. Neither `INTEGRAL(.)` nor "
          "`BOUNDARYINTEGRAL(.)` names its domain, because the grammar has no "
          "binder, so the fact that the two domains are related by 'boundary of' "
          "lives entirely in the head names and cannot be checked."],
         [sym("omega", "variable", "integrand_form",
              "Smooth (k-1)-form with compact support on an oriented "
              "k-manifold with boundary.", 1),
          sym("M", "set", "domain",
              "Oriented smooth manifold with boundary over which the exterior "
              "derivative is integrated.")],
         [EQ],
         "The integral of a derivative over a region equals the integral of the "
         "original object over that region's boundary.",
         "Authored as the honest general statement, with the knowledge that it "
         "would not twin with anything -- and it does not. Its typed skeleton is "
         "`BOUNDARYINTEGRAL⟨?0:V⟩ = INTEGRAL⟨D⟨?0:V⟩⟩` while "
         "calculus.integration.ftc_evaluation_part sits on "
         "`INTEGRAL⟨D⟨?0:V⟩⟩ = +(F⟨?1:V⟩, neg(F⟨?2:V⟩))`. The left-hand sides are "
         "identical; the right-hand sides are not, because FTC spells the "
         "boundary integral out as a signed two-point evaluation and this node "
         "keeps it as one opaque call. Both spellings are correct: integrating a "
         "0-form over the oriented 0-manifold {a, b} *is* F(b) - F(a). But the "
         "matcher compares call heads literally, so a statement that names its "
         "boundary operator can never meet one that expands it. Rather than "
         "distort either node, the corpus carries "
         "diffgeo.stokes.stokes_zero_form_case, which states the k = 0 case in "
         "FTC's own vocabulary and does twin exactly. The pair measures something "
         "worth measuring: the gap between 'the same theorem' and 'the same "
         "template' is one act of notational translation, and somebody has to "
         "perform it by hand.",
         ["Oriented smooth manifold with boundary, boundary given the induced orientation",
          "The form is smooth and compactly supported, or the manifold is compact",
          "Degree of the form is one less than the dimension of the manifold",
          "Both integrals taken with respect to the orientation, so signs are not free"],
         [SPIVAK1965, CARTAN1899, STOKES1854, LEE2013, BOTT1982],
         disciplines=DG,
         functionals=[INTEGRAL_FN, BOUNDARY_INTEGRAL_FN, D_FN],
         failure_modes=[
             "Orientation is not optional. Reversing the induced orientation on "
             "the boundary flips the sign of the right-hand side, and most "
             "sign errors in applied vector calculus are exactly this.",
             "Compact support or compactness is needed. On a non-compact manifold "
             "with a form that does not decay, both sides can be infinite or the "
             "equality can fail outright.",
             "Corners and non-smooth boundaries need a separate argument; the "
             "theorem as stated assumes a smooth boundary, and the standard "
             "extension to manifolds with corners is a theorem, not a remark."],
         inferential_links=links(
             generalizes=["diffgeo.stokes.stokes_zero_form_case"],
             composed_with=["diffgeo.surfaces.gauss_bonnet_theorem"]),
         keywords=["Stokes theorem", "exterior derivative", "boundary",
                   "differential form", "duality", "honest miss"],
         canonical_objects=["oriented manifold with boundary", "differential form",
                            "exterior derivative"]),

    node("diffgeo.stokes.stokes_zero_form_case",
         "Stokes' Theorem for a 0-Form (Gradient Theorem for Line Integrals)",
         "theorem", "derived", "exterior_calculus", "integration_by_parts",
         "INTEGRAL(d(f)) = f(q) - f(p)",
         "\\int_c df = f(q) - f(p)",
         [{"form_id": "gradient", "notation_system": "vector_notation",
           "expression": "INTEGRAL(<grad(f), dr>) = f(q) - f(p)",
           "scope_note": "Classical gradient theorem: the line integral of a gradient depends only on the endpoints"},
          {"form_id": "boundary_chain", "notation_system": "ascii",
           "expression": "INTEGRAL(d(f)) = BOUNDARYINTEGRAL(f), with boundary(c) = q - p as an oriented 0-chain",
           "scope_note": "The general Stokes form; the right side unpacks to a signed sum over the two boundary points"},
          {"form_id": "conservative_field", "notation_system": "ascii",
           "expression": "INTEGRAL(d(f)) = 0 around any closed curve",
           "scope_note": "Path independence: the reason a conservative force field has a potential"}],
         "boundary_difference_evaluation",
         "INTEGRAL(D(F)) = F(ENDPOINT) - F(STARTPOINT)",
         [slot("F", "functional", "potential_zero_form"),
          slot("ENDPOINT", "variable", "terminal_boundary_point"),
          slot("STARTPOINT", "variable", "initial_boundary_point")],
         ["An integral over a one-dimensional domain collapses to a signed "
          "difference of two boundary values: the interior of the path is "
          "irrelevant to the total. This is the invariant "
          "calculus.integration.ftc_evaluation_part states in the same words, "
          "because it is the same invariant.",
          "The two boundary points carry opposite signs, which is the induced "
          "orientation on a 0-manifold. A signed count of points is what a "
          "0-dimensional integral is, and the minus sign in the template is that "
          "orientation and not an arithmetic accident.",
          "The potential is determined only up to an additive constant, which "
          "cancels in the difference -- the same reason the antiderivative in FTC "
          "is not unique and the same reason it does not matter.",
          "The call head is spelled `F` deliberately, matching the head "
          "scripts/seed_calculus.py uses for the antiderivative. The matcher "
          "compares heads literally, so this spelling is what makes the twin fire; "
          "it is a translation into an existing vocabulary, exactly as "
          "scripts/seed_infotheory.py adopted CARD/MEET/JOIN from the set-theory "
          "corpus."],
         [sym("f", "variable", "potential_zero_form",
              "Smooth real-valued function on the manifold: a 0-form."),
          sym("p", "variable", "initial_boundary_point",
              "Initial point of the oriented curve."),
          sym("q", "variable", "terminal_boundary_point",
              "Terminal point of the oriented curve."),
          sym("c", "variable", "path",
              "Piecewise smooth oriented curve from p to q.")],
         [EQ, SUB],
         "The integral of the differential of a function along a path is the "
         "function's value at the far end minus its value at the near end, "
         "whatever route the path takes.",
         "The corpus's second sought cross-discipline typed twin, and the one "
         "that required an act of translation to obtain. Its typed skeleton "
         "`INTEGRAL⟨D⟨?0:V⟩⟩ = +(F⟨?1:V⟩, neg(F⟨?2:V⟩))` is shared character for "
         "character with calculus.integration.ftc_evaluation_part, and it carries "
         "that node's archetype id, `boundary_difference_evaluation`, so no "
         "label drift is reported. The claim is identity, not resemblance: the "
         "fundamental theorem of calculus is Stokes' theorem for a 0-form on a "
         "compact oriented 1-manifold with boundary, and the only differences "
         "between the two nodes are that this one lives on a manifold rather than "
         "an interval and calls `D` the exterior derivative rather than the "
         "derivative -- on a 0-form in one variable those are the same operator. "
         "What the pair demonstrates about the tooling is less flattering than "
         "what it demonstrates about mathematics. The general statement, "
         "diffgeo.stokes.stokes_theorem, is the one a geometer would write, and "
         "it twins with nothing; this node twins only because it was written in "
         "the target's vocabulary by an author who already knew the answer. "
         "Structural matching over anonymized templates finds analogies between "
         "*notations*, and a shared abstraction has to be adopted into notation "
         "before it becomes visible.",
         ["Piecewise smooth oriented curve with two endpoints, lying in the domain of f",
          "f continuously differentiable on a neighbourhood of the curve",
          "Endpoints distinct and ordered by the orientation; for a closed curve both sides are zero",
          "The manifold need not be simply connected: this is about exact forms, not closed ones"],
         [SPIVAK1965, LEE2013, DOCARMO1992],
         disciplines=DG,
         functionals=[INTEGRAL_FN, D_FN, F_FN],
         failure_modes=[
             "The converse needs topology. A closed 1-form has vanishing line "
             "integrals around contractible loops but not around all loops, so "
             "'path independent implies gradient' requires simple connectedness "
             "-- the failure is measured by de Rham cohomology.",
             "The form must actually be exact. Applying the formula to d(theta) "
             "on the punctured plane gives 2*pi around the origin instead of 0, "
             "and that discrepancy is the generator of H^1."],
         inferential_links=links(
             special_case_of=["diffgeo.stokes.stokes_theorem"],
             composed_with=["diffgeo.curves.arc_length_functional"]),
         keywords=["gradient theorem", "line integral", "fundamental theorem of calculus",
                   "exact form", "path independence", "typed twin"],
         canonical_objects=["oriented curve", "0-form", "exterior derivative"]),
]


# --------------------------------------------------------------------------
# Differential topology
# --------------------------------------------------------------------------

DT = ["differential_topology"]

DIFFTOP_NODES = [

    node("difftop.invariants.euler_characteristic_diffeomorphism_invariance",
         "Diffeomorphism Invariance of the Euler Characteristic",
         "theorem", "derived", "invariants", "diffeomorphism_invariance",
         "chi(M) = chi(N) whenever M and N are diffeomorphic",
         "M \\cong N \\;\\Longrightarrow\\; \\chi(M) = \\chi(N)",
         [{"form_id": "homotopy", "notation_system": "ascii",
           "expression": "chi(M) = chi(N) whenever M and N are homotopy equivalent",
           "scope_note": "The stronger statement: chi is a homotopy invariant, so diffeomorphism invariance is a corollary"},
          {"form_id": "triangulation", "notation_system": "ascii",
           "expression": "chi = V - E + F, independent of the triangulation chosen",
           "scope_note": "The combinatorial definition; independence of triangulation is the same theorem in another dress"},
          {"form_id": "betti", "notation_system": "ascii",
           "expression": "chi(M) = sum_i (-1)^i * b_i(M)",
           "scope_note": "Alternating sum of Betti numbers, which is where the algebraic-topology corpus takes over"}],
         "invariant_under_equivalence", "EULERCHAR(SOURCE) = EULERCHAR(TARGET)",
         [slot("SOURCE", "set", "equivalent_object_first"),
          slot("TARGET", "set", "equivalent_object_second")],
         ["The equivalence hypothesis -- that the two spaces are diffeomorphic -- "
          "is nowhere in the template. The grammar has no implication connective "
          "usable at top level with these operands, so the statement reduces to "
          "its conclusion and the hypothesis lives in regularity_conditions. Any "
          "invariance statement anyone adds later will lose its hypothesis the "
          "same way.",
          "The same functional head applied to both operands, which is what makes "
          "this the shape of *every* invariance claim: F(x) = F(y) whenever x ~ y. "
          "It is a template worth having even though it currently twins with "
          "nothing.",
          "Euler characteristic is held as a call here and as a bare slot in "
          "diffgeo.surfaces.gauss_bonnet_theorem, which is why the two corpora "
          "cannot see that they are talking about the same integer.",
          "Multiplicative under products and additive under disjoint union, "
          "neither of which this template records; those would be separate nodes."],
         [sym("chi", "variable", "invariant_value",
              "Euler characteristic: an integer attached to the space."),
          sym("M", "set", "equivalent_object_first", "First smooth manifold."),
          sym("N", "set", "equivalent_object_second",
              "Second smooth manifold, diffeomorphic to the first.")],
         [EQ],
         "Diffeomorphic manifolds have the same Euler characteristic, so the "
         "number is a property of the space rather than of any description of it.",
         "The node that licenses every other appearance of the Euler "
         "characteristic in these two corpora. Without it, the chi on the right "
         "of Gauss-Bonnet would be a number attached to a particular smooth "
         "structure and the theorem would say much less. Structurally it is a "
         "singleton -- `EULERCHAR⟨?0:V⟩ = EULERCHAR⟨?1:V⟩` matches nothing -- and "
         "the reason is instructive: the corpus has plenty of invariance claims "
         "(entropy under relabelling, arc length under reparameterization, "
         "Gaussian curvature under isometry) but every one of them is stated in "
         "prose inside an `invariants` array rather than as a template. This is "
         "the first node to put an invariance claim in the template itself, and "
         "if others follow the shape F(x) = F(y) it will stop being a singleton. "
         "The algebraic-topology corpus being authored in parallel will own the "
         "computational nodes for chi (planned "
         "`algtop.invariants.euler_characteristic_surface`); this node is the "
         "differential-topology half, asserting that the invariant is well "
         "defined on diffeomorphism classes.",
         ["M and N smooth compact manifolds, possibly with boundary",
          "A diffeomorphism between them exists -- the hypothesis the template cannot carry",
          "Both admit finite triangulations, so the combinatorial definition applies"],
         [MILNOR1965, GP1974, LEE2013],
         disciplines=DT,
         functionals=[EULERCHAR_FN],
         failure_modes=[
             "The converse is false and badly so: equal Euler characteristics do "
             "not imply diffeomorphism, or even homotopy equivalence. The torus "
             "and the Klein bottle both have chi = 0.",
             "In odd dimensions the Euler characteristic of a closed manifold is "
             "always zero, so the invariant carries no information there and "
             "arguments that rely on it silently do nothing."],
         inferential_links=links(
             composed_with=["difftop.vectorfields.poincare_hopf_index_theorem",
                            "difftop.morse.weak_morse_inequality"]),
         keywords=["Euler characteristic", "diffeomorphism invariance",
                   "topological invariant", "well-definedness"],
         canonical_objects=["smooth compact manifold", "diffeomorphism",
                            "Euler characteristic"]),

    node("difftop.degree.degree_regular_value_count",
         "Degree of a Smooth Map as a Signed Preimage Count",
         "definition", "formal", "mapping_degree", "degree",
         "deg(f) = sum_i sign(det(Df(x_i)))",
         "\\deg(f) = \\sum_{x \\in f^{-1}(y)} \\operatorname{sign}\\det(Df_x)",
         [{"form_id": "homology", "notation_system": "ascii",
           "expression": "f_* : H_n(M) -> H_n(N) is multiplication by deg(f)",
           "scope_note": "The homological definition, which the algebraic-topology corpus will own"},
          {"form_id": "form_integral", "notation_system": "ascii",
           "expression": "INTEGRAL(f^*(omega)) = deg(f) * INTEGRAL(omega) for any top form omega",
           "scope_note": "De Rham version: degree is the factor by which pullback scales total integrals"},
          {"form_id": "circle", "notation_system": "ascii",
           "expression": "deg(z -> z^n) = n on the unit circle",
           "scope_note": "The winding-number case, where the signed count is visibly a count"}],
         "signed_index_sum", "DEGREE(SMOOTHMAP) = sum_i SIGN_i",
         [slot("SMOOTHMAP", "functional", "map_between_manifolds"),
          slot("SIGN_i", "variable", "local_orientation_sign")],
         ["A local-to-global statement: a global invariant of the map is a finite "
          "sum of purely local data, one term per preimage point. The same shape "
          "as difftop.vectorfields.poincare_hopf_index_theorem, but with a "
          "different left-hand head, which is why the two do not twin even though "
          "they are the same idea.",
          "Independent of the regular value chosen, which is the substance of the "
          "definition and is invisible in the template -- the value y appears "
          "nowhere, and the grammar has no binder that could introduce it.",
          "Each summand is +1 or -1. The template declares SIGN_i a `variable` "
          "because it varies over the index set, but it takes only two values, and "
          "that quantization is what makes the total an integer.",
          "Homotopy invariant, so degree descends to homotopy classes of maps -- "
          "the property that turns it into a tool rather than a computation.",
          "The index suffix is a suffix by necessity: an identifier beginning "
          "`sum_` would be parsed as a prefix big-operator (docs/BACKLOG.md), so "
          "indexed slots in this corpus are named `SIGN_i`, never `SUM_SIGN`."],
         [sym("f", "variable", "map_between_manifolds",
              "Smooth map between compact oriented manifolds of equal dimension."),
          sym("y", "variable", "regular_value",
              "Regular value of f, whose preimage is finite."),
          sym("x", "variable", "preimage_point",
              "A point of the preimage, at which the Jacobian determinant is nonzero.")],
         [EQ, SUM],
         "The degree of a map is what you get by counting the preimages of a "
         "typical point with a plus or minus depending on whether the map "
         "preserves or reverses orientation there.",
         "A singleton at `DEGREE⟨?0:V⟩ = sum⟨?1:V⟩`, and its nearest neighbour is "
         "in its own corpus: difftop.vectorfields.poincare_hopf_index_theorem is "
         "`EULERCHAR⟨?0:V⟩ = sum⟨?1:V⟩`, identical except for the left-hand call "
         "head. That is not a coincidence the matcher is missing -- the two "
         "theorems are the same theorem, since the index of a vector field at a "
         "zero is the local degree of the associated Gauss map -- but the matcher "
         "compares heads literally and DEGREE is not EULERCHAR. The pair is the "
         "cheapest available demonstration that head-level literalness is the "
         "binding constraint on this corpus: two nodes that differ in exactly one "
         "identifier, written by the same author on the same afternoon, do not "
         "meet.",
         ["f smooth, M and N compact oriented of the same dimension, N connected",
          "y a regular value of f, which exists for almost every y by Sard's theorem",
          "The preimage is finite, which follows from compactness and regularity",
          "Orientations fixed on both manifolds; reversing either flips the sign"],
         [MILNOR1965, GP1974, BOTT1982],
         disciplines=DT,
         functionals=[DEGREE_FN],
         index_sets=[IDX_PREIMAGE],
         failure_modes=[
             "Degree is defined only between manifolds of equal dimension and only "
             "when both are oriented; for non-orientable targets there is a "
             "mod-2 degree instead, which loses the sign and most of the power.",
             "Computing the sum at a critical value is meaningless. The count is "
             "unstable there, and Sard's theorem is what guarantees a legal value "
             "exists rather than what finds one."],
         inferential_links=links(
             entails=["difftop.degree.degree_multiplicativity"],
             composed_with=["difftop.degree.brouwer_fixed_point",
                            "difftop.vectorfields.poincare_hopf_index_theorem"]),
         keywords=["degree", "regular value", "Sard's theorem", "winding number",
                   "signed count", "local to global"],
         canonical_objects=["smooth map", "compact oriented manifold", "regular value"]),

    node("difftop.degree.degree_multiplicativity",
         "Multiplicativity of Degree Under Composition",
         "theorem", "derived", "mapping_degree", "degree",
         "deg(g o f) = deg(g) * deg(f)",
         "\\deg(g \\circ f) = \\deg(g)\\,\\deg(f)",
         [{"form_id": "functorial", "notation_system": "ascii",
           "expression": "deg is a monoid homomorphism from self-maps under composition to integers under multiplication"},
          {"form_id": "diffeomorphism", "notation_system": "ascii",
           "expression": "deg(f) = +1 or -1 for a diffeomorphism, and deg(f^-1) = deg(f)",
           "scope_note": "The invertible case, obtained by composing with the inverse"},
          {"form_id": "circle_powers", "notation_system": "ascii",
           "expression": "deg((z -> z^m) o (z -> z^n)) = m*n",
           "scope_note": "The winding-number case, where multiplicativity is visible by inspection"}],
         "composition_factorization",
         "DEGREE(COMPOSE(OUTER, INNER)) = DEGREE(OUTER) * DEGREE(INNER)",
         [slot("OUTER", "functional", "outer_map"),
          slot("INNER", "functional", "inner_map")],
         ["Both slots appear twice: once inside the composition on the left and "
          "once alone on the right. That repetition is the whole content of a "
          "homomorphism law, and it is what distinguishes this from a statement "
          "that merely relates three unrelated degrees.",
          "The argument order of COMPOSE is fixed to outer-then-inner, matching "
          "the convention scripts/seed_calculus.py established for the chain "
          "rule. Call arguments are ordered for the matcher (docs/BACKLOG.md), so "
          "this is a convention that has to be stated and kept.",
          "Multiplication is commutative but composition is not, so the "
          "right-hand side is symmetric while the left-hand side is not. The "
          "matcher's canonical sort will reorder the product but never the "
          "composition, which is correct and is the reason the template is not "
          "self-twinning under argument swap.",
          "Degree of the identity is 1 and degree of a constant map is 0, which "
          "together with this law makes the degree a monoid homomorphism onto the "
          "integers under multiplication."],
         [sym("f", "variable", "inner_map", "Inner smooth map."),
          sym("g", "variable", "outer_map", "Outer smooth map."),
          sym("n", "variable", "degree_value",
              "Integer degree; the codomain of the homomorphism.")],
         [EQ, MUL],
         "Composing two maps multiplies their degrees, so degree turns "
         "composition into multiplication.",
         "The near-miss this corpus most wanted to land, and did not. "
         "calculus.differentiation.chain_rule is "
         "`D(COMPOSE(OUTER, INNER)) = COMPOSE(D(OUTER), INNER) * D(INNER)`; this "
         "node is `DEGREE(COMPOSE(OUTER, INNER)) = DEGREE(OUTER) * DEGREE(INNER)`. "
         "Both say that an invariant of a composite factorizes into a product of "
         "invariants of the factors, both use the same COMPOSE head with the same "
         "argument order, and both were written to be compared. They do not twin, "
         "and the reason is mathematically real rather than a notational "
         "accident: the chain rule's right-hand side has to *transport* the outer "
         "derivative along the inner map -- the extra `COMPOSE(D(OUTER), INNER)` "
         "-- because the derivative at a point lives in a tangent space that "
         "depends on the point. Degree has no such dependence; it is a single "
         "integer for the whole map, so no transport is needed and the "
         "factorization is bare. So the structural difference between the two "
         "templates is exactly the difference between a pointwise invariant and a "
         "global one. That is the most satisfying negative result in these two "
         "corpora: the matcher found no twin, and the missing subterm is the "
         "content. Both nodes share the archetype id "
         "`composition_factorization`, which makes the matcher report them under "
         "'archetype ids spanning multiple structures' -- an intentional use of "
         "that diagnostic to record a hand-asserted kinship the skeletons do not "
         "carry.",
         ["All three maps between compact oriented manifolds of the same dimension",
          "Target manifolds connected, so degree is well defined",
          "Orientations fixed and consistent; the composite inherits them",
          "Smoothness of both factors, or continuity plus the homological definition"],
         [MILNOR1965, GP1974, BOTT1982],
         disciplines=DT,
         functionals=[DEGREE_FN, COMPOSE_FN],
         failure_modes=[
             "Multiplicativity needs the middle manifold connected. Through a "
             "disconnected intermediate the degrees can fail to multiply because "
             "'the' degree is not well defined there.",
             "Read as a statement about winding numbers of plane curves it is "
             "true only for maps of the circle to itself; the winding number of a "
             "composite of curves in the plane is not a product."],
         inferential_links=links(
             entailed_by=["difftop.degree.degree_regular_value_count"],
             composed_with=["difftop.degree.brouwer_fixed_point"]),
         keywords=["degree", "composition", "homomorphism", "chain rule",
                   "multiplicativity", "honest miss"],
         canonical_objects=["smooth map", "composition", "mapping degree"]),

    node("difftop.degree.brouwer_fixed_point", "Brouwer Fixed-Point Theorem",
         "theorem", "derived", "mapping_degree", "fixed_points",
         "there exists x with f(x) = x",
         "\\exists\\, x \\in D^n : f(x) = x",
         [{"form_id": "no_retraction", "notation_system": "ascii",
           "expression": "there is no smooth retraction of the disk onto its boundary sphere",
           "scope_note": "The equivalent statement the degree argument actually proves; a retraction would need degree 1 and 0 at once"},
          {"form_id": "degree_argument", "notation_system": "ascii",
           "expression": "if f had no fixed point, DEGREE(r) would be both 0 and 1",
           "scope_note": "The contradiction: a fixed-point-free self-map builds a retraction, whose degree is forced two ways"},
          {"form_id": "one_dimensional", "notation_system": "ascii",
           "expression": "a continuous f from [a,b] to [a,b] has a fixed point",
           "scope_note": "The case n = 1, which is the intermediate value theorem applied to f(x) - x"}],
         "fixed_point_equation", "FIXEDPOINT = SELFMAP(FIXEDPOINT)",
         [slot("FIXEDPOINT", "variable", "invariant_point"),
          slot("SELFMAP", "functional", "self_map")],
         ["One slot appearing on both sides of the equality, once bare and once "
          "under the map. That self-reference is the definition of a fixed point "
          "and is the only structure the template carries.",
          "The existential quantifier is not in the template. The theorem asserts "
          "that a solution exists; the template states only the equation to be "
          "solved. The grammar has identifiers, arithmetic, calls and relations "
          "and no quantifier at all, so this is the same class of loss as "
          "infotheory.channel.channel_capacity's missing binder -- the statement "
          "parses, the logical force does not survive.",
          "Non-constructive. The degree argument proves that no fixed-point-free "
          "self-map exists without exhibiting a fixed point, and Sperner's lemma "
          "and Scarf's algorithm are separate work.",
          "Requires the domain to be its own codomain, which is why SELFMAP is a "
          "distinct head from the general smooth maps in "
          "difftop.degree.degree_regular_value_count."],
         [sym("x", "variable", "invariant_point",
              "Point fixed by the map, whose existence is asserted."),
          sym("f", "variable", "self_map",
              "Continuous map of the closed ball to itself."),
          sym("n", "variable", "dimension",
              "Dimension of the ball; the theorem holds for every n >= 0.")],
         [EQ],
         "Every continuous map of a closed ball to itself leaves at least one "
         "point where it started.",
         "Included as the fixed-point end of the degree machinery, and it is a "
         "structural singleton -- `?0:V = SELFMAP⟨?0:V⟩` matches nothing. The "
         "near neighbours are worth naming because they are near in the way that "
         "matters: logic.boolean_laws.double_negation is "
         "`?0 = NEG⟨NEG⟨?0⟩⟩`, settheory.boolean_laws.idempotence is "
         "`?0 = MEET⟨?0, ?0⟩`, and calculus.integration.ftc_differentiation_part "
         "is `?0 = D⟨INTEGRAL⟨?0⟩⟩`. All four are 'an operation that returns its "
         "argument', and all four have different arities or nesting depths, so no "
         "two of them meet. There is a real family here -- fixed points of "
         "operators, idempotents, involutions, left inverses -- and the matcher "
         "as built cannot see it, because it works on exact skeletons and the "
         "family is defined by a *property* of the skeleton (the argument slot "
         "recurring at the root) rather than by its shape. That would need a "
         "different query than twin detection: something like 'find templates "
         "where one slot occurs on both sides of the relation at different "
         "depths'. Recorded in docs/BACKLOG.md as a wanted match level.",
         ["Domain homeomorphic to a closed finite-dimensional ball: compact, convex, non-empty",
          "Map continuous; smoothness is not needed and the smooth case implies the general one by approximation",
          "Fails for open balls, for spheres, and in infinite dimensions without extra compactness"],
         [BROUWER1911, MILNOR1965, GP1974],
         disciplines=DT,
         functionals=[SELFMAP_FN, DEGREE_FN],
         failure_modes=[
             "Convexity or its topological equivalent is essential. A rotation of "
             "the annulus and an irrational rotation of the circle are "
             "fixed-point free, and the disk's contractibility is what rules that "
             "out.",
             "In infinite dimensions the theorem is false as stated; Schauder's "
             "version needs compactness of the map, and Kakutani's set-valued "
             "version needs upper hemicontinuity. Economists citing 'Brouwer' for "
             "an equilibrium existence proof almost always mean Kakutani.",
             "Non-constructive: knowing a fixed point exists gives no bound on how "
             "hard it is to find, and computing one is PPAD-complete."],
         inferential_links=links(
             composed_with=["difftop.degree.degree_regular_value_count",
                            "difftop.degree.degree_multiplicativity"]),
         keywords=["Brouwer", "fixed point", "degree", "retraction",
                   "non-constructive", "missing quantifier"],
         canonical_objects=["closed ball", "continuous self-map", "retraction"]),

    node("difftop.morse.weak_morse_inequality", "Weak Morse Inequality",
         "theorem", "derived", "morse_theory", "critical_points",
         "c_k >= b_k", "c_k \\ge b_k",
         [{"form_id": "strong", "notation_system": "ascii",
           "expression": "c_k - c_(k-1) + ... ± c_0 >= b_k - b_(k-1) + ... ± b_0",
           "scope_note": "The strong Morse inequalities: alternating partial sums, of which the weak form is the leading consequence"},
          {"form_id": "morse_equality", "notation_system": "ascii",
           "expression": "sum_k (-1)^k * c_k = sum_k (-1)^k * b_k = chi(M)",
           "scope_note": "The alternating sums are equal and both compute the Euler characteristic"},
          {"form_id": "existence", "notation_system": "ascii",
           "expression": "a Morse function on a compact M has at least sum_k b_k critical points",
           "scope_note": "Summing the weak inequalities: topology forces critical points to exist"}],
         "componentwise_lower_bound", "CRITICALCOUNT_k >= BETTINUMBER_k",
         [slot("CRITICALCOUNT_k", "variable", "analytic_count"),
          slot("BETTINUMBER_k", "variable", "topological_count")],
         ["A relational statement with no output slot and no operator between the "
          "operands: the entire content is that one integer bounds another, and "
          "the template is as thin as a template can be while still saying "
          "something.",
          "Analytic on the left, topological on the right. Critical points depend "
          "on the choice of Morse function; Betti numbers do not. The inequality "
          "is therefore a bound that holds for every choice, and the interesting "
          "question -- whether it is attained, i.e. whether a perfect Morse "
          "function exists -- is a separate and often hard problem.",
          "Index-matched: the bound holds degree by degree, which is strictly "
          "stronger than bounding the total number of critical points, and it is "
          "why the strong form with alternating sums exists at all.",
          "Both slot ids carry the degree index as a *suffix*. A slot named "
          "`MIN_COUNT` or `MAX_COUNT` would be eaten by the prefix "
          "big-operator rule (docs/BACKLOG.md), so suffix indexing is the "
          "convention here as in the information-theory corpus."],
         [sym("c_k", "variable", "analytic_count",
              "Number of critical points of index k of a Morse function on M."),
          sym("b_k", "variable", "topological_count",
              "k-th Betti number of M: the rank of its k-th homology group."),
          sym("k", "index", "degree", "Index, or degree, running from 0 to dim M.")],
         [GE],
         "A Morse function on a compact manifold must have at least as many "
         "critical points of each index as the manifold has independent cycles in "
         "that dimension.",
         "Structurally the thinnest node in either corpus -- `?0:V >= ?1:V` -- and "
         "kept anyway, because a corpus that only admitted structurally rich "
         "statements would be evidence of selection rather than of structure. The "
         "closest thing to a relative is "
         "infotheory.divergence.gibbs_inequality, which is a `>=` against the "
         "numeral 0 rather than against a second slot, so it does not twin. What "
         "the node contributes is not a skeleton but a *direction*: it is the "
         "only statement in these two corpora where topology constrains analysis "
         "rather than the other way round. Gauss-Bonnet computes a topological "
         "invariant from an analytic integral; Poincare-Hopf computes it from a "
         "count of zeros; this one runs backwards, using the topology as a floor "
         "under what any smooth function can do. The Morse equality in the "
         "equivalent_forms list closes the loop by recovering the Euler "
         "characteristic from the same counts.",
         ["M compact smooth manifold without boundary",
          "f a Morse function: all critical points non-degenerate, hence isolated",
          "Betti numbers taken over a field, so that ranks add correctly",
          "The inequality holds for every k independently, and for every Morse function"],
         [MORSE1925, MILNOR1963, GP1974],
         disciplines=DT,
         failure_modes=[
             "Degenerate critical points invalidate the count. A function with a "
             "single monkey-saddle can have fewer critical points than the "
             "inequality allows, which is why non-degeneracy is a hypothesis and "
             "not a convenience.",
             "Betti numbers over Z rather than a field bring torsion into the "
             "count and the inequality can fail; the standard statement is over a "
             "field.",
             "Attainment is not asserted. Manifolds admitting a perfect Morse "
             "function are special, and assuming the bound is tight is a common "
             "error in low-dimensional arguments."],
         inferential_links=links(
             composed_with=["difftop.invariants.euler_characteristic_diffeomorphism_invariance",
                            "difftop.vectorfields.poincare_hopf_index_theorem"]),
         keywords=["Morse theory", "critical points", "Betti number",
                   "inequality", "index"],
         canonical_objects=["Morse function", "critical point", "Betti number"]),

    node("difftop.vectorfields.poincare_hopf_index_theorem",
         "Poincare-Hopf Index Theorem",
         "theorem", "derived", "vector_fields", "index_theory",
         "chi(M) = sum_i index(V, x_i)",
         "\\chi(M) = \\sum_{x \\in \\mathrm{Zero}(V)} \\mathrm{ind}_x(V)",
         [{"form_id": "morse_gradient", "notation_system": "ascii",
           "expression": "chi(M) = sum_k (-1)^k * c_k",
           "scope_note": "For the gradient of a Morse function the index at a critical point is (-1)^k, and the theorem becomes the Morse equality"},
          {"form_id": "boundary", "notation_system": "ascii",
           "expression": "chi(M) = sum_i index(V, x_i) for V pointing outward along the boundary",
           "scope_note": "Version for manifolds with boundary, with an outward-pointing condition"},
          {"form_id": "gauss_bonnet", "notation_system": "ascii",
           "expression": "2*pi*chi(M) = INTEGRAL(K)",
           "scope_note": "The differential-geometric half of the same statement; Chern's proof passes between them"}],
         "invariant_from_local_indices", "EULERCHAR(MANIFOLD) = sum_i INDEX_i",
         [slot("MANIFOLD", "set", "ambient_space"),
          slot("INDEX_i", "variable", "local_index")],
         ["Local data summed to a global invariant, with the striking feature "
          "that the left side does not mention the vector field at all: any "
          "field with isolated zeros gives the same total, so the sum is a "
          "property of the manifold.",
          "The indices are integers of either sign, and a field can be modified "
          "to move zeros around or merge them, which changes the individual terms "
          "and never the sum. That invariance is the theorem.",
          "Same skeleton shape as difftop.degree.degree_regular_value_count "
          "except for the left-hand call head, and the resemblance is genuine: "
          "the index of a field at an isolated zero is the local degree of the "
          "normalized field on a small sphere around it.",
          "The right-hand side uses the prefix big-operator `sum_i`, which parses "
          "to the head `sum`. diffgeo.surfaces.gauss_bonnet_theorem states the "
          "same fact with `INTEGRAL(.)`, a call. The heads are unrelated strings "
          "and the two nodes cannot meet; see that node's significance field."],
         [sym("chi", "variable", "invariant_value",
              "Euler characteristic of the manifold."),
          sym("V", "variable", "vector_field",
              "Smooth tangent vector field with isolated zeros."),
          sym("x", "variable", "zero_point", "An isolated zero of the field."),
          sym("M", "set", "ambient_space",
              "Compact smooth manifold, without boundary in the basic form.")],
         [EQ, SUM],
         "For any smooth vector field with isolated zeros on a compact manifold, "
         "the signed count of its zeros equals the Euler characteristic -- so the "
         "field cannot avoid having them unless the characteristic is zero.",
         "One half of Chern's theorem, standing next to the other half in the "
         "sibling corpus and structurally invisible to it. This node is "
         "`EULERCHAR⟨?0:V⟩ = sum⟨?1:V⟩`; diffgeo.surfaces.gauss_bonnet_theorem is "
         "`INTEGRAL⟨?0:V⟩ = *(?1:P, ?2:V)`. They are the same theorem in the "
         "discrete and continuous registers -- the index sum is what the "
         "curvature integral becomes when the metric degenerates onto a "
         "triangulation -- and the matcher relates them not at all. Three "
         "independent obstacles were counted while authoring the pair: the "
         "`sum`/`INTEGRAL` head split, the Euler characteristic being a call here "
         "and a slot there, and the explicit 2*pi normalization on the "
         "Gauss-Bonnet side that the integer index sum does not need. Removing "
         "any one of them would not be enough. This is recorded in "
         "docs/BACKLOG.md as the corpus's clearest evidence that discrete and "
         "continuous statements of one fact are systematically unmatchable, which "
         "is a much larger problem than any single pair: every conservation law, "
         "every normalization, and every expectation in the graph has both forms.",
         ["M compact smooth manifold, without boundary in this form",
          "Vector field smooth with only isolated zeros; a field with a zero curve is excluded",
          "Indices computed with a consistent orientation convention",
          "For manifolds with boundary the field must point outward everywhere along it"],
         [POINCARE1885, HOPF1927, MILNOR1965, GP1974, CHERN1944],
         disciplines=DT,
         functionals=[EULERCHAR_FN],
         index_sets=[IDX_ZEROS],
         failure_modes=[
             "The theorem counts zeros with sign, so a field with many zeros can "
             "have index sum zero; 'no zeros' and 'indices cancel' are different "
             "situations that the total cannot distinguish.",
             "For manifolds with boundary the outward-pointing hypothesis is not "
             "cosmetic: an inward-pointing field gives chi of the manifold "
             "relative to its boundary instead, which differs by the boundary's "
             "own characteristic."],
         inferential_links=links(
             entails=["difftop.vectorfields.hairy_ball_theorem"],
             composed_with=["difftop.degree.degree_regular_value_count",
                            "difftop.invariants.euler_characteristic_diffeomorphism_invariance",
                            "difftop.morse.weak_morse_inequality"]),
         keywords=["Poincare-Hopf", "index", "vector field", "Euler characteristic",
                   "local to global", "Gauss-Bonnet", "honest miss"],
         canonical_objects=["compact manifold", "vector field", "isolated zero",
                            "index"]),

    node("difftop.vectorfields.hairy_ball_theorem",
         "Hairy Ball Theorem (Vanishing Characteristic is Necessary)",
         "theorem", "derived", "vector_fields", "index_theory",
         "chi(M) = 0 whenever M carries a nowhere-vanishing vector field",
         "\\text{$V$ nowhere zero on $M$} \\;\\Longrightarrow\\; \\chi(M) = 0",
         [{"form_id": "sphere", "notation_system": "ascii",
           "expression": "every continuous tangent vector field on an even-dimensional sphere vanishes somewhere",
           "scope_note": "The classical statement: chi(S^2n) = 2, so no nowhere-zero field exists -- you cannot comb a hairy ball flat"},
          {"form_id": "converse", "notation_system": "ascii",
           "expression": "a compact manifold with chi(M) = 0 admits a nowhere-vanishing vector field",
           "scope_note": "Hopf's converse: for connected compact manifolds the condition is sufficient as well as necessary"},
          {"form_id": "odd_sphere", "notation_system": "ascii",
           "expression": "S^(2n+1) carries the nowhere-zero field V(x) = (-x_2, x_1, -x_4, x_3, ...)",
           "scope_note": "Odd spheres have chi = 0 and an explicit field, which shows the parity is the whole story"}],
         "vanishing_invariant", "EULERCHAR(MANIFOLD) = 0",
         [slot("MANIFOLD", "set", "ambient_space")],
         ["A single slot against a numeric literal: the thinnest possible "
          "template that still names its subject. The hypothesis -- that a "
          "nowhere-vanishing field exists -- is absent, as in every conditional "
          "statement in these corpora, and lives in regularity_conditions.",
          "An immediate corollary of "
          "difftop.vectorfields.poincare_hopf_index_theorem: an empty sum is "
          "zero, so a field with no zeros forces the characteristic to vanish. "
          "The derivation is one line and the `entails` edge records it.",
          "The literal 0 on the right is not a slot, which places this node in "
          "the same structural category as infotheory.divergence."
          "gibbs_inequality (`... >= 0`) without twinning with it, since the "
          "relation differs.",
          "Parity is the operative fact in the classical case: chi(S^n) is 2 for "
          "even n and 0 for odd n, so the obstruction appears exactly on "
          "even-dimensional spheres."],
         [sym("chi", "variable", "invariant_value",
              "Euler characteristic, asserted to vanish."),
          sym("V", "variable", "vector_field",
              "Nowhere-vanishing smooth tangent vector field, whose existence is the hypothesis."),
          sym("M", "set", "ambient_space", "Compact smooth manifold.")],
         [EQ],
         "A compact manifold can carry a vector field that vanishes nowhere only "
         "if its Euler characteristic is zero -- which is why the hair on a "
         "sphere cannot be combed flat, and why there is always a point of zero "
         "horizontal wind speed somewhere on Earth.",
         "The corpus's smallest theorem and a useful control. Its skeleton "
         "`0 = EULERCHAR⟨?0:V⟩` twins with nothing, which is expected, but the "
         "node earns its place by being the one statement here whose *content* is "
         "entirely in its hypothesis: the template says an integer is zero, and "
         "the theorem is that a geometric condition forces it. Every conditional "
         "statement in these two corpora loses its antecedent the same way, and "
         "counting them gives a number worth having -- of sixteen nodes across "
         "the two files, four (this one, the Euler-characteristic invariance "
         "node, Brouwer, and the weak Morse inequality) are conditionals or "
         "quantified statements whose logical form the grammar cannot carry. That "
         "is a quarter of the corpus reduced to its conclusion. The matcher is "
         "not wrong to compare only what it is given; the observation is that "
         "what it is given is systematically weaker for theorems than for "
         "definitions, so twin density is not comparable across statement "
         "classes.",
         ["M compact smooth manifold",
          "The hypothesis the template cannot carry: M admits a smooth tangent vector field vanishing nowhere",
          "Tangent field, not an arbitrary map to R^n; the tangency is what makes the index defined",
          "For the classical sphere case, M = S^n with n even"],
         [HOPF1927, POINCARE1885, MILNOR1965, GP1974],
         disciplines=DT,
         functionals=[EULERCHAR_FN],
         failure_modes=[
             "The theorem gives no bound on how many zeros there are or where "
             "they sit -- only that the signed count cannot be avoided. A field "
             "on S^2 can have one zero of index 2 or two of index 1.",
             "It is about tangent fields. A nowhere-zero field of *normal* "
             "vectors, or a nowhere-zero map to R^3 that is not tangent, exists "
             "on the sphere and is not a counterexample.",
             "Odd-dimensional spheres are not exceptions to a rule; they satisfy "
             "the hypothesis because their characteristic is zero, and Hopf's "
             "converse says every such manifold does."],
         inferential_links=links(
             entailed_by=["difftop.vectorfields.poincare_hopf_index_theorem"],
             composed_with=["difftop.invariants.euler_characteristic_diffeomorphism_invariance"]),
         keywords=["hairy ball", "vector field", "Euler characteristic",
                   "obstruction", "Poincare-Hopf", "missing hypothesis"],
         canonical_objects=["even-dimensional sphere", "tangent vector field"]),
]


CORPORA = [
    ("data/differential_geometry/nodes.json",
     {"schema": "../../schema/equation-node.schema.json",
      "corpus_id": "differential_geometry.curves_surfaces_forms.v1",
      "discipline": "differential_geometry",
      "version": "1.0.0-alpha",
      "statement_nodes": DIFFGEO_NODES}),
    ("data/differential_topology/nodes.json",
     {"schema": "../../schema/equation-node.schema.json",
      "corpus_id": "differential_topology.degree_index_morse.v1",
      "discipline": "differential_topology",
      "version": "1.0.0-alpha",
      "statement_nodes": DIFFTOP_NODES}),
]


def main() -> None:
    for rel, corpus in CORPORA:
        out = Path(rel)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print(f"wrote {len(corpus['statement_nodes'])} "
              f"{corpus['discipline']} nodes -> {out}")


if __name__ == "__main__":
    main()
