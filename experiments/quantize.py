"""Size-reduction pass: accuracy-vs-bytes for a trained checkpoint.

Ladder: fp32 -> fp16 -> int8 dynamic quant (Linear layers) -> int8 + magnitude
pruning at rising sparsity. Accuracy measured on test and OOD splits each rung.
CPU-only by design (int8 dynamic quant is CPU-backend), so it can run without
re-stressing the GPU.

Usage:
  python quantize.py --checkpoint results/twins_canon.pt --task twins --arm canon
"""

from __future__ import annotations

import argparse
import copy
import io
import json
from pathlib import Path

import torch

from tokenizers import SERIALIZERS, Vocab
from train import PairDataset, TinyTransformer, collate, evaluate, load_jsonl
from torch.utils.data import DataLoader


def state_bytes(model: torch.nn.Module) -> int:
    buf = io.BytesIO()
    torch.save(model.state_dict(), buf)
    return buf.getbuffer().nbytes


def prune_magnitude(model: torch.nn.Module, sparsity: float) -> torch.nn.Module:
    pruned = copy.deepcopy(model)
    with torch.no_grad():
        for name, p in pruned.named_parameters():
            if p.dim() < 2:  # keep biases/norms dense
                continue
            k = int(p.numel() * sparsity)
            if k == 0:
                continue
            threshold = p.abs().flatten().kthvalue(k).values
            p.mul_((p.abs() > threshold).to(p.dtype))
    return pruned


def sparse_bytes(model: torch.nn.Module, elem_bytes: float) -> int:
    """Idealized compressed size: nonzero payload + 4-byte indices for 2D
    weights, dense storage for the rest."""
    total = 0
    for p in model.parameters():
        if p.dim() < 2:
            total += p.numel() * elem_bytes
        else:
            nnz = int((p != 0).sum())
            total += nnz * (elem_bytes + 4)
    return int(total)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    cfg = ckpt["config"]
    vocab = Vocab(set(ckpt["vocab"]))
    vocab.itos = ckpt["vocab"]
    vocab.stoi = {t: i for i, t in enumerate(vocab.itos)}

    model = TinyTransformer(len(vocab.itos), cfg["d_model"], cfg["n_layers"],
                            max_len=cfg["max_len"])
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    loaders = {}
    for split in ["test", "ood"]:
        rows = load_jsonl(args.data_dir / f"{args.task}_{split}.jsonl")
        ds = PairDataset(rows, vocab, args.arm, cfg["max_len"])
        loaders[split] = DataLoader(ds, batch_size=256, collate_fn=collate)

    rungs = []

    def measure(label: str, m: torch.nn.Module, nbytes: int) -> None:
        acc = {s: evaluate(m, loaders[s], "cpu") for s in loaders}
        rungs.append({"rung": label, "bytes": nbytes,
                      "test_acc": acc["test"], "ood_acc": acc["ood"]})
        print(f"{label:24s} {nbytes/1e6:7.2f} MB  test={acc['test']:.4f} "
              f"ood={acc['ood']:.4f}", flush=True)

    measure("fp32", model, state_bytes(model))

    fp16 = copy.deepcopy(model).half()
    # fp16 inference on CPU is unsupported for some ops; measure size from
    # the fp16 state dict but evaluate the fp32-equivalent weights.
    fp16_bytes = state_bytes(fp16)
    roundtrip = copy.deepcopy(model)
    roundtrip.load_state_dict(
        {k: v.float() for k, v in fp16.state_dict().items()})
    measure("fp16 (roundtrip eval)", roundtrip, fp16_bytes)

    int8 = torch.ao.quantization.quantize_dynamic(
        copy.deepcopy(model), {torch.nn.Linear}, dtype=torch.qint8)
    measure("int8 dynamic", int8, state_bytes(int8))

    for sparsity in [0.3, 0.5, 0.7]:
        pruned = prune_magnitude(model, sparsity)
        pruned_int8 = torch.ao.quantization.quantize_dynamic(
            pruned, {torch.nn.Linear}, dtype=torch.qint8)
        measure(f"prune{int(sparsity*100)} + int8", pruned_int8,
                sparse_bytes(pruned, 1.0))

    out = args.out or Path("results") / f"quant_{args.task}_{args.arm}.json"
    out.write_text(json.dumps({
        "task": args.task, "arm": args.arm,
        "checkpoint": str(args.checkpoint), "rungs": rungs,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"-> {out}", flush=True)


if __name__ == "__main__":
    main()
