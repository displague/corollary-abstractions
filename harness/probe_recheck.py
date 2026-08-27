#!/usr/bin/env python3
"""The program-absent rechecker for the C-E3 probe receipts.

This file is **harness code, not program code**. It lives outside `scripts/`
because `scripts/` is the tree the harness renames away, and it imports
nothing from this repository — the whole point of COLD RECEIPT is that this
procedure runs with the program gone. It is stdlib-only and runs under
`python -S -I`, so no `site-packages` (and therefore no `.venv`) is on its
path.

It executes `cold/reconstruction_rule.json`'s five steps against a bundle:

1. take each row's `substituted_proposition` verbatim;
2. substitute into the two templates the rule publishes;
3. sha256 the LF form and compare against the recorded `source_sha256`;
4. write `<tmp>/Probe.lean` and run `[<checker...>, <that path>]` with
   `cwd=<tmp>`, no flags, environment inherited;
5. map the two exit codes to a verdict and compare against the recorded one.

**Every row is evaluated; there is no short-circuit.** A rechecker that
stopped at the first mismatch would make B6's 200 scrambled bundles cost
almost nothing, and the arm the design budgeted at an hour would have been
softened by an implementation detail rather than by a finding.

Exit codes: 0 the bundle re-checks, 1 it does not, 2 a listed dependency is
missing (B4's FAIL LOUD, which names it).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PASS, FAIL, MISSING_DEPENDENCY = 0, 1, 2


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _verdict(positive_accepted: bool, negative_accepted: bool) -> str:
    if positive_accepted and negative_accepted:
        return "did_not_reduce"
    if positive_accepted:
        return "refuted_counterexample"
    if negative_accepted:
        return "confirmed_counterexample"
    return "did_not_reduce"


def recheck(
    bundle: Path,
    checker_argv: list[str],
    timeout: int,
    skip_invocation: bool = False,
) -> dict:
    rule = json.loads((bundle / "reconstruction_rule.json").read_text("utf-8"))
    receipts = json.loads((bundle / "receipts.json").read_text("utf-8"))

    step2 = next(s for s in rule["steps"] if s["step"] == 2)
    positive_template = step2["positive_template"]
    negative_template = step2["negative_template"]

    rows = [row for row in receipts["rows"] if "checker_receipt" in row]
    results = []
    started = time.time()
    invocations = 0

    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "Probe.lean"
        for index, row in enumerate(rows):
            receipt = row["checker_receipt"]
            proposition = row["substituted_proposition"]
            row_result = {
                "row_index": index,
                "statement_id": row.get("statement_id"),
                "checks": {},
            }
            accepted = {}
            for side, template, key in (
                ("positive", positive_template, "positive_probe"),
                ("negative", negative_template, "negative_probe"),
            ):
                text = template.format(prop=proposition)
                recomputed = _digest(text)
                recorded = receipt[key]["source_sha256"]
                row_result["checks"][f"{side}_digest"] = {
                    "recomputed": recomputed,
                    "recorded": recorded,
                    "ok": recomputed == recorded,
                }
                if skip_invocation:
                    accepted[side] = None
                    continue
                probe.write_text(text, encoding="utf-8")
                try:
                    completed = subprocess.run(
                        [*checker_argv, str(probe)],
                        cwd=tmp,
                        capture_output=True,
                        timeout=timeout,
                    )
                except FileNotFoundError as exc:
                    return {
                        "outcome": "MISSING_DEPENDENCY",
                        "missing_dependency": {
                            "name": "lean.exe",
                            "role": "the pinned external checker this "
                            "procedure invokes by path",
                            "argv_attempted": [*checker_argv, str(probe)],
                            "error": f"{type(exc).__name__}: {exc}",
                        },
                        "rows_evaluated": index,
                        "elapsed_seconds": round(time.time() - started, 3),
                    }
                except subprocess.TimeoutExpired as exc:
                    completed = None
                    row_result["checks"][f"{side}_exit_code"] = {
                        "recomputed": None,
                        "recorded": receipt[key]["returncode"],
                        "ok": False,
                        "failure": f"TimeoutExpired after {exc.timeout}s",
                    }
                    accepted[side] = None
                    invocations += 1
                    continue
                invocations += 1
                row_result["checks"][f"{side}_exit_code"] = {
                    "recomputed": completed.returncode,
                    "recorded": receipt[key]["returncode"],
                    "ok": completed.returncode == receipt[key]["returncode"],
                }
                accepted[side] = completed.returncode == 0

            if not skip_invocation and None not in accepted.values():
                derived = _verdict(accepted["positive"], accepted["negative"])
                row_result["checks"]["verdict"] = {
                    "recomputed": derived,
                    "recorded": row.get("decide_verdict"),
                    "ok": derived == row.get("decide_verdict"),
                }
            row_result["ok"] = all(
                check["ok"] for check in row_result["checks"].values()
            )
            results.append(row_result)

    passed = bool(results) and all(row["ok"] for row in results)
    return {
        "outcome": "PASS" if passed else "FAIL",
        "rows_evaluated": len(results),
        "rows_ok": sum(1 for row in results if row["ok"]),
        "checker_invocations": invocations,
        "elapsed_seconds": round(time.time() - started, 3),
        "first_failures": [
            {
                "row_index": row["row_index"],
                "statement_id": row["statement_id"],
                "failed_checks": sorted(
                    name for name, c in row["checks"].items() if not c["ok"]
                ),
            }
            for row in results
            if not row["ok"]
        ][:5],
        "rows": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument(
        "--checker-argv",
        required=True,
        help="JSON list: the argv prefix the probe path is appended to",
    )
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--digests-only",
        action="store_true",
        help="run steps 1-3 only; used to price what the invocation adds",
    )
    args = parser.parse_args(argv)

    checker_argv = json.loads(args.checker_argv)
    # B4's FAIL LOUD has to fire before any row is evaluated when the
    # dependency is simply not there, and it has to NAME it.
    if not args.digests_only:
        head = Path(checker_argv[0])
        if not head.is_file():
            report = {
                "outcome": "MISSING_DEPENDENCY",
                "missing_dependency": {
                    "name": "lean.exe",
                    "role": "the pinned external checker this procedure "
                    "invokes by path",
                    "resolved_to": str(head),
                    "error": "the listed dependency is not present at the "
                    "path the procedure resolves it to",
                },
            }
            if args.out:
                args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(
                "FAIL-LOUD: missing dependency lean.exe "
                f"(resolved to {head}); the procedure cannot run"
            )
            return MISSING_DEPENDENCY

    report = recheck(args.bundle, checker_argv, args.timeout, args.digests_only)
    if args.out:
        args.out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    if report["outcome"] == "MISSING_DEPENDENCY":
        missing = report["missing_dependency"]
        print(
            f"FAIL-LOUD: missing dependency {missing['name']} "
            f"({missing['error']}); the procedure cannot run"
        )
        return MISSING_DEPENDENCY
    print(
        f"{report['outcome']} rows {report['rows_ok']}/{report['rows_evaluated']} "
        f"invocations {report['checker_invocations']} "
        f"elapsed {report['elapsed_seconds']}s"
    )
    return PASS if report["outcome"] == "PASS" else FAIL


if __name__ == "__main__":
    sys.exit(main())
