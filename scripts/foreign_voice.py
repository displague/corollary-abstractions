#!/usr/bin/env python3
"""The foreign voice: render R(s), invert it literally, and let the oracle judge.

DESIGN-foreign-voice §3.1.  Two directions and one gate:

* **forward** — `render` walks `R(s)` left to right and emits one English
  phrase per dialect token.  All precedence lives here, as v0.18's realizer
  already does it (`scripts/realize_term.py:41`).
* **inverse** — `delexicalize` is **literal table substitution only**.  It
  *"never counts a bracket, never consults an arity and never compares
  precedences"* (`scripts/realize_term.py:387–396`).  L1 and L2, enforced at
  load by `foreign_voice_lexicon`, are what make its longest-match reading the
  **unique** reading rather than merely a rule.
* **gate** — the pinned external Lean checker, through
  `foreign_voice_oracle`.  Identity holds iff
  `sha256(serialize(elaborate(R(s))))` equals
  `sha256(serialize(elaborate(R(literal_inverse(render(R(s)))))))`, both
  recomputed in the same run and never carried from ingest.

## The grammar, and the one place it is narrower than v0.18's

The rendering is **token-faithful**: every token of `R(s)` emits its phrase,
identifiers emit `variable <index>`, literals emit the registered numeral
pair's words, and the joins are single spaces.  **Precedence is carried, not
rebuilt** — `R(s)`'s own parentheses become `the quantity` / `end quantity` and
none is added — because the inverse feeds the result back to the *same*
grammar it came from, so the source's bracketing is already the bracketing the
reader needs.  v0.18's realizer had to re-bracket for a different grammar; this
one must not, and adding a bracket here would be adding surface outside the
table.

**Identifiers are erased to slot indices on purpose.**  `Serialize.lean` drops
the `Name` field of every binder, so a rendered name would be information the
identity witness cannot see — a rendering error B1 could never catch.  Indices
are assigned by first occurrence in `R(s)`, left to right, from zero.

**Numerals are unsigned**: `-` is always the operator row, so the pair is only
ever asked for non-negative values and its word `negative` never appears.
That is what removes v0.18's `neg`/`-` token collision at the root instead of
legislating around it.

## What this module refuses, and why refusing is the product

A construct with no row **refuses at the surface** rather than improvising, in
the closed vocabulary `data/foreign_voice/lexicon.json` declares.  The
refusals are not the residue of an unfinished renderer; they are rows in the
frozen register, which §8 calls the headline artifact.  Three of them —
`no_lexicon_row`, `unsupported_numeral`, `noncanonical_numeral` — are decided
here.  The other two are decided before this module is reached.

The numeral canonicality gate is the subtle one.  `23.50` and `23.5` are
different `OfScientific` terms to the elaborator, and the registered pair is
exact rather than approximately exact, so it renders the canonical spelling
and cannot get back to the other.  Rendering it anyway would produce a
sentence that is right about the number and wrong about the term, and B1 would
score the renderer for it.  So it refuses.

## What a passing identity certifies

`scripts/external_verifier.py:6–7`, unweakened: *"a passing check certifies
what it checks, not correctness in general."*  Here that is: **the English
determines the term** under the declared interpretation, **up to what
elaboration erases and what rule R's preamble regenerates**.  C-V4 is the only
instrument that bounds the second half, and no sentence quoting B1 may omit
it.  Nothing here mints a `verified_by` link and nothing here claims a
statement is true.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice_lexicon as fvl  # noqa: E402
import foreign_voice_oracle as fvo  # noqa: E402
import foreign_voice_rule_r as fvr  # noqa: E402
import grouping_canonical_probe as gp  # noqa: E402
import numeral_words as nw  # noqa: E402

RENDERER_ID = "foreign_voice.renderer.v2-canonical"

#: The canonical grouping rule, loaded once. A TRUSTED, reviewed artifact with
#: its own digest, exactly as rule R and the lexicon are — see
#: `data/foreign_voice/grouping.json`.
GROUPING_RULE = gp.Rule.load()

#: Rule R's identifier grammar, mirrored. A name is read here exactly as the
#: interpretation reads it, so the two cannot disagree about what a token is.
_IDENT_START = r"A-Za-z_α-ωΑ-Ω"
_IDENT_CONT = _IDENT_START + r"0-9'₀-₉ₐ-ₜ"
_IDENT_RE = re.compile(rf"[{_IDENT_START}][{_IDENT_CONT}]*")

#: A numeral literal. The identifier rule is tried FIRST, so a digit run inside
#: `x_2` is never seen here.
_NUMERAL_RE = re.compile(r"\d+(?:\.\d+)?")


class ForeignVoiceError(ValueError):
    """The renderer was asked for something it must not improvise."""


@dataclass(frozen=True)
class Refusal:
    """A statement this cycle does not say out loud, and the reason it does not."""

    statement_id: str | None
    source: str
    interpreted: str
    reason: str
    detail: str

    served: bool = False

    @property
    def rendered(self) -> bool:
        return False


@dataclass(frozen=True)
class Rendering:
    """One rendered statement and everything a receipt needs."""

    statement_id: str | None
    source: str
    interpreted: str
    interpretation_shift: tuple[str, ...]
    surface: str
    #: `R(s)` re-emitted under the canonical grouping rule — what the sentence
    #: is actually a rendering OF.
    canonical: str
    slot_names: dict[str, int]
    numerals_used: tuple[str, ...]
    lexicon_entries: tuple[tuple[str, str], ...]
    preamble_binders: tuple[str, ...]

    served: bool = True

    @property
    def rendered(self) -> bool:
        return True

    def receipt(self) -> dict:
        """§3.3's per-statement receipt. `interpretation_shift` is mandatory.

        *"A rate quoted without that field beside it is a number pretending to
        be a fact."*
        """
        return {
            "renderer_id": RENDERER_ID,
            "statement_id": self.statement_id,
            "source": self.source,
            "interpreted": self.interpreted,
            "canonical": self.canonical,
            "interpretation_shift": list(self.interpretation_shift),
            "surface": self.surface,
            "parameters": {
                "order": "canonical",
                "grouping": "canonical — emitted only where precedence demands",
                "grouping_rule": GROUPING_RULE.rule_id,
                "surface_slot_names": dict(self.slot_names),
                "slot_index_basis": (
                    "first occurrence in R(s), left to right, from zero. There "
                    "is only ONE numbering here, unlike v0.18's two, because "
                    "nothing in this path re-orders arguments before numbering "
                    "them: the dialect's own token order is the order."
                ),
                "preamble_binders": list(self.preamble_binders),
                "numerals_used": list(self.numerals_used),
            },
            "lexicon_entries": [list(pair) for pair in self.lexicon_entries],
        }


@dataclass
class Receipt:
    """A rendering with the oracle's two digests beside it."""

    rendering: Rendering
    roundtrip_text: str
    orig_elab_digest: str
    rt_elab_digest: str
    orig_error: str = ""
    rt_error: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def identity(self) -> bool:
        return bool(self.orig_elab_digest) and (
            self.orig_elab_digest == self.rt_elab_digest)

    @property
    def outcome(self) -> str:
        """B2's three outcomes, and there is no fourth."""
        if not self.orig_elab_digest:
            return "orig_failed"
        if not self.rt_elab_digest:
            return "roundtrip_failed"
        return "identity" if self.identity else "digest_differed"

    def as_dict(self) -> dict:
        out = self.rendering.receipt()
        out.update({
            "roundtrip_text": self.roundtrip_text,
            "orig_elab_digest": self.orig_elab_digest,
            "rt_elab_digest": self.rt_elab_digest,
            "orig_error": self.orig_error,
            "rt_error": self.rt_error,
            "identity": self.identity,
            "outcome": self.outcome,
            "identity_is_bounded": (
                "up to what elaboration erases and what rule R's preamble "
                "regenerates; C-V4 bounds how often that is the case"
            ),
        })
        return out


# --------------------------------------------------------------------------
# Forward: R(s) -> English
# --------------------------------------------------------------------------


def _numeral_words(literal: str) -> str:
    """The registered pair's words, or raise with the refusal reason.

    Canonicality is checked by round-tripping the pair against the literal's
    own spelling. `23.50` renders as "twenty-three point five", which reads
    back as `23.5` — a different `OfScientific` term — so it refuses instead of
    producing a sentence that is right about the number and wrong about the
    term.
    """
    value: float | int = float(literal) if "." in literal else int(literal)
    try:
        words = nw.number_to_words(value)
    except nw.NumeralError as exc:
        raise ForeignVoiceError(f"unsupported_numeral: {literal!r} ({exc})") from None
    try:
        back = nw.words_to_numeral_token(words)
    except nw.NumeralError as exc:  # pragma: no cover - the pair is a bijection
        raise ForeignVoiceError(
            f"unsupported_numeral: {literal!r} does not read back ({exc})") from None
    if back != literal:
        raise ForeignVoiceError(
            f"noncanonical_numeral: {literal!r} renders as {words!r}, which "
            f"reads back as {back!r} — a different term, not a different spelling")
    return words


def tokenize(text: str, lexicon: fvl.ForeignLexicon) -> list[tuple[str, str]]:
    """`R(s)` as `(kind, text)` pairs: `row`, `ident`, `numeral`.

    Longest-first over the table's tokens, and identifiers before tokens so a
    type name is read as one name rather than as a prefix of one. This is the
    munch order that the `>=` correction exists to make correct: `>=` is tried
    before `>`, because `lexicon.tokens` is sorted longest first.
    """
    tokens = lexicon.tokens
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        match = _IDENT_RE.match(text, i)
        if match:
            name = match.group(0)
            out.append(("row" if name in lexicon.types else "ident", name))
            i = match.end()
            continue
        match = _NUMERAL_RE.match(text, i)
        if match:
            out.append(("numeral", match.group(0)))
            i = match.end()
            continue
        for token in tokens:
            if text.startswith(token, i):
                out.append(("row", token))
                i += len(token)
                break
        else:
            refusal = lexicon.refusal_for(text[i])
            reason = refusal["reason"] if refusal else "no_lexicon_row"
            raise ForeignVoiceError(
                f"{reason}: {text[i]!r} has no row in {lexicon.lexicon_id}")
    return out


def render_interpreted(interpreted: str, lexicon: fvl.ForeignLexicon,
                       source: str = "", statement_id: str | None = None,
                       interpretation_shift: tuple[str, ...] = (),
                       preamble_binders: tuple[str, ...] = ()
                       ) -> Rendering | Refusal:
    """Render an already-interpreted `R(s)`. Never raises on corpus input.

    **The one change v0.20 makes to the forward path.** `R(s)` is re-emitted
    under `grouping.json` before it is tokenized, so a grouping word appears
    only where precedence demands one. Everything downstream — the slot
    marker, the numeral pair, the phrase lookup, the literal inverse and the
    oracle — is byte-for-byte the v0.19 path.

    v0.19 rendered the source's own brackets verbatim, which is why a served
    sentence could have a redundant-bracket variant that read differently and
    certified identically. That variant is now not rare but *ungrammatical*,
    and G1b establishes it over all 5,228 surviving pairs rather than a sample.
    """
    try:
        canonical = gp.canon(interpreted, GROUPING_RULE)
    except gp.GroupingError as exc:
        # Unreachable over the covered set — G-P parses all 2,313 — so this is
        # a guard, not a class. It is mapped onto the CLOSED refusal vocabulary
        # rather than widening it: a construct the grouping rule has no clause
        # for is a construct with no row, and widening the vocabulary would
        # move the lexicon digest that the B0d seed derivation now depends on.
        return Refusal(statement_id, source or interpreted, interpreted,
                       "no_lexicon_row",
                       f"the grouping rule cannot read this statement: {exc}")
    try:
        tokens = tokenize(canonical, lexicon)
    except ForeignVoiceError as exc:
        reason, _, detail = str(exc).partition(": ")
        return Refusal(statement_id, source or interpreted, interpreted,
                       reason, detail)

    words: list[str] = []
    slots: dict[str, int] = {}
    numerals: list[str] = []
    used: dict[str, str] = {}
    for kind, text in tokens:
        if kind == "row":
            phrase = lexicon.words_for(text)
            used[text] = phrase
            words.append(phrase)
        elif kind == "ident":
            index = slots.setdefault(text, len(slots))
            words.append(lexicon.slot_word)
            words.append(nw.int_to_words(index))
            used[f"slot_marker:{lexicon.slot_word}"] = lexicon.slot_word
        else:
            try:
                spelling = _numeral_words(text)
            except ForeignVoiceError as exc:
                reason, _, detail = str(exc).partition(": ")
                return Refusal(statement_id, source or interpreted, interpreted,
                               reason, detail)
            numerals.append(text)
            words.append(spelling)

    return Rendering(
        statement_id=statement_id,
        source=source or interpreted,
        interpreted=interpreted,
        interpretation_shift=interpretation_shift,
        surface=" ".join(words),
        canonical=canonical,
        slot_names=slots,
        numerals_used=tuple(numerals),
        lexicon_entries=tuple(sorted(used.items())),
        preamble_binders=preamble_binders,
    )


def render(source: str, lexicon: fvl.ForeignLexicon | None = None,
           rule: fvr.RuleR | None = None,
           statement_id: str | None = None) -> Rendering | Refusal:
    """Apply rule R, then render. The renderer never sees the raw corpus text.

    Correction 3 is why: with `autoImplicit` off the surface must carry an
    explicit binder preamble, so the sentence a reader sees is the sentence for
    the statement UNDER the declared interpretation.
    """
    lexicon = lexicon or fvl.load()
    rule = rule or fvr.load()
    if not source or not source.strip():
        return Refusal(statement_id, source, "", "no_lexicon_row",
                       "empty statement")
    interpretation = rule.apply(source)
    return render_interpreted(
        interpretation.text, lexicon, source=source, statement_id=statement_id,
        interpretation_shift=interpretation.interpretation_shift,
        preamble_binders=interpretation.preamble_binders)


# --------------------------------------------------------------------------
# Inverse: English -> Lean text, by table lookup and nothing else
# --------------------------------------------------------------------------


def delexicalize(surface: str, lexicon: fvl.ForeignLexicon | None = None) -> str:
    """The literal inverse. No brackets counted, no arities, no precedence.

    Longest match is the UNIQUE match here, and that is a property the loader
    enforces rather than a hope: L1 (no phrase is a proper word-prefix of
    another) and L2 (no phrase word is a word the numeral pair can emit)
    together mean one word decides "numeral run or table phrase", and a numeral
    run can be scanned greedily without ever swallowing a phrase.

    Tokens come out **space-separated**, so the pinned binary's lexer never has
    to make a maximal-munch decision this table could have got wrong.
    """
    lexicon = lexicon or fvl.load()
    words = surface.split()
    out: list[str] = []
    i = 0
    longest = lexicon.max_phrase_words
    while i < len(words):
        phrase = None
        for size in range(min(longest, len(words) - i), 0, -1):
            candidate = tuple(words[i:i + size])
            if candidate in lexicon.phrase_to_token:
                phrase = candidate
                break
        if phrase is not None:
            token = lexicon.phrase_to_token[phrase]
            i += len(phrase)
            if phrase == (lexicon.slot_word,):
                run, i = _numeral_run(words, i)
                if not run:
                    raise ForeignVoiceError(
                        f"the slot word at {i} is not followed by a numeral run")
                out.append(f"{token}{nw.words_to_int(' '.join(run))}")
            else:
                out.append(token)
            continue
        run, i = _numeral_run(words, i)
        if not run:
            raise ForeignVoiceError(
                f"{words[i]!r} is neither a table phrase nor a numeral word")
        out.append(nw.words_to_numeral_token(" ".join(run)))
    return " ".join(out)


def _numeral_run(words: list[str], i: int) -> tuple[list[str], int]:
    """The maximal run of numeral words at `i`. L2 is what makes this safe."""
    run: list[str] = []
    while i < len(words) and nw.is_numeral_word(words[i]):
        run.append(words[i])
        i += 1
    return run, i


def surface_words_are_covered(surface: str,
                              lexicon: fvl.ForeignLexicon | None = None) -> bool:
    """R2's sweep: every word traces to a row or to the registered pair."""
    lexicon = lexicon or fvl.load()
    vocabulary = {word for phrase in lexicon.phrase_to_token for word in phrase}
    return all(word in vocabulary or nw.is_numeral_word(word)
               for word in surface.split())


# --------------------------------------------------------------------------
# The gate: both digests, recomputed in the same run
# --------------------------------------------------------------------------


def gate(renderings: list[Rendering], oracle: fvo.Oracle,
         rule: fvr.RuleR | None = None,
         lexicon: fvl.ForeignLexicon | None = None,
         batch_size: int = 300) -> list[Receipt]:
    """Adjudicate a batch. Rule R is applied INDEPENDENTLY on each side.

    There is deliberately no argument by which the round-trip side could learn
    anything about the original side. A preamble mismatch is a B1 failure,
    never a repair (§3.2).
    """
    rule = rule or fvr.load()
    lexicon = lexicon or fvl.load()

    terms: list[tuple[str, str]] = []
    roundtrips: list[str] = []
    for index, rendering in enumerate(renderings):
        roundtrip = delexicalize(rendering.surface, lexicon)
        # R applied to the inverse output, independently. It normally adds
        # nothing, because the inverse hands back a fully-bound term — but it
        # is applied rather than assumed, because "normally" is not a rule.
        roundtrips.append(rule.apply(roundtrip).text)
        terms.append((f"o{index}", rendering.interpreted))
        terms.append((f"r{index}", roundtrips[-1]))

    answers = oracle.serialize(terms, batch_size=batch_size)
    receipts: list[Receipt] = []
    for index, rendering in enumerate(renderings):
        orig = answers[f"o{index}"]
        rt = answers[f"r{index}"]
        receipts.append(Receipt(
            rendering=rendering,
            roundtrip_text=roundtrips[index],
            orig_elab_digest=orig.digest,
            rt_elab_digest=rt.digest,
            orig_error=orig.error,
            rt_error=rt.error,
        ))
    return receipts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--statement", action="append", default=[],
                        help="a corpus statement to render; repeatable")
    parser.add_argument("--gate", action="store_true",
                        help="also submit to the pinned oracle and report identity")
    args = parser.parse_args(argv)
    if not args.statement:
        parser.error("nothing to do: pass at least one --statement")

    lexicon = fvl.load()
    rule = fvr.load()
    results = [render(text, lexicon, rule) for text in args.statement]
    rendered = [row for row in results if isinstance(row, Rendering)]

    receipts: dict[int, Receipt] = {}
    if args.gate and rendered:
        try:
            oracle = fvo.load()
        except fvo.OracleRefusal as exc:
            print(f"oracle refused: {exc}", file=sys.stderr)
            return 2
        for rendering, receipt in zip(rendered, gate(rendered, oracle, rule, lexicon)):
            receipts[id(rendering)] = receipt

    for row in results:
        if isinstance(row, Refusal):
            print(json.dumps({"refused": row.reason, "detail": row.detail,
                              "source": row.source}, ensure_ascii=False))
            continue
        receipt = receipts.get(id(row))
        payload = receipt.as_dict() if receipt else row.receipt()
        print(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
