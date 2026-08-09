#!/usr/bin/env python3
"""Run the registered v0.6 depth-consumer ladder and summarize all seeds.

P-DC5 stays verbatim in the roadmap but is retracted before adjudication: its
12-GiB clause measured live tensors after clearing the allocator and could not
observe the 15.76-GiB device condition that preceded two Windows bugchecks.

P-DC6 (registered before the replacement run): logical training batch 192 is
split into 64-example GPU microbatches, every validation/test/OOD loader uses
batch 32, and all values are bound into results and checkpoints.  All fifteen
rows must complete, record allocated/reserved/whole-device footprints for
train-validation and final evaluation, and final evaluation may add no more
than 512 MiB above the train-validation device or reserved high-water marks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

import torch

from depth_consumer_protocol import (EVAL_BATCH_SIZE, LOGICAL_BATCH_SIZE,
                                     MAX_DEVICE_FOOTPRINT_FRACTION,
                                     MAX_EVAL_INCREMENT_BYTES,
                                     MICROBATCH_SIZE,
                                     PER_PROCESS_MEMORY_FRACTION,
                                     RUN_TIMEOUT_SECONDS, atomic_write_json)


ROOT = Path(__file__).resolve().parent.parent
ARMS = ("address", "query", "memory", "both", "mlp")
SPLITS = ("train", "val", "test", "ood")
IMPLEMENTATION_FILES = (
    ROOT / "experiments" / "train_analogy.py",
    ROOT / "experiments" / "run_depth_consumers.py",
    ROOT / "experiments" / "depth_consumer_protocol.py",
    ROOT / "experiments" / "tokenizers.py",
    ROOT / "experiments" / "train_span.py",
)
RESUME_ERRORS = (OSError, ValueError, EOFError, RuntimeError,
                 pickle.UnpicklingError, json.JSONDecodeError)


def gpu_environment() -> dict:
    """Capture the local trust boundary relevant to the two driver crashes."""
    if not torch.cuda.is_available():
        return {"stable": {"cuda_available": False}, "telemetry": {}}
    driver = None
    try:
        driver = subprocess.check_output([
            "nvidia-smi", "--query-gpu=driver_version",
            "--format=csv,noheader,nounits"], text=True).strip()
    except (OSError, subprocess.SubprocessError):
        pass
    clock_events = None
    try:
        clock_events = subprocess.check_output([
            "nvidia-smi", "--query-gpu=clocks_event_reasons.active",
            "--format=csv,noheader,nounits"], text=True).strip()
    except (OSError, subprocess.SubprocessError):
        pass
    tdr_delay = tdr_ddi_delay = None
    tdr_registry_readable = False
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers") as key:
                for name, target in (("TdrDelay", "delay"),
                                     ("TdrDdiDelay", "ddi")):
                    try:
                        value = winreg.QueryValueEx(key, name)[0]
                    except FileNotFoundError:
                        value = None
                    if target == "delay":
                        tdr_delay = value
                    else:
                        tdr_ddi_delay = value
                tdr_registry_readable = True
        except OSError:
            pass
    device_index = torch.cuda.current_device()
    props = torch.cuda.get_device_properties(device_index)
    return {
        "stable": {
            "cuda_available": True,
            "torch_version": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "device_index": device_index,
            "device_name": props.name,
            "device_total_bytes": props.total_memory,
            "driver_version": driver,
            "tdr_registry_readable": tdr_registry_readable,
            "tdr_delay_seconds": tdr_delay,
            "tdr_ddi_delay_seconds": tdr_ddi_delay,
        },
        "telemetry": {"clock_event_reasons_active": clock_events},
    }


def validate_gpu_environment(environment: dict) -> None:
    required = ("cuda_available", "torch_version", "cuda_runtime",
                "device_name", "device_total_bytes", "driver_version")
    missing = [key for key in required if not environment.get(key)]
    if missing:
        raise RuntimeError(
            "cannot launch depth matrix without stable GPU environment: "
            + ", ".join(missing))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def requested_provenance(data_dir: Path, epochs: int, arm: str, seed: int,
                         max_tgt: int = 96,
                         max_len: int = 512,
                         batch_size: int = LOGICAL_BATCH_SIZE,
                         microbatch_size: int = MICROBATCH_SIZE,
                         eval_batch_size: int = EVAL_BATCH_SIZE,
                         memory_fraction: float =
                         PER_PROCESS_MEMORY_FRACTION,
                         runtime_environment: dict | None = None) -> dict:
    return {
        "task_prefix": "analogy",
        "data_sha256": {
            split: sha256(data_dir / f"analogy_{split}.jsonl")
            for split in SPLITS
        },
        "epochs": epochs,
        "max_tgt": max_tgt,
        "max_len": max_len,
        "batch_size": batch_size,
        "microbatch_size": microbatch_size,
        "eval_batch_size": eval_batch_size,
        "memory_fraction": memory_fraction,
        "runtime_environment": (runtime_environment
                                if runtime_environment is not None else {}),
        "level_code": "recurrent",
        "consumer": arm,
        "seed": seed,
        "implementation_sha256": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in IMPLEMENTATION_FILES
        },
    }


def bind_artifacts(out: Path, checkpoint: Path, provenance: dict,
                   launch_telemetry: dict | None = None) -> dict:
    row = json.loads(out.read_text(encoding="utf-8"))
    if (row.get("consumer") != provenance["consumer"]
            or row.get("seed") != provenance["seed"]
            or row.get("level_code") != provenance["level_code"]
            or row.get("batch_size") != provenance["batch_size"]
            or row.get("microbatch_size") != provenance["microbatch_size"]
            or row.get("eval_batch_size") != provenance["eval_batch_size"]
            or row.get("memory_fraction") != provenance["memory_fraction"]):
        raise ValueError(f"cannot bind mislabelled {out.name}")
    saved = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if (saved.get("config", {}).get("consumer") != provenance["consumer"]
            or saved.get("seed") != provenance["seed"]
            or saved.get("config", {}).get("level_code") !=
            provenance["level_code"]
            or saved.get("config", {}).get("batch_size") !=
            provenance["batch_size"]
            or saved.get("config", {}).get("microbatch_size") !=
            provenance["microbatch_size"]
            or saved.get("config", {}).get("eval_batch_size") !=
            provenance["eval_batch_size"]
            or saved.get("config", {}).get("memory_fraction") !=
            provenance["memory_fraction"]):
        raise ValueError(f"cannot bind mislabelled {checkpoint.name}")
    row["run_provenance"] = provenance
    row["launch_telemetry"] = launch_telemetry or {}
    row["checkpoint_sha256"] = sha256(checkpoint)
    atomic_write_json(out, row)
    return row


def load_resumable(out: Path, checkpoint: Path, provenance: dict) -> dict:
    row = json.loads(out.read_text(encoding="utf-8"))
    arm = provenance["consumer"]
    seed = provenance["seed"]
    if row.get("consumer") != arm or row.get("seed") != seed:
        raise ValueError(f"cannot resume mislabelled {out.name}")
    for split in ("test", "ood"):
        if (row.get(f"{split}_diagnostics") or {}).get("mode") != "teacher-forced":
            raise ValueError(f"cannot resume {out.name} without {split} diagnostics")
    saved = torch.load(checkpoint, map_location="cpu", weights_only=True)
    if (saved.get("config", {}).get("consumer") != arm
            or saved.get("seed") != seed
            or saved.get("config", {}).get("level_code") !=
            provenance["level_code"]
            or saved.get("config", {}).get("batch_size") !=
            provenance["batch_size"]
            or saved.get("config", {}).get("microbatch_size") !=
            provenance["microbatch_size"]
            or saved.get("config", {}).get("eval_batch_size") !=
            provenance["eval_batch_size"]
            or saved.get("config", {}).get("memory_fraction") !=
            provenance["memory_fraction"]):
        raise ValueError(f"cannot resume mislabelled {checkpoint.name}")
    if row.get("run_provenance") != provenance:
        raise ValueError(f"cannot resume {out.name} from different experiment")
    if row.get("checkpoint_sha256") != sha256(checkpoint):
        raise ValueError(f"cannot resume unbound checkpoint {checkpoint.name}")
    return row


def try_load_resumable(out: Path, checkpoint: Path,
                       provenance: dict) -> tuple[dict | None, Exception | None]:
    try:
        return load_resumable(out, checkpoint, provenance), None
    except RESUME_ERRORS as error:
        return None, error


def safety_breaches(row: dict, environment: dict) -> list[str]:
    """Stop the serial matrix before a dangerous row can be followed."""
    memory = row.get("cuda_memory") or {}
    train_val = memory.get("train_validation") or {}
    evaluation = memory.get("final_evaluation") or {}
    total = environment["device_total_bytes"]
    reserved_limit = int(total * PER_PROCESS_MEMORY_FRACTION)
    device_limit = int(total * MAX_DEVICE_FOOTPRINT_FRACTION)
    breaches = []
    for phase_name, phase in (("train_validation", train_val),
                              ("final_evaluation", evaluation)):
        reserved = phase.get("peak_reserved_bytes")
        footprint = phase.get("peak_device_footprint_bytes")
        if type(reserved) is not int or type(footprint) is not int:
            breaches.append(f"{phase_name}: missing memory evidence")
            continue
        if reserved > reserved_limit:
            breaches.append(f"{phase_name}: reserved {reserved} > {reserved_limit}")
        if footprint >= device_limit:
            breaches.append(f"{phase_name}: device {footprint} >= {device_limit}")
    if not breaches:
        reserved_increment = (evaluation["peak_reserved_bytes"]
                              - train_val["peak_reserved_bytes"])
        device_increment = (evaluation["peak_device_footprint_bytes"]
                            - train_val["peak_device_footprint_bytes"])
        if reserved_increment > MAX_EVAL_INCREMENT_BYTES:
            breaches.append(
                f"evaluation reserved increment {reserved_increment} > "
                f"{MAX_EVAL_INCREMENT_BYTES}")
        if device_increment > MAX_EVAL_INCREMENT_BYTES:
            breaches.append(
                f"evaluation device increment {device_increment} > "
                f"{MAX_EVAL_INCREMENT_BYTES}")
    return breaches


def enforce_row_safety(row: dict, environment: dict) -> None:
    breaches = safety_breaches(row, environment)
    if breaches:
        raise RuntimeError("depth safety breach; stopping matrix: "
                           + "; ".join(breaches))


def accept_safe_row(rows: list[dict], row: dict, environment: dict) -> None:
    """Make safety enforcement inseparable from serial-matrix acceptance."""
    enforce_row_safety(row, environment)
    rows.append(row)


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
    parser.add_argument("--batch-size", type=int, default=LOGICAL_BATCH_SIZE)
    parser.add_argument("--microbatch-size", type=int, default=MICROBATCH_SIZE)
    parser.add_argument("--eval-batch-size", type=int, default=EVAL_BATCH_SIZE)
    parser.add_argument("--memory-fraction", type=float,
                        default=PER_PROCESS_MEMORY_FRACTION)
    parser.add_argument("--resume", action="store_true",
                        help="reuse a row only when its requested checkpoint "
                             "also exists and labels match")
    args = parser.parse_args()
    requested_protocol = (args.batch_size, args.microbatch_size,
                          args.eval_batch_size, args.memory_fraction)
    registered_protocol = (LOGICAL_BATCH_SIZE, MICROBATCH_SIZE,
                           EVAL_BATCH_SIZE, PER_PROCESS_MEMORY_FRACTION)
    if requested_protocol != registered_protocol:
        raise ValueError(
            "depth-consumer matrix requires registered protocol "
            f"{registered_protocol}, got {requested_protocol}")
    args.data_dir = args.data_dir.resolve()
    args.results_dir = args.results_dir.resolve()

    args.results_dir.mkdir(parents=True, exist_ok=True)
    captured_environment = gpu_environment()
    runtime_environment = captured_environment["stable"]
    launch_telemetry = captured_environment["telemetry"]
    validate_gpu_environment(runtime_environment)
    rows = []
    for arm in args.arms:
        for seed in args.seeds:
            out = args.results_dir / f"depth_{arm}_s{seed}.json"
            checkpoint = args.results_dir / f"depth_{arm}_s{seed}.pt"
            provenance = requested_provenance(
                args.data_dir, args.epochs, arm, seed,
                args.max_tgt, args.max_len, args.batch_size,
                args.microbatch_size, args.eval_batch_size,
                args.memory_fraction, runtime_environment
            )
            if args.resume and out.exists() and checkpoint.exists():
                row, error = try_load_resumable(out, checkpoint, provenance)
                if error is not None:
                    print(f"REJECT arm={arm} seed={seed}: {error}", flush=True)
                else:
                    assert row is not None
                    accept_safe_row(rows, row, runtime_environment)
                    print(f"REUSE arm={arm} seed={seed}", flush=True)
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
                "--batch-size", str(args.batch_size),
                "--microbatch-size", str(args.microbatch_size),
                "--eval-batch-size", str(args.eval_batch_size),
                "--memory-fraction", str(args.memory_fraction),
            ]
            command += ["--save-model", str(checkpoint)]
            print(f"RUN arm={arm} seed={seed}", flush=True)
            subprocess.run(command, cwd=ROOT / "experiments", check=True,
                           timeout=RUN_TIMEOUT_SECONDS)
            row = bind_artifacts(
                out, checkpoint, provenance, launch_telemetry)
            accept_safe_row(rows, row, runtime_environment)

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
    summary["launch_telemetry"] = launch_telemetry
    atomic_write_json(summary_path, summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
