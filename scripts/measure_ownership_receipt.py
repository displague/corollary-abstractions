#!/usr/bin/env python3
"""Time one `owns` turn end-to-end over HTTP, so 4a's claim gets a number.

ROADMAP-v0.20 §4a: the ownership double-lookup has been quoted at "~3.4 s"
across three release cycles **with no timing artifact behind it**. This
script is that artifact's writer. It runs one side of the measurement; the
committed record (`experiments/ownership_receipt_timing.json`) carries both,
written by `--merge` once the second side exists.

What is measured, stated precisely because a wall clock invites overreading:

* **End-to-end over the wire.** The number is the whole `POST
  /v1/chat/completions` round trip for `owns x ^ 2` on `corollary/kernel`,
  not an isolated call to `ownership.lookup`. That is the surface the claim
  was made about.
* **The session pool is OFF and the store memo is warmed first.** Both are
  request-independent costs that would otherwise land unevenly across the
  ten reps and swamp the effect being measured. The point is the receipt
  path, not the boot path.
* **Median of ten, with the full sample kept.** A median alone hides a
  bimodal distribution; every reading is committed so a reader can see the
  shape rather than trust the summary.

**Two modes, because the obvious one measures the wrong thing.** §4a asks for
`owns x ^ 2`, ten reps. Run literally, that sends ONE query ten times — and
on the *before* side the skin's `lru_cache` on the pure lookup (v0.17, added
precisely to blunt this defect) is warm from rep one onward, so nine of the
ten reps never pay the second lookup at all. The repeat reading therefore
compares a memo against a fix and shows almost nothing. It is kept, because
it is what was asked and because "no change on a repeated query" is a true
and useful statement about the shipped server.

`distinct` mode is the one that isolates the defect: ten DIFFERENT queries,
so the memo can never hit, which is the shape a task book of distinct
ownership questions actually has. Both modes are committed; quoting either
without the other would misdescribe the fix.

This is **not a performance claim** (§4a says so in as many words). It is
published to close an unmeasured entry. A change that made the number worse
would still be published — the artifact records what the run read.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import threading
import time
from http.client import HTTPConnection
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

#: The query the BACKLOG entry and §4a both name.
QUERY_LINE = "owns x ^ 2"

#: Ten DISTINCT template expressions, all of which parse and search the whole
#: graph. This list exists because the single-query reading turned out to
#: measure the wrong thing (see the module docstring's "two modes"), and the
#: same list runs on both sides so the comparison is like-for-like.
DISTINCT_QUERIES = (
    "x ^ 2", "x + y", "x * y", "x / y", "x - y",
    "x ^ 3", "sin ( x )", "cos ( x )", "sqrt ( x )", "log ( x )",
)
MODEL = "corollary/kernel"
DEFAULT_REPS = 10

ARTIFACT = "experiments/ownership_receipt_timing.json"


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        return "unknown"


def measure(reps: int, mode: str) -> dict:
    """One side, one mode, from a warmed server with no pool."""

    import serve_chat

    if mode == "distinct":
        queries = [f"owns {q}" for q in DISTINCT_QUERIES[:reps]]
    else:
        queries = [QUERY_LINE] * reps

    server, engine = serve_chat.build_server(REPO, 0, pool_size=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        headers = {"Content-Type": "application/json"}
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=600)

        def post(line: str) -> dict:
            body = json.dumps(
                {"model": MODEL, "messages": [{"role": "user", "content": line}]}
            )
            connection.request("POST", "/v1/chat/completions", body, headers)
            return json.loads(connection.getresponse().read().decode("utf-8"))

        # One unmeasured warm-up on a query that is NOT in the sample: it pays
        # the store parse and the ownership tree load, neither of which is
        # what this measures, without warming any sampled query's memo.
        warm = post("owns y ^ 2")

        samples_ms: list[float] = []
        final = warm
        for line in queries:
            started = time.perf_counter()
            final = post(line)
            samples_ms.append((time.perf_counter() - started) * 1000)
        connection.close()
    finally:
        server.shutdown()
        server.server_close()

    receipt = final["x_corollary"]["receipt"]
    return {
        "commit": _git("rev-parse", "HEAD"),
        "commit_subject": _git("log", "-1", "--format=%s"),
        "mode": mode,
        "queries": queries,
        "model": MODEL,
        "reps": reps,
        "warmup_reps": 1,
        "pool_size": 0,
        "samples_ms": [round(value, 3) for value in samples_ms],
        "median_ms": round(statistics.median(samples_ms), 3),
        "mean_ms": round(statistics.mean(samples_ms), 3),
        "min_ms": round(min(samples_ms), 3),
        "max_ms": round(max(samples_ms), 3),
        # The answer is part of the evidence: a faster turn that stopped
        # citing its hosts would not be the same turn.
        "status": final["x_corollary"]["status"],
        "receipt_keys": sorted(receipt),
        "hosts_cited": len(receipt.get("hosts", [])),
        "searched": receipt.get("searched"),
        "content_sha256": __import__("hashlib")
        .sha256(final["choices"][0]["message"]["content"].encode("utf-8"))
        .hexdigest(),
        "warmup_content_matches": (
            warm["choices"][0]["message"]["content"]
            == final["choices"][0]["message"]["content"]
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS)
    parser.add_argument(
        "--mode",
        choices=("repeat", "distinct"),
        required=True,
        help="repeat: one query x reps (what §4a literally asks, and what the "
        "pre-existing memo already covered). distinct: reps different "
        "queries, which is what isolates the double lookup.",
    )
    parser.add_argument(
        "--side",
        choices=("before", "after"),
        required=True,
        help="which side of 4a this reading is",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=f"where to write (default: {ARTIFACT}, merging the other side)",
    )
    args = parser.parse_args(argv)

    reading = measure(args.reps, args.mode)
    out = Path(args.out) if args.out else REPO / ARTIFACT

    record: dict = {}
    if out.is_file():
        record = json.loads(out.read_text(encoding="utf-8"))
    record.setdefault("run_id", "ownership.receipt.timing.v1")
    record.setdefault("roadmap", "docs/ROADMAP-v0.20.md")
    record.setdefault("gate", "ROADMAP-v0.20 §4a — the unmeasured claim, measured")
    record.setdefault(
        "what_this_is",
        [
            "The before/after reading §4a owes. The entry it closes had been "
            "quoted at ~3.4 s across three release cycles with no timing "
            "artifact behind it; this is that artifact.",
            "Measured end-to-end over HTTP for 'owns x ^ 2' on "
            "corollary/kernel, session pool OFF, store memo warmed by one "
            "unmeasured request, median of ten with every sample kept.",
            "NOT a performance claim (§4a). Published to close an unmeasured "
            "entry; a worse number would have been published too.",
        ],
    )
    record.setdefault("writer", "scripts/measure_ownership_receipt.py")
    record.setdefault(
        "host",
        {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
    )
    record.setdefault(args.mode, {})[args.side] = reading

    if {"before", "after"} <= set(record.get(args.mode, {})):
        before, after = record[args.mode]["before"], record[args.mode]["after"]
        record[args.mode]["delta"] = {
            "median_ms_before": before["median_ms"],
            "median_ms_after": after["median_ms"],
            "removed_ms": round(before["median_ms"] - after["median_ms"], 3),
            "speedup": (
                round(before["median_ms"] / after["median_ms"], 3)
                if after["median_ms"]
                else None
            ),
            "answer_unchanged": (
                before["content_sha256"] == after["content_sha256"]
            ),
            "receipt_unchanged": (
                before["receipt_keys"] == after["receipt_keys"]
                and before["hosts_cited"] == after["hosts_cited"]
                and before["searched"] == after["searched"]
            ),
        }

    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"{args.side}: median {reading['median_ms']:.1f} ms over {args.reps} reps")
    print(f"  samples : {reading['samples_ms']}")
    print(f"  hosts   : {reading['hosts_cited']} of {reading['searched']}")
    if "delta" in record.get(args.mode, {}):
        print(f"  delta   : {json.dumps(record[args.mode]['delta'])}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
