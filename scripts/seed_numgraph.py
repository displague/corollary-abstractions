#!/usr/bin/env python3
"""Seed data/numerical_analysis, data/graph_theory and data/geometric_modeling.

Three corpora authored in one pass (8 + 8 + 8 = 24 nodes), chosen so that the
question "does computational mathematics reuse the graph's existing forms, or
does it have its own?" is decided mechanically. Six predictions were registered
before `scripts/match_signatures.py` was run; the verdicts below are what the
matcher returned, hits and misses alike.

Predictions registered before running the matcher
-------------------------------------------------

1. **The iteration/update family.** Newton's method
   (`XNEXT = X - FVALUE/FDERIV`) and Euler's method
   (`YNEXT = Y + STEPSIZE*SLOPE`) should meet
   `ml.optimization.gradient_descent_step`
   (`PARAMNEXT = PARAM - LEARNRATE*GRADIENT`); Euler at typed or family level.

   VERDICT: **split.** Euler FIRED at *family* level -- sign absorption turns
   `+(?1:V, neg(*(?2:P, ?3:V)))` into `+(?1:V, *(?2:P, ?3:V))`, so
   `numanalysis.ode.euler_method_step` family-twins both
   `ml.optimization.gradient_descent_step` and
   `ml.objective.kl_regularized_rl_objective`. Gradient descent *is* Euler's
   method on the gradient flow, and the matcher says so without being told.
   Newton MISSED at every level: dividing by the derivative introduces an
   `inv` node (`?0:V = +(?1:V, neg(*(?2:V, inv(?3:V))))`) that no other
   statement in the graph carries. The correction term of a Newton step is a
   *ratio*, the correction term of a gradient step is a *product*, and that is
   a real difference (Newton is scale-free, gradient descent is not), so the
   miss is correct rather than a tooling gap.

2. **Convex combination vs the affine family and probability mixtures.**
   `numanalysis.interpolation.linear_interpolation`
   (`RESULT = (1 - PARAM)*START + PARAM*FINISH`) should meet the affine family
   and any mixture node.

   VERDICT: **missed, twice, for two different reasons.** Against the affine
   family: a convex combination is affine *in disguise* -- expand it and you
   get `START + PARAM*(FINISH - START)`, which is exactly
   `?0:V = +(?1:V, *(?2:P, ?3:V))` -- but the unexpanded form has the
   interpolation parameter occurring *twice*, so its skeleton
   `?0:V = +(*(?1:P, ?2:V), *(?3:V, +(1, neg(?1:P))))` has a repeated slot and
   an extra `+` node that no affine-family member has. Rewriting to the
   expanded form would have made it fire; that would have been authoring to
   match, and the expanded form is not how anyone writes lerp. Against
   probability mixtures: **there is no mixture node in the graph.** The
   statistics corpus carries `total_probability_partition` (an indexed sum, not
   a two-point convex combination), so the comparison had nothing to run
   against. Recorded as a corpus gap, not a matcher failure.

3. **The weighted-sum family.** Bernstein/Bezier evaluation
   (`POINT = sum_i BASIS_i*CONTROL_i`) should join
   `probstat.probability.total_probability_partition` and
   `algtop.homology.betti_alternating_sum`.

   VERDICT: **FIRED**, and it is the best result of the three corpora.
   `?0:V = sum⟨*(?1:P, ?2:V)⟩` now spans **four** statements in **four**
   disciplines: a Bezier point, a barycentric combination, a marginal
   probability and an Euler characteristic. All four are "a variable quantity
   read off as a parameter-weighted accumulation of variable parts", and three
   of the four normalize their weights to one.

4. **Complete-graph edge count vs pair-coupling structures.**
   `EDGES = VERTICES*(VERTICES - 1)/2` against anything in the graph.

   VERDICT: **nothing fires, at any level.** Skeleton
   `?0:V = *(?1:V, +(?1:V, neg(1)), inv(2))`. Two independent reasons, and
   both are informative: the slot *recurs* (the same VERTICES appears in two
   places, which is what "choose 2 from the same set" means and is exactly the
   backlog's "slot recurrence, not slot shape" wanted-feature), and the
   statement carries two numeric literals in positions where a matchable
   statement would carry slots. The honest report is that the graph has no
   combinatorial-counting family yet; this node and
   `graphtheory.enumeration.cayley_formula` are its first two members and they
   do not even match each other.

5. **Euler's formula, not duplicated.** `geotop.polyhedra.euler_polyhedron_formula`
   already states `VERTICES - EDGES + FACES = 2`, so graph theory authors the
   *neighbours* instead -- the handshake lemma, the tree edge count, and
   adjacency-power walk counting -- and points at the existing node with
   one-sided `composed_with` edges from `planar_edge_bound` and
   `tree_edge_count`.

   VERDICT on the neighbours: **all three are singletons.** `sum⟨?0:V⟩ =
   *(2, ?1:V)` (handshake), `?0:V = +(?1:V, neg(1))` (tree edges) and
   `?0:V = MATRIXPOWER⟨?1:V, ?2:V⟩` (walks) match nothing. The walk-counting
   node is the sixth head in the graph carrying the two-argument
   opaque-composition shape `?0 = HEAD⟨?1, ?2⟩` (after CONCAT, REALIZE,
   CAPMAX, MEET, UPDATE) and, as with the other five, it twins none of them.

6. **Homogeneous transform vs the state-space update.**
   `POINTNEW = ROTATION*POINT + TRANSLATION` was predicted to typed-twin
   `ml.recurrence.linear_ssm_state_update`, "both P*V + P*V shapes".

   VERDICT: **the prediction's premise was wrong and the matcher caught it.**
   A rigid transform is `P*V + P`, not `P*V + P*V`: the translation is a bare
   parameter, not a parameter times a variable. So it MISSES the SSM update
   (`?0:V = +(*(?1:P, ?2:V), *(?3:P, ?4:V))`) and instead FIRES against the
   affine family `?0:V = +(?1:P, *(?2:P, ?3:V))`, joining tangent-line
   linearization, CAPM, the Keynesian consumption function and
   `probstat.transform.affine_location_scale`. That is the correct answer --
   a rigid motion is the canonical affine map -- and it was reached by the
   tool disagreeing with the author.

Other results worth recording
-----------------------------

- `numanalysis.integration.trapezoidal_rule` **typed-twins**
  `geometry.area_formulas.trapezoid_area_formula`, character for character:
  `?0:V = *(?1:P, ?2:V, +(?3:V, ?4:V))`. This is the sharpest "the numerical
  method IS the elementary formula" result available -- the trapezoidal rule
  computes the area of a trapezoid whose parallel sides are the two sampled
  function values and whose width is the step. Authored in the geometry node's
  shape (the one-half as a `constant` slot rather than a literal `/2`) because
  that is the same statement, and the `/2` spelling is kept as an equivalent
  form; the alternative spelling `STEPSIZE*(FIRST + SECOND)/2` produces
  `*(?1:P, +(?2:V, ?3:V), inv(2))` and matches nothing.
- `numanalysis.error.relative_condition_number` joins the rate/density family
  `?0:V = *(?1:V, inv(?2:V))` -- seven members now, across calculus,
  chemistry, economics, machine learning, physics and numerical analysis. A
  condition number is a density in the same sense a molarity is: output change
  per unit input change.
- `graphtheory.enumeration.complete_bipartite_edge_count`
  (`EDGES = PARTONE*PARTTWO`) typed-twins
  `geometry.area_formulas.rectangle_area_formula` and
  `diffgeo.surfaces.gaussian_curvature_principal_product`. Counting the edges
  of K_{m,n} and measuring a rectangle are one statement about a product of
  two independent extents.
- `graphtheory.degree.average_degree_from_edge_count` (`AVGDEGREE =
  2*EDGES/VERTICES`) is a *near* miss against the rate/density family, blocked
  by a single numeric literal: `?0:V = *(2, ?1:V, inv(?2:V))` versus
  `?0:V = *(?1:V, inv(?2:V))`. Same shape of blocker docs/BACKLOG.md records
  for `diffgeo.curves.circle_curvature`, from the other direction -- there a
  literal `1` in the numerator, here a literal `2`.
- `numanalysis.rootfinding.fixed_point_iteration` deliberately adopts the
  `SELFMAP` head from `difftop.degree.brouwer_fixed_point`, since g really is
  a self-map of the bracketing interval. It still does not twin, because
  Brouwer is `?0:V = SELFMAP⟨?0:V⟩` (one slot, twice) and the iteration is
  `?0:V = SELFMAP⟨?1:V⟩` (two slots). The difference is precisely the
  fixed-point *property* versus the fixed-point *iteration*, so this is a
  correct non-match -- and a clean, deliberately constructed instance of the
  backlog's "slot recurrence, not slot shape" item.

What the other two tools recovered
----------------------------------

`match_signatures.py` answers "is this the same statement"; two of this pass's
misses are answered by the other tools, and the pattern is worth naming.

- `scripts/decompose.py` sees three relations the twin matcher structurally
  cannot, all for one reason: it compares expression SIDES, so it is blind to
  the relation symbol and to slot recurrence across the relation.
  (a) Newton's method, a singleton at every twin level, has correction term
  `*(?0:V, inv(?1:V))` -- the rate/density family's expression side, shared
  with 11 statements. A Newton correction is a rate, and prediction 1's
  Newton half is recovered as a *constituent* rather than as a twin.
  (b) `numanalysis.floatingpoint.machine_epsilon_bound`, isolated only by its
  `<=`, has right side `*(?0:P, ?1:V)` -- Ohm's law, Newton's second law,
  circle circumference, 35 statements in all.
  (c) `numanalysis.rootfinding.fixed_point_iteration`, which does not twin
  `difftop.degree.brouwer_fixed_point` because of slot recurrence, IS reported
  by decompose as sharing Brouwer's expression side, because on one side of
  the relation the recurrence is invisible. Two tools, one pair of nodes, two
  opposite and individually correct answers.
  Also worth recording: `graphtheory.enumeration.complete_graph_edge_count`
  contains `graphtheory.trees.tree_edge_count`'s whole expression side
  (`+(?0:V, neg(1))`) as a constituent, which is the mathematical fact that
  every vertex of K_n has degree n-1 and every spanning tree has n-1 edges;
  and `graphtheory.degree.handshake_lemma`'s bare `sum⟨?0:V⟩` is shared with
  `difftop.degree.degree_regular_value_count` and
  `difftop.vectorfields.poincare_hopf_index_theorem` -- three statements
  summing an unweighted index, in two senses of the word "degree".
- `scripts/specialize.py` produced 8 edges touching the 24 new nodes, of which
  **three are informative** and they are all the same recovery:
  `calculus.differentiation.average_rate_of_change >=
  graphtheory.degree.average_degree_from_edge_count` via absorption, binding
  `QUANTITY -> *(2, EDGES)`, plus the same edge from
  `chemistry.solutions.molarity_definition` and (more loosely)
  `chemistry.kinetics.half_life_first_order`. So the literal-2 blocker that
  keeps average degree out of the rate family as a TWIN is absorbed cleanly
  one level down: average degree is edge-count-per-vertex in exactly the sense
  molarity is amount-per-volume. The other five are the degenerate kind
  docs/BACKLOG.md has recorded four times already -- `beer_lambert_law >=
  complete_bipartite_edge_count` (ABSORPTIVITY -> 1),
  `lora_low_rank_update >= euler_method_step` (SCALING -> 1), and
  `trapezoidal_rule >= rectangle_perimeter_formula` (STEPWIDTH -> 2), which is
  the specific noise edge the backlog already names.

Authoring constraints observed (all from docs/BACKLOG.md)
---------------------------------------------------------

- `statement_id` may not contain `_` in its first segment, so the prefixes are
  `numanalysis.` / `graphtheory.` / `geomodel.` while the directories and the
  `discipline` fields are `numerical_analysis` / `graph_theory` /
  `geometric_modeling`.
- `constantToken` has no `name` key; `symbol_lexicon.symbols` needs at least
  one scalar entry and cannot hold functionals, so SELFMAP, MATRIXPOWER and
  CROSS live in `functionals`.
- No binders, no min/max, no factorials and no binomial coefficients: the
  Bernstein basis is a `parameter` slot rather than a written-out
  `C(n,i) t^i (1-t)^(n-i)`, and the node says so.
- Call arguments are ORDERED, so `MATRIXPOWER(matrix, exponent)` and
  `CROSS(first, second)` fix an argument order anything added later must keep.
  CROSS is *anti*commutative, which the matcher cannot represent at all.
- `*` is flattened and sorted, i.e. asserted commutative. The rigid-transform
  node uses it for matrix-vector application, which does not commute; the node
  declares the per-coordinate scalar reading under which the template is
  literally true, the same escape `ml.recurrence.linear_ssm_state_update`
  takes with a diagonal state matrix.
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
    context = {"disciplines": disciplines or ["mathematics"],
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
LEQ = op("<=", "less than or equal", 2, "relational")
ADD = op("+", "addition", 2, "arithmetic")
SUB = op("-", "subtraction", 2, "arithmetic")
MUL = op("*", "multiplication", 2, "arithmetic")
DIV = op("/", "division", 2, "arithmetic")
POW = op("^", "exponentiation", 2, "arithmetic")
SUM = op("sum", "finite summation over an index set", 1, "arithmetic")

SELFMAP_FN = {
    "notation": "SELFMAP(.)", "name": "iteration map",
    "input_arity": 1, "codomain": "the same interval as its domain",
    "description": "The map g whose fixed points are the sought roots, and "
                   "which sends the bracketing interval into itself. The head "
                   "is deliberately the one difftop.degree.brouwer_fixed_point "
                   "uses, because it is the same kind of object -- a self-map "
                   "of a set -- and adopting the vocabulary is the graph's "
                   "only cross-corpus channel. It does not produce a twin: "
                   "Brouwer says SELFMAP(x) = x (one slot twice), this node "
                   "says x_next = SELFMAP(x) (two slots)."}

MATRIXPOWER_FN = {
    "notation": "MATRIXPOWER(matrix, exponent)", "name": "matrix power",
    "input_arity": 2, "codomain": "square matrices over the same ring",
    "description": "The exponent-fold matrix product A^k. Written as an opaque "
                   "two-argument call rather than with `^` because `^` in this "
                   "grammar is scalar exponentiation and the canonicalizer "
                   "would treat the base as a commutative factor; matrix "
                   "multiplication is not commutative and A^k is not a "
                   "pointwise power. The consequence is that the entire "
                   "mechanism -- that the (i,j) entry accumulates one term per "
                   "walk -- is invisible to the matcher. Argument order is "
                   "fixed: matrix first, exponent second."}

CROSS_FN = {
    "notation": "CROSS(first, second)", "name": "vector cross product",
    "input_arity": 2, "codomain": "vectors in three-space",
    "description": "The three-dimensional cross product. An opaque call: the "
                   "grammar has no antisymmetric binary operator, and using "
                   "`*` would assert commutativity, which is the exact "
                   "opposite of the truth (CROSS(a,b) = -CROSS(b,a)). Argument "
                   "order is fixed and load-bearing -- swapping it flips the "
                   "surface's orientation -- and the matcher cannot see that."}

IDX_CONTROL = {"notation": "i in 0..n", "domain": "the control-point indices of a degree-n curve",
               "description": "Index running over the n+1 control points; the "
                              "sum is over the whole control polygon."}
IDX_SIMPLEX = {"notation": "i in 0..d", "domain": "the vertices of a d-simplex",
               "description": "Index running over the vertices of the simplex "
                              "whose barycentric coordinates are being stated."}
IDX_VERTICES = {"notation": "v in V", "domain": "the vertex set of a finite graph",
                "description": "Index running over every vertex of the graph, "
                               "each counted once."}

HALF_CONST = {
    "symbol": "1/2",
    "value": 0.5,
    "description": "The one-half of the trapezoid. Carried as a constant slot "
                   "rather than as a literal `/2` so that the template is the "
                   "same string as geometry.area_formulas.trapezoid_area_formula's "
                   "-- which is not a trick, because the two statements are the "
                   "same statement. The `/2` spelling is kept as an equivalent "
                   "form and is what produces the non-matching skeleton "
                   "`*(?1:P, +(?2:V, ?3:V), inv(2))`."}

UNITROUNDOFF_CONST = {
    "symbol": "u",
    "value": "2^-53 for IEEE 754 binary64 with round-to-nearest",
    "description": "Unit roundoff, half the machine epsilon in the "
                   "round-to-nearest convention. A fixed property of the "
                   "arithmetic, not of the problem: the single number that "
                   "converts every exact quantity into a bound on its "
                   "representable neighbour."}


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

NEWTON1669 = {"citation_key": "newton1669",
              "bibliographic_entry": "Newton, I. (1669, published 1711). De analysi per aequationes numero terminorum infinitas. London: William Jones."}
RAPHSON1690 = {"citation_key": "raphson1690",
               "bibliographic_entry": "Raphson, J. (1690). Analysis aequationum universalis, seu ad aequationes algebraicas resolvendas methodus generalis et expedita. London: Thomas Braddyll."}
SIMPSON1740 = {"citation_key": "simpson1740",
               "bibliographic_entry": "Simpson, T. (1740). Essays on Several Curious and Useful Subjects in Speculative and Mix'd Mathematicks. London: H. Woodfall."}
YPMA1995 = {"citation_key": "ypma1995",
            "bibliographic_entry": "Ypma, T. J. (1995). Historical Development of the Newton-Raphson Method. SIAM Review, 37(4), 531-551.",
            "url": "https://doi.org/10.1137/1037125"}
EULER1768 = {"citation_key": "euler1768",
             "bibliographic_entry": "Euler, L. (1768). Institutionum calculi integralis, volumen primum, sectio secunda, caput VII. St Petersburg: Academia Imperialis Scientiarum."}
BUTCHER2016 = {"citation_key": "butcher2016",
               "bibliographic_entry": "Butcher, J. C. (2016). Numerical Methods for Ordinary Differential Equations (3rd ed.). Chichester: Wiley."}
HAIRER1993 = {"citation_key": "hairer1993",
              "bibliographic_entry": "Hairer, E., Norsett, S. P., Wanner, G. (1993). Solving Ordinary Differential Equations I: Nonstiff Problems (2nd ed.). Berlin: Springer."}
BANACH1922 = {"citation_key": "banach1922",
              "bibliographic_entry": "Banach, S. (1922). Sur les operations dans les ensembles abstraits et leur application aux equations integrales. Fundamenta Mathematicae, 3, 133-181.",
              "url": "https://doi.org/10.4064/fm-3-1-133-181"}
BOLZANO1817 = {"citation_key": "bolzano1817",
               "bibliographic_entry": "Bolzano, B. (1817). Rein analytischer Beweis des Lehrsatzes, dass zwischen je zwey Werthen, die ein entgegengesetztes Resultat gewaehren, wenigstens eine reelle Wurzel der Gleichung liege. Prague: Gottlieb Haase."}
BURDEN2015 = {"citation_key": "burden2015",
              "bibliographic_entry": "Burden, R. L., Faires, J. D., Burden, A. M. (2015). Numerical Analysis (10th ed.). Boston: Cengage Learning."}
COTES1722 = {"citation_key": "cotes1722",
             "bibliographic_entry": "Cotes, R. (1722). Harmonia mensurarum, sive analysis et synthesis per rationum et angulorum mensuras promotae. Cambridge: Robert Smith (posthumous)."}
DAVIS1984 = {"citation_key": "davis1984",
             "bibliographic_entry": "Davis, P. J., Rabinowitz, P. (1984). Methods of Numerical Integration (2nd ed.). Orlando: Academic Press."}
TURING1948 = {"citation_key": "turing1948",
              "bibliographic_entry": "Turing, A. M. (1948). Rounding-off Errors in Matrix Processes. Quarterly Journal of Mechanics and Applied Mathematics, 1(1), 287-308.",
              "url": "https://doi.org/10.1093/qjmam/1.1.287"}
RICE1966 = {"citation_key": "rice1966",
            "bibliographic_entry": "Rice, J. R. (1966). A Theory of Condition. SIAM Journal on Numerical Analysis, 3(2), 287-310.",
            "url": "https://doi.org/10.1137/0703023"}
TREFETHEN1997 = {"citation_key": "trefethen1997",
                 "bibliographic_entry": "Trefethen, L. N., Bau, D. (1997). Numerical Linear Algebra. Philadelphia: SIAM."}
WILKINSON1963 = {"citation_key": "wilkinson1963",
                 "bibliographic_entry": "Wilkinson, J. H. (1963). Rounding Errors in Algebraic Processes. Englewood Cliffs: Prentice-Hall."}
HIGHAM2002 = {"citation_key": "higham2002",
              "bibliographic_entry": "Higham, N. J. (2002). Accuracy and Stability of Numerical Algorithms (2nd ed.). Philadelphia: SIAM."}
IEEE754 = {"citation_key": "ieee754_2019",
           "bibliographic_entry": "IEEE (2019). IEEE Standard for Floating-Point Arithmetic. IEEE Std 754-2019.",
           "url": "https://doi.org/10.1109/IEEESTD.2019.8766229"}
MEIJERING2002 = {"citation_key": "meijering2002",
                 "bibliographic_entry": "Meijering, E. (2002). A Chronology of Interpolation: From Ancient Astronomy to Modern Signal and Image Processing. Proceedings of the IEEE, 90(3), 319-342.",
                 "url": "https://doi.org/10.1109/5.993400"}

EULER1736 = {"citation_key": "euler1736",
             "bibliographic_entry": "Euler, L. (1736). Solutio problematis ad geometriam situs pertinentis. Commentarii Academiae Scientiarum Imperialis Petropolitanae, 8, 128-140."}
EULER1758 = {"citation_key": "euler1758",
             "bibliographic_entry": "Euler, L. (1758). Elementa doctrinae solidorum. Novi Commentarii Academiae Scientiarum Imperialis Petropolitanae, 4, 109-140."}
CAYLEY1889 = {"citation_key": "cayley1889",
              "bibliographic_entry": "Cayley, A. (1889). A theorem on trees. Quarterly Journal of Pure and Applied Mathematics, 23, 376-378."}
BORCHARDT1860 = {"citation_key": "borchardt1860",
                 "bibliographic_entry": "Borchardt, C. W. (1860). Ueber eine der Interpolation entsprechende Darstellung der Eliminations-Resultante. Journal fuer die reine und angewandte Mathematik, 57, 111-121."}
SYLVESTER1857 = {"citation_key": "sylvester1857",
                 "bibliographic_entry": "Sylvester, J. J. (1857). On the change of systems of independent variables. Quarterly Journal of Pure and Applied Mathematics, 1, 42-56."}
KIRCHHOFF1847 = {"citation_key": "kirchhoff1847",
                 "bibliographic_entry": "Kirchhoff, G. (1847). Ueber die Aufloesung der Gleichungen, auf welche man bei der Untersuchung der linearen Vertheilung galvanischer Stroeme gefuehrt wird. Annalen der Physik und Chemie, 72(12), 497-508."}
BIGGS1993 = {"citation_key": "biggs1993",
             "bibliographic_entry": "Biggs, N. (1993). Algebraic Graph Theory (2nd ed.). Cambridge: Cambridge University Press."}
CVETKOVIC1980 = {"citation_key": "cvetkovic1980",
                 "bibliographic_entry": "Cvetkovic, D. M., Doob, M., Sachs, H. (1980). Spectra of Graphs: Theory and Application. New York: Academic Press."}
KONIG1936 = {"citation_key": "konig1936",
             "bibliographic_entry": "Koenig, D. (1936). Theorie der endlichen und unendlichen Graphen. Leipzig: Akademische Verlagsgesellschaft."}
DIESTEL2017 = {"citation_key": "diestel2017",
               "bibliographic_entry": "Diestel, R. (2017). Graph Theory (5th ed.). Berlin: Springer. Graduate Texts in Mathematics 173."}
BONDY2008 = {"citation_key": "bondy2008",
             "bibliographic_entry": "Bondy, J. A., Murty, U. S. R. (2008). Graph Theory. London: Springer. Graduate Texts in Mathematics 244."}
WEST2001 = {"citation_key": "west2001",
            "bibliographic_entry": "West, D. B. (2001). Introduction to Graph Theory (2nd ed.). Upper Saddle River: Prentice Hall."}
KURATOWSKI1930 = {"citation_key": "kuratowski1930",
                  "bibliographic_entry": "Kuratowski, K. (1930). Sur le probleme des courbes gauches en topologie. Fundamenta Mathematicae, 15, 271-283.",
                  "url": "https://doi.org/10.4064/fm-15-1-271-283"}

BERNSTEIN1912 = {"citation_key": "bernstein1912",
                 "bibliographic_entry": "Bernstein, S. N. (1912). Demonstration du theoreme de Weierstrass fondee sur le calcul des probabilites. Communications de la Societe Mathematique de Kharkow, 13(1), 1-2."}
DECASTELJAU1963 = {"citation_key": "decasteljau1963",
                   "bibliographic_entry": "de Casteljau, P. de F. (1963). Courbes et surfaces a poles. Internal technical report, Andre Citroen Automobiles SA, Paris (work carried out from 1959)."}
BEZIER1972 = {"citation_key": "bezier1972",
              "bibliographic_entry": "Bezier, P. (1972). Numerical Control: Mathematics and Applications. London: Wiley."}
FARIN2002 = {"citation_key": "farin2002",
             "bibliographic_entry": "Farin, G. (2002). Curves and Surfaces for CAGD: A Practical Guide (5th ed.). San Francisco: Morgan Kaufmann."}
PRAUTZSCH2002 = {"citation_key": "prautzsch2002",
                 "bibliographic_entry": "Prautzsch, H., Boehm, W., Paluszny, M. (2002). Bezier and B-Spline Techniques. Berlin: Springer."}
MOBIUS1827 = {"citation_key": "mobius1827",
              "bibliographic_entry": "Moebius, A. F. (1827). Der barycentrische Calcul: ein neues Huelfsmittel zur analytischen Behandlung der Geometrie. Leipzig: Johann Ambrosius Barth."}
HAMILTON1844 = {"citation_key": "hamilton1844",
                "bibliographic_entry": "Hamilton, W. R. (1844). On quaternions; or on a new system of imaginaries in algebra. Philosophical Magazine, 25(163), 10-13.",
                "url": "https://doi.org/10.1080/14786444408644923"}
SHOEMAKE1985 = {"citation_key": "shoemake1985",
                "bibliographic_entry": "Shoemake, K. (1985). Animating rotation with quaternion curves. ACM SIGGRAPH Computer Graphics, 19(3), 245-254.",
                "url": "https://doi.org/10.1145/325165.325242"}
DENAVIT1955 = {"citation_key": "denavit1955",
               "bibliographic_entry": "Denavit, J., Hartenberg, R. S. (1955). A Kinematic Notation for Lower-Pair Mechanisms Based on Matrices. Journal of Applied Mechanics, 22(2), 215-221.",
               "url": "https://doi.org/10.1115/1.4011045"}
ROBERTS1965 = {"citation_key": "roberts1965",
               "bibliographic_entry": "Roberts, L. G. (1965). Homogeneous matrix representation and manipulation of N-dimensional constructs. MS-1505, Lincoln Laboratory, Massachusetts Institute of Technology."}
FOLEY1990 = {"citation_key": "foley1990",
             "bibliographic_entry": "Foley, J. D., van Dam, A., Feiner, S. K., Hughes, J. F. (1990). Computer Graphics: Principles and Practice (2nd ed.). Reading: Addison-Wesley."}
DOCARMO1976 = {"citation_key": "docarmo1976",
               "bibliographic_entry": "do Carmo, M. P. (1976). Differential Geometry of Curves and Surfaces. Englewood Cliffs: Prentice-Hall."}
PHONG1975 = {"citation_key": "phong1975",
             "bibliographic_entry": "Phong, B. T. (1975). Illumination for computer generated pictures. Communications of the ACM, 18(6), 311-317.",
             "url": "https://doi.org/10.1145/360825.360839"}


# --------------------------------------------------------------------------
# Corpus 1: numerical analysis
# --------------------------------------------------------------------------

NUMANALYSIS = [

    # ---------------------------------------------------------------- 1 ----
    node("numanalysis.rootfinding.newton_iteration",
         "Newton-Raphson Iteration Step",
         "definition", "formal", "root_finding", "iteration",
         "x_(n+1) = x_n - f(x_n)/f'(x_n)",
         "x_{n+1} = x_n - \\frac{f(x_n)}{f'(x_n)}",
         [{"form_id": "correction", "notation_system": "ascii",
           "expression": "x_(n+1) = x_n + delta_n,  f'(x_n)*delta_n = -f(x_n)",
           "scope_note": "Split into the linear solve and the update; this is the form that generalizes to systems, where the division becomes a Jacobian solve"},
          {"form_id": "multivariate", "notation_system": "matrix_notation",
           "expression": "x_(n+1) = x_n - J(x_n)^(-1) * F(x_n)",
           "scope_note": "Vector form; the reciprocal derivative becomes an inverse Jacobian, which is why the scalar `/` in the template is the honest scalar case only"},
          {"form_id": "as_fixed_point", "notation_system": "ascii",
           "expression": "x_(n+1) = g(x_n),  g(x) = x - f(x)/f'(x)",
           "scope_note": "Newton exhibited as fixed-point iteration; g'(root) = 0 is exactly why convergence is quadratic rather than linear"},
          {"form_id": "secant", "notation_system": "ascii",
           "expression": "x_(n+1) = x_n - f(x_n)*(x_n - x_(n-1))/(f(x_n) - f(x_(n-1)))",
           "scope_note": "The secant method: the same step with the derivative replaced by a difference quotient"}],
         "state_minus_ratio_correction",
         "XNEXT = X - FVALUE/FDERIV",
         [slot("XNEXT", "variable", "updated_iterate"),
          slot("X", "variable", "current_iterate"),
          slot("FVALUE", "variable", "residual_at_iterate"),
          slot("FDERIV", "variable", "derivative_at_iterate")],
         ["The correction is a RATIO, not a product. That single structural "
          "fact is the difference between this node and every other update "
          "step in the graph: gradient descent, Euler's method and the "
          "state-space recurrence all correct by a parameter times a variable, "
          "and Newton corrects by a variable divided by a variable.",
          "Because the correction is a ratio of two quantities that both scale "
          "with f, the step is invariant under rescaling the function: replace "
          "f by c*f and the iteration is unchanged. No other node in the "
          "update family has that property, and it is what removes the "
          "step-size parameter every other method needs.",
          "All four slots are variable-like. There is no tuning parameter at "
          "all, which is the method's entire selling point and also the source "
          "of its fragility: nothing can be turned down when it diverges.",
          "The template is one step. Quadratic convergence is a property of "
          "the iterated map's derivative at the root, invisible here, and "
          "recorded in the significance and failure-mode fields instead."],
         [sym("x_n", "variable", "current_iterate",
              "The n-th approximation to a root.", 0),
          sym("f", "variable", "residual_at_iterate",
              "Value of the function whose root is sought, at the current iterate.", 0),
          sym("fprime", "variable", "derivative_at_iterate",
              "Derivative of that function at the current iterate.", 0),
          sym("n", "index", "iteration_index", "Iteration counter.", 0)],
         [EQ, SUB, DIV],
         "Replace the current guess by the root of the tangent line drawn at "
         "the current guess: linearize, solve exactly, repeat.",
         "Prediction 1 said Newton and Euler would meet gradient descent as one "
         "iteration/update family. Newton MISSED at shape, typed and family "
         "level, and the miss is correct rather than a tooling gap. Its "
         "skeleton is `?0:V = +(?1:V, neg(*(?2:V, inv(?3:V))))`; gradient "
         "descent's is `?0:V = +(?1:V, neg(*(?2:P, ?3:V)))`. The `inv` node is "
         "not decoration -- it is the second-order information. A gradient step "
         "multiplies the residual by a number someone chose; a Newton step "
         "divides it by a number the problem supplied. Everything that "
         "distinguishes the two methods (scale invariance, quadratic versus "
         "linear convergence, no learning rate to tune) follows from that one "
         "`inv`, so a matcher that grouped them would be hiding the finding "
         "rather than making it. Recorded as the corpus's clearest example of "
         "a registered prediction that deserved to fail.",
         ["f differentiable in a neighbourhood of the root",
          "f'(x_n) nonzero at every iterate",
          "An initial guess in the basin of attraction of the sought root",
          "A simple root, if quadratic convergence is wanted"],
         [NEWTON1669, RAPHSON1690, SIMPSON1740, YPMA1995, BURDEN2015],
         disciplines=["numerical_analysis", "mathematics"],
         failure_modes=[
             "A zero or near-zero derivative makes the step unbounded; the "
             "equation is silent about it because division by zero is a fact "
             "about the arithmetic, not about the statement.",
             "At a multiple root convergence degrades from quadratic to "
             "linear, and the residual stops being a usable stopping test.",
             "Basins of attraction for polynomials of degree three or more are "
             "fractal, so 'a good enough initial guess' is not a neighbourhood "
             "condition that can be checked cheaply.",
             "The scalar `/` in the template hides that the multivariate step "
             "is a linear SOLVE, not an inverse-and-multiply; forming J^(-1) "
             "explicitly is the classic way to make a correct method "
             "numerically useless."],
         inferential_links=links(
             special_case_of=["numanalysis.rootfinding.fixed_point_iteration"],
             composed_with=["numanalysis.rootfinding.bisection_interval_halving",
                            "numanalysis.error.relative_condition_number"]),
         keywords=["Newton's method", "Newton-Raphson", "root finding",
                   "quadratic convergence", "tangent line", "secant method"],
         canonical_objects=["iterate", "residual", "derivative"]),

    # ---------------------------------------------------------------- 2 ----
    node("numanalysis.rootfinding.fixed_point_iteration",
         "Fixed-Point Iteration",
         "definition", "formal", "root_finding", "iteration",
         "x_(n+1) = g(x_n)",
         "x_{n+1} = g(x_n)",
         [{"form_id": "fixed_point_condition", "notation_system": "ascii",
           "expression": "g(xstar) = xstar",
           "scope_note": "The limit's defining property: what the iteration converges TO, which is difftop.degree.brouwer_fixed_point's statement rather than this one"},
          {"form_id": "contraction_bound", "notation_system": "ascii",
           "expression": "|x_(n+1) - xstar| <= L * |x_n - xstar|",
           "scope_note": "Banach's estimate with Lipschitz constant L < 1; linear convergence at rate L"},
          {"form_id": "root_form", "notation_system": "ascii",
           "expression": "g(x) = x - f(x)/f'(x)",
           "scope_note": "The choice of g that makes this Newton's method; other choices give the chord method, Steffensen's method, and so on"}],
         "opaque_unary_state_map",
         "XNEXT = SELFMAP(X)",
         [slot("XNEXT", "variable", "next_iterate"),
          slot("X", "variable", "current_iterate"),
          slot("SELFMAP", "functional", "iteration_map")],
         ["The head is deliberately `SELFMAP`, the head "
          "difftop.degree.brouwer_fixed_point uses, because g really is a "
          "self-map of the bracketing interval and adopting an existing "
          "vocabulary is the graph's only cross-corpus channel "
          "(docs/BACKLOG.md). The adoption is honest and it still does not "
          "produce a twin -- see the significance field.",
          "Every root-finding method in this corpus is an instance: choosing g "
          "is choosing a method. Newton, the secant method, the chord method "
          "and Jacobi/Gauss-Seidel splitting all differ only in which g is "
          "substituted here.",
          "Both slots are variable-like and the map is opaque, so the template "
          "carries no rate information at all. The contraction constant that "
          "decides whether the iteration converges lives in "
          "regularity_conditions, which is where a quarter of the graph's "
          "theorems already keep their real content.",
          "The statement is one step of a recurrence. That the sequence has a "
          "limit, and that the limit is a fixed point, are separate claims "
          "requiring completeness and continuity respectively."],
         [sym("x_n", "variable", "current_iterate",
              "The n-th iterate of the sequence.", 0),
          sym("xstar", "variable", "next_iterate",
              "The successor iterate; in the limit, the fixed point itself.", 0),
          sym("n", "index", "iteration_index", "Iteration counter.", 0)],
         [EQ],
         "Iterating a map that sends an interval into itself: the next "
         "approximation is whatever the map returns on the current one.",
         "A deliberately constructed instance of docs/BACKLOG.md's wanted match "
         "level, 'slot recurrence, not slot shape'. This node adopts Brouwer's "
         "`SELFMAP` head on purpose, so the two skeletons differ in exactly one "
         "respect: `difftop.degree.brouwer_fixed_point` is "
         "`?0:V = SELFMAP⟨?0:V⟩` -- one slot, occurring twice -- and this node "
         "is `?0:V = SELFMAP⟨?1:V⟩` -- two slots. They do not twin at shape, "
         "typed or family level. And they should not: the difference between "
         "one slot and two IS the difference between the fixed-point property "
         "and the fixed-point iteration, between 'x is unmoved by g' and 'apply "
         "g to get the next x'. What the backlog wants is not for these to be "
         "merged but for the graph to be able to ASK 'which templates have a "
         "slot occurring on both sides of the relation', a query that would "
         "collect Brouwer, double negation, idempotence and the FTC, and would "
         "correctly exclude this node. Recorded because it is the cheapest "
         "available control case: same head, same arity, different slot "
         "recurrence, authored on purpose.",
         ["g maps a closed interval into itself",
          "g Lipschitz with constant strictly less than one, for Banach's "
          "guarantee of a unique fixed point and linear convergence",
          "A starting point inside that interval",
          "Completeness of the underlying space"],
         [BANACH1922, BURDEN2015, HIGHAM2002],
         disciplines=["numerical_analysis", "mathematics"],
         functionals=[SELFMAP_FN],
         failure_modes=[
             "A Lipschitz constant at or above one makes the iteration diverge "
             "or cycle; the template cannot express the constant, so nothing "
             "in the structure warns of it.",
             "A fixed point can exist without the iteration finding it: "
             "Brouwer guarantees existence on a convex compact set with no "
             "contraction assumption, and the iteration then has no reason to "
             "converge.",
             "Reading `SELFMAP` as 'the function whose root we want' is wrong "
             "by one algebraic step -- the roots of f are the fixed points of "
             "g, and constructing g from f is where the method is chosen."],
         inferential_links=links(
             generalizes=["numanalysis.rootfinding.newton_iteration"],
             composed_with=["difftop.degree.brouwer_fixed_point",
                            "numanalysis.rootfinding.bisection_interval_halving"]),
         keywords=["fixed-point iteration", "contraction mapping", "Banach",
                   "self-map", "linear convergence", "slot recurrence"],
         canonical_objects=["iteration map", "fixed point", "bracketing interval"]),

    # ---------------------------------------------------------------- 3 ----
    node("numanalysis.rootfinding.bisection_interval_halving",
         "Bisection Interval Halving",
         "proposition", "formal", "root_finding", "bracketing",
         "w_(n+1) = w_n / 2",
         "w_{n+1} = \\frac{w_n}{2}",
         [{"form_id": "closed_form", "notation_system": "ascii",
           "expression": "w_n = w_0 / 2^n",
           "scope_note": "The solved recurrence; this form exposes the geometric decay, and it is a different statement from the one-step template"},
          {"form_id": "error_bound", "notation_system": "ascii",
           "expression": "|x_n - xstar| <= w_0 / 2^(n+1)",
           "scope_note": "The guarantee: the midpoint is within half the current bracket of the root, unconditionally"},
          {"form_id": "iterations_needed", "notation_system": "ascii",
           "expression": "n >= LOG(w_0/tol)/LOG(2)",
           "scope_note": "Inverting the bound: the iteration count is known in advance, which no other method in this corpus can say"}],
         "halving_recurrence",
         "WIDTHNEXT = WIDTH/2",
         [slot("WIDTHNEXT", "variable", "next_bracket_width"),
          slot("WIDTH", "variable", "current_bracket_width")],
         ["The smallest non-trivial update in the three corpora: one variable, "
          "one literal. It carries no parameter at all, which is why the "
          "convergence rate is fixed in advance and identical on every problem.",
          "Written as the one-step recurrence rather than as the closed form "
          "w_0/2^n on purpose. The closed form belongs to the "
          "exponential-decay family (cousin to first-order kinetics and "
          "continuous discounting); the one-step form does not. Both are honest "
          "statements of different things, and the corpus keeps the recurrence "
          "in the template with the closed form as an equivalent variant, "
          "because bisection is specified as a loop, not as a formula.",
          "The literal 2 is the bisection: replacing it with a slot would be "
          "the false-position or golden-section method, and those have "
          "different guarantees. So the literal is structure, not an "
          "unparameterized constant.",
          "The width recurrence is unconditional. Unlike every other node in "
          "this corpus, no smoothness, no derivative and no basin of attraction "
          "is required -- only a sign change at the endpoints."],
         [sym("w_n", "variable", "current_bracket_width",
              "Width of the bracketing interval after n halvings.", 0),
          sym("n", "index", "iteration_index", "Iteration counter.", 0)],
         [EQ, DIV],
         "Each step of bisection halves the interval known to contain a root, "
         "so the uncertainty about the root's location is cut in half per "
         "function evaluation.",
         "Authored honestly rather than baited into the exponential family, and "
         "the outcome is a singleton: `?0:V = *(?1:V, inv(2))` matches nothing "
         "at shape, typed or family level. Two near misses are worth naming. "
         "Against the rate/density family `?0:V = *(?1:V, inv(?2:V))` -- seven "
         "members including this corpus's own condition number -- the only "
         "difference is that the denominator is the literal 2 rather than a "
         "slot, which is character for character the blocker docs/BACKLOG.md "
         "records for `diffgeo.curves.circle_curvature` (a literal 1 in the "
         "numerator) and which these corpora hit a second time in "
         "`graphtheory.degree.average_degree_from_edge_count`. Against "
         "`chemistry.kinetics.half_life_first_order` the relationship is "
         "semantic and exact -- a half-life IS the time for a halving -- but "
         "the two statements are written from opposite sides (one asks how much "
         "remains after a step, the other how long a halving takes), so no "
         "match is available. Three independent corpora now want the same "
         "'numeric literal may bind a parameter-like slot' match level.",
         ["A continuous function with a sign change across the initial bracket",
          "Exact arithmetic on the midpoint, or a midpoint formula that cannot "
          "fall outside the bracket in floating point",
          "The bracket, not the iterate, is what the recurrence describes"],
         [BOLZANO1817, BURDEN2015, HIGHAM2002],
         disciplines=["numerical_analysis", "mathematics"],
         failure_modes=[
             "Guaranteed but slow: one bit of accuracy per function evaluation, "
             "so the method that never fails is also the one no one uses alone.",
             "A sign change is not a root -- a pole with a sign change "
             "satisfies the hypothesis and the method converges confidently to "
             "the singularity.",
             "Even-multiplicity roots produce no sign change and are invisible "
             "to the bracket, so the method cannot find them at all.",
             "Computing the midpoint as (a+b)/2 can overflow or fall outside "
             "[a,b] in floating point; a + (b-a)/2 is the form that preserves "
             "the invariant this node states."],
         inferential_links=links(
             composed_with=["numanalysis.rootfinding.newton_iteration",
                            "numanalysis.rootfinding.fixed_point_iteration"]),
         keywords=["bisection", "bracketing", "interval halving",
                   "intermediate value theorem", "guaranteed convergence"],
         canonical_objects=["bracketing interval", "midpoint", "sign change"]),

    # ---------------------------------------------------------------- 4 ----
    node("numanalysis.integration.trapezoidal_rule",
         "Trapezoidal Rule (Single Panel)",
         "approximation", "derived", "quadrature", "newton_cotes",
         "I = (1/2) * (f(a) + f(b)) * h,  h = b - a",
         "I \\approx \\tfrac{1}{2}\\left(f(a) + f(b)\\right) h, \\qquad h = b - a",
         [{"form_id": "step_over_two", "notation_system": "ascii",
           "expression": "I = h*(f(a) + f(b))/2",
           "scope_note": "The spelling every textbook uses. Structurally different: it produces `*(?1:P, +(?2:V, ?3:V), inv(2))`, with the half as a literal, and matches nothing"},
          {"form_id": "mean_times_width", "notation_system": "ascii",
           "expression": "I = MEAN(f(a), f(b)) * h",
           "scope_note": "Read as average height times width -- the mean-value reading, and the reason the rule is exact for affine integrands"},
          {"form_id": "composite", "notation_system": "ascii",
           "expression": "I = h*(f(x_0)/2 + f(x_1) + ... + f(x_(n-1)) + f(x_n)/2)",
           "scope_note": "The composite rule over n equal subintervals; interior samples are shared between neighbouring trapezoids and so carry weight one"},
          {"form_id": "error_term", "notation_system": "ascii",
           "expression": "E = -(h^3/12) * fsecond(xi),  xi in (a,b)",
           "scope_note": "Euler-Maclaurin remainder for one panel; the h^3 is what makes the composite rule second-order accurate"}],
         "scaled_sum_product",
         "AREA = CONSTANT * (VALUELEFT + VALUERIGHT) * STEPWIDTH",
         [slot("AREA", "variable", "approximated_integral"),
          slot("CONSTANT", "constant", "one_half"),
          slot("VALUELEFT", "variable", "left_sample"),
          slot("VALUERIGHT", "variable", "right_sample"),
          slot("STEPWIDTH", "variable", "panel_width")],
         ["Authored in geometry.area_formulas.trapezoid_area_formula's own "
          "shape, with the one-half as a `constant` slot rather than a literal "
          "`/2`. That is not a disguise: the trapezoidal rule computes exactly "
          "the area of a trapezoid whose parallel sides are the two sampled "
          "function values and whose width is the step. Same statement, "
          "therefore same template. The textbook `/2` spelling is kept as an "
          "equivalent form and produces a skeleton that matches nothing.",
          "The two samples are variable-like and enter symmetrically; the "
          "commutative `+` of the grammar tells no lie here, since swapping the "
          "endpoints of the panel does not change the estimate.",
          "The step width is variable-like rather than parameter-like because "
          "in the single-panel statement it IS the trapezoid's height -- a "
          "geometric extent of the problem. In the composite rule it becomes a "
          "tuning parameter, which is a different statement and would be a "
          "different slot category.",
          "The rule is exact for affine integrands and in general for nothing "
          "else, which is the same fact as: a trapezoid is the region under a "
          "straight line."],
         [sym("I", "variable", "approximated_integral",
              "Estimate of the integral over one panel.", 0),
          sym("f_a", "variable", "left_sample",
              "Integrand evaluated at the left endpoint.", 0),
          sym("f_b", "variable", "right_sample",
              "Integrand evaluated at the right endpoint.", 0),
          sym("h", "variable", "panel_width",
              "Width of the panel, b - a.", 0)],
         [EQ, ADD, MUL],
         "Approximate the area under a curve on one interval by the area of "
         "the trapezoid through the two endpoint samples.",
         "The sharpest 'the numerical method IS the elementary formula' result "
         "in the three corpora, and it fires at TYPED level, character for "
         "character: `?0:V = *(?1:P, ?2:V, +(?3:V, ?4:V))`, shared with "
         "geometry.area_formulas.trapezoid_area_formula. A quadrature rule from "
         "Cotes and a mensuration formula from antiquity are one statement, and "
         "the matcher says so. Two caveats keep the claim honest. First, this "
         "is an `authored_to_match` twin in docs/BACKLOG.md's sense: the "
         "one-half is written as a constant slot because geometry writes it "
         "that way, and the textbook `h*(f(a)+f(b))/2` would not have fired. "
         "The defence is that the two statements really are the same statement, "
         "so adopting the notation is translation rather than disguise -- the "
         "same defence diffgeo.stokes.stokes_zero_form_case makes. Second, the "
         "twin is with the ONE-PANEL rule; the composite rule is a weighted sum "
         "with halved endpoint weights and belongs instead to the "
         "`sum⟨*(?1:P, ?2:V)⟩` family that this seeding pass grows to four "
         "members elsewhere.",
         ["Integrand defined and finite at both endpoints",
          "A single panel; the composite rule is a different statement",
          "Twice-differentiable integrand, if the h^3/12 error term is wanted",
          "Exactness holds for affine integrands and, by symmetry, for odd "
          "perturbations about the midpoint"],
         [COTES1722, DAVIS1984, BURDEN2015],
         disciplines=["numerical_analysis", "mathematics"],
         constants=[HALF_CONST],
         failure_modes=[
             "Applying it to an integrand with an endpoint singularity gives a "
             "finite answer for an infinite integral, silently.",
             "The composite rule's second-order accuracy becomes spectral "
             "accuracy for smooth periodic integrands over a full period -- so "
             "its reputation as a crude method is wrong in precisely the case "
             "where it is most often used.",
             "The error term's sign is fixed by the second derivative's sign, "
             "so for convex integrands the rule always OVERestimates; averaging "
             "it with the midpoint rule (which always underestimates) is "
             "Simpson's rule, and that structure is invisible here."],
         inferential_links=links(
             composed_with=["geometry.area_formulas.trapezoid_area_formula",
                            "numanalysis.interpolation.linear_interpolation"]),
         keywords=["trapezoidal rule", "quadrature", "Newton-Cotes",
                   "numerical integration", "trapezoid area", "Euler-Maclaurin"],
         canonical_objects=["panel", "endpoint sample", "quadrature estimate"]),

    # ---------------------------------------------------------------- 5 ----
    node("numanalysis.ode.euler_method_step",
         "Explicit Euler Method Step",
         "approximation", "derived", "ordinary_differential_equations", "time_stepping",
         "y_(n+1) = y_n + h * f(t_n, y_n)",
         "y_{n+1} = y_n + h\\, f(t_n, y_n)",
         [{"form_id": "increment", "notation_system": "ascii",
           "expression": "y_(n+1) - y_n = h * f(t_n, y_n)",
           "scope_note": "The increment form: a difference quotient set equal to the vector field, i.e. the ODE with the derivative replaced by a forward difference"},
          {"form_id": "implicit", "notation_system": "ascii",
           "expression": "y_(n+1) = y_n + h * f(t_(n+1), y_(n+1))",
           "scope_note": "Backward Euler: the same template, the slope evaluated at the new point. Structurally identical, numerically opposite (A-stable)"},
          {"form_id": "gradient_flow", "notation_system": "ascii",
           "expression": "theta_(n+1) = theta_n - h * GRAD(L)(theta_n)",
           "scope_note": "Explicit Euler applied to the gradient flow dtheta/dt = -GRAD(L); this IS ml.optimization.gradient_descent_step, with h the learning rate"},
          {"form_id": "runge_kutta", "notation_system": "ascii",
           "expression": "y_(n+1) = y_n + h * sum_j WEIGHT_j*STAGE_j",
           "scope_note": "The general explicit Runge-Kutta step; Euler is the one-stage member, and this form belongs to the weighted-sum family instead"}],
         "state_plus_scaled_rate",
         "YNEXT = Y + STEPSIZE*SLOPE",
         [slot("YNEXT", "variable", "next_state"),
          slot("Y", "variable", "current_state"),
          slot("STEPSIZE", "parameter", "step_size"),
          slot("SLOPE", "variable", "vector_field_value")],
         ["The step size is parameter-like and the slope is variable-like, "
          "which is the categorical fingerprint of every first-order method in "
          "the graph: a chosen number times a quantity the problem supplies.",
          "Sign is the only difference from ml.optimization.gradient_descent_step, "
          "and the matcher's family level absorbs it, since a free parameter "
          "can carry a sign. That absorption is the whole content of "
          "prediction 1's surviving half.",
          "One step, first order: the local error is O(h^2) and the global "
          "error O(h). Neither exponent appears in the template, because both "
          "are properties of the iterated map rather than of this statement.",
          "Explicit and implicit Euler share this template exactly. What "
          "separates them -- whether SLOPE is evaluated at the old or the new "
          "state -- is a statement about the arguments of f, and f does not "
          "appear. The grammar cannot distinguish the stable method from the "
          "unstable one."],
         [sym("y_n", "variable", "current_state",
              "Numerical approximation to the solution at time t_n.", 0),
          sym("h", "parameter", "step_size",
              "Time step, chosen by the integrator.", 0),
          sym("f", "variable", "vector_field_value",
              "Value of the right-hand side at the current point: the slope the "
              "solution has there.", 0),
          sym("t_n", "index", "time_index", "Discrete time level.", 0)],
         [EQ, ADD, MUL],
         "Advance the solution by following the tangent direction the "
         "differential equation prescribes at the current point, for one step.",
         "Prediction 1's surviving half, and it FIRED at family level. The "
         "typed skeleton `?0:V = +(?1:V, *(?2:P, ?3:V))` has no partner, "
         "because gradient descent carries a minus sign: "
         "`?0:V = +(?1:V, neg(*(?2:P, ?3:V)))`. But `absorb_parameter_signs` "
         "drops a negation whose operand has a parameter-like factor, which is "
         "exactly the case here -- so at family level this node twins "
         "`ml.optimization.gradient_descent_step` AND "
         "`ml.objective.kl_regularized_rl_objective`. The relationship is not a "
         "pun and not an analogy: gradient descent IS explicit Euler applied to "
         "the gradient flow dtheta/dt = -GRAD(L), and the learning rate IS the "
         "step size, with the entire stability theory (why too large a rate "
         "diverges) carried over unchanged. The one honest caveat is that the "
         "match level which fired is the loosest one, and it fired by erasing "
         "the minus sign that says descent rather than ascent -- true for a "
         "free parameter, and the reason the corpus reports family twins "
         "separately from typed ones. At shape level this node also joins the "
         "affine family (tangent-line linearization, CAPM, the Keynesian "
         "consumption function, affine location-scale), which is correct for a "
         "different reason: one Euler step is a tangent-line linearization of "
         "the solution.",
         ["f defined and continuous on the step interval",
          "Lipschitz continuity of f in y, for the classical convergence proof",
          "A step size inside the method's stability region for the problem's "
          "stiffest mode",
          "A supplied initial condition y_0"],
         [EULER1768, HAIRER1993, BUTCHER2016, BURDEN2015],
         disciplines=["numerical_analysis", "mathematics"],
         failure_modes=[
             "Explicit Euler is conditionally stable: on a stiff problem the "
             "step size is limited by the fastest decaying mode, not by the "
             "accuracy wanted, and the method blows up rather than degrading.",
             "First-order accuracy means halving the step buys one bit; the "
             "method is almost never the right choice and is almost always the "
             "one taught, which is the same relationship bisection has to "
             "root finding.",
             "Energy drift: applied to a Hamiltonian system, explicit Euler "
             "systematically gains energy, so the qualitative behaviour is "
             "wrong however small the step. The template cannot express the "
             "geometric structure being violated."],
         inferential_links=links(
             composed_with=["ml.optimization.gradient_descent_step",
                            "calculus.approximation.tangent_line_linearization",
                            "numanalysis.error.relative_condition_number"]),
         keywords=["Euler method", "explicit Euler", "time stepping",
                   "gradient flow", "gradient descent", "step size",
                   "first-order method"],
         canonical_objects=["state", "vector field", "time step"]),

    # ---------------------------------------------------------------- 6 ----
    node("numanalysis.interpolation.linear_interpolation",
         "Linear Interpolation (Convex Combination of Two Points)",
         "definition", "formal", "interpolation", "affine_combination",
         "y = (1 - t)*y_0 + t*y_1,  t in [0,1]",
         "y = (1-t)\\,y_0 + t\\,y_1, \\qquad t \\in [0,1]",
         [{"form_id": "expanded_affine", "notation_system": "ascii",
           "expression": "y = y_0 + t*(y_1 - y_0)",
           "scope_note": "Algebraically identical and structurally different: this form IS the affine family `?0:V = +(?1:V, *(?2:P, ?3:V))`, with the base point and the scaled displacement. Kept here rather than in the template because it is not how interpolation is written"},
          {"form_id": "two_point_form", "notation_system": "ascii",
           "expression": "y = y_0 + (x - x_0)*(y_1 - y_0)/(x_1 - x_0)",
           "scope_note": "The form used when the parameter must be recovered from an abscissa; the fraction is the parameter t"},
          {"form_id": "lagrange", "notation_system": "ascii",
           "expression": "y = sum_i BASIS_i*VALUE_i",
           "scope_note": "Degree-one Lagrange interpolation; the same statement written as a weighted sum, which is the form that joins the graph's four-discipline weighted-sum family"},
          {"form_id": "geometric", "notation_system": "vector_notation",
           "expression": "P(t) = (1 - t)*P_0 + t*P_1",
           "scope_note": "Vector-valued: the parameterized segment between two points, which is geomodel.bezier.de_casteljau_step"}],
         "two_point_convex_combination",
         "RESULT = (1 - PARAM)*START + PARAM*FINISH",
         [slot("RESULT", "variable", "interpolated_value"),
          slot("PARAM", "parameter", "interpolation_parameter"),
          slot("START", "variable", "left_value"),
          slot("FINISH", "variable", "right_value")],
         ["The interpolation parameter occurs TWICE, once bare and once inside "
          "`1 - PARAM`. That repetition is the partition of unity -- the two "
          "weights sum to one -- and it is the reason the node cannot reach the "
          "affine family, whose members all have distinct slots in every "
          "position.",
          "The weights sum to one, so the statement is invariant under adding a "
          "constant to both data values: interpolation commutes with "
          "translation. That is what makes it meaningful for points in space, "
          "where there is no origin, and it is the defining property of an "
          "AFFINE combination as opposed to a merely linear one.",
          "Restricting the parameter to [0,1] makes the combination convex and "
          "the result lie between the data; outside that range the same "
          "template is extrapolation, with the same algebra and none of the "
          "guarantees. The interval is a regularity condition, not part of the "
          "structure.",
          "Both data slots are variable-like and enter symmetrically under "
          "PARAM -> 1 - PARAM, which is the reversal symmetry of the segment."],
         [sym("y", "variable", "interpolated_value",
              "Interpolated value at parameter t.", 0),
          sym("t", "parameter", "interpolation_parameter",
              "Normalized position along the segment, zero at the left datum "
              "and one at the right.", 0),
          sym("y_0", "variable", "left_value", "Value at the left datum.", 0),
          sym("y_1", "variable", "right_value", "Value at the right datum.", 0)],
         [EQ, ADD, SUB, MUL],
         "The value at a fraction t of the way between two data is the same "
         "fraction of the way between their values: a straight line through "
         "two points, parameterized.",
         "Prediction 2 registered two comparisons and lost both, for two "
         "different and separately interesting reasons. (a) Against the AFFINE "
         "FAMILY: the relationship is real -- expand and you get "
         "`START + PARAM*(FINISH - START)`, which is "
         "`?0:V = +(?1:V, *(?2:P, ?3:V))` -- but the unexpanded skeleton is "
         "`?0:V = +(*(?1:P, ?2:V), *(?3:V, +(1, neg(?1:P))))`, with the "
         "parameter slot occurring twice and an extra `+` node inside a factor. "
         "Nothing matches at any level. Rewriting to the expanded form would "
         "have made it fire and would have been authoring to match, so the "
         "expanded form sits in equivalent_forms where it belongs; the miss "
         "goes on the record. It is a rewrite-based relation, the same class "
         "docs/BACKLOG.md already records for series truncation and for "
         "collapsing a sum under a constant summand. (b) Against PROBABILITY "
         "MIXTURES: there is nothing to compare with. The graph has no mixture "
         "node -- `probstat.probability.total_probability_partition` is an "
         "indexed sum, not a two-point convex combination -- so the prediction "
         "could not be evaluated at all. A two-component mixture "
         "`p = (1-w)*p_0 + w*p_1` would twin this node exactly, and is the "
         "single highest-value addition anyone could make to "
         "data/statistics for the purpose of connecting it to geometry.",
         ["Two data values and a parameter in [0,1] for interpolation proper",
          "Values in an affine space, so that convex combinations are defined; "
          "the statement is meaningless for categorical data however numeric "
          "the codes",
          "Outside [0,1] the same formula is extrapolation and carries no "
          "betweenness guarantee"],
         [MEIJERING2002, FARIN2002, BURDEN2015],
         disciplines=["numerical_analysis", "mathematics", "geometric_modeling"],
         failure_modes=[
             "Interpolating angles, hues or rotations componentwise takes the "
             "chord instead of the arc: the formula is defined but the answer "
             "leaves the manifold, which is exactly why "
             "geomodel.quaternions.unit_quaternion_constraint exists.",
             "Repeated linear interpolation of sampled data is only "
             "C-zero continuous, so derivatives computed from it are "
             "discontinuous at every knot.",
             "Written as (1-t)*y_0 + t*y_1 the formula is not exactly "
             "value-preserving at t = 1 in floating point; the expanded form "
             "y_0 + t*(y_1 - y_0) is monotone but not endpoint-exact. No "
             "spelling is both, and the template cannot say which was meant."],
         inferential_links=links(
             equivalent_to=["geomodel.bezier.de_casteljau_step"],
             composed_with=["numanalysis.integration.trapezoidal_rule",
                            "probstat.transform.affine_location_scale"]),
         keywords=["linear interpolation", "lerp", "convex combination",
                   "affine combination", "partition of unity", "barycentric"],
         canonical_objects=["data pair", "interpolation parameter", "segment"]),

    # ---------------------------------------------------------------- 7 ----
    node("numanalysis.error.relative_condition_number",
         "Relative Condition Number",
         "definition", "formal", "error_analysis", "conditioning",
         "kappa = (relative change in output) / (relative change in input)",
         "\\kappa = \\frac{\\lVert \\delta f \\rVert / \\lVert f \\rVert}{\\lVert \\delta x \\rVert / \\lVert x \\rVert}",
         [{"form_id": "derivative_form", "notation_system": "ascii",
           "expression": "kappa = |x * f'(x) / f(x)|",
           "scope_note": "The differential limit for a scalar function; the elasticity of f, which is the same quantity economics calls price elasticity"},
          {"form_id": "matrix_condition", "notation_system": "matrix_notation",
           "expression": "kappa(A) = NORM(A) * NORM(INVERSE(A))",
           "scope_note": "Turing's condition number of a linear system, the special case for f(x) = A^(-1)x"},
          {"form_id": "error_budget", "notation_system": "ascii",
           "expression": "(relative forward error) <= kappa * (relative backward error)",
           "scope_note": "The rule of thumb the number exists for: conditioning is the problem's, stability is the algorithm's, and this inequality is how they combine"}],
         "ratio_rate",
         "CONDITION = OUTPUTPERTURB / INPUTPERTURB",
         [slot("CONDITION", "variable", "condition_number"),
          slot("OUTPUTPERTURB", "variable", "relative_output_change"),
          slot("INPUTPERTURB", "variable", "relative_input_change")],
         ["Both perturbations are already RELATIVE, so the ratio is "
          "dimensionless and scale-free. That is what makes it a property of "
          "the problem rather than of the units, and it is why the node belongs "
          "in the same family as a price elasticity rather than in the same "
          "family as a speed.",
          "Both slots are variable-like: neither perturbation is chosen, both "
          "are observed. A parameter-like slot here would make the statement a "
          "model rather than a measurement.",
          "The template is the ratio, not the supremum over perturbations. The "
          "actual definition takes a limit of a supremum over all perturbations "
          "of a given size, and the grammar has neither a binder nor a limit "
          "that composes with one -- the same obstacle "
          "infotheory.channel.channel_capacity records.",
          "Conditioning is a property of the problem; stability is a property "
          "of the algorithm. This statement mentions no algorithm, and that "
          "absence is the point."],
         [sym("kappa", "variable", "condition_number",
              "Relative condition number of the problem at the given input.", 0),
          sym("rel_out", "variable", "relative_output_change",
              "Relative change induced in the output.", 0),
          sym("rel_in", "variable", "relative_input_change",
              "Relative change applied to the input.", 0)],
         [EQ, DIV],
         "How much a problem amplifies relative perturbations: the factor by "
         "which a small relative error in the data is multiplied on its way to "
         "the answer.",
         "FIRED into the graph's largest cross-discipline family. "
         "`?0:V = *(?1:V, inv(?2:V))` -- one variable over another -- now has "
         "seven members across six disciplines: average rate of change "
         "(calculus), molarity (chemistry), price elasticity (economics), the "
         "PPO probability ratio (machine learning), average speed and mass "
         "density (physics), and this. The membership is not a coincidence of "
         "notation. A condition number IS an elasticity: the derivative-form "
         "variant `|x f'(x)/f(x)|` is character for character the economists' "
         "definition of elasticity of demand, discovered independently in the "
         "1890s and the 1940s. What the family shares is the act of dividing a "
         "response by the stimulus that caused it and reading the quotient as a "
         "property of the system, and the matcher groups all seven without "
         "being told any of the semantics.",
         ["A well-defined nonzero input and output, so the relative measures "
          "exist",
          "Perturbations small enough for the linearization to hold; the "
          "definition is a limit, and the template is its ratio",
          "A norm chosen on each side; different norms give different constants "
          "and the same order of magnitude"],
         [TURING1948, RICE1966, TREFETHEN1997, HIGHAM2002],
         disciplines=["numerical_analysis", "mathematics"],
         failure_modes=[
             "A large condition number does not mean the algorithm is bad -- it "
             "means no algorithm can do better. Reporting it as a criticism of "
             "the code is the commonest misreading.",
             "The relative form is undefined where the output vanishes, which "
             "is exactly where root-finding problems live; near a multiple root "
             "the condition number diverges and the accuracy loss it predicts "
             "is real.",
             "Condition numbers compose multiplicatively along a pipeline, so a "
             "chain of well-conditioned steps can be badly conditioned overall "
             "and no single step's number will show it."],
         inferential_links=links(
             composed_with=["numanalysis.floatingpoint.machine_epsilon_bound",
                            "numanalysis.rootfinding.newton_iteration",
                            "economics.microeconomics.price_elasticity_of_demand"]),
         keywords=["condition number", "conditioning", "error analysis",
                   "elasticity", "relative error", "backward stability"],
         canonical_objects=["problem", "perturbation", "amplification factor"]),

    # ---------------------------------------------------------------- 8 ----
    node("numanalysis.floatingpoint.machine_epsilon_bound",
         "Floating-Point Rounding Bound",
         "theorem", "formal", "floating_point", "rounding",
         "|fl(x) - x| <= u * |x|",
         "\\lvert \\mathrm{fl}(x) - x \\rvert \\le u \\lvert x \\rvert",
         [{"form_id": "relative_form", "notation_system": "ascii",
           "expression": "fl(x) = x*(1 + delta),  |delta| <= u",
           "scope_note": "The (1+delta) model: the form every rounding-error proof actually uses, because it composes multiplicatively through a computation"},
          {"form_id": "spacing", "notation_system": "ascii",
           "expression": "|fl(x) - x| <= ULP(x)/2",
           "scope_note": "Absolute form in units in the last place; equivalent under round-to-nearest and sharper near the bottom of a binade"},
          {"form_id": "operation_form", "notation_system": "ascii",
           "expression": "fl(a OP b) = (a OP b)*(1 + delta),  |delta| <= u",
           "scope_note": "IEEE 754's correct-rounding requirement extended from representation to each of the five basic operations"}],
         "relative_error_bound",
         "ROUNDOFF <= UNITROUNDOFF*EXACT",
         [slot("ROUNDOFF", "variable", "representation_error"),
          slot("UNITROUNDOFF", "constant", "unit_roundoff"),
          slot("EXACT", "variable", "exact_magnitude")],
         ["A `<=`, not an `=`. It is one of the few inequalities in the graph, "
          "and the relation is the content: no equality holds, because the "
          "actual error depends on where in a binade the number falls, and the "
          "guarantee is exactly that it never exceeds this bound.",
          "The unit roundoff is a `constant` slot -- a fixed property of the "
          "arithmetic, not of the problem. That is what distinguishes this "
          "statement from the condition number, whose every slot is "
          "variable-like: one is about the machine, the other about the "
          "problem.",
          "The bound is RELATIVE (the right-hand side scales with the "
          "magnitude), which is the whole design of floating point: constant "
          "relative precision across many orders of magnitude, paid for with "
          "unbounded absolute error at the top of the range.",
          "The statement covers representation only. That every basic operation "
          "obeys the same bound is IEEE 754's correct-rounding requirement -- a "
          "much stronger claim about an implementation, kept in "
          "equivalent_forms rather than in the template."],
         [sym("x", "variable", "exact_magnitude",
              "The exact real number being represented.", 0),
          sym("fl_x", "variable", "representation_error",
              "Magnitude of the difference between x and its nearest "
              "representable neighbour.", 0)],
         [LEQ, MUL],
         "Rounding a real number to the nearest floating-point number changes "
         "it by at most a fixed fraction of its own size.",
         "A singleton, and the relation symbol is why. Its skeleton "
         "`?0:V <= *(?1:P, ?2:V)` is the family "
         "`?0:V = *(?1:P, ?2:V)` -- circle circumference, Newton's second law, "
         "Ohm's law -- with `=` replaced by `<=`, and the matcher treats "
         "relations as part of the skeleton, so nothing fires at any level. "
         "That is defensible: `F = m*a` and `err <= u*|x|` really are different "
         "kinds of claim, one an identity and one a guarantee, and collapsing "
         "them would erase the difference between a law and a bound. But it "
         "does mean the graph currently has no way to say 'this bound is the "
         "inequality form of that proportionality', and every error bound "
         "anyone adds will land in the same isolation. Worth contrasting with "
         "`geotop.measure.area_monotonicity`, the graph's other lonely "
         "inequality, which is isolated for the opposite reason -- it is the "
         "only relation nested inside a call argument.",
         ["Round-to-nearest, ties-to-even; other rounding modes double the "
          "constant",
          "x within the normal range: no overflow, and not subnormal, where the "
          "relative bound fails and only an absolute one holds",
          "u = 2^-53 for binary64, 2^-24 for binary32, under IEEE 754"],
         [WILKINSON1963, IEEE754, HIGHAM2002, TREFETHEN1997],
         disciplines=["numerical_analysis", "computer_science"],
         constants=[UNITROUNDOFF_CONST],
         failure_modes=[
             "Subnormal numbers violate the relative bound outright: near zero "
             "the spacing stops shrinking and only an absolute bound survives.",
             "The bound is per operation and composes as a product of "
             "(1 + delta) factors, so an n-operation computation carries "
             "roughly n*u, and quoting the single-operation bound for a whole "
             "algorithm understates the error by that factor.",
             "'Machine epsilon' names two different numbers in common use -- "
             "the spacing above one (2^-52 for binary64) and the unit roundoff "
             "(2^-53) -- and the constant slot here is the second."],
         inferential_links=links(
             composed_with=["numanalysis.error.relative_condition_number",
                            "numanalysis.rootfinding.bisection_interval_halving"]),
         keywords=["machine epsilon", "unit roundoff", "IEEE 754",
                   "floating point", "relative error", "correct rounding"],
         canonical_objects=["floating-point number", "rounding", "unit roundoff"]),
]


# --------------------------------------------------------------------------
# Corpus 2: graph theory
# --------------------------------------------------------------------------

GRAPHTHEORY = [

    # ---------------------------------------------------------------- 1 ----
    node("graphtheory.degree.handshake_lemma",
         "Handshake Lemma (Degree-Sum Formula)",
         "lemma", "formal", "degree_theory", "counting",
         "sum over v in V of deg(v) = 2*|E|",
         "\\sum_{v \\in V} \\deg(v) = 2\\lvert E\\rvert",
         [{"form_id": "parity_corollary", "notation_system": "ascii",
           "expression": "|{v : deg(v) is odd}| is even",
           "scope_note": "The corollary everyone remembers: a graph has an even number of odd-degree vertices, immediate from the left side being even"},
          {"form_id": "incidence_double_count", "notation_system": "ascii",
           "expression": "|{(v, e) : v incident to e}| = 2*|E|",
           "scope_note": "The proof made explicit: count incident vertex-edge pairs two ways. The sum of degrees IS that count"},
          {"form_id": "directed", "notation_system": "ascii",
           "expression": "sum_v indeg(v) = sum_v outdeg(v) = |E|",
           "scope_note": "Digraph version, where the factor two disappears because each arc is counted once at each end for a different statistic"}],
         "degree_sum_double_count",
         "sum_i DEGREE_i = 2*EDGES",
         [slot("DEGREE_i", "variable", "vertex_degree"),
          slot("EDGES", "variable", "edge_count")],
         ["The literal 2 is not a scale factor, it is an ARITY: every edge has "
          "exactly two ends. Replacing it with a slot would make the statement "
          "about hypergraphs, where it becomes sum of degrees = sum of edge "
          "sizes and the constant disappears entirely.",
          "This is the archetypal double count: one set (the incident "
          "vertex-edge pairs) enumerated two ways, once per vertex and once per "
          "edge. The template records the equality and cannot record that both "
          "sides count the same set, which is where the proof lives.",
          "The sum is over vertices and the right-hand side counts edges, so "
          "the two sides range over different index sets. Nothing in the "
          "grammar marks that, and it is the only reason the statement is not "
          "trivial.",
          "Euler stated it in 1736 in the Koenigsberg paper, as the obstruction "
          "to an Eulerian walk. It is the oldest theorem in graph theory and "
          "the first result in the subject to be proved by counting a set two "
          "ways."],
         [sym("deg_v", "variable", "vertex_degree",
              "Number of edge-ends incident with a vertex; loops count twice.", 0),
          sym("E", "variable", "edge_count",
              "Number of edges in the graph.", 0),
          sym("v", "index", "vertex_index", "Index over the vertex set.", 0)],
         [EQ, MUL, SUM],
         "Adding up how many edges touch each vertex counts every edge exactly "
         "twice, once at each end.",
         "A singleton at every level: `sum⟨?0:V⟩ = *(2, ?1:V)`. The nearest "
         "structures in the graph are the weighted-sum family "
         "`?0:V = sum⟨*(?1:P, ?2:V)⟩` (four members after this seeding pass) "
         "and `algtop.invariants.euler_characteristic_complex`, and neither is "
         "reachable: the summand here is a BARE slot with no weight, and the "
         "aggregate sits on the left of the relation with a literal-scaled "
         "count on the right. The interesting reading is that an unweighted sum "
         "is the weighted sum with every weight equal to one -- the same "
         "collapse-a-sum-under-a-constant rewrite docs/BACKLOG.md records as "
         "the missing relation between uniform and Shannon entropy, and as the "
         "missing series truncation. Three independent occurrences of one "
         "rewrite class, in three unrelated corpora, is the strongest available "
         "case for it being the next thing built.",
         ["A finite graph",
          "Loops contribute two to their vertex's degree; this convention is "
          "what makes the statement true rather than approximately true",
          "Multi-edges permitted and counted with multiplicity"],
         [EULER1736, DIESTEL2017, WEST2001, BONDY2008],
         disciplines=["graph_theory", "mathematics", "combinatorics"],
         index_sets=[IDX_VERTICES],
         failure_modes=[
             "Applied to a digraph without adjustment the factor two is wrong; "
             "in-degree and out-degree each sum to |E|, not to 2|E|.",
             "For infinite graphs both sides can be infinite and the equality "
             "carries no information, so the finiteness hypothesis is not "
             "decoration.",
             "The parity corollary is often quoted as if it were the lemma; it "
             "is strictly weaker, and the double-counting content is lost in "
             "the retelling."],
         inferential_links=links(
             entails=["graphtheory.degree.average_degree_from_edge_count",
                      "graphtheory.enumeration.complete_graph_edge_count"],
             composed_with=["geotop.polyhedra.euler_polyhedron_formula"]),
         keywords=["handshake lemma", "degree sum", "double counting",
                   "Euler 1736", "Koenigsberg", "parity"],
         canonical_objects=["vertex", "edge", "degree"]),

    # ---------------------------------------------------------------- 2 ----
    node("graphtheory.degree.average_degree_from_edge_count",
         "Average Degree of a Finite Graph",
         "corollary", "derived", "degree_theory", "density",
         "dbar = 2*|E| / |V|",
         "\\bar{d} = \\frac{2\\lvert E\\rvert}{\\lvert V\\rvert}",
         [{"form_id": "from_handshake", "notation_system": "ascii",
           "expression": "dbar = (sum_v deg(v)) / |V|",
           "scope_note": "The definition before the handshake lemma is applied; substituting the lemma is the whole derivation"},
          {"form_id": "edge_density", "notation_system": "ascii",
           "expression": "|E| = dbar*|V| / 2",
           "scope_note": "Solved for the edge count: a graph on n vertices with average degree d has dn/2 edges, the form used in random-graph arguments"}],
         "scaled_ratio_rate",
         "AVGDEGREE = 2*EDGES/VERTICES",
         [slot("AVGDEGREE", "variable", "average_degree"),
          slot("EDGES", "variable", "edge_count"),
          slot("VERTICES", "variable", "vertex_count")],
         ["Structurally a density -- a count divided by an extent -- with a "
          "literal 2 in front that comes from the handshake lemma and from "
          "nowhere else. The 2 is the arity of an edge, inherited.",
          "Both counts are variable-like: this is a measurement of a given "
          "graph, not a model with tunable constants.",
          "The average is over vertices, so it is a per-vertex quantity, while "
          "the numerator counts edges. Densities in the graph's rate family all "
          "share that mismatch of units between numerator and denominator; it "
          "is what makes them informative.",
          "Sparse and dense are defined by how this quantity behaves as the "
          "vertex count grows -- bounded average degree is sparse, average "
          "degree growing like the vertex count is dense -- and the template "
          "cannot express an asymptotic regime."],
         [sym("dbar", "variable", "average_degree",
              "Mean degree over all vertices.", 0),
          sym("E", "variable", "edge_count", "Number of edges.", 0),
          sym("V", "variable", "vertex_count", "Number of vertices.", 0)],
         [EQ, MUL, DIV],
         "The average number of neighbours a vertex has is twice the edge count "
         "divided by the vertex count.",
         "The corpus's cleanest near miss, and the second in this seeding pass. "
         "Its skeleton is `?0:V = *(2, ?1:V, inv(?2:V))`; the rate/density "
         "family is `?0:V = *(?1:V, inv(?2:V))` with seven members across six "
         "disciplines, including this pass's own condition number. The ONLY "
         "difference is one numeric literal in a multiplicative position, and "
         "the semantics agree perfectly -- average degree is edge density per "
         "vertex, with a factor two for edge arity, exactly as a molarity is "
         "amount per volume. docs/BACKLOG.md records the same blocker from the "
         "other direction for `diffgeo.curves.circle_curvature`, where a "
         "literal 1 in the numerator keeps a curvature out of the same family, "
         "and `numanalysis.rootfinding.bisection_interval_halving` hits it a "
         "third time with a literal 2 in the denominator. Three independent "
         "instances, all of them 'a family member with an unparameterized "
         "constant attached', argue that the wanted match level (a numeric "
         "literal may bind a parameter-like slot) should be reported as its "
         "own strictly-looser level.",
         ["A finite graph with at least one vertex",
          "Simple or multigraph alike, provided the degree convention for loops "
          "is the handshake lemma's",
          "The quantity is a mean, so it says nothing about the degree "
          "distribution, which in real networks is usually heavy-tailed"],
         [DIESTEL2017, BONDY2008, WEST2001],
         disciplines=["graph_theory", "mathematics", "combinatorics"],
         failure_modes=[
             "In a scale-free network the mean degree is finite while the "
             "variance diverges, so the average is a poor summary of exactly "
             "the graphs it is most often quoted for.",
             "Reading it as 'a typical vertex has dbar neighbours' fails "
             "whenever the degree distribution is skewed; the friendship "
             "paradox is precisely the gap between this mean and the mean "
             "degree of a neighbour."],
         inferential_links=links(
             entailed_by=["graphtheory.degree.handshake_lemma"],
             composed_with=["physics.materials.mass_density",
                            "calculus.differentiation.average_rate_of_change"]),
         keywords=["average degree", "edge density", "sparse graph",
                   "handshake lemma", "numeric literal blocker"],
         canonical_objects=["vertex set", "edge set", "degree distribution"]),

    # ---------------------------------------------------------------- 3 ----
    node("graphtheory.enumeration.complete_graph_edge_count",
         "Edge Count of the Complete Graph",
         "proposition", "formal", "enumerative_graph_theory", "counting",
         "|E(K_n)| = n*(n - 1)/2",
         "\\lvert E(K_n)\\rvert = \\binom{n}{2} = \\frac{n(n-1)}{2}",
         [{"form_id": "binomial", "notation_system": "ascii",
           "expression": "|E(K_n)| = C(n, 2)",
           "scope_note": "As a binomial coefficient: the number of unordered pairs. The grammar has no binomial form, which is why the template is the expanded product"},
          {"form_id": "from_handshake", "notation_system": "ascii",
           "expression": "2*|E| = n*(n-1)",
           "scope_note": "The handshake lemma with every degree equal to n-1; this is the derivation, and it is also the form without the division"},
          {"form_id": "triangular", "notation_system": "ascii",
           "expression": "|E(K_n)| = sum_(k=1)^(n-1) k",
           "scope_note": "The (n-1)-st triangular number: add a vertex, and it joins to every vertex already present"}],
         "unordered_pair_count",
         "EDGES = VERTICES*(VERTICES - 1)/2",
         [slot("EDGES", "variable", "edge_count"),
          slot("VERTICES", "variable", "vertex_count")],
         ["The vertex-count slot occurs TWICE. That repetition is the whole "
          "combinatorial content -- both members of the pair are drawn from the "
          "same set -- and it is what makes the statement unreachable from "
          "every product-shaped node in the graph, all of which have two "
          "independent extents.",
          "Two numeric literals, and they mean different things: the 1 removes "
          "the self-pair, the 2 divides out the ordering. A generalization to "
          "k-subsets replaces both, so neither is a scale factor.",
          "Contrast graphtheory.enumeration.complete_bipartite_edge_count, "
          "`EDGES = PARTONE*PARTTWO`, which counts pairs drawn from two "
          "different sets and consequently DOES twin rectangle area. The two "
          "nodes are the same act of counting -- choose one endpoint, then the "
          "other -- and they differ exactly in whether the two choices are "
          "independent. The graph can see the independent case and cannot see "
          "the dependent one.",
          "The statement is an equality about a specific family of graphs, not "
          "a bound; it is the maximum edge count for a simple graph on n "
          "vertices, and that maximality is a separate claim."],
         [sym("E", "variable", "edge_count",
              "Number of edges of the complete graph.", 0),
          sym("n", "variable", "vertex_count", "Number of vertices.", 0)],
         [EQ, MUL, SUB, DIV],
         "A complete graph has one edge for every unordered pair of distinct "
         "vertices, and there are n(n-1)/2 such pairs.",
         "Prediction 4 asked what, if anything, this meets among pair-coupling "
         "and combination structures. The answer is NOTHING, at shape, typed or "
         "family level, and both reasons are worth having on the record. "
         "(1) SLOT RECURRENCE: the skeleton is "
         "`?0:V = *(?1:V, +(?1:V, neg(1)), inv(2))`, where `?1` appears twice. "
         "The graph's product-shaped families -- rectangle area, Gaussian "
         "curvature as a product of principal curvatures, Beer-Lambert, "
         "Newton's second law -- all have distinct slots in each factor, "
         "because they multiply independent quantities. Choosing two things "
         "from one set is structurally a different act from multiplying two "
         "extents, and the matcher is right to say so. (2) LITERALS: even if "
         "slot recurrence were handled, the two numeric literals sit where a "
         "matchable statement would have slots. The honest summary is that the "
         "graph has no combinatorial-counting family yet; this node and "
         "`graphtheory.enumeration.cayley_formula` are its first two members "
         "and they do not match each other either, since one is a product and "
         "the other a power. Both, however, have the recurrent-slot property, "
         "and a structural query facility of the kind docs/BACKLOG.md wants "
         "would collect them together with the fixed-point and idempotence "
         "nodes on the strength of it.",
         ["A simple graph: no loops and no multi-edges",
          "n at least one; the formula gives zero at n = 1, correctly",
          "Undirected; the directed complete graph has n(n-1) arcs, the same "
          "count without the division"],
         [DIESTEL2017, WEST2001, BONDY2008],
         disciplines=["graph_theory", "mathematics", "combinatorics"],
         failure_modes=[
             "Quoted as an upper bound for arbitrary graphs it is correct only "
             "for simple graphs; multigraphs have no such bound.",
             "The quadratic growth is the whole reason dense-graph algorithms "
             "are quoted in terms of |E| rather than |V|, and reading the "
             "formula as 'about n^2' loses the exactness that makes it a "
             "counting statement rather than an estimate."],
         inferential_links=links(
             entailed_by=["graphtheory.degree.handshake_lemma"],
             composed_with=["graphtheory.enumeration.complete_bipartite_edge_count"]),
         keywords=["complete graph", "K_n", "edge count", "binomial coefficient",
                   "unordered pairs", "slot recurrence"],
         canonical_objects=["complete graph", "vertex pair", "edge set"]),

    # ---------------------------------------------------------------- 4 ----
    node("graphtheory.enumeration.complete_bipartite_edge_count",
         "Edge Count of the Complete Bipartite Graph",
         "proposition", "formal", "enumerative_graph_theory", "counting",
         "|E(K_(m,n))| = m*n",
         "\\lvert E(K_{m,n})\\rvert = mn",
         [{"form_id": "as_matrix", "notation_system": "matrix_notation",
           "expression": "|E| = ONES(m, n) counted entrywise",
           "scope_note": "The biadjacency matrix is the all-ones m-by-n matrix, so the edge count is its number of entries"},
          {"form_id": "from_handshake", "notation_system": "ascii",
           "expression": "2*|E| = m*n + n*m",
           "scope_note": "Handshake applied to the bipartition: every vertex on one side has degree equal to the other side's size"},
          {"form_id": "turan_extremal", "notation_system": "ascii",
           "expression": "|E| <= FLOOR(N^2/4) with equality for m = n = N/2",
           "scope_note": "The extremal reading: among complete bipartite graphs on N vertices the balanced one is largest, which is the base case of Turan's theorem"}],
         "bilinear_product",
         "EDGES = PARTONE*PARTTWO",
         [slot("EDGES", "variable", "edge_count"),
          slot("PARTONE", "variable", "first_part_size"),
          slot("PARTTWO", "variable", "second_part_size")],
         ["Two independent extents multiplied. Unlike the complete graph, the "
          "two endpoint choices come from different sets, so the slots are "
          "distinct and the statement joins the graph's product family "
          "immediately.",
          "Both slots are variable-like and enter symmetrically, which the "
          "commutative `*` of the grammar represents faithfully here: "
          "K_(m,n) and K_(n,m) are the same graph.",
          "The pair (this node, complete_graph_edge_count) is a controlled "
          "experiment on slot recurrence held inside one corpus: same subject, "
          "same act of counting, one with independent choices and one with "
          "dependent ones, one twinning three disciplines and one twinning "
          "nothing.",
          "Bipartiteness is a hypothesis about the graph, not a term in the "
          "formula; the template says only that a count factors as a product."],
         [sym("E", "variable", "edge_count", "Number of edges.", 0),
          sym("m", "variable", "first_part_size",
              "Number of vertices in the first part.", 0),
          sym("n", "variable", "second_part_size",
              "Number of vertices in the second part.", 0)],
         [EQ, MUL],
         "Joining every vertex of one part to every vertex of the other "
         "produces exactly one edge per pair, so the edge count is the product "
         "of the part sizes.",
         "FIRED, and across a gap nobody would have looked for. "
         "`?0:V = *(?1:V, ?2:V)` is shared with "
         "`geometry.area_formulas.rectangle_area_formula` and "
         "`diffgeo.surfaces.gaussian_curvature_principal_product`: a "
         "combinatorial count, a mensuration formula and a curvature invariant, "
         "in three disciplines. The shared content is real -- each is a "
         "quantity determined by two independent extents, and in each case the "
         "product is exactly the count of a grid of pairs. The biadjacency "
         "matrix of K_(m,n) IS an m-by-n rectangle of ones, and its edge count "
         "IS that rectangle's area. Set beside "
         "`graphtheory.enumeration.complete_graph_edge_count`, which twins "
         "nothing, this is the sharpest illustration available of what slot "
         "recurrence costs: the two nodes are one page apart in every textbook "
         "and they land in different worlds.",
         ["A complete bipartite graph, so every cross pair is present exactly "
          "once",
          "Simple and undirected",
          "The two parts disjoint; overlapping parts are not a bipartition"],
         [KONIG1936, DIESTEL2017, WEST2001],
         disciplines=["graph_theory", "mathematics", "combinatorics"],
         failure_modes=[
             "The formula counts edges of the COMPLETE bipartite graph; an "
             "arbitrary bipartite graph only satisfies it as an upper bound.",
             "Reading the product as 'area' is a genuine structural analogy and "
             "not a metric one: there is no length in a graph, and the twin the "
             "matcher reports is a statement about the arithmetic, which is all "
             "it claims to be."],
         inferential_links=links(
             composed_with=["graphtheory.enumeration.complete_graph_edge_count",
                            "geometry.area_formulas.rectangle_area_formula"]),
         keywords=["complete bipartite graph", "K_{m,n}", "edge count",
                   "biadjacency matrix", "product", "Turan"],
         canonical_objects=["bipartition", "cross pair", "biadjacency matrix"]),

    # ---------------------------------------------------------------- 5 ----
    node("graphtheory.trees.tree_edge_count",
         "A Tree on n Vertices Has n - 1 Edges",
         "theorem", "formal", "trees", "counting",
         "|E| = |V| - 1",
         "\\lvert E\\rvert = \\lvert V\\rvert - 1",
         [{"form_id": "euler_planar", "notation_system": "ascii",
           "expression": "|V| - |E| + 1 = 2",
           "scope_note": "Euler's polyhedron formula for a plane tree, which has exactly one face. This is geotop.polyhedra.euler_polyhedron_formula with FACES bound to 1 -- the same theorem, and the two templates cannot see it"},
          {"form_id": "forest", "notation_system": "ascii",
           "expression": "|E| = |V| - c",
           "scope_note": "A forest with c components; the tree is the case c = 1, and the general statement replaces the literal with a slot"},
          {"form_id": "characterization", "notation_system": "ascii",
           "expression": "connected AND |E| = |V| - 1 implies acyclic",
           "scope_note": "Any two of {connected, acyclic, |E| = |V| - 1} imply the third; the grammar has no conjunction, so this stays in prose"}],
         "count_minus_unit",
         "EDGES = VERTICES - 1",
         [slot("EDGES", "variable", "edge_count"),
          slot("VERTICES", "variable", "vertex_count")],
         ["The literal 1 is the number of components. Writing it as a slot "
          "would state the forest version, which is strictly more general and "
          "is a different theorem; keeping it literal is the choice to state "
          "the tree case.",
          "The statement is an equality between two counts of different kinds "
          "of object, which is the same double-counting genre as the handshake "
          "lemma -- here realized by the bijection sending each non-root vertex "
          "to the edge above it.",
          "It is Euler's polyhedron formula for a plane tree: one face, so "
          "V - E + 1 = 2. The graph carries that formula "
          "(geotop.polyhedra.euler_polyhedron_formula) and the connection is "
          "recorded here by hand, because a literal bound into a slot is "
          "exactly the specialization `specialize.py` suppresses by design.",
          "Minimality and maximality are corollaries, not the statement: a tree "
          "is the sparsest connected graph and the densest acyclic one, and "
          "neither claim is in the template."],
         [sym("E", "variable", "edge_count", "Number of edges of the tree.", 0),
          sym("V", "variable", "vertex_count", "Number of vertices.", 0)],
         [EQ, SUB],
         "Every tree has exactly one fewer edge than it has vertices.",
         "A singleton: `?0:V = +(?1:V, neg(1))` matches nothing. The near "
         "relation worth naming is not a twin but a specialization the tooling "
         "cannot report. `geotop.polyhedra.euler_polyhedron_formula` "
         "(`VERTICES - EDGES + FACES = 2`) covers this node by binding FACES to "
         "the literal 1 -- a plane tree has one face -- and that binding is a "
         "plain slot-to-literal substitution with no absorption and no identity "
         "element, which is precisely the class `specialize.py` filters out. "
         "docs/BACKLOG.md already records two instances of that filter dropping "
         "a corpus's headline specialization (Euler characteristic covering the "
         "polyhedron formula; DE-9IM disjointness covering the complement law) "
         "and one more from machine learning. This is the fourth, and it is the "
         "same pair of nodes as the first: `euler_polyhedron_formula` is now "
         "the target of two suppressed specializations from two different "
         "corpora. The edge is asserted by hand as a one-sided `composed_with`.",
         ["A tree: connected and acyclic",
          "Finite",
          "Undirected; the rooted/directed version counts the same edges"],
         [EULER1758, CAYLEY1889, DIESTEL2017, WEST2001],
         disciplines=["graph_theory", "mathematics", "combinatorics"],
         failure_modes=[
             "The equality alone does not characterize a tree: a disjoint union "
             "of a cycle and an isolated vertex satisfies it. Connectivity is "
             "not optional.",
             "Applied to a forest without adjusting the constant it "
             "overestimates the edge count by one per extra component."],
         inferential_links=links(
             composed_with=["geotop.polyhedra.euler_polyhedron_formula",
                            "graphtheory.enumeration.cayley_formula"]),
         keywords=["tree", "spanning tree", "acyclic", "Euler formula",
                   "edge count", "suppressed specialization"],
         canonical_objects=["tree", "vertex", "edge"]),

    # ---------------------------------------------------------------- 6 ----
    node("graphtheory.enumeration.cayley_formula",
         "Cayley's Formula for Labelled Trees",
         "theorem", "formal", "enumerative_graph_theory", "tree_counting",
         "t(n) = n^(n - 2)",
         "t(n) = n^{n-2}",
         [{"form_id": "prufer", "notation_system": "ascii",
           "expression": "t(n) = |{sequences of length n-2 over an n-letter alphabet}|",
           "scope_note": "Pruefer's bijection: the count is a word count, which is what makes the power the natural form"},
          {"form_id": "matrix_tree", "notation_system": "matrix_notation",
           "expression": "t(G) = DET(reduced Laplacian of G)",
           "scope_note": "Kirchhoff's matrix-tree theorem; Cayley's formula is the case G = K_n, where the determinant evaluates to n^(n-2)"},
          {"form_id": "rooted", "notation_system": "ascii",
           "expression": "|{rooted labelled trees}| = n^(n-1)",
           "scope_note": "One factor of n for the choice of root; the exponent's off-by-one is where the formula's difficulty is concentrated"}],
         "self_indexed_power",
         "TREES = VERTICES^(VERTICES - 2)",
         [slot("TREES", "variable", "tree_count"),
          slot("VERTICES", "variable", "vertex_count")],
         ["The vertex-count slot appears in the base AND in the exponent. That "
          "self-reference is what makes the growth super-exponential and is the "
          "structural signature of a count of labelled objects on the very set "
          "being counted over.",
          "The literal 2 in the exponent is the reason the formula is famous: "
          "n^n would be sequences, n^(n-1) rooted trees, and the two lost "
          "factors correspond to the root and the last Pruefer letter. Making "
          "the 2 a slot would state a family of formulas nobody needs.",
          "Labelled, not unlabelled. The count of unlabelled trees has no "
          "closed form at all, and nothing in the template marks which is "
          "meant -- the entire distinction lives in the prose.",
          "Shares the recurrent-slot property with "
          "graphtheory.enumeration.complete_graph_edge_count, and shares "
          "nothing else: one is a product, one a power, so the two members of "
          "this corpus's counting family cannot see each other."],
         [sym("t_n", "variable", "tree_count",
              "Number of labelled trees on n vertices.", 0),
          sym("n", "variable", "vertex_count",
              "Number of vertices, equivalently the size of the label set.", 0)],
         [EQ, POW, SUB],
         "There are exactly n^(n-2) different trees on a fixed set of n "
         "labelled vertices.",
         "A singleton at every level, and the honest report on prediction 4's "
         "wider question. The graph contains no other statement in which a slot "
         "occurs both as a base and as an exponent; the closest structures are "
         "the exponential family (`?0 = *(?1, EXP⟨*(?2, ?3)⟩)`, five members) "
         "and the power laws in geometry (`?0:V = *(?1:P, ^(?2:V, 2))`), and "
         "both keep base and exponent independent. That independence is exactly "
         "what a labelled-object count does not have. Attributed to Cayley "
         "(1889), proved earlier by Borchardt (1860) and stated by Sylvester "
         "(1857), which is itself a small lesson about provenance in a graph "
         "that records citation keys.",
         ["A fixed label set of size n at least one; the formula reads 1 at "
          "n = 1 and n = 2 by the usual conventions",
          "Labelled trees: two trees differing by a relabelling are counted "
          "separately",
          "Unrooted and undirected"],
         [CAYLEY1889, BORCHARDT1860, SYLVESTER1857, KIRCHHOFF1847, DIESTEL2017],
         disciplines=["graph_theory", "mathematics", "combinatorics"],
         failure_modes=[
             "Read as a count of tree SHAPES it is wildly wrong; unlabelled "
             "trees grow like C*alpha^n/n^(5/2) with no closed form.",
             "The n = 1 and n = 2 cases require the convention 1^(-1) = 1 and "
             "0^0-style edge handling; the formula is stated for n >= 1 by "
             "fiat rather than derived there.",
             "Kirchhoff's matrix-tree theorem is the real generalization, and "
             "reading Cayley's formula as the fundamental fact inverts the "
             "logical order."],
         inferential_links=links(
             composed_with=["graphtheory.trees.tree_edge_count",
                            "graphtheory.walks.adjacency_power_walk_count"]),
         keywords=["Cayley's formula", "labelled trees", "Pruefer sequence",
                   "matrix-tree theorem", "enumeration"],
         canonical_objects=["labelled tree", "label set", "Pruefer sequence"]),

    # ---------------------------------------------------------------- 7 ----
    node("graphtheory.walks.adjacency_power_walk_count",
         "Walks Counted by Powers of the Adjacency Matrix",
         "theorem", "formal", "algebraic_graph_theory", "spectral",
         "W = A^k,  W_ij = number of walks of length k from i to j",
         "(A^k)_{ij} = \\#\\{\\text{walks of length } k \\text{ from } i \\text{ to } j\\}",
         [{"form_id": "entrywise", "notation_system": "matrix_notation",
           "expression": "(A^k)_ij = sum over paths of prod of A entries",
           "scope_note": "The proof by induction made explicit: matrix multiplication IS the concatenation of walks, one term per intermediate vertex"},
          {"form_id": "closed_walks", "notation_system": "ascii",
           "expression": "TRACE(A^k) = sum_i EIGENVALUE_i^k",
           "scope_note": "Closed walks counted spectrally; this is where walk counting becomes the spectral theory of graphs"},
          {"form_id": "triangles", "notation_system": "ascii",
           "expression": "|{triangles}| = TRACE(A^3)/6",
           "scope_note": "The most-used instance: each triangle contributes six closed walks of length three"}],
         "opaque_binary_power",
         "WALKS = MATRIXPOWER(ADJACENCY, LENGTH)",
         [slot("WALKS", "variable", "walk_count_matrix"),
          slot("ADJACENCY", "variable", "adjacency_matrix"),
          slot("LENGTH", "index", "walk_length"),
          slot("MATRIXPOWER", "functional", "matrix_power")],
         ["MATRIXPOWER is an opaque call and the node says so. `^` in this "
          "grammar is scalar exponentiation over a base the canonicalizer may "
          "treat as a commutative factor; matrix multiplication is not "
          "commutative, so writing `ADJACENCY^LENGTH` would assert something "
          "false about the algebra.",
          "The price is total: the mechanism -- that the (i,j) entry "
          "accumulates exactly one term per walk, because matrix "
          "multiplication sums over intermediate vertices -- is invisible. What "
          "survives in the template is only the dependency of the walk count on "
          "the adjacency structure and the length.",
          "The statement is an identification of two objects (a matrix power "
          "and a table of counts), not a numeric identity, which is why every "
          "slot is a matrix or an index and none is a scalar.",
          "The length slot is an index, not a parameter: it ranges over "
          "non-negative integers and indexes a family of statements rather than "
          "tuning one."],
         [sym("A", "variable", "adjacency_matrix",
              "Adjacency matrix of the graph.", 2),
          sym("W", "variable", "walk_count_matrix",
              "Matrix whose (i,j) entry counts walks of the given length.", 2),
          sym("k", "index", "walk_length", "Walk length; a non-negative integer.", 0)],
         [EQ],
         "The k-th power of a graph's adjacency matrix has, in each entry, the "
         "number of walks of length k between the corresponding vertices.",
         "The sixth head in the graph carrying the two-argument "
         "opaque-composition shape `?0 = HEAD⟨?1, ?2⟩`, after "
         "morphology's CONCAT and REALIZE, information theory's CAPMAX, "
         "geospatial topology's MEET and machine learning's UPDATE. Six nodes, "
         "six heads, zero groups at shape, typed or family level. "
         "docs/BACKLOG.md proposed that count as the cheapest available "
         "measurement of what head literalism costs; it grows by one every time "
         "a corpus needs a vocabulary the graph does not have, and this seeding "
         "pass adds a seventh independently "
         "(`geomodel.surfaces.surface_normal_cross_product`, CROSS). The other "
         "half of the cost is specific to this node: because the head is "
         "opaque, the statement's relationship to "
         "`graphtheory.degree.handshake_lemma` -- walks of length one are edges, "
         "counted twice -- and to the whole weighted-sum family (a matrix "
         "product IS a sum of products) cannot be seen. An honest opaque call "
         "records a dependency and hides a derivation.",
         ["A finite graph with a fixed vertex ordering, so that the adjacency "
          "matrix is defined",
          "Walks, not paths: repeated vertices and repeated edges are allowed, "
          "and this is what makes the count multiplicative",
          "Non-negative integer length; A^0 is the identity, correctly counting "
          "the empty walk",
          "Works verbatim for digraphs and for weighted graphs, where the "
          "entries become path weights rather than counts"],
         [BIGGS1993, CVETKOVIC1980, WEST2001],
         disciplines=["graph_theory", "mathematics", "linear_algebra"],
         functionals=[MATRIXPOWER_FN],
         failure_modes=[
             "Walk counts are not path counts; using A^k to count simple paths "
             "overcounts badly, and counting simple paths is #P-hard.",
             "Entries grow like the spectral radius to the k, so direct "
             "computation overflows quickly and the practical route is "
             "spectral.",
             "For a weighted graph the entries are sums of products of weights, "
             "not counts, and the theorem's name misleads."],
         inferential_links=links(
             composed_with=["graphtheory.degree.handshake_lemma",
                            "graphtheory.enumeration.cayley_formula"]),
         keywords=["adjacency matrix", "walk counting", "matrix power",
                   "algebraic graph theory", "spectral graph theory",
                   "opaque head"],
         canonical_objects=["adjacency matrix", "walk", "matrix power"]),

    # ---------------------------------------------------------------- 8 ----
    node("graphtheory.planarity.planar_edge_bound",
         "Edge Bound for Simple Planar Graphs",
         "corollary", "derived", "planarity", "extremal",
         "|E| <= 3*|V| - 6",
         "\\lvert E\\rvert \\le 3\\lvert V\\rvert - 6",
         [{"form_id": "from_euler", "notation_system": "ascii",
           "expression": "|V| - |E| + |F| = 2  AND  2*|E| >= 3*|F|",
           "scope_note": "The derivation in two steps: Euler's formula, plus the face-degree count (every face is bounded by at least three edges, every edge borders at most two faces)"},
          {"form_id": "triangle_free", "notation_system": "ascii",
           "expression": "|E| <= 2*|V| - 4",
           "scope_note": "Bipartite or triangle-free planar graphs: every face has at least four sides, and the constants change accordingly"},
          {"form_id": "nonplanarity_certificate", "notation_system": "ascii",
           "expression": "K_5 has |E| = 10 > 9 = 3*5 - 6",
           "scope_note": "What the bound is for: violating it certifies non-planarity, and K_5 is the smallest witness"}],
         "linear_extremal_bound",
         "EDGES <= 3*VERTICES - 6",
         [slot("EDGES", "variable", "edge_count"),
          slot("VERTICES", "variable", "vertex_count")],
         ["Both literals descend from geometry: the 3 is the minimum number of "
          "sides of a face, the 6 is twice the Euler characteristic of the "
          "sphere. Neither is a fitted constant, and the triangle-free variant "
          "(2 and 4) shows exactly how they move when the face-degree "
          "hypothesis changes.",
          "The relation is `<=`, and it is one of only three inequalities in "
          "the graph. Unlike numanalysis.floatingpoint.machine_epsilon_bound "
          "this one is EXTREMAL rather than approximate: equality holds for "
          "every maximal planar graph, so the bound is attained rather than "
          "merely respected.",
          "The bound is linear in the vertex count while "
          "graphtheory.enumeration.complete_graph_edge_count is quadratic. "
          "Placing the two side by side is the proof that K_n is non-planar for "
          "n at least five, and the graph holds both statements without being "
          "able to combine them.",
          "Derived from Euler's polyhedron formula, which the graph already "
          "carries as geotop.polyhedra.euler_polyhedron_formula. The link is a "
          "one-sided composed_with, since the derivation needs an inequality "
          "about face degrees that has no node."],
         [sym("E", "variable", "edge_count", "Number of edges.", 0),
          sym("V", "variable", "vertex_count", "Number of vertices.", 0)],
         [LEQ, MUL, SUB],
         "A simple graph that can be drawn in the plane without crossings has "
         "at most 3n - 6 edges, so planar graphs are sparse.",
         "A singleton, expected. Recorded for two reasons beyond its own "
         "content. First, it is this seeding pass's second inequality, and both "
         "are isolated for the same mechanical reason -- the relation symbol is "
         "part of the skeleton -- while being completely different kinds of "
         "claim: a rounding bound that is never attained and an extremal bound "
         "that is attained by a whole family. The graph cannot distinguish "
         "them. Second, it carries the corpus's link to "
         "`geotop.polyhedra.euler_polyhedron_formula`, the node this seeding "
         "pass was explicitly instructed not to duplicate. Two of the eight "
         "graph-theory nodes point at it (`tree_edge_count` is Euler's formula "
         "with one face, this one is derived from it), and in both cases the "
         "relationship is real and unrepresentable: one is a suppressed "
         "specialization, the other needs a premise that is not in the graph.",
         ["A simple graph: no loops, no multi-edges",
          "At least three vertices; the bound is false for n = 1, 2",
          "Planar, i.e. embeddable in the sphere or the plane without crossings",
          "Equality exactly for maximal planar graphs, whose faces are all "
          "triangles"],
         [EULER1758, KURATOWSKI1930, DIESTEL2017, BONDY2008],
         disciplines=["graph_theory", "mathematics", "topology"],
         failure_modes=[
             "The converse fails: satisfying the bound does not make a graph "
             "planar, and K_(3,3) with 9 edges on 6 vertices is the standard "
             "counterexample (9 <= 12).",
             "Multi-edges and loops break it immediately, which is why the "
             "simplicity hypothesis is doing more work than it appears to.",
             "Applied to a graph on one or two vertices the right-hand side is "
             "negative, so the small cases must be excluded by hand rather "
             "than being degenerate instances."],
         inferential_links=links(
             composed_with=["geotop.polyhedra.euler_polyhedron_formula",
                            "graphtheory.enumeration.complete_graph_edge_count",
                            "graphtheory.degree.handshake_lemma"]),
         keywords=["planar graph", "Euler formula", "edge bound", "K_5",
                   "Kuratowski", "extremal", "sparsity"],
         canonical_objects=["planar embedding", "face", "edge set"]),
]


# --------------------------------------------------------------------------
# Corpus 3: geometric modeling
# --------------------------------------------------------------------------

GEOMODEL = [

    # ---------------------------------------------------------------- 1 ----
    node("geomodel.bezier.bernstein_bezier_evaluation",
         "Bezier Curve as a Bernstein-Weighted Sum of Control Points",
         "definition", "formal", "curves_and_surfaces", "bezier_representation",
         "P(t) = sum_(i=0)^(n) B_i(t) * C_i",
         "P(t) = \\sum_{i=0}^{n} B_i^n(t)\\, C_i",
         [{"form_id": "bernstein_basis", "notation_system": "ascii",
           "expression": "B_i(t) = C(n,i) * t^i * (1-t)^(n-i)",
           "scope_note": "What the weight slot stands for. The grammar has no binomial coefficient, so the basis is a parameter slot and this expansion lives here"},
          {"form_id": "partition_of_unity", "notation_system": "ascii",
           "expression": "sum_i B_i(t) = 1,  B_i(t) >= 0 on [0,1]",
           "scope_note": "The two properties that make the sum an affine and in fact convex combination: the curve lies in the convex hull of its control polygon"},
          {"form_id": "matrix_form", "notation_system": "matrix_notation",
           "expression": "P(t) = TVEC(t) * M * CVEC",
           "scope_note": "The power-basis factorization used in graphics pipelines; numerically worse and computationally cheaper"},
          {"form_id": "degree_one", "notation_system": "vector_notation",
           "expression": "P(t) = (1-t)*C_0 + t*C_1",
           "scope_note": "The n = 1 case, which is geomodel.bezier.de_casteljau_step and numanalysis.interpolation.linear_interpolation"}],
         "weighted_accumulation",
         "POINT = sum_i BASIS_i*CONTROL_i",
         [slot("POINT", "variable", "curve_point"),
          slot("BASIS_i", "parameter", "basis_weight"),
          slot("CONTROL_i", "variable", "control_point")],
         ["The Bernstein basis is a PARAMETER slot, not an expanded "
          "polynomial. That is a deliberate authoring choice: the grammar has "
          "no binomial coefficient, and more importantly the statement being "
          "made is 'a curve point is a weighted accumulation of control "
          "points', with the identity of the weights a separate matter. "
          "Expanding the basis would have produced a singleton and lost the "
          "statement.",
          "The weights sum to one and are non-negative on [0,1]. Neither fact "
          "is in the template -- the first is a companion node "
          "(geomodel.barycentric.barycentric_partition_of_unity has the same "
          "shape for a different family), the second has no expressible form -- "
          "and together they are what make the curve lie inside its control "
          "polygon's convex hull.",
          "Control points are variable-like, weights parameter-like: the "
          "designer moves the points, the parameterization supplies the "
          "weights. That split is the entire user interface of computer-aided "
          "design, and it is visible in the slot categories.",
          "Affine invariance follows from the weights summing to one: "
          "transforming the control points and then evaluating gives the same "
          "curve as evaluating and then transforming. This is why "
          "geomodel.transforms.homogeneous_rigid_transform can be applied to "
          "control polygons rather than to sampled curves, and it is the same "
          "translation-invariance property that "
          "numanalysis.interpolation.linear_interpolation records."],
         [sym("P", "variable", "curve_point",
              "Point on the curve at parameter t.", 1),
          sym("C_i", "variable", "control_point",
              "The i-th control point of the curve.", 1),
          sym("B_i", "parameter", "basis_weight",
              "Value of the i-th Bernstein basis polynomial at t.", 0),
          sym("t", "index", "curve_parameter",
              "Curve parameter, conventionally in [0,1].", 0),
          sym("n", "index", "curve_degree", "Degree of the curve.", 0)],
         [EQ, MUL, SUM],
         "A Bezier curve's point at a given parameter is a weighted average of "
         "its control points, the weights being the Bernstein polynomials.",
         "Prediction 3, and it FIRED -- the best result of this seeding pass. "
         "`?0:V = sum⟨*(?1:P, ?2:V)⟩` previously held two members and now holds "
         "FOUR, in four disciplines: this node (geometric modeling), "
         "`geomodel.barycentric.barycentric_point_reconstruction` (also "
         "geometric modeling, and a genuinely different statement), "
         "`probstat.probability.total_probability_partition` (statistics) and "
         "`algtop.homology.betti_alternating_sum` (algebraic topology). What "
         "they share is exact and not superficial: a variable quantity is read "
         "off as a parameter-weighted accumulation of variable parts, and in "
         "three of the four the weights sum to one -- Bernstein basis "
         "polynomials, barycentric coordinates, and the probabilities of a "
         "partition. The topology member is the informative exception: its "
         "weights are the alternating signs, which sum to zero or one depending "
         "on parity, and that is why an Euler characteristic can be negative "
         "while a probability cannot. Bernstein's own 1912 proof of the "
         "Weierstrass approximation theorem was probabilistic -- the basis "
         "polynomials ARE binomial probabilities -- so the twin with the law of "
         "total probability is not an analogy the matcher stumbled into; it is "
         "the theorem's original derivation, recovered from structure alone.",
         ["Parameter conventionally in [0,1]; outside it the same formula "
          "extrapolates and loses the convex-hull property",
          "A fixed number of control points, one per basis function",
          "Control points in an affine space, so that weighted combinations "
          "with weights summing to one are well defined",
          "The weights are the degree-n Bernstein polynomials; other weight "
          "families give B-splines, NURBS and box splines, with the same "
          "template"],
         [BERNSTEIN1912, BEZIER1972, DECASTELJAU1963, FARIN2002, PRAUTZSCH2002],
         disciplines=["geometric_modeling", "mathematics", "computer_graphics"],
         index_sets=[IDX_CONTROL],
         failure_modes=[
             "Every control point influences every parameter value, so Bezier "
             "curves have no local control; moving one point changes the whole "
             "curve, which is the defect B-splines exist to fix.",
             "Evaluating the basis directly from the binomial formula loses "
             "accuracy for high degree; de Casteljau's recursive scheme is "
             "backward stable and the closed form is not.",
             "The curve interpolates only its first and last control points. "
             "Reading the control polygon as data the curve passes through is "
             "the commonest beginner error and is wrong for every interior "
             "point."],
         inferential_links=links(
             generalizes=["geomodel.bezier.de_casteljau_step"],
             composed_with=["probstat.probability.total_probability_partition",
                            "algtop.homology.betti_alternating_sum",
                            "geomodel.barycentric.barycentric_partition_of_unity"]),
         keywords=["Bezier curve", "Bernstein polynomial", "control point",
                   "weighted sum", "convex hull", "CAGD"],
         canonical_objects=["control polygon", "basis polynomial", "curve point"]),

    # ---------------------------------------------------------------- 2 ----
    node("geomodel.bezier.de_casteljau_step",
         "de Casteljau Interpolation Step",
         "definition", "formal", "curves_and_surfaces", "subdivision",
         "P_i^(r) = (1 - t)*P_i^(r-1) + t*P_(i+1)^(r-1)",
         "P_i^{(r)} = (1-t)\\,P_i^{(r-1)} + t\\,P_{i+1}^{(r-1)}",
         [{"form_id": "one_level", "notation_system": "vector_notation",
           "expression": "Q = (1 - t)*A + t*B",
           "scope_note": "One step stripped of indices: the point a fraction t along the segment AB. This is the template"},
          {"form_id": "recursive_scheme", "notation_system": "ascii",
           "expression": "apply the step to every adjacent pair, n times; the single survivor is P(t)",
           "scope_note": "The full algorithm. Repeated affine interpolation on the control polygon evaluates the Bernstein sum, which is the theorem the step exists for"},
          {"form_id": "subdivision", "notation_system": "ascii",
           "expression": "the two outer edges of the triangular scheme are the control polygons of the two halves",
           "scope_note": "Why the algorithm matters beyond evaluation: it splits a curve at t for free, which is the basis of rendering by recursive subdivision"}],
         "two_point_convex_combination",
         "INTERMEDIATE = (1 - PARAM)*LEFT + PARAM*RIGHT",
         [slot("INTERMEDIATE", "variable", "interpolated_point"),
          slot("PARAM", "parameter", "curve_parameter"),
          slot("LEFT", "variable", "left_point"),
          slot("RIGHT", "variable", "right_point")],
         ["This IS linear interpolation, and the corpus records it as such "
          "rather than pretending otherwise: reciprocal `equivalent_to` edges "
          "join it to numanalysis.interpolation.linear_interpolation and the "
          "two templates are identical up to slot naming. The de Casteljau "
          "algorithm's content is not this step, it is that ITERATING this step "
          "on a control polygon evaluates a degree-n Bernstein sum -- and that "
          "content is not in the template, because the grammar has no "
          "recursion.",
          "It is also the degree-one case of "
          "geomodel.bezier.bernstein_bezier_evaluation, since the degree-one "
          "Bernstein polynomials are exactly (1-t) and t. Recorded as a "
          "reciprocal special_case_of / generalizes pair; the matcher cannot "
          "derive it, because collapsing an indexed sum to two explicit terms "
          "is a rewrite rather than a slot binding -- the same class "
          "docs/BACKLOG.md records for uniform versus Shannon entropy.",
          "Every point produced lies on the segment between its two inputs, so "
          "the whole scheme stays inside the convex hull of the control "
          "polygon. That is the geometric fact the algorithm's numerical "
          "stability rests on, and it follows from the weights being "
          "non-negative and summing to one.",
          "The parameter slot occurs twice, once bare and once inside "
          "`1 - PARAM`. Same structure, and same consequence, as the "
          "interpolation node: it cannot reach the affine family."],
         [sym("Q", "variable", "interpolated_point",
              "Point produced by one interpolation step.", 1),
          sym("A", "variable", "left_point",
              "First input point of the step.", 1),
          sym("B", "variable", "right_point",
              "Second input point of the step.", 1),
          sym("t", "parameter", "curve_parameter",
              "Curve parameter at which the curve is being evaluated.", 0),
          sym("r", "index", "level_index",
              "Level of the triangular scheme.", 0)],
         [EQ, ADD, SUB, MUL],
         "One step of de Casteljau's algorithm takes two neighbouring points "
         "and returns the point a fraction t of the way between them.",
         "Authored as an honest duplicate, which is a claim worth defending. "
         "The instruction that produced this corpus asked for de Casteljau to "
         "be recorded as a special case or an equivalent of linear "
         "interpolation rather than dressed up as something new, and both edges "
         "turned out to be true simultaneously: it is EQUIVALENT to "
         "`numanalysis.interpolation.linear_interpolation` (same statement, "
         "different discipline's name for it) and a SPECIAL CASE OF "
         "`geomodel.bezier.bernstein_bezier_evaluation` (the degree-one "
         "instance). The matcher confirms only the first -- the two "
         "interpolation nodes typed-twin each other, forming this pass's one "
         "wholly internal twin group -- and cannot confirm the second. That "
         "asymmetry is the finding: a twin group and a suppressed "
         "specialization can attach to the same node, and only one of them is "
         "machine-checkable. Both remain isolated from the affine family for "
         "the reason recorded on the interpolation node.",
         ["Points in an affine space",
          "Parameter in [0,1] for the convex-hull guarantee; outside it the "
          "step still computes but leaves the segment",
          "The full algorithm requires the step applied n levels deep for a "
          "degree-n curve"],
         [DECASTELJAU1963, BEZIER1972, FARIN2002, PRAUTZSCH2002],
         disciplines=["geometric_modeling", "mathematics", "computer_graphics"],
         failure_modes=[
             "Quadratic in the degree, where the matrix form is linear; the "
             "stability is bought with work, and for low degrees in graphics "
             "the trade often goes the other way.",
             "Naming the step after the algorithm invites the reading that "
             "something curve-specific happens in it. Nothing does: the step is "
             "a straight-line interpolation, and the curve emerges only from "
             "the repetition."],
         inferential_links=links(
             equivalent_to=["numanalysis.interpolation.linear_interpolation"],
             special_case_of=["geomodel.bezier.bernstein_bezier_evaluation"],
             composed_with=["geomodel.barycentric.barycentric_point_reconstruction"]),
         keywords=["de Casteljau", "subdivision", "linear interpolation",
                   "Bezier", "convex hull", "numerical stability"],
         canonical_objects=["control polygon", "interpolation step",
                            "triangular scheme"]),

    # ---------------------------------------------------------------- 3 ----
    node("geomodel.barycentric.barycentric_partition_of_unity",
         "Barycentric Coordinates Sum to One",
         "definition", "formal", "affine_geometry", "barycentric_coordinates",
         "sum_(i=0)^(d) lambda_i = 1",
         "\\sum_{i=0}^{d} \\lambda_i = 1",
         [{"form_id": "with_positivity", "notation_system": "ascii",
           "expression": "sum_i lambda_i = 1  AND  lambda_i >= 0",
           "scope_note": "Adding non-negativity restricts the point to the closed simplex; without it the coordinates describe the whole affine hull"},
          {"form_id": "areal", "notation_system": "ascii",
           "expression": "lambda_i = AREA(subtriangle_i)/AREA(triangle)",
           "scope_note": "Moebius's original reading in the plane: the coordinates are area ratios, which is why they sum to one"},
          {"form_id": "probability_analogue", "notation_system": "event_probability",
           "expression": "sum_i p_i = 1",
           "scope_note": "The discrete normalization axiom. Identical structure, different subject; the graph carries no node for it, so no twin exists to find"}],
         "normalized_weight_sum",
         "sum_i BARY_i = 1",
         [slot("BARY_i", "parameter", "barycentric_coordinate")],
         ["A one-slot template, and the smallest statement in the three "
          "corpora. Everything it says is in the relation: an indexed family of "
          "weights accumulates to the multiplicative unit.",
          "The coordinates are parameter-like because they describe WHERE in "
          "the simplex a point lies -- they are the coordinates, not the "
          "geometry. Making them variable-like would state something about a "
          "moving family rather than about a coordinate system.",
          "This is the affine-ness condition. Together with "
          "geomodel.barycentric.barycentric_point_reconstruction it says the "
          "point is an affine combination of the vertices, which is exactly "
          "what makes barycentric coordinates independent of any origin -- "
          "Moebius's point in introducing them in 1827.",
          "Non-negativity is a separate condition and is not here; with it the "
          "point is in the simplex, without it merely in its affine hull. The "
          "grammar has no way to attach a sign constraint to an indexed family."],
         [sym("lambda_i", "parameter", "barycentric_coordinate",
              "The i-th barycentric coordinate of a point with respect to a "
              "simplex.", 0),
          sym("d", "index", "simplex_dimension",
              "Dimension of the simplex; there are d+1 coordinates.", 0)],
         [EQ, SUM],
         "The barycentric coordinates of a point with respect to a simplex add "
         "up to one.",
         "A singleton, and the interesting part is what it ALMOST meets. Its "
         "skeleton is `1 = sum⟨?0:P⟩`. The discrete probability normalization "
         "axiom `sum_i p_i = 1` is character for character the same statement "
         "about a different subject, and the graph does not contain it -- "
         "`data/statistics` carries the law of total probability, Bayes's rule "
         "and the CLT, but not normalization. So this node's most natural twin "
         "is absent for the same reason prediction 2's mixture comparison could "
         "not be run: a gap in the corpus, not a limit of the matcher. "
         "docs/BACKLOG.md separately records that probability normalization has "
         "a continuous form (`INTEGRAL(density) = 1`) that could never twin the "
         "discrete one anyway, so the missing node would arrive already split "
         "in two. Recorded as a concrete, cheap, high-value corpus addition: "
         "one node in `data/statistics` would create a cross-discipline twin "
         "with this one and, with a two-component mixture, a second with "
         "linear interpolation.",
         ["A non-degenerate simplex, so that the coordinates are unique",
          "Coordinates taken with respect to a fixed vertex ordering",
          "Non-negativity is NOT assumed here; it is the extra condition that "
          "confines the point to the simplex"],
         [MOBIUS1827, FARIN2002, DOCARMO1976],
         disciplines=["geometric_modeling", "mathematics", "computer_graphics"],
         index_sets=[IDX_SIMPLEX],
         failure_modes=[
             "For a degenerate simplex the coordinates are not unique and the "
             "constraint no longer pins a point; interpolation code that does "
             "not check for degeneracy divides by a vanishing area.",
             "In floating point the computed coordinates sum to one only to "
             "within rounding, so tests of the form 'is the point inside' must "
             "use a tolerance -- the constraint that defines the object cannot "
             "be checked exactly on the machine that uses it."],
         inferential_links=links(
             composed_with=["geomodel.barycentric.barycentric_point_reconstruction",
                            "geomodel.bezier.bernstein_bezier_evaluation"]),
         keywords=["barycentric coordinates", "partition of unity", "simplex",
                   "affine combination", "Moebius", "normalization"],
         canonical_objects=["simplex", "barycentric coordinate", "affine hull"]),

    # ---------------------------------------------------------------- 4 ----
    node("geomodel.barycentric.barycentric_point_reconstruction",
         "Point Recovered from Barycentric Coordinates",
         "definition", "formal", "affine_geometry", "barycentric_coordinates",
         "P = sum_(i=0)^(d) lambda_i * V_i",
         "P = \\sum_{i=0}^{d} \\lambda_i V_i",
         [{"form_id": "triangle", "notation_system": "vector_notation",
           "expression": "P = lambda_0*V_0 + lambda_1*V_1 + lambda_2*V_2",
           "scope_note": "The planar case used in every rasterizer and every finite-element shape function"},
          {"form_id": "centroid", "notation_system": "ascii",
           "expression": "P = (1/(d+1)) * sum_i V_i",
           "scope_note": "Equal coordinates give the centroid -- the barycentre the coordinates are named for"},
          {"form_id": "interpolant", "notation_system": "ascii",
           "expression": "f(P) = sum_i lambda_i * f(V_i)",
           "scope_note": "The same weights applied to sampled values rather than positions: linear interpolation over a triangle, the P1 finite element"}],
         "weighted_accumulation",
         "POINT = sum_i BARY_i*VERTEX_i",
         [slot("POINT", "variable", "reconstructed_point"),
          slot("BARY_i", "parameter", "barycentric_coordinate"),
          slot("VERTEX_i", "variable", "simplex_vertex")],
         ["Same template as geomodel.bezier.bernstein_bezier_evaluation and a "
          "different statement: there the weights are polynomials in a curve "
          "parameter and the summands are designer-chosen control points, here "
          "the weights are a point's coordinates and the summands are the "
          "vertices of a fixed simplex. Two statements can share a skeleton and "
          "not be the same claim, which docs/BACKLOG.md notes the "
          "archetype-drift lint cannot currently distinguish; both nodes "
          "deliberately carry the archetype `weighted_accumulation` because in "
          "this case the shared structure is the point.",
          "The weights are exactly the family constrained by "
          "geomodel.barycentric.barycentric_partition_of_unity. Split across "
          "two nodes because they are two statements, and the grammar has no "
          "conjunction to join them; together they define an affine "
          "combination.",
          "Vertices are variable-like, coordinates parameter-like -- the same "
          "split as the Bezier node, and the reason both land in the same typed "
          "group rather than only in the untyped one.",
          "Because the coordinates sum to one, the reconstruction commutes with "
          "any affine map of the ambient space. That is what makes barycentric "
          "coordinates coordinates: they are attached to the simplex, not to "
          "the space."],
         [sym("P", "variable", "reconstructed_point",
              "The point described by the coordinates.", 1),
          sym("V_i", "variable", "simplex_vertex",
              "The i-th vertex of the simplex.", 1),
          sym("lambda_i", "parameter", "barycentric_coordinate",
              "The i-th barycentric coordinate.", 0),
          sym("d", "index", "simplex_dimension", "Dimension of the simplex.", 0)],
         [EQ, MUL, SUM],
         "A point is recovered from its barycentric coordinates as the "
         "coordinate-weighted sum of the simplex's vertices.",
         "The fourth member of the weighted-sum family, and the one that makes "
         "the group cross four disciplines: with "
         "`geomodel.bezier.bernstein_bezier_evaluation`, "
         "`probstat.probability.total_probability_partition` and "
         "`algtop.homology.betti_alternating_sum` it shares "
         "`?0:V = sum⟨*(?1:P, ?2:V)⟩` exactly. The four-way group is the "
         "strongest result of this seeding pass and it is also the one most "
         "exposed to the objection that shared structure is not shared "
         "meaning -- so the objection is worth answering here rather than "
         "deflecting. The four statements agree on this much and no more: a "
         "quantity is DEFINED as an accumulation over an index set, of parts "
         "weighted by numbers the statement does not otherwise constrain. What "
         "differs is what constrains the weights, and that constraint lives in "
         "a separate node (partition of unity here, the Bernstein basis in "
         "Bezier, a probability distribution in statistics, alternating signs "
         "in topology). The matcher is therefore reporting the accumulation and "
         "silently dropping the normalization, which is exactly why this corpus "
         "authors the partition-of-unity constraint as its own node instead of "
         "trusting the group to imply it.",
         ["A non-degenerate simplex with a fixed vertex ordering",
          "Coordinates summing to one, which is the companion node's statement",
          "An affine space; no origin is needed and none may be assumed",
          "Non-negative coordinates if the point is required to lie inside"],
         [MOBIUS1827, FARIN2002, PRAUTZSCH2002],
         disciplines=["geometric_modeling", "mathematics", "computer_graphics"],
         index_sets=[IDX_SIMPLEX],
         failure_modes=[
             "Without the sum-to-one constraint the same expression is an "
             "arbitrary linear combination and depends on the choice of origin; "
             "the two nodes are only jointly meaningful.",
             "Perspective-correct interpolation in a rasterizer requires "
             "dividing by the interpolated reciprocal depth; applying this "
             "formula directly in screen space is the classic affine-texturing "
             "artefact.",
             "Coordinates computed from areas lose precision for slivers, so "
             "the reconstruction is least accurate exactly where triangles are "
             "worst conditioned."],
         inferential_links=links(
             composed_with=["geomodel.barycentric.barycentric_partition_of_unity",
                            "geomodel.bezier.bernstein_bezier_evaluation",
                            "geomodel.bezier.de_casteljau_step"]),
         keywords=["barycentric coordinates", "simplex", "affine combination",
                   "weighted sum", "shape function", "rasterization"],
         canonical_objects=["simplex", "vertex", "interior point"]),

    # ---------------------------------------------------------------- 5 ----
    node("geomodel.transforms.homogeneous_rigid_transform",
         "Rigid Transform of a Point (Rotation then Translation)",
         "transformation", "formal", "transformations", "rigid_motion",
         "p' = R*p + t",
         "p' = R\\,p + t",
         [{"form_id": "homogeneous", "notation_system": "matrix_notation",
           "expression": "PHOM' = M * PHOM,  M = [[R, t],[0, 1]]",
           "scope_note": "The homogeneous 4x4 form: the whole point of homogeneous coordinates is that this turns an affine map into a linear one, so transforms compose by matrix multiplication"},
          {"form_id": "per_coordinate", "notation_system": "ascii",
           "expression": "p'_j = sum_k R_jk * p_k + t_j",
           "scope_note": "Coordinatewise. In this form every product is a product of scalars, which is the reading under which the template's commutative `*` is literally true"},
          {"form_id": "composition", "notation_system": "matrix_notation",
           "expression": "(R_2, t_2) o (R_1, t_1) = (R_2*R_1, R_2*t_1 + t_2)",
           "scope_note": "The group law of SE(3). Composition is where non-commutativity becomes unavoidable, and no template in this grammar can state it"},
          {"form_id": "inverse", "notation_system": "matrix_notation",
           "expression": "p = TRANSPOSE(R)*(p' - t)",
           "scope_note": "The inverse motion; the transpose stands in for the inverse because R is orthogonal, which the template cannot record"}],
         "affine_operator",
         "POINTNEW = ROTATION*POINT + TRANSLATION",
         [slot("POINTNEW", "variable", "transformed_point"),
          slot("ROTATION", "parameter", "rotation_operator"),
          slot("POINT", "variable", "source_point"),
          slot("TRANSLATION", "parameter", "translation_vector")],
         ["The `*` here is matrix-vector application, which does not commute, "
          "while the canonicalizer flattens and SORTS `*` -- i.e. asserts "
          "commutativity. The node is written anyway, with the escape declared: "
          "in the per-coordinate form (see equivalent_forms) every factor is a "
          "scalar and the template is literally true. This is the same escape "
          "`ml.recurrence.linear_ssm_state_update` takes via a diagonal state "
          "matrix, and it is not available to "
          "`ml.recurrence.mlstm_matrix_memory_update`, which had to introduce "
          "an OUTER head instead. Recorded so the reader knows the choice was "
          "made and why.",
          "Rotation and translation are both PARAMETER-like: they describe the "
          "motion, which is fixed while it is applied to many points. The point "
          "is variable-like. That split is what puts this node in the affine "
          "family rather than in the state-recurrence family.",
          "Orthogonality of the rotation (six constraints on nine numbers, plus "
          "a determinant of +1) is the entire difference between a rigid motion "
          "and a general affine map, and none of it is expressible. The "
          "template describes the affine map; the constraint lives in "
          "regularity_conditions, and in "
          "geomodel.quaternions.unit_quaternion_constraint, which states the "
          "unit-norm condition for the three-dimensional rotation case only.",
          "Order matters: rotate, then translate. The reverse order is a "
          "different motion with translation R*t, and the template cannot "
          "record that either, since `+` is commutative here."],
         [sym("p", "variable", "source_point",
              "Point in the source frame.", 1),
          sym("pprime", "variable", "transformed_point",
              "Its image in the target frame.", 1),
          sym("R", "parameter", "rotation_operator",
              "Rotation matrix; orthogonal with determinant one.", 2),
          sym("t", "parameter", "translation_vector",
              "Translation vector of the motion.", 1)],
         [EQ, ADD, MUL],
         "A rigid motion sends a point to its rotated image displaced by a "
         "fixed translation.",
         "Prediction 6 said this would typed-twin "
         "`ml.recurrence.linear_ssm_state_update`, 'both P*V + P*V shapes'. The "
         "matcher says the premise was wrong, and it is right. A rigid "
         "transform is P*V + P: the translation is a bare parameter, not a "
         "parameter times a variable, because a translation does not scale "
         "anything. So the SSM comparison MISSES -- "
         "`?0:V = +(*(?1:P, ?2:V), *(?3:P, ?4:V))` has one more product node "
         "than this statement has -- and what FIRES instead is the AFFINE "
         "FAMILY: `?0:V = +(?1:P, *(?2:P, ?3:V))`, joining "
         "`calculus.approximation.tangent_line_linearization`, "
         "`economics.finance.capm_expected_return`, "
         "`economics.macroeconomics.keynesian_consumption_function` and "
         "`probstat.transform.affine_location_scale`, making a five-member "
         "group across five disciplines. That is the correct answer and a "
         "better one than the prediction: a rigid motion is the canonical "
         "affine map, the object the affine family is named after, and the "
         "graph's four existing members are all one-dimensional shadows of it. "
         "Worth recording as the pass's clearest case of the tool correcting "
         "the author rather than confirming him -- the registered prediction "
         "named the right neighbourhood and the wrong neighbour.",
         ["R orthogonal with determinant +1, so the motion preserves distances "
          "and orientation",
          "Point and translation in the same coordinate frame",
          "Rotate first, then translate; the opposite convention is a different "
          "map",
          "The per-coordinate reading is the one under which the commutative "
          "`*` of the template is exact"],
         [DENAVIT1955, ROBERTS1965, FOLEY1990, SHOEMAKE1985],
         disciplines=["geometric_modeling", "robotics", "computer_graphics"],
         failure_modes=[
             "Repeated composition of floating-point rotation matrices drifts "
             "off the orthogonal group; without periodic re-orthonormalization "
             "the 'rigid' motion starts shearing.",
             "Interpolating rotation matrices entrywise leaves SO(3) entirely, "
             "which is the practical reason quaternions and their unit-norm "
             "constraint are used instead.",
             "The template's `+` invites reading rotation and translation as "
             "independent contributions; they are not, since composing two "
             "motions mixes them (see the group law)."],
         inferential_links=links(
             composed_with=["probstat.transform.affine_location_scale",
                            "ml.recurrence.linear_ssm_state_update",
                            "geomodel.quaternions.unit_quaternion_constraint",
                            "geomodel.bezier.bernstein_bezier_evaluation"]),
         keywords=["rigid transform", "SE(3)", "homogeneous coordinates",
                   "rotation matrix", "affine map", "robotics"],
         canonical_objects=["rotation matrix", "translation vector", "point"]),

    # ---------------------------------------------------------------- 6 ----
    node("geomodel.surfaces.surface_normal_cross_product",
         "Surface Normal from the Tangent Cross Product",
         "definition", "formal", "surfaces", "differential_geometry",
         "N = CROSS(dS/du, dS/dv)",
         "N = \\frac{\\partial S}{\\partial u} \\times \\frac{\\partial S}{\\partial v}",
         [{"form_id": "unit_normal", "notation_system": "vector_notation",
           "expression": "nhat = CROSS(Su, Sv) / NORM(CROSS(Su, Sv))",
           "scope_note": "Normalized; the direction is the content, the magnitude is the area element"},
          {"form_id": "area_element", "notation_system": "ascii",
           "expression": "dA = NORM(CROSS(Su, Sv)) * du * dv",
           "scope_note": "The magnitude's meaning: the cross product's length is the area of the parallelogram the tangents span, which is how surface integrals are computed"},
          {"form_id": "triangle_mesh", "notation_system": "vector_notation",
           "expression": "N = CROSS(V1 - V0, V2 - V0)",
           "scope_note": "The discrete case used in every renderer; two edge vectors of a triangle stand in for the tangent vectors"}],
         "opaque_binary_composition",
         "NORMAL = CROSS(TANGENTU, TANGENTV)",
         [slot("NORMAL", "variable", "surface_normal"),
          slot("TANGENTU", "variable", "first_tangent"),
          slot("TANGENTV", "variable", "second_tangent"),
          slot("CROSS", "functional", "cross_product")],
         ["CROSS is an opaque call because the grammar has no antisymmetric "
          "binary operator. Using `*` would be worse than imprecise: the "
          "canonicalizer sorts the arguments of `*`, which would assert "
          "CROSS(a,b) = CROSS(b,a), and the truth is CROSS(a,b) = -CROSS(b,a). "
          "Argument order here is not a convention to be fixed for the "
          "matcher's convenience, it is the surface's orientation, and swapping "
          "it turns the object inside out.",
          "The seventh head in the graph carrying `?0 = HEAD⟨?1, ?2⟩` -- after "
          "CONCAT, REALIZE, CAPMAX, MEET, UPDATE and this pass's own "
          "MATRIXPOWER -- and, like the other six, it twins none of them. Two "
          "of the seven arrived in this single seeding pass.",
          "The result is a vector orthogonal to both inputs, which is a "
          "statement about the codomain that the template cannot make. So is "
          "the fact that the construction only exists in three dimensions.",
          "Both tangent slots are variable-like: they vary over the surface, "
          "and so does the normal. Nothing here is chosen."],
         [sym("N", "variable", "surface_normal",
              "Normal vector at a point of the surface.", 1),
          sym("Su", "variable", "first_tangent",
              "Partial derivative of the parameterization in the first "
              "parameter.", 1),
          sym("Sv", "variable", "second_tangent",
              "Partial derivative in the second parameter.", 1)],
         [EQ],
         "The normal direction at a point of a parameterized surface is the "
         "cross product of the two coordinate tangent vectors there.",
         "An honest opaque call, and the second one this pass contributes to "
         "docs/BACKLOG.md's running count of two-argument heads that cannot see "
         "each other. What is lost here is unusually concrete. The cross "
         "product's magnitude is the area of the parallelogram the tangents "
         "span -- which is `geometry.area_formulas.rectangle_area_formula`'s "
         "content for orthogonal tangents, and the graph holds that node, and "
         "this pass just added a third member to its typed group "
         "(`graphtheory.enumeration.complete_bipartite_edge_count`). None of "
         "that is reachable from behind an opaque head. The parallel with "
         "`ml.recurrence.mlstm_matrix_memory_update`'s OUTER is exact: both are "
         "bilinear constructions on two vectors that had to become calls "
         "because `*` in this grammar means 'commutative product' and nothing "
         "else, and in both cases the wrapper quarantines a subterm that would "
         "otherwise join a well-populated family. A per-head "
         "commutativity/antisymmetry table is the fix both nodes want.",
         ["A regular parameterization: the two tangents linearly independent, "
          "so the cross product is nonzero",
          "Three dimensions; the construction has no analogue in other "
          "dimensions without exterior algebra",
          "A consistent choice of parameter order across the surface, which is "
          "what an orientation is"],
         [DOCARMO1976, FOLEY1990, PHONG1975, FARIN2002],
         disciplines=["geometric_modeling", "differential_geometry",
                      "computer_graphics"],
         functionals=[CROSS_FN],
         failure_modes=[
             "At a parametric singularity (a pole of a sphere's standard "
             "parameterization) the tangents become dependent and the normal "
             "vanishes, though the surface is perfectly smooth there.",
             "A non-orientable surface admits no consistent global choice, so "
             "the pointwise definition cannot be extended and the failure is "
             "topological rather than numerical.",
             "For meshes, averaging face normals to get vertex normals is a "
             "convention with no unique right answer; weighting by area, by "
             "angle or not at all gives visibly different shading."],
         inferential_links=links(
             composed_with=["geomodel.transforms.homogeneous_rigid_transform",
                            "geometry.area_formulas.rectangle_area_formula"]),
         keywords=["surface normal", "cross product", "tangent vector",
                   "orientation", "area element", "opaque head"],
         canonical_objects=["parameterized surface", "tangent plane",
                            "normal vector"]),

    # ---------------------------------------------------------------- 7 ----
    node("geomodel.quaternions.unit_quaternion_constraint",
         "Unit-Norm Constraint on a Rotation Quaternion",
         "definition", "formal", "rotations", "quaternion_representation",
         "w^2 + x^2 + y^2 + z^2 = 1",
         "w^2 + x^2 + y^2 + z^2 = 1",
         [{"form_id": "norm_form", "notation_system": "ascii",
           "expression": "NORM(q)^2 = 1",
           "scope_note": "The same constraint as a norm condition; the expanded form is kept in the template because the grammar has no norm"},
          {"form_id": "axis_angle", "notation_system": "ascii",
           "expression": "q = (COS(theta/2), SIN(theta/2)*axis)",
           "scope_note": "The parameterization that satisfies the constraint identically, by the Pythagorean identity. The half-angle is why q and -q give the same rotation"},
          {"form_id": "double_cover", "notation_system": "ascii",
           "expression": "q and -q represent the same rotation",
           "scope_note": "The unit quaternions form a double cover of SO(3); this is a statement about the map, not about the constraint, and has no template here"}],
         "unit_sphere_constraint",
         "REALPART^2 + IMAGI^2 + IMAGJ^2 + IMAGK^2 = 1",
         [slot("REALPART", "variable", "scalar_component"),
          slot("IMAGI", "variable", "first_vector_component"),
          slot("IMAGJ", "variable", "second_vector_component"),
          slot("IMAGK", "variable", "third_vector_component")],
         ["Four squares summing to one: the equation of the unit sphere in four "
          "dimensions, S^3. That the rotations of three-space are parameterized "
          "by a three-sphere -- doubly, since q and -q agree -- is the whole "
          "content of the quaternion representation, and the template states "
          "only the sphere.",
          "All four slots are variable-like and enter symmetrically. The "
          "commutative `+` of the grammar is faithful here, and the symmetry is "
          "real: no component is distinguished BY THE CONSTRAINT, even though "
          "the real part is distinguished by the algebra.",
          "A constraint, not an assignment. It is one of the few statements in "
          "the three corpora with no designated output slot, which is what a "
          "constraint is: the relation holds among the four, and none is "
          "computed from the others.",
          "This is the quaternion counterpart of the orthogonality condition "
          "that geomodel.transforms.homogeneous_rigid_transform cannot express. "
          "Four numbers and one equation, versus nine numbers and six "
          "equations, is the practical argument for quaternions."],
         [sym("w", "variable", "scalar_component",
              "Real (scalar) part of the quaternion.", 0),
          sym("x", "variable", "first_vector_component",
              "Coefficient of i.", 0),
          sym("y", "variable", "second_vector_component",
              "Coefficient of j.", 0),
          sym("z", "variable", "third_vector_component",
              "Coefficient of k.", 0)],
         [EQ, ADD, POW],
         "A quaternion represents a rotation exactly when its four components' "
         "squares sum to one.",
         "A singleton, and the miss is arity alone. "
         "`geometry.right_triangles.pythagorean_theorem` and "
         "`diffgeo.surfaces.euclidean_line_element` share "
         "`+(^(?0:V, 2), ^(?1:V, 2)) = ^(?2:V, 2)`; this node is "
         "`1 = +(^(?0:V, 2), ^(?1:V, 2), ^(?2:V, 2), ^(?3:V, 2))`. Two "
         "differences, and both are structural rather than notational: four "
         "squares instead of two, and a literal on the right where the "
         "Pythagorean pair has a third square. The second difference is the "
         "more interesting one -- the Pythagorean form says 'this length equals "
         "that combination' and the unit-sphere form says 'this combination is "
         "pinned', which is the difference between a measurement and a "
         "constraint. The graph has no machinery for the sum-of-squares family "
         "as such (a variadic accumulation of squared slots), and it now has "
         "three members of it in three disciplines. That is a better case for "
         "an associativity-aware `+` family query than any single pair.",
         ["Unit norm, which is what makes the quaternion a rotation rather than "
          "a rotation-and-scaling",
          "q and -q denote the same rotation, so the representation is "
          "two-to-one",
          "Renormalization required after numerical composition; the constraint "
          "is not preserved by floating-point multiplication"],
         [HAMILTON1844, SHOEMAKE1985, FOLEY1990],
         disciplines=["geometric_modeling", "mathematics", "computer_graphics",
                      "robotics"],
         failure_modes=[
             "Linear interpolation between two unit quaternions leaves the "
             "sphere and must be renormalized, and even then does not "
             "interpolate at constant angular velocity -- which is what "
             "spherical linear interpolation exists to fix.",
             "The double cover means naive interpolation between q and -q takes "
             "the long way round the sphere for the same rotation; sign "
             "canonicalization is a real step, not a nicety.",
             "Reading the four components as a point in R^4 with Euclidean "
             "structure is right for the constraint and wrong for the "
             "rotation metric, which is the angular one."],
         inferential_links=links(
             composed_with=["geomodel.transforms.homogeneous_rigid_transform",
                            "geometry.right_triangles.pythagorean_theorem"]),
         keywords=["quaternion", "unit norm", "rotation", "SO(3)",
                   "three-sphere", "Hamilton", "slerp"],
         canonical_objects=["quaternion", "rotation", "unit sphere"]),

    # ---------------------------------------------------------------- 8 ----
    node("geomodel.bezier.endpoint_tangent",
         "Bezier Endpoint Tangent",
         "proposition", "derived", "curves_and_surfaces", "derivatives",
         "P'(0) = n*(C_1 - C_0)",
         "P'(0) = n\\left(C_1 - C_0\\right)",
         [{"form_id": "other_end", "notation_system": "vector_notation",
           "expression": "P'(1) = n*(C_n - C_(n-1))",
           "scope_note": "The same statement at the far end; the curve leaves along the last leg of the control polygon as it entered along the first"},
          {"form_id": "hodograph", "notation_system": "ascii",
           "expression": "P'(t) = n * sum_i BASIS_i(t) * (C_(i+1) - C_i)",
           "scope_note": "The derivative curve: a degree n-1 Bezier over the forward differences. The endpoint statement is this evaluated at t = 0"},
          {"form_id": "g1_continuity", "notation_system": "ascii",
           "expression": "C_n - C_(n-1) parallel to D_1 - D_0",
           "scope_note": "Why the fact is used: joining two Bezier segments smoothly is a condition on the two adjacent control legs, not on the curves"}],
         "scaled_difference",
         "TANGENT = DEGREE*(CONTROLONE - CONTROLZERO)",
         [slot("TANGENT", "variable", "endpoint_tangent"),
          slot("DEGREE", "parameter", "curve_degree"),
          slot("CONTROLONE", "variable", "second_control_point"),
          slot("CONTROLZERO", "variable", "first_control_point")],
         ["A scaled difference of two variables. The degree is parameter-like "
          "-- it is fixed when the curve is chosen -- and the control points "
          "are variable-like, so the structure is 'a chosen number times a "
          "displacement'.",
          "The difference is translation-invariant while the individual points "
          "are not, which is the algebraic reason a tangent is a vector and a "
          "position is a point. The template shows the difference and cannot "
          "show that the two live in different spaces.",
          "The degree multiplies the whole displacement. That factor is what "
          "makes degree elevation change the control polygon while leaving the "
          "curve alone: adding a control point shortens the first leg by "
          "exactly the factor that keeps this product fixed.",
          "One endpoint only. The companion statement at t = 1 is the same "
          "template with different slots filled, which is a fact about the "
          "curve's symmetry that the graph records as an equivalent form."],
         [sym("Pprime0", "variable", "endpoint_tangent",
              "Derivative of the curve at the start parameter.", 1),
          sym("C_0", "variable", "first_control_point",
              "First control point.", 1),
          sym("C_1", "variable", "second_control_point",
              "Second control point.", 1),
          sym("n", "parameter", "curve_degree", "Degree of the curve.", 0)],
         [EQ, SUB, MUL],
         "A Bezier curve leaves its first control point in the direction of the "
         "second, at a speed of the degree times the distance between them.",
         "A singleton at typed and family level "
         "(`?0:V = *(?1:P, +(?2:V, neg(?3:V)))`), with one instructive "
         "near-neighbour. The shape-level skeleton "
         "`?0 = *(?1, +(?2, neg(?3)))` is what you get by factoring "
         "`probstat.transform.z_standardization`'s "
         "`?0:V = *(+(?1:V, neg(?2:P)), inv(?3:P))` differently -- both are 'a "
         "scale factor times a difference' -- but z-standardization divides "
         "where this multiplies, so the `inv` separates them, in the same way "
         "it separates Newton's method from gradient descent in this pass's "
         "first prediction. Two independent misses in three corpora caused by "
         "the same one-node difference between multiplying by a scale and "
         "dividing by one is worth noting: the graph treats `k*x` and `x/k` as "
         "unrelated, and a normalization convention decides which a discipline "
         "writes.",
         ["A Bezier curve of degree at least one",
          "Distinct first two control points, or the tangent vanishes and the "
          "direction is undefined",
          "Parameterization over [0,1]; a different interval rescales the "
          "derivative"],
         [BEZIER1972, FARIN2002, PRAUTZSCH2002],
         disciplines=["geometric_modeling", "mathematics", "computer_graphics"],
         failure_modes=[
             "A vanishing tangent at a coincident control pair is a "
             "parameterization cusp, not a geometric one; the curve is still "
             "smooth as a set, and code that reads the derivative as a "
             "direction will divide by zero anyway.",
             "Matching tangent DIRECTIONS gives geometric continuity, matching "
             "tangent VECTORS gives parametric continuity, and confusing the "
             "two is the standard source of visible creases in joined "
             "surfaces."],
         inferential_links=links(
             composed_with=["geomodel.bezier.bernstein_bezier_evaluation",
                            "geomodel.bezier.de_casteljau_step"]),
         keywords=["Bezier", "tangent", "hodograph", "control polygon",
                   "degree elevation", "G1 continuity"],
         canonical_objects=["control polygon", "tangent vector", "curve degree"]),
]


CORPORA = [
    ("data/numerical_analysis/nodes.json",
     "numerical_analysis.computation_and_error.v1", "numerical_analysis",
     NUMANALYSIS),
    ("data/graph_theory/nodes.json",
     "graph_theory.counting_and_structure.v1", "graph_theory", GRAPHTHEORY),
    ("data/geometric_modeling/nodes.json",
     "geometric_modeling.curves_and_transforms.v1", "geometric_modeling",
     GEOMODEL),
]


def main() -> None:
    for path, corpus_id, discipline, nodes in CORPORA:
        corpus = {
            "schema": "../../schema/equation-node.schema.json",
            "corpus_id": corpus_id,
            "discipline": discipline,
            "version": "1.0.0-alpha",
            "statement_nodes": nodes,
        }
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print(f"wrote {len(nodes)} {discipline} nodes -> {out}")


if __name__ == "__main__":
    main()
