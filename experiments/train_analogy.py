"""Pointer-only analogy trainer: D = f(C) produced entirely by pointing.

Every decode step is a COPY of an input position (structure from segment B,
fillers from segment C) or EOS. No free-generation steps exist, so the
memorization channel that sank the solvex2 pointer-gen is closed by
construction; what remains to learn is the A<->C structural correspondence
across vocabularies — the analogy itself.

Metric: exact reconstruction of D's token stream from the pointed positions.

v0.6 depth-consumer predictions (P-DC, registered before adjudication):

P-DC1. Extending shared path iteration into both the pointer query and decoder
    memory consumer improves mean depth-OOD exact over recurrent-address only,
    wins materially on at least two of three paired seeds, and keeps every
    trained-depth seed at or above 0.99 exact.
P-DC2. Query-only and memory-only each improve materially over address, each on
    at least two paired seeds, while both is at least as strong as the better
    single consumer.
P-DC3. The parameter-matched, order/level-aware, identity-preserving one-shot
    MLP consumer with fixed closed-form level codes does not match the both-
    recurrent consumer. The address encoder remains recurrent in every arm;
    this compares consumer mechanisms but does not isolate iteration from
    learned level processing.
P-DC4. All five arms run seeds 0/1/2 and report parameters, trained-depth exact,
    conditional depth-OOD exact, teacher-forced per-step/decile failure,
    inclusion by depth, source/data/config provenance, and checkpoint digests.
    This is a protocol gate: analysis either satisfies it or refuses to run.

Registered adjudication thresholds (before any final-matrix run): "improves"
and "does not match" require an absolute mean depth-OOD margin of at least
0.15 and at least two of three paired-seed wins by that margin. "At least as
strong" permits at most a 0.01 mean deficit. The trained-depth floor is 0.99.
The 0.15 margin exceeds the documented 0.139 cold-seed spread of the recurrent
address control. P-DC4 is a protocol gate, not an empirical firing.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import defaultdict
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
        self.total_rows = len(rows)
        self.dropped_max_len = 0
        self.dropped_max_tgt = 0
        self.by_depth = defaultdict(
            lambda: {"generated": 0, "kept": 0,
                     "dropped_max_len": 0, "dropped_max_tgt": 0})
        for r in rows:
            if "depth" not in r:
                raise ValueError("analogy row is missing required depth metadata")
            depth = str(r["depth"])
            self.by_depth[depth]["generated"] += 1
            toks = r["tokens_struct"]
            ids = vocab.encode(toks)
            if len(ids) > max_len:
                self.dropped_max_len += 1
                self.by_depth[depth]["dropped_max_len"] += 1
                continue
            coords = seg_coords(toks)
            G = len(GEN_TOKENS)
            acts = [BOS] + [G + p + 1 for p in r["target_positions"]] + [EOS]
            if len(acts) > max_tgt:
                self.dropped_max_tgt += 1
                self.by_depth[depth]["dropped_max_tgt"] += 1
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
            self.by_depth[depth]["kept"] += 1

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
                 level_code: str = "table", consumer: str = "address"):
        super().__init__()
        self.level_code = level_code
        self.consumer = consumer
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
        if consumer in {"query", "both"}:
            self.query_path_cell = nn.GRUCell(d_model, d_model)
        if consumer in {"memory", "both"}:
            self.memory_path_cell = nn.GRUCell(d_model, d_model)
        if consumer == "mlp":
            # 99,073 parameters each versus 99,072 for GRUCell(128, 128):
            # the two-consumer control differs from ``both`` by only 2 params.
            width = 3 * d_model + 1
            self.query_consumer_mlp = nn.Sequential(
                nn.Linear(d_model, width), nn.GELU(),
                nn.Linear(width, d_model),
            )
            self.memory_consumer_mlp = nn.Sequential(
                nn.Linear(d_model, width), nn.GELU(),
                nn.Linear(width, d_model),
            )
            self.register_buffer(
                "consumer_level_codes",
                sinusoidal_level_codes(MAX_LEVELS, d_model),
            )
        if consumer != "address" and level_code != "recurrent":
            raise ValueError("depth consumers require recurrent level coding")

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

    def recurrent_consume(self, base, paths, cell):
        shape = paths.shape
        flat_paths = paths.reshape(-1, shape[-1])
        flat_base = base.reshape(-1, base.size(-1))
        siblings = self.sib_shared(flat_paths)
        hidden = flat_base
        for level in range(flat_paths.size(1)):
            step = cell(siblings[:, level], hidden)
            active = (flat_paths[:, level] > 0).unsqueeze(-1)
            hidden = torch.where(active, step, hidden)
        return hidden.reshape(*shape[:-1], base.size(-1))

    def one_shot_path_summary(self, paths):
        """Order-aware, non-iterative path summary for the MLP control."""
        level_codes = self.consumer_level_codes[: paths.size(-1)]
        siblings = self.sib_shared(paths) * level_codes
        return (siblings * (paths > 0).unsqueeze(-1)).sum(dim=-2)

    def prepare_memory(self, memory, source_paths):
        if self.consumer in {"memory", "both"}:
            return self.recurrent_consume(
                memory, source_paths, self.memory_path_cell
            )
        if self.consumer == "mlp":
            active = (source_paths > 0).any(dim=-1, keepdim=True)
            consumed = self.memory_consumer_mlp(
                memory + self.one_shot_path_summary(source_paths))
            return torch.where(active, consumed, memory)
        return memory

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
        if self.consumer in {"query", "both"}:
            if tgt_coords is None:
                raise ValueError("recurrent query consumer requires target paths")
            q = self.recurrent_consume(q, tgt_coords, self.query_path_cell)
        elif self.consumer == "mlp":
            if tgt_coords is None:
                raise ValueError("MLP query consumer requires target paths")
            active = (tgt_coords > 0).any(dim=-1, keepdim=True)
            consumed = self.query_consumer_mlp(
                q + self.one_shot_path_summary(tgt_coords))
            q = torch.where(active, consumed, q)
        ptr = torch.bmm(q, memory.transpose(1, 2))
        ptr = ptr.masked_fill(~mem_mask.unsqueeze(1),
                              torch.finfo(ptr.dtype).min)
        return torch.cat([gen_logits, ptr], dim=-1)


def teacher_forced_diagnostics(model, loader, device, itos) -> dict:
    """Locate failures without autoregressive drift.

    Report absolute-step and normalized-decile action accuracy, first-error
    deciles, and the structural-copy/C-leaf/EOS split used by the original
    depth-wall diagnosis.  These are diagnostics, not additional success
    metrics: greedy sequence exact remains the adjudicating result.
    """
    model.eval()
    by_step: dict[int, list[int]] = {}
    by_decile = {index: [0, 0] for index in range(10)}
    first_error = {index: 0 for index in range(10)}
    by_kind = {kind: [0, 0] for kind in ("B-struct", "C-leaf", "EOS")}
    perfect = total = 0
    sep_id = itos.index("<sep>")
    with torch.no_grad():
        for x, crd, mask, y, tc, _ in loader:
            x, crd, mask, y, tc = (x.to(device), crd.to(device),
                                   mask.to(device), y.to(device),
                                   tc.to(device))
            memory = model.encode(x, crd, mask)
            memory = model.prepare_memory(memory, crd[..., 1:])
            logits = model.decode(memory, mask, y[:, :-1],
                                  tc[:, : y.size(1) - 1])
            pred = logits.argmax(-1)
            gold = y[:, 1:]
            for batch_index in range(x.size(0)):
                valid = gold[batch_index] != 0
                n_steps = int(valid.sum())
                if not n_steps:
                    continue
                separators = torch.nonzero(
                    x[batch_index] == sep_id, as_tuple=False).flatten()
                if len(separators) < 2:
                    raise ValueError("analogy input has fewer than two separators")
                c_start = int(separators[1]) + 1
                errors = []
                for step in range(n_steps):
                    action = int(gold[batch_index, step])
                    ok = int(pred[batch_index, step] == action)
                    by_step.setdefault(step, [0, 0])
                    by_step[step][0] += ok
                    by_step[step][1] += 1
                    decile = min(9, 10 * step // n_steps)
                    by_decile[decile][0] += ok
                    by_decile[decile][1] += 1
                    if action == EOS:
                        kind = "EOS"
                    else:
                        source_position = action - len(GEN_TOKENS)
                        kind = "C-leaf" if source_position >= c_start else "B-struct"
                    by_kind[kind][0] += ok
                    by_kind[kind][1] += 1
                    if not ok:
                        errors.append(step)
                if errors:
                    decile = min(9, 10 * errors[0] // n_steps)
                    first_error[decile] += 1
                else:
                    perfect += 1
                total += 1

    def rates(counts: dict) -> dict:
        return {
            str(key): {
                "correct": value[0],
                "total": value[1],
                "accuracy": value[0] / max(value[1], 1),
            }
            for key, value in counts.items()
        }

    erroneous = total - perfect
    return {
        "mode": "teacher-forced",
        "examples": total,
        "step_perfect": perfect,
        "step_perfect_rate": perfect / max(total, 1),
        "by_kind": rates(by_kind),
        "by_absolute_step": rates(dict(sorted(by_step.items()))),
        "by_decile": rates(by_decile),
        "first_error_decile": {
            str(key): {
                "examples": value,
                "fraction_of_erroneous": value / max(erroneous, 1),
            }
            for key, value in first_error.items()
        },
    }


def greedy_exact(model, loader, device, max_tgt: int, itos) -> float:
    model.eval()
    G = len(GEN_TOKENS)
    correct = total = 0
    with torch.no_grad():
        for x, crd, mask, y, tc, tgts in loader:
            x, crd, mask = x.to(device), crd.to(device), mask.to(device)
            memory = model.encode(x, crd, mask)
            memory = model.prepare_memory(memory, crd[..., 1:])
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
    ap.add_argument("--consumer",
                    choices=["address", "query", "memory", "both", "mlp"],
                    default="address")
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
    inclusion = {
        split: {
            "generated": dataset.total_rows,
            "kept": len(dataset),
            "dropped_max_len": dataset.dropped_max_len,
            "dropped_max_tgt": dataset.dropped_max_tgt,
            "by_depth": dict(dataset.by_depth),
        }
        for split, dataset in datasets.items()
    }
    train_generator = torch.Generator().manual_seed(args.seed)
    loaders = {s: DataLoader(
        ds, batch_size=args.batch_size, shuffle=(s == "train"),
        collate_fn=collate, generator=train_generator if s == "train" else None)
        for s, ds in datasets.items()}

    model = AnalogyPointer(len(vocab), args.d_model, max_tgt=args.max_tgt,
                           level_code=args.level_code,
                           consumer=args.consumer).to(device)
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
            memory = model.prepare_memory(memory, crd[..., 1:])
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
    test_exact = greedy_exact(model, loaders["test"], device,
                              args.max_tgt, vocab.itos)
    ood_exact = greedy_exact(model, loaders["ood"], device,
                             args.max_tgt, vocab.itos)
    result = {
        "task": "analogy", "params": n_params, "seed": args.seed,
        "level_code": args.level_code,
        "consumer": args.consumer,
        "inclusion": inclusion,
        "val_exact_best": best_val,
        "test_exact": test_exact,
        "ood_exact": ood_exact,
        "test_diagnostics": teacher_forced_diagnostics(
            model, loaders["test"], device, vocab.itos),
        "ood_diagnostics": teacher_forced_diagnostics(
            model, loaders["ood"], device, vocab.itos),
        "seconds": round(time.time() - t0, 1),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"DONE {json.dumps({k: result[k] for k in ['test_exact','ood_exact','seconds']})}",
          flush=True)
    if args.save_model:
        args.save_model.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "vocab": vocab.itos,
                    "seed": args.seed,
                    "config": {"d_model": args.d_model,
                               "max_tgt": args.max_tgt,
                               "max_len": args.max_len,
                               "level_code": args.level_code,
                               "consumer": args.consumer}},
                   args.save_model)


if __name__ == "__main__":
    main()
