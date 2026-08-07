"""Real-data task (realsyn): same-lemma detection on Spanish Wikipedia forms.

The first non-synthetic task in the suite. Pairs of surface word forms from
the user-supplied Spanish wlp sample (word/lemma/PoS): are they forms of the
same lemma? Positives are real inflectional variants (hablo/hablas);
negatives are half random, half HARD (distinct lemmas sharing a 4-char
prefix), so string-prefix matching alone cannot solve it.

Registered prediction (for once favoring the char arm): morphology is
surface-visible, so raw characters carry real signal here — the front-end
thesis says symbolic layers own what has closed form, and lemmatization of
unseen forms does not; this is exactly the graded residual weights are for.

Split hygiene: lemmas are partitioned across train/test/ood (no lemma
appears in two splits), so the model must learn morphology, not lemma
identity. OOD = lemmas with the highest form-fanout (hardest paradigms).
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

WLP = Path(r"C:\Users\displ\Documents\corollary-abstractions\experiments"
           r"\data_real\wiki-es-wlp\wordLemPoS.txt")


def load_lemma_forms(path: Path, min_count: int = 3) -> dict[str, list[str]]:
    forms: dict[str, set] = defaultdict(set)
    counts: dict[str, int] = defaultdict(int)
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 5:
                continue
            word, lemma = parts[2].strip().lower(), parts[3].strip().lower()
            if (not word or not lemma or word.startswith("@@")
                    or word == "-----" or not word.isalpha()
                    or not lemma.isalpha() or len(word) < 3):
                continue
            forms[lemma].add(word)
            counts[lemma] += 1
    return {l: sorted(ws) for l, ws in forms.items()
            if len(ws) >= 2 and counts[l] >= min_count}


def build_pairs(lemmas: list[str], forms: dict[str, list[str]],
                n: int, rng: random.Random) -> list[dict]:
    by_prefix: dict[str, list[str]] = defaultdict(list)
    for l in lemmas:
        for w in forms[l]:
            by_prefix[w[:4]].append(l)
    out = []
    attempts = 0
    n_pos = 0
    while len(out) < n and attempts < n * 60:
        attempts += 1
        want_pos = n_pos < (len(out) + 1) // 2 + 1
        if want_pos:
            l = rng.choice(lemmas)
            a, b = rng.sample(forms[l], 2)
            out.append({"expr1": a, "expr2": b, "label": 1, "lemma": l})
            n_pos += 1
        else:
            hard = rng.random() < 0.5
            l1 = rng.choice(lemmas)
            w1 = rng.choice(forms[l1])
            if hard:
                cands = [l for l in by_prefix.get(w1[:4], []) if l != l1]
                if not cands:
                    continue
                l2 = rng.choice(cands)
            else:
                l2 = rng.choice(lemmas)
                if l2 == l1:
                    continue
            w2 = rng.choice(forms[l2])
            if w1 == w2:
                continue
            out.append({"expr1": w1, "expr2": w2, "label": 0,
                        "lemma": f"{l1}|{l2}", "hard": hard})
    rng.shuffle(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wlp", type=Path, default=WLP)
    ap.add_argument("--out-dir", type=Path, default=Path("data"))
    ap.add_argument("--train", type=int, default=50000)
    ap.add_argument("--val", type=int, default=5000)
    ap.add_argument("--test", type=int, default=5000)
    ap.add_argument("--ood", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=53)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    forms = load_lemma_forms(args.wlp)
    lemmas = sorted(forms)
    print(f"{len(lemmas)} lemmas with >=2 forms")

    # ood = highest-fanout paradigms; rest split 80/10/10 by lemma
    by_fanout = sorted(lemmas, key=lambda l: -len(forms[l]))
    ood_lemmas = by_fanout[: max(200, len(lemmas) // 20)]
    rest = [l for l in lemmas if l not in set(ood_lemmas)]
    rng.shuffle(rest)
    n_test = len(rest) // 10
    test_lemmas = rest[:n_test]
    val_lemmas = rest[n_test: 2 * n_test]
    train_lemmas = rest[2 * n_test:]
    print(f"lemma split: train={len(train_lemmas)} val={len(val_lemmas)} "
          f"test={len(test_lemmas)} ood={len(ood_lemmas)} (disjoint)")

    splits = {
        "train": build_pairs(train_lemmas, forms, args.train, rng),
        "val": build_pairs(val_lemmas, forms, args.val, rng),
        "test": build_pairs(test_lemmas, forms, args.test, rng),
        "ood": build_pairs(ood_lemmas, forms, args.ood, rng),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in splits.items():
        path = args.out_dir / f"realsyn_{split}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        n_pos = sum(r["label"] for r in rows)
        print(f"realsyn/{split}: {len(rows)} ({n_pos} pos) -> {path}")


if __name__ == "__main__":
    main()
