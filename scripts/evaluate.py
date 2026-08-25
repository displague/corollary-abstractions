#!/usr/bin/env python3
"""Exact arithmetic under a frame's bindings — the calculator half.

Four probe questions exposed the same hole:

    suppose x=5, what is the square of x?   -> held the QUESTION as a claim
    when x=5, what is x ^ 2?                -> asked about quantifier nodes
    how many continents are on earth?       -> correctly exhausted
    tell me a story about a chicken         -> exhausted

The third is right. The first two are wrong in the same way: the system
could look statements up and could hold conjecture, but it could not
*compute*. "What is x squared when x is 5" has an exact answer, and by this
project's own rule an exact answer belongs in code rather than in a model or
a lookup.

## Exact, not floating point

Values are `Fraction`s. `1/3` is one third, not 0.333...; `(1/3)*3` is
exactly 1. Results print as integers when they are integers and as exact
fractions otherwise. A calculator that quietly rounds is the thing this
project spent two releases refusing to be.

## Bindings come from the person, never from the corpus

`x = 5` is a supposition: the person said so, and it holds only for this
line. The corpus is never consulted for a variable's value, so nothing here
can turn a typed assumption into a corpus fact. An expression with a free
variable nobody bound is REFUSED with the variable named — not defaulted,
not guessed (P-LS5).

## Parsing is delegated, not reinvented

The expression is read by `match_signatures.tokenize`/`Parser`, the same
front end that reads every committed template. To find the expression inside
a sentence, the text is split on separators and each fragment is offered to
that parser from progressively later starting tokens; the longest fragment
that parses wins. The parser decides what is an expression. This module only
decides what to offer it.
"""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from match_signatures import Parser, TemplateParseError, tokenize  # noqa: E402

#: `x = 5`, `x=5`, `n = -3`, `r = 1.5`. A binding is a name, an equals sign
#: and a literal number -- nothing that could itself need evaluating, so a
#: binding can never smuggle in a computation.
BINDING = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)\b")

#: Where one clause ends and another begins in typed English.
_SEPARATORS = re.compile(r"[,;?]|\bwhat is\b|\bwhen\b|\bthen\b|\bsuppose\b")

_NAMED_POWERS = {"square": 2, "squared": 2, "cube": 3, "cubed": 3}


class EvalError(ValueError):
    """The expression cannot be evaluated exactly."""


class ResourceBound(EvalError):
    """A registered bound refused this computation BY NAME (E0e).

    Distinct from `EvalError` on purpose, and the distinction is the whole
    point of ROADMAP-v0.20 §4c. A plain `EvalError` means *this route cannot
    read that line*, and the router answers by returning `None` so the line
    falls through the chain rather than refusing on everyone else's behalf.
    A `ResourceBound` means *this route read the line, understood it, and
    refuses it* — which must reach the person as a refusal naming the bound,
    not as a fall-through that ends in a generic abstention.
    """


#: The largest decimal result this evaluator will produce, and it is not an
#: arbitrary round number: CPython refuses to convert an int wider than
#: `sys.get_int_max_str_digits()` (4,300 by default) to a string. Above that
#: the computation SUCCEEDS and the *printing* raises an uncaught ValueError
#: — which is what §4c calls crashing rather than refusing, and the two are
#: different products.
#:
#: Setting the bound to the interpreter's own printing limit makes the
#: accept/refuse boundary and the can-it-be-rendered boundary the same number
#: by construction rather than by coincidence. A registered constant rather
#: than a live `sys.get_int_max_str_digits()` read, so the refusal is
#: reproducible on a process that moved the cap.
MAX_RESULT_DIGITS = 4300

#: log10(2), the fallback scale when a magnitude is too large to take
#: `math.log10` of at all. `len(str(n))` would be the obvious way to count
#: digits and is exactly the operation the bound exists to prevent, so the
#: estimate never stringifies anything.
_LOG10_2 = 0.30102999566398119521


def _log10_magnitude(n: int) -> float:
    """log10 of a positive int, accurately where floats reach and safely above.

    `bit_length() * log10(2)` alone was tried and over-refused by about a
    fifth: `10 ** 4000` is 4,001 digits and that estimate called it 4,817, so
    a renderable answer near the edge was declined. Bit length bounds log2,
    not log10, and the slack compounds with the exponent. `math.log10` is
    exact enough wherever it works; the bit-length form is kept only for
    magnitudes past a float's reach, which are far beyond the bound anyway.
    """

    try:
        return math.log10(n)
    except (OverflowError, ValueError):  # pragma: no cover - astronomically rare
        return n.bit_length() * _LOG10_2


def refuse_if_unrenderable(value: "Fraction") -> None:
    """The bound that actually holds, checked where every result must pass.

    §4c bounded the `^` NODE, which the adversarial review escaped in one
    line: `(10 ^ 4000) * (10 ^ 4000)` builds two admissible powers and
    multiplies them, so nothing exceeded a per-node bound and the PRINT
    raised the same uncaught `ValueError` §4c existed to abolish. A bound on
    one operator is a bound on one operator; a bound on the result is a bound.

    So this is checked at the rendering boundary, which every served value
    passes through by construction — `Evaluation.formatted` and
    `Verification._fmt` are the only ways a number reaches a person. The
    per-node check upstream is kept and is NOT redundant: it refuses
    `2^200000` before the power is built, so an unrenderable request costs a
    comparison rather than the arithmetic. This one guarantees that whatever
    is built can be shown.

    Measured from bit lengths, never from `str`, because stringifying is the
    operation that raises.
    """

    widest = max(abs(value.numerator), abs(value.denominator))
    if widest <= 1:
        return
    digits = _log10_magnitude(widest) + 1.0
    if digits > MAX_RESULT_DIGITS:
        raise ResourceBound(
            f"that result is about {int(digits):,} digits wide; this "
            f"evaluator is bounded at {MAX_RESULT_DIGITS:,} digits, which is "
            f"the widest integer this interpreter will render. The value was "
            f"computed exactly and is not being shown, because showing it is "
            f"what this interpreter cannot do."
        )


def _power_digit_estimate(base: "Fraction", power: int) -> float:
    """The decimal width of `base ** power`, without building it.

    Never stringifies and never computes the power, because both are the
    operations the bound exists to prevent. The estimate is tight enough that
    everything it admits renders and nothing renderable is refused near the
    edge — `test_everything_the_bound_admits_can_actually_be_rendered` is the
    assertion of the first half.
    """

    magnitude = max(abs(base.numerator), base.denominator)
    if magnitude <= 1 or power == 0:
        return 1.0
    return abs(power) * _log10_magnitude(magnitude) + 1.0


@dataclass(frozen=True)
class Evaluation:
    expression: str
    bindings: dict[str, Fraction]
    value: Fraction
    free_variables: tuple[str, ...] = ()

    def formatted(self) -> str:
        refuse_if_unrenderable(self.value)
        if self.value.denominator == 1:
            return str(self.value.numerator)
        return f"{self.value.numerator}/{self.value.denominator}"


def find_bindings(text: str) -> dict[str, Fraction]:
    """Every `name = number` the person typed on this line."""
    out: dict[str, Fraction] = {}
    for name, literal in BINDING.findall(text):
        out[name] = Fraction(literal)
    return out


def _strip_bindings(text: str) -> str:
    return BINDING.sub(" ", text)


def _expand_named_powers(text: str) -> str:
    """`the square of x` -> `x ^ 2`, `x squared` -> `x ^ 2`.

    Two fixed English forms for an operator the grammar already has. This is
    a rewrite of two phrasings, not comprehension: anything else is left
    alone and will simply fail to parse.
    """
    lowered = text
    for word, power in _NAMED_POWERS.items():
        lowered = re.sub(
            rf"\b{word}\s+of\s+([a-zA-Z][a-zA-Z0-9_]*|\d+)\b",
            rf"\1 ^ {power}",
            lowered,
        )
        lowered = re.sub(
            rf"\b([a-zA-Z][a-zA-Z0-9_]*|\d+)\s+{word}\b",
            rf"\1 ^ {power}",
            lowered,
        )
    return lowered


def find_expression(text: str) -> str | None:
    """The longest fragment the committed parser accepts as an expression."""
    cleaned = _expand_named_powers(_strip_bindings(text))
    best: str | None = None
    for fragment in _SEPARATORS.split(cleaned):
        words = fragment.split()
        # Every contiguous window, longest first. Dropping only leading words
        # was not enough: "what is x ^ 2 if" needs the trailing `if` gone too,
        # and that phrasing ("... if x=5") is at least as natural as the one
        # that happened to work. The parser is the judge in every case; this
        # only decides what to offer it.
        for length in range(len(words), 0, -1):
            for start in range(0, len(words) - length + 1):
                candidate = " ".join(words[start:start + length]).strip()
                if not candidate or not any(c.isalnum() for c in candidate):
                    continue
                try:
                    parsed = Parser(tokenize(candidate)).parse()
                except (TemplateParseError, ValueError, IndexError):
                    continue
                # A lone identifier or numeral parses fine and is useless:
                # "does 2+2=4" was yielding `does`, a bare slot, and the
                # relation behind it was never seen. An expression worth
                # evaluating is compound or a relation.
                if parsed[0] in {"slot", "num"}:
                    continue
                if best is None or len(candidate) > len(best):
                    best = candidate
                break
            if best is not None:
                break
    return best


def _eval_tree(tree: tuple, bindings: dict[str, Fraction],
               free: set[str]) -> Fraction:
    kind = tree[0]
    if kind == "num":
        return Fraction(str(tree[1]))
    if kind == "slot":
        name = tree[1]
        if name not in bindings:
            free.add(name)
            return Fraction(0)
        return bindings[name]
    if kind == "op":
        op = tree[1]
        args = [_eval_tree(a, bindings, free) for a in tree[2]]
        if op == "+":
            return sum(args, Fraction(0))
        if op == "*":
            out = Fraction(1)
            for a in args:
                out *= a
            return out
        if op == "neg":
            return -args[0]
        if op == "inv":
            if args[0] == 0:
                raise EvalError("division by zero")
            return Fraction(1) / args[0]
        if op == "^":
            base, exponent = args
            if exponent.denominator != 1:
                raise EvalError("only integer exponents are exact here")
            power = int(exponent)
            # E0e: refuse BEFORE computing. `2^200000` computes in
            # microseconds and then cannot be printed, so a bound checked
            # after the fact would still have done the work and still have
            # nothing to show for it.
            estimate = _power_digit_estimate(base, power)
            if estimate > MAX_RESULT_DIGITS:
                raise ResourceBound(
                    f"that power is about {int(estimate):,} digits wide; this "
                    f"evaluator is bounded at {MAX_RESULT_DIGITS:,} digits, "
                    f"which is the widest integer this interpreter will "
                    f"render. Nothing was computed and nothing is claimed."
                )
            return base ** power
        raise EvalError(f"no exact rule for operator {op!r}")
    if kind == "rel":
        raise EvalError(
            "that is a relation, not a value; ask for one side of it"
        )
    raise EvalError(f"no exact rule for {kind!r}")


#: Relations the exact evaluator can decide. `NE` is the parser's spelling of
#: the not-equal glyph.
_RELATIONS = {
    "=": lambda a, b: a == b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


@dataclass(frozen=True)
class Verification:
    """A relation decided exactly: `2 + 2 = 4` is true, and provably so."""

    relation: str
    left: Fraction
    right: Fraction
    holds: bool
    bindings: dict[str, Fraction]

    def _fmt(self, value: Fraction) -> str:
        refuse_if_unrenderable(value)
        return (
            str(value.numerator) if value.denominator == 1
            else f"{value.numerator}/{value.denominator}"
        )

    def rendered(self) -> list[str]:
        out = [
            f"relation   : {self.relation}",
            f"left       : {self._fmt(self.left)}",
            f"right      : {self._fmt(self.right)}",
            f"holds      : {'yes' if self.holds else 'no'}",
        ]
        if self.bindings:
            out.append(
                "given      : "
                + ", ".join(
                    f"{k} = {self._fmt(v)}" for k, v in sorted(self.bindings.items())
                )
            )
        out.append(
            "decided by exact arithmetic on what you typed; no corpus "
            "statement was consulted and none is claimed"
        )
        return out


def verify(text: str) -> Verification:
    """Decide a typed relation exactly. `does 2+2=4?` is a question with an
    answer, and refusing it because the parser calls it a relation was a gap,
    not a principle. Truth here is arithmetic truth about the numbers typed —
    never a claim that the corpus proves it.
    """
    bindings = find_bindings(text)
    expression = find_expression(text)
    if expression is None:
        raise EvalError("no relation to check")
    try:
        tree = Parser(tokenize(expression)).parse()
    except (TemplateParseError, ValueError, IndexError) as exc:
        raise EvalError(f"cannot parse {expression!r}: {exc}") from None
    if tree[0] != "rel" or tree[1] not in _RELATIONS:
        raise EvalError("not a relation this evaluator can decide")
    free: set[str] = set()
    left = _eval_tree(tree[2][0], bindings, free)
    right = _eval_tree(tree[2][1], bindings, free)
    if free:
        raise EvalError(
            "nothing was said about " + ", ".join(sorted(free))
            + "; bind it like `x = 5` and nothing will be assumed for you"
        )
    return Verification(
        relation=expression,
        left=left,
        right=right,
        holds=_RELATIONS[tree[1]](left, right),
        bindings=bindings,
    )


def evaluate(text: str) -> Evaluation:
    """Read bindings and an expression out of `text`, then compute exactly."""
    bindings = find_bindings(text)
    expression = find_expression(text)
    if expression is None:
        raise EvalError("no expression to evaluate")
    try:
        tree = Parser(tokenize(expression)).parse()
    except (TemplateParseError, ValueError, IndexError) as exc:
        raise EvalError(f"cannot parse {expression!r}: {exc}") from None
    free: set[str] = set()
    value = _eval_tree(tree, bindings, free)
    if free:
        raise EvalError(
            "nothing was said about " + ", ".join(sorted(free))
            + "; bind it like `x = 5` and nothing will be assumed for you"
        )
    return Evaluation(expression, bindings, value)


def render(result: Evaluation) -> list[str]:
    out = [f"expression : {result.expression}"]
    if result.bindings:
        given = ", ".join(
            f"{k} = {v.numerator if v.denominator == 1 else v}"
            for k, v in sorted(result.bindings.items())
        )
        out.append(f"given      : {given}")
    out.append(f"exact      : {result.formatted()}")
    out.append(
        "computed symbolically from what you typed; no corpus statement was "
        "consulted and none is claimed"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("text", nargs="+")
    args = ap.parse_args(argv)
    try:
        print("\n".join(render(evaluate(" ".join(args.text)))))
    except EvalError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
