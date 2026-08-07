"""Train the same tiny transformer on one task/arm and report metrics.

Usage:
  python train.py --task twins --arm char --data-dir data --out results/twins_char.json
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from tokenizers import SERIALIZERS, Vocab, build_vocab
from train_span import MAX_LEVELS, MAX_SIB, tree_paths


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def pair_coords(tokens: list[str]) -> list[list[int]]:
    zero = [0] * MAX_LEVELS
    if "<sep>" in tokens:
        cut = tokens.index("<sep>")
        return ([[0] + zero]
                + [[0] + p for p in tree_paths(tokens[:cut])]
                + [[1] + zero]
                + [[1] + p for p in tree_paths(tokens[cut + 1:])])
    return [[0] + zero] + [[0] + p for p in tree_paths(tokens)]


class PairDataset(Dataset):
    def __init__(self, rows: list[dict], vocab: Vocab, arm: str, max_len: int):
        serialize = SERIALIZERS[arm]
        self.items = []
        self.n_truncated = 0
        for r in rows:
            toks = serialize(r)
            ids = vocab.encode(toks)
            coords = pair_coords(toks)  # aligns with CLS via leading origin row
            if len(ids) > max_len:
                ids = ids[:max_len]
                coords = coords[:max_len]
                self.n_truncated += 1
            self.items.append((torch.tensor(ids, dtype=torch.long),
                               torch.tensor(coords, dtype=torch.long),
                               r["label"]))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


def collate(batch):
    seqs, coords, labels = zip(*batch)
    max_len = max(len(s) for s in seqs)
    out = torch.zeros(len(seqs), max_len, dtype=torch.long)
    crd = torch.zeros(len(seqs), max_len, 1 + MAX_LEVELS, dtype=torch.long)
    mask = torch.zeros(len(seqs), max_len, dtype=torch.bool)
    for i, (s, c) in enumerate(zip(seqs, coords)):
        out[i, : len(s)] = s
        crd[i, : len(c)] = c
        mask[i, : len(s)] = True
    return out, crd, mask, torch.tensor(labels, dtype=torch.float32)


class TinyTransformer(nn.Module):
    def __init__(self, vocab_size: int, d_model: int = 128, n_layers: int = 4,
                 n_heads: int = 4, max_len: int = 1024, positions: str = "abs"):
        super().__init__()
        self.positions = positions
        self.embed = nn.Embedding(vocab_size, d_model, padding_idx=0)
        if positions == "abs":
            self.pos = nn.Embedding(max_len, d_model)
        else:
            self.seg_emb = nn.Embedding(2, d_model)
            self.path_emb = nn.Embedding(MAX_LEVELS * (MAX_SIB + 1), d_model)
            self.register_buffer("level_offsets",
                                 torch.arange(MAX_LEVELS) * (MAX_SIB + 1))
        layer = nn.TransformerEncoderLayer(
            d_model, n_heads, dim_feedforward=4 * d_model,
            dropout=0.1, batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, n_layers)
        self.head = nn.Sequential(
            nn.LayerNorm(d_model), nn.Linear(d_model, d_model), nn.GELU(),
            nn.Linear(d_model, 1))

    def forward(self, x, coords, mask):
        h = self.embed(x)
        if self.positions == "abs":
            pos = torch.arange(x.size(1), device=x.device).unsqueeze(0)
            h = h + self.pos(pos)
        else:
            paths = coords[..., 1:]
            emb = self.path_emb(paths + self.level_offsets)
            emb = emb * (paths > 0).unsqueeze(-1)
            h = h + emb.sum(dim=-2) + self.seg_emb(coords[..., 0])
        h = self.encoder(h, src_key_padding_mask=~mask)
        cls = h[:, 0]
        return self.head(cls).squeeze(-1)


def evaluate(model, loader, device) -> float:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, crd, mask, y in loader:
            x, crd, mask, y = x.to(device), crd.to(device), mask.to(device), y.to(device)
            logits = model(x, crd, mask)
            correct += ((logits > 0) == (y > 0.5)).sum().item()
            total += len(y)
    return correct / max(total, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=["twins", "equiv", "xlang", "qa", "syn", "realsyn"], required=True)
    ap.add_argument("--arm", choices=["char", "struct", "canon", "hybrid"], required=True)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--n-layers", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--positions", choices=["abs", "tree"], default="abs")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--save-model", type=Path, default=None)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    splits = {s: load_jsonl(args.data_dir / f"{args.task}_{s}.jsonl")
              for s in ["train", "val", "test", "ood"]}
    vocab = build_vocab(splits["train"], args.arm)
    datasets = {s: PairDataset(rows, vocab, args.arm, args.max_len)
                for s, rows in splits.items()}
    loaders = {
        s: DataLoader(ds, batch_size=args.batch_size, shuffle=(s == "train"),
                      collate_fn=collate)
        for s, ds in datasets.items()
    }
    mean_len = sum(len(it[0]) for it in datasets["train"].items) / len(datasets["train"])

    model = TinyTransformer(len(vocab), args.d_model, args.n_layers,
                            max_len=args.max_len,
                            positions=args.positions).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = args.epochs * math.ceil(len(datasets["train"]) / args.batch_size)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr,
                                                total_steps=total_steps)
    loss_fn = nn.BCEWithLogitsLoss()

    print(f"task={args.task} arm={args.arm} vocab={len(vocab)} params={n_params:,} "
          f"mean_seq_len={mean_len:.1f} truncated={datasets['train'].n_truncated} device={device}")

    best_val, best_state = 0.0, None
    history = []
    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for x, crd, mask, y in loaders["train"]:
            x, crd, mask, y = (x.to(device), crd.to(device), mask.to(device),
                               y.to(device))
            opt.zero_grad()
            loss = loss_fn(model(x, crd, mask), y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            running += loss.item()
        val_acc = evaluate(model, loaders["val"], device)
        history.append({"epoch": epoch, "loss": running / len(loaders["train"]),
                        "val_acc": val_acc})
        print(f"  epoch {epoch}: loss={history[-1]['loss']:.4f} val_acc={val_acc:.4f}")
        if val_acc > best_val:
            best_val = val_acc
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    test_acc = evaluate(model, loaders["test"], device)
    ood_acc = evaluate(model, loaders["ood"], device)
    elapsed = time.time() - t0

    result = {
        "task": args.task, "arm": args.arm, "positions": args.positions,
        "vocab_size": len(vocab),
        "params": n_params, "mean_train_seq_len": round(mean_len, 1),
        "truncated_train": datasets["train"].n_truncated,
        "val_acc_best": best_val, "test_acc": test_acc, "ood_acc": ood_acc,
        "epochs": args.epochs, "seconds": round(elapsed, 1),
        "d_model": args.d_model, "n_layers": args.n_layers,
        "history": history,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"DONE task={args.task} arm={args.arm} test={test_acc:.4f} ood={ood_acc:.4f} "
          f"({elapsed:.0f}s) -> {args.out}")

    if args.save_model:
        args.save_model.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "vocab": vocab.itos,
                    "config": {"d_model": args.d_model, "n_layers": args.n_layers,
                               "max_len": args.max_len, "task": args.task,
                               "arm": args.arm}},
                   args.save_model)


if __name__ == "__main__":
    main()
