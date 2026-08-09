"""Exercise a released analogy-pointer checkpoint without retraining.

The demo builds fresh deterministic analogy quadruples A:B::C:D.  D is not
present in the input, but each of its structural and lexical pieces is.  The
model must assemble D entirely by pointing into B and C.  We show both the
held-out-combination split at trained depth and the deeper-tree split so the
successful capability and its remaining generalization wall stay together.

Run from ``experiments/``::

    python demo_analogy_checkpoint.py \
        --checkpoint results/analogy_maskskel_s0.pt
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import torch

from analogygen import build_split
from tokenizers import Vocab
from train_analogy import (AnalogyDataset, AnalogyPointer, BOS, EOS,
                           GEN_TOKENS)
from train_span import MAX_LEVELS, tree_paths


def restore_vocab(tokens: list[str]) -> Vocab:
    vocab = Vocab(set(tokens))
    vocab.itos = tokens
    vocab.stoi = {token: i for i, token in enumerate(tokens)}
    return vocab


def infer_level_code(state: dict[str, torch.Tensor]) -> str:
    if any(key.startswith("path_cell.") for key in state):
        return "recurrent"
    if "level_codes" in state:
        return "sinusoidal"
    return "table"


def decode_one(model: AnalogyPointer, item, vocab: Vocab,
               max_tgt: int, device: str) -> list[str]:
    x, coords, _acts, _target_coords, _target = item
    x = x.unsqueeze(0).to(device)
    coords = coords.unsqueeze(0).to(device)
    mask = torch.ones_like(x, dtype=torch.bool)
    with torch.no_grad():
        memory = model.encode(x, coords, mask)
        memory = model.prepare_memory(memory, coords[..., 1:])
        out = torch.tensor([[BOS]], dtype=torch.long, device=device)
        emitted: list[str] = []
        gen_count = len(GEN_TOKENS)
        for _ in range(max_tgt - 1):
            target_coords = torch.zeros(
                1, out.size(1), MAX_LEVELS, dtype=torch.long, device=device)
            rows = [[0] * MAX_LEVELS] + tree_paths(emitted)
            for j, row in enumerate(rows[:out.size(1)]):
                target_coords[0, j] = torch.tensor(row, device=device)
            logits = model.decode(memory, mask, out, target_coords)
            nxt = int(logits[0, -1].argmax())
            if nxt == EOS:
                break
            if nxt < gen_count or nxt - gen_count >= x.size(1):
                return emitted + ["<invalid-action>"]
            emitted.append(vocab.itos[int(x[0, nxt - gen_count])])
            out = torch.cat(
                [out, torch.tensor([[nxt]], dtype=torch.long, device=device)],
                dim=1)
        return emitted


def compact(tokens: list[str], limit: int = 100) -> str:
    text = " ".join(tokens)
    return text if len(text) <= limit else text[:limit - 3] + "..."


def run_split(name: str, dataset: AnalogyDataset, model: AnalogyPointer,
              vocab: Vocab, cfg: dict, device: str,
              show: int) -> None:
    predictions = [decode_one(model, item, vocab, cfg["max_tgt"], device)
                   for item in dataset]
    exact = sum(pred == item[-1] for pred, item in zip(predictions, dataset))

    print(f"\n{name}: {exact}/{len(dataset)} exact = "
          f"{exact / max(len(dataset), 1):.3f}")
    for i, (pred, item) in enumerate(zip(predictions[:show], dataset[:show]), 1):
        target = item[-1]
        print(f"  example {i}: {'CORRECT' if pred == target else 'MISS'}")
        print(f"    target:    {compact(target)}")
        print(f"    predicted: {compact(pred)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--examples", type=int, default=3,
                        help="examples printed per split")
    parser.add_argument("--eval-size", type=int, default=100,
                        help="fresh deterministic examples per split")
    args = parser.parse_args()
    if args.examples < 0 or args.eval_size < 1:
        parser.error("--examples must be non-negative and --eval-size positive")

    checkpoint = torch.load(args.checkpoint, map_location="cpu",
                            weights_only=False)
    vocab = restore_vocab(checkpoint["vocab"])
    cfg = checkpoint["config"]
    level_code = infer_level_code(checkpoint["state_dict"])
    consumer = cfg.get("consumer", "address")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = AnalogyPointer(len(vocab), cfg["d_model"],
                           max_tgt=cfg["max_tgt"],
                           level_code=level_code,
                           consumer=consumer).to(device)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    # These are fresh examples, not the training run's saved evaluation rows.
    # Both use unseen transform/base-shape combinations.  Only depth differs.
    # Deeper held-out generation rejects many random candidates.  Ask the
    # generator for a surplus, then take the announced evaluation size so the
    # denominator never changes silently with generator yield.
    test_rows = build_split(args.eval_size * 4, random.Random(5061),
                            [2, 2, 3], set(), True)
    ood_rows = build_split(args.eval_size * 4, random.Random(5062),
                           [4, 5], set(), True)
    test_data = AnalogyDataset(test_rows, vocab, cfg["max_len"], cfg["max_tgt"])
    ood_data = AnalogyDataset(ood_rows, vocab, cfg["max_len"], cfg["max_tgt"])
    if len(test_data) < args.eval_size or len(ood_data) < args.eval_size:
        raise RuntimeError("fresh-example generator did not reach --eval-size")
    test_data.items = test_data.items[:args.eval_size]
    ood_data.items = ood_data.items[:args.eval_size]
    print(f"checkpoint={args.checkpoint.name} params="
          f"{sum(p.numel() for p in model.parameters()):,} "
          f"addressing={level_code} device={device}")
    print(f"depth_consumer={consumer}")
    print("Every output token is copied from the input; no generation head "
          "can invent one.")
    run_split("held-out combinations, trained depth", test_data, model,
              vocab, cfg, device, args.examples)
    run_split("held-out combinations, deeper trees", ood_data, model,
              vocab, cfg, device, args.examples)


if __name__ == "__main__":
    main()
