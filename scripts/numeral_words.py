#!/usr/bin/env python3
"""The registered numeral pair: integers, decimals and fractions <-> English.

DESIGN-sans-template-rendering §3 draws a hard line through the realization
gate.  The *lexicon* is a finite, reviewed, bijective table; numerals are not,
because the corpus's literals are unbounded (`data/lean_workbook` alone carries
407 distinct integer-valued literals and 21 non-integer ones).  So the design
registers numerals as **a genuine algorithmic pair with its own tests and its
own scrambled-numeral control**, on the stated ground that *"an unregistered
numeral inverse is the hole this gate would otherwise leak through"*.

This module is that pair, and nothing else.  It has no knowledge of terms,
operators, precedence or bracketing; it converts between a number and a word
sequence, in both directions, and it refuses anything it cannot convert.

Registered domain (everything outside it RAISES, and `realize_term` turns the
raise into a refusal rather than a guess):

- integers with ``abs(n) < 10**15`` — short scale, so the largest sayable
  magnitude is "nine hundred ninety-nine trillion nine hundred ninety-nine
  billion ...".  The corpus's own extreme is a 76-digit lean_workbook literal
  that floats to ``8.888...e+75``; that is outside the domain and refuses.
- non-integer floats whose ``repr`` is a plain decimal (``\\d+\\.\\d+``),
  rendered digit-by-digit after the word "point".  ``repr`` is the shortest
  string that floats back to the identical value, so the pair is exact rather
  than approximately exact.
- ``fractions.Fraction`` values, rendered "N over M".  The corpus's exact
  values are Fractions — `scripts/evaluate.py` answers ``19 / 13`` with the
  exact value ``19/13``, and the v0.17 throughput run served exactly that
  string — so the pair covers them rather than leaving the exact surface
  unsayable.

**Canonicality is enforced in both directions.**  Every reading function
re-renders its result and refuses if the re-rendering is not the input it was
given.  That makes the accepted word language exactly the emitted word
language, which is what "bijective" has to mean for a gate to lean on it: it
is not enough that the reader accepts what the writer emits, the reader must
also reject everything the writer would never emit.  Without this,
"twenty ten" would read as 30 and the inverse would be a many-to-one map
dressed as a pair.

**Vocabulary disjointness.**  `NUMERAL_VOCABULARY` is the complete set of
words this module can emit.  `data/realization/lexicon.json` is refused at
load if any lexicon phrase uses one of them, which is what lets the stage-1
inverter decide "numeral run or table phrase?" by looking at one word.
"""

from __future__ import annotations

import re
from fractions import Fraction

# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------

UNITS: tuple[str, ...] = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
)

TENS: dict[int, str] = {
    20: "twenty", 30: "thirty", 40: "forty", 50: "fifty",
    60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety",
}

# Short scale, largest first. Extending this table extends `MAX_INT`; it is a
# reviewed diff exactly as a lexicon row is.
SCALES: tuple[tuple[int, str], ...] = (
    (10 ** 12, "trillion"),
    (10 ** 9, "billion"),
    (10 ** 6, "million"),
    (10 ** 3, "thousand"),
)

HUNDRED_WORD = "hundred"
NEGATIVE_WORD = "negative"
POINT_WORD = "point"
FRACTION_WORD = "over"

MAX_INT = 10 ** 15

_UNIT_VALUE = {w: i for i, w in enumerate(UNITS)}
_TENS_VALUE = {w: v for v, w in TENS.items()}
_SCALE_VALUE = {w: v for v, w in SCALES}

#: Every word this module can emit. `realization_lexicon` refuses any lexicon
#: phrase that uses one of these, so a single word decides numeral-vs-phrase.
NUMERAL_VOCABULARY: frozenset[str] = frozenset(
    set(UNITS)
    | set(TENS.values())
    | set(_SCALE_VALUE)
    | {HUNDRED_WORD, NEGATIVE_WORD, POINT_WORD, FRACTION_WORD}
)

_DECIMAL_RE = re.compile(r"(-?)(\d+)\.(\d+)")


class NumeralError(ValueError):
    """A value outside the registered domain, or words outside its language."""


def is_numeral_word(word: str) -> bool:
    """True for any word a numeral rendering can contain.

    Hyphenated compounds ("twenty-four") are single whitespace-delimited words
    and count, so the disjointness rule the lexicon loader enforces sees them.
    """
    if word in NUMERAL_VOCABULARY:
        return True
    if "-" in word:
        left, _, right = word.partition("-")
        return left in _TENS_VALUE and right in _UNIT_VALUE
    return False


# --------------------------------------------------------------------------
# Integers
# --------------------------------------------------------------------------


def _under_thousand(n: int) -> str:
    assert 0 < n < 1000
    parts: list[str] = []
    hundreds, rest = divmod(n, 100)
    if hundreds:
        parts.append(f"{UNITS[hundreds]} {HUNDRED_WORD}")
    if rest:
        if rest < 20:
            parts.append(UNITS[rest])
        else:
            tens, unit = divmod(rest, 10)
            parts.append(TENS[tens * 10] + (f"-{UNITS[unit]}" if unit else ""))
    return " ".join(parts)


def int_to_words(n: int) -> str:
    """Render an integer in the registered domain as English words."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise NumeralError(f"not an int: {n!r}")
    if abs(n) >= MAX_INT:
        raise NumeralError(
            f"magnitude {abs(n)} is outside the registered numeral domain "
            f"(|n| < {MAX_INT})"
        )
    if n < 0:
        return f"{NEGATIVE_WORD} {int_to_words(-n)}"
    if n == 0:
        return UNITS[0]
    parts: list[str] = []
    rest = n
    for scale, name in SCALES:
        chunk, rest = divmod(rest, scale)
        if chunk:
            parts.append(f"{_under_thousand(chunk)} {name}")
    if rest:
        parts.append(_under_thousand(rest))
    return " ".join(parts)


def words_to_int(text: str) -> int:
    """Read English words back to an integer, refusing non-canonical input.

    Refusal on non-canonical input is the point: "twenty ten" and "one one"
    are arithmetically readable and are rejected, because the writer never
    emits them and a reader that accepts more than the writer emits is not
    half of a bijection.
    """
    words = text.split()
    if not words:
        raise NumeralError("empty numeral")
    negative = words[0] == NEGATIVE_WORD
    body = words[1:] if negative else words
    if not body:
        raise NumeralError("`negative` with no magnitude")

    total = 0
    current = 0
    for word in body:
        if "-" in word:
            left, _, right = word.partition("-")
            if left not in _TENS_VALUE or right not in _UNIT_VALUE:
                raise NumeralError(f"unknown numeral compound {word!r}")
            value = _UNIT_VALUE[right]
            if not 1 <= value <= 9:
                raise NumeralError(f"unknown numeral compound {word!r}")
            current += _TENS_VALUE[left] + value
        elif word in _UNIT_VALUE:
            current += _UNIT_VALUE[word]
        elif word in _TENS_VALUE:
            current += _TENS_VALUE[word]
        elif word == HUNDRED_WORD:
            current *= 100
        elif word in _SCALE_VALUE:
            total += current * _SCALE_VALUE[word]
            current = 0
        else:
            raise NumeralError(f"unknown numeral word {word!r}")
    value = total + current
    if negative:
        value = -value

    if int_to_words(value) != " ".join(words):
        raise NumeralError(f"non-canonical numeral words: {text!r}")
    return value


# --------------------------------------------------------------------------
# Numbers (integers and plain decimals)
# --------------------------------------------------------------------------


def number_to_words(value: float | int) -> str:
    """Render an int or a float in the registered domain as English words."""
    if isinstance(value, bool):
        raise NumeralError(f"not a number: {value!r}")
    if isinstance(value, int):
        return int_to_words(value)
    if not isinstance(value, float):
        raise NumeralError(f"not a number: {value!r}")
    if value != value or value in (float("inf"), float("-inf")):
        raise NumeralError(f"not a finite float: {value!r}")
    if value.is_integer():
        return int_to_words(int(value))
    match = _DECIMAL_RE.fullmatch(repr(value))
    if match is None:
        # repr fell back to scientific notation; the template tokenizer has no
        # spelling for it either, so this is a refusal, not a rounding call.
        raise NumeralError(
            f"float {value!r} has no plain-decimal spelling in the "
            f"registered numeral domain"
        )
    sign, integral, fractional = match.groups()
    head = int_to_words(int(integral))
    if sign:
        head = f"{NEGATIVE_WORD} {head}"
    digits = " ".join(UNITS[int(d)] for d in fractional)
    return f"{head} {POINT_WORD} {digits}"


def words_to_numeral_token(text: str) -> str:
    """Read words back to the ASCII literal the template tokenizer accepts.

    This is what the stage-1 inverter emits: a token string, never a value.
    `float(words_to_numeral_token(number_to_words(v))) == v` for every `v` in
    the registered domain, which is the property the round-trip gate needs.
    """
    if f" {POINT_WORD} " not in f" {text} ":
        return str(words_to_int(text))
    head, _, tail = text.partition(f" {POINT_WORD} ")
    if not tail:
        raise NumeralError(f"`{POINT_WORD}` with no digits: {text!r}")
    digits = []
    for word in tail.split():
        if word not in _UNIT_VALUE or _UNIT_VALUE[word] > 9:
            raise NumeralError(f"not a decimal digit word: {word!r}")
        digits.append(str(_UNIT_VALUE[word]))
    # The sign is read off the head directly rather than through
    # `words_to_int`, because `-0.25` renders as "negative zero point two five"
    # and "negative zero" is not a canonical INTEGER rendering — `int_to_words`
    # spells 0 as "zero" and nothing else. Delegating would refuse a value the
    # writer emits, which is the one failure a bijection may not have.
    head_words = head.split()
    negative = head_words[:1] == [NEGATIVE_WORD]
    integral = words_to_int(" ".join(head_words[1:] if negative else head_words))
    if integral < 0:
        raise NumeralError(f"double sign in {text!r}")
    token = f"{'-' if negative else ''}{integral}.{''.join(digits)}"
    if number_to_words(float(token)) != text:
        raise NumeralError(f"non-canonical decimal words: {text!r}")
    return token


def words_to_number(text: str) -> float:
    """Read words back to a float."""
    return float(words_to_numeral_token(text))


# --------------------------------------------------------------------------
# Fractions
# --------------------------------------------------------------------------


def fraction_to_words(value: Fraction) -> str:
    """Render an exact rational as "N over M" (or as an integer if it is one).

    `scripts/evaluate.py` answers with exact `Fraction`s — the v0.17 run served
    `exact      : 19/13` — so the exact surface has a spelling here rather than
    being unsayable.
    """
    if not isinstance(value, Fraction):
        raise NumeralError(f"not a Fraction: {value!r}")
    if value.denominator == 1:
        return int_to_words(value.numerator)
    numerator = value.numerator
    prefix = ""
    if numerator < 0:
        prefix = f"{NEGATIVE_WORD} "
        numerator = -numerator
    return (f"{prefix}{int_to_words(numerator)} "
            f"{FRACTION_WORD} {int_to_words(value.denominator)}")


def words_to_fraction(text: str) -> Fraction:
    """Read "N over M" back to an exact rational, refusing non-canonical input."""
    marker = f" {FRACTION_WORD} "
    if marker not in text:
        return Fraction(words_to_int(text))
    head, _, tail = text.partition(marker)
    negative = head.split()[:1] == [NEGATIVE_WORD]
    numerator = words_to_int(head)
    denominator = words_to_int(tail)
    if denominator <= 0:
        raise NumeralError(f"non-positive denominator in {text!r}")
    value = Fraction(numerator, denominator)
    if fraction_to_words(value) != text:
        raise NumeralError(f"non-canonical fraction words: {text!r}")
    if negative and value >= 0:  # pragma: no cover - covered by the check above
        raise NumeralError(f"sign lost reading {text!r}")
    return value


__all__ = [
    "MAX_INT",
    "NUMERAL_VOCABULARY",
    "NumeralError",
    "fraction_to_words",
    "int_to_words",
    "is_numeral_word",
    "number_to_words",
    "words_to_fraction",
    "words_to_int",
    "words_to_number",
    "words_to_numeral_token",
]
