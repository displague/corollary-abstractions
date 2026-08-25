#!/usr/bin/env python3
"""G-P: a precedence-aware parser and canonical re-emitter for the dialect.

DESIGN-voice-completion §3.1 and Correction 1.  The v0.19 renderer has **no
parse tree**: `scripts/foreign_voice.py` tokenizes `R(s)` into a flat list and
emits one phrase per token, so `(` and `)` are ordinary lexicon rows and
*"precedence is carried, not rebuilt"*.  Canonical grouping therefore needs a
**new object** — this one — and it is a construction prerequisite with its own
discharge, not a diff.

## The three kinds of parenthesis, and why a regex could not do this

Correction 2: a parenthesis in this dialect has three kinds and only one is a
grouping bracket.

* **grouping** — `(a + b) * c`.  Removable exactly when precedence already
  says what the bracket says.  This is the only kind any mutation pool or
  canonicalization may touch.
* **ascription** — `(36 : Rat)`.  **Syntax.**  Never a grouping pair, never
  removed: the brackets *are* the ascription.
* **binder_group** — `∃ (x y z : Rat),`.  Optional syntax, and the rule
  **strips** it (Correction 3): the two forms elaborate identically and the
  unbracketed one is canonical.

All three render through the same two lexicon rows, so the distinction lives
in the tree and nowhere else.  That is why the rule ships as an artifact
recording a per-statement classification rather than as a pattern over
surfaces.

## The levels are measured, not remembered

Every precedence and associativity in `data/foreign_voice/grouping.json` was
read off the **pinned binary** before this file was written, by elaborating
`a OP b OP c` against its two bracketings and comparing serialized `Expr`
digests.  The table is what the toolchain does, not what a reference manual
says — and G1 re-checks the whole thing over all 2,313 covered statements,
because one wrong level is wrong everywhere.

Two rules could not be measured that way and were supplied as clauses
(Correction 3), then confirmed against the binary:

* **binder-group stripping** — `∃ (x y : Rat), p` ≡ `∃ x y : Rat, p`.
* **tail-position propagation** — a binder body extends maximally right, so a
  binder needs brackets **iff it is not in tail position**.  `¬ ∃ x : Rat, p`
  is already canonical; `(∀ x : Rat, p) ∧ q` is not removable.

## What the rule cannot do

It never **adds** a bracket the source omitted.  A source statement parses, so
the structure it denotes already follows precedence, and the canonical form of
a parsing source can only remove.  Checked rather than assumed: the census
publishes the per-statement delta and there is no negative bucket.

## Read-only

This module measures and re-emits.  It writes no artifact of its own except
through its CLI, imports nothing from the renderer, and is the target G-P's
implementation must agree with on all 2,313 statements.
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

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULE = REPO_ROOT / "data" / "foreign_voice" / "grouping.json"

#: An atom binds tighter than every operator; nothing ever brackets one.
ATOM_LEVEL = 1000
#: A binder expression sits below every operator: it is bracketed by POSITION
#: (tail or not), never by level.
BINDER_LEVEL = 0

_IDENT_START = r"A-Za-z_α-ωΑ-Ω"
_IDENT_CONT = _IDENT_START + r"0-9'₀-₉ₐ-ₜ"
_IDENT_RE = re.compile(rf"[{_IDENT_START}][{_IDENT_CONT}]*")
_NUMERAL_RE = re.compile(r"\d+(?:\.\d+)?")


class GroupingError(ValueError):
    """The dialect said something this parser does not model. Never guessed at."""


# --------------------------------------------------------------------------
# The rule artifact
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rule:
    """`grouping.json`, loaded. Trusted and reviewed, like rule R and the table."""

    rule_id: str
    infix: dict[str, tuple[int, str]]
    prefix: dict[str, int]
    binders: tuple[str, ...]
    strip_binder_group: bool
    keep_ascription: bool

    @classmethod
    def load(cls, path: Path | None = None) -> "Rule":
        raw = json.loads((path or DEFAULT_RULE).read_text(encoding="utf-8"))
        infix = {row["token"]: (row["precedence"], row["associativity"])
                 for row in raw["levels"]}
        prefix = {row["token"]: row["argument_precedence"] for row in raw["prefix"]}
        for token, (_lvl, assoc) in infix.items():
            if assoc not in {"left", "right", "none"}:
                raise GroupingError(f"{token!r}: unknown associativity {assoc!r}")
        return cls(
            rule_id=raw["rule_id"],
            infix=infix,
            prefix=prefix,
            binders=tuple(raw["binders"]),
            strip_binder_group=raw["binder_group_rule"]["strip"],
            keep_ascription=raw["ascription_rule"]["never_a_grouping_pair"],
        )


# --------------------------------------------------------------------------
# The tree
# --------------------------------------------------------------------------


@dataclass
class Node:
    level: int = ATOM_LEVEL


@dataclass
class Atom(Node):
    text: str = ""


@dataclass
class Infix(Node):
    op: str = ""
    left: Node | None = None
    right: Node | None = None
    assoc: str = "left"


@dataclass
class Prefix(Node):
    op: str = ""
    arg: Node | None = None
    arg_level: int = 0


@dataclass
class Binder(Node):
    op: str = ""
    names: tuple[str, ...] = ()
    type_name: str | None = None
    body: Node | None = None
    #: the source wrote `∃ (x y : T),`. The rule strips it; recorded for the census.
    source_bracketed: bool = False
    level: int = BINDER_LEVEL


@dataclass
class Ascription(Node):
    """`(e : T)` — the brackets ARE the ascription and are never grouping."""

    inner: Node | None = None
    type_name: str = ""
    level: int = ATOM_LEVEL


@dataclass
class Group(Node):
    """A grouping pair the SOURCE wrote. Kept for the census; never emitted as-is."""

    inner: Node | None = None

    @property
    def effective(self) -> Node:
        node = self.inner
        while isinstance(node, Group):
            node = node.inner
        return node


# --------------------------------------------------------------------------
# Tokenizing
# --------------------------------------------------------------------------


def tokenize(text: str, rule: Rule) -> list[str]:
    """R(s) as a flat token list. Longest-first, so `>=` never splits into `>` `=`."""
    tokens = sorted(set(rule.infix) | set(rule.prefix) | set(rule.binders)
                    | {"(", ")", ",", ":"}, key=lambda t: (-len(t), t))
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        match = _IDENT_RE.match(text, i)
        if match:
            out.append(match.group(0))
            i = match.end()
            continue
        match = _NUMERAL_RE.match(text, i)
        if match:
            out.append(match.group(0))
            i = match.end()
            continue
        for token in tokens:
            if text.startswith(token, i):
                out.append(token)
                i += len(token)
                break
        else:
            raise GroupingError(f"no rule covers {text[i]!r} at offset {i}")
    return out


def _is_name(token: str) -> bool:
    return bool(_IDENT_RE.fullmatch(token))


# --------------------------------------------------------------------------
# Parsing — a Pratt parser at the measured levels
# --------------------------------------------------------------------------


class Parser:
    def __init__(self, tokens: list[str], rule: Rule) -> None:
        self.tokens = tokens
        self.rule = rule
        self.i = 0

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise GroupingError("unexpected end of statement")
        self.i += 1
        return token

    def expect(self, token: str) -> None:
        got = self.take()
        if got != token:
            raise GroupingError(f"expected {token!r}, got {got!r}")

    def parse(self) -> Node:
        node = self.expr(0)
        if self.peek() is not None:
            raise GroupingError(f"trailing {self.tokens[self.i:][:4]}")
        return node

    def expr(self, min_level: int) -> Node:
        left = self.leading()
        if isinstance(left, Binder):
            # An UNBRACKETED binder swallowed everything to the end of the
            # extent, so it can never be the left operand of an infix operator:
            # `∀ x, p ∧ q` puts the `∧` inside the body, and getting `∧` outside
            # requires the bracket that `(∀ x, p) ∧ q` writes.
            # Without this, `∀ a b c : Rat, a = b = c` — which the toolchain
            # REJECTS — parsed here as `(∀ a b c : Rat, a = b) = c`, silently
            # re-associating an input that is not a term. A parser that invents
            # a reading the pinned binary refuses is the exact class of defect
            # G1 exists to catch, and this one is catchable structurally.
            return left
        banned: int | None = None
        while True:
            token = self.peek()
            if token is None or token not in self.rule.infix:
                break
            level, assoc = self.rule.infix[token]
            if level < min_level or level == banned:
                break
            left_min = level if assoc == "left" else level + 1
            if _written_level(left) < left_min:
                # The left operand is too loose to sit there as written. The
                # toolchain rejects such input and so must this: without the
                # check, `a = b ∧ b = c → a = b = c` parsed as
                # `(… → (a = b)) = c`, re-associating a non-associative
                # relation across an implication — a reading the pinned binary
                # has no term for. A parser that invents one is a parser whose
                # agreement with G1 would be luck.
                raise GroupingError(
                    f"{token!r} cannot take a level-{_written_level(left)} left "
                    f"operand; it requires at least {left_min}")
            self.take()
            if assoc == "left":
                right_min = level + 1
            elif assoc == "right":
                right_min = level
            else:
                right_min = level + 1
            right = self.expr(right_min)
            left = Infix(level=level, op=token, left=left, right=right, assoc=assoc)
            # A non-associative operator may not chain at its own level: Lean
            # rejects `a = b = c`, so this parser must too rather than inventing
            # an associativity the toolchain does not have.
            banned = level if assoc == "none" else None
        return left

    def leading(self) -> Node:
        token = self.peek()
        if token is None:
            raise GroupingError("expected a term")
        if token in self.rule.binders:
            return self.binder()
        if token in self.rule.prefix:
            self.take()
            arg_level = self.rule.prefix[token]
            return Prefix(level=arg_level, op=token, arg=self.expr(arg_level),
                          arg_level=arg_level)
        if token == "(":
            return self.bracketed()
        self.take()
        return Atom(text=token)

    def binder(self) -> Node:
        op = self.take()
        bracketed = self.peek() == "("
        if bracketed:
            self.take()
        names: list[str] = []
        while _is_name(self.peek() or ""):
            names.append(self.take())
        if not names:
            raise GroupingError(f"{op}: no binder names")
        type_name = None
        if self.peek() == ":":
            self.take()
            type_name = self.take()
        if bracketed:
            self.expect(")")
        self.expect(",")
        body = self.expr(0)
        return Binder(op=op, names=tuple(names), type_name=type_name, body=body,
                      source_bracketed=bracketed)

    def bracketed(self) -> Node:
        self.expect("(")
        inner = self.expr(0)
        if self.peek() == ":":
            self.take()
            type_name = self.take()
            self.expect(")")
            return Ascription(inner=inner, type_name=type_name)
        self.expect(")")
        return Group(level=inner.level, inner=inner)


def parse(text: str, rule: Rule) -> Node:
    return Parser(tokenize(text, rule), rule).parse()


# --------------------------------------------------------------------------
# Canonical emission
# --------------------------------------------------------------------------


@dataclass
class Emission:
    tokens: list[str] = field(default_factory=list)
    #: one entry per emitted bracket pair: "grouping" | "ascription"
    pair_kinds: list[str] = field(default_factory=list)


def _level(node: Node) -> int:
    """The level a node BEHAVES at once its source brackets are discarded."""
    return _level(node.effective) if isinstance(node, Group) else node.level


def _written_level(node: Node) -> int:
    """The level a node behaves at AS THE SOURCE WROTE IT.

    A bracketed sub-expression is an atom to the parser however loose its
    contents are: `(a + b) * c` is fine, `a + b * c` groups differently. The
    two functions differ only for `Group`, and that difference is the whole
    distinction between what the source said and what the tree means.
    """
    return ATOM_LEVEL if isinstance(node, (Group, Ascription, Atom)) else node.level


def emit(node: Node, rule: Rule) -> Emission:
    """The canonical token stream: a bracket only where precedence demands one."""
    out = Emission()
    _emit(node, rule, 0, True, out)
    return out


def _emit(node: Node, rule: Rule, min_level: int, tail: bool,
          out: Emission) -> None:
    if isinstance(node, Group):
        # A source grouping pair carries no information the tree does not: it
        # is re-derived, never copied.
        _emit(node.effective, rule, min_level, tail, out)
        return

    if isinstance(node, Binder):
        # Tail-position propagation (Correction 3): a binder body extends
        # maximally right, so a binder needs brackets iff something follows it
        # inside the current extent.
        wrap = not tail
        if wrap:
            out.tokens.append("(")
            out.pair_kinds.append("grouping")
        out.tokens.append(node.op)
        # binder_group_rule: the source's `( … )` around the names is dropped.
        out.tokens.extend(node.names)
        if node.type_name is not None:
            out.tokens.extend([":", node.type_name])
        out.tokens.append(",")
        _emit(node.body, rule, 0, True, out)
        if wrap:
            out.tokens.append(")")
        return

    if isinstance(node, Ascription):
        # The brackets ARE the ascription: emitted always, classified always.
        out.tokens.append("(")
        out.pair_kinds.append("ascription")
        _emit(node.inner, rule, 0, True, out)
        out.tokens.extend([":", node.type_name, ")"])
        return

    wrap = _level(node) < min_level
    if wrap:
        out.tokens.append("(")
        out.pair_kinds.append("grouping")
    # A bracket RE-ESTABLISHES tail position: inside it the extent ends at the
    # matching `)`, so whatever sits rightmost inside is in tail position there.
    # Getting this backwards is what made the emitter ADD a bracket on
    # lean_workbook_plus_82031 — `(B → ∀ x y z : Rat, body)` came back as
    # `(B → (∀ x y z : Rat, body))` — and the census's no-negative-bucket check
    # caught it on exactly one statement in 2,313. The rule can only remove;
    # one statement gaining a bracket was the whole claim failing.
    inner_tail = True if wrap else tail

    if isinstance(node, Atom):
        out.tokens.append(node.text)
    elif isinstance(node, Prefix):
        out.tokens.append(node.op)
        _emit(node.arg, rule, node.arg_level, inner_tail, out)
    elif isinstance(node, Infix):
        level, assoc = node.level, node.assoc
        left_min = level if assoc == "left" else level + 1
        right_min = level if assoc == "right" else level + 1
        _emit(node.left, rule, left_min, False, out)
        out.tokens.append(node.op)
        _emit(node.right, rule, right_min, inner_tail, out)
    else:  # pragma: no cover - every node type is handled above
        raise GroupingError(f"cannot emit {type(node).__name__}")

    if wrap:
        out.tokens.append(")")


def canon(text: str, rule: Rule) -> str:
    """R(s) -> its canonical spelling, space-separated."""
    return " ".join(emit(parse(text, rule), rule).tokens)


# --------------------------------------------------------------------------
# Census helpers
# --------------------------------------------------------------------------


def signature(node: Node) -> tuple:
    """The tree with every GROUPING bracket erased — what the brackets denote.

    G-P's round-trip test is `parse → emit → parse` yielding *the same tree*,
    and a `Group` wrapper is not part of the tree's meaning: it is the source's
    way of writing the shape. Comparing raw nodes would compare bracket
    placement, which is exactly the thing canonicalization is allowed to change.

    Ascriptions and binder groups DO appear here — an ascription is syntax with
    a meaning, and whether a binder group was written bracketed is recorded so
    the stripping is visible as a change rather than hidden by the comparison.
    """
    if isinstance(node, Group):
        return signature(node.effective)
    if isinstance(node, Atom):
        return ("atom", node.text)
    if isinstance(node, Prefix):
        return ("prefix", node.op, signature(node.arg))
    if isinstance(node, Infix):
        return ("infix", node.op, signature(node.left), signature(node.right))
    if isinstance(node, Binder):
        return ("binder", node.op, node.names, node.type_name,
                signature(node.body))
    if isinstance(node, Ascription):
        return ("ascription", node.type_name, signature(node.inner))
    raise GroupingError(f"cannot sign {type(node).__name__}")  # pragma: no cover


def source_pairs(node: Node, tail: bool = True) -> list[str]:
    """Every bracket pair the SOURCE wrote, classified by kind."""
    kinds: list[str] = []
    if isinstance(node, Group):
        kinds.append("grouping")
        kinds.extend(source_pairs(node.inner, tail))
    elif isinstance(node, Ascription):
        kinds.append("ascription")
        kinds.extend(source_pairs(node.inner, True))
    elif isinstance(node, Binder):
        if node.source_bracketed:
            kinds.append("binder_group")
        kinds.extend(source_pairs(node.body, True))
    elif isinstance(node, Prefix):
        kinds.extend(source_pairs(node.arg, tail))
    elif isinstance(node, Infix):
        kinds.extend(source_pairs(node.left, False))
        kinds.extend(source_pairs(node.right, tail))
    return kinds


def grouping_pair_spans(tokens: list[str], kinds: list[str]) -> list[tuple[int, int]]:
    """Index spans of the emitted GROUPING pairs, in emission order.

    `kinds` is `Emission.pair_kinds`, one entry per emitted `(` in the order
    they were emitted, which is the order they open in the token stream.
    """
    spans: list[tuple[int, int]] = []
    stack: list[tuple[int, int]] = []
    opened = 0
    for index, token in enumerate(tokens):
        if token == "(":
            stack.append((index, opened))
            opened += 1
        elif token == ")":
            start, which = stack.pop()
            if kinds[which] == "grouping":
                spans.append((start, index))
    spans.sort()
    return spans


def delete_pair(tokens: list[str], span: tuple[int, int]) -> list[str]:
    """The matched-pair deletion §3.3 specifies — by index, not by `str.replace`."""
    start, end = span
    return [t for i, t in enumerate(tokens) if i not in (start, end)]


__all__ = ["ATOM_LEVEL", "Ascription", "Atom", "Binder", "Emission", "Group",
           "GroupingError", "Infix", "Node", "Parser", "Prefix", "Rule",
           "canon", "delete_pair", "emit", "grouping_pair_spans", "parse",
           "source_pairs", "tokenize"]


def census(rows: list[dict], sealed: list[dict], rule: Rule) -> dict:
    """G0 — the §3 probe, published BEFORE any bracketing rule is proposed.

    No floor. *A probe with a floor is an item*; its ordering is the gate. The
    exposure counts say how much surface moves and nothing about whether the
    move helps a reader — only C-V3 could say that, and it is ABSENT.
    """
    from collections import Counter

    statements: list[dict] = []
    failures: list[dict] = []
    kinds = Counter()
    carrying = Counter()
    delta = Counter()
    source_grouping = emitted_grouping = 0
    binder_groups_stripped = 0
    changed = gained = lose_all = only_ascription = 0
    admitting_before = admitting_after = admitting_through_grouping = 0

    for row in rows:
        text = row["interpreted"]
        try:
            node = parse(text, rule)
            emission = emit(node, rule)
        except GroupingError as exc:
            failures.append({"statement_id": row["statement_id"],
                             "error": str(exc)})
            continue
        source = source_pairs(node)
        emitted = emission.pair_kinds
        kinds.update(source)
        for kind in set(source):
            carrying[kind] += 1
        before = source.count("grouping")
        after = emitted.count("grouping")
        source_grouping += before
        emitted_grouping += after
        binder_groups_stripped += source.count("binder_group")
        moved = tokenize(text, rule) != emission.tokens
        changed += moved
        gained += after > before
        delta[before - after] += 1
        if before and not after:
            lose_all += 1
        if not after and emitted.count("ascription"):
            only_ascription += 1
        # v0.19's `_admits` for drop_group and shift_group asks whether the
        # phrase `the quantity` appears in the surface. All three pair kinds
        # render through that one row, so the pool admits on ANY pair — which
        # is G5b's whole point.
        if source:
            admitting_before += 1
        if emitted:
            admitting_after += 1
        if before:
            admitting_through_grouping += 1
        statements.append({
            "statement_id": row["statement_id"],
            "corpus": row["corpus"],
            "changed": moved,
            "pair_kinds_source": source,
            "pair_kinds_canonical": emitted,
            "grouping_pairs_before": before,
            "grouping_pairs_after": after,
            "canonical": " ".join(emission.tokens),
        })

    sealed_changed: list[str] = []
    sealed_source = sealed_emitted = sealed_gained = sealed_failed = 0
    for row in sealed:
        try:
            node = parse(row["interpreted"], rule)
            emission = emit(node, rule)
        except GroupingError:
            sealed_failed += 1
            continue
        before = source_pairs(node).count("grouping")
        after = emission.pair_kinds.count("grouping")
        sealed_source += before
        sealed_emitted += after
        sealed_gained += after > before
        if tokenize(row["interpreted"], rule) != emission.tokens:
            sealed_changed.append(row["statement_id"])

    total_source_pairs = sum(kinds.values())
    redundant_grouping = source_grouping - emitted_grouping
    return {
        "census_id": "foreign_voice.grouping_census.v1",
        "measured": "2026-08-24",
        "gate": "G0 — the §3 probe, published before the rule is proposed",
        "design": "docs/DESIGN-voice-completion.md",
        "rule": "data/foreign_voice/grouping.json",
        "no_floor": (
            "A probe with a floor is an item. Its ORDERING is the gate: this "
            "file is published before the bracketing rule is proposed, and the "
            "design is admissible only behind it."
        ),
        "covered": {
            "statements": len(rows),
            "parse_failures": len(failures),
            "failures": failures,
            "changed": changed,
            "already_canonical": len(rows) - changed - len(failures),
            "changed_share": round(changed / len(rows), 4) if rows else 0.0,
        },
        "pairs": {
            "source_by_kind": dict(kinds),
            "statements_carrying_kind": dict(carrying),
            "source_grouping_pairs": source_grouping,
            "canonical_grouping_pairs": emitted_grouping,
            "redundant_grouping_pairs": redundant_grouping,
            "binder_group_pairs_stripped": binder_groups_stripped,
            "total_source_pairs_all_kinds": total_source_pairs,
            "redundant_or_stripped": redundant_grouping + binder_groups_stripped,
            "grouping_words_emitted_before": source_grouping * 2,
            "grouping_words_removed": redundant_grouping * 2,
            "grouping_words_removed_share": (
                round(redundant_grouping / source_grouping, 4)
                if source_grouping else 0.0),
            "note": [
                "`redundant_or_stripped` over `total_source_pairs_all_kinds` is "
                "the design's §6 headline pair ratio: it counts a stripped "
                "binder group as removed and takes all three kinds in the "
                "denominator.",
                "`redundant_grouping_pairs` over `source_grouping_pairs` is the "
                "narrower reading, over grouping pairs only, and it is the one "
                "G1b's floor is stated against."
            ],
        },
        "it_can_only_remove": {
            "gained_a_bracket": gained,
            "delta_distribution": {str(k): v for k, v in sorted(delta.items())},
            "claim": "the canonical form of a parsing source can only remove",
            "checked": (
                "there is no negative bucket in the delta distribution. This "
                "check found a real defect during construction: the first "
                "transcription of the tail-position clause made the emitter add "
                "a bracket on exactly one statement of 2,313 "
                "(lean_workbook_plus_82031)."
            ),
        },
        "exposure": {
            "label": (
                "EXPOSURE, NOT READABILITY. These counts say how much surface "
                "changes and nothing about whether the change helps a reader. "
                "Only C-V3 could say that, and it is ABSENT."
            ),
            "statements_losing_every_grouping_word": lose_all,
            "definition": (
                "a statement that carried at least one grouping pair and "
                "carries none after canonicalization"
            ),
            "statements_whose_only_remaining_pair_is_an_ascription": only_ascription,
            "delta_distribution": {str(k): v for k, v in sorted(delta.items())},
            "worked_example": (
                "lean_workbook_20627 canonicalizes to four disjuncts with no "
                "grouping word anywhere; §8 keeps open whether that helps"
            ),
        },
        "drop_group_pool": {
            "gate": "G5b — no mutation pool contains a cross-kind record",
            "v019_admitting": admitting_before,
            "canonical_admitting": admitting_after,
            "admitting_through_a_real_grouping_pair": admitting_through_grouping,
            "admitting_only_through_ascription_or_binder_group": (
                admitting_before - admitting_through_grouping),
            "why_this_is_the_finding": [
                "v0.19's `_admits` asked whether the phrase `the quantity` "
                "appears in the surface. All three pair kinds render through "
                "that one lexicon row, so the pool admitted statements whose "
                "only bracket was an ascription or a binder group — statements "
                "with no grouping bracket at all, padding the denominator of a "
                "control about grouping.",
                "C-V4-prime's drop_group and shift_group pools are grouping-only "
                "by `pair_kind`, and G5b's floor is zero cross-kind records read "
                "from the field rather than argued."
            ],
        },
        "sealed_hundred": {
            "statements": len(sealed),
            "parse_failures": sealed_failed,
            "changed": len(sealed_changed),
            "byte_identical": len(sealed) - len(sealed_changed) - sealed_failed,
            "gained_a_bracket": sealed_gained,
            "source_grouping_pairs": sealed_source,
            "canonical_grouping_pairs": sealed_emitted,
            "redundant_grouping_pairs": sealed_source - sealed_emitted,
            "changed_ids": sorted(sealed_changed),
            "note": (
                "these 15 are the re-seal of §3.2 — 15 hand-authored sentences, "
                "not 100. The other 85 must stay byte-identical to the v0.19 "
                "seal, and G2 asserts it."
            ),
        },
        "statements": statements,
    }


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--term", action="append", default=[])
    parser.add_argument("--census", action="store_true")
    parser.add_argument("--out", type=Path,
                        default=REPO_ROOT / "experiments" / "grouping_census.json")
    args = parser.parse_args(argv)
    rule = Rule.load()
    for term in args.term:
        print(f"  in : {term}")
        print(f"  out: {canon(term, rule)}")
    if args.census:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import measure_foreign_voice as mfv

        data = REPO_ROOT / "data" / "foreign_voice"
        preview = json.loads((data / "eligibility_preview.json").read_text(encoding="utf-8"))
        register = json.loads((data / "register.json").read_text(encoding="utf-8"))
        sealed = json.loads((data / "b0d_sealed_renderings.json").read_text(encoding="utf-8"))
        report = census(mfv.covered_rows(preview, register),
                        sealed["renderings"], rule)
        args.out.write_text(
            json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
        covered, pairs = report["covered"], report["pairs"]
        print(f"G0  covered {covered['statements']}  failures {covered['parse_failures']}  "
              f"changed {covered['changed']}  canonical {covered['already_canonical']}")
        print(f"    grouping pairs {pairs['source_grouping_pairs']} -> "
              f"{pairs['canonical_grouping_pairs']} "
              f"(redundant {pairs['redundant_grouping_pairs']}); "
              f"gained {report['it_can_only_remove']['gained_a_bracket']}")
        print(f"    written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
