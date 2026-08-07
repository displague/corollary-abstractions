"""Analogy completion (analogy): creating as recombinant pointing.

Quadruple A : B :: C : D where B = f(A) for a structural transform f, C is A
re-skinned into a different vocabulary, and the target D = f(C) exists
NOWHERE in the input — the first non-extractive generation task. But every
atom of D exists: its structure is B's, its fillers are C's. Supervision is
pure pointer actions (structural tokens point at B positions, leaves point
at C positions), so creation = learned A<->C correspondence + proven
pointing. Both prior decoder failures are answered by construction: no
free-generation steps exist to memorize.

Held-out split: (transform, base-skeleton-hash) combos never seen together
in training; OOD adds deeper base trees.
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from exprgen import NAME_POOLS, random_tree, tree_slots  # noqa: E402

SEP = "<sep>"

TRANSFORMS = {
    "negate": lambda t: ("op", "neg", (t,)),
    "invert": lambda t: ("op", "inv", (t,)),
    "square": lambda t: ("op", "^", (t, ("num", 2.0))),
    "root": lambda t: ("call", "SQRT", (t,)),
    "selfmul": lambda t: ("op", "*", (t, t)),
}


def skin_tree(t: tuple, skin: dict[str, str]) -> tuple:
    if t[0] == "slot":
        return ("slot", skin[t[1]])
    if t[0] == "num":
        return t
    return (t[0], t[1], tuple(skin_tree(a, skin) for a in t[2]))


def serialize(t: tuple) -> list[str]:
    """Deterministic traversal; leaves keep their (skinned) names so A and C
    differ lexically while sharing token-stream structure position-for-
    position."""
    kind = t[0]
    if kind == "num":
        return [f"#{t[1]:g}"]
    if kind == "slot":
        return [t[1]]
    out = [f"{t[1]}("]
    for a in t[2]:
        out.extend(serialize(a))
    out.append(")")
    return out


def make_skin(rng: random.Random, slots: set[str], pool_idx: int) -> dict:
    pool = list(NAME_POOLS[pool_idx])
    rng.shuffle(pool)
    while len(pool) < len(slots):
        pool += [f"{p}{rng.randrange(10)}" for p in pool]
    return {s: pool[i] for i, s in enumerate(sorted(slots))}


def shape_hash(t: tuple) -> str:
    if t[0] == "slot":
        return "?"
    if t[0] == "num":
        return f"#{t[1]:g}"
    return f"{t[1]}({','.join(shape_hash(a) for a in t[2])})"


def is_leaf_token(tok: str) -> bool:
    return not (tok.endswith("(") or tok == ")" or tok.startswith("#"))


def build_split(n: int, rng: random.Random, depths: list[int],
                heldout: set, want_heldout: bool) -> list[dict]:
    out = []
    attempts = 0
    while len(out) < n and attempts < n * 60:
        attempts += 1
        d = rng.choice(depths)
        base = random_tree(rng, d, rng.choice([2, 3, 3]))
        if not tree_slots(base):
            continue
        tname = rng.choice(list(TRANSFORMS))
        combo = (tname, shape_hash(base))
        digest = hashlib.md5(f"{tname}|{combo[1]}".encode()).digest()
        is_held = (digest[0] % 100) < 15  # stable 15% of combos (not hash():
        # Python string hashing is process-randomized and would break
        # regeneration-from-seeds)
        if is_held != want_heldout:
            continue
        f = TRANSFORMS[tname]
        skin_a = make_skin(rng, tree_slots(base), 0)
        skin_c = make_skin(rng, tree_slots(base), 1)
        A, C = skin_tree(base, skin_a), skin_tree(base, skin_c)
        B, D = f(A), f(C)
        a_toks, b_toks, c_toks, d_toks = (serialize(A), serialize(B),
                                          serialize(C), serialize(D))
        tokens = a_toks + [SEP] + b_toks + [SEP] + c_toks
        b_off = len(a_toks) + 1
        c_off = b_off + len(b_toks) + 1
        c_leaf_positions = [c_off + i for i, t in enumerate(c_toks)
                            if is_leaf_token(t)]
        actions, leaf_ordinal = [], 0
        for i, tok in enumerate(d_toks):
            if is_leaf_token(tok):
                actions.append(c_leaf_positions[leaf_ordinal
                                                % len(c_leaf_positions)])
                leaf_ordinal += 1
            else:
                actions.append(b_off + i)
        if [tokens[p] for p in actions] != d_toks:
            continue
        out.append({"task": "analogy", "tokens_struct": tokens,
                    "target_positions": actions, "target_tokens": d_toks,
                    "transform": tname, "combo": [tname, shape_hash(base)],
                    "depth": d, "label": 1})
    rng.shuffle(out)
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("data"))
    ap.add_argument("--train", type=int, default=50000)
    ap.add_argument("--val", type=int, default=5000)
    ap.add_argument("--test", type=int, default=5000)
    ap.add_argument("--ood", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=61)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    splits = {
        "train": build_split(args.train, rng, [2, 2, 3], set(), False),
        "val": build_split(args.val, rng, [2, 2, 3], set(), False),
        "test": build_split(args.test, rng, [2, 2, 3], set(), True),
        "ood": build_split(args.ood, rng, [4, 5], set(), True),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in splits.items():
        path = args.out_dir / f"analogy_{split}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"analogy/{split}: {len(rows)} -> {path}")


if __name__ == "__main__":
    main()
