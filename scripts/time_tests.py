#!/usr/bin/env python3
"""Per-test wall-clock, because every explanation of the slow gate was wrong.

Three times during v0.12 a reason was given for the ~10-hour suite and three
times it was folklore:

1. "several tests each reload the 12k graph" — only FOUR modules rebuild it,
   and they cache in `setUpClass`.
2. "the cost is the eight torch modules" — the modules actually observed
   crawling (`test_controller`, `test_ask`, `test_corpus_analogy_split`)
   contain no torch, no epochs, no training.
3. "I don't know" — correct, and the reason it stayed unknown is that
   `unittest -v` prints test NAMES and not DURATIONS, so every estimate came
   from a proxy: CPU counters, progress marks, module counts.

This prints the durations. It is deliberately tiny and has no dependencies
beyond the standard library, so it can be pointed at one suspicious module
during a release without competing for much.

    python scripts/time_tests.py tests.test_ask
    python scripts/time_tests.py --top 25 tests.test_controller tests.test_ask
    python scripts/time_tests.py --json timings.json tests.test_probes

The output is a ranked table, because the question is never "how long did
the suite take" — it is "which handful of tests are the suite".
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import unittest
from pathlib import Path

# `python -m unittest` puts the repo root on sys.path; running this as a file
# does not, so `tests.test_x` would not import. Both the root (for `tests`)
# and `scripts/` (for what the tests import) are needed.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))


class TimingResult(unittest.TextTestResult):
    """Records elapsed per test, from `startTest` to `stopTest`.

    **Fixture time is NOT captured, and the gap is the point.** `unittest`
    runs `setUpClass` and `setUpModule` before any `startTest`, so their cost
    lands in no test's row. An earlier version of this docstring claimed the
    cost was attributed to the first test of the class; that was wrong, and
    the first real run proved it: `test_corpus_analogy_split` summed to
    6,064.8s across its tests while the module took 10,765.0s. The missing
    ~4,700s is class fixtures.

    So read the output as two numbers, not one. `total` is what the module
    costs a gate. The sum of the rows is what the *tests* cost. When they
    diverge, the difference is fixture work, and no amount of speeding up
    individual tests will touch it.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timings: list[tuple[str, float, str]] = []
        self._started: float | None = None

    def startTest(self, test) -> None:
        self._started = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test) -> None:
        elapsed = time.perf_counter() - (self._started or time.perf_counter())
        self.timings.append((test.id(), elapsed, test.__class__.__module__))
        super().stopTest(test)


class TimingRunner(unittest.TextTestRunner):
    resultclass = TimingResult


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="+", help="module or test ids")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args(argv)

    suite = unittest.defaultTestLoader.loadTestsFromNames(args.targets)
    runner = TimingRunner(verbosity=0)
    started = time.perf_counter()
    result = runner.run(suite)
    total = time.perf_counter() - started

    rows = sorted(result.timings, key=lambda r: -r[1])
    print(f"\n{len(rows)} tests in {total:.1f}s "
          f"({'OK' if result.wasSuccessful() else 'FAILED'})")

    by_module: dict[str, float] = {}
    for _tid, elapsed, module in rows:
        by_module[module] = by_module.get(module, 0.0) + elapsed
    print("\nby module:")
    for module, elapsed in sorted(by_module.items(), key=lambda kv: -kv[1]):
        share = 100 * elapsed / total if total else 0
        print(f"  {elapsed:8.1f}s  {share:5.1f}%  {module}")

    print(f"\nslowest {min(args.top, len(rows))} tests:")
    for tid, elapsed, _m in rows[:args.top]:
        print(f"  {elapsed:8.2f}s  {tid}")

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "total_seconds": round(total, 2),
                    "tests": len(rows),
                    "by_module": {k: round(v, 2) for k, v in by_module.items()},
                    "slowest": [
                        {"test": t, "seconds": round(e, 3)} for t, e, _ in rows
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"\nwrote {args.json}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
