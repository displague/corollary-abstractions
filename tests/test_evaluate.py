#!/usr/bin/env python3
"""Exact arithmetic: right answers, or a refusal that names what is missing.

A calculator that is usually right is not a calculator. The tests that
matter are exactness (no floating point creeping in) and the refusal to
supply a value nobody typed.
"""

from __future__ import annotations

import sys
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from evaluate import (  # noqa: E402
    EvalError,
    evaluate,
    find_bindings,
    find_expression,
)


class ItComputesExactly(unittest.TestCase):
    def test_the_probe_questions(self) -> None:
        for text in (
            "when x=5, what is x ^ 2?",
            "suppose x=5, what is the square of x?",
            "x = 5, x squared",
        ):
            with self.subTest(text=text):
                self.assertEqual(evaluate(text).value, Fraction(25))

    def test_fractions_stay_exact(self) -> None:
        """1/3 + 1/6 is one half, not 0.49999999999999994."""
        self.assertEqual(evaluate("1 / 3 + 1 / 6").value, Fraction(1, 2))

    def test_a_third_times_three_is_one(self) -> None:
        self.assertEqual(evaluate("(1 / 3) * 3").value, Fraction(1))

    def test_negative_and_nested(self) -> None:
        self.assertEqual(evaluate("(2 + 3) ^ 2 - 5").value, Fraction(20))

    def test_bindings_are_read_from_the_line(self) -> None:
        self.assertEqual(
            find_bindings("let a = 2 and b = -3"),
            {"a": Fraction(2), "b": Fraction(-3)},
        )

    def test_the_expression_is_found_inside_a_sentence(self) -> None:
        self.assertEqual(find_expression("when x=5, what is x ^ 2?"), "x ^ 2")


class ItRefusesRatherThanGuesses(unittest.TestCase):
    def test_an_unbound_variable_is_named_not_defaulted(self) -> None:
        with self.assertRaises(EvalError) as caught:
            evaluate("what is y ^ 2")
        self.assertIn("y", str(caught.exception))

    def test_division_by_zero_refuses(self) -> None:
        with self.assertRaises(EvalError):
            evaluate("1 / 0")

    def test_text_with_no_expression_refuses(self) -> None:
        with self.assertRaises(EvalError):
            evaluate("tell me a story about a chicken")

    def test_a_relation_is_not_a_value(self) -> None:
        with self.assertRaises(EvalError):
            evaluate("x = 5, x ^ 2 = 25")

    def test_a_binding_cannot_smuggle_in_a_computation(self) -> None:
        """`x = 2 + 3` is not a binding; bindings are literals only."""
        self.assertEqual(find_bindings("x = 2 + 3"), {"x": Fraction(2)})


class ComputationIsNotALookup(unittest.TestCase):
    def test_nothing_from_the_corpus_is_consulted(self) -> None:
        """The value comes from the line, so it cannot cite a statement."""
        result = evaluate("x = 7, x ^ 2")
        self.assertEqual(result.value, Fraction(49))
        self.assertEqual(result.bindings, {"x": Fraction(7)})


if __name__ == "__main__":
    unittest.main()
