"""Mechanical slice-verification harness — the reviewable 80%, as one command.

Motivation (docs/HANDOFF-v0.10-loop.md, user-directed): each adversarial
review was re-deriving the same mechanical checks at a cost of hundreds of
thousands of tokens. Everything that does not require judgment lives here;
a review then spends its budget only on what a script cannot do — attacking
the design, hand-adjudicating a sample of newly covered rows, and hunting a
novel false-positive class.

Usage (from a slice worktree, venv python):

    python scripts/verify_slice.py --base <merge-base-commit> [--goedel]
        [--skip-suite] [--skip-ledgers]

Checks (each prints PASS/FAIL; exit is nonzero if any FAIL):

  regen        check_regeneration.py + validate_nodes.py exit 0
  matcher      signature report: parse_problems / slot_schema_gaps / ladder
               violations all empty
  ledgers      every report + the two extract-based coverage JSONs regenerate
               git-clean (--goedel adds the 1.73M parquet re-run, minutes)
  audits       every *foreign_glyph* / *carrier_residual* audit field in the
               three coverage JSONs is 0
  dual-pass    per-row old-vs-new over miniF2F + Lean-workbook extracts
               (and Goedel parquets with --goedel): previously covered rows
               must stay covered; every loss is printed; gains are bucketed
               by the old refusal reason so the reviewer sees exactly where
               the delta came from
  acks         every "Registered acknowledgment" paragraph present in the
               base commit's test_decompose_channels.py docstring is intact
  guards       structural guard arithmetic recomputed live: absorption count
               floor (e_best > 4*a_best), generous ⊆ conservative dominance,
               recursive channel empty at defaults; GC4 aggregates and
               group_counts printed for the pin diff
  suite        full unittest discovery

The harness is deliberately conservative: it FAILs on any lost cover. A
slice that legitimately removes covers (a correction) runs with
--allow-losses, which downgrades the loss to a printed, counted disclosure —
the reviewer still sees every row.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PY = sys.executable
ENV_NOTE = {"PYTHONIOENCODING": "utf-8"}

RESULTS: list[tuple[str, str, str]] = []  # (check, PASS/FAIL/SKIP, detail)


def record(check: str, ok: bool | None, detail: str = "") -> None:
    status = "SKIP" if ok is None else ("PASS" if ok else "FAIL")
    RESULTS.append((check, status, detail))
    print(f"[{status}] {check}" + (f" — {detail}" if detail else ""))


def run_cmd(args: list[str], timeout: int = 3600) -> tuple[int, str]:
    import os

    env = dict(os.environ)
    env.update(ENV_NOTE)
    proc = subprocess.run(
        args, cwd=REPO, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env, timeout=timeout,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def git_show(base: str, relpath: str) -> str | None:
    code, out = run_cmd(["git", "show", f"{base}:{relpath}"])
    return out if code == 0 else None


def load_module_from_source(source: str, name: str):
    """Import a python module from source text (the base-commit classifier)."""
    tmp = Path(tempfile.mkdtemp(prefix="verify_slice_")) / f"{name}.py"
    tmp.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, tmp)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_head_gc():
    sys.path.insert(0, str(REPO / "scripts"))
    import grammar_coverage as gc_new  # noqa: E402

    return gc_new


# --------------------------------------------------------------------------
# checks
# --------------------------------------------------------------------------

def check_regen() -> None:
    ok = True
    details = []
    for script in ("check_regeneration.py", "validate_nodes.py"):
        code, out = run_cmd([PY, str(REPO / "scripts" / script)])
        if code != 0:
            ok = False
            details.append(f"{script} exit {code}: {out[-300:]}")
    record("regen", ok, "; ".join(details) if details else "seeds byte-identical, nodes validate")


def check_matcher() -> None:
    report = json.loads((REPO / "reports" / "signature_matches.json").read_text(encoding="utf-8"))
    probs = report.get("parse_problems", report.get("slot_vs_call_head_collisions"))
    gaps = report.get("slot_schema_gaps")
    ladder = report.get("ladder_violations")
    ok = not probs and not gaps and not ladder
    record(
        "matcher", ok,
        f"nodes={report.get('nodes_analyzed')} group_counts={report.get('group_counts')}",
    )


def check_ledgers(with_goedel: bool) -> None:
    steps = [
        [PY, str(REPO / "scripts" / "match_signatures.py"), "--write-report",
         str(REPO / "reports" / "signature_matches.json")],
        [PY, str(REPO / "scripts" / "specialize.py"), "--write-report",
         str(REPO / "reports" / "specializations.json")],
        [PY, str(REPO / "scripts" / "decompose.py"), "--write-report",
         str(REPO / "reports" / "decompositions.json")],
        [PY, str(REPO / "scripts" / "measure_compression.py"), "--write-report",
         str(REPO / "reports" / "compression.json")],
        [PY, str(REPO / "scripts" / "proof_correspondence.py"), "--write-report",
         str(REPO / "reports" / "proof_correspondence.json")],
        [PY, str(REPO / "scripts" / "ingest_minif2f.py")],
        [PY, str(REPO / "scripts" / "ingest_lean_workbook.py")],
    ]
    if with_goedel:
        steps.append([PY, str(REPO / "scripts" / "ingest_goedel_pset.py")])
    ok = True
    details = []
    for step in steps:
        code, out = run_cmd(step, timeout=7200)
        if code != 0:
            ok = False
            details.append(f"{Path(step[1]).name} exit {code}: {out[-300:]}")
    code, out = run_cmd(
        ["git", "status", "--porcelain", "--", "reports", "experiments",
         "data", "data_sources/derived"])
    if out.strip():
        ok = False
        details.append(f"NOT git-clean after regeneration:\n{out.strip()}")
    record("ledgers", ok, "; ".join(details) if details else
           ("all reports + coverage JSONs regenerate git-clean"
            + ("" if with_goedel else " (goedel skipped: --goedel to include)")))


def _audit_leaves(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _audit_leaves(v, f"{path}.{k}")
    elif isinstance(obj, list):
        return
    else:
        if "foreign_glyph" in path or "carrier_residual" in path:
            if isinstance(obj, (int, float)):
                yield path, obj


def check_audits() -> None:
    ok = True
    details = []
    for name in ("minif2f_coverage.json", "lean_workbook_coverage.json",
                 "goedel_pset_coverage.json"):
        doc = json.loads((REPO / "experiments" / name).read_text(encoding="utf-8"))
        for path, val in _audit_leaves(doc):
            if val != 0:
                ok = False
                details.append(f"{name}{path} = {val}")
    record("audits", ok, "; ".join(details) if details else "all audit fields 0")


def _classify_extract(gc_mod, doc: dict) -> dict[str, dict]:
    out = {}
    for stmt in doc["statements"]:
        r = gc_mod.classify(stmt)
        out[stmt["name"]] = r
    return out


def check_dual_pass(base: str, with_goedel: bool, allow_losses: bool) -> None:
    gc_new = load_head_gc()
    old_src = git_show(base, "scripts/grammar_coverage.py")
    if old_src is None:
        record("dual-pass", False, f"cannot read scripts/grammar_coverage.py at {base}")
        return
    gc_old = load_module_from_source(old_src, "gc_base")

    total_lost: list[str] = []
    gain_buckets: Counter = Counter()
    details = []

    # -- the two committed extracts ---------------------------------------
    for src in ("minif2f", "lean_workbook"):
        rel = f"data_sources/derived/{src}/statements.json"
        old_doc_txt = git_show(base, rel)
        if old_doc_txt is None:
            details.append(f"{src}: no extract at base (skipped)")
            continue
        old_rows = _classify_extract(gc_old, json.loads(old_doc_txt))
        new_rows = _classify_extract(
            gc_new, json.loads((REPO / rel).read_text(encoding="utf-8")))
        lost = [n for n, r in old_rows.items()
                if r["full_ok"] and not new_rows.get(n, {}).get("full_ok")]
        gained = [n for n, r in new_rows.items()
                  if r["full_ok"] and not old_rows.get(n, {}).get("full_ok")]
        vanished = [n for n in old_rows if n not in new_rows]
        for n in gained:
            old_r = old_rows.get(n)
            gain_buckets[old_r["full_reason"] if old_r else "newly_parsed"] += 1
        total_lost += [f"{src}:{n} ({old_rows[n]['full_reason'] if n in old_rows else '?'} "
                       f"-> {new_rows.get(n, {}).get('full_reason', 'VANISHED')})"
                       for n in lost]
        total_lost += [f"{src}:{n} (VANISHED from extract)"
                       for n in vanished if old_rows[n]["full_ok"]]
        details.append(f"{src}: old_cov={sum(r['full_ok'] for r in old_rows.values())} "
                       f"lost={len(lost)} gained={len(gained)} vanished={len(vanished)}")

    # -- Goedel parquets ---------------------------------------------------
    if with_goedel:
        try:
            import pyarrow.parquet as pq
        except ImportError:
            details.append("goedel: pyarrow missing (SKIPPED)")
            pq = None
        archive = REPO / "data_sources" / "archives" / "goedel-pset"
        if pq is not None and archive.exists():
            manifest = json.loads(
                (REPO / "data_sources" / "manifest.json").read_text(encoding="utf-8"))
            src_meta = next(s for s in manifest["sources"] if s["id"] == "hf-goedel-pset-v1")
            g_lost = g_old_cov = g_gained = rows = 0
            for fmeta in src_meta["files"]:
                pf = pq.ParquetFile(archive / fmeta["filename"])
                for batch in pf.iter_batches(
                        columns=["problem_id", "formal_statement"], batch_size=8192):
                    for pid, formal in zip(batch.column("problem_id").to_pylist(),
                                           batch.column("formal_statement").to_pylist()):
                        rows += 1
                        so = gc_old.parse_lean4_theorem(pid, formal or "")
                        sn = gc_new.parse_lean4_theorem(pid, formal or "")
                        ro = gc_old.classify(so) if so else None
                        rn = gc_new.classify(sn) if sn else None
                        o_ok = bool(ro and ro["full_ok"])
                        n_ok = bool(rn and rn["full_ok"])
                        if o_ok:
                            g_old_cov += 1
                        if o_ok and not n_ok:
                            g_lost += 1
                            if len(total_lost) < 200:
                                total_lost.append(
                                    f"goedel:{pid} ({ro['full_reason'] if ro else '?'} -> "
                                    f"{rn['full_reason'] if rn else 'UNPARSED'})")
                        if n_ok and not o_ok:
                            g_gained += 1
                            gain_buckets[ro["full_reason"] if ro else "newly_parsed"] += 1
            details.append(f"goedel: rows={rows} old_cov={g_old_cov} "
                           f"lost={g_lost} gained={g_gained}")
        elif pq is not None:
            details.append("goedel: parquets not on disk (SKIPPED — fetch or junction them)")

    ok = not total_lost or allow_losses
    if total_lost:
        print(f"  LOST rows ({len(total_lost)} shown, cap 200):")
        for line in total_lost[:200]:
            print(f"    {line}")
    print(f"  gains by old refusal reason: {dict(gain_buckets.most_common(12))}")
    record("dual-pass", ok,
           "; ".join(details) + (f"; LOSSES={len(total_lost)}"
                                 + (" (allowed by --allow-losses)" if allow_losses and total_lost else "")))


def check_acks(base: str) -> None:
    rel = "tests/test_decompose_channels.py"
    old = git_show(base, rel)
    new = (REPO / rel).read_text(encoding="utf-8")
    if old is None:
        record("acks", False, f"cannot read {rel} at {base}")
        return
    old_doc = old.split('"""', 2)[1] if '"""' in old else ""
    new_doc = new.split('"""', 2)[1] if '"""' in new else ""

    def norm(text: str) -> str:
        return " ".join(text.split())

    def blocks(doc: str) -> list[str]:
        # paragraph units: blank lines AND top-level "- " bullets both break,
        # so an acknowledgment glued to the next bullet stays one clean unit
        out, cur = [], []
        for line in doc.splitlines():
            if not line.strip() or line.startswith("- "):
                if cur:
                    out.append("\n".join(cur))
                cur = [line] if line.strip() else []
            else:
                cur.append(line)
        if cur:
            out.append("\n".join(cur))
        return out

    new_norm = norm(new_doc)
    missing = []
    for para in blocks(old_doc):
        if "acknowledgment" in para.lower() and norm(para) not in new_norm:
            missing.append(para.strip().splitlines()[0][:70])
    record("acks", not missing,
           f"{len(missing)} acknowledgment paragraph(s) altered/removed: {missing}"
           if missing else "all base acknowledgments intact (append-only)")


def check_guards() -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    from decompose import analyze, least_independent_channel  # noqa: E402,F401

    result = analyze(REPO / "data")
    decs = result["decompositions"]
    summary = result["channel_summary"]
    graph = summary["graph"]
    exact = [c for d in decs for c in d["constituents"] if c["grounded_via"] == "exact"]
    absorbed = [c for d in decs for c in d["constituents"]
                if c["channel"] == "pattern_absorption"]
    e_best = sum(1 for c in exact if c["channel"] == "external")
    a_best = sum(1 for c in absorbed if c["absorbed_from_channel"] == "external")
    generous = {cid for cid, blk in summary["corpora"].items() if blk["same_corpus_dominant"]}
    conserv = {cid for cid, blk in summary["corpora"].items()
               if blk["same_corpus_dominant_lower"]}
    recursive_sum = sum(d["channels"]["recursive"] for d in decs)
    problems = []
    if not (e_best > 4 * a_best):
        problems.append(f"absorption count floor broken: {e_best} <= 4*{a_best}")
    if not generous <= conserv:
        problems.append("generous dominance not a subset of conservative")
    if recursive_sum != 0:
        problems.append(f"recursive channel nonzero at defaults: {recursive_sum}")
    print(f"  GC4 aggregates: mean={graph['mean_groundedness']} "
          f"exact={sum(d['grounded_exact'] for d in decs)} "
          f"pattern={sum(d['grounded_via_pattern'] for d in decs)} "
          f"constituents={sum(1 for d in decs if d['constituents'])}")
    print(f"  absorption: e_best={e_best} a_best={a_best} "
          f"ratio={e_best / a_best:.2f}:1; dominance {len(generous)}/{len(conserv)}")
    record("guards", not problems, "; ".join(problems) if problems else
           "count floor, dominance subset, recursive-empty all hold")


def check_suite() -> None:
    code, out = run_cmd([PY, "-m", "unittest", "discover", "-s", "tests",
                         "-p", "test_*.py"], timeout=3600)
    tail = out.strip().splitlines()[-3:] if out.strip() else []
    record("suite", code == 0, " / ".join(tail))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True,
                    help="merge-base commit the slice builds on (for dual pass + acks)")
    ap.add_argument("--goedel", action="store_true",
                    help="include the 1.73M-row Goedel regeneration + dual pass (minutes)")
    ap.add_argument("--allow-losses", action="store_true",
                    help="corrections only: report lost covers without failing")
    ap.add_argument("--skip-suite", action="store_true")
    ap.add_argument("--skip-ledgers", action="store_true")
    args = ap.parse_args(argv)

    check_regen()
    if not args.skip_ledgers:
        check_ledgers(args.goedel)
    check_matcher()
    check_audits()
    check_dual_pass(args.base, args.goedel, args.allow_losses)
    check_acks(args.base)
    check_guards()
    if not args.skip_suite:
        check_suite()

    print("\n=== verify_slice summary ===")
    worst = 0
    for check, status, detail in RESULTS:
        print(f"  {status:4} {check}: {detail}")
        if status == "FAIL":
            worst = 1
    print("VERDICT: " + ("MECHANICAL CHECKS PASS — review may proceed to design "
                         "attack + row sample + novel-FP hunt" if worst == 0
                         else "MECHANICAL FAILURES — fix before review"))
    return worst


if __name__ == "__main__":
    sys.exit(main())
