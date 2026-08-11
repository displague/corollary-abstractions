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

v0.10 item 1 (cont.) adds the RELATIONAL/PREDICATE head family:

* A goal need not carry an infix relation to be a proposition. A bare
  application of a supported predicate head (EVEN/ODD/PRIME/IRRATIONAL, carried
  by data/number_theory), a prop constant (TRUTH/FALSITY, carried by
  data/logic), or a top-level ¬/∧/∨/→ composition of such atoms is prop-shaped.
  The predicate's argument must still pass every blocker/carrier/symbol check —
  a supported predicate over an unsupported inner term is NOT covered — and the
  application is arity-checked (the 2-arg `log b x` lesson: `Even x y` is a
  malformed extra-arg application, not the parity head).
* `let x := e` / `let x : T := e` bindings prefixing a goal are definitional
  equalities, which the corpus expresses as `=` definition nodes. The parser
  previously truncated the statement at the let's `:=`, mislabeling 87% of
  Goedel-Pset's `no_relation_in_goal` bucket. Bindings are now split into
  `goal_lets` equations (`x = e`, `x = (e : T)`); each must reduce exactly like
  a goal conjunct, and the body is classified on its own shape. An untyped
  numeral binding contributes a ℕ carrier (Lean's numeral default), a typed one
  its declared carrier, so carrier-honesty (`/` `-` over ℕ/ℤ) is preserved.
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


_THEOREM_RE = re.compile(r"(?m)^theorem[ \t]+(\S+)")

# `let` keyword boundary: not preceded by an identifier char or `.`, not
# followed by one (identifier continuation includes digits, subscripts, primes).
_LET_BOUND_CHARS = r"\w'₀-ₜᵢ-ᵪ"
_LET_KW_RE = re.compile(r"^\s*let(?![" + _LET_BOUND_CHARS + r"])")
_LET_AT_RE = re.compile(r"let(?![" + _LET_BOUND_CHARS + r"])")


def _find_statement_end(s: str) -> int:
    """Index of the depth-0 `:=` that terminates a theorem STATEMENT.

    A goal may legally contain depth-0 `:=` tokens of its own: Lean 4 `let`
    bindings (`let x := e; body`). The old scan stopped at the FIRST depth-0
    `:=`, truncating every let-goal to the text `let x` — which mislabeled 87%
    of Goedel-Pset's no_relation_in_goal bucket. Each depth-0 `let` keyword
    claims the next depth-0 `:=` as its binder; the first UNCLAIMED depth-0
    `:=` is the proof terminator."""
    depth = 0
    pending = 0
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0:
            if s.startswith(":=", i):
                if pending:
                    pending -= 1
                    i += 2
                    continue
                return i
            if s.startswith("let", i):
                prev_ok = i == 0 or not re.match(
                    "[" + _LET_BOUND_CHARS + ".]", s[i - 1]
                )
                if prev_ok and _LET_AT_RE.match(s, i):
                    pending += 1
                    i += 3
                    continue
        i += 1
    return -1


def _depth0_find_any(s: str, needles: str) -> int:
    depth = 0
    for i, c in enumerate(s):
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0 and c in needles:
            return i
    return -1


# An RHS line that is empty or ends dangling on a binary operator / opener
# continues on the next line (Lean's layout rule, approximated).
_DANGLING = set("+-*/^(,=<>≤≥∧∨→↔⟨:")


def _split_lets(goal_raw: str) -> tuple[list[tuple[str, str | None, str]], str]:
    """Split leading `let NAME [: TYPE] := RHS` bindings off a RAW (newline-
    preserving) goal text. RHS extends to the first depth-0 `;` or newline (Lean
    layout), continuing past newlines while it is empty or dangles on an open
    operator (`:=` at end of line, `... +` continuation). The remainder is the
    goal body. Returns ([(name, type, rhs)], body)."""
    lets: list[tuple[str, str | None, str]] = []
    s = goal_raw
    while True:
        m = _LET_KW_RE.match(s)
        if not m:
            break
        rest = s[m.end() :]
        j = _depth0_seek(rest, ":=")
        if j < 0:
            break
        head = rest[:j]
        after = rest[j + 2 :]
        rhs_parts: list[str] = []
        while True:
            k = _depth0_find_any(after, ";\n")
            if k < 0:
                rhs_parts.append(after)
                after = ""
                break
            rhs_parts.append(after[:k])
            sep, after = after[k], after[k + 1 :]
            joined = " ".join(" ".join(rhs_parts).split())
            if sep == ";" or (joined and joined[-1] not in _DANGLING):
                break
        rhs = " ".join(" ".join(rhs_parts).split())
        s = after
        ci = first_top_level_colon(head)
        if ci >= 0:
            name = " ".join(head[:ci].split())
            typ: str | None = " ".join(head[ci + 1 :].split()) or None
        else:
            name, typ = " ".join(head.split()), None
        lets.append((name, typ, rhs))
    return lets, s


def _depth0_seek(s: str, token: str) -> int:
    depth = 0
    i, n, tlen = 0, len(s), len(token)
    while i < n:
        c = s[i]
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0 and s[i : i + tlen] == token:
            return i
        i += 1
    return -1


_INT_NUMERAL_RE = re.compile(r"-?\s*\d+")


def apply_goal_lets(
    b: dict, lets: list[tuple[str, str | None, str]]
) -> list[str] | None:
    """Fold parsed `let` bindings into a parse_binders dict IN PLACE and return
    the binding-equation strings (`x = e`, `x = (e : T)`), or None if a binding
    is malformed (empty rhs) and the statement should count as unparsed.

    Each simple-named binding registers a value var; a typed binding contributes
    its declared carrier, and an untyped bare-numeral binding the ℕ carrier
    (ℤ if negated) that Lean's numeral elaboration gives it — so `/` and `-`
    over let-bound integers stay the floor-division/monus gaps (carrier-honesty)."""
    goal_lets: list[str] = []
    for nm, typ, rhs in lets:
        if not rhs:
            return None  # malformed binding; refuse rather than misparse
        goal_lets.append(f"{nm} = ({rhs} : {typ})" if typ else f"{nm} = {rhs}")
        if typ is not None and ("→" in typ or "->" in typ):
            # `let f : ℝ → ℝ := (· * 60)` binds an unknown FUNCTION, exactly
            # like a function-typed binder: its name is not a value slot, and
            # the full statement is honestly untranslatable.
            b["fn_unknown"] = True
            continue
        if _IDENT_RE.fullmatch(nm):
            b["value_vars"].append(nm)
            if typ is not None:
                ts = typ.strip()
                if ts in _NAT_TYPES:
                    b["has_nat_carrier"] = True
                elif ts in _INTZ_TYPES:
                    b["has_int_carrier"] = True
                elif ts in _FIELD_TYPES:
                    b["has_field_carrier"] = True
            elif _INT_NUMERAL_RE.fullmatch(rhs):
                if rhs.lstrip().startswith("-"):
                    b["has_int_carrier"] = True
                else:
                    b["has_nat_carrier"] = True
    return goal_lets


def parse_lean4_theorem(name: str, text: str) -> dict | None:
    """Parse a Lean 4 `theorem` (statement part only) from raw source text that
    may carry an `import`/`open` preamble and comments. Returns the statement
    dict `classify` consumes, or None if no parseable theorem/goal is found."""
    t = strip_comments(text)
    m = _THEOREM_RE.search(t)
    if not m:
        return None
    sig = split_signature(t[m.end() :], ":=")
    if sig is None:
        return None
    binders_text, goal, lets = sig
    if not goal:
        return None
    b = parse_binders(binders_text)
    goal_lets = apply_goal_lets(b, lets)
    if goal_lets is None:
        return None
    out = {"name": name, "goal": goal, **b}
    if goal_lets:
        out["goal_lets"] = goal_lets
    return out


def split_signature(
    rest: str, terminator: str = ":="
) -> tuple[str, str, list[tuple[str, str | None, str]]] | None:
    """Given the text AFTER `theorem NAME`, return (binders_text, goal, lets) by
    trimming at the depth-0 proof terminator (let-aware: a `let x := e` binding's
    `:=` does not terminate the statement) and splitting at the goal colon.
    `lets` is the list of (name, type-or-None, rhs) goal-prefix bindings."""
    end = _find_statement_end(rest)
    if end < 0:
        return None
    sig = rest[:end]
    ci = first_top_level_colon(sig)
    if ci < 0:
        return None
    binders_text = sig[:ci].strip()
    lets, body = _split_lets(sig[ci + 1 :])
    goal = " ".join(body.split())
    return binders_text, goal, lets


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
    # v0.10 item 1: SIN/COS/TAN are now corpus heads (data/trigonometry). Forward
    # trig only; inverse and reciprocal trig remain gaps (see the trig blocker).
    "real.sin": "SIN", "Real.sin": "SIN", "sin": "SIN",
    "real.cos": "COS", "Real.cos": "COS", "cos": "COS",
    "real.tan": "TAN", "Real.tan": "TAN", "tan": "TAN",
}
_ALLOWED_CONSTS = {"π", "real.pi", "Real.pi", "pi", "ℯ"}

# v0.10 item 1 (cont.): predicate heads the corpus carries (data/number_theory).
# Both Lean 3 (nat.prime, even) and Lean 4 (Nat.Prime, Even; bare Prime under
# `open Nat`) spellings. All arity 1 — enforced structurally in the prop-shape
# gate and by the predicate_extra_arg blocker (the 2-arg `log b x` lesson).
# Coprime (arity 2), Squarefree, Function.Injective/Surjective, Monotone etc.
# have NO corpus head and stay gaps.
_SUPPORTED_PREDICATES = {
    "even": "EVEN", "Even": "EVEN",
    "odd": "ODD", "Odd": "ODD",
    "nat.prime": "PRIME", "Nat.Prime": "PRIME",
    "prime": "PRIME", "Prime": "PRIME",
    "irrational": "IRRATIONAL", "Irrational": "IRRATIONAL",
}
# Prop constants carried by data/logic (TRUTH/FALSITY templates: identity laws,
# non-contradiction, ex falso). Lean 4 True/False, Lean 3 true/false. A bare
# `False` goal is the contradiction node IMPLIES(MEET(hyps), FALSITY).
_PROP_CONSTS = {"True": "TRUTH", "False": "FALSITY", "true": "TRUTH", "false": "FALSITY"}

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
    # a `[...]` surviving the modulo blocker (which owns `[MOD`/`[ZMOD`) is a list
    # literal or a function-iteration `f^[n]` (n-fold composition) -- no head.
    ("list_or_iteration", re.compile(r"\[")),
    # a fractional exponent `^(1/3)` is not a head: the corpus carries integer POW
    # and an explicit SQRT head, not general rational powers -- and over ℕ the
    # exponent `1/3` is Nat.div = 0 (the classic `x^(1/3)` = x^0 trap) regardless.
    ("fractional_exponent", re.compile(r"\^\s*\([^)]*/")),
    # bare two-argument `log b x` is a base-b logarithm (Nat.log / Real.logb),
    # which has no head -- unlike one-argument `log x` (= Real.log, supported) and
    # consistent with the classifier's existing rejection of `logb`/`Real.logb`.
    ("two_arg_log_no_head", re.compile(r"(?<![\w.])log\s+(?:\([^()]*\)|[\w.\d]+)\s+(?:\(|[\w.\d])")),
    # a supported predicate applied to a SECOND argument is not the corpus head
    # (EVEN/ODD/PRIME/IRRATIONAL are arity 1): `Even x y` is malformed, exactly
    # the arity-blindness the 2-arg log fix taught.
    ("predicate_extra_arg", re.compile(
        r"(?<![\w.])(?:[Nn]at\.[Pp]rime|[Ee]ven|[Oo]dd|[Pp]rime|[Ii]rrational)"
        r"\s+(?:\([^()]*\)|[\w.\d]+)\s+(?:\(|[\w.\d])")),
    ("set_or_finset", re.compile(r"[Ff]inset|∈|∉|⊆|⊂|\.card\b|ℵ|(?<![A-Za-z])[Ss]et(?![A-Za-z])|Set\.")),
    ("existential_quantifier", re.compile(r"∃")),
    ("universal_quantifier", re.compile(r"∀")),
    # a comma or an anonymous constructor ⟨…⟩ surviving big-operator / quantifier /
    # set screening is a pair / tuple / list constructor (no `(a,b,…)` head).
    ("tuple_or_structure", re.compile(r",|⟨|⟩")),
    # module/vector/product operators with no head: × (Prod / cross), • (SMul),
    # ⊗ (tensor), ⊕ (direct sum), ⊘. NOT ∘ (the corpus carries a COMPOSE head).
    ("vector_or_module_op", re.compile(r"×|•|⊗|⊕|⊘")),
    # anonymous functions and uninterpreted notation: Lean section dots
    # `(· * 60)`, lambda `fun x => e` / `λ x => e`, and custom infix glyphs
    # like `⋆`. The section dot and `⋆` are invisible to the identifier scan,
    # so without this blocker a `let`-bound lambda covered as a value — the
    # exact false-positive class the Goedel-Pset foreign-glyph audit caught
    # (6 offenders at 1.73M scale, all conversion lambdas or custom operators).
    ("uninterpreted_notation", re.compile(r"⋆|·|=>|(?<![\w.'])fun(?![\w.'])|λ")),
    ("modular_type_zmod", re.compile(r"[Zz][Mm]od")),
    ("complex_number", re.compile(r"ℂ|complex|Complex|ℐ|ℑ|ℜ|𝕀")),
    # primality itself became a head (PRIME, data/number_theory); coprimality is
    # a DIFFERENT, 2-ary predicate the corpus does not carry -- it keeps its own
    # precise label instead of vanishing into the old shared `primality` bucket.
    ("coprime_no_head", re.compile(r"[Cc]oprime")),
    ("gcd_lcm", re.compile(r"\b[Gg]cd\b|\b[Ll]cm\b|[Nn]at\.gcd|[Nn]at\.lcm")),
    ("binomial_choose", re.compile(r"\b[Nn]at\.choose\b|\b[Cc]hoose\b|\b[Nn]at\.factorial\b")),
    ("factorial", re.compile(r"!")),
    ("floor_ceil", re.compile(r"⌊|⌋|⌈|⌉|\b[Ff]loor\b|\b[Cc]eil\b|\b[Nn]at\.floor\b|\bInt\.floor\b")),
    ("digit_expansion", re.compile(r"[Nn]at\.digits|[Nn]at\.of_digits")),
    ("rational_component", re.compile(r"\.denom\b|\.num\b")),
    # absolute value / norm: ASCII |·|, mathlib norm bars ∥·∥ / ‖·‖, and words.
    ("absolute_value", re.compile(r"\babs\b|\bnorm\b|lvert|lVert|\||∥|‖|⟪|⟫")),
    ("min_max", re.compile(r"\b[Mm]in\b|\b[Mm]ax\b|⊓|⊔|⨅|⨆")),
    ("metavar_or_string", re.compile(r'"|\?')),
    # forward sin/cos/tan are now supported heads (data/trigonometry); the trig
    # GAP is now only inverse, reciprocal, and hyperbolic trig, which have no head.
    # Inverse trig appears BOTH as words (arctan) and as superscript (tan⁻¹) -- the
    # latter must be caught here, because _IDENT_RE drops the ⁻¹ and `Real.tan⁻¹`
    # would otherwise read as the forward TAN head.
    ("trig", re.compile(r"(?:sin|cos|tan|cot|sec|csc)⁻¹|[Rr]eal\.(?:arcsin|arccos|arctan|sinh|cosh|tanh)|\b(?:cot|sec|csc|arcsin|arccos|arctan|sinh|cosh|tanh)\b")),
    ("polynomial", re.compile(r"[Pp]olynomial")),
    ("matrix", re.compile(r"[Mm]atrix")),
    ("derivative", re.compile(r"deriv|∂")),
]

# Identifier tokens: dotted names (real.sqrt, Nat.succ) and simple names. Lean
# admits Greek letters and subscripts in identifiers (α, β, ω, x₀), so the class
# must include them -- otherwise a Greek-named ℂ/zmod variable escapes the domain
# check and its statement is wrongly counted covered.
# ASCII + Greek/Coptic (U+0370-03FF: α β ω π …) + Greek Extended (U+1F00-1FFF)
# + Cyrillic (U+0400-04FF: Goedel-Pset uses Cyrillic var names) + ℓ (U+2113).
# NB: deliberately NOT the ℝ/ℕ/ℤ/ℚ/ℂ type symbols (letterlike U+2100-214F), which
# stay non-identifier glyphs handled by the carrier/domain logic.
_ID_START = "A-Za-z_Ͱ-Ͽἀ-῿Ѐ-ӿℓ"
# continuation adds digits, subscripts (U+2080-209C), phonetic subscript
# modifiers (U+1D62-1D6A: ᵢ ᵣ ᵤ …, used in var names like hᵣ), and prime.
_ID_CONT = _ID_START + "0-9₀-ₜᵢ-ᵪ'"
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
        if tok in _SUPPORTED_PREDICATES or tok in _PROP_CONSTS:
            continue
        if tok in _IGNORE_IDENTS:
            continue
        return tok
    return None


def _has_relation(goal: str) -> bool:
    return any(r in goal for r in _RELATIONS)


# --------------------------------------------------------------------------
# Prop-shape gate: what counts as a proposition-shaped goal
# --------------------------------------------------------------------------

_SINGLE_TOKEN_RE = re.compile(r"↑?[\w'ℯπ₀-ₜᵢ-ᵪ]+(?:\.[\w'₀-ₜᵢ-ᵪ]+)*")


def _spans_whole(s: str) -> bool:
    """True iff s is one balanced (...) group covering the entire string."""
    if not (s.startswith("(") and s.endswith(")")):
        return False
    depth = 0
    for i, c in enumerate(s):
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
            if depth == 0:
                return i == len(s) - 1
    return False


def _bare_predicate_app(atom: str) -> bool:
    """A supported predicate applied to exactly ONE argument atom (arity-aware:
    the argument must be a single balanced group or a single token; a second
    argument or a trailing operator is NOT the corpus head)."""
    m = _IDENT_RE.match(atom)
    if not m or m.group(0) not in _SUPPORTED_PREDICATES:
        return False
    rest = atom[m.end() :].strip()
    if not rest:
        return False  # unapplied predicate is a function value, not a proposition
    if _spans_whole(rest):
        return True
    return bool(_SINGLE_TOKEN_RE.fullmatch(rest))


def _split_top_level(s: str, seps: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    for i, c in enumerate(s):
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0 and c in seps:
            parts.append(s[start:i])
            start = i + 1
    parts.append(s[start:])
    return parts


def _prop_atom_shaped(atom: str) -> bool:
    a = atom.strip()
    while True:
        if a.startswith("¬"):
            a = a[1:].lstrip()
            continue
        if _spans_whole(a):
            a = a[1:-1].strip()
            continue
        break
    if not a:
        return False
    if _has_relation(a):
        return True
    parts = _split_top_level(a, "→∧∨")
    if len(parts) > 1:
        return all(_prop_atom_shaped(p) for p in parts)
    if a in _PROP_CONSTS:
        return True
    return _bare_predicate_app(a)


def _prop_shaped(goal: str) -> bool:
    """A goal is proposition-shaped if it carries an infix relation, OR is a
    top-level ¬/∧/∨/→ composition whose every atom is a relation, a supported
    bare predicate application, or a prop constant. MEET/JOIN/NEG/IMPLIES are
    corpus heads, so the composition itself is in-grammar; each atom's INNER
    term is still subject to every blocker/carrier/symbol check downstream."""
    if _has_relation(goal):
        return True
    return _prop_atom_shaped(goal)


# Integer predicates over a field carrier are NOT the corpus head: data/
# number_theory's EVEN/ODD/PRIME are integer parity/primality (over ℝ, mathlib's
# `Even x` is trivially true for every real -- a different, uncarried reading).
# Conservative: if the statement declares a field-typed value var and an integer
# predicate's text touches any variable, the carrier cannot be attributed.
_INT_PRED_RE = re.compile(
    r"(?<![\w.])(?:[Ee]ven|[Oo]dd|(?:[Nn]at\.)?[Pp]rime)(?![\w.'])"
)


def _int_pred_field_gap(text: str, has_field: bool, value_vars: set[str]) -> str | None:
    if not has_field or not _INT_PRED_RE.search(text):
        return None
    if any(tok in value_vars for tok in _IDENT_RE.findall(text)):
        return "integer_predicate_field_carrier"
    return None


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
    lets = stmt.get("goal_lets", [])
    value_vars = set(stmt["value_vars"])
    domain_vars = stmt.get("domain_vars", {})
    # the let bindings are PART of the goal proposition (a let-goal is the
    # definitional equations plus the body), so they join every goal-side check.
    goal_segments = [*lets, goal]
    goal_idents: set[str] = set()
    for seg in goal_segments:
        goal_idents |= set(_IDENT_RE.findall(seg))

    has_nat = stmt.get("has_nat_carrier", False)
    has_int = stmt.get("has_int_carrier", False)
    has_field = stmt.get("has_field_carrier", False)
    all_text = " || ".join(goal_segments + stmt["hyps"])
    field_signal = has_field or bool(_FIELD_SIGNAL_RE.search(all_text))

    # ---- goal-only ----
    goal_reason: str | None = None
    if not _prop_shaped(goal):
        # prefer the precise construct label when one exists (a relationless
        # `Nat.Coprime m n` is the coprime gap, a relationless `∑`-term the
        # big-operator gap); `no_relation_in_goal` is only the residue that
        # no blocker can name better.
        goal_reason = _blocker(goal) or "no_relation_in_goal"
    if goal_reason is None:
        hit = sorted(domain_vars[v] for v in (set(domain_vars) & goal_idents))
        if hit:
            goal_reason = hit[0]
    if goal_reason is None:
        for seg in goal_segments:
            goal_reason = (
                _blocker(seg)
                or _carrier_gap(seg, has_nat, has_int, field_signal)
                or _int_pred_field_gap(seg, has_field, value_vars)
            )
            if goal_reason is None:
                bad = _unsupported_symbol(seg, value_vars)
                if bad is not None:
                    goal_reason = f"unsupported_symbol:{bad}"
            if goal_reason is not None:
                break
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
                    or _int_pred_field_gap(hyp, has_field, value_vars)
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
