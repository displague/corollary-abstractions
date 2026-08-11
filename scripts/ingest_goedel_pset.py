#!/usr/bin/env python3
"""Goedel-Pset-v1 grammar-coverage at scale (1.73M Lean 4 statements).

The third v0.9 ingestion-coverage data point, and the SCALE test: does the
grammar's reach hold at ~58x the Lean-workbook size, and how redundant is a
formal set this large? Goedel-Pset-v1 is 1.73M formalized Lean 4 statements
(MIT), Numina-derived; its proofs are `sorry` (unverified), so it measures reach
and redundancy only — it cannot ground a verified_by link (Lean-workbook is the
source for that).

Single-pass, AGGREGATE-ONLY by necessity: a 1.73M-row per-statement extract
would be a ~300 MB JSON, too large to commit, so unlike the miniF2F /
Lean-workbook slices this source commits ONLY the small aggregate measurement.
The reproducibility anchor is the 4 pinned parquets (SHA-256 + HF revision in the
manifest); the number regenerates from them with pyarrow (not stdlib-CI-
regenerable from a committed extract — the honest tradeoff at this size). The
false-positive audit is baked into the artifact as self-checking fields
(`covered_foreign_glyph_count` / `covered_carrier_residual_count`, both must be 0
by construction — a nonzero value means the classifier let a bad statement
through).

The classifier is the shared, carrier-aware scripts/grammar_coverage.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grammar_coverage as gc  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "data_sources" / "manifest.json"
ARCHIVE_DIR = REPO_ROOT / "data_sources" / "archives" / "goedel-pset"
COVERAGE_PATH = REPO_ROOT / "experiments" / "goedel_pset_coverage.json"

MANIFEST_SOURCE_ID = "hf-goedel-pset-v1"

# Whitelist for the covered-set foreign-glyph audit (matches the committed tests).
# v0.10 quantifier slice: ∀ ∃ and the binder comma are now grammar glyphs (a
# covered `∀ x : ℝ, ...` carries all three). `!` is NOT whitelisted — only the
# two-character token `∃!` is, via the targeted pre-strip in
# `_has_foreign_glyph` — so a stray factorial `!` in a covered row still trips
# the audit. Braces (implicit binders `{x : ℝ}`) stay OUTSIDE the whitelist on
# purpose: if a covered row ever carries them the audit should say so first.
_ALLOWED = set(
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "+-*/^=<>≤≥≠∧∨¬→↔() .:_'↑ℝℕℤℚπ√∀∃,"
)
_ALLOWED |= {chr(c) for c in range(0x2080, 0x209D)}  # subscripts
_ALLOWED |= {chr(c) for c in range(0x2070, 0x2080)}  # superscripts
_ALLOWED |= set("¹²³⁄ℓℯ")  # frac slash, script l (var), euler e (const)
_ALLOWED |= {chr(c) for c in range(0x1D62, 0x1D6B)}  # phonetic subscript modifiers (var names)
_ALLOWED |= {chr(c) for c in range(0x0370, 0x0400)}  # Greek block
_ALLOWED |= {chr(c) for c in range(0x0400, 0x0500)}  # Cyrillic (var names)
_FRAC_EXP_RE = re.compile(r"\^\s*\([^)]*/")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _goal_key(stmt: dict) -> bytes:
    # a let-goal's identity is its bindings PLUS its body: keying on the body
    # alone would collapse distinct let-statements (the old truncated parse did
    # exactly that, deflating unique_goals).
    full = "\n".join([*stmt.get("goal_lets", []), stmt["goal"]])
    return hashlib.blake2b(full.encode("utf-8"), digest_size=16).digest()


def _load_manifest_source() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for src in manifest["sources"]:
        if src["id"] == MANIFEST_SOURCE_ID:
            return src
    raise KeyError(f"manifest source `{MANIFEST_SOURCE_ID}` not found")


# Implicit binder groups directly after a quantifier (`∀ {x y : ℝ},`) are the
# same quantification as explicit ones; their braces become parens for the
# glyph audit ONLY in that position, and only when no set-builder `|` is
# inside — a brace anywhere else in a covered row still trips the audit.
_IMPLICIT_BINDER_RE = re.compile(r"([∀∃]\s*)\{([^{}|]*)\}")


def _audit_normalize(txt: str) -> str:
    # `∃!` is the unique-existence token (covered via its ExistsUnique
    # expansion); a bare `!` is factorial and must keep tripping the audit.
    # Strict-implicit brackets ⦃⦄ are binder brackets and NOTHING else in
    # Lean, so they normalize to parens unconditionally (32 realized covers).
    txt = txt.replace("∃!", "∃").replace("⦃", "(").replace("⦄", ")")
    return _IMPLICIT_BINDER_RE.sub(r"\1(\2)", txt)


def _has_foreign_glyph(stmt: dict) -> bool:
    for txt in [stmt["goal"], *stmt.get("goal_lets", []), *stmt["hyps"]]:
        if set(_audit_normalize(txt)) - _ALLOWED:
            return True
    return False


def _carrier_residual(stmt: dict) -> bool:
    """A covered statement that STILL carries an integer-only division/monus/frac
    exponent — must never happen; this is the classifier self-check.

    SEGMENT-LOCAL, like the classifier's own carrier rule: a field signal in one
    segment must not excuse a `/`/`⁻¹` in another. (The earlier concatenated
    form was blind to exactly the cross-segment shielding the adversarial
    review caught, so it could never flag the class it existed to catch.)

    Quantifier-aware since the v0.10 slice: a segment's own binder can declare
    the field carrier (`∃ last : Rat, last = 1 /. 2` under an ℕ theorem
    binder — the audit's first hit). The prefix is re-parsed with the shared
    extractor so the audit sees the same segmentation the classifier saw, but
    the carrier VERDICT below stays the audit's own independent regex logic."""
    if stmt.get("has_field_carrier"):
        return False
    if not (stmt.get("has_nat_carrier") or stmt.get("has_int_carrier")):
        return False
    for txt in [stmt["goal"], *stmt.get("goal_lets", []), *stmt["hyps"]]:
        q = gc.extract_quantifier_prefix(txt)
        if q is not None and q[0] == "ok":
            _, check_text, _names, carriers = q
            if "field" in carriers:
                continue  # the segment's own binder declares the field carrier
            txt = check_text
        if gc._FIELD_SIGNAL_RE.search(txt):
            continue
        if "/" in txt or "⁻¹" in txt or _FRAC_EXP_RE.search(txt):
            return True
    return False


def run() -> int:
    src = _load_manifest_source()
    files = src["files"]
    # verify every pinned parquet before reading a single row
    for fmeta in files:
        path = ARCHIVE_DIR / fmeta["filename"]
        if not path.exists():
            print(
                f"MISSING: {path}. Fetch first:\n"
                f"  python scripts/fetch_sources.py --fetch {src['id']}",
                file=sys.stderr,
            )
            return 2
        digest = _sha256_file(path)
        if digest != fmeta["sha256"]:
            print(
                f"SHA MISMATCH for {fmeta['filename']}: expected {fmeta['sha256']}, "
                f"got {digest}. Refusing.",
                file=sys.stderr,
            )
            return 3

    import pyarrow.parquet as pq  # extract-stage-only dependency

    rows = parsed = unparsed = goal_ok = full_ok = 0
    goal_reasons: Counter = Counter()
    full_reasons: Counter = Counter()
    all_goal_keys: set[bytes] = set()
    covered_goal_keys: set[bytes] = set()
    covered_sample: list[str] = []
    audit_foreign = audit_carrier = 0

    for fmeta in files:
        path = ARCHIVE_DIR / fmeta["filename"]
        pf = pq.ParquetFile(path)
        file_rows = 0
        for batch in pf.iter_batches(columns=["problem_id", "formal_statement"], batch_size=8192):
            ids = batch.column("problem_id").to_pylist()
            stmts = batch.column("formal_statement").to_pylist()
            for pid, formal in zip(ids, stmts):
                rows += 1
                file_rows += 1
                st = gc.parse_lean4_theorem(pid, formal or "")
                if st is None:
                    unparsed += 1
                    continue
                parsed += 1
                r = gc.classify(st)
                all_goal_keys.add(_goal_key(st))
                if r["goal_ok"]:
                    goal_ok += 1
                else:
                    goal_reasons[r["goal_reason"]] += 1
                if r["full_ok"]:
                    full_ok += 1
                    covered_goal_keys.add(_goal_key(st))
                    if len(covered_sample) < 300:
                        covered_sample.append(pid)
                    if _has_foreign_glyph(st):
                        audit_foreign += 1
                    if _carrier_residual(st):
                        audit_carrier += 1
                else:
                    full_reasons[r["full_reason"]] += 1
        if file_rows != fmeta["row_count"]:
            print(
                f"ROW COUNT MISMATCH for {fmeta['filename']}: read {file_rows}, "
                f"manifest pins {fmeta['row_count']}. Refusing.",
                file=sys.stderr,
            )
            return 4

    unique_goals = len(all_goal_keys)
    coverage = {
        "generated_by": "scripts/ingest_goedel_pset.py",
        "source": {
            "id": src["id"],
            "url": src["url"],
            "hf_repo": src["hf_repo"],
            "hf_revision": src["hf_revision"],
            "license": src["license"],
            "attribution": "Goedel-Pset-v1 (c) Goedel-LM, MIT License. Formalized by "
            "Goedel-Prover (Lin et al., 2025, arXiv:2502.07640); problems from NuminaMath. "
            "Proofs are `sorry` (unverified). Aggregate measurement only; no statements "
            "redistributed.",
            "files": [
                {"filename": f["filename"], "sha256": f["sha256"], "row_count": f["row_count"]}
                for f in files
            ],
        },
        "note": "Aggregate-only (1.73M statements would be a ~300 MB extract). Regenerate "
        "from the pinned parquets with pyarrow; not stdlib-CI-regenerable. Proofs are "
        "`sorry`, so this measures grammar reach + redundancy, not verifiability.",
        "totals": {
            "rows": rows,
            "parsed": parsed,
            "unparsed": unparsed,
            "goal_only": {"covered": goal_ok, "pct_of_rows": gc.pct(goal_ok, rows)},
            "full_statement": {"covered": full_ok, "pct_of_rows": gc.pct(full_ok, rows)},
        },
        "duplicate_analysis": {
            "keyed_on": "blake2b-128 of the whitespace-normalized goal string",
            "total_parsed": parsed,
            "unique_goals": unique_goals,
            "duplicate_statements": parsed - unique_goals,
            "duplicate_rate_pct": gc.pct(parsed - unique_goals, parsed),
            "unique_covered_goals": len(covered_goal_keys),
        },
        "audit": {
            "covered_foreign_glyph_count": audit_foreign,
            "covered_carrier_residual_count": audit_carrier,
            "note": "both must be 0; nonzero means the classifier let a bad statement "
            "into the covered set (a regression).",
        },
        "goal_only_untranslatable_reasons": gc.tally(list(goal_reasons.elements())),
        "full_statement_untranslatable_reasons": gc.tally(list(full_reasons.elements())),
        "covered_sample_first_300": covered_sample,
    }
    gc.write_json(COVERAGE_PATH, coverage)
    t = coverage["totals"]
    d = coverage["duplicate_analysis"]
    print(
        f"coverage OK -> {gc.rel(COVERAGE_PATH)}\n"
        f"  parsed:          {parsed}/{rows} rows ({unparsed} unparsed)\n"
        f"  goal-only:       {goal_ok}/{rows} ({t['goal_only']['pct_of_rows']}%)\n"
        f"  full-statement:  {full_ok}/{rows} ({t['full_statement']['pct_of_rows']}%)\n"
        f"  duplicate rate:  {d['duplicate_rate_pct']}% "
        f"({unique_goals} unique goals; {len(covered_goal_keys)} unique covered)\n"
        f"  audit:           foreign_glyphs={audit_foreign} carrier_residual={audit_carrier}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
