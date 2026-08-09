"""Masked skeleton modeling: BERT's objective transposed to structure.

ROADMAP-v0.5 item 10e / DESIGN-cognitive-frames §5. Mask one node of a
parse tree; the model recovers it by POINTING into a shuffled candidate
bag appended after the tree -- no generation head, so the objective is
native to the pointer architecture rather than borrowed from language
modeling. The encoder trained here (embedding, segment embedding,
recurrent path cell, transformer stack) is exactly AnalogyPointer's
encoder, so its weights transfer verbatim to the analogy task via
train_analogy.py --init-encoder.

Registered predictions (P-CF5, written before adjudication):

P-CF5a. Fine-tuning the recurrent analogy arm from this pretrained
    encoder improves depth OOD (baseline 0.226) by MORE than it improves
    in-distribution test exact (baseline 1.000, so any test movement is
    downward slack): gains should concentrate where structure is the
    bottleneck, or the objective taught content, not structure.
P-CF5b. The pretraining corpus contains ONLY trained-depth trees (the
    analogy train split's segments, depths 2-3). Any OOD gain is
    therefore attributable to the objective, not to deeper exposure --
    the contamination the curriculum arm proved worthless (0.006) and
    that this control deliberately excludes.

Honest boundary: this is self-supervised pretraining on synthetic
algebra trees, not web-scale text; the claim under test is the
objective's effect on structural generalization at fixed data depth,
nothing broader.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from tokenizers import Vocab
from train_analogy import load_jsonl
from train_span import MAX_LEVELS, tree_paths

MASK = "<mask>"


def split_segments(tokens: list[str]) -> list[list[str]]:
    segs, cur = [], []
    for t in tokens:
        if t == "<sep>":
            segs.append(cur)
            cur = []
        else:
            cur.append(t)
    segs.append(cur)
    return [s for s in segs if s]


class MaskedTreeDataset(Dataset):
    """Dynamic masking: each __getitem__ draws a fresh mask position."""

    def __init__(self, trees: list[list[str]], vocab: Vocab, mask_id: int,
                 n_distractors: int, seed: int):
        self.trees = trees
        self.vocab = vocab
        self.mask_id = mask_id
        self.n_distractors = n_distractors
        self.rng = random.Random(seed)
        self.content = sorted(
            t for t in vocab.itos
            if t not in {"<pad>", "<cls>", "<sep>", "(", ")"}
        )

    def __len__(self):
        return len(self.trees)

    def __getitem__(self, i):
        tokens = self.trees[i]
        maskable = [j for j, t in enumerate(tokens) if t not in {"(", ")"}]
        pos = self.rng.choice(maskable)
        answer = tokens[pos]

        bag = sorted(set(tokens) - {"(", ")"})
        distractors = [
            t for t in self.rng.sample(
                self.content, min(self.n_distractors + 8, len(self.content)))
            if t not in bag
        ][: self.n_distractors]
        bag = bag + distractors
        self.rng.shuffle(bag)

        ids = [self.vocab.stoi["<cls>"]]
        coords = [[0] + [0] * MAX_LEVELS]
        paths = tree_paths(tokens)
        for j, t in enumerate(tokens):
            ids.append(self.mask_id if j == pos else self.vocab.stoi[t])
            coords.append([0] + paths[j])
        ids.append(self.vocab.stoi["<sep>"])
        coords.append([1] + [0] * MAX_LEVELS)
        bag_start = len(ids)
        for t in bag:
            ids.append(self.vocab.stoi[t])
            coords.append([1] + [0] * MAX_LEVELS)

        mask_pos = 1 + pos
        target = bag_start + bag.index(answer)
        return (torch.tensor(ids, dtype=torch.long),
                torch.tensor(coords, dtype=torch.long),
                mask_pos, target, bag_start)


def collate(batch):
    seqs, coords, mask_pos, target, bag_start = zip(*batch)
    max_len = max(len(s) for s in seqs)
    x = torch.zeros(len(seqs), max_len, dtype=torch.long)
    crd = torch.zeros(len(seqs), max_len, 1 + MAX_LEVELS, dtype=torch.long)
    pad = torch.zeros(len(seqs), max_len, dtype=torch.bool)
    for i, (s, c) in enumerate(zip(seqs, coords)):
        x[i, : len(s)] = s
        crd[i, : len(c)] = c
        pad[i, : len(s)] = True
    return (x, crd, pad, torch.tensor(mask_pos), torch.tensor(target),
            torch.tensor(bag_start))


def run_eval(model, loader, device) -> float:
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, crd, pad, mpos, tgt, bstart in loader:
            x, crd, pad = x.to(device), crd.to(device), pad.to(device)
            memory = model.encode(x, crd, pad)
            q = model.ptr_q(
                memory[torch.arange(x.size(0)), mpos])
            scores = torch.bmm(q.unsqueeze(1),
                               memory.transpose(1, 2)).squeeze(1)
            arange = torch.arange(x.size(1), device=device).unsqueeze(0)
            in_bag = (arange >= bstart.to(device).unsqueeze(1)) & pad
            scores = scores.masked_fill(~in_bag,
                                        torch.finfo(scores.dtype).min)
            pred = scores.argmax(-1).cpu()
            correct += int((pred == tgt).sum())
            total += x.size(0)
    return correct / max(total, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--task-prefix", default="analogy")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--save-encoder", type=Path, required=True)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--n-distractors", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--level-code",
                    choices=["table", "sinusoidal", "recurrent"],
                    default="recurrent")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Vocabulary MUST be built exactly as train_analogy builds it (same
    # split, same set-comprehension), so that itos aligns and the encoder
    # transfers row-for-row. <mask> is one extra row appended past the
    # shared vocabulary; the fine-tune loader slices it off.
    train_rows = load_jsonl(args.data_dir / f"{args.task_prefix}_train.jsonl")
    val_rows = load_jsonl(args.data_dir / f"{args.task_prefix}_val.jsonl")
    src_tokens = set()
    for r in train_rows:
        src_tokens.update(r["tokens_struct"])
    vocab = Vocab(src_tokens)
    mask_id = len(vocab)

    # P-CF5b control: pretraining trees come ONLY from the train split's
    # segments -- trained depths, no deeper exposure.
    def rows_to_trees(rows):
        trees = []
        for r in rows:
            trees.extend(split_segments(r["tokens_struct"]))
        return trees

    train_trees = rows_to_trees(train_rows)
    val_trees = rows_to_trees(val_rows)

    from train_analogy import AnalogyPointer
    model = AnalogyPointer(len(vocab) + 1, level_code=args.level_code
                           ).to(device)
    n_params = sum(p.numel() for p in model.parameters())

    datasets = {
        "train": MaskedTreeDataset(train_trees, vocab, mask_id,
                                   args.n_distractors, args.seed),
        "val": MaskedTreeDataset(val_trees, vocab, mask_id,
                                 args.n_distractors, args.seed + 1),
    }
    loaders = {k: DataLoader(v, batch_size=args.batch_size,
                             shuffle=(k == "train"), collate_fn=collate)
               for k, v in datasets.items()}

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr,
                            weight_decay=0.01)
    print(f"maskskel vocab={len(vocab)}+mask params={n_params:,} "
          f"trees={len(train_trees)} level_code={args.level_code} "
          f"device={device}", flush=True)

    t0 = time.time()
    history = []
    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for x, crd, pad, mpos, tgt, bstart in loaders["train"]:
            x, crd, pad = x.to(device), crd.to(device), pad.to(device)
            tgt = tgt.to(device)
            opt.zero_grad()
            memory = model.encode(x, crd, pad)
            q = model.ptr_q(memory[torch.arange(x.size(0)), mpos])
            scores = torch.bmm(q.unsqueeze(1),
                               memory.transpose(1, 2)).squeeze(1)
            arange = torch.arange(x.size(1), device=device).unsqueeze(0)
            in_bag = (arange >= bstart.to(device).unsqueeze(1)) & pad
            scores = scores.masked_fill(~in_bag,
                                        torch.finfo(scores.dtype).min)
            loss = nn.functional.cross_entropy(scores, tgt)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            running += loss.item()
        val_acc = run_eval(model, loaders["val"], device)
        history.append({"epoch": epoch,
                        "loss": running / len(loaders["train"]),
                        "val_mask_acc": val_acc})
        print(f"  epoch {epoch}: loss={history[-1]['loss']:.4f} "
              f"val_mask_acc={val_acc:.4f}", flush=True)

    encoder_keys = ("embed.", "seg_emb.", "sib_shared.", "path_cell.",
                    "encoder.", "ptr_q.")
    encoder_state = {k: v.detach().cpu() for k, v in
                     model.state_dict().items()
                     if k.startswith(encoder_keys)}
    args.save_encoder.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"encoder_state": encoder_state, "itos": vocab.itos,
                "level_code": args.level_code, "mask_id": mask_id},
               args.save_encoder)

    result = {"task": "maskskel_pretrain", "params": n_params,
              "seed": args.seed, "level_code": args.level_code,
              "n_trees": len(train_trees), "history": history,
              "final_val_mask_acc": history[-1]["val_mask_acc"],
              "seconds": round(time.time() - t0, 1)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n",
                        encoding="utf-8")
    print(f"DONE {json.dumps({'final_val_mask_acc': result['final_val_mask_acc'], 'seconds': result['seconds']})}",
          flush=True)


if __name__ == "__main__":
    main()
