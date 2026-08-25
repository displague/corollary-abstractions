#!/usr/bin/env python3
"""Write `experiments/exponent_bound.json` — 4c's before/after, both sides real.

ROADMAP-v0.20 §4c owes a before/after. The first version of that artifact
recorded `measured.before` as **null** while two commit messages claimed
"five cases before and after" (adversarial review, H3), which is the kind of
gap that makes every other number in a file harder to trust. This writer
exists so the before side is produced the same way the after side is —
executed, not remembered — and so the artifact has a `writer` field naming
the program that made it, on the precedent 4a and 4b set.

**How the before side is produced.** A temporary git worktree at a named
commit, and the cases are run in a CHILD interpreter rooted there, so
"before" is the committed evaluator rather than this one with a flag
flipped. The child reports the digest of the `evaluate.py` it loaded, and
the writer refuses to record a comparison whose two sides loaded the same
file — the same guard `exact_literals_served_diff.py` carries, for the same
reason.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARTIFACT = "experiments/exponent_bound.json"

#: The cases §4c and BACKLOG name, plus the escape the review found.
CASES = (
    "(100+1)^1000",
    "2^20000",
    "2^200000",
    "2^100",
    "3^5",
    "(10 ^ 4000) * (10 ^ 4000)",
)

_CHILD = r'''
import hashlib, json, sys, time
from pathlib import Path

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
cases = json.loads(sys.argv[3])
sys.path.insert(0, str(repo / "scripts"))

import evaluate as ev

loaded = hashlib.sha256(
    (repo / "scripts" / "evaluate.py").read_bytes().replace(b"\r\n", b"\n")
).hexdigest()

bound = getattr(ev, "MAX_RESULT_DIGITS", None)
ResourceBound = getattr(ev, "ResourceBound", None)

rows = {}
for expr in cases:
    started = time.perf_counter()
    row = {}
    try:
        result = ev.evaluate(expr)
        try:
            shown = result.formatted()
            row = {"outcome": "served", "digits": len(shown.lstrip("-"))}
        except Exception as exc:
            name = type(exc).__name__
            if ResourceBound is not None and isinstance(exc, ResourceBound):
                row = {"outcome": "refused_by_name",
                       "refusal": "ResourceBound",
                       "detail": str(exc)}
            else:
                row = {"outcome": "CRASHED_WHILE_PRINTING",
                       "exception": name, "detail": str(exc)[:160]}
    except Exception as exc:
        name = type(exc).__name__
        if ResourceBound is not None and isinstance(exc, ResourceBound):
            row = {"outcome": "refused_by_name", "refusal": "ResourceBound",
                   "detail": str(exc)}
        else:
            row = {"outcome": "eval_error", "exception": name,
                   "detail": str(exc)[:160]}
    row["ms"] = round((time.perf_counter() - started) * 1000, 3)
    rows[expr] = row

# The typed line, because that is the served surface the defect was on.
try:
    from harness import CoreSession, route_line

    session = CoreSession.boot(repo, offline=True, session_id="exponent-bound")
    for expr in cases:
        try:
            verdict = route_line(repo, session, expr)
            rows[expr]["route"] = verdict["route"]
            rows[expr]["status"] = verdict["status"]
        except Exception as exc:
            rows[expr]["route"] = "RAISED OUT OF route_line"
            rows[expr]["status"] = type(exc).__name__
        session.pending_candidates = ()
        session.pending_query = None
        session.context_hops = 0
        session.context_seen.clear()
except Exception as exc:  # pragma: no cover
    rows["_route_line_unavailable"] = str(exc)[:200]

out.write_text(json.dumps({
    "evaluate_sha256_lf": loaded,
    "bound": bound,
    "has_resource_bound_type": ResourceBound is not None,
    "cases": rows,
}, ensure_ascii=False), encoding="utf-8")
'''


def _run_side(tree: Path, tmp: Path, label: str) -> dict:
    child = tmp / f"child_{label}.py"
    child.write_text(_CHILD, encoding="utf-8")
    out = tmp / f"{label}.json"
    subprocess.run(
        [sys.executable, str(child), str(tree), str(out), json.dumps(list(CASES))],
        check=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return json.loads(out.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--before", default="main",
        help="the commit whose evaluator is the BEFORE side (default: main)",
    )
    parser.add_argument("--out", default=ARTIFACT)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        before_tree = tmp / "before-tree"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(before_tree), args.before],
            cwd=REPO, check=True, capture_output=True,
        )
        try:
            before = _run_side(before_tree, tmp, "before")
            after = _run_side(REPO, tmp, "after")
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(before_tree)],
                cwd=REPO, check=True, capture_output=True,
            )

    if before["evaluate_sha256_lf"] == after["evaluate_sha256_lf"]:
        print("REFUSING to write: both sides loaded one evaluate.py", file=sys.stderr)
        return 2

    crashed_before = sorted(
        expr for expr, row in before["cases"].items()
        if row.get("outcome") == "CRASHED_WHILE_PRINTING"
    )
    crashed_after = sorted(
        expr for expr, row in after["cases"].items()
        if row.get("outcome") == "CRASHED_WHILE_PRINTING"
    )

    record = {
        "run_id": "exponent_bound.v2",
        "roadmap": "docs/ROADMAP-v0.20.md §4c",
        "design": "docs/DESIGN-statements-that-run.md E0e",
        "writer": "scripts/measure_exponent_bound.py",
        "regenerate_with": f"python scripts/measure_exponent_bound.py --before {args.before}",
        "what_this_is": [
            "The before/after §4c owes, both sides EXECUTED. v1 of this file "
            "recorded `before` as null while two commit messages claimed "
            "'five cases before and after'; the adversarial review was right "
            "to call that a gap, and this is the repair.",
            "Each side runs in a child interpreter rooted at its own git "
            "worktree, so 'before' is the committed evaluator rather than "
            "this one with a flag flipped. Each child reports the digest of "
            "the evaluate.py it loaded and the writer refuses to record a "
            "comparison whose two sides loaded the same file.",
        ],
        "sides": {
            "before": {"commit": args.before,
                       "evaluate_sha256_lf": before["evaluate_sha256_lf"],
                       "bound": before["bound"],
                       "has_resource_bound_type": before["has_resource_bound_type"]},
            "after": {"commit": "working tree",
                      "evaluate_sha256_lf": after["evaluate_sha256_lf"],
                      "bound": after["bound"],
                      "has_resource_bound_type": after["has_resource_bound_type"]},
        },
        "the_bound": {
            "constant": "evaluate.MAX_RESULT_DIGITS",
            "value": after["bound"],
            "why_this_number": (
                "It is CPython's own int->str limit "
                "(sys.get_int_max_str_digits(), 4,300 by default). A bound "
                "BELOW it is a display policy about how long an answer may "
                "be — a different decision, arguable on its own terms. A "
                "bound ABOVE it still crashes on exactly the input the fix "
                "exists for. Registered as a constant rather than read live, "
                "so the refusal reproduces on a process that moved the cap."
            ),
            "checked_where": (
                "At the RESULT-FORMATTING boundary (Evaluation.formatted, "
                "Verification._fmt), plus an early per-node check on `^`."
            ),
            "why_both": (
                "H2: §4c bounded the `^` NODE, and the adversarial review "
                "escaped it in one line — `(10 ^ 4000) * (10 ^ 4000)` builds "
                "two admissible powers and multiplies them, so nothing "
                "exceeded a per-node bound and the PRINT raised the same "
                "uncaught ValueError §4c existed to abolish. A bound on one "
                "operator is a bound on one operator. The formatting "
                "boundary is the one every served value passes through by "
                "construction, so that is where the bound that HOLDS lives. "
                "The per-node check is kept and is not redundant: it refuses "
                "2^200000 before the power is built, so an unrenderable "
                "request costs a comparison rather than the arithmetic."
            ),
            "refusal_type": "evaluate.ResourceBound, a distinct subclass of EvalError",
            "why_a_distinct_type": (
                "A plain EvalError means the route cannot READ the line, and "
                "the router returns None so it falls through the chain. "
                "ResourceBound means the route read it, understood it, and "
                "refuses — so `_route_evaluate` returns a `refused` verdict "
                "naming the bound instead of ending in a generic dispatcher "
                "abstention."
            ),
        },
        "corrected_claim": {
            "v1_said": (
                "'4,300 is the only value at which accepted and renderable "
                "are the same set' — asserted as true BY CONSTRUCTION."
            ),
            "why_that_was_wrong": (
                "It was true of the `^` node and false of the evaluator: "
                "multiplication could build a value the bound had never "
                "seen. The set-equality claim is now true because the check "
                "sits at the rendering boundary — earned by where the check "
                "is, not by the number's arithmetic."
            ),
        },
        "a_divergence_from_the_brief_stated_rather_than_quietly_taken": {
            "the_brief_expected": (
                "§4c's landing note expected BOTH `(100+1)^1000` and the "
                "4,300-digit print-crash case to refuse cleanly."
            ),
            "what_this_implementation_does": (
                "`(100+1)^1000` is 2,005 digits — under the bound — so it is "
                "still SERVED, exactly and correctly. Only results past the "
                "bound refuse."
            ),
            "why": (
                "BACKLOG cites `(100+1)^1000` as EVIDENCE OF UNBOUNDEDNESS, "
                "not as a defect: it computes, it prints, and its value is "
                "right. A bound that refused it would be declining exact "
                "arithmetic this evaluator can do and render."
            ),
        },
        "measured": {"before": before["cases"], "after": after["cases"]},
        "crashed_while_printing": {
            "before": crashed_before,
            "after": crashed_after,
            "read_this_as": (
                "The defect, counted. A served path whose refusal is an "
                "uncaught exception is not refusing; it is crashing, and the "
                "two are different products."
            ),
        },
        "external_verifier_timeouts": {
            "why": (
                "BACKLOG: `grep -c timeout` over scripts/external_verifier.py "
                "returned 0, across four subprocess.run calls, under the cost "
                "argument the external-verifier lane rests on."
            ),
            "now": {
                "PROVER_TIMEOUT_SECONDS": 600,
                "VERSION_TIMEOUT_SECONDS": 60,
                "TYPECHECK_TIMEOUT_SECONDS": 300,
                "TESTS_TIMEOUT_SECONDS": 300,
            },
        },
        "non_claims": [
            "Not a security fix. Loopback-only, single user; ROADMAP-v0.20 §4 "
            "says so in as many words.",
            "Not a performance claim.",
        ],
    }
    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"before ({args.before}): crashed while printing = {crashed_before}")
    print(f"after  (working tree): crashed while printing = {crashed_after}")
    for expr in CASES:
        b = before["cases"].get(expr, {}).get("outcome")
        a = after["cases"].get(expr, {}).get("outcome")
        flag = "" if b == a else "   <- moved"
        print(f"  {expr:28s} {str(b):26s} -> {a}{flag}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
