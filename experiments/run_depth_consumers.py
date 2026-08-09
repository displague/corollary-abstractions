#!/usr/bin/env python3
"""Run the registered v0.6 depth-consumer ladder and summarize all seeds."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parent.parent
ARMS = ("address", "query", "memory", "both", "mlp")
SPLITS = ("train", "val", "test", "ood")
IMPLEMENTATION_FILES = (
    ROOT / "experiments" / "train_analogy.py",
    ROOT / "experiments" / "tokenizers.py",
    ROOT / "experiments" / "train_span.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def requested_provenance(data_dir: Path, epochs: int, arm: str, seed: int,
                         max_tgt: int = 96,
                         max_len: int = 512) -> dict:
    return {
        "task_prefix": "analogy",
        "data_sha256": {
            split: sha256(data_dir / f"analogy_{split}.jsonl")
            for split in SPLITS
        },
        "epochs": epochs,
        "max_tgt": max_tgt,
        "max_len": max_len,
        "level_code": "recurrent",
        "consumer": arm,
        "seed": seed,
        "implementation_sha256": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in IMPLEMENTATION_FILES
        },
    }


def bind_artifacts(out: Path, checkpoint: Path, provenance: dict) -> dict:
    row = json.loads(out.read_text(encoding="utf-8"))
    if (row.get("consumer") != provenance["consumer"]
            or row.get("seed") != provenance["seed"]
            or row.get("level_code") != provenance["level_code"]):
        raise ValueError(f"cannot bind mislabelled {out.name}")
    saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if (saved.get("config", {}).get("consumer") != provenance["consumer"]
            or saved.get("seed") != provenance["seed"]
            or saved.get("config", {}).get("level_code") !=
            provenance["level_code"]):
        raise ValueError(f"cannot bind mislabelled {checkpoint.name}")
    row["run_provenance"] = provenance
    row["checkpoint_sha256"] = sha256(checkpoint)
    out.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
    return row


def load_resumable(out: Path, checkpoint: Path, provenance: dict) -> dict:
    row = json.loads(out.read_text(encoding="utf-8"))
    arm = provenance["consumer"]
    seed = provenance["seed"]
    if row.get("consumer") != arm or row.get("seed") != seed:
        raise ValueError(f"cannot resume mislabelled {out.name}")
    for split in ("test", "ood"):
        if row.get(f"{split}_diagnostics", {}).get("mode") != "teacher-forced":
            raise ValueError(f"cannot resume {out.name} without {split} diagnostics")
    saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if (saved.get("config", {}).get("consumer") != arm
            or saved.get("seed") != seed
            or saved.get("config", {}).get("level_code") !=
            provenance["level_code"]):
        raise ValueError(f"cannot resume mislabelled {checkpoint.name}")
    if row.get("run_provenance") != provenance:
        raise ValueError(f"cannot resume {out.name} from different experiment")
    if row.get("checkpoint_sha256") != sha256(checkpoint):
        raise ValueError(f"cannot resume unbound checkpoint {checkpoint.name}")
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path,
                        default=ROOT / "experiments" / "results")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--arms", nargs="+", choices=ARMS, default=list(ARMS))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--max-tgt", type=int, default=96)
    parser.add_argument("--max-len", type=int, default=512)
    parser.add_argument("--resume", action="store_true",
                        help="reuse a row only when its requested checkpoint "
                             "also exists and labels match")
    args = parser.parse_args()
    args.data_dir = args.data_dir.resolve()
    args.results_dir = args.results_dir.resolve()

    args.results_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for arm in args.arms:
        for seed in args.seeds:
            out = args.results_dir / f"depth_{arm}_s{seed}.json"
            checkpoint = args.results_dir / f"depth_{arm}_s{seed}.pt"
            provenance = requested_provenance(
                args.data_dir, args.epochs, arm, seed,
                args.max_tgt, args.max_len
            )
            if args.resume and out.exists() and checkpoint.exists():
                row = load_resumable(out, checkpoint, provenance)
                print(f"REUSE arm={arm} seed={seed}", flush=True)
                rows.append(row)
                continue
            command = [
                sys.executable,
                str(ROOT / "experiments" / "train_analogy.py"),
                "--data-dir", str(args.data_dir),
                "--task-prefix", "analogy",
                "--out", str(out),
                "--level-code", "recurrent",
                "--consumer", arm,
                "--seed", str(seed),
                "--epochs", str(args.epochs),
                "--max-tgt", str(args.max_tgt),
                "--max-len", str(args.max_len),
            ]
            command += ["--save-model", str(checkpoint)]
            print(f"RUN arm={arm} seed={seed}", flush=True)
            subprocess.run(command, cwd=ROOT / "experiments", check=True)
            rows.append(bind_artifacts(out, checkpoint, provenance))

    summary = {"experiment": "depth-consumers-v0.6", "seeds": args.seeds,
               "arms": {}}
    for arm in args.arms:
        arm_rows = [row for row in rows if row["consumer"] == arm]
        summary["arms"][arm] = {
            "params": sorted({row["params"] for row in arm_rows}),
            "test_exact": [row["test_exact"] for row in arm_rows],
            "ood_exact": [row["ood_exact"] for row in arm_rows],
            "test_mean": sum(row["test_exact"] for row in arm_rows) /
                         len(arm_rows),
            "ood_mean": sum(row["ood_exact"] for row in arm_rows) /
                        len(arm_rows),
        }
    summary["complete_registered_matrix"] = (
        len(args.arms) == len(ARMS) and set(args.arms) == set(ARMS)
        and len(args.seeds) == 3 and set(args.seeds) == {0, 1, 2}
    )
    summary_path = args.results_dir / "depth_consumers_raw.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
