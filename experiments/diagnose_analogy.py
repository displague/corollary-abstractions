"""Per-step teacher-forced diagnostic for the analogy depth wall.

Three positional mechanisms produced a bit-identical OOD failure set, so the
wall is not addressing. This measures WHERE prediction breaks under teacher
forcing (no autoregressive drift): per-step accuracy split by step kind
(structure copy from segment B vs leaf copy from segment C), by absolute
step index, and the first-error position distribution — on test (novel
combos, solved) vs ood (deeper trees, 1.4% solved).

Usage: python diagnose_analogy.py --checkpoint results/analogy_diag.pt
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import torch

from tokenizers import Vocab
from train_analogy import (AnalogyDataset, AnalogyPointer, GEN_TOKENS,
                           collate, load_jsonl)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path,
                    default=Path("results/analogy_diag.pt"))
    ap.add_argument("--data-dir", type=Path, default=Path(
        r"C:\Users\displ\Documents\corollary-abstractions\experiments\data"))
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    vocab = Vocab(set(ckpt["vocab"]))
    vocab.itos = ckpt["vocab"]
    vocab.stoi = {t: i for i, t in enumerate(vocab.itos)}
    cfg = ckpt["config"]
    model = AnalogyPointer(len(vocab.itos), cfg["d_model"],
                           max_tgt=cfg["max_tgt"]).to(device)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    G = len(GEN_TOKENS)

    for split in ["test", "ood"]:
        rows = load_jsonl(args.data_dir / f"analogy_{split}.jsonl")
        # Recover step kinds from raw rows (aligned with dataset filtering).
        ds = AnalogyDataset(rows, vocab, cfg["max_len"], cfg["max_tgt"])
        kept = []
        i = 0
        for r in rows:
            toks = r["tokens_struct"]
            if len(vocab.encode(toks)) > cfg["max_len"]:
                continue
            if len(r["target_positions"]) + 2 > cfg["max_tgt"]:
                continue
            kept.append(r)
        assert len(kept) == len(ds)

        loader = torch.utils.data.DataLoader(
            ds, batch_size=128, collate_fn=collate)
        by_kind = defaultdict(lambda: [0, 0])
        by_decile = defaultdict(lambda: [0, 0])
        first_err = Counter()
        n_perfect = 0
        row_iter = iter(kept)
        with torch.no_grad():
            for x, crd, mask, y, tc, _ in loader:
                x, crd, mask, y, tc = (x.to(device), crd.to(device),
                                       mask.to(device), y.to(device),
                                       tc.to(device))
                memory = model.encode(x, crd, mask)
                logits = model.decode(memory, mask, y[:, :-1],
                                      tc[:, : y.size(1) - 1])
                pred = logits.argmax(-1)
                gold = y[:, 1:]
                for b in range(x.size(0)):
                    r = next(row_iter)
                    n_steps = len(r["target_positions"]) + 1  # + EOS
                    sep_positions = [i for i, t in
                                     enumerate(r["tokens_struct"])
                                     if t == "<sep>"]
                    c_start = sep_positions[1] + 1
                    errs = []
                    for s in range(n_steps):
                        ok = bool(pred[b, s] == gold[b, s])
                        if s < len(r["target_positions"]):
                            src = r["target_positions"][s]
                            kind = "C-leaf" if src >= c_start else "B-struct"
                        else:
                            kind = "EOS"
                        by_kind[kind][0] += ok
                        by_kind[kind][1] += 1
                        dec = min(9, 10 * s // max(n_steps, 1))
                        by_decile[dec][0] += ok
                        by_decile[dec][1] += 1
                        if not ok:
                            errs.append(s)
                    if errs:
                        first_err[min(9, 10 * errs[0] // max(n_steps, 1))] += 1
                    else:
                        n_perfect += 1

        print(f"\n=== {split} (n={len(ds)}) — teacher-forced ===")
        print(f"  step-perfect examples: {n_perfect}/{len(ds)} "
              f"({n_perfect/len(ds):.3f})")
        for kind in ["B-struct", "C-leaf", "EOS"]:
            ok, tot = by_kind[kind]
            print(f"  {kind:9s}: {ok}/{tot} = {ok/max(tot,1):.4f}")
        print("  accuracy by sequence decile:",
              " ".join(f"{by_decile[d][0]/max(by_decile[d][1],1):.2f}"
                       for d in range(10)))
        if first_err:
            total_err = sum(first_err.values())
            print("  first-error decile distribution:",
                  " ".join(f"{first_err.get(d,0)/total_err:.2f}"
                           for d in range(10)))


if __name__ == "__main__":
    main()
