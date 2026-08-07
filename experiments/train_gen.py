"""Answer-tree decoder: pointing -> producing (the creating experiment).

Encoder reads question(B) + distractor KB(A) with tree-path positions;
a small autoregressive decoder EMITS the answer as canonical concept
tokens (interlingua tree serialization). The symbolic renderer can then
realize the tree as fluent text in either language — fluency costs zero
parameters and surface hallucination is structurally impossible.

Metric: exact generated-sequence match against the gold canonical answer
tree. Capability-blind floors are near zero here (answers are
high-entropy NP trees), and the held-out-combo split carries the
recombination question into generation.
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

from tokenizers import Vocab
from train_span import MAX_LEVELS, MAX_SIB, tree_paths


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


BOS, EOS = "<bos>", "<eos>"


class GenDataset(Dataset):
    def __init__(self, rows, src_vocab: Vocab, tgt_vocab: Vocab, max_len: int,
                 max_tgt: int):
        self.items = []
        for r in rows:
            toks = r["tokens_struct"]
            ids = src_vocab.encode(toks)
            if len(ids) > max_len:
                continue
            zero = [0] * MAX_LEVELS
            cut = toks.index("<sep>")
            coords = ([[0] + zero]
                      + [[0] + p for p in tree_paths(toks[:cut])]
                      + [[1] + zero]
                      + [[1] + p for p in tree_paths(toks[cut + 1:])])
            tgt = [tgt_vocab.stoi[BOS]] + [
                tgt_vocab.stoi.get(t, 3) for t in r["answer_canon"]
            ] + [tgt_vocab.stoi[EOS]]
            if len(tgt) > max_tgt:
                continue
            self.items.append((torch.tensor(ids, dtype=torch.long),
                               torch.tensor(coords, dtype=torch.long),
                               torch.tensor(tgt, dtype=torch.long)))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


def collate(batch):
    seqs, coords, tgts = zip(*batch)
    max_len = max(len(s) for s in seqs)
    max_t = max(len(t) for t in tgts)
    x = torch.zeros(len(seqs), max_len, dtype=torch.long)
    crd = torch.zeros(len(seqs), max_len, 1 + MAX_LEVELS, dtype=torch.long)
    mask = torch.zeros(len(seqs), max_len, dtype=torch.bool)
    y = torch.zeros(len(seqs), max_t, dtype=torch.long)
    for i, (s, c, t) in enumerate(zip(seqs, coords, tgts)):
        x[i, : len(s)] = s
        crd[i, : len(c)] = c
        mask[i, : len(s)] = True
        y[i, : len(t)] = t
    return x, crd, mask, y


class TreeSeq2Seq(nn.Module):
    def __init__(self, src_vocab: int, tgt_vocab: int, d_model: int = 128,
                 n_layers: int = 4, n_dec: int = 2, n_heads: int = 4,
                 max_tgt: int = 40):
        super().__init__()
        self.embed = nn.Embedding(src_vocab, d_model, padding_idx=0)
        self.seg_emb = nn.Embedding(2, d_model)
        self.path_emb = nn.Embedding(MAX_LEVELS * (MAX_SIB + 1), d_model)
        self.register_buffer("level_offsets",
                             torch.arange(MAX_LEVELS) * (MAX_SIB + 1))
        enc_layer = nn.TransformerEncoderLayer(
            d_model, n_heads, dim_feedforward=4 * d_model, dropout=0.1,
            batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(enc_layer, n_layers)
        self.tgt_embed = nn.Embedding(tgt_vocab, d_model, padding_idx=0)
        self.tgt_pos = nn.Embedding(max_tgt, d_model)
        dec_layer = nn.TransformerDecoderLayer(
            d_model, n_heads, dim_feedforward=4 * d_model, dropout=0.1,
            batch_first=True, norm_first=True)
        self.decoder = nn.TransformerDecoder(dec_layer, n_dec)
        self.out = nn.Linear(d_model, tgt_vocab)

    def encode(self, x, coords, mask):
        h = self.embed(x)
        paths = coords[..., 1:]
        emb = self.path_emb(paths + self.level_offsets)
        emb = emb * (paths > 0).unsqueeze(-1)
        h = h + emb.sum(dim=-2) + self.seg_emb(coords[..., 0])
        return self.encoder(h, src_key_padding_mask=~mask)

    def decode(self, memory, mem_mask, y_in):
        pos = torch.arange(y_in.size(1), device=y_in.device).unsqueeze(0)
        h = self.tgt_embed(y_in) + self.tgt_pos(pos)
        causal = nn.Transformer.generate_square_subsequent_mask(
            y_in.size(1), device=y_in.device)
        h = self.decoder(h, memory, tgt_mask=causal,
                         memory_key_padding_mask=~mem_mask)
        return self.out(h)


def greedy_exact(model, loader, device, tgt_vocab, max_tgt: int) -> float:
    model.eval()
    eos = tgt_vocab.stoi[EOS]
    bos = tgt_vocab.stoi[BOS]
    correct = total = 0
    with torch.no_grad():
        for x, crd, mask, y in loader:
            x, crd, mask = x.to(device), crd.to(device), mask.to(device)
            memory = model.encode(x, crd, mask)
            B = x.size(0)
            out = torch.full((B, 1), bos, dtype=torch.long, device=device)
            done = torch.zeros(B, dtype=torch.bool, device=device)
            for _ in range(max_tgt - 1):
                logits = model.decode(memory, mask, out)
                nxt = logits[:, -1].argmax(-1, keepdim=True)
                out = torch.cat([out, nxt], dim=1)
                done |= nxt.squeeze(1) == eos
                if done.all():
                    break
            for i in range(B):
                gen = out[i].tolist()[1:]
                gen = gen[: gen.index(eos)] if eos in gen else gen
                gold = y[i].tolist()[1:]
                gold = gold[: gold.index(eos)] if eos in gold else [g for g in gold if g]
                correct += int(gen == gold)
                total += 1
    return correct / max(total, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--task-prefix", default="solvex2")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=192)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--max-tgt", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    splits = {s: load_jsonl(args.data_dir / f"{args.task_prefix}_{s}.jsonl")
              for s in ["train", "val", "test", "ood"]}
    src_tokens, tgt_tokens = set(), set()
    for r in splits["train"]:
        src_tokens.update(r["tokens_struct"])
        tgt_tokens.update(r["answer_canon"])
    src_vocab = Vocab(src_tokens)
    tgt_vocab = Vocab(tgt_tokens | {BOS, EOS})

    datasets = {s: GenDataset(rows, src_vocab, tgt_vocab, args.max_len,
                              args.max_tgt)
                for s, rows in splits.items()}
    loaders = {s: DataLoader(ds, batch_size=args.batch_size,
                             shuffle=(s == "train"), collate_fn=collate)
               for s, ds in datasets.items()}

    model = TreeSeq2Seq(len(src_vocab), len(tgt_vocab), args.d_model,
                        max_tgt=args.max_tgt).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = args.epochs * math.ceil(len(datasets["train"]) / args.batch_size)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr,
                                                total_steps=total_steps)
    loss_fn = nn.CrossEntropyLoss(ignore_index=0)

    print(f"gen task={args.task_prefix} src_vocab={len(src_vocab)} "
          f"tgt_vocab={len(tgt_vocab)} params={n_params:,} device={device}",
          flush=True)

    best_val, best_state = 0.0, None
    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for x, crd, mask, y in loaders["train"]:
            x, crd, mask, y = (x.to(device), crd.to(device), mask.to(device),
                               y.to(device))
            opt.zero_grad()
            memory = model.encode(x, crd, mask)
            logits = model.decode(memory, mask, y[:, :-1])
            loss = loss_fn(logits.reshape(-1, logits.size(-1)),
                           y[:, 1:].reshape(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            running += loss.item()
        val = greedy_exact(model, loaders["val"], device, tgt_vocab, args.max_tgt)
        print(f"  epoch {epoch}: loss={running/len(loaders['train']):.4f} "
              f"val_exact={val:.4f}", flush=True)
        if val > best_val:
            best_val = val
            best_state = {k: v.detach().cpu().clone()
                          for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    result = {
        "task": f"{args.task_prefix}-gen", "params": n_params,
        "src_vocab": len(src_vocab), "tgt_vocab": len(tgt_vocab),
        "seed": args.seed, "val_exact_best": best_val,
        "test_exact": greedy_exact(model, loaders["test"], device, tgt_vocab,
                                   args.max_tgt),
        "ood_exact": greedy_exact(model, loaders["ood"], device, tgt_vocab,
                                  args.max_tgt),
        "seconds": round(time.time() - t0, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"DONE {json.dumps({k: result[k] for k in ['test_exact','ood_exact','seconds']})}",
          flush=True)


if __name__ == "__main__":
    main()
