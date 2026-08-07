#!/usr/bin/env python3
"""Seed data/calculus/nodes.json with foundational calculus statement nodes.

Chosen so structural twins fire across disciplines: the average rate of change
is the same ratio archetype as average speed and mass density; the tangent-line
linearization is the same affine archetype as the location-scale transform in
the statistics corpus; the exponential growth law is the shared skeleton behind
chemical decay, radioactive decay, and compound interest. The remaining nodes
(limit definition of the derivative, power rule, linearity, product and chain
rules, both halves of the fundamental theorem) supply the operator calculus that
generates those forms and gives the corpus its internal entailment lattice.
"""

from __future__ import annotations

import json
from pathlib import Path


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="arithmetic"):
    return {"symbol": symbol, "name": name, "arity": arity, "operator_family": family}


def fn(notation, name, arity, desc, codomain="real"):
    return {"notation": notation, "name": name, "input_arity": arity,
            "codomain": codomain, "description": desc}


EQ = op("=", "equality", 2, "relational")
ADD = op("+", "addition", 2, "arithmetic")
SUB = op("-", "subtraction", 2, "arithmetic")
MUL = op("*", "multiplication", 2, "arithmetic")
DIV = op("/", "division", 2, "arithmetic")
POW = op("^", "exponentiation", 2, "arithmetic")
LIM = op("lim", "limit", 1, "limit")

D_FN = fn("D(.)", "differentiation_operator", 1,
          "Maps a differentiable function to its derivative function.",
          "function")
INT_FN = fn("INTEGRAL(.)", "integration_operator", 1,
            "Maps an integrable function to its accumulation function or "
            "definite integral.", "function")
EXP_FN = fn("EXP(.)", "natural_exponential", 1,
            "Natural exponential function, the base-e power map.")
LIM_FN = fn("lim", "limit_functional", 1,
            "Limit of an expression as the indicated variable approaches its "
            "target value.")
COMPOSE_FN = fn("COMPOSE(.,.)", "function_composition", 2,
                "Composition of an outer map with an inner map.", "function")


def slot(sid, cat, role):
    return {"slot_id": sid, "syntactic_category": cat, "semantic_role": role}


def node(sid, title, cls, status, subfield, topic, ascii_, latex, forms,
         archetype, template, slots, invariants, symbols, operators,
         meaning, significance, conditions, provenance, disciplines=None,
         functionals=None, constants=None, links=None, keywords=None,
         failure_modes=None, canonical_objects=None):
    context = {"disciplines": disciplines or ["calculus"],
               "subfield": subfield, "topic": topic}
    if canonical_objects:
        context["canonical_objects"] = canonical_objects
    interpretation = {"statement_meaning": meaning,
                      "statistical_significance": significance,
                      "regularity_conditions": conditions}
    if failure_modes:
        interpretation["failure_modes"] = failure_modes
    base_links = {"entailed_by": [], "entails": [], "equivalent_to": [],
                  "special_case_of": [], "generalizes": [], "composed_with": []}
    base_links.update(links or {})
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
                           "functionals": functionals or [], "index_sets": [],
                           "constants": constants or []},
        "semantic_interpretation": interpretation,
        "inferential_links": base_links,
        "provenance": provenance,
    }
    if keywords:
        out["keywords"] = keywords
    return out


CAUCHY = {"citation_key": "cauchy1823",
          "bibliographic_entry": ("Cauchy, A.-L. (1823). Resume des lecons donnees "
                                  "a l'Ecole Royale Polytechnique sur le calcul "
                                  "infinitesimal. Paris: Imprimerie Royale.")}
RUDIN = {"citation_key": "rudin1976",
         "bibliographic_entry": ("Rudin, W. (1976). Principles of Mathematical "
                                 "Analysis (3rd ed.). McGraw-Hill.")}
APOSTOL = {"citation_key": "apostol1967",
           "bibliographic_entry": ("Apostol, T. M. (1967). Calculus, Volume I: "
                                   "One-Variable Calculus with an Introduction to "
                                   "Linear Algebra (2nd ed.). Wiley.")}
SPIVAK = {"citation_key": "spivak2008",
          "bibliographic_entry": ("Spivak, M. (2008). Calculus (4th ed.). "
                                  "Publish or Perish.")}
STEWART = {"citation_key": "stewart2015",
           "bibliographic_entry": ("Stewart, J. (2015). Calculus: Early "
                                   "Transcendentals (8th ed.). Cengage Learning.")}
COURANT = {"citation_key": "courant1937",
           "bibliographic_entry": ("Courant, R. (1937). Differential and Integral "
                                   "Calculus, Volume I (2nd ed.). Interscience.")}
LEIBNIZ = {"citation_key": "leibniz1684",
           "bibliographic_entry": ("Leibniz, G. W. (1684). Nova Methodus pro Maximis "
                                   "et Minimis. Acta Eruditorum, 467-473.")}
BARROW = {"citation_key": "barrow1670",
          "bibliographic_entry": "Barrow, I. (1670). Lectiones Geometricae. London."}
EULER = {"citation_key": "euler1748",
         "bibliographic_entry": ("Euler, L. (1748). Introductio in Analysin "
                                 "Infinitorum. Lausanne: Bousquet.")}
TAYLOR = {"citation_key": "taylor1715",
          "bibliographic_entry": ("Taylor, B. (1715). Methodus Incrementorum Directa "
                                  "et Inversa. London: Pearson.")}
MALTHUS = {"citation_key": "malthus1798",
           "bibliographic_entry": ("Malthus, T. R. (1798). An Essay on the Principle "
                                   "of Population. London: J. Johnson.")}


NODES = [
    node("calculus.limits.derivative_definition",
         "Derivative as the Limit of Difference Quotients",
         "definition", "formal", "differential_calculus", "limits",
         "D(f)(x) = lim_{h->0} (f(x + h) - f(x)) / h",
         "f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}",
         [{"form_id": "leibniz_notation", "notation_system": "ascii",
           "expression": "df/dx = lim_{h->0} (f(x+h) - f(x))/h",
           "scope_note": "Leibniz differential notation for the same limit"},
          {"form_id": "increment_quotient", "notation_system": "ascii",
           "expression": "D(f)(x) = lim_{Delta_x->0} Delta_f/Delta_x",
           "scope_note": "Increment notation: the derivative as a limit of average rates"},
          {"form_id": "secant_at_point", "notation_system": "ascii",
           "expression": "D(f)(a) = lim_{x->a} (f(x) - f(a))/(x - a)",
           "scope_note": "Equivalent point form obtained by substituting x = a + h"}],
         "limit_of_difference_quotient",
         "D(F) = lim_h (F(VAR + STEP) - F(VAR)) / STEP",
         [slot("F", "functional", "differentiand"),
          slot("VAR", "variable", "evaluation_point"),
          slot("STEP", "variable", "vanishing_increment")],
         ["A ratio archetype wrapped in a limit: the derivative is an average rate "
          "of change pushed to a vanishing interval.",
          "The increment appears twice, once inside the perturbed argument and once "
          "as the denominator; those two roles must be the same quantity.",
          "Existence requires the left and right one-sided limits to agree, which is "
          "what makes differentiability strictly stronger than continuity."],
         [sym("x", "variable", "evaluation_point",
              "Point at which the derivative is evaluated."),
          sym("h", "variable", "vanishing_increment",
              "Increment in the argument, driven to zero.")],
         [EQ, ADD, SUB, DIV, LIM],
         "The derivative of a function at a point is the limit of its average rate "
         "of change over intervals shrinking to that point.",
         "Root definition of the whole differential corpus: every differentiation "
         "rule below is discharged against this limit, and it is the bridge from the "
         "finite ratio archetype shared with physics rate definitions to the "
         "infinitesimal operator D.",
         ["f defined on an open neighbourhood of x",
          "The two-sided limit exists and is finite",
          "The increment h is nonzero throughout the limiting process"],
         [CAUCHY, RUDIN, SPIVAK],
         functionals=[D_FN, LIM_FN,
                      fn("f(.)", "differentiand", 1,
                         "Real-valued function being differentiated.")],
         links={"entails": ["calculus.differentiation.power_rule",
                            "calculus.differentiation.linearity_of_derivative",
                            "calculus.differentiation.product_rule",
                            "calculus.differentiation.chain_rule",
                            "calculus.differentiation.exponential_derivative",
                            "calculus.approximation.tangent_line_linearization"],
                "composed_with": ["calculus.differentiation.average_rate_of_change"]},
         keywords=["derivative", "limit", "difference quotient", "differentiability"],
         failure_modes=["Corner or cusp points where the one-sided limits differ",
                        "Vertical tangents where the limit diverges",
                        "Everywhere-continuous nowhere-differentiable functions"]),

    node("calculus.differentiation.average_rate_of_change",
         "Average Rate of Change",
         "definition", "formal", "differential_calculus", "rates_of_change",
         "R = Delta_f / Delta_x",
         "R = \\frac{\\Delta f}{\\Delta x}",
         [{"form_id": "endpoint_form", "notation_system": "ascii",
           "expression": "R = (f(b) - f(a)) / (b - a)",
           "scope_note": "Secant slope over the interval [a, b]"},
          {"form_id": "difference_quotient", "notation_system": "ascii",
           "expression": "R = (f(x + h) - f(x)) / h",
           "scope_note": "Increment form entering the derivative definition"}],
         "ratio_rate", "RATE = QUANTITY / INTERVAL",
         [slot("RATE", "variable", "output"),
          slot("QUANTITY", "variable", "accumulated_quantity"),
          slot("INTERVAL", "variable", "reference_extent")],
         ["Rate as ratio of accumulated quantity to elapsed interval.",
          "Invariant under a common rescaling of numerator and denominator; only "
          "their dimensional quotient is meaningful.",
          "Undefined exactly when the reference extent collapses to zero, which is "
          "what forces the limit construction."],
         [sym("R", "variable", "output", "Average rate of change."),
          sym("Delta_f", "variable", "accumulated_quantity",
              "Change in the function value across the interval."),
          sym("Delta_x", "variable", "reference_extent",
              "Extent of the interval over which the change accumulates.")],
         [EQ, DIV],
         "The average rate of change is the total change in the output divided by "
         "the extent of the input interval over which it accrued.",
         "The purely structural core of every rate notion: an exact typed twin of "
         "physics.kinematics.average_speed and physics.materials.mass_density. The "
         "same skeleton carries distance-per-time, mass-per-volume, and "
         "output-change-per-input-change, which is the clearest evidence in the "
         "corpus that rate is a shape rather than a physical dimension.",
         ["Nonzero interval extent", "Function defined at both endpoints"],
         [STEWART, APOSTOL],
         functionals=[fn("f(.)", "response_function", 1,
                         "Function whose change is being measured.")],
         links={"composed_with": ["calculus.limits.derivative_definition"]},
         keywords=["rate", "secant slope", "difference quotient", "ratio archetype"]),

    node("calculus.differentiation.power_rule",
         "Power Rule for Differentiation",
         "theorem", "derived", "differential_calculus", "differentiation_rules",
         "D(x^n) = n*x^(n - 1)",
         "\\frac{d}{dx} x^n = n x^{n-1}",
         [{"form_id": "antiderivative_form", "notation_system": "ascii",
           "expression": "INTEGRAL(x^n) = x^(n + 1)/(n + 1)",
           "scope_note": "Inverse form, valid for n != -1"},
          {"form_id": "monomial_form", "notation_system": "ascii",
           "expression": "D(c*x^n) = c*n*x^(n - 1)",
           "scope_note": "With a leading coefficient, via linearity"}],
         "exponent_decrement_rule",
         "D(VAR^EXPONENT) = EXPONENT * VAR^(EXPONENT - 1)",
         [slot("VAR", "variable", "base"),
          slot("EXPONENT", "parameter", "exponent")],
         ["Differentiation lowers polynomial degree by exactly one.",
          "The old exponent is not destroyed but reappears as a multiplicative "
          "factor, so the exponent occupies two structural positions on the right.",
          "Holds for every real exponent on the domain where the power is defined, "
          "not merely for positive integers."],
         [sym("x", "variable", "base", "Base variable."),
          sym("n", "parameter", "exponent", "Real exponent.")],
         [EQ, MUL, SUB, POW],
         "The derivative of a power function multiplies by the exponent and reduces "
         "the exponent by one.",
         "The rule that makes the geometric power hierarchy differentiable: it maps "
         "the scaled-cubic, scaled-quadratic and scaled-linear archetypes of the "
         "geometry corpus onto one another, so sphere volume differentiates to "
         "sphere surface area and circle area to circumference.",
         ["x in the domain of x^n",
          "For non-integer n, restrict to positive x",
          "For n = 0 the derivative is identically zero"],
         [LEIBNIZ, APOSTOL, STEWART],
         functionals=[D_FN],
         constants=[{"symbol": "1", "value": 1,
                     "description": "Unit decrement applied to the exponent."}],
         links={"entailed_by": ["calculus.limits.derivative_definition"]},
         keywords=["power rule", "polynomial", "degree", "exponent"]),

    node("calculus.differentiation.linearity_of_derivative",
         "Linearity of the Derivative",
         "theorem", "derived", "differential_calculus", "differentiation_rules",
         "D(a*f + b*g) = a*D(f) + b*D(g)",
         "\\frac{d}{dx}\\bigl(a f + b g\\bigr) = a \\frac{df}{dx} + b \\frac{dg}{dx}",
         [{"form_id": "additivity", "notation_system": "ascii",
           "expression": "D(f + g) = D(f) + D(g)",
           "scope_note": "Additivity alone, with both coefficients set to one"},
          {"form_id": "homogeneity", "notation_system": "ascii",
           "expression": "D(a*f) = a*D(f)",
           "scope_note": "Homogeneity alone, with the second summand dropped"}],
         "linear_operator_law",
         "D(SCALAR1*FUNC1 + SCALAR2*FUNC2) = SCALAR1*D(FUNC1) + SCALAR2*D(FUNC2)",
         [slot("SCALAR1", "parameter", "coefficient"),
          slot("FUNC1", "functional", "first_summand"),
          slot("SCALAR2", "parameter", "coefficient"),
          slot("FUNC2", "functional", "second_summand")],
         ["The operator commutes with the affine combination: the same expression "
          "shape appears on both sides of the relation with D pushed inward.",
          "Coefficients are inert under the operator; only the function slots are "
          "acted upon.",
          "Additivity and homogeneity are packaged as one statement, which is the "
          "defining property of a linear map on the space of differentiable "
          "functions."],
         [sym("a", "parameter", "coefficient", "Scalar multiplier of the first term."),
          sym("b", "parameter", "coefficient", "Scalar multiplier of the second term.")],
         [EQ, ADD, MUL],
         "Differentiation distributes over sums and passes through constant "
         "multipliers.",
         "Establishes D as a linear operator, which is why the derivative interacts "
         "with the affine archetype shared by the tangent-line linearization and the "
         "location-scale transform of the statistics corpus: an operator that "
         "preserves affine structure is what lets local linear models be composed.",
         ["f and g differentiable at the point of evaluation",
          "Coefficients independent of the differentiation variable"],
         [RUDIN, APOSTOL],
         functionals=[D_FN],
         links={"entailed_by": ["calculus.limits.derivative_definition"],
                "composed_with": ["calculus.differentiation.power_rule"]},
         keywords=["linearity", "linear operator", "additivity", "homogeneity"]),

    node("calculus.differentiation.product_rule",
         "Product Rule (Leibniz Rule)",
         "theorem", "derived", "differential_calculus", "differentiation_rules",
         "D(f*g) = D(f)*g + f*D(g)",
         "(fg)' = f' g + f g'",
         [{"form_id": "prime_notation", "notation_system": "ascii",
           "expression": "(f*g)' = f'*g + f*g'"},
          {"form_id": "quotient_corollary", "notation_system": "ascii",
           "expression": "D(f/g) = (D(f)*g - f*D(g))/g^2",
           "scope_note": "Quotient rule, obtained by applying the product rule to f*(1/g)"}],
         "derivation_leibniz_law",
         "D(FUNC1*FUNC2) = D(FUNC1)*FUNC2 + FUNC1*D(FUNC2)",
         [slot("FUNC1", "functional", "first_factor"),
          slot("FUNC2", "functional", "second_factor")],
         ["Each factor is differentiated exactly once per summand; the two summands "
          "exhaust the ways of placing the operator.",
          "Symmetric under exchange of the two factors, matching the commutativity "
          "of the product being differentiated.",
          "Differentiation is a derivation rather than a ring homomorphism: it is "
          "additive but explicitly not multiplicative."],
         [sym("f", "variable", "first_factor", "First factor evaluated pointwise."),
          sym("g", "variable", "second_factor", "Second factor evaluated pointwise.")],
         [EQ, ADD, MUL],
         "The derivative of a product is the first factor differentiated times the "
         "second, plus the first times the second differentiated.",
         "The canonical failure of naive operator distribution: it is the statement "
         "that separates linear operators from multiplicative ones, and its shape "
         "recurs wherever a coupled pair is perturbed, as in error propagation for "
         "products of measured quantities.",
         ["Both factors differentiable at the point of evaluation"],
         [LEIBNIZ, SPIVAK, RUDIN],
         functionals=[D_FN],
         links={"entailed_by": ["calculus.limits.derivative_definition"]},
         keywords=["product rule", "Leibniz rule", "derivation"],
         failure_modes=["Assuming D(f*g) = D(f)*D(g), which holds only in "
                        "degenerate cases"]),

    node("calculus.differentiation.chain_rule",
         "Chain Rule",
         "theorem", "derived", "differential_calculus", "differentiation_rules",
         "D(COMPOSE(f, g)) = COMPOSE(D(f), g) * D(g)",
         "\\frac{d}{dx} f(g(x)) = f'(g(x))\\, g'(x)",
         [{"form_id": "pointwise_form", "notation_system": "ascii",
           "expression": "D(f(g(x))) = D(f)(g(x)) * D(g)(x)",
           "scope_note": "Explicit pointwise evaluation of the composite derivative"},
          {"form_id": "leibniz_cancellation", "notation_system": "ascii",
           "expression": "dy/dx = (dy/du)*(du/dx)",
           "scope_note": "Leibniz form, mnemonically a cancellation of differentials"}],
         "composition_factorization",
         "D(COMPOSE(OUTER, INNER)) = COMPOSE(D(OUTER), INNER) * D(INNER)",
         [slot("OUTER", "functional", "outer_map"),
          slot("INNER", "functional", "inner_map")],
         ["The derivative of a composite factorizes into a product of derivatives, "
          "with the outer derivative re-evaluated along the inner map.",
          "The inner map appears twice: once as the argument of the outer derivative "
          "and once differentiated in its own right.",
          "Reduces to the identity rule when the inner map is the identity, which "
          "fixes the normalization of the factorization."],
         [sym("x", "variable", "input", "Input to the inner map."),
          sym("u", "variable", "intermediate", "Intermediate value produced by the "
              "inner map and consumed by the outer map.")],
         [EQ, MUL],
         "The rate of change of a composite equals the outer rate of change measured "
         "at the inner value, scaled by the inner rate of change.",
         "The composition law that makes local rates chainable, and therefore the "
         "mechanism by which unit conversions, change of variables in integration, "
         "and backpropagation through layered models are all one statement.",
         ["g differentiable at the point",
          "f differentiable at the image of that point under g"],
         [CAUCHY, RUDIN, COURANT],
         functionals=[D_FN, COMPOSE_FN],
         links={"entailed_by": ["calculus.limits.derivative_definition"],
                "composed_with": ["calculus.differentiation.exponential_derivative"]},
         keywords=["chain rule", "composition", "change of variables"]),

    node("calculus.differentiation.exponential_derivative",
         "Derivative of the Natural Exponential",
         "theorem", "derived", "differential_calculus", "transcendental_functions",
         "D(EXP(k*x)) = k*EXP(k*x)",
         "\\frac{d}{dx} e^{kx} = k e^{kx}",
         [{"form_id": "unit_rate", "notation_system": "ascii",
           "expression": "D(EXP(x)) = EXP(x)",
           "scope_note": "Fixed point of differentiation, obtained at k = 1"},
          {"form_id": "ode_form", "notation_system": "ascii",
           "expression": "D(y) = k*y",
           "scope_note": "The differential equation that the exponential solves"}],
         "eigenfunction_of_differentiation",
         "D(EXP(RATE*VAR)) = RATE * EXP(RATE*VAR)",
         [slot("RATE", "parameter", "rate_constant"),
          slot("VAR", "variable", "input")],
         ["The operand is reproduced exactly on the right, scaled by a constant: an "
          "eigenvalue equation for the differentiation operator.",
          "The rate constant occupies two positions, inside the exponent and as the "
          "outer scale factor, and those must be the same quantity.",
          "Self-similarity under differentiation is preserved under repeated "
          "application, each pass contributing another factor of the rate."],
         [sym("k", "parameter", "rate_constant",
              "Rate constant appearing in the exponent."),
          sym("x", "variable", "input", "Input variable.")],
         [EQ, MUL],
         "Differentiating a scaled exponential returns the same exponential "
         "multiplied by the rate constant in its exponent.",
         "Identifies the exponential family as the eigenfunctions of differentiation, "
         "which is exactly why the exponential growth law is the universal solution "
         "shape for any process whose rate is proportional to its own size.",
         ["k independent of x", "Natural base for the stated eigenvalue"],
         [EULER, APOSTOL],
         functionals=[D_FN, EXP_FN],
         constants=[{"symbol": "e",
                     "description": "Base of the natural exponential, the unique base "
                                    "for which the eigenvalue equals the exponent rate."}],
         links={"entailed_by": ["calculus.limits.derivative_definition"],
                "entails": ["calculus.growth.exponential_growth_law"],
                "composed_with": ["calculus.differentiation.chain_rule"]},
         keywords=["exponential", "eigenfunction", "rate constant"]),

    node("calculus.growth.exponential_growth_law",
         "Exponential Growth and Decay Law",
         "model_specification", "derived", "differential_equations",
         "growth_and_decay",
         "N = N0*EXP(k*t)",
         "N(t) = N_0 e^{k t}",
         [{"form_id": "governing_ode", "notation_system": "ascii",
           "expression": "D(N) = k*N",
           "scope_note": "Equivalent differential specification: rate proportional to size"},
          {"form_id": "decay_form", "notation_system": "ascii",
           "expression": "N = N0*EXP(-k*t)",
           "scope_note": "Decay regime, obtained by negating the rate constant"},
          {"form_id": "half_life_form", "notation_system": "ascii",
           "expression": "N = N0*2^(-t/T)",
           "scope_note": "Base-2 reparameterization in terms of a half-life T"}],
         "exponential_evolution", "AMOUNT = INITIAL * EXP(RATE * TIME)",
         [slot("AMOUNT", "variable", "output"),
          slot("INITIAL", "parameter", "initial_condition"),
          slot("RATE", "parameter", "rate_constant"),
          slot("TIME", "variable", "input")],
         ["Constant proportional rate of change: the relative growth rate is "
          "time-invariant even though the absolute rate is not.",
          "Multiplicative in elapsed time, so equal intervals multiply the amount by "
          "equal factors and the law is invariant under time translation up to a "
          "change of the initial condition.",
          "The sign of the rate constant separates growth from decay while leaving "
          "the structure untouched, which is why growth and decay are one archetype."],
         [sym("N", "variable", "output", "Amount present at time t."),
          sym("N0", "parameter", "initial_condition", "Amount present at time zero."),
          sym("k", "parameter", "rate_constant",
              "Proportional rate constant; positive for growth, negative for decay."),
          sym("t", "variable", "input", "Elapsed time.")],
         [EQ, MUL],
         "A quantity whose instantaneous rate of change is proportional to its "
         "current size evolves as its initial value times an exponential of the "
         "rate times elapsed time.",
         "The most heavily reused shape in the corpus: radioactive and chemical "
         "first-order decay, continuously compounded interest, unconstrained "
         "population growth, and RC circuit relaxation are the same statement with "
         "different slot fillings. It is the intended cross-discipline anchor "
         "between the calculus corpus and any chemistry kinetics corpus.",
         ["Rate constant independent of time and of the amount",
          "Unbounded resources, i.e. no saturation term",
          "Continuous rather than discrete evolution"],
         [MALTHUS, EULER, STEWART],
         functionals=[EXP_FN, D_FN],
         constants=[{"symbol": "e", "description": "Base of the natural exponential."}],
         links={"entailed_by": ["calculus.differentiation.exponential_derivative"]},
         keywords=["exponential growth", "decay", "rate constant", "half-life"],
         failure_modes=["Saturating systems where a carrying capacity invalidates "
                        "the constant-rate assumption",
                        "Time-varying rate constants",
                        "Small-population regimes where discreteness dominates"],
         canonical_objects=["amount", "initial condition", "rate constant", "time"]),

    node("calculus.integration.ftc_differentiation_part",
         "Fundamental Theorem of Calculus, Differentiation Part",
         "theorem", "formal", "integral_calculus", "fundamental_theorem",
         "D(INTEGRAL(f)) = f",
         "\\frac{d}{dx}\\int_a^x f(t)\\,dt = f(x)",
         [{"form_id": "explicit_limits", "notation_system": "ascii",
           "expression": "D(INTEGRAL(f, a, x)) = f(x)",
           "scope_note": "Accumulation function with an explicit lower limit"},
          {"form_id": "operator_form", "notation_system": "ascii",
           "expression": "D o INTEGRAL = identity",
           "scope_note": "Operator composition statement on continuous integrands"}],
         "left_inverse_operator_pair", "D(INTEGRAL(F)) = F",
         [slot("F", "functional", "integrand")],
         ["Differentiation is a left inverse of accumulation on continuous "
          "integrands: the composite operator is the identity.",
          "The single function slot appears on both sides unchanged, which is what "
          "makes this an operator identity rather than a computation.",
          "Independent of the lower limit of accumulation, since changing it shifts "
          "the accumulation function by a constant."],
         [sym("x", "variable", "upper_limit", "Upper limit of accumulation."),
          sym("t", "variable", "integration_variable",
              "Bound variable of integration.")],
         [EQ],
         "Differentiating the accumulation function of a continuous integrand "
         "recovers the integrand at the upper limit.",
         "One half of the statement that the two central operators of calculus are "
         "mutually inverse; it converts the integral from an area computation into "
         "an antidifferentiation problem.",
         ["f continuous on the interval of accumulation",
          "Upper limit interior to that interval"],
         [BARROW, APOSTOL, RUDIN],
         functionals=[D_FN, INT_FN,
                      fn("f(.)", "integrand", 1,
                         "Continuous function being accumulated.")],
         links={"entails": ["calculus.integration.ftc_evaluation_part"]},
         keywords=["fundamental theorem", "accumulation", "antiderivative",
                   "operator inverse"],
         failure_modes=["Discontinuous integrands, where the derivative of the "
                        "accumulation function can fail to exist at jumps"]),

    node("calculus.integration.ftc_evaluation_part",
         "Fundamental Theorem of Calculus, Evaluation Part",
         "theorem", "derived", "integral_calculus", "fundamental_theorem",
         "INTEGRAL(D(f)) = f(b) - f(a)",
         "\\int_a^b f'(x)\\,dx = f(b) - f(a)",
         [{"form_id": "antiderivative_form", "notation_system": "ascii",
           "expression": "INTEGRAL(g, a, b) = F(b) - F(a)",
           "scope_note": "Stated for any antiderivative F of the integrand g"},
          {"form_id": "net_change_form", "notation_system": "ascii",
           "expression": "INTEGRAL(D(f)) = Delta_f",
           "scope_note": "Net change theorem reading"}],
         "boundary_difference_evaluation",
         "INTEGRAL(D(F)) = F(UPPER) - F(LOWER)",
         [slot("F", "functional", "antiderivative"),
          slot("UPPER", "variable", "upper_limit"),
          slot("LOWER", "variable", "lower_limit")],
         ["An integral over an extent collapses to a difference of boundary values: "
          "interior behaviour is irrelevant to the total.",
          "The continuum analogue of a telescoping sum, and the one-dimensional case "
          "of the general Stokes pattern relating a region to its boundary.",
          "Any two antiderivatives differ by an additive constant, which cancels in "
          "the difference and makes the right-hand side well defined."],
         [sym("a", "variable", "lower_limit", "Lower limit of integration."),
          sym("b", "variable", "upper_limit", "Upper limit of integration.")],
         [EQ, SUB],
         "The definite integral of a derivative over an interval equals the net "
         "change of the function between the endpoints.",
         "Turns integration into evaluation and supplies the accounting identity "
         "behind conservation arguments: total accumulated change depends only on "
         "the boundary, which is the shape reused by path-independence and "
         "potential-function statements in physics.",
         ["f continuously differentiable on the closed interval",
          "The derivative integrable over that interval"],
         [BARROW, LEIBNIZ, APOSTOL],
         functionals=[D_FN, INT_FN,
                      fn("f(.)", "antiderivative", 1,
                         "Function whose derivative is being integrated.")],
         links={"entailed_by": ["calculus.integration.ftc_differentiation_part"]},
         keywords=["fundamental theorem", "net change", "boundary evaluation",
                   "telescoping"]),

    node("calculus.approximation.tangent_line_linearization",
         "Tangent-Line Linearization",
         "definition", "formal", "differential_calculus", "linear_approximation",
         "L = f(a) + D(f)(a)*(x - a)",
         "L(x) = f(a) + f'(a)(x - a)",
         [{"form_id": "approximation_form", "notation_system": "ascii",
           "expression": "f(x) approx f(a) + D(f)(a)*(x - a)",
           "scope_note": "First-order Taylor approximation valid near a"},
          {"form_id": "differential_form", "notation_system": "ascii",
           "expression": "Delta_f approx D(f)(a)*Delta_x",
           "scope_note": "Increment form used for error propagation"}],
         "affine_operator", "LINEARIZED = BASEVALUE + SLOPE * DISPLACEMENT",
         [slot("LINEARIZED", "variable", "output"),
          slot("BASEVALUE", "parameter", "anchor_value"),
          slot("SLOPE", "parameter", "linear_factor"),
          slot("DISPLACEMENT", "variable", "input")],
         ["Affine in the displacement from the anchor point: a constant offset plus "
          "a scaled input.",
          "Agrees with the function to first order at the anchor, where both the "
          "value and the slope are matched exactly.",
          "The anchor value and slope are frozen constants of the approximation, "
          "even though both are function evaluations."],
         [sym("L", "variable", "output", "Linearized value."),
          sym("a", "parameter", "anchor_point", "Point of expansion."),
          sym("x", "variable", "input", "Point at which the linearization is read.")],
         [EQ, ADD, MUL, SUB],
         "Near a chosen point, a differentiable function is replaced by the affine "
         "function that matches its value and slope there.",
         "The exact typed twin of probstat.transform.affine_location_scale: the "
         "linearization is a location-scale map whose shift is the anchored value "
         "and whose scale is the derivative. This is why delta-method variance "
         "propagation in statistics and first-order error propagation in physics "
         "are the same computation performed on the same skeleton.",
         ["f differentiable at the anchor point",
          "Displacement small enough that the first-order remainder is negligible"],
         [TAYLOR, COURANT, STEWART],
         functionals=[D_FN,
                      fn("f(.)", "target_function", 1,
                         "Function being locally approximated.")],
         links={"entailed_by": ["calculus.limits.derivative_definition"],
                "composed_with": ["probstat.transform.affine_location_scale"]},
         keywords=["linearization", "tangent line", "affine", "first-order Taylor",
                   "delta method"],
         failure_modes=["Large displacements where curvature dominates",
                        "Anchors at inflection or non-differentiable points"]),
]


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "calculus.foundations.v1",
        "discipline": "calculus",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data/calculus/nodes.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {len(NODES)} calculus nodes -> {out}")


if __name__ == "__main__":
    main()
