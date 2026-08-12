#!/usr/bin/env python3
"""Seed data/number_theory/nodes.json — parity, primality, and irrationality.

v0.10 item 1 (cont.): the coverage instrument measured the relational/predicate
family as the largest named gap on the three committed sources, and the
predicate-head frequency ranking inside Goedel-Pset's `no_relation_in_goal`
bucket put integer parity (`Even`/`Odd`), primality (`Nat.Prime`, bare and
negated), and irrationality (`Irrational`, mostly over square roots) at the top
of the genuinely-predicate remainder. A head is only legitimate once a corpus
node carries it, so this seed authors the canonical statements that DEFINE the
EVEN/ODD/PRIME/IRRATIONAL heads: the parity algebra of sums and products, the
even/odd dichotomy, the primality of two and its uniqueness among evens, and the
irrationality of square roots of primes with its classical instance sqrt(2).

These are Prop-valued (P-typed) heads, in the same head-algebra as logic's
MEET/JOIN/NEG and provability's IMPLIES/BOX: a predicate applied to an integer
slot yields a proposition, and the propositional connectives compose them. That
is exactly the shape the classifier now accepts from ingested Lean statements
(`Even (n^2 + n)`, `¬ Nat.Prime 100`, `Irrational (Real.sqrt 3)`).

Small, canonical exemplars, not invented scale: they establish the heads so
ingested predicate statements have something to reduce onto.

The v0.10 quantifier slice adds the two existential witness DEFINITIONS
(even(n) = ∃k, n = 2k and odd(n) = ∃k, n = 2k+1): they tie this discipline's
predicate heads to the EXISTS binder head that data/logic's quantifier laws
define, so an ingested parity witness (`∃ k, n = 2 * k`) is honestly
expressible rather than a quantifier gap.
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
MUL = op("*", "multiplication", 2, "arithmetic")
AND = op("and", "conjunction", 2, "logical")
OR = op("or", "disjunction", 2, "logical")
NOT = op("not", "negation", 1, "logical")
IMP = op("implies", "material implication / meta-level inference", 2, "logical")

EVEN_FN = {"notation": "EVEN(.)", "name": "evenness predicate", "input_arity": 1,
           "codomain": "propositions",
           "description": "The parity predicate: EVEN(n) holds exactly when the "
           "integer n is a multiple of two. A Prop-valued head over an integer "
           "slot, like logic's connectives over propositions — the corpus's "
           "reading of Lean's `Even n`. Integer parity only: over a field every "
           "element is trivially a double, so the head does not extend there."}
ODD_FN = {"notation": "ODD(.)", "name": "oddness predicate", "input_arity": 1,
          "codomain": "propositions",
          "description": "The complementary parity predicate: ODD(n) holds "
          "exactly when n is not a multiple of two, equivalently when n has the "
          "form 2k+1. The corpus's reading of Lean's `Odd n`."}
PRIME_FN = {"notation": "PRIME(.)", "name": "primality predicate", "input_arity": 1,
            "codomain": "propositions",
            "description": "PRIME(n) holds when the integer n exceeds one and "
            "admits no factorization into two smaller positive integers. The "
            "corpus's reading of Lean's `Nat.Prime n` (and bare `Prime n` under "
            "`open Nat`). Divisibility itself remains an uncarried gap; these "
            "nodes state primality facts expressible without a divides head."}
IRRATIONAL_FN = {"notation": "IRRATIONAL(.)", "name": "irrationality predicate",
                 "input_arity": 1, "codomain": "propositions",
                 "description": "IRRATIONAL(x) holds when the real number x is "
                 "not a ratio of integers. The corpus's reading of Lean's "
                 "`Irrational x`; its canonical carriers here are square roots "
                 "of primes."}
MEET_FN = {"notation": "MEET(.,.)", "name": "conjunction", "input_arity": 2,
           "codomain": "propositions",
           "description": "Propositional conjunction, the same MEET head as "
           "scripts/seed_logic.py; here it bundles two predicate facts into a "
           "joint antecedent."}
JOIN_FN = {"notation": "JOIN(.,.)", "name": "disjunction", "input_arity": 2,
           "codomain": "propositions",
           "description": "Propositional (inclusive) disjunction, the same JOIN "
           "head as scripts/seed_logic.py; the parity dichotomy's exclusivity is "
           "recorded as an invariant, not a different head."}
NEG_FN = {"notation": "NEG(.)", "name": "propositional negation", "input_arity": 1,
          "codomain": "propositions",
          "description": "Propositional negation, the same NEG head as "
          "scripts/seed_logic.py; ODD is DEFINED through it over the integers."}
IMPLIES_FN = {"notation": "IMPLIES(.,.)", "name": "implication", "input_arity": 2,
              "codomain": "propositions",
              "description": "Material implication where the statement is an "
              "object-level conditional, and the meta-level 'if ... then' where "
              "it is a theorem schema. Same head and same documented double "
              "reading as scripts/seed_logic.py and seed_provability.py."}
SQRT_FN = {"notation": "SQRT(.)", "name": "square root", "input_arity": 1,
           "codomain": "nonnegative reals",
           "description": "The principal square root, the same SQRT head the "
           "algebra and calculus corpora carry; here it is the map that sends a "
           "prime to the canonical irrational."}
EXISTS_FN = {"notation": "EXISTS(.,.)", "name": "existential quantification",
             "input_arity": 2, "codomain": "propositions",
             "description": "The existential binder, the same EXISTS head as "
             "data/logic's quantifier laws (first argument the bound witness "
             "slot, second the body; binding carried by slot recurrence). Here "
             "it binds the integer witness that DEFINES a parity predicate — "
             "the corpus's reading of an ingested `∃ k, n = 2 * k`."}

INT_N = sym("n", "variable", "integer", "An arbitrary integer.")
INT_M = sym("m", "variable", "integer", "A second arbitrary integer, independent of n.")
INT_K = sym("k", "variable", "integer",
            "The bound witness integer: it occurs only under the existential "
            "binder, and exhibiting it is what proves the parity claim.")
INT_P = sym("p", "variable", "integer", "An integer in the role of a prime candidate.")
CONST_TWO = sym("2", "constant", "the_integer_two",
                "The integer two: the smallest prime, the modulus of parity, and "
                "the radicand of the first irrationality proof.")


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
    context = {"disciplines": ["number_theory"], "subfield": subfield, "topic": topic}
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


HARDY_WRIGHT = {"citation_key": "hardywright2008",
                "bibliographic_entry": "Hardy, G. H., Wright, E. M. (2008). An Introduction to the Theory of Numbers (6th ed.). Oxford: Oxford University Press."}
BURTON = {"citation_key": "burton2010",
          "bibliographic_entry": "Burton, D. M. (2010). Elementary Number Theory (7th ed.). New York: McGraw-Hill."}

INTEGER_ONLY = "Integer argument: parity is a property of the ring of integers, not of the rationals or reals"


NODES = [
    node("numbertheory.parity.even_double",
         "Twice Any Integer Is Even",
         "proposition", "derived", "parity", "parity_of_forms",
         "even(2*n)", "2n \\in 2\\mathbb{Z}",
         [{"form_id": "witness", "notation_system": "ascii",
           "expression": "2*n = n + n",
           "scope_note": "The doubling witness: 2n is the sum of n with itself"}],
         "parity_doubling", "EVEN(2 * INT1)",
         [slot("INT1", "variable", "integer")],
         ["A bare predicate application: the whole statement is one P-typed head "
          "over an arithmetic term, the exact shape of an ingested `Even (2 * k)` goal.",
          "The canonical form of evenness: every even integer arises this way.",
          "The instance of even-factor absorption with the even factor fixed at 2."],
         [INT_N], [MUL],
         "Doubling any integer lands in the even numbers: 2n is a multiple of two "
         "by construction.",
         "The generating exemplar of the EVEN head — evenness asserted of a term "
         "rather than of a bare slot, which is what ingested parity goals look like.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[EVEN_FN],
         inferential_links=links(
             special_case_of=["numbertheory.parity.even_product_absorbs"]),
         keywords=["parity", "even", "doubling", "multiple of two"]),

    node("numbertheory.parity.odd_successor",
         "One More Than an Even Number Is Odd",
         "proposition", "derived", "parity", "parity_of_forms",
         "odd(2*n + 1)", "2n + 1 \\notin 2\\mathbb{Z}",
         [{"form_id": "canonical_form", "notation_system": "ascii",
           "expression": "odd(m) iff m = 2*n + 1 for some integer n",
           "scope_note": "The form is exhaustive: every odd integer is 2n+1"}],
         "parity_offset", "ODD(2*INT1 + 1)",
         [slot("INT1", "variable", "integer")],
         ["A bare predicate application over a compound term, like its even twin.",
          "The canonical form of oddness: every odd integer arises this way.",
          "Offsetting the canonical even form by one crosses the parity classes."],
         [INT_N], [ADD, MUL],
         "One past any double is odd: 2n+1 leaves remainder one on division by two.",
         "The ODD head's generating exemplar, dual to the doubling node; together "
         "they name the two residue classes that partition the integers.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[ODD_FN],
         inferential_links=links(
             composed_with=["numbertheory.parity.even_double",
                            "numbertheory.parity.odd_is_not_even"]),
         keywords=["parity", "odd", "successor", "residue class"]),

    node("numbertheory.parity.even_witness_definition",
         "Evenness Is Having a Doubling Witness",
         "definition", "formal", "parity", "parity_classes",
         "even(n) = exists k. n = 2*k",
         "n \\in 2\\mathbb{Z} \\iff \\exists k\\,(n = 2k)",
         [{"form_id": "mathlib_form", "notation_system": "ascii",
           "expression": "Even n iff exists r, n = r + r",
           "scope_note": "mathlib's Even; 2k and k + k are the same witness "
                         "under the doubling identity"},
          {"form_id": "unicode", "notation_system": "ascii",
           "expression": "Even n ↔ ∃ k, n = 2 * k"}],
         "parity_witness_even", "EVEN(INT1) = EXISTS(INT2, INT1 = 2 * INT2)",
         [slot("INT1", "variable", "integer"),
          slot("INT2", "variable", "integer")],
         ["The definitional bridge between a predicate head and the "
          "existential binder: EVEN applied to a slot equals EXISTS over the "
          "witness equation, the same P-typed use of `=` as odd_is_not_even.",
          "The witness slot INT2 occurs only under the binder — the recurrence "
          "pattern IS the binding, exactly as in data/logic's quantifier laws.",
          "The exact shape of an ingested `∃ k, n = 2 * k` goal: exhibiting "
          "the witness is the whole proof (existential generalization).",
          "The reverse direction instantiated at any n is the doubling node "
          "EVEN(2 * INT1), which displays the witness instead of binding it."],
         [INT_N, INT_K], [EQ, MUL],
         "An integer is even exactly when some integer doubles to it: "
         "evenness is the existence of a halving witness.",
         "The corpus's definition of EVEN through the EXISTS head — the node "
         "that ties the parity predicates of this discipline to the binder "
         "heads of data/logic, so an existential parity witness is honestly "
         "expressible rather than a quantifier gap.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[EVEN_FN, EXISTS_FN],
         inferential_links=links(
             composed_with=["numbertheory.parity.even_double"]),
         keywords=["parity", "even", "witness", "existential", "definition"]),

    node("numbertheory.parity.odd_witness_definition",
         "Oddness Is Having an Offset Doubling Witness",
         "definition", "formal", "parity", "parity_classes",
         "odd(n) = exists k. n = 2*k + 1",
         "n \\in 2\\mathbb{Z}+1 \\iff \\exists k\\,(n = 2k + 1)",
         [{"form_id": "mathlib_form", "notation_system": "ascii",
           "expression": "Odd n iff exists m, n = 2 * m + 1",
           "scope_note": "mathlib's Odd, verbatim"},
          {"form_id": "unicode", "notation_system": "ascii",
           "expression": "Odd n ↔ ∃ k, n = 2 * k + 1"}],
         "parity_witness_odd", "ODD(INT1) = EXISTS(INT2, INT1 = 2 * INT2 + 1)",
         [slot("INT1", "variable", "integer"),
          slot("INT2", "variable", "integer")],
         ["The odd twin of the even witness definition: same binder, same "
          "recurrence pattern, the witness equation offset by one.",
          "With even_witness_definition and odd_is_not_even it closes the "
          "loop: the negation definition and the two witness definitions are "
          "consistent because no integer is both 2k and 2k+1.",
          "The exact shape of an ingested `∃ k, n = 2 * k + 1` goal."],
         [INT_N, INT_K], [EQ, ADD, MUL],
         "An integer is odd exactly when it is one more than some double: "
         "oddness is the existence of an offset halving witness.",
         "The ODD head's definition through the EXISTS binder, dual to the "
         "even witness definition; together they make the canonical forms of "
         "the two residue classes quantifier-explicit.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[ODD_FN, EXISTS_FN],
         inferential_links=links(
             composed_with=["numbertheory.parity.odd_successor"]),
         keywords=["parity", "odd", "witness", "existential", "definition"]),

    node("numbertheory.parity.odd_is_not_even",
         "Odd Means Not Even",
         "definition", "formal", "parity", "parity_classes",
         "odd(n) = not even(n)", "\\text{odd}(n) \\iff \\neg\\,\\text{even}(n)",
         [{"form_id": "contrapositive_reading", "notation_system": "ascii",
           "expression": "even(n) = not odd(n)",
           "scope_note": "The same definition read from the even side"}],
         "predicate_negation_definition", "ODD(INT1) = NEG(EVEN(INT1))",
         [slot("INT1", "variable", "integer")],
         ["A definitional equality between propositions, the same P-typed use of "
          "`=` as logic's Boolean-algebra laws.",
          "Over the integers the two parity classes are complementary, so negation "
          "defines one predicate from the other.",
          "This is what licenses reading a negated parity goal (`¬ Even n`) as odd."],
         [INT_N], [EQ, NOT],
         "An integer is odd exactly when it is not even: over the integers, "
         "oddness is the propositional negation of evenness.",
         "The definitional bridge between the two parity heads; with the dichotomy "
         "it makes parity a two-class partition rather than two unrelated predicates.",
         [INTEGER_ONLY,
          "The complementarity is specific to the integers; in a general monoid "
          "neither predicate need be the other's negation"],
         [HARDY_WRIGHT, BURTON],
         functionals=[ODD_FN, EVEN_FN, NEG_FN],
         keywords=["parity", "odd", "even", "negation", "definition"]),

    node("numbertheory.parity.dichotomy",
         "Every Integer Is Even or Odd",
         "theorem", "derived", "parity", "parity_classes",
         "even(n) or odd(n)", "n \\in 2\\mathbb{Z} \\cup (2\\mathbb{Z}+1)",
         [{"form_id": "partition", "notation_system": "ascii",
           "expression": "exactly one of even(n), odd(n) holds",
           "scope_note": "With odd-is-not-even the disjunction is exclusive"}],
         "predicate_dichotomy", "JOIN(EVEN(INT1), ODD(INT1))",
         [slot("INT1", "variable", "integer")],
         ["A bare disjunction of predicate applications: a whole statement built "
          "from P-typed heads with no relation symbol at all.",
          "Division by two admits exactly the remainders zero and one; the "
          "disjunction is exhaustive.",
          "Exclusive in content — no integer is both — but the JOIN head is "
          "inclusive-or; exclusivity is carried by the odd-is-not-even definition."],
         [INT_N], [OR],
         "Division by two sorts every integer into exactly one of two classes: "
         "the evens and the odds.",
         "The exhaustiveness half of the parity partition; the case split that "
         "grounds every parity argument by cases.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[JOIN_FN, EVEN_FN, ODD_FN],
         inferential_links=links(
             composed_with=["numbertheory.parity.odd_is_not_even"]),
         keywords=["parity", "dichotomy", "case split", "partition"],
         canonical_objects=["ring of integers", "residue classes modulo two"]),

    node("numbertheory.parity.even_sum_closed",
         "Even Numbers Are Closed Under Addition",
         "theorem", "derived", "parity", "parity_arithmetic",
         "if even(n) and even(m) then even(n + m)",
         "2\\mathbb{Z} + 2\\mathbb{Z} \\subseteq 2\\mathbb{Z}",
         [{"form_id": "witness_sum", "notation_system": "ascii",
           "expression": "2*a + 2*b = 2*(a + b)",
           "scope_note": "The witness computation behind the closure"}],
         "parity_closure_addition",
         "IMPLIES(MEET(EVEN(INT1), EVEN(INT2)), EVEN(INT1 + INT2))",
         [slot("INT1", "variable", "integer"), slot("INT2", "variable", "integer")],
         ["Symmetric under exchanging INT1 and INT2.",
          "Parity respects addition: the evens form a subgroup of the integers.",
          "A conditional whose antecedent and consequent are all predicate heads — "
          "the P-typed analogue of an algebraic closure law."],
         [INT_N, INT_M], [IMP, AND, ADD],
         "Adding two even integers yields an even integer: doubles sum to doubles.",
         "The additive closure of the even class — half of the statement that "
         "parity is a homomorphism from addition to addition modulo two.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[IMPLIES_FN, MEET_FN, EVEN_FN],
         keywords=["parity", "even", "closure", "addition", "subgroup"]),

    node("numbertheory.parity.odd_sum_even",
         "The Sum of Two Odd Numbers Is Even",
         "theorem", "derived", "parity", "parity_arithmetic",
         "if odd(n) and odd(m) then even(n + m)",
         "(2\\mathbb{Z}+1) + (2\\mathbb{Z}+1) \\subseteq 2\\mathbb{Z}",
         [{"form_id": "witness_sum", "notation_system": "ascii",
           "expression": "(2*a + 1) + (2*b + 1) = 2*(a + b + 1)",
           "scope_note": "The two offsets of one combine into a fresh double"}],
         "parity_crossing_addition",
         "IMPLIES(MEET(ODD(INT1), ODD(INT2)), EVEN(INT1 + INT2))",
         [slot("INT1", "variable", "integer"), slot("INT2", "variable", "integer")],
         ["Symmetric under exchanging INT1 and INT2.",
          "Addition CROSSES the parity classes here: the antecedent predicates and "
          "the consequent predicate are different heads, unlike the even closure.",
          "The residue computation 1 + 1 = 0 modulo two, spoken in predicates."],
         [INT_N, INT_M], [IMP, AND, ADD],
         "Adding two odd integers yields an even integer: the two unit offsets "
         "cancel modulo two.",
         "The class-crossing case of parity addition — with the even closure it "
         "completes the addition table of the two residue classes.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[IMPLIES_FN, MEET_FN, ODD_FN, EVEN_FN],
         keywords=["parity", "odd", "sum", "residue arithmetic"]),

    node("numbertheory.parity.even_product_absorbs",
         "A Product With an Even Factor Is Even",
         "theorem", "derived", "parity", "parity_arithmetic",
         "if even(n) then even(n * m)",
         "2\\mathbb{Z} \\cdot \\mathbb{Z} \\subseteq 2\\mathbb{Z}",
         [{"form_id": "witness_product", "notation_system": "ascii",
           "expression": "(2*a) * m = 2*(a * m)",
           "scope_note": "The factor of two survives any multiplication"}],
         "parity_absorption_multiplication",
         "IMPLIES(EVEN(INT1), EVEN(INT1 * INT2))",
         [slot("INT1", "variable", "integer"), slot("INT2", "variable", "integer")],
         ["ONE even factor suffices; the other factor is unconstrained — an "
          "absorption law, not a closure law.",
          "The evens form an ideal of the integer ring, not merely a subgroup.",
          "Its INT1 = 2 instance, detached against the primality of two's "
          "evenness, is the doubling node."],
         [INT_N, INT_M], [IMP, MUL],
         "Multiplying an even integer by anything keeps it even: the factor of "
         "two is never lost.",
         "The multiplicative absorption of the even class — the ideal property "
         "that makes even-times-anything a one-hypothesis statement where the odd "
         "product law needs two.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[IMPLIES_FN, EVEN_FN],
         inferential_links=links(
             generalizes=["numbertheory.parity.even_double"]),
         keywords=["parity", "even", "product", "absorption", "ideal"]),

    node("numbertheory.parity.odd_product_closed",
         "Odd Numbers Are Closed Under Multiplication",
         "theorem", "derived", "parity", "parity_arithmetic",
         "if odd(n) and odd(m) then odd(n * m)",
         "(2\\mathbb{Z}+1) \\cdot (2\\mathbb{Z}+1) \\subseteq 2\\mathbb{Z}+1",
         [{"form_id": "witness_product", "notation_system": "ascii",
           "expression": "(2*a + 1)*(2*b + 1) = 2*(2*a*b + a + b) + 1",
           "scope_note": "The expansion exhibits the odd canonical form"}],
         "parity_closure_multiplication",
         "IMPLIES(MEET(ODD(INT1), ODD(INT2)), ODD(INT1 * INT2))",
         [slot("INT1", "variable", "integer"), slot("INT2", "variable", "integer")],
         ["Symmetric under exchanging INT1 and INT2.",
          "Both factors must be odd: a single even factor is absorbed instead.",
          "The residue computation 1 * 1 = 1 modulo two, spoken in predicates."],
         [INT_N, INT_M], [IMP, AND, MUL],
         "Multiplying two odd integers yields an odd integer: no factor of two "
         "can appear in the product that was absent from the factors.",
         "The multiplicative closure of the odd class — with even absorption it "
         "completes the multiplication table of the two residue classes.",
         [INTEGER_ONLY],
         [HARDY_WRIGHT, BURTON],
         functionals=[IMPLIES_FN, MEET_FN, ODD_FN],
         keywords=["parity", "odd", "product", "closure"]),

    node("numbertheory.primality.two_is_prime",
         "Two Is Prime",
         "proposition", "derived", "primality", "small_primes",
         "prime(2)", "2 \\in \\mathbb{P}",
         [{"form_id": "factor_check", "notation_system": "ascii",
           "expression": "2 > 1 and the only positive factorizations of 2 are 1*2 and 2*1",
           "scope_note": "The finite verification that grounds the claim"}],
         "atomic_predicate_instance", "PRIME(TWO)",
         [slot("TWO", "constant", "the_integer_two")],
         ["A predicate head applied to a single constant: the smallest possible "
          "P-typed statement, and the exact shape of an ingested `Nat.Prime 17` goal.",
          "TWO is a constant slot in the settheory UNIVERSE / logic TRUTH sense: a "
          "distinguished element, not a bindable variable.",
          "The smallest prime, and the base case of every induction over primes.",
          "The witness that primality and evenness are compatible at exactly one point."],
         [CONST_TWO], [],
         "The integer two is prime: it exceeds one and admits no factorization "
         "into smaller positive integers.",
         "The atomic exemplar of the PRIME head — a closed statement with no "
         "slots, whose whole content is one predicate over one constant.",
         ["None: a closed arithmetic fact"],
         [HARDY_WRIGHT, BURTON],
         functionals=[PRIME_FN],
         inferential_links=links(
             composed_with=["numbertheory.primality.only_even_prime"]),
         keywords=["prime", "two", "smallest prime"],
         canonical_objects=["the set of prime numbers"]),

    node("numbertheory.primality.only_even_prime",
         "Two Is the Only Even Prime",
         "theorem", "derived", "primality", "small_primes",
         "if prime(n) and even(n) then n = 2",
         "n \\in \\mathbb{P} \\cap 2\\mathbb{Z} \\implies n = 2",
         [{"form_id": "contrapositive", "notation_system": "ascii",
           "expression": "if even(n) and n != 2 then not prime(n)",
           "scope_note": "Every other even number has the proper factor 2"}],
         "predicate_uniqueness",
         "IMPLIES(MEET(PRIME(INT1), EVEN(INT1)), INT1 = 2)",
         [slot("INT1", "variable", "integer")],
         ["A conditional from two predicate heads to an ordinary equation: the "
          "P-typed and relational fragments of the grammar in one statement.",
          "Any even number beyond two factors through its evenness, so primality "
          "pins the intersection to a single point.",
          "The reason parity arguments split 'p = 2' from 'p odd' in prime proofs."],
         [INT_N], [IMP, AND, EQ],
         "A prime that is even can only be two: evenness exhibits a proper factor "
         "in any larger candidate.",
         "The uniqueness that makes two the exceptional prime; jointly with even "
         "absorption it is why every prime beyond two is odd.",
         ["None: a closed arithmetic fact about the integers"],
         [HARDY_WRIGHT, BURTON],
         functionals=[IMPLIES_FN, MEET_FN, PRIME_FN, EVEN_FN],
         inferential_links=links(
             composed_with=["numbertheory.primality.two_is_prime",
                            "numbertheory.parity.even_product_absorbs"]),
         keywords=["prime", "even", "uniqueness", "two"]),

    node("numbertheory.irrationality.sqrt_prime_irrational",
         "Square Roots of Primes Are Irrational",
         "theorem", "derived", "irrationality", "algebraic_irrationals",
         "if prime(p) then irrational(sqrt(p))",
         "p \\in \\mathbb{P} \\implies \\sqrt{p} \\notin \\mathbb{Q}",
         [{"form_id": "no_rational_square", "notation_system": "ascii",
           "expression": "if prime(p) then p != (a/b)^2 for all integers a, b",
           "scope_note": "No rational squares to a prime; Euclid's descent"}],
         "irrationality_of_radicals",
         "IMPLIES(PRIME(INT1), IRRATIONAL(SQRT(INT1)))",
         [slot("INT1", "variable", "integer")],
         ["A predicate-to-predicate conditional whose consequent wraps an "
          "arithmetic head (SQRT) inside a P-typed head (IRRATIONAL).",
          "A prime appears to an odd power in p and to even powers in any square "
          "of a rational — the exponent parity mismatch IS the proof.",
          "Fails for composite radicands with square factors: sqrt(4) = 2."],
         [INT_P], [IMP],
         "The square root of any prime lies outside the rationals: a rational "
         "square carries every prime factor an even number of times, and a prime "
         "carries itself once.",
         "The general irrationality theorem for prime radicals, whose p = 2 "
         "instance is the classical first irrationality proof.",
         ["Principal (positive) square root",
          "Primality of the radicand is essential: perfect squares give integers"],
         [HARDY_WRIGHT, BURTON],
         functionals=[IMPLIES_FN, PRIME_FN, IRRATIONAL_FN, SQRT_FN],
         failure_modes=["Square-free composite radicands are also irrational, but "
                        "by a longer argument this statement does not carry."],
         inferential_links=links(
             generalizes=["numbertheory.irrationality.sqrt_two_irrational"]),
         keywords=["irrational", "square root", "prime", "descent"]),

    node("numbertheory.irrationality.sqrt_two_irrational",
         "The Square Root of Two Is Irrational",
         "theorem", "derived", "irrationality", "algebraic_irrationals",
         "irrational(sqrt(2))", "\\sqrt{2} \\notin \\mathbb{Q}",
         [{"form_id": "no_fraction", "notation_system": "ascii",
           "expression": "sqrt(2) != a/b for all integers a, b with b != 0",
           "scope_note": "The spelled-out membership denial"}],
         "irrationality_of_radicals_instance", "IRRATIONAL(SQRT(TWO))",
         [slot("TWO", "constant", "the_integer_two")],
         ["A closed statement: one P-typed head over one arithmetic head over one "
          "constant, the exact shape of an ingested `Irrational (Real.sqrt 2)` goal.",
          "The classical descent: an equality 2*b^2 = a^2 forces both sides' "
          "parities apart — the proof runs on this corpus's own parity nodes.",
          "The hypotenuse of the unit square: geometry's first incommensurable."],
         [CONST_TWO], [],
         "No ratio of integers squares to two: the diagonal of the unit square is "
         "incommensurable with its side.",
         "The founding irrationality result (Pythagorean school), and the p = 2 "
         "instance of the prime-radical theorem; its classical proof is a parity "
         "argument, tying this discipline's two subfields together.",
         ["Principal (positive) square root"],
         [HARDY_WRIGHT, BURTON],
         functionals=[IRRATIONAL_FN, SQRT_FN],
         inferential_links=links(
             special_case_of=["numbertheory.irrationality.sqrt_prime_irrational"],
             composed_with=["numbertheory.parity.even_product_absorbs",
                            "numbertheory.parity.odd_product_closed"]),
         keywords=["irrational", "square root of two", "incommensurable", "descent"],
         canonical_objects=["diagonal of the unit square"]),
]


# ---------------------------------------------------------------------------
# v0.10 item 2 — ingested Lean-workbook statements (docs/DESIGN-external-verifier.md)
#
# Two statements restated verbatim from the pinned derived extract
# data_sources/derived/lean_workbook/statements.json (HF Goedel-LM/
# Lean-workbook-proofs, revision b731852af8d8ab11498fda27bce9020738c01c59,
# MIT). They are the two halves of the design's hybrid decision:
#
# * lean_workbook_1041 executes option (a): core-Lean-decidable, so it carries
#   the corpus's first ingested `verified_by`, grounded end-to-end through the
#   external verifier (pinned source -> lean4 verdict -> traced transition
#   rows -> manifest digest pin -> this link; the correspondence rung's
#   ground-arithmetic fragment re-checks the shape).
# * lean_workbook_10202 executes option (b): its proof needs Mathlib (`ZMOD`
#   is Mathlib notation core Lean cannot parse), which is outside the hermetic
#   verification budget, so it enters as `formal` WITHOUT a bridge and says so
#   in its own semantic_interpretation — the node-level record the roadmap
#   demands.
#
# Both templates are fully GROUND: no matcher slots, every numeral an object.
# The slot_schema and symbols entries below are therefore documentation of
# ground constants (the schema requires at least one entry each), not matcher
# slots — CORRESPONDS for these nodes is exact structural identity of the
# ground equation.
# ---------------------------------------------------------------------------

POW = op("^", "exponentiation", 2, "arithmetic")

DIVIDES_FN = {"notation": "DIVIDES(., .)", "name": "divisibility predicate",
              "input_arity": 2, "codomain": "propositions",
              "description": "DIVIDES(d, n) holds exactly when d divides n in "
              "the natural numbers — the corpus's reading of Lean's `d ∣ n` "
              "on ℕ. Prop-valued over ground arithmetic terms, first "
              "argument the divisor."}

MOD_FN = {"notation": "MOD(., .)", "name": "residue (mod)",
          "input_arity": 2, "codomain": "natural numbers",
          "description": "MOD(a, n) is the remainder of a on division by n — "
          "the corpus's reading of Lean's `a % n` on ℕ. Already declared "
          "ordered_compose in the matcher's head algebra."}

LEAN_WORKBOOK = {
    "citation_key": "leanworkbook_goedel2025",
    "bibliographic_entry": "Lean Workbook problems, proofs by Goedel-Prover "
    "(Lin et al., 2025, arXiv:2502.07640). Ingested from the pinned derived "
    "extract data_sources/derived/lean_workbook/statements.json (HF "
    "Goedel-LM/Lean-workbook-proofs, revision "
    "b731852af8d8ab11498fda27bce9020738c01c59, MIT License; attribution in "
    "data_sources/derived/lean_workbook/NOTICE.md).",
    "url": "https://huggingface.co/datasets/Goedel-LM/Lean-workbook-proofs",
}

_LW_1041 = node(
    "numbertheory.ingested.lean_workbook_1041",
    "Thirteen Divides 2^30 + 3^60 (Ingested)",
    "proposition", "formal", "divisibility", "ingested_ground_arithmetic",
    "13 | 2^30 + 3^60", "13 \\mid 2^{30} + 3^{60}",
    [{"form_id": "ascii_ground",
      "notation_system": "ascii",
      "expression": "13 | 2^30 + 3^60",
      "scope_note": "The same ground surface the pinned Lean source states "
      "as `13 ∣ 2^30 + 3^60`; translated by the correspondence rung's "
      "ground-arithmetic fragment, not the propositional one."}],
    "ingested_ground_divisibility",
    "DIVIDES(13, 2 ^ 30 + 3 ^ 60)",
    [slot("GROUND_DIVISOR_13", "constant",
          "documentation of the ground divisor 13 — the template itself is "
          "fully ground and carries no matcher slots")],
    ["Fully ground: no slots, no variables — a single decidable arithmetic "
     "fact, the exact shape of the ingested Lean goal `⊢ 13 ∣ 2 ^ 30 + 3 ^ 60`.",
     "DIVIDES is Prop-valued over ground natural-number terms, the corpus "
     "reading of Lean's `∣` on ℕ; the ground-arithmetic correspondence "
     "fragment translates the goal with no slot folding, so CORRESPONDS here "
     "is exact structural identity of the ground equation.",
     "The proof route is kernel-checked `decide` in core Lean 4 — no Mathlib, "
     "no axioms beyond propext — which is exactly why this statement, and not "
     "a Mathlib-dependent one, carries the first ingested bridge."],
    [sym("13", "constant", "divisor",
         "The fixed divisor: a ground object, not a placeholder.", 0)],
    [ADD, MUL, POW],
    "13 divides 2^30 + 3^60: the ground divisibility fact stated by "
    "Lean-workbook problem lean_workbook_1041, restated verbatim from the "
    "pinned extract.",
    "The first ingested statement to carry a real `verified_by` end-to-end "
    "(ROADMAP-v0.10 item 2, option (a)): pinned source "
    "prover/lean/ingested/Ingested.lean -> external-verifier lean4 verdict "
    "(exit 0, no warnings, axioms exactly [propext]) -> traced transition "
    "rows prover/ingested_triples.json -> digest pin in "
    "prover/proof-artifact-manifest.json -> this node's link, plus an "
    "independent python-tests verdict over the same claim in exact integer "
    "arithmetic. Every verdict certifies exactly what it checked, not "
    "correctness in general (docs/DESIGN-external-verifier.md).",
    ["Natural-number carrier: `∣` and `^` are read on ℕ, where they agree "
     "with the corpus heads; no subtraction or division appears, so no "
     "monus/floor-division carrier hazard arises"],
    [LEAN_WORKBOOK],
    functionals=[DIVIDES_FN],
    constants=[{"symbol": "13", "value": 13,
                "description": "the divisor"},
               {"symbol": "2^30 + 3^60", "value": None,
                "description": "the dividend, kept symbolic: 1073741824 + "
                "42391158275216203514294433201 (its exact value is the "
                "python-tests verdict's business, not this record's)"}],
    keywords=["ingested", "lean workbook", "divisibility", "decidable",
              "external verifier", "verified_by"])
_LW_1041["verified_by"] = [{
    "system": "lean4",
    "artifact": "prover/ingested_triples.json",
    "reference": "lean_workbook_1041",
}]

_LW_10202 = node(
    "numbertheory.ingested.lean_workbook_10202",
    "2^21 Is Congruent to 1 Modulo 7 (Ingested, Formal Without Bridge)",
    "proposition", "formal", "modular_arithmetic", "ingested_ground_arithmetic",
    "2^21 % 7 = 1 % 7", "2^{21} \\equiv 1 \\pmod{7}",
    [{"form_id": "ascii_residues",
      "notation_system": "ascii",
      "expression": "2^21 % 7 = 1 % 7",
      "scope_note": "Int.ModEq unfolded to its defining residue equation; "
      "the source Lean surface is `2^21 ≡ 1 [ZMOD 7]`."}],
    "ingested_ground_congruence",
    "MOD(2 ^ 21, 7) = MOD(1, 7)",
    [slot("GROUND_MODULUS_7", "constant",
          "documentation of the ground modulus 7 — the template itself is "
          "fully ground and carries no matcher slots")],
    ["Fully ground congruence, stated as the residue equation that defines "
     "Int.ModEq; both sides are MOD applications over numerals.",
     "NO BRIDGE: this node deliberately carries no verified_by link — see "
     "statistical_significance for the recorded decision.",
     "The MOD head is the matcher's declared ordered_compose; nothing about "
     "this node extends the head algebra."],
    [sym("7", "constant", "modulus",
         "The fixed modulus: a ground object, not a placeholder.", 0)],
    [EQ, POW],
    "2^21 leaves remainder 1 on division by 7 (equivalently 7 divides "
    "2^21 - 1): the congruence stated by Lean-workbook problem "
    "lean_workbook_10202, restated as its defining residue equation.",
    "NODE-LEVEL RECORD, decision (b) of ROADMAP-v0.10 item 2 "
    "(docs/DESIGN-external-verifier.md Sec. 4): this statement is `formal` "
    "WITHOUT a `verified_by` bridge. Its Lean-workbook proof needs Mathlib "
    "(`ZMOD` is Mathlib's Int.ModEq notation; core Lean cannot parse the "
    "statement — verified by direct probe), and Mathlib is outside the "
    "repo's hermetic verification budget, so no bridge is claimed. "
    "`epistemic_status: formal` here records formal PROVENANCE (a Lean "
    "statement with an upstream machine-checked proof this repo cannot "
    "re-check); this corpus does NOT certify the congruence. Any future "
    "ingested node without a bridge must carry this same record.",
    ["Residue reading: the ZMOD congruence is recorded via its defining "
     "residue equation over ℕ, where % agrees with the corpus MOD head"],
    [LEAN_WORKBOOK],
    functionals=[MOD_FN],
    constants=[{"symbol": "7", "value": 7, "description": "the modulus"}],
    keywords=["ingested", "lean workbook", "congruence", "modular arithmetic",
              "formal without bridge"])

NODES.append(_LW_1041)
NODES.append(_LW_10202)


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "number_theory.core.v1",
        "discipline": "number_theory",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data") / "number_theory" / "nodes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {out} ({len(NODES)} nodes)")


if __name__ == "__main__":
    main()
