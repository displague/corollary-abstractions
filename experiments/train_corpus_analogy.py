#!/usr/bin/env python3
"""First corpus-analogy MODEL ARM, reported against the frozen blind ceilings.

WHAT THIS IS (and, more importantly, is not)
--------------------------------------------
`experiments/corpus_analogy_split.py` froze the split and the capability-blind
ceiling table (v0.7 item 5, v0.8 item 2's shape holdout). No model was trained
there; the split and its ceilings ARE the slice. THIS module trains the first
learned pointer on the split's TRAIN rows and reports its exact-match on each
holdout's HELD rows, against the same blind ceilings:

    family 0.400 | discipline 0.9318 | vocabulary 0.3976 | shape 0.1069

The shape ceiling 0.1069 is the strict one and the release-gate target. The
discipline ceiling 0.9318 is NEAR-VACUOUS (a blind nearest-template replay
already scores it) and is never cited alone as difficulty.

POINTING, NOT REASONING (restated so no number here is sold as reasoning)
------------------------------------------------------------------------
v0.7 disclosed (P-CS2, and the shape adjudication) that this task is CLOSED-FORM
from the token stream PLUS two corpus declarations, each verified in the split
file: (1) every slot's parameter/variable (P/V) class, and (2) the identity
table (`*` has identity 1, `+` has identity 0). With BOTH, `symbolic_typed_input`
scores 1.000 on every holdout including shape; with NEITHER, the token-stream
solver `symbolic_input_only` scores only 0.458/0.545/0.651/0.290. So the residual
above the token stream IS those two declarations -- not reasoning.

This model receives NEITHER declaration. It sees only the raw serialized token
stream `A <sep> B <sep> C` and must POINT: every decode step copies an input
position (dedup makes every held target novel, so retrieval scores 0 by
construction; only a genuine pointer can emit a held target). Its vocabulary is
the full symbol inventory so a copied position decodes back to its own token --
that is the round-trip a pointer needs, NOT the P/V class or the identity table,
neither of which is ever handed to the model. Therefore:

  * A model score AT/BELOW a blind ceiling means it has internalized no more of
    the pointing mechanism than the cheapest blind control (nearest-template
    replay) -- it is not pointing past the leak the ceiling measures.
  * A model score ABOVE the strict shape ceiling 0.1069 means it has
    internalized the POINTER (the A<->C structural correspondence that realizes
    a target whose every atom is present but whose arrangement is novel) BETTER
    than a blind replay -- and STILL not the two declarations, which is the only
    thing that would carry it to the 1.000 sighted roof. Above-ceiling is a
    pointing result, never a reasoning result.

REGISTERED PREDICTIONS (P-CM*, committed BEFORE the training run; a miss is
recorded MISSED with a correction appended, the split is NOT re-rolled)
-----------------------------------------------------------------------
P-CM1  The trained pointer BEATS the strict shape blind ceiling 0.1069 (mean
       over seeds strictly above 0.1069). Rationale: the pointer is trained on
       267 shape-train rows to realize the exact A<->C correspondence the
       nearest-template control only approximates by edit distance; a learned
       pointer should exceed a blind replay on the very mechanism it is trained
       for, even on unseen shapes. If it does NOT, that is a valid gate result
       and is reported as the pointer failing to beat the blind replay on
       unseen shapes.

P-CM2  The trained pointer BEATS the family (0.400) and vocabulary (0.3976)
       blind ceilings. These holdouts leave the target's shape reachable
       (family holds out a typed NAME; vocabulary holds out rare target words
       but leaves them pointable), so a trained pointer has a standing shape to
       point through and should clear a blind replay comfortably.

P-CM3  The trained pointer does NOT beat the near-vacuous discipline ceiling
       0.9318 outright by a wide margin, and may fall short of it: 0.9318 is
       already near-ceiling for a blind control, so there is little headroom and
       beating it is not evidence of difficulty. Whatever the model scores here,
       the discipline holdout stays labelled near-vacuous.

P-CM4  No model number is at or near the sighted 1.000 roof on any holdout,
       because the model is denied both corpus declarations that close the gap
       to 1.000. A model near 1.000 would mean the pointing task leaks the
       declarations through the token stream after all, and would be reported as
       such rather than as reasoning.

ADJUDICATION OF P-CM* (appended after the single 3-seed run; the registrations
above are unchanged and the split was NOT re-rolled)
--------------------------------------------------------------------------------
3 seeds (0/1/2), 120 epochs each, train exact-match >=0.9925 (the pointer is
fully fit on every axis). Held exact-match, mean +/- sd over seeds, vs the frozen
blind ceilings (committed artifact
`experiments/results/corpus_analogy_model_arm.json`; exact per-seed values vary
run-to-run under CUDA nondeterminism and are NOT pinned in the tests):

    family      0.168 +/- 0.013   ceiling 0.400   BELOW  (-0.232)
    discipline  0.491 +/- 0.012   ceiling 0.9318  BELOW  (-0.441)  [near-vacuous]
    vocabulary  0.201 +/- 0.028   ceiling 0.3976  BELOW  (-0.197)
    shape       0.104 +/- 0.012   ceiling 0.1069  BELOW  (-0.003)  [STRICT]

The blind nearest-template replay beats the trained pointer on ALL FOUR
holdouts. The trained model arm beats NO blind ceiling.

  P-CM1 MISSED. The pointer scored shape 0.104 +/- 0.012, mean below the strict
      ceiling 0.1069 (14/131). Its three seeds STRADDLE the ceiling
      (15/131=0.1145 above, 14/131=0.1069 exactly at -- and strict `>` counts
      at-ceiling as not beating -- 12/131=0.0916 below), so the honest reading is
      that the fully-trained pointer sits essentially AT the blind ceiling on
      genuinely unseen shapes, within CUDA run-to-run nondeterminism, and does
      not clear it. On unseen shapes the learned pointer has internalized no more
      of the pointing mechanism than a blind edit-distance replay. This is a
      VALID gate result and is reported as the model NOT beating the strict
      ceiling.
  P-CM2 MISSED. family 0.168 < 0.400 and vocabulary 0.201 < 0.3976 -- the pointer
      beats NEITHER, and by wide margins. Correction: the cheap blind baseline
      wins the whole lane (the v0.7 pattern), not merely the strict shape cut.
      Even where the target's shape is reachable in training, the learned pointer
      generalizes BELOW a blind nearest-template replay.
  P-CM3 FIRED. discipline 0.491 << 0.9318: the pointer falls well short of the
      near-vacuous ceiling and does not beat it. The discipline holdout stays
      labelled near-vacuous and is never cited alone as difficulty.
  P-CM4 FIRED. The largest model mean is discipline 0.491, nowhere near the
      sighted 1.000 roof. Denied both corpus declarations, the model gets
      nowhere near closing the gap to 1.000 -- so no number here can be, or is,
      sold as reasoning.

DISCIPLINE
----------
Seeds torch/numpy/python and record them. `torch.cuda.set_per_process_memory_
fraction(0.7)` before any allocation; checkpoints written atomically; allocated/
reserved/whole-device footprints recorded. Any CUDA error falls back to CPU and
says so. The split is frozen; this module trains and reports only.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "scripts"))

import corpus_analogy_split as cas  # noqa: E402
from tokenizers import Vocab  # noqa: E402
from train_span import MAX_LEVELS, tree_paths  # noqa: E402
from train_analogy import (  # noqa: E402
    GEN_TOKENS,
    BOS,
    EOS,
    AnalogyPointer,
    collate,
    cuda_memory_snapshot,
    greedy_exact,
    save_checkpoint_atomic,
    seg_coords,
)
from depth_consumer_protocol import (  # noqa: E402
    MAX_DEVICE_FOOTPRINT_FRACTION,
    PER_PROCESS_MEMORY_FRACTION,
    atomic_write_json,
)

CEILINGS_PATH = ROOT / "experiments" / "results" / "corpus_analogy_v07_ceilings.json"

# The frozen blind ceilings this arm is reported against (v0.7 item 5 +
# v0.8 shape holdout). Hard-coded here so the reporting harness is
# self-checking: `load_frozen_ceilings` asserts these equal the committed
# ceiling table, and the test pins BOTH these values and that agreement. The
# strict release-gate target is `shape`; `discipline` is near-vacuous.
EXPECTED_BLIND_CEILINGS = {
    "family": 0.4,
    "discipline": 0.9318181818181818,
    "vocabulary": 0.39759036144578314,
    "shape": 0.10687022900763359,
}
STRICT_HOLDOUT = "shape"
NEAR_VACUOUS_HOLDOUT = "discipline"


# ---------------------------------------------------------------------------
# reporting harness (pure; pinned by tests, does not touch torch)
# ---------------------------------------------------------------------------

def load_frozen_ceilings(path: Path = CEILINGS_PATH) -> dict[str, float]:
    """The blind ceiling per holdout, read from the committed table.

    Verified against `EXPECTED_BLIND_CEILINGS` so a silent change to the frozen
    split (which would move a ceiling) breaks loudly here instead of quietly
    re-baselining the model verdict.
    """
    table = json.loads(path.read_text(encoding="utf-8"))["ceilings"]
    ceilings = {name: entry["blind_ceiling"] for name, entry in table.items()}
    for name, expected in EXPECTED_BLIND_CEILINGS.items():
        got = ceilings.get(name)
        if got is None or abs(got - expected) > 1e-9:
            raise ValueError(
                f"frozen ceiling for {name!r} is {got!r}, expected {expected!r}; "
                "the split has changed -- do not report a model against a moved "
                "ceiling")
    return ceilings


def summarize_scores(per_seed: list[float]) -> dict:
    """Mean and (sample) sd of a per-seed score list, with the raw list kept."""
    if not per_seed:
        raise ValueError("no per-seed scores to summarize")
    mean = statistics.fmean(per_seed)
    sd = statistics.stdev(per_seed) if len(per_seed) > 1 else 0.0
    return {"mean": mean, "sd": sd, "per_seed": list(per_seed),
            "n_seeds": len(per_seed)}


def compare_to_ceiling(model_mean: float, ceiling: float) -> dict:
    """Whether the model's mean strictly beats a blind ceiling, and by how much.

    Strict `>`: matching a blind control is NOT beating it. `margin` is signed
    (positive = above the ceiling).
    """
    return {"ceiling": ceiling, "model_mean": model_mean,
            "margin": model_mean - ceiling,
            "beats_ceiling": model_mean > ceiling}


def build_holdout_report(name: str, per_seed: list[float],
                         ceiling: float) -> dict:
    summary = summarize_scores(per_seed)
    verdict = compare_to_ceiling(summary["mean"], ceiling)
    entry = {"model_exact": summary, **verdict,
             "is_strict_ceiling": name == STRICT_HOLDOUT,
             "is_near_vacuous": name == NEAR_VACUOUS_HOLDOUT}
    return entry


# ---------------------------------------------------------------------------
# dataset (pointing rows; no `depth` field -- unlike the synthetic AnalogyDataset)
# ---------------------------------------------------------------------------

class PointerRowDataset(Dataset):
    """The split's pointer rows as (ids, coords, actions, tgt-coords, tokens).

    Mirrors `train_analogy.AnalogyDataset` item construction exactly, minus its
    synthetic-only `depth` requirement: corpus-analogy rows carry no depth.
    """

    def __init__(self, rows: list[dict], vocab: Vocab, max_len: int,
                 max_tgt: int):
        self.items = []
        self.total_rows = len(rows)
        self.dropped_max_len = 0
        self.dropped_max_tgt = 0
        G = len(GEN_TOKENS)
        for r in rows:
            toks = r["tokens_struct"]
            ids = vocab.encode(toks)
            if len(ids) > max_len:
                self.dropped_max_len += 1
                continue
            coords = seg_coords(toks)
            acts = [BOS] + [G + p + 1 for p in r["target_positions"]] + [EOS]
            if len(acts) > max_tgt:
                self.dropped_max_tgt += 1
                continue
            tpaths = tree_paths(r["target_tokens"])
            tcoords = [[0] * MAX_LEVELS] + tpaths
            self.items.append((
                torch.tensor(ids, dtype=torch.long),
                torch.tensor(coords, dtype=torch.long),
                torch.tensor(acts, dtype=torch.long),
                torch.tensor(tcoords, dtype=torch.long),
                r["target_tokens"]))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


# ---------------------------------------------------------------------------
# split construction (from the frozen builder; no re-rolling)
# ---------------------------------------------------------------------------

def build_split_rows() -> tuple[list[dict], dict[str, dict[str, str]], list]:
    """Every pointer row, plus the frozen train/holdout assignment per axis.

    Uses `corpus_analogy_split`'s own builder/dedup/split so this arm trains on
    exactly the frozen rows -- there is no seed or threshold to re-roll.
    """
    quads = cas.dedup_by_target(cas.build_quadruples())
    splits = cas.build_splits(quads)
    rows_by_target = {q.target: cas.pointer_row(q) for q in quads}
    return quads, splits, rows_by_target


def axis_rows(quads, splits, rows_by_target, axis: str
              ) -> tuple[list[dict], list[dict]]:
    assignment = splits[axis]
    train, held = [], []
    for q in quads:
        (train if assignment[q.target] == "train" else held).append(
            rows_by_target[q.target])
    return train, held


def full_vocabulary(rows_by_target: dict[str, dict]) -> Vocab:
    """One symbol inventory over ALL rows.

    A pointer decodes a copied position back to ITS OWN token, so the vocabulary
    must round-trip every symbol that can appear at test time. This is the
    identity of the symbols in the token stream -- NOT the P/V class table and
    NOT the arithmetic identity table, the two corpus declarations the model is
    deliberately denied. Held targets stay novel by dedup; the vocabulary hands
    the model no held ANSWER, only the alphabet its input is written in.
    """
    tokens: set[str] = set()
    for row in rows_by_target.values():
        tokens.update(row["tokens_struct"])
    return Vocab(tokens)


# ---------------------------------------------------------------------------
# a single (seed, axis) training run
# ---------------------------------------------------------------------------

def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train_one(train_rows: list[dict], held_rows: list[dict], vocab: Vocab,
              *, seed: int, device: str, epochs: int, d_model: int,
              batch_size: int, lr: float, max_len: int, max_tgt: int,
              save_model: Path | None, footprint: dict) -> dict:
    """Train the pointer on `train_rows`, report exact-match on `held_rows`."""
    seed_everything(seed)
    train_ds = PointerRowDataset(train_rows, vocab, max_len, max_tgt)
    held_ds = PointerRowDataset(held_rows, vocab, max_len, max_tgt)
    gen = torch.Generator().manual_seed(seed)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              collate_fn=collate, generator=gen)
    held_loader = DataLoader(held_ds, batch_size=batch_size, shuffle=False,
                             collate_fn=collate)

    model = AnalogyPointer(len(vocab), d_model, max_tgt=max_tgt,
                           level_code="table", consumer="address").to(device)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    loss_fn = torch.nn.CrossEntropyLoss(ignore_index=0, reduction="sum")

    if device == "cuda":
        torch.cuda.reset_peak_memory_stats(device)

    def observe() -> None:
        snap = cuda_memory_snapshot(device)
        footprint["peak_allocated_bytes"] = max(
            footprint["peak_allocated_bytes"], snap["allocated_bytes"])
        footprint["peak_reserved_bytes"] = max(
            footprint["peak_reserved_bytes"], snap["reserved_bytes"])
        footprint["peak_device_footprint_bytes"] = max(
            footprint["peak_device_footprint_bytes"],
            snap["device_footprint_bytes"])

    model.train()
    for _epoch in range(epochs):
        for x, crd, mask, y, tc, _ in train_loader:
            x, crd, mask, y, tc = (t.to(device)
                                   for t in (x, crd, mask, y, tc))
            opt.zero_grad()
            memory = model.encode(x, crd, mask)
            memory = model.prepare_memory(memory, crd[..., 1:])
            logits = model.decode(memory, mask, y[:, :-1],
                                  tc[:, : y.size(1) - 1])
            valid = int((y[:, 1:] != 0).sum())
            loss = loss_fn(logits.reshape(-1, logits.size(-1)),
                           y[:, 1:].reshape(-1)) / max(valid, 1)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        if device == "cuda":
            observe()

    train_exact = greedy_exact(model, train_loader, device, max_tgt, vocab.itos,
                               observe if device == "cuda" else None)
    held_exact = greedy_exact(model, held_loader, device, max_tgt, vocab.itos,
                              observe if device == "cuda" else None)

    if save_model is not None:
        save_checkpoint_atomic(save_model, {
            "state_dict": model.state_dict(), "vocab": vocab.itos, "seed": seed,
            "config": {"d_model": d_model, "max_tgt": max_tgt,
                       "max_len": max_len, "level_code": "table",
                       "consumer": "address"}})
    return {"held_exact": held_exact, "train_exact": train_exact,
            "params": n_params, "train_n": len(train_ds),
            "held_n": len(held_ds),
            "dropped": {"max_len": held_ds.dropped_max_len
                        + train_ds.dropped_max_len,
                        "max_tgt": held_ds.dropped_max_tgt
                        + train_ds.dropped_max_tgt}}


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

def run(seeds: list[int], *, epochs: int, d_model: int, batch_size: int,
        lr: float, max_len: int, max_tgt: int, memory_fraction: float,
        save_dir: Path | None, out: Path) -> dict:
    ceilings = load_frozen_ceilings()
    quads, splits, rows_by_target = build_split_rows()
    vocab = full_vocabulary(rows_by_target)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    fell_back = False
    cuda_error = None
    if device == "cuda":
        try:
            torch.cuda.set_per_process_memory_fraction(memory_fraction)
            device_total = torch.cuda.get_device_properties(
                torch.cuda.current_device()).total_memory
        except RuntimeError as exc:  # pragma: no cover - hardware dependent
            device, fell_back, cuda_error = "cpu", True, str(exc)
            device_total = None
    else:
        device_total = None

    axes = list(EXPECTED_BLIND_CEILINGS)
    t0 = time.time()

    def sweep(dev: str) -> dict:
        """One full seeds x axes sweep on `dev`, from clean footprint counters.

        Returned wholesale so a CUDA failure can restart the ENTIRE sweep on CPU
        rather than splice a half-GPU/half-CPU run with mismatched seed counts.
        """
        footprint = {"peak_allocated_bytes": 0, "peak_reserved_bytes": 0,
                     "peak_device_footprint_bytes": 0}
        held: dict[str, list[float]] = defaultdict(list)
        train: dict[str, list[float]] = defaultdict(list)
        log: list[dict] = []
        params = None
        for seed in seeds:
            for axis in axes:
                train_rows, held_rows = axis_rows(quads, splits,
                                                  rows_by_target, axis)
                save_model = (None if save_dir is None else
                              save_dir / f"corpus_analogy_{axis}_s{seed}.pt")
                result = train_one(
                    train_rows, held_rows, vocab, seed=seed, device=dev,
                    epochs=epochs, d_model=d_model, batch_size=batch_size,
                    lr=lr, max_len=max_len, max_tgt=max_tgt,
                    save_model=save_model, footprint=footprint)
                params = result["params"]
                held[axis].append(result["held_exact"])
                train[axis].append(result["train_exact"])
                log.append({"seed": seed, "axis": axis, **result})
                print(f"seed={seed} axis={axis} "
                      f"held_exact={result['held_exact']:.4f} "
                      f"train_exact={result['train_exact']:.4f} "
                      f"(ceiling {ceilings[axis]:.4f})", flush=True)
        return {"footprint": footprint, "held": held, "train": train,
                "log": log, "params": params}

    try:
        swept = sweep(device)
    except RuntimeError as exc:  # pragma: no cover - CUDA fallback
        if device != "cuda":
            raise
        print(f"CUDA failure ({exc}); restarting the whole sweep on CPU",
              flush=True)
        device, fell_back, cuda_error = "cpu", True, str(exc)
        device_total = None
        swept = sweep(device)

    footprint = swept["footprint"]
    per_seed_scores = swept["held"]
    per_seed_train = swept["train"]
    run_log = swept["log"]
    params = swept["params"]

    holdouts = {axis: {**build_holdout_report(axis, per_seed_scores[axis],
                                              ceilings[axis]),
                       "train_exact": summarize_scores(per_seed_train[axis])}
                for axis in axes}

    # whole-device safety verdict against the house cap
    within_cap = None
    device_footprint_fraction = None
    if device == "cuda" and device_total:
        device_footprint_fraction = (
            footprint["peak_device_footprint_bytes"] / device_total)
        within_cap = (device_footprint_fraction < MAX_DEVICE_FOOTPRINT_FRACTION)

    report = {
        "task": "corpus_analogy_model_arm",
        "device": device,
        "fell_back_to_cpu": fell_back,
        "cuda_error": cuda_error,
        "memory_fraction": memory_fraction if device == "cuda" else None,
        "per_process_memory_fraction_house_rule": PER_PROCESS_MEMORY_FRACTION,
        "max_device_footprint_fraction_house_rule": MAX_DEVICE_FOOTPRINT_FRACTION,
        "seeds": list(seeds),
        "params": params,
        "config": {"epochs": epochs, "d_model": d_model,
                   "batch_size": batch_size, "lr": lr, "max_len": max_len,
                   "max_tgt": max_tgt, "level_code": "table",
                   "consumer": "address"},
        "frozen_blind_ceilings": ceilings,
        "strict_holdout": STRICT_HOLDOUT,
        "near_vacuous_holdout": NEAR_VACUOUS_HOLDOUT,
        "holdouts": holdouts,
        "beats_strict_shape_ceiling": holdouts[STRICT_HOLDOUT]["beats_ceiling"],
        "gpu_footprint": {
            **footprint,
            "device_total_bytes": device_total,
            "device_footprint_fraction": device_footprint_fraction,
            "within_house_cap": within_cap,
        },
        "seconds": round(time.time() - t0, 1),
        "pointing_not_reasoning": (
            "The model receives only the raw token stream and points; it is "
            "denied both corpus declarations (per-slot P/V class and the "
            "identity table) that carry symbolic_typed_input to 1.000. A score "
            "above a blind ceiling is a POINTING result -- the learned A<->C "
            "correspondence beating a blind edit-distance replay -- never a "
            "reasoning result."),
        "run_log": run_log,
    }
    atomic_write_json(out, report)
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--max-len", type=int, default=96)
    ap.add_argument("--max-tgt", type=int, default=64)
    ap.add_argument("--memory-fraction", type=float,
                    default=PER_PROCESS_MEMORY_FRACTION)
    ap.add_argument("--save-dir", type=Path,
                    default=ROOT / "experiments" / "results" / "checkpoints")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "experiments" / "results" /
                    "corpus_analogy_model_arm.json")
    args = ap.parse_args()
    report = run(args.seeds, epochs=args.epochs, d_model=args.d_model,
                 batch_size=args.batch_size, lr=args.lr, max_len=args.max_len,
                 max_tgt=args.max_tgt, memory_fraction=args.memory_fraction,
                 save_dir=args.save_dir, out=args.out)
    print(json.dumps({"beats_strict_shape_ceiling":
                      report["beats_strict_shape_ceiling"],
                      "shape": report["holdouts"]["shape"]["model_exact"],
                      "device": report["device"]}, indent=2))


if __name__ == "__main__":
    main()
