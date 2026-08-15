#!/usr/bin/env python3
"""Seed data/programming/nodes.json — verified-code nodes.

ROADMAP-v0.10 item 3. Design: docs/DESIGN-programming-discipline.md
(committed first). The canonical form of an algorithm here is its
recurrence, not its control-flow; the existing matcher carries the twins.

Predictions registered BEFORE running scripts/match_signatures.py
-----------------------------------------------------------------

P4. programming.euclid.recursive and programming.euclid.iterative
    typed-twin (same remainder recurrence after the first-arg-zero
    orientation). programming.stein.binary is a singleton.
P5. The token-`gcd` baseline forms 3 pairs on the three nodes; the
    matcher forms 1. Matcher precision 1.0 vs baseline 1/3.
P9. group_counts shape 30→31, typed 31→32, family 30→31, aliased 32→33,
    mirror 5 unchanged.
P10. specialize.py finds no general/specific nest (the Euclid pair are
    twins, not a nest). Zero parse problems, zero slot gaps.

Verdict-backed rule (P7 / P-W7): this seed will not emit a verified_by
link unless a committed python-tests PASS names that statement_id.

Second wave (docs/DESIGN-programming-second-wave.md), registered BEFORE
the matcher re-run:
P-W4. three new typed groups of size 2 (factorial, dfactorial, binexp);
      Euclid unchanged; Stein singleton; no FACT/DFACT or BEXP/STEIN cross.
P-W5. token-`factorial` baseline forms 6 pairs; matcher forms 2.
P-W9. group_counts {1027,972,971,973,5} -> {1030,975,974,976,5}.
P-W10. no programming specialization edge (pairs are twins, not nests).
"""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
VERDICT_DIR = REPO / "prover" / "verifier-verdicts"


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="arithmetic"):
    return {"symbol": symbol, "name": name, "arity": arity, "operator_family": family}


EQ = op("=", "equality", 2, "relational")
MUL = op("*", "multiplication", 2, "arithmetic")
SUB = op("-", "subtraction", 2, "arithmetic")
POW = op("^", "exponentiation", 2, "arithmetic")

GCD_FN = {"notation": "GCD(.,.)", "name": "greatest common divisor",
          "input_arity": 2, "codomain": "integers",
          "description": "The greatest common divisor of two integers. "
          "Declared commutative in the head algebra (CONVENTION)."}
ITE_FN = {"notation": "ITE(.,.,.)", "name": "if-then-else",
          "input_arity": 3, "codomain": "the then/else carrier",
          "description": "Ordered ternary: condition, then-branch, else-branch. "
          "Not commutative. The control-flow of a recurrence, not a new matcher."}
ABS_FN = {"notation": "ABS(.)", "name": "integer absolute value",
          "input_arity": 1, "codomain": "nonnegative integers",
          "description": "Absolute value on Z, so gcd of negatives is positive."}
MOD_FN = {"notation": "MOD(.,.)", "name": "residue (mod)",
          "input_arity": 2, "codomain": "integers",
          "description": "Remainder; the same MOD head number theory already "
          "carries. Euclid's reduction step."}
EVEN_FN = {"notation": "EVEN(.)", "name": "evenness predicate",
           "input_arity": 1, "codomain": "propositions",
           "description": "The number-theory EVEN head, reused: Stein branches "
           "on parity."}
MEET_FN = {"notation": "MEET(.,.)", "name": "conjunction",
           "input_arity": 2, "codomain": "propositions",
           "description": "Propositional conjunction, same MEET as logic."}
STEIN_FN = {"notation": "STEIN(.,.)", "name": "binary GCD (Stein)",
            "input_arity": 2, "codomain": "integers",
            "description": "Stein's binary GCD. A different recurrence from "
            "Euclid; the opaque head quarantines it from the Euclid twin."}
HALVE_FN = {"notation": "HALVE(.)", "name": "exact divide-by-two",
            "input_arity": 1, "codomain": "integers",
            "description": "Exact halving of an even integer. Not Nat.div: "
            "the argument is even by the EVEN guard that wraps it."}
MINOF_FN = {"notation": "MINOF(.,.)", "name": "binary minimum",
            "input_arity": 2, "codomain": "integers",
            "description": "The existing MINOF head, used in Stein's both-odd "
            "reduction."}
FACT_FN = {"notation": "FACT(.)", "name": "factorial",
           "input_arity": 1, "codomain": "integers",
           "description": "n!. Unary; the recurrence is n * FACT(n-1)."}
DFACT_FN = {"notation": "DFACT(.)", "name": "double factorial",
            "input_arity": 1, "codomain": "integers",
            "description": "n!!. Unary; the recurrence is n * DFACT(n-2). "
            "Different skeleton from FACT; the token factorial is shared "
            "on purpose (docs/DESIGN-programming-second-wave.md §5.2)."}
BEXP_FN = {"notation": "BEXP(.,.)", "name": "binary exponentiation",
           "input_arity": 2, "codomain": "reals",
           "description": "a^b by squaring. Ordered: exponentiation is not "
           "commutative. Authored even-first (EVEN/HALVE already exist)."}
LEQ_FN = {"notation": "LEQ(.,.)", "name": "non-strict order",
          "input_arity": 2, "codomain": "propositions",
          "description": "The existing LEQ head, reused for the n <= 1 base."}

INT_N = sym("n", "variable", "integer", "Non-negative integer argument.")
BASE_X = sym("a", "variable", "real", "Exponentiation base.")
EXP_N = sym("b", "variable", "integer", "Non-negative integer exponent.")

INT_A = sym("a", "variable", "integer", "First integer argument.")
INT_B = sym("b", "variable", "integer", "Second integer argument.")

HONESTY = (
    "A python-tests PASS certifies that the pinned candidate compiled, "
    "passed mypy --strict, and survived the pinned tests under the "
    "sandbox. It does not certify the candidate correct "
    "(docs/DESIGN-programming-discipline.md §2)."
)

THEALGORITHMS = {
    "citation_key": "thealgorithms_python_f5988cc",
    "bibliographic_entry": (
        "TheAlgorithms and contributors. TheAlgorithms/Python. MIT License. "
        "https://github.com/TheAlgorithms/Python "
        "(commit f5988cc09713315817df6a7e327e258013a94440)."
    ),
    "url": "https://github.com/TheAlgorithms/Python",
}

FIRST_PARTY = {
    "citation_key": "corollary_stein_first_party",
    "bibliographic_entry": (
        "First-party Stein binary GCD, authored in this slice as the "
        "name-similar non-twin. Not ingested. See "
        "docs/DESIGN-programming-discipline.md §3."
    ),
}


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
    context = {"disciplines": ["programming"], "subfield": subfield, "topic": topic}
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


def require_python_tests_pass(statement_id: str) -> dict:
    """P7: no verified_by without a committed python-tests PASS."""
    if not VERDICT_DIR.is_dir():
        raise SystemExit(
            f"seed_programming: no verdict dir {VERDICT_DIR}; refuse to "
            f"emit verified_by for {statement_id}"
        )
    matches = []
    for path in sorted(VERDICT_DIR.glob("*.json")):
        verdict = json.loads(path.read_text(encoding="utf-8"))
        claim = verdict.get("claim") or {}
        if claim.get("statement_id") != statement_id:
            continue
        if verdict.get("backend") != "python-tests":
            continue
        matches.append((path, verdict))
    passes = [m for m in matches if m[1].get("verdict") == "pass"]
    if not passes:
        raise SystemExit(
            f"seed_programming: no committed python-tests PASS for "
            f"{statement_id}; refusing to emit a verified_by link "
            "(docs/DESIGN-programming-discipline.md §6)"
        )
    return passes[0][1]


EUCLID_TEMPLATE = (
    "GCD(INTA, INTB) = ITE(EQ(INTA, 0), ABS(INTB), "
    "GCD(MOD(INTB, INTA), INTA))"
)
EUCLID_SLOTS = [
    slot("INTA", "variable", "integer"),
    slot("INTB", "variable", "integer"),
]
EUCLID_INVARIANTS = [
    "Canonical form is the remainder recurrence, not the control-flow: "
    "recursion and a while-loop that realize this recurrence are the "
    "same algorithm (docs/DESIGN-programming-discipline.md §4).",
    "First-arg-zero orientation: the TheAlgorithms recursive body already "
    "uses `a == 0`; the iterative `while y` form is authored onto the "
    "same orientation by slot renaming.",
    "ABS makes the result nonnegative, matching the source doctests on "
    "negative inputs.",
]


def _euclid(sid, title, source_fn, artifact, reference, extra_meaning, keywords):
    require_python_tests_pass(sid)
    n = node(
        sid, title, "identity", "formal",
        "number_theoretic_algorithms", "euclidean_gcd",
        "gcd(a, b) = |b| if a = 0 else gcd(b % a, a)",
        "\\gcd(a,b)=\\lvert b\\rvert\\text{ if }a=0\\text{ else }\\gcd(b\\bmod a,\\,a)",
        [{"form_id": "recurrence", "notation_system": "ascii",
          "expression": "gcd(a, b) = abs(b) if a == 0 else gcd(b % a, a)",
          "scope_note": "The TheAlgorithms recursive orientation; the "
          "iterative implementation is the same recurrence."}],
        "euclid_remainder_recurrence",
        EUCLID_TEMPLATE,
        EUCLID_SLOTS,
        EUCLID_INVARIANTS,
        [INT_A, INT_B], [EQ],
        extra_meaning,
        HONESTY,
        ["Integer arguments; ABS on the base case so negatives agree "
         "with the source doctests"],
        [THEALGORITHMS],
        functionals=[GCD_FN, ITE_FN, ABS_FN, MOD_FN],
        constants=[{"symbol": "0", "value": 0,
                    "description": "the Euclidean base-case test"}],
        inferential_links=links(
            equivalent_to=["programming.euclid.iterative"]
            if sid == "programming.euclid.recursive"
            else ["programming.euclid.recursive"]
        ),
        keywords=keywords,
        canonical_objects=["euclidean algorithm"],
        failure_modes=[
            "Dropping ABS leaks a negative remainder (the committed "
            "drop-abs FAIL records this)."
        ],
    )
    n["verified_by"] = [{
        "system": "python-tests",
        "artifact": artifact,
        "reference": reference,
    }]
    return n


def _stein():
    sid = "programming.stein.binary"
    require_python_tests_pass(sid)
    template = (
        "STEIN(INTA, INTB) = ITE(EQ(INTA, 0), INTB, "
        "ITE(EQ(INTB, 0), INTA, "
        "ITE(MEET(EVEN(INTA), EVEN(INTB)), "
        "2 * STEIN(HALVE(INTA), HALVE(INTB)), "
        "ITE(EVEN(INTA), STEIN(HALVE(INTA), INTB), "
        "ITE(EVEN(INTB), STEIN(INTA, HALVE(INTB)), "
        "STEIN(HALVE(ABS(INTA - INTB)), MINOF(INTA, INTB)))))))"
    )
    n = node(
        sid,
        "Stein's Binary GCD",
        "identity", "formal",
        "number_theoretic_algorithms", "binary_gcd",
        "stein(a, b) branches on parity, not remainder",
        "\\mathrm{stein}(a,b)\\text{ reduces by halving evens, not }a \\bmod b",
        [{"form_id": "recurrence", "notation_system": "ascii",
          "expression": "stein(a,b) = ...parity/halving...",
          "scope_note": "First-party foil: name contains gcd, recurrence "
          "does not share Euclid's skeleton."}],
        "stein_binary_gcd",
        template,
        EUCLID_SLOTS,
        [
            "Different recurrence from Euclid: reduction is by HALVE on "
            "evens, not MOD. The matcher must not twin this with the "
            "Euclid pair (P4).",
            "EVEN is the number-theory predicate head; HALVE is exact "
            "divide-by-two under an EVEN guard, not Nat.div.",
            "First-party, not ingested (design §3).",
        ],
        [INT_A, INT_B], [EQ, MUL, SUB],
        "Stein's binary GCD: the name-similar non-twin for the Euclid "
        "pair. The token `gcd` appears in the statement_id so the "
        "capability-blind baseline pairs it with both Euclid nodes.",
        HONESTY,
        ["Integer arguments; abs at entry so negatives agree with Euclid "
         "on the shared test cases"],
        [FIRST_PARTY],
        functionals=[STEIN_FN, ITE_FN, EVEN_FN, MEET_FN, HALVE_FN,
                     ABS_FN, MINOF_FN],
        constants=[{"symbol": "0", "value": 0,
                    "description": "the zero base cases"},
                   {"symbol": "2", "value": 2,
                    "description": "the factor restored after shared twos"}],
        keywords=["gcd", "stein", "binary gcd", "first-party",
                  "programming"],
        canonical_objects=["Stein's algorithm"],
    )
    n["verified_by"] = [{
        "system": "python-tests",
        "artifact": "prover/pychecks/gcd_stein.py",
        "reference": "gcd_stein",
    }]
    return n


FACT_TEMPLATE = "FACT(N) = ITE(LEQ(N, 1), 1, N * FACT(N - 1))"
FACT_SLOTS = [slot("N", "variable", "integer")]
FACT_INVARIANTS = [
    "Canonical form is the product recurrence, not the control-flow: "
    "recursion and a for-loop that realize this recurrence are the "
    "same algorithm (docs/DESIGN-programming-second-wave.md §4).",
    "Base case LEQ(N, 1) is the source's n in {0, 1} under the "
    "regularity condition N >= 0.",
    "Volume tests compare against math.factorial on range(20).",
]


def _fact(sid, title, artifact, reference, extra_meaning, keywords, twin):
    require_python_tests_pass(sid)
    n = node(
        sid, title, "identity", "formal",
        "combinatorial_algorithms", "factorial",
        "n! = 1 if n <= 1 else n * (n-1)!",
        "n! = 1 \\text{ if } n \\le 1 \\text{ else } n\\cdot(n-1)!",
        [{"form_id": "recurrence", "notation_system": "ascii",
          "expression": "fact(n) = 1 if n <= 1 else n * fact(n - 1)",
          "scope_note": "Recursive orientation; the iterative "
          "implementation is the same recurrence."}],
        "factorial_product_recurrence",
        FACT_TEMPLATE,
        FACT_SLOTS,
        FACT_INVARIANTS,
        [INT_N], [EQ, MUL, SUB],
        extra_meaning,
        HONESTY,
        ["Non-negative integer argument; negatives are regularity, "
         "not structure"],
        [THEALGORITHMS],
        functionals=[FACT_FN, ITE_FN, LEQ_FN],
        constants=[{"symbol": "1", "value": 1,
                    "description": "the factorial base-case value and the "
                    "LEQ threshold"}],
        inferential_links=links(equivalent_to=[twin]),
        keywords=keywords,
        canonical_objects=["factorial"],
        failure_modes=[
            "Stepping by 2 instead of 1 agrees on {0, 1} and fails at 3 "
            "(the committed n-minus-2 FAIL records this)."
        ],
    )
    n["verified_by"] = [{
        "system": "python-tests",
        "artifact": artifact,
        "reference": reference,
    }]
    return n


DFACT_TEMPLATE = "DFACT(N) = ITE(LEQ(N, 1), 1, N * DFACT(N - 2))"
DFACT_INVARIANTS = [
    "Different recurrence from factorial: the step is N - 2, not N - 1. "
    "The matcher must not twin this with the factorial pair (P-W4).",
    "The token `factorial` is in keywords so the capability-blind "
    "baseline pairs it with both factorial nodes.",
    "Volume tests compare against math.prod(range(i, 0, -2)) on range(20).",
]


def _dfact(sid, title, artifact, reference, extra_meaning, keywords, twin):
    require_python_tests_pass(sid)
    n = node(
        sid, title, "identity", "formal",
        "combinatorial_algorithms", "double_factorial",
        "n!! = 1 if n <= 1 else n * (n-2)!!",
        "n!! = 1 \\text{ if } n \\le 1 \\text{ else } n\\cdot(n-2)!!",
        [{"form_id": "recurrence", "notation_system": "ascii",
          "expression": "dfact(n) = 1 if n <= 1 else n * dfact(n - 2)",
          "scope_note": "The ingested foil: name contains factorial, "
          "recurrence does not share FACT's skeleton."}],
        "double_factorial_recurrence",
        DFACT_TEMPLATE,
        FACT_SLOTS,
        DFACT_INVARIANTS,
        [INT_N], [EQ, MUL, SUB],
        extra_meaning,
        HONESTY,
        ["Non-negative integer argument"],
        [THEALGORITHMS],
        functionals=[DFACT_FN, ITE_FN, LEQ_FN],
        constants=[{"symbol": "1", "value": 1,
                    "description": "the double-factorial base-case value"},
                   {"symbol": "2", "value": 2,
                    "description": "the double-factorial step"}],
        inferential_links=links(equivalent_to=[twin]),
        keywords=keywords,
        canonical_objects=["double factorial"],
    )
    n["verified_by"] = [{
        "system": "python-tests",
        "artifact": artifact,
        "reference": reference,
    }]
    return n


BEXP_TEMPLATE = (
    "BEXP(BASE, EXPN) = ITE(EQ(EXPN, 0), 1, "
    "ITE(EVEN(EXPN), BEXP(BASE, HALVE(EXPN)) ^ 2, "
    "BASE * BEXP(BASE, EXPN - 1)))"
)
BEXP_SLOTS = [
    slot("BASE", "variable", "real"),
    slot("EXPN", "variable", "integer"),
]
BEXP_INVARIANTS = [
    "Canonical form is the square-and-multiply recurrence, not the "
    "bit-shift accumulator. Recursion and a while-loop that realize "
    "this recurrence are the same algorithm.",
    "Even-first orientation: EVEN and HALVE already exist (Stein). "
    "The TheAlgorithms recursive body checks odd first; both nodes "
    "are authored onto the even-first template "
    "(docs/DESIGN-programming-second-wave.md §4).",
    "The even branch is rec ^ 2 (one recursive call, then square), "
    "matching the source's bind-then-multiply.",
]


def _bexp(sid, title, artifact, reference, extra_meaning, keywords, twin):
    require_python_tests_pass(sid)
    n = node(
        sid, title, "identity", "formal",
        "number_theoretic_algorithms", "binary_exponentiation",
        "bexp(a, e) = 1 if e = 0 else (bexp(a, e/2)^2 if e even else a * bexp(a, e-1))",
        "a^{e}=1\\text{ if }e=0\\text{ else }(a^{e/2})^{2}\\text{ if }e\\text{ even else }a\\cdot a^{e-1}",
        [{"form_id": "recurrence", "notation_system": "ascii",
          "expression": "bexp(a, e) = 1 if e == 0 else "
          "(bexp(a, e//2)**2 if e%2==0 else a * bexp(a, e-1))",
          "scope_note": "Even-first authored orientation."}],
        "binary_exponentiation_recurrence",
        BEXP_TEMPLATE,
        BEXP_SLOTS,
        BEXP_INVARIANTS,
        [BASE_X, EXP_N], [EQ, MUL, SUB, POW],
        extra_meaning,
        HONESTY,
        ["Non-negative integer exponent; real base. Modular variants "
         "in the source file are declined this slice."],
        [THEALGORITHMS],
        functionals=[BEXP_FN, ITE_FN, EVEN_FN, HALVE_FN],
        constants=[{"symbol": "0", "value": 0,
                    "description": "the exponent base-case test"},
                   {"symbol": "1", "value": 1,
                    "description": "a^0"},
                   {"symbol": "2", "value": 2,
                    "description": "the even-branch square"}],
        inferential_links=links(equivalent_to=[twin]),
        keywords=keywords,
        canonical_objects=["binary exponentiation"],
    )
    n["verified_by"] = [{
        "system": "python-tests",
        "artifact": artifact,
        "reference": reference,
    }]
    return n


NODES = [
    _euclid(
        "programming.euclid.recursive",
        "Euclidean GCD, Recursive (TheAlgorithms)",
        "greatest_common_divisor",
        "prover/pychecks/gcd_euclid_recursive.py",
        "greatest_common_divisor",
        "The Euclidean remainder recurrence, recursive evaluation, as "
        "implemented by TheAlgorithms/Python greatest_common_divisor "
        "(commit f5988cc, MIT).",
        ["gcd", "euclid", "recursive", "ingested", "programming"],
    ),
    _euclid(
        "programming.euclid.iterative",
        "Euclidean GCD, Iterative (TheAlgorithms)",
        "gcd_by_iterative",
        "prover/pychecks/gcd_euclid_iterative.py",
        "gcd_by_iterative",
        "The same Euclidean remainder recurrence, while-loop evaluation, "
        "as implemented by TheAlgorithms/Python gcd_by_iterative "
        "(commit f5988cc, MIT). Control-flow is evaluation strategy, "
        "not structure.",
        ["gcd", "euclid", "iterative", "ingested", "programming"],
    ),
    _stein(),
    _fact(
        "programming.factorial.recursive",
        "Factorial, Recursive (TheAlgorithms)",
        "prover/pychecks/factorial_recursive.py",
        "factorial_recursive",
        "The factorial recurrence, recursive evaluation, as implemented "
        "by TheAlgorithms/Python factorial_recursive (commit f5988cc, MIT).",
        ["factorial", "recursive", "ingested", "programming"],
        twin="programming.factorial.iterative",
    ),
    _fact(
        "programming.factorial.iterative",
        "Factorial, Iterative (TheAlgorithms)",
        "prover/pychecks/factorial_iterative.py",
        "factorial",
        "The same factorial recurrence, for-loop evaluation, as implemented "
        "by TheAlgorithms/Python factorial (commit f5988cc, MIT). "
        "Control-flow is evaluation strategy, not structure.",
        ["factorial", "iterative", "ingested", "programming"],
        twin="programming.factorial.recursive",
    ),
    _dfact(
        "programming.dfactorial.recursive",
        "Double Factorial, Recursive (TheAlgorithms)",
        "prover/pychecks/dfactorial_recursive.py",
        "double_factorial_recursive",
        "The double-factorial recurrence (step n-2), recursive evaluation, "
        "as implemented by TheAlgorithms/Python double_factorial_recursive "
        "(commit f5988cc, MIT). Name-similar non-twin of the factorial pair.",
        ["factorial", "double factorial", "recursive", "ingested",
         "programming"],
        twin="programming.dfactorial.iterative",
    ),
    _dfact(
        "programming.dfactorial.iterative",
        "Double Factorial, Iterative (TheAlgorithms)",
        "prover/pychecks/dfactorial_iterative.py",
        "double_factorial_iterative",
        "The same double-factorial recurrence, for-loop evaluation, as "
        "implemented by TheAlgorithms/Python double_factorial_iterative "
        "(commit f5988cc, MIT).",
        ["factorial", "double factorial", "iterative", "ingested",
         "programming"],
        twin="programming.dfactorial.recursive",
    ),
    _bexp(
        "programming.binexp.recursive",
        "Binary Exponentiation, Recursive (TheAlgorithms)",
        "prover/pychecks/binexp_recursive.py",
        "binary_exp_recursive",
        "Binary exponentiation by squaring, recursive evaluation, as "
        "implemented by TheAlgorithms/Python binary_exp_recursive "
        "(commit f5988cc, MIT). Authored even-first (EVEN/HALVE already "
        "exist); the source checks odd first.",
        ["exponentiation", "power", "recursive", "ingested", "programming"],
        twin="programming.binexp.iterative",
    ),
    _bexp(
        "programming.binexp.iterative",
        "Binary Exponentiation, Iterative (TheAlgorithms)",
        "prover/pychecks/binexp_iterative.py",
        "binary_exp_iterative",
        "The same binary-exponentiation recurrence, bit-shift evaluation, "
        "as implemented by TheAlgorithms/Python binary_exp_iterative "
        "(commit f5988cc, MIT).",
        ["exponentiation", "power", "iterative", "ingested", "programming"],
        twin="programming.binexp.recursive",
    ),
]


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "programming.core.v1",
        "discipline": "programming",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data") / "programming" / "nodes.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(corpus, indent=2, ensure_ascii=False) + "\n"
    out.write_bytes(payload.encode("utf-8"))
    print(f"wrote {out} ({len(NODES)} nodes)")


if __name__ == "__main__":
    main()
