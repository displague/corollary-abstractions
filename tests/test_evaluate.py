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
    MAX_RESULT_DIGITS,
    EvalError,
    ResourceBound,
    evaluate,
    find_bindings,
    find_expression,
    refuse_if_unrenderable,
    verify,
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


class TheExponentBoundRefusesByName(unittest.TestCase):
    """E0e (ROADMAP-v0.20 §4c): a bound that refuses, not an exception that escapes.

    The defect this pins was specific and easy to misread as a hang: the
    computation SUCCEEDED and the printing raised an uncaught `ValueError`,
    because CPython caps `int` -> `str` at 4,300 digits. A served path whose
    refusal is an uncaught exception is not refusing.
    """

    def test_a_power_too_wide_to_render_refuses_by_name(self) -> None:
        with self.assertRaises(ResourceBound) as caught:
            evaluate("2 ^ 20000")
        message = str(caught.exception)
        self.assertIn("digits", message)
        self.assertIn(f"{MAX_RESULT_DIGITS:,}", message)
        self.assertIn("Nothing was computed", message)

    def test_the_refusal_is_a_subclass_so_old_callers_still_catch_it(self):
        """A caller that only knows `EvalError` must not start crashing."""
        self.assertTrue(issubclass(ResourceBound, EvalError))
        with self.assertRaises(EvalError):
            evaluate("2 ^ 20000")

    def test_it_refuses_before_computing_rather_than_after(self) -> None:
        """`2^200000` computes in microseconds; the cost is the rendering.

        A bound checked after the fact would still have done the work. This
        asserts the refusal is fast enough that no such power was built.
        """
        import time

        started = time.perf_counter()
        with self.assertRaises(ResourceBound):
            evaluate("2 ^ 2000000")
        self.assertLess(time.perf_counter() - started, 0.5)

    def test_a_wide_but_renderable_power_is_still_served_exactly(self) -> None:
        """The bound is printability, not a dislike of long answers.

        BACKLOG cites `(100+1)^1000` as evidence of unboundedness, not as a
        defect: it is 2,005 digits, it renders, and its value is right.
        Refusing it would be declining arithmetic this evaluator can do.
        """
        result = evaluate("(100+1)^1000")
        rendered = result.formatted()
        self.assertEqual(len(rendered.lstrip("-")), 2005)
        self.assertLess(len(rendered.lstrip("-")), MAX_RESULT_DIGITS)
        self.assertEqual(result.value, Fraction(101) ** 1000)

    def test_everything_the_bound_admits_can_actually_be_rendered(self) -> None:
        """The property the bound exists to guarantee, asserted directly."""
        for expression in ("2 ^ 100", "3 ^ 5", "(100+1)^1000", "10 ^ 4000"):
            with self.subTest(expression=expression):
                result = evaluate(expression)
                self.assertIsInstance(result.formatted(), str)

    def test_a_negative_exponent_is_bounded_on_the_same_estimate(self) -> None:
        with self.assertRaises(ResourceBound):
            evaluate("2 ^ (0 - 20000)")

    def test_small_bases_do_not_trip_the_bound(self) -> None:
        """1 and 0 stay cheap at any exponent; the estimate must know that."""
        self.assertEqual(evaluate("1 ^ 100000").value, Fraction(1))
        self.assertEqual(evaluate("0 ^ 100000").value, Fraction(0))


class TheBoundHoldsWhereEveryResultPasses(unittest.TestCase):
    """H2: a per-node bound is a bound on one operator, not a bound.

    §4c checked the `^` node, and the adversarial review escaped it in one
    line: two admissible powers multiplied together build a value the check
    never saw, and the PRINT raised the same uncaught `ValueError` §4c
    existed to abolish. The check now sits at the rendering boundary, which
    every served value passes through by construction.
    """

    ESCAPE = "(10 ^ 4000) * (10 ^ 4000)"

    def test_multiplied_powers_refuse_by_name(self) -> None:
        result = evaluate(self.ESCAPE)          # the value builds fine
        with self.assertRaises(ResourceBound) as caught:
            result.formatted()                  # showing it is what refuses
        self.assertIn(f"{MAX_RESULT_DIGITS:,}", str(caught.exception))

    def test_the_escape_never_raises_an_uncaught_valueerror(self) -> None:
        """The exact failure mode: computed, then crashed while printing."""
        try:
            evaluate(self.ESCAPE).formatted()
        except ResourceBound:
            pass
        except ValueError as exc:  # pragma: no cover - the defect returning
            self.assertIsInstance(
                exc, ResourceBound,
                f"an uncaught ValueError escaped again: {exc}",
            )

    def test_a_relation_over_oversized_values_refuses_too(self) -> None:
        """`Verification._fmt` is the other way a number reaches a person."""
        checked = verify(f"{self.ESCAPE} = 1")
        with self.assertRaises(ResourceBound):
            checked.rendered()

    def test_the_guard_admits_everything_it_can_render(self) -> None:
        for expression in ("2 ^ 100", "3 ^ 5", "(100+1)^1000", "10 ^ 4000"):
            with self.subTest(expression=expression):
                self.assertIsInstance(evaluate(expression).formatted(), str)

    def test_the_result_guard_is_callable_on_its_own(self) -> None:
        from fractions import Fraction as F

        refuse_if_unrenderable(F(10) ** 4000)      # renderable
        with self.assertRaises(ResourceBound):
            refuse_if_unrenderable(F(10) ** 8000)  # not
        # A wide DENOMINATOR is just as unrenderable as a wide numerator.
        with self.assertRaises(ResourceBound):
            refuse_if_unrenderable(F(1, 10 ** 8000))


if __name__ == "__main__":
    unittest.main()
