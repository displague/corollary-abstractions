"""End-to-end demo: creating by pointing + symbolic realization.

Foreign-language question + multi-statement KB -> trained span pointer finds
the answer constituent -> exact code parses the span, canonicalizes, inverts
the lexicon to concepts -> the symbolic renderer realizes the answer as a
fluent phrase in EITHER language. No learned decoder anywhere; fluency and
faithfulness live outside the weights.

Usage: python demo_answer.py [--n 5] [--split test]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import torch

from tokenizers import Vocab
from train_span import SpanDataset, SpanPointer, collate

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from langgen import LEX_A, LEX_B, render_np  # noqa: E402
from match_signatures import canonicalize  # noqa: E402

INV_SPAN = {w: c for c, w in LEX_A.items() if c[0] in "nai" or c == "WH"}


def span_to_tree(tokens: list[str]) -> tuple:
    """Parse a serialized NP span back to a tree with concept-id leaves —
    exact code, the symbolic half of generation."""
    pos = 0

    def parse() -> tuple:
        nonlocal pos
        t = tokens[pos]
        pos += 1
        if t.endswith("("):
            head = t[:-1]
            args = []
            while tokens[pos] != ")":
                args.append(parse())
            pos += 1
            return ("op", "+", tuple(args)) if head == "+" else \
                ("call", head, tuple(args))
        return ("slot", INV_SPAN[t])

    tree = parse()
    assert pos == len(tokens)
    return tree


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--split", default="test")
    ap.add_argument("--checkpoint", type=Path,
                    default=Path("results/solvex2_demo.pt"))
    ap.add_argument("--data-dir", type=Path, default=Path(
        r"C:\Users\displ\Documents\corollary-abstractions\experiments\data"))
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()

    ckpt = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    cfg = ckpt["config"]
    vocab = Vocab(set(ckpt["vocab"]))
    vocab.itos = ckpt["vocab"]
    vocab.stoi = {t: i for i, t in enumerate(vocab.itos)}
    model = SpanPointer(len(vocab.itos), cfg["d_model"], cfg["n_layers"],
                        max_len=cfg["max_len"], positions=cfg["positions"])
    model.load_state_dict(ckpt["state_dict"])
    model.eval()

    rows = [json.loads(l) for l in
            (args.data_dir / f"solvex2_{args.split}.jsonl").open(encoding="utf-8")]
    rng = random.Random(args.seed)
    picks = rng.sample(rows, args.n)

    ds = SpanDataset(picks, vocab, "struct", cfg["max_len"])
    x, crd, mask, s_gold, e_gold = collate(ds.items)
    with torch.no_grad():
        ls, le = model(x, crd, mask)
        ps, pe = ls.argmax(-1), le.argmax(-1)

    for i, r in enumerate(picks):
        print("=" * 70)
        print(f"QUESTION (language B): {r['expr1']}")
        print(f"KNOWLEDGE (language A):")
        for stmt in r["expr2"].split(" | "):
            print(f"  - {stmt}")
        lo, hi = int(ps[i]) - 1, int(pe[i]) - 1  # undo CLS shift
        span = r["tokens_struct"][lo:hi + 1]
        try:
            tree = canonicalize(span_to_tree(span))
            ans_a = " ".join(render_np(tree, LEX_A, "A", rng))
            ans_b = " ".join(render_np(tree, LEX_B, "B", rng))
            gold = r["answer_canon"]
            ok = "correct" if (int(ps[i]) == r["ans_start"] + 1
                              and int(pe[i]) == r["ans_end"] + 1) else "WRONG SPAN"
            print(f"MODEL POINTS AT: {' '.join(span)}   [{ok}]")
            print(f"REALIZED (A): {ans_a}")
            print(f"REALIZED (B): {ans_b}")
        except Exception as exc:
            print(f"MODEL POINTS AT: {' '.join(span)}   [unparseable: {exc}]")
    print("=" * 70)


if __name__ == "__main__":
    main()
