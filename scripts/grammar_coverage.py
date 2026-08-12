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
  numeral binding contributes a ℕ carrier (Lean's numeral default) and an
  integer-typed one its declared carrier, so carrier-honesty (`/` `-` over
  ℕ/ℤ) is preserved; a field-typed binding signals only its OWN segment —
  the field signal is segment-local throughout (review-caught: computed
  statement-wide it shielded ℕ floor-division/monus in sibling segments).

The v0.10 quantifier slice adds the FORALL/EXISTS binder heads (carried by
data/logic's quantification laws and data/number_theory's parity-witness
definitions): a quantifier PREFIX on the goal body or a hypothesis — chains,
¬-wrappers, bounded binders, binder groups, ∃! via its ExistsUnique
expansion — is extracted before any other check; bound names become value
slots and binder carriers register for that segment only (untyped binders
default to ℕ, the untyped-`let` rule; shadowing is refused). Any ∀/∃ that
survives extraction is in a non-prefix position and keeps the precise
`quantifier_embedded` label; non-numeric binder domains keep their own labels
(function, structure, ℂ/zmod, shadowed, malformed).

The v0.10 embedded-quantifier slice adds the atom-tree walk: where the flat
verdict on a goal body or hypothesis would be `quantifier_embedded`, the
segment is re-judged as a depth-0 connective tree (∧/∨/→/↔/¬ — all carried
heads) whose leaves are relations or quantified subformulas, each leaf
checked by the existing machinery (prefix extraction per subformula, binder
names and carriers per subformula, leaf-local field signals, every blocker).
Term-position quantifiers (set-builders, Prop-valued equality operands,
function arguments), quantified `let` equations, scope-overlapping shadowing,
and past-cap nesting keep precise refusals.
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

    Each simple-named binding registers a value var; an INTEGER-typed binding
    contributes its declared carrier, and an untyped bare-numeral binding the ℕ
    carrier (ℤ if negated) that Lean's numeral elaboration gives it — so `/`
    and `-` over let-bound integers stay the floor-division/monus gaps.
    A FIELD-typed binding deliberately does not set the statement-wide field
    carrier (its ascription is a segment-local signal only; see the comment
    below — the review-caught shielding over-count)."""
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
            # Carrier flags from lets are ASYMMETRIC on purpose. An integer
            # carrier only ever CREATES gaps (`/` becomes Nat.div, `-` monus),
            # so ℕ/ℤ-typed and untyped-numeral bindings register statement-
            # wide — the safe direction. A field-typed binding must NOT set
            # the statement-wide field carrier: that would let one `: ℚ`
            # binding shield Nat.div/monus in a SIBLING ℕ binding (the
            # review's evidence row Goedel-Pset-1082706, where the shielded
            # `s / n` over ℕ is 0 and the claim is false). Its `(rhs : ℚ)`
            # equation string already carries the SEGMENT-local signal.
            if typ is not None:
                ts = typ.strip()
                if ts in _NAT_TYPES:
                    b["has_nat_carrier"] = True
                elif ts in _INTZ_TYPES:
                    b["has_int_carrier"] = True
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
    sig = split_signature(t[m.end() :])
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
    rest: str,
) -> tuple[str, str, list[tuple[str, str | None, str]]] | None:
    """Given the text AFTER `theorem NAME`, return (binders_text, goal, lets) by
    trimming at the depth-0 `:=` proof terminator (let-aware: a `let x := e`
    binding's `:=` does not terminate the statement) and splitting at the goal
    colon. `lets` is the list of (name, type-or-None, rhs) goal-prefix bindings.
    (The old `terminator` parameter is gone: `_find_statement_end` is
    necessarily `:=`-specific because the let-claiming rule is.)"""
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
    # v0.10: a quantifier PREFIX is extracted before the blocker scan ever
    # runs (FORALL/EXISTS are corpus heads now — data/logic quantification,
    # data/number_theory witness definitions). Any ∀/∃ that still reaches
    # this scan is EMBEDDED: inside a connective/iff composition, nested in a
    # non-prefix position of a body, or inside a let-binding equation. Since
    # the v0.10 embedded-quantifier slice, a goal-body or hypothesis segment
    # with this verdict is re-judged by the atom-tree walk (`_tree_walk`);
    # the label survives only for what the walk itself refuses (term
    # position, quantified lets, past-cap nesting).
    ("quantifier_embedded", re.compile(r"[∀∃]")),
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
    # ... plus the star-family custom operators (★ U+2605, ∗ U+2217, ⊛): the
    # quantifier slice's 1.73M audit caught a covered `2 ★ (2 ★ x)` — same
    # class as `⋆`, glyphs invisible to the identifier scan.
    ("uninterpreted_notation", re.compile(r"⋆|★|∗|⊛|·|=>|(?<![\w.'])fun(?![\w.'])|λ")),
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


# --------------------------------------------------------------------------
# Quantifier-prefix extraction (v0.10: the FORALL/EXISTS binder heads)
#
# A goal or hypothesis of the form `∀ x : T, body` / `∃ x : T, body`
# (chains, ¬-wrappers, bounded binders, binder groups, ∃!) is a quantified
# proposition whose heads the corpus now carries: data/logic's quantification
# topic defines FORALL/EXISTS (instantiation, generalization, the De Morgan
# duals that license the ¬-wrapper, the ∃!-expansion that licenses the
# ExistsUnique desugar), and data/number_theory carries the existential
# parity-witness definitions. The extraction rules, registered in the design
# checkpoint BEFORE this code existed:
#
# * Binding is segment-local: bound names join the value slots for THEIR
#   segment only, and their carriers register for that segment only — a
#   `∀ x : ℝ` in the goal must not shield Nat-division in a hypothesis, and a
#   `∀ n : ℕ` hypothesis must not manufacture gaps in the goal. Shadowing an
#   outer variable is refused outright (`quantifier_shadowed_binder`): the
#   per-statement carrier flags cannot express two carriers for one name.
# * Untyped and relation-bounded binders default to the ℕ carrier — Lean's
#   own elaboration defaults them absent a field signal, so `∀ x > 0,
#   x + 1/x ≥ 2` IS a ℕ statement as formalized and `1/x` stays the
#   Nat.div gap; a segment-local field signal lifts the default, because the
#   same signal is what pins Lean's unification to ℝ/ℚ. (The untyped-`let`
#   numeral rule, applied to binders.)
# * Bounded binders desugar the way Lean elaborates them: the binder
#   predicate joins the body as one more checked conjunct. Prop-typed
#   binders `(hx : x > 0)` contribute their type the same way; their names
#   are proof terms, not value slots.
# * `∃!` desugars to its ExistsUnique expansion (EXISTS/MEET/FORALL/IMPLIES
#   and an equation between two bound slots — all carried heads, stated by
#   logic.quantification.unique_existence_expansion): checking-wise the
#   uniqueness clause re-checks the same body, so ∃! rides the ∃ path.
# * Quantification over functions, sets/structures, ℂ/zmod domains, and
#   other non-numeric types keeps precise labels; a type that is none of
#   those is treated as a Prop binder conjunct (the classify_binder
#   fallback), whose head then faces the ordinary symbol check.
# --------------------------------------------------------------------------

_QUANT_CHARS = "∀∃"
_REL_BOUND_CHARS = "<>≤≥≠"


def _outside_groups(s: str) -> str:
    """Characters of `s` at bracket depth 0, brackets themselves excluded."""
    out: list[str] = []
    depth = 0
    for c in s:
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0:
            out.append(c)
    return "".join(out)


def _quant_binder_section(
    sec: str, names: list[str], bounds: list[str], carriers: set[str]
) -> str | None:
    """Classify ONE binder section (the text between ∀/∃ and its comma),
    appending bound value names / bound-predicate conjuncts / carriers.
    Returns a precise gap label, or None when the section is supported."""
    sec = sec.strip()
    if not sec:
        return "quantifier_malformed"
    # strict-implicit binder brackets `⦃A B C : ℕ⦄` are not in the global
    # bracket alphabet; unwrap them and read the inner binder as usual.
    if sec.startswith("⦃") and sec.endswith("⦄"):
        return _quant_binder_section(sec[1:-1], names, bounds, carriers)
    groups = top_level_groups(sec)
    # A LIST of binder groups only when nothing but whitespace sits outside
    # them — `(x : ℝ) (hx : x > 0)`. A section with groups AND residue is an
    # ordinary binder whose type or predicate merely contains parentheses
    # (`x ∈ Set.Icc (-3 : ℝ) (-1)`, `q : ℕ → (ℝ × ℝ)`) and falls through to
    # the analysis below. (The first cut labeled those `quantifier_malformed`
    # — 10,691 rows at 1.73M scale — which the step-1 remainder inspection
    # caught before the numbers landed.)
    if groups and not _outside_groups(sec).strip():
        for opener, inner in groups:
            if opener in "[⟨":
                # instance binder `[Fact p]` / destructuring pattern `⟨a, b⟩`:
                # a typeclass assumption or a structure pattern — no head.
                return "quantifier_structure_binder"
            gap = _quant_binder_section(inner, names, bounds, carriers)
            if gap is not None:
                return gap
        return None
    # membership/subset binder `x ∈ S` / `B ⊆ A`: treated as a bounded binder
    # whose predicate text carries the ∈/⊆, so the set blocker names the gap
    # precisely (the same bucket these rows occupied before extraction).
    mi = _depth0_find_any(sec, "∈∉⊆⊂")
    if mi >= 0:
        nm = sec[:mi].split()
        if nm and all(_IDENT_RE.fullmatch(n) for n in nm):
            names.extend(nm)
            bounds.append(sec)
            carriers.add("unknown")
            return None
        return "quantifier_malformed"
    ci = first_top_level_colon(sec)
    if ci >= 0:
        nm = sec[:ci].split()
        typ = sec[ci + 1 :].strip()
        if not nm or not all(_IDENT_RE.fullmatch(n) for n in nm) or not typ:
            return "quantifier_malformed"
        if typ in _NUMERIC_TYPES:
            names.extend(nm)
            carriers.add(
                "nat" if typ in _NAT_TYPES
                else "int" if typ in _INTZ_TYPES
                else "field"
            )
            return None
        dr = domain_reason(typ)
        if dr is not None:
            return dr
        typ_norm = typ.replace("->", "→")
        if "→" in typ_norm and not (set(typ_norm) & _PROP_CHARS - {"→"}):
            return "quantifier_function_binder"
        first = typ.split()[0] if typ.split() else ""
        if first in {"Prop", "Type", "Sort", "Type*", "Sort*"}:
            # second-order quantification (over propositions or types): the
            # binder heads are first-order over numeric domains only.
            return "quantifier_over_sort"
        if first in _STRUCTURE_HEADS:
            return _blocker(typ) or "quantifier_structure_binder"
        # Prop-typed (proof) binder: the type is a bound conjunct; its names
        # are proof terms, not value slots. Custom non-Prop types land here
        # too and their head then fails the symbol check — the same
        # conservative fallback classify_binder applies at statement level.
        bounds.append(typ)
        return None
    ri = _depth0_find_any(sec, _REL_BOUND_CHARS)
    if ri >= 0:
        nm = sec[:ri].split()
        if nm and all(_IDENT_RE.fullmatch(n) for n in nm):
            names.extend(nm)
            bounds.append(sec)
            carriers.add("unknown")
            return None
        return "quantifier_malformed"
    nm = sec.split()
    if nm and all(_IDENT_RE.fullmatch(n) for n in nm):
        names.extend(nm)
        carriers.add("unknown")
        return None
    return "quantifier_malformed"


def _strip_neg_wrappers(s: str) -> str:
    """Strip leading ¬ and whole-span parens WHEN a quantifier follows: the
    NEG head is carried, and the quantifier De Morgan nodes state exactly the
    NEG∘FORALL / NEG∘EXISTS compositions. `¬(A ∧ B)` is left alone."""
    while True:
        if s.startswith("¬"):
            t = s[1:].lstrip()
            u = t
            if _spans_whole(u):
                v = u[1:-1].strip()
                if v[:1] in _QUANT_CHARS or v.startswith("¬"):
                    u = v
            if u[:1] in _QUANT_CHARS or u.startswith("¬"):
                s = t
                continue
        if _spans_whole(s):
            inner = s[1:-1].strip()
            if inner[:1] in _QUANT_CHARS or inner.startswith("¬"):
                s = inner
                continue
        break
    return s


def extract_quantifier_prefix(seg: str):
    """Parse a (possibly ¬-wrapped) quantifier-PREFIX proposition.

    Returns None when `seg` is not quantifier-led (the caller uses it
    unchanged); ("gap", label, [], set()) for a precisely refused shape; or
    ("ok", check_text, bound_names, carriers) where `check_text` is the
    desugared proposition every segment check runs on — binder predicates and
    prop-binder types joined to the body with `→`, in binding order."""
    s = _strip_neg_wrappers(seg.strip())
    if s[:1] not in _QUANT_CHARS:
        return None
    names: list[str] = []
    bounds: list[str] = []
    carriers: set[str] = set()
    while s[:1] in _QUANT_CHARS:
        rest = s[1:].lstrip()
        if rest.startswith("!"):
            # ∃!: rides the ∃ path via its ExistsUnique expansion — the
            # uniqueness clause re-checks the same body and adds an equation
            # between two bound slots, both already carried.
            rest = rest[1:].lstrip()
        ci = _depth0_seek(rest, ",")
        if ci < 0:
            return ("gap", "quantifier_malformed", [], set())
        gap = _quant_binder_section(rest[:ci], names, bounds, carriers)
        if gap is not None:
            return ("gap", gap, [], set())
        s = _strip_neg_wrappers(rest[ci + 1 :].strip())
    if not s:
        return ("gap", "quantifier_malformed", [], set())
    check_text = " → ".join([*bounds, s]) if bounds else s
    return ("ok", check_text, names, carriers)


def _quantifier_segment(seg: str, outer_names: set[str]):
    """Segment-level wrapper: None (not quantifier-led) | ("gap", label) |
    ("ok", check_text, extra_vars, nat, int, field). Shadowing is refused
    here because only the caller knows the statement's outer names."""
    r = extract_quantifier_prefix(seg)
    if r is None:
        return None
    if r[0] == "gap":
        return ("gap", r[1])
    _, check_text, bound, carriers = r
    if len(set(bound)) != len(bound) or (set(bound) & outer_names):
        return ("gap", "quantifier_shadowed_binder")
    return (
        "ok",
        check_text,
        set(bound),
        "nat" in carriers or "unknown" in carriers,
        "int" in carriers,
        "field" in carriers,
    )


# --------------------------------------------------------------------------
# Atom-tree walk (v0.10 embedded quantifiers)
#
# Where the flat path's verdict on a GOAL-BODY or HYPOTHESIS segment would be
# `quantifier_embedded` — and ONLY there — the segment is re-judged as a
# connective tree whose leaves are either relations or quantified
# subformulas. The gate guarantees the dual pass loses nothing: a segment the
# flat path already judged some other way is never re-judged, and `let`
# equations keep the embedded refusal (a quantified let-RHS is a Prop-valued
# binding). Design registered in ANALYSIS "embedded quantifiers: the
# atom-tree walk" BEFORE this code existed; the rules:
#
# * Split at depth-0 ∧/∨/→/↔ — every one a carried head (MEET/JOIN/IMPLIES
#   and the ↔ relation) — STOPPING at the first depth-0 ∀/∃: a Lean binder's
#   scope swallows everything to its right, so the remainder is one leaf.
# * ¬-wrappers and whole-span parens strip per part: NEG is a carried head
#   over any checked subtree (the quantifier De Morgan nodes state the
#   quantified compositions; the propositional laws the rest).
# * A quantifier-led leaf runs the EXISTING prefix extractor — binder rules
#   unchanged (ℕ-default, bounded-binder desugar, ∃! expansion, precise
#   function/structure/sort/malformed refusals) — then the walk recurses into
#   the desugared body. A quantifier-free leaf must be prop-shaped and pass
#   every existing blocker/carrier/symbol check.
# * Binder names are tracked PER SUBFORMULA. Shadowing is refused on scope
#   OVERLAP (a leaf binder colliding with a statement binder, domain var, or
#   ENCLOSING quantifier binder on its path): slot-recurrence binding cannot
#   express two carriers for one name in one scope chain. Disjoint SIBLING
#   scopes reusing a name — `(∃ k, n = 2*k) ∨ (∃ k, n = 2*k+1)` — are
#   alpha-independent and accepted: every occurrence sits inside exactly one
#   binder's subtree, so skeleton recurrence stays unambiguous.
# * Carrier honesty is LEAF-LOCAL, strictly finer than segment-local: a
#   field signal legitimizes `/`/`-` in its own conjunct's subtree only, and
#   the mixed-carrier chain shield applies per quantified leaf against the
#   flags inherited on its path. The one disclosed asymmetry is inherited
#   unchanged: a statement-binder field variable is statement-scoped and
#   reaches every leaf, exactly as it reaches every segment.
# * A ∀/∃ that is not leaf-leading after the split — term position: inside a
#   set-builder (`IsLeast {n | ∀ …}`), a Prop-valued equality operand
#   (`(∃ …) = False`), a function argument — keeps `quantifier_embedded`, as
#   does anything past the depth cap (adversarially deep nests refuse
#   conservatively).
# --------------------------------------------------------------------------

_CONN_CHARS = "→∧∨↔"
_TREE_DEPTH_CAP = 40


def _split_tree_parts(s: str) -> tuple[list[str], list[str]]:
    """Split at depth-0 connectives, stopping at the first depth-0 quantifier
    char (whose Lean scope swallows everything rightward into one leaf)."""
    parts: list[str] = []
    conns: list[str] = []
    depth = 0
    start = 0
    for i, c in enumerate(s):
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0:
            if c in _CONN_CHARS:
                parts.append(s[start:i])
                conns.append(c)
                start = i + 1
            elif c in _QUANT_CHARS:
                break
    parts.append(s[start:])
    return parts, conns


def _tree_leaf_gap(a: str, leaf_vars: set[str], nat: bool, int_: bool,
                   field: bool) -> str | None:
    """Every flat check, applied to ONE quantifier-free leaf: prop shape
    first (an atom must be a relation, a prop constant, or a supported bare
    predicate application), then blockers, the leaf-local carrier rule, the
    integer-predicate rule, and the symbol scan under the leaf's own vars."""
    if not _prop_atom_shaped(a):
        return _blocker(a) or "no_relation_in_goal"
    r = (
        _blocker(a)
        or _carrier_gap(a, nat, int_, field or bool(_FIELD_SIGNAL_RE.search(a)))
        or _int_pred_field_gap(a, field, leaf_vars)
    )
    if r is None:
        bad = _unsupported_symbol(a, leaf_vars)
        if bad is not None:
            r = f"unsupported_symbol:{bad}"
    return r


def _tree_walk(seg: str, leaf_vars: set[str], nat: bool, int_: bool,
               field: bool, path_names: set[str], depth: int = 0) -> str | None:
    """Judge one subformula of the atom tree. None means every leaf reduced;
    otherwise the first leaf's precise gap label."""
    if depth > _TREE_DEPTH_CAP:
        return "quantifier_embedded"
    parts, _conns = _split_tree_parts(seg)
    if len(parts) > 1:
        for p in parts:
            if not p.strip():
                return "quantifier_embedded"  # dangling connective operand
            r = _tree_walk(p, leaf_vars, nat, int_, field, path_names, depth + 1)
            if r is not None:
                return r
        return None
    a = seg.strip()
    if not a:
        return "quantifier_embedded"
    if a.startswith("¬"):
        return _tree_walk(a[1:], leaf_vars, nat, int_, field, path_names, depth + 1)
    if _spans_whole(a):
        return _tree_walk(a[1:-1], leaf_vars, nat, int_, field, path_names, depth + 1)
    if a[0] in _QUANT_CHARS:
        r = extract_quantifier_prefix(a)
        if r is None or r[0] == "gap":
            return r[1] if r is not None else "quantifier_embedded"
        _, check_text, bound, carriers = r
        if len(set(bound)) != len(bound) or (set(bound) & path_names):
            return "quantifier_shadowed_binder"
        q_nat = "nat" in carriers or "unknown" in carriers
        q_int = "int" in carriers
        # mixed-carrier chain shield, per quantified leaf: the chain's field
        # carrier is demoted when it mixes with an integer-or-unknown carrier
        # (its own or anything inherited on the path) — same direction as the
        # statement-level shield, applied to the leaf's inherited flags.
        l_field = field or ("field" in carriers and not (q_nat or q_int or nat or int_))
        return _tree_walk(check_text, leaf_vars | set(bound), nat or q_nat,
                          int_ or q_int, l_field, path_names | set(bound),
                          depth + 1)
    if "∀" in a or "∃" in a:
        return "quantifier_embedded"  # TERM position: genuinely out
    return _tree_leaf_gap(a, leaf_vars, nat, int_, field)


# Integer predicates over a field carrier are NOT the corpus head: data/
# number_theory's EVEN/ODD/PRIME are integer parity/primality (over ℝ, mathlib's
# `Even x` is trivially true for every real -- a different, uncarried reading).
# Conservative: if the statement declares a field-typed value var and an integer
# predicate's text touches any variable, the carrier cannot be attributed.
_INT_PRED_RE = re.compile(
    r"(?<![\w.])(?:[Ee]ven|[Oo]dd|(?:[Nn]at\.)?[Pp]rime)(?![\w.'])"
)
# ... and the argument-level hole: even WITHOUT a field binder, a predicate
# applied to a coerced/ascribed-real argument (`Even ↑x`, `Odd (y : ℝ)`) is
# the trivial field reading, not the integer head. (Review follow-up; zero
# realized false positives at 1.73M today — this keeps it that way.)
_INT_PRED_ARG_RE = re.compile(
    r"(?<![\w.])(?:[Ee]ven|[Oo]dd|(?:[Nn]at\.)?[Pp]rime)\s*"
    r"(↑\S*|\((?:[^()]|\([^()]*\))*\))"
)


def _int_pred_field_gap(text: str, has_field: bool, value_vars: set[str]) -> str | None:
    if not _INT_PRED_RE.search(text):
        return None
    if has_field and any(tok in value_vars for tok in _IDENT_RE.findall(text)):
        return "integer_predicate_field_carrier"
    for m in _INT_PRED_ARG_RE.finditer(text):
        if _FIELD_SIGNAL_RE.search(m.group(1)):
            return "integer_predicate_field_carrier"
    return None


# An EXPRESSION whose arithmetic is over a field: an explicit coercion ↑, a
# ℝ/ℚ ascription, a Real/Rat namespace call, or a decimal literal. Applied
# PER SEGMENT (goal body, each let-binding equation, each hypothesis): a
# signal legitimizes `/` and `-` only in the segment that carries it —
# computed over the whole statement it shielded ℕ floor-division/monus in
# sibling segments (the review-caught over-count). Without a local signal
# (or a binder-declared field var), `/` and `-` over ℕ/ℤ carriers are the
# floor-division / monus GAPS, not the real operations.
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

    has_nat = stmt.get("has_nat_carrier", False)
    has_int = stmt.get("has_int_carrier", False)
    has_field = stmt.get("has_field_carrier", False)

    # v0.10: a quantifier PREFIX on the goal body (or a hypothesis, below) is
    # extracted before any other check — its bound names become value slots
    # and its carriers register for THAT segment only. `let` equations are
    # deliberately not extracted: a quantified let-RHS is a Prop-valued
    # binding, which stays the quantifier_embedded gap.
    # MIXED-CARRIER CHAIN SHIELD (review-caught over-count, this slice's own
    # regression): the chain-level field flag is ONE boolean for the whole
    # segment, so `∀ (d : ℚ) (n : ℕ), …` shielded a sibling ℕ binder's
    # Nat.div/monus in conjuncts that never touch d (realized rows: the
    # `(n-2)*180` monus family, `4/m` with m : ℕ — value-breaking — and
    # vacuous field binders over statement-ℕ/ℤ division). When a chain's
    # field carrier MIXES with an integer-or-unknown carrier (its own or the
    # statement's), the field flag is demoted and the division/monus cannot
    # be attributed to the field binder: the integer reading's gap wins —
    # the same conservative direction as the ℕ default for untyped binders.
    # An in-segment textual signal (`↑`, `: ℚ` ascription, decimal) still
    # legitimizes, exactly as everywhere else.
    def _q_field_unmixed(q_nat: bool, q_int: bool, q_field: bool) -> bool:
        return q_field and not (q_nat or q_int or has_nat or has_int)

    outer_names = value_vars | set(domain_vars)
    gq = _quantifier_segment(goal, outer_names)
    goal_gap: str | None = None
    goal_check, goal_vars = goal, value_vars
    g_nat, g_int, g_field = has_nat, has_int, has_field
    if gq is not None:
        if gq[0] == "gap":
            goal_gap = gq[1]
        else:
            _, goal_check, extra, q_nat, q_int, q_field = gq
            goal_vars = value_vars | extra
            g_nat, g_int, g_field = (
                has_nat or q_nat, has_int or q_int,
                has_field or _q_field_unmixed(q_nat, q_int, q_field),
            )

    # the let bindings are PART of the goal proposition (a let-goal is the
    # definitional equations plus the body), so they join every goal-side
    # check — under the STATEMENT context, while the (desugared) goal body
    # checks under its quantifier-extended context.
    # the final True/False flag marks the segment as goal-body/hypothesis
    # (atom-tree walk eligible) vs let-equation (embedded stays refused).
    goal_contexts = [
        *((seg, value_vars, has_nat, has_int, has_field, False) for seg in lets),
        (goal_check, goal_vars, g_nat, g_int, g_field, True),
    ]
    goal_idents: set[str] = set()
    for seg, _v, _n, _i, _f, _t in goal_contexts:
        goal_idents |= set(_IDENT_RE.findall(seg))

    # The field signal is SEGMENT-LOCAL (review-caught over-count): a `: ℚ`
    # ascription, coercion `↑`, `Real.` call, or decimal literal legitimizes
    # `/` and `-` only in the expression that carries it. Computed globally it
    # shielded ℕ floor-division/monus in OTHER segments — e.g. a `(w : ℚ)`
    # goal body hiding the `a + b - 1` monus inside a sibling ℕ let-binding
    # (Goedel-Pset-413727), or a ℚ-typed binding hiding Nat.div AND monus
    # inside an ℕ-typed one (Goedel-Pset-1082706, where `s / n` over ℕ is 0
    # and the stated claim is false — exactly what carrier-honesty refuses).
    # A binder-DECLARED field var (statement or quantifier) stays scoped to
    # every segment its scope reaches: the whole statement for a theorem
    # binder, its OWN segment for a quantifier binder.
    def _seg_field_signal(seg: str, seg_field: bool) -> bool:
        return seg_field or bool(_FIELD_SIGNAL_RE.search(seg))

    def _segment_gap(seg, seg_vars, seg_nat, seg_int, seg_field,
                     tree_names=None):
        r = (
            _blocker(seg)
            or _carrier_gap(seg, seg_nat, seg_int,
                            _seg_field_signal(seg, seg_field))
            or _int_pred_field_gap(seg, seg_field, seg_vars)
        )
        if r is None:
            bad = _unsupported_symbol(seg, seg_vars)
            if bad is not None:
                r = f"unsupported_symbol:{bad}"
        # v0.10 embedded quantifiers: exactly where the flat verdict would be
        # `quantifier_embedded` AND the segment is a goal body or hypothesis
        # (tree_names is not None), the atom-tree walk gets the final word.
        if r == "quantifier_embedded" and tree_names is not None:
            r = _tree_walk(seg, seg_vars, seg_nat, seg_int, seg_field,
                           tree_names)
        return r

    # ---- goal-only ----
    goal_reason: str | None = goal_gap
    if goal_reason is None and not _prop_shaped(goal_check):
        # prefer the precise construct label when one exists (a relationless
        # `Nat.Coprime m n` is the coprime gap, a relationless `∑`-term the
        # big-operator gap); `no_relation_in_goal` is only the residue that
        # no blocker can name better.
        goal_reason = _blocker(goal_check) or "no_relation_in_goal"
        if goal_reason == "quantifier_embedded":
            # a not-yet-prop-shaped goal whose blocker verdict is the embedded
            # label (e.g. `(∀ x : ℕ, Even x) ∧ Odd 3`, relationless): the walk
            # judges it — its per-leaf prop-shape check subsumes this gate.
            goal_reason = _tree_walk(goal_check, goal_vars, g_nat, g_int,
                                     g_field, outer_names | goal_vars)
    if goal_reason is None:
        hit = sorted(domain_vars[v] for v in (set(domain_vars) & goal_idents))
        if hit:
            goal_reason = hit[0]
    if goal_reason is None:
        for seg, seg_vars, seg_nat, seg_int, seg_field, is_body in goal_contexts:
            goal_reason = _segment_gap(
                seg, seg_vars, seg_nat, seg_int, seg_field,
                (outer_names | seg_vars) if is_body else None)
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
                hq = _quantifier_segment(hyp, outer_names)
                if hq is None:
                    r = _segment_gap(hyp, value_vars, has_nat, has_int,
                                     has_field, outer_names)
                elif hq[0] == "gap":
                    r = hq[1]
                else:
                    _, h_check, h_extra, h_nat, h_int, h_field = hq
                    r = _segment_gap(
                        h_check, value_vars | h_extra,
                        has_nat or h_nat, has_int or h_int,
                        has_field or _q_field_unmixed(h_nat, h_int, h_field),
                        outer_names | h_extra,
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
