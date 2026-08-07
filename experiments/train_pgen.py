"""Pointer-generator answer decoder: creating as iterated pointing.

Each decode step chooses an action: GEN(structural token) from a ~5-token
vocabulary, or COPY(encoder position). Copied surface words are translated
to concept tokens by the span-restricted inverse lexicon — deterministic,
outside the weights. Exact-tree match against the gold canonical answer.

This is the mechanism the naive seq2seq lacked (0.064 exact); the pointer
path is the one the span task proved at 1.000.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from tokenizers import Vocab
from train_span import MAX_LEVELS, MAX_SIB, tree_paths

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from langgen import LEX_A  # noqa: E402

INV_SPAN = {w: c for c, w in LEX_A.items() if c[0] in "nai" or c == "WH"}
GEN_TOKENS = ["<pad>", "<bos>", "<eos>", "+(", "MOD(", ")"]
GEN_IDX = {t: i for i, t in enumerate(GEN_TOKENS)}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


class PGenDataset(Dataset):
    def __init__(self, rows, src_vocab: Vocab, max_len: int, max_tgt: int):
        self.items = []
        for r in rows:
            toks = r["tokens_struct"]
            ids = src_vocab.encode(toks)  # CLS at 0 -> input pos p maps to p+1
            if len(ids) > max_len:
                continue
            zero = [0] * MAX_LEVELS
            cut = toks.index("<sep>")
            coords = ([[0] + zero]
                      + [[0] + p for p in tree_paths(toks[:cut])]
                      + [[1] + zero]
                      + [[1] + p for p in tree_paths(toks[cut + 1:])])
            # action targets: gen ids in [0, G); copies as G + (pos+1)
            G = len(GEN_TOKENS)
            acts = [GEN_IDX["<bos>"]]
            for a in r["answer_actions"]:
                acts.append(GEN_IDX[a[1]] if a[0] == "g" else G + a[1] + 1)
            acts.append(GEN_IDX["<eos>"])
            if len(acts) > max_tgt:
                continue
            self.items.append((torch.tensor(ids, dtype=torch.long),
                               torch.tensor(coords, dtype=torch.long),
                               torch.tensor(acts, dtype=torch.long),
                               r["answer_canon"]))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


def collate(batch):
    seqs, coords, acts, canons = zip(*batch)
    max_len = max(len(s) for s in seqs)
    max_t = max(len(a) for a in acts)
    x = torch.zeros(len(seqs), max_len, dtype=torch.long)
    crd = torch.zeros(len(seqs), max_len, 1 + MAX_LEVELS, dtype=torch.long)
    mask = torch.zeros(len(seqs), max_len, dtype=torch.bool)
    y = torch.zeros(len(seqs), max_t, dtype=torch.long)
    for i, (s, c, a) in enumerate(zip(seqs, coords, acts)):
        x[i, : len(s)] = s
        crd[i, : len(c)] = c
        mask[i, : len(s)] = True
        y[i, : len(a)] = a
    return x, crd, mask, y, canons


class PointerGen(nn.Module):
    def __init__(self, src_vocab: int, d_model: int = 128, n_layers: int = 4,
                 n_dec: int = 2, n_heads: int = 4, max_tgt: int = 48):
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
        self.act_embed = nn.Embedding(len(GEN_TOKENS), d_model)  # gen actions
        self.copy_proj = nn.Linear(d_model, d_model)  # embed copies via source
        self.tgt_pos = nn.Embedding(max_tgt, d_model)
        dec_layer = nn.TransformerDecoderLayer(
            d_model, n_heads, dim_feedforward=4 * d_model, dropout=0.1,
            batch_first=True, norm_first=True)
        self.decoder = nn.TransformerDecoder(dec_layer, n_dec)
        self.gen_head = nn.Linear(d_model, len(GEN_TOKENS))
        self.ptr_q = nn.Linear(d_model, d_model)

    def encode(self, x, coords, mask):
        h = self.embed(x)
        paths = coords[..., 1:]
        emb = self.path_emb(paths + self.level_offsets)
        emb = emb * (paths > 0).unsqueeze(-1)
        h = h + emb.sum(dim=-2) + self.seg_emb(coords[..., 0])
        return self.encoder(h, src_key_padding_mask=~mask)

    def step_embed(self, y, memory):
        """Embed previous actions: gen actions via table, copies via the
        pointed source representation (grounded copy embedding)."""
        G = len(GEN_TOKENS)
        is_copy = y >= G
        gen_part = self.act_embed(torch.clamp(y, max=G - 1))
        pos = torch.clamp(y - G, min=0)  # encoded position (already +1 for CLS)
        copy_part = self.copy_proj(
            torch.gather(memory, 1,
                         pos.unsqueeze(-1).expand(-1, -1, memory.size(-1))))
        return torch.where(is_copy.unsqueeze(-1), copy_part, gen_part)

    def decode(self, memory, mem_mask, y_in):
        h = self.step_embed(y_in, memory)
        pos = torch.arange(y_in.size(1), device=y_in.device).unsqueeze(0)
        h = h + self.tgt_pos(pos)
        causal = nn.Transformer.generate_square_subsequent_mask(
            y_in.size(1), device=y_in.device)
        h = self.decoder(h, memory, tgt_mask=causal,
                         memory_key_padding_mask=~mem_mask)
        gen_logits = self.gen_head(h)                       # B x T x G
        q = self.ptr_q(h)                                   # B x T x D
        ptr = torch.bmm(q, memory.transpose(1, 2))          # B x T x L
        ptr = ptr.masked_fill(~mem_mask.unsqueeze(1),
                              torch.finfo(ptr.dtype).min)
        return torch.cat([gen_logits, ptr], dim=-1)         # B x T x (G+L)


def greedy_exact(model, loader, device, max_tgt: int, raw_by_batch) -> float:
    model.eval()
    G = len(GEN_TOKENS)
    correct = total = 0
    with torch.no_grad():
        for x, crd, mask, y, canons in loader:
            x, crd, mask = x.to(device), crd.to(device), mask.to(device)
            memory = model.encode(x, crd, mask)
            B = x.size(0)
            out = torch.full((B, 1), GEN_IDX["<bos>"], dtype=torch.long,
                             device=device)
            done = torch.zeros(B, dtype=torch.bool, device=device)
            for _ in range(max_tgt - 1):
                logits = model.decode(memory, mask, out)
                nxt = logits[:, -1].argmax(-1, keepdim=True)
                out = torch.cat([out, nxt], dim=1)
                done |= nxt.squeeze(1) == GEN_IDX["<eos>"]
                if done.all():
                    break
            xs = x.cpu()
            for i in range(B):
                acts = out[i].tolist()[1:]
                if GEN_IDX["<eos>"] in acts:
                    acts = acts[: acts.index(GEN_IDX["<eos>"])]
                recon, ok = [], True
                for a in acts:
                    if a < G:
                        if a < 3:
                            ok = False
                            break
                        recon.append(GEN_TOKENS[a])
                    else:
                        src_id = int(xs[i, a - G])
                        word = vocab_itos[src_id]
                        c = INV_SPAN.get(word)
                        if c is None:
                            ok = False
                            break
                        recon.append(c)
                correct += int(ok and recon == canons[i])
                total += 1
    return correct / max(total, 1)


vocab_itos: list[str] = []


def main() -> None:
    global vocab_itos
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=192)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--max-tgt", type=int, default=48)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    splits = {s: load_jsonl(args.data_dir / f"solvex2_{s}.jsonl")
              for s in ["train", "val", "test", "ood"]}
    src_tokens = set()
    for r in splits["train"]:
        src_tokens.update(r["tokens_struct"])
    src_vocab = Vocab(src_tokens)
    vocab_itos = src_vocab.itos

    datasets = {s: PGenDataset(rows, src_vocab, args.max_len, args.max_tgt)
                for s, rows in splits.items()}
    loaders = {s: DataLoader(ds, batch_size=args.batch_size,
                             shuffle=(s == "train"), collate_fn=collate)
               for s, ds in datasets.items()}

    model = PointerGen(len(src_vocab), args.d_model,
                       max_tgt=args.max_tgt).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = args.epochs * math.ceil(len(datasets["train"]) / args.batch_size)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr,
                                                total_steps=total_steps)
    loss_fn = nn.CrossEntropyLoss(ignore_index=0)

    print(f"pgen src_vocab={len(src_vocab)} params={n_params:,} device={device}",
          flush=True)

    best_val, best_state = 0.0, None
    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for x, crd, mask, y, _ in loaders["train"]:
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
        val = greedy_exact(model, loaders["val"], device, args.max_tgt, None)
        print(f"  epoch {epoch}: loss={running/len(loaders['train']):.4f} "
              f"val_exact={val:.4f}", flush=True)
        if val > best_val:
            best_val = val
            best_state = {k: v.detach().cpu().clone()
                          for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    result = {
        "task": "solvex2-pgen", "params": n_params, "seed": args.seed,
        "val_exact_best": best_val,
        "test_exact": greedy_exact(model, loaders["test"], device,
                                   args.max_tgt, None),
        "ood_exact": greedy_exact(model, loaders["ood"], device,
                                  args.max_tgt, None),
        "seconds": round(time.time() - t0, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"DONE {json.dumps({k: result[k] for k in ['test_exact','ood_exact','seconds']})}",
          flush=True)


if __name__ == "__main__":
    main()
