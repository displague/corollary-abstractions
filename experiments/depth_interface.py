#!/usr/bin/env python3
"""v0.8 item 5 -- move depth to the interface, on UNTRUNCATED OOD.

The v0.6/v0.7 consumer matrix is a closed negative: address-only is best and
more recurrence at the consumers damages the copy interface.  This slice does
NOT add another consumer arm.  It does two things the roadmap gate requires:

1. Removes the conditional-only OOD blind spot.  The reported ``ood_exact`` is
   ``correct / kept`` -- the 550 capacity-excluded OOD rows (target copy-length
   beyond ``max_tgt``=96, or source length beyond ``max_len``=512) never enter
   the denominator, so they are invisible.  ``unconditional_ood`` counts every
   generated OOD row: an excluded row is a row this copy interface cannot emit,
   so it is scored as a failure.  ``unconditional = retained * kept/generated``.
   Per-depth generated/kept/excluded counts make the 550 exclusions visible.

2. Produces one interface-level result.  The interface variable is the copy
   budget itself: ``max_tgt`` (target copy length) and ``max_len`` (source
   length).  The control is the existing address-only arm at 96/512 (the same
   data by sha256, same epochs, same safe batch protocol).  The treatment is
   the SAME address arm retrained with the budget enlarged so OOD is fully
   untruncated (0 rows dropped), then scored on the untruncated OOD set and on
   the previously-excluded subset in isolation.  Not another consumer -- the
   only change is the interface budget.

Registered predictions (P-DI1..P-DI3) are fixed BEFORE the treatment run and
adjudicated on the record; a miss is reported, not edited away.  The v0.6/v0.7
depth predictions (P-DC1..P-DC7) are untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

from depth_consumer_protocol import (  # noqa: E402
    EVAL_BATCH_SIZE, LOGICAL_BATCH_SIZE, MAX_DEVICE_FOOTPRINT_FRACTION,
    MICROBATCH_SIZE, PER_PROCESS_MEMORY_FRACTION, atomic_write_json)

ARMS = ("address", "query", "memory", "both", "mlp")
CONTROL_ARM = "address"
SEEDS = (0, 1, 2)
# Fully untruncates the OOD split: max OOD target action length is 326 and max
# OOD source length is 649, so 330/700 drops zero OOD rows.  Enlarging the copy
# budget is the interface manipulation; it is the ONLY change from the control.
UNTRUNCATED_MAX_TGT = 330
UNTRUNCATED_MAX_LEN = 700
CONTROL_MAX_TGT = 96
CONTROL_MAX_LEN = 512
# Registered materiality boundary, matched to the v0.6 depth ladder's MIN_EFFECT
# so "does the interface move OOD" is asked at the same bar the consumer arms
# were asked at.
MIN_EFFECT = 0.15
EXCLUDED_SUBSET_CEILING = 0.05
# Measured on the matched dataset: the deepest target the interface ever trains
# is 88 copy steps (train 88 / val 84 / test 76), while OOD needs up to 326.
# Every copy position at or beyond 96 is therefore untrained under ANY max_tgt,
# so the copy budget is bounded by training exposure, not by the hyperparameter.
MAX_TRAINED_TARGET_LENGTH = 88

P_DI1 = (
    "The conditional-only OOD metric was a blind spot: reported ood_exact is "
    "correct/kept, so the 550 capacity-excluded OOD rows never entered the "
    "denominator. The unconditional metric equals retained times "
    "kept/generated, so every arm's unconditional OOD is strictly below its "
    "retained OOD by the same 550/3000 denominator inflation, the arm ordering "
    "(address best, both worst) is preserved, and the 550 excluded rows are "
    "entirely depth 4 and 5 -- the deepest, out-of-distribution rows whose "
    "target copy-length or source-length exceeds the interface budget."
)
P_DI2 = (
    "Enlarging the copy interface budget (max_tgt 96->330, max_len 512->700) so "
    "the OOD split is fully untruncated does NOT move untruncated OOD upward. "
    "Address-only untruncated greedy-exact stays at or below the control's "
    "unconditional metric plus the 0.15 materiality bar -- it does not climb "
    "back toward the retained metric -- and the previously-excluded rows score "
    "below 0.05 in isolation, because their targets extend into copy positions "
    "the interface never trained. The cliff is a depth/interface-boundary "
    "property, not a budget artifact; this is a NEGATIVE interface result."
)
P_DI3 = (
    "On untruncated OOD the residual failure mass localizes to the deep end: "
    "every one of the 550 capacity exclusions is depth 4 or 5 and fails at the "
    "copy-budget boundary (target length beyond 96), and among the retained "
    "rows the teacher-forced first error concentrates in the latest decode "
    "deciles rather than being spread uniformly."
)
PREDICTIONS = {"P-DI1": P_DI1, "P-DI2": P_DI2, "P-DI3": P_DI3}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --------------------------------------------------------------------------
# Blind-spot removal: retained vs unconditional accounting (pure, testable).
# --------------------------------------------------------------------------
def unconditional_from_row(row: dict, split: str = "ood") -> dict:
    """Turn a retained-only ``{split}_exact`` into an unconditional metric.

    The reported metric is correct/kept; the excluded rows are invisible.  An
    excluded row is one the copy interface cannot emit within its budget, so it
    is a failure and belongs in the denominator.  Returns both metrics, the
    recovered integer correct count, and per-depth generated/kept/excluded and
    retained/unconditional scored counts so the exclusions stop being invisible.
    """
    inclusion = row["inclusion"][split]
    generated = inclusion["generated"]
    kept = inclusion["kept"]
    if kept < 1:
        raise ValueError(f"{split} inclusion has no kept rows")
    if generated != kept + inclusion["dropped_max_len"] + inclusion["dropped_max_tgt"]:
        raise ValueError(f"incoherent {split} inclusion accounting")
    retained = row[f"{split}_exact"]
    exact_correct = retained * kept
    correct = round(exact_correct)
    if abs(exact_correct - correct) > 1e-6:
        raise ValueError(
            f"{split}_exact {retained} is not correct/{kept}; cannot recover "
            "an integer correct count for unconditional accounting")
    unconditional = correct / generated
    per_depth = {}
    for depth, stats in inclusion["by_depth"].items():
        excluded = stats["dropped_max_len"] + stats["dropped_max_tgt"]
        if stats["generated"] != stats["kept"] + excluded:
            raise ValueError(f"incoherent {split} depth {depth} accounting")
        per_depth[depth] = {
            "generated": stats["generated"],
            "kept": stats["kept"],
            "excluded": excluded,
            "retained_scored": stats["kept"],
            "unconditional_scored": stats["generated"],
        }
    return {
        "generated": generated,
        "kept": kept,
        "excluded": generated - kept,
        "correct": correct,
        "retained_ood": retained,
        "unconditional_ood": unconditional,
        "denominator_inflation": (generated - kept) / generated,
        "by_depth": per_depth,
    }


def control_accounting(results_dir: Path) -> dict:
    """Retained vs unconditional OOD for every matched consumer arm."""
    arms = {}
    for arm in ARMS:
        per_seed = []
        for seed in SEEDS:
            path = results_dir / f"depth_{arm}_s{seed}.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            if row.get("consumer") != arm or row.get("seed") != seed:
                raise ValueError(f"mislabelled control result {path.name}")
            per_seed.append(unconditional_from_row(row, "ood"))
        arms[arm] = {
            "retained_ood": [item["retained_ood"] for item in per_seed],
            "unconditional_ood": [item["unconditional_ood"] for item in per_seed],
            "retained_mean": statistics.mean(i["retained_ood"] for i in per_seed),
            "unconditional_mean": statistics.mean(
                i["unconditional_ood"] for i in per_seed),
            "generated": per_seed[0]["generated"],
            "kept": per_seed[0]["kept"],
            "excluded": per_seed[0]["excluded"],
            "by_depth": per_seed[0]["by_depth"],
            "correct_by_seed": [item["correct"] for item in per_seed],
        }
    return arms


def retained_localization(results_dir: Path, arm: str = CONTROL_ARM) -> dict:
    """Where the retained teacher-forced first error concentrates by decile."""
    per_seed = []
    for seed in SEEDS:
        path = results_dir / f"depth_{arm}_s{seed}.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        diag = row["ood_diagnostics"]
        first_error = diag.get("first_error_decile", {})
        per_seed.append({
            decile: value["fraction_of_erroneous"]
            for decile, value in first_error.items()
        })
    deciles = sorted({d for item in per_seed for d in item}, key=int)
    return {
        "arm": arm,
        "first_error_fraction_by_decile_mean": {
            decile: statistics.mean(item.get(decile, 0.0) for item in per_seed)
            for decile in deciles
        },
        "per_seed": per_seed,
    }


# --------------------------------------------------------------------------
# Interface manipulation: enlarge the copy budget, retrain address-only.
#
# The metric is TEACHER-FORCED step-perfect, not free-running greedy.  The
# excluded rows need up to 326 copy steps, but the deepest target the interface
# ever trains is 88 steps, so a 330-step autoregressive greedy over the deep
# OOD tail is quadratic in the emitted prefix and impractical.  Teacher forcing
# is a single forward pass and asks the sharper question directly: even handed
# the gold prefix, can the model emit the right copy action at a position it
# never trained?  The answer localizes the boundary without the decode cost.
# --------------------------------------------------------------------------
def _actlen(row) -> int:
    return 2 + len(row["target_positions"])


def _sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train_untruncated(data_dir: Path, results_dir: Path, seeds, epochs: int):
    """Train address-only at the enlarged copy budget; teacher-forced eval.

    Same data (by sha256), same recurrent address arm, same safe batch protocol
    (logical 192 / microbatch 64 / eval 32 / memory fraction 0.70), same 10
    epochs as the control.  The ONLY change is the interface budget (max_tgt
    96->330, max_len 512->700), so the OOD split is fully untruncated.  Reuses
    train_analogy.py's model, dataset, accumulating backward, teacher-forced
    diagnostics, and footprint snapshot -- nothing about the mechanism is
    reimplemented, only the greedy final eval is replaced by teacher forcing.
    """
    import math

    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader

    from train_analogy import (AnalogyDataset, AnalogyPointer, Vocab,
                              backward_logical_batch, collate,
                              cuda_memory_snapshot, greedy_exact, load_jsonl,
                              save_checkpoint_atomic, teacher_forced_diagnostics)

    results_dir.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    data_sha = {
        split: _sha256_bytes(data_dir / f"analogy_{split}.jsonl")
        for split in ("train", "val", "test", "ood")}

    for seed in seeds:
        torch.manual_seed(seed)
        if device == "cuda":
            torch.cuda.set_per_process_memory_fraction(
                PER_PROCESS_MEMORY_FRACTION)
            torch.cuda.reset_peak_memory_stats(device)
            pre_footprint = cuda_memory_snapshot(device)["device_footprint_bytes"]
        splits = {s: load_jsonl(data_dir / f"analogy_{s}.jsonl")
                  for s in ("train", "val", "test", "ood")}
        src_tokens = set()
        for row in splits["train"]:
            src_tokens.update(row["tokens_struct"])
        vocab = Vocab(src_tokens)

        def source_len(row):
            return len(vocab.encode(row["tokens_struct"]))

        train_ds = AnalogyDataset(splits["train"], vocab, UNTRUNCATED_MAX_LEN,
                                  UNTRUNCATED_MAX_TGT)
        val_ds = AnalogyDataset(splits["val"], vocab, UNTRUNCATED_MAX_LEN,
                                UNTRUNCATED_MAX_TGT)
        ood_all_ds = AnalogyDataset(splits["ood"], vocab, UNTRUNCATED_MAX_LEN,
                                    UNTRUNCATED_MAX_TGT)
        kept_rows, excluded_rows = [], []
        for row in splits["ood"]:
            if (source_len(row) > CONTROL_MAX_LEN
                    or _actlen(row) > CONTROL_MAX_TGT):
                excluded_rows.append(row)
            else:
                kept_rows.append(row)
        ood_kept_ds = AnalogyDataset(kept_rows, vocab, UNTRUNCATED_MAX_LEN,
                                     UNTRUNCATED_MAX_TGT)
        ood_excl_ds = AnalogyDataset(excluded_rows, vocab, UNTRUNCATED_MAX_LEN,
                                     UNTRUNCATED_MAX_TGT)
        gen = torch.Generator().manual_seed(seed)
        train_loader = DataLoader(train_ds, batch_size=LOGICAL_BATCH_SIZE,
                                  shuffle=True, collate_fn=collate,
                                  generator=gen)
        val_loader = DataLoader(val_ds, batch_size=EVAL_BATCH_SIZE,
                                shuffle=False, collate_fn=collate)

        model = AnalogyPointer(len(vocab), 128, max_tgt=UNTRUNCATED_MAX_TGT,
                               level_code="recurrent",
                               consumer=CONTROL_ARM).to(device)
        n_params = sum(p.numel() for p in model.parameters())
        opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
        total_steps = epochs * math.ceil(len(train_ds) / LOGICAL_BATCH_SIZE)
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-4,
                                                    total_steps=total_steps)
        loss_fn = nn.CrossEntropyLoss(ignore_index=0, reduction="sum")
        train_val_peak = 0

        def observe():
            nonlocal train_val_peak
            if device == "cuda":
                train_val_peak = max(
                    train_val_peak,
                    cuda_memory_snapshot(device)["device_footprint_bytes"])

        best_val, best_state = -1.0, None
        for epoch in range(epochs):
            model.train()
            for batch in train_loader:
                opt.zero_grad()
                backward_logical_batch(model, batch, MICROBATCH_SIZE, loss_fn,
                                       device)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                sched.step()
                observe()
            val = greedy_exact(model, val_loader, device, UNTRUNCATED_MAX_TGT,
                               vocab.itos, observe if device == "cuda" else None)
            print(f"  seed{seed} epoch{epoch}: val_exact={val:.4f}", flush=True)
            if val > best_val:
                best_val = val
                best_state = {k: v.detach().cpu().clone()
                              for k, v in model.state_dict().items()}
        if best_state is not None:
            model.load_state_dict(best_state)

        checkpoint = results_dir / f"depth_interface_untrunc_s{seed}.pt"
        save_checkpoint_atomic(checkpoint, {
            "state_dict": model.state_dict(), "vocab": vocab.itos, "seed": seed,
            "config": {"d_model": 128, "max_tgt": UNTRUNCATED_MAX_TGT,
                       "max_len": UNTRUNCATED_MAX_LEN, "level_code": "recurrent",
                       "consumer": CONTROL_ARM, "batch_size": LOGICAL_BATCH_SIZE,
                       "microbatch_size": MICROBATCH_SIZE,
                       "eval_batch_size": EVAL_BATCH_SIZE,
                       "memory_fraction": PER_PROCESS_MEMORY_FRACTION}})

        train_val_memory = eval_memory = None
        if device == "cuda":
            train_val_memory = {
                "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
                "peak_device_footprint_bytes": train_val_peak}
            torch.cuda.reset_peak_memory_stats(device)
            eval_peak = cuda_memory_snapshot(device)["device_footprint_bytes"]

        def eval_observe():
            nonlocal eval_peak
            if device == "cuda":
                eval_peak = max(
                    eval_peak,
                    cuda_memory_snapshot(device)["device_footprint_bytes"])

        def tf(dataset):
            loader = DataLoader(dataset, batch_size=EVAL_BATCH_SIZE,
                                shuffle=False, collate_fn=collate)
            return teacher_forced_diagnostics(
                model, loader, device, vocab.itos,
                eval_observe if device == "cuda" else None)

        tf_all = tf(ood_all_ds)
        tf_kept = tf(ood_kept_ds)
        tf_excl = tf(ood_excl_ds)
        cuda_memory = None
        if device == "cuda":
            cuda_memory = {
                "pre_model_device_footprint_bytes": pre_footprint,
                "train_validation": train_val_memory,
                "final_evaluation": {
                    "peak_allocated_bytes": torch.cuda.max_memory_allocated(
                        device),
                    "peak_reserved_bytes": torch.cuda.max_memory_reserved(
                        device),
                    "peak_device_footprint_bytes": eval_peak}}

        result = {
            "experiment": "depth-interface-untruncated-treatment",
            "consumer": CONTROL_ARM, "seed": seed, "params": n_params,
            "level_code": "recurrent", "epochs": epochs,
            "max_tgt": UNTRUNCATED_MAX_TGT, "max_len": UNTRUNCATED_MAX_LEN,
            "batch_size": LOGICAL_BATCH_SIZE,
            "microbatch_size": MICROBATCH_SIZE,
            "eval_batch_size": EVAL_BATCH_SIZE,
            "memory_fraction": PER_PROCESS_MEMORY_FRACTION,
            "data_sha256": data_sha,
            "device": device,
            "val_greedy_best": best_val,
            "eval_mode": "teacher-forced",
            "ood_untruncated": {
                "generated": ood_all_ds.total_rows,
                "kept": len(ood_all_ds),
                "step_perfect_rate": tf_all["step_perfect_rate"],
                "examples": tf_all["examples"]},
            "ood_control_kept_subset": {
                "n": len(ood_kept_ds),
                "step_perfect_rate": tf_kept["step_perfect_rate"]},
            "ood_control_excluded_subset": {
                "n": len(ood_excl_ds),
                "step_perfect_rate": tf_excl["step_perfect_rate"]},
            "cuda_memory": cuda_memory,
        }
        out = results_dir / f"depth_interface_untrunc_s{seed}.json"
        atomic_write_json(out, result)
        print(f"DONE untruncated seed={seed} "
              f"untrunc_tf={tf_all['step_perfect_rate']:.4f} "
              f"kept_tf={tf_kept['step_perfect_rate']:.4f} "
              f"excl_tf={tf_excl['step_perfect_rate']:.4f}", flush=True)


def treatment_accounting(data_dir: Path, results_dir: Path,
                         score_subsets: bool = True) -> dict | None:
    """Read the untruncated address runs (teacher-forced metrics + footprints)."""
    per_seed = []
    for seed in SEEDS:
        path = results_dir / f"depth_interface_untrunc_s{seed}.json"
        if not path.exists():
            return None
        row = json.loads(path.read_text(encoding="utf-8"))
        ood = row["ood_untruncated"]
        if ood["kept"] != ood["generated"]:
            raise ValueError(
                "treatment OOD is not fully untruncated: "
                f"{ood['kept']}/{ood['generated']} kept")
        per_seed.append({
            "seed": seed,
            "params": row["params"],
            "max_tgt": row["max_tgt"],
            "max_len": row["max_len"],
            "untruncated_step_perfect": ood["step_perfect_rate"],
            "kept_step_perfect": row["ood_control_kept_subset"][
                "step_perfect_rate"],
            "excluded_step_perfect": row["ood_control_excluded_subset"][
                "step_perfect_rate"],
            "excluded_n": row["ood_control_excluded_subset"]["n"],
            "generated": ood["generated"],
            "cuda_memory": row.get("cuda_memory"),
        })
    return {
        "arm": CONTROL_ARM,
        "eval_mode": "teacher-forced",
        "max_tgt": UNTRUNCATED_MAX_TGT,
        "max_len": UNTRUNCATED_MAX_LEN,
        "untruncated_step_perfect": [i["untruncated_step_perfect"]
                                     for i in per_seed],
        "untruncated_step_perfect_mean": statistics.mean(
            i["untruncated_step_perfect"] for i in per_seed),
        "kept_step_perfect_mean": statistics.mean(
            i["kept_step_perfect"] for i in per_seed),
        "excluded_step_perfect": [i["excluded_step_perfect"] for i in per_seed],
        "params": sorted({i["params"] for i in per_seed}),
        "per_seed": per_seed,
    }


def control_retained_tf(results_dir: Path, arm: str = CONTROL_ARM) -> list:
    """The control arm's retained teacher-forced OOD step-perfect, per seed."""
    rates = []
    for seed in SEEDS:
        path = results_dir / f"depth_{arm}_s{seed}.json"
        row = json.loads(path.read_text(encoding="utf-8"))
        rates.append(row["ood_diagnostics"]["step_perfect_rate"])
    return rates


def adjudicate(data_dir: Path, results_dir: Path,
               score_subsets: bool = True) -> dict:
    control = control_accounting(results_dir)
    control_retained_tf_rates = control_retained_tf(results_dir, CONTROL_ARM)
    localization = retained_localization(results_dir, CONTROL_ARM)
    treatment = treatment_accounting(data_dir, results_dir, score_subsets)

    address = control[CONTROL_ARM]
    # P-DI1: unconditional strictly below retained for every arm; ordering kept;
    # exclusions entirely depth 4/5.
    uncond_below = all(
        control[arm]["unconditional_mean"] < control[arm]["retained_mean"]
        for arm in ARMS)
    retained_order = [
        arm for arm in sorted(ARMS, key=lambda a: -control[a]["retained_mean"])]
    uncond_order = [
        arm for arm in sorted(ARMS, key=lambda a: -control[a]["unconditional_mean"])]
    ordering_preserved = retained_order == uncond_order
    address_best = (retained_order[0] == CONTROL_ARM
                    and uncond_order[0] == CONTROL_ARM)
    excluded_depths = {
        depth for depth, stats in address["by_depth"].items()
        if stats["excluded"] > 0}
    exclusions_are_deep = excluded_depths.issubset({"4", "5"}) and bool(
        excluded_depths)
    pdi1 = (uncond_below and ordering_preserved and address_best
            and exclusions_are_deep)

    pdi2 = None
    pdi3 = None
    if treatment is not None:
        # Teacher-forced baseline: the control's retained OOD step-perfect,
        # scaled onto the full generated denominator (the excluded rows the
        # control could not emit count as failures) -- the honest unconditional
        # teacher-forced level the enlarged budget must beat to "move OOD".
        control_retained_tf_mean = statistics.mean(control_retained_tf_rates)
        control_uncond_tf = control_retained_tf_mean * address["kept"] / address[
            "generated"]
        treat_untrunc = treatment["untruncated_step_perfect_mean"]
        # Negative: the enlarged budget does not lift untruncated teacher-forced
        # OOD above the control unconditional level by the materiality bar.
        does_not_move = treat_untrunc <= control_uncond_tf + MIN_EFFECT
        excluded_scores = treatment["excluded_step_perfect"]
        excluded_low = (bool(excluded_scores)
                        and max(excluded_scores) < EXCLUDED_SUBSET_CEILING)
        pdi2 = {
            "prediction": P_DI2,
            "eval_mode": "teacher-forced (step-perfect)",
            "control_retained_tf_mean": control_retained_tf_mean,
            "control_unconditional_tf_mean": control_uncond_tf,
            "treatment_untruncated_tf_mean": treat_untrunc,
            "treatment_kept_subset_tf_mean": treatment["kept_step_perfect_mean"],
            "materiality_bar": MIN_EFFECT,
            "budget_does_not_move_ood": does_not_move,
            "excluded_subset_tf_step_perfect": excluded_scores,
            "excluded_subset_below_ceiling": excluded_low,
            "excluded_subset_ceiling": EXCLUDED_SUBSET_CEILING,
            "max_trained_target_length": MAX_TRAINED_TARGET_LENGTH,
            "status": ("FIRED" if does_not_move and excluded_low else "MISSED"),
            "adjudication_kind": "interface_manipulation",
        }

    # P-DI3: predicted the retained first error concentrates in the LATEST
    # deciles.  Adjudicated on the record; a miss keeps the prediction and
    # attaches a correction rather than editing the registered wording.
    first_error = localization["first_error_fraction_by_decile_mean"]
    if first_error:
        late = sum(v for d, v in first_error.items() if int(d) >= 7)
        early = sum(v for d, v in first_error.items() if int(d) <= 2)
        peak_decile = max(first_error, key=lambda d: first_error[d])
        fired = exclusions_are_deep and late > early
        pdi3 = {
            "prediction": P_DI3,
            "exclusions_depth_set": sorted(excluded_depths),
            "exclusions_are_depth_4_5": exclusions_are_deep,
            "retained_first_error_late_deciles_7to9": late,
            "retained_first_error_early_deciles_0to2": early,
            "first_error_concentrates_late": late > early,
            "first_error_peak_decile": peak_decile,
            "first_error_fraction_by_decile_mean": first_error,
            "status": "FIRED" if fired else "MISSED",
            "adjudication_kind": "cliff_localization",
        }
        if not fired:
            pdi3["correction"] = (
                "MISS: the retained cliff does NOT concentrate in the late "
                f"deciles. {early:.3f} of erroneous retained OOD rows take their "
                f"first teacher-forced error in deciles 0-2 (peak at decile "
                f"{peak_decile}) versus {late:.3f} in deciles 7-9, so on "
                "untruncated OOD the failure is bimodal: retained rows derail "
                "EARLY -- the model loses the deep structure near the start of "
                "the decode -- while the 550 capacity exclusions sit at the "
                "opposite extreme, all depth 4/5 and beyond the copy budget. "
                "The cliff is still localized (an early structural break plus a "
                "hard budget wall), just not where P-DI3 predicted.")

    treatment_safety = None
    if treatment is not None:
        control_row = json.loads(
            (results_dir / f"depth_{CONTROL_ARM}_s0.json").read_text(
                encoding="utf-8"))
        device_total = control_row["run_provenance"]["runtime_environment"][
            "device_total_bytes"]
        reserved_limit = int(device_total * PER_PROCESS_MEMORY_FRACTION)
        device_limit = int(device_total * MAX_DEVICE_FOOTPRINT_FRACTION)
        rows = []
        within = True
        for entry in treatment["per_seed"]:
            memory = entry.get("cuda_memory")
            if not memory:
                within = None
                continue
            for phase in ("train_validation", "final_evaluation"):
                pm = memory[phase]
                ok = (pm["peak_reserved_bytes"] <= reserved_limit
                      and pm["peak_device_footprint_bytes"] < device_limit)
                within = within and ok
                rows.append({
                    "seed": entry["seed"], "phase": phase,
                    "peak_reserved_bytes": pm["peak_reserved_bytes"],
                    "peak_device_footprint_bytes":
                    pm["peak_device_footprint_bytes"],
                    "within_caps": ok})
        treatment_safety = {
            "device_total_bytes": device_total,
            "reserved_limit_bytes": reserved_limit,
            "device_footprint_limit_bytes": device_limit,
            "all_phases_within_caps": within,
            "rows": rows,
        }

    result = {
        "experiment": "depth-interface-v0.8-item5",
        "seeds": list(SEEDS),
        "interface_variable": "copy_budget(max_tgt,max_len)",
        "control": {
            "arm_budget": {"max_tgt": CONTROL_MAX_TGT, "max_len": CONTROL_MAX_LEN},
            "arms": control,
        },
        "treatment": treatment,
        "treatment_safety": treatment_safety,
        "retained_localization": localization,
        "adjudication": {
            "P-DI1": {
                "prediction": P_DI1,
                "unconditional_below_retained_all_arms": uncond_below,
                "retained_ordering": retained_order,
                "unconditional_ordering": uncond_order,
                "ordering_preserved": ordering_preserved,
                "address_best_both_metrics": address_best,
                "exclusions_depth_set": sorted(excluded_depths),
                "status": "FIRED" if pdi1 else "MISSED",
                "adjudication_kind": "blind_spot_removal",
            },
            "P-DI2": pdi2 if pdi2 is not None else {
                "prediction": P_DI2,
                "status": "PENDING",
                "reason": "treatment runs not present",
            },
            "P-DI3": pdi3 if pdi3 is not None else {
                "prediction": P_DI3, "status": "PENDING"},
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path,
                        default=ROOT / "experiments" / "results")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--train", action="store_true",
                        help="retrain address-only at the enlarged copy budget")
    parser.add_argument("--no-subset-eval", action="store_true",
                        help="skip loading treatment checkpoints for subset "
                             "scoring (accounting only)")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    args.data_dir = args.data_dir.resolve()
    args.results_dir = args.results_dir.resolve()
    if args.train:
        train_untruncated(args.data_dir, args.results_dir, args.seeds,
                          args.epochs)
    result = adjudicate(args.data_dir, args.results_dir,
                        score_subsets=not args.no_subset_eval)
    out = args.out or args.results_dir / "depth_interface.json"
    atomic_write_json(out, result)
    print(json.dumps(result["adjudication"], indent=2), flush=True)


if __name__ == "__main__":
    main()
