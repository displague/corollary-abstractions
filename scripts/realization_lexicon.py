#!/usr/bin/env python3
"""Load and gate `data/realization/lexicon.json` — the trusted, bijective table.

DESIGN-sans-template-rendering §3 splits the realization gate in two and is
explicit that only the second half is independent:

    Stage 1 — lexicon inversion (trusted, committed, reviewed).  The surface is
    de-lexicalized back to template tokens by the *same committed lexicon table
    used forward*, read in reverse.  This is not an independent check and is
    not claimed as one: it is a bijective table whose entries are reviewed in a
    diff with tests, exactly the rule `prose.py`'s banks live by.  Bijectivity
    is itself gated (**R2b**): forward and reverse readings of every row compose
    to the identity on both sides, and a table that is not injective in either
    direction refuses at load.

This module is the load and the refusal.  It holds no grammar: no precedence,
no bracketing, no arity — those live in `realize_term.py` (forward) and in the
byte-frozen `match_signatures.Parser` (the independent stage-2 reader).

## The longest-match rule, and why it is decidable here

The inverter reads a surface left to right.  At each position it takes the
**longest table phrase that matches the upcoming words**; if no phrase matches
it expects a numeral run (`scripts/numeral_words`).  Longest match is only a
rule, not a guarantee — "plus" and "plus or minus" would still leave a reader
guessing whether the writer meant the short phrase followed by content that
happens to start with "or".  So the load enforces the two properties that make
longest match *provably* the unique match:

  **L1 — prefix-free.**  No phrase is a proper word-prefix of another phrase.
  A phrase set that is prefix-free decodes uniquely under longest match, and
  the decode of any concatenation of phrases is the concatenation itself.

  **L2 — numeral disjointness.**  No word of any phrase is a word the
  registered numeral pair can emit (`numeral_words.NUMERAL_VOCABULARY`).  So
  one word decides "numeral run" versus "table phrase", and a numeral run may
  be scanned greedily without ever swallowing a phrase.

Together L1+L2 make stage 1 a table lookup with no lookahead policy of its
own, which is what §3 means by "table-driven, with no operator-precedence or
bracketing logic of its own".

## R2b, enforced here

  B1  no head/operator/relation/structural key appears twice (JSON duplicate
      keys are caught, not silently last-wins);
  B2  no two keys share a phrase (forward injective);
  B3  no two keys share a token (reverse injective);
  B4  forward(reverse(phrase)) == phrase and reverse(forward(key)) == key for
      every row — the identity composed on both sides, stated as §3 states it;
  B5  every phrase is lowercase ASCII words, and L2 holds;
  B6  L1 holds;
  B7  every emitted token is one the byte-frozen tokenizer accepts *as the
      thing the row means*.  This is `_check_emitted_token`, and it runs over
      EVERY token any row can emit — the structural, operator and relation
      keys, the VALUES of `operator_tokens`, the slot marker's token prefix
      and every call-head token — because the one bug this table has actually
      had (commit 8910138: `neg` emitted as the identifier `neg` and re-read
      as a call head) was in exactly the place a key-only check does not look.
      The rules:

        * the frozen tokenizer must read the token as exactly one token, and
          that token must be the token itself;
        * a structural / operator / relation row must NOT emit an identifier
          — `operator_tokens: {"neg": "negg"}` tokenizes fine and means a slot,
          which is 8910138's bug wearing a different spelling. The single
          exception is `approx`, the one relation the grammar spells as a word;
        * a call-head row MUST emit an identifier, must not be `approx`, and
          must not lower-case to a big-operator prefix (`sum_`, `prod_`,
          `lim_`, `max_`, `min_`) — `Parser.parse_atom` would read the emitted
          call as a big operator over the following product and stage 2 would
          recover a different head;
        * no row may emit `<slot_prefix><digits>` (`V0`), because the slot
          marker synthesizes exactly those tokens and a head spelled `V0`
          would be indistinguishable from the first variable.

A table that fails any of these raises `LexiconError` at load.  Nothing
downstream gets a chance to work around it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from match_signatures import TemplateParseError, tokenize
from numeral_words import is_numeral_word

DEFAULT_LEXICON_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "realization" / "lexicon.json"
)

#: Head spellings whose lower-casing would be read as a big operator by
#: `match_signatures.Parser.parse_atom`. Mirrored from `BIG_OP_PREFIXES` there;
#: the parser is byte-frozen, so this is a read of it, never a change to it.
BIG_OP_PREFIXES = ("sum_", "prod_", "lim_", "max_", "min_")

_IDENTIFIER_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_PHRASE_RE = re.compile(r"[a-z]+( [a-z]+)*")

_SECTIONS = ("structural", "operators", "relations", "call_heads")


class LexiconError(ValueError):
    """The table is not a bijection, or not readable by longest match."""


#: Sections whose rows spell a piece of GRAMMAR, not a name. Their tokens must
#: not be identifiers, because an identifier in operator position is a slot.
_GLYPH_SECTIONS = frozenset({"structural", "operators", "relations"})

#: The one relation the frozen grammar spells as a word
#: (`Parser.parse_relation` tests `tok == "approx"` explicitly).
_WORD_RELATION = "approx"


def _check_emitted_token(key: str, token: str, section: str,
                         slot_prefix: str) -> None:
    """B7 for one row. Raises `LexiconError`; returns nothing on success.

    Factored out and applied to every emitted token — keys, `operator_tokens`
    values, the slot prefix and head tokens alike — because the table's one
    real bug lived in a value, not a key.
    """
    if not isinstance(token, str) or not token:
        raise LexiconError(f"B7: {key!r} emits {token!r}, which is not a token")
    try:
        produced = tokenize(token)
    except TemplateParseError as exc:
        raise LexiconError(
            f"B7: {key!r} emits {token!r}, which the byte-frozen tokenizer "
            f"cannot read ({exc})"
        ) from None
    if produced != [token]:
        raise LexiconError(
            f"B7: {key!r} emits {token!r}, which the byte-frozen tokenizer "
            f"splits into {produced!r}"
        )

    if re.fullmatch(rf"{re.escape(slot_prefix)}\d+", token):
        raise LexiconError(
            f"B7: {key!r} emits {token!r}, which is the spelling the slot "
            f"marker synthesizes for a variable index"
        )

    identifier = bool(_IDENTIFIER_RE.fullmatch(token))
    if section in _GLYPH_SECTIONS:
        if identifier and token != _WORD_RELATION:
            raise LexiconError(
                f"B7: the {section} row {key!r} emits the identifier {token!r}; "
                f"the frozen parser would read it as a slot or a call head, not "
                f"as {key!r}"
            )
        return
    if not identifier:
        raise LexiconError(f"B7: call head {key!r} emits a non-identifier token")
    if token == _WORD_RELATION:
        raise LexiconError("B7: `approx` is a relation word, not a call head")
    if token.lower().startswith(BIG_OP_PREFIXES):
        raise LexiconError(
            f"B7: call head {key!r} lower-cases to a big-operator prefix; "
            f"stage 2 would read it as an operator over the following product"
        )


def head_token(head: str) -> str:
    """The tokenizer spelling of a call head.

    `Parser.parse_atom` builds the head `E[]` from the token `E` followed by
    `[`; the trailing marker is grammar, not name (`match_signatures.lint_stem`
    says the same thing for its own lint). Every other head is its own token.
    """
    return head[:-2] if head.endswith("[]") else head


@dataclass(frozen=True)
class Lexicon:
    """A loaded, gated table. Immutable; the file is the artifact."""

    path: Path
    lexicon_id: str
    structural: dict[str, str]
    operators: dict[str, str]
    relations: dict[str, str]
    call_heads: dict[str, str]
    slot_marker: str
    #: phrase words -> emitted token, the whole of stage 1's table
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


def _load_pairs(pairs: list[tuple[str, object]]) -> dict:
    seen: set[str] = set()
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise LexiconError(f"B1: duplicate key {key!r} in the lexicon file")
        seen.add(key)
        out[key] = value
    return out


def load(path: Path | str | None = None) -> Lexicon:
    """Read, gate and return the table. Raises `LexiconError` on any failure."""
    path = Path(path) if path is not None else DEFAULT_LEXICON_PATH
    raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_load_pairs)
    return build(raw, path)


def build(raw: dict, path: Path | str = "<memory>") -> Lexicon:
    """Gate an already-parsed table. Split from `load` so tests can inject."""
    path = Path(path) if not isinstance(path, str) else Path(path)

    for section in _SECTIONS:
        if section not in raw or not isinstance(raw[section], dict):
            raise LexiconError(f"missing or malformed section {section!r}")
    marker = raw.get("slot_marker")
    if not isinstance(marker, dict) or "word" not in marker:
        raise LexiconError("missing or malformed `slot_marker`")
    slot_word = marker["word"]

    # -- collect every row as (key, phrase, token) -------------------------
    # Most keys ARE their token. Two are not: the canonical tree spells unary
    # minus `neg` and reciprocal `inv` (`Parser.parse_sum` / `parse_product`
    # rewrite `-` and `/` into them), while the tokenizer only knows the
    # glyphs. `operator_tokens` states that mapping in the file rather than
    # letting the loader guess it, because a row whose emitted token is not
    # the token the frozen tokenizer expects produces a fluent sentence that
    # re-parses to a DIFFERENT tree — `neg` reads back as a call head.
    operator_tokens = raw.get("operator_tokens", {})
    unknown = set(operator_tokens) - set(raw["operators"])
    if unknown:
        raise LexiconError(
            f"`operator_tokens` names {sorted(unknown)}, which are not operator rows"
        )

    slot_prefix = marker.get("token_prefix", "V")

    # (key, phrase, emitted token, section) — the section decides which half
    # of B7 applies, and every row goes through it, values included.
    rows: list[tuple[str, str, str, str]] = []
    for key, phrase in raw["structural"].items():
        rows.append((key, phrase, key, "structural"))
    for key, phrase in raw["operators"].items():
        rows.append((key, phrase, operator_tokens.get(key, key), "operators"))
    for key, phrase in raw["relations"].items():
        rows.append((key, phrase, key, "relations"))
    for key, phrase in raw["call_heads"].items():
        rows.append((key, phrase, head_token(key), "call_heads"))
    rows.append((f"slot_marker:{slot_word}", slot_word, slot_prefix, "call_heads"))

    for key, phrase, _, _section in rows:
        if not isinstance(phrase, str) or not _PHRASE_RE.fullmatch(phrase):
            raise LexiconError(
                f"B5: phrase for {key!r} is not lowercase ASCII words: {phrase!r}"
            )
        for word in phrase.split():
            if is_numeral_word(word):
                raise LexiconError(
                    f"L2: phrase for {key!r} uses the numeral word {word!r}; "
                    f"the inverter could not tell it from a numeral run"
                )

    # -- B2 / B3: injective in both directions -----------------------------
    by_phrase: dict[str, str] = {}
    for key, phrase, _, _section in rows:
        if phrase in by_phrase:
            raise LexiconError(
                f"B2: phrase {phrase!r} maps to both {by_phrase[phrase]!r} "
                f"and {key!r}; the table is not injective forward"
            )
        by_phrase[phrase] = key
    by_token: dict[str, str] = {}
    for key, _phrase, token, _section in rows:
        if token in by_token:
            raise LexiconError(
                f"B3: token {token!r} is emitted by both {by_token[token]!r} "
                f"and {key!r}; the table is not injective in reverse"
            )
        by_token[token] = key

    # -- B4: both compositions are the identity ----------------------------
    key_to_phrase = {key: phrase for key, phrase, _t, _s in rows}
    phrase_to_key = {phrase: key for key, phrase, _t, _s in rows}
    for key, phrase, _token, _section in rows:
        if phrase_to_key[key_to_phrase[key]] != key:
            raise LexiconError(f"B4: reverse(forward({key!r})) is not {key!r}")
        if key_to_phrase[phrase_to_key[phrase]] != phrase:
            raise LexiconError(f"B4: forward(reverse({phrase!r})) is not {phrase!r}")

    # -- B6 / L1: prefix-free ----------------------------------------------
    word_seqs = {tuple(phrase.split()): key for key, phrase, _t, _s in rows}
    ordered = sorted(word_seqs)
    for i, seq in enumerate(ordered):
        for other in ordered[i + 1:]:
            if len(other) <= len(seq):
                continue
            if other[: len(seq)] != seq:
                break  # sorted: no later phrase can share this prefix either
            raise LexiconError(
                f"L1: phrase {' '.join(seq)!r} ({word_seqs[seq]!r}) is a proper "
                f"prefix of {' '.join(other)!r} ({word_seqs[other]!r}); longest "
                f"match cannot resolve them"
            )

    # -- B7: EVERY emitted token survives the byte-frozen tokenizer --------
    # Keys, `operator_tokens` values and the slot prefix alike: the table's
    # one real bug was in a value, so a key-only check is a check with a hole
    # exactly where the bug was.
    for key, _phrase, token, section in rows:
        _check_emitted_token(key, token, section, slot_prefix)

    phrase_to_token = {tuple(phrase.split()): token
                       for _k, phrase, token, _s in rows}
    return Lexicon(
        path=path,
        lexicon_id=raw.get("lexicon_id", "<unnamed>"),
        structural=dict(raw["structural"]),
        operators=dict(raw["operators"]),
        relations=dict(raw["relations"]),
        call_heads=dict(raw["call_heads"]),
        slot_marker=slot_word,
        phrase_to_token=phrase_to_token,
        key_to_phrase=key_to_phrase,
        max_phrase_words=max(len(seq) for seq in phrase_to_token),
    )


__all__ = ["Lexicon", "LexiconError", "DEFAULT_LEXICON_PATH", "build", "head_token",
           "load"]
