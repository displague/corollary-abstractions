#!/usr/bin/env python3
"""Load and gate `data/foreign_voice/lexicon.json` — the loanword table.

DESIGN-foreign-voice §3.1 says this table "inherits v0.18's lexicon rules
**whole, cited not restated**": prefix-freeness (L1) and numeral-disjointness
(L2) at `scripts/realization_lexicon.py:30–38`, which `:39–41` explains are
together what make stage one *"a table lookup with no lookahead policy of its
own"*, and the R2b gate list enforced at `:295–317`, where a table that fails
any of them raises at load and *"nothing downstream gets a chance to work
around it"*.

This module is the load and the refusal.  It holds no grammar: no precedence,
no bracketing, no arity.  Where v0.18's loader ends in `_check_emitted_token`
against the byte-frozen Python tokenizer, this one cannot — **the stage-2
reader here is the pinned Lean binary**, which is not callable at import time
and must never become an import-time dependency.  What replaces it is stated
below as F7, and the difference is real rather than cosmetic.

## The gate list, F1–F8

  F1  no duplicate keys in the file (JSON duplicate keys are caught, not
      silently last-wins);
  F2  no two keys share a phrase (forward injective);
  F3  no two keys emit the same token (reverse injective);
  F4  forward(reverse(phrase)) == phrase and reverse(forward(key)) == key for
      every row — the identity composed on both sides;
  F5  every phrase is lowercase ASCII words, and L2 holds;
  F6  L1 holds;
  F7  every emitted token is a single, non-empty, whitespace-free string that
      no numeral run and no other row can produce, and no row emits the
      spelling the slot marker synthesizes;
  F8  the refusal rows are disjoint from the lexicon rows, and every refusal
      names a reason from the closed vocabulary.

### Why F7 is shaped the way it is, and what v0.18 does that this cannot

v0.18's B7 asks the byte-frozen tokenizer directly, because its inverse hands a
*token stream* to that tokenizer and a row emitting `neg` instead of `-` reads
back as a call head — commit 8910138's bug, "a fluent sentence that re-parses
to a DIFFERENT tree".  Here the inverse hands **Lean source text** to the
pinned binary, and the design's own rule closes that hole at the source
instead: the inverse writes every token **space-separated**, so no maximal
munch decision is left for the lexer to get wrong, and there is exactly one
`-` row (numerals are unsigned), so the collision v0.18 legislated around does
not exist to legislate.  What F7 can still check without running Lean is that
every token is one whitespace-free lexeme, that no two rows produce the same
one, and that no row's token can be confused with the slot marker's
synthesized `v<index>`.  That last clause is 8910138's lesson in this dialect:
the one place a value, not a key, can collide.

Whether Lean actually reads each token as this table means it is not asserted
here — it is **measured**, by `tests/test_foreign_voice_lexicon.py`'s
constructive coverage assertion and, at corpus scale, by the registered run.
Saying so is the point: a check this module cannot run must not be described
as if it did.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))

from numeral_words import NUMERAL_VOCABULARY, is_numeral_word  # noqa: E402

DEFAULT_LEXICON_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "foreign_voice" / "lexicon.json"
)

#: The sections whose rows are (dialect token -> English phrase). The key IS
#: the emitted token in every one of them, which is the simplification the
#: dialect buys us over v0.18's canonical tree: there is no `operator_tokens`
#: indirection because no row is keyed by a node name the surface never spells.
_SECTIONS = ("binders", "connectives", "relations", "operators", "types",
             "structural")

_PHRASE_RE = re.compile(r"[a-z]+( [a-z]+)*")

#: The closed refusal vocabulary, mirrored from the file and checked against it.
_REFUSAL_REASONS = (
    "no_lexicon_row",
    "unsupported_numeral",
    "noncanonical_numeral",
    "interpretation_absent",
    "oracle_rejected",
)


class ForeignLexiconError(ValueError):
    """The table is not a bijection, or not readable by longest match."""


def _load_pairs(pairs: list[tuple[str, object]]) -> dict:
    seen: set[str] = set()
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise ForeignLexiconError(f"F1: duplicate key {key!r} in the lexicon file")
        seen.add(key)
        out[key] = value
    return out


@dataclass(frozen=True)
class ForeignLexicon:
    """A loaded, gated table. Immutable; the file is the artifact."""

    path: Path
    lexicon_id: str
    binders: dict[str, str]
    connectives: dict[str, str]
    relations: dict[str, str]
    operators: dict[str, str]
    types: dict[str, str]
    structural: dict[str, str]
    slot_word: str
    slot_prefix: str
    refusals: dict[str, dict]
    #: phrase words -> emitted token, the whole of the inverse's table
    phrase_to_token: dict[tuple[str, ...], str]
    #: key -> phrase, every section merged, for receipts
    key_to_phrase: dict[str, str]
    max_phrase_words: int

    def words_for(self, key: str) -> str:
        try:
            return self.key_to_phrase[key]
        except KeyError:
            raise KeyError(f"no lexicon row for {key!r}") from None

    def covers(self, key: str) -> bool:
        return key in self.key_to_phrase

    def refusal_for(self, key: str) -> dict | None:
        return self.refusals.get(key)

    @property
    def tokens(self) -> tuple[str, ...]:
        """Every dialect token this table can read, longest first.

        Longest first is the tokenizer's own maximal-munch order on the
        *dialect* side: `≥` is one character but `Rat` is three, and a scanner
        that tried `R` first would split a type name into an identifier.
        """
        return tuple(sorted(self.key_to_phrase, key=lambda t: (-len(t), t)))

    def slot_token(self, index: int) -> str:
        """The token the slot marker synthesizes for slot `index`."""
        if index < 0:
            raise ValueError("slot indices are non-negative")
        return f"{self.slot_prefix}{index}"


def load(path: Path | str | None = None) -> ForeignLexicon:
    """Read, gate and return the table. Raises `ForeignLexiconError` on failure."""
    path = Path(path) if path is not None else DEFAULT_LEXICON_PATH
    raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_load_pairs)
    return build(raw, path)


def build(raw: dict, path: Path | str = "<memory>") -> ForeignLexicon:
    """Gate an already-parsed table. Split from `load` so tests can inject."""
    path = Path(path) if not isinstance(path, str) else Path(path)

    for section in _SECTIONS:
        if section not in raw or not isinstance(raw[section], dict):
            raise ForeignLexiconError(f"missing or malformed section {section!r}")
    marker = raw.get("slot_marker")
    if not isinstance(marker, dict) or "word" not in marker:
        raise ForeignLexiconError("missing or malformed `slot_marker`")
    slot_word = marker["word"]
    slot_prefix = marker.get("token_prefix", "v")
    if not isinstance(slot_prefix, str) or not slot_prefix or slot_prefix.isdigit():
        raise ForeignLexiconError(
            f"F7: slot prefix {slot_prefix!r} must be a non-empty non-numeric string"
        )

    # (key, phrase, emitted token, section). The slot marker is a row too — it
    # is a phrase the inverse must read and a token it must emit, so leaving it
    # out of the gates would be leaving out the one row that is generated
    # rather than written down.
    rows: list[tuple[str, str, str, str]] = []
    for section in _SECTIONS:
        for key, phrase in raw[section].items():
            rows.append((key, phrase, key, section))
    rows.append((f"slot_marker:{slot_word}", slot_word, slot_prefix, "slot_marker"))

    # -- F5: phrases are lowercase ASCII words, and L2 holds ---------------
    for key, phrase, _token, _section in rows:
        if not isinstance(phrase, str) or not _PHRASE_RE.fullmatch(phrase):
            raise ForeignLexiconError(
                f"F5: phrase for {key!r} is not lowercase ASCII words: {phrase!r}"
            )
        for word in phrase.split():
            if is_numeral_word(word):
                raise ForeignLexiconError(
                    f"L2: phrase for {key!r} uses the numeral word {word!r}; the "
                    f"inverter could not tell it from a numeral run"
                )

    # -- F2 / F3: injective in both directions -----------------------------
    by_phrase: dict[str, str] = {}
    for key, phrase, _token, _section in rows:
        if phrase in by_phrase:
            raise ForeignLexiconError(
                f"F2: phrase {phrase!r} maps to both {by_phrase[phrase]!r} and "
                f"{key!r}; the table is not injective forward"
            )
        by_phrase[phrase] = key
    by_token: dict[str, str] = {}
    for key, _phrase, token, _section in rows:
        if token in by_token:
            raise ForeignLexiconError(
                f"F3: token {token!r} is emitted by both {by_token[token]!r} and "
                f"{key!r}; the table is not injective in reverse"
            )
        by_token[token] = key

    # -- F4: both compositions are the identity ----------------------------
    # Stated rather than discovered: given F2 and F3 above, this loop CANNOT
    # fail — the two dicts are built from the same rows and F2 has already
    # refused any duplicate phrase. It is kept because F4 is the property the
    # design actually leans on ("forward and reverse readings of every row
    # compose to the identity on both sides"), and a gate list whose entries
    # are only implied by other entries is a gate list a reader has to derive.
    # v0.18's loader carries the same tautology for the same reason. If F2 or
    # F3 is ever weakened, this stops being redundant, which is exactly when a
    # reader would want it to have been here all along.
    key_to_phrase = {key: phrase for key, phrase, _t, _s in rows}
    phrase_to_key = {phrase: key for key, phrase, _t, _s in rows}
    for key, phrase, _token, _section in rows:
        if phrase_to_key[key_to_phrase[key]] != key:
            raise ForeignLexiconError(f"F4: reverse(forward({key!r})) is not {key!r}")
        if key_to_phrase[phrase_to_key[phrase]] != phrase:
            raise ForeignLexiconError(
                f"F4: forward(reverse({phrase!r})) is not {phrase!r}"
            )

    # -- F6 / L1: prefix-free ----------------------------------------------
    word_seqs = {tuple(phrase.split()): key for key, phrase, _t, _s in rows}
    ordered = sorted(word_seqs)
    for i, seq in enumerate(ordered):
        for other in ordered[i + 1:]:
            if len(other) <= len(seq):
                continue
            if other[: len(seq)] != seq:
                break  # sorted: no later phrase can share this prefix either
            raise ForeignLexiconError(
                f"L1: phrase {' '.join(seq)!r} ({word_seqs[seq]!r}) is a proper "
                f"prefix of {' '.join(other)!r} ({word_seqs[other]!r}); longest "
                f"match cannot resolve them"
            )

    # -- F7: every emitted token, keys and generated alike -----------------
    for key, _phrase, token, section in rows:
        _check_emitted_token(key, token, section, slot_prefix)

    # -- F8: refusals are rows this table deliberately does not have -------
    refusals = raw.get("refusals", {})
    if not isinstance(refusals, dict):
        raise ForeignLexiconError("`refusals` must be an object")
    declared = raw.get("refusal_reasons", list(_REFUSAL_REASONS))
    if list(declared) != list(_REFUSAL_REASONS):
        raise ForeignLexiconError(
            f"F8: `refusal_reasons` is {list(declared)!r}; the vocabulary is "
            f"closed at {list(_REFUSAL_REASONS)!r} and widening it is a diff with "
            f"its own review"
        )
    for construct, entry in refusals.items():
        if construct in key_to_phrase:
            raise ForeignLexiconError(
                f"F8: {construct!r} has both a lexicon row and a refusal row; the "
                f"renderer would render it and the register would claim it is "
                f"unspoken, and one of those two artifacts would be lying"
            )
        if not isinstance(entry, dict) or entry.get("reason") not in _REFUSAL_REASONS:
            raise ForeignLexiconError(
                f"F8: refusal row {construct!r} names no reason from the closed "
                f"vocabulary {list(_REFUSAL_REASONS)!r}"
            )

    phrase_to_token = {tuple(phrase.split()): token
                       for _k, phrase, token, _s in rows}
    return ForeignLexicon(
        path=path,
        lexicon_id=raw.get("lexicon_id", "<unnamed>"),
        binders=dict(raw["binders"]),
        connectives=dict(raw["connectives"]),
        relations=dict(raw["relations"]),
        operators=dict(raw["operators"]),
        types=dict(raw["types"]),
        structural=dict(raw["structural"]),
        slot_word=slot_word,
        slot_prefix=slot_prefix,
        refusals={k: dict(v) for k, v in refusals.items()},
        phrase_to_token=phrase_to_token,
        key_to_phrase=key_to_phrase,
        max_phrase_words=max(len(seq) for seq in phrase_to_token),
    )


def _check_emitted_token(key: str, token: str, section: str,
                         slot_prefix: str) -> None:
    """F7 for one row. Raises `ForeignLexiconError`; returns nothing on success.

    Applied to the slot marker's synthesized prefix as well as to every written
    key, because v0.18's one real table bug (commit 8910138) lived in a value,
    not in a key, and a key-only check is a check with a hole exactly where the
    bug was.
    """
    if not isinstance(token, str) or not token:
        raise ForeignLexiconError(f"F7: {key!r} emits {token!r}, which is not a token")
    if any(ch.isspace() for ch in token):
        raise ForeignLexiconError(
            f"F7: {key!r} emits {token!r}, which carries whitespace; the inverse "
            f"writes tokens space-separated and this one would arrive as two"
        )
    if re.fullmatch(rf"{re.escape(slot_prefix)}\d+", token):
        raise ForeignLexiconError(
            f"F7: {key!r} emits {token!r}, which is the spelling the slot marker "
            f"synthesizes for a variable index"
        )
    if re.fullmatch(r"-?\d+(?:\.\d+)?", token):
        raise ForeignLexiconError(
            f"F7: {key!r} emits {token!r}, which the inverse would re-read as a "
            f"numeral rather than as {key!r}"
        )
    if section == "types" and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_']*", token):
        raise ForeignLexiconError(
            f"F7: the type row {key!r} emits {token!r}, which is not an identifier; "
            f"a type ascription that is not a name is not a type ascription"
        )


def numeral_vocabulary() -> frozenset[str]:
    """The words the registered pair can emit — L2's other half, for callers."""
    return NUMERAL_VOCABULARY


__all__ = ["ForeignLexicon", "ForeignLexiconError", "DEFAULT_LEXICON_PATH",
           "build", "load", "numeral_vocabulary"]
