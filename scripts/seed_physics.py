#!/usr/bin/env python3
"""Seed data/physics/nodes.json with foundational physics statement nodes.

Chosen so structural twins fire across disciplines: scaled-linear laws
(Newton II, Ohm), scaled-quadratic energy (kinetic energy vs geometric areas),
inverse-square pair couplings (gravitation vs Coulomb), and ratio definitions
(speed vs density).

`physics.thermodynamics.gibbs_entropy` was added later and for a different
reason. It is not here to survey thermodynamics -- it is here because
information theory's Shannon entropy is the *same functional*, and the corpus
should be able to say so mechanically rather than in prose. Its template

    ENTROPY = -(SCALE * sum_i PROBABILITY_i * LOG(PROBABILITY_i))

is authored identically, modulo slot names, to
infotheory.entropy.shannon_entropy's in scripts/seed_infotheory.py, so both
land on the typed skeleton

    ?0:V = neg(*(?1:P, sum⟨*(?2:V, LOG⟨?2:V⟩)⟩))

with kB and 1/ln 2 occupying the same parameter-like (P) slot. The pair also
carries a reciprocal `equivalent_to` edge, which the two files can do only
because one branch owns both of them; see docs/BACKLOG.md on cross-corpus
reciprocity. Do not "simplify" either template without editing the other --
folding the constant into the logarithm's base on one side alone silently
breaks the twin.

Reference-frame predictions were registered before their adjudicating matcher
run in docs/DESIGN-cognitive-frames.md as P-CF2 and P-CF3.  This seed repeats
them at the source-of-truth boundary:

* P-CF2: the rotating-frame declaration may family with
  narrative.frames.cartoon_gravity because both scopes suspend an ordinary
  physics law and admit a local dynamics premise.  The matcher cannot read
  scope, so the prediction is deliberately at risk: the physical equation is
  not to be respelled as a temporal liveness law to make it fire.
* P-CF3: Galilean velocity addition should join an existing additive or
  composition family rather than create a new structural archetype. The
  registered form named convex-combination/vector-addition as candidates.
  ADJUDICATED: fired in class, missed in candidates -- the twin formed
  with chain_rank_nullity (previously a singleton), a skeleton not on the
  candidate list; neither named candidate matched structurally.

Both outcomes, including a scope-invisible P-CF2 miss, are findings.
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
ADD = op("+", "addition", 2, "arithmetic")
IMPL = op("implies", "implication", 2, "logical")


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
         inferential_links=None, keywords=None, scope=None):
    interpretation = {"statement_meaning": meaning,
                      "statistical_significance": significance,
                      "regularity_conditions": conditions}
    if failure_modes:
        interpretation["failure_modes"] = failure_modes
    out = {
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
                           "functionals": functionals or [],
                           "index_sets": index_sets or [],
                           "constants": constants or []},
        "semantic_interpretation": interpretation,
        "inferential_links": inferential_links or links(),
        "provenance": provenance,
    }
    if keywords:
        out["keywords"] = keywords
    if scope is not None:
        out["scope"] = scope
    return out


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

    node("physics.thermodynamics.gibbs_entropy",
         "Gibbs Entropy (Boltzmann-Gibbs Statistical Entropy)",
         "definition", "formal", "thermodynamics", "statistical_mechanics",
         "S = -(kB * sum_i p_i*ln(p_i))",
         "S = -k_B \\sum_i p_i \\ln p_i",
         [{"form_id": "boltzmann", "notation_system": "ascii",
           "expression": "S = kB*ln(W)",
           "scope_note": "Boltzmann's form for W equally likely microstates; the uniform special case"},
          {"form_id": "von_neumann", "notation_system": "measure_theoretic",
           "expression": "S = -kB*Tr(rho*ln(rho))",
           "scope_note": "Quantum form; reduces to the Gibbs sum in the eigenbasis of the density matrix"},
          {"form_id": "canonical_ensemble", "notation_system": "ascii",
           "expression": "S = (U - F)/T",
           "scope_note": "Thermodynamic identity recovered when the p_i are the Boltzmann weights"},
          {"form_id": "shannon_units", "notation_system": "ascii",
           "expression": "S = kB * ln(2) * H(X)",
           "scope_note": "Conversion to bits; the whole content of the information-theory twin"}],
         "negated_scaled_expected_log",
         "ENTROPY = -(SCALE * sum_i PROBABILITY_i * LOG(PROBABILITY_i))",
         [slot("ENTROPY", "variable", "output"),
          slot("SCALE", "constant", "unit_scale_constant"),
          slot("PROBABILITY_i", "variable", "distribution_weight")],
         ["The microstate-probability slot occurs twice inside the summand -- as "
          "the weight and inside the logarithm -- which is what makes the "
          "quantity an expected log-probability rather than a sum of independent "
          "contributions.",
          "kB is a fixed constant, not a fitted parameter: it converts between "
          "the dimensionless count of states and thermodynamic units of J/K, and "
          "occupies the same parameter-like slot that information theory fills "
          "with 1/ln 2.",
          "Extensive: for independent subsystems the joint distribution factors "
          "and the entropies add, which is the property the logarithm is there to "
          "supply.",
          "Maximized, at fixed constraints, by the distribution that maximizes it "
          "subject to those constraints -- the canonical ensemble is that "
          "maximizer under fixed mean energy, which is Jaynes' derivation.",
          "Zero for a pure state (a single microstate with probability 1), the "
          "third-law reference point."],
         [sym("S", "variable", "output", "Statistical (Gibbs) entropy of the ensemble."),
          sym("p_i", "distribution", "distribution_weight",
              "Probability of microstate i in the ensemble."),
          sym("T", "variable", "state_variable",
              "Absolute temperature, which converts entropy to energy in the "
              "thermodynamic identities.")],
         [EQ, MUL, NEG,
          op("sum", "summation over microstates", 1, "arithmetic")],
         "The entropy of an ensemble is the negated, kB-scaled average of the "
         "logarithm of its own microstate probabilities.",
         "The corpus's information/thermodynamics bridge, and the node added "
         "specifically to test whether the twin thesis survives contact with a "
         "case where the identity is claimed to be literal rather than "
         "analogical. It does: the typed skeleton "
         "`?0:V = neg(*(?1:P, sum⟨*(?2:V, LOG⟨?2:V⟩)⟩))` is shared character for "
         "character with infotheory.entropy.shannon_entropy, and the two "
         "templates are authored identically modulo slot names because the "
         "underlying claim -- Shannon's, sharpened by Jaynes and priced by "
         "Landauer -- is that thermodynamic entropy *is* missing information "
         "about the microstate, in units of kB instead of bits. The reciprocal "
         "`equivalent_to` edge between the two nodes is therefore meant "
         "literally, with the base-conversion constant as the exchange rate. "
         "Within physics the node also supplies the statistical foundation the "
         "chemistry corpus's Gibbs free energy leans on: the ENTROPY slot in "
         "`FREE_ENERGY = ENTHALPY - TEMPERATURE * ENTROPY` is this quantity.",
         ["A well-defined ensemble with normalized microstate probabilities",
          "Terms with p_i = 0 read as 0 via the limit x*ln(x) -> 0",
          "Discrete (or suitably coarse-grained) microstates; the continuous "
          "phase-space version needs a reference measure to be well defined"],
         [{"citation_key": "gibbs1902",
           "bibliographic_entry": "Gibbs, J. W. (1902). Elementary Principles in Statistical Mechanics. New York: Charles Scribner's Sons."},
          {"citation_key": "boltzmann1877",
           "bibliographic_entry": "Boltzmann, L. (1877). Ueber die Beziehung zwischen dem zweiten Hauptsatze der mechanischen Waermetheorie und der Wahrscheinlichkeitsrechnung. Sitzungsberichte der Kaiserlichen Akademie der Wissenschaften, Wien, 76, 373-435."},
          {"citation_key": "jaynes1957",
           "bibliographic_entry": "Jaynes, E. T. (1957). Information Theory and Statistical Mechanics. Physical Review, 106(4), 620-630."},
          {"citation_key": "landauer1961",
           "bibliographic_entry": "Landauer, R. (1961). Irreversibility and Heat Generation in the Computing Process. IBM Journal of Research and Development, 5(3), 183-191."}],
         functionals=[{"notation": "LOG(.)", "name": "logarithm", "input_arity": 1,
                       "codomain": "extended reals",
                       "description": "Logarithm of a positive argument; natural "
                                      "log in the thermodynamic convention. The "
                                      "base is absorbed into the scale constant, "
                                      "which is why that constant is an explicit "
                                      "slot here."}],
         constants=[{"symbol": "kB", "value": 1.380649e-23,
                     "description": "Boltzmann constant in J/K. Fixes the units of "
                                    "entropy; the information-theoretic reading "
                                    "replaces it by 1/ln 2 to count bits, and "
                                    "Landauer's bound kB*T*ln 2 is the exchange "
                                    "rate between the two."}],
         index_sets=[{"notation": "i in Omega",
                      "domain": "the set of accessible microstates",
                      "description": "Index running over the microstates of the "
                                     "ensemble."}],
         failure_modes=[
             "For continuous phase spaces the sum becomes an integral that is not "
             "invariant under change of variables; a reference measure (h^3N per "
             "cell) must be supplied, which is where the classical entropy's "
             "additive constant and the Gibbs paradox come from.",
             "Gibbs entropy of an isolated system under Hamiltonian evolution is "
             "constant, so the second law needs coarse-graining or an open "
             "system; deriving increase from this formula alone is circular.",
             "Reading kB as a free parameter invites nonsense: it is a fixed "
             "conversion factor, and since the 2019 SI redefinition it is exact."],
         inferential_links=links(
             equivalent_to=["infotheory.entropy.shannon_entropy"]),
         keywords=["entropy", "Gibbs", "Boltzmann", "statistical mechanics",
                   "microstates", "information", "Landauer"]),

    node("physics.frames.inertial_frame_definition",
         "Inertial Frame Definition",
         "model_specification", "formal", "classical_mechanics",
         "frames_of_reference",
         "net_force = 0 implies acceleration = 0",
         "\\mathbf{F}_{\\mathrm{net}}=0 \\Rightarrow \\mathbf{a}=0",
         [{"form_id": "newton_first_law", "notation_system": "ascii",
           "expression": "a free body remains at rest or in uniform straight-line motion"}],
         "zero_response_under_zero_input",
         "IMPLIES(NET_FORCE = ZERO, ACCELERATION = ZERO)",
         [slot("NET_FORCE", "variable", "net_force"),
          slot("ACCELERATION", "variable", "acceleration"),
          slot("ZERO", "constant", "additive_identity")],
         ["The same zero denotes the additive identity in force and acceleration spaces; the implication is the frame criterion, not a claim that every body is force-free."],
         [sym("F_net", "variable", "net_force", "Net external force."),
          sym("a", "variable", "acceleration", "Acceleration measured in the candidate frame."),
          sym("0", "constant", "additive_identity", "The relevant zero vector.")],
         [EQ, IMPL],
         "A reference frame is inertial when a force-free body has zero acceleration in that frame.",
         "Makes the law suspended by a non-inertial frame an explicit corpus node rather than prose attached to Newton's second law.",
         ["Classical mechanics", "Force-free test body", "Speeds far below c"],
         [{"citation_key": "mit801_ch11",
           "bibliographic_entry": "MIT OpenCourseWare. 8.01SC Classical Mechanics, Chapter 11: Reference Frames.",
           "url": "https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/mit8_01scs22_chapter11.pdf"}],
         keywords=["inertial frame", "Newton first law", "reference frame"]),

    node("physics.frames.galilean_velocity_addition",
         "Galilean Velocity Addition",
         "transformation", "derived", "classical_mechanics",
         "frames_of_reference",
         "object_velocity = relative_velocity + frame_velocity",
         "\\mathbf{u}=\\mathbf{u}' + \\mathbf{v}",
         [{"form_id": "subtractive", "notation_system": "ascii",
           "expression": "relative_velocity = object_velocity - frame_velocity",
           "scope_note": "The equivalent form usually written as u' = u - v."}],
         "additive_frame_transformation",
         "OBJECT_VELOCITY = RELATIVE_VELOCITY + FRAME_VELOCITY",
         [slot("OBJECT_VELOCITY", "variable", "velocity_in_base_frame"),
          slot("RELATIVE_VELOCITY", "variable", "velocity_in_moving_frame"),
          slot("FRAME_VELOCITY", "variable", "frame_velocity")],
         ["The same frame-velocity term transforms every object's velocity.",
          "Composition is additive only between inertial frames in Galilean mechanics."],
         [sym("u", "variable", "velocity_in_base_frame", "Object velocity in the base frame."),
          sym("u_prime", "variable", "velocity_in_moving_frame", "Object velocity in the translating frame."),
          sym("v", "variable", "frame_velocity", "Velocity of the translating frame.")],
         [EQ, ADD],
         "An object's velocity in the base inertial frame is the sum of its velocity relative to a translating inertial frame and that frame's velocity.",
         "P-CF3's test: relative motion should reuse an existing additive skeleton rather than require a frame-specific learned operation.",
         ["Frames translate uniformly without rotation", "Galilean, not relativistic, kinematics"],
         [{"citation_key": "mit801_ch11",
           "bibliographic_entry": "MIT OpenCourseWare. 8.01SC Classical Mechanics, Chapter 11: Reference Frames.",
           "url": "https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/mit8_01scs22_chapter11.pdf"},
          {"citation_key": "fowler_galilean",
           "bibliographic_entry": "Fowler, M. Galileo and Einstein, Lecture 1: Space and Time in Newtonian Physics. University of Virginia.",
           "url": "https://galileo.phys.virginia.edu/classes/252/lecture1.htm"}],
         keywords=["Galilean transformation", "velocity addition", "relative motion"]),

    node("physics.frames.galilean_acceleration_invariance",
         "Galilean Acceleration Invariance",
         "transformation", "derived", "classical_mechanics",
         "frames_of_reference",
         "moving_frame_acceleration = base_frame_acceleration",
         "\\mathbf{a}'=\\mathbf{a}",
         [{"form_id": "derivative", "notation_system": "ascii",
           "expression": "d(relative_velocity)/dt = d(object_velocity)/dt when frame_velocity is constant"}],
         "invariant_under_frame_transformation",
         "MOVING_ACCELERATION = BASE_ACCELERATION",
         [slot("MOVING_ACCELERATION", "variable", "moving_frame_measurement"),
          slot("BASE_ACCELERATION", "variable", "base_frame_measurement")],
         ["Differentiating the velocity transformation removes the constant boost velocity."],
         [sym("a_prime", "variable", "moving_frame_measurement", "Acceleration in the translating frame."),
          sym("a", "variable", "base_frame_measurement", "Acceleration in the base frame.")],
         [EQ],
         "Uniformly translating inertial observers measure the same acceleration.",
         "Exhibits the world-tier/frame-local seam: velocities change under a Galilean boost while acceleration and Newtonian dynamics are invariant.",
         ["Constant relative frame velocity", "No relative rotation"],
         [{"citation_key": "mit801_ch11",
           "bibliographic_entry": "MIT OpenCourseWare. 8.01SC Classical Mechanics, Chapter 11: Reference Frames.",
           "url": "https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/mit8_01scs22_chapter11.pdf"}],
         keywords=["Galilean invariance", "acceleration", "inertial frame"]),

    node("physics.frames.rotating_frame",
         "Uniformly Rotating Reference Frame Declaration",
         "transformation", "derived", "classical_mechanics",
         "non_inertial_frames",
         "apparent_acceleration = inertial_acceleration + centrifugal_acceleration + coriolis_acceleration",
         "\\mathbf{a}_{\\mathrm{rot}}=\\mathbf{a}_{\\mathrm{in}}+\\mathbf{a}_{\\mathrm{cf}}+\\mathbf{a}_{\\mathrm{cor}}",
         [{"form_id": "force_form", "notation_system": "ascii",
           "expression": "apparent_force = real_force + centrifugal_force + coriolis_force"}],
         "non_inertial_additive_correction",
         "APPARENT_ACCELERATION = INERTIAL_ACCELERATION + CENTRIFUGAL_ACCELERATION + CORIOLIS_ACCELERATION",
         [slot("APPARENT_ACCELERATION", "variable", "rotating_frame_measurement"),
          slot("INERTIAL_ACCELERATION", "variable", "inertial_frame_measurement"),
          slot("CENTRIFUGAL_ACCELERATION", "variable", "frame_local_correction"),
          slot("CORIOLIS_ACCELERATION", "variable", "velocity_dependent_correction")],
         ["The correction terms are frame-local: they disappear when the same motion is described in an inertial frame.",
          "Uniform rotation removes the Euler-acceleration term; changing angular velocity requires one more summand."],
         [sym("a_rot", "variable", "rotating_frame_measurement", "Acceleration measured in the rotating frame."),
          sym("a_in", "variable", "inertial_frame_measurement", "Acceleration described in an inertial frame."),
          sym("a_cf", "variable", "frame_local_correction", "Centrifugal acceleration admitted locally."),
          sym("a_cor", "variable", "velocity_dependent_correction", "Coriolis acceleration admitted locally.")],
         [EQ, ADD],
         "A uniformly rotating observer recovers Newtonian form by adding centrifugal and Coriolis accelerations to the inertial description.",
         "P-CF2's cross-domain scope test. The scope mechanism matches cartoon gravity, but the physical equation remains an additive correction law rather than being authored into a temporal liveness shape.",
         ["Uniform angular velocity", "Classical mechanics", "A declared rotating coordinate frame"],
         [{"citation_key": "mit801_ch11",
           "bibliographic_entry": "MIT OpenCourseWare. 8.01SC Classical Mechanics, Chapter 11: Reference Frames.",
           "url": "https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/mit8_01scs22_chapter11.pdf"}],
         inferential_links=links(
             composed_with=["physics.frames.inertial_frame_definition"]),
         keywords=["rotating frame", "centrifugal", "Coriolis", "fictitious force"],
         scope={
             "frame": "physics.frames.rotating_frame",
             "role": "declaration",
             "frame_title": "Uniformly rotating reference frame",
             "premises": [{
                 "premise_id": "rotating_corrections",
                 "expression": "APPARENT_ACCELERATION = INERTIAL_ACCELERATION + CENTRIFUGAL_ACCELERATION + CORIOLIS_ACCELERATION",
             }],
             "suspends": ["physics.frames.inertial_frame_definition"],
             "governed_by": ["narrative.frame.frame_consistency"],
             "on_exit": "conjectured",
             "retrieval": "open",
         }),
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
