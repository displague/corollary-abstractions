#!/usr/bin/env python3
"""Seed data/economics/nodes.json with foundational economics/finance nodes.

Chosen to test the matcher's cross-discipline reach rather than to survey a
syllabus. Economics is a good adversarial corpus for the twin thesis because
its content is entirely social while its *forms* are borrowed wholesale from
the natural sciences, so any twin that fires is a pure form-level hit:

- Continuous compounding is the exponential archetype with a positive rate,
  present-value discounting the same archetype with a negative one. Under the
  matcher's `family` level -- which absorbs a negation into a free
  parameter-like coefficient -- the two collapse together with calculus'
  exponential growth law and chemistry's integrated first-order rate law. Money
  compounding, populations growing and reactants decaying are one statement.
- Price elasticity is an intensive ratio of two measured quantities, the same
  move as average rate of change, average speed, mass density and molarity.
- CAPM in risk-premium form and the Keynesian consumption function are affine
  maps, joining the location-scale transform and the tangent-line linearization.
- The equation of exchange is included specifically to probe a *predicted*
  twin with the ideal gas law (both "balanced product of state quantities");
  see the module note at QUANTITY_THEORY_NOTE for what actually happened.
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
APPROX = op("~=", "approximate equality", 2, "relational")
ADD = op("+", "addition", 2, "arithmetic")
MUL = op("*", "multiplication", 2, "arithmetic")
DIV = op("/", "division", 2, "arithmetic")
POW = op("^", "exponentiation", 2, "arithmetic")
NEG = op("-", "negation", 1, "arithmetic")

EXP_FN = {"notation": "EXP(.)", "name": "exponential", "input_arity": 1,
          "codomain": "positive reals",
          "description": "Natural exponential of a dimensionless argument."}

# The literal 1 in the interest templates is not decoration: it is the return
# of the principal itself, which is why these forms are affine rather than
# purely multiplicative in the rate.
UNIT_PRINCIPAL = {"symbol": "1", "value": 1,
                  "description": "Unit multiplier standing for return of the principal "
                                 "itself; the interest terms are what is added to it."}

# schema/equation-node.schema.json's constantToken takes {symbol, description,
# value?} -- a "name" key fails validation (see docs/BACKLOG.md).
EULER_E = {"symbol": "e", "value": 2.718281828459045,
           "description": "Base of natural logarithms; the limit of (1 + 1/m)^m, which is "
                          "exactly the continuous-compounding limit of the discrete form."}


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
    context = {"disciplines": disciplines or ["economics"],
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


QUANTITY_THEORY_NOTE = """The predicted equation-of-exchange <-> ideal-gas-law twin does NOT
fire, and the near miss is informative. Both are "balanced products of state
quantities", but the arities differ: MONEY*VELOCITY = PRICE_LEVEL*OUTPUT is
2x2, while PRESSURE*VOLUME = AMOUNT*CONSTANT*TEMPERATURE is 2x3 because the
gas law carries an explicit dimensional constant R. The matcher groups exact
skeletons, so *(?0,?1) = *(?2,?3) and *(?0,?1) = *(?2,?3,?4) stay apart. Only
the specialization/identity-element matching sketched in docs/BACKLOG.md
("Specialization matching (v2)") would unify them, by recognizing a suppressed
unit constant in the economics form. Recorded here rather than papered over by
inventing a spurious constant slot."""


FISHER_INTEREST = {"citation_key": "fisher1930",
                   "bibliographic_entry": "Fisher, I. (1930). The Theory of Interest, as Determined by Impatience to Spend Income and Opportunity to Invest It. New York: Macmillan."}
FISHER_MONEY = {"citation_key": "fisher1911",
                "bibliographic_entry": "Fisher, I. (1911). The Purchasing Power of Money: Its Determination and Relation to Credit, Interest and Crises. New York: Macmillan."}
KEYNES = {"citation_key": "keynes1936",
          "bibliographic_entry": "Keynes, J. M. (1936). The General Theory of Employment, Interest and Money. London: Macmillan."}
MARSHALL = {"citation_key": "marshall1890",
            "bibliographic_entry": "Marshall, A. (1890). Principles of Economics. London: Macmillan."}
VARIAN = {"citation_key": "varian1992",
          "bibliographic_entry": "Varian, H. R. (1992). Microeconomic Analysis (3rd ed.). New York: W. W. Norton."}
BKM = {"citation_key": "bodie2014",
       "bibliographic_entry": "Bodie, Z., Kane, A., Marcus, A. J. (2014). Investments (10th ed.). New York: McGraw-Hill Education."}
SNA = {"citation_key": "sna2008",
       "bibliographic_entry": "European Commission, IMF, OECD, United Nations, World Bank (2009). System of National Accounts 2008. New York: United Nations."}
ROMER = {"citation_key": "romer2019",
         "bibliographic_entry": "Romer, D. (2019). Advanced Macroeconomics (5th ed.). New York: McGraw-Hill Education."}


NODES = [
    node("economics.finance.continuous_compounding", "Continuous Compounding",
         "theorem", "derived", "financial_mathematics", "time_value_of_money",
         "V = P*exp(r*t)", "V(t) = P e^{r t}",
         [{"form_id": "discrete_limit", "notation_system": "ascii",
           "expression": "V = lim_m P*(1 + r/m)^(m*t)",
           "scope_note": "Continuous compounding as the limit of m compoundings per period"},
          {"form_id": "log_return", "notation_system": "ascii",
           "expression": "ln(V/P) = r*t",
           "scope_note": "Continuously compounded (log) return is linear in time"},
          {"form_id": "differential", "notation_system": "ascii",
           "expression": "dV/dt = r*V",
           "scope_note": "The growth law the closed form solves"}],
         "exponential_evolution", "VALUE = PRINCIPAL * EXP(RATE * TIME)",
         [slot("VALUE", "variable", "output"),
          slot("PRINCIPAL", "parameter", "initial_condition"),
          slot("RATE", "parameter", "rate_constant"),
          slot("TIME", "variable", "input")],
         ["Constant proportional increment per unit time: dV/dt = RATE*VALUE.",
          "Semilog-linear: LOG(VALUE) is affine in TIME with slope RATE.",
          "Scale free in the principal: doubling PRINCIPAL doubles VALUE at every TIME.",
          "Time-additive: the growth factor over an interval depends only on its length, "
          "so compounding over t1 then t2 equals compounding over t1 + t2."],
         [sym("V", "variable", "output", "Account value at time t."),
          sym("P", "parameter", "initial_condition", "Principal invested at t = 0."),
          sym("r", "parameter", "rate_constant",
              "Continuously compounded (force of) interest, per unit time."),
          sym("t", "variable", "input", "Elapsed time in the rate's units.")],
         [EQ, MUL],
         "Money left to compound without interruption grows by a fixed proportion of its "
         "current size, so value is the principal times an exponential in rate times time.",
         "Economics' entry into the exponential archetype. Its typed skeleton is identical "
         "to the calculus exponential growth law, and identical up to one sign to chemistry's "
         "integrated first-order rate law: the matcher's family level, which absorbs a "
         "negation into a free rate parameter, puts compounding interest, population growth "
         "and radioactive-style decay in one group. Nothing physical is shared; only the "
         "single-parameter multiplicative-increment form is.",
         ["Interest accrues continuously with no withdrawal or deposit",
          "Constant rate over the horizon", "Rate and time expressed in matching units"],
         [FISHER_INTEREST,
          {"citation_key": "bernoulli1690",
           "bibliographic_entry": "Bernoulli, J. (1690). Quaestiones nonnullae de usuris, cum solutione problematis de sorte alearum. Acta Eruditorum, May 1690, 219-223."},
          BKM],
         disciplines=["economics", "finance"],
         functionals=[EXP_FN],
         constants=[EULER_E],
         failure_modes=[
             "Quoted rates are usually nominal annual rates with a stated compounding "
             "frequency; substituting one for the force of interest overstates or "
             "understates growth.",
             "Fails once cash flows enter or leave the account, or once the rate is itself "
             "stochastic."],
         inferential_links=links(
             equivalent_to=["economics.finance.present_value_continuous"],
             composed_with=["economics.finance.compound_interest_discrete",
                            "calculus.growth.exponential_growth_law",
                            "calculus.differentiation.exponential_derivative"]),
         keywords=["compounding", "force of interest", "exponential growth",
                   "time value of money"]),

    node("economics.finance.present_value_continuous", "Continuous-Time Present Value",
         "theorem", "derived", "financial_mathematics", "discounting",
         "PV = FV*exp(-r*t)", "PV = FV\\, e^{-r t}",
         [{"form_id": "discount_factor", "notation_system": "ascii",
           "expression": "PV = FV*DF(t), DF(t) = exp(-r*t)",
           "scope_note": "Isolating the discount factor"},
          {"form_id": "discrete_discounting", "notation_system": "ascii",
           "expression": "PV = FV/(1 + r)^n",
           "scope_note": "Period-by-period discounting"},
          {"form_id": "log_form", "notation_system": "ascii",
           "expression": "ln(PV/FV) = -r*t"}],
         "exponential_decay", "PRESENT = FUTURE * EXP(-(RATE * HORIZON))",
         [slot("PRESENT", "variable", "output"),
          slot("FUTURE", "parameter", "terminal_condition"),
          slot("RATE", "parameter", "discount_rate"),
          slot("HORIZON", "variable", "input")],
         ["Constant proportional decrement per unit of deferral.",
          "Semilog-linear: LOG(PRESENT) is affine in HORIZON with slope -RATE.",
          "Multiplicatively separable in horizon: discounting over t1 then t2 equals "
          "discounting over t1 + t2, which is what makes discount factors chainable.",
          "Exact inverse of the continuous-compounding map at the same rate."],
         [sym("PV", "variable", "output", "Value today of a deferred amount."),
          sym("FV", "parameter", "terminal_condition", "Amount receivable at the horizon."),
          sym("r", "parameter", "discount_rate", "Continuously compounded discount rate."),
          sym("t", "variable", "input", "Deferral horizon.")],
         [EQ, MUL, NEG],
         "A sum receivable later is worth less today by an exponential factor in the "
         "discount rate times the waiting time.",
         "The decay-signed member of the exponential archetype from the economics side, and "
         "therefore an exact typed twin of chemistry's integrated first-order rate law: "
         "`PRESENT = FUTURE * EXP(-(RATE * HORIZON))` and "
         "`AMOUNT = INITIAL * EXP(-(RATECONST * TIME))` are the same statement. The pairing "
         "is unusually apt -- both say the future is discounted at a constant proportional "
         "rate, one by impatience and one by decay probability.",
         ["Constant discount rate over the horizon", "A single certain cash flow",
          "Rate and horizon in matching units"],
         [FISHER_INTEREST, BKM],
         disciplines=["economics", "finance"],
         functionals=[EXP_FN],
         constants=[EULER_E],
         failure_modes=[
             "A single flat rate misprices cash flows when the term structure is not flat; "
             "each maturity needs its own zero-coupon rate.",
             "Risky cash flows require either a risk-adjusted rate or risk-neutral "
             "expectation, not this deterministic factor."],
         inferential_links=links(
             equivalent_to=["economics.finance.continuous_compounding"],
             composed_with=["economics.finance.capm_expected_return",
                            "economics.macroeconomics.fisher_equation",
                            "chemistry.kinetics.first_order_integrated_rate_law"]),
         keywords=["present value", "discounting", "discount factor", "exponential decay"]),

    node("economics.finance.simple_interest", "Simple Interest Accumulation",
         "definition", "formal", "financial_mathematics", "time_value_of_money",
         "V = P*(1 + r*t)", "V = P(1 + r t)",
         [{"form_id": "interest_isolated", "notation_system": "ascii",
           "expression": "I = P*r*t, V = P + I",
           "scope_note": "Interest earned separated from the principal"},
          {"form_id": "accumulation_factor", "notation_system": "ascii",
           "expression": "V/P = 1 + r*t",
           "scope_note": "Accumulation factor per unit of principal"}],
         "affine_accumulation_factor", "VALUE = PRINCIPAL * (1 + RATE * TIME)",
         [slot("VALUE", "variable", "output"),
          slot("PRINCIPAL", "parameter", "initial_condition"),
          slot("RATE", "parameter", "rate_constant"),
          slot("TIME", "variable", "input")],
         ["Affine in TIME at fixed rate, with slope PRINCIPAL*RATE: interest does not "
          "itself earn interest.",
          "Homogeneous of degree one in PRINCIPAL.",
          "Reduces to the principal at TIME = 0, since the unit term returns the principal.",
          "First-order Taylor expansion of the compounded forms in RATE*TIME, so it "
          "understates them for all positive rate-time products."],
         [sym("V", "variable", "output", "Accumulated value."),
          sym("P", "parameter", "initial_condition", "Principal."),
          sym("r", "parameter", "rate_constant", "Simple interest rate per unit time."),
          sym("t", "variable", "input", "Elapsed time.")],
         [EQ, ADD, MUL],
         "Under simple interest only the original principal earns, so value grows linearly "
         "in time rather than exponentially.",
         "The linear degeneration of the exponential archetype: the same four slots in the "
         "same roles, but the accumulation factor is the exponential's first-order truncation "
         "`1 + RATE*TIME` instead of `EXP(RATE*TIME)`. The matcher keeps them apart, correctly "
         "-- an approximation and the thing it approximates are not the same form -- but the "
         "pair is exactly the specialization relation docs/BACKLOG.md wants a v2 matcher to see.",
         ["Interest computed on the original principal only",
          "Constant rate", "No intermediate capitalization"],
         [FISHER_INTEREST,
          {"citation_key": "kellison2008",
           "bibliographic_entry": "Kellison, S. G. (2008). The Theory of Interest (3rd ed.). New York: McGraw-Hill/Irwin."}],
         disciplines=["economics", "finance"],
         constants=[UNIT_PRINCIPAL],
         failure_modes=[
             "Diverges badly from compounded value over long horizons or high rates; usable "
             "mainly for sub-annual money-market conventions."],
         inferential_links=links(
             composed_with=["economics.finance.compound_interest_discrete"]),
         keywords=["simple interest", "accumulation factor", "linear growth"]),

    node("economics.finance.compound_interest_discrete", "Discrete Compound Interest",
         "theorem", "derived", "financial_mathematics", "time_value_of_money",
         "V = P*(1 + r)^n", "V_n = P(1 + r)^{n}",
         [{"form_id": "sub_period", "notation_system": "ascii",
           "expression": "V = P*(1 + r/m)^(m*t)",
           "scope_note": "m compoundings per period over t periods"},
          {"form_id": "effective_rate", "notation_system": "ascii",
           "expression": "1 + r_eff = (1 + r/m)^m",
           "scope_note": "Effective annual rate from a nominal rate"},
          {"form_id": "log_form", "notation_system": "ascii",
           "expression": "ln(V/P) = n*ln(1 + r)",
           "scope_note": "Linear in the number of periods on a log scale"}],
         "geometric_accumulation", "VALUE = PRINCIPAL * (1 + RATE)^PERIODS",
         [slot("VALUE", "variable", "output"),
          slot("PRINCIPAL", "parameter", "initial_condition"),
          slot("RATE", "parameter", "rate_constant"),
          slot("PERIODS", "variable", "input")],
         ["Geometric in PERIODS: each period multiplies value by the same factor.",
          "Log-linear in PERIODS with slope LOG(1 + RATE).",
          "Homogeneous of degree one in PRINCIPAL.",
          "Tends to the continuous-compounding form as the compounding frequency grows "
          "without bound, which is where the base of natural logarithms enters finance."],
         [sym("V", "variable", "output", "Value after n periods."),
          sym("P", "parameter", "initial_condition", "Principal."),
          sym("r", "parameter", "rate_constant", "Periodic interest rate."),
          sym("n", "variable", "input", "Number of compounding periods.")],
         [EQ, ADD, MUL, POW],
         "When interest is capitalized each period, value is the principal times the "
         "per-period growth factor raised to the number of periods.",
         "A power-law in the accumulation factor rather than in a measured quantity: the "
         "exponent slot is the *variable* and the base is built from the parameter, which is "
         "the mirror image of chemistry's power-law rate law and geometry's scaled powers, "
         "where the base varies and the exponent is fixed. Same `^` node, opposite slot "
         "typing -- a case where the typed level earns its keep by refusing the match.",
         ["Interest capitalized at the end of each period",
          "Constant periodic rate", "Whole or fractional periods measured consistently"],
         [{"citation_key": "bernoulli1690",
           "bibliographic_entry": "Bernoulli, J. (1690). Quaestiones nonnullae de usuris, cum solutione problematis de sorte alearum. Acta Eruditorum, May 1690, 219-223."},
          FISHER_INTEREST, BKM],
         disciplines=["economics", "finance"],
         constants=[UNIT_PRINCIPAL],
         failure_modes=[
             "Comparing quoted rates without converting to a common effective rate confuses "
             "nominal with effective compounding.",
             "Negative rates make the base less than one and can invert the usual monotonicity "
             "arguments."],
         inferential_links=links(
             composed_with=["economics.finance.simple_interest",
                            "economics.finance.continuous_compounding"]),
         keywords=["compound interest", "geometric growth", "effective rate",
                   "power law"]),

    node("economics.microeconomics.price_elasticity_of_demand",
         "Price Elasticity of Demand",
         "definition", "formal", "microeconomics", "demand_response",
         "E = pct_change_Q / pct_change_P",
         "\\varepsilon = \\frac{\\%\\Delta Q}{\\%\\Delta P}",
         [{"form_id": "point_elasticity", "notation_system": "ascii",
           "expression": "E = (dQ/dP)*(P/Q)",
           "scope_note": "Limiting form as the price change goes to zero"},
          {"form_id": "log_derivative", "notation_system": "ascii",
           "expression": "E = d(ln Q)/d(ln P)",
           "scope_note": "Elasticity as a log-log slope"},
          {"form_id": "arc_elasticity", "notation_system": "ascii",
           "expression": "E = ((Q2-Q1)/((Q1+Q2)/2))/((P2-P1)/((P1+P2)/2))",
           "scope_note": "Midpoint formula used for finite changes"}],
         "ratio_rate", "ELASTICITY = PCT_QUANTITY / PCT_PRICE",
         [slot("ELASTICITY", "variable", "output"),
          slot("PCT_QUANTITY", "variable", "accumulated_quantity"),
          slot("PCT_PRICE", "variable", "reference_extent")],
         ["Dimensionless: both arguments are relative changes, so the value is invariant "
          "to the units of price and of quantity.",
          "Invariant to currency redenomination and to the choice of quantity unit, which "
          "is precisely why elasticities are comparable across markets.",
          "Undefined in the limit of vanishing price change.",
          "Negative for ordinary demand; the sign carries the law of demand and is often "
          "suppressed by reporting the magnitude."],
         [sym("E", "variable", "output", "Own-price elasticity of demand."),
          sym("pct_change_Q", "variable", "accumulated_quantity",
              "Proportional change in quantity demanded."),
          sym("pct_change_P", "variable", "reference_extent",
              "Proportional change in own price.")],
         [EQ, DIV],
         "Elasticity is the proportional response of quantity demanded to a proportional "
         "change in price -- how much buyers move, per unit of how much the price moved.",
         "Exact typed twin of the ratio archetype already held by calculus' average rate of "
         "change, physics' average speed and mass density, and chemistry's molarity: one "
         "measured quantity per unit of a measured reference extent, with all slots "
         "variable-like. Elasticity is the most abstract member of that group because both "
         "of its arguments are already dimensionless, which is what lets it compare a "
         "grocery market to an airline route.",
         ["Own price varies while other prices, income and tastes are held fixed",
          "Nonzero price change", "Movement along a fixed demand curve, not a shift of it"],
         [MARSHALL, VARIAN],
         failure_modes=[
             "Point and arc formulas disagree for large price changes; the midpoint form "
             "exists only to make the discrepancy symmetric.",
             "Estimating it from observed price-quantity pairs recovers neither the demand "
             "nor the supply elasticity without an instrument -- the classic identification "
             "problem."],
         inferential_links=links(
             composed_with=["calculus.differentiation.average_rate_of_change"]),
         keywords=["elasticity", "demand", "intensive ratio", "dimensionless"]),

    node("economics.macroeconomics.gdp_expenditure_identity",
         "GDP Expenditure Identity",
         "identity", "formal", "macroeconomics", "national_accounts",
         "Y = C + I + G + NX", "Y = C + I + G + (X - M)",
         [{"form_id": "explicit_trade", "notation_system": "ascii",
           "expression": "Y = C + I + G + X - M",
           "scope_note": "Net exports written as exports less imports"},
          {"form_id": "closed_economy", "notation_system": "ascii",
           "expression": "Y = C + I + G",
           "scope_note": "Closed-economy special case, NX = 0"},
          {"form_id": "saving_investment", "notation_system": "ascii",
           "expression": "S = I + NX",
           "scope_note": "Rearrangement giving the saving-investment balance"}],
         "additive_decomposition",
         "OUTPUT = CONSUMPTION + INVESTMENT + GOVERNMENT + NET_EXPORTS",
         [slot("OUTPUT", "variable", "output"),
          slot("CONSUMPTION", "variable", "component"),
          slot("INVESTMENT", "variable", "component"),
          slot("GOVERNMENT", "variable", "component"),
          slot("NET_EXPORTS", "variable", "component")],
         ["Exhaustive and mutually exclusive: every unit of final expenditure lands in "
          "exactly one component.",
          "Additive and unit-homogeneous: all terms carry the same currency-per-period units.",
          "Holds ex post for any period by construction, whatever behaviour generated it.",
          "Only NET_EXPORTS may be negative, so the decomposition is not a partition of "
          "a positive quantity into positive parts."],
         [sym("Y", "variable", "output", "Gross domestic product at market prices."),
          sym("C", "variable", "component", "Household final consumption expenditure."),
          sym("I", "variable", "component", "Gross capital formation."),
          sym("G", "variable", "component", "Government final consumption expenditure."),
          sym("NX", "variable", "component", "Net exports of goods and services.")],
         [EQ, ADD],
         "Total output equals the sum of what households, firms, government and the rest of "
         "the world spend on final goods and services.",
         "A pure additive decomposition, and deliberately the corpus's clearest example of a "
         "statement with no empirical content: it is true by the construction of the accounts, "
         "the way a partition sums to the whole. Its structural neighbours are the "
         "law-of-total-probability decomposition in the statistics corpus, which sums "
         "weighted parts to a whole, though the matcher separates them because that one "
         "carries an index and a weight and this one does not.",
         ["Final expenditure only; intermediate goods are netted out",
          "A single consistently valued accounting period",
          "Components measured at the same prices, all nominal or all real"],
         [SNA,
          {"citation_key": "kuznets1934",
           "bibliographic_entry": "Kuznets, S. (1934). National Income, 1929-1932. Senate Document No. 124, 73rd Congress, 2nd Session. Washington: US Government Printing Office."},
          ROMER],
         failure_modes=[
             "Statistical discrepancy: the expenditure, income and production measures of "
             "the same total differ in practice because they are collected separately.",
             "Non-market production, unpaid work and the informal sector fall outside the "
             "boundary, so the identity is exact only for what is inside it."],
         inferential_links=links(
             composed_with=["economics.macroeconomics.keynesian_consumption_function",
                            "economics.monetary.equation_of_exchange",
                            "economics.production.cobb_douglas_production_function"]),
         keywords=["GDP", "national accounts", "identity", "additive decomposition"]),

    node("economics.monetary.equation_of_exchange",
         "Equation of Exchange (Quantity Theory of Money)",
         "identity", "formal", "monetary_economics", "money_and_prices",
         "M*V = P*Q", "M V = P Q",
         [{"form_id": "nominal_output", "notation_system": "ascii",
           "expression": "M*V = P*Y",
           "scope_note": "With real output Y in place of transaction volume Q"},
          {"form_id": "growth_rates", "notation_system": "ascii",
           "expression": "g_M + g_V = g_P + g_Y",
           "scope_note": "Log-differentiated form used for inflation accounting"},
          {"form_id": "velocity_definition", "notation_system": "ascii",
           "expression": "V = P*Q/M",
           "scope_note": "The definition that makes the equation an identity"}],
         "balanced_product_relation", "MONEY * VELOCITY = PRICE_LEVEL * OUTPUT",
         [slot("MONEY", "variable", "state_variable"),
          slot("VELOCITY", "variable", "state_variable"),
          slot("PRICE_LEVEL", "variable", "state_variable"),
          slot("OUTPUT", "variable", "state_variable")],
         ["Balanced bilinear relation: the product on each side is the same nominal "
          "transaction volume, so all four slots carry compatible units.",
          "Scale invariant in a joint sense: doubling MONEY with VELOCITY and OUTPUT fixed "
          "forces PRICE_LEVEL to double.",
          "Any one slot is determined by the other three; velocity is the slot that is "
          "residually defined rather than independently measured.",
          "Log-additive: the identity becomes a sum of growth rates under differentiation."],
         [sym("M", "variable", "state_variable", "Money stock on a stated aggregate."),
          sym("V", "variable", "state_variable", "Income velocity of money."),
          sym("P", "variable", "state_variable", "Price level (deflator or index)."),
          sym("Q", "variable", "state_variable", "Real volume of transactions or output.")],
         [EQ, MUL],
         "The money stock times the rate at which it turns over equals the price level times "
         "real output: every transaction is a payment on one side and a good on the other.",
         "Included to probe a predicted twin with the ideal gas law, and the probe came back "
         "negative -- see the module-level QUANTITY_THEORY_NOTE. Both statements are "
         "'balanced products of state quantities' and both are read as 'raise one factor and "
         "another must give', but the gas law carries an explicit dimensional constant, "
         "making it a 2x3 product against this 2x2 one, so the exact-skeleton matcher keeps "
         "them apart. The near miss is the sharpest live argument in this corpus for the "
         "specialization matching queued in the backlog.",
         ["A stated monetary aggregate and a matching measure of transactions",
          "Velocity defined residually, which is what makes the relation an identity",
          "Consistent nominal-versus-real accounting on the two sides"],
         [FISHER_MONEY,
          {"citation_key": "friedman1956",
           "bibliographic_entry": "Friedman, M. (1956). The Quantity Theory of Money: A Restatement. In M. Friedman (Ed.), Studies in the Quantity Theory of Money (pp. 3-21). Chicago: University of Chicago Press."},
          ROMER],
         failure_modes=[
             "The identity is empty until velocity is assumed stable; the quantity *theory* "
             "is that behavioural assumption, not the equation, and velocity has been "
             "visibly unstable since the 1980s.",
             "Results depend on which monetary aggregate is chosen, and the aggregates "
             "diverge."],
         inferential_links=links(
             composed_with=["economics.macroeconomics.gdp_expenditure_identity",
                            "physics.thermodynamics.ideal_gas_law"]),
         keywords=["quantity theory", "velocity of money", "equation of exchange",
                   "inflation"]),

    node("economics.production.cobb_douglas_production_function",
         "Cobb-Douglas Production Function",
         "model_specification", "empirical", "production_theory", "production_functions",
         "Y = A*K^alpha*L^beta", "Y = A K^{\\alpha} L^{\\beta}",
         [{"form_id": "constant_returns", "notation_system": "ascii",
           "expression": "Y = A*K^alpha*L^(1-alpha)",
           "scope_note": "Constant-returns-to-scale restriction beta = 1 - alpha"},
          {"form_id": "log_linear", "notation_system": "ascii",
           "expression": "ln(Y) = ln(A) + alpha*ln(K) + beta*ln(L)",
           "scope_note": "The form actually estimated"},
          {"form_id": "intensive", "notation_system": "ascii",
           "expression": "y = A*k^alpha",
           "scope_note": "Per-worker form under constant returns"}],
         "scaled_power_product",
         "OUTPUT = PRODUCTIVITY * CAPITAL^CAPITAL_SHARE * LABOR^LABOR_SHARE",
         [slot("OUTPUT", "variable", "output"),
          slot("PRODUCTIVITY", "parameter", "scale_coefficient"),
          slot("CAPITAL", "variable", "input"),
          slot("CAPITAL_SHARE", "parameter", "power_exponent"),
          slot("LABOR", "variable", "input"),
          slot("LABOR_SHARE", "parameter", "power_exponent")],
         ["Homogeneous of degree CAPITAL_SHARE + LABOR_SHARE, so returns to scale are read "
          "straight off the exponents.",
          "Log-log linear in both inputs, which is the entire reason for its empirical "
          "popularity.",
          "Unit elasticity of substitution between the two inputs, everywhere.",
          "Exponents equal factor income shares under competitive pricing, so the parameters "
          "are observable in the national accounts.",
          "Output is zero if either input is zero: the inputs are essential, not substitutes."],
         [sym("Y", "variable", "output", "Real output."),
          sym("A", "parameter", "scale_coefficient", "Total factor productivity."),
          sym("K", "variable", "input", "Capital services."),
          sym("alpha", "parameter", "power_exponent", "Output elasticity of capital."),
          sym("L", "variable", "input", "Labour input."),
          sym("beta", "parameter", "power_exponent", "Output elasticity of labour.")],
         [EQ, MUL, POW],
         "Output is a productivity level times capital and labour each raised to a fixed "
         "exponent, so each input has a constant output elasticity.",
         "The two-factor generalization of the scaled power law that chemistry states with "
         "one factor (`RATE = RATECONST * CONCENTRATION^ORDER`). Same construction -- a scale "
         "coefficient multiplying inputs at symbolic exponents fitted rather than derived -- "
         "and the same epistemic status, empirical rather than formal. The matcher does not "
         "group them, since one product has two power factors and the other has one, which "
         "is again the specialization gap: this is the arity-extended sibling, not a twin.",
         ["Inputs measured as flows of services over the same period",
          "Exponents constant over the fitted sample",
          "Competitive factor markets if the exponents are to be read as income shares"],
         [{"citation_key": "cobb1928",
           "bibliographic_entry": "Cobb, C. W., Douglas, P. H. (1928). A Theory of Production. American Economic Review, 18(1), 139-165."},
          {"citation_key": "solow1957",
           "bibliographic_entry": "Solow, R. M. (1957). Technical Change and the Aggregate Production Function. Review of Economics and Statistics, 39(3), 312-320."},
          ROMER],
         failure_modes=[
             "Unit elasticity of substitution is an assumption, not a finding; CES forms "
             "nest it as a special case and generally reject it.",
             "The log-linear fit recovers shares rather than technology when the accounting "
             "identity itself generates the correlation (the Shaikh critique).",
             "Aggregating heterogeneous capital into a single K is not innocuous."],
         inferential_links=links(
             composed_with=["economics.macroeconomics.gdp_expenditure_identity",
                            "chemistry.kinetics.rate_law_power"]),
         keywords=["Cobb-Douglas", "production function", "returns to scale",
                   "power law", "factor shares"]),

    node("economics.finance.capm_expected_return",
         "CAPM Expected Return (Risk-Premium Form)",
         "model_specification", "derived", "asset_pricing", "risk_and_return",
         "E[Ri] = rf + beta_i*MRP", "\\mathbb{E}[R_i] = r_f + \\beta_i\\,\\mathrm{MRP}",
         [{"form_id": "market_excess", "notation_system": "ascii",
           "expression": "E[Ri] = rf + beta_i*(E[Rm] - rf)",
           "scope_note": "Risk premium written out as market excess return"},
          {"form_id": "beta_definition", "notation_system": "ascii",
           "expression": "beta_i = Cov(Ri, Rm)/Var(Rm)",
           "scope_note": "The slot that carries the asset's identity"},
          {"form_id": "excess_return", "notation_system": "ascii",
           "expression": "E[Ri] - rf = beta_i*(E[Rm] - rf)",
           "scope_note": "Security market line through the origin in excess returns"}],
         "affine_operator", "EXPECTED = RISKFREE + SENSITIVITY * PREMIUM",
         [slot("EXPECTED", "variable", "output"),
          slot("RISKFREE", "parameter", "anchor_value"),
          slot("SENSITIVITY", "parameter", "linear_factor"),
          slot("PREMIUM", "variable", "input")],
         ["Affine in the market premium, with intercept RISKFREE and slope SENSITIVITY.",
          "Reduces to the risk-free rate when SENSITIVITY is zero: only covariance with the "
          "market is compensated.",
          "Linear in SENSITIVITY, so portfolio expected return is the value-weighted average "
          "of its holdings' expected returns.",
          "Idiosyncratic risk enters nowhere in the form, which is the theorem's whole claim."],
         [sym("E[Ri]", "variable", "output", "Expected return on asset i."),
          sym("rf", "parameter", "anchor_value", "Risk-free rate of return."),
          sym("beta_i", "parameter", "linear_factor",
              "Sensitivity of the asset's return to the market return."),
          sym("MRP", "variable", "input",
              "Market risk premium, the market's expected excess return.")],
         [EQ, ADD, MUL],
         "An asset's expected return is the risk-free rate plus its sensitivity to market "
         "risk times the price the market charges for bearing that risk.",
         "Joins the affine family at the typed level with the statistics location-scale "
         "transform (`OUT = SCALE*IN + SHIFT`) and the calculus tangent-line linearization "
         "(`LINEARIZED = BASEVALUE + SLOPE*DISPLACEMENT`) -- all three are "
         "`?0:V = +(?1:P, *(?2:P, ?3:V))`, an anchor displaced by a scaled input. That the "
         "anchor is a risk-free rate, a function value at a point, or a distributional "
         "location is invisible to the form, which is the twin thesis in miniature.",
         ["Mean-variance optimizing investors over a single period",
          "Homogeneous expectations and a risk-free asset available to all",
          "The market portfolio is the relevant, and observable, benchmark"],
         [{"citation_key": "sharpe1964",
           "bibliographic_entry": "Sharpe, W. F. (1964). Capital Asset Prices: A Theory of Market Equilibrium under Conditions of Risk. Journal of Finance, 19(3), 425-442."},
          {"citation_key": "lintner1965",
           "bibliographic_entry": "Lintner, J. (1965). The Valuation of Risk Assets and the Selection of Risky Investments in Stock Portfolios and Capital Budgets. Review of Economics and Statistics, 47(1), 13-37."},
          {"citation_key": "fama2004",
           "bibliographic_entry": "Fama, E. F., French, K. R. (2004). The Capital Asset Pricing Model: Theory and Evidence. Journal of Economic Perspectives, 18(3), 25-46."},
          BKM],
         disciplines=["economics", "finance"],
         failure_modes=[
             "The market portfolio is unobservable, so every test is a joint test of the "
             "model and the chosen proxy (Roll's critique).",
             "Empirically the security market line is too flat, and size, value and momentum "
             "carry premia the single beta does not explain."],
         inferential_links=links(
             composed_with=["economics.finance.present_value_continuous",
                            "probstat.transform.affine_location_scale"]),
         keywords=["CAPM", "beta", "risk premium", "affine", "asset pricing"]),

    node("economics.macroeconomics.keynesian_consumption_function",
         "Keynesian Consumption Function",
         "model_specification", "empirical", "macroeconomics", "consumption",
         "C = a + b*Yd", "C = a + b\\,Y_d",
         [{"form_id": "average_propensity", "notation_system": "ascii",
           "expression": "C/Yd = a/Yd + b",
           "scope_note": "Average propensity falls toward the marginal one as income rises"},
          {"form_id": "marginal_propensity", "notation_system": "ascii",
           "expression": "dC/dYd = b",
           "scope_note": "The marginal propensity to consume as a derivative"},
          {"form_id": "multiplier", "notation_system": "ascii",
           "expression": "dY/dG = 1/(1 - b)",
           "scope_note": "The expenditure multiplier this specification implies"}],
         "affine_operator", "CONSUMPTION = AUTONOMOUS + PROPENSITY * DISPOSABLE_INCOME",
         [slot("CONSUMPTION", "variable", "output"),
          slot("AUTONOMOUS", "parameter", "anchor_value"),
          slot("PROPENSITY", "parameter", "linear_factor"),
          slot("DISPOSABLE_INCOME", "variable", "input")],
         ["Affine in income with constant slope PROPENSITY, strictly between zero and one.",
          "Average propensity exceeds the marginal one whenever AUTONOMOUS is positive, and "
          "falls monotonically toward it as income rises.",
          "Positive consumption at zero income, financed by dissaving.",
          "Because the slope is below one, the implied expenditure multiplier 1/(1 - "
          "PROPENSITY) is finite and greater than one."],
         [sym("C", "variable", "output", "Aggregate real consumption."),
          sym("a", "parameter", "anchor_value", "Autonomous consumption at zero income."),
          sym("b", "parameter", "linear_factor", "Marginal propensity to consume."),
          sym("Yd", "variable", "input", "Real disposable income.")],
         [EQ, ADD, MUL],
         "Consumption is a fixed autonomous amount plus a constant fraction of disposable "
         "income, with that fraction less than one.",
         "The second economics member of the affine family, and the one that shows why the "
         "family matters: written as a stochastic relation it is literally the simple linear "
         "regression specification from the statistics corpus, with the marginal propensity "
         "to consume in the slope slot. Structure travels between a behavioural postulate and "
         "an estimator without changing shape, which is exactly the identification hazard "
         "econometrics spent decades on.",
         ["Aggregate income and consumption in real terms over the same period",
          "Propensity stable over the sample",
          "Income taken as given rather than jointly determined with consumption"],
         [KEYNES,
          {"citation_key": "friedman1957",
           "bibliographic_entry": "Friedman, M. (1957). A Theory of the Consumption Function. Princeton: Princeton University Press."},
          ROMER],
         failure_modes=[
             "Fails in long-run and cross-section data, where the average propensity is "
             "roughly constant; permanent-income and life-cycle theories were built to "
             "explain that failure.",
             "Regressing consumption on income conflates the behavioural slope with the "
             "accounting identity linking the two, so the estimate is not the parameter."],
         inferential_links=links(
             composed_with=["economics.macroeconomics.gdp_expenditure_identity",
                            "probstat.regression.slr_conditional_expectation"]),
         keywords=["consumption function", "marginal propensity to consume", "multiplier",
                   "affine", "Keynes"]),

    node("economics.macroeconomics.fisher_equation", "Fisher Equation (Additive Form)",
         "approximation", "derived", "monetary_economics", "interest_and_inflation",
         "i approx r + pi", "i \\approx r + \\pi",
         [{"form_id": "exact", "notation_system": "ascii",
           "expression": "(1 + i) = (1 + r)*(1 + pi)",
           "scope_note": "The exact multiplicative relation the additive form approximates"},
          {"form_id": "real_rate_solved", "notation_system": "ascii",
           "expression": "r = (1 + i)/(1 + pi) - 1",
           "scope_note": "Exact real rate"},
          {"form_id": "ex_ante", "notation_system": "ascii",
           "expression": "i approx r + E[pi]",
           "scope_note": "Ex ante form with expected rather than realized inflation"}],
         "additive_approximation", "NOMINAL approx REAL + INFLATION",
         [slot("NOMINAL", "variable", "output"),
          slot("REAL", "variable", "component"),
          slot("INFLATION", "variable", "component")],
         ["Error is exactly the cross term REAL*INFLATION, so accuracy degrades as the "
          "product of the two rates grows.",
          "Additive and symmetric in its two components, unlike the exact multiplicative form.",
          "Exact in the continuously compounded convention, where log rates add without "
          "remainder.",
          "Unit slope in each component: a point of inflation passes one for one into the "
          "nominal rate, which is the Fisher effect."],
         [sym("i", "variable", "output", "Nominal interest rate."),
          sym("r", "variable", "component", "Real interest rate."),
          sym("pi", "variable", "component", "Inflation rate over the same horizon.")],
         [APPROX, ADD],
         "The nominal interest rate is approximately the real rate plus inflation, so lenders "
         "are compensated for both waiting and for the erosion of the currency.",
         "The corpus's clearest case of an approximation node carrying its exactness "
         "condition in the notation rather than in prose: the relation is `approx` under "
         "simple compounding and `=` under continuous compounding, because taking logs turns "
         "the exact product into an exact sum. Structurally it is the additive shadow of the "
         "multiplicative accumulation factors in the interest nodes.",
         ["Rates quoted for the same horizon and compounding convention",
          "Small rates, so the cross term is negligible",
          "Realized inflation for the ex post form, expected inflation for the ex ante one"],
         [FISHER_INTEREST, FISHER_MONEY, ROMER],
         failure_modes=[
             "The approximation is poor under high inflation, exactly when the real rate "
             "matters most.",
             "The ex ante real rate is unobservable, so empirical work substitutes a forecast "
             "and inherits its error.",
             "One-for-one pass-through of inflation is an equilibrium claim that fails over "
             "short horizons when nominal rates are sticky or at the effective lower bound."],
         inferential_links=links(
             composed_with=["economics.finance.present_value_continuous"]),
         keywords=["Fisher equation", "real interest rate", "inflation", "approximation"]),
]


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "economics.foundations.v1",
        "discipline": "economics",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data/economics/nodes.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {len(NODES)} economics nodes -> {out}")


if __name__ == "__main__":
    main()
