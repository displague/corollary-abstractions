#!/usr/bin/env python3
"""The WITNESS obligation builder: two readings of one statement, compared.

`docs/DESIGN-witnessed-conformance.md` §3 and §6. The draft's obligation is
`forall x in D: eval(S)(x) <-> S(x)`, and the whole design turns on those two
sides being **genuinely different objects**. If both come from one parse by
one renderer the obligation is `P <-> P`, B4 must reject it, and the
instrument has measured nothing.

**What the two sides actually are here.** `eval(S)` is what
`conform.eval_under_domain` COMPUTES, and that is not the statement as
written. At a `+` node the evaluator hoists every positive operand and
subtracts the sum of the negatives; at a `*` node it multiplies every
numerator and divides once by the product of the denominators. Over the
declared `Nat` domain — truncated subtraction, floor division — those
regroupings are **observable**:

    a - b + c     evaluator: (a + c) - b        as written: (a - b) + c
                  at a=1, b=4, c=10:  7                        10

    a / b * c     evaluator: (a * c) / b        as written: (a / b) * c
                  at a=1, b=2, c=2:   1                         0

So `S(x)` is the statement read left to right the way it is written, and
`eval(S)(x)` is the statement read the way the conformance evaluator groups
it. The obligation asks whether the 775 counterexamples v0.20 published were
counterexamples to the statements or to the evaluator's regrouping of them.
That question can be answered `no`, which is what makes it worth asking.

**Trivial by construction is detected on TREES, not on strings.** A first
version compared rendered strings and called `((6*a) + (2*b)) - (2*b)`
different from `(((6*a) + (2*b))) - ((2*b))` — the same term with different
redundant brackets. Eighteen of forty-five statements looked non-trivial and
most of them were parenthesis noise. The comparison is structural.

**The domain D is the evaluator's admitted set, said rather than assumed.**
The guard is rendered from the evaluator's own reading, because the
evaluator's guard is what decides which points it tests. A reader who wants
the guard's surface reading audited is asking a different question, and §6's
front-end residual is where it lives.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import conform  # noqa: E402

DISCHARGED = "discharged"
NOT_DISCHARGED = "not_discharged"
REJECTED_TRIVIAL = "rejected_trivial"

#: The only domain W0 admitted. Kept as a constant so a future carrier has to
#: be added deliberately rather than by a renderer that happens not to crash.
SUPPORTED = {("Nat", "truncating", "truncated-at-zero")}


class Unbuildable(Exception):
    """No obligation can be built, and the reason is carried."""


# --------------------------------------------------------------------------
# Two readings, as explicit binary trees
# --------------------------------------------------------------------------


def eval_tree(node):
    """The term AS THE EVALUATOR GROUPS IT — `conform.eval_under_domain`."""

    kind = node[0]
    if kind == "num":
        return ("lit", node[1])
    if kind == "slot":
        return ("var", node[1])
    if kind == "call":
        raise Unbuildable(f"call head {node[1]!r} is outside the evaluator")
    if kind != "op":
        raise Unbuildable(f"node kind {kind!r} has no reading")

    op = node[1]
    if op == "+":
        positives, negatives = [], []
        for arg in node[2]:
            if arg[0] == "op" and arg[1] == "neg":
                negatives.append(eval_tree(arg[2][0]))
            else:
                positives.append(eval_tree(arg))
        # A `neg` is legal ONLY here, as an immediate operand of `+`, where
        # it is binary subtraction wearing the parser's spelling. Anywhere
        # else it is unary negation of a positive quantity, which
        # `eval_under_domain` REFUSES over Nat rather than clamping — see the
        # comment there about a quarter of the ground class deciding for a
        # reason that was not the statement's. The `neg` branch below is
        # what catches every other position.
        head = _fold("add", positives, ("lit", 0))
        if not negatives:
            return head
        return ("sub", head, _fold("add", negatives, ("lit", 0)))
    if op == "*":
        numerators, denominators = conform._split_division(node[2])
        head = _fold("mul", [eval_tree(a) for a in numerators], ("lit", 1))
        if not denominators:
            return head
        return ("div", head,
                _fold("mul", [eval_tree(a) for a in denominators], ("lit", 1)))
    if op == "inv":
        return ("div", ("lit", 1), eval_tree(node[2][0]))
    if op == "^":
        return ("pow", eval_tree(node[2][0]), eval_tree(node[2][1]))
    if op == "neg":
        # Unreachable from an admitted W0 candidate: a bare `neg` outside a
        # `+` node is refused by `eval_under_domain` over Nat, so no point
        # ever reaches it. It refuses here for the same reason rather than
        # inventing Nat's missing negation.
        raise Unbuildable("unary negation has no value in Nat")
    raise Unbuildable(f"operator {op!r} has no reading")


def surface_tree(node):
    """The term AS WRITTEN — operands folded strictly left to right."""

    kind = node[0]
    if kind == "num":
        return ("lit", node[1])
    if kind == "slot":
        return ("var", node[1])
    if kind == "call":
        raise Unbuildable(f"call head {node[1]!r} is outside the evaluator")
    if kind != "op":
        raise Unbuildable(f"node kind {kind!r} has no reading")

    op = node[1]
    if op == "+":
        accumulator = None
        for arg in node[2]:
            negated = arg[0] == "op" and arg[1] == "neg"
            piece = surface_tree(arg[2][0] if negated else arg)
            if accumulator is None:
                accumulator = ("sub", ("lit", 0), piece) if negated else piece
            else:
                accumulator = ("sub" if negated else "add", accumulator, piece)
        return accumulator if accumulator is not None else ("lit", 0)
    if op == "*":
        accumulator = None
        for arg in node[2]:
            inverted = arg[0] == "op" and arg[1] == "inv"
            piece = surface_tree(arg[2][0] if inverted else arg)
            if accumulator is None:
                accumulator = ("div", ("lit", 1), piece) if inverted else piece
            else:
                accumulator = ("div" if inverted else "mul", accumulator, piece)
        return accumulator if accumulator is not None else ("lit", 1)
    if op == "inv":
        return ("div", ("lit", 1), surface_tree(node[2][0]))
    if op == "^":
        return ("pow", surface_tree(node[2][0]), surface_tree(node[2][1]))
    if op == "neg":
        raise Unbuildable("unary negation has no value in Nat")
    raise Unbuildable(f"operator {op!r} has no reading")


def _fold(operator: str, pieces: list, empty):
    if not pieces:
        return empty
    accumulator = pieces[0]
    for piece in pieces[1:]:
        accumulator = (operator, accumulator, piece)
    return accumulator


# --------------------------------------------------------------------------
# Rendering into core Lean over Nat
# --------------------------------------------------------------------------

_INFIX = {"add": "+", "sub": "-", "mul": "*", "div": "/", "pow": "^"}


def render(tree) -> str:
    """Fully parenthesised, so Lean's precedence table never enters it."""

    kind = tree[0]
    if kind == "lit":
        number = Fraction(str(tree[1]))
        if number.denominator != 1 or number < 0:
            raise Unbuildable(f"literal {number} is not a Nat")
        return str(number.numerator)
    if kind == "var":
        return tree[1]
    if kind == "pow":
        exponent = tree[2]
        if exponent[0] != "lit":
            raise Unbuildable("a computed exponent has no Nat rendering")
        return f"({render(tree[1])} ^ {render(exponent)})"
    return f"({render(tree[1])} {_INFIX[kind]} {render(tree[2])})"


def _relation(symbol: str) -> str:
    if symbol not in {"=", "<", ">", "<=", ">="}:
        raise Unbuildable(f"relation {symbol!r} has no rendering")
    return symbol


# --------------------------------------------------------------------------
# The obligation
# --------------------------------------------------------------------------


def _side(conclusion, builder) -> tuple:
    return (builder(conclusion[2][0]), builder(conclusion[2][1]))


def build(program, self_comparison: bool = False) -> dict:
    """One `agreement_lemma` obligation, or a `rejected_trivial` reason.

    `self_comparison=True` builds B4's trap: the SAME reading on both sides
    of the iff. It must come back `rejected_trivial`, and it comes back that
    way by the ordinary structural test rather than by a special case — a
    special case would be an instrument that recognises the trap rather than
    one the trap can catch.
    """

    domain = (program.carrier, program.division, program.subtraction)
    if domain not in SUPPORTED:
        raise Unbuildable(f"domain {domain} is outside this slice")
    if not program.variables:
        raise Unbuildable("no quantifier: the ground class is E1's, not this")

    relation = _relation(program.conclusion[1])
    left_eval, right_eval = _side(program.conclusion, eval_tree)
    if self_comparison:
        left_surface, right_surface = left_eval, right_eval
    else:
        left_surface, right_surface = _side(program.conclusion, surface_tree)

    trivial = (left_eval, right_eval) == (left_surface, right_surface)

    guards = []
    for conjunct in program.guard_conjuncts:
        guards.append(
            f"({render(eval_tree(conjunct[2][0]))} "
            f"{_relation(conjunct[1])} "
            f"{render(eval_tree(conjunct[2][1]))})")

    binder = " ".join(program.variables)
    evaluated = (f"({render(left_eval)} {relation} {render(right_eval)})")
    as_written = (f"({render(left_surface)} {relation} "
                  f"{render(right_surface)})")
    body = f"{evaluated} ↔ {as_written}"
    if guards:
        body = f"{' ∧ '.join(guards)} → ({body})"

    statement = f"∀ ({binder} : Nat), {body}"
    return {
        "statement_id": program.statement_id,
        "obligation": statement,
        "obligation_shape": "forall x in D: eval(S)(x) <-> S(x)",
        "evaluated_reading": evaluated,
        "as_written_reading": as_written,
        "guard_conjuncts_rendered": guards,
        "domain": {"carrier": program.carrier, "division": program.division,
                   "subtraction": program.subtraction},
        "variables": list(program.variables),
        "trivial_by_construction": trivial,
        "trivial_reason": (
            "the evaluator's grouping is a no-op on this term: the two "
            "readings are the SAME TREE, so the obligation is `P ↔ P` and "
            "discharging it would measure nothing"
            if trivial else ""
        ),
        "lean_source": f"example : {statement} := by omega\n",
        "tactic": "omega",
        "tactic_is_core": (
            "Lean 4 core's `omega` decides linear arithmetic over Nat and Int "
            "INCLUDING truncated subtraction and division by literals — which "
            "is exactly why W0's fragment is the linear one. No Mathlib, and "
            "Mathlib stays outside the hermetic budget as design law."
        ),
    }
