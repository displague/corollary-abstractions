"""Adjudicate the complete v0.6 depth-consumer matrix from result artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path

import torch


ARMS = ("address", "query", "memory", "both", "mlp")
SEEDS = (0, 1, 2)
MIN_EFFECT = 0.15
EQUIVALENCE_TOLERANCE = 0.01
PREDICTIONS = {
    "P-DC1": (
        "Extending shared path iteration into both the pointer query and "
        "decoder memory consumer improves mean depth-OOD exact over recurrent-"
        "address only, wins materially on at least two of three paired seeds, "
        "and keeps every trained-depth seed at or above 0.99 exact."
    ),
    "P-DC2": (
        "Query-only and memory-only each improve materially over address, each "
        "on at least two paired seeds, while both is at least as strong as the "
        "better single consumer."
    ),
    "P-DC3": (
        "The parameter-matched, order/level-aware, identity-preserving one-shot "
        "MLP consumer with fixed closed-form level codes does not match the "
        "both-recurrent consumer. The address encoder remains recurrent in "
        "every arm; this compares consumer mechanisms but does not isolate "
        "iteration from learned level processing."
    ),
    "P-DC4": (
        "All five arms run seeds 0/1/2 and report parameters, trained-depth "
        "exact, conditional depth-OOD exact, teacher-forced per-step/decile "
        "failure, inclusion by depth, source/data/config provenance, and "
        "checkpoint digests. This is a protocol gate: analysis either "
        "satisfies it or refuses to run."
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def material_gain(candidate: float, control: float) -> bool:
    """Compare at the registered boundary without binary-float edge flips."""
    return candidate - control >= MIN_EFFECT - 1e-12


def load_matrix(results_dir: Path) -> dict[str, dict[int, dict]]:
    matrix = {arm: {} for arm in ARMS}
    common_provenance = None
    common_inclusion = None
    for arm in ARMS:
        for seed in SEEDS:
            path = results_dir / f"depth_{arm}_s{seed}.json"
            if not path.exists():
                raise ValueError(f"incomplete matrix: missing {path.name}")
            row = json.loads(path.read_text(encoding="utf-8"))
            required_scalars = {"params", "test_exact", "ood_exact"}
            if not required_scalars.issubset(row):
                raise ValueError(f"missing reported metrics in {path.name}")
            if row.get("consumer") != arm or row.get("seed") != seed:
                raise ValueError(
                    f"mislabelled result {path.name}: "
                    f"consumer={row.get('consumer')!r}, seed={row.get('seed')!r}"
                )
            matrix[arm][seed] = row
            for split in ("test", "ood"):
                diagnostics = row.get(f"{split}_diagnostics")
                if not diagnostics or diagnostics.get("mode") != "teacher-forced":
                    raise ValueError(
                        f"missing teacher-forced {split} diagnostics in {path.name}"
                    )
            inclusion = row.get("inclusion")
            if not inclusion:
                raise ValueError(f"missing inclusion accounting in {path.name}")
            for split in ("train", "val", "test", "ood"):
                stats = inclusion.get(split, {})
                required = {"generated", "kept", "dropped_max_len",
                            "dropped_max_tgt", "by_depth"}
                if not required.issubset(stats):
                    raise ValueError(
                        f"incomplete {split} inclusion accounting in {path.name}"
                    )
                if stats["generated"] != (stats["kept"]
                                           + stats["dropped_max_len"]
                                           + stats["dropped_max_tgt"]):
                    raise ValueError(
                        f"incoherent {split} inclusion accounting in {path.name}"
                    )
                by_depth = stats["by_depth"]
                if not by_depth or "unknown" in by_depth:
                    raise ValueError(
                        f"empty {split} by-depth accounting in {path.name}"
                    )
                depth_required = required - {"by_depth"}
                for depth, depth_stats in by_depth.items():
                    if not depth_required.issubset(depth_stats):
                        raise ValueError(
                            f"incomplete {split} depth {depth} accounting in "
                            f"{path.name}"
                        )
                    if depth_stats["generated"] != (
                            depth_stats["kept"]
                            + depth_stats["dropped_max_len"]
                            + depth_stats["dropped_max_tgt"]):
                        raise ValueError(
                            f"incoherent {split} depth {depth} accounting in "
                            f"{path.name}"
                        )
                for key in depth_required:
                    if sum(item[key] for item in by_depth.values()) != stats[key]:
                        raise ValueError(
                            f"{split} by-depth totals disagree in {path.name}"
                        )
            if common_inclusion is None:
                common_inclusion = inclusion
            elif inclusion != common_inclusion:
                raise ValueError(f"mixed inclusion accounting in {path.name}")
            provenance = row.get("run_provenance")
            if not provenance or not row.get("checkpoint_sha256"):
                raise ValueError(f"unbound result {path.name}")
            if (provenance.get("consumer") != arm
                    or provenance.get("seed") != seed
                    or row.get("level_code") != provenance.get("level_code")):
                raise ValueError(f"mislabelled provenance in {path.name}")
            common = {
                key: provenance.get(key)
                for key in ("task_prefix", "data_sha256", "epochs", "level_code",
                            "max_tgt", "max_len", "implementation_sha256")
            }
            if any(value is None for value in common.values()):
                raise ValueError(f"incomplete provenance in {path.name}")
            if provenance["level_code"] != "recurrent":
                raise ValueError(f"non-recurrent depth matrix row {path.name}")
            if common_provenance is None:
                common_provenance = common
            elif common != common_provenance:
                raise ValueError(f"mixed experiment provenance in {path.name}")
    return matrix


def adjudicate(results_dir: Path) -> dict:
    matrix = load_matrix(results_dir)
    arms: dict[str, dict] = {}
    for arm in ARMS:
        rows = [matrix[arm][seed] for seed in SEEDS]
        tests = [row["test_exact"] for row in rows]
        ood = [row["ood_exact"] for row in rows]
        params = sorted({row["params"] for row in rows})
        if len(params) != 1:
            raise ValueError(f"{arm} changes parameter count across seeds: {params}")
        diagnostics = {}
        for split in ("test", "ood"):
            diagnostics[split] = {
                "step_perfect_rate": [
                    row[f"{split}_diagnostics"]["step_perfect_rate"]
                    for row in rows
                ],
                "by_kind_accuracy": {
                    kind: [row[f"{split}_diagnostics"]["by_kind"][kind]["accuracy"]
                           for row in rows]
                    for kind in ("B-struct", "C-leaf", "EOS")
                },
                "by_decile_accuracy": {
                    str(decile): [
                        row[f"{split}_diagnostics"]["by_decile"][str(decile)]["accuracy"]
                        for row in rows
                    ]
                    for decile in range(10)
                },
                "by_absolute_step_accuracy": [
                    {
                        step: values["accuracy"]
                        for step, values in row[f"{split}_diagnostics"][
                            "by_absolute_step"].items()
                    }
                    for row in rows
                ],
            }
        arms[arm] = {
            "params": params[0],
            "test_exact": tests,
            "test_mean": statistics.mean(tests),
            "test_pstdev": statistics.pstdev(tests),
            "ood_exact": ood,
            "ood_mean": statistics.mean(ood),
            "ood_pstdev": statistics.pstdev(ood),
            "diagnostics": diagnostics,
        }

    address = arms["address"]["ood_exact"]
    query = arms["query"]["ood_exact"]
    memory = arms["memory"]["ood_exact"]
    both = arms["both"]["ood_exact"]
    mlp = arms["mlp"]["ood_exact"]
    both_wins = sum(candidate > control
                    for candidate, control in zip(both, address))
    both_material_wins = sum(material_gain(candidate, control)
                             for candidate, control in zip(both, address))
    query_material_wins = sum(material_gain(candidate, control)
                              for candidate, control in zip(query, address))
    memory_material_wins = sum(material_gain(candidate, control)
                               for candidate, control in zip(memory, address))
    mlp_material_losses = sum(material_gain(candidate, control)
                              for candidate, control in zip(both, mlp))
    id_floor = 0.99
    pdc1 = (material_gain(arms["both"]["ood_mean"],
                          arms["address"]["ood_mean"])
            and both_material_wins >= 2
            and min(arms["both"]["test_exact"]) >= id_floor)
    pdc2 = (
        material_gain(arms["query"]["ood_mean"], arms["address"]["ood_mean"])
        and material_gain(arms["memory"]["ood_mean"],
                          arms["address"]["ood_mean"])
        and query_material_wins >= 2
        and memory_material_wins >= 2
        and arms["both"]["ood_mean"] + EQUIVALENCE_TOLERANCE >= max(
            arms["query"]["ood_mean"], arms["memory"]["ood_mean"])
    )
    parameter_delta = arms["both"]["params"] - arms["mlp"]["params"]
    parameter_matched = abs(parameter_delta) <= 2
    pdc3 = (parameter_matched
            and material_gain(arms["both"]["ood_mean"], arms["mlp"]["ood_mean"])
            and mlp_material_losses >= 2)
    checkpoints = []
    for arm in ARMS:
        for seed in SEEDS:
            path = results_dir / f"depth_{arm}_s{seed}.pt"
            if not path.exists():
                raise ValueError(f"missing requested checkpoint {path.name}")
            saved = torch.load(path, map_location="cpu", weights_only=False)
            if (saved.get("config", {}).get("consumer") != arm
                    or saved.get("seed") != seed
                    or saved.get("config", {}).get("level_code") !=
                    matrix[arm][seed]["run_provenance"]["level_code"]):
                raise ValueError(f"mislabelled checkpoint {path.name}")
            digest = sha256(path)
            if matrix[arm][seed]["checkpoint_sha256"] != digest:
                raise ValueError(f"checkpoint digest mismatch for {path.name}")
            checkpoints.append({
                "file": path.name,
                "consumer": arm,
                "seed": seed,
                "bytes": path.stat().st_size,
                "sha256": digest,
            })

    return {
        "experiment": "depth-consumers-v0.6",
        "seeds": list(SEEDS),
        "inclusion": matrix["address"][0]["inclusion"],
        "arms": arms,
        "parameter_match": {
            "both_minus_mlp": parameter_delta,
            "within_two_parameters": parameter_matched,
        },
        "materiality": {
            "minimum_absolute_mean_effect": MIN_EFFECT,
            "at_least_as_strong_tolerance": EQUIVALENCE_TOLERANCE,
        },
        "adjudication": {
            "P-DC1": {"prediction": PREDICTIONS["P-DC1"],
                       "status": "FIRED" if pdc1 else "MISSED",
                       "both_seedwise_wins": both_wins,
                       "both_material_seedwise_wins": both_material_wins,
                       "in_distribution_floor": id_floor},
            "P-DC2": {"prediction": PREDICTIONS["P-DC2"],
                       "status": "FIRED" if pdc2 else "MISSED",
                       "query_material_seedwise_wins": query_material_wins,
                       "memory_material_seedwise_wins": memory_material_wins},
            "P-DC3": {"prediction": PREDICTIONS["P-DC3"],
                       "status": ("BLOCKED" if not parameter_matched else
                                  "FIRED" if pdc3 else "MISSED"),
                       "both_over_mlp_material_seedwise_wins": mlp_material_losses,
                       "parameter_match_required": parameter_matched},
            "P-DC4": {"prediction": PREDICTIONS["P-DC4"],
                       "status": "SATISFIED",
                       "adjudication_kind": "protocol_gate"},
        },
        "checkpoints": checkpoints,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path,
                        default=Path(__file__).resolve().parent / "results")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = adjudicate(args.results_dir)
    out = args.out or args.results_dir / "depth_consumers.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
