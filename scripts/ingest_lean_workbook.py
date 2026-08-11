#!/usr/bin/env python3
"""Deterministic Lean-workbook-proofs ingestion + grammar-coverage measurement.

The second real formal source for v0.9 item 1 (after miniF2F). Goedel-LM's
Lean-workbook-proofs is 29,750 Lean 4 theorems, each with a real tactic proof
(not `sorry`) — so unlike Goedel-Pset it can eventually ground a `verified_by`
link. It is MIT-licensed, so a derived statement extract may be committed. This
tool answers the same honest first question as the miniF2F slice — what fraction
expresses in the corpus grammar — plus a **duplicate-rate** measurement, which is
a real finding at this scale (Lean Workbook carries many restated problems).

Two stages, so the measurement regenerates in CI without the source parquet:

  extract   pinned parquet (SHA-256 verified against data_sources/manifest.json;
            fetched by hf_hub_download at the pinned revision, gitignored under
            data_sources/archives/lean-workbook/) -> committed
            data_sources/derived/lean_workbook/statements.json
  coverage  committed statements.json -> committed
            experiments/lean_workbook_coverage.json

The classifier is scripts/grammar_coverage.py, shared with miniF2F and made
dialect-aware (Lean 4 capitalizes namespaces: Real.sqrt, Finset, Nat.Prime; and
under `open Real Nat` the bare forms appear). The extract stage needs pyarrow to
read the parquet; the coverage stage needs only the standard library.
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
ARCHIVE_DIR = REPO_ROOT / "data_sources" / "archives" / "lean-workbook"
EXTRACT_PATH = REPO_ROOT / "data_sources" / "derived" / "lean_workbook" / "statements.json"
COVERAGE_PATH = REPO_ROOT / "experiments" / "lean_workbook_coverage.json"

MANIFEST_SOURCE_ID = "hf-goedel-lean-workbook-proofs"

# search, not match: each `full_proof` has an `import Mathlib ... open ...`
# preamble before the theorem line.
THEOREM_RE = re.compile(r"(?m)^theorem[ \t]+(\S+)")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_manifest_source() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for src in manifest["sources"]:
        if src["id"] == MANIFEST_SOURCE_ID:
            return src
    raise KeyError(f"manifest source `{MANIFEST_SOURCE_ID}` not found")


# --------------------------------------------------------------------------
# Stage 1: extract  (parquet full_proof -> statement signatures)
# --------------------------------------------------------------------------

def parse_full_proof(problem_id: str, full_proof: str) -> dict | None:
    """Split one Lean 4 `theorem` (statement part only) into name/binders/goal.
    The proof after `:=` is discarded; `problem_id` maps back to the pinned
    parquet for the later authoring/verify phase."""
    text = gc.strip_comments(full_proof)
    m = THEOREM_RE.search(text)
    if not m:
        return None
    sig = gc.split_signature(text[m.end() :], ":=")
    if sig is None:
        return None
    binders_text, goal, lets = sig
    if not goal:
        return None
    b = gc.parse_binders(binders_text)
    goal_lets = gc.apply_goal_lets(b, lets)
    if goal_lets is None:
        return None
    out = {
        "name": problem_id,
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


def _read_parquet_rows(path: Path) -> list[dict]:
    import pyarrow.parquet as pq  # extract-stage-only dependency

    table = pq.read_table(path, columns=["problem_id", "full_proof"])
    return table.to_pylist()


def run_extract() -> int:
    src = _load_manifest_source()
    fmeta = src["files"][0]
    path = ARCHIVE_DIR / fmeta["filename"]
    if not path.exists():
        print(
            f"MISSING: {path} not present. Fetch the pinned source first:\n"
            f"  python scripts/fetch_sources.py --fetch {src['id']}",
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

    rows = _read_parquet_rows(path)
    if len(rows) != fmeta["row_count"]:
        print(
            f"ROW COUNT MISMATCH: parquet has {len(rows)}, manifest pins "
            f"{fmeta['row_count']}. Refusing.",
            file=sys.stderr,
        )
        return 4

    statements: list[dict] = []
    unparsed: list[str] = []
    for row in rows:
        parsed = parse_full_proof(row["problem_id"], row["full_proof"])
        if parsed is None:
            unparsed.append(row["problem_id"])
        else:
            statements.append(parsed)
    statements.sort(key=lambda s: s["name"])
    unparsed.sort()

    doc = {
        "generated_by": "scripts/ingest_lean_workbook.py extract",
        "source": {
            "id": src["id"],
            "url": src["url"],
            "hf_repo": src["hf_repo"],
            "hf_revision": src["hf_revision"],
            "license": src["license"],
            "attribution": "Lean-workbook-proofs (c) Goedel-LM, MIT License. Proofs by "
            "Goedel-Prover (Lin et al., 2025, arXiv:2502.07640); problems from Lean "
            "Workbook. Statement signatures extracted; proofs omitted (retrievable by "
            "problem_id from the pinned parquet).",
            "file": {
                "filename": fmeta["filename"],
                "sha256": fmeta["sha256"],
                "row_count": fmeta["row_count"],
            },
        },
        "row_count": len(rows),
        "parsed_count": len(statements),
        "unparsed_count": len(unparsed),
        "unparsed_sample": unparsed[:25],
        "statements": statements,
    }
    EXTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    gc.write_json(EXTRACT_PATH, doc)
    print(
        f"extract OK: {len(statements)} parsed / {len(rows)} rows "
        f"({len(unparsed)} unparsed) -> {gc.rel(EXTRACT_PATH)}"
    )
    return 0


# --------------------------------------------------------------------------
# Stage 2: coverage  (statement signatures -> grammar-coverage + duplicate rate)
# --------------------------------------------------------------------------

def _dup_stats(statements: list[dict], covered_names: set[str]) -> dict:
    """Exact-duplicate rate keyed on the whitespace-normalized goal string.
    (Alpha-renamed / structural duplicates are a deeper, twin-matcher measure,
    deliberately deferred; this is the honest lower bound on redundancy.)"""
    from collections import Counter

    def _full_goal(s: dict) -> str:
        return "\n".join([*s.get("goal_lets", []), s["goal"]])

    goal_counts: Counter = Counter(_full_goal(s) for s in statements)
    covered_goals = [_full_goal(s) for s in statements if s["name"] in covered_names]
    covered_counts: Counter = Counter(covered_goals)
    total = len(statements)
    unique = len(goal_counts)
    top = sorted(goal_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return {
        "keyed_on": "exact whitespace-normalized goal string",
        "total_statements": total,
        "unique_goals": unique,
        "duplicate_statements": total - unique,
        "duplicate_rate_pct": gc.pct(total - unique, total),
        "covered_statements": len(covered_goals),
        "unique_covered_goals": len(covered_counts),
        "note": "structural (alpha-renamed) duplicates are not counted here; they "
        "are a twin-matcher measure deferred to the authoring phase.",
        "most_repeated_goals": [
            {"count": c, "goal": g[:160]} for g, c in top if c > 1
        ],
    }


def build_coverage(doc: dict) -> dict:
    """Pure function: extract doc -> coverage doc, guarded byte-for-byte."""
    statements = doc["statements"]
    results = [gc.classify(s) for s in statements]
    results.sort(key=lambda r: r["name"])

    parsed = len(results)
    row_count = doc["row_count"]
    goal_ok = sum(1 for r in results if r["goal_ok"])
    full_ok = sum(1 for r in results if r["full_ok"])
    covered_names = {r["name"] for r in results if r["full_ok"]}

    # Denominator honesty: report coverage over ALL rows (unparsed rows are an
    # untranslatable category), and also over parsed statements.
    goal_reasons = [r["goal_reason"] for r in results]
    full_reasons = [r["full_reason"] for r in results]
    unparsed = doc["unparsed_count"]
    full_reasons_all = full_reasons + ["parse_failed"] * unparsed
    goal_reasons_all = goal_reasons + ["parse_failed"] * unparsed

    coverage = {
        "generated_by": "scripts/ingest_lean_workbook.py coverage",
        "source_extract": {
            "path": gc.rel(EXTRACT_PATH),
            "hf_revision": doc["source"]["hf_revision"],
            "row_count": row_count,
            "parsed_count": parsed,
        },
        "grammar": {
            "shared_classifier": "scripts/grammar_coverage.py (same heads as miniF2F; "
            "dialect-aware for Lean 4).",
            "supported_heads": [
                "relations(= ≠ < ≤ > ≥ ↔)",
                "MEET(∧) JOIN(∨) NEG(¬) IMPLIES(→)",
                "arithmetic(+ - * / ^)",
                "SQRT LOG EXP SIN COS TAN",
                "predicates EVEN ODD PRIME IRRATIONAL (arity 1, bare application)",
                "prop constants TRUTH FALSITY; let-bindings as definitional =",
            ],
            "explicit_gaps_no_head_in_corpus": [
                "modulo(%, [MOD n])", "divides(∣)", "absolute-value/norm(|·|, ∥·∥)",
                "tuple/pair constructor", "gcd/lcm", "big operators(∑ ∏)",
                "quantifiers(∀ ∃) in goal", "unknown-function slot",
                "coprime(2-ary)", "Function.Injective/Surjective, Monotone, …",
            ],
        },
        "totals": {
            "rows": row_count,
            "parsed": parsed,
            "unparsed": unparsed,
            "goal_only": {
                "covered": goal_ok,
                "pct_of_rows": gc.pct(goal_ok, row_count),
                "pct_of_parsed": gc.pct(goal_ok, parsed),
            },
            "full_statement": {
                "covered": full_ok,
                "pct_of_rows": gc.pct(full_ok, row_count),
                "pct_of_parsed": gc.pct(full_ok, parsed),
            },
        },
        "duplicate_analysis": _dup_stats(statements, covered_names),
        "goal_only_untranslatable_reasons": gc.tally(goal_reasons_all),
        "full_statement_untranslatable_reasons": gc.tally(full_reasons_all),
        "covered_full_statement_names": [
            r["name"] for r in results if r["full_ok"]
        ],
    }
    return coverage


def run_coverage() -> int:
    if not EXTRACT_PATH.exists():
        print(f"MISSING extract: {gc.rel(EXTRACT_PATH)}. Run `extract` first.", file=sys.stderr)
        return 2
    doc = json.loads(EXTRACT_PATH.read_text(encoding="utf-8"))
    coverage = build_coverage(doc)
    gc.write_json(COVERAGE_PATH, coverage)
    t = coverage["totals"]
    d = coverage["duplicate_analysis"]
    print(
        f"coverage OK -> {gc.rel(COVERAGE_PATH)}\n"
        f"  parsed:          {t['parsed']}/{t['rows']} rows\n"
        f"  goal-only:       {t['goal_only']['covered']}/{t['rows']} "
        f"({t['goal_only']['pct_of_rows']}% of rows)\n"
        f"  full-statement:  {t['full_statement']['covered']}/{t['rows']} "
        f"({t['full_statement']['pct_of_rows']}% of rows)\n"
        f"  duplicate rate:  {d['duplicate_rate_pct']}% "
        f"({d['unique_goals']} unique goals)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "stage",
        choices=["extract", "coverage", "all"],
        help="extract: parquet->statements.json (needs pinned parquet + pyarrow); "
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
