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


@dataclass(frozen=True)
class Evaluation:
    expression: str
    bindings: dict[str, Fraction]
    value: Fraction
    free_variables: tuple[str, ...] = ()

    def formatted(self) -> str:
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
                    Parser(tokenize(candidate)).parse()
                except (TemplateParseError, ValueError, IndexError):
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
            return base ** int(exponent)
        raise EvalError(f"no exact rule for operator {op!r}")
    if kind == "rel":
        raise EvalError(
            "that is a relation, not a value; ask for one side of it"
        )
    raise EvalError(f"no exact rule for {kind!r}")


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
