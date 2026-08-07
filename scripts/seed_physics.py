#!/usr/bin/env python3
"""Seed data/physics/nodes.json with foundational physics statement nodes.

Chosen so structural twins fire across disciplines: scaled-linear laws
(Newton II, Ohm), scaled-quadratic energy (kinetic energy vs geometric areas),
inverse-square pair couplings (gravitation vs Coulomb), and ratio definitions
(speed vs density).
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
MUL = op("*", "multiplication", 2, "arithmetic")
DIV = op("/", "division", 2, "arithmetic")
POW = op("^", "exponentiation", 2, "arithmetic")
NEG = op("-", "negation", 1, "arithmetic")


def slot(sid, cat, role):
    return {"slot_id": sid, "syntactic_category": cat, "semantic_role": role}


def node(sid, title, cls, status, subfield, topic, ascii_, latex, forms,
         archetype, template, slots, invariants, symbols, operators,
         meaning, significance, conditions, provenance, disciplines=None,
         functionals=None, constants=None):
    return {
        "statement_id": sid, "title": title, "statement_class": cls,
        "epistemic_status": status,
        "theory_context": {"disciplines": disciplines or ["physics"],
                           "subfield": subfield, "topic": topic},
        "formal_statement": {"canonical_ascii": ascii_, "canonical_latex": latex,
                             "equivalent_forms": forms},
        "structural_signature": {"archetype_id": archetype,
                                 "anonymized_template": template,
                                 "slot_schema": slots, "invariants": invariants},
        "symbol_lexicon": {"symbols": symbols, "operators": operators,
                           "functionals": functionals or [], "index_sets": [],
                           "constants": constants or []},
        "semantic_interpretation": {"statement_meaning": meaning,
                                    "statistical_significance": significance,
                                    "regularity_conditions": conditions},
        "inferential_links": {"entailed_by": [], "entails": [], "equivalent_to": [],
                              "special_case_of": [], "generalizes": [],
                              "composed_with": []},
        "provenance": provenance,
    }


NODES = [
    node("physics.mechanics.newton_second_law", "Newton's Second Law",
         "model_specification", "empirical", "classical_mechanics", "dynamics",
         "F = m*a", "F = m a",
         [{"form_id": "momentum_rate", "notation_system": "ascii",
           "expression": "F = dp/dt", "scope_note": "Momentum form for constant mass"}],
         "scaled_linear", "FORCE = INERTIA * RESPONSE",
         [slot("FORCE", "variable", "output"),
          slot("INERTIA", "parameter", "linear_factor"),
          slot("RESPONSE", "variable", "input")],
         ["Linearity of force in acceleration at fixed mass."],
         [sym("F", "variable", "output", "Net force."),
          sym("m", "parameter", "linear_factor", "Inertial mass."),
          sym("a", "variable", "input", "Acceleration.")],
         [EQ, MUL],
         "Net force equals mass times acceleration.",
         "Central linear response law of classical dynamics.",
         ["Inertial reference frame", "Speeds far below c", "Constant mass"],
         [{"citation_key": "newton1687",
           "bibliographic_entry": "Newton, I. (1687). Philosophiae Naturalis Principia Mathematica."}]),

    node("physics.circuits.ohms_law", "Ohm's Law",
         "model_specification", "empirical", "electromagnetism", "circuits",
         "V = I*R", "V = I R",
         [{"form_id": "current_form", "notation_system": "ascii",
           "expression": "I = V/R"}],
         "scaled_linear", "POTENTIAL = FLOW * RESISTANCE",
         [slot("POTENTIAL", "variable", "output"),
          slot("FLOW", "variable", "input"),
          slot("RESISTANCE", "parameter", "linear_factor")],
         ["Linearity of voltage in current at fixed resistance."],
         [sym("V", "variable", "output", "Potential difference."),
          sym("I", "variable", "input", "Current."),
          sym("R", "parameter", "linear_factor", "Resistance.")],
         [EQ, MUL],
         "Voltage across an ohmic conductor is proportional to current.",
         "Prototype linear constitutive relation; structural twin of Newton's second law.",
         ["Ohmic (linear) material", "Constant temperature"],
         [{"citation_key": "ohm1827",
           "bibliographic_entry": "Ohm, G. S. (1827). Die galvanische Kette, mathematisch bearbeitet."}]),

    node("physics.relativity.mass_energy_equivalence", "Mass-Energy Equivalence",
         "theorem", "derived", "special_relativity", "energy",
         "E = m*c^2", "E = m c^2",
         [{"form_id": "rest_energy", "notation_system": "ascii",
           "expression": "E_0 = m*c^2", "scope_note": "Rest energy"}],
         "scaled_linear_by_squared_constant", "ENERGY = MASS * SPEEDLIMIT^2",
         [slot("ENERGY", "variable", "output"),
          slot("MASS", "variable", "input"),
          slot("SPEEDLIMIT", "constant", "scale_constant")],
         ["Linearity of rest energy in mass; universal constant squared as scale."],
         [sym("E", "variable", "output", "Rest energy."),
          sym("m", "variable", "input", "Rest mass.")],
         [EQ, MUL, POW],
         "Rest energy is proportional to rest mass with c squared as the constant of proportionality.",
         "Cross-domain shape twin of geometric scaled-quadratic forms with the squared quantity as constant rather than variable.",
         ["Rest frame of the body"],
         [{"citation_key": "einstein1905",
           "bibliographic_entry": "Einstein, A. (1905). Ist die Traegheit eines Koerpers von seinem Energieinhalt abhaengig? Annalen der Physik."}],
         constants=[{"symbol": "c",
                     "description": "Invariant speed of light in vacuum."}]),

    node("physics.mechanics.kinetic_energy", "Kinetic Energy",
         "definition", "formal", "classical_mechanics", "energy",
         "KE = (1/2)*m*v^2", "KE = \\tfrac{1}{2} m v^2",
         [{"form_id": "momentum_form", "notation_system": "ascii",
           "expression": "KE = p^2/(2*m)"}],
         "scaled_quadratic", "ENERGY = CONSTANT * MASS * SPEED^2",
         [slot("ENERGY", "variable", "output"),
          slot("CONSTANT", "constant", "scale_factor"),
          slot("MASS", "parameter", "linear_factor"),
          slot("SPEED", "variable", "input")],
         ["Quadratic in speed; linear in mass."],
         [sym("KE", "variable", "output", "Kinetic energy."),
          sym("m", "parameter", "linear_factor", "Mass."),
          sym("v", "variable", "input", "Speed.")],
         [EQ, MUL, POW],
         "Kinetic energy grows with the square of speed, scaled by half the mass.",
         "Physics member of the scaled-quadratic archetype shared with circle and sphere area formulas.",
         ["Non-relativistic speeds"],
         [{"citation_key": "goldstein2002",
           "bibliographic_entry": "Goldstein, H., Poole, C., Safko, J. (2002). Classical Mechanics (3rd ed.). Addison Wesley."}],
         constants=[{"symbol": "1/2",
                     "description": "Kinetic energy scale factor."}]),

    node("physics.mechanics.hookes_law", "Hooke's Law",
         "model_specification", "empirical", "classical_mechanics", "elasticity",
         "F = -k*x", "F = -k x",
         [{"form_id": "magnitude_form", "notation_system": "ascii",
           "expression": "|F| = k*|x|"}],
         "negated_scaled_linear", "FORCE = -(STIFFNESS * DISPLACEMENT)",
         [slot("FORCE", "variable", "output"),
          slot("STIFFNESS", "parameter", "linear_factor"),
          slot("DISPLACEMENT", "variable", "input")],
         ["Linear restoring response opposing displacement."],
         [sym("F", "variable", "output", "Restoring force."),
          sym("k", "parameter", "linear_factor", "Spring stiffness."),
          sym("x", "variable", "input", "Displacement from equilibrium.")],
         [EQ, MUL, NEG],
         "Restoring force is proportional to displacement and directed against it.",
         "Signed variant of the scaled-linear archetype; generator of harmonic motion.",
         ["Small displacements within the elastic limit"],
         [{"citation_key": "hooke1678",
           "bibliographic_entry": "Hooke, R. (1678). Lectures de Potentia Restitutiva."}]),

    node("physics.gravitation.newton_universal_gravitation",
         "Newton's Law of Universal Gravitation",
         "model_specification", "empirical", "classical_mechanics", "gravitation",
         "F = G*m1*m2/r^2", "F = G \\frac{m_1 m_2}{r^2}",
         [{"form_id": "vector_form", "notation_system": "ascii",
           "expression": "F = -(G*m1*m2/r^2) * rhat",
           "scope_note": "Attractive direction along separation"}],
         "inverse_square_pair_coupling",
         "COUPLING = CONSTANT * SOURCE1 * SOURCE2 / SEPARATION^2",
         [slot("COUPLING", "variable", "output"),
          slot("CONSTANT", "constant", "coupling_constant"),
          slot("SOURCE1", "variable", "source_charge"),
          slot("SOURCE2", "variable", "source_charge"),
          slot("SEPARATION", "variable", "distance")],
         ["Symmetric bilinear in the two sources; inverse-square in separation."],
         [sym("F", "variable", "output", "Gravitational force magnitude."),
          sym("m1", "variable", "source_charge", "First mass."),
          sym("m2", "variable", "source_charge", "Second mass."),
          sym("r", "variable", "distance", "Separation distance.")],
         [EQ, MUL, DIV, POW],
         "Two masses attract with force proportional to their product and inversely to squared separation.",
         "Canonical inverse-square pair coupling; exact typed twin of Coulomb's law.",
         ["Point masses or spherical symmetry", "Weak-field regime"],
         [{"citation_key": "newton1687",
           "bibliographic_entry": "Newton, I. (1687). Philosophiae Naturalis Principia Mathematica."}],
         constants=[{"symbol": "G",
                     "description": "Universal gravitational constant."}]),

    node("physics.electromagnetism.coulombs_law", "Coulomb's Law",
         "model_specification", "empirical", "electromagnetism", "electrostatics",
         "F = k*q1*q2/r^2", "F = k \\frac{q_1 q_2}{r^2}",
         [{"form_id": "permittivity_form", "notation_system": "ascii",
           "expression": "F = q1*q2/(4*pi*eps0*r^2)"}],
         "inverse_square_pair_coupling",
         "COUPLING = CONSTANT * SOURCE1 * SOURCE2 / SEPARATION^2",
         [slot("COUPLING", "variable", "output"),
          slot("CONSTANT", "constant", "coupling_constant"),
          slot("SOURCE1", "variable", "source_charge"),
          slot("SOURCE2", "variable", "source_charge"),
          slot("SEPARATION", "variable", "distance")],
         ["Symmetric bilinear in the two charges; inverse-square in separation."],
         [sym("F", "variable", "output", "Electrostatic force magnitude."),
          sym("q1", "variable", "source_charge", "First charge."),
          sym("q2", "variable", "source_charge", "Second charge."),
          sym("r", "variable", "distance", "Separation distance.")],
         [EQ, MUL, DIV, POW],
         "Two point charges interact with force proportional to their product and inversely to squared separation.",
         "Exact typed twin of Newtonian gravitation across subfields; the flagship cross-domain isomorphism.",
         ["Point charges at rest", "Vacuum or linear medium"],
         [{"citation_key": "coulomb1785",
           "bibliographic_entry": "Coulomb, C. A. (1785). Premier memoire sur l'electricite et le magnetisme."}],
         constants=[{"symbol": "k",
                     "description": "Electrostatic coupling constant."}]),

    node("physics.thermodynamics.ideal_gas_law", "Ideal Gas Law",
         "model_specification", "empirical", "thermodynamics", "equations_of_state",
         "P*V = n*R*T", "P V = n R T",
         [{"form_id": "particle_form", "notation_system": "ascii",
           "expression": "P*V = N*kB*T", "scope_note": "Particle-count form"}],
         "balanced_product_state_relation",
         "PRESSURE * VOLUME = AMOUNT * CONSTANT * TEMPERATURE",
         [slot("PRESSURE", "variable", "state_variable"),
          slot("VOLUME", "variable", "state_variable"),
          slot("AMOUNT", "parameter", "extensive_quantity"),
          slot("CONSTANT", "constant", "gas_constant"),
          slot("TEMPERATURE", "variable", "state_variable")],
         ["Product of state variables balanced against scaled temperature."],
         [sym("P", "variable", "state_variable", "Pressure."),
          sym("V", "variable", "state_variable", "Volume."),
          sym("n", "parameter", "extensive_quantity", "Amount of substance."),
          sym("T", "variable", "state_variable", "Absolute temperature.")],
         [EQ, MUL],
         "Pressure times volume balances amount times temperature for an ideal gas.",
         "State-equation archetype with products on both relation sides.",
         ["Dilute gas", "No intermolecular forces", "Absolute temperature scale"],
         [{"citation_key": "clapeyron1834",
           "bibliographic_entry": "Clapeyron, E. (1834). Memoire sur la puissance motrice de la chaleur."}],
         constants=[{"symbol": "R",
                     "description": "Universal gas constant."}]),

    node("physics.kinematics.average_speed", "Average Speed",
         "definition", "formal", "classical_mechanics", "kinematics",
         "v = d/t", "v = d/t",
         [{"form_id": "rate_form", "notation_system": "ascii",
           "expression": "v = distance/elapsed_time"}],
         "ratio_rate", "RATE = QUANTITY / INTERVAL",
         [slot("RATE", "variable", "output"),
          slot("QUANTITY", "variable", "accumulated_quantity"),
          slot("INTERVAL", "variable", "reference_extent")],
         ["Rate as ratio of accumulated quantity to elapsed interval."],
         [sym("v", "variable", "output", "Average speed."),
          sym("d", "variable", "accumulated_quantity", "Distance traveled."),
          sym("t", "variable", "reference_extent", "Elapsed time.")],
         [EQ, DIV],
         "Average speed is distance traveled per unit time.",
         "Prototype rate definition; structural twin of density and other intensive ratios.",
         ["Nonzero elapsed time"],
         [{"citation_key": "halliday2013",
           "bibliographic_entry": "Halliday, D., Resnick, R., Walker, J. (2013). Fundamentals of Physics (10th ed.). Wiley."}]),

    node("physics.materials.mass_density", "Mass Density",
         "definition", "formal", "classical_mechanics", "material_properties",
         "rho = m/V", "\\rho = m/V",
         [{"form_id": "verbose_form", "notation_system": "ascii",
           "expression": "density = mass/volume"}],
         "ratio_rate", "RATE = QUANTITY / INTERVAL",
         [slot("RATE", "variable", "output"),
          slot("QUANTITY", "variable", "accumulated_quantity"),
          slot("INTERVAL", "variable", "reference_extent")],
         ["Intensive quantity as ratio of extensive quantities."],
         [sym("rho", "variable", "output", "Mass density."),
          sym("m", "variable", "accumulated_quantity", "Mass."),
          sym("V", "variable", "reference_extent", "Volume.")],
         [EQ, DIV],
         "Density is mass per unit volume.",
         "Same ratio archetype as average speed; slots range over different physical dimensions.",
         ["Homogeneous material or local limit"],
         [{"citation_key": "halliday2013",
           "bibliographic_entry": "Halliday, D., Resnick, R., Walker, J. (2013). Fundamentals of Physics (10th ed.). Wiley."}]),
]


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "physics.foundations.v1",
        "discipline": "physics",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data/physics/nodes.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {len(NODES)} physics nodes -> {out}")


if __name__ == "__main__":
    main()
