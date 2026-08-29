#!/usr/bin/env python3
"""ECHO's import-disjoint reader for the committed foreign-voice dialect.

The reader deliberately imports no repository module. It reads the committed
JSON table, applies longest phrase match, and emits space-separated Lean token
text. It is not algorithmically independent of the renderer's inverse: the
same bijective table determines both. DESIGN-echo B4 buys code separation;
the later scramble arm, if licensed, tests the remaining dependence.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEXICON_PATH = ROOT / "data" / "foreign_voice" / "lexicon.json"

_UNITS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen",
    "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
)
_UNIT = {word: value for value, word in enumerate(_UNITS)}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
         "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_SCALE = {"thousand": 10**3, "million": 10**6, "billion": 10**9,
          "trillion": 10**12}
_NUMERAL_WORDS = frozenset(_UNIT) | frozenset(_TENS) | frozenset(_SCALE) | {
    "hundred", "negative", "point"
}


class ReparseError(ValueError):
    """The sentence is outside the registered foreign-voice language."""


def _is_numeral_word(word: str) -> bool:
    if word in _NUMERAL_WORDS:
        return True
    left, separator, right = word.partition("-")
    return bool(separator and left in _TENS and 1 <= _UNIT.get(right, -1) <= 9)


def _integer(words: list[str]) -> int:
    if not words:
        raise ReparseError("empty numeral")
    negative = words[:1] == ["negative"]
    body = words[1:] if negative else words
    if not body:
        raise ReparseError("negative without a magnitude")
    total = current = 0
    for word in body:
        if word in _UNIT:
            current += _UNIT[word]
        elif word in _TENS:
            current += _TENS[word]
        elif "-" in word:
            left, _, right = word.partition("-")
            if left not in _TENS or not 1 <= _UNIT.get(right, -1) <= 9:
                raise ReparseError(f"unknown numeral compound {word!r}")
            current += _TENS[left] + _UNIT[right]
        elif word == "hundred":
            current *= 100
        elif word in _SCALE:
            total += current * _SCALE[word]
            current = 0
        else:
            raise ReparseError(f"unknown numeral word {word!r}")
    value = total + current
    return -value if negative else value


def _numeral_token(words: list[str]) -> str:
    if "point" not in words:
        return str(_integer(words))
    pivot = words.index("point")
    head, tail = words[:pivot], words[pivot + 1:]
    if not head or not tail or any(word not in _UNIT or _UNIT[word] > 9
                                   for word in tail):
        raise ReparseError("malformed decimal numeral")
    negative = head[:1] == ["negative"]
    magnitude = _integer(head[1:] if negative else head)
    if magnitude < 0:
        raise ReparseError("double-signed decimal numeral")
    return f"{'-' if negative else ''}{magnitude}." + "".join(
        str(_UNIT[word]) for word in tail
    )


def _table(path: Path = LEXICON_PATH) -> tuple[dict[tuple[str, ...], str], str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    phrase_to_token: dict[tuple[str, ...], str] = {}
    for section in ("binders", "connectives", "relations", "operators",
                    "types", "structural"):
        for token, phrase in raw[section].items():
            key = tuple(phrase.split())
            if key in phrase_to_token:
                raise ReparseError(f"duplicate phrase {phrase!r}")
            phrase_to_token[key] = token
    marker = raw["slot_marker"]
    phrase_to_token[(marker["word"],)] = marker.get("token_prefix", "v")
    return phrase_to_token, marker["word"], marker.get("token_prefix", "v")


def reparse(surface: str, lexicon_path: Path = LEXICON_PATH) -> str:
    """Return the single table-determined Lean token string for ``surface``."""
    table, slot_word, slot_prefix = _table(lexicon_path)
    words = surface.split()
    longest = max(map(len, table))
    out: list[str] = []
    index = 0
    while index < len(words):
        phrase = next(
            (tuple(words[index:index + size])
             for size in range(min(longest, len(words) - index), 0, -1)
             if tuple(words[index:index + size]) in table),
            None,
        )
        if phrase is not None:
            index += len(phrase)
            if phrase == (slot_word,):
                start = index
                while index < len(words) and _is_numeral_word(words[index]):
                    index += 1
                if start == index:
                    raise ReparseError("slot marker is not followed by a numeral")
                out.append(f"{slot_prefix}{_integer(words[start:index])}")
            else:
                out.append(table[phrase])
            continue
        start = index
        while index < len(words) and _is_numeral_word(words[index]):
            index += 1
        if start == index:
            raise ReparseError(
                f"{words[index]!r} is neither a table phrase nor a numeral word"
            )
        out.append(_numeral_token(words[start:index]))
    return " ".join(out)


__all__ = ["LEXICON_PATH", "ReparseError", "reparse"]
