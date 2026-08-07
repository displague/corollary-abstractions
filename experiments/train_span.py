"""Span-pointer trainer for solve-for-X: answer = (start, end) into the input.

Arms:
- struct: tokens_struct as-is
- hybrid: struct + two symbolic feature tokens (structural-unification bit,
  WH role) — same features as the classification hybrid

Metric: exact span match. --d-model/--n-layers/--train-frac expose the
scaling-grid axes.
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

from tokenizers import Vocab, hybrid_tokens


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def tokens_for(example: dict, arm: str) -> tuple[list[str], int]:
    """Token list and the index shift applied before the original stream."""
    if arm == "struct":
        return example["tokens_struct"], 0
    feats = hybrid_tokens(example)[:2]
    return feats + example["tokens_struct"], 2


MAX_DEPTH, MAX_SIB = 32, 64
MAX_LEVELS = 12


def tree_paths(tokens: list[str]) -> list[list[int]]:
    """Per-token ancestry path of sibling indices — unique addressing that
    stays level-wise in-distribution as trees deepen."""
    paths = []
    sib_stack = [0]
    path_stack: list[int] = []
    for t in tokens:
        if t.endswith("(") or t.endswith("⟨"):
            idx = sib_stack[-1]
            sib_stack[-1] += 1
            path_stack.append(idx)
            paths.append(list(path_stack))
            sib_stack.append(0)
        elif t == ")":
            paths.append(list(path_stack) if path_stack else [0])
            if len(sib_stack) > 1:
                sib_stack.pop()
            if path_stack:
                path_stack.pop()
        else:
            idx = sib_stack[-1]
            sib_stack[-1] += 1
            paths.append(list(path_stack) + [idx])
    out = []
    for p in paths:
        p = [min(x, MAX_SIB - 1) + 1 for x in p[:MAX_LEVELS]]  # 0 = absent
        out.append(p + [0] * (MAX_LEVELS - len(p)))
    return out


def tree_coords(tokens: list[str]) -> list[tuple[int, int]]:
    """(depth, sibling-index) per token from the serialized bracket stream —
    symbolic coordinates the front-end knows exactly, depth-capped."""
    coords = []
    sib_stack = [0]
    for t in tokens:
        if t.endswith("(") or t.endswith("⟨"):
            coords.append((len(sib_stack) - 1, sib_stack[-1]))
            sib_stack[-1] += 1
            sib_stack.append(0)
        elif t == ")":
            coords.append((max(len(sib_stack) - 2, 0), 0))
            if len(sib_stack) > 1:
                sib_stack.pop()
        else:
            coords.append((len(sib_stack) - 1, sib_stack[-1]))
            sib_stack[-1] += 1
    return [(min(d, MAX_DEPTH - 1), min(s, MAX_SIB - 1)) for d, s in coords]


class SpanDataset(Dataset):
    def __init__(self, rows: list[dict], vocab: Vocab, arm: str, max_len: int):
        self.items = []
        for r in rows:
            toks, shift = tokens_for(r, arm)
            ids = vocab.encode(toks)  # adds CLS at index 0
            if len(ids) > max_len:
                continue
            start = r["ans_start"] + shift + 1  # +1 for CLS
            end = r["ans_end"] + shift + 1
            # coords rooted per side; segment id disambiguates the trees
            zero_path = [0] * MAX_LEVELS
            if "<sep>" in toks:
                cut = toks.index("<sep>")
                coords = ([[0] + zero_path]
                          + [[0] + p for p in tree_paths(toks[:cut])]
                          + [[1] + zero_path]
                          + [[1] + p for p in tree_paths(toks[cut + 1:])])
            else:
                coords = [[0] + zero_path] + [[0] + p for p in tree_paths(toks)]
            self.items.append((torch.tensor(ids, dtype=torch.long),
                               torch.tensor(coords, dtype=torch.long),
                               start, end))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


def collate(batch):
    seqs, coords, starts, ends = zip(*batch)
    max_len = max(len(s) for s in seqs)
    out = torch.zeros(len(seqs), max_len, dtype=torch.long)
    crd = torch.zeros(len(seqs), max_len, 1 + MAX_LEVELS, dtype=torch.long)
    mask = torch.zeros(len(seqs), max_len, dtype=torch.bool)
    for i, (s, c) in enumerate(zip(seqs, coords)):
        out[i, : len(s)] = s
        crd[i, : len(c)] = c
        mask[i, : len(s)] = True
    return (out, crd, mask, torch.tensor(starts, dtype=torch.long),
            torch.tensor(ends, dtype=torch.long))


class SpanPointer(nn.Module):
    def __init__(self, vocab_size: int, d_model: int, n_layers: int,
                 n_heads: int = 4, max_len: int = 512, positions: str = "abs"):
        super().__init__()
        self.positions = positions
        self.embed = nn.Embedding(vocab_size, d_model, padding_idx=0)
        if positions == "abs":
            self.pos = nn.Embedding(max_len, d_model)
        else:  # tree: symbolic (depth, sibling) coordinates from the parse
            self.seg_emb = nn.Embedding(2, d_model)
            # one table, level-offset indices: level l sib s -> l*(MAX_SIB+1)+s
            self.path_emb = nn.Embedding(MAX_LEVELS * (MAX_SIB + 1), d_model,
                                         padding_idx=None)
            self.register_buffer(
                "level_offsets",
                torch.arange(MAX_LEVELS) * (MAX_SIB + 1))
        layer = nn.TransformerEncoderLayer(
            d_model, n_heads, dim_feedforward=4 * d_model,
            dropout=0.1, batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(layer, n_layers)
        self.span_head = nn.Linear(d_model, 2)  # start logit, end logit per pos

    def forward(self, x, coords, mask):
        h = self.embed(x)
        if self.positions == "abs":
            pos = torch.arange(x.size(1), device=x.device).unsqueeze(0)
            h = h + self.pos(pos)
        else:
            seg = coords[..., 0]
            paths = coords[..., 1:]
            idx = paths + self.level_offsets  # broadcast over levels
            emb = self.path_emb(idx)
            emb = emb * (paths > 0).unsqueeze(-1)  # zero out absent levels
            h = h + emb.sum(dim=-2) + self.seg_emb(seg)
        h = self.encoder(h, src_key_padding_mask=~mask)
        logits = self.span_head(h)  # B x L x 2
        neg = torch.finfo(logits.dtype).min
        logits = logits.masked_fill(~mask.unsqueeze(-1), neg)
        return logits[..., 0], logits[..., 1]


def evaluate(model, loader, device) -> float:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, crd, mask, s, e in loader:
            x, crd, mask = x.to(device), crd.to(device), mask.to(device)
            ls, le = model(x, crd, mask)
            ps, pe = ls.argmax(-1).cpu(), le.argmax(-1).cpu()
            correct += ((ps == s) & (pe == e)).sum().item()
            total += len(s)
    return correct / max(total, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["struct", "hybrid"], required=True)
    ap.add_argument("--task-prefix", default="solvex")
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--n-layers", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--train-frac", type=float, default=1.0,
                    help="fraction of the train split used (scaling axis)")
    ap.add_argument("--positions", choices=["abs", "tree"], default="abs")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    splits = {s: load_jsonl(args.data_dir / f"{args.task_prefix}_{s}.jsonl")
              for s in ["train", "val", "test", "ood"]}
    if args.train_frac < 1.0:
        keep = int(len(splits["train"]) * args.train_frac)
        splits["train"] = splits["train"][:keep]

    seen: set[str] = set()
    for r in splits["train"]:
        toks, _ = tokens_for(r, args.arm)
        seen.update(toks)
    vocab = Vocab(seen)

    datasets = {s: SpanDataset(rows, vocab, args.arm, args.max_len)
                for s, rows in splits.items()}
    loaders = {s: DataLoader(ds, batch_size=args.batch_size,
                             shuffle=(s == "train"), collate_fn=collate)
               for s, ds in datasets.items()}

    model = SpanPointer(len(vocab), args.d_model, args.n_layers,
                        max_len=args.max_len, positions=args.positions).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = args.epochs * math.ceil(len(datasets["train"]) / args.batch_size)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr,
                                                total_steps=total_steps)
    loss_fn = nn.CrossEntropyLoss()

    print(f"solvex arm={args.arm} pos={args.positions} d={args.d_model} L={args.n_layers} "
          f"train={len(datasets['train'])} vocab={len(vocab)} "
          f"params={n_params:,} device={device}", flush=True)

    best_val, best_state = 0.0, None
    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for x, crd, mask, s, e in loaders["train"]:
            x, crd, mask, s, e = (x.to(device), crd.to(device), mask.to(device),
                                  s.to(device), e.to(device))
            opt.zero_grad()
            ls, le = model(x, crd, mask)
            loss = loss_fn(ls, s) + loss_fn(le, e)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            running += loss.item()
        val = evaluate(model, loaders["val"], device)
        print(f"  epoch {epoch}: loss={running/len(loaders['train']):.4f} "
              f"val_exact={val:.4f}", flush=True)
        if val > best_val:
            best_val = val
            best_state = {k: v.detach().cpu().clone()
                          for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    result = {
        "task": args.task_prefix, "arm": args.arm, "positions": args.positions,
        "d_model": args.d_model,
        "n_layers": args.n_layers, "train_frac": args.train_frac,
        "train_size": len(datasets["train"]), "params": n_params,
        "vocab_size": len(vocab), "seed": args.seed,
        "val_exact_best": best_val,
        "test_exact": evaluate(model, loaders["test"], device),
        "ood_exact": evaluate(model, loaders["ood"], device),
        "seconds": round(time.time() - t0, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"DONE {json.dumps({k: result[k] for k in ['arm','positions','test_exact','ood_exact']})}",
          flush=True)


if __name__ == "__main__":
    main()
