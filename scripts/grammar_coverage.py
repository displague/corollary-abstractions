#!/usr/bin/env python3
"""Shared grammar-coverage classifier for ingested formal statements.

Extracted from the miniF2F slice so a second source (Lean-workbook-proofs, in
Lean 4) can reuse the exact same head-algebra judgement. The parser is
dialect-agnostic (it scans parentheses, not keywords); the classifier is made
dialect-aware by carrying BOTH spellings of the mathlib names that differ between
Lean 3 (lowercase `real.sqrt`, `finset`, `nat.prime`) and Lean 4 (capitalized
`Real.sqrt`, `Finset`, `Nat.Prime`, and — under `open Real Nat` — the bare forms
`sqrt`, `Prime`). Every Lean-4 spelling is added as an ALTERNATIVE to the Lean-3
one, never a replacement, so the miniF2F measurement regenerates byte-for-byte.

"Covered" is unchanged from the miniF2F write-up: a statement reduces to a
skeleton whose every leaf is a numeral or a numeric-typed bound variable and
every internal node is a head the corpus actually carries (verified against
data/*/nodes.json): relations (= ≠ < ≤ > ≥ ↔), MEET/JOIN/NEG/IMPLIES, arithmetic
(+ - * / ^), and SQRT/LOG/EXP. Modulo (%) and divides (∣) are GAPS, not heads.
Anything else is UNTRANSLATABLE, tagged by the first construct with no head.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# Dialect-agnostic bracket scanning
# --------------------------------------------------------------------------

_OPEN = "([{⟨"
_CLOSE = ")]}⟩"


def strip_comments(text: str) -> str:
    """Remove Lean `/- ... -/` (nesting) block comments and `-- ...` lines."""
    out: list[str] = []
    i, n, depth = 0, len(text), 0
    while i < n:
        two = text[i : i + 2]
        if two == "/-":
            depth += 1
            i += 2
            continue
        if two == "-/" and depth > 0:
            depth -= 1
            i += 2
            continue
        if depth > 0:
            i += 1
            continue
        if two == "--":
            j = text.find("\n", i)
            if j == -1:
                break
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def take_until_top_level(s: str, token: str) -> str | None:
    """Prefix of `s` up to the first depth-0 occurrence of `token`."""
    depth = 0
    i, n, tlen = 0, len(s), len(token)
    while i < n:
        c = s[i]
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0 and s[i : i + tlen] == token:
            return s[:i]
        i += 1
    return None


def first_top_level_colon(s: str) -> int:
    """Index of the first depth-0 `:` (not `:=`), or -1."""
    depth = 0
    for i, c in enumerate(s):
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0 and c == ":" and s[i : i + 2] != ":=":
            return i
    return -1


def top_level_groups(s: str) -> list[tuple[str, str]]:
    """Top-level bracketed binder groups: (opening_bracket, inner_text)."""
    groups: list[tuple[str, str]] = []
    depth = 0
    start = -1
    opener = ""
    for i, c in enumerate(s):
        if c in _OPEN:
            if depth == 0:
                start = i + 1
                opener = c
            depth += 1
        elif c in _CLOSE:
            depth -= 1
            if depth == 0 and start >= 0:
                groups.append((opener, s[start:i]))
                start = -1
    return groups


# --------------------------------------------------------------------------
# Binder classification
# --------------------------------------------------------------------------

# Numeric leaf types (Lean 3 + Lean 4 spellings). nnreal/NNReal (ℝ≥0) and
# ℕ+/PNat are numeric: a positivity domain is a regularity condition on the
# leaf, not a construct the grammar lacks.
# Partitioned by CARRIER, because `/` and `-` are different operations over each:
# over a field (ℝ/ℚ) they are real division/subtraction (supported heads); over ℕ
# `/` is Nat.div (floor) and `-` is monus (truncated), and over ℤ `/` is Int.div
# (floor) -- operations the corpus has no head for, exactly like the sibling `%`.
_NAT_TYPES = {"ℕ", "nat", "Nat", "ℕ+", "pnat", "PNat"}
_INTZ_TYPES = {"ℤ", "int", "Int", "ℤ+"}
_FIELD_TYPES = {"ℝ", "ℚ", "real", "rat", "Real", "Rat", "nnreal", "NNReal", "ℝ≥0"}
_NUMERIC_TYPES = _NAT_TYPES | _INTZ_TYPES | _FIELD_TYPES
_PROP_CHARS = set("=<>≤≥≠∧∨¬↔∀∃∈∉")
# Value carriers the grammar has no leaf slot for, keyed to the reason.
_DOMAIN_REASONS = {
    "ℂ": "complex_number", "complex": "complex_number", "Complex": "complex_number",
}
_STRUCTURE_HEADS = {
    "equiv", "Equiv", "is_least", "IsLeast", "is_greatest", "IsGreatest",
    "finset", "Finset", "set", "Set", "multiset", "Multiset",
    "list", "List", "polynomial", "Polynomial", "matrix", "Matrix",
}


def domain_reason(typ: str) -> str | None:
    if typ in _DOMAIN_REASONS:
        return _DOMAIN_REASONS[typ]
    first = typ.split()[:1]
    if first and first[0].lower() == "zmod":  # `zmod N` / `ZMod N`
        return "modular_type_zmod"
    return None


def classify_binder(inner: str) -> tuple[list[str], str | None, bool, list[tuple[str, str]]]:
    """(value_var_names, hypothesis_prop_or_None, is_function_unknown,
    [(name, domain_reason)] for slots over an unsupported carrier)."""
    if ":" not in inner:
        return [], None, False, []
    names_part, type_part = inner.split(":", 1)
    names = names_part.split()
    typ = type_part.strip()
    typ_norm = typ.replace("->", "→")
    if typ in _NUMERIC_TYPES:
        return names, None, False, []
    dr = domain_reason(typ)
    if dr is not None:
        return [], None, False, [(n, dr) for n in names]
    # An arrow type with no Prop characters is a function/structure value -- an
    # unknown function (ℝ→ℝ, ℂ→ℂ, ℕ→NNReal, ℕ→ℕ→ℕ); its names are not slots.
    if "→" in typ_norm and not (set(typ_norm) & _PROP_CHARS - {"→"}):
        return [], None, True, []
    # A bundled-structure type (Equiv ℝ ℝ, IsLeast S u, Finset ℕ) with no Prop
    # characters also introduces an unknown value; treat as a function unknown so
    # the whole statement is (correctly) untranslatable.
    if not (set(typ) & _PROP_CHARS) and not typ[:1].isdigit():
        first = typ.split()[0] if typ.split() else ""
        if first in _STRUCTURE_HEADS:
            return [], None, True, []
    # otherwise the binder introduces a proof term of a Prop: the Prop is a hyp.
    return [], typ, False, []


def _value_carrier(inner: str) -> str | None:
    """'nat' | 'int' | 'field' for a numeric VALUE binder, else None."""
    if ":" not in inner:
        return None
    names_part, type_part = inner.split(":", 1)
    if not names_part.split():
        return None
    typ = type_part.strip()
    if typ in _NAT_TYPES:
        return "nat"
    if typ in _INTZ_TYPES:
        return "int"
    if typ in _FIELD_TYPES:
        return "field"
    return None


def parse_binders(binders_text: str) -> dict:
    value_vars: list[str] = []
    domain_vars: dict[str, str] = {}
    hyps: list[str] = []
    fn_unknown = False
    carriers: set[str] = set()
    for _bracket, inner in top_level_groups(binders_text):
        names, hyp, is_fn, dvars = classify_binder(inner)
        value_vars.extend(names)
        for nm, reason in dvars:
            domain_vars[nm] = reason
        if hyp is not None:
            hyps.append(" ".join(hyp.split()))
        fn_unknown = fn_unknown or is_fn
        c = _value_carrier(inner)
        if c:
            carriers.add(c)
    return {
        "value_vars": value_vars,
        "domain_vars": domain_vars,
        "hyps": hyps,
        "fn_unknown": fn_unknown,
        "has_nat_carrier": "nat" in carriers,
        "has_int_carrier": "int" in carriers,
        "has_field_carrier": "field" in carriers,
    }


def split_signature(rest: str, terminator: str = ":=") -> tuple[str, str] | None:
    """Given the text AFTER `theorem NAME`, return (binders_text, goal) by
    trimming at the depth-0 proof terminator and splitting at the goal colon."""
    sig = take_until_top_level(rest, terminator)
    if sig is None:
        return None
    ci = first_top_level_colon(sig)
    if ci < 0:
        return None
    binders_text = sig[:ci].strip()
    goal = " ".join(sig[ci + 1 :].split())
    return binders_text, goal


# --------------------------------------------------------------------------
# Classifier
# --------------------------------------------------------------------------

# Transcendental heads the corpus carries (verified against data/). Both Lean 3
# (real.sqrt) and Lean 4 (Real.sqrt, and bare under `open Real`).
_SUPPORTED_FUNCS = {
    "real.sqrt": "SQRT", "Real.sqrt": "SQRT",
    "real.log": "LOG", "Real.log": "LOG",
    "real.exp": "EXP", "Real.exp": "EXP",
    "nnreal.sqrt": "SQRT", "NNReal.sqrt": "SQRT",
    "sqrt": "SQRT", "log": "LOG", "exp": "EXP",
}
_ALLOWED_CONSTS = {"π", "real.pi", "Real.pi", "pi"}

# Relations that make a goal a statement node. `∣` (divides) is kept here so a
# `12 ∣ n` goal counts as HAVING a relation and is then rejected by the
# divides_no_head blocker with the correct label (not "no_relation").
_RELATIONS = ["=", "≠", "<", "≤", ">", "≥", "≡", "∣", "↔"]

# Blocker constructs, checked in order; the first hit names why the grammar has
# no head for the statement. Each pattern carries Lean 3 + Lean 4 spellings.
_BLOCKERS: list[tuple[str, re.Pattern]] = [
    ("big_operator", re.compile(r"∑|∏|[Ff]inset\.sum|[Ff]inset\.prod")),
    ("integral", re.compile(r"∫")),
    # modulo and divides have NO head in data/*/nodes.json (the only MOD there is
    # morphology's linguistic modifier; there is no divides head): GAPS.
    ("modulo_no_head", re.compile(r"%|\[ZMOD|\[MOD|\b[Mm]odeq\b|\b[Nn]at\.mod\b|\b[Ii]nt\.mod\b")),
    ("divides_no_head", re.compile(r"∣|\bdvd\b|\b[Nn]at\.dvd\b")),
    # a fractional exponent `^(1/3)` is not a head: the corpus carries integer POW
    # and an explicit SQRT head, not general rational powers -- and over ℕ the
    # exponent `1/3` is Nat.div = 0 (the classic `x^(1/3)` = x^0 trap) regardless.
    ("fractional_exponent", re.compile(r"\^\s*\([^)]*/")),
    ("set_or_finset", re.compile(r"[Ff]inset|∈|∉|⊆|⊂|\.card\b|(?<![A-Za-z])[Ss]et(?![A-Za-z])|Set\.")),
    ("existential_quantifier", re.compile(r"∃")),
    ("universal_quantifier", re.compile(r"∀")),
    # a comma surviving big-operator / quantifier / set screening is a pair /
    # tuple / list constructor (the `(a,b,…)` head, which the grammar lacks).
    ("tuple_or_structure", re.compile(r",")),
    ("modular_type_zmod", re.compile(r"[Zz][Mm]od")),
    ("complex_number", re.compile(r"ℂ|complex|Complex")),
    ("primality", re.compile(r"\b[Nn]at\.[Pp]rime\b|\b[Pp]rime\b|[Cc]oprime")),
    ("gcd_lcm", re.compile(r"\b[Gg]cd\b|\b[Ll]cm\b|[Nn]at\.gcd|[Nn]at\.lcm")),
    ("binomial_choose", re.compile(r"\b[Nn]at\.choose\b|\b[Cc]hoose\b|\b[Nn]at\.factorial\b")),
    ("factorial", re.compile(r"!")),
    ("floor_ceil", re.compile(r"⌊|⌋|⌈|⌉|\b[Ff]loor\b|\b[Cc]eil\b|\b[Nn]at\.floor\b|\bInt\.floor\b")),
    ("digit_expansion", re.compile(r"[Nn]at\.digits|[Nn]at\.of_digits")),
    ("rational_component", re.compile(r"\.denom\b|\.num\b")),
    # absolute value / norm: ASCII |·|, mathlib norm bars ∥·∥ / ‖·‖, and words.
    ("absolute_value", re.compile(r"\babs\b|\bnorm\b|lvert|lVert|\||∥|‖|⟪|⟫")),
    ("min_max", re.compile(r"\b[Mm]in\b|\b[Mm]ax\b")),
    # trig has no head; under `open Real` the functions appear bare (sin, cos …).
    ("trig", re.compile(r"[Rr]eal\.(?:cos|sin|tan|arcsin|arccos|arctan)|\b(?:sin|cos|tan|cot|sec|csc|arcsin|arccos|arctan)\b")),
    ("polynomial", re.compile(r"[Pp]olynomial")),
    ("matrix", re.compile(r"[Mm]atrix")),
    ("derivative", re.compile(r"deriv|∂")),
]

# Identifier tokens: dotted names (real.sqrt, Nat.succ) and simple names. Lean
# admits Greek letters and subscripts in identifiers (α, β, ω, x₀), so the class
# must include them -- otherwise a Greek-named ℂ/zmod variable escapes the domain
# check and its statement is wrongly counted covered.
# ASCII + Greek/Coptic (U+0370-03FF: α β ω π …) + Greek Extended (U+1F00-1FFF).
_ID_START = "A-Za-z_Ͱ-Ͽἀ-῿"
_ID_CONT = _ID_START + "0-9₀-ₜ'"  # + digits, subscripts, prime
_IDENT_RE = re.compile(
    "[" + _ID_START + "][" + _ID_CONT + "]*"
    "(?:\\.[" + _ID_START + "][" + _ID_CONT + "]*)*"
)
_IGNORE_IDENTS = {"begin", "end", "by", "have", "show", "from"}


def _blocker(text: str) -> str | None:
    for reason, pat in _BLOCKERS:
        if pat.search(text):
            return reason
    return None


def _unsupported_symbol(expr: str, value_vars: set[str]) -> str | None:
    for tok in _IDENT_RE.findall(expr):
        if tok in value_vars or tok in _SUPPORTED_FUNCS or tok in _ALLOWED_CONSTS:
            continue
        if tok in _IGNORE_IDENTS:
            continue
        return tok
    return None


def _has_relation(goal: str) -> bool:
    return any(r in goal for r in _RELATIONS)


# A statement whose arithmetic is (even partly) over a field: a field-typed
# value var, an explicit coercion ↑, a ℝ/ℚ ascription, a Real/Rat namespace call,
# or a decimal literal. Without any such signal, `/` and `-` over ℕ/ℤ carriers
# are the floor-division / monus GAPS, not the real operations.
_FIELD_SIGNAL_RE = re.compile(
    r"↑|:\s*ℝ|:\s*ℚ|:\s*NNReal|:\s*ℝ≥0|\bReal\.|\bNNReal\b|\bRat\.|[0-9]\.[0-9]"
)


def _carrier_gap(text: str, has_nat: bool, has_int: bool, field_signal: bool) -> str | None:
    if field_signal:
        return None
    # `/` (Nat.div/Int.div, floor) and `⁻¹` (Nat.inv, = 0 for x>1) are the same
    # non-field division family; neither has a head over ℕ/ℤ.
    if (has_nat or has_int) and ("/" in text or "⁻¹" in text):
        return "integer_division_no_head"
    if has_nat and not has_int and "-" in text:
        return "nat_monus_no_head"  # truncated subtraction over ℕ
    return None


def classify(stmt: dict) -> dict:
    """Classify one statement: goal-only and full-statement coverage + reason.

    `stmt` needs: name, goal, value_vars, hyps, fn_unknown, domain_vars, and any
    grouping key the caller carries through (passed unmodified into the result)."""
    goal = stmt["goal"]
    value_vars = set(stmt["value_vars"])
    domain_vars = stmt.get("domain_vars", {})
    goal_idents = set(_IDENT_RE.findall(goal))

    has_nat = stmt.get("has_nat_carrier", False)
    has_int = stmt.get("has_int_carrier", False)
    has_field = stmt.get("has_field_carrier", False)
    all_text = goal + " || " + " || ".join(stmt["hyps"])
    field_signal = has_field or bool(_FIELD_SIGNAL_RE.search(all_text))

    # ---- goal-only ----
    goal_reason: str | None = None
    if not _has_relation(goal):
        goal_reason = "no_relation_in_goal"
    if goal_reason is None:
        hit = sorted(domain_vars[v] for v in (set(domain_vars) & goal_idents))
        if hit:
            goal_reason = hit[0]
    if goal_reason is None:
        goal_reason = _blocker(goal)
    if goal_reason is None:
        goal_reason = _carrier_gap(goal, has_nat, has_int, field_signal)
    if goal_reason is None:
        bad = _unsupported_symbol(goal, value_vars)
        if bad is not None:
            goal_reason = f"unsupported_symbol:{bad}"
    goal_ok = goal_reason is None

    # ---- full statement (goal AND every hypothesis must reduce) ----
    full_reason = goal_reason
    if goal_ok:
        if stmt["fn_unknown"]:
            full_reason = "function_unknown_binder"
        else:
            for hyp in stmt["hyps"]:
                r = (
                    _blocker(hyp)
                    or _carrier_gap(hyp, has_nat, has_int, field_signal)
                    or (
                        (lambda b: f"unsupported_symbol:{b}" if b else None)(
                            _unsupported_symbol(hyp, value_vars)
                        )
                    )
                )
                if r is not None:
                    full_reason = f"hyp:{r}"
                    break
    full_ok = full_reason is None

    out: dict = {"name": stmt["name"]}
    if "split" in stmt:  # keep the miniF2F key order: name, split, goal_ok, ...
        out["split"] = stmt["split"]
    out["goal_ok"] = goal_ok
    out["goal_reason"] = goal_reason
    out["full_ok"] = full_ok
    out["full_reason"] = full_reason
    return out


# --------------------------------------------------------------------------
# Shared reporting helpers
# --------------------------------------------------------------------------

def tally(reasons: list[str | None]) -> dict:
    counts: dict[str, int] = {}
    for r in reasons:
        if r is None:
            continue
        counts[r] = counts.get(r, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def pct(num: int, den: int) -> float:
    return round(100.0 * num / den, 1) if den else 0.0


def serialize(doc: dict) -> bytes:
    return (
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def write_json(path: Path, doc: dict) -> None:
    # write_bytes, not write_text: on Windows write_text translates \n -> \r\n,
    # which breaks byte-for-byte regeneration. .gitattributes pins these LF.
    path.write_bytes(serialize(doc))


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()
