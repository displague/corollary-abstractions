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

The head-algebra classifier lives in scripts/grammar_coverage.py and is shared
with the Lean-workbook slice; a head counts as supported only if a node in
data/*/nodes.json carries it (relations, MEET/JOIN/NEG/IMPLIES, arithmetic
+ - * / ^, and SQRT/LOG/EXP). Modulo (%) and divides (∣) are GAPS. A statement
is COVERED only if it reduces to a skeleton whose every leaf is a numeral or a
numeric-typed bound variable and every internal node is a supported head;
anything else is UNTRANSLATABLE, tagged by the first construct with no head.

Two numbers are reported and both matter:
  * goal-only coverage    -- the bare goal reduces; an UPPER BOUND that silently
                             drops the hypotheses.
  * full-statement coverage -- the goal AND every hypothesis reduce, so the whole
                             conditional node IMPLIES(MEET(hyps), goal) is
                             expressible. This is the real ingestion number.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grammar_coverage as gc  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "data_sources" / "manifest.json"
ARCHIVE_DIR = REPO_ROOT / "data_sources" / "archives" / "minif2f"
EXTRACT_PATH = REPO_ROOT / "data_sources" / "derived" / "minif2f" / "statements.json"
COVERAGE_PATH = REPO_ROOT / "experiments" / "minif2f_coverage.json"

MANIFEST_SOURCE_ID = "git-openai-minif2f"

THEOREM_RE = re.compile(r"(?m)^theorem[ \t]+(\S+)")


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


def parse_theorem_block(block: str) -> dict | None:
    """Parse one `theorem NAME ... := ...` block into name/binders/hyps/goal."""
    m = THEOREM_RE.match(block)
    if not m:
        return None
    name = m.group(1)
    sig = gc.split_signature(block[m.end() :])
    if sig is None:
        return None
    binders_text, goal, lets = sig
    b = gc.parse_binders(binders_text)
    goal_lets = gc.apply_goal_lets(b, lets)
    if goal_lets is None:
        return None
    out = {
        "name": name,
        "value_vars": b["value_vars"],
        "domain_vars": b["domain_vars"],
        "hyps": b["hyps"],
        "goal": goal,
        "fn_unknown": b["fn_unknown"],
        "has_nat_carrier": b["has_nat_carrier"],
        "has_int_carrier": b["has_int_carrier"],
        "has_field_carrier": b["has_field_carrier"],
    }
    if goal_lets:  # absent, not empty, so let-free extracts stay byte-identical
        out["goal_lets"] = goal_lets
    return out


def extract_file(text: str, split: str) -> list[dict]:
    text = gc.strip_comments(text)
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
    gc.write_json(EXTRACT_PATH, doc)
    print(f"extract OK: {len(statements)} statements -> {gc.rel(EXTRACT_PATH)}")
    return 0


# --------------------------------------------------------------------------
# Stage 2: coverage  (statement signatures -> grammar-coverage measurement)
# --------------------------------------------------------------------------

def build_coverage(doc: dict) -> dict:
    """Pure function: extract doc -> coverage doc. No I/O, so a test can assert
    it reproduces the committed measurement byte-for-byte."""
    results = [gc.classify(s) for s in doc["statements"]]
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
            "path": gc.rel(EXTRACT_PATH),
            "git_commit": doc["source"]["git_commit"],
            "statement_count": doc["statement_count"],
        },
        "grammar": {
            "supported_heads": [
                "relations(= ≠ < ≤ > ≥ ↔)",
                "MEET(∧) JOIN(∨) NEG(¬) IMPLIES(→)",
                "arithmetic(+ - * / ^)",
                "SQRT(real.sqrt) LOG(real.log) EXP(real.exp) SIN COS TAN",
                "predicates EVEN ODD PRIME IRRATIONAL (arity 1, bare application)",
                "prop constants TRUTH FALSITY; let-bindings as definitional =",
                "quantifier PREFIX chains FORALL(∀) EXISTS(∃) over numeric domains "
                "(bounded/untyped binders ℕ-defaulted, ¬-wrappers, ∃! via its "
                "ExistsUnique expansion)",
            ],
            "explicit_gaps_no_head_in_corpus": [
                "modulo(%, [MOD n])", "divides(∣)", "absolute-value/norm(|·|, ∥·∥)",
                "tuple/pair constructor", "gcd/lcm", "big operators(∑ ∏)",
                "quantifiers in NON-prefix position (embedded in ∧/∨/→/↔, in a let "
                "RHS)", "quantification over functions/sets/structures/sorts", "unknown-function slot",
                "coprime(2-ary)", "Function.Injective/Surjective, Monotone, …",
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
            "goal_only": {"covered": goal_ok, "pct": gc.pct(goal_ok, total)},
            "full_statement": {"covered": full_ok, "pct": gc.pct(full_ok, total)},
        },
        "by_split": by_split,
        "goal_only_untranslatable_reasons": gc.tally(
            [r["goal_reason"] for r in results]
        ),
        "full_statement_untranslatable_reasons": gc.tally(
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
            f"MISSING extract: {gc.rel(EXTRACT_PATH)}. Run `extract` first.",
            file=sys.stderr,
        )
        return 2
    doc = json.loads(EXTRACT_PATH.read_text(encoding="utf-8"))
    coverage = build_coverage(doc)
    gc.write_json(COVERAGE_PATH, coverage)
    t = coverage["totals"]
    print(
        f"coverage OK -> {gc.rel(COVERAGE_PATH)}\n"
        f"  goal-only:       {t['goal_only']['covered']}/{t['statements']} "
        f"({t['goal_only']['pct']}%)\n"
        f"  full-statement:  {t['full_statement']['covered']}/{t['statements']} "
        f"({t['full_statement']['pct']}%)"
    )
    return 0


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
