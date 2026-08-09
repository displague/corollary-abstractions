"""Pointer-only analogy trainer: D = f(C) produced entirely by pointing.

Every decode step is a COPY of an input position (structure from segment B,
fillers from segment C) or EOS. No free-generation steps exist, so the
memorization channel that sank the solvex2 pointer-gen is closed by
construction; what remains to learn is the A<->C structural correspondence
across vocabularies — the analogy itself.

Metric: exact reconstruction of D's token stream from the pointed positions.
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

GEN_TOKENS = ["<pad>", "<bos>", "<eos>"]
BOS, EOS = 1, 2
N_SEG = 3


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def seg_coords(tokens: list[str]) -> list[list[int]]:
    zero = [0] * MAX_LEVELS
    coords = [[0] + zero]  # CLS
    seg = 0
    start = 0
    for i, t in enumerate(tokens + ["<sep>"]):
        if t == "<sep>":
            for p in tree_paths(tokens[start:i]):
                coords.append([seg] + p)
            if i < len(tokens):
                coords.append([seg + 1] + zero)  # the sep token itself
            seg += 1
            start = i + 1
    return coords


class AnalogyDataset(Dataset):
    def __init__(self, rows, vocab: Vocab, max_len: int, max_tgt: int):
        self.items = []
        for r in rows:
            toks = r["tokens_struct"]
            ids = vocab.encode(toks)
            if len(ids) > max_len:
                continue
            coords = seg_coords(toks)
            G = len(GEN_TOKENS)
            acts = [BOS] + [G + p + 1 for p in r["target_positions"]] + [EOS]
            if len(acts) > max_tgt:
                continue
            # tree coords for the target prefix: position of token t is fully
            # determined by the bracket structure of tokens < t (computable
            # at inference from the emitted prefix)
            tpaths = tree_paths(r["target_tokens"])
            tcoords = [[0] * MAX_LEVELS] + tpaths  # BOS at origin; step t
            tcoords = tcoords[: len(acts) - 1 + 1]
            self.items.append((torch.tensor(ids, dtype=torch.long),
                               torch.tensor(coords, dtype=torch.long),
                               torch.tensor(acts, dtype=torch.long),
                               torch.tensor(tcoords, dtype=torch.long),
                               r["target_tokens"]))

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return self.items[i]


def collate(batch):
    seqs, coords, acts, tcoords, tgts = zip(*batch)
    max_len = max(len(s) for s in seqs)
    max_t = max(len(a) for a in acts)
    x = torch.zeros(len(seqs), max_len, dtype=torch.long)
    crd = torch.zeros(len(seqs), max_len, 1 + MAX_LEVELS, dtype=torch.long)
    mask = torch.zeros(len(seqs), max_len, dtype=torch.bool)
    y = torch.zeros(len(seqs), max_t, dtype=torch.long)
    tc = torch.zeros(len(seqs), max_t, MAX_LEVELS, dtype=torch.long)
    for i, (s, c, a, t) in enumerate(zip(seqs, coords, acts, tcoords)):
        x[i, : len(s)] = s
        crd[i, : len(c)] = c
        mask[i, : len(s)] = True
        y[i, : len(a)] = a
        tc[i, : len(t)] = t
    return x, crd, mask, y, tc, tgts


def sinusoidal_level_codes(n_levels: int, d_model: int) -> torch.Tensor:
    """Fixed per-level modulation codes -- closed form over depth, so no
    level ever carries an untrained parameter (the 34=34 diagnosis)."""
    pos = torch.arange(n_levels, dtype=torch.float32).unsqueeze(1)
    i = torch.arange(d_model // 2, dtype=torch.float32)
    ang = pos / torch.pow(50.0, 2 * i / d_model)
    codes = torch.zeros(n_levels, d_model)
    codes[:, 0::2] = torch.sin(ang)
    codes[:, 1::2] = torch.cos(ang)
    return codes


class AnalogyPointer(nn.Module):
    def __init__(self, src_vocab: int, d_model: int = 128, n_layers: int = 4,
                 n_dec: int = 2, n_heads: int = 4, max_tgt: int = 96,
                 level_code: str = "table"):
        super().__init__()
        self.level_code = level_code
        self.embed = nn.Embedding(src_vocab, d_model, padding_idx=0)
        self.seg_emb = nn.Embedding(N_SEG + 1, d_model)
        if level_code == "sinusoidal":
            self.sib_shared = nn.Embedding(MAX_SIB + 2, d_model, padding_idx=0)
            self.register_buffer("level_codes",
                                 sinusoidal_level_codes(MAX_LEVELS, d_model))
        elif level_code == "recurrent":
            # depth as ITERATION: one shared cell walks the path root->leaf,
            # so a level-8 address is eight applications of the same learned
            # step -- no depth-indexed parameter, and the consumer trains the
            # same transition at every level it ever sees.
            self.sib_shared = nn.Embedding(MAX_SIB + 2, d_model, padding_idx=0)
            self.path_cell = nn.GRUCell(d_model, d_model)
        else:
            self.path_emb = nn.Embedding(MAX_LEVELS * (MAX_SIB + 1), d_model)
        self.register_buffer("level_offsets",
                             torch.arange(MAX_LEVELS) * (MAX_SIB + 1))
        enc_layer = nn.TransformerEncoderLayer(
            d_model, n_heads, dim_feedforward=4 * d_model, dropout=0.1,
            batch_first=True, norm_first=True)
        self.encoder = nn.TransformerEncoder(enc_layer, n_layers)
        self.act_embed = nn.Embedding(len(GEN_TOKENS), d_model)
        self.copy_proj = nn.Linear(d_model, d_model)
        self.tgt_pos = nn.Embedding(max_tgt, d_model)
        dec_layer = nn.TransformerDecoderLayer(
            d_model, n_heads, dim_feedforward=4 * d_model, dropout=0.1,
            batch_first=True, norm_first=True)
        self.decoder = nn.TransformerDecoder(dec_layer, n_dec)
        self.gen_head = nn.Linear(d_model, len(GEN_TOKENS))
        self.ptr_q = nn.Linear(d_model, d_model)

    def path_embedding(self, paths):
        if self.level_code == "sinusoidal":
            emb = self.sib_shared(paths) * self.level_codes  # broadcast levels
            return (emb * (paths > 0).unsqueeze(-1)).sum(dim=-2)
        if self.level_code == "recurrent":
            B_, L_, K_ = paths.shape
            flat = paths.reshape(-1, K_)
            sib = self.sib_shared(flat)                     # (BL, K, d)
            h = torch.zeros(flat.size(0), sib.size(-1),
                            device=paths.device)
            for k in range(K_):
                step = self.path_cell(sib[:, k], h)
                active = (flat[:, k] > 0).unsqueeze(-1)
                h = torch.where(active, step, h)
            return h.reshape(B_, L_, -1)
        emb = self.path_emb(paths + self.level_offsets)
        return (emb * (paths > 0).unsqueeze(-1)).sum(dim=-2)

    def encode(self, x, coords, mask):
        h = self.embed(x)
        h = h + self.path_embedding(coords[..., 1:]) + self.seg_emb(
            torch.clamp(coords[..., 0], max=N_SEG))
        return self.encoder(h, src_key_padding_mask=~mask)

    def step_embed(self, y, memory):
        G = len(GEN_TOKENS)
        is_copy = y >= G
        gen_part = self.act_embed(torch.clamp(y, max=G - 1))
        pos = torch.clamp(y - G, min=0)
        copy_part = self.copy_proj(
            torch.gather(memory, 1,
                         pos.unsqueeze(-1).expand(-1, -1, memory.size(-1))))
        return torch.where(is_copy.unsqueeze(-1), copy_part, gen_part)

    def decode(self, memory, mem_mask, y_in, tgt_coords=None):
        h = self.step_embed(y_in, memory)
        if tgt_coords is None:
            pos = torch.arange(y_in.size(1), device=y_in.device).unsqueeze(0)
            h = h + self.tgt_pos(pos)
        else:
            h = h + self.path_embedding(tgt_coords)
        causal = nn.Transformer.generate_square_subsequent_mask(
            y_in.size(1), device=y_in.device)
        h = self.decoder(h, memory, tgt_mask=causal,
                         memory_key_padding_mask=~mem_mask)
        gen_logits = self.gen_head(h)
        q = self.ptr_q(h)
        ptr = torch.bmm(q, memory.transpose(1, 2))
        ptr = ptr.masked_fill(~mem_mask.unsqueeze(1),
                              torch.finfo(ptr.dtype).min)
        return torch.cat([gen_logits, ptr], dim=-1)


def greedy_exact(model, loader, device, max_tgt: int, itos) -> float:
    model.eval()
    G = len(GEN_TOKENS)
    correct = total = 0
    with torch.no_grad():
        for x, crd, mask, y, tc, tgts in loader:
            x, crd, mask = x.to(device), crd.to(device), mask.to(device)
            memory = model.encode(x, crd, mask)
            B = x.size(0)
            out = torch.full((B, 1), BOS, dtype=torch.long, device=device)
            done = torch.zeros(B, dtype=torch.bool, device=device)
            xs = x.cpu()
            # incremental target tree-coords from the emitted prefixes
            emitted: list[list[str]] = [[] for _ in range(B)]
            G = len(GEN_TOKENS)
            for _ in range(max_tgt - 1):
                tc_step = torch.zeros(B, out.size(1), MAX_LEVELS,
                                      dtype=torch.long, device=device)
                for i in range(B):
                    paths = tree_paths(emitted[i])
                    rows = [[0] * MAX_LEVELS] + paths
                    for j, row in enumerate(rows[: out.size(1)]):
                        tc_step[i, j] = torch.tensor(row, device=device)
                logits = model.decode(memory, mask, out, tc_step)
                nxt = logits[:, -1].argmax(-1, keepdim=True)
                out = torch.cat([out, nxt], dim=1)
                for i in range(B):
                    a = int(nxt[i, 0])
                    if a >= G and not bool(done[i]):
                        emitted[i].append(itos[int(xs[i, a - G])])
                done |= nxt.squeeze(1) == EOS
                if done.all():
                    break
            for i in range(B):
                acts = out[i].tolist()[1:]
                if EOS in acts:
                    acts = acts[: acts.index(EOS)]
                recon = []
                ok = True
                for a in acts:
                    if a < G:
                        ok = False
                        break
                    recon.append(itos[int(xs[i, a - G])])
                correct += int(ok and recon == tgts[i])
                total += 1
    return correct / max(total, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=192)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--d-model", type=int, default=128)
    ap.add_argument("--max-len", type=int, default=512)
    ap.add_argument("--max-tgt", type=int, default=96)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--save-model", type=Path, default=None)
    ap.add_argument("--task-prefix", default="analogy")
    ap.add_argument("--level-code",
                    choices=["table", "sinusoidal", "recurrent"],
                    default="table")
    ap.add_argument("--init-encoder", type=Path, default=None,
                    help="warm-start encoder weights from "
                         "pretrain_maskskel.py's --save-encoder artifact")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    splits = {s: load_jsonl(args.data_dir / f"{args.task_prefix}_{s}.jsonl")
              for s in ["train", "val", "test", "ood"]}
    src_tokens = set()
    for r in splits["train"]:
        src_tokens.update(r["tokens_struct"])
    vocab = Vocab(src_tokens)

    datasets = {s: AnalogyDataset(rows, vocab, args.max_len, args.max_tgt)
                for s, rows in splits.items()}
    loaders = {s: DataLoader(ds, batch_size=args.batch_size,
                             shuffle=(s == "train"), collate_fn=collate)
               for s, ds in datasets.items()}

    model = AnalogyPointer(len(vocab), args.d_model, max_tgt=args.max_tgt,
                           level_code=args.level_code).to(device)
    if args.init_encoder is not None:
        ckpt = torch.load(args.init_encoder, map_location="cpu",
                          weights_only=False)
        if ckpt["itos"] != vocab.itos:
            raise ValueError(
                "pretrained encoder vocabulary does not match this run's "
                "vocabulary; encoder rows would silently misalign")
        if ckpt["level_code"] != args.level_code:
            raise ValueError(
                f"pretrained encoder used level_code={ckpt['level_code']!r}, "
                f"this run uses {args.level_code!r}")
        state = dict(ckpt["encoder_state"])
        # The pretrain embedding has one extra trailing row for <mask>;
        # the fine-tune vocabulary does not contain it.
        state["embed.weight"] = state["embed.weight"][: len(vocab)]
        missing, unexpected = model.load_state_dict(state, strict=False)
        loaded = sorted({k.split(".")[0] for k in state})
        assert not unexpected, unexpected
        print(f"init-encoder loaded modules: {loaded}; "
              f"cold-start modules: "
              f"{sorted({k.split('.')[0] for k in missing})}", flush=True)
    n_params = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = args.epochs * math.ceil(len(datasets["train"]) / args.batch_size)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr,
                                                total_steps=total_steps)
    loss_fn = nn.CrossEntropyLoss(ignore_index=0)

    print(f"analogy vocab={len(vocab)} params={n_params:,} "
          f"train={len(datasets['train'])} device={device}", flush=True)

    best_val, best_state = 0.0, None
    t0 = time.time()
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for x, crd, mask, y, tc, _ in loaders["train"]:
            x, crd, mask, y, tc = (x.to(device), crd.to(device),
                                   mask.to(device), y.to(device),
                                   tc.to(device))
            opt.zero_grad()
            memory = model.encode(x, crd, mask)
            logits = model.decode(memory, mask, y[:, :-1], tc[:, : y.size(1) - 1])
            loss = loss_fn(logits.reshape(-1, logits.size(-1)),
                           y[:, 1:].reshape(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            running += loss.item()
        val = greedy_exact(model, loaders["val"], device, args.max_tgt,
                           vocab.itos)
        print(f"  epoch {epoch}: loss={running/len(loaders['train']):.4f} "
              f"val_exact={val:.4f}", flush=True)
        if val > best_val:
            best_val = val
            best_state = {k: v.detach().cpu().clone()
                          for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    result = {
        "task": "analogy", "params": n_params, "seed": args.seed,
        "level_code": args.level_code,
        "val_exact_best": best_val,
        "test_exact": greedy_exact(model, loaders["test"], device,
                                   args.max_tgt, vocab.itos),
        "ood_exact": greedy_exact(model, loaders["ood"], device,
                                  args.max_tgt, vocab.itos),
        "seconds": round(time.time() - t0, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"DONE {json.dumps({k: result[k] for k in ['test_exact','ood_exact','seconds']})}",
          flush=True)
    if args.save_model:
        args.save_model.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "vocab": vocab.itos,
                    "config": {"d_model": args.d_model,
                               "max_tgt": args.max_tgt,
                               "max_len": args.max_len}},
                   args.save_model)


if __name__ == "__main__":
    main()
