#!/usr/bin/env python3
"""Seed data/chemistry/nodes.json with foundational chemistry statement nodes.

Selected so structural twins fire across the existing corpora rather than
merely covering a syllabus: ratio definitions (molarity vs speed/density),
scaled multilinear products (Beer-Lambert vs prism volume and triangle area),
signed affine combinations (Gibbs vs Helmholtz free energy), and exponential
decay (integrated first-order kinetics), which is the chemical instance of the
same shape calculus states as exponential growth.
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

EXP_FN = {"notation": "EXP(.)", "name": "exponential", "input_arity": 1,
          "codomain": "positive reals",
          "description": "Natural exponential of a dimensionless argument."}
LOG_FN = {"notation": "LOG(.)", "name": "logarithm", "input_arity": 1,
          "codomain": "reals",
          "description": "Logarithm of a dimensionless argument (base fixed by convention)."}


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
         functionals=None, constants=None, failure_modes=None,
         inferential_links=None, keywords=None, canonical_objects=None):
    context = {"disciplines": disciplines or ["chemistry"],
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
                           "functionals": functionals or [], "index_sets": [],
                           "constants": constants or []},
        "semantic_interpretation": interpretation,
        "inferential_links": inferential_links or links(),
        "provenance": provenance,
    }
    if keywords:
        out["keywords"] = keywords
    return out


ATKINS = {"citation_key": "atkins2014",
          "bibliographic_entry": "Atkins, P., de Paula, J. (2014). Atkins' Physical Chemistry (10th ed.). Oxford University Press."}
GREENBOOK = {"citation_key": "iupac2007",
             "bibliographic_entry": "IUPAC (2007). Quantities, Units and Symbols in Physical Chemistry (Green Book, 3rd ed.). RSC Publishing."}


NODES = [
    node("chemistry.kinetics.rate_law_power", "Power-Law Rate Law",
         "model_specification", "empirical", "chemical_kinetics", "rate_laws",
         "rate = k*[A]^n", "v = k\\,[\\mathrm{A}]^{n}",
         [{"form_id": "multi_reactant", "notation_system": "ascii",
           "expression": "rate = k*[A]^n*[B]^m",
           "scope_note": "Empirical form with partial orders in several reactants"},
          {"form_id": "differential_first_order", "notation_system": "ascii",
           "expression": "-d[A]/dt = k*[A]", "scope_note": "Order one in A"}],
         "scaled_power_law", "RATE = RATECONST * CONCENTRATION^ORDER",
         [slot("RATE", "variable", "output"),
          slot("RATECONST", "parameter", "rate_coefficient"),
          slot("CONCENTRATION", "variable", "input"),
          slot("ORDER", "parameter", "power_exponent")],
         ["Homogeneous of degree ORDER in concentration.",
          "Linear in the rate coefficient at fixed concentration.",
          "Log-log linear: LOG(RATE) is affine in LOG(CONCENTRATION) with slope ORDER."],
         [sym("rate", "variable", "output", "Reaction rate (amount concentration per time)."),
          sym("k", "parameter", "rate_coefficient", "Rate coefficient at fixed temperature."),
          sym("[A]", "variable", "input", "Amount concentration of reactant A."),
          sym("n", "parameter", "power_exponent", "Reaction order in A.")],
         [EQ, MUL, POW],
         "The reaction rate is proportional to a power of the reactant concentration, "
         "with the exponent fixed by experiment rather than by stoichiometry.",
         "Chemistry's member of the scaled-power-law family: a symbolic-exponent "
         "generalization of the fixed-exponent scaled quadratics and cubics that "
         "geometry and mechanics instantiate with ORDER pinned to 2 or 3.",
         ["Well-mixed homogeneous phase", "Constant temperature so RATECONST is fixed",
          "Order determined empirically for non-elementary steps"],
         [{"citation_key": "vanthoff1884",
           "bibliographic_entry": "van 't Hoff, J. H. (1884). Etudes de dynamique chimique. Amsterdam: Frederik Muller."},
          ATKINS],
         failure_modes=[
             "Fails when the order changes across the concentration range, as under "
             "saturating (Michaelis-Menten) or diffusion-controlled conditions.",
             "The stoichiometric coefficient is not the order except for elementary steps."],
         inferential_links=links(
             entails=["chemistry.kinetics.first_order_integrated_rate_law"],
             composed_with=["chemistry.kinetics.arrhenius_equation"]),
         keywords=["rate law", "reaction order", "kinetics", "power law"]),

    node("chemistry.kinetics.first_order_integrated_rate_law",
         "Integrated First-Order Rate Law",
         "theorem", "derived", "chemical_kinetics", "integrated_rate_laws",
         "N = N0*exp(-k*t)", "N(t) = N_0 e^{-k t}",
         [{"form_id": "semilog", "notation_system": "ascii",
           "expression": "ln(N/N0) = -k*t",
           "scope_note": "Linearized form used to fit k"},
          {"form_id": "concentration", "notation_system": "ascii",
           "expression": "[A] = [A]0*exp(-k*t)"}],
         "exponential_decay", "AMOUNT = INITIAL * EXP(-(RATECONST * TIME))",
         [slot("AMOUNT", "variable", "output"),
          slot("INITIAL", "parameter", "initial_condition"),
          slot("RATECONST", "parameter", "decay_rate"),
          slot("TIME", "variable", "input")],
         ["Constant fractional decrement per unit time.",
          "Semilog-linear: LOG(AMOUNT) is affine in TIME with slope -RATECONST.",
          "Scale free in the initial condition: doubling INITIAL doubles AMOUNT at every TIME.",
          "Memoryless: the decay factor over an interval depends only on its length."],
         [sym("N", "variable", "output", "Amount (or concentration) remaining at time t."),
          sym("N0", "parameter", "initial_condition", "Amount present at t = 0."),
          sym("k", "parameter", "decay_rate", "First-order rate constant, units of inverse time."),
          sym("t", "variable", "input", "Elapsed time.")],
         [EQ, MUL, NEG],
         "A first-order species decays exponentially: the amount remaining is the initial "
         "amount times an exponential factor in the product of rate constant and elapsed time.",
         "The decay-signed member of the exponential archetype; identical in shape to "
         "unconstrained exponential growth in calculus and to radioactive decay, with only "
         "the sign of the rate slot distinguishing them.",
         ["First-order kinetics throughout the observed interval",
          "Isothermal conditions", "No back reaction or parallel channel"],
         [{"citation_key": "wilhelmy1850",
           "bibliographic_entry": "Wilhelmy, L. (1850). Ueber das Gesetz, nach welchem die Einwirkung der Saeuren auf den Rohrzucker stattfindet. Annalen der Physik, 157, 413-428."},
          ATKINS],
         functionals=[EXP_FN],
         inferential_links=links(
             entailed_by=["chemistry.kinetics.rate_law_power"],
             entails=["chemistry.kinetics.half_life_first_order"]),
         keywords=["first order", "exponential decay", "integrated rate law"]),

    node("chemistry.kinetics.half_life_first_order", "First-Order Half-Life",
         "corollary", "derived", "chemical_kinetics", "characteristic_times",
         "t_half = ln(2)/k", "t_{1/2} = \\frac{\\ln 2}{k}",
         [{"form_id": "rate_constant_form", "notation_system": "ascii",
           "expression": "k = ln(2)/t_half"},
          {"form_id": "mean_lifetime", "notation_system": "ascii",
           "expression": "t_half = ln(2)*tau", "scope_note": "tau = 1/k is the mean lifetime"}],
         "ratio_rate", "HALFLIFE = CONSTANT / RATECONST",
         [slot("HALFLIFE", "variable", "output"),
          slot("CONSTANT", "constant", "scale_constant"),
          slot("RATECONST", "parameter", "decay_rate")],
         ["Independent of the initial amount.",
          "Inversely proportional to the rate constant.",
          "The numerator is dimensionless, so HALFLIFE inherits the reciprocal units of RATECONST."],
         [sym("t_half", "variable", "output", "Time for the amount to fall to one half."),
          sym("k", "parameter", "decay_rate", "First-order rate constant.")],
         [EQ, DIV],
         "The time to consume half the material is a fixed dimensionless constant divided "
         "by the rate constant, and does not depend on how much material was present.",
         "Joins the ratio archetype of average speed, density and molarity at the shape "
         "level but splits from them under typing: its numerator is a constant rather than "
         "a measured extensive quantity, which is exactly the initial-amount independence "
         "that makes half-life a usable fingerprint.",
         ["First-order kinetics", "Constant temperature"],
         [{"citation_key": "rutherford1903",
           "bibliographic_entry": "Rutherford, E., Soddy, F. (1903). Radioactive change. Philosophical Magazine, 5(29), 576-591."},
          ATKINS],
         constants=[{"symbol": "ln 2", "value": 0.6931471805599453,
                     "description": "Natural logarithm of two; the dimensionless numerator fixed by halving."}],
         failure_modes=[
             "Constant half-life is diagnostic of first order only; second-order half-life "
             "depends on the initial concentration."],
         inferential_links=links(
             entailed_by=["chemistry.kinetics.first_order_integrated_rate_law"]),
         keywords=["half-life", "first order", "characteristic time"]),

    node("chemistry.kinetics.arrhenius_equation", "Arrhenius Equation",
         "model_specification", "empirical", "chemical_kinetics", "temperature_dependence",
         "k = A*exp(-Ea/(R*T))", "k = A e^{-E_a/(R T)}",
         [{"form_id": "linearized", "notation_system": "ascii",
           "expression": "ln(k) = ln(A) - Ea/(R*T)",
           "scope_note": "Arrhenius plot: slope -Ea/R against 1/T"},
          {"form_id": "two_point", "notation_system": "ascii",
           "expression": "ln(k2/k1) = -(Ea/R)*(1/T2 - 1/T1)"}],
         "thermally_activated_exponential",
         "RATECONST = PREFACTOR * EXP(-(BARRIER / (GASCONST * TEMPERATURE)))",
         [slot("RATECONST", "variable", "output"),
          slot("PREFACTOR", "parameter", "frequency_factor"),
          slot("BARRIER", "parameter", "activation_energy"),
          slot("GASCONST", "constant", "gas_constant"),
          slot("TEMPERATURE", "variable", "state_variable")],
         ["Log-linear in reciprocal temperature.",
          "Exponential argument is dimensionless: BARRIER is measured against thermal energy.",
          "Monotone increasing in TEMPERATURE for positive BARRIER."],
         [sym("k", "variable", "output", "Rate constant."),
          sym("A", "parameter", "frequency_factor", "Pre-exponential (frequency) factor."),
          sym("Ea", "parameter", "activation_energy", "Activation energy per mole."),
          sym("T", "variable", "state_variable", "Absolute temperature.")],
         [EQ, MUL, DIV, NEG],
         "The rate constant rises exponentially with temperature, controlled by the ratio of "
         "an activation barrier to the available thermal energy.",
         "Same exponential envelope as first-order decay, but the exponent is itself a ratio: "
         "a Boltzmann-factor archetype shared with any thermally activated process rather than "
         "a plain product in the exponent.",
         ["Single dominant elementary step over the fitted temperature range",
          "Temperature-independent PREFACTOR and BARRIER",
          "Absolute temperature scale"],
         [{"citation_key": "arrhenius1889",
           "bibliographic_entry": "Arrhenius, S. (1889). Ueber die Reaktionsgeschwindigkeit bei der Inversion von Rohrzucker durch Saeuren. Zeitschrift fuer Physikalische Chemie, 4, 226-248."},
          ATKINS],
         functionals=[EXP_FN],
         constants=[{"symbol": "R", "description": "Molar gas constant, shared with the ideal gas law."}],
         failure_modes=[
             "Curved Arrhenius plots arise from tunnelling, changing rate-determining steps, "
             "or a temperature-dependent pre-exponential factor."],
         inferential_links=links(
             composed_with=["chemistry.kinetics.rate_law_power"]),
         keywords=["Arrhenius", "activation energy", "Boltzmann factor", "kinetics"]),

    node("chemistry.spectroscopy.beer_lambert_law", "Beer-Lambert Law",
         "model_specification", "empirical", "spectroscopy", "absorption",
         "A = eps*l*c", "A = \\varepsilon\\, l\\, c",
         [{"form_id": "transmittance", "notation_system": "ascii",
           "expression": "A = -log10(I/I0)", "scope_note": "Absorbance from transmitted intensity"},
          {"form_id": "attenuation", "notation_system": "ascii",
           "expression": "I = I0*10^(-eps*l*c)", "scope_note": "Exponential attenuation form"}],
         "scaled_bilinear_product",
         "ABSORBANCE = ABSORPTIVITY * PATHLENGTH * CONCENTRATION",
         [slot("ABSORBANCE", "variable", "output"),
          slot("ABSORPTIVITY", "parameter", "material_coefficient"),
          slot("PATHLENGTH", "variable", "geometric_extent"),
          slot("CONCENTRATION", "variable", "amount_density")],
         ["Multilinear: absorbance doubles if any single factor doubles.",
          "Additive over independent absorbing species at the same wavelength.",
          "Zero absorbance whenever any factor vanishes."],
         [sym("A", "variable", "output", "Decadic absorbance (dimensionless)."),
          sym("eps", "parameter", "material_coefficient",
              "Molar absorption coefficient at the working wavelength."),
          sym("l", "variable", "geometric_extent", "Optical path length through the sample."),
          sym("c", "variable", "amount_density", "Amount concentration of the absorbing species.")],
         [EQ, MUL],
         "Absorbance is the product of a substance-specific absorption coefficient, the optical "
         "path length, and the concentration of absorber.",
         "A trilinear product whose skeleton is that of a rectangular prism's volume: one output "
         "measure built from three independent factors. Under typing it sits with the triangle "
         "area formula instead, because the absorptivity is a fixed material coefficient in the "
         "same slot position that geometry fills with the one-half constant.",
         ["Monochromatic, collimated incident light", "Dilute, homogeneous, non-scattering sample",
          "No photochemistry or saturation of the transition"],
         [{"citation_key": "beer1852",
           "bibliographic_entry": "Beer, A. (1852). Bestimmung der Absorption des rothen Lichts in farbigen Fluessigkeiten. Annalen der Physik und Chemie, 86, 78-88."},
          {"citation_key": "bouguer1729",
           "bibliographic_entry": "Bouguer, P. (1729). Essai d'optique sur la gradation de la lumiere. Paris: Claude Jombert."}],
         failure_modes=[
             "Linearity breaks above roughly 10 mM through solute-solute interaction and "
             "refractive-index change.",
             "Stray light and polychromatic sources bend the calibration curve toward saturation."],
         inferential_links=links(
             composed_with=["chemistry.solutions.molarity_definition"]),
         keywords=["Beer-Lambert", "absorbance", "spectrophotometry", "trilinear"]),

    node("chemistry.thermodynamics.gibbs_free_energy", "Gibbs Free Energy",
         "definition", "formal", "chemical_thermodynamics", "thermodynamic_potentials",
         "G = H - T*S", "G = H - T S",
         [{"form_id": "reaction_change", "notation_system": "ascii",
           "expression": "dG = dH - T*dS", "scope_note": "Change at constant temperature"},
          {"form_id": "equilibrium_relation", "notation_system": "ascii",
           "expression": "dG_standard = -R*T*ln(K)",
           "scope_note": "Link to the equilibrium constant"}],
         "signed_affine_combination",
         "FREE_ENERGY = ENTHALPY - TEMPERATURE * ENTROPY",
         [slot("FREE_ENERGY", "variable", "output"),
          slot("ENTHALPY", "variable", "energy_term"),
          slot("TEMPERATURE", "variable", "conjugate_intensive"),
          slot("ENTROPY", "variable", "conjugate_extensive")],
         ["Affine in ENTROPY at fixed TEMPERATURE, with slope -TEMPERATURE.",
          "Legendre transform of the enthalpy in the entropy-temperature conjugate pair.",
          "Extensive: scaling the system scales every term but TEMPERATURE."],
         [sym("G", "variable", "output", "Gibbs free energy."),
          sym("H", "variable", "energy_term", "Enthalpy."),
          sym("T", "variable", "conjugate_intensive", "Absolute temperature."),
          sym("S", "variable", "conjugate_extensive", "Entropy.")],
         [EQ, SUB, MUL],
         "The energy available to do non-expansion work is the enthalpy less the part of it "
         "bound up by temperature times entropy.",
         "A signed affine combination: the same skeleton as the statistical affine "
         "location-scale map except that the product term enters negated, which is precisely "
         "the sign that turns an offset into a trade-off between enthalpy and entropy.",
         ["Closed system at constant temperature and pressure",
          "Absolute temperature scale", "Well-defined equilibrium state"],
         [{"citation_key": "gibbs1878",
           "bibliographic_entry": "Gibbs, J. W. (1878). On the Equilibrium of Heterogeneous Substances. Transactions of the Connecticut Academy of Arts and Sciences, 3, 108-248, 343-524."},
          ATKINS],
         inferential_links=links(
             composed_with=["chemistry.thermodynamics.helmholtz_free_energy"]),
         keywords=["Gibbs energy", "spontaneity", "Legendre transform", "thermodynamic potential"]),

    node("chemistry.thermodynamics.helmholtz_free_energy", "Helmholtz Free Energy",
         "definition", "formal", "chemical_thermodynamics", "thermodynamic_potentials",
         "A = U - T*S", "A = U - T S",
         [{"form_id": "constant_volume_change", "notation_system": "ascii",
           "expression": "dA = dU - T*dS", "scope_note": "Change at constant temperature"},
          {"form_id": "gibbs_relation", "notation_system": "ascii",
           "expression": "G = A + P*V", "scope_note": "Relation to the Gibbs energy"}],
         "signed_affine_combination",
         "FREE_ENERGY = INTERNAL_ENERGY - TEMPERATURE * ENTROPY",
         [slot("FREE_ENERGY", "variable", "output"),
          slot("INTERNAL_ENERGY", "variable", "energy_term"),
          slot("TEMPERATURE", "variable", "conjugate_intensive"),
          slot("ENTROPY", "variable", "conjugate_extensive")],
         ["Affine in ENTROPY at fixed TEMPERATURE, with slope -TEMPERATURE.",
          "Legendre transform of the internal energy in the entropy-temperature conjugate pair.",
          "Differs from the Gibbs potential only in which energy term occupies the first slot."],
         [sym("A", "variable", "output", "Helmholtz free energy."),
          sym("U", "variable", "energy_term", "Internal energy."),
          sym("T", "variable", "conjugate_intensive", "Absolute temperature."),
          sym("S", "variable", "conjugate_extensive", "Entropy.")],
         [EQ, SUB, MUL],
         "The energy available to do total work at constant volume is the internal energy less "
         "temperature times entropy.",
         "Exact typed twin of the Gibbs free energy: the two thermodynamic potentials are the "
         "same Legendre transform applied to different energy terms, and the matcher recovers "
         "that identity from form alone, the way it recovers gravitation from Coulomb.",
         ["Closed system at constant temperature and volume",
          "Absolute temperature scale", "Well-defined equilibrium state"],
         [{"citation_key": "helmholtz1882",
           "bibliographic_entry": "Helmholtz, H. (1882). Die Thermodynamik chemischer Vorgaenge. Sitzungsberichte der Koeniglich Preussischen Akademie der Wissenschaften zu Berlin, 22-39."},
          ATKINS],
         inferential_links=links(
             composed_with=["chemistry.thermodynamics.gibbs_free_energy"]),
         keywords=["Helmholtz energy", "thermodynamic potential", "Legendre transform"]),

    node("chemistry.acid_base.ph_definition", "Definition of pH",
         "definition", "formal", "acid_base_chemistry", "acidity_scales",
         "pH = -log10(a_H)", "\\mathrm{pH} = -\\log_{10} a_{\\mathrm{H}^+}",
         [{"form_id": "concentration_approximation", "notation_system": "ascii",
           "expression": "pH = -log10([H+])",
           "scope_note": "Dilute-solution approximation with activity coefficient one"},
          {"form_id": "conjugate_scale", "notation_system": "ascii",
           "expression": "pX = -log10(X)", "scope_note": "General p-function, e.g. pKa, pOH"}],
         "negated_logarithmic_scale", "PH = -LOG(ACTIVITY)",
         [slot("PH", "variable", "output"),
          slot("ACTIVITY", "variable", "input")],
         ["Order-reversing: greater hydrogen-ion activity gives smaller PH.",
          "Decade-additive: a tenfold change in ACTIVITY shifts PH by exactly one unit.",
          "Argument must be dimensionless (activity, not raw concentration)."],
         [sym("pH", "variable", "output", "Acidity on the logarithmic p-scale."),
          sym("a_H", "variable", "input", "Relative activity of the hydrogen ion.")],
         [EQ, NEG],
         "Acidity is reported as the negative logarithm of hydrogen-ion activity, compressing "
         "many orders of magnitude onto a small linear scale.",
         "The generic p-function: a negated logarithmic rescaling that converts multiplicative "
         "structure into additive structure, which is what makes every downstream acid-base "
         "relation affine rather than multiplicative.",
         ["Aqueous solution at a stated temperature",
          "Activity referenced to the standard state"],
         [{"citation_key": "sorensen1909",
           "bibliographic_entry": "Sorensen, S. P. L. (1909). Enzymstudien II: Ueber die Messung und die Bedeutung der Wasserstoffionenkonzentration bei enzymatischen Prozessen. Biochemische Zeitschrift, 21, 131-304."},
          GREENBOOK],
         functionals=[LOG_FN],
         failure_modes=[
             "The concentration form fails at high ionic strength where activity coefficients "
             "depart from unity."],
         inferential_links=links(
             entails=["chemistry.acid_base.henderson_hasselbalch"]),
         keywords=["pH", "p-function", "logarithmic scale", "acidity"]),

    node("chemistry.acid_base.henderson_hasselbalch", "Henderson-Hasselbalch Equation",
         "proposition", "derived", "acid_base_chemistry", "buffers",
         "pH = pKa + log10([A-]/[HA])",
         "\\mathrm{pH} = \\mathrm{p}K_a + \\log_{10}\\frac{[\\mathrm{A}^-]}{[\\mathrm{HA}]}",
         [{"form_id": "base_form", "notation_system": "ascii",
           "expression": "pOH = pKb + log10([BH+]/[B])"},
          {"form_id": "ratio_solved", "notation_system": "ascii",
           "expression": "[A-]/[HA] = 10^(pH - pKa)"}],
         "log_ratio_offset", "PH = PKA + LOG(BASE / ACID)",
         [slot("PH", "variable", "output"),
          slot("PKA", "parameter", "reference_offset"),
          slot("BASE", "variable", "numerator_species"),
          slot("ACID", "variable", "denominator_species")],
         ["Affine in the logarithm of the base-to-acid ratio, with unit slope.",
          "PH equals PKA exactly when the two species are equimolar.",
          "Invariant under common dilution of both species, since only their ratio enters."],
         [sym("pH", "variable", "output", "Solution pH."),
          sym("pKa", "parameter", "reference_offset", "Negative logarithm of the acid dissociation constant."),
          sym("[A-]", "variable", "numerator_species", "Concentration of conjugate base."),
          sym("[HA]", "variable", "denominator_species", "Concentration of undissociated acid.")],
         [EQ, ADD, DIV],
         "The pH of a buffer is its pKa displaced by the logarithm of the ratio of conjugate "
         "base to weak acid.",
         "Composition of the ratio archetype inside the p-function: taking logarithms turns a "
         "multiplicative equilibrium expression into an offset-plus-log-ratio, the acid-base "
         "analogue of any calibration line written on a log axis.",
         ["Weak monoprotic acid", "Dilute solution with activity coefficients near one",
          "Analytical concentrations approximate equilibrium concentrations"],
         [{"citation_key": "henderson1908",
           "bibliographic_entry": "Henderson, L. J. (1908). Concerning the relationship between the strength of acids and their capacity to preserve neutrality. American Journal of Physiology, 21(2), 173-179."},
          {"citation_key": "hasselbalch1917",
           "bibliographic_entry": "Hasselbalch, K. A. (1917). Die Berechnung der Wasserstoffzahl des Blutes aus der freien und gebundenen Kohlensaeure desselben. Biochemische Zeitschrift, 78, 112-144."}],
         functionals=[LOG_FN],
         failure_modes=[
             "Unreliable when the ratio is far from unity or the acid is not weak, because the "
             "approximation that dissociation does not perturb the stated concentrations fails."],
         inferential_links=links(
             entailed_by=["chemistry.acid_base.ph_definition"]),
         keywords=["buffer", "Henderson-Hasselbalch", "pKa", "log ratio"]),

    node("chemistry.solutions.molarity_definition", "Molar Concentration",
         "definition", "formal", "solution_chemistry", "composition_measures",
         "c = n/V", "c = \\frac{n}{V}",
         [{"form_id": "verbose_form", "notation_system": "ascii",
           "expression": "molarity = moles_of_solute/volume_of_solution"},
          {"form_id": "from_mass", "notation_system": "ascii",
           "expression": "c = m/(M*V)", "scope_note": "Via molar mass M"}],
         "ratio_rate", "CONCENTRATION = AMOUNT / VOLUME",
         [slot("CONCENTRATION", "variable", "output"),
          slot("AMOUNT", "variable", "accumulated_quantity"),
          slot("VOLUME", "variable", "reference_extent")],
         ["Intensive quantity formed as the ratio of two extensive quantities.",
          "Invariant under splitting a homogeneous solution into portions.",
          "Undefined in the limit of vanishing volume."],
         [sym("c", "variable", "output", "Amount concentration (molarity)."),
          sym("n", "variable", "accumulated_quantity", "Amount of solute in moles."),
          sym("V", "variable", "reference_extent", "Volume of solution.")],
         [EQ, DIV],
         "Molar concentration is the amount of solute divided by the volume of solution "
         "that contains it.",
         "Exact typed twin of average speed and mass density: one extensive quantity per unit "
         "of a reference extent. The slots range over different physical dimensions, which is "
         "the whole point - the intensive-ratio move is discipline independent.",
         ["Homogeneous solution", "Volume measured for the solution, not the solvent",
          "Nonzero volume", "Stated temperature, since volume is temperature dependent"],
         [GREENBOOK, ATKINS],
         inferential_links=links(
             composed_with=["chemistry.spectroscopy.beer_lambert_law",
                            "physics.thermodynamics.ideal_gas_law"]),
         keywords=["molarity", "concentration", "intensive ratio", "solution"]),
]


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "chemistry.foundations.v1",
        "discipline": "chemistry",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data/chemistry/nodes.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {len(NODES)} chemistry nodes -> {out}")


if __name__ == "__main__":
    main()
