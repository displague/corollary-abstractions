"""Overnight driver: generate full datasets, then train every task/arm."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PY = sys.executable
HERE = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=HERE)


def main() -> None:
    if not (HERE / "data" / "twins_train.jsonl").exists():
        rc = run([PY, "exprgen.py", "--out-dir", "data", "--train", "50000",
                  "--val", "5000", "--test", "5000", "--ood", "3000"])
        if rc != 0:
            sys.exit(rc)
    for task in ["twins", "equiv"]:
        for arm in ["char", "struct", "canon"]:
            out = HERE / "results" / f"{task}_{arm}.json"
            if out.exists():
                print(f"skip {task}/{arm} (exists)", flush=True)
                continue
            rc = run([PY, "train.py", "--task", task, "--arm", arm,
                      "--data-dir", "data", "--out", str(out),
                      "--save-model", str(HERE / "results" / f"{task}_{arm}.pt")])
            if rc != 0:
                print(f"FAILED {task}/{arm} rc={rc}", flush=True)
    print("ALL RUNS COMPLETE", flush=True)


if __name__ == "__main__":
    main()
