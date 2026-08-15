#!/usr/bin/env python3
"""Lean-surface → matcher-template emitter (docs/DESIGN-skeleton-emitter.md).

Admission is still `grammar_coverage.classify` (`full_ok`). This module only
translates a covered statement into a string the matcher already parses.
A failed emit or a failed `template_parses` is an exclusion, not a reason
to widen the matcher.
"""

from __future__ import annotations

import re

import grammar_coverage as gc
from match_signatures import (
    Parser,
    TemplateParseError,
    canonicalize,
    template_slots,
    tokenize,
)

# Longest Lean spellings first so `Real.sin` wins over `sin`.
_HEAD_REWRITE: list[tuple[str, str]] = sorted(
    (
        list(gc._SUPPORTED_FUNCS.items())
        + list(gc._SUPPORTED_PREDICATES.items())
        + list(gc._PROP_CONSTS.items())
    ),
    key=lambda kv: -len(kv[0]),
)
_HEAD_RE = re.compile(
    r"(?<![\w.])("
    + "|".join(re.escape(src) for src, _ in _HEAD_REWRITE)
    + r")(?![\w.'])"
)
_HEAD_MAP = dict(_HEAD_REWRITE)
FUNC_HEADS = frozenset(gc._SUPPORTED_FUNCS.values()) | frozenset(
    gc._SUPPORTED_PREDICATES.values()
)
NULLARY_HEADS = frozenset(gc._PROP_CONSTS.values())

_GREEK = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "eps",
    "ζ": "zeta", "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa",
    "λ": "lam", "μ": "mu", "ν": "nu", "ξ": "xi", "ο": "omicron",
    "π": "pi", "ρ": "rho", "σ": "sigma", "ς": "sigma", "τ": "tau",
    "υ": "ups", "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
    "Α": "Alpha", "Β": "Beta", "Γ": "Gamma", "Δ": "Delta", "Θ": "Theta",
    "Λ": "Lam", "Π": "Pi", "Σ": "Sigma", "Φ": "Phi", "Ψ": "Psi", "Ω": "Omega",
}
_SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
_SQRT_BARE = re.compile(r"√\s*(\d+(?:\.\d+)?)")
_ASCRIPTION = re.compile(r"\(\s*([^():]+?)\s*:\s*[^)]+\)")
# Unparenthesized binder types: `∀ x y : ℝ,` — not an ascription group.
_TYPE_ANN = re.compile(
    r":\s*(?:ℝ≥0|NNReal|Real|Nat|Int|Rat|PNat|ℝ|ℕ\+|ℕ|ℤ|ℚ)"
)
_COERCE = re.compile(r"↑")

_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
_NUMBER = re.compile(r"\d+(?:\.\d+)?")

_OPS = [
    ("∃!", "EXISTS_UNIQUE"),
    ("<=", "<="),
    (">=", ">="),
    ("≠", "NE"),
    ("≤", "<="),
    ("≥", ">="),
    ("↔", "IFF"),
    ("→", "IMPLIES"),
    ("∧", "AND"),
    ("∨", "OR"),
    ("¬", "NOT"),
    ("∀", "FORALL"),
    ("∃", "EXISTS"),
    ("=", "="),
    ("<", "<"),
    (">", ">"),
    ("+", "+"),
    ("-", "-"),
    ("*", "*"),
    ("/", "/"),
    ("^", "^"),
    ("(", "("),
    (")", ")"),
    (",", ","),
]


class EmitError(ValueError):
    pass


def romanize(text: str) -> str:
    return "".join(_GREEK.get(ch, ch) for ch in text.translate(_SUBSCRIPTS))


def strip_ascriptions(text: str) -> str:
    prev = None
    cur = text
    while prev != cur:
        prev = cur
        cur = _ASCRIPTION.sub(r"\1", cur)
    return _COERCE.sub("", cur)


def rewrite_heads(text: str) -> str:
    text = _SQRT_BARE.sub(r"SQRT(\1)", text)
    text = text.replace("√", "SQRT")
    return _HEAD_RE.sub(lambda m: _HEAD_MAP[m.group(1)], text)


def preprocess(text: str) -> str:
    text = _TYPE_ANN.sub("", text)
    return rewrite_heads(strip_ascriptions(romanize(text)))


def tokenize_lean(text: str) -> list[str]:
    s = " ".join(preprocess(text).split())
    tokens: list[str] = []
    i, n = 0, len(s)
    while i < n:
        if s[i].isspace():
            i += 1
            continue
        hit = False
        for lex, name in _OPS:
            if s.startswith(lex, i):
                tokens.append(name)
                i += len(lex)
                hit = True
                break
        if hit:
            continue
        m = _IDENT.match(s, i)
        if m:
            tokens.append(m.group(0))
            i = m.end()
            continue
        m = _NUMBER.match(s, i)
        if m:
            tokens.append(m.group(0))
            i = m.end()
            continue
        raise EmitError(f"untokenizable {s[i:i + 12]!r}")
    return tokens


def _is_ident(tok: str) -> bool:
    return bool(tok) and tok[0].isalpha()


def _is_num(tok: str) -> bool:
    return bool(tok) and tok[0].isdigit()


class LeanParser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def next(self) -> str:
        tok = self.peek()
        if tok is None:
            raise EmitError("unexpected end")
        self.i += 1
        return tok

    def eat(self, expected: str) -> None:
        got = self.next()
        if got != expected:
            raise EmitError(f"expected {expected!r}, got {got!r}")

    def parse(self) -> tuple:
        node = self.parse_iff()
        if self.peek() is not None:
            raise EmitError(f"trailing {self.peek()!r}")
        return node

    def parse_iff(self) -> tuple:
        node = self.parse_implies()
        while self.peek() == "IFF":
            self.next()
            rhs = self.parse_implies()
            node = (
                "call",
                "MEET",
                (
                    ("call", "IMPLIES", (node, rhs)),
                    ("call", "IMPLIES", (rhs, node)),
                ),
            )
        return node

    def parse_implies(self) -> tuple:
        node = self.parse_or()
        if self.peek() == "IMPLIES":
            self.next()
            return ("call", "IMPLIES", (node, self.parse_implies()))
        return node

    def parse_or(self) -> tuple:
        node = self.parse_and()
        while self.peek() == "OR":
            self.next()
            node = ("call", "JOIN", (node, self.parse_and()))
        return node

    def parse_and(self) -> tuple:
        node = self.parse_not()
        while self.peek() == "AND":
            self.next()
            node = ("call", "MEET", (node, self.parse_not()))
        return node

    def parse_not(self) -> tuple:
        if self.peek() == "NOT":
            self.next()
            return ("call", "NEG", (self.parse_not(),))
        if self.peek() in {"FORALL", "EXISTS", "EXISTS_UNIQUE"}:
            return self.parse_quant()
        return self.parse_relation()

    def parse_quant(self) -> tuple:
        kind = self.next()
        head = "EXISTS" if kind in {"EXISTS", "EXISTS_UNIQUE"} else "FORALL"
        names = self._quant_names()
        body = self.parse_iff()
        node = body
        for name in reversed(names):
            node = ("call", head, (("slot", name), node))
        return node

    def _quant_names(self) -> list[str]:
        names: list[str] = []
        while True:
            tok = self.peek()
            if tok is None or tok == ",":
                break
            if tok == "(":
                self.next()
                inner: list[str] = []
                depth = 1
                while depth:
                    t = self.next()
                    if t == "(":
                        depth += 1
                    elif t == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    inner.append(t)
                if ":" in inner:
                    inner = inner[: inner.index(":")]
                names.extend(t for t in inner if _is_ident(t))
                continue
            if tok == ":":
                while self.peek() not in {None, ","}:
                    if self.peek() == "(":
                        self._skip_parens()
                    else:
                        self.next()
                break
            if _is_ident(tok):
                names.append(self.next())
                continue
            break
        if self.peek() == ",":
            self.next()
        if not names:
            raise EmitError("quantifier with no bound names")
        return names

    def _skip_parens(self) -> None:
        self.eat("(")
        depth = 1
        while depth:
            t = self.next()
            if t == "(":
                depth += 1
            elif t == ")":
                depth -= 1

    def parse_relation(self) -> tuple:
        lhs = self.parse_sum()
        tok = self.peek()
        if tok in {"=", "<=", ">=", "<", ">", "NE"}:
            self.next()
            rhs = self.parse_sum()
            if tok == "NE":
                return ("call", "NEG", (("rel", "=", (lhs, rhs)),))
            return ("rel", tok, (lhs, rhs))
        return lhs

    def parse_sum(self) -> tuple:
        node = self.parse_prod()
        while self.peek() in {"+", "-"}:
            op = self.next()
            rhs = self.parse_prod()
            if op == "-":
                rhs = ("op", "neg", (rhs,))
            node = ("op", "+", (node, rhs))
        return node

    def parse_prod(self) -> tuple:
        node = self.parse_pow()
        while self.peek() in {"*", "/"}:
            op = self.next()
            rhs = self.parse_pow()
            if op == "/":
                rhs = ("op", "inv", (rhs,))
            node = ("op", "*", (node, rhs))
        return node

    def parse_pow(self) -> tuple:
        base = self.parse_app()
        if self.peek() == "^":
            self.next()
            return ("op", "^", (base, self.parse_pow()))
        return base

    def parse_app(self) -> tuple:
        node = self.parse_atom()
        if node[0] == "slot" and node[1] in FUNC_HEADS:
            return ("call", node[1], (self.parse_atom(),))
        if node[0] == "slot" and node[1] in NULLARY_HEADS:
            return ("call", node[1], ())
        return node

    def parse_atom(self) -> tuple:
        tok = self.peek()
        if tok is None:
            raise EmitError("unexpected end")
        if tok == "(":
            self.next()
            node = self.parse_iff()
            self.eat(")")
            return node
        if tok == "-":
            self.next()
            return ("op", "neg", (self.parse_atom(),))
        if tok == "NOT":
            self.next()
            return ("call", "NEG", (self.parse_atom(),))
        if tok in {"FORALL", "EXISTS", "EXISTS_UNIQUE"}:
            return self.parse_quant()
        tok = self.next()
        if _is_num(tok):
            return ("num", float(tok))
        if _is_ident(tok):
            return ("slot", tok)
        raise EmitError(f"unexpected token {tok!r}")


def parse_lean(text: str) -> tuple:
    return LeanParser(tokenize_lean(text)).parse()


def render_template(node: tuple, parent_prec: int = 0) -> str:
    kind = node[0]
    if kind == "num":
        val = node[1]
        return str(int(val)) if float(val).is_integer() else f"{val:g}"
    if kind == "slot":
        return node[1]
    if kind == "rel":
        lhs = render_template(node[2][0], 11)
        rhs = render_template(node[2][1], 11)
        s = f"{lhs} {node[1]} {rhs}"
        return f"({s})" if parent_prec > 10 else s
    if kind == "op" and node[1] == "neg":
        inner = render_template(node[2][0], 50)
        return f"(-{inner})" if parent_prec > 20 else f"-{inner}"
    if kind == "op" and node[1] == "+":
        s = " + ".join(render_template(a, 20) for a in node[2])
        return f"({s})" if parent_prec > 20 else s
    if kind == "op" and node[1] == "*":
        nums: list[str] = []
        dens: list[str] = []
        for a in node[2]:
            if a[0] == "op" and a[1] == "inv":
                dens.append(render_template(a[2][0], 31))
            else:
                nums.append(render_template(a, 30))
        if not nums:
            nums = ["1"]
        s = " * ".join(nums)
        for d in dens:
            s = f"{s} / {d}"
        return f"({s})" if parent_prec > 30 else s
    if kind == "op" and node[1] == "^":
        s = (
            f"{render_template(node[2][0], 41)} ^ "
            f"{render_template(node[2][1], 40)}"
        )
        return f"({s})" if parent_prec > 40 else s
    if kind == "op" and node[1] == "inv":
        s = f"1 / {render_template(node[2][0], 31)}"
        return f"({s})" if parent_prec > 30 else s
    if kind == "call":
        args = ", ".join(render_template(a, 0) for a in node[2])
        return f"{node[1]}({args})"
    raise EmitError(f"cannot render {kind}")


def _fold_meet(nodes: list[tuple]) -> tuple:
    acc = nodes[0]
    for n in nodes[1:]:
        acc = ("call", "MEET", (acc, n))
    return acc


def emit_expr(text: str) -> str:
    return render_template(parse_lean(text))


def emit_statement(stmt: dict) -> str:
    """Emit the full statement (hyps → IMPLIES) as a matcher template."""
    goal_node = parse_lean(stmt["goal"])
    pieces = [parse_lean(h) for h in [*(stmt.get("goal_lets") or []),
                                      *(stmt.get("hyps") or [])]]
    if pieces:
        return render_template(
            ("call", "IMPLIES", (_fold_meet(pieces), goal_node))
        )
    return render_template(goal_node)


def template_parses(template: str) -> bool:
    try:
        canonicalize(Parser(tokenize(template)).parse())
    except TemplateParseError:
        return False
    return True


def emit_or_reason(stmt: dict) -> tuple[str | None, str | None]:
    """Return (template, None) or (None, reason)."""
    try:
        template = emit_statement(stmt)
    except EmitError as exc:
        return None, f"emit:{exc}"
    if not template_parses(template):
        return None, "parse_fail"
    return template, None


def slots_in(template: str) -> list[str]:
    try:
        tree = Parser(tokenize(template)).parse()
    except TemplateParseError:
        return []
    return sorted(template_slots(tree))
