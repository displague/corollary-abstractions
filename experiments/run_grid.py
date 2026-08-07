"""Scaling grid: solvex across model width x data scale x positional scheme.

Emergence is a claim about curves, not points. This grid asks whether depth
generalization appears with scale under absolute positions (if yes, tree
addressing is a shortcut; if no, it is a qualitative interface difference
that scale does not buy at these budgets).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PY = sys.executable
HERE = Path(__file__).resolve().parent
DATA = Path(r"C:\Users\displ\Documents\corollary-abstractions\experiments\data")

WIDTHS = [32, 64, 128, 256]
FRACS = [0.1, 1.0]
POSITIONS = ["abs", "tree"]


def main() -> None:
    for d in WIDTHS:
        for frac in FRACS:
            for pos in POSITIONS:
                out = HERE / "results" / f"grid_solvex_d{d}_f{int(frac*100)}_{pos}.json"
                if out.exists():
                    print(f"skip {out.name}", flush=True)
                    continue
                cmd = [PY, "train_span.py", "--arm", "struct",
                       "--positions", pos, "--d-model", str(d),
                       "--train-frac", str(frac), "--epochs", "10",
                       "--data-dir", str(DATA), "--out", str(out)]
                print("+", " ".join(cmd[1:]), flush=True)
                rc = subprocess.call(cmd, cwd=HERE)
                if rc != 0:
                    print(f"FAILED d={d} f={frac} {pos} rc={rc}", flush=True)
    print("GRID COMPLETE", flush=True)


if __name__ == "__main__":
    main()
