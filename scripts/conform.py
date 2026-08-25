#!/usr/bin/env python3
"""The conformance compiler: statements to evaluators, and what a verdict is worth.

`docs/DESIGN-statements-that-run.md` §3. A statement node becomes a
**conformance program** — a guard, a conclusion, and the free variables both
range over — and running it at points produces a **conformance record** whose
`certifies` sentence comes from a closed table keyed on the verdict, so the
sentence a reader sees is emitted by the same code path that computed the
verdict and cannot drift from it.

**The claim's shape, which is not a caveat appended to it.** For the ground
statements — closed arithmetic, no free variable — exact evaluation decides,
and the record is a proof-shaped object. For everything else, sampling is
**falsification-only**: a counterexample decides, and agreement at any number
of points certifies nothing universally. `NO_COUNTEREXAMPLE_FOUND` is named
that way rather than anything with the word *conforms* in it, and the
`certifies` table says so in the verdict's own row.

**The arithmetic is the committed one; the DOMAIN READINGS are the schema's.**
`+`, `*`, `^`, `neg` and every comparison are `scripts/evaluate.py`'s,
unchanged, so the thing tested and the thing already served are the same
arithmetic rather than two implementations that agree today. What this module
adds is exactly what §3.3 declares a domain must carry: the reading of `/`
(truncating or exact) and the reading of `-` (truncated-at-zero or signed).
Correction 4 is why that is not optional — `2017 - (2017/3) = 1345` is exactly
right over Nat and exactly wrong over Rat, and eight of ten apparent ground
errors were this difference rather than corpus defects.

**Three outcomes per point, because two is one too few.** A point can be
admitted and still fail to evaluate: division by zero, a non-integer
exponent, a result past the rendering bound. **An errored point is not a
counterexample and is not agreement**, and collapsing it into either is how a
branch cut becomes a corpus finding. A statement whose admitted points ALL
error is `REFUSED`, not `NO_COUNTEREXAMPLE_FOUND`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))

import conform_census as census  # noqa: E402
import conform_sampler as sampler  # noqa: E402
import evaluate as ev  # noqa: E402

# --------------------------------------------------------------------------
# §3.4's closed tables. A verdict without a `certifies` sentence is the one a
# reader will fill in themselves.
# --------------------------------------------------------------------------

DECIDED_TRUE = "DECIDED_TRUE"
DECIDED_FALSE = "DECIDED_FALSE"
NONCONFORMANT = "NONCONFORMANT"
NO_COUNTEREXAMPLE_FOUND = "NO_COUNTEREXAMPLE_FOUND"
UNDECLARED_DOMAIN = "UNDECLARED_DOMAIN"
REFUSED = "REFUSED"

CERTIFIES = {
    DECIDED_TRUE:
        "decided exactly under the declared domain; no sampling was involved",
    DECIDED_FALSE:
        "decided exactly under the declared domain; this is a disagreement "
        "between the statement and the declared domain, not yet a claim about "
        "either",
    NONCONFORMANT:
        "a counterexample was found and is printed; a counterexample decides. "
        "The domain under which it was found was declared by this repository "
        "— see the adjudication field",
    NO_COUNTEREXAMPLE_FOUND:
        "tested at N admitted points and not falsified; this certifies "
        "nothing universally and is not evidence the statement is true",
    UNDECLARED_DOMAIN:
        "no domain was established for this statement, so no verdict about it "
        "is claimed; this is not a finding about the statement",
    REFUSED:
        "nothing was computed, and the named construct says why; a refusal is "
        "not a negative result about the statement",
}

#: NIHIL's own closed table (§3.4 type two), keyed the same way.
NO_SUCH_OBJECT = "NO_SUCH_OBJECT"
EXISTS = "EXISTS"
OUT_OF_CLASS = "OUT_OF_CLASS"

NIHIL_CERTIFIES = {
    NO_SUCH_OBJECT:
        "the candidate set is finite, every candidate was evaluated exactly, "
        "and none satisfies the equation; this is a decided non-existence "
        "over the declared class, not a failure to find",
    EXISTS:
        "a witness was found and is printed; the enumeration that found it is "
        "printed beside it",
    OUT_OF_CLASS:
        "the instance is outside the class this procedure decides, so the "
        "procedure returned nothing about it; that is a refusal, not a "
        "negative",
}


class Refusal(Exception):
    """A register construct applies. Carries the construct id, nothing else."""

    def __init__(self, construct: str, detail: str = "") -> None:
        super().__init__(f"{construct}: {detail}" if detail else construct)
        self.construct = construct
        self.detail = detail


# --------------------------------------------------------------------------
# Domain-aware evaluation
# --------------------------------------------------------------------------


def _split_division(args):
    """`*(a, inv(b), c)` -> ([a, c], [b]). The parser spells `/` this way."""

    numerators, denominators = [], []
    for arg in args:
        if arg[0] == "op" and arg[1] == "inv":
            denominators.append(arg[2][0])
        else:
            numerators.append(arg)
    return numerators, denominators


def eval_under_domain(tree, bindings: dict, carrier: str, division: str,
                      subtraction: str) -> Fraction:
    """Evaluate one term under a DECLARED domain.

    The exact-and-signed reading delegates to `evaluate._eval_tree` verbatim,
    so the common path is the committed arithmetic and nothing else. The two
    declared readings §3.3 names — truncating `/`, truncated-at-zero `-` —
    are applied here and only here, because they are the schema's
    declarations rather than the evaluator's behaviour, and the evaluator is
    frozen by E7.
    """

    if division == "exact" and subtraction == "signed":
        return ev._eval_tree(tree, bindings, set())

    kind = tree[0]
    if kind == "num":
        return Fraction(str(tree[1]))
    if kind == "slot":
        name = tree[1]
        if name not in bindings:
            raise Refusal("undeclared_slot", f"{name} unbound at evaluation")
        return bindings[name]
    if kind != "op":
        raise ev.EvalError(f"no exact rule for {kind!r}")

    op = tree[1]
    if op == "+":
        # Under a truncated-at-zero reading, `a - b` is `max(0, a - b)`. The
        # parser spells subtraction as `+(a, neg(b))`, so the clamp lands
        # here rather than at a `-` node that does not exist.
        positives, negatives = [], []
        for arg in tree[2]:
            if arg[0] == "op" and arg[1] == "neg":
                negatives.append(arg[2][0])
            else:
                positives.append(arg)
        total = sum(
            (eval_under_domain(a, bindings, carrier, division, subtraction)
             for a in positives), Fraction(0))
        taken = sum(
            (eval_under_domain(a, bindings, carrier, division, subtraction)
             for a in negatives), Fraction(0))
        result = total - taken
        if subtraction == "truncated-at-zero" and result < 0:
            return Fraction(0)
        return result
    if op == "*":
        numerators, denominators = _split_division(tree[2])
        product = Fraction(1)
        for arg in numerators:
            product *= eval_under_domain(
                arg, bindings, carrier, division, subtraction)
        if not denominators:
            return product
        divisor = Fraction(1)
        for arg in denominators:
            divisor *= eval_under_domain(
                arg, bindings, carrier, division, subtraction)
        if divisor == 0:
            raise ev.EvalError("division by zero")
        if division == "truncating":
            # Correction 4's operator. Floor division is Lean's `/` on Nat.
            return Fraction(product.numerator * divisor.denominator
                            // (product.denominator * divisor.numerator))
        return product / divisor
    if op == "neg":
        inner = eval_under_domain(
            tree[2][0], bindings, carrier, division, subtraction)
        if subtraction == "truncated-at-zero" and inner > 0:
            # `Nat` HAS NO NEGATION, and clamping a negative literal to zero
            # would be inventing a reading the carrier does not have. Found
            # while implementing: clamping made 76 of the 297 ground
            # statements decide with both sides at 0 — a quarter of the class
            # returning DECIDED_TRUE for a reason that is not the statement's.
            #
            # Binary subtraction is a different case and is handled at the
            # `+` node above, where `a - b` really is truncating on Nat.
            # This branch is unary negation of a positive quantity, which is
            # simply not a Nat value.
            raise Refusal(
                "negation_outside_carrier",
                f"unary negation of {inner} has no value in {carrier}",
            )
        return -inner
    if op == "inv":
        inner = eval_under_domain(
            tree[2][0], bindings, carrier, division, subtraction)
        if inner == 0:
            raise ev.EvalError("division by zero")
        if division == "truncating":
            return Fraction(1 // inner) if inner != 0 else Fraction(0)
        return Fraction(1) / inner
    if op == "^":
        base = eval_under_domain(
            tree[2][0], bindings, carrier, division, subtraction)
        exponent = eval_under_domain(
            tree[2][1], bindings, carrier, division, subtraction)
        if exponent.denominator != 1:
            raise ev.EvalError("only integer exponents are exact here")
        power = int(exponent)
        if ev._power_digit_estimate(base, power) > ev.MAX_RESULT_DIGITS:
            raise Refusal("evaluation_budget_exceeded",
                          f"{base}^{power} exceeds the rendering bound")
        return base ** power
    raise ev.EvalError(f"no exact rule for operator {op!r}")


def decide_relation(relation: str, left: Fraction, right: Fraction) -> bool:
    """`evaluate._RELATIONS`, unchanged. The comparison is the committed one."""

    return bool(ev._RELATIONS[relation](left, right))


def in_carrier(value: Fraction, carrier: str) -> bool:
    """Whether a sampled value is IN the declared carrier.

    A candidate that is not a member of the carrier is domain-rejected, not
    guard-rejected, and the two counts are reported separately. Sampling over
    `Nat` and scoring a negative rational would be testing a statement the
    schema did not declare.
    """

    if carrier == "Rat":
        return True
    if value.denominator != 1:
        return False
    if carrier == "Nat":
        return value.numerator >= 0
    return carrier == "Int"


# --------------------------------------------------------------------------
# The compiled program
# --------------------------------------------------------------------------


@dataclass
class Program:
    statement_id: str
    corpus: str
    conclusion: tuple
    guard_conjuncts: tuple
    variables: tuple
    held: dict = field(default_factory=dict)
    carrier: str = "Rat"
    division: str = "exact"
    subtraction: str = "signed"
    compiled_from: str = "formal_statement.canonical_ascii"
    guard_source_field: str = "structural_signature.anonymized_template"
    provenance: dict = field(default_factory=dict)


def compile_statement(node: dict, row, schema) -> Program:
    """One classified statement into a runnable program, or `Refusal`."""

    if row.typed_refusal:
        raise Refusal(row.typed_refusal, row.statement_id)
    if row.bucket == "refused_numeral_beyond_exact_parse":
        raise Refusal("numeral_beyond_exact_parse", row.statement_id)
    if row.bucket == "refused_guard_unevaluable":
        raise Refusal("guard_unevaluable",
                      row.guard.unevaluable_reason or "")
    if row.shape_exclusion:
        raise Refusal(
            {
                "does_not_parse": "does_not_parse",
                "not_a_top_level_relation": "not_a_top_level_relation",
                "nested_relation": "nested_relation",
                "head_outside_evaluator": "head_outside_evaluator",
                "relation_undecidable": "relation_undecidable",
                "operator_outside_evaluator": "operator_pm",
            }[row.shape_exclusion],
            row.shape_detail,
        )

    declared = schema.carrier_for(row.statement_id, row.corpus)
    if declared is None:
        raise Refusal("domain_absent", row.corpus)

    ascii_text = (
        (node.get("formal_statement") or {}).get("canonical_ascii") or ""
    )
    conclusion = census.parse(ascii_text)
    if conclusion is None:
        raise Refusal("does_not_parse", row.statement_id)

    return Program(
        statement_id=row.statement_id,
        corpus=row.corpus,
        conclusion=conclusion,
        guard_conjuncts=row.guard.conjuncts,
        variables=tuple(row.sampled_variables),
        carrier=declared["carrier"],
        division=declared["division"],
        subtraction=declared["subtraction"],
        provenance={
            "corpus_id": row.corpus,
            "epistemic_status": row.epistemic_status,
            "bridge": (
                "formal-without-bridge"
                if row.corpus.startswith("lean_workbook") else "authored"
            ),
        },
    )


# --------------------------------------------------------------------------
# Running one program
# --------------------------------------------------------------------------


def _guard_holds(program: Program, bindings: dict) -> bool:
    for conjunct in program.guard_conjuncts:
        left = eval_under_domain(
            conjunct[2][0], bindings, program.carrier,
            program.division, program.subtraction)
        right = eval_under_domain(
            conjunct[2][1], bindings, program.carrier,
            program.division, program.subtraction)
        if not decide_relation(conjunct[1], left, right):
            return False
    return True


def run(program: Program, schema_digest: str,
        budget: int = sampler.DEFAULT_BUDGET,
        keep_points: int = 8) -> dict:
    """One conformance record. Never raises on a compiled program."""

    record = {
        "statement_id": program.statement_id,
        "compiled_from": program.compiled_from,
        "domain": {
            "carrier": program.carrier,
            "division": program.division,
            "subtraction": program.subtraction,
        },
        "guard": {
            "conjuncts": len(program.guard_conjuncts),
            "source_field": program.guard_source_field,
        },
        "free_variables": [
            {"name": name, "kind": "variable"} for name in program.variables
        ],
        "provenance": program.provenance,
        "sampler_seed": sampler.derive_seed(schema_digest, program.statement_id),
    }

    # --- the ground class: decided, not sampled -------------------------
    if not program.variables:
        try:
            left = eval_under_domain(
                program.conclusion[2][0], {}, program.carrier,
                program.division, program.subtraction)
            right = eval_under_domain(
                program.conclusion[2][1], {}, program.carrier,
                program.division, program.subtraction)
            holds = decide_relation(program.conclusion[1], left, right)
        except Refusal as exc:
            record.update(verdict=REFUSED, refusal_reason=exc.construct,
                          certifies=CERTIFIES[REFUSED])
            return record
        except (ev.EvalError, ArithmeticError, ValueError) as exc:
            record.update(verdict=REFUSED, refusal_reason="evaluation_error",
                          refusal_detail=str(exc)[:160],
                          certifies=CERTIFIES[REFUSED])
            return record
        record.update(
            verdict=DECIDED_TRUE if holds else DECIDED_FALSE,
            certifies=CERTIFIES[DECIDED_TRUE if holds else DECIDED_FALSE],
            left=str(left), right=str(right),
            points_sampled=0, points_admitted=0, points_rejected=0,
            points_errored=0,
        )
        return record

    # --- the sampled class: falsification only --------------------------
    points = sampler.sample_points(
        program.variables, schema_digest, program.statement_id, budget)
    admitted = rejected_domain = rejected_guard = errored = 0
    counterexample = None
    kept = []

    for point in points:
        bindings = point.as_dict()
        if not all(in_carrier(v, program.carrier) for v in bindings.values()):
            rejected_domain += 1
            continue
        try:
            if not _guard_holds(program, bindings):
                rejected_guard += 1
                continue
        except Refusal:
            rejected_guard += 1
            continue
        except (ev.EvalError, ArithmeticError, ValueError):
            rejected_guard += 1
            continue
        admitted += 1
        try:
            left = eval_under_domain(
                program.conclusion[2][0], bindings, program.carrier,
                program.division, program.subtraction)
            right = eval_under_domain(
                program.conclusion[2][1], bindings, program.carrier,
                program.division, program.subtraction)
        except Refusal as exc:
            errored += 1
            if len(kept) < keep_points:
                kept.append({"bindings": point.printable(), "guard_held": True,
                             "outcome": "evaluation_error",
                             "reason": exc.construct})
            continue
        except (ev.EvalError, ArithmeticError, ValueError) as exc:
            errored += 1
            if len(kept) < keep_points:
                kept.append({"bindings": point.printable(), "guard_held": True,
                             "outcome": "evaluation_error",
                             "reason": str(exc)[:80]})
            continue
        holds = decide_relation(program.conclusion[1], left, right)
        if len(kept) < keep_points:
            kept.append({
                "bindings": point.printable(), "guard_held": True,
                "left": str(left), "right": str(right),
                "outcome": "holds" if holds else "fails",
            })
        if not holds:
            counterexample = {
                "bindings": point.printable(),
                "left": str(left), "right": str(right),
                "relation": program.conclusion[1],
            }
            break

    record.update(
        points_sampled=len(points),
        points_admitted=admitted,
        points_rejected=rejected_guard,
        points_domain_rejected=rejected_domain,
        points_errored=errored,
        points_tested=kept,
    )
    record["counts_are_never_summed"] = (
        "points_admitted and points_rejected are separate and never summed; "
        "points_domain_rejected is separate again (added 2026-08-25: a "
        "candidate outside the declared carrier is not guard-excluded, and "
        "reporting the two as one would hide which gate did the work)."
    )

    if counterexample is not None:
        record.update(
            verdict=NONCONFORMANT, certifies=CERTIFIES[NONCONFORMANT],
            counterexample=counterexample,
            correlated_interpretation=(
                "This verdict is PROVISIONAL until the domain is "
                "independently adjudicated. Every domain row in this cycle "
                "was authored by this repository, so the label is applied to "
                "every NONCONFORMANT verdict rather than only to suspect "
                "ones — a label applied conditionally would imply the "
                "unlabelled ones had an independent domain when none of them "
                "does. Discharged per counterexample by C-E3, or it stands."
            ),
        )
        return record
    if admitted == 0:
        record.update(verdict=REFUSED, refusal_reason="guard_measure_zero",
                      certifies=CERTIFIES[REFUSED])
        return record
    if errored == admitted:
        record.update(verdict=REFUSED, refusal_reason="all_admitted_points_errored",
                      certifies=CERTIFIES[REFUSED])
        return record
    record.update(
        verdict=NO_COUNTEREXAMPLE_FOUND,
        certifies=CERTIFIES[NO_COUNTEREXAMPLE_FOUND].replace(
            "N admitted points", f"{admitted - errored} admitted points"),
    )
    return record


# --------------------------------------------------------------------------
# NIHIL — a decided non-existence (§3.4 type two)
# --------------------------------------------------------------------------


def rational_root_test(coefficients) -> dict:
    """The rational-root test over an integer-coefficient univariate polynomial.

    A DECIDED negative rather than a failure to find: the candidate set is
    finite by the rational root theorem, every candidate is evaluated
    exactly, and the record is the enumeration.

    E4 scores this over a committed constructed class, not over the corpus.
    Correction 5 is why: the corpus reach is three statements, all of which
    carry `sqrt` — a call head outside the evaluator — so none is compiled
    by this cycle's machinery. **No corpus-coverage number is quoted.**
    """

    coefficients = [int(c) for c in coefficients]
    while coefficients and coefficients[-1] == 0:
        coefficients.pop()
    if len(coefficients) < 2:
        return {
            "class_id": "rational_root_univariate",
            "verdict": OUT_OF_CLASS,
            "certifies": NIHIL_CERTIFIES[OUT_OF_CLASS],
            "reason": "not a univariate polynomial of degree >= 1",
        }

    constant, leading = coefficients[0], coefficients[-1]
    if constant == 0:
        return {
            "class_id": "rational_root_univariate",
            "instance": coefficients,
            "verdict": EXISTS,
            "witness": "0",
            "candidates_enumerated": 1,
            "candidates_refuted": 0,
            "certifies": NIHIL_CERTIFIES[EXISTS],
        }

    def divisors(n: int):
        n = abs(n)
        return sorted({d for d in range(1, n + 1) if n % d == 0})

    candidates = []
    for p in divisors(constant):
        for q in divisors(leading):
            for sign in (1, -1):
                candidates.append(Fraction(sign * p, q))
    candidates = sorted(set(candidates))

    refuted = []
    for candidate in candidates:
        value = sum(
            Fraction(c) * candidate ** i for i, c in enumerate(coefficients)
        )
        if value == 0:
            return {
                "class_id": "rational_root_univariate",
                "instance": coefficients,
                "verdict": EXISTS,
                "witness": str(candidate),
                "candidates_enumerated": len(candidates),
                "candidates_refuted": len(refuted),
                "certifies": NIHIL_CERTIFIES[EXISTS],
            }
        refuted.append({"candidate": str(candidate), "value": str(value)})

    return {
        "class_id": "rational_root_univariate",
        "instance": coefficients,
        "verdict": NO_SUCH_OBJECT,
        "candidates_enumerated": len(candidates),
        "candidates_refuted": len(refuted),
        "enumeration": refuted,
        "certifies": NIHIL_CERTIFIES[NO_SUCH_OBJECT],
    }
