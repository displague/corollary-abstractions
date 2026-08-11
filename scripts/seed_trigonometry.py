#!/usr/bin/env python3
"""Seed data/trigonometry/nodes.json — the canonical trigonometric identities.

v0.10 item 1: the coverage instrument (v0.9) found trig one of the demanded heads
the grammar lacked (~5% of Goedel-Pset, 603 Lean-workbook statements blocked on
`sin`/`cos`/`tan`). A head is only legitimate once a corpus node carries it, so
this seed authors the canonical identities that DEFINE the SIN/COS/TAN heads —
the Pythagorean identity, the angle-sum laws and their double-angle special cases,
the tangent definition, and the even/odd symmetries. With these in `data/`, the
classifier may honestly count `sin`/`cos`/`tan` as supported, and the coverage
delta on the three committed sources is the head's justification.

These are small, canonical exemplars, not invented scale: they establish the head
so that ingested trig statements have something to reduce onto.
"""

from __future__ import annotations

import json
from pathlib import Path


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="arithmetic"):
    return {"symbol": symbol, "name": name, "arity": arity, "operator_family": family}


EQ = op("=", "equality", 2, "relational")
ADD = op("+", "addition", 2, "arithmetic")
SUB = op("-", "subtraction", 2, "arithmetic")
MUL = op("*", "multiplication", 2, "arithmetic")
DIV = op("/", "division", 2, "arithmetic")
POW = op("^", "exponentiation", 2, "arithmetic")
NEG = op("-", "negation", 1, "arithmetic")

SIN_FN = {"notation": "SIN(.)", "name": "sine", "input_arity": 1,
          "codomain": "[-1, 1]",
          "description": "Sine of an angle (radians); ordinate on the unit circle."}
COS_FN = {"notation": "COS(.)", "name": "cosine", "input_arity": 1,
          "codomain": "[-1, 1]",
          "description": "Cosine of an angle (radians); abscissa on the unit circle."}
TAN_FN = {"notation": "TAN(.)", "name": "tangent", "input_arity": 1,
          "codomain": "reals (extended)",
          "description": "Tangent of an angle; the ratio SIN/COS where COS is nonzero."}

ANGLE = sym("x", "variable", "angle", "An angle, measured in radians.")
ANGLE_A = sym("a", "variable", "angle", "A first angle, in radians.")
ANGLE_B = sym("b", "variable", "angle", "A second angle, in radians.")


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
         meaning, significance, conditions, provenance,
         functionals=None, constants=None, failure_modes=None,
         inferential_links=None, keywords=None, canonical_objects=None):
    context = {"disciplines": ["trigonometry"], "subfield": subfield, "topic": topic}
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
                           "functionals": functionals or [], "index_sets": [],
                           "constants": constants or []},
        "semantic_interpretation": interpretation,
        "inferential_links": inferential_links or links(),
        "provenance": provenance,
    }
    if keywords:
        out["keywords"] = keywords
    return out


ABRAMOWITZ = {"citation_key": "abramowitz1964",
              "bibliographic_entry": "Abramowitz, M., Stegun, I. A. (1964). Handbook of Mathematical Functions. Washington: National Bureau of Standards."}
STEWART = {"citation_key": "stewart2015",
           "bibliographic_entry": "Stewart, J. (2015). Calculus: Early Transcendentals (8th ed.). Boston: Cengage Learning."}


NODES = [
    node("trigonometry.identities.pythagorean",
         "Pythagorean Identity",
         "identity", "derived", "circular_functions", "fundamental_identities",
         "sin(x)^2 + cos(x)^2 = 1", "\\sin^2 x + \\cos^2 x = 1",
         [{"form_id": "tangent_secant", "notation_system": "ascii",
           "expression": "1 + tan(x)^2 = sec(x)^2",
           "scope_note": "Divide through by cos(x)^2 where cos(x) is nonzero"},
          {"form_id": "sine_from_cosine", "notation_system": "ascii",
           "expression": "sin(x)^2 = 1 - cos(x)^2",
           "scope_note": "Solved for the squared sine"}],
         "unit_circle_constraint", "SIN(ANGLE)^2 + COS(ANGLE)^2 = 1",
         [slot("ANGLE", "variable", "angle")],
         ["Holds for every real angle without exception.",
          "Even in the angle: the identity is unchanged under ANGLE -> -ANGLE.",
          "The single constraint that a point (COS, SIN) lies on the unit circle."],
         [ANGLE], [EQ, ADD, POW],
         "The squared sine and squared cosine of any angle sum to one: the "
         "coordinates of a unit-circle point satisfy the circle's equation.",
         "The foundational circular identity; a squared-sum equal to a constant, "
         "distinguished from the Pythagorean theorem it descends from by the SIN and "
         "COS heads wrapping its slots rather than free legs.",
         ["Angle measured in radians (or any consistent measure)",
          "Real-valued angle"],
         [ABRAMOWITZ, STEWART],
         functionals=[SIN_FN, COS_FN],
         keywords=["Pythagorean identity", "unit circle", "sine", "cosine"]),

    node("trigonometry.definitions.tangent",
         "Definition of Tangent",
         "definition", "formal", "circular_functions", "ratios",
         "tan(x) = sin(x)/cos(x)", "\\tan x = \\dfrac{\\sin x}{\\cos x}",
         [{"form_id": "cotangent", "notation_system": "ascii",
           "expression": "cot(x) = cos(x)/sin(x)",
           "scope_note": "Reciprocal ratio where sin(x) is nonzero"}],
         "ratio_definition", "TAN(ANGLE) = SIN(ANGLE) / COS(ANGLE)",
         [slot("ANGLE", "variable", "angle")],
         ["Undefined where COS(ANGLE) = 0.",
          "Odd in the angle: TAN(-ANGLE) = -TAN(ANGLE).",
          "A ratio of the two coordinate functions."],
         [ANGLE], [EQ, DIV],
         "The tangent of an angle is the ratio of its sine to its cosine, defined "
         "wherever the cosine does not vanish.",
         "A ratio definition in the shape of speed = distance / time and density = "
         "mass / volume, with the numerator and denominator both trigonometric heads.",
         ["Cosine of the angle is nonzero"],
         [ABRAMOWITZ, STEWART],
         functionals=[SIN_FN, COS_FN, TAN_FN],
         failure_modes=["Undefined at odd multiples of pi/2 where the cosine is zero."],
         keywords=["tangent", "ratio", "sine", "cosine"]),

    node("trigonometry.identities.sine_angle_sum",
         "Sine of an Angle Sum",
         "identity", "derived", "circular_functions", "angle_addition",
         "sin(a + b) = sin(a)*cos(b) + cos(a)*sin(b)",
         "\\sin(a+b) = \\sin a\\cos b + \\cos a\\sin b",
         [{"form_id": "difference", "notation_system": "ascii",
           "expression": "sin(a - b) = sin(a)*cos(b) - cos(a)*sin(b)",
           "scope_note": "Replace b by -b using the odd/even symmetries"}],
         "angle_addition_sine",
         "SIN(ANGLE1 + ANGLE2) = SIN(ANGLE1)*COS(ANGLE2) + COS(ANGLE1)*SIN(ANGLE2)",
         [slot("ANGLE1", "variable", "angle"), slot("ANGLE2", "variable", "angle")],
         ["Symmetric under exchanging ANGLE1 and ANGLE2.",
          "Reduces to the double-angle sine when the two angles are equal.",
          "Bilinear in the sine/cosine coordinates of the two angles."],
         [ANGLE_A, ANGLE_B], [EQ, ADD, MUL],
         "The sine of a sum of two angles expands into a bilinear combination of the "
         "sines and cosines of the parts.",
         "The generating angle-addition law for sine; its equal-angle restriction is "
         "the double-angle identity.",
         ["Real-valued angles in radians"],
         [ABRAMOWITZ, STEWART],
         functionals=[SIN_FN, COS_FN],
         inferential_links=links(
             generalizes=["trigonometry.identities.double_angle_sine"]),
         keywords=["angle addition", "sine", "sum formula"]),

    node("trigonometry.identities.cosine_angle_sum",
         "Cosine of an Angle Sum",
         "identity", "derived", "circular_functions", "angle_addition",
         "cos(a + b) = cos(a)*cos(b) - sin(a)*sin(b)",
         "\\cos(a+b) = \\cos a\\cos b - \\sin a\\sin b",
         [{"form_id": "difference", "notation_system": "ascii",
           "expression": "cos(a - b) = cos(a)*cos(b) + sin(a)*sin(b)",
           "scope_note": "Replace b by -b using the odd/even symmetries"}],
         "angle_addition_cosine",
         "COS(ANGLE1 + ANGLE2) = COS(ANGLE1)*COS(ANGLE2) - SIN(ANGLE1)*SIN(ANGLE2)",
         [slot("ANGLE1", "variable", "angle"), slot("ANGLE2", "variable", "angle")],
         ["Symmetric under exchanging ANGLE1 and ANGLE2.",
          "Reduces to the double-angle cosine when the two angles are equal.",
          "The real part of the complex product e^{i a} e^{i b}."],
         [ANGLE_A, ANGLE_B], [EQ, SUB, MUL],
         "The cosine of a sum of two angles is the product of cosines minus the "
         "product of sines.",
         "The generating angle-addition law for cosine; with the sine law it is the "
         "trigonometric face of complex multiplication.",
         ["Real-valued angles in radians"],
         [ABRAMOWITZ, STEWART],
         functionals=[SIN_FN, COS_FN],
         inferential_links=links(
             generalizes=["trigonometry.identities.double_angle_cosine"]),
         keywords=["angle addition", "cosine", "sum formula"]),

    node("trigonometry.identities.double_angle_sine",
         "Double-Angle Sine",
         "identity", "derived", "circular_functions", "multiple_angles",
         "sin(2*x) = 2*sin(x)*cos(x)", "\\sin 2x = 2\\sin x\\cos x",
         [{"form_id": "product_to_sum", "notation_system": "ascii",
           "expression": "sin(x)*cos(x) = sin(2*x)/2"}],
         "double_angle_sine", "SIN(2*ANGLE) = 2*SIN(ANGLE)*COS(ANGLE)",
         [slot("ANGLE", "variable", "angle")],
         ["The equal-angle case of the sine angle-sum law.",
          "Vanishes exactly where SIN or COS vanishes."],
         [ANGLE], [EQ, MUL],
         "The sine of twice an angle is twice the product of the angle's sine and "
         "cosine.",
         "The double-angle sine, a special case of the sine angle-sum law with the "
         "two angles identified.",
         ["Real-valued angle in radians"],
         [ABRAMOWITZ, STEWART],
         functionals=[SIN_FN, COS_FN],
         inferential_links=links(
             special_case_of=["trigonometry.identities.sine_angle_sum"]),
         keywords=["double angle", "sine"]),

    node("trigonometry.identities.double_angle_cosine",
         "Double-Angle Cosine",
         "identity", "derived", "circular_functions", "multiple_angles",
         "cos(2*x) = cos(x)^2 - sin(x)^2", "\\cos 2x = \\cos^2 x - \\sin^2 x",
         [{"form_id": "sine_only", "notation_system": "ascii",
           "expression": "cos(2*x) = 1 - 2*sin(x)^2",
           "scope_note": "Using the Pythagorean identity"}],
         "double_angle_cosine", "COS(2*ANGLE) = COS(ANGLE)^2 - SIN(ANGLE)^2",
         [slot("ANGLE", "variable", "angle")],
         ["The equal-angle case of the cosine angle-sum law.",
          "A difference of squares in the coordinate functions."],
         [ANGLE], [EQ, SUB, POW],
         "The cosine of twice an angle is the difference of the squared cosine and "
         "the squared sine.",
         "The double-angle cosine, a special case of the cosine angle-sum law with "
         "the two angles identified.",
         ["Real-valued angle in radians"],
         [ABRAMOWITZ, STEWART],
         functionals=[SIN_FN, COS_FN],
         inferential_links=links(
             special_case_of=["trigonometry.identities.cosine_angle_sum"]),
         keywords=["double angle", "cosine", "difference of squares"]),

    node("trigonometry.symmetry.sine_odd",
         "Sine is Odd",
         "identity", "derived", "circular_functions", "parity",
         "sin(-x) = -sin(x)", "\\sin(-x) = -\\sin x",
         [{"form_id": "reflection", "notation_system": "ascii",
           "expression": "sin(-x) + sin(x) = 0"}],
         "odd_function", "SIN(-ANGLE) = -SIN(ANGLE)",
         [slot("ANGLE", "variable", "angle")],
         ["Odd symmetry: reflection through the origin negates the value.",
          "Equivalent to point symmetry of the sine graph about the origin."],
         [ANGLE], [EQ, NEG],
         "Sine reverses sign when its angle is negated: it is an odd function.",
         "The odd-function archetype instantiated by sine; shares its shape with any "
         "sign-reversing map f(-x) = -f(x).",
         ["Real-valued angle"],
         [ABRAMOWITZ, STEWART],
         functionals=[SIN_FN],
         keywords=["odd function", "sine", "parity", "symmetry"]),

    node("trigonometry.symmetry.cosine_even",
         "Cosine is Even",
         "identity", "derived", "circular_functions", "parity",
         "cos(-x) = cos(x)", "\\cos(-x) = \\cos x",
         [{"form_id": "reflection", "notation_system": "ascii",
           "expression": "cos(-x) - cos(x) = 0"}],
         "even_function", "COS(-ANGLE) = COS(ANGLE)",
         [slot("ANGLE", "variable", "angle")],
         ["Even symmetry: reflection through the origin preserves the value.",
          "Equivalent to mirror symmetry of the cosine graph about the vertical axis."],
         [ANGLE], [EQ, NEG],
         "Cosine is unchanged when its angle is negated: it is an even function.",
         "The even-function archetype instantiated by cosine; shares its shape with "
         "any reflection-invariant map f(-x) = f(x).",
         ["Real-valued angle"],
         [ABRAMOWITZ, STEWART],
         functionals=[COS_FN],
         keywords=["even function", "cosine", "parity", "symmetry"]),
]


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "trigonometry.core.v1",
        "discipline": "trigonometry",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data") / "trigonometry" / "nodes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {out} ({len(NODES)} nodes)")


if __name__ == "__main__":
    main()
