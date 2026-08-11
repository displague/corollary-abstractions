#!/usr/bin/env python3
"""Deterministic miniF2F ingestion + grammar-coverage measurement.

The honest first question of ingestion (v0.9 item 1, argued in
docs/DESIGN-corpus-scale-and-programming.md) is NOT "how many nodes did we add"
but "how much of a real formal source expresses in the corpus's grammar at all".
This tool answers that for miniF2F, before any node is authored, so the scale
claim is made against a measured coverage number rather than asserted.

Two stages, so the measurement regenerates in CI *without* redistributing or
re-fetching the source archive:

  extract   pinned Lean-3 files (SHA-256 verified against data_sources/manifest.json;
            gitignored under data_sources/archives/minif2f/) -> committed
            data_sources/derived/minif2f/statements.json
  coverage  committed statements.json -> committed experiments/minif2f_coverage.json

The corpus grammar is the head-algebra that appears in data/*/nodes.json
`structural_signature.anonymized_template`. A head counts as supported only if a
node in data/ actually carries it: relations (=, <=, <, >=, >, !=), the Boolean
operators MEET/JOIN/NEG/IMPLIES, arithmetic (+, -, *, /, ^) and the three
transcendental heads the corpus carries (SQRT, LOG, EXP). Modulo (%) and divides
(the only MOD head in data/ is morphology's *linguistic modifier*, and there is
no divides head) are therefore GAPS, not supported -- number theory needs them
but the corpus has no head for them yet. A miniF2F statement counts as COVERED
only if it reduces to a skeleton whose every leaf is a numeral or a numeric-typed
bound variable and every internal node is one of the supported heads. Anything
else is UNTRANSLATABLE, tagged by the first construct the grammar has no head for
(modulo, divides, big operators, quantifier goals, set membership, tuple
constructors, absolute value / norm, modular/complex carriers, an unknown
function binder, primality, gcd, factorial, ...). Each untranslatable form is a
finding about the grammar's reach, scored not asserted -- exactly how v0.7's
correspondence rung already treats an unprovable link.

Two numbers are reported and both matter:
  * goal-only coverage    -- the bare goal reduces; an UPPER BOUND that silently
                             drops the hypotheses.
  * full-statement coverage -- the goal AND every hypothesis reduce, so the whole
                             conditional node IMPLIES(MEET(hyps), goal) is
                             expressible. This is the real ingestion number,
                             because dropping a competition problem's hypotheses
                             changes the theorem.

Determinism: no timestamps, no dict-order dependence, integer counts with
percentages rounded to one place. `coverage` is a pure function of the committed
extract, so a regeneration test can hold it byte-for-byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "data_sources" / "manifest.json"
ARCHIVE_DIR = REPO_ROOT / "data_sources" / "archives" / "minif2f"
EXTRACT_PATH = REPO_ROOT / "data_sources" / "derived" / "minif2f" / "statements.json"
COVERAGE_PATH = REPO_ROOT / "experiments" / "minif2f_coverage.json"

MANIFEST_SOURCE_ID = "git-openai-minif2f"


# --------------------------------------------------------------------------
# Stage 1: extract  (Lean-3 source -> statement signatures)
# --------------------------------------------------------------------------

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_manifest_source() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for src in manifest["sources"]:
        if src["id"] == MANIFEST_SOURCE_ID:
            return src
    raise KeyError(f"manifest source `{MANIFEST_SOURCE_ID}` not found")


def _strip_comments(text: str) -> str:
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


_OPEN = "([{⟨"
_CLOSE = ")]}⟩"
_MATCH = {")": "(", "]": "[", "}": "{", "⟩": "⟨"}


def _take_until_top_level(s: str, token: str) -> str | None:
    """Return the prefix of `s` up to the first depth-0 occurrence of `token`."""
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


def _first_top_level_colon(s: str) -> int:
    """Index of the first depth-0 `:` in `s`, or -1. Skips `:=` (never a
    goal separator) though the signature is already trimmed before `:=`."""
    depth = 0
    for i, c in enumerate(s):
        if c in _OPEN:
            depth += 1
        elif c in _CLOSE:
            depth -= 1
        elif depth == 0 and c == ":" and s[i : i + 2] != ":=":
            return i
    return -1


def _top_level_groups(s: str) -> list[tuple[str, str]]:
    """Split binder text into its top-level bracketed groups: (bracket, inner)."""
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


THEOREM_RE = re.compile(r"(?m)^theorem[ \t]+(\S+)")

# Numeric leaf types. nnreal (ℝ≥0) and ℕ+/pnat are included on purpose: a
# nonnegativity/positivity domain narrows the *leaf*, but the arithmetic over it
# is identical, so it is a regularity condition on the slot (exactly what a node's
# `regularity_conditions` already records) -- not a construct the grammar lacks.
_NUMERIC_TYPES = {
    "ℕ", "ℝ", "ℤ", "ℚ", "nat", "real", "int", "rat",
    "nnreal", "ℝ≥0", "ℕ+", "pnat", "ℤ+",
}
# Characters that mark a binder type as a Prop (a hypothesis), not a type.
_PROP_CHARS = set("=<>≤≥≠∧∨¬↔∀∃∈∉")
# Value domains the corpus grammar does not carry as leaf slots, keyed to the
# reason a statement over them is untranslatable. Unlike nnreal (real-with-
# constraint), these are genuinely different carriers.
_DOMAIN_REASONS = {"ℂ": "complex_number", "complex": "complex_number"}


def _domain_reason(typ: str) -> str | None:
    if typ in _DOMAIN_REASONS:
        return _DOMAIN_REASONS[typ]
    if typ.split()[:1] == ["zmod"]:  # `zmod N` -- a modular carrier
        return "modular_type_zmod"
    return None


def _classify_binder(inner: str) -> tuple[list[str], str | None, bool, list[tuple[str, str]]]:
    """(value_var_names, hypothesis_prop_or_None, is_function_unknown,
    [(name, domain_reason), ...] for slots over an unsupported carrier)."""
    if ":" not in inner:
        return [], None, False, []
    names_part, type_part = inner.split(":", 1)
    names = names_part.split()
    typ = type_part.strip()
    typ_norm = typ.replace("->", "→")
    if typ in _NUMERIC_TYPES:
        return names, None, False, []
    dr = _domain_reason(typ)
    if dr is not None:
        return [], None, False, [(n, dr) for n in names]
    # An arrow type with no Prop characters is a function/structure value, i.e.
    # an unknown function (ℝ→ℝ, ℂ→ℂ, ℕ→nnreal, ℕ→ℕ→ℕ). Its names are not slots.
    if "→" in typ_norm and not (set(typ_norm) & _PROP_CHARS - {"→"}):
        return [], None, True, []
    # A bundled-structure type (equiv ℝ ℝ, is_least S u, finset ℕ, set ℕ) with no
    # Prop characters also introduces an unknown value, not a hypothesis; treat it
    # as a function unknown so the whole statement is (correctly) untranslatable.
    if not (set(typ) & _PROP_CHARS) and not typ[:1].isdigit():
        first = typ.split()[0] if typ.split() else ""
        if first in {"equiv", "is_least", "is_greatest", "finset", "set",
                     "multiset", "list", "polynomial", "matrix"}:
            return [], None, True, []
    # otherwise the binder introduces a proof term of a Prop: the Prop is a hyp.
    return [], typ, False, []


def parse_theorem_block(block: str) -> dict | None:
    """Parse one `theorem NAME ... := ...` block into name/binders/hyps/goal."""
    m = THEOREM_RE.match(block)
    if not m:
        return None
    name = m.group(1)
    rest = block[m.end() :]
    sig = _take_until_top_level(rest, ":=")
    if sig is None:
        return None  # no proof terminator found; skip (not a statement we can trust)
    ci = _first_top_level_colon(sig)
    if ci < 0:
        return None
    binders_text = sig[:ci].strip()
    goal = " ".join(sig[ci + 1 :].split())

    value_vars: list[str] = []
    domain_vars: dict[str, str] = {}
    hyps: list[str] = []
    fn_unknown = False
    for _bracket, inner in _top_level_groups(binders_text):
        names, hyp, is_fn, dvars = _classify_binder(inner)
        value_vars.extend(names)
        for nm, reason in dvars:
            domain_vars[nm] = reason
        if hyp is not None:
            hyps.append(" ".join(hyp.split()))
        fn_unknown = fn_unknown or is_fn
    return {
        "name": name,
        "value_vars": value_vars,
        "domain_vars": domain_vars,
        "hyps": hyps,
        "goal": goal,
        "fn_unknown": fn_unknown,
    }


def extract_file(text: str, split: str) -> list[dict]:
    text = _strip_comments(text)
    starts = [m.start() for m in THEOREM_RE.finditer(text)]
    starts.append(len(text))
    out: list[dict] = []
    for a, b in zip(starts, starts[1:]):
        parsed = parse_theorem_block(text[a:b])
        if parsed is not None:
            parsed["split"] = split
            out.append(parsed)
    return out


def run_extract() -> int:
    src = _load_manifest_source()
    statements: list[dict] = []
    file_records = []
    for fmeta in src["files"]:
        path = ARCHIVE_DIR / fmeta["filename"]
        if not path.exists():
            print(
                f"MISSING: {path} not present. Fetch the pinned source first:\n"
                f"  curl -s {src['raw_url_template'].format(filename=fmeta['filename'])} "
                f"-o {path}",
                file=sys.stderr,
            )
            return 2
        raw = path.read_bytes()
        digest = _sha256(raw)
        if digest != fmeta["sha256"]:
            print(
                f"SHA MISMATCH for {fmeta['filename']}:\n"
                f"  expected {fmeta['sha256']}\n  got      {digest}\n"
                "Refusing to extract from unpinned bytes.",
                file=sys.stderr,
            )
            return 3
        parsed = extract_file(raw.decode("utf-8"), fmeta["split"])
        if len(parsed) != fmeta["theorem_count"]:
            print(
                f"COUNT MISMATCH for {fmeta['filename']}: parsed {len(parsed)}, "
                f"manifest pins {fmeta['theorem_count']}. Parser drift; refusing.",
                file=sys.stderr,
            )
            return 4
        statements.extend(parsed)
        file_records.append(
            {
                "filename": fmeta["filename"],
                "sha256": fmeta["sha256"],
                "split": fmeta["split"],
                "theorem_count": len(parsed),
            }
        )

    statements.sort(key=lambda s: (s["split"], s["name"]))
    doc = {
        "generated_by": "scripts/ingest_minif2f.py extract",
        "source": {
            "id": src["id"],
            "url": src["url"],
            "git_commit": src["git_commit"],
            "license": src["license"],
            "attribution": "miniF2F (c) 2021 OpenAI, released under Apache License 2.0. "
            "Statement signatures extracted; proofs omitted.",
            "files": file_records,
        },
        "statement_count": len(statements),
        "statements": statements,
    }
    EXTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_json(EXTRACT_PATH, doc)
    print(f"extract OK: {len(statements)} statements -> {_rel(EXTRACT_PATH)}")
    return 0


# --------------------------------------------------------------------------
# Stage 2: coverage  (statement signatures -> grammar-coverage measurement)
# --------------------------------------------------------------------------

# Supported transcendental heads the corpus already carries. Everything
# arithmetic/relational/logical is handled structurally below.
_SUPPORTED_FUNCS = {
    "real.sqrt": "SQRT",
    "real.log": "LOG",
    "real.exp": "EXP",
    "nnreal.sqrt": "SQRT",
    "sqrt": "SQRT",
    "exp": "EXP",
}
# Allowed constant leaves (specific reals with no slot).
_ALLOWED_CONSTS = {"π", "real.pi", "pi"}

# Relations that make a goal a statement node. `∣` is Lean's "divides".
_RELATIONS = ["=", "≠", "<", "≤", ">", "≥", "≡", "∣", "↔"]

# Blocker constructs, checked in order; the first hit names why the grammar
# cannot yet express the statement. Reasons are the finding.
_BLOCKERS: list[tuple[str, re.Pattern]] = [
    ("big_operator", re.compile(r"∑|∏|finset\.sum|finset\.prod")),
    ("integral", re.compile(r"∫")),
    # modulo and divides have NO head in data/*/nodes.json (the only MOD there is
    # the morphology `modifier` head, not integer modulo; there is no divides
    # head). They are grammar GAPS, not supported -- number theory needs them.
    ("modulo_no_head", re.compile(r"%|\[MOD|\bmodeq\b|\bnat\.mod\b|\bint\.mod\b")),
    ("divides_no_head", re.compile(r"∣|\bdvd\b|\bnat\.dvd\b")),
    ("set_or_finset", re.compile(r"finset|∈|∉|⊆|⊂|\.card\b|(?<![A-Za-z])set(?![A-Za-z])")),
    ("existential_quantifier", re.compile(r"∃")),
    ("universal_quantifier", re.compile(r"∀")),
    # a comma surviving big-operator / quantifier / set screening is a pair /
    # tuple / list constructor (the `(a,b,…)` head, which the grammar lacks).
    ("tuple_or_structure", re.compile(r",")),
    ("modular_type_zmod", re.compile(r"zmod")),
    ("complex_number", re.compile(r"ℂ|complex")),
    ("primality", re.compile(r"\bnat\.prime\b|\bprime\b|coprime")),
    ("gcd_lcm", re.compile(r"\bgcd\b|\blcm\b|nat\.gcd|nat\.lcm")),
    ("binomial_choose", re.compile(r"\bnat\.choose\b|\bchoose\b|\bnat\.factorial\b")),
    ("factorial", re.compile(r"!")),
    ("floor_ceil", re.compile(r"⌊|⌋|⌈|⌉|\bfloor\b|\bceil\b|\bnat\.floor\b")),
    ("digit_expansion", re.compile(r"nat\.digits|nat\.of_digits")),
    ("rational_component", re.compile(r"\.denom\b|\.num\b")),
    # absolute value / norm: ASCII |·|, mathlib norm bars ∥·∥ / ‖·‖, and words.
    ("absolute_value", re.compile(r"\babs\b|\bnorm\b|lvert|lVert|\||∥|‖|⟪|⟫")),
    ("min_max", re.compile(r"\bmin\b|\bmax\b")),
    ("trig", re.compile(r"real\.cos|real\.sin|real\.tan|real\.arcsin|real\.arccos")),
    ("polynomial", re.compile(r"polynomial")),
    ("matrix", re.compile(r"matrix")),
    ("derivative", re.compile(r"deriv|∂")),
]

# Identifier tokens: dotted lowercase names (real.sqrt, nat.succ) and simple names.
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
# Lean keywords / harmless tokens that are not leaves needing a slot.
_IGNORE_IDENTS = {"begin", "end", "by", "have", "show", "from"}


def _blocker(text: str) -> str | None:
    for reason, pat in _BLOCKERS:
        if pat.search(text):
            return reason
    return None


def _unsupported_symbol(expr: str, value_vars: set[str]) -> str | None:
    """First identifier in `expr` that is neither a value slot, a supported
    function, nor an allowed constant -- i.e. a leaf the grammar cannot name."""
    for tok in _IDENT_RE.findall(expr):
        if tok in value_vars or tok in _SUPPORTED_FUNCS or tok in _ALLOWED_CONSTS:
            continue
        if tok in _IGNORE_IDENTS:
            continue
        return tok
    return None


def _has_relation(goal: str) -> bool:
    return any(r in goal for r in _RELATIONS)


def classify(stmt: dict) -> dict:
    """Classify one statement: goal-only and full-statement coverage + reason."""
    goal = stmt["goal"]
    value_vars = set(stmt["value_vars"])
    domain_vars = stmt.get("domain_vars", {})
    goal_idents = set(_IDENT_RE.findall(goal))

    # ---- goal-only ----
    goal_reason: str | None = None
    if not _has_relation(goal):
        goal_reason = "no_relation_in_goal"
    if goal_reason is None:
        # a slot's carrier is ℂ / zmod / ... -- not a corpus leaf domain
        hit = sorted(domain_vars[v] for v in (set(domain_vars) & goal_idents))
        if hit:
            goal_reason = hit[0]
    if goal_reason is None:
        goal_reason = _blocker(goal)
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
                r = _blocker(hyp) or (
                    (lambda b: f"unsupported_symbol:{b}" if b else None)(
                        _unsupported_symbol(hyp, value_vars)
                    )
                )
                if r is not None:
                    full_reason = f"hyp:{r}"
                    break
    full_ok = full_reason is None

    return {
        "name": stmt["name"],
        "split": stmt["split"],
        "goal_ok": goal_ok,
        "goal_reason": goal_reason,
        "full_ok": full_ok,
        "full_reason": full_reason,
    }


def _tally(reasons: list[str | None]) -> dict:
    counts: dict[str, int] = {}
    for r in reasons:
        if r is None:
            continue
        counts[r] = counts.get(r, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def _pct(num: int, den: int) -> float:
    return round(100.0 * num / den, 1) if den else 0.0


def build_coverage(doc: dict) -> dict:
    """Pure function: extract doc -> coverage doc. No I/O, so a test can assert
    it reproduces the committed measurement byte-for-byte."""
    results = [classify(s) for s in doc["statements"]]
    results.sort(key=lambda r: (r["split"], r["name"]))

    total = len(results)
    goal_ok = sum(1 for r in results if r["goal_ok"])
    full_ok = sum(1 for r in results if r["full_ok"])

    by_split: dict[str, dict] = {}
    for split in sorted({r["split"] for r in results}):
        rs = [r for r in results if r["split"] == split]
        by_split[split] = {
            "total": len(rs),
            "goal_only_covered": sum(1 for r in rs if r["goal_ok"]),
            "full_statement_covered": sum(1 for r in rs if r["full_ok"]),
        }

    coverage = {
        "generated_by": "scripts/ingest_minif2f.py coverage",
        "source_extract": {
            "path": _rel(EXTRACT_PATH),
            "git_commit": doc["source"]["git_commit"],
            "statement_count": doc["statement_count"],
        },
        "grammar": {
            "supported_heads": [
                "relations(= ≠ < ≤ > ≥ ↔)",
                "MEET(∧) JOIN(∨) NEG(¬) IMPLIES(→)",
                "arithmetic(+ - * / ^)",
                "SQRT(real.sqrt) LOG(real.log) EXP(real.exp)",
            ],
            "explicit_gaps_no_head_in_corpus": [
                "modulo(%, [MOD n])", "divides(∣)", "absolute-value/norm(|·|, ∥·∥)",
                "tuple/pair constructor", "gcd/lcm", "big operators(∑ ∏)",
                "quantifiers(∀ ∃) in goal", "unknown-function slot",
            ],
            "supported_heads_verified": "each supported head has a corresponding node "
            "in data/*/nodes.json; % and ∣ were removed after review found they have "
            "no modulo/divides head in the corpus (the only MOD head is morphology's "
            "linguistic modifier).",
            "covered_definition": "every leaf is a numeral or numeric-typed bound "
            "variable; every internal node is a supported head; no blocker construct "
            "in goal (goal-only) or in goal and all hypotheses (full-statement).",
        },
        "totals": {
            "statements": total,
            "goal_only": {"covered": goal_ok, "pct": _pct(goal_ok, total)},
            "full_statement": {"covered": full_ok, "pct": _pct(full_ok, total)},
        },
        "by_split": by_split,
        "goal_only_untranslatable_reasons": _tally(
            [r["goal_reason"] for r in results]
        ),
        "full_statement_untranslatable_reasons": _tally(
            [r["full_reason"] for r in results]
        ),
        "covered_full_statement_names": [
            r["name"] for r in results if r["full_ok"]
        ],
        "per_statement": results,
    }
    return coverage


def run_coverage() -> int:
    if not EXTRACT_PATH.exists():
        print(
            f"MISSING extract: {_rel(EXTRACT_PATH)}. Run `extract` first.",
            file=sys.stderr,
        )
        return 2
    doc = json.loads(EXTRACT_PATH.read_text(encoding="utf-8"))
    coverage = build_coverage(doc)
    _write_json(COVERAGE_PATH, coverage)
    t = coverage["totals"]
    print(
        f"coverage OK -> {_rel(COVERAGE_PATH)}\n"
        f"  goal-only:       {t['goal_only']['covered']}/{t['statements']} "
        f"({t['goal_only']['pct']}%)\n"
        f"  full-statement:  {t['full_statement']['covered']}/{t['statements']} "
        f"({t['full_statement']['pct']}%)"
    )
    return 0


# --------------------------------------------------------------------------

def _write_json(path: Path, doc: dict) -> None:
    # write_bytes, not write_text: on Windows write_text translates \n -> \r\n,
    # which would make the committed artifact CRLF and break byte-for-byte
    # regeneration (and any LF-assuming digest). The .gitattributes pin keeps the
    # working tree LF on checkout regardless of core.autocrlf.
    text = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    path.write_bytes(text.encode("utf-8"))


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "stage",
        choices=["extract", "coverage", "all"],
        help="extract: Lean->statements.json (needs pinned archive); "
        "coverage: statements.json->coverage.json (CI-regenerable); all: both.",
    )
    args = ap.parse_args(argv)
    if args.stage in ("extract", "all"):
        rc = run_extract()
        if rc != 0:
            return rc
    if args.stage in ("coverage", "all"):
        rc = run_coverage()
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
