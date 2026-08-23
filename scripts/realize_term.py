#!/usr/bin/env python3
"""Say a canonical term in English, and gate the sentence by re-parsing it.

DESIGN-sans-template-rendering §3's first-class object.  `realize()` turns a
parseable `formal_statement.canonical_ascii` into an English sentence and a
**realization receipt**; `reparse()` reads a sentence back to a skeleton
through the two-stage gate; `round_trip` is EXACT only when the second stage's
skeleton equals the source's.

    realization {
      statement_id | session_ref,
      term_skeleton,            # canonical skeleton of the SOURCE term
      surface,                  # the emitted English sentence
      reparse_skeleton,         # what the reading path recovered from surface
      round_trip in { EXACT | FAILED },
      lexicon_entries[],        # every (operator|constant -> words) row used
      parameters { order, ... },
    }

## The two stages, and which one can fail

**Stage 1 — lexicon inversion (trusted).**  `delexicalize()` walks the surface
left to right taking the longest `data/realization/lexicon.json` phrase that
matches, or a numeral run when no phrase does, and emits the corresponding
token **in surface order**.  It has no precedence table, no bracket counter and
no arity knowledge: grouping words become `(` and `)` tokens exactly where the
writer put them, and every structural decision is deferred.  The load gate
(`realization_lexicon`) is what makes longest match the unique match, so this
walk needs no lookahead policy of its own.  It is not an independent check and
is not claimed as one.

**Stage 2 — structural re-parse (independent).**  The token string goes to
`match_signatures.tokenize` -> `Parser` -> `canonicalize` -> `skeleton`, all
byte-frozen before this file was written and digest-recorded in
`experiments/realization_prereg.json` (C-R3).  Stage 2 has never seen the
realizer.  It is the part that can fail, and when it does the sentence is
refused at the surface rather than served with a caveat (R3).

## Where the structure lives, stated so it is reviewable

All precedence lives HERE, in the forward direction, as a five-level ladder
read directly off the frozen grammar:

    0 relation   parse_relation      1 sum      parse_sum
    2 product    parse_product       3 power    parse_power
    4 atom       parse_atom

A subterm is wrapped in the grouping words ("the quantity" / "end quantity")
exactly when its own level is below the level its context accepts — minimal
parenthesization, decided by the writer, re-derived independently by stage 2.
Two consequences worth naming because they are easy to get wrong against this
particular parser:

- `parse_atom`'s unary `-` branch recurses into `parse_atom`, not
  `parse_power`, so `neg` binds TIGHTER than `^`: a `neg` node sits at level 4
  and its operand must be an atom.  `- a ^ 2` is `^(neg(a), 2)`, which is why
  `neg(^(a,2))` must group its operand.
- `parse_atom`'s big-operator branch swallows a whole following *product*, so
  the prefix form `sum_i EXPR` is never emitted; `sum(EXPR)` parses to the
  identical node and needs no special grammar.

## What refuses, and why refusing is the honest move

`REFUSAL_REASONS` is closed.  A term that does not parse has no source skeleton
to round-trip to; a head with no lexicon row would have to be improvised; a
numeral outside the registered pair would have to be rounded; a canonical `*`
whose every argument is an `inv` has no leading factor to divide.  Each of
those returns a `Refusal` with its class named, and the census counts them by
class rather than folding them into the round-trip rate.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numeral_words as nw
import realization_lexicon as rlex
from match_signatures import (
    Parser,
    TemplateParseError,
    canonicalize,
    skeleton,
    tokenize,
)

REALIZER_ID = "realization.grammar.v1"

# Precedence ladder, read off match_signatures' recursive descent.
LEVEL_RELATION = 0
LEVEL_SUM = 1
LEVEL_PRODUCT = 2
LEVEL_POWER = 3
LEVEL_ATOM = 4

REFUSAL_REASONS = (
    "unparseable_term",       # the frozen parser cannot read the source
    "uncovered_head",         # a call head with no lexicon row
    "uncovered_operator",     # an operator node with no lexicon row
    "uncovered_relation",     # a relation with no lexicon row
    "unsupported_numeral",    # outside the registered numeral pair
    "leading_divisor",        # a canonical `*` with no non-inv argument
    "leading_pm",             # a canonical `+` with no non-pm argument
    "bare_inverse",           # an `inv`/`pm` node with no operator parent
    "empty_term",             # nothing to say
)


class RefusalError(Exception):
    """Internal control flow: a linearization that must not be improvised."""

    def __init__(self, reason: str, detail: str) -> None:
        assert reason in REFUSAL_REASONS, reason
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class Refusal:
    """No sentence, and the class of the reason (R3)."""

    reason: str
    detail: str
    source: str
    statement_id: str | None = None

    round_trip: str = "REFUSED"
    served: bool = False

    def as_dict(self) -> dict:
        return {
            "statement_id": self.statement_id,
            "source": self.source,
            "round_trip": "REFUSED",
            "refusal": {"reason": self.reason, "detail": self.detail},
        }


@dataclass(frozen=True)
class Realization:
    """The receipt of design §3, with the surface it gates."""

    source: str
    term_skeleton: str
    surface: str
    reparse_skeleton: str | None
    round_trip: str                      # EXACT | FAILED
    lexicon_entries: tuple[tuple[str, str], ...]
    parameters: dict
    statement_id: str | None = None
    reparse_tokens: tuple[str, ...] = field(default_factory=tuple)

    @property
    def served(self) -> bool:
        """R3: only an EXACT round trip may reach a surface."""
        return self.round_trip == "EXACT"

    def as_dict(self) -> dict:
        return {
            "statement_id": self.statement_id,
            "source": self.source,
            "term_skeleton": self.term_skeleton,
            "surface": self.surface,
            "reparse_skeleton": self.reparse_skeleton,
            "round_trip": self.round_trip,
            "lexicon_entries": [
                {"key": key, "words": words} for key, words in self.lexicon_entries
            ],
            "parameters": self.parameters,
        }


# --------------------------------------------------------------------------
# Forward: the realization grammar
# --------------------------------------------------------------------------


class _Linearizer:
    """Walks a canonicalized tree and emits words. All precedence lives here."""

    def __init__(self, lexicon: rlex.Lexicon, slot_index: dict[str, int]) -> None:
        self.lex = lexicon
        self.slot_index = slot_index
        self.used: dict[str, str] = {}

    # -- lexicon access, recording every row consumed (R2's evidence) ------
    def _row(self, key: str, missing: str) -> list[str]:
        if not self.lex.covers(key):
            raise RefusalError(missing, f"no lexicon row for {key!r}")
        phrase = self.lex.words_for(key)
        self.used[key] = phrase
        return phrase.split()

    def _structural(self, key: str) -> list[str]:
        return self._row(key, "uncovered_operator")

    # -- the ladder --------------------------------------------------------
    def emit(self, node: tuple, min_level: int) -> list[str]:
        words, level = self._emit(node)
        if level < min_level:
            return self._structural("(") + words + self._structural(")")
        return words

    def _emit(self, node: tuple) -> tuple[list[str], int]:
        kind = node[0]
        if kind == "num":
            try:
                return nw.number_to_words(node[1]).split(), LEVEL_ATOM
            except nw.NumeralError as exc:
                raise RefusalError("unsupported_numeral", str(exc)) from None
        if kind == "slot":
            index = self.slot_index[node[1]]
            marker = self.lex.slot_marker
            self.used[f"slot_marker:{marker}"] = marker
            return [marker] + nw.int_to_words(index).split(), LEVEL_ATOM
        if kind == "rel":
            return self._emit_relation(node)
        if kind == "op":
            return self._emit_operator(node)
        if kind == "call":
            return self._emit_call(node)
        raise RefusalError("uncovered_operator", f"unknown node kind {kind!r}")

    def _emit_relation(self, node: tuple) -> tuple[list[str], int]:
        rel = node[1]
        if rel not in self.lex.relations:
            raise RefusalError("uncovered_relation", f"no lexicon row for {rel!r}")
        self.used[rel] = self.lex.words_for(rel)
        lhs, rhs = node[2]
        words = (self.emit(lhs, LEVEL_SUM)
                 + self.lex.words_for(rel).split()
                 + self.emit(rhs, LEVEL_SUM))
        return words, LEVEL_RELATION

    def _emit_operator(self, node: tuple) -> tuple[list[str], int]:
        name, args = node[1], node[2]
        if name == "+":
            return self._emit_sum(args)
        if name == "*":
            return self._emit_product(args)
        if name == "^":
            base = self.emit(args[0], LEVEL_ATOM)
            power = self._row("^", "uncovered_operator")
            exponent = self.emit(args[1], LEVEL_POWER)
            return base + power + exponent, LEVEL_POWER
        if name == "neg":
            # Level 4: `parse_atom`'s `-` branch recurses into `parse_atom`,
            # so the operand must itself be an atom and the node as a whole
            # sits where an atom sits (including as a `^` base).
            return self._row("neg", "uncovered_operator") + self.emit(
                args[0], LEVEL_ATOM), LEVEL_ATOM
        if name in {"inv", "pm"}:
            raise RefusalError(
                "bare_inverse",
                f"{name!r} with no operator parent has no template spelling",
            )
        raise RefusalError("uncovered_operator", f"no lexicon row for {name!r}")

    def _emit_sum(self, args: tuple) -> tuple[list[str], int]:
        if len(args) == 1:
            return self._emit(args[0])
        plain = [a for a in args if not (a[0] == "op" and a[1] == "pm")]
        spread = [a for a in args if a[0] == "op" and a[1] == "pm"]
        if not plain:
            # `± x` cannot open a sum: `parse_sum` reaches `±` only as an
            # infix continuation, never through `parse_atom`.
            raise RefusalError("leading_pm", "every summand is a `pm` node")
        words = self.emit(plain[0], LEVEL_PRODUCT)
        for arg in plain[1:]:
            words += self._row("+", "uncovered_operator")
            words += self.emit(arg, LEVEL_PRODUCT)
        for arg in spread:
            words += self._row("±", "uncovered_operator")
            words += self.emit(arg[2][0], LEVEL_PRODUCT)
        return words, LEVEL_SUM

    def _emit_product(self, args: tuple) -> tuple[list[str], int]:
        if len(args) == 1:
            return self._emit(args[0])
        divisors = [a for a in args if a[0] == "op" and a[1] == "inv"]
        factors = [a for a in args if not (a[0] == "op" and a[1] == "inv")]
        if not factors:
            # `/ x` cannot open a product either; `parse_product` reaches `/`
            # only as an infix continuation.
            raise RefusalError("leading_divisor", "every factor is an `inv` node")
        words = self.emit(factors[0], LEVEL_POWER)
        for arg in factors[1:]:
            words += self._row("*", "uncovered_operator")
            words += self.emit(arg, LEVEL_POWER)
        for arg in divisors:
            words += self._row("inv", "uncovered_operator")
            words += self.emit(arg[2][0], LEVEL_POWER)
        return words, LEVEL_PRODUCT

    def _emit_call(self, node: tuple) -> tuple[list[str], int]:
        head, args = node[1], node[2]
        if head not in self.lex.call_heads:
            raise RefusalError("uncovered_head", f"no lexicon row for {head!r}")
        self.used[head] = self.lex.words_for(head)
        opener, closer = ("[", "]") if head.endswith("[]") else ("(", ")")
        words = self.lex.words_for(head).split() + self._structural(opener)
        for i, arg in enumerate(args):
            if i:
                words += self._structural(",")
            words += self.emit(arg, LEVEL_RELATION)
        words += self._structural(closer)
        return words, LEVEL_ATOM


def _slot_order(node: tuple, out: list[str]) -> None:
    """First occurrence in a fixed pre-order walk — deterministic (R5)."""
    if node[0] == "slot":
        if node[1] not in out:
            out.append(node[1])
        return
    if node[0] == "num":
        return
    for arg in node[2]:
        _slot_order(arg, out)


# --------------------------------------------------------------------------
# Stage 1: lexicon inversion (trusted, table-driven, no structural logic)
# --------------------------------------------------------------------------


def delexicalize(surface: str, lexicon: rlex.Lexicon | None = None) -> list[str] | None:
    """Surface -> template tokens, in surface order. `None` if unreadable.

    The whole of stage 1.  It knows three things and no more: the longest
    matching phrase, that a run of numeral words is a numeral, and that a
    numeral run right after the slot marker is a slot index.  It never counts
    a bracket, never consults an arity and never compares precedences —
    `(` and `)` come out where the grouping words were and stage 2 decides
    what they mean.
    """
    lex = lexicon or rlex.load()
    words = surface.split()
    tokens: list[str] = []
    i = 0
    while i < len(words):
        phrase = None
        for width in range(min(lex.max_phrase_words, len(words) - i), 0, -1):
            candidate = tuple(words[i:i + width])
            if candidate in lex.phrase_to_token:
                phrase = candidate
                break
        if phrase is not None:
            token = lex.phrase_to_token[phrase]
            i += len(phrase)
            if phrase == (lex.slot_marker,):
                run, i = _numeral_run(words, i)
                if not run:
                    return None
                try:
                    tokens.append(f"{token}{nw.words_to_int(run)}")
                except nw.NumeralError:
                    return None
            else:
                tokens.append(token)
            continue
        run, i = _numeral_run(words, i)
        if not run:
            return None
        try:
            tokens.append(nw.words_to_numeral_token(run))
        except nw.NumeralError:
            return None
    return tokens


def _numeral_run(words: list[str], i: int) -> tuple[str, int]:
    """Greedy scan of numeral words. Safe because of the loader's L2 rule."""
    start = i
    while i < len(words) and nw.is_numeral_word(words[i]):
        i += 1
    return " ".join(words[start:i]), i


# --------------------------------------------------------------------------
# Stage 2: the byte-frozen structural re-parse (independent)
# --------------------------------------------------------------------------


def reparse(surface: str, lexicon: rlex.Lexicon | None = None
            ) -> tuple[str | None, tuple[str, ...]]:
    """The two-stage gate. Returns (skeleton or None, the stage-1 tokens)."""
    tokens = delexicalize(surface, lexicon)
    if tokens is None:
        return None, ()
    try:
        tree = canonicalize(Parser(tokenize(" ".join(tokens))).parse())
    except (TemplateParseError, RecursionError):
        return None, tuple(tokens)
    return skeleton(tree), tuple(tokens)


# --------------------------------------------------------------------------
# The realization
# --------------------------------------------------------------------------


def realize(canonical_ascii: str, lexicon: rlex.Lexicon | None = None,
            statement_id: str | None = None) -> Realization | Refusal:
    """Realize one term, gated. Never raises on corpus input."""
    lex = lexicon or rlex.load()
    source = canonical_ascii
    if not source or not source.strip():
        return Refusal("empty_term", "no canonical_ascii", source, statement_id)
    try:
        tree = canonicalize(Parser(tokenize(source)).parse())
    except (TemplateParseError, RecursionError) as exc:
        return Refusal("unparseable_term", str(exc), source, statement_id)

    names: list[str] = []
    _slot_order(tree, names)
    slot_index = {name: i for i, name in enumerate(names)}

    linearizer = _Linearizer(lex, slot_index)
    try:
        words = linearizer.emit(tree, LEVEL_RELATION)
    except RefusalError as exc:
        return Refusal(exc.reason, exc.detail, source, statement_id)
    except RecursionError:
        return Refusal("unparseable_term", "term too deep to linearize",
                       source, statement_id)

    surface = " ".join(words)
    term_skeleton = skeleton(tree)
    reparse_skeleton, tokens = reparse(surface, lex)
    round_trip = "EXACT" if reparse_skeleton == term_skeleton else "FAILED"

    return Realization(
        source=source,
        term_skeleton=term_skeleton,
        surface=surface,
        reparse_skeleton=reparse_skeleton,
        round_trip=round_trip,
        lexicon_entries=tuple(sorted(linearizer.used.items())),
        parameters={
            "realizer_id": REALIZER_ID,
            "lexicon_id": lex.lexicon_id,
            "order": "canonical",
            "grouping": "minimal",
            "slot_names": {name: i for name, i in slot_index.items()},
        },
        statement_id=statement_id,
        reparse_tokens=tokens,
    )


def surface_words_are_covered(surface: str,
                              lexicon: rlex.Lexicon | None = None) -> bool:
    """R2: every word traces to a lexicon row or the registered numeral pair."""
    lex = lexicon or rlex.load()
    vocabulary = {word for phrase in lex.phrase_to_token for word in phrase}
    return all(word in vocabulary or nw.is_numeral_word(word)
               for word in surface.split())


# --------------------------------------------------------------------------
# R0's prerequisite table: the census
# --------------------------------------------------------------------------


def census(data_dir: Path, lexicon: rlex.Lexicon | None = None,
           examples_per_class: int = 3) -> dict:
    """Parse rate per corpus, and round-trip rate over parseable terms.

    This is the R0 PREREQUISITE table, not the registered run: it exists so
    R1's floor is read against a denominator that was published first.
    """
    lex = lexicon or rlex.load()
    corpora: list[dict] = []
    totals = Counter()
    refusal_classes: Counter = Counter()
    parse_failures: Counter = Counter()
    examples: dict[str, list[dict]] = {}

    for path in sorted(data_dir.glob("*/nodes.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        name = doc.get("discipline", path.parent.name)
        row = Counter()
        for node in doc.get("statement_nodes", []):
            sid = node.get("statement_id", "<missing-id>")
            source = ((node.get("formal_statement") or {})
                      .get("canonical_ascii") or "")
            row["nodes"] += 1
            result = realize(source, lex, statement_id=sid)
            if isinstance(result, Refusal):
                refusal_classes[result.reason] += 1
                if result.reason in {"unparseable_term", "empty_term"}:
                    parse_failures[_parse_failure_class(result.detail)] += 1
                else:
                    row["parseable"] += 1
                    row["refused_after_parse"] += 1
                bucket = examples.setdefault(result.reason, [])
                if len(bucket) < examples_per_class:
                    bucket.append({"statement_id": sid, "source": source[:120],
                                   "detail": result.detail[:120]})
                continue
            row["parseable"] += 1
            if result.round_trip == "EXACT":
                row["round_trip_exact"] += 1
            else:
                row["round_trip_failed"] += 1
                bucket = examples.setdefault("round_trip_failed", [])
                if len(bucket) < examples_per_class:
                    bucket.append({
                        "statement_id": sid,
                        "source": source[:120],
                        "term_skeleton": result.term_skeleton[:160],
                        "reparse_skeleton": (result.reparse_skeleton or "<none>")[:160],
                        "surface": result.surface[:200],
                    })
        totals.update(row)
        corpora.append({
            "corpus": name,
            "nodes": row["nodes"],
            "parseable": row["parseable"],
            "parse_rate": _rate(row["parseable"], row["nodes"]),
            "round_trip_exact": row["round_trip_exact"],
            "round_trip_failed": row["round_trip_failed"],
            "refused_after_parse": row["refused_after_parse"],
            "round_trip_rate_over_parseable": _rate(row["round_trip_exact"],
                                                    row["parseable"]),
            "thin_denominator": row["parseable"] < 50,
        })

    corpora.sort(key=lambda r: (-r["parseable"], r["corpus"]))
    return {
        "census_id": "realization.census.v1",
        "realizer_id": REALIZER_ID,
        "lexicon_id": lex.lexicon_id,
        "source_field": "formal_statement.canonical_ascii",
        "data_dir": str(data_dir).replace("\\", "/"),
        "note": [
            "R0's construction prerequisite (design §6): the parse rate of the "
            "source field under the byte-frozen parser, per corpus, with "
            "failure classes named — published before R1's floor is read.",
            "R1's floor is a fraction of the PARSEABLE denominator, which is "
            "reported beside every rate here.",
            "This is not the registered full-corpus run "
            "(experiments/realization_rate.json); it is the table that run's "
            "denominator comes from.",
        ],
        "totals": {
            "nodes": totals["nodes"],
            "parseable": totals["parseable"],
            "parse_rate": _rate(totals["parseable"], totals["nodes"]),
            "round_trip_exact": totals["round_trip_exact"],
            "round_trip_failed": totals["round_trip_failed"],
            "refused_after_parse": totals["refused_after_parse"],
            "round_trip_rate_over_parseable": _rate(totals["round_trip_exact"],
                                                    totals["parseable"]),
            "r1_floor": 0.90,
            "r1_verdict": ("FIRES" if _rate(totals["round_trip_exact"],
                                            totals["parseable"]) >= 0.90
                           else "MISSES"),
        },
        "corpora": corpora,
        "refusal_classes": dict(sorted(refusal_classes.items())),
        "parse_failure_classes": dict(sorted(parse_failures.items(),
                                             key=lambda kv: (-kv[1], kv[0]))),
        "examples": {k: examples[k] for k in sorted(examples)},
    }


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def _parse_failure_class(detail: str) -> str:
    """Name the tokenizer/parser failure, not the offending text."""
    if not detail:
        return "empty"
    return detail.split(" at ")[0].split(" `")[0][:48]


def _print_census(report: dict) -> None:
    totals = report["totals"]
    print(f"R0 census over {report['data_dir']}/*/nodes.json "
          f"({report['source_field']})")
    print(f"realizer {report['realizer_id']}  lexicon {report['lexicon_id']}")
    print()
    head = (f"{'corpus':32s} {'nodes':>7s} {'parse':>7s} {'parse%':>8s} "
            f"{'exact':>7s} {'failed':>7s} {'refused':>8s} {'rt%':>8s}")
    print(head)
    print("-" * len(head))
    for row in report["corpora"]:
        mark = " *" if row["thin_denominator"] else "  "
        print(f"{row['corpus'][:32]:32s} {row['nodes']:7d} {row['parseable']:7d} "
              f"{row['parse_rate']:8.4f} {row['round_trip_exact']:7d} "
              f"{row['round_trip_failed']:7d} {row['refused_after_parse']:8d} "
              f"{row['round_trip_rate_over_parseable']:8.4f}{mark}")
    print("-" * len(head))
    print(f"{'TOTAL':32s} {totals['nodes']:7d} {totals['parseable']:7d} "
          f"{totals['parse_rate']:8.4f} {totals['round_trip_exact']:7d} "
          f"{totals['round_trip_failed']:7d} {totals['refused_after_parse']:8d} "
          f"{totals['round_trip_rate_over_parseable']:8.4f}")
    print("  * fewer than 50 parseable terms: reported individually per R1, "
          "never averaged into a per-corpus floor")
    print()
    print(f"R1 floor 0.90 over the parseable denominator "
          f"({totals['parseable']}): {totals['r1_verdict']} at "
          f"{totals['round_trip_rate_over_parseable']:.4f}")
    if report["refusal_classes"]:
        print("\nrefusal classes:")
        for name, count in report["refusal_classes"].items():
            print(f"  {count:7d}  {name}")
    if report["parse_failure_classes"]:
        print("\nparse failure classes (R0's named classes):")
        for name, count in report["parse_failure_classes"].items():
            print(f"  {count:7d}  {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--census", action="store_true",
                        help="run R0 over every data/*/nodes.json term")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path, default=None,
                        help="write the census table here as JSON")
    parser.add_argument("--term", default=None,
                        help="realize one canonical_ascii term and show its receipt")
    parser.add_argument("--lexicon", type=Path, default=None)
    args = parser.parse_args(argv)

    lex = rlex.load(args.lexicon)

    if args.term is not None:
        result = realize(args.term, lex)
        print(json.dumps(result.as_dict(), indent=2, ensure_ascii=False))
        return 0 if getattr(result, "served", False) else 1

    if not args.census:
        parser.error("nothing to do: pass --census or --term")

    report = census(args.data_dir, lex)
    _print_census(report)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(
            (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )
        print(f"\ncensus written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
